"""ANGER - the huge, grim armored warrior (BIBLE.md section 2). Procedural 2D rig (skia), same contract as the
other films' rigs (anim/rig.py).

Public API
    draw(canvas, pose, t)            draw Anger; the canvas already carries the camera (stage units)
    head_center(pose, t=None)        stage point between the eyes (pass the draw time t to the anchors so the
                                     automatic breathing / sway / state animation match the drawing)
    hand_pos(pose, side, t=None)     palm centre of the 'l' / 'r' gauntlet; holding a prop = its grip point
    torch_pos(pose, t=None)          centre of the held torch's flame (the scene's light source), None without a torch
    sword_tip_pos(pose, t=None)      blade point; in 'sword_drag' the point where the blade enters the wall
    eye_pos(pose, side, t), mouth_pos(pose, t), pelvis_pos(pose, t)
    face_pos(pose, x0, y0, t=None)   any spot on the face from front-view head coords (x0 > 0 = Anger's LEFT, y0 down
                                     from the eye line: eyes (+-20.5, 0), nose tip (0, 18), mouth (0, 38),
                                     cheekbones (+-30, 12), beard bottom (0, 84)) - drips, saliva, a cut ...
    near_side(pose) -> 'r' | 'l'     which side of Anger is nearer the camera
    blink(t)                         his heavy, slow auto blink (what lid_l / lid_r = None use)
    ARMS                             ArmPose presets: rest, torch_high, torch_up, torch_near, sword_low, sword_guard,
                                     chop_windup, chop_strike, swipe_gather, swipe_back, door_grip, run_pump,
                                     hang_reach, sword_both_hands_thrust, weak_raise, wipe_face, cross_arms, swat,
                                     prop_rest, fist, shield_up, fall_up, flail, lie_side
    EXPR, EXPR_EXTRA, expr(pose, name, amount=1.0, t=None)   face presets: grim, listen, scan, stoic_close, startled,
                                     pain, dazed, strain, flat, eye_roll, squint, smirk, smirk_suppressed, deadpan,
                                     exhausted, side_eye, confused, contemplate, raised_brow, one_eye
                                     (pass t so the preset's lid levels keep the heavy blink)
    HEIGHT = 820                     floor -> crown, standing, scale 1
    WALK_CYCLE = 1.10 s, RUN_CYCLE = 0.62 s (BIBLE: fixed cadence; a footfall every half cycle)
    WALK_ADVANCE = 300, RUN_ADVANCE = 560: stage units per cycle (scale 1, turn >= 0.4) so planted feet do not skate;
    walk_advance(pose) = the same for the pose's state / turn / scale (front views advance less: 0.3x at turn 0)
    phase_at(state, t, t0, phase0), cycle_len(state)
    step_times(state, t0, t1, phase0=0) -> foot-plant times (walk/run/charge: right foot at phase 0, left at 0.5;
                                     chop: the stamp at phase 0.5; stumble: slip 0.25 + recovery 0.62, with phase
                                     running phase0 -> 1 over [t0, t1])
    step_events(state, t0, t1, phase0=0, gain_db=-6) -> [{"name": "armor_step" | "armor_step_run", "start", ...}]
    STATES                           the body states below
    Loose props for scenes (same art, stage coords):
    draw_torch(canvas, x, y, angle=0, t, scale=1, flame=1, light=1, glow=True)  grip at (x, y), angle = degrees from
                                     up of the burning end (+ clockwise); the flame always rises; torch_flame_offset()
    draw_flame(canvas, x, y, t, scale=1, intensity=1, wind=(0, 0))   just the flame (e.g. an emissive pass)
    draw_sword(canvas, x, y, angle=180, scale=1, light=1, tint, tint_amt, embed=0)  grip centre at (x, y), angle of
                                     the point from up (90 = right); embed hides that fraction of the blade (in rock);
                                     sword_wall_point(x, y, angle, scale, embed) = where it enters the rock
    draw_shield(canvas, x, y, scale=1, squash=1, angle=0, light=1, back_side=False)

pose.extra keys (all optional)
    state        "stand" (default; "walk" when pose.walk is set), "walk", "run", "chop", "swipe", "door_push",
                 "charge", "stumble", "hang", "fall", "sword_drag", "crumpled", "lie_back", "prop_sit", "sleep"
    state_b, mix blend toward a second state: every body parameter (joint angles, pelvis, body rotation, cloth wind,
                 arm overrides) is interpolated, e.g. state="lie_back", state_b="prop_sit", mix=0..1 (propping up);
                 stand -> walk (start / stop walking); sleep <-> prop_sit (waking); fall -> crumpled ...
    phase        walk / run / charge: cycle phase in cycles (or pose.walk); chop / swipe / stumble: 0..1 progress;
                 door_push: 0..1 per try (0-0.5 pull, 0.5-1 push), cycles allowed. phase_b: the same for state_b.
    torch        None | "l" | "r": torch held in that hand (flickering flame, warm glow, key light from it);
                 torch_flame 0..1 (0 = out); torch_angle: override the torch direction (deg from up, + = toward facing)
    sword        "hand" (default, in sword_hand = "r") | "back" ("sheathed": scabbard on his back, hilt over the right
                 shoulder) | "in_wall" (not drawn with him - draw it with draw_sword) | None;
                 sword_angle (deg from up, + toward facing) overrides the blade direction;
                 two_hand: the off hand closes on the grip (sword_drag does this itself)
    shield       "back" (default: round shield on his back, peeking past the silhouette) | "arm" (left forearm) | None
    cross_arms   0..1 blends both arms into crossed arms (near forearm on top); combine with sword="back"
    arms_w       0..1 weight of the state's own arm animation (0 = use pose.arm_l / arm_r unchanged), default 1
    one_eye      0..1 only the eye nearer the camera opens (the far one stays squeezed shut)
    smirk_suppress 0..1 fights pose.smirk: corner twitching back, lips pressed, a little squint
    bruised      0..1 dust smudges, scrapes, a cut over his right brow, dust on the armor
    dazed        0..1 unfocused, drifting, slightly divergent eyes, heavy fluttering lids
    grimace      0..1 clenched teeth (pain / effort); strain 0..1 effort brows + squint (hanging, sword_drag)
    brow_l, brow_r  extra raise per brow (-1..1.5) on top of brow_raise: a single raised eyebrow = brow_l=1
    Per state:   chop: sword_hand; swipe: swipe_side ("r"); door_push: grip_side ("r"), ring=(x, y) stage point the
                 gripping hand holds (default 176 forward, 462 up from the floor point); charge: lead ("r" shoulder);
                 stumble: slip_foot ("r"); hang: hang_hand ("l"), swing (deg, 5), kick 0..1, slip 0..1;
                 fall: tumble (deg), fall_speed (900, drives the cloth); sword_drag: sword_tilt (8 deg, tip down),
                 embed (0.78), shake (1); prop_sit / sleep: knee_up 0..1 (0.55); sleep: sleep_tilt (deg, 15)
    reach_l / reach_r = (x, y) stage point (+ reach_l_w 0..1): IK that hand's palm onto a point
    key_dir      cel-shading light direction (screen angle deg toward the light, or (x, y)); default: from the held
                 torch when lit, else from the front-above
    rim_dir / rim_pos   rim light direction (screen angle deg toward the light: 0 = from the right, -90 = from above;
                 or a vector) or a stage point the light comes from (e.g. torch_pos(...)); default behind-above

Pose fields used: x, y, scale, facing, turn (0..0.9), lean, head_tilt, head_nod, head_turn, breath (None = auto, big
chest), lid_l/lid_r (None = heavy auto blink), look_x/look_y, pupil, squint, eye_wide, brow_raise, brow_worry,
brow_furrow, mouth_open/mouth_round (lip-sync; the beard follows the jaw), smile, smirk (> 0 = the corner nearer the
camera), mouth_tremble, arm_l/arm_r (ArmPose), shoulders_up, bounce, walk, light/tint/tint_amt (colour filter on every
paint), rim/rim_color. Not used: back, sit, seat_y, kneel, foot_tap, mug, tears, blush, glow, process, sniffle.

Conventions
    * l / r are Anger's TRUE sides (sword in the right hand, torch in the left, scar through the LEFT eyebrow) for both
      facings: facing -1 is not a pure mirror. With facing +1 his right side is nearer the camera (near_side()).
      torch_high suits the FAR hand (facing +1 with the torch in the left hand); with the torch in the near hand
      use torch_up (straight up) or torch_near, otherwise the raised arm crosses his face.
    * (pose.x, pose.y) = the floor point under the pelvis (stand, walk, run, actions, fall: the body rotates / tumbles
      about the pelvis 398 above it, lie_back / crumpled / prop_sit / sleep: the floor he lies or sits on).
      hang: (x, y) = where the gripping gauntlet's fingers curl over the ledge edge (the body dangles below).
      sword_drag: (x, y) = where the embedded blade enters the wall (the wall face is at x, on the facing side).
    * lie_back / crumpled are side views (body turn >= 0.8, head at the end AWAY from facing: screen-left for facing
      +1); pose.turn + head_turn then only turn the HEAD toward the camera (turn 0.35 shows his face). hang and
      sword_drag force body turn >= 0.62; fall keeps pose.turn.
    * ArmPose angles are relative to the chest: 0 = hanging, 90 = forward (toward facing), 180 = up; elbow + bends
      the forearm forward/up; wrist rotates the gauntlet (a held prop's axis = hand direction + 60 deg). across pulls
      the hand toward / across the chest or face (0.5 midline, 1 opposite shoulder); behind tucks it behind the back.
      Near the front view arms swing out to the sides. In lying / sitting states the angles stay body-relative
      ("rest" lies along his side, weak_raise points at the ceiling).
    * A near arm raised high beside the head (hang, sword_drag, torch_up, swat) is drawn UNDER the head so the face
      stays readable; a far hand that comes to the face (wipe_face, across) is drawn over it.
    * Walking backward: decrease phase while x moves against facing. Footsteps: step_times / step_events.
    * Lighting: light/tint go through core.light_filter on every paint; rim renders him offscreen (~+10 ms);
      flames are emissive (never darkened) and in dark poses (light < 0.95) the eye catch-lights are re-drawn
      un-darkened so his eyes read.
"""
from __future__ import annotations

import math

import skia

from anim.core import breathe, clamp, col, hash01, lerp, light_filter, mix_col, noise1, smoothstep
from anim.core import paint as _core_paint
from anim.rig import ArmPose, Pose

D2R = math.pi / 180.0

# =========================================================================== proportions (stage units, scale 1)
HEIGHT = 820.0            # floor -> crown of the shaved head, standing
TURN_DEG = 80.0           # yaw (deg) per unit of pose.turn / head_turn
ANKLE_H = 30.0            # ankle joint above the sole
THIGH = 190.0
SHIN = 184.0
HIP_H = 398.0             # standing hip-joint height (knees a hair flexed)
HIP_LAT = 50.0            # half distance between the hip joints (front view)
NECK_Y = -668.0           # base of the neck / top of the torso (upright body coords, floor = 0)
WAIST_Y = -490.0          # spine bend pivot
SH_X = 120.0              # shoulder joint half spacing (front view)
SH_DY = 44.0              # shoulder joints below the neck base
UPPER = 166.0             # upper arm
FORE = 150.0              # forearm
PALM = 31.0               # wrist -> palm centre
NECK_PIVOT = (6.0, -716.0)  # head pivot (upright body coords, x = forward depth offset at turn 1)
EYE_ABOVE_PIVOT = 46.0    # eye line above the head pivot
HEAD_S = 1.0
HAND_S = 1.16             # gauntlet drawing scale (hand-local design units -> body units)

WALK_CYCLE = 1.10         # seconds per walk cycle (a heavy footfall every 0.55 s)
RUN_CYCLE = 0.62          # seconds per run / charge cycle
WALK_STANCE = 0.60        # fraction of the cycle a foot is planted (walk)
RUN_STANCE = 0.38
WALK_ADVANCE = 300.0      # stage units the body moves per walk cycle (scale 1, turn >= 0.4)
RUN_ADVANCE = 560.0       # per run cycle
WALK_S = 0.5 * WALK_ADVANCE * WALK_STANCE      # foot travel half-range relative to the pelvis
RUN_S = 0.5 * RUN_ADVANCE * RUN_STANCE

SWORD_BLADE = 330.0       # blade length (guard -> point)
SWORD_GRIP = 66.0
TORCH_LEN = 236.0
TORCH_GRIP = 78.0         # hand -> butt end distance along the torch
PROP_GRIP_DEG = 60.0      # a held prop's axis = hand direction + this (the grip runs diagonally in the fist)

# =========================================================================== colours
C_SKIN = col("a_skin")
C_SKIN_SH = col("a_skin_shade")
C_SKIN_HI = col("a_skin_hi")
C_SKIN_LINE = col("#4A2414")
C_SKIN_DEEP = col("#7A4630")
C_LID = mix_col("a_skin", "a_skin_shade", 0.55)
C_SOCKET = col("#4E2A1A")
C_LIP = col("#A0604C")
C_LIP_SH = col("#7A4234")
C_MOUTH = col("#2A0E0C")
C_TEETH = col("#E8DFCF")
C_TONGUE = col("#8E3A3A")
C_BEARD = col("a_beard")
C_BEARD_SH = col("#22140C")
C_BEARD_HI = col("#5E402C")
C_HAIR = col("a_hair")
C_BROW = col("#24150D")
C_SCAR = col("a_scar")
C_SCAR_HI = col("#E7B79A")
C_SCLERA = col("#D3C7B9")
C_SCLERA_SH = col("#8E7C70")
C_IRIS = col("#3E2414")
C_IRIS_DK = col("#1A0E08")
C_IRIS_LT = col("a_eye")
C_PUPIL = col("#120A06")
C_LASH = col("#1A0E08")
C_STEEL = col("a_steel")
C_STEEL_SH = col("a_steel_shade")
C_STEEL_HI = col("a_steel_hi")
C_STEEL_DK = col("#3C424C")
C_STEEL_LINE = col("#1C2027")
C_LEATHER = col("a_leather")
C_LEATHER_SH = col("#3C2416")
C_LEATHER_HI = col("#7E5438")
C_LEATHER_LINE = col("#22140C")
C_CLOTH = col("a_cloth")
C_CLOTH_SH = col("#4A1814")
C_CLOTH_HI = col("#8E3C30")
C_CLOTH_LINE = col("#260A08")
C_GOLD = col("a_gold")
C_GOLD_SH = col("#8A6A28")
C_GOLD_HI = col("#F4DC92")
C_PANTS = col("#3A2C26")
C_PANTS_SH = col("#251B17")
C_SLEEVE = col("#4A3024")
C_SLEEVE_SH = col("#2F1E16")
C_WOOD = col("wood")
C_WOOD_DK = col("wood_dark")
C_IRON = col("iron")
C_IRON_DK = col("#2C2F35")
C_BLOOD = col("blood")
C_DUST = col("#9C8C78")
WHITE = col("#FFFFFF")

# =========================================================================== lighting state (per draw)
_CF = None            # colour filter applied to every paint while Anger is drawn (pose.light / tint)
_CF_KEY = None
_LIGHT = (-0.55, -0.83)   # screen-space unit vector toward the key light (cel shading direction)
_PAINT_CACHE = {}


def paint(color, alpha=1.0, **kw):
    """core.paint + the current lighting colour filter (plain paints are cached)."""
    if kw.get("shader") is None and kw.get("blend") is None:
        key = (color, round(alpha, 3), kw.get("stroke", 0.0), kw.get("blur", 0.0), kw.get("cap", "round"), _CF_KEY)
        p = _PAINT_CACHE.get(key)
        if p is None:
            p = _core_paint(color, alpha, **kw)
            if _CF is not None:
                p.setColorFilter(_CF)
            if len(_PAINT_CACHE) > 8000:
                _PAINT_CACHE.clear()
            _PAINT_CACHE[key] = p
        return p
    p = _core_paint(color, alpha, **kw)
    if _CF is not None:
        p.setColorFilter(_CF)
    return p


_LV_CACHE = [None, None, (0.0, -1.0)]


def _lv(c, k=1.0):
    """The key-light direction expressed in the canvas' current local coordinates, length k."""
    M = c.getTotalMatrix()
    key = (M.getScaleX(), M.getSkewX(), M.getSkewY(), M.getScaleY())
    if key == _LV_CACHE[0] and _LIGHT == _LV_CACHE[1]:
        ux, uy = _LV_CACHE[2]
        return ux * k, uy * k
    inv = skia.Matrix()
    if not M.invert(inv):
        return 0.0, -k
    v = inv.mapVector(_LIGHT[0], _LIGHT[1])
    n = math.hypot(v.fX, v.fY)
    u = (0.0, -1.0) if n < 1e-9 else (v.fX / n, v.fY / n)
    _LV_CACHE[0], _LV_CACHE[1], _LV_CACHE[2] = key, _LIGHT, u
    return u[0] * k, u[1] * k


# =========================================================================== geometry helpers
class _NS:
    pass


def _cr(path, pts, move=True, tension=0.5):
    """Append an open Catmull-Rom curve through pts."""
    n = len(pts)
    if n == 0:
        return path
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


def _loop(pts, tension=0.5):
    """Closed Catmull-Rom loop."""
    n = len(pts)
    p = skia.Path()
    if n < 3:
        return p
    k = tension / 3.0
    p.moveTo(pts[0][0], pts[0][1])
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        p.cubicTo(p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
                  p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1])
    p.close()
    return p


def _poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def _closed2(a, b, tension=0.5):
    p = skia.Path()
    _cr(p, a, True, tension)
    _cr(p, b, False, tension)
    p.close()
    return p


def _norm(x, y):
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def _ribbon(center, widths, tension=0.5):
    n = len(center)
    L, R = [], []
    for i in range(n):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        nx, ny = _norm(-(b[1] - a[1]), b[0] - a[0])
        w = widths[i] * 0.5
        L.append((center[i][0] + nx * w, center[i][1] + ny * w))
        R.append((center[i][0] - nx * w, center[i][1] - ny * w))
    return _closed2(L, R[::-1], tension)


def _capsule(a, b, ra, rb, bulge=0.0, at=0.5, path=None):
    """Tapered limb outline (rounded ends) as ONE closed contour (strokable without simplify)."""
    p = path if path is not None else skia.Path()
    dx, dy = b[0] - a[0], b[1] - a[1]
    ux, uy = _norm(dx, dy)
    if ux == 0 and uy == 0:
        p.addCircle(a[0], a[1], max(ra, rb))
        return p
    nx, ny = -uy, ux
    m = (a[0] + dx * at, a[1] + dy * at)
    rm = lerp(ra, rb, at) + bulge
    pts = []
    for k in range(7):                       # end cap at b (half circle)
        ang = -math.pi / 2 + math.pi * k / 6
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append((b[0] + (ux * ca - nx * sa) * rb * 1.0 + 0, b[1] + (uy * ca - ny * sa) * rb))
    side2 = [(m[0] - nx * rm, m[1] - ny * rm)]
    cap_a = []
    for k in range(7):
        ang = math.pi / 2 + math.pi * k / 6
        ca, sa = math.cos(ang), math.sin(ang)
        cap_a.append((a[0] + (ux * ca - nx * sa) * ra, a[1] + (uy * ca - ny * sa) * ra))
    side1 = [(m[0] + nx * rm, m[1] + ny * rm)]
    _cr(p, pts + side2 + cap_a + side1 + [pts[0]], True, 0.45)
    p.close()
    return p


def _ik(a, b, l1, l2, prefer):
    """2-bone IK: the joint between a and b; prefer(j1, j2) picks a solution."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return (a[0], a[1] + l1)
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


def _dirv(a_deg):
    """Unit vector for an angle measured from straight DOWN, + rotating toward forward (+x): 90 = forward."""
    a = a_deg * D2R
    return math.sin(a), math.cos(a)


def _ang_of(dx, dy):
    """Inverse of _dirv."""
    return math.atan2(dx, dy) / D2R


def _fill(c, path, color, alpha=1.0, blur=0.0):
    c.drawPath(path, paint(color, alpha, blur=blur))


def _stroke(c, path, color, width, alpha=1.0, blur=0.0, cap="round"):
    c.drawPath(path, paint(color, alpha, stroke=width, blur=blur, cap=cap))


def _axis_scale(c, cx, cy, ux, uy, r, f, frac=1.0):
    """Concat a matrix that scales by f along the unit axis u about the point centre + u * r * frac."""
    px, py = cx + ux * r * frac, cy + uy * r * frac
    ang = math.degrees(math.atan2(uy, ux))
    c.translate(px, py)
    c.rotate(ang)
    c.scale(f, 1.0)
    c.rotate(-ang)
    c.translate(-px, -py)


def _cel(c, path, base, shade, k=6.0, blur=0.0, line=None, line_w=1.4, line_a=0.85, hi=None, hi_k=None, hi_a=0.5):
    """Cel shading with solid fills only (fast on the CPU rasteriser): the shade colour, then copies of the shape
    squeezed toward the key light along the light axis - a shade band ~k*1.6 wide stays on the far side; blur > 0
    adds an intermediate tone (soft terminator); hi adds a small highlight band on the lit side."""
    if line is not None:
        c.drawPath(path, paint(line, line_a, stroke=line_w * 2.0))
    c.drawPath(path, paint(shade))
    b = path.getBounds()
    cx, cy = 0.5 * (b.fLeft + b.fRight), 0.5 * (b.fTop + b.fBottom)
    lx, ly = _lv(c, 1.0)
    r = 0.5 * (abs(lx) * (b.fRight - b.fLeft) + abs(ly) * (b.fBottom - b.fTop)) + 0.5
    f = clamp(1.0 - 1.6 * k / (2.0 * r), 0.3, 0.97)
    if blur > 0:
        c.save()
        _axis_scale(c, cx, cy, lx, ly, r, min(0.99, f + 0.35 * (1 - f)))
        c.drawPath(path, paint(mix_col(_rgb_of(base), _rgb_of(shade), 0.5)))
        c.restore()
    c.save()
    _axis_scale(c, cx, cy, lx, ly, r, f)
    c.drawPath(path, paint(base))
    c.restore()
    if hi is not None:
        c.save()
        _axis_scale(c, cx, cy, lx, ly, r, 0.22, 0.92)
        c.drawPath(path, paint(hi, hi_a))
        c.restore()


def _rgb_of(cc):
    if not isinstance(cc, int):
        cc = col(cc)
    return (skia.ColorGetR(cc), skia.ColorGetG(cc), skia.ColorGetB(cc))


def _metal(c, path, p0, p1, line=True, base=None, shade=None, hi=None, lw=1.5, dark=None, gloss=1.0):
    """Steel plate with solid fills: dark far edge, shade, base, and a bright specular band toward the key light,
    all squeezed copies of the plate along its width axis p0 -> p1 (so a vambrace keeps its length)."""
    base = C_STEEL if base is None else base
    shade = C_STEEL_SH if shade is None else shade
    hi = C_STEEL_HI if hi is None else hi
    dark = C_STEEL_DK if dark is None else dark
    if line:
        c.drawPath(path, paint(C_STEEL_LINE, 0.9, stroke=lw * 2.0))
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    r = 0.5 * math.hypot(ax, ay)
    if r < 1e-3:
        c.drawPath(path, paint(base))
        return
    ux, uy = ax / (2 * r), ay / (2 * r)
    cx, cy = 0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1])
    lx, ly = _lv(c, 1.0)
    d = lx * ux + ly * uy
    if d < 0:
        ux, uy, d = -ux, -uy, -d
    c.drawPath(path, paint(shade))
    c.save()
    _axis_scale(c, cx, cy, ux, uy, r, 0.7, 1.0)
    c.drawPath(path, paint(base))
    c.restore()
    c.save()
    _axis_scale(c, cx, cy, ux, uy, r, 0.16 * gloss, 0.5 + 0.25 * d)
    c.drawPath(path, paint(hi, 0.9))
    c.restore()


def _rivet(c, x, y, r=2.6, color=None):
    color = C_GOLD if color is None else color
    c.drawCircle(x, y, r + 0.9, paint(C_STEEL_LINE, 0.7))
    c.drawCircle(x, y, r, paint(color))
    if r >= 2.4:
        lx, ly = _lv(c, r * 0.4)
        c.drawCircle(x + lx, y + ly, r * 0.42, paint(C_GOLD_HI, 0.85))


def _soft_oval(c, x, y, rx, ry, color, alpha):
    """Soft blob without a blur filter: two nested translucent ovals."""
    c.drawOval(skia.Rect(x - rx, y - ry, x + rx, y + ry), paint(color, alpha * 0.45))
    c.drawOval(skia.Rect(x - rx * 0.6, y - ry * 0.6, x + rx * 0.6, y + ry * 0.6), paint(color, alpha * 0.55))


def _rot(p, ang_deg, o=(0.0, 0.0)):
    a = ang_deg * D2R
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * ca - y * sa, o[1] + x * sa + y * ca)


def _mp(M, p):
    q = M.mapXY(p[0], p[1])
    return (q.fX, q.fY)


# =========================================================================== blink / timing
def blink(t, seed=3):
    """Anger's heavy, slow blink (1 open .. 0 shut): every ~5.2 s, ~0.32 s long, lids linger a moment."""
    if t is None:
        return 1.0
    rate = 5.2
    k = math.floor(t / rate)
    for kk in (k - 1, k, k + 1):
        bt = kk * rate + hash01(kk, seed) * rate * 0.55
        dt = t - bt
        dur = 0.30 + 0.08 * hash01(kk, seed + 7)
        if 0 <= dt < dur:
            x = dt / dur
            if x < 0.32:
                return 1.0 - math.sin(x / 0.32 * math.pi / 2)
            if x < 0.45:
                return 0.0
            return 1.0 - math.cos((x - 0.45) / 0.55 * math.pi / 2)
    return 1.0


# =========================================================================== head geometry
# Head-local frame: origin on the head's vertical axis at eye level, y down, x = front-view across (-x = the
# side nearer the camera once turned toward +x). A cross-section at height y is two half-ellipses:
# half-width a, front depth zf, back depth zb. Above y = -12 the skull is an ellipsoid dome.
_HCAP = (-14.0, 41.0, 47.0, 49.0, 56.0)
_HTAB = [(-14.0, 47.0, 49.0, 56.0), (-6.0, 46.5, 50.0, 54.0), (2.0, 46.0, 50.0, 49.0), (10.0, 47.5, 49.0, 43.0),
         (18.0, 47.5, 48.0, 37.0), (26.0, 46.5, 47.0, 31.0), (34.0, 45.0, 45.0, 25.0), (42.0, 42.0, 43.0, 19.0),
         (50.0, 37.0, 40.0, 13.0), (56.0, 30.0, 37.0, 8.0), (60.5, 21.0, 34.0, 4.0), (63.5, 10.0, 31.0, 1.0)]
_HOUT_YS = [-55.0, -54.0, -51.5, -47.0, -41.0, -34.0, -26.0, -19.0, -12.0, -5.0, 2.0, 9.0, 16.0, 23.0, 30.0,
            38.0, 46.0, 53.0, 58.5, 62.0, 63.5]
# leading-edge (profile) offsets: brow ridge, eye-socket notch, cheekbone
_HBUMP = [(-26.0, 0.0), (-17.0, 2.4), (-11.0, 5.0), (-6.0, 3.6), (-1.0, -1.6), (5.0, -1.2), (11.0, 1.8),
          (18.0, 1.2), (26.0, 0.0)]
EX = 20.5            # eye centre offset
EW = 9.8             # eye half width
HU0, HL0 = 4.7, 3.7  # open upper / lower lid heights (heavy, deep-set)
RI = 5.9             # iris radius
MOUTH_Y = 38.0


def _tab(tab, y):
    if y <= tab[0][0]:
        return tab[0][1:]
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0 = tab[i - 1][0]
            u = (y - y0) / (tab[i][0] - y0)
            return tuple(a + (b - a) * u for a, b in zip(tab[i - 1][1:], tab[i][1:]))
    return tab[-1][1:]


def _hprof(y):
    cy, ry, A, ZF, ZB = _HCAP
    if y <= cy:
        q = (y - cy) / ry
        k = math.sqrt(max(0.0, 1.0 - q * q))
        return A * k, ZF * k, ZB * k
    return _tab(_HTAB, y)


def _bumpv(tab, y):
    if y <= tab[0][0] or y >= tab[-1][0]:
        return 0.0
    for i in range(1, len(tab)):
        if y < tab[i][0]:
            y0, v0 = tab[i - 1]
            y1, v1 = tab[i]
            return v0 + (v1 - v0) * smoothstep((y - y0) / (y1 - y0))
    return 0.0


def _jaw(H, y):
    return H.jaw * 14.0 * smoothstep((y - 33.0) / 12.0) if y > 33.0 else 0.0


def _hp(H, x0, y, dz=0.0):
    """Face-surface point given in front-view coords (+ extra depth dz) -> (x, y, depth) in head-local coords."""
    a, zf, _ = _hprof(y)
    u = clamp(x0 / max(a, 1e-3), -0.995, 0.995)
    z = zf * math.sqrt(1.0 - u * u) + dz
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    return x, y + H.ndy * dep / 50.0 + _jaw(H, y), dep


def _hpp(H, x0, y, dz=0.0):
    p = _hp(H, x0, y, dz)
    return (p[0], p[1])


def _haz(H, phi_deg, y, dr=0.0, prof=None):
    """Surface point at azimuth phi (0 = front centre, +90 = the +x side) -> (x, y, visibility)."""
    a, zf, zb = prof if prof is not None else _hprof(y)
    ph = phi_deg * D2R
    sp, cp = math.sin(ph), math.cos(ph)
    zz = zf if cp >= 0 else zb
    x0, z = (a + dr) * sp, (zz + dr) * cp
    x = x0 * H.c + z * H.s
    dep = -x0 * H.s + z * H.c
    vis = -sp / max(a + dr, 1e-3) * H.s + cp / max(zz + dr, 1e-3) * H.c
    return x, y + H.ndy * dep / 50.0 + _jaw(H, y), vis * 50.0


def _hsil(H, y, side, prof=None, bump=True):
    a, zf, zb = prof if prof is not None else _hprof(y)
    z = zf if side * H.s >= 0 else zb
    x = math.sqrt(a * a * H.c * H.c + z * z * H.s * H.s)
    if bump and side * H.s > 0:
        x += _bumpv(_HBUMP, y) * min(1.0, abs(H.s) * 2.2)
    return side * x


def _head_outline(H):
    R, L = [], []
    for y in _HOUT_YS:
        dy = _jaw(H, y)
        R.append((_hsil(H, y, 1), y + dy))
        L.append((_hsil(H, y, -1), y + dy))
    return _closed2(R, L[::-1])


# --------------------------------------------------------------------------- beard volume
_BEARD_LOW = [(56.0, 40.0, 46.0), (66.0, 38.0, 45.0), (76.0, 35.0, 43.0), (82.0, 32.0, 41.0), (85.0, 29.0, 39.0),
              (86.5, 26.0, 37.0)]
_BTOP = [(-97.0, -5.0), (-90.0, 0.5), (-80.0, 7.0), (-68.0, 13.5), (-55.0, 18.5), (-42.0, 22.0), (-29.0, 25.0),
         (-16.0, 27.0), (-6.0, 28.0), (0.0, 28.4)]
_BBOT = [(97.0, 46.0), (89.0, 59.0), (77.0, 71.0), (62.0, 79.0), (42.0, 83.6), (21.0, 85.6), (0.0, 86.2)]
_BTOP_FULL = _BTOP + [(-p, y) for p, y in reversed(_BTOP[:-1])]
_BBOT_FULL = _BBOT + [(-p, y) for p, y in reversed(_BBOT[:-1])]


def _bprof(y, H=None):
    """Beard surface radii (a, zf, zb) at level y: the head + a growing thickness, hanging below the chin."""
    if y <= 56.0:
        a, zf, zb = _hprof(y)
        th = lerp(2.0, 8.5, clamp((y + 5.0) / 61.0))
        bulk = H.bulk if H is not None else 1.0
        th *= bulk
        return a + th, zf + th, zb + th
    a, zf = _tab(_BEARD_LOW, y)
    return a, zf, 12.0


def _bside(H, side, y):
    a, zf, zb = _bprof(y, H)
    x, yy, vis = _haz(H, side * 97.0, y, 0.0, (a, zf, zb))
    if vis > 0.0:
        return (x, yy)
    return (_hsil(H, y, side, (a, zf, zb), bump=False), y + H.ndy * 0.0 + _jaw(H, y))


def _beard_outline(H):
    top = []
    sm_s, sm_k = getattr(H, "sm", (0, 0.0))
    for phi, y in _BTOP_FULL:
        if sm_k > 0 and phi * sm_s > 0:
            y -= 3.5 * sm_k * math.exp(-((abs(phi) - 42.0) / 22.0) ** 2)
        x, yy, vis = _haz(H, phi, y, 0.0, _bprof(y, H))
        if vis > 0.5:
            top.append((x, yy, y))
    bot = []
    for phi, y in _BBOT_FULL:
        x, yy, vis = _haz(H, phi, y, 0.0, _bprof(y, H))
        if vis > 0.5:
            bot.append((x, yy, y))
    if not top or not bot:
        return None
    pts = [(p[0], p[1]) for p in top]
    # leading (+x when turned that way) side: from the last top point down to the first bottom point
    y0, y1 = top[-1][2], bot[0][2]
    n = max(2, int((y1 - y0) / 7.0))
    for i in range(1, n):
        pts.append(_bside(H, 1, lerp(y0, y1, i / n)))
    pts += [(p[0], p[1]) for p in bot]
    y0, y1 = bot[-1][2], top[0][2]
    n = max(2, int((y0 - y1) / 7.0))
    for i in range(1, n):
        pts.append(_bside(H, -1, lerp(y0, y1, i / n)))
    return _loop(pts, 0.45)


# --------------------------------------------------------------------------- face parameters
def _face_params(p: Pose, R, t):
    """Resolve the face controls (pose fields + extra keys + body state) into per-eye / mouth values."""
    ex = p.extra
    F = _NS()
    tt = t if t is not None else 0.0
    bl = blink(t)
    fac = R.fac
    dazed = clamp(ex.get("dazed", 0.0))
    one = clamp(ex.get("one_eye", 0.0))
    sup = clamp(ex.get("smirk_suppress", 0.0))
    F.dazed, F.one, F.sup = dazed, one, sup
    # the smile reaching the eyes: even the tiny S6 smirk (0.38) gets all of it; suppression takes it away again
    warm = smoothstep(clamp(abs(p.smirk) * (1.0 - 0.75 * sup) / 0.32))
    F.warm = warm
    F.bruised = clamp(ex.get("bruised", 0.0))
    F.grimace = clamp(ex.get("grimace", 0.0))
    F.strain = clamp(ex.get("strain", 0.0))
    sleepk = R.sleep
    F.squint = clamp(p.squint + 0.25 * F.grimace + 0.2 * F.strain + 0.15 * sup)
    F.wide = clamp(p.eye_wide)
    F.pupil = clamp(p.pupil * (1.0 + 0.25 * dazed) * (1.0 - 0.25 * F.wide), 0.5, 1.6)
    gx = clamp(p.look_x * fac, -1.25, 1.25)
    gy = clamp(p.look_y, -1.0, 1.0)
    F.slot_l = 1 if fac > 0 else -1          # local slot of Anger's LEFT eye / brow (the scarred one)
    F.eye = {}
    for slot in (-1, 1):
        side = "l" if slot == F.slot_l else "r"
        E = _NS()
        lid = getattr(p, "lid_" + side)
        lv = (1.0 if lid is None else clamp(lid))
        if lid is None:
            lv *= bl
        lv *= (1.0 - 0.38 * dazed) * (1.0 - sleepk if lid is None else 1.0) * (1.0 - 0.05 * warm)
        if dazed > 0:
            # slow, heavy, out-of-sync lid flutter
            lv *= 1.0 - 0.22 * dazed * (0.5 + 0.5 * noise1(tt * 0.9, 41 + slot))
        if slot > 0:                             # the far eye stays shut with one_eye
            lv *= 1.0 - one
        E.lid = clamp(lv)
        sm_side = (-1 if p.smirk >= 0 else 1) == slot
        E.squint = clamp(F.squint + (0.3 * one if slot > 0 else 0.0) + (0.4 * abs(p.smirk) if sm_side else 0.0)
                         + (0.2 + (0.06 if sm_side else 0.0)) * warm)       # cheeks push the lower lids up
        E.wide = F.wide * (1.0 if slot < 0 or one < 0.5 else 0.0)
        dgx = dazed * (0.32 * slot + 0.35 * noise1(tt * 0.33, 7 + 3 * slot))
        dgy = dazed * 0.3 * noise1(tt * 0.27, 19 + slot)
        E.gx = clamp(gx * (1.0 - 0.5 * dazed) + dgx, -1.3, 1.3)
        E.gy = clamp(gy * (1.0 - 0.4 * dazed) + dgy + 0.15 * dazed, -1.0, 1.0)
        braise = p.brow_raise + float(ex.get("brow_" + side, 0.0))
        braise += 0.25 * F.wide + (0.35 * one if slot < 0 else -0.15 * one)
        braise += 0.12 * dazed - 0.25 * F.strain + 0.1 * warm
        E.braise = clamp(braise, -1.2, 1.5)
        E.bworry = clamp(p.brow_worry + 0.35 * dazed + 0.25 * F.strain + 0.15 * F.grimace + 0.05 * warm)
        # warm: the brows relax - the default scowl (0.3) un-knots and the inner ends stop pulling down
        E.bfurrow = clamp(0.3 + p.brow_furrow + 0.45 * F.grimace + 0.35 * F.strain - 0.3 * max(0.0, braise)
                          - 0.2 * dazed + 0.12 * sup - 0.42 * warm)
        E.side = side
        F.eye[slot] = E
    F.open = clamp(p.mouth_open + R.mouth_add)
    F.round = clamp(p.mouth_round)
    F.smile = clamp(p.smile + 0.16 * warm, -1.0, 1.0)      # a hint of the OTHER corner too: warm, not a sneer
    sm = p.smirk * (1.0 - 0.75 * sup)
    F.smirk_slot = -1 if sm >= 0 else 1      # smirk > 0 lifts the corner nearer the camera
    F.smirk = abs(sm)
    F.tremble = clamp(p.mouth_tremble)
    F.t = tt
    return F


# --------------------------------------------------------------------------- eyes
def _bump01(s, pk, e):
    q = (s - pk) / (1.0 - pk) if s >= pk else (s - pk) / (1.0 + pk)
    v = 1.0 - q * q
    return v ** e if v > 0 else 0.0


_ES = [-1.0, -0.82, -0.58, -0.32, -0.06, 0.2, 0.46, 0.7, 0.88, 1.0]
_EU = [_bump01(s, -0.18, 0.55) for s in _ES]
_EL = [_bump01(s, 0.12, 0.8) for s in _ES]
_EB = [lerp(1.4, 0.6, (s + 1) / 2) for s in _ES]


def _eye_curves(E):
    hu = HU0 * (1.0 + 0.78 * E.wide)
    hl = HL0 * (1.0 + 0.15 * E.wide)
    if E.gy > 0:
        hu *= 1.0 - 0.3 * E.gy           # looking down: the upper lid follows the eye
    else:
        hu *= 1.0 - 0.08 * E.gy
    U, L, C = [], [], []
    for b, pu, pl in zip(_EB, _EU, _EL):
        u = b - hu * pu
        l_ = b + hl * pl - E.squint * (hl + 0.4 * HU0) * (pl ** 0.85)
        l_ = max(l_, u + 0.8 * pu)
        cl = b + 0.42 * hl * pl - 0.5 * E.squint * hl * pl
        cl = max(cl, u + 0.5 * pu)
        U.append(u)
        L.append(l_)
        C.append(min(cl, l_))
    op = clamp(E.lid)
    UL = [c_ + (u - c_) * op for u, c_ in zip(U, C)]
    return U, L, C, UL, op


def _draw_eye(c, H, F, slot, emit):
    E = F.eye[slot]
    sd = float(slot)
    cx = sd * EX
    ex_, ey_, dep = _hp(H, cx, 0.0, -3.0)
    if dep < -8:
        return None
    U, L, C, UL, op = _eye_curves(E)
    xs = [cx + sd * s * EW for s in _ES]

    def P(x0, v, dz=-3.0):
        return _hpp(H, x0, v, dz)

    pL = [P(x, v) for x, v in zip(xs, L)]
    pUL = [P(x, v) for x, v in zip(xs, UL)]
    # deep socket: soft shadow under the brow ridge and around the eye
    sock = [P(cx + sd * s * (EW + 3.5), v - 2.5 - 4.5 * pu, -1.0) for s, v, pu in zip(_ES, U, _EU)]
    sock_lo = [P(cx + sd * s * (EW + 2.0), v + 2.5 + 2.5 * pl, -1.0) for s, v, pl in zip(_ES, L, _EL)]
    _fill(c, _closed2(sock, sock_lo[::-1]), C_SOCKET, 0.5 + 0.1 * F.bruised, blur=3.4)
    brs = [P(cx + sd * s * (EW + 5.0), -9.5 - 2.5 * math.sin((s + 1) * 1.57), 2.0) for s in _ES]
    _fill(c, _closed2(brs, [P(x, v - 1.0) for x, v in zip(xs, U)][::-1]), C_SOCKET, 0.42, blur=2.4)
    # heavy lid skin between the lash line and the brow shadow
    fold = [P(x, v - 3.2 - 2.4 * pu * (1 - 0.5 * E.wide)) for x, v, pu in zip(xs, U, _EU)]
    _fill(c, _closed2(fold, pUL[::-1]), C_LID, 0.85)
    _stroke(c, _curve(fold[1:-1]), C_SKIN_DEEP, 1.25, 0.55 * (0.4 + 0.6 * op))
    closed = op < 0.04
    info = None
    if not closed:
        opening = _closed2(pUL, pL[::-1])
        _fill(c, opening, C_SCLERA)
        c.save()
        c.clipPath(opening, doAntiAlias=True)
        # foreshortening of the iris on the turned face
        xa = _hp(H, cx - 3.0, 0.0, -3.0)[0]
        xb = _hp(H, cx + 3.0, 0.0, -3.0)[0]
        fs = clamp(abs(xb - xa) / 6.0, 0.25, 1.1)
        gxk = 5.2
        ix0 = cx + E.gx * gxk * (1.0 if E.gx * sd >= 0 else 0.85)
        iy0 = 0.6 + E.gy * (3.0 if E.gy > 0 else 6.4)
        ix, iy, _ = _hp(H, ix0, iy0, -1.0)
        fsi = lerp(1.0, fs, 0.7)
        rx, ry = RI * fsi, RI
        c.drawCircle(ex_, ey_ - 4.0, 9.0, paint(C_SCLERA_SH, 0.55, blur=3.0))
        c.drawCircle(P(cx + sd * EW, 0)[0], ey_ + 1.0, 5.0, paint(C_SCLERA_SH, 0.35, blur=3.0))
        ir = skia.Rect(ix - rx, iy - ry, ix + rx, iy + ry)
        c.drawOval(ir, paint(C_IRIS))
        c.drawOval(skia.Rect(ix - rx * 0.8, iy + ry * 0.05, ix + rx * 0.8, iy + ry * 1.05), paint(C_IRIS_LT, 0.55, blur=1.6))
        c.drawOval(ir, paint(C_IRIS_DK, 0.9, stroke=1.3))
        pr = 2.5 * F.pupil
        c.drawOval(skia.Rect(ix - pr * fsi, iy - pr, ix + pr * fsi, iy + pr), paint(C_PUPIL))
        # lid shadow across the top of the eye (deep-set)
        sh = _closed2(pUL, [(x, y + 3.6) for x, y in pUL[::-1]])
        _fill(c, sh, C_SOCKET, 0.55, blur=1.6)
        lx, ly = _lv(c, 1.0)
        gl = (ix + (lx * 2.2 - 0.6) * fsi, iy + ly * 2.2 - 0.8)
        glint = (gl[0], gl[1], 0.95 + 0.15 * F.pupil)
        c.drawCircle(gl[0], gl[1], glint[2], paint(WHITE, 0.8))
        c.drawCircle(ix - lx * 2.6 * fsi, iy - ly * 2.4, 0.55, paint(WHITE, 0.35))
        c.restore()
        info = (opening, glint)
        _stroke(c, _curve(pL[2:-1]), C_SKIN_DEEP, 1.1, 0.55)
    # lash line (upper lid edge): bold, thicker toward the outer corner
    th = [lerp(1.3, 3.1, ((s + 1) / 2) ** 0.7) * (0.85 if closed else 1.0) for s in _ES]
    top = [(x, y - w) for (x, y), w in zip(pUL, th)]
    _fill(c, _closed2(pUL, top[::-1]), C_LASH, 0.95)
    if closed:
        for s_ in (0.35, 0.65, 0.9):
            i = min(range(len(_ES)), key=lambda j: abs(_ES[j] - s_))
            px, py = pUL[i]
            _stroke(c, _curve([(px, py), (px + sd * 0.8, py + 2.0)]), C_LASH, 0.9, 0.6)
    # squint / pain creases at the outer corner, under-eye bags
    k = clamp((E.squint - 0.3 - 0.26 * F.warm) / 0.5)
    if k > 0.01:
        ox, oy = P(cx + sd * (EW + 2.0), L[-1] + 1.0)
        for dy_, ln in ((1.5, 7.0), (5.0, 5.5)):
            q0 = P(cx + sd * (EW + 1.0), L[-1] + dy_)
            q1 = P(cx + sd * (EW + 1.0 + ln), L[-1] + dy_ - 1.5)
            _stroke(c, _curve([q0, q1]), C_SKIN_DEEP, 1.1, 0.5 * k)
    bag = [P(x, v + 3.8 + 1.0 * pl) for x, v, pl in zip(xs[2:-2], L[2:-2], _EL[2:-2])]
    _stroke(c, _curve(bag), C_SKIN_DEEP, 1.0, 0.32 + 0.15 * F.dazed + 0.1 * F.warm)
    if F.warm > 0.02:
        # a hint of crow's feet: three fine lines fanning out of the outer corner, the cheek pushed up under the eye
        y0 = 0.5 * (UL[-1] + L[-1])
        for dy0, sl_, ln, a_ in ((-1.4, -0.42, 4.0, 0.22), (0.6, -0.1, 4.8, 0.27), (2.6, 0.28, 3.6, 0.2)):
            q0 = (cx + sd * (EW + 2.4), y0 + dy0)
            q1 = (cx + sd * (EW + 2.4 + 0.55 * ln), y0 + dy0 + 0.55 * ln * sl_ - 0.35)
            q2 = (cx + sd * (EW + 2.4 + ln), y0 + dy0 + ln * sl_)
            _stroke(c, _curve([P(*q0, -1.5), P(*q1, -2.0), P(*q2, -3.0)]), C_SKIN_DEEP, 0.85, a_ * F.warm)
        ch = [P(x, v + 6.2 + 1.2 * pl, -0.5) for x, v, pl in zip(xs[1:-1], L[1:-1], _EL[1:-1])]
        _stroke(c, _curve(ch), C_SKIN_HI, 1.6, 0.22 * F.warm, blur=0.8)
    if info is not None and emit is not None:
        emit.append(info)
    return info


def _brow_pts(H, E, slot):
    sd = float(slot)
    r, w, f = E.braise, E.bworry, E.bfurrow
    base = [(6.0, -7.4), (12.5, -9.9), (19.5, -11.8), (26.0, -12.6), (32.0, -11.4)]
    ws = [9.0, 9.2, 8.2, 6.2, 3.0]
    pts = []
    for i, (x, y) in enumerate(base):
        u = i / 4.0
        dy = -7.4 * r * (0.7 + 0.6 * math.sin(u * math.pi)) if r > 0 else -3.2 * r * (1.0 - 0.3 * u)
        dy += (3.6 * f) * (1.0 - u) ** 1.4 - 1.0 * f * u
        dy += -5.5 * w * (1.0 - u) ** 1.3 + 1.6 * w * u
        dx = -2.2 * f * (1.0 - u)
        pts.append((sd * (x + dx), y + dy))
    return pts, ws


def _draw_brow(c, H, F, slot):
    E = F.eye[slot]
    pts, ws = _brow_pts(H, E, slot)
    pp = [_hpp(H, x, y, 5.5) for x, y in pts]
    _fill(c, _ribbon(pp, ws), C_BROW)
    # a few hair strokes at the inner end (texture)
    for i in (0, 1):
        x, y = pts[i]
        q0 = _hpp(H, x, y + 2.5, 6.0)
        q1 = _hpp(H, x + slot * 3.5, y - 2.5, 6.0)
        _stroke(c, _curve([q0, q1]), C_BEARD_HI, 1.0, 0.45)
    return pts


def _fold_y(E, xa):
    """Front-view height of the upper-lid crease (the top of the eye region _draw_eye paints) at |x| = xa."""
    U = _eye_curves(E)[0]
    s = clamp((xa - EX) / EW, -1.0, 1.0)
    for i in range(1, len(_ES)):
        if s <= _ES[i] or i == len(_ES) - 1:
            u = clamp((s - _ES[i - 1]) / (_ES[i] - _ES[i - 1]))
            uu = lerp(U[i - 1], U[i], u)
            pu = lerp(_EU[i - 1], _EU[i], u)
            return uu - 3.2 - 2.4 * pu * (1.0 - 0.5 * E.wide)
    return U[-1] - 3.2


SCAR_CLEAR = 3.4          # front-view clearance kept between the scar and the lid crease (stroke + projection slack)


def _scar_geom(F, slot, brow_pts):
    """Front-view points (x0, y) of the scar line and of the notch cut through the brow (Anger's LEFT brow).
    A short slash across the brow, from the forehead just above it down to the brow's lower half - never lower
    than SCAR_CLEAR above the lid crease, so it can't reach the eyelid / eye in any expression, turn or blink."""
    sd = float(slot)
    E = F.eye[slot]
    bx, by = brow_pts[2]
    xa = bx / sd
    xs = (xa - 2.4, xa - 0.4, xa + 1.2)
    y_lo = min(by + 2.0, _fold_y(E, xs[2]) - SCAR_CLEAR)
    y_top = min(by - 8.0, y_lo - 5.0)
    y_mid = min(by - 2.4, lerp(y_top, y_lo, 0.6))
    line = [(sd * xs[0], y_top), (sd * xs[1], y_mid), (sd * xs[2], y_lo)]
    n_lo = min(by + 3.0, _fold_y(E, xa + 0.4) - SCAR_CLEAR + 0.6)
    notch = [(sd * (xa - 1.2), min(by - 4.0, n_lo - 2.0)), (sd * (xa + 0.4), n_lo)]
    return line, notch


def _draw_scar(c, H, F, slot, brow_pts):
    """Pale scar through Anger's LEFT eyebrow: a gap cut through the brow and a short slanted line across it
    (forehead -> brow only; it stops above the lid crease)."""
    line, notch = _scar_geom(F, slot, brow_pts)
    # the same clamp once more in projected head coords (a nodding / turned head shifts the brow ridge against the
    # deeper-set eye): every point stays above the projected crease by its stroke radius + a margin
    E = F.eye[slot]
    sd = float(slot)
    U = _eye_curves(E)[0]
    fold = sorted(_hpp(H, sd * (EX + s * EW), v - 3.2 - 2.4 * pu * (1.0 - 0.5 * E.wide), -3.0)
                  for s, v, pu in zip(_ES, U, _EU))

    def clampq(q, r):
        x, y = q
        if fold[0][0] <= x <= fold[-1][0]:
            for (x0, y0), (x1, y1) in zip(fold, fold[1:]):
                if x0 <= x <= x1:
                    fy = y0 + (y1 - y0) * ((x - x0) / (x1 - x0) if x1 > x0 else 0.0)
                    return (x, min(y, fy - r - 1.3))
        return q

    pn = [clampq(_hpp(H, x, y, 6.0), 1.5) for x, y in notch]
    pn[0] = (pn[0][0], min(pn[0][1], pn[1][1] - 1.5))
    _stroke(c, _curve(pn), C_LID, 3.0)                          # the notch cut through the brow
    pl = [clampq(_hpp(H, x, y, 6.0), 1.1) for x, y in line]
    pl[1] = (pl[1][0], min(pl[1][1], pl[2][1] - 1.0))
    pl[0] = (pl[0][0], min(pl[0][1], pl[1][1] - 2.0))
    _stroke(c, _curve(pl), C_SCAR, 2.2, 0.85)
    _stroke(c, _curve(pl), C_SCAR_HI, 1.1, 0.95)


def _draw_forehead(c, H, F):
    """Creases when the brows lift (per side), a vertical furrow pair between the brows."""
    for slot in (-1, 1):
        E = F.eye[slot]
        k = clamp((E.braise - 0.15) / 0.7)
        if k > 0.01:
            for j, y in enumerate((-24.0, -30.5, -37.0)):
                kk = k * (1.0 - 0.25 * j)
                pts = [_hpp(H, slot * x, y - 1.6 * math.sin(x / 34.0 * math.pi) - 2.2 * E.braise, 1.5)
                       for x in (3.0, 12.0, 22.0, 31.0)]
                _stroke(c, _curve(pts), C_SKIN_DEEP, 1.2, 0.5 * kk)
                _stroke(c, _curve([(x + 0.0, y_ + 1.4) for x, y_ in pts]), C_SKIN_HI, 0.9, 0.35 * kk)
    fu = 0.5 * (F.eye[-1].bfurrow + F.eye[1].bfurrow)
    if fu > 0.05:
        for slot in (-1, 1):
            q = [_hpp(H, slot * 3.2, -11.5, 6.0), _hpp(H, slot * 4.4, -17.0, 4.5), _hpp(H, slot * 4.0, -21.0, 3.0)]
            _stroke(c, _curve(q), C_SKIN_DEEP, 1.25, 0.55 * clamp(fu))


# --------------------------------------------------------------------------- nose
_NOSE_C = [(-9.0, 5.0), (-2.0, 7.0), (5.0, 10.0), (12.0, 14.0), (17.5, 17.6), (21.0, 16.4), (23.6, 11.5),
           (25.0, 6.0), (26.4, 2.0)]                       # bridge / profile line: (y, dz)
_NOSE_W = [(-9.0, 5.0), (0.0, 5.5), (8.0, 7.0), (14.0, 9.5), (19.0, 12.5), (22.0, 13.5), (24.5, 11.0)]


def _draw_nose(c, H, F):
    s = H.s
    lead = 1.0 if s >= 0 else -1.0
    sk = abs(s)
    cl = [_hp(H, 0.0, y, dz) for y, dz in _NOSE_C]
    clp = [(x, y) for x, y, _ in cl]

    def wall(side, frac=0.45):
        out = []
        for y, w in _NOSE_W:
            dz = _tab(_NOSE_C, y)[0] * frac
            out.append(_hpp(H, side * w, y, dz))
        return out

    tw = wall(-lead)
    lw = wall(lead)
    # trailing side of the nose: form shadow
    _fill(c, _closed2(clp[:6], tw[:6][::-1]), C_SKIN_SH, 0.5 + 0.2 * sk, blur=1.6)
    # leading half protruding past the cheek: re-fill with skin, then contour the profile line
    if sk > 0.06:
        body = _closed2(clp[:8], lw[::-1])
        _fill(c, body, C_SKIN)
        dx, dy = _lv(c, 2.5)
        c.save()
        c.clipPath(body, doAntiAlias=True)
        c.translate(-dx, -dy)
        _fill(c, body, C_SKIN_SH, 0.35, blur=2.0)
        c.restore()
        _stroke(c, _curve(clp[1:8]), C_SKIN_LINE, 1.5, 0.85 * clamp((sk - 0.06) / 0.2))
    # alae + nostrils
    for side in (-1.0, 1.0):
        far = side == lead
        vis = 1.0 - (clamp((sk - 0.3) / 0.25) if far else 0.0)
        if vis <= 0.02:
            continue
        al = [_hpp(H, side * 8.5, 15.0, 8.0), _hpp(H, side * 13.6, 19.0, 4.5), _hpp(H, side * 13.2, 23.4, 3.5),
              _hpp(H, side * 9.0, 25.2, 6.0)]
        _stroke(c, _curve(al), C_SKIN_LINE, 1.5, 0.7 * vis)
        n0 = _hp(H, side * 6.6, 24.0, 8.0)
        rw = 3.4 * max(0.25, H.c if not far else H.c * 0.8)
        c.save()
        c.translate(n0[0], n0[1])
        c.rotate(side * -14.0 * H.c)
        c.drawOval(skia.Rect(-rw, -1.7, rw, 1.7), paint(C_SKIN_LINE, 0.85 * vis))
        c.restore()
    # under-nose shadow onto the mustache, tip highlight
    u0 = _hp(H, 0.0, 26.5, 6.0)
    c.drawOval(skia.Rect(u0[0] - 11, u0[1] - 1.5, u0[0] + 11, u0[1] + 3.0), paint(C_BEARD_SH, 0.5, blur=2.0))
    lx, ly = _lv(c, 1.0)
    tp = _hp(H, lx * 3.0, 15.5, 17.0)
    c.drawOval(skia.Rect(tp[0] - 3.2, tp[1] - 2.2, tp[0] + 3.2, tp[1] + 2.2), paint(C_SKIN_HI, 0.75, blur=1.2))
    bp = _hp(H, lx * 1.5, 2.0, 7.5)
    c.drawOval(skia.Rect(bp[0] - 1.6, bp[1] - 4.5, bp[0] + 1.6, bp[1] + 4.5), paint(C_SKIN_HI, 0.45, blur=1.4))


# --------------------------------------------------------------------------- mouth / beard / mustache
def _mouth_geom(H, F):
    """Front-view mouth: corners, upper edge (under the mustache) and lower edge (lower lip top)."""
    o = F.open
    rd = F.round
    g = F.grimace
    sup = F.sup
    wk = (1.0 - 0.34 * rd) * (1.0 + 0.12 * g + 0.06 * max(0.0, F.smile)) * (1.0 - 0.07 * sup)
    cw = 16.5 * wk
    cy = MOUTH_Y + 0.6 - 3.2 * F.smile + 1.8 * g
    tw = 0.0
    if F.tremble > 0:
        tw = F.tremble * 0.9 * math.sin(F.t * 31.0)
    corners = {}
    for slot in (-1, 1):
        lift = 7.5 * F.smirk if slot == F.smirk_slot else 0.0
        if sup > 0 and slot == F.smirk_slot:
            lift += sup * (0.9 + 0.7 * math.sin(F.t * 9.0) * math.sin(F.t * 3.1))     # the twitch fighting it
        corners[slot] = (slot * (cw + (1.2 * F.smirk if slot == F.smirk_slot else 0.0)), cy - lift + tw * slot)
    up = [corners[-1], (-8.5 * wk, MOUTH_Y - 0.5 - 0.6 * o), (0.0, MOUTH_Y - 0.3 - 0.9 * o),
          (8.5 * wk, MOUTH_Y - 0.5 - 0.6 * o), corners[1]]
    hgt = o * (12.5 + 4.0 * rd) * (1.0 - 0.6 * g) + 2.6 * g
    lo = [corners[-1], (-8.5 * wk, MOUTH_Y + 0.4 + hgt * 0.78 - 1.0 * F.smile), (0.0, MOUTH_Y + 0.6 + hgt - 1.2 * F.smile),
          (8.5 * wk, MOUTH_Y + 0.4 + hgt * 0.78 - 1.0 * F.smile), corners[1]]
    return corners, up, lo, hgt


def _draw_beard(c, H, F):
    path = _beard_outline(H)
    if path is None:
        return None
    k = 7.0
    _cel(c, path, C_BEARD, C_BEARD_SH, k=k, blur=2.0, line=C_BEARD_SH, line_w=1.2, line_a=0.9)
    # strands (texture): flowing down the jaw; only the visible ones
    c.save()
    c.clipPath(path, doAntiAlias=True)
    for i, (x0, y0, ln, cv) in enumerate(_STRANDS):
        p0 = _hp(H, x0, y0, 8.0)
        if p0[2] < 4:
            continue
        p1 = _hp(H, x0 * 0.92 + cv, y0 + ln * 0.5, 9.0)
        p2 = _hp(H, x0 * 0.85 + cv * 1.6, y0 + ln, 9.0)
        colr = C_BEARD_HI if i % 3 else C_BEARD_SH
        _stroke(c, _curve([p0[:2], p1[:2], p2[:2]]), colr, 1.4, 0.55)
    c.restore()
    return path


_STRANDS = [(-36.0, 20.0, 16.0, 1.5), (-28.0, 34.0, 18.0, 2.0), (-18.0, 48.0, 16.0, 2.0), (-8.0, 52.0, 18.0, 1.0),
            (6.0, 52.0, 18.0, -1.0), (16.0, 47.0, 17.0, -2.0), (27.0, 35.0, 18.0, -2.0), (36.0, 21.0, 16.0, -1.5),
            (-40.0, 6.0, 14.0, 0.5), (40.0, 6.0, 14.0, -0.5), (-24.0, 58.0, 12.0, 2.0), (22.0, 58.0, 12.0, -2.0),
            (0.0, 62.0, 13.0, 0.0), (-12.0, 64.0, 10.0, 1.0), (12.0, 64.0, 10.0, -1.0)]


def _draw_mouth(c, H, F):
    corners, up, lo, hgt = _mouth_geom(H, F)
    dz = 9.0
    pu = [_hpp(H, x, y, dz) for x, y in up]
    pl = [_hpp(H, x, y, dz) for x, y in lo]
    # lower lip (shows under the mustache, pressed thin when suppressing)
    lip_t = 4.6 * (1.0 - 0.55 * F.sup) * (1.0 - 0.5 * F.grimace) * (1.0 - 0.25 * F.round)
    lip = [(x, y + lip_t * math.sin((i / (len(lo) - 1)) * math.pi)) for i, (x, y) in enumerate(lo)]
    pli = [_hpp(H, x, y, dz - 0.5) for x, y in lip]
    lipp = _closed2(pl, pli[::-1])
    _fill(c, lipp, C_LIP)
    lx, ly = _lv(c, 1.0)
    mid = _hp(H, lx * 2.0, lo[2][1] + lip_t * 0.45, dz)
    c.drawOval(skia.Rect(mid[0] - 4.5, mid[1] - 1.0, mid[0] + 4.5, mid[1] + 1.2), paint(C_SKIN_HI, 0.35, blur=1.2))
    _stroke(c, _curve(pli[1:-1]), C_BEARD_SH, 1.2, 0.7)
    if hgt > 0.5:
        op = _closed2(pu, pl[::-1])
        _fill(c, op, C_MOUTH)
        c.save()
        c.clipPath(op, doAntiAlias=True)
        tt = min(4.2, hgt * 0.7)
        tpts = [(x, y + tt) for x, y in up]
        _fill(c, _closed2([_hpp(H, x, y - 1.0, dz) for x, y in up], [_hpp(H, x, y, dz) for x, y in tpts][::-1]), C_TEETH)
        if F.grimace > 0.05 or hgt > 9.0:
            bt = min(3.6, 1.2 + 4.0 * F.grimace)
            bpts = [(x, y - bt) for x, y in lo]
            _fill(c, _closed2([_hpp(H, x, y, dz) for x, y in bpts], [_hpp(H, x, y + 1, dz) for x, y in lo][::-1]),
                  C_TEETH, 0.9)
        if hgt > 6.0:
            tg = _hp(H, 0.0, lo[2][1] - 1.0, dz - 2)
            c.drawOval(skia.Rect(tg[0] - 8.0, tg[1] - 3.6, tg[0] + 8.0, tg[1] + 3.0), paint(C_TONGUE, 0.9))
        if F.grimace > 0.1:
            for x in (-8.0, -3.0, 2.0, 7.0):
                q0 = _hpp(H, x, MOUTH_Y - 0.5, dz)
                q1 = _hpp(H, x, MOUTH_Y + hgt, dz)
                _stroke(c, _curve([q0, q1]), C_MOUTH, 0.7, 0.4 * F.grimace)
        c.restore()
        _stroke(c, op, C_MOUTH, 1.0, 0.8)
    else:
        _stroke(c, _curve(pu), C_MOUTH, 1.6, 0.9)
    # tension / smirk cheek crease at the lifted corner
    sl = F.smirk_slot
    k = clamp(F.smirk * 1.6 + 0.6 * F.sup)
    if k > 0.02:
        cx, cy = corners[sl]
        q = [_hpp(H, cx + sl * 3.0, cy - 7.0, 6.0), _hpp(H, cx + sl * 5.5, cy - 1.0, 7.0), _hpp(H, cx + sl * 4.0, cy + 4.0, 7.0)]
        _stroke(c, _curve(q), C_BEARD_SH, 1.4, 0.75 * k)
    return corners


def _draw_mustache(c, H, F, corners):
    sm, sl = F.smirk, F.smirk_slot
    pts = []
    for slot in (-1, 1):
        lift = (6.5 * sm if slot == sl else 0.0) + 2.2 * F.smile
        cx, cy = corners[slot]
        pts.append((slot, [(slot * 15.5, 27.0), (slot * 20.5, 30.0 - 0.5 * lift), (slot * 24.0, 35.5 - lift),
                           (slot * 25.0, 42.5 - 1.3 * lift), (slot * 21.0, 43.6 - 1.4 * lift),
                           (cx + slot * 1.0, cy + 0.6), (slot * 9.0, MOUTH_Y - 0.4)]))
    right = pts[1][1]
    left = pts[0][1]
    ring = [(-8.0, 26.5), (0.0, 27.4), (8.0, 26.5)] + right + [(0.0, MOUTH_Y + 0.1)] + left[::-1]
    pp = [_hpp(H, x, y, 9.5 if abs(x) < 20 else 7.5) for x, y in ring]
    path = _loop(pp, 0.4)
    _cel(c, path, C_BEARD, C_BEARD_SH, k=3.0, blur=1.0, line=C_BEARD_SH, line_w=1.0, line_a=0.85)
    for slot in (-1, 1):
        for j in range(3):
            x0 = slot * (5.0 + 5.5 * j)
            q = [_hpp(H, x0, 28.5, 10.0), _hpp(H, x0 + slot * 3.0, 33.0, 10.0), _hpp(H, x0 + slot * 4.5, 36.5, 9.5)]
            _stroke(c, _curve(q), C_BEARD_HI, 1.1, 0.5)
    return path


def _draw_ear(c, H, slot):
    x, y, vis = _haz(H, slot * 101.0, 6.0, 1.0)
    if vis < -12.0:
        return
    k = clamp(vis / 25.0 + 0.45)                 # how much of the ear's face we see
    w = lerp(4.5, 12.0, k)
    yc = y
    xo = x + slot * lerp(5.0, 2.0, k) * (1.0 if slot * H.s <= 0 else 0.5)
    pts = [(xo - slot * w * 0.5, yc - 12.0), (xo + slot * w * 0.55, yc - 10.5), (xo + slot * w * 0.75, yc - 1.0),
           (xo + slot * w * 0.45, yc + 10.0), (xo - slot * w * 0.25, yc + 13.0), (xo - slot * w * 0.55, yc + 4.0)]
    path = _loop(pts, 0.5)
    _cel(c, path, C_SKIN, C_SKIN_SH, k=2.5, line=C_SKIN_LINE, line_w=1.2, line_a=0.75)
    if k > 0.3:
        inner = [(xo + slot * w * 0.35, yc - 7.0), (xo + slot * w * 0.2, yc + 1.0), (xo, yc + 6.5)]
        _stroke(c, _curve(inner), C_SKIN_DEEP, 1.3, 0.7 * k)


def _hairline_region(H):
    """Shaved-scalp stubble region (head-local path) - above the hairline, around the back to the nape."""
    hl = [(-180.0, 30.0), (-150.0, 22.0), (-120.0, 8.0), (-104.0, -3.0), (-92.0, -12.0), (-78.0, -21.0),
          (-60.0, -27.5), (-38.0, -31.0), (-16.0, -33.0), (0.0, -33.5)]
    hl = hl + [(-p, y) for p, y in reversed(hl[:-1])]
    pts = []
    for phi, y in hl:
        x, yy, vis = _haz(H, phi, y, 0.6)
        if vis > 0.0:
            pts.append((x, yy))
    if len(pts) < 2:
        return None
    p = skia.Path()
    _cr(p, pts)
    x1, y1 = pts[-1]
    x0, y0 = pts[0]
    p.lineTo(x1 + (12.0 if x1 >= x0 else -12.0), y1)
    p.lineTo(x1 + (12.0 if x1 >= x0 else -12.0), -90.0)
    p.lineTo(x0 - (12.0 if x1 >= x0 else -12.0), -90.0)
    p.lineTo(x0 - (12.0 if x1 >= x0 else -12.0), y0)
    p.close()
    return p


def _draw_bruises(c, H, F):
    b = F.bruised
    if b <= 0.01:
        return
    # dust smudges
    for (x0, y0, r, a) in ((-30.0, 10.0, 9.0, 0.35), (24.0, -30.0, 11.0, 0.25), (-12.0, -42.0, 8.0, 0.25),
                           (34.0, 16.0, 7.0, 0.3)):
        p = _hp(H, x0, y0, 0.0)
        if p[2] > 2:
            c.drawOval(skia.Rect(p[0] - r, p[1] - r * 0.6, p[0] + r, p[1] + r * 0.6), paint(C_DUST, a * b, blur=3.0))
    # scrapes on the cheekbone and the forehead
    for (x0, y0, x1, y1) in ((-36.0, 9.0, -27.0, 13.0), (-34.0, 13.0, -27.0, 16.5), (14.0, -40.0, 22.0, -37.0)):
        p0, p1 = _hp(H, x0, y0, 1.0), _hp(H, x1, y1, 1.0)
        if p0[2] > 2:
            _stroke(c, _curve([p0[:2], p1[:2]]), C_BLOOD, 1.1, 0.55 * b)
    # a cut over the right brow (not the scarred one) with a short dried trickle
    slot_r = -F.slot_l
    p0 = _hp(H, slot_r * 12.0, -21.0, 3.0)
    p1 = _hp(H, slot_r * 21.0, -24.0, 3.0)
    if p0[2] > 0:
        _stroke(c, _curve([p0[:2], p1[:2]]), C_BLOOD, 2.0, 0.85 * b)
        _stroke(c, _curve([(p0[0] + 0.6, p0[1] - 0.9), (p1[0] + 0.6, p1[1] - 0.9)]), C_SKIN_HI, 0.8, 0.5 * b)
        q = [_hpp(H, slot_r * 15.0, -21.5, 3.0), _hpp(H, slot_r * 15.5, -17.0, 4.0)]
        _stroke(c, _curve(q), C_BLOOD, 1.2, 0.6 * b)


def _draw_head(c, R, F, emit):
    """Draw the head in head-local coords (canvas already in the head frame)."""
    H = R.H
    out = _head_outline(H)
    # ears behind the head outline (front view / the far ear) - the near ear is drawn over the cheek below
    for slot in (-1, 1):
        if slot * H.s > -0.25:
            _draw_ear(c, H, slot)
    # skin: shade colour, the lit colour shifted toward the light (soft terminator)
    _cel(c, out, C_SKIN, C_SKIN_SH, k=9.0, blur=1.0, line=C_SKIN_LINE, line_w=1.6, line_a=0.9)
    c.save()
    c.clipPath(out, doAntiAlias=True)
    # stubble on the shaved scalp
    hr = _hairline_region(H)
    if hr is not None:
        _fill(c, hr, C_HAIR, 0.13)
        c.save()
        c.translate(0.0, -3.0)
        _fill(c, hr, C_HAIR, 0.12)
        c.restore()
    # crown sheen + cheekbone / brow highlights toward the light
    lx, ly = _lv(c, 1.0)
    sx, sy, _ = _hp(H, lx * 18.0, -44.0 + ly * 6.0, 2.0)
    _soft_oval(c, sx, sy, 15.0, 7.0, C_SKIN_HI, 0.6)
    for slot in (-1, 1):
        q = _hp(H, slot * 33.0, 12.0 - 3.2 * F.warm, 0.0)
        if q[2] > 5:
            _soft_oval(c, q[0], q[1], 7.0, 3.0 + 0.6 * F.warm, C_SKIN_HI, 0.3 + 0.2 * (lx * slot > 0) + 0.14 * F.warm)
        q = _hp(H, slot * 18.0, -20.0, 3.0)
        _soft_oval(c, q[0], q[1], 9.0, 2.5, C_SKIN_HI, 0.3)
    # nasolabial folds (above the beard line); the smirk side bunches up into a deeper crease + cheek highlight
    for slot in (-1, 1):
        k = (F.smirk + 0.5 * F.sup) if slot == F.smirk_slot else 0.0
        k += 0.5 * max(0.0, F.smile)
        q = [_hpp(H, slot * (14.5 + 1.0 * k), 21.0 - 2.0 * k, 2.0), _hpp(H, slot * (19.5 + 2.0 * k), 25.0 - 2.5 * k, 1.0),
             _hpp(H, slot * (23.5 + 2.5 * k), 27.5 - 2.0 * k, 0.5)]
        _stroke(c, _curve(q), C_SKIN_DEEP, 1.3 + 0.9 * k, clamp(0.5 + 0.45 * k))
        if k > 0.05:
            ch = _hp(H, slot * 30.0, 14.0 - 2.0 * k, 0.0)
            if ch[2] > 0:
                _soft_oval(c, ch[0], ch[1], 8.0, 4.0, C_SKIN_HI, 0.5 * clamp(k))
    _draw_forehead(c, H, F)
    infos = []
    for slot in (-1, 1):
        infos.append(_draw_eye(c, H, F, slot, emit))
    for slot in (-1, 1):
        bp = _draw_brow(c, H, F, slot)
        if slot == F.slot_l:
            _draw_scar(c, H, F, slot, bp)
    _draw_bruises(c, H, F)
    c.restore()
    for slot in (-1, 1):
        if slot * H.s <= -0.25:
            _draw_ear(c, H, slot)
    _draw_beard(c, H, F)
    corners = _draw_mouth(c, H, F)
    _draw_mustache(c, H, F, corners)
    _draw_nose(c, H, F)


# =========================================================================== arm presets
ARMS = {
    "rest": ArmPose(shoulder=6.0, elbow=14.0, wrist=0.0, hand="relaxed"),
    "torch_high": ArmPose(shoulder=132.0, elbow=48.0, wrist=-62.0, hand="hold"),
    "torch_up": ArmPose(shoulder=166.0, elbow=18.0, wrist=-64.0, hand="hold"),
    "torch_near": ArmPose(shoulder=10.0, elbow=140.0, wrist=-30.0, hand="hold"),
    "sword_low": ArmPose(shoulder=10.0, elbow=16.0, wrist=-26.0, hand="hold"),
    "sword_guard": ArmPose(shoulder=32.0, elbow=76.0, wrist=-14.0, hand="hold", across=0.12),
    "chop_windup": ArmPose(shoulder=168.0, elbow=62.0, wrist=-14.0, hand="hold"),
    "chop_strike": ArmPose(shoulder=64.0, elbow=6.0, wrist=-62.0, hand="hold"),
    "swipe_gather": ArmPose(shoulder=58.0, elbow=118.0, wrist=24.0, hand="fist", across=0.85),
    "swipe_back": ArmPose(shoulder=104.0, elbow=12.0, wrist=-18.0, hand="open"),
    "door_grip": ArmPose(shoulder=70.0, elbow=28.0, wrist=-8.0, hand="grip"),
    "run_pump": ArmPose(shoulder=10.0, elbow=78.0, wrist=0.0, hand="fist"),
    "hang_reach": ArmPose(shoulder=174.0, elbow=6.0, wrist=6.0, hand="grip"),
    "sword_both_hands_thrust": ArmPose(shoulder=84.0, elbow=10.0, wrist=-56.0, hand="hold"),
    "weak_raise": ArmPose(shoulder=98.0, elbow=38.0, wrist=14.0, hand="claw"),
    "wipe_face": ArmPose(shoulder=96.0, elbow=128.0, wrist=6.0, hand="open", across=0.5),
    "cross_arms": ArmPose(shoulder=22.0, elbow=116.0, wrist=6.0, hand="fist", across=1.0),
    "swat": ArmPose(shoulder=122.0, elbow=58.0, wrist=-10.0, hand="open", across=0.22),
    "prop_rest": ArmPose(shoulder=34.0, elbow=34.0, wrist=8.0, hand="relaxed"),
    "fist": ArmPose(shoulder=8.0, elbow=18.0, wrist=0.0, hand="fist"),
    "shield_up": ArmPose(shoulder=40.0, elbow=96.0, wrist=0.0, hand="fist", across=0.3),
    "fall_up": ArmPose(shoulder=128.0, elbow=34.0, wrist=8.0, hand="open"),
    "flail": ArmPose(shoulder=140.0, elbow=28.0, wrist=0.0, hand="open"),
    "lie_side": ArmPose(shoulder=4.0, elbow=10.0, wrist=0.0, hand="relaxed"),
}
_CROSS_NEAR = ArmPose(shoulder=24.0, elbow=118.0, wrist=8.0, hand="fist", across=1.0)
_CROSS_FAR = ArmPose(shoulder=20.0, elbow=110.0, wrist=2.0, hand="fist", across=0.95)


# =========================================================================== body states
STATES = ("stand", "walk", "run", "chop", "swipe", "door_push", "charge", "stumble", "hang", "fall",
          "sword_drag", "crumpled", "lie_back", "prop_sit", "sleep")
_ARMLESS = ("arm_r", "arm_l", "anchor")


def _bp():
    return {"px": 0.0, "py": -HIP_H, "rot": 0.0, "ox": 0.0, "oy": 0.0, "spine": 0.0, "neck": 0.0, "tilt": 0.0,
            "nod": 0.0, "sh_up": 0.0, "bturn": 0.0, "bturn_w": 0.0, "wind_x": 0.0, "wind_y": 0.0, "flut": 0.0,
            "anchor_w": 0.0, "breath_k": 1.0, "breath_rate": 1.0, "sleep": 0.0, "mouth_add": 0.0,
            "swing": 0.0, "swing_ph": 0.0, "lying": 0.0, "sitting": 0.0, "slip": 0.0, "shake": 0.0,
            "r_th": 0.0, "r_kn": 0.0, "r_ft": 0.0, "r_fr": 0.0, "r_sp": 10.0,
            "l_th": 0.0, "l_kn": 0.0, "l_ft": 0.0, "l_fr": 0.0, "l_sp": 10.0,
            "reach_w": 0.0, "reach_x": 0.0, "reach_y": 0.0, "arm_r_w": 0.0, "arm_l_w": 0.0,
            "arm_r": None, "arm_l": None, "anchor": None, "reach_side": None}


def _plant(P, feet):
    """feet: side -> (forward, lift, pitch, spread): sagittal 2-bone IK for planted / stepping feet.
    pitch = foot angle against the floor (+ toes up)."""
    hx, hy = P["px"], P["py"]
    fwd = (lambda j1, j2: j1 if j1[0] >= j2[0] else j2)
    for side, (f, lift, pitch, spread) in feet.items():
        ax, ay = f, -(ANKLE_H + lift)
        kn = _ik((hx, hy), (ax, ay), THIGH, SHIN, fwd)
        th = _ang_of(kn[0] - hx, kn[1] - hy)
        sh = _ang_of(ax - kn[0], ay - kn[1])
        P[side + "_th"] = th
        P[side + "_kn"] = th - sh
        P[side + "_ft"] = pitch
        P[side + "_fr"] = 0.0
        P[side + "_sp"] = spread


def _keys(keys, u):
    """Piecewise eased scalar track: keys [(u, v[, ease])], ease in 'io' (default), 'in', 'out', 'lin'."""
    if u <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if u < keys[i][0]:
            u0, v0 = keys[i - 1][0], keys[i - 1][1]
            u1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "io"
            x = clamp((u - u0) / (u1 - u0))
            if e == "in":
                x = x * x * x
            elif e == "out":
                x = 1 - (1 - x) ** 3
            elif e == "io":
                x = 0.5 - 0.5 * math.cos(math.pi * x)
            return v0 + (v1 - v0) * x
    return keys[-1][1]


def _arm_keys(keys, u, free):
    """Arm track over presets: keys [(u, preset name | None (= the pose's own arm) | ArmPose[, ease])]."""
    def get(v):
        if v is None:
            return free
        return ARMS[v] if isinstance(v, str) else v
    if u <= keys[0][0]:
        return get(keys[0][1])
    for i in range(1, len(keys)):
        if u < keys[i][0]:
            u0, u1 = keys[i - 1][0], keys[i][0]
            e = keys[i][2] if len(keys[i]) > 2 else "io"
            x = clamp((u - u0) / (u1 - u0))
            x = x * x * x if e == "in" else (1 - (1 - x) ** 3 if e == "out" else 0.5 - 0.5 * math.cos(math.pi * x))
            return ArmPose.blend(get(keys[i - 1][1]), get(keys[i][1]), x)
    return get(keys[-1][1])


def _side_other(s):
    return "l" if s == "r" else "r"


def _st_stand(p, t, ph, ex):
    P = _bp()
    P["py"] = -HIP_H + 1.2 * noise1(t * 0.31, 5)
    P["px"] = 1.5 * noise1(t * 0.23, 9)
    _plant(P, {"r": (-16.0, 0.0, 0.0, 16.0), "l": (22.0, 0.0, 0.0, 16.0)})
    P["spine"] = 1.0
    return P


def _cycle_feet(q, S, stance, lift, roll=50.0):
    feet = {}
    for side, off in (("r", 0.0), ("l", 0.5)):
        u = (q - off) % 1.0
        if u < stance:
            v = u / stance
            f = S - 2.0 * S * v
            if v < 0.12:
                pitch = 14.0 * (1.0 - v / 0.12)
            elif v > 0.62:
                pitch = -30.0 * ((v - 0.62) / 0.38) ** 1.5
            else:
                pitch = 0.0
            la = roll * math.sin(max(0.0, -pitch) * D2R)
            f += roll * (1.0 - math.cos(pitch * D2R)) if pitch < 0 else 0.0
        else:
            v = (u - stance) / (1.0 - stance)
            f0 = -S + roll * (1.0 - math.cos(30.0 * D2R))
            f = lerp(f0, S, smoothstep(v))
            la = roll * 0.5 * (1.0 - v) ** 2 + lift * math.sin(math.pi * v) ** 1.2
            pitch = lerp(-30.0, 14.0, smoothstep(v))
        feet[side] = (f, la, pitch, 10.0)
    return feet


def _st_walk(p, t, ph, ex):
    P = _bp()
    q = ph % 1.0
    P["py"] = -(HIP_H - 10.0) + 9.0 * (0.5 + 0.5 * math.cos(4 * math.pi * (q - 0.04)))
    _plant(P, _cycle_feet(q, WALK_S, WALK_STANCE, 46.0))
    P["spine"] = 4.0
    P["rot"] = 1.0
    P["swing"] = 13.0
    P["swing_ph"] = q
    P["tilt"] = 1.5 * math.sin(2 * math.pi * q)
    P["wind_x"] = -80.0
    P["flut"] = 0.4
    return P


def _st_run(p, t, ph, ex):
    P = _bp()
    q = ph % 1.0
    P["py"] = -(HIP_H - 26.0) + 12.0 * (0.5 + 0.5 * math.cos(4 * math.pi * (q - RUN_STANCE * 0.5)))
    _plant(P, _cycle_feet(q, RUN_S, RUN_STANCE, 92.0, roll=46.0))
    P["spine"] = 9.0
    P["rot"] = 4.0
    P["swing"] = 42.0
    P["swing_ph"] = q
    P["arm_r"], P["arm_r_w"] = ARMS["run_pump"], 1.0
    P["arm_l"], P["arm_l_w"] = ARMS["run_pump"], 1.0
    P["tilt"] = 2.0 * math.sin(2 * math.pi * q)
    P["wind_x"] = -260.0
    P["flut"] = 0.9
    P["breath_k"] = 1.4
    P["breath_rate"] = 2.2
    return P


def _st_charge(p, t, ph, ex):
    P = _st_run(p, t, ph, ex)
    lead = ex.get("lead", "r")
    P["spine"] = 16.0
    P["rot"] = 9.0
    P["neck"] = 14.0
    P["nod"] = -0.35
    P["sh_up"] = 0.45
    P["arm_" + lead] = ArmPose(shoulder=30.0, elbow=112.0, wrist=8.0, hand="fist", across=0.35)
    P["swing"] = 26.0
    P["wind_x"] = -340.0
    return P


def _st_chop(p, t, ph, ex):
    P = _bp()
    u = clamp(ph)
    side = ex.get("sword_hand", "r")
    P["spine"] = _keys([(0.0, 2.0), (0.36, -8.0), (0.5, 18.0, "in"), (0.72, 15.0), (1.0, 3.0)], u)
    P["rot"] = _keys([(0.0, 0.0), (0.36, -3.0), (0.5, 5.0, "in"), (0.72, 4.0), (1.0, 0.0)], u)
    drop = _keys([(0.0, 0.0), (0.36, -4.0), (0.5, 24.0, "in"), (0.72, 22.0), (1.0, 2.0)], u)
    P["py"] = -HIP_H + drop
    P["neck"] = _keys([(0.0, 0.0), (0.36, -10.0), (0.5, 10.0, "in"), (0.72, 8.0), (1.0, 2.0)], u)
    P["sh_up"] = _keys([(0.0, 0.0), (0.36, 0.5), (0.5, 0.0), (1.0, 0.0)], u)
    fl = 26.0 * math.sin(math.pi * clamp((u - 0.28) / 0.22)) if 0.28 < u < 0.5 else 0.0
    ff = _keys([(0.0, 26.0), (0.28, 26.0), (0.5, 50.0), (1.0, 40.0)], u)
    _plant(P, {_side_other(side): (ff, fl, 0.0, 18.0), side: (-34.0, 0.0, 0.0, 18.0)})
    P["arm_" + side] = _arm_keys([(0.0, "sword_guard"), (0.36, "chop_windup"), (0.5, "chop_strike", "in"),
                                  (0.72, "chop_strike"), (1.0, "sword_low")], u, None)
    P["arm_" + side + "_w"] = 1.0
    P["wind_x"] = -60.0 * (0.36 < u < 0.6)
    P["flut"] = 0.5
    return P


def _st_swipe(p, t, ph, ex):
    P = _bp()
    u = clamp(ph)
    side = ex.get("swipe_side", "r")
    P["spine"] = _keys([(0.0, 1.0), (0.3, -3.0), (0.48, 8.0, "in"), (0.7, 6.0), (1.0, 1.0)], u)
    P["rot"] = _keys([(0.0, 0.0), (0.3, -2.0), (0.48, 3.0, "in"), (1.0, 0.0)], u)
    P["neck"] = _keys([(0.0, 0.0), (0.3, 4.0), (0.48, -4.0), (1.0, 0.0)], u)
    P["py"] = -HIP_H + _keys([(0.0, 0.0), (0.3, 8.0), (0.48, 4.0), (1.0, 0.0)], u)
    _plant(P, {"r": (-18.0, 0.0, 0.0, 16.0), "l": (26.0, 0.0, 0.0, 16.0)})
    P["arm_" + side] = _arm_keys([(0.0, None), (0.3, "swipe_gather"), (0.48, "swipe_back", "in"),
                                  (0.7, "swipe_back"), (1.0, None)], u, getattr(p, "arm_" + side))
    P["arm_" + side + "_w"] = 1.0
    return P


def _st_door(p, t, ph, ex):
    P = _bp()
    u = ph % 1.0
    side = ex.get("grip_side", "r")
    pull = math.sin(math.pi * clamp(u / 0.5)) if u < 0.5 else 0.0
    push = math.sin(math.pi * clamp((u - 0.5) / 0.5)) if u >= 0.5 else 0.0
    rattle = (pull + push) * 1.4 * noise1(t * 26.0, 3)
    P["rot"] = -9.0 * pull + 8.0 * push + rattle
    P["px"] = -16.0 * pull + 12.0 * push
    P["spine"] = -4.0 * pull + 9.0 * push
    P["py"] = -HIP_H + 10.0 * (pull + push)
    P["neck"] = 4.0 * push - 3.0 * pull
    P["sh_up"] = 0.5 * (pull + push)
    _plant(P, {"r": (-36.0, 0.0, 0.0, 22.0), "l": (34.0, 0.0, 0.0, 22.0)})
    P["arm_" + side] = ARMS["door_grip"]
    P["arm_" + side + "_w"] = 1.0
    P["reach_side"] = side
    P["reach_w"] = 1.0
    P["reach_x"], P["reach_y"] = 176.0, -462.0       # the iron ring, relative to the floor point (L coords)
    return P


def _st_stumble(p, t, ph, ex):
    P = _bp()
    u = clamp(ph)
    side = ex.get("slip_foot", "r")
    P["rot"] = _keys([(0.0, 0.0), (0.12, -4.0), (0.3, -14.0), (0.5, -8.0), (0.75, 3.0), (1.0, 0.0)], u)
    P["spine"] = _keys([(0.0, 0.0), (0.3, -10.0), (0.55, 7.0), (1.0, 0.0)], u)
    P["py"] = -HIP_H + _keys([(0.0, 0.0), (0.3, 12.0), (0.55, 18.0), (1.0, 0.0)], u)
    P["neck"] = _keys([(0.0, 0.0), (0.3, -12.0), (0.6, 6.0), (1.0, 0.0)], u)
    P["tilt"] = _keys([(0.0, 0.0), (0.3, -6.0), (0.6, 3.0), (1.0, 0.0)], u)
    sf = _keys([(0.0, 12.0), (0.25, 74.0, "out"), (0.45, 30.0), (0.62, -40.0), (1.0, -26.0)], u)
    sl = _keys([(0.0, 0.0), (0.2, 34.0), (0.45, 24.0), (0.62, 0.0, "in"), (1.0, 0.0)], u)
    sp = _keys([(0.0, 0.0), (0.12, 26.0), (0.3, 18.0), (0.62, 0.0), (1.0, 0.0)], u)
    _plant(P, {side: (sf, sl, sp, 22.0), _side_other(side): (-6.0, 0.0, 0.0, 20.0)})
    P["arm_r"] = _arm_keys([(0.0, None), (0.25, ArmPose(124.0, 36.0, 0.0, "open")), (0.55, ArmPose(66.0, 42.0, 0.0, "open")),
                            (1.0, None)], u, p.arm_r)
    P["arm_l"] = _arm_keys([(0.0, None), (0.25, ArmPose(150.0, 22.0, -10.0, "open")), (0.55, ArmPose(80.0, 40.0, 0.0, "open")),
                            (1.0, None)], u, p.arm_l)
    P["arm_r_w"] = P["arm_l_w"] = 1.0
    P["wind_x"] = 120.0 * math.sin(math.pi * clamp(u / 0.5))
    P["flut"] = 0.6
    return P


def _st_hang(p, t, ph, ex):
    P = _bp()
    side = ex.get("hang_hand", "l")
    other = _side_other(side)
    sw = float(ex.get("swing", 5.0))
    kick = clamp(ex.get("kick", 0.0))
    slip = clamp(ex.get("slip", 0.0))
    P["rot"] = sw * math.sin(2 * math.pi * t / 2.7) + 2.0 * kick * noise1(t * 3.0, 4)
    P["spine"] = -2.0
    P["neck"] = -10.0
    P["sh_up"] = 0.8
    lag = -0.9 * P["rot"]
    for s_, o in ((side, 0.0), (other, 1.0)):
        P[s_ + "_th"] = 8.0 + lag + 6.0 * o + kick * 26.0 * noise1(t * 2.2 + o * 5, 11)
        P[s_ + "_kn"] = 14.0 + 10.0 * o + kick * 34.0 * (0.5 + 0.5 * noise1(t * 2.6 + o * 3, 13))
        P[s_ + "_ft"] = -28.0
        P[s_ + "_fr"] = 1.0
        P[s_ + "_sp"] = 6.0
    P["arm_" + side] = ArmPose(shoulder=174.0, elbow=6.0, wrist=6.0, hand="grip" if slip < 0.6 else "open")
    P["arm_" + side + "_w"] = 1.0
    P["arm_" + other] = ArmPose(shoulder=12.0, elbow=22.0, wrist=-30.0, hand="hold")
    P["arm_" + other + "_w"] = 0.7
    P["anchor"] = ("hand", side)
    P["anchor_w"] = 1.0
    P["slip"] = slip
    P["bturn"], P["bturn_w"] = 0.62, 1.0
    P["wind_x"] = -30.0 * math.cos(2 * math.pi * t / 2.7)
    P["flut"] = 0.25
    P["breath_k"] = 1.3
    P["breath_rate"] = 1.6
    return P


def _st_fall(p, t, ph, ex):
    P = _bp()
    P["rot"] = float(ex.get("tumble", 0.0)) + 4.0 * math.sin(t * 0.9) + 2.0 * noise1(t * 1.3, 8)
    P["spine"] = -5.0
    P["neck"] = -4.0
    P["r_th"], P["r_kn"], P["r_ft"], P["r_fr"] = 16.0 + 6 * noise1(t * 1.7, 2), 36.0, -24.0, 1.0
    P["l_th"], P["l_kn"], P["l_ft"], P["l_fr"] = -6.0 + 6 * noise1(t * 1.5, 3), 52.0, -20.0, 1.0
    P["r_sp"] = P["l_sp"] = 26.0
    P["arm_r"], P["arm_r_w"] = ArmPose(128.0 + 6 * noise1(t * 2.0, 5), 34.0, 8.0, "open"), 1.0
    P["arm_l"], P["arm_l_w"] = ArmPose(112.0 + 6 * noise1(t * 2.1, 6), 44.0, 8.0, "open"), 1.0
    P["wind_y"] = -float(ex.get("fall_speed", 900.0))
    P["flut"] = 1.0
    P["sh_up"] = 0.5
    return P


def _st_sword_drag(p, t, ph, ex):
    P = _bp()
    side = ex.get("sword_hand", "r")
    other = _side_other(side)
    sh = float(ex.get("shake", 1.0))
    jit = sh * 1.6 * noise1(t * 31.0, 7)
    P["rot"] = -12.0 + jit
    P["spine"] = 6.0
    P["neck"] = -6.0
    P["sh_up"] = 0.9
    sc = 0.5 + 0.5 * clamp(sh)
    P[side + "_th"] = 46.0 + 14.0 * sc * noise1(t * 2.3, 21)
    P[side + "_kn"] = 78.0 + 16.0 * sc * noise1(t * 2.9, 22)
    P[other + "_th"] = 24.0 + 14.0 * sc * noise1(t * 2.1, 23)
    P[other + "_kn"] = 56.0 + 18.0 * sc * noise1(t * 2.7, 24)
    for s_ in ("r", "l"):
        P[s_ + "_ft"] = -10.0
        P[s_ + "_fr"] = 1.0
        P[s_ + "_sp"] = 8.0
    P["arm_" + side] = ArmPose(shoulder=150.0, elbow=30.0, wrist=-40.0, hand="hold")
    P["arm_" + side + "_w"] = 1.0
    P["arm_" + other] = ArmPose(shoulder=146.0, elbow=36.0, wrist=-40.0, hand="hold")
    P["arm_" + other + "_w"] = 1.0
    P["anchor"] = ("wall",)
    P["anchor_w"] = 1.0
    P["bturn"], P["bturn_w"] = 0.62, 1.0
    P["wind_y"] = -300.0
    P["flut"] = 0.5
    P["shake"] = sh
    return P


def _st_lie(p, t, ph, ex):
    P = _bp()
    P["rot"] = -90.0
    P["oy"] = HIP_H - 50.0
    P["neck"] = -6.0
    P["r_th"], P["r_kn"], P["r_ft"] = -2.0, 6.0, 4.0
    P["l_th"], P["l_kn"], P["l_ft"] = 3.0, 12.0, 0.0
    P["r_sp"] = P["l_sp"] = 4.0
    P["bturn"], P["bturn_w"] = 0.8, 1.0
    P["lying"] = 1.0
    P["breath_k"] = 1.25
    P["sh_up"] = -0.2
    return P


def _st_crumpled(p, t, ph, ex):
    P = _st_lie(p, t, ph, ex)
    P["rot"] = -84.0
    P["oy"] = HIP_H - 56.0
    P["neck"] = -14.0
    P["tilt"] = 8.0
    P["r_th"], P["r_kn"], P["r_ft"] = 38.0, 76.0, -6.0
    P["l_th"], P["l_kn"], P["l_ft"] = -4.0, 18.0, 0.0
    P["r_sp"], P["l_sp"] = 18.0, 4.0
    P["arm_r"], P["arm_r_w"] = ArmPose(64.0, 44.0, 10.0, "relaxed"), 0.85
    P["arm_l"], P["arm_l_w"] = ArmPose(-8.0, 24.0, 0.0, "relaxed"), 0.85
    return P


def _st_prop_sit(p, t, ph, ex):
    P = _bp()
    P["py"] = -74.0
    P["rot"] = -12.0
    P["spine"] = 5.0
    P["neck"] = 4.0
    ku = clamp(ex.get("knee_up", 0.55))
    P["r_th"], P["r_kn"], P["r_ft"] = 74.0, 20.0, 10.0
    P["l_th"], P["l_kn"], P["l_ft"] = 92.0 + 34.0 * ku, 24.0 + 86.0 * ku, 12.0 - 10.0 * ku
    P["r_sp"], P["l_sp"] = 22.0, 18.0
    P["sitting"] = 1.0
    P["breath_k"] = 1.15
    return P


def _st_sleep(p, t, ph, ex):
    P = _st_prop_sit(p, t, ph, ex)
    P["tilt"] = float(ex.get("sleep_tilt", 15.0))
    P["neck"] = 16.0
    P["nod"] = -0.15
    P["spine"] = 8.0
    P["sh_up"] = -0.45
    P["sleep"] = 1.0
    P["breath_k"] = 1.6
    P["breath_rate"] = 0.8
    P["mouth_add"] = 0.12
    return P


_STATE_FN = {"stand": _st_stand, "walk": _st_walk, "run": _st_run, "chop": _st_chop, "swipe": _st_swipe,
             "door_push": _st_door, "charge": _st_charge, "stumble": _st_stumble, "hang": _st_hang,
             "fall": _st_fall, "sword_drag": _st_sword_drag, "crumpled": _st_crumpled, "lie_back": _st_lie,
             "prop_sit": _st_prop_sit, "sleep": _st_sleep}


def _phase(p, key="phase"):
    ex = p.extra
    if key in ex and ex[key] is not None:
        return float(ex[key])
    if key == "phase" and p.walk is not None:
        return float(p.walk)
    return 0.0


def _params(p, t):
    ex = p.extra
    st = ex.get("state", "walk" if p.walk is not None else "stand")
    if st not in _STATE_FN:
        st = "walk" if p.walk is not None else "stand"
    P = _STATE_FN[st](p, t, _phase(p), ex)
    st2 = ex.get("state_b")
    m = clamp(ex.get("mix", 0.0)) if st2 else 0.0
    if st2 in _STATE_FN and m > 0.0:
        ph2 = float(ex.get("phase_b", _phase(p)))
        B = _STATE_FN[st2](p, t, ph2, ex)
        out = {}
        for k, v in P.items():
            if k in _ARMLESS or k == "reach_side":
                continue
            out[k] = v + (B[k] - v) * m
        for side in ("r", "l"):
            a, b = P["arm_" + side], B["arm_" + side]
            wa, wb = P["arm_" + side + "_w"], B["arm_" + side + "_w"]
            if a is not None and b is not None:
                out["arm_" + side] = ArmPose.blend(a, b, m)
            else:
                out["arm_" + side] = a if a is not None else b
            out["arm_" + side + "_w"] = lerp(wa if a is not None else 0.0, wb if b is not None else 0.0, m)
        out["anchor"] = B["anchor"] if (B["anchor"] is not None and (m >= 0.5 or P["anchor"] is None)) else P["anchor"]
        out["reach_side"] = B["reach_side"] if (B["reach_side"] is not None and (m >= 0.5 or P["reach_side"] is None)) else P["reach_side"]
        P = out
    P["state"] = st
    return P


# =========================================================================== solver
def _blade_reach(embed=0.0):
    """Distance from the grip centre to the blade point (embed 0) / to where an embedded blade enters the rock."""
    return SWORD_GRIP * 0.5 + 10.0 + SWORD_BLADE * (1.0 - embed)


# torso profile (y relative to NECK_Y): half width, front depth, back depth
_TTAB = [(0.0, 54.0, 44.0, 42.0), (12.0, 94.0, 56.0, 54.0), (30.0, 117.0, 67.0, 62.0), (54.0, 118.0, 76.0, 64.0),
         (88.0, 112.0, 79.0, 64.0), (122.0, 101.0, 73.0, 60.0), (154.0, 91.0, 65.0, 54.0), (176.0, 87.0, 61.0, 52.0),
         (200.0, 86.0, 59.0, 51.0), (224.0, 88.0, 59.0, 52.0)]
_HEAD_REG = (47.0, 58.0, 50.0)       # rough head / beard section for hand targets above the torso


def _tprof(y):
    if y < 0.0:
        k = clamp(-y / 40.0)
        a0, f0, b0 = _tab(_TTAB, 0.0)
        return lerp(a0, _HEAD_REG[0], k), lerp(f0, _HEAD_REG[1], k), lerp(b0, _HEAD_REG[2], k)
    return _tab(_TTAB, y)


def _tsil(R, y, side, dr=0.0):
    a, zf, zb = _tprof(y)
    a += dr
    z = (zf if side * R.sb >= 0 else zb) + dr
    return side * math.sqrt(a * a * R.cb * R.cb + z * z * R.sb * R.sb)


def _tp(R, x0, y, dz=0.0):
    """Torso front-surface point (front-view x0, y relative to NECK_Y) -> chest coords (x, y), depth."""
    a, zf, _ = _tprof(y)
    u = clamp(x0 / max(a, 1e-3), -0.995, 0.995)
    z = zf * math.sqrt(1.0 - u * u) + dz
    return x0 * R.cb + z * R.sb, NECK_Y + y, -x0 * R.sb + z * R.cb


def _taz(R, phi_deg, y, dr=0.0):
    a, zf, zb = _tprof(y)
    ph = phi_deg * D2R
    sp, cp = math.sin(ph), math.cos(ph)
    zz = zf if cp >= 0 else zb
    x0, z = (a + dr) * sp, (zz + dr) * cp
    vis = -sp / max(a + dr, 1e-3) * R.sb + cp / max(zz + dr, 1e-3) * R.cb
    return x0 * R.cb + z * R.sb, NECK_Y + y, vis * 50.0


def _arm_solve(R, side, ap, P, swing):
    """FK (+ across / behind pulls) for one arm in chest coords."""
    A = _NS()
    slot = R.slot[side]
    A.side, A.slot = side, slot
    A.near = (slot * (R.sb if abs(R.sb) > 1e-3 else 1.0)) < 0 if abs(R.tb) > 0.02 else slot < 0
    ax = lerp(slot * 0.72, 1.0, R.wf)
    A.ax = ax
    sh_ang = ap.shoulder
    el = ap.elbow
    if swing:
        k = clamp(1.0 - abs(sh_ang) / 110.0)
        sh_ang += swing * k
        el += max(0.0, swing) * 0.45 * k
    S = (slot * SH_X * R.cb, NECK_Y + SH_DY - 10.0 * (P["sh_up"] + R.sh_up_pose) - 1.8 * R.br)
    abd = (1.0 - 0.55 * R.wf)
    a1 = sh_ang
    a2 = a1 + el
    ah = a2 + ap.wrist
    d1 = _dirv(a1)
    d2 = _dirv(a2)
    E = (S[0] + UPPER * d1[0] * ax + slot * 16.0 * abd, S[1] + UPPER * d1[1])
    W = (E[0] + FORE * d2[0] * ax + slot * 12.0 * abd, E[1] + FORE * d2[1])
    dh = _dirv(ah)
    hv = _norm(dh[0] * ax, dh[1])
    fv = _norm(W[0] - E[0], W[1] - E[1])
    A.hrel = _ang_of(*hv) - _ang_of(*fv)          # hand angle relative to the forearm (2D)
    A.S, A.E, A.W = S, E, W
    A.Efk = E
    A.shape = ap.hand
    A.across = clamp(ap.across)
    A.behind = clamp(ap.behind)
    pulled = False
    if A.across > 0.0:
        yy = clamp(W[1] - NECK_Y, -95.0, 190.0)
        phi = lerp(slot * 70.0, -slot * 62.0, A.across)
        tx, ty, _ = _taz(R, phi, yy, 24.0 + 6.0 * (1 - A.across))
        k = min(1.0, A.across * 2.2)
        W = (lerp(W[0], tx, k), lerp(W[1], ty, k * 0.6))
        pulled = True
    if A.behind > 0.0:
        yy = clamp(W[1] - NECK_Y, 60.0, 230.0)
        tx, ty, _ = _taz(R, slot * 150.0, yy, 20.0)
        W = (lerp(W[0], tx, A.behind), lerp(W[1], ty, A.behind))
        pulled = True
    if pulled:
        _arm_ik(A, W)
    return A


def _elbow_side(R, A, W, k):
    """Which side of the shoulder->wrist line the elbow goes, -1..1 (+1 = the normal n = (-d_y, d_x)), for
    reach-type IK (door ring, reach_l / reach_r, the two-handed grip). Anatomical rule: the elbow points OUT (the
    arm's own side) + DOWN + a little BACK (projected for the body turn), plus a flexion term in the arm plane (the
    forearm folds toward the biceps, never backward), so a hand reaching forward / down never flips its elbow up
    and across the chest. Near the indifferent direction the side changes smoothly (the elbow swivels through the
    line, i.e. points at the camera for a moment) instead of popping; k (the reach weight) fades the rule in from
    the FK elbow's side, so a reach starting / ending on the free arm pose is continuous."""
    S, Efk = A.S, A.Efk
    px, py = A.slot * 0.6 * R.cb - 0.42 * R.sb, 1.0
    pl = math.hypot(px, py)
    dx, dy = W[0] - S[0], W[1] - S[1]
    dl = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / dl, dx / dl
    # flexion weight (turned views): it decides alone (> any pole term) unless the hand is well above the shoulder,
    # so a hand that sweeps around the shoulder at or below its height never flips the elbow; overhead / behind the
    # head the pole takes over and the elbow flares OUT; none in the stylised front view (arms swing to the sides)
    kf = clamp(A.ax, -1.0, 1.0) * R.wf * (0.25 + 0.95 * smoothstep((dy / dl + 0.9) / 0.4))
    pole = (nx * px + ny * py) / pl + kf
    s_pole = clamp(pole / 0.15, -1.0, 1.0)
    if k >= 1.0:
        return s_pole
    # the FK elbow's side, soft (a near-straight FK arm must not flip the elbow from frame to frame)
    d = clamp(dl, abs(UPPER - FORE) + 1e-3, UPPER + FORE)
    a = (UPPER * UPPER - FORE * FORE + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, UPPER * UPPER - a * a))
    s_fk = clamp(((Efk[0] - S[0]) * nx + (Efk[1] - S[1]) * ny) / max(0.5 * h, 4.0), -1.0, 1.0)
    return lerp(s_fk, s_pole, clamp(k))


def _arm_ik(A, W, R=None, k=1.0):
    """Re-solve the elbow for wrist target W. With R: reach-type IK, the elbow side from _elbow_side (weight k);
    without it (across / behind pulls of the presets) the elbow nearest the FK pose wins."""
    Efk = A.Efk
    if R is not None:
        S = A.S
        dx, dy = W[0] - S[0], W[1] - S[1]
        d0 = math.hypot(dx, dy)
        if d0 < 1e-6:
            dx, dy, d0 = 0.0, 1.0, 1.0
        ux, uy = dx / d0, dy / d0
        d = clamp(d0, abs(UPPER - FORE) + 1e-3, UPPER + FORE)
        a = (UPPER * UPPER - FORE * FORE + d * d) / (2.0 * d)
        h = math.sqrt(max(0.0, UPPER * UPPER - a * a))
        sd = _elbow_side(R, A, W, k)
        E = (S[0] + ux * a - uy * h * sd, S[1] + uy * a + ux * h * sd)
    else:
        near = (lambda j1, j2: j1 if math.hypot(j1[0] - Efk[0], j1[1] - Efk[1]) <= math.hypot(j2[0] - Efk[0], j2[1] - Efk[1]) else j2)
        E = _ik(A.S, W, UPPER, FORE, near)
    fv = _norm(W[0] - E[0], W[1] - E[1])
    d = math.hypot(W[0] - A.S[0], W[1] - A.S[1])
    if d > UPPER + FORE:
        W = (E[0] + fv[0] * FORE, E[1] + fv[1] * FORE)
    A.E, A.W = E, W


def _hand_frame(A):
    """2D hand direction (from-down angle) and palm centre, chest coords."""
    fv = _norm(A.W[0] - A.E[0], A.W[1] - A.E[1])
    A.ha = _ang_of(*fv) + A.hrel
    hv = _dirv(A.ha)
    A.palm = (A.W[0] + hv[0] * PALM, A.W[1] + hv[1] * PALM)


def _arm_to_L(R, A):
    M = R.MC
    A.Sl, A.El, A.Wl, A.Pl = _mp(M, A.S), _mp(M, A.E), _mp(M, A.W), _mp(M, A.palm)
    hv = _dirv(A.ha)
    q = _mp(M, (A.W[0] + hv[0] * 10.0, A.W[1] + hv[1] * 10.0))
    A.hal = _ang_of(q[0] - A.Wl[0], q[1] - A.Wl[1])


def _solve(p: Pose, t):
    R = _NS()
    ex = p.extra if p.extra is not None else {}
    tt = 0.0 if t is None else float(t)
    R.t = tt
    fac = 1.0 if p.facing >= 0 else -1.0
    R.fac = fac
    R.slot = {"r": -1 if fac > 0 else 1, "l": 1 if fac > 0 else -1}
    P = _params(p, tt)
    R.P = P
    R.state = P["state"]
    tb = clamp(p.turn, -0.45, 0.9)
    if P["bturn_w"] > 0:
        tb = lerp(tb, max(tb, P["bturn"]), clamp(P["bturn_w"]))
    R.tb = tb
    thb = tb * TURN_DEG * D2R
    R.cb, R.sb = math.cos(thb), math.sin(thb)
    R.fk = lerp(0.3, 1.0, smoothstep(abs(tb) / 0.4))
    R.wf = smoothstep(abs(tb) / 0.35)
    if p.breath is not None:
        br = p.breath
    else:
        br = breathe(tt, 0.2 * P["breath_rate"], 2) * P["breath_k"]
    R.br = br
    R.sleep = clamp(P["sleep"])
    R.mouth_add = P["mouth_add"] * (1.0 + 0.6 * max(0.0, br)) if P["sleep"] > 0 else P["mouth_add"]
    R.lying, R.sitting = P["lying"], P["sitting"]
    R.sh_up_pose = clamp(p.shoulders_up, -1.0, 1.0)
    # ---- matrices
    MS = skia.Matrix()
    MS.setTranslate(p.x, p.y)
    MS.preScale(fac * p.scale, p.scale)
    R.MS = MS
    px, py = P["px"], P["py"] + p.bounce
    R.px, R.py = px, py
    MB0 = skia.Matrix()
    MB0.setTranslate(P["ox"], P["oy"])
    MB0.preRotate(P["rot"], px, py)
    dpy = py + HIP_H
    spine = P["spine"] + p.lean
    R.spine = spine

    def chest_m(MB):
        MC = skia.Matrix.Concat(MB, skia.Matrix())
        MC.preTranslate(px, dpy)
        MC.preRotate(spine, 0.0, WAIST_Y)
        MC.preScale(1.0 + 0.016 * br, 1.0 + 0.006 * br, 0.0, WAIST_Y)
        return MC

    R.MB, R.MC = MB0, chest_m(MB0)
    # ---- arms (chest coords)
    arms = {}
    ca = clamp(ex.get("cross_arms", 0.0))
    aw = clamp(ex.get("arms_w", 1.0))
    for side in ("r", "l"):
        ap = getattr(p, "arm_" + side)
        ov, w = P["arm_" + side], P["arm_" + side + "_w"] * aw
        if ov is not None and w > 0:
            ap = ArmPose.blend(ap, ov, w)
        if ca > 0:
            slot = R.slot[side]
            near = slot * (1 if tb >= 0 else -1) < 0
            ap = ArmPose.blend(ap, _CROSS_NEAR if near else _CROSS_FAR, ca)
        sw = 0.0
        if P["swing"]:
            sw = P["swing"] * math.cos(2 * math.pi * P["swing_ph"]) * (-1.0 if side == "r" else 1.0)
        A = _arm_solve(R, side, ap, P, sw)
        A.ap = ap
        arms[side] = A
    R.arms = arms
    # door ring etc.: reach target given in L coords by the state, or stage coords via extra reach_r / reach_l
    inv = skia.Matrix()
    for side in ("r", "l"):
        A = arms[side]
        tgt, w = None, 0.0
        if P["reach_side"] == side and P["reach_w"] > 0:
            ring = ex.get("ring")
            if ring is not None:
                iv = skia.Matrix()
                MS.invert(iv)
                tgt = _mp(iv, ring)
            else:
                tgt = (P["reach_x"], P["reach_y"])
            w = P["reach_w"]
        rk = ex.get("reach_" + side)
        if rk is not None:
            iv = skia.Matrix()
            MS.invert(iv)
            tgt = _mp(iv, rk)
            w = clamp(ex.get("reach_" + side + "_w", 1.0))
        if tgt is not None and w > 0 and R.MC.invert(inv):
            tc = _mp(inv, tgt)
            # target is the palm: back off to the wrist along the current hand direction
            _hand_frame(A)
            hv = _dirv(A.ha)
            wt = (tc[0] - hv[0] * PALM, tc[1] - hv[1] * PALM)
            _arm_ik(A, (lerp(A.W[0], wt[0], w), lerp(A.W[1], wt[1], w)), R, w)
    for A in arms.values():
        _hand_frame(A)
    # ---- props (decided before anchoring)
    R.sword = ex.get("sword", "hand")
    if R.sword == "sheathed":
        R.sword = "back"
    R.sword_hand = ex.get("sword_hand", "r")
    R.torch = ex.get("torch", None)
    if R.torch is True:
        R.torch = "l"
    R.torch_flame = clamp(ex.get("torch_flame", 1.0))
    R.embed = clamp(ex.get("embed", 0.78), 0.0, 0.95)
    R.shield = ex.get("shield", "back")
    R.two_hand = bool(ex.get("two_hand", False)) or R.state == "sword_drag"
    # ---- anchoring (hang: the gripping hand; sword_drag: the blade's entry point in the wall)
    off = (0.0, 0.0)
    anc = P["anchor"]
    if anc is not None and P["anchor_w"] > 0:
        if anc[0] == "hand":
            A = arms[anc[1]]
            hv = _dirv(A.ha)
            pt = _mp(R.MC, (A.W[0] + hv[0] * 38.0, A.W[1] + hv[1] * 38.0))     # top of the curled fingers
            pt = (pt[0], pt[1] - 14.0 * P["slip"])
        else:
            A = arms[R.sword_hand]
            g = _mp(R.MC, A.palm)
            tilt = float(ex.get("sword_tilt", 8.0))
            ax_ = _dirv(90.0 - tilt)
            dist = _blade_reach(R.embed)
            pt = (g[0] + ax_[0] * dist, g[1] + ax_[1] * dist)
        w = P["anchor_w"]
        off = (-pt[0] * w, -pt[1] * w)
    MB = skia.Matrix()
    MB.setTranslate(off[0], off[1])
    MB.preConcat(MB0)
    R.MB = MB
    R.MC = chest_m(MB)
    for A in arms.values():
        _arm_to_L(R, A)
    # ---- held props in L coords
    R.props = {}
    if R.sword == "hand" or R.state == "sword_drag":
        A = arms[R.sword_hand]
        ang = A.hal + PROP_GRIP_DEG
        if R.state == "sword_drag":
            ang = 90.0 - float(ex.get("sword_tilt", 8.0))
        elif ex.get("sword_angle") is not None:
            ang = 180.0 - float(ex["sword_angle"])
        R.props["sword"] = (A.Pl, ang, A)
    if R.torch in ("l", "r"):
        A = arms[R.torch]
        ang = A.hal + PROP_GRIP_DEG
        if ex.get("torch_angle") is not None:
            ang = 180.0 - float(ex["torch_angle"])
        R.props["torch"] = (A.Pl, ang, A)
    # two hands on the sword: the off hand closes on the grip, toward the pommel
    if R.two_hand and "sword" in R.props:
        g, ang, A0 = R.props["sword"]
        other = arms[_side_other(R.sword_hand)]
        dv = _dirv(ang)
        tgt = (g[0] - dv[0] * 24.0, g[1] - dv[1] * 24.0)
        if R.MC.invert(inv):
            tc = _mp(inv, tgt)
            hv = _dirv(other.ha)
            # the off hand's direction: same grip as the main hand (prop axis = hand + PROP_GRIP)
            hl_target = ang - PROP_GRIP_DEG
            rotc = _ang_of(*_norm(*(lambda a, b: (b[0] - a[0], b[1] - a[1]))(_mp(R.MC, (0, 0)), _mp(R.MC, (0, 10)))))
            hc = hl_target - rotc
            hv = _dirv(hc)
            wt = (tc[0] - hv[0] * PALM, tc[1] - hv[1] * PALM)
            _arm_ik(other, wt, R)
            fv = _norm(other.W[0] - other.E[0], other.W[1] - other.E[1])
            other.hrel = hc - _ang_of(*fv)
            other.shape = "hold"
            _hand_frame(other)
            _arm_to_L(R, other)
    # ---- arm layers
    for A in arms.values():
        A.layer = _arm_layer(R, A)
    # ---- legs (upright body coords -> L)
    legs = {}
    for side in ("r", "l"):
        L = _NS()
        slot = R.slot[side]
        L.side, L.slot = side, slot
        hip = (px + slot * HIP_LAT * R.cb, py)
        th, kn, sp = P[side + "_th"], P[side + "_kn"], P[side + "_sp"]
        d1 = _dirv(th)
        knee = (hip[0] + THIGH * d1[0] * R.fk + slot * sp * 0.45 * R.cb, hip[1] + THIGH * d1[1])
        d2 = _dirv(th - kn)
        ank = (knee[0] + SHIN * d2[0] * R.fk + slot * sp * 0.55 * R.cb, knee[1] + SHIN * d2[1])
        fa = lerp(90.0 + P[side + "_ft"], (th - kn) + 90.0 + P[side + "_ft"], P[side + "_fr"])
        L.hip, L.knee, L.ankle = _mp(MB, hip), _mp(MB, knee), _mp(MB, ank)
        fd = _dirv(fa)
        fdv = _norm(fd[0] * R.fk, fd[1])
        L.fl = math.hypot(fd[0] * R.fk, fd[1])               # foreshortening of the foot
        q = _mp(MB, (ank[0] + fdv[0] * 10.0, ank[1] + fdv[1] * 10.0))
        L.fang = _ang_of(q[0] - L.ankle[0], q[1] - L.ankle[1])
        L.near = (slot * (1 if tb >= 0 else -1)) < 0
        legs[side] = L
    R.legs = legs
    # ---- head
    ndl = p.head_nod + P["nod"]
    pitch = P["neck"] - 15.0 * ndl
    thh = clamp(p.turn + p.head_turn, -0.65, 0.95) * TURN_DEG * D2R
    H = _NS()
    H.c, H.s = math.cos(thh), math.sin(thh)
    H.th = thh
    H.ndy = pitch * 0.32 * H.c
    H.bulk = 1.0
    R.H = H
    R.F = _face_params(p, R, tt)
    H.jaw = R.F.open
    H.sm = (R.F.smirk_slot, R.F.smirk + 0.4 * R.F.sup)
    rot2d = p.head_tilt + P["tilt"] + pitch * H.s * 0.85
    MH = skia.Matrix.Concat(R.MC, skia.Matrix())
    pv = (NECK_PIVOT[0] * R.sb, NECK_PIVOT[1] - 1.2 * br)
    MH.preTranslate(pv[0], pv[1])
    MH.preRotate(rot2d)
    MH.preTranslate(0.0, -EYE_ABOVE_PIVOT)
    MH.preScale(HEAD_S, HEAD_S)
    R.MH = MH
    R.pivot = pv
    return R


def _arm_layer(R, A):
    if A.behind > 0.5:
        return "back"
    if A.near:
        # raised high beside the head (hang, sword_drag, torch_up, swat ...): drawn under the head so the face
        # stays readable (the hand / forearm are above the head anyway)
        if A.W[1] < NECK_Y - 120.0 and A.E[1] < A.S[1] - 50.0 and A.across < 0.3:
            return "under"
        return "near"
    # far arm: behind the torso unless it comes forward / across
    fwd = A.W[0] - _tsil(R, clamp(A.W[1] - NECK_Y, 0.0, 224.0), 1 if R.sb >= 0 else -1)
    high = A.W[1] < NECK_Y - 10.0
    if A.across > 0.3 or (fwd > -10.0 and A.W[1] < NECK_Y + 150.0) or (high and A.W[0] * (1 if R.sb >= 0 else -1) > 20):
        if A.W[1] < NECK_Y - 20.0 and A.across > 0.3:
            return "top"
        return "front"
    return "back"


# =========================================================================== public anchors
def _stage(R, M, pt):
    q = _mp(M, pt)
    return _mp(R.MS, q)


def head_center(pose: Pose, t=None):
    """Stage point between the eyes."""
    R = _solve(pose, t)
    x, y, _ = _hp(R.H, 0.0, -1.0, 2.0)
    return _stage(R, R.MH, (x, y))


def eye_pos(pose: Pose, side: str, t=None):
    R = _solve(pose, t)
    slot = R.slot[side]
    x, y, _ = _hp(R.H, slot * EX, 0.0, -3.0)
    return _stage(R, R.MH, (x, y))


def mouth_pos(pose: Pose, t=None):
    R = _solve(pose, t)
    x, y, _ = _hp(R.H, 0.0, MOUTH_Y + 2.0, 8.0)
    return _stage(R, R.MH, (x, y))


def face_pos(pose: Pose, x0: float, y0: float, t=None, dz: float = 0.0):
    """Stage point of a spot on the face given in front-view head coords (x0 > 0 = toward Anger's LEFT, y0 down
    from the eye line; eyes at (+-20.5, 0), nose tip (0, 18), mouth (0, 38), cheekbones (+-30, 12), chin beard
    (0, 80)). E.g. a drip landing on the cheek nearer the camera: face_pos(p, -26 * near_sign, 16)."""
    R = _solve(pose, t)
    xl = x0 * (1.0 if R.slot["l"] > 0 else -1.0)
    x, y, _ = _hp(R.H, xl, y0, dz)
    return _stage(R, R.MH, (x, y))


def near_side(pose: Pose) -> str:
    """'r' or 'l': which of Anger's sides is nearer the camera (his right when facing +1 and turned)."""
    return "r" if (pose.facing >= 0) == (pose.turn >= 0) else "l"


def hand_pos(pose: Pose, side: str, t=None):
    """Stage point at the palm centre of Anger's 'l' / 'r' gauntlet (on a held prop: the grip point)."""
    R = _solve(pose, t)
    return _mp(R.MS, R.arms[side].Pl)


def pelvis_pos(pose: Pose, t=None):
    R = _solve(pose, t)
    return _mp(R.MS, _mp(R.MB, (R.px, R.py)))


def _torch_geom(R):
    if "torch" not in R.props:
        return None
    g, ang, A = R.props["torch"]
    dv = _dirv(ang)
    head = (g[0] + dv[0] * (TORCH_LEN - TORCH_GRIP - 22.0), g[1] + dv[1] * (TORCH_LEN - TORCH_GRIP - 22.0))
    return g, ang, head


def torch_pos(pose: Pose, t=None):
    """Stage point of the torch flame's centre (the scene's light source), or None without a torch in hand."""
    R = _solve(pose, t)
    tg = _torch_geom(R)
    if tg is None:
        return None
    hx, hy = _mp(R.MS, tg[2])
    return hx, hy - 30.0 * pose.scale


def sword_tip_pos(pose: Pose, t=None):
    """Stage point of the blade tip; in 'sword_drag' the point where the blade enters the wall (= pose.x, y)."""
    R = _solve(pose, t)
    if "sword" not in R.props:
        return None
    g, ang, A = R.props["sword"]
    dv = _dirv(ang)
    if R.state == "sword_drag":
        d = _blade_reach(R.embed)
    else:
        d = _blade_reach(0.0)
    return _mp(R.MS, (g[0] + dv[0] * d, g[1] + dv[1] * d))


# =========================================================================== timing helpers
def cycle_len(state):
    return RUN_CYCLE if state in ("run", "charge") else WALK_CYCLE


def walk_advance(pose: Pose) -> float:
    """Stage units the floor point must move per cycle (toward facing) so the planted foot does not skate."""
    st = pose.extra.get("state", "walk" if pose.walk is not None else "stand")
    base = RUN_ADVANCE if st in ("run", "charge") else WALK_ADVANCE
    return base * lerp(0.3, 1.0, smoothstep(abs(pose.turn) / 0.4)) * pose.scale


def phase_at(state, t, t0=0.0, phase0=0.0):
    """Cycle phase at time t for a walk / run / charge that had phase0 at t0 (fixed BIBLE cadence)."""
    return phase0 + (t - t0) / cycle_len(state)


def step_times(state, t0, t1, phase0=0.0):
    """Foot-plant times in [t0, t1]. walk / run / charge: the phase advances at the fixed cadence from phase0
    at t0; the right foot plants at phase 0 (mod 1), the left at 0.5. chop: the front-foot stamp, door_push /
    stumble: the recovering foot - for these actions phase runs 0 -> 1 over [t0, t1] (phase0 = start)."""
    out = []
    if state in ("walk", "run", "charge"):
        cl = cycle_len(state)
        k = math.ceil(phase0 * 2.0 - 1e-9)
        while True:
            tk = t0 + (k * 0.5 - phase0) * cl
            if tk > t1 + 1e-9:
                break
            if tk >= t0 - 1e-9:
                out.append(round(tk, 4))
            k += 1
        return out
    ev = {"chop": (0.5,), "stumble": (0.25, 0.62), "door_push": (), "swipe": ()}.get(state, ())
    span = t1 - t0
    for u in ev:
        if u >= phase0 and span > 0:
            out.append(round(t0 + (u - phase0) / max(1e-6, 1.0 - phase0) * span, 4))
    return out


def step_events(state, t0, t1, phase0=0.0, gain_db=-6.0):
    """step_times() as scene sfx events: [{"name": "armor_step" | "armor_step_run", "start", "gain_db"}]."""
    name = "armor_step_run" if state in ("run", "charge") else "armor_step"
    return [{"name": name, "start": tk, "gain_db": gain_db} for tk in step_times(state, t0, t1, phase0)]


# =========================================================================== drawing: small props (stage-free)
def _flame_path(w, h, lean, wob, tt):
    """Teardrop flame standing on its base (0, 0), tip up (-y)."""
    n = 7
    right, left = [], []
    for i in range(1, n):
        u = i / n
        y = -h * u
        hw = w * 0.5 * math.sin(math.pi * (0.18 + 0.82 * u) ** 0.9) * (1.0 - u) ** 0.35
        xc = lean * h * u * u + wob * math.sin(tt * 9.0 + u * 7.0) * u
        right.append((xc + hw, y))
        left.append((xc - hw, y))
    tip = (lean * h + wob * math.sin(tt * 9.0 + 7.0), -h * 1.02)
    return _loop([tip] + right[::-1] + [(0.0, w * 0.22)] + left, 0.55)


def _draw_flame_local(c, t, s=1.0, intensity=1.0, wind=(0.0, 0.0), seed=0):
    """Flickering torch flame with its base at the canvas origin (canvas y down = world down). Unfiltered."""
    if intensity <= 0.01:
        return
    f1 = noise1(t * 7.3, 31 + seed)
    f2 = noise1(t * 11.7, 37 + seed)
    f3 = noise1(t * 3.1, 41 + seed)
    h = 64.0 * s * intensity * (1.0 + 0.14 * f1 + 0.06 * f2)
    w = 34.0 * s * (0.75 + 0.25 * intensity) * (1.0 + 0.08 * f2)
    lean = clamp(0.18 * f3 - wind[0] / 900.0, -0.9, 0.9)
    c.drawPath(_flame_path(w * 1.25, h * 1.15, lean, 3.0 * s, t), _core_paint("torch_ember", 0.55 * intensity, blur=3.0 * s))
    c.drawPath(_flame_path(w, h, lean, 2.6 * s, t + 0.3), _core_paint("torch_ember", 0.95 * intensity))
    c.drawPath(_flame_path(w * 0.72, h * 0.78, lean * 0.9, 2.0 * s, t + 0.7), _core_paint("torch_flame", 0.98))
    c.drawPath(_flame_path(w * 0.42, h * 0.48, lean * 0.7, 1.2 * s, t + 1.1), _core_paint("torch_core", 0.95))
    # licking side tongues
    for k, sx in ((0, -1.0), (1, 1.0)):
        ph = (t * (1.7 + 0.4 * k) + 0.37 * k) % 1.0
        hh = h * (0.35 + 0.3 * ph)
        c.save()
        c.translate(sx * w * 0.22, -h * (0.15 + 0.35 * ph))
        c.drawPath(_flame_path(w * 0.28 * (1 - ph), hh * (1 - ph), lean + sx * 0.25, 1.0 * s, t + k),
                   _core_paint("torch_flame", 0.75 * intensity * (1 - ph)))
        c.restore()


def _draw_torch_local(c, t, flame=1.0, burnt=0.0):
    """Torch in its own frame: grip at the origin, +y toward the burning head. The flame is not drawn."""
    L0, L1 = -TORCH_GRIP, TORCH_LEN - TORCH_GRIP
    shaft = _capsule((0.0, L0), (0.0, L1 - 40.0), 6.5, 8.0)
    _cel(c, shaft, C_WOOD, C_WOOD_DK, k=3.0, line=C_LEATHER_LINE, line_w=1.1)
    for y in (L0 + 18.0, L0 + 52.0):
        _stroke(c, _curve([(-6.0, y), (6.0, y + 3.0)]), C_WOOD_DK, 1.2, 0.7)
    head = _loop([(-9.0, L1 - 48.0), (9.0, L1 - 48.0), (13.0, L1 - 26.0), (12.0, L1 - 4.0), (7.0, L1 + 2.0),
                  (-7.0, L1 + 2.0), (-12.0, L1 - 4.0), (-13.0, L1 - 26.0)], 0.5)
    _cel(c, head, mix_col("#3A2A1E", "#1A120C", burnt), col("#15100C"), k=3.0, line=C_LEATHER_LINE, line_w=1.0)
    for i, y in enumerate((L1 - 42.0, L1 - 30.0, L1 - 18.0)):
        _stroke(c, _curve([(-12.0, y + 3.0), (0.0, y - 1.0), (12.5, y + 2.0)]), col("#5A4632"), 1.6, 0.8)
    if flame > 0.02:
        c.drawCircle(0.0, L1 - 2.0, 9.0, _core_paint("torch_ember", 0.8 * flame, blur=3.0))


def _draw_sword_local(c, scabbard=False, nick=True):
    """Broadsword in its own frame: grip centre at the origin, +y toward the point."""
    G = SWORD_GRIP * 0.5
    L = SWORD_BLADE
    b0 = G + 10.0
    if scabbard:
        sc = _loop([(-15.0, b0), (15.0, b0), (13.5, b0 + L * 0.9), (6.0, b0 + L + 6.0), (-6.0, b0 + L + 6.0),
                    (-13.5, b0 + L * 0.9)], 0.3)
        _cel(c, sc, C_LEATHER, C_LEATHER_SH, k=4.0, line=C_LEATHER_LINE, line_w=1.3)
        chape = _loop([(-13.6, b0 + L * 0.86), (13.6, b0 + L * 0.86), (6.5, b0 + L + 7.0), (-6.5, b0 + L + 7.0)], 0.3)
        _metal(c, chape, (-14.0, 0.0), (14.0, 0.0))
        for y in (b0 + 30.0, b0 + L * 0.5):
            _stroke(c, _curve([(-15.0, y), (15.0, y)]), C_LEATHER_LINE, 2.0, 0.7)
    else:
        blade = _poly([(-13.5, b0 - 2.0), (13.5, b0 - 2.0), (11.0, b0 + L * 0.84), (0.0, b0 + L), (-11.0, b0 + L * 0.84)])
        _metal(c, blade, (-14.0, 0.0), (14.0, 0.0), lw=1.3, gloss=1.4)
        fuller = _poly([(-3.0, b0 + 10.0), (3.0, b0 + 10.0), (2.0, b0 + L * 0.62), (0.0, b0 + L * 0.66), (-2.0, b0 + L * 0.62)])
        _fill(c, fuller, C_STEEL_DK, 0.55)
        lx, ly = _lv(c, 1.0)
        es = 1.0 if lx >= 0 else -1.0
        _stroke(c, _curve([(es * 12.2, b0 + 6.0), (es * 10.4, b0 + L * 0.82), (0.0, b0 + L - 2.0)]), C_STEEL_HI, 1.4, 0.8)
        if nick:
            for y, sd in ((b0 + L * 0.35, -1.0), (b0 + L * 0.58, 1.0)):
                x = sd * 12.5
                _fill(c, _poly([(x, y), (x - sd * 4.0, y + 3.0), (x, y + 6.0)]), C_STEEL_DK, 0.9)
    guard = _loop([(-50.0, G + 2.0), (-30.0, G - 1.0), (0.0, G + 1.0), (30.0, G - 1.0), (50.0, G + 2.0), (48.0, G + 10.0),
                   (30.0, G + 11.0), (0.0, G + 13.0), (-30.0, G + 11.0), (-48.0, G + 10.0)], 0.4)
    _metal(c, guard, (0.0, G - 2.0), (0.0, G + 14.0), base=C_STEEL_SH, shade=C_STEEL_DK)
    _rivet(c, 0.0, G + 6.5, 3.4)
    grip = _loop([(-7.5, -G), (7.5, -G), (8.0, G), (-8.0, G)], 0.2)
    _cel(c, grip, C_LEATHER, C_LEATHER_SH, k=2.0, line=C_LEATHER_LINE, line_w=1.0)
    for i in range(6):
        y = -G + 6.0 + i * (2 * G - 10.0) / 5.0
        _stroke(c, _curve([(-7.5, y), (7.5, y + 5.0)]), C_LEATHER_LINE, 1.1, 0.7)
    pm = skia.Path()
    pm.addCircle(0.0, -G - 9.0, 11.5)
    _metal(c, pm, (-12.0, 0.0), (12.0, 0.0), base=C_GOLD, shade=C_GOLD_SH, hi=C_GOLD_HI, dark=col("#5A4418"))


def _draw_shield_local(c, r=120.0, back_side=False, dent=True):
    """Round iron-rimmed shield facing the camera, centre at the origin."""
    disc = skia.Path()
    disc.addCircle(0.0, 0.0, r)
    c.drawPath(disc, paint(C_IRON_DK, 0.9, stroke=3.0))
    _cel(c, disc, C_WOOD, C_WOOD_DK, k=r * 0.08)
    c.save()
    c.clipPath(disc, doAntiAlias=True)
    for x in range(-int(r), int(r) + 1, 30):
        _stroke(c, _curve([(x + 2.0, -r), (x - 2.0, r)]), C_WOOD_DK, 2.2, 0.8)
        _stroke(c, _curve([(x + 4.0, -r), (x + 0.5, r)]), col("#7A5434"), 1.0, 0.35)
    if back_side:
        band = _poly([(-r, -16.0), (r, -16.0), (r, 16.0), (-r, 16.0)])
        _cel(c, band, C_LEATHER, C_LEATHER_SH, k=3.0, line=C_LEATHER_LINE, line_w=1.2)
    c.restore()
    rim = skia.Path()
    rim.addCircle(0.0, 0.0, r - 6.0)
    c.drawPath(rim, paint(C_STEEL_LINE, 0.9, stroke=15.0))
    c.drawPath(rim, paint(C_IRON, stroke=11.0))
    lx, ly = _lv(c, 1.0)
    arc = skia.Path()
    ang0 = math.degrees(math.atan2(ly, lx))
    arc.addArc(skia.Rect(-r + 6, -r + 6, r - 6, r - 6), ang0 - 50.0, 100.0)
    c.drawPath(arc, paint(C_STEEL_HI, 0.55, stroke=3.0))
    for i in range(14):
        a = 2 * math.pi * i / 14.0
        _rivet(c, math.cos(a) * (r - 6.0), math.sin(a) * (r - 6.0), 2.8, C_IRON)
    if not back_side:
        boss = skia.Path()
        boss.addCircle(0.0, 0.0, 27.0)
        _metal(c, boss, (-27.0, -27.0), (27.0, 27.0))
        _soft_oval(c, lx * 9.0, ly * 9.0, 8.0, 8.0, C_STEEL_HI, 0.6)
        if dent:
            for (x, y, l_) in ((-50.0, 30.0, 16.0), (40.0, -60.0, 12.0), (64.0, 40.0, 10.0)):
                _stroke(c, _curve([(x, y), (x + l_, y + l_ * 0.3)]), col("#2A1A10"), 1.6, 0.7)


# =========================================================================== drawing: body parts
def _cloth_floor(R, pts):
    """Keep cloth above the floor (L coords y <= -3) unless Anger is airborne / hanging."""
    if R.state in ("hang", "fall", "sword_drag"):
        return pts
    return [(x, min(y, -3.0)) for x, y in pts]


def _draw_cape(c, R, t):
    P = R.P
    lie = max(R.lying, R.sitting)
    if lie > 0.6:
        return
    tt = R.t
    wind = (P["wind_x"], P["wind_y"])
    flut = P["flut"]
    length = 440.0 * (1.0 - 0.8 * lie)
    zb = _tprof(24.0)[2] + 8.0
    tl = _mp(R.MC, (-84.0 * R.cb - zb * R.sb, NECK_Y + 30.0))
    tr = _mp(R.MC, (84.0 * R.cb - zb * R.sb, NECK_Y + 30.0))
    top = (0.5 * (tl[0] + tr[0]), 0.5 * (tl[1] + tr[1]))
    axv = _norm(tr[0] - tl[0], tr[1] - tl[1])
    hw0 = 0.5 * math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    d = _norm(wind[0] / 520.0, 1.0 + wind[1] / 520.0)
    pts_l, pts_r = [], []
    n = 6
    for i in range(n + 1):
        u = i / n
        wmax = lerp(78.0, 128.0, clamp(flut + abs(wind[0]) / 300.0 + abs(wind[1]) / 600.0))
        w = lerp(hw0, wmax * max(R.cb, 0.32), u ** 0.8) + 10.0 * math.sin(math.pi * u) * (0.4 + 0.6 * R.sb)
        wave = (flut * 14.0 + abs(wind[1]) * 0.03) * u * math.sin(tt * 7.0 + u * 5.0)
        cx = top[0] + d[0] * length * u + wave * 0.5 - d[1] * wave * 0.4
        cy = top[1] + d[1] * length * u
        nx, ny = (axv if u == 0 else _norm(-d[1], d[0]))
        if u > 0:
            nx, ny = _norm(lerp(axv[0], -d[1], u), lerp(axv[1], d[0], u))
        amp = (3.0 + 14.0 * clamp(math.hypot(*wind) / 600.0) + 6.0 * flut) * u
        el = amp * math.sin(tt * 8.1 + u * 6.0)
        er = amp * math.sin(tt * 7.3 + u * 6.0 + 1.7)
        pts_l.append((cx - nx * (w + el), cy - ny * (w + el) + wave * 0.3))
        pts_r.append((cx + nx * (w + er), cy + ny * (w + er) - wave * 0.3))
    pts_l, pts_r = _cloth_floor(R, pts_l), _cloth_floor(R, pts_r)
    a, b = pts_l[-1], pts_r[-1]
    hem = []
    for j in range(1, 8):
        u = j / 8.0
        dd = (18.0 if j % 2 else -6.0) * (0.6 + 0.5 * hash01(j, 5)) + flut * 9.0 * math.sin(tt * 9.0 + j * 1.3)
        hem.append((lerp(a[0], b[0], u) + d[0] * dd, lerp(a[1], b[1], u) + d[1] * dd))
    hem = _cloth_floor(R, hem)
    path = skia.Path()
    _cr(path, pts_l)
    for q in hem:
        path.lineTo(*q)
    _cr(path, pts_r[::-1], move=False)
    path.close()
    _cel(c, path, mix_col("a_cloth", "#2A0E0C", 0.35), col("#2A0C0A"), k=10.0, line=C_CLOTH_LINE, line_w=1.2)
    for k in (0.3, 0.55, 0.78):
        f0 = (lerp(pts_l[1][0], pts_r[1][0], k), lerp(pts_l[1][1], pts_r[1][1], k))
        f1 = (lerp(pts_l[-1][0], pts_r[-1][0], k + 0.04), lerp(pts_l[-1][1], pts_r[-1][1], k))
        _stroke(c, _curve([f0, f1]), col("#240A08"), 2.0, 0.5)


def _draw_shield_back(c, R):
    if R.lying > 0.5:
        return
    c.save()
    c.concat(R.MC)
    zb = _tprof(90.0)[2]
    cx = -(zb + 16.0) * R.sb
    cy = NECK_Y + 96.0
    c.translate(cx, cy)
    c.scale(max(R.cb, 0.16) * 1.0, 1.0)
    r = 120.0
    disc = skia.Path()
    disc.addCircle(0.0, 0.0, r)
    _cel(c, disc, C_WOOD, C_WOOD_DK, k=10.0, line=C_IRON_DK, line_w=1.5)
    rim = skia.Path()
    rim.addCircle(0.0, 0.0, r - 6.0)
    c.drawPath(rim, paint(C_STEEL_LINE, 0.9, stroke=15.0))
    c.drawPath(rim, paint(C_IRON, stroke=11.0))
    tr = -1.0 if R.sb >= 0 else 1.0
    for a in (150.0, 180.0, 210.0) if tr < 0 else (-30.0, 0.0, 30.0):
        _rivet(c, math.cos(a * D2R) * (r - 6.0), math.sin(a * D2R) * (r - 6.0), 2.8, C_IRON)
    c.restore()


def _draw_sword_back(c, R):
    if R.lying > 0.5:
        return
    sr = R.slot["r"]
    c.save()
    c.concat(R.MC)
    zb = _tprof(10.0)[2]
    x = sr * 52.0 * R.cb - (zb + 26.0) * R.sb
    c.translate(x, NECK_Y - 52.0)
    c.rotate(sr * 26.0 * max(R.cb, 0.25))
    _draw_sword_local(c, scabbard=True)
    c.restore()


_BOOT_LAMES = _loop([(21.0, -3.0), (46.0, 2.0), (62.0, 8.0), (76.0, 15.0), (78.0, 26.0), (20.0, 26.0)], 0.3)


def _draw_boot(c, R, L):
    c.save()
    c.translate(*L.ankle)
    fv = _dirv(L.fang)
    c.rotate(math.degrees(math.atan2(fv[1], fv[0])))
    fl = max(0.55, L.fl)
    c.scale(fl * 1.18, 1.18)
    boot = _loop([(-22.0, -30.0), (14.0, -30.0), (17.0, -8.0), (44.0, 1.0), (68.0, 12.0), (76.0, 22.0), (72.0, 30.0),
                  (20.0, 31.0), (-20.0, 31.0), (-26.0, 22.0), (-26.0, 0.0)], 0.4)
    _cel(c, boot, C_LEATHER, C_LEATHER_SH, k=5.0, line=C_LEATHER_LINE, line_w=1.4)
    sole = _poly([(-21.0, 27.0), (72.0, 26.5), (71.0, 31.5), (-20.0, 32.0)])
    _fill(c, sole, col("#1E140E"))
    lames = _BOOT_LAMES
    _metal(c, lames, (40.0, -4.0), (40.0, 27.0), lw=1.2)
    for (x0, x1, y0) in ((40.0, 62.0, 4.0), (56.0, 76.0, 11.0)):
        _stroke(c, _curve([(x0, y0), (x0 - 1.0, 25.0)]), C_STEEL_LINE, 1.3, 0.8)
    c.restore()


def _draw_leg(c, R, L):
    hip, knee, ank = L.hip, L.knee, L.ankle
    th = _capsule(hip, knee, 48.0, 34.0, bulge=5.0, at=0.35)
    _cel(c, th, C_PANTS, C_PANTS_SH, k=9.0, line=C_LEATHER_LINE, line_w=1.4)
    _draw_boot(c, R, L)
    kv = _norm(ank[0] - knee[0], ank[1] - knee[1])
    g0 = (knee[0] + kv[0] * 8.0, knee[1] + kv[1] * 8.0)
    g1 = (ank[0] - kv[0] * 4.0, ank[1] - kv[1] * 4.0)
    gp = _capsule(g0, g1, 30.0, 22.0, bulge=4.0, at=0.3)
    nx, ny = -kv[1], kv[0]
    _metal(c, gp, (g0[0] - nx * 30, g0[1] - ny * 30), (g0[0] + nx * 30, g0[1] + ny * 30))
    rid = [(lerp(g0[0], g1[0], u) + nx * 6.0, lerp(g0[1], g1[1], u) + ny * 6.0) for u in (0.08, 0.5, 0.92)]
    _stroke(c, _curve(rid), C_STEEL_HI, 1.3, 0.55)
    # greave straps
    for u in (0.22, 0.8):
        r_ = lerp(29.0, 22.0, u)
        p0 = (lerp(g0[0], g1[0], u) - nx * r_, lerp(g0[1], g1[1], u) - ny * r_)
        p1 = (lerp(g0[0], g1[0], u) + nx * r_, lerp(g0[1], g1[1], u) + ny * r_)
        _stroke(c, _curve([p0, p1]), C_LEATHER_LINE, 5.0, 0.95, cap="butt")
        _stroke(c, _curve([p0, p1]), C_LEATHER, 3.4, 1.0, cap="butt")
    # knee cop (poleyn) with a side wing
    tv = _norm(knee[0] - hip[0], knee[1] - hip[1])
    kc = (knee[0] + (tv[0] + kv[0]) * 2.0, knee[1] + (tv[1] + kv[1]) * 2.0)
    pol = skia.Path()
    pol.addOval(skia.Rect(kc[0] - 27.0, kc[1] - 24.0, kc[0] + 27.0, kc[1] + 24.0))
    _metal(c, pol, (kc[0] - 27, kc[1] - 24), (kc[0] + 27, kc[1] + 24))
    _rivet(c, kc[0], kc[1], 2.6)
    lx, ly = _lv(c, 1.0)
    _soft_oval(c, kc[0] + lx * 8.0, kc[1] + ly * 8.0, 6.0, 5.0, C_STEEL_HI, 0.55)


_PTAB = [(-482.0, 84.0, 56.0, 48.0), (-452.0, 88.0, 57.0, 52.0), (-424.0, 92.0, 58.0, 58.0), (-400.0, 90.0, 54.0, 60.0),
         (-382.0, 78.0, 48.0, 56.0), (-366.0, 58.0, 38.0, 46.0)]


def _psil(R, y, side):
    a, zf, zb = _tab(_PTAB, y)
    z = zf if side * R.sb >= 0 else zb
    return side * math.sqrt(a * a * R.cb * R.cb + z * z * R.sb * R.sb)


def _pband(R, yfun, dr=0.0, tab=None, step=12.0):
    """Visible points of a curve running round the pelvis / torso at height yfun(phi), sorted right -> left."""
    tab = _PTAB if tab is None else tab
    pts = []
    phi = -180.0
    while phi <= 180.0:
        y = yfun(phi)
        a, zf, zb = _tab(tab, y) if tab is not _TTAB else _tprof(y - NECK_Y)
        ph = phi * D2R
        sp, cp = math.sin(ph), math.cos(ph)
        zz = zf if cp >= 0 else zb
        x0, z = (a + dr) * sp, (zz + dr) * cp
        vis = -sp / (a + dr) * R.sb + cp / (zz + dr) * R.cb
        if vis > -0.004:
            pts.append((x0 * R.cb + z * R.sb, y, phi))
        phi += step
    pts.sort(key=lambda q: -q[0])
    return pts


def _draw_pelvis(c, R):
    c.save()
    c.concat(R.MB)
    c.translate(R.px, R.py + HIP_H)
    ys = [-470.0, -452.0, -436.0, -420.0, -404.0, -390.0, -378.0, -368.0]
    rgt = [(_psil(R, y, 1), y) for y in ys]
    lft = [(_psil(R, y, -1), y) for y in ys]
    path = _closed2(rgt, lft[::-1])
    _cel(c, path, C_PANTS, C_PANTS_SH, k=10.0, line=C_LEATHER_LINE, line_w=1.4)
    c.restore()


def _draw_belt(c, R):
    c.save()
    c.concat(R.MB)
    c.translate(R.px, R.py + HIP_H)
    top = _pband(R, lambda ph: -482.0, 3.0)
    bot = _pband(R, lambda ph: -458.0 + 2.0 * math.cos(ph * D2R), 3.0)
    if len(top) >= 2 and len(bot) >= 2:
        path = _closed2([(x, y) for x, y, _ in top], [(x, y) for x, y, _ in bot][::-1])
        _cel(c, path, C_LEATHER, C_LEATHER_SH, k=4.0, line=C_LEATHER_LINE, line_w=1.3)
        for x, y, ph in top:
            if abs(ph) < 170 and int(ph) % 36 == 0 and abs(ph) > 20:
                _rivet(c, x, y + 12.0, 2.3)
    # buckle
    a, zf, _ = _tab(_PTAB, -470.0)
    bx = (zf + 5.0) * R.sb
    bw = 17.0 * max(R.cb, 0.25)
    if R.cb > 0.12 or R.sb > 0:
        buck = _loop([(bx - bw, -484.0), (bx + bw, -484.0), (bx + bw * 1.05, -456.0), (bx - bw * 1.05, -456.0)], 0.3)
        _metal(c, buck, (bx - bw, -484.0), (bx + bw, -456.0), base=C_GOLD, shade=C_GOLD_SH, hi=C_GOLD_HI,
               dark=col("#5A4418"), lw=1.3)
        inner = _poly([(bx - bw * 0.55, -478.0), (bx + bw * 0.55, -478.0), (bx + bw * 0.55, -462.0), (bx - bw * 0.55, -462.0)])
        _fill(c, inner, C_LEATHER_SH)
        _stroke(c, _curve([(bx, -478.0), (bx, -462.0)]), C_GOLD_HI, 1.6, 0.9)
    # pouch on Anger's right hip
    sr = R.slot["r"]
    px_, py_, vis = _taz(R, sr * 64.0, 200.0, 4.0)
    if vis > -5.0:
        pw = 20.0 * max(0.45, min(1.0, 0.5 + vis / 60.0))
        pch = _loop([(px_ - pw, -460.0), (px_ + pw, -460.0), (px_ + pw * 1.05, -420.0), (px_, -414.0), (px_ - pw * 1.05, -420.0)], 0.4)
        _cel(c, pch, C_LEATHER, C_LEATHER_SH, k=4.0, line=C_LEATHER_LINE, line_w=1.2)
        _stroke(c, _curve([(px_ - pw, -448.0), (px_, -442.0), (px_ + pw, -448.0)]), C_LEATHER_LINE, 1.4, 0.8)
        _rivet(c, px_, -444.0, 2.4)
    c.restore()


def _tabard_geom(R, t, front=True):
    """Front / back tabard panel centre line in L coords: hangs from the belt, drapes along the thighs when gravity
    presses it onto them (standing, sitting, lying), swings / flies with the wind, never below the floor."""
    P = R.P
    tt = R.t
    flut = P["flut"]
    a, zf, zb = _tab(_PTAB, -458.0)
    att = _mp(R.MB, (R.px + ((zf + 6.0) if front else -(zb + 4.0)) * R.sb, R.py + HIP_H - 458.0))
    fwd = _norm(*(lambda q0, q1: (q1[0] - q0[0], q1[1] - q0[1]))(_mp(R.MB, (0.0, 0.0)), _mp(R.MB, (1.0, 0.0))))
    wind = (P["wind_x"] / 700.0, P["wind_y"] / 700.0)
    kn = [L.knee for L in R.legs.values()]
    an = [L.ankle for L in R.legs.values()]
    hp = [L.hip for L in R.legs.values()]
    if front:
        thd = _norm(0.5 * (kn[0][0] + kn[1][0]) - 0.5 * (hp[0][0] + hp[1][0]), 0.5 * (kn[0][1] + kn[1][1]) - 0.5 * (hp[0][1] + hp[1][1]))
        # forward-most thigh pushes the panel
        k_fwd = max((kn[0][0] - hp[0][0]) * fwd[0] + (kn[0][1] - hp[0][1]) * fwd[1],
                    (kn[1][0] - hp[1][0]) * fwd[0] + (kn[1][1] - hp[1][1]) * fwd[1]) / THIGH
        thd = _norm(thd[0] + fwd[0] * max(0.0, k_fwd) * 0.5, thd[1] + fwd[1] * max(0.0, k_fwd) * 0.5)
        sdot = fwd[1]                      # gravity (0, 1) . front direction: > 0 -> the panel falls away
        d1 = _norm(lerp(thd[0], 0.0, clamp(sdot)) + wind[0], lerp(thd[1], 1.0, clamp(sdot)) + wind[1])
    else:
        d1 = _norm(wind[0] * 1.3, 1.0 + wind[1] * 1.3)
    l1 = 150.0
    m = (att[0] + d1[0] * l1, att[1] + d1[1] * l1)
    sw = flut * 0.25 * math.sin(tt * 6.0)
    if front and R.lying > 0.5:
        shd = _norm(0.5 * (an[0][0] + an[1][0]) - 0.5 * (kn[0][0] + kn[1][0]), 0.5 * (an[0][1] + an[1][1]) - 0.5 * (kn[0][1] + kn[1][1]))
        d2 = _norm(lerp(wind[0] + sw, shd[0], R.lying), lerp(1.0 + wind[1], shd[1], R.lying))
    else:
        d2 = _norm(wind[0] * 1.2 + sw, 1.0 + wind[1] * 1.2)
    l2 = 128.0
    e = (m[0] + d2[0] * l2, m[1] + d2[1] * l2)
    fw = clamp(flut - 0.3) * (6.0 + 10.0 * clamp(math.hypot(P["wind_x"], P["wind_y"]) / 600.0))
    if fw > 0:
        m = (m[0] - d1[1] * fw * math.sin(tt * 8.3), m[1] + d1[0] * fw * math.sin(tt * 8.3))
        e = (e[0] - d2[1] * fw * 1.6 * math.sin(tt * 8.3 - 1.2), e[1] + d2[0] * fw * 1.6 * math.sin(tt * 8.3 - 1.2))
    return att, m, e, d1, d2


def _draw_tabard(c, R, t, front=True):
    if not front and R.lying > 0.5:
        return
    p0, m, e, d1, d2 = _tabard_geom(R, t, front)
    tt = R.t
    flut = R.P["flut"]
    wf = max(R.cb, 0.34)
    ws = [36.0 * wf, 34.0 * wf, 31.0 * wf]
    cen = [p0, m, e]
    dirs = [d1, _norm(d1[0] + d2[0], d1[1] + d2[1]), d2]
    L, Rr = [], []
    for (x, y), (dx, dy), w in zip(cen, dirs, ws):
        nx, ny = -dy, dx
        L.append((x + nx * w, y + ny * w))
        Rr.append((x - nx * w, y - ny * w))
    hem = []
    a, b = L[-1], Rr[-1]
    for j in range(1, 7):
        u = j / 7.0
        dd = (16.0 if j % 2 else 2.0) * (0.5 + 0.6 * hash01(j + (0 if front else 9), 3)) + flut * 5.0 * math.sin(tt * 8.0 + j)
        hem.append((lerp(a[0], b[0], u) + d2[0] * dd, lerp(a[1], b[1], u) + d2[1] * dd))
    L, Rr, hem = _cloth_floor(R, L), _cloth_floor(R, Rr), _cloth_floor(R, hem)
    path = skia.Path()
    _cr(path, L)
    for q in hem:
        path.lineTo(*q)
    _cr(path, Rr[::-1], move=False)
    path.close()
    if front:
        _cel(c, path, C_CLOTH, C_CLOTH_SH, k=7.0, line=C_CLOTH_LINE, line_w=1.3)
        _stroke(c, _curve([(L[0][0] + d1[0] * 12, L[0][1] + d1[1] * 12), (Rr[0][0] + d1[0] * 12, Rr[0][1] + d1[1] * 12)]),
                C_GOLD, 2.4, 0.75)
        for k in (0.35, 0.68):
            f0 = (lerp(L[0][0], Rr[0][0], k) + d1[0] * 20, lerp(L[0][1], Rr[0][1], k) + d1[1] * 20)
            f1 = (lerp(L[-1][0], Rr[-1][0], k + 0.05), lerp(L[-1][1], Rr[-1][1], k))
            _stroke(c, _curve([f0, (lerp(f0[0], f1[0], 0.5) + 2.0, lerp(f0[1], f1[1], 0.5)), f1]), C_CLOTH_LINE, 1.8, 0.45)
    else:
        _cel(c, path, mix_col("a_cloth", "#1A0806", 0.3), C_CLOTH_LINE, k=5.0, line=C_CLOTH_LINE, line_w=1.2)


def _draw_torso(c, R, emit_far_pauldron):
    c.save()
    c.concat(R.MC)
    lead = 1.0 if R.sb >= 0 else -1.0
    # faulds (one lame under the breastplate)
    ysf = [160.0, 172.0, 184.0]
    rgt = [(_tsil(R, y, 1, 2.0), NECK_Y + y) for y in ysf]
    lft = [(_tsil(R, y, -1, 2.0), NECK_Y + y) for y in ysf]
    bot = _pband(R, lambda ph: NECK_Y + 196.0 + 5.0 * math.cos(ph * D2R) ** 2, 3.0, tab=_TTAB)
    if bot:
        fp = skia.Path()
        _cr(fp, rgt)
        _cr(fp, [(x, y) for x, y, _ in bot], move=False)
        _cr(fp, lft[::-1], move=False)
        fp.close()
        _metal(c, fp, (lft[1][0], 0.0), (rgt[1][0], 0.0), lw=1.3)
        for x, y, ph in bot:
            if abs(ph) < 100 and int(abs(ph)) % 36 == 0:
                _rivet(c, x, y - 9.0, 2.2)
    if emit_far_pauldron is not None:
        emit_far_pauldron(c)
    # breastplate
    ys = [0.0, 5.0, 12.0, 22.0, 32.0, 44.0, 58.0, 74.0, 90.0, 106.0, 122.0, 138.0, 152.0, 164.0]
    rgt = [(_tsil(R, y, 1), NECK_Y + y) for y in ys]
    lft = [(_tsil(R, y, -1), NECK_Y + y) for y in ys]
    bot = _pband(R, lambda ph: NECK_Y + 170.0 + 12.0 * max(0.0, math.cos(ph * D2R)) ** 3, 0.5, tab=_TTAB)
    path = skia.Path()
    _cr(path, rgt)
    _cr(path, [(x, y) for x, y, _ in bot], move=False)
    _cr(path, lft[::-1], move=False)
    path.close()
    _metal(c, path, (lft[8][0], 0.0), (rgt[8][0], 0.0), lw=1.6)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    # side / back plate strip on the trailing side + leather side straps
    tr = -lead
    seam = [_taz(R, tr * 86.0, y)[:2] for y in (14.0, 50.0, 90.0, 130.0, 166.0)]
    sil = [(_tsil(R, y, int(tr)), NECK_Y + y) for y in (166.0, 130.0, 90.0, 50.0, 14.0)]
    side = _closed2(seam, sil)
    _fill(c, side, C_STEEL_DK, 0.55)
    _stroke(c, _curve(seam), C_STEEL_LINE, 1.4, 0.7)
    for y in (64.0, 128.0):
        a0 = _taz(R, tr * 70.0, y)
        a1 = _taz(R, tr * 112.0, y + 4.0)
        if a0[2] > -10:
            _stroke(c, _curve([a0[:2], a1[:2]]), C_LEATHER_LINE, 9.0, 0.9, cap="butt")
            _stroke(c, _curve([a0[:2], a1[:2]]), C_LEATHER, 6.5, 1.0, cap="butt")
            mx, my = 0.5 * (a0[0] + a1[0]), 0.5 * (a0[1] + a1[1])
            c.drawRect(skia.Rect(mx - 3.5, my - 5.0, mx + 3.5, my + 5.0), paint(C_GOLD, 1.0, stroke=1.6))
    # medial ridge
    ridge = [_tp(R, 0.0, y, 3.0)[:2] for y in (10.0, 40.0, 80.0, 120.0, 160.0, 180.0)]
    lx, ly = _lv(c, 1.0)
    sd = 1.0 if lx * R.cb >= 0 else -1.0
    _stroke(c, _curve([(x - sd * 1.6, y) for x, y in ridge]), C_STEEL_DK, 2.0, 0.65)
    _stroke(c, _curve([(x + sd * 1.4, y) for x, y in ridge]), C_STEEL_HI, 1.5, 0.75)
    # pectoral plate contours
    for s_ in (-1.0, 1.0):
        pts = [_tp(R, s_ * x0, y, 1.0) for x0, y in ((5.0, 96.0), (32.0, 110.0), (62.0, 104.0), (86.0, 84.0))]
        vis = [q for q in pts if q[2] > -4]
        if len(vis) >= 2:
            _stroke(c, _curve([q[:2] for q in vis]), C_STEEL_DK, 1.7, 0.6)
            _stroke(c, _curve([(q[0], q[1] + 3.0) for q in vis]), C_STEEL_HI, 1.1, 0.4)
    # neckline roll + rivets
    roll = _pband(R, lambda ph: NECK_Y + 9.0 + 3.0 * math.cos(ph * D2R), 1.0, tab=_TTAB)
    rp = [(x, y) for x, y, ph in roll if abs(ph) < 95]
    if len(rp) >= 2:
        _stroke(c, _curve(rp), C_STEEL_HI, 2.0, 0.6)
    for ph in (-56.0, -28.0, 28.0, 56.0):
        x, y, vis = _taz(R, ph, 16.0, 0.0)
        if vis > 2:
            _rivet(c, x, y, 2.4)
    # weathering: dents and scratches
    for (x0, y0, r_) in ((-30.0, 60.0, 9.0), (40.0, 134.0, 7.0)):
        x, y, dep = _tp(R, x0, y0, 0.0)
        if dep > 0:
            _soft_oval(c, x, y, r_, r_ * 0.7, C_STEEL_DK, 0.3)
    for (x0, y0, x1, y1) in ((-56.0, 120.0, -38.0, 128.0), (20.0, 40.0, 38.0, 46.0), (52.0, 140.0, 64.0, 150.0)):
        q0, q1 = _tp(R, x0, y0, 0.5), _tp(R, x1, y1, 0.5)
        if q0[2] > 0:
            _stroke(c, _curve([q0[:2], q1[:2]]), C_STEEL_HI, 0.9, 0.55)
    if R.F.bruised > 0.01:
        for (x0, y0, r_) in ((-20.0, 110.0, 30.0), (36.0, 60.0, 24.0)):
            x, y, dep = _tp(R, x0, y0, 0.0)
            _soft_oval(c, x, y, r_, r_ * 0.6, C_DUST, 0.4 * R.F.bruised)
    c.restore()
    _draw_emblem(c, R)
    c.restore()


_EMB = [([(0.0, 122.0), (-3.0, 104.0), (2.0, 84.0), (-1.0, 64.0), (5.0, 46.0)], [9.0, 11.0, 9.0, 5.0, 0.6]),
        ([(-9.0, 120.0), (-15.0, 106.0), (-18.0, 90.0), (-26.0, 74.0)], [7.5, 8.5, 5.5, 0.6]),
        ([(9.0, 120.0), (16.0, 106.0), (21.0, 92.0), (29.0, 80.0)], [7.5, 8.5, 5.5, 0.6])]


def _draw_emblem(c, R):
    """Original emblem: a three-tongued flame that doubles as a claw slash, gold inlay on the breastplate."""
    paths = []
    for pts, ws in _EMB:
        pp = [_tp(R, x0, y, 1.5) for x0, y in pts]
        if min(q[2] for q in pp) < 0:
            continue
        paths.append(_ribbon([q[:2] for q in pp], [w * max(0.4, R.cb + 0.25 * R.sb) for w in ws]))
    arc = [_tp(R, x0, y, 1.5) for x0, y in ((-22.0, 124.0), (-10.0, 131.0), (0.0, 133.0), (10.0, 131.0), (22.0, 124.0))]
    arc = [q for q in arc if q[2] > 0]
    if len(arc) >= 2:
        paths.append(_ribbon([q[:2] for q in arc], [0.8] + [4.6] * (len(arc) - 2) + [0.8]))
    lx, ly = _lv(c, 1.0)
    for pth in paths:
        c.save()
        c.translate(-lx * 1.6, -ly * 1.6)
        _fill(c, pth, C_STEEL_LINE, 0.75)
        c.restore()
        _fill(c, pth, C_GOLD)
        c.save()
        c.clipPath(pth, doAntiAlias=True)
        c.translate(-lx * 1.8, -ly * 1.8)
        _fill(c, pth, C_GOLD_SH, 0.8)
        c.translate(lx * 2.6, ly * 2.6)
        _fill(c, pth, C_GOLD)
        c.restore()
        _stroke(c, pth, C_GOLD_HI, 0.7, 0.5)


def _draw_neck_skin(c, R):
    c.save()
    c.concat(R.MC)
    pv = R.pivot
    nk = _capsule((pv[0] - 4.0 * R.sb, pv[1] - 10.0), (-6.0 * R.sb, NECK_Y + 10.0), 40.0, 46.0)
    _cel(c, nk, C_SKIN_SH, mix_col("a_skin_shade", "#5A3020", 0.4), k=6.0, line=C_SKIN_LINE, line_w=1.4)
    c.restore()


def _draw_neck(c, R):
    c.save()
    c.concat(R.MC)
    # gorget: steel collar
    top = _pband(R, lambda ph: NECK_Y - 20.0 + 5.0 * math.cos(ph * D2R), 0.0, tab=_GTAB)
    bot = _pband(R, lambda ph: NECK_Y + 12.0 + 4.0 * math.cos(ph * D2R), 0.0, tab=_GTAB)
    if len(top) >= 2 and len(bot) >= 2:
        path = _closed2([(x, y) for x, y, _ in top], [(x, y) for x, y, _ in bot][::-1])
        _metal(c, path, (bot[-1][0], 0.0), (bot[0][0], 0.0), lw=1.4)
        mid = _pband(R, lambda ph: NECK_Y - 4.0 + 4.5 * math.cos(ph * D2R), 1.0, tab=_GTAB)
        _stroke(c, _curve([(x, y) for x, y, _ in mid]), C_STEEL_DK, 1.6, 0.7)
        _stroke(c, _curve([(x, y + 2.5) for x, y, _ in mid]), C_STEEL_HI, 1.1, 0.45)
        for x, y, ph in bot:
            if abs(ph) < 80 and int(abs(ph)) % 48 == 0:
                _rivet(c, x, y - 6.0, 2.2)
    c.restore()


_GTAB = [(NECK_Y - 40.0, 56.0, 50.0, 46.0), (NECK_Y + 30.0, 60.0, 52.0, 48.0)]


# pauldron (outward u, down v) relative to the shoulder joint
_PAUL_DOME = [(-36.0, -22.0), (-24.0, -40.0), (0.0, -51.0), (26.0, -49.0), (48.0, -35.0), (60.0, -10.0), (62.0, 16.0),
              (54.0, 36.0), (30.0, 42.0), (4.0, 36.0), (-20.0, 22.0), (-34.0, 2.0)]
_PAUL_L1 = [(6.0, 28.0), (32.0, 36.0), (56.0, 30.0), (66.0, 42.0), (60.0, 60.0), (34.0, 64.0), (8.0, 54.0)]
_PAUL_L2 = [(12.0, 52.0), (34.0, 60.0), (58.0, 56.0), (64.0, 66.0), (56.0, 80.0), (34.0, 82.0), (14.0, 74.0)]


def _draw_pauldron(c, R, A):
    c.save()
    c.concat(R.MC)
    S = A.S
    c.translate(S[0], S[1] - 4.0)
    ua = _ang_of(A.E[0] - A.S[0], A.E[1] - A.S[1])
    c.rotate(clamp(-0.3 * ua, -40.0, 40.0))
    c.scale(1.12, 1.12)
    near = A.near
    su = lerp(1.0, 0.82, abs(R.sb)) if near else lerp(1.0, 0.6, abs(R.sb))
    ox = A.slot
    c.scale(ox * su, 1.0)
    for shape in (_PAUL_L2, _PAUL_L1):
        pth = _loop(shape, 0.45)
        _metal(c, pth, (0.0, 0.0), (66.0, 0.0), lw=1.3)
    dome = _loop(_PAUL_DOME, 0.5)
    _metal(c, dome, (-36.0, -20.0), (62.0, 20.0), lw=1.6, gloss=1.3)
    lx, ly = _lv(c, 1.0)
    _soft_oval(c, 8.0 + lx * 14, -30.0 + ly * 10, 14.0, 8.0, C_STEEL_HI, 0.5)
    flange = [(-30.0, -28.0), (-14.0, -44.0), (8.0, -50.0), (30.0, -46.0), (50.0, -32.0)]
    _stroke(c, _curve(flange), C_STEEL_HI, 2.2, 0.55)
    _stroke(c, _curve([(x, y + 4.0) for x, y in flange]), C_STEEL_DK, 1.4, 0.5)
    for (x, y) in ((-22.0, 16.0), (2.0, 30.0), (28.0, 36.0), (52.0, 30.0), (22.0, 56.0), (46.0, 54.0), (28.0, 76.0)):
        _rivet(c, x, y, 2.5)
    c.restore()


def _draw_upper_arm(c, R, A):
    path = _capsule(A.Sl, A.El, 37.0, 30.0, bulge=5.0, at=0.4)
    _cel(c, path, C_SLEEVE, C_SLEEVE_SH, k=7.0, line=C_LEATHER_LINE, line_w=1.4)
    v = _norm(A.El[0] - A.Sl[0], A.El[1] - A.Sl[1])
    nx, ny = -v[1], v[0]
    m = (lerp(A.Sl[0], A.El[0], 0.62), lerp(A.Sl[1], A.El[1], 0.62))
    _stroke(c, _curve([(m[0] - nx * 35, m[1] - ny * 35), (m[0] + nx * 35, m[1] + ny * 35)]), C_LEATHER_LINE, 8.0, 0.9, cap="butt")
    _stroke(c, _curve([(m[0] - nx * 35, m[1] - ny * 35), (m[0] + nx * 35, m[1] + ny * 35)]), C_LEATHER, 5.5, 1.0, cap="butt")


def _draw_forearm(c, R, A):
    E, W = A.El, A.Wl
    v = _norm(W[0] - E[0], W[1] - E[1])
    nx, ny = -v[1], v[0]
    p0 = (E[0] + v[0] * 6.0, E[1] + v[1] * 6.0)
    vb = _capsule(p0, W, 31.0, 25.0, bulge=3.5, at=0.3)
    _metal(c, vb, (p0[0] - nx * 31, p0[1] - ny * 31), (p0[0] + nx * 31, p0[1] + ny * 31), lw=1.4)
    for u in (0.3, 0.72):
        q = (lerp(p0[0], W[0], u), lerp(p0[1], W[1], u))
        r_ = lerp(31.0, 25.0, u)
        _stroke(c, _curve([(q[0] - nx * r_, q[1] - ny * r_), (q[0] + nx * r_, q[1] + ny * r_)]), C_LEATHER_LINE, 6.0, 0.9, cap="butt")
        _stroke(c, _curve([(q[0] - nx * r_, q[1] - ny * r_), (q[0] + nx * r_, q[1] + ny * r_)]), C_LEATHER, 4.0, 1.0, cap="butt")
        _rivet(c, q[0], q[1], 2.0)
    cp = skia.Path()
    cp.addOval(skia.Rect(E[0] - 25.0, E[1] - 22.0, E[0] + 25.0, E[1] + 22.0))
    _metal(c, cp, (E[0] - 25, E[1] - 22), (E[0] + 25, E[1] + 22))
    _rivet(c, E[0], E[1], 2.6)


# --------------------------------------------------------------------------- gauntlets
def _finger_set(shape):
    """Finger geometry for a hand shape (hand-local: wrist at origin, +y toward the fingers, +x thumb side).
    Returns (finger block path, thumb path, lines)."""
    fp = skia.Path()
    lines = []
    if shape in ("open", "palm_out", "palm_up"):
        k = 0.72 if shape == "palm_up" else 1.0
        for i, (x, ang) in enumerate(((-12.5, -7.0), (-4.2, -2.0), (4.2, 2.0), (12.5, 6.0))):
            ln = (30.0 if i in (1, 2) else 26.0) * k
            dx, dy = math.sin(ang * D2R), math.cos(ang * D2R)
            a = (x, 28.0)
            b = (x + dx * ln, 28.0 + dy * ln)
            _capsule(a, b, 5.0, 4.3, path=fp)
            lines.append(_curve([(a[0] + dx * ln * 0.45 - 4.0, a[1] + dy * ln * 0.45), (a[0] + dx * ln * 0.45 + 4.0, a[1] + dy * ln * 0.45)]))
        th = _capsule((15.0, 6.0), (30.0, 24.0) if shape != "palm_up" else (31.0, 14.0), 6.4, 5.0)
    elif shape in ("claw",):
        for i, (x, ang) in enumerate(((-12.5, -10.0), (-4.2, -3.0), (4.2, 3.0), (12.5, 10.0))):
            a = (x, 28.0)
            b = (x + math.sin(ang * D2R) * 14.0, 42.0)
            cc = (b[0] + math.sin(ang * D2R) * 4.0 - 2.0, 50.0)
            _capsule(a, b, 5.0, 4.6, path=fp)
            _capsule(b, cc, 4.6, 4.0, path=fp)
        th = _capsule((15.0, 6.0), (25.0, 26.0), 6.4, 5.0)
    elif shape in ("relaxed",):
        p = _loop([(-18.5, 26.0), (18.5, 26.0), (17.5, 40.0), (14.0, 50.0), (6.0, 55.0), (-6.0, 55.0), (-15.0, 50.0), (-18.0, 40.0)], 0.4)
        fp.addPath(p)
        for x in (-9.0, 0.0, 9.0):
            lines.append(_curve([(x, 30.0), (x * 0.9, 44.0), (x * 0.7, 53.0)]))
        lines.append(_curve([(-17.5, 40.0), (0.0, 42.5), (17.5, 40.0)]))
        th = _capsule((15.0, 6.0), (22.0, 30.0), 6.4, 5.2)
    elif shape in ("point",):
        p = _loop([(-18.5, 26.0), (18.5, 26.0), (19.0, 36.0), (14.0, 44.0), (-14.0, 44.0), (-19.0, 36.0)], 0.4)
        fp.addPath(p)
        _capsule((11.0, 30.0), (13.0, 66.0), 5.0, 4.3, path=fp)
        for x in (-9.0, 0.0):
            lines.append(_curve([(x, 30.0), (x, 42.0)]))
        th = _capsule((16.0, 8.0), (6.0, 38.0), 6.4, 5.2)
    elif shape in ("grip",):
        p = _loop([(-18.5, 26.0), (18.5, 26.0), (19.5, 40.0), (17.0, 52.0), (8.0, 58.0), (-8.0, 58.0), (-17.0, 52.0), (-19.5, 40.0)], 0.4)
        fp.addPath(p)
        lines.append(_curve([(-19.0, 40.0), (0.0, 43.0), (19.0, 40.0)]))
        lines.append(_curve([(-16.0, 51.0), (0.0, 54.0), (16.0, 51.0)]))
        for x in (-9.0, 0.0, 9.0):
            lines.append(_curve([(x, 30.0), (x, 57.0)]))
        th = _capsule((16.0, 8.0), (18.0, 34.0), 6.4, 5.4)
    else:   # fist / hold
        p = _loop([(-19.0, 25.0), (19.0, 25.0), (20.5, 34.0), (18.0, 45.0), (-18.0, 45.0), (-20.5, 34.0)], 0.4)
        fp.addPath(p)
        for x in (-9.5, 0.0, 9.5):
            lines.append(_curve([(x, 33.0), (x, 45.0)]))
        lines.append(_curve([(-20.0, 34.0), (0.0, 36.0), (20.0, 34.0)]))
        th = _capsule((16.0, 8.0), (6.0, 40.0), 6.6, 5.4) if shape == "fist" else _capsule((16.0, 8.0), (9.0, 38.0), 6.6, 5.4)
    return fp, th, lines


_HAND_CACHE = {}


def _draw_hand(c, R, A, mirror=1.0):
    c.save()
    c.translate(*A.Wl)
    c.rotate(-A.hal)
    c.scale(HAND_S * (1.0 if mirror >= 0 else -1.0), HAND_S)
    shape = A.shape if A.shape else "relaxed"
    geo = _HAND_CACHE.get(shape)
    if geo is None:
        cuff = None
        back = _loop([(-23.0, -22.0), (23.0, -22.0), (19.5, 5.0), (19.0, 18.0), (18.5, 29.0), (-18.5, 29.0),
                      (-19.0, 18.0), (-19.5, 5.0)], 0.3)
        fp, th, lines = _finger_set(shape)
        geo = (cuff, back, fp, th, lines)
        _HAND_CACHE[shape] = geo
    cuff, back, fp, th, lines = geo
    _metal(c, fp, (-20.0, 0.0), (20.0, 0.0), lw=1.3)
    for ln in lines:
        _stroke(c, ln, C_STEEL_LINE, 1.1, 0.7)
    _metal(c, back, (-23.0, 0.0), (23.0, 0.0), lw=1.4)
    _stroke(c, _curve([(-18.0, 27.0), (0.0, 29.5), (18.0, 27.0)]), C_STEEL_DK, 1.6, 0.8)
    _stroke(c, _curve([(-20.0, 4.0), (0.0, 6.0), (20.0, 4.0)]), C_STEEL_LINE, 1.4, 0.85)
    _rivet(c, -12.0, -8.0, 2.2)
    _rivet(c, 12.0, -8.0, 2.2)
    _metal(c, th, (10.0, 0.0), (28.0, 0.0), lw=1.2)
    c.restore()


def _hand_mirror(R, A):
    if A.near:
        return 1.0
    v = lerp(-1.0, 1.0, R.wf)
    return 1.0 if v >= 0 else -1.0


def _draw_arm_shield(c, R, A):
    m = (lerp(A.El[0], A.Wl[0], 0.55), lerp(A.El[1], A.Wl[1], 0.55))
    c.save()
    c.translate(m[0] + (-18.0 if A.near else 10.0), m[1])
    c.scale(lerp(0.55, 0.85, R.cb), 1.0)
    _draw_shield_local(c, 120.0)
    c.restore()


# =========================================================================== main draw
def _draw_body(c, R, pose, t, emit):
    c.save()
    c.concat(R.MS)
    arms = R.arms
    _draw_cape(c, R, t)
    if R.sword == "back":
        _draw_sword_back(c, R)
    if R.shield == "back":
        _draw_shield_back(c, R)
    _draw_tabard(c, R, t, front=False)
    farA = [A for A in arms.values() if not A.near]
    nearA = [A for A in arms.values() if A.near]
    for A in arms.values():
        if A.layer == "back":
            _draw_arm_full(c, R, A, emit, pauldron=False)
    legs = R.legs.values()
    for L in legs:
        if not L.near:
            _draw_leg(c, R, L)
    _draw_pelvis(c, R)
    for L in legs:
        if L.near:
            _draw_leg(c, R, L)
    turned = abs(R.sb) > 0.2
    behind_paul = [A for A in farA if A.layer == "back"] if turned else []

    def fp(cc):
        cc.save()
        iv = skia.Matrix()
        R.MC.invert(iv)
        cc.concat(iv)
        for A in behind_paul:
            _draw_pauldron(cc, R, A)
        cc.restore()

    _draw_neck_skin(c, R)
    _draw_torso(c, R, fp if behind_paul else None)
    _draw_belt(c, R)
    _draw_tabard(c, R, t, front=True)
    for A in farA:
        if A.layer == "back" and not turned:
            _draw_pauldron(c, R, A)
    for A in farA:
        if A.layer == "front":
            _draw_arm_full(c, R, A, emit, pauldron=True)
    _draw_neck(c, R)
    for A in nearA:
        if A.layer == "under":
            _draw_arm_full(c, R, A, emit, pauldron=True)
    c.save()
    c.concat(R.MH)
    _draw_head(c, R, R.F, R.eye_emit)
    c.restore()
    for A in farA:
        if A.layer == "top":
            _draw_arm_full(c, R, A, emit, pauldron=True)
    for A in nearA:
        if A.layer in ("near", "front", "top"):
            _draw_arm_full(c, R, A, emit, pauldron=True)
    c.restore()


def _draw_arm_full(c, R, A, emit, pauldron=True):
    _draw_upper_arm(c, R, A)
    if pauldron:
        _draw_pauldron(c, R, A)
    _draw_forearm(c, R, A)
    for name, (g, ang, AA) in R.props.items():
        if AA is A:
            _draw_prop(c, R, name, emit)
    _draw_hand(c, R, A, _hand_mirror(R, A))
    if R.shield == "arm" and A.side == "l":
        _draw_arm_shield(c, R, A)


def _draw_prop(c, R, name, emit):
    g, ang, A = R.props[name]
    c.save()
    c.translate(*g)
    c.rotate(-ang)
    if name == "sword":
        if R.state == "sword_drag" or R.sword == "in_wall":
            embed = clamp(R.embed, 0.0, 0.95)
            c.clipRect(skia.Rect(-80.0, -200.0, 80.0, _blade_reach(embed)))
        _draw_sword_local(c)
    else:
        _draw_torch_local(c, R.t, R.torch_flame, 1.0 - R.torch_flame)
    c.restore()
    if name == "torch":
        tg = _torch_geom(R)
        if tg is not None and R.torch_flame > 0.01:
            emit.append(("flame", tg[2], R.torch_flame))


def _bounds_L(R):
    pts = []
    for A in R.arms.values():
        pts += [A.Sl, A.El, A.Wl, A.Pl]
    for L in R.legs.values():
        pts += [L.hip, L.knee, L.ankle]
    for q in ((0.0, -75.0), (60.0, 0.0), (-60.0, 0.0), (0.0, 95.0)):
        pts.append(_mp(R.MH, q))
    for q in ((-175.0, NECK_Y - 70.0), (175.0, NECK_Y - 70.0), (-175.0, NECK_Y + 240.0), (175.0, NECK_Y + 240.0),
              (-190.0, NECK_Y + 480.0), (190.0, NECK_Y + 480.0)):
        pts.append(_mp(R.MC, q))
    for name, (g, ang, A) in R.props.items():
        dv = _dirv(ang)
        ln = SWORD_BLADE + 60.0 if name == "sword" else TORCH_LEN
        pts.append((g[0] + dv[0] * ln, g[1] + dv[1] * ln))
        pts.append((g[0] - dv[0] * 90.0, g[1] - dv[1] * 90.0))
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    pad = 90.0
    return skia.Rect(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _dir_from(v, default):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        a = float(v) * D2R
        return math.cos(a), math.sin(a)
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 1e-9 else default


_SURF_CACHE = {}


def _scratch(w, h, slot):
    """Reusable offscreen raster surface (at least w x h), cleared."""
    key = (slot, (w + 63) // 64 * 64, (h + 63) // 64 * 64)
    sf = _SURF_CACHE.get(key)
    if sf is None:
        if len(_SURF_CACHE) > 9:
            _SURF_CACHE.clear()
        sf = skia.Surface(key[1], key[2])
        _SURF_CACHE[key] = sf
    sf.getCanvas().clear(skia.ColorTRANSPARENT)
    return sf


def _draw_rimlit(c, R, pose, t, rim, emit):
    """Rim light: the character rendered offscreen; behind it a soft glow of its silhouette tinted with rim_color
    (blurred at 1/4 resolution, pushed toward the light, cut at the floor); then the character; then a thin bright
    edge on the side facing the light (the silhouette minus itself shifted away from the light).
    Light direction: extra rim_pos (stage point, e.g. torch_pos()) or rim_dir (screen angle in degrees, 0 = from
    screen-right, -90 = from above, or an (x, y) vector toward the light); default from behind-above."""
    M = c.getTotalMatrix()
    MM = skia.Matrix.Concat(M, R.MS)
    devs = math.sqrt(abs(MM.getScaleX() * MM.getScaleY() - MM.getSkewX() * MM.getSkewY()))   # device px per unit
    dscale = devs / max(pose.scale, 1e-3)                                                      # camera zoom
    dev = MM.mapRect(_bounds_L(R))
    clipb = c.getDeviceClipBounds()
    bx0 = int(max(math.floor(dev.left()), clipb.left()))
    by0 = int(max(math.floor(dev.top()), clipb.top()))
    bx1 = int(min(math.ceil(dev.right()), clipb.right()))
    by1 = int(min(math.ceil(dev.bottom()), clipb.bottom()))
    if bx1 - bx0 < 2 or by1 - by0 < 2:
        return
    w, h = bx1 - bx0, by1 - by0
    ex = pose.extra
    rp = ex.get("rim_pos")
    if rp is not None:
        hc = _mp(R.MS, _mp(R.MH, _hp(R.H, 0.0, 0.0, 0.0)[:2]))
        v = M.mapVector(rp[0] - hc[0], rp[1] - hc[1])
        lx, ly = _dir_from((v.fX, v.fY), (0.0, -1.0))
    else:
        lx, ly = _dir_from(ex.get("rim_dir"), _dir_from((-R.fac * 0.55, -0.83), (0.0, -1.0)))
    rc = col(pose.rim_color)
    tint = skia.ColorFilters.Blend(rc, skia.BlendMode.kSrcIn)
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    sa = _scratch(w, h, "body")
    oc = sa.getCanvas()
    oc.save()
    oc.translate(-bx0, -by0)
    oc.concat(M)
    _draw_body(oc, R, pose, t, emit)
    oc.restore()
    img = sa.makeImageSnapshot(skia.IRect.MakeWH(w, h))
    c.save()
    c.resetMatrix()
    # ---- soft glow behind (blurred in a 1/4-size surface, then drawn scaled up)
    q = 4.0
    pad = 6
    sw_, sh_ = int(w / q) + 2 * pad, int(h / q) + 2 * pad
    sb = _scratch(sw_, sh_, "glow")
    sc = sb.getCanvas()
    gp = skia.Paint()
    gp.setColorFilter(tint)
    sig = clamp(7.0 * devs / q, 0.6, 6.0)
    gp.setImageFilter(skia.ImageFilters.Blur(sig, sig))
    sc.save()
    sc.translate(pad, pad)
    sc.scale(1.0 / q, 1.0 / q)
    sc.drawImage(img, 0.0, 0.0, samp, gp)
    sc.restore()
    simg = sb.makeImageSnapshot(skia.IRect.MakeWH(sw_, sh_))
    floor_cut = R.state not in ("hang", "fall", "sword_drag")
    if floor_cut:
        fy = MM.mapXY(0.0, 0.0).fY
        c.save()
        c.clipRect(skia.Rect(-1e5, -1e5, 1e5, fy - 1.0))
    off = 6.0 * devs
    ap = skia.Paint()
    ap.setAlphaf(clamp(0.75 * rim))
    dst = skia.Rect.MakeXYWH(bx0 - pad * q + lx * off, by0 - pad * q + ly * off, sw_ * q, sh_ * q)
    c.drawImageRect(simg, skia.Rect.MakeWH(sw_, sh_), dst, samp, ap)
    if floor_cut:
        c.restore()
    # ---- the character
    c.drawImage(img, bx0, by0)
    # ---- the edge on the light side
    dpx = clamp(2.4 * dscale ** 0.5, 1.8, 4.0)
    sc2 = _scratch(w, h, "edge")
    ec = sc2.getCanvas()
    ec.drawImage(img, 0, 0)
    dp = skia.Paint()
    dp.setBlendMode(skia.BlendMode.kDstOut)
    ox, oy = int(round(lx * dpx)), int(round(ly * dpx))
    if ox == 0 and oy == 0:
        oy = -2
    near = skia.SamplingOptions()
    ec.drawImage(img, -ox, -oy, near, dp)          # integer offsets: the sub-pixel path is ~10x slower
    eimg = sc2.makeImageSnapshot(skia.IRect.MakeWH(w, h))
    ep = skia.Paint()
    ep.setColorFilter(tint)
    ep.setAlphaf(clamp(1.0 * rim))
    if ly < -0.3 and R.lying < 0.5:
        # light from above: the legs catch less of it (cheap two-band fade instead of a gradient mask)
        hy = int(MM.mapXY(R.px, R.py - 40.0).fY)
        c.save()
        c.clipRect(skia.Rect(-1e5, -1e5, 1e5, hy))
        c.drawImage(eimg, bx0, by0, near, ep)
        c.restore()
        c.save()
        c.clipRect(skia.Rect(-1e5, hy, 1e5, 1e5))
        ep.setAlphaf(clamp(0.45 * rim))
        c.drawImage(eimg, bx0, by0, near, ep)
        c.restore()
        ep.setAlphaf(clamp(1.0 * rim))
    else:
        c.drawImage(eimg, bx0, by0, near, ep)
    if dscale > 1.6:
        ep.setAlphaf(clamp(0.35 * rim))
        c.drawImage(eimg, bx0 - int(round(lx)), by0 - int(round(ly)), near, ep)
    c.restore()
    del img, simg, eimg


def _key_light(R, pose, canvas):
    ex = pose.extra
    kd = ex.get("key_dir")
    if kd is not None:
        return _dir_from(kd, (0.0, -1.0))
    M = skia.Matrix.Concat(canvas.getTotalMatrix(), R.MS)
    if "torch" in R.props and R.torch_flame > 0.05:
        tg = _torch_geom(R)
        chest = _mp(R.MC, (0.0, NECK_Y + 40.0))
        v = M.mapVector(tg[2][0] - chest[0], tg[2][1] - 60.0 - chest[1])
        return _dir_from((v.fX, v.fY), (0.0, -1.0))
    v = M.mapVector(0.5, -0.87)
    return _dir_from((v.fX, v.fY), (0.0, -1.0))


def draw(canvas, pose: Pose, t: float):
    """Draw Anger. The canvas must already carry the camera transform (stage coordinates)."""
    global _CF, _CF_KEY, _LIGHT
    R = _solve(pose, t)
    R.eye_emit = [] if pose.light < 0.95 else None
    emit = []
    lit = pose.light != 1.0 or pose.tint_amt > 0
    _LIGHT = _key_light(R, pose, canvas)
    _CF = light_filter(max(0.0, pose.light), pose.tint, pose.tint_amt) if lit else None
    _CF_KEY = (round(pose.light, 3), tuple(pose.tint), round(pose.tint_amt, 3)) if lit else None
    try:
        rim = clamp(pose.rim)
        if rim > 0.01:
            _draw_rimlit(canvas, R, pose, t, rim, emit)
        else:
            _draw_body(canvas, R, pose, t, emit)
    finally:
        _CF = None
        _CF_KEY = None
    _draw_emissive(canvas, R, pose, emit)


def _draw_emissive(canvas, R, pose, emit):
    c = canvas
    if R.eye_emit:
        a = clamp(0.9 * (1.0 - pose.light) / 0.7)
        c.save()
        c.concat(R.MS)
        c.concat(R.MH)
        for opening, (gx, gy, gr) in R.eye_emit:
            c.save()
            c.clipPath(opening, doAntiAlias=True)
            c.drawCircle(gx, gy, gr, _core_paint("#FFFFFF", 0.8 * a))
            c.restore()
        c.restore()
    for kind, pos, k in emit:
        if kind == "flame":
            c.save()
            c.concat(R.MS)
            c.translate(pos[0], pos[1] + 4.0)
            c.scale(R.fac, 1.0)             # flames are not mirrored: world-up, world wind
            _draw_flame_local(c, R.t, 1.0, k, (R.P["wind_x"] * R.fac, R.P["wind_y"]))
            c.restore()
            c.save()
            c.concat(R.MS)
            glow_c = col("torch_light", 0.33 * k)
            sh = skia.GradientShader.MakeRadial((pos[0], pos[1] - 26.0), 150.0, [glow_c, skia.ColorSetA(glow_c, 0)])
            c.drawCircle(pos[0], pos[1] - 26.0, 150.0, _core_paint(None, shader=sh, blend="add"))
            c.restore()


# =========================================================================== stand-alone props for scenes
def draw_torch(canvas, x, y, angle=0.0, t=0.0, scale=1.0, flame=1.0, light=1.0, glow=True):
    """A loose torch (e.g. tumbling through the air): grip point at (x, y) stage, angle = degrees from straight up
    (+ clockwise) of the burning end; flame 0..1 (0 = out, charred). The flame always rises in world up."""
    global _CF, _CF_KEY, _LIGHT
    _LIGHT = (0.4, -0.9)
    _CF = light_filter(light) if light != 1.0 else None
    _CF_KEY = (round(light, 3), "torch") if light != 1.0 else None
    c = canvas
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.rotate(angle + 180.0)
    _draw_torch_local(c, t, flame, 1.0 - flame)
    c.restore()
    _CF, _CF_KEY = None, None
    if flame > 0.01:
        a = (angle + 180.0) * D2R
        L1 = (TORCH_LEN - TORCH_GRIP - 22.0) * scale
        hx, hy = x - math.sin(a) * L1, y + math.cos(a) * L1
        c.save()
        c.translate(hx, hy + 4.0 * scale)
        _draw_flame_local(c, t, scale, flame)
        c.restore()
        if glow:
            glow_c = col("torch_light", 0.33 * flame)
            sh = skia.GradientShader.MakeRadial((hx, hy - 26.0 * scale), 150.0 * scale, [glow_c, skia.ColorSetA(glow_c, 0)])
            c.drawCircle(hx, hy - 26.0 * scale, 150.0 * scale, _core_paint(None, shader=sh, blend="add"))


def torch_flame_offset(angle=0.0, scale=1.0):
    """Offset (dx, dy) from a loose torch's grip point (draw_torch) to its flame centre."""
    a = (angle + 180.0) * D2R
    L1 = (TORCH_LEN - TORCH_GRIP - 22.0) * scale
    return -math.sin(a) * L1, math.cos(a) * L1 - 30.0 * scale


def draw_flame(canvas, x, y, t=0.0, scale=1.0, intensity=1.0, wind=(0.0, 0.0)):
    """Just the flame, base at (x, y) stage (e.g. an emissive pass after the scene's darkness)."""
    canvas.save()
    canvas.translate(x, y)
    _draw_flame_local(canvas, t, scale, intensity, wind)
    canvas.restore()


def draw_sword(canvas, x, y, angle=180.0, scale=1.0, light=1.0, tint=(0, 0, 0), tint_amt=0.0, embed=0.0):
    """Anger's broadsword alone: grip centre at (x, y) stage, angle = direction of the POINT in degrees from straight
    up (+ clockwise): 90 = pointing right (e.g. stuck in a wall on the right). embed 0..1 hides that fraction of the
    blade (sunk into rock: the part beyond the wall surface is clipped)."""
    global _CF, _CF_KEY, _LIGHT
    _LIGHT = (0.4, -0.9)
    lit = light != 1.0 or tint_amt > 0
    _CF = light_filter(light, tint, tint_amt) if lit else None
    _CF_KEY = (round(light, 3), tuple(tint), round(tint_amt, 3)) if lit else None
    c = canvas
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.rotate(angle + 180.0)
    if embed > 0:
        cut = _blade_reach(embed)
        c.clipRect(skia.Rect(-80.0, -200.0, 80.0, cut))
    _draw_sword_local(c)
    c.restore()
    _CF, _CF_KEY = None, None


def sword_wall_point(x, y, angle=90.0, scale=1.0, embed=0.72):
    """Where draw_sword(x, y, angle, scale, embed=embed)'s blade enters the wall (stage)."""
    d = _blade_reach(embed) * scale
    a = angle * D2R
    return x + math.sin(a) * d, y - math.cos(a) * d


def draw_shield(canvas, x, y, scale=1.0, squash=1.0, angle=0.0, light=1.0, back_side=False):
    """The round iron-rimmed shield, centre (x, y) stage; squash < 1 narrows it (seen at an angle)."""
    global _CF, _CF_KEY, _LIGHT
    _LIGHT = (0.4, -0.9)
    _CF = light_filter(light) if light != 1.0 else None
    _CF_KEY = (round(light, 3), "shield") if light != 1.0 else None
    canvas.save()
    canvas.translate(x, y)
    canvas.rotate(angle)
    canvas.scale(scale * squash, scale)
    _draw_shield_local(canvas, 120.0, back_side=back_side)
    canvas.restore()
    _CF, _CF_KEY = None, None


# =========================================================================== face presets
EXPR = {
    "grim": dict(),
    "listen": dict(look_x=-0.9, brow_furrow=0.2, lid_l=0.9, lid_r=0.9),
    "scan": dict(look_x=0.9, brow_furrow=0.25, squint=0.15),
    "stoic_close": dict(lid_l=0.0, lid_r=0.0, brow_raise=-0.05, brow_furrow=-0.15, head_nod=0.1),
    "startled": dict(eye_wide=1.0, brow_raise=1.0, mouth_open=0.35, mouth_round=0.3, pupil=0.75, head_nod=0.15),
    "pain": dict(squint=0.75, lid_l=0.3, lid_r=0.25, brow_furrow=0.6, brow_worry=0.45, smile=-0.35, mouth_open=0.08),
    "dazed": dict(lid_l=0.7, lid_r=0.62, mouth_open=0.12, brow_worry=0.25),
    "strain": dict(squint=0.5, brow_furrow=0.5, smile=-0.25, mouth_open=0.05),
    "flat": dict(lid_l=0.68, lid_r=0.68, brow_raise=-0.1, smile=-0.1),
    "eye_roll": dict(look_y=-1.0, look_x=0.3, lid_l=1.0, lid_r=1.0, brow_raise=0.4, head_nod=0.2, head_tilt=-3.0),
    "squint": dict(squint=0.6, lid_l=0.8, lid_r=0.8, brow_furrow=0.45),
    "smirk": dict(smirk=0.55, smile=0.06, lid_l=0.85, lid_r=0.85),
    "deadpan": dict(lid_l=0.62, lid_r=0.62, brow_raise=0.05, smile=-0.05, look_x=0.0),
    "exhausted": dict(lid_l=0.42, lid_r=0.4, brow_worry=0.3, smile=-0.15, head_nod=-0.2),
    "side_eye": dict(lid_l=0.55, lid_r=0.55, look_x=0.9, look_y=-0.25, brow_furrow=0.25),
    "confused": dict(brow_raise=0.35, brow_furrow=0.35, squint=0.15, smile=-0.1),
    "contemplate": dict(look_x=0.4, look_y=0.25, lid_l=0.7, lid_r=0.7, brow_worry=0.2),
}
# extra-key parts of the presets (merged into pose.extra by expr())
EXPR_EXTRA = {
    "pain": {"grimace": 0.8},
    "dazed": {"dazed": 1.0},
    "strain": {"strain": 1.0, "grimace": 0.45},
    "raised_brow": {"brow_l": 1.0, "brow_r": -0.3},
    "smirk_suppressed": {"smirk_suppress": 1.0},
    "one_eye": {"one_eye": 1.0},
}
EXPR.setdefault("raised_brow", dict(lid_l=0.85, lid_r=0.8))
EXPR.setdefault("smirk_suppressed", dict(smirk=0.5, lid_l=0.75, lid_r=0.75, look_x=-0.5, head_nod=-0.15))
EXPR.setdefault("one_eye", dict(lid_r=0.8, lid_l=0.8, brow_furrow=0.1))


def expr(pose: Pose, name: str, amount: float = 1.0, t=None) -> Pose:
    """Blend face preset `name` into pose by amount (lids None count as open). Pass t to keep the heavy blink
    running on the preset's lid levels. Extra-key parts (grimace, dazed, brow_l ...) are blended into a copy of
    pose.extra."""
    if amount <= 0.0:
        return pose
    kw = {}
    for k, v in EXPR.get(name, {}).items():
        cur = getattr(pose, k)
        if k in ("lid_l", "lid_r"):
            val = lerp(1.0 if cur is None else cur, v, amount)
            if t is not None:
                val *= blink(t)
            kw[k] = val
            continue
        kw[k] = lerp(cur, v, amount)
    exx = EXPR_EXTRA.get(name)
    if exx:
        e2 = dict(pose.extra)
        for k, v in exx.items():
            e2[k] = lerp(float(e2.get(k, 0.0)), v, amount)
        kw["extra"] = e2
    return pose.copy(**kw)
