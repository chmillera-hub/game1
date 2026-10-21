"""gnome.py -- THE GNOME GRANDMOTHER ("the Old Woman", speaker OLD_WOMAN): the film's second lead.

Tiny and round -- a pear with a cone on top. A big soft rosy nose, rosy cheeks, round brass
spectacles that glint, silver-white hair rolled at the brow and twisted into a bun that peeks
out under the back of a faded-red pointed hood whose long tip flops about (secondary motion),
a lavender knitted shawl-cardigan, a mossy green skirt, little laced boots, and a linen
satchel with a round crusty loaf. Twinkly; dry wit.

    from film.lib import characters as ch
    pose = ch.GnomePose(facing=1, sit=1, mood="kind", talk=timeline.talk(6, t, "OLD_WOMAN"),
                        near=ch.GnomeArm("toss_crumbs", phase=u, bread="piece"))
    rig = ch.draw_gnome(cr, x, ground_y, 0.9, pose, ch.LIGHTS["dusk"], t)
    # crumbs from her hand: her rig at the release moment (once, in setup()), pigeons eat them
    rel = ch.gnome_rig_at(x, ground_y, 0.9, pose_at(t_release), t_release)
    flock = ch.PigeonFlock(6, crumbs=ch.gnome_crumb_landings(t_release, rel, ground_y + 10))
    ch.gnome_toss_crumbs(cr, t, t_release, rel, ground_y + 10, flock=flock)

Scale 1.0: standing, ground -> hood crown = GNOME_HEIGHT = 160 px (the floppy hood tip rises
~45 px more and, like hats, is not counted). Seated on the standard bench (GNOME_SEAT_H = 125)
her head is ~228 px above the ground, level with the seated dragon's elbow at the same scale,
and her little boots dangle ~95 px off the ground. Anchor (x, y) = the ground point below her
pelvis (pose.anchor="seat": the seat point). 3D-lite like the dragon: joints in body space
(X = her left, Y down, Z forward), projected with the body yaw, so she turns continuously.
"""

import math
from dataclasses import dataclass, field, replace

from .. import core, fx
from ..core import clamp, lerp, smooth
from . import _cast_kit as K
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp

TAU = math.tau

__all__ = ["GnomePose", "GnomeArm", "GnomeRig", "draw_gnome", "gnome_bread", "gnome_bread_hold",
           "gnome_toss_crumbs", "gnome_crumb_landings", "gnome_tear_crumbs", "gnome_rig_at", "gnome_stride",
           "gnome_walk_phase", "GNOME_HEIGHT",
           "GNOME_SEAT_H", "GNOME_LINE", "GNOME_LOAF", "GNOME_COLORS", "GNOME_GESTURES", "gnome_mats"]

# ----------------------------------------------------------------------------------------
# design constants (body space px at scale 1.0)
# ----------------------------------------------------------------------------------------
GNOME_HEIGHT = 160.0
GNOME_SEAT_H = B.BENCH_SEAT_H      # 125: the standard bench
GNOME_LINE = B.LINE                # 2.2: the house weight (the same for every creature)
GNOME_LOAF = 46.0                  # loaf diameter

PELVIS_Y = -60.0
HIP_W = 10.0
THIGH, SHIN, ANKLE_H = 25.0, 23.0, 12.0
UPPER_ARM, FOREARM, HAND_LEN = 21.0, 20.0, 20.0
SHOULDER_W = 21.0
STRIDE = 46.0                      # body-space distance per walk cycle (two little steps)
ELEV = 0.12
SEAT_DY = 6.0                      # hip joint above the seat surface when seated
SIT_SWAP = 0.5                     # sit >= this: the seated skirt (lap + drape) replaces the bell

# head space (px, origin = head center; X her left, Y down, Z forward). The hood sits snug on
# the skull and its hem runs in front of the ears, so the round face fills most of the head.
FACE_C, FACE_R = (0.0, 0.5, 0.0), (25.0, 26.5, 24.5)
DOME_C, DOME_R = (0.0, -3.5, -2.5), (28.5, 30.0, 28.5)
EYE_X, EYE_Y, EYE_Z = 11.2, -5.0, 20.0
EYE_RX, EYE_RY = 6.4, 7.7
LENS_R = 9.4
NOSE_C, NOSE_R = (0.0, 7.5, 25.0), 8.8
MOUTH_Y, MOUTH_Z = 20.5, 19.0
BRIM_R = 2.1
ARCH = [(-20.5, 17.5, 1.5), (-25.5, 5.0, 0.5), (-25.0, -10.0, 3.0), (-18.0, -22.0, 7.0),
        (0.0, -27.5, 9.5), (18.0, -22.0, 7.0), (25.0, -10.0, 3.0), (25.5, 5.0, 0.5),
        (20.5, 17.5, 1.5)]

GNOME_COLORS = {
    "skin": "#EDB596",        # warm peach
    "nose": "#EBA88E",        # the big soft nose, a little rosier than the face
    "blush": "#E8706B",       # rosy cheeks
    "hair": "#E9E5EE",        # silver-white
    "brow": "#C2BBCE",        # her brows, a deeper silver so they act against skin and hair
    "hood": "#B5524A",        # faded red: HER signature accent
    "tassel": "#8E3A36",
    "lining": "#C9786B",      # the hood's lining, showing at its rolled edge
    "shawl": "#9B8BB8",       # lavender knit (SPEC)
    "sleeve": "#8C7CAB",      # cardigan sleeves, a shade deeper
    "cuff": "#75669A",
    "skirt": "#6A7A45",       # mossy green
    "stocking": "#5A5163",    # charcoal-plum wool
    "boot": "#70492F",        # brown leather
    "sole": "#3D2A1F",
    "satchel": "#CDBA90",     # oatmeal linen
    "flap": "#B8A276",
    "strap": "#86603F",
    "toggle": "#6E4A2C",
    "crust": "#C47A36",       # loaf crust, golden brown
    "crust_hi": "#EDBF73",    # the scored "ears" and floury crust
    "crumb": "#F2DFB4",       # inside of the loaf
    "specs": "#C9A04A",       # brass wire
    "eye": "#5D86B6",         # forget-me-not blue-grey
    "eye_hi": "#BCD7F3",
    "mouth": "#6E2B30",
    "tongue": "#CC6470",
    "teeth": "#F3EDE0",
}

_MATS = {}


def gnome_mats():
    """Materials used by the gnome (also handy for props that should match her)."""
    if not _MATS:
        C = GNOME_COLORS
        _MATS.update({
            "skin": Mat.of(C["skin"], sss=0.45, line_k=0.5),
            "nose": Mat.of(C["nose"], sss=0.5, sheen=0.3, line_k=0.5),
            "hair": Mat.of(C["hair"], shadow_k=0.92, line_k=0.72),
            "brow": Mat.of(C["brow"], line_k=0.62),
            "hood": Mat.of(C["hood"], shadow_k=1.05),
            "tassel": Mat.of(C["tassel"]),
            "lining": Mat.of(C["lining"], line_k=0.5),
            "shawl": Mat.of(C["shawl"], shadow_k=1.1),
            "sleeve": Mat.of(C["sleeve"], shadow_k=1.1),
            "cuff": Mat.of(C["cuff"], shadow_k=1.1),
            "skirt": Mat.of(C["skirt"], shadow_k=1.1),
            "stocking": Mat.of(C["stocking"], shadow_k=1.05),
            "boot": Mat.of(C["boot"], sheen=0.35),
            "satchel": Mat.of(C["satchel"], shadow_k=0.95),
            "flap": Mat.of(C["flap"]),
            "strap": Mat.of(C["strap"], sheen=0.3),
            "toggle": Mat.of(C["toggle"], sheen=0.4),
            "crust": Mat.of(C["crust"], sheen=0.25, sss=0.2),
            "crust_hi": Mat.of(C["crust_hi"]),
            "crumb": Mat.of(C["crumb"], shadow_k=0.9, line_k=0.5),
            "specs": Mat.of(C["specs"], sheen=0.8),
        })
    return _MATS


# shared supporting-cast helpers (see _cast_kit.py)
_union, _union_paths, _flat, _caps, _tube = K.union, K.union_paths, K.flat, K.caps, K.tube
_circle_pts, _yaw_of, _bench = K.circle_pts, K.yaw_of, K.sheet_bench


# ----------------------------------------------------------------------------------------
# pose
# ----------------------------------------------------------------------------------------

@dataclass
class GnomeArm:
    """One arm's gesture (names: GNOME_GESTURES).

    amt     0..1 blend from `prev` into `gesture` (animate it for the move; hands travel on arcs)
    hold    callback hold(cr, frame) drawing a prop in the hand (z-correct, see base.hand)
    bread   draw HER bread in this hand without a callback: "loaf", "half" or "piece"
    target  explicit wrist target in body space (x her left, y down, z forward; px at scale 1)
    screen  wrist target in the CALLER's coordinates (e.g. the dragon's rig.hand_near), reached
            at the depth of her shoulder + `depth`; overrides gesture/target
    hand    hand pose override (base.HAND_POSES name)
    phase   gesture-internal 0..1 (toss_crumbs wind-up -> flick, tear_bread, pat_bench, wave)
    """
    gesture: str = "rest"
    amt: float = 1.0
    prev: str = "rest"
    hold: object = None
    bread: str = None
    target: tuple = None
    screen: tuple = None
    depth: float = 16.0
    hand: str = None
    phase: float = 0.0


@dataclass
class GnomePose:
    """Everything that poses the gnome grandmother. All fields are optional.

    facing    +1 faces screen-right (3/4 view), -1 screen-left, 0 front
    turn      extra body yaw (x0.6 rad) on top of facing; yaw is clamped to +-1.45 (no back views)
    sit       0 standing .. 1 seated (the blend hops her up onto the seat); seat_h seat height
    walk      0..1 blend into her waddle; phase = gnome_walk_phase(distance, scale, facing)
    lean      -1 back .. +1 forward
    head_turn -1..1 head yaw relative to the body; head_tilt roll (rad); head_nod -1 down .. +1 up
    look      eye direction (-1..1, -1..1) relative to the head, +x screen right, +y down
    mood      base.MOODS name or Expr (default "kind"); mood2 + mood_mix blend toward a second
    talk      0..1 from timeline.talk(scene, t, "OLD_WOMAN"); smile -1..1 overrides the mood's
    smirk     0..1 one-sided dry-wit smile (her near mouth corner)
    laugh     0..1 the warm laugh: eyes squeeze shut, head back, shoulders shake, hood tip bounces
    blink     None = automatic, else 0..1
    specs     0 spectacles on .. 1 slid down her nose: she peers OVER them (S6 glance)
    glint     None = an occasional automatic glint, 0..1 = force the sweep across the lenses,
              -1 = never
    near/far  GnomeArm for the arm nearer / farther from the camera (front view: near = screen-left)
    satchel   "loaf" (her loaf peeks out), "empty", or None; satchel_side -1 her right hip, +1 left
    kick      seated: the dangling legs swing 0..1 (idle swing is always on)
    legs_out  seated: 0 legs dangle .. 1 stuck straight out (too short for the bench)
    hood_swing  extra hood-tip follow-through -1..1 (e.g. B.follow(turn_fn, t, 0.2, 2.0))
    anchor    "ground" or "seat"; elev camera elevation; shadow draw the contact shadow
    """
    facing: int = 1
    turn: float = 0.0
    sit: float = 0.0
    seat_h: float = GNOME_SEAT_H
    walk: float = 0.0
    phase: float = 0.0
    lean: float = 0.0
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    mood: object = "kind"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    smile: float = None
    smirk: float = 0.0
    laugh: float = 0.0
    blink: float = None
    specs: float = 0.0
    glint: float = None
    near: GnomeArm = field(default_factory=GnomeArm)
    far: GnomeArm = field(default_factory=GnomeArm)
    satchel: str = "loaf"
    satchel_side: float = -1.0
    kick: float = 0.0
    legs_out: float = 0.0
    hood_swing: float = 0.0
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class GnomeRig:
    """Attach points returned by draw_gnome, all in the CALLER's coordinates."""
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    nose: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    lenses: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)
    hood_tip: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    lap: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    seat: tuple = (0.0, 0.0)
    satchel: tuple = (0.0, 0.0)
    bread: tuple = None          # tear_bread: where the loaf breaks (crumbs come from here)
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0


def gnome_stride(scale=1.0, facing=1, turn=0.0):
    """Screen px the anchor travels per waddle cycle (feet don't slide)."""
    return STRIDE * abs(math.sin(_yaw_of(facing, turn))) * scale


def gnome_walk_phase(distance_px, scale=1.0, facing=1, turn=0.0):
    st = gnome_stride(scale, facing, turn)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


# ----------------------------------------------------------------------------------------
# gestures -> (wrist target in body space, hand pose, extra hand angle, layer)
# layer: "front" (over the head), "mid" (over the body, under the head), "auto" (by view)
# ----------------------------------------------------------------------------------------

def _g_rest(sk, side, c):
    # standing: hands folded over her tummy; seated: resting on her lap
    stand = v_add(c["waist"], (side * 8.5, 3.0, 20.0))
    k = c["sit_k"]
    if k <= 0.0:
        return stand, "relaxed", 0.45, "front"
    lap = v_add(c["lap"][side], (side * 3.0, -3.0, -3.0))
    return v_lerp(stand, lap, k), "relaxed", lerp(0.45, 0.2, k), "front"


def _g_toss(sk, side, c):
    # pinch crumbs off the bread in her lap, a little wind-up, then a flick out the way she faces
    ph = c["phase"]
    f = c["fwd"]
    base = v_add(c["lap"][side], (side * 2.0, -6.0, 4.0)) if c["sit_k"] > 0.5 else v_add(c["waist"], (side * 10.0, 2.0, 18.0))
    wind = v_add(sk, (side * 12.0 - f[0] * 8.0, 24.0, -6.0))
    rel = v_add(sk, (side * 6.0 + f[0] * 30.0, 8.0, 10.0 + f[2] * 26.0))
    if ph < 0.38:
        return v_lerp(base, wind, core.inout_sine(ph / 0.38)), "pinch", 0.0, "front"
    if ph < 0.55:
        return v_lerp(wind, rel, core.in_quad((ph - 0.38) / 0.17)), "pinch", 0.0, "front"
    return v_lerp(rel, base, 0.55 * core.inout_sine((ph - 0.55) / 0.45)), "open", 0.0, "front"


def _tear_sep(ph):
    """tear_bread: how far apart the hands are (0 whole loaf .. 1 halves apart)."""
    if ph < 0.5:
        return 0.0
    return core.out_back(clamp((ph - 0.5) / 0.32), 1.4)


def _g_tear(sk, side, c):
    ph = c["phase"]
    sep = _tear_sep(ph)
    strain = 0.0 if ph < 0.3 or ph >= 0.5 else math.sin((ph - 0.3) / 0.2 * math.pi * 3.0) * 1.2
    ctr = v_add(c["chest"], (0.0, 14.0, 19.0))
    return v_add(ctr, (side * (21.0 + 15.0 * sep + strain), -1.5 - 4.0 * sep, -3.0 * sep)), "grip", side * -0.0, "front"


def _g_hold_bread(sk, side, c):
    return v_add(c["chest"], (side * 9.0, 15.0, 17.0)), "grip", 0.0, "front"


def _g_offer(sk, side, c):
    # arm out the way she faces (toward whoever sits beside her), palm up, at chest height
    f = c["fwd"]
    return v_add(sk, (side * 5.0 + f[0] * 33.0, 7.0, 8.0 + f[2] * 27.0)), "offer", 0.0, "front"


def _g_hand_on_chest(sk, side, c):
    return v_add(c["chest"], (-side * 4.0, 0.0, 17.0)), "flat", side * 0.35, "front"


def _g_reach_satchel(sk, side, c):
    return v_add(c["satchel_mouth"], (0.0, -6.0, 2.0)), "pinch", 0.0, "front"


def _g_pat(sk, side, c):
    # seated: pat the bench beside her ("sit, sit") -- phase drives two pats
    ph = c["phase"]
    lift = abs(math.sin(ph * math.pi * 2.0)) * 9.0
    return v_add(c["pelvis"], (side * 33.0, -2.0 - lift, 4.0)), "flat", 0.0, "auto"


def _g_wave(sk, side, c):
    ph = c["phase"]
    return v_add(sk, (side * (16.0 + 5.0 * math.sin(ph * TAU * 2)), -16.0, 12.0)), "open", 0.0, "front"


def _g_point(sk, side, c):
    return v_add(sk, (side * 6.0, 10.0, 35.0)), "point", 0.0, "front"


GNOME_GESTURES = {
    "rest": _g_rest, "toss_crumbs": _g_toss, "tear_bread": _g_tear, "hold_bread": _g_hold_bread,
    "hand_out_offer": _g_offer, "hand_on_chest": _g_hand_on_chest, "reach_satchel": _g_reach_satchel,
    "pat_bench": _g_pat, "wave": _g_wave, "point": _g_point,
}


# ----------------------------------------------------------------------------------------
# per-draw context
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_gnome(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    """Draw the gnome grandmother with her anchor at (x, y) (see module doc). Returns a GnomeRig.
    t drives the idle life (breathing, blinks, hood tip, dangling feet, glints)."""
    pose = pose or GnomePose()
    light = light or B.LIGHTS["neutral"]
    q = K.Q(cr, light, gnome_mats(), t, pose)
    yaw = _yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    sit = clamp(pose.sit)
    q.sit = sit
    seat_h = pose.seat_h
    dev = q.lod(scale, detail)          # detail 2/1/0; q.micro = close-up textures (knit, laces...)
    q.lw = max(GNOME_LINE, B.MIN_LINE_PX / max(dev, 1e-6))

    cr.save()
    cr.translate(x, y + (seat_h * scale * sit if pose.anchor == "seat" else 0.0))
    cr.scale(scale, scale)
    S = _skeleton(pose, t, sit, seat_h, yaw)
    q.S = S
    rig = GnomeRig(scale=scale, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)

    if pose.shadow:
        fa = [proj.xy(f["ankle"]) for f in S["feet"]]
        cxs = (fa[0][0] + fa[1][0]) / 2.0
        k = smooth(sit)
        # seated, the shadow pools under the bench seat and her dangling boots
        B.contact_shadow(cr, lerp(cxs, cxs * 0.5, k), 1.5, lerp(46.0, 40.0, k), lerp(9.0, 8.0, k),
                         alpha=lerp(0.34, 0.2, k))

    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    arms = {near_side: pose.near, far_side: pose.far}
    S["ctx"]["satchel_mouth"] = _satchel_frame(q)["mouth"]
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
    tear = pose.near.gesture == "tear_bread" and pose.far.gesture == "tear_bread"
    if tear:
        near_layer = far_layer = "two"
    sat_near = (pose.satchel_side < 0) == (yaw >= 0) or abs(yaw) < 0.3

    # ---------------- back to front
    if far_layer == "back":
        rig.hand_far = _arm(q, A[far_side], far_side)
    _legs(q)
    if pose.satchel and not sat_near:
        rig.satchel = _satchel(q)
    _skirt(q)
    for s, layer in ((far_side, far_layer), (near_side, near_layer)):
        if layer != "back":
            _arm(q, A[s], s, parts="upper")
    if pose.satchel:
        _strap(q)
    _shawl(q)
    if pose.satchel and sat_near:
        rig.satchel = _satchel(q)
    if far_layer == "mid":
        rig.hand_far = _arm(q, A[far_side], far_side, parts="lower")
    if near_layer == "mid":
        rig.hand_near = _arm(q, A[near_side], near_side, parts="lower")
    head = _head(q)
    if tear:
        rig.hand_far, rig.hand_near, rig.bread = _tear_bread(q, A[far_side], A[near_side])
    else:
        if far_layer == "front":
            rig.hand_far = _arm(q, A[far_side], far_side, parts="lower")
        if near_layer == "front":
            rig.hand_near = _arm(q, A[near_side], near_side, parts="lower")

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
    rig.lenses = [C(e) for e in head["lenses"]]
    rig.top = C(head["top"])
    rig.hood_tip = C(head["tip"])
    rig.chest = C(proj.xy(S["chest"]))
    rig.lap = C(proj.xy(v_lerp(S["ctx"]["lap"][-1.0], S["ctx"]["lap"][1.0], 0.5)))
    rig.feet = [C(proj.xy(f["ankle"])) for f in S["feet"]]
    rig.seat = C((0.0, -seat_h * sit))
    rig.satchel = C(rig.satchel) if rig.satchel else C(proj.xy(_satchel_frame(q)["c"]))
    if rig.bread is not None:
        rig.bread = C(rig.bread)
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

HEAD_CHEAT = 0.28          # the head turns (1 - this) x the body yaw: faces stay readable in 3/4


def _skeleton(pose, t, sit, seat_h, yaw=0.0):
    S = {}
    br = B.breathing(t, 0.27, pose.seed)               # small creature: a slightly quicker breath
    laugh = clamp(pose.laugh)
    shake = laugh * (math.sin(t * TAU * 5.3) * 1.5 + math.sin(t * TAU * 2.4 + 1.0) * 0.8)
    k = smooth(sit)
    walk = clamp(pose.walk) * (1.0 - k)
    wc = B.walk_cycle(pose.phase, stride=STRIDE, lift=6.5, bob=1.8, swing=1.0)
    S.update(br=br, shake=shake, walk=walk, wc=wc, laugh=laugh, sit_k=k)

    arc = math.sin(math.pi * clamp(sit))
    stand_pel = (walk * wc.hip_sway * 2.2, PELVIS_Y + walk * (wc.hip_dy + 1.0), 0.0)
    sit_pel = (0.0, -seat_h - SEAT_DY, -6.0)
    pel = v_add(v_lerp(stand_pel, sit_pel, k), (0.0, -12.0 * arc, -6.0 * arc))   # a hop up onto the seat
    S["pelvis"] = pel
    idle = B.sway(t, 0.21, pose.seed + 4)
    tilt = 0.30 * pose.lean - 0.15 * laugh + 0.04 * k + 0.05 * walk + 0.02 * idle + 0.015 * br
    roll = walk * wc.hip_sway * 0.06 + 0.02 * B.sway(t, 0.16, pose.seed + 9)       # waddle
    R = m_mul(m_rot_z(roll), m_rot_x(-tilt))
    S["R"], S["tilt"] = R, tilt

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["waist"] = T((0.0, -13.0, 1.0))
    S["chest"] = T((0.0, -25.0 - 0.6 * br, 5.0 + 0.6 * br))
    sh_y = -30.5 - 0.9 * br - shake * 0.7
    S["sh_y"] = sh_y
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y + 2.5, -1.0)) for s in (-1.0, 1.0)}
    S["neck"] = T((0.0, sh_y - 6.0, 2.0))

    # head: tiny emphasis nods while she talks; the laugh throws it back
    talk = clamp(pose.talk)
    nod = (pose.head_nod * 0.38 + 0.2 * laugh + 0.015 * br + 0.035 * talk * math.sin(t * 7.3)
           + 0.02 * B.sway(t, 0.27, pose.seed + 2) - 0.45 * tilt)
    hy = clamp(pose.head_turn, -1.2, 1.2) * 0.95
    hr = pose.head_tilt + 0.05 * laugh * math.sin(t * 8.5) + 0.03 * B.sway(t, 0.19, pose.seed + 6)
    RH = m_mul(m_rot_y(hy - HEAD_CHEAT * yaw), m_mul(m_rot_x(nod), m_rot_z(hr)))
    S["RH"], S["head_yaw"] = RH, hy - HEAD_CHEAT * yaw
    S["head_c"] = v_add(S["neck"], v_add(m_vec(RH, (0.0, -27.0, 3.0)),
                                         (0.0, shake * 0.5 + walk * wc.head_bob * 0.6, 0.0)))

    # legs: standing (waddle) <-> seated (thighs along the seat, shins dangling and swinging)
    feet = []
    u_feet = smooth((sit - 0.45) / 0.55)
    kick = clamp(pose.kick)
    out = clamp(pose.legs_out)
    lap = {}
    for s in (-1.0, 1.0):
        hip = v_add(pel, m_vec(R, (s * HIP_W, 5.0, 0.0)))
        fz, lift, toe, _planted = wc.feet[0 if s < 0 else 1]
        stand_ank = (s * (HIP_W + 1.0) + stand_pel[0] * 0.3, -ANKLE_H - lift * walk, fz * walk + 1.0)
        sw = (0.16 + kick * 0.5 * math.sin(t * TAU * 0.95 + (0.0 if s < 0 else math.pi))
              + 0.07 * math.sin(t * 0.8 + s * 1.3 + pose.seed))
        sw = lerp(sw, 1.4 + 0.06 * math.sin(t * 1.1 + s), out)
        knee_s = v_add(pel, (s * (HIP_W + 1.0), 4.0, THIGH * 0.97))
        seat_ank = v_add(knee_s, (s * 1.0, SHIN * math.cos(sw), SHIN * math.sin(sw)))
        ankle = v_lerp(stand_ank, seat_ank, u_feet)
        knee, ank = B.ik3(hip, ankle, THIGH, SHIN, (s * 0.12, lerp(0.1, -0.9, k), 1.0))
        # foot pitch (+ toe up): walking roll-over, seated a relaxed droop (or up when legs stick out)
        pitch = lerp(toe * walk, lerp(-0.35 + 0.35 * (sw - 0.16), 1.15, out), u_feet)
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "pitch": pitch, "side": s})
        lap[s] = v_add(v_lerp(hip, knee, 0.55), (0.0, -11.0, 0.0))
    S["feet"] = feet
    S["knee"] = {-1.0: feet[0]["knee"], 1.0: feet[1]["knee"]}
    # the screen-facing direction in body space (3/4 right: forward and toward her left)
    fwd = K.facing_dir(yaw)
    S["ctx"] = {"sit_k": k, "waist": S["waist"], "chest": S["chest"], "lap": lap, "pelvis": pel,
                "phase": 0.0, "satchel_mouth": (0.0, 0.0, 0.0), "fwd": fwd}
    return S


def _solve_arm(q, S, side, arm):
    sk = S["shoulders"][side]
    c = dict(S["ctx"], phase=arm.phase)
    tgt, hp, hang, z = GNOME_GESTURES.get(arm.gesture, _g_rest)(sk, side, c)
    if arm.amt < 1.0:
        t0, hp0, ha0, z0 = GNOME_GESTURES.get(arm.prev, _g_rest)(sk, side, dict(c, phase=0.0))
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 6.0           # hands travel on an arc, never in a straight line
        tgt = v_add(v_lerp(t0, tgt, u), (side * arc * 0.5, -arc * 0.5, arc))
        hang = lerp(ha0, hang, u)
        if u < 0.5:
            hp = hp0
    if arm.target is not None:
        tgt = arm.target
    if arm.screen is not None:
        tgt = K.screen_to_body(q, q.proj, arm.screen, q.proj.depth(sk) + arm.depth)
    if arm.hand:
        hp = arm.hand
    if arm.gesture == "rest" and q.sit < SIT_SWAP:
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"]
        tgt = v_add(tgt, (side * abs(sw) * 4.0, -abs(sw) * 3.0, sw * 7.0))
    if arm.gesture in ("rest", "hold_bread", "hand_on_chest"):
        tgt = v_add(tgt, (0.0, S["shake"] * 0.7, 0.0))
    if arm.gesture in ("hand_on_chest", "rest"):
        pole = (side * 1.0, 0.6, -0.1)
    elif arm.gesture == "tear_bread":
        pole = (side * 1.0, 0.9, -0.2)
    else:
        pole = (side * 0.9, 0.8, -0.35)
    elbow, wrist = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side}


# ----------------------------------------------------------------------------------------
# arms + hands
# ----------------------------------------------------------------------------------------

def _bread_hold(q, state, inward, size=GNOME_LOAF):
    """A hold callback drawing her own bread upright in the hand, torn face toward `inward`."""
    light, detail = q.light, q.detail

    def draw(cr, f):
        cr.save()
        cr.rotate(-f.angle)
        if state == "piece":
            gnome_bread(cr, inward * 3.0, -3.0, size, light, "piece", face=inward, detail=detail, seed=3)
        elif state == "half":
            gnome_bread(cr, inward * size * 0.16, -size * 0.12, size, light, "half", face=inward, detail=detail)
        else:
            gnome_bread(cr, inward * size * 0.3, -size * 0.18, size, light, "loaf", detail=detail)
        cr.restore()
    return draw


def _arm(q, A, side, parts="all", hold=True, hold_cb=None):
    """Sleeve + cuff + hand. parts: "upper" (shoulder -> elbow, drawn under the shawl's cape),
    "lower" (elbow -> wrist, cuff and hand, over it) or "all"."""
    cr, proj, M = q.cr, q.proj, q.M
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    arm = A["arm"]
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    if parts == "upper":            # mostly under the shawl's cape and in its shadow: one flat tone
        s_, o_ = _caps(cr, [sh, el], [8.6, 7.6], q.lw)
        _flat(q, s_, o_, M["sleeve"], tone=0.55)
        return None
    spine = [sh, el, wr] if parts == "all" else [el, wr]
    radii = [8.6, 7.6, 6.4] if parts == "all" else [7.6, 6.4]
    s_, o_ = _caps(cr, spine, radii, q.lw)
    pal = q.shade(s_, M["sleeve"], outline=o_, size=15, rim=0.6)
    if q.detail >= 2:                                # crease on the inside of the elbow
        nx, ny = -fdy, fdx
        bend = (el[0] - sh[0]) * (wr[1] - el[1]) - (el[1] - sh[1]) * (wr[0] - el[0])
        sg = 1.0 if bend > 0 else -1.0
        B.detail_lines(cr, [[(el[0] + nx * 3.0 * sg - fdx * 3, el[1] + ny * 3.0 * sg - fdy * 3),
                             (el[0] + nx * 6.5 * sg + fdx * 2, el[1] + ny * 6.5 * sg + fdy * 2)]],
                       q.lw * 0.75, pal.line, 0.5)
    # ribbed knit cuff
    cx_, cy_ = wr[0] - fdx * 1.5, wr[1] - fdy * 1.5
    cuff, cout = B.ellipse_paths(cr, cx_, cy_, 4.4, 7.4, q.lw, ang)
    cp = _flat(q, cuff, cout, M["cuff"])
    if q.micro:
        nx, ny = -fdy, fdx
        B.detail_lines(cr, [[(cx_ + nx * 5.2 * k2 - fdx * 2.5, cy_ + ny * 5.2 * k2 - fdy * 2.5),
                             (cx_ + nx * 5.2 * k2 + fdx * 2.5, cy_ + ny * 5.2 * k2 + fdy * 2.5)]
                            for k2 in (-0.6, 0.0, 0.6)], q.lw * 0.5, cp.line, 0.45)
    hp = A["hand"]
    hang = ang + A["hang"] * (1 if side < 0 else -1) * (1 if q.yaw >= 0 else -1)
    flip = (side > 0) == (q.yaw >= 0)
    show_palm = hp in ("open", "offer") and arm.gesture in ("hand_out_offer", "wave")
    cb = None
    if hold:
        cb = hold_cb or arm.hold
        if cb is None and arm.bread:
            inward = 1.0 if wr[0] < proj.xy(q.S["chest"])[0] else -1.0
            if arm.gesture == "hand_out_offer":
                inward = -inward
            cb = _bread_hold(q, arm.bread, inward)
    return B.hand(cr, wr[0] + fdx * 2.0, wr[1] + fdy * 2.0, hang, HAND_LEN, hp, M["skin"], q.light_nb, q.lw,
                  flip=flip, claw=None, show_palm=show_palm, pad=GNOME_COLORS["nose"], hold=cb,
                  finger_w=1.32, finger_len=0.84, palm_w=1.2, detail=q.detail)


def _tear_bread(q, A0, A1):
    """Both hands on the loaf (tear_bread): before the snap the whole loaf sits between the grips
    with a widening crack; after it each hand holds a half, torn faces toward each other."""
    ph = A0["arm"].phase
    what = A0["arm"].bread or A1["arm"].bread or "loaf"
    cr, proj = q.cr, q.proj
    grips = []
    for A in (A0, A1):
        el, wr = proj.xy(A["el"]), proj.xy(A["wr"])
        fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
        grips.append((wr[0] + fdx * 9.0, wr[1] + fdy * 9.0))
    mx, my = (grips[0][0] + grips[1][0]) / 2, (grips[0][1] + grips[1][1]) / 2
    size = GNOME_LOAF if what == "loaf" else GNOME_LOAF * 0.7
    if ph < 0.5:
        crack = smooth(clamp((ph - 0.25) / 0.25))
        # whole: the loaf sits between the grips, then both forearms + hands go over it
        if what == "loaf":
            gnome_bread(cr, mx, my - 2.0, size, q.light, "loaf", crack=crack, detail=q.detail, lw=q.lw)
        else:
            gnome_bread(cr, mx, my - 2.0, size * 1.4, q.light, "half", face=1.0, detail=q.detail, lw=q.lw)
        f0 = _arm(q, A0, A0["side"], parts="lower", hold=False)
        f1 = _arm(q, A1, A1["side"], parts="lower", hold=False)
        return f0, f1, (mx, my - 6.0)
    out = []
    for A in (A0, A1):
        g = grips[0] if A is A0 else grips[1]
        inward = 1.0 if g[0] < mx else -1.0
        state = "half" if what == "loaf" else ("half" if A is A0 else "piece")
        cb = _bread_hold(q, state, inward, size)
        out.append(_arm(q, A, A["side"], parts="lower", hold_cb=cb))
    return out[0], out[1], (mx, my - 6.0)


# ----------------------------------------------------------------------------------------
# legs, skirt, shawl, satchel
# ----------------------------------------------------------------------------------------

def _boot_pts(q, f):
    """Boot hull points: an ankle cuff, heel, ball and a little upturned toe, pitched about the
    ankle (toe up +)."""
    proj = q.proj
    a = f["ankle"]
    pc, ps = math.cos(f["pitch"]), math.sin(f["pitch"])

    def F(dx, dy, dz):     # dy down from the ankle, dz forward; rotate in the y-z plane
        return proj.xy((a[0] + dx, a[1] + dy * pc - dz * ps, a[2] + dy * ps + dz * pc))

    pts = []
    for k in range(6):
        ang = TAU * k / 6
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append(F(ca * 6.6, -3.0 + sa * 1.2, sa * 6.0))                  # cuff
        pts.append(F(ca * 5.6, ANKLE_H - 4.5 + sa * 4.0, -3.5 + sa * 1.5))  # heel
        pts.append(F(ca * 6.2, ANKLE_H - 4.0 + sa * 4.0, 7.5))              # ball of the foot
    pts += [F(0.0, ANKLE_H - 6.5, 13.5), F(-2.6, ANKLE_H - 5.0, 12.5), F(2.6, ANKLE_H - 5.0, 12.5),
            F(0.0, ANKLE_H - 8.5, 15.0)]                                     # the upturned toe
    return pts, F


def _legs(q):
    """Both legs: the two wool stockings as one union, then the two little laced boots as one
    union (one outline + one shading pass each; the details are batched)."""
    cr, proj, M, S = q.cr, q.proj, q.M, q.S
    seated = q.sit >= SIT_SWAP
    lw = q.lw
    tubes = []
    for f in S["feet"]:
        kn, an = proj.xy(f["knee"]), proj.xy(f["ankle"])
        spine = [kn, an] if seated else [proj.xy(f["hip"]), kn, an]
        tubes.append(_caps(cr, spine, [6.4, 5.4] if seated else [7.5, 6.6, 5.4], lw))
    cr.new_path()                     # dark wool, mostly under the skirt: one flat union
    for _sh, o_ in tubes:
        o_.add(cr)
    sp_ = q.P(M["stocking"])
    core.src(cr, sp_.line)
    cr.fill()
    for sh_, _o in tubes:
        sh_.add(cr)
    core.src(cr, core.mix(sp_.lit, sp_.shadow, 0.3))
    cr.fill()
    hulls, Fs = [], []
    for f in S["feet"]:
        pts, F = _boot_pts(q, f)
        hulls.append(core.convex_hull(pts))
        Fs.append(F)
    path = _union(q, hulls, M["boot"], size=12, rim=0.6)
    bp = q.P(M["boot"])
    if q.detail >= 1:
        cr.save()
        path.add(cr)
        cr.clip()
        cr.new_path()                    # the soles: a darker slab along the bottom of each boot
        for F in Fs:
            core.polygon(cr, core.convex_hull([F(x_, y_, z_) for x_ in (-8.0, 8.0) for y_ in (ANKLE_H - 2.4, ANKLE_H + 1.5)
                                               for z_ in (-10.0, 19.0)]))
        core.src(cr, core.mix(bp.shadow, (0.12, 0.07, 0.05), 0.45))
        cr.fill()
        for F in Fs:                     # the folded cuffs at the tops
            core.polygon(cr, core.convex_hull([F(math.cos(a_) * 6.9, -2.2, math.sin(a_) * 6.3) for a_ in (0.0, 1.05, 2.1, 3.14, 4.2, 5.25)]
                                              + [F(-6.5, -0.4, 0.0), F(6.5, -0.4, 0.0), F(0.0, -0.4, 6.0), F(0.0, -0.4, -6.0)]))
        core.src(cr, core.mix(bp.lit, bp.hi, 0.25))
        cr.fill()
        cr.restore()
        if q.micro and proj.depth((0.0, 0.0, 1.0)) > -0.2:     # criss-cross laces
            lines = []
            for F in Fs:
                for dy in (1.5, 4.5):
                    lines.append([F(-2.6, dy - 1.2, 6.2), F(2.6, dy + 1.2, 6.4)])
                    lines.append([F(2.6, dy - 1.2, 6.2), F(-2.6, dy + 1.2, 6.4)])
            cr.new_path()
            for ln_ in lines:
                core.polygon(cr, ln_, close=False)
            cr.set_line_width(lw * 0.5)
            core.src(cr, bp.line, 0.7)
            cr.stroke()
        for F in Fs:
            B.sheen(cr, *F(0.0, ANKLE_H - 6.5, 11.0), 3.5, 2.0, alpha=0.25)


def _skirt(q):
    if q.sit >= SIT_SWAP:
        return _skirt_seated(q)
    cr, proj, S, t = q.cr, q.proj, q.S, q.t
    T, pel = S["T"], S["pelvis"]
    walk = S["walk"]
    sw = walk * math.sin(TAU * S["wc"].phase * 2.0) * 1.8 + 0.7 * math.sin(t * 1.3 + q.pose.seed)
    k = S["sit_k"]
    rings = [(T((0.0, -13.5, 1.0)), 19.5, 16.5),
             (v_add(pel, (0.0, -1.0, 0.0)), 27.5, 23.5),
             (v_add(pel, (sw * 0.4, 23.0, -0.5 + 6 * k)), 36.0 - 4 * k, 31.0),
             (v_add(pel, (sw, 42.0 - 14 * k, -1.0 - walk * 2.0 + 14 * k)), 42.5 + walk * 2.0 - 8 * k, 37.0 - 4 * k)]
    left, right = [], []
    for (c, a, cz) in rings:
        x, y, hw = proj.ellipse(c, a, cz)
        left.append((x - hw, y))
        right.append((x + hw, y))
    cH, aH, czH = rings[-1]
    ring = [proj((cH[0] + math.sin(TAU * i / 24) * aH, cH[1], cH[2] + math.cos(TAU * i / 24) * czH)) for i in range(24)]
    hem = []
    xL, xR = left[-1][0], right[-1][0]
    for i in range(1, 9):
        xx = lerp(xL, xR, i / 9)
        best = None
        for j in range(24):               # lowest crossing of the hem ring = the near edge
            pa, pb = ring[j], ring[(j + 1) % 24]
            if (pa[0] - xx) * (pb[0] - xx) <= 0 and pa[0] != pb[0]:
                yy = pa[1] + (pb[1] - pa[1]) * (xx - pa[0]) / (pb[0] - pa[0])
                best = yy if best is None else max(best, yy)
        if best is not None:
            hem.append((xx, best + 1.3 * math.sin(i * 2.3 + t * 1.6) * (0.5 + walk)))
    c0, a0, cz0 = rings[0]
    x0, y0, hw0 = proj.ellipse(c0, a0, cz0)
    top = [(x0 - hw0 * 0.7, y0 - 3.0), (x0, y0 - 4.5), (x0 + hw0 * 0.7, y0 - 3.0)]
    pts = left + hem + right[::-1] + top[::-1]
    sk, so = B.smooth_paths(cr, pts, q.lw, 0.8)
    pal = q.shade(sk, q.M["skirt"], outline=so, size=60, shadow=0.7, bounce=1.0)
    if q.detail >= 1:                     # an embroidered band along the hem
        cr.save()
        sk.add(cr)
        cr.clip()
        band = [(x_, y_ - 7.0) for x_, y_ in hem]
        cr.new_path()
        core.polygon(cr, [(xL - 4, left[-1][1] - 7.0)] + band + [(xR + 4, right[-1][1] - 7.0), (xR + 4, 1e3), (xL - 4, 1e3)])
        core.src(cr, core.mix(pal.shadow, pal.lit, 0.25))
        cr.fill()
        if q.micro:
            fl = q.P(Mat.of("#EADFC3"))
            dots = []
            for i in range(1, len(hem) - 1):
                x_, y_ = hem[i]
                dots.append((lerp(x_, hem[i + 1][0], 0.5), (y_ + hem[i + 1][1]) * 0.5 - 3.6))
            core.src(cr, fl.lit)
            for (x_, y_) in dots:
                for k2 in range(4):
                    a2 = TAU * k2 / 4 + 0.4
                    core.circle(cr, x_ + math.cos(a2) * 1.3, y_ + math.sin(a2) * 1.3, 0.95)
            cr.fill()
            core.src(cr, GNOME_COLORS["hood"])
            for (x_, y_) in dots:
                core.circle(cr, x_, y_, 0.75)
            cr.fill()
        cr.restore()
    if q.detail >= 1:                     # a few soft folds falling from the hips
        cr.save()
        sk.add(cr)
        cr.clip()
        cW, aW, czW = rings[1]
        lines = []
        for phi in (-1.1, -0.35, 0.4, 1.15):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.15:
                continue
            A2 = proj.xy((cW[0] + math.sin(phi) * aW * 0.9, cW[1] + 10.0, cW[2] + math.cos(phi) * czW * 0.9))
            B2 = proj.xy((cH[0] + math.sin(phi * 1.05) * aH * 0.97, cH[1] - 1.0, cH[2] + math.cos(phi * 1.05) * czH * 0.97))
            lines.append([A2, ((A2[0] + B2[0]) / 2 + 1.5 * math.sin(phi * 3 + t), (A2[1] + B2[1]) / 2), B2])
        if lines:
            B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.45, taper=(0.05, 0.8, 1.0))
        cr.restore()


def _skirt_seated(q):
    """Seated: ONE union of the seat mass, the lap over both thighs and the drape hanging off the
    knees (her shins and boots dangle below the hem)."""
    cr, proj, S, t = q.cr, q.proj, q.S, q.t
    T, pel = S["T"], S["pelvis"]
    xy = proj.xy
    sway = 0.8 * math.sin(t * 1.2 + q.pose.seed)
    kns = S["knee"]
    hips = B.ellipsoid_pts(xy, v_add(pel, (0.0, 2.0, -3.0)), 27.5, 9.0, 23.0, 10)
    waist = B.ellipsoid_pts(xy, T((0.0, -12.5, 1.0)), 20.0, 4.0, 17.0, 8)
    knees, drape = [], []
    for s in (-1.0, 1.0):
        kn = kns[s]
        knees += B.ellipsoid_pts(xy, v_add(kn, (s * 0.5, -1.5, 3.0)), 12.5, 10.5, 11.0, 8)
        for i in range(10):
            a = TAU * i / 10
            drape.append(xy(v_add(kn, (s * 1.5 + math.cos(a) * 13.0 + sway, 15.0 + 1.5 * math.sin(a * 2 + s),
                                       3.0 + math.sin(a) * 11.5))))
    hulls = [core.convex_hull(hips + waist), core.convex_hull(hips + knees), core.convex_hull(knees + drape)]
    path = _union(q, hulls, q.M["skirt"], size=46, shadow=0.75, rim=0.8, bounce=1.0)
    if q.detail < 1:
        return
    pal = q.P(q.M["skirt"])
    cr.save()
    path.add(cr)
    cr.clip()
    km = v_lerp(kns[-1.0], kns[1.0], 0.5)
    soft = []
    # the hammock between the knees and the folds hanging off them
    soft.append([xy(v_add(kns[-1.0], (6.0, -6.0, 10.0))), xy(v_add(km, (sway, 4.0, 12.0))), xy(v_add(kns[1.0], (-6.0, -6.0, 10.0)))])
    for s in (-1.0, 1.0):
        a = xy(v_add(kns[s], (s * 3.0, 4.0, 13.0)))
        b = xy(v_add(kns[s], (s * 4.0 + sway, 15.5, 13.0)))
        soft.append([a, ((a[0] + b[0]) / 2 + 1.0, (a[1] + b[1]) / 2), b])
    B.detail_lines(cr, soft, q.lw * 0.85, pal.line, 0.45, taper=(0.1, 1.0, 0.2))
    cr.restore()


def _shawl(q):
    """The lavender knitted shawl draped over her shoulders like a little cape (it covers the
    upper arms), knotted at the front."""
    cr, proj, S = q.cr, q.proj, q.S
    T = S["T"]
    xy = proj.xy
    br = S["br"]
    sh_y = S["sh_y"]
    collar = B.ellipsoid_pts(xy, T((0.0, sh_y - 4.0, 1.5)), 13.5, 3.0, 12.5, 8)
    shoulder = B.ellipsoid_pts(xy, T((0.0, sh_y + 3.0, -0.5)), 29.0 + 0.4 * br, 5.0, 23.0, 10)
    edge = []
    for i in range(16):
        a = TAU * i / 16
        sa, ca = math.sin(a), math.cos(a)
        y = -13.0 + 4.0 * max(0.0, ca) ** 2 - 1.5 * max(0.0, -ca)    # dips to a point at the front
        edge.append(xy(T((sa * (32.5 + 0.5 * br), y, 1.5 + ca * 26.5))))
    hull = core.convex_hull(collar + shoulder + edge)
    sh, so = B.smooth_paths(cr, hull, q.lw, 0.85)
    pal = q.shade(sh, q.M["shawl"], outline=so, size=34, shadow=0.85)
    front = proj.depth(m_vec(S["R"], (0.0, 0.0, 1.0)))
    if q.detail >= 1:
        cr.save()
        sh.add(cr)
        cr.clip()
        # knitted border along the lower edge (a darker band) + rib lines radiating from the neck
        cr.new_path()
        lo = [xy(T((math.sin(a) * 33.0, -13.0 + 4.0 * max(0.0, math.cos(a)) ** 2, 1.5 + math.cos(a) * 27.0)))
              for a in [TAU * i / 24 for i in range(24)]]
        hi = [xy(T((math.sin(a) * 31.0, -17.5 + 4.0 * max(0.0, math.cos(a)) ** 2, 1.5 + math.cos(a) * 25.5)))
              for a in [TAU * i / 24 for i in range(24)]]
        for i in range(24):
            j = (i + 1) % 24
            ai, aj = TAU * i / 24, TAU * j / 24
            if proj.depth((math.sin(ai), 0.0, math.cos(ai))) < -0.1 and proj.depth((math.sin(aj), 0.0, math.cos(aj))) < -0.1:
                continue
            core.polygon(cr, [lo[i], lo[j], hi[j], hi[i]])
        core.src(cr, core.mix(pal.shadow, pal.lit, 0.35), 0.75)
        cr.fill()
        if q.micro:
            # knitted texture: two rows of little V stitches just above the border band
            vs = []
            for row, (yy, rr) in enumerate(((-21.5, 30.0), (-26.5, 27.5))):
                for i in range(15):
                    a = -1.4 + 2.8 * (i + 0.5 * row) / 14
                    if proj.depth((math.sin(a), 0.0, math.cos(a))) < 0.1:
                        continue
                    c = xy(T((math.sin(a) * rr, yy + 3.0 * max(0.0, math.cos(a)) ** 2, 1.5 + math.cos(a) * rr * 0.82)))
                    vs.append([(c[0] - 1.6, c[1] - 1.4), (c[0], c[1] + 0.9), (c[0] + 1.6, c[1] - 1.4)])
            cr.new_path()
            for v_ in vs:
                core.polygon(cr, v_, close=False)
            cr.set_line_width(q.lw * 0.4)
            core.src(cr, pal.line, 0.35)
            cr.stroke()
        cr.restore()
    if front > 0.15:
        # the knot at her chest and its two short ends: ONE union (tubes wound like ellipses)
        kc = T((0.0, sh_y + 8.0, 24.0))
        k0 = xy(v_add(kc, (0.0, 1.0, 0.0)))
        pieces = [_tube(cr, [k0, xy(T((-4.0, -11.0, 26.5))), xy(T((-6.5, -4.0, 26.5)))], [3.5, 3.0, 2.0], q.lw, samples=3),
                  _tube(cr, [k0, xy(T((3.5, -12.0, 26.5))), xy(T((5.5, -6.0, 26.0)))], [3.5, 3.0, 2.0], q.lw, samples=3)]
        kxy = xy(kc)
        pieces.append(B.ellipse_paths(cr, kxy[0], kxy[1], 5.6, 4.6, q.lw))
        cr.new_path()                 # a small knot on the shawl: one flat union, a shade lighter
        for _sh, o_ in pieces:
            o_.add(cr)
        core.src(cr, pal.line)
        cr.fill()
        for sh_, _o in pieces:
            sh_.add(cr)
        core.src(cr, core.mix(pal.lit, pal.hi, 0.15))
        cr.fill()
        if q.detail >= 1:
            B.detail_lines(cr, [[(kxy[0] - 3.0, kxy[1] - 1.5), (kxy[0], kxy[1] + 0.5), (kxy[0] + 3.0, kxy[1] - 1.5)]],
                           q.lw * 0.7, pal.line, 0.6)


def _satchel_frame(q):
    """Where the satchel sits: on her right hip standing, beside her on the seat when sitting."""
    S = q.S
    side = q.pose.satchel_side
    k = S["sit_k"]
    stand_c = S["T"]((side * 22.0, 9.0, 9.0))
    seat_c = v_add(S["pelvis"], (side * 33.0, SEAT_DY - 10.5, 2.0))
    c = v_lerp(stand_c, seat_c, k)
    return {"c": c, "mouth": v_add(c, (0.0, -9.0, 0.0)), "side": side}


def _satchel(q):
    """The linen satchel (her loaf peeks out of it), with a flap and a wooden toggle."""
    cr, proj, M = q.cr, q.proj, q.M
    fr = _satchel_frame(q)
    c, side = fr["c"], fr["side"]
    xy = proj.xy
    th = side * 0.6                              # broad face turned toward the front-side
    ux, uz = math.cos(th), -math.sin(th)
    nx, nz_ = math.sin(th), math.cos(th)

    def Bp(u, v, w):
        return xy((c[0] + u * ux + w * nx, c[1] + v, c[2] + u * uz + w * nz_))

    if q.pose.satchel == "loaf":
        lt = Bp(0.0, -9.5, 0.0)
        gnome_bread(cr, lt[0], lt[1], 30.0, q.light, "loaf", detail=q.detail, lw=q.lw)
    pts = []
    for i in range(14):
        a = TAU * i / 14
        u, v = math.cos(a) * 12.5, math.sin(a) * 10.0
        u = math.copysign(min(abs(u), 11.5), u)
        for w in (-4.0, 4.5):
            pts.append(Bp(u, v + (1.0 if v > 0 else 0.0), w * (1.0 - 0.3 * abs(math.sin(a)))))
    hull = core.convex_hull(pts)
    sh, so = B.smooth_paths(cr, hull, q.lw, 0.85)
    q.shade(sh, M["satchel"], outline=so, size=18)
    front = proj.depth((nx, 0.0, nz_))
    if front > -0.2:
        # the flap over the top half of the bag
        flap = [Bp(-12.0, -9.0, 4.4), Bp(12.0, -9.0, 4.4), Bp(11.5, -2.0, 5.0), Bp(6.0, 2.5, 5.2),
                Bp(0.0, 3.6, 5.3), Bp(-6.0, 2.5, 5.2), Bp(-11.5, -2.0, 5.0)]
        fsh, fso = B.smooth_paths(cr, flap, q.lw * 0.8, 0.7)
        cr.save()
        sh.add(cr)
        cr.clip()
        fp = _flat(q, fsh, fso, M["flap"])
        cr.restore()
        tg = Bp(0.0, 3.0, 5.6)
        ts, to = B.ellipse_paths(cr, tg[0], tg[1], 2.0, 3.6, q.lw * 0.6, 0.0)
        _flat(q, ts, to, M["toggle"])
        if q.micro:                          # stitching along the flap
            B.detail_lines(cr, [[Bp(-10.0, -1.5, 5.2), Bp(-5.0, 1.0, 5.4), Bp(0.0, 1.8, 5.4), Bp(5.0, 1.0, 5.4), Bp(10.0, -1.5, 5.2)]],
                           q.lw * 0.45, fp.line, 0.5)
    return xy(c)


def _strap(q):
    """The satchel strap across her chest, from the opposite shoulder."""
    cr, proj, S = q.cr, q.proj, q.S
    T = S["T"]
    side = q.pose.satchel_side
    front = proj.depth(m_vec(S["R"], (0.0, 0.0, 1.0)))
    if front < -0.1:
        return
    fr = _satchel_frame(q)
    k = S["sit_k"]
    pts3 = [T((-side * 17.0, S["sh_y"] - 1.0, 9.0)), T((-side * 6.0, S["sh_y"] + 10.0, 24.0)),
            T((side * 10.0, -10.0, 24.5)), v_lerp(T((side * 19.0, 1.0, 14.0)), v_add(fr["c"], (side * -6.0, -9.0, 3.0)), k)]
    pts = [proj.xy(p) for p in pts3]
    s_, o_ = B.taper_paths(cr, pts, 4.2, 4.2, q.lw * 0.7)
    _flat(q, s_, o_, q.M["strap"])


# ----------------------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------------------

def _expr(pose):
    e = B.expr(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    if pose.laugh > 0:
        e = e.blend(B.MOODS["laugh"], pose.laugh)
    if pose.specs > 0:              # peering over the spectacles: brows up, lids open
        e = e.blend(e.with_(brow_y=max(e.brow_y, 0.35), brow_asym=max(e.brow_asym, 0.35), lid=min(e.lid, 0.12)), pose.specs)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    return e


def _auto_glint(t, seed):
    """An occasional glint sweeping across her spectacles (every ~6-10 s), else -1."""
    cell = 8.0
    k = math.floor(t / cell)
    start = k * cell + 1.0 + core.hash01(k, seed + 31) * (cell - 2.5)
    u = (t - start) / 0.4
    return u if 0.0 <= u <= 1.0 else -1.0


def _cone_spine(q, hood_swing):
    """The hood's long tip (head space): up and back from the crown, then flopping over toward
    her left and down. Chain sway, laugh bounce and the scene's follow-through drive it."""
    t, pose = q.t, q.pose
    laugh = clamp(pose.laugh)
    sw = B.chain(t, 5, freq=0.36, delay=0.17, amp=0.55 + 0.9 * laugh, seed=pose.seed + 21, grow=2.6)
    bounce = laugh * 0.1 * math.sin(t * TAU * 2.6)
    p = (0.0, -24.0, -11.0)
    pts = [p]
    lens = (16.0, 14.0, 12.0, 10.0)
    theta, phi = 0.32 - 0.25 * hood_swing, 0.18 + 0.4 * hood_swing
    for i, L in enumerate(lens):
        theta += 0.42 + 0.5 * sw[i + 1] * 0.5 + bounce * (i + 1) * 0.5 - 0.05 * pose.head_nod
        phi += 0.14 + sw[i + 1] * 0.8 + 0.1 * hood_swing
        d = (math.sin(phi) * math.sin(min(theta, 1.6)) * 0.9, -math.cos(theta), -math.sin(theta) * math.cos(phi))
        p = v_add(p, (d[0] * L, d[1] * L, d[2] * L))
        pts.append(p)
    return pts


def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH, HC = S["RH"], S["head_c"]
    e = _expr(pose)
    lw = q.lw
    hyaw = q.yaw + S["head_yaw"]           # effective head yaw (incl. the 3/4 cheat)
    near = -1.0 if hyaw >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    open_ = clamp(max(talk * 0.85, e.open))
    xy = proj.xy

    def P(v):
        w = m_vec(RH, v)
        return xy((HC[0] + w[0], HC[1] + w[1], HC[2] + w[2]))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    skin = q.P(M["skin"])
    hood = q.P(M["hood"])
    hair = q.P(M["hair"])

    # ---- the bun, peeking out under the back of the hood
    bcx, bcy = P((0.0, 17.0, -27.0))
    bsh, bso = B.ellipse_paths(cr, bcx, bcy, 9.4, 9.0, lw)
    if q.detail >= 2:
        q.shade(bsh, M["hair"], outline=bso, size=16, rim=0.0)
    else:
        _flat(q, bsh, bso, M["hair"], tone=0.25)
    if q.detail >= 1 and nz((0.0, 0.2, -1.0)) > -0.2:
        bc = P((0.0, 17.0, -31.0))
        B.detail_lines(cr, [[(bc[0] - 5, bc[1] - 3), (bc[0] - 1, bc[1] - 5.5), (bc[0] + 4, bc[1] - 2.5)],
                            [(bc[0] - 4, bc[1] + 2.5), (bc[0] + 1, bc[1] + 4.5), (bc[0] + 5, bc[1] + 1)]],
                       lw * 0.6, hair.line, 0.55)

    # ---- the hood: dome + the drape round her neck + the long tip, ONE union
    dc = P(DOME_C)
    dome = _circle_pts(dc, 29.2, 16, sy=1.02)
    drape = [P((math.sin(a) * 24.5, 17.0 + 8.0 * math.cos(a), -6.0 + math.cos(a) * 19.0))
             for a in (TAU * i / 8 for i in range(8))]
    cone3 = _cone_spine(q, pose.hood_swing)
    cone = [P(p) for p in cone3]
    hull = core.convex_hull(dome + drape)
    cs, co = _tube(cr, cone, [15.0, 10.5, 7.0, 4.7, 3.1], lw)
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(hull, lw), 0.85)
    co.add(cr)
    core.src(cr, hood.line)
    cr.fill()
    core.smooth_closed(cr, hull, 0.85)
    cs.add(cr)
    q.shade(Path(cr), M["hood"], outline=False, size=58, shadow=0.9, rim=0.3)
    if q.detail >= 1:                               # soft folds where the tip leaves the crown
        cr.save()
        cs.add(cr)
        cr.clip()
        B.detail_lines(cr, [[cone[0], core.lerp_pt(cone[0], cone[1], 0.55), core.lerp_pt(cone[1], cone[2], 0.4)]],
                       lw * 0.8, hood.line, 0.35)
        cr.restore()
    # the tassel at the tip (hidden when the tip flops behind her head)
    tip3 = cone3[-1]
    tip = cone[-1]
    tip_hidden = nz((tip3[0] / 40.0, tip3[1] / 40.0, tip3[2] / 40.0)) < -0.25 and _inside(hull, tip)
    if not tip_hidden:
        prev = cone[-2]
        ta = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        tx_, ty_ = tip[0] + math.cos(ta) * 2.5, tip[1] + math.sin(ta) * 2.5 + 2.0
        ts, to = B.ellipse_paths(cr, tx_, ty_, 4.6, 4.0, lw * 0.8)
        tp = _flat(q, ts, to, M["tassel"])
        if q.micro:
            B.detail_lines(cr, [[(tx_ - 2.2, ty_ + 1.0), (tx_ - 2.8, ty_ + 5.5)], [(tx_ + 0.2, ty_ + 1.5), (tx_ + 0.3, ty_ + 6.2)],
                                [(tx_ + 2.4, ty_ + 1.0), (tx_ + 3.2, ty_ + 5.2)]], lw * 0.6, tp.line, 0.7)

    # ---- the hood's soft hem framing her face: the whole band first (the face will hide its
    # far run behind the far cheek), the near run again over the face further down
    arch = [P(a) for a in ARCH]
    vis = [nz(_unit3(a)) for a in ARCH]
    if min(vis) < -0.2:
        bs, bo = _hem(cr, arch, lw)
        _flat(q, bs, bo, M["lining"])

    # ---- the face: a big round face with plump cheeks and a soft chin, clipped to the hood's
    # opening above the jaw line (below it the hood falls behind her jowls)
    face3 = []
    for i in range(8):
        a = TAU * i / 8
        ca, sa = math.cos(a), math.sin(a)
        face3 += [(FACE_C[0] + ca * FACE_R[0], FACE_C[1] + sa * FACE_R[1], FACE_C[2]),
                  (FACE_C[0] + ca * FACE_R[0], FACE_C[1], FACE_C[2] + sa * FACE_R[2]),
                  (FACE_C[0], FACE_C[1] + ca * FACE_R[1], FACE_C[2] + sa * FACE_R[2])]
    face2 = [P(v) for v in face3]
    for s in (-1.0, 1.0):
        face2 += _circle_pts(P((s * 14.5, 11.0, 12.0)), 10.2, 8)                  # cheeks
        face2 += _circle_pts(P((s * 11.5, 17.5 + open_ * 1.5, 7.5)), 9.8, 8)      # jowls
        face2 += _circle_pts(P((s * 3.5, 21.5 + open_ * 2.5, 9.5)), 8.6, 8)       # chin
    fhull = core.convex_hull(face2)
    front = [P(v) for v in face3 if v[2] > 1.0] + [P((0.0, 0.0, 26.0)), P((0.0, 12.0, 24.0))]
    opening = core.convex_hull(arch + front)
    # below the jaw corners the face is free (the hood falls behind the jowls), but only
    # between them: behind the jaw corner the hood wraps the back of her head and neck
    le, re_ = sorted((arch[0], arch[-1]))
    below = core.convex_hull([le, re_, (re_[0] + 5.0, re_[1] + 120.0), (le[0] - 5.0, le[1] + 120.0)])
    cr.save()
    cr.new_path()
    core.polygon(cr, opening)
    core.polygon(cr, below)
    cr.clip()
    fsh, fso = B.smooth_paths(cr, fhull, lw, 0.85)
    q.shade(fsh, M["skin"], outline=fso, size=40, shadow=0.8)
    # rosy cheeks
    for s in (far, near):
        fz = nz((s * 0.6, 0.35, 0.72))
        if fz < -0.15:
            continue
        bc = P((s * 15.5, 10.5 - 1.5 * e.cheek, 17.5))
        r = 7.8 * (0.65 + 0.35 * clamp(fz + 0.3)) * (1.0 + 0.12 * e.cheek)
        B.sheen(cr, bc[0], bc[1], r, r * 0.78, alpha=0.48 + 0.2 * clamp(e.cheek), color=GNOME_COLORS["blush"])
    cr.restore()

    # ---- ink: kind wrinkles (smile lines, crow's feet)
    if q.detail >= 1:
        lines, crows = [], []
        sm = clamp(e.smile + 0.5 * pose.smirk, -1.0, 1.0)
        for s in (far, near):
            if nz((s * 0.5, 0.3, 0.8)) < 0.0:
                continue
            lines.append([P((s * 8.6, 11.5, 23.5)), P((s * 11.8, 16.0, 20.5)), P((s * 10.8 + s * sm * 0.8, 21.5 - sm, 17.0))])
            if q.micro and nz((s * 0.7, -0.1, 0.6)) > 0.05:
                crows.append([P((s * 19.0, -5.5, 15.5)), P((s * 22.0, -7.5, 12.0))])
                crows.append([P((s * 19.0, -2.0, 15.5)), P((s * 22.5, -1.5, 11.5))])
        B.detail_lines(cr, lines, lw * 0.8, skin.line, 0.42, taper=(0.1, 1.0, 0.2))
        if crows:      # crow's feet deepen when she smiles
            B.detail_lines(cr, crows, lw * 0.7, skin.line, 0.25 + 0.4 * clamp(max(sm, e.cheek)), taper=(0.2, 1.0, 0.1))

    # ---- hair: soft silver rolls at the brow and puffs at the temples, under the hood's edge
    hair_hulls = []
    for s in (-1.0, 1.0):
        hair_hulls.append(core.convex_hull(B.ellipsoid_pts(P, (s * 9.5, -23.6, 10.5), 11.0, 4.6, 7.0, 6)))
        if nz((s * 0.8, 0.0, 0.5)) > -0.3:
            hair_hulls.append(core.convex_hull(B.ellipsoid_pts(P, (s * 22.0, -5.5, 4.0), 5.2, 8.5, 5.5, 6)))
    hp_ = _union(q, hair_hulls, M["hair"], size=9, rim=0.6)
    if q.detail >= 1:
        cr.save()
        hp_.add(cr)
        cr.clip()
        strands = [[P((s * 1.0, -26.0, 13.5)), P((s * 7.5, -23.5, 15.5)), P((s * 16.0, -20.0, 12.0))] for s in (-1.0, 1.0)]
        B.detail_lines(cr, strands, lw * 0.6, hair.line, 0.4, taper=(0.2, 1.0, 0.3))
        cr.restore()

    # ---- eyes (behind the spectacles)
    blink = B.auto_blink(t, pose.seed + 17) if pose.blink is None else pose.blink
    eyes = []
    for s in (far, near):
        ec = P((s * EYE_X, EYE_Y, EYE_Z))
        eyes.append(ec)
        fz = nz((s * 0.42, -0.1, 0.9))
        if fz < 0.06:
            continue
        fore = clamp(0.3 + fz * 0.8, 0.3, 1.0)
        op = P((s * (EYE_X + 7.0), EYE_Y, EYE_Z - 3.0))
        outer = 1.0 if op[0] > ec[0] else -1.0
        ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)
        B.eye(cr, ec[0], ec[1], EYE_RX * fore, EYE_RY, q.light, lw * 0.85, angle=ang * 0.6,
              look=(pose.look[0] * outer, pose.look[1]), lid=e.lid, lid_bot=e.lid_bot, tilt=e.lid_tilt,
              outer=outer, blink=blink, squint_arc=clamp((pose.laugh - 0.5) * 2.0),
              iris=GNOME_COLORS["eye"], iris_hi=GNOME_COLORS["eye_hi"], pupil="#1d120c",
              pupil_size=0.5 * e.pupil, skin=GNOME_COLORS["skin"], crease=0.45,
              bags=0.3 if q.detail >= 1 else 0.0, line=skin.line, lid_shade=0.14, lash=0.85)

    # ---- mouth
    mouth = _mouth(q, P, nz, e, open_, near, skin)

    # ---- brows: short bushy silver tufts that act hard
    _brows(q, P, nz, e, near)

    # ---- spectacle arms run back under the hood's edge
    slide = 4.5 * smooth(clamp(pose.specs))
    spal = q.P(M["specs"])
    arms_ = []
    for s in (far, near):
        if nz((s * 0.9, 0.0, 0.3)) < -0.1:
            continue
        arms_.append([P((s * (EYE_X + LENS_R), -4.0 + slide * 0.8, 22.5)), P((s * 23.5, -5.0 + slide * 0.3, 13.0)),
                      P((s * 25.5, -4.5, 0.0))])
    if arms_:
        B.detail_lines(cr, arms_, lw * 0.6, spal.line, 1.0, taper=(1.0, 1.0, 0.6))

    # ---- the near run of the hem over the face edge (points whose outward normal faces us)
    run = _near_run(arch, vis, -0.2)
    if run is not None:
        pts_, rad_ = run
        bs, bo = _hem(cr, pts_, lw, rad_[0] / BRIM_R, rad_[-1] / BRIM_R)
        _flat(q, bs, bo, M["lining"])

    # ---- spectacle lenses (the nose sits in front of their inner rims)
    lenses = _specs(q, P, nz, slide, near, spal, "lenses")

    # ---- the big soft nose
    nc = P(NOSE_C)
    ax_ = P((-1.0, 0.0, 0.0)), P((1.0, 0.0, 0.0))
    roll = math.atan2(ax_[1][1] - ax_[0][1], ax_[1][0] - ax_[0][0])
    if abs(roll) > math.pi / 2:
        roll -= math.copysign(math.pi, roll)
    ns, no = B.ellipse_paths(cr, nc[0], nc[1], NOSE_R * 1.04, NOSE_R * 0.9, lw * 0.9, roll)
    npal = q.shade(ns, M["nose"], outline=no, size=18, rim=0.7)
    kx, ky = B.local_dir(cr, q.light.direction)
    B.sheen(cr, nc[0] + kx * 3.4, nc[1] + ky * 3.4 - 1.0, 3.4, 2.3, alpha=0.5)
    if q.detail >= 1:
        nl = []
        for s in (-1.0, 1.0):
            if nz((s * 0.6, 0.5, 0.6)) < -0.05:
                continue
            nl.append([P((s * 2.2, 15.0, 29.0)), P((s * 4.0, 16.0, 28.0)), P((s * 5.8, 14.5, 26.5))])
        if nl:
            B.detail_lines(cr, nl, lw * 0.8, npal.line, 0.6, taper=(0.3, 1.0, 0.3))

    # ---- the bridge rests on her nose
    _specs(q, P, nz, slide, near, spal, "bridge")
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mouth, "nose": nc, "eyes": eyes, "lenses": lenses,
            "top": P((0.0, -33.5, -3.5)), "tip": tip}


def _hem(cr, pts, lw, k0=0.7, k1=0.7):
    """The hood's rolled hem along projected points: a tapered ribbon (ends k0/k1 x radius)."""
    def prof(u):
        k = k0 + (1.0 - k0) * min(1.0, u / 0.12) if u < 0.12 else (k1 + (1.0 - k1) * min(1.0, (1.0 - u) / 0.12) if u > 0.88 else 1.0)
        return 2.0 * BRIM_R * k
    sh, so = B.taper_paths(cr, pts, 2 * BRIM_R, 2 * BRIM_R, lw, cap=True, profile=prof)
    return sh, so


def _unit3(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _near_run(pts, vis, thr):
    """The contiguous run of a polyline whose visibility (normal depth) exceeds thr, cut cleanly
    at interpolated end points -> (points, radii) for a tube, or None. The run is the longest
    one (the hem: from the near jaw corner over the top to wherever it turns away)."""
    n = len(pts)
    best, cur = None, None
    for i in range(n):
        if vis[i] >= thr:
            cur = (cur[0], i) if cur else (i, i)
            if best is None or cur[1] - cur[0] > best[1] - best[0]:
                best = cur
        else:
            cur = None
    if best is None:
        return None
    i0, i1 = best
    out = list(pts[i0:i1 + 1])
    if i0 > 0:           # cut in at the threshold crossing before the run
        u = (thr - vis[i0 - 1]) / ((vis[i0] - vis[i0 - 1]) or 1e-9)
        out.insert(0, core.lerp_pt(pts[i0 - 1], pts[i0], clamp(u)))
    if i1 < n - 1:
        u = (thr - vis[i1]) / ((vis[i1 + 1] - vis[i1]) or 1e-9)
        out.append(core.lerp_pt(pts[i1], pts[i1 + 1], clamp(u)))
    if len(out) < 2:
        return None
    rad = [BRIM_R] * len(out)
    rad[0] = BRIM_R * 0.7 if i0 == 0 else BRIM_R * 0.45
    rad[-1] = BRIM_R * 0.7 if i1 == n - 1 else BRIM_R * 0.45
    return out, rad


def _inside(poly, p):
    """Point-in-convex-polygon test (hull from core.convex_hull)."""
    n = len(poly)
    if n < 3:
        return False
    sgn = 0
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        c = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if c != 0:
            if sgn == 0:
                sgn = 1 if c > 0 else -1
            elif (c > 0) != (sgn > 0):
                return False
    return True


def _brows(q, P, nz, e, near):
    """Bushy silver brows: a tapered main stroke + little hairs flicking up at the inner end and
    out at the outer end, one outline fill + one colour fill. They act hard (MOODS)."""
    cr = q.cr
    far = -near
    strokes = []
    for s in (far, near):
        if nz((s * 0.45, -0.4, 0.8)) < -0.05:
            continue
        asym = e.brow_asym * (1.0 if s == near else -0.4)
        li = (e.brow_in * 0.8 + e.brow_y + asym) * 5.5
        lo = (e.brow_out * 0.6 + e.brow_y + asym) * 4.5
        y0 = -16.2
        a_ = P((s * 4.6, y0 + 0.4 - li, 21.5))
        m_ = P((s * 10.8, y0 - 2.2 - (li + lo) * 0.5, 21.0))
        o_ = P((s * 17.4, y0 - 0.2 - lo, 17.5))
        strokes.append(([a_, m_, o_], 5.4, 2.4))
        # wisps: two up-flicks at the inner end, one tuft out past the outer end
        for dx, dy, L in ((1.2, -1.0, 3.6), (2.8, -1.6, 3.2)):
            b0 = P((s * (4.6 + dx), y0 - li - dy * 0.2, 21.5))
            strokes.append(([b0, P((s * (4.6 + dx - 0.6), y0 - li - dy - L, 21.5))], 2.0, 0.6))
        strokes.append(([P((s * 15.5, y0 - 1.0 - lo, 18.5)), P((s * 19.8, y0 + 0.6 - lo, 15.5))], 2.2, 0.6))
    if not strokes:
        return
    lwb = q.lw * 0.7
    bp = q.P(q.M["brow"])
    cr.new_path()
    for pts, w0, w1 in strokes:
        core.tapered(cr, pts, w0 + 2 * lwb, w1 + 2 * lwb)
    core.src(cr, bp.line)
    cr.fill()
    for pts, w0, w1 in strokes:
        core.tapered(cr, pts, w0, w1)
    core.src(cr, core.mix(bp.lit, bp.hi, 0.35))
    cr.fill()


def _mouth(q, P, nz, e, open_, near, skin):
    """Small expressive mouth: corners from smile (+ her one-sided smirk), opening from talk /
    laugh / the mood. Returns the mouth center in local coordinates."""
    cr, pose, lw = q.cr, q.pose, q.lw
    sm = e.smile
    smirk = clamp(pose.smirk)
    far = -near
    lift = {near: sm * 3.4 + smirk * 3.2, far: sm * 3.4 - smirk * 0.6}
    hw = 7.0 * (1.0 + 0.12 * sm + (0.25 if e.mouth == "laugh" else 0.0) - (0.3 if e.mouth == "o" else 0.0))
    y0, z0 = MOUTH_Y, MOUTH_Z
    corners = {s: P((s * hw, y0 - lift[s], z0 - 2.0)) for s in (-1.0, 1.0)}
    center = P((0.0, y0 + 0.6, z0 + 0.8))
    if nz((0.0, 0.3, 1.0)) < -0.2:
        return center
    lc = skin.line
    if open_ < 0.05:
        pts = [corners[-1.0], P((-hw * 0.5, y0 + 0.5 - lift[-1.0] * 0.3, z0)), P((0.0, y0 + 0.9, z0 + 0.8)),
               P((hw * 0.5, y0 + 0.5 - lift[1.0] * 0.3, z0)), corners[1.0]]
        B.detail_line(cr, pts, lw * 1.15, lc, 1.0, taper=(0.35, 1.0, 0.35))
        if q.detail >= 1:
            # lower lip shadow + corner tucks (deeper when smiling)
            B.detail_lines(cr, [[P((-2.6, y0 + 3.4, z0 + 0.3)), P((0.0, y0 + 4.0, z0 + 0.6)), P((2.6, y0 + 3.4, z0 + 0.3))]],
                           lw * 0.7, lc, 0.4, taper=(0.2, 1.0, 0.2))
            tucks = []
            for s in (-1.0, 1.0):
                if lift[s] > 1.2 and nz((s * 0.5, 0.3, 0.8)) > 0.0:
                    c0 = corners[s]
                    tucks.append([(c0[0] - s * 0.5, c0[1] - 1.8), (c0[0] + s * 1.2, c0[1] + 0.2), (c0[0] + s * 0.4, c0[1] + 2.0)])
            if tucks:
                B.detail_lines(cr, tucks, lw * 0.8, lc, 0.6)
        return center
    # open: upper lip arc from corner to corner, lower lip dropping with the opening
    h = 2.0 + 9.5 * open_ * (1.15 if e.mouth == "laugh" else 1.0)
    top_mid = P((0.0, y0 - 0.6 + (0.3 if e.mouth != "laugh" else -0.8), z0 + 0.8))
    bot_mid = P((0.0, y0 + h, z0 - h * 0.25))
    L, R = corners[-1.0], corners[1.0]
    cr.new_path()
    cr.move_to(*L)
    cr.curve_to(lerp(L[0], top_mid[0], 0.6), top_mid[1], lerp(R[0], top_mid[0], 0.6), top_mid[1], *R)
    cr.curve_to(lerp(R[0], bot_mid[0], 0.35), bot_mid[1], lerp(L[0], bot_mid[0], 0.35), bot_mid[1], *L)
    cr.close_path()
    mp = Path(cr)
    B.flat(cr, mp, GNOME_COLORS["mouth"], lw * 0.9, lc)
    cr.save()
    mp.add(cr)
    cr.clip()
    core.src(cr, GNOME_COLORS["tongue"])
    core.ellipse(cr, bot_mid[0], bot_mid[1] - 0.5, abs(R[0] - L[0]) * 0.32 + 1.0, h * 0.42)
    cr.fill()
    if h > 4.0:                         # a neat row of upper teeth
        core.src(cr, GNOME_COLORS["teeth"])
        tl, tr = P((-hw * 0.55, y0 - 2.0, z0)), P((hw * 0.55, y0 - 2.0, z0))
        core.polygon(cr, [tl, tr, (tr[0], tr[1] + 3.8), (tl[0], tl[1] + 3.8)])
        cr.fill()
    cr.restore()
    return center


def _specs(q, P, nz, slide, near, spal, part):
    """Round brass spectacles: part "lenses" (glass, glint, wire rims; returns the lens
    centers) is drawn before the nose, part "bridge" after it."""
    cr, t, pose, lw = q.cr, q.t, q.pose, q.lw
    far = -near
    glint = pose.glint if pose.glint is not None else _auto_glint(t, pose.seed)
    centers = []
    lenses = []
    for s in (far, near):
        c3 = (s * EYE_X, -4.0 + slide, 23.5 - slide * 0.1)
        if nz((s * 0.3, 0.0, 0.95)) < 0.02:
            continue
        ring = []
        for i in range(16):
            a = TAU * i / 16
            ring.append(P((c3[0] + math.cos(a) * LENS_R, c3[1] + math.sin(a) * LENS_R, c3[2] - 1.2 * (math.cos(a) * s + 1.0) * 0.5)))
        lenses.append(ring)
        centers.append(P(c3))
    if part == "bridge":
        lenses = []
    # glass: a faint sheen of reflected sky + a reflection crescent, and the glint sweep
    for ring in lenses:
        cr.new_path()
        core.smooth_closed(cr, ring, 0.9)
        lens_p = Path(cr)
        cr.save()
        lens_p.add(cr)
        cr.clip()
        core.src(cr, core.mix(q.light.rim, (1, 1, 1), 0.5), 0.07)
        cr.paint()
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = x1 - x0, y1 - y0
        cr.set_source_rgba(1, 1, 1, 0.2)
        cr.move_to(x0 + w * 0.12, y0 + h * 0.45)
        cr.curve_to(x0 + w * 0.15, y0 + h * 0.12, x0 + w * 0.45, y0 + h * 0.02, x0 + w * 0.7, y0 + h * 0.08)
        cr.curve_to(x0 + w * 0.42, y0 + h * 0.14, x0 + w * 0.22, y0 + h * 0.28, x0 + w * 0.12, y0 + h * 0.45)
        cr.fill()
        if 0.0 <= glint <= 1.0:
            d = lerp(-1.2, 1.2, glint)
            cx_, cy_ = (x0 + x1) / 2 + d * w * 0.5, (y0 + y1) / 2 + d * h * 0.5
            cr.set_source_rgba(1, 1, 0.97, 0.85 * math.sin(math.pi * glint))
            bw = w * 0.16
            core.polygon(cr, [(cx_ - w, cy_ + w - bw), (cx_ + w - bw, cy_ - w), (cx_ + w + bw, cy_ - w), (cx_ - w + bw * 2, cy_ + w)])
            cr.fill()
        cr.restore()
    # rims + bridge (one fill in the brass line color, then the brass)
    lwr = lw * 0.4
    bridge = None
    if part == "bridge" and nz((0.0, 0.0, 1.0)) > 0.1:
        bridge = [P((-EYE_X + LENS_R * 0.95, -5.0 + slide, 25.0)), P((0.0, -7.0 + slide, 28.0)),
                  P((EYE_X - LENS_R * 0.95, -5.0 + slide, 25.0))]
    if not lenses and not bridge:
        return centers
    for pass_ in (0, 1):
        cr.new_path()
        wpx = 1.35 if pass_ == 1 else 1.35 + 2 * lwr
        for ring in lenses:
            core.smooth_closed(cr, B.offset_closed(ring, wpx * 0.5), 0.9)
            core.smooth_closed(cr, B.offset_closed(ring, -wpx * 0.5)[::-1], 0.9)
        if bridge:
            core.tapered(cr, bridge, wpx, wpx)
        core.src(cr, spal.line if pass_ == 0 else core.mix(spal.lit, spal.hi, 0.2))
        cr.fill()
    return centers


# ----------------------------------------------------------------------------------------
# the bread (her loaf, its halves and the pieces she hands out)
# ----------------------------------------------------------------------------------------

def gnome_bread(cr, x, y, size=GNOME_LOAF, light=None, state="loaf", angle=0.0, crack=0.0, face=1.0,
                lw=None, seed=0, detail=2):
    """Her round crusty loaf, centered at (x, y) in the current units (outlined + house shading,
    it is a prop she touches).

    state  "loaf": the whole round boule, scored on top (crack 0..1 opens a tear down the middle)
           "half": a torn half; its pale torn face points toward `face` (+1 = +x, -1 = -x)
           "piece": a torn chunk -- crust cap on top, soft crumb below (what she hands out)
    size   loaf diameter (her loaf: GNOME_LOAF = 46 at scale 1.0; pieces are ~0.45 of it)
    lw     outline weight (default: the house LINE, kept >= 1 screen px)
    """
    light = light or B.LIGHTS["neutral"]
    M = gnome_mats()
    if lw is None:
        lw = B.line_w(cr, GNOME_LINE)
    r = size * 0.5
    cr.save()
    cr.translate(x, y)
    if angle:
        cr.rotate(angle)
    if state == "piece":
        _bread_piece(cr, r, light, M, lw, face, seed, detail)
    elif state == "half":
        _bread_half(cr, r, light, M, lw, face, detail)
    else:
        _bread_loaf(cr, r, light, M, lw, crack, detail)
    cr.restore()


def _loaf_pts(r, x0=-1.0, x1=1.0, n=20):
    """The boule's silhouette: a high domed top, a flatter base."""
    pts = []
    for i in range(n):
        a = math.pi + math.pi * i / (n - 1)         # top half, left -> right
        pts.append((math.cos(a) * r, math.sin(a) * r * 0.8 + r * 0.12))
    pts += [(r * 0.96, r * 0.32), (r * 0.7, r * 0.5), (0.0, r * 0.56), (-r * 0.7, r * 0.5), (-r * 0.96, r * 0.32)]
    return [(px, py) for px, py in pts if x0 * r - 1e-6 <= px <= x1 * r + 1e-6]


def _bread_loaf(cr, r, light, M, lw, crack, detail):
    sh, so = B.smooth_paths(cr, _loaf_pts(r), lw, 0.85)
    p = B.shade(cr, sh, M["crust"], light, lw, outline=so, size=r * 1.4, bounce=0)
    hi = B.palette(light, M["crust_hi"])
    cr.save()
    sh.add(cr)
    cr.clip()
    if detail >= 1:
        # three curved score marks: pale torn "ears" with a dark lip
        cr.new_path()
        for k in (-1, 0, 1):
            x0 = k * r * 0.42
            pts = [(x0 - r * 0.2, -r * 0.42 + abs(k) * r * 0.1), (x0, -r * 0.6 + abs(k) * r * 0.12), (x0 + r * 0.2, -r * 0.42 + abs(k) * r * 0.1)]
            core.tapered(cr, [(pts[0][0] + r * 0.05 * k, pts[0][1] + r * 0.05), pts[1], (pts[2][0], pts[2][1] - r * 0.05)],
                         r * 0.13, r * 0.13, profile=lambda u: r * 0.14 * math.sin(math.pi * u) + 0.4)
        sc = Path(cr)
        sc.add(cr, 0.0, r * 0.045)
        core.src(cr, p.line, 0.7)
        cr.fill()
        sc.add(cr)
        core.src(cr, hi.lit)
        cr.fill()
    if detail >= 2:                                  # flour dusting
        core.src(cr, "#f7efdc", 0.55)
        for i in range(9):
            fx_ = (core.hash01(i, 77) - 0.5) * r * 1.5
            fy_ = -r * 0.55 + core.hash01(i, 78) * r * 0.35
            core.circle(cr, fx_, fy_, r * 0.035 + 0.3)
        cr.fill()
    if crack > 0.0:                                  # the tear opening down the middle
        w = r * 0.22 * crack
        pts_l, pts_r = [], []
        for i in range(7):
            u = i / 6
            yy = -r * 0.75 + u * r * 1.35
            jx = (core.hash01(i, 5) - 0.5) * r * 0.12
            ww = w * math.sin(math.pi * min(1.0, 0.15 + u)) * (1.0 - 0.6 * u)
            pts_l.append((jx - ww, yy))
            pts_r.append((jx + ww, yy))
        cr.new_path()
        core.polygon(cr, pts_l + pts_r[::-1])
        core.src(cr, p.line)
        cr.fill()
        cr.new_path()
        core.polygon(cr, [(px + 0.8, py) for px, py in pts_l] + [(px - 0.8, py) for px, py in pts_r[::-1]])
        core.src(cr, B.palette(light, M["crumb"]).lit)
        cr.fill()
    cr.restore()
    B.sheen(cr, -r * 0.35, -r * 0.48, r * 0.3, r * 0.14, angle=-0.4, alpha=0.3)


def _bread_half(cr, r, light, M, lw, face, detail):
    sx = 1.0 if face >= 0 else -1.0
    cr.save()
    cr.scale(sx, 1.0)                       # author with the torn face toward +x
    crust = _loaf_pts(r, -1.0, 0.18)
    crust += [(r * 0.24, r * 0.3), (r * 0.3, -r * 0.1), (r * 0.22, -r * 0.62)]
    sh, so = B.smooth_paths(cr, crust, lw, 0.8)
    B.shade(cr, sh, M["crust"], light, lw, outline=so, size=r * 1.2, bounce=0)
    if detail >= 1:
        hi = B.palette(light, M["crust_hi"])
        cr.save()
        sh.add(cr)
        cr.clip()
        cr.new_path()
        for k in (-1, 0):
            x0 = k * r * 0.42 - r * 0.1
            core.tapered(cr, [(x0 - r * 0.18, -r * 0.38), (x0, -r * 0.56), (x0 + r * 0.18, -r * 0.42)], r * 0.12, r * 0.12,
                         profile=lambda u: r * 0.13 * math.sin(math.pi * u) + 0.4)
        core.src(cr, hi.lit)
        cr.fill()
        cr.restore()
    # the torn face: pale crumb with a ragged edge, seen a little from the side
    face_pts = []
    for i in range(16):
        a = TAU * i / 16
        rag = 1.0 + 0.08 * math.sin(i * 2.7) + 0.05 * math.cos(i * 4.1)
        face_pts.append((r * 0.2 + math.cos(a) * r * 0.36 * rag, r * -0.05 + math.sin(a) * r * 0.62 * rag))
    fs, fo = B.smooth_paths(cr, face_pts, lw * 0.8, 0.7)
    cp = B.shade(cr, fs, M["crumb"], light, lw * 0.8, outline=fo, size=r * 0.6, bounce=0)
    if detail >= 1:                          # the crumb's little holes
        core.src(cr, cp.shadow, 0.8)
        for i in range(7):
            hx = r * 0.2 + (core.hash01(i, 41) - 0.5) * r * 0.42
            hy = -r * 0.05 + (core.hash01(i, 42) - 0.5) * r * 0.9
            core.ellipse(cr, hx, hy, r * 0.045 + 0.4, r * 0.03 + 0.3)
        cr.fill()
    cr.restore()


def _bread_piece(cr, r, light, M, lw, face, seed, detail):
    s = r * 0.48
    pts = []
    for i in range(9):
        a = TAU * i / 9
        rag = 1.0 + 0.16 * (core.hash01(i, seed + 11) - 0.5)
        pts.append((math.cos(a) * s * 1.15 * rag, math.sin(a) * s * 0.85 * rag))
    sh, so = B.smooth_paths(cr, pts, lw * 0.85, 0.8)
    B.shade(cr, sh, M["crumb"], light, lw * 0.85, outline=so, size=s, bounce=0)
    # the crust cap over the top
    cr.save()
    sh.add(cr)
    cr.clip()
    cap = [(-s * 1.4, -s * 1.4), (s * 1.4, -s * 1.4), (s * 1.4, -s * 0.15 * face), (s * 0.5, -s * 0.35), (-s * 0.5, -s * 0.2),
           (-s * 1.4, s * 0.1 * face)]
    cr.new_path()
    core.polygon(cr, cap)
    cpal = B.palette(light, M["crust"])
    core.src(cr, cpal.line)
    cr.fill()
    core.polygon(cr, [(px, py - lw * 0.6) for px, py in cap])
    core.src(cr, cpal.lit)
    cr.fill()
    if detail >= 1:
        core.src(cr, B.palette(light, M["crumb"]).shadow, 0.8)
        for i in range(3):
            core.circle(cr, (core.hash01(i, seed + 3) - 0.5) * s, s * 0.25 + core.hash01(i, seed + 4) * s * 0.4, s * 0.09 + 0.3)
        cr.fill()
    cr.restore()


def gnome_bread_hold(state="piece", light=None, size=GNOME_LOAF, face=1.0, upright=True):
    """A `hold` callback that puts her bread in ANY character's hand (e.g. the dragon receiving
    a piece: DragonPose(near=Arm("hand_out_offer", hold=ch.gnome_bread_hold("piece", L))))."""
    def draw(cr, f):
        cr.save()
        if upright:
            cr.rotate(-f.angle)
        if state == "piece":
            gnome_bread(cr, -4.0, -6.0, size, light, "piece", face=face)
        elif state == "half":
            gnome_bread(cr, 0.0, -size * 0.18, size, light, "half", face=face)
        else:
            gnome_bread(cr, 0.0, -size * 0.25, size, light, "loaf")
        cr.restore()
    return draw


# ----------------------------------------------------------------------------------------
# crumbs (pair with pigeons via gnome_crumb_landings)
# ----------------------------------------------------------------------------------------

def _crumb_kw(rig, ground_y, n, seed):
    s = rig.scale
    fwd = rig.facing
    return dict(n=n, seed=seed, vx=(fwd * 20.0, fwd * 150.0), vy=(-170.0, -60.0), ground_y=ground_y,
                scale=s, release=0.1)


def gnome_rig_at(x, y, scale, pose, t, light=None):
    """Her rig (hand frames, head, bread...) for this pose and time WITHOUT drawing her -- e.g.
    the release moment of a toss, for gnome_toss_crumbs / gnome_crumb_landings. Costs about one
    draw; compute it once (setup()) when the toss is fixed."""
    _s, c = core.frame(4, 4)
    return draw_gnome(c, x, y, scale, pose, light, t)


def gnome_toss_crumbs(cr, t, t0, rig, ground_y, n=10, seed=0, size=3.0, flock=None, first=0):
    """The crumbs she flicks at t0 (toss_crumbs phase ~0.5) from her near hand, landing on
    ground_y. `rig` must be her rig AT THE RELEASE (gnome_rig_at(..., t0)), so crumbs already in
    the air don't follow her hand. gnome_crumb_landings() gives where they come to rest (for
    the pigeons); pass the PigeonFlock built from them as `flock` and the crumbs it has pecked
    up vanish (`first` = the index of this toss's first crumb in the flock's crumb list)."""
    h = rig.hand_near
    kw = _crumb_kw(rig, ground_y, n, seed)
    gone = []
    if flock is not None:
        land = fx.crumb_landings(t0, h.x, h.y, **kw)
        gone = [lx for k, (lx, _tr) in enumerate(land) if flock.crumb_eaten(first + k, t)]
    if gone:
        cr.save()
        cr.new_path()
        cr.set_fill_rule(1)                    # even-odd: everything but small discs round the eaten
        cr.rectangle(-1e5, -1e5, 2e5, 2e5)
        r = 9.0 * rig.scale
        for lx in gone:
            cr.new_sub_path()
            cr.arc(lx, ground_y, r, 0.0, TAU)
        cr.clip()
        cr.set_fill_rule(0)
    fx.crumbs(cr, t, t0, h.x, h.y, size=size, color=GNOME_COLORS["crumb"], crust=GNOME_COLORS["crust"], **kw)
    if gone:
        cr.restore()


def gnome_crumb_landings(t0, rig, ground_y, n=10, seed=0):
    """[(x_rest, t_rest, ground_y)] for gnome_toss_crumbs with the same arguments -- pass them
    straight to PigeonFlock(crumbs=...)."""
    h = rig.hand_near
    return [(lx, tr, ground_y) for lx, tr in fx.crumb_landings(t0, h.x, h.y, **_crumb_kw(rig, ground_y, n, seed))]


def gnome_tear_crumbs(cr, t, t0, rig, n=8, seed=4):
    """The little spray of crumbs when the loaf snaps in two (tear_bread, phase 0.5 = t0)."""
    if rig.bread is None:
        return
    s = rig.scale
    fx.crumbs(cr, t, t0, rig.bread[0], rig.bread[1], n=n, seed=seed, vx=(-70.0, 70.0), vy=(-120.0, -20.0),
              ground_y=rig.bread[1] + 240.0 * s, size=2.2, color=GNOME_COLORS["crumb"], crust=GNOME_COLORS["crust"],
              scale=s, release=0.05)


# ----------------------------------------------------------------------------------------
# character sheet (python3 film/render.py --sheet)
# ----------------------------------------------------------------------------------------

def lineup():
    """The gnome on the cast height chart (character_sheet_lineup.png)."""
    return [B.LineupItem("gnome", lambda cr, x, y, sc: draw_gnome(cr, x, y, sc, GnomePose(facing=1), t=0.4), 110.0)]


def sheet_items():
    """Character sheet cells for render.py --sheet (see API.md: sheet convention)."""
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    # ---- turnaround (drawn at 2.2x so she can be judged in detail)
    SC = 2.2
    for label, pose in (("3/4 left", GnomePose(facing=-1)), ("front", GnomePose(facing=0)),
                        ("3/4 right", GnomePose(facing=1)), ("near profile", GnomePose(facing=1, turn=0.7)),
                        ("talking, dry wit", GnomePose(facing=1, turn=-0.4, talk=0.6, smirk=0.8, mood="skeptical")),
                        ("warm laugh", GnomePose(facing=0, turn=0.3, laugh=1.0, near=GnomeArm("hand_on_chest")))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 290, 470, floor=440)
            draw_gnome(cr, 145, 452, SC, p.with_(blink=0.0), neutral, t=0.4)
        add(label, 290, 470, fn, "turnaround")
    for tv in (-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4):
        def fn(cr, tv=tv):
            B.sheet_bg(cr, 240, 360, floor=330)
            draw_gnome(cr, 120, 342, 1.6, GnomePose(facing=0, turn=tv, blink=0.0), neutral, t=0.4 + 0.3 * tv)
        add(f"turn {tv:+.1f} (yaw {_yaw_of(0, tv):+.2f})", 240, 360, fn, "turnaround")

    # ---- seated on the standard bench, and the scale gag: her head at the dragon's elbow
    SS = 1.5
    for label, pose in (("seated 3/4 (bench 125)", GnomePose(facing=1, sit=1.0)),
                        ("seated front", GnomePose(facing=0, sit=1.0, mood="warm")),
                        ("seated: legs swinging", GnomePose(facing=1, turn=-0.3, sit=1.0, kick=1.0, mood="happy")),
                        ("seated: legs stuck out", GnomePose(facing=0, turn=0.4, sit=1.0, legs_out=1.0, mood="raised"))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 300, 470, floor=440)
            _bench(cr, 150, 452, SS, w=230)
            draw_gnome(cr, 140, 452, SS, p.with_(blink=0.0), neutral, t=0.7)
        add(label, 300, 470, fn, "seated & scale")

    for ph in (0.0, 0.25, 0.5, 0.75):
        def fn(cr, ph=ph):
            B.sheet_bg(cr, 200, 300, floor=270)
            draw_gnome(cr, 96, 282, 1.35, GnomePose(facing=1, walk=1.0, phase=ph, blink=0.0, mood="warm"), neutral, t=ph)
        add(f"waddle {ph:.2f}", 200, 300, fn, "seated & scale")

    def two_shot(cr, w=620, h=470, light=neutral, name="neutral", sc=0.82, t=0.4):
        from . import dragon as D
        B.sheet_bg(cr, w, h, name, floor=h - 30)
        g = h - 18
        _bench(cr, w * 0.5, g, sc, w=430 * sc, light=light)
        D.draw_dragon(cr, w * 0.5 + 115 * sc, g, sc, D.DragonPose(facing=-1, sit=1.0, mood="tired"), light, t=t)
        draw_gnome(cr, w * 0.5 - 120 * sc, g, sc, GnomePose(facing=1, sit=1.0, blink=0.0, look=(0.3, -0.2)), light, t=t)
    add("same scale on one bench: her head at his elbow", 620, 470, two_shot, "seated & scale")

    def heights(cr):
        B.sheet_bg(cr, 300, 470, floor=440)
        g, sc = 452, 1.5
        cr.set_source_rgba(1, 1, 1, 0.25)
        for k in range(0, 260, 50):
            cr.rectangle(10, g - k * sc, 280, 1)
        cr.fill()
        for k in range(0, 260, 50):
            core.text(cr, f"{k}", 14, g - k * sc - 3, 11, core.SANS, "#dfe6ee")
        _bench(cr, 190, g, sc, w=150)
        draw_gnome(cr, 90, g, sc, GnomePose(facing=1, blink=0.0), neutral, t=0.4)
        draw_gnome(cr, 190, g, sc, GnomePose(facing=1, sit=1.0, blink=0.0), neutral, t=0.4)
    add("standing 160 / seated head ~228", 300, 470, heights, "seated & scale")

    # ---- faces (head close-ups at 3.2x)
    FS = 2.7
    moods = [("kind (default)", dict()), ("warm smile", dict(mood="warm")), ("happy", dict(mood="happy")),
             ("dry wit: smirk", dict(mood="skeptical", smirk=1.0)), ("talk 0.5", dict(talk=0.5)),
             ("talk 1.0", dict(talk=1.0, mood="warm")), ("WARM LAUGH", dict(laugh=1.0)),
             ("glance over specs", dict(specs=1.0, look=(0.5, -0.65), head_nod=-0.5, mood="skeptical")),
             ("raised", dict(mood="raised")), ("surprised", dict(mood="surprised")), ("worried", dict(mood="worried")),
             ("sad", dict(mood="sad")), ("skeptical", dict(mood="skeptical")), ("blink", dict(blink=1.0)),
             ("look left", dict(look=(-0.9, 0.1))), ("look right", dict(look=(0.9, 0.0))),
             ("glint on the specs", dict(glint=0.5, mood="happy")), ("front: kind", dict(facing=0)),
             ("front: laugh", dict(facing=0, laugh=1.0)), ("front: glance", dict(facing=0, specs=1.0, look=(0.0, -0.7), head_nod=-0.45)),
             ("3/4 left: talking", dict(facing=-1, talk=0.7, mood="warm"))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        pose = GnomePose(facing=facing, turn=-0.35 if facing == 1 else (0.35 if facing == -1 else 0.0),
                         **dict(dict(blink=0.0), **kw))

        def fn(cr, p=pose):
            B.sheet_bg(cr, 230, 230)
            hx, hy = K.head_frame(draw_gnome, p, FS, neutral)
            draw_gnome(cr, 115 - hx, 112 - hy, FS, p, neutral, t=0.4)
        add(label, 230, 230, fn, "faces")

    # ---- gestures with props (seated on the bench, as in S6/S7)
    GS = 1.55

    def gcell(pose, extra=None, light=neutral, name="neutral"):
        def fn(cr):
            B.sheet_bg(cr, 290, 440, name, floor=410)
            g = 422
            if pose.sit > 0.5:
                _bench(cr, 145, g, GS, w=250, light=light)
            rig = draw_gnome(cr, 140, g, GS, pose, light, t=0.6)
            if extra:
                extra(cr, rig, g)
        return fn

    def crumbs_fx(cr, rig, g):
        gnome_toss_crumbs(cr, 0.75, 0.45, rig, g - 4, n=12)

    def tear_fx(cr, rig, g):
        gnome_tear_crumbs(cr, 0.68, 0.5, rig)

    gest = [
        ("toss_crumbs: wind-up", GnomePose(facing=1, sit=1.0, near=GnomeArm("toss_crumbs", phase=0.3), far=GnomeArm("hold_bread", bread="half"), mood="warm", blink=0.0), None),
        ("toss_crumbs: flick + crumbs", GnomePose(facing=1, sit=1.0, near=GnomeArm("toss_crumbs", phase=0.6), far=GnomeArm("hold_bread", bread="half"), mood="happy", blink=0.0), crumbs_fx),
        ("tear_bread 0.0: the loaf", GnomePose(facing=1, turn=-0.4, sit=1.0, near=GnomeArm("tear_bread", phase=0.0), far=GnomeArm("tear_bread"), satchel="empty", look=(0.3, 0.6), head_nod=-0.3, blink=0.0), None),
        ("tear_bread 0.42: strain", GnomePose(facing=1, turn=-0.4, sit=1.0, near=GnomeArm("tear_bread", phase=0.42), far=GnomeArm("tear_bread", phase=0.42), satchel="empty", mood="worried", look=(0.3, 0.6), head_nod=-0.3, blink=0.0), None),
        ("tear_bread 0.62: snap", GnomePose(facing=1, turn=-0.4, sit=1.0, near=GnomeArm("tear_bread", phase=0.62), far=GnomeArm("tear_bread", phase=0.62), satchel="empty", mood="happy", blink=0.0), tear_fx),
        ("tear_bread 1.0: halves", GnomePose(facing=1, turn=-0.4, sit=1.0, near=GnomeArm("tear_bread", phase=1.0), far=GnomeArm("tear_bread", phase=1.0), satchel="empty", mood="warm", blink=0.0), None),
        ("far arm: hand_out_offer (piece)", GnomePose(facing=1, sit=1.0, far=GnomeArm("hand_out_offer", bread="piece"), near=GnomeArm("hold_bread", bread="half"), satchel="empty", mood="kind", look=(0.6, -0.3), blink=0.0), None),
        ("far arm: hand_out_offer (half)", GnomePose(facing=1, turn=-0.2, sit=1.0, far=GnomeArm("hand_out_offer", bread="half"), satchel="empty", mood="warm", look=(0.6, -0.3), blink=0.0), None),
        ("hand_on_chest (laugh)", GnomePose(facing=1, turn=-0.5, sit=1.0, laugh=1.0, near=GnomeArm("hand_on_chest"), blink=0.0), None),
        ("reach_satchel", GnomePose(facing=1, turn=-0.3, sit=1.0, near=GnomeArm("reach_satchel"), look=(-0.5, 0.6), head_nod=-0.3, blink=0.0), None),
        ("pat_bench (sit, sit)", GnomePose(facing=1, turn=-0.4, sit=1.0, far=GnomeArm("pat_bench", phase=0.25), mood="warm", look=(0.8, 0.0), blink=0.0), None),
        ("wave (standing)", GnomePose(facing=1, turn=-0.4, near=GnomeArm("wave", phase=0.2), mood="happy", blink=0.0), None),
    ]
    for label, pose, extra in gest:
        add(label, 290, 440, gcell(pose, extra), "gestures")

    # ---- the same gnome under every scene light, then her signature poses per scene
    for name in ("washhouse", "apothecary", "street_night", "tavern", "square", "dusk", "golden", "lantern_night"):
        add(name, 210, 440, gcell(GnomePose(facing=1, turn=-0.25, blink=0.0), None, L[name], name), "lighting")
    story = [
        ("S6 dusk: tossing crumbs", "dusk", GnomePose(facing=1, sit=1.0, near=GnomeArm("toss_crumbs", phase=0.6), far=GnomeArm("hold_bread", bread="half"), mood="kind", look=(0.3, 0.6), blink=0.0), crumbs_fx),
        ("S6 12.6: glance over specs", "dusk", GnomePose(facing=1, sit=1.0, specs=1.0, look=(0.7, -0.5), head_nod=-0.4, head_turn=0.3, mood="skeptical", glint=0.5, blink=0.0), None),
        ("S6 talk: dry wit", "dusk", GnomePose(facing=1, sit=1.0, talk=0.6, smirk=0.9, head_turn=0.25, mood="kind", blink=0.0), None),
        ("S6 26.8: he laughs, she smiles", "dusk", GnomePose(facing=1, sit=1.0, mood="happy", head_turn=0.35, look=(0.6, -0.3), blink=0.0), None),
        ("S7 golden: tear the loaf", "golden", GnomePose(facing=1, turn=-0.3, sit=1.0, near=GnomeArm("tear_bread", phase=0.8), far=GnomeArm("tear_bread", phase=0.8), satchel="empty", mood="warm", blink=0.0), None),
        ("S7: offer to the teen", "golden", GnomePose(facing=1, sit=1.0, far=GnomeArm("hand_out_offer", bread="piece"), near=GnomeArm("hold_bread", bread="half"), satchel="empty", mood="kind", look=(0.8, -0.4), blink=0.0), None),
        ("S7 blue hour: the last piece", "blue_hour", GnomePose(facing=1, sit=1.0, talk=0.5, far=GnomeArm("hand_out_offer", bread="piece"), satchel="empty", mood="warm", blink=0.0), None),
        ("S8 lantern: content", "lantern_night", GnomePose(facing=0, turn=0.3, sit=1.0, mood="warm", satchel="empty", kick=0.4, blink=0.0), None),
    ]
    for label, name, pose, extra in story:
        add(label, 210, 440, gcell(pose, extra, L[name], name), "lighting")

    # ---- film-scale readability: at the bench scale of S6/S7 she is ~150-230 px on screen
    for label, px, pose in (("230 px (S7 medium, seated)", 230, GnomePose(facing=1, sit=1.0, talk=0.6, smirk=0.6)),
                            ("160 px standing", 160, GnomePose(facing=1, mood="happy")),
                            ("120 px (S6 wide, seated)", 120, GnomePose(facing=1, sit=1.0, near=GnomeArm("toss_crumbs", phase=0.6))),
                            ("80 px (S8 wide)", 80, GnomePose(facing=0, turn=0.3, sit=1.0, mood="warm"))):
        def fn(cr, px=px, p=pose):
            B.sheet_bg(cr, 220, 400, "dusk", floor=372)
            sc = px / (228.0 if p.sit > 0.5 else GNOME_HEIGHT)
            if p.sit > 0.5:
                _bench(cr, 110, 386, sc, w=150 * sc / 0.6, light=L["dusk"])
            draw_gnome(cr, 110, 386, sc, p, L["dusk"], t=0.4)
        add(label, 220, 400, fn, "film scale")
    add("S6 two-shot at film scale (dusk)", 620, 400,
        lambda cr: two_shot(cr, 620, 400, L["dusk"], "dusk", 0.62), "film scale")
    return items
