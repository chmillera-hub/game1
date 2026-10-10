"""Sets for "ANGER" (BIBLE sections 3, 4, 7): the tunnel, the cavern, the shaft (the fall), the depths.

All sets draw in STAGE coordinates (the scene applies its Camera first; stage = 720 x 1280, sets
extend far beyond it for pans; built to hold up from zoom ~0.45 wide shots to zoom 3 close-ups).
They are drawn LIT (readable full colour); light.apply_darkness turns them into a dark cave.
Characters stand with their feet at the exported FLOOR_Y values.

Public API ----------------------------------------------------------------------------------------

TUNNEL (S1) -- side view of a rough passage running left -> right; the DOOR ends it on the right.
    draw_tunnel(canvas, t, scroll=0.0, vines_cut=0.0, webs_torn=0.0, door="closed", door_t=0.0,
                part="all", cut_times=None, tear_times=None, tear_dir=-1.0)
        scroll    parallax of the far wall: pass the camera's x offset (cam.cx - 360) for natural
                  depth (the far wall then slides at 1-BACK_PARALLAX of the camera speed).
        vines_cut 0..1: the vine curtain at VINES_X is cut in 3 groups (one per chop). Group k is cut
                  once vines_cut >= k/3 and its pieces have been falling for
                  (vines_cut - k/3) * VINE_CUT_SPAN seconds -> ramp vines_cut linearly from 0 at chop1
                  to 1 at chop1 + VINE_CUT_SPAN (3.6 s, = 3 chops 1.2 s apart).
                  Or pass cut_times=(t_chop1, t_chop2, t_chop3) (absolute) to drive it by real time.
        webs_torn 0..1: web A (lower) tears over 0..0.5, web B (upper) over 0.5..1
                  (or tear_times=(t_swipe1, t_swipe2) -> each tears over WEB_TEAR_DUR seconds).
                  tear_dir = direction of the gauntlet swipe (-1 = toward screen-left).
        door      "closed" | "rattle" (door_t = seconds since that pull started: shaking, ring swinging,
                  dust sifting) | "burst" (door_t = seconds since the burst: planks and splinters fly,
                  dust, then a broken frame with darkness beyond; door_t < 0 = still closed).
        part      "all" | "back" (everything behind characters) | "front" (things that fly toward the
                  camera: burst splinters, dust; foreground rocks) -> back, characters, front.
    door_lights(door, door_t) -> [light.Light]   flash for the burst (add to apply_darkness lights)
    Constants: FLOOR_Y, FLOOR_BACK_Y, CEIL_Y, VINES_X, VINES_SPAN, VINE_CHOP_Y (chop height),
               WEBS_X, WEB_A, WEB_B (centres), DOOR_X, DOOR_W, DOOR_TOP, DOOR_BOTTOM,
               DOOR_RING_POS, DOOR_IMPACT (shoulder hit point), TUNNEL_X (walkable x range),
               BACK_PARALLAX, VINE_CUT_SPAN, WEB_TEAR_DUR

CAVERN (S2) -- vast; depth by perspective (horizon y ~ CAV_HORIZON_Y), Anger walks the near floor.
    draw_cavern(canvas, t, stone_tilt=0.0, pool_splash_t=None, torch_pos=None, drips=True,
                torch_float=True)
        stone_tilt   0..1 (beyond is fine for wobble): the stone at SHIFT_STONE_POS tips up to 24 deg
                     (pivot on its right foot, left end rising).
        pool_splash_t seconds since the torch hit the water at TORCH_SPLASH_POS (None = never):
                     splash, ripples across the pool (clipped to it), steam, then the dead torch
                     floating and bobbing.
        torch_pos    optional (x, y) of the lit flame -> a warm reflection streak on the pool.
    cavern_lights(t, strength=1.0) -> [Light]     dim teal fungus lights (for apply_darkness)
    path_point(u) -> (x, y, scale)                 walkable path, u 0 (entry) .. 1 (far archway);
                                                   scale = perspective size factor for Anger.
    depth_scale(y) -> float                        perspective size factor at floor y.
    Constants: FLOOR_Y (=1150, same as the tunnel), CAV_HORIZON_Y, WALK_PATH (points), ENTRY_POS,
               ENTRY_ARCH, FAR_ARCH_POS, POOL_POS, POOL_R (rx, ry), TORCH_SPLASH_POS,
               SHIFT_STONE_POS, CREVICE_POS (eyes centre), CREVICE_SCALE, CAV_FUNGI

SHAFT (S3) -- face-on view of the shaft's back wall; the cavern floor's broken lip at the top.
    draw_shaft(canvas, t, scroll=0.0, gouge=None, crack=0.0, collapse_t=None, blur=0.0,
               bottom=None, dust=1.0)
        scroll   stage units the wall has moved UP (falling = increasing scroll). Everything (lip,
                 wall, gouge) is drawn at y - scroll; the wall texture repeats every SHAFT_PERIOD.
        gouge    (x, y0, y1) in WALL coordinates (= stage coords at scroll 0): the long cut the
                 sword carves from y0 down to y1 (the end y1 is fresh and glowing hot).
                 shaft_wall_y(stage_y, scroll) converts a stage point into wall coordinates.
        crack    0..1 cracks spreading in the floor before the collapse (scroll 0 framing).
        collapse_t seconds since the floor gave way (None = intact floor slab over the hole):
                 slabs drop into the hole with grit, the hole opens.
        blur     vertical motion smear in stage units (pass ~fall speed / 24 * 0.6).
        bottom   wall-y of the shaft bottom (the rubble floor of the depths) or None (bottomless).
    shaft_wall_y(y, scroll) -> wall y ; shaft_lights(t) -> [Light]
    Constants: LEDGE_POS (hand grip on the lip), LEDGE_Y, SHAFT_FLOOR_Y (standing on the floor before
               the collapse), HOLE_X (x0, x1), SHAFT_X (wall x range), SHAFT_PERIOD, GOUGE_X (x)

DEPTHS (S4-S6) -- the bottom grotto: rubble, a wall at screen-right to lean on, voice in the dark left.
    draw_depths(canvas, t, dust=0.0, shake=0.0)
        dust 0..1 dust hanging in the air (after the impact / stomps); shake = extra grit falling.
    depths_lights(t, strength=1.0) -> [Light]       dim fungus lights
    Constants: FLOOR_Y, WALL_X (face of the wall Anger leans on), WALL_LEAN_Y (shoulder height when
               propped), DARK_X (x left of which it is deep shadow / the voice), SHAFT_OPEN_X,
               DEP_FUNGI

Generic helpers
    draw_fungi_glow(canvas, t, which="cavern"|"depths", alpha=1.0)   EMISSIVE fungus specks: draw
        after apply_darkness so the caps visibly glow (cheap).

Implementation notes ------------------------------------------------------------------------------
* The static part of every set is recorded ONCE as a vector skia Picture (with an R-tree) and
  rasterised on demand into camera-sized tiles at a zoom-bucketed resolution (LRU cache bounded by
  pixels, as in the previous film) -> a frame costs one or two image blits + the small dynamic bits
  (vines, webs, door, stone, water, gouge).  Periodic layers (tunnel far wall, shaft wall) wrap.
* No noise/grain: rock is cel-shaded plates (light top lip, dark bottom lip) + smooth gradients.
"""
from __future__ import annotations

import math
from collections import OrderedDict
from functools import lru_cache

import numpy as np
import skia

from anim import fx
from anim.core import clamp, ease_in_out, ease_out, hash01, lerp, noise1, smooth_path, smoothstep
from anim.light import Light, flash_light, fungus_light
from config import H, W

TAU = math.tau
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)

# =========================================================================== palette (lit sets)
K_DEEP = "#1A1720"
K_R1 = "#3A3442"
K_R2 = "#575061"
K_R3 = "#766C7E"
K_R4 = "#968A9C"
K_R5 = "#B8ACBA"
K_WARM = "#7E6450"
K_WARM2 = "#A0805F"
K_SOIL = "#5A4232"
K_SOIL2 = "#7A5A42"
K_MOSS = "#46663A"
K_MOSS2 = "#6E8F4A"
K_INK = "#0C0A10"


# =========================================================================== small helpers
def _rgbt(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _mixc(a, b, t):
    a, b = _rgbt(a), _rgbt(b)
    t = clamp(t)
    return "#%02X%02X%02X" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _c(c, a=1.0):
    if isinstance(c, int):
        return skia.ColorSetA(c, int(255 * clamp(a)))
    r, g, b = _rgbt(c)
    return skia.Color(r, g, b, int(255 * clamp(a)))


def _P(color, a=1.0, blur=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setColor(_c(color, a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def _S(color, w, a=1.0, cap="round", blur=0.0):
    p = _P(color, a, blur)
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


def _lg(x0, y0, x1, y1, colors, pos=None):
    cs = [c if isinstance(c, int) else (_c(*c) if isinstance(c, tuple) else _c(c)) for c in colors]
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], cs, pos)


def _rg(cx, cy, r, colors, pos=None, sx=1.0, sy=1.0):
    cs = [c if isinstance(c, int) else (_c(*c) if isinstance(c, tuple) else _c(c)) for c in colors]
    if sx != 1.0 or sy != 1.0:
        m = skia.Matrix()
        m.setScale(sx, sy, cx, cy)
        return skia.GradientShader.MakeRadial((cx, cy), max(r, 0.01), cs, pos, skia.TileMode.kClamp, 0, m)
    return skia.GradientShader.MakeRadial((cx, cy), max(r, 0.01), cs, pos)


def _poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def _nz(x, seed, octs=((1 / 420.0, 1.0), (1 / 140.0, 0.45), (1 / 48.0, 0.18))):
    return sum(noise1(x * f, seed + 13 * i) * a for i, (f, a) in enumerate(octs))


def _mscale(canvas) -> float:
    m = canvas.getTotalMatrix()
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0


def _clip(c, path):
    c.clipPath(path, skia.ClipOp.kIntersect, True)


# =========================================================================== tile cache
class _TileCache:
    """Rasterised tiles of static set Pictures keyed by (name, res bucket); each tile covers the
    view plus a margin.  LRU bounded by total pixels."""

    def __init__(self, budget_px=40_000_000):
        self.entries = OrderedDict()
        self.budget = budget_px
        self.pixels = 0
        self.misses = 0

    def get(self, name, res, vis, bounds, pic_fn, opaque, margin=(0.45, 0.35), full=(False, False)):
        bx0, by0, bx1, by1 = bounds
        vis = skia.Rect(max(vis.left(), bx0), max(vis.top(), by0), min(vis.right(), bx1), min(vis.bottom(), by1))
        if vis.isEmpty():
            return None, None
        for key in reversed(list(self.entries.keys())):
            if key[0] == name and key[1] == res:
                rect, img = self.entries[key]
                if rect.contains(vis):
                    self.entries.move_to_end(key)
                    return rect, img
        self.misses += 1
        mw = max(vis.width() * margin[0], 120)
        mh = max(vis.height() * margin[1], 120)
        g = 64.0
        x0 = bx0 if full[0] else math.floor(max(vis.left() - mw, bx0) / g) * g
        x1 = bx1 if full[0] else math.ceil(min(vis.right() + mw, bx1) / g) * g
        y0 = by0 if full[1] else math.floor(max(vis.top() - mh, by0) / g) * g
        y1 = by1 if full[1] else math.ceil(min(vis.bottom() + mh, by1) / g) * g
        if x1 <= x0 or y1 <= y0:
            return None, None
        rect = skia.Rect(x0, y0, x1, y1)
        iw, ih = max(1, int(math.ceil((x1 - x0) * res))), max(1, int(math.ceil((y1 - y0) * res)))
        surf = skia.Surface(iw, ih)
        cc = surf.getCanvas()
        cc.clear(skia.ColorBLACK if opaque else skia.ColorTRANSPARENT)
        cc.scale(iw / (x1 - x0), ih / (y1 - y0))
        cc.translate(-x0, -y0)
        cc.drawPicture(pic_fn())
        img = surf.makeImageSnapshot()
        key = (name, res, x0, y0, x1, y1)
        old = self.entries.pop(key, None)
        if old is not None:
            self.pixels -= old[1].width() * old[1].height()
        self.entries[key] = (rect, img)
        self.pixels += iw * ih
        while self.pixels > self.budget and len(self.entries) > 1:
            _, (_, im) = self.entries.popitem(last=False)
            self.pixels -= im.width() * im.height()
        return rect, img


_TILES = _TileCache()


def _res_bucket(z):
    return 2.0 ** (math.ceil(math.log2(max(z, 0.2)) * 4 - 1e-6) / 4.0)


def _blit(canvas, name, pic_fn, bounds, opaque=True, alpha=1.0, full=(False, False)):
    vis = canvas.getLocalClipBounds()
    b = skia.Rect(*bounds)
    if not vis.intersect(b):
        return
    res = _res_bucket(_mscale(canvas))
    rect, img = _TILES.get(name, res, vis, bounds, pic_fn, opaque, full=full)
    if img is None:
        return
    p = skia.Paint()
    if alpha < 1:
        p.setAlphaf(alpha)
    canvas.drawImageRect(img, skia.Rect(0, 0, img.width(), img.height()), rect, _LIN, p,
                         skia.Canvas.kFast_SrcRectConstraint)


def _record(bounds, fn) -> skia.Picture:
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect(*bounds), skia.RTreeFactory()())
    fn(c)
    return rec.finishRecordingAsPicture()


# =========================================================================== rock painting kit
def _plates(c, x0, y0, x1, y1, cell, seed, tone_fn, dark=K_R1, light=K_R4, aspect=1.0, alpha=1.0,
            lip=0.035, jitter=0.45, sides=6):
    """Cel-shaded rock plates over a region (caller clips): each plate is an irregular polygon drawn
    with a light top lip and a dark bottom lip.  tone_fn(x, y) -> 0..1."""
    rng = np.random.default_rng(seed)
    ch = cell * aspect
    ys = np.arange(y0 - ch, y1 + ch, ch * 0.62)
    for j, yy in enumerate(ys):
        off = (j % 2) * 0.5 * cell
        xs = np.arange(x0 - cell + off, x1 + cell, cell * 0.8)
        for xx in xs:
            cx = xx + (rng.random() - 0.5) * cell * jitter
            cy = yy + (rng.random() - 0.5) * ch * jitter
            rx = cell * (0.48 + 0.3 * rng.random())
            ry = ch * (0.42 + 0.25 * rng.random())
            n = sides + int(rng.integers(0, 2))
            a0 = rng.random() * TAU
            pts = []
            for k in range(n):
                a = a0 + TAU * k / n + (rng.random() - 0.5) * 0.5
                r = 0.75 + 0.35 * rng.random()
                pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
            tone = clamp(tone_fn(cx, cy) + (rng.random() - 0.5) * 0.22)
            base = _mixc(dark, light, tone)
            hi = _mixc(base, "#B8AEC0", 0.28)
            lo = _mixc(base, K_INK, 0.55)
            path = _poly(pts)
            d = cell * lip
            c.save()
            c.translate(0, d)
            c.drawPath(path, _P(lo, 0.85 * alpha))
            c.translate(0, -2 * d)
            c.drawPath(path, _P(hi, 0.75 * alpha))
            c.restore()
            c.drawPath(path, _P(base, alpha))


def _lumps(c, x0, y0, x1, y1, cell, seed, tone_fn, dark=K_R1, light=K_R4, aspect=0.8, alpha=1.0, density=1.3,
           sharp=0.22, rim=0.35, crease=0.5, warm=0.0, var=0.26):
    """Natural rock surface (caller clips): overlapping irregular lumps, each shaded top-light ->
    bottom-dark with a faint lit rim on its upper edge and a dark crease under it.  Sizes vary a lot
    and the draw order is random, so nothing reads as tiles.  tone_fn(x, y) -> 0..1."""
    rng = np.random.default_rng(seed)
    area = (x1 - x0) * (y1 - y0)
    n = int(area / (cell * cell * aspect) * density) + 1
    xs = x0 + rng.random(n) * (x1 - x0)
    ys = y0 + rng.random(n) * (y1 - y0)
    sz = 0.35 + 0.85 * rng.random(n) ** 1.6
    order = np.argsort(-sz + rng.random(n) * 0.5)          # mostly big first, small on top
    for i in order:
        cx, cy = float(xs[i]), float(ys[i])
        rx = cell * float(sz[i])
        ry = rx * aspect * (0.7 + 0.45 * rng.random())
        m = 6 + int(rng.integers(0, 3))
        a0 = rng.random() * TAU
        pts = []
        for k in range(m):
            a = a0 + TAU * k / m + (rng.random() - 0.5) * 0.55
            r = 0.72 + 0.38 * rng.random()
            pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
        tone = clamp(tone_fn(cx, cy) + (rng.random() - 0.5) * var * 2)
        base = _mixc(dark, light, tone)
        if warm > 0 and rng.random() < warm:
            base = _mixc(base, K_WARM2, 0.35 + 0.3 * rng.random())
        path = smooth_path(pts, closed=True, tension=sharp)
        top = _mixc(base, "#D8CCD8", 0.22)
        bot = _mixc(base, K_INK, 0.42)
        c.drawPath(path, _G(_lg(cx, cy - ry, cx, cy + ry, [top, base, bot], [0.0, 0.45, 1.0]), alpha))
        # rim on the upper arc, crease under the lower arc
        up = sorted(pts, key=lambda p: p[1])
        upper = [p for p in pts if p[1] < cy - ry * 0.1]
        lower = [p for p in pts if p[1] > cy + ry * 0.2]
        if len(upper) >= 2 and rim > 0:
            upper.sort(key=lambda p: p[0])
            c.drawPath(smooth_path(upper, closed=False, tension=sharp), _S(_mixc(base, "#E8DEE8", 0.4), cell * 0.022,
                                                                           rim * alpha))
        if len(lower) >= 2 and crease > 0:
            lower.sort(key=lambda p: p[0])
            c.drawPath(smooth_path(lower, closed=False, tension=sharp), _S(K_INK, cell * 0.03, crease * alpha))
        del up


def _wash_blobs(c, x0, y0, x1, y1, n, seed, colors, size=(300, 900), alpha=(0.08, 0.22), sy=0.6):
    """Painterly large soft colour variations (warm / cool / moss) over a region."""
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = x0 + rng.random() * (x1 - x0)
        y = y0 + rng.random() * (y1 - y0)
        r = size[0] + rng.random() * (size[1] - size[0])
        colr = colors[int(rng.integers(0, len(colors)))]
        a = alpha[0] + rng.random() * (alpha[1] - alpha[0])
        c.drawOval(skia.Rect(x - r, y - r * sy, x + r, y + r * sy),
                   _G(_rg(x, y, r, [_c(colr, a), _c(colr, 0.0)], sx=1.0, sy=sy)))


def _crack_lines(c, x0, y0, x1, y1, n, seed, color=K_INK, alpha=0.55, w=2.2, length=120.0, vertical=0.5):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = x0 + rng.random() * (x1 - x0)
        y = y0 + rng.random() * (y1 - y0)
        pts = [(x, y)]
        ang = (math.pi / 2 if rng.random() < vertical else 0.0) + (rng.random() - 0.5) * 1.2
        L = length * (0.5 + rng.random())
        for k in range(4):
            ang += (rng.random() - 0.5) * 0.9
            x += math.cos(ang) * L / 4
            y += math.sin(ang) * L / 4
            pts.append((x, y))
        c.drawPath(smooth_path(pts, closed=False), _S(color, w * (0.6 + 0.6 * rng.random()), alpha))


def _boulder(c, cx, cy, rx, ry, seed, base=K_R3, light=K_R5, dark=K_R1, shadow=True, moss=0.0, outline=0.8):
    rng = np.random.default_rng(seed)
    n = 9
    pts = []
    for k in range(n):
        a = -math.pi / 2 + TAU * k / n + (rng.random() - 0.5) * 0.35
        r = 0.86 + 0.24 * rng.random()
        px, py = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        if py > cy + ry * 0.5:
            py = cy + ry * 0.5 + (py - cy - ry * 0.5) * 0.3
        pts.append((px, py))
    path = smooth_path(pts, closed=True, tension=0.42)
    if shadow:
        c.drawOval(skia.Rect(cx - rx * 1.25, cy + ry * 0.35, cx + rx * 1.25, cy + ry * 0.85),
                   _P(K_INK, 0.45, blur=ry * 0.12))
    c.drawPath(path, _G(_lg(cx - rx * 0.3, cy - ry, cx + rx * 0.3, cy + ry * 0.6, [_mixc(base, light, 0.35), base, dark],
                            [0, 0.5, 1])))
    c.save()
    _clip(c, path)
    # lit facet (upper-left)
    fp = []
    for k in range(6):
        a = -math.pi * 0.95 + math.pi * 0.95 * k / 5
        r = 0.7 + 0.2 * rng.random()
        fp.append((cx - rx * 0.12 + math.cos(a) * rx * r, cy - ry * 0.05 + math.sin(a) * ry * r * 0.9))
    fp.append((cx + rx * 0.2, cy + ry * 0.05))
    fp.append((cx - rx * 0.5, cy + ry * 0.12))
    c.drawPath(_poly(fp), _P(_mixc(base, light, 0.55), 0.55))
    # shadow side (right)
    c.drawOval(skia.Rect(cx + rx * 0.15, cy - ry * 0.6, cx + rx * 1.6, cy + ry * 1.4), _P(dark, 0.45, blur=rx * 0.15))
    if moss > 0:
        c.drawOval(skia.Rect(cx - rx * 0.8, cy - ry * 1.1, cx + rx * 0.5, cy - ry * 0.45), _P(K_MOSS, 0.7 * moss, blur=2))
        c.drawOval(skia.Rect(cx - rx * 0.6, cy - ry * 1.05, cx + rx * 0.1, cy - ry * 0.7), _P(K_MOSS2, 0.45 * moss, blur=2))
    c.restore()
    if outline > 0:
        c.drawPath(path, _S(K_INK, max(1.2, rx * 0.025), outline))


def _pebbles(c, x0, x1, yfn, n, seed, smin=4, smax=16, yspread=(0, 200)):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = x0 + rng.random() * (x1 - x0)
        dy = yspread[0] + rng.random() * (yspread[1] - yspread[0])
        y = yfn(x) + dy
        s = (smin + (smax - smin) * rng.random() ** 2) * (0.7 + 0.5 * dy / max(1, yspread[1]))
        tone = rng.random()
        base = _mixc(K_R2, K_R4, tone)
        c.drawOval(skia.Rect(x - s * 1.2, y + s * 0.15, x + s * 1.2, y + s * 0.6), _P(K_INK, 0.4))
        c.drawOval(skia.Rect(x - s, y - s * 0.55, x + s, y + s * 0.45), _P(base))
        c.drawOval(skia.Rect(x - s * 0.7, y - s * 0.5, x + s * 0.3, y - s * 0.05), _P(_mixc(base, K_R5, 0.5), 0.7))
        c.drawOval(skia.Rect(x - s, y - s * 0.55, x + s, y + s * 0.45), _S(K_INK, max(0.8, s * 0.09), 0.7))


def _taper_path(pts, w0, w1):
    """Filled tapered ribbon along a polyline (width w0 at start -> w1 at end)."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        p0 = pts[max(0, i - 1)]
        p1 = pts[min(n - 1, i + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        dl = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / dl, dx / dl
        w = lerp(w0, w1, i / max(1, n - 1)) * 0.5
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    return smooth_path(left + right[::-1], closed=True, tension=0.4)


def _root(c, x, y, length, seed, w0=10.0, color=K_SOIL, hi=K_SOIL2, droop=1.0, curl=1.0, alpha=1.0):
    rng = np.random.default_rng(seed)
    pts = [(x, y)]
    ang = math.pi / 2 + (rng.random() - 0.5) * 0.6 * curl
    n = 7
    for k in range(n):
        ang += (rng.random() - 0.5) * 0.5 * curl
        ang = ang * (1 - 0.15 * droop) + (math.pi / 2) * 0.15 * droop
        x += math.cos(ang) * length / n
        y += math.sin(ang) * length / n
        pts.append((x, y))
    path = _taper_path(pts, w0, w0 * 0.12)
    c.drawPath(path, _P(color, alpha))
    c.drawPath(smooth_path([(p[0] - w0 * 0.15, p[1]) for p in pts[:-2]], closed=False), _S(hi, w0 * 0.22, 0.6 * alpha))
    c.drawPath(path, _S(K_INK, max(0.8, w0 * 0.1), 0.6 * alpha))
    # rootlets
    for k in range(2, n, 2):
        if rng.random() < 0.6:
            px, py = pts[k]
            side = 1 if rng.random() < 0.5 else -1
            q = [(px, py), (px + side * length * 0.08, py + length * 0.06), (px + side * length * 0.12, py + length * 0.16)]
            c.drawPath(smooth_path(q, closed=False), _S(color, w0 * 0.25, alpha))
    return pts


def _stalactite(c, x, y, w, h, seed, base=K_R3, light=K_R5, dark=K_R1, wet=True):
    rng = np.random.default_rng(seed)
    bend = (rng.random() - 0.5) * w * 0.4
    pts = [(x - w / 2, y - 4), (x - w * 0.38, y + h * 0.25), (x - w * 0.16 + bend * 0.5, y + h * 0.7),
           (x + bend, y + h), (x + w * 0.12 + bend * 0.5, y + h * 0.68), (x + w * 0.36, y + h * 0.28), (x + w / 2, y - 4)]
    path = smooth_path(pts, closed=True, tension=0.45)
    c.drawPath(path, _G(_lg(x - w / 2, 0, x + w / 2, 0, [_mixc(base, light, 0.45), base, dark], [0, 0.45, 1])))
    # rings / bands
    c.save()
    _clip(c, path)
    for k in range(1, 4):
        yy = y + h * k * 0.22 * (0.8 + 0.4 * rng.random())
        c.drawLine(x - w, yy, x + w, yy + w * 0.12, _S(dark, max(1.0, w * 0.05), 0.35))
    c.drawLine(x - w * 0.22, y + h * 0.05, x - w * 0.05 + bend * 0.6, y + h * 0.8, _S(light, max(1.0, w * 0.07), 0.45))
    c.restore()
    c.drawPath(path, _S(K_INK, max(1.0, w * 0.04), 0.75))
    if wet:
        c.drawCircle(x + bend, y + h + 2, max(1.5, w * 0.05), _P("#9FD0DC", 0.6))


def _stalagmite(c, x, y, w, h, seed, base=K_R3, light=K_R5, dark=K_R1):
    rng = np.random.default_rng(seed)
    bend = (rng.random() - 0.5) * w * 0.4
    pts = [(x - w / 2, y + 6), (x - w * 0.4, y - h * 0.3), (x - w * 0.18 + bend * 0.5, y - h * 0.72), (x + bend, y - h),
           (x + w * 0.16 + bend * 0.5, y - h * 0.7), (x + w * 0.38, y - h * 0.3), (x + w / 2, y + 6)]
    path = smooth_path(pts, closed=True, tension=0.45)
    c.drawOval(skia.Rect(x - w * 0.8, y - w * 0.08, x + w * 0.8, y + w * 0.16), _P(K_INK, 0.45, blur=w * 0.05))
    c.drawPath(path, _G(_lg(x - w / 2, 0, x + w / 2, 0, [_mixc(base, light, 0.5), base, dark], [0, 0.4, 1])))
    c.save()
    _clip(c, path)
    for k in range(1, 4):
        yy = y - h * k * 0.24 * (0.8 + 0.4 * rng.random())
        c.drawLine(x - w, yy, x + w, yy - w * 0.1, _S(dark, max(1.0, w * 0.05), 0.3))
    c.drawLine(x - w * 0.25, y - h * 0.05, x - w * 0.06 + bend * 0.6, y - h * 0.82, _S(light, max(1.0, w * 0.06), 0.4))
    c.restore()
    c.drawPath(path, _S(K_INK, max(1.0, w * 0.04), 0.75))


def _fungi_patch(c, x, y, r, seed, n=None, scale=1.0, facing=0.0):
    """Cluster of little glowing teal caps (lit look; the emissive specks are separate)."""
    rng = np.random.default_rng(seed)
    n = n or int(5 + r / 6)
    c.drawOval(skia.Rect(x - r * 1.6, y - r * 0.7, x + r * 1.6, y + r * 0.7), _P("#3FA894", 0.16, blur=r * 0.5))
    for k in range(n):
        dx = (rng.random() - 0.5) * 2 * r
        dy = (rng.random() - 0.5) * r * 0.6
        s = scale * (3 + 6 * rng.random() ** 2)
        px, py = x + dx, y + dy
        c.drawLine(px, py, px + facing * s * 0.3, py - s * 1.2, _S("#9ADCCB", s * 0.35, 0.9))
        cap = skia.Rect(px - s + facing * s * 0.3, py - s * 1.7, px + s + facing * s * 0.3, py - s * 0.7)
        c.drawOval(cap, _P("#7FE0C8"))
        c.drawOval(skia.Rect(cap.left() + s * 0.3, cap.top() + s * 0.1, cap.right() - s * 0.6, cap.top() + s * 0.45),
                   _P("#D8FFF6", 0.8))
        c.drawOval(cap, _S("#1F5A50", max(0.6, s * 0.12), 0.8))


def _fungi_glow_specks(c, t, patches, alpha=1.0, seed0=900, scales=None):
    """EMISSIVE glow for fungus patches [(x, y, r), ...] (same random caps as _fungi_patch(seed0 + i))."""
    for i, (x, y, r) in enumerate(patches):
        br = (0.8 + 0.2 * math.sin(t * 0.7 + i * 1.7)) * alpha
        scale = 1.0 if scales is None else scales[i]
        fx._blob(c, x, y - r * 0.2, r * 2.6, "#3FD8B8", 0.22 * br, add=True)
        rng = np.random.default_rng(seed0 + i)
        n = int(5 + r / 6)
        for k in range(n):
            dx = (rng.random() - 0.5) * 2 * r
            dy = (rng.random() - 0.5) * r * 0.6
            s = scale * (3 + 6 * rng.random() ** 2)
            fx._blob(c, x + dx, y + dy - s * 1.2, s * 2.4, "#B8FFF0", 0.5 * br, add=True)


# =========================================================================== TUNNEL constants
FLOOR_Y = 1150.0
FLOOR_BACK_Y = 1050.0
CEIL_Y = -60.0
VINES_X = 1000.0
VINES_SPAN = (VINES_X - 175.0, VINES_X + 175.0)
VINE_CHOP_Y = 300.0
WEBS_X = 2050.0
WEB_A = (WEBS_X - 30.0, 600.0)
WEB_B = (WEBS_X + 250.0, 330.0)
DOOR_X = 3150.0
DOOR_W = 470.0
DOOR_TOP = 110.0
DOOR_BOTTOM = 1062.0
DOOR_SPRING_Y = DOOR_TOP + DOOR_W / 2
DOOR_RING_POS = (DOOR_X + 105.0, 700.0)
DOOR_IMPACT = (DOOR_X - 40.0, 640.0)
TUNNEL_X = (-3000.0, DOOR_X - 120.0)
BACK_PARALLAX = 0.35
BACK_PERIOD = 2400.0
VINE_CUT_SPAN = 3.6
WEB_TEAR_DUR = 0.9
_END_X = 2700.0                      # where the end rock face starts
_T_BOUNDS = (-3900.0, -1500.0, 4700.0, 2300.0)
_TB_BOUNDS = (-2600.0, -1000.0, BACK_PERIOD + 3800.0, 1250.0)


def _ceil_y(x):
    return CEIL_Y + 70 * _nz(x, 3) + 30 * noise1(x / 60.0, 8)


def _floor_back_y(x):
    return FLOOR_BACK_Y + 16 * _nz(x, 5)


# --------------------------------------------------------------------------- tunnel: far wall (periodic)
def _recess(c, ax, ay, aw, ah, seed, deep="#07060A", edge="#2E2936"):
    """Irregular dark recess / crack-cave in a wall, fading to black inside."""
    rng = np.random.default_rng(seed)
    n = 11
    pts = []
    for k in range(n):
        a = TAU * k / n
        r = 0.7 + 0.35 * rng.random()
        pts.append((ax + math.cos(a) * aw * 0.5 * r, ay + math.sin(a) * ah * 0.5 * r * (1.15 if math.sin(a) < 0 else 0.9)))
    path = smooth_path(pts, closed=True, tension=0.3)
    c.drawPath(path, _S("#8A7F90", aw * 0.05, 0.25))
    c.drawPath(path, _G(_rg(ax, ay + ah * 0.08, max(aw, ah) * 0.55, [deep, deep, edge], [0, 0.55, 1],
                            sx=aw / max(aw, ah), sy=ah / max(aw, ah))))
    upper = sorted([p for p in pts if p[1] < ay], key=lambda p: p[0])
    if len(upper) > 1:
        c.drawPath(smooth_path(upper, closed=False, tension=0.3), _S(K_INK, aw * 0.04, 0.7))


def _paint_tunnel_back(c):
    P = BACK_PERIOD
    x0, y0, x1, y1 = _TB_BOUNDS
    c.drawRect(skia.Rect(x0, y0, x1, y1), _P("#2E2936"))

    def one(c):
        c.drawRect(skia.Rect(0, -1000, P, 1250), _G(_lg(0, -1000, 0, 1250, ["#2A2532", "#433C4C", "#4A4352", "#2E2936"],
                                                       [0, 0.4, 0.75, 1])))
        c.save()
        c.clipRect(skia.Rect(0, -1000, P, 1250))
        _wash_blobs(c, 0, -800, P, 1100, 10, 91, ["#7A6250", "#55607A", "#4E6A44"], size=(250, 700), alpha=(0.10, 0.25))

        def tone(x, y):
            return 0.42 + 0.22 * noise1(x / 500.0 + y / 900.0, 21) + 0.12 * noise1(y / 300.0, 22)
        _lumps(c, -150, -950, P + 150, 1200, 300, 101, tone, dark="#2E2936", light="#625A6C", aspect=0.6, alpha=0.6,
               rim=0.18, crease=0.3, warm=0.06, density=0.9, var=0.12)
        rng = np.random.default_rng(7)
        for k in range(7):
            yy = -700 + k * 270 + rng.random() * 60
            pts = [(x, yy + 26 * math.sin(x / 300.0 + k) + 14 * noise1(x / 90.0, k)) for x in np.linspace(-50, P + 50, 40)]
            c.drawPath(smooth_path(pts, closed=False), _S("#1A1720", 4 + 4 * rng.random(), 0.35))
        for (ax, ay, aw, ah, sd) in ((420, 600, 230, 380, 1), (1380, 330, 150, 460, 2), (1990, 700, 300, 240, 3)):
            _recess(c, ax, ay, aw, ah, 40 + sd)
        for k in range(10):
            rx = 100 + k * 230 + rng.random() * 80
            _root(c, rx, -320 + rng.random() * 200, 160 + rng.random() * 240, 300 + k, w0=6, color="#4A3828",
                  hi="#6A5038", alpha=0.75)
        c.restore()

    for k in (-1, 0, 1, 2):
        c.save()
        c.translate(k * P, 0)
        one(c)
        c.restore()
    # aerial depth: a cool dark veil (the far wall reads behind the main layer)
    c.drawRect(skia.Rect(x0, y0, x1, y1), _P("#12121C", 0.42))


@lru_cache(maxsize=1)
def _tunnel_back_pic():
    return _record(_TB_BOUNDS, _paint_tunnel_back)


# --------------------------------------------------------------------------- tunnel: main layer
def _arch_outline(cx, top, w, bottom):
    """Door-shaped path: rectangle with a semicircular top (spring line at top + w/2)."""
    p = skia.Path()
    r = w / 2
    p.moveTo(cx - r, bottom)
    p.lineTo(cx - r, top + r)
    p.arcTo(skia.Rect(cx - r, top, cx + r, top + w), 180, 180, False)
    p.lineTo(cx + r, bottom)
    p.close()
    return p


def _paint_stone_arch(c, cx, top, w, bottom, seed, frame=88.0, broken=False):
    """Carved stone arch: jamb blocks + voussoirs + keystone with a carved mark."""
    rng = np.random.default_rng(seed)
    r_in = w / 2
    r_out = r_in + frame
    cyc = top + r_in
    # recess shadow inside the opening edge
    c.drawPath(_arch_outline(cx, top - frame, w + 2 * frame, bottom + 8), _P(K_INK, 0.6, blur=10))
    # voussoirs
    nv = 11
    for k in range(nv):
        a0 = math.pi + math.pi * k / nv
        a1 = math.pi + math.pi * (k + 1) / nv
        gap = 0.012
        pts = []
        for a in np.linspace(a0 + gap, a1 - gap, 5):
            pts.append((cx + math.cos(a) * r_out, cyc + math.sin(a) * r_out))
        for a in np.linspace(a1 - gap, a0 + gap, 5):
            pts.append((cx + math.cos(a) * r_in, cyc + math.sin(a) * r_in))
        tone = 0.45 + 0.3 * rng.random()
        base = _mixc(K_R2, "#857A86", tone)
        if k == nv // 2:
            base = _mixc(base, "#9A8E98", 0.3)
        path = _poly(pts)
        am = (a0 + a1) / 2
        c.drawPath(path, _G(_lg(cx + math.cos(am) * r_out, cyc + math.sin(am) * r_out, cx + math.cos(am) * r_in,
                                cyc + math.sin(am) * r_in, [_mixc(base, "#B0A6B4", 0.25), base, _mixc(base, K_INK, 0.35)],
                                [0, 0.55, 1])))
        c.drawPath(path, _S(K_INK, 3.0, 0.85))
        if k == nv // 2:   # keystone mark: an original carved sigil (circle + three rising strokes)
            kx, ky = cx, cyc - (r_in + r_out) / 2
            c.drawCircle(kx, ky + 6, 16, _S("#1A1620", 4.5, 0.85))
            for d in (-12, 0, 12):
                c.drawLine(kx + d, ky + 4, kx + d * 1.4, ky - 26 + abs(d) * 0.6, _S("#1A1620", 4, 0.85))
            c.drawCircle(kx, ky + 6, 16, _S("#A89EAC", 1.5, 0.35))
    # jambs (stacked blocks)
    for side in (-1, 1):
        xin = cx + side * r_in
        xout = cx + side * r_out
        yb = cyc
        hgt = bottom - cyc
        nb = 5
        ys = [cyc + hgt * k / nb + (rng.random() - 0.5) * 18 * (0 < k < nb) for k in range(nb + 1)]
        for k in range(nb):
            ya, yb2 = ys[k] + 3, ys[k + 1] - 3
            ext = side * (10 + 22 * rng.random())
            pts = [(xin, ya), (xout + ext, ya), (xout + ext * 1.05, yb2), (xin, yb2)]
            tone = 0.42 + 0.3 * rng.random()
            base = _mixc(K_R2, "#857A86", tone)
            path = _poly(pts)
            c.drawPath(path, _G(_lg(xout, 0, xin, 0, [_mixc(base, "#B0A6B4", 0.2), base, _mixc(base, K_INK, 0.3)],
                                    [0, 0.6, 1])))
            c.drawLine(min(xin, xout + ext), ya + 3, max(xin, xout + ext), ya + 3, _S("#A89EAC", 2.0, 0.35))
            c.drawPath(path, _S(K_INK, 3.0, 0.85))
        # inner reveal (depth of the opening, seen on the left side since we look from the left)
        if side < 0:
            rv = _poly([(xin, cyc), (xin + 34, cyc + 18), (xin + 34, bottom), (xin, bottom)])
            c.drawPath(rv, _P("#1D1A22"))
    # chips / moss / cracks on the frame
    c.save()
    outer = _arch_outline(cx, top - frame, w + 2 * frame, bottom)
    _clip(c, outer)
    _crack_lines(c, cx - r_out, top - frame, cx + r_out, bottom, 7, seed + 3, alpha=0.5, length=90)
    for k in range(5):
        a = math.pi + math.pi * rng.random()
        mx, my = cx + math.cos(a) * (r_out - 10), cyc + math.sin(a) * (r_out - 10)
        c.drawOval(skia.Rect(mx - 30, my - 10, mx + 30, my + 12), _P(K_MOSS, 0.6, blur=4))
    c.restore()
    # threshold step
    c.drawPath(_poly([(cx - r_out - 20, bottom - 6), (cx + r_out + 20, bottom - 6), (cx + r_out + 34, bottom + 22),
                      (cx - r_out - 34, bottom + 22)]), _P("#3E3845"))
    c.drawLine(cx - r_out - 20, bottom - 5, cx + r_out + 20, bottom - 5, _S("#7A7080", 2.5, 0.6))
    c.drawPath(_poly([(cx - r_out - 20, bottom - 6), (cx + r_out + 20, bottom - 6), (cx + r_out + 34, bottom + 22),
                      (cx - r_out - 34, bottom + 22)]), _S(K_INK, 2.5, 0.8))


def _paint_tunnel_main(c):
    X0, Y0, X1, Y1 = _T_BOUNDS
    xs = np.arange(X0, X1 + 40, 40.0)
    # ---------------- floor
    fl = [(x, _floor_back_y(x)) for x in xs]
    floor = _poly(fl + [(X1, Y1), (X0, Y1)])
    c.drawPath(floor, _G(_lg(0, FLOOR_BACK_Y - 20, 0, Y1, ["#544C5C", "#6E6476", "#5E5566", "#3E3846", "#24202A"],
                             [0, 0.12, 0.3, 0.62, 1])))
    c.save()
    _clip(c, floor)

    def ftone(x, y):
        return 0.55 + 0.18 * noise1(x / 600.0, 31) - 0.4 * clamp((y - 1150) / 900)
    _wash_blobs(c, X0, FLOOR_BACK_Y, X1, Y1, 40, 92, ["#8A6A50", "#5A6A80", "#56703E"], size=(200, 600),
                alpha=(0.08, 0.2), sy=0.4)
    _lumps(c, X0, FLOOR_BACK_Y - 30, X1, Y1, 300, 202, ftone, dark="#3A3442", light="#8E8494", aspect=0.3,
           alpha=0.55, rim=0.22, crease=0.3, warm=0.06, density=0.8, var=0.12)
    # back-edge contact shadow and light rim
    c.drawPath(smooth_path(fl, closed=False), _S(K_INK, 26, 0.55, blur=10))
    c.restore()
    c.drawPath(smooth_path([(x, y + 3) for x, y in fl], closed=False), _S("#A89CB0", 2.5, 0.35))
    # ---------------- far side of the floor: boulders against the wall
    rng = np.random.default_rng(55)
    for k in range(34):
        x = X0 + rng.random() * (X1 - X0)
        if abs(x - VINES_X) < 120 or _END_X - 120 < x:
            continue
        rx = 40 + 110 * rng.random() ** 2
        _boulder(c, x, _floor_back_y(x) - rx * 0.25, rx, rx * 0.62, 600 + k, base=K_R3, moss=rng.random() * 0.8)
    # ---------------- ribs / pillars (closer than the far wall)
    for k, (px, pw) in enumerate(((-2650, 300), (-1650, 240), (-520, 330), (1560, 250), (2480, 210))):
        top = -1500
        pts_l, pts_r = [], []
        for yy in np.linspace(top, _floor_back_y(px) + 30, 26):
            u = (yy - top) / (FLOOR_BACK_Y + 30 - top)
            waist = 1.0 - 0.18 * math.sin(math.pi * clamp((yy + 100) / 1150))
            wl = pw * 0.5 * waist * (1 + 0.12 * _nz(yy + k * 900, 40 + k))
            wr = pw * 0.5 * waist * (1 + 0.12 * _nz(yy + k * 700, 50 + k))
            flare = 1 + 0.6 * smoothstep((yy - 820) / 260)
            pts_l.append((px - wl * flare, yy))
            pts_r.append((px + wr * flare, yy))
        pp = smooth_path(pts_l + pts_r[::-1], closed=True, tension=0.4)
        c.drawPath(pp, _P(K_INK, 0.5, blur=30))
        c.drawPath(pp, _G(_lg(px - pw * 0.6, 0, px + pw * 0.6, 0, ["#958A9C", "#776D80", "#4E4757", "#2E2A35"],
                              [0, 0.35, 0.75, 1])))
        c.save()
        _clip(c, pp)

        def ptone(x, y, px=px, pw=pw):
            return 0.62 - 0.55 * clamp((x - px + pw * 0.3) / pw)
        _lumps(c, px - pw, top, px + pw, FLOOR_BACK_Y + 40, 150, 900 + k, ptone, dark="#3A3442", light="#A096A8",
               aspect=1.6, alpha=0.5, rim=0.22, crease=0.3, warm=0.05, density=0.8, var=0.1)
        c.drawRect(skia.Rect(px - pw, top, px + pw, FLOOR_BACK_Y + 40),
                   _G(_lg(px - pw * 0.5, 0, px + pw * 0.6, 0, [_c("#000000", 0.0), _c("#000000", 0.0), _c("#120F18", 0.55)],
                          [0, 0.45, 1])))
        _crack_lines(c, px - pw / 2, -200, px + pw / 2, 1000, 5, 950 + k, length=200, vertical=0.9)
        c.drawRect(skia.Rect(px - pw, 760, px + pw, 1100), _G(_lg(0, 760, 0, 1100, [_c(K_MOSS, 0.0), _c(K_MOSS, 0.35)])))
        c.restore()
        c.drawPath(pp, _S(K_INK, 3.5, 0.8))
    # ---------------- end face (the tunnel ends in a rock wall with the door)
    ef = []
    for yy in np.linspace(Y0, _floor_back_y(_END_X) + 4, 30):
        ef.append((_END_X + 60 * _nz(yy, 61) + 40 * smoothstep((yy - 600) / 500), yy))
    end_face = _poly([(ef[0][0], Y0), (X1, Y0), (X1, _floor_back_y(X1) + 4)] + ef[::-1])
    c.drawPath(end_face, _P(K_INK, 0.55, blur=40))
    c.drawPath(end_face, _G(_lg(_END_X, 0, X1, 0, ["#3E3846", "#6E6476", "#625A6A", "#443E4C"], [0, 0.12, 0.5, 1])))
    c.save()
    _clip(c, end_face)

    def etone(x, y):
        return 0.45 + 0.2 * noise1(x / 400 + y / 700, 71) - 0.25 * smoothstep((_END_X + 200 - x) / 200)
    _wash_blobs(c, _END_X, Y0 + 600, X1, FLOOR_BACK_Y, 10, 93, ["#8A6A50", "#56703E"], size=(200, 500), alpha=(0.1, 0.22))
    _lumps(c, _END_X - 200, Y0, X1, FLOOR_BACK_Y + 40, 260, 303, etone, dark="#3A3442", light="#968A9C", aspect=0.65,
           alpha=0.6, rim=0.22, crease=0.32, warm=0.06, density=0.9, var=0.12)
    # side face (the passage wall turning toward us): darker band along the left edge
    side = _poly([(p[0], p[1]) for p in ef] + [(p[0] + 130, p[1]) for p in ef[::-1]])
    c.drawPath(side, _G(_lg(_END_X - 60, 0, _END_X + 160, 0, [_c("#0E0C12", 0.75), _c("#0E0C12", 0.0)])))
    _crack_lines(c, _END_X, -600, X1, 1000, 14, 333, length=160)
    c.restore()
    c.drawPath(smooth_path(ef, closed=False), _S(K_INK, 4, 0.8))
    # the door opening (darkness beyond) + stone arch
    c.drawPath(_arch_outline(DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM),
               _G(_rg(DOOR_X, DOOR_BOTTOM - 300, 600, ["#06070C", "#030305"], [0, 1])))
    _paint_stone_arch(c, DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM, 404)
    # ---------------- ceiling
    cl = [(x, _ceil_y(x)) for x in xs]
    ceil = _poly([(X0, Y0), (X1, Y0)] + cl[::-1])
    c.drawPath(ceil, _G(_lg(0, Y0, 0, CEIL_Y + 120, ["#1E1A24", "#3A3442", "#5E5566"], [0, 0.6, 1])))
    c.save()
    _clip(c, ceil)

    def ctone(x, y):
        return 0.2 + 0.5 * clamp((y + 700) / 800) + 0.15 * noise1(x / 500.0, 81)
    _lumps(c, X0, Y0, X1, CEIL_Y + 150, 280, 404, ctone, dark="#2A2532", light="#8A7F90", aspect=0.55, alpha=0.65,
           rim=0.22, crease=0.35, warm=0.05, density=0.9, var=0.12)
    _wash_blobs(c, X0, -600, X1, CEIL_Y + 100, 30, 94, ["#5A6E44", "#8A6A50"], size=(150, 400), alpha=(0.08, 0.2))
    c.drawPath(smooth_path(cl, closed=False), _S(K_INK, 40, 0.45, blur=16))
    c.restore()
    c.drawPath(smooth_path(cl, closed=False), _S(K_INK, 4, 0.85))
    c.drawPath(smooth_path([(x, y - 6) for x, y in cl], closed=False), _S("#A89CB0", 2.0, 0.3))
    # stalactites & hanging roots along the ceiling
    rng = np.random.default_rng(77)
    for k in range(70):
        x = X0 + rng.random() * (_END_X + 200 - X0)
        if VINES_SPAN[0] - 40 < x < VINES_SPAN[1] + 40:
            continue
        y = _ceil_y(x)
        if rng.random() < 0.45:
            _stalactite(c, x, y, 26 + 50 * rng.random(), 60 + 200 * rng.random() ** 1.5, 1200 + k)
        else:
            for j in range(1 + int(rng.random() * 3)):
                _root(c, x + j * 14, y - 4, 90 + 320 * rng.random() ** 1.3, 1300 + k * 5 + j, w0=5 + 7 * rng.random())
    # vine root mass at VINES_X (the curtain hangs from it)
    for k in range(16):
        x = VINES_SPAN[0] - 40 + k * (VINES_SPAN[1] - VINES_SPAN[0] + 80) / 15
        _root(c, x, _ceil_y(x) - 6, 60 + 90 * rng.random(), 1500 + k, w0=12 + 8 * rng.random(), color="#2F3A22",
              hi="#4E6A34", curl=1.5)
    # web anchor rocks
    _boulder(c, WEBS_X - 330, 1000, 150, 110, 1601, base=K_R3, moss=0.5)
    _boulder(c, WEBS_X + 360, 820, 120, 240, 1602, base=K_R3, shadow=False)
    _stalactite(c, WEBS_X + 120, _ceil_y(WEBS_X + 120), 120, 170, 1603)
    _stalactite(c, WEBS_X - 250, _ceil_y(WEBS_X - 250), 90, 120, 1604)
    # ---------------- loose stones on the floor
    _pebbles(c, X0, X1, _floor_back_y, 150, 1700, smin=4, smax=18, yspread=(20, 260))
    for k in range(10):
        x = X0 + rng.random() * (_END_X - X0)
        if abs(x - VINES_X) < 200 or abs(x - WEBS_X) < 250:
            continue
        _boulder(c, x, FLOOR_Y + 60 + rng.random() * 140, 30 + 40 * rng.random(), 20 + 18 * rng.random(), 1800 + k)
    # ---------------- far left: the passage fades into the dark
    c.drawRect(skia.Rect(X0, Y0, -2300, Y1), _G(_lg(X0, 0, -2300, 0, [_c("#0A090D", 1.0), _c("#0A090D", 0.0)])))


@lru_cache(maxsize=1)
def _tunnel_main_pic():
    return _record(_T_BOUNDS, _paint_tunnel_main)


# --------------------------------------------------------------------------- tunnel: vines
def _vine_strands():
    rng = np.random.default_rng(909)
    out = []
    n = 15
    xs = np.sort(VINES_SPAN[0] + 10 + rng.random(n) * (VINES_SPAN[1] - VINES_SPAN[0] - 20))
    for i in range(n):
        x = float(xs[i])
        top = _ceil_y(x) + 8
        kind = "root" if i % 4 == 1 else "vine"
        L = (720 + rng.random() * 380) if kind == "vine" else (520 + rng.random() * 380)
        grp = [0, 1, 2][(i * 7 + 1) % 3]
        out.append(dict(x=x, top=top, L=L, grp=grp, ph=rng.random() * TAU, w=0.55 + 0.25 * rng.random(),
                        thick=(7 + 7 * rng.random()) if kind == "vine" else (5 + 4 * rng.random()),
                        leaf_seed=int(rng.integers(0, 10000)), dark=rng.random() < 0.4, kind=kind,
                        vx=(rng.random() - 0.5) * 160, amp=12 + 26 * rng.random(), fr=0.6 + 1.2 * rng.random(),
                        leafy=0.6 + 0.8 * rng.random()))
    return out


_VINES = None


def _vines():
    global _VINES
    if _VINES is None:
        _VINES = _vine_strands()
    return _VINES


def _cut_y(grp, x):
    """Height where chop `grp` severs a strand at x (diagonal sword cuts)."""
    base = (VINE_CHOP_Y - 40, VINE_CHOP_Y + 60, VINE_CHOP_Y - 10)[grp]
    slope = (0.45, -0.4, 0.2)[grp]
    return base + slope * (x - VINES_X)


def _draw_vine(c, pts, thick, leaf_seed, dark, alpha=1.0, leaves=True, kind="vine", leafy=1.0):
    if len(pts) < 2:
        return
    if kind == "root":
        col, hi = ("#4A3626", "#6E5038") if dark else ("#5A4230", "#80603F")
        leaves = False
    else:
        col = "#3A5A2C" if dark else "#4E7034"
        hi = "#6E8F4A" if dark else "#8AAE52"
    path = _taper_path(pts, thick, thick * 0.55)
    c.drawPath(path, _P(col, alpha))
    c.drawPath(smooth_path([(p[0] - thick * 0.2, p[1]) for p in pts], closed=False), _S(hi, thick * 0.25, 0.7 * alpha))
    c.drawPath(path, _S(K_INK, 1.4, 0.7 * alpha))
    if not leaves:
        return
    rng = np.random.default_rng(leaf_seed)
    acc = 0.0
    nxt = 30 + rng.random() * 40
    side = 1
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        acc += seg
        while acc > nxt:
            u = 1 - (acc - nxt) / max(seg, 1e-6)
            lx, ly = lerp(x0, x1, u), lerp(y0, y1, u)
            ang = math.atan2(y1 - y0, x1 - x0)
            la = ang + side * (1.0 + 0.4 * rng.random())
            ll = 20 + 22 * rng.random()
            lw = 9 + 8 * rng.random()
            tx, ty = lx + math.cos(la) * ll, ly + math.sin(la) * ll
            nx, ny = -math.sin(la) * lw * 0.5, math.cos(la) * lw * 0.5
            mx, my = (lx + tx) / 2, (ly + ty) / 2
            lp = smooth_path([(lx, ly), (mx + nx, my + ny), (tx, ty), (mx - nx, my - ny)], closed=True, tension=0.5)
            lc = _mixc(col, hi, rng.random() * 0.7)
            c.drawPath(lp, _P(lc, alpha))
            c.drawLine(lx, ly, mx + (tx - lx) * 0.3, my + (ty - ly) * 0.3, _S(_mixc(lc, K_INK, 0.4), 1.0, 0.6 * alpha))
            c.drawPath(lp, _S(K_INK, 1.0, 0.5 * alpha))
            side = -side
            nxt += (34 + rng.random() * 44) / max(0.3, leafy)


def _strand_points(s, t, L0, L1, swing=0.0, n=16):
    """Points of a hanging strand between arc length L0..L1 (from the top), gentle sway + swing angle."""
    pts = []
    for k in range(n + 1):
        d = lerp(L0, L1, k / n)
        u = d / s["L"]
        sway = (math.sin(t * 0.9 * s["w"] + s["ph"]) * 9 + math.sin(t * 2.1 + s["ph"] * 2) * 3) * u ** 1.4
        ax = math.sin(swing) * d
        ay = math.cos(swing) * d
        curve = s["amp"] * math.sin(u * s["fr"] * math.pi + s["ph"]) * min(1.0, u * 3)
        pts.append((s["x"] + sway + ax + curve, s["top"] + ay))
    return pts


def _draw_vines(c, t, vines_cut, cut_times):
    g = 2600.0
    for i, s in enumerate(_vines()):
        k = s["grp"]
        if cut_times is not None:
            age = t - cut_times[k]
        else:
            age = (vines_cut - k / 3.0) * VINE_CUT_SPAN if vines_cut >= k / 3.0 + 1e-6 else -1.0
        if age < 0:
            _draw_vine(c, _strand_points(s, t, 0, s["L"]), s["thick"], s["leaf_seed"], s["dark"], kind=s["kind"],
                       leafy=s["leafy"])
            continue
        yc = _cut_y(k, s["x"])
        Lc = clamp(yc - s["top"], 60, s["L"] - 80)
        # upper stub: springs back and swings
        swing = 0.22 * math.exp(-age * 1.6) * math.sin(age * 6.0 + 0.4) * (1 if i % 2 else -1)
        _draw_vine(c, _strand_points(s, t, 0, Lc, swing), s["thick"], s["leaf_seed"], s["dark"], kind=s["kind"],
                   leafy=s["leafy"])
        # lower piece falls (rigid, slight spin), then lays down / piles on the floor from its bottom end
        pts = _strand_points(s, t if age < 0.05 else t - age + 0.05, Lc, s["L"], 0.0, n=22)
        drop = 0.5 * g * age * age
        vx = s["vx"]
        dirn = 1.0 if vx >= 0 else -1.0
        fy = FLOOR_Y - 20 + ((i * 37) % 90) - 45
        cx = sum(p[0] for p in pts) / len(pts)
        spin = (0.25 if i % 2 else -0.25) * min(age, 0.5)
        fall = []
        for (px, py) in pts:
            dy = py - pts[0][1]
            rx = cx + (px - cx) * math.cos(spin) - dy * math.sin(spin)
            ry = pts[0][1] + (px - cx) * math.sin(spin) + dy * math.cos(spin)
            fall.append((rx + vx * min(age, 0.6), ry + drop))
        # arc length from the bottom end
        dist = [0.0] * len(fall)
        for j in range(len(fall) - 2, -1, -1):
            dist[j] = dist[j + 1] + math.hypot(fall[j + 1][0] - fall[j][0], fall[j + 1][1] - fall[j][1])
        xb = fall[-1][0]
        out = []
        for j, (x, y) in enumerate(fall):
            if y >= fy:
                d = dist[j]
                lx = xb + dirn * (d * 0.38 + 26 * math.sin(d / 55.0 + i))
                ly = fy - 10 * abs(math.sin(d / 70.0 + i * 0.7)) - 6 * math.sin(d / 23.0)
                out.append((lx, ly))
            else:
                out.append((x, y))
        _draw_vine(c, out, s["thick"], s["leaf_seed"] + 7, s["dark"], kind=s["kind"], leafy=s["leafy"])


# --------------------------------------------------------------------------- tunnel: webs
def _web_def(center, R, anchors, seed, rings=8):
    rng = np.random.default_rng(seed)
    cx, cy = center
    # radial ends: anchors plus extra radials ending on the frame threads between anchors
    ends = []
    na = len(anchors)
    for k in range(na):
        a0 = anchors[k]
        a1 = anchors[(k + 1) % na]
        ends.append((a0, k, 1.0))
        for j in (1, 2):
            u = j / 3 + (rng.random() - 0.5) * 0.12
            ends.append(((lerp(a0[0], a1[0], u), lerp(a0[1], a1[1], u)), k, 0.0))
    ends.sort(key=lambda e: math.atan2(e[0][1] - cy, e[0][0] - cx))
    radii = [0.12 + 0.82 * (r / (rings - 1)) ** 1.1 + (rng.random() - 0.5) * 0.03 for r in range(rings)]
    return dict(c=center, R=R, anchors=anchors, ends=ends, radii=radii, seed=seed)


@lru_cache(maxsize=1)
def _webs():
    wa = _web_def(WEB_A, 360, [(WEBS_X - 300, 120), (WEBS_X + 130, 110), (WEBS_X + 300, 700), (WEBS_X + 160, 1010),
                               (WEBS_X - 260, 930), (WEBS_X - 420, 520)], 31)
    wb = _web_def(WEB_B, 260, [(WEBS_X + 70, 40), (WEBS_X + 470, 60), (WEBS_X + 400, 640), (WEBS_X + 180, 600),
                               (WEBS_X + 40, 300)], 37, rings=7)
    return [wa, wb]


def _web_point(wd, ri, ei, p, tear_dir, t):
    """Position of web vertex on radial ei at ring fraction r (ri = None -> the end), tear progress p."""
    cx, cy = wd["c"]
    (ex, ey), ak, _ = wd["ends"][ei]
    r = 1.0 if ri is None else wd["radii"][ri]
    # resting position (slight sag of the rings toward the centre is applied by the caller)
    x, y = lerp(cx, ex, r), lerp(cy, ey, r)
    breath = math.sin(t * 0.8 + ei) * 1.5 * (1 - r)
    y += breath
    if p <= 0:
        return x, y
    # torn: collapse toward the radial's end (its anchor), droop, swipe push, swing
    k = ease_out(clamp(p * 1.4))
    f = k * (0.85 - 0.25 * r)
    x = lerp(x, ex, f)
    y = lerp(y, ey, f)
    y += 150 * k * (1 - r) ** 0.8 * smoothstep(p * 2)
    push = math.sin(math.pi * clamp(p * 1.6)) * 140 * (1 - r)
    x += tear_dir * push
    sw = math.sin(t * 2.4 + ei) * 8 * k * (1 - r)
    return x + sw, y


def _draw_web(c, t, wd, p, tear_dir, alpha=1.0):
    zs = _mscale(c)
    th = min(1.0, (1.0 / max(zs, 0.3)) ** 0.6)          # threads stay fine in close-ups
    ne = len(wd["ends"])
    nr = len(wd["radii"])
    col = "#D9D6CF"
    a_line = 0.62 * alpha * (1 - 0.35 * clamp(p))
    cx, cy = wd["c"]
    # torn side: the split line through the centre, perpendicular to the swipe (vertical-ish)
    split_a = math.radians(80)
    nxs, nys = math.cos(split_a), math.sin(split_a)

    def side(px, py):
        return (px - cx) * nys - (py - cy) * nxs

    pts = [[_web_point(wd, ri, ei, p, tear_dir * (1 if side(*wd["ends"][ei][0]) > 0 else 0.6), t) for ri in range(nr)]
           for ei in range(ne)]
    ends = [_web_point(wd, None, ei, p, tear_dir, t) for ei in range(ne)]
    # frame threads (anchor to anchor) - thick; when torn they snap and dangle from each anchor
    fr = [e[0] for e in wd["ends"]]
    if p <= 0.02:
        c.drawPath(_poly(fr, close=True), _S(col, 3.0 * th, a_line * 0.8))
    else:
        k = ease_out(clamp(p * 1.3))
        for ia in range(len(fr)):
            a_, b_ = fr[ia], fr[(ia + 1) % len(fr)]
            for (p0, p1) in ((a_, b_), (b_, a_)):
                u = lerp(0.5, 0.18, k)
                mx, my = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
                ex, ey = lerp(mx, p0[0], 0.3 * k), my + 120 * k * u
                pth = skia.Path()
                pth.moveTo(*p0)
                pth.quadTo(mx, my + 40 * k, ex + tear_dir * 10 * k, ey)
                c.drawPath(pth, _S(col, 2.4 * th, a_line * 0.75))
    # silk sheets near the centre (thick dusty webs)
    if p < 0.6:
        sheet = []
        for ei in range(ne):
            sheet.append(pts[ei][min(3, nr - 1)])
        c.drawPath(smooth_path(sheet, closed=True), _P(col, 0.12 * alpha * (1 - p / 0.6), blur=6))
    # radials
    for ei in range(ne):
        line = [pts[ei][0]] if p < 0.08 else []
        line += [pts[ei][ri] for ri in range(nr)] + [ends[ei]]
        if p >= 0.08:
            line = line[1:] if len(line) > 2 else line
        c.drawPath(smooth_path(line, closed=False), _S(col, 2.2 * th, a_line))
    # spiral rings (sagging chords between neighbouring radials); torn chords removed
    for ri in range(nr):
        for ei in range(ne):
            ej = (ei + 1) % ne
            a, b = pts[ei][ri], pts[ej][ri]
            if p > 0.05:
                s1, s2 = side(*wd["ends"][ei][0]), side(*wd["ends"][ej][0])
                if s1 * s2 < 0 or ri < 2 or (hash01(ri * 31 + ei, wd["seed"]) < p * 0.5):
                    continue
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            sag = 0.12 + 0.25 * p
            mx = lerp(mx, cx, sag * (1 - p))
            my = lerp(my, cy, sag * (1 - p)) + 10 * p
            pth = skia.Path()
            pth.moveTo(*a)
            pth.quadTo(mx, my, *b)
            c.drawPath(pth, _S(col, 1.5 * th, a_line * 0.85))
    # wrapped husks caught in the web
    rng = np.random.default_rng(wd["seed"] + 5)
    for k in range(3):
        ei = int(rng.integers(0, ne))
        ri = int(rng.integers(2, nr - 1))
        hx, hy = pts[ei][ri]
        c.drawOval(skia.Rect(hx - 6, hy - 9, hx + 6, hy + 9), _P("#BEB8AE", 0.75 * alpha))
        c.drawOval(skia.Rect(hx - 6, hy - 9, hx + 6, hy + 9), _S("#3A3640", 1.0, 0.6 * alpha))
    # loose strands drifting down after the tear
    if 0 < p < 1.0:
        for k in range(6):
            sx = cx + (hash01(k, wd["seed"]) - 0.5) * wd["R"]
            sy = cy + (hash01(k + 9, wd["seed"]) - 0.5) * wd["R"] * 0.6 + p * 260
            ln = 40 + 50 * hash01(k + 3, wd["seed"])
            pth = skia.Path()
            pth.moveTo(sx, sy)
            pth.quadTo(sx + 20 * tear_dir, sy + ln * 0.5, sx + 6, sy + ln)
            c.drawPath(pth, _S(col, 1.3 * th, 0.5 * alpha * (1 - p)))


def _draw_webs(c, t, webs_torn, tear_times, tear_dir):
    for k, wd in enumerate(_webs()):
        if tear_times is not None:
            p = clamp((t - tear_times[k]) / WEB_TEAR_DUR)
        else:
            p = clamp(webs_torn * 2.0 - k)
        _draw_web(c, t, wd, p, tear_dir)


# --------------------------------------------------------------------------- tunnel: door
_N_PLANKS = 5


def _door_path():
    return _arch_outline(DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM)


def _plank_x(i):
    x0 = DOOR_X - DOOR_W / 2
    return x0 + DOOR_W * i / _N_PLANKS, x0 + DOOR_W * (i + 1) / _N_PLANKS


_BANDS_Y = (300.0, 560.0, 900.0)


def _paint_plank(c, i, rng):
    xa, xb = _plank_x(i)
    tone = rng.random()
    base = _mixc("#5A3B22", "#6E4A2C", tone)
    r = skia.Rect(xa + 1.5, DOOR_TOP - 10, xb - 1.5, DOOR_BOTTOM)
    c.drawRect(r, _G(_lg(xa, 0, xb, 0, [_mixc(base, "#8A6040", 0.35), base, _mixc(base, "#2A1A0E", 0.45)], [0, 0.5, 1])))
    # grain
    for k in range(6):
        gx = xa + 8 + (xb - xa - 16) * (k + rng.random() * 0.6) / 6
        pts = [(gx + 5 * math.sin(yy / 90.0 + k * 1.3 + i) + 3 * noise1(yy / 40.0, i * 10 + k), yy)
               for yy in np.linspace(DOOR_TOP, DOOR_BOTTOM, 24)]
        c.drawPath(smooth_path(pts, closed=False), _S("#2E1C10", 1.6 + rng.random(), 0.5))
    # knots
    for k in range(2):
        ky = DOOR_TOP + 200 + rng.random() * 700
        kx = lerp(xa + 20, xb - 20, rng.random())
        c.drawOval(skia.Rect(kx - 9, ky - 14, kx + 9, ky + 14), _P("#2E1C10", 0.8))
        c.drawOval(skia.Rect(kx - 15, ky - 24, kx + 15, ky + 24), _S("#2E1C10", 1.4, 0.45))
    c.drawRect(r, _S("#1A0F08", 3.0, 0.9))


def _paint_door(c, broken_mask=None):
    """Closed door (planks + iron bands + ring + lock plate), clipped to the arch."""
    rng = np.random.default_rng(4242)
    dp = _door_path()
    c.save()
    _clip(c, dp)
    for i in range(_N_PLANKS):
        _paint_plank(c, i, rng)
    # iron bands with rivets
    for by in _BANDS_Y:
        r = skia.Rect(DOOR_X - DOOR_W / 2 - 4, by - 18, DOOR_X + DOOR_W / 2 + 4, by + 18)
        c.drawRect(r, _G(_lg(0, by - 18, 0, by + 18, ["#7A808A", "#4B4F57", "#2A2C32"], [0, 0.45, 1])))
        c.drawRect(r, _S("#121316", 2.5, 0.9))
        for i in range(_N_PLANKS):
            xa, xb = _plank_x(i)
            for rx in (xa + 18, xb - 18):
                c.drawCircle(rx, by, 6, _P("#2A2C32"))
                c.drawCircle(rx - 1.5, by - 1.5, 2.5, _P("#A8AEB8", 0.8))
    # arched iron rim along the top
    rim = skia.Path()
    rim.addArc(skia.Rect(DOOR_X - DOOR_W / 2 + 12, DOOR_TOP + 12, DOOR_X + DOOR_W / 2 - 12, DOOR_TOP + DOOR_W - 12), 180, 180)
    c.drawPath(rim, _S("#3A3D44", 14, 0.9))
    c.drawPath(rim, _S("#7A808A", 3, 0.5))
    c.restore()
    c.drawPath(dp, _S("#120A06", 4, 0.9))
    # lock plate + keyhole
    lx, ly = DOOR_X + 160, 760
    lp = skia.RRect.MakeRectXY(skia.Rect(lx - 28, ly - 46, lx + 28, ly + 46), 8, 8)
    c.drawRRect(lp, _G(_lg(lx - 28, 0, lx + 28, 0, ["#6A707A", "#3E4148", "#24262C"], [0, 0.5, 1])))
    c.drawRRect(lp, _S("#101114", 2.5, 0.9))
    c.drawCircle(lx, ly - 8, 7, _P("#08080A"))
    c.drawPath(_poly([(lx - 4, ly - 6), (lx + 4, ly - 6), (lx + 6, ly + 18), (lx - 6, ly + 18)]), _P("#08080A"))


def _draw_ring(c, swing, alpha=1.0):
    mx, my = DOOR_RING_POS[0], DOOR_RING_POS[1] - 40
    # mount plate
    c.drawCircle(mx, my, 22, _G(_rg(mx - 6, my - 6, 26, ["#8A909A", "#4B4F57", "#24262C"], [0, 0.6, 1]), alpha))
    c.drawCircle(mx, my, 22, _S("#101114", 2.5, 0.9 * alpha))
    c.drawCircle(mx, my, 6, _P("#1A1B1F", alpha))
    c.save()
    c.translate(mx, my)
    c.rotate(math.degrees(swing))
    R = 44
    c.drawCircle(0, R + 6, R, _S("#24262C", 13, alpha))
    c.drawCircle(0, R + 6, R, _S("#6E747E", 5, alpha))
    c.drawArc(skia.Rect(-R, 6, R, 2 * R + 6), 200, 70, False, _S("#B8BEC8", 2.5, 0.8 * alpha))
    c.drawRect(skia.Rect(-8, -4, 8, 14), _P("#3A3D44", alpha))
    c.restore()


@lru_cache(maxsize=1)
def _door_pic():
    return _record((DOOR_X - DOOR_W, DOOR_TOP - 40, DOOR_X + DOOR_W, DOOR_BOTTOM + 40), _paint_door)


@lru_cache(maxsize=1)
def _door_pieces():
    """Burst pieces: (local Picture, centre, polygon) per piece; recorded in door coordinates."""
    rng = np.random.default_rng(777)
    pieces = []
    for i in range(_N_PLANKS):
        xa, xb = _plank_x(i)
        nb = 2 + int(rng.random() * 2)
        cuts = sorted([DOOR_TOP + (DOOR_BOTTOM - DOOR_TOP) * (k + 0.5 + (rng.random() - 0.5) * 0.6) / nb for k in range(nb - 1)])
        ys = [DOOR_TOP - 20] + cuts + [DOOR_BOTTOM]
        for k in range(nb):
            ya, yb = ys[k], ys[k + 1]
            # jagged break edges
            top = [(xa, ya)] if k == 0 else [(lerp(xa, xb, u), ya + (rng.random() - 0.5) * 50) for u in np.linspace(0, 1, 5)]
            bot = [(xb, yb)] if k == nb - 1 else [(lerp(xb, xa, u), yb + (rng.random() - 0.5) * 50) for u in np.linspace(0, 1, 5)]
            if k == 0:
                top = [(xa, ya), (xb, ya)]
            if k == nb - 1:
                bot = [(xb, yb), (xa, yb)]
            poly = top + bot
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            rec = skia.PictureRecorder()
            pc = rec.beginRecording(skia.Rect(xa - cx - 60, ya - cy - 60, xb - cx + 60, yb - cy + 60))
            pc.save()
            pc.translate(-cx, -cy)
            pp = _poly(poly)
            pc.clipPath(pp, skia.ClipOp.kIntersect, True)
            pc.drawPicture(_door_pic())
            pc.restore()
            pc.save()
            pc.translate(-cx, -cy)
            pc.drawPath(pp, _S("#1A0F08", 3.0, 0.9))
            pc.restore()
            pieces.append((rec.finishRecordingAsPicture(), (cx, cy), i, k))
    return pieces


def _draw_door_closed(c, t, door, door_t):
    dx = drot = swing = 0.0
    if door == "rattle" and door_t >= 0:
        env = math.exp(-door_t * 2.6) * smoothstep(door_t / 0.05)
        dx = math.sin(door_t * TAU * 11.0) * 4.5 * env
        drot = math.sin(door_t * TAU * 7.0 + 1.0) * 0.25 * env
        swing = math.sin(door_t * 9.0) * 0.5 * math.exp(-door_t * 1.4)
    else:
        swing = 0.03 * math.sin(t * 0.7)
    c.save()
    c.translate(DOOR_X + dx, DOOR_BOTTOM)
    c.rotate(drot)
    c.translate(-DOOR_X, -DOOR_BOTTOM)
    c.drawPicture(_door_pic())
    _draw_ring(c, swing)
    c.restore()
    if door == "rattle" and 0 <= door_t < 3.0:
        fx.dust_fall(c, t, DOOR_X - DOOR_W / 2 - 40, DOOR_X + DOOR_W / 2 + 40, DOOR_TOP - 70,
                     amount=math.exp(-door_t * 1.2), seed=5, length=420, size=1.4)


def _piece_motion(i, k, cx, cy, age):
    h = lambda q: hash01(i * 17 + k * 5 + q, 991)
    dx, dy = cx - DOOR_IMPACT[0], cy - DOOR_IMPACT[1]
    dl = math.hypot(dx, dy) or 1.0
    ang = math.atan2(dy, dx) + (h(1) - 0.5) * 0.7
    sp = 700 + 900 * h(2)
    vx, vy = math.cos(ang) * sp, math.sin(ang) * sp - 500 * h(3)
    toward = h(4) < 0.45
    g = 2600.0
    x = cx + vx * age
    y = cy + vy * age + 0.5 * g * age * age
    rot = (h(5) - 0.5) * 1400 * age
    sc = (1.0 + 0.9 * age) if toward else 1.0 / (1.0 + 2.2 * age)
    fy = FLOOR_Y + 40 + 160 * h(6) if toward else DOOR_BOTTOM
    landed = False
    if toward and y > fy:
        a_, b_, c_ = 0.5 * g, vy, cy - fy
        disc = b_ * b_ - 4 * a_ * c_
        tl = (-b_ + math.sqrt(max(disc, 0))) / (2 * a_)
        dt = age - tl
        x = cx + vx * tl + vx * 0.12 * (1 - math.exp(-dt / 0.12))
        y = fy
        rot = (h(5) - 0.5) * 1400 * tl
        rot = round(rot / 180.0) * 180.0 + (h(7) - 0.5) * 30 if dt > 0.25 else rot
        sc = 1.0 + 0.9 * min(tl, 0.6)
        landed = True
    return x, y, rot, sc, toward, landed


def _draw_door_burst(c, t, age, part):
    if part in ("all", "back"):
        # dark opening with a faint cold glimmer far beyond
        c.drawPath(_door_path(), _G(_rg(DOOR_X, DOOR_BOTTOM - 260, 520, ["#0B1016", "#040507"], [0, 1])))
        for (fx_, fy_, r) in ((DOOR_X - 120, 860, 10), (DOOR_X + 90, 900, 7), (DOOR_X + 30, 820, 5)):
            c.drawCircle(fx_, fy_, r * 0.5, _P("#4FB8A4", 0.25))
        # hinge-side stubs (jagged remnants on the left jamb and in the arch)
        rng = np.random.default_rng(31)
        xa = DOOR_X - DOOR_W / 2
        for (y0, y1) in ((DOOR_SPRING_Y - 40, DOOR_SPRING_Y + 160), (520, 640), (840, 1000)):
            pts = [(xa, y0), (xa + 30 + rng.random() * 40, y0 + 10)]
            for u in np.linspace(0.2, 0.8, 4):
                pts.append((xa + 20 + rng.random() * 70, lerp(y0, y1, u)))
            pts += [(xa + 26, y1), (xa, y1)]
            c.drawPath(_poly(pts), _P("#4A3020"))
            c.drawPath(_poly(pts), _S("#1A0F08", 2.5, 0.9))
        # bent bands stubs
        for by in _BANDS_Y:
            c.drawRect(skia.Rect(xa - 4, by - 16, xa + 40, by + 16), _P("#3A3D44"))
            c.drawRect(skia.Rect(xa - 4, by - 16, xa + 40, by + 16), _S("#121316", 2, 0.9))
        # receding pieces (flying into the dark beyond): clipped to the opening
        c.save()
        _clip(c, _door_path())
        for (pic, (cx, cy), i, k) in _door_pieces():
            x, y, rot, sc, toward, landed = _piece_motion(i, k, cx, cy, age)
            if toward:
                continue
            fade = clamp(1 - age / 0.7)
            if fade <= 0:
                continue
            c.save()
            c.translate(lerp(DOOR_X, x, 0.6), y)
            c.rotate(rot)
            c.scale(sc, sc)
            p = skia.Paint()
            p.setAlphaf(fade)
            c.saveLayer(None, p)
            c.drawPicture(pic)
            c.restore()
            c.restore()
        c.restore()
        # pieces that already landed on the floor stay behind characters
        for (pic, (cx, cy), i, k) in _door_pieces():
            x, y, rot, sc, toward, landed = _piece_motion(i, k, cx, cy, age)
            if toward and landed:
                _draw_piece_flat(c, pic, x, y, rot, sc)
        fx.debris(c, t, age, (DOOR_X - 20, 640), seed=12, kind="wood", n=14, speed=1100, direction=-90, spread=360,
                  floor_y=FLOOR_Y + 60, size=1.3)
    if part in ("all", "front"):
        for (pic, (cx, cy), i, k) in _door_pieces():
            x, y, rot, sc, toward, landed = _piece_motion(i, k, cx, cy, age)
            if toward and not landed:
                _draw_piece_flat(c, pic, x, y, rot, sc)
        fx.debris(c, t, age, DOOR_IMPACT, seed=13, kind="wood", n=22, speed=1500, direction=-90, spread=360,
                  floor_y=None, size=1.6, toward=1.2, life=1.6)
        fx.debris(c, t, age, (DOOR_X, 300), seed=14, kind="stone", n=8, speed=500, direction=90, spread=120,
                  floor_y=FLOOR_Y + 30, size=1.4)
        fx.dust_cloud(c, t, DOOR_X, DOOR_BOTTOM - 20, age, size=3.0, seed=3, n=20, life=4.5, alpha=1.0)
        fx.dust_cloud(c, t, DOOR_X - 60, 620, age, size=2.4, seed=4, n=14, life=3.2, ground=False, alpha=0.8,
                      drift=(-140.0, -10.0))
        if age < 1.5:
            fx.dust_fall(c, t, DOOR_X - DOOR_W / 2 - 60, DOOR_X + DOOR_W / 2 + 60, DOOR_TOP - 80,
                         amount=1.0 - age / 1.5, seed=9, length=500, size=1.6)


def _draw_piece_flat(c, pic, x, y, rot, sc):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(sc, sc)
    c.drawPicture(pic)
    c.restore()


def door_lights(door, door_t):
    """Lights for the door event (the burst flash) -> list (possibly empty)."""
    if door == "burst":
        L = flash_light(DOOR_X, 640, door_t, strength=1.0, radius=1700)
        return [L] if L else []
    return []


# --------------------------------------------------------------------------- tunnel: front layer
def _draw_tunnel_front_rocks(c, scroll):
    off = -0.25 * scroll
    vis = c.getLocalClipBounds()
    if vis.bottom() < 1380:
        return
    P = 1700.0
    c.save()
    c.translate(off, 0)
    k0 = math.floor((vis.left() - off - 600) / P)
    k1 = math.floor((vis.right() - off + 600) / P)
    for k in range(k0, k1 + 1):
        bx = k * P + 300 * hash01(k, 5)
        w = 360 + 240 * hash01(k, 6)
        hgt = 120 + 140 * hash01(k, 7)
        pts = [(bx - w / 2, 2300), (bx - w * 0.45, 1700 - hgt * 0.4), (bx - w * 0.2, 1660 - hgt),
               (bx + w * 0.15, 1670 - hgt * 0.8), (bx + w * 0.45, 1710 - hgt * 0.3), (bx + w / 2, 2300)]
        pp = smooth_path(pts, closed=True)
        c.drawPath(pp, _G(_lg(0, 1600 - hgt, 0, 1900, ["#2A2630", "#141218"])))
        c.drawPath(smooth_path(pts[1:5], closed=False), _S("#5A5262", 3, 0.5))
    c.restore()


def draw_tunnel(canvas, t, scroll=0.0, vines_cut=0.0, webs_torn=0.0, door="closed", door_t=0.0, part="all",
                cut_times=None, tear_times=None, tear_dir=-1.0):
    """The S1 tunnel (STAGE coords). See module doc."""
    c = canvas
    burst = door == "burst" and door_t is not None and door_t >= 0
    if part in ("all", "back"):
        # far wall (periodic, parallax)
        off = BACK_PARALLAX * scroll
        c.save()
        c.translate(off, 0)
        vis = c.getLocalClipBounds()
        kk = math.floor(vis.left() / BACK_PERIOD)
        c.translate(kk * BACK_PERIOD, 0)
        _blit(c, "tunnel_back", _tunnel_back_pic, _TB_BOUNDS, opaque=True)
        c.restore()
        # main layer
        _blit(c, "tunnel_main", _tunnel_main_pic, _T_BOUNDS, opaque=False)
        vis = c.getLocalClipBounds()
        if vis.right() > VINES_SPAN[0] - 400 and vis.left() < VINES_SPAN[1] + 400:
            _draw_vines(c, t, vines_cut, cut_times)
        if vis.right() > WEBS_X - 600 and vis.left() < WEBS_X + 700:
            _draw_webs(c, t, webs_torn, tear_times, tear_dir)
        if vis.right() > DOOR_X - 1400 and vis.left() < DOOR_X + 1400:
            if burst:
                _draw_door_burst(c, t, door_t, "back")
            else:
                _draw_door_closed(c, t, door, door_t if door_t is not None else 0.0)
    if part in ("all", "front"):
        if burst:
            _draw_door_burst(c, t, door_t, "front")
        _draw_tunnel_front_rocks(c, scroll)


# =========================================================================== CAVERN (S2)
CAV_HORIZON_Y = 560.0
_C_BOUNDS = (-2300.0, -2800.0, 3100.0, 3500.0)
ENTRY_ARCH = (-90.0, 985.0, 0.72)                 # base centre x, base y, scale of the broken entry arch
ENTRY_POS = (-90.0, 992.0)                         # where Anger stands in the doorway
FAR_ARCH_POS = (722.0, 648.0)                      # base centre of the far archway (the other door)
POOL_POS = (430.0, 1015.0)
POOL_R = (250.0, 52.0)
TORCH_SPLASH_POS = (470.0, 1012.0)
SHIFT_STONE_POS = (300.0, 1166.0)                  # stone centre on the floor (Anger steps on it)
CREVICE_POS = (1046.0, 628.0)                      # centre of the 4 eyes inside the crevice
CREVICE_SCALE = 0.4                                # perspective scale at the crevice (crawler size factor)
WALK_PATH = [(-90.0, 992.0), (40.0, 1070.0), (180.0, 1135.0), (300.0, 1166.0), (450.0, 1180.0), (620.0, 1170.0),
             (760.0, 1120.0), (860.0, 1040.0), (880.0, 950.0), (840.0, 860.0), (790.0, 770.0), (745.0, 690.0),
             (722.0, 650.0)]
CAV_FUNGI = [(-430.0, 992.0, 26.0), (175.0, 978.0, 16.0), (985.0, 792.0, 14.0), (1255.0, 965.0, 24.0),
             (655.0, 1052.0, 13.0), (385.0, 762.0, 9.0), (830.0, 705.0, 8.0), (1520.0, 1045.0, 30.0),
             (-760.0, 994.0, 20.0), (40.0, 1250.0, 18.0), (1130.0, 1180.0, 22.0), (560.0, 690.0, 7.0),
             (-250.0, 1300.0, 24.0), (1700.0, 1350.0, 28.0)]
_CAV_STALAC_DRIP = (520.0, 990.0)                  # where drips hit the pool


@lru_cache(maxsize=4)
def _pool_path(kx=1.0, ky=1.0, seed=3):
    """Organic outline of the pool (stage coords), kx/ky scale it (basin rim)."""
    rng = np.random.default_rng(seed)
    px_, py_ = POOL_POS
    rx, ry = POOL_R
    pts = []
    for k in range(14):
        a = TAU * k / 14
        r = 1.0 + 0.09 * math.sin(a * 3 + 1.0) + 0.05 * (rng.random() - 0.5)
        pts.append((px_ + math.cos(a) * rx * kx * r, py_ + math.sin(a) * ry * ky * r))
    return smooth_path(pts, closed=True, tension=0.5)


def depth_scale(y):
    """Perspective size factor at floor height y in the cavern (1 at FLOOR_Y, ~0.14 at the far arch)."""
    return max(0.04, (y - CAV_HORIZON_Y) / (FLOOR_Y - CAV_HORIZON_Y))


@lru_cache(maxsize=1)
def _path_cum():
    d = [0.0]
    for (a, b) in zip(WALK_PATH[:-1], WALK_PATH[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return d


def path_point(u):
    """(x, y, scale) on the walkable path, u 0 (entry arch) .. 1 (far archway), by arc length."""
    d = _path_cum()
    s = clamp(u) * d[-1]
    for i in range(len(d) - 1):
        if s <= d[i + 1] or i == len(d) - 2:
            f = (s - d[i]) / max(1e-6, d[i + 1] - d[i])
            x = lerp(WALK_PATH[i][0], WALK_PATH[i + 1][0], f)
            y = lerp(WALK_PATH[i][1], WALK_PATH[i + 1][1], f)
            return x, y, depth_scale(y)
    return WALK_PATH[-1][0], WALK_PATH[-1][1], depth_scale(WALK_PATH[-1][1])


_HAZE = "#3A384C"


def _hz(color, depth, k=0.75):
    """Atmospheric haze: far things (small depth) lean toward the haze colour."""
    return _mixc(color, _HAZE, k * clamp(1.0 - depth * 1.5))


def _pillar(c, x, base_y, w, top_y, seed, depth, flare=1.6):
    rng = np.random.default_rng(seed)
    pts_l, pts_r = [], []
    n = 22
    for k in range(n + 1):
        yy = lerp(top_y, base_y, k / n)
        u = k / n
        waist = 1.0 - 0.22 * math.sin(math.pi * u) + flare * 0.35 * smoothstep((u - 0.78) / 0.22) \
            + 0.5 * smoothstep((0.12 - u) / 0.12)
        if top_y > -900:                      # free-standing tower: tapers to a blunt tip
            waist = (0.25 + 0.75 * smoothstep(u / 0.55)) * (1.0 + flare * 0.3 * smoothstep((u - 0.8) / 0.2))
        wl = w * 0.5 * waist * (1 + 0.1 * noise1(yy / (90 * max(depth, 0.2)), seed))
        wr = w * 0.5 * waist * (1 + 0.1 * noise1(yy / (80 * max(depth, 0.2)), seed + 1))
        pts_l.append((x - wl, yy))
        pts_r.append((x + wr, yy))
    pp = smooth_path(pts_l + pts_r[::-1], closed=True, tension=0.4)
    c.drawOval(skia.Rect(x - w * 1.2, base_y - w * 0.12, x + w * 1.2, base_y + w * 0.14), _P(K_INK, 0.35, blur=w * 0.1))
    c.drawPath(pp, _G(_lg(x - w * 0.6, 0, x + w * 0.6, 0, [_hz("#968A9C", depth), _hz("#766C80", depth),
                                                           _hz("#4A4352", depth), _hz("#2A2530", depth)],
                          [0, 0.35, 0.75, 1])))
    c.save()
    _clip(c, pp)
    if depth > 0.25:
        _lumps(c, x - w, top_y, x + w, base_y, max(30.0, w * 0.6), seed + 3,
               lambda xx, yy: 0.62 - 0.5 * clamp((xx - x + w * 0.3) / w), dark=_hz("#3A3442", depth),
               light=_hz("#A096A8", depth), aspect=1.7, alpha=0.45, rim=0.2, crease=0.25, density=0.7, var=0.1)
    # vertical flowstone streaks
    for k in range(5):
        sx = x + (rng.random() - 0.5) * w * 0.8
        c.drawLine(sx, top_y, sx + (rng.random() - 0.5) * w * 0.2, base_y, _S(_hz("#B0A4B4", depth), w * 0.04, 0.25))
    c.restore()
    c.drawPath(pp, _S(K_INK, max(1.2, 3.5 * depth), 0.75))


def _paint_cavern(c):
    X0, Y0, X1, Y1 = _C_BOUNDS
    # ---------------- far wall (vast, hazy)
    c.drawRect(skia.Rect(X0, Y0, X1, 900), _G(_lg(0, Y0, 0, 700, ["#0C0B10", "#16141C", "#24222E", "#363446", "#3E3C50"],
                                                  [0, 0.3, 0.6, 0.88, 1])))
    c.save()
    c.clipRect(skia.Rect(X0, -1900, X1, 760))
    _wash_blobs(c, X0, -1500, X1, 700, 18, 501, ["#4A5A70", "#6A5A58", "#3E5A58"], size=(300, 900), alpha=(0.08, 0.2))
    _lumps(c, X0, -1800, X1, 740, 420, 502, lambda x, y: 0.35 + 0.35 * clamp((y + 1400) / 2000) + 0.1 * noise1(x / 700, 3),
           dark="#1A1822", light="#4E4C5E", aspect=0.8, alpha=0.4, rim=0.15, crease=0.2, density=0.7, var=0.1)
    # flowstone curtains on the far wall
    rng = np.random.default_rng(503)
    for k in range(26):
        fx_ = X0 + rng.random() * (X1 - X0)
        top = -1700 + rng.random() * 600
        ln = 500 + rng.random() * 1100
        w = 40 + 120 * rng.random()
        pts = [(fx_ - w / 2, top), (fx_ - w * 0.35, top + ln * 0.6), (fx_, top + ln), (fx_ + w * 0.35, top + ln * 0.62),
               (fx_ + w / 2, top)]
        c.drawPath(smooth_path(pts, closed=True), _G(_lg(fx_ - w / 2, 0, fx_ + w / 2, 0, ["#4E4C60", "#36344A", "#242230"]),
                                                     0.6))
    # distant rock ridges (3 layers, increasing contrast as they come closer)
    for li, (ybase, amp, colr, sd) in enumerate(((560, 220, "#3A384C", 511), (610, 180, "#363246", 512),
                                                  (660, 140, "#322E42", 513))):
        pts = [(X0, 900)]
        for x in np.arange(X0, X1 + 60, 60.0):
            h = amp * (0.5 + 0.5 * _nz(x * 1.3, sd)) + 60 * max(0.0, noise1(x / 160.0, sd + 1))
            pts.append((x, ybase - max(0.0, h)))
        pts.append((X1, 900))
        rp = _poly(pts)
        c.drawPath(rp, _G(_lg(0, ybase - amp, 0, ybase + 60, [colr, _mixc(colr, "#2E2B38", 0.35)])))
        c.drawPath(smooth_path(pts[1:-1], closed=False), _S("#6A687E", 2.0, 0.25 + 0.1 * li))
    # far archway (the other door) on a far wall buttress
    ax, ay = FAR_ARCH_POS
    sc = depth_scale(ay)
    bpts = [(ax - 150, 900), (ax - 140, ay - 260), (ax - 90, ay - 330), (ax + 60, ay - 345), (ax + 140, ay - 280),
            (ax + 160, 900)]
    c.drawPath(smooth_path(bpts, closed=True, tension=0.3), _G(_lg(ax - 150, 0, ax + 160, 0, ["#4A4660", "#3C3850", "#302C42"])))
    c.save()
    c.translate(ax, ay)
    c.scale(sc, sc)
    c.translate(-DOOR_X, -DOOR_BOTTOM)
    c.drawPath(_arch_outline(DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM), _P("#07070B"))
    _paint_stone_arch(c, DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM, 808)
    c.restore()
    c.drawRect(skia.Rect(ax - 160, ay - 360, ax + 170, ay + 30), _P(_HAZE, 0.35))
    # far pillars
    for (px, pb, pw, top, sd) in ((300, 662, 150, -1250, 521), (585, 655, 70, 160, 522), (930, 676, 210, -1250, 523),
                                  (-170, 700, 190, -1250, 524), (1300, 690, 260, -1250, 525), (470, 652, 46, 420, 526),
                                  (1900, 700, 240, -1250, 527), (-600, 690, 230, -1250, 528)):
        _pillar(c, px, pb, pw, top, sd, depth_scale(pb), flare=1.8)
    # luminous mist over the far floor (aerial depth)
    c.drawRect(skia.Rect(X0, 300, X1, 760), _G(_lg(0, 300, 0, 760, [_c("#5A5A74", 0.0), _c("#5A5A74", 0.4),
                                                                    _c("#5A5A74", 0.0)], [0, 0.75, 1])))
    c.restore()
    # ---------------- floor
    fl = [(x, 648 + 14 * noise1(x / 90.0, 531) + 8 * noise1(x / 31.0, 532)) for x in np.arange(X0, X1 + 30, 30.0)]
    floor = _poly(fl + [(X1, Y1), (X0, Y1)])
    c.drawPath(floor, _G(_lg(0, 640, 0, Y1, ["#46445C", "#4E4A62", "#4A4458", "#3E3848", "#2A2632", "#121016"],
                             [0, 0.02, 0.07, 0.18, 0.3, 1])))
    c.save()
    _clip(c, floor)
    _wash_blobs(c, X0, 700, X1, 2000, 30, 533, ["#8A6A50", "#4E6A44", "#5A6A86"], size=(150, 600), alpha=(0.08, 0.2),
                sy=0.3)
    for (ya, yb, cell, asp, sd) in ((648, 720, 50, 0.22, 541), (700, 820, 90, 0.24, 542), (800, 980, 150, 0.27, 543),
                                    (960, 1250, 240, 0.3, 544), (1220, 1800, 380, 0.32, 545), (1750, 3500, 640, 0.34, 546)):
        dep = depth_scale((ya + yb) / 2)
        _lumps(c, X0, ya, X1, yb, cell, sd, lambda x, y: 0.5 + 0.15 * noise1(x / 500.0, 7) - 0.4 * clamp((y - 900) / 1400),
               dark=_hz("#2E2A36", dep), light=_hz("#887E92", dep), aspect=asp, alpha=0.5, rim=0.22, crease=0.3,
               density=0.85, var=0.12)
    c.restore()
    # ---------------- right wall (receding, with the crevice)
    rw = [(960, -2800)]
    for yy in np.linspace(-1600, 780, 30):
        rw.append((960 + 40 * _nz(yy, 551) + 70 * smoothstep((yy + 200) / 900), yy))
    rw += [(1010, 800), (1300, 900), (1700, 1080), (2200, 1300), (X1, 1420), (X1, -2800)]
    rwp = smooth_path(rw, closed=True, tension=0.25)
    c.drawPath(rwp, _G(_lg(960, 0, X1, 0, ["#34303F", "#4A4458", "#3E3848", "#24202C"], [0, 0.15, 0.5, 1])))
    c.save()
    _clip(c, rwp)
    _lumps(c, 900, -2000, X1, 1500, 230, 552, lambda x, y: 0.5 - 0.25 * clamp((x - 1000) / 1500) + 0.1 * noise1(y / 300, 5),
           dark="#2E2A36", light="#7A7086", aspect=0.75, alpha=0.5, rim=0.22, crease=0.32, density=0.9, var=0.12)
    _wash_blobs(c, 960, -800, X1, 1300, 10, 553, ["#4E6A44", "#8A6A50"], size=(150, 400), alpha=(0.1, 0.22))
    # near-edge AO at the floor junction
    c.drawPath(_poly([(1010, 800), (1300, 900), (1700, 1080), (2200, 1300), (X1, 1420)], close=False),
               _S(K_INK, 40, 0.4, blur=14))
    c.restore()
    c.drawPath(rwp, _S(K_INK, 3.5, 0.8))
    # the crevice: a tall jagged crack fading to black
    cx_, cy_ = CREVICE_POS
    rngc = np.random.default_rng(577)
    left_e, right_e = [], []
    for k in range(13):
        u = k / 12
        yy = cy_ - 230 + 410 * u
        w = 34 * math.sin(math.pi * (0.08 + 0.84 * u)) ** 0.8 + 4
        sh = 12 * math.sin(u * 5.0) + 6 * (rngc.random() - 0.5)
        left_e.append((cx_ + sh - w * (0.8 + 0.5 * rngc.random()), yy))
        right_e.append((cx_ + sh + w * (0.6 + 0.5 * rngc.random()), yy + 8 * (rngc.random() - 0.5)))
    crack = left_e + right_e[::-1]
    cp = _poly(crack)
    c.drawPath(cp, _S(K_INK, 30, 0.35, blur=12))
    c.drawPath(cp, _S("#8A8094", 7, 0.3))
    c.drawPath(cp, _G(_rg(cx_, cy_ - 20, 230, ["#020203", "#030304", "#100E14"], [0, 0.75, 1], sx=0.25, sy=1.0)))
    c.drawPath(_poly(left_e, close=False), _S(K_INK, 4, 0.85))
    c.drawPath(_poly(right_e, close=False), _S("#A89EB0", 2.5, 0.4))
    # fallen chips at its foot
    for k in range(6):
        bx = cx_ - 60 + rngc.random() * 130
        _boulder(c, bx, 800 + rngc.random() * 20, 6 + 10 * rngc.random(), 4 + 5 * rngc.random(), 580 + k, outline=0.5)
    # ---------------- left wall with the broken entry arch
    lw = [(X0, -2800), (60, -2800)]
    for yy in np.linspace(-1600, 990, 30):
        lw.append((150 + 50 * _nz(yy, 561) - 40 * smoothstep((yy - 600) / 400), yy))
    lw += [(110, 992), (X0, 992)]
    lwp = smooth_path(lw, closed=True, tension=0.25)
    c.drawPath(lwp, _G(_lg(X0, 0, 200, 0, ["#221E2A", "#3E3848", "#4E4658", "#34303E"], [0, 0.6, 0.85, 1])))
    c.save()
    _clip(c, lwp)
    _lumps(c, X0, -2000, 300, 1000, 220, 562, lambda x, y: 0.5 + 0.12 * noise1(x / 400, 9) - 0.2 * clamp((-x - 400) / 1200),
           dark="#2E2A36", light="#7A7086", aspect=0.7, alpha=0.5, rim=0.22, crease=0.32, density=0.9, var=0.12)
    _wash_blobs(c, X0, -600, 200, 990, 10, 563, ["#4E6A44", "#8A6A50"], size=(150, 400), alpha=(0.1, 0.22))
    c.drawRect(skia.Rect(X0, 900, 300, 1000), _G(_lg(0, 900, 0, 1000, [_c(K_INK, 0.0), _c(K_INK, 0.45)])))
    c.restore()
    c.drawPath(lwp, _S(K_INK, 3.5, 0.8))
    exs, exb, esc = ENTRY_ARCH
    c.save()
    c.translate(exs, exb)
    c.scale(esc, esc)
    c.translate(-DOOR_X, -DOOR_BOTTOM)
    c.drawPath(_arch_outline(DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM), _G(_rg(DOOR_X, DOOR_BOTTOM - 300, 600,
                                                                          ["#0A0A10", "#040406"], [0, 1])))
    _paint_stone_arch(c, DOOR_X, DOOR_TOP, DOOR_W, DOOR_BOTTOM, 404)
    rng2 = np.random.default_rng(31)
    xa = DOOR_X - DOOR_W / 2
    for (y0, y1) in ((DOOR_SPRING_Y - 40, DOOR_SPRING_Y + 160), (520, 640), (840, 1000)):
        pts = [(xa, y0), (xa + 30 + rng2.random() * 40, y0 + 10)]
        for u in np.linspace(0.2, 0.8, 4):
            pts.append((xa + 20 + rng2.random() * 70, lerp(y0, y1, u)))
        pts += [(xa + 26, y1), (xa, y1)]
        c.drawPath(_poly(pts), _P("#5A3B26"))
        c.drawPath(_poly(pts), _S("#1A0F08", 2.5, 0.9))
    c.restore()
    # splintered planks that flew in, lying on the floor in front of the entry
    rng3 = np.random.default_rng(571)
    for k in range(14):
        px = exs - 160 + rng3.random() * 520
        py = exb + 20 + rng3.random() * 200
        ds = depth_scale(py)
        L = (40 + 130 * rng3.random()) * ds
        wd = (10 + 14 * rng3.random()) * ds
        a = (rng3.random() - 0.5) * 50
        c.save()
        c.translate(px, py)
        c.rotate(a)
        c.drawRect(skia.Rect(-L / 2, -wd / 2 + wd * 0.3, L / 2, wd / 2 + wd * 0.3), _P(K_INK, 0.35))
        c.drawPath(_poly([(-L / 2, -wd / 2), (L / 2 - wd * 0.6, -wd / 2), (L / 2, 0), (L / 2 - wd * 0.3, wd / 2),
                          (-L / 2, wd / 2), (-L / 2 - wd * 0.4, 0)]), _P(_mixc("#6A4A2E", "#4A3020", rng3.random())))
        c.drawLine(-L / 2, -wd * 0.1, L / 2 - wd, -wd * 0.15, _S("#2E1C10", max(0.8, wd * 0.08), 0.6))
        c.restore()
    # ---------------- mid / near pillars, stalagmites
    _pillar(c, 1460, 1030, 170, -2800, 581, depth_scale(1030))
    for (sx, sy, sw, sh, sd) in ((235, 790, 26, 90, 591), (610, 815, 30, 120, 592), (880, 760, 22, 70, 593),
                                 (1180, 1230, 70, 260, 594), (1290, 1200, 46, 150, 595), (-330, 1180, 60, 210, 596),
                                 (-470, 1210, 40, 120, 597), (60, 960, 34, 110, 598), (1620, 1150, 80, 300, 599),
                                 (700, 735, 16, 50, 600)):
        ds = depth_scale(sy)
        _stalagmite(c, sx, sy, sw, sh, sd, base=_hz(K_R3, ds), light=_hz(K_R5, ds), dark=_hz(K_R1, ds))
    # boulders and stones by depth
    rng4 = np.random.default_rng(610)
    for k in range(60):
        y = 690 + rng4.random() ** 1.4 * 1300
        x = -900 + rng4.random() * 2900
        if (POOL_POS[0] - POOL_R[0] - 80 < x < POOL_POS[0] + POOL_R[0] + 80 and POOL_POS[1] - 90 < y < POOL_POS[1] + 110):
            continue
        if abs(x - SHIFT_STONE_POS[0]) < 120 and abs(y - SHIFT_STONE_POS[1]) < 60:
            continue
        if x < 150 and y < 1000:
            continue
        ds = depth_scale(y)
        r = (14 + 60 * rng4.random() ** 2.5) * ds
        if r < 2:
            continue
        _boulder(c, x, y - r * 0.3, r, r * 0.6, 620 + k, base=_hz(K_R3, ds), light=_hz(K_R5, ds), dark=_hz(K_R1, ds),
                 moss=rng4.random() * 0.6 if ds > 0.4 else 0.0, outline=0.8 if ds > 0.3 else 0.4)
    # ---------------- the pool (basin + still black water)
    wp = _pool_path()
    px_, py_ = POOL_POS
    rx, ry = POOL_R
    rim = _pool_path(1.13, 1.32, 6)
    c.drawPath(rim, _P("#26222E"))
    c.drawPath(rim, _S("#6E6478", 3, 0.3))
    for k in range(11):
        a = TAU * (k + rng4.random() * 0.6) / 11
        if 0.2 < a < 1.2:
            continue
        bx, by = px_ + math.cos(a) * (rx + 22), py_ + math.sin(a) * (ry + 9)
        r = 10 + 18 * rng4.random()
        _boulder(c, bx, by, r, r * 0.5, 700 + k, base=K_R2, light=K_R4, dark=K_R1, shadow=False, outline=0.6)
    c.drawPath(wp, _G(_lg(0, py_ - ry, 0, py_ + ry, ["#1E3644", "#10202A", "#081218", "#05090C"], [0, 0.3, 0.7, 1])))
    c.save()
    _clip(c, wp)
    for (rx_, w_) in ((330, 30), (560, 24), (px_ + rx * 0.8, 60)):
        c.drawRect(skia.Rect(rx_ - w_ / 2, py_ - ry, rx_ + w_ / 2, py_ + ry),
                   _G(_lg(0, py_ - ry, 0, py_ + ry * 0.6, [_c("#4A5A6A", 0.3), _c("#4A5A6A", 0.0)])))
    for k in range(5):
        gy = py_ - ry * 0.6 + k * ry * 0.28
        gx = px_ + (rng4.random() - 0.5) * rx
        c.drawLine(gx - 40, gy, gx + 40, gy, _S("#5FA8C0", 1.6, 0.16))
    c.restore()
    c.drawPath(wp, _S("#5FA8C0", 2.0, 0.2))
    # ---------------- fungi
    for i, (fx_, fy_, fr) in enumerate(CAV_FUNGI):
        ds = depth_scale(fy_)
        _fungi_patch(c, fx_, fy_, fr * max(0.35, ds), 900 + i, scale=max(0.35, ds))
    # ---------------- ceiling: dark vault + stalactites
    cl = [(x, -1150 + 150 * _nz(x * 0.5, 641)) for x in np.arange(X0, X1 + 60, 60.0)]
    cp = _poly([(X0, Y0), (X1, Y0)] + cl[::-1])
    c.drawPath(cp, _G(_lg(0, Y0, 0, -1000, ["#0A090E", "#16141C", "#262430"])))
    c.drawPath(smooth_path(cl, closed=False), _S("#4A4858", 3, 0.35))
    rng5 = np.random.default_rng(650)
    for k in range(48):
        x = X0 + rng5.random() * (X1 - X0)
        near = rng5.random()
        w = 40 + 170 * near ** 2
        h = 250 + 950 * near ** 1.5
        top = -1150 + 150 * _nz(x * 0.5, 641) - 40 - 80 * near
        _stalactite(c, x, top, w, h, 660 + k, base=_mixc("#34324A", K_R3, near), light=_mixc("#4E4C60", K_R5, near),
                    dark=_mixc("#1E1C26", K_R1, near), wet=near > 0.5)
    # ---------------- near framing pillars (foreground, very dark when unlit)
    _pillar(c, -1500, 1700, 420, -2800, 701, 1.4, flare=1.2)
    _pillar(c, 2350, 1800, 480, -2800, 702, 1.5, flare=1.2)


@lru_cache(maxsize=1)
def _cavern_pic():
    return _record(_C_BOUNDS, _paint_cavern)


def _draw_shift_stone(c, tilt):
    x, y = SHIFT_STONE_POS
    ang = -24.0 * tilt
    w, h = 128.0, 36.0
    px, py = x + w * 0.45, y + h * 0.4               # pivot: right foot
    # contact shadow and the dark gap under the lifted end
    c.drawOval(skia.Rect(x - w * 0.62, y + h * 0.15, x + w * 0.62, y + h * 0.7), _P(K_INK, 0.5, blur=4))
    c.save()
    c.translate(px, py)
    c.rotate(ang)
    c.translate(-px, -py)
    pts = [(x - w * 0.5, y + h * 0.3), (x - w * 0.46, y - h * 0.25), (x - w * 0.2, y - h * 0.52), (x + w * 0.25, y - h * 0.5),
           (x + w * 0.5, y - h * 0.18), (x + w * 0.48, y + h * 0.35), (x, y + h * 0.48)]
    path = smooth_path(pts, closed=True, tension=0.3)
    c.drawPath(path, _G(_lg(0, y - h * 0.5, 0, y + h * 0.5, ["#A094A6", "#766C80", "#3E3848"], [0, 0.45, 1])))
    c.drawPath(_poly([(x - w * 0.42, y - h * 0.2), (x - w * 0.18, y - h * 0.45), (x + w * 0.2, y - h * 0.44),
                      (x + w * 0.05, y - h * 0.1)]), _P("#B8ACBA", 0.45))
    c.drawLine(x - w * 0.1, y - h * 0.4, x + w * 0.05, y + h * 0.3, _S(K_INK, 1.6, 0.5))
    c.drawPath(path, _S(K_INK, 2.2, 0.85))
    c.restore()


def _draw_pool_dynamic(c, t, splash_t, torch_pos, drips, torch_float):
    px_, py_ = POOL_POS
    rx, ry = POOL_R
    wp = _pool_path()
    c.save()
    _clip(c, wp)
    # slow shimmering glints (still water)
    for k in range(4):
        gx = px_ - rx * 0.6 + k * rx * 0.4 + 20 * math.sin(t * 0.3 + k)
        gy = py_ - ry * 0.4 + (k % 2) * ry * 0.5
        a = 0.15 + 0.1 * math.sin(t * 0.9 + k * 1.7)
        c.drawLine(gx - 30, gy, gx + 30, gy, _S("#7FC4D8", 1.4, a))
    if torch_pos is not None:
        tx, ty = torch_pos
        mx = tx
        d = max(0.0, (py_ - ty)) / 700.0
        a = clamp(1.0 - abs(tx - px_) / (rx * 1.6)) * clamp(1.2 - d * 0.6)
        if a > 0.01:
            for k in range(6):
                yy = py_ - ry * 0.85 + k * ry * 0.32
                ww = 26 + 10 * k + 6 * math.sin(t * 3 + k)
                xo = 6 * math.sin(t * 2.3 + k * 1.3)
                c.drawLine(mx - ww / 2 + xo, yy, mx + ww / 2 + xo, yy, _S("#FFB860", 3.0, 0.55 * a * (1 - k / 7)))
    # periodic drip ripples from the stalactite above
    if drips:
        dx, dy = _CAV_STALAC_DRIP
        per = 3.7
        ph = (t + 1.3) % per
        fx.ripples(c, dx, dy, ph, size=0.35, n=2, alpha=0.8, life=2.2)
    c.restore()
    if splash_t is not None and splash_t >= 0:
        sx, sy = TORCH_SPLASH_POS
        if splash_t < 4.0:
            fx.splash(c, t, sx, sy, splash_t, size=1.15, seed=17, rings=False)
        c.save()
        _clip(c, wp)
        fx.ripples(c, sx, sy, splash_t, size=0.85, n=4, life=5.0, squash=ry / rx)
        c.restore()
        # the dead torch floating, bobbing, slowly drifting
        if torch_float and splash_t > 0.35:
            u = splash_t - 0.35
            bob = math.sin(u * 2.4) * 3 * math.exp(-u * 0.25) + 2
            fxp = sx + 26 * (1 - math.exp(-u * 0.25)) + 8 * math.sin(u * 0.4)
            fyp = sy + 4 + bob
            emerge = smoothstep(u / 0.6)
            c.save()
            _clip(c, _poly([(px_ - rx - 50, py_ - ry - 400), (px_ + rx + 50, py_ - ry - 400), (px_ + rx + 50, fyp + 2),
                            (px_ - rx - 50, fyp + 2)]))
            fx.draw_torch(c, fxp, fyp + 10 * (1 - emerge), t, angle=80 + 4 * math.sin(u * 1.1), scale=0.8, lit=0.0, wet=1.0)
            c.restore()
            c.drawOval(skia.Rect(fxp - 80, fyp - 4, fxp + 80, fyp + 8), _S("#7FC4D8", 1.4, 0.25 * emerge))
        fx.steam(c, t, sx, sy - 6, splash_t, amount=1.4, size=1.2, seed=21)
    # drips falling from the stalactite (the drop itself)
    if drips:
        dx, dy = _CAV_STALAC_DRIP
        fx.drips(c, t, dx, dy - 640, period=3.7, phase=-1.3 - 3.7 * 0.78 - math.sqrt(2 * 640 / 2000.0), fall=640,
                 size=0.8, splash=False)


def draw_cavern(canvas, t, stone_tilt=0.0, pool_splash_t=None, torch_pos=None, drips=True, torch_float=True):
    """The S2 cavern (STAGE coords). See module doc."""
    c = canvas
    _blit(c, "cavern", _cavern_pic, _C_BOUNDS, opaque=True)
    vis = c.getLocalClipBounds()
    if vis.right() > SHIFT_STONE_POS[0] - 200 and vis.left() < SHIFT_STONE_POS[0] + 200 and vis.bottom() > 1050:
        _draw_shift_stone(c, stone_tilt)
    if vis.right() > POOL_POS[0] - POOL_R[0] - 300 and vis.left() < POOL_POS[0] + POOL_R[0] + 300:
        _draw_pool_dynamic(c, t, pool_splash_t, torch_pos, drips, torch_float)


def cavern_lights(t, strength=1.0):
    """Dim teal fungus lights of the cavern (stage coords) for light.apply_darkness."""
    if strength <= 0:
        return []
    out = []
    for i, (x, y, r) in enumerate(CAV_FUNGI):
        ds = max(0.35, depth_scale(y))
        out.append(fungus_light(x, y - r * 0.3, t, radius=(230 + r * 8) * ds, strength=strength, seed=i))
    return out


def draw_fungi_glow(canvas, t, which="cavern", alpha=1.0):
    """EMISSIVE glow specks on the fungus patches (draw after apply_darkness, under the camera)."""
    if alpha <= 0.01:
        return
    if which == "cavern":
        sc = [max(0.35, depth_scale(y)) for (x, y, r) in CAV_FUNGI]
        patches = [(x, y, r * k) for (x, y, r), k in zip(CAV_FUNGI, sc)]
        _fungi_glow_specks(canvas, t, patches, alpha, seed0=900, scales=sc)
    else:
        _fungi_glow_specks(canvas, t, DEP_FUNGI, alpha, seed0=950)


# =========================================================================== SHAFT (S3)
LEDGE_Y = 600.0                     # floor surface of the cavern at the hole (where Anger stands)
SHAFT_FLOOR_Y = LEDGE_Y
HOLE_X = (150.0, 610.0)             # the hole / shaft opening between these x
LEDGE_POS = (HOLE_X[0] + 6.0, LEDGE_Y + 2.0)      # the lip corner his gauntlet grips (left edge of the hole)
SHAFT_X = (HOLE_X[0] - 30.0, HOLE_X[1] + 30.0)    # visible back-wall span of the shaft
GOUGE_X = 300.0                     # a good x for the sword gouge (on the back wall)
SHAFT_PERIOD = 3072.0
_SLAB_Y = LEDGE_Y + 200.0           # bottom of the rock slab; the periodic wall starts here
_SH_X = (-900.0, 1600.0)
_SH_TOP_BOUNDS = (-900.0, -1600.0, 1600.0, _SLAB_Y + 160.0)
_CRACK_O = (380.0, LEDGE_Y)


def shaft_wall_y(y, scroll):
    """Stage y (at the given scroll) -> wall coordinates (stage y at scroll 0)."""
    return y + scroll


def _strata_colors():
    return ["#5A4232", "#4A382C", "#6E5444", "#3E3236", "#5E4E46", "#4A3C34", "#6A5A50", "#3A2E28"]


def _paint_shaft_wall(c):
    """One period [0, P) of the shaft below the slab (wall-y measured from _SLAB_Y):
    left / right cut-away earth (strata, roots, embedded stones) + the face-on back wall in the middle."""
    P = SHAFT_PERIOD
    x0, x1 = _SH_X
    rng = np.random.default_rng(1201)
    # strata bands across the whole width (wrap-safe: all band shapes are periodic in y by construction)
    cols = _strata_colors()
    y = 0.0
    bands = []
    while y < P:
        h = 90 + rng.random() * 220
        bands.append((y, min(P, y + h), cols[int(rng.integers(0, len(cols)))]))
        y += h
    for (ya, yb, colr) in bands:
        pts = [(x, ya + 18 * math.sin(x / 260.0 + ya) + 8 * noise1(x / 70.0, int(ya)))
               for x in np.arange(x0, x1 + 40, 40.0)]
        if ya == 0.0:
            pts = [(x, -60.0) for x in np.arange(x0, x1 + 40, 40.0)]
        poly = pts + [(x1, yb + 80), (x0, yb + 80)]
        c.drawPath(_poly(poly), _G(_lg(0, ya, 0, yb + 80, [_mixc(colr, "#8A7262", 0.18), colr, _mixc(colr, K_INK, 0.25)],
                                       [0, 0.5, 1])))
        c.drawPath(smooth_path(pts, closed=False), _S(_mixc(colr, "#B8A08A", 0.4), 2.5, 0.35))
    # embedded stones (cross-sections) + roots
    for k in range(70):
        sx = x0 + rng.random() * (x1 - x0)
        sy = 60 + rng.random() * (P - 160)
        r = 8 + 46 * rng.random() ** 2.2
        _boulder(c, sx, sy, r, r * 0.65, 1300 + k, base=_mixc(K_R3, K_WARM, rng.random() * 0.5), shadow=False,
                 outline=0.7)
    for k in range(26):
        rx = x0 + rng.random() * (x1 - x0)
        ry = 40 + rng.random() * (P - 500)
        _root(c, rx, ry, 120 + 300 * rng.random(), 1400 + k, w0=4 + 9 * rng.random(), color="#6A4A32", hi="#8A6A4A",
              curl=1.8, alpha=0.9)
    # the shaft: face-on back wall (lighter, rockier), dark inner edges where the cut faces turn away
    l_edge = [(HOLE_X[0] + 14 * noise1(yy / 150.0, 1211) + 10 * noise1(yy / 47.0, 1212), yy)
              for yy in np.arange(-40.0, P + 41.0, 40.0)]
    r_edge = [(HOLE_X[1] + 14 * noise1(yy / 150.0, 1213) + 10 * noise1(yy / 47.0, 1214), yy)
              for yy in np.arange(-40.0, P + 41.0, 40.0)]
    # make the edges periodic: blend the last 200 units back to the first values
    def per(edge):
        out = []
        for (x, yy) in edge:
            if yy > P - 200:
                k = (yy - (P - 200)) / 200
                x0_ = [e for e in edge if abs(e[1] - (yy - P)) < 21]
                if x0_:
                    x = lerp(x, x0_[0][0], smoothstep(k))
            out.append((x, yy))
        return out
    l_edge, r_edge = per(l_edge), per(r_edge)
    shaft = _poly(l_edge + r_edge[::-1])
    c.save()
    _clip(c, shaft)
    c.drawRect(skia.Rect(x0, -60, x1, P + 60), _P("#4A4250"))
    for (ya, yb, colr) in bands:
        c.drawRect(skia.Rect(x0, ya, x1, yb + 2), _G(_lg(0, ya, 0, yb, [_mixc(colr, "#8A8094", 0.5),
                                                                       _mixc(colr, "#5E566A", 0.5)])))
        c.drawLine(x0, ya + 1, x1, ya + 1, _S(_mixc(colr, "#B0A4B4", 0.5), 2.0, 0.3))
    _lumps(c, HOLE_X[0] - 60, 60, HOLE_X[1] + 60, P - 60, 230, 1220, lambda xx, yy: 0.5 + 0.12 * noise1(yy / 300.0, 3),
           dark="#3A3442", light="#8E8494", aspect=0.45, alpha=0.35, rim=0.2, crease=0.28, density=0.45, var=0.14,
           warm=0.3)
    for k in range(22):
        sx = HOLE_X[0] + rng.random() * (HOLE_X[1] - HOLE_X[0])
        sy = 80 + rng.random() * (P - 160)
        r = 10 + 30 * rng.random() ** 1.5
        _boulder(c, sx, sy, r, r * 0.7, 1230 + k, base=_mixc(K_R3, K_WARM, rng.random() * 0.4), shadow=False, outline=0.6)
    # vertical scrape / water streaks
    for k in range(18):
        sx = HOLE_X[0] + rng.random() * (HOLE_X[1] - HOLE_X[0])
        sy = rng.random() * P
        c.drawLine(sx, sy, sx + (rng.random() - 0.5) * 10, sy + 100 + 300 * rng.random(), _S("#2A2430", 2 + 3 * rng.random(), 0.3))
    # shading: dark toward both cut edges (the shaft is round), light in the middle
    mid = (HOLE_X[0] + HOLE_X[1]) / 2
    hw = (HOLE_X[1] - HOLE_X[0]) / 2
    c.drawRect(skia.Rect(HOLE_X[0] - 60, -60, HOLE_X[1] + 60, P + 60),
               _G(_lg(mid - hw - 30, 0, mid + hw + 30, 0, [_c(K_INK, 0.85), _c(K_INK, 0.25), _c(K_INK, 0.0),
                                                            _c(K_INK, 0.1), _c(K_INK, 0.45), _c(K_INK, 0.9)],
                      [0, 0.12, 0.4, 0.6, 0.88, 1])))
    c.restore()
    c.drawPath(_poly(l_edge, close=False), _S(K_INK, 5, 0.85))
    c.drawPath(_poly(r_edge, close=False), _S(K_INK, 5, 0.85))
    c.drawPath(_poly([(x - 5, y) for x, y in l_edge], close=False), _S("#B09A88", 2, 0.3))
    c.drawPath(_poly([(x + 5, y) for x, y in r_edge], close=False), _S("#B09A88", 2, 0.3))
    # roots poking out of the cut faces into the shaft
    for k in range(9):
        side = -1 if k % 2 == 0 else 1
        ex = HOLE_X[0] if side < 0 else HOLE_X[1]
        ey = 100 + rng.random() * (P - 300)
        L = 60 + 140 * rng.random()
        pts = [(ex, ey), (ex - side * L * 0.4, ey + L * 0.15), (ex - side * L * 0.75, ey + L * 0.45),
               (ex - side * L * 0.85, ey + L * 0.9)]
        c.drawPath(_taper_path(pts, 9, 1.5), _P("#6A4A32"))
        c.drawPath(_taper_path(pts, 9, 1.5), _S(K_INK, 1.2, 0.7))
    # far side vignette: the cut-away earth darkens away from the shaft
    c.drawRect(skia.Rect(x0, -60, HOLE_X[0] - 200, P + 60), _G(_lg(x0, 0, HOLE_X[0] - 200, 0,
                                                                    [_c("#100E12", 0.85), _c("#100E12", 0.0)])))
    c.drawRect(skia.Rect(HOLE_X[1] + 200, -60, x1, P + 60), _G(_lg(HOLE_X[1] + 200, 0, x1, 0,
                                                                    [_c("#100E12", 0.0), _c("#100E12", 0.85)])))


@lru_cache(maxsize=1)
def _shaft_wall_pic():
    return _record((_SH_X[0], 0.0, _SH_X[1], SHAFT_PERIOD), _paint_shaft_wall)


def _slab_edge(x):
    return LEDGE_Y + 4 * noise1(x / 60.0, 1251)


def _paint_shaft_top(c):
    """Non-periodic top: the dark cavern above, the floor slab (cut-away) on both sides of the hole."""
    X0, Y0, X1, Y1 = _SH_TOP_BOUNDS
    # dark cavern backdrop above the floor
    c.drawRect(skia.Rect(X0, Y0, X1, LEDGE_Y + 10), _G(_lg(0, Y0, 0, LEDGE_Y, ["#0A090E", "#16141E", "#262436", "#2E2C40"],
                                                          [0, 0.5, 0.85, 1])))
    c.save()
    c.clipRect(skia.Rect(X0, Y0, X1, LEDGE_Y + 10))
    _ridge = [(x, 470 - 120 * max(0.0, _nz(x * 1.2, 1261))) for x in np.arange(X0, X1 + 40, 40.0)]
    c.drawPath(_poly([(X0, LEDGE_Y + 10)] + _ridge + [(X1, LEDGE_Y + 10)]), _P("#24222F"))
    for (px, w) in ((-500, 160), (1100, 220), (40, 90), (820, 120)):
        _pillar(c, px, LEDGE_Y + 5, w, -1600, 1270 + int(px), 0.3, flare=1.5)
    rng = np.random.default_rng(1271)
    for k in range(18):
        x = X0 + rng.random() * (X1 - X0)
        _stalactite(c, x, -1600, 40 + 100 * rng.random(), 300 + 700 * rng.random(), 1280 + k, base="#3A3848",
                    light="#5A586A", dark="#22202A", wet=False)
    c.drawRect(skia.Rect(X0, 200, X1, LEDGE_Y + 10), _G(_lg(0, 200, 0, LEDGE_Y, [_c("#4A4A64", 0.0), _c("#4A4A64", 0.3)])))
    c.restore()
    # the slab (left and right of the hole): floor surface + rock cross-section
    for (xa, xb, sd) in ((X0, HOLE_X[0], 1290), (HOLE_X[1], X1, 1291)):
        top = [(x, _slab_edge(x)) for x in np.arange(xa, xb + 1, 20.0)]
        bot = [(x, _SLAB_Y + 30 * noise1(x / 120.0, sd) + 30) for x in np.arange(xb, xa - 1, -20.0)]
        # broken edge at the hole side
        if xb == HOLE_X[0]:
            edge = [(xb, LEDGE_Y + 2), (xb + 8, LEDGE_Y + 30), (xb - 4, LEDGE_Y + 80), (xb + 6, LEDGE_Y + 130),
                    (xb - 6, _SLAB_Y + 40)]
            pts = top + edge + bot[1:]
        else:
            edge = [(xa + 6, _SLAB_Y + 40), (xa - 6, LEDGE_Y + 120), (xa + 4, LEDGE_Y + 60), (xa - 8, LEDGE_Y + 20),
                    (xa, LEDGE_Y + 2)]
            pts = edge + top + bot[:-1]
        slab = _poly(pts)
        c.drawPath(slab, _G(_lg(0, LEDGE_Y, 0, _SLAB_Y + 60, ["#6E6476", "#5A5266", "#463E50", "#3A3240"],
                                [0, 0.1, 0.6, 1])))
        c.save()
        _clip(c, slab)
        _lumps(c, xa - 50, LEDGE_Y, xb + 50, _SLAB_Y + 80, 90, sd + 5, lambda x, y: 0.55 - 0.3 * clamp((y - LEDGE_Y) / 200),
               dark="#3A3442", light="#968A9C", aspect=0.55, alpha=0.55, rim=0.25, crease=0.35, density=1.1, var=0.12)
        c.drawRect(skia.Rect(xa - 50, LEDGE_Y - 4, xb + 50, LEDGE_Y + 16), _P("#8A7F90", 0.55))
        _crack_lines(c, xa, LEDGE_Y + 20, xb, _SLAB_Y, int(abs(xb - xa) / 120) + 2, sd + 9, length=70, vertical=0.8)
        c.restore()
        c.drawPath(slab, _S(K_INK, 3.5, 0.85))
        c.drawPath(_poly(top, close=False), _S("#B8ACBA", 2.0, 0.45))
    _pebbles(c, X0, X1, lambda x: LEDGE_Y - 6, 40, 1299, smin=3, smax=10, yspread=(0, 6))


@lru_cache(maxsize=1)
def _shaft_top_pic():
    return _record(_SH_TOP_BOUNDS, _paint_shaft_top)


def _blit_periodic_y(c, name, pic_fn, x_bounds, period, y_origin, blur=0.0):
    """Blit a vertically periodic picture (one period [0, P) recorded) so that wall-y 0 sits at
    stage y = y_origin.  Each res bucket rasterises the full period once as a strip."""
    vis = c.getLocalClipBounds()
    res = _res_bucket(_mscale(c))
    taps = [(0.0, 1.0)] if blur <= 0.5 else [(-blur * 0.5, 0.34), (0.0, 0.5), (blur * 0.5, 1.0)]
    for (dy, a) in taps:
        top = vis.top() - y_origin - dy
        bot = vis.bottom() - y_origin - dy
        k0 = math.floor(top / period)
        k1 = math.floor(bot / period)
        for k in range(k0, k1 + 1):
            c.save()
            c.translate(0, y_origin + dy + k * period)
            c.clipRect(skia.Rect(x_bounds[0], 0, x_bounds[1], period))
            v = c.getLocalClipBounds()
            if not v.isEmpty():
                rect, img = _TILES.get(name, res, v, (x_bounds[0], 0.0, x_bounds[1], period), pic_fn, True,
                                       full=(False, True))
                if img is not None:
                    p = skia.Paint()
                    if a < 1:
                        p.setAlphaf(a)
                    c.drawImageRect(img, skia.Rect(0, 0, img.width(), img.height()), rect, _LIN, p,
                                    skia.Canvas.kFast_SrcRectConstraint)
            c.restore()


def _slab_pieces():
    """Chunks of the floor slab over the hole (polygons in stage coords at scroll 0)."""
    rng = np.random.default_rng(1311)
    xs = [HOLE_X[0]] + sorted(HOLE_X[0] + 40 + rng.random(4) * (HOLE_X[1] - HOLE_X[0] - 80)) + [HOLE_X[1]]
    pieces = []
    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]
        ym = LEDGE_Y + 70 + rng.random() * 60
        for (ya, yb) in ((LEDGE_Y, ym), (ym, _SLAB_Y + 30)):
            j1 = (rng.random() - 0.5) * 30
            j2 = (rng.random() - 0.5) * 30
            poly = [(xa + j1 * 0.3, ya), (xb + j2 * 0.3, ya), (xb + j2, yb), (xa + j1, yb)]
            pieces.append(poly)
    return pieces


_SLAB_PIECES = None


def _draw_slab(c, t, crack, collapse_t, scroll):
    global _SLAB_PIECES
    if _SLAB_PIECES is None:
        _SLAB_PIECES = _slab_pieces()
    g = 2600.0
    if collapse_t is None or collapse_t < 0:
        top = [(x, _slab_edge(x)) for x in np.arange(HOLE_X[0] - 20, HOLE_X[1] + 21, 20.0)]
        bot = [(x, _SLAB_Y + 30 * noise1(x / 120.0, 1290) + 30) for x in np.arange(HOLE_X[1] + 20, HOLE_X[0] - 21, -20.0)]
        slab = _poly([(x, y - scroll) for x, y in top + bot])
        c.drawPath(slab, _G(_lg(0, LEDGE_Y - scroll, 0, _SLAB_Y + 60 - scroll, ["#6E6476", "#5A5266", "#463E50", "#3A3240"],
                                [0, 0.1, 0.6, 1])))
        c.save()
        _clip(c, slab)
        c.translate(0, -scroll)
        _lumps(c, HOLE_X[0] - 40, LEDGE_Y, HOLE_X[1] + 40, _SLAB_Y + 80, 90, 1295,
               lambda x, y: 0.55 - 0.3 * clamp((y - LEDGE_Y) / 200), dark="#3A3442", light="#968A9C", aspect=0.55,
               alpha=0.55, rim=0.25, crease=0.35, density=1.1, var=0.12)
        c.drawRect(skia.Rect(HOLE_X[0] - 40, LEDGE_Y - 4, HOLE_X[1] + 40, LEDGE_Y + 16), _P("#8A7F90", 0.55))
        c.restore()
        c.drawPath(_poly([(x, y - scroll) for x, y in top], close=False), _S("#B8ACBA", 2.0, 0.45))
    for i, poly in enumerate(_SLAB_PIECES if (collapse_t is not None and collapse_t >= 0) else []):
        cx = sum(p[0] for p in poly) / 4
        cy = sum(p[1] for p in poly) / 4
        dx = dy = rot = 0.0
        if collapse_t is not None and collapse_t >= 0:
            delay = 0.02 + 0.10 * abs(cx - _CRACK_O[0]) / 300.0 + (0.04 if cy > LEDGE_Y + 100 else 0.0)
            a = max(0.0, collapse_t - delay)
            dy = 0.5 * g * a * a
            dx = (cx - _CRACK_O[0]) * 0.25 * a
            rot = (hash01(i, 77) - 0.5) * 120 * a
            if dy > 2600:
                continue
        c.save()
        c.translate(cx + dx, cy + dy - scroll)
        c.rotate(rot)
        path = _poly([(p[0] - cx, p[1] - cy) for p in poly])
        top = min(p[1] for p in poly) - cy
        c.drawPath(path, _G(_lg(0, top, 0, top + 200, ["#6E6476", "#4E4658", "#3A3240"])))
        if poly[0][1] <= LEDGE_Y + 1:
            c.drawLine(poly[0][0] - cx, top + 2, poly[1][0] - cx, top + 2, _S("#B8ACBA", 2.0, 0.45))
        c.drawPath(path, _S(K_INK, 3.0, 0.85))
        c.restore()
    if crack > 0 and (collapse_t is None or collapse_t < 0.05):
        rng = np.random.default_rng(1321)
        ox, oy = _CRACK_O
        for b in range(7):
            ang = math.pi * (0.15 + 0.7 * rng.random()) if b > 1 else (0.0 if b == 0 else math.pi)
            L = (60 + 200 * rng.random()) * clamp(crack * 1.3 - b * 0.08)
            if L <= 1:
                continue
            pts = [(ox, oy - scroll)]
            x, y = ox, oy
            for k in range(5):
                ang += (rng.random() - 0.5) * 0.7
                x += math.cos(ang) * L / 5
                y += abs(math.sin(ang)) * L / 5 * (1 if b > 1 else 0.15)
                pts.append((x, y - scroll))
            c.drawPath(_poly(pts, close=False), _S(K_INK, 3.0 * (1 - 0.1 * b), 0.9))
        fx.dust_fall(c, t, ox - 80, ox + 80, _SLAB_Y - scroll, amount=crack, seed=31, length=240)


def _draw_gouge(c, t, gouge, scroll):
    gx, y0, y1 = gouge
    if y1 <= y0 + 1:
        return
    n = max(4, int((y1 - y0) / 30))
    pts = [(gx + 7 * noise1(yy / 90.0, 1331) + 3 * noise1(yy / 23.0, 1332), yy - scroll)
           for yy in np.linspace(y0, y1, n + 1)]
    # spilled soil beside the groove and the gash itself
    c.drawPath(_taper_path(pts, 30, 40), _P("#3A2C24", 0.55))
    c.drawPath(_taper_path([(x - 3, y) for x, y in pts], 16, 22), _P("#0A0808", 0.95))
    c.drawPath(_poly([(x - 13, y) for x, y in pts], close=False), _S("#C8B8A8", 2.4, 0.6))
    c.drawPath(_poly([(x + 11, y) for x, y in pts], close=False), _S("#8A7868", 2.0, 0.5))
    # hot fresh end
    ex, ey = pts[-1]
    hot = min(1.0, (y1 - y0) / 80.0)
    tail = [p for p in pts if p[1] > ey - 160]
    if len(tail) >= 2:
        c.drawPath(_poly(tail, close=False), _S("#FF7A2A", 6, 0.55 * hot))
    fx._blob(c, ex, ey, 40, "#FF8A3A", 0.5 * hot, add=True)


def draw_shaft(canvas, t, scroll=0.0, gouge=None, crack=0.0, collapse_t=None, blur=0.0, bottom=None, dust=0.0):
    """The S3 shaft (STAGE coords; scroll moves everything up). See module doc."""
    c = canvas
    vis = c.getLocalClipBounds()
    # periodic wall below the slab
    if vis.bottom() > _SLAB_Y - scroll:
        _blit_periodic_y(c, "shaft_wall", _shaft_wall_pic, _SH_X, SHAFT_PERIOD, _SLAB_Y - scroll, blur=blur)
    # top (cavern + slab remnants)
    if vis.top() < _SH_TOP_BOUNDS[3] - scroll:
        c.save()
        c.translate(0, -scroll)
        _blit(c, "shaft_top", _shaft_top_pic, _SH_TOP_BOUNDS, opaque=False)
        c.restore()
        _draw_slab(c, t, crack, collapse_t, scroll)
        if collapse_t is not None and collapse_t >= 0:
            fx.debris(c, t, collapse_t, (_CRACK_O[0], LEDGE_Y + 40 - scroll), seed=41, kind="stone", n=16, speed=420,
                      direction=90, spread=150, size=1.3)
            fx.dust_cloud(c, t, _CRACK_O[0], LEDGE_Y - 10 - scroll, collapse_t, size=1.8, seed=42, life=3.0, alpha=0.8)
        if dust > 0:
            fx.dust_fall(c, t, LEDGE_POS[0] - 30, LEDGE_POS[0] + 50, LEDGE_Y + 6 - scroll, amount=dust, seed=43,
                         length=420, size=1.2)
    if gouge is not None:
        _draw_gouge(c, t, gouge, scroll)
    if bottom is not None:
        by = bottom - scroll
        if by < vis.bottom() + 200:
            c.drawRect(skia.Rect(_SH_X[0], by + 40, _SH_X[1], by + 3000), _P("#141218"))
            rng = np.random.default_rng(1341)
            for k in range(24):
                bx = HOLE_X[0] - 300 + rng.random() * (HOLE_X[1] - HOLE_X[0] + 600)
                r = 20 + 60 * rng.random() ** 1.5
                _boulder(c, bx, by + 30 + rng.random() * 60, r, r * 0.6, 1350 + k, base=K_R3, moss=0.0)


def shaft_lights(t, strength=1.0):
    """Faint cold glow from the cavern above the lip (stage coords at scroll 0; offset y by -scroll)."""
    return [Light(380.0, 200.0, 900.0, 0.18 * strength, "#6A86B0", "point")]


# =========================================================================== DEPTHS (S4-S6)
WALL_X = 560.0                       # face of the wall Anger props his back against (wall extends right)
WALL_LEAN_Y = 760.0                  # where his shoulders touch when propped
DARK_X = 40.0                        # left of this: deep shadow (the voice, the glove, the friend's entrance)
SHAFT_OPEN_X = (240.0, 600.0)        # the hole in the ceiling he fell through
DEP_FUNGI = [(650.0, 1132.0, 18.0), (905.0, 760.0, 14.0), (200.0, 1185.0, 11.0), (1180.0, 1110.0, 24.0),
             (-260.0, 1175.0, 10.0), (760.0, 420.0, 12.0), (1450.0, 1150.0, 20.0), (-700.0, 1190.0, 14.0)]
_D_BOUNDS = (-2200.0, -2000.0, 2600.0, 2600.0)


def _wall_face_x(y):
    return WALL_X + 30 * noise1(y / 220.0, 1401) + 0.10 * max(0.0, 760 - y) - 40 * smoothstep((y - 1080) / 80) * 0


def _paint_depths(c):
    X0, Y0, X1, Y1 = _D_BOUNDS
    # back wall of the grotto
    c.drawRect(skia.Rect(X0, Y0, X1, 1100), _G(_lg(0, Y0, 0, 1100, ["#0E0C12", "#2A2634", "#3E3848", "#463F50"],
                                                   [0, 0.4, 0.8, 1])))
    c.save()
    c.clipRect(skia.Rect(X0, -1400, X1, 1120))
    _lumps(c, X0, -1400, X1, 1120, 260, 1411, lambda x, y: 0.45 + 0.12 * noise1(x / 500.0, 5) + 0.1 * clamp((y + 500) / 1500),
           dark="#2A2532", light="#6E6478", aspect=0.65, alpha=0.5, rim=0.2, crease=0.3, density=0.9, var=0.12, warm=0.1)
    _wash_blobs(c, X0, -800, X1, 1100, 16, 1412, ["#8A6A50", "#4E6A44", "#5A6A86"], size=(200, 600), alpha=(0.08, 0.2))
    _recess(c, -420, 640, 520, 700, 1413)
    _recess(c, 1500, 560, 300, 520, 1414)
    rng = np.random.default_rng(1415)
    for k in range(22):
        _root(c, X0 + rng.random() * (X1 - X0), -900 + rng.random() * 500, 200 + 500 * rng.random(), 1420 + k,
              w0=5 + 9 * rng.random(), alpha=0.85)
    c.restore()
    # ceiling with the shaft opening
    cl = [(x, -950 + 90 * _nz(x, 1431)) for x in np.arange(X0, X1 + 40, 40.0)]
    ceil = _poly([(X0, Y0), (X1, Y0)] + cl[::-1])
    c.drawPath(ceil, _G(_lg(0, Y0, 0, -850, ["#0A090E", "#1E1A24", "#2E2A36"])))
    c.drawPath(_poly(cl, close=False), _S("#6E6476", 2.5, 0.3))
    hole = smooth_path([(SHAFT_OPEN_X[0], -930), (SHAFT_OPEN_X[0] + 40, -1150), (SHAFT_OPEN_X[0] + 60, Y0 - 50),
                        (SHAFT_OPEN_X[1] - 50, Y0 - 50), (SHAFT_OPEN_X[1] - 30, -1150), (SHAFT_OPEN_X[1], -930),
                        ((SHAFT_OPEN_X[0] + SHAFT_OPEN_X[1]) / 2, -890)], closed=True)
    c.drawPath(hole, _G(_lg(0, -900, 0, Y0, ["#08070A", "#020203"])))
    c.drawPath(hole, _S(K_INK, 4, 0.8))
    for k in range(9):
        x = X0 + 500 + rng.random() * (X1 - X0 - 1000)
        _stalactite(c, x, -950 + 90 * _nz(x, 1431), 30 + 70 * rng.random(), 90 + 260 * rng.random(), 1440 + k)
    # floor (rubble)
    fl = [(x, 1085 + 14 * _nz(x, 1451)) for x in np.arange(X0, X1 + 40, 40.0)]
    floor = _poly(fl + [(X1, Y1), (X0, Y1)])
    c.drawPath(floor, _G(_lg(0, 1080, 0, Y1, ["#544C5C", "#5E5566", "#4A4352", "#2A2632", "#16141C"],
                             [0, 0.08, 0.25, 0.5, 1])))
    c.save()
    _clip(c, floor)
    _lumps(c, X0, 1060, X1, Y1, 240, 1452, lambda x, y: 0.5 - 0.35 * clamp((y - 1150) / 900) + 0.1 * noise1(x / 400.0, 3),
           dark="#3A3442", light="#8E8494", aspect=0.32, alpha=0.5, rim=0.22, crease=0.3, density=0.85, var=0.12, warm=0.1)
    _wash_blobs(c, X0, 1100, X1, 1600, 18, 1453, ["#8A6A50", "#6A6A7A"], size=(150, 450), alpha=(0.1, 0.22), sy=0.35)
    c.restore()
    c.drawPath(_poly(fl, close=False), _S(K_INK, 18, 0.45, blur=8))
    # rubble heap under the shaft and the impact scar
    rng2 = np.random.default_rng(1461)
    for k in range(30):
        bx = 200 + rng2.random() * 420
        by = 1090 + rng2.random() * 120
        r = 10 + 34 * rng2.random() ** 1.6
        _boulder(c, bx, by, r, r * 0.6, 1470 + k, base=_mixc(K_R3, K_WARM, rng2.random() * 0.4))
    c.drawOval(skia.Rect(250, 1140, 560, 1200), _P(K_INK, 0.25, blur=12))
    for k in range(40):
        x = X0 + rng2.random() * (X1 - X0)
        if 180 < x < 660:
            continue
        r = 8 + 60 * rng2.random() ** 2.5
        _boulder(c, x, 1100 + rng2.random() * 250, r, r * 0.6, 1520 + k, moss=rng2.random() * 0.5)
    _pebbles(c, X0, X1, lambda x: 1090.0, 120, 1530, smin=3, smax=14, yspread=(0, 320))
    # the right wall (lean surface)
    wpts = []
    for yy in np.linspace(-1000, 1110, 40):
        wpts.append((_wall_face_x(yy) + 140 * smoothstep((-200 - yy) / 700), yy))
    wall = _poly(wpts + [(X1, 1110), (X1, -1000)])
    c.drawPath(wall, _P(K_INK, 0.5, blur=30))
    c.drawPath(wall, _G(_lg(WALL_X - 20, 0, WALL_X + 900, 0, ["#6E6478", "#544C5E", "#3E3848", "#26222E"],
                            [0, 0.15, 0.5, 1])))
    c.drawPath(wall, _G(_lg(0, -1000, 0, 1110, [_c(K_INK, 0.6), _c(K_INK, 0.0), _c(K_INK, 0.0), _c(K_INK, 0.3)],
                            [0, 0.45, 0.85, 1])))
    c.save()
    _clip(c, wall)
    _lumps(c, WALL_X - 100, -1000, X1, 1110, 210, 1541, lambda x, y: 0.6 - 0.45 * clamp((x - WALL_X) / 700),
           dark="#2E2A36", light="#9A90A2", aspect=0.75, alpha=0.6, rim=0.3, crease=0.42, density=1.0, var=0.16, warm=0.15)
    _wash_blobs(c, WALL_X, -600, X1, 1100, 8, 1542, ["#4E6A44", "#8A6A50"], size=(150, 400), alpha=(0.1, 0.2))
    # smoother lean patch at shoulder height
    c.drawOval(skia.Rect(WALL_X - 40, 560, WALL_X + 180, 1000), _P("#6E6478", 0.35, blur=20))
    for k in range(6):
        _root(c, WALL_X + 60 + rng2.random() * 600, -950 + rng2.random() * 300, 300 + 400 * rng2.random(), 1550 + k,
              w0=7 + 7 * rng2.random())
    c.restore()
    c.drawPath(_poly(wpts, close=False), _S(K_INK, 4, 0.85))
    c.drawPath(_poly([(x - 4, y) for x, y in wpts], close=False), _S("#B0A4B4", 2.0, 0.35))
    c.drawPath(_poly([(WALL_X - 30, 1112), (X1, 1112)], close=False), _S(K_INK, 20, 0.5, blur=8))
    # formations: a big boulder pile left-centre, stalagmites by the wall, a fallen slab
    _boulder(c, -120, 1080, 210, 150, 1561, base="#5E5668", moss=0.6)
    _boulder(c, 90, 1120, 110, 70, 1562, base="#665E70", moss=0.3)
    _boulder(c, 1250, 1060, 260, 170, 1563, base="#5E5668", moss=0.4)
    for (sx, sy, sw, sh, sd) in ((760, 1110, 70, 260, 1571), (860, 1100, 44, 150, 1572), (1500, 1120, 90, 380, 1573),
                                 (-560, 1110, 80, 300, 1574), (-380, 1100, 40, 140, 1575)):
        _stalagmite(c, sx, sy, sw, sh, sd)
    for k in range(10):
        x = -800 + rng2.random() * 2400
        _root(c, x, -950 + 90 * _nz(x, 1431), 350 + 600 * rng2.random(), 1580 + k, w0=6 + 9 * rng2.random())
    # fungi
    for i, (fx_, fy_, fr) in enumerate(DEP_FUNGI):
        _fungi_patch(c, fx_, fy_, fr, 950 + i)
    # deep shadow on the left (where the voice is)
    c.drawRect(skia.Rect(X0, Y0, DARK_X + 260, Y1), _G(_lg(DARK_X - 520, 0, DARK_X + 260, 0,
                                                            [_c("#050407", 0.97), _c("#050407", 0.8), _c("#050407", 0.0)],
                                                            [0, 0.55, 1])))
    c.drawRect(skia.Rect(X0, Y0, DARK_X - 520, Y1), _P("#050407", 0.97))


@lru_cache(maxsize=1)
def _depths_pic():
    return _record(_D_BOUNDS, _paint_depths)


def draw_depths(canvas, t, dust=0.0, shake=0.0):
    """The bottom grotto (STAGE coords). See module doc."""
    c = canvas
    _blit(c, "depths", _depths_pic, _D_BOUNDS, opaque=True)
    if dust > 0.01:
        # slow hanging dust motes + soft haze near the floor
        for k in range(26):
            per = 9.0 + 5.0 * hash01(k, 1601)
            ph = (t / per + hash01(k, 1602)) % 1.0
            x = -200 + 1300 * hash01(k, 1603) + 40 * math.sin(t * 0.3 + k)
            y = 1150 - 1100 * hash01(k, 1604) + 120 * ph
            a = dust * 0.5 * math.sin(math.pi * ph)
            fx._blob(c, x, y, 3.5, "#C8B8A4", a)
        fx._blob(c, 420, 1100, 520, "#8A8075", 0.25 * dust, kind="puff", ry=140)
    if shake > 0.01:
        for k, (x0, x1) in enumerate(((SHAFT_OPEN_X[0], SHAFT_OPEN_X[1]), (700.0, 1100.0), (-300.0, 100.0))):
            fx.dust_fall(c, t, x0, x1, -930.0, amount=shake, seed=1610 + k, length=2000, size=1.6)


def depths_lights(t, strength=1.0):
    """Dim fungus lights of the depths (stage coords)."""
    if strength <= 0:
        return []
    return [fungus_light(x, y - r * 0.3, t, radius=220 + r * 8, strength=strength, seed=i)
            for i, (x, y, r) in enumerate(DEP_FUNGI)]
