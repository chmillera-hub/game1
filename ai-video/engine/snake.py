"""Hissy -- the villain's snake sidekick (the audience's side-eye).

    draw_snake_head(ctx, x, y, s, t, expr="idle", look=(0,0), mouth=0.0,
                    tongue=None, blink=None, tail_from=None, seed=5)

(x, y) = centre of the head (just below the eye line). At s=1 the head is
~180 px wide and ~140 px tall (top ~66 px above y, snout ~72 px below y);
eyes at (+-40, -18). With neck=True (default) a neck stub hangs ~230 px below.  Exprs: idle, smug, shocked, worried, side_eye, unimpressed, happy,
nod, facepalm  (name or (from, to, blend) tuple from core.state_at).

Body helpers used by the villain rig:
    coil_points(pts, n) / draw_tube(ctx, P, widths, i0, i1, ...)
"""
import math

from .core import (PAL, hexc, clamp, lerp, smoothstep, seg, noise1, hash01,
                   blink_amount, ellipse, circle, smooth_path, set_color)

INK = hexc("ink")
GREEN = hexc("snake")
GREEN_DK = hexc("snake_dk")
BELLY = hexc("snake_belly")
BELLY_DK = hexc("#b4d063")
WHITE = hexc("#ffffff")
PUPIL = hexc("#15101c")
MOUTH_IN = hexc("#5a1424")
TONGUE = hexc("#e8314f")
TONGUE_DK = hexc("#a81732")
BLUSH = hexc("#ff7aa0", 0.45)

OUT_W = 6.0      # outer ink line at s=1
IN_W = 3.5       # inner detail lines

# ---------------------------------------------------------------------------
# expressions
# ---------------------------------------------------------------------------
_BASE = dict(ul=0.22, ll=0.06, lt=0.0, ps=1.0, es=1.0, ex=0.0, ey=0.0,
             mc=0.3, mo=0.0, mw=1.0, msk=0.0, tilt=0.0, hy=0.0, sq=1.0,
             hap=0.0, blush=0.0, fp=0.0, nod=0.0, tng=1.0, wob=0.0, by=0.0)

SNAKE_EXPR = {
    "idle": {},
    "smug": dict(ul=0.5, ll=0.18, lt=0.22, mc=0.85, msk=0.55, mw=1.05,
                 tilt=-0.10, hy=-4, ps=0.9),
    "shocked": dict(by=10, ul=0.0, ll=0.0, es=1.18, ps=0.55, mc=-0.25, mo=0.85, mw=0.62,
                    hy=-14, sq=1.08, tng=0.0),
    "worried": dict(ul=0.12, ll=0.05, lt=-0.42, ps=0.78, mc=-0.55, mo=0.12, mw=0.8,
                    msk=0.25, wob=1.0, tilt=0.06, hy=4),
    "side_eye": dict(ul=0.44, ll=0.18, lt=0.08, ex=1.15, ey=0.1, ps=0.95,
                     mc=-0.15, msk=-0.5, mw=0.72, tilt=0.10, tng=0.0, by=-3),
    "unimpressed": dict(ul=0.5, ll=0.1, lt=-0.04, ey=0.25, ps=0.95, mc=-0.35, mw=0.62,
                        msk=0.18, tilt=-0.03, tng=0.0, by=-3),
    "happy": dict(hap=1.0, mc=1.0, mo=0.35, mw=1.1, blush=0.8, hy=-6, tilt=-0.05),
    "nod": dict(ul=0.42, ll=0.2, mc=0.75, mw=0.95, nod=1.0, blush=0.3, tng=0.0),
    "facepalm": dict(fp=1.0, mc=-0.45, mw=0.7, msk=0.3, tilt=0.12, hy=6, tng=0.0,
                     ul=0.7),
}
SNAKE_EXPRS = list(SNAKE_EXPR)


_warned = set()


def _params(name):
    if name not in SNAKE_EXPR and name not in _warned:
        _warned.add(name)
        import sys
        print(f"[snake] unknown expr '{name}', using idle", file=sys.stderr)
    d = dict(_BASE)
    d.update(SNAKE_EXPR.get(name, {}))
    return d


def resolve_expr(expr):
    """name | (from, to, blend) -> blended parameter dict."""
    if isinstance(expr, (tuple, list)):
        a, b, k = expr
        pa, pb = _params(a), _params(b)
        k = clamp(float(k))
        return {key: pa[key] + (pb[key] - pa[key]) * k for key in pa}
    return _params(expr)


# ---------------------------------------------------------------------------
# tube body helpers
# ---------------------------------------------------------------------------
def coil_points(pts, n_per=8, tension=0.5):
    """Sample a Catmull-Rom spline through pts -> list of (x, y)."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts)):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        for j in range(n_per):
            u = j / n_per
            v = 1 - u
            out.append((v * v * v * p1[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u * u * u * p2[0],
                        v * v * v * p1[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u * u * u * p2[1]))
    out.append(tuple(pts[-1]))
    return out


def _normals(P):
    n = len(P)
    N = []
    for i in range(n):
        a = P[max(0, i - 1)]
        b = P[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        N.append((-dy / L, dx / L))
    return N


def _poly_to(ctx, pts):
    for p in pts:
        ctx.line_to(p[0], p[1])


def draw_tube(ctx, P, widths, i0=0, i1=None, cap0=True, cap1=True, belly_side=1,
              belly=True, spots=True, spot_phase=0.0, line_w=OUT_W, N=None,
              belly_lines=True):
    """Draw snake body samples P[i0..i1] as an outlined tube.

    widths: per-sample widths. cap0/cap1: round (outlined) ends; a False cap
    is a flush cut WITHOUT an ink line so two parts can join seamlessly.
    """
    n = len(P)
    if i1 is None:
        i1 = n - 1
    if i1 - i0 < 1:
        return
    if N is None:
        N = _normals(P)
    idx = range(i0, i1 + 1)
    L = [(P[i][0] + N[i][0] * widths[i] / 2, P[i][1] + N[i][1] * widths[i] / 2) for i in idx]
    R = [(P[i][0] - N[i][0] * widths[i] / 2, P[i][1] - N[i][1] * widths[i] / 2) for i in idx]

    def outline_path():
        ctx.move_to(*L[0])
        _poly_to(ctx, L[1:])
        if cap1:
            nx, ny = N[i1]
            a0 = math.atan2(ny, nx)
            ctx.arc_negative(P[i1][0], P[i1][1], widths[i1] / 2, a0, a0 - math.pi)
        else:
            ctx.line_to(*R[-1])
        _poly_to(ctx, R[::-1][1:])
        if cap0:
            nx, ny = N[i0]
            a0 = math.atan2(-ny, -nx)
            ctx.arc_negative(P[i0][0], P[i0][1], widths[i0] / 2, a0, a0 - math.pi)
        ctx.close_path()

    outline_path()
    ctx.set_source_rgba(*GREEN)
    ctx.fill()

    # belly band on one side
    if belly:
        sd = belly_side
        A = [(P[i][0] + sd * N[i][0] * widths[i] * 0.06, P[i][1] + sd * N[i][1] * widths[i] * 0.06)
             for i in idx]
        B = [(P[i][0] + sd * N[i][0] * widths[i] * 0.47, P[i][1] + sd * N[i][1] * widths[i] * 0.47)
             for i in idx]
        ctx.move_to(*A[0])
        _poly_to(ctx, A[1:])
        _poly_to(ctx, B[::-1])
        ctx.close_path()
        ctx.set_source_rgba(*BELLY)
        ctx.fill()
        # belly segment lines
        if not belly_lines:
            A = A[:1]
        ctx.set_line_width(2.5)
        ctx.set_source_rgba(*BELLY_DK)
        acc = 0.0
        for k in range(1, len(A)):
            acc += math.hypot(A[k][0] - A[k - 1][0], A[k][1] - A[k - 1][1])
            if acc > 15 and widths[i0 + k] > 14:
                acc = 0.0
                ctx.move_to(*A[k])
                ctx.line_to(*B[k])
        ctx.stroke()

    # back spots
    if spots:
        ctx.set_source_rgba(*GREEN_DK)
        acc = spot_phase
        for k in range(1, len(L)):
            i = i0 + k
            acc += math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])
            if acc > 46 and widths[i] > 18:
                acc = 0.0
                nx, ny = N[i]
                w = widths[i]
                cx, cy = P[i][0] - belly_side * nx * w * 0.2, P[i][1] - belly_side * ny * w * 0.2
                ellipse(ctx, cx, cy, w * 0.16, w * 0.11, math.atan2(nx, -ny))
        ctx.fill()

    # outline: edges (+ caps)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(line_w)
    if cap0 and cap1:
        outline_path()
        ctx.stroke()
    else:
        ctx.move_to(*L[0])
        _poly_to(ctx, L[1:])
        if cap1:
            nx, ny = N[i1]
            a0 = math.atan2(ny, nx)
            ctx.arc_negative(P[i1][0], P[i1][1], widths[i1] / 2, a0, a0 - math.pi)
            _poly_to(ctx, R[::-1])
        ctx.stroke()
        if not cap1:
            ctx.move_to(*R[-1])
            _poly_to(ctx, R[::-1][1:])
            if cap0:
                nx, ny = N[i0]
                a0 = math.atan2(-ny, -nx)
                ctx.arc_negative(P[i0][0], P[i0][1], widths[i0] / 2, a0, a0 - math.pi)
                ctx.line_to(*L[0])
            ctx.stroke()


def tail_widths(n, w, taper_frac=0.3, tip=6.0, head_frac=0.0):
    """Width profile: constant w, tapering to `tip` over the last taper_frac."""
    out = []
    for i in range(n):
        u = i / max(1, n - 1)
        k = 1.0
        if u > 1 - taper_frac:
            q = (u - (1 - taper_frac)) / taper_frac
            k = lerp(1.0, tip / w, q ** 1.3)
        if head_frac and u < head_frac:
            k *= lerp(0.82, 1.0, u / head_frac)
        out.append(w * k)
    return out




# ---------------------------------------------------------------------------
# head
# ---------------------------------------------------------------------------
# spade-shaped head: wide brow with the eyes, tapering to a rounded snout
_HEAD = [(0, -66), (48, -62), (80, -38), (90, -6), (80, 26), (54, 52), (22, 68), (0, 71),
         (-22, 68), (-54, 52), (-80, 26), (-90, -6), (-80, -38), (-48, -62)]
EYE_X, EYE_Y, EYE_R = 40.0, -18.0, 26.0
IRIS = hexc("#e9d64a")


def _head_path(ctx, jaw):
    pts = [(x, y + (jaw * (y - 18) / 53 if y > 18 else 0)) for x, y in _HEAD]
    smooth_path(ctx, pts, closed=True)


def _tongue_amount(t, tongue, seed):
    """0..1 tongue extension; None = automatic periodic flicks."""
    if tongue is False:
        return 0.0
    if tongue is True:
        p = (t * 2.2) % 1.0
        return math.sin(p * math.pi) ** 0.7
    if isinstance(tongue, (int, float)):
        return clamp(float(tongue))
    period = 3.4
    k = math.floor(t / period)
    start = k * period + hash01(k, seed + 31) * period * 0.6
    p = (t - start) / 0.55
    if 0 <= p <= 1:
        return math.sin(p * math.pi) ** 0.6
    return 0.0


def _tail_over_eyes(ctx, fp, tail_from, t):
    """Tail tip slapped over the eyes (facepalm). fp 0..1 = progress."""
    fx, fy = tail_from if tail_from is not None else (-8.0, 200.0)
    sg = 1.0 if fx >= 0 else -1.0
    # rest pose (tail tip curled near tail_from) -> over-eyes pose
    rest = [(fx, fy), (fx - sg * 10, fy - 30), (fx - sg * 30, fy - 50), (fx - sg * 50, fy - 48),
            (fx - sg * 58, fy - 32)]
    over = [(fx, fy), (sg * 104, 50), (sg * 80, 0), (sg * 30, -24), (-sg * 30, -26),
            (-sg * 78, -14)]
    rest = rest + [(fx - sg * 50, fy - 18)]
    k = smoothstep(fp)
    wig = math.sin(t * 5.0) * 3 * k
    pts = [(lerp(a[0], b[0], k), lerp(a[1], b[1], k) + (wig if i > 1 else 0))
           for i, (a, b) in enumerate(zip(rest, over))]
    P = coil_points(pts, 6)
    n = len(P)
    W = []
    for i in range(n):
        u = i / (n - 1)
        w_rest = lerp(40, 10, u ** 1.5)
        w_over = 42 + 14 * math.sin(clamp((u - 0.35) / 0.6) * math.pi) - 26 * clamp((u - 0.9) / 0.1)
        W.append(lerp(w_rest, w_over, k))
    draw_tube(ctx, P, W, 0, n - 1, cap0=False, cap1=True, belly_side=-1, spots=True)


def draw_snake_head(ctx, x, y, s, t, expr="idle", look=(0, 0), mouth=0.0, tongue=None,
                    blink=None, tail_from=None, seed=5, flip=False, neck=True):
    """Draw Hissy's head centred at (x, y) with scale s.

    mouth: 0..1 (or (open, wide) tuple from lip-sync).  tongue: None=auto
    flicks, True=flicking now, False=never, float=fixed extension.
    tail_from: head-local point (unscaled) where the tail enters for the
    'facepalm' expression (the villain rig passes its coil end).
    flip: mirror horizontally (look is not mirrored).  neck: draw a short
    neck curving down out of frame below the head (standalone use).
    """
    p = resolve_expr(expr)
    if isinstance(mouth, (tuple, list)):
        mouth = mouth[0]
    lx, ly = look
    if flip:
        lx = -lx
    lx = clamp(lx + p["ex"], -1.2, 1.2)
    ly = clamp(ly + p["ey"], -1.2, 1.2)

    # nod animation: head dips + tilts rhythmically
    nod = p["nod"]
    nod_phase = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, nod_phase) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, nod_phase)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5  # idle sway
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if flip else s, s)
    ctx.set_tolerance(0.3)
    ctx.set_line_join(1)
    ctx.set_line_cap(1)
    if neck:
        P = coil_points([(4, 20), (16, 90), (6, 160), (-14, 230)], 5)
        draw_tube(ctx, P, [56] * len(P), 0, len(P) - 1, cap0=True, cap1=False,
                  belly_side=1, spot_phase=20)
    ctx.translate(0, p["hy"] + bob + nod_dy)
    ctx.rotate(p["tilt"] + sway + nod_rot + wob)
    sq = p["sq"]
    if sq != 1.0:
        ctx.scale(1 / math.sqrt(sq), sq)

    mo = clamp(p["mo"] + mouth * 0.9 * (1 - 0.5 * p["mo"]))
    jaw = mo * 22
    es = p["es"]

    # ---- head fill + one shadow tone -------------------------------------
    _head_path(ctx, jaw)
    ctx.set_source_rgba(*GREEN_DK)
    ctx.fill()
    ctx.save()
    ctx.translate(-50, -50)
    ctx.scale(0.9, 0.92)
    ctx.translate(50, 50)
    _head_path(ctx, jaw)
    ctx.restore()
    ctx.set_source_rgba(*GREEN)
    ctx.fill()
    # forehead chevron marking + cheek spots
    ctx.set_source_rgba(*GREEN_DK)
    ctx.move_to(0, -60)
    ctx.line_to(16, -44)
    ctx.line_to(0, -30)
    ctx.line_to(-16, -44)
    ctx.close_path()
    ctx.fill()
    for sx in (-1, 1):
        ellipse(ctx, sx * 22, -54, 6, 4, sx * 0.4)
        ctx.fill()
        ellipse(ctx, sx * 72, -30, 5, 4, sx * 0.9)
        ctx.fill()

    # ---- mouth / lower jaw ------------------------------------------------
    mc, mw, msk = p["mc"], p["mw"], p["msk"]
    hw = 60 * mw
    cy0 = 30.0
    yl = cy0 - mc * 14 + msk * 9
    yr = cy0 - mc * 14 - msk * 9
    ym = cy0 + mc * 12
    # pale under-jaw below the mouth line
    ctx.save()
    _head_path(ctx, jaw)
    ctx.clip()
    ctx.set_source_rgba(*BELLY)
    ctx.move_to(-100, yl + 3)
    ctx.line_to(-hw, yl + 3)
    ctx.curve_to(-hw * 0.4, ym + 5, hw * 0.4, ym + 5, hw, yr + 3)
    ctx.line_to(100, yr + 3)
    ctx.line_to(100, 140)
    ctx.line_to(-100, 140)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    # head outline
    _head_path(ctx, jaw)
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(OUT_W)
    ctx.stroke()

    open_h = mo * 34

    def mouth_path():
        ctx.move_to(-hw, yl)
        ctx.curve_to(-hw * 0.4, ym - open_h * 0.2, hw * 0.4, ym - open_h * 0.2, hw, yr)
        ctx.curve_to(hw * 0.5, ym + open_h * 1.15, -hw * 0.5, ym + open_h * 1.15, -hw, yl)
        ctx.close_path()

    if mo > 0.03:
        mouth_path()
        ctx.set_source_rgba(*MOUTH_IN)
        ctx.fill()
        ctx.save()
        mouth_path()
        ctx.clip()
        ctx.set_source_rgba(*TONGUE_DK)
        ellipse(ctx, 0, ym + open_h * 0.95, hw * 0.42, open_h * 0.45)
        ctx.fill()
        # two little fangs
        ctx.set_source_rgba(*WHITE)
        for fx in (-hw * 0.36, hw * 0.36):
            fy = ym - open_h * 0.2 - 4
            ctx.move_to(fx - 5.5, fy)
            ctx.line_to(fx + 5.5, fy)
            ctx.line_to(fx, fy + 13)
            ctx.close_path()
        ctx.fill()
        ctx.restore()
        mouth_path()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W + 1)
        ctx.stroke()
    else:
        ctx.move_to(-hw, yl)
        ctx.curve_to(-hw * 0.4, ym, hw * 0.4, ym, hw, yr)
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W + 1)
        ctx.stroke()
    # mouth corner ticks
    ctx.set_source_rgba(*INK)
    ctx.set_line_width(IN_W)
    for sx, yy in ((-1, yl), (1, yr)):
        ctx.move_to(sx * hw - sx * 2, yy - 7 - mc * 2)
        ctx.curve_to(sx * hw + sx * 6, yy - 3, sx * hw + sx * 6, yy + 2, sx * hw + sx * 1, yy + 6)
    ctx.stroke()

    # tongue
    ta = _tongue_amount(t, tongue, seed)
    if tongue is None:
        ta *= p["tng"]
    if ta > 0.02:
        L = 14 + 50 * ta
        ty0 = ym + (open_h * 0.7 if mo > 0.03 else 0)
        wig = math.sin(t * 38) * 7 * ta
        tip = (wig, ty0 + L)
        mid = (-wig * 0.4, ty0 + L * 0.55)
        ctx.move_to(0, ty0)
        ctx.curve_to(mid[0], mid[1], mid[0], mid[1], tip[0], tip[1])
        ctx.move_to(*tip)
        ctx.line_to(tip[0] - 9, tip[1] + 12)
        ctx.move_to(*tip)
        ctx.line_to(tip[0] + 9, tip[1] + 12)
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(12)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*TONGUE)
        ctx.set_line_width(6)
        ctx.stroke()

    # nostrils
    ctx.set_source_rgba(*INK)
    ellipse(ctx, -12, 14, 3.4, 4.6, 0.5)
    ctx.fill()
    ellipse(ctx, 12, 14, 3.4, 4.6, -0.5)
    ctx.fill()

    # blush
    if p["blush"] > 0.01:
        ctx.set_source_rgba(BLUSH[0], BLUSH[1], BLUSH[2], BLUSH[3] * p["blush"])
        ellipse(ctx, -62, 18, 15, 9)
        ctx.fill()
        ellipse(ctx, 62, 18, 15, 9)
        ctx.fill()

    # ---- eyes -------------------------------------------------------------
    b = blink_amount(t, seed, rate=0.22) if blink is None else blink
    hap = p["hap"]
    kk = math.floor(t * 1.1)
    sacc_x = noise1(kk * 3.7, seed + 11) * 0.12
    sacc_y = noise1(kk * 2.9, seed + 12) * 0.08
    for sx in (-1, 1):
        cx, cy = sx * EYE_X, EYE_Y
        r = EYE_R * es
        ul, ll, lt = p["ul"], p["ll"], p["lt"] * sx * -1  # inner side = toward centre
        bb = max(b, hap)
        if bb > 0.0:   # lids meet ~60% down the eye
            ll = lerp(ll, max(ll, 0.4), bb)
        ul_eff = lerp(ul, max(ul, 1.0 - ll), bb)
        top_y = cy - r + 2 * r * ul_eff
        bot_y = cy + r - 2 * r * ll
        dy = math.tan(lt) * r
        ctx.save()
        circle(ctx, cx, cy, r)
        ctx.clip()
        ctx.set_source_rgba(*WHITE)
        ctx.paint()
        # iris + slit pupil, kept inside the visible slit when squinting
        ps = p["ps"]
        ir = 14.5 * ps
        px = cx + (lx + sacc_x) * r * 0.44
        py = cy + (ly + sacc_y) * r * 0.36
        lo, hi = top_y + r * 0.12 + ir * 0.45, bot_y - ir * 0.25
        py = (lo + hi) / 2 if lo > hi else clamp(py, lo, hi)
        ctx.set_source_rgba(*IRIS)
        circle(ctx, px, py, ir)
        ctx.fill()
        ctx.set_source_rgba(*PUPIL)
        ellipse(ctx, px, py, 4.6 * ps + 1.5, ir * 0.92)
        ctx.fill()
        ctx.set_source_rgba(*WHITE)
        circle(ctx, px - ir * 0.42, py - ir * 0.45, 3.6 * ps + 1.0)
        ctx.fill()
        # lids (green)
        ctx.set_source_rgba(*GREEN)
        ctx.move_to(cx - r - 2, top_y - dy)
        ctx.curve_to(cx - r * 0.4, top_y - dy * 0.4 + r * 0.12, cx + r * 0.4,
                     top_y + dy * 0.4 + r * 0.12, cx + r + 2, top_y + dy)
        ctx.line_to(cx + r + 2, cy - r - 4)
        ctx.line_to(cx - r - 2, cy - r - 4)
        ctx.close_path()
        ctx.fill()
        if ll > 0.01:
            ctx.move_to(cx - r - 2, bot_y)
            ctx.curve_to(cx - r * 0.4, bot_y - r * 0.12, cx + r * 0.4, bot_y - r * 0.12,
                         cx + r + 2, bot_y)
            ctx.line_to(cx + r + 2, cy + r + 4)
            ctx.line_to(cx - r - 2, cy + r + 4)
            ctx.close_path()
            ctx.fill()
        ctx.set_source_rgba(*INK)
        if ul_eff >= 1.0 - ll - 0.01:
            ctx.set_line_width(IN_W + 2)
            ctx.move_to(cx - r - 2, bot_y + 1)
            ctx.curve_to(cx - r * 0.4, bot_y + r * 0.1, cx + r * 0.4, bot_y + r * 0.1,
                         cx + r + 2, bot_y + 1)
            ctx.stroke()
        elif ul_eff > 0.02:
            ctx.set_line_width(IN_W + 1.5)
            ctx.move_to(cx - r - 2, top_y - dy)
            ctx.curve_to(cx - r * 0.4, top_y - dy * 0.4 + r * 0.12, cx + r * 0.4,
                         top_y + dy * 0.4 + r * 0.12, cx + r + 2, top_y + dy)
            ctx.stroke()
        if ll > 0.05 and ul_eff < 1 - ll - 0.02:
            ctx.set_line_width(IN_W - 0.5)
            ctx.move_to(cx - r - 2, bot_y)
            ctx.curve_to(cx - r * 0.4, bot_y - r * 0.12, cx + r * 0.4, bot_y - r * 0.12,
                         cx + r + 2, bot_y)
            ctx.stroke()
        ctx.restore()
        # happy closed eyes: upward arcs over a green lid
        if hap > 0.5:
            ctx.set_source_rgba(*GREEN)
            circle(ctx, cx, cy, r + 1)
            ctx.fill()
            ctx.set_source_rgba(*INK)
            ctx.set_line_width(IN_W + 2)
            ctx.move_to(cx - r * 0.65, cy + r * 0.25)
            ctx.curve_to(cx - r * 0.3, cy - r * 0.45, cx + r * 0.3, cy - r * 0.45,
                         cx + r * 0.65, cy + r * 0.25)
            ctx.stroke()
        ctx.set_source_rgba(*INK)
        ctx.set_line_width(IN_W + 0.5)
        circle(ctx, cx, cy, r)
        ctx.stroke()

    # brow ridges: sell side-eye / unimpressed / worried
    ctx.set_source_rgba(*GREEN_DK)
    ctx.set_line_width(8)
    for sx in (-1, 1):
        cx = sx * EYE_X
        r = EYE_R * es
        ang = -p["lt"] * sx  # positive lt: inner end lower
        top = EYE_Y - r - 9 + p["ul"] * 6 - p["by"]
        x0, x1 = cx - r * 0.8, cx + r * 0.8
        ctx.move_to(x0, top - math.tan(ang) * r * 0.8)
        ctx.line_to(x1, top + math.tan(ang) * r * 0.8)
    ctx.stroke()

    # facepalm tail
    if p["fp"] > 0.02:
        _tail_over_eyes(ctx, p["fp"], tail_from, t)

    ctx.restore()
