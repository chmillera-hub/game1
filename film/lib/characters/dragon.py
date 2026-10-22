"""dragon.py -- THE HERO: the young dragon ("the Man", speaker MAN).

A lanky, gently hunched young-adult dragon: slate-teal scales, sand belly plates, two small
swept-back ivory horns, a soft snout, big tired amber eyes under heavy lids, expressive brow
ridges, ear-fins, small folded wings (drooped = lonely, lifted = happy), a long expressive tail,
a long charcoal-navy traveller's coat and a chunky mustard knitted scarf.

    from film.lib import characters as ch
    pose = ch.DragonPose(facing=1, sit=1.0, mood="tired", talk=timeline.talk(1, t, "MAN"),
                         wings=-0.7, near=ch.Arm("hand_to_ear", hold=draw_stone))
    rig = ch.draw_dragon(cr, x, ground_y, scale=0.9, pose=pose, light=ch.LIGHTS["washhouse"], t=t)
    rig.hand_near.x, rig.mouth ...                 # attach points in the caller's coordinates

Scale 1.0: standing, ground -> horn tips = DRAGON_HEIGHT = 520 px (crown of the head ~488 in
his default hunch, ~503 upright; eyes ~445). Seated on the standard bench (DRAGON_SEAT_H = 125
px) the crown is ~390 px above the ground, the eyes ~345. Anchor (x, y) = the GROUND point
below his pelvis (between the feet when standing, below the seat when sitting);
pose.anchor="seat" takes the seat point instead. Internally "3D-lite": joints are
posed in body space (X = his left, Y down, Z forward) and projected with the body yaw, so he
turns continuously from 3/4-left through front to 3/4-right, nods and sits down smoothly.
"""

import math
from dataclasses import dataclass, field, replace

from .. import core, fx
from ..core import clamp, lerp, smooth
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp

__all__ = ["DragonPose", "Arm", "DragonRig", "draw_dragon", "dragon_smoke", "dragon_embers",
           "dragon_stride", "dragon_walk_phase", "DRAGON_HEIGHT", "DRAGON_SEAT_H", "DRAGON_LINE",
           "DRAGON_COLORS", "DRAGON_GESTURES", "dragon_mats"]

# ----------------------------------------------------------------------------------------
# design constants (body space px at scale 1.0)
# ----------------------------------------------------------------------------------------
DRAGON_HEIGHT = 520.0
DRAGON_SEAT_H = 125.0      # standard bench seat height (props: build benches to this * scale)
DRAGON_LINE = 2.4          # outline weight at scale 1.0

DRAGON_COLORS = {
    "scales": "#3E6E73",     # slate teal
    "scales_dk": "#2B5357",  # ridges, spines, brow ridges, tail tip
    "belly": "#D9C08C",      # sand belly plates
    "coat": "#2F3A4F",       # charcoal-navy coat
    "coat_lining": "#4C405E",  # dusky plum lining (lapel facings, cuffs)
    "scarf": "#C9A13B",      # mustard knit
    "horn": "#E6D8B8",       # ivory horns
    "claw": "#3F3D3A",       # dark slate claws
    "eye": "#E2A23A",        # amber-gold iris
    "eye_hi": "#FFD978",
    "membrane": "#6F9C94",   # wing membrane (lighter teal)
    "mouth": "#5B2430",
    "tongue": "#C25B67",
    "button": "#B8913F",     # brass
    "fin": "#62938C",        # ear-fin membrane
}

HS = 1.25                  # head scale (head-space units -> body px)
PELVIS_Y = -238.0
HIP_W = 20.0
THIGH, SHIN, ANKLE_H = 104.0, 106.0, 22.0
UPPER_ARM, FOREARM = 98.0, 94.0
HAND_LEN = 56.0
SHOULDER_W = 47.0
STRIDE = 150.0              # body-space distance per walk cycle (two steps)
ELEV = 0.12
SIT_SWAP = 0.6              # sit >= this: the seated coat (lap + back flap) replaces the skirt

_MATS = {}


def dragon_mats():
    """Materials used by the dragon (also handy for props that should match him)."""
    if not _MATS:
        C = DRAGON_COLORS
        _MATS.update({
            "scales": Mat.of(C["scales"], sss=0.15),
            "scales_dk": Mat.of(C["scales_dk"], sss=0.1),
            "belly": Mat.of(C["belly"], sss=0.5, line_k=0.5),
            "coat": Mat.of(C["coat"], shadow_k=1.15, line_k=0.6),
            "coat_wet": Mat.of(core.shade(C["coat"], 0.18), shadow_k=1.2, line_k=0.6),
            "lining": Mat.of(C["coat_lining"], shadow_k=1.1),
            "scarf": Mat.of(C["scarf"], shadow_k=1.1, line_k=0.5),
            "scarf_wet": Mat.of(core.shade(C["scarf"], 0.22), shadow_k=1.15, line_k=0.5),
            "horn": Mat.of(C["horn"], sheen=0.5, line_k=0.45),
            "claw": Mat.of(C["claw"], sheen=0.4),
            "membrane": Mat.of(C["membrane"], sss=0.6),
            "fin": Mat.of(C["fin"], sss=0.6),
            "button": Mat.of(C["button"], sheen=0.8),
            "mouth": Mat.of(C["mouth"]),
            "tongue": Mat.of(C["tongue"], sss=0.5),
        })
    return _MATS


# ----------------------------------------------------------------------------------------
# pose
# ----------------------------------------------------------------------------------------

@dataclass
class Arm:
    """One arm's gesture. gesture names: see DRAGON_GESTURES.

    amt     0..1 blend from `prev` into `gesture` (animate it for the move)
    hold    callback hold(cr, frame) drawing a prop gripped in the hand (z-correct: between the
            palm and the curled fingers); cr origin = grip point, +x along the fingers
    stamp   callback stamp(cr) drawing on the BACK of the hand (look_at_hand: the SMILE stamp)
    target  explicit hand target in body space (x, y, z) overriding the gesture
    hand    hand pose override (base.HAND_POSES name)
    phase   gesture-internal 0..1 (toss_crumbs: wind-up -> release, wave)
    """
    gesture: str = "rest"
    amt: float = 1.0
    prev: str = "rest"
    hold: object = None
    stamp: object = None
    target: tuple = None
    hand: str = None
    phase: float = 0.0


@dataclass
class DragonPose:
    """Everything that poses the dragon. All fields are optional.

    facing    +1 faces screen-right (3/4 view), -1 screen-left, 0 front (toward camera)
    turn      extra body yaw -1..1 (about +-0.6 rad) on top of facing (fine 3/4 adjustments)
    sit       0 standing .. 1 seated (blend while sitting down); seat_h seat height (px @1.0)
    walk      0..1 blend into the walk cycle; phase = cycle phase (dragon_walk_phase)
    lean      -1 back .. +1 forward; hunch 0 upright .. 1 very hunched (his default 0.45)
    head_turn -1..1 head yaw relative to the body; head_tilt roll (rad); head_nod -1 down..+1 up
    look      eye direction (-1..1, -1..1), relative to the head (+x = screen right)
    mood      base.MOODS name or base.Expr; mood2 + mood_mix blend toward a second mood
    talk      0..1 mouth from timeline.talk(); smile -1..1 overrides the mood's smile
    laugh     0..1 the big laugh (head back, shoulders shake, wings lift, eyes squeeze)
    sigh      0..1 deflate (shoulders drop, eyes close, exhale) -- add dragon_smoke() for the puff
    blink     None = automatic, else 0..1 lid closure
    wings     -1 drooped (lonely) .. 0 folded .. +1 lifted/half-open (happy)
    tail_curl 0..1 tip curl; tail_swing -1..1 sideways sweep; tail_drag 0..1 drags on the ground
    tail_front  tail wraps around the front (curled around a bench leg)
    near/far  Arm() for the arm nearer / farther from the camera (front view: near = screen-left)
    damp      0..1 rain-soaked (darker coat/scarf, droopier fringe)
    anchor    "ground" (default: ground point below the pelvis) or "seat" (the seat point)
    elev      camera elevation (0 eye level .. 0.3 from above); shadow: draw the contact shadow
    """
    facing: int = 1
    turn: float = 0.0
    sit: float = 0.0
    seat_h: float = DRAGON_SEAT_H
    walk: float = 0.0
    phase: float = 0.0
    lean: float = 0.0
    hunch: float = 0.45
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    mood: object = "tired"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    smile: float = None
    laugh: float = 0.0
    sigh: float = 0.0
    blink: float = None
    wings: float = -0.4
    tail_curl: float = 0.4
    tail_swing: float = 0.0
    tail_drag: float = 0.0
    tail_front: bool = False
    near: Arm = field(default_factory=Arm)
    far: Arm = field(default_factory=Arm)
    damp: float = 0.0
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class DragonRig:
    """Attach points returned by draw_dragon, all in the CALLER's coordinates."""
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    nose: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    ear_near: tuple = (0.0, 0.0)
    top: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    lap: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    seat: tuple = (0.0, 0.0)
    scale: float = 1.0
    facing: float = 1.0        # +1 body faces screen-right (or head-on), -1 screen-left
    yaw: float = 0.0           # continuous body turn (rad): 0 head-on, +-1.0 the 3/4 views


def _yaw_of(facing, turn):
    base = {1: 1.0, -1: -1.0, 0: 0.0}.get(int(facing), 0.0)
    return clamp(base + turn * 0.6, -1.45, 1.45)


def dragon_stride(scale=1.0, facing=1, turn=0.0):
    """Screen px the anchor must travel per walk cycle so his feet don't slide."""
    return STRIDE * abs(math.sin(_yaw_of(facing, turn))) * scale


def dragon_walk_phase(distance_px, scale=1.0, facing=1, turn=0.0):
    """Walk phase from the screen distance travelled (use with DragonPose(walk=1, phase=...))."""
    st = dragon_stride(scale, facing, turn)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


# ----------------------------------------------------------------------------------------
# gestures -> (hand target in body space, hand pose, extra hand angle, layer)
# layer: "front" (over the head), "mid" (over the body, under the head), "auto" (by view)
# ----------------------------------------------------------------------------------------

def _rest_sit(sit):
    """How far the resting hands have moved from hanging to the thighs (0..1) while sitting."""
    return smooth(clamp((sit - 0.25) / 0.6))


def _g_rest(sk, side, c):
    stand = v_add(sk, (side * 12.0, 172.0, 16.0))
    k = _rest_sit(c["sit"])
    if k <= 0.0:
        return stand, "relaxed", 0.0, "auto"
    hip = c["hip"][side]
    kn = c["knee"][0 if side < 0 else 1]
    on_thigh = v_add(v_lerp(hip, kn, 0.6), (side * 8.0, -24.0, -8.0))
    return v_lerp(stand, on_thigh, k), "relaxed", 0.25 * k, ("mid" if c["sit"] >= SIT_SWAP else "auto")


def _g_hand_to_ear(sk, side, c):
    # wrist down by the jaw, hand rising along the side of the head: palm (and stone) on the ear
    ear = c["ear"][0 if side < 0 else 1]
    return v_add(ear, (side * 10.0, 38.0, -2.0)), "cup", -0.3, "front"


def _g_offer(sk, side, c):
    # seated, the hand reaches forward over the knees instead of dropping onto them
    return v_add(sk, (side * 2.0, lerp(100.0, 64.0, c["sit"]), lerp(116.0, 132.0, c["sit"]))), "offer", 0.0, "front"


def _g_hold_item(sk, side, c):
    return v_add(sk, (side * 4.0, 96.0, 96.0)), "grip", 0.0, "front"


def _g_carry_bag(sk, side, c):
    return v_add(sk, (side * 14.0, 166.0, 40.0)), "grip", 0.0, "auto"


def _g_slide_note(sk, side, c):
    return v_add(sk, (side * -8.0, 110.0, 126.0)), "flat", 0.0, "front"


def _g_look_at_hand(sk, side, c):
    # back of the hand raised in front of the chest, below the snout, toward the camera
    hc = c["head_c"]
    return v_add(hc, (side * 14.0, 96.0, 92.0)), "back", 0.0, "front"


def _g_arms_crossed(sk, side, c):
    ch = c["chest"]
    return v_add(ch, (-side * 36.0, 30.0 + (5.0 if side < 0 else 0.0), 44.0 + (6.0 if side < 0 else 0.0))), "relaxed", 0.0, "front"


def _g_hug(sk, side, c):
    return v_add(sk, (side * 64.0, 70.0, 96.0)), "open", 0.0, "front"


def _g_toss(sk, side, c):
    ph = c["phase"]
    a = v_add(sk, (side * 2.0, 126.0, 62.0))
    b = v_add(sk, (side * 2.0, 64.0, 130.0))
    u = core.inout_sine(clamp(ph / 0.55)) if ph < 0.55 else 1.0 - 0.25 * core.inout_sine((ph - 0.55) / 0.45)
    return v_lerp(a, b, u), ("pinch" if ph < 0.45 else "open"), 0.0, "front"


def _g_hold_book(sk, side, c):
    ch = c["chest"]
    return v_add(ch, (side * 62.0, 48.0, 60.0)), "grip", 0.0, "front"


def _g_pockets(sk, side, c):
    hp = c["hip"][side]
    return v_add(hp, (side * 30.0, -6.0, 18.0)), "fist", 0.0, "auto"


def _g_point(sk, side, c):
    return v_add(sk, (side * 8.0, 60.0, 150.0)), "point", 0.0, "front"


def _g_wave(sk, side, c):
    # forearm up, open palm to the camera, out beside the head; phase wags it side to side
    ph = c["phase"]
    return v_add(sk, (side * (74.0 + 16.0 * math.sin(ph * math.tau * 2)), -60.0, 34.0)), "open", 0.0, "front"


DRAGON_GESTURES = {
    "rest": _g_rest, "hand_to_ear": _g_hand_to_ear, "hand_out_offer": _g_offer,
    "hold_item": _g_hold_item, "carry_bag": _g_carry_bag, "slide_note": _g_slide_note,
    "look_at_hand": _g_look_at_hand, "arms_crossed": _g_arms_crossed, "hug": _g_hug,
    "toss_crumbs": _g_toss, "hold_book": _g_hold_book, "pockets": _g_pockets, "point": _g_point,
    "wave": _g_wave,
}


# ----------------------------------------------------------------------------------------
# per-draw context
# ----------------------------------------------------------------------------------------

def _circle2(c, r, n=12):
    return [(c[0] + math.cos(math.tau * i / n) * r, c[1] + math.sin(math.tau * i / n) * r) for i in range(n)]


class _Q:
    """Per-draw context: cr, projection, light, line weight, level of detail, time, skeleton."""
    __slots__ = ("cr", "proj", "light", "lw", "detail", "t", "pose", "yaw", "sit", "M", "S", "pal")

    def P(self, mat):
        p = self.pal.get(mat)
        if p is None:
            p = self.pal[mat] = B.palette(self.light, mat)
        return p

    def shade(self, path, mat, lw=None, **kw):
        return B.shade(self.cr, path, mat, self.light, self.lw if lw is None else lw, **kw)

    def hull(self, pts, tension=0.85):
        return B.hull_paths(self.cr, pts, self.lw, tension)


def _coat_mat(q):
    return q.M["coat_wet"] if q.pose.damp > 0.5 else q.M["coat"]


def _scarf_mat(q):
    return q.M["scarf_wet"] if q.pose.damp > 0.5 else q.M["scarf"]


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_dragon(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    """Draw the dragon with its anchor at (x, y) (see module doc). Returns a DragonRig.

    t drives the idle life (breathing, blinks, tail/wing/scarf secondary motion) -- pass the
    scene time. detail: None = automatic level of detail from the on-screen size (0..2)."""
    pose = pose or DragonPose()
    light = light or B.LIGHTS["neutral"]
    q = _Q()
    q.cr, q.M, q.light, q.t, q.pose, q.pal = cr, dragon_mats(), light, t, pose, {}
    yaw = _yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    sit = clamp(pose.sit)
    q.sit = sit
    seat_h = pose.seat_h
    dev = scale * B.device_scale(cr)
    if detail is None:
        detail = 2 if dev >= 0.9 else 1 if dev >= 0.55 else 0
    q.detail = detail
    q.lw = B.line_for(DRAGON_LINE, dev)

    cr.save()
    cr.translate(x, y + (seat_h * scale * sit if pose.anchor == "seat" else 0.0))
    cr.scale(scale, scale)

    S = _skeleton(pose, t, sit, seat_h)
    q.S = S
    rig = DragonRig(scale=scale, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)

    if pose.shadow:
        fa = [proj.xy(f["ankle"]) for f in S["feet"]]
        cxs = (fa[0][0] + fa[1][0]) / 2
        w = 64 + 26 * abs(math.cos(yaw)) + 36 * abs(math.sin(yaw)) * sit
        B.contact_shadow(cr, cxs - 10 * math.sin(yaw) * (1 - sit), 2.0, w, 13 + 5 * sit, alpha=0.34)

    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    arms = {near_side: pose.near, far_side: pose.far}
    A = {s: _solve_arm(q, S, s, arms[s]) for s in (near_side, far_side)}
    frontish = abs(yaw) < 0.38
    zf = A[far_side]["z"]
    if zf == "auto":
        far_layer = "mid" if frontish else "back"
    elif zf == "front":
        far_layer = "front" if frontish else "mid"
    else:
        far_layer = zf
    near_layer = "mid" if A[near_side]["z"] == "mid" else "front"
    # two-handed prop (e.g. the open book): both arms "hold_book", one of them carries `hold`
    two_hand = None
    if pose.near.gesture == "hold_book" and pose.far.gesture == "hold_book":
        two_hand = pose.near.hold or pose.far.hold
        if two_hand is not None:
            near_layer = far_layer = "two"

    # ---------------- back to front
    _wing(q, far_side)
    _tail(q)
    if far_layer == "back":
        rig.hand_far = _arm(q, A[far_side], far_side)
    _leg(q, far_side)
    _wing(q, near_side)
    _scarf_back_end(q)
    if sit < SIT_SWAP:
        _leg(q, near_side)
        _coat(q)
    else:
        _coat_back_flap(q)
        _coat(q)
        _leg(q, near_side)
        _lap(q)
    _collar(q)
    _neck(q)
    _scarf(q)
    if far_layer == "mid":
        rig.hand_far = _arm(q, A[far_side], far_side)
    if near_layer == "mid":
        rig.hand_near = _arm(q, A[near_side], near_side)
    head = _head(q)
    if two_hand:
        rig.hand_far, rig.hand_near = _two_hand_prop(q, A[far_side], A[near_side], two_hand)
    else:
        if near_layer == "front":
            rig.hand_near = _arm(q, A[near_side], near_side)
        if far_layer == "front":
            rig.hand_far = _arm(q, A[far_side], far_side)
    if pose.tail_front and sit >= SIT_SWAP:
        # the part curled in front of the feet goes over the legs and the coat
        _tail(q, front=max(proj.depth(f["ankle"]) for f in S["feet"]) + 12.0)

    # ---------------- attach points -> caller coordinates
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    rig.head = C(head["center"])
    rig.mouth = C(head["mouth"])
    rig.nose = C(head["nose"])
    rig.eyes = [C(e) for e in head["eyes"]]
    rig.ear_near = C(head["ear_near"])
    rig.top = C(head["top"])
    rig.chest = C(proj.xy(S["chest"]))
    rig.lap = C(proj.xy(v_lerp(S["pelvis"], v_lerp(S["knee"][0], S["knee"][1], 0.5), 0.6)))
    rig.feet = [C(proj.xy(f["ankle"])) for f in S["feet"]]
    rig.seat = C((0.0, -seat_h * sit))
    for hf in (rig.hand_near, rig.hand_far):
        if hf is not None:
            hf.x, hf.y = C((hf.x, hf.y))
            hf.tips = [C(tp) for tp in hf.tips]
            hf.palm = C(hf.palm)
            hf.scale *= scale
    return rig


# ----------------------------------------------------------------------------------------
# skeleton (body space)
# ----------------------------------------------------------------------------------------

def _skeleton(pose, t, sit, seat_h):
    S = {}
    br = B.breathing(t, 0.21, pose.seed)
    laugh = clamp(pose.laugh)
    sigh = clamp(pose.sigh)
    hunch = clamp(pose.hunch + 0.35 * sigh - 0.3 * laugh, 0.0, 1.2)
    walk = clamp(pose.walk)
    wc = B.walk_cycle(pose.phase, stride=STRIDE, lift=24.0, bob=4.0, swing=1.0)
    shake = laugh * (math.sin(t * math.tau * 6.5) * 2.6 + math.sin(t * math.tau * 3.1) * 1.2)
    S.update(br=br, hunch=hunch, wc=wc, walk=walk, shake=shake)

    stand_pel = (0.0, PELVIS_Y + walk * wc.hip_dy, 0.0)
    sit_pel = (0.0, -seat_h - 14.0, -8.0)
    arc = math.sin(math.pi * sit)           # 0 at both ends, 1 half-way down
    # sitting down: the hips travel down AND back while the chest tips forward over the feet
    pel = v_add(v_lerp(stand_pel, sit_pel, smooth(sit)), (0.0, 0.0, -22.0 * arc))
    S["pelvis"] = pel
    # torso tilt: hunch, lean, walking, and the counterbalance while sitting down
    tilt = (0.08 * hunch + 0.30 * pose.lean + 0.04 * sit + 0.05 * walk + 0.36 * arc
            - 0.10 * laugh)
    S["tilt"] = tilt
    R = m_rot_x(-tilt)
    S["R"] = R

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["waist"] = T((0.0, -46.0, 3.0))
    S["chest"] = T((0.0, -96.0, 10.0 + 2.0 * br))
    sh_y = -140.0 + 9.0 * hunch - 2.2 * br - shake * 0.8
    sh_z = 4.0 + 14.0 * hunch
    S["sh_c"] = T((0.0, sh_y, sh_z))
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y + 13.0 + 3 * hunch, sh_z - 3.0)) for s in (-1.0, 1.0)}
    S["neck_base"] = T((0.0, sh_y - 8.0 + 4 * hunch, sh_z + 4.0 + 12.0 * hunch))
    S["hip"] = {s: v_add(pel, (s * HIP_W, 8.0, 0.0)) for s in (-1.0, 1.0)}

    nb = S["neck_base"]
    pivot = v_add(nb, m_vec(R, (0.0, -34.0 + 12.0 * hunch, 12.0 + 22.0 * hunch)))
    S["neck_top"] = pivot
    nod = pose.head_nod * 0.42 - 0.10 * hunch - 0.22 * sigh + 0.24 * laugh + 0.03 * br
    hy = pose.head_turn * 1.1
    hr = pose.head_tilt + 0.06 * laugh * math.sin(t * 9.0)
    RH = m_mul(m_rot_y(hy), m_mul(m_rot_x(nod + tilt * 0.3), m_rot_z(hr)))
    S["RH"] = RH
    hb = walk * wc.head_bob * 0.8
    S["head_c"] = v_add(pivot, v_add(m_vec(RH, (0.0, -30.0 * HS, 10.0 * HS)), (0.0, hb + shake * 0.6, 0.0)))
    S["ear"] = [v_add(S["head_c"], m_vec(RH, (s * 36.0 * HS, 4.0 * HS, -4.0 * HS))) for s in (-1.0, 1.0)]

    feet = []
    u_feet = smooth((sit - 0.55) / 0.45)   # feet stay planted until the seat takes the weight
    for s in (-1.0, 1.0):
        hip = S["hip"][s]
        fz, lift, toe, planted = wc.feet[0 if s < 0 else 1]
        stand_ank = (s * (HIP_W + 2.0), -ANKLE_H - lift * walk, fz * walk + 2.0)
        seat_ank = (s * (HIP_W + 9.0), -ANKLE_H, 66.0 + 0.28 * seat_h)
        ankle = v_lerp(stand_ank, seat_ank, u_feet)
        toe *= walk * (1.0 - smooth(sit))
        knee, ank = B.ik3(hip, ankle, THIGH, SHIN, (s * 0.15, lerp(0.15, -0.35, smooth(sit)), 1.0))
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "toe": toe, "side": s})
    S["feet"] = feet
    S["knee"] = [feet[0]["knee"], feet[1]["knee"]]
    return S


def _solve_arm(q, S, side, arm):
    sk = S["shoulders"][side]
    c = {"sit": q.sit, "knee": S["knee"], "ear": S["ear"], "head_c": S["head_c"],
         "chest": S["chest"], "hip": S["hip"], "phase": arm.phase}
    tgt, hp, hang, z = DRAGON_GESTURES.get(arm.gesture, _g_rest)(sk, side, c)
    if arm.amt < 1.0:
        t0, hp0, ha0, z0 = DRAGON_GESTURES.get(arm.prev, _g_rest)(sk, side, c)
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 14.0          # hands travel on an arc, never in a straight line
        tgt = v_add(v_lerp(t0, tgt, u), (side * arc * 0.5, -arc * 0.4, arc))
        hang = lerp(ha0, hang, u)
        if u < 0.5:
            hp = hp0
            if z0 != "auto":
                z = z0
    if arm.target is not None:
        tgt = arm.target
    if arm.hand:
        hp = arm.hand
    if arm.gesture == "rest" and q.sit < SIT_SWAP:
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"] * (1.0 - _rest_sit(q.sit))
        tgt = v_add(tgt, (0.0, -abs(sw) * 6.0, sw * 34.0 + 3.0 * math.sin(q.t * 0.9 + side)))
    if arm.gesture in ("rest", "carry_bag"):
        tgt = v_add(tgt, (0.0, S["shake"] * 0.6, 0.0))
    if arm.gesture in ("hand_to_ear", "look_at_hand"):
        pole = (side * 1.0, 0.9, -0.15)
    elif arm.gesture == "arms_crossed":
        pole = (side * 1.0, 0.6, 0.2)
    elif arm.gesture == "rest":
        pole = v_lerp((side * 0.3, 0.15, -1.0), (side * 1.0, 0.45, 0.05), _rest_sit(q.sit))
    else:
        pole = (side * 0.9, 0.8, -0.3)
    elbow, wrist = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side}


# ----------------------------------------------------------------------------------------
# limbs
# ----------------------------------------------------------------------------------------

def _arm(q, A, side, parts="all", hold=True):
    """Sleeve (+ elbow folds + cuff) and hand. parts: "all", "sleeve" or "hand"."""
    cr, proj, M = q.cr, q.proj, q.M
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    arm = A["arm"]
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    pocket = arm.gesture == "pockets" and arm.amt > 0.5
    if parts in ("all", "sleeve"):
        sleeve, out = B.tube_paths(cr, [sh, el, wr], [18.0, 14.5, 12.8], q.lw, samples=5, tension=0.7)
        pal = q.shade(sleeve, _coat_mat(q), outline=out, size=30)
        if q.detail >= 2:                               # elbow folds on the inside of the bend
            ux, uy = core.normalize((wr[0] - sh[0], wr[1] - sh[1]))
            nx, ny = -uy, ux
            bend = (el[0] - sh[0]) * (wr[1] - el[1]) - (el[1] - sh[1]) * (wr[0] - el[0])
            sg = 1.0 if bend > 0 else -1.0
            lines = []
            for off in (0.15, 0.55):
                lines.append([(el[0] + nx * 14.5 * off * sg - ux * 7, el[1] + ny * 14.5 * off * sg - uy * 7),
                              (el[0] + nx * 14.5 * (off + 0.55) * sg + ux * 3, el[1] + ny * 14.5 * (off + 0.55) * sg + uy * 3)])
            B.detail_lines(cr, lines, q.lw * 0.8, pal.line, 0.5)
        if pocket:
            # the forearm disappears into the pocket: a flap of coat over the wrist
            cx_, cy_ = wr[0] - fdx * 4.0, wr[1] - fdy * 4.0
            flap, fo = B.ellipse_paths(cr, cx_, cy_, 13.0, 18.0, q.lw, ang)
            q.shade(flap, _coat_mat(q), outline=fo, size=20, rim=0.3)
            B.detail_lines(cr, [[(cx_ - 15, cy_ - 6), (cx_, cy_ - 9), (cx_ + 15, cy_ - 6)]], q.lw * 0.9, pal.line, 0.7)
        else:
            cuff, cout = B.ellipse_paths(cr, wr[0] - fdx * 3.0, wr[1] - fdy * 3.0, 8.5, 15.0, q.lw, ang)
            q.shade(cuff, M["lining"], outline=cout, size=14, rim=0.5)
    if parts == "sleeve" or pocket:
        return B.HandFrame(wr[0], wr[1], ang, 1.0, [], wr, False)
    hp = A["hand"]
    hang = ang + A["hang"] * (1 if side < 0 else -1) * (1 if q.yaw >= 0 else -1)
    flip = (side > 0) == (q.yaw >= 0)
    show_palm = hp in ("open", "offer") and arm.gesture in ("hand_out_offer", "hug", "wave")
    return B.hand(cr, wr[0] + fdx * 5.0, wr[1] + fdy * 5.0, hang, HAND_LEN, hp, M["scales"], q.light, q.lw,
                  flip=flip, claw=DRAGON_COLORS["claw"], claw_len=0.08, pad=DRAGON_COLORS["belly"],
                  show_palm=show_palm, hold=arm.hold if hold else None, stamp=arm.stamp, finger_w=1.05,
                  detail=q.detail, hold_behind=arm.gesture == "hand_to_ear")


def _two_hand_prop(q, A0, A1, draw):
    """A prop held in both hands (the open coloring book): sleeves, then the prop between the
    grips, then both hands over it. The prop callback's frame is at the midpoint, upright."""
    _arm(q, A0, A0["side"], parts="sleeve")
    _arm(q, A1, A1["side"], parts="sleeve")
    g = []
    for A in (A0, A1):
        el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
        fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
        g.append((wr[0] + fdx * 30.0, wr[1] + fdy * 30.0))
    mx, my = (g[0][0] + g[1][0]) / 2, (g[0][1] + g[1][1]) / 2
    cr = q.cr
    cr.save()
    cr.translate(mx, my)
    draw(cr, B.HandFrame(0.0, 0.0, 0.0, 1.0, [], (0.0, 0.0), False))
    cr.restore()
    return _arm(q, A0, A0["side"], parts="hand", hold=False), _arm(q, A1, A1["side"], parts="hand", hold=False)


def _leg(q, side):
    """Shin + foot (+ toes) as ONE union: a single outline and shading pass."""
    cr, proj, M = q.cr, q.proj, q.M
    lw = q.lw
    f = q.S["feet"][0 if side < 0 else 1]
    knee, ank = proj.xy(f["knee"]), proj.xy(f["ankle"])
    if q.sit >= SIT_SWAP:                   # the thigh is under the lap
        spine, radii = [knee, ank], [13.5, 8.5]
    else:
        spine, radii = [proj.xy(f["hip"]), knee, ank], [18.0, 11.0, 8.2]
    shin, shin_o = B.tube_outline(spine, radii, 4, 0.8, (0.0, lw))
    a = f["ankle"]
    toe = f["toe"]
    base = (a[0], a[1] + ANKLE_H, a[2])
    c, sn = math.cos(toe), math.sin(toe)

    def P(dx, dy, dz):
        return proj.xy((base[0] + dx, base[1] + dy * c - dz * sn, base[2] + dy * sn + dz * c))

    pts = []
    for k in range(8):
        ang = math.tau * k / 8
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append(P(ca * 8.0, -ANKLE_H + 4 + sa * 2.5, sa * 6.0))       # ankle
        pts.append(P(ca * 6.5, -6.5 + sa * 6.0, -7.0))                   # heel
        pts.append(P(ca * 11.0, -6.0 + sa * 5.5, 12.0))                  # ball of the foot
    pts += [P(0.0, -13.0, 4.0), P(-9.0, -11.0, 6.0), P(9.0, -11.0, 6.0)]
    hull = core.convex_hull(pts)
    toes = []
    for tx_, tz, tr in ((-8.0, 25.0, 5.4), (0.0, 30.0, 6.0), (8.0, 25.0, 5.4)):
        toes.append((P(tx_ * 0.55, -6.0, 11.0), P(tx_, -tr * 0.95, tz), tr, tx_, tz))
    # outline (dilated pieces) then the union
    cr.new_path()
    core.smooth_closed(cr, shin_o, 0.9)
    core.smooth_closed(cr, B.offset_closed(hull, lw), 0.9)
    for a0, a1, tr, _x, _z in toes:
        core.capsule(cr, a0[0], a0[1], tr * 1.05 + lw, a1[0], a1[1], tr + lw)
    pal = q.P(M["scales"])
    core.src(cr, pal.line)
    cr.fill()
    core.smooth_closed(cr, shin, 0.9)
    core.smooth_closed(cr, hull, 0.9)
    for a0, a1, tr, _x, _z in toes:
        core.capsule(cr, a0[0], a0[1], tr * 1.05, a1[0], a1[1], tr)
    q.shade(Path(cr), M["scales"], outline=False, size=21, rim=0.5)
    cp = q.P(M["claw"])
    cr.new_path()
    for _a0, _a1, tr, tx_, tz in toes:
        c0 = P(tx_, -tr * 0.55, tz + tr * 0.55)
        c1 = P(tx_, -0.4, tz + tr * 0.55 + 6.5)
        dx, dy = c1[0] - c0[0], c1[1] - c0[1]
        L = math.hypot(dx, dy)
        if L < 2.0:
            core.ellipse(cr, c0[0], c0[1] + 2.2, 3.0, 2.0)
            continue
        w = 3.3
        nx, ny = -dy / L * w, dx / L * w
        cr.move_to(c0[0] + nx, c0[1] + ny)
        cr.curve_to(c1[0] + nx * 0.4, c1[1] + ny * 0.4, c1[0], c1[1] + 1.2, c1[0] + dx / L * 1.2, c1[1] + dy / L * 1.2 + 1.8)
        cr.line_to(c0[0] - nx, c0[1] - ny)
        cr.close_path()
    B.flat(cr, Path(cr), cp.lit, lw * 0.6, cp.line)


def _tail_spine(q):
    """Tail control points in body space (base -> tip), blended continuously stand -> sit."""
    pose = q.pose
    pel = q.S["pelvis"]
    pts = [v_add(pel, (0.0, 30.0, -24.0)), (3.0, -140.0, -46.0), (12.0, -64.0, -74.0), (28.0, -18.0, -108.0),
           (50.0, -10.0, -150.0), (68.0, -12.0, -190.0), (78.0, -30.0, -220.0)]
    d = clamp(pose.tail_drag)
    if d > 0:
        flat_ = [pts[0], pts[1], (8.0, -46.0, -78.0), (16.0, -10.0, -118.0), (24.0, -8.0, -166.0),
                 (30.0, -8.0, -212.0), (34.0, -12.0, -254.0)]
        pts = [v_lerp(a, b, d) for a, b in zip(pts, flat_)]
    if q.sit <= 0.0:
        return pts
    base = v_add(pel, (0.0, 22.0, -26.0))
    if pose.tail_front:
        # off the side of the seat (his left), round the outside of that leg and curled in
        # front of the feet, like a cat's
        seat = [base, v_add(base, (34.0, 30.0, -16.0)), (70.0, -14.0, -40.0), (92.0, -10.0, 16.0),
                (84.0, -10.0, 84.0), (46.0, -10.0, 136.0), (-6.0, -16.0, 150.0)]
    else:
        # off the side of the seat and out along the ground behind, toward whichever side
        # the camera sees best (never straight back: head-on that foreshortens into a post)
        sg = clamp(0.6 * math.cos(q.yaw) - 1.3 * math.sin(q.yaw), -1.0, 1.0)
        seat = [base, v_add(base, (sg * 34.0, 30.0, -16.0)), (sg * 66.0, -14.0, -56.0), (sg * 100.0, -10.0, -86.0),
                (sg * 134.0, -10.0, -100.0), (sg * 162.0, -14.0, -98.0), (sg * 180.0, -32.0, -88.0)]
    k = smooth(q.sit)
    return [v_lerp(a, b, k) for a, b in zip(pts, seat)]


def _tail(q, front=None):
    """The tail. front=None draws all of it (behind the body); front=<depth> redraws only the
    part nearer the camera than that depth (e.g. curled in front of the feet), clipped to a
    band along the tail, so the second pass matches the first pixel for pixel."""
    cr, proj, M, pose, t = q.cr, q.proj, q.M, q.pose, q.t
    swing = pose.tail_swing + 0.22 * B.sway(t * 0.6, 0.5, pose.seed + 3)
    curl = clamp(pose.tail_curl + 0.12 * math.sin(t * 0.7 + 1.3))
    wav = B.chain(t, 7, freq=0.3, delay=0.2, amp=0.5, seed=pose.seed + 11, grow=2.4)
    pts = _tail_spine(q)
    out, depth = [], []
    n = len(pts)
    acc = 0.0
    for i, p in enumerate(pts):
        u = i / (n - 1)
        if i:
            acc += wav[min(i, len(wav) - 1)]
        dx = (swing * 70.0 * u * u + acc * 60.0 * u) * (1.0 - 0.6 * q.sit)   # calmer when seated
        lift = -curl * 28.0 * smooth((u - 0.62) / 0.38) * (0.35 if pose.tail_front else 1.0)
        p3 = (p[0] + dx, p[1] + lift, p[2])
        out.append(proj.xy(p3))
        depth.append(proj.depth(p3))
    radii = [19.0, 16.0, 13.5, 11.0, 8.5, 6.0, 3.8]
    sp = core.spline(out, n=4, tension=0.8)
    if front is not None:
        # the band: dense spine samples whose interpolated depth exceeds `front`, widened
        ns = len(sp)
        j0 = None
        for j in range(ns):
            f = j / (ns - 1) * (n - 1)
            k = min(int(f), n - 2)
            if lerp(depth[k], depth[k + 1], f - k) > front:
                j0 = j
                break
        if j0 is None or j0 > ns - 2:
            return
        band = sp[j0:]
        left, right = [], []
        for j, pt in enumerate(band):
            a, b = band[min(j + 1, len(band) - 1)], band[max(j - 1, 0)]
            tx, ty = core.normalize((a[0] - b[0], a[1] - b[1]))
            r = radii[0] + (radii[-1] - radii[0]) * (j0 + j) / (ns - 1) + q.lw + 16.0
            left.append((pt[0] - ty * r, pt[1] + tx * r))
            right.append((pt[0] + ty * r, pt[1] - tx * r))
        cr.save()
        cr.new_path()
        core.polygon(cr, left + right[::-1])
        cr.clip()
    if q.detail >= 1:                       # dorsal spines (their bases hide under the tail)
        cr.new_path()
        ns = len(sp)
        for k in range(3, ns - 3, 3):
            p0, p1 = sp[k], sp[k + 1]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            nx, ny = uy, -ux
            if ny > 0:
                nx, ny = -nx, -ny
            u = k / ns
            rr = radii[0] + (radii[-1] - radii[0]) * u
            h = 10.0 * (1.0 - u) + 3.5
            bx, by = p0[0] + nx * rr * 0.7, p0[1] + ny * rr * 0.7
            cr.move_to(bx - ux * h * 0.8, by - uy * h * 0.8)
            cr.curve_to(bx + nx * h * 0.5 - ux * h * 0.2, by + ny * h * 0.5 - uy * h * 0.2,
                        bx + nx * h + ux * h * 0.1, by + ny * h + uy * h * 0.1,
                        bx + nx * h * 1.05 + ux * h * 0.55, by + ny * h * 1.05 + uy * h * 0.55)
            cr.line_to(bx + ux * h * 0.8, by + uy * h * 0.8)
            cr.close_path()
        spines = Path(cr)
        B.outline_under(cr, spines, q.lw, q.P(M["scales_dk"]).line)
        q.shade(spines, M["scales_dk"], outline=False, rim=0.0, size=7, shadow=0.6)
    tail, tout = B.tube_paths(cr, out, radii, q.lw, samples=4, tension=0.85)
    q.shade(tail, M["scales"], outline=tout, size=24)
    if q.detail >= 1:                       # belly-plate stripe along the underside
        cr.save()
        tail.add(cr)
        cr.clip()
        ns = len(sp)
        under = [(sp[i][0], sp[i][1] + (radii[0] + (radii[-1] - radii[0]) * i / (ns - 1)) * 1.02) for i in range(ns)]
        bp = q.P(M["belly"])
        cr.new_path()
        core.tapered(cr, under, 10.0, 2.5)
        core.src(cr, core.mix(bp.shadow, bp.lit, 0.3))
        cr.fill()
        cr.restore()
    tip, prev = out[-1], sp[-3]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    ca, sa = math.cos(a), math.sin(a)
    spade = [(tip[0] + x * ca - y * sa, tip[1] + x * sa + y * ca)
             for x, y in ((-5, 0), (5, -9), (18, -7), (27, 0), (18, 7), (5, 9))]
    sh, so = B.smooth_paths(cr, spade, q.lw, 0.9)
    q.shade(sh, M["scales_dk"], outline=so, size=14)
    if front is not None:
        cr.restore()


def _wing(q, side):
    cr, proj, M, pose, t, S = q.cr, q.proj, q.M, q.pose, q.t, q.S
    w = clamp(pose.wings + 1.3 * pose.laugh - 0.4 * pose.sigh, -1.0, 1.0)
    lift = (w + 1.0) / 2.0                  # 0 drooped .. 1 lifted
    flutter = 0.05 * math.sin(t * 2.3 + side) + 0.1 * math.sin(t * 13.0) * pose.laugh
    T = S["T"]
    h = S["hunch"]
    root = T((side * 22.0, -121.0 + 8.0 * h, -24.0 - 8.0 * h))
    wrist = v_add(root, (side * (22.0 + 22.0 * lift), -10.0 - 72.0 * lift + flutter * 60, -16.0 - 14.0 * lift))
    tips = []
    for k in range(3):
        ang = lerp(0.12 + 0.24 * k, -1.15 + 0.5 * k, lift) + flutter
        L = 80.0 - 15.0 * k
        tips.append(v_add(wrist, (side * ((5.0 + 9.0 * k) * (0.4 + lift) + math.sin(ang) * L * 0.35), math.cos(ang) * L,
                                  -12.0 - 12.0 * k - 18.0 * lift)))
    pr, pw = proj.xy(root), proj.xy(wrist)
    t0, t1, t2 = (proj.xy(p) for p in tips)
    back_pt = proj.xy(v_add(root, (side * 2.0, 44.0, 8.0)))
    cr.new_path()
    cr.move_to(*pr)
    cr.line_to(*pw)
    cr.line_to(*t0)

    def scallop(a, b):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        cx_, cy_ = lerp(mx, pw[0], 0.32), lerp(my, pw[1], 0.32)
        cr.curve_to(lerp(a[0], cx_, 0.6), lerp(a[1], cy_, 0.6), lerp(b[0], cx_, 0.6), lerp(b[1], cy_, 0.6), b[0], b[1])

    scallop(t0, t1)
    scallop(t1, t2)
    cr.curve_to(lerp(t2[0], back_pt[0], 0.4), lerp(t2[1], back_pt[1], 0.2), back_pt[0], back_pt[1] - 10, back_pt[0], back_pt[1])
    cr.close_path()
    q.shade(Path(cr), M["membrane"], size=40, rim=0.8)
    # bones (arm + fingers) as one union with a dilated outline
    lw = q.lw
    bones = [([pr, ((pr[0] + pw[0]) / 2, (pr[1] + pw[1]) / 2 - 2.0), pw], 9.0, 6.5)]
    bones += [([pw, ((pw[0] + tp[0]) / 2, (pw[1] + tp[1]) / 2), tp], 5.2, 1.4) for tp in (t0, t1, t2)]
    sp_ = q.P(M["scales"])
    cr.new_path()
    for b_pts, w0, w1 in bones:
        core.tapered(cr, b_pts, w0 + 2 * lw * 0.8, w1 + 2 * lw * 0.8)
    core.src(cr, sp_.line)
    cr.fill()
    for b_pts, w0, w1 in bones:
        core.tapered(cr, b_pts, w0, w1)
    core.src(cr, core.mix(sp_.lit, sp_.shadow, 0.35))
    cr.fill()
    cp = q.P(M["claw"])
    cr.new_path()
    sx = side if q.yaw >= 0 else -side
    cr.move_to(pw[0] - 4, pw[1] + 1)
    cr.curve_to(pw[0] - 3, pw[1] - 7, pw[0] + sx * 3, pw[1] - 11, pw[0] + sx * 6, pw[1] - 12)
    cr.line_to(pw[0] + 4, pw[1])
    cr.close_path()
    B.flat(cr, Path(cr), cp.lit, q.lw * 0.6, cp.line)


# ----------------------------------------------------------------------------------------
# coat
# ----------------------------------------------------------------------------------------

def _coat_rings(q):
    """Cross-sections (center, half-width a, half-depth c) of the coat, top -> hem."""
    S = q.S
    T = S["T"]
    h = S["hunch"]
    br = S["br"]
    pel = S["pelvis"]
    rings = [
        (T((0.0, -130.0 + 9 * h, 6.0 + 13 * h)), 40.0, 25.0),             # 0 shoulder top (sloped)
        (T((0.0, -106.0 + 5 * h, 1.0 - 4 * h)), 54.0 + br, 34.0 + 5 * h),   # 1 armpits / rounded upper back
        (T((0.0, -76.0, 5.0)), 51.0 + 1.5 * br, 35.0),                     # 2 chest
        (T((0.0, -40.0, 4.0)), 43.0, 29.0),                                # 3 waist
        (v_add(pel, (0.0, 0.0, 1.0)), 52.0, 33.0),                         # 4 hips
    ]
    if q.sit < SIT_SWAP:
        walk = S["walk"]
        sw = walk * math.sin(math.tau * S["wc"].phase * 2)
        hem_y = -72.0
        c5, a5 = (sw * 2.0, (pel[1] + hem_y) / 2 + 6, -3.0 - walk * 5.0), 69.0        # 5 thigh
        c6, a6 = (sw * 4.0, hem_y, -6.0 - walk * 12.0), 94.0 + 4 * walk                 # 6 hem (A-line)
        k = smooth(q.sit / SIT_SWAP)
        if k > 0.0:
            # sitting down: the skirt swings forward with the thighs and rides up over the knees
            kn = v_lerp(S["knee"][0], S["knee"][1], 0.5)
            c5 = v_lerp(c5, v_add(v_lerp(pel, kn, 0.5), (0.0, 12.0, -6.0)), k)
            c6 = v_lerp(c6, v_add(kn, (0.0, 42.0, -10.0)), k)
            a5, a6 = lerp(a5, 64.0, k), lerp(a6, 80.0, k)
        rings += [(c5, a5, 43.0), (c6, a6, 56.0)]
    return rings


def _coat(q):
    cr, proj, S, yaw = q.cr, q.proj, q.S, q.yaw
    rings = _coat_rings(q)
    left, right = [], []
    for (c, a, cz) in rings:
        x, y, hw = proj.ellipse(c, a, cz)
        left.append((x - hw, y))
        right.append((x + hw, y))
    c0, a0, cz0 = rings[0]
    x0, y0, hw0 = proj.ellipse(c0, a0, cz0)
    nb = proj.xy(S["neck_base"])
    top = [(x0 - hw0 * 0.9, y0 - 6.0), (lerp(x0 - hw0, nb[0], 0.6), y0 - 15.0), (nb[0] - 16.0, nb[1] - 2.0),
           (nb[0] + 16.0, nb[1] - 2.0), (lerp(x0 + hw0, nb[0], 0.6), y0 - 15.0), (x0 + hw0 * 0.9, y0 - 6.0)]
    hem = []
    if q.sit < SIT_SWAP:
        cH, aH, czH = rings[-1]
        ring = [proj((cH[0] + math.sin(math.tau * i / 24) * aH, cH[1], cH[2] + math.cos(math.tau * i / 24) * czH))
                for i in range(24)]
        xL, xR = left[-1][0], right[-1][0]
        for i in range(1, 8):
            xx = lerp(xL, xR, i / 8)
            best = None
            for k in range(24):           # lowest crossing of the hem ring = nearest edge
                pa, pb = ring[k], ring[(k + 1) % 24]
                if (pa[0] - xx) * (pb[0] - xx) <= 0 and pa[0] != pb[0]:
                    yy = pa[1] + (pb[1] - pa[1]) * (xx - pa[0]) / (pb[0] - pa[0])
                    best = yy if best is None else max(best, yy)
            if best is not None:
                hem.append((xx, best + 1.6 * math.sin(i * 2.1 + q.t * 1.3) * (0.4 + S["walk"])))
    else:
        cH, aH, czH = rings[-1]
        x, y, hw = proj.ellipse(cH, aH, czH)
        hem = [(x - hw * 0.5, y + 10), (x, y + 12), (x + hw * 0.5, y + 10)]
    pts = left + hem + right[::-1] + top[::-1]
    coat, cout = B.smooth_paths(cr, pts, q.lw, 0.8)
    pal = q.shade(coat, _coat_mat(q), outline=cout, size=110, shadow=0.55)
    if math.cos(yaw) > -0.15:
        _coat_front(q, rings, coat)
    if q.detail >= 1 and q.sit < SIT_SWAP:
        _coat_folds(q, rings, coat, pal)
    return coat


def _coat_folds(q, rings, coat, pal):
    cr, proj = q.cr, q.proj
    cH, aH, czH = rings[-1]
    cW, aW, czW = rings[4]
    cr.save()
    coat.add(cr)
    cr.clip()
    lines = []
    for phi in (-1.25, -0.5, 0.42, 1.18):
        if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.12:
            continue
        A2 = proj.xy((cW[0] + math.sin(phi) * aW * 0.92, cW[1] + 22.0, cW[2] + math.cos(phi) * czW * 0.92))
        B2 = proj.xy((cH[0] + math.sin(phi * 1.06) * aH * 0.96, cH[1] - 2.0, cH[2] + math.cos(phi * 1.06) * czH * 0.96))
        lines.append([A2, ((A2[0] + B2[0]) / 2 + 2.5 * math.sin(phi * 3), (A2[1] + B2[1]) / 2), B2])
    if lines:
        B.detail_lines(cr, lines, q.lw * 1.1, pal.line, 0.45, taper=(0.05, 0.8, 1.0))
    # the front panel edge: from the waist closure down to the hem, slightly off-center
    if proj.depth((0.0, 0.0, 1.0)) > 0.1:
        edge = []
        for k, phi in ((3, 0.03), (4, 0.08), (5, 0.13), (6, 0.17)):
            cc, aa, zz = rings[k]
            edge.append(proj.xy((cc[0] + math.sin(phi) * aa, cc[1] + (6.0 if k == 3 else 0.0), cc[2] + math.cos(phi) * zz)))
        edge[-1] = (edge[-1][0], edge[-1][1] + 4.0)
        B.detail_lines(cr, [edge], q.lw * 1.0, pal.line, 0.85, taper=(0.4, 1.0, 1.0))
        B.detail_lines(cr, [[(x + 2.2, y) for x, y in edge]], q.lw * 0.6, core.tint(pal.lit, 0.25), 0.5, taper=(0.1, 1.0, 0.8))
    # pocket flaps on the hips
    if q.detail >= 2:
        c4, a4, cz4 = rings[4]
        c5, a5, cz5 = rings[5]
        cc = v_lerp(c4, c5, 0.42)
        aa, zz = lerp(a4, a5, 0.42), lerp(cz4, cz5, 0.42)
        for phi in (-0.95, 0.95):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.2:
                continue
            pts = [proj.xy((cc[0] + math.sin(phi + (k - 2) * 0.13) * aa * 1.01, cc[1], cc[2] + math.cos(phi + (k - 2) * 0.13) * zz * 1.01))
                   for k in range(5)]
            lo = [(p[0], p[1] + 8.0) for p in pts[1:-1]]
            B.detail_lines(cr, [pts], q.lw * 0.9, pal.line, 0.6, taper=(0.6, 1.0, 0.6))
            B.detail_lines(cr, [[pts[0], lo[0], lo[-1], pts[-1]]], q.lw * 0.7, pal.line, 0.35)
    cr.restore()


def _coat_front(q, rings, coat):
    cr, proj, M, S = q.cr, q.proj, q.M, q.S
    widths = [0.66, 0.5, 0.27, 0.0]
    edgeL, edgeR = [], []
    for (c, a, cz), wv in zip(rings[:4], widths):
        for sgn, lst in ((-1, edgeL), (1, edgeR)):
            lst.append(proj.xy((c[0] + math.sin(sgn * wv) * a * 0.98, c[1], c[2] + math.cos(sgn * wv) * cz * 0.98)))
    nb = proj.xy(S["neck_base"])
    edgeL[0] = (lerp(edgeL[0][0], nb[0] - 12, 0.4), edgeL[0][1] - 6)
    edgeR[0] = (lerp(edgeR[0][0], nb[0] + 12, 0.4), edgeR[0][1] - 6)
    cr.save()
    coat.add(cr)
    cr.clip()
    cr.new_path()
    core.smooth_open(cr, edgeL)
    core.smooth_open(cr, edgeR[::-1], move=False)
    cr.close_path()
    opening = Path(cr)
    bp = q.shade(opening, M["belly"], size=40, rim=0.0, outline=False)
    if q.detail >= 1:
        cr.save()
        opening.add(cr)
        cr.clip()
        lines = []
        for k in range(1, 6):
            u = k / 6.0
            i = min(2, int(u * 3))
            f = u * 3 - i
            a = core.lerp_pt(edgeL[i], edgeL[i + 1], f)
            b = core.lerp_pt(edgeR[i], edgeR[i + 1], f)
            lines.append([(a[0] - 4, a[1]), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 4.0), (b[0] + 4, b[1])])
        B.detail_lines(cr, lines, q.lw * 0.9, bp.line, 0.5, taper=(0.5, 1.0, 0.5))
        cr.restore()
        B.occlusion(cr, nb[0], nb[1] + 18, 34, 22, bp.deep, 0.5)        # shade under the scarf
    cp = q.P(_coat_mat(q))
    if q.detail >= 1:                                                     # lapel facings
        cr.new_path()
        for edge, sgn in ((edgeL, -1), (edgeR, 1)):
            core.tapered(cr, [(p[0] + sgn * 3.5 * (1 - i / 3.5), p[1] + 0.5) for i, p in enumerate(edge)], 8.0, 1.0)
        q.shade(Path(cr), M["lining"], rim=0.3, size=8, outline=False)
    B.detail_lines(cr, [edgeL, edgeR], q.lw * 1.05, cp.line, 0.95, taper=(0.6, 1.0, 0.3))
    cr.restore()
    # brass buttons at the closure
    c3, a3, cz3 = rings[3]
    c2, a2, cz2 = rings[2]
    bts = []
    for cc, zz in ((v_add(c3, (0.0, 5.0, 0.0)), cz3), (v_lerp(c2, c3, 0.55), lerp(cz2, cz3, 0.55))):
        p = proj((cc[0], cc[1], cc[2] + zz))
        if p[2] >= 0:
            bts.append(p)
    if bts:
        lwb = q.lw * 0.7
        cr.new_path()
        for p in bts:
            core.circle(cr, p[0], p[1], 4.4 + lwb)
        core.src(cr, q.P(M["button"]).line)
        cr.fill()
        for p in bts:
            core.circle(cr, p[0], p[1], 4.4)
        q.shade(Path(cr), M["button"], lw=lwb, outline=False, size=8, rim=0.6)
        for p in bts:
            B.sheen(cr, p[0] - 1.3, p[1] - 1.5, 1.8, 1.4, alpha=0.8)


def _blob(proj, c, rx, ry, rz, n=10):
    """Silhouette points of an ellipsoid (three orthogonal rings, projected) for hulls."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        pts.append(proj.xy((c[0] + ca * rx, c[1] + sa * ry, c[2])))
        pts.append(proj.xy((c[0] + ca * rx, c[1], c[2] + sa * rz)))
        pts.append(proj.xy((c[0], c[1] + ca * ry, c[2] + sa * rz)))
    return pts


def _lap(q):
    """Seated: the coat skirt over the thighs. ONE union (one outline, one shading pass) of five
    convex pieces -- both thighs, the panel hanging off each knee, and the cloth sagging between
    the knees -- so the silhouette shows two knees, the panels falling off them and a soft U
    between them. Ink then carries the cloth: knee caps, the hammock folds, the panel folds."""
    cr, proj, S, lw = q.cr, q.proj, q.S, q.lw
    cm = _coat_mat(q)
    pal = q.P(cm)
    pel = S["pelvis"]
    near = -1.0 if q.yaw >= 0 else 1.0
    sway = 1.6 * math.sin(q.t * 1.1 + 0.4)
    kns = {-1.0: S["knee"][0], 1.0: S["knee"][1]}
    hips = {s: v_add(pel, (s * 25.0, 0.0, -4.0)) for s in (-1.0, 1.0)}
    km = v_lerp(kns[-1.0], kns[1.0], 0.5)
    DROP = 56.0                                   # how far the panels hang below the knees

    hulls = []
    for s in (-near, near):
        kn = kns[s]
        # thigh: hip to knee
        hulls.append(core.convex_hull(_blob(proj, hips[s], 27.0, 24.0, 25.0)
                                      + _blob(proj, v_add(kn, (0.0, -1.0, 2.0)), 21.0, 20.0, 20.0)))
        # the panel hanging off the knee, flaring toward its hem, longer on the outer side
        pts = _blob(proj, v_add(kn, (0.0, 6.0, -2.0)), 21.0, 12.0, 19.0, 8)
        for i in range(12):
            a = math.tau * i / 12
            ox = math.cos(a)                      # +1 = outer side of this leg (s * x)
            pts.append(proj.xy(v_add(kn, (s * ox * 26.0 + s * 4.0 + sway, DROP + 7.0 * ox + 2.0 * math.sin(a * 2.0),
                                          4.0 + math.sin(a) * 23.0))))
        hulls.append(core.convex_hull(pts))
    # the cloth between the knees: a hammock whose lowest point sags well above the panels' hems
    pts = []
    for s in (-1.0, 1.0):
        kn = kns[s]
        pts += [proj.xy(v_add(kn, (-s * 6.0, -18.0, -12.0))), proj.xy(v_add(kn, (-s * 10.0, 12.0, 10.0))),
                proj.xy(v_add(hips[s], (-s * 14.0, -18.0, 12.0)))]
    for u in (-0.5, -0.2, 0.2, 0.5):
        pts.append(proj.xy(v_add(km, (u * 28.0 + sway * 0.6, 26.0 - 12.0 * abs(u), 12.0))))
    hulls.append(core.convex_hull(pts))

    cr.new_path()
    for h in hulls:
        core.smooth_closed(cr, B.offset_closed(h, lw), 0.85)
    core.src(cr, pal.line)
    cr.fill()
    for h in hulls:
        core.smooth_closed(cr, h, 0.85)
    lap = Path(cr)
    q.shade(lap, cm, outline=False, size=52, shadow=0.7, rim=0.8)
    if q.detail < 1:
        return
    cr.save()
    lap.add(cr)
    cr.clip()
    lines, soft = [], []
    # knee caps: the taut cloth over each knee
    for s in (-1.0, 1.0):
        kn = kns[s]
        if proj.depth((s, 0.0, 0.0)) < -0.7:      # far knee seen edge-on: skip
            continue
        lines.append([proj.xy(v_add(kn, (s * 19.0, 2.0, 6.0))), proj.xy(v_add(kn, (s * 8.0, -8.0, 17.0))),
                      proj.xy(v_add(kn, (-s * 9.0, -7.0, 16.0)))])
        # a fold down the hanging panel
        a = proj.xy(v_add(kn, (s * 4.0, 20.0, 21.0)))
        b = proj.xy(v_add(kn, (s * 6.0 + sway, DROP, 25.0)))
        soft.append([a, ((a[0] + b[0]) / 2 + 1.5, (a[1] + b[1]) / 2), b])
    # hammock folds hanging between the knees
    for dy in (2.0, 14.0):
        soft.append([proj.xy(v_add(kns[-1.0], (10.0, dy - 14.0, 12.0))),
                     proj.xy(v_add(km, (sway * 0.6, dy + 8.0, 14.0))),
                     proj.xy(v_add(kns[1.0], (-10.0, dy - 14.0, 12.0)))])
    # tension folds from the hip crease toward each knee (top of the thighs)
    for s in (-1.0, 1.0):
        a = proj.xy(v_add(hips[s], (-s * 8.0, -18.0, 18.0)))
        b = proj.xy(v_add(v_lerp(hips[s], kns[s], 0.55), (-s * 4.0, -20.0, 0.0)))
        soft.append([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 2.0), b])
    # the front panels part below the waist button: an inverted V of shadowed lining
    if proj.depth((0.0, 0.0, 1.0)) > 0.25:
        top = proj.xy(v_add(pel, (0.0, -30.0, 30.0)))
        legs = [proj.xy(v_add(kns[s], (-s * 9.0, 14.0, 14.0))) for s in (-1.0, 1.0)]
        mid = proj.xy(v_add(km, (sway * 0.6, 20.0, 14.0)))
        cr.new_path()
        cr.move_to(*top)
        cr.curve_to(lerp(top[0], legs[0][0], 0.5) + 2.0, lerp(top[1], legs[0][1], 0.45), legs[0][0], legs[0][1] - 12.0, *legs[0])
        cr.curve_to(lerp(legs[0][0], mid[0], 0.5), mid[1], lerp(mid[0], legs[1][0], 0.5), mid[1], *legs[1])
        cr.curve_to(legs[1][0], legs[1][1] - 12.0, lerp(top[0], legs[1][0], 0.5) - 2.0, lerp(top[1], legs[1][1], 0.45), *top)
        cr.close_path()
        lp = q.P(q.M["lining"])
        core.src(cr, core.mix(lp.shadow, pal.deep, 0.45))
        cr.fill()
        lines.append([top, (lerp(top[0], legs[0][0], 0.5) + 2.0, lerp(top[1], legs[0][1], 0.45)), legs[0]])
        lines.append([top, (lerp(top[0], legs[1][0], 0.5) - 2.0, lerp(top[1], legs[1][1], 0.45)), legs[1]])
    B.detail_lines(cr, lines, lw * 1.0, pal.line, 0.7, taper=(0.2, 1.0, 0.3))
    B.detail_lines(cr, soft, lw * 0.9, pal.line, 0.42, taper=(0.1, 1.0, 0.2))
    # the near thigh's upper contour where it crosses the far one (3/4 views)
    if abs(q.yaw) > 0.3:
        kn = kns[near]
        cont = [proj.xy(v_add(hips[near], (0.0, -22.0, 8.0))), proj.xy(v_add(v_lerp(hips[near], kn, 0.5), (-near * 4.0, -23.0, 0.0))),
                proj.xy(v_add(kn, (-near * 10.0, -19.0, 4.0)))]
        B.detail_lines(cr, [cont], lw * 1.0, pal.line, 0.6, taper=(0.1, 1.0, 0.6))
    cr.restore()


def _coat_back_flap(q):
    """Seated: the coat tail hanging behind the seat (behind the body)."""
    pel = q.S["pelvis"]
    pts = []
    for (dy, rx, dz) in ((0.0, 50.0, -16.0), (44.0, 56.0, -30.0)):
        for i in range(10):
            a = math.tau * i / 10
            pts.append(q.proj.xy((math.sin(a) * rx, pel[1] + dy, pel[2] + dz + math.cos(a) * 14.0)))
    sh, so, _ = q.hull(pts)
    q.shade(sh, _coat_mat(q), outline=so, size=50, shadow=0.8, rim=0.5)


def _collar(q):
    """Turned-up coat collar standing behind the scarf."""
    nb = q.S["neck_base"]
    R = q.S["R"]
    pts = []
    for i in range(12):
        a = math.tau * i / 12
        for dy in (6.0, -22.0):
            pts.append(q.proj.xy(v_add(nb, m_vec(R, (math.sin(a) * 30.0, dy + (4.0 if math.cos(a) > 0 else 0.0), math.cos(a) * 24.0 - 4.0)))))
    sh, so, _ = q.hull(pts)
    q.shade(sh, _coat_mat(q), outline=so, size=30, rim=0.6)


def _neck(q):
    proj, S = q.proj, q.S
    nb, nt, hc = proj.xy(S["neck_base"]), proj.xy(S["neck_top"]), proj.xy(S["head_c"])
    sh, so = B.tube_paths(q.cr, [nb, nt, ((nt[0] + hc[0]) / 2, (nt[1] + hc[1]) / 2)], [22.0, 19.0, 18.0], q.lw, samples=4)
    q.shade(sh, q.M["scales"], outline=so, size=36, rim=0.5)


# ----------------------------------------------------------------------------------------
# scarf
# ----------------------------------------------------------------------------------------

def _knit_lines(q, spine, width):
    """Rib lines along a scarf strip (+ faint stitch rows at full detail): the knit texture."""
    if q.detail < 1:
        return
    cr = q.cr
    p = q.P(_scarf_mat(q))
    sp = core.spline(spine, n=4)
    lines = []
    for off in (-0.27, 0.0, 0.27):
        line = []
        for i in range(len(sp)):
            j, k = min(i + 1, len(sp) - 1), max(i - 1, 0)
            dx, dy = sp[j][0] - sp[k][0], sp[j][1] - sp[k][1]
            L = math.hypot(dx, dy) or 1.0
            line.append((sp[i][0] - dy / L * width * off, sp[i][1] + dx / L * width * off))
        lines.append(line)
    B.detail_lines(cr, lines, q.lw * 0.7, p.line, 0.36, taper=(0.4, 1.0, 0.4))
    if q.detail >= 2:
        cr.new_path()
        for i in range(1, len(sp) - 1, 2):
            dx, dy = sp[i + 1][0] - sp[i - 1][0], sp[i + 1][1] - sp[i - 1][1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            for s in (-1, 1):
                cr.move_to(sp[i][0] + nx * width * 0.42 * s, sp[i][1] + ny * width * 0.42 * s)
                cr.line_to(sp[i][0] + nx * width * 0.1 * s + dx / L * 3, sp[i][1] + ny * width * 0.1 * s + dy / L * 3)
        cr.set_line_width(q.lw * 0.45)
        core.src(cr, p.line, 0.2)
        cr.stroke()


def _fringe(q, end, prev, width, seed=0):
    """Six swaying tassels at a scarf end: one union, dilated outline."""
    cr, t = q.cr, q.t
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    damp = q.pose.damp
    n = 6 if q.detail >= 1 else 4
    strands = []
    for k in range(n):
        u = (k + 0.5) / n - 0.5
        bx, by = end[0] + nx * width * u * 0.95, end[1] + ny * width * u * 0.95
        sw = math.sin(t * 2.2 + k * 0.9 + seed) * (3.0 - 2.0 * damp) + q.pose.walk * 3 * math.sin(t * 8 + k)
        ln = 15.0 + 4.0 * core.hash01(k, seed) + 4 * damp
        strands.append([(bx, by), (bx + ux * ln * 0.5 + sw * 0.4, by + uy * ln * 0.5), (bx + ux * ln + sw, by + uy * ln)])
    lw = q.lw * 0.7
    cr.new_path()
    for st in strands:
        core.tapered(cr, st, 3.6 + 2 * lw, 1.6 + 2 * lw)
    core.src(cr, q.P(_scarf_mat(q)).line)
    cr.fill()
    for st in strands:
        core.tapered(cr, st, 3.6, 1.6)
    q.shade(Path(cr), _scarf_mat(q), lw=lw, rim=0.0, size=4, outline=False)


def _scarf_back_end(q):
    """The end thrown back over his left shoulder, hanging down his back."""
    proj, pose, t, S = q.proj, q.pose, q.t, q.S
    sh = S["shoulders"][1.0]
    R = S["R"]
    sway = B.chain(t, 4, freq=0.4, delay=0.15, amp=0.6, seed=pose.seed + 5)
    pts3 = [v_add(sh, m_vec(R, (-16.0, -12.0, -6.0))), v_add(sh, m_vec(R, (-12.0, 18.0, -30.0))),
            v_add(sh, m_vec(R, (-13.0, 66.0, -38.0))), v_add(sh, m_vec(R, (-15.0, 112.0, -36.0)))]
    pts2 = []
    for i, p in enumerate(pts3):
        p2 = proj.xy(p)
        pts2.append((p2[0] + sway[min(i, 3)] * 16 * i, p2[1]))
    shp, so = B.taper_paths(q.cr, pts2, 29.0, 26.0, q.lw, cap=False)
    q.shade(shp, _scarf_mat(q), outline=so, size=26)
    if q.detail >= 2:
        _knit_lines(q, pts2, 26.0)
    _fringe(q, pts2[-1], pts2[-2], 26.0, seed=3)


def _scarf(q):
    cr, proj, pose, t, S = q.cr, q.proj, q.pose, q.t, q.S
    sm = _scarf_mat(q)
    p = q.P(sm)
    nb = S["neck_base"]
    R = S["R"]
    lw = q.lw
    for (dy, rad, th) in ((-6.0, 30.0, 15.0), (-25.0, 27.0, 13.5)):      # two chunky wraps
        c = v_add(nb, m_vec(R, (0.0, dy, 3.0)))
        ring = [proj.xy((c[0] + math.sin(math.tau * i / 16) * rad, c[1] + 2.5 * math.sin(math.tau * i / 8),
                         c[2] + math.cos(math.tau * i / 16) * rad * 0.9)) for i in range(16)]
        xs = [r[0] for r in ring]
        ys = [r[1] for r in ring]
        cx_, cy_ = sum(xs) / 16, sum(ys) / 16
        rx = (max(xs) - min(xs)) / 2 + th
        ry = (max(ys) - min(ys)) / 2 + th
        cr.new_path()
        core.superellipse(cr, cx_, cy_, rx, ry, 2.6, steps=28)
        wrap = Path(cr)
        core.superellipse(cr, cx_, cy_, rx + lw, ry + lw, 2.6, steps=28)
        q.shade(wrap, sm, outline=Path(cr), size=th * 2.2, shadow=0.8)
        if q.detail >= 1:                                                 # knit ribs
            cr.save()
            wrap.add(cr)
            cr.clip()
            cr.new_path()
            for i in range(12):
                a = -math.pi * 0.9 + math.pi * 1.8 * i / 11
                if abs(math.sin(a)) > 0.93:
                    continue
                xx = cx_ + math.sin(a) * rx * 0.95
                cr.move_to(xx, cy_ - ry * 0.75)
                cr.curve_to(xx + 1.5, cy_ - ry * 0.2, xx + 1.5, cy_ + ry * 0.2, xx, cy_ + ry * 0.8)
            cr.set_line_width(lw * 0.6)
            core.src(cr, p.line, 0.32)
            cr.stroke()
            cr.restore()
    # front hanging end (his right side) with fringe
    sway = B.chain(t, 4, freq=0.42, delay=0.14, amp=0.5, seed=pose.seed + 9)
    c1 = v_add(nb, m_vec(R, (0.0, -6.0, 3.0)))
    walk_sw = S["walk"] * 4.0 * math.sin(math.tau * S["wc"].phase * 2 + 0.6)
    pts3 = [v_add(c1, m_vec(R, (-12.0, 8.0, 26.0))), v_add(c1, m_vec(R, (-15.0, 40.0, 36.0))),
            v_add(c1, m_vec(R, (-17.0, 82.0, 40.0))), v_add(c1, m_vec(R, (-16.0, 120.0, 41.0)))]
    if q.sit > 0.0:                         # seated: the end rests forward on the lap
        pts3[-1] = v_lerp(pts3[-1], v_add(c1, m_vec(R, (-17.0, 112.0, 54.0))), smooth(q.sit))
    pts2 = []
    for i, pp in enumerate(pts3):
        p2 = proj.xy(pp)
        pts2.append((p2[0] + (sway[min(i, 3)] * 16 + walk_sw) * i * 0.6, p2[1] - S["shake"] * 0.3))
    shp, so = B.taper_paths(cr, pts2, 30.0, 27.0, lw, cap=False)
    q.shade(shp, sm, outline=so, size=28)
    _knit_lines(q, pts2, 27.0)
    _fringe(q, pts2[-1], pts2[-2], 27.0, seed=1)


# ----------------------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------------------

def _expr(pose):
    e = B.expr(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    if pose.sigh > 0:
        e = e.blend(B.MOODS["sigh"], pose.sigh)
    if pose.laugh > 0:
        e = e.blend(B.MOODS["laugh"], pose.laugh)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    return e


def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH = S["RH"]
    HC = S["head_c"]
    e = _expr(pose)
    jaw_open = clamp(clamp(pose.talk) * 0.85 + e.open * 0.9)
    near = -1.0 if q.yaw + pose.head_turn * 1.1 >= 0 else 1.0
    far = -near
    lw = q.lw
    pal = q.P(M["scales"])

    def P(v):
        w = m_vec(RH, (v[0] * HS, v[1] * HS, v[2] * HS))
        return proj.xy((HC[0] + w[0], HC[1] + w[1], HC[2] + w[2]))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    ja = -jaw_open * 0.42
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):                               # rotate about the jaw hinge (0, 22, -2)
        y, z = v[1] - 22.0, v[2] + 2.0
        return (v[0], 22.0 + y * cj - z * sj, -2.0 + y * sj + z * cj)

    # ---- geometry (head space: X his left, Y down, Z forward)
    cran = []
    for i in range(16):
        a = math.tau * i / 16
        ca, sa = math.cos(a), math.sin(a)
        cran += [P((ca * 40.0, sa * 37.0, -4.0)), P((ca * 40.0, 0.0, -4.0 + sa * 39.0)), P((0.0, ca * 37.0, -4.0 + sa * 39.0))]
    snout = [P((math.cos(math.tau * i / 12) * 22.0, 17.0 + math.sin(math.tau * i / 12) * 15.0, 20.0)) for i in range(12)]
    snout += _circle2(P((0.0, 12.5, 40.0)), 13.5 * HS, 10)
    snout += _circle2(P((0.0, 20.0, 57.0)), 14.5 * HS, 12)
    jaw = [P(J((math.cos(math.tau * i / 10) * 18.0, 33.0 + math.sin(math.tau * i / 10) * 9.0, 10.0))) for i in range(10)]
    jaw += _circle2(P(J((0.0, 31.0, 28.0))), 11.0 * HS, 10)
    jaw += _circle2(P(J((0.0, 33.0, 46.0))), 10.0 * HS, 10)
    cheeks = [(P((s * 25.0, 17.0, 6.0)), 16.5 * HS * (0.65 + 0.35 * abs(nz((s, 0.2, 0.6))))) for s in (-1.0, 1.0)]

    _horn(q, P, far)
    _ear_fin(q, P, far, e)
    # ---- one seamless silhouette: all dilated pieces filled once in the line color
    hulls = [core.convex_hull(pts) for pts in (cran, jaw, snout)]
    cr.new_path()
    for h in hulls:
        core.smooth_closed(cr, B.offset_closed(h, lw), 0.85)
    for (c, r) in cheeks:
        core.circle(cr, c[0], c[1], r + lw)
    core.src(cr, pal.line)
    cr.fill()
    paths = []
    for h in hulls:
        core.smooth_closed(cr, h, 0.85)
        paths.append(Path(cr))
    cran_p, jaw_p, snout_p = paths
    for (c, r) in cheeks:
        core.circle(cr, c[0], c[1], r)
    cheek_p = Path(cr)
    cran_p.add(cr)                          # skull + jowls + jaw shaded as ONE form
    cheek_p.add(cr)
    jaw_p.add(cr)
    q.shade(Path(cr), M["scales"], outline=False, size=80)
    if q.detail >= 1:                       # sand under-jaw
        cr.save()
        jaw_p.add(cr)
        cr.clip()
        bp = q.P(M["belly"])
        ub = [P(J((s * 15.0, 41.0, z))) for s in (-1.0, 1.0) for z in (6.0, 26.0, 44.0)] + [P(J((0.0, 43.0, 50.0)))]
        lowest = max(p[1] for p in ub) + 26
        cr.new_path()
        core.smooth_closed(cr, core.convex_hull(ub + [(ub[0][0], lowest), (ub[3][0], lowest)]), 0.85)
        core.src(cr, core.mix(bp.shadow, bp.lit, 0.5))
        cr.fill()
        cr.restore()
    if jaw_open > 0.04:                     # mouth interior: over the jaw, under the snout
        ip = [P((sd * 17.0, 27.0, z)) for sd in (-1.0, 1.0) for z in (12.0, 30.0, 46.0)]
        ip += [P(J((sd * 15.0, 30.0, z))) for sd in (-1.0, 1.0) for z in (12.0, 30.0, 44.0)]
        ip += [P((0.0, 28.0, 58.0)), P(J((0.0, 31.0, 50.0)))]
        mouth_in, mouth_o, _ = q.hull(ip)
        mouth_o.add(cr)
        core.src(cr, pal.line)
        cr.fill()
        mouth_in.add(cr)
        core.src(cr, q.P(M["mouth"]).lit)
        cr.fill()
        cr.save()
        mouth_in.add(cr)
        cr.clip()
        tg = P(J((0.0, 30.0, 32.0)))
        core.src(cr, q.P(M["tongue"]).lit)
        core.ellipse(cr, tg[0], tg[1] + 3, 15.0 * HS, (6.0 + 5 * jaw_open) * HS)
        cr.fill()
        cr.restore()
    q.shade(snout_p, M["scales"], outline=False, size=40, rim=0.8)
    if jaw_open > 0.15:
        core.src(cr, "#F2EBDD")
        for sd in (-1.0, 1.0):
            if nz((sd * 0.5, 0.3, 0.8)) < 0.0:
                continue
            f0 = P((sd * 10.0, 27.5, 49.0))
            cr.move_to(f0[0] - 2.6, f0[1] - 1)
            cr.line_to(f0[0] + 2.6, f0[1] - 1)
            cr.line_to(f0[0], f0[1] + 5.5)
            cr.close_path()
        cr.fill()
    # ---- internal ink
    _snout_contour(q, P, hulls[2], pal, q.yaw + pose.head_turn * 1.1)
    mouth = _mouth_line(q, P, nz, e, jaw_open, pal, near)
    nose = P((0.0, 12.0, 68.0))
    lines = [[P((s * 6.0, 13.5, 66.0)), P((s * 9.0, 12.5, 67.0))] for s in (-1.0, 1.0) if nz((s * 0.4, -0.4, 0.8)) > -0.05]
    if lines:
        B.detail_lines(cr, lines, lw * 1.7, pal.line, 0.9, taper=(1.0, 0.8, 0.25))
    B.sheen(cr, *P((0.0, 7.0, 60.0)), 8.0, 4.0, alpha=0.16)
    if q.detail >= 2:                       # a few scale marks on the brow and snout
        cr.new_path()
        for (u, v, z) in ((-12, -26, 30), (0, -30, 26), (12, -26, 30), (-6, -20, 36), (6, -20, 36), (0, 3.0, 52), (-8, 5, 46), (8, 5, 46)):
            if nz((u / 40, v / 40, z / 40)) < 0.3:
                continue
            c0 = P((u, v, z))
            core.tapered(cr, [(c0[0] - 3.5, c0[1]), (c0[0], c0[1] + 2.0), (c0[0] + 3.5, c0[1])], 0.6, 0.6,
                         profile=lambda s_: 0.5 + 1.0 * math.sin(math.pi * s_))
        core.src(cr, pal.line, 0.32)
        cr.fill()
    if e.smile > 0.15 or e.cheek > 0.2:
        c = P((near * 24.0, 22.0, 18.0))
        B.detail_line(cr, [(c[0] + 3 * near, c[1] - 6), (c[0], c[1]), (c[0] - 2 * near, c[1] + 5)],
                      lw * 0.9, pal.line, 0.6 * clamp(max(e.smile, e.cheek)))
    # ---- eyes + brow ridges
    blink = B.auto_blink(t, pose.seed + 2) if pose.blink is None else pose.blink
    eyes = []
    tired = isinstance(pose.mood, str) and pose.mood in ("tired", "lonely", "sad")
    for s in (far, near):
        ec = P((s * 17.5, -7.0, 32.0))
        eyes.append(ec)
        fz = nz((s * 0.42, -0.12, 0.9))
        if fz < 0.06:
            continue
        fore = clamp(0.28 + fz * 0.8, 0.3, 1.0)
        op = P((s * 30.0, -7.0, 26.0))
        outer = 1.0 if op[0] > ec[0] else -1.0
        ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)   # eye axis, near horizontal
        B.eye(cr, ec[0], ec[1], 13.0 * HS * fore, 15.5 * HS, q.light, lw, angle=ang * 0.6,
              look=(pose.look[0] * outer, pose.look[1]), lid=e.lid, lid_bot=e.lid_bot, tilt=e.lid_tilt,
              outer=outer, blink=blink, squint_arc=clamp((pose.laugh - 0.5) * 2.0),
              iris=DRAGON_COLORS["eye"], iris_hi=DRAGON_COLORS["eye_hi"], pupil="#24150c",
              pupil_size=0.5 * e.pupil, pupil_aspect=0.78, skin=DRAGON_COLORS["scales"], crease=0.0,
              bags=(0.5 if tired else 0.2) if q.detail >= 1 else 0.0, line=pal.line, lid_shade=0.18)
        _brow_ridge(q, P, nz, s, e, near, None if s == near else paths + [cheek_p])
    _horn(q, P, near)
    _ear_fin(q, P, near, e)
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mouth, "nose": nose, "eyes": eyes,
            "ear_near": P((near * 38.0, 6.0, -4.0)), "top": P((0.0, -40.0, 0.0))}


def _snout_contour(q, P, hull, pal, turn):
    """Ink the snout's upper edge where it crosses the face, fading toward its root; only in
    turned views (head-on, the muzzle reads by its shading and the nose)."""
    fade = clamp((abs(math.sin(turn)) - 0.18) / 0.3)
    if fade <= 0.0:
        return
    tc = P((0.0, 20.0, 57.0))
    hc = P((0.0, 0.0, 0.0))
    dx, dy = tc[0] - hc[0], tc[1] - hc[1]
    L = math.hypot(dx, dy)
    if L < 10.0 * HS:
        return
    ux, uy = dx / L, dy / L
    seg = []
    for p in hull:
        rel = ((p[0] - hc[0]) * ux + (p[1] - hc[1]) * uy) / L
        up = ((p[0] - tc[0]) * -uy + (p[1] - tc[1]) * ux) * (1 if ux >= 0 else -1)
        if 0.12 < rel < 1.08 and up < 2.0:
            seg.append((rel, p))
    if len(seg) < 2:
        return
    seg.sort()
    a = clamp((L - 10.0 * HS) / 30.0) * fade
    B.detail_line(q.cr, [p for _, p in seg], q.lw * 0.9, pal.line, 0.75 * a, taper=(0.0, 0.8, 1.0))


def _mouth_line(q, P, nz, e, jaw_open, pal, near):
    """Closed-mouth line along each visible side of the snout (corners curl with the smile)."""
    sm = e.smile
    lift = -sm * 13.0
    lines, ticks = [], []
    for s in (near, -near):
        vis = nz((s * 0.75, 0.25, 0.6))
        if s != near and vis < 0.2:
            continue
        pts = []
        for z in (12.0, 22.0, 34.0, 46.0, 56.0):
            u = (z - 12.0) / 44.0
            pts.append(P((s * (19.0 - 9.0 * u * u), 28.0 + lift * (1.0 - u) ** 2 + jaw_open * 2, z)))
        pts.append(P((0.0, 29.0 + jaw_open * 2, 64.0)))
        lines.append(pts)
        c = pts[0]
        if sm < -0.1:
            ticks.append([c, (c[0], c[1] + 5 * -sm)])
        elif sm > 0.2:
            ticks.append([(c[0] + 3 * -s, c[1] + 2), c, (c[0] - 2 * -s, c[1] - 4)])
    if jaw_open < 0.04 and lines:
        B.detail_lines(q.cr, lines + ticks, q.lw * 1.25, pal.line, 1.0, taper=(0.9, 1.0, 0.3))
    return P((0.0, 30.0 + jaw_open * 8, 58.0))


def _brow_ridge(q, P, nz, s, e, near, clip=None):
    """Scaly brow ridge above the eye, driven by the expression (the far one is clipped to the
    head silhouette so it never pokes out like a third horn)."""
    if nz((s * 0.4, -0.5, 0.75)) < -0.1:
        return
    cr = q.cr
    if clip:
        cr.save()
        for pth in clip:
            pth.add(cr)
        cr.clip()
    asym = e.brow_asym * (1.0 if s == near else -0.4)
    li = (e.brow_in * 0.75 + e.brow_y + asym) * 14.0
    lo = (e.brow_out * 0.6 + e.brow_y + asym) * 12.0
    pts = [P((s * 6.0, -23.0 - li, 38.0)), P((s * 17.0, -27.0 - (li + lo) * 0.5 - 2.0, 35.0)), P((s * 29.0, -22.0 - lo, 27.0))]

    def prof(u):
        return 10.5 * (1.0 - 0.45 * u) * (0.75 + 0.25 * math.sin(math.pi * min(1.0, u * 1.2)))

    lwb = q.lw * 0.85
    shp, so = B.taper_paths(cr, pts, 9.0, 4.0, lwb, profile=prof)
    q.shade(shp, q.M["scales_dk"], lw=lwb, outline=so, size=7, rim=0.8)
    if clip:
        cr.restore()


def _horn(q, P, s):
    cr = q.cr
    pts = [P((s * 15.0, -30.0, -12.0)), P((s * 19.0, -45.0, -30.0)), P((s * 21.0, -52.0, -50.0)), P((s * 22.0, -50.0, -64.0))]
    lwh = q.lw * 0.9
    shp, so = B.taper_paths(cr, pts, 15.0 * HS, 2.4, lwh)
    pal = q.shade(shp, q.M["horn"], lw=lwh, outline=so, size=11, rim=0.8)
    if q.detail >= 2:                       # growth rings
        sp = core.spline(pts, n=3)
        lines = []
        for k in (2, 4):
            if k + 1 < len(sp):
                p0, p1 = sp[k], sp[k + 1]
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                L = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / L, dx / L
                w = (6.0 - k * 0.9) * HS
                lines.append([(p0[0] - nx * w, p0[1] - ny * w), (p0[0] + dx / L * 1.5, p0[1] + dy / L * 1.5), (p0[0] + nx * w, p0[1] + ny * w)])
        B.detail_lines(cr, lines, q.lw * 0.6, pal.line, 0.5)


def _ear_fin(q, P, s, e):
    """Membranous ear-fin behind the cheek: droops with sadness, perks with joy/surprise."""
    cr, t = q.cr, q.t
    perk = clamp(0.5 + 0.5 * (e.brow_y + 0.6 * e.smile - 0.5 * max(0.0, e.lid_tilt)), 0.0, 1.0)
    twitch = 0.06 * math.sin(t * 1.7 + s) + 0.12 * B.wobble(t, math.floor(t / 5.0) * 5.0 + 2.0, 6.0, 7.0)
    droop = lerp(0.9, -0.25, perk) + twitch
    root = (s * 33.0, 3.0, -12.0)
    L = 27.0
    d = (s * 0.55, math.sin(droop) * 0.9, -0.85)
    tip = (root[0] + d[0] * L, root[1] + d[1] * L + 6, root[2] + d[2] * L)
    upper = (root[0] + d[0] * L * 0.55, root[1] - 9.0 + d[1] * L * 0.5, root[2] + d[2] * L * 0.55)
    lower = (root[0] + d[0] * L * 0.45, root[1] + 12.0 + d[1] * L * 0.45, root[2] + d[2] * L * 0.4)
    pts = [P((root[0], root[1] - 9.0, root[2] + 4)), P(upper), P(tip), P(lower), P((root[0], root[1] + 10.0, root[2] + 2))]
    lwf = q.lw * 0.9
    shp, so = B.smooth_paths(cr, pts, lwf, 0.9)
    pal = q.shade(shp, q.M["fin"], lw=lwf, outline=so, size=16, rim=0.7)
    if q.detail >= 2:
        r0 = P(root)
        lines = []
        for f in (0.0, 0.5):
            mid = v_lerp(upper, lower, f)
            lines.append([r0, P(v_lerp(root, mid, 0.5)), P(v_lerp(mid, tip, 0.6))])
        B.detail_lines(cr, lines, q.lw * 0.7, pal.line, 0.5, taper=(0.8, 0.8, 0.1))


# ----------------------------------------------------------------------------------------
# breath effects
# ----------------------------------------------------------------------------------------

def dragon_smoke(cr, t, t0, rig, scale=None, dur=2.6, alpha=0.5, light_tint=None):
    """The sigh: a little curl of grey smoke from his nostrils starting at t0."""
    s = rig.scale if scale is None else scale
    col = "#9aa3ab" if light_tint is None else core.mix("#9aa3ab", light_tint, 0.3)
    fx.smoke(cr, t, t0, rig.nose[0], rig.nose[1], n=8, dur=dur, rise=60.0, drift=(26.0 * rig.facing, -6.0),
             size=6.5, color=col, alpha=alpha, seed=7, scale=s)


def dragon_embers(cr, t, t0, rig, scale=None, n=34, life=1.9, intensity=1.0):
    """The laugh: a small warm puff of golden embers/sparks from his mouth starting at t0 --
    the first warm light that comes from him (includes a short warm glow)."""
    s = rig.scale if scale is None else scale
    if t < t0:
        return
    u = t - t0
    side = math.sin(rig.yaw)
    front = 1.0 - min(1.0, abs(side) * 1.6)       # 1 head-on .. 0 from ~40 degrees of turn
    mx = rig.mouth[0] + 8.0 * s * side
    g = clamp(1.0 - u / 1.4) * clamp(u * 6.0) * intensity
    if g > 0:
        # a PAINTED warm glow (additive orange over his teal face turned pale green-white),
        # plus a small additive hot-spot for the bloom pass
        gx, gy = mx + 2.0 * s * side, rig.mouth[1] - 6 * s
        fx.glow(cr, gx, gy, 90.0 * s, "#ffa040", 0.32 * g, additive=False)
        fx.glow(cr, gx, gy, 34.0 * s, "#ffc060", 0.30 * g)
    # two half-puffs: head-on they fountain out to either side so they never veil the eyes;
    # solid cores keep them GOLD in front of the teal scales (the film's first warm light)
    for sgn, seed in ((-1.0, 21), (1.0, 22)):
        fx.embers(cr, t, mx + sgn * 10.0 * s * front, rig.mouth[1], t0=t0, n=n // 2, life=life,
                  spread=46.0 * (1.0 - 0.4 * front), rise=120.0, color="#ff8a24", hot="#ffe27a", size=2.6,
                  seed=seed, burst=0.5, scale=s, wind=30.0 * side + sgn * 100.0 * front, alpha=intensity,
                  solid=True)


# ----------------------------------------------------------------------------------------
# character sheet (python3 film/render.py --sheet)
# ----------------------------------------------------------------------------------------

_SHEET_BG = {
    "neutral": ("#6f7a86", "#4b545e"), "washhouse": ("#1d3a3d", "#0e1f22"),
    "apothecary": ("#d9e6e0", "#a9bdb6"), "street_night": ("#1b2340", "#0b1022"),
    "tavern": ("#5a2440", "#2a1020"), "square": ("#4a5668", "#2c3442"),
    "dusk": ("#a98aa6", "#e0a98a"), "golden": ("#e6b070", "#a8704a"),
    "blue_hour": ("#3a4a78", "#1e2848"), "lantern_night": ("#141c34", "#070a16"),
}


def _bg(cr, w, h, light="neutral", floor=None):
    top, bot = _SHEET_BG.get(light, _SHEET_BG["neutral"])
    core.vgrad(cr, 0, 0, w, h, [top, bot])
    if floor is not None:
        cr.set_source_rgba(0, 0, 0, 0.12)
        cr.rectangle(0, floor, w, h - floor)
        cr.fill()


def _sheet_stone(cr, frame):
    """Placeholder speaking stone (the props kit draws the real one). With hand_to_ear it is
    drawn BEHIND the hand, so it is longer than the hand is wide: its ends and glow show."""
    cr.save()
    core.ellipse(cr, 8, 0, 36, 17)
    core.src(cr, "#21343a")
    cr.fill()
    core.ellipse(cr, 8, 0, 33.5, 14.5)
    core.src(cr, "#5c6a70")
    cr.fill()
    core.src(cr, "#8ff0ff", 0.95)
    for k in range(4):
        core.circle(cr, -16 + k * 15, -3 + (k % 2) * 5, 2.4)
    cr.fill()
    cr.restore()


def _sheet_bag(cr, frame):
    """Placeholder apothecary bag hanging from the grip (kept upright)."""
    cr.save()
    cr.rotate(-frame.angle)
    core.src(cr, "#efe9dc")
    core.rounded_rect(cr, -18, 6, 36, 44, 4)
    cr.fill()
    core.src(cr, "#3a9a5a")
    cr.rectangle(-3, 18, 6, 18)
    cr.rectangle(-9, 24, 18, 6)
    cr.fill()
    cr.set_source_rgba(0.3, 0.25, 0.2, 0.8)
    cr.set_line_width(1.6)
    cr.move_to(-8, 8)
    cr.curve_to(-8, -6, 8, -6, 8, 8)
    cr.stroke()
    cr.restore()


def _sheet_note(cr, frame):
    cr.save()
    core.src(cr, "#efe2bf")
    cr.rotate(0.1)
    core.rounded_rect(cr, -6, -14, 34, 22, 2)
    cr.fill()
    cr.restore()


def _sheet_book(cr, frame):
    """Placeholder open coloring book (the props kit draws the real one)."""
    cr.save()
    core.src(cr, "#5a3a5a")
    core.rounded_rect(cr, -64, -40, 128, 70, 4)
    cr.fill()
    for sx in (-1, 1):
        core.src(cr, "#f2ead6")
        core.rounded_rect(cr, -62 if sx < 0 else 1, -38, 61, 64, 2)
        cr.fill()
        core.src(cr, "#8a5a8a", 0.6)
        core.circle(cr, sx * 31, -6, 18)
        cr.set_line_width(1.5)
        cr.stroke()
    cr.restore()


def _sheet_smile(cr):
    core.rotated_text(cr, "SMILE", 0, 0, -0.15, 15, core.MARKER, "#ff5fa2")


def _head_frame(pose, scale, light, t=0.4):
    """Where the head ends up for this pose (dry run on a scratch surface)."""
    s, c = core.frame(4, 4)
    rig = draw_dragon(c, 0.0, 0.0, scale, pose, light, t=t)
    return rig.head


def lineup():
    """The dragon on the cast height chart (render.py --sheet -> character_sheet_lineup.png)."""
    return [B.LineupItem("dragon", lambda cr, x, y, sc: draw_dragon(cr, x, y, sc, DragonPose(facing=1), t=0.4), 230.0)]


def sheet_items():
    """Character sheet cells for render.py --sheet (see API.md: sheet convention)."""
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    def bench(cr, x, ground, sc, seat_h, w=170):
        core.src(cr, "#6b4a2e")
        cr.rectangle(x - w / 2, ground - seat_h * sc - 8 * sc, w, 11 * sc)
        cr.fill()

    # ---- turnaround (scale 1.0 = 520 px standing)
    for label, pose in (("3/4 left", DragonPose(facing=-1)), ("front", DragonPose(facing=0)),
                        ("3/4 right", DragonPose(facing=1)), ("near profile", DragonPose(facing=1, turn=0.7)),
                        ("lean in, look", DragonPose(facing=1, lean=0.8, look=(0.6, 0.2), mood="raised")),
                        ("hunched sigh", DragonPose(facing=0, turn=0.3, sigh=1.0, wings=-1.0))):
        def fn(cr, p=pose):
            _bg(cr, 290, 600, floor=560)
            draw_dragon(cr, 120 if p.lean > 0 else 145, 572, 1.0, p, neutral, t=0.4)
            if p.sigh > 0:
                pass
        add(label, 290, 600, fn, "turnaround")
    # the turn is continuous (animate facing/turn); yaw is limited to +-1.45 rad: no back views
    for k, tv in enumerate((-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4)):
        def fn(cr, tv=tv):
            _bg(cr, 240, 320, floor=292)
            draw_dragon(cr, 120, 304, 0.54, DragonPose(facing=0, turn=tv, mood="tired"), neutral, t=0.4 + 0.3 * tv)
        add(f"turn {tv:+.1f} (yaw {_yaw_of(0, tv):+.2f})", 240, 320, fn, "turnaround")

    # ---- walk cycle + sitting
    for ph in (0.0, 0.25, 0.5, 0.75):
        add(f"walk {ph:.2f}", 200, 440, lambda cr, ph=ph: (_bg(cr, 200, 440, floor=412), draw_dragon(
            cr, 92, 424, 0.74, DragonPose(facing=1, walk=1.0, phase=ph, tail_drag=0.6), neutral, t=ph)), "walk & sit")
    for label, pose, sh in (("sit 3/4 (bench)", DragonPose(facing=1, sit=1.0), DRAGON_SEAT_H),
                            ("sit front, tail curled (S8)", DragonPose(facing=0, sit=1.0, tail_front=True, mood="warm"), DRAGON_SEAT_H),
                            ("too-small stool (S1)", DragonPose(facing=0, turn=0.45, sit=1.0, seat_h=72.0, wings=-0.9, hunch=0.85), 72.0)):
        def fn(cr, p=pose, sh=sh):
            _bg(cr, 270, 440, floor=412)
            bench(cr, 135, 424, 0.74, sh)
            draw_dragon(cr, 135, 424, 0.74, p.with_(seat_h=sh), neutral, t=0.4)
        add(label, 270, 440, fn, "walk & sit")
    # sitting down is one continuous parameter (hips back, chest over the feet, skirt swings)
    for sv in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        def fn(cr, sv=sv):
            _bg(cr, 240, 440, floor=412)
            bench(cr, 112, 424, 0.74, DRAGON_SEAT_H)
            draw_dragon(cr, 112, 424, 0.74, DragonPose(facing=1, turn=-0.3, sit=sv), neutral, t=0.4)
        add(f"sitting down: sit={sv:.1f}", 240, 440, fn, "walk & sit")

    # ---- faces (head close-ups, 3/4 + front)
    moods = [("tired (default)", dict(mood="tired")), ("lonely", dict(mood="lonely")),
             ("worried", dict(mood="worried")), ("raised", dict(mood="raised")),
             ("surprised", dict(mood="surprised")), ("skeptical", dict(mood="skeptical")),
             ("happy", dict(mood="happy")), ("warm smile", dict(mood="warm")),
             ("LAUGH + embers", dict(mood="tired", laugh=1.0)), ("sigh + smoke", dict(mood="tired", sigh=1.0)),
             ("talk 0.5", dict(mood="tired", talk=0.5)), ("talk 1.0", dict(mood="tired", talk=1.0)),
             ("frown", dict(mood="sad", smile=-0.8)), ("blink", dict(mood="tired", blink=1.0)),
             ("look up-left", dict(mood="raised", look=(-0.8, -0.6), head_nod=0.4)),
             ("front: kind, talking", dict(mood="kind", talk=0.6, facing=0)),
             ("front: lonely", dict(mood="lonely", facing=0)), ("front: laugh", dict(mood="tired", laugh=1.0, facing=0)),
             ("3/4 left: worried", dict(mood="worried", facing=-1)), ("3/4 left: happy", dict(mood="happy", facing=-1)),
             ("head turn", dict(mood="tired", head_turn=-0.6))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        pose = DragonPose(facing=facing, turn=-0.35 if facing == 1 else (0.35 if facing == -1 else 0.0), **kw)

        def fn(cr, p=pose):
            _bg(cr, 230, 230)
            hx, hy = _head_frame(p, 1.45, neutral)
            rig = draw_dragon(cr, 115 - hx, 128 - hy, 1.45, p, neutral, t=0.4)
            if p.laugh > 0:
                dragon_embers(cr, 0.9, 0.2, rig)
            if p.sigh > 0:
                dragon_smoke(cr, 1.2, 0.0, rig)
        add(label, 230, 230, fn, "faces")

    # ---- gestures (placeholder props: the props kit draws the real stone, bag, note, book)
    gest = [("hand_to_ear (stone)", DragonPose(facing=1, near=Arm("hand_to_ear", hold=_sheet_stone))),
            ("hand_to_ear + carry_bag, walk", DragonPose(facing=-1, walk=1.0, phase=0.3, far=Arm("carry_bag", hold=_sheet_bag), near=Arm("hand_to_ear", hold=_sheet_stone))),
            ("hand_out_offer", DragonPose(facing=1, near=Arm("hand_out_offer"), mood="raised")),
            ("slide_note", DragonPose(facing=1, lean=0.5, near=Arm("slide_note", hold=_sheet_note), mood="worried")),
            ("look_at_hand (SMILE stamp)", DragonPose(facing=1, near=Arm("look_at_hand", stamp=_sheet_smile), mood="sad", head_nod=-0.3, look=(0.4, 0.6))),
            ("arms_crossed", DragonPose(facing=0, turn=0.3, near=Arm("arms_crossed"), far=Arm("arms_crossed"), mood="skeptical")),
            ("hug-ready", DragonPose(facing=0, near=Arm("hug"), far=Arm("hug"), mood="warm", wings=0.4)),
            ("toss_crumbs: wind-up", DragonPose(facing=1, sit=1.0, near=Arm("toss_crumbs", phase=0.1), mood="warm")),
            ("toss_crumbs: release", DragonPose(facing=1, sit=1.0, near=Arm("toss_crumbs", phase=0.6), mood="happy")),
            ("hold_book (two hands)", DragonPose(facing=0, sit=1.0, near=Arm("hold_book", hold=_sheet_book), far=Arm("hold_book"), mood="skeptical", head_nod=-0.4, look=(0, 0.8))),
            ("pockets", DragonPose(facing=1, turn=-0.3, near=Arm("pockets"), far=Arm("pockets"), mood="lonely", wings=-0.9)),
            ("wave", DragonPose(facing=0, turn=0.2, near=Arm("wave", phase=0.2), mood="happy", wings=0.5))]
    for label, pose in gest:
        def fn(cr, p=pose):
            _bg(cr, 290, 440, floor=412)
            if p.sit > 0.5:
                bench(cr, 145, 424, 0.72, DRAGON_SEAT_H)
            rig = draw_dragon(cr, 145, 424, 0.72, p, neutral, t=0.4)
            if p.near.gesture == "hand_to_ear":     # the stone's light spills over the hand
                h = rig.hand_near
                fx.glow(cr, h.x, h.y, 34, "#5fe0ff", 0.45)
        add(label, 290, 440, fn, "gestures")

    # ---- the same dragon under every scene light
    for name in ("washhouse", "apothecary", "street_night", "tavern", "square", "dusk", "golden", "lantern_night"):
        def fn(cr, name=name):
            _bg(cr, 210, 440, name, floor=412)
            pose = DragonPose(facing=1, turn=-0.25, mood="tired", damp=1.0 if name == "street_night" else 0.0)
            draw_dragon(cr, 100, 424, 0.72, pose, L[name], t=0.4)
        add(f"{name}", 210, 440, fn, "lighting (LIGHTS presets)")
    # ---- ... and in each scene's signature pose (placeholder props; see SPEC beat sheet)
    story = [
        ("S1 washhouse: stool, drooped", "washhouse", 72.0,
         DragonPose(facing=0, turn=0.45, sit=1.0, seat_h=72.0, hunch=0.9, wings=-1.0, mood="lonely", look=(0.6, 0.2))),
        ("S2 apothecary: slide_note", "apothecary", 0.0,
         DragonPose(facing=1, lean=0.5, hunch=0.7, near=Arm("slide_note", hold=_sheet_note), mood="worried")),
        ("S3 street: stone, bag, damp", "street_night", 0.0,
         DragonPose(facing=1, walk=1.0, phase=0.35, damp=1.0, tail_drag=0.8, wings=-0.9, mood="sad",
                    near=Arm("hand_to_ear", hold=_sheet_stone), far=Arm("carry_bag", hold=_sheet_bag))),
        ("S4 tavern: look_at_hand", "tavern", 0.0,
         DragonPose(facing=1, near=Arm("look_at_hand", stamp=_sheet_smile), mood="sad", head_nod=-0.3, look=(0.4, 0.6))),
        ("S5 square: watching", "square", 0.0,
         DragonPose(facing=-1, turn=0.3, near=Arm("pockets"), far=Arm("pockets"), mood="lonely", wings=-0.8, look=(-0.8, 0.0))),
        ("S6 dusk: coloring book", "dusk", DRAGON_SEAT_H,
         DragonPose(facing=0, turn=-0.4, sit=1.0, near=Arm("hold_book", hold=_sheet_book), far=Arm("hold_book"),
                    mood="skeptical", head_nod=-0.9, look=(0.0, 0.9))),
        ("S7 golden: offered bread", "golden", DRAGON_SEAT_H,
         DragonPose(facing=1, turn=-0.3, sit=1.0, near=Arm("hand_out_offer"), mood="warm", wings=0.2)),
        ("S8 lantern: tail curled", "lantern_night", DRAGON_SEAT_H,
         DragonPose(facing=0, turn=0.25, sit=1.0, tail_front=True, mood="kind", wings=0.0)),
    ]
    for label, name, sh, pose in story:
        def fn(cr, name=name, sh=sh, p=pose):
            _bg(cr, 210, 440, name, floor=412)
            if sh:
                bench(cr, 105, 424, 0.62, sh, w=190)
            rig = draw_dragon(cr, 105 if p.walk == 0 else 92, 424, 0.62, p, L[name], t=0.4)
            if p.near.gesture == "hand_to_ear":
                fx.glow(cr, rig.hand_near.x, rig.hand_near.y, 30, "#5fe0ff", 0.45)
        add(label, 210, 440, fn, "lighting (LIGHTS presets)")

    # ---- film-scale readability (faces must read at 350-600 px tall)
    for label, sc, pose in (("350 px tall", 350 / DRAGON_HEIGHT, DragonPose(facing=1, mood="sad", talk=0.6)),
                            ("450 px", 450 / DRAGON_HEIGHT, DragonPose(facing=0, mood="worried")),
                            ("600 px", 600 / DRAGON_HEIGHT, DragonPose(facing=-1, mood="happy", wings=0.6, laugh=0.4)),
                            ("200 px (wide shot)", 200 / DRAGON_HEIGHT, DragonPose(facing=0, sit=1.0, mood="warm", tail_front=True))):
        w = 300 if sc > 0.5 else 220

        def fn(cr, sc=sc, p=pose, w=w):
            _bg(cr, w, 640, "dusk" if sc < 0.5 else "neutral", floor=610)
            if p.sit > 0.5:
                bench(cr, w / 2, 625, sc, DRAGON_SEAT_H, w=90)
            draw_dragon(cr, w / 2, 625, sc, p, L["dusk"] if sc < 0.5 else neutral, t=0.4)
        add(label, w, 640, fn, "film scale")
    return items
