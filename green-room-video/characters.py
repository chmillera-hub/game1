"""Cartoon characters: heads with expressive eyes, brows and lip-sync,
plus seated/standing/running bodies built from simple shapes."""
import math, random
import skia
from common import *

# ---------------------------------------------------------------- expressions

NEUTRAL = dict(gx=0.0, gy=0.0, turn=0.0, tilt=0.0, blink=0.0, lid=0.12, lidtilt=0.0,
               squint=0.0, browL=0.0, browR=0.0, browA=0.0, mouth=0.0, smile=0.0, mw=1.0,
               skew=0.0, pupil=1.0, sweat=0.0, blush=0.0, twitch=0.0, glisten=0.0,
               teeth=0.0, red=0.0, tears=0.0, cheek=0.0)

EXPR = {
    "neutral": {},
    "smile": dict(smile=0.65, squint=0.2, browL=0.1, browR=0.1),
    "grin": dict(smile=1.0, squint=0.35, browL=0.25, browR=0.25, teeth=1, mouth=0.25),
    "smug": dict(smile=0.45, lid=0.38, browL=0.35, browR=-0.1, skew=0.35),
    "skeptical": dict(browL=0.75, browR=-0.35, lid=0.3, smile=-0.15, skew=0.3),
    "confused": dict(browL=0.65, browR=-0.25, browA=-0.25, smile=-0.3, skew=-0.35, lid=0.05),
    "shocked": dict(lid=-0.3, browL=0.95, browR=0.95, pupil=0.55, mouth=0.55, smile=-0.25),
    "angry": dict(browA=1.0, browL=-0.35, browR=-0.35, lid=0.28, lidtilt=0.7, smile=-0.6, squint=0.25),
    "furious": dict(browA=1.2, browL=-0.45, browR=-0.45, lid=0.2, lidtilt=0.9, smile=-0.8, squint=0.3, red=0.8, teeth=1),
    "annoyed": dict(lid=0.48, browA=0.35, smile=-0.35),
    "sad": dict(browA=-0.85, browL=0.3, browR=0.3, smile=-0.5, lid=0.3, lidtilt=-0.5),
    "serene": dict(lid=0.4, smile=0.42, browL=0.12, browR=0.12, squint=0.18),
    "kind": dict(lid=0.25, smile=0.55, browA=-0.2, browL=0.2, browR=0.2, squint=0.25),
    "compassion": dict(lid=0.3, smile=0.2, browA=-0.45, browL=0.25, browR=0.25, glisten=0.7),
    "awkward": dict(smile=0.35, mw=1.3, browA=-0.55, browL=0.4, browR=0.4, sweat=1, teeth=1, mouth=0.12),
    "deadpan": dict(lid=0.55, smile=-0.1, browL=-0.1, browR=-0.1),
    "nervous": dict(browA=-0.65, browL=0.45, browR=0.45, smile=-0.15, sweat=1, mw=0.75, lid=0.0),
    "excited": dict(browL=0.65, browR=0.65, smile=0.9, lid=-0.1, teeth=1, mouth=0.15),
    "tired": dict(lid=0.62, browA=-0.3, browL=0.1, browR=0.1, smile=-0.2),
    "stern": dict(browA=0.6, browL=-0.2, browR=-0.2, lid=0.3, smile=-0.35),
    "sleepy": dict(lid=0.72, smile=0.0),
    "hopeful": dict(browA=-0.35, browL=0.35, browR=0.35, smile=0.45, glisten=0.8, lid=0.1),
    "wince": dict(squint=0.8, lid=0.5, browA=-0.4, smile=-0.6, mw=1.2, teeth=1, mouth=0.15),
}


def expr(name, **over):
    d = dict(NEUTRAL)
    d.update(EXPR[name])
    d.update(over)
    return d


def face_blend(a, b, u):
    return {k: lerp(a.get(k, NEUTRAL[k]), b.get(k, NEUTRAL[k]), u) for k in NEUTRAL}


class FaceTrack:
    """Expression keyframes with soft cross-fades: list of (t, name or dict[, dur])."""

    def __init__(self, keys, dur=0.35):
        self.keys = []
        for k in sorted(keys, key=lambda k: k[0]):
            v = expr(k[1]) if isinstance(k[1], str) else k[1]
            self.keys.append((k[0], v, k[2] if len(k) > 2 else dur))

    def __call__(self, t):
        cur = self.keys[0][1]
        for (t0, v, d) in self.keys[1:]:
            if t < t0:
                break
            u = smooth(prog(t, t0, t0 + d))
            cur = face_blend(cur, v, u)
        return dict(cur)


class Blinker:
    def __init__(self, seed, t_end=400, mean=3.6):
        r = random.Random(seed)
        self.times = []
        t = r.uniform(0.3, 2.5)
        while t < t_end:
            self.times.append(t)
            if r.random() < 0.18:                      # occasional double blink
                self.times.append(t + 0.32)
            t += r.uniform(mean * 0.45, mean * 1.5)

    def __call__(self, t, extra=()):
        v = 0.0
        for bt in list(self.times) + list(extra):
            if bt - 0.1 < t < bt + 0.25:
                d = t - bt
                v = max(v, 1 - abs(d - 0.06) / 0.1 if d > -0.04 else 0)
        return clamp(v)


# ---------------------------------------------------------------- appearance

class Look:
    def __init__(self, **k):
        self.skin = "#f1c7a3"
        self.hair = "#3a2a20"
        self.brow = None
        self.iris = "#4a3426"
        self.hw, self.hh, self.jaw = 72, 84, 0.62
        self.eye_rx, self.eye_ry, self.eye_sep, self.eye_y = 13.5, 15.5, 31, -6
        self.hair_style = "short"
        self.beard = None
        self.glasses = False
        self.outfit = "suit"
        self.c1 = "#22304d"     # main garment
        self.c2 = "#f4f4f4"     # shirt
        self.c3 = "#c0392b"     # tie / accent
        self.sw = 104           # shoulder half-width
        self.lipcol = None
        self.freckles = False
        self.wrinkles = False
        self.earrings = False
        self.airpods = False
        self.lashes = False
        self.nose = 1.0
        self.__dict__.update(k)
        if self.brow is None:
            self.brow = shade(self.hair, -0.25)


def S(x):
    return x


# ---------------------------------------------------------------- head

def head_path(hw, hh, jaw):
    p = skia.Path()
    p.moveTo(0, -hh)
    p.cubicTo(hw * 0.62, -hh, hw, -hh * 0.62, hw, -hh * 0.1)
    p.cubicTo(hw, hh * 0.42, hw * jaw * 1.05, hh * 0.92, 0, hh)
    p.cubicTo(-hw * jaw * 1.05, hh * 0.92, -hw, hh * 0.42, -hw, -hh * 0.1)
    p.cubicTo(-hw, -hh * 0.62, -hw * 0.62, -hh, 0, -hh)
    p.close()
    return p


def nrm_path(pts, hw, hh, dx=0.0, close=True, tension=0.5):
    return smooth_path([(x * hw + dx, y * hh) for x, y in pts], close, tension)


def draw_hair_back(cv, L, f, t):
    hw, hh = L.hw, L.hh
    col = L.hair
    if L.hair_style == "jesus":
        sway = noise1(t * 0.4, 3) * 0.03
        cv.drawPath(nrm_path([(-1.05, -0.6), (-0.6, -1.12), (0.6, -1.12), (1.05, -0.6), (1.25, 0.3),
                              (1.35 + sway, 1.1), (1.05, 1.55), (0.5, 1.2), (-0.5, 1.2), (-1.05, 1.55),
                              (-1.35 + sway, 1.1), (-1.25, 0.3)], hw, hh), paint(shade(col, -0.12)))
    elif L.hair_style == "ponytail":
        sw = noise1(t * 0.7, 9) * 0.12
        cv.drawPath(nrm_path([(0.6, -0.75), (1.2, -0.55), (1.45 + sw, 0.1), (1.35 + sw, 0.8), (1.15 + sw, 1.05),
                              (1.1, 0.5), (0.95, -0.1)], hw, hh), paint(shade(col, -0.1)))
        ellipse(cv, 0.98 * hw, -0.6 * hh, 10, 12, paint(L.c3))
    elif L.hair_style == "bun":
        circle(cv, 0, -hh * 1.12, hw * 0.42, paint(shade(col, -0.05)))
        cv.drawPath(nrm_path([(-0.25, -1.3), (0.0, -1.42), (0.25, -1.3)], hw, hh, close=False),
                    paint(shade(col, 0.15), stroke=4))
    elif L.hair_style in ("messy", "quiff", "short", "ceo", "bob"):
        pass
    if L.hair_style == "bob":
        cv.drawPath(nrm_path([(-1.12, -0.4), (-0.7, -1.1), (0.7, -1.1), (1.12, -0.4), (1.18, 0.55),
                              (0.9, 0.7), (-0.9, 0.7), (-1.18, 0.55)], hw, hh), paint(shade(col, -0.1)))


def draw_hair_front(cv, L, f, t):
    hw, hh = L.hw, L.hh
    dx = f["turn"] * hw * 0.1
    col = L.hair
    hi = shade(col, 0.18)
    st = L.hair_style
    if st == "ceo":
        # receding slicked silver hair
        cv.drawPath(nrm_path([(-1.02, -0.05), (-1.04, -0.55), (-0.75, -0.95), (-0.2, -1.07), (0.35, -1.05),
                              (0.8, -0.9), (1.04, -0.55), (1.02, -0.05), (0.92, -0.35), (0.6, -0.7),
                              (0.15, -0.78), (-0.35, -0.72), (-0.75, -0.55), (-0.93, -0.3)], hw, hh, dx * 0.5),
                    paint(col))
        for k in range(4):
            y0 = -0.9 + k * 0.07
            cv.drawPath(nrm_path([(-0.7, y0 + 0.12), (-0.1, y0 - 0.05), (0.6, y0 + 0.05)], hw, hh, dx * 0.5, False),
                        paint(hi, 0.6, stroke=2.5))
    elif st == "bun":
        cv.drawPath(nrm_path([(-1.03, -0.05), (-1.05, -0.6), (-0.65, -1.02), (0.0, -1.1), (0.65, -1.02),
                              (1.05, -0.6), (1.03, -0.05), (0.88, -0.45), (0.45, -0.72), (0.04, -0.72),
                              (0.0, -0.8), (-0.04, -0.72), (-0.45, -0.72), (-0.88, -0.45)], hw, hh, dx), paint(col))
        cv.drawPath(nrm_path([(-0.6, -0.92), (-0.25, -0.98)], hw, hh, dx, False), paint(hi, 0.6, stroke=3))
    elif st == "quiff":
        cv.drawPath(nrm_path([(-1.03, -0.1), (-1.06, -0.62), (-0.8, -1.0), (-0.3, -1.25), (0.35, -1.38),
                              (0.85, -1.2), (1.08, -0.7), (1.03, -0.1), (0.9, -0.5), (0.55, -0.62),
                              (0.1, -0.66), (-0.4, -0.7), (-0.85, -0.5)], hw, hh, dx), paint(col))
        cv.drawPath(nrm_path([(-0.4, -1.05), (0.2, -1.25), (0.7, -1.1)], hw, hh, dx, False), paint(hi, 0.8, stroke=4))
        cv.drawPath(nrm_path([(-0.2, -0.85), (0.35, -1.0), (0.8, -0.85)], hw, hh, dx, False), paint(hi, 0.5, stroke=3))
    elif st == "ponytail":
        cv.drawPath(nrm_path([(-1.04, -0.05), (-1.06, -0.6), (-0.7, -1.02), (0.0, -1.12), (0.7, -1.02),
                              (1.06, -0.6), (1.04, -0.05), (0.92, -0.42), (0.6, -0.5), (0.3, -0.42),
                              (0.05, -0.55), (-0.25, -0.45), (-0.55, -0.55), (-0.9, -0.4)], hw, hh, dx), paint(col))
        cv.drawPath(nrm_path([(-0.5, -0.9), (0.2, -1.0)], hw, hh, dx, False), paint(hi, 0.6, stroke=3))
    elif st == "jesus":
        sway = noise1(t * 0.4, 3) * 0.03
        cv.drawPath(nrm_path([(-1.08, 0.5), (-1.08, -0.5), (-0.7, -1.04), (0.0, -1.12), (0.7, -1.04),
                              (1.08, -0.5), (1.08, 0.5), (1.18 + sway, 1.05), (0.98, 1.15), (0.92, 0.3),
                              (0.82, -0.32), (0.45, -0.72), (0.06, -0.8), (0.0, -0.7), (-0.06, -0.8),
                              (-0.45, -0.72), (-0.82, -0.32), (-0.92, 0.3), (-0.98, 1.15), (-1.18 + sway, 1.05)],
                             hw, hh, dx), paint(col))
        for s in (-1, 1):
            cv.drawPath(nrm_path([(s * 0.12, -0.92), (s * 0.6, -0.8), (s * 0.95, -0.3), (s * 1.0, 0.4)],
                                 hw, hh, dx, False), paint(hi, 0.45, stroke=3))
    elif st == "messy":
        pts = [(-1.04, -0.05), (-1.08, -0.62), (-0.8, -1.02), (-0.2, -1.15), (0.5, -1.12), (0.95, -0.85),
               (1.08, -0.45), (1.02, -0.05), (0.92, -0.38), (0.75, -0.35), (0.7, -0.55), (0.45, -0.42),
               (0.3, -0.6), (0.05, -0.45), (-0.15, -0.62), (-0.4, -0.45), (-0.55, -0.62), (-0.8, -0.4),
               (-0.92, -0.42)]
        cv.drawPath(nrm_path(pts, hw, hh, dx, tension=0.35), paint(col))
        cv.drawPath(nrm_path([(-0.3, -1.12), (-0.1, -1.32), (0.05, -1.12)], hw, hh, dx, False, 0.3), paint(col, stroke=9))
        cv.drawPath(nrm_path([(-0.6, -0.95), (0.0, -1.05), (0.5, -0.95)], hw, hh, dx, False), paint(hi, 0.6, stroke=3))
    elif st == "bob":
        cv.drawPath(nrm_path([(-1.06, 0.4), (-1.08, -0.55), (-0.7, -1.06), (0.0, -1.12), (0.7, -1.06),
                              (1.08, -0.55), (1.06, 0.4), (0.92, 0.0), (0.85, -0.5), (0.3, -0.6), (-0.4, -0.55),
                              (-0.85, -0.5), (-0.92, 0.0)], hw, hh, dx), paint(col))
    elif st == "short":
        cv.drawPath(nrm_path([(-1.03, -0.1), (-1.05, -0.62), (-0.7, -1.04), (0.0, -1.12), (0.7, -1.04),
                              (1.05, -0.62), (1.03, -0.1), (0.9, -0.5), (0.3, -0.62), (-0.4, -0.6),
                              (-0.9, -0.5)], hw, hh, dx), paint(col))


def draw_eye(cv, L, f, side, ex, ey, t):
    rx, ry = L.eye_rx, L.eye_ry
    lid = f["lid"]
    if lid < 0:
        ry = ry * (1 - lid * 0.55)
        rx = rx * (1 - lid * 0.25)
    twitch = f["twitch"] * (0.5 + 0.5 * math.sin(t * 55)) * (side > 0)
    eye = skia.Path()
    eye.addOval(skia.Rect.MakeLTRB(ex - rx, ey - ry, ex + rx, ey + ry))
    # socket shadow
    ellipse(cv, ex, ey - 1, rx + 2.5, ry + 2.5, paint(shade(L.skin, -0.18), 0.5))
    cv.drawPath(eye, paint("#fbfaf7"))
    cv.save()
    cv.clipPath(eye, skia.ClipOp.kIntersect, True)
    ix = ex + f["gx"] * rx * 0.48
    iy = ey + f["gy"] * ry * 0.4 + 1.5
    ir = rx * 0.66
    circle(cv, ix, iy, ir, paint(L.iris))
    circle(cv, ix, iy, ir * 0.8, paint(shade(L.iris, 0.18), 0.55))
    circle(cv, ix, iy, ir * 0.5 * f["pupil"], paint("#120c0a"))
    circle(cv, ix + ir * 0.35, iy - ir * 0.38, ir * 0.26, paint("#ffffff", 0.95))
    circle(cv, ix - ir * 0.3, iy + ir * 0.35, ir * 0.12, paint("#ffffff", 0.7))
    if f["glisten"] > 0.01:
        ellipse(cv, ex, ey + ry * 0.75, rx * 0.9, ry * 0.25, paint("#bfe3ff", 0.45 * f["glisten"]))
        circle(cv, ix - ir * 0.2, iy - ir * 0.5, ir * 0.18, paint("#ffffff", f["glisten"]))
    # upper lid
    closed = clamp(max(f["blink"], clamp(lid) + twitch * 0.35))
    tilt = f["lidtilt"] * side   # inner corner lower for angry
    ly = ey - ry + 2 * ry * closed
    lidp = skia.Path()
    lidp.moveTo(ex - rx - 3, ey - ry - 4)
    lidp.lineTo(ex + rx + 3, ey - ry - 4)
    yo = ly - tilt * ry * 0.45 * (1 - closed * 0.8)
    yi = ly + tilt * ry * 0.45 * (1 - closed * 0.8)
    if side > 0:   # right eye on screen: inner corner is left (x small)
        y_left, y_right = yi, yo
    else:
        y_left, y_right = yo, yi
    lidp.lineTo(ex + rx + 3, y_right)
    lidp.quadTo(ex, (y_left + y_right) / 2 - ry * 0.35 * (1 - closed), ex - rx - 3, y_left)
    lidp.close()
    lid_col = shade(L.skin, -0.06)
    cv.drawPath(lidp, paint(lid_col))
    # lower lid
    sq = f["squint"]
    if sq > 0.01:
        lo = skia.Path()
        by = ey + ry - 2 * ry * sq * 0.45
        lo.moveTo(ex - rx - 3, ey + ry + 4)
        lo.lineTo(ex - rx - 3, by + 2)
        lo.quadTo(ex, by - ry * 0.25 * sq, ex + rx + 3, by + 2)
        lo.lineTo(ex + rx + 3, ey + ry + 4)
        lo.close()
        cv.drawPath(lo, paint(shade(L.skin, -0.02)))
    cv.restore()
    # lash line
    lash = skia.Path()
    lash.moveTo(ex - rx, y_left)
    lash.quadTo(ex, (y_left + y_right) / 2 - ry * 0.35 * (1 - closed), ex + rx, y_right)
    lw = 3.2 if not L.lashes else 4.2
    cv.drawPath(lash, paint("#2a1a14", 0.9, stroke=lw))
    if L.lashes and closed < 0.9:
        ox = ex + rx * side
        line(cv, ox, (y_right if side > 0 else y_left), ox + 5 * side, (y_right if side > 0 else y_left) - 5,
             paint("#2a1a14", 0.9, stroke=3))
    if f["glisten"] > 0.5 and f["tears"] > 0.01:
        p = skia.Path()
        tx, ty = ex + rx * 0.3 * side, ey + ry + 2 + f["tears"] * 30
        p.moveTo(tx, ty - 9)
        p.quadTo(tx + 6, ty, tx, ty + 6)
        p.quadTo(tx - 6, ty, tx, ty - 9)
        cv.drawPath(p, paint("#9fd4ff", 0.8 * clamp(f["tears"] * 3)))


def draw_brow(cv, L, f, side, ex, ey):
    raise_ = f["browL"] if side < 0 else f["browR"]
    a = f["browA"]
    ry = L.eye_ry
    by = ey - ry - 13 - raise_ * 10
    rx = L.eye_rx + 4
    inner_x = ex - rx * side * -1 if False else ex - side * -rx  # placeholder for clarity
    # inner end is towards nose (x toward 0)
    xi = ex - side * rx * -1
    xi = ex + (-rx if side > 0 else rx)
    xo = ex + (rx if side > 0 else -rx)
    yi = by + a * 7
    yo = by - a * 2.5 + (raise_ * 2 if raise_ > 0 else 0)
    p = skia.Path()
    p.moveTo(xi, yi)
    p.quadTo((xi + xo) / 2, min(yi, yo) - 5 + a * 1.5, xo, yo + 3)
    cv.drawPath(p, paint(L.brow, stroke=7.5 if L.hair_style != "jesus" else 8))


def draw_mouth(cv, L, f, mx, my, speak, t):
    o = clamp(max(f["mouth"], speak))
    s = f["smile"]
    k = f["skew"]
    w = 21 * f["mw"] * (1 + 0.12 * s) * (1 - 0.18 * o)
    if L.beard:
        w *= 0.95
    lc = shade(L.skin, -0.55)
    if o < 0.06:
        p = skia.Path()
        lx, ly = mx - w, my - s * 7 - k * 6
        rx_, ry_ = mx + w, my - s * 7 + k * 6
        p.moveTo(lx, ly)
        p.quadTo(mx, my + s * 9, rx_, ry_)
        cv.drawPath(p, paint(lc, stroke=4.5))
        if f["teeth"] > 0.5 and s > 0.2:
            pass
        if s > 0.3:
            for sx, sy in ((lx, ly), (rx_, ry_)):
                d = -1 if sx < mx else 1
                cv.drawPath(quad_path((sx - d * 2, sy + 4), (sx + d * 3, sy), (sx - d * 1, sy - 4)),
                            paint(lc, 0.6, stroke=2.5))
        return
    lx, ly = mx - w, my - s * 6 - k * 6
    rx_, ry_ = mx + w, my - s * 6 + k * 6
    top_c = my - 3 - o * 3 + s * 3
    bot_c = my + o * 34 + s * 6 + 4
    p = skia.Path()
    p.moveTo(lx, ly)
    p.quadTo(mx, top_c, rx_, ry_)
    p.quadTo(mx, bot_c, lx, ly)
    p.close()
    cv.drawPath(p, paint("#4a1a22"))
    cv.save()
    cv.clipPath(p, skia.ClipOp.kIntersect, True)
    ellipse(cv, mx, bot_c - 4, w * 0.75, 10 + o * 6, paint("#d66a72"))
    if o > 0.2 or f["teeth"] > 0.5:
        rect(cv, mx - w, top_c - 10, 2 * w, 9.5 + min(o, 0.5) * 2, paint("#fbfbf6"))
    cv.restore()
    cv.drawPath(p, paint(lc, stroke=3.2))
    if L.lipcol:
        cv.drawPath(quad_path((lx + 3, ly + 1), (mx, bot_c + 4), (rx_ - 3, ry_ + 1)), paint(L.lipcol, 0.7, stroke=3.5))


def draw_beard(cv, L, f, t):
    hw, hh = L.hw, L.hh
    dx = f["turn"] * hw * 0.2
    col = L.hair
    mx = dx * 1.1
    my = hh * 0.47
    p = nrm_path([(-0.98, -0.05), (-0.92, 0.45), (-0.62, 0.95), (-0.25, 1.24), (0.0, 1.3), (0.25, 1.24),
                  (0.62, 0.95), (0.92, 0.45), (0.98, -0.05), (0.85, 0.22), (0.55, 0.3), (0.3, 0.38),
                  (0.0, 0.36), (-0.3, 0.38), (-0.55, 0.3), (-0.85, 0.22)], hw, hh, dx * 0.6)
    cv.drawPath(p, paint(col))
    cv.drawPath(nrm_path([(-0.45, 0.8), (-0.15, 1.05)], hw, hh, dx * 0.6, False), paint(shade(col, 0.15), 0.5, stroke=3))
    cv.drawPath(nrm_path([(0.45, 0.8), (0.15, 1.05)], hw, hh, dx * 0.6, False), paint(shade(col, 0.15), 0.5, stroke=3))
    # mouth hollow so the lips read clearly
    ellipse(cv, mx, my + 6, 26, 15, paint(shade(L.skin, -0.12)))


def draw_mustache(cv, L, f):
    hw, hh = L.hw, L.hh
    dx = f["turn"] * hw * 0.22
    col = L.hair
    s = f["smile"]
    p = skia.Path()
    y = hh * 0.36
    p.moveTo(dx, y)
    p.cubicTo(dx + 14, y - 8, dx + 30, y - 2, dx + 34, y + 10 - s * 5)
    p.cubicTo(dx + 22, y + 4, dx + 10, y + 6, dx, y + 5)
    p.cubicTo(dx - 10, y + 6, dx - 22, y + 4, dx - 34, y + 10 - s * 5)
    p.cubicTo(dx - 30, y - 2, dx - 14, y - 8, dx, y)
    p.close()
    cv.drawPath(p, paint(col))


def draw_head(cv, L, f, t, speak=0.0):
    """Head centred at origin."""
    hw, hh = L.hw, L.hh
    cv.save()
    cv.rotate(f["tilt"])
    draw_hair_back(cv, L, f, t)
    fx = f["turn"] * hw * 0.22
    # ears
    for s in (-1, 1):
        ex = s * hw * 0.97 - f["turn"] * hw * 0.12
        ellipse(cv, ex, hh * 0.02, 13, 19, paint(L.skin))
        ellipse(cv, ex + s * 1.5, hh * 0.02, 7, 11, paint(shade(L.skin, -0.15)))
        if L.earrings:
            circle(cv, ex, hh * 0.25, 5, paint("#f2e6c9"))
        if L.airpods:
            rrect(cv, ex - 5, hh * 0.0, 10, 22, 5, paint("#ffffff"))
            circle(cv, ex, hh * 0.02, 7, paint("#f4f4f4"))
    hp = head_path(hw, hh, L.jaw)
    cv.drawPath(hp, paint(L.skin))
    # soft shading on one side
    cv.save()
    cv.clipPath(hp, skia.ClipOp.kIntersect, True)
    ellipse(cv, hw * 0.95 + fx * 0.5, hh * 0.15, hw * 0.45, hh * 1.1, paint(shade(L.skin, -0.25), 0.22, blur=14))
    ellipse(cv, 0, hh * 1.05, hw * 0.8, hh * 0.25, paint(shade(L.skin, -0.3), 0.18, blur=10))
    if f["red"] > 0.01:
        cv.drawPath(hp, paint("#ff2a1a", 0.35 * f["red"]))
    cv.restore()
    if L.wrinkles:
        for s in (-1, 1):
            x0 = fx + s * (L.eye_sep + L.eye_rx + 6)
            cv.drawPath(quad_path((x0, L.eye_y - 4), (x0 + s * 5, L.eye_y + 2), (x0, L.eye_y + 8)),
                        paint(shade(L.skin, -0.3), 0.6, stroke=2))
        cv.drawPath(quad_path((fx - 20, -hh * 0.62), (fx, -hh * 0.66), (fx + 20, -hh * 0.62)),
                    paint(shade(L.skin, -0.25), 0.5, stroke=2))
        for s in (-1, 1):   # nasolabial folds
            cv.drawPath(quad_path((fx + s * 22, hh * 0.2), (fx + s * 32, hh * 0.38), (fx + s * 30, hh * 0.52)),
                        paint(shade(L.skin, -0.28), 0.45, stroke=2.4))
    # blush / cheeks
    b = max(f["blush"], 0.12)
    for s in (-1, 1):
        ellipse(cv, fx + s * hw * 0.55, hh * 0.24, 16, 10, paint("#ff7a7a", 0.35 * b + 0.25 * f["blush"], blur=6))
    if L.freckles:
        r = random.Random(4)
        for s in (-1, 1):
            for _ in range(6):
                circle(cv, fx + s * hw * (0.4 + r.random() * 0.3), hh * (0.12 + r.random() * 0.15), 1.8,
                       paint(shade(L.skin, -0.35), 0.7))
    if L.beard:
        draw_beard(cv, L, f, t)
    # eyes
    for s in (-1, 1):
        ex = fx + s * L.eye_sep
        draw_eye(cv, L, f, s, ex, L.eye_y, t)
        draw_brow(cv, L, f, s, ex, L.eye_y)
    # nose
    nx, ny = fx * 1.25, hh * 0.2
    n = L.nose
    cv.drawPath(quad_path((nx - 7 * n, ny + 2), (nx, ny + 10 * n), (nx + 7 * n, ny + 2)),
                paint(shade(L.skin, -0.32), 0.85, stroke=3.2))
    ellipse(cv, nx + 2, ny - 6, 4 * n, 6 * n, paint("#ffffff", 0.18))
    # mouth
    draw_mouth(cv, L, f, fx * 1.1, hh * 0.5, speak, t)
    if L.beard:
        draw_mustache(cv, L, f)
    if L.glasses:
        for s in (-1, 1):
            ex = fx + s * L.eye_sep
            r = skia.Rect.MakeLTRB(ex - L.eye_rx - 9, L.eye_y - L.eye_ry - 6, ex + L.eye_rx + 9, L.eye_y + L.eye_ry + 6)
            cv.drawRRect(skia.RRect.MakeRectXY(r, 7, 7), paint("#ffffff", 0.12))
            cv.drawRRect(skia.RRect.MakeRectXY(r, 7, 7), paint("#1d1d24", stroke=4))
            line(cv, ex - 6, L.eye_y - L.eye_ry + 2, ex + 4, L.eye_y - 2, paint("#ffffff", 0.35, stroke=3))
        line(cv, fx - L.eye_sep + L.eye_rx + 9, L.eye_y - 3, fx + L.eye_sep - L.eye_rx - 9, L.eye_y - 3,
             paint("#1d1d24", stroke=4))
    draw_hair_front(cv, L, f, t)
    if f["sweat"] > 0.01:
        k = (t * 0.45) % 1.0
        sx, sy = hw * 0.78 + fx * 0.3, -hh * 0.45 + k * hh * 0.5
        a = f["sweat"] * (1 - k) ** 0.5
        p = skia.Path()
        p.moveTo(sx, sy - 14)
        p.quadTo(sx + 10, sy + 2, sx, sy + 8)
        p.quadTo(sx - 10, sy + 2, sx, sy - 14)
        cv.drawPath(p, paint("#8fd0ff", a))
        circle(cv, sx - 2, sy + 1, 2.5, paint("#ffffff", a))
    cv.restore()


# ---------------------------------------------------------------- body

def ik(sx, sy, hx, hy, l1, l2, bend):
    dx, dy = hx - sx, hy - sy
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 0.5)
    d = max(d, abs(l1 - l2) + 0.5)
    a = math.atan2(dy, dx)
    c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    b = math.acos(c) * bend
    ex, ey = sx + l1 * math.cos(a + b), sy + l1 * math.sin(a + b)
    return ex, ey, sx + d * math.cos(a), sy + d * math.sin(a)


def draw_hand(cv, L, x, y, kind="fist", side=1, ang=0.0, scale=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang)
    cv.scale(scale, scale)
    sk = paint(L.skin)
    ol = paint(shade(L.skin, -0.3), 0.7, stroke=2)
    if kind == "open":
        for i, (fx, fl) in enumerate(((-12, 22), (-4, 27), (4, 27), (12, 22))):
            rrect(cv, fx - 4.5, -10 - fl, 9, fl + 8, 4.5, sk)
        ellipse(cv, -side * 16, 2, 7, 12, sk)
        ellipse(cv, 0, 0, 18, 17, sk)
        ellipse(cv, 0, 0, 18, 17, ol)
    elif kind == "point":
        ellipse(cv, 0, 0, 16, 15, sk)
        rrect(cv, -4.5, -38, 9, 30, 4.5, sk)
        ellipse(cv, 0, 0, 16, 15, ol)
    else:
        ellipse(cv, 0, 0, 17, 16, sk)
        ellipse(cv, side * -9, -4, 7, 9, sk)
        ellipse(cv, 0, 0, 17, 16, ol)
        for k in (-6, 1, 8):
            line(cv, k, -12, k, -6, paint(shade(L.skin, -0.25), 0.6, stroke=1.8))
    cv.restore()


def torso_path(sw, h=330, waist=0.9):
    p = skia.Path()
    p.moveTo(-sw + 26, -2)
    p.quadTo(-sw - 4, 0, -sw - 4, 44)
    p.lineTo(-sw * waist, h)
    p.lineTo(sw * waist, h)
    p.lineTo(sw + 4, 44)
    p.quadTo(sw + 4, 0, sw - 26, -2)
    p.close()
    return p


def draw_torso(cv, L, t, breathe=0.0):
    sw = L.sw
    cv.save()
    cv.scale(1, 1 + breathe * 0.012)
    tp = torso_path(sw)
    o = L.outfit
    if o == "suit":
        cv.drawPath(tp, paint(L.c1))
        cv.drawPath(poly([(-30, -2), (30, -2), (0, 120)]), paint(L.c2))
        cv.drawPath(poly([(-9, 8), (9, 8), (13, 140), (0, 165), (-13, 140)]), paint(L.c3))
        cv.drawPath(poly([(-9, 8), (9, 8), (6, 22), (-6, 22)]), paint(shade(L.c3, -0.2)))
        for s in (-1, 1):
            cv.drawPath(poly([(s * 30, -2), (s * 48, 30), (s * 30, 52), (s * 4, 150)], False),
                        paint(shade(L.c1, -0.35), stroke=4))
            cv.drawPath(poly([(s * 10, -6), (s * 30, -2), (s * 22, 26)]), paint(L.c2))
        rrect(cv, 48, 70, 30, 7, 2, paint("#e9d27a"))
    elif o == "blazer":
        cv.drawPath(tp, paint(L.c1))
        cv.drawPath(poly([(-34, -2), (34, -2), (0, 135)]), paint(L.c2))
        for i in range(9):
            a = math.pi * (0.15 + 0.7 * i / 8)
            circle(cv, 34 * math.cos(a), -2 + 22 * math.sin(a), 4.2, paint("#f6f1e6"))
        for s in (-1, 1):
            cv.drawPath(poly([(s * 34, -2), (s * 52, 40), (s * 40, 60), (s * 2, 160)], False),
                        paint(shade(L.c1, -0.3), stroke=4))
        circle(cv, 0, 190, 6, paint(shade(L.c1, -0.35)))
    elif o == "vest":
        cv.drawPath(tp, paint(L.c2))
        cv.drawPath(poly([(-22, -2), (22, -2), (0, 30)]), paint(shade(L.c2, 0.25)))
        for s in (-1, 1):
            cv.drawPath(poly([(s * 6, -4), (s * 26, -4), (s * 20, 24)]), paint(shade(L.c2, 0.15)))
        vp = skia.Path()
        vp.moveTo(-sw + 30, 4)
        vp.lineTo(-30, 2)
        vp.lineTo(-8, 60)
        vp.lineTo(-8, 330)
        vp.lineTo(-sw * 0.9 + 8, 330)
        vp.lineTo(-sw + 18, 60)
        vp.close()
        cv.drawPath(vp, paint(L.c1))
        m = skia.Matrix()
        m.setScale(-1, 1)
        vp2 = skia.Path(vp)
        vp2.transform(m)
        cv.drawPath(vp2, paint(L.c1))
        line(cv, -8, 60, -8, 330, paint(shade(L.c1, 0.25), stroke=2))
        rrect(cv, -sw + 46, 70, 26, 14, 4, paint("#e6e6e6", 0.85))
        for s in (-1, 1):
            cv.drawPath(poly([(s * 30, 2), (s * 8, 60)], False), paint(shade(L.c1, 0.3), stroke=3))
    elif o == "cardigan":
        cv.drawPath(tp, paint(L.c2))
        for s in (-1, 1):
            cp = skia.Path()
            cp.moveTo(s * (sw - 22), -2)
            cp.lineTo(s * 26, -2)
            cp.lineTo(s * 20, 330)
            cp.lineTo(s * sw * 0.9, 330)
            cp.lineTo(s * (sw + 4), 44)
            cp.close()
            cv.drawPath(cp, paint(L.c1))
            for k in range(4):
                circle(cv, s * 30, 60 + k * 55, 4.5, paint(shade(L.c1, -0.3)))
        cv.drawPath(quad_path((-26, -2), (0, 22), (26, -2)), paint(shade(L.c2, -0.12), stroke=4))
    elif o == "robe":
        cv.drawPath(tp, paint(L.c1))
        cv.drawPath(poly([(-28, -4), (28, -4), (0, 70)]), paint(shade(L.skin, -0.08)))
        cv.drawPath(quad_path((-30, -4), (-6, 40), (0, 72)), paint(shade(L.c1, -0.15), stroke=4))
        cv.drawPath(quad_path((30, -4), (6, 40), (0, 72)), paint(shade(L.c1, -0.15), stroke=4))
        sp = poly([(-sw + 14, 4), (-sw + 58, -6), (sw * 0.9, 250), (sw * 0.86, 300), (sw * 0.6, 300)])
        cv.drawPath(sp, paint(L.c3))
        cv.drawPath(poly([(-sw + 30, 8), (sw * 0.8, 270)], False), paint(shade(L.c3, 0.2), 0.5, stroke=3))
        for k in range(3):
            cv.drawPath(quad_path((-sw * 0.5 + k * 30, 120), (-sw * 0.45 + k * 30, 220), (-sw * 0.55 + k * 30, 320)),
                        paint(shade(L.c1, -0.12), 0.7, stroke=3))
    elif o == "hoodie":
        cv.drawPath(tp, paint(L.c1))
        cv.drawPath(smooth_path([(-70, -8), (-40, 26), (0, 36), (40, 26), (70, -8), (40, 6), (0, 12), (-40, 6)]),
                    paint(shade(L.c1, -0.15)))
        for s in (-1, 1):
            line(cv, s * 14, 28, s * 16, 110, paint("#f4f4f4", stroke=4))
            circle(cv, s * 16, 112, 4.5, paint("#d0d0d0"))
        rrect(cv, -60, 200, 120, 70, 18, paint(shade(L.c1, -0.12)))
    cv.restore()


class Pose:
    """Arm targets for a body. Hands in body coords (origin at shoulder line centre)."""

    def __init__(self, hl=(-62, 190), hr=(62, 190), kl="fist", kr="fist", al=0.0, ar=0.0):
        self.hl, self.hr, self.kl, self.kr, self.al, self.ar = hl, hr, kl, kr, al, ar


def draw_arm(cv, L, side, hand, kind, ang, color, l1=104, l2=92, width=40, back=False):
    sx = side * (L.sw - 20)
    sy = 34
    bend = 1 if side < 0 else -1
    ex, ey, hx, hy = ik(sx, sy, hand[0], hand[1], l1, l2, bend)
    cuff = shade(color, -0.1)
    cv.drawPath(poly([(sx, sy), (ex, ey), (hx, hy)], close=False), paint(shade(color, -0.35), stroke=width + 5))
    cv.drawPath(poly([(sx, sy), (ex, ey), (hx, hy)], close=False), paint(color, stroke=width))
    p = paint(shade(color, -0.25), 0.35, stroke=2.5)
    line(cv, ex - 6, ey, ex + 6, ey + 4, p)
    ux, uy = hx - ex, hy - ey
    n = math.hypot(ux, uy) or 1
    line(cv, hx - ux / n * 12, hy - uy / n * 12, hx - ux / n * 4, hy - uy / n * 4,
         paint(L.c2 if L.outfit == "suit" else cuff, stroke=width * 0.95, cap="butt"))
    a = math.degrees(math.atan2(uy, ux)) - 90 + ang
    draw_hand(cv, L, hx, hy, kind, side, a)
    return hx, hy


def arm_color(L):
    return {"suit": L.c1, "blazer": L.c1, "vest": L.c2, "cardigan": L.c1, "robe": L.c1, "hoodie": L.c1}[L.outfit]


def draw_neck(cv, L):
    rect(cv, -21, -48, 42, 60, paint(L.skin))
    ellipse(cv, 0, -2, 22, 10, paint(shade(L.skin, -0.2), 0.5))
