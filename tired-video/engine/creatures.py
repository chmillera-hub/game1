"""Creature rigs for "TIREDNESS"  (documented in API_creatures.md).

    draw_impulsivity(ctx, x, y, s, t, pose, expr, ...)    big goofy dog-thing ("it")
    draw_thing(ctx, x, y, s, t, state, ...)                small violet carrier critter
    draw_sweater_lump(ctx, x, y, s, t, wiggle)             the thing hiding under a knit sweater
    draw_specimen(ctx, x, y, s, t, form, pose, expr, ...)  Specimen Zero (shadow mass -> true shape)
    draw_specimen_pod_sleeper(ctx, x, y, s, t, seed)       cheap curled sleeper for the pods

Conventions shared by every rig
  * (x, y) is the GROUND point under the body, except airborne / held poses
    (see the per-rig tables in API_creatures.md) where it is the body centre.
  * s scales everything (ink outline 5.5 px at s=1).  Rigs face RIGHT; flip=True
    mirrors them to face left.  Every `look` is in SCREEN space (+x = right,
    +y = down, length <= 1) whatever `flip` is.
  * Every call returns a dict of anchors in the caller's coordinates.
  * All motion is a pure function of t (deterministic, no randomness).
"""
import math

import cairocffi as cairo

from .core import (hexc, mixc, clamp, lerp, seg, smoothstep, ease_in_out, ease_out,
                   ease_out_back, noise1, hash01, blink_amount, smooth_path, ellipse, circle,
                   radial_glow)

TAU = 2.0 * math.pi
PI = math.pi
LW = 5.5
_sin, _cos, _hyp, _atan2 = math.sin, math.cos, math.hypot, math.atan2
ROUND_CAP = cairo.LINE_CAP_ROUND
ROUND_JOIN = cairo.LINE_JOIN_ROUND

INK = hexc("ink")
WHITE = (1.0, 1.0, 1.0, 1.0)


def _a(c, a):
    c = hexc(c)
    return (c[0], c[1], c[2], c[3] * a)


# ============================================================================
# anchors
# ============================================================================
class _Anch:
    """Records local points as caller-space points (works through any nesting)."""
    __slots__ = ("ctx", "m0", "inv", "d", "s", "flip")

    def __init__(self, ctx, s=1.0, flip=False):
        self.ctx = ctx
        self.s = s
        self.flip = bool(flip)
        self.m0 = ctx.get_matrix()
        inv = ctx.get_matrix()
        inv.invert()
        self.inv = inv
        self.d = {}

    def pt(self, x, y):
        return self.inv.transform_point(*self.ctx.user_to_device(x, y))

    def put(self, name, x, y):
        p = self.pt(x, y)
        self.d[name] = p
        return p

    def call(self, fn, **extra):
        """Run a scene callback fn(ctx, anchors) in the caller's coordinates."""
        if fn is None:
            return
        ctx = self.ctx
        ctx.save()
        ctx.set_matrix(self.m0)
        d = dict(self.d)
        d.update(extra)
        d["s"] = self.s
        d["flip"] = self.flip
        if self.flip and "angle" in d:
            d["angle"] = -d["angle"]
        fn(ctx, d)
        ctx.restore()
        ctx.new_path()


# ============================================================================
# low-level drawing helpers
# ============================================================================
def _setup(ctx):
    ctx.set_line_cap(ROUND_CAP)
    ctx.set_line_join(ROUND_JOIN)
    ctx.set_tolerance(0.3)     # 0.3 device px curve flattening: invisible, ~10% faster


def _f(ctx, c):
    ctx.set_source_rgba(*c)
    ctx.fill()


def _s(ctx, c, w):
    ctx.set_source_rgba(*c)
    ctx.set_line_width(w)
    ctx.stroke()


def _fs(ctx, c, w=LW, ink=INK):
    ctx.set_source_rgba(*c)
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(w)
    ctx.stroke()


def _epts(cx, cy, rx, ry, n, rot=0.0, a0=0.0):
    cr, sr = _cos(rot), _sin(rot)
    out = []
    for i in range(n):
        a = a0 + TAU * i / n
        px, py = rx * _cos(a), ry * _sin(a)
        out.append((cx + px * cr - py * sr, cy + px * sr + py * cr))
    return out


def _orient(pts):
    """Return pts ordered with positive (screen-clockwise) winding."""
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return pts if a >= 0 else pts[::-1]


def _rot(px, py, a, cx=0.0, cy=0.0):
    c, s_ = _cos(a), _sin(a)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s_, cy + dx * s_ + dy * c)


def _scallop(ctx, pts, h, sweep=0.18, seed=0, var=0.3, hf=None):
    """Closed fur outline: one rounded, slightly swept tuft per segment of pts.

    hf(mx, my) -> multiplier for the tuft height at a segment midpoint (0 = flat).
    """
    pts = _orient(pts)
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L = _hyp(dx, dy) or 1.0
        hh = h * (1.0 - var + 2.0 * var * hash01(i, seed))
        if hf is not None:
            hh *= hf((ax + bx) * 0.5, (ay + by) * 0.5)
        k = hh / L
        nx, ny = dy * k, -dx * k
        ctx.curve_to(ax + nx * 1.3 + dx * (0.06 + sweep), ay + ny * 1.3 + dy * (0.06 + sweep),
                     bx + nx * 0.62 + dx * sweep * 0.5, by + ny * 0.62 + dy * sweep * 0.5, bx, by)
    ctx.close_path()


def _taper(pts, widths):
    """Centre line + widths -> closed outline points (tip width 0 -> single point)."""
    n = len(pts)
    L, R = [], []
    for i in range(n):
        x, y = pts[i]
        if i == 0:
            ax, ay = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            ax, ay = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            ax, ay = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        l = _hyp(ax, ay) or 1.0
        w = widths[i] * 0.5
        nx, ny = -ay / l * w, ax / l * w
        L.append((x + nx, y + ny))
        R.append((x - nx, y - ny))
    if widths[-1] <= 0.5:
        R.pop()
        L[-1] = pts[-1]
    return L + R[::-1]


def _capsule(ctx, x0, y0, x1, y1, r0, r1=None):
    r1 = r0 if r1 is None else r1
    a = _atan2(y1 - y0, x1 - x0)
    ctx.new_sub_path()
    ctx.arc(x1, y1, r1, a - PI / 2, a + PI / 2)
    ctx.arc(x0, y0, r0, a + PI / 2, a + 1.5 * PI)
    ctx.close_path()


def _shaded(ctx, path, base, dk, off=(14.0, 14.0), lw=LW, ink=INK, inner=None):
    """Fill path with one shadow tone: light area = path shifted by -off, clipped."""
    path(ctx)
    ctx.set_source_rgba(*dk)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.translate(-off[0], -off[1])
    path(ctx)
    ctx.set_source_rgba(*base)
    ctx.fill()
    ctx.translate(off[0], off[1])
    if inner is not None:
        inner(ctx)
    ctx.restore()
    if lw:
        path(ctx)
        ctx.set_source_rgba(*ink)
        ctx.set_line_width(lw)
        ctx.stroke()


def _ik(hx, hy, fx, fy, l1, l2, bend):
    """2-bone IK -> joint position. bend=+1 puts the joint clockwise of hip->foot."""
    dx, dy = fx - hx, fy - hy
    d = max(1e-3, min(_hyp(dx, dy), l1 + l2 - 1e-3))
    c = (l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d)
    a = math.acos(max(-1.0, min(1.0, c)))
    b = _atan2(dy, dx) + bend * a
    return (hx + l1 * _cos(b), hy + l1 * _sin(b))


def _pulse(t, period, dur, seed):
    """Occasional quick 0->1->0 pulses at hashed times (ear twitches etc.)."""
    k = math.floor(t / period)
    out = 0.0
    for j in (k - 1, k):
        st = j * period + hash01(j, seed) * period * 0.6
        p = (t - st) / dur
        if 0.0 <= p <= 1.0:
            out = max(out, _sin(p * PI))
    return out


def _eye(ctx, cx, cy, rx, ry, lx=0.0, ly=0.0, pr=10.0, lid=INK, up=0.0, upt=0.0, lo=0.0,
         lot=0.0, lcurve=0.0, sclera=WHITE, pupil=INK, iris=None, ring=None, ir=0.0, hl=1.0,
         hls=1.0, lw=LW, ink=INK, pw=1.0, wet=0.0, lidlw=None, outline=True):
    """Generic cartoon eye.

    (lx, ly) pupil direction (-1..1), pr pupil radius, optional iris (ir radius).
    up / lo: upper / lower lid coverage 0..1 (up+lo >= 1 closes the eye).
    upt / lot: lid tilt, >0 = RIGHT end of the lid edge lower.
    lcurve: extra upward bulge of the lower lid (happy cheeks).
    """
    if rx <= 0.4 or ry <= 0.4:
        return
    ellipse(ctx, cx, cy, rx, ry)
    ctx.set_source_rgba(*sclera)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    d = _hyp(lx, ly)
    if d > 1.0:
        lx, ly = lx / d, ly / d
    r0 = ir if (iris is not None and ir > 0.3) else pr
    ox = cx + lx * max(0.0, rx - r0 * 0.85)
    oy = cy + ly * max(0.0, ry - r0 * 0.85)
    if iris is not None and ir > 0.3:
        circle(ctx, ox, oy, ir)
        ctx.set_source_rgba(*(ring or iris))
        ctx.fill()
        if ring is not None:
            circle(ctx, ox, oy, ir * 0.8)
            ctx.set_source_rgba(*iris)
            ctx.fill()
    if pr > 0.3:
        ellipse(ctx, ox, oy, pr * pw, pr)
        ctx.set_source_rgba(*pupil)
        ctx.fill()
    if hl > 0.01 and r0 > 0.5:
        k = hl * hls
        circle(ctx, ox - r0 * 0.36, oy - r0 * 0.40, r0 * 0.30 * k)
        circle(ctx, ox + r0 * 0.40, oy + r0 * 0.34, r0 * 0.13 * k)
        if wet > 0.01:
            circle(ctx, ox + r0 * 0.05, oy - r0 * 0.58, r0 * 0.11 * k)
            circle(ctx, ox - r0 * 0.5, oy + r0 * 0.25, r0 * 0.08 * k)
        ctx.set_source_rgba(*WHITE)
        ctx.fill()
    if wet > 0.01:
        ctx.move_to(cx - rx * 0.62, cy + ry * 0.55)
        ctx.curve_to(cx - rx * 0.25, cy + ry * 0.8, cx + rx * 0.25, cy + ry * 0.8,
                     cx + rx * 0.62, cy + ry * 0.55)
        _s(ctx, _a(WHITE, 0.75 * wet), max(1.0, ry * 0.09))
    e = rx + 6.0
    llw = lidlw or lw * 0.85
    if up > 0.002:
        up = min(up, 1.0)
        yb = cy - ry + 2.0 * ry * up
        yl = yb - upt * ry * 0.5
        yr = yb + upt * ry * 0.5
        sag = ry * 0.22 * (1.0 - up * 0.6)
        ctx.move_to(cx - e, cy - ry - 8)
        ctx.line_to(cx + e, cy - ry - 8)
        ctx.line_to(cx + e, yr)
        ctx.curve_to(cx + rx * 0.45, yr + sag, cx - rx * 0.45, yl + sag, cx - e, yl)
        ctx.close_path()
        _f(ctx, lid)
        ctx.move_to(cx + e, yr)
        ctx.curve_to(cx + rx * 0.45, yr + sag, cx - rx * 0.45, yl + sag, cx - e, yl)
        _s(ctx, ink, llw)
    if lo > 0.002:
        lo = min(lo, 1.0)
        yb = cy + ry - 2.0 * ry * lo
        yl = yb - lot * ry * 0.5
        yr = yb + lot * ry * 0.5
        bul = -ry * (0.10 + lcurve)
        ctx.move_to(cx - e, cy + ry + 8)
        ctx.line_to(cx + e, cy + ry + 8)
        ctx.line_to(cx + e, yr)
        ctx.curve_to(cx + rx * 0.45, yr + bul, cx - rx * 0.45, yl + bul, cx - e, yl)
        ctx.close_path()
        _f(ctx, lid)
        ctx.move_to(cx + e, yr)
        ctx.curve_to(cx + rx * 0.45, yr + bul, cx - rx * 0.45, yl + bul, cx - e, yl)
        _s(ctx, ink, llw * 0.8)
    ctx.restore()
    if outline:
        ellipse(ctx, cx, cy, rx, ry)
        _s(ctx, ink, lw)


def _happy_eye(ctx, cx, cy, rx, ry, w, ink=INK, down=False):
    """Closed eye arc: ^-shape (happy) or u-shape (down=True, sleeping)."""
    if down:
        ctx.move_to(cx - rx, cy)
        ctx.curve_to(cx - rx * 0.5, cy + ry * 0.55, cx + rx * 0.5, cy + ry * 0.55, cx + rx, cy)
    else:
        ctx.move_to(cx - rx, cy + ry * 0.3)
        ctx.curve_to(cx - rx * 0.55, cy - ry * 0.55, cx + rx * 0.55, cy - ry * 0.55,
                     cx + rx, cy + ry * 0.3)
    _s(ctx, ink, w)


def _screen_look(look, flip):
    if look is None:
        return None
    lx, ly = look
    return (-lx if flip else lx, ly)


def _begin(ctx, x, y, s, flip):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if flip else s, s)
    _setup(ctx)


def _lr(A, a_name, b_name):
    """Rename two local eye anchors to eye_l / eye_r by their screen x."""
    pa, pb = A.d.pop(a_name, None), A.d.pop(b_name, None)
    if pa is None or pb is None:
        return
    if pa[0] <= pb[0]:
        A.d["eye_l"], A.d["eye_r"] = pa, pb
    else:
        A.d["eye_l"], A.d["eye_r"] = pb, pa


# ============================================================================
# IMPULSIVITY
# ============================================================================
IMP = hexc("imp_fur")
IMP_DK = hexc("imp_fur_dk")
IMP_FAR = mixc("imp_fur", "imp_fur_dk", 0.55)
IMP_CR = mixc("imp_fur", "#fff4de", 0.62)
IMP_CRD = mixc("imp_fur", "#fff4de", 0.26)
TONGUE = hexc("imp_tongue")
TONGUE_DK = mixc("imp_tongue", "#b5305a", 0.55)
MOUTH = hexc("#5a1838")
NOSE = hexc("#2b1b30")

# default derp wall-eye (screen space): left eye up-left, right eye down-right
IMP_DERP_L = (-0.78, -0.42)
IMP_DERP_R = (0.72, 0.5)

_IMPX = {
    "derp":    dict(es=1.00, pr=1.00, up=0.00, upt=0.00, lo=0.00, lc=0.0, by=0, bt=0.00,
                    grin=1.00, tongue=1.00, ears=0.00, flap=0.0, hz=3.0),
    "happy":   dict(es=1.00, pr=1.00, up=0.00, upt=0.00, lo=0.40, lc=0.30, by=-12, bt=0.25,
                    grin=1.10, tongue=1.05, ears=-0.08, flap=0.0, hz=3.0),
    "excited": dict(es=1.20, pr=0.70, up=0.00, upt=0.00, lo=0.00, lc=0.0, by=-12, bt=0.20,
                    grin=1.16, tongue=1.30, ears=-0.30, flap=1.0, hz=4.0),
    "focused": dict(es=0.95, pr=1.10, up=0.32, upt=0.30, lo=0.14, lc=0.0, by=12, bt=-0.45,
                    grin=0.74, tongue=0.30, ears=0.06, flap=0.0, hz=3.0),
    "sleepy":  dict(es=1.00, pr=0.95, up=0.62, upt=-0.12, lo=0.14, lc=0.0, by=8, bt=0.15,
                    grin=0.82, tongue=1.35, ears=0.16, flap=0.0, hz=1.2),
}

_IMP_HEAD = _epts(0, 0, 174, 146, 26, a0=0.06)


def _imp_hhf(x, y):
    return (1.0 + 1.5 * smoothstep((-y - 92.0) / 44.0)
            + 0.8 * smoothstep((abs(x) - 135.0) / 25.0) * smoothstep((y + 20.0) / 40.0))


def _imp_head_path(ctx):
    _scallop(ctx, _IMP_HEAD, 15.0, 0.16, 11, 0.3, _imp_hhf)


_IMP_EAR = [(18, -16), (-22, -22), (-62, 10), (-84, 80), (-86, 150), (-66, 196), (-36, 207),
            (-14, 186), (-4, 130), (4, 64), (14, 18)]


def _imp_ear_path(ctx):
    smooth_path(ctx, _IMP_EAR, closed=True)


def _imp_ear(ctx, side, ang, tx):
    ctx.save()
    ctx.translate(side * 114 + tx * 0.5, -88)
    if side > 0:
        ctx.scale(-1, 1)
    ctx.rotate(ang)
    _shaded(ctx, _imp_ear_path, IMP, IMP_DK, off=(16.0, -4.0))
    ctx.restore()


def _imp_head(ctx, A, t, e, la, lb, bl, pv, turn=0.0, ear_a=(0.12, 0.12), ears_back=False,
              mouth="grin", swing=0.0, hold=None, tdir=1.0, hold_angle=0.0, blow=0.0):
    """Head in head-local coords (centre 0,0). la/lb local look of left/right eye."""
    tx = turn * 40.0
    if ears_back:
        _imp_ear(ctx, -1, ear_a[0], tx)
        _imp_ear(ctx, 1, ear_a[1], tx)
    _shaded(ctx, _imp_head_path, IMP, IMP_DK, off=(10.0, 26.0))
    if not ears_back:
        _imp_ear(ctx, -1, ear_a[0], tx)
        _imp_ear(ctx, 1, ear_a[1], tx)
    A.put("head", 0, 0)
    A.put("top", tx * 0.3, -168)
    mx = tx * 1.1
    # muzzle
    _shaded(ctx, lambda c: ellipse(c, mx, 48, 132, 70), IMP_CR, IMP_CRD, off=(0.0, 14.0),
            lw=LW * 0.8)
    _imp_mouth(ctx, A, t, e, pv, mx, mouth, swing, hold, tdir, hold_angle, blow)
    # nose
    nx = mx * 1.05
    ctx.save()
    ctx.translate(nx, 4)
    smooth_path(ctx, [(-32, -12), (0, -17), (32, -12), (27, 6), (0, 25), (-27, 6)], closed=True)
    _fs(ctx, NOSE, LW * 0.8)
    ellipse(ctx, -11, -6, 10, 5, -0.2)
    _f(ctx, _a(WHITE, 0.85))
    ctx.restore()
    ctx.move_to(nx, 27)
    ctx.line_to(mx, 57)
    _s(ctx, INK, LW * 0.75)
    A.put("nose", nx, 4)
    # eyes
    es = e["es"]
    ax_, bx_ = -72 + tx * 0.9, 74 + tx * 0.9
    sqa = 1.0 - max(0.0, -turn) * 0.4
    sqb = 1.0 - max(0.0, turn) * 0.4
    up = e["up"] + (1.0 - e["up"]) * bl
    lo = e["lo"] * (1.0 - bl)
    eyes = ((ax_, -52.0, 51 * es * sqa, 55 * es, la, 13.5, e["upt"], "eA"),
            (bx_, -57.0, 44 * es * sqb, 48 * es, lb, 12.5, -e["upt"], "eB"))
    for (cx, cy, rx, ry, lk, pr, upt, nm) in eyes:
        _eye(ctx, cx, cy, rx, ry, lk[0], lk[1], pr * e["pr"] * min(1.0, sqa if nm == "eA" else sqb),
             lid=IMP, up=up, upt=upt, lo=lo, lot=-upt * 0.3, lcurve=e["lc"], lw=LW)
        A.put(nm, cx, cy)
    # brows (ink tufts)
    for (cx, cy, rx, ry, lk, pr, upt, nm), sd in zip(eyes, (-1, 1)):
        by = cy - ry - 16 + e["by"]
        bt = e["bt"]
        ox_, ix_ = cx + sd * 26, cx - sd * 22
        ctx.move_to(ox_, by + 4)
        ctx.curve_to(cx + sd * 10, by - 8, cx - sd * 6, by - 8 - bt * 16, ix_, by - bt * 26)
        _s(ctx, INK, 8.0)


def _imp_mouth(ctx, A, t, e, pv, mx, mode, swing, hold, tdir, hold_angle, blow=0.0):
    g = e["grin"]
    cl = (mx - 126 * g, 42.0)
    cr = (mx + 128 * g, 36.0)
    mt = (mx, 58.0)
    clamp_ = mode == "clamp"
    if clamp_:
        bot = 104.0 + 3 * pv
    else:
        bot = 44.0 + (80.0 + 8.0 * pv) * min(1.15, 0.55 + 0.45 * g)
    mb = (mx + 4, bot)
    dep = (bot - 44.0) * 0.75

    def mp(c):
        c.move_to(*cl)
        c.curve_to(cl[0] + 36, cl[1] + 10, mt[0] - 44, mt[1] + 2, mt[0], mt[1])
        c.curve_to(mt[0] + 44, mt[1] + 2, cr[0] - 36, cr[1] + 10, cr[0], cr[1])
        c.curve_to(cr[0] - 6, cr[1] + dep, mb[0] + 72 * g, mb[1], mb[0], mb[1])
        c.curve_to(mb[0] - 72 * g, mb[1], cl[0] + 6, cl[1] + dep, cl[0], cl[1])
        c.close_path()

    def top_edge(c):
        c.move_to(*cl)
        c.curve_to(cl[0] + 36, cl[1] + 10, mt[0] - 44, mt[1] + 2, mt[0], mt[1])
        c.curve_to(mt[0] + 44, mt[1] + 2, cr[0] - 36, cr[1] + 10, cr[0], cr[1])

    def bot_edge(c):
        c.move_to(*cr)
        c.curve_to(cr[0] - 6, cr[1] + dep, mb[0] + 72 * g, mb[1], mb[0], mb[1])
        c.curve_to(mb[0] - 72 * g, mb[1], cl[0] + 6, cl[1] + dep, cl[0], cl[1])

    mp(ctx)
    ctx.set_source_rgba(*MOUTH)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ellipse(ctx, mx + 16 * tdir, bot + 4, 80 * g, 34)
    _f(ctx, TONGUE)
    ctx.move_to(mx + 16 * tdir, bot - 24)
    ctx.line_to(mx + 16 * tdir, bot)
    _s(ctx, TONGUE_DK, 4)
    if not clamp_:
        for fx_, fy_ in ((cl[0] + 30, cl[1] + 4), (cr[0] - 30, cr[1] + 4)):
            ctx.move_to(fx_ - 10, fy_ - 6)
            ctx.line_to(fx_ + 10, fy_ - 6)
            ctx.line_to(fx_ + 1, fy_ + 17)
            ctx.close_path()
            _fs(ctx, WHITE, LW * 0.5)
    ctx.restore()
    A.put("mouth", mx, (mt[1] + bot) * 0.5)
    if clamp_:
        # scene draws the cage handle here: over the mouth, under the teeth
        A.call(hold, angle=hold_angle)
        _setup(ctx)
        mp(ctx)
        ctx.save()
        ctx.clip()
        for k in (-1.5, -0.5, 0.5, 1.5):
            xx = mx + k * 27
            yt = 58 - 17 * (k * 27 / 120.0) ** 2
            _capsule(ctx, xx, yt - 10, xx, yt + 17, 11.5, 10.5)
        for k in (-1, 1):
            xx = mx + k * 46 + 4
            _capsule(ctx, xx, bot + 10, xx, bot - 13, 10.0, 9.0)
        ctx.set_source_rgba(*WHITE)
        ctx.fill_preserve()
        _s(ctx, INK, 2.8)
        ctx.restore()
    mp(ctx)
    _s(ctx, INK, LW)
    # grin creases at the corners
    for (px, py), sd in ((cl, -1), (cr, 1)):
        ctx.move_to(px + sd * 2, py - 16)
        ctx.curve_to(px + sd * 16, py - 8, px + sd * 16, py + 6, px + sd * 6, py + 14)
    _s(ctx, INK, LW * 0.7)
    # lolling tongue
    tl = e["tongue"]
    if tl > 0.45:
        B = (mx + 50 * g * tdir, bot - 32)
        Lp = (mx + 78 * g * tdir, bot - 4)
        T = (Lp[0] + (12 + swing) * tdir, Lp[1] + 60 * tl + 10 * pv)
        if blow > 0:   # streaming back in the wind
            T = (lerp(T[0], Lp[0] - 96, blow), lerp(T[1], Lp[1] + 30 + swing * 0.4, blow))

        def tp(c):
            c.move_to(*B)
            c.curve_to(B[0] + 12 * tdir, B[1] + 16, Lp[0] - 6 * tdir, Lp[1] - 12, Lp[0], Lp[1])
            c.curve_to(Lp[0] + 4 * tdir, Lp[1] + 22, T[0] - swing * 0.3 * tdir, T[1] - 26,
                       T[0], T[1])
        tp(ctx)
        _s(ctx, INK, 48 + 2 * LW)
        tp(ctx)
        _s(ctx, TONGUE, 48)
        ctx.move_to(Lp[0] + 2 * tdir, Lp[1] + 6)
        ctx.curve_to(Lp[0] + 5 * tdir, Lp[1] + 24, T[0] - 3 * tdir, T[1] - 26, T[0] - 1 * tdir,
                     T[1] - 10)
        _s(ctx, TONGUE_DK, 4.5)
        ellipse(ctx, T[0] - 12 * tdir, T[1] - 12, 5, 8, 0.2 * tdir)
        _f(ctx, _a(WHITE, 0.55))
        A.put("tongue", T[0], T[1] + 24)


def _imp_tail(ctx, A, bx, by, ang, sc=1.0, wag=0.0):
    C = ((0, 0), (66, -22), (124, -80), (146, -158), (128, -226))
    Wd = (46, 76, 86, 70, 16)
    pts = []
    for i, (px, py) in enumerate(C):
        a = ang + wag * (1.0 + 0.45 * i)     # whip: the tip lags further
        qx, qy = _rot(px * sc, py * sc, a)
        pts.append((bx + qx, by + qy))
    outline = _taper(pts, [w * sc for w in Wd])
    _shaded(ctx, lambda c: _scallop(c, outline, 13.0 * sc, 0.3, 21, 0.35), IMP, IMP_DK,
            off=(-10.0, 14.0))
    A.put("tail", *pts[-1])


def _imp_body_path(pts, h, seed, flat=True):
    hf = (lambda x, y: smoothstep((-y - 40.0) / 50.0)) if flat else None
    return lambda c: _scallop(c, pts, h, 0.16, seed, 0.3, hf)


def _imp_paw(ctx, x, y, rx, ry, rot=0.0, col=IMP_CR, dk=IMP_CRD):
    _shaded(ctx, lambda c: ellipse(c, x, y, rx, ry, rot), col, dk, off=(0.0, 8.0))
    for k in (-1, 1):
        px, py = _rot(x + k * rx * 0.3, y - ry * 0.05, rot, x, y)
        qx, qy = _rot(x + k * rx * 0.3, y + ry * 0.6, rot, x, y)
        ctx.move_to(px, py)
        ctx.line_to(qx, qy)
    _s(ctx, INK, LW * 0.6)


def _imp_leg(ctx, x0, y0, x1, y1, r0, r1, col=IMP, dk=IMP_DK, off=(10.0, 0.0)):
    _shaded(ctx, lambda c: _capsule(c, x0, y0, x1, y1, r0, r1), col, dk, off=off)


def draw_impulsivity(ctx, x, y, s, t, pose="sit", expr="derp", look_l=None, look_r=None,
                     pant=1.0, wag=0.0, blink=None, frozen=True, flip=False, hold=None,
                     pose_t=None):
    """Impulsivity. See API_creatures.md. Returns anchors (screen coords)."""
    A = _Anch(ctx, s, flip)
    e = dict(_IMPX.get(expr, _IMPX["derp"]))
    pt = t if pose_t is None else pose_t
    # --- eyes: screen-space look -> local; default derp wall-eye
    if expr == "focused":
        base = look_l if look_l is not None else (look_r if look_r is not None else (0.0, 0.05))
        ll = look_l if look_l is not None else base
        lr = look_r if look_r is not None else base
    elif expr == "sleepy":
        ll = look_l if look_l is not None else (-0.35, 0.75)
        lr = look_r if look_r is not None else (0.45, 0.8)
    else:
        ll = look_l if look_l is not None else IMP_DERP_L
        lr = look_r if look_r is not None else IMP_DERP_R
    if not frozen:
        ll = (ll[0] + noise1(t * 0.45, 31) * 0.12, ll[1] + noise1(t * 0.4, 32) * 0.1)
        lr = (lr[0] + noise1(t * 0.45, 33) * 0.12, lr[1] + noise1(t * 0.4, 34) * 0.1)
    # local: left-eye (A) is the screen-left eye unless flipped
    if flip:
        la, lb = (-lr[0], lr[1]), (-ll[0], ll[1])
    else:
        la, lb = ll, lr
    if blink is not None:
        bl = clamp(blink)
    elif frozen:
        bl = 0.0
    else:
        bl = blink_amount(t, seed=17)
    # --- pant / breath
    hz = e["hz"]
    pv = pant * _sin(TAU * hz * t)
    breath = _sin(TAU * t / 3.5) * (1.0 - min(1.0, pant))
    pv_all = pv + breath * 0.5
    idle = 0.0 if frozen else 1.0
    head_rot = idle * noise1(t * 0.35, 41) * 0.05
    head_bob = 4.0 * pv_all + idle * noise1(t * 0.5, 42) * 3.0
    ear_j = 0.05 * pv_all + idle * noise1(t * 0.8, 43) * 0.06
    wag_amp = wag if wag > 0 else 0.0
    wag_a = wag_amp * 0.38 * _sin(TAU * 2.6 * t) + idle * 0.05 * noise1(t * 0.5, 44)
    swing = 0.0
    if e["flap"]:
        swing = 34.0 * _sin(TAU * 5.0 * t)
    _begin(ctx, x, y, s, flip)
    ears = (0.12 + e["ears"] + ear_j, 0.12 + e["ears"] + ear_j * 0.8)

    if pose == "stand":
        _imp_stand(ctx, A, t, e, la, lb, bl, pv_all, head_rot, head_bob, ears, swing, wag_a,
                   idle)
    elif pose == "lunge":
        _imp_lunge(ctx, A, t, pt, e, la, lb, bl, pv_all, head_rot, swing, wag_a)
    elif pose == "tug":
        _imp_tug(ctx, A, t, e, la, lb, bl, pv_all, ears, wag_a, hold)
    elif pose == "lie":
        _imp_lie(ctx, A, t, e, la, lb, bl, pv_all, head_rot, head_bob, ears, swing, wag_a)
    else:
        _imp_sit(ctx, A, t, e, la, lb, bl, pv_all, head_rot, head_bob, ears, swing, wag_a)
    ctx.restore()
    _lr(A, "eA", "eB")
    pl, pr_ = A.d.get("paw_l"), A.d.get("paw_r")
    if pl and pr_ and pl[0] > pr_[0]:
        A.d["paw_l"], A.d["paw_r"] = pr_, pl
    return A.d


def _imp_sit(ctx, A, t, e, la, lb, bl, pv, hrot, hbob, ears, swing, wag_a):
    _imp_tail(ctx, A, 168, -74, 0.22, 1.0, wag_a)
    bpts = [(px, min(py, -6.0)) for (px, py) in
            _epts(0, -212 - 2 * pv, 222 + 3 * pv, 200 + 4 * pv, 30, a0=0.1)]
    _shaded(ctx, _imp_body_path(bpts, 18, 3), IMP, IMP_DK, off=(26.0, 18.0))
    for sd in (-1, 1):
        hp = _epts(sd * 162, -100, 100, 92, 16)
        _shaded(ctx, lambda c, hp=hp: _scallop(c, hp, 12, 0.2, 5 + sd, 0.3,
                                               lambda qx, qy: smoothstep((-qy - 70) / 30.0)),
                IMP, IMP_DK, off=(-sd * 4.0 + 10, 20.0))
        _imp_paw(ctx, sd * 198, -27, 66, 30, sd * 0.12)
    for sd in (-1, 1):
        _imp_leg(ctx, sd * 62, -222 - pv, sd * 70, -46, 37, 35, off=(12.0, 0.0))
        _imp_paw(ctx, sd * 76, -30, 58, 30)
        A.put("paw_l" if sd < 0 else "paw_r", sd * 76, -30)
    cb = _epts(0, -268 - 3 * pv, 124, 104, 18, a0=0.2)
    _shaded(ctx, lambda c: _scallop(c, cb, 14, 0.12, 9, 0.35,
                                    lambda qx, qy: 0.5 + smoothstep((qy + 280) / 60.0)),
            IMP_CR, IMP_CRD, off=(10.0, 16.0))
    A.put("chest", 0, -250)
    A.put("center", 0, -230)
    ctx.save()
    ctx.translate(0, -424 + hbob)
    ctx.rotate(hrot)
    _imp_head(ctx, A, t, e, la, lb, bl, pv, 0.0, ears, False, "grin", swing)
    ctx.restore()


def _imp_stand(ctx, A, t, e, la, lb, bl, pv, hrot, hbob, ears, swing, wag_a, idle):
    _imp_tail(ctx, A, -222, -300, -1.0, 1.0, wag_a)
    for lx_ in (-150, 128):
        _imp_leg(ctx, lx_ + 14, -200, lx_ + 20, -46, 40, 38, IMP_FAR, IMP_DK)
        _imp_paw(ctx, lx_ + 32, -28, 52, 26, 0.0, IMP_CRD, IMP_DK)
    bpts = _epts(-20, -236 - 2 * pv, 238 + 2 * pv, 136 + 4 * pv, 30, a0=0.1)
    _shaded(ctx, _imp_body_path(bpts, 17, 4, flat=False), IMP, IMP_DK, off=(10.0, 24.0))
    hp = _epts(-160, -196, 96, 92, 16)
    _shaded(ctx, lambda c: _scallop(c, hp, 12, 0.2, 7, 0.3,
                                    lambda qx, qy: smoothstep((-qy - 170) / 30.0)),
            IMP, IMP_DK, off=(8.0, 20.0))
    _imp_leg(ctx, -168, -170, -176, -46, 42, 40)
    _imp_paw(ctx, -160, -28, 60, 29)
    _imp_leg(ctx, 112, -190, 118, -46, 42, 40)
    _imp_paw(ctx, 134, -28, 60, 29)
    A.put("paw_l", -160, -28)
    A.put("paw_r", 134, -28)
    cb = _epts(150, -270 - 2 * pv, 84, 92, 14, a0=0.2)
    _shaded(ctx, lambda c: _scallop(c, cb, 13, 0.12, 9, 0.35), IMP_CR, IMP_CRD, off=(10.0, 16.0))
    A.put("chest", 150, -260)
    A.put("center", -20, -236)
    ctx.save()
    ctx.translate(222, -400 + hbob)
    ctx.rotate(hrot - 0.04)
    ctx.scale(0.94, 0.94)
    _imp_head(ctx, A, t, e, la, lb, bl, pv, 0.45, ears, False, "grin", swing)
    ctx.restore()


def _imp_lunge(ctx, A, t, pt, e, la, lb, bl, pv, hrot, swing, wag_a):
    """Bursting through a door. (x, y) = body centre. pose_t (s) drives the stretch."""
    k = ease_out(seg(pt, 0.0, 0.45))
    st = 1.0 + 0.2 * (1.0 - k) + 0.04 * _sin(TAU * 3 * t)
    flut = 0.1 * _sin(TAU * 7 * t)
    ctx.save()
    ctx.rotate(-0.1)
    _imp_tail(ctx, A, -226 * st, -46, -1.95, 1.0, flut)
    # far legs (reaching forward / kicking back)
    _imp_leg(ctx, 150 * st, 30, 300 * st, 56, 36, 34, IMP_FAR, IMP_DK)
    _imp_paw(ctx, 320 * st, 60, 52, 27, 0.2, IMP_CRD, IMP_DK)
    _imp_leg(ctx, -190 * st, 10, -300 * st, 2, 34, 32, IMP_FAR, IMP_DK)
    _imp_paw(ctx, -318 * st, 0, 28, 46, 0.1, IMP_CRD, IMP_DK)
    bpts = _epts(0, 0, 236 * st, 134 / st ** 0.5, 30, a0=0.1)
    _shaded(ctx, lambda c: _scallop(c, bpts, 18, -0.12, 6, 0.3), IMP, IMP_DK, off=(10.0, 26.0))
    hp = _epts(-176 * st, 26, 96, 88, 16)
    _shaded(ctx, lambda c: _scallop(c, hp, 12, -0.15, 7, 0.3), IMP, IMP_DK, off=(8.0, 20.0))
    _imp_leg(ctx, -214 * st, 60, -318 * st, 70, 38, 34)
    _imp_paw(ctx, -338 * st, 70, 30, 50, 0.1)
    _imp_leg(ctx, 166 * st, 52, 340 * st, 96, 40, 38)
    _imp_paw(ctx, 362 * st, 102, 58, 29, 0.3)
    A.put("paw_l", -340 * st, 32)
    A.put("paw_r", 362 * st, 102)
    cb = _epts(196 * st, 4, 92, 92, 14, a0=0.2)
    _shaded(ctx, lambda c: _scallop(c, cb, 13, 0.12, 9, 0.35), IMP_CR, IMP_CRD, off=(10.0, 16.0))
    A.put("chest", 196 * st, 4)
    A.put("center", 0, 0)
    ctx.save()
    ctx.translate(262 * st, -126)
    ctx.rotate(-0.06 + hrot)
    eb = 1.2 + 0.14 * _sin(TAU * 6 * t)
    eb2 = 1.3 + 0.14 * _sin(TAU * 6 * t + 1.3)
    _imp_head(ctx, A, t, e, la, lb, bl, pv, 0.5, (eb, -eb2), True, "grin",
              10.0 * _sin(TAU * 6 * t), tdir=-1.0, blow=0.9)
    ctx.restore()
    ctx.restore()


def _imp_tug(ctx, A, t, e, la, lb, bl, pv, ears, wag_a, hold):
    """Tug-of-war: braced, leaning back, cage handle in the grinning mouth."""
    yank = 0.5 + 0.5 * _sin(TAU * 2.2 * t)
    ox = -14.0 * yank
    wag_a = 0.32 * _sin(TAU * 3.0 * t) + wag_a
    _imp_tail(ctx, A, -222 + ox, -190, -0.75, 1.0, wag_a)
    _imp_leg(ctx, 16 + ox, -200, 128, -44, 32, 30, IMP_FAR, IMP_DK)
    _imp_paw(ctx, 146, -27, 52, 26, 0.0, IMP_CRD, IMP_DK)
    bpts = _epts(-70 + ox, -212, 182, 158, 30, rot=-0.42, a0=0.1)
    _shaded(ctx, _imp_body_path(bpts, 17, 8, flat=False), IMP, IMP_DK, off=(10.0, 24.0))
    hp = _epts(-170 + ox * 0.5, -96, 98, 90, 16)
    _shaded(ctx, lambda c: _scallop(c, hp, 12, 0.2, 7, 0.3,
                                    lambda qx, qy: smoothstep((-qy - 70) / 30.0)),
            IMP, IMP_DK, off=(8.0, 20.0))
    _imp_paw(ctx, -150, -27, 62, 28)
    _imp_leg(ctx, 44 + ox, -196, 168, -44, 36, 34)
    _imp_paw(ctx, 190, -28, 58, 28)
    A.put("paw_l", -150, -27)
    A.put("paw_r", 190, -28)
    cb = _epts(60 + ox, -270, 92, 92, 14, a0=0.2)
    _shaded(ctx, lambda c: _scallop(c, cb, 13, 0.12, 9, 0.35), IMP_CR, IMP_CRD, off=(10.0, 16.0))
    A.put("chest", 60 + ox, -260)
    A.put("center", -60 + ox, -220)
    ctx.save()
    shake = 0.07 * _sin(TAU * 4.4 * t)
    ctx.translate(120 + ox * 1.4, -420 - 6 * yank)
    hang = -0.16 - 0.08 * yank + shake
    ctx.rotate(hang)
    ee = dict(e)
    ee["grin"] = max(1.0, e["grin"])
    ee["tongue"] = max(0.9, e["tongue"])
    _imp_head(ctx, A, t, ee, la, lb, bl, pv * 0.5, 0.42, (ears[0] - 0.1, ears[1] + 0.25), False,
              "clamp", 10 * _sin(TAU * 4.4 * t), hold, 1.0, hang)
    ctx.restore()


def _imp_lie(ctx, A, t, e, la, lb, bl, pv, hrot, hbob, ears, swing, wag_a):
    _imp_tail(ctx, A, 200, -40, 0.95, 0.9, wag_a * 0.6)
    bpts = [(px, min(py, -6.0)) for (px, py) in
            _epts(0, -128 - pv, 250 + 2 * pv, 120 + 3 * pv, 32, a0=0.1)]
    _shaded(ctx, _imp_body_path(bpts, 17, 12), IMP, IMP_DK, off=(20.0, 18.0))
    for sd in (-1, 1):
        hp = _epts(sd * 206, -76, 80, 66, 14)
        _shaded(ctx, lambda c, hp=hp: _scallop(c, hp, 11, 0.2, 13 + sd, 0.3,
                                               lambda qx, qy: smoothstep((-qy - 50) / 30.0)),
                IMP, IMP_DK, off=(10.0, 16.0))
        _imp_paw(ctx, sd * 250, -24, 54, 24)
    for sd in (-1, 1):
        _imp_leg(ctx, sd * 92, -110, sd * 100, -40, 34, 32)
        _imp_paw(ctx, sd * 104, -28, 66, 30)
        A.put("paw_l" if sd < 0 else "paw_r", sd * 104, -28)
    A.put("chest", 0, -150)
    A.put("center", 0, -128)
    ctx.save()
    ctx.translate(0, -214 + hbob * 0.5)
    ctx.rotate(hrot * 0.5)
    _imp_head(ctx, A, t, e, la, lb, bl, pv, 0.0, (ears[0] + 0.3, ears[1] + 0.3), False, "grin",
              swing)
    ctx.restore()


# ============================================================================
# THE THING
# ============================================================================
TH = hexc("thing_fur")
TH_DK = hexc("thing_dk")
TH_LT = mixc("thing_fur", "#ffffff", 0.2)
TH_EYE = hexc("#120a1c")
TH_NOSE = hexc("#ff93bd")
TH_IN = mixc("thing_fur", "#ff93bd", 0.5)
LWT = 4.8

_TH_HEAD = _epts(0, 0, 33, 29, 12, a0=0.2)


def _th_head_path(ctx):
    _scallop(ctx, _TH_HEAD, 3.8, 0.22, 7, 0.3)


def _th_head(ctx, A, t, look, bl, turn=0.3, mode="normal", ears=(0.0, 0.0), lw=LWT, open_=0.0):
    """Thing head, local coords (centre 0,0, radius ~30). look is local."""
    tx = turn * 9.0
    for sd, ea in ((-1, ears[0]), (1, ears[1])):
        ctx.save()
        ctx.translate(sd * 16 + tx * 0.4, -20)
        ctx.rotate(sd * (0.28 + ea))
        r = 11.5 - sd * turn * 1.5
        circle(ctx, 0, -10, r)
        _fs(ctx, TH, lw)
        circle(ctx, 0, -9, r * 0.55)
        _f(ctx, TH_IN)
        ctx.restore()
    _shaded(ctx, _th_head_path, TH, TH_DK, off=(4.0, 6.0), lw=lw)
    A.put("head", 0, 0)
    A.put("top", 0, -34)
    es = 1.18 if mode == "wide" else 1.0
    sq = (1.0 - max(0.0, -turn) * 0.45, 1.0 - max(0.0, turn) * 0.45)
    lx, ly = look
    for i, ex in enumerate((-12.0 + tx, 13.0 + tx)):
        rx, ry = 10.8 * es * sq[i], 12.8 * es
        cx, cy = ex + lx * 2.0, -3.0 + ly * 1.6
        A.put("eA" if i == 0 else "eB", cx, cy)
        if mode == "squeeze":
            sd = 1 if i == 0 else -1
            ctx.move_to(cx - sd * 7, cy - 6)
            ctx.line_to(cx + sd * 5, cy)
            ctx.line_to(cx - sd * 7, cy + 6)
            _s(ctx, INK, lw * 0.7)
            continue
        up, upt = bl, 0.0
        if mode == "hiss":
            up = max(up, 0.36)
            upt = 0.7 if i == 0 else -0.7
        _eye(ctx, cx, cy, rx, ry, lx, ly, pr=rx * 0.62, lid=TH, up=up, upt=upt, sclera=TH_EYE,
             pupil=TH_EYE, hl=1.0, hls=1.7, lw=lw * 0.55, lidlw=lw * 0.5)
    mx = tx * 1.25
    # whiskers
    for sd in (-1, 1):
        bx_ = mx + sd * 13
        ctx.move_to(bx_, 10)
        ctx.line_to(bx_ + sd * 17, 6)
        ctx.move_to(bx_, 12)
        ctx.line_to(bx_ + sd * 16, 15)
    _s(ctx, INK, lw * 0.3)
    if mode == "hiss" or open_ > 0:
        ellipse(ctx, mx, 17, 7.5, 6.5)
        _fs(ctx, MOUTH, lw * 0.45)
    else:
        ctx.move_to(mx - 7, 13)
        ctx.curve_to(mx - 4, 16, mx - 1, 15, mx, 13)
        ctx.curve_to(mx + 1, 15, mx + 4, 16, mx + 7, 13)
        _s(ctx, INK, lw * 0.4)
    if mode == "squeeze":
        for sd in (-1, 1):   # puffed cheeks
            ctx.move_to(mx + sd * 10, 8)
            ctx.curve_to(mx + sd * 16, 10, mx + sd * 16, 17, mx + sd * 10, 19)
        _s(ctx, INK, lw * 0.35)
    for k in (-1, 0):
        ctx.rectangle(mx + k * 3.6 + 0.2, 12.5, 3.2, 5.4)
    _fs(ctx, WHITE, lw * 0.3)
    ellipse(ctx, mx, 9, 4.4, 3.3)
    _fs(ctx, TH_NOSE, lw * 0.35)
    A.put("nose", mx, 9)
    A.put("mouth", mx, 16)


def _th_tail(ctx, A, pts, w=3.8, lw=LWT):
    smooth_path(ctx, pts)
    _s(ctx, INK, w + 2 * lw * 0.75)
    smooth_path(ctx, pts)
    _s(ctx, TH_DK, w)
    A.put("tail_tip", *pts[-1])


def _th_body(ctx, cx, cy, rx, ry, rot=0.0, seed=3, lw=LWT, spiky=0.0):
    pts = _epts(cx, cy, rx, ry, 13, rot, 0.3)
    h = 4.0 + 5.0 * spiky
    _shaded(ctx, lambda c: _scallop(c, pts, h, 0.22 + 0.25 * spiky, seed, 0.3 + 0.3 * spiky),
            TH, TH_DK, off=(5.0, 7.0), lw=lw)


def _th_foot(ctx, x, y, rx=8.5, ry=4.6, rot=0.0, col=None, lw=LWT):
    ellipse(ctx, x, y, rx, ry, rot)
    _fs(ctx, col or TH, lw * 0.7)


def _th_leg(ctx, x0, y0, x1, y1, w=6.0, col=None, lw=LWT):
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    _s(ctx, INK, w + lw * 1.4)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    _s(ctx, col or TH, w)


def _speed_lines(ctx, x0, ys, length, motion, t, lw=LWT):
    if motion <= 0.02:
        return
    for i, yy in enumerate(ys):
        ph = (t * 7.0 + i * 0.37) % 1.0
        l = length * motion * (0.6 + 0.4 * hash01(i, 5))
        xs = x0 - ph * 18
        ctx.move_to(xs, yy)
        ctx.line_to(xs - l, yy)
    _s(ctx, _a(INK, 0.75), lw * 0.6)


def draw_thing(ctx, x, y, s, t, state="sit", look=(0, 0), flip=False, blink=None, motion=0.0):
    """The thing. See API_creatures.md. Returns anchors (screen coords)."""
    A = _Anch(ctx, s, flip)
    lk = _screen_look(look or (0, 0), flip)
    if blink is not None:
        bl = clamp(blink)
    else:
        bl = blink_amount(t, seed=5, rate=0.35)
    tw1 = _pulse(t, 1.4, 0.16, 3)
    tw2 = _pulse(t + 0.5, 1.7, 0.16, 4)
    _begin(ctx, x, y, s, flip)
    fn = _TH_STATES.get(state, _th_sit)
    fn(ctx, A, t, lk, bl, motion, (tw1, tw2))
    ctx.restore()
    _lr(A, "eA", "eB")
    return A.d


def _th_sit(ctx, A, t, lk, bl, motion, tw):
    sway = _sin(t * 2.1) * 0.12
    tail = [(-16, -8), (-48, -4), (-78, -10)]
    tail += [_rot(-96, -30, sway, -78, -10), _rot(-92, -54, sway * 1.6, -78, -10)]
    _th_tail(ctx, A, tail)
    br = 1.0 + 0.025 * _sin(t * TAU * 1.3)
    _th_foot(ctx, -14, -4)
    _th_foot(ctx, 18, -4)
    _th_body(ctx, 0, -36 * br, 29, 33 * br)
    ellipse(ctx, 7, -30 * br, 16, 19)
    _f(ctx, TH_LT)
    for px in (-6, 16):
        ellipse(ctx, px, -52 * br, 6.5, 5.5)
        _fs(ctx, TH, LWT * 0.6)
    A.put("center", 0, -45)
    ctx.save()
    ctx.translate(4, -86 * br)
    ctx.rotate(lk[0] * 0.08)
    _th_head(ctx, A, t, lk, bl, 0.3, "normal", (0.35 * tw[0], 0.35 * tw[1]))
    ctx.restore()


def _th_cage(ctx, A, t, lk, bl, motion, tw):
    sway = _sin(t * 1.6) * 0.1
    tail = [(-14, -6), (-34, -4), (-38, 6), (0, 4), (34, 2)]
    tail[-1] = _rot(36, -6, sway, 0, 4)
    br = 1.0 + 0.02 * _sin(t * TAU * 1.1)
    _th_foot(ctx, -13, -4)
    _th_foot(ctx, 15, -4)
    _th_body(ctx, 0, -34 * br, 30, 32 * br, 0.0, 5)
    ellipse(ctx, 2, -30 * br, 17, 19)
    _f(ctx, TH_LT)
    _th_tail(ctx, A, tail, 3.6)
    for sd in (-1, 1):
        _th_foot(ctx, sd * 22, -60, 6.5, 5.5, 0.0)
    A.put("paw_l", -22, -60)
    A.put("paw_r", 22, -60)
    A.put("center", 0, -40)
    ctx.save()
    ctx.translate(0, -80 * br)
    _th_head(ctx, A, t, lk, bl, lk[0] * 0.3, "normal", (0.55 + 0.3 * tw[0], 0.55 + 0.3 * tw[1]))
    ctx.restore()


def _th_peek(ctx, A, t, lk, bl, motion, tw):
    ctx.save()
    ctx.translate(0, -27)
    _th_head(ctx, A, t, lk, bl, clamp(lk[0], -1, 1) * 0.45, "normal",
             (0.2 + 0.4 * tw[0], 0.2 + 0.4 * tw[1]))
    ctx.restore()
    for sd in (-1, 1):
        _th_foot(ctx, sd * 15, -4, 7.5, 5.2)
    A.put("center", 0, -27)


def _th_scurry(ctx, A, t, lk, bl, motion, tw):
    T = 0.22
    ph = (t / T) * TAU
    bob = abs(_sin(ph)) * 4.0
    st = 1.0 + 0.14 * motion
    # speed smear + lines
    if motion > 0.02:
        ellipse(ctx, -40 * st, -30 - bob, 50 * motion + 20, 18)
        _f(ctx, _a(TH, 0.28 * motion))
        ellipse(ctx, -80 * st, -30 - bob, 46 * motion + 10, 11)
        _f(ctx, _a(TH, 0.16 * motion))
    _speed_lines(ctx, -70 * st, (-46, -30, -14), 70, motion, t)
    tail = []
    for i in range(5):
        tail.append((-44 * st - i * 26, -26 - bob * 0.5 + _sin(t * 16 - i * 1.1) * (2 + i * 2.6)))
    _th_tail(ctx, A, tail)
    blur = smoothstep((motion - 0.35) / 0.4)
    # far legs
    for i, hx in enumerate((-30, 22)):
        a = ph + i * PI + PI * 0.5
        fx, fy = hx * st + _cos(a) * 13, -3 - max(0.0, _sin(a)) * 8
        _th_leg(ctx, hx * st, -16 - bob, fx, fy - 2, 5.0, TH_DK)
    _th_body(ctx, -6 * st, -30 - bob, 46 * st, 24, -0.04, 9)
    if blur > 0.01:
        ellipse(ctx, -2, -6, 46 * st, 9)
        _f(ctx, _a(TH_DK, 0.35 * blur))
        for k in range(3):
            ctx.arc(-2 + (k - 1) * 22, -8, 9, PI * 0.1 + ph * 0.0, PI * 0.9)
            ctx.new_sub_path()
        _s(ctx, _a(INK, 0.6 * blur), 2.2)
    for i, hx in enumerate((-36, 16)):
        a = ph + i * PI
        fx, fy = hx * st + _cos(a) * 14, -3 - max(0.0, _sin(a)) * 8
        if blur < 0.95:
            _th_leg(ctx, hx * st, -16 - bob, fx, fy - 2, 5.5)
            _th_foot(ctx, fx + 2, fy, 6.5, 3.8)
    A.put("center", -6 * st, -30 - bob)
    ctx.save()
    ctx.translate(40 * st, -42 - bob)
    ctx.rotate(-0.08 + _sin(ph) * 0.04)
    _th_head(ctx, A, t, (max(0.4, lk[0]), lk[1]), bl, 0.75, "normal", (0.9, 0.8))
    ctx.restore()


def _th_hiss(ctx, A, t, lk, bl, motion, tw):
    tr = noise1(t * 14, 9) * 1.2      # trembling
    tail = [(-38, -46), (-52, -62), (-60, -82), (-58 + tr, -102), (-50, -118), (-38, -128)]
    tp = _taper(tail, [12, 17, 19, 18, 14, 4])
    _shaded(ctx, lambda c: _scallop(c, tp, 5.5, 0.5, 17, 0.45), TH, TH_DK, off=(3.0, 3.0),
            lw=LWT)
    A.put("tail_tip", -38, -132)
    for hx, fx in ((-24, -28), (24, 28)):
        _th_leg(ctx, hx, -34, fx, -4, 7.0, TH_DK)
    cl = [(-44, -36), (-30, -64), (-2, -78), (24, -66), (38, -42)]
    pts = _taper(cl, [36, 44, 46, 42, 34])
    _shaded(ctx, lambda c: _scallop(c, pts, 7.5, 0.45, 13, 0.5), TH, TH_DK, off=(4.0, 7.0),
            lw=LWT)
    for hx, fx in ((-32, -36), (20, 24)):
        _th_leg(ctx, hx, -30, fx + tr * 0.5, -4, 7.5)
        _th_foot(ctx, fx + 2, -4, 7.5, 4.2)
    A.put("center", 0, -56)
    ctx.save()
    ctx.translate(44, -44 + tr * 0.4)
    ctx.rotate(0.1)
    _th_head(ctx, A, t, lk, 0.0, 0.45, "hiss", (1.0, 1.0))
    ctx.restore()


def _th_leap(ctx, A, t, lk, bl, motion, tw):
    """(x, y) = body centre."""
    _speed_lines(ctx, -60, (-16, 0, 16), 60, max(motion, 0.4), t)
    tail = [(-48, 4)]
    for i in range(1, 5):
        tail.append((-48 - i * 28, 6 + i * 3 + _sin(t * 12 - i) * (2 + i * 2)))
    _th_tail(ctx, A, tail)
    _th_leg(ctx, 26, -4, 58, -2, 5.0, TH_DK)
    _th_leg(ctx, -30, 6, -64, 22, 5.0, TH_DK)
    _th_body(ctx, 0, 0, 52, 22, -0.22, 11)
    _th_leg(ctx, 30, 2, 64, 8, 5.5)
    _th_foot(ctx, 66, 8, 6, 4, -0.4)
    _th_leg(ctx, -32, 10, -66, 30, 5.5)
    _th_foot(ctx, -68, 31, 6, 4, 0.5)
    A.put("center", 0, 0)
    ctx.save()
    ctx.translate(48, -20)
    ctx.rotate(-0.25)
    _th_head(ctx, A, t, (max(0.5, lk[0]), lk[1]), 0.0, 0.6, "wide", (1.0, 0.9))
    ctx.restore()


def _th_bite(ctx, A, t, lk, bl, motion, tw):
    """(x, y) = the bite point (its clamped teeth)."""
    sw = _sin(t * TAU * 1.7) * 0.2 + noise1(t * 6, 2) * 0.08
    ctx.save()
    ctx.rotate(sw)
    tail = [(-50, 52)]
    for i in range(1, 5):
        tail.append((-52 + _sin(t * 5 - i) * i * 3, 52 + i * 24))
    _th_tail(ctx, A, tail)
    kick = _sin(t * TAU * 4) * 6
    _th_leg(ctx, -42, 50, -50, 80 + kick, 5.0, TH_DK)
    _th_body(ctx, -30, 34, 36, 25, 1.0, 13)
    _th_leg(ctx, -22, 54, -18, 82 - kick, 5.5)
    _th_foot(ctx, -18, 84 - kick, 6, 4)
    _th_leg(ctx, -6, 20, 6, 42 + kick * 0.5, 5.5)
    _th_foot(ctx, 7, 44 + kick * 0.5, 6, 4)
    A.put("center", -30, 34)
    ctx.save()
    ctx.translate(-3, -16)
    ctx.rotate(-0.1)
    _th_head(ctx, A, t, (0, 0), 0.0, 0.2, "squeeze", (0.6, 0.6))
    ctx.restore()
    ctx.restore()
    # chomp lines (pop on a 0.25 s beat)
    p = (t * 4.0) % 1.0
    k = 1.0 - p
    for i, a in enumerate((-2.4, -1.75, -0.95, -0.35, 0.35)):
        r0 = 34 + 6 * p
        r1 = r0 + 12 * k + 4
        ctx.move_to(_cos(a) * r0, -6 + _sin(a) * r0)
        ctx.line_to(_cos(a) * r1, -6 + _sin(a) * r1)
    _s(ctx, INK, LWT * 0.75)


def _th_struggle(ctx, A, t, lk, bl, motion, tw):
    """(x, y) = body centre. Wriggling (held or caught)."""
    w = _sin(t * TAU * 3.2)
    ctx.save()
    ctx.rotate(w * 0.22)
    tail = [(-20, 20)]
    for i in range(1, 5):
        tail.append((-20 - i * 18, 20 + _sin(t * 18 - i * 0.9) * (3 + i * 5)))
    _th_tail(ctx, A, tail)
    for k, (hx, hy) in enumerate(((-22, 14), (22, 14), (-26, -12), (26, -12))):
        sd = -1 if hx < 0 else 1
        fx = hx + sd * (12 + 6 * _sin(t * 21 + k * 1.7))
        fy = hy + 14 + 6 * _cos(t * 23 + k * 2.1)
        _th_leg(ctx, hx * 0.6, hy, fx, fy, 5.0, TH if k < 2 else TH_DK)
        _th_foot(ctx, fx, fy + 1, 5.5, 4.0)
    sq = 1.0 + 0.08 * w
    _th_body(ctx, 0, 0, 34 * sq, 30 / sq, 0.0, 15)
    A.put("center", 0, 0)
    ctx.save()
    ctx.translate(2, -38)
    ctx.rotate(-w * 0.18)
    mode = "squeeze" if _sin(t * TAU * 0.9) > 0.2 else "wide"
    _th_head(ctx, A, t, (_sin(t * 9) * 0.8, -0.2), 0.0, w * 0.3, mode, (0.5, 0.5))
    ctx.restore()
    ctx.restore()


_TH_STATES = {
    "sit": _th_sit, "scurry": _th_scurry, "peek": _th_peek, "hiss": _th_hiss, "leap": _th_leap,
    "bite": _th_bite, "struggle": _th_struggle, "cage_inside": _th_cage,
}


# --- sweater lump ------------------------------------------------------------
KNIT = hexc("#c9524a")


def draw_sweater_lump(ctx, x, y, s, t, wiggle=0.0, color=None, tail=0.0, flip=False):
    """A knit sweater heaped on the floor with the thing moving underneath.

    wiggle 0..1 drives the lump (0 = a still heap, 1 = it roams and jerks).
    tail 0..1 pokes the thing's tail out from under the hem. (x, y) = floor point
    under the middle; the heap is ~340 x 110 px at s=1.  color overrides the knit.
    """
    A = _Anch(ctx, s, flip)
    base = hexc(color) if color else KNIT
    dk = mixc(base, "ink", 0.3)
    rib = mixc(base, "ink", 0.12)
    w = clamp(wiggle)
    lx = 46.0 * noise1(t * (0.35 + 1.1 * w), 5) * w - 10.0
    jerk = _pulse(t, 0.9, 0.14, 8) * w * w
    lh = 16.0 + 34.0 * w * (0.6 + 0.4 * _sin(t * TAU * 1.3)) + 16.0 * jerk
    lx += 12 * jerk * noise1(t * 30, 2)
    _begin(ctx, x, y, s, flip)

    ears_k = smoothstep((w - 0.2) / 0.4)

    def top(xx):
        u = xx / 168.0
        if abs(u) >= 1.0:
            return -2.0
        mound = 60.0 * (1.0 - u * u) ** 0.9 + 7.0 * _sin(xx * 0.045 + 1.0) * (1.0 - u * u)
        d = (xx - lx) / 58.0
        bump = lh * max(0.0, 1.0 - d * d) ** 0.7 * (1.0 - u * u * 0.6)
        for ex in (-15.0, 15.0):     # its little ears pressing up under the knit
            q = (xx - lx - ex) / 9.0
            bump += 7.0 * ears_k * max(0.0, 1.0 - q * q)
        return -(mound + bump)

    xs = [-176 + i * 16.0 for i in range(23)]
    ridge = [(xx, min(-2.0, top(xx))) for xx in xs]

    def path(c):
        smooth_path(c, ridge)
        c.close_path()

    def knit(c):
        # cable columns of V stitches that ride the surface (and the lump)
        for col in range(10):
            xx = -126 + col * 28
            yt = top(xx)
            for row in range(4):
                fr = 0.18 + row * 0.22
                yy = yt * (1.0 - fr) - 2
                if yy > -10:
                    continue
                c.move_to(xx - 7, yy - 6)
                c.line_to(xx, yy + 1)
                c.line_to(xx + 7, yy - 6)
        _s(c, dk, 2.6)
        # stretch folds radiating from the lump
        yl = top(lx)
        for sd in (-1, 1):
            c.move_to(lx + sd * 16, yl + 12)
            c.curve_to(lx + sd * 40, yl + 26, lx + sd * 58, -20, lx + sd * 70, -14)
        _s(c, _a(dk, min(1.0, 0.25 + lh / 50.0)), 3.0)
        c.rectangle(-172, -18, 344, 18)
        _f(c, rib)
        for i in range(29):
            xx = -168 + i * 12
            c.move_to(xx, -16)
            c.line_to(xx, -3)
        _s(c, dk, 2.2)

    _shaded(ctx, path, base, dk, off=(16.0, 18.0), inner=knit)
    # sleeve draped over the front, with a ribbed cuff on the floor
    sl = [(-70, -44), (-104, -32), (-130, -16), (-150, -14)]
    smooth_path(ctx, sl)
    _s(ctx, INK, 30 + 2 * LW * 0.8)
    smooth_path(ctx, sl)
    _s(ctx, base, 30)
    smooth_path(ctx, [(-82, -34), (-110, -22), (-132, -10)])
    _s(ctx, dk, 2.4)
    ctx.save()
    ctx.translate(-158, -14)
    ctx.rotate(-0.12)
    _capsule(ctx, -4, 0, 8, 0, 16, 16)
    _fs(ctx, rib, LW * 0.8)
    for k in (-1.5, -0.5, 0.5, 1.5):
        ctx.move_to(-6, k * 7.5)
        ctx.line_to(9, k * 7.5)
    _s(ctx, dk, 2.2)
    ctx.restore()
    A.put("lump", lx, top(lx))
    A.put("center", 0, -40)
    if tail > 0.01:
        k = clamp(tail)
        tp = [(140, -5), (140 + 24 * k, -3), (140 + 46 * k, -10 - 10 * k * _sin(t * 3))]
        smooth_path(ctx, tp)
        _s(ctx, INK, 3.8 + 2 * LWT * 0.75)
        smooth_path(ctx, tp)
        _s(ctx, TH_DK, 3.8)
        A.put("tail_tip", *tp[-1])
    ctx.restore()
    return A.d


# ============================================================================
# SPECIMEN ZERO
# ============================================================================
SP = hexc("spec_body")
SP_DK = hexc("spec_dk")
SP_FAR = mixc("spec_body", "spec_dk", 0.6)
GLOW = hexc("power")
SHADOW = hexc("#0c0914")
SH_DK = hexc("#050308")
SH_EDGE = hexc("#3b2b66")
SCLERA = hexc("#e8ecff")
IRING = mixc("power", "hush_dk", 0.62)
PUPIL = hexc("#0b0d22")
MAW = hexc("#22091c")
TEETH = hexc("#e2f4f2")
CLAW = hexc("#d9e2ff")

_SPX = {
    #           eye scale, lids,                  pupil/iris, ears(+droop), split, tilt, mouth
    "calm":     dict(es=1.00, up=0.14, upt=0.00, lo=0.06, pr=0.52, pw=1.0, ears=0.00, split=0.0,
                     tilt=0.00, mouth="calm", look=(0, 0)),
    "snarl":    dict(es=0.92, up=0.40, upt=0.55, lo=0.24, pr=0.34, pw=0.45, ears=0.55, split=0.0,
                     tilt=0.04, mouth="snarl", look=(0, 0)),
    "wide":     dict(es=1.22, up=0.00, upt=0.00, lo=0.00, pr=0.30, pw=1.0, ears=-0.5, split=0.0,
                     tilt=-0.03, mouth="o", look=(0, 0)),
    "curious":  dict(es=1.08, up=0.04, upt=-0.1, lo=0.00, pr=0.64, pw=1.0, ears=-0.15, split=0.45,
                     tilt=-0.24, mouth="small", look=(0, 0)),
    "content":  dict(es=1.00, up=1.00, upt=0.00, lo=0.00, pr=0.5, pw=1.0, ears=0.25, split=0.0,
                     tilt=0.07, mouth="smile", look=(0, 0), closed=True),
    "eyeroll":  dict(es=1.00, up=0.14, upt=0.00, lo=0.10, pr=0.50, pw=1.0, ears=0.1, split=0.2,
                     tilt=0.0, mouth="flat", look=(0, 0)),
    "pleading": dict(es=1.15, up=0.00, upt=-0.4, lo=0.00, pr=0.76, pw=1.0, ears=0.5, split=0.0,
                     tilt=0.10, mouth="wobble", look=(0, -0.15), wet=1.0),
    "sad":      dict(es=1.00, up=0.34, upt=-0.6, lo=0.08, pr=0.52, pw=1.0, ears=0.95, split=0.0,
                     tilt=0.14, mouth="frown", look=(0, 0.6)),
    "annoyed":  dict(es=1.00, up=0.50, upt=0.00, lo=0.18, pr=0.46, pw=1.0, ears=0.15, split=0.25,
                     tilt=0.0, mouth="flat", look=(0, 0)),
}

EYEROLL_DUR = 1.25
SPEC_SCALE = 0.92         # rig units -> px at s=1 (crouch ~530 x 315 px incl. tail and ears)
SPEC_WALK_CYCLE = 0.9     # s per stride cycle (pose="walk")
SPEC_WALK_SPEED = 120.0   # ground speed (px/s at s=1) that keeps the walking feet planted


def _eyeroll(pt):
    """Eyeroll timeline -> (look_x, look_y, upper_lid, head_rot, settle 0..1)."""
    if pt < 0.0:
        return (0.0, 0.0, 0.14, 0.0, 1.0)
    if pt < 0.2:
        k = ease_in_out(pt / 0.2)
        return (0.85 * k, -0.12 * k, lerp(0.14, 0.40, k), -0.03 * k, 0.0)
    if pt < 0.95:
        k = ease_in_out((pt - 0.2) / 0.75)
        a = lerp(0.14, PI - 0.14, k)
        return (0.86 * _cos(a), -0.88 * _sin(a), 0.40 - 0.3 * _sin(k * PI),
                -0.03 - 0.07 * _sin(k * PI), 0.0)
    a = PI - 0.14
    sx, sy = 0.86 * _cos(a), -0.88 * _sin(a)
    if pt < EYEROLL_DUR:
        k = ease_in_out((pt - 0.95) / (EYEROLL_DUR - 0.95))
        return (lerp(sx, 0, k), lerp(sy, 0, k), 0.40 + 0.1 * k, lerp(-0.03, 0.0, k), k)
    return (0.0, 0.0, 0.50, 0.0, 1.0)


def _morph(f, glow):
    m = {}
    m["mass"] = 1.0 - smoothstep(seg(f, 0.0, 0.72))
    kc = smoothstep(seg(f, 0.28, 0.85))
    m["body"] = mixc(SHADOW, SP, kc)
    m["dk"] = mixc(SH_DK, SP_DK, kc)
    m["far"] = mixc(SH_DK, SP_FAR, kc)
    m["edge"] = mixc(SH_EDGE, INK, smoothstep(seg(f, 0.45, 0.9)))
    m["bedge"] = mixc(SHADOW, INK, smoothstep(seg(f, 0.22, 0.6)))
    m["shell"] = 1.0 - smoothstep(seg(f, 0.0, 0.66))
    m["tend"] = 1.0 - smoothstep(seg(f, 0.0, 0.48))
    m["curl"] = smoothstep(seg(f, 0.0, 0.42))
    m["lines"] = smoothstep(seg(f, 0.3, 0.62))
    m["eye"] = smoothstep(seg(f, 0.32, 0.82))
    m["iris"] = smoothstep(seg(f, 0.45, 0.8))
    m["pupil"] = smoothstep(seg(f, 0.55, 0.86))
    m["hl"] = ease_out_back(seg(f, 0.78, 0.95)) if f > 0.78 else 0.0
    m["maw"] = 1.0 - smoothstep(seg(f, 0.08, 0.55))
    m["trace"] = smoothstep(seg(f, 0.52, 0.93))
    m["flash"] = _sin(PI * seg(f, 0.52, 1.0))
    m["glow"] = glow
    m["f"] = f
    return m


def _spine_outline(sp, rt, rb, cap_b=0.9, cap_f=0.75):
    # subdivide spine once (midpoints) for smoother outlines
    S, T_, B_ = [sp[0]], [rt[0]], [rb[0]]
    for i in range(1, len(sp)):
        S.append(((sp[i - 1][0] + sp[i][0]) * 0.5, (sp[i - 1][1] + sp[i][1]) * 0.5))
        T_.append((rt[i - 1] + rt[i]) * 0.5)
        B_.append((rb[i - 1] + rb[i]) * 0.5)
        S.append(sp[i])
        T_.append(rt[i])
        B_.append(rb[i])
    n = len(S)
    top, bot = [], []
    back = front = None
    for i in range(n):
        x, y = S[i]
        if i == 0:
            ax, ay = S[1][0] - x, S[1][1] - y
        elif i == n - 1:
            ax, ay = x - S[i - 1][0], y - S[i - 1][1]
        else:
            ax, ay = S[i + 1][0] - S[i - 1][0], S[i + 1][1] - S[i - 1][1]
        l = _hyp(ax, ay) or 1.0
        ux, uy = ax / l, ay / l
        nx, ny = uy, -ux
        top.append((x + nx * T_[i], y + ny * T_[i]))
        bot.append((x - nx * B_[i], y - ny * B_[i]))
        if i == 0:
            r = (T_[0] + B_[0]) * 0.5
            back = (x - ux * r * cap_b + nx * (T_[0] - B_[0]) * 0.5,
                    y - uy * r * cap_b + ny * (T_[0] - B_[0]) * 0.5)
        if i == n - 1:
            r = (T_[-1] + B_[-1]) * 0.5
            front = (x + ux * r * cap_f, y + uy * r * cap_f)
    return [back] + top + [front] + bot[::-1], len(top)


def _displace(pts, m, t, seed=0, spikes_top=0):
    """Shadow-mass displacement of a closed outline (inflate + noise + back spikes)."""
    mass = m["shell"]
    if mass <= 0.005:
        return pts
    n = len(pts)
    out = []
    for i in range(n):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        l = _hyp(dx, dy) or 1.0
        nx, ny = dy / l, -dx / l
        d = mass * (30.0 + 18.0 * noise1(t * 0.9 + i * 0.83, seed))
        if 1 <= i <= spikes_top and i % 2 == 0:
            d += mass * 12.0 * (0.6 + 0.4 * noise1(t * 1.4 + i, seed + 3))
        x, y = pts[i]
        out.append((x + nx * d, y + ny * d))
    return out


def _wisp(x, y, ang, L, w0, ph, curl, side, n=7):
    """One smoke wisp: wide base, waving body, rounded tip that hooks into a curl."""
    cl = [(x, y)]
    for q in range(1, n):
        u = q / (n - 1.0)
        a = (ang + 0.6 * _sin(ph - u * 2.6) * u + (0.8 + curl * 2.2) * u * u * side
             + 1.4 * u ** 3 * side)
        cl.append((cl[-1][0] + _cos(a) * L / (n - 1.0), cl[-1][1] + _sin(a) * L / (n - 1.0)))
    ws = [w0 * (1.0 - 0.8 * (q / (n - 1.0)) ** 0.8) for q in range(n)]
    return _taper(cl, ws)


def _tendrils(R, m, t, outline, ntop):
    """Smoky wisps for the shadow shell -> list of closed point lists.

    Wide-based, rising and curling; as form rises they shorten and curl back in.
    """
    k = m["tend"]
    if k <= 0.01:
        return []
    n = len(outline)
    picks = [(1, 1.0), (3, 0.9), (5, 1.15), (7, 0.8), (ntop, 0.7), (ntop + 4, 0.75),
             (ntop + 7, 0.85), (n - 2, 0.7), (0, 1.1)]
    out = []
    curl = m["curl"]
    for j, (i, lw_) in enumerate(picks):
        i %= n
        x, y = outline[i]
        xa, ya = outline[i - 1]
        xb, yb = outline[(i + 1) % n]
        dx, dy = xb - xa, yb - ya
        l = _hyp(dx, dy) or 1.0
        nx, ny = dy / l, -dx / l
        rise = 0.55 if ny < 0.3 else 0.15
        ang = _atan2(ny - rise, nx)
        L = (80.0 + 70.0 * hash01(j, 77)) * lw_ * (0.2 + 0.8 * k)
        w0 = (40.0 + 16.0 * hash01(j, 78)) * (0.4 + 0.6 * k)
        ph = t * (1.5 + 0.5 * hash01(j, 79)) + j * 1.7
        out.append(_wisp(x - nx * 14, y - ny * 14, ang, L, w0, ph, curl, 1 if j % 2 else -1))
    return out


def _spec_rig(pose, t, pt, wr, point_angle):
    """Skeleton for a pose (local coords, facing right, ground y=0)."""
    R = {"tail_front": False, "claws": 0.0, "airborne": False, "held": False, "point": False,
         "head_scale": 1.2}
    br = _sin(t * TAU / 3.0)
    if pose == "leap":
        R["airborne"] = True
        R["claws"] = 1.0
        R["sp"] = [(-128, 14), (-50, 2), (38, -14), (96, -40)]
        R["rt"] = [40, 40, 44, 28]
        R["rb"] = [38, 38, 44, 28]
        R["head"] = (150, -56, -0.18)
        R["legs"] = [
            ("front", False, [(32, 6), (110, 34), (196, 56)]),
            ("hind", False, [(-112, 18), (-156, 44), (-206, 62), (-238, 76)]),
            ("hind", True, [(-120, 20), (-160, 52), (-214, 66), (-248, 86)]),
            ("front", True, [(50, 4), (136, 30), (226, 40)]),
        ]
        R["haunch"] = (-112, 8, 50, 42, 0.2)
        w = _sin(t * 9) * 8
        R["tail"] = [(-160, 12), (-212, 0 + w * 0.3), (-262, -16 - w * 0.5), (-312, -24 + w),
                     (-360, -18 - w), (-400, -30 + w)]
        R["center"] = (0, 0)
    elif pose in ("held", "writhe"):
        R["airborne"] = R["held"] = True
        a = wr if wr > 0 else (1.0 if pose == "writhe" else 0.0)
        R["held_wr"] = a
        ph = t * TAU * 1.7
        def bend(i):
            return a * _sin(ph + i * 1.25) * 22
        R["sp"] = [(-112, 2 + bend(0)), (-48, 22 + bend(1)), (34, 16 + bend(2)),
                   (90, -10 + bend(3))]
        R["rt"] = [44, 40, 44, 28]
        R["rb"] = [44, 38, 46, 28]
        R["head"] = (142, -26 + bend(4) * 1.2, 0.14 + a * 0.35 * _sin(ph * 1.3 + 2))
        kick = [a * _sin(t * TAU * 2.6 + k * 1.9) * 26 for k in range(4)]
        R["legs"] = [
            ("hind", False, [(-96, 22), (-80, 66), (-104, 98 + kick[0]), (-92, 120 + kick[0])]),
            ("front", False, [(28, 30), (40, 76), (34 + kick[1] * 0.5, 104 + kick[1])]),
            ("hind", True, [(-110, 26), (-92, 74), (-118, 108 + kick[2]), (-106, 132 + kick[2])]),
            ("front", True, [(50, 32), (66, 70), (60 + kick[3] * 0.5, 104 + kick[3])]),
        ]
        R["front_last"] = True
        R["haunch"] = (-108, 6, 50, 46, 0.0)
        w = _sin(t * TAU * 0.9) * (6 + a * 26)
        R["tail"] = [(-152, -2), (-178, 34), (-190 + w * 0.4, 80), (-180 + w, 126),
                     (-160 + w * 1.4, 160), (-134 + w * 1.6, 176)]
        R["hold"] = {"front": (38, 74), "back": (-98, 64), "chest": (34, 16),
                     "rump": (-112, 2), "belly": (-44, 80)}
        R["center"] = (0, 0)
    elif pose in ("sit", "point"):
        R["sp"] = [(-46, -66), (-34, -124), (-2, -176), (30, -214)]
        R["rt"] = [58, 46, 40, 28]
        R["rb"] = [52, 44, 50, 28]
        R["head"] = (72, -256 + br * 1.5, -0.04)
        R["haunch"] = (-40, -66, 70, 60, 0.0)
        legs = [
            ("front", False, [(6, -164), (14, -92), (18, -10)]),
            ("hind", True, [(-38, -62), (10, -42), (16, -16), (44, -9)]),
        ]
        if pose == "point":
            R["point"] = True
            a = clamp(point_angle, -0.7, 0.9)
            sx_, sy_ = 34, -170
            ex, ey = sx_ + _cos(a) * 64, sy_ + _sin(a) * 64 + 6
            px_, py_ = ex + _cos(a) * 62, ey + _sin(a) * 62
            legs.append(("front", True, [(sx_, sy_), (ex, ey), (px_, py_)]))
            R["paw_dir"] = a
        else:
            legs.append(("front", True, [(28, -164), (40, -92), (46, -10)]))
        R["legs"] = legs
        sw = _sin(t * 1.3) * 6
        R["tail"] = [(-100, -34), (-132, -14), (-104, -2), (-44, -4), (18, -6), (66 + sw, -20)]
        R["tail_front"] = True
        R["center"] = (0, -120)
    elif pose == "tug":
        yank = 0.5 + 0.5 * _sin(TAU * 2.0 * t)
        ox = -12 * yank
        R["sp"] = [(-118 + ox, -70), (-58 + ox, -88), (16 + ox, -102), (70 + ox * 0.6, -136)]
        R["rt"] = [46, 42, 44, 28]
        R["rb"] = [44, 40, 46, 28]
        R["head"] = (116 + ox * 0.3, -150 - 4 * yank, 0.32 + 0.08 * _sin(TAU * 4.0 * t))
        R["haunch"] = (-104 + ox, -66, 54, 50, 0.0)
        R["legs"] = [
            ("front", False, [(20 + ox, -90), (64, -52), (110, -10)]),
            ("hind", False, [(-96 + ox, -66), (-60, -40), (-82, -18), (-60, -9)]),
            ("hind", True, [(-108 + ox, -60), (-70, -36), (-96, -16), (-72, -9)]),
            ("front", True, [(36 + ox, -84), (84, -50), (134, -10)]),
        ]
        w = _sin(t * 4.0) * 10
        R["tail"] = [(-160 + ox, -70), (-210, -56 + w * 0.3), (-256, -66 - w * 0.5),
                     (-294, -96 + w), (-308, -136 - w * 0.6), (-300, -170 + w)]
        R["center"] = (-30 + ox, -100)
        R["mouth_mode"] = "clamp"
    elif pose == "nuzzle":
        rub = _sin(TAU * pt / 1.2)
        R["sp"] = [(-118, -168), (-48, -176), (40, -172), (92, -206)]
        R["rt"] = [42, 40, 44, 28]
        R["rb"] = [42, 38, 46, 28]
        R["head"] = (132 + 6 * rub, -240 - 6 * rub, -0.42 + 0.1 * rub)
        R["haunch"] = (-112, -162, 52, 48, 0.0)
        R["legs"] = _stand_legs(0.0, stand=True)
        R["tail"] = [(-160, -178), (-204, -218), (-222, -272), (-206, -322), (-172, -340),
                     (-146 + 4 * rub, -326)]
        R["center"] = (-20, -170)
        R["force_content"] = True
    elif pose in ("walk", "stand"):
        ph = (pt / 0.9) % 1.0 if pose == "walk" else 0.0
        bob = -abs(_sin(ph * TAU)) * 4.0 if pose == "walk" else br * 1.5
        R["sp"] = [(-118, -170 + bob), (-48, -176 + bob), (40, -170 + bob), (94, -196 + bob)]
        R["rt"] = [42, 40, 44, 28]
        R["rb"] = [42, 38, 46, 28]
        R["head"] = (144, -222 + bob * 1.3, -0.04 + (_sin(ph * TAU * 2) * 0.02))
        R["haunch"] = (-112, -162 + bob, 52, 48, 0.0)
        R["legs"] = _stand_legs(ph, stand=(pose == "stand"), bob=bob)
        sw = _sin(t * 2.4) * 8
        R["tail"] = [(-160, -170 + bob), (-210, -184), (-262, -176 + sw * 0.5),
                     (-306, -192 - sw * 0.3), (-334, -228 + sw), (-336, -262 - sw * 0.4)]
        R["center"] = (-20, -170)
    else:   # crouch
        wig = _sin(t * TAU * 1.1) * 3.0
        R["sp"] = [(-118 + wig * 0.4, -152 + wig), (-46, -146), (40, -118), (96, -128)]
        R["rt"] = [44, 42, 46, 28]
        R["rb"] = [44, 40, 50, 28]
        R["head"] = (150, -132 + br, 0.04)
        R["haunch"] = (-106, -130 + wig * 0.6, 54, 50, 0.0)
        R["legs"] = [
            ("front", False, [(32, -104), (62, -56), (104, -10)]),
            ("hind", False, [(-94, -128), (-56, -84), (-92, -36), (-70, -9)]),
            ("hind", True, [(-106, -124), (-64, -76), (-108, -32), (-84, -9)]),
            ("front", True, [(50, -100), (88, -54), (130, -10)]),
        ]
        lash = _sin(t * 2.4)
        R["tail"] = [(-158, -154 + wig), (-210, -180), (-262, -172 + lash * 4),
                     (-302, -192 - lash * 6), (-322, -232 + lash * 10), (-314, -272 + lash * 16)]
        R["center"] = (-20, -130)
    return R


def _stand_legs(ph, stand=False, bob=0.0):
    legs = []
    spec = (("hind", False, -86, 0.5), ("front", False, 32, 0.75),
            ("hind", True, -104, 0.0), ("front", True, 52, 0.25))
    for kind, near, hx, off in spec:
        u = (ph + off) % 1.0
        stride = 0.0 if stand else 70.0
        if u < 0.6:
            fx = hx + 14 + stride * (0.5 - u / 0.6)
            fy = -9.0
        else:
            v = (u - 0.6) / 0.4
            fx = hx + 14 + stride * (-0.5 + v)
            fy = -9.0 - _sin(PI * v) * 24.0
        if kind == "front":
            top = (hx, -150 + bob)
            kx, ky = _ik(top[0], top[1], fx, fy, 74, 72, 1)
            legs.append((kind, near, [top, (kx, ky), (fx, fy)]))
        else:
            top = (hx, -152 + bob)
            hock_y = fy - 40
            kx, ky = _ik(top[0], top[1], fx - 26, hock_y, 66, 50, -1)
            legs.append((kind, near, [top, (kx, ky), (fx - 26, hock_y), (fx, fy)]))
    return legs


def _spec_leg(ctx, pts, kind, col, edge, lw, claws, paw_dir=None):
    ws = (38, 30) if kind == "front" else (38, 28, 26)
    n = len(pts)
    px, py = pts[-1]
    qx, qy = pts[-2]
    a = _atan2(py - qy, px - qx) if paw_dir is None else paw_dir
    # the paw sits flat on the ground unless the leg is clearly not vertical
    pa = 0.0 if paw_dir is None and abs(a - PI / 2) < 0.6 else a - PI / 2
    if paw_dir is not None:
        pa = a
    for pas in (0, 1):
        for i in range(n - 1):
            ctx.move_to(*pts[i])
            ctx.line_to(*pts[i + 1])
            w = ws[min(i, len(ws) - 1)]
            _s(ctx, edge if pas == 0 else col, w + (2 * lw if pas == 0 else 0))
        if paw_dir is not None:
            ellipse(ctx, px, py, 24, 15, pa)
        else:
            ellipse(ctx, px + 6, py, 25, 14, pa)
        if pas == 0:
            ctx.set_source_rgba(*edge)
            ctx.set_line_width(2 * lw)
            ctx.stroke()
        else:
            _f(ctx, col)
    if claws > 0.01:
        cx_, cy_ = (px + 6, py) if paw_dir is None else (px, py)
        for k in (-1, 0, 1):
            bx_, by_ = _rot(cx_ + 22, cy_ + k * 7, pa, cx_, cy_)
            tx_, ty_ = _rot(cx_ + 23 + 12 * claws, cy_ + k * 8 + 4, pa, cx_, cy_)
            ctx.move_to(bx_, by_ - 3)
            ctx.line_to(tx_, ty_)
            ctx.line_to(bx_, by_ + 3)
            ctx.close_path()
        _f(ctx, CLAW)
    if paw_dir is not None:
        return _rot(px + 30, py, pa, px, py)
    return (px + 6, py)


def _spec_ear_pts(m, t, seed):
    base = [(14, 8), (10, -16), (-14, -40), (-52, -60), (-94, -74), (-130, -80),
            (-106, -62), (-98, -52), (-80, -46), (-70, -32), (-52, -26), (-38, -10), (-14, 12)]
    mass = m["mass"]
    if mass < 0.01:
        return base
    out = []
    sc = 1.0 - 0.3 * mass
    for i, (x, y) in enumerate(base):
        j = mass * (5 + 7 * noise1(t * 1.2 + i * 1.3, seed))
        out.append((x * sc, y * sc - j * (1 if i < 6 else -1)))
    return out


def _spec_ear(ctx, x, y, ang, m, t, col, far, lw):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(0.9, 0.9)
    pts = _spec_ear_pts(m, t, 51 if far else 52)
    smooth_path(ctx, pts, closed=True)
    _fs(ctx, col, lw, m["edge"])
    if not far and m["mass"] < 0.6:
        ka = 1.0 - m["mass"]
        for (ex, ey) in ((-120, -74), (-96, -52), (-68, -32)):
            ctx.move_to(-4, 2)
            ctx.curve_to(ex * 0.35, ey * 0.2, ex * 0.7, ey * 0.62, ex, ey)
        _s(ctx, _a(m["dk"], ka), 3.2)
        g = m["glow"] * m["trace"]
        if g > 0.01:
            ctx.move_to(6, -14)
            ctx.curve_to(-20, -38, -60, -60, -122, -76)
            _s(ctx, _a(GLOW, 0.75 * g), 3.0)
    ctx.restore()


def _spec_glow_stroke(ctx, path, m, wide=26.0):
    g = m["glow"] * (m["trace"] * 0.8 + m["flash"] * 0.5)
    if g <= 0.01:
        return
    path(ctx)
    _s(ctx, _a(GLOW, 0.10 * g), wide)
    path(ctx)
    _s(ctx, _a(GLOW, 0.16 * g), wide * 0.5)


def _spec_rim(ctx, path, m, perim, dy=8.0, w=5.0):
    """Teal rim along the top edges (inside the current clip). Traces in during the morph."""
    g = m["glow"]
    tr = m["trace"]
    if g <= 0.01 or tr <= 0.01:
        return
    ctx.save()
    ctx.translate(0, dy)
    path(ctx)
    ctx.restore()
    if tr < 0.999:
        ctx.set_dash([perim * tr, perim * 2.0], 0)
    _s(ctx, _a(GLOW, min(1.0, (0.8 + 0.6 * m["flash"]) * g)), w + 4.0 * m["flash"])
    ctx.set_dash([], 0)


def _perim(pts):
    n = len(pts)
    return sum(_hyp(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(n))


def _spec_head(ctx, A, t, R, M, E, look, bl, yaw, mirror, lw, mouth_mode=None, hold=None):
    """Specimen head in head-local coords (facing right, centre 0,0)."""
    mass = M["mass"]
    body, dk, edge = M["body"], M["dk"], M["edge"]
    sy = _sin(abs(yaw))
    if mirror:
        ctx.scale(-1, 1)
        look = (-look[0], look[1])
    mx = 8 + 62 * sy
    exn, exf = -30 + 50 * sy, 34 + 24 * sy
    fsq = 1.0 - 0.28 * sy
    ears = E["ears"]
    split = E.get("split", 0.0)
    ear_anim = 0.05 * _sin(t * 1.7) + 0.25 * _pulse(t, 2.3, 0.22, 61) * (1 - mass)
    # head wisps (form 0) behind the skull; they pull in as the ears form
    if M["tend"] > 0.01:
        hw = []
        for j, (bx0, by0, a0) in enumerate(((-30, -40, -2.2), (0, -52, -1.9), (-50, -10, -2.7))):
            L = (70 + 30 * hash01(j, 81)) * (0.2 + 0.8 * M["tend"])
            hw.append(_wisp(bx0, by0, a0, L, 34 * (0.4 + 0.6 * M["tend"]), t * 1.7 + j * 2.1,
                            M["curl"], 1 if j % 2 else -1, 6))
        for wp in hw:
            smooth_path(ctx, wp, closed=True)
            _s(ctx, _a(SH_EDGE, min(1.0, M["shell"] * 3)), 2 * lw)
        for wp in hw:
            smooth_path(ctx, wp, closed=True)
            _f(ctx, SHADOW)
    # far ear (behind the skull)
    _spec_ear(ctx, -6 + 12 * sy, -46, -0.1 - (ears - split) * 0.6 + ear_anim * 0.7, M, t,
              M["far"], True, lw)
    # skull + jaw + muzzle (union outline)
    ins = 1.0 + 0.16 * mass
    if mass > 0.01:
        sk = []
        for i in range(14):
            a = TAU * i / 14
            r = 1.0 + mass * 0.16 * noise1(t * 1.2 + i * 1.1, 71)
            sk.append((64 * ins * r * _cos(a), 56 * ins * r * _sin(a)))
        skull = lambda c: smooth_path(c, sk, closed=True)
    else:
        sk = None
        skull = lambda c: ellipse(c, 0, 0, 64, 56)
    mk = 1.0 - 0.45 * mass
    mrx, mry = (36 + 8 * sy) * mk, 25 * mk
    jx = mx * 0.45 - 6

    def parts(c):
        skull(c)
        ellipse(c, jx, 26, 48, 30)
        ellipse(c, mx, 22, mrx, mry)

    _spec_glow_stroke(ctx, parts, M, 24.0)
    parts(ctx)
    _s(ctx, edge, 2 * lw)
    parts(ctx)
    ctx.set_source_rgba(*dk)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.translate(-4, -14)
    parts(ctx)
    _f(ctx, body)
    ctx.translate(4, 14)
    ctx.restore()
    if M["glow"] > 0.01 and M["trace"] > 0.01:
        ctx.save()
        ctx.scale(56 * ins, 48 * ins)
        a0 = PI * 1.02
        ctx.arc(0, 0, 1, a0, a0 + PI * 0.78 * M["trace"])
        ctx.restore()
        _s(ctx, _a(GLOW, min(1.0, (0.8 + 0.6 * M["flash"]) * M["glow"])), 4.5 + 3 * M["flash"])
    # near ear
    _spec_ear(ctx, -30 + 8 * sy, -38, -0.24 - (ears + split) * 0.6 + ear_anim, M, t, body, False,
              lw)
    A.put("head", 0, 0)
    A.put("nose", 8 + 62 * sy + 24, 19)
    # eyes
    k = M["eye"]
    closed = E.get("closed", False)
    es = lerp(0.82, E["es"], k)
    up = lerp(0.45, E["up"], k)
    lo = lerp(0.42, E["lo"], k)
    upt = lerp(0.65, E["upt"], k)
    if not closed:
        up = up + (1.0 - up) * bl
    sclera = mixc(GLOW, SCLERA, M["iris"])
    eyes = ((exn, -4.0, 29 * es, 32 * es, upt, "eA"), (exf, -6.0, 29 * es * fsq, 31 * es, -upt,
                                                        "eB"))
    g = M["glow"]
    for (cx, cy, rx, ry, ut, nm) in eyes:
        A.put(nm, cx, cy)
        if g > 0.01:
            radial_glow(ctx, cx, cy, ry * 2.0, GLOW, 0.26 * g * (1.0 - 0.7 * float(closed)))
    for (cx, cy, rx, ry, ut, nm) in eyes:
        if closed and k > 0.5:
            _happy_eye(ctx, cx, cy, rx * 0.8, ry * 0.8, lw * 1.1, INK,
                       down=E.get("sleep", False))
            continue
        ir = min(rx, ry) * 0.68 * M["iris"]
        _eye(ctx, cx, cy, rx, ry, look[0], look[1], pr=ir * E["pr"] * M["pupil"], lid=body,
             up=up, upt=ut, lo=lo, lot=-ut * 0.4, sclera=sclera, pupil=PUPIL, iris=GLOW,
             ring=IRING, ir=ir, hl=M["hl"], hls=1.25, lw=lw * 0.9,
             ink=_a(INK, M["lines"]), pw=E["pw"], wet=E.get("wet", 0.0),
             outline=M["lines"] > 0.02)
    # mouth / maw
    mm = mouth_mode or E["mouth"]
    _spec_mouth(ctx, A, t, M, mm, mx, mrx, lw, hold)


def _spec_mouth(ctx, A, t, M, mm, mx, mrx, lw, hold):
    edge = M["edge"]
    mk = M["maw"]
    if mk > 0.02:
        # jagged maw with too many teeth; shrinks toward the real mouth as form rises
        snap = 0.5 + 0.5 * _sin(t * 3.1) * (0.6 + 0.4 * noise1(t * 2, 4))
        wl, wr_ = lerp(mx - 20, -66, mk), lerp(mx + 20, mx + 60, mk)
        top = lerp(36, 12, mk)
        dep = (22 + 34 * snap) * mk
        cxm = (wl + wr_) * 0.5
        ctx.move_to(wl, top)
        ctx.curve_to(cxm - 20, top + 10 * mk, cxm + 20, top + 10 * mk, wr_, top - 2)
        ctx.curve_to(wr_ - 10, top + dep, wl + 10, top + dep, wl, top)
        ctx.close_path()
        ctx.set_source_rgba(*MAW)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        nt = 11
        for i in range(nt):
            u = (i + 0.5) / nt
            xx = lerp(wl + 4, wr_ - 4, u)
            ytop = top + 10 * mk * 0.75 * (1 - (2 * u - 1) ** 2)
            hgt = (12 + 8 * hash01(i, 3)) * mk
            ctx.move_to(xx - 5.5 * mk - 1, ytop - 4)
            ctx.line_to(xx + 5.5 * mk + 1, ytop - 4)
            ctx.line_to(xx, ytop + hgt)
            ctx.close_path()
        for i in range(nt - 1):
            u = (i + 1.0) / nt
            xx = lerp(wl + 4, wr_ - 4, u)
            ybot = top + dep * 0.75 * (1 - (2 * u - 1) ** 2 * 0.8) + 4
            hgt = (11 + 7 * hash01(i, 4)) * mk
            ctx.move_to(xx - 5 * mk - 1, ybot + 6)
            ctx.line_to(xx + 5 * mk + 1, ybot + 6)
            ctx.line_to(xx, ybot - hgt)
            ctx.close_path()
        _f(ctx, TEETH)
        ctx.restore()
        A.put("mouth", cxm, top + dep * 0.4)
        if mk > 0.5:
            if mm == "clamp":
                A.call(hold, angle=0.0)
                _setup(ctx)
            return
    # true-form mouth
    k = 1.0 - mk
    ink = _a(edge, k) if k < 1 else edge
    bx_ = mx - 4
    if mm == "snarl":
        ctx.move_to(bx_ - 30, 33)
        ctx.curve_to(bx_ - 10, 28, bx_ + 14, 28, bx_ + 34, 31)
        ctx.curve_to(bx_ + 24, 52, bx_ - 16, 56, bx_ - 30, 33)
        ctx.close_path()
        ctx.set_source_rgba(*MAW)
        ctx.fill_preserve()
        _s(ctx, ink, lw * 0.8)
        for fx_, fy_, d in ((bx_ - 16, 31, 1), (bx_ + 18, 30, 1), (bx_ - 8, 48, -1),
                            (bx_ + 10, 47, -1)):
            ctx.move_to(fx_ - 4, fy_)
            ctx.line_to(fx_ + 4, fy_)
            ctx.line_to(fx_, fy_ + d * 11)
            ctx.close_path()
        _f(ctx, TEETH)
        ctx.move_to(mx + 4, 2)
        ctx.curve_to(mx + 10, -2, mx + 16, -2, mx + 22, 2)
        ctx.move_to(mx + 2, 8)
        ctx.curve_to(mx + 8, 4, mx + 14, 4, mx + 20, 8)
        _s(ctx, ink, lw * 0.5)
        A.put("mouth", bx_ + 2, 42)
    elif mm == "o":
        ellipse(ctx, bx_ + 6, 42, 7, 9)
        ctx.set_source_rgba(*MAW)
        ctx.fill_preserve()
        _s(ctx, ink, lw * 0.7)
        A.put("mouth", bx_ + 6, 42)
    elif mm == "clamp":
        ctx.move_to(bx_ - 28, 36)
        ctx.curve_to(bx_ - 6, 42, bx_ + 18, 42, bx_ + 36, 36)
        _s(ctx, ink, lw * 0.8)
        A.put("mouth", bx_ + 38, 40)
        A.call(hold, angle=0.0)
        _setup(ctx)
        for fx_ in (bx_ - 8, bx_ + 16):
            ctx.move_to(fx_ - 4, 38)
            ctx.line_to(fx_ + 4, 38)
            ctx.line_to(fx_, 50)
            ctx.close_path()
        ctx.set_source_rgba(*TEETH)
        ctx.fill_preserve()
        _s(ctx, ink, lw * 0.35)
    else:
        if mm == "smile":
            pts = [(bx_ - 28, 32), (bx_ - 14, 42), (bx_, 36), (bx_ + 14, 42), (bx_ + 26, 32)]
        elif mm == "frown":
            pts = [(bx_ - 22, 44), (bx_, 36), (bx_ + 22, 44)]
        elif mm == "flat":
            pts = [(bx_ - 22, 39), (bx_ + 4, 40), (bx_ + 26, 37)]
        elif mm == "wobble":
            pts = [(bx_ - 20, 40), (bx_ - 8, 37), (bx_ + 4, 41), (bx_ + 16, 37), (bx_ + 24, 40)]
        elif mm == "small":
            pts = [(bx_ - 8, 38), (bx_ + 4, 42), (bx_ + 16, 38)]
        else:   # calm
            pts = [(bx_ - 26, 35), (bx_ - 2, 41), (bx_ + 24, 35)]
        smooth_path(ctx, pts)
        _s(ctx, ink, lw * 0.75)
        A.put("mouth", bx_, 40)
    # nose
    ellipse(ctx, mx + 24, 19, 8, 6)
    ctx.set_source_rgba(*PUPIL)
    ctx.fill()
    circle(ctx, mx + 22, 17, 2.2)
    _f(ctx, _a(WHITE, 0.7 * k))


def _spec_tail(ctx, A, R, M, t, lw):
    pts = list(R["tail"])
    mass = M["mass"]
    if mass > 0.01:
        pts = [(x + mass * 14 * _sin(t * 2.1 - i * 1.1) * i, y + mass * 12 * _cos(t * 1.7 - i)
                * i) for i, (x, y) in enumerate(pts)]
    ws = [30 + 24 * mass, 26 + 22 * mass, 20 + 20 * mass, 15 + 18 * mass, 10 + 14 * mass,
          6 + 10 * mass]
    outline = _taper(pts, ws)
    tx, ty = pts[-1]
    a = _atan2(ty - pts[-2][1], tx - pts[-2][0])
    fin = []
    spk = 1.0 - 0.75 * mass
    for (fx, fy) in ((-4, 0), (10, -15 * spk), (34 * spk, -12), (48 * spk, 0), (34 * spk, 12),
                     (10, 15 * spk)):
        fin.append(_rot(tx + fx, ty + fy, a, tx, ty))
    A.put("tail_tip", *_rot(tx + 48 * spk, ty, a, tx, ty))

    def path(c):
        smooth_path(c, outline, closed=True)
        if mass < 0.7:
            smooth_path(c, fin, closed=True)
    _spec_glow_stroke(ctx, path, M, 20.0)
    path(ctx)
    _s(ctx, M["edge"], 2 * lw)
    path(ctx)
    _f(ctx, M["body"])
    ctx.save()
    smooth_path(ctx, outline, closed=True)
    ctx.clip()
    _spec_rim(ctx, lambda c: smooth_path(c, outline, closed=True), M, _perim(outline), 6.0, 4.0)
    ctx.restore()


def draw_specimen(ctx, x, y, s, t, form=1.0, pose="crouch", expr="calm", look=(0, 0), glow=1.0,
                  writhe=0.0, sleeping=False, blink=None, flip=False, pose_t=None, face=1.0,
                  point_angle=0.0, hold=None, tilt=0.0):
    """Specimen Zero. See API_creatures.md. Returns anchors (screen coords)."""
    if sleeping:
        return draw_specimen_pod_sleeper(ctx, x, y, s, t, 0, flip=flip, glow=glow)
    A = _Anch(ctx, s, flip)
    f = clamp(form)
    pt = t if pose_t is None else pose_t
    lk = _screen_look(look or (0, 0), flip)
    M = _morph(f, clamp(glow, 0.0, 2.0))
    E = dict(_SPX.get(expr, _SPX["calm"]))
    R = _spec_rig(pose, t, pt, clamp(writhe), point_angle)
    if R.get("force_content"):
        E.update(_SPX["content"])
    head_rot_extra = E["tilt"] + tilt
    rolling = False
    if expr == "eyeroll":
        ept = pt % 2.6 if pose_t is None else pt
        rolling = 0.0 <= ept < EYEROLL_DUR
        rx_, ry_, up_, hr_, settle = _eyeroll(ept)
        E["up"] = up_
        head_rot_extra += hr_
        lk = (rx_ + lk[0] * settle, ry_ + lk[1] * settle)
    else:
        lk = (lk[0] + E["look"][0], lk[1] + E["look"][1])
    if expr == "content" or R.get("force_content"):
        head_rot_extra += 0.03 * _sin(t * TAU * 0.5)
    if blink is not None:
        bl = clamp(blink)
    elif f < 0.5 or rolling:
        bl = 0.0
    else:
        bl = blink_amount(t, seed=23, rate=0.22)
    lw = LW / SPEC_SCALE
    _begin(ctx, x, y, s * SPEC_SCALE, flip)
    edge = M["edge"]
    # ------------------------------------------------------------------ tail
    if not R["tail_front"]:
        _spec_tail(ctx, A, R, M, t, lw)
    # ------------------------------------------------------------------ far legs
    legs = R["legs"]
    paw_pt = None
    for kind, near, pts in legs:
        if not near:
            _spec_leg(ctx, pts, kind, M["far"], edge, lw, R["claws"])
    # ------------------------------------------------------------------ body
    nsp = len(R["sp"])
    rt = [r * (1.3 if i < nsp - 1 else 1.1) for i, r in enumerate(R["rt"])]
    rb = [r * (1.26 if i < nsp - 1 else 1.08) for i, r in enumerate(R["rb"])]
    outline, ntop = _spine_outline(R["sp"], rt, rb)
    torso = lambda c: smooth_path(c, outline, closed=True)
    if M["shell"] > 0.01:
        # shadow shell: an inflated, wispy mass that contracts onto the true body
        shell = _displace(outline, M, t, 13, ntop)
        tends = _tendrils(R, M, t, shell, ntop)
        sedge = _a(SH_EDGE, min(1.0, M["shell"] * 3.0))
        for tp in tends:
            smooth_path(ctx, tp, closed=True)
            _s(ctx, sedge, 2 * lw)
        smooth_path(ctx, shell, closed=True)
        _s(ctx, sedge, 2 * lw)
        for tp in tends:
            smooth_path(ctx, tp, closed=True)
            _f(ctx, SHADOW)
        smooth_path(ctx, shell, closed=True)
        _f(ctx, SHADOW)
    _spec_glow_stroke(ctx, torso, M, 30.0)
    torso(ctx)
    _s(ctx, M["bedge"], 2 * lw)
    torso(ctx)
    ctx.set_source_rgba(*M["dk"])
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.translate(0, -24)
    torso(ctx)
    _f(ctx, M["body"])
    ctx.translate(0, 24)
    _spec_rim(ctx, torso, M, _perim(outline), 9.0, 5.0)
    ctx.restore()
    if M["mass"] > 0.05:
        # slow inner smoke curls
        cxm, cym = R["center"]
        for j in range(3):
            a0 = t * 0.6 + j * 2.1
            r = 24 + 10 * j
            ctx.arc(cxm + 30 * (j - 1), cym + 6, r, a0, a0 + 2.2)
            ctx.new_sub_path()
        _s(ctx, _a(SH_EDGE, 0.7 * M["mass"]), 3.0)
    # ------------------------------------------------------------------ near hind + haunch
    hx, hy, hrx, hry, hrot = R["haunch"]
    for kind, near, pts in legs:
        if near and kind == "hind":
            _spec_leg(ctx, pts, kind, M["body"], edge, lw, R["claws"])
    _shaded(ctx, lambda c: ellipse(c, hx, hy, hrx, hry, hrot), M["body"], M["dk"],
            off=(6.0, 12.0), lw=lw * 0.7, ink=M["bedge"])
    hp = R.get("hold") or {"front": (R["sp"][2][0], R["sp"][2][1] + R["rb"][2] + 6),
                            "back": (R["sp"][0][0] + 10, R["sp"][0][1] + R["rb"][0] + 6),
                            "chest": R["sp"][2], "rump": R["sp"][0],
                            "belly": (R["sp"][1][0], R["sp"][1][1] + R["rb"][1])}
    A.d["hold_points"] = {k_: A.pt(*v) for k_, v in hp.items()}
    A.put("center", *R["center"])
    if R["held"]:
        A.call(hold, hold_points=A.d["hold_points"])
        _setup(ctx)
    # ------------------------------------------------------------------ near front leg
    for kind, near, pts in legs:
        if near and kind == "front":
            pd = R.get("paw_dir") if R["point"] else None
            paw_pt = _spec_leg(ctx, pts, kind, M["body"], edge, lw, R["claws"], pd)
            if R["point"]:
                # one extended digit
                ax_, ay_ = pts[-1]
                a = R["paw_dir"]
                bx1, by1 = _rot(ax_ + 18, ay_ - 4, a, ax_, ay_)
                bx2, by2 = _rot(ax_ + 44, ay_ - 2, a, ax_, ay_)
                ctx.move_to(bx1, by1)
                ctx.line_to(bx2, by2)
                _s(ctx, edge, 11 + 2 * lw)
                ctx.move_to(bx1, by1)
                ctx.line_to(bx2, by2)
                _s(ctx, M["body"], 11)
                paw_pt = _rot(ax_ + 50, ay_ - 2, a, ax_, ay_)
    if paw_pt is not None:
        A.put("paw", *paw_pt)
    # ------------------------------------------------------------------ head
    hx, hy, hrot = R["head"]
    yaw = 0.45 * clamp(face, -1.0, 1.0)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(hrot + head_rot_extra)
    if R["head_scale"] != 1.0:
        ctx.scale(R["head_scale"], R["head_scale"])
    _spec_head(ctx, A, t, R, M, E, lk, bl, yaw, face < 0, lw, R.get("mouth_mode"), hold)
    ctx.restore()
    if R["tail_front"]:
        _spec_tail(ctx, A, R, M, t, lw)
    ctx.restore()
    _lr(A, "eA", "eB")
    return A.d


# --- pod sleeper -------------------------------------------------------------
def draw_specimen_pod_sleeper(ctx, x, y, s, t, seed=0, flip=None, glow=1.0):
    """Cheap curled-up sleeping specimen (~300 x 150 px at s=1). (x, y) = ground point.

    seed varies the breathing phase/rate, facing and the tail tip. Slow breath ~0.28 Hz.
    """
    if flip is None:
        flip = hash01(seed, 9) < 0.5
    A = _Anch(ctx, s, flip)
    lw = max(LW, 2.0 / max(s, 1e-3))
    br = _sin(t * TAU / (3.2 + 0.8 * hash01(seed, 2)) + hash01(seed, 1) * TAU)
    sy = 1.0 + 0.04 * br
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if flip else s, s)
    _setup(ctx)
    # body ball: shadow tone first, lit part inset up-left (no clip)
    cy = -64 * sy
    ellipse(ctx, -8, cy, 122, 64 * sy)
    ctx.set_source_rgba(*SP_DK)
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(lw)
    ctx.stroke()
    ellipse(ctx, -16, cy - 10, 108, 50 * sy)
    _f(ctx, SP)
    g = min(1.0, glow)
    if g > 0.01:
        ctx.save()
        ctx.translate(-10, cy + 6)
        ctx.scale(108, 58 * sy)
        ctx.arc(0, 0, 1, PI * 1.06, PI * 1.74)
        ctx.restore()
        _s(ctx, _a(GLOW, 0.95 * g), lw * 1.1)
    # ear fin folded back along the body (glowing leading edge)
    ctx.move_to(78, cy - 30)
    ctx.curve_to(40, cy - 78, -30, cy - 74, -92, cy - 60)
    ctx.curve_to(-64, cy - 50, -54, cy - 44, -36, cy - 46)
    ctx.curve_to(-20, cy - 36, 30, cy - 34, 78, cy - 30)
    _fs(ctx, SP, lw * 0.85)
    if g > 0.01:
        ctx.move_to(70, cy - 42)
        ctx.curve_to(36, cy - 72, -30, cy - 70, -84, cy - 60)
        _s(ctx, _a(GLOW, 0.8 * g), lw * 0.6)
    # head tucked at the front, resting on the tail
    ellipse(ctx, 96, -48 * sy, 56, 44 * sy)
    _fs(ctx, SP, lw)
    if g > 0.01:   # a faint teal glint leaks under the closed lid
        ctx.move_to(88, -48 * sy)
        ctx.curve_to(96, -40 * sy, 112, -40 * sy, 122, -48 * sy)
        _s(ctx, _a(GLOW, 0.85 * g), lw * 0.7)
    _happy_eye(ctx, 104, -54 * sy, 20, 16, lw * 0.95, INK, down=True)
    ellipse(ctx, 146, -38 * sy, 6.5, 5)
    _f(ctx, PUPIL)
    # tail wrapped around the front with its fin tip
    tw = 10 * hash01(seed, 5)
    ctx.move_to(-122, -44)
    ctx.curve_to(-136, -6, -40, -2, 40, -6)
    ctx.curve_to(80, -8, 110, -6 - tw, 150, -10 - tw)
    _s(ctx, INK, 20 + 2 * lw)
    ctx.move_to(-122, -44)
    ctx.curve_to(-136, -6, -40, -2, 40, -6)
    ctx.curve_to(80, -8, 110, -6 - tw, 150, -10 - tw)
    _s(ctx, SP, 20)
    ellipse(ctx, 164, -12 - tw, 18, 10, -0.1)
    _fs(ctx, SP, lw * 0.85)
    A.put("center", 0, -64)
    A.put("head", 96, -48)
    A.put("top", -10, -128)
    ctx.restore()
    return A.d
