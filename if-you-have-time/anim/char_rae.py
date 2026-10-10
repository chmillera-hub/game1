"""RAE - the human crew member (BIBLE.md section 2). Full procedural 2D rig.

Rig contract (anim/rig.py):
    draw(canvas, pose, t, before_near_arm=None)   draw Rae; canvas already carries the camera (stage units);
                                     before_near_arm(canvas) is drawn between her body and her near arm
    head_center(pose, t=None)        stage point between the eyes
    hand_pos(pose, side, t=None)     stage point at the palm centre of Rae's 'l' / 'r' hand (holding the mug: in
                                     front of it for the near hand, behind it for the far hand)
    ARMS                             ArmPose presets (rest, hold_mug, sip, mug_raise, point, hand_on_chest,
                                     wipe_eye, cover_mouth, hands_up, grip_knee, reach_back, shrug,
                                     hug_self, knee_rest)
    HEIGHT                           floor -> top of the hair puff, standing, scale 1 (700)
    (pass the draw time t to the anchor functions to include the automatic breathing; ~1 unit)
Extras:
    draw_mug(canvas, x, y, scale=1.0, angle=0.0, flip=False)   the mug standing on its base at (x, y)
    mug_pose(pose, t=None) -> (x, y, scale, angle, flip) | None  the held mug; draw_mug(c, *mug_pose(p, t)) matches
    mouth_pos(pose, t=None), eye_pos(pose, side, t=None)        stage points of the mouth centre / an eye centre
    blink(t)                         Rae's natural blink (1 open .. 0 shut) - exactly what lid_*=None uses
    EXPR, expr(pose, name, amount=1.0, t=None)   face presets; pass t so the preset's lids keep blinking
    WALK_ADVANCE, walk_advance(pose) stage units the pelvis must move per walk cycle (126.1 at turn >= 0.3)
    STRIDE                           half stride (side-plane units)
    RIM_LIGHT_POS                    stage point the rim light comes from (default: the window); reassignable
    RIM_MIN                          pose.rim at or below this is skipped (env.char_light(1.0) returns 0.06)

Conventions specific to Rae (on top of rig.py):
    * pose.x is the body axis (pelvis centre). Standing, the feet are under it; seated they rest ~148 units
      forward of it (shins ~vertical); kneeling, the shins point backward with the toes tucked under.
    * kneel 0..1 is the whole slide: the knees travel down to the floor (touching at kneel ~0.62) while the
      feet pivot onto their toes (heel lift <= 56 deg) and slide back; at 1 she sits back a little (hip 150).
    * bounce is a vertical body offset in stage y (+ = down, like Quill's rig); legs bend to absorb it.
    * smirk > 0 lifts the mouth corner on the `facing` side (and cocks the opposite brow).
    * ArmPose.across 0..1 pulls the hand toward the opposite shoulder (0.5 ~ face / chest midline; on the face
      0.25 lands on the same-side eye); across < 0 (Rae extension) spreads the arm outward (shrug, hands_up).
      The far arm (arm_l when turned) mirrors this: its across targets are the matching features on its own
      side, and a far hand resting near the knee / thigh lands on the far leg - presets work on either arm.
    * Arms swing toward `facing` once turn >= ~0.25; near the front view hanging segments swing slightly
      outward and raised ones come toward the camera; across < 0 spreads in the picture plane.
    * facing=-1 is a pure mirror image (as in Quill's rig): arm_r / lid_r / tear_r always belong to the
      side nearer the camera once Rae is turned (screen-left of the body for facing +1).
    * Mug: held round its body like a real mug; the hand continues the forearm (no cocked wrist). NEAR hand
      (arm_r once turned; BIBLE section 10): the hand is in front of the mug - the back of the hand / the edge
      of the palm toward the camera over the lower front of the body (the rim and the top of the logo show
      above it), the knuckles toward the handle side, the fingers wrapping round the far side (they vanish
      round its silhouette edge), the thumb tucked along the top of the hand; a hand coming down from above
      grips a little higher. FAR hand: the hand wraps the back of the mug, which sits in front of the hand
      (toward the camera) centred just past the palm; the fingers come round through the handle (outer side,
      logo toward the camera) with their tips over the front and the thumb rests on top of the handle (if the
      hand points the other way in the mug's frame - far arm near the front view - the fingers wrap the bare
      side instead). Either way mug_pose() is the drawn mug. When the hand comes near
      the mouth ('sip'), the rig places the rim on the lower lip and tilts the mug - for either arm. The lip
      lock blends in while the palm is ~78 -> 26 units from the mouth (scenes hold the mug at the chin / chest
      inside that band on purpose, so it is not widened). From hold_mug that band is blend(hold_mug, sip,
      ~0.47 -> 0.8): ease the lift onto blend(hold_mug, sip, 0.8) and lower from it, or the lock snaps on in
      a frame or two at the fastest point of the move.
    * Lids given explicitly (lid_l / lid_r not None) are used as-is (scene-controlled blinks); use
      lid = level * blink(t) or expr(..., t=t) for long holds so she keeps blinking.
    * walk: pose.walk is the phase in cycles; advance pose.x by walk_advance(pose) per cycle (toward facing) so
      the planted foot does not skate. Walking backward = decreasing phase while x moves the other way.
    * light: pose.light/tint/tint_amt go through core.light_filter applied to every paint (equivalent
      to a filtered layer, without the offscreen cost), with a perceptual curve light**0.65 so Rae's
      dark-brown skin still reads at light 0.25; eye catch-lights are re-drawn un-darkened in low light.
    * rim: a soft glow behind the silhouette (strongest toward the light, cut at the floor) plus a ~2.5 device
      px bright edge on the side facing RIM_LIGHT_POS, fixed in screen space (does not flip with facing).

Local drawing frame: facing=+1 orientation, origin = floor point under the pelvis, y down.
"Near" side = -x (Rae's right), "far" side = +x.
"""
from __future__ import annotations

import math

import numpy as np
import skia
from scipy.ndimage import gaussian_filter

from anim.core import auto_blink, breathe, clamp, col, lerp, light_filter, mix_col, noise1, smooth_path, smoothstep
from anim.core import paint as _core_paint
from anim.rig import ArmPose, Pose

# --------------------------------------------------------------------------- proportions
D2R = math.pi / 180.0
HIP_H = 326.0           # standing hip-joint height
HIP_LAT = 25.0          # half distance between hip joints
THIGH, SHIN = 158.0, 148.0
ANKLE_H = 22.0
SEAT_OFF = 13.0         # hip joint above the seat surface (sunk into the cushion)
KNEEL_HIP = 150.0       # kneeling: hip height (sitting back a little toward the heels)
KNEE_R = 16.5           # knee centre height when the knee rests on the floor
SIT_FOOT = 148.0        # seated: ankles this far forward of the hips (shins ~vertical, relaxed flop)
KNEEL_TOUCH = 0.62      # kneel blend value at which the knees touch the floor
KNEEL_HEEL = 56.0       # heel lift (deg) with the toes tucked under while kneeling
STRIDE, LIFT = 34.0, 8.0
SH_Y = -136.0           # shoulder joints (relative to pelvis)
SH_A = 52.0
UPPER, FORE = 104.0, 94.0
NECK_PIVOT = -184.0     # head pivot (relative to pelvis)
PIVOT_HL = 46.0         # pivot position in head-local y (eye line = 0)
HEAD_S = 0.92           # head-local units -> body units
HAND_S = 1.3            # hand-local units -> body units
TURN_DEG = 82.0

MUG_S = 1.4             # mug scale (base design is 26 x 32): ~45 units tall, ~0.31 of the head height
MUG_W, MUG_H = 13.0, 32.0
MUG_GX, MUG_GY = 22.0, -17.5    # the handle's grip point (mug-local, base units; legacy reference)
MUG_TILT = 40.0         # mug tilt (deg) when drinking
MUG_HEEL = 4.0          # held mug (far hand): its edge sits this far past the wrist (the heel of the hand shows)
# near hand (the one nearer the camera) on the mug: the hand is IN FRONT of the mug (BIBLE section 10), the back of
# the hand / the outer edge of the palm toward the camera, the fingers wrapping round the far side of the body
MUG_BODY_H = MUG_H      # height (base units) of the part of the body the near hand wraps (the cadet's: below the lid)
MUG_NEAR_Y = 0.25       # near hand: the fingers wrap the far side at this fraction of the body height (low: logo shows)
MUG_NEAR_FING = 11.0    # near hand: visible finger length (units) from the knuckles to the far silhouette edge
MUG_NEAR_KY = 19.0      # near hand: hand-local y of the knuckle line (the palm centre is at 15)

RIM_LIGHT_POS = (360.0, 380.0)   # stage point the rim light comes from (the window); scenes may reassign.
RIM_MIN = 0.08          # pose.rim at or below this is invisible and skipped (env.char_light(1) gives 0.06)

HEIGHT = 700.0         # floor -> top of the hair puff, standing (head top without the puff ~ 640, eyes ~ 552)
WALK_ADVANCE = 4.0 * STRIDE * math.sin(68.0 * D2R)   # 126.1: pelvis travel per walk cycle (turn >= 0.3, scale 1)

# look knobs (Rae's values; anim/char_cadet.py runs its own instance of this module with different ones)
LASH_TH = 1.0           # upper lash line thickness multiplier
LASH_FLICK = 1.0        # outer lash flick length multiplier
LASH_EXTRA = True       # the two little flick lashes above the outer corner
BROW_W = (6.4, 1.6)     # brow ribbon width, inner -> outer end
EYE_BAG = 0.2           # under-eye (tired) shading
WALK_BOB = 2.6          # pelvis bob per step
WALK_SWING = 8.0        # arm swing (deg)
WALK_LEAN = 3.0         # forward lean while walking (deg)
HEAD_SY = 1.0           # extra vertical scale of the head (face length)

# --------------------------------------------------------------------------- palette
C_SKIN = col("r_skin")
C_SKIN_SH = col("r_skin_shade")
C_SKIN_HI = col("r_skin_hi")
C_SKIN_LINE = col("#58301A")
C_SKIN_DEEP = col("#6A3E22")
C_LID = mix_col("r_skin", "r_skin_shade", 0.38)
C_PALM = col("#B98863")
C_HAIR = col("r_hair")
C_HAIR_HI = col("r_hair_hi")
C_HAIR_SH = col("#170D08")
C_HAIR_SHEEN = col("#6E4A35")
C_BROW = col("#22130C")
C_LASH = col("#150B07")
C_SCLERA = col("#F3EDE7")
C_SCLERA_SH = col("#BCA698")
C_IRIS = col("r_iris")
C_IRIS_LT = col("#9C6638")
C_IRIS_MID = col("#64391D")
C_PUPIL = col("#0C0604")
C_MOUTH = col("#3A1015")
C_TEETH = col("#F7F2EC")
C_TONGUE = col("#B4434D")
C_LIP = col("r_lips")
C_LIP_HI = col("#A3594A")
C_LIP_LINE = col("#43160F")
C_SHIRT = col("r_shirt")
C_SHIRT_SH = col("#B3742A")
C_JACKET = col("r_jacket")
C_JACKET_SH = col("r_jacket_shade")
C_JACKET_HI = col("#535B7D")
C_JACKET_LINE = col("#1B1E2C")
C_ZIP = col("#8D94B0")
C_PANTS = col("r_pants")
C_PANTS_SH = col("#1F2336")
C_PANTS_LINE = col("#151826")
C_SHOE = col("#3C3444")
C_SHOE_SH = col("#2A2430")
C_SHOE_LINE = col("#1A161E")
C_SOLE = col("#DED7CA")
C_TIE = col("#C99B50")
C_TIE_SH = col("#8F6A36")
C_TIE_HI = col("#EACB8E")
C_TEAR = col("tear")
C_BLUSH = col("blush")
C_STUD = col("#F2C86E")
C_PATCH = col("#2EC4B6")
C_MUG = col("mug")
C_MUG_SH = col("#C8C6BE")
C_MUG_LINE = col("#8A877F")
C_LOGO = col("mug_text")
C_COFFEE = col("#4B2A19")
C_NAIL = col("#D9A98A")
WHITE = col("#FFFFFF")

# Colour filter applied to every paint while the body is drawn (lighting). Filtering each paint is
# equivalent to filtering the composite for this affine colour matrix, and avoids an offscreen layer.
_CF = None


_CF_KEY = None


_PAINT_CACHE = {}


def paint(color, alpha=1.0, **kw):
    """core.paint plus the current lighting colour filter. Plain (shader-less) paints are cached: they are
    never mutated after creation, and building skia Paints / blur mask filters is a measurable cost."""
    if kw.get("shader") is None and kw.get("blend") is None:
        key = (color, round(alpha, 3), kw.get("stroke", 0.0), kw.get("blur", 0.0), kw.get("cap", "round"), _CF_KEY)
        p = _PAINT_CACHE.get(key)
        if p is None:
            p = _core_paint(color, alpha, **kw)
            if _CF is not None:
                p.setColorFilter(_CF)
            if len(_PAINT_CACHE) > 6000:
                _PAINT_CACHE.clear()
            _PAINT_CACHE[key] = p
        return p
    p = _core_paint(color, alpha, **kw)
    if _CF is not None:
        p.setColorFilter(_CF)
    return p


_PIC_CACHE = {}
_PIC_SEEN = set()


def _cached(c, key, bounds, fn):
    """Draw fn(canvas) through a skia.Picture cache keyed on key (+ current lighting). A picture is recorded
    only the second time a key is seen, so animated parameters (head turns, light fades) that produce a new
    key every frame just draw directly with no recording overhead; static holds replay the picture."""
    k = (key, _CF_KEY)
    pic = _PIC_CACHE.get(k)
    if pic is None:
        if k not in _PIC_SEEN:
            if len(_PIC_SEEN) > 4000:
                _PIC_SEEN.clear()
            _PIC_SEEN.add(k)
            fn(c)
            return
        rec = skia.PictureRecorder()
        fn(rec.beginRecording(bounds))
        pic = rec.finishRecordingAsPicture()
        if len(_PIC_CACHE) > 200:
            _PIC_CACHE.clear()
        _PIC_CACHE[k] = pic
    c.drawPicture(pic)


# --------------------------------------------------------------------------- small geometry helpers
class _NS:
    pass


def _cr(path, pts, move=True, tension=0.5):
    """Append an open Catmull-Rom curve through pts (same maths as core.smooth_path)."""
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


def _closed2(a, b):
    """Closed path: curve through a, then curve through b (b traversed as given)."""
    p = skia.Path()
    _cr(p, a)
    _cr(p, b, move=False)
    p.close()
    return p


def _norm(x, y):
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def _ribbon(center, widths):
    """Closed tapered ribbon around a polyline; widths are full widths per point."""
    n = len(center)
    L, R = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        w = widths[i] * 0.5
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    return _closed2(L, R[::-1])


def _capsule(path, a, b, ra, rb, bulge=0.0, bulge_at=0.5):
    """Add a tapered capsule (round ends) to `path` (CCW sub-paths; Simplify() before stroking)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ux, uy = _norm(dx, dy)
    if ux == 0 and uy == 0:
        path.addCircle(a[0], a[1], max(ra, rb), skia.PathDirection.kCCW)
        return path
    nx, ny = -uy, ux
    m = (a[0] + dx * bulge_at, a[1] + dy * bulge_at)
    rm = lerp(ra, rb, bulge_at) + bulge
    s1 = [(a[0] + nx * ra, a[1] + ny * ra), (m[0] + nx * rm, m[1] + ny * rm), (b[0] + nx * rb, b[1] + ny * rb)]
    s2 = [(b[0] - nx * rb, b[1] - ny * rb), (m[0] - nx * rm, m[1] - ny * rm), (a[0] - nx * ra, a[1] - ny * ra)]
    _cr(path, s1)
    _cr(path, s2, move=False)
    path.close()
    path.addCircle(a[0], a[1], ra, skia.PathDirection.kCCW)
    path.addCircle(b[0], b[1], rb, skia.PathDirection.kCCW)
    return path


def _fill(c, path, color, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, blur=blur))


def _stroke(c, path, color, width, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, stroke=width, blur=blur))


def _cel(c, path, base, shade, dx, dy, blur=0.0, line=None, line_w=1.3, line_a=0.8):
    """Cel shading: fill with shade, then the base colour shifted toward the light, clipped.
    The shade shows as a crescent on the side opposite to (dx, dy). The contour is drawn as an
    underlay stroke (so unions of overlapping sub-paths need no path simplification)."""
    if line is not None:
        c.drawPath(path, paint(line, line_a, stroke=line_w * 2.0))
    _fill(c, path, shade)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    c.translate(dx, dy)
    _fill(c, path, base, blur=blur)
    c.restore()
    return path


def _ik(a, b, l1, l2, prefer):
    """2-bone IK: joint between a and b. `prefer(j1, j2)` picks one of the two solutions."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return (a[0] + l1, a[1])
    if d >= l1 + l2 - 1e-6:
        r = l1 / (l1 + l2)
        return (a[0] + dx * r, a[1] + dy * r)
    d = max(d, abs(l1 - l2) + 1e-4)
    ca = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1.0, 1.0)
    ang = math.acos(ca)
    base = math.atan2(dy, dx)
    j1 = (a[0] + l1 * math.cos(base + ang), a[1] + l1 * math.sin(base + ang))
    j2 = (a[0] + l1 * math.cos(base - ang), a[1] + l1 * math.sin(base - ang))
    return prefer(j1, j2)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


# --------------------------------------------------------------------------- head geometry
# Head-local frame: origin on the head's vertical axis at eye level, y down (scaled by HEAD_S).
# Each horizontal cross-section is two half-ellipses: half-width a, front depth zf, back depth zb.
_FACE_TAB = [  # y, a, zf, zb
    (-20, 61.0, 58.0, 72.0), (-8, 61.0, 59.0, 70.0), (4, 60.5, 60.0, 65.0), (14, 59.0, 60.0, 58.0),
    (24, 56.0, 59.0, 50.0), (32, 52.0, 58.0, 43.0), (40, 47.5, 56.5, 36.0), (47, 42.0, 55.0, 29.0),
    (53, 35.5, 53.0, 22.0), (58, 28.0, 50.5, 16.0), (62, 20.0, 47.5, 10.0), (65, 12.0, 44.0, 6.0),
    (67, 4.0, 40.0, 2.0)]
_CR_CY, _CR_RY, _CR_A, _CR_ZF, _CR_ZB = -20.0, 70.0, 61.0, 58.0, 72.0
_OUT_YS = [-90, -87, -81, -72, -60, -46, -32, -20, -10, -2, 6, 14, 22, 30, 38, 46, 53, 58, 62, 65]
EX = 28.5               # eye centre offset from the face centre line
EW = 16.6               # eye half width
HU0, HL0 = 11.4, 9.0    # upper / lower lid heights when open
RI = 11.0               # iris radius
MOUTH_Y = 42.5


def _prof(y):
    if y <= _CR_CY:
        q = (y - _CR_CY) / _CR_RY
        k = math.sqrt(max(0.0, 1.0 - q * q))
        return _CR_A * k, _CR_ZF * k, _CR_ZB * k
    tab = _FACE_TAB
    if y >= tab[-1][0]:
        return tab[-1][1], tab[-1][2], tab[-1][3]
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, a0, f0, b0 = tab[i - 1]
            y1, a1, f1, b1 = tab[i]
            u = (y - y0) / (y1 - y0)
            return a0 + (a1 - a0) * u, f0 + (f1 - f0) * u, b0 + (b1 - b0) * u
    return tab[-1][1], tab[-1][2], tab[-1][3]


def _jaw_dy(H, y):
    return H.jaw * 7.0 * (y - 30.0) / 38.0 if y > 30.0 else 0.0


def _hx(H, x0, y, dz=0.0):
    """Project a face-surface point given in front-view coords (x0, y) (+ extra depth dz)
    -> (x, y, depth, fs) in head-local coords; fs = horizontal foreshortening factor."""
    a, zf, _ = _prof(y)
    u = clamp(x0 / max(a, 1e-3), -0.995, 0.995)
    z = zf * math.sqrt(1.0 - u * u) + dz
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    phi = math.asin(u)
    fs = clamp(math.cos(phi + H.th * 0.92) / max(math.cos(phi), 0.25), 0.1, 1.15)
    return x, y + H.nod_dy * (dep / 60.0), dep, fs


def _surf_az(H, phi_deg, y):
    """Point on the head surface at azimuth phi (0 = front centre, +90 = local +x side), level y.
    Returns (x, y, visibility); visibility > 0 when the surface faces the camera."""
    a, zf, zb = _prof(y)
    ph = phi_deg * D2R
    sp, cp = math.sin(ph), math.cos(ph)
    zz = zf if cp >= 0 else zb
    x0, z = a * sp, zz * cp
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    vis = (-H.s * sp / max(a, 1e-3) + H.c * cp / max(zz, 1e-3)) * 60.0
    return x, y + H.nod_dy * (dep / 60.0), vis


_PBUMP = [(-62, 0.0), (-42, 1.2), (-26, 3.8), (-17, 3.4), (-8, 0.8), (0, -0.3), (7, 1.4), (13, 3.0), (20, 2.2),
          (30, 0.6), (44, -0.6), (54, 0.2), (62, 0.8), (70, 0.0)]


def _bump_k(s):
    """How much of the brow-ridge / cheekbone profile shows (0 front view .. 1 from turn ~0.25)."""
    return min(1.0, abs(s) * 2.5)


def _profile_bump(y):
    """Small offsets that give the leading cheek edge brow-ridge / eye-socket / cheekbone shape."""
    tab = _PBUMP
    if y <= tab[0][0] or y >= tab[-1][0]:
        return 0.0
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, v0 = tab[i - 1]
            y1, v1 = tab[i]
            u = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * u
    return 0.0


_LIP_YS = (35.0, 39.0, 42.5, 46.5, 51.5, 57.5, 62.0)
_LIP_TAB = [(30.0, 0.0), (35.0, 0.5), (39.0, 2.3), (42.5, 1.0), (46.5, 2.1), (51.5, -0.7), (57.5, 1.9), (62.0, 0.9), (67.0, 0.0)]


def _lip_profile(y, H):
    """Leading-edge offset for the lips / chin in near-profile (head-local, y before the jaw drop)."""
    y -= _jaw_dy(H, y) * 0.5
    tab = _LIP_TAB
    if y <= tab[0][0] or y >= tab[-1][0]:
        return 0.0
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, v0 = tab[i - 1]
            y1, v1 = tab[i]
            u = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * smoothstep(u)
    return 0.0


def _head_outline(H, grow=0.0, gy=(18.0, 18.0), mext=None):
    """Head silhouette (head-local). grow > 0 inflates the upper head (hair volume); the inflation tapers to 0
    at y = gy[0] on the -x edge and gy[1] on the +x edge (where the hairline meets the silhouette)."""
    s, c = H.s, H.c
    R, L = [], []
    for y in _OUT_YS:
        a, zf, zb = _prof(y)
        gl = grow * smoothstep((gy[0] - y) / 26.0)
        gr = grow * smoothstep((gy[1] - y) / 26.0)
        if s >= 0:
            r = math.sqrt((a + gr) ** 2 * c * c + (zf + gr) ** 2 * s * s)
            l = -math.sqrt((a + gl) ** 2 * c * c + (zb + gl) ** 2 * s * s)
        else:
            r = math.sqrt((a + gr) ** 2 * c * c + (zb + gr) ** 2 * s * s)
            l = -math.sqrt((a + gl) ** 2 * c * c + (zf + gl) ** 2 * s * s)
        yy = y + _jaw_dy(H, y)
        if y > 40:
            yy += H.nod_dy * 0.55 * (y - 40) / 28.0
        bump = _profile_bump(y) * _bump_k(s)
        if s >= 0:
            r += bump
        else:
            l -= bump
        R.append((r, yy))
        L.append((l, yy))
    top = (0.0, -90.0 - grow)
    chin = (40.0 * s * 0.98, 67.0 + _jaw_dy(H, 67.0) + H.nod_dy * 0.6)
    nose_k = smoothstep((abs(s) - 0.45) / 0.3)
    lip_k = smoothstep((abs(s) - 0.42) / 0.28) if grow == 0.0 else 0.0
    if nose_k > 0 or lip_k > 0 or mext is not None:
        edge = R if s >= 0 else L
        sg = 1.0 if s >= 0 else -1.0
        new = list(edge)
        if nose_k > 0:
            # nose breaks the silhouette in near-profile views
            nd = H.nod_dy * 0.95
            for ny, dz in ((5.0, 0.0), (15.0, 4.0), (22.0, 9.5), (26.0, 6.0), (28.5, 0.0)):
                a_, zf_, _ = _prof(ny)
                ex = sg * math.sqrt(a_ * a_ * c * c + zf_ * zf_ * s * s)
                nx = sg * (zf_ + dz) * abs(s)
                px = ex + (nx - ex) * nose_k if sg * (nx - ex) > 0 else ex
                new.append((px, ny + nd))
        if lip_k > 0:
            # lips and chin shape the lower silhouette (upper lip, lower lip, chin dimple, chin)
            for ly in _LIP_YS:
                a_, zf_, _ = _prof(ly)
                ex = sg * (math.sqrt(a_ * a_ * c * c + zf_ * zf_ * s * s) + _profile_bump(ly) * _bump_k(s))
                yy = ly + _jaw_dy(H, ly) + (H.nod_dy * 0.55 * (ly - 40) / 28.0 if ly > 40 else 0.0)
                new.append((ex, yy))
            new = [(x + sg * lip_k * _lip_profile(y, H), y) if 30.0 < y < 70.0 else (x, y) for x, y in new]
        if mext is not None:
            # never clip the mouth: the silhouette bulges just enough to hold the lips
            mx, my0, my1 = mext
            out = []
            for x, y in new:
                w = smoothstep((y - (my0 - 6.0)) / 6.0) * smoothstep(((my1 + 6.0) - y) / 6.0)
                need = sg * mx + 1.8
                if w > 0 and sg * x < need:
                    x = sg * lerp(sg * x, need, w)
                out.append((x, y))
            new = out
        new.sort(key=lambda q: q[1])
        if s >= 0:
            R = new
        else:
            L = new
    pts = [top] + R[1:] + [chin] + L[1:][::-1]
    return smooth_path(pts, closed=True)


def _sil_x(H, y, side):
    """x of the head silhouette at head-local level y on the +x (side=+1) or -x (side=-1) edge,
    including the brow-ridge / cheekbone bumps on the leading edge (same maths as _head_outline)."""
    a, zf, zb = _prof(y)
    s, c = H.s, H.c
    lead = (s >= 0) == (side > 0)
    z = zf if lead else zb
    x = math.sqrt(a * a * c * c + z * z * s * s)
    if lead:
        x += _profile_bump(y) * _bump_k(s)
    return side * x


# hairline loop on the head surface: (azimuth deg, y)
_HAIRLINE = [(0, -52.0), (14, -51.0), (28, -47.0), (42, -39.0), (54, -29.0), (64, -18.0), (73, -7.0),
             (80, 4.0), (86, 5.0), (91, -5.0), (97, -10.0), (104, -6.0), (114, 6.0), (130, 20.0),
             (150, 28.0), (180, 31.0)]


def _hairline_y(phi):
    """Catmull-Rom interpolation of the (symmetric) hairline table."""
    a = abs(phi)
    tab = _HAIRLINE
    n = len(tab)
    for i in range(1, n):
        if a <= tab[i][0]:
            p0, y1 = tab[i - 1]
            p1, y2 = tab[i]
            y0 = tab[i - 2][1] if i >= 2 else tab[1][1]
            y3 = tab[i + 1][1] if i + 1 < n else y2
            u = (a - p0) / (p1 - p0)
            u2, u3 = u * u, u * u * u
            return 0.5 * ((2 * y1) + (-y0 + y2) * u + (2 * y0 - 5 * y1 + 4 * y2 - y3) * u2 + (-y0 + 3 * y1 - 3 * y2 + y3) * u3)
    return tab[-1][1]


def _hair_region(H):
    """Polygon covering everything above the visible part of the hairline (clip with the head)."""
    samp = []
    start = -H.th / D2R + 180.0          # start opposite the view direction so the visible run is contiguous
    for i in range(91):
        ph = start + i * 4.0
        ph = (ph + 180.0) % 360.0 - 180.0
        samp.append(_surf_az(H, ph, _hairline_y(ph)))
    idx = [i for i, sm in enumerate(samp) if sm[2] > 0]
    if not idx:
        return None, None
    i0, i1 = idx[0], idx[-1]
    pts = [(samp[i][0], samp[i][1]) for i in range(i0, i1 + 1)]

    def cross(ia, ib):
        va, vb = samp[ia][2], samp[ib][2]
        u = va / (va - vb) if va != vb else 0.5
        return (lerp(samp[ia][0], samp[ib][0], u), lerp(samp[ia][1], samp[ib][1], u))
    if i0 > 0:
        pts.insert(0, cross(i0, i0 - 1))
    if i1 < len(samp) - 1:
        pts.append(cross(i1, i1 + 1))
    xl, yl = pts[0]
    xr, yr = pts[-1]
    path = skia.Path()
    _cr(path, pts)
    path.lineTo(xr + 30, yr - 6)
    path.lineTo(xr + 40, -260)
    path.lineTo(xl - 40, -260)
    path.lineTo(xl - 30, yl - 6)
    path.close()
    return path, pts


def _toe_lift_h(phi):
    """Ankle height that keeps the shoe's lowest point on the floor with the heel lifted by phi degrees."""
    a = -phi * D2R
    ca_, sa_ = math.cos(a), math.sin(a)
    return -min(f_ * sa_ + v_ * ca_ for f_, v_ in _SHOE)


def _kneel_leg(hv_b, fa0, va0, ang0, k):
    """Leg on its way from its base pose (ankle fa0/va0, foot angle ang0, hip height hv_b) down onto the knee.
    The knee follows an eased path to the floor (touching at KNEEL_TOUCH) while the foot pivots onto its toes
    (heel lifting <= KNEEL_HEEL) and slides back; the hip height follows from the rigid thigh.
    Returns (ankle f, ankle v, foot angle, hip height)."""
    fwd = (lambda j1, j2: j1 if j1[0] >= j2[0] else j2)
    k0 = _ik((0.0, hv_b), (fa0, va0), THIGH, SHIN, fwd)
    k1f = math.sqrt(THIGH * THIGH - (KNEEL_HIP - KNEE_R) ** 2)
    ktf = k1f + 6.0
    if k < KNEEL_TOUCH:
        u = k / KNEEL_TOUCH
        e = smoothstep(u)
        kf = lerp(k0[0], ktf, e) + 16.0 * math.sin(math.pi * u) * (1.0 - min(1.0, k0[0] / 100.0))
        kv = lerp(k0[1], KNEE_R, u * u * (1.6 - 0.6 * u))        # slow start, settles onto the floor
        phi = lerp(-ang0, KNEEL_HEEL, smoothstep(u / 0.75))
    else:
        u = (k - KNEEL_TOUCH) / (1.0 - KNEEL_TOUCH)
        kf = lerp(ktf, k1f, smoothstep(u))
        kv = KNEE_R
        phi = KNEEL_HEEL
    kf = min(kf, THIGH - 0.5)
    hv = kv + math.sqrt(THIGH * THIGH - kf * kf)
    av = _toe_lift_h(phi)
    dv = kv - av
    af = kf - math.sqrt(max(0.0, SHIN * SHIN - dv * dv))
    if dv > SHIN:            # (only possible right at the start) the toe cannot reach: keep the shin vertical
        av = kv - SHIN
    w = smoothstep(k / 0.14)     # leave the base pose smoothly
    return lerp(fa0, af, w), lerp(va0, av, w), lerp(ang0, -phi, w), hv


# --------------------------------------------------------------------------- pose solving
def _solve(p: Pose, t):
    R = _NS()
    fac = 1.0 if p.facing >= 0 else -1.0
    R.fac = fac
    back = p.back > 0.5
    R.back = back
    turn = clamp(p.turn, -0.45, 0.85)
    R.turn = turn
    th = turn * TURN_DEG * D2R
    if back:
        th = math.pi - th
    R.th, R.s, R.c = th, math.sin(th), math.cos(th)
    br = p.breath if p.breath is not None else (breathe(t, 0.2, 2) if t is not None else 0.0)
    R.br = br
    k = clamp(p.kneel)
    sw = clamp(p.sit) * (1.0 - k)
    stw = max(0.0, 1.0 - sw - k)
    R.k, R.sw, R.stw = k, sw, stw
    seat_h = (p.y - p.seat_y) / max(p.scale, 1e-4)
    walking = p.walk is not None
    ph = (p.walk or 0.0)
    R.walking, R.ph = walking, ph
    bob = WALK_BOB * (0.5 - 0.5 * math.cos(4 * math.pi * ph)) if walking else 0.0
    hv_st = HIP_H - (6.0 if walking else 0.0) + bob
    sb = clamp(p.sit)
    hv_b = (1.0 - sb) * hv_st + sb * (seat_h + SEAT_OFF)       # hip height before kneeling
    s = R.s

    # ---------------- legs (side plane f = forward, v = up; projected with the body turn)
    th_leg = th
    if not back:
        tgt = (52.0 * (sw + k) + (68.0 * stw if walking else 0.0)) / max(1e-6, sw + k + (stw if walking else 0.0))
        th_leg = lerp(th, max(th, tgt * D2R), clamp(sw + k + (stw if walking else 0.0)) * smoothstep((turn - 0.04) / 0.26))
    R.sl, R.cl = math.sin(th_leg), math.cos(th_leg)
    sl_, cl_ = R.sl, R.cl
    tap = 0.0
    if p.foot_tap > 0 and t is not None:
        tap = p.foot_tap * 21.0 * max(0.0, math.sin(2 * math.pi * 2.5 * t)) ** 0.7
    fwd = (lambda j1, j2: j1 if j1[0] >= j2[0] else j2)
    sol = {}
    for o in (-1, 1):
        if walking:
            lp = (ph + (0.0 if o < 0 else 0.5)) % 1.0
            if lp < 0.5:
                f_w, lift, toe = lerp(STRIDE, -STRIDE, lp / 0.5), 0.0, 0.0
            else:
                q = (lp - 0.5) / 0.5
                f_w = lerp(-STRIDE, STRIDE, smoothstep(q))
                lift = math.sin(math.pi * q) * LIFT
                toe = -14.0 * math.sin(math.pi * min(1.0, q * 1.6))
        else:
            f_w, lift, toe = 0.0, 0.0, 0.0
        fa = (1.0 - sb) * f_w + sb * SIT_FOOT
        va = (1.0 - sb) * (ANKLE_H + lift) + sb * ANKLE_H
        ang = (1.0 - sb) * toe
        if k > 0:
            fa, va, ang, hvk = _kneel_leg(hv_b, fa, va, ang, k)
        else:
            hvk = hv_b
        sol[o] = [fa, va, ang, hvk]
    hv = 0.5 * (sol[-1][3] + sol[1][3]) - p.bounce
    R.hv = hv
    legs = {}
    for o in (-1, 1):
        L = _NS()
        fa, va, ang, _ = sol[o]
        kn = _ik((0.0, hv), (fa, va), THIGH, SHIN, fwd)
        if k > 0 and kn[1] < KNEE_R:
            # knee on the floor (e.g. a sob bounce while kneeling): keep it there, the shin slides back
            dv = hv - KNEE_R
            kn = (math.sqrt(max(0.0, THIGH * THIGH - dv * dv)), KNEE_R)
            ux, uy = _norm(fa - kn[0], va - kn[1])
            fa, va = kn[0] + ux * SHIN, max(va, kn[1] + uy * SHIN)
        lat_h = o * HIP_LAT
        lat_k = o * (stw * 24.0 + sw * 31.0 + k * 27.0)
        lat_a = o * (stw * 21.0 + sw * 28.0 + k * 26.0)
        L.hip = (lat_h * cl_, -hv)
        L.knee = (lat_k * cl_ + kn[0] * sl_, -kn[1])
        L.ankle = (lat_a * cl_ + fa * sl_, -va)
        L.foot_ang = ang
        L.tap = tap if o < 0 else 0.0
        L.o = o
        legs[o] = L
    R.legs = legs
    lean = p.lean + (WALK_LEAN if walking else 0.0) * stw
    R.lean = lean
    MU = skia.Matrix()
    MU.preTranslate(0.0, -hv)
    MU.preRotate(lean)
    R.MU = MU
    su = clamp(p.shoulders_up)
    R.su = su

    # ---------------- head
    H = _NS()
    tt = clamp(turn + p.head_turn, -0.6, 0.9)
    H.th = tt * TURN_DEG * D2R
    if back:
        H.th = math.pi - H.th
    H.s, H.c = math.sin(H.th), math.cos(H.th)
    H.nod = clamp(p.head_nod, -1.0, 1.0)
    H.nod_dy = -H.nod * 13.0      # features slide up (chin up) / down on the head sphere
    H.jaw = clamp(p.mouth_open) * (1.0 - 0.3 * clamp(p.mouth_round))
    MHr = skia.Matrix()        # head frame relative to the upper-body frame
    # chin down also drops the head a little so the jaw tucks over the collar
    MHr.preTranslate(4.0 * s, NECK_PIVOT - br * 1.1 + su * 2.0 + max(0.0, -H.nod) * 5.0)
    # nod pitches the head about the neck pivot (visible as a rotation in 3/4 views) ...
    MHr.preRotate(p.head_tilt - H.nod * 14.0 * H.s)
    # ... and foreshortens the face vertically when seen from the front
    MHr.preScale(HEAD_S, HEAD_S * HEAD_SY * (1.0 - 0.07 * abs(H.nod) * abs(H.c)))
    MHr.preTranslate(0.0, -PIVOT_HL)
    R.MHr = MHr
    R.MH = skia.Matrix.Concat(MU, MHr)
    R.H = H
    face_x = MHr.mapXY(_hx(H, 0.0, 30.0)[0], 30.0).fX
    R.face_x = face_x
    R.turn_k = smoothstep((turn - 0.02) / 0.23)

    # ---------------- arms (upper-body frame)
    R.sw_amp = WALK_SWING * stw if walking else 0.0
    arms = {}
    for o in (-1, 1):
        A = _NS()
        A.on_leg = 0.0
        side = "r" if o < 0 else "l"       # facing=-1 is a pure mirror (same as Quill's rig)
        A.side = side
        ap = p.arm_r if side == "r" else p.arm_l
        A.ap = ap
        A.o = o
        fk = _arm_fk(R, o, ap)
        tgt, moved = _arm_target(R, o, ap, fk)
        if o > 0 and not back:
            # the far arm reaches the same body feature on its own side as the near arm would on the near side:
            # face / chest touches (across) are mirrored across the midline, knee / thigh rests follow the legs
            fk_n = _arm_fk(R, -1, ap)
            tgt_n, mv_n = _arm_target(R, -1, ap, fk_n)
            wm = smoothstep((ap.across - 0.18) / 0.17) * (1.0 - clamp(ap.behind * 2.0))
            if wm > 0:
                # palm of the near-arm equivalent -> same height, mirrored lateral position on the face / chest
                An = _NS()
                An.ap = ap
                _arm_finish(R, An, fk_n, tgt_n if mv_n else None)
                lat = (1.0 - 2.0 * ap.across)
                sp = _surface_point(R, lat, An.palm[1])
                _arm_finish(R, A, fk, tgt if moved else None)
                goal = (lerp(A.palm[0], sp[0], wm), lerp(A.palm[1], sp[1], wm))
                for _ in range(2):
                    hd = A.hd
                    _arm_finish(R, A, fk, (goal[0] - hd[0] * 15.0 * HAND_S, goal[1] - hd[1] * 15.0 * HAND_S))
                tgt = A.W
                moved = True
            wk = (1.0 - wm) * (1.0 - clamp(ap.behind * 2.0))
            if wk > 0 and (R.sw + R.k) > 0.05:
                km = _knee_magnet(R, tgt_n)
                if km is not None:
                    wkm, delta = km
                    wkm *= wk
                    A.on_leg = wkm
                    if wkm > 0.001:
                        tgt = (lerp(tgt[0], tgt_n[0] + delta[0], wkm), lerp(tgt[1], tgt_n[1] + delta[1], wkm))
                        moved = True
        _arm_finish(R, A, fk, tgt if moved else None)
        A.front_w = 0.0
        if ap.behind > 0.5:
            A.layer = "behind"
        elif o < 0:
            A.layer = "front"
        elif ap.across >= 0.25:
            A.layer = "over"
        else:
            A.layer = "back"
            if not back:
                # near the front view the far arm hangs beside the body like the near one: cross-fade it to the front
                A.front_w = 1.0 - smoothstep((abs(turn) - 0.06) / 0.08)
        A.hand = ap.hand
        arms[o] = A
    R.arms = arms

    MS = skia.Matrix()
    MS.preTranslate(p.x, p.y)
    MS.preScale(fac * p.scale, p.scale)
    R.MS = MS

    # ---------------- mug (upper-body frame). Near hand (the arm nearer the camera): the hand is in front of the
    # mug, its back / outer edge toward the camera, the fingers wrapping round the far side of the body (they
    # vanish round its far silhouette edge), the thumb lying along the near face. Far hand: the palm wraps the
    # back of the mug body, which sits in front of the hand, centred just past the palm; the fingers come round
    # through the handle (outer, +x side) and the thumb rests on top of the handle. Either way the wrist keeps
    # the forearm line (no cocked-back wrist).
    R.mug = None
    if p.mug in ("l", "r"):
        A = arms[-1] if arms[-1].side == p.mug else arms[1]
        near = A.o < 0 and not back
        hs = 1.0
        mouth = MHr.mapXY(_hx(H, 0.0, MOUTH_Y)[0], MOUTH_Y)
        dist = math.hypot(A.palm[0] - (mouth.fX + 30.0), A.palm[1] - mouth.fY)
        w = 1.0 - smoothstep((dist - 26.0) / 52.0)                  # how much this is a sip
        ang = -MUG_TILT * smoothstep(w)
        a = ang * D2R
        ca_, sa_ = math.cos(a), math.sin(a)

        def rot(v):
            return (v[0] * ca_ - v[1] * sa_, v[0] * sa_ + v[1] * ca_)
        if w > 0.001:
            # sip: put the rim's face-side edge on the lower lip
            cx_, _, _, _ = _hx(H, -4.0, MOUTH_Y + 3.0)
            C = MHr.mapXY(cx_, MOUTH_Y + 3.0)
            Kc = (-(MUG_W - 1.0) * MUG_S, -MUG_H * MUG_S)
            palm0 = A.palm
            for _ in range(7 if near else 3):         # the near grip moves more with the hand angle: more passes
                G = _mug_grip(A.hd, a, near)
                off = rot((G[0] - Kc[0], G[1] - Kc[1]))
                goal = (lerp(palm0[0], C.fX + off[0], w), lerp(palm0[1], C.fY + off[1], w))
                hd = A.hd
                _arm_finish(R, A, A.fk, (goal[0] - hd[0] * 15.0 * HAND_S, goal[1] - hd[1] * 15.0 * HAND_S))
        G = _mug_grip(A.hd, a, near)                                # palm centre in mug-local coords
        g = rot(G)
        M = _NS()
        M.x = A.palm[0] - g[0]
        M.y = A.palm[1] - g[1]
        M.ang = ang
        M.hs = hs
        M.flip = hs < 0
        M.arm = A
        M.near = near                  # hand in front of the mug (near arm) / behind it (far arm)
        M.tilt = w
        M.dist = dist                  # raw palm -> mouth distance (QA probes)
        R.mug = M
    return R


# --------------------------------------------------------------------------- arm solving helpers
def _mug_hw(y):
    """Half-width (base units) of the mug body at base-unit height y (<= 0); straight sides."""
    return MUG_W


def _mug_grip(hd, a, near=False):
    """Palm centre of the holding hand in mug-local coords (mug rotated by `a` radians, scaled units, bottom
    centre at the origin). Far hand: the mug body sits in front of the hand, centred on the hand's line just past
    the palm, its near edge MUG_HEEL past the wrist whatever the hand direction (rounded-box support distance).
    Near hand (near=True): the hand lies over the front of the body; its knuckle line sits MUG_NEAR_FING short
    of the far silhouette edge (the side the hand points to), where the fingers wrap round at MUG_NEAR_Y of the
    body height."""
    ca_, sa_ = math.cos(a), math.sin(a)
    hx_, hy_ = hd[0] * ca_ + hd[1] * sa_, -hd[0] * sa_ + hd[1] * ca_
    if near:
        ye = -(MUG_NEAR_Y + 0.25 * max(0.0, hy_)) * MUG_BODY_H     # a hand coming down from above grips higher
        ex = clamp(hx_ / 0.3, -1.0, 1.0) * _mug_hw(ye) * MUG_S
        dk = MUG_NEAR_FING + (MUG_NEAR_KY - 15.0) * HAND_S
        return (ex - hx_ * dk, ye * MUG_S - hy_ * dk)
    bx, by = MUG_W * MUG_S, MUG_H * MUG_S * 0.5
    e = 0.5 * (abs(hx_) * bx + abs(hy_) * by + math.hypot(hx_ * bx, hy_ * by))
    dl = e + MUG_HEEL - 15.0 * HAND_S
    return (-hx_ * dl, -by - hy_ * dl)


def _arm_fk(R, o, ap):
    """Forward kinematics of arm `o` (-1 near / +1 far) in the upper-body frame."""
    F = _NS()
    s, c = R.s, R.c
    S = (o * SH_A * c - 3.0 * s, SH_Y - R.su * 12.0 - R.br * 1.1)
    tk = R.turn_k
    # front view: hanging segments swing slightly outward, segments raised forward come toward the camera
    # (foreshortened, slightly inward); upper arm and forearm each by their own elevation
    d1 = lerp(o * lerp(0.15, -0.3, smoothstep((ap.shoulder - 15.0) / 45.0)), 1.0, tk)
    d2 = lerp(o * lerp(0.15, -0.3, smoothstep((ap.shoulder + ap.elbow - 25.0) / 45.0)), 1.0, tk)
    if ap.across < 0:
        sp = min(1.0, -ap.across * (1.0 + 3.0 * (1.0 - tk)))
        d1, d2 = lerp(d1, float(o), sp), lerp(d2, float(o), sp)
    d = d2
    swing = -o * R.sw_amp * math.cos(2 * math.pi * R.ph) * (1.0 - clamp(ap.across * 2.0))
    a1 = (ap.shoulder + swing) * D2R
    a2 = a1 + ap.elbow * D2R
    v1 = (math.sin(a1) * d1, math.cos(a1))
    v2 = (math.sin(a2) * d2, math.cos(a2))
    fl1, fl2 = math.hypot(*v1), math.hypot(*v2)
    if fl1 < 0.5:
        v1 = _norm(v1[0] - 1e-4 * o, v1[1])
        v1, fl1 = (v1[0] * 0.5, v1[1] * 0.5), 0.5
    if fl2 < 0.5:
        v2 = _norm(v2[0] - 1e-4 * o, v2[1])
        v2, fl2 = (v2[0] * 0.5, v2[1] * 0.5), 0.5
    F.S = S
    F.l1, F.l2 = UPPER * fl1, FORE * fl2
    F.E = (S[0] + v1[0] * UPPER, S[1] + v1[1] * UPPER)
    F.W = (F.E[0] + v2[0] * FORE, F.E[1] + v2[1] * FORE)
    flex = _norm(math.cos(a2) * d, -math.sin(a2))
    if flex == (0.0, 0.0):
        flex = (1.0, 0.0)
    F.flex = flex
    F.v2n = _norm(*v2)
    F.rot_sense = 1.0 if _cross(F.v2n, flex) >= 0 else -1.0
    return F


def _mid_x(R, y):
    """Projected body midline (front surface) at upper-body-frame height y: chest -> face."""
    return lerp(30.0 * R.s, R.face_x, smoothstep((SH_Y + 10.0 - y) / 45.0))


def _arm_target(R, o, ap, F):
    """Hand (wrist) target for across / behind; returns ((x, y), moved)."""
    tx, ty = F.W
    moved = False
    if ap.across > 0:
        opp_x = -o * SH_A * R.c * 0.92 + 30.0 * R.s
        mid_x = _mid_x(R, F.W[1])
        if ap.across <= 0.5:
            tx = lerp(F.W[0], mid_x, ap.across * 2.0)
        else:
            tx = lerp(mid_x, opp_x, (ap.across - 0.5) * 2.0)
        moved = True
    if ap.behind > 0:
        tx = lerp(tx, -24.0 * R.s - 6.0 * o * R.c, ap.behind)
        ty = lerp(ty, -40.0, ap.behind * 0.6)
        moved = True
    return (tx, ty), moved


def _surface_point(R, lat, y):
    """Upper-body-frame point on the front of the chest / face at height y, at lateral position
    lat (-1 near edge .. 0 midline .. +1 far side; on the face +-0.5 are the eyes), a hand's thickness out."""
    s, c = R.s, R.c
    lc = clamp(lat, -1.0, 1.0) * 50.0
    xc = lc * c + (32.0 * math.sqrt(max(0.0, 1.0 - (lc / 54.0) ** 2)) + 6.0) * s
    wf = smoothstep((SH_Y + 10.0 - y) / 45.0)
    if wf <= 0:
        return (xc, y)
    inv = skia.Matrix()
    if not R.MHr.invert(inv):
        return (xc, y)
    q = inv.mapXY(R.face_x, y)
    hy = clamp(q.fY, -60.0, 64.0)
    hx, hyy, _, _ = _hx(R.H, clamp(lat, -1.0, 1.0) * 2.0 * EX, hy, 5.0)
    m = R.MHr.mapXY(hx, hyy)
    return (lerp(xc, m.fX, wf), y)


def _knee_magnet(R, T):
    """If the (near-arm-equivalent) hand target T rests on the near leg, return (weight, delta) mapping it to
    the same spot on the far leg. Coordinates: upper-body frame."""
    inv = skia.Matrix()
    if not R.MU.invert(inv):
        return None
    Ln, Lf = R.legs[-1], R.legs[1]
    segs_n = [(Ln.hip, Ln.knee), (Ln.knee, Ln.ankle)]
    segs_f = [(Lf.hip, Lf.knee), (Lf.knee, Lf.ankle)]
    best = None
    for (a, b), (af, bf) in zip(segs_n, segs_f):
        pa, pb = inv.mapXY(*a), inv.mapXY(*b)
        pa, pb = (pa.fX, pa.fY), (pb.fX, pb.fY)
        dx, dy = pb[0] - pa[0], pb[1] - pa[1]
        L2 = dx * dx + dy * dy
        u = clamp(((T[0] - pa[0]) * dx + (T[1] - pa[1]) * dy) / max(L2, 1e-6))
        px, py = pa[0] + dx * u, pa[1] + dy * u
        dist = math.hypot(T[0] - px, T[1] - py)
        if best is None or dist < best[0]:
            qa, qb = inv.mapXY(*af), inv.mapXY(*bf)
            fx_, fy_ = qa.fX + (qb.fX - qa.fX) * u, qa.fY + (qb.fY - qa.fY) * u
            best = (dist, (fx_ - px, fy_ - py))
    dist, delta = best
    w = 1.0 - smoothstep((dist - 22.0) / 40.0)
    return w, delta


def _arm_finish(R, A, F, target):
    """Solve the elbow for a wrist target (or keep the FK pose) and set the hand frame on A."""
    S, E, W = F.S, F.E, F.W
    v2n, flex = F.v2n, F.flex
    if target is not None:
        Efk = F.E

        def pref(j1, j2, Efk=Efk):
            d1 = (j1[0] - Efk[0]) ** 2 + (j1[1] - Efk[1]) ** 2
            d2 = (j2[0] - Efk[0]) ** 2 + (j2[1] - Efk[1]) ** 2
            return j1 if d1 <= d2 else j2
        E = _ik(S, target, F.l1, F.l2, pref)
        dx, dy = target[0] - E[0], target[1] - E[1]
        dd = math.hypot(dx, dy)
        v2n = _norm(dx, dy)
        W = (E[0] + v2n[0] * min(dd, F.l2), E[1] + v2n[1] * min(dd, F.l2))
        flex = (-v2n[1] * F.rot_sense, v2n[0] * F.rot_sense)
    A.fk = F
    A.S, A.E, A.W = S, E, W
    wa = A.ap.wrist * D2R
    hd = _norm(v2n[0] * math.cos(wa) + flex[0] * math.sin(wa), v2n[1] * math.cos(wa) + flex[1] * math.sin(wa))
    fx = (-hd[1], hd[0])
    if fx[0] * flex[0] + fx[1] * flex[1] < 0:
        fx = (hd[1], -hd[0])
    A.hd, A.fx = hd, fx
    A.palm = (W[0] + hd[0] * 15.0 * HAND_S, W[1] + hd[1] * 15.0 * HAND_S)



# --------------------------------------------------------------------------- public queries
def blink(t, seed=11):
    """Rae's natural blink at time t (1 open .. 0 closed; irregular ~3.7 s rhythm). This is exactly what
    draw() uses when lid_l / lid_r is None. Scenes that hold an explicit lid level for a long time should
    write  lid = level * R.blink(t)  so she keeps blinking (or use expr(..., t=t))."""
    return auto_blink(t, seed=seed, rate=3.7) if t is not None else 1.0


def _to_stage(R, pt):
    q = R.MS.mapXY(pt.fX, pt.fY) if isinstance(pt, skia.Point) else R.MS.mapXY(pt[0], pt[1])
    return (q.fX, q.fY)


def head_center(pose: Pose, t=None):
    """Stage coords of the point between the eyes. Pass the same `t` as draw() to include the automatic
    breathing motion (only matters when pose.breath is None; ~1 unit)."""
    R = _solve(pose, t)
    x, y, _, _ = _hx(R.H, 0.0, 0.0)
    return _to_stage(R, R.MH.mapXY(x, y))


def mouth_pos(pose: Pose, t=None):
    """Stage coords of the centre of the mouth."""
    R = _solve(pose, t)
    x, y, _, _ = _hx(R.H, 0.0, MOUTH_Y)
    return _to_stage(R, R.MH.mapXY(x, y))


def eye_pos(pose: Pose, side: str, t=None):
    """Stage coords of the centre of Rae's 'l' or 'r' eye."""
    R = _solve(pose, t)
    slot = -1 if side == "r" else 1
    x, y, _, _ = _hx(R.H, slot * EX, 0.0)
    return _to_stage(R, R.MH.mapXY(x, y))


def hand_pos(pose: Pose, side: str, t=None):
    """Stage coords of the palm centre of Rae's 'l' or 'r' hand."""
    R = _solve(pose, t)
    A = R.arms[-1] if R.arms[-1].side == side else R.arms[1]
    return _to_stage(R, R.MU.mapXY(*A.palm))


def mug_pose(pose: Pose, t=None):
    """(x, y, scale, angle, flip) of the held mug in stage coords (bottom centre), or None.
    draw_mug(canvas, *mug_pose(pose, t)) reproduces the in-hand mug exactly."""
    R = _solve(pose, t)
    if R.mug is None:
        return None
    x, y = _to_stage(R, R.MU.mapXY(R.mug.x, R.mug.y))
    ang = (R.mug.ang + R.lean) * R.fac
    flip = R.mug.flip if R.fac > 0 else (not R.mug.flip)
    return (x, y, pose.scale, ang, flip)


def walk_advance(pose: Pose) -> float:
    """Stage units the pelvis must travel (toward `facing`) per walk cycle so the planted foot does not
    skate: 4 * STRIDE * sin(leg yaw) * scale. = WALK_ADVANCE at turn >= 0.3, scale 1. Walking backward
    works by decreasing pose.walk while moving pose.x the other way."""
    R = _solve(pose.copy(walk=0.0, sit=0.0, kneel=0.0), None)
    return 4.0 * STRIDE * R.sl * pose.scale


# --------------------------------------------------------------------------- mug
def _mug_handle_path():
    w = MUG_W
    hp = skia.Path()
    _cr(hp, [(w - 1, -26.5), (w + 8.0, -26.0), (w + 10.8, -17.0), (w + 7.4, -9.0), (w - 1, -8.0)])
    return hp


def _mug_body_path():
    w, h = MUG_W, MUG_H
    body = skia.Path()
    _cr(body, [(-w, -h), (-w, -12.0), (-w + 0.6, -3.0), (-w + 4.0, 0.0)])
    _cr(body, [(w - 4.0, 0.0), (w - 0.6, -3.0), (w, -12.0), (w, -h)], move=False)
    body.close()
    return body


def _mug_local(c, flip=False, handle=True):
    """Mug in its own frame: bottom centre at origin, MUG_H*MUG_S tall, handle on +x (or -x if flip)."""
    c.scale(-MUG_S if flip else MUG_S, MUG_S)
    w, h = MUG_W, MUG_H
    if handle:
        hp = _mug_handle_path()
        _stroke(c, hp, C_MUG_LINE, 6.4)
        _stroke(c, hp, C_MUG, 4.3)
        _stroke(c, _curve([(w + 4.0, -25.0), (w + 8.6, -22.0), (w + 9.2, -16.0)]), WHITE, 1.1, 0.6)
    body = _mug_body_path()
    _fill(c, body, C_MUG_SH)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.translate(-4.5, 0)
    _fill(c, body, C_MUG)
    c.restore()
    lx, ly = -2.0, -15.5        # logo sits a little away from the handle (flip is a pure mirror)
    c.drawCircle(lx, ly, 6.4, paint(C_LOGO, stroke=1.35))
    hp2 = skia.Path()
    hp2.moveTo(lx, ly + 3.7)
    hp2.cubicTo(lx - 5.3, ly - 0.4, lx - 3.0, ly - 4.7, lx, ly - 2.0)
    hp2.cubicTo(lx + 3.0, ly - 4.7, lx + 5.3, ly - 0.4, lx, ly + 3.7)
    hp2.close()
    _fill(c, hp2, C_LOGO)
    _stroke(c, body, C_MUG_LINE, 1.2, 0.9)
    rim = skia.Rect(-w, -h - 3.6, w, -h + 3.6)
    c.drawOval(rim, paint(C_MUG))
    c.drawOval(skia.Rect(-w + 2.0, -h - 2.2, w - 2.0, -h + 2.2), paint(C_COFFEE))
    c.drawOval(skia.Rect(-w + 4.0, -h - 1.2, -1.0, -h + 0.6), paint(WHITE, 0.18))
    c.drawOval(rim, paint(C_MUG_LINE, 0.9, stroke=1.1))
    c.drawRoundRect(skia.Rect(-w + 3.0, -h + 6.0, -w + 5.6, -6.0), 1.3, 1.3, paint(WHITE, 0.55))


def draw_mug(canvas, x, y, scale=1.0, angle=0.0, flip=False):
    """Rae's off-white mug (red heart-in-circle logo). (x, y) = bottom centre where it rests,
    `angle` degrees (rotation about the bottom centre), flip=True puts the handle on the left."""
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(angle)
    canvas.scale(scale, scale)
    _mug_local(canvas, flip)
    canvas.restore()


# --------------------------------------------------------------------------- hands
_HAND_CACHE = {}


def _hand_paths(shape):
    """[(path, kind)] in hand-local coords (wrist at 0,0, fingers toward +y, thumb toward +x)."""
    if shape in _HAND_CACHE:
        return _HAND_CACHE[shape]
    out = []
    if shape in ("relaxed", "hold"):
        main = smooth_path([(-7.2, -1.0), (-8.8, 8.5), (-9.2, 17.5), (-8.2, 26.0), (-5.2, 32.0), (-0.6, 34.6),
                            (3.4, 33.4), (5.0, 29.0), (5.4, 23.5), (7.2, 16.0), (8.4, 8.0), (7.4, 0.0)])
        out.append((main, "skin"))
        out.append((_curve([(-4.0, 20.5), (-3.8, 26.0), (-2.6, 31.0)]), "crease"))
        out.append((_curve([(0.0, 21.0), (0.4, 26.0), (1.6, 30.5)]), "crease"))
        out.append((skia.Simplify(_capsule(skia.Path(), (6.6, 8.0), (8.4, 20.5), 3.7, 2.9)), "skin"))
    elif shape in ("fist", "point"):
        main = smooth_path([(-7.6, -1.0), (-9.4, 9.0), (-9.6, 18.0), (-7.6, 24.6), (-2.0, 27.2), (4.4, 26.6),
                            (9.0, 21.5), (9.8, 12.0), (8.4, 2.0), (5.0, -1.6)])
        out.append((main, "skin"))
        out.append((_curve([(-8.0, 17.6), (-1.0, 19.6), (6.5, 18.6)]), "crease"))
        out.append((_curve([(-3.2, 19.4), (-2.9, 25.6)]), "crease"))
        out.append((_curve([(1.6, 19.6), (1.9, 26.0)]), "crease"))
        if shape == "point":
            out.append((skia.Simplify(_capsule(skia.Path(), (5.4, 18.0), (6.0, 40.0), 3.4, 2.8)), "skin"))
            out.append((_curve([(3.8, 28.5), (6.0, 29.5), (8.2, 28.8)]), "crease"))
        out.append((skia.Simplify(_capsule(skia.Path(), (8.8, 6.0), (4.2, 16.0), 3.9, 3.3)), "skin"))
    elif shape in ("open", "palm_out"):
        spread = 1.0 if shape == "open" else 1.5
        path = smooth_path([(-7.6, -1.0), (-9.4, 8.0), (-9.6, 16.5), (-4.0, 18.6), (4.0, 18.8), (9.0, 15.8),
                            (8.8, 5.0), (5.4, -1.6)])
        for fxp, ln, ang in ((-7.0, 13.0, -12.0), (-2.5, 16.5, -4.0), (2.1, 17.5, 3.0), (6.4, 15.5, 9.0)):
            a = ang * spread * D2R
            b = (fxp, 15.0)
            e = (fxp + math.sin(a) * ln, 15.0 + math.cos(a) * ln)
            _capsule(path, b, e, 2.95, 2.5)
        out.append((skia.Simplify(path), "palm" if shape == "palm_out" else "skin"))
        ta = (50.0 if shape == "open" else 64.0) * D2R
        out.append((skia.Simplify(_capsule(skia.Path(), (7.2, 4.5),
                                           (7.2 + math.sin(ta) * 13.5, 4.5 + math.cos(ta) * 13.5), 3.7, 3.0)), "skin"))
        if shape == "palm_out":
            out.append((_curve([(-6.5, 11.0), (0.0, 8.5), (6.0, 11.5)]), "crease"))
            out.append((_curve([(3.6, 1.5), (1.4, 7.0), (2.2, 13.0)]), "crease"))
        else:
            for x in (-4.6, -0.1, 4.3):
                out.append((_curve([(x, 9.0), (x + 0.3, 14.0)]), "crease"))
    elif shape == "palm_up":
        # open palm turned up toward the viewer: cupped, fingers together with a slight curl, thumb out
        path = smooth_path([(-6.6, -1.0), (-8.2, 8.0), (-8.4, 15.6), (-3.6, 18.4), (3.4, 18.6), (7.6, 15.6),
                            (7.6, 5.0), (4.8, -1.6)])
        for fxp, ln, ang in ((-5.7, 11.8, -7.0), (-2.0, 14.6, -2.5), (1.8, 15.2, 2.0), (5.3, 12.8, 7.0)):
            a = ang * D2R
            b0 = (fxp, 14.5)
            m = (fxp + math.sin(a) * ln * 0.6, 14.5 + math.cos(a) * ln * 0.6)
            e = (m[0] + math.sin(a + 0.35) * ln * 0.42, m[1] + math.cos(a + 0.35) * ln * 0.42)
            _capsule(path, b0, m, 2.75, 2.5)
            _capsule(path, m, e, 2.5, 2.15)
        out.append((skia.Simplify(path), "palm"))
        out.append((skia.Simplify(_capsule(skia.Path(), (6.8, 4.0), (6.8 + math.sin(56 * D2R) * 12.5, 4.0 + math.cos(56 * D2R) * 12.5),
                                           3.6, 2.9)), "skin"))
        out.append((_curve([(-6.2, 10.6), (-0.5, 8.4), (5.6, 10.4)]), "crease"))
        out.append((_curve([(3.4, 1.8), (1.2, 7.2), (1.9, 12.6)]), "crease"))
        out.append((_curve([(-6.8, 14.4), (-1.0, 13.0), (5.0, 14.2)]), "crease"))
        for fxp in (-5.4, -1.9, 1.9, 5.4):
            out.append((_curve([(fxp - 1.3, 22.6), (fxp, 23.1), (fxp + 1.3, 22.7)]), "crease"))
    else:
        return _hand_paths("relaxed")
    _HAND_CACHE[shape] = out
    return out


def _draw_hand(c, A):
    W, hd, fx = A.W, A.hd, A.fx
    m = skia.Matrix.MakeAll(fx[0], hd[0], W[0], fx[1], hd[1], W[1], 0, 0, 1)
    c.save()
    c.concat(m)
    c.scale(HAND_S, HAND_S)
    for path, kind in _hand_paths(A.hand):
        if kind == "crease":
            _stroke(c, path, C_SKIN_SH, 1.1, 0.8)
        elif kind == "palmline":
            _stroke(c, path, C_PALM, 2.6, 0.9)
        else:
            base = C_PALM if kind == "palm" else C_SKIN
            _cel(c, path, base, C_SKIN_SH, -2.2, -1.4, line=C_SKIN_LINE, line_w=1.25, line_a=0.8)
    c.restore()


def _grip_fingers(handle_side):
    """[(knuckle, tip, r_knuckle, r_tip)] of the fingers wrapped round the held mug, mug base units (handle on +x).
    handle_side: through the handle with the tips resting on the front of the body beside it (and the little
    finger curled under the handle); otherwise round the bare (-x) side of the body."""
    w = MUG_W
    if handle_side:
        return [((w + 4.0, -21.0), (w - 3.4, -21.4), 2.45, 2.2),
                ((w + 4.4, -16.3), (w - 4.2, -16.6), 2.55, 2.3),
                ((w + 4.0, -11.6), (w - 3.3, -11.7), 2.45, 2.2),
                ((w + 1.6, -6.3), (w - 2.6, -5.6), 2.05, 1.85)]
    return [((-w - 3.6, -24.2), (-w + 4.4, -24.6), 2.55, 2.25),
            ((-w - 3.9, -19.3), (-w + 5.0, -19.6), 2.65, 2.35),
            ((-w - 3.6, -14.4), (-w + 4.4, -14.5), 2.55, 2.25),
            ((-w - 2.8, -9.6), (-w + 3.4, -9.4), 2.2, 1.95)]


def _draw_grip_set(c, handle_side):
    fingers = _grip_fingers(handle_side)
    body = _mug_body_path()
    fp = skia.Path()
    for kn, tp, rk, rt in fingers:
        _capsule(fp, kn, tp, rk, rt)
    # soft contact shadow of the fingers on the mug
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.save()
    c.translate(0.9, 1.3)
    _fill(c, fp, C_MUG_LINE, 0.45, blur=1.3)
    c.restore()
    c.restore()
    _cel(c, fp, C_SKIN, C_SKIN_SH, -1.0, -1.3, line=C_SKIN_LINE, line_w=0.85, line_a=0.85)
    for kn, tp, rk, rt in fingers:
        ux, uy = _norm(tp[0] - kn[0], tp[1] - kn[1])
        # last knuckle crease and a hint of nail at the tip
        jx, jy = tp[0] - ux * 3.6, tp[1] - uy * 3.6
        _stroke(c, _curve([(jx + uy * rt * 0.8, jy - ux * rt * 0.8), (jx - ux * 0.5, jy - uy * 0.5),
                           (jx - uy * rt * 0.8, jy + ux * rt * 0.8)]), C_SKIN_SH, 0.6, 0.6)
        nx_, ny_ = tp[0] - ux * 0.9, tp[1] - uy * 0.9 - 0.5
        c.drawOval(skia.Rect(nx_ - 1.3, ny_ - 0.9, nx_ + 1.3, ny_ + 0.7), paint("#D9A98A", 0.55))


def _draw_held_mug(c, R):
    """Mug held round its body: the hand continues the forearm behind the mug, the mug sits in front of it (toward
    the camera) centred just past the palm, the fingers come round through the handle with their tips over the
    front of the body, the thumb rests on top of the handle. When the hand points the other way in the mug's frame
    (far arm near the front view) the fingers wrap the bare side instead (cross-faded over a narrow band)."""
    M = R.mug
    A = M.arm
    W, hd = A.W, A.hd
    # the hand behind the mug (only the heel shows past the mug's edge; the rest is hidden by the mug)
    hand = skia.Path()
    _capsule(hand, (W[0] - hd[0] * 1.5, W[1] - hd[1] * 1.5), (W[0] + hd[0] * 26.0, W[1] + hd[1] * 26.0), 7.7, 10.4,
             bulge=0.6, bulge_at=0.3)
    _cel(c, hand, C_SKIN, C_SKIN_SH, -1.6, -1.4, line=C_SKIN_LINE, line_w=1.1, line_a=0.8)
    c.save()
    c.translate(M.x, M.y)
    c.rotate(M.ang)
    hs = M.hs
    c.save()
    _mug_local(c, flip=hs < 0)
    c.restore()
    c.scale(hs * MUG_S, MUG_S)
    a = -M.ang * D2R
    hlx = (hd[0] * math.cos(a) - hd[1] * math.sin(a)) * hs
    k = smoothstep((hlx + 0.4) / 0.1)        # 1: fingers through the handle; 0: round the bare side
    for side, wgt in ((True, k), (False, 1.0 - k)):
        if wgt <= 0.005:
            continue
        if wgt < 0.995:
            c.saveLayerAlpha(skia.Rect(-MUG_W - 12, -MUG_H - 12, MUG_W + 18, 8), int(255 * wgt))
            _draw_grip_set(c, side)
            c.restore()
        else:
            _draw_grip_set(c, side)
    # thumb resting on top of the handle
    w = MUG_W
    th = _capsule(skia.Path(), (w - 0.6, -28.4), (w + 5.6, -29.6), 2.6, 2.3)
    _cel(c, th, C_SKIN, C_SKIN_SH, -1.0, -1.3, line=C_SKIN_LINE, line_w=0.85, line_a=0.85)
    c.drawOval(skia.Rect(w + 3.6, -31.0, w + 6.4, -29.4), paint("#D9A98A", 0.6))
    c.restore()


# near hand on the mug: fingers (index .. little) as (hand-local x, knuckle y, r_knuckle, r_tip), hand units
_NEAR_FINGERS = ((5.0, 18.4, 2.7, 2.45), (1.6, 19.4, 2.9, 2.6), (-1.9, 19.0, 2.8, 2.5), (-5.1, 17.4, 2.45, 2.2))
_NEAR_BACK = ((-7.4, -1.0), (-8.6, 6.0), (-8.9, 12.5), (-7.8, 17.8), (-4.2, 20.2), (1.0, 21.0), (5.2, 20.2),
              (8.0, 16.8), (8.5, 9.0), (7.3, 0.0))
_NEAR_THUMB = ((7.4, 3.6), (10.4, 15.4), 3.15, 2.55)     # base, tip (hand-local), radii (hand units)
_NEAR_HAND_W = 0.9          # the near hand seen a little edge-on: its width (across the fingers) foreshortened


def _draw_mug_in_hand(c, R):
    """The held mug on its own (drawn before the near hand, which lies over it)."""
    M = R.mug
    c.save()
    c.translate(M.x, M.y)
    c.rotate(M.ang)
    _mug_local(c, flip=M.hs < 0)
    c.restore()


def _near_grip_geo(R):
    """Upper-body-frame geometry of the near hand gripping the mug: (hp, back, fingers, thumb, df).
    hp(x, y): hand-local -> upper-body frame; fingers: [(knuckle, mid, end, r_knuckle, r_end)] (index first). The
    finger ends sit just past the far silhouette edge of the body (found by marching along the finger), so the
    fingers read as wrapping round behind it; they rise a little toward the edge like the front of the rim
    ellipse (the mug is seen from slightly above)."""
    M = R.mug
    A = M.arm
    W, hd, fx = A.W, A.hd, A.fx
    hs = HAND_S

    def hp(x, y):
        x *= _NEAR_HAND_W
        return (W[0] + (fx[0] * x + hd[0] * y) * hs, W[1] + (fx[1] * x + hd[1] * y) * hs)
    a = M.ang * D2R
    ca_, sa_ = math.cos(a), math.sin(a)
    body = _mug_body_path()
    msx = MUG_S * M.hs

    def inside(p):
        dx, dy = p[0] - M.x, p[1] - M.y
        return body.contains((dx * ca_ + dy * sa_) / msx, (-dx * sa_ + dy * ca_) / MUG_S)
    # the fingers bend round the body: their direction leans from the hand's line toward the mug's sideways axis
    side = (ca_ * M.hs, sa_ * M.hs)
    if hd[0] * side[0] + hd[1] * side[1] < 0:
        side = (-side[0], -side[1])
    up = (sa_, -ca_)                                     # the mug's axis (base -> rim) in the upper-body frame
    bend = 0.55 + 0.8 * (1.0 - abs(hd[0] * side[0] + hd[1] * side[1]))    # more when the hand runs along the axis
    df = _norm(hd[0] + bend * side[0], hd[1] + bend * side[1])
    fingers = []
    for x, ky, rk, rt in _NEAR_FINGERS:
        K = hp(x, ky)
        e = 0.0
        if inside(K):
            step = 0.6
            while e < 60.0 and inside((K[0] + df[0] * (e + step), K[1] + df[1] * (e + step))):
                e += step
            for _ in range(5):                       # refine the edge crossing (no 0.6-unit jitter in motion)
                step *= 0.5
                if inside((K[0] + df[0] * (e + step), K[1] + df[1] * (e + step))):
                    e += step
        rk_, rt_ = rk * hs * _NEAR_HAND_W, rt * hs * _NEAR_HAND_W
        e = max(e + 0.1 * rt_, 0.5)
        lift = 0.1 * e
        mid = (K[0] + df[0] * e * 0.5 + up[0] * lift * 0.35, K[1] + df[1] * e * 0.5 + up[1] * lift * 0.35)
        end = (K[0] + df[0] * e + up[0] * lift, K[1] + df[1] * e + up[1] * lift)
        fingers.append(((K[0] - df[0] * 2.0, K[1] - df[1] * 2.0), mid, end, rk_, rt_))
    back = [hp(x, y) for x, y in _NEAR_BACK]
    tb, tt, trb, trt = _NEAR_THUMB
    thumb = (hp(*tb), hp(*tt), trb * hs * _NEAR_HAND_W, trt * hs * _NEAR_HAND_W)
    return hp, back, fingers, thumb, df


def _finger_path(f):
    kn, mid, en, rk, rt = f
    p = skia.Path()
    _capsule(p, kn, mid, rk, lerp(rk, rt, 0.5))
    _capsule(p, mid, en, lerp(rk, rt, 0.5), rt)
    return p


def _draw_near_grip(c, R):
    """The near hand in front of the held mug (drawn after the mug and the forearm): the back of the hand over the
    front of the body, the knuckle ridge toward the far side, the fingers running on to its far edge and
    wrapping round it (their ends turn away into shadow), the thumb tucked along the top of the hand. The edge
    of the palm (the 'meat' of the hand) shows as a lighter band along the little-finger side."""
    M = R.mug
    hp, back_pts, fingers, thumb, df = _near_grip_geo(R)
    back = smooth_path(back_pts)
    fpaths = [_finger_path(f) for f in fingers]
    th = _capsule(skia.Path(), thumb[0], thumb[1], thumb[2], thumb[3])
    allp = skia.Path(back)
    for fp in fpaths:
        allp.addPath(fp)
    allp.addPath(th)
    # soft contact shadow of the hand on the mug
    mm = skia.Matrix()
    mm.setTranslate(M.x, M.y)
    mm.preRotate(M.ang)
    mm.preScale(MUG_S * M.hs, MUG_S)
    body = _mug_body_path()
    body.transform(mm)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.translate(1.2, 1.8)
    _fill(c, allp, C_MUG_LINE, 0.4, blur=1.6)
    c.restore()
    # thumb along the top edge of the hand, tucked under it (it lies a little deeper than the index knuckle)
    _cel(c, th, C_SKIN, C_SKIN_SH, -1.0, -1.2, line=C_SKIN_LINE, line_w=0.9, line_a=0.85)
    tx, ty = thumb[1]
    ux, uy = _norm(thumb[1][0] - thumb[0][0], thumb[1][1] - thumb[0][1])
    nail = skia.Path()
    nail.addOval(skia.Rect(-1.6, -1.2, 1.6, 1.2))
    nail.transform(skia.Matrix.MakeAll(ux, -uy, tx - ux, uy, ux, ty - uy, 0, 0, 1))
    _fill(c, nail, C_NAIL, 0.55)
    # back of the hand (contour only round the outside), then the fingers from under the knuckle ridge
    c.drawPath(back, paint(C_SKIN_LINE, 0.8, stroke=2.2))
    fp_all = skia.Path()
    for fp in reversed(fpaths):              # little finger first: each contour reads over its neighbour
        fp_all.addPath(fp)
        _cel(c, fp, C_SKIN, C_SKIN_SH, -1.0, -1.2, line=C_SKIN_LINE, line_w=0.9, line_a=0.85)
    # the fingers turn away round the far edge: darken their ends
    c.save()
    c.clipPath(fp_all, doAntiAlias=True)
    for kn, mid, en, rk, rt in fingers:
        c.drawCircle(en[0] + df[0] * rt * 0.7, en[1] + df[1] * rt * 0.7, rt * 1.3, paint(C_SKIN_SH, 0.8, blur=1.8))
    c.restore()
    _cel(c, back, C_SKIN, C_SKIN_SH, -1.6, -1.4)
    c.save()
    c.clipPath(back, doAntiAlias=True)
    meat = _curve([hp(-8.4, 0.5), hp(-9.2, 7.0), hp(-9.2, 13.0), hp(-8.0, 18.0)])
    _stroke(c, meat, C_PALM, 2.4 * HAND_S, 0.7, blur=0.8)
    # knuckle ridge: highlights on the knuckles, soft valleys between them
    for i, (x, ky, rk, rt) in enumerate(_NEAR_FINGERS):
        k0 = hp(x, ky - 1.0)
        c.drawCircle(k0[0], k0[1], 2.0, paint(C_SKIN_HI, 0.28, blur=1.0))
        if i < len(_NEAR_FINGERS) - 1:
            x2, ky2 = _NEAR_FINGERS[i + 1][0], _NEAR_FINGERS[i + 1][1]
            v0, v1 = hp(0.5 * (x + x2), 0.5 * (ky + ky2) - 3.5), hp(0.5 * (x + x2), 0.5 * (ky + ky2) + 1.5)
            _stroke(c, _curve([v0, v1]), C_SKIN_SH, 1.0, 0.55, blur=0.4)
    c.restore()


# --------------------------------------------------------------------------- legs / hips / shoes
def _draw_leg(c, L, R):
    p = skia.Path()
    _capsule(p, L.hip, L.knee, 23.0, 16.5, bulge=1.2, bulge_at=0.4)
    _capsule(p, L.knee, L.ankle, 16.5, 13.0, bulge=0.8, bulge_at=0.35)
    kneel_order = R.k > 0.5
    if kneel_order:
        _draw_shoe(c, L, R)
    _cel(c, p, C_PANTS, C_PANTS_SH, -4.0, -2.0, line=C_PANTS_LINE, line_w=1.4, line_a=0.85)
    ax, ay = L.ankle
    kx, ky = L.knee
    ux, uy = _norm(ax - kx, ay - ky)
    nx, ny = -uy, ux
    hem = _curve([(ax - ux * 6 + nx * 11, ay - uy * 6 + ny * 11), (ax - ux * 3, ay - uy * 3),
                  (ax - ux * 6 - nx * 11, ay - uy * 6 - ny * 11)])
    _stroke(c, hem, C_PANTS_LINE, 1.1, 0.5)
    if R.sw > 0.3 or R.k > 0.3:
        hx_, hy_ = L.hip
        ux2, uy2 = _norm(kx - hx_, ky - hy_)
        _stroke(c, _curve([(kx - ux2 * 12 - uy2 * 8, ky - uy2 * 12 + ux2 * 8), (kx - ux2 * 4, ky - uy2 * 4),
                           (kx - ux2 * 12 + uy2 * 8, ky - uy2 * 12 - ux2 * 8)]), C_PANTS_SH, 1.6, 0.8)
    if not kneel_order:
        _draw_shoe(c, L, R)


_SHOE = [(-13.0, 7.0), (-1.0, 9.5), (8.0, 8.0), (18.0, 3.0), (31.0, -4.0), (40.0, -10.0), (43.5, -16.0),
         (41.0, -21.5), (32.0, -23.0), (-12.0, -23.0), (-16.5, -19.0), (-16.5, -8.0), (-15.0, 2.0)]
_SOLE = [(-16.8, -17.0), (42.6, -17.0), (43.2, -18.5), (41.0, -21.5), (32.0, -23.0), (-12.0, -23.0), (-16.5, -19.0)]
_SOLE_C = [(-13.5, -19.6), (-6.0, -20.1), (10.0, -20.1), (30.0, -19.9), (37.5, -18.6), (40.6, -17.0)]   # sole band centre
# cross-section slices (f, half-width, v_bottom, v_top) -> give the shoe its width in front views
_SLICES = [(-9.0, 11.5, -23.0, 8.0), (6.0, 12.5, -23.0, 8.0), (20.0, 12.5, -23.0, 1.0), (32.0, 11.0, -23.0, -6.0),
           (39.0, 8.5, -22.0, -11.0)]


def _draw_shoe(c, L, R):
    """Sneaker-boot: side profile in the side plane (f forward, v up) relative to the ankle, rotated by the
    foot angle (and the toe tap about the heel), projected with the body turn. Width comes from lateral copies
    of the profile plus cross-section slices, all through the same transform (no shape switching)."""
    s, cc = R.sl, R.cl
    ang = L.foot_ang * D2R
    tap = L.tap * D2R
    ca_, sa_ = math.cos(ang), math.sin(ang)
    ct_, st_ = math.cos(tap), math.sin(tap)

    def tf(f, v):
        if tap:
            hf, hv = -14.0, -23.0
            f0, v0 = f - hf, v - hv
            f, v = hf + f0 * ct_ - v0 * st_, hv + f0 * st_ + v0 * ct_
        return f * ca_ - v * sa_, f * sa_ + v * ca_

    ax, ay = L.ankle
    prof = [tf(f, v) for f, v in _SHOE]
    sole = [tf(f, v) for f, v in _SOLE_C]
    hw = 11.0 * abs(cc)
    lats = (-hw, -0.5 * hw, 0.0, 0.5 * hw, hw) if hw > 8.5 else ((-hw, 0.0, hw) if hw > 0.6 else (0.0,))
    pieces, soles = [], []
    for lat in lats:
        pieces.append(smooth_path([(ax + lat + f * s, ay - v) for f, v in prof], closed=True))
        soles.append(_curve([(ax + lat + f * s, ay - v) for f, v in sole]))
    if abs(cc) > 0.2 and abs(s) < 0.72:
        # cross-section slices swept sideways give the shoe its width where the profile is seen end-on
        for f, w, vb, vt in _SLICES:
            sw_ = w * abs(cc)
            fb, vb2 = tf(f, vb + 2.0)
            ft, vt2 = tf(f, vt - 2.0)
            xb, yb, xt, yt = ax + fb * s, ay - vb2, ax + ft * s, ay - vt2
            pieces.append(smooth_path([(xb - sw_, yb), (xt - sw_ + 1.0, yt), (xt, yt - 1.5), (xt + sw_ - 1.0, yt),
                                       (xb + sw_, yb), (xb, yb + 1.5)], closed=True, tension=0.35))
            fs0, vs0 = tf(f, vb + 3.0)
            xs0, ys0 = ax + fs0 * s, ay - vs0
            q = skia.Path()
            q.moveTo(xs0 - sw_ + 3.0, ys0)
            q.lineTo(xs0 + sw_ - 3.0, ys0)
            soles.append(q)
    pl = paint(C_SHOE_LINE, stroke=2.6)
    for q in pieces:
        c.drawPath(q, pl)
    pf = paint(C_SHOE)
    for q in pieces:
        c.drawPath(q, pf)
    # rubber sole: thick round-capped strokes along the bottom of every copy -> one smooth swept band
    ps = paint(C_SOLE, stroke=6.0)
    for q in soles:
        c.drawPath(q, ps)
    tfx, tfv = tf(28.0, -8.0)
    c.drawOval(skia.Rect(ax + tfx * s - 6, ay - tfv - 3.5, ax + tfx * s + 4, ay - tfv + 1.5), paint(WHITE, 0.10))
    if abs(s) > 0.25:
        f1, v1 = tf(9.0, 5.5)
        f2, v2 = tf(23.0, -0.5)
        lat = -hw
        for kk in (0.0, 0.5, 1.0):
            fx_ = lerp(f1, f2, kk)
            fv_ = lerp(v1, v2, kk)
            c.drawLine(ax + lat + fx_ * s - 2.5, ay - fv_ - 1.5, ax + lat + fx_ * s + 2.5, ay - fv_ + 1.5,
                       paint(C_SOLE, 0.55, stroke=1.2))


def _draw_hips(c, R):
    s, cc = R.s, R.c
    hv = R.hv

    def edge(x, y, b):
        sg = 1 if x > 0 else -1
        return (sg * math.sqrt(x * x * cc * cc + b * b * s * s), y - hv)

    def surf(x, y, z):
        return (x * cc + z * s, y - hv)

    pts = [edge(-47, -40, 28), edge(-53, -6, 31), edge(-50, 20, 30), surf(-24, 42, 20), surf(0, 38, 30),
           surf(24, 42, 20), edge(50, 20, 30), edge(53, -6, 31), edge(47, -40, 28)]
    p = smooth_path(pts, closed=True)
    _cel(c, p, C_PANTS, C_PANTS_SH, -4.0, -2.5, line=C_PANTS_LINE, line_w=1.4, line_a=0.85)


# --------------------------------------------------------------------------- torso / neck / arms
def _torso_geo(R):
    s, cc = R.s, R.c
    su = R.su
    br = R.br

    def edge(x, y, b):
        sg = 1 if x > 0 else -1
        return (sg * math.sqrt(x * x * cc * cc + b * b * s * s), y)

    def surf(x, y, z):
        return (x * cc + z * s, y)

    def chest(pt):
        x, y = pt
        if y < -76:
            return (x * (1 + 0.008 * br), y - br * 1.1)
        return pt
    nk = 4.0 * s
    hem_up = 8.0 * R.sw
    out = [
        (nk - 19.0, -151.0 - su * 5),
        surf(-40, -147 - su * 9, 8),
        edge(-60, -131 - su * 12, 24),
        edge(-58.5, -104, 30),
        edge(-55, -84, 34),
        edge(-46.5, -46, 28),
        edge(-51.5, -8, 31),
        edge(-53.5, 14 - hem_up, 31),
        surf(0, 17 - hem_up, 33),
        edge(53.5, 14 - hem_up, 31),
        edge(51.5, -8, 31),
        edge(46.5, -46, 28),
        edge(55, -84, 34),
        edge(58.5, -104, 30),
        edge(60, -131 - su * 12, 24),
        surf(40, -147 - su * 9, 8),
        (nk + 19.0, -151.0 - su * 5),
        (nk + 9.0 + 14 * s, -141.0),
        surf(0, -137.5, 22),
        (nk - 9.0 + 14 * s, -141.0),
    ]
    out = [chest(q) for q in out]
    if s > 0.05:
        out[12] = (out[12][0] + 3.0 * s, out[12][1])
    near_e = [chest(surf(x, y, z)) for x, y, z in [(-13, -147, 20), (-17, -120, 31), (-19, -84, 33),
                                                     (-18, -44, 27), (-16, 15 - hem_up, 32)]]
    far_e = [chest(surf(x, y, z)) for x, y, z in [(13, -147, 20), (17, -120, 31), (19, -84, 33),
                                                    (18, -44, 27), (16, 15 - hem_up, 32)]]
    return out, near_e, far_e


def _draw_torso(c, R):
    s = R.s
    out, near_e, far_e = _torso_geo(R)
    torso = smooth_path(out, closed=True, tension=0.45)
    _cel(c, torso, C_JACKET, C_JACKET_SH, -5.0 - 7.0 * max(s, 0), -3.0, blur=0.0)
    if R.back:
        _stroke(c, torso, C_JACKET_LINE, 1.5, 0.85)
        return
    neck_mid = out[18]
    band = skia.Path()
    _cr(band, near_e)
    _cr(band, far_e[::-1], move=False)
    _cr(band, [far_e[0], out[17], neck_mid, out[19], near_e[0]], move=False)
    band.close()
    c.save()
    c.clipPath(torso, doAntiAlias=True)
    _fill(c, band, C_SHIRT)
    c.save()
    c.clipPath(band, doAntiAlias=True)
    y_ub = -70.0 - R.br
    c.drawRect(skia.Rect(-80, y_ub - 4, 80, y_ub + 9), paint(C_SHIRT_SH, 0.45, blur=4))
    sh = skia.Path()
    _cr(sh, [(x - 1.0, y) for x, y in far_e])
    _cr(sh, [(x - 7.5, y) for x, y in far_e[::-1]], move=False)
    sh.close()
    _fill(c, sh, C_SHIRT_SH, 0.75, blur=1.5)
    c.drawOval(skia.Rect(neck_mid[0] - 24, neck_mid[1] - 10, neck_mid[0] + 24, neck_mid[1] + 7),
               paint(C_SHIRT_SH, 0.6, blur=3))
    c.restore()
    _stroke(c, _curve([out[17], neck_mid, out[19]]), C_SHIRT_SH, 2.4, 0.9)
    for e, sg in ((near_e, -1), (far_e, 1)):
        _stroke(c, _curve(e), C_JACKET_LINE, 3.0, 0.95)
        _stroke(c, _curve([(x + sg * 1.6, y) for x, y in e[1:]]), C_ZIP, 1.0, 0.55)
    # stand-up collar ends, folded open at the front
    for e, sg, top in ((near_e, -1, out[0]), (far_e, 1, out[16])):
        x0, y0 = e[0]
        k = 1.0 if sg < 0 else max(0.45, R.c)
        flap = smooth_path([(x0 - sg * 0.5, y0 - 1.0), (top[0] + sg * 2.0, top[1] - 6.0),
                            (top[0] + sg * 9.0 * k, top[1] - 3.0), (x0 + sg * 12.0 * k, y0 + 9.0),
                            (x0 + sg * 3.0 * k, y0 + 14.0)], closed=True, tension=0.4)
        _fill(c, flap, C_JACKET_HI)
        _stroke(c, flap, C_JACKET_LINE, 1.2, 0.85)
    if s < 0.75:
        px = -36.0 * R.c + 20 * s
        _stroke(c, _curve([(px - 9, -22), (px + 4, -10)]), C_JACKET_LINE, 2.0, 0.7)
    c.restore()
    _stroke(c, torso, C_JACKET_LINE, 1.5, 0.85)


def _draw_neck(c, R):
    s = R.s
    nx = 4.0 * s
    collar = smooth_path([(nx - 27, -146), (nx - 25, -163), (nx, -169), (nx + 25, -163), (nx + 27, -146),
                          (nx, -150)], closed=True)
    _fill(c, collar, C_JACKET_SH)
    _stroke(c, collar, C_JACKET_LINE, 1.2, 0.8)
    neck = skia.Path()
    neck.addRRect(skia.RRect.MakeRectXY(skia.Rect(nx - 16.5, -205.0, nx + 16.5, -133.0), 8, 8))
    _fill(c, neck, C_SKIN)
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    # jaw shadow falls on the neck (drawn in the head frame so it follows tilts)
    c.concat(R.MHr)
    chin_y = 68.0 + _jaw_dy(R.H, 68.0)
    cx = 30.0 * R.H.s
    c.drawOval(skia.Rect(cx - 52, chin_y - 40, cx + 52, chin_y + 13), paint(C_SKIN_SH, 0.95, blur=3.0))
    c.restore()
    c.save()
    c.clipPath(neck, doAntiAlias=True)
    c.drawRect(skia.Rect(nx + 8.0, -210, nx + 30, -120), paint(C_SKIN_SH, 0.5, blur=3.0))
    c.restore()
    _stroke(c, neck, C_SKIN_LINE, 1.2, 0.55)


def _limb_band(a, b, u0, u1, r):
    """Rounded band across the segment a->b between fractions u0..u1 with half-width r."""
    ux, uy = _norm(b[0] - a[0], b[1] - a[1])
    nx, ny = -uy, ux
    p0 = (a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0)
    p1 = (a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1)
    pts = [(p0[0] + nx * r, p0[1] + ny * r), (p1[0] + nx * (r + 0.5), p1[1] + ny * (r + 0.5)),
           (p1[0] + ux * 1.2, p1[1] + uy * 1.2),
           (p1[0] - nx * (r + 0.5), p1[1] - ny * (r + 0.5)), (p0[0] - nx * r, p0[1] - ny * r),
           (p0[0] - ux * 1.2, p0[1] - uy * 1.2)]
    return smooth_path(pts, closed=True, tension=0.25)


def _arm_occluder(A, R):
    """Rough silhouette (upper-body frame) of an arm drawn over the face, to mask eye glints."""
    S, E, W = A.S, A.E, A.W
    occ = skia.Path()
    _capsule(occ, S, E, 16.0, 15.0)
    _capsule(occ, E, W, 11.0, 8.0)
    occ.addCircle(A.palm[0], A.palm[1], 15.0 * HAND_S, skia.PathDirection.kCCW)
    if R.mug is not None and R.mug.arm is A:
        m = skia.Matrix()
        m.setRotate(R.mug.ang, R.mug.x, R.mug.y)
        mp = skia.Path()
        mp.addRect(skia.Rect(R.mug.x - (MUG_W + 7) * MUG_S, R.mug.y - (MUG_H + 5) * MUG_S,
                             R.mug.x + (MUG_W + 14) * MUG_S, R.mug.y + 1))
        mp.transform(m)
        occ.addPath(mp)
    return occ


def _draw_arm(c, A, R):
    S, E, W = A.S, A.E, A.W
    ux, uy = _norm(E[0] - S[0], E[1] - S[1])
    held = R.mug is not None and R.mug.arm is A
    near = held and R.mug.near
    if near:
        _draw_mug_in_hand(c, R)          # near hand: the mug first, the forearm and the hand over it
    fore = skia.Path()
    _capsule(fore, (E[0] - ux * 2, E[1] - uy * 2), W, 10.8, 7.6, bulge=1.4, bulge_at=0.3)
    _cel(c, fore, C_SKIN, C_SKIN_SH, -3.0, -2.0, line=C_SKIN_LINE, line_w=1.25, line_a=0.75)
    if near:
        _draw_near_grip(c, R)
    elif held:
        _draw_held_mug(c, R)
    else:
        _draw_hand(c, A)
    sl = skia.Path()
    Ee = (E[0] + ux * 4, E[1] + uy * 4)
    _capsule(sl, S, Ee, 15.0, 13.6, bulge=1.0, bulge_at=0.35)
    _cel(c, sl, C_JACKET, C_JACKET_SH, -4.0, -2.5, line=C_JACKET_LINE, line_w=1.4, line_a=0.85)
    _stroke(c, _curve([(E[0] - ux * 14 - uy * 7, E[1] - uy * 14 + ux * 7), (E[0] - ux * 9, E[1] - uy * 9),
                       (E[0] - ux * 12 + uy * 6, E[1] - uy * 12 - ux * 6)]), C_JACKET_SH, 1.4, 0.8)
    seg_len = max(1.0, math.hypot(Ee[0] - S[0], Ee[1] - S[1]))
    u0 = 1.0 - 11.0 / seg_len
    cuff = _limb_band(S, Ee, u0, 1.0, 15.2)
    _cel(c, cuff, C_JACKET_HI, C_JACKET, -2.0, -2.0, line=C_JACKET_LINE, line_w=1.3, line_a=0.85)
    um = lerp(u0, 1.0, 0.5)
    mx, my = S[0] + (Ee[0] - S[0]) * um, S[1] + (Ee[1] - S[1]) * um
    _stroke(c, _curve([(mx - uy * 14.5, my + ux * 14.5), (mx + ux * 0.8, my + uy * 0.8),
                       (mx + uy * 14.5, my - ux * 14.5)]), C_JACKET_LINE, 1.0, 0.55)
    if A.o < 0 and A.layer == "front" and R.s < 0.65 and not R.back:
        px, py = S[0] + ux * 30 - uy * 3, S[1] + uy * 30 + ux * 3
        c.drawCircle(px, py, 5.2, paint(C_PATCH))
        c.drawCircle(px, py, 5.2, paint(C_JACKET_LINE, 0.8, stroke=1.0))
        c.drawCircle(px - 0.8, py - 0.8, 1.6, paint(WHITE, 0.85))


# --------------------------------------------------------------------------- eyes
def _bump(s, pk, e):
    q = (s - pk) / (1.0 - pk) if s >= pk else (s - pk) / (1.0 + pk)
    v = 1.0 - q * q
    return v ** e if v > 0 else 0.0


_SS = [-1.0, -0.82, -0.6, -0.36, -0.12, 0.12, 0.36, 0.6, 0.8, 0.93, 1.0]
_PU = [_bump(s, -0.1, 0.6) for s in _SS]
_PL = [_bump(s, 0.15, 0.75) for s in _SS]
_BASE = [lerp(2.2, -2.6, (s + 1) / 2) for s in _SS]


_OUTER = [smoothstep((s - 0.15) / 0.7) for s in _SS]     # weight of the outer third of the eye


def _eye_curves(op, squint, wide, gy, worry=0.0):
    hu = HU0 * (1.0 + 0.6 * wide)
    hl = HL0 * (1.0 + 0.14 * wide)
    if gy > 0:
        hu *= 1.0 - 0.28 * gy
    else:
        hu *= 1.0 - 0.1 * gy
    U, LL = [], []
    for b, pu, pl, wo in zip(_BASE, _PU, _PL, _OUTER):
        # worry: the outer third of the upper lid droops (sad eyes), the lower lid follows a little
        u = b - hu * pu + worry * 3.4 * wo * pu
        l_ = b + hl * pl - squint * (hl + 0.45 * HU0) * (pl ** 0.9) - max(0.0, -gy) * 1.4 * pl
        l_ += worry * 1.6 * wo * squint
        l_ = max(l_, u + 0.6 * pu)
        U.append(u)
        LL.append(l_)
    ope = clamp(op) * (1.0 - 0.16 * squint)
    UL = [l_ + (u - l_) * ope for u, l_ in zip(U, LL)]
    return U, LL, UL, ope


def _draw_eye(c, H, P, slot, t):
    """slot = -1 (eye at local -x) or +1. P = per-eye params."""
    x0 = slot * EX
    ex, ey, dep, fs = _hx(H, x0, 0.0)
    if dep < -6:
        return
    sd = float(slot)
    U, LL, UL, ope = _eye_curves(P.lid, P.squint, P.wide, P.gy, P.bworry)
    # far eye near the silhouette: squash its outer half so the corner (and lash flick) stays inside the
    # cheek outline instead of being sliced by it
    fso = fs
    far = slot * H.s > 0.02
    if far:
        lim = sd * _sil_x(H, -2.0, slot) - 5.0
        fso = clamp((lim - sd * ex) / (EW + 2.0), 0.12, fs)
    P.gsc = fso / max(fs, 1e-3) if far else 1.0
    P.evis = 0.5 * (fs + fso)          # visible width of the eye opening relative to the front view

    def m(u, v):
        return (ex + sd * u * (fso if u > 0 else fs), ey + v)

    us = [s * EW for s in _SS]
    pU = [m(u, v) for u, v in zip(us, U)]
    pLL = [m(u, v) for u, v in zip(us, LL)]
    pUL = [m(u, v) for u, v in zip(us, UL)]
    # under-eye: tired shading + sniffle puffiness
    bag = _closed2([(x, y + 2.0) for x, y in pLL[2:-1]], [(x, y + 6.0 + 2.0 * P.sniffle) for x, y in pLL[2:-1]][::-1])
    _fill(c, bag, C_SKIN_SH, EYE_BAG + 0.12 * P.sniffle, blur=2.0)
    if P.sniffle > 0:
        _fill(c, bag, C_BLUSH, 0.45 * P.sniffle, blur=2.2)
        _stroke(c, _curve([(x, y + 4.8 + 1.5 * P.sniffle) for x, y in pLL[3:-2]]), C_SKIN_SH, 1.2, 0.45 * P.sniffle)
    # socket shading above the lid (form of the brow ridge)
    sock = _closed2([(x, y - 2.0) for x, y in pU[1:-1]], [(x, y - 8.0) for x, y in pU[1:-1]][::-1])
    _fill(c, sock, C_SKIN_SH, 0.22, blur=2.5)
    # lid skin that came down over the eye
    if ope < 0.985:
        lid = _closed2(pU, pUL[::-1])
        _fill(c, lid, C_LID)
    crease = [m(u, v - 4.4 - 1.0 * pu - 1.6 * P.wide) for u, v, pu in zip(us[1:-1], U[1:-1], _PU[1:-1])]
    _stroke(c, _curve(crease), C_SKIN_DEEP, 1.3, 0.55 * (0.45 + 0.55 * ope))
    closed = ope < 0.03
    if not closed:
        opening = _closed2(pUL, pLL[::-1])
        _fill(c, opening, C_SCLERA)
        c.save()
        c.clipPath(opening, doAntiAlias=True)
        c.drawCircle(m(-EW, 0)[0], ey, 7.5, paint(C_SCLERA_SH, 0.35, blur=4))
        c.drawCircle(m(EW, 0)[0], ey - 1, 7.5, paint(C_SCLERA_SH, 0.3, blur=4))
        if P.sniffle > 0:
            c.drawCircle(m(-EW + 2, 1)[0], ey + 1, 6.5, paint("#E08A84", 0.5 * P.sniffle, blur=3))
            c.drawCircle(m(EW - 2, 1)[0], ey + 1, 5.5, paint("#E08A84", 0.3 * P.sniffle, blur=3))
        fsi = lerp(1.0, fs, 0.6)
        ix = ex + P.gx * 7.0 * (fso if P.gx * sd > 0 else fs)
        if far:     # keep the iris centre inside the squashed outer corner
            ix = sd * min(sd * ix, sd * ex + EW * fso - 1.5)
        iy = ey + 0.6 + P.gy * 3.6
        rx, ry = RI * fsi, RI
        iris = skia.Rect(ix - rx, iy - ry, ix + rx, iy + ry)
        c.drawOval(iris, paint(C_IRIS))
        ip = skia.Path()
        ip.addOval(iris)
        c.save()
        c.clipPath(ip, doAntiAlias=True)
        c.drawOval(skia.Rect(ix - rx * 0.78, iy - ry * 0.78, ix + rx * 0.78, iy + ry * 0.78), paint(C_IRIS_MID, blur=1.6))
        c.drawOval(skia.Rect(ix - rx * 0.8, iy + 0.5, ix + rx * 0.8, iy + ry * 1.2),
                   paint(C_IRIS_LT, 0.8 + 0.2 * P.shine, blur=2.6))
        pr = 4.5 * P.pupil
        c.drawOval(skia.Rect(ix - pr * fsi, iy - pr + 0.3, ix + pr * fsi, iy + pr + 0.3), paint(C_PUPIL))
        if P.shine > 0:
            c.drawOval(skia.Rect(ix - rx * 0.76, iy - ry * 0.76, ix + rx * 0.76, iy + ry * 0.76),
                       paint(C_IRIS_LT, 0.5 * P.shine, stroke=1.2))
        c.restore()
        c.drawOval(iris, paint(C_PUPIL, 0.75, stroke=1.2))
        shadow = _closed2(pUL, [(x, y + 5.0) for x, y in pUL[::-1]])
        _fill(c, shadow, C_SCLERA_SH, 0.75, blur=1.8)
        if P.tears > 0:
            pool = _closed2([(x, y - 2.8 * P.tears) for x, y in pLL[1:-1]], pLL[1:-1][::-1])
            _fill(c, pool, C_TEAR, 0.5 * P.tears)
        glint = (lambda cc, ix=ix, iy=iy, fsi=fsi, P=P: _eye_glints(cc, ix, iy, fsi, P))
        glint(c)
        c.restore()
        if P.emit is not None:
            P.emit.append((opening, glint))
        _stroke(c, _curve(pLL[3:]), C_LASH, 1.3, 0.5 * clamp(ope * 3))
        if P.sniffle > 0:
            _stroke(c, _curve(pLL[2:]), "#B45A50", 1.6, 0.55 * P.sniffle)
        if P.tears > 0:
            _stroke(c, _curve([(x, y - 1.0) for x, y in pLL[2:-1]]), WHITE, 1.2, 0.85 * P.tears)
            _stroke(c, _curve([(x, y + 0.7) for x, y in pLL[1:-1]]), C_TEAR, 1.8, 0.6 * P.tears)

    def lash(c):
        # lash line (upper lid edge) with an outer flick
        th = [lerp(1.0, 4.0, ((s + 1) / 2) ** 0.5) * LASH_TH for s in _SS]
        if closed:
            th = [w * 0.85 for w in th]
        base = pUL
        top = [(x, y - w) for (x, y), w in zip(base, th)]
        bo = _BASE[-1]
        # the flick keeps some length on the far eye so it can poke past the cheek silhouette
        fk = max(fso, min(fs + 0.2, 0.8)) if far else fs
        e0 = m(EW, 0.0)[0]
        flick_tip = (e0 + sd * 6.0 * LASH_FLICK * fk, ey + bo - 4.6 * LASH_FLICK - 1.4 * LASH_FLICK * P.wide + (1.5 if closed else 0.0))
        lash = skia.Path()
        _cr(lash, base)
        q1 = (e0 + sd * 2.8 * LASH_FLICK * fk, ey + bo - 0.6)
        lash.quadTo(q1[0], q1[1], flick_tip[0], flick_tip[1])
        q2 = (e0 + sd * 1.0 * LASH_FLICK * fk, ey + bo - 4.4 * LASH_FLICK - LASH_FLICK * P.wide)
        lash.quadTo(q2[0], top[-1][1] - 0.6, top[-1][0], top[-1][1])
        _cr(lash, top[::-1], move=False)
        lash.close()
        _fill(c, lash, C_LASH)
        if not closed and LASH_EXTRA:
            for k, (u, ln, ang) in enumerate(((0.66, 2.8, -40.0), (0.86, 3.6, -22.0))):
                i = min(range(len(_SS)), key=lambda j: abs(_SS[j] - u))
                px, py = top[i]
                dx = math.cos(ang * D2R) * ln * sd * fs
                dy = math.sin(ang * D2R) * ln
                _fill(c, _ribbon([(px - sd * 0.8 * fs, py + 0.8), (px + dx * 0.6, py + dy * 0.6), (px + dx, py + dy)],
                                 [1.6, 1.1, 0.3]), C_LASH)
        if closed:
            for u in (0.3, 0.62, 0.9):
                i = min(range(len(_SS)), key=lambda j: abs(_SS[j] - u))
                px, py = base[i]
                _stroke(c, _curve([(px, py), (px + sd * 1.4 * fs, py + 2.8)]), C_LASH, 1.0, 0.7)
        if ope < 0.4 and P.squint > 0.35:
            # squeezed shut: little creases fanning from the outer corner
            k = clamp((P.squint - 0.35) / 0.4) * clamp((0.4 - ope) / 0.3)
            ox_, oy_ = m(EW * 0.95, LL[-1])
            for dy_, ln in ((3.4, 6.0), (7.4, 4.6)):
                _stroke(c, _curve([(ox_ - sd * 1.0 * fs, oy_ + dy_ - 1.6), (ox_ + sd * ln * 0.55 * fso, oy_ + dy_),
                                   (ox_ + sd * ln * fso, oy_ + dy_ - 1.8)]), C_SKIN_DEEP, 1.2, 0.55 * k)

    if getattr(P, "lash_out", None) is not None:
        P.lash_out.append(lash)
    else:
        lash(c)
    if P.tear_roll > 0:
        _draw_tear(c, H, slot, P.tear_roll)


def _eye_glints(c, ix, iy, fsi, P):
    """Catch-lights / wet glints (also replayed un-darkened in low light)."""
    g = getattr(P, "gsc", 1.0)      # < 1 on the far eye squashed against the cheek silhouette
    ev = getattr(P, "evis", 1.0)
    va = smoothstep((ev - 0.17) / 0.13)  # a near-profile far eye: glints shrink and fade instead of floating
    if va <= 0.0:
        return
    gs = 0.55 + 0.45 * clamp(ev / 0.45)
    big = (1.0 + 0.45 * P.tears + 0.25 * P.shine) * gs
    hx, hy = ix + 3.4 * fsi * g - (1.0 - g) * 1.5, iy - 4.0
    c.drawOval(skia.Rect(hx - 3.3 * big * fsi, hy - 2.8 * big, hx + 3.3 * big * fsi, hy + 2.8 * big), paint(WHITE, 0.97 * va))
    sm = (1.0 + 0.35 * P.tears) * gs
    c.drawCircle(ix - 3.6 * fsi * g, iy + 3.8, 1.4 * sm, paint(WHITE, 0.9 * va))
    if P.tears > 0:
        arc = skia.Path()
        arc.addArc(skia.Rect(ix - (RI - 2.4) * fsi, iy - RI + 2.4, ix + (RI - 2.4) * fsi, iy + RI - 2.4), 25, 130)
        _stroke(c, arc, WHITE, 1.4, 0.55 * P.tears * va)
        c.drawCircle(ix + 5.0 * fsi * g, iy + 2.4, (0.9 * P.tears + 0.25) * gs, paint(WHITE, 0.85 * P.tears * va))
    if P.shine > 0 and ev > 0.3:
        sx, sy = ix - 5.0 * fsi, iy - 5.4
        r = 3.0 * P.shine * gs
        star = skia.Path()
        star.moveTo(sx, sy - r)
        star.quadTo(sx, sy, sx + r * 0.75, sy)
        star.quadTo(sx, sy, sx, sy + r)
        star.quadTo(sx, sy, sx - r * 0.75, sy)
        star.quadTo(sx, sy, sx, sy - r)
        _fill(c, star, WHITE, 0.9)


def _draw_tear(c, H, slot, prog):
    """A droplet rolling from the lower lid down the cheek, leaving a shiny trail that dries to a faint streak.
    On the far side of the face the tear runs inward (toward the nose) instead of along the silhouette."""
    kf = smoothstep((slot * H.s - 0.08) / 0.25)
    pts = []
    for (xo_n, xo_f), y in (((4.0, 1.0), 11.5), ((6.5, -1.5), 21.0), ((7.5, -3.5), 32.0), ((5.0, -5.0), 44.0),
                            ((0.5, -7.0), 55.0)):
        x0 = slot * (EX + lerp(xo_n, xo_f, kf))
        x, yy, _, _ = _hx(H, x0, y, 1.0)
        pts.append((x, yy))
    path = _curve(pts)
    meas = skia.PathMeasure(path, False)
    total = meas.getLength()
    p = clamp(prog)
    d = total * min(1.0, p * 1.08)
    if d < 1:
        return
    fade = 1.0 - smoothstep((p - 0.88) / 0.12)
    # wet trail: bright just behind the drop, drying to ~30 % further up (one stroke, alpha gradient)
    seg = skia.Path()
    meas.getSegment(0, d, seg, True)
    p0, _ = meas.getPosTan(0.0)
    p1, _ = meas.getPosTan(d)
    bright = 0.35 + 0.65 * fade
    u = clamp(1.0 - 0.32 * total / max(d, 1e-3), 0.0, 0.999)
    for colr, a, wd in ((C_TEAR, 0.45, 3.2), (WHITE, 0.7, 1.1)):
        sh = skia.GradientShader.MakeLinear([(p0.fX, p0.fY), (p1.fX, p1.fY)],
                                            [col(colr, a * 0.3), col(colr, a * 0.3), col(colr, a * bright)], [0.0, u, 1.0])
        tp = paint(None, stroke=wd, shader=sh, cap="butt")
        if _CF is not None:
            tp.setColorFilter(_CF)
        c.drawPath(seg, tp)
    pos, _ = meas.getPosTan(d)
    x, y = pos.fX, pos.fY
    r = 3.0 + 0.7 * min(1.0, p * 3)
    drop = skia.Path()
    drop.moveTo(x, y - r * 2.1)
    drop.cubicTo(x + r * 0.5, y - r * 1.0, x + r, y - r * 0.2, x + r, y + r * 0.35)
    drop.cubicTo(x + r, y + r * 1.25, x - r, y + r * 1.25, x - r, y + r * 0.35)
    drop.cubicTo(x - r, y - r * 0.2, x - r * 0.5, y - r * 1.0, x, y - r * 2.1)
    drop.close()
    _fill(c, drop, C_TEAR, 0.88 * fade)
    _stroke(c, drop, "#7FB3D6", 0.9, 0.75 * fade)
    c.drawCircle(x - r * 0.35, y - r * 0.05, r * 0.38, paint(WHITE, 0.95 * fade))


def _draw_brow(c, H, P, slot):
    x0 = slot * EX
    ex, _, dep, fs = _hx(H, x0, -24.0)
    if dep < -6:
        return
    ey = H.nod_dy * (dep / 60.0)
    sd = float(slot)
    r, w, f = P.braise, P.bworry, P.bfurrow
    fso = fs
    if slot * H.s > 0.02:
        lim = sd * _sil_x(H, -24.0, slot) - 2.5
        fso = clamp((lim - sd * ex) / (EW * 1.18), 0.2, fs)
    pts, ths = [], []
    n = 7
    for i in range(n):
        s = i / (n - 1)
        u = lerp(-EW * 0.92, EW * 1.18, s)
        # worry flattens the arch and tilts the whole brow (inner end up, outer end down)
        v = -23.5 - 4.2 * (1.0 - 0.45 * w) * math.sin(math.pi * min(1.0, s * 1.08)) + 1.6 * s
        th = lerp(BROW_W[0], BROW_W[1], s ** 1.1)
        if r >= 0:
            v -= r * (6.5 + 2.8 * math.sin(math.pi * s))
        else:
            v -= r * 5.0
        v -= w * 10.5 * (1 - s) ** 1.25
        v += w * 4.2 * s ** 1.3
        u -= w * 1.4 * (1 - s)
        v += f * 6.8 * (1 - s) ** 1.5
        v -= f * 1.4 * s
        u -= f * 3.0 * (1 - s)
        th *= 1.0 + 0.12 * f + 0.1 * w * (1 - s)
        v += P.squint * 2.0
        pts.append((ex + sd * u * (fso if u > 0 else fs), ey + v))
        ths.append(th)
    p0, p1 = pts[0], pts[1]
    dx, dy = _norm(p0[0] - p1[0], p0[1] - p1[1])
    pts.insert(0, (p0[0] + dx * 2.0, p0[1] + dy * 2.0 + 0.6))
    ths.insert(0, ths[0] * 0.8)
    path = _ribbon(pts, ths)
    _fill(c, path, C_BROW)
    _stroke(c, _curve([(x, y - 0.8) for x, y in pts[2:5]]), C_HAIR_HI, 1.0, 0.4)


# --------------------------------------------------------------------------- nose / mouth / ears
def _draw_nose(c, H, P):
    s = H.s
    tx, ty, _, _ = _hx(H, 0.0, 22.5, 8.0 + 4.0 * smoothstep((abs(s) - 0.3) / 0.4))
    nd = H.nod_dy * 0.95
    bx = _hx(H, 0.0, 6.0, 3.0)[0]
    side = _curve([(bx + 3.0 + 1.5 * s, 0.0 + nd), (tx + 4.5 + 1.2 * s, 13.0 + nd), (tx + 5.5, 20.5 + nd)])
    _stroke(c, side, C_SKIN_SH, 4.5, 0.32 + 0.25 * min(1.0, abs(s) * 2), blur=2.0)
    c.drawOval(skia.Rect(tx - 6.0 + 3.0 * s, 24.0 + nd, tx + 7.5 + 2.0 * s, 29.5 + nd), paint(C_SKIN_SH, 0.5, blur=2.2))
    pts = []
    for x0, y, dz in ((-6.6, 21.6, 2.0), (-7.4, 24.4, 3.0), (-5.0, 26.6, 5.0), (-1.8, 26.9, 8.0), (0.8, 26.3, 9.0)):
        x, yy, _, _ = _hx(H, x0, y, dz)
        pts.append((x, yy))
    _stroke(c, _curve(pts), C_SKIN_LINE, 1.6, 0.72)
    pts2 = []
    for x0, y, dz in ((2.8, 26.7, 8.0), (5.6, 26.2, 5.0), (7.2, 23.6, 2.5)):
        x, yy, _, _ = _hx(H, x0, y, dz)
        pts2.append((x, yy))
    _stroke(c, _curve(pts2), C_SKIN_LINE, 1.6, 0.5 * clamp(1 - s * 1.6))
    for x0 in (-3.6, 3.6):
        x, yy, dep, fs = _hx(H, x0, 25.6, 5.5)
        if x0 > 0 and s > 0.35:
            continue
        c.drawOval(skia.Rect(x - 1.8 * fs, yy - 0.9, x + 1.8 * fs, yy + 0.9), paint(C_SKIN_LINE, 0.45))
    c.drawOval(skia.Rect(tx - 4.8, ty - 4.0, tx + 0.8, ty - 0.6), paint(C_SKIN_HI, 0.65, blur=1.0))
    if P.sniffle > 0:
        c.drawCircle(tx + 0.5, ty + 1.5, 8.5, paint(C_BLUSH, 0.6 * P.sniffle, blur=4.0))


def _mouth_geom(H, p, t):
    y0 = MOUTH_Y
    op = clamp(p.mouth_open)
    rd = clamp(p.mouth_round)
    sm = clamp(p.smile, -1.0, 1.0)
    sk = clamp(p.smirk, -1.0, 1.0)
    tr = clamp(p.mouth_tremble)
    W = 15.0 * (1 + 0.24 * max(sm, 0) - 0.05 * max(-sm, 0)) * (1 - 0.42 * rd) * (1 + 0.08 * op) * (1 - 0.1 * tr)
    qL = qR = qM = 0.0
    if tr > 0 and t is not None:
        qL = noise1(t * 13.0, 5) * tr * 1.6
        qR = noise1(t * 12.0, 9) * tr * 1.6
        qM = noise1(t * 16.0, 2) * tr * 2.0
    cyL = y0 - sm * 4.8 + tr * 2.0 + qL + max(sk, 0) * 1.0 - max(-sk, 0) * 5.6
    cyR = y0 - sm * 4.8 + tr * 2.0 + qR - max(sk, 0) * 5.6 + max(-sk, 0) * 1.0
    cxL = -W - max(-sk, 0) * 2.0
    cxR = W + max(sk, 0) * 2.0
    up_m = y0 - 0.6 - op * (2.6 + 2.8 * rd) - max(sm, 0) * 0.8 * op
    lo_m = y0 + 0.8 + op * 16.5 * (1 - 0.18 * rd) + max(sm, 0) * op * 3.0 + qM
    lo_m = max(lo_m, up_m + 0.8)
    # round shapes morph toward an ellipse: corners at mid height, quarter points on the ellipse (O / OO)
    yc, hb = (up_m + lo_m) * 0.5, (lo_m - up_m) * 0.5
    rdo = rd * smoothstep(op / 0.25)
    cyL = lerp(cyL, yc, rdo * 0.85)
    cyR = lerp(cyR, yc, rdo * 0.85)

    def upq(cy):
        return lerp(lerp(cy, up_m, 0.78) - 0.3, yc - 0.87 * hb, rdo)

    def loq(cy):
        return lerp(lerp(cy, lo_m, 0.8), yc + 0.87 * hb, rdo)
    U = [(cxL, cyL), (cxL * 0.5, upq(cyL)), (0.0, up_m), (cxR * 0.5, upq(cyR)), (cxR, cyR)]
    Lw = [(cxL, cyL), (cxL * 0.55, loq(cyL)), (0.0, lo_m), (cxR * 0.55, loq(cyR)), (cxR, cyR)]
    if op < 0.06:
        k = 1 - op / 0.06
        mid = y0 + sm * 1.4 - abs(sk) * 0.4 + qM * 0.5
        U[2] = (0.0, lerp(up_m, mid, k))
        U[1] = (U[1][0], lerp(U[1][1], (cyL + mid) / 2 + sm * 1.0, k))
        U[3] = (U[3][0], lerp(U[3][1], (cyR + mid) / 2 + sm * 1.0, k))
    nd = H.nod_dy * 0.9

    def pj(pt):
        return (_hx(H, pt[0], y0)[0], pt[1] + nd)
    pU = [pj(q) for q in U]
    pL = [pj(q) for q in Lw]
    return pU, pL, op, rd, sm, sk


def _mouth_extent(H, geom):
    """(x, y_top, y_bottom) of the mouth's outermost point on the leading (far) side, lips included."""
    pU, pL = geom[0], geom[1]
    sg = 1.0 if H.s >= 0 else -1.0
    x = max(sg * q[0] for q in pU + pL) * sg
    return x, min(q[1] for q in pU) - 3.0, max(q[1] for q in pL) + 6.0


def _draw_mouth(c, H, p, t, geom=None):
    pU, pL, op, rd, sm, sk = geom if geom is not None else _mouth_geom(H, p, t)
    lo_y = pL[2][1]
    _stroke(c, _curve([(pL[2][0] - 6.0, lo_y + 8.5), (pL[2][0], lo_y + 10.0), (pL[2][0] + 6.0, lo_y + 8.5)]),
            C_SKIN_SH, 2.0, 0.4, blur=0.8)
    lip = _closed2([pL[0], pL[1], pL[2], pL[3], pL[4]],
                   [(pL[3][0], pL[3][1] + 3.0), (pL[2][0], pL[2][1] + 6.6), (pL[1][0], pL[1][1] + 3.0)])
    _fill(c, lip, C_LIP, 0.88, blur=0.4)
    c.drawOval(skia.Rect(pL[2][0] - 4.4, pL[2][1] + 1.8, pL[2][0] + 2.4, pL[2][1] + 4.0), paint(C_LIP_HI, 0.7, blur=0.8))
    ulip = _closed2([pU[0], pU[1], pU[2], pU[3], pU[4]],
                    [(pU[3][0], pU[3][1] - 2.4), (pU[2][0] + 2.0, pU[2][1] - 3.6), (pU[2][0], pU[2][1] - 2.7),
                     (pU[2][0] - 2.0, pU[2][1] - 3.6), (pU[1][0], pU[1][1] - 2.4)])
    _fill(c, ulip, C_LIP, 0.62, blur=0.4)
    if op >= 0.03:
        # corners split vertically for round shapes -> rounded sides instead of pointed corners
        gapc = (pL[2][1] - pU[2][1]) * 0.22 * rd
        inner = smooth_path([(pU[0][0] + 0.8 * rd, pU[0][1] - gapc * 0.5), pU[1], pU[2], pU[3],
                             (pU[4][0] - 0.8 * rd, pU[4][1] - gapc * 0.5), (pL[4][0] - 0.8 * rd, pL[4][1] + gapc * 0.5),
                             pL[3], pL[2], pL[1], (pL[0][0] + 0.8 * rd, pL[0][1] + gapc * 0.5)], closed=True)
        _fill(c, inner, C_MOUTH)
        c.save()
        c.clipPath(inner, doAntiAlias=True)
        gap = pL[2][1] - pU[2][1]
        tth = min(4.6, 0.42 * gap) * (1.0 - 0.55 * rd)
        if op > 0.08:
            teeth = _closed2([(x, y - 2) for x, y in pU],
                             [(x, y + tth * (0.55 + 0.45 * (1 - abs(i - 2) / 2.0))) for i, (x, y) in enumerate(pU)][::-1])
            _fill(c, teeth, C_TEETH)
        if op > 0.18:
            ta = smoothstep((op - 0.18) / 0.25)
            tx = pL[2][0]
            tw = abs(pU[4][0] - pU[0][0]) * 0.36
            c.drawOval(skia.Rect(tx - tw, pL[2][1] - 6.5, tx + tw, pL[2][1] + 3.0), paint(C_TONGUE, ta))
        c.restore()
        _stroke(c, inner, C_LIP_LINE, 1.3, 0.9)
    _fill(c, _ribbon(pU, [0.9, 2.1, 2.6, 2.1, 0.9]), C_LIP_LINE, 0.95)
    for sgn, (cx, cy), amt in ((-1, pU[0], max(sm, 0) + max(-sk, 0)), (1, pU[4], max(sm, 0) + max(sk, 0))):
        if amt > 0.2:
            a = clamp((amt - 0.2) / 0.6)
            _stroke(c, _curve([(cx + sgn * 0.6, cy - 2.8), (cx + sgn * 2.8, cy - 0.4), (cx + sgn * 2.0, cy + 2.4)]),
                    C_SKIN_LINE, 1.3, 0.6 * a)
        if sm < -0.2:
            a = clamp((-sm - 0.2) / 0.5)
            _stroke(c, _curve([(cx, cy), (cx + sgn * 1.6, cy + 3.2)]), C_SKIN_LINE, 1.1, 0.45 * a)


def _draw_ear(c, H, slot):
    x, y, vis = _surf_az(H, slot * 90.0, 3.0)
    k = clamp(abs(H.s) * 1.3) if (slot * H.s) < 0 else 0.0
    w = lerp(9.0, 13.0, k)
    o = float(slot)
    if k > 0.2:
        o = -1.0 if H.s > 0 else 1.0
    pts = [(0.0, -14.0), (0.45 * w, -17.0), (0.92 * w, -11.0), (w, 0.0), (0.8 * w, 10.0), (0.45 * w, 18.0),
           (0.1 * w, 20.0), (-1.0, 12.0)]
    path = smooth_path([(x + o * px, y + py) for px, py in pts], closed=True)
    _fill(c, path, C_SKIN)
    _stroke(c, path, C_SKIN_LINE, 1.3, 0.7)
    inner = _curve([(x + o * 0.62 * w, y - 10.0), (x + o * 0.74 * w, y), (x + o * 0.5 * w, y + 8.5),
                    (x + o * 0.2 * w, y + 9.5)])
    _stroke(c, inner, C_SKIN_SH, 2.2, 0.9)
    c.drawCircle(x + o * 0.32 * w, y + 17.0, 2.0, paint(C_STUD))
    c.drawCircle(x + o * 0.32 * w - 0.5, y + 16.5, 0.75, paint(WHITE, 0.9))


# --------------------------------------------------------------------------- hair
PUFF_CY, PUFF_RX, PUFF_RY = -113.5, 50.0, 29.0      # curly puff (head-local); lobes ring the oval
PUFF_LOBE_R = 16.0


def _puff_geom(H):
    s = H.s
    cx = -10.0 * s - H.nod * 10.0 * s
    cy = PUFF_CY - H.nod_dy * 0.45
    ph = H.th * 0.9
    lobes = []
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n + ph
        r = PUFF_LOBE_R + 2.5 * math.sin(i * 2.3 + 1.0)
        lobes.append((cx + (PUFF_RX - 4.0) * math.cos(a), cy + PUFF_RY * math.sin(a), r, a))
    return cx, cy, lobes


def _draw_puff(c, H):
    cx, cy, lobes = _puff_geom(H)
    path = skia.Path()
    path.addOval(skia.Rect(cx - PUFF_RX, cy - PUFF_RY - 5.0, cx + PUFF_RX, cy + PUFF_RY + 5.0), skia.PathDirection.kCCW)
    for bx, by, r, a in lobes:
        path.addCircle(bx, by, r, skia.PathDirection.kCCW)
    c.drawPath(path, paint(C_HAIR_SH, 0.85, stroke=2.6))
    sh = skia.GradientShader.MakeLinear([(cx, cy - 36), (cx, cy + 46)], [C_HAIR, C_HAIR, C_HAIR_SH], [0.0, 0.45, 1.0])
    c.drawPath(path, paint(None, shader=sh))
    hl = skia.GradientShader.MakeRadial((cx - 16, cy - 16), 30, [col(C_HAIR_HI, 0.55), col(C_HAIR_HI, 0.0)])
    c.drawCircle(cx - 16, cy - 16, 30, paint(None, shader=hl))
    # curl arcs, batched into a few paths (one draw each)
    hi_strong, hi_soft, shade = skia.Path(), skia.Path(), skia.Path()
    for bx, by, r, a in lobes:
        lit = -math.sin(a) * 0.75 - math.cos(a) * 0.55
        rr = r * 0.6
        tgt = shade if lit <= 0.0 else (hi_strong if lit > 0.45 else hi_soft)
        tgt.addArc(skia.Rect(bx - rr, by - rr, bx + rr, by + rr), 160, 140)
    inner_hi, inner_sh = skia.Path(), skia.Path()
    for (ix, iy, rr, a0) in ((-22, -12, 9, 150), (8, -18, 10, 170), (26, -1, 9, 190), (-6, 4, 10, 160),
                             (-34, 6, 8, 150), (16, 14, 8, 200)):
        (inner_hi if iy < 0 else inner_sh).addArc(skia.Rect(cx + ix - rr, cy + iy - rr, cx + ix + rr, cy + iy + rr), a0, 130)
    _stroke(c, hi_strong, C_HAIR_HI, 2.3, 0.85)
    _stroke(c, hi_soft, C_HAIR_HI, 2.3, 0.55)
    _stroke(c, shade, C_HAIR_SH, 2.0, 0.5)
    _stroke(c, inner_hi, C_HAIR_HI, 2.0, 0.55)
    _stroke(c, inner_sh, C_HAIR_SH, 2.0, 0.55)


def _draw_hair_cap(c, H, head_out, head_grow=None):
    region, hl_pts = _hair_region(H)
    if region is None:
        return None
    # hair volume tapers to nothing where the hairline meets the silhouette (no wedge at the temple)
    head_grow = _head_outline(H, grow=4.0, gy=(hl_pts[0][1] - 4.0, hl_pts[-1][1] - 4.0))
    hair = skia.Op(head_grow, region, skia.PathOp.kIntersect_PathOp)
    sh_reg = skia.Path(region)
    sh_reg.offset(-0.8, 3.6)
    shadow = skia.Op(head_out, sh_reg, skia.PathOp.kIntersect_PathOp)
    _fill(c, shadow, C_SKIN_SH, 0.55, blur=1.2)
    gx = -26.0 - 14.0 * H.s
    sh = skia.GradientShader.MakeRadial((gx, -58.0), 118.0, [C_HAIR, C_HAIR, C_HAIR_SH], [0.0, 0.55, 1.0])
    c.drawPath(hair, paint(None, shader=sh))
    s = H.s
    tie = (-4.0 * s, -90.0 - H.nod_dy * 0.4)
    strands = skia.Path()
    for ph in (-60, -44, -28, -12, 4, 20, 36, 52, 66):
        x, y, vis = _surf_az(H, ph, _hairline_y(ph) - 2.0)
        if vis <= 0.15:
            continue
        mx, my, _ = _surf_az(H, ph * 0.8, -72.0)
        _cr(strands, [(x, y - 3.0), (mx, my), (tie[0] + ph * 0.16, tie[1] + 6)])
    _stroke(c, strands, C_HAIR_HI, 1.1, 0.3)
    # curved sheen band following the skull contour (light from the upper left)
    lx0 = -_sil_x(H, -20.0, -1)
    rx0 = _sil_x(H, -20.0, 1)
    gcx, gcy, grx, gry = (rx0 - lx0) * 0.5, -22.0, (rx0 + lx0) * 0.5, 68.0
    sp = []
    for i in range(7):
        a = (198.0 + i * 13.0) * D2R
        sp.append((gcx + grx * 0.84 * math.cos(a), gcy + gry * 0.84 * math.sin(a)))
    widths = [1.0 + 9.0 * math.sin(math.pi * (i + 0.15) / 6.3) ** 1.3 for i in range(7)]
    _fill(c, _ribbon(sp, widths), C_HAIR_HI, 0.85, blur=2.6)
    _fill(c, _ribbon(sp[1:-1], [w * 0.35 for w in widths[1:-1]]), C_HAIR_SHEEN, 0.55, blur=1.0)
    _stroke(c, hair, C_HAIR_SH, 1.5, 0.75)
    for sg in (-1, 1):
        x, y, vis = _surf_az(H, sg * 60.0, _hairline_y(60.0) + 0.5)
        if vis > 0.3:
            d = 1.0 if (sg > 0) else -1.0
            _stroke(c, _curve([(x - d * 4, y - 3), (x - d * 1, y + 1.5), (x + d * 3, y + 1.0), (x + d * 1.5, y - 1.5),
                               (x - d * 0.5, y + 0.3)]), C_HAIR, 1.1, 0.85)
    return hl_pts


def _lock(c, x, y, out, length, width, phase, sway, waves=1.15, amp=4.6):
    """One chunky S-shaped curl: a tapered ribbon whose centre line snakes side to side, ending in a
    small hook, with a soft highlight on the bulges that face the light (upper-left)."""
    n = 16
    pts, wid = [], []
    for i in range(n + 1):
        u = i / n
        a = phase + u * 2.0 * math.pi * waves
        am = amp * (1.0 - 0.3 * u)
        pts.append((x + out * (1.0 + 5.5 * u) + am * math.sin(a) * out + sway * u * u, y + u * length))
        wid.append(width * min(1.0, 0.4 + u * 4.0) * (1.0 - 0.7 * u ** 1.3))
    # pointed root tucked into the hairline
    r0, r1 = pts[0], pts[1]
    dx, dy = _norm(r0[0] - r1[0], r0[1] - r1[1])
    pts.insert(0, (r0[0] + dx * 3.5, r0[1] + dy * 3.5))
    wid.insert(0, 0.8)
    # tip hook: curls back under itself
    tx, ty = pts[-1]
    hk = -out if math.cos(phase + 2.0 * math.pi * waves) * out > 0 else out
    pts.append((tx + hk * 2.6, ty + 2.4))
    pts.append((tx + hk * 3.4, ty + 0.4))
    wid += [wid[-1] * 0.8, 0.6]
    rib = _ribbon(pts, wid)
    c.drawPath(rib, paint(C_HAIR_SH, 0.9, stroke=1.6))
    _fill(c, rib, C_HAIR)
    # highlight on the lit side of each bulge (where the curl turns toward the light), one batched stroke
    hl = skia.Path()
    for i in range(2, n):
        a = phase + ((i - 1) / n) * 2.0 * math.pi * waves
        lit = -math.cos(a) * out
        if lit > 0.3:
            q0, q1 = pts[i - 1], pts[i + 1]
            w = wid[i] * 0.2
            _cr(hl, [(q0[0] - w, q0[1] - 0.4), (pts[i][0] - w, pts[i][1] - 0.4), (q1[0] - w, q1[1] - 0.4)])
    _stroke(c, hl, C_HAIR_SHEEN, max(0.9, width * 0.22), 0.5)


def _draw_ringlet(c, H, slot, t, far=False):
    """Loose curls framing the face at the temple: two S-shaped locks. The far-side locks hang from
    behind the cheek (drawn before the skin so only the part outside the silhouette shows)."""
    s = abs(H.s)
    ph = slot * (66.0 + (40.0 * s if far else 0.0))
    x, y, vis = _surf_az(H, ph, _hairline_y(ph) - 1.0)
    if not far and vis < -0.1:
        return
    sway = math.sin(t * 1.6 + slot) * 1.4
    out = float(slot)
    _lock(c, x + out * 1.5, y + 1.0, out, 32.0, 6.2, 1.9 + slot * 0.4, sway * 0.7, waves=1.0, amp=4.0)
    _lock(c, x - out * 1.0, y + 1.0, out, 50.0, 8.6, 0.3, sway, waves=1.3, amp=5.4)


def _draw_bang(c, H, t):
    """One loose curl springing from the hairline onto the forehead."""
    x, y, vis = _surf_az(H, -16.0, _hairline_y(-16.0) - 3.0)
    if vis <= 0.25:
        return
    sw = math.sin(t * 1.3) * 0.7
    pts = []
    for i in range(14):
        u = i / 13.0
        a = -0.6 + u * 5.2
        r = 6.2 * (1.0 - 0.55 * u)
        pts.append((x - 3.0 + sw * u + r * math.cos(a) * 0.85, y + 6.0 + u * 5.0 + r * math.sin(a)))
    pts.insert(0, (x + 1.0, y - 1.5))
    widths = [lerp(4.6, 1.4, (i / (len(pts) - 1)) ** 0.8) for i in range(len(pts))]
    _fill(c, _ribbon(pts, widths), C_HAIR)
    _stroke(c, _curve(pts[1:7]), C_HAIR_HI, 0.9, 0.6)


def _draw_cap_and_tie(c, H, head_out):
    _draw_hair_cap(c, H, head_out)
    _draw_scrunchie(c, H)


def _draw_scrunchie(c, H):
    """Fabric scrunchie around the base of the puff: a thick gathered band along the near (lower) half of a
    ring above eye level; overlapping soft puffs share one outline so it reads as one ruffled tube whose ends
    turn away behind the hair."""
    s = H.s
    tx, ty = -4.0 * s - 8.0 * s * max(0.0, H.nod), -90.5 - H.nod_dy * 0.4
    rx, ry = 26.0, 4.5 + 2.0 * H.nod
    ph0 = H.th * 0.8
    n = 9
    band = skia.Path()
    pts = []
    for i in range(n):
        u = i / (n - 1)
        th_ = (4.0 + 172.0 * u) * D2R + 0.05 * math.sin(ph0)
        e = math.sin(th_)
        x, y = tx + rx * math.cos(th_), ty + ry * e
        w, h = 6.8 * (0.55 + 0.45 * e), (5.6 + 0.6 * math.sin(i * 2.1 + ph0)) * (0.78 + 0.22 * e)
        band.addOval(skia.Rect(x - w, y - h, x + w, y + h))
        pts.append((x, y, w, h, e))
    c.drawPath(band, paint(C_HAIR_SH, 0.85, stroke=3.0))
    sh = skia.GradientShader.MakeLinear([(tx, ty - 6.0), (tx, ty + ry + 6.0)], [C_TIE_HI, C_TIE, C_TIE_SH], [0.0, 0.38, 1.0])
    c.drawPath(band, paint(None, shader=sh))
    # soft gathers between the puffs and a sheen along the top
    for i in range(1, n - 1, 1):
        x, y, w, h, e = pts[i]
        xg = x + w * 0.62
        _stroke(c, _curve([(xg - 0.6, y - h * 0.7), (xg + 0.7, y + 0.2), (xg - 0.2, y + h * 0.75)]), C_TIE_SH, 1.0, 0.45 * e)
    _stroke(c, _curve([(x, y - h * 0.55) for x, y, w, h, e in pts[2:-2]]), WHITE, 1.3, 0.22)


# --------------------------------------------------------------------------- head assembly
def _draw_head(c, R, p, t):
    H = R.H
    tt = t if t is not None else 0.0
    P = _NS()
    P.squint = clamp(p.squint + 0.22 * max(0.0, p.smile))
    P.wide = clamp(p.eye_wide)
    P.gx = clamp(p.look_x * R.fac, -1.2, 1.2)
    P.gy = clamp(p.look_y, -1.0, 1.0)
    P.pupil = clamp(p.pupil, 0.5, 1.6)
    P.tears = clamp(p.tears)
    P.shine = clamp(p.eye_shine)
    P.sniffle = clamp(p.sniffle)
    bl = blink(t)
    lids = {s_: (clamp(v) if v is not None else bl) for s_, v in (("l", p.lid_l), ("r", p.lid_r))}
    mgeom = _mouth_geom(H, p, t) if not R.back else None
    head_out = _head_outline(H, mext=_mouth_extent(H, mgeom) if (mgeom is not None and abs(H.s) > 0.3) else None)
    hkey = (round(H.th, 3), round(H.nod_dy, 2))
    _cached(c, ("puff",) + hkey, skia.Rect(-140, -230, 140, -40), lambda cv: _draw_puff(cv, H))
    far_slots = [sl for sl in (-1, 1) if sl * H.s > 0.08] if not R.back else []
    for slot in far_slots:
        _draw_ringlet(c, H, slot, tt, far=True)
    for slot in (-1, 1):
        if H.s * slot > 0.12 or abs(H.s) <= 0.12:
            _draw_ear(c, H, slot)
    # skin with a soft cel-like form shadow on the far side / jaw: an elliptical radial gradient
    # centred toward the light (no clipping needed)
    ys = (-90.0, 67.0)
    a0 = _prof(0.0)[0]
    lft = -math.sqrt(a0 * a0 * H.c * H.c + _prof(0.0)[2] ** 2 * max(H.s, 0) ** 2)
    rgt = math.sqrt(a0 * a0 * H.c * H.c + _prof(0.0)[1] ** 2 * max(H.s, 0) ** 2)
    rx, ry = (rgt - lft) * 0.5, (ys[1] - ys[0]) * 0.5
    fcx = (lft + rgt) * 0.5 - 0.1 * rx - 3.0 * max(H.s, 0.0)
    fcy = (ys[0] + ys[1]) * 0.5 - 0.1 * ry + H.nod_dy * 0.3
    lm = skia.Matrix()
    lm.setScale(rx / ry, 1.0, fcx, fcy)
    shade = skia.GradientShader.MakeRadial((fcx, fcy), ry * 1.06, [C_SKIN, C_SKIN, C_SKIN_SH, C_SKIN_SH],
                                           [0.0, 0.88, 0.95, 1.0], skia.TileMode.kClamp, 0, lm)
    c.drawPath(head_out, paint(None, shader=shade))
    c.save()
    c.clipPath(head_out, doAntiAlias=False)
    if not R.back:
        for slot in (-1, 1):
            bx, by, dep, fs = _hx(H, slot * 34.0, 24.0)
            if dep > -5:
                a = 0.12 + 0.5 * clamp(p.blush) + 0.3 * P.sniffle
                rr = 13.0
                sh = skia.GradientShader.MakeRadial((bx, by), rr, [col(C_BLUSH, a), col(C_BLUSH, 0.0)])
                c.save()
                c.translate(bx, by)
                c.scale(max(fs, 0.3), 0.62)
                c.translate(-bx, -by)
                c.drawCircle(bx, by, rr, paint(None, shader=sh))
                c.restore()
        hx_, hy_, _, _ = _hx(H, -31.0, 13.0)
        c.drawOval(skia.Rect(hx_ - 9, hy_ - 4, hx_ + 6, hy_ + 3), paint(C_SKIN_HI, 0.4, blur=4))
        fx_, fy_, _, _ = _hx(H, -14.0, -36.0)
        c.drawOval(skia.Rect(fx_ - 13, fy_ - 6, fx_ + 11, fy_ + 5), paint(C_SKIN_HI, 0.3, blur=6))
        cx_, cy_, _, _ = _hx(H, -4.0, 62.0)
        c.drawOval(skia.Rect(cx_ - 6, cy_ - 2.5, cx_ + 4, cy_ + 2), paint(C_SKIN_HI, 0.3, blur=2.5))
    c.restore()
    _stroke(c, head_out, C_SKIN_LINE, 1.6, 0.8)
    _cached(c, ("cap",) + hkey, skia.Rect(-120, -140, 120, 60), lambda cv: _draw_cap_and_tie(cv, H, head_out))
    for slot in (-1, 1):
        if H.s * slot < -0.12:
            _draw_ear(c, H, slot)
    if R.back:
        return
    c.save()
    c.clipPath(head_out, doAntiAlias=True)
    lashes = []
    for slot in (-1, 1):
        side = "r" if slot < 0 else "l"
        E = _NS()
        E.__dict__.update(P.__dict__)
        E.lash_out = lashes
        E.lid = lids[side]
        E.emit = R.emit
        E.tear_roll = clamp(p.tear_r if side == "r" else p.tear_l)
        xs = 1.0 if slot > 0 else -1.0
        E.braise = clamp(p.brow_raise + 0.25 * P.wide - 0.45 * p.smirk * xs, -1.2, 1.4)
        E.bworry = clamp(p.brow_worry)
        E.bfurrow = clamp(p.brow_furrow)
        _draw_eye(c, H, E, slot, t)
        _draw_brow(c, H, E, slot)
    _draw_nose(c, H, P)
    _draw_mouth(c, H, p, t, mgeom)
    c.restore()
    for lash in lashes:          # upper lash lines are not clipped: the far flick may poke past the cheek
        lash(c)
    for slot in (-1, 1):
        if slot not in far_slots:
            _draw_ringlet(c, H, slot, tt)
    _draw_bang(c, H, tt)


# --------------------------------------------------------------------------- main draw
def _draw_body(c, R, p, t):
    near, far = R.arms[-1], R.arms[1]
    legs = R.legs
    # seated near the front view both thighs come toward the camera: the far leg also goes over the hips
    # (cross-faded over turn 0.05..0.12 so there is no pop)
    front_k = 0.0 if R.back else (R.sw + R.k) * (1.0 - smoothstep((abs(R.turn) - 0.05) / 0.07))
    far_late = far.layer == "back" and far.on_leg > 0.5      # far hand resting on the far knee / thigh
    c.save()
    c.concat(R.MU)
    for A in (far, near):
        if A.layer == "behind":
            _draw_arm(c, A, R)
    if far.layer == "back" and not far_late and far.front_w < 0.995:
        _draw_arm(c, far, R)
    c.restore()
    if front_k < 0.995:
        _draw_leg(c, legs[1], R)
    if far_late:
        c.save()
        c.concat(R.MU)
        _draw_arm(c, far, R)
        c.restore()
    _draw_hips(c, R)
    if front_k > 0.005:
        if front_k < 0.995:
            L = legs[1]
            xs = [L.hip[0], L.knee[0], L.ankle[0]]
            ys = [L.hip[1], L.knee[1], L.ankle[1]]
            c.saveLayerAlpha(skia.Rect(min(xs) - 60, min(ys) - 40, max(xs) + 60, max(ys) + 40), int(255 * front_k))
            _draw_leg(c, L, R)
            c.restore()
        else:
            _draw_leg(c, legs[1], R)
    _draw_leg(c, legs[-1], R)
    c.save()
    c.concat(R.MU)
    _draw_neck(c, R)
    _draw_torso(c, R)
    c.restore()
    c.save()
    c.concat(R.MH)
    _draw_head(c, R, p, t)
    c.restore()
    c.save()
    c.concat(R.MU)
    R.occluders = []
    if far.layer == "back" and far.front_w > 0.005 and not far_late:
        # front view: the far arm hangs beside the body in front of it, like the near arm (cross-faded)
        if far.front_w < 0.995:
            xs = [far.S[0], far.E[0], far.W[0], far.palm[0]]
            ys = [far.S[1], far.E[1], far.W[1], far.palm[1]]
            c.saveLayerAlpha(skia.Rect(min(xs) - 40, min(ys) - 40, max(xs) + 40, max(ys) + 40), int(255 * far.front_w))
            _draw_arm(c, far, R)
            c.restore()
        else:
            _draw_arm(c, far, R)
    for A in (far, near):
        if A is near and A.layer == "front":
            _call_before_near_arm(c, R, skia.Matrix.Concat(R.MS, R.MU))
        if (A is far and A.layer == "over") or (A is near and A.layer == "front"):
            _draw_arm(c, A, R)
            if R.emit is not None:
                R.occluders.append(_arm_occluder(A, R))
    c.restore()
    _call_before_near_arm(c, R, R.MS)      # near arm not in the front pass (behind the back): after everything


def _call_before_near_arm(c, R, frame):
    """Run draw()'s before_near_arm callable once (stage coordinates: the canvas as the caller passed it in;
    the body's lighting colour filter is suspended so the caller's own paints / layers are not filtered twice).
    `frame` is the local transform currently on the canvas (MS, or MS * MU inside the arm pass)."""
    global _CF, _CF_KEY
    fn = getattr(R, "before_near_arm", None)
    if fn is None:
        return
    R.before_near_arm = None
    cf, key = _CF, _CF_KEY
    _CF, _CF_KEY = None, None
    c.save()
    inv = skia.Matrix()
    if frame.invert(inv):
        c.concat(inv)
    try:
        fn(c)
    finally:
        c.restore()
        _CF, _CF_KEY = cf, key


def _light_cf(pose):
    # perceptual response: light 0.25 still leaves faces readable (~0.41 linear) in the dark scenes
    return light_filter(max(0.0, pose.light) ** 0.65, pose.tint, pose.tint_amt)


def _bounds(R):
    """Tight local-frame bounding rect of the character (for layers)."""
    pts = []
    for x, y in ((-80, -190), (80, -190), (-80, 85), (80, 85)):
        q = R.MH.mapXY(x, y)
        pts.append((q.fX, q.fY))
    for A in R.arms.values():
        for x, y in (A.S, A.E, A.W, A.palm):
            q = R.MU.mapXY(x, y)
            pts.append((q.fX, q.fY))
    if R.mug is not None:
        q = R.MU.mapXY(R.mug.x, R.mug.y - MUG_H * MUG_S * 0.5)
        pts.append((q.fX, q.fY))
    for L in R.legs.values():
        pts += [L.hip, L.knee, L.ankle]
    pad = 50.0
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    return skia.Rect(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


_NATIVE_CT = skia.Surface(1, 1).imageInfo().colorType()


def _premul_image(a, color):
    """skia.Image (native pixel order, premultiplied) of `color` with per-pixel alpha array a (float 0..1)."""
    h, w = a.shape
    r, g, b = skia.ColorGetR(color), skia.ColorGetG(color), skia.ColorGetB(color)
    out = np.empty((h, w, 4), np.uint8)
    if _NATIVE_CT == skia.kBGRA_8888_ColorType:
        chans = (b, g, r)
    else:
        chans = (r, g, b)
    for i, cv in enumerate(chans):
        out[:, :, i] = a * cv
    out[:, :, 3] = a * 255.0
    return skia.Image.fromarray(out, colorType=_NATIVE_CT, alphaType=skia.kPremul_AlphaType)


def _draw_rimlit(c, R, pose, t, rim):
    """Rim-lit render. The character is drawn once into an offscreen image (device pixels, tight bounds).
    Behind it goes a soft glow (silhouette tinted with rim_color, blurred at 1/4 resolution, nudged toward the
    light, cut at the floor line); on top goes a thin bright edge on the side facing the light: the silhouette
    minus itself shifted toward the light by a fixed ~2.5 device px (so it stays a hairline at any zoom).
    The light direction is fixed in screen space: from the head toward RIM_LIGHT_POS (the window).
    A before_near_arm callable is kept out of the silhouette (no rim on it): it is drawn over the finished rim-lit
    character, and the near arm (with its share of the rim edge) is drawn again over it."""
    hook = getattr(R, "before_near_arm", None)
    R.before_near_arm = None
    M = c.getTotalMatrix()
    dscale = math.sqrt(abs(M.getScaleX() * M.getScaleY() - M.getSkewX() * M.getSkewY()))
    rc = col(pose.rim_color)
    dev = M.mapRect(_bounds(R))
    clipb = c.getDeviceClipBounds()
    bx0 = max(math.floor(dev.left()), clipb.left())
    by0 = max(math.floor(dev.top()), clipb.top())
    bx1 = min(math.ceil(dev.right()), clipb.right())
    by1 = min(math.ceil(dev.bottom()), clipb.bottom())
    if bx1 <= bx0 or by1 <= by0:
        if hook is not None:                   # she is out of view; what goes with her may not be
            R.before_near_arm = hook
            _call_before_near_arm(c, R, R.MS)
        return
    # light direction in device space
    hx, hy, _, _ = _hx(R.H, 0.0, 0.0)
    hq = R.MH.mapXY(hx, hy)
    hs_ = R.MS.mapXY(hq.fX, hq.fY)
    if RIM_LIGHT_POS is not None:
        lx, ly = _norm(RIM_LIGHT_POS[0] - hs_.fX, RIM_LIGHT_POS[1] - hs_.fY)
    else:
        lx, ly = 0.0, -1.0
    inv_ms = skia.Matrix()
    Mstage = M
    if R.MS.invert(inv_ms):
        Mstage = skia.Matrix.Concat(M, inv_ms)
    dv = Mstage.mapVector(lx, ly)
    lx, ly = _norm(dv.fX, dv.fY)
    if lx == 0.0 and ly == 0.0:
        lx, ly = 0.0, -1.0
    floor_dev = M.mapXY(0.0, 0.0).fY
    w, h = int(bx1 - bx0), int(by1 - by0)
    surf = skia.Surface(w, h)
    oc = surf.getCanvas()
    oc.translate(-bx0, -by0)
    oc.concat(M)
    _draw_body(oc, R, pose, t)
    img = surf.makeImageSnapshot()
    # ---- soft glow (low resolution: ~4 stage units per sample at any zoom), behind the character, cut at the
    # floor. Blurred with scipy on the tiny alpha mask (skia's CPU blur filter is several times slower here).
    q = clamp(4.0 * dscale, 4.0, 12.0)
    padg = 36.0 * dscale
    gx0, gy0 = bx0 - padg, by0 - padg
    gw, gh = int((w + 2 * padg) / q) + 2, int((h + 2 * padg) / q) + 2
    small = skia.Surface(gw, gh)
    sc = small.getCanvas()
    sc.scale(1.0 / q, 1.0 / q)
    sc.drawImage(img, padg, padg)
    msk = np.empty((gh, gw), np.uint8)
    small.makeImageSnapshot().readPixels(skia.ImageInfo.MakeA8(gw, gh), msk, gw)
    af = msk.astype(np.float32) * (1.0 / 255.0)
    g = (0.5 * rim) * gaussian_filter(af, 16.0 * dscale / q) + (0.7 * rim) * gaussian_filter(af, 5.5 * dscale / q)
    # back-light bloom: strong on the side facing the light, fading off toward the far side
    ext = 0.5 * (abs(gw * lx) + abs(gh * ly))
    tt = ((np.arange(gw, dtype=np.float32)[None, :] - gw * 0.5) * lx +
          (np.arange(gh, dtype=np.float32)[:, None] - gh * 0.5) * ly) / max(ext, 1.0)
    g *= np.interp(tt, (-1.0, -0.1, 0.7), (0.12, 0.55, 1.0)).astype(np.float32)
    np.clip(g, 0.0, 1.0, out=g)
    glow_img = _premul_image(g, rc)
    c.save()
    c.resetMatrix()
    c.save()
    c.clipRect(skia.Rect(-1e5, -1e5, 1e5, floor_dev - 1.5 * dscale))
    off = 5.0 * dscale
    c.drawImageRect(glow_img, skia.Rect(gx0 + lx * off, gy0 + ly * off, gx0 + lx * off + gw * q, gy0 + ly * off + gh * q),
                    skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()
    # ---- the character (already light-filtered while drawing)
    c.drawImage(img, bx0, by0, skia.SamplingOptions())
    # ---- thin rim edge on the light side: silhouette minus the silhouette shifted toward the light. With the
    # light above (the usual case) only the upper body catches it: the edge pass stops below the hips, fading.
    dpx = 2.6
    ox, oy = round(lx * dpx), round(ly * dpx)
    if ox == 0 and oy == 0:
        oy = -2
    he = h
    if ly < -0.3:
        hip_dev = M.mapXY(0.0, -R.hv).fY
        he = int(clamp(hip_dev - by0 + 30.0 * dscale, 8.0, float(h)))
    eh = skia.Surface(w, he)
    ec = eh.getCanvas()
    ec.drawImage(img, 0, 0)
    dp = skia.Paint()
    dp.setBlendMode(skia.BlendMode.kDstOut)
    ec.drawImage(img, -ox, -oy, skia.SamplingOptions(), dp)
    if he < h:
        fp = skia.Paint()
        fp.setBlendMode(skia.BlendMode.kDstIn)
        y0f = max(0.0, he - 70.0 * dscale)
        fp.setShader(skia.GradientShader.MakeLinear([(0, y0f), (0, he)], [col("#FFFFFF"), col("#FFFFFF", 0.0)]))
        ec.drawRect(skia.Rect(0, y0f, w, he), fp)
    ep = skia.Paint()
    ep.setColorFilter(skia.ColorFilters.Blend(rc, skia.BlendMode.kSrcIn))
    ep.setAlphaf(min(1.0, 1.15 * rim))
    eimg = eh.makeImageSnapshot()
    c.drawImage(eimg, bx0, by0, skia.SamplingOptions(), ep)
    c.restore()
    if hook is not None:
        R.before_near_arm = hook
        _call_before_near_arm(c, R, R.MS)
        near = R.arms[-1]
        if near.layer == "front":
            # the near arm (and its rim edge) again, only where it covers what the hook drew
            hsurf = skia.Surface(w, h)
            hc = hsurf.getCanvas()
            hc.translate(-bx0, -by0)
            hc.concat(M)
            R.before_near_arm = hook
            _call_before_near_arm(hc, R, R.MS)
            himg = hsurf.makeImageSnapshot()
            mp = skia.Paint()
            mp.setBlendMode(skia.BlendMode.kDstIn)
            asurf = skia.Surface(w, h)
            ac = asurf.getCanvas()
            ac.save()
            ac.translate(-bx0, -by0)
            ac.concat(M)
            ac.concat(R.MU)
            _draw_arm(ac, near, R)
            ac.restore()
            ac.drawImage(himg, 0, 0, skia.SamplingOptions(), mp)
            aimg = asurf.makeImageSnapshot()
            es = skia.Surface(w, he)
            e2 = es.getCanvas()
            e2.drawImage(eimg, 0, 0)
            e2.drawImage(aimg, 0, 0, skia.SamplingOptions(), mp)
            c.save()
            c.resetMatrix()
            c.drawImage(aimg, bx0, by0, skia.SamplingOptions())
            c.drawImage(es.makeImageSnapshot(), bx0, by0, skia.SamplingOptions(), ep)
            c.restore()

def draw(canvas, pose: Pose, t: float, before_near_arm=None):
    """Draw Rae. The canvas must already carry the camera transform (stage coordinates).
    before_near_arm: optional callable(canvas) drawn (in stage coordinates) after her body, legs, head and far arm
    and just before her near arm - e.g. a mug standing on the bench that her near hand is in front of while it
    lets go of it / picks it up. It never catches her rim light (pose.rim). None (default) draws exactly as
    before."""
    global _CF, _CF_KEY
    R = _solve(pose, t)
    R.before_near_arm = before_near_arm
    c = canvas
    c.save()
    c.concat(R.MS)
    lit = pose.light != 1.0 or pose.tint_amt > 0
    R.emit = [] if pose.light < 0.95 else None
    _CF = _light_cf(pose) if lit else None
    _CF_KEY = (round(pose.light, 3), tuple(pose.tint), round(pose.tint_amt, 3)) if lit else None
    try:
        rim = clamp((pose.rim - RIM_MIN) / (1.0 - RIM_MIN))
        if rim > 0.004:
            _draw_rimlit(c, R, pose, t, rim)
        else:
            _draw_body(c, R, pose, t)
    finally:
        _CF = None
        _CF_KEY = None
    if R.emit:
        # eye glints stay bright in low light (reflections of the window / ribbons)
        a = clamp(0.85 * (1.0 - pose.light) / 0.75)
        c.concat(R.MH)
        inv = skia.Matrix()
        occ = []
        if getattr(R, "occluders", None) and R.MHr.invert(inv):
            for o_ in R.occluders:
                q = skia.Path(o_)
                q.transform(inv)
                occ.append(q)
        for opening, glint in R.emit:
            c.save()
            c.clipPath(opening, doAntiAlias=True)
            for q in occ:
                c.clipPath(q, skia.ClipOp.kDifference, True)
            c.saveLayerAlpha(None, int(255 * a))
            glint(c)
            c.restore()
            c.restore()
    c.restore()


# --------------------------------------------------------------------------- presets
ARMS = {
    "rest": ArmPose(shoulder=5.0, elbow=12.0, wrist=0.0, hand="relaxed"),
    "hold_mug": ArmPose(shoulder=10.0, elbow=84.0, wrist=0.0, hand="hold", across=0.22),
    "sip": ArmPose(shoulder=56.0, elbow=104.0, wrist=0.0, hand="hold", across=0.38),
    "mug_raise": ArmPose(shoulder=48.0, elbow=78.0, wrist=0.0, hand="hold", across=0.0),
    "point": ArmPose(shoulder=76.0, elbow=10.0, wrist=0.0, hand="point"),
    "hand_on_chest": ArmPose(shoulder=12.0, elbow=118.0, wrist=10.0, hand="open", across=0.58),
    "wipe_eye": ArmPose(shoulder=88.0, elbow=130.0, wrist=16.0, hand="fist", across=0.3),
    "cover_mouth": ArmPose(shoulder=60.0, elbow=100.0, wrist=4.0, hand="open", across=0.48),
    "hands_up": ArmPose(shoulder=28.0, elbow=104.0, wrist=-14.0, hand="palm_out", across=-0.25),
    "grip_knee": ArmPose(shoulder=42.0, elbow=4.0, wrist=12.0, hand="fist"),
    "reach_back": ArmPose(shoulder=-42.0, elbow=14.0, wrist=-10.0, hand="open"),
    "shrug": ArmPose(shoulder=14.0, elbow=96.0, wrist=-12.0, hand="palm_up", across=-0.8),
    "hug_self": ArmPose(shoulder=22.0, elbow=128.0, wrist=8.0, hand="relaxed", across=1.0),
    "knee_rest": ArmPose(shoulder=40.0, elbow=8.0, wrist=34.0, hand="relaxed"),
}

# Face presets: Pose field overrides (scenes: pose.copy(**EXPR["awe"]) or expr(pose, "awe", 0.5)).
EXPR = {
    "neutral": dict(),
    "tired": dict(lid_l=0.52, lid_r=0.5, brow_raise=-0.15, brow_worry=0.15, smile=-0.1, look_y=0.15, head_nod=-0.15),
    "skeptical": dict(smirk=0.7, smile=0.1, brow_furrow=0.2, lid_l=0.72, lid_r=0.72, look_y=0.05, head_tilt=-3.0),
    "frozen_sip": dict(lid_l=0.8, lid_r=0.8, look_x=0.85, look_y=-0.05, brow_raise=0.15),
    "confused": dict(brow_furrow=0.55, brow_raise=0.45, mouth_open=0.18, mouth_round=0.5, smile=-0.15, head_tilt=-6.0,
                     squint=0.1),
    "shocked": dict(eye_wide=1.0, brow_raise=1.0, mouth_open=0.7, mouth_round=0.55, pupil=0.85),
    "awe": dict(pupil=1.3, eye_shine=1.0, brow_raise=0.5, brow_worry=0.35, mouth_open=0.22, mouth_round=0.25,
                lid_l=0.95, lid_r=0.95, look_y=-0.3, head_nod=0.25),
    "moved": dict(tears=0.7, brow_worry=0.8, brow_raise=0.2, pupil=1.2, eye_shine=0.6, mouth_open=0.1, smile=-0.1,
                  look_y=-0.25, lid_l=0.9, lid_r=0.9),
    "tear_smile": dict(tears=0.8, tear_r=0.6, brow_worry=0.75, smile=0.45, mouth_tremble=0.7, eye_shine=0.5,
                       pupil=1.15, squint=0.2, lid_l=0.85, lid_r=0.85),
    "laugh_cry": dict(smile=0.95, mouth_open=0.55, squint=0.65, tears=0.75, brow_worry=0.6, brow_raise=0.25,
                      lid_l=0.55, lid_r=0.55, tear_l=0.4, blush=0.4),
    "sob": dict(squint=0.8, brow_worry=1.0, brow_furrow=0.25, lid_l=0.05, lid_r=0.05, mouth_open=0.4, smile=-0.7,
                mouth_tremble=0.8, tears=0.9, tear_r=0.7, blush=0.35, sniffle=0.5),
    "rapid_blink": dict(lid_l=0.18, lid_r=0.22, brow_raise=0.7, eye_wide=0.0),
    "sniffly_point": dict(sniffle=0.85, tears=0.45, brow_furrow=0.35, brow_worry=0.3, lid_l=0.78, lid_r=0.78, smile=0.05,
                          mouth_open=0.12),
    "dread": dict(eye_wide=0.5, brow_worry=0.7, brow_raise=0.4, smile=-0.35, mouth_open=0.08, look_y=0.1),
    "grin": dict(smile=1.0, mouth_open=0.35, squint=0.35, brow_raise=0.3, blush=0.2),
}


def expr(pose: Pose, name: str, amount: float = 1.0, t=None) -> Pose:
    """Blend face preset `name` into pose by `amount` (a lid of None counts as fully open when blending).
    Pass t (the draw time) to keep the natural blink running on the preset's lid levels during holds;
    without t the lids are static values (the preset as a still)."""
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
