"""Cartoon toolkit: drawing helpers, posable characters, props and scenery.

Everything is drawn as vector shapes with skia, so the characters are new
cartoon versions inspired by the book's drawings (no pixels from the photos).

Character coordinates: origin at the feet (ground contact), y grows down,
scale 1 is the "model" size. Arm/leg angles are in degrees; 0 means the limb
hangs straight down, positive "raise" swings it outward/up away from the body.
"""
import math
import os

import numpy as np
import skia

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

OUT = (58, 44, 76)          # outline: deep plum, like the crayon outlines
SKIN = (255, 238, 226)
CHEEK = (255, 140, 170)
WHITE = (255, 255, 255)
BLACK = (40, 32, 48)

LINE = 7.0                  # main outline width at scale 1


# ----------------------------------------------------------------- basics
def color(rgb, a=1.0):
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), int(rgb[0]), int(rgb[1]), int(rgb[2]))


def fill_paint(rgb, a=1.0, shader=None, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=color(rgb, a))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke_paint(rgb, w, a=1.0, cap=skia.Paint.kRound_Cap):
    return skia.Paint(AntiAlias=True, Color=color(rgb, a), Style=skia.Paint.kStroke_Style,
                      StrokeWidth=w, StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)


def shape(c, path, rgb, line=LINE, out=OUT, a=1.0, shader=None):
    """Filled shape with a cartoon outline."""
    c.drawPath(path, fill_paint(rgb, a, shader))
    if line:
        c.drawPath(path, stroke_paint(out, line, a))


def outlined_union(c, paths, rgb, line=LINE, out=OUT, a=1.0):
    """Fluffy shapes: outline every piece first, then fill all on top, so the
    pieces read as one puffy silhouette with a single outline."""
    if line:
        for p in paths:
            c.drawPath(p, stroke_paint(out, line * 2, a))
    for p in paths:
        c.drawPath(p, fill_paint(rgb, a))


def circle(cx, cy, r):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth(pts, close=True, k=1.0):
    """Catmull-Rom spline through points -> smooth bezier path."""
    n = len(pts)
    p = skia.Path()
    p.moveTo(*pts[0])
    last = n if close else n - 1
    for i in range(last):
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 6, p1[1] + (p2[1] - p0[1]) * k / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 6, p2[1] - (p3[1] - p1[1]) * k / 6)
        p.cubicTo(*c1, *c2, *p2)
    if close:
        p.close()
    return p


def arc_path(cx, cy, rx, ry, a0, a1, n=24):
    pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return smooth(pts, close=False)


def spiky(cx, cy, rx, ry, n, depth, a0=0.0, a1=360.0, lean=0.35, seed=0, smooth_rest=True):
    """An ellipse whose edge between angles a0..a1 (degrees, screen space) is
    drawn as flame-like fur spikes. Spikes lean around the outline a bit."""
    rng = np.random.default_rng(seed)
    pts = []
    p = skia.Path()
    span = (a1 - a0) % 360 or 360
    step = span / n

    def at(a, extra=0.0):
        r = math.radians(a)
        return (cx + (rx + extra) * math.cos(r), cy + (ry + extra) * math.sin(r))

    start = at(a0)
    p.moveTo(*start)
    for i in range(n):
        av = a0 + i * step
        d = depth * (0.75 + 0.5 * rng.random())
        tip = at(av + step * (0.5 + lean), d)
        nxt = at(av + step)
        mid1 = at(av + step * 0.45, d * 0.25)
        mid2 = at(av + step * 0.95, d * 0.15)
        p.quadTo(*mid1, *tip)
        p.quadTo(*mid2, *nxt)
        pts.append(tip)
    if smooth_rest and span < 360:
        # rest of the ellipse, smooth
        m = 18
        for j in range(1, m + 1):
            a = a0 + span + (360 - span) * j / m
            p.lineTo(*at(a))
    p.close()
    return p


def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + 0.85 * s)
    p.cubicTo(cx - 1.25 * s, cy + 0.05 * s, cx - 0.95 * s, cy - 0.95 * s, cx, cy - 0.45 * s)
    p.cubicTo(cx + 0.95 * s, cy - 0.95 * s, cx + 1.25 * s, cy + 0.05 * s, cx, cy + 0.85 * s)
    p.close()
    return p


def star_path(cx, cy, ro, ri, n=5, rot=-90.0):
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180.0 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def sparkle_path(cx, cy, r):
    """Four-point twinkle."""
    p = skia.Path()
    k = 0.22 * r
    p.moveTo(cx, cy - r)
    p.quadTo(cx + k, cy - k, cx + r, cy)
    p.quadTo(cx + k, cy + k, cx, cy + r)
    p.quadTo(cx - k, cy + k, cx - r, cy)
    p.quadTo(cx - k, cy - k, cx, cy - r)
    p.close()
    return p


_FONT_CACHE = {}


def font(name, size):
    key = (name, size)
    if key not in _FONT_CACHE:
        tf = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
        _FONT_CACHE[key] = skia.Font(tf, size)
    return _FONT_CACHE[key]


def text(c, s, x, y, size, rgb=WHITE, outline=OUT, ow=8, name="Chewy-Regular.ttf", align="center", a=1.0):
    f = font(name, size)
    w = f.measureText(s)
    x0 = x - w / 2 if align == "center" else x
    blob = skia.TextBlob.MakeFromString(s, f)
    if ow:
        c.drawTextBlob(blob, x0, y, stroke_paint(outline, ow, a))
    c.drawTextBlob(blob, x0, y, fill_paint(rgb, a))
    return w


class Xf:
    """`with Xf(c, x, y, rot, sx, sy):` save / transform / restore."""

    def __init__(self, c, x=0.0, y=0.0, rot=0.0, sx=1.0, sy=None):
        self.c, self.args = c, (x, y, rot, sx, sx if sy is None else sy)

    def __enter__(self):
        x, y, rot, sx, sy = self.args
        self.c.save()
        self.c.translate(x, y)
        if rot:
            self.c.rotate(rot)
        if sx != 1 or sy != 1:
            self.c.scale(sx, sy)
        return self.c

    def __exit__(self, *a):
        self.c.restore()


class Fade:
    """`with Fade(c, alpha):` draw a group with uniform transparency."""

    def __init__(self, c, a):
        self.c, self.a = c, a

    def __enter__(self):
        if self.a < 0.999:
            self.c.saveLayerAlpha(None, int(max(0, self.a) * 255))
        else:
            self.c.save()
        return self.c

    def __exit__(self, *a):
        self.c.restore()


def limb(c, x, y, ang, length, w, rgb, line=LINE):
    """Round-capped limb from (x, y) at screen angle `ang` (0 = straight down).
    Returns the end point."""
    a = math.radians(ang)
    ex, ey = x - length * math.sin(a), y + length * math.cos(a)
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(ex, ey)
    if line:
        c.drawPath(p, stroke_paint(OUT, w + 2 * line * 0.75))
    c.drawPath(p, stroke_paint(rgb, w))
    return ex, ey


def two_bone(c, x, y, a1, a2, l1, l2, w, rgb):
    """Upper + lower limb; a2 is relative to a1. Returns end point."""
    ex, ey = limb(c, x, y, a1, l1, w, rgb)
    return limb(c, ex, ey, a1 + a2, l2, w, rgb)


def ground_shadow(c, x, y, w, a=0.18):
    c.drawPath(oval(x, y, w, w * 0.16), fill_paint(OUT, a, blur=6))


# ------------------------------------------------------------ face pieces
def eye(c, x, y, rx, ry, open_=1.0, look=(0.0, 0.0), sclera=True, pupil=None, line=4.0):
    """Cartoon eye; closes to a happy arc when open_ is small."""
    if open_ < 0.18:
        p = skia.Path()
        p.moveTo(x - rx, y)
        p.quadTo(x, y - ry * 0.9, x + rx, y)
        c.drawPath(p, stroke_paint(OUT, line + 1))
        return
    ry2 = ry * open_
    if sclera:
        shape(c, oval(x, y, rx, ry2), WHITE, line)
        pr = pupil or rx * 0.62
        px = x + look[0] * (rx - pr * 0.8)
        py = y + look[1] * (ry2 - pr * 0.8)
        c.save()
        c.clipPath(oval(x, y, rx, ry2), doAntiAlias=True)
        c.drawPath(oval(px, py, pr, pr * min(1, ry2 / pr)), fill_paint(BLACK))
        c.drawPath(circle(px + pr * 0.35, py - pr * 0.4, pr * 0.32), fill_paint(WHITE))
        c.restore()
    else:  # simple dot eye
        c.drawPath(oval(x + look[0] * 2, y + look[1] * 2, rx, ry2), fill_paint(BLACK))
        c.drawPath(circle(x + rx * 0.35 + look[0] * 2, y - ry2 * 0.4, rx * 0.36), fill_paint(WHITE))


def mouth(c, x, y, w, kind="smile", line=4.5, tongue=(255, 138, 160)):
    if kind == "smile":
        p = skia.Path()
        p.moveTo(x - w / 2, y - w * 0.08)
        p.quadTo(x, y + w * 0.45, x + w / 2, y - w * 0.08)
        c.drawPath(p, stroke_paint(OUT, line))
    elif kind in ("open", "laugh"):
        h = w * (0.55 if kind == "open" else 0.7)
        p = skia.Path()
        p.moveTo(x - w / 2, y - h * 0.15)
        p.quadTo(x, y - h * 0.32, x + w / 2, y - h * 0.15)
        p.cubicTo(x + w * 0.42, y + h * 0.95, x - w * 0.42, y + h * 0.95, x - w / 2, y - h * 0.15)
        p.close()
        c.drawPath(p, fill_paint((140, 40, 70)))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.drawPath(oval(x, y + h * 0.7, w * 0.3, h * 0.35), fill_paint(tongue))
        c.restore()
        c.drawPath(p, stroke_paint(OUT, line))
    elif kind == "o":
        shape(c, oval(x, y + w * 0.1, w * 0.2, w * 0.26), (140, 40, 70), line)
    elif kind == "sad":
        p = skia.Path()
        p.moveTo(x - w * 0.4, y + w * 0.15)
        p.quadTo(x, y - w * 0.2, x + w * 0.4, y + w * 0.15)
        c.drawPath(p, stroke_paint(OUT, line))
    elif kind == "flat":
        p = skia.Path()
        p.moveTo(x - w * 0.3, y)
        p.lineTo(x + w * 0.3, y)
        c.drawPath(p, stroke_paint(OUT, line))


def blush(c, x, y, rx, a=0.55):
    if a > 0.01:
        c.drawPath(oval(x, y, rx, rx * 0.62), fill_paint(CHEEK, a, blur=2.5))


# ------------------------------------------------------------ characters
class BunnyGirl:
    """Teal bunny-ear hat with pom-pom flaps, pink dress with a bunny on it,
    teal boots. Front view."""
    TEAL, TEAL_D, TEAL_L = (64, 196, 196), (36, 150, 160), (150, 230, 226)
    EAR_IN = (255, 205, 222)
    DRESS, DRESS_D = (247, 164, 200), (230, 128, 172)

    def ear(self, c, bx, by, ang, bend, side):
        L, Wd = 165.0, 56.0
        a = math.radians(ang)
        tip = (bx + L * math.sin(a), by - L * math.cos(a))
        nx, ny = math.cos(a), math.sin(a)          # perpendicular (outward for +x)
        ctrl = ((bx + tip[0]) / 2 + bend * side * L * 0.35 * nx, (by + tip[1]) / 2 + bend * side * L * 0.35 * ny)

        def outline(width, length_k=1.0, inset=0.0):
            left, right = [], []
            for i in range(0, 13):
                u = i / 12 * length_k
                px = (1 - u) ** 2 * bx + 2 * (1 - u) * u * ctrl[0] + u * u * tip[0]
                py = (1 - u) ** 2 * by + 2 * (1 - u) * u * ctrl[1] + u * u * tip[1]
                dx = 2 * (1 - u) * (ctrl[0] - bx) + 2 * u * (tip[0] - ctrl[0])
                dy = 2 * (1 - u) * (ctrl[1] - by) + 2 * u * (tip[1] - ctrl[1])
                dl = math.hypot(dx, dy) or 1
                qx, qy = -dy / dl, dx / dl
                w = width / 2 * (0.62 + 0.55 * math.sin(math.pi * min(u / length_k, 1) * 0.92 + 0.15))
                if u / length_k > 0.82:
                    w *= math.sqrt(max(0.0, 1 - ((u / length_k - 0.82) / 0.2) ** 2))
                left.append((px + qx * w, py + qy * w + inset))
                right.append((px - qx * w, py - qy * w + inset))
            return smooth(left + right[::-1])
        shape(c, outline(Wd), self.TEAL)
        c.drawPath(outline(Wd * 0.42, 0.8, 10), fill_paint(self.EAR_IN))

    def draw(self, c, x, y, s=1.0, facing=1, sx=1.0, sy=1.0, lean=0.0, head_tilt=0.0,
             ear_l=-14.0, ear_r=14.0, ear_bend=0.0, arm_l=(18, 0), arm_r=(18, 0),
             leg_l=0.0, leg_r=0.0, lift_l=0.0, lift_r=0.0, eye_open=1.0, look=(0, 0),
             mouth_kind="smile", blush_a=0.55, alpha=1.0, shadow=True, hands_together=False):
        if shadow:
            ground_shadow(c, x, y, 120 * s)
        with Fade(c, alpha), Xf(c, x, y, lean, s * sx * facing, s * sy):
            # legs + boots
            for side, ang, lift in ((-1, leg_l, lift_l), (1, leg_r, lift_r)):
                hx, hy = side * 30, -112
                ex, ey = limb(c, hx, hy - lift, side * -4 + ang, 70, 13, SKIN)
                shape(c, rrect(ex - 25 + side * 4, ey - 10, ex + 25 + side * 4, ey + 28, 15), self.TEAL)
                c.drawPath(rrect(ex - 23 + side * 4, ey + 18, ex + 23 + side * 4, ey + 26, 4), fill_paint(self.TEAL_D))
            # dress
            dress = smooth([(-34, -280), (-62, -230), (-96, -160), (-118, -112), (-60, -98),
                            (0, -96), (60, -98), (118, -112), (96, -160), (62, -230), (34, -280), (0, -284)], k=0.9)
            shape(c, dress, self.DRESS)
            c.save()
            c.clipPath(dress, doAntiAlias=True)
            c.drawPath(oval(0, -96, 140, 26), fill_paint(self.DRESS_D, 0.8))
            c.restore()
            c.drawPath(dress, stroke_paint(OUT, LINE))
            # bunny on the dress
            for sgn in (-1, 1):
                shape(c, oval(sgn * 9, -232, 7, 19), (166, 214, 245), 3.5)
            shape(c, circle(0, -200, 22), (166, 214, 245), 3.5)
            c.drawPath(circle(-7, -204, 2.6), fill_paint(OUT))
            c.drawPath(circle(7, -204, 2.6), fill_paint(OUT))
            c.drawPath(oval(0, -196, 3.5, 2.6), fill_paint((255, 130, 160)))
            # arms (with puffy sleeves)
            for side, (a1, a2) in ((-1, arm_l), (1, arm_r)):
                sxx, syy = side * 40, -262
                if hands_together:
                    a1, a2 = 28, 70
                hx, hy = two_bone(c, sxx, syy, -side * a1, -side * a2, 56, 52, 13, SKIN)
                shape(c, circle(hx, hy, 15), SKIN, 5)
                shape(c, oval(sxx + side * 4, syy + 6, 20, 16), self.DRESS, 5)
            # head group
            with Xf(c, 0, -282, head_tilt):
                c.translate(0, 282)
                # flaps behind the face edges
                for side in (-1, 1):
                    flap = smooth([(side * 78, -420), (side * 116, -398), (side * 120, -330),
                                   (side * 110, -294), (side * 86, -300), (side * 84, -360)], k=0.9)
                    shape(c, flap, self.TEAL)
                # face
                shape(c, circle(0, -372, 100), SKIN)
                blush(c, -60, -334, 19, blush_a)
                blush(c, 60, -334, 19, blush_a)
                eye(c, -36, -366, 21, 25, eye_open, look)
                eye(c, 36, -366, 21, 25, eye_open, look)
                nose = skia.Path()
                nose.moveTo(-6, -346)
                nose.quadTo(0, -339, 6, -346)
                c.drawPath(nose, stroke_paint(OUT, 3.5))
                mouth(c, 0, -322, 44, mouth_kind)
                # ears behind the hat, then the hat
                self.ear(c, -40, -448, ear_l, ear_bend, -1)
                self.ear(c, 40, -448, ear_r, ear_bend, 1)
                dome = smooth([(-114, -404), (-110, -452), (-76, -488), (0, -503), (76, -488), (110, -452),
                               (114, -404), (60, -412), (0, -415), (-60, -412)], k=0.95)
                shape(c, dome, self.TEAL)
                c.save()
                c.clipPath(dome, doAntiAlias=True)
                for k in (-62, -22, 22, 62):  # knit ribs
                    rib = skia.Path()
                    rib.moveTo(k * 0.55, -496)
                    rib.quadTo(k * 1.05, -455, k, -412)
                    c.drawPath(rib, stroke_paint(self.TEAL_D, 4, 0.55))
                c.restore()
                c.drawPath(dome, stroke_paint(OUT, LINE))
                band = smooth([(-117, -412), (-60, -424), (0, -427), (60, -424), (117, -412),
                               (115, -392), (60, -401), (0, -404), (-60, -401), (-115, -392)], k=0.9)
                shape(c, band, self.TEAL_L, 5)
                # pom-poms at the end of the flaps
                for side in (-1, 1):
                    shape(c, circle(side * 106, -296, 19), self.TEAL_L)
                    c.drawPath(circle(side * 100, -302, 6), fill_paint(WHITE, 0.7))


class WolfDog:
    """Big, fluffy, spiky-furred, smiley. 3/4 view facing right.

    parts: "all", "back" (everything except the front arm) or "arm" (only the
    front arm) - so another character can be drawn inside a hug.
    """
    FUR, FUR_D, BELLY = (180, 168, 176), (150, 136, 150), (248, 228, 228)
    EAR_IN = (255, 188, 205)

    def tail(self, c, wag):
        with Xf(c, -150, -150, wag):
            pts_out = []
            for i in range(9):  # spiky outer edge of a plume curling up-left
                u = i / 8
                a = math.radians(200 + 95 * u)
                r = 95 + 40 * math.sin(math.pi * u)
                pts_out.append((-70 + r * math.cos(a) * 1.05, -40 + r * math.sin(a) * 0.95))
            path = skia.Path()
            path.moveTo(0, 0)
            path.quadTo(-60, 40, *pts_out[0])
            for i in range(1, len(pts_out)):
                x0, y0 = pts_out[i - 1]
                x1, y1 = pts_out[i]
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                dx, dy = mx + 70, my + 40
                dl = math.hypot(dx, dy) or 1
                path.quadTo(x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.2, mx + dx / dl * 26, my + dy / dl * 26)
                path.quadTo(x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.8, x1, y1)
            path.quadTo(-20, -120, 0, -60)
            path.close()
            shape(c, path, self.FUR)
            c.save()
            c.clipPath(path, doAntiAlias=True)
            c.drawPath(circle(*pts_out[-2], 48), fill_paint(self.BELLY, 0.95))
            c.restore()
            c.drawPath(path, stroke_paint(OUT, LINE))

    def leg(self, c, hx, ang, lift, rgb):
        with Xf(c, hx, -58 - lift, ang):
            shape(c, rrect(-34, -30, 34, 40, 30), rgb)
            shape(c, oval(6, 44, 42, 18), rgb)
            for k in (-8, 12):
                t = skia.Path()
                t.moveTo(6 + k, 36)
                t.lineTo(6 + k, 50)
                c.drawPath(t, stroke_paint(OUT, 3.5))

    def arm(self, c, ang, rgb):
        # ang: 0 hangs down, 90 sticks out sideways, 120 is a happy wave
        with Xf(c, 0, 0, -ang):
            shape(c, rrect(-24, -12, 24, 100, 24), rgb)
            shape(c, circle(0, 108, 27), rgb)
            for k in (-9, 9):
                t = skia.Path()
                t.moveTo(k, 120)
                t.lineTo(k, 132)
                c.drawPath(t, stroke_paint(OUT, 3.5))

    def draw(self, c, x, y, s=1.0, facing=1, sx=1.0, sy=1.0, lean=0.0, head_tilt=0.0,
             arm_b=20.0, arm_f=20.0, leg_b=0.0, leg_f=0.0, lift_b=0.0, lift_f=0.0, tail=0.0,
             ear_droop=0.0, eye_open=1.0, look=(0, 0), mouth_kind="smile", blush_a=0.0,
             alpha=1.0, shadow=True, glow=0.0, parts="all"):
        if glow > 0 and parts != "arm":
            g = skia.GradientShader.MakeRadial(skia.Point(x, y - 280 * s), 430 * s,
                                               [color((255, 244, 160), 0.9 * glow), color((255, 220, 120), 0)])
            c.drawPath(circle(x, y - 280 * s, 430 * s), fill_paint(WHITE, 1.0, shader=g))
        if shadow and parts != "arm":
            ground_shadow(c, x, y, 150 * s, 0.18 * alpha)
        with Fade(c, alpha), Xf(c, x, y, lean, s * sx * facing, s * sy):
            if parts in ("all", "back"):
                self.tail(c, tail)
                self.leg(c, -64, leg_b, lift_b, self.FUR_D)
                with Xf(c, -118, -292):
                    self.arm(c, -arm_b, self.FUR_D)
                body = spiky(0, -210, 160, 182, 26, 30, a0=95, a1=95 + 330, lean=0.45, seed=7)
                shape(c, body, self.FUR)
                c.save()
                c.clipPath(body, doAntiAlias=True)
                c.drawPath(oval(-150, -260, 90, 200), fill_paint(self.FUR_D, 0.55))
                c.restore()
                shape(c, oval(28, -180, 108, 126), self.BELLY, 0)
                for tx, ty in ((-10, -300), (40, -296), (85, -270), (-50, -270)):
                    tuft = skia.Path()
                    tuft.moveTo(tx - 14, ty - 8)
                    tuft.lineTo(tx, ty + 12)
                    tuft.lineTo(tx + 14, ty - 8)
                    c.drawPath(tuft, stroke_paint(OUT, 4))
                self.leg(c, 70, leg_f, lift_f, self.FUR)
                with Xf(c, 30, -330, head_tilt):
                    c.translate(0, 330)
                    self.head(c, ear_droop, eye_open, look, mouth_kind, blush_a)
            if parts in ("all", "arm"):
                with Xf(c, 126, -282):
                    self.arm(c, arm_f, self.FUR)

    def head(self, c, ear_droop, eye_open, look, mouth_kind, blush_a):
        hx, hy = 30, -418
        for ex, lean_e in ((-48, -16), (92, 16)):
            with Xf(c, ex, -505, lean_e + (ear_droop if lean_e > 0 else -ear_droop)):
                shape(c, poly([(-38, 18), (0, -88), (38, 18)]), self.FUR)
                c.drawPath(poly([(-20, 10), (0, -58), (20, 10)]), fill_paint(self.EAR_IN))
        head = spiky(hx, hy, 122, 112, 14, 22, a0=120, a1=300, lean=0.3, seed=11)
        shape(c, head, self.FUR)
        snout = smooth([(70, -440), (135, -432), (176, -410), (172, -386), (120, -370), (70, -372)], k=1.0)
        shape(c, snout, self.BELLY)
        shape(c, oval(172, -410, 15, 12), BLACK, 3)
        c.drawPath(circle(167, -414, 4), fill_paint(WHITE, 0.8))
        eye(c, 18, -446, 10, 14, eye_open, look, sclera=False)
        eye(c, 78, -450, 10, 14, eye_open, look, sclera=False)
        for bx in (18, 78):
            br = skia.Path()
            br.moveTo(bx - 14, -476)
            br.quadTo(bx, -486, bx + 14, -478)
            c.drawPath(br, stroke_paint(OUT, 4))
        blush(c, -12, -400, 22, blush_a)
        blush(c, 112, -398, 14, blush_a * 0.8)
        if mouth_kind == "smile":
            m = skia.Path()
            m.moveTo(20, -392)
            m.quadTo(80, -350, 140, -378)
            c.drawPath(m, stroke_paint(OUT, 5))
        elif mouth_kind in ("open", "laugh"):
            m = skia.Path()
            m.moveTo(30, -392)
            m.quadTo(85, -386, 138, -380)
            m.cubicTo(128, -325, 52, -320, 30, -392)
            m.close()
            c.drawPath(m, fill_paint((140, 40, 70)))
            c.save()
            c.clipPath(m, doAntiAlias=True)
            c.drawPath(oval(88, -335, 30, 20), fill_paint((255, 138, 160)))
            c.restore()
            c.drawPath(m, stroke_paint(OUT, 5))
        elif mouth_kind == "o":
            shape(c, oval(95, -362, 14, 18), (140, 40, 70), 4.5)
        elif mouth_kind == "sad":
            m = skia.Path()
            m.moveTo(45, -362)
            m.quadTo(90, -385, 132, -364)
            c.drawPath(m, stroke_paint(OUT, 5))


class Mom:
    """Blonde bob, pink dress with a white collar. Front view."""
    HAIR, HAIR_D = (248, 214, 110), (222, 172, 62)
    DRESS, DRESS_D = (250, 186, 208), (236, 150, 182)

    def draw(self, c, x, y, s=1.0, facing=1, sx=1.0, sy=1.0, lean=0.0, head_tilt=0.0,
             arm_l=(14, 0), arm_r=(14, 0), leg_l=0.0, leg_r=0.0, lift_l=0.0, lift_r=0.0,
             eye_open=1.0, look=(0, 0), mouth_kind="smile", blush_a=0.5, alpha=1.0, shadow=True):
        if shadow:
            ground_shadow(c, x, y, 130 * s)
        with Fade(c, alpha), Xf(c, x, y, lean, s * sx * facing, s * sy):
            for side, ang, lift in ((-1, leg_l, lift_l), (1, leg_r, lift_r)):
                ex, ey = limb(c, side * 40, -150 - lift, side * -3 + ang, 118, 14, SKIN)
                shape(c, oval(ex + side * 6, ey + 6, 27, 15), (216, 112, 143))
            # back hair
            back = smooth([(-114, -600), (-122, -680), (-96, -770), (0, -800), (96, -770), (122, -680),
                           (114, -600), (84, -588), (60, -600), (0, -620), (-60, -600), (-84, -588)], k=0.9)
            shape(c, back, self.HAIR)
            # dress with wavy hem
            hem = []
            for i in range(11):
                u = i / 10
                hem.append((175 - 350 * u, -135 + (10 if i % 2 else -8)))
            dress = smooth([(-46, -592), (-80, -520), (-130, -330), (-176, -140)] + hem[::-1][1:-1]
                           + [(176, -140), (130, -330), (80, -520), (46, -592), (0, -600)], k=0.85)
            shape(c, dress, self.DRESS)
            c.save()
            c.clipPath(dress, doAntiAlias=True)
            c.drawPath(oval(0, -140, 210, 34), fill_paint(self.DRESS_D, 0.7))
            c.restore()
            c.drawPath(dress, stroke_paint(OUT, LINE))
            for side in (-1, 1):  # collar
                shape(c, smooth([(0, -598), (side * 48, -594), (side * 52, -566), (side * 22, -556)], k=1), WHITE, 5)
            # arms
            for side, (a1, a2) in ((-1, arm_l), (1, arm_r)):
                hx, hy = two_bone(c, side * 52, -572, -side * a1, -side * a2, 100, 92, 15, SKIN)
                shape(c, circle(hx, hy, 17), SKIN, 5)
                shape(c, oval(side * 56, -566, 24, 19), self.DRESS, 5)
            with Xf(c, 0, -600, head_tilt):
                c.translate(0, 600)
                shape(c, circle(0, -688, 90), SKIN)
                blush(c, -52, -660, 17, blush_a)
                blush(c, 52, -660, 17, blush_a)
                eye(c, -30, -688, 10, 14, eye_open, look, sclera=False)
                eye(c, 30, -688, 10, 14, eye_open, look, sclera=False)
                mouth(c, 0, -648, 40, mouth_kind)
                # bangs with a middle part
                bangs = smooth([(-100, -690), (-92, -744), (-50, -786), (0, -794), (50, -786), (92, -744),
                                (100, -690), (70, -722), (24, -742), (0, -762), (-24, -742), (-70, -722)], k=0.9)
                shape(c, bangs, self.HAIR)
                for sgn in (-1, 1):
                    st = skia.Path()
                    st.moveTo(sgn * 6, -780)
                    st.quadTo(sgn * 50, -770, sgn * 74, -730)
                    c.drawPath(st, stroke_paint(self.HAIR_D, 4))


class Dog:
    """Small side-view dogs (facing right). Five looks for the five dogs."""
    LOOKS = {
        "Cosmo": dict(kind="fluffy", body=(255, 255, 255), shade=(232, 228, 244), ear="round", collar=(90, 170, 240),
                      bx=0, by=-74, brx=72, bry=48, hx=66, hy=-128, hr=44, leg=38, legw=24, snout=22, tail="pom", size=1.0),
        "Pettie": dict(kind="smooth", body=(246, 182, 200), shade=(226, 140, 170), ear="floppy", collar=(255, 205, 60),
                       bx=0, by=-60, brx=112, bry=36, hx=120, hy=-92, hr=34, leg=26, legw=20, snout=40, tail="thin", size=1.0),
        "Luna": dict(kind="fluffy", body=(74, 66, 84), shade=(52, 46, 60), ear="pointy", collar=(255, 120, 170),
                     bx=0, by=-56, brx=56, bry=38, hx=50, hy=-98, hr=36, leg=30, legw=19, snout=16, tail="curl", size=1.0, bow=True),
        "Mooky": dict(kind="fluffy", body=(170, 178, 192), shade=(140, 148, 165), ear="pointy", collar=(235, 80, 90),
                      bx=0, by=-112, brx=104, bry=66, hx=100, hy=-186, hr=58, leg=58, legw=32, snout=34, tail="plume", size=1.0, mask=(244, 246, 250)),
        "Buddy": dict(kind="smooth", body=(230, 170, 106), shade=(200, 140, 82), ear="floppy_dark", collar=(90, 190, 110),
                      bx=0, by=-84, brx=84, bry=50, hx=84, hy=-136, hr=46, leg=46, legw=26, snout=30, tail="tip", size=1.0, patch=(138, 86, 54)),
    }

    def __init__(self, name):
        self.name = name
        self.L = self.LOOKS[name]

    def body_path(self, L):
        if L["kind"] == "fluffy":
            return None
        return oval(L["bx"], L["by"], L["brx"], L["bry"])

    def fluffy(self, c, cx, cy, rx, ry, rgb, seed, n=9, line=LINE):
        rng = np.random.default_rng(seed)
        paths = []
        for i in range(n):
            a = 2 * math.pi * i / n
            r = min(rx, ry) * (0.42 + 0.1 * rng.random())
            paths.append(circle(cx + (rx - r * 0.9) * math.cos(a), cy + (ry - r * 0.9) * math.sin(a), r))
        paths.append(oval(cx, cy, rx * 0.85, ry * 0.85))
        outlined_union(c, paths, rgb, line / 2)

    def draw(self, c, x, y, s=1.0, facing=1, phase=0.0, run=0.0, tail=0.0, jump=0.0, sx=1.0, sy=1.0,
             mouth_kind="smile", eye_open=1.0, look=(0.3, 0), head_tilt=0.0, alpha=1.0, shadow=True, ear_flop=0.0):
        L = self.L
        if shadow:
            ground_shadow(c, x, y + jump * 0, (L["brx"] + 20) * s, 0.16)
        bob = -abs(math.sin(phase)) * 10 * run
        with Fade(c, alpha), Xf(c, x, y - jump + bob * s, 0, s * sx * facing, s * sy):
            bx, by, brx, bry = L["bx"], L["by"], L["brx"], L["bry"]
            leg, lw = L["leg"], L["legw"]
            hips = [(bx - brx * 0.62, by + bry * 0.55), (bx + brx * 0.6, by + bry * 0.55)]
            swing = [math.sin(phase), math.sin(phase + math.pi)]

            def legs(far):
                for i, (hx, hy) in enumerate(hips):
                    ang = 32 * run * (swing[i] if far else -swing[i])
                    col = L["shade"] if far else L["body"]
                    with Xf(c, hx + (8 if far else -6), hy - 6, ang):
                        shape(c, rrect(-lw / 2, -lw / 2, lw / 2, leg + 6, lw / 2), col, LINE * 0.8)
            legs(True)
            # tail
            with Xf(c, bx - brx * 0.9, by - bry * 0.35, -30 + tail):
                t = L["tail"]
                if t == "pom":
                    outlined_union(c, [circle(-14, -16, 20), circle(-26, -6, 15), circle(-4, -28, 14)], L["body"], LINE / 2)
                elif t == "thin":
                    p = skia.Path()
                    p.moveTo(0, 0)
                    p.quadTo(-30, -20, -42, -52)
                    c.drawPath(p, stroke_paint(OUT, 12))
                    c.drawPath(p, stroke_paint(L["body"], 6))
                elif t == "curl":
                    p = skia.Path()
                    p.moveTo(0, 0)
                    p.cubicTo(-30, -10, -40, -45, -14, -50)
                    c.drawPath(p, stroke_paint(OUT, 18))
                    c.drawPath(p, stroke_paint(L["body"], 10))
                elif t == "plume":
                    p = skia.Path()
                    p.moveTo(0, 0)
                    p.cubicTo(-46, -6, -60, -70, -18, -86)
                    c.drawPath(p, stroke_paint(OUT, 44))
                    c.drawPath(p, stroke_paint(L["body"], 30))
                    shape(c, circle(-18, -86, 17), L.get("mask", WHITE), 5)
                elif t == "tip":
                    p = skia.Path()
                    p.moveTo(0, 0)
                    p.quadTo(-26, -24, -36, -60)
                    c.drawPath(p, stroke_paint(OUT, 16))
                    c.drawPath(p, stroke_paint(L["body"], 9))
                    c.drawPath(circle(-36, -62, 8), fill_paint(WHITE))
                    c.drawPath(circle(-36, -62, 8), stroke_paint(OUT, 3))
            # body
            if L["kind"] == "fluffy":
                self.fluffy(c, bx, by, brx, bry, L["body"], seed=hash(self.name) % 97)
            else:
                shape(c, oval(bx, by, brx, bry), L["body"])
                if "patch" in L:
                    c.save()
                    c.clipPath(oval(bx, by, brx, bry), doAntiAlias=True)
                    c.drawPath(oval(bx - brx * 0.25, by - bry * 0.7, brx * 0.5, bry * 0.55), fill_paint(L["patch"]))
                    c.restore()
                    c.drawPath(oval(bx, by, brx, bry), stroke_paint(OUT, LINE))
                c.drawPath(oval(bx + brx * 0.35, by + bry * 0.35, brx * 0.45, bry * 0.4), fill_paint(WHITE, 0.55))
            legs(False)
            # head
            hx, hy, hr = L["hx"], L["hy"], L["hr"]
            with Xf(c, hx - hr * 0.6, hy + hr * 0.6, head_tilt):
                c.translate(-(hx - hr * 0.6), -(hy + hr * 0.6))
                ear = L["ear"]
                if ear == "pointy":
                    for ex, k in ((hx - hr * 0.55, 1.0), (hx + hr * 0.05, 1.0)):
                        shape(c, poly([(ex - hr * 0.32, hy - hr * 0.55), (ex + hr * 0.02, hy - hr * 1.45), (ex + hr * 0.36, hy - hr * 0.55)]), L["body"])
                        c.drawPath(poly([(ex - hr * 0.15, hy - hr * 0.62), (ex + hr * 0.02, hy - hr * 1.15), (ex + hr * 0.2, hy - hr * 0.62)]), fill_paint((255, 180, 200)))
                if L["kind"] == "fluffy":
                    self.fluffy(c, hx, hy, hr, hr * 0.92, L["body"], seed=hash(self.name) % 89 + 3, n=8)
                else:
                    shape(c, circle(hx, hy, hr), L["body"])
                if "mask" in L:
                    c.drawPath(oval(hx + hr * 0.25, hy + hr * 0.2, hr * 0.62, hr * 0.55), fill_paint(L["mask"]))
                # snout + nose
                sn = L["snout"]
                shape(c, oval(hx + hr * 0.75 + sn * 0.25, hy + hr * 0.18, hr * 0.38 + sn * 0.45, hr * 0.32), L.get("mask", L["body"]), LINE * 0.8)
                nx = hx + hr * 0.78 + sn * 0.7 + hr * 0.25
                shape(c, oval(nx, hy + hr * 0.08, hr * 0.15, hr * 0.12), BLACK, 3)
                ew = max(7.0, hr * 0.17) * (1.35 if L["body"][0] < 100 else 1.0)
                eye(c, hx + hr * 0.38, hy - hr * 0.2, ew, ew * 1.25, eye_open, look, sclera=L["body"][0] < 100)
                if mouth_kind in ("open", "laugh"):
                    m = skia.Path()
                    m.moveTo(hx + hr * 0.55, hy + hr * 0.42)
                    m.quadTo(hx + hr * 0.9, hy + hr * 0.95, hx + hr * 1.15, hy + hr * 0.42)
                    m.close()
                    shape(c, m, (140, 40, 70), 4)
                    c.drawPath(oval(hx + hr * 0.86, hy + hr * 0.78, hr * 0.15, hr * 0.2), fill_paint((255, 138, 160)))
                else:
                    m = skia.Path()
                    m.moveTo(hx + hr * 0.55, hy + hr * 0.45)
                    m.quadTo(hx + hr * 0.82, hy + hr * 0.62, hx + hr * 1.05, hy + hr * 0.42)
                    c.drawPath(m, stroke_paint(OUT, 4))
                if ear in ("floppy", "floppy_dark"):
                    col = L["patch"] if ear == "floppy_dark" else L["shade"]
                    with Xf(c, hx - hr * 0.2, hy - hr * 0.75, ear_flop):
                        shape(c, smooth([(0, 0), (hr * 0.32, hr * 0.12), (hr * 0.28, hr * 0.95), (hr * 0.02, hr * 1.55),
                                         (-hr * 0.32, hr * 1.35), (-hr * 0.36, hr * 0.5)], k=1), col)
                elif ear == "round":
                    with Xf(c, hx - hr * 0.3, hy - hr * 0.55, ear_flop):
                        outlined_union(c, [circle(-hr * 0.12, hr * 0.25, hr * 0.3), circle(-hr * 0.2, hr * 0.7, hr * 0.32),
                                           circle(-hr * 0.08, hr * 1.1, hr * 0.27)], L["shade"], LINE / 2)
                if L.get("bow"):
                    for sgn in (-1, 1):
                        shape(c, poly([(hx - hr * 0.1, hy - hr * 0.95), (hx - hr * 0.1 + sgn * hr * 0.45, hy - hr * 1.2),
                                       (hx - hr * 0.1 + sgn * hr * 0.45, hy - hr * 0.7)]), L["collar"], 4)
                    shape(c, circle(hx - hr * 0.1, hy - hr * 0.95, hr * 0.13), L["collar"], 4)
            # collar
            c.drawPath(arc_path(hx - hr * 0.55, hy + hr * 0.85, hr * 0.42, hr * 0.2, 20, 160), stroke_paint(OUT, 11))
            c.drawPath(arc_path(hx - hr * 0.55, hy + hr * 0.85, hr * 0.42, hr * 0.2, 20, 160), stroke_paint(L["collar"], 6))


class LittleBunny:
    """A real little white bunny (side view, facing left by default)."""

    def draw(self, c, x, y, s=1.0, facing=-1, sx=1.0, sy=1.0, ear=0.0, eye_open=1.0, nose=0.0):
        ground_shadow(c, x, y, 50 * s, 0.15)
        with Xf(c, x, y, 0, s * sx * facing, s * sy):
            shape(c, circle(52, -40, 16), WHITE, 5)                      # cotton tail
            shape(c, oval(18, -42, 46, 36), WHITE)                         # body
            shape(c, oval(-14, -14, 16, 9), WHITE, 5)                      # front foot
            for k, lean in ((10, 8 + ear), (-6, -6 + ear)):                # ears
                with Xf(c, -18 + k * 0.4, -86, lean):
                    shape(c, oval(0, -40, 11, 36), WHITE, 5)
                    c.drawPath(oval(0, -38, 5, 26), fill_paint((255, 190, 210)))
            shape(c, circle(-24, -78, 27), WHITE)                          # head
            eye(c, -34, -82, 6, 8, eye_open, (-0.5, 0), sclera=False)
            c.drawPath(oval(-50, -71 + nose, 5, 4), fill_paint((255, 130, 160)))
            blush(c, -26, -64, 8, 0.6)


def limb_end(x, y, ang, length):
    a = math.radians(ang)
    return x - length * math.sin(a), y + length * math.cos(a)


def girl_hand(x, y, s, side, a1, a2, facing=1, sy=1.0):
    """World position of Bunny Girl's hand for an arm pose (side -1 left, 1 right)."""
    ex, ey = limb_end(side * 40, -262, -side * a1, 56)
    hx, hy = limb_end(ex, ey, -side * a1 - side * a2, 52)
    return x + facing * s * hx, y + s * sy * hy


def mom_hand(x, y, s, side, a1, a2, facing=1, sy=1.0):
    ex, ey = limb_end(side * 52, -572, -side * a1, 100)
    hx, hy = limb_end(ex, ey, -side * a1 - side * a2, 92)
    return x + facing * s * hx, y + s * sy * hy


def wolf_paw(x, y, s, front, ang, facing=1, sy=1.0):
    """World position of Wolf Dog's paw (front arm or back arm)."""
    if front:
        lx, ly = 126 + 108 * math.sin(math.radians(ang)), -282 + 108 * math.cos(math.radians(ang))
    else:
        lx, ly = -118 - 108 * math.sin(math.radians(ang)), -292 + 108 * math.cos(math.radians(ang))
    return x + facing * s * lx, y + s * sy * ly
