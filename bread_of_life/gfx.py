"""Small drawing toolkit on top of skia-python."""
import math

import numpy as np
import skia


def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    return (r, g, b, a)


def mix(c1, c2, t):
    c1 = hexc(c1) if isinstance(c1, str) else c1
    c2 = hexc(c2) if isinstance(c2, str) else c2
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def c4(c, a=None):
    if isinstance(c, str):
        c = hexc(c)
    if a is not None:
        c = (c[0], c[1], c[2], a)
    elif len(c) == 3:
        c = (c[0], c[1], c[2], 1.0)
    return skia.Color4f(*c)


def cint(c, a=None):
    return c4(c, a).toColor()


def fill(color, alpha=None, blur=0.0, shader=None, blend=None):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(c4(color, alpha))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        if alpha is not None:
            p.setAlphaf(alpha)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def stroke(color, width, alpha=None, cap="round", blur=0.0, blend=None):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(c4(color, alpha))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap}[cap])
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def lin_grad(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear(
        [skia.Point(*p0), skia.Point(*p1)], [cint(c) for c in colors], pos)


def rad_grad(center, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), max(r, 1e-3), [cint(c) for c in colors], pos)


def _bez_ctrl(p0, p1, p2, p3, alpha=0.5):
    """Centripetal Catmull-Rom segment p1->p2 as cubic Bezier control points (no overshoot/cusps)."""
    def dist(a, b):
        return max(math.hypot(b[0] - a[0], b[1] - a[1]), 1e-6)
    d1 = dist(p0, p1) ** alpha
    d2 = dist(p1, p2) ** alpha
    d3 = dist(p2, p3) ** alpha
    d1s, d2s, d3s = d1 * d1, d2 * d2, d3 * d3
    b1 = ((d1s * p2[0] - d2s * p0[0] + (2 * d1s + 3 * d1 * d2 + d2s) * p1[0]) / (3 * d1 * (d1 + d2)),
          (d1s * p2[1] - d2s * p0[1] + (2 * d1s + 3 * d1 * d2 + d2s) * p1[1]) / (3 * d1 * (d1 + d2)))
    b2 = ((d3s * p1[0] - d2s * p3[0] + (2 * d3s + 3 * d3 * d2 + d2s) * p2[0]) / (3 * d3 * (d3 + d2)),
          (d3s * p1[1] - d2s * p3[1] + (2 * d3s + 3 * d3 * d2 + d2s) * p2[1]) / (3 * d3 * (d3 + d2)))
    return b1, b2


def spline(points, closed=True, corners=(), tension=0.5, path=None):
    """Centripetal Catmull-Rom spline through points -> skia.Path.

    `corners` are indices where the curve may turn sharply (tangents point straight
    at the neighbouring point on each side)."""
    pts = [(float(p[0]), float(p[1])) for p in points]
    # drop consecutive duplicates
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 1e-7 or abs(p[1] - clean[-1][1]) > 1e-7:
            clean.append(p)
    n = len(clean)
    path = path if path is not None else skia.Path()
    if n < 2:
        return path
    if len(clean) != len(pts):
        corners = ()
    corners = set(i % n for i in corners) if closed else set(corners)
    pts = clean
    path.moveTo(*pts[0])
    segs = n if closed else n - 1
    for i in range(segs):
        i1, i2 = i, (i + 1) % n
        p1, p2 = pts[i1], pts[i2]
        if closed:
            p0 = pts[(i - 1) % n]
            p3 = pts[(i + 2) % n]
        else:
            p0 = pts[i - 1] if i > 0 else None
            p3 = pts[i + 2] if i + 2 < n else None
        if p0 is None or i1 in corners:
            p0 = (2 * p1[0] - p2[0], 2 * p1[1] - p2[1])
        if p3 is None or i2 in corners:
            p3 = (2 * p2[0] - p1[0], 2 * p2[1] - p1[1])
        b1, b2 = _bez_ctrl(p0, p1, p2, p3)
        path.cubicTo(b1[0], b1[1], b2[0], b2[1], p2[0], p2[1])
    if closed:
        path.close()
    return path


def poly(points, closed=True):
    path = skia.Path()
    path.moveTo(*points[0])
    for p in points[1:]:
        path.lineTo(*p)
    if closed:
        path.close()
    return path


def ellipse(cx, cy, rx, ry, rot_deg=0.0):
    path = skia.Path()
    path.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    if rot_deg:
        m = skia.Matrix()
        m.setRotate(rot_deg, cx, cy)
        path.transform(m)
    return path


def tapered(points, w0, w1, wmid=None, closed_cap=True):
    """Filled tapered stroke along a polyline/spline sample list."""
    pts = np.asarray(points, dtype=float)
    n = len(pts)
    if n < 2:
        return skia.Path()
    d = np.gradient(pts, axis=0)
    norm = np.stack([-d[:, 1], d[:, 0]], axis=1)
    norm /= (np.linalg.norm(norm, axis=1, keepdims=True) + 1e-9)
    t = np.linspace(0, 1, n)
    if wmid is None:
        w = w0 + (w1 - w0) * t
    else:
        w = np.where(t < 0.5, w0 + (wmid - w0) * (t / 0.5), wmid + (w1 - wmid) * ((t - 0.5) / 0.5))
        w = np.maximum(w, 0)
    left = pts + norm * (w[:, None] / 2)
    right = pts - norm * (w[:, None] / 2)
    outline = list(map(tuple, left)) + list(map(tuple, right[::-1]))
    return spline(outline, closed=True, tension=0.5)


def sample_spline(points, closed=False, n=24, tension=0.5):
    """Sample a Catmull-Rom spline into n points (list of (x,y))."""
    pts = np.asarray(points, dtype=float)
    m = len(pts)
    out = []
    segs = m if closed else m - 1
    per = max(2, n // segs)
    for i in range(segs):
        p0 = pts[(i - 1) % m] if (closed or i > 0) else pts[0]
        p1 = pts[i % m]
        p2 = pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if (closed or i + 2 < m) else pts[-1]
        for k in range(per):
            u = k / per
            u2, u3 = u * u, u * u * u
            # Catmull-Rom with tension
            a = 2 * tension
            m1 = (p2 - p0) * tension
            m2 = (p3 - p1) * tension
            h00 = 2 * u3 - 3 * u2 + 1
            h10 = u3 - 2 * u2 + u
            h01 = -2 * u3 + 3 * u2
            h11 = u3 - u2
            out.append(tuple(h00 * p1 + h10 * m1 + h01 * p2 + h11 * m2))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_io(t):
    t = min(max(t, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def lerp(a, b, t):
    return a + (b - a) * t


def font(path, size):
    tf = skia.Typeface.MakeFromFile(path)
    f = skia.Font(tf, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


FONT_DIR = "/usr/share/fonts/truetype/noto/"
