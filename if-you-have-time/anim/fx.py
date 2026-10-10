"""Light effects, memories, holo-cards and titles for "If You Have Time" (BIBLE section 4: S0, S2, S4, S5).

Coordinates: every function draws in whatever space the canvas is currently in (stage units under a
scene Camera, usually). Functions marked SCREEN space expect an identity matrix (call after
canvas.resetMatrix() / outside the camera transform).

Public API
    draw_motes(canvas, t, area, density, env, color, seed, rise, alpha)          floating light dust
    draw_note_sparkles(canvas, t, onsets, area, seed, life, color, alpha)          sparkle per music onset
    draw_ribbons(canvas, t, intensity, env, area, seed, palette, freeze, burst)    the symphony ribbons
    draw_memory(canvas, t, kind, cx, cy, r, alpha, age)                            memory bubble vignettes
    draw_holo_card(canvas, t, cx, cy, scale, number, title, icon, state, alpha, wobble, fold)
    draw_card_fan(canvas, t, cx, cy, progress, alpha, numbers, titles, icons, wobble_set, fold_set,
                  fold, wobble, focus, focus_amt)
    draw_music_box(canvas, t, cx, cy, scale, alpha)
    draw_title(canvas, t, text, cy, alpha, size, sub, sub_alpha)                   SCREEN space
    draw_flash(canvas, amount, color)                                              SCREEN space
    draw_vignette(canvas, amount)                                                  SCREEN space
    draw_light_burst(canvas, t, cx, cy, amount, color)
    draw_falling_sparks(canvas, t, area, amount, seed)
    draw_send_lights(canvas, t, progress, src, dst, n)
    draw_pixel_sparkles(canvas, t, area, amount, seed)
    draw_rain_streaks(canvas, t, area, amount)

Extras: MEMORY_KINDS, CARD_TITLES, CARD_ICONS, card_fan_layout(cx, cy, progress, ...) -> card placements.

Everything is stateless (a pure function of its arguments), so frames can be rendered in any order
and in parallel. Static illustration parts are recorded once into skia Pictures; soft lights are
cached sprite images blitted additively; ribbons are gouraud-shaded triangle meshes (soft edges for
free, no blur passes) -- all smooth, low-frequency and compression friendly.
"""
from __future__ import annotations

import bisect
import colorsys
import math
import re
from functools import lru_cache

import numpy as np
import skia

from anim.core import (clamp, ease_in_out, ease_out, hash01, lerp, noise1, paint, rgb, smooth_path,
                       smoothstep, timeline)
from config import H, W

TAU = math.tau
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
_LIN_NOMIP = skia.SamplingOptions(skia.FilterMode.kLinear)


# =========================================================================== small helpers
def _rgb(c):
    """palette key / hex / (r,g,b) -> (r, g, b) ints."""
    if isinstance(c, str):
        return rgb(c)
    if isinstance(c, int):
        return (skia.ColorGetR(c), skia.ColorGetG(c), skia.ColorGetB(c))
    return (int(c[0]), int(c[1]), int(c[2]))


def _hex(c) -> str:
    r, g, b = _rgb(c)
    return f"#{r:02X}{g:02X}{b:02X}"


def _mixrgb(a, b, t):
    a, b = _rgb(a), _rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


@lru_cache(maxsize=512)
def _saturate(c, k=1.3):
    """Scale HSV saturation by k (keeps hue and value)."""
    r, g, b = (v / 255.0 for v in _rgb(c))
    h, s_, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, clamp(s_ * k), v)
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def _c(c, a=1.0):
    """color (key/hex/tuple) with alpha -> skia color int."""
    r, g, b = _rgb(c)
    return skia.Color(r, g, b, int(255 * clamp(a)))


def _mscale(canvas) -> float:
    """Uniform scale of the canvas matrix (local units -> device px)."""
    m = canvas.getTotalMatrix()
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0


def _add_paint(alpha=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(alpha))
    p.setBlendMode(skia.BlendMode.kPlus)
    return p


def _image_from_rgba(arr: np.ndarray, mips=True) -> skia.Image:
    """float (h,w,4) premultiplied 0..1 -> skia Image."""
    a8 = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    img = skia.Image.fromarray(np.ascontiguousarray(a8), colorType=skia.kRGBA_8888_ColorType,
                               alphaType=skia.kPremul_AlphaType)
    return img.withDefaultMipmaps() if mips else img


@lru_cache(maxsize=256)
def _sprite(color: str, kind: str = "soft") -> skia.Image:
    """Premultiplied radial light sprite in `color` (alpha = light amount, for additive or src-over)."""
    n = 96
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - (n - 1) / 2) ** 2 + (yy - (n - 1) / 2) ** 2) / (n / 2)
    edge = np.clip(1 - d * d, 0, 1) ** 1.5
    if kind == "soft":          # gaussian, long tail
        prof = np.exp(-d * d * 4.0) * edge
    elif kind == "core":        # bright point + halo (mote / spark)
        prof = (np.exp(-d * d * 60.0) * 0.75 + np.exp(-d * d * 9.0) * 0.30 + np.exp(-d * d * 2.5) * 0.10) * edge
    elif kind == "wide":        # flatter falloff (bloom / light pool)
        prof = np.clip(1 - d, 0, 1) ** 2.0
    elif kind == "disc":        # soft-edged bokeh disc
        t = np.clip((1.0 - d) / 0.25, 0, 1)
        prof = t * t * (3 - 2 * t)
    elif kind == "bokeh":       # disc (inner 45 %) + soft halo, one blit
        t = np.clip((0.45 - d) / 0.1, 0, 1)
        prof = 0.8 * t * t * (3 - 2 * t) + 0.2 * np.exp(-d * d * 5.0) * edge
    else:
        raise ValueError(kind)
    prof = np.clip(prof, 0, 1).astype(np.float32)
    c = np.array(_rgb(color), np.float32) / 255.0
    arr = np.dstack([c[None, None, :] * prof[..., None], prof])
    return _image_from_rgba(arr)


def _blob(canvas, x, y, r, color, alpha=1.0, kind="soft", add=True, ry=None, angle=0.0):
    """Soft light blob (one cached sprite blit). r = outer radius."""
    if alpha <= 0.004 or r <= 0.05:
        return
    p = skia.Paint()
    p.setAlphaf(clamp(alpha))
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    ry = r if ry is None else ry
    img = _sprite(_hex(color), kind)
    if angle:
        canvas.save()
        canvas.translate(x, y)
        canvas.rotate(angle)
        canvas.drawImageRect(img, skia.Rect(-r, -ry, r, ry), _LIN, p)
        canvas.restore()
    else:
        canvas.drawImageRect(img, skia.Rect(x - r, y - ry, x + r, y + ry), _LIN, p)


def _argb_np(rgb3, alpha):
    """numpy alpha array (0..1) + rgb tuple or (N,3) array -> list of skia color ints."""
    a = (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint32)
    rgb3 = np.asarray(rgb3, np.uint32)
    if rgb3.ndim == 1:
        r, g, b = (int(v) for v in rgb3)
        v = (a << 24) | np.uint32((r << 16) | (g << 8) | b)
    else:
        v = (a << 24) | (rgb3[:, 0] << 16) | (rgb3[:, 1] << 8) | rgb3[:, 2]
    return v.astype(np.uint32)


@lru_cache(maxsize=32)
def _strip_indices(n: int, rows: int) -> np.ndarray:
    """Triangle indices for a grid of n samples x rows (vertex = j*rows + r)."""
    j = np.arange(n - 1)[:, None]
    r = np.arange(rows - 1)[None, :]
    v = (j * rows + r).ravel()
    tri = np.stack([v, v + rows, v + 1, v + 1, v + rows, v + rows + 1], axis=1)
    return tri.ravel().astype(np.int64)


class _Mesh:
    """Accumulates gouraud strips; one drawVertices call at the end."""

    def __init__(self):
        self.xs, self.ys, self.cols, self.idx = [], [], [], []
        self.nv = 0

    def strip(self, px, py, nx, ny, offsets, widths, rgb3, alphas):
        """Center line (px,py), unit normals (nx,ny) (n,), per-row offsets (rows,) in units of
        widths (n,), color rgb (tuple) and alphas (n, rows)."""
        n, rows = len(px), len(offsets)
        off = np.asarray(offsets, np.float64)[None, :] * widths[:, None]
        X = px[:, None] + nx[:, None] * off
        Y = py[:, None] + ny[:, None] * off
        self.xs.append(X.ravel())
        self.ys.append(Y.ravel())
        self.cols.append(_argb_np(rgb3, alphas.ravel()))
        self.idx.append(_strip_indices(n, rows) + self.nv)
        self.nv += n * rows

    def draw(self, canvas, paint_=None):
        if not self.nv:
            return
        xs = np.concatenate(self.xs).tolist()
        ys = np.concatenate(self.ys).tolist()
        pts = list(map(skia.Point, xs, ys))
        cl = np.concatenate(self.cols).tolist()
        ix = np.concatenate(self.idx).tolist()
        v = skia.Vertices.MakeCopy(skia.Vertices.kTriangles_VertexMode, pts, None, cl, ix)
        if paint_ is None:
            paint_ = skia.Paint()
            paint_.setBlendMode(skia.BlendMode.kPlus)
        canvas.drawVertices(v, paint_, skia.BlendMode.kDst)   # kDst = use the vertex colors


def _beat_or(name, default):
    try:
        return timeline()["beats"][name]
    except Exception:
        return default


def _ss(a, b, x):
    """smoothstep from a to b."""
    if b == a:
        return 1.0 if x >= b else 0.0
    return smoothstep((x - a) / (b - a))


# =========================================================================== motes
def draw_motes(canvas, t, area=(0, 0, W, H), density=1.0, env=0.0, color="amber_soft", seed=0,
               rise=20.0, alpha=1.0, size=1.0):
    """Soft floating light dust inside `area` (x0, y0, x1, y1).

    density: ~22 motes per 720x1280 area at 1.0 (motes fade in one by one as density grows).
    env: 0..1 music loudness -> gentle size/brightness pulse. rise: upward drift in units/s
    (negative = sink). size: radius multiplier. Sparse, smooth, additive."""
    if alpha <= 0.003 or density <= 0:
        return
    x0, y0, x1, y1 = area
    aw, ah = x1 - x0, y1 - y0
    if aw <= 0 or ah <= 0:
        return
    base_n = 22.0 * (aw * ah) / (W * H)
    nf = base_n * density
    n = int(math.ceil(nf))
    margin = 40.0
    span = ah + 2 * margin
    pulse = 1.0 + 0.45 * env
    glow_c = _saturate(color, 1.5)
    for i in range(n):
        wgt = clamp(nf - i)
        if wgt <= 0:
            continue
        h = lambda k: hash01(i * 13 + k, seed + 101)  # noqa: E731
        speed = rise * (0.55 + 0.9 * h(1))
        yy = (h(2) * span - speed * t) % span
        y = y0 - margin + yy
        sway = 14 + 22 * h(3)
        x = x0 + h(4) * aw + sway * math.sin(t * (0.18 + 0.25 * h(5)) + TAU * h(6)) \
            + 10 * noise1(t * 0.15 + 30 * h(7), seed + i)
        depth = h(8)                      # 0 far .. 1 near
        r = (3.0 + 7.0 * depth ** 2) * size * pulse
        tw = 0.65 + 0.35 * math.sin(t * (0.6 + 0.9 * h(9)) + TAU * h(10))
        edge = _ss(y0 - margin, y0 + margin * 0.5, y) * _ss(y1 + margin, y1 - margin * 0.5, y)
        a = alpha * wgt * edge * tw * (0.55 + 0.45 * depth) * (0.75 + 0.5 * env)
        if a <= 0.004:
            continue
        if depth > 0.82:   # a few big soft out-of-focus bokeh motes
            _blob(canvas, x, y, r * 2.2, glow_c, a * 0.22, kind="bokeh")
        else:
            _blob(canvas, x, y, r * 5.0, glow_c, a * 0.22, kind="soft")
            _blob(canvas, x, y, r * 3.2, glow_c, a, kind="core")


# =========================================================================== note sparkles
def _star_path(r_long, r_short, points=4, rot=0.0):
    p = skia.Path()
    for k in range(points * 2):
        ang = rot + k * math.pi / points
        rr = r_long if k % 2 == 0 else r_short
        x, y = math.cos(ang) * rr, math.sin(ang) * rr
        if k == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    return p


def _sparkle(canvas, x, y, s, color, a, rot=0.0):
    """Four-point glint: halo + crossed flare + white-hot center. s = size (radius of flare)."""
    if a <= 0.004 or s <= 0.1:
        return
    _blob(canvas, x, y, s * 2.2, _saturate(color, 1.3), a * 0.6, kind="soft")
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(rot)
    p = _add_paint(a * 0.9)
    p.setColor(_c(_mixrgb(color, "#FFFFFF", 0.45)))
    canvas.drawPath(_star_path(s, s * 0.09, 4), p)
    p.setAlphaf(clamp(a * 0.35))
    canvas.rotate(45)
    canvas.drawPath(_star_path(s * 0.45, s * 0.07, 4), p)
    canvas.restore()
    _blob(canvas, x, y, s * 0.42, "#FFFFFF", a * 0.9, kind="core")


def draw_note_sparkles(canvas, t, onsets, area=(0, 0, W, H), seed=0, life=1.4, color="teal_glow",
                       alpha=1.0, size=1.0, colors=None):
    """A sparkle is born at each onset time (absolute seconds, sorted) at a pseudo-random spot in
    `area`; it blooms quickly, drifts up a little and fades over `life` seconds.
    colors: optional list of colors to cycle through (overrides `color`)."""
    if alpha <= 0.003 or not onsets:
        return
    x0, y0, x1, y1 = area
    lo = bisect.bisect_left(onsets, t - life)
    hi = bisect.bisect_right(onsets, t)
    for i in range(lo, hi):
        age = t - onsets[i]
        u = age / life
        if not 0 <= u < 1:
            continue
        k = int(round(onsets[i] * 1000))       # stable per-onset identity
        h = lambda j: hash01(k * 7 + j, seed + 501)  # noqa: E731
        x = x0 + (0.06 + 0.88 * h(1)) * (x1 - x0)
        y = y0 + (0.06 + 0.88 * h(2)) * (y1 - y0) - 18 * ease_out(u)
        bloom = ease_out(min(1.0, u * 5.0))
        fade = (1 - u) ** 1.6
        s = size * (9 + 9 * h(3)) * (0.35 + 0.65 * bloom) * (1 + 0.15 * math.sin(age * 9))
        cc = colors[k % len(colors)] if colors else color
        _sparkle(canvas, x, y, s, cc, alpha * fade * (0.6 + 0.4 * bloom), rot=h(4) * 30 - 15 + age * 12)


# =========================================================================== vectorized strips
def _layer_mesh(mesh, px, py, nx, ny, offsets, widths, rgbs, alphas):
    """Vectorized strips for R ribbons at once. px..widths: (R, n); offsets (rows,);
    rgbs (R, 3) ints; alphas (R, n, rows)."""
    R, n = px.shape
    rows = len(offsets)
    off = widths[:, :, None] * np.asarray(offsets, np.float64)[None, None, :]
    X = px[:, :, None] + nx[:, :, None] * off
    Y = py[:, :, None] + ny[:, :, None] * off
    a8 = (np.clip(alphas, 0, 1) * 255 + 0.5).astype(np.uint32)
    rgbs = np.asarray(rgbs, np.uint32)
    rgbi = (rgbs[:, 0] << 16) | (rgbs[:, 1] << 8) | rgbs[:, 2]
    colors = (a8 << 24) | rgbi[:, None, None]
    base = _strip_indices(n, rows)
    idx = (base[None, :] + (np.arange(R) * n * rows)[:, None]).ravel() + mesh.nv
    mesh.xs.append(X.ravel())
    mesh.ys.append(Y.ravel())
    mesh.cols.append(colors.ravel())
    mesh.idx.append(idx)
    mesh.nv += R * n * rows


@lru_cache(maxsize=16)
def _rib_params(seed):
    return np.array([[hash01(k * 17 + j, seed + 907) for j in range(32)] for k in range(6)])


# =========================================================================== ribbons
_RIB_SLOTS = np.array((0.30, 0.64, 0.12, 0.86, 0.47, 0.75))      # vertical placement per ribbon
# glowing edge filaments: (offset across the ribbon in half-widths, alpha, width multiplier). Leading edge
# only, a little wider and softer than a hairline: the old faint trailing-edge filament and the 2-px-crisp
# moving edges were S2's main bit hog (QA encode: ~7 % + ~5 % of the bits) for almost no visible light.
_RIB_FILAMENTS = ((-0.62, 0.62 * 0.6, 1.8),)


def draw_ribbons(canvas, t, intensity=1.0, env=0.0, area=(0, 0, W, H), seed=0,
                 palette=("teal_glow", "amber_soft", "#B79CFF"), freeze=0.0, burst=0.0,
                 freeze_t=None, alpha=1.0, width=1.0, glints=True, n=48):
    """3-6 flowing luminous ribbons through `area` (the symphony made visible). Additive light.

    intensity 0..1: count (3 -> 6) and opacity.   env 0..1: breathing width/brightness.
    freeze 0..1: eases the motion to a hold (grand pause). Stateless: time is pulled toward
        `freeze_t` (default: beat 'sym_grand_pause' + 0.35 s) by `freeze`, so ramp freeze while t is
        near freeze_t (a ramp far from it would visibly scrub the motion).
    burst 0..1: ribbons sweep outward from the area center, widen and brighten (climax).
    width: global width multiplier.  palette: ribbon colors (cycled).  n: samples per ribbon."""
    if alpha <= 0.003 or intensity <= 0.001:
        return
    x0, y0, x1, y1 = area
    aw, ah = x1 - x0, y1 - y0
    acx, acy = (x0 + x1) / 2, (y0 + y1) / 2
    if freeze > 0:
        if freeze_t is None:
            freeze_t = _beat_or("sym_grand_pause", t) + 0.35
        tau = lerp(t, freeze_t, smoothstep(freeze))
    else:
        tau = t
    bs = smoothstep(burst)
    tau += 2.6 * bs                       # sweep faster while the burst ramps
    nvis = 2.0 + 4.0 * clamp(intensity)
    R = min(6, int(math.ceil(nvis)))
    glob = alpha * smoothstep(intensity * 4) * (0.45 + 0.55 * clamp(intensity)) \
        * (0.80 + 0.45 * env) * (1 + 1.0 * burst) * (1 - 0.18 * smoothstep(freeze))
    diag = math.hypot(aw, ah)
    P = _rib_params(seed)[:R]
    hcol = lambda j: P[:, j][:, None]  # noqa: E731
    k = np.arange(R)
    wk = np.clip(nvis - k, 0, 1)[:, None]
    s = np.linspace(0.0, 1.0, n)[None, :]
    L = diag * (0.62 + 0.30 * hcol(0))
    side = np.where(k % 2 == 0, 1.0, -1.0)[:, None]
    theta = side * (0.28 + 0.45 * hcol(1)) + 0.22 * np.sin(0.031 * tau + TAU * hcol(2)) \
        + np.where(hcol(3) > 0.5, math.pi, 0.0)
    cx = x0 + aw * (0.32 + 0.36 * hcol(4)) + aw * 0.10 * np.sin(0.047 * tau + TAU * hcol(5))
    cy = y0 + ah * _RIB_SLOTS[:R, None] + ah * 0.05 * np.sin(0.039 * tau + TAU * hcol(6))
    B1, f1, w1 = 0.65 + 0.40 * hcol(7), 0.50 + 0.30 * hcol(8), 0.26 + 0.14 * hcol(9)
    B2, f2, w2 = 0.22 + 0.18 * hcol(10), 1.25 + 0.55 * hcol(11), 0.18 + 0.16 * hcol(12)
    phi = (theta + B1 * np.sin(TAU * f1 * s - w1 * tau + TAU * hcol(13))
           + B2 * np.sin(TAU * f2 * s + w2 * tau + TAU * hcol(14)))
    ds = L / (n - 1)
    dx, dy = np.cos(phi) * ds, np.sin(phi) * ds
    px = np.concatenate([np.zeros((R, 1)), np.cumsum(dx[:, :-1], axis=1)], axis=1)
    py = np.concatenate([np.zeros((R, 1)), np.cumsum(dy[:, :-1], axis=1)], axis=1)
    m = n // 2
    px = px - px[:, m:m + 1] + cx
    py = py - py[:, m:m + 1] + cy
    if bs > 0:
        sc = 1 + 0.28 * bs
        px = acx + (px - acx) * sc
        py = acy + (py - acy) * sc
    nx, ny = -np.sin(phi), np.cos(phi)
    # ribbon width: tapered + twisting (signed -> the edges cross at the pinch points)
    Wr = (24 + 18 * hcol(15)) * width * (0.85 + 0.4 * env) * (1 + 0.55 * bs)
    taper = np.sin(np.pi * s) ** 0.7
    twist = np.cos(TAU * (0.70 + 0.50 * hcol(16)) * s - (0.42 + 0.28 * hcol(17)) * tau + TAU * hcol(18))
    hw = Wr * taper * twist
    ef = np.clip(np.minimum(s, 1 - s) / 0.16, 0, 1)
    ef = ef * ef * (3 - 2 * ef)
    flow = 0.70 + 0.30 * np.sin(TAU * (1.4 * s - 0.11 * tau) + TAU * hcol(19))
    edge_on = (1 - np.abs(twist)) ** 2
    a = glob * wk * ef * flow                                          # (R, n)
    base = [_rgb(palette[i % len(palette)]) for i in range(R)]
    body_rgb = np.array([_saturate(c, 1.7) for c in base])
    fil_rgb = np.array([_mixrgb(_saturate(c, 1.3), "#FFFFFF", 0.4) for c in base])

    mesh = _Mesh()
    # silky body with a soft halo built into the same strip (rows beyond +-1 are the glow);
    # brighter where the ribbon turns edge-on, sheen along the leading edge
    ab = a * (0.50 + 0.60 * edge_on)
    w_u = np.maximum(np.abs(hw), Wr * 0.22 * taper)            # unsigned: halo stays continuous
    prof = np.array((0, 0.10, 0.62, 0.42, 0.28, 0.08, 0))
    profs = np.where((twist >= 0)[:, :, None], prof[None, None, :], prof[::-1][None, None, :])
    offs = (-1.8, -1.0, -0.62, 0, 0.62, 1.0, 1.8)
    _layer_mesh(mesh, px, py, nx, ny, offs, w_u, body_rgb, ab[:, :, None] * profs)
    # glowing filament along the leading edge
    fw = np.full((R, n), 2.1 + 1.3 * env + 1.4 * bs)
    tri = np.array((0, 1, 0))[None, None, :]
    pinch = 0.35 + 0.65 * np.sqrt(np.abs(twist))        # soften the X where the edges cross
    for off, fa, fwk in _RIB_FILAMENTS:
        fx_ = px + nx * hw * off
        fy_ = py + ny * hw * off
        _layer_mesh(mesh, fx_, fy_, nx, ny, (-1, 0, 1), fw * fwk, fil_rgb, (a * fa * pinch)[:, :, None] * tri)
    mesh.draw(canvas)
    if glints:
        for r_ in range(R):
            for j in range(2):
                u = (0.045 * tau * (0.8 + 0.5 * P[r_, 20 + j]) + j * 0.5 + P[r_, 22 + j]) % 1.0
                fi = u * (n - 1)
                i0 = int(fi)
                i1 = min(i0 + 1, n - 1)
                fr = fi - i0
                gx = lerp(px[r_, i0] + nx[r_, i0] * hw[r_, i0] * -0.62, px[r_, i1] + nx[r_, i1] * hw[r_, i1] * -0.62, fr)
                gy = lerp(py[r_, i0] + ny[r_, i0] * hw[r_, i0] * -0.62, py[r_, i1] + ny[r_, i1] * hw[r_, i1] * -0.62, fr)
                ga = float(lerp(a[r_, i0], a[r_, i1], fr)) * (0.6 + 0.4 * math.sin(tau * 2.1 + j * 2))
                _blob(canvas, gx, gy, 18 + 6 * env, tuple(fil_rgb[r_]), ga * 0.9, kind="core")


# =========================================================================== screen-space overlays
def draw_flash(canvas, amount, color="#FFF4E0"):
    """SCREEN space full-frame flash (src-over, amount = opacity 0..1)."""
    if amount <= 0.002:
        return
    canvas.drawRect(skia.Rect(0, 0, W, H), paint(color, clamp(amount), aa=False))


_VIG_STOPS = (0.0, 0.45, 0.70, 0.88, 1.0, 1.25)
_VIG_ALPHAS = (0.0, 0.0, 0.22, 0.55, 0.82, 1.0)


@lru_cache(maxsize=4)
def _vignette_assets():
    ky = H / W * 0.86
    m = skia.Matrix()
    m.setScale(1.0, ky, W / 2, H / 2)
    R = W * 0.80 * 1.25
    cols = [skia.Color(0, 0, 0, int(255 * a)) for a in _VIG_ALPHAS]
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), R, cols, [p / 1.25 for p in _VIG_STOPS],
                                        skia.TileMode.kClamp, 0, m)
    # only paint outside the fully transparent inner ellipse
    r0 = R * 0.45 / 1.25 * 0.995
    path = skia.Path()
    path.addRect(skia.Rect(0, 0, W, H))
    path.addOval(skia.Rect(W / 2 - r0, H / 2 - r0 * ky, W / 2 + r0, H / 2 + r0 * ky))
    path.setFillType(skia.PathFillType.kEvenOdd)
    return sh, path


def draw_vignette(canvas, amount=0.5):
    """SCREEN space soft dark edges (smooth elliptical radial gradient). amount 0..1."""
    if amount <= 0.002:
        return
    sh, path = _vignette_assets()
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    p.setAlphaf(clamp(amount))
    p.setDither(True)
    canvas.drawPath(path, p)


# =========================================================================== light burst
def draw_light_burst(canvas, t, cx, cy, amount, color="#FFF1D6", radius=1100.0, rays=1.0):
    """Soft god-rays + bloom radiating from (cx, cy). amount 0..1 (climax). Additive.
    One gouraud-shaded polar mesh: a low-frequency, slowly turning angular ray profile times a radial
    falloff, plus a bloom core -- smooth, no hard stripes."""
    if amount <= 0.003:
        return
    a = clamp(amount)
    R = radius * (0.75 + 0.35 * a)
    na = 120
    ang = np.linspace(0, TAU, na + 1)
    prof = np.zeros(na + 1)
    for (fr, sp, ph, w) in ((7, 0.035, 0.3, 0.55), (11, -0.025, 1.7, 0.35), (5, 0.018, 4.1, 0.45), (17, 0.05, 2.2, 0.18)):
        prof += w * (0.5 + 0.5 * np.cos(fr * ang + TAU * sp * t + ph)) ** 3
    prof = 0.15 + 0.85 * prof / prof.max()
    rr = np.array((0.0, 0.025, 0.07, 0.15, 0.28, 0.46, 0.70, 1.0))
    ray_r = np.array((0.95, 0.80, 0.55, 0.32, 0.17, 0.08, 0.03, 0.0))
    bloom = np.array((1.0, 0.85, 0.55, 0.26, 0.10, 0.03, 0.0, 0.0))
    alpha = (prof[:, None] * ray_r[None, :] * 0.85 * rays + bloom[None, :] * 0.75) * a      # (na+1, rings)
    px = cx + np.cos(ang)[:, None] * rr[None, :] * R
    py = cy + np.sin(ang)[:, None] * rr[None, :] * R
    mesh = _Mesh()
    rows = len(rr)
    mesh.xs.append(px.ravel())
    mesh.ys.append(py.ravel())
    mesh.cols.append(_argb_np(_saturate(_rgb(color), 1.8), alpha.ravel()))
    mesh.idx.append(_strip_indices(na + 1, rows))
    mesh.nv = (na + 1) * rows
    mesh.draw(canvas)
    _blob(canvas, cx, cy, R * 0.06, "#FFFFFF", 0.9 * a, kind="soft")


# =========================================================================== falling sparks
def draw_falling_sparks(canvas, t, area=(0, 0, W, H), amount=1.0, seed=0,
                        colors=("#FFF1D6", "amber_soft", "teal_glow", "#D9C8FF"), fall=34.0, density=1.0):
    """Slow drifting/falling glowing sparks like snow inside `area`. amount 0..1 fades them in
    one by one (and overall opacity). fall: mean fall speed units/s."""
    if amount <= 0.003:
        return
    x0, y0, x1, y1 = area
    aw, ah = x1 - x0, y1 - y0
    nmax = 46.0 * density * (aw * ah) / (W * H)
    nf = nmax * clamp(amount) ** 0.7
    n = int(math.ceil(nf))
    margin = 30.0
    span = ah + 2 * margin
    for i in range(n):
        wgt = clamp(nf - i)
        h = lambda k: hash01(i * 11 + k, seed + 303)  # noqa: E731
        depth = h(1)
        sp = fall * (0.5 + 0.9 * depth)
        y = y0 - margin + (h(2) * span + sp * t) % span
        x = x0 + h(3) * aw + (12 + 20 * h(4)) * math.sin(t * (0.35 + 0.4 * h(5)) + TAU * h(6))
        tw = 0.6 + 0.4 * math.sin(t * (1.0 + 1.5 * h(7)) + TAU * h(8))
        edge = _ss(y0 - margin, y0 + margin, y) * _ss(y1 + margin, y1 - margin, y)
        a = clamp(amount) * wgt * edge * tw * (0.5 + 0.5 * depth)
        r = 7 + 11 * depth * depth
        cc = _saturate(colors[i % len(colors)], 1.3)
        _blob(canvas, x, y, r * 2.4, cc, a, kind="core")


# =========================================================================== send lights
def _bez(p0, p1, p2, p3, u):
    v = 1 - u
    return (v ** 3 * p0[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u ** 3 * p3[0],
            v ** 3 * p0[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u ** 3 * p3[1])


def draw_send_lights(canvas, t, progress, src, dst, n=8, color="amber_soft", size=1.0):
    """`n` small warm lights lift from `src` (palm) and stream in gentle staggered arcs to `dst`.
    progress 0..1 drives the whole send (light k leaves at ~k*0.06 and arrives ~0.5 later)."""
    if progress <= 0:
        return
    sx, sy = src
    dx_, dy_ = dst
    dist = math.hypot(dx_ - sx, dy_ - sy) or 1.0
    stagger = 0.42 / max(1, n - 1)
    dur = 0.52
    core = _mixrgb(color, "#FFFFFF", 0.6)
    for k in range(n):
        u = (progress - k * stagger) / dur
        if u <= 0 or u >= 1.12:
            continue
        h = lambda j: hash01(k * 5 + j, 77)  # noqa: E731
        p0 = (sx + (h(1) - 0.5) * 26, sy - 4)
        lift = 90 + 70 * h(2) + 0.12 * dist
        p1 = (sx + (h(3) - 0.5) * 120, sy - lift)
        arc = 0.25 * dist * (0.6 + 0.8 * h(4))
        p2 = (lerp(sx, dx_, 0.75) + (h(5) - 0.5) * 80, min(sy, dy_) - arc)
        p3 = (dx_ + (h(6) - 0.5) * 20, dy_ + (h(7) - 0.5) * 30)
        uu = ease_in_out(min(u, 1.0))
        appear = _ss(0.0, 0.08, u)
        arrive = 1.0 - _ss(0.96, 1.12, u)
        # trail
        for j in range(9, 0, -1):
            ut = uu - j * 0.018
            if ut <= 0:
                continue
            x, y = _bez(p0, p1, p2, p3, ut)
            f = (1 - j / 10.0)
            _blob(canvas, x, y, (9 + 6 * f) * size, color, 0.22 * f * appear * arrive, kind="core")
        x, y = _bez(p0, p1, p2, p3, uu)
        tw = 0.85 + 0.15 * math.sin(t * 9 + k * 1.7)
        _blob(canvas, x, y, 44 * size, color, 0.40 * appear * arrive * tw, kind="soft")
        _blob(canvas, x, y, 22 * size, core, 1.0 * appear * arrive * tw, kind="core")
        if u > 0.9:   # arrival twinkle
            fl = math.sin(clamp((u - 0.9) / 0.22) * math.pi)
            _sparkle(canvas, p3[0], p3[1], 14 * size * fl, color, 0.8 * fl)


# =========================================================================== pixel sparkles
_PIX_COLORS = ("#FF77A8", "#FFEC27", "#29ADFF", "#00E436", "#FFFFFF", "#FFA300")
_PIX_FRAMES = (
    ((0, 0),),
    ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)),
    ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)),
    ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)),
    ((3, 0), (-3, 0), (0, 3), (0, -3)),
)


def draw_pixel_sparkles(canvas, t, area=(0, 0, W, H), amount=1.0, seed=0, px=7.0, step=1 / 12, count=20):
    """Chunky 8-bit sparkles/pluses popping in `area` (arcade gag). Animation is quantized to
    `step` seconds like a sprite sheet; px = pixel block size in local units."""
    if amount <= 0.003:
        return
    x0, y0, x1, y1 = area
    nf = count * clamp(amount)
    tq = math.floor(t / step) * step
    nfr = len(_PIX_FRAMES)
    life = (nfr + 2) * step
    p = skia.Paint(AntiAlias=False)
    for i in range(int(math.ceil(nf))):
        wgt = clamp(nf - i)
        h0 = hash01(i, seed + 11)
        period = life + (0.25 + 0.6 * h0)
        ph = tq + h0 * period
        cyc = math.floor(ph / period)
        loc = ph - cyc * period
        fi = int(loc / step + 1e-6)
        if fi >= nfr + 2:
            continue
        frame = _PIX_FRAMES[min(fi, nfr - 1) if fi < nfr else nfr - 1 - (fi - nfr) - 1]
        h = lambda k: hash01(cyc * 31 + i * 7 + k, seed + 19)  # noqa: E731
        x = x0 + (0.05 + 0.9 * h(1)) * (x1 - x0)
        y = y0 + (0.05 + 0.9 * h(2)) * (y1 - y0)
        x = round(x / px) * px
        y = round(y / px) * px
        cc = _PIX_COLORS[int(h(3) * len(_PIX_COLORS)) % len(_PIX_COLORS)]
        a = clamp(amount) * wgt
        _blob(canvas, x + px / 2, y + px / 2, px * 5, cc, 0.25 * a, kind="soft")
        p.setColor(_c(cc, a))
        g = _even_grid(canvas, x, y, px)            # whole even device-px cells (crisp, chroma-safe)
        sx_, sy_, cl = g if g else (x, y, px)
        p.setAntiAlias(g is None)
        for (gx, gy) in frame:
            canvas.drawRect(skia.Rect.MakeXYWH(sx_ + gx * cl, sy_ + gy * cl, cl, cl), p)


# =========================================================================== rain streaks
def draw_rain_streaks(canvas, t, area=(0, 0, W, H), amount=1.0, seed=0, color="#CFE6FF", slant=0.10):
    """Soft rain on glass inside `area`: a few thin fast streaks plus slow beaded rivulets.
    amount 0..1 -> count/opacity. Low density on purpose (compression)."""
    if amount <= 0.003:
        return
    x0, y0, x1, y1 = area
    aw, ah = x1 - x0, y1 - y0
    a0 = clamp(amount)
    canvas.save()
    canvas.clipRect(skia.Rect(x0, y0, x1, y1), True)
    c = _rgb(color)
    # fast falling streaks
    nf = 18 * a0 * (aw / 540.0)
    for i in range(int(math.ceil(nf))):
        wgt = clamp(nf - i)
        h = lambda k: hash01(i * 9 + k, seed + 41)  # noqa: E731
        ln = 40 + 70 * h(1)
        sp = 380 + 320 * h(2)
        span = ah + ln + 60
        yy = (h(3) * span + sp * t) % span + y0 - ln - 30
        xx = x0 + h(4) * aw + slant * (yy - y0)
        al = 0.30 * wgt * a0 * (0.5 + 0.5 * h(5))
        sh = skia.GradientShader.MakeLinear([(xx - slant * ln, yy - ln), (xx, yy)],
                                            [_c(c, 0), _c(c, al)])
        p = skia.Paint(AntiAlias=True)
        p.setShader(sh)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(1.6)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        canvas.drawLine(xx - slant * ln, yy - ln, xx, yy, p)
    # slow rivulets: bead + wet trail, irregular speed
    nr = 7 * a0 * (aw / 540.0)
    for i in range(int(math.ceil(nr))):
        wgt = clamp(nr - i)
        h = lambda k: hash01(i * 13 + k, seed + 43)  # noqa: E731
        period = 5.0 + 4.0 * h(1)
        ph = (t + h(2) * period) / period
        cyc = math.floor(ph)
        u = ph - cyc
        hh = lambda k: hash01(cyc * 17 + i * 3 + k, seed + 47)  # noqa: E731
        bx = x0 + (0.05 + 0.9 * hh(1)) * aw
        travel = u + 0.06 * math.sin(u * 23 + hh(2) * 6)       # stick-slip
        by = y0 + travel * (ah + 40) - 20
        trail = 30 + 120 * u
        wob = lambda yy: bx + 3 * math.sin(yy * 0.05 + hh(3) * 6)  # noqa: E731
        fade = _ss(0, 0.08, u) * (1 - _ss(0.85, 1.0, u)) * wgt * a0
        pth = skia.Path()
        pth.moveTo(wob(by - trail), by - trail)
        for q in range(1, 7):
            yy = by - trail + trail * q / 6
            pth.lineTo(wob(yy), yy)
        sh = skia.GradientShader.MakeLinear([(bx, by - trail), (bx, by)], [_c(c, 0), _c(c, 0.22 * fade)])
        p = skia.Paint(AntiAlias=True)
        p.setShader(sh)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(2.4)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        canvas.drawPath(pth, p)
        canvas.drawCircle(wob(by), by, 3.2, paint(c, 0.45 * fade))
        canvas.drawCircle(wob(by) - 1.0, by - 1.0, 1.1, paint("#FFFFFF", 0.7 * fade))
    canvas.restore()


# =========================================================================== memories
# Each vignette is authored in a local 400x400 box (circle radius 200 at the origin, y down).
# The static part is recorded once into a skia Picture; a small per-frame function adds motion.
_MR = 200.0


def _P(color, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setColor(_c(color, a))
    return p


def _S(color, w, a=1.0, cap="round"):
    p = skia.Paint(AntiAlias=True)
    p.setColor(_c(color, a))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def _G(shader, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(shader)
    p.setAlphaf(clamp(a))
    p.setDither(True)
    return p


def _lin(x0, y0, x1, y1, colors, pos=None):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [c if isinstance(c, int) else _c(c) for c in colors], pos)


def _rad(cx, cy, r, colors, pos=None):
    return skia.GradientShader.MakeRadial((cx, cy), max(r, 0.01), [c if isinstance(c, int) else _c(c) for c in colors], pos)


def _sp(pts, closed=True, tension=0.5):
    return smooth_path(pts, closed=closed, tension=tension)


def _poly(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def _record(fn) -> skia.Picture:
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(-_MR - 10, -_MR - 10, _MR + 10, _MR + 10))
    fn(c)
    return rec.finishRecordingAsPicture()


def _xf(path, dx=0.0, dy=0.0, rot=0.0, sc=1.0, px=0.0, py=0.0):
    """Copy of path rotated/scaled about (px, py) then translated."""
    m = skia.Matrix()
    m.setRotate(rot, px, py)
    m.preScale(sc, sc, px, py)
    m.postTranslate(dx, dy)
    q = skia.Path(path)
    q.transform(m)
    return q


# ---------------------------------------------------------------- car_window
_CW_WIN = skia.RRect.MakeRectXY(skia.Rect(-150, -158, 240, 62), 46, 46)


def _child_head_path():
    return _sp([(-72, -80), (-38, -74), (-14, -58), (-4, -36), (0, -20), (8, -11), (2, -5),
                (-3, 3), (-1, 9), (-6, 14), (-4, 19), (-12, 30), (-26, 40), (-42, 46), (-66, 48),
                (-96, 40), (-118, 14), (-124, -18), (-116, -52), (-98, -72)])


def _cw_back(c):
    c.drawRect(skia.Rect(-210, -210, 210, 210), _P("#221D31"))
    c.save()
    c.clipRRect(_CW_WIN, True)
    c.drawRect(skia.Rect(-160, -170, 250, 70), _G(_lin(0, -158, 0, 62, ["#131833", "#262852", "#4D3B68"], [0, 0.62, 1])))
    c.restore()


# young Rae (BIBLE section 10): brown skin like Rae's, a curly dark hair puff tied up on top, big dark eyes
_YR_SKIN, _YR_SHADE, _YR_HI = "r_skin", "r_skin_shade", "r_skin_hi"
_YR_LINE = "#5A361D"
_YR_HAIR, _YR_HAIR_HI = "r_hair", "r_hair_hi"
_YR_TIE = ("#D9B566", "#A9853F")          # her gold hair tie (as grown-up Rae's)
_YR_COAT = ("#B5762F", "#CB8B3F", "#93591F")   # a mustard kid's jacket (the colour of Rae's shirt, at night)


def _curly(c, pts, r, paint_, jitter=0.25, seed=0):
    """Curly hair edge: a run of overlapping small circles along pts (a polyline)."""
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (r * 1.1)))
        for k in range(n):
            u = k / n
            rr = r * (1.0 + jitter * (hash01(i * 31 + k, seed) - 0.5) * 2)
            c.drawCircle(lerp(x0, x1, u), lerp(y0, y1, u), rr, paint_)


def _yr_hair_cap():
    return _sp([(-12, -56), (-20, -68), (-40, -84), (-70, -92), (-102, -82), (-124, -58), (-134, -22), (-128, 12),
                (-112, 34), (-100, 20), (-98, -2), (-90, -24), (-74, -38), (-54, -46), (-36, -52), (-22, -50)])


def _cw_front(c):
    # glass sheen
    c.save()
    c.clipRRect(_CW_WIN, True)
    c.drawPath(_poly([(80, -160), (130, -160), (40, 66), (-10, 66)]), _P("#FFFFFF", 0.04))
    c.drawPath(_poly([(150, -160), (165, -160), (75, 66), (60, 66)]), _P("#FFFFFF", 0.035))
    c.restore()
    # door panel + sill
    c.drawRect(skia.Rect(-210, 62, 210, 210), _P("#2E2741"))
    c.drawRect(skia.Rect(-210, 62, 210, 78), _P("#3B3352"))
    c.drawLine(-210, 79, 210, 79, _S("#4E4568", 2))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(100, 118, 176, 132), 7, 7), _P("#3F3757"))
    # window frame (rubber seal)
    c.drawRRect(_CW_WIN, _S("#120F1C", 13))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-143, -151, 233, 55), 40, 40), _S("#4C4470", 1.6, 0.6))
    coat, coat_hi, coat_dk = _YR_COAT
    # the hair puff, tied up on top of her head (behind the head; curly edge, a cool edge light from the window)
    puff_c, puff_r = (-76.0, -116.0), 36.0
    hp = _P(_YR_HAIR)
    c.drawCircle(puff_c[0], puff_c[1], puff_r, hp)
    ring = [(puff_c[0] + math.cos(a) * (puff_r - 2), puff_c[1] + math.sin(a) * (puff_r - 3))
            for a in (math.radians(d) for d in range(0, 361, 30))]
    _curly(c, ring, 10.5, hp, seed=3)
    edge = skia.Path()
    edge.addArc(skia.Rect(puff_c[0] - puff_r - 8, puff_c[1] - puff_r - 8, puff_c[0] + puff_r + 8, puff_c[1] + puff_r + 8),
                -80, 115)
    c.drawPath(edge, _S("#7F8FC4", 2.2, 0.35))
    for (x, y, a0) in ((-92, -128, 200), (-70, -138, 250), (-58, -112, 300), (-84, -104, 160), (-66, -122, 20),
                       (-96, -112, 120)):
        arc = skia.Path()
        arc.addArc(skia.Rect(x - 6, y - 6, x + 6, y + 6), a0, 220)
        c.drawPath(arc, _S(_YR_HAIR_HI, 2.0, 0.9))
    # jacket / shoulders
    c.drawPath(_sp([(-210, 210), (-210, 70), (-160, 48), (-110, 44), (-62, 52), (-20, 80), (10, 130), (20, 210)]),
               _P(coat))
    c.drawPath(_sp([(-120, 60), (-80, 64), (-40, 84), (-15, 120), (-60, 120), (-110, 90)]), _P(coat_hi, 0.8))
    c.drawPath(_sp([(-104, 44), (-60, 46), (-40, 62), (-70, 70), (-104, 62)]), _P(coat_dk))    # collar
    c.drawPath(_sp([(-86, 30), (-52, 30), (-50, 56), (-88, 58)]), _P(_YR_SHADE))                # neck
    # arm up to the glass + small hand pressed on it
    c.drawPath(_sp([(-30, 130), (14, 84), (52, 50), (72, 40), (86, 56), (62, 80), (24, 118), (-2, 150)]), _P(coat))
    c.drawPath(_sp([(58, 48), (74, 39), (86, 54), (68, 66)]), _P(coat_dk))   # cuff
    hand = _sp([(70, 48), (68, 26), (70, 4), (75, 2), (78, 20), (80, -4), (85, -6), (87, 18), (90, -2),
                (95, -2), (95, 20), (99, 8), (104, 10), (100, 32), (96, 48), (84, 58)])
    c.drawPath(hand, _P(_YR_SKIN))
    c.drawPath(hand, _S(_YR_LINE, 1.2, 0.6))
    # head
    head = _child_head_path()
    c.drawPath(head, _P(_YR_SKIN))
    c.save()
    c.clipPath(head, True)
    c.drawCircle(-98, 0, 70, _P(_YR_SHADE, 0.6))           # shade on the back of the head (lit from the window)
    c.drawCircle(-6, -30, 26, _P(_YR_HI, 0.35))            # forehead / brow catching the window light
    c.drawCircle(-30, 4, 13, _P("#C46552", 0.3))           # cheek
    c.restore()
    c.drawPath(_sp([(-84, -16), (-74, -14), (-70, 0), (-76, 12), (-86, 8)]), _P(_YR_SHADE))     # ear
    c.drawPath(_sp([(-80, -8), (-75, 0), (-79, 6)], closed=False), _S(_YR_LINE, 1.6))
    # hair: curly cap over the top and back of the head, curls along its edge, a gold tie at the puff
    cap = _yr_hair_cap()
    c.drawPath(cap, hp)
    _curly(c, [(-22, -66), (-40, -84), (-70, -93), (-102, -83), (-124, -59), (-134, -24), (-128, 10), (-114, 32)],
           7.5, hp, seed=5)
    _curly(c, [(-24, -52), (-40, -52), (-56, -47)], 4.5, hp, seed=6)        # little curls along the hairline
    for (x, y, a0) in ((-48, -70, 190), (-80, -78, 220), (-108, -62, 250), (-118, -30, 280), (-112, 4, 300),
                       (-64, -58, 160), (-94, -46, 210)):
        arc = skia.Path()
        arc.addArc(skia.Rect(x - 5.5, y - 5.5, x + 5.5, y + 5.5), a0, 220)
        c.drawPath(arc, _S(_YR_HAIR_HI, 1.8, 0.85))
    # a loose ringlet at the temple, in front of the ear (as Rae's)
    c.drawPath(_sp([(-64, -40), (-58, -30), (-64, -22), (-58, -14), (-63, -6)], closed=False, tension=0.6),
               _S(_YR_HAIR, 3.2))
    tie, tie_dk = _YR_TIE
    for k in range(5):
        x = -98 + k * 10.5
        y = -86 - 4.0 * math.sin(math.pi * k / 4)
        c.drawOval(skia.Rect(x - 6, y - 4.5, x + 6, y + 4.5), _P(tie))
        c.drawOval(skia.Rect(x - 6, y - 4.5, x + 6, y + 4.5), _S(tie_dk, 1.0, 0.8))
    # brow, a big dark eye (wide, looking out at the lights), a little 'o' mouth
    c.drawPath(_sp([(-36, -42), (-24, -47), (-11, -43)], closed=False), _S(_YR_HAIR, 2.8))
    eye = _sp([(-31, -26), (-23, -34), (-12, -34), (-5, -27), (-11, -18), (-24, -18)])
    c.drawPath(eye, _P("#F4EEE6"))
    c.save()
    c.clipPath(eye, True)
    c.drawCircle(-13, -26, 8.2, _P("r_iris"))
    c.drawCircle(-13, -26, 8.2, _S("#1E120B", 1.4))
    c.drawCircle(-12, -26, 4.4, _P("#120A06"))
    c.drawCircle(-10, -29.5, 2.6, _P("#FFFFFF"))
    c.drawCircle(-16, -22, 1.2, _P("#FFFFFF", 0.75))
    c.restore()
    c.drawPath(_sp([(-32, -27), (-23, -35.5), (-12, -35), (-4, -27)], closed=False), _S("#1A0F0A", 2.8))
    c.drawPath(_sp([(-31, -28), (-36, -33)], closed=False), _S("#1A0F0A", 1.8))         # lashes
    c.drawPath(_sp([(-28, -32), (-32, -38)], closed=False), _S("#1A0F0A", 1.6))
    c.drawPath(_sp([(-24, -17), (-12, -16.5)], closed=False), _S(_YR_LINE, 1.1, 0.6))    # lower lid
    c.drawOval(skia.Rect(-9, 7, -2, 15), _P("#4E201A"))
    c.drawPath(_sp([(4, -11), (1, -5)], closed=False), _S(_YR_LINE, 1.3, 0.8))


_CW_LIGHTS = ("#FFC46B", "#FFE9C2", "#6FD6D0", "#F08FA0", "#FFB45A", "#9FC2FF")


def _cw_city(c, age, t):
    """Night city sliding past inside the window (drawn behind the child)."""
    c.save()
    c.clipRRect(_CW_WIN, True)
    off = (age * 18.0) % 420
    bpath, wpath = skia.Path(), skia.Path()
    for rep in (0, 1):                                   # low distant skyline (two batched paths)
        for i in range(10):
            bx = -160 + i * 42 + rep * 420 - off
            if bx > 250 or bx < -210:
                continue
            bw = 30 + 14 * hash01(i, 6)
            top = 12 - 46 * hash01(i, 5)
            bpath.addRect(skia.Rect(bx, top, bx + bw, 70))
            for wy in range(int(top) + 8, 56, 14):
                if hash01(i * 31 + wy, 7) > 0.6:
                    wpath.addRect(skia.Rect(bx + 7, wy, bx + 13, wy + 5))
    c.drawPath(bpath, _P("#2A2950"))
    c.drawPath(wpath, _P("#FFC46B", 0.5))
    for i in range(9):                                   # bokeh lights, parallax
        h = lambda k: hash01(i * 7 + k, 21)  # noqa: E731
        rr = 7 + 20 * h(1)
        sp = 60 + 8 * rr
        span = 560
        x = 280 - ((h(2) * span + sp * age) % span)
        y = -135 + 150 * h(3)
        cc = _CW_LIGHTS[i % len(_CW_LIGHTS)]
        _blob(c, x, y, rr * 2.3, cc, 0.55 + 0.4 * h(4), kind="bokeh", add=True)
    ph = (age + 0.9) % 2.8                               # big street lamp sweeping past
    lx = 340 - ph * 260
    _blob(c, lx, -100, 90, "#FFD08A", 0.55, kind="core", add=True)
    c.restore()


def _cw_light(c, age, t):
    """Passing light washing over the child's face and hand."""
    ph = (age + 0.9) % 2.8
    lx = 340 - ph * 260
    lit = max(0.0, 1 - abs(lx - 10) / 210.0) ** 1.5
    lit = clamp(0.25 + 0.75 * lit + 0.12 * math.sin(age * 3.1))
    head = _child_head_path()
    c.save()
    c.clipPath(head, True)
    _blob(c, 14, -24, 95, "#FFD9A8", 0.5 * lit, kind="soft", add=True)
    c.restore()
    c.drawPath(_sp([(-14, -58), (-4, -36), (0, -20), (8, -11), (2, -5), (-3, 3), (-1, 9), (-6, 14), (-4, 19),
                    (-12, 30)], closed=False), _S("#FFE6C4", 2.2, 0.3 + 0.6 * lit))
    _blob(c, 90, 16, 40, "#FFD9A8", 0.35 * lit, kind="soft", add=True)


# ---------------------------------------------------------------- hands
_OLD = ("#E3B39A", "#C99079", "#93604C")        # skin, shade, line
_KID = ("#EDB58A", "#D49670", "#A66B4C")


def _hands_back(c):
    c.drawRect(skia.Rect(-210, -210, 210, 210),
               _G(_rad(-90, -130, 420, ["#F4DDA2", "#B9B278", "#7A8F5E", "#4E6244"], [0, 0.3, 0.62, 1])))
    for (x, y, r, a) in ((-140, -110, 34, 0.22), (120, -150, 46, 0.14), (165, 40, 28, 0.14), (-150, 120, 40, 0.10),
                         (10, -175, 22, 0.24), (-70, -160, 18, 0.22), (150, 150, 30, 0.08)):
        c.drawCircle(x, y, r, _P("#FFF1D2", a))


def _finger(c, x, base, tip, w, skin, line, curl=0.0, nail=None):
    """Upright finger from (x, base) to tip y (< base), width w; curl bends the tip forward."""
    hw = w / 2
    pts = [(x - hw, base), (x - hw * 0.98, lerp(base, tip, 0.5)), (x - hw * 0.85 + curl, tip + hw * 0.6),
           (x + curl, tip), (x + hw * 0.85 + curl, tip + hw * 0.6), (x + hw * 0.98, lerp(base, tip, 0.5)), (x + hw, base)]
    f = _sp(pts, closed=False)
    f.close()
    c.drawPath(f, _P(skin))
    c.drawPath(f, _S(line, 1.2, 0.5))
    if nail:
        c.drawOval(skia.Rect(x - hw * 0.5 + curl, tip + 2, x + hw * 0.5 + curl, tip + hw * 1.3), _P(nail, 0.8))


def _old_hand_palm_up(c):
    """Big wrinkled hand, palm toward us, fingers up (local frame, wrist at y=120)."""
    skin, shade, line = _OLD
    # cardigan sleeve
    c.drawPath(_sp([(-70, 230), (-64, 150), (-58, 118), (58, 118), (66, 150), (70, 230)]), _P("#6F7D61"))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-62, 106, 62, 136), 10, 10), _P("#5D6A51"))
    for xx in range(-50, 60, 14):
        c.drawLine(xx, 110, xx + 1, 132, _S("#4B5641", 1.6, 0.7))
    # fingers (palm side) - little, ring, middle, index
    for (x, tip, w) in ((-40, -62, 22), (-14, -86, 25), (13, -94, 26), (39, -80, 25)):
        _finger(c, x, 0, tip, w, skin, line)
        for k in (0.33, 0.62):                                   # finger creases
            yy = lerp(0, tip, k)
            c.drawLine(x - w * 0.32, yy, x + w * 0.32, yy + 1, _S(line, 1.2, 0.45))
    # palm
    palm = _sp([(-54, 4), (-30, -8), (0, -12), (30, -10), (54, 0), (60, 50), (50, 104), (0, 114), (-48, 104), (-60, 50)])
    c.drawPath(palm, _P(skin))
    c.drawPath(_sp([(-50, 60), (-20, 96), (20, 100), (46, 80), (40, 108), (0, 114), (-46, 102)]), _P(shade, 0.5))
    # palm lines
    c.drawPath(_sp([(-50, 26), (-10, 22), (30, 12), (52, 14)], closed=False), _S(line, 1.6, 0.55))
    c.drawPath(_sp([(-52, 44), (-16, 44), (16, 36)], closed=False), _S(line, 1.5, 0.5))
    c.drawPath(_sp([(40, 30), (20, 60), (14, 96)], closed=False), _S(line, 1.6, 0.5))
    c.drawPath(_sp([(-30, 62), (-12, 74)], closed=False), _S(line, 1.1, 0.35))
    c.drawPath(palm, _S(line, 1.3, 0.4))
    # age spots on the wrist
    for (x, y, r) in ((-30, 100, 3.5), (22, 104, 2.8), (-6, 92, 2.2)):
        c.drawCircle(x, y, r, _P("#B97C5E", 0.45))


def _old_thumb(c, sq):
    skin, shade, line = _OLD
    th = _sp([(46, 70), (70, 40), (78, 6), (70, -26 - 4 * sq), (54, -40 - 4 * sq), (36, -34), (40, -8), (40, 30)])
    c.drawPath(th, _P(skin))
    c.drawPath(th, _S(line, 1.3, 0.5))
    c.drawOval(skia.Rect(46, -40 - 4 * sq, 64, -26 - 4 * sq), _P("#F4D9C8", 0.9))      # nail (back of thumb)
    c.drawLine(52, -6, 70, -2, _S(line, 1.2, 0.5))


def _kid_hand_palm_down(c, sq):
    """Small chubby hand, back toward us, fingers down (local frame, wrist at y=-80)."""
    skin, shade, line = _KID
    c.drawPath(_sp([(-34, -210), (-34, -110), (-28, -84), (28, -84), (34, -110), (34, -210)]), _P("#E3A94B"))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-32, -98, 32, -76), 8, 8), _P("#C98C34"))
    for (x, tip, w) in ((-21, 28, 13), (-7, 38, 14), (7, 40, 14), (20, 32, 13)):
        _finger(c, x, -10, tip, -w, skin, line, nail="#F6D2B6")
    hand = _sp([(-30, -80), (30, -80), (34, -40), (30, -6), (0, 0), (-30, -6), (-34, -40)])
    c.drawPath(hand, _P(skin))
    c.drawPath(hand, _S(line, 1.2, 0.5))
    for x in (-15, 0, 14):                                      # knuckle dimples
        c.drawCircle(x, -12, 2.0, _P(shade, 0.8))
    c.drawPath(_sp([(-34, -60), (-48, -36), (-50, -16), (-42, -12), (-34, -30)]), _P(shade))   # thumb (tucked)
    c.drawCircle(10, -44, 10, _P("#F2A08A", 0.22))


def _hands_anim(c, age, t):
    """Old palm cradling a small hand; the thumb closes gently over it; sun flecks drift."""
    sq = 0.5 + 0.5 * math.sin(age * 1.4)
    sway = 1.8 * math.sin(age * 0.9)
    c.save()
    c.translate(-12, 30)
    c.rotate(36 + sway)
    c.scale(1.12, 1.12)
    _old_hand_palm_up(c)
    c.save()
    c.translate(2, 30 - 3 * sq)
    c.rotate(-10)
    _kid_hand_palm_down(c, sq)
    c.restore()
    _old_thumb(c, sq)
    c.restore()
    for i in range(4):
        x = -150 + ((age * 9 + i * 97) % 300)
        y = -130 + 40 * math.sin(age * 0.4 + i * 1.7) + i * 18
        _blob(c, x, y, 24, "#FFF0C8", 0.2, kind="disc", add=True)


# ---------------------------------------------------------------- dog_door
_DOOR = (-150, -205, 12, 96)


def _dd_static(c):
    x0, y0, x1, y1 = _DOOR
    c.drawRect(skia.Rect(-210, -210, 210, 210), _P("#D8B184"))                    # warm wall
    c.drawRect(skia.Rect(60, -210, 210, 96), _G(_lin(60, 0, 210, 0, ["#D8B184", "#BF956A"])))
    c.drawRect(skia.Rect(-210, 96, 210, 210), _P("#8E5E43"))                     # wooden floor
    for yy in (126, 162, 200):
        c.drawLine(-210, yy, 210, yy, _S("#7A4F38", 2, 0.7))
    c.drawRect(skia.Rect(-210, 86, 210, 98), _P("#EBD6B6"))                       # baseboard
    # door frame + door
    c.drawRect(skia.Rect(x0 - 14, y0, x1 + 14, y1), _P("#EEDDC2"))
    c.drawRect(skia.Rect(x0, y0, x1, y1), _P("#7B4A31"))
    for (a, b, cc, d) in ((x0 + 18, y0 + 104, x1 - 18, y0 + 190), (x0 + 18, y0 + 206, x1 - 18, y1 - 14)):
        c.drawRect(skia.Rect(a, b, cc, d), _P("#6C3F29"))
        c.drawRect(skia.Rect(a, b, cc, d), _S("#93603F", 2, 0.7))
    # frosted window in the door (light from outside)
    win = skia.RRect.MakeRectXY(skia.Rect(x0 + 26, y0 + 20, x1 - 26, y0 + 88), 8, 8)
    c.drawRRect(win, _G(_lin(0, y0 + 20, 0, y0 + 88, ["#FFE7B2", "#F7C981"])))
    c.drawRRect(win, _S("#5A331F", 4))
    c.drawLine((x0 + x1) / 2, y0 + 20, (x0 + x1) / 2, y0 + 88, _S("#5A331F", 3))
    # knob
    c.drawCircle(x1 - 20, 6, 8, _P("#E2B65C"))
    c.drawCircle(x1 - 22, 4, 3, _P("#FFF0C0", 0.9))
    # light under the door + pool on the floor
    c.drawRect(skia.Rect(x0, y1 - 3, x1, y1), _P("#FFE7B2", 0.9))
    c.drawPath(_poly([(x0, y1), (x1, y1), (x1 + 50, 150), (x0 - 40, 150)]),
               _G(_lin(0, y1, 0, 150, [_c("#FFD99A", 0.45), _c("#FFD99A", 0.0)])))
    # dog's shadow
    c.drawOval(skia.Rect(-20, 104, 140, 128), _P("#5C3A28", 0.35))


def _dog(c, age):
    fur, shade, dark, light = "#D99B57", "#B97B3E", "#8E5A2C", "#F0C185"
    wag = math.sin(age * TAU * 2.6) * (0.8 + 0.2 * math.sin(age * 0.7))
    # tail (behind the body), sweeping
    c.save()
    c.rotate(-34 + 30 * wag, 140, 96)
    tail = _sp([(132, 88), (160, 92), (186, 84), (204, 66), (212, 50), (216, 58), (208, 84), (186, 104), (156, 108),
                (132, 104)])
    c.drawPath(tail, _P(fur))
    c.drawPath(_sp([(176, 92), (200, 74), (212, 52), (210, 72), (192, 96)]), _P(light, 0.7))
    c.drawPath(tail, _S(dark, 1.2, 0.35))
    c.restore()
    # haunch + body (sitting, facing left toward the door)
    c.drawPath(_sp([(40, -10), (90, -18), (130, 10), (156, 60), (150, 104), (100, 112), (56, 108), (36, 60)]), _P(fur))
    c.drawPath(_sp([(96, 36), (140, 44), (152, 84), (138, 108), (96, 110), (84, 76)]), _P(shade))   # haunch
    c.drawPath(_sp([(100, 100), (132, 102), (138, 112), (98, 112)]), _P(dark, 0.8))                 # back paw
    # chest + front legs
    c.drawPath(_sp([(30, -28), (60, -12), (64, 40), (56, 108), (40, 112), (30, 60), (18, 10)]), _P(light))
    for x in (36, 56):
        c.drawPath(_sp([(x - 8, 40), (x + 8, 40), (x + 8, 104), (x + 12, 112), (x - 10, 112), (x - 9, 100)]), _P(fur))
        c.drawLine(x - 4, 107, x - 4, 112, _S(dark, 1.2, 0.6))
    # head looking at the door, slight eager lean
    lean = 2.5 * math.sin(age * 1.3) - 3
    c.save()
    c.rotate(lean, 40, -20)
    head = _sp([(56, -56), (54, -86), (34, -104), (6, -104), (-12, -92), (-34, -80), (-46, -70), (-46, -58),
                (-30, -50), (-4, -48), (20, -36), (44, -30)])
    c.drawPath(head, _P(fur))
    c.drawPath(_sp([(-44, -70), (-30, -60), (-10, -52), (-30, -50), (-46, -58)]), _P(light, 0.8))  # muzzle
    c.drawCircle(-46, -70, 7, _P("#2A1A12"))                                                    # nose
    c.drawCircle(-48, -72, 2, _P("#FFFFFF", 0.6))
    c.drawPath(_sp([(-34, -56), (-24, -54), (-14, -55)], closed=False), _S("#5A3420", 1.6, 0.8))  # mouth
    c.drawCircle(-6, -86, 5.5, _P("#2A1A12"))                                                   # eye
    c.drawCircle(-7.5, -88, 1.8, _P("#FFFFFF"))
    c.drawPath(_sp([(-12, -94), (-2, -97)], closed=False), _S(dark, 2, 0.7))                     # brow
    perk = max(0.0, math.sin(age * 0.9)) ** 4
    c.save()
    c.rotate(-10 * perk, 26, -96)
    c.drawPath(_sp([(14, -102), (34, -100), (46, -76), (40, -52), (26, -56), (20, -80)]), _P(dark))  # ear
    c.restore()
    c.restore()
    # collar
    c.drawPath(_sp([(22, -40), (50, -30), (52, -22), (20, -32)]), _P("#C0473F"))
    c.drawCircle(30, -24, 4, _P("#F2C94C"))


def _dd_anim(c, age, t):
    # a silhouette arriving behind the frosted window (someone's coming home)
    x0, y0, x1, y1 = _DOOR
    arrive = _ss(1.5, 4.5, age)
    if arrive > 0:
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 26, y0 + 20, x1 - 26, y0 + 88), 8, 8), True)
        hx = lerp(x0 - 10, (x0 + x1) / 2, arrive)
        c.drawCircle(hx, y0 + 62, 22, _P("#9C6E4C", 0.45 * arrive))
        c.drawOval(skia.Rect(hx - 40, y0 + 80, hx + 40, y0 + 140), _P("#9C6E4C", 0.45 * arrive))
        c.restore()
    c.save()
    c.translate(-30, 0)
    _dog(c, age * (1 + 0.6 * arrive))
    c.restore()


# ---------------------------------------------------------------- kitchen_dawn
_KW = skia.RRect.MakeRectXY(skia.Rect(-40, -170, 170, -10), 10, 10)


def _kd_static(c):
    c.drawRect(skia.Rect(-210, -210, 210, 210), _G(_lin(-200, -200, 200, 200, ["#F2DDB7", "#E2C094", "#C99A6E"])))
    # tiles hint
    for xx in range(-200, 210, 46):
        c.drawLine(xx, -10, xx, 40, _S("#D6B48A", 1.5, 0.6))
    c.drawLine(-210, 40, 210, 40, _S("#D6B48A", 1.5, 0.6))
    # dawn window
    c.save()
    c.clipRRect(_KW, True)
    c.drawRect(skia.Rect(-40, -170, 170, -10), _G(_lin(0, -170, 0, -10, ["#AFC0DD", "#F2C9B0", "#FFD49A"], [0, 0.6, 1])))
    c.drawPath(_sp([(-40, -40), (20, -52), (90, -46), (170, -58), (170, -10), (-40, -10)]), _P("#C9A390", 0.7))  # hills
    c.restore()
    c.drawRRect(_KW, _S("#FFF6E6", 9))
    c.drawLine(65, -170, 65, -10, _S("#FFF6E6", 7))
    c.drawLine(-40, -90, 170, -90, _S("#FFF6E6", 7))
    c.drawRect(skia.Rect(-52, -12, 182, 0), _P("#FFF6E6"))                       # sill
    c.drawPath(_sp([(120, -18), (112, -40), (126, -54), (138, -40), (132, -18)]), _P("#7FA37A"))  # little plant
    c.drawRect(skia.Rect(114, -22, 140, -10), _P("#C9785A"))
    # table / counter
    c.drawRect(skia.Rect(-210, 92, 210, 210), _P("#A86F48"))
    c.drawRect(skia.Rect(-210, 92, 210, 106), _P("#C18A5E"))
    c.drawLine(-210, 140, 210, 140, _S("#93603D", 2, 0.5))
    # two cups
    for (x, body, band) in ((-70, "#F4EEE4", "#6E8DB0"), (34, "#F4EEE4", "#D98C6A")):
        c.drawOval(skia.Rect(x - 40, 120, x + 40, 134), _P("#7A4E31", 0.45))
        c.drawPath(_sp([(x - 32, 70), (x + 32, 70), (x + 28, 118), (x + 18, 128), (x - 18, 128), (x - 28, 118)]), _P(body))
        c.drawPath(_poly([(x - 31, 88), (x + 31, 88), (x + 30.2, 98), (x - 30.2, 98)]), _P(band))
        c.drawPath(_sp([(x + 30, 82), (x + 48, 84), (x + 48, 104), (x + 28, 108)], closed=False), _S(body, 7))
        c.drawOval(skia.Rect(x - 32, 63, x + 32, 77), _P("#E8DED0"))
        c.drawOval(skia.Rect(x - 27, 66, x + 27, 75), _P("#B3703C"))   # tea
        c.drawPath(_sp([(x - 26, 76), (x - 24, 110), (x - 16, 124)], closed=False), _S("#FFFFFF", 3, 0.5))


def _kd_anim(c, age, t):
    # sunbeams through the window (soft, shimmering)
    sh = 0.75 + 0.25 * math.sin(age * 0.8)
    for (a, b, w, al) in ((40, -150, 70, 0.17), (-10, -160, 40, 0.11)):
        c.drawPath(_poly([(a, b), (a + w, b), (a + w - 230, b + 330), (a - 230, b + 330)]),
                   _G(_lin(a, b, a - 230, b + 330, [_c("#FFF2CC", al * sh), _c("#FFF2CC", 0)])))
    # sun rising behind the window
    sy = -40 - 6 * clamp(age / 6.0)
    c.save()
    c.clipRRect(_KW, True)
    _blob(c, 120, sy, 70, "#FFE2A0", 0.8, kind="soft", add=True)
    c.drawCircle(120, sy, 16, _P("#FFF4D6"))
    c.restore()
    # teapot pouring (held from the right)
    tilt = 30 + 3 * math.sin(age * 1.3)
    tx, ty = 104, 6
    c.save()
    c.translate(tx, ty)
    c.rotate(-tilt)
    c.drawPath(_sp([(-46, -10), (-40, -40), (0, -50), (40, -40), (46, -10), (34, 18), (-34, 18)]), _P("#7FA3A0"))
    c.drawPath(_sp([(-20, -48), (0, -62), (20, -48)]), _P("#6C8F8C"))
    c.drawCircle(0, -64, 6, _P("#E9D9B8"))
    c.drawPath(_sp([(-44, -6), (-72, -22), (-86, -40), (-80, -42), (-64, -26), (-40, -18)]), _P("#7FA3A0"))   # spout
    c.drawPath(_sp([(40, -34), (64, -30), (66, 4), (40, 6)], closed=False), _S("#6C8F8C", 8))               # handle
    c.drawPath(_sp([(-34, -36), (-10, -42)], closed=False), _S("#FFFFFF", 4, 0.45))
    c.drawPath(_sp([(56, -40), (78, -42), (86, -24), (80, 4), (58, 8), (60, -20)]), _P("#E0AE8A"))         # hand
    c.drawPath(_sp([(78, -48), (140, -60), (150, 20), (80, 14)]), _P("#C76B5A"))                            # sleeve
    c.restore()
    # stream of tea from the spout tip into the right cup
    a_ = math.radians(-tilt)
    spx, spy = -84, -41
    sx = tx + spx * math.cos(a_) - spy * math.sin(a_)
    sy2 = ty + spx * math.sin(a_) + spy * math.cos(a_)
    cupx, cupy = 34, 70
    pts = []
    for k in range(8):
        u = k / 7
        x = lerp(sx, cupx, u * u) + 1.5 * math.sin(age * 9 + u * 6) * u
        y = lerp(sy2, cupy, u)
        pts.append((x, y))
    c.drawPath(_sp(pts, closed=False), _S("#B9733A", 4.5, 0.95))
    c.drawPath(_sp(pts, closed=False), _S("#F2B36E", 1.5, 0.7))
    c.drawCircle(cupx, cupy, 5 + 1.5 * math.sin(age * 11), _P("#E8B07A", 0.6))
    # steam from both cups
    for (x, ph) in ((-70, 0.0), (34, 1.7)):
        for j in range(3):
            u = ((age * 0.35 + j / 3 + ph) % 1.0)
            base_y = 60 - u * 120
            pts = [(x - 10 + j * 10 + 9 * math.sin(age * 1.6 + j + q * 1.3 + ph), base_y - q * 16) for q in range(4)]
            c.drawPath(_sp(pts, closed=False), _S("#FFFFFF", 5, 0.32 * math.sin(u * math.pi)))
    # dust in the beam
    for i in range(6):
        x = -60 + ((i * 53 + age * 6) % 200)
        y = -80 + ((i * 41 + age * 4) % 160)
        _blob(c, x, y, 4.5, "#FFF6DD", 0.5 * (0.5 + 0.5 * math.sin(age * 2 + i)), kind="core", add=True)


# ---------------------------------------------------------------- friends_table
_FT_PEOPLE = (  # x, y (shoulder line), scale, facing (+1 right), laugh phase, shirt color
    (-138, 72, 1.08, 1, 0.0, "#4A2F3A"),
    (-52, 40, 0.86, 1, 1.9, "#3B3046"),
    (58, 40, 0.88, -1, 0.8, "#4A3326"),
    (142, 74, 1.1, -1, 2.7, "#2F3A3A"),
)


def _ft_static(c):
    c.drawRect(skia.Rect(-210, -210, 210, 210), _G(_rad(0, -40, 280, ["#7A4A2E", "#4A2C22", "#2A1A18"], [0, 0.5, 1])))
    # window with night blue + string lights hint
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -150, -70, -50), 6, 6), _P("#2C3350", 0.8))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -150, -70, -50), 6, 6), _S("#5E3A26", 5))
    for i in range(7):
        c.drawCircle(-10 + i * 30, -150 + 10 * math.sin(i * 1.4), 3.5, _P("#FFD08A", 0.85))
    # light cone from the lamp
    c.drawPath(_poly([(-30, -110), (30, -110), (190, 140), (-190, 140)]),
               _G(_lin(0, -110, 0, 140, [_c("#FFD49A", 0.30), _c("#FFD49A", 0.04)])))


def _person(c, x, y, s, facing, laugh, shirt, rim, arm=None, arm_amt=0.0):
    """Warm rim-lit silhouette in profile; laugh 0..1 throws the head back and drops the jaw.
    arm: None | 'glass' (raised toast) | 'table' (hand slapping the table)."""
    skin = "#3A2622"
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    body = _sp([(-50, 120), (-48, 34), (-32, 2), (0, -6), (28, 0), (44, 30), (50, 120)])
    c.drawPath(body, _P(shirt))
    c.drawPath(_sp([(28, 0), (44, 30), (50, 120)], closed=False), _S(rim, 3, 0.7))
    if arm == "glass":
        lift = arm_amt
        c.drawPath(_sp([(30, 30), (54, 40 - 50 * lift), (66, 12 - 70 * lift), (58, 4 - 70 * lift), (42, 30 - 40 * lift),
                        (20, 44)]), _P(shirt))
        gx, gy = 62, -6 - 70 * lift
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(gx - 7, gy - 22, gx + 7, gy + 4), 3, 3), _P("#F4D7A0", 0.75))
        c.drawRect(skia.Rect(gx - 5.5, gy - 10, gx + 5.5, gy + 2), _P("#E2A04A", 0.85))
        c.drawCircle(gx + 2, gy - 18, 2.2, _P("#FFFFFF", 0.8))
    elif arm == "table":
        dy = 10 * arm_amt
        c.drawPath(_sp([(26, 36), (60, 70 + dy), (80, 92 + dy), (70, 104 + dy), (48, 92 + dy), (16, 60)]), _P(shirt))
        c.drawOval(skia.Rect(66, 92 + dy, 90, 106 + dy), _P(skin))
    c.save()
    c.translate(0, -8 - 4 * laugh)
    c.rotate(-24 * laugh, 0, -14)
    c.drawRect(skia.Rect(-9, -16, 9, 6), _P(skin))
    jaw = 14 * laugh
    c.save()
    c.rotate(jaw, 6, -26)
    c.drawPath(_sp([(-12, -30), (6, -30), (22, -24), (26, -18), (16, -10), (0, -10), (-16, -16)]), _P(skin))
    c.drawPath(_sp([(22, -24), (26, -18), (16, -10)], closed=False), _S(rim, 2.4, 0.8))
    c.restore()
    head = _sp([(-22, -40), (-14, -62), (6, -68), (22, -58), (28, -44), (32, -36), (27, -31), (24, -26),
                (6, -26), (-16, -28)])
    c.drawPath(head, _P(skin))
    c.drawPath(_sp([(-18, -52), (-4, -70), (14, -68), (6, -58), (-10, -48)]), _P("#2A1A18"))   # hair tuft
    c.drawPath(_sp([(6, -68), (22, -58), (28, -44), (32, -36), (27, -31), (24, -26)], closed=False),
               _S(rim, 2.6, 0.9))
    c.drawPath(_sp([(10, -46), (15, -49), (20, -46)], closed=False), _S(rim, 1.8, 0.55 + 0.4 * laugh))  # smiling eye
    c.restore()
    c.restore()


def _ft_anim(c, age, t):
    sway = 4.0 * math.sin(age * 0.9)
    # lamp
    c.save()
    c.rotate(sway, 0, -210)
    c.drawLine(0, -210, 0, -128, _S("#1E1210", 2.5))
    c.drawPath(_poly([(-34, -96), (34, -96), (16, -130), (-16, -130)]), _P("#C9763B"))
    c.drawPath(_poly([(-34, -96), (34, -96), (30, -92), (-30, -92)]), _P("#FFE2A6"))
    _blob(c, 0, -92, 90, "#FFC874", 0.6, kind="soft", add=True)
    c.drawCircle(0, -94, 9, _P("#FFF4D8"))
    c.restore()
    # people behind the table, laughing in overlapping waves
    for i, (x, y, s_, f, ph, shirt) in enumerate(_FT_PEOPLE):
        wave = max(0.0, math.sin(age * 1.1 + ph)) ** 1.5
        laugh = clamp(0.3 + 0.7 * wave)
        bob = 4 * wave * abs(math.sin(age * 10 + ph * 3))
        arm = "glass" if i == 0 else ("table" if i == 3 else None)
        arm_amt = wave if i == 0 else abs(math.sin(age * 7 + ph)) * wave
        _person(c, x, y - bob, s_, f, laugh, shirt, "#FFC27A", arm, arm_amt)
        if wave > 0.4:                                       # little laugh ticks
            hx = x + f * 8 * s_
            hy = y - 80 * s_ - bob
            for k in (-1, 1):
                a_ = clamp((wave - 0.4) / 0.4)
                c.drawLine(hx + k * 30 * s_, hy - 6, hx + k * 40 * s_, hy - 14, _S("#FFD9A0", 2.2, 0.6 * a_))
    # table + things on it
    c.drawOval(skia.Rect(-190, 96, 190, 176), _P("#7A4A2E"))
    c.drawOval(skia.Rect(-182, 92, 182, 160), _P("#A8683F"))
    c.drawOval(skia.Rect(-120, 104, 120, 150), _P("#C8844F", 0.5))
    for (x, y) in ((-90, 120), (70, 118)):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 9, y - 26, x + 9, y + 4), 3, 3), _P("#F4D7A0", 0.55))
        c.drawRect(skia.Rect(x - 7, y - 10, x + 7, y + 2), _P("#E2A04A", 0.7))
    c.drawOval(skia.Rect(-40, 112, 40, 136), _P("#F1E4CF"))
    c.drawOval(skia.Rect(-26, 116, 26, 130), _P("#D98C5A"))
    # candle-ish glints on glasses
    tw = 0.7 + 0.3 * math.sin(age * 5)
    _blob(c, -86, 98, 8, "#FFF0D0", 0.8 * tw, kind="core", add=True)
    _blob(c, 74, 96, 8, "#FFF0D0", 0.8 * (1.4 - tw), kind="core", add=True)


# ---------------------------------------------------------------- sea_sunset
_HORIZON = 34.0


def _ss_static(c):
    c.drawRect(skia.Rect(-210, -210, 210, _HORIZON),
               _G(_lin(0, -200, 0, _HORIZON, ["#5E4E86", "#B8668A", "#EE9A72", "#FAD08E"], [0, 0.42, 0.78, 1])))
    for (x, y, w, a) in ((-120, -110, 150, 0.35), (60, -80, 190, 0.3), (-40, -40, 120, 0.25)):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - w / 2, y - 5, x + w / 2, y + 5), 5, 5), _P("#F2A98E", a))
    c.drawRect(skia.Rect(-210, _HORIZON, 210, 210), _G(_lin(0, _HORIZON, 0, 200, ["#7A5F84", "#3E3F6C", "#252A50"])))


def _ss_anim(c, age, t):
    sy = _HORIZON - 12 + 3.0 * clamp(age / 8.0)
    c.save()
    c.clipRect(skia.Rect(-210, -210, 210, _HORIZON))
    _blob(c, 0, sy, 150, "#FFC98A", 0.55, kind="soft", add=True)
    c.drawCircle(0, sy, 38, _P("#FFE7B0"))
    c.restore()
    c.drawLine(-210, _HORIZON, 210, _HORIZON, _S("#FFE0A8", 2, 0.6))
    # glitter path below the sun
    for i in range(14):
        h = lambda k: hash01(i * 5 + k, 77)  # noqa: E731
        y = _HORIZON + 8 + 150 * h(1) ** 1.4
        spread = 14 + (y - _HORIZON) * 0.45
        x = (h(2) - 0.5) * 2 * spread + 6 * math.sin(age * 1.2 + i)
        w = 6 + 16 * h(3) * (0.4 + (y - _HORIZON) / 150)
        a = 0.35 + 0.45 * (0.5 + 0.5 * math.sin(age * (1.5 + h(4) * 2) + TAU * h(5)))
        c.drawLine(x - w, y, x + w, y, _S("#FFE2A6", 2.4, a * (1 - (y - _HORIZON) / 220)))
    # gentle waves rolling (slow sine strokes)
    for j in range(5):
        y0 = _HORIZON + 24 + j * j * 7 + j * 14
        amp = 2 + j * 1.6
        ph = age * (0.6 + 0.15 * j) + j * 1.3
        pts = [(x, y0 + amp * math.sin(x * 0.03 + ph)) for x in range(-210, 220, 30)]
        c.drawPath(_sp(pts, closed=False), _S("#9C88B8", 2 + j * 0.6, 0.35 - j * 0.04))
    # two birds gliding
    for i in range(2):
        bx = -150 + ((age * 14 + i * 60) % 360) - 20
        by = -90 + i * 22 + 4 * math.sin(age * 1.5 + i)
        fl = 6 * math.sin(age * 4 + i)
        c.drawPath(_sp([(bx - 12, by - fl * 0.5), (bx - 5, by - 3), (bx, by), (bx + 5, by - 3), (bx + 12, by - fl * 0.5)],
                       closed=False, tension=0.3), _S("#4A3352", 2.2))


# ---------------------------------------------------------------- bubble assembly
# layer stacks: plain functions are static (recorded once into a Picture); ("a", fn) are animated fn(c, age, t)
_MEM_LAYERS = {
    "car_window": (_cw_back, ("a", _cw_city), _cw_front, ("a", _cw_light)),
    "hands": (_hands_back, ("a", _hands_anim)),
    "dog_door": (_dd_static, ("a", _dd_anim)),
    "kitchen_dawn": (_kd_static, ("a", _kd_anim)),
    "friends_table": (_ft_static, ("a", _ft_anim)),
    "sea_sunset": (_ss_static, ("a", _ss_anim)),
}
MEMORY_KINDS = tuple(_MEM_LAYERS)


@lru_cache(maxsize=64)
def _mem_picture(fn):
    return _record(fn)


def _annulus(r0, r1):
    p = skia.Path()
    p.addCircle(0, 0, r1)
    p.addCircle(0, 0, max(r0, 0.01))
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p


def draw_memory(canvas, t, kind, cx, cy, r, alpha=1.0, age=0.0, glow=0.0, rim_color="#FFE3B8", develop=True):
    """Round soft-edged memory bubble at (cx, cy) radius r with an animated wordless vignette.

    kind: one of MEMORY_KINDS ('car_window', 'hands', 'dog_door', 'kitchen_dawn', 'friends_table', 'sea_sunset').
    age: seconds since the bubble appeared (drives the internal animation; with develop=True the picture
    'develops' out of a warm haze over the first ~1.1 s). glow 0..1: extra rim/inner light (climax)."""
    if alpha <= 0.003 or r <= 1:
        return
    if kind not in _MEM_LAYERS:
        raise ValueError(f"unknown memory kind {kind!r}")
    s = r / _MR
    dev = smoothstep(age / 1.1) if develop else 1.0
    canvas.save()
    canvas.translate(cx, cy)
    # ---- content layer (clipped, vignetted, soft edge)
    lp = skia.Paint()
    lp.setAlphaf(clamp(alpha))
    canvas.saveLayer(skia.Rect(-r - 1, -r - 1, r + 1, r + 1), lp)
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    canvas.clipPath(clip, True)
    canvas.save()
    canvas.scale(s, s)
    for item in _MEM_LAYERS[kind]:
        if isinstance(item, tuple):
            item[1](canvas, age, t)
        else:
            canvas.drawPicture(_mem_picture(item))
    canvas.restore()
    # warm storybook unification + inner vignette
    canvas.drawPath(_annulus(r * 0.68, r + 1), _G(_rad(0, 0, r, [_c("#3A1E14", 0.0), _c("#3A1E14", 0.16),
                                                                  _c("#2A140E", 0.55)], [0.68, 0.85, 1.0])))
    haze = (1 - dev) * 0.92
    if haze > 0.003:
        canvas.drawCircle(0, 0, r, _P("#FFF0D8", haze))
    if glow > 0:
        pg = _G(_rad(0, 0, r, [_c("#FFE6B8", 0.0), _c("#FFE6B8", 0.28 * glow)], [0.55, 1.0]))
        pg.setBlendMode(skia.BlendMode.kPlus)
        canvas.drawCircle(0, 0, r, pg)
    # soft edge: erase toward the rim
    pe = _G(_rad(0, 0, r, [_c("#000000", 0.0), _c("#000000", 0.35), _c("#000000", 1.0)], [0.86, 0.95, 1.0]))
    pe.setBlendMode(skia.BlendMode.kDstOut)
    canvas.drawPath(_annulus(r * 0.86, r + 1), pe)
    canvas.restore()
    # ---- glowing rim + bubble highlight (additive)
    ga = clamp(alpha) * (0.85 + 0.6 * glow) * (0.6 + 0.4 * dev)
    rc = _rgb(rim_color)
    outer = r * (1.12 + 0.10 * glow)
    k = r / outer
    pr = _G(_rad(0, 0, outer, [_c(rc, 0.0), _c(rc, 0.22 * ga), _c(rc, 0.30 * ga), _c(rc, 0.08 * ga), _c(rc, 0.0)],
                 [0.88 * k, 0.95 * k, 0.99 * k, 1.03 * k, 1.0]))
    pr.setBlendMode(skia.BlendMode.kPlus)
    canvas.drawPath(_annulus(r * 0.88, outer), pr)
    p = _S(_mixrgb(rc, "#FFFFFF", 0.5), max(1.0, r * 0.008), 0.45 * ga)
    p.setBlendMode(skia.BlendMode.kPlus)
    canvas.drawCircle(0, 0, r * 0.975, p)
    hl = _S("#FFFFFF", r * 0.035, 0.22 * ga)
    hl.setBlendMode(skia.BlendMode.kPlus)
    arc = skia.Path()
    arc.addArc(skia.Rect(-r * 0.86, -r * 0.86, r * 0.86, r * 0.86), 198, 48)
    canvas.drawPath(arc, hl)
    canvas.drawCircle(-r * 0.43, -r * 0.62, r * 0.025, _P("#FFFFFF", 0.35 * ga))
    canvas.restore()


# =========================================================================== holo cards
CARD_W, CARD_H = 170.0, 230.0
CARD_TITLES = {1: "SYMPHONY", 2: "SOLO KAZOO", 3: "ARCADE", 4: "LO-FI", 5: "LULLABY", 6: "BAROQUE",
               7: "SEA SHANTY", 8: "WHALE SONG"}
CARD_ICONS = {1: "symphony", 2: "kazoo", 3: "arcade", 4: "lofi", 5: "lullaby", 6: "symphony", 7: "symphony",
              8: "symphony"}
_HOLO = "#7FFFE9"
_HOLO_MID = "#2EC4B6"
_HOLO_DARK = "#0A2E36"


def _hp(color=_HOLO, a=1.0, w=0.0, add=True, blur=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setColor(_c(color, a))
    if w:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if add:
        p.setBlendMode(skia.BlendMode.kPlus)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _tracked(c, text, x, y, size, color, a, weight=300, tracking=1.0, align="center", family="Inter Display",
             add=True, glow=0.0, max_w=None):
    """Tracked single-line text (baseline y). Shrinks to max_w if given. Returns drawn width."""
    from anim.core import font
    f = font(size, family, weight)
    widths = [f.measureText(ch) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if max_w and total > max_w:
        k = max_w / total
        f = font(size * k, family, weight)
        widths = [w_ * k for w_ in widths]
        tracking *= k
        total = max_w
    sx = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    if glow > 0:
        pg = _hp(color, a * glow, add=add, blur=max(1.0, size * 0.18))
        xx = sx
        for ch, w_ in zip(text, widths):
            c.drawString(ch, xx, y, f, pg)
            xx += w_ + tracking
    p = _hp(color, a, add=add)
    xx = sx
    for ch, w_ in zip(text, widths):
        c.drawString(ch, xx, y, f, p)
        xx += w_ + tracking
    return total


# ---------------------------------------------------------------- icons (box ~100 x 100 centered at 0,0)
def _icon_symphony(c, t, a):
    # violin-scroll spiral with a curling staff and floating notes
    pts = []
    for k in range(60):
        th = k / 59 * 3.2 * math.pi
        r = 34 * math.exp(-0.16 * th)
        pts.append((-8 + r * math.cos(th + 1.2 + 0.15 * math.sin(t * 0.8)), 4 + r * math.sin(th + 1.2 + 0.15 * math.sin(t * 0.8))))
    sp = _sp(pts, closed=False)
    c.drawPath(sp, _hp(_HOLO, 0.35 * a, 7, blur=3))
    c.drawPath(sp, _hp(_HOLO, 0.95 * a, 2.6))
    for j in range(3):                                   # staff lines sweeping out of the scroll
        yo = -30 + j * 8
        st = _sp([(-40, yo + 34), (-6, yo + 10), (22, yo - 4), (48, yo - 2 + 3 * math.sin(t * 1.3 + j))], closed=False)
        c.drawPath(st, _hp(_HOLO, 0.45 * a, 1.3))
    for j, (nx_, ny_) in enumerate(((16, -26), (32, -34), (44, -18))):
        bob = 3.5 * math.sin(t * 2.2 + j * 1.9)
        y = ny_ + bob
        c.save()
        c.translate(nx_, y)
        c.rotate(-20)
        c.drawOval(skia.Rect(-5.5, -4, 5.5, 4), _hp(_HOLO, 0.95 * a))
        c.restore()
        c.drawLine(nx_ + 4.5, y - 1, nx_ + 4.5, y - 20, _hp(_HOLO, 0.9 * a, 1.6))
    c.drawLine(36.5, -55 + 3.5 * math.sin(t * 2.2 + 1.9), 48.5, -40 + 3.5 * math.sin(t * 2.2 + 3.8), _hp(_HOLO, 0.8 * a, 2.4))


def _icon_kazoo(c, t, a):
    body = _sp([(-42, -6), (10, -12), (40, -18), (46, -2), (40, 14), (10, 8), (-42, 6)])
    c.drawPath(body, _hp(_HOLO_MID, 0.30 * a))
    c.drawPath(body, _hp(_HOLO, 0.95 * a, 2.4))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-4, -26, 14, -9), 4, 4), _hp(_HOLO, 0.9 * a, 2.2))   # turret
    c.drawLine(-2, -26, 12, -26, _hp(_HOLO, 0.9 * a, 3))
    for j in range(3):                                   # pulsing sound arcs from the bell
        u = (t * 1.6 + j / 3) % 1.0
        r = 10 + 22 * u
        arc = skia.Path()
        arc.addArc(skia.Rect(44 - r, -2 - r, 44 + r, -2 + r), -40, 80)
        c.drawPath(arc, _hp(_HOLO, a * (1 - u) * 0.9, 2.0))
    zz = [(-40 + k * 7, 24 + (4 if k % 2 else -4) * (0.6 + 0.4 * math.sin(t * 14))) for k in range(9)]
    c.drawPath(_poly(zz, closed=False), _hp(_HOLO, 0.55 * a, 1.6))


_HEART = ("01100110", "11111111", "11111111", "11111111", "01111110", "00111100", "00011000")
# the heart as horizontal runs (col, row, length) -> one gap-free path when drawn solid
_HEART_RUNS = tuple((m.start(), j, len(m.group())) for j, row in enumerate(_HEART) for m in re.finditer("1+", row))
_PLUS = ((-1, 0, 3, 1), (0, -1, 1, 3))       # 8-bit plus sparkle as two bars (col, row, w, h) in cells


def _axis_aligned(c) -> bool:
    m = c.getTotalMatrix()
    return abs(m.getSkewX()) < 1e-6 and abs(m.getSkewY()) < 1e-6 and not m.hasPerspective()


def _even_grid(c, x, y, cell):
    """Pixel-art snapping for small sprites. Under an axis-aligned uniform-scale matrix returns local
    (x, y, cell) moved so the sprite origin lands on an EVEN device pixel and the cell is a whole, even number
    of device px (>= 2): crisp edges whose colour survives 4:2:0 chroma subsampling. None when the matrix
    rotates or skews (draw anti-aliased instead: aliased rotated cells crawl)."""
    if not _axis_aligned(c):
        return None
    m = c.getTotalMatrix()
    sx, sy = m.getScaleX(), m.getScaleY()
    if abs(sx) < 1e-6 or abs(abs(sy) - abs(sx)) > 1e-3 * abs(sx):
        return None
    tx, ty = m.getTranslateX(), m.getTranslateY()
    X = 2.0 * round((sx * x + tx) / 2.0)
    Y = 2.0 * round((sy * y + ty) / 2.0)
    cd = max(2.0, 2.0 * round(abs(cell * sx) / 2.0))
    return (X - tx) / sx, (Y - ty) / sy, cd / abs(sx)


def _icon_arcade(c, t, a):
    # 8-bit heart beating by one whole local unit per cell (8.5 -> 9.5, ~12 %). Close and upright (the card-3
    # focus) its cells keep an exact 1-device-px grid, every edge snapped to a device pixel. Small and tilted
    # (in the fan) it is one solid anti-aliased path: a sub-pixel gap grid there aliased into crawling dots
    # that the encoder smeared into a blob. The two cross-fade over 0.5..3 deg of tilt (the card swooping
    # between focus and fan), so the change never pops on a still card.
    beat = (t * 2.4) % 1.0 < 0.18
    px = 8.5 + (1.0 if beat else 0.0)
    ox, oy = -4 * px, -3.5 * px - 10
    heart = skia.Path()
    for (i, j, n) in _HEART_RUNS:
        heart.addRect(skia.Rect.MakeXYWH(ox + i * px, oy + j * px, n * px, px))
    c.drawPath(heart, _hp("#FF77A8", 0.35 * a, blur=5))
    m = c.getTotalMatrix()
    s = _mscale(c)
    uniform = (not m.hasPerspective() and m.getScaleX() > 0 and m.getScaleY() > 0
               and abs(m.getScaleX() - m.getScaleY()) < 0.01 * s)
    wg = 0.0                                             # weight of the snapped-grid look
    if uniform:
        ang = abs(math.degrees(math.atan2(m.getSkewY(), m.getScaleX())))
        wg = (1.0 - smoothstep((ang - 0.5) / 2.5)) * smoothstep((px * s - 5.0) / 2.0)
    if wg < 0.999:                                       # solid, anti-aliased
        c.drawPath(heart, _hp("#FF77A8", 0.9 * a * (1 - wg)))
        c.drawRect(skia.Rect.MakeXYWH(ox + 1 * px, oy + 1 * px, px, px), _hp("#FFFFFF", 0.8 * a * (1 - wg)))
    if wg > 0.001:                                       # device-px grid (cells snapped, 1-px gaps)
        hc = m.mapXY(0.0, -10.0)                         # heart center in device px
        cd = px * s
        ex = lambda i: round(hc.x() + (i - 4) * cd)  # noqa: E731
        ey = lambda j: round(hc.y() + (j - 3.5) * cd)  # noqa: E731
        p = _hp("#FF77A8", 0.9 * a * wg)
        p.setAntiAlias(False)
        c.save()
        c.resetMatrix()
        for (i0, j, n) in _HEART_RUNS:
            for i in range(i0, i0 + n):
                c.drawRect(skia.Rect(ex(i), ey(j), ex(i + 1) - 1, ey(j + 1) - 1), p)
        p.setColor(_c("#FFFFFF", 0.8 * a * wg))
        c.drawRect(skia.Rect(ex(1), ey(1), ex(2) - 1, ey(2) - 1), p)
        c.restore()
    # tiny joystick
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-20, 36, 20, 46), 3, 3), _hp(_HOLO, 0.9 * a, 2))
    tilt = 7 * math.sin(t * 5)
    c.drawLine(0, 36, tilt, 24, _hp(_HOLO, 0.9 * a, 2.4))
    c.drawCircle(tilt, 21, 5, _hp(_HOLO, 0.95 * a))
    # blinking pixel pluses: solid (no sub-pixel gaps), snapped to even device pixels when axis-aligned
    py_ = _hp("#FFEC27", 0.85 * a)
    for k, (sx, sy) in enumerate(((36, -34), (-40, 22), (40, 18))):
        on = ((t * 3 + k * 0.33) % 1.0) < 0.5
        if on:
            cell = 3.5
            x0, y0 = sx - cell / 2, sy - cell / 2          # top-left of the center cell
            g = _even_grid(c, x0, y0, cell)
            if g:
                x0, y0, cell = g
            py_.setAntiAlias(g is None)
            plus = skia.Path()
            for (i, j, w_, h_) in _PLUS:
                plus.addRect(skia.Rect.MakeXYWH(x0 + i * cell, y0 + j * cell, w_ * cell, h_ * cell))
            c.drawPath(plus, py_)


def _icon_lofi(c, t, a):
    # rainy window behind (top left)
    win = skia.RRect.MakeRectXY(skia.Rect(-48, -50, 10, 4), 5, 5)
    c.drawRRect(win, _hp(_HOLO_MID, 0.18 * a))
    c.drawRRect(win, _hp(_HOLO, 0.6 * a, 1.6))
    c.drawLine(-19, -50, -19, 4, _hp(_HOLO, 0.45 * a, 1.2))
    c.drawLine(-48, -23, 10, -23, _hp(_HOLO, 0.45 * a, 1.2))
    c.save()
    c.clipRRect(win, True)
    for k in range(6):
        x = -44 + k * 10
        y = -54 + ((t * 40 + k * 23) % 64)
        c.drawLine(x, y, x - 1.5, y + 8, _hp("#BFEFFF", 0.7 * a, 1.2))
    c.restore()
    # steaming mug (right)
    mug = _sp([(6, 4), (40, 4), (38, 40), (32, 46), (14, 46), (8, 40)])
    c.drawPath(mug, _hp(_HOLO_DARK, 0.6 * a, add=False))
    c.drawPath(mug, _hp(_HOLO_MID, 0.35 * a))
    c.drawPath(mug, _hp(_HOLO, 0.95 * a, 2.2))
    c.drawPath(_sp([(39, 12), (50, 14), (50, 30), (38, 34)], closed=False), _hp(_HOLO, 0.9 * a, 2.2))
    for j in range(2):
        u = (t * 0.6 + j * 0.5) % 1.0
        pts = [(16 + j * 12 + 4 * math.sin(t * 2 + q + j), 0 - u * 14 - q * 7) for q in range(4)]
        c.drawPath(_sp(pts, closed=False), _hp(_HOLO, 0.75 * a * math.sin(u * math.pi), 1.6))
    # headphones lying in front (bottom left)
    c.save()
    c.translate(-26, 34)
    c.rotate(-12)
    band = skia.Path()
    band.addArc(skia.Rect(-20, -20, 20, 20), 190, 160)
    c.drawPath(band, _hp(_HOLO, 0.95 * a, 3))
    for x in (-20, 20):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 5, -4, x + 5, 12), 4, 4), _hp(_HOLO_DARK, 0.6 * a, add=False))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 5, -4, x + 5, 12), 4, 4), _hp(_HOLO, 0.95 * a))
    c.restore()


def _icon_theremin(c, t, a):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-38, 20, 30, 40), 4, 4), _hp(_HOLO_MID, 0.35 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-38, 20, 30, 40), 4, 4), _hp(_HOLO, 0.95 * a, 2.2))
    c.drawLine(26, 20, 26, -46, _hp(_HOLO, 0.95 * a, 2.4))                    # pitch antenna
    c.drawCircle(26, -48, 2.5, _hp(_HOLO, a))
    loop = skia.Path()
    loop.addArc(skia.Rect(-56, 2, -34, 24), 90, 270)
    c.drawPath(loop, _hp(_HOLO, 0.9 * a, 2.2))                                 # volume loop
    for k in (0, 1):
        c.drawLine(-12 + k * 12, 40, -12 + k * 12, 50, _hp(_HOLO, 0.6 * a, 2))
    pts = [(-44 + k * 4, -14 + 9 * math.sin(k * 0.55 - t * 9) * (0.6 + 0.4 * math.sin(t * 2.3))) for k in range(17)]
    c.drawPath(_sp(pts, closed=False), _hp(_HOLO, 0.4 * a, 6, blur=3))
    c.drawPath(_sp(pts, closed=False), _hp(_HOLO, 0.95 * a, 2))


def _icon_lullaby(c, t, a):
    rock = 8 * math.sin(t * 1.2)
    c.save()
    c.rotate(rock, -6, 0)
    moon = skia.Path()
    moon.addCircle(-6, 0, 30)
    cut = skia.Path()
    cut.addCircle(8, -10, 26)
    moon = skia.Op(moon, cut, skia.PathOp.kDifference_PathOp)
    c.drawPath(moon, _hp(_HOLO, 0.35 * a, 8, blur=4))
    c.drawPath(moon, _hp(_HOLO_MID, 0.4 * a))
    c.drawPath(moon, _hp(_HOLO, 0.95 * a, 2.2))
    c.restore()
    tw = 0.5 + 0.5 * math.sin(t * 2.6)
    sx, sy = 30, -26
    c.save()
    c.translate(sx, sy)
    c.rotate(t * 20)
    st = _star_path(11 + 2.5 * tw, 4.2, 5)
    c.drawPath(st, _hp("#FFE6A8", (0.6 + 0.4 * tw) * a))
    c.restore()
    _blob(c, sx, sy, 22, "#FFE6A8", 0.35 * a * (0.5 + 0.5 * tw), kind="soft")
    for k, (x, y) in enumerate(((22, 18), (38, 4), (-40, -32))):
        on = 0.5 + 0.5 * math.sin(t * 3 + k * 2)
        c.drawCircle(x, y, 1.6 + on, _hp(_HOLO, 0.4 + 0.5 * on))


_ICONS = {"symphony": _icon_symphony, "kazoo": _icon_kazoo, "arcade": _icon_arcade, "lofi": _icon_lofi,
          "theremin": _icon_theremin, "lullaby": _icon_lullaby}


def _card_glow(c, b, a):
    w2, h2 = CARD_W / 2, CARD_H / 2
    rr = skia.RRect.MakeRectXY(skia.Rect(-w2, -h2, w2, h2), 14, 14)
    ga = a * (0.45 + 0.55 * b)
    c.drawRRect(rr, _hp(_HOLO, 0.30 * ga * (0.5 + 0.8 * b), 6 + 6 * b, blur=6 + 4 * b))


def _card_body(c, t, number, title, icon, b, a, seed=0, glow=True):
    """Card at the origin in card units (170 x 230). b = brightness 0..1, a = alpha."""
    w2, h2 = CARD_W / 2, CARD_H / 2
    rr = skia.RRect.MakeRectXY(skia.Rect(-w2, -h2, w2, h2), 14, 14)
    ga = a * (0.45 + 0.55 * b)
    # translucent panel (src-over so it reads on bright and dark backgrounds)
    c.drawRRect(rr, _G(_lin(0, -h2, 0, h2, [_c(_HOLO_DARK, 0.42 * a), _c(_HOLO_DARK, 0.30 * a)])))
    c.drawRRect(rr, _G(_lin(0, -h2, 0, h2, [_c(_HOLO_MID, 0.20 * ga), _c(_HOLO_MID, 0.06 * ga)])))
    # glow + border + corner brackets
    if glow:
        _card_glow(c, b, a)
    c.drawRRect(rr, _hp(_HOLO, 0.75 * ga, 1.5))
    k = 18
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w2 - 7), sy * (h2 - 7)
            c.drawPath(_poly([(x, y - sy * k), (x, y), (x - sx * k, y)], closed=False), _hp(_HOLO, 0.95 * ga, 2.0))
    # moving sheen + a couple of slow scanlines
    c.save()
    c.clipRRect(rr, True)
    ph = ((t * 0.22 + seed * 0.37) % 1.6) - 0.3
    sx0 = -w2 - 120 + ph * (CARD_W + 240)
    c.drawPath(_poly([(sx0, -h2), (sx0 + 40, -h2), (sx0 - 60, h2), (sx0 - 100, h2)]),
               _G(_lin(sx0 - 100, 0, sx0 + 40, 0, [_c(_HOLO, 0), _c(_HOLO, 0.10 * ga), _c(_HOLO, 0)])))
    for j in range(3):
        y = -h2 + ((t * 18 + j * CARD_H / 3 + seed * 29) % CARD_H)
        c.drawRect(skia.Rect(-w2, y, w2, y + 2), _hp(_HOLO, 0.05 * ga))
    c.restore()
    # header
    _tracked(c, f"No. {number}", -w2 + 16, -h2 + 30, 17, _HOLO, 0.95 * ga, weight=300, tracking=1.0, align="left",
             glow=0.6 * b)
    c.drawCircle(w2 - 20, -h2 + 24, 3.2, _hp(_HOLO, ga * (0.6 + 0.4 * math.sin(t * 3 + number))))
    c.drawLine(-w2 + 14, -h2 + 42, w2 - 14, -h2 + 42, _hp(_HOLO, 0.35 * ga, 1))
    # icon
    c.save()
    c.translate(0, -8)
    _ICONS.get(icon, _icon_symphony)(c, t, ga)
    c.restore()
    # title + tiny waveform bar
    c.drawLine(-w2 + 14, h2 - 58, w2 - 14, h2 - 58, _hp(_HOLO, 0.35 * ga, 1))
    _tracked(c, title.upper(), 0, h2 - 32, 15, _mixrgb(_HOLO, "#FFFFFF", 0.35 * b), 0.95 * ga, weight=400, tracking=2.4,
             glow=0.5 + 0.5 * b, max_w=CARD_W - 26)
    for i in range(14):
        hgt = 2 + 5 * abs(math.sin(t * (2 + 0.3 * i) * (0.4 + b) + i * 1.3))
        x = -w2 + 30 + i * (CARD_W - 60) / 13
        c.drawLine(x, h2 - 16 - hgt / 2, x, h2 - 16 + hgt / 2, _hp(_HOLO, 0.45 * ga, 1.6))


def draw_holo_card(canvas, t, cx, cy, scale=1.0, number=1, title="", icon="symphony", state=0.0, alpha=1.0,
                   wobble=0.0, fold=0.0, rot=0.0):
    """Translucent teal hologram card (~170 x 230 at scale 1) centered at (cx, cy).

    number -> "No. N" header; title (caps; default from CARD_TITLES); icon in
    {'symphony','kazoo','arcade','lofi','theremin','lullaby'}. state 0 idle/dim .. 1 selected (brighter, glow,
    +6 % scale). wobble 0..1: sine-wave ripple through the card (theremin gag). fold 0..1: folds into a
    glowing line and vanishes. rot: degrees."""
    if alpha <= 0.003 or scale <= 0.001 or fold >= 1.0:
        return
    title = title or CARD_TITLES.get(number, "")
    st = clamp(state)
    sc = scale * (1 + 0.06 * ease_in_out(st))
    # fold: squash to a line (0..0.62), then shrink the line to a point (0.62..1)
    f1 = ease_in_out(clamp(fold / 0.62))
    f2 = ease_in_out(clamp((fold - 0.62) / 0.38))
    sy = 1.0 - 0.985 * f1
    sx = 1.0 - f2
    a = alpha * (1 - 0.15 * f1) * (1 - f2 * 0.6)
    canvas.save()
    canvas.translate(cx, cy)
    if rot:
        canvas.rotate(rot)
    canvas.scale(sc, sc)
    if fold > 0:
        # energy concentrating into the fold line
        _blob(canvas, 0, 0, CARD_W * 0.62 * max(sx, 0.05), _HOLO, 0.55 * f1 * (1 - f2 * 0.5) * alpha, kind="soft",
              ry=26 + 20 * f2)
    if sx <= 0.01:
        canvas.restore()
        return
    canvas.scale(sx, 1.0)
    if wobble <= 0.001:
        canvas.save()
        canvas.scale(1.0, sy)
        _card_body(canvas, t, number, title, icon, st, a, seed=number)
        if f1 > 0:
            _fold_bands(canvas, f1, a)
        canvas.restore()
    else:
        # record once, replay in horizontal slices displaced by a travelling sine wave
        rec = skia.PictureRecorder()
        pc = rec.beginRecording(skia.Rect(-CARD_W, -CARD_H, CARD_W, CARD_H))
        _card_body(pc, t, number, title, icon, st, a, seed=number, glow=False)
        if f1 > 0:
            _fold_bands(pc, f1, a)
        pic = rec.finishRecordingAsPicture()
        wb = clamp(wobble)
        canvas.save()
        canvas.scale(1.0 + 0.06 * wb * math.sin(t * 7), sy)
        _card_glow(canvas, st, a * (1 - 0.4 * wb))
        canvas.restore()
        dev_h = CARD_H * sy * _mscale(canvas)
        n = int(clamp(dev_h / 4.5, 14, 72))
        top, bot = -CARD_H / 2 - 4, CARD_H / 2 + 4
        hgt = (bot - top) / n
        amp = 22 * wb
        for i in range(n):
            y0 = top + i * hgt
            yc = y0 + hgt / 2
            dx = amp * math.sin(yc / CARD_H * TAU * 1.3 - t * 11.0) + 0.35 * amp * math.sin(yc * 0.05 + t * 5)
            canvas.save()
            canvas.scale(1.0, sy)
            canvas.clipRect(skia.Rect(-CARD_W, y0, CARD_W, y0 + hgt + 0.6))
            canvas.translate(dx, 0)
            canvas.drawPicture(pic)
            canvas.restore()
    canvas.restore()


def _fold_bands(c, f1, a):
    """Accordion shading while the card folds (alternating dark / bright bands + a hot center line)."""
    w2, h2 = CARD_W / 2, CARD_H / 2
    nb = 8
    for i in range(nb):
        y0 = -h2 + i * CARD_H / nb
        if i % 2:
            c.drawRect(skia.Rect(-w2, y0, w2, y0 + CARD_H / nb), _P("#000000", 0.35 * f1 * a))
        else:
            c.drawRect(skia.Rect(-w2, y0, w2, y0 + CARD_H / nb), _hp(_HOLO, 0.10 * f1 * a))
    c.drawRect(skia.Rect(-w2, -h2, w2, h2), _hp(_HOLO, 0.45 * f1 * f1 * a))


# ---------------------------------------------------------------- card fan
def card_fan_layout(cx, cy, progress, numbers=range(1, 9), radius=300.0, center=(-26.0, 60.0),
                    angles=(-48.0, 12.0), card_scale=0.36):
    """Positions for the fan: list of (number, x, y, rot_deg, scale, visibility 0..1).
    The arc's center of curvature is (cx + center[0], cy + center[1]); cards spread from the palm (cx, cy)."""
    nums = list(numbers)
    n = len(nums)
    out = []
    pcx, pcy = cx + center[0], cy + center[1]
    for i, num in enumerate(nums):
        u = i / max(1, n - 1)
        ang = lerp(angles[0], angles[1], u)
        tx = pcx + radius * math.sin(math.radians(ang))
        ty = pcy - radius * math.cos(math.radians(ang))
        lp = clamp((progress - i * 0.045) / 0.62)
        e = ease_out(lp)
        x = lerp(cx, tx, e)
        y = lerp(cy - 10, ty, e) - 26 * math.sin(math.pi * e)          # little arc on the way out
        rot = ang * 0.55 * e
        scl = card_scale * lerp(0.18, 1.0, e)
        out.append((num, x, y, rot, scl, smoothstep(lp * 2.5)))
    return out


def draw_card_fan(canvas, t, cx, cy, progress, alpha=1.0, numbers=range(1, 9), titles=None, icons=None,
                  wobble_set=(), fold_set=(), fold=0.0, wobble=0.0, focus=None, focus_amt=0.0,
                  states=None, focus_pos=None, focus_scale=0.95, radius=300.0, center=(-26.0, 60.0),
                  angles=(-48.0, 12.0), card_scale=0.36, dim=0.38):
    """Eight holo cards fanned in an arc above/left of the palm at (cx, cy).

    progress 0..1: spreading out from the palm.  focus: number of a card pulled to center-front and enlarged
    by focus_amt 0..1 (to focus_scale, at focus_pos; default = in front of the arc's apex) while the others
    dim to `dim`.  wobble_set / fold_set: card numbers that get `wobble` / `fold`.  states: {number: state}
    (e.g. {1: 0.6} for the softly glowing "one you heard").  Geometry kwargs as in card_fan_layout()."""
    if alpha <= 0.003 or progress <= 0:
        return
    titles = titles or CARD_TITLES
    icons = icons or CARD_ICONS
    states = states or {}
    lay = card_fan_layout(cx, cy, progress, numbers, radius, center, angles, card_scale)
    if focus_pos is None:
        apx, apy = cx + center[0], cy + center[1] - radius
        focus_pos = (apx, apy + 70)
    fa = ease_in_out(clamp(focus_amt)) if focus is not None else 0.0
    order = [L for L in lay if L[0] != focus] + [L for L in lay if L[0] == focus]
    for (num, x, y, rot, scl, vis) in order:
        st = states.get(num, 0.0)
        a = alpha * vis
        if focus is not None:
            if num == focus:
                x = lerp(x, focus_pos[0], fa)
                y = lerp(y, focus_pos[1], fa)
                rot = lerp(rot, 0.0, fa)
                scl = lerp(scl, focus_scale, fa)
                st = max(st, fa)
            else:
                a *= lerp(1.0, dim, fa)
                st *= (1 - fa)
        draw_holo_card(canvas, t, x, y, scl, num, titles.get(num, ""), icons.get(num, "symphony"), st, a,
                       wobble=wobble if num in wobble_set else 0.0, fold=fold if num in fold_set else 0.0, rot=rot)


# =========================================================================== music box
def draw_music_box(canvas, t, cx, cy, scale=1.0, alpha=1.0):
    """Small holographic music box (~130 wide at scale 1, (cx, cy) = bottom center) with a turning pinned
    cylinder, a tiny spinning dancer star and notes drifting up."""
    if alpha <= 0.003:
        return
    a = alpha
    c = canvas
    c.save()
    c.translate(cx, cy)
    c.scale(scale, scale)
    bob = 3 * math.sin(t * 1.6)
    c.translate(0, bob)
    _blob(c, 0, -40, 120, _HOLO, 0.22 * a, kind="soft")
    # box: front face, top face (perspective), lid open behind
    front = _poly([(-60, -40), (60, -40), (60, 0), (-60, 0)])
    top = _poly([(-60, -40), (60, -40), (44, -58), (-44, -58)])
    lid = _poly([(-44, -58), (44, -58), (52, -108), (-52, -108)])
    for pth, fa in ((lid, 0.10), (front, 0.22), (top, 0.16)):
        c.drawPath(pth, _hp(_HOLO_MID, fa * a))
        c.drawPath(pth, _hp(_HOLO, 0.85 * a, 1.8))
    c.drawPath(lid, _hp(_HOLO, 0.25 * a, 6, blur=4))
    # lid inner mirror line + front keyhole + feet
    c.drawPath(_poly([(-38, -66), (38, -66), (44, -100), (-44, -100)]), _hp(_HOLO, 0.35 * a, 1))
    c.drawCircle(0, -22, 3.5, _hp(_HOLO, 0.8 * a, 1.5))
    for x in (-50, 50):
        c.drawRect(skia.Rect(x - 6, 0, x + 6, 5), _hp(_HOLO, 0.6 * a))
    # pinned cylinder seen through the top face (pins scroll as it turns)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-34, -54, 34, -44), 5, 5), _hp(_HOLO, 0.7 * a, 1.4))
    for k in range(9):
        x = -30 + ((k * 7.3 + t * 18) % 60)
        y = -49 + 3 * math.sin(k * 2.1)
        c.drawCircle(x, y, 1.3, _hp("#FFFFFF", 0.8 * a))
    for k in range(7):                                   # comb teeth
        x = -24 + k * 8
        c.drawLine(x, -44, x - 2, -40, _hp(_HOLO, 0.6 * a, 1.2))
    # spindle + tiny dancer star (spins: x-scale = cos)
    c.drawLine(0, -58, 0, -78, _hp(_HOLO, 0.8 * a, 1.6))
    spin = math.cos(t * 3.0)
    c.save()
    c.translate(0, -88)
    c.scale(0.25 + 0.75 * abs(spin), 1.0)
    st = _star_path(12, 5, 5, rot=-math.pi / 2)
    c.drawPath(st, _hp("#FFE6A8", 0.95 * a))
    c.restore()
    _blob(c, 0, -88, 26, "#FFE6A8", 0.45 * a, kind="soft")
    # notes floating up
    for k in range(3):
        u = (t * 0.35 + k / 3) % 1.0
        x = -20 + 40 * hash01(int(t * 0.35 + k / 3) * 3 + k, 9) + 10 * math.sin(u * 6 + k)
        y = -100 - u * 70
        na = a * math.sin(u * math.pi)
        c.drawOval(skia.Rect(x - 4, y - 3, x + 4, y + 3), _hp(_HOLO, 0.9 * na))
        c.drawLine(x + 3.5, y, x + 3.5, y - 13, _hp(_HOLO, 0.9 * na, 1.4))
    c.restore()


# =========================================================================== title
def draw_title(canvas, t, text, cy, alpha=1.0, size=44, sub=None, sub_alpha=0.0, color="#EFFFFC", glow_color="teal_glow",
               tracking=None, cx=W / 2, sub_size=None, rise=0.0):
    """SCREEN space title: thin, widely tracked caps (Inter Display ExtraLight) with a soft, slowly breathing
    teal glow. cy = baseline of the main line (auto-shrinks to fit the frame width). sub: optional smaller
    line under it, faded by sub_alpha. rise: px the text sits lower when alpha is 0 (cy + rise*(1-alpha)),
    e.g. rise=8 gives the BIBLE's 'fade + 8 px drift up' on the way in."""
    cy = cy + rise * (1 - clamp(alpha))
    if alpha > 0.003:
        tr = size * 0.24 if tracking is None else tracking
        txt = text.upper()
        # soft glow pass (blurred), slowly breathing
        br = 0.75 + 0.25 * math.sin(t * 0.9)
        _tracked_glow(canvas, txt, cx, cy, size, glow_color, 0.55 * alpha * br, tr, W - 70)
        _tracked(canvas, txt, cx, cy, size, color, alpha, weight=200, tracking=tr, add=False, max_w=W - 70)
    if sub and sub_alpha > 0.003:
        ss = sub_size or max(14.0, size * 0.36)
        _tracked(canvas, sub, cx, cy + size * 0.95 + ss * 0.4, ss, glow_color, 0.5 * sub_alpha, weight=300,
                 tracking=ss * 0.12, add=True, glow=1.2, max_w=W - 80)
        _tracked(canvas, sub, cx, cy + size * 0.95 + ss * 0.4, ss, color, 0.9 * sub_alpha, weight=300,
                 tracking=ss * 0.12, add=False, max_w=W - 80)


def _tracked_glow(c, text, x, y, size, color, a, tracking, max_w):
    from anim.core import font
    f = font(size, "Inter Display", 300)
    widths = [f.measureText(ch) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if total > max_w:
        k = max_w / total
        f = font(size * k, "Inter Display", 300)
        widths = [w_ * k for w_ in widths]
        tracking *= k
        total = max_w
    p = _hp(color, a, blur=size * 0.28)
    xx = x - total / 2
    for ch, w_ in zip(text, widths):
        c.drawString(ch, xx, y, f, p)
        xx += w_ + tracking
