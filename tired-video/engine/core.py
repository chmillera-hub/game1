"""Core drawing + timing helpers shared by every scene and character rig.

All drawing happens in a LOGICAL 1080x1920 portrait space. The renderer
scales the cairo context so the same code renders at any output size.
"""
import math
import cairocffi as cairo

W, H = 1080, 1920
FPS = 24

# Safe zones (logical px). Platform UI (TikTok/Reels/Shorts) covers the
# bottom ~330px and the right ~150px. Keep faces/text out of those.
SAFE_TOP = 120
SAFE_BOTTOM = H - 330
SAFE_RIGHT = W - 150
SAFE_LEFT = 60

# ----------------------------------------------------------------------------
# Palette (shared art direction)
# ----------------------------------------------------------------------------
PAL = {
    # line + neutrals
    "ink": "#1d1626", "white": "#ffffff", "black": "#000000", "shadow": "#1d1626",
    # Tiredness
    "t_skin": "#c08a62", "t_skin_sh": "#a06e4c", "t_hair": "#2e2320", "t_bags": "#8a6a8e",
    "t_hoodie": "#3d4f86", "t_hoodie_dk": "#2c3a66", "t_pants": "#8d8f9a", "t_slipper": "#7fb2e8",
    "t_iris": "#6b4a2e", "headphones": "#e9e9ef", "headphones_dk": "#9a9aa8",
    "polo": "#d9c7a0", "khaki": "#b59a6a",
    # Embarrassment
    "e_skin": "#f7d3bf", "e_skin_sh": "#e2ab94", "e_hair": "#d9793d", "e_coat": "#f4f6f8",
    "e_coat_sh": "#c9d2da", "e_vest": "#4fb3a9", "e_pants": "#5a5f7a", "e_iris": "#5a8f4a",
    "blush": "#ff4f6d", "glasses": "#2b2b38",
    # Boss
    "b_skin": "#f2d6c6", "b_hair": "#e6e8ee", "b_suit": "#2a2d3a", "b_suit_dk": "#1b1d27",
    "b_iris": "#7d8fa3", "b_lip": "#9c3a4a",
    # guard / receptionist
    "g_uniform": "#33415c", "g_skin": "#8a5a3c", "r_skin": "#e8b98f", "r_top": "#7a5ca8",
    # creatures
    "imp_fur": "#f2a93b", "imp_fur_dk": "#cf7f22", "imp_tongue": "#ff7a9a",
    "thing_fur": "#6a4fa0", "thing_dk": "#3f2d6b",
    "spec_body": "#232a52", "spec_dk": "#141833", "spec_glow": "#3ff2e0", "power": "#3ff2e0",
    # HushCorp
    "hush": "#2fd1c5", "hush_dk": "#0f6f6a", "corp_wall": "#dfe6ee", "corp_glass": "#a9c7d8",
    # signals
    "danger": "#ff3b5c", "safe": "#3ddc84", "warn": "#ffb020",
}


def hexc(s, a=1.0):
    """'#rrggbb' -> (r, g, b, a) floats. Accepts tuples unchanged."""
    if isinstance(s, (tuple, list)):
        return tuple(s) if len(s) == 4 else (s[0], s[1], s[2], a)
    s = PAL.get(s, s).lstrip("#")
    return (int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a)


def mixc(c1, c2, t):
    a, b = hexc(c1), hexc(c2)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def alpha(c, a):
    c = hexc(c)
    return (c[0], c[1], c[2], c[3] * a)


# ----------------------------------------------------------------------------
# Math / easing
# ----------------------------------------------------------------------------
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, t0, t1):
    """Progress 0..1 of t through [t0, t1] (clamped)."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def smoothstep(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in(t):
    t = clamp(t); return t * t * t


def ease_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return 1 + t * t * ((s + 1) * t + s)


def ease_out_elastic(t):
    t = clamp(t)
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def ease_out_bounce(t):
    t = clamp(t)
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d; return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d; return n * t * t + 0.9375
    t -= 2.625 / d; return n * t * t + 0.984375


def pop(t, t0, dur=0.35):
    """Scale-in 'pop' factor (0 -> overshoot -> 1) starting at t0."""
    return ease_out_back(seg(t, t0, t0 + dur)) if t >= t0 else 0.0


def tween(t, keys, ease=ease_in_out):
    """Interpolate numeric (or tuple) keyframes [(time, value), ...]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1:
            k = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, (tuple, list)):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]


def state_at(t, keys, trans=0.25):
    """Named-state keyframes [(time, name), ...] -> (prev_name, name, blend 0..1).

    Each key switches to `name` at `time`, blending over `trans` seconds.
    """
    prev, cur, start = keys[0][1], keys[0][1], -1e9
    for (tk, name) in keys:
        if t >= tk:
            prev, cur, start = cur, name, tk
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + trans))


def hash01(i, seed=0):
    """Deterministic pseudo-random float in [0,1) from an int."""
    x = (int(i) * 374761393 + int(seed) * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFFFF) / float(0x1000000)


def noise1(x, seed=0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(i, seed) * 2 - 1
    b = hash01(i + 1, seed) * 2 - 1
    return lerp(a, b, f * f * (3 - 2 * f))


def wobble(t, freq=1.0, amp=1.0, seed=0):
    return noise1(t * freq, seed) * amp


def blink_amount(t, seed=0, rate=0.28, dur=0.16):
    """0 = open, 1 = fully closed. Deterministic natural-looking blinks.

    Roughly `rate` blinks per second with jitter; occasional double blink.
    """
    period = 1.0 / rate
    k = math.floor(t / period)
    out = 0.0
    for j in (k - 1, k):
        start = j * period + hash01(j, seed) * period * 0.7
        for s in ([start, start + 0.28] if hash01(j, seed + 7) < 0.18 else [start]):
            p = (t - s) / dur
            if 0 <= p <= 1:
                out = max(out, math.sin(p * math.pi))
    return out


# ----------------------------------------------------------------------------
# Drawing helpers (all take a cairo context)
# ----------------------------------------------------------------------------
def set_color(ctx, c):
    ctx.set_source_rgba(*hexc(c))


def fill(ctx, c, preserve=False):
    set_color(ctx, c)
    ctx.fill_preserve() if preserve else ctx.fill()


def stroke(ctx, c, width=4, preserve=False, cap="round", join="round"):
    set_color(ctx, c)
    ctx.set_line_width(width)
    ctx.set_line_cap({"round": cairo.LINE_CAP_ROUND, "butt": cairo.LINE_CAP_BUTT,
                      "square": cairo.LINE_CAP_SQUARE}[cap])
    ctx.set_line_join({"round": cairo.LINE_JOIN_ROUND, "miter": cairo.LINE_JOIN_MITER,
                       "bevel": cairo.LINE_JOIN_BEVEL}[join])
    ctx.stroke_preserve() if preserve else ctx.stroke()


def fill_stroke(ctx, fc, sc, width=4):
    if fc is not None:
        fill(ctx, fc, preserve=True)
    if sc is not None:
        stroke(ctx, sc, width, preserve=True)
    ctx.new_path()


def rrect(ctx, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def ellipse(ctx, cx, cy, rx, ry, angle=0.0):
    if rx <= 0 or ry <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    if angle:
        ctx.rotate(angle)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def circle(ctx, cx, cy, r):
    ctx.new_sub_path()
    ctx.arc(cx, cy, max(r, 0.01), 0, 2 * math.pi)


def poly(ctx, pts, closed=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if closed:
        ctx.close_path()


def smooth_path(ctx, pts, closed=False, tension=0.5):
    """Catmull-Rom spline through pts, emitted as cubic beziers."""
    n = len(pts)
    if n < 2:
        return
    if closed:
        P = [pts[-1]] + list(pts) + [pts[0], pts[1]]
    else:
        P = [pts[0]] + list(pts) + [pts[-1]]
    ctx.move_to(*P[1])
    rng = range(1, n + 1) if closed else range(1, n)
    for i in rng:
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def bg(ctx, c):
    set_color(ctx, c)
    ctx.paint()


def vgradient(ctx, c1, c2, x=0, y=0, w=W, h=H):
    g = cairo.LinearGradient(x, y, x, y + h)
    g.add_color_stop_rgba(0, *hexc(c1))
    g.add_color_stop_rgba(1, *hexc(c2))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def radial_glow(ctx, cx, cy, r, c, a=0.5):
    """Soft radial glow. Keep these few and large: gradients cost bitrate."""
    col = hexc(c)
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], a)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.set_source(g)
    circle(ctx, cx, cy, r)
    ctx.fill()


# ----------------------------------------------------------------------------
# Text
# ----------------------------------------------------------------------------
FONTS = {
    "caption": ("Inter", cairo.FONT_WEIGHT_BOLD),        # use 'Inter Black' via family
    "ui": ("Nunito", cairo.FONT_WEIGHT_BOLD),
    "comic": ("Bangers", cairo.FONT_WEIGHT_NORMAL),
    "title": ("Luckiest Guy", cairo.FONT_WEIGHT_NORMAL),
    "round": ("Fredoka", cairo.FONT_WEIGHT_BOLD),
    "mono": ("DejaVu Sans Mono", cairo.FONT_WEIGHT_BOLD),
    "black": ("Inter Black", cairo.FONT_WEIGHT_NORMAL),
}


def set_font(ctx, font="ui", size=40, italic=False):
    fam, wt = FONTS.get(font, (font, cairo.FONT_WEIGHT_BOLD))
    ctx.select_font_face(fam, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL, wt)
    ctx.set_font_size(size)


def text_width(ctx, s, font="ui", size=40):
    set_font(ctx, font, size)
    return ctx.text_extents(s)[4]  # x_advance


def text(ctx, s, x, y, size=40, color="white", font="ui", align="center",
         outline=None, outline_w=8, italic=False, shadow=None):
    """Draw single-line text. y is the BASELINE. align: left|center|right.

    outline: color for a thick outer stroke (great for captions/comic text).
    shadow: (dx, dy, color) drop shadow.
    Returns advance width.
    """
    set_font(ctx, font, size, italic)
    adv = ctx.text_extents(s)[4]
    ox = {"left": 0, "center": -adv / 2, "right": -adv}[align]
    if shadow:
        dx, dy, sc = shadow
        ctx.move_to(x + ox + dx, y + dy)
        ctx.text_path(s)
        if outline:
            stroke(ctx, sc, outline_w, preserve=True)
        fill(ctx, sc)
    ctx.move_to(x + ox, y)
    ctx.text_path(s)
    if outline:
        stroke(ctx, outline, outline_w, preserve=True)
    fill(ctx, color)
    return adv


def wrap_lines(ctx, s, max_w, font="ui", size=40):
    words, lines, cur = s.split(), [], ""
    set_font(ctx, font, size)
    for w in words:
        test = (cur + " " + w).strip()
        if ctx.text_extents(test)[4] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(ctx, s, x, y, max_w, size=40, color="white", font="ui", align="center",
               line_h=1.2, outline=None, outline_w=8, reveal=1.0):
    """Wrapped multi-line text; y = top of block. reveal 0..1 typewriter.

    Returns the block height.
    """
    lines = wrap_lines(ctx, s, max_w, font, size)
    total = sum(len(l) for l in lines)
    budget = int(round(total * clamp(reveal)))
    yy = y + size
    for l in lines:
        shown = l[:max(0, budget)]
        budget -= len(l)
        if shown:
            if align == "left":
                text(ctx, shown, x, yy, size, color, font, "left", outline, outline_w)
            else:
                # keep partially revealed lines anchored like the full line
                full_w = text_width(ctx, l, font, size)
                lx = x - full_w / 2 if align == "center" else x - full_w
                text(ctx, shown, lx, yy, size, color, font, "left", outline, outline_w)
        yy += size * line_h
    return len(lines) * size * line_h


# ----------------------------------------------------------------------------
# Transform helpers
# ----------------------------------------------------------------------------
class saved:
    """with saved(ctx, x, y, scale, rot): ...  -> translate/scale/rotate block."""

    def __init__(self, ctx, x=0, y=0, scale=1.0, rot=0.0, alpha_=None):
        self.ctx, self.x, self.y, self.s, self.r, self.a = ctx, x, y, scale, rot, alpha_

    def __enter__(self):
        self.ctx.save()
        if self.a is not None and self.a < 1:
            self.ctx.push_group()
        self.ctx.save()
        self.ctx.translate(self.x, self.y)
        if self.r:
            self.ctx.rotate(self.r)
        if isinstance(self.s, (tuple, list)):
            self.ctx.scale(self.s[0], self.s[1])
        elif self.s != 1.0:
            self.ctx.scale(self.s, self.s)
        return self.ctx

    def __exit__(self, *a):
        self.ctx.restore()
        if self.a is not None and self.a < 1:
            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(max(0.0, self.a))
        self.ctx.restore()


def fade_group(ctx, a, draw_fn):
    """Draw draw_fn(ctx) composited at opacity a (0..1)."""
    if a <= 0.001:
        return
    if a >= 0.999:
        draw_fn(ctx)
        return
    ctx.push_group()
    draw_fn(ctx)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def shake(t, t0, dur=0.4, amp=14, seed=3):
    """Screen-shake offset (dx, dy) decaying after t0."""
    if t < t0 or t > t0 + dur:
        return (0.0, 0.0)
    k = 1 - (t - t0) / dur
    return (noise1(t * 40, seed) * amp * k, noise1(t * 40, seed + 9) * amp * k)


class camera:
    """with camera(ctx, cx, cy, zoom, rot, sx, sy): draw in WORLD coordinates.

    World point (cx, cy) lands on screen point (sx, sy) (default: frame
    centre) at `zoom`x, rotated by `rot` radians around it. Sets larger than
    the frame (e.g. a 2400 px wide bedroom) are drawn once in world space and
    framed by moving the camera.
    """
    def __init__(self, ctx, cx, cy, zoom=1.0, rot=0.0, sx=W / 2, sy=H / 2):
        self.ctx, self.a = ctx, (cx, cy, zoom, rot, sx, sy)

    def __enter__(self):
        cx, cy, zoom, rot, sx, sy = self.a
        c = self.ctx
        c.save()
        c.translate(sx, sy)
        if rot:
            c.rotate(rot)
        c.scale(zoom, zoom)
        c.translate(-cx, -cy)
        return c

    def __exit__(self, *a):
        self.ctx.restore()


# ----------------------------------------------------------------------------
# Static-layer cache: draw an expensive, unchanging drawing once per process
# (per device scale) and blit it every frame.
# ----------------------------------------------------------------------------
from collections import OrderedDict as _OD

_LAYERS = _OD()
_LAYERS_MAX = 24
_Q_STEPS = [8]   # cache resolution steps per octave (see cache_steps)


def cached(ctx, key, x0, y0, w, h, draw_fn, pad=4):
    """Blit `draw_fn(ctx)` (drawn in the CURRENT user coordinates, inside the
    rect x0, y0, w, h) from a cached bitmap rendered at the current device
    scale. `key` must change whenever the drawing would change (include any
    state such as damage level). Scale is quantised to 1/8-octave steps
    (rendered at the step above, so never blurry), which keeps slow camera
    zooms from re-rendering every frame. Rotation in the CTM is fine.
    """
    m = ctx.get_matrix()
    sc = math.hypot(m.xx, m.yx)
    if sc <= 0:
        return
    n = _Q_STEPS[-1]
    q = 2 ** (math.ceil(math.log2(sc) * n - 1e-6) / n)
    k = (key, round(q, 5), w, h)
    surf = _LAYERS.get(k)
    if surf is None:
        sw, sh = int(math.ceil((w + 2 * pad) * q)), int(math.ceil((h + 2 * pad) * q))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, sw), max(1, sh))
        c = cairo.Context(surf)
        c.scale(q, q)
        c.translate(-(x0 - pad), -(y0 - pad))
        draw_fn(c)
        surf.flush()
        _LAYERS[k] = surf
        while len(_LAYERS) > _LAYERS_MAX:
            _LAYERS.popitem(last=False)
    else:
        _LAYERS.move_to_end(k)
    ctx.save()
    ctx.translate(x0 - pad, y0 - pad)
    ctx.scale(1 / q, 1 / q)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.rectangle(0, 0, surf.get_width(), surf.get_height())
    ctx.fill()
    ctx.restore()


class cache_steps:
    """with cache_steps(1): ... -> coarser cache resolution steps (per octave)
    for big camera zoom moves, so cached sets re-render only once per octave
    (rendered at the step above, i.e. never blurry, at most 2x oversampled)."""
    def __init__(self, n=1):
        self.n = max(1, int(n))

    def __enter__(self):
        _Q_STEPS.append(self.n)

    def __exit__(self, *a):
        _Q_STEPS.pop()
