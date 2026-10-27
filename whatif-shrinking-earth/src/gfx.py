"""Small drawing helpers on top of skia-python."""
import math

import numpy as np
import skia


def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], np.float32)


def mix(h1, h2, t, a=1.0):
    c = rgb(h1) * (1 - t) + rgb(h2) * t
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(1, a)) * 255))


def mixhex(h1, h2, t):
    c = rgb(h1) * (1 - t) + rgb(h2) * t
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in c)


def fill(color, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kFill_Style)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(color, width, cap="round", blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def path_poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_path(pts, close=True, tension=0.5):
    """Catmull-Rom spline through points as cubic Beziers."""
    n = len(pts)
    p = skia.Path()
    if n < 2:
        return p
    pts = [tuple(map(float, q)) for q in pts]
    p.moveTo(*pts[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        k = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if close:
        p.close()
    return p


def ellipse_path(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def circle(c, x, y, r, color, blur=0.0):
    c.drawCircle(x, y, r, fill(color, blur))


def tapered_stroke(pts, w0, w1, wmid=None):
    """Polygon around a polyline whose width goes w0 -> (wmid) -> w1."""
    pts = np.asarray(pts, np.float64)
    n = len(pts)
    t = np.linspace(0, 1, n)
    if wmid is None:
        widths = w0 + (w1 - w0) * t
    else:
        widths = np.where(t < 0.5, w0 + (wmid - w0) * t * 2, wmid + (w1 - wmid) * (t - 0.5) * 2)
    d = np.gradient(pts, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    left = pts + nrm * widths[:, None] / 2
    right = pts - nrm * widths[:, None] / 2
    poly = np.concatenate([left, right[::-1]], 0)
    return smooth_path([tuple(q) for q in poly], close=True, tension=0.3)


def quad_pts(a, b, ctrl, n=16):
    t = np.linspace(0, 1, n)[:, None]
    a, b, ctrl = np.array(a), np.array(b), np.array(ctrl)
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * ctrl + t ** 2 * b


def cubic_pts(a, c1, c2, b, n=20):
    t = np.linspace(0, 1, n)[:, None]
    a, c1, c2, b = map(np.array, (a, c1, c2, b))
    return (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * b


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smoothstep(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def ease_io(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_back(t, s=1.4):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def rot(x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return x * c - y * s, x * s + y * c


def linear_shader(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], colors, pos)


def radial_shader(center, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), r, colors, pos)


def glow(c, x, y, r, color_hex, alpha=0.6, layers=((1.0, 1.0), (0.55, 0.6), (0.25, 0.35))):
    """Soft radial glow made of a radial gradient."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((x, y), r, [hexc(color_hex, alpha), hexc(color_hex, alpha * 0.35),
                                          hexc(color_hex, 0.0)], [0.0, 0.35, 1.0]))
    c.drawCircle(x, y, r, p)


_FONTS = {}


def font(size, weight="bold", family="Inter", italic=False):
    key = (size, weight, family, italic)
    if key not in _FONTS:
        wmap = {"regular": skia.FontStyle.kNormal_Weight, "medium": 500, "semibold": 600,
                "bold": skia.FontStyle.kBold_Weight, "extrabold": 800, "black": 900}
        slant = skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant
        st = skia.FontStyle(wmap.get(weight, 700), skia.FontStyle.kNormal_Width, slant)
        tf = skia.Typeface(family, st)
        f = skia.Font(tf, size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _FONTS[key] = f
    return _FONTS[key]


def text_width(s, f):
    return f.measureText(s)


def draw_text(c, s, x, y, f, color, align="center", outline=None, outline_w=0.0, shadow=None):
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow is not None:
        c.drawString(s, x + shadow[0], y + shadow[1], f, fill(shadow[2], shadow[3] if len(shadow) > 3 else 0))
    if outline is not None and outline_w > 0:
        p = stroke(outline, outline_w)
        c.drawString(s, x, y, f, p)
    c.drawString(s, x, y, f, fill(color))
    return w


class Rng:
    """Deterministic noise helpers (so every render of a frame is identical)."""

    def __init__(self, seed):
        self.r = np.random.default_rng(seed)

    def u(self, a=0.0, b=1.0, n=None):
        return self.r.uniform(a, b, n)


def vnoise1(t, seed=0):
    """Smooth 1-D value noise in [-1, 1]."""
    i = math.floor(t)
    f = t - i

    def h(k):
        x = math.sin((k + seed * 131.7) * 12.9898) * 43758.5453
        return (x - math.floor(x)) * 2 - 1

    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def fbm1(t, seed=0, oct=3):
    v, a, s = 0.0, 0.5, 1.0
    for k in range(oct):
        v += a * vnoise1(t * s, seed + k * 7)
        a *= 0.5
        s *= 2.0
    return v
