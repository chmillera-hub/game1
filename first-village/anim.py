"""Animation math, colour and skia drawing helpers shared by the renderer."""
import math
import os

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 720, 1280, 24


# ---------------------------------------------------------------- math / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ramp(t, t0, t1, f=smooth):
    """0 before t0, 1 after t1, eased in between."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return f((t - t0) / (t1 - t0))


def window(t, t0, t1, fin=0.3, fout=0.3):
    """1 inside [t0, t1] with soft edges."""
    return ramp(t, t0, t0 + fin) * (1 - ramp(t, t1 - fout, t1))


def noise(t, seed=0, freq=1.0):
    """Smooth pseudo-noise in about [-1, 1]."""
    s = seed * 12.9898
    return (math.sin(t * freq * 1.0 + s) * 0.5 + math.sin(t * freq * 2.31 + s * 1.7) * 0.3
            + math.sin(t * freq * 4.73 + s * 2.3) * 0.2)


def hashf(*a):
    """Deterministic float in [0, 1) from ints/floats."""
    x = 0
    for v in a:
        x = (x * 1000003 + int(v * 1000)) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5bd1e995) & 0xFFFFFFFF
    x ^= x >> 15
    return (x & 0xFFFFFF) / float(0x1000000)


class Track:
    """Keyframed value: [(time, value), ...], eased between keys. Values may be tuples."""

    def __init__(self, keys, f=smooth):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.f = f

    def __call__(self, t):
        k = self.keys
        if t <= k[0][0]:
            return k[0][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t <= t1:
                u = self.f((t - t0) / (t1 - t0)) if t1 > t0 else 1
                if isinstance(v0, tuple):
                    return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
                return lerp(v0, v1, u)
        return k[-1][1]


# ---------------------------------------------------------------- colour
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mixc(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


def shade(c, k):
    """k<1 darker, k>1 lighter (towards white)."""
    if k <= 1:
        return tuple(v * k for v in c)
    return tuple(v + (255 - v) * (k - 1) for v in c)


def C(c, a=1.0):
    if isinstance(c, str):
        c = rgb(c)
    return skia.ColorSetARGB(int(clamp(a) * 255), int(clamp(c[0], 0, 255)), int(clamp(c[1], 0, 255)),
                             int(clamp(c[2], 0, 255)))


def paint(c=(0, 0, 0), a=1.0, stroke=None, cap="round", blur=None, blend=None, shader=None, join="round"):
    p = skia.Paint(AntiAlias=True)
    p.setColor(C(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin({"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join}[join])
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend:
        p.setBlendMode({"plus": skia.BlendMode.kPlus, "screen": skia.BlendMode.kScreen,
                        "multiply": skia.BlendMode.kMultiply, "overlay": skia.BlendMode.kOverlay,
                        "softlight": skia.BlendMode.kSoftLight, "color": skia.BlendMode.kColor,
                        "srcin_fix": skia.BlendMode.kSrcIn,
                        "srcatop": skia.BlendMode.kSrcATop}[blend])
    if shader is not None:
        p.setShader(shader)
    return p


def _col(c):
    """colour or (colour, alpha)"""
    if isinstance(c, tuple) and len(c) == 2:
        return C(c[0], c[1])
    return C(c)


def lin(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [_col(c) for c in cols], pos)


def rad(center, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), max(r, 0.01), [_col(c) for c in cols], pos)


def glow(cv, x, y, r, c, a=1.0, blend="plus"):
    """Soft radial light."""
    if r <= 0 or a <= 0:
        return
    sh = rad((x, y), r, [(c, a), (c, a * 0.35), (c, 0.0)], [0, 0.35, 1])
    cv.drawCircle(x, y, r, paint(shader=sh, blend=blend))


# ---------------------------------------------------------------- paths
def path(points, closed=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def spline(points, closed=True, tension=0.5):
    """Smooth closed/open curve through points (Catmull-Rom -> cubic)."""
    p = skia.Path()
    n = len(points)
    p.moveTo(*points[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = points[(i - 1) % n] if closed or i > 0 else points[i]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if closed or i + 2 < n else p2
        k = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


# ---------------------------------------------------------------- text
_fonts = {}


def font(name, size, weight=None):
    key = (name, size, weight)
    if key not in _fonts:
        files = {"title": "Cinzel[wght].ttf", "serif": "CormorantGaramond[wght].ttf",
                 "italic": "CormorantGaramond-Italic[wght].ttf"}
        tf = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", files[name]))
        if weight:
            VP = skia.FontArguments.VariationPosition
            vp = VP(VP.Coordinates([VP.Coordinate(0x77676874, weight)]))  # 'wght'
            fa = skia.FontArguments()
            fa.setVariationDesignPosition(vp)
            tf = tf.makeClone(fa)
        f = skia.Font(tf, size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _fonts[key] = f
    return _fonts[key]


def text_w(s, f):
    return f.measureText(s)


def wrap(s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(t, f) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines
