"""Skia drawing helpers, colors, easing, keyframes."""
import math, os
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920  # authoring space


# ------------------------------------------------------------------ color
def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255, g / 255, b / 255, a)


def C(c):
    if isinstance(c, str):
        c = hexc(c)
    if len(c) == 3:
        c = (*c, 1.0)
    return skia.Color4f(*[float(x) for x in c])


def mixc(a, b, t):
    a = hexc(a) if isinstance(a, str) else a
    b = hexc(b) if isinstance(b, str) else b
    if len(a) == 3: a = (*a, 1.0)
    if len(b) == 3: b = (*b, 1.0)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def shade(c, k):
    """k<1 darker, k>1 lighter (towards white)."""
    c = hexc(c) if isinstance(c, str) else c
    if len(c) == 3: c = (*c, 1.0)
    if k <= 1:
        return (c[0] * k, c[1] * k, c[2] * k, c[3])
    t = k - 1
    return (c[0] + (1 - c[0]) * t, c[1] + (1 - c[1]) * t, c[2] + (1 - c[2]) * t, c[3])


def alpha(c, a):
    c = hexc(c) if isinstance(c, str) else c
    return (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1.0) * a)


# ------------------------------------------------------------------ paints
def fill(c, aa=True):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(C(c))
    return p


def stroke(c, w, cap="round"):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=float(w))
    p.setColor4f(C(c))
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def lin_grad(p0, p1, colors, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                               [C(c).toColor() for c in colors], pos))
    return p


def rad_grad(c, r, colors, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(*c), float(max(r, 0.01)),
                                               [C(c2).toColor() for c2 in colors], pos))
    return p


# ------------------------------------------------------------------ paths
def path_poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_closed(pts, tension=0.5):
    """Closed Catmull-Rom through pts as cubic beziers."""
    p = skia.Path()
    n = len(pts)
    p.moveTo(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        p.cubicTo(*c1, *c2, *p2)
    p.close()
    return p


def smooth_open(pts, tension=0.5):
    p = skia.Path()
    n = len(pts)
    p.moveTo(*pts[0])
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        p.cubicTo(*c1, *c2, *p2)
    return p


def ellipse(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p


def quad_path(p0, c, p1):
    p = skia.Path()
    p.moveTo(*p0)
    p.quadTo(*c, *p1)
    return p


def draw_outlined(cv, path, col, outline=None, ow=4.0):
    cv.drawPath(path, fill(col))
    if outline is not None and ow > 0:
        cv.drawPath(path, stroke(outline, ow))


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_back(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def ramp(t, t0, t1, ease=smooth):
    if t1 <= t0:
        return 1.0 if t >= t0 else 0.0
    return ease((t - t0) / (t1 - t0))


def wobble(t, seed=0, freq=0.5, octaves=3):
    """Smooth pseudo-noise in [-1,1]."""
    v = 0.0
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        ph = (seed * 12.9898 + o * 78.233) % 6.283
        ph2 = (seed * 4.1414 + o * 3.7) % 6.283
        v += amp * (math.sin(t * freq * (1.7 ** o) * 6.283 + ph) * 0.6 + math.sin(t * freq * (1.7 ** o) * 4.1 + ph2) * 0.4)
        tot += amp
        amp *= 0.5
    return v / tot


# ------------------------------------------------------------------ keyframes
class Track:
    """Hold-and-transition keys: key(t, value, dur) -> from t, move from previous to value over dur."""

    def __init__(self, v0, dur=0.35, ease=ease_io):
        self.keys = [(-1e9, v0, 0.0, ease)]
        self.default_dur = dur
        self.default_ease = ease

    def key(self, t, v, dur=None, ease=None):
        self.keys.append((t, v, self.default_dur if dur is None else dur, ease or self.default_ease))
        self.keys.sort(key=lambda k: k[0])
        return self

    def __call__(self, t):
        prev = self.keys[0][1]
        for (kt, kv, kd, ke) in self.keys[1:]:
            if t < kt:
                break
            if kd <= 0 or t >= kt + kd:
                prev = kv
            else:
                prev = blend(prev, kv, ke((t - kt) / kd))
                # later keys can't have started yet (sorted), but allow overlap chaining
        return prev


def blend(a, b, t):
    if isinstance(a, dict) or isinstance(b, dict):
        a = a or {}
        b = b or {}
        out = {}
        for k in set(a) | set(b):
            va = a.get(k, DEFAULTS_FACE.get(k, 0.0))
            vb = b.get(k, DEFAULTS_FACE.get(k, 0.0))
            out[k] = blend(va, vb, t)
        return out
    if isinstance(a, (tuple, list)):
        return tuple(blend(x, y, t) for x, y in zip(a, b))
    if isinstance(a, str) or isinstance(b, str):
        return b if t > 0.5 else a
    return a + (b - a) * t


DEFAULTS_FACE = {}  # filled by rig


# ------------------------------------------------------------------ text
_FONTS = {}


def font(name, size):
    if name not in _FONTS:
        _FONTS[name] = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", name))
    f = skia.Font(_FONTS[name], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_width(txt, f):
    return f.measureText(txt)


def wrap_text(txt, f, maxw):
    words = txt.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_center(cv, txt, x, y, f, col, outline=None, ow=0):
    w = text_width(txt, f)
    if outline:
        p = stroke(outline, ow)
        cv.drawString(txt, x - w / 2, y, f, p)
    cv.drawString(txt, x - w / 2, y, f, fill(col))
