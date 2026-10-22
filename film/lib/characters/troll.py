"""troll.py -- THE STONE TROLL, the tavern bouncer (speaker BOUNCER, S4).

A boulder with small legs: huge mossy grey stone shoulders hunched up past his head, a low
heavy-browed head thrust forward, tiny bored eyes, a big stone nose, an underbite with two
small tusks, cracks and lichen; a leather jerkin straining over his chest (laced across the
gap), rough breeches, and the SMILE stamp lost in his enormous fist.

    p = ch.TrollPose(facing=-1, mood="bored", look=(-0.6, 0.2),
                     near=ch.TrollArm("press_stamp", phase=u, screen=dragon_rig.hand_near.palm))
    rig = ch.draw_troll(cr, x, ground_y, 0.8, p, ch.LIGHTS["tavern"], t)
    rig.stamp_face        # where the die meets the hand (the thunk, an ink puff)

Scale 1.0: ground -> the top of his silhouette (the mossy crown, 3/4 view) = TROLL_HEIGHT =
660 px (eyes ~575, chest ~365). Anchor = the ground point between his feet. 3D-lite: body space
X = his left, Y down, Z forward, turned by the yaw (clamped to +-1.45).
"""

import math
from dataclasses import dataclass, field, replace

from .. import core
from ..core import clamp, lerp
from . import _cast_kit as K
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp

TAU = math.tau

__all__ = ["TrollPose", "TrollArm", "TrollRig", "draw_troll", "troll_stamp", "TROLL_HEIGHT", "TROLL_COLORS",
           "TROLL_GESTURES", "troll_mats"]

TROLL_HEIGHT = 660.0
LINE = B.LINE
PELVIS_Y = -150.0
HIP_W = 46.0
THIGH, SHIN, ANKLE_H = 66.0, 60.0, 30.0
UPPER_ARM, FOREARM, FIST = 158.0, 150.0, 128.0
SHOULDER_W = 150.0
ELEV = 0.12
HS = 1.18                  # head scale (head-space units -> body px)
# the rig is authored a little small: this brings the measured top (his crown) to TROLL_HEIGHT
SIZE_K = 660.0 / 616.0

TROLL_COLORS = {
    "stone": "#8E9294",      # cool grey
    "stone_dk": "#6C7174",
    "moss": "#6F8C45",
    "moss_hi": "#9DB660",
    "lichen": "#CBC46B",
    "jerkin": "#7B5232",
    "lace": "#D2BC8C",
    "breeches": "#5C5148",
    "tusk": "#E8DDC2",
    "eye": "#C9A645",
    "mouth": "#3B2828",
    "wood": "#8A6038",       # the stamp's handle
    "die": "#4A3A3E",         # the carved, ink-stained face of the stamp
    "ink": "#FF5FA2",        # SMILE in pink
}

_MATS = {}


def troll_mats():
    if not _MATS:
        C = TROLL_COLORS
        _MATS.update({
            "stone": Mat.of(C["stone"], shadow_k=1.1),
            "stone_dk": Mat.of(C["stone_dk"], shadow_k=1.1),
            "moss": Mat.of(C["moss"], shadow_k=1.05),
            "jerkin": Mat.of(C["jerkin"], sheen=0.35),
            "lace": Mat.of(C["lace"]),
            "breeches": Mat.of(C["breeches"], shadow_k=1.1),
            "tusk": Mat.of(C["tusk"], sheen=0.5, line_k=0.45),
            "wood": Mat.of(C["wood"], sheen=0.3),
            "die": Mat.of(C["die"]),
        })
    return _MATS


@dataclass
class TrollArm:
    """gesture (TROLL_GESTURES), amt/prev blend, hold callback (default for the stamp gestures:
    troll_stamp), target (body space) / screen (caller coords: where the stamp's die lands),
    hand pose override, phase 0..1 (press_stamp: raise -> slam at 0.5 -> hold -> lift)."""
    gesture: str = "rest"
    amt: float = 1.0
    prev: str = "rest"
    hold: object = None
    target: tuple = None
    screen: tuple = None
    depth: float = 120.0
    hand: str = None
    phase: float = 0.0


@dataclass
class TrollPose:
    """facing/turn, lean, head_turn/tilt/nod, look (his tiny eyes slide; -1..1), mood (default
    "bored"), mood2/mood_mix, talk (slow, flat jaw), smile, blink, near/far TrollArm,
    shrug 0..1, elev, shadow, seed."""
    facing: int = -1
    turn: float = 0.0
    lean: float = 0.0
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    mood: object = "bored"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    smile: float = None
    blink: float = None
    near: TrollArm = field(default_factory=TrollArm)
    far: TrollArm = field(default_factory=TrollArm)
    shrug: float = 0.0
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class TrollRig:
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    stamp_face: tuple = None      # press_stamp / hold_up_stamp: the die's face, caller coords
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0


# ----------------------------------------------------------------------------------------
# the stamp
# ----------------------------------------------------------------------------------------

def _stamp_drop(hand_size):
    """How far below the grip the stamp's block hangs, so it clears the fingers of a fist of
    `hand_size` (the hand's wrist-to-fingertip length, frame.scale in a hold callback)."""
    return max(6.0, 0.30 * hand_size)


def _stamp_die_y(hand_size):
    """The die FACE's offset below the grip (upright stamp) for a hand of `hand_size`."""
    return _stamp_drop(hand_size) + 30.0


def troll_stamp(cr, frame, light=None, ink=1.0, die_down=True):
    """The tavern's wooden SMILE stamp as a hold callback (a turned handle through the fist,
    the block and the inked die hanging clear BELOW the fist -- _stamp_drop() -- with SMILE cut
    in mirror-writing, pink ink). Usable in any hand: the neck lengthens with the hand size
    (frame.scale), so the die always shows under the fingers."""
    light = light or B.LIGHTS["neutral"]
    M = troll_mats()
    cr.save()
    if die_down:
        cr.rotate(-frame.angle)           # keep it upright: the die faces the ground
    lw = B.line_w(cr, LINE * 0.8)
    wood = B.palette(light, M["wood"])
    rub = B.palette(light, M["die"])
    y0 = _stamp_drop(getattr(frame, "scale", 0.0) or 0.0)
    # the handle: a turned knob up through the fist, its neck down to the block
    hs, ho = B.smooth_paths(cr, [(-9, -46), (9, -46), (11, -30), (7, -14), (8, y0), (-8, y0), (-7, -14), (-11, -30)], lw, 0.8)
    B.shade(cr, hs, M["wood"], light, lw, outline=ho, size=18, bounce=0)
    # the block and the die
    bs, bo = B.smooth_paths(cr, [(-34, y0), (34, y0), (36, y0 + 20), (-36, y0 + 20)], lw, 0.4)
    B.shade(cr, bs, M["wood"], light, lw, outline=bo, size=18, bounce=0)
    ds, do = B.smooth_paths(cr, [(-33, y0 + 20), (33, y0 + 20), (33, y0 + 30), (-33, y0 + 30)], lw, 0.3)
    do.add(cr)
    core.src(cr, rub.line)
    cr.fill()
    ds.add(cr)
    core.src(cr, rub.lit)
    cr.fill()
    if ink > 0:
        core.src(cr, TROLL_COLORS["ink"], 0.9 * ink)
        cr.rectangle(-32, y0 + 28.5, 64, 2.0)
        cr.fill()
    B.detail_lines(cr, [[(-28, y0 + 7), (28, y0 + 7)]], lw * 0.7, wood.line, 0.5)
    cr.restore()


def _stamp_cb(light):
    def cb(cr, f):
        troll_stamp(cr, f, light)
    return cb


# ----------------------------------------------------------------------------------------
# gestures -> (wrist target in body space, hand pose, extra angle, layer)
# ----------------------------------------------------------------------------------------

def _g_rest(sk, side, c):
    # knuckles hanging by the knees
    return v_add(sk, (side * 24.0, 320.0, 30.0)), "fist", 0.0, "auto"


def _g_arms_crossed(sk, side, c):
    # a bouncer's folded arms, high on the chest: the NEAR forearm lies on top and its fist
    # grips the far biceps (knuckles to us); the FAR forearm passes under it and its fist tucks
    # in behind the near upper arm (hidden) -- not two paws held out like a carried box
    ch = c["chest"]
    if c.get("near_side", -1.0) == side:
        return v_add(ch, (-side * AC_NEAR[0], AC_NEAR[1], AC_NEAR[2])), "fist", side * AC_NEAR[3], "front"
    return v_add(ch, (-side * AC_FAR[0], AC_FAR[1], AC_FAR[2])), "fist", side * AC_FAR[3], "front"


AC_NEAR = (86.0, -30.0, 130.0, 1.4)      # wrist offset from the chest (x toward the far side, y, z) + fist hang
AC_FAR = (60.0, 16.0, 80.0, 0.6)


def _g_hold_up_stamp(sk, side, c):
    # the stamp shown at head height, out front
    f = c["fwd"]
    # held up beside his shoulder like a torch, the die toward whoever is at the door
    return v_add(sk, (side * 115.0 + f[0] * 30.0, 0.0, 45.0 + f[2] * 30.0)), "grip", 0.0, "front"


def _g_press_stamp(sk, side, c):
    # raise high -> slam down (impact at 0.5) -> hold -> lift back
    ph = c["phase"]
    f = c["fwd"]
    hi = v_add(sk, (side * 20.0 + f[0] * 110.0, -70.0, 50.0 + f[2] * 70.0))
    lo = c.get("press_target") or v_add(sk, (side * 10.0 + f[0] * 150.0, 200.0, 60.0 + f[2] * 110.0))
    if ph < 0.35:
        return v_lerp(hi, v_add(hi, (0.0, -20.0, 0.0)), core.inout_sine(ph / 0.35)), "grip", 0.0, "front"
    if ph < 0.5:
        return v_lerp(v_add(hi, (0.0, -20.0, 0.0)), lo, core.in_quad((ph - 0.35) / 0.15)), "grip", 0.0, "front"
    if ph < 0.75:
        return v_add(lo, (0.0, -6.0 * B.wobble(ph, 0.5, 6.0, 9.0), 0.0)), "grip", 0.0, "front"
    return v_lerp(lo, hi, core.inout_sine((ph - 0.75) / 0.25)), "grip", 0.0, "front"


def _g_belt(sk, side, c):
    return v_add(c["waist"], (side * 70.0, 20.0, 70.0)), "fist", 0.0, "auto"


def _g_thumb(sk, side, c):
    # a jerk of the thumb over his shoulder (toward the street)
    return v_add(sk, (side * 60.0, 30.0, -20.0)), "point", 0.0, "front"


TROLL_GESTURES = {"rest": _g_rest, "arms_crossed": _g_arms_crossed, "hold_up_stamp": _g_hold_up_stamp,
                  "press_stamp": _g_press_stamp, "belt": _g_belt, "thumb": _g_thumb}


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_troll(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    pose = pose or TrollPose()
    light = light or B.LIGHTS["neutral"]
    q = K.Q(cr, light, troll_mats(), t, pose)
    yaw = K.yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    scale_px = scale
    scale = scale * SIZE_K            # internal units: lines stay LINE px on screen
    # LOD: his features are big (a 660 px creature), so judge detail by size, not raw scale
    dev = q.lod(scale * 1.6, detail) / 1.6
    q.lw = B.line_for(LINE / SIZE_K, dev, 1.0 / SIZE_K)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    S = _skeleton(pose, t, yaw)
    q.S = S
    rig = TrollRig(scale=scale_px, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)
    if pose.shadow:
        B.contact_shadow(cr, 0.0, 3.0, 150.0, 26.0, alpha=0.36)
    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    arms = {near_side: pose.near, far_side: pose.far}
    A = {s: _solve_arm(q, S, s, arms[s]) for s in (near_side, far_side)}
    frontish = abs(yaw) < 0.38
    zf = A[far_side]["z"]
    far_layer = ("mid" if frontish else "back") if zf == "auto" else (("front" if frontish else "mid") if zf == "front" else zf)
    if far_layer == "back":
        rig.hand_far = _arm(q, A[far_side], far_side)
    _legs(q)
    _torso(q)
    if far_layer == "mid":
        rig.hand_far = _arm(q, A[far_side], far_side)
    if A[near_side]["z"] == "auto" and not frontish:
        rig.hand_near = _arm(q, A[near_side], near_side)
    head = _head(q)
    if far_layer == "front":
        rig.hand_far = _arm(q, A[far_side], far_side)
    if rig.hand_near is None:
        rig.hand_near = _arm(q, A[near_side], near_side)
    stamp = None
    for s_, hf in ((near_side, rig.hand_near), (far_side, rig.hand_far)):
        if A[s_]["stamp"] and hf is not None:
            stamp = (hf.x, hf.y + _stamp_die_y(FIST))         # the upright die hangs below the grip
    ex = K.Exporter(cr)
    cr.restore()
    ex.ready(cr)
    rig.head, rig.mouth = ex(head["center"]), ex(head["mouth"])
    rig.eyes = [ex(e) for e in head["eyes"]]
    rig.top = ex(head["top"])
    rig.chest = ex(proj.xy(S["chest"]))
    rig.feet = [ex(proj.xy(f["ankle"])) for f in S["feet"]]
    if stamp is not None:
        rig.stamp_face = ex(stamp)
    ex.hand(rig.hand_near, scale)
    ex.hand(rig.hand_far, scale)
    return rig


def _slam_lean(pose):
    """press_stamp leans his whole bulk into the slam (wind-up upright, lunge on the down
    stroke, hold, settle back): extra reach, and the weight of the gesture reads."""
    k = 0.0
    for arm in (pose.near, pose.far):
        if arm is not None and arm.gesture == "press_stamp":
            ph = arm.phase
            if ph < 0.35:
                k = max(k, -0.25 * core.inout_sine(ph / 0.35))
            elif ph < 0.5:
                k = max(k, lerp(-0.25, 1.0, core.in_quad((ph - 0.35) / 0.15)))
            elif ph < 0.75:
                k = max(k, 1.0)
            else:
                k = max(k, 1.0 - core.inout_sine((ph - 0.75) / 0.25))
            k *= clamp(arm.amt)
    return k


def _skeleton(pose, t, yaw):
    S = {}
    br = B.breathing(t, 0.15, pose.seed)          # big creature: a slow, deep breath
    pel = (0.0, PELVIS_Y, 0.0)
    S["pelvis"] = pel
    tilt = 0.28 + 0.2 * pose.lean + 0.26 * _slam_lean(pose) + 0.01 * br    # always hunched forward
    R = m_mul(m_rot_z(0.015 * B.sway(t, 0.12, pose.seed + 3)), m_rot_x(-tilt))
    S["R"], S["br"] = R, br

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["waist"] = T((0.0, -70.0, 10.0))
    S["chest"] = T((0.0, -220.0, 40.0 + 3.0 * br))
    shr = clamp(pose.shrug)
    sh_y = -335.0 - 4.0 * br - 30.0 * shr
    S["sh_y"] = sh_y
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y, 0.0)) for s in (-1.0, 1.0)}
    talk = clamp(pose.talk)
    nod = pose.head_nod * 0.3 + 0.02 * talk * math.sin(t * 3.0) + 0.008 * br
    hy = clamp(pose.head_turn, -1.2, 1.2) * 0.9
    hr = pose.head_tilt
    RH = m_mul(m_rot_y(hy - 0.2 * yaw), m_mul(m_rot_x(nod), m_rot_z(hr)))
    S["RH"], S["head_yaw"] = RH, hy - 0.2 * yaw
    # the head hangs low and forward between the shoulder mounds
    S["head_c"] = T((0.0, sh_y - 92.0 - 10.0 * shr, 62.0))
    feet = []
    for s in (-1.0, 1.0):
        hip = (s * HIP_W, PELVIS_Y + 10.0, 0.0)
        ank = (s * (HIP_W + 14.0), -ANKLE_H, 14.0)
        knee, ank = B.ik3(hip, ank, THIGH, SHIN, (s * 0.4, 0.0, 1.0))
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "side": s})
    S["feet"] = feet
    S["ctx"] = {"chest": S["chest"], "waist": S["waist"], "fwd": K.facing_dir(yaw), "phase": 0.0}
    return S


def _solve_arm(q, S, side, arm):
    sk = S["shoulders"][side]
    c = dict(S["ctx"], phase=arm.phase, near_side=-1.0 if q.yaw >= 0 else 1.0)
    stamp_g = arm.gesture in ("press_stamp", "hold_up_stamp")
    if arm.screen is not None and stamp_g:
        # aim the DIE FACE at the screen point (the wrist that puts it there, solved through
        # the real hand geometry -- see _aim_stamp)
        die = K.screen_to_body(q, q.proj, arm.screen, q.proj.depth(sk) + arm.depth)
        c["press_target"] = _aim_stamp(q, sk, side, die)
    tgt, hp, hang, z = TROLL_GESTURES.get(arm.gesture, _g_rest)(sk, side, c)
    if arm.amt < 1.0:
        t0, hp0, ha0, z0 = TROLL_GESTURES.get(arm.prev, _g_rest)(sk, side, dict(c, phase=0.0))
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 40.0
        tgt = v_add(v_lerp(t0, tgt, u), (side * arc * 0.5, -arc * 0.5, arc))
        hang = lerp(ha0, hang, u)
        if u < 0.5:
            hp = hp0
    if arm.target is not None:
        tgt = arm.target
    if arm.screen is not None and not stamp_g:
        tgt = K.screen_to_body(q, q.proj, arm.screen, q.proj.depth(sk) + arm.depth)
    if arm.hand:
        hp = arm.hand
    if arm.gesture == "arms_crossed":
        pole = (side * 1.0, 0.5, 0.3)
    else:
        pole = (side * 1.0, 0.6, -0.4)
    elbow, wrist = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side,
            "stamp": stamp_g and not arm.hold}


def _grip_of(proj, el, wr, side, yaw, hang=0.0, size=FIST):
    """Where B.hand puts the grip for this arm (2D): the hand is drawn at the wrist + 10 along
    the forearm, and its grip is (0.50, 0.06) hand lengths along / across it."""
    w2, e2 = proj.xy(wr), proj.xy(el)
    fx_, fy_ = core.normalize((w2[0] - e2[0], w2[1] - e2[1]))
    a = math.atan2(fy_, fx_) + hang
    fy = -1.0 if (side > 0) == (yaw >= 0) else 1.0
    return (w2[0] + fx_ * 10.0 + math.cos(a) * 0.50 * size - math.sin(a) * 0.06 * size * fy,
            w2[1] + fy_ * 10.0 + math.sin(a) * 0.50 * size + math.cos(a) * 0.06 * size * fy)


def _aim_stamp(q, sk, side, die):
    """The wrist target (body space) that lands the stamp's DIE FACE on `die`: the grip sits
    half a fist along the hand and the die hangs _stamp_die_y() below it, both depending on the
    forearm's direction -- so iterate the IK a few times with the true geometry. Out of reach,
    it returns the best effort (stand the troll within ~350 x scale px of the target)."""
    proj = q.proj
    dy = _stamp_die_y(FIST)
    tx, ty = proj.xy(die)
    wt = v_add(die, (0.0, -(dy + 0.3 * FIST), 0.0))
    pole = (side * 1.0, 0.6, -0.4)
    for _ in range(5):
        el, wr = B.ik3(sk, wt, UPPER_ARM, FOREARM, pole)
        gx, gy = _grip_of(proj, el, wr, side, q.yaw)
        ex_, ey_ = tx - gx, ty - (gy + dy)
        if abs(ex_) + abs(ey_) < 0.5:
            break
        wt = v_add(wt, (ex_ * proj.c, ey_, ex_ * proj.s))
    return wt


def _arm(q, A, side):
    """A massive stone arm (one capsule union) with a moss patch on the forearm, and the fist."""
    cr, proj, M = q.cr, q.proj, q.M
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    s_, o_ = K.caps(cr, [sh, el, wr], [62.0, 48.0, 44.0], q.lw)
    pal = q.shade(s_, M["stone"], outline=o_, size=110, rim=0.8)
    if q.detail >= 1:
        cr.save()
        s_.add(cr)
        cr.clip()
        # a moss patch over the elbow and a couple of cracks
        mp = q.P(M["moss"])
        nx, ny = -fdy, fdx
        cx_, cy_ = el[0] - nx * 26.0, el[1] - ny * 26.0
        cr.new_path()
        core.blob(cr, cx_, cy_, 30.0, 0.22, 8, int(side * 3 + 5))
        core.src(cr, mp.lit)
        cr.fill()
        core.src(cr, q.P(M["stone_dk"]).lit, 0.45)
        for k, u in enumerate((0.3, 0.62)):
            px, py = lerp(sh[0], el[0], u) + nx * 18.0 * (1 - 2 * k), lerp(sh[1], el[1], u) + ny * 18.0 * (1 - 2 * k)
            core.blob(cr, px, py, 16.0 - 4 * k, 0.3, 6, k + int(side * 7))
        core.blob(cr, lerp(el[0], wr[0], 0.55) - nx * 14.0, lerp(el[1], wr[1], 0.55) - ny * 14.0, 13.0, 0.3, 6, 3)
        cr.fill()
        B.detail_lines(cr, [[(el[0] + fdx * 40 + nx * 10, el[1] + fdy * 40 + ny * 10), (el[0] + fdx * 70 + nx * 22, el[1] + fdy * 70 + ny * 22),
                             (el[0] + fdx * 95 + nx * 12, el[1] + fdy * 95 + ny * 12)]], q.lw * 1.0, pal.line, 0.6)
        cr.restore()
    arm = A["arm"]
    hold = arm.hold
    if hold is None and arm.gesture in ("press_stamp", "hold_up_stamp"):
        hold = _stamp_cb(q.light)
    hang = ang + A["hang"]
    flip = (side > 0) == (q.yaw >= 0)
    fist = FIST * (0.72 if arm.gesture == "arms_crossed" else 1.0)     # folded arms: the fists tuck in
    return B.hand(cr, wr[0] + fdx * 10.0, wr[1] + fdy * 10.0, hang, fist, A["hand"], M["stone"], q.light_nb, q.lw,
                  flip=flip, claw=None, show_palm=False, hold=hold, finger_w=1.35, finger_len=0.9, palm_w=1.25,
                  detail=q.detail)


def _legs(q):
    """Short thick legs: rough breeches to the knee, stone shins and big flat feet."""
    cr, proj, S, M = q.cr, q.proj, q.S, q.M
    pairs, feet = [], []
    for f in S["feet"]:
        hip, kn = proj.xy(f["hip"]), proj.xy(f["knee"])
        pairs.append(K.caps(cr, [hip, kn], [52.0, 44.0], q.lw))
        a = f["ankle"]
        pts = []
        for k in range(8):
            ang = TAU * k / 8
            pts.append(proj.xy((a[0] + math.cos(ang) * 40.0, a[1] - 8.0 + math.sin(ang) * 6.0, a[2] + math.sin(ang) * 30.0)))
            pts.append(proj.xy((a[0] + math.cos(ang) * 46.0, a[1] + ANKLE_H - 8.0, a[2] + 26.0 + math.sin(ang) * 26.0)))
        pts.append(proj.xy((a[0], a[1] - 30.0, a[2])))
        feet.append(core.convex_hull(pts + [proj.xy((a[0], a[1] - 40.0, a[2]))] + K.circle_pts(kn, 40.0, 8)))
    K.union(q, feet, M["stone"], size=60, rim=0.6)
    K.union_paths(q, pairs, M["breeches"], size=90, rim=0.5)
    if q.detail >= 1 and proj.depth((0.0, 0.0, 1.0)) > -0.2:     # toes
        lines = []
        for f in S["feet"]:
            a = f["ankle"]
            for dx in (-18.0, 0.0, 18.0):
                p0 = proj.xy((a[0] + dx, a[1] + ANKLE_H - 18.0, a[2] + 40.0))
                p1 = proj.xy((a[0] + dx * 1.15, a[1] + ANKLE_H - 2.0, a[2] + 50.0))
                lines.append([p0, p1])
        B.detail_lines(cr, lines, q.lw * 1.1, q.P(M["stone"]).line, 0.7)


def _torso(q):
    """The boulder: one stone union of the chest mass, the gut and the two shoulder mounds,
    the leather jerkin over it (laced across a gap), and moss on the shoulders."""
    cr, proj, S, M = q.cr, q.proj, q.S, q.M
    T = S["T"]
    xy = proj.xy
    br = S["br"]
    sh_y = S["sh_y"]
    chest = B.ellipsoid_pts(xy, T((0.0, -215.0, 20.0)), 150.0 + 2 * br, 140.0, 98.0 + 3 * br, 10)
    gut = B.ellipsoid_pts(xy, T((0.0, -90.0, 20.0)), 125.0, 90.0, 90.0, 8)
    mounds = []
    for s in (-1.0, 1.0):
        mc = xy(T((s * 122.0, sh_y - 18.0, -10.0)))
        mounds.append([(mc[0] + math.cos(a) * 82.0, mc[1] + math.sin(a) * 58.0) for a in (TAU * i / 14 for i in range(14))])
    body_hull = core.convex_hull(chest + gut)
    path = K.union(q, [body_hull] + mounds, M["stone"], size=260, shadow=0.75, rim=0.9)
    pal = q.P(M["stone"])
    front = proj.depth(m_vec(S["R"], (0.0, 0.0, 1.0)))
    # ---- the jerkin: front panels over the chest/gut, sleeveless, laced over a gap
    cr.save()
    path.add(cr)
    cr.clip()
    jk = []
    for i in range(16):
        a = TAU * i / 16
        jk.append(xy(T((math.sin(a) * 156.0, -330.0 + 18.0 * math.cos(a), 20.0 + math.cos(a) * 106.0))))
        jk.append(xy(T((math.sin(a) * 140.0, -40.0 - 10.0 * math.cos(a), 20.0 + math.cos(a) * 98.0))))
    jh = core.convex_hull(jk)
    js, jo = B.smooth_paths(cr, jh, q.lw, 0.85)
    jp = q.shade(js, M["jerkin"], outline=jo, size=200, shadow=0.7, rim=0.6)
    if front > 0.0:
        # the gap down the front, showing stone, with laces criss-crossing it
        gap_l, gap_r = [], []
        for k in range(7):
            yy = -310.0 + k * 40.0
            w = 18.0 + 10.0 * math.sin(k * 0.7) + 4.0 * br
            gap_l.append(xy(T((-w, yy, 20.0 + 116.0 - abs(yy + 170.0) * 0.12))))
            gap_r.append(xy(T((w, yy, 20.0 + 116.0 - abs(yy + 170.0) * 0.12))))
        cr.new_path()
        core.polygon(cr, gap_l + gap_r[::-1])
        core.src(cr, jp.line)
        cr.fill()
        cr.new_path()
        core.polygon(cr, [(p[0] + 2.5, p[1]) for p in gap_l] + [(p[0] - 2.5, p[1]) for p in gap_r[::-1]])
        core.src(cr, core.mix(pal.shadow, pal.lit, 0.35))
        cr.fill()
        laces = []
        for k in range(len(gap_l) - 1):
            laces.append([gap_l[k], gap_r[k + 1]])
            laces.append([gap_r[k], gap_l[k + 1]])
        B.detail_lines(cr, laces, q.lw * 1.6, q.P(M["lace"]).lit, 1.0, taper=(1.0, 1.0, 1.0))
        if q.detail >= 1:                  # stitching along the jerkin's seams + the straining folds
            B.detail_lines(cr, [[xy(T((-90.0, -300.0, 125.0))), xy(T((-110.0, -200.0, 125.0))), xy(T((-100.0, -80.0, 115.0)))],
                                [xy(T((90.0, -300.0, 125.0))), xy(T((110.0, -200.0, 125.0))), xy(T((100.0, -80.0, 115.0)))]],
                           q.lw * 0.8, jp.line, 0.4)
    cr.restore()
    # ---- moss on the shoulder mounds, lichen speckles, cracks
    mp = q.P(M["moss"])
    cr.new_path()
    for s in (-1.0, 1.0):
        c = xy(T((s * 122.0, sh_y - 52.0, 0.0)))
        core.blob(cr, c[0], c[1], 64.0, 0.25, 9, int(7 + s), sy=0.75)
    moss = Path(cr)
    cr.save()
    for m_ in mounds:
        core.smooth_closed(cr, m_, 0.85)
    cr.clip()
    moss.add(cr)
    core.src(cr, mp.lit)
    cr.fill()
    if q.detail >= 1:
        core.src(cr, core.mix(mp.lit, mp.hi, 0.5))
        for i in range(14):
            px = (core.hash01(i, 3) - 0.5) * 80.0
            py = (core.hash01(i, 4) - 0.5) * 50.0
            for s in (-1.0, 1.0):
                c = xy(T((s * 122.0 + px, sh_y - 54.0 + py * 0.5, 0.0)))
                core.circle(cr, c[0], c[1], 3.0)
        cr.fill()
    cr.restore()
    if q.detail >= 1:
        cr.save()
        cr.new_path()
        for m_ in mounds:
            core.smooth_closed(cr, m_, 0.85)
        cr.clip()
        lc = q.P(Mat.of(TROLL_COLORS["lichen"]))
        core.src(cr, lc.lit, 0.8)
        for i in range(10):
            s = 1.0 if i % 2 else -1.0
            c = xy(T((s * (90.0 + 70.0 * core.hash01(i, 8)), sh_y - 10.0 + 40.0 * core.hash01(i, 9), 30.0)))
            core.circle(cr, c[0], c[1], 3.0 + 3.0 * core.hash01(i, 10))
        cr.fill()
        cracks = [[xy(T((-130.0, sh_y - 20.0, 40.0))), xy(T((-115.0, sh_y + 30.0, 70.0))), xy(T((-128.0, sh_y + 70.0, 80.0)))],
                  [xy(T((128.0, sh_y + 10.0, 50.0))), xy(T((140.0, sh_y + 60.0, 70.0)))]]
        B.detail_lines(cr, cracks, q.lw * 1.2, pal.line, 0.65)
        cr.restore()


# ----------------------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------------------

def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH, HC = S["RH"], S["head_c"]
    e = B.expr(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    lw = q.lw
    hyaw = q.yaw + S["head_yaw"]
    near = -1.0 if hyaw >= 0 else 1.0
    far = -near
    jaw = clamp(clamp(pose.talk) * 0.75 + e.open * 0.8)
    xy = proj.xy

    def P(v):
        w = m_vec(RH, v)
        return xy((HC[0] + w[0] * HS, HC[1] + w[1] * HS, HC[2] + w[2] * HS))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    stone = q.P(M["stone"])
    # ears: small stone lumps on the sides
    for s in (far, near):
        if nz((s * 0.9, 0.0, -0.2)) < -0.6:
            continue
        ec = P((s * 66.0, 4.0, -8.0))
        es, eo = B.ellipse_paths(cr, ec[0], ec[1], 16.0 * HS, 22.0 * HS, lw, 0.3 * s)
        if s == near:
            q.shade(es, M["stone_dk"], outline=eo, size=20, rim=0.5)
        else:
            K.flat(q, es, eo, M["stone_dk"], tone=0.3)
    # skull + brow shelf + jaw (underbite) as ONE stone union
    skull = K.circle_pts(P((0.0, -10.0, -6.0)), 62.0 * HS, 16)
    brow = B.ellipsoid_pts(P, (0.0, -24.0, 40.0), 60.0, 18.0, 22.0, 8)
    ja = 0.32 * jaw
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):            # rotate about the jaw hinge (0, 10, 0): the chin swings DOWN as it opens
        yy, zz = v[1] - 10.0, v[2]
        return (v[0], 10.0 + yy * cj + zz * sj, -yy * sj + zz * cj)

    jaw_pts = B.ellipsoid_pts(lambda v: P(J(v)), (0.0, 42.0, 34.0), 64.0, 26.0, 40.0, 8)
    hull_s = core.convex_hull(skull + brow)
    hull_j = core.convex_hull(jaw_pts + K.circle_pts(P(J((0.0, 30.0, 0.0))), 46.0 * HS, 8))
    hp = K.union(q, [hull_s, hull_j], M["stone"], size=130, shadow=0.8, rim=0.8)
    # mouth: the line between the overbite and the jaw (opens slow and flat when he talks)
    corners = {s: P(J((s * 50.0, 26.0 - 4.0 * e.smile, 50.0))) for s in (-1.0, 1.0)}
    mid = P(J((0.0, 30.0 + 8.0 * jaw, 66.0)))
    top_mid = P((0.0, 22.0, 70.0))
    if jaw > 0.05:
        cr.new_path()
        cr.move_to(*corners[-1.0])
        cr.curve_to(corners[-1.0][0], top_mid[1], corners[1.0][0], top_mid[1], *corners[1.0])
        cr.curve_to(corners[1.0][0], mid[1] + 10.0, corners[-1.0][0], mid[1] + 10.0, *corners[-1.0])
        cr.close_path()
        B.flat(cr, Path(cr), TROLL_COLORS["mouth"], lw * 0.9, stone.line)
    else:
        B.detail_line(cr, [corners[-1.0], ((corners[-1.0][0] + mid[0]) / 2, mid[1] + 2.0), mid,
                           ((corners[1.0][0] + mid[0]) / 2, mid[1] + 2.0), corners[1.0]], lw * 1.5, stone.line, 1.0)
    # tusks: rising from the lower jaw at the mouth corners
    for s in (far, near):
        if nz((s * 0.5, 0.3, 0.8)) < -0.1:
            continue
        b0 = P(J((s * 36.0, 30.0, 58.0)))
        b1 = P(J((s * 41.0, 8.0, 63.0)))
        ts, to = B.taper_paths(cr, [b0, ((b0[0] + b1[0]) / 2 + s * 2, (b0[1] + b1[1]) / 2), b1], 13.0 * HS, 3.0, lw * 0.8)
        tpal = K.flat(q, ts, to, M["tusk"])
        if q.detail >= 1:       # a shadow down the tusk's inner side
            B.detail_lines(cr, [[b0, ((b0[0] + b1[0]) / 2 - s * 1.5, (b0[1] + b1[1]) / 2), b1]], lw * 1.6, tpal.shadow, 0.8,
                           taper=(1.0, 0.8, 0.1))
    # nose: a big round stone nose under the brow
    nc = P((0.0, -4.0, 66.0))
    ns, no = B.ellipse_paths(cr, nc[0], nc[1], 20.0 * HS, 16.0 * HS, lw)
    q.shade(ns, M["stone"], outline=no, size=40, rim=0.6)
    if q.detail >= 1:
        nl = [[P((s * 7.0, 5.0, 79.0)), P((s * 12.0, 3.0, 76.0))] for s in (-1.0, 1.0) if nz((s * 0.4, 0.4, 0.8)) > -0.1]
        B.detail_lines(cr, nl, lw * 1.6, stone.line, 0.8, taper=(1.0, 0.8, 0.3))
    # tiny bored eyes deep under the brow shelf, half-lidded, sliding sideways (look)
    blink = B.auto_blink(t, pose.seed + 61, interval=(3.0, 6.0)) if pose.blink is None else pose.blink
    eyes = []
    for s in (far, near):
        ec = P((s * 26.0, -10.0, 54.0))
        eyes.append(ec)
        fz = nz((s * 0.4, -0.1, 0.9))
        if fz < 0.08:
            continue
        fore = clamp(0.3 + fz * 0.8, 0.3, 1.0)
        outer = 1.0 if P((s * 40.0, -10.0, 50.0))[0] > ec[0] else -1.0
        B.eye(cr, ec[0], ec[1], 10.0 * HS * fore, 8.5 * HS, q.light, lw * 0.9, look=(pose.look[0] * outer, pose.look[1]),
              lid=e.lid, lid_bot=e.lid_bot, tilt=e.lid_tilt, outer=outer, blink=blink, iris=TROLL_COLORS["eye"],
              pupil="#1d120c", pupil_size=0.5, iris_size=0.8, skin=TROLL_COLORS["stone"], crease=0.0,
              bags=0.6 if q.detail >= 1 else 0.0, line=stone.line, lid_shade=0.2, lash=1.2)
    # the brow shelf's lower edge shadows the eyes + bushy stone brows that act (a little)
    li = (e.brow_in * 0.6 + e.brow_y) * 6.0
    lo = (e.brow_out * 0.5 + e.brow_y) * 5.0
    brows = []
    for s in (far, near):
        if nz((s * 0.4, -0.4, 0.8)) < -0.05:
            continue
        brows.append([P((s * 8.0, -26.0 - li, 62.0)), P((s * 28.0, -30.0 - (li + lo) / 2, 58.0)), P((s * 48.0, -24.0 - lo, 46.0))])
    if brows:
        cr.save()
        hp.add(cr)
        cr.clip()
        B.detail_lines(cr, brows, lw * 4.5 * HS, q.P(M["stone_dk"]).shadow, 1.0, taper=(0.5, 1.0, 0.4))
        cr.restore()
    # moss on the crown + a few cracks
    if q.detail >= 1:
        cr.save()
        hp.add(cr)
        cr.clip()
        mpal = q.P(M["moss"])
        c = P((0.0, -58.0, -14.0))
        cr.new_path()
        core.blob(cr, c[0], c[1], 40.0 * HS, 0.28, 9, 13, sy=0.6)
        core.src(cr, mpal.lit)
        cr.fill()
        # darker rock blotches: a storybook stone texture
        core.src(cr, q.P(M["stone_dk"]).lit, 0.45)
        for (bx, by, bz, br_) in ((-40.0, -20.0, 30.0, 12.0), (44.0, -30.0, 20.0, 9.0), (20.0, 30.0, 50.0, 8.0), (-50.0, 20.0, 20.0, 10.0)):
            if nz((bx / 60.0, by / 60.0, bz / 60.0)) > 0.1:
                c2 = P((bx, by, bz))
                core.blob(cr, c2[0], c2[1], br_ * HS, 0.3, 6, int(bx))
        cr.fill()
        B.detail_lines(cr, [[P((-30.0, -46.0, 30.0)), P((-22.0, -36.0, 44.0)), P((-30.0, -30.0, 50.0))],
                            [P((36.0, 10.0, 50.0)), P((44.0, 26.0, 44.0))]], lw * 1.1, stone.line, 0.6)
        cr.restore()
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mid, "eyes": eyes, "top": P((0.0, -70.0, 0.0))}


# ----------------------------------------------------------------------------------------
# sheets
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("troll", lambda cr, x, y, sc: draw_troll(cr, x, y, sc, TrollPose(facing=1), t=0.4), 330.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    SC = 0.46
    for label, pose in (("3/4 left", TrollPose(facing=-1)), ("front", TrollPose(facing=0)), ("3/4 right", TrollPose(facing=1)),
                        ("arms crossed (bouncer idle)", TrollPose(facing=-1, turn=0.4, near=TrollArm("arms_crossed"), far=TrollArm("arms_crossed"))),
                        ("hold_up_stamp", TrollPose(facing=-1, near=TrollArm("hold_up_stamp"), look=(-0.6, 0.0))),
                        ("press_stamp 0.5 (thunk)", TrollPose(facing=-1, near=TrollArm("press_stamp", phase=0.5), look=(-0.5, 0.5), head_nod=-0.2))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 290, 470, floor=440)
            # the slam lunges him forward: stand him further back so the die stays in the cell
            lunge = 60 if p.near.gesture == "press_stamp" else 0
            draw_troll(cr, 145 - 14 * p.facing + lunge, 455, SC, p.with_(blink=0.0), neutral, t=0.4)
        add(label, 290, 470, fn, "turnaround & gestures")
    FS = 1.6
    for label, kw in (("bored (default)", {}), ("look sideways", dict(look=(-0.9, 0.1))), ("talking: 'Keep it light, buddy.'", dict(talk=0.8)),
                      ("skeptical", dict(mood="skeptical")), ("blink", dict(blink=1.0)), ("front: bored", dict(facing=0))):
        kw = dict(kw)
        facing = kw.pop("facing", -1)
        pose = TrollPose(facing=facing, blink=kw.pop("blink", 0.0), **kw)

        def fn(cr, p=pose):
            B.sheet_bg(cr, 300, 300)
            hx, hy = K.head_frame(draw_troll, p, FS, neutral)
            draw_troll(cr, 150 - hx, 150 - hy, FS, p, neutral, t=0.4)
        add(label, 300, 300, fn, "faces & light")

    def stamp_cell(cr):
        B.sheet_bg(cr, 300, 300, "tavern")
        cr.save()
        cr.translate(150, 130)
        cr.scale(2.4, 2.4)
        troll_stamp(cr, B.HandFrame(0, 0, 0, 1, [], (0, 0), False), L["tavern"])
        cr.restore()
        core.text(cr, "SMILE die (mirrored), pink ink", 150, 270, 13, core.SANS, "#f0e6ee", align="center")
    add("the stamp prop", 300, 300, stamp_cell, "faces & light")
    for name in ("tavern", "street_night", "neutral"):
        def fn(cr, name=name):
            B.sheet_bg(cr, 300, 300, name, floor=270)
            draw_troll(cr, 150, 285, 0.4, TrollPose(facing=-1, near=TrollArm("hold_up_stamp"), blink=0.0), L[name], t=0.4)
        add(name, 300, 300, fn, "faces & light")
    return items
