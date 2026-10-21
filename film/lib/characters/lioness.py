"""lioness.py -- THE LIONESS, the kind apothecary (speaker PHARMACIST, S2).

Tidy, kind and graceful: tawny fur with a pale muzzle and dark tear-lines, round ears, a long
tail with a dark tuft; a deep apothecary-green robe under a cream linen bib-apron, a cream
collar with a little rose ribbon (her one warm accent), rolled cuffs, and gold half-moon
spectacles on a beaded chain -- she looks OVER them, and reads THROUGH them.

    p = ch.LionessPose(facing=-1, talk=timeline.talk(2, t, "PHARMACIST"), mood="kind",
                       near=ch.LionessArm("place", phase=u, hold=props_jar))
    rig = ch.draw_lioness(cr, x, ground_y, 0.95, p, ch.LIGHTS["apothecary"], t)

Scale 1.0: ground -> ear tips = LIONESS_HEIGHT = 450 px (crown ~442, eyes ~400). Anchor (x, y) =
the ground point between her feet. The counter in S2 is built to LIONESS_COUNTER_H = 200 px
(her hands rest on it with "on_counter", items are set down on it with "place").
3D-lite like the dragon: body space X = her left, Y down, Z forward, turned by the yaw.
"""

import math
from dataclasses import dataclass, field, replace

from .. import core
from ..core import clamp, lerp, smooth
from . import _cast_kit as K
from . import base as B
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp

TAU = math.tau

__all__ = ["LionessPose", "LionessArm", "LionessRig", "draw_lioness", "lioness_walk_phase", "lioness_stride",
           "LIONESS_HEIGHT", "LIONESS_COUNTER_H", "LIONESS_COLORS", "LIONESS_GESTURES", "lioness_mats"]

LIONESS_HEIGHT = 450.0
LIONESS_COUNTER_H = 200.0
LINE = B.LINE

PELVIS_Y = -205.0
HIP_W = 17.0
THIGH, SHIN, ANKLE_H = 98.0, 92.0, 15.0
UPPER_ARM, FOREARM, HAND_LEN = 74.0, 68.0, 44.0
SHOULDER_W = 44.0
HS = 1.3                   # head scale: head-space units -> body px (a big, appealing head)
STRIDE = 170.0
# the rig is authored a little small: this brings the measured top (ear tips) to LIONESS_HEIGHT
SIZE_K = 450.0 / 432.0
ELEV = 0.12
HEAD_CHEAT = 0.22

LIONESS_COLORS = {
    "fur": "#C9944F",        # tawny gold
    "fur_dk": "#A8743A",     # brows, the back of the tail
    "pale": "#F2E1C2",       # muzzle, chin, the fur over the eyes
    "nose": "#B9705B",
    "mark": "#5B3826",       # tear-lines, ear backs, the tail tuft
    "ear_in": "#E9C6A2",
    "robe": "#3F6E66",       # deep apothecary green
    "apron": "#EEE5D0",      # cream linen
    "collar": "#F4EDDF",
    "ribbon": "#C8576A",     # her one warm accent
    "specs": "#D2A84A",      # gold
    "eye": "#9AA43E",        # olive-gold
    "eye_hi": "#E3E59A",
    "mouth": "#5E2A2C",
    "tongue": "#C9606A",
    "pad": "#8E5A4C",
}

_MATS = {}


def lioness_mats():
    if not _MATS:
        C = LIONESS_COLORS
        _MATS.update({
            "fur": Mat.of(C["fur"], sss=0.25),
            "fur_dk": Mat.of(C["fur_dk"], sss=0.2),
            "pale": Mat.of(C["pale"], sss=0.3, line_k=0.5),
            "nose": Mat.of(C["nose"], sss=0.4, sheen=0.4),
            "mark": Mat.of(C["mark"]),
            "ear_in": Mat.of(C["ear_in"], sss=0.5),
            "robe": Mat.of(C["robe"], shadow_k=1.1),
            "apron": Mat.of(C["apron"], shadow_k=0.95),
            "collar": Mat.of(C["collar"], shadow_k=0.95),
            "ribbon": Mat.of(C["ribbon"]),
            "specs": Mat.of(C["specs"], sheen=0.8),
        })
    return _MATS


@dataclass
class LionessArm:
    """gesture (LIONESS_GESTURES), amt/prev blend, hold callback (z-correct), target (body
    space) or screen (caller coordinates) wrist target, hand pose override, phase 0..1."""
    gesture: str = "rest"
    amt: float = 1.0
    prev: str = "rest"
    hold: object = None
    target: tuple = None
    screen: tuple = None
    depth: float = 30.0
    hand: str = None
    phase: float = 0.0


@dataclass
class LionessPose:
    """facing/turn (yaw clamped to +-1.45), walk/phase (lioness_walk_phase), lean, head_turn/
    tilt/nod (nod -1 down .. +1 up), look, mood (default "kind"), mood2/mood_mix, talk, smile,
    blink, near/far LionessArm, counter_h (the counter top for on_counter/place),
    specs: 0 low on the muzzle (she looks over them) .. 1 pushed up (reading through them),
    whisker: twitch 0..1 (the S2 frozen-smile pause), freeze 0..1 (idle motion stops: the held
    beat), tail_swing -1..1, anchor ("ground"), elev, shadow, seed."""
    facing: int = -1
    turn: float = 0.0
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
    blink: float = None
    near: LionessArm = field(default_factory=LionessArm)
    far: LionessArm = field(default_factory=LionessArm)
    counter_h: float = LIONESS_COUNTER_H
    specs: float = 0.0
    whisker: float = 0.0
    freeze: float = 0.0
    tail_swing: float = 0.0
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class LionessRig:
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)
    nose: tuple = (0.0, 0.0)
    eyes: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    note: tuple = None            # read_note: where the two-handed note sits
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0


def lioness_stride(scale=1.0, facing=1, turn=0.0):
    return STRIDE * abs(math.sin(K.yaw_of(facing, turn))) * scale * SIZE_K


def lioness_walk_phase(distance_px, scale=1.0, facing=1, turn=0.0):
    st = lioness_stride(scale, facing, turn)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


# ----------------------------------------------------------------------------------------
# gestures -> (wrist target in body space, hand pose, extra hand angle, layer)
# ----------------------------------------------------------------------------------------

def _g_rest(sk, side, c):
    # hands loosely clasped in front of the apron
    return v_add(c["waist"], (side * 13.0, 22.0, 36.0)), "relaxed", 0.5, "front"


def _g_on_counter(sk, side, c):
    # both paws resting on the counter top in front of her
    return (side * 30.0 + c["fwd"][0] * 10.0, -c["counter"] - 4.0, 58.0), "flat", 0.0, "front"


def _g_reach_up(sk, side, c):
    # up to a high shelf (use screen= for the exact jar)
    f = c["fwd"]
    return v_add(sk, (side * 12.0 + f[0] * 40.0, -140.0, f[2] * 40.0)), "grip", 0.0, "front"


def _g_place(sk, side, c):
    # carry at the chest -> set it down on the counter (0.55) -> let go and draw back
    ph = c["phase"]
    f = c["fwd"]
    carry = v_add(c["chest"], (side * 12.0 + f[0] * 26.0, 30.0, 30.0 + f[2] * 20.0))
    down = (side * 6.0 + f[0] * 70.0, -c["counter"] - 22.0, 40.0 + f[2] * 50.0)
    if ph < 0.55:
        return v_lerp(carry, down, core.inout_sine(ph / 0.55)), "grip", 0.0, "front"
    back = v_add(down, (-f[0] * 14.0, -18.0, -10.0))
    return v_lerp(down, back, core.inout_sine((ph - 0.55) / 0.45)), "open" if ph > 0.62 else "grip", 0.0, "front"


def _g_hold_note(sk, side, c):
    return v_add(c["chest"], (side * 6.0 + c["fwd"][0] * 20.0, -10.0, 46.0)), "pinch", 0.0, "front"


def _g_read_note(sk, side, c):
    # two hands hold the note up in front of her chest (two-hand prop, like the dragon's book)
    return v_add(c["chest"], (side * 40.0 + c["fwd"][0] * 18.0, 4.0, 44.0)), "pinch", 0.0, "front"


def _g_present(sk, side, c):
    # "Try these": an open palm toward the pile in front of her
    f = c["fwd"]
    return v_add(sk, (side * 26.0 + f[0] * 42.0, 70.0, 30.0 + f[2] * 30.0)), "offer", 0.0, "front"


def _g_ring(sk, side, c):
    # ringing the till: hand lifts, presses the key down (0.45), a little bounce back
    ph = c["phase"]
    f = c["fwd"]
    key = (side * 10.0 + f[0] * 56.0, -c["counter"] - 16.0, 50.0 + f[2] * 30.0)
    if ph < 0.35:
        y = -24.0 * core.out_quad(ph / 0.35)
    elif ph < 0.45:
        y = lerp(-24.0, 0.0, core.in_quad((ph - 0.35) / 0.1))
    else:
        y = -10.0 * B.wobble(ph * 2.0, 0.9, 3.0, 5.0) * 0.4 - 4.0 * smooth((ph - 0.45) / 0.55)
    return v_add(key, (0.0, y, 0.0)), "point" if ph < 0.5 else "relaxed", 0.0, "front"


def _g_point(sk, side, c):
    f = c["fwd"]
    return v_add(sk, (side * 14.0 + f[0] * 70.0, 40.0, 20.0 + f[2] * 60.0)), "point", 0.0, "front"


LIONESS_GESTURES = {
    "rest": _g_rest, "on_counter": _g_on_counter, "reach_up": _g_reach_up, "place": _g_place,
    "hold_note": _g_hold_note, "read_note": _g_read_note, "present": _g_present, "ring_till": _g_ring,
    "point": _g_point,
}


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_lioness(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    """Draw the lioness apothecary, feet at (x, y). Returns a LionessRig (caller coordinates)."""
    pose = pose or LionessPose()
    light = light or B.LIGHTS["neutral"]
    q = K.Q(cr, light, lioness_mats(), t, pose)
    yaw = K.yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    scale_px = scale
    scale = scale * SIZE_K            # internal units: lines stay LINE px on screen
    dev = q.lod(scale, detail)
    q.lw = max(LINE / SIZE_K, B.MIN_LINE_PX / max(dev, 1e-6))
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    S = _skeleton(pose, t, yaw)
    q.S = S
    rig = LionessRig(scale=scale_px, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)
    if pose.shadow:
        fa = [proj.xy(f["ankle"]) for f in S["feet"]]
        B.contact_shadow(cr, (fa[0][0] + fa[1][0]) / 2.0, 2.0, 62.0, 13.0, alpha=0.32)

    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    arms = {near_side: pose.near, far_side: pose.far}
    A = {s: _solve_arm(q, S, s, arms[s]) for s in (near_side, far_side)}
    frontish = abs(yaw) < 0.38
    zf = A[far_side]["z"]
    far_layer = ("mid" if frontish else "back") if zf == "auto" else (("front" if frontish else "mid") if zf == "front" else zf)
    near_layer = "mid" if A[near_side]["z"] == "mid" else "front"
    two = pose.near.gesture == "read_note" and pose.far.gesture == "read_note" and (pose.near.hold or pose.far.hold)

    _tail(q)
    if far_layer == "back":
        rig.hand_far = _arm(q, A[far_side], far_side)
    _feet(q)
    _robe(q)
    _apron(q)
    if far_layer == "mid" and not two:
        rig.hand_far = _arm(q, A[far_side], far_side)
    _collar_neck(q)
    head = _head(q)
    if two:
        rig.hand_far, rig.hand_near, rig.note = _two_hand(q, A[far_side], A[near_side], pose.near.hold or pose.far.hold)
    else:
        if far_layer == "front":
            rig.hand_far = _arm(q, A[far_side], far_side)
        if near_layer in ("front", "mid"):
            rig.hand_near = _arm(q, A[near_side], near_side)

    ex = K.Exporter(cr)
    cr.restore()
    ex.ready(cr)
    rig.head, rig.mouth, rig.nose = ex(head["center"]), ex(head["mouth"]), ex(head["nose"])
    rig.eyes = [ex(e) for e in head["eyes"]]
    rig.top = ex(head["top"])
    rig.chest = ex(proj.xy(S["chest"]))
    rig.feet = [ex(proj.xy(f["ankle"])) for f in S["feet"]]
    if rig.note is not None:
        rig.note = ex(rig.note)
    ex.hand(rig.hand_near, scale)
    ex.hand(rig.hand_far, scale)
    return rig


def _skeleton(pose, t, yaw):
    S = {}
    frz = 1.0 - clamp(pose.freeze)
    br = B.breathing(t, 0.22, pose.seed) * frz
    walk = clamp(pose.walk)
    wc = B.walk_cycle(pose.phase, stride=STRIDE, lift=20.0, bob=4.0, swing=1.0)
    S.update(br=br, walk=walk, wc=wc, frz=frz)
    pel = (walk * wc.hip_sway * 3.0, PELVIS_Y + walk * wc.hip_dy, 0.0)
    S["pelvis"] = pel
    idle = B.sway(t, 0.2, pose.seed + 3) * frz
    tilt = 0.25 * pose.lean + 0.04 * walk + 0.012 * idle
    roll = walk * wc.hip_sway * 0.03 + 0.012 * B.sway(t, 0.15, pose.seed + 7) * frz
    R = m_mul(m_rot_z(roll), m_rot_x(-tilt))
    S["R"], S["tilt"] = R, tilt

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["waist"] = T((0.0, -42.0, 2.0))
    S["chest"] = T((0.0, -80.0, 6.0 + 1.0 * br))
    sh_y = -112.0 - 1.4 * br
    S["sh_y"] = sh_y
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y + 6.0, -2.0)) for s in (-1.0, 1.0)}
    S["neck"] = T((0.0, sh_y - 6.0, 2.0))
    talk = clamp(pose.talk)
    nod = (pose.head_nod * 0.4 + 0.025 * talk * math.sin(t * 6.1) + 0.012 * br
           + 0.02 * B.sway(t, 0.25, pose.seed + 2) * frz - 0.4 * tilt)
    hy = clamp(pose.head_turn, -1.2, 1.2) * 0.95
    hr = pose.head_tilt + 0.025 * B.sway(t, 0.18, pose.seed + 5) * frz
    RH = m_mul(m_rot_y(hy - HEAD_CHEAT * yaw), m_mul(m_rot_x(nod), m_rot_z(hr)))
    S["RH"], S["head_yaw"] = RH, hy - HEAD_CHEAT * yaw
    pivot = v_add(S["neck"], m_vec(R, (0.0, -16.0, 8.0)))
    S["pivot"] = pivot
    S["head_c"] = v_add(pivot, v_add(m_vec(RH, (0.0, -34.0 * HS, 4.0)), (0.0, walk * wc.head_bob * 0.8, 0.0)))
    feet = []
    for s in (-1.0, 1.0):
        hip = v_add(pel, (s * HIP_W, 6.0, 0.0))
        fz, lift, toe, _p = wc.feet[0 if s < 0 else 1]
        ank = (s * (HIP_W - 2.0), -ANKLE_H - lift * walk, fz * walk + 3.0)
        knee, ank = B.ik3(hip, ank, THIGH, SHIN, (s * 0.1, 0.1, 1.0))
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "toe": toe * walk, "side": s})
    S["feet"] = feet
    S["ctx"] = {"waist": S["waist"], "chest": S["chest"], "counter": pose.counter_h / SIZE_K, "fwd": K.facing_dir(yaw), "phase": 0.0}
    return S


def _solve_arm(q, S, side, arm):
    sk = S["shoulders"][side]
    c = dict(S["ctx"], phase=arm.phase)
    tgt, hp, hang, z = LIONESS_GESTURES.get(arm.gesture, _g_rest)(sk, side, c)
    if arm.amt < 1.0:
        t0, hp0, ha0, z0 = LIONESS_GESTURES.get(arm.prev, _g_rest)(sk, side, dict(c, phase=0.0))
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 16.0
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
    if arm.gesture == "rest":
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"]
        tgt = v_add(tgt, (side * 6.0 * abs(sw), -abs(sw) * 10.0, sw * 40.0))
        if S["walk"] > 0.3:     # walking: the arms swing at her sides instead of staying clasped
            hang_down = v_add(sk, (side * 10.0, 150.0, 14.0 + sw * 44.0))
            tgt = v_lerp(tgt, hang_down, smooth((S["walk"] - 0.3) / 0.5))
    pole = (side * 1.0, 0.7, -0.3) if arm.gesture not in ("reach_up",) else (side * 1.0, 0.3, -0.6)
    elbow, wrist = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    return {"sh": sk, "el": elbow, "wr": wrist, "hand": hp, "z": z, "arm": arm, "hang": hang, "side": side}


def _arm(q, A, side, parts="all", hold=True):
    """Robe sleeve (one capsule union), the blouse's rolled cream cuff, and the paw."""
    cr, proj, M = q.cr, q.proj, q.M
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = math.atan2(fdy, fdx)
    if parts in ("all", "sleeve"):
        s_, o_ = K.caps(cr, [sh, el, wr], [18.0, 15.0, 13.0], q.lw)
        pal = q.shade(s_, M["robe"], outline=o_, size=40, rim=0.7)
        if q.detail >= 2:
            nx, ny = -fdy, fdx
            bend = (el[0] - sh[0]) * (wr[1] - el[1]) - (el[1] - sh[1]) * (wr[0] - el[0])
            sg = 1.0 if bend > 0 else -1.0
            B.detail_lines(cr, [[(el[0] + nx * 6 * sg - fdx * 8, el[1] + ny * 6 * sg - fdy * 8),
                                 (el[0] + nx * 15 * sg + fdx * 4, el[1] + ny * 15 * sg + fdy * 4)]], q.lw * 0.8, pal.line, 0.5)
        cs, co = B.ellipse_paths(cr, wr[0] - fdx * 4.0, wr[1] - fdy * 4.0, 8.5, 15.5, q.lw, ang)
        K.flat(q, cs, co, M["collar"])
    if parts == "sleeve":
        return B.HandFrame(wr[0], wr[1], ang, 1.0, [], wr, False)
    arm = A["arm"]
    hp = A["hand"]
    hang = ang + A["hang"] * (1 if side < 0 else -1) * (1 if q.yaw >= 0 else -1)
    flip = (side > 0) == (q.yaw >= 0)
    show_palm = hp in ("open", "offer") and arm.gesture in ("present", "place")
    return B.hand(cr, wr[0] + fdx * 6.0, wr[1] + fdy * 6.0, hang, HAND_LEN, hp, M["fur"], q.light_nb, q.lw,
                  flip=flip, claw=None, pad=LIONESS_COLORS["pad"], show_palm=show_palm,
                  hold=arm.hold if hold else None, finger_w=1.15, palm_w=1.1, detail=q.detail)


def _two_hand(q, A0, A1, draw):
    """read_note: sleeves, then the note between the paws, then both paws over it."""
    _arm(q, A0, A0["side"], parts="sleeve")
    _arm(q, A1, A1["side"], parts="sleeve")
    g = []
    for A in (A0, A1):
        el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
        fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
        g.append((wr[0] + fdx * 24.0, wr[1] + fdy * 24.0))
    mx, my = (g[0][0] + g[1][0]) / 2, (g[0][1] + g[1][1]) / 2 - 34.0      # the paws pinch its lower edge
    cr = q.cr
    cr.save()
    cr.translate(mx, my)
    draw(cr, B.HandFrame(0.0, 0.0, 0.0, 1.0, [], (0.0, 0.0), False))
    cr.restore()
    h0 = _arm(q, A0, A0["side"], parts="hand", hold=False)
    h1 = _arm(q, A1, A1["side"], parts="hand", hold=False)
    return h0, h1, (mx, my)


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _tail(q):
    """The long tail sweeping out behind her, the dark tuft at its tip."""
    cr, proj, S, t, pose = q.cr, q.proj, q.S, q.t, q.pose
    pel = S["pelvis"]
    sw = B.chain(t, 6, freq=0.3, delay=0.2, amp=0.6 * S["frz"] + 0.2, seed=pose.seed + 11, grow=2.6)
    swing = pose.tail_swing + 0.3 * S["walk"] * math.sin(TAU * S["wc"].phase)
    # out of the robe's back seam, down and out to the side the camera sees best
    side = math.copysign(1.0, -math.sin(q.yaw) + 0.3)
    # a J: down behind her, out to the side and curling up, the tuft ~100 px off the ground
    pts3 = [v_add(pel, (0.0, 10.0, -26.0)), v_add(pel, (side * 12.0, 60.0, -48.0)), v_add(pel, (side * 30.0, 100.0, -60.0)),
            v_add(pel, (side * 58.0, 112.0, -60.0)), v_add(pel, (side * 80.0, 94.0, -54.0)), v_add(pel, (side * 90.0, 70.0, -48.0))]
    out = []
    acc = 0.0
    for i, p in enumerate(pts3):
        u = i / 5.0
        if i:
            acc += sw[i]
        out.append(proj.xy((p[0] + (swing * 40.0 * u * u + acc * 34.0 * u) * side, p[1] - 10.0 * u * u * acc, p[2])))
    s_, o_ = B.tube_paths(cr, out, [12.0, 10.5, 9.0, 8.0, 7.0, 6.5], q.lw, samples=3)
    q.shade(s_, q.M["fur"], outline=o_, size=14, rim=0.6)
    tip, prev = out[-1], out[-2]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    tuft = []
    for k in range(9):
        r = 13.0 if k % 2 == 0 else 8.5
        b_ = a + TAU * k / 9
        tuft.append((tip[0] + math.cos(a) * 8.0 + math.cos(b_) * r, tip[1] + math.sin(a) * 8.0 + math.sin(b_) * r))
    ts, to = B.smooth_paths(cr, tuft, q.lw, 0.7)
    K.flat(q, ts, to, q.M["mark"], tone=0.15)


def _feet(q):
    """Her paws peeking out under the robe's hem (one union)."""
    cr, proj, S = q.cr, q.proj, q.S
    hulls = []
    for f in S["feet"]:
        a = f["ankle"]
        c, sn = math.cos(f["toe"]), math.sin(f["toe"])

        def F(dx, dy, dz, a=a, c=c, sn=sn):
            return proj.xy((a[0] + dx, a[1] + ANKLE_H + dy * c - dz * sn, a[2] + dy * sn + dz * c))
        pts = []
        for k in range(8):
            ang = TAU * k / 8
            pts.append(F(math.cos(ang) * 12.0, -12.0 + math.sin(ang) * 3.0, math.sin(ang) * 9.0))
            pts.append(F(math.cos(ang) * 13.0, -6.0 + math.sin(ang) * 6.0, 12.0 + math.sin(ang) * 6.0))
        hulls.append(core.convex_hull(pts))
    K.union(q, hulls, q.M["fur"], size=16, rim=0.5)
    if q.detail >= 2 and proj.depth((0.0, 0.0, 1.0)) > 0.2:      # toe lines
        lines = []
        for f in S["feet"]:
            a = f["ankle"]
            for dx in (-4.0, 4.0):
                p0 = proj.xy((a[0] + dx, a[1] + ANKLE_H - 9.0, a[2] + 15.0))
                p1 = proj.xy((a[0] + dx * 1.2, a[1] + ANKLE_H - 2.0, a[2] + 18.0))
                lines.append([p0, p1])
        B.detail_lines(cr, lines, q.lw * 0.7, q.P(q.M["fur"]).line, 0.6)


def _robe_rings(q):
    S = q.S
    T, pel = S["T"], S["pelvis"]
    walk = S["walk"]
    ph = S["wc"].phase
    sw = walk * math.sin(TAU * ph) * 10.0
    return [(T((0.0, -108.0, 2.0)), 38.0, 26.0),            # shoulders (under the collar)
            (T((0.0, -80.0, 5.0)), 41.0, 29.0),             # bust
            (T((0.0, -44.0, 3.0)), 32.0, 24.0),             # waist
            (v_add(pel, (0.0, 4.0, 0.0)), 44.0, 33.0),      # hips
            ((pel[0] * 0.5 + sw * 0.4, -110.0, 0.0), 53.0, 40.0),
            ((pel[0] * 0.3 + sw, -12.0, -2.0 - walk * 6.0), 66.0 + walk * 6.0, 48.0)]


def _robe(q):
    """The long apothecary robe: one A-line silhouette from the shoulders to the ankles."""
    cr, proj, S, t = q.cr, q.proj, q.S, q.t
    rings = _robe_rings(q)
    left, right = [], []
    for (c, a, cz) in rings:
        x, y, hw = proj.ellipse(c, a, cz)
        left.append((x - hw, y))
        right.append((x + hw, y))
    cH, aH, czH = rings[-1]
    ring = [proj((cH[0] + math.sin(TAU * i / 20) * aH, cH[1], cH[2] + math.cos(TAU * i / 20) * czH)) for i in range(20)]
    hem = []
    xL, xR = left[-1][0], right[-1][0]
    for i in range(1, 10):
        xx = lerp(xL, xR, i / 10)
        best = None
        for j in range(20):
            pa, pb = ring[j], ring[(j + 1) % 20]
            if (pa[0] - xx) * (pb[0] - xx) <= 0 and pa[0] != pb[0]:
                yy = pa[1] + (pb[1] - pa[1]) * (xx - pa[0]) / (pb[0] - pa[0])
                best = yy if best is None else max(best, yy)
        if best is not None:
            hem.append((xx, best + 2.0 * math.sin(i * 2.1 + t * 1.4) * (0.4 + S["walk"])))
    nb = proj.xy(S["neck"])
    c0, a0, cz0 = rings[0]
    x0, y0, hw0 = proj.ellipse(c0, a0, cz0)
    top = [(x0 - hw0 * 0.95, y0 - 4.0), (nb[0] - 18.0, nb[1] + 2.0), (nb[0] + 18.0, nb[1] + 2.0), (x0 + hw0 * 0.95, y0 - 4.0)]
    pts = left + hem + right[::-1] + top[::-1]
    rs, ro = B.smooth_paths(cr, pts, q.lw, 0.8)
    pal = q.shade(rs, q.M["robe"], outline=ro, size=120, shadow=0.6)
    q.S["robe_path"] = rs
    if q.detail >= 1:                       # long folds from the hips to the hem
        cr.save()
        rs.add(cr)
        cr.clip()
        cW, aW, czW = rings[3]
        lines = []
        for phi in (-1.25, -0.55, 0.5, 1.2):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.12:
                continue
            A2 = proj.xy((cW[0] + math.sin(phi) * aW * 0.92, cW[1] + 30.0, cW[2] + math.cos(phi) * czW * 0.92))
            B2 = proj.xy((cH[0] + math.sin(phi * 1.05) * aH * 0.97, cH[1] - 2.0, cH[2] + math.cos(phi * 1.05) * czH * 0.97))
            lines.append([A2, ((A2[0] + B2[0]) / 2 + 3.0 * math.sin(phi * 3), (A2[1] + B2[1]) / 2), B2])
        if lines:
            B.detail_lines(cr, lines, q.lw * 1.0, pal.line, 0.45, taper=(0.05, 0.8, 1.0))
        cr.restore()


def _apron(q):
    """The cream linen bib-apron on the front of the robe, with its pocket and straps."""
    cr, proj, S = q.cr, q.proj, q.S
    rings = _robe_rings(q)
    front = proj.depth(m_vec(S["R"], (0.0, 0.0, 1.0)))
    if front < -0.15:
        return

    def on(k, phi, dy=0.0, out=1.04):
        c, a, cz = rings[k]
        return proj.xy((c[0] + math.sin(phi) * a * out, c[1] + dy, c[2] + math.cos(phi) * cz * out))

    # skirt panel: waist -> below the knee, wrapping the front half
    W = 1.05
    skirt = [on(2, -W * 0.85), on(3, -W, -2.0), on(4, -W * 0.96, 26.0)]
    for i in range(7):                      # its hem, following the robe's curve
        phi = -W * 0.96 + 2 * W * 0.96 * i / 6
        skirt.append(on(4, phi, 30.0 + 3.0 * math.cos(phi)))
    skirt += [on(4, W * 0.96, 26.0), on(3, W, -2.0), on(2, W * 0.85)]
    # bib: up the bust to the chest
    Wb = 0.62
    bib = [on(2, -Wb), on(1, -Wb * 0.95, -6.0), on(1, -Wb * 0.85, -22.0), on(1, Wb * 0.85, -22.0), on(1, Wb * 0.95, -6.0), on(2, Wb)]
    hs = core.convex_hull(bib)
    pairs = [B.smooth_paths(cr, skirt, q.lw, 0.75), B.smooth_paths(cr, hs, q.lw, 0.85)]
    cr.save()
    S["robe_path"].add(cr)
    cr.clip()
    K.union_paths(q, pairs, q.M["apron"], size=70, shadow=0.6)
    cr.restore()
    pal = q.P(q.M["apron"])
    if q.detail >= 1:
        # the waistband (a darker tie) and the pocket with a sprig of lavender
        band = [on(2, -W * 0.85, -4.0), on(2, 0.0, -4.0, 1.06), on(2, W * 0.85, -4.0), on(2, W * 0.85, 4.0),
                on(2, 0.0, 4.0, 1.06), on(2, -W * 0.85, 4.0)]
        cr.new_path()
        core.smooth_closed(cr, band, 0.7)
        core.src(cr, core.mix(pal.shadow, pal.lit, 0.4))
        cr.fill()
        side = -1.0 if q.yaw >= 0 else 1.0
        pk = [on(3, side * 0.62, 16.0, 1.07), on(3, side * 0.2, 16.0, 1.08), on(3, side * 0.2, 46.0, 1.08), on(3, side * 0.62, 46.0, 1.07)]
        if q.detail >= 2:
            sp = q.P(Mat.of("#7E6AA6"))
            stem = [((pk[0][0] + pk[1][0]) / 2, pk[0][1] + 2.0), ((pk[0][0] + pk[1][0]) / 2 + 4.0, pk[0][1] - 20.0)]
            B.detail_lines(cr, [stem], q.lw * 0.8, q.P(Mat.of("#5E7A4A")).lit, 1.0, taper=(1.0, 1.0, 0.5))
            core.src(cr, sp.lit)
            for k in range(5):
                core.circle(cr, stem[1][0] - 1.0 + (k % 2) * 2.5, stem[1][1] + k * 3.5, 2.2)
            cr.fill()
        cr.new_path()
        core.polygon(cr, pk)
        core.src(cr, core.mix(pal.lit, pal.shadow, 0.25))
        cr.fill()
        B.detail_lines(cr, [pk[:2], [pk[1], pk[2], pk[3], pk[0]]], q.lw * 0.7, pal.line, 0.6)


def _collar_neck(q):
    """The neck (fur) rising out of a soft cream collar with a little rose ribbon bow."""
    cr, proj, S = q.cr, q.proj, q.S
    nb = proj.xy(S["neck"])
    pv = proj.xy(S["pivot"])
    hc = proj.xy(S["head_c"])
    ns, no = K.caps(cr, [nb, pv, ((pv[0] + hc[0]) / 2, (pv[1] + hc[1]) / 2)], [23.0, 21.0, 20.0], q.lw)
    q.shade(ns, q.M["fur"], outline=no, size=36, rim=0.5)
    R = S["R"]
    pts = []
    for i in range(14):
        a = TAU * i / 14
        for dy in (4.0, -8.0):
            pts.append(proj.xy(v_add(S["neck"], m_vec(R, (math.sin(a) * 28.0, dy + (3.0 if math.cos(a) > 0 else 0.0), math.cos(a) * 22.0)))))
    cs, co, hull = B.hull_paths(cr, pts, q.lw)
    pal = q.shade(cs, q.M["collar"], outline=co, size=16, rim=0.6)
    front = proj.depth(m_vec(R, (0.0, 0.0, 1.0)))
    if q.detail >= 1 and front > 0.0:
        # frill scallops along the collar's lower edge + the ribbon bow at the throat
        lines = []
        for i in range(-4, 5):
            a = i * 0.32
            if proj.depth((math.sin(a), 0.0, math.cos(a))) < 0.1:
                continue
            p0 = proj.xy(v_add(S["neck"], m_vec(R, (math.sin(a) * 28.5, 3.0, math.cos(a) * 22.5))))
            lines.append([(p0[0] - 3.0, p0[1] - 1.0), (p0[0], p0[1] + 2.5), (p0[0] + 3.0, p0[1] - 1.0)])
        B.detail_lines(cr, lines, q.lw * 0.6, pal.line, 0.45)
        bow = proj.xy(v_add(S["neck"], m_vec(R, (0.0, 0.0, 24.0))))
        rp = q.P(q.M["ribbon"])
        cr.new_path()
        for sx in (-1.0, 1.0):
            core.ellipse(cr, bow[0] + sx * 6.0, bow[1], 6.5 + q.lw * 0.7, 4.0 + q.lw * 0.7, sx * 0.3)
        core.ellipse(cr, bow[0], bow[1], 3.0 + q.lw * 0.7, 3.0 + q.lw * 0.7)
        core.src(cr, rp.line)
        cr.fill()
        for sx in (-1.0, 1.0):
            core.ellipse(cr, bow[0] + sx * 6.0, bow[1], 6.5, 4.0, sx * 0.3)
        core.src(cr, rp.lit)
        cr.fill()
        core.circle(cr, bow[0], bow[1], 3.0)
        core.src(cr, rp.shadow)
        cr.fill()


# ----------------------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------------------

def _expr(pose):
    e = B.expr(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(B.expr(pose.mood2), pose.mood_mix)
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    return e


def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH, HC = S["RH"], S["head_c"]
    e = _expr(pose)
    lw = q.lw
    hyaw = q.yaw + S["head_yaw"]
    near = -1.0 if hyaw >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    jaw = clamp(talk * 0.8 + e.open * 0.9)
    xy = proj.xy

    def P(v):
        w = m_vec(RH, v)
        return xy((HC[0] + w[0] * HS, HC[1] + w[1] * HS, HC[2] + w[2] * HS))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    fur = q.P(M["fur"])
    pale = q.P(M["pale"])

    # ---- ears (behind the skull): round, dark-backed, pale inside
    def ear(s):
        base = (s * 23.0, -22.0, -7.0)
        pts = [P((base[0] + math.cos(a) * 9.5 * (0.85 + 0.15 * s * math.cos(a)), base[1] - 5.0 + math.sin(a) * 9.0, base[2] - 2.0))
               for a in (TAU * i / 10 for i in range(10))]
        es, eo = B.smooth_paths(cr, pts, lw, 0.9)
        facing = nz((s * 0.3, -0.2, 0.9))
        if facing > -0.1:
            q.shade(es, M["fur"], outline=eo, size=16, rim=0.6)
        else:
            K.flat(q, es, eo, M["mark"], tone=0.2)
        if facing > 0.0:
            inner = [P((base[0] + math.cos(a) * 5.2, base[1] - 4.0 + math.sin(a) * 5.2, base[2] + 0.5)) for a in (TAU * i / 8 for i in range(8))]
            cr.new_path()
            core.smooth_closed(cr, inner, 0.9)
            core.src(cr, q.P(M["ear_in"]).lit)
            cr.fill()
            # the dark rim of the ear
            rim_pts = [P((base[0] + math.cos(a) * 9.0, base[1] - 5.0 + math.sin(a) * 8.6, base[2] - 1.8)) for a in (-2.6, -2.0, -1.4, -0.8, -0.2)]
            B.detail_lines(cr, [rim_pts], lw * 1.2, q.P(M["mark"]).lit, 0.9, taper=(0.2, 1.0, 0.2))

    ear(far)
    ear(near)

    # ---- the head: skull + cheek ruffs + muzzle + chin, one fur union
    skull = K.circle_pts(P((0.0, -3.0, -3.0)), 30.0 * HS, 20, sy=0.97)   # a projected sphere: a circle
    ruffs = []
    for s in (-1.0, 1.0):
        ruffs += K.circle_pts(P((s * 21.0, 15.0, 6.0)), 12.0 * HS, 10)
    muzzle = B.ellipsoid_pts(P, (0.0, 13.0, 22.0), 18.5, 13.5, 15.0, 8)
    chin = K.circle_pts(P((0.0, 24.0 + 8.0 * jaw, 18.0 - 2.0 * jaw)), 10.5 * HS, 8)
    hull = core.convex_hull(skull + ruffs + muzzle + chin)
    hs, ho = B.smooth_paths(cr, hull, lw, 0.85)
    q.shade(hs, M["fur"], outline=ho, size=70, shadow=0.85)
    # ---- pale fur: muzzle, chin, and soft patches over the eyes
    cr.save()
    hs.add(cr)
    cr.clip()
    pm = B.ellipsoid_pts(P, (0.0, 14.0, 24.0), 17.5, 12.5, 14.0, 8) + K.circle_pts(P((0.0, 24.0 + 8.0 * jaw, 19.0 - 2.0 * jaw)), 9.5 * HS, 8)
    cr.new_path()
    core.smooth_closed(cr, core.convex_hull(pm), 0.85)
    for s in (far, near):
        if nz((s * 0.4, -0.4, 0.8)) > -0.1:
            core.ellipse(cr, *P((s * 14.0, -15.0, 26.0)), 7.5 * HS, 4.0 * HS)
    core.src(cr, pale.lit)
    cr.fill()
    cr.restore()
    # ---- mouth (an open jaw when she talks)
    mouth = _mouth(q, P, nz, e, jaw, near, fur, pale)
    # ---- eyes with the dark tear-lines
    blink = (B.auto_blink(t, pose.seed + 23) if pose.blink is None else pose.blink) * (1.0 - clamp(pose.freeze))
    eyes = []
    marks = []
    for s in (far, near):
        ec = P((s * 14.5, -6.0, 25.0))
        eyes.append(ec)
        fz = nz((s * 0.45, -0.1, 0.9))
        if fz < 0.05:
            continue
        fore = clamp(0.3 + fz * 0.8, 0.3, 1.0)
        op = P((s * 22.0, -8.0, 21.0))
        outer = 1.0 if op[0] > ec[0] else -1.0
        ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)
        B.eye(cr, ec[0], ec[1], 8.2 * HS * fore, 8.0 * HS, q.light, lw, angle=ang * 0.8 - 0.12 * outer,
              look=(pose.look[0] * outer, pose.look[1]), lid=e.lid, lid_bot=e.lid_bot, tilt=e.lid_tilt,
              outer=outer, blink=blink, iris=LIONESS_COLORS["eye"], iris_hi=LIONESS_COLORS["eye_hi"],
              pupil="#1d120c", pupil_size=0.55 * e.pupil, pupil_aspect=0.72, skin=LIONESS_COLORS["fur"],
              crease=0.2, bags=0.0, line=q.P(M["mark"]).line, lid_shade=0.15, lash=1.0, lash_flick=0.5)
        marks.append([P((s * 8.0, -1.5, 30.0)), P((s * 6.8, 3.5, 33.0)), P((s * 5.0, 6.5, 35.5))])
    if marks and q.detail >= 1:
        B.detail_lines(cr, marks, lw * 1.3, q.P(M["mark"]).lit, 0.9, taper=(1.0, 0.8, 0.2))
    cr.save()
    hs.add(cr)
    cr.clip()
    _brows(q, P, nz, e, near)
    cr.restore()
    # ---- nose: a rounded triangle on the muzzle top + whisker pads + whiskers
    nc = P((0.0, 7.0, 37.0))
    tri = [P((-6.5, 3.5, 36.0)), P((6.5, 3.5, 36.0)), P((0.0, 11.0, 38.0))]
    ns, no = B.smooth_paths(cr, [tri[0], P((0.0, 2.5, 37.5)), tri[1], P((3.3, 7.8, 37.5)), tri[2], P((-3.3, 7.8, 37.5))], lw * 0.9, 0.9)
    q.shade(ns, M["nose"], lw=lw * 0.9, outline=no, size=10, rim=0.6)
    B.sheen(cr, nc[0] - 1.5 * HS, nc[1] - 1.5 * HS, 2.6 * HS, 1.6 * HS, alpha=0.5)
    _whiskers(q, P, nz, near)
    # ---- half-moon spectacles low on the muzzle, the chain looping down behind
    _specs(q, P, nz, near)
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mouth, "nose": nc, "eyes": eyes, "top": P((0.0, -34.0, 0.0))}


def _brows(q, P, nz, e, near):
    cr = q.cr
    far = -near
    strokes = []
    for s in (far, near):
        if nz((s * 0.45, -0.4, 0.8)) < -0.05:
            continue
        asym = e.brow_asym * (1.0 if s == near else -0.4)
        li = (e.brow_in * 0.8 + e.brow_y + asym) * 7.0
        lo = (e.brow_out * 0.6 + e.brow_y + asym) * 6.0
        strokes.append([P((s * 6.5, -16.0 - li, 28.0)), P((s * 14.0, -19.0 - (li + lo) * 0.5, 27.0)), P((s * 22.0, -16.5 - lo, 22.0))])
    if strokes:
        B.detail_lines(cr, strokes, q.lw * 2.0 * HS, q.P(q.M["fur_dk"]).shadow, 0.95, taper=(0.5, 1.0, 0.2))


def _mouth(q, P, nz, e, jaw, near, fur, pale):
    """The cat mouth: a short philtrum under the nose, two curves out to the corners (a smile
    lifts them); talking drops the jaw."""
    cr, lw = q.cr, q.lw
    sm = e.smile
    lc = q.P(q.M["mark"]).lit
    top = P((0.0, 11.0, 36.0))
    mid = P((0.0, 16.0, 35.0))
    if nz((0.0, 0.4, 0.9)) < -0.2:
        return mid
    corners = {s: P((s * 10.5, 17.5 - sm * 3.5, 30.5)) for s in (-1.0, 1.0)}
    if jaw > 0.05:
        h = 3.0 + 12.0 * jaw
        L, R = corners[-1.0], corners[1.0]
        bot = P((0.0, 15.5 + h, 33.0 - h * 0.25))
        cr.new_path()
        cr.move_to(*L)
        cr.curve_to(L[0] * 0.5 + mid[0] * 0.5, mid[1] + 1.0, R[0] * 0.5 + mid[0] * 0.5, mid[1] + 1.0, *R)
        cr.curve_to(R[0], bot[1], L[0], bot[1], *L)
        cr.close_path()
        mp = Path(cr)
        B.flat(cr, mp, LIONESS_COLORS["mouth"], lw * 0.9, lc)
        cr.save()
        mp.add(cr)
        cr.clip()
        core.src(cr, LIONESS_COLORS["tongue"])
        core.ellipse(cr, bot[0], bot[1] - 1.0, abs(R[0] - L[0]) * 0.35 + 1.0, h * 0.4 * HS)
        cr.fill()
        cr.restore()
    lines = [[top, mid]]
    for s in (-1.0, 1.0):
        c = corners[s]
        if nz((s * 0.6, 0.3, 0.7)) > -0.25:
            lines.append([mid, ((mid[0] + c[0]) / 2, (mid[1] + c[1]) / 2 + 2.5), c])
    B.detail_lines(cr, lines, lw * 1.1, lc, 0.95, taper=(0.4, 1.0, 0.3))
    return mid


def _whiskers(q, P, nz, near):
    cr, t, pose = q.cr, q.t, q.pose
    tw = clamp(pose.whisker)
    pads, wh = [], []
    for s in (-1.0, 1.0):
        if nz((s * 0.6, 0.2, 0.75)) < -0.15:
            continue
        for row in range(3):
            for col in range(3 - (row == 2)):
                pads.append(P((s * (6.0 + col * 3.6), 9.5 + row * 3.2, 35.0 - col * 1.5)))
        if q.detail >= 1:
            for k, (dy, spread) in enumerate(((-2.0, -0.12), (1.0, 0.0), (4.0, 0.14))):
                flick = 0.2 * tw * math.sin(t * 31.0 + k + s) + 0.04 * math.sin(t * 1.3 + k)
                a = P((s * 11.0, 11.0 + dy * 0.6, 32.5))
                b = P((s * 40.0, 8.0 + dy * 3.0 + spread * 30.0 + flick * 22.0, 30.0))
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 2.5)
                wh.append([a, m, b])
    core.src(cr, q.P(q.M["mark"]).lit, 0.75)
    for p in pads:
        core.circle(cr, p[0], p[1], 1.05 * HS)
    cr.fill()
    if wh:
        B.detail_lines(cr, wh, q.lw * 0.55, core.mix(q.P(q.M["pale"]).hi, (1, 1, 1), 0.2), 0.9, taper=(1.0, 0.7, 0.15))


def _specs(q, P, nz, near):
    """Gold half-moon spectacles: straight tops just under the eyes, round bottoms; a beaded
    chain from the temples loops down behind her neck. specs=1 pushes them up to read."""
    cr, pose, lw = q.cr, q.pose, q.lw
    up = 3.0 * clamp(pose.specs)
    sp = q.P(q.M["specs"])
    rims = []
    for s in (-near, near):
        if nz((s * 0.35, 0.1, 0.93)) < 0.05:
            continue
        cx, cy, cz = s * 12.5, 1.5 - up, 32.5
        pts = [P((cx - 8.0, cy, cz - s * 0.5)), P((cx + 8.0, cy, cz - s * 0.5))]
        for k in range(1, 8):
            a = math.pi * k / 8
            pts.append(P((cx + math.cos(a) * 8.0, cy + math.sin(a) * 6.0, cz)))
        rims.append(pts[:1] + pts[2:][::-1] + pts[1:2])
    if rims:
        cr.new_path()
        for r in rims:
            core.smooth_closed(cr, r, 0.6)
        lens = Path(cr)
        cr.save()
        lens.add(cr)
        cr.clip()
        core.src(cr, (1, 1, 1), 0.12)
        cr.paint()
        cr.restore()
        bridge = [P((-4.5, 1.0 - up, 36.0)), P((0.0, -0.5 - up, 38.0)), P((4.5, 1.0 - up, 36.0))]
        for pass_, w in ((0, 1.4 + lw * 0.8), (1, 1.4)):
            cr.new_path()
            for r in rims:
                core.smooth_closed(cr, B.offset_closed(r, w * 0.5), 0.6)
                core.smooth_closed(cr, B.offset_closed(r, -w * 0.5)[::-1], 0.6)
            core.tapered(cr, bridge, w, w)
            core.src(cr, sp.line if pass_ == 0 else core.mix(sp.lit, sp.hi, 0.25))
            cr.fill()
    # the chain: temples -> back past the ears -> a loop down the side of the neck
    if q.detail >= 1:
        chains = []
        for s in (-1.0, 1.0):
            if nz((s * 0.9, 0.2, 0.2)) < -0.2:
                continue
            a = P((s * 20.5, 1.5 - up, 28.0))
            b = P((s * 23.0, 22.0, 18.0))
            c_ = P((s * 19.0, 40.0, 14.0))
            d = P((s * 12.0, 52.0, 16.0))
            chains.append([a, b, c_, d])
        if chains:
            bead = core.mix(sp.lit, sp.hi, 0.2)
            for ch_ in chains:
                pts = core.resample(core.spline(ch_, n=4), 11)
                core.src(cr, sp.line)
                for p in pts:
                    core.circle(cr, p[0], p[1], 1.45 * HS)
                cr.fill()
                core.src(cr, bead)
                for p in pts:
                    core.circle(cr, p[0], p[1], 0.95 * HS)
                cr.fill()


# ----------------------------------------------------------------------------------------
# sheets
# ----------------------------------------------------------------------------------------

def _sheet_jar(cr, frame):
    """Placeholder SLEEP DRAUGHT bottle (the props kit draws the real items)."""
    cr.save()
    cr.rotate(-frame.angle)
    core.src(cr, "#2b4a8a")
    core.rounded_rect(cr, -10, -26, 20, 30, 5)
    cr.fill()
    core.src(cr, "#efe6cf")
    cr.rectangle(-8, -16, 16, 9)
    cr.fill()
    core.src(cr, "#7a5a3a")
    cr.rectangle(-4, -32, 8, 7)
    cr.fill()
    cr.restore()


def _sheet_note(cr, frame):
    cr.save()
    core.src(cr, "#efe2bf")
    cr.rotate(0.06)
    core.rounded_rect(cr, -46, -28, 92, 56, 3)
    cr.fill()
    core.text(cr, "Something for", 0, -4, 13, core.HAND, "#3a3040", align="center")
    core.text(cr, "loneliness?", 0, 14, 13, core.HAND, "#3a3040", align="center")
    cr.restore()


def lineup():
    return [B.LineupItem("lioness", lambda cr, x, y, sc: draw_lioness(cr, x, y, sc, LionessPose(facing=1), t=0.4), 170.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    def counter(cr, x, ground, sc, w=260, light=neutral):
        p = B.palette(light, Mat.of("#5a3a26"))
        core.src(cr, p.shadow)
        cr.rectangle(x - w / 2, ground - LIONESS_COUNTER_H * sc, w, LIONESS_COUNTER_H * sc)
        cr.fill()
        core.src(cr, p.lit)
        cr.rectangle(x - w / 2 - 6, ground - LIONESS_COUNTER_H * sc - 10 * sc, w + 12, 12 * sc)
        cr.fill()

    SC = 0.95
    for label, pose in (("3/4 left", LionessPose(facing=-1)), ("front", LionessPose(facing=0)),
                        ("3/4 right", LionessPose(facing=1)), ("near profile", LionessPose(facing=-1, turn=-0.7)),
                        ("talking, kind", LionessPose(facing=-1, talk=0.6, mood="warm")),
                        ("walk", LionessPose(facing=-1, turn=-0.4, walk=1.0, phase=0.3))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 290, 470, floor=440)
            draw_lioness(cr, 145, 455, SC, p.with_(blink=0.0), neutral, t=0.4)
        add(label, 290, 470, fn, "turnaround")
    for label, pose in (("reach_up (shelf)", LionessPose(facing=-1, turn=-0.3, near=LionessArm("reach_up"), look=(-0.3, -0.8), head_nod=0.5)),
                        ("place 0.55 (on the counter)", LionessPose(facing=-1, near=LionessArm("place", phase=0.55, hold=_sheet_jar), look=(-0.3, 0.6), head_nod=-0.2)),
                        ("read_note (2 hands)", LionessPose(facing=-1, turn=0.3, near=LionessArm("read_note", hold=_sheet_note), far=LionessArm("read_note"), specs=1.0, look=(0.0, 0.7), head_nod=-0.35)),
                        ("present: 'Try these'", LionessPose(facing=-1, near=LionessArm("present"), talk=0.5, mood="warm")),
                        ("ring_till 0.45", LionessPose(facing=-1, far=LionessArm("ring_till", phase=0.45), mood="kind", look=(-0.5, 0.5))),
                        ("on_counter + frozen smile", LionessPose(facing=-1, turn=0.3, near=LionessArm("on_counter"), far=LionessArm("on_counter"), smile=0.6, freeze=1.0, whisker=1.0))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 290, 470, "apothecary", floor=440)
            draw_lioness(cr, 150, 455, SC, p.with_(blink=0.0), L["apothecary"], t=0.4)
            if p.near.gesture in ("place", "on_counter") or p.far.gesture == "ring_till":
                counter(cr, 70, 455, SC, w=140, light=L["apothecary"])
        add(label, 290, 470, fn, "gestures")
    FS = 2.2
    for label, kw in (("kind (default)", {}), ("warm, talking", dict(mood="warm", talk=0.7)), ("nod (reading)", dict(head_nod=-0.4, look=(0.0, 0.8), specs=1.0)),
                      ("frozen smile + whiskers", dict(smile=0.7, freeze=1.0, whisker=1.0)), ("happy", dict(mood="happy")),
                      ("worried", dict(mood="worried")), ("surprised", dict(mood="surprised")), ("front: kind", dict(facing=0))):
        kw = dict(kw)
        facing = kw.pop("facing", -1)
        pose = LionessPose(facing=facing, blink=0.0, **kw)

        def fn(cr, p=pose):
            B.sheet_bg(cr, 230, 230)
            hx, hy = K.head_frame(draw_lioness, p, FS, neutral)
            draw_lioness(cr, 115 - hx, 120 - hy, FS, p, neutral, t=0.4)
        add(label, 230, 230, fn, "faces")
    for name in ("apothecary", "washhouse", "street_night", "tavern", "square", "dusk", "golden", "lantern_night"):
        def fn(cr, name=name):
            B.sheet_bg(cr, 210, 440, name, floor=410)
            draw_lioness(cr, 105, 425, 0.82, LionessPose(facing=-1, turn=0.25, blink=0.0), L[name], t=0.4)
        add(name, 210, 440, fn, "lighting & scale")
    for label, px in (("350 px", 350), ("250 px", 250)):
        def fn(cr, px=px):
            B.sheet_bg(cr, 210, 440, "apothecary", floor=410)
            draw_lioness(cr, 105, 425, px / LIONESS_HEIGHT, LionessPose(facing=-1, talk=0.5, mood="warm"), L["apothecary"], t=0.4)
        add(label, 210, 440, fn, "lighting & scale")
    return items
