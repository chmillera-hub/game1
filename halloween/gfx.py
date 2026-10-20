"""Small drawing toolkit on top of skia-python.

Everything here is resolution independent: callers draw in world units and
the camera (see Camera) maps world -> 1080x1920 frame pixels.
"""
import math
import os
import random

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")
W, H = 1080, 1920

# ------------------------------------------------------------------ palette
NIGHT_DEEP = (8, 9, 22)
NIGHT_BLUE = (20, 26, 56)
NIGHT_TEAL = (22, 50, 64)
MOON = (240, 241, 214)
MOON_GLOW = (150, 190, 215)
PUMPKIN = (255, 126, 22)
PUMPKIN_DARK = (170, 60, 12)
CANDLE = (255, 200, 96)
PAPER = (238, 232, 216)
PAPER_SHADE = (196, 196, 206)
GRAPHITE = (40, 40, 50)
INK = (14, 12, 20)


def rgba(c, a=1.0):
    if len(c) == 4:
        return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, c[3] * a))))
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, 255 * a))))


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def scale_col(c, k):
    return tuple(max(0, min(255, v * k)) for v in c[:3])


# ------------------------------------------------------------------ easing / math
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def back_out(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ramp(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def noise1(x, seed=0):
    """Cheap smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i

    def h(n):
        n = (n * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 32767.5 - 1.0

    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def rng(*key):
    return random.Random(hash(key) & 0xFFFFFFFF)


# ------------------------------------------------------------------ fonts
_TF = {}


def typeface(name):
    if name not in _TF:
        _TF[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return _TF[name]


def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


# ------------------------------------------------------------------ paints
def fill(color, a=1.0, shader=None, blend=None, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=rgba(color, a))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    if blend is not None:
        p.setBlendMode(blend)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(color, width, a=1.0, cap="round", effect=None, blur=0.0, blend=None):
    p = skia.Paint(AntiAlias=True, Color=rgba(color, a), Style=skia.Paint.kStroke_Style,
                   StrokeWidth=width)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if effect is not None:
        p.setPathEffect(effect)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def wobble(seg=9.0, dev=1.2, seed=0):
    return skia.DiscretePathEffect.Make(seg, dev, int(seed) & 0x7FFFFFFF)


def lin_grad(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                          [rgba(c) if len(c) == 3 else rgba(c[:3], c[3]) for c in colors], pos)


def rad_grad(center, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), max(r, 0.01),
                                          [rgba(c) if len(c) == 3 else rgba(c[:3], c[3]) for c in colors], pos)


# ------------------------------------------------------------------ paths
def poly(points, closed=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    if closed:
        p.close()
    return p


def smooth_path(points, closed=True, tension=1.0):
    """Catmull-Rom spline through points -> cubic Bezier path."""
    n = len(points)
    p = skia.Path()
    if n < 2:
        return p
    p.moveTo(*points[0])
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0 = points[(i - 1) % n] if (closed or i > 0) else points[i]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else p2
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        p.close()
    return p


def ellipse(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def circle(cx, cy, r):
    return ellipse(cx, cy, r, r)


def rounded_poly(points, radius):
    """Polygon with rounded corners (quadratic fillets)."""
    n = len(points)
    p = skia.Path()
    for i in range(n):
        a = points[i - 1]
        b = points[i]
        c = points[(i + 1) % n]
        da = math.hypot(a[0] - b[0], a[1] - b[1])
        dc = math.hypot(c[0] - b[0], c[1] - b[1])
        r = min(radius, da / 2.1, dc / 2.1)
        p_in = (b[0] + (a[0] - b[0]) * r / da, b[1] + (a[1] - b[1]) * r / da)
        p_out = (b[0] + (c[0] - b[0]) * r / dc, b[1] + (c[1] - b[1]) * r / dc)
        if i == 0:
            p.moveTo(*p_in)
        else:
            p.lineTo(*p_in)
        p.quadTo(b[0], b[1], p_out[0], p_out[1])
    p.close()
    return p


def spiral_pts(cx, cy, r0, r1, turns, a0=0.0, n=60, direction=1):
    pts = []
    for i in range(n + 1):
        t = i / n
        a = a0 + direction * t * turns * 2 * math.pi
        r = r0 + (r1 - r0) * t
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def open_path(points):
    return smooth_path(points, closed=False)


def bezier_pts(p0, p1, p2, n=12):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def trim(path, t0, t1):
    """Sub-path from fraction t0..t1 of total length (multi-contour aware)."""
    pm = skia.PathMeasure(path, False, 1.0)
    lens = []
    while True:
        lens.append(pm.getLength())
        if not pm.nextContour():
            break
    total = sum(lens)
    out = skia.Path()
    if total <= 0:
        return out
    a, b = t0 * total, t1 * total
    pm = skia.PathMeasure(path, False, 1.0)
    acc = 0.0
    for L in lens:
        s, e = max(a - acc, 0), min(b - acc, L)
        if e > s:
            pm.getSegment(s, e, out, True)
        acc += L
        pm.nextContour()
    return out


# ------------------------------------------------------------------ pencil look
def pencil(c, path, width=3.0, color=GRAPHITE, a=1.0, seed=0, rough=1.0, double=True):
    """Graphite line: two jittered passes."""
    c.drawPath(path, stroke(color, width, a * 0.92, effect=wobble(8.0, 0.9 * rough, seed)))
    if double:
        c.drawPath(path, stroke(color, width * 0.55, a * 0.55, effect=wobble(11.0, 1.6 * rough, seed + 101)))


class Xf:
    """with Xf(c, tx, ty, rot=deg, sx=, sy=): ..."""

    def __init__(self, c, tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=None, alpha=None):
        self.c, self.tx, self.ty, self.rot, self.sx = c, tx, ty, rot, sx
        self.sy = sx if sy is None else sy
        self.alpha = alpha

    def __enter__(self):
        if self.alpha is not None and self.alpha < 0.999:
            self.c.saveLayerAlpha(None, int(255 * clamp(self.alpha)))
        else:
            self.c.save()
        self.c.translate(self.tx, self.ty)
        if self.rot:
            self.c.rotate(self.rot)
        if self.sx != 1.0 or self.sy != 1.0:
            self.c.scale(self.sx, self.sy)
        return self.c

    def __exit__(self, *a):
        self.c.restore()


class Camera:
    """World -> screen. (cx, cy) world point at frame centre, zoom, roll in degrees."""

    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, roll=0.0):
        self.cx, self.cy, self.zoom, self.roll = cx, cy, zoom, roll

    def apply(self, c, parallax=1.0):
        c.translate(W / 2, H / 2)
        if self.roll:
            c.rotate(self.roll)
        z = 1.0 + (self.zoom - 1.0) * parallax
        c.scale(z, z)
        c.translate(-(W / 2 + (self.cx - W / 2) * parallax), -(H / 2 + (self.cy - H / 2) * parallax))


def glow(c, x, y, r, color, a=1.0, blend=skia.BlendMode.kScreen):
    c.drawCircle(x, y, r, fill(color, 1.0, rad_grad((x, y), r, [(*color, a), (*color, a * 0.35), (*color, 0.0)],
                                                     [0.0, 0.4, 1.0]), blend=blend))


def text_center(c, s, x, y, f, color, a=1.0, outline=None, outline_w=0.0):
    w = f.measureText(s)
    if outline is not None and outline_w > 0:
        c.drawString(s, x - w / 2, y, f, stroke(outline, outline_w, a))
    c.drawString(s, x - w / 2, y, f, fill(color, a))
    return w
