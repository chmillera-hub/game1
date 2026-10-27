"""'Drawn with starlight' helpers shared by sky overlays and vignettes."""
import math

import numpy as np
import skia

from gfx import clamp, ease_back, ease_io, ease_out, fill, font, hexc, smooth_path, stroke

COOL = "#d8ecff"
WARM = "#ffe9b8"
BLUE = "#7fc8ff"
PINK = "#ffb3c7"
SHADOW = "#050a1c"


def pop(t, t0, dur=0.38, s=1.7):
    """0 -> 1 with a slight overshoot, starting at t0."""
    if t0 is None:
        return 1.0
    if t <= t0:
        return 0.0
    return max(0.0, ease_back((t - t0) / dur, s))


def appear(t, t0, dur=0.35):
    if t0 is None:
        return 1.0
    return ease_out((t - t0) / dur) if t > t0 else 0.0


def ramp(t, t0, dur):
    if t0 is None:
        return 1.0
    return ease_io((t - t0) / dur) if t > t0 else 0.0


def cue(cues, name, default=None):
    v = cues.get(name) if cues else None
    return default if v is None else v


def trim_path(path, t1, t0=0.0):
    """Sub-path covering fraction [t0, t1] of the total length (all contours)."""
    if t1 >= 0.999 and t0 <= 0.0:
        return path
    pm = skia.PathMeasure(path, False)
    lens = []
    while True:
        lens.append(pm.getLength())
        if not pm.nextContour():
            break
    total = sum(lens)
    out = skia.Path()
    if total <= 0 or t1 <= t0:
        return out
    a, b = t0 * total, t1 * total
    pm = skia.PathMeasure(path, False)
    acc = 0.0
    for L in lens:
        s, e = max(a - acc, 0.0), min(b - acc, L)
        if e > s and L > 0:
            pm.getSegment(s, e, out, True)
        acc += L
        if not pm.nextContour():
            break
    return out


def glow_path(c, path, color=COOL, width=5.0, alpha=1.0, draw=1.0, glow_w=None, glow_a=0.35,
              shadow=True, cap="round"):
    """Glowing chalk stroke: dark halo (legibility), wide soft glow, crisp core."""
    if alpha <= 0.01 or draw <= 0.001:
        return
    p = trim_path(path, draw) if draw < 0.999 else path
    gw = glow_w if glow_w is not None else width * 3.2
    if shadow:
        c.drawPath(p, stroke(hexc(SHADOW, 0.30 * alpha), width * 2.2, cap=cap, blur=width * 1.1))
    c.drawPath(p, stroke(hexc(color, glow_a * alpha), gw, cap=cap, blur=gw * 0.45))
    c.drawPath(p, stroke(hexc(color, alpha), width, cap=cap))


def glow_fill(c, path, color, alpha=1.0, glow_r=14.0, glow_a=0.45):
    if alpha <= 0.01:
        return
    c.drawPath(path, fill(hexc(color, glow_a * alpha), blur=glow_r))
    c.drawPath(path, fill(hexc(color, alpha)))


LABEL_SCALE = 1.14


def label(c, text, x, y, size=34, color=WARM, alpha=1.0, weight="semibold", align="center", glow_a=0.45):
    if alpha <= 0.01:
        return
    size = size * LABEL_SCALE
    f = font(size, weight)
    w = f.measureText(text)
    xx = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    c.drawString(text, xx, y, f, fill(hexc(SHADOW, 0.55 * alpha), blur=size * 0.18))
    c.drawString(text, xx, y, f, fill(hexc(color, glow_a * alpha), blur=size * 0.22))
    c.drawString(text, xx, y, f, fill(hexc(color, alpha)))


def scaled(c, x, y, s, fn, rot=0.0):
    """Run fn() with the canvas scaled by s around (x, y)."""
    if s <= 0.001:
        return
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(math.degrees(rot))
    c.scale(s, s)
    c.translate(-x, -y)
    fn()
    c.restore()


# ----------------------------------------------------------------------------
# icon paths (centered on (0,0), roughly unit size 100)
# ----------------------------------------------------------------------------

def p_circle(r, cx=0.0, cy=0.0):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def p_lines(*segs):
    p = skia.Path()
    for seg in segs:
        p.moveTo(*seg[0])
        for q in seg[1:]:
            p.lineTo(*q)
    return p


def p_smooth(pts, close=False, tension=0.5):
    return smooth_path(pts, close, tension)


def p_hill():
    p = smooth_path([(-70, 35), (-38, -8), (-5, -30), (30, -12), (70, 35)], False, 0.5)
    p.moveTo(-90, 36)
    p.lineTo(90, 36)
    # little tree
    p.moveTo(18, -14)
    p.lineTo(18, -40)
    p.addCircle(18, -50, 12)
    return p


def p_wave():
    p = skia.Path()
    for row, y in enumerate((-18, 8, 34)):
        pts = []
        for k in range(9):
            x = -80 + k * 20
            pts.append((x, y + (-12 if k % 2 else 0) + (6 if row == 1 else 0)))
        q = smooth_path(pts, False, 0.6)
        p.addPath(q)
    return p


def p_cloud():
    p = skia.Path()
    p.moveTo(-70, 25)
    p.cubicTo(-95, 25, -95, -10, -62, -10)
    p.cubicTo(-58, -42, -15, -45, -5, -22)
    p.cubicTo(5, -52, 55, -50, 58, -15)
    p.cubicTo(92, -15, 92, 25, 65, 25)
    p.close()
    return p


def p_moon_icon(r=48):
    p = skia.Path()
    p.addCircle(0, 0, r)
    for (x, y, rr) in ((-14, -12, 10), (16, 8, 7), (-4, 20, 6), (20, -18, 5)):
        p.addCircle(x * r / 48, y * r / 48, rr * r / 48)
    return p


def p_house(w=90, h=80):
    p = skia.Path()
    p.moveTo(-w / 2, h / 2)
    p.lineTo(-w / 2, -h * 0.05)
    p.lineTo(0, -h / 2 - h * 0.15)
    p.lineTo(w / 2, -h * 0.05)
    p.lineTo(w / 2, h / 2)
    p.close()
    # door + window
    p.moveTo(-w * 0.12, h / 2)
    p.lineTo(-w * 0.12, h * 0.15)
    p.lineTo(w * 0.12, h * 0.15)
    p.lineTo(w * 0.12, h / 2)
    p.addRect(skia.Rect.MakeLTRB(w * 0.2, -h * 0.02, w * 0.38, h * 0.14))
    return p


def p_school(w=120, h=90):
    p = skia.Path()
    p.addRect(skia.Rect.MakeLTRB(-w / 2, -h * 0.15, w / 2, h / 2))
    # tower
    p.moveTo(-w * 0.15, -h * 0.15)
    p.lineTo(-w * 0.15, -h * 0.45)
    p.lineTo(0, -h * 0.62)
    p.lineTo(w * 0.15, -h * 0.45)
    p.lineTo(w * 0.15, -h * 0.15)
    # flag
    p.moveTo(0, -h * 0.62)
    p.lineTo(0, -h * 0.88)
    p.lineTo(w * 0.16, -h * 0.80)
    p.lineTo(0, -h * 0.73)
    # windows + door
    for x in (-0.36, -0.22, 0.22, 0.36):
        p.addRect(skia.Rect.MakeLTRB(w * x - 7, h * 0.02, w * x + 7, h * 0.16))
    p.addRect(skia.Rect.MakeLTRB(-w * 0.07, h * 0.22, w * 0.07, h / 2))
    p.addCircle(0, -h * 0.33, 8)
    return p


def p_ruler(w=170, h=38):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), 6, 6))
    n = 10
    for k in range(1, n):
        x = -w / 2 + w * k / n
        L = h * (0.45 if k % 5 == 0 else 0.25)
        p.moveTo(x, -h / 2)
        p.lineTo(x, -h / 2 + L)
    return p


def p_eye(w=120, h=64):
    p = skia.Path()
    p.moveTo(-w / 2, 0)
    p.quadTo(0, -h, w / 2, 0)
    p.quadTo(0, h, -w / 2, 0)
    p.close()
    p.addCircle(0, 0, h * 0.30)
    return p


def p_arrow(x0, y0, x1, y1, head=18):
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (-1, 1):
        p.moveTo(x1, y1)
        p.lineTo(x1 - head * math.cos(a + s * 0.5), y1 - head * math.sin(a + s * 0.5))
    return p


def p_burst(r0, r1, n=12, rot=0.0):
    p = skia.Path()
    for k in range(n * 2 + 1):
        r = r1 if k % 2 == 0 else r0
        a = rot + k * math.pi / n
        x, y = math.cos(a) * r, math.sin(a) * r
        if k == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    return p


def dotted(c, pts, color=COOL, r=4.0, gap=22.0, draw=1.0, alpha=1.0):
    """Dots along a polyline (with glow)."""
    pts = np.asarray(pts, np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    total = seg.sum()
    n = int(total * draw / gap)
    d = 0.0
    k = 0
    acc = np.concatenate([[0], np.cumsum(seg)])
    for i in range(n + 1):
        d = i * gap
        j = min(np.searchsorted(acc, d) - 1, len(seg) - 1)
        j = max(j, 0)
        f = (d - acc[j]) / max(seg[j], 1e-6)
        x, y = pts[j] + (pts[j + 1] - pts[j]) * f
        c.drawCircle(x, y, r * 2.2, fill(hexc(color, 0.25 * alpha), blur=r))
        c.drawCircle(x, y, r, fill(hexc(color, alpha)))


def spotlight_bg(c, W=1080, H=1920, center=(540, 760), inner="#2a3f7a", outer="#0a1230", r=1100):
    c.drawRect(skia.Rect.MakeWH(W, H), fill(hexc(outer)))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(*center), r, [hexc(inner), hexc(outer)], [0.0, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def _capsule(x0, y0, x1, y1, w):
    """Rounded bar from (x0,y0) to (x1,y1) as a closed path."""
    L = math.hypot(x1 - x0, y1 - y0)
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -w / 2, L + w / 2, w / 2), w / 2, w / 2))
    m = skia.Matrix()
    m.setRotate(math.degrees(math.atan2(y1 - y0, x1 - x0)))
    m.postTranslate(x0, y0)
    p.transform(m)
    return p


def _union(paths):
    out = paths[0]
    for q in paths[1:]:
        out = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
    return out


def p_open_hand():
    """Open hand, palm toward viewer, fingers up; palm centre at (0,0)."""
    parts = [skia.Path()]
    parts[0].addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-42, -28, 42, 46), 24, 24))
    for (bx, L, ang) in ((-31, 52, -0.20), (-11, 70, -0.07), (10, 76, 0.05), (30, 64, 0.17)):
        tx, ty = bx + math.sin(ang) * L, -18 - math.cos(ang) * L
        parts.append(_capsule(bx, -18, tx, ty, 19))
    parts.append(_capsule(34, 22, 70, -14, 22))
    wr = skia.Path()
    wr.addRect(skia.Rect.MakeLTRB(-30, 30, 30, 96))
    parts.append(wr)
    return _union(parts)


def p_point_hand():
    """Fist with the index finger pointing up; fist centre at (0,0)."""
    parts = [skia.Path()]
    parts[0].addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-40, -30, 40, 34), 20, 20))
    for kx in (-27, -9, 9):
        q = skia.Path()
        q.addCircle(kx, -28, 11)
        parts.append(q)
    parts.append(_capsule(27, -20, 27, -112, 21))
    wr = skia.Path()
    wr.addRect(skia.Rect.MakeLTRB(-30, 20, 30, 130))
    parts.append(wr)
    return _union(parts)


def hand_creases_point():
    p = skia.Path()
    for kx in (-18, 0):
        p.moveTo(kx, -26)
        p.lineTo(kx, -6)
    p.moveTo(-34, 6)
    p.quadTo(-8, 14, 16, 2)
    return p
