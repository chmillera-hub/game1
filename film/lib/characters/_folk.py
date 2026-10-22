"""_folk.py -- the shared biped rig behind the supporting cast, part B: orc, minotaur, faun,
dwarf, pixie and the crowd extras. Private (leading underscore = not auto-imported); the creature
modules import it. Scene authors never call it directly.

It is the dragon's "3D-lite" recipe generalised by a `Build` (a species' proportions):

  * joints are posed in body space (X = the creature's left, Y down, Z forward) and projected
    with base.Proj(yaw, elev), so every creature turns continuously -- all the way round to the
    back view (the crowd turns away in S5) -- leans, walks and sits down in one motion;
  * torsos and garments are stacks of elliptical cross-sections ("rings") projected to one
    smooth silhouette; limbs are base.tube_paths; hands are base.hand; eyes are base.eye;
    every part is shaded with base.shade (outline = filled dilated copy, three tones);
  * arm gestures are functions of the skeleton returning a 3D hand target, a hand pose and a
    layer hint; base.ik3 solves the elbow;
  * drawing is split into layers ("back", "body", "mid", "head", "front") and `parts` picks
    which ones a call draws, so two creatures can interleave (the S5 hug: one creature's arm
    goes behind the other's body, the other arm over it).

Units: body px at scale 1.0 (= base.CAST_HEIGHTS), origin at the anchor (ground point below the
pelvis, or below the seat when sitting), y down.
"""

import math
from dataclasses import dataclass, field, replace
from typing import NamedTuple

from .. import core
from ..core import clamp, lerp, smooth
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp, v_sub
from .dragon import Arm  # one Arm type for the whole cast: Arm(gesture, amt, prev, hold, stamp, target, hand, phase)

TAU = math.tau
ELEV = 0.12
LAYERS = ("back", "body", "mid", "head", "front")


# ========================================================================================
# pose / rig / build
# ========================================================================================

@dataclass
class FolkPose:
    """Fields shared by every part-B biped (same names and meanings as DragonPose).

    facing   +1 3/4 view facing screen-right, -1 screen-left, 0 front, +-2 back view
    turn     extra body yaw (x0.6 rad) on top of facing; yaw (rad) overrides both (any value:
             these creatures can be seen from behind)
    sit      0 standing .. 1 seated on a seat seat_h high (animate 0 -> 1 to sit down)
    walk     0..1 blend into the walk cycle; phase = cycle phase (<creature>_walk_phase)
    lean     -1 back .. +1 forward; hunch None = species default
    stance   -1..1 fighting stance: + puts the creature's left foot forward, - the right
    head_turn / head_tilt / head_nod, look   as DragonPose
    mood, mood2, mood_mix, talk, smile, laugh, blink   as DragonPose (laugh adds the shake)
    near / far   Arm(...) for the arm nearer / farther from the camera
    anchor   "ground" or "seat"; elev camera elevation; shadow draws the contact shadow
    """
    facing: float = 1
    turn: float = 0.0
    yaw: float = None
    sit: float = 0.0
    seat_h: float = B.BENCH_SEAT_H
    walk: float = 0.0
    phase: float = 0.0
    lean: float = 0.0
    hunch: float = None
    stance: float = 0.0
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    mood: object = "neutral"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    smile: float = None
    laugh: float = 0.0
    blink: float = None
    near: Arm = field(default_factory=Arm)
    far: Arm = field(default_factory=Arm)
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class FolkRig:
    """Attach points returned by every part-B draw function, all in the CALLER's coordinates.
    `points` holds creature-specific extras (e.g. "lamp", "beak", "pipe", "grip", "crystal")."""
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    nose: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    lap: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    seat: tuple = (0.0, 0.0)
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0
    points: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Build:
    """A biped species' proportions (body px at scale 1.0)."""
    pelvis_h: float = 200.0     # standing pelvis joint above the ground
    hip_w: float = 24.0         # half distance between the hip joints
    thigh: float = 95.0
    shin: float = 92.0
    ankle_h: float = 18.0       # ankle joint above the ground (plantigrade feet)
    cannon: float = 0.0         # > 0: digitigrade leg (goat / bird): hock -> hoof length
    cannon_tilt: float = 0.30   # rad the cannon leans (hock behind the hoof)
    sh_y: float = 150.0         # shoulder joints above the pelvis (upright torso)
    sh_z: float = 0.0
    sh_w: float = 50.0          # half shoulder width (joint centres)
    upper_arm: float = 90.0
    forearm: float = 86.0
    hand_len: float = 56.0
    neck_y: float = 172.0       # neck base above the pelvis
    neck_z: float = 4.0
    neck_len: float = 24.0      # neck base -> head pivot
    head_up: float = 30.0       # head pivot -> head centre (head space)
    head_fwd: float = 6.0
    hunch: float = 0.3          # default hunch 0..1
    hunch_fwd: float = 14.0     # how far a full hunch pushes shoulders / neck forward
    stride: float = 150.0       # body px per walk cycle (two steps)
    lift: float = 20.0
    bob: float = 4.0
    breath: float = 0.22
    sit_drop: float = 14.0      # pelvis joint above the seat surface
    sit_back: float = 8.0
    sway: float = 2.0           # idle weight shift (px)
    knee_out: float = 0.15
    fit: float = 1.0            # calibration: the drawn scale is scale * fit, so that scale 1.0
                                # matches base.CAST_HEIGHTS (seat / table heights stay in screen px)


def yaw_of(pose):
    """Body yaw (rad, wrapped to -pi..pi) from pose.yaw or facing + turn."""
    if pose.yaw is not None:
        y = pose.yaw
    else:
        base = {1: 1.0, -1: -1.0, 0: 0.0, 2: math.pi, -2: -math.pi}.get(int(round(pose.facing)), 0.0)
        y = base + pose.turn * 0.6
    return math.atan2(math.sin(y), math.cos(y))


def walk_stride(build, scale=1.0, yaw=1.0):
    """Screen px the anchor travels per walk cycle (so planted feet don't slide)."""
    return build.stride * abs(math.sin(yaw)) * scale * build.fit


def walk_phase(build, distance_px, scale=1.0, yaw=1.0):
    st = walk_stride(build, scale, yaw)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


def expr_of(pose, extra=()):
    """The pose's Expr: mood (+ mood2 blend) + laugh + smile override; extra = [(mood, amount)]."""
    e = B.expr(pose.mood) if pose.mood is not None else B.MOODS["neutral"]
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    for m, u in extra:
        if u > 0:
            e = e.blend(B.expr(m), u)
    if pose.laugh > 0:
        e = e.blend(B.MOODS["laugh"], pose.laugh)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    return e


# ========================================================================================
# per-draw context
# ========================================================================================

class Q:
    """Per-draw context: cr, projection, light, line weight, level of detail, time, skeleton."""
    __slots__ = ("cr", "proj", "light", "lw", "detail", "t", "pose", "yaw", "sit", "M", "S", "pal",
                 "b", "scale", "near", "far", "parts", "x", "y", "dev")

    def P(self, mat):
        p = self.pal.get(mat)
        if p is None:
            p = self.pal[mat] = B.palette(self.light, mat)
        return p

    def shade(self, path, mat, lw=None, **kw):
        if self.detail == 0:                # small on screen: no rim pass (one fill less per part)
            kw["rim"] = 0.0
        return B.shade(self.cr, path, mat, self.light, self.lw if lw is None else lw, **kw)

    def want(self, layer):
        return self.parts is None or layer in self.parts

    def xy(self, v):
        return self.proj.xy(v)

    def depth(self, v):
        return self.proj.depth(v)


LOD_PX = (420.0, 300.0)          # on-screen height (px) for detail 2 / detail 1 (else 0)


def lod_for(dev, height):
    """Level of detail from the creature's ON-SCREEN height (dev = drawn scale x device scale,
    height = its height at scale 1): 2 >= 420 px, 1 >= 300 px, else 0. Small creatures at
    scale 1 (a goblin is 260 px) are small on screen, so they simplify like distant big ones."""
    h = dev * height
    return 2 if h >= LOD_PX[0] else 1 if h >= LOD_PX[1] else 0


def begin(cr, x, y, scale, pose, light, t, detail, build, mats, parts=None, line=B.LINE, skel=None, height=None):
    """Set up the context (cr is saved, translated to the anchor and scaled) and the skeleton.
    Pair with end(). height = the creature's height at scale 1.0 (CAST_HEIGHTS): the level of
    detail then follows its on-screen size (lod_for); without it, the scale thresholds."""
    q = Q()
    outer = scale
    scale = scale * build.fit
    q.cr, q.M, q.light, q.t, q.pose, q.pal, q.b, q.scale = cr, mats, light or B.LIGHTS["neutral"], t, pose, {}, build, scale
    q.parts = None if parts is None else ({parts} if isinstance(parts, str) else set(parts))
    q.yaw = yaw_of(pose)
    q.proj = Proj(q.yaw, pose.elev)
    q.sit = clamp(pose.sit)
    q.near = -1.0 if math.sin(q.yaw) >= 0 else 1.0
    q.far = -q.near
    dev = scale * B.device_scale(cr)
    q.dev = dev
    if detail is None:
        detail = lod_for(dev, height) if height else (2 if dev >= 0.9 else 1 if dev >= 0.55 else 0)
    q.detail = detail
    q.lw = B.line_for(line, dev, 1.0 / build.fit)
    q.x, q.y = x, y
    cr.save()
    cr.translate(x, y + (pose.seat_h * outer * q.sit if pose.anchor == "seat" else 0.0))
    cr.scale(scale, scale)
    q.S = (skel or skeleton)(q)
    return q


def end(q, rig):
    """Restore cr and convert every attach point in `rig` (a FolkRig holding body-local 2D
    points) to the caller's coordinates."""
    cr = q.cr
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    for k in ("head", "mouth", "nose", "top", "chest", "lap", "seat"):
        setattr(rig, k, C(getattr(rig, k)))
    rig.eyes = [C(e) for e in rig.eyes]
    rig.feet = [C(f) for f in rig.feet]
    rig.points = {k: (C(v) if isinstance(v, tuple) and len(v) == 2 else v) for k, v in rig.points.items()}
    for hf in (rig.hand_near, rig.hand_far):
        if hf is not None:
            hf.x, hf.y = C((hf.x, hf.y))
            hf.tips = [C(tp) for tp in hf.tips]
            hf.palm = C(hf.palm)
            hf.scale *= q.scale
    rig.scale = q.scale
    rig.yaw = q.yaw
    rig.facing = 1.0 if math.sin(q.yaw) >= 0 else -1.0
    return rig


def base_rig(q, head_pts):
    """A FolkRig filled with the skeleton's standard body points (body-local; end() converts)."""
    S, proj = q.S, q.proj
    rig = FolkRig()
    rig.head = head_pts.get("center", proj.xy(S["head_c"]))
    rig.mouth = head_pts.get("mouth", rig.head)
    rig.nose = head_pts.get("nose", rig.head)
    rig.eyes = list(head_pts.get("eyes", []))
    rig.top = head_pts.get("top", rig.head)
    rig.chest = proj.xy(S["chest"])
    rig.lap = proj.xy(v_lerp(S["pelvis"], v_lerp(S["knee"][0], S["knee"][1], 0.5), 0.6))
    rig.feet = [proj.xy(f["ground"]) for f in S["feet"]]
    rig.seat = (0.0, -q.pose.seat_h / q.b.fit * q.sit)
    return rig


# ========================================================================================
# skeleton (body space)
# ========================================================================================

def skeleton(q):
    """Generic biped skeleton: pelvis (walk bob, idle weight shift, sit), torso tilt (hunch,
    lean, the sit-down counterbalance, laugh), shoulders, neck, head, legs (plantigrade or
    digitigrade, feet planted by the walk cycle, seated feet planted or dangling)."""
    b, pose, t, sit = q.b, q.pose, q.t, q.sit
    S = {}
    br = B.breathing(t, b.breath, pose.seed)
    laugh = clamp(pose.laugh)
    hunch = clamp((b.hunch if pose.hunch is None else pose.hunch) - 0.25 * laugh, 0.0, 1.4)
    walk = clamp(pose.walk)
    wc = B.walk_cycle(pose.phase, stride=b.stride, lift=b.lift, bob=b.bob, swing=1.0)
    shake = laugh * (math.sin(t * TAU * 6.0 + pose.seed) * 2.2 + math.sin(t * TAU * 2.9) * 1.0)
    idle = (1.0 - walk) * (1.0 - sit)
    sx = b.sway * B.sway(t, 0.22, pose.seed + 5) * idle
    S.update(br=br, hunch=hunch, wc=wc, walk=walk, shake=shake, laugh=laugh)

    stand = (sx, -b.pelvis_h + walk * wc.hip_dy + 0.6 * b.bob * abs(pose.stance), 0.0)
    seat = (0.0, -pose.seat_h / b.fit - b.sit_drop, -b.sit_back)
    arc = math.sin(math.pi * sit)
    pel = v_add(v_lerp(stand, seat, smooth(sit)), (0.0, 0.0, -0.18 * b.thigh * arc))
    S["pelvis"] = pel
    tilt = 0.10 * hunch + 0.32 * pose.lean + 0.05 * walk + 0.34 * arc - 0.08 * laugh
    S["tilt"] = tilt
    R = m_rot_x(-tilt)
    S["R"] = R

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    hz = b.hunch_fwd * hunch
    S["waist"] = T((0.0, -0.3 * b.sh_y, 2.0))
    S["chest"] = T((0.0, -0.68 * b.sh_y, 6.0 + 2.0 * br))
    sh_y = -b.sh_y + 0.06 * b.sh_y * hunch - 2.0 * br - shake * 0.6
    sh_z = b.sh_z + hz
    S["sh_c"] = T((0.0, sh_y, sh_z))
    S["shoulders"] = {s: T((s * b.sh_w, sh_y + 4.0 * hunch, sh_z - 2.0)) for s in (-1.0, 1.0)}
    S["neck_base"] = T((0.0, -b.neck_y + 0.05 * b.sh_y * hunch, b.neck_z + hz * 1.2))
    na = 0.15 + 0.55 * hunch
    pivot = v_add(S["neck_base"], m_vec(R, (0.0, -b.neck_len * math.cos(na), b.neck_len * math.sin(na))))
    S["neck_top"] = pivot
    nod = pose.head_nod * 0.42 - 0.08 * hunch + 0.22 * laugh + 0.02 * br
    hy = pose.head_turn * 1.1
    hr = pose.head_tilt + 0.05 * laugh * math.sin(t * 9.0)
    RH = m_mul(m_rot_y(hy), m_mul(m_rot_x(nod + tilt * 0.35), m_rot_z(hr)))
    S["RH"] = RH
    S["head_yaw"] = q.yaw + hy
    hb = walk * wc.head_bob * 0.8
    S["head_c"] = v_add(pivot, v_add(m_vec(RH, (0.0, -b.head_up, b.head_fwd)), (0.0, hb + shake * 0.5, 0.0)))
    S["hip"] = {s: v_add(pel, (s * b.hip_w, 6.0, 0.0)) for s in (-1.0, 1.0)}

    feet = []
    u_feet = smooth((sit - 0.55) / 0.45)        # feet stay planted until the seat takes the weight
    st = clamp(pose.stance, -1.0, 1.0) * b.stride * 0.17
    seat_hip_y = -pose.seat_h / b.fit - b.sit_drop + 6.0
    for s in (-1.0, 1.0):
        hip = S["hip"][s]
        fz, lift, toe, planted = wc.feet[0 if s < 0 else 1]
        sz = st * s * (1.0 - walk)
        # seated: thigh forward, shin hanging from the knee -- planted if the ground is in
        # reach, dangling (a slow little swing) if the seat is too high (dwarf, gnome)
        knee_s = (s * (b.hip_w + 5.0), seat_hip_y + 4.0, -b.sit_back + b.thigh * 0.96)
        if b.cannon > 0:
            ground = (s * (b.hip_w + 2.0), -lift * walk, fz * walk + 2.0 + sz)
            ca = b.cannon_tilt + 0.5 * toe * walk
            stand_h = v_add(ground, (0.0, -b.ankle_h - b.cannon * math.cos(ca), -b.cannon * math.sin(ca)))
            g_sit = (knee_s[0], 0.0, knee_s[2] + 4.0)
            sa = 0.95
            sit_h = v_add(g_sit, (0.0, -b.ankle_h - b.cannon * math.cos(sa), -b.cannon * math.sin(sa)))
            hock = v_lerp(stand_h, sit_h, u_feet)
            ground = v_lerp(ground, g_sit, u_feet)
            knee, ank = B.ik3(hip, hock, b.thigh, b.shin, (s * b.knee_out, lerp(0.15, -0.4, smooth(sit)), 1.0))
            feet.append({"hip": hip, "knee": knee, "ankle": ank, "ground": ground, "toe": toe * walk * (1 - smooth(sit)),
                         "side": s, "lift": lift * walk, "cannon": True})
            continue
        stand_a = (s * (b.hip_w + 2.0), -b.ankle_h - lift * walk, fz * walk + 2.0 + sz)
        drop = (-b.ankle_h) - knee_s[1]
        if drop <= b.shin * 0.97:
            fwd = math.sqrt(max(0.0, (b.shin * 0.97) ** 2 - drop * drop)) * 0.55
            sit_a = (knee_s[0], -b.ankle_h, knee_s[2] + fwd)
        else:
            sw = 0.10 * math.sin(t * 1.7 + s * 1.3 + pose.seed)
            sit_a = (knee_s[0], knee_s[1] + b.shin * 0.97 * math.cos(sw), knee_s[2] + b.shin * 0.97 * math.sin(sw) + 3.0)
        ankle = v_lerp(stand_a, sit_a, u_feet)
        knee, ank = B.ik3(hip, ankle, b.thigh, b.shin, (s * b.knee_out, lerp(0.15, -0.35, smooth(sit)), 1.0))
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "ground": (ank[0], 0.0 if ank[1] > -b.ankle_h - 1 else ank[1] + b.ankle_h, ank[2]),
                     "toe": toe * walk * (1.0 - smooth(sit)), "side": s, "lift": lift * walk, "cannon": False})
    S["feet"] = feet
    S["knee"] = [feet[0]["knee"], feet[1]["knee"]]
    return S


# ========================================================================================
# arm gestures: fn(q, sk, side, arm) -> G(target, hand pose, hang, layer, pole, thumb)
#   target  wrist target in body space; hang = extra hand angle (rad)
#   layer   "auto" (by side), "mid" (over the torso, under the head), "front" (over the head)
#   pole    where the elbow points (body space); thumb: "fwd" | "in" | "out" | "up" | "down"
# ========================================================================================

class G(NamedTuple):
    target: tuple
    hand: str = "relaxed"
    hang: float = 0.0
    layer: str = "auto"
    pole: tuple = None
    thumb: str = "fwd"


def _AL(q):
    return q.b.upper_arm + q.b.forearm


def _rest_k(sit):
    return smooth(clamp((sit - 0.25) / 0.6))


def g_rest(q, sk, side, arm):
    """Hanging at the side (standing); on the thighs (seated). Blends while sitting."""
    AL = _AL(q)
    stand = v_add(sk, (side * 0.10 * AL, 0.90 * AL, 0.07 * AL))
    k = _rest_k(q.sit)
    if k <= 0.0:
        return G(stand, "relaxed", 0.0, "auto", (side * 0.3, 0.2, -1.0))
    S = q.S
    kn = S["knee"][0 if side < 0 else 1]
    on_thigh = v_add(v_lerp(S["hip"][side], kn, 0.62), (side * 6.0, -0.12 * q.b.thigh - 8.0, -6.0))
    return G(v_lerp(stand, on_thigh, k), "relaxed", 0.25 * k, "auto",
             v_lerp((side * 0.3, 0.2, -1.0), (side * 1.0, 0.45, 0.05), k))


def g_slump(q, sk, side, arm):
    """Arms dropped, heavy and limp (S5: the orc stops fighting)."""
    AL = _AL(q)
    return G(v_add(sk, (side * 0.04 * AL, 0.96 * AL, 0.10 * AL)), "relaxed", 0.1, "auto", (side * 0.2, 0.1, -1.0))


def g_guard(q, sk, side, arm):
    """Fists up in front of the chest (squaring up)."""
    AL = _AL(q)
    return G(v_add(sk, (-side * 0.10 * AL, 0.30 * AL, 0.50 * AL)), "fist", -0.6, "front", (side * 0.8, 1.0, -0.2), "up")


def g_shove(q, sk, side, arm):
    """Two-handed shove. phase 0..0.35 wind-up (hands drawn back to the chest), 0.35..0.55
    thrust (arms shoot out, palms flat), 0.55..1 recover toward a guard."""
    AL = _AL(q)
    ph = arm.phase
    back = v_add(sk, (-side * 0.06 * AL, 0.36 * AL, 0.22 * AL))
    out = v_add(sk, (-side * 0.12 * AL, 0.22 * AL, 0.92 * AL))
    guard = v_add(sk, (-side * 0.08 * AL, 0.34 * AL, 0.48 * AL))
    sy = getattr(q.pose, "shove_y", None)        # aim: hands at this height above the pelvis
    if sy is not None:
        y = q.S["pelvis"][1] - sy
        dy = y - out[1]
        out = (out[0], y, out[2] - 0.25 * max(0.0, dy))
        back = (back[0], back[1] + 0.5 * dy, back[2])
    if ph < 0.35:
        p = v_lerp(guard, back, core.inout_sine(ph / 0.35))
    elif ph < 0.55:
        p = v_lerp(back, out, core.out_cubic((ph - 0.35) / 0.2))
    else:
        p = v_lerp(out, guard, core.inout_sine((ph - 0.55) / 0.45))
    return G(p, "flat", -1.25, "front", (side * 0.7, 1.0, -0.4), "in")


def g_stagger(q, sk, side, arm):
    """Knocked back off balance (being shoved): arms flung out and back at chest height for
    balance, hands open; phase wobbles them."""
    AL = _AL(q)
    w = math.sin(arm.phase * TAU * 1.5) * 0.08
    return G(v_add(sk, (side * (0.58 + w) * AL, (0.30 - w) * AL, -0.30 * AL)), "open", 0.0, "auto",
             (side * 0.3, 1.0, -0.4), "fwd")


def g_hug(q, sk, side, arm):
    """Arms wrapped round a partner standing `reach` px in front (pose.hug_reach), whose torso
    is hug_w wide and hug_d deep there (pose.hug_w / hug_d), at hug_y height above the pelvis
    (pose.hug_y_far, if set, for the far arm: one arm over the shoulder, one under). The near
    arm wraps the partner's near side, the far arm the far side; the hands spread on the
    partner's back. arm.phase opens the arms a little (0 = closed tight)."""
    p = q.pose
    reach = getattr(p, "hug_reach", 90.0)
    hw = getattr(p, "hug_w", 60.0)
    hd = getattr(p, "hug_d", 40.0)
    hy = getattr(p, "hug_y", 0.62 * q.b.sh_y)
    hyf = getattr(p, "hug_y_far", None)
    near = side == q.near
    if hyf is not None and not near:       # "one arm over, one under"
        hy = hyf
    pel = q.S["pelvis"]
    o = arm.phase
    high = hy > 0.3 * q.b.sh_y
    if high:                                # over the shoulders: hands meet on the partner's back
        tgt = (side * (hw * (0.25 + 0.9 * o)), pel[1] - hy, pel[2] + reach + hd * (0.72 - 0.9 * o))
        pole = (side * 1.0, 0.35, -0.15)
    else:                                   # round the waist: the upper arm hangs down the side,
        # only the forearm curls round (it never crosses the partner's face)
        tgt = (side * (hw * (0.55 + 0.9 * o)), pel[1] - hy, pel[2] + reach + hd * (0.3 - 0.9 * o))
        pole = (side * 0.45, 1.0, -1.0)
    d = v_sub(tgt, sk)
    L = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
    lim = 0.93 * _AL(q)                     # keep the elbow bent: never a straight arm across
    if L > lim:
        tgt = v_add(sk, (d[0] * lim / L, d[1] * lim / L, d[2] * lim / L))
    return G(tgt, "relaxed", 0.35, "auto", pole, "down")


def g_cheer(q, sk, side, arm):
    """Arm up, fist pumping (phase drives the pump)."""
    AL = _AL(q)
    pump = 0.08 * math.sin(arm.phase * TAU)
    return G(v_add(sk, (side * 0.30 * AL, -(0.84 + pump) * AL, 0.12 * AL)), "fist", 0.0, "auto",
             (side * 1.0, 0.4, -0.3), "in")


def g_raise_crystal(q, sk, side, arm):
    """Holding a scrying crystal up to film: forearm up, the grip at brow level out in front and
    to the side, so the crystal stands above eye level beside the face (the face stays visible
    under its glow; from behind, the crystal's face shows past the head)."""
    AL = _AL(q)
    hc = q.S["head_c"]
    tgt = (sk[0] * 0.80 + side * 0.06 * AL, hc[1] - 0.06 * AL, hc[2] + 0.50 * AL)
    return G(tgt, "grip", -0.9, "front", (side * 1.0, 0.9, -0.2), "up")


def g_lower_crystal(q, sk, side, arm):
    """The crystal held low in front of the belly, looked down at."""
    AL = _AL(q)
    return G(v_add(sk, (-side * 0.12 * AL, 0.62 * AL, 0.45 * AL)), "grip", -1.3, "front", (side * 0.9, 1.0, -0.4), "up")


def g_tankard(q, sk, side, arm):
    """A tankard held at the chest; phase 0..1 raises it in a toast (1 = high)."""
    AL = _AL(q)
    lo = v_add(sk, (side * 0.02 * AL, 0.50 * AL, 0.45 * AL))
    hi = v_add(sk, (side * 0.10 * AL, -0.55 * AL, 0.42 * AL))
    return G(v_lerp(lo, hi, core.inout_sine(clamp(arm.phase))), "grip", -1.25, "front", (side * 1.0, 0.8, -0.4), "up")


def g_offer(q, sk, side, arm):
    """Open palm forward / up: receiving bread (S7) -- over the knees when seated."""
    AL = _AL(q)
    return G(v_add(sk, (-side * 0.02 * AL, lerp(0.55, 0.45, q.sit) * AL, lerp(0.62, 0.72, q.sit) * AL)), "offer", 0.0,
             "front", (side * 0.9, 1.0, -0.3), "out")


def g_reach(q, sk, side, arm):
    """Reaching out to take something (phase 0 = hand still near, 1 = arm extended)."""
    AL = _AL(q)
    u = core.inout_sine(clamp(arm.phase if arm.phase else 1.0))
    a = v_add(sk, (side * 0.05 * AL, 0.60 * AL, 0.30 * AL))
    b = v_add(sk, (-side * 0.04 * AL, 0.36 * AL, 0.86 * AL))
    return G(v_lerp(a, b, u), "cup", -0.4, "front", (side * 0.9, 1.0, -0.3), "up")


def g_point(q, sk, side, arm):
    AL = _AL(q)
    return G(v_add(sk, (-side * 0.04 * AL, 0.12 * AL, 0.92 * AL)), "point", 0.0, "front", (side * 0.8, 1.0, -0.2), "up")


def g_wave(q, sk, side, arm):
    AL = _AL(q)
    w = 0.10 * math.sin(arm.phase * TAU * 2.0)
    return G(v_add(sk, (side * (0.38 + w) * AL, -0.42 * AL, 0.18 * AL)), "open", 0.0, "auto", (side * 1.0, 1.0, -0.2), "in")


def g_talk(q, sk, side, arm):
    """Explaining with an open hand at waist height; phase wiggles it (lean in and talk)."""
    AL = _AL(q)
    w = 0.05 * math.sin(arm.phase * TAU * 2.0)
    return G(v_add(sk, (side * 0.12 * AL, (0.52 + w) * AL, 0.42 * AL)), "offer", -0.2, "front", (side * 1.0, 1.0, -0.4), "out")


def g_arms_crossed(q, sk, side, arm):
    ch_ = q.S["chest"]
    AL = _AL(q)
    return G(v_add(ch_, (-side * 0.25 * AL, 0.10 * AL + (4.0 if side < 0 else 0.0), 0.24 * AL + (5.0 if side < 0 else 0.0))),
             "relaxed", 0.0, "front", (side * 1.0, 0.6, 0.2), "up")


def g_on_table(q, sk, side, arm):
    """Forearms resting on a table edge in front (seated at a tavern table): pose.table_h is
    the table top above the ground."""
    AL = _AL(q)
    th = getattr(q.pose, "table_h", None)
    th = (q.pose.seat_h / q.b.fit + 0.45 * q.b.sh_y) if th is None else th / q.b.fit
    return G((sk[0] * 0.7 - side * 0.10 * AL, -th - 6.0, sk[2] + 0.62 * AL), "relaxed", -0.6, "front",
             (side * 1.0, 0.7, -0.3), "up")


def g_knees(q, sk, side, arm):
    """Seated, hands on the knees."""
    kn = q.S["knee"][0 if side < 0 else 1]
    return G(v_add(kn, (side * 4.0, -14.0, 2.0)), "relaxed", 0.6, "auto", (side * 1.0, 0.5, -0.2), "fwd")


def g_strap(q, sk, side, arm):
    """Hand gripping a cross-body strap at the chest (hesitating, holding on)."""
    ch_ = q.S["chest"]
    AL = _AL(q)
    return G(v_add(ch_, (side * 0.12 * AL, -0.04 * AL, 0.24 * AL)), "grip", -1.4, "front", (side * 1.0, 1.0, -0.1), "in")


def g_drag(q, sk, side, arm):
    """Both hands forward and low, gripping (dragging a bench): pose.grip = (forward, height)
    of the grip point relative to the anchor (default: a bench end at seat height)."""
    fwd, h = getattr(q.pose, "grip", (0.9 * _AL(q), B.BENCH_SEAT_H))
    return G((side * (q.b.sh_w * 0.55), -h, fwd), "grip", -0.2, "front", (side * 1.0, 0.8, -0.2), "in")


def g_eat(q, sk, side, arm):
    """Bringing food to the mouth (phase 0 = hand in the lap, 1 = at the mouth), held in front
    of the face, a little to the side so the mouth still shows."""
    hc = q.S["head_c"]
    AL = _AL(q)
    lap = v_add(sk, (-side * 0.05 * AL, 0.62 * AL, 0.40 * AL))
    mouth = (hc[0] + side * 0.10 * AL, hc[1] + 0.20 * AL, hc[2] + 0.36 * AL)
    u = core.inout_sine(clamp(arm.phase if arm.phase else 1.0))
    return G(v_lerp(lap, mouth, u), "grip", -1.0, "front", (side * 1.0, 1.0, -0.2), "up")


def g_chest(q, sk, side, arm):
    """Hand on the heart."""
    ch_ = q.S["chest"]
    AL = _AL(q)
    return G(v_add(ch_, (side * 0.10 * AL, -0.06 * AL, 0.22 * AL)), "flat", -1.6, "front", (side * 1.0, 1.0, -0.1), "in")


def g_hip(q, sk, side, arm):
    """Hand on the hip, elbow out (attitude): the back of the wrist on the waist."""
    AL = _AL(q)
    w = q.S["waist"]
    return G(v_add(w, (side * (q.b.hip_w + 0.24 * AL), 0.10 * AL, -0.04 * AL)), "fist", 1.2, "auto",
             (side * 1.0, -0.1, -0.7), "fwd")


GESTURES = {
    "hip": g_hip, "hand_on_hip": g_hip,
    "rest": g_rest, "slump": g_slump, "guard": g_guard, "shove": g_shove, "stagger": g_stagger, "hug": g_hug,
    "cheer": g_cheer, "raise_crystal_film": g_raise_crystal, "raise_crystal": g_raise_crystal,
    "lower_crystal": g_lower_crystal, "tankard": g_tankard, "hold_tankard": g_tankard,
    "hand_out_offer": g_offer, "offer": g_offer, "reach": g_reach, "take": g_reach, "point": g_point,
    "wave": g_wave, "talk": g_talk, "arms_crossed": g_arms_crossed, "on_table": g_on_table,
    "knees": g_knees, "strap": g_strap, "drag": g_drag, "hand_on_chest": g_chest, "eat": g_eat,
}


def solve_arm(q, side, arm, gestures=GESTURES):
    """Gesture -> (shoulder, elbow, wrist) in body space + hand pose + layer hint."""
    S, b = q.S, q.b
    sk = S["shoulders"][side]
    fn = gestures.get(arm.gesture, gestures["rest"])
    g = fn(q, sk, side, arm)
    tgt, hp, hang, z, pole, thumb = g
    if arm.amt < 1.0:
        g0 = gestures.get(arm.prev, gestures["rest"])(q, sk, side, arm)
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 0.07 * _AL(q)     # hands travel on an arc
        tgt = v_add(v_lerp(g0.target, tgt, u), (side * arc * 0.5, -arc * 0.4, arc))
        hang = lerp(g0.hang, hang, u)
        pole = v_lerp(g0.pole or (side, 0.6, -0.3), pole or (side, 0.6, -0.3), u)
        if u < 0.5:
            hp, thumb = g0.hand, g0.thumb
            if g0.layer != "auto":
                z = g0.layer
    if arm.target is not None:
        tgt = arm.target
    if arm.hand:
        hp = arm.hand
    if arm.gesture in ("rest", "slump") and q.sit < 0.6:
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"]
        tgt = v_add(tgt, (0.0, -abs(sw) * 0.03 * _AL(q), sw * 0.17 * _AL(q) + 1.5 * math.sin(q.t * 0.9 + side)))
    if arm.gesture in ("rest", "slump", "cheer", "tankard", "hold_tankard"):
        tgt = v_add(tgt, (0.0, S["shake"] * 0.6, 0.0))
    elbow, wrist = B.ik3(sk, tgt, b.upper_arm, b.forearm, pole or (side * 0.9, 0.8, -0.3))
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side,
            "thumb": thumb}


def arm_layer(q, A):
    """'back' (behind the torso), 'mid' (over the torso, under the head) or 'front'."""
    z, near = A["z"], A["side"] == q.near
    c, s = math.cos(q.yaw), abs(math.sin(q.yaw))
    frontish = s < 0.38
    if c < -0.25:                         # seen from behind: the body hides what is in front of it
        if z in ("front", "mid"):
            return "back"
        return "mid" if (frontish or near) else "back"
    if z == "auto":
        return "mid" if frontish else ("front" if near else "back")
    if z == "front":
        return "front" if (near or frontish) else "mid"
    return z


def hand_flip(q, A, ang):
    """Mirror the 2D hand so its thumb points the way the gesture wants (projected)."""
    side = A["side"]
    th = A["thumb"]
    v = {"fwd": (0.0, 0.0, 1.0), "in": (-side, 0.0, 0.0), "out": (side, 0.0, 0.0), "up": (0.0, -1.0, 0.0),
         "down": (0.0, 1.0, 0.0)}.get(th, (0.0, 0.0, 1.0))
    tx, ty = q.proj.xy(v)
    ox, oy = q.proj.xy((0.0, 0.0, 0.0))
    tx, ty = tx - ox, ty - oy
    # thumb side of an unflipped base.hand drawn at angle `ang`: local -y -> (sin a, -cos a)
    d = tx * math.sin(ang) - ty * math.cos(ang)
    if abs(d) < 0.25:                      # ambiguous (thumb toward the camera): the dragon's rule
        return (side > 0) == (math.sin(q.yaw) >= 0)
    return d < 0


# ========================================================================================
# drawing helpers
# ========================================================================================

_UNIT = {}


def ellipsoid2d(f, c, rx, ry, rz, n=14):
    """EXACT silhouette of an ellipsoid (centre c, semi-axes rx, ry, rz along its local axes)
    under an affine map f (point -> 2D): the image of an ellipsoid under an affine 3D->2D map is
    an ellipse whose shape matrix is M M^T (M = images of the scaled axes). n points on it.
    ~10x cheaper than sampling rings and hulling them."""
    o = f(c)
    a = f((c[0] + rx, c[1], c[2]))
    b = f((c[0], c[1] + ry, c[2]))
    d = f((c[0], c[1], c[2] + rz))
    m = ((a[0] - o[0], a[1] - o[1]), (b[0] - o[0], b[1] - o[1]), (d[0] - o[0], d[1] - o[1]))
    sxx = m[0][0] * m[0][0] + m[1][0] * m[1][0] + m[2][0] * m[2][0]
    syy = m[0][1] * m[0][1] + m[1][1] * m[1][1] + m[2][1] * m[2][1]
    sxy = m[0][0] * m[0][1] + m[1][0] * m[1][1] + m[2][0] * m[2][1]
    tr2 = (sxx + syy) * 0.5
    disc = math.sqrt(max(0.0, tr2 * tr2 - (sxx * syy - sxy * sxy)))
    r1, r2 = math.sqrt(tr2 + disc), math.sqrt(max(0.0, tr2 - disc))
    ang = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
    ca, sa = math.cos(ang), math.sin(ang)
    u = _UNIT.get(n)
    if u is None:
        u = _UNIT[n] = [(math.cos(TAU * i / n), math.sin(TAU * i / n)) for i in range(n)]
    return [(o[0] + r1 * cu * ca - r2 * su * sa, o[1] + r1 * cu * sa + r2 * su * ca) for cu, su in u]


def blob_pts(proj, c, rx, ry, rz, n=12):
    """Silhouette points of a body-space ellipsoid (exact projected ellipse) for hulls."""
    return ellipsoid2d(proj.xy, c, rx, ry, rz, n)


def hull_union(q, groups, mat, size, tension=0.85, **kw):
    """Several convex point groups -> ONE union with one dilated outline, shaded once.
    Returns (Path of the union, Palette)."""
    cr, lw = q.cr, q.lw
    hulls = [core.convex_hull(g) for g in groups if len(g) >= 3]
    pal = q.P(mat)
    cr.new_path()
    for h in hulls:
        core.smooth_closed(cr, B.offset_closed(h, lw), tension)
    core.src(cr, kw.pop("line_color", None) or pal.line)
    cr.fill()
    for h in hulls:
        core.smooth_closed(cr, h, tension)
    shape = Path(cr)
    q.shade(shape, mat, outline=False, size=size, **kw)
    return shape, pal


def limb(q, pts, radii, mat, size, samples=4, rim=0.5, **kw):
    """A tapered tube through 2D points (one contour, rounded joints) + outline, shaded."""
    shp, out = B.tube_paths(q.cr, pts, radii, q.lw, samples=samples, tension=0.75)
    pal = q.shade(shp, mat, outline=out, size=size, rim=rim, **kw)
    return shp, pal


def ring_edges(q, rings):
    """Projected silhouette edges (left, right) of a stack of cross-sections (c, a, cz)."""
    left, right = [], []
    for (c, a, cz) in rings:
        x, y, hw = q.proj.ellipse(c, a, cz)
        left.append((x - hw, y))
        right.append((x + hw, y))
    return left, right


def hem_curve(q, c, a, cz, n=8, wave=0.0, phase=0.0):
    """The visible bottom edge of a garment ring: for each x across its width the LOWEST
    crossing of the projected ring (the near edge), left -> right, optionally rippled."""
    proj = q.proj
    ring = [proj((c[0] + math.sin(TAU * i / 24) * a, c[1], c[2] + math.cos(TAU * i / 24) * cz)) for i in range(24)]
    x, _y, hw = proj.ellipse(c, a, cz)
    xL, xR = x - hw, x + hw
    out = []
    for i in range(1, n):
        xx = lerp(xL, xR, i / n)
        best = None
        for k in range(24):
            pa, pb = ring[k], ring[(k + 1) % 24]
            if (pa[0] - xx) * (pb[0] - xx) <= 0 and pa[0] != pb[0]:
                yy = pa[1] + (pb[1] - pa[1]) * (xx - pa[0]) / (pb[0] - pa[0])
                best = yy if best is None else max(best, yy)
        if best is not None:
            out.append((xx, best + wave * math.sin(i * 2.1 + phase)))
    return out


def front_arc(q, c, a, cz, n=9, extend=1.0):
    """Projected points of the half of a horizontal ring (centre c, half-axes a / cz) facing
    the camera, sorted left -> right: the visible edge of a belt, a hem, a collar."""
    phc = -q.yaw
    out = []
    for i in range(n):
        ph = phc - math.pi / 2 * extend + math.pi * extend * i / (n - 1)
        out.append(q.proj.xy((c[0] + math.sin(ph) * a, c[1], c[2] + math.cos(ph) * cz)))
    out.sort(key=lambda p: p[0])
    return out


def dome_cap(q, P, D, c, r, h, mat, size, brim=1.5, rim=0.8, n=16, shadow=1.0, extra=()):
    """A round cap on a head: a dome of radius r / height h on a circular rim (head-space centre
    c, the rim plane horizontal in head space) + a brim ring r + brim. Drawn as the hull of the
    dome clipped to the region above the rim's NEAR half -- so when the head tips back the back
    of the cap never paints over the face (it is behind the skull) -- with an ink line along
    the visible brim edge. `extra`: more head-space points for the hull (e.g. the peak of a
    pointed felt hat). P/D from head_xf. Returns (Path, Palette, near-rim 2D points)."""
    cr = q.cr
    rb = r + brim
    ring = [(c[0] + rb * math.cos(TAU * i / n), c[1], c[2] + rb * math.sin(TAU * i / n)) for i in range(n)]
    dc = D(c)
    near = [D(p) >= dc for p in ring]
    start = next((i for i in range(n) if near[i] and not near[i - 1]), 0)
    run, i = [], start
    while near[i % n] and len(run) < n:
        run.append(i % n)
        i += 1
    arc = [P(ring[j]) for j in [(start - 1) % n] + run + [i % n]]   # + the two tangent points
    if arc[0][0] > arc[-1][0]:
        arc.reverse()
    pts = ellipsoid2d(P, c, r, h, r, 16) + ellipsoid2d(P, c, rb, 0.01, rb, 16) + [P(e) for e in extra]
    big = 10.0 * rb * max(1.0, abs(q.scale))
    y_top = min(p[1] for p in pts) - big
    clip = [(arc[0][0] - big, arc[0][1])] + arc + [(arc[-1][0] + big, arc[-1][1]), (arc[-1][0] + big, y_top),
                                                    (arc[0][0] - big, y_top)]
    cr.save()
    cr.new_path()
    core.polygon(cr, clip)
    cr.clip()
    shp, pal = hull_union(q, [pts], mat, size, rim=rim, shadow=shadow)
    cr.restore()
    cr.new_path()
    core.smooth_open(cr, arc, 0.8)
    cr.set_line_width(q.lw * 1.4)
    cr.set_line_cap(1)
    core.src(cr, pal.line)
    cr.stroke()
    return shp, pal, arc


def belt(q, c, a, cz, half_h, mat, buckle_mat=None, buckle_w=11.0, rim=0.0):
    """A belt: the camera-facing half of a band round the body at ring (c, a, cz), half_h tall,
    and a buckle at the front when it faces the camera. Returns the belt palette."""
    cr = q.cr
    up = front_arc(q, v_add(c, (0.0, -half_h, 0.0)), a, cz)
    lo = front_arc(q, v_add(c, (0.0, half_h, 0.0)), a + 0.5, cz + 0.5)
    shp, so = B.smooth_paths(cr, up + lo[::-1], q.lw, 0.6)
    pal = q.shade(shp, mat, outline=so, size=half_h * 2.0, rim=rim)
    if buckle_mat is not None:
        bp = q.proj((c[0], c[1], c[2] + cz + 1.0))
        if bp[2] > 0.3 * cz:
            w = buckle_w * max(0.35, q.proj.c)
            cr.new_path()
            core.rounded_rect(cr, bp[0] - w, bp[1] - half_h - 2.0, 2 * w, 2 * half_h + 4.0, 4.0)
            bpal = q.P(buckle_mat)
            B.flat(cr, Path(cr), bpal.lit, q.lw * 0.8, bpal.line)
            if q.detail >= 2:
                B.detail_lines(cr, [[(bp[0] - w * 0.55, bp[1] - half_h * 0.5), (bp[0] - w * 0.55, bp[1] + half_h * 0.5)],
                                    [(bp[0] - w * 0.6, bp[1]), (bp[0] + w * 1.2, bp[1])]], q.lw * 1.0, pal.line, 0.9)
                B.sheen(cr, bp[0] - w * 0.3, bp[1] - half_h * 0.5, w * 0.5, 2.0, alpha=0.5)
    return pal


def shoulder_top(q, ring0, neck_r=16.0):
    """The shoulder line over the neck base for a garment/torso silhouette (right -> left)."""
    c0, a0, cz0 = ring0
    x0, y0, hw0 = q.proj.ellipse(c0, a0, cz0)
    nb = q.proj.xy(q.S["neck_base"])
    return [(x0 + hw0 * 0.92, y0 - 4.0), (lerp(x0 + hw0, nb[0], 0.6), y0 - 12.0), (nb[0] + neck_r, nb[1] - 2.0),
            (nb[0] - neck_r, nb[1] - 2.0), (lerp(x0 - hw0, nb[0], 0.6), y0 - 12.0), (x0 - hw0 * 0.92, y0 - 4.0)]


def inside_convex(hull, p):
    """True if 2D point p is inside the convex polygon `hull` (either winding)."""
    n = len(hull)
    sgn = 0.0
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        c = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if c != 0.0:
            if sgn == 0.0:
                sgn = c
            elif (c > 0) != (sgn > 0):
                return False
    return True


def clamp_into(hull, pts, margin=0.92):
    """Pull every point of `pts` that lies outside the convex `hull` toward the hull's centroid
    until it is inside (scaled by `margin`): keeps a hole inside its shape."""
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    out = []
    for p in pts:
        if inside_convex(hull, p):
            out.append(p)
            continue
        lo, hi = 0.0, 1.0
        for _ in range(7):
            m = (lo + hi) / 2
            if inside_convex(hull, (cx + (p[0] - cx) * m, cy + (p[1] - cy) * m)):
                lo = m
            else:
                hi = m
        k = lo * margin
        out.append((cx + (p[0] - cx) * k, cy + (p[1] - cy) * k))
    return out


def area2(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a


def digi_legs(q, radii, mat, size, rim=0.5, contour=True):
    """BOTH digitigrade legs (hip -> knee -> hock -> hoof top) as one union, shaded once.
    radii = (hip, knee, hock, fetlock)."""
    cr, lw, proj = q.cr, q.lw, q.proj
    outs, shapes = [], []
    spines = []
    for f in q.S["feet"]:
        g = f["ground"]
        top_hoof = (g[0], g[1] - q.b.ankle_h * 0.9, g[2] + 2.0)
        sp = [proj.xy(f["hip"]), proj.xy(f["knee"]), proj.xy(f["ankle"]), proj.xy(top_hoof)]
        spines.append(sp)
        a, b = B.tube_outline(sp, radii, 4, 0.7, (0.0, lw))
        shapes.append(a)
        outs.append(b)
    pal = q.P(mat)
    cr.new_path()
    for o in outs:
        core.smooth_closed(cr, o, 0.9)
    core.src(cr, pal.line)
    cr.fill()
    for s_ in shapes:
        core.smooth_closed(cr, s_, 0.9)
    shp = Path(cr)
    q.shade(shp, mat, outline=False, size=size, rim=rim)
    if contour and abs(math.sin(q.yaw)) > 0.2:
        ni = 0 if q.near < 0 else 1
        sp, sf = spines[ni], spines[1 - ni]
        fx = sum(p[0] for p in sf) / 4.0
        nx_ = sum(p[0] for p in sp) / 4.0
        sg = 1.0 if fx > nx_ else -1.0
        pts = []
        for i, p in enumerate(sp):
            j0, j1 = max(0, i - 1), min(3, i + 1)
            tx, ty = core.normalize((sp[j1][0] - sp[j0][0], sp[j1][1] - sp[j0][1]))
            nxv, nyv = -ty, tx
            if nxv * sg < 0:
                nxv, nyv = -nxv, -nyv
            pts.append((p[0] + nxv * radii[i] * 0.98, p[1] + nyv * radii[i] * 0.98))
        B.detail_lines(cr, [pts], lw * 1.0, pal.line, 0.85, taper=(0.2, 1.0, 0.6))
    return shp, pal, spines


def smooth_shape(q, pts, mat, size, tension=0.8, **kw):
    shp, out = B.smooth_paths(q.cr, pts, q.lw, tension)
    pal = q.shade(shp, mat, outline=out, size=size, **kw)
    return shp, pal


def foot_groups(q, f, *, length=30.0, width=11.0, height=13.0, shaft=0.0, shaft_r=None, toe_up=0.0):
    """Convex point groups of a plantigrade foot/boot (+ a boot shaft `shaft` px up the shin)
    for hull_union. Feet point along +Z (forward). Returns (groups, P) where P(dx, dy, dz) maps
    foot-local offsets (from the ground point under the ankle, toe pitch applied) to 2D."""
    proj = q.proj
    a = f["ankle"]
    toe = f["toe"] + toe_up
    base = (a[0], a[1] + q.b.ankle_h, a[2])
    c, sn = math.cos(toe), math.sin(toe)

    def P(dx, dy, dz):
        return proj.xy((base[0] + dx, base[1] + dy * c - dz * sn, base[2] + dy * sn + dz * c))

    pts = []
    for k in range(8):
        ang = TAU * k / 8
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append(P(ca * width * 0.72, -q.b.ankle_h + 3 + sa * 2.0, sa * width * 0.6))       # ankle
        pts.append(P(ca * width * 0.62, -height * 0.5 + sa * height * 0.45, -length * 0.22))   # heel
        pts.append(P(ca * width, -height * 0.45 + sa * height * 0.42, length * 0.45))         # ball
        pts.append(P(ca * width * 0.8, -height * 0.35 + sa * height * 0.32, length * 0.72))   # toe
    groups = [pts]
    if shaft > 0:
        kn = f["knee"]
        top = v_lerp(a, kn, clamp(shaft / max(1.0, q.b.shin)))
        r = shaft_r or width * 0.95
        groups.append(blob_pts(proj, top, r, 4.0, r, 8) + blob_pts(proj, a, r * 0.85, 4.0, r * 0.85, 8))
    return groups, P


def foot(q, f, mat, *, size=22.0, **kw):
    """One plantigrade foot/boot as a shaded union (see foot_groups)."""
    groups, P = foot_groups(q, f, **kw)
    shape, pal = hull_union(q, groups, mat, size, rim=0.5)
    return shape, pal, P


def feet(q, mat, *, size=22.0, rim=0.5, **kw):
    """BOTH feet/boots as one union (one outline, one shading pass: half the cost of two)."""
    groups = []
    for f in q.S["feet"]:
        g, _P = foot_groups(q, f, **kw)
        groups += g
    return hull_union(q, groups, mat, size, rim=rim)


def leg_spine(q, f, upto="ankle"):
    proj = q.proj
    return [proj.xy(f["hip"]), proj.xy(f["knee"]), proj.xy(f[upto])]


def legs(q, radii, mat, size, contour=True, rim=0.5):
    """BOTH legs (hip -> knee -> ankle tubes) as one union, shaded once. Where the near leg
    crosses the far one an ink contour keeps them apart (3/4 views)."""
    cr, lw = q.cr, q.lw
    outs = []
    shapes = []
    for f in q.S["feet"]:
        a, b = B.tube_outline(leg_spine(q, f), radii, 4, 0.75, (0.0, lw))
        shapes.append(a)
        outs.append(b)
    pal = q.P(mat)
    cr.new_path()
    for o in outs:
        core.smooth_closed(cr, o, 0.9)
    core.src(cr, pal.line)
    cr.fill()
    for s_ in shapes:
        core.smooth_closed(cr, s_, 0.9)
    shp = Path(cr)
    q.shade(shp, mat, outline=False, size=size, rim=rim)
    if contour and abs(math.sin(q.yaw)) > 0.2:
        fn = q.S["feet"][0 if q.near < 0 else 1]
        ff = q.S["feet"][0 if q.near > 0 else 1]
        sp = leg_spine(q, fn)
        # offset the near leg's spine toward the far leg by its radius: its overlapping edge
        fx = sum(p[0] for p in leg_spine(q, ff)) / 3.0
        nx = sum(p[0] for p in sp) / 3.0
        sg = 1.0 if fx > nx else -1.0
        pts = []
        for i, p in enumerate(sp):
            j0, j1 = max(0, i - 1), min(2, i + 1)
            tx, ty = core.normalize((sp[j1][0] - sp[j0][0], sp[j1][1] - sp[j0][1]))
            r = radii[i] * 0.98
            nxv, nyv = -ty, tx
            if nxv * sg < 0:
                nxv, nyv = -nxv, -nyv
            pts.append((p[0] + nxv * r, p[1] + nyv * r))
        B.detail_lines(cr, [pts], lw * 1.0, pal.line, 0.85, taper=(0.2, 1.0, 0.6))
    return shp, pal


def hoof(q, f, mat, *, w=13.0, h=16.0, size=20.0, split=True):
    """A hoof at the ground point of a digitigrade or hoofed leg (cloven line when split)."""
    proj = q.proj
    g = f["ground"]
    toe = f["toe"]
    c, sn = math.cos(toe), math.sin(toe)

    def P(dx, dy, dz):
        return proj.xy((g[0] + dx, g[1] + dy * c - dz * sn, g[2] + dy * sn + dz * c))

    pts = []
    for k in range(10):
        ang = TAU * k / 10
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append(P(ca * w * 0.8, -h + 2.0, sa * w * 0.75 + 1.0))
        pts.append(P(ca * w, -1.0, sa * w * 0.9 + 4.0))
    pts.append(P(0.0, -1.0, w * 1.25 + 4.0))
    shape, pal = hull_union(q, [pts], mat, size, rim=0.6)
    if split and q.detail >= 1:
        a, b_ = P(0.0, -h * 0.55, w * 0.8 + 4.0), P(0.0, -1.0, w * 1.2 + 4.0)
        if proj.depth((0.0, 0.0, 1.0)) > 0.2:
            B.detail_lines(q.cr, [[a, b_]], q.lw * 0.9, pal.line, 0.8)
    return shape, pal


def hand(q, A, mat, *, size=None, claw=None, pad=None, finger_w=1.0, palm_w=1.0, finger_len=1.0, hold=True,
         stamp=None, behind=False):
    """base.hand at the end of a solved arm (A from solve_arm): wrist, forearm direction + hang,
    thumb side from the gesture, z-correct hold callback."""
    proj = q.proj
    el, wr = proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    side = A["side"]
    hang = ang + A["hang"] * (1 if side < 0 else -1) * (1 if math.sin(q.yaw) >= 0 else -1)
    arm = A["arm"]
    hp = A["hand"]
    flip = hand_flip(q, A, hang)
    show_palm = hp in ("open", "offer") and arm.gesture in ("hand_out_offer", "offer", "stagger", "wave", "talk")
    if q.detail == 0:
        return mitten(q, wr[0] + fdx * 3.0, wr[1] + fdy * 3.0, hang, size or q.b.hand_len, hp, mat, flip=flip,
                      hold=arm.hold if hold else None, claw=claw)
    return B.hand(q.cr, wr[0] + fdx * 3.0, wr[1] + fdy * 3.0, hang, size or q.b.hand_len, hp, mat, q.light, q.lw,
                  flip=flip, claw=claw, claw_len=0.06, pad=pad, show_palm=show_palm,
                  hold=arm.hold if hold else None, stamp=stamp or arm.stamp, finger_w=finger_w, palm_w=palm_w,
                  finger_len=finger_len, detail=q.detail, hold_behind=behind)


def mitten(q, x, y, angle, size, pose, mat, *, flip=False, hold=None, claw=None):
    """The detail-0 hand (small on screen): palm + finger block + thumb as ONE flat-lit union
    with its outline (2 fills instead of ~5-10), the held prop drawn under the fingers in the
    same frame base.hand gives a hold callback. Returns a base.HandFrame."""
    cr = q.cr
    pal = q.P(mat if isinstance(mat, B.Mat) else B.Mat.of(mat))
    s = size
    fy = -1.0 if flip else 1.0
    curl = sum(B.HAND_POSES[pose]["curl"]) / 3.0 if isinstance(pose, str) and pose in B.HAND_POSES else 0.3
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(s, s * fy)
    lwu = q.lw / s
    kx = 0.42
    if hold is not None:
        cr.save()
        cr.translate(kx + 0.08, 0.06)
        cr.scale(1.0 / s, 1.0 / s * fy)
        hold(cr, B.HandFrame(0.0, 0.0, angle, s, [], (0.0, 0.0), flip))
        cr.restore()
    # three short fingers (they fold toward the palm as they curl) + a thumb, one union
    fingers = []
    for i, u in enumerate((-1.0, 0.0, 1.0)):
        L = 0.50 * (0.95, 1.0, 0.86)[i]
        a0 = u * 0.10 + curl * 1.1
        b0 = (kx - 0.03, u * 0.095)
        tip_ = (b0[0] + math.cos(a0) * L, b0[1] + math.sin(a0) * L)
        fingers.append((b0, tip_))
    fx_, fr = fingers[1][1][0] - 0.2, 0.2

    def shape(d):
        core.ellipse(cr, 0.22, 0.0, 0.25 + d, 0.155 + d)
        for (b0, tp) in fingers:
            core.capsule(cr, b0[0], b0[1], 0.062 + d, tp[0], tp[1], 0.05 + d)
        core.capsule(cr, 0.12, -0.10, 0.072 + d, 0.33 - 0.08 * curl, -0.21 + 0.06 * curl, 0.058 + d)

    cr.new_path()
    shape(lwu)
    core.src(cr, pal.line)
    cr.fill()
    shape(0.0)
    core.src(cr, pal.lit)
    cr.fill()
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def tocaller(px, py):
        dx, dy = m.transform_point(px, py)
        return inv.transform_point(dx, dy)

    tip = tocaller(fx_ + fr, 0.02)
    return B.HandFrame(*tocaller(kx + 0.08, 0.06), angle, s, [tip, tip, tip], tocaller(0.21, 0.0), flip)


def arm_tube(q, A, mat, radii, size, *, cut=1.0, rim=0.5):
    """Upper arm + forearm as one tube (cut < 1 stops it part-way down the forearm: a sleeve).
    Returns (shape Path, Palette, (sh, el, end) 2D)."""
    proj = q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    end = core.lerp_pt(el, wr, cut)
    r2 = lerp(radii[1], radii[2], cut)
    shp, pal = limb(q, [sh, el, end], [radii[0], radii[1], r2], mat, size, rim=rim)
    return shp, pal, (sh, el, end)


def band(q, limb_path, p0, p1, half_w, mat, size=30.0, seams=True):
    """Paint a band of material `mat` round an already shaded limb between the 2D points p0 and
    p1 (a bracer, a cuff, a boot strap): clipped to the limb so it follows its silhouette, two
    tones (shadow, then the limb shifted toward the key in the lit tone), seam ink at both
    ends. Cheaper than a separately outlined part (no outline pass, no rim pass)."""
    cr = q.cr
    pal = q.P(mat)
    ux, uy = core.normalize((p1[0] - p0[0], p1[1] - p0[1]))
    nx, ny = -uy, ux
    w = half_w * 1.6
    cr.save()
    limb_path.add(cr)
    cr.clip()
    core.polygon(cr, [(p0[0] + nx * w, p0[1] + ny * w), (p1[0] + nx * w, p1[1] + ny * w),
                      (p1[0] - nx * w, p1[1] - ny * w), (p0[0] - nx * w, p0[1] - ny * w)])
    cr.clip()
    core.src(cr, pal.shadow)
    cr.paint()
    kx, ky = B.local_dir(cr, q.light.direction)
    d = 0.2 * size * q.light.shadow_size
    limb_path.add(cr, kx * d, ky * d)
    core.src(cr, pal.lit)
    cr.fill()
    cr.restore()
    if seams:
        r = half_w * 0.98
        lines = [[(p[0] - nx * r, p[1] - ny * r), (p[0] + ux * 2.5, p[1] + uy * 2.5), (p[0] + nx * r, p[1] + ny * r)]
                 for p in (p0, p1)]
        B.detail_lines(cr, lines, q.lw * 1.0, pal.line, 0.9, taper=(0.6, 1.0, 0.6))
    return pal


def elbow_folds(q, sh, el, wr, r, pal, alpha=0.5):
    """Two short ink folds on the inside of the elbow bend (cloth sleeves)."""
    if q.detail < 2:
        return
    ux, uy = core.normalize((wr[0] - sh[0], wr[1] - sh[1]))
    nx, ny = -uy, ux
    bend = (el[0] - sh[0]) * (wr[1] - el[1]) - (el[1] - sh[1]) * (wr[0] - el[0])
    sg = 1.0 if bend > 0 else -1.0
    lines = []
    for off in (0.15, 0.55):
        lines.append([(el[0] + nx * r * off * sg - ux * 6, el[1] + ny * r * off * sg - uy * 6),
                      (el[0] + nx * r * (off + 0.55) * sg + ux * 3, el[1] + ny * r * (off + 0.55) * sg + uy * 3)])
    B.detail_lines(q.cr, lines, q.lw * 0.8, pal.line, alpha)


def contact(q, rx=None, alpha=0.32):
    """Contact shadow under the feet (and under the seat when sitting)."""
    S = q.S
    proj = q.proj
    g = [proj.xy((f["ground"][0], 0.0, f["ground"][2])) for f in S["feet"]]
    cx = (g[0][0] + g[1][0]) / 2
    w = rx or (q.b.hip_w * 2.2 + 30.0)
    w = w * (0.8 + 0.25 * abs(math.cos(q.yaw))) + abs(g[0][0] - g[1][0]) * 0.5
    lifted = max(0.0, -max(f["ground"][1] for f in S["feet"]))
    B.contact_shadow(q.cr, cx, 2.0, w, w * 0.2, alpha=alpha * (1.0 - clamp(lifted / 120.0) * 0.6))


# ----------------------------------------------------------------------------------------
# heads
# ----------------------------------------------------------------------------------------

def head_xf(q, HS=1.0, center=None, R=None):
    """Head-space transforms for the head drawn at the skeleton's head centre:
    P(v) -> 2D point, nz(dir) -> how much a head-space direction faces the camera (-1..1),
    D(v) -> depth of a head-space point (bigger = nearer)."""
    RH = q.S["RH"] if R is None else R
    HC = q.S["head_c"] if center is None else center
    proj = q.proj

    def W(v):
        w = m_vec(RH, (v[0] * HS, v[1] * HS, v[2] * HS))
        return (HC[0] + w[0], HC[1] + w[1], HC[2] + w[2])

    def P(v):
        return proj.xy(W(v))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    def D(v):
        return proj.depth(W(v))

    return P, nz, D, W


def eye_at(q, P, nz, s, e, pos, rx, ry, *, iris, iris_hi=None, skin, pupil="#1d120c", pupil_aspect=1.0,
           pupil_size=0.5, crease=0.3, bags=0.0, lash=1.0, lash_flick=0.0, line=None, lid_add=0.0, look=None,
           blink=None, normal=None, squint=None, lid_shade=0.14, iris_size=0.66, highlight=1.0):
    """One base.eye placed in head space (pos = (x, y, z) of the eye centre for side s):
    foreshortened by how much it faces the camera, axis tilted toward its outer corner, culled
    when it turns away. Returns the 2D centre (or None when culled)."""
    ec = P(pos)
    nrm = normal or (s * 0.42, -0.12, 0.9)
    fz = nz(nrm)
    if fz < 0.06:
        return None
    fore = clamp(0.28 + fz * 0.8, 0.3, 1.0)
    op = P((pos[0] + s * 12.0, pos[1], pos[2] - 6.0))
    outer = 1.0 if op[0] > ec[0] else -1.0
    ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)
    lk = q.pose.look if look is None else look
    bl = blink if blink is not None else (B.auto_blink(q.t, q.pose.seed * 7 + 2) if q.pose.blink is None else q.pose.blink)
    if q.detail == 0:
        eye_lite(q.cr, ec[0], ec[1], rx * fore, ry, q.light, q.lw, angle=ang * 0.6, look=(lk[0] * outer, lk[1]),
                 lid=clamp(e.lid + lid_add), lid_bot=e.lid_bot, tilt=e.lid_tilt, outer=outer, blink=bl,
                 squint_arc=clamp((q.pose.laugh - 0.5) * 2.0) if squint is None else squint, iris=iris, pupil=pupil,
                 pupil_size=pupil_size * e.pupil, pupil_aspect=pupil_aspect, skin=skin, iris_size=iris_size, line=line)
        return ec
    B.eye(q.cr, ec[0], ec[1], rx * fore, ry, q.light, q.lw, angle=ang * 0.6, look=(lk[0] * outer, lk[1]),
          lid=clamp(e.lid + lid_add), lid_bot=e.lid_bot, tilt=e.lid_tilt, outer=outer, blink=bl,
          squint_arc=clamp((q.pose.laugh - 0.5) * 2.0) if squint is None else squint, iris=iris, iris_hi=iris_hi,
          pupil=pupil, pupil_size=pupil_size * e.pupil, pupil_aspect=pupil_aspect, skin=skin, crease=crease,
          bags=bags if q.detail >= 1 else 0.0, lash=lash, lash_flick=lash_flick, line=line, lid_shade=lid_shade,
          iris_size=iris_size, highlight=highlight)
    return ec


def eye_lite(cr, cx, cy, rx, ry, light, lw, *, angle=0.0, look=(0.0, 0.0), lid=0.22, lid_bot=0.06, tilt=0.0,
             outer=1.0, blink=0.0, squint_arc=0.0, iris="#D99A2B", pupil="#1d120c", pupil_size=0.5,
             pupil_aspect=1.0, skin="#888888", iris_size=0.66, line=None):
    """base.eye's look in ~6 flat fills (no gradients, no lid skin pass, no crease): for faces
    small on screen (detail 0). Same parameters and the same lid / iris / catchlight placement."""
    sk = B.palette(light, Mat.of(skin, sss=0.2))
    line_c = line if line is not None else sk.line
    lid = clamp(lid + 0.28 * max(0.0, look[1]) - 0.10 * max(0.0, -look[1]))
    closed = clamp(max(lid, blink))
    cr.save()
    cr.translate(cx, cy)
    if angle:
        cr.rotate(angle)
    cr.scale(outer, 1.0)
    n = 7
    xs = [-rx + 2 * rx * i / (n - 1) for i in range(n)]

    def y_top(x):
        u = x / rx
        k = math.sqrt(max(0.0, 1.0 - u * u))
        return max(-ry * k, -ry + 2.0 * ry * closed - 0.38 * ry * (1.0 - u * u) * (1.0 - closed * 0.85)
                   + tilt * 0.42 * ry * u * (1.0 - closed * 0.4))

    def y_bot(x):
        u = x / rx
        k = math.sqrt(max(0.0, 1.0 - u * u))
        return min(ry * k, ry - 2.0 * ry * lid_bot + 0.32 * ry * (1.0 - u * u) * (1.0 - lid_bot))

    top = [(x, y_top(x)) for x in xs]
    bot = [(x, y_bot(x)) for x in xs]
    if closed < 0.97 and any(b_[1] - a_[1] > 0.6 for a_, b_ in zip(top, bot)):
        cr.new_path()
        core.polygon(cr, top + bot[::-1])
        cr.save()
        cr.clip_preserve()
        core.src(cr, "#ECE6DA")
        cr.fill()
        ir = ry * iris_size
        ix = clamp(look[0] * rx * 0.42 * outer, -rx + ir * 0.6, rx - ir * 0.6)
        iy = look[1] * ry * 0.38 + ry * 0.06
        core.src(cr, iris)
        core.circle(cr, ix, iy, ir)
        cr.fill()
        core.src(cr, pupil)
        pr = ir * pupil_size
        core.ellipse(cr, ix, iy, pr * pupil_aspect, pr)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.9)
        core.circle(cr, ix + ir * (0.32 - 0.07 * outer), iy - ir * 0.42, ir * 0.28)
        cr.fill()
        cr.restore()
        cr.new_path()
        wt = lw * 1.6
        core.tapered(cr, top, wt * 0.5, wt * 0.8, profile=lambda u: wt * (0.4 + 0.6 * math.sin(math.pi * min(1.0, 0.15 + u))))
        core.src(cr, line_c)
        cr.fill()
    else:
        if squint_arc >= 0.5:
            pts = [(x, -ry * 0.35 * (1.0 - (x / rx) ** 2) + ry * 0.15) for x in xs]
        else:
            pts = [(x, ry * 0.28 * (1.0 - (x / rx) ** 2) - ry * 0.02) for x in xs]
        B.detail_line(cr, pts, lw * 1.5, line_c, 1.0, taper=(0.3, 1.0, 0.5))
    cr.restore()


def brow_pts(P, s, e, near, x0, x1, y, z0, z1, k_in=13.0, k_out=11.0):
    """Brow centre-line (inner -> outer) for side s driven by the Expr (pushed hard, STYLE §8)."""
    asym = e.brow_asym * (1.0 if s == near else -0.4)
    li = (e.brow_in * 0.75 + e.brow_y + asym) * k_in
    lo = (e.brow_out * 0.6 + e.brow_y + asym) * k_out
    return [P((s * x0, y - li, z0)), P((s * (x0 + x1) * 0.5, y - 3.0 - (li + lo) * 0.5, (z0 + z1) * 0.5)),
            P((s * x1, y + 1.0 - lo, z1))]


def mouth_at(q, P, nz, pos, w, e, talk, *, skin, normal=(0.0, 0.25, 1.0), lip=None, inside="#5A1E24",
             tongue="#C4566A", teeth="#F4EEE2", upper_teeth=True, line=None, side_shift=0.0):
    """base.mouth placed in head space, squeezed by the head's turn. Returns the 2D centre."""
    c = P(pos)
    fz = nz(normal)
    if fz < -0.05:
        return c
    cr = q.cr
    side_dir = P((pos[0] + 10.0, pos[1], pos[2]))
    ang = math.atan2(side_dir[1] - c[1], side_dir[0] - c[0])
    if side_dir[0] < c[0]:
        ang += math.pi
    fore = clamp(0.35 + 0.65 * fz, 0.3, 1.0)
    cr.save()
    cr.translate(c[0] + side_shift, c[1])
    cr.rotate(ang * 0.7)
    cr.scale(fore, 1.0)
    B.mouth(cr, 0.0, 0.0, w, q.light, q.lw / max(fore, 0.5), e=e, talk=talk, skin=skin, lip=lip, inside=inside,
            tongue=tongue, teeth=teeth, upper_teeth=upper_teeth, line=line)
    cr.restore()
    return c


# ========================================================================================
# character-sheet helpers (python3 film/render.py --sheet)
# ========================================================================================

SHEET_BG = {
    "neutral": ("#6f7a86", "#4b545e"), "washhouse": ("#1d3a3d", "#0e1f22"),
    "apothecary": ("#d9e6e0", "#a9bdb6"), "street_night": ("#1b2340", "#0b1022"),
    "tavern": ("#5a2440", "#2a1020"), "square": ("#4a5668", "#2c3442"),
    "dusk": ("#a98aa6", "#e0a98a"), "golden": ("#e6b070", "#a8704a"),
    "blue_hour": ("#3a4a78", "#1e2848"), "lantern_night": ("#141c34", "#070a16"),
}
SHEET_LIGHTS = ("washhouse", "apothecary", "street_night", "tavern", "square", "dusk", "golden", "lantern_night")


def sheet_bg(cr, w, h, light="neutral", floor=None):
    top, bot = SHEET_BG.get(light, SHEET_BG["neutral"])
    core.vgrad(cr, 0, 0, w, h, [top, bot])
    if floor is not None:
        cr.set_source_rgba(0, 0, 0, 0.12)
        cr.rectangle(0, floor, w, h - floor)
        cr.fill()


def sheet_bench(cr, x, ground, sc, seat_h=B.BENCH_SEAT_H, w=200.0, back=True, light=None):
    """Placeholder garden bench (oak planks on wrought iron) with its seat at seat_h * sc above
    `ground` (the props kit draws the real one)."""
    L = light or B.LIGHTS["neutral"]
    oak = B.pal(L, "#8a6240")
    iron = B.pal(L, "#2e3236")
    sy = ground - seat_h * sc
    core.src(cr, iron.lit)
    for dx in (-w / 2 + 14 * sc, w / 2 - 22 * sc):
        cr.rectangle(x + dx, sy, 8 * sc, seat_h * sc)
    if back:
        for dx in (-w / 2 + 16 * sc, w / 2 - 20 * sc):
            cr.rectangle(x + dx, sy - 70 * sc, 5 * sc, 70 * sc)
    cr.fill()
    if back:
        core.src(cr, core.mix(oak.lit, oak.shadow, 0.35))
        cr.rectangle(x - w / 2, sy - 64 * sc, w, 9 * sc)
        cr.rectangle(x - w / 2, sy - 44 * sc, w, 9 * sc)
        cr.fill()
    core.src(cr, oak.shadow)
    cr.rectangle(x - w / 2, sy, w, 10 * sc)
    cr.fill()
    core.src(cr, oak.lit)
    cr.rectangle(x - w / 2, sy - 3 * sc, w, 7 * sc)
    cr.fill()


def bench_ms(fn, reps=6, n=8):
    """min CPU ms per call of fn() over several runs (the machine is shared)."""
    import time
    best = 1e9
    for _ in range(reps):
        t0 = time.process_time()
        for _ in range(n):
            fn()
        best = min(best, (time.process_time() - t0) / n)
    return best * 1000.0
