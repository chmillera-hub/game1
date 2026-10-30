"""Shared helpers: timeline access, easing, keyframes, noise, colour, shading."""
import json, math, os
import cairo

W, H = 720, 1280
BUILD = os.environ.get("CZ_BUILD", "/tmp/claude-0/cz")
TL = json.load(open(f"{BUILD}/timeline.json"))
FPS = TL["fps"]
DUR = TL["duration"]
LINES = TL["lines"]
SCENES = {s["id"]: (s["t0"], s["t1"]) for s in TL["scenes"]}


# ---------------------------------------------------------------- time / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, k):
    if isinstance(a, (tuple, list)):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease2(x):  # softer in/out
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def ramp(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return ease((t - t0) / (t1 - t0))


def kf(t, keys, fn=ease):
    """keys: [(time, value), ...] sorted. Eased interpolation, held at ends."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(v0, v1, fn((t - t0) / max(1e-6, t1 - t0)))
    return keys[-1][1]


def sn(t, seed=0.0, f=1.0):
    """Smooth deterministic noise in [-1, 1]."""
    s = seed * 12.9898
    return (math.sin(t * f * 1.13 + s) * 0.5 + math.sin(t * f * 2.31 + s * 1.7) * 0.3
            + math.sin(t * f * 0.57 + s * 2.3) * 0.2)


def hsh(i, k=0):
    """Deterministic hash -> [0, 1)."""
    x = math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return x - math.floor(x)


# ---------------------------------------------------------------- timeline
def L(lid):
    d = LINES[lid]
    return d["t0"], d["t1"]


def at(lid, frac):
    """Time at a fraction through a line (for syncing actions to words)."""
    t0, t1 = L(lid)
    return t0 + (t1 - t0) * frac


def word_t(lid, word, nth=0):
    """Approximate time a word is spoken (proportional by characters)."""
    d = LINES[lid]
    txt = d["text"]
    i = -1
    for _ in range(nth + 1):
        i = txt.find(word, i + 1)
    if i < 0:
        return d["t0"]
    return d["t0"] + (d["t1"] - d["t0"]) * (i / max(1, len(txt)))


def mouth(spk, t):
    """(open, wide) lip-sync values for speaker at time t."""
    for lid in TL["order"]:
        d = LINES[lid]
        if d["spk"] != spk:
            continue
        if d["t0"] - 0.05 <= t <= d["t1"] + 0.1:
            i = int((t - d["t0"]) * FPS)
            if 0 <= i < len(d["env"]):
                return d["env"][i], d["wide"][i]
            return 0.0, 0.0
    return 0.0, 0.0


def speaking(spk, t, pad=0.0):
    for lid in TL["order"]:
        d = LINES[lid]
        if d["spk"] == spk and d["t0"] - pad <= t <= d["t1"] + pad:
            return True
    return False


_BLINKS = {}


def blink(t, seed=1):
    """Eyelid closure 0..1 from a natural blink schedule."""
    if seed not in _BLINKS:
        ts, x = [], 0.7 + hsh(seed) * 1.5
        k = 0
        while x < DUR + 10:
            ts.append(x)
            k += 1
            x += 2.3 + hsh(seed, k) * 3.2
        _BLINKS[seed] = ts
    for b in _BLINKS[seed]:
        if b - 0.01 <= t <= b + 0.2:
            u = t - b
            return clamp(u / 0.06) if u < 0.06 else clamp(1 - (u - 0.07) / 0.12)
        if b > t:
            break
    return 0.0


# ---------------------------------------------------------------- colour
def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def mul(c, k):
    return tuple(clamp(x * k) for x in c)


def tint(c, light):
    """Gentle scene grading: multiply + small mix toward ambient."""
    amb, k = light["amb"], light.get("amb_k", 0.12)
    m = tuple(x * (0.82 + 0.18 * y) for x, y in zip(c, amb))
    return mix(m, amb, k)


# ---------------------------------------------------------------- paths
def smooth_closed(ctx, pts, tension=1.0):
    """Closed Catmull-Rom spline through pts."""
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        ctx.curve_to(*c1, *c2, *p2)
    ctx.close_path()


def smooth_open(ctx, pts, move=True):
    n = len(pts)
    if move:
        ctx.move_to(*pts[0])
    else:
        ctx.line_to(*pts[0])
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[0]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(*c1, *c2, *p2)


def capsule(ctx, p0, p1, r0, r1):
    """Tapered capsule from p0 (radius r0) to p1 (radius r1)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy) or 1e-6
    a = math.atan2(dy, dx)
    # tangent offset for tapered sides
    s = clamp((r0 - r1) / d, -0.99, 0.99)
    b = math.acos(s)
    ctx.new_sub_path()
    ctx.arc(p0[0], p0[1], r0, a + b, a - b + 2 * math.pi)
    ctx.arc(p1[0], p1[1], r1, a - b, a + b)
    ctx.close_path()


def ellipse(ctx, x, y, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(max(rx, 1e-3), max(ry, 1e-3))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def soft_dot(ctx, x, y, r, col, a):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, a)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.rectangle(x - r, y - r, 2 * r, 2 * r)
    ctx.fill()


def rgba(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def shade(ctx, path, base, light, lw, outline=True, shadow=0.38, rim=0.85, rim_w=3.0, outline_col=None, union=False):
    """Fill a path with base colour, soft form shadow away from light, rim light toward it.
    union=True: outline drawn as one silhouette around overlapping sub-shapes (no inner seams)."""
    if union:
        ctx.new_path()
        path()
        rgba(ctx, outline_col or light.get("line", (0.1, 0.08, 0.1)), 0.9)
        ctx.set_line_width(lw * 2)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
        outline = False
    ctx.new_path()
    path()
    x0, y0, x1, y1 = ctx.path_extents()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = max(x1 - x0, y1 - y0) / 2 + 1e-3
    lx, ly = light["dir"]
    rgba(ctx, tint(base, light))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    g = cairo.LinearGradient(cx + lx * r, cy + ly * r, cx - lx * r, cy - ly * r)
    sc = light["shadow"]
    g.add_color_stop_rgba(0, *sc, 0)
    g.add_color_stop_rgba(0.45, *sc, shadow * 0.25)
    g.add_color_stop_rgba(1, *sc, shadow)
    ctx.set_source(g)
    ctx.fill_preserve()
    if rim > 0:
        g = cairo.LinearGradient(cx + lx * r, cy + ly * r, cx, cy)
        rc = light["rim"]
        g.add_color_stop_rgba(0, *rc, rim)
        g.add_color_stop_rgba(0.55, *rc, 0)
        ctx.set_source(g)
        ctx.set_line_width(lw * rim_w * 2)
        ctx.stroke_preserve()
    ctx.restore()
    if outline:
        rgba(ctx, outline_col or light.get("line", (0.1, 0.08, 0.1)), 0.9)
        ctx.set_line_width(lw)
        ctx.stroke()
    ctx.new_path()


def soft_stroke(ctx, pts, col, a, w, smooth=True):
    """Soft anatomical / fold line: wide faint stroke + thinner core."""
    for k, ww in ((0.35, w * 2.2), (1.0, w)):
        ctx.new_path()
        if smooth:
            smooth_open(ctx, pts)
        else:
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
        rgba(ctx, col, a * k)
        ctx.set_line_width(ww)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


# default light rigs (scene code copies + tweaks)
LIGHT_DUSK_FRONT = dict(dir=(-0.35, -0.94), rim=hexc("ffb070"), shadow=hexc("2a2040"),
                        amb=hexc("8c7f9e"), amb_k=0.10, line=hexc("1c1520"))
