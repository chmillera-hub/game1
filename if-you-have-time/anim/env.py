"""Environments for "If You Have Time": deep space, the ship *Meridian*, the observation lounge.

Public API (BIBLE.md sections 3 and 7)

    draw_space(canvas, t, drift=1.0, brightness=1.0, offset=(0, 0), zoom=1.0)          SCREEN space
    draw_ship(canvas, t, x, y, scale=1.0, angle=0.0, glow=1.0)                          SCREEN space
    ship_window(x, y, scale=1.0, angle=0.0) -> (wx, wy)                                 SCREEN space
    draw_lounge(canvas, t, light=1, door=0, swirl=0, window_bright=1, rain=0, warm=0)   STAGE coords
    draw_lounge_front(canvas, t, light=1, door=0)                                       STAGE coords
    char_light(light=1, warm=0, swirl=0, window_bright=1) -> dict   (optional helper: Pose lighting
                                                                      fields that match the room)

Performance notes (this machine's CPU skia: full-frame gradients ~14 ms, kPlus blends ~36 ms,
native BGRA image blits ~5 ms):
  * the static lounge set is recorded once per lighting state ("lit", "dark", "warm") as a vector
    skia Picture and rasterised into camera-sized tiles at a zoom-bucketed resolution (LRU cache),
    so a frame is one image blit (two during a light cross-fade) + the small dynamic parts;
  * glows use cached premultiplied sprites whose alpha is 0 -> plain src-over == additive light,
    which is ~10x cheaper than kPlus;
  * nebula / galaxy are numpy-generated textures (smooth, compression friendly).
"""
from __future__ import annotations

import math
from collections import OrderedDict
from functools import lru_cache

import numpy as np
import skia

from anim.core import clamp, col, hash01, lerp, noise1, paint, smooth_path, smoothstep
from config import H, W

# =========================================================================== set constants
FLOOR_Y = 1150
DOOR_CX = -40
DOOR_W = 200
DOOR_TOP = 430
DOOR_X0, DOOR_X1 = DOOR_CX - DOOR_W // 2, DOOR_CX + DOOR_W // 2      # -140 .. 60
WINDOW = (90, 140, 630, 860)            # x0, y0, x1, y1 of the glass (arched top)
WINDOW_R = (WINDOW[2] - WINDOW[0]) / 2  # 270: arch radius
WINDOW_CX = (WINDOW[0] + WINDOW[2]) / 2  # 360
WINDOW_SPRING_Y = WINDOW[1] + WINDOW_R  # 410: where the arch starts
SILL_Y = (860, 900)
BENCH = (40, 420)
_BENCH_DRAW = (50, 420)                 # drawn cushion extent (left end tucked against the door jamb)
BENCH_SEAT_Y = 960
BENCH_FRONT_Y = 1030
CONSOLE_X = (640, 720)
CONSOLE_PANEL_Y = (760, 860)
GALAXY_CENTER = (352, 468)              # stage coords of the swirl galaxy core in the window
CEILING_Y = 60                          # ceiling light strip
SCONCES = ((-250, 520), (790, 520))

# extents of the drawn set (generous so no camera framing shows a void)
SET_X = (-1000, 1700)
SET_Y = (-800, 2400)

_TAU = math.tau
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)


# =========================================================================== image helpers
def _bgra(rgb: np.ndarray, alpha: np.ndarray | None = None) -> skia.Image:
    """float rgb (h,w,3) 0..1 premultiplied (+ alpha 0..1) -> native N32 premul skia Image.

    alpha may be lower than rgb on purpose: alpha 0 with rgb > 0 composites as pure additive
    light under the default src-over blend (premultiplied math: dst*(1-a) + src)."""
    h, w = rgb.shape[:2]
    arr = np.empty((h, w, 4), np.uint8)
    q = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    arr[..., 0] = q[..., 2]
    arr[..., 1] = q[..., 1]
    arr[..., 2] = q[..., 0]
    arr[..., 3] = 255 if alpha is None else np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kBGRA_8888_ColorType,
                                alphaType=skia.kPremul_AlphaType)


def _pnoise(h, w, tile_h, tile_w, cutoff, beta=1.0, seed=0):
    """Seamlessly tiling smooth noise (h x w samples over a tile_h x tile_w unit tile).
    cutoff: feature size in units (gaussian low-pass), beta: 1/f^beta slope. Zero mean, unit std."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None] * h / tile_h
    fx = np.fft.rfftfreq(w)[None, :] * w / tile_w
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    amp = f ** (-beta) * np.exp(-(f * cutoff) ** 2)
    amp[0, 0] = 0.0
    spec = amp * (rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape))
    n = np.fft.irfft2(spec, s=(h, w))
    n = (n - n.mean()) / (n.std() + 1e-9)
    return n.astype(np.float32)


def _sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _hexf(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def _mscale(canvas) -> float:
    """Uniform scale of the canvas matrix (stage units -> device px)."""
    m = canvas.getTotalMatrix()
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0


@lru_cache(maxsize=128)
def _sprite(color: str, kind: str = "soft", occl: float = 0.0) -> skia.Image:
    """Radial light sprite (premultiplied). occl=0 -> purely additive light."""
    n = 128
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - (n - 1) / 2) ** 2 + (yy - (n - 1) / 2) ** 2) / (n / 2)
    edge = np.clip(1 - d * d, 0, 1)
    if kind == "soft":          # gaussian-ish, long tail
        prof = np.exp(-d * d * 3.0) * edge
    elif kind == "core":        # tight bright centre + faint tail
        prof = (np.exp(-d * d * 14.0) * 0.8 + np.exp(-d * d * 3.0) * 0.2) * edge
    elif kind == "wide":        # flatter falloff (light pools)
        prof = edge ** 1.6
    elif kind == "disc":        # soft-edged disc
        prof = _sstep(1.0, 0.72, d)
    else:
        raise ValueError(kind)
    c = _hexf(color)
    rgb = c[None, None, :] * prof[..., None]
    return _bgra(rgb.astype(np.float32), (prof * occl).astype(np.float32))


@lru_cache(maxsize=64)
def _band(color: str, kind: str = "down", occl: float = 0.0) -> skia.Image:
    """1D light ramp sprite (8 x 128) along y: 'down' = bright at top fading down,
    'up' = bright at the bottom, 'mid' = bright in the middle."""
    n = 128
    y = (np.arange(n, dtype=np.float32) + 0.5) / n
    if kind == "down":
        prof = (1 - y) ** 2.2
    elif kind == "up":
        prof = y ** 2.2
    elif kind == "mid":
        prof = np.exp(-((y - 0.5) / 0.22) ** 2) * np.clip(1 - (2 * y - 1) ** 2, 0, 1)
    else:
        raise ValueError(kind)
    prof = np.repeat(prof[:, None], 8, axis=1)
    c = _hexf(color)
    return _bgra((c[None, None, :] * prof[..., None]).astype(np.float32), (prof * occl).astype(np.float32))


def _glow(canvas, x, y, rx, ry, color, alpha=1.0, kind="soft", angle=0.0, occl=0.0):
    """Additive-looking light blob (cheap: one sprite blit)."""
    if alpha <= 0.003 or rx <= 0 or ry <= 0:
        return
    p = skia.Paint()
    p.setAlphaf(clamp(alpha))
    if angle:
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(angle)
        canvas.drawImageRect(_sprite(color, kind, occl), skia.Rect(-rx, -ry, rx, ry), _LIN, p)
        canvas.restore()
    else:
        canvas.drawImageRect(_sprite(color, kind, occl), skia.Rect(x - rx, y - ry, x + rx, y + ry), _LIN, p)


def _wash(canvas, x0, y0, x1, y1, color, alpha=1.0, kind="down", occl=0.0):
    if alpha <= 0.003:
        return
    p = skia.Paint()
    p.setAlphaf(clamp(alpha))
    canvas.drawImageRect(_band(color, kind, occl), skia.Rect(x0, y0, x1, y1), _LIN, p)


def _lg(x0, y0, x1, y1, colors, pos=None):
    cs = [c if isinstance(c, int) else col(c) for c in colors]
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], cs, pos)


def _sp(shader, alpha=1.0, stroke=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(shader)
    p.setAlphaf(clamp(alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def _rrect(x0, y0, x1, y1, r):
    return skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r)


def _poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


# =========================================================================== nebula / stars
NEB_TILE = (1440.0, 2560.0)          # nebula texture tile in layer units (w, h)


@lru_cache(maxsize=2)
def _nebula_rgb(seed: int = 7):
    """Tileable deep-space colour field (base + soft violet/teal/magenta nebula) as float rgb."""
    from scipy.ndimage import map_coordinates
    tw, th = NEB_TILE
    w, h = 576, 1024                 # 2.5 units per texel
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = _pnoise(h, w, th, tw, 200, 1.0, seed + 10)
    wy = _pnoise(h, w, th, tw, 200, 1.0, seed + 11)

    def warp(f, ax, ay, amt):
        return map_coordinates(f, [(yy + ay * amt) % h, (xx + ax * amt) % w], order=1, mode="wrap")

    big = _pnoise(h, w, th, tw, 320, 1.3, seed)
    midw = warp(_pnoise(h, w, th, tw, 110, 1.1, seed + 1), wx, wy, 14)
    finew = warp(_pnoise(h, w, th, tw, 30, 0.8, seed + 2), wx, wy, 10)
    darkw = warp(_pnoise(h, w, th, tw, 100, 1.0, seed + 5), wy, wx, 12)
    hue_a = _pnoise(h, w, th, tw, 300, 1.0, seed + 3)
    hue_b = _pnoise(h, w, th, tw, 260, 1.0, seed + 4)
    base_v = _pnoise(h, w, th, tw, 500, 1.0, seed + 6)
    band = _sstep(-0.3, 1.0, np.cos(_TAU * (xx / w + yy / h) + 1.2 * big))     # periodic diagonal band
    F = big * 0.52 + midw * 0.44 + finew * 0.25
    dens = _sstep(-0.25, 2.05, F + 1.2 * band - 0.6)
    lanes = 1 - 0.68 * _sstep(0.35, 1.45, darkw + 0.35 * finew) * dens
    em = (dens ** 1.55 * 0.9 + 0.32 * _sstep(1.05, 2.45, F + band)) * lanes
    violet, teal, magenta = _hexf("#6A48D8"), _hexf("#2BA3BD"), _hexf("#D04A92")
    wa = np.exp(hue_a * 1.6)
    wb = np.exp(hue_b * 1.6) * 0.9
    wv = np.full_like(wa, 1.2)
    s = wa + wb + wv
    colr = violet * (wv / s)[..., None] + teal * (wa / s)[..., None] + magenta * (wb / s)[..., None]
    neb = colr * em[..., None] * 0.7
    base = (_hexf("#070920") * (1.0 + 0.3 * np.tanh(base_v))[..., None]
            + _hexf("#0C1236") * _sstep(-0.5, 1.5, base_v)[..., None] * 0.6)
    rgb = base + 1.0 - np.exp(-neb * 1.5)
    return rgb.astype(np.float32)


@lru_cache(maxsize=2)
def _nebula_image(seed: int = 7) -> skia.Image:
    return _bgra(_nebula_rgb(seed))


@lru_cache(maxsize=8)
def _star_layer(seed, n, rmin, rmax, amin, amax, tile_w=W, tile_h=H):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, tile_w, n)
    y = rng.uniform(0, tile_h, n)
    u = rng.random(n) ** 2.4
    r = rmin + (rmax - rmin) * u
    a = amin + (amax - amin) * (0.35 * rng.random(n) + 0.65 * u)
    ci = rng.choice(4, n, p=[0.55, 0.2, 0.15, 0.10])
    return x, y, r, a, ci


_STAR_COLS = ["#E8EEFF", "#CFE0FF", "#FFE9CF", "#BFFFF4"]
# (seed, count, rmin, rmax, amin, amax, parallax, speed px/s)
_SPACE_LAYERS = [
    (101, 170, 0.45, 0.95, 0.30, 0.70, 0.30, 5.0),
    (202, 70, 0.75, 1.35, 0.50, 0.90, 0.62, 12.0),
    (303, 22, 1.15, 1.90, 0.75, 1.00, 1.00, 26.0),
]
_HERO_STARS = [(118, 236, 2.0), (604, 418, 1.7), (262, 980, 2.2), (520, 1150, 1.6), (40, 700, 1.5)]


def _glint(canvas, x, y, r, alpha, color="#E8F2FF"):
    """Tiny 4-point glint: soft halo + two thin fading spikes."""
    _glow(canvas, x, y, r * 5, r * 5, color, 0.55 * alpha)
    c = col(color)
    L = r * 6.5
    for dx, dy in ((L, 0), (0, L)):
        sh = skia.GradientShader.MakeLinear([(x - dx, y - dy), (x + dx, y + dy)],
                                            [skia.ColorSetA(c, 0), skia.ColorSetA(c, int(200 * clamp(alpha))),
                                             skia.ColorSetA(c, 0)], [0.0, 0.5, 1.0])
        canvas.drawLine(x - dx, y - dy, x + dx, y + dy, _sp(sh, 1.0, max(0.6, r * 0.36)))
    canvas.drawCircle(x, y, r * 0.75, paint("#FFFFFF", clamp(alpha)))


def _star_dot(canvas, x, y, r, a, color):
    if r < 0.7:                       # sub-pixel: keep a 0.7 px dot and fade instead (crisper)
        a *= r / 0.7
        r = 0.7
    canvas.drawCircle(x, y, r, paint(color, a))


def draw_space(canvas, t, drift=1.0, brightness=1.0, offset=(0.0, 0.0), zoom=1.0) -> None:
    """Deep space backdrop in SCREEN space (identity matrix); fills the 720x1280 frame.

    drift:      speed multiplier of the downward star drift (ship moving "up"); 0 = frozen.
    brightness: 0..1 multiplier for nebula + stars (1 = normal).
    offset:     (dx, dy) screen-px shift of the NEAREST star layer (camera pan); farther layers
                and the nebula move proportionally less (parallax).
    zoom:       camera push (>1 = moving in); each layer scales by zoom**parallax.
    """
    canvas.save()
    canvas.drawRect(skia.Rect(0, 0, W, H), paint("#000000"))
    # ---- nebula (parallax 0.12): opaque texture tiles, drawn without AA so seams are exact
    img = _nebula_image()
    tw, th = NEB_TILE
    par = 0.12
    zl = zoom ** par
    ox = offset[0] * par - 340.0
    oy = offset[1] * par + t * drift * 1.6 - 610.0
    lx0 = (0 - W / 2) / zl + W / 2 - ox
    lx1 = (W - W / 2) / zl + W / 2 - ox
    ly0 = (0 - H / 2) / zl + H / 2 - oy
    ly1 = (H - H / 2) / zl + H / 2 - oy
    p = skia.Paint(AntiAlias=False)
    p.setAlphaf(clamp(brightness))
    src = skia.Rect(0, 0, img.width(), img.height())
    for kx in range(math.floor(lx0 / tw), math.floor(lx1 / tw) + 1):
        for ky in range(math.floor(ly0 / th), math.floor(ly1 / th) + 1):
            u0, v0 = kx * tw, ky * th
            dx0 = (u0 + ox - W / 2) * zl + W / 2
            dy0 = (v0 + oy - H / 2) * zl + H / 2
            canvas.drawImageRect(img, src, skia.Rect(dx0, dy0, dx0 + tw * zl, dy0 + th * zl), _LIN, p,
                                 skia.Canvas.kFast_SrcRectConstraint)
    # ---- star layers
    for (seed, n, rmin, rmax, amin, amax, par, speed) in _SPACE_LAYERS:
        xs, ys, rs, as_, ci = _star_layer(seed, n, rmin, rmax, amin, amax)
        zl = zoom ** par
        ox = offset[0] * par
        oy = offset[1] * par + t * drift * speed
        lx0 = (0 - W / 2) / zl + W / 2 - ox
        lx1 = (W - W / 2) / zl + W / 2 - ox
        ly0 = (0 - H / 2) / zl + H / 2 - oy
        ly1 = (H - H / 2) / zl + H / 2 - oy
        rsc = zl ** 0.5
        for kx in range(math.floor(lx0 / W), math.floor(lx1 / W) + 1):
            for ky in range(math.floor(ly0 / H), math.floor(ly1 / H) + 1):
                sx = (xs + kx * W + ox - W / 2) * zl + W / 2
                sy = (ys + ky * H + oy - H / 2) * zl + H / 2
                vis = np.nonzero((sx > -4) & (sx < W + 4) & (sy > -4) & (sy < H + 4))[0]
                for i in vis:
                    _star_dot(canvas, float(sx[i]), float(sy[i]), float(rs[i] * rsc),
                              float(as_[i] * brightness), _STAR_COLS[ci[i]])
    # ---- hero stars with glints (near-layer motion), very slow gentle twinkle
    speed = _SPACE_LAYERS[-1][7] * 0.8
    for i, (hx, hy, hr) in enumerate(_HERO_STARS):
        ly = (hy + t * drift * speed + offset[1]) % (H + 120) - 60
        lx = (hx + offset[0]) % (W + 120) - 60
        sx = (lx - W / 2) * zoom + W / 2
        sy = (ly - H / 2) * zoom + H / 2
        if -30 < sx < W + 30 and -30 < sy < H + 30:
            tw_ = 0.85 + 0.15 * math.sin(t * 0.8 + i * 1.9)
            _glint(canvas, sx, sy, hr * zoom ** 0.5, brightness * tw_)
    canvas.restore()


# =========================================================================== the Meridian
_SHIP_NOSE, _SHIP_TAIL = -250.0, 168.0
_SHIP_WIDE_Y, _SHIP_HW = -122.0, 44.0
_RING_Y, _RING_R, _RING_W, _RING_K = -52.0, 118.0, 16.0, 0.30
_HERO_WIN = (-2.0, -152.0, 6.4, 8.6)        # glass centre x, y, width, height (arched top)


def _hull_hw(y):
    """Half-width of the slender teardrop hull at local y (rounded nose -250 .. tapered tail 168)."""
    if y <= _SHIP_WIDE_Y:
        v = clamp((y - _SHIP_WIDE_Y) / (_SHIP_NOSE - _SHIP_WIDE_Y), 0, 1)     # 0 widest .. 1 nose
        return _SHIP_HW * (1 - v ** 2.3) ** 0.5
    u = clamp((y - _SHIP_WIDE_Y) / (_SHIP_TAIL - _SHIP_WIDE_Y), 0, 1)
    return 15.0 + (_SHIP_HW - 15.0) * math.cos(u * math.pi / 2) ** 1.3


@lru_cache(maxsize=1)
def _ship_geom():
    g = {}
    # hull outline, denser sampling near the nose
    ts = np.linspace(0, 1, 70)
    ys = _SHIP_NOSE + (_SHIP_TAIL - _SHIP_NOSE) * (1 - np.cos(ts * math.pi / 2))
    ys = np.unique(np.concatenate([ys, np.linspace(-150, _SHIP_TAIL, 30)]))
    right = [(_hull_hw(float(y)), float(y)) for y in ys]
    right[0] = (0.0, _SHIP_NOSE)
    pts = right + [(-x, y) for x, y in reversed(right[1:])]
    g["hull"] = _poly(pts)
    # engine nozzle
    hw_t = _hull_hw(_SHIP_TAIL)
    g["nozzle"] = smooth_path([(-hw_t + 1, _SHIP_TAIL - 2), (hw_t - 1, _SHIP_TAIL - 2), (hw_t + 4, _SHIP_TAIL + 22),
                               (0, _SHIP_TAIL + 25), (-hw_t - 4, _SHIP_TAIL + 22)], closed=True, tension=0.25)
    # fins (right fin; left is mirrored)
    r0 = _hull_hw(-14)
    r1 = _hull_hw(152)
    fin = [(r0 - 3, -14), (r0 + 12, 22), (58, 92), (98, 178), (122, 228), (113, 234), (88, 214), (56, 190),
           (r1 + 8, 172), (r1 - 3, 162)]
    g["fin_r"] = smooth_path(fin, closed=True, tension=0.4)
    g["fin_l"] = smooth_path([(-x, y) for x, y in fin], closed=True, tension=0.4)
    g["fin_line"] = [(r0 + 4, 4), (r0 + 16, 34), (60, 102), (96, 180), (116, 224)]
    g["fin_line2"] = [(r1 + 9, 166), (50, 178), (78, 196)]
    g["fin_tip"] = (118, 230)
    # panel seam stations
    g["seams"] = [-228, -200, -120, -88, -10, 40, 92, 136]
    # windows: (x, y, w, h, lit level 0..1, tone)
    wins = []
    cols = (-0.52, -0.16, 0.22)
    k = 0
    for sec in (np.arange(-212, -78, 12.5), np.arange(-24, 132, 12.5)):
        for y in sec:
            hw = _hull_hw(float(y))
            for ci, u in enumerate(cols):
                if abs(u) * hw + 4 > hw * 0.86:
                    continue
                x = u * hw
                if abs(x - _HERO_WIN[0]) < 8 and abs(y - _HERO_WIN[1]) < 11:
                    continue                                    # room for the hero window
                fs = math.sqrt(max(0.15, 1 - u * u))
                h01 = hash01(k, 31)
                lit = 0.0 if h01 < 0.16 else (0.55 + 0.45 * hash01(k, 77))
                wins.append((x, float(y), 3.0 * fs, 4.4, lit, hash01(k, 5)))
                k += 1
    g["wins"] = wins
    # hero (arched) window
    hx, hy, hwd, hht = _HERO_WIN
    arch = skia.Path()
    rr = hwd / 2
    top = hy - hht / 2
    arch.moveTo(hx - rr, hy + hht / 2)
    arch.lineTo(hx - rr, top + rr)
    arch.arcTo(skia.Rect(hx - rr, top, hx + rr, top + 2 * rr), 180, 180, False)
    arch.lineTo(hx + rr, hy + hht / 2)
    arch.close()
    g["hero"] = arch
    return g


def ship_window(x, y, scale=1.0, angle=0.0):
    """Screen position of the centre of the Meridian's hero window (the lounge window) for a ship
    drawn with draw_ship(canvas, t, x, y, scale, angle)."""
    a = math.radians(angle)
    lx, ly = _HERO_WIN[0] * scale, _HERO_WIN[1] * scale
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


def _ring_pt(th, c=0.0, r=_RING_R):
    return (r * math.cos(th), _RING_Y + c + _RING_K * r * math.sin(th))


def _ring_band(th0, th1, c0, c1, r=_RING_R, n=40):
    pts = []
    for i in range(n + 1):
        th = th0 + (th1 - th0) * i / n
        pts.append(_ring_pt(th, c0, r))
    for i in range(n, -1, -1):
        th = th0 + (th1 - th0) * i / n
        pts.append(_ring_pt(th, c1, r))
    return _poly(pts)


def _ring_curve(th0, th1, c, r=_RING_R, n=40):
    return _poly([_ring_pt(th0 + (th1 - th0) * i / n, c, r) for i in range(n + 1)], close=False)


def draw_ship(canvas, t, x, y, scale=1.0, angle=0.0, glow=1.0) -> None:
    """The Meridian (original design) in SCREEN space.

    (x, y) = ship origin in screen px (the habitat ring sits at y-52*scale); at scale 1 the nose is
    at y-250, the engine nozzle ends at y+193, fin tips reach x+-122 / y+234 and the engine glow
    fades out by ~y+265; the ring spans x+-118. angle in degrees, clockwise, 0 = nose up (-y).
    glow = engine / light-line / window glow 0..1+.
    Readable from scale ~0.3 to 6+; the hero window (ship_window) stays clean at any zoom."""
    g = _ship_geom()
    c = canvas
    c.save()
    c.translate(x, y)
    if angle:
        c.rotate(angle)
    c.scale(scale, scale)
    px = 1.0 / max(scale, 1e-3)              # one device pixel in local units
    om = _TAU / 44.0                          # ring angular speed
    rot = (t * om) % _TAU
    flick = 0.92 + 0.08 * noise1(t * 3.1, 5)

    # ---- engine plume (behind everything)
    _glow(c, 0, _SHIP_TAIL + 70, 30, 95, "#3FA9F5", 0.55 * glow * flick)
    _glow(c, 0, _SHIP_TAIL + 34, 17, 34, "#9FF6FF", 0.75 * glow * flick, kind="core")

    # ---- fins (behind hull)
    for side, path in ((-1, g["fin_l"]), (1, g["fin_r"])):
        lit = side < 0
        sh = _lg(0, 0, side * 120, 230, ["#D3DAE7" if lit else "#A2ADC4", "#8F9BB5" if lit else "#626E8C"])
        c.drawPath(path, _sp(sh))
        c.drawPath(path, paint("#5D6A88", 0.7, stroke=max(0.6, 0.8 * px)))
        for ln, w_ in ((g["fin_line"], 1.0), (g["fin_line2"], 0.8)):
            pts = [(side * a, b) for a, b in ln]
            pth = smooth_path(pts, closed=False)
            c.drawPath(pth, paint("#2EC4B6", 0.45 * clamp(glow), stroke=5.0 * w_))
            c.drawPath(pth, paint("#5FF2DE", 0.9, stroke=max(2.2 * w_, 1.0 * px)))
            c.drawPath(pth, paint("#E0FFF9", 0.9, stroke=max(0.8 * w_, 0.6 * px)))
        # nav light at the fin tip
        bl = 0.5 + 0.5 * math.sin(t * 2.6 + (0 if lit else 1.6))
        bl = smoothstep((bl - 0.55) / 0.45)
        tip = (side * g["fin_tip"][0], g["fin_tip"][1])
        _glow(c, tip[0], tip[1], 9, 9, "#FF8A5C" if lit else "#7FFFE9", 0.85 * bl * glow, kind="core")
        c.drawCircle(tip[0], tip[1], 1.4, paint("#FFE2C8" if lit else "#D8FFF8", 0.5 + 0.5 * bl))

    # ---- habitat ring: far half (inner surface), behind the hull
    c2 = _RING_W / 2
    c.drawPath(_ring_band(math.pi, _TAU, -c2, c2), paint("#6F7B98"))
    c.drawPath(_ring_band(math.pi, _TAU, -c2, -c2 + 3.0), paint("#9AA6C0"))
    c.drawPath(_ring_curve(math.pi, _TAU, c2), paint("#4A5574", stroke=1.0))
    nmod = 6
    for k in range(nmod):
        th = (rot + k * _TAU / nmod) % _TAU
        if math.sin(th) < 0:
            c.drawPath(_ring_band(th - 0.11, th + 0.11, -c2 - 2.2, c2 + 2.2, n=8), paint("#5E6986"))
            for j in (-0.06, 0.0, 0.06):
                wx, wy = _ring_pt(th + j, 0.0)
                c.drawCircle(wx, wy, 1.3, paint("#FFC877", 0.9))
    for k in range(36):                                   # inner windows of the far band
        th = (rot + k * _TAU / 36 + 0.05) % _TAU
        if math.sin(th) < -0.05 and hash01(k, 9) > 0.25:
            wx, wy = _ring_pt(th, 1.5)
            c.drawCircle(wx, wy, 0.9, paint("#FFD29A", 0.75))
    hub_r = _hull_hw(_RING_Y)
    for k in range(3):                                    # far spokes
        th = (rot + 0.5 + k * _TAU / 3) % _TAU
        if math.sin(th) < 0:
            a = _ring_pt(th, 0, hub_r)
            b = _ring_pt(th, 0, _RING_R - 2)
            c.drawLine(*a, *b, paint("#7E89A5", stroke=3.2, cap="butt"))

    # ---- hull
    hull = g["hull"]
    sh = _lg(-_SHIP_HW, 0, _SHIP_HW, 0, ["#A7B2C9", "#E6EBF4", "#F4F6FA", "#D5DCE8", "#97A3BD", "#6A7694"],
             [0.0, 0.18, 0.34, 0.55, 0.82, 1.0])
    c.drawPath(hull, _sp(sh))
    c.save()
    c.clipPath(hull, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect(-60, 20, 60, _SHIP_TAIL + 2), _sp(_lg(0, 20, 0, _SHIP_TAIL, ["#46527000", "#465270B0"])))
    _glow(c, -15, -130, 7, 120, "#FFFFFF", 0.35, kind="soft")
    hw = _hull_hw(_RING_Y + 16)                               # soft shadow of the ring on the hull
    _glow(c, 4, _RING_Y + 16 + 0.25 * hw, hw * 1.1, 9, "#2A3350", 1.0, occl=0.5)
    seam_w = max(0.55, 0.8 * px)
    for ys in g["seams"]:
        hw = _hull_hw(ys)
        pth = skia.Path()
        pth.addArc(skia.Rect(-hw, ys - 0.22 * hw, hw, ys + 0.22 * hw), 0, 180)
        c.drawPath(pth, paint("#6E7A98", 0.55, stroke=seam_w))
    # hub collar band under the ring
    hw = _hull_hw(_RING_Y)
    collar = skia.Path()
    collar.addArc(skia.Rect(-hw, _RING_Y - 6 - 0.3 * hw, hw, _RING_Y - 6 + 0.3 * hw), 0, 180)
    collar.lineTo(-hw, _RING_Y + 6)
    collar.arcTo(skia.Rect(-hw, _RING_Y + 6 - 0.3 * hw, hw, _RING_Y + 6 + 0.3 * hw), 180, -180, False)
    collar.close()
    c.drawPath(collar, _sp(_lg(-hw, 0, hw, 0, ["#7D89A6", "#B4BED2", "#5C6886"], [0, 0.35, 1])))
    tl = skia.Path()
    tl.addArc(skia.Rect(-hw, _RING_Y - 0.3 * hw, hw, _RING_Y + 0.3 * hw), 10, 160)
    c.drawPath(tl, paint("#2EC4B6", 0.35 * clamp(glow), stroke=3.0))
    c.drawPath(tl, paint("#B9FFF5", 0.95, stroke=max(0.9, 0.9 * px)))
    # windows
    for (wx, wy, ww, wh, lit, tone) in g["wins"]:
        if lit <= 0:
            c.drawRRect(_rrect(wx - ww / 2, wy - wh / 2, wx + ww / 2, wy + wh / 2, 1.2), paint("#3A4566", 0.9))
            continue
        _glow(c, wx, wy, 6.0, 7.0, "#FFB060", 0.32 * lit * glow)
        colr = "#FFD9A0" if tone > 0.6 else ("#FFC27A" if tone > 0.25 else "#F4A259")
        c.drawRRect(_rrect(wx - ww / 2, wy - wh / 2, wx + ww / 2, wy + wh / 2, 1.2), paint(colr, 0.55 + 0.45 * lit))
    c.restore()
    # rim light (teal, right edge) + soft outline
    c.save()
    c.clipRect(skia.Rect(6, -300, 80, 220))
    c.drawPath(hull, paint("#8FEAF2", 0.55, stroke=max(1.4, 1.1 * px)))
    c.restore()
    c.drawPath(hull, paint("#56627F", 0.55, stroke=max(0.5, 0.7 * px)))

    # ---- hero window (the lounge's arched window seen from outside)
    _draw_hero_window(c, g, glow, px)

    # ---- engine nozzle
    c.drawPath(g["nozzle"], _sp(_lg(-26, 0, 26, 0, ["#5A6582", "#8D98B2", "#3C4662"], [0, 0.35, 1])))
    c.drawOval(skia.Rect(-17, _SHIP_TAIL + 17, 17, _SHIP_TAIL + 27), paint("#BFFBFF", 0.85 * clamp(glow)))
    _glow(c, 0, _SHIP_TAIL + 22, 26, 12, "#7FFFE9", 0.6 * glow * flick, kind="core")

    # ---- habitat ring: front half (outer surface) + spokes + modules
    for k in range(3):
        th = (rot + 0.5 + k * _TAU / 3) % _TAU
        if math.sin(th) >= 0:
            a = _ring_pt(th, 0, hub_r)
            b = _ring_pt(th, 0, _RING_R - 2)
            c.drawLine(*a, *b, paint("#9AA5BE", stroke=3.4, cap="butt"))
            c.drawLine(*a, *b, paint("#E7ECF5", 0.7, stroke=1.0, cap="butt"))
    band = _ring_band(0, math.pi, -c2, c2)
    c.drawPath(band, _sp(_lg(_RING_R, 0, -_RING_R, 0, ["#7D89A6", "#C9D1E1", "#F1F4F9", "#C0C9DB"],
                             [0.0, 0.45, 0.78, 1.0])))
    c.drawPath(_ring_band(0, math.pi, c2 - 3.2, c2), paint("#56627F", 0.55))
    c.drawPath(_ring_curve(0, math.pi, -c2), paint("#FFFFFF", 0.7, stroke=max(0.6, 0.8 * px)))
    c.drawPath(_ring_curve(0.05, math.pi - 0.05, -0.5), paint("#2EC4B6", 0.25 * clamp(glow), stroke=2.2))
    for k in range(nmod):
        th = (rot + k * _TAU / nmod) % _TAU
        if math.sin(th) >= 0:
            fs = max(0.2, math.sin(th))
            c.drawPath(_ring_band(th - 0.11, th + 0.11, -c2 - 2.4, c2 + 2.4, n=8),
                       _sp(_lg(_RING_R, 0, -_RING_R, 0, ["#8C97B2", "#D9DFEA", "#EEF1F7"])))
            for j in (-0.065, 0.0, 0.065):
                wx, wy = _ring_pt(th + j, 0.5)
                _glow(c, wx, wy, 4.5, 4.5, "#FFB060", 0.3 * glow)
                c.drawRRect(_rrect(wx - 1.3 * fs, wy - 2.0, wx + 1.3 * fs, wy + 2.0, 0.8), paint("#FFD29A", 0.95))
    for th in (0.0, math.pi):                             # ring silhouette edges
        a = _ring_pt(th, -c2)
        b = _ring_pt(th, c2)
        c.drawLine(*a, *b, paint("#6A7694", 0.8, stroke=max(0.6, 0.8 * px), cap="butt"))
    c.restore()


def _draw_hero_window(c, g, glow, px):
    hx, hy, hwd, hht = _HERO_WIN
    arch = g["hero"]
    _glow(c, hx, hy, 16, 18, "#FFB060", 0.55 * glow)
    c.drawPath(arch, paint("#2D3550", 0.9, stroke=2.6))
    c.drawPath(arch, _sp(_lg(hx - 4, hy - 5, hx + 4, hy + 5, ["#FFFFFF", "#C3CCDD", "#8D99B5"]), 1.0, 1.6))
    c.save()
    c.clipPath(arch, skia.ClipOp.kIntersect, True)
    top, bot = hy - hht / 2, hy + hht / 2
    c.drawRect(skia.Rect(hx - 4, top - 1, hx + 4, bot + 1),
               _sp(_lg(0, top, 0, bot, ["#FFE6B5", "#FFC77D", "#F59A4E"], [0, 0.55, 1])))
    _glow(c, hx - 0.6, top + 2.2, 4.5, 3.2, "#FFF6E0", 0.7, kind="soft")
    # a tall, slim figure standing at the window, softly backlit (only readable when very close)
    fx = hx - 1.15
    c.drawOval(skia.Rect(fx - 0.48, hy - 0.55, fx + 0.48, hy + 0.62), paint("#6A4A32", 0.42))
    sil = smooth_path([(fx - 1.05, bot + 0.6), (fx - 0.95, hy + 1.55), (fx - 0.55, hy + 1.18), (fx - 0.16, hy + 1.0),
                       (fx - 0.15, hy + 0.55), (fx + 0.15, hy + 0.55), (fx + 0.16, hy + 1.0), (fx + 0.55, hy + 1.18),
                       (fx + 0.95, hy + 1.55), (fx + 1.05, bot + 0.6)], closed=True, tension=0.35)
    c.drawPath(sil, paint("#6A4A32", 0.4))
    c.drawPath(sil, paint("#FFE9C8", 0.25, stroke=0.08))
    c.drawPath(_poly([(hx - 3.2, hy - 0.8), (hx - 1.4, top - 0.5), (hx - 0.6, top - 0.5), (hx - 2.4, hy + 0.2)]),
               paint("#FFFFFF", 0.28))
    c.restore()
    c.drawPath(arch, paint("#FFF2D8", 0.8, stroke=max(0.25, 0.6 * px)))


# =========================================================================== lounge geometry
def _arch_path(grow: float, bottom: float) -> skia.Path:
    """Arch-topped outline grown by `grow` around the glass, closed at y=bottom."""
    x0, y0, x1, _ = WINDOW
    r = WINDOW_R + grow
    p = skia.Path()
    p.moveTo(x0 - grow, bottom)
    p.lineTo(x0 - grow, WINDOW_SPRING_Y)
    p.arcTo(skia.Rect(WINDOW_CX - r, WINDOW_SPRING_Y - r, WINDOW_CX + r, WINDOW_SPRING_Y + r), 180, 180, False)
    p.lineTo(x1 + grow, bottom)
    p.close()
    return p


@lru_cache(maxsize=1)
def _glass() -> skia.Path:
    return _arch_path(0.0, WINDOW[3])


def _in_glass(x, y):
    """Approximate signed distance (stage units, > 0 inside) to the glass boundary."""
    x0, y0, x1, y1 = WINDOW
    d = min(x - x0, x1 - x, y1 - y)
    if y < WINDOW_SPRING_Y:
        d = min(d, WINDOW_R - math.hypot(x - WINDOW_CX, y - WINDOW_SPRING_Y))
    return d


@lru_cache(maxsize=1)
def _bench_paths():
    """(cushion, bolster, base) paths of the curved upholstered bench."""
    x0, x1 = _BENCH_DRAW
    seat, front = BENCH_SEAT_Y, BENCH_FRONT_Y
    cx = (x0 + x1) / 2
    r = 22.0
    top_e, top_m = seat - 10, seat - 7          # gentle curve: the middle bows toward the camera
    bot_e, bot_m = front - 8, front
    cushion = skia.Path()
    cushion.moveTo(x0 + r, top_e)
    cushion.quadTo(cx, 2 * top_m - top_e, x1 - r, top_e)
    cushion.quadTo(x1, top_e, x1, top_e + r)
    cushion.lineTo(x1, bot_e - r)
    cushion.quadTo(x1, bot_e, x1 - r, bot_e)
    cushion.quadTo(cx, 2 * bot_m - bot_e, x0 + r, bot_e)
    cushion.quadTo(x0, bot_e, x0, bot_e - r)
    cushion.lineTo(x0, top_e + r)
    cushion.quadTo(x0, top_e, x0 + r, top_e)
    cushion.close()
    bolster = skia.Path()
    bolster.addRRect(_rrect(x0 + 12, 902, x1 - 12, seat - 2, 26))
    base = _poly([(x0 + 30, front - 10), (x1 - 30, front - 10), (x1 - 34, FLOOR_Y), (x0 + 34, FLOOR_Y)])
    return cushion, bolster, base


# =========================================================================== lighting states
# amb: albedo multipliers (r,g,b); add: added colour; cove/sconce: practical lights; spill: window
# light into the room; win: window view brightness; con: console glow; haze: room reflection on glass
_STATES = {
    "lit": dict(amb=(1.06, 1.0, 0.93), add=(5, 2, 0), cove=1.0, sconce=1.0, spill=0.2, win=1.0, con=1.0,
                haze=0.12, pool="#F4A259", pool2="#FFD29A", refl=0.32, cozy=0.0),
    "dark": dict(amb=(0.30, 0.34, 0.50), add=(2, 4, 14), cove=0.05, sconce=0.06, spill=1.0, win=1.06, con=0.6,
                 haze=0.0, pool="#F4A259", pool2="#FFD29A", refl=0.45, cozy=0.0),
    "warm": dict(amb=(0.74, 0.52, 0.56), add=(10, 3, 2), cove=0.4, sconce=1.6, spill=0.15, win=0.72, con=0.35,
                 haze=0.22, pool="#F0883A", pool2="#FFC27A", refl=0.2, cozy=1.0),
}


def _shade(S, hexc, a=1.0):
    r, g, b = (int(hexc.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    ar, ag, ab = S["amb"]
    dr, dg, db = S["add"]
    return skia.Color(int(min(255, r * ar + dr)), int(min(255, g * ag + dg)), int(min(255, b * ab + db)),
                      int(255 * clamp(a)))


def _sh(S, hexc, a=1.0, stroke=0.0, cap="round"):
    p = paint("#000000", stroke=stroke, cap=cap)
    p.setColor(_shade(S, hexc, a))
    return p


def _shlg(S, x0, y0, x1, y1, colors, pos=None, alpha=1.0):
    return _sp(skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [_shade(S, c) for c in colors], pos), alpha)


# =========================================================================== the static set
_WV_PAD = 24
_WV_RES = 1.1                     # texels per stage unit of the window view texture


@lru_cache(maxsize=1)
def _window_view_image() -> skia.Image:
    """The space view through the lounge window (static): deep gradient + a soft nebula band that
    runs behind both characters' head positions (Quill ~(545,430), Rae seated ~(230,600)) so their
    silhouettes separate from the background."""
    from scipy.ndimage import map_coordinates
    x0, y0, x1, y1 = WINDOW
    pad = _WV_PAD
    uw, uh = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    w, h = int(uw * _WV_RES), int(uh * _WV_RES)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    U = x0 - pad + (xx + 0.5) / _WV_RES                  # stage coords of each texel
    V = y0 - pad + (yy + 0.5) / _WV_RES

    def n(cut, beta, sd):
        return _pnoise(h, w, uh * 1.0, uw * 1.0, cut, beta, sd)

    wx, wy = n(120, 1.0, 61), n(120, 1.0, 62)

    def warp(f, amt):
        return map_coordinates(f, [(yy + wy * amt) % h, (xx + wx * amt) % w], order=1, mode="wrap")

    big = n(220, 1.2, 51)
    mid = warp(n(70, 1.1, 52), 16)
    fine = warp(n(18, 0.8, 53), 9)
    dark = warp(n(60, 1.0, 57), 12)
    hue_a, hue_b = n(260, 1.0, 55), n(240, 1.0, 56)
    # band through the two head positions (upper-right -> lower-left)
    ax, ay, bx, by = 600.0, 400.0, 150.0, 650.0
    L = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / L, (bx - ax) / L
    d = (U - ax) * nx + (V - ay) * ny + 40 * big + 18 * mid
    band = np.exp(-(d / 170.0) ** 2)
    F = band * 1.4 + big * 0.35 + mid * 0.35 + fine * 0.22
    dens = _sstep(0.15, 1.9, F)
    lanes = 1 - 0.6 * _sstep(0.35, 1.4, dark + 0.3 * fine) * dens
    em = (dens ** 1.4 * 0.8 + 0.25 * _sstep(1.3, 2.4, F)) * lanes
    em += 0.22 * np.exp(-((U - 545) ** 2 + (V - 430) ** 2) / (2 * 120.0 ** 2))       # soft glow behind Quill
    em += 0.22 * np.exp(-((U - 230) ** 2 + (V - 600) ** 2) / (2 * 120.0 ** 2))       # ... and behind Rae
    violet, teal, magenta = _hexf("#6A48D8"), _hexf("#2BA3BD"), _hexf("#D04A92")
    wa = np.exp(hue_a * 1.2 + (U - 360) / 260.0)          # teal toward the right (Quill's side)
    wb = np.exp(hue_b * 1.2 - (U - 360) / 300.0 + (V - 500) / 300.0) * 0.7   # magenta lower left
    wv = np.full_like(wa, 1.4)
    ssum = wa + wb + wv
    colr = violet * (wv / ssum)[..., None] + teal * (wa / ssum)[..., None] + magenta * (wb / ssum)[..., None]
    neb = colr * em[..., None] * 0.52
    gy = np.clip((V - y0) / (y1 - y0), 0, 1)[..., None]
    base = _hexf("#05071A") * (1 - gy) + _hexf("#0D1338") * gy
    rgb = base + 1.0 - np.exp(-neb * 1.5)
    # soft inner shadow along the frame, baked (distance to the glass edge, stage units)
    dist = np.minimum(np.minimum(U - x0, x1 - U), y1 - V)
    arch = WINDOW_R - np.hypot(U - WINDOW_CX, V - WINDOW_SPRING_Y)
    dist = np.where(V < WINDOW_SPRING_Y, np.minimum(dist, arch), dist)
    dist = np.maximum(dist, 0.0)
    vig = 1.0 - 0.55 * np.exp(-dist / 12.0) - 0.28 * np.exp(-dist / 48.0)
    rgb = rgb * vig[..., None]
    return _bgra(rgb.astype(np.float32))


def _draw_window_view(c, S):
    """Space seen through the window (static part): nebula view + inner-edge vignette + sheen."""
    x0, y0, x1, y1 = WINDOW
    img = _window_view_image()
    c.save()
    c.clipPath(_glass(), skia.ClipOp.kIntersect, True)
    c.drawImageRect(img, skia.Rect(x0 - _WV_PAD, y0 - _WV_PAD, x1 + _WV_PAD, y1 + _WV_PAD), _LIN, skia.Paint())
    if S["win"] < 1:
        c.drawRect(skia.Rect(x0, y0, x1, y1), paint("#000000", 1 - S["win"]))
    elif S["win"] > 1:
        _glow(c, WINDOW_CX, 520, 330, 420, "#3A4A9A", (S["win"] - 1) * 3)
    if S["haze"] > 0:                                      # room light reflected in the glass
        _wash(c, x0, y1 - 300, x1, y1, S["pool"], S["haze"] * 1.4, kind="up")
    c.drawPath(_poly([(150, 860), (330, 300), (390, 300), (210, 860)]), paint("#FFFFFF", 0.022))
    c.drawPath(_poly([(420, 860), (560, 420), (585, 420), (445, 860)]), paint("#FFFFFF", 0.018))
    c.restore()


def _draw_door_panel(c, S):
    """Closed sliding door panel occupying the opening (-140..60, 430..1150)."""
    x0, x1, y0, y1 = DOOR_X0, DOOR_X1, DOOR_TOP, FLOOR_Y
    c.drawRect(skia.Rect(x0, y0, x1, y1), _shlg(S, 0, y0, 0, y1, ["#2A3858", "#223050", "#1A2440"]))
    c.drawRRect(_rrect(x0 + 26, y0 + 40, x1 - 34, y1 - 40, 14), _sh(S, "#1B2744"))
    c.drawRRect(_rrect(x0 + 26, y0 + 40, x1 - 34, y1 - 40, 14), _sh(S, "#33456C", 0.9, stroke=2))
    for yy in (y0 + 250, y0 + 470):
        c.drawLine(x0 + 30, yy, x1 - 38, yy, _sh(S, "#121A30", stroke=3))
        c.drawLine(x0 + 30, yy + 3, x1 - 38, yy + 3, _sh(S, "#3A4D78", 0.6, stroke=1.2))
    c.drawRRect(_rrect(x1 - 20, y0 + 60, x1 - 13, y1 - 60, 3.5), paint("#2EC4B6", 0.5 + 0.4 * S["con"]))
    _glow(c, x1 - 16, (y0 + y1) / 2, 18, 330, "#2EC4B6", 0.25 * S["con"], kind="wide")
    c.drawLine(x1 - 2, y0, x1 - 2, y1, _sh(S, "#45588A", 0.8, stroke=3))


@lru_cache(maxsize=1)
def _corridor_picture() -> skia.Picture:
    """Lit corridor seen through the open door (own cool lighting, not dimmed by the lounge)."""
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(DOOR_X0 - 10, DOOR_TOP - 10, DOOR_X1 + 10, FLOOR_Y + 10))
    x0, x1, y0, y1 = DOOR_X0, DOOR_X1, DOOR_TOP, FLOOR_Y
    horizon = 1086
    c.drawRect(skia.Rect(x0, y0, x1, y1), _sp(_lg(0, y0, 0, horizon, ["#24304C", "#56688F", "#6E80A6", "#5A6B90"],
                                                 [0, 0.18, 0.55, 1])))
    c.drawRect(skia.Rect(x0, y0, x1, y0 + 46), paint("#1A2238"))
    c.drawRect(skia.Rect(x0, y0 + 46, x1, y0 + 54), paint("#E6F4FF"))
    _glow(c, -40, y0 + 52, 190, 70, "#BFE4FF", 0.7)
    for xx in (-110, -10, 90):
        c.drawLine(xx, y0 + 60, xx, horizon, paint("#3F4F73", 0.8, stroke=4))
        c.drawLine(xx + 3, y0 + 60, xx + 3, horizon, paint("#8DA0C6", 0.35, stroke=1.5))
    c.drawRect(skia.Rect(x0, 700, x1, 712), paint("#3A4A6E", 0.9))
    c.drawRect(skia.Rect(x0, 712, x1, 716), paint("#7FFFE9", 0.55))
    _glow(c, -40, 714, 220, 26, "#7FFFE9", 0.35)
    c.drawRect(skia.Rect(x0, horizon, x1, y1), _sp(_lg(0, horizon, 0, y1, ["#3B4A6B", "#4F6189", "#2C3858"])))
    c.drawLine(x0, horizon, x1, horizon, paint("#A9BCE0", 0.6, stroke=2))
    _glow(c, -40, 1118, 160, 26, "#DDEBFF", 0.35)
    c.drawPath(_poly([(x0, y0), (x0 + 16, y0 + 12), (x0 + 16, y1 - 8), (x0, y1)]), paint("#151D30"))
    c.drawPath(_poly([(x1, y0), (x1 - 12, y0 + 12), (x1 - 12, y1 - 8), (x1, y1)]), paint("#2B3756"))
    c.drawRect(skia.Rect(x0, y0, x1, y0 + 12), paint("#141B2D"))
    return rec.finishRecordingAsPicture()


def _draw_set(c, S):
    """Draw the complete static lounge for lighting state S (stage coords)."""
    X0, X1 = SET_X
    Y0, Y1 = SET_Y
    wx0, wy0, wx1, wy1 = WINDOW
    pool, pool2 = S["pool"], S["pool2"]
    cv, sp = S["cove"], S["spill"]

    # ---------------- ceiling + back wall
    c.drawRect(skia.Rect(X0, Y0, X1, 44), _sh(S, "#0D1322"))
    c.drawRect(skia.Rect(X0, 44, X1, FLOOR_Y),
               _shlg(S, 0, 44, 0, FLOOR_Y, ["#1F2B48", "#19233D", "#151E35", "#111A2E"], [0, 0.3, 0.7, 1]))
    c.drawRect(skia.Rect(X0, 900, X1, FLOOR_Y), _sh(S, "#0F1628", 0.35))          # wainscot
    for (a, b) in ((X0, DOOR_X0 - 18), (CONSOLE_X[1] - 4, X1)):                    # dado rail
        c.drawRect(skia.Rect(a, 888, b, 898), _sh(S, "#33456C"))
        c.drawRect(skia.Rect(a, 888, b, 890), _sh(S, "#4F6A9E"))
        c.drawRect(skia.Rect(a, 898, b, 902), _sh(S, "#0E1526", 0.8))
    for xx in (-760, -580, -400, 860, 960, 1120, 1300, 1480):                      # panel seams
        c.drawRect(skia.Rect(xx - 1.5, 80, xx + 1.5, FLOOR_Y - 14), _sh(S, "#0C1322", 0.9))
        c.drawRect(skia.Rect(xx + 1.5, 80, xx + 2.5, FLOOR_Y - 14), _sh(S, "#33456C", 0.6))
    for (a, b) in ((-560, -420), (-380, -180), (880, 1100)):
        c.drawRRect(_rrect(a, 120, b, 860, 10), _sh(S, "#2A3A5C", 0.25, stroke=2))

    # ---------------- practical light washes on the walls (additive)
    _wash(c, X0, 66, X1, 360, pool, 0.30 * cv)
    _wash(c, X0, 66, X1, 150, pool2, 0.18 * cv)
    for xx in (-470, -300, 880, 1060):
        _glow(c, xx, 160, 80, 200, pool2, 0.26 * cv, kind="soft")
    for (sx, sy) in SCONCES:
        sc = S["sconce"]
        _glow(c, sx, sy - 120, 80, 260, pool, 0.42 * sc)
        _glow(c, sx, sy + 120, 70, 210, pool, 0.32 * sc)
        _glow(c, sx, sy, 150, 170, pool2, 0.16 * sc, kind="wide")

    _glow(c, (CONSOLE_X[0] + CONSOLE_X[1]) / 2, 810, 130, 170, "#2EC4B6", 0.22 * S["con"], kind="wide")
    # ---------------- window light spilling onto the wall around the window
    _glow(c, WINDOW_CX, 520, 470, 560, "#4A63C8", 0.28 * sp, kind="wide")
    _glow(c, WINDOW_CX, 600, 380, 420, "#7A6AD8", 0.12 * sp, kind="soft")

    # ---------------- door casing + pilaster between door and window
    c.drawRect(skia.Rect(DOOR_X0 - 18, DOOR_TOP - 18, DOOR_X1 + 2, DOOR_TOP),
               _shlg(S, 0, DOOR_TOP - 18, 0, DOOR_TOP, ["#4F6A9E", "#2E4066"]))
    c.drawRect(skia.Rect(DOOR_X0 - 18, DOOR_TOP - 4, DOOR_X0, FLOOR_Y),
               _shlg(S, DOOR_X0 - 18, 0, DOOR_X0, 0, ["#3B5180", "#22304E"]))
    c.drawRect(skia.Rect(DOOR_X1 - 1, 66, WINDOW[0] - 12, FLOOR_Y),
               _shlg(S, DOOR_X1, 0, WINDOW[0] - 12, 0, ["#22304E", "#33497A", "#2A3C64"]))
    c.drawRect(skia.Rect(DOOR_X1 + 9, 120, DOOR_X1 + 12, FLOOR_Y - 30), paint(pool2, 0.25 + 0.35 * cv))
    c.drawRect(skia.Rect(DOOR_X0 - 18, DOOR_TOP - 19, DOOR_X1 + 2, DOOR_TOP - 17), _sh(S, "#6F89BE", 0.7))
    _draw_door_panel(c, S)          # closed; draw_lounge overlays the moving panel when door > 0

    # ---------------- window casing (arched) + glass view
    c.drawPath(_arch_path(16, wy1 + 2), _shlg(S, 0, wy0 - 16, 0, wy1, ["#4A6297", "#2E4066", "#283A60"],
                                               [0, 0.35, 1]))
    c.drawPath(_arch_path(15, wy1 + 2), _sh(S, "#5C78B0", 0.8, stroke=1.5))
    c.drawPath(_arch_path(5, wy1 + 2), _shlg(S, 0, wy0, 0, wy1, ["#C7D1E6", "#8C9AB8", "#6F7E9E"], [0, 0.4, 1]))
    _draw_window_view(c, S)
    c.drawPath(_arch_path(0.5, wy1), paint("#0A0E1A", 0.8, stroke=1.5))
    c.drawPath(_arch_path(4, wy1), paint("#9FB6FF", 0.25 * sp + 0.1, stroke=1.5))

    # ---------------- sill
    c.drawRect(skia.Rect(wx0 - 22, SILL_Y[0], wx1 + 22, SILL_Y[0] + 9),
               _shlg(S, 0, SILL_Y[0], 0, SILL_Y[0] + 9, ["#7D93C2", "#4D6597"]))
    c.drawRect(skia.Rect(wx0 - 22, SILL_Y[0] + 9, wx1 + 22, SILL_Y[1]),
               _shlg(S, 0, SILL_Y[0] + 9, 0, SILL_Y[1], ["#2E4066", "#1D2944"]))
    c.drawRect(skia.Rect(wx0 - 22, SILL_Y[1], wx1 + 22, SILL_Y[1] + 4), _sh(S, "#070B16", 0.7))
    c.drawRect(skia.Rect(wx0 - 22, SILL_Y[0], wx1 + 22, SILL_Y[0] + 1.5), paint("#B9C8F0", 0.35 + 0.3 * sp))
    c.drawRect(skia.Rect(wx0 - 10, SILL_Y[1] - 4, wx1 + 10, SILL_Y[1] - 1.5), paint(pool2, 0.3 + 0.6 * cv))
    _wash(c, wx0 - 30, SILL_Y[1], wx1 + 30, SILL_Y[1] + 120, pool, 0.35 * cv)

    # ---------------- ceiling cove + strip (self-luminous)
    c.drawRect(skia.Rect(X0, 40, X1, 70), _sh(S, "#0A0F1C"))
    c.drawRect(skia.Rect(X0, 68, X1, 72), _sh(S, "#33456C"))
    c.drawRect(skia.Rect(X0, 52, X1, 61), paint(pool2, 0.15 + 0.85 * cv))
    c.drawRect(skia.Rect(X0, 55, X1, 58), paint("#FFF4E0", 0.1 + 0.85 * cv))
    _wash(c, X0, 61, X1, 120, pool2, 0.5 * cv)
    _wash(c, X0, -60, X1, 52, pool, 0.25 * cv, kind="up")

    # ---------------- sconces
    for (sx, sy) in SCONCES:
        sc = S["sconce"]
        c.drawRRect(_rrect(sx - 13, sy - 52, sx + 13, sy + 52, 6), _sh(S, "#22304E"))
        c.drawRRect(_rrect(sx - 9, sy - 46, sx + 9, sy + 46, 9), _shlg(S, sx - 9, 0, sx + 9, 0,
                                                                       ["#8C9AB8", "#4A5A80"]))
        c.drawRRect(_rrect(sx - 5, sy - 44, sx + 5, sy - 34, 4), paint("#FFF1D6", 0.2 + 0.8 * clamp(sc)))
        c.drawRRect(_rrect(sx - 5, sy + 34, sx + 5, sy + 44, 4), paint("#FFF1D6", 0.2 + 0.8 * clamp(sc)))
        _glow(c, sx, sy - 40, 30, 34, pool2, 0.6 * sc, kind="core")
        _glow(c, sx, sy + 40, 28, 30, pool2, 0.5 * sc, kind="core")

    # ---------------- floor
    c.drawRect(skia.Rect(X0, FLOOR_Y, X1, Y1), _shlg(S, 0, FLOOR_Y, 0, FLOOR_Y + 600,
                                                     ["#18213A", "#10172A", "#0B1020"], [0, 0.35, 1]))
    for i, dy in enumerate((26, 60, 104, 160, 232, 322, 434, 570, 740)):
        c.drawRect(skia.Rect(X0, FLOOR_Y + dy, X1, FLOOR_Y + dy + 1.5 + i * 0.25), _sh(S, "#060A14", 0.5))
        c.drawRect(skia.Rect(X0, FLOOR_Y + dy - 1, X1, FLOOR_Y + dy), _sh(S, "#26324F", 0.35))
    rf = S["refl"]
    c.save()
    c.clipRect(skia.Rect(X0, FLOOR_Y, X1, Y1))
    _glow(c, WINDOW_CX, FLOOR_Y, 250, 300, "#4E66C8", 0.5 * rf)                      # window reflection
    _glow(c, WINDOW_CX, FLOOR_Y, 190, 120, "#8FA2F0", 0.3 * rf)
    for (sx, sy) in SCONCES:
        _glow(c, sx, FLOOR_Y, 34, 190, pool, 0.4 * S["sconce"])
    _wash(c, X0, FLOOR_Y, X1, FLOOR_Y + 70, pool, 0.16 * cv)
    _glow(c, (CONSOLE_X[0] + CONSOLE_X[1]) / 2, FLOOR_Y, 40, 170, "#2EC4B6", 0.3 * S["con"])
    c.restore()
    c.drawRect(skia.Rect(X0, FLOOR_Y - 14, X1, FLOOR_Y), _sh(S, "#0B1120"))          # baseboard
    c.drawRect(skia.Rect(X0, FLOOR_Y - 8, X1, FLOOR_Y - 6), paint(pool2, 0.12 + 0.4 * cv))
    c.drawRect(skia.Rect(X0, FLOOR_Y, X1, FLOOR_Y + 1.5), _sh(S, "#33456C", 0.8))
    _wash(c, X0, FLOOR_Y, X1, FLOOR_Y + 26, pool, 0.2 * cv)
    c.drawRect(skia.Rect(DOOR_X0 - 18, FLOOR_Y, DOOR_X1 + 2, FLOOR_Y + 8), _sh(S, "#2A3A5C"))   # threshold

    # ---------------- bench
    cushion, bolster, base = _bench_paths()
    bx0, bx1 = _BENCH_DRAW
    bcx = (bx0 + bx1) / 2
    c.save()
    c.clipRect(skia.Rect(SET_X[0], FLOOR_Y, SET_X[1], SET_Y[1]))
    _glow(c, bcx, FLOOR_Y + 4, (bx1 - bx0) * 0.62, 46, "#000000", 1.0, kind="wide", occl=0.75)
    c.restore()
    c.drawPath(base, _shlg(S, 0, BENCH_FRONT_Y, 0, FLOOR_Y, ["#202A44", "#18203A", "#131A2E"], [0, 0.5, 1]))
    c.drawRect(skia.Rect(bx0 + 30, BENCH_FRONT_Y - 10, bx1 - 30, BENCH_FRONT_Y + 26),
               _sp(_lg(0, BENCH_FRONT_Y - 10, 0, BENCH_FRONT_Y + 26, ["#05080FE0", "#05080F00"])))
    c.drawLine(bx0 + 36, FLOOR_Y - 12, bx1 - 36, FLOOR_Y - 12, _sh(S, "#4F6A9E", 0.6, stroke=1.5))
    c.drawRect(skia.Rect(bx0 + 40, FLOOR_Y - 6, bx1 - 40, FLOOR_Y - 3), paint(pool2, 0.2 + 0.6 * cv))
    _glow(c, bcx, FLOOR_Y + 4, 190, 22, pool, 0.5 * cv + 0.08)
    # back bolster with button tufts
    c.drawPath(bolster, _shlg(S, 0, 902, 0, BENCH_SEAT_Y, ["#2C6672", "#1F4E5A", "#163C46"], [0, 0.5, 1]))
    c.drawLine(bx0 + 30, 931, bx1 - 30, 931, _sh(S, "#143642", 0.6, stroke=2.0))
    c.drawLine(bx0 + 30, 933.5, bx1 - 30, 933.5, _sh(S, "#3F8A94", 0.3, stroke=1.0))
    for i in range(6):
        xx = bx0 + 46 + (bx1 - bx0 - 92) * i / 5
        c.drawCircle(xx, 931, 3.2, _sh(S, "#10303A", 0.9))
        c.drawCircle(xx - 0.8, 930, 1.2, _sh(S, "#5FA8B0", 0.5))
    c.save()
    c.clipPath(bolster, skia.ClipOp.kIntersect, True)
    _wash(c, bx0, 900, bx1, 930, pool2, 0.12 + 0.22 * cv)
    c.restore()
    # seat cushion: top surface highlight + front face shading + piping
    c.drawPath(cushion, _shlg(S, 0, BENCH_SEAT_Y - 10, 0, BENCH_FRONT_Y,
                              ["#3E8792", "#2A6470", "#1F4E5A", "#163A44"], [0, 0.2, 0.5, 1]))
    c.save()
    c.clipPath(cushion, skia.ClipOp.kIntersect, True)
    c.drawPath(smooth_path([(bx0 - 5, BENCH_SEAT_Y + 4), (bcx, BENCH_SEAT_Y + 9), (bx1 + 5, BENCH_SEAT_Y + 4)],
                           closed=False), _sh(S, "#6FB8BE", 0.55, stroke=1.6))
    c.drawPath(smooth_path([(bx0 - 5, BENCH_FRONT_Y - 18), (bcx, BENCH_FRONT_Y - 10), (bx1 + 5, BENCH_FRONT_Y - 18)],
                           closed=False), _sh(S, "#10303A", 0.7, stroke=2.0))
    for i in range(1, 5):                     # soft channel seams on the front face
        xx = bx0 + (bx1 - bx0) * i / 5
        c.drawLine(xx, BENCH_SEAT_Y + 16, xx, BENCH_FRONT_Y - 20, _sh(S, "#163F49", 0.45, stroke=2.2))
    c.restore()
    c.drawPath(cushion, _sh(S, "#0E2830", 0.6, stroke=1.2))
    # rim of window light on the top of the bolster and the seat (cool; strong in the dark state)
    c.drawLine(bx0 + 34, 903, bx1 - 34, 903, paint("#A9BFFF", 0.12 + 0.4 * sp, stroke=1.5))
    c.drawPath(smooth_path([(bx0 + 20, BENCH_SEAT_Y - 9), (bcx, BENCH_SEAT_Y - 7), (bx1 - 20, BENCH_SEAT_Y - 9)],
                           closed=False), paint("#A9BFFF", 0.08 + 0.35 * sp, stroke=1.5))

    # ---------------- console pillar (floor-to-ceiling, integrated panel)
    cx0, cx1 = CONSOLE_X
    ccx = (cx0 + cx1) / 2
    con = S["con"]
    c.drawRect(skia.Rect(cx0 + 8, 66, cx1 - 8, FLOOR_Y),
               _shlg(S, cx0 + 8, 0, cx1 - 8, 0, ["#3A4B72", "#2A3858", "#1C2640", "#151D33"], [0, 0.3, 0.7, 1]))
    c.drawRect(skia.Rect(cx0 + 8, 66, cx0 + 10, FLOOR_Y), _sh(S, "#5C78B0", 0.6))
    c.drawRect(skia.Rect(cx0 + 2, 66, cx1 - 2, 96), _shlg(S, 0, 66, 0, 96, ["#2E4066", "#22304E"]))
    c.drawRect(skia.Rect(cx0 + 2, 1118, cx1 - 2, FLOOR_Y), _shlg(S, 0, 1118, 0, FLOOR_Y, ["#2E4066", "#1A2238"]))
    c.drawRect(skia.Rect(cx0 + 2, 1118, cx1 - 2, 1120), _sh(S, "#5C78B0", 0.7))
    for (ya, yb) in ((110, 736), (892, 1104)):                      # vertical light lines
        c.drawRect(skia.Rect(ccx - 1.3, ya, ccx + 1.3, yb), paint("#2EC4B6", 0.2 + 0.35 * con))
        _glow(c, ccx, (ya + yb) / 2, 9, (yb - ya) / 2 + 20, "#2EC4B6", 0.22 * con)
    # panel housing + glowing screen
    c.drawRRect(_rrect(cx0 - 3, CONSOLE_PANEL_Y[0] - 8, cx1 + 3, CONSOLE_PANEL_Y[1] + 22, 9), _sh(S, "#0E1526"))
    c.drawRRect(_rrect(cx0 - 3, CONSOLE_PANEL_Y[0] - 8, cx1 + 3, CONSOLE_PANEL_Y[1] + 22, 9),
                _sh(S, "#4F6A9E", 0.8, stroke=1.5))
    scr = skia.Rect(cx0 + 6, CONSOLE_PANEL_Y[0] + 2, cx1 - 6, CONSOLE_PANEL_Y[1] - 2)
    c.drawRRect(skia.RRect.MakeRectXY(scr, 5, 5),
                _sp(_lg(0, scr.top(), 0, scr.bottom(), ["#17707A", "#0F4550", "#0B2F38"], [0, 0.6, 1]), 0.45 + 0.55 * con))
    for (ww, yy) in ((44, 776), (28, 788), (50, 800), (20, 812)):
        c.drawRect(skia.Rect(cx0 + 13, yy, cx0 + 13 + ww, yy + 2.5), paint("#7FFFE9", 0.25 + 0.4 * con))
    c.drawCircle(cx1 - 19, 832, 8, paint("#7FFFE9", 0.3 + 0.4 * con, stroke=1.5))
    c.drawLine(cx0 + 13, 846, cx1 - 30, 846, paint("#7FFFE9", 0.2 + 0.3 * con, stroke=1.0))
    _glow(c, ccx, 806, 46, 50, "#2EC4B6", 0.35 * con)
    c.drawRRect(_rrect(cx0 + 8, 864, cx1 - 8, 876, 5), _sh(S, "#070B16"))

    # ---------------- window light falling forward into the room (dark state)
    _glow(c, WINDOW_CX - 40, 990, 360, 120, "#5E78E0", 0.12 * sp, kind="wide")
    # ---------------- cozy warm pool around the bench (lullaby)
    if S.get("cozy", 0) > 0:
        _glow(c, 320, 860, 560, 460, "#E07A30", 0.30 * S["cozy"], kind="wide")
        _glow(c, 320, 1150, 380, 100, "#F08A3C", 0.3 * S["cozy"])


@lru_cache(maxsize=4)
def _set_picture(state: str) -> skia.Picture:
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(SET_X[0], SET_Y[0], SET_X[1], SET_Y[1]))
    _draw_set(c, _STATES[state])
    return rec.finishRecordingAsPicture()


@lru_cache(maxsize=4)
def _door_panel_picture(state: str) -> skia.Picture:
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(DOOR_X0 - 10, DOOR_TOP - 10, DOOR_X1 + 10, FLOOR_Y + 10))
    _draw_door_panel(c, _STATES[state])
    return rec.finishRecordingAsPicture()


# =========================================================================== raster tile cache
class _TileCache:
    """Rasterised tiles of the static set Picture, keyed by (state, resolution bucket); each tile
    covers the camera view plus a margin. LRU, bounded by total pixels."""

    def __init__(self, budget_px=48_000_000):
        self.entries = OrderedDict()
        self.budget = budget_px
        self.pixels = 0
        self.misses = 0

    def get(self, state, res, vis: skia.Rect):
        for key in reversed(list(self.entries.keys())):
            rect, img = self.entries[key]
            if key[0] == state and key[1] == res and rect.contains(vis):
                self.entries.move_to_end(key)
                return rect, img
        self.misses += 1
        mw = max(vis.width() * 0.45, 120)
        mh = max(vis.height() * 0.35, 120)
        g = 64.0
        x0 = math.floor(max(vis.left() - mw, SET_X[0]) / g) * g
        y0 = math.floor(max(vis.top() - mh, SET_Y[0]) / g) * g
        x1 = math.ceil(min(vis.right() + mw, SET_X[1]) / g) * g
        y1 = math.ceil(min(vis.bottom() + mh, SET_Y[1]) / g) * g
        rect = skia.Rect(x0, y0, x1, y1)
        iw, ih = max(1, int(math.ceil((x1 - x0) * res))), max(1, int(math.ceil((y1 - y0) * res)))
        surf = skia.Surface(iw, ih)
        cc = surf.getCanvas()
        cc.clear(skia.ColorBLACK)
        cc.scale(iw / (x1 - x0), ih / (y1 - y0))
        cc.translate(-x0, -y0)
        cc.drawPicture(_set_picture(state))
        img = surf.makeImageSnapshot()
        key = (state, res, x0, y0, x1, y1)
        self.entries[key] = (rect, img)
        self.pixels += iw * ih
        while self.pixels > self.budget and len(self.entries) > 1:
            _, (_, im) = self.entries.popitem(last=False)
            self.pixels -= im.width() * im.height()
        return rect, img


_TILES = _TileCache()


def _res_bucket(z):
    return 2.0 ** (math.ceil(math.log2(max(z, 0.25)) * 4 - 1e-6) / 4.0)


def _state_weights(light, warm):
    """[(state, alpha)] composited bottom-up: first entry opaque, later ones cross-faded on top."""
    f = clamp((max(0.0, light) - 0.25) / 0.75)
    w = clamp(warm)
    if f >= 0.999:
        layers = [("lit", 1.0)]
    elif f <= 0.001:
        layers = [("dark", 1.0)]
    else:
        layers = [("dark", 1.0), ("lit", f)]
    if w >= 0.999:
        layers = [("warm", 1.0)]
    elif w > 0.001:
        layers.append(("warm", w))
    return layers


def _blit_set(canvas, light, warm, clip: skia.Rect | None = None):
    vis = canvas.getLocalClipBounds()
    if clip is not None and not vis.intersect(clip):
        return
    res = _res_bucket(_mscale(canvas))
    for state, a in _state_weights(light, warm):
        rect, img = _TILES.get(state, res, vis)
        p = skia.Paint(AntiAlias=False)
        if a < 1:
            p.setAlphaf(a)
        canvas.drawImageRect(img, skia.Rect(0, 0, img.width(), img.height()), rect, _LIN, p,
                             skia.Canvas.kFast_SrcRectConstraint)
    if light < 0.25:
        canvas.drawRect(vis, paint("#000000", 1 - max(0.0, light) / 0.25))
    elif light > 1.0:
        _glow(canvas, (vis.left() + vis.right()) / 2, (vis.top() + vis.bottom()) / 2,
              vis.width() * 0.9, vis.height() * 0.9, "#FFE6C0", (light - 1.0) * 0.35, kind="wide")


# =========================================================================== window: stars + galaxy
_G_PITCH_B = 1.0 / math.tan(math.radians(15.0))
_G_R0 = 26.0
_G_RADIUS = 330.0
_G_Q = 0.80                 # inclination (minor/major)
_G_PA = -24.0               # position angle, degrees


def _arm_phase(r):
    return _G_PITCH_B * np.log(np.maximum(r, 1e-3) / _G_R0)


@lru_cache(maxsize=1)
def _window_stars():
    rng = np.random.default_rng(4242)
    n = 260
    x0, y0, x1, y1 = WINDOW
    xs = rng.uniform(x0 - 10, x1 + 10, n)
    ys = rng.uniform(y0 - 30, y1 + 30, n)
    u = rng.random(n) ** 2.3
    r = 0.55 + 1.15 * u                                   # device px at zoom 1
    a = 0.35 + 0.65 * (0.4 * rng.random(n) + 0.6 * u)
    speed = np.where(rng.random(n) < 0.6, 1.1, 2.6) * (0.85 + 0.3 * rng.random(n))
    ci = rng.choice(4, n, p=[0.55, 0.2, 0.15, 0.10])
    gr = np.clip(rng.gamma(2.0, 62.0, n) + 18, 20, 300)  # galaxy-plane radius of the swirl target
    arm = rng.integers(0, 2, n)
    disk = rng.random(n) < 0.22
    jitter = rng.normal(0, 1, n)
    gphi = np.where(disk, rng.uniform(0, _TAU, n), _arm_phase(gr) + arm * math.pi + jitter * (0.16 + 9.0 / gr))
    stagger = rng.random(n) * 0.28
    extra = (rng.random(n) < 0.35).astype(float)
    return dict(x=xs, y=ys, r=r, a=a, speed=speed, ci=ci, gr=gr, gphi=gphi, stagger=stagger, extra=extra)


@lru_cache(maxsize=2)
def _galaxy_image(n: int = 560) -> skia.Image:
    """Face-on two-armed spiral galaxy as an additive premultiplied sprite (radius _G_RADIUS)."""
    R = _G_RADIUS
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x = (xx - (n - 1) / 2) / (n / 2) * R
    y = (yy - (n - 1) / 2) / (n / 2) * R
    r = np.sqrt(x * x + y * y) + 1e-3
    phi = np.arctan2(y, x)
    sig = 15.0 + 0.13 * r
    arms = np.zeros_like(r)
    dust = np.zeros_like(r)
    base = _arm_phase(r)
    for k in range(2):
        d = np.angle(np.exp(1j * (phi - base - k * math.pi)))
        s = d * r
        arms += np.exp(-(s * s) / (2 * sig * sig)) + 0.3 * np.exp(-(s * s) / (2 * (2.6 * sig) ** 2))
        dd = s + 0.9 * sig
        dust += np.exp(-(dd * dd) / (2 * (0.38 * sig) ** 2))
    clump = _pnoise(n, n, 2 * R, 2 * R, 9.0, 0.6, 99)
    clump2 = _pnoise(n, n, 2 * R, 2 * R, 26.0, 1.0, 98)
    env_arm = _sstep(18, 85, r) * np.exp(-r / 165.0) * (1 - _sstep(230, 322, r))
    arms_e = (arms * env_arm * (0.62 + 0.5 * _sstep(-0.6, 1.4, clump) + 0.2 * clump2)
              * (1 - np.clip(1.1 * dust * env_arm, 0, 0.8)))
    bulge = np.exp(-(r / 26.0) ** 2) * 1.6 + np.exp(-r / 62.0) * 0.55 + np.exp(-(r / 110.0) ** 2) * 0.22
    diskl = np.exp(-r / 115.0) * 0.32 * (1 - _sstep(250, 328, r)) * (0.8 + 0.2 * clump2)
    t_in = _sstep(40, 200, r)[..., None]
    arm_col = _hexf("#FFE1B5") * (1 - t_in) + _hexf("#8FB4FF") * t_in
    edge_teal = _sstep(170, 290, r)[..., None]
    arm_col = arm_col * (1 - 0.45 * edge_teal) + _hexf("#7FE8F0") * 0.45 * edge_teal
    E = (bulge[..., None] * _hexf("#FFF0D8") * 0.85 + arms_e[..., None] * arm_col * 1.9
         + diskl[..., None] * _hexf("#7C68D8"))
    rng = np.random.default_rng(5)
    for i in range(60):                                   # star-forming knots along the arms
        rr = rng.uniform(70, 280)
        k = rng.integers(0, 2)
        ph = float(_arm_phase(np.array(rr))) + k * math.pi + rng.normal(0, 0.12)
        kx, ky = rr * math.cos(ph), rr * math.sin(ph)
        rad = rng.uniform(2.6, 5.5)
        x0i, x1i = int((kx - 4 * rad) / R * n / 2 + n / 2), int((kx + 4 * rad) / R * n / 2 + n / 2) + 1
        y0i, y1i = int((ky - 4 * rad) / R * n / 2 + n / 2), int((ky + 4 * rad) / R * n / 2 + n / 2) + 1
        x0i, y0i, x1i, y1i = max(0, x0i), max(0, y0i), min(n, x1i), min(n, y1i)
        sub = (slice(y0i, y1i), slice(x0i, x1i))
        gk = np.exp(-((x[sub] - kx) ** 2 + (y[sub] - ky) ** 2) / (2 * rad * rad))
        cc = _hexf("#FF7FC0") if i % 3 == 0 else _hexf("#BFD8FF")
        E[sub] += gk[..., None] * cc * rng.uniform(0.25, 0.6)
    rgb = 1.0 - np.exp(-E * 1.15)
    fade = (1 - _sstep(0.86 * R, 0.99 * R, r))[..., None]
    rgb = (rgb * fade).astype(np.float32)
    return _bgra(rgb, np.zeros(rgb.shape[:2], np.float32))


def _galaxy_rot(t, s):
    """In-plane rotation (deg) of the galaxy: slow constant spin + spin-in while forming."""
    e = smoothstep(s)
    return -t * 3.2 - (1 - e) ** 2 * 140.0


def _galaxy_to_stage(gx, gy, t, s):
    """Galaxy-plane coords (arrays) -> stage coords for the current rotation / formation scale."""
    e = smoothstep(s)
    sc = 1.0 + 0.25 * (1 - e)
    a = math.radians(_galaxy_rot(t, s))
    ca, sa = math.cos(a), math.sin(a)
    x1 = (gx * ca - gy * sa) * sc
    y1 = (gx * sa + gy * ca) * sc * _G_Q
    p = math.radians(_G_PA)
    cp, spa = math.cos(p), math.sin(p)
    return GALAXY_CENTER[0] + x1 * cp - y1 * spa, GALAXY_CENTER[1] + x1 * spa + y1 * cp


_GAL_SURF = {}


def _galaxy_layer(t, s, z, vis: skia.Rect | None = None, base_alpha: float = 0.0):
    """Render the rotating, tilted galaxy into a small stage-aligned offscreen (rotated image draws
    are ~10x slower than axis-aligned blits here, so we rotate at low resolution and upscale).
    Only the visible part of the window is rendered (vis = local clip bounds)."""
    x0, y0, x1, y1 = WINDOW
    rx0, ry0, rx1, ry1 = x0 - 8, y0 - 8, x1 + 8, y1 + 8
    if vis is not None:
        rx0, ry0 = max(rx0, math.floor(vis.left() / 16) * 16 - 16), max(ry0, math.floor(vis.top() / 16) * 16 - 16)
        rx1, ry1 = min(rx1, math.ceil(vis.right() / 16) * 16 + 16), min(ry1, math.ceil(vis.bottom() / 16) * 16 + 16)
        if rx1 <= rx0 or ry1 <= ry0:
            return None, None
    res = clamp(z * 0.45, 0.3, 0.75)
    iw, ih = int(math.ceil((rx1 - rx0) * res)), int(math.ceil((ry1 - ry0) * res))
    key = (int(math.ceil(iw / 32.0)) * 32, int(math.ceil(ih / 32.0)) * 32)
    surf = _GAL_SURF.get(key)
    if surf is None:
        if len(_GAL_SURF) > 8:
            _GAL_SURF.clear()
        surf = _GAL_SURF[key] = skia.Surface(*key)
    cc = surf.getCanvas()
    cc.clear(skia.Color4f(0, 0, 0, clamp(base_alpha)))       # black veil: dims what is behind
    cc.save()
    cc.clipRect(skia.Rect(0, 0, iw, ih))
    cc.scale(iw / (rx1 - rx0), ih / (ry1 - ry0))
    cc.translate(-rx0, -ry0)
    e = smoothstep(s)
    sc = 1.0 + 0.25 * (1 - e)
    cc.translate(*GALAXY_CENTER)
    cc.rotate(_G_PA)
    cc.scale(sc, sc * _G_Q)
    cc.rotate(_galaxy_rot(t, s))
    cc.drawImageRect(_galaxy_image(), skia.Rect(-_G_RADIUS, -_G_RADIUS, _G_RADIUS, _G_RADIUS), _LIN, skia.Paint())
    cc.restore()
    return surf.makeImageSnapshot(skia.IRect(0, 0, iw, ih)), skia.Rect(rx0, ry0, rx1, ry1)


def _draw_window_dynamic(c, t, swirl, wb, rain, warm, z):
    x0, y0, x1, y1 = WINDOW
    s = clamp(swirl)
    e = smoothstep(s)
    wbv = max(0.0, wb) * (1 - 0.25 * clamp(warm))
    c.save()
    c.clipPath(_glass(), skia.ClipOp.kIntersect, True)
    dim = 1 - (1 - 0.5 * e) * min(1.0, wbv)             # galaxy gathers the nebula in / wb < 1
    ga = e * min(1.0, wbv)
    # the galaxy layer carries a black veil that also does the dimming (saves a full blend pass)
    veil = clamp(dim / ga) if (s > 0.002 and ga > 1e-3) else 0.0
    if dim > 0.01 and (s <= 0.002 or abs(veil * ga - dim) > 0.01):
        c.drawRect(skia.Rect(x0, y0, x1, y1), paint("#020309", dim))
        veil = 0.0
    # ---- galaxy
    img = rect = None
    if s > 0.002:
        img, rect = _galaxy_layer(t, s, z, c.getLocalClipBounds(), veil)
    if img is not None:
        src = skia.Rect(0, 0, img.width(), img.height())
        p = skia.Paint()
        p.setAlphaf(clamp(ga))
        c.drawImageRect(img, src, rect, _LIN, p, skia.Canvas.kFast_SrcRectConstraint)
        if wbv > 1.0:                                     # blaze: second additive pass
            p.setAlphaf(clamp(0.5 * (wbv - 1.0) * e))
            c.drawImageRect(img, src, rect, _LIN, p, skia.Canvas.kFast_SrcRectConstraint)
        breath = 1.0 + 0.05 * math.sin(t * 1.3)
        _glow(c, GALAXY_CENTER[0], GALAXY_CENTER[1], 60 * breath, 50 * breath, "#FFE6C4", 0.75 * e * min(1.4, wbv),
              kind="core")
    # ---- stars (drift slowly; swirl into the galaxy arms)
    st = _window_stars()
    span = (y1 + 30) - (y0 - 30)
    by = (st["y"] - (y0 - 30) + t * st["speed"]) % span + (y0 - 30)
    bx = st["x"]
    if s > 0.002:
        tx, ty = _galaxy_to_stage(st["gr"] * np.cos(st["gphi"]), st["gr"] * np.sin(st["gphi"]), t, s)
        cx_, cy_ = GALAXY_CENTER
        r0 = np.hypot(bx - cx_, by - cy_)
        a0 = np.arctan2(by - cy_, bx - cx_)
        r1 = np.hypot(tx - cx_, ty - cy_)
        a1 = np.arctan2(ty - cy_, tx - cx_)
        ee = np.clip((s - st["stagger"]) / (1 - 0.28), 0, 1)
        ee = ee * ee * (3 - 2 * ee)
        er = np.clip(ee * 1.15 - 0.15, 0, 1)
        er = er * er * (3 - 2 * er)
        da = (a0 - a1) % _TAU + _TAU * st["extra"]       # travel = galaxy spin direction (counter-cw)
        ang = a0 - da * ee
        rad = r0 + (r1 - r0) * er
        px_ = cx_ + rad * np.cos(ang)
        py_ = cy_ + rad * np.sin(ang)
    else:
        px_, py_ = bx, by
        ee = np.zeros_like(bx)
    zr = z ** 0.3
    bright = min(1.25, wbv) * (1 + 0.35 * e)
    for i in range(len(px_)):
        x, y = float(px_[i]), float(py_[i])
        d = _in_glass(x, y)
        if d < -2:
            continue
        yb = by[i]
        a = (st["a"][i] * bright * clamp((d + 2) / 6)
             * clamp((yb - (y0 - 30)) / 25) * clamp(((y1 + 30) - yb) / 25))   # no pop at the wrap
        if a <= 0.01:
            continue
        rpx = st["r"][i] * (1 + 0.3 * ee[i]) * zr
        if rpx < 0.7:
            a *= rpx / 0.7
            rpx = 0.7
        c.drawCircle(x, y, rpx / z, paint(_STAR_COLS[st["ci"][i]], min(1.0, a)))
    if rain > 0.003:
        _draw_rain(c, t, clamp(rain))
    c.restore()


@lru_cache(maxsize=1)
def _rain_data():
    rng = np.random.default_rng(77)
    x0, y0, x1, y1 = WINDOW
    drops = [(rng.uniform(x0 + 8, x1 - 8), rng.uniform(0, 1), rng.uniform(60, 140), rng.uniform(2.6, 4.6),
              rng.uniform(90, 260), rng.uniform(0, _TAU)) for _ in range(34)]
    beads = [(rng.uniform(x0 + 6, x1 - 6), rng.uniform(y0 + 10, y1 - 6), rng.uniform(1.4, 3.6)) for _ in range(110)]
    return drops, beads


def _draw_rain(c, t, rain):
    x0, y0, x1, y1 = WINDOW
    drops, beads = _rain_data()
    c.drawRect(skia.Rect(x0, y0, x1, y1), paint("#7F93BC", 0.13 * rain))
    for (bx, by, br) in beads:
        if _in_glass(bx, by) < 3:
            continue
        c.drawCircle(bx, by + br * 0.25, br, paint("#0A0F22", 0.25 * rain))
        c.drawCircle(bx, by, br, paint("#B8C9EE", 0.3 * rain))
        c.drawCircle(bx - br * 0.3, by - br * 0.35, br * 0.38, paint("#FFFFFF", 0.55 * rain))
    span = (y1 - y0) + 220
    for (dx, ph, speed, rad, trail, wph) in drops:
        yy = y0 - 60 + ((ph * span + t * speed) % span)
        xx = dx + 3.0 * math.sin(yy * 0.03 + wph)
        tl = smooth_path([(dx + 3.0 * math.sin((yy - k) * 0.03 + wph), yy - k)
                          for k in (trail, trail * 0.6, trail * 0.3, 0)], closed=False)
        c.drawPath(tl, paint("#AFC3EC", 0.22 * rain, stroke=rad * 1.1))
        c.drawPath(tl, paint("#FFFFFF", 0.18 * rain, stroke=rad * 0.35))
        c.drawCircle(xx, yy + rad * 0.3, rad * 1.05, paint("#0A0F22", 0.3 * rain))
        c.drawCircle(xx, yy, rad, paint("#C8D7F6", 0.5 * rain))
        c.drawCircle(xx - rad * 0.3, yy - rad * 0.35, rad * 0.4, paint("#FFFFFF", 0.75 * rain))


def _draw_console_lights(c, t, con):
    cx0, cx1 = CONSOLE_X
    for i, colr in enumerate(("#2EC4B6", "#F4A259", "#FF5D73", "#7FFFE9", "#F4A259")):
        x = cx0 + 16 + i * 12.0
        per = 2.2 + 0.9 * hash01(i, 3)
        ph = 0.5 + 0.5 * math.sin(_TAU * t / per + i * 1.7)
        a = 0.25 + 0.75 * smoothstep((ph - 0.35) / 0.65)
        c.drawCircle(x, 870, 2.4, paint(colr, (0.4 + 0.6 * con) * a))
        _glow(c, x, 870, 9, 9, colr, 0.5 * con * a, kind="core")
    sx = cx0 + 8 + ((t * 18.0) % 62)                     # slow scanning highlight on the screen
    c.drawRect(skia.Rect(sx, CONSOLE_PANEL_Y[0] + 4, sx + 3, CONSOLE_PANEL_Y[1] - 4), paint("#B9FFF5", 0.10 * con))


def _draw_door_dynamic(c, door, light, warm):
    d = clamp(door)
    cushion, bolster, base = _bench_paths()
    c.save()
    c.clipRect(skia.Rect(DOOR_X0, DOOR_TOP, DOOR_X1, FLOOR_Y), True)
    c.clipPath(cushion, skia.ClipOp.kDifference, True)
    c.clipPath(bolster, skia.ClipOp.kDifference, True)
    c.drawPicture(_corridor_picture())
    dom = max(_state_weights(light, warm), key=lambda s: s[1])[0]
    c.translate(-DOOR_W * d, 0)
    c.drawPicture(_door_panel_picture(dom))
    c.restore()
    _glow(c, DOOR_CX + 30, FLOOR_Y + 70, 150 * (0.4 + 0.6 * d), 80, "#BFE4FF", 0.30 * d, kind="wide")
    _glow(c, DOOR_X1 - 10, 800, 40, 300, "#BFE4FF", 0.10 * d, kind="soft")


def _draw_door_status(c, door, light):
    """Little status light on the lintel: amber when closed, teal when open."""
    d = clamp(door * 3)
    hexc = "#%02X%02X%02X" % (int(lerp(0xF4, 0x7F, d)), int(lerp(0xA2, 0xFF, d)), int(lerp(0x59, 0xE9, d)))
    c.drawRRect(_rrect(DOOR_CX - 22, DOOR_TOP - 12, DOOR_CX + 22, DOOR_TOP - 7, 2.5),
                paint(hexc, 0.55 + 0.45 * clamp(light)))
    _glow(c, DOOR_CX, DOOR_TOP - 9, 40, 14, hexc, 0.45 * clamp(light), kind="core")


# =========================================================================== public: lounge
def draw_lounge(canvas, t, light=1.0, door=0.0, swirl=0.0, window_bright=1.0, rain=0.0, warm=0.0) -> None:
    """The observation lounge, BEHIND the characters. STAGE coords (apply the Camera first).

    light:  1 warm amber interior .. 0.25 dark-blue symphony lighting (window stays bright);
            < 0.25 darkens further, > 1 floods the room with warm light.
    door:   0 closed .. 1 fully open (panel slides left into the wall, lit corridor behind).
    swirl:  0..1 window stars gather into a spiral galaxy with a bright core (S2 climax).
    window_bright: multiplier for the window view (> 1 = blazing galaxy / brighter view).
    rain:   0..1 rain streaks and beads on the window glass (lo-fi gag).
    warm:   0..1 cozy warm dim lighting (lullaby).
    """
    c = canvas
    z = _mscale(c)
    _blit_set(c, light, warm)
    if door > 0.001:
        _draw_door_dynamic(c, door, light, warm)
    _draw_door_status(c, door, light)
    _draw_window_dynamic(c, t, swirl, window_bright, rain, warm, z)
    s = smoothstep(clamp(swirl))
    wb = max(0.0, window_bright)
    dark = 1 - clamp((light - 0.25) / 0.75)
    if s > 0.002 or wb > 1.0:                 # galaxy light spilling into the room + floor reflection
        k = s * min(2.0, wb) * (0.35 + 0.65 * dark)
        _glow(c, GALAXY_CENTER[0], GALAXY_CENTER[1] + 50, 480, 560, "#A892F4",
              0.11 * k + 0.14 * max(0.0, wb - 1.0), kind="wide")
        c.save()
        c.clipRect(skia.Rect(SET_X[0], FLOOR_Y, SET_X[1], SET_Y[1]))
        _glow(c, GALAXY_CENTER[0], FLOOR_Y + 30, 420, 170, "#B8A8FF", 0.13 * k, kind="wide")   # light on floor
        _glow(c, GALAXY_CENTER[0], FLOOR_Y, 120, 150, "#FFE2B8", 0.10 * k)
        c.restore()
    _draw_console_lights(c, t, (1 - 0.4 * dark) * (1 - 0.5 * clamp(warm)))


def draw_lounge_front(canvas, t, light=1.0, door=0.0, warm=0.0, lintel=True) -> None:
    """Foreground pieces of the lounge, drawn AFTER the characters (STAGE coords).

    Re-draws the wall + jamb left of the door opening (x < -140) and, with lintel=True, the door
    header above y=430, so a character walking through the door is occluded by the frame; plus a
    soft floor-edge shadow at the very bottom of wide shots (y > 1450). Pass the same light / warm
    as draw_lounge."""
    c = canvas
    r = skia.Rect(SET_X[0], SET_Y[0], DOOR_X0, FLOOR_Y + 12)
    c.save()
    c.clipRect(r, True)
    _blit_set(c, light, warm, r)
    c.restore()
    if lintel:
        r = skia.Rect(DOOR_X0 - 18, SET_Y[0], DOOR_X1 + 2, DOOR_TOP)
        c.save()
        c.clipRect(r, True)
        _blit_set(c, light, warm, r)
        _draw_door_status(c, door, light)
        c.restore()
    d = clamp(door)
    if d > 0.001:                              # corridor light catching the inner edge of the jamb
        c.drawRect(skia.Rect(DOOR_X0 - 3, DOOR_TOP, DOOR_X0, FLOOR_Y), paint("#BFE4FF", 0.35 * d))
    c.drawRect(skia.Rect(SET_X[0], 1450, SET_X[1], SET_Y[1]),
               _sp(_lg(0, 1450, 0, 1650, ["#03050A00", "#03050A99"])))


def char_light(light=1.0, warm=0.0, swirl=0.0, window_bright=1.0) -> dict:
    """Suggested Pose lighting fields for characters in the lounge (optional helper):
    dict(light, tint, tint_amt, rim, rim_color)."""
    dark = 1 - clamp((light - 0.25) / 0.75)
    w = clamp(warm)
    s = smoothstep(clamp(swirl))
    lt = lerp(1.0, 0.55, dark) * lerp(1.0, 0.85, w)
    if light < 0.25:
        lt *= max(0.0, light / 0.25)
    tint = (20, 30, 70) if w < 0.5 else (70, 35, 10)
    tint_amt = 0.35 * dark + 0.18 * w
    rim = min(0.45, 0.06 + 0.22 * dark + 0.17 * s * max(1.0, window_bright))
    rim_color = "#9FB6FF" if s < 0.5 else "#FFE2C0"
    return dict(light=lt, tint=tint, tint_amt=tint_amt, rim=rim, rim_color=rim_color)
