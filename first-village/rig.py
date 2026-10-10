"""Puppet rig: a front-facing character with an expressive face and posable arms.

Local coordinates: feet at (0, 0), y grows downward (so the head is at negative y).
A standing adult is ~520 units tall. Draw with draw_person(canvas, style, pose).
"""
import math

import skia

from anim import (C, clamp, glow, hashf, lerp, mixc, oval, paint, rad, lin, shade, spline)

R = 50.0  # head radius unit


class Style:
    def __init__(self, **kw):
        self.skin = (198, 143, 102)
        self.iris = (72, 46, 28)
        self.brow = (52, 36, 28)
        self.hair = (44, 32, 26)
        self.beard = None            # colour
        self.beard_len = 1.0
        self.beard_kind = "full"     # full | long | short
        self.mustache = True
        self.robe = (150, 120, 90)
        self.robe2 = None            # vertical stripe colour
        self.sash = (120, 52, 40)
        self.cloak = None
        self.sleeve = None
        self.head = "keffiyeh"       # keffiyeh | tall_hat | helmet | veil | cap | wrap
        self.head_c1 = (220, 205, 175)
        self.head_c2 = (120, 70, 50)
        self.face_w = 1.0
        self.jaw = 1.0
        self.wrinkles = 0.0
        self.female = False
        self.girth = 1.0
        self.ears = False
        self.apron = None
        self.armor = None
        self.lips = None
        self.seed = 0
        self.__dict__.update(kw)
        if self.sleeve is None:
            self.sleeve = self.robe
        if self.lips is None:
            self.lips = mixc(self.skin, (150, 60, 60), 0.35)


DEFAULT_POSE = dict(
    kneel=0.0, bow=0.0, turn=0.0, tilt=0.0, pitch=0.0, lean=0.0,
    gx=0.0, gy=0.0, blink=0.0, lid=0.0, squint=0.0,
    brow=0.0, brow_l=0.0, brow_r=0.0, worry=0.0, anger=0.0, furrow=0.0,
    open=0.0, bright=0.5, smile=0.0, sneer=0.0, press=0.0, mouth_w=1.0, jaw_clench=0.0,
    arm_l=(8, -8, 1, 1), arm_r=(8, -8, 1, 1), hand_l="open", hand_r="open", hand_rot_l=0, hand_rot_r=0,
    tears=0.0, tear_t=0.0, dirt=0.0, wet=0.0, ember=0.0, flush=0.0,
    breath=0.0, shake=0.0, walk=None, staff=False, shadow=1.0, rim=None, rim_a=0.0,
    light=None, light_a=0.0, sad=0.0, mood_t=0.0, shoulder=0.0, sigh=0.0, dim=0.0,
    gloss=0.0, glowhand=0.0, wide=0.0,
)


def mk(**kw):
    p = dict(DEFAULT_POSE)
    p.update(kw)
    return p


# ------------------------------------------------------------------ helpers
def _quad(p, a, c, b):
    p.moveTo(*a)
    p.quadTo(*c, *b)
    return p


def _dim(c, p):
    """Apply scene darkening / colour tint to a colour."""
    d = p.get("dim", 0.0)
    tint = p.get("tint")
    if tint is not None:
        c = mixc(c, tint[0], tint[1])
    if d:
        c = shade(c, 1 - d)
    return c


# ------------------------------------------------------------------ face parts
def draw_eye(cv, st, p, cx, cy, side, sx):
    """side: -1 screen-left eye, +1 screen-right eye. sx: width scale (perspective)."""
    rx = R * 0.2 * sx * (1.08 if st.female else 1.0)
    ry = R * 0.13 * (1.12 if st.female else 1.0) * (1 - 0.25 * max(0, p["pitch"])) * (1 + 0.3 * p["wide"])
    skin = _dim(st.skin, p)
    tilt = (0.12 if st.female else 0.04) * R * (-1)  # outer corner slightly up
    inner = (cx - side * rx, cy)
    outer = (cx + side * rx, cy + tilt)
    lft, rgt = (inner, outer) if side > 0 else (outer, inner)

    eye = skia.Path()
    eye.moveTo(*lft)
    eye.quadTo(cx, cy - ry * 1.6, *rgt)
    eye.quadTo(cx, cy + ry * 1.25, *lft)
    eye.close()

    cv.save()
    cv.clipPath(eye, skia.ClipOp.kIntersect, True)
    cv.drawPath(eye, paint(_dim((246, 240, 232), p)))
    # iris & pupil, following gaze
    ix = cx + p["gx"] * rx * 0.55
    iy = cy + p["gy"] * ry * 0.85 + ry * 0.05
    ri = R * 0.092 * (1.05 if st.female else 1.0)
    iris = _dim(st.iris, p)
    cv.drawCircle(ix, iy, ri, paint(shader=rad((ix, iy - ri * 0.2), ri * 1.1,
                                                  [shade(iris, 1.35), iris, shade(iris, 0.6)], [0, 0.6, 1])))
    cv.drawCircle(ix, iy, ri * 0.48, paint(_dim((12, 8, 8), p)))
    # upper lid shadow on the eyeball
    cv.drawPath(eye, paint((60, 30, 20), 0.18, stroke=ry * 0.5))
    # highlights: what makes eyes look alive
    hl = 0.95 * (1 - p.get("dim", 0) * 0.6)
    cv.drawCircle(ix - ri * 0.35, iy - ri * 0.38, ri * 0.27, paint((255, 255, 255), hl))
    cv.drawCircle(ix + ri * 0.32, iy + ri * 0.3, ri * 0.12, paint((255, 255, 255), hl * 0.7))
    if p["wet"] > 0:  # glistening, tear-filled lower rim
        cv.drawPath(_quad(skia.Path(), lft, (cx, cy + ry * 1.05), rgt),
                    paint((230, 240, 255), 0.75 * p["wet"], stroke=ry * 0.45))

    # eyelids
    u = clamp(max(p["blink"], p["lid"]))
    lidc = shade(skin, 0.93)
    up = skia.Path()
    up.moveTo(lft[0] - 3, lft[1] - ry * 3)
    up.lineTo(lft[0] - 3, lft[1])
    up.quadTo(cx, cy - ry * 1.6 + ry * 2.85 * u, rgt[0] + 3, rgt[1])
    up.lineTo(rgt[0] + 3, rgt[1] - ry * 3)
    up.close()
    cv.drawPath(up, paint(lidc))
    l = clamp(p["squint"]) * (1 - u)
    if l > 0:
        lo = skia.Path()
        lo.moveTo(lft[0] - 3, lft[1] + ry * 3)
        lo.lineTo(lft[0] - 3, lft[1])
        lo.quadTo(cx, cy + ry * 1.25 - ry * 2.0 * l, rgt[0] + 3, rgt[1])
        lo.lineTo(rgt[0] + 3, rgt[1] + ry * 3)
        lo.close()
        cv.drawPath(lo, paint(lidc))
    cv.restore()

    # lash line on the lid edge + crease
    line = _dim((38, 22, 18), p)
    edge = _quad(skia.Path(), (lft[0] - 1, lft[1]), (cx, cy - ry * 1.6 + ry * 2.85 * u), (rgt[0] + 1, rgt[1]))
    cv.drawPath(edge, paint(line, 0.95, stroke=R * (0.05 if st.female else 0.04)))
    if st.female:
        ox, oy = outer
        cv.drawLine(ox, oy, ox + side * R * 0.07, oy - R * 0.06 + u * R * 0.05, paint(line, 0.9, stroke=R * 0.03))
    if u < 0.85:
        crease = _quad(skia.Path(), (lft[0] + side * 0, lft[1] - ry * 0.5),
                       (cx, cy - ry * 2.3 + ry * 1.2 * u), (rgt[0], rgt[1] - ry * 0.5))
        cv.drawPath(crease, paint(shade(skin, 0.72), 0.5, stroke=R * 0.022))
    # lower lid hint
    low = _quad(skia.Path(), (lft[0] + 2, lft[1] + 2), (cx, cy + ry * 1.45), (rgt[0] - 2, rgt[1] + 2))
    cv.drawPath(low, paint(shade(skin, 0.8), 0.35, stroke=R * 0.018))


def draw_brow(cv, st, p, cx, cy, side, sx, raise_):
    worry, anger, furrow = p["worry"], p["anger"], p["furrow"]
    bw = R * 0.26 * sx
    base = cy - R * 0.3 - raise_ * R * 0.13 + anger * R * 0.05
    ix = cx - side * bw * 0.55 + side * furrow * R * 0.05
    iy = base - worry * R * 0.13 + anger * R * 0.1 + furrow * R * 0.03
    ox = cx + side * bw * 0.55
    oy = base + worry * R * 0.05 - anger * R * 0.05 + R * 0.02
    mx, my = (ix + ox) / 2, min(iy, oy) - R * 0.06 * (1 - 0.6 * anger)
    th = R * (0.075 if not st.female else 0.05)
    pth = _quad(skia.Path(), (ix, iy), (mx, my), (ox, oy))
    col = _dim(st.brow, p)
    cv.drawPath(pth, paint(col, 0.95, stroke=th))
    cv.drawCircle(ix, iy, th * 0.62, paint(col, 0.95))  # heavier inner end


def draw_mouth(cv, st, p, mx, my, sx):
    o = clamp(p["open"]) * (1 - 0.7 * p["jaw_clench"])
    smile, sneer, press = p["smile"], p["sneer"], p["press"]
    roundness = (1 - p["bright"]) * o
    hw = R * 0.2 * p["mouth_w"] * sx * (1 + 0.2 * smile - 0.3 * roundness + 0.15 * press)
    h = R * 0.32 * o
    cy_l = my - smile * R * 0.08 + sneer * R * 0.01
    cy_r = my - smile * R * 0.08 - sneer * R * 0.1
    lc, rc = (mx - hw, cy_l), (mx + hw, cy_r)
    lipdark = _dim(shade(st.lips, 0.55), p)
    if h < 1.2:
        pth = _quad(skia.Path(), lc, (mx + sneer * hw * 0.3, my + smile * R * 0.07 - sneer * R * 0.04), rc)
        cv.drawPath(pth, paint(lipdark, 0.95, stroke=R * (0.045 - 0.012 * press)))
        if not st.beard:
            lower = _quad(skia.Path(), (mx - hw * 0.5, my + R * 0.08), (mx, my + R * 0.13 + smile * R * 0.03),
                          (mx + hw * 0.5, my + R * 0.08))
            cv.drawPath(lower, paint(shade(_dim(st.skin, p), 0.8), 0.45, stroke=R * 0.03))
        if press > 0.2:
            for s, c in ((-1, lc), (1, rc)):
                cv.drawLine(c[0], c[1], c[0] + s * R * 0.03, c[1] + R * 0.04,
                            paint(lipdark, 0.6 * press, stroke=R * 0.025))
        return
    m = skia.Path()
    m.moveTo(*lc)
    m.quadTo(mx + sneer * hw * 0.3, my - h * 0.32 - sneer * R * 0.08 + smile * R * 0.02, *rc)
    m.quadTo(mx, my + h * 1.15 + smile * R * 0.04, *lc)
    m.close()
    cv.drawPath(m, paint(_dim((70, 24, 26), p)))
    cv.save()
    cv.clipPath(m, skia.ClipOp.kIntersect, True)
    if o > 0.22:
        cv.drawRect(skia.Rect.MakeLTRB(mx - hw, my - h, mx + hw, my - h * 0.32 + h * 0.28),
                    paint(_dim((236, 228, 214), p)))
    cv.drawOval(oval(mx, my + h * 1.0, hw * 0.6, h * 0.45), paint(_dim((168, 70, 72), p)))
    cv.restore()
    cv.drawPath(m, paint(lipdark, 0.9, stroke=R * 0.03))


def face_path(st, rx, ry):
    j = st.jaw
    f = skia.Path()
    f.moveTo(0, -ry)
    f.cubicTo(rx * 0.95, -ry, rx, -ry * 0.45, rx, -ry * 0.05)
    f.cubicTo(rx, ry * 0.42, rx * 0.66 * j, ry * 0.9, 0, ry)
    f.cubicTo(-rx * 0.66 * j, ry * 0.9, -rx, ry * 0.42, -rx, -ry * 0.05)
    f.cubicTo(-rx, -ry * 0.45, -rx * 0.95, -ry, 0, -ry)
    f.close()
    return f


def draw_beard(cv, st, p, rx, ry, fx, my, open_):
    col = _dim(st.beard, p)
    drop = open_ * R * 0.13
    L = {"full": R * 0.42, "long": R * 0.95, "short": R * 0.12}[st.beard_kind] * st.beard_len + drop
    b = skia.Path()
    top = R * 0.12
    b.moveTo(-rx * 0.99, top)
    b.cubicTo(-rx * 1.04, ry * 0.6, -rx * 0.62, ry + L * 0.9, fx * 0.4, ry + L)
    b.cubicTo(rx * 0.62, ry + L * 0.9, rx * 1.04, ry * 0.6, rx * 0.99, top)
    b.quadTo(rx * 0.92, R * 0.6, fx + R * 0.3, my - R * 0.02)
    b.quadTo(fx, my - R * 0.24, fx - R * 0.3, my - R * 0.02)
    b.quadTo(-rx * 0.92, R * 0.6, -rx * 0.99, top)
    b.close()
    cv.drawPath(b, paint(shader=lin((0, 0), (0, ry + L), [shade(col, 1.1), col, shade(col, 0.82)])))
    # strands
    cv.save()
    cv.clipPath(b, skia.ClipOp.kIntersect, True)
    rng = st.seed * 7.1
    for i in range(16):
        u = hashf(rng, i)
        x0 = lerp(-rx * 0.8, rx * 0.8, u)
        y0 = lerp(R * 0.5, ry + L * 0.6, hashf(rng, i, 2))
        x1 = x0 * 0.82 + fx * 0.1
        y1 = y0 + R * (0.25 + 0.3 * hashf(rng, i, 3))
        c2 = shade(col, 0.7) if i % 2 else shade(col, 1.35)
        cv.drawLine(x0, y0, x1, y1, paint(c2, 0.3, stroke=R * 0.018))
    cv.restore()
    if st.mustache:
        hw = R * 0.27
        ms = skia.Path()
        ms.moveTo(fx - hw * 1.15, my + R * 0.06 - p["smile"] * R * 0.06)
        ms.quadTo(fx - hw * 0.6, my - R * 0.26, fx, my - R * 0.17 - p["sneer"] * R * 0.05)
        ms.quadTo(fx + hw * 0.6, my - R * 0.26 - p["sneer"] * R * 0.08, fx + hw * 1.15,
                  my + R * 0.06 - p["smile"] * R * 0.06 - p["sneer"] * R * 0.1)
        ms.quadTo(fx + hw * 0.5, my - R * 0.06, fx, my - R * 0.07)
        ms.quadTo(fx - hw * 0.5, my - R * 0.06, fx - hw * 1.15, my + R * 0.06 - p["smile"] * R * 0.06)
        ms.close()
        cv.drawPath(ms, paint(shade(col, 0.92)))


def draw_head_back(cv, st, p, rx, ry):
    c1, c2 = _dim(st.head_c1, p), _dim(st.head_c2, p)
    if st.head in ("keffiyeh", "veil", "wrap"):
        k = skia.Path()
        k.moveTo(-rx * 1.22, -ry * 0.2)
        k.cubicTo(-rx * 1.3, -ry * 1.5, rx * 1.3, -ry * 1.5, rx * 1.22, -ry * 0.2)
        k.cubicTo(rx * 1.35, ry * 0.6, rx * 1.75, ry * 1.4, rx * 1.85, ry * 2.0)
        k.lineTo(-rx * 1.85, ry * 2.0)
        k.cubicTo(-rx * 1.75, ry * 1.4, -rx * 1.35, ry * 0.6, -rx * 1.22, -ry * 0.2)
        k.close()
        cv.drawPath(k, paint(shade(c1, 0.78)))
    elif st.head == "tall_hat":
        k = skia.Path()
        k.moveTo(-rx * 1.1, -ry * 0.3)
        k.lineTo(rx * 1.1, -ry * 0.3)
        k.lineTo(rx * 1.45, ry * 1.9)
        k.lineTo(-rx * 1.45, ry * 1.9)
        k.close()
        cv.drawPath(k, paint(shade(c1, 0.7)))


def draw_head_front(cv, st, p, rx, ry, fx):
    c1, c2 = _dim(st.head_c1, p), _dim(st.head_c2, p)
    if st.head == "keffiyeh":
        k = skia.Path()
        k.moveTo(-rx * 1.16, -ry * 0.05)
        k.cubicTo(-rx * 1.25, -ry * 1.55, rx * 1.25, -ry * 1.55, rx * 1.16, -ry * 0.05)
        k.cubicTo(rx * 1.02, -ry * 0.4, rx * 0.6, -ry * 0.62, fx * 0.2, -ry * 0.64)
        k.cubicTo(-rx * 0.6, -ry * 0.62, -rx * 1.02, -ry * 0.4, -rx * 1.16, -ry * 0.05)
        k.close()
        cv.drawPath(k, paint(shader=lin((0, -ry * 1.3), (0, -ry * 0.3), [shade(c1, 1.08), c1])))
        cv.save()
        cv.clipPath(k, skia.ClipOp.kIntersect, True)
        for i in range(-3, 4):
            x = i * rx * 0.3
            cv.drawLine(x, -ry * 1.5, x * 1.3, -ry * 0.3, paint(c2, 0.35, stroke=R * 0.03))
        cv.restore()
        band = _quad(skia.Path(), (-rx * 1.12, -ry * 0.62), (0, -ry * 1.02), (rx * 1.12, -ry * 0.62))
        cv.drawPath(band, paint(_dim((40, 28, 24), p), stroke=R * 0.13))
        cv.drawPath(band, paint(_dim((80, 60, 50), p), 0.6, stroke=R * 0.03))
    elif st.head == "tall_hat":
        top, bot = -ry * 2.05, -ry * 0.55
        k = skia.Path()
        k.moveTo(-rx * 0.98, bot)
        k.lineTo(-rx * 0.86, top)
        k.lineTo(rx * 0.86, top)
        k.lineTo(rx * 0.98, bot)
        k.close()
        cv.drawPath(k, paint(shader=lin((-rx, 0), (rx, 0), [shade(c1, 0.8), shade(c1, 1.15), c1, shade(c1, 0.7)],
                                         [0, 0.35, 0.6, 1])))
        for i in range(-3, 4):
            x = i * rx * 0.26
            cv.drawLine(x, top + 4, x * 1.05, bot - 4, paint(shade(c1, 0.65), 0.7, stroke=R * 0.022, cap="butt"))
        cv.drawRect(skia.Rect.MakeLTRB(-rx * 1.02, bot - R * 0.2, rx * 1.02, bot + R * 0.04), paint(c2))
        cv.drawRect(skia.Rect.MakeLTRB(-rx * 0.88, top, rx * 0.88, top + R * 0.08), paint(c2))
    elif st.head == "helmet":
        k = skia.Path()
        k.moveTo(-rx * 1.12, -ry * 0.28)
        k.cubicTo(-rx * 1.15, -ry * 1.45, rx * 1.15, -ry * 1.45, rx * 1.12, -ry * 0.28)
        k.close()
        cv.drawPath(k, paint(shader=lin((-rx, -ry), (rx, -ry * 0.3), [shade(c1, 1.3), c1, shade(c1, 0.6)])))
        cv.drawRect(skia.Rect.MakeLTRB(-rx * 1.14, -ry * 0.42, rx * 1.14, -ry * 0.24), paint(shade(c1, 0.75)))
        for s in (-1, 1):  # cheek guards
            g = skia.Path()
            g.moveTo(s * rx * 1.12, -ry * 0.3)
            g.lineTo(s * rx * 0.86, -ry * 0.3)
            g.quadTo(s * rx * 0.8, ry * 0.3, s * rx * 0.68, ry * 0.52)
            g.lineTo(s * rx * 1.04, ry * 0.4)
            g.close()
            cv.drawPath(g, paint(shade(c1, 0.85)))
        cv.drawLine(0, -ry * 1.18, 0, -ry * 1.48, paint(c2, stroke=R * 0.1))
    elif st.head in ("veil", "wrap"):
        k = skia.Path()
        k.moveTo(-rx * 1.12, ry * 0.25)
        k.cubicTo(-rx * 1.3, -ry * 1.6, rx * 1.3, -ry * 1.6, rx * 1.12, ry * 0.25)
        k.cubicTo(rx * 1.0, -ry * 0.3, rx * 0.65, -ry * 0.68, fx * 0.2, -ry * 0.7)
        k.cubicTo(-rx * 0.65, -ry * 0.68, -rx * 1.0, -ry * 0.3, -rx * 1.12, ry * 0.25)
        k.close()
        cv.drawPath(k, paint(shader=lin((0, -ry * 1.3), (0, ry * 0.3), [shade(c1, 1.12), c1, shade(c1, 0.85)])))
        edge = _quad(skia.Path(), (-rx * 1.0, -ry * 0.25), (0, -ry * 0.98), (rx * 1.0, -ry * 0.25))
        cv.drawPath(edge, paint(c2, 0.8, stroke=R * 0.05))
    elif st.head == "cap":
        k = skia.Path()
        k.moveTo(-rx * 1.04, -ry * 0.45)
        k.cubicTo(-rx * 1.0, -ry * 1.32, rx * 1.0, -ry * 1.32, rx * 1.04, -ry * 0.45)
        k.quadTo(0, -ry * 0.62, -rx * 1.04, -ry * 0.45)
        k.close()
        cv.drawPath(k, paint(c1))
        cv.drawPath(_quad(skia.Path(), (-rx * 1.04, -ry * 0.47), (0, -ry * 0.64), (rx * 1.04, -ry * 0.47)),
                    paint(c2, stroke=R * 0.08))


def draw_hair(cv, st, p, rx, ry, fx):
    col = _dim(st.hair, p)
    if st.head in ("cap", "keffiyeh", "wrap"):
        for s in (-1, 1):
            hp = skia.Path()
            hp.moveTo(s * rx * 1.02, -ry * 0.55)
            hp.quadTo(s * rx * 1.12, -ry * 0.1, s * rx * 0.98, ry * 0.12)
            hp.lineTo(s * rx * 0.86, -ry * 0.1)
            hp.quadTo(s * rx * 0.86, -ry * 0.45, s * rx * 0.7, -ry * 0.62)
            hp.close()
            cv.drawPath(hp, paint(col))
    if st.head == "veil":
        hp = skia.Path()
        hp.moveTo(-rx * 0.92, -ry * 0.3)
        hp.quadTo(-rx * 0.5, -ry * 0.82, fx * 0.3, -ry * 0.62)
        hp.quadTo(rx * 0.5, -ry * 0.82, rx * 0.92, -ry * 0.3)
        hp.quadTo(rx * 0.7, -ry * 0.8, 0, -ry * 0.92)
        hp.quadTo(-rx * 0.7, -ry * 0.8, -rx * 0.92, -ry * 0.3)
        hp.close()
        cv.drawPath(hp, paint(col))


def draw_head(cv, st, p, front=True):
    """Head centred at (0,0)."""
    rx, ry = R * 0.86 * st.face_w, R * 1.08
    turn, pitch = p["turn"], p["pitch"]
    fx = turn * R * 0.3
    fy = pitch * R * 0.3
    skin = _dim(st.skin, p)
    if p["flush"]:
        skin = mixc(skin, (200, 70, 60), 0.25 * p["flush"])
    draw_head_back(cv, st, p, rx, ry)
    if st.ears:
        for s in (-1, 1):
            cv.drawOval(oval(s * rx * 0.98 - fx * 0.3, R * 0.05, R * 0.14, R * 0.24), paint(shade(skin, 0.9)))
    fp = face_path(st, rx, ry)
    cv.drawPath(fp, paint(shader=rad((fx - rx * 0.25, -ry * 0.35), ry * 1.6,
                                      [shade(skin, 1.1), skin, shade(skin, 0.78)], [0, 0.55, 1])))
    cv.save()
    cv.clipPath(fp, skia.ClipOp.kIntersect, True)
    # shading on the turned-away side
    side = -1 if turn > 0 else 1
    if abs(turn) > 0.02:
        cv.drawRect(skia.Rect.MakeLTRB(-rx, -ry, rx, ry), paint(
            shader=lin((side * rx, 0), (side * rx * 0.2, 0), [(shade(skin, 0.6), 0.55 * abs(turn)),
                                                             (shade(skin, 0.6), 0.0)])))
    # cheeks
    cheek = (215, 110, 95) if not p["flush"] else (215, 70, 60)
    for s in (-1, 1):
        cv.drawOval(oval(fx + s * R * 0.48, R * 0.28 + fy, R * 0.2, R * 0.12),
                    paint(cheek, 0.18 + 0.25 * p["flush"] + (0.1 if st.female else 0), blur=R * 0.08))
    # wrinkles
    if st.wrinkles:
        wc = shade(skin, 0.62)
        a = 0.55 * st.wrinkles
        for k in range(3):
            y = -R * 0.55 - k * R * 0.12 + fy - p["worry"] * R * 0.05
            cv.drawPath(_quad(skia.Path(), (fx - R * 0.32, y), (fx, y - R * 0.06), (fx + R * 0.32, y)),
                        paint(wc, a * (1 - k * 0.2), stroke=R * 0.022))
        for s in (-1, 1):
            cv.drawPath(_quad(skia.Path(), (fx + s * R * 0.2, R * 0.28 + fy), (fx + s * R * 0.36, R * 0.45 + fy),
                              (fx + s * R * 0.3, R * 0.68 + fy)), paint(wc, a, stroke=R * 0.025))
            ex = fx + s * R * 0.36 * st.face_w + s * R * 0.24
            for k in (-1, 0, 1):
                cv.drawLine(ex, -R * 0.08 + fy, ex + s * R * 0.09, -R * 0.08 + fy + k * R * 0.06,
                            paint(wc, a * 0.8, stroke=R * 0.015))
        if p["anger"] > 0 or p["furrow"] > 0:  # glabella lines
            k = max(p["anger"], p["furrow"])
            for s in (-1, 1):
                cv.drawLine(fx + s * R * 0.05, -R * 0.38 + fy, fx + s * R * 0.03, -R * 0.24 + fy,
                            paint(wc, 0.7 * k, stroke=R * 0.022))
    # dirt and tear tracks
    if p["dirt"] > 0:
        for i in range(9):
            dx = lerp(-rx * 0.85, rx * 0.85, hashf(st.seed, i, 11))
            dy = lerp(-ry * 0.6, ry * 0.8, hashf(st.seed, i, 12))
            cv.drawOval(oval(dx, dy, R * (0.12 + 0.18 * hashf(i, 3)), R * (0.07 + 0.1 * hashf(i, 4))),
                        paint((92, 64, 40), 0.35 * p["dirt"], blur=R * 0.06))
    cv.restore()

    ey = -R * 0.08 + fy
    sep = R * 0.37 * st.face_w
    sl = 1 - 0.28 * max(0, turn) + 0.05 * max(0, -turn)
    sr_ = 1 - 0.28 * max(0, -turn) + 0.05 * max(0, turn)
    lx = fx * 1.05 - sep * (1 - 0.15 * max(0, turn))
    rxe = fx * 1.05 + sep * (1 - 0.15 * max(0, -turn))
    my = R * 0.56 + fy * 0.9

    # tear tracks through the grime
    if p["tears"] > 0:
        for s, ex in ((-1, lx), (1, rxe)):
            ln = R * 0.75 * clamp(p["tears"] * 1.3)
            tr = _quad(skia.Path(), (ex + s * R * 0.04, ey + R * 0.14), (ex - s * R * 0.03, ey + ln * 0.5),
                       (ex + s * R * 0.02, ey + R * 0.14 + ln))
            cv.drawPath(tr, paint(shade(skin, 1.12), 0.7 * clamp(p["dirt"] + 0.3), stroke=R * 0.07))
            cv.drawPath(tr, paint((215, 232, 250), 0.55 * clamp(p["tears"] * 1.5), stroke=R * 0.035))
            # a drop sliding down
            ph = (p["tear_t"] * 0.45 + (0.5 if s > 0 else 0)) % 1.0
            if p["tears"] > 0.3:
                dy = ey + R * 0.14 + ln * ph
                cv.drawCircle(ex + s * R * 0.01, dy, R * 0.045, paint((225, 238, 255), 0.85 * (1 - ph * 0.6)))
                cv.drawCircle(ex + s * R * 0.0 - R * 0.012, dy - R * 0.015, R * 0.015, paint((255, 255, 255), 0.9))

    # nose
    nx = fx * 1.35
    ny = R * 0.3 + fy * 0.8
    nose = skia.Path()
    nose.moveTo(fx * 1.05 + R * 0.04 * (1 if turn >= 0 else -1), -R * 0.02 + fy)
    nose.quadTo(nx + R * 0.12 * (1 if turn >= 0 else -1), ny - R * 0.05, nx + R * 0.02, ny + R * 0.03)
    cv.drawPath(nose, paint(shade(skin, 0.7), 0.55, stroke=R * 0.035))
    cv.drawPath(_quad(skia.Path(), (nx - R * 0.12, ny), (nx, ny + R * 0.09), (nx + R * 0.12, ny)),
                paint(shade(skin, 0.62), 0.7, stroke=R * 0.035))
    cv.drawCircle(nx - R * 0.03, ny - R * 0.06, R * 0.05, paint(shade(skin, 1.25), 0.35, blur=R * 0.02))

    # eyes and brows
    draw_eye(cv, st, p, lx, ey, -1, sl)
    draw_eye(cv, st, p, rxe, ey, 1, sr_)
    draw_brow(cv, st, p, lx, ey, -1, sl, p["brow"] + p["brow_l"])
    draw_brow(cv, st, p, rxe, ey, 1, sr_, p["brow"] + p["brow_r"])

    if st.beard:
        draw_beard(cv, st, p, rx, ry, fx * 1.1, my, p["open"])
    draw_mouth(cv, st, p, fx * 1.1, my + p["open"] * R * 0.04, 1 - 0.15 * abs(turn))
    draw_hair(cv, st, p, rx, ry, fx)
    draw_head_front(cv, st, p, rx, ry, fx)


# ------------------------------------------------------------------ body
def arm_points(sx, sy, side, a, e, f1=1.0, f2=1.0, L1=108, L2=100):
    ar = math.radians(a)
    ex = sx + side * math.sin(ar) * L1 * f1
    ey = sy + math.cos(ar) * L1 * f1
    br = math.radians(a + e)
    wx = ex + side * math.sin(br) * L2 * f2
    wy = ey + math.cos(br) * L2 * f2
    return (ex, ey), (wx, wy), math.atan2(wy - ey, wx - ex)


def draw_hand(cv, st, p, x, y, ang, kind, side, s=1.0):
    skin = _dim(st.skin, p)
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang) - 90)
    pa = paint(skin)
    edge = paint(shade(skin, 0.7), 0.6, stroke=2.2)
    if kind == "fist":
        cv.drawOval(oval(0, 10 * s, 13 * s, 14 * s), pa)
        cv.drawOval(oval(0, 10 * s, 13 * s, 14 * s), edge)
        for k in range(3):
            cv.drawLine(-8 * s + k * 7 * s, 18 * s, -8 * s + k * 7 * s, 22 * s, paint(shade(skin, 0.7), 0.6, stroke=1.6))
    elif kind == "point":
        cv.drawOval(oval(0, 9 * s, 12 * s, 13 * s), pa)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-3.5 * s, 12 * s, 3.5 * s, 40 * s), 4 * s, 4 * s, pa)
        cv.drawOval(oval(0, 9 * s, 12 * s, 13 * s), edge)
    else:  # open / grip
        spread = 0.25 if kind == "open" else 0.05
        cv.drawOval(oval(0, 11 * s, 12 * s, 14 * s), pa)
        for k in range(4):
            ang2 = (k - 1.5) * spread
            fx, fy = math.sin(ang2) * 20 * s, 14 * s + math.cos(ang2) * 18 * s
            fl = (18 - abs(k - 1.5) * 3) * s * (0.7 if kind == "grip" else 1)
            cv.save()
            cv.translate(-7.5 * s + k * 5 * s, 18 * s)
            cv.rotate(-math.degrees(ang2))
            cv.drawRoundRect(skia.Rect.MakeLTRB(-2.6 * s, -4 * s, 2.6 * s, fl), 2.6 * s, 2.6 * s, pa)
            cv.restore()
        cv.drawLine(-side * 10 * s, 8 * s, -side * 15 * s, 22 * s, paint(skin, stroke=6 * s))
    cv.restore()


def draw_arm(cv, st, p, which, sx, sy, front=True):
    side = -1 if which == "l" else 1
    a, e, f1, f2 = p["arm_" + which]
    elbow, wrist, ang = arm_points(sx, sy, side, a, e, f1, f2)
    sl = _dim(st.sleeve, p)
    path = skia.Path()
    path.moveTo(sx, sy)
    path.lineTo(*elbow)
    path.lineTo(*wrist)
    cv.drawPath(path, paint(shade(sl, 0.75), stroke=36, join="round"))
    cv.drawPath(path, paint(sl, stroke=30, join="round"))
    # sleeve fold highlight
    cv.drawLine(sx, sy + 4, elbow[0], elbow[1], paint(shade(sl, 1.15), 0.45, stroke=8))
    # cuff
    cx = lerp(elbow[0], wrist[0], 0.88)
    cy = lerp(elbow[1], wrist[1], 0.88)
    cv.drawLine(cx, cy, wrist[0], wrist[1], paint(shade(sl, 0.7), stroke=31, cap="butt"))
    hx = wrist[0] + math.cos(ang) * 2
    hy = wrist[1] + math.sin(ang) * 2
    draw_hand(cv, st, p, hx, hy, ang + math.radians(p["hand_rot_" + which]), p["hand_" + which], side)
    return (hx, hy)


def robe_path(SW, SY, WY, HW, hem_y, waist_w):
    r = skia.Path()
    r.moveTo(-SW, SY + 10)
    r.cubicTo(-SW - 6, SY - 6, -SW * 0.6, SY - 14, -SW * 0.3, SY - 14)
    r.lineTo(SW * 0.3, SY - 14)
    r.cubicTo(SW * 0.6, SY - 14, SW + 6, SY - 6, SW, SY + 10)
    r.cubicTo(SW + 4, SY + 80, waist_w + 2, WY - 30, waist_w, WY)
    r.cubicTo(waist_w + 10, WY + 60, HW, hem_y - 60, HW, hem_y)
    r.quadTo(0, hem_y + 10, -HW, hem_y)
    r.cubicTo(-HW, hem_y - 60, -waist_w - 10, WY + 60, -waist_w, WY)
    r.cubicTo(-waist_w - 2, WY - 30, -SW - 4, SY + 80, -SW, SY + 10)
    r.close()
    return r


def draw_person(cv, st, p, t=0.0):
    """Draw a full figure. Returns dict of useful world-space anchor points (local coords)."""
    g = st.girth
    kneel, bow = p["kneel"], p["bow"]
    breath = math.sin(t * 2 * math.pi / 4.2 + st.seed) * 2.0 * (1 + p["breath"])
    shake = p["shake"]
    jx = (math.sin(t * 53.0 + st.seed) + math.sin(t * 37.0)) * 0.6 * shake
    off = kneel * 172
    bob = 0.0
    if p["walk"] is not None:
        bob = abs(math.sin(p["walk"] * math.pi)) * 7
    sigh = p["sigh"]
    SY = -372 + off + bow * 16 - breath - bob - sigh * 8
    SW = 62 * g * (1 - 0.1 * bow)
    WY = -228 + off * 0.95 - bob * 0.5
    hem = -8
    HW = 86 * g + kneel * 52
    ww = 52 * g + kneel * 20
    HY = SY - 78 + bow * 30

    cv.save()
    cv.translate(jx, 0)
    # ground shadow
    if p["shadow"]:
        cv.drawOval(oval(0, 0, HW * 1.3, 14), paint((0, 0, 0), 0.28 * p["shadow"], blur=8))
    lean = p["lean"]
    cv.save()
    cv.rotate(lean)

    # cloak behind
    if st.cloak:
        ck = _dim(st.cloak, p)
        c = skia.Path()
        c.moveTo(-SW - 6, SY + 6)
        c.cubicTo(-SW - 30, SY + 140, -HW - 30, hem - 160, -HW - 26, hem - 4)
        c.lineTo(HW + 26, hem - 4)
        c.cubicTo(HW + 30, hem - 160, SW + 30, SY + 140, SW + 6, SY + 6)
        c.close()
        cv.drawPath(c, paint(shade(ck, 0.8)))

    # feet / sandals
    fcol = _dim((96, 64, 40), p)
    skin = _dim(st.skin, p)
    if kneel < 0.5:
        if p["walk"] is not None:
            ph = math.sin(p["walk"] * math.pi)
            for s, k in ((-1, ph), (1, -ph)):
                fy = -2 + k * 6
                sc = 1 + 0.18 * k
                cv.drawOval(oval(s * 24, fy, 17 * sc, 9 * sc), paint(skin))
                cv.drawOval(oval(s * 24, fy + 3, 19 * sc, 7 * sc), paint(fcol))
        else:
            for s in (-1, 1):
                cv.drawOval(oval(s * 26, -3, 18, 9), paint(skin))
                cv.drawOval(oval(s * 26, 0, 20, 7), paint(fcol))

    # neck (behind the robe's neckline)
    cv.drawRect(skia.Rect.MakeLTRB(-R * 0.3, HY + 20, R * 0.3, SY + 10), paint(shade(skin, 0.78)))
    # robe
    robe = _dim(st.robe, p)
    rp = robe_path(SW, SY, WY, HW, hem, ww)
    cv.drawPath(rp, paint(shader=lin((-HW, 0), (HW, 0), [shade(robe, 0.82), shade(robe, 1.06), robe,
                                                         shade(robe, 0.78)], [0, 0.35, 0.65, 1])))
    cv.save()
    cv.clipPath(rp, skia.ClipOp.kIntersect, True)
    if st.robe2:
        r2 = _dim(st.robe2, p)
        for s in (-1, 1):
            cv.drawLine(s * 16, SY, s * 22 * (1 + kneel), hem, paint(r2, 0.85, stroke=10, cap="butt"))
    # folds
    for i, x in enumerate((-0.5, -0.15, 0.25, 0.55)):
        cv.drawLine(x * ww, WY + 10, x * HW * 1.05, hem, paint(shade(robe, 0.7), 0.35, stroke=3))
    if st.apron:
        ap = _dim(st.apron, p)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-ww * 0.85, WY - 70, ww * 0.85, hem - 30), 14, 14, paint(ap))
        for i in range(5):
            cv.drawCircle(lerp(-ww * 0.6, ww * 0.6, hashf(i, 1)), lerp(WY - 50, hem - 50, hashf(i, 2)),
                          4 + 5 * hashf(i, 3), paint(shade(ap, 0.7), 0.6))
    if st.armor:
        ar = _dim(st.armor, p)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-SW * 0.85, SY + 4, SW * 0.85, WY + 10), 12, 12, paint(ar))
        for k in range(4):
            y = SY + 30 + k * (WY - SY - 30) / 4
            cv.drawLine(-SW * 0.8, y, SW * 0.8, y, paint(shade(ar, 0.7), 0.8, stroke=3))
    # neckline
    nk = skia.Path()
    nk.moveTo(-22, SY - 13)
    nk.quadTo(0, SY + 34, 22, SY - 13)
    cv.drawPath(nk, paint(shade(skin, 0.75)))
    cv.drawPath(nk, paint(shade(robe, 0.6), stroke=3))
    # sash
    sash = _dim(st.sash, p)
    cv.drawRect(skia.Rect.MakeLTRB(-ww - 8, WY - 16, ww + 8, WY + 6), paint(sash))
    cv.drawRect(skia.Rect.MakeLTRB(-ww - 8, WY - 16, ww + 8, WY - 11), paint(shade(sash, 1.2), 0.6))
    cv.restore()

    # cloak front edges
    if st.cloak:
        ck = _dim(st.cloak, p)
        for s in (-1, 1):
            e = skia.Path()
            e.moveTo(s * (SW - 4), SY - 2)
            e.cubicTo(s * (SW + 2), SY + 120, s * (HW - 4), hem - 140, s * (HW + 22), hem - 4)
            e.lineTo(s * (HW - 14), hem - 4)
            e.cubicTo(s * (HW - 34), hem - 150, s * (SW - 26), SY + 120, s * (SW - 34), SY - 6)
            e.close()
            cv.drawPath(e, paint(ck))
            cv.drawPath(e, paint(shade(ck, 0.7), 0.7, stroke=2))

    # ember of the divine fire, glowing through the chest
    if p["ember"] > 0:
        em = p["ember"]
        fl = 1 + 0.12 * math.sin(t * 9.0) + 0.08 * math.sin(t * 23.0)
        glow(cv, 0, SY + 58, (50 + 110 * em) * fl, (255, 140, 50), 0.55 * em, blend="screen")
        glow(cv, 0, SY + 58, (10 + 22 * em) * fl, (255, 225, 160), 0.75 * min(1, em * 1.4))

    # rim light (backlit shots)
    if p["rim"] is not None and p["rim_a"] > 0:
        s = p["rim"]
        cv.save()
        cv.clipPath(rp, skia.ClipOp.kIntersect, True)
        cv.drawPath(rp, paint(p.get("rim_c", (255, 200, 140)), p["rim_a"], stroke=10, blur=4))
        cv.restore()

    # head
    cv.save()
    cv.translate(0, HY)
    cv.rotate(p["tilt"])
    draw_head(cv, st, p)
    cv.restore()

    # arms
    hl = draw_arm(cv, st, p, "l", -SW + 6, SY + 18)
    hr = draw_arm(cv, st, p, "r", SW - 6, SY + 18)

    if p["staff"]:
        sx, sy = hl
        cv.drawLine(sx - 6, sy - 210, sx + 4, -4 if kneel < 0.5 else -60,
                    paint(_dim((110, 76, 44), p), stroke=11))
        cv.drawLine(sx - 8, sy - 210, sx - 2, sy - 230, paint(_dim((90, 60, 34), p), stroke=12))
        draw_hand(cv, st, p, sx, sy, p.get("_staff_ang", math.pi / 2), "grip", -1)

    if p["glowhand"] > 0:  # the presence's warmth resting on his shoulders
        gh = p["glowhand"]
        cv.save()
        cv.translate(0, SY + 4)
        cv.scale(1.0, 0.42)
        glow(cv, 0, 0, SW * 2.6, (255, 205, 130), 0.42 * gh, blend="screen")
        cv.restore()
        glow(cv, 0, SY - 40, 240, (255, 190, 110), 0.18 * gh, blend="screen")
    cv.restore()
    cv.restore()
    return {"head": (jx, HY), "chest": (jx, SY + 58), "hand_l": hl, "hand_r": hr, "shoulder_y": SY,
            "SW": SW}
