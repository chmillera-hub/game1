"""THE CADET - a passer-by (BIBLE.md section 2). Young, lanky, a bit gangly; light skin with freckles, short
tousled ginger hair, sage-green crew shirt under the crew's slate jacket (full sleeves), dark trousers, a lidded
takeaway coffee cup.

Built on Rae's rig machinery so the two share line weights, cel shading, eye construction, lip-sync, blinking,
lighting / rim light and the walk solver: this module loads its OWN instance of anim/char_rae.py (module
"anim._cadet_rig"; Rae's module object is untouched) and re-skins / re-proportions it through that instance's
globals and a few drawing-function overrides (hair, ears, nose + freckles, neck, torso taper, legs, sleeves,
cup and grip).

Rig contract (anim/rig.py):
    draw(canvas, pose, t, before_near_arm=None)   draw the cadet; canvas already carries the camera (stage
                                     units); before_near_arm(canvas) is drawn between his body and his near arm
    head_center(pose, t=None)        stage point between the eyes
    hand_pos(pose, side, t=None)     palm centre of his 'l' / 'r' hand (holding the cup: in front of it for the
                                     near hand, behind it for the far hand)
    ARMS                             rest, hold_cup, sip_cup, wave, hand_to_mouth, point
    HEIGHT                           floor -> top of the hair, standing, scale 1 (757; Rae 700, Quill 770)
Extras:
    draw_cup(canvas, x, y, scale=1.0, angle=0.0, flip=False)   the takeaway cup standing on its base at (x, y)
    cup_pose(pose, t=None) -> (x, y, scale, angle, flip) | None  the held cup; draw_cup(c, *cup_pose(p, t)) matches
    mouth_pos(pose, t=None), eye_pos(pose, side, t=None)
    blink(t)                         his natural blink (what lid_*=None uses)
    EXPR, expr(pose, name, amount=1.0, t=None)   face presets (neutral, what_now, side_eye, cough, half_smile,
                                     mutter, awkward)
    wave_arm(t, amount=1.0, side_base=None) -> ArmPose   the wave preset with its wiggle baked in for time t
    WAVE_HZ                          wave frequency (Hz)
    WALK_ADVANCE, walk_advance(pose), STRIDE   pelvis travel per walk cycle (148.3 at turn >= 0.3, scale 1)
    RIM_LIGHT_POS, RIM_MIN           as in Rae's rig (RIM_LIGHT_POS is reassignable here too)

Conventions: exactly Rae's (see anim/char_rae.py): pose.x = pelvis axis, facing=-1 is a pure mirror,
arm_r is the near arm once turned, ArmPose.across targets face / chest features, pose.mug = 'r' / 'l' holds
the coffee cup: the NEAR hand (arm_r once turned) is in front of the cup, its back toward the camera over the
lower part of the sleeve, the fingers wrapping round the cup's far side (BIBLE section 10, Rae's near grip);
the FAR hand wraps the back of the cup, which sits in front of it, fingertips curling round onto its front and
the thumb round the other side. Bringing it to the mouth locks the lid's spout onto the lower lip.
ARMS['wave'] (hand "wave") waves by itself from t: the forearm swings about the elbow and the wrist flaps;
the wiggle amplitude follows how far the arm is raised, so blends into / out of the wave do not pop.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import skia

from anim.core import auto_blink, clamp, col, lerp, light_filter, mix_col, smoothstep
from anim.rig import ArmPose, Pose


def _load_base():
    name = "anim._cadet_rig"
    m = sys.modules.get(name)
    if m is not None:
        return m
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("char_rae.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


B = _load_base()
D2R = B.D2R
_capsule, _cel, _fill, _stroke, _curve, _norm = B._capsule, B._cel, B._fill, B._stroke, B._curve, B._norm
_cr, _ribbon, smooth_path = B._cr, B._ribbon, B.smooth_path


def paint(*a, **k):
    return B.paint(*a, **k)


# =========================================================================== proportions (lanky)
B.HIP_H = 400.0
B.HIP_LAT = 21.0
B.THIGH, B.SHIN = 192.0, 188.0
B.KNEEL_HIP = 178.0
B.SIT_FOOT = 172.0
B.STRIDE, B.LIFT = 40.0, 10.0
B.SH_Y = -158.0
B.SH_A = 48.5
B.UPPER, B.FORE = 118.0, 108.0
B.NECK_PIVOT = -218.0
B.HEAD_S = 0.86
B.HEAD_SY = 1.06            # a longer face than Rae's
B.HAND_S = 1.42
B.WALK_BOB = 3.6            # a loose, slightly bouncy stroll
B.WALK_SWING = 10.0
B.WALK_LEAN = 1.5
TORSO_KY = 1.16             # torso length vs Rae's

# face: narrower, a little more angular jaw; slightly smaller eyes, thinner brows / lashes, no tired bags
B._FACE_TAB = [
    (-20, 57.5, 56.0, 70.0), (-8, 57.5, 57.0, 68.0), (4, 57.0, 58.0, 63.0), (14, 55.5, 58.0, 56.0),
    (24, 52.5, 57.5, 48.0), (32, 49.0, 56.5, 41.0), (40, 45.5, 55.0, 34.0), (47, 41.5, 53.5, 27.0),
    (53, 38.0, 52.0, 21.0), (58, 32.5, 50.0, 15.0), (62, 25.5, 47.5, 9.5), (65, 16.0, 44.5, 5.5),
    (67, 5.0, 41.0, 2.0)]
B._CR_A, B._CR_ZF, B._CR_ZB = 57.5, 56.0, 70.0
B.EX = 27.0
B.EW = 14.8
B.HU0, B.HL0 = 10.0, 7.9
B.RI = 9.3
B.LASH_TH = 0.62
B.LASH_FLICK = 0.3
B.LASH_EXTRA = False
B.BROW_W = (6.0, 2.6)
B.EYE_BAG = 0.08
B.MUG_HEEL = 3.0

# =========================================================================== palette
B.C_SKIN = col("#F2CBAA")
B.C_SKIN_SH = col("#D9A07F")
B.C_SKIN_HI = col("#FFE6D2")
B.C_SKIN_LINE = col("#9A5E45")
B.C_SKIN_DEEP = col("#B97A5C")
B.C_LID = mix_col("#F2CBAA", "#D9A07F", 0.38)
B.C_PALM = col("#F6D2B6")
B.C_HAIR = col("#C9622A")
B.C_HAIR_HI = col("#F2A35E")
B.C_HAIR_SH = col("#7A3112")
B.C_HAIR_SHEEN = col("#FFD09A")
B.C_BROW = col("#8A3D1B")
B.C_LASH = col("#4A2414")
B.C_SCLERA = col("#F6F1EC")
B.C_SCLERA_SH = col("#C9B3A8")
B.C_IRIS = col("#5B7A35")
B.C_IRIS_LT = col("#A9BE6B")
B.C_IRIS_MID = col("#3D5424")
B.C_PUPIL = col("#0E0B07")
B.C_MOUTH = col("#4A1C1E")
B.C_TONGUE = col("#C25560")
B.C_LIP = col("#C98472")
B.C_LIP_HI = col("#E3A796")
B.C_LIP_LINE = col("#7E3B2E")
B.C_SHIRT = col("#94AE88")
B.C_SHIRT_SH = col("#6F8B66")
B.C_PANTS = col("#2B2D35")
B.C_PANTS_SH = col("#1D1F25")
B.C_PANTS_LINE = col("#121318")
B.C_SHOE = col("#5A4032")
B.C_SHOE_SH = col("#3E2C22")
B.C_SHOE_LINE = col("#21170F")
B.C_SOLE = col("#E4DCCD")
B.C_PATCH = col("#E3B341")          # department patch (Rae's is teal)
B.C_BLUSH = col("#E58A7E")
C_FRECKLE = col("#C27650")
C_CUP = col("#F3F0E9")
C_CUP_SH = col("#D0CABF")
C_CUP_LINE = col("#8A847A")
C_SLEEVE = col("#B98653")
C_SLEEVE_SH = col("#946A3F")
C_LID_W = col("#ECEBE7")
C_LID_SH = col("#BEBCB6")
C_CUP_MARK = col("#F4E6CF")

# =========================================================================== cup (replaces the mug)
CUP_BW, CUP_TW, CUP_BH, CUP_LH = 9.0, 12.5, 33.0, 6.5   # base units: bottom / top half-width, body / lid height
B.MUG_W, B.MUG_H = CUP_TW, CUP_BH + CUP_LH
B.MUG_S = 1.36              # ~53 units tall
B.MUG_TILT = 36.0


def _cup_hw(y):
    """Half-width of the cup body at base-unit height y (<= 0)."""
    return lerp(CUP_BW, CUP_TW, clamp(-y / CUP_BH))


def _cup_body_path():
    p = skia.Path()
    _cr(p, [(-CUP_TW, -CUP_BH), (-(CUP_BW + 0.4), -1.6), (-CUP_BW + 1.6, 0.0)])
    _cr(p, [(CUP_BW - 1.6, 0.0), (CUP_BW + 0.4, -1.6), (CUP_TW, -CUP_BH)], move=False)
    p.close()
    return p


def _mug_local(c, flip=False, handle=True):
    """The takeaway cup in its own frame (bottom centre at the origin, base units scaled by MUG_S). The sip spout
    sits on the -x side of the lid (+x when flip)."""
    S = B.MUG_S
    c.scale(-S if flip else S, S)
    body = _cup_body_path()
    _fill(c, body, C_CUP_SH)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.translate(-3.6, 0)
    _fill(c, body, C_CUP)
    c.restore()
    # kraft sleeve
    y0, y1 = -9.0, -24.0
    sl = skia.Path()
    sl.moveTo(-_cup_hw(y1) - 0.4, y1)
    sl.lineTo(_cup_hw(y1) + 0.4, y1)
    sl.lineTo(_cup_hw(y0) + 0.4, y0)
    sl.lineTo(-_cup_hw(y0) - 0.4, y0)
    sl.close()
    _fill(c, sl, C_SLEEVE_SH)
    c.save()
    c.clipPath(sl, doAntiAlias=True)
    c.translate(-2.8, 0)
    _fill(c, sl, C_SLEEVE)
    c.restore()
    _stroke(c, sl, C_SLEEVE_SH, 0.8, 0.9)
    # plain printed band + a little steam squiggle (no brand-like logo: original IP)
    for yy in (y1 + 2.2, y0 - 2.2):
        _stroke(c, _curve([(-_cup_hw(yy) + 0.6, yy), (_cup_hw(yy) - 0.6, yy)]), C_CUP, 0.9, 0.55)
    sq = _curve([(-2.6, -12.8), (-3.6, -15.2), (-1.8, -17.4), (-2.8, -20.0)])
    _stroke(c, sq, C_CUP_MARK, 1.3, 0.9)
    sq2 = _curve([(1.0, -13.2), (0.0, -15.4), (1.8, -17.6), (0.8, -19.8)])
    _stroke(c, sq2, C_CUP_MARK, 1.3, 0.9)
    _stroke(c, body, C_CUP_LINE, 1.1, 0.9)
    c.drawRoundRect(skia.Rect(-CUP_TW + 2.6, -CUP_BH + 2.5, -CUP_TW + 4.6, y1 - 1.5), 1.0, 1.0, paint("#FFFFFF", 0.5))
    # lid: rim band + low dome with the spout on the -x side
    lid = skia.Path()
    lid.addRRect(skia.RRect.MakeRectXY(skia.Rect(-CUP_TW - 1.0, -CUP_BH - 3.0, CUP_TW + 1.0, -CUP_BH + 0.8), 1.6, 1.6))
    dome = smooth_path([(-CUP_TW + 0.6, -CUP_BH - 2.6), (-CUP_TW + 2.0, -CUP_BH - CUP_LH + 0.4),
                        (-CUP_TW + 6.0, -CUP_BH - CUP_LH), (CUP_TW - 3.0, -CUP_BH - CUP_LH + 1.6),
                        (CUP_TW - 0.6, -CUP_BH - 2.6)], closed=True, tension=0.4)
    _fill(c, dome, C_LID_SH)
    c.save()
    c.clipPath(dome, doAntiAlias=True)
    c.translate(-1.8, -0.6)
    _fill(c, dome, C_LID_W)
    c.restore()
    _stroke(c, dome, C_CUP_LINE, 0.9, 0.85)
    _fill(c, lid, C_LID_W)
    _stroke(c, lid, C_CUP_LINE, 0.9, 0.9)
    c.drawOval(skia.Rect(-CUP_TW + 3.0, -CUP_BH - CUP_LH + 0.6, -CUP_TW + 6.6, -CUP_BH - CUP_LH + 2.2), paint("#3A302A", 0.8))


B._mug_local = _mug_local


def draw_cup(canvas, x, y, scale=1.0, angle=0.0, flip=False):
    """The lidded takeaway cup standing on its base at (x, y); angle in degrees about the base centre."""
    B.draw_mug(canvas, x, y, scale, angle, flip)


def cup_pose(pose: Pose, t=None):
    """(x, y, scale, angle, flip) of the held cup (bottom centre, stage coords) or None.
    draw_cup(canvas, *cup_pose(pose, t)) reproduces the in-hand cup exactly."""
    return B.mug_pose(_prep(pose, t), t)


# --------------------------------------------------------------------------- grip
def _grip_fingers(s):
    """[(knuckle, tip, r_knuckle, r_tip)] round the cup's side s (+1 = +x), base units."""
    out = []
    for i, (y, r) in enumerate(((-26.0, 2.5), (-20.6, 2.6), (-15.2, 2.55), (-10.0, 2.2))):
        hw = _cup_hw(y)
        ln = 8.6 - 1.4 * (i == 3)
        out.append(((s * (hw + 3.2), y + 0.4), (s * (hw + 3.2 - ln), y - 0.2), r, r * 0.88))
    return out


def _draw_grip(c, s):
    fingers = _grip_fingers(s)
    body = _cup_body_path()
    fp = skia.Path()
    for kn, tp, rk, rt in fingers:
        _capsule(fp, kn, tp, rk, rt)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.save()
    c.translate(0.8 * (-s), 1.3)
    _fill(c, fp, C_CUP_LINE, 0.4, blur=1.3)
    c.restore()
    c.restore()
    _cel(c, fp, B.C_SKIN, B.C_SKIN_SH, -1.0, -1.3, line=B.C_SKIN_LINE, line_w=0.85, line_a=0.85)
    for kn, tp, rk, rt in fingers:
        ux, uy = _norm(tp[0] - kn[0], tp[1] - kn[1])
        jx, jy = tp[0] - ux * 3.6, tp[1] - uy * 3.6
        _stroke(c, _curve([(jx + uy * rt * 0.8, jy - ux * rt * 0.8), (jx - ux * 0.5, jy - uy * 0.5),
                           (jx - uy * rt * 0.8, jy + ux * rt * 0.8)]), B.C_SKIN_SH, 0.6, 0.6)
        nx_, ny_ = tp[0] - ux * 0.9, tp[1] - uy * 0.9 - 0.5
        c.drawOval(skia.Rect(nx_ - 1.3, ny_ - 0.9, nx_ + 1.3, ny_ + 0.7), paint("#FFF0E4", 0.5))
    # thumb round the other side, tip on the front
    y = -27.5
    hw = _cup_hw(y)
    th = _capsule(skia.Path(), (-s * (hw + 3.0), y + 1.6), (-s * (hw - 5.4), y - 0.8), 2.8, 2.4)
    _cel(c, th, B.C_SKIN, B.C_SKIN_SH, -1.0, -1.3, line=B.C_SKIN_LINE, line_w=0.85, line_a=0.85)
    c.drawOval(skia.Rect(-s * (hw - 4.6) - 1.4, y - 2.2, -s * (hw - 4.6) + 1.4, y - 0.4), paint("#FFF0E4", 0.5))


def _held_hand_behind(c, R):
    """The hand behind the cup (only the heel shows past the cup's edge)."""
    A = R.mug.arm
    W, hd = A.W, A.hd
    hand = skia.Path()
    _capsule(hand, (W[0] - hd[0] * 1.5, W[1] - hd[1] * 1.5), (W[0] + hd[0] * 27.0, W[1] + hd[1] * 27.0), 8.2, 10.8,
             bulge=0.6, bulge_at=0.3)
    _cel(c, hand, B.C_SKIN, B.C_SKIN_SH, -1.6, -1.4, line=B.C_SKIN_LINE, line_w=1.1, line_a=0.8)


def _held_cup_front(c, R):
    M = R.mug
    A = M.arm
    c.save()
    c.translate(M.x, M.y)
    c.rotate(M.ang)
    hs = M.hs
    c.save()
    _mug_local(c, flip=hs < 0)
    c.restore()
    c.scale(hs * B.MUG_S, B.MUG_S)
    a = -M.ang * D2R
    hd = A.hd
    hlx = (hd[0] * math.cos(a) - hd[1] * math.sin(a)) * hs
    k = smoothstep((hlx + 0.15) / 0.3)       # fingers round the side the hand points to
    for s, wgt in ((1.0, k), (-1.0, 1.0 - k)):
        if wgt <= 0.005:
            continue
        if wgt < 0.995:
            c.saveLayerAlpha(skia.Rect(-CUP_TW - 14, -B.MUG_H - 12, CUP_TW + 14, 8), int(255 * wgt))
            _draw_grip(c, s)
            c.restore()
        else:
            _draw_grip(c, s)
    c.restore()


def _draw_held_mug(c, R):
    _held_hand_behind(c, R)
    _held_cup_front(c, R)


B._draw_held_mug = _draw_held_mug
# near hand (in front of the cup, fingers round its far side): Rae's machinery on the cup's tapered body
B._mug_body_path = _cup_body_path
B._mug_hw = _cup_hw
B.MUG_BODY_H = CUP_BH
B.C_MUG_LINE = C_CUP_LINE          # contact shadow of the near hand on the cup
B.C_NAIL = col("#FFF0E4")


# =========================================================================== body overrides
_rae_torso_geo = B._torso_geo
_KX = [(-170.0, 0.95), (-120.0, 0.95), (-84.0, 0.93), (-46.0, 1.04), (-8.0, 0.92), (20.0, 0.88)]


def _kx(y):
    if y <= _KX[0][0]:
        return _KX[0][1]
    for (y0, k0), (y1, k1) in zip(_KX, _KX[1:]):
        if y < y1:
            return lerp(k0, k1, smoothstep((y - y0) / (y1 - y0)))
    return _KX[-1][1]


def _torso_geo(R):
    """Rae's jacket torso, longer and straighter (broader waist, narrower hips: a lanky young man)."""
    out, ne, fe = _rae_torso_geo(R)

    def f(q):
        return (q[0] * _kx(q[1]), q[1] * TORSO_KY)
    return [f(q) for q in out], [f(q) for q in ne], [f(q) for q in fe]


B._torso_geo = _torso_geo
_rae_draw_hips = B._draw_hips


def _draw_hips(c, R):
    c.save()
    c.scale(0.88, 1.0)
    _rae_draw_hips(c, R)
    c.restore()


B._draw_hips = _draw_hips


def _draw_neck(c, R):
    s = R.s
    nx = 4.0 * s
    collar = smooth_path([(nx - 26, -169), (nx - 24, -189), (nx, -196), (nx + 24, -189), (nx + 26, -169),
                          (nx, -174)], closed=True)
    _fill(c, collar, B.C_JACKET_SH)
    _stroke(c, collar, B.C_JACKET_LINE, 1.2, 0.8)
    neck = skia.Path()
    neck.addRRect(skia.RRect.MakeRectXY(skia.Rect(nx - 15.5, -238.0, nx + 15.5, -160.0), 8, 8))
    _fill(c, neck, B.C_SKIN)
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    c.concat(R.MHr)
    chin_y = 68.0 + B._jaw_dy(R.H, 68.0)
    cx = 30.0 * R.H.s
    c.drawOval(skia.Rect(cx - 52, chin_y - 40, cx + 52, chin_y + 15), paint(B.C_SKIN_SH, 0.95, blur=3.0))
    c.restore()
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    c.drawRect(skia.Rect(nx + 6.0, -240, nx + 30, -140), paint(B.C_SKIN_SH, 0.5, blur=3.0))
    c.restore()
    # Adam's apple hint
    if R.s < 0.7:
        ax = nx + 2.0 + 9.0 * R.s
        _stroke(c, _curve([(ax - 2.5, -190.0), (ax, -187.5), (ax + 2.5, -190.0)]), B.C_SKIN_SH, 1.2, 0.5)
    _stroke(c, neck, B.C_SKIN_LINE, 1.2, 0.55)


B._draw_neck = _draw_neck


def _draw_leg(c, L, R):
    p = skia.Path()
    _capsule(p, L.hip, L.knee, 19.5, 14.0, bulge=1.0, bulge_at=0.4)
    _capsule(p, L.knee, L.ankle, 14.0, 11.6, bulge=0.6, bulge_at=0.35)
    kneel_order = R.k > 0.5
    if kneel_order:
        B._draw_shoe(c, L, R)
    _cel(c, p, B.C_PANTS, B.C_PANTS_SH, -4.0, -2.0, line=B.C_PANTS_LINE, line_w=1.4, line_a=0.85)
    ax, ay = L.ankle
    kx, ky = L.knee
    ux, uy = _norm(ax - kx, ay - ky)
    nx, ny = -uy, ux
    hem = _curve([(ax - ux * 6 + nx * 10, ay - uy * 6 + ny * 10), (ax - ux * 3, ay - uy * 3),
                  (ax - ux * 6 - nx * 10, ay - uy * 6 - ny * 10)])
    _stroke(c, hem, B.C_PANTS_LINE, 1.1, 0.5)
    if R.sw > 0.3 or R.k > 0.3:
        hx_, hy_ = L.hip
        ux2, uy2 = _norm(kx - hx_, ky - hy_)
        _stroke(c, _curve([(kx - ux2 * 12 - uy2 * 7, ky - uy2 * 12 + ux2 * 7), (kx - ux2 * 4, ky - uy2 * 4),
                           (kx - ux2 * 12 + uy2 * 7, ky - uy2 * 12 - ux2 * 7)]), B.C_PANTS_SH, 1.6, 0.8)
    else:
        # a soft crease at the knee of the straight leg (trouser drape)
        _stroke(c, _curve([(kx - 6.0, ky - 3.0), (kx - 1.0, ky + 1.0), (kx + 4.0, ky - 1.0)]), B.C_PANTS_SH, 1.2, 0.6)
    if not kneel_order:
        B._draw_shoe(c, L, R)


B._draw_leg = _draw_leg


def _draw_arm(c, A, R):
    """Full-length jacket sleeves (Rae rolls hers): hand first, sleeve over the wrist, a cuff band."""
    S, E, W = A.S, A.E, A.W
    ux, uy = _norm(E[0] - S[0], E[1] - S[1])
    held = R.mug is not None and R.mug.arm is A
    near = held and R.mug.near
    if near:
        # near hand: the cup first, the hand over it (the sleeve then covers the wrist)
        B._draw_mug_in_hand(c, R)
        B._draw_near_grip(c, R)
    elif held:
        _held_hand_behind(c, R)
    else:
        B._draw_hand(c, A)
    vx, vy = _norm(W[0] - E[0], W[1] - E[1])
    We = (W[0] + vx * 2.0, W[1] + vy * 2.0)
    fore = skia.Path()
    _capsule(fore, (E[0] - ux * 2, E[1] - uy * 2), We, 12.2, 9.4, bulge=1.0, bulge_at=0.3)
    _cel(c, fore, B.C_JACKET, B.C_JACKET_SH, -3.0, -2.0, line=B.C_JACKET_LINE, line_w=1.3, line_a=0.85)
    fl = max(1.0, math.hypot(We[0] - E[0], We[1] - E[1]))
    cuff = B._limb_band(E, We, 1.0 - 9.0 / fl, 1.0, 9.8)
    _cel(c, cuff, B.C_JACKET_HI, B.C_JACKET, -2.0, -2.0, line=B.C_JACKET_LINE, line_w=1.2, line_a=0.85)
    if held and not near:
        _held_cup_front(c, R)
    sl = skia.Path()
    Ee = (E[0] + ux * 3, E[1] + uy * 3)
    _capsule(sl, S, Ee, 14.2, 12.6, bulge=1.0, bulge_at=0.35)
    _cel(c, sl, B.C_JACKET, B.C_JACKET_SH, -4.0, -2.5, line=B.C_JACKET_LINE, line_w=1.4, line_a=0.85)
    # elbow folds
    _stroke(c, _curve([(E[0] - ux * 13 - uy * 6, E[1] - uy * 13 + ux * 6), (E[0] - ux * 8, E[1] - uy * 8),
                       (E[0] - ux * 11 + uy * 5, E[1] - uy * 11 - ux * 5)]), B.C_JACKET_SH, 1.4, 0.8)
    _stroke(c, _curve([(E[0] + vx * 10 - vy * 6, E[1] + vy * 10 + vx * 6), (E[0] + vx * 14, E[1] + vy * 14),
                       (E[0] + vx * 11 + vy * 5, E[1] + vy * 11 - vx * 5)]), B.C_JACKET_SH, 1.1, 0.6)
    if A.o < 0 and A.layer == "front" and R.s < 0.65 and not R.back:
        px, py = S[0] + ux * 32 - uy * 3, S[1] + uy * 32 + ux * 3
        c.drawCircle(px, py, 5.0, paint(B.C_PATCH))
        c.drawCircle(px, py, 5.0, paint(B.C_JACKET_LINE, 0.8, stroke=1.0))
        c.drawCircle(px - 0.8, py - 0.8, 1.5, paint("#FFFFFF", 0.85))


B._draw_arm = _draw_arm


# =========================================================================== head overrides
def _draw_ear(c, H, slot):
    """Slightly larger, outward ears (short hair shows them); no earring."""
    x, y, vis = B._surf_az(H, slot * 90.0, 2.0)
    k = clamp(abs(H.s) * 1.3) if (slot * H.s) < 0 else 0.0
    w = lerp(11.0, 14.5, k)
    o = float(slot)
    if k > 0.2:
        o = -1.0 if H.s > 0 else 1.0
    pts = [(0.0, -16.0), (0.5 * w, -19.5), (0.95 * w, -13.0), (w, 0.0), (0.82 * w, 11.0), (0.45 * w, 19.0),
           (0.1 * w, 21.0), (-1.0, 12.0)]
    path = smooth_path([(x + o * px, y + py) for px, py in pts], closed=True)
    _fill(c, path, B.C_SKIN)
    _stroke(c, path, B.C_SKIN_LINE, 1.3, 0.7)
    inner = _curve([(x + o * 0.62 * w, y - 12.0), (x + o * 0.76 * w, y), (x + o * 0.5 * w, y + 9.0),
                    (x + o * 0.2 * w, y + 10.0)])
    _stroke(c, inner, B.C_SKIN_SH, 2.2, 0.9)
    c.drawOval(skia.Rect(x + o * 0.3 * w - 3.0, y - 6.0, x + o * 0.3 * w + 3.0, y + 4.0), paint(B.C_BLUSH, 0.25, blur=2.0))


B._draw_ear = _draw_ear

# freckles: (front-view x, y, radius) on the nose bridge and upper cheeks (mirrored)
_FRECKLES = []
for _i, (_x, _y, _r) in enumerate([(7.0, 13.0, 1.0), (11.5, 16.5, 1.15), (15.5, 12.0, 0.9), (21.0, 15.5, 1.2),
                                    (25.5, 11.5, 1.0), (28.5, 17.5, 1.25), (33.5, 13.5, 1.0), (24.0, 20.5, 0.9),
                                    (37.5, 18.5, 1.1), (31.0, 22.5, 0.95), (18.5, 19.5, 1.0), (4.0, 17.0, 0.85)]):
    _FRECKLES.append((_x, _y, _r))
    _FRECKLES.append((-_x - 0.8 * ((_i % 3) - 1), _y + 0.9 * ((_i % 2) - 0.5), _r * (0.9 + 0.2 * (_i % 2))))


def _draw_nose(c, H, P):
    """Freckles, then a slightly longer, straighter nose than Rae's."""
    pf = paint(C_FRECKLE, 0.5)
    for x0, y, r in _FRECKLES:
        x, yy, dep, fs = B._hx(H, x0, y, 0.5)
        if dep < 4.0:
            continue
        c.drawOval(skia.Rect(x - r * fs, yy - r * 0.85, x + r * fs, yy + r * 0.85), pf)
    s = H.s
    tx, ty, _, _ = B._hx(H, 0.0, 24.0, 9.0 + 4.0 * smoothstep((abs(s) - 0.3) / 0.4))
    nd = H.nod_dy * 0.95
    bx = B._hx(H, 0.0, 4.0, 3.0)[0]
    side = _curve([(bx + 3.0 + 1.5 * s, -3.0 + nd), (tx + 4.0 + 1.2 * s, 13.0 + nd), (tx + 5.0, 22.0 + nd)])
    _stroke(c, side, B.C_SKIN_SH, 4.0, 0.3 + 0.25 * min(1.0, abs(s) * 2), blur=2.0)
    c.drawOval(skia.Rect(tx - 6.0 + 3.0 * s, 25.5 + nd, tx + 7.5 + 2.0 * s, 30.5 + nd), paint(B.C_SKIN_SH, 0.45, blur=2.2))
    pts = []
    for x0, y, dz in ((-6.0, 23.0, 2.0), (-6.8, 26.0, 3.0), (-4.6, 28.0, 5.0), (-1.6, 28.3, 8.0), (0.8, 27.8, 9.0)):
        x, yy, _, _ = B._hx(H, x0, y, dz)
        pts.append((x, yy))
    _stroke(c, _curve(pts), B.C_SKIN_LINE, 1.5, 0.65)
    pts2 = []
    for x0, y, dz in ((2.8, 28.1, 8.0), (5.2, 27.6, 5.0), (6.6, 25.0, 2.5)):
        x, yy, _, _ = B._hx(H, x0, y, dz)
        pts2.append((x, yy))
    _stroke(c, _curve(pts2), B.C_SKIN_LINE, 1.5, 0.45 * clamp(1 - s * 1.6))
    for x0 in (-3.4, 3.4):
        x, yy, dep, fs = B._hx(H, x0, 27.2, 5.5)
        if x0 > 0 and s > 0.35:
            continue
        c.drawOval(skia.Rect(x - 1.7 * fs, yy - 0.8, x + 1.7 * fs, yy + 0.8), paint(B.C_SKIN_LINE, 0.4))
    c.drawOval(skia.Rect(tx - 4.6, ty - 5.5, tx + 0.6, ty - 1.4), paint(B.C_SKIN_HI, 0.7, blur=1.0))
    _stroke(c, _curve([(B._hx(H, -2.5, 2.0, 4.0)[0], 2.0 + nd), (B._hx(H, -3.0, 14.0, 7.0)[0], 14.0 + nd)]),
            B.C_SKIN_HI, 2.0, 0.35, blur=1.0)
    if P.sniffle > 0:
        c.drawCircle(tx + 0.5, ty + 1.5, 8.5, paint(B.C_BLUSH, 0.6 * P.sniffle, blur=4.0))


B._draw_nose = _draw_nose

# --------------------------------------------------------------------------- hair: short, tousled, ginger
# hairline: a boyish front hairline, short sideburns, tapered above the ears and at the nape
B._HAIRLINE = [(0, -50.0), (14, -49.0), (28, -45.0), (42, -38.0), (54, -29.0), (64, -19.0), (72, -6.0),
               (78, 5.0), (84, 6.0), (90, -9.0), (98, -13.0), (106, -6.0), (116, 4.0), (132, 14.0),
               (152, 20.0), (180, 22.0)]
_rae_hairline_y = B._hairline_y
# fringe: tufts of the front hairline hanging onto the forehead, swept toward local +x: (azimuth, half width, drop)
_FRINGE = [(-34.0, 9.0, 6.0), (-19.0, 9.0, 11.0), (-3.0, 10.0, 13.5), (13.0, 9.0, 11.0), (27.0, 8.0, 7.0)]


def _hairline_y(phi):
    y = _rae_hairline_y(phi)
    for c_, hw, drop in _FRINGE:
        u = (phi - c_) / hw
        if -1.0 < u < 1.0:
            # asymmetric tooth: steep on the -phi side, long slope on the +phi side (swept)
            v = (1.0 + u) / 0.45 if u < -0.55 else (1.0 - u) / 1.55
            y += drop * smoothstep(v) ** 1.3
    return y


B._hairline_y = _hairline_y
_TUFTS = 13


def _hair_outline(H):
    """Upper head silhouette grown into a tousled mop: ~10 units of volume on top tapering to the temples, with
    rounded tufts that lean toward the face side. Head-local; closed across the brow line (the hairline region
    does the real clipping)."""
    s = H.s
    lft = -B._sil_x(H, -20.0, -1)
    rgt = B._sil_x(H, -20.0, 1)
    cy, ry = -20.0, 70.0
    lean = 5.0 + 3.0 * s
    pts = []
    n = 2 * _TUFTS
    for i in range(n + 1):
        u = i / n
        ph = math.pi + u * math.pi             # pi .. 2pi: left side over the top to the right side
        cx_, sy_ = math.cos(ph), math.sin(ph)
        a = lft if cx_ < 0 else rgt
        bx, by = a * cx_, cy + ry * sy_
        nx, ny = _norm(cx_ / max(a, 1.0), sy_ / ry)
        top = math.sin(math.pi * u)                  # 0 at the temples, 1 on top
        thick = 2.5 + 7.5 * top ** 0.8
        tip = (i % 2 == 1)
        if tip:
            thick += (3.6 + 1.8 * math.sin(i * 2.1)) * (0.5 + 0.5 * top)
        tx_, ty_ = -ny, nx                           # tangent (left -> right over the top)
        sh = (lean * (1.0 if tip else 0.0)) * top
        pts.append((bx + nx * thick + tx_ * sh, by + ny * thick + ty_ * sh))
    # down the sides to below the hairline, then close under the brow (clipped by the hairline region anyway)
    sides_r = [(B._sil_x(H, y, 1) + 2.0, y) for y in (-6.0, 8.0, 22.0)]
    sides_l = [(B._sil_x(H, y, -1) - 2.0, y) for y in (22.0, 8.0, -6.0)]
    path = skia.Path()
    _cr(path, sides_l + pts + sides_r, tension=0.55)
    path.lineTo(sides_r[-1][0], 40.0)
    path.lineTo(sides_l[0][0], 40.0)
    path.close()
    return path, pts


def _draw_puff(c, H):
    """(Rae's puff slot) nothing behind the head for the cadet: his hair is all in the cap."""
    return None


B._draw_puff = _draw_puff


def _draw_cap_and_tie(c, H, head_out):
    region, hl_pts = B._hair_region(H)
    if region is None:
        return None
    outline, tips = _hair_outline(H)
    hair = skia.Op(outline, region, skia.PathOp.kIntersect_PathOp)
    if hair is None:
        return None
    sh_reg = skia.Path(region)
    sh_reg.offset(-0.6, 3.2)
    shadow = skia.Op(head_out, sh_reg, skia.PathOp.kIntersect_PathOp)
    if shadow is not None:
        _fill(c, shadow, B.C_SKIN_SH, 0.5, blur=1.2)
    gx = -24.0 - 14.0 * H.s
    sh = skia.GradientShader.MakeRadial((gx, -66.0), 120.0, [B.C_HAIR, B.C_HAIR, B.C_HAIR_SH], [0.0, 0.5, 1.0])
    c.drawPath(hair, paint(None, shader=sh))
    c.save()
    c.clipPath(hair, doAntiAlias=True)
    # tousled strands: short swept strokes on the tufts (lit) and between them (shade), light from the upper left
    dark, lit = skia.Path(), skia.Path()
    for i in range(1, len(tips) - 1):
        x, y = tips[i]
        dx, dy = _norm(-x * 0.35 + 6.0, -y - 34.0)      # into the mass, leaning with the sweep
        if i % 2 == 0:
            _cr(dark, [(x + dx * 2.0, y + dy * 2.0), (x + dx * 8.0 + 2.0, y + dy * 8.0), (x + dx * 13.0 + 5.0, y + dy * 13.0)])
        elif i % 4 == 1:
            _cr(lit, [(x + dx * 3.0 - 1.0, y + dy * 3.0), (x + dx * 9.0 + 0.5, y + dy * 9.0), (x + dx * 15.0 + 3.5, y + dy * 15.0)])
    for x0, y0, x1, y1, x2, y2 in ((-30, -70, -16, -62, -2, -60), (4, -76, 16, -68, 26, -64), (-44, -50, -34, -44, -24, -43)):
        _cr(dark, [(x0 + 30 * H.s, y0), (x1 + 30 * H.s, y1), (x2 + 30 * H.s, y2)])
    _stroke(c, dark, B.C_HAIR_SH, 1.5, 0.5)
    _stroke(c, lit, B.C_HAIR_HI, 1.8, 0.5)
    # sheen across the crown
    lx0 = -B._sil_x(H, -20.0, -1)
    rx0 = B._sil_x(H, -20.0, 1)
    gcx, gcy, grx, gry = (rx0 - lx0) * 0.5, -22.0, (rx0 + lx0) * 0.5, 72.0
    sp = []
    for i in range(7):
        a = (200.0 + i * 12.0) * D2R
        sp.append((gcx + grx * 0.82 * math.cos(a), gcy + gry * 0.82 * math.sin(a)))
    widths = [1.0 + 8.0 * math.sin(math.pi * (i + 0.15) / 6.3) ** 1.3 for i in range(7)]
    _fill(c, _ribbon(sp, widths), B.C_HAIR_HI, 0.75, blur=2.6)
    _fill(c, _ribbon(sp[1:-1], [w * 0.3 for w in widths[1:-1]]), B.C_HAIR_SHEEN, 0.5, blur=1.0)
    c.restore()
    _stroke(c, hair, B.C_HAIR_SH, 1.5, 0.75)
    return hl_pts


B._draw_cap_and_tie = _draw_cap_and_tie


def _draw_ringlet(c, H, slot, t, far=False):
    return None


B._draw_ringlet = _draw_ringlet


def _draw_bang(c, H, t):
    """(the cadet's fringe is part of the hair cap: see _hairline_y)"""
    return None


B._draw_bang = _draw_bang


def _light_cf(pose):
    """Lighting colour filter: a softer curve than Rae's (light ** 0.5) so his face, freckles and ginger hair stay
    readable in the dimmed symphony lighting (light ~0.3)."""
    return light_filter(max(0.0, pose.light) ** 0.5, pose.tint, pose.tint_amt)


B._light_cf = _light_cf


def blink(t, seed=23):
    """The cadet's natural blink (1 open .. 0 closed; ~3.3 s rhythm). draw() uses this when lid_l / lid_r is None."""
    return auto_blink(t, seed=seed, rate=3.3) if t is not None else 1.0


B.blink = blink

# =========================================================================== exports
STRIDE = B.STRIDE
WALK_ADVANCE = 4.0 * STRIDE * math.sin(68.0 * D2R)       # 148.3 pelvis travel per walk cycle (turn >= 0.3, scale 1)
B.WALK_ADVANCE = WALK_ADVANCE
RIM_LIGHT_POS = B.RIM_LIGHT_POS
RIM_MIN = B.RIM_MIN
HEIGHT = 757.0              # floor -> top of the hair, standing, scale 1 (measured; eyes at 660)
WAVE_HZ = 2.1

ARMS = {
    "rest": ArmPose(shoulder=4.0, elbow=9.0, wrist=0.0, hand="relaxed"),
    "hold_cup": ArmPose(shoulder=6.0, elbow=84.0, wrist=0.0, hand="hold", across=0.2),
    "sip_cup": ArmPose(shoulder=50.0, elbow=106.0, wrist=0.0, hand="hold", across=0.4),
    "wave": ArmPose(shoulder=24.0, elbow=146.0, wrist=-10.0, hand="wave", across=-0.6),
    "hand_to_mouth": ArmPose(shoulder=60.0, elbow=90.0, wrist=6.0, hand="fist", across=0.46),
    "point": ArmPose(shoulder=70.0, elbow=12.0, wrist=0.0, hand="point"),
}


def _wiggle(ap: ArmPose, t, amount=1.0) -> ArmPose:
    """Animated wave on a 'wave' hand: forearm swings about the elbow, wrist flaps a beat behind. The amplitude
    follows how far the arm is raised (so ArmPose.blend into / out of the wave does not pop)."""
    if t is None:
        return ArmPose(ap.shoulder, ap.elbow, ap.wrist, "palm_out", ap.across, ap.behind)
    lift = smoothstep((ap.shoulder + ap.elbow - 70.0) / 70.0) * amount
    w = 2.0 * math.pi * WAVE_HZ * t
    return ArmPose(ap.shoulder + 3.0 * lift * math.sin(w + 0.6), ap.elbow + 13.0 * lift * math.sin(w),
                   ap.wrist + 12.0 * lift * math.sin(w - 1.0), "palm_out", ap.across, ap.behind)


def wave_arm(t, amount=1.0, base: ArmPose | None = None) -> ArmPose:
    """ARMS['wave'] (or `base`, default rest) blended in by `amount` with the wiggle baked in for time t; the hand
    opens to 'palm_out' once amount >= 0.35. Use for explicit control; ARMS['wave'] alone also waves by itself."""
    b = base if base is not None else ARMS["rest"]
    ap = ArmPose.blend(b, ARMS["wave"], clamp(amount))
    ap = _wiggle(ArmPose(ap.shoulder, ap.elbow, ap.wrist, "wave", ap.across, ap.behind), t, 1.0)
    if amount < 0.35:
        ap = ArmPose(ap.shoulder, ap.elbow, ap.wrist, b.hand, ap.across, ap.behind)
    return ap


def _prep(pose: Pose, t):
    """Resolve the cadet-only conventions (the self-animating 'wave' hand) into a plain rig pose."""
    kw = {}
    for f in ("arm_l", "arm_r"):
        ap = getattr(pose, f)
        if ap.hand == "wave":
            kw[f] = _wiggle(ap, t)
    return pose.copy(**kw) if kw else pose


def draw(canvas, pose: Pose, t: float, before_near_arm=None):
    """Draw the cadet. The canvas must already carry the camera transform (stage coordinates).
    before_near_arm: optional callable(canvas), drawn between his body and his near arm (as in Rae's rig)."""
    B.RIM_LIGHT_POS = RIM_LIGHT_POS
    B.draw(canvas, _prep(pose, t), t, before_near_arm=before_near_arm)


def head_center(pose: Pose, t=None):
    return B.head_center(_prep(pose, t), t)


def mouth_pos(pose: Pose, t=None):
    return B.mouth_pos(_prep(pose, t), t)


def eye_pos(pose: Pose, side: str, t=None):
    return B.eye_pos(_prep(pose, t), side, t)


def hand_pos(pose: Pose, side: str, t=None):
    """Stage coords of the palm centre of his 'l' or 'r' hand (holding the cup: in front of it for the near hand,
    behind it for the far hand)."""
    return B.hand_pos(_prep(pose, t), side, t)


def walk_advance(pose: Pose) -> float:
    """Stage units the pelvis must travel (toward `facing`) per walk cycle: = WALK_ADVANCE at turn >= 0.3."""
    return B.walk_advance(pose)


# Face presets (Pose field overrides). Pass t to expr() so the preset's lids keep blinking.
EXPR = {
    "neutral": dict(),
    "what_now": dict(brow_raise=0.95, eye_wide=0.35, mouth_open=0.14, mouth_round=0.45, lid_l=1.0, lid_r=1.0,
                     head_nod=-0.05),
    "side_eye": dict(lid_l=0.66, lid_r=0.66, brow_raise=0.1, brow_furrow=0.12, smirk=0.12, look_x=0.85, look_y=0.05),
    "cough": dict(squint=0.65, lid_l=0.3, lid_r=0.3, brow_furrow=0.35, brow_worry=0.2, mouth_open=0.35,
                  mouth_round=0.55, head_nod=-0.25, shoulders_up=0.25),
    "half_smile": dict(smile=0.32, smirk=0.35, squint=0.12, brow_raise=0.2, lid_l=0.92, lid_r=0.92),
    "mutter": dict(mouth_open=0.18, mouth_round=0.2, brow_raise=0.3, lid_l=0.8, lid_r=0.8, look_y=0.15,
                   smile=0.08),
    "awkward": dict(smile=0.15, smirk=-0.25, brow_worry=0.35, brow_raise=0.3, lid_l=0.88, lid_r=0.88,
                    shoulders_up=0.3, look_y=0.2),
}


def expr(pose: Pose, name: str, amount: float = 1.0, t=None) -> Pose:
    """Blend face preset `name` into pose by `amount` (as Rae's expr; pass t to keep blinking on held lids)."""
    if amount <= 0.0:
        return pose
    kw = {}
    for k, v in EXPR[name].items():
        cur = getattr(pose, k)
        if k in ("lid_l", "lid_r"):
            val = lerp(1.0 if cur is None else cur, v, amount)
            if t is not None:
                val *= blink(t)
            kw[k] = val
            continue
        kw[k] = lerp(cur, v, amount)
    return pose.copy(**kw)
