"""THE FRIEND - the enormous, round, shaggy creature of ANGER (BIBLE.md section 2). Non-verbal.

Original design: a huge pear-shaped body of shaggy warm-brown fur (no face mask - the face is fur like the rest),
a cream belly patch, mossy clumps growing in the fur, two small curled horn nubs, tiny round ears, tiny beady
black eyes with a catch-light, a wide dumb grin with big flat teeth, a long pink tongue that hangs out and drips,
short stubby arms (they *can* cross over the belly - barely), stubby legs with big round feet.

Public API
    draw(canvas, pose, t)              the friend (canvas carries the camera; stage units)
    draw_tongue(canvas, pose, t)       the hanging tongue + drip alone (use with extra["tongue_layer"]="skip" when
                                       the tongue must go in front of something drawn after the body)
    head_center(pose, t=0.0)           stage point between the eyes
    hand_pos(pose, side, t=0.0)        stage point at the centre of the paw, side "l" (+x local) / "r"
    mouth_pos(pose, t=0.0)             stage point at the centre of the mouth
    tongue_tip(pose, t=0.0)            stage point of the tongue tip (None when the tongue is in)
    drip_pos(pose, t=0.0)              stage point of the saliva drop (forming at the tip, then falling) or None
    foot_pos(pose, side, t=0.0)        stage point under the centre of a foot (its sole)
    stomp_offset(pose)                 local x travel already applied by "stomp" (scaled, signed, stage units)
    stomp_hits(phase0, phase1)         phases in (phase0, phase1] where a stomp foot lands (sfx / camera shake)
    tap_hits(phase0, phase1)           same for foot_tap
    EXPR (presets), ARMS (preset names), HEIGHT (1600: floor -> horn tips), WIDTH (~1180)
    STOMP_HIT (0.55) / TAP_HIT (0.58): landing point inside one stomp / tap cycle; STOMP_STEP (60)

Pose fields used
    x, y (floor between the feet), scale, facing (+1 = turned toward screen-right; -1 = mirror image),
    turn (0 front .. 0.35 three-quarter toward facing), lean (deg, whole body sway, + toward facing),
    head_tilt (deg, + toward facing), head_turn (-0.3..0.3 extra face turn), head_nod (-1 chin down .. +1 up),
    lid_l / lid_r (None = expression level x automatic blink; a value overrides), look_x (+ = screen-right) /
    look_y, squint, brow_raise / brow_furrow / brow_worry, smile, smirk (+ raises the corner on the facing side),
    mouth_open, bounce (stage units, + = down; body only), breath (None = auto), shoulders_up,
    light / tint / tint_amt, rim / rim_color.
    The expression preset gives the base; the Pose face fields are ADDED on top (lids override).
pose.extra keys
    expr    "dumb_grin" | "side_eye" | "squint" | "huff" | "snort" | "giggle" | "smug" | "neutral"
            or a dict {name: weight} to blend presets; expr_amt 0..1 scales a single preset
    arms    "rest" | "cross" | "cover_mouth" | "wave" ("l" arm waves, "r" stays at rest) | "tap" (crossed, the
            top paw's middle finger tapping)
            or a dict {name: weight} to blend (e.g. {"rest": 0.4, "cross": 0.6} mid-move).
            Default: "cover_mouth" for giggle, else "rest".
    arm_l / arm_r   per-arm override of the preset name (side "l" = +x local)
    legs    "stand" | "stomp" (alias "stomp_back") | "foot_tap"
    phase   cycles for stomp / foot_tap (1 cycle = one stomp, alternating feet; one tap); also "wave" uses t
    stomp_step  local units of backward travel per stomp (default STOMP_STEP; 0 = in place). Backward = -x local
            (away from where it is facing). pose.x stays the START point; the rig moves the body itself.
    tongue  0..1 how far the tongue hangs out (0 = in); drip 0..1 saliva drop: 0..0.6 forming at the tip,
            0.6..1 falling drip_fall local units (default 520); drip_pos() reports it
    lean_down 0..1 looming toward the camera over someone lying below: the head comes ~330*scale down and grows
            x1.42, the face slides down the head and the eyes look down (look_y += 0.75*lean_down); the tongue
            hangs straight down (gravity). Combine with pose.lean to put the head over a target.
    puff    0..1 progress of one nostril puff (huff / snort); None = automatic cycle in those expressions
    giggle  0..1 strength of the giggle bounce (default 1 in "giggle")
    tongue_layer  "with_body" (default) | "skip"
    shadow  contact shadow alpha (default 0.32; 0 = none)
"""
from __future__ import annotations

import math

import skia

from anim.core import auto_blink, breathe, clamp, col, ease_in, ease_in_out, ease_out, hash01, lerp, light_filter
from anim.core import mix_col, smooth_path, smoothstep
from anim.core import paint as _core_paint
from anim.rig import Pose

D2R = math.pi / 180.0
HEIGHT = 1600.0
WIDTH = 1180.0
STOMP_HIT = 0.55
TAP_HIT = 0.58
STOMP_STEP = 60.0
DRIP_FALL = 520.0

# --------------------------------------------------------------------------- palette
C_FUR = col("b_fur")
C_FUR_SH = col("b_fur_shade")
C_FUR_HI = col("b_fur_hi")
C_FUR_DK = mix_col("b_fur_shade", "#1E140C", 0.45)
C_BELLY = col("b_belly")
C_BELLY_SH = mix_col("b_belly", "#8A6A4E", 0.45)
C_BELLY_HI = mix_col("b_belly", "#FFF4DA", 0.4)
C_LINE = col("#2A1A10")
C_EYE = col("b_eye")
C_TONGUE = col("b_tongue")
C_TONGUE_SH = mix_col("b_tongue", "#5A1626", 0.42)
C_TONGUE_HI = mix_col("b_tongue", "#FFE0E6", 0.55)
C_MOUTH = col("#3A1418")
C_TOOTH = col("#F4EEDC")
C_TOOTH_SH = col("#CFC2A0")
C_NOSE = col("#3A2620")
C_NOSE_HI = col("#8A6A58")
C_HORN = col("#D9CBA6")
C_HORN_SH = col("#A08C66")
C_HORN_LINE = col("#5A4A32")
C_EAR_IN = col("#9A6A55")
C_MOSS = col("#55703A")
C_MOSS_DK = col("moss")
C_MOSS_HI = col("vine_light")
C_PAD = col("#7A5644")
C_CLAW = col("#3A2A20")
C_SALIVA = col("#E6F2F4")
C_PUFF = col("#E9E4DA")
WHITE = col("#FFFFFF")

# --------------------------------------------------------------------------- lighting-aware paint
_CF = None
_CF_KEY = None
_PAINT_CACHE = {}


def paint(color, alpha=1.0, **kw):
    if kw.get("shader") is None and kw.get("blend") is None:
        key = (color, round(alpha, 3), kw.get("stroke", 0.0), kw.get("blur", 0.0), kw.get("cap", "round"), _CF_KEY)
        p = _PAINT_CACHE.get(key)
        if p is None:
            p = _core_paint(color, alpha, **kw)
            if _CF is not None:
                p.setColorFilter(_CF)
            if len(_PAINT_CACHE) > 4000:
                _PAINT_CACHE.clear()
            _PAINT_CACHE[key] = p
        return p
    p = _core_paint(color, alpha, **kw)
    if _CF is not None:
        p.setColorFilter(_CF)
    return p


def _set_light(pose):
    global _CF, _CF_KEY
    if pose.light != 1.0 or pose.tint_amt > 0:
        _CF = light_filter(max(0.0, pose.light) ** 0.65, pose.tint, pose.tint_amt)
        _CF_KEY = (round(pose.light, 3), tuple(pose.tint), round(pose.tint_amt, 3))
    else:
        _CF, _CF_KEY = None, None


def _clear_light():
    global _CF, _CF_KEY
    _CF, _CF_KEY = None, None


# --------------------------------------------------------------------------- small helpers
def _norm(x, y):
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def _rot(p, a_deg, o=(0.0, 0.0)):
    a = a_deg * D2R
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * ca - y * sa, o[1] + x * sa + y * ca)


def _cr(path, pts, move=True, tension=0.5):
    n = len(pts)
    if move:
        path.moveTo(pts[0][0], pts[0][1])
    else:
        path.lineTo(pts[0][0], pts[0][1])
    k = tension / 3.0
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[n - 1]
        path.cubicTo(p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
                     p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1])
    return path


def _curve(pts, tension=0.5):
    return _cr(skia.Path(), pts, True, tension)


def _fill(c, path, color, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, blur=blur))


def _stroke(c, path, color, width, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, stroke=width, blur=blur))


def _cel(c, path, base, shade, dx, dy, line=C_LINE, line_w=2.2, line_a=0.85):
    if line is not None:
        c.drawPath(path, paint(line, line_a, stroke=line_w * 2.0))
    _fill(c, path, shade)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.translate(dx, dy)
    _fill(c, path, base)
    c.restore()
    return path


def _oval2(c, rect, base, shade, dx, dy, line_w=1.8, line_a=0.85):
    """Clip-free two-tone oval (contour, shade, lit oval shrunk toward the light) for small convex parts."""
    c.drawOval(rect, paint(C_LINE, line_a, stroke=line_w * 2.0))
    c.drawOval(rect, paint(shade))
    ax, ay = abs(dx), abs(dy)
    lit = skia.Rect(rect.left() + (0.0 if dx < 0 else ax), rect.top() + (0.0 if dy < 0 else ay),
                    rect.right() - (ax if dx < 0 else 0.0), rect.bottom() - (ay if dy < 0 else 0.0))
    if lit.width() > 1 and lit.height() > 1:
        c.drawOval(lit, paint(base))


def _ribbon(center, widths, tension=0.5, cap=1.0):
    n = len(center)
    L, R = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        w = widths[i] * 0.5
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    p = skia.Path()
    _cr(p, L, tension=tension)
    tx, ty = _norm(center[-1][0] - center[-2][0], center[-1][1] - center[-2][1])
    w = widths[-1] * 0.5
    p.cubicTo(L[-1][0] + tx * w * 1.3 * cap, L[-1][1] + ty * w * 1.3 * cap,
              R[-1][0] + tx * w * 1.3 * cap, R[-1][1] + ty * w * 1.3 * cap, R[-1][0], R[-1][1])
    _cr(p, R[::-1], move=False, tension=tension)
    p.close()
    return p


def _map(m, p):
    q = m.mapXY(p[0], p[1])
    return (q.fX, q.fY)


# --------------------------------------------------------------------------- base design (facing +1, y up = -)
OUT_R = [(0.0, -1556.0), (118.0, -1546.0), (222.0, -1512.0), (298.0, -1452.0), (344.0, -1376.0), (370.0, -1296.0),
         (390.0, -1224.0), (408.0, -1166.0), (420.0, -1106.0), (442.0, -1040.0), (478.0, -968.0), (522.0, -880.0),
         (560.0, -770.0), (583.0, -640.0), (588.0, -510.0), (573.0, -385.0), (530.0, -282.0), (455.0, -212.0),
         (345.0, -178.0), (215.0, -176.0), (100.0, -186.0), (0.0, -190.0)]
BELLY_R = [(0.0, -1050.0), (190.0, -1006.0), (330.0, -890.0), (412.0, -720.0), (430.0, -520.0), (392.0, -340.0),
           (290.0, -214.0), (140.0, -176.0), (0.0, -172.0)]
EYE_X, EYE_Y = 112.0, -1335.0
FACE_C = (0.0, -1290.0)
MOUTH_Y = -1212.0
HIP_X, HIP_Y = 255.0, -250.0
FOOT_X = 262.0
N_OUT = 116

_BASE = {}


def _loop(right):
    return right + [(-x, y) for (x, y) in reversed(right[1:-1])]


def _sample(path, n):
    meas = skia.PathMeasure(path, True)
    L = meas.getLength()
    pts, tans = [], []
    for i in range(n):
        pos, tan = meas.getPosTan(L * i / n)
        pts.append((pos.fX, pos.fY))
        tans.append((tan.fX, tan.fY))
    return pts, tans


def _base():
    """Static base geometry (cached): smooth silhouette, hanging fur locks, belly, fur marks, moss."""
    if _BASE:
        return _BASE
    out_path = smooth_path(_loop(OUT_R), closed=True, tension=0.5)
    pts, tans = _sample(out_path, N_OUT)
    sil = []
    for i, (p, tg) in enumerate(zip(pts, tans)):
        nx, ny = tg[1], -tg[0]
        if p[0] * nx + (p[1] + 760.0) * ny < 0:
            nx, ny = -nx, -ny
        w = 4.0 * math.sin(i * 1.7) + 3.0 * (hash01(i, 9) - 0.5)
        sil.append((p[0] + nx * w, p[1] + ny * w))
    _BASE["out"] = sil
    _BASE["out_path"] = out_path
    # hanging locks along the silhouette: (base_l, ctrl_l, tip, ctrl_r, base_r) in base coords
    locks = []
    meas = skia.PathMeasure(out_path, True)
    Ltot = meas.getLength()
    u = 0.0
    k = 0
    while u < Ltot:
        k += 1
        w = 60.0 + 36.0 * hash01(k, 21)
        pos, tan = meas.getPosTan(u + w * 0.5)
        p = (pos.fX, pos.fY)
        tx, ty = tan.fX, tan.fY
        nx, ny = ty, -tx
        if p[0] * nx + (p[1] + 760.0) * ny < 0:
            nx, ny = -nx, -ny
        u += w * 0.68
        y = p[1]
        if y > -205.0 and abs(p[0]) < 470:
            continue            # between / above the legs: handled by the bottom fringe below
        L = 32.0 + 34.0 * hash01(k, 23)
        if -1270 < y < -1080:
            L += 16.0           # cheek fluff
        if y < -1480:
            L *= 0.8
        # direction: outward, hanging down on the sides, tousled on top
        if ny < -0.6:
            dx, dy = _norm(nx + 0.5 * (hash01(k, 25) - 0.5), ny)
        else:
            dx, dy = _norm(nx * 0.55, ny * 0.55 + 0.85)
        curl = (hash01(k, 27) - 0.5) * 0.6
        bl = (p[0] - tx * w * 0.5 - nx * 14.0, p[1] - ty * w * 0.5 - ny * 14.0)
        br = (p[0] + tx * w * 0.5 - nx * 14.0, p[1] + ty * w * 0.5 - ny * 14.0)
        tip = (p[0] + dx * L - dy * L * curl, p[1] + dy * L + dx * L * curl)
        cl = (bl[0] + dx * L * 0.85 - tx * w * 0.02, bl[1] + dy * L * 0.85 - ty * w * 0.02)
        cr = (br[0] + dx * L * 0.7 - tx * w * 0.3, br[1] + dy * L * 0.7 - ty * w * 0.3)
        locks.append((bl, cl, tip, cr, br, y))
    # bottom fringe (hangs over the tops of the legs)
    for j in range(13):
        x = -470.0 + j * (940.0 / 12.0) + 10.0 * (hash01(j, 31) - 0.5)
        yb = -192.0 + 14.0 * (abs(x) / 470.0) ** 2
        w = 70.0 + 20.0 * hash01(j, 33)
        L = 40.0 + 26.0 * hash01(j, 35)
        bl, br = (x - w * 0.5, yb - 26.0), (x + w * 0.5, yb - 26.0)
        tip = (x + (hash01(j, 37) - 0.5) * 20.0, yb + L)
        locks.append((bl, (bl[0] + 6.0, yb + L * 0.6), tip, (br[0] - 10.0, yb + L * 0.5), br, yb))
    locks.sort(key=lambda q: q[5], reverse=True)     # draw low locks first: upper hair falls over them
    _BASE["locks"] = locks
    # belly patch outline (tufted on the upper rim)
    bpath = smooth_path(_loop(BELLY_R), closed=True, tension=0.5)
    bp, bt = _sample(bpath, 60)
    bel = []
    for i, (p, tg) in enumerate(zip(bp, bt)):
        nx, ny = tg[1], -tg[0]
        if (p[0]) * nx + (p[1] + 620.0) * ny < 0:
            nx, ny = -nx, -ny
        if i % 2 and p[1] < -420:
            L = 9.0 + 12.0 * hash01(i, 5)
            bel.append((p[0] + nx * L, p[1] + ny * L + L * 0.6))
        else:
            bel.append((p[0] - nx * 2.0, p[1] - ny * 2.0))
    _BASE["belly"] = bel
    # fur marks: little hanging locks inside the fur, avoiding belly and face
    marks = []
    k = 0
    while len(marks) < 46 and k < 3000:
        k += 1
        x = (hash01(k, 11) - 0.5) * 1150.0
        y = -220.0 - hash01(k, 13) * 1320.0
        if not out_path.contains(x, y):
            continue
        if not out_path.contains(x * 1.08, y + 40.0) or not out_path.contains(x * 1.08, y - 40.0):
            continue
        if bpath.contains(x * 0.93, y) and y > -1070:
            continue
        if abs(x) < 300 and -1440 < y < -1130:
            continue
        sz = 11.0 + 9.0 * hash01(k, 17)
        sw = (hash01(k, 19) - 0.5) * 8.0
        hook = 1.0 if x > 0 else -1.0
        marks.append(((x - sz * 0.3, y - sz), (x + sw, y + sz * 0.1), (x + sw + hook * sz * 0.55, y + sz * 0.6), y, x))
    _BASE["marks"] = marks
    # moss clumps: (centre, radius, seed)
    _BASE["moss"] = [((-268.0, -1405.0), 62.0, 1), ((440.0, -1030.0), 60.0, 2), ((-505.0, -585.0), 78.0, 3),
                     ((350.0, -315.0), 52.0, 4), ((40.0, -1545.0), 30.0, 5)]
    return _BASE


# --------------------------------------------------------------------------- expressions / arms
_NEUTRAL = dict(lid=1.0, lid_asym=0.0, squint=0.0, look_x=0.0, look_y=0.0, brow_raise=0.0, brow_furrow=0.0,
                brow_worry=0.0, brow_asym=0.0, smile=0.25, smirk=0.0, mouth_open=0.0, mouth_w=150.0,
                cheek_puff=0.0, wrinkle=0.0, flare=0.0, head_tilt=0.0, head_turn=0.0, head_nod=0.0, happy=0.0,
                shoulders=0.0, giggle=0.0)
EXPR = {
    "neutral": {},
    "dumb_grin": dict(brow_raise=0.45, smile=1.0, mouth_open=0.36, mouth_w=205.0, head_tilt=4.0, squint=0.06,
                      look_y=0.1),
    "side_eye": dict(lid=0.46, squint=0.2, look_x=1.0, look_y=-0.05, brow_asym=0.6, brow_raise=0.05,
                     brow_furrow=0.25, smile=-0.05, smirk=0.3, mouth_w=118.0, head_turn=-0.16, head_tilt=-5.0,
                     head_nod=0.12),
    "squint": dict(lid=0.36, squint=0.6, brow_furrow=0.85, brow_raise=-0.35, smile=-0.2, mouth_w=108.0,
                   head_nod=-0.1, look_x=0.3),
    "huff": dict(lid=0.6, squint=0.2, brow_furrow=0.6, brow_raise=-0.2, smile=-0.35, mouth_w=92.0, cheek_puff=1.0,
                 flare=1.0, head_nod=0.2, head_turn=-0.1, shoulders=0.4),
    "snort": dict(lid=0.1, squint=0.85, happy=0.6, brow_raise=0.3, brow_worry=0.3, smile=0.7, mouth_w=118.0,
                  wrinkle=1.0, flare=1.0, cheek_puff=0.45, head_nod=0.1, shoulders=0.6),
    "giggle": dict(lid=0.0, squint=1.0, happy=1.0, brow_raise=0.45, brow_worry=0.45, smile=1.0, mouth_open=0.35,
                   mouth_w=190.0, giggle=1.0, head_tilt=6.0, shoulders=0.6),
    "smug": dict(lid=0.55, squint=0.28, look_x=0.45, brow_raise=0.2, brow_asym=0.35, smile=0.6, smirk=0.45,
                 mouth_w=150.0, head_nod=0.22, head_tilt=6.0, head_turn=-0.06),
}

# arm presets for the +x ("l") arm, base coords: shoulder, elbow, paw, paw angle (deg), palm (0 back .. 1 palm),
# follow_face (paw follows the face deformation), layer (0 under, 1 over when both arms overlap)
ARMS = {
    "rest": dict(S=(340.0, -965.0), E=(446.0, -850.0), P=(448.0, -738.0), ang=95.0, palm=0.0, face=0.0),
    "cross": dict(S=(338.0, -968.0), E=(400.0, -810.0), P=(-30.0, -850.0), ang=186.0, palm=0.0, face=0.0),
    "cover_mouth": dict(S=(340.0, -975.0), E=(436.0, -1092.0), P=(62.0, -1206.0), ang=200.0, palm=1.0, face=1.0),
    "wave": dict(S=(350.0, -985.0), E=(536.0, -1062.0), P=(566.0, -1262.0), ang=-80.0, palm=1.0, face=0.0),
    "tap": dict(S=(338.0, -968.0), E=(400.0, -810.0), P=(-30.0, -850.0), ang=186.0, palm=0.0, face=0.0),
}
# the "r" arm mirrors the preset; in "cross"/"tap" it sits a little lower and goes underneath
_R_CROSS = dict(S=(338.0, -960.0), E=(410.0, -770.0), P=(-10.0, -770.0), ang=180.0)


def _expr_values(pose, ex):
    e = ex.get("expr", "neutral")
    if isinstance(e, str):
        ws = {e: clamp(ex.get("expr_amt", 1.0))}
    elif isinstance(e, dict):
        ws = e
    else:
        ws = dict(e)
    v = dict(_NEUTRAL)
    for name, w in ws.items():
        pre = EXPR.get(name, {})
        for k, val in pre.items():
            v[k] += (val - _NEUTRAL[k]) * w
    return v, ws


# --------------------------------------------------------------------------- solve
class _R:
    pass


def _legs_state(R, ex, t):
    """Foot offsets (local), lift, squash, sway, travel for stomp / foot_tap."""
    legs = ex.get("legs", "stand")
    if legs == "stomp_back":
        legs = "stomp"
    ph = ex.get("phase", 0.0) or 0.0
    R.legs = legs
    R.foot = {"l": [FOOT_X, 0.0, 0.0], "r": [-FOOT_X, 0.0, 0.0]}   # x, lift, toe tilt
    R.sq = 0.0
    R.jig = 0.0
    R.sway = 0.0
    R.travel = 0.0
    R.hip_shift = 0.0
    R.bob = 0.0
    if legs == "stomp":
        step = ex.get("stomp_step", STOMP_STEP)
        n = math.floor(ph)
        f = ph - n
        side = "l" if n % 2 == 0 else "r"
        other = "r" if side == "l" else "l"
        e = ease_in_out(clamp(f / STOMP_HIT))
        R.travel = -step * (n + e)
        # feet in world (relative to pose.x, local units)
        def world_after(sd, j):     # foot position after its stomp j (or home if none)
            home = FOOT_X if sd == "l" else -FOOT_X
            return home - step * (j + 1) if j >= 0 else home
        last_other = n - 1 if n >= 1 else -1
        wo = world_after(other, last_other)
        prev = n - 2 if n >= 2 else -1
        ws_old = world_after(side, prev)
        ws_new = world_after(side, n)
        ws = lerp(ws_old, ws_new, e)
        lift_t = clamp(f / 0.42)
        if f < 0.42:
            lift = 190.0 * math.sin(lift_t * math.pi / 2) ** 0.8
        elif f < STOMP_HIT:
            lift = 190.0 * (1.0 - ease_in((f - 0.42) / (STOMP_HIT - 0.42)))
        else:
            lift = 0.0
        R.foot[side] = [ws - R.travel, lift, 0.0]
        R.foot[other] = [wo - R.travel, 0.0, 0.0]
        # body: tilt away from the lifted leg (sass), drop at the slam, squash + jiggle after
        sgn = 1.0 if side == "l" else -1.0
        up = math.sin(math.pi * clamp(f / STOMP_HIT))
        R.sway = -sgn * 3.4 * up
        R.hip_shift = -sgn * 26.0 * up
        R.bob = -26.0 * up
        if f >= STOMP_HIT:
            d = f - STOMP_HIT
            R.sq = 0.045 * math.exp(-d * 8.0) * math.cos(d * 21.0)
            R.jig = math.exp(-d * 6.0) * math.sin(d * 30.0)
        R.stomp_side = side
    elif legs == "foot_tap":
        f = ph - math.floor(ph)
        if f < 0.45:
            lift = 34.0 * ease_out(f / 0.45)
        elif f < TAP_HIT:
            lift = 34.0 * (1.0 - ease_in((f - 0.45) / (TAP_HIT - 0.45)))
        else:
            lift = 0.0
        R.foot["l"] = [FOOT_X, lift * 0.9, lift / 34.0]
        if f >= TAP_HIT:
            d = f - TAP_HIT
            R.jig = 0.35 * math.exp(-d * 9.0) * math.sin(d * 34.0)
            R.bob = 6.0 * math.exp(-d * 10.0)
    return R


def _solve(pose: Pose, t: float):
    ex = pose.extra or {}
    R = _R()
    R.ex = ex
    v, ws = _expr_values(pose, ex)
    fac = 1.0 if pose.facing >= 0 else -1.0
    R.fac = fac
    R.t = t
    # combine with pose fields (additive)
    R.look_x = clamp(v["look_x"] + pose.look_x * fac, -1.2, 1.2)
    R.look_y = clamp(v["look_y"] + pose.look_y + 0.75 * clamp(ex.get("lean_down", 0.0) or 0.0), -1.0, 1.0)
    R.squint = clamp(v["squint"] + pose.squint)
    R.brow_raise = v["brow_raise"] + pose.brow_raise
    R.brow_furrow = clamp(v["brow_furrow"] + pose.brow_furrow)
    R.brow_worry = clamp(v["brow_worry"] + pose.brow_worry)
    R.brow_asym = v["brow_asym"]
    R.smile = clamp(v["smile"] + pose.smile, -1.0, 1.2)
    R.smirk = clamp(v["smirk"] + pose.smirk, -1.0, 1.0)
    R.tongue = clamp(ex.get("tongue", 0.0) or 0.0)
    R.mouth_open = clamp(v["mouth_open"] + pose.mouth_open)
    if R.tongue > 0.02:
        R.mouth_open = max(R.mouth_open, 0.22 + 0.12 * min(1.0, R.tongue * 3.0))
    R.mouth_w = v["mouth_w"]
    R.cheek_puff = clamp(v["cheek_puff"])
    R.wrinkle = clamp(v["wrinkle"])
    R.flare = clamp(v["flare"])
    R.happy = clamp(v["happy"])
    R.giggle = clamp(ex.get("giggle", v["giggle"]))
    # lids
    blink = auto_blink(t, seed=21, rate=4.6)
    lid = v["lid"]
    lid_l = lid * (blink if lid > 0.15 else 1.0) if pose.lid_l is None else pose.lid_l
    lid_r = lid * (blink if lid > 0.15 else 1.0) if pose.lid_r is None else pose.lid_r
    R.lid = {"l": clamp(lid_l), "r": clamp(lid_r)}
    # puff (huff / snort)
    puff = ex.get("puff")
    R.puff = None
    w_huff = ws.get("huff", 0.0) if isinstance(ws, dict) else 0.0
    w_snort = ws.get("snort", 0.0) if isinstance(ws, dict) else 0.0
    if puff is not None:
        R.puff = clamp(puff)
    elif w_huff > 0.3:
        R.puff = (t / 2.2) % 1.0
    elif w_snort > 0.3:
        R.puff = (t / 1.3) % 1.0
    jerk = 0.0
    if R.puff is not None and w_snort > 0.3:
        jerk = math.exp(-R.puff * 10.0) * (1.0 if R.puff < 0.6 else 0.0)
    # head / body motion
    R.tilt = v["head_tilt"] + pose.head_tilt
    R.turn = clamp(pose.turn, -0.5, 0.5)
    R.head_turn = clamp(v["head_turn"] + pose.head_turn, -0.5, 0.5)
    R.nod = clamp(v["head_nod"] + pose.head_nod + 0.25 * jerk, -1.0, 1.0)
    br = breathe(t, rate=0.18, seed=4) if pose.breath is None else pose.breath
    R.breath = br
    _legs_state(R, ex, t)
    gig = R.giggle
    hop = abs(math.sin(2 * math.pi * 3.1 * t)) if gig > 0 else 0.0
    R.upper_bounce = -(18.0 * hop * gig) - 26.0 * clamp(v["shoulders"] + pose.shoulders_up) * 0.4 - 10.0 * jerk
    R.tilt += 3.0 * gig * math.sin(2 * math.pi * 1.55 * t)
    R.jig += 0.25 * gig * math.sin(2 * math.pi * 6.2 * t)
    R.body_bounce = pose.bounce + R.bob
    R.lean = pose.lean + R.sway
    R.ld = clamp(ex.get("lean_down", 0.0) or 0.0)
    # face matrix (affine approximation of the deformation around the face)
    R.face = _face_matrix(R)
    # arms
    arms = ex.get("arms")
    if arms is None:
        arms = "cover_mouth" if ws.get("giggle", 0.0) >= 0.5 else "rest"
    R.arms = {}
    for sd in ("l", "r"):
        name = ex.get("arm_" + sd, arms)
        R.arms[sd] = _arm_solve(R, sd, name, t)
    return R


# --------------------------------------------------------------------------- deformation
def _deform(R, x, y):
    """Base (design) coords -> local drawing coords (facing +1 frame)."""
    # belly jiggle (after stomps / taps / giggles)
    if R.jig:
        wb = math.exp(-((y + 600.0) / 330.0) ** 2)
        x += R.jig * 0.045 * x * wb
        y += R.jig * 16.0 * wb
    # breathing + squash about the floor
    sq = R.sq
    k_b = 1.0 + 0.006 * R.breath
    x *= (1.0 + sq * 0.6) * (1.0 + 0.004 * R.breath)
    y *= (1.0 - sq) * k_b
    # upper-body bounce / shoulders
    if R.upper_bounce:
        wu = smoothstep((-y - 600.0) / 520.0)
        y += R.upper_bounce * wu
    # head tilt (rotation of the upper part)
    if R.tilt:
        wt = smoothstep((-y - 940.0) / 260.0)
        if wt > 0:
            x, y = _rot((x, y), R.tilt * wt, (0.0, -1120.0))
    # loom toward the camera
    if R.ld > 0:
        x, y = _loom(R, x, y)
    # whole-body sway / lean about the hips + hip shift + vertical bob
    yb = y
    if R.lean:
        x, y = _rot((x, y), R.lean, (0.0, -230.0))
    w_body = smoothstep((-yb - 120.0) / 160.0)
    x += R.hip_shift * w_body
    y += R.body_bounce * w_body
    return x, y


def _loom(R, x, y):
    ld = R.ld
    y_b, y_h = -620.0, -1050.0
    drop = 330.0 * ld
    k_h = 1.0 + 0.42 * ld
    y_h2 = y_h + drop
    if y >= y_b:
        return x, y
    if y > y_h:
        u = (y - y_b) / (y_h - y_b)
        uu = smoothstep(u)
        ny = lerp(y_b, y_h2, u)
        kx = lerp(1.0, k_h, uu)
        return x * kx, ny
    return x * k_h, y_h2 + (y - y_h) * k_h


def _face_pre(R, x, y):
    """Turn the face decal round the head sphere + nod (+ the look-down slide when looming)."""
    th = (R.turn + R.head_turn) * 0.85
    fc = FACE_C
    xx = x * math.cos(th) + 420.0 * math.sin(th)
    yy = y - R.nod * 34.0 - (y - fc[1]) * 0.08 * abs(R.nod)
    if R.ld > 0:
        yy += 56.0 * R.ld
        yy = fc[1] + (yy - fc[1]) * (1.0 - 0.1 * R.ld)
    return xx, yy


def _face_matrix(R):
    """Affine fit of (deform o face_pre) around the face centre: base face coords -> local coords."""
    fc = FACE_C
    d = 60.0
    p0 = _deform(R, *_face_pre(R, *fc))
    px = _deform(R, *_face_pre(R, fc[0] + d, fc[1]))
    py = _deform(R, *_face_pre(R, fc[0], fc[1] + d))
    a, c_ = (px[0] - p0[0]) / d, (px[1] - p0[1]) / d
    b, dd = (py[0] - p0[0]) / d, (py[1] - p0[1]) / d
    m = skia.Matrix()
    m.setAll(a, b, p0[0] - a * fc[0] - b * fc[1], c_, dd, p0[1] - c_ * fc[0] - dd * fc[1], 0.0, 0.0, 1.0)
    return m


def _mscale(m):
    return math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY())) or 1.0


def _local_scale(R, p):
    a = _deform(R, p[0] - 20.0, p[1])
    b = _deform(R, p[0] + 20.0, p[1])
    return math.hypot(b[0] - a[0], b[1] - a[1]) / 40.0


# --------------------------------------------------------------------------- arms
def _turn_x(R, x, rad=640.0):
    th = R.turn * 0.85
    s = clamp(x / rad, -1.0, 1.0)
    return rad * math.sin(math.asin(s) + th)


def _arm_preset(sd, name):
    pre = ARMS.get(name, ARMS["rest"])
    S, E, P, ang = pre["S"], pre["E"], pre["P"], pre["ang"]
    if sd == "r":
        if name in ("cross", "tap"):
            S, E, P, ang = _R_CROSS["S"], _R_CROSS["E"], _R_CROSS["P"], _R_CROSS["ang"]
        S = (-S[0], S[1])
        E = (-E[0], E[1])
        P = (-P[0], P[1])
        ang = 180.0 - ang
        if name == "wave":
            # the other arm stays at rest while one waves
            r = ARMS["rest"]
            S, E, P, ang = (-r["S"][0], r["S"][1]), (-r["E"][0], r["E"][1]), (-r["P"][0], r["P"][1]), 180.0 - r["ang"]
            return S, E, P, ang, 0.0, 0.0, "rest"
    return S, E, P, ang, pre["palm"], pre["face"], name


def _arm_solve(R, sd, name, t):
    if isinstance(name, dict):
        acc = None
        tot = sum(name.values()) or 1.0
        for nm, w in name.items():
            a = _arm_solve(R, sd, nm, t)
            if acc is None:
                acc = {k: v for k, v in a.items()}
                for k in ("S", "E", "P"):
                    acc[k] = (a[k][0] * w / tot, a[k][1] * w / tot)
                acc["ang"] = a["ang"] * w / tot
                acc["palm"] = a["palm"] * w / tot
                acc["wmax"] = w
            else:
                for k in ("S", "E", "P"):
                    acc[k] = (acc[k][0] + a[k][0] * w / tot, acc[k][1] + a[k][1] * w / tot)
                acc["ang"] += a["ang"] * w / tot
                acc["palm"] += a["palm"] * w / tot
                if w > acc["wmax"]:
                    acc["wmax"] = w
                    acc["name"] = a["name"]
        return acc
    S, E, P, ang, palm, face, nm = _arm_preset(sd, name)
    # body turn moves the shoulders round the body
    sx = _turn_x(R, S[0])
    dsx = sx - S[0]
    S2 = _deform(R, sx, S[1])
    k = _local_scale(R, S)
    E_rel = ((E[0] - S[0]) * k, (E[1] - S[1]) * k)
    P_rel = ((P[0] - E[0]) * k, (P[1] - E[1]) * k)
    E2 = (S2[0] + E_rel[0], S2[1] + E_rel[1])
    P2 = (E2[0] + P_rel[0], E2[1] + P_rel[1])
    if face > 0:
        P_face = _map(R.face, (P[0], P[1]))
        E_face = _deform(R, E[0] + dsx * 0.5, E[1])
        P2 = (lerp(P2[0], P_face[0], face), lerp(P2[1], P_face[1], face))
        E2 = (lerp(E2[0], E_face[0], face * 0.6), lerp(E2[1], E_face[1], face * 0.6))
    wav = 0.0
    if nm == "wave":
        wav = 18.0 * math.sin(2 * math.pi * 1.6 * t)
        P2 = _rot(P2, wav * 0.5, E2)
    tap = 0.0
    if nm == "tap":
        tap = max(0.0, math.sin(2 * math.pi * 2.4 * t)) ** 2
    return {"S": S2, "E": E2, "P": P2, "ang": ang + wav, "palm": palm, "name": nm, "k": k, "tap": tap}


# --------------------------------------------------------------------------- drawing: pieces
def _body_path(R):
    B = _base()
    pts = [_deform(R, x, y) for (x, y) in B["out"]]
    return smooth_path(pts, closed=True, tension=0.5)


def _locks_path(R):
    B = _base()
    path = skia.Path()
    path.setFillType(skia.PathFillType.kWinding)
    strands = skia.Path()
    for (bl, cl, tip, cr, br, _) in B["locks"]:
        a, b, t_, d, e = (_deform(R, *q) for q in (bl, cl, tip, cr, br))
        path.moveTo(*a)
        path.quadTo(b[0], b[1], t_[0], t_[1])
        path.quadTo(d[0], d[1], e[0], e[1])
        path.close()
        m = ((a[0] + e[0]) * 0.5, (a[1] + e[1]) * 0.5)
        strands.moveTo(m[0] * 0.7 + t_[0] * 0.3, m[1] * 0.7 + t_[1] * 0.3)
        strands.quadTo((m[0] + t_[0]) * 0.5 + (d[0] - b[0]) * 0.08, (m[1] + t_[1]) * 0.5 + (d[1] - b[1]) * 0.08,
                       t_[0] * 0.85 + m[0] * 0.15, t_[1] * 0.85 + m[1] * 0.15)
    return path, strands


def _draw_shadow(c, R, alpha):
    if alpha <= 0:
        return
    xl = R.foot["l"][0] + R.hip_shift * 0.3
    xr = R.foot["r"][0] + R.hip_shift * 0.3
    cx = (xl + xr) * 0.5
    w = (xl - xr) * 0.5 + 300.0
    for k_, a_ in ((1.0, 0.35), (0.82, 0.35), (0.62, 0.4)):
        c.drawOval(skia.Rect(cx - (w + 40.0) * k_, -34.0 * k_, cx + (w + 40.0) * k_, 34.0 * k_),
                   paint(col("#000000"), alpha * a_))


def _leg_shape(R, sd):
    fx, lift, tilt = R.foot[sd]
    sg = 1.0 if sd == "l" else -1.0
    hip = _deform(R, sg * HIP_X, HIP_Y)
    foot_top = (fx, -80.0 - lift)
    rw = 112.0 + 10.0 * clamp(lift / 120.0)     # a lifted thigh comes toward the camera (a bit bigger)
    leg = smooth_path([(hip[0] - rw, hip[1] - 40.0), (hip[0] + rw, hip[1] - 40.0),
                       (foot_top[0] + rw * 0.95, foot_top[1]), (foot_top[0], foot_top[1] + 30.0),
                       (foot_top[0] - rw * 0.95, foot_top[1])], closed=True, tension=0.45)
    return leg, foot_top, rw


def _draw_legs(c, R, part="back"):
    """part "back": the leg columns behind the body; "front": the feet (and a lifted leg) in front of it."""
    for sd in ("r", "l"):
        fx, lift, tilt = R.foot[sd]
        sg = 1.0 if sd == "l" else -1.0
        lifted = lift > 6.0
        leg, foot_top, rw = _leg_shape(R, sd)
        if part == "back" and not lifted or part == "front" and lifted:
            if part == "front":
                # the knee comes forward over the bottom fringe: a rounded shaggy thigh, top tucked into the fur
                hip = _deform(R, sg * HIP_X, HIP_Y)
                kl = clamp(lift / 150.0)
                top_y = hip[1] + 40.0 - 50.0 * kl
                th = []
                for j in range(9):
                    u = j / 8.0
                    xx = lerp(hip[0] - rw * 1.02, hip[0] + rw * 1.02, u)
                    yy = top_y - 26.0 * math.sin(u * math.pi) + (10.0 if j % 2 else 0.0)
                    th.append((xx, yy))
                pts = th + [(foot_top[0] + rw * 0.95, foot_top[1]), (foot_top[0], foot_top[1] + 30.0),
                            (foot_top[0] - rw * 0.95, foot_top[1])]
                leg = smooth_path(pts, closed=True, tension=0.45)
                _cel(c, leg, C_FUR, C_FUR_SH, -18.0 * R.fac, -16.0)
            else:
                _cel(c, leg, C_FUR, C_FUR_SH, -18.0 * R.fac, -16.0)
            hm = skia.Path()
            hm.moveTo(foot_top[0] - rw * 0.5, foot_top[1] - 40.0)
            hm.quadTo(foot_top[0] - rw * 0.45, foot_top[1] - 10.0, foot_top[0] - rw * 0.3, foot_top[1] + 6.0)
            hm.moveTo(foot_top[0] + rw * 0.3, foot_top[1] - 46.0)
            hm.quadTo(foot_top[0] + rw * 0.4, foot_top[1] - 14.0, foot_top[0] + rw * 0.5, foot_top[1] + 2.0)
            _stroke(c, hm, C_FUR_DK, 3.0, 0.5)
        if part == "front":
            _draw_foot(c, R, fx, lift, tilt, sg)


def _draw_foot(c, R, fx, lift, tilt, sg):
    y0 = -lift
    rx, ry = 162.0, 62.0
    c.save()
    if lift > 6.0 and tilt <= 0:
        # a stomping foot raised toward the camera reads bigger, showing its pale sole pads
        kk = 1.0 + 0.22 * clamp(lift / 190.0)
        c.translate(fx, y0 - 40.0)
        c.scale(kk, kk)
        c.translate(-fx, -(y0 - 40.0))
        sole = skia.Path()
        sole.addOval(skia.Rect(fx - rx * 0.8, y0 - 26.0, fx + rx * 0.8, y0 + 22.0 * clamp(lift / 120.0)))
        _fill(c, sole, C_PAD)
    if tilt > 0:
        # toes up toward the camera: the foot shows a sliver of pale sole under the toes
        sole = skia.Path()
        sole.addOval(skia.Rect(fx - rx * 0.85, y0 - 30.0, fx + rx * 0.85, y0 + 14.0 * tilt))
        _fill(c, sole, C_PAD)
        c.translate(fx, y0 - 50.0)
        c.scale(1.0 + 0.04 * tilt, 1.0 + 0.1 * tilt)
        c.translate(-fx, -(y0 - 50.0))
    foot = smooth_path([(fx - rx, y0 - 40.0), (fx - rx * 0.6, y0 - ry - 40.0), (fx + rx * 0.6, y0 - ry - 40.0),
                        (fx + rx, y0 - 40.0), (fx + rx * 0.8, y0 - 6.0), (fx, y0 + 2.0), (fx - rx * 0.8, y0 - 6.0)],
                       closed=True, tension=0.5)
    _cel(c, foot, C_FUR, C_FUR_SH, -14.0 * R.fac, -12.0)
    # toes along the front-bottom edge with blunt dark nails
    for k in (-1, 0, 1):
        tx = fx + k * 72.0
        ty = y0 - 18.0 - (6.0 if k == 0 else 0.0) - 18.0 * tilt
        _oval2(c, skia.Rect(tx - 42.0, ty - 30.0, tx + 42.0, ty + 18.0), C_FUR_HI if k != 1 else C_FUR, C_FUR_SH,
               -8.0 * R.fac, -8.0)
        nail = skia.Path()
        nail.addOval(skia.Rect(tx - 13.0, ty + 2.0, tx + 13.0, ty + 18.0))
        _fill(c, nail, C_CLAW)
        c.drawCircle(tx - 4.0, ty + 7.0, 3.0, paint(C_NOSE_HI, 0.8))
    c.restore()


def _draw_ears_horns(c, R):
    for sg in (-1.0, 1.0):
        # tiny round ear (mostly behind the head)
        ex_, ey_ = _deform(R, sg * 326.0, -1440.0)
        k = _local_scale(R, (sg * 326.0, -1440.0))
        ear = skia.Path()
        ear.addCircle(ex_ + sg * 8.0 * k, ey_, 44.0 * k)
        _cel(c, ear, C_FUR, C_FUR_SH, -8.0 * R.fac, -8.0)
        inner = skia.Path()
        inner.addCircle(ex_ + sg * 12.0 * k, ey_ + 3.0 * k, 24.0 * k)
        _fill(c, inner, C_EAR_IN)
        c.drawCircle(ex_ + sg * 8.0 * k, ey_ + 8.0 * k, 12.0 * k, paint(C_FUR_SH, 0.6))
    for sg in (-1.0, 1.0):
        bx, by = 165.0 * sg, -1500.0
        p0 = _deform(R, bx, by)
        k = _local_scale(R, (bx, by))
        ang = R.tilt * smoothstep((-by - 940.0) / 260.0) + R.lean
        c.save()
        c.translate(*p0)
        c.rotate(ang)
        c.scale(1.3 * k * sg, 1.3 * k)
        # a small curled nub: thick base spiralling outward and down
        horn = skia.Path()
        horn.moveTo(-26.0, 10.0)
        horn.cubicTo(-30.0, -40.0, 30.0, -78.0, 70.0, -52.0)
        horn.cubicTo(96.0, -34.0, 86.0, 4.0, 62.0, 4.0)
        horn.cubicTo(46.0, 4.0, 42.0, -14.0, 54.0, -20.0)
        horn.cubicTo(44.0, -36.0, 14.0, -30.0, 22.0, 12.0)
        horn.close()
        c.drawPath(horn, paint(C_HORN_LINE, 0.9, stroke=4.0))
        _fill(c, horn, C_HORN_SH)
        c.save()
        c.clipPath(horn, doAntiAlias=True)
        c.translate(-5.0, -6.0)
        _fill(c, horn, C_HORN)
        c.restore()
        for j in range(4):
            u = 0.2 + j * 0.2
            rr = skia.Path()
            xx = lerp(-18.0, 70.0, u)
            yy = lerp(0.0, -58.0, u) + 10.0 * math.sin(u * math.pi)
            rr.moveTo(xx - 8.0, yy - 10.0 + j * 2)
            rr.quadTo(xx, yy + 2.0, xx + 10.0, yy + 12.0)
            _stroke(c, rr, C_HORN_SH, 2.4, 0.9)
        c.restore()


def _draw_body(c, R):
    B = _base()
    body = R.body_path
    locks, strands = _locks_path(R)
    dx, dy = -46.0 * R.fac, -30.0
    # contour underlays (only the outside edges survive), shade fills, then the lit base shifted toward the light
    c.drawPath(locks, paint(C_LINE, 0.85, stroke=4.4))
    c.drawPath(body, paint(C_LINE, 0.85, stroke=4.4))
    _fill(c, body, C_FUR_SH)
    _fill(c, locks, C_FUR_SH)
    sb = skia.Path(body)
    sb.offset(dx, dy)
    c.save()
    c.clipPath(sb, doAntiAlias=True)
    _fill(c, body, C_FUR)
    _fill(c, locks, C_FUR)
    c.restore()
    _stroke(c, strands, C_FUR_DK, 3.0, 0.45)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    # soft top-light sheen on the upper (lit) side
    hx, hy = _deform(R, -220.0 * R.fac, -1250.0)
    # cel highlight: a crescent along the lit edge of the silhouette (second, lighter tone)
    hl = skia.Path(body)
    hl.offset(-dx * 0.9, -dy * 0.9)
    c.save()
    c.clipPath(hl, skia.ClipOp.kDifference, True)
    c.drawRect(skia.Rect(-900.0, -1800.0, 900.0, 100.0), paint(C_FUR_HI, 0.5))
    c.restore()
    # belly patch (shifts with the body turn)
    th = R.turn * 0.85
    bel = [_deform(R, _turn_x(R, x, 700.0), y) for (x, y) in B["belly"]]
    bp = smooth_path(bel, closed=True, tension=0.42)
    R.belly_path = bp
    c.drawPath(bp, paint(C_FUR_SH, 0.6, stroke=3.2))
    _fill(c, bp, C_BELLY_SH)
    sbp = skia.Path(bp)
    sbp.offset(-40.0 * R.fac, -40.0)
    lit = skia.Op(bp, sbp, skia.PathOp.kIntersect_PathOp)
    if lit is not None:
        _fill(c, lit, C_BELLY)
    c.save()
    c.clipPath(bp, doAntiAlias=True)
    bh = _deform(R, -120.0 * R.fac + 600.0 * math.sin(th), -760.0)
    c.drawOval(skia.Rect(bh[0] - 230.0, bh[1] - 250.0, bh[0] + 170.0, bh[1] + 190.0), paint(C_BELLY_HI, 0.22))
    # a few soft belly fur strokes
    for i in range(9):
        x = (hash01(i, 71) - 0.5) * 560.0
        y = -330.0 - hash01(i, 73) * 600.0
        a = _deform(R, _turn_x(R, x - 10.0, 700.0), y - 12.0)
        b = _deform(R, _turn_x(R, x, 700.0), y + 8.0)
        d = _deform(R, _turn_x(R, x + 12.0, 700.0), y - 10.0)
        mk = skia.Path()
        mk.moveTo(*a)
        mk.lineTo(*b)
        mk.lineTo(*d)
        _stroke(c, mk, C_BELLY_SH, 3.0, 0.55)
    c.restore()
    # fur marks (hanging tufts)
    sh = skia.Path()
    hi = skia.Path()
    for (a, b, d, y, x) in B["marks"]:
        pa, pb, pd = _deform(R, *a), _deform(R, *b), _deform(R, *d)
        lit = (x * R.fac < 60.0) and y < -500.0
        tgt = hi if lit else sh
        tgt.moveTo(*pa)
        tgt.cubicTo(pa[0] + 2.0, (pa[1] + pb[1]) * 0.5, pb[0] - 2.0, pb[1] - 4.0, *pd)
    _stroke(c, sh, C_FUR_DK, 3.4, 0.5)
    _stroke(c, hi, C_FUR_HI, 3.2, 0.65)
    # moss clumps growing in the fur
    for (cpt, rad, seed) in B["moss"]:
        _draw_moss(c, R, cpt, rad, seed)
    c.restore()


def _draw_moss(c, R, cpt, rad, seed):
    """A clump of moss growing in the fur: overlapping round cushions (plain circles: fast) + sprouts."""
    p0 = _deform(R, *cpt)
    k = _local_scale(R, cpt)
    blobs = []
    for i in range(8):
        a = hash01(i, seed * 7) * 2 * math.pi
        d = hash01(i, seed * 7 + 1) * rad * 0.75
        r = rad * (0.3 + 0.22 * hash01(i, seed * 7 + 2)) * k
        blobs.append((p0[0] + math.cos(a) * d * k, p0[1] + math.sin(a) * d * k * 0.7, r))
    lp = paint(C_LINE, 0.8)
    for x, y, r in blobs:
        c.drawCircle(x, y, r + 2.5 * k, lp)
    dk = paint(C_MOSS_DK)
    for x, y, r in blobs:
        c.drawCircle(x, y, r, dk)
    mp = paint(C_MOSS)
    lx, ly = -0.22 * R.fac, -0.28
    for x, y, r in blobs:
        c.drawCircle(x + lx * r, y + ly * r, r * 0.78, mp)
    hp = paint(C_MOSS_HI, 0.8)
    for x, y, r in blobs[::2]:
        c.drawCircle(x + lx * r * 1.6, y + ly * r * 1.6, r * 0.22, hp)
    # two tiny sprouts
    for i in range(2):
        x = p0[0] + (hash01(i, seed * 13) - 0.5) * rad * k
        y = p0[1] - rad * 0.35 * k
        sp = skia.Path()
        sp.moveTo(x, y)
        sp.quadTo(x + 4.0 * k, y - 14.0 * k, x + 2.0 * k, y - 24.0 * k)
        _stroke(c, sp, C_MOSS_DK, 2.6 * k, 0.9)
        c.drawCircle(x + 2.0 * k, y - 25.0 * k, 4.5 * k, paint(C_MOSS_HI, 0.95))


# --------------------------------------------------------------------------- face (drawn in base face coords via R.face)
def _brow_pts(R, sd):
    sg = 1.0 if sd == "l" else -1.0
    raise_ = R.brow_raise + (R.brow_asym if sd == "l" else -0.6 * R.brow_asym)
    fur, wor = R.brow_furrow, R.brow_worry
    cx, cy = sg * EYE_X, EYE_Y - 60.0 - 34.0 * raise_
    inner = (cx - sg * 50.0 + sg * 10.0 * fur, cy + 24.0 * fur - 22.0 * wor)
    outer = (cx + sg * 50.0, cy - 2.0 - 10.0 * fur + 8.0 * wor)
    mid = (cx, cy - 9.0 - 5.0 * wor)
    return inner, mid, outer


def _draw_face(c, R):
    c.save()
    c.concat(R.face)
    # cheeks (puff up with smile / squint / huff)
    up = 0.5 * clamp(R.smile) + 0.5 * R.squint
    for sg in (-1.0, 1.0):
        cx, cy = sg * 186.0, -1258.0 - 14.0 * up
        r = 58.0 + 26.0 * R.cheek_puff
        ch = skia.Path()
        ch.addOval(skia.Rect(cx - r * (1.0 + 0.3 * R.cheek_puff), cy - r * 0.62, cx + r * (1.0 + 0.3 * R.cheek_puff),
                             cy + r * 0.62))
        _fill(c, ch, C_FUR_HI, 0.2 + 0.3 * R.cheek_puff + 0.15 * up, blur=6.0)
        arc = skia.Path()
        arc.moveTo(cx - sg * 46.0, cy - 6.0)
        arc.quadTo(cx, cy - 24.0 - 10.0 * up, cx + sg * 46.0, cy - 2.0)
        _stroke(c, arc, C_FUR_SH, 3.0, 0.35 + 0.4 * up)
    # eyes
    for sd in ("l", "r"):
        _draw_eye(c, R, sd)
    # brows: chunky tufts of darker fur
    for sd in ("l", "r"):
        a, m, b = _brow_pts(R, sd)
        br = skia.Path()
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        th = 21.0
        br.moveTo(a[0] + nx * 9.0, a[1] + ny * 9.0)
        br.quadTo(m[0] - nx * th * 1.3, m[1] - ny * th * 1.3 - 10.0, b[0], b[1])
        br.quadTo(m[0] + nx * th * 0.25, m[1] + ny * th * 0.25 - 2.0, a[0] - nx * 9.0, a[1] - ny * 9.0)
        br.close()
        sg = 1.0 if sd == "l" else -1.0
        c.drawPath(br, paint(C_LINE, 0.7, stroke=3.0))
        _fill(c, br, C_FUR_DK)
        # little hairs
        for j in range(3):
            u = 0.25 + j * 0.25
            hx = a[0] + (b[0] - a[0]) * u
            hy = a[1] + (b[1] - a[1]) * u - 10.0
            hp = skia.Path()
            hp.moveTo(hx, hy)
            hp.lineTo(hx + sg * 9.0, hy - 9.0)
            _stroke(c, hp, C_FUR_DK, 3.0, 0.9)
    # nose
    _draw_nose(c, R)
    # mouth (+ teeth + tongue root)
    _draw_mouth(c, R)
    c.restore()


def _draw_eye(c, R, sd):
    sg = 1.0 if sd == "l" else -1.0
    cx, cy = sg * EYE_X, EYE_Y
    rs = 27.0
    lid = R.lid[sd]
    sq = R.squint
    happy = R.happy
    # socket: a slightly darker fur ring
    sock = skia.Path()
    sock.addOval(skia.Rect(cx - rs * 1.25, cy - rs * 1.05, cx + rs * 1.25, cy + rs * 1.05))
    _fill(c, sock, C_FUR_SH, 0.75, blur=3.0)
    closed = lid < 0.08
    if closed:
        # closed: happy "^" arcs when squeezed / smiling, otherwise a relaxed lid line
        ln = skia.Path()
        if happy > 0.3 or sq > 0.6:
            ln.moveTo(cx - 22.0, cy + 6.0)
            ln.quadTo(cx, cy - 22.0 * (0.6 + 0.4 * happy), cx + 22.0, cy + 6.0)
        else:
            ln.moveTo(cx - 22.0, cy - 2.0)
            ln.quadTo(cx, cy + 12.0, cx + 22.0, cy - 2.0)
        _stroke(c, ln, C_EYE, 7.0, 1.0)
        # squeeze creases at the outer corner
        if sq > 0.5:
            for j in (-1, 1):
                cr = skia.Path()
                cr.moveTo(cx + sg * 28.0, cy + j * 4.0)
                cr.lineTo(cx + sg * 40.0, cy + j * 12.0 - 2.0)
                _stroke(c, cr, C_FUR_DK, 3.0, 0.8)
        return
    # bead (with gaze)
    br = 15.5
    bx = cx + R.look_x * 9.0
    by = cy + R.look_y * 7.0
    clip = skia.Path()
    top = cy - rs + 2.0 * rs * (1.0 - lid)
    bot = cy + rs - 1.4 * rs * sq
    if bot < top + 4.0:
        bot = top + 4.0
    clip.addRect(skia.Rect(cx - rs * 1.4, top, cx + rs * 1.4, bot))
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    bead = skia.Path()
    bead.addCircle(bx, by, br)
    _fill(c, bead, C_EYE)
    # catch-light (always toward screen upper-left)
    hx = -5.5 * R.fac
    c.drawCircle(bx + hx, by - 5.5, 4.8, paint(WHITE, 0.95))
    c.drawCircle(bx - hx * 0.9, by + 6.0, 1.9, paint(WHITE, 0.8))
    c.restore()
    # upper lid (fur) + lid line
    if lid < 0.97:
        lp = skia.Path()
        lp.addRect(skia.Rect(cx - rs * 1.3, cy - rs * 1.2, cx + rs * 1.3, top))
        c.save()
        c.clipPath(sock, doAntiAlias=True)
        _fill(c, lp, C_FUR)
        c.restore()
        ll = skia.Path()
        ll.moveTo(cx - rs * 0.95, top + 2.0)
        ll.quadTo(cx, top - 3.0, cx + rs * 0.95, top + 2.0)
        _stroke(c, ll, C_EYE, 4.5, 0.95)
    if sq > 0.05:
        lp = skia.Path()
        lp.addRect(skia.Rect(cx - rs * 1.3, bot, cx + rs * 1.3, cy + rs * 1.3))
        c.save()
        c.clipPath(sock, doAntiAlias=True)
        _fill(c, lp, C_FUR_HI)
        c.restore()
        ll = skia.Path()
        ll.moveTo(cx - rs * 0.9, bot + 2.0)
        ll.quadTo(cx, bot - 4.0, cx + rs * 0.9, bot + 2.0)
        _stroke(c, ll, C_FUR_DK, 3.0, 0.8)


def _draw_nose(c, R):
    nx, ny = 0.0, -1270.0
    w, h = 40.0 + 6.0 * R.flare, 25.0
    wr = R.wrinkle
    if wr > 0.05:
        for j in range(3):
            cr = skia.Path()
            y = ny - h - 10.0 - j * 9.0
            cr.moveTo(-18.0 + j * 2, y)
            cr.quadTo(0.0, y - 6.0, 18.0 - j * 2, y)
            _stroke(c, cr, C_FUR_DK, 3.0, 0.8 * wr)
    nose = smooth_path([(nx - w, ny - h * 0.55), (nx - w * 0.5, ny - h), (nx + w * 0.5, ny - h),
                        (nx + w, ny - h * 0.55), (nx + w * 0.55, ny + h * 0.45), (nx, ny + h),
                        (nx - w * 0.55, ny + h * 0.45)], closed=True, tension=0.55)
    c.drawPath(nose, paint(C_LINE, 0.9, stroke=3.0))
    _fill(c, nose, C_NOSE)
    for sg in (-1.0, 1.0):
        n = skia.Path()
        rx = 9.0 + 4.0 * R.flare
        n.addOval(skia.Rect(nx + sg * 16.0 - rx, ny + 2.0, nx + sg * 16.0 + rx, ny + 12.0 + 2.0 * R.flare))
        _fill(c, n, col("#120A08"))
    hl = skia.Path()
    hl.moveTo(nx - w * 0.45, ny - h * 0.55)
    hl.quadTo(nx - w * 0.1, ny - h * 0.85, nx + w * 0.25, ny - h * 0.6)
    _stroke(c, hl, C_NOSE_HI, 4.5, 0.85)
    # philtrum down to the lip
    ph = skia.Path()
    ph.moveTo(nx, ny + h)
    ph.lineTo(nx, _mouth_geom(R)["upc"][1] + 2.0)
    _stroke(c, ph, C_FUR_DK, 3.0, 0.7)


def _mouth_geom(R):
    W = R.mouth_w * (1.0 - 0.25 * R.cheek_puff)
    sm = R.smile
    y0 = MOUTH_Y
    lift_l = sm * 42.0 + R.smirk * 30.0
    lift_r = sm * 42.0 - R.smirk * 18.0
    cl = (W, y0 - lift_l)          # +x corner ("l" side)
    cr_ = (-W, y0 - lift_r)
    op = R.mouth_open
    oh = 6.0 + 150.0 * op
    upc = (R.smirk * 10.0, y0 + sm * 12.0 - 6.0 * op)
    up = [cr_, (-W * 0.55, y0 + sm * 6.0 - 4.0 * op), upc, (W * 0.55, y0 + sm * 6.0 - 4.0 * op), cl]
    loc = (R.smirk * 8.0, y0 + oh + sm * 30.0)
    lo = [cr_, (-W * 0.6, y0 + oh * 0.75 + sm * 22.0), loc, (W * 0.6, y0 + oh * 0.75 + sm * 22.0), cl]
    return {"W": W, "up": up, "lo": lo, "upc": upc, "loc": loc, "cl": cl, "cr": cr_, "oh": oh}


def _draw_mouth(c, R):
    g = _mouth_geom(R)
    up, lo = g["up"], g["lo"]
    op = R.mouth_open
    if op < 0.03:
        ln = _curve(up)
        _stroke(c, ln, C_LINE, 5.5, 0.95)
        _stroke(c, _curve([(x, y + 6.0) for x, y in up[1:-1]]), C_FUR_HI, 2.4, 0.4)
    else:
        mouth = skia.Path()
        _cr(mouth, up)
        _cr(mouth, lo[::-1], move=False)
        mouth.close()
        c.drawPath(mouth, paint(C_LINE, 0.95, stroke=8.0))
        _fill(c, mouth, C_MOUTH)
        c.save()
        c.clipPath(mouth, doAntiAlias=True)
        # tongue (inside)
        tc = g["loc"]
        tong = skia.Path()
        tong.addOval(skia.Rect(tc[0] - g["W"] * 0.55, tc[1] - 48.0 - 30.0 * op, tc[0] + g["W"] * 0.55, tc[1] + 30.0))
        _fill(c, tong, C_TONGUE)
        _fill(c, tong, C_TONGUE_SH, 0.0)
        tl = skia.Path()
        tl.moveTo(tc[0], tc[1] - 40.0 - 22.0 * op)
        tl.lineTo(tc[0], tc[1] - 8.0)
        _stroke(c, tl, C_TONGUE_SH, 3.0, 0.7)
        c.drawOval(skia.Rect(tc[0] - 46.0, tc[1] - 40.0 - 26.0 * op, tc[0] - 12.0, tc[1] - 28.0 - 22.0 * op),
                   paint(C_TONGUE_HI, 0.5, blur=2.0))
        # big flat teeth hanging from the upper lip
        teeth = skia.Path()
        xs = (-1.5, -0.5, 0.5, 1.5)
        tw = 47.0
        for i, u in enumerate(xs):
            x0 = u * (tw + 4.0) - tw * 0.5 + R.smirk * 8.0
            x1 = x0 + tw
            xm = (x0 + x1) * 0.5
            ytop = _curve_y(up, xm) - 6.0
            h = 54.0 if abs(u) < 1 else 46.0
            tooth = smooth_path([(x0, ytop), (x1, ytop), (x1, ytop + h - 10.0), (x1 - 6.0, ytop + h),
                                 (x0 + 6.0, ytop + h), (x0, ytop + h - 10.0)], closed=True, tension=0.25)
            teeth.addPath(tooth)
        c.drawPath(teeth, paint(C_LINE, 0.8, stroke=4.0))
        _fill(c, teeth, C_TOOTH_SH)
        c.save()
        c.clipPath(teeth, doAntiAlias=True)
        c.translate(0.0, -7.0)
        _fill(c, teeth, C_TOOTH)
        c.restore()
        c.restore()
        # lips
        _stroke(c, _curve(up), C_LINE, 5.0, 0.95)
        _stroke(c, _curve(lo), C_LINE, 4.0, 0.9)
        _stroke(c, _curve([(x, y + 7.0) for x, y in lo[1:-1]]), C_FUR_HI, 3.0, 0.45)
    # corner dimples
    for crn, sg in ((g["cl"], 1.0), (g["cr"], -1.0)):
        dp = skia.Path()
        dp.moveTo(crn[0] - sg * 4.0, crn[1] - 10.0)
        dp.quadTo(crn[0] + sg * 12.0, crn[1] - 2.0, crn[0] + sg * 2.0, crn[1] + 12.0)
        _stroke(c, dp, C_LINE, 4.0, 0.75)


def _curve_y(pts, x):
    """Approximate y of a polyline-ish curve at x (linear between points)."""
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            u = (x - a[0]) / (b[0] - a[0])
            # mild curvature compensation (catmull bulge)
            return a[1] + (b[1] - a[1]) * u
    return pts[len(pts) // 2][1]


def _draw_puff(c, R):
    if R.puff is None:
        return
    p = R.puff
    if p <= 0.0 or p >= 1.0:
        return
    c.save()
    c.concat(R.face)
    a = (1.0 - p) ** 1.3
    for sg in (-1.0, 1.0):
        bx, by = sg * 18.0, -1258.0
        for j in range(3):
            q = clamp(p * 1.4 - j * 0.12)
            if q <= 0:
                continue
            d = 30.0 + 150.0 * ease_out(q)
            x = bx + sg * d * 0.55
            y = by + d * 0.7
            r = 12.0 + 26.0 * ease_out(q) + j * 4.0
            c.drawCircle(x, y, r, paint(C_PUFF, 0.55 * a * (1.0 - j * 0.2), blur=4.0 + 6.0 * q))
    c.restore()


# --------------------------------------------------------------------------- tongue + drip
def _tongue_geom(R, t):
    tg = R.tongue
    if tg <= 0.02:
        return None
    g = _mouth_geom(R)
    root = _map(R.face, (g["loc"][0], g["loc"][1] - 26.0))
    k = _mscale(R.face)
    L = (70.0 + 420.0 * tg) * k
    n = 10
    pts = [root]
    ang = 90.0 - R.lean * 0.5
    sway = 7.0 * math.sin(2 * math.pi * 0.55 * t) + 3.0 * math.sin(2 * math.pi * 1.3 * t + 1.0)
    for i in range(1, n + 1):
        u = i / n
        a = (ang + sway * u * u + 9.0 * math.sin(u * math.pi * 1.6) * (1.0 - 0.6 * R.ld)) * D2R
        p = pts[-1]
        pts.append((p[0] + math.cos(a) * L / n, p[1] + math.sin(a) * L / n))
    widths = []
    for i in range(n + 1):
        u = i / n
        w = 124.0 - 34.0 * math.sin(min(1.0, u * 1.25) * math.pi * 0.5) + 30.0 * smoothstep((u - 0.72) / 0.28)
        widths.append(w * k)
    return pts, widths, k


def _draw_tongue(c, R, t, drip=True):
    tgm = _tongue_geom(R, t)
    if tgm is None:
        return
    pts, widths, k = tgm
    tp = _ribbon(pts, widths, cap=1.15)
    _cel(c, tp, C_TONGUE, C_TONGUE_SH, -10.0 * k * R.fac, -6.0 * k, line_w=2.0 * k)
    # centre groove + wet shine
    _stroke(c, _curve(pts[1:-1]), C_TONGUE_SH, 4.0 * k, 0.8)
    shine = [(x - 26.0 * k * R.fac, y) for x, y in pts[2:-2]]
    if len(shine) >= 2:
        _stroke(c, _curve(shine), C_TONGUE_HI, 5.0 * k, 0.7)
        c.drawCircle(shine[-1][0], shine[-1][1] + 16.0 * k, 5.0 * k, paint(WHITE, 0.7))
    # the lower lip lies over the tongue root
    c.save()
    c.concat(R.face)
    g = _mouth_geom(R)
    lo = g["lo"]
    lip = skia.Path()
    _cr(lip, [(x, y - 4.0) for x, y in lo[1:-1]])
    _stroke(c, lip, C_LINE, 4.0, 0.85)
    c.restore()
    if drip:
        _draw_drip(c, R, t, pts, widths, k)


def _drip_state(R, pts, widths, k, ex):
    d = ex.get("drip", None)
    if d is None or d <= 0.0:
        return None
    tip = pts[-1]
    tx, ty = _norm(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
    tip = (tip[0] + tx * widths[-1] * 0.55, tip[1] + ty * widths[-1] * 0.55)
    fall_d = ex.get("drip_fall", DRIP_FALL)
    if d < 0.6:
        g = d / 0.6
        r = (5.0 + 12.0 * g) * k
        stretch = 1.0 + 0.9 * smoothstep((g - 0.6) / 0.4)
        return {"pos": (tip[0], tip[1] + r * stretch * 0.9), "r": r, "stretch": stretch, "tip": tip, "fall": 0.0}
    f = (d - 0.6) / 0.4
    r = 17.0 * k
    fall = fall_d * k * f * f
    return {"pos": (tip[0], tip[1] + r * 1.6 + fall), "r": r * (1.0 - 0.15 * f), "stretch": 1.25 - 0.2 * f,
            "tip": tip, "fall": fall, "f": f}


def _draw_drip(c, R, t, pts, widths, k):
    st = _drip_state(R, pts, widths, k, R.ex)
    if st is None:
        return
    px, py = st["pos"]
    r = st["r"]
    s = st["stretch"]
    tip = st["tip"]
    if st["fall"] <= 0.0 or st.get("f", 1.0) < 0.12:
        # saliva strand from the tongue tip to the drop
        sp = skia.Path()
        sp.moveTo(tip[0] - 6.0 * k, tip[1] - 4.0)
        sp.quadTo(px - 3.0 * k, (tip[1] + py) * 0.5, px, py - r * s)
        sp.quadTo(px + 3.0 * k, (tip[1] + py) * 0.5, tip[0] + 6.0 * k, tip[1] - 4.0)
        sp.close()
        _fill(c, sp, C_SALIVA, 0.75)
    drop = skia.Path()
    drop.moveTo(px, py - r * s * 1.4)
    drop.cubicTo(px + r * 0.6, py - r * s * 0.6, px + r * 1.05, py + r * 0.1, px + r * 0.9, py + r * 0.45)
    drop.cubicTo(px + r * 0.6, py + r * 1.05, px - r * 0.6, py + r * 1.05, px - r * 0.9, py + r * 0.45)
    drop.cubicTo(px - r * 1.05, py + r * 0.1, px - r * 0.6, py - r * s * 0.6, px, py - r * s * 1.4)
    drop.close()
    c.drawPath(drop, paint(C_LINE, 0.35, stroke=2.0))
    _fill(c, drop, C_SALIVA, 0.85)
    c.drawCircle(px - r * 0.35, py - r * 0.05, r * 0.28, paint(WHITE, 0.95))
    c.drawCircle(px + r * 0.3, py + r * 0.5, r * 0.14, paint(WHITE, 0.6))


# --------------------------------------------------------------------------- arms (drawing)
def _arm_outline(A):
    S, E, P = A["S"], A["E"], A["P"]
    k = A["k"]
    rS, rE, rP = 96.0 * k, 82.0 * k, 68.0 * k
    n1 = _norm(-(E[1] - S[1]), E[0] - S[0])
    n2 = _norm(-(P[1] - E[1]), P[0] - E[0])
    nb = _norm(n1[0] + n2[0], n1[1] + n2[1])
    if nb == (0.0, 0.0):
        nb = n1
    cosh = max(0.45, nb[0] * n1[0] + nb[1] * n1[1])
    rEb = rE / cosh
    d2 = _norm(P[0] - E[0], P[1] - E[1])
    left = [(S[0] + n1[0] * rS, S[1] + n1[1] * rS), (E[0] + nb[0] * rEb, E[1] + nb[1] * rEb),
            (P[0] + n2[0] * rP, P[1] + n2[1] * rP)]
    right = [(P[0] - n2[0] * rP, P[1] - n2[1] * rP), (E[0] - nb[0] * rE * 0.95, E[1] - nb[1] * rE * 0.95),
             (S[0] - n1[0] * rS, S[1] - n1[1] * rS)]
    tipc = (P[0] + d2[0] * rP * 1.05, P[1] + d2[1] * rP * 1.05)
    back = (S[0] - _norm(E[0] - S[0], E[1] - S[1])[0] * rS * 0.9, S[1] - _norm(E[0] - S[0], E[1] - S[1])[1] * rS * 0.9)
    pts = left + [tipc] + right + [back]
    return smooth_path(pts, closed=True, tension=0.5), (n1, n2, d2, rP)


def _draw_arm(c, R, A, sd):
    path, (n1, n2, d2, rP) = _arm_outline(A)
    k = A["k"]
    # soft shadow on the body
    c.save()
    c.translate(10.0 * k * R.fac, 22.0 * k)
    _fill(c, path, C_FUR_DK, 0.22)
    c.drawPath(path, paint(C_FUR_DK, 0.12, stroke=16.0 * k))
    c.restore()
    _cel(c, path, C_FUR, C_FUR_SH, -16.0 * k * R.fac, -14.0 * k)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    # fur tufts / elbow fluff
    E = A["E"]
    for j in range(4):
        u = j / 3.0
        p = (lerp(A["S"][0], E[0], 0.4 + 0.6 * u) - n1[0] * 40.0 * k, lerp(A["S"][1], E[1], 0.4 + 0.6 * u) - n1[1] * 40.0 * k)
        mk = skia.Path()
        mk.moveTo(p[0] - 10.0 * k, p[1] - 12.0 * k)
        mk.lineTo(p[0], p[1] + 6.0 * k)
        mk.lineTo(p[0] + 10.0 * k, p[1] - 12.0 * k)
        _stroke(c, mk, C_FUR_DK, 3.0 * k, 0.5)
    c.restore()
    # paw: three fingers + blunt claws; palm pad when facing the camera
    P = A["P"]
    ang = A["ang"]
    palm = A.get("palm", 0.0)
    tap = A.get("tap", 0.0)
    c.save()
    c.translate(*P)
    c.rotate(ang)
    c.scale(k, k)
    if palm > 0.5:
        pad = skia.Path()
        pad.addOval(skia.Rect(-26.0, -30.0, 30.0, 30.0))
        _fill(c, pad, C_PAD)
        for j in (-1, 0, 1):
            tp = skia.Path()
            tp.addOval(skia.Rect(34.0, j * 24.0 - 9.0, 52.0, j * 24.0 + 9.0))
            _fill(c, tp, C_PAD)
    for j in (-1, 0, 1):
        lift = (12.0 * tap if j == 0 else 0.0)
        fx = 48.0 - lift * 0.3
        fy = j * 25.0
        frect = skia.Rect(fx - 22.0, fy - 18.0 - lift * 0.2, fx + 22.0, fy + 18.0 - lift * 0.2)
        c.save()
        if lift:
            c.rotate(-lift * 0.8, 30.0, fy)
        if palm <= 0.5:
            _oval2(c, frect, C_FUR, C_FUR_SH, -5.0, -5.0, line_w=1.6)
            nail = skia.Path()
            nail.moveTo(fx + 14.0, fy - 8.0)
            nail.quadTo(fx + 34.0, fy, fx + 14.0, fy + 8.0)
            nail.close()
            _fill(c, nail, C_CLAW)
        else:
            sep = skia.Path()
            sep.moveTo(fx - 18.0, fy + 12.0)
            sep.lineTo(fx + 18.0, fy + 12.0)
            if j < 1:
                _stroke(c, sep, C_FUR_SH, 3.0, 0.6)
        c.restore()
    c.restore()


# --------------------------------------------------------------------------- public
def draw(canvas, pose: Pose, t: float):
    R = _solve(pose, t)
    ex = R.ex
    c = canvas
    _set_light(pose)
    try:
        c.save()
        c.translate(pose.x + R.travel * pose.scale * R.fac, pose.y)
        c.scale(pose.scale * R.fac, pose.scale)
        _draw_shadow(c, R, ex.get("shadow", 0.32))
        far_arm = None
        if R.turn > 0.18:
            far_arm = "l"
        elif R.turn < -0.18:
            far_arm = "r"
        if far_arm and R.arms[far_arm]["name"] not in ("rest", "wave"):
            far_arm = None          # crossed / mouth-covering arms stay in front of the belly
        R.body_path = _body_path(R)
        _draw_ears_horns(c, R)
        if far_arm:
            _draw_arm(c, R, R.arms[far_arm], far_arm)
        _draw_legs(c, R, "back")
        _draw_body(c, R)
        _draw_legs(c, R, "front")
        _draw_face(c, R)
        _draw_puff(c, R)
        with_tongue = ex.get("tongue_layer", "with_body") == "with_body"
        covering = any(R.arms[sd]["name"] == "cover_mouth" for sd in ("l", "r"))
        if with_tongue and covering:
            _draw_tongue(c, R, t)
        for sd in ("r", "l"):      # "r" first: in "cross" the "l" forearm lies on top
            if sd != far_arm:
                _draw_arm(c, R, R.arms[sd], sd)
        if with_tongue and not covering:
            _draw_tongue(c, R, t)
        if pose.rim > 0.01:
            _rim(c, R, pose)
        c.restore()
    finally:
        _clear_light()


def _rim(c, R, pose):
    a = clamp(pose.rim)
    dx, dy = 6.0 * R.fac, 7.0
    for pth in (R.body_path,):
        c.save()
        c.clipPath(pth, doAntiAlias=True)
        sh = skia.Path(pth)
        sh.offset(dx, dy)
        c.clipPath(sh, skia.ClipOp.kDifference, True)
        c.drawPath(pth, paint(pose.rim_color, a * 0.85))
        c.restore()


def draw_tongue(canvas, pose: Pose, t: float):
    R = _solve(pose, t)
    c = canvas
    _set_light(pose)
    try:
        c.save()
        c.translate(pose.x + R.travel * pose.scale * R.fac, pose.y)
        c.scale(pose.scale * R.fac, pose.scale)
        _draw_tongue(c, R, t)
        c.restore()
    finally:
        _clear_light()


def _stage(pose, R, p):
    return (pose.x + (R.travel + p[0]) * pose.scale * R.fac, pose.y + p[1] * pose.scale)


def head_center(pose: Pose, t: float = 0.0):
    R = _solve(pose, t)
    return _stage(pose, R, _map(R.face, (0.0, EYE_Y)))


def mouth_pos(pose: Pose, t: float = 0.0):
    R = _solve(pose, t)
    g = _mouth_geom(R)
    return _stage(pose, R, _map(R.face, (0.0, (g["upc"][1] + g["loc"][1]) * 0.5)))


def hand_pos(pose: Pose, side: str, t: float = 0.0):
    R = _solve(pose, t)
    return _stage(pose, R, R.arms["l" if side == "l" else "r"]["P"])


def tongue_tip(pose: Pose, t: float = 0.0):
    R = _solve(pose, t)
    tg = _tongue_geom(R, t)
    if tg is None:
        return None
    return _stage(pose, R, tg[0][-1])


def drip_pos(pose: Pose, t: float = 0.0):
    R = _solve(pose, t)
    tg = _tongue_geom(R, t)
    if tg is None:
        return None
    st = _drip_state(R, tg[0], tg[1], tg[2], pose.extra or {})
    if st is None:
        return None
    return _stage(pose, R, st["pos"])


def foot_pos(pose: Pose, side: str, t: float = 0.0):
    R = _solve(pose, t)
    fx, lift, _ = R.foot["l" if side == "l" else "r"]
    return _stage(pose, R, (fx, -lift))


def stomp_offset(pose: Pose):
    ex = pose.extra or {}
    R = _R()
    _legs_state(R, ex, 0.0)
    return R.travel * pose.scale * (1.0 if pose.facing >= 0 else -1.0)


def _hits(p0, p1, hit):
    out = []
    k = math.floor(p0 - hit) + 1
    while k + hit <= p1:
        if k + hit > p0:
            out.append(k + hit)
        k += 1
    return out


def stomp_hits(phase0, phase1):
    return _hits(phase0, phase1, STOMP_HIT)


def tap_hits(phase0, phase1):
    return _hits(phase0, phase1, TAP_HIT)
