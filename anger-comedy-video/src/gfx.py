"""Small skia helpers: colors, paints, shapes."""
import math
import skia


def rgb(c, a=1.0):
    """c is (r,g,b) 0-255 tuple or '#rrggbb'."""
    if isinstance(c, str):
        c = c.lstrip('#')
        c = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(1, a)) * 255))


def hx(c):
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


def shade(c, f):
    """f<1 darker, f>1 lighter (towards white)."""
    if f <= 1:
        return tuple(v * f for v in c)
    return mix(c, (255, 255, 255), f - 1)


def fill(c, a=1.0, blur=0):
    p = skia.Paint(Color=rgb(c, a), AntiAlias=True)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(c, w, a=1.0, cap='round', blur=0):
    p = skia.Paint(Color=rgb(c, a), AntiAlias=True, Style=skia.Paint.kStroke_Style,
                   StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == 'round' else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(l, t, r, b, rad):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, r, b), rad, rad))
    return p


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def superellipse(cx, cy, a, b, n=2.0, jaw=0.0, top_flat=0.0, steps=72):
    """Rounded head shape. jaw narrows the lower half, top_flat flattens the crown."""
    pts = []
    for i in range(steps):
        th = 2 * math.pi * i / steps
        c, s = math.cos(th), math.sin(th)
        x = a * math.copysign(abs(c) ** (2.0 / n), c)
        y = b * math.copysign(abs(s) ** (2.0 / n), s)
        if y > 0:
            x *= 1 - jaw * (y / b) ** 2
        elif top_flat:
            y = y * (1 - top_flat) + (-b) * top_flat * (abs(s) ** 6) * 0 + y * 0
        pts.append((cx + x, cy + y))
    return poly(pts)


def lin_grad(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear(
        points=[skia.Point(*p0), skia.Point(*p1)],
        colors=[rgb(c, a) for c, a in colors], positions=pos)


def rad_grad(c, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(
        center=skia.Point(*c), radius=r,
        colors=[rgb(cc, a) for cc, a in colors], positions=pos)


_tf_cache = {}


def font(name='Inter-Bold', size=40):
    if name not in _tf_cache:
        from common import FONT_DIR
        _tf_cache[name] = skia.Typeface.MakeFromFile(f"{FONT_DIR}/{name}.otf")
    f = skia.Font(_tf_cache[name], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def hash01(*args):
    """Deterministic pseudo-random in [0,1)."""
    h = 0
    for a in args:
        h = (h * 1000003) ^ int(a * 1000 + 7919) & 0xFFFFFFFF
        h &= 0xFFFFFFFF
    h ^= (h >> 13)
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    h ^= (h >> 15)
    return (h & 0xFFFFFF) / float(0x1000000)


def noise1(t, seed=0.0):
    """Smooth 1D value noise in [-1,1]."""
    i = math.floor(t)
    f = t - i
    a = hash01(i, seed) * 2 - 1
    b = hash01(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u
