"""griffin.py -- THE GRIFFIN COURIER (S7): a tired royal-post courier on his break. Walks in on
four legs, sits on his haunches beside the bench, yawns, takes bread in his beak or a talon.

An eagle's head (golden-brown plumage, a cream face, a hooked amber beak, droopy-lidded tired
eyes under a stern feathered brow, feather ear-tufts) on a lion's body (tawny fur, cream
belly, a tufted tail), eagle front legs (feathered "trousers", scaly yellow shanks, dark
talons), lion hind legs, brown wings folded on his back. He wears the royal post's blue felt
courier cap with a long feather and a brass post-horn badge (his signature accent), and a
leather parcel satchel on a strap across his chest, its flap closed with a red wax seal.
Silhouette: walking, a long horizontal lion with a raised eagle head; sitting, a sphinx-like
upright triangle -- the cap and feather on top.

    from film.lib import characters as ch
    p = ch.GriffinPose(facing=-1, sit=1.0, yawn=core.window(t, 12.2, 14.0), mood="tired")
    rig = ch.draw_griffin(cr, x, ground_y, 0.9, p, ch.LIGHTS["golden"], t)
    rig.points["beak"]      # tip of the beak: hand him bread here (beak_hold=...)

Scale 1.0: SITTING on his haunches, ground -> top of the ear-tufts = GRIFFIN_HEIGHT = 380 px
(cap and feather excluded); walking, the head top is ~330. Anchor (x, y) = ground point below
his hips (the haunches): it stays put while he sits down (the hips go down and forward, the
front talons stay planted ~150 px ahead of the anchor along his facing).
"""

import math
from dataclasses import dataclass, field, replace

from .. import core
from ..core import clamp, lerp, smooth
from . import base as B
from . import _folk as F
from .base import Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_lerp, v_sub
from .dragon import Arm

__all__ = ["GriffinPose", "GriffinRig", "draw_griffin", "griffin_walk_phase", "griffin_stride", "GRIFFIN_HEIGHT",
           "GRIFFIN_COLORS", "griffin_mats"]

GRIFFIN_HEIGHT = 380.0
HS = 1.5
TAU = math.tau
ELEV = 0.12
BODY_LEN = 150.0
STRIDE = 150.0

GRIFFIN_COLORS = {
    "plume": "#9C6E3A",      # golden-brown head plumage
    "plume_dk": "#6A4826",   # brow, ear-tufts, wing coverts
    "face": "#E8D6B0",       # cream face
    "beak": "#E3A63A",       # amber beak + cere
    "beak_dk": "#B07A22",
    "fur": "#C49A5E",        # tawny lion body
    "belly": "#E3CFA4",
    "tuft": "#5E3E24",       # tail tuft
    "wing": "#86602F",       # folded wings
    "wing_lt": "#B08A52",
    "scale": "#D9AE4E",      # scaly yellow shanks
    "talon": "#2E2A26",
    "cap": "#2E4A8A",        # royal-post blue felt -- the signature accent
    "cap_dk": "#22386A",
    "badge": "#C9A04A",      # brass post-horn
    "feather": "#EFE7D6",    # the cap's long feather
    "feather_tip": "#6A4826",
    "satchel": "#7A5232",
    "strap": "#5E3E24",
    "seal": "#B8322A",       # red wax seal
    "eye": "#D49A30",        # amber
    "eye_hi": "#FFD978",
    "mouth": "#6A2A30",
    "tongue": "#D06A78",
}

_MATS = {}


def griffin_mats():
    if not _MATS:
        C = GRIFFIN_COLORS
        _MATS.update({
            "plume": Mat.of(C["plume"], sss=0.15),
            "plume_dk": Mat.of(C["plume_dk"]),
            "face": Mat.of(C["face"], sss=0.3, shadow_k=1.1),
            "beak": Mat.of(C["beak"], sheen=0.6, line_k=0.5),
            "fur": Mat.of(C["fur"], sss=0.25),
            "belly": Mat.of(C["belly"], sss=0.4, shadow_k=1.1),
            "tuft": Mat.of(C["tuft"]),
            "wing": Mat.of(C["wing"], shadow_k=1.05),
            "wing_lt": Mat.of(C["wing_lt"]),
            "scale": Mat.of(C["scale"], sheen=0.4),
            "talon": Mat.of(C["talon"], sheen=0.5),
            "cap": Mat.of(C["cap"], shadow_k=1.1, line_k=0.5),
            "badge": Mat.of(C["badge"], sheen=0.8),
            "feather": Mat.of(C["feather"], shadow_k=1.2),
            "satchel": Mat.of(C["satchel"], sheen=0.3),
            "strap": Mat.of(C["strap"], sheen=0.2),
            "seal": Mat.of(C["seal"], sheen=0.5),
        })
    return _MATS


@dataclass
class GriffinPose:
    """Everything that poses the griffin (all optional; same names as DragonPose where they apply).

    facing / turn / yaw   as the bipeds (+1 3/4 facing screen-right, -1 left, 0 front, +-2 back)
    sit        0 on four legs .. 1 sitting on his haunches (animate it: the hips go down and
               forward, the front talons stay planted)
    walk/phase walk blend and cycle phase (griffin_walk_phase from the distance travelled)
    head_turn / head_tilt / head_nod / look / mood / mood2 / mood_mix / blink   as DragonPose
    yawn       0..1 the big droopy yawn: head back, beak wide open, eyes squeezed, wings stretch
    beak_open  0..1 extra beak opening (talk / take bread)
    beak_hold  callback(cr, frame) drawing something held crosswise in the beak (bread)
    talon      Arm-like: Arm("rest") (planted) or Arm("reach", phase=0..1, hold=cb) -- the near
               front talon lifts and reaches forward to take something; Arm("offer") palm-up
    wings      -1 drooped .. 0 folded .. +1 stretched up a little
    tail_curl  0..1 when sitting, how far the tail curls round his front feet
    cap        draw the courier's cap; satchel: draw the parcel satchel
    """
    facing: float = 1
    turn: float = 0.0
    yaw: float = None
    sit: float = 0.0
    walk: float = 0.0
    phase: float = 0.0
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
    blink: float = None
    yawn: float = 0.0
    beak_open: float = 0.0
    beak_hold: object = None
    talon: Arm = field(default_factory=Arm)
    wings: float = 0.0
    tail_curl: float = 1.0
    cap: bool = True
    satchel: bool = True
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


GriffinRig = F.FolkRig


def griffin_stride(scale=1.0, facing=1, turn=0.0):
    y = F.yaw_of(GriffinPose(facing=facing, turn=turn))
    return STRIDE * abs(math.sin(y)) * scale * _B.fit


def griffin_walk_phase(distance_px, scale=1.0, facing=1, turn=0.0):
    st = griffin_stride(scale, facing, turn)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


# ----------------------------------------------------------------------------------------
# skeleton (body space: X his left, Y down, Z forward; origin = ground under his hips)
# ----------------------------------------------------------------------------------------

def _skeleton(q):
    pose, t = q.pose, q.t
    S = {}
    sit = q.sit
    k = smooth(sit)
    walk = clamp(pose.walk) * (1.0 - k)
    br = B.breathing(t, 0.2, pose.seed)
    yawn = clamp(pose.yawn)
    hind = B.walk_cycle(pose.phase, stride=STRIDE, lift=18.0, bob=3.0)
    front = B.walk_cycle(pose.phase + 0.25, stride=STRIDE, lift=22.0, bob=3.0)
    S.update(br=br, walk=walk, yawn=yawn)
    pel = v_lerp((0.0, -170.0 + walk * hind.hip_dy, 0.0), (0.0, -66.0, 34.0), k)
    pel = v_add(pel, (0.0, 0.0, -14.0 * math.sin(math.pi * sit)))
    theta = lerp(0.08, 1.08, k) + 0.04 * yawn
    u = (0.0, -math.sin(theta), math.cos(theta))           # spine direction (hips -> shoulders)
    n = (0.0, -math.cos(theta), -math.sin(theta))          # "up" from the back
    sh = v_add(pel, v_mul3(u, BODY_LEN))
    sh = v_add(sh, (0.0, 1.5 * br + walk * front.hip_dy, 0.0))
    S.update(pel=pel, sh=sh, u=u, n=n, theta=theta)
    S["mid"] = v_add(v_lerp(pel, sh, 0.5), v_mul3(n, -6.0))
    # neck and head
    chest_top = v_add(sh, v_add(v_mul3(u, 22.0), v_mul3(n, 20.0)))
    pivot = v_add(chest_top, (0.0, lerp(-30.0, -26.0, k) - 8.0 * yawn, lerp(34.0, 16.0, k) - 8.0 * yawn))
    S["neck_base"] = chest_top
    S["neck_top"] = pivot
    nod = pose.head_nod * 0.42 + 0.5 * yawn - 0.05 + 0.02 * br
    hy = pose.head_turn * 1.1
    hr = pose.head_tilt + 0.08 * yawn
    RH = m_mul(m_rot_y(hy), m_mul(m_rot_x(nod), m_rot_z(hr)))
    S["RH"] = RH
    S["head_yaw"] = q.yaw + hy
    hb = walk * front.head_bob
    S["head_c"] = v_add(pivot, v_add(m_vec(RH, (0.0, -22.0, 10.0)), (0.0, hb, 0.0)))
    # legs
    feet = []
    for s in (-1.0, 1.0):
        i = 0 if s < 0 else 1
        # front: eagle legs, talons planted ~150 ahead of the hips
        fz, lift, toe, planted = front.feet[i]
        shj = v_add(sh, (s * 30.0, 26.0, 10.0))
        paw = (s * 30.0, -lift * walk, BODY_LEN + 14.0 + fz * walk)
        ank = v_add(paw, (0.0, -16.0, -6.0))
        el, wr = B.ik3(shj, ank, 84.0, 82.0, (s * 0.15, 0.1, -1.0))
        feet.append({"kind": "front", "side": s, "top": shj, "knee": el, "ankle": wr, "ground": paw,
                     "toe": toe * walk, "lift": lift * walk})
    for s in (-1.0, 1.0):
        i = 0 if s < 0 else 1
        fz, lift, toe, planted = hind.feet[i]
        hip = v_add(pel, v_add((s * 34.0, 0.0, 0.0), v_add(v_mul3(u, 4.0), v_mul3(n, -6.0))))
        g_stand = (s * 32.0, -lift * walk, -6.0 + fz * walk)
        g_sit = (s * 44.0, 0.0, 86.0)
        g = v_lerp(g_stand, g_sit, k)
        ca = lerp(0.42 + 0.5 * toe * walk, 1.45, k)         # the cannon lies flat when sitting
        hock = v_add(g, (0.0, -12.0 - 50.0 * math.cos(ca), -50.0 * math.sin(ca)))
        kn, hk = B.ik3(hip, hock, 66.0, 62.0, (s * 0.25, lerp(0.1, -0.2, k), 1.0))
        feet.append({"kind": "hind", "side": s, "top": hip, "knee": kn, "ankle": hk, "ground": g,
                     "toe": toe * walk * (1 - k), "lift": lift * walk})
    S["feet"] = feet
    S["knee"] = [feet[2]["knee"], feet[3]["knee"]]
    S["chest"] = v_add(sh, v_add(v_mul3(u, 20.0), v_mul3(n, -30.0)))
    S["pelvis"] = pel
    S["walk"] = walk
    return S


def v_mul3(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

class _B:
    """A stand-in Build so the _folk context helpers work (only line weight / LOD are used)."""
    hip_w = 30.0
    ankle_h = 14.0
    fit = 1.086        # scale calibration to base.CAST_HEIGHTS (see _folk.Build.fit)


def draw_griffin(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the griffin courier with his anchor at (x, y). Returns a GriffinRig: head, mouth
    (= beak), eyes, top, chest, feet, hand_near (= the near front talon's frame when it
    reaches), points["beak"] (beak tip), points["satchel"], points["seal"]."""
    pose = pose or GriffinPose()
    q = F.begin(cr, x, y, scale, pose, light, t, detail, _B, griffin_mats(), parts, skel=_skeleton,
                height=GRIFFIN_HEIGHT)
    S = q.S
    near, far = q.near, q.far
    rig = F.FolkRig()
    pts = {}
    if q.want("body"):
        if pose.shadow:
            g = [q.proj.xy((f["ground"][0], 0.0, f["ground"][2])) for f in S["feet"]]
            xs = [p[0] for p in g]
            B.contact_shadow(cr, (min(xs) + max(xs)) / 2, 2.0, (max(xs) - min(xs)) / 2 + 40.0, 14.0, alpha=0.32)
        _wing(q, far)
        tail_front = q.sit > 0.6 and pose.tail_curl > 0.3
        if not tail_front:
            _tail(q)
        _leg(q, _foot(S, "hind", far))
        _leg(q, _foot(S, "front", far))
        _body(q)
        _leg(q, _foot(S, "hind", near))
        if tail_front:
            _tail(q)
        talon_frame = _leg(q, _foot(S, "front", near), reach=pose.talon)
        if talon_frame is not None:
            rig.hand_near = talon_frame
        if pose.satchel:
            pts.update(_satchel(q))
        _wing(q, near)
    head = _head(q, draw=q.want("head"))
    rig.head = head["center"]
    rig.mouth = head["mouth"]
    rig.nose = head["mouth"]
    rig.eyes = head["eyes"]
    rig.top = head["top"]
    rig.chest = q.proj.xy(S["chest"])
    rig.lap = q.proj.xy(S["chest"])
    rig.feet = [q.proj.xy(f["ground"]) for f in S["feet"]]
    rig.seat = q.proj.xy(S["pel"])
    if rig.hand_near is None:
        f = _foot(S, "front", near)
        g = q.proj.xy(f["ground"])
        rig.hand_near = B.HandFrame(g[0], g[1] - 10.0, 0.0, 1.0, [], g, False)
    pts["beak"] = head["beak"]
    rig.points.update(pts)
    return F.end(q, rig)


def _foot(S, kind, side):
    for f in S["feet"]:
        if f["kind"] == kind and f["side"] == side:
            return f


# ----------------------------------------------------------------------------------------
# body, legs, tail, wings
# ----------------------------------------------------------------------------------------

def _body(q):
    """The lion torso: haunches, belly, deep chest -- one union, fur; the cream belly below."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    pel, sh, u, n = S["pel"], S["sh"], S["u"], S["n"]
    br = S["br"]
    hq = v_add(pel, v_add(v_mul3(u, 6.0), v_mul3(n, -4.0)))
    mid = S["mid"]
    ch = v_add(sh, v_add(v_mul3(u, 6.0), v_mul3(n, -12.0)))
    k = smooth(q.sit)
    groups = [F.blob_pts(proj, hq, 50.0 + 8 * k, 50.0 + 4 * k, 54.0, 16), F.blob_pts(proj, mid, 44.0 + br, 46.0, 50.0, 14),
              F.blob_pts(proj, ch, 52.0 + br, 60.0, 52.0, 16)]
    shp, pal = F.hull_union(q, groups, M["fur"], 110.0, shadow=0.7)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        # the cream belly / chest underside
        bel = [v_add(hq, v_mul3(n, -40.0)), v_add(mid, v_mul3(n, -40.0)), v_add(ch, v_mul3(n, -46.0)),
               v_add(ch, v_add(v_mul3(n, -30.0), v_mul3(u, 40.0)))]
        bp = [proj.xy(p) for p in bel]
        cr.new_path()
        core.tapered(cr, bp, 34.0, 40.0)
        bpal = q.P(M["belly"])
        core.src(cr, core.mix(bpal.lit, bpal.shadow, 0.35))
        cr.fill()
        if q.detail >= 2:                   # haunch muscle line + shoulder line
            lines = [[proj.xy(v_add(hq, (q.near * 40.0, -30.0, 20.0))), proj.xy(v_add(hq, (q.near * 44.0, 0.0, 34.0))),
                      proj.xy(v_add(hq, (q.near * 40.0, 26.0, 22.0)))]]
            B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.4, taper=(0.1, 1.0, 0.1))
        cr.restore()


def _leg(q, f, reach=None):
    """One leg. Front: eagle leg -- feathered "trousers", a scaly shank, three talons forward
    and one back (lifts to take bread when `reach` is a reaching Arm: then a base.hand talon
    with a z-correct hold). Hind: lion leg -- thigh, shin, hock, a round paw."""
    cr, proj, M = q.cr, q.proj, q.M
    top, kn, an, g = proj.xy(f["top"]), proj.xy(f["knee"]), proj.xy(f["ankle"]), f["ground"]
    lw = q.lw
    if f["kind"] == "hind":
        # leg tube + paw: ONE union (one outline, one shading pass)
        pawc = proj.xy((g[0], g[1] - 8.0, g[2] + 6.0))
        ta, to = B.tube_outline([top, kn, an, pawc], [34.0, 16.0, 10.0, 11.0], 4, 0.75, (0.0, lw), True, True)
        paw = core.convex_hull(F.blob_pts(proj, (g[0], g[1] - 8.0, g[2] + 10.0), 13.0, 9.0, 17.0, 12))
        if (F.area2(paw) > 0) != (F.area2(ta) > 0):      # same winding as the tube: a union, not a hole
            paw = paw[::-1]
        pp = q.P(M["fur"])
        cr.new_path()
        core.smooth_closed(cr, to, 0.9)
        core.smooth_closed(cr, B.offset_closed(paw, lw), 0.85)
        core.src(cr, pp.line)
        cr.fill()
        core.smooth_closed(cr, ta, 0.9)
        core.smooth_closed(cr, paw, 0.85)
        q.shade(Path(cr), M["fur"], outline=False, size=38.0)
        if q.detail >= 1 and proj.depth((0.0, 0.0, 1.0)) > 0.1:
            toes = [[proj.xy((g[0] + d, g[1] - 9.0, g[2] + 18.0)), proj.xy((g[0] + d, g[1] - 2.0, g[2] + 24.0))] for d in (-5.0, 0.0, 5.0)]
            B.detail_lines(cr, toes, q.lw * 0.8, pp.line, 0.6)
        return None
    # front (eagle) leg
    lifted = reach is not None and reach.gesture in ("reach", "take", "offer", "hand_out_offer") and reach.amt > 0
    if lifted:
        u = core.inout_sine(clamp(reach.amt)) * (core.inout_sine(clamp(reach.phase)) if reach.gesture in ("reach", "take") else 1.0)
        shj = f["top"]
        tgt = v_add(f["ankle"], (0.0, -70.0 * u, 50.0 * u))
        el, wr = B.ik3(shj, tgt, 84.0, 82.0, (f["side"] * 0.2, 0.3, -1.0))
        kn, an = proj.xy(el), proj.xy(wr)
    # scaly shank + (planted) the four toes: ONE union
    pal = q.P(M["scale"])
    ta, to = B.tube_outline([top, kn, an], [22.0, 12.0, 9.0], 4, 0.75, (0.0, lw), True, True)
    toes = []
    if not lifted:
        toe = f["toe"]
        for (dx, dz, L) in ((-6.0, 1.0, 22.0), (0.0, 1.0, 26.0), (6.0, 1.0, 22.0), (0.0, -1.0, 13.0)):
            a_ = proj.xy((g[0] + dx * 0.3, g[1] - 6.0, g[2] - 2.0))
            b_ = proj.xy((g[0] + dx, g[1] - 2.0, g[2] + dz * L * math.cos(toe)))
            toes.append((a_, b_))
    tshapes = [B.taper_paths(cr, [a_, b_], 8.0, 4.5, lw * 0.8) for a_, b_ in toes]
    cr.new_path()
    core.smooth_closed(cr, to, 0.9)
    for _sh, so in tshapes:
        so.add(cr)
    core.src(cr, pal.line)
    cr.fill()
    core.smooth_closed(cr, ta, 0.9)
    for sh_, _so in tshapes:
        sh_.add(cr)
    q.shade(Path(cr), M["scale"], outline=False, size=20.0, rim=0.4)
    # feathered "trousers" over the upper leg
    th, thp = F.limb(q, [top, core.lerp_pt(top, kn, 0.85), core.lerp_pt(kn, an, 0.3)], [27.0, 19.0, 13.0], M["plume"], 32.0)
    if q.detail >= 1:                       # jagged feather fringe at the trouser cuff
        c = core.lerp_pt(kn, an, 0.22)
        ux, uy = core.normalize((an[0] - kn[0], an[1] - kn[1]))
        nx, ny = -uy, ux
        lines = [[(c[0] + nx * d * 11 - ux * 6, c[1] + ny * d * 11 - uy * 6), (c[0] + nx * d * 9 + ux * 6, c[1] + ny * d * 9 + uy * 6)]
                 for d in (-0.8, -0.2, 0.4, 0.9)]
        B.detail_lines(cr, lines, q.lw * 0.9, thp.line, 0.6, taper=(1.0, 0.8, 0.1))
        # scale rings on the shank
        lines = []
        for k in range(3):
            m = core.lerp_pt(kn, an, 0.4 + 0.18 * k)
            lines.append([(m[0] - nx * 6, m[1] - ny * 6), (m[0] + ux * 1.5, m[1] + uy * 1.5), (m[0] + nx * 6, m[1] + ny * 6)])
        B.detail_lines(cr, lines, q.lw * 0.6, pal.line, 0.5)
    if lifted:
        el2 = proj.xy(el)
        fdx, fdy = core.normalize((an[0] - el2[0], an[1] - el2[1]))
        ang = math.atan2(fdy, fdx)
        hp = "grip" if reach.hold is not None else ("offer" if reach.gesture in ("offer", "hand_out_offer") else "open")
        return B.hand(cr, an[0], an[1], ang, 44.0, hp, M["scale"], q.light, q.lw, flip=(f["side"] > 0) == (math.sin(q.yaw) >= 0),
                      claw=GRIFFIN_COLORS["talon"], claw_len=0.16, finger_w=0.8, palm_w=0.7, finger_len=1.15,
                      hold=reach.hold, detail=q.detail)
    # planted talons: the dark claws on the toes (drawn with the shank above)
    cp = q.P(M["talon"])
    cr.new_path()
    for a, b_ in toes:
        dx, dy = core.normalize((b_[0] - a[0], b_[1] - a[1]))
        core.tapered(cr, [b_, (b_[0] + dx * 6.0, b_[1] + dy * 6.0 + 2.5)], 4.0, 0.6)
    core.src(cr, cp.lit)
    cr.fill()
    return None


def _tail(q):
    """A lion's tail with a dark tuft: swishing behind when he stands, curled round his front
    feet on the ground when he sits."""
    cr, proj, S, pose, t = q.cr, q.proj, q.S, q.pose, q.t
    pel, u, n = S["pel"], S["u"], S["n"]
    k = smooth(q.sit)
    wav = B.chain(t, 5, freq=0.36, delay=0.18, amp=0.5, seed=pose.seed + 7, grow=2.5)
    root = v_add(pel, v_add(v_mul3(u, -40.0), v_mul3(n, 14.0)))
    side = -q.near                                          # curls round toward the camera side
    stand = [root, v_add(root, (0.0, 30.0, -40.0)), v_add(root, (0.0, 80.0, -62.0)), v_add(root, (0.0, 120.0, -60.0)),
             v_add(root, (0.0, 140.0, -40.0)), v_add(root, (0.0, 146.0, -16.0))]
    c = clamp(pose.tail_curl)
    sit = [root, (side * 20.0, -8.0, -30.0), (side * 52.0, -8.0, -10.0), (side * 64.0, -8.0, 40.0),
           (side * 52.0, -8.0, 90.0 * c + 40.0 * (1 - c)), (side * 20.0, -10.0, 112.0 * c + 50.0 * (1 - c))]
    pts = []
    acc = 0.0
    for i, (a, b_) in enumerate(zip(stand, sit)):
        p = v_lerp(a, b_, k)
        if i:
            acc += wav[min(i - 1, 4)]
        p = (p[0] + acc * 50.0 * (1 - 0.7 * k) * (i / 5.0), p[1], p[2])
        pts.append(proj.xy(p))
    shp, so = B.tube_paths(cr, pts, [12.0, 10.0, 8.5, 7.5, 7.0, 6.5], q.lw, samples=3)
    q.shade(shp, q.M["fur"], outline=so, size=16.0, rim=0.5)
    tip, prev = pts[-1], pts[-2]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    ca, sa = math.cos(a), math.sin(a)
    tuft = [(tip[0] + x * ca - y * sa, tip[1] + x * sa + y * ca) for x, y in ((-6, 0), (4, -10), (24, -7), (34, 0), (24, 7), (4, 10))]
    ts, tso = B.smooth_paths(cr, tuft, q.lw, 0.9)
    q.shade(ts, q.M["tuft"], outline=tso, size=14.0, rim=0.4)


def _wing(q, side):
    """A folded wing along his back: coverts at the shoulder, long primaries sweeping back past
    the haunches; drooped / stretched by pose.wings (and the yawn's stretch)."""
    cr, proj, S, pose, t = q.cr, q.proj, q.S, q.pose, q.t
    sh, u, n = S["sh"], S["u"], S["n"]
    w = clamp(pose.wings + 0.9 * S["yawn"], -1.0, 1.0)
    lift = (w + 1.0) / 2.0
    flutter = 0.6 * math.sin(t * 2.1 + side)
    root = v_add(sh, v_add((side * 26.0, 0.0, 0.0), v_add(v_mul3(u, -6.0), v_mul3(n, 34.0))))
    wrist = v_add(root, v_add((side * (8.0 + 10.0 * lift), 0.0, 0.0), v_add(v_mul3(u, -26.0 + 8 * lift), v_mul3(n, 14.0 + 26.0 * lift))))
    tip = v_add(root, v_add((side * (6.0 + 8 * lift), 0.0, 0.0), v_add(v_mul3(u, -186.0 + 30 * lift), v_mul3(n, -6.0 + 44.0 * lift + flutter))))
    low = v_add(root, v_add((side * 14.0, 0.0, 0.0), v_add(v_mul3(u, -100.0), v_mul3(n, -30.0 + 20 * lift))))
    rp, wp, tp, lp = proj.xy(root), proj.xy(wrist), proj.xy(tip), proj.xy(low)
    under = proj.xy(v_add(root, v_add((side * 16.0, 0.0, 0.0), v_mul3(n, -34.0))))
    # outline of the folded wing: root -> wrist (leading edge) -> tip -> scalloped trailing edge -> under
    trail = []
    for i in range(1, 6):
        a = core.lerp_pt(tp, lp, i / 6.0)
        trail.append((a[0], a[1] + (5.0 if i % 2 else 0.0) * (1.0 if q.detail >= 1 else 0.0)))
    pts = [rp, wp, core.lerp_pt(wp, tp, 0.5), tp] + trail + [lp, under]
    if q.detail >= 1:                       # long primaries fanning past the tip
        prim = []
        for i, (du, dn) in enumerate(((-14.0, 6.0), (-4.0, -4.0), (6.0, -14.0))):
            base_ = v_add(tip, v_add(v_mul3(u, 40.0 + du), v_mul3(n, dn)))
            end_ = v_add(tip, v_add(v_mul3(u, -18.0 + du), v_mul3(n, dn - 8.0 - 4.0 * i)))
            prim.append(B.taper_paths(cr, [proj.xy(base_), proj.xy(end_)], 13.0, 4.0, q.lw * 0.9))
        B.fill_outlines(cr, [o for _, o in prim], q.P(q.M["wing"]).line)
        for sh_, _o in prim:
            sh_.add(cr)
        q.shade(Path(cr), q.M["wing"], lw=q.lw * 0.9, outline=False, size=10.0, rim=0.6)
    shp, pal = F.smooth_shape(q, pts, q.M["wing"], 50.0, tension=0.6, rim=0.8)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        # the paler coverts near the shoulder + primary feather lines
        cov = [rp, wp, core.lerp_pt(wp, tp, 0.35), core.lerp_pt(under, lp, 0.5), under]
        cr.new_path()
        core.smooth_closed(cr, cov, 0.7)
        lt = q.P(q.M["wing_lt"])
        core.src(cr, core.mix(lt.lit, lt.shadow, 0.3))
        cr.fill()
        lines = []
        for i in range(4):
            a = core.lerp_pt(wp, lp, 0.3 + 0.18 * i)
            b_ = core.lerp_pt(tp, lp, 0.1 + 0.2 * i)
            lines.append([a, b_])
        B.detail_lines(cr, lines, q.lw * 0.8, pal.line, 0.45, taper=(0.1, 1.0, 0.4))
        cr.restore()


def _satchel(q):
    """The leather parcel satchel on the near flank, behind the shoulder, its strap across the
    chest, the flap closed with a red wax seal. Returns {"satchel": xy, "seal": xy}."""
    cr, proj, S, M = q.cr, q.proj, q.S, q.M
    sh, u, n = S["sh"], S["u"], S["n"]
    side = q.near
    if math.cos(q.yaw) < -0.6:
        side = q.near
    sw = 2.0 * math.sin(q.t * 1.2) + S["walk"] * 4.0 * math.sin(q.t * 6.0)
    c = v_add(sh, v_add((side * 48.0, 0.0, 0.0), v_add(v_mul3(u, -52.0), v_mul3(n, -22.0 + sw * 0.3))))
    # strap: from the far shoulder over the chest to the bag
    st = [proj.xy(v_add(sh, v_add((-side * 30.0, 0.0, 0.0), v_mul3(n, 30.0)))),
          proj.xy(v_add(S["chest"], (0.0, -6.0, 36.0))), proj.xy(v_add(c, (0.0, -24.0, 10.0)))]
    ss, sso = B.taper_paths(cr, st, 10.0, 10.0, q.lw * 0.8, cap=False)
    q.shade(ss, M["strap"], lw=q.lw * 0.8, outline=sso, size=9.0, rim=0.0)
    bag = F.blob_pts(proj, v_add(c, (0.0, -10.0, 0.0)), 10.0, 18.0, 26.0, 12) + F.blob_pts(proj, v_add(c, (0.0, 14.0, 0.0)), 11.0, 8.0, 28.0, 12)
    bs, bp = F.hull_union(q, [bag], M["satchel"], 34.0, rim=0.4)
    flap = proj.xy(v_add(c, (side * 11.0, -2.0, 0.0)))
    if q.detail >= 1:
        a, b_ = proj.xy(v_add(c, (side * 11.0, -4.0, -24.0))), proj.xy(v_add(c, (side * 11.0, -4.0, 24.0)))
        B.detail_lines(cr, [[a, (flap[0], flap[1] + 8.0), b_]], q.lw * 1.0, bp.line, 0.85)
    vis = q.proj.depth((side, 0.0, 0.0)) > -0.2
    if vis:
        sp = q.P(M["seal"])
        r = 7.5
        cr.new_path()
        core.blob(cr, flap[0], flap[1] + 7.0, r, wobble=0.18, n=8, seed=3)
        B.flat(cr, Path(cr), sp.lit, q.lw * 0.7, sp.line)
        if q.detail >= 1:
            core.src(cr, core.shade(sp.lit, 0.25))
            core.circle(cr, flap[0], flap[1] + 7.0, r * 0.5)
            cr.fill()
    return {"satchel": proj.xy(c), "seal": (flap[0], flap[1] + 7.0)}


# ----------------------------------------------------------------------------------------
# head (head space x HS)
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


def _head(q, draw=True):
    cr, M, pose, S, proj = q.cr, q.M, q.pose, q.S, q.proj
    e = F.expr_of(pose, extra=(("sigh", 0.0),))
    yawn = S["yawn"]
    if yawn > 0:
        e = e.blend(B.expr("laugh", smile=0.0, mouth="o"), yawn)
    P, nz, D, W = F.head_xf(q, HS)
    hyaw = S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    far = -near
    op = clamp(max(pose.beak_open, pose.talk * 0.6, yawn * 1.0))
    ja = op * 0.75
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):                               # lower mandible hinge at (0, 8, 14)
        y, z = v[1] - 8.0, v[2] - 14.0
        return (v[0], 8.0 + y * cj + z * sj, 14.0 - y * sj + z * cj)

    tipv = (0.0, 25.0, 46.0)
    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P((0.0, 15.0, 36.0)), "beak": P(tipv),
           "eyes": [P((s * 14.5, -13.0, 24.0)) for s in (far, near)], "top": P((0.0, -36.0, -2.0))}
    if not draw:
        return pts
    lw = q.lw
    facing_away = nz((0.0, 0.0, 1.0)) < -0.3
    behind = {s: D((s * 18.0, -30.0, -12.0)) < D((0.0, -30.0, -12.0)) - 2.0 for s in (-1.0, 1.0)}
    _tufts(q, P, [s for s in (-1.0, 1.0) if behind[s]])
    # ---- neck ruff + skull: plumage, one union
    nb, nt = S["neck_base"], S["neck_top"]
    neck = F.blob_pts(proj, nb, 36.0, 22.0, 32.0) + F.blob_pts(proj, nt, 24.0, 12.0, 22.0)
    skull = _bp(P, (0.0, -6.0, -2.0), 30.0, 30.0, 32.0, 16)
    cheek = _bp(P, (0.0, 8.0, 12.0), 25.0, 17.0, 22.0, 12)
    shp, pal = F.hull_union(q, [neck, skull, cheek], M["plume"], 76.0)
    if q.detail >= 1:                       # the ruff: feather points where plumage meets fur
        ruff = []
        for i in range(7):
            a = -1.3 + 2.6 * i / 6
            p0 = v_add(nb, (math.sin(a) * 34.0, 18.0, math.cos(a) * 30.0))
            if proj.depth((math.sin(a), 0.0, math.cos(a))) < -0.1:
                continue
            p1 = v_add(p0, (0.0, 14.0, 4.0))
            ruff.append([proj.xy(p0), proj.xy(p1)])
        B.detail_lines(cr, ruff, lw * 1.0, pal.line, 0.55, taper=(1.0, 0.8, 0.1))
    if not facing_away:
        # cream face mask round the eyes and the beak base
        fm = _bp(P, (0.0, -6.0, 18.0), 23.0, 20.0, 14.0, 14) + _bp(P, (0.0, 8.0, 22.0), 16.0, 12.0, 12.0, 10)
        cr.save()
        shp.add(cr)
        cr.clip()
        cr.new_path()
        core.smooth_closed(cr, core.convex_hull(fm), 0.85)
        fp = q.P(M["face"])
        core.src(cr, fp.lit)
        cr.fill()
        cr.restore()
        eyes = []
        for s in (far, near):
            ec = F.eye_at(q, P, nz, s, e, (s * 14.5, -13.0, 24.0), 10.5 * HS, 12.0 * HS, iris=GRIFFIN_COLORS["eye"],
                          iris_hi=GRIFFIN_COLORS["eye_hi"], skin=GRIFFIN_COLORS["face"], pupil="#1d120c",
                          lid_add=0.1, crease=0.35 if q.detail >= 2 else 0.0, bags=0.6 if q.detail >= 1 else 0.0,
                          line=pal.line, normal=(s * 0.45, -0.1, 0.88), squint=clamp((yawn - 0.4) * 2.0),
                          blink=1.0 if yawn > 0.6 else None)
            eyes.append(ec or P((s * 14.5, -13.0, 24.0)))
        pts["eyes"] = eyes
        _brows(q, P, nz, e, near, [shp])
        _beak(q, P, J, nz, op)
    else:
        pts["eyes"] = []
    _tufts(q, P, [s for s in (-1.0, 1.0) if not behind[s]])
    if pose.cap:
        _cap(q, P, nz, D)
    return pts


def _beak(q, P, J, nz, op):
    """The hooked amber beak: cere, upper mandible curving down to the hook, lower mandible
    (it drops for the yawn: the inside of the mouth and a tongue show). beak_hold draws bread
    held crosswise in it."""
    cr, M = q.cr, q.M
    lw = q.lw * 0.9
    if op > 0.05:
        ip = [P((s * 10.0, 11.0, z)) for s in (-1.0, 1.0) for z in (18.0, 30.0)] + [P((0.0, 13.0, 40.0))]
        ip += [P(J((s * 9.0, 13.0, z))) for s in (-1.0, 1.0) for z in (18.0, 28.0)] + [P(J((0.0, 15.0, 37.0)))]
        mh = core.convex_hull(ip)
        cr.new_path()
        core.smooth_closed(cr, mh, 0.8)
        core.src(cr, B.pal(q.light, GRIFFIN_COLORS["mouth"]).lit)
        cr.fill()
        tg = P(J((0.0, 12.0, 30.0)))
        core.src(cr, B.pal(q.light, GRIFFIN_COLORS["tongue"], sss=0.4).lit)
        core.ellipse(cr, tg[0], tg[1], 6.0 * HS, (2.0 + 2.5 * op) * HS)
        cr.fill()
    # lower mandible
    low = [P(J(p)) for p in ((-10.0, 10.0, 16.0), (10.0, 10.0, 16.0), (-7.0, 17.0, 28.0), (7.0, 17.0, 28.0), (0.0, 18.0, 38.0),
                             (0.0, 13.0, 40.0))]
    ls, lso, _ = B.hull_paths(cr, low, lw, 0.8)
    q.shade(ls, M["beak"], lw=lw, outline=lso, size=10.0, rim=0.0, shadow=1.2)
    # upper mandible: cere -> ridge -> hook
    up = [(-11.0, 0.0, 16.0), (11.0, 0.0, 16.0), (-11.0, 13.0, 18.0), (11.0, 13.0, 18.0), (-8.0, 3.0, 30.0), (8.0, 3.0, 30.0),
          (-6.0, 14.0, 31.0), (6.0, 14.0, 31.0), (0.0, 6.0, 40.0), (0.0, 15.0, 42.0)]
    us, uso, _ = B.hull_paths(cr, [P(p) for p in up], lw, 0.8)
    bp = q.shade(us, M["beak"], lw=lw, outline=uso, size=16.0, rim=0.6)
    hook = [P((0.0, 7.0, 38.0)), P((0.0, 14.0, 46.0)), P((0.0, 25.0, 46.0))]
    hs, hso = B.taper_paths(cr, hook, 12.0, 2.5, lw)
    q.shade(hs, M["beak"], lw=lw, outline=hso, size=8.0, rim=0.4)
    lines = []
    for s in (-1.0, 1.0):                   # the nostril on the cere + the gape line
        if nz((s * 0.6, 0.0, 0.7)) > -0.1:
            lines.append([P((s * 5.5, 4.0, 22.0)), P((s * 6.5, 5.0, 25.0))])
            if op < 0.05:
                lines.append([P((s * 13.0, 10.0, 15.0)), P((s * 8.5, 12.0, 28.0)), P((0.0, 13.0, 40.0))])
    if lines:
        B.detail_lines(cr, lines, q.lw * 1.2, bp.line, 0.85, taper=(0.6, 1.0, 0.4))
    if q.detail >= 2:
        B.sheen(cr, *P((-4.0, 0.0, 34.0)), 5.0, 2.5, alpha=0.4)
    hold = q.pose.beak_hold
    if hold is not None:
        # a mouthful held in the gape near the tip, over the mandibles (it reads in any view):
        # frame origin = the gape, +x = the head's left-right axis tilted with the head (do NOT
        # undo frame.angle), 1 unit = 1 body px. Draw a piece ~40-60 px wide.
        a, b_ = P((0.0, 13.0, 33.0)), P(J((0.0, 14.0, 33.0)))
        ax0, ax1 = P((-10.0, 13.0, 30.0)), P((10.0, 13.0, 30.0))
        ang = math.atan2(ax1[1] - ax0[1], ax1[0] - ax0[0])
        if abs(ang) > math.pi / 2:
            ang += math.pi
        cr.save()
        cr.translate((a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2)
        cr.rotate(ang)
        hold(cr, B.HandFrame(0.0, 0.0, ang, 1.0, [], (0.0, 0.0), False))
        cr.restore()


def _brows(q, P, nz, e, near, clip):
    """The stern feathered brow ridge -- here mostly droopy and tired."""
    cr = q.cr
    lwb = q.lw * 0.85
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.45, -0.4, 0.8)) < -0.1:
            continue
        pts = F.brow_pts(P, s, e, near, 5.0, 28.0, -26.0, 30.0, 20.0, 13.0, 11.0)
        sh, so = B.taper_paths(cr, pts, 12.0, 5.0, lwb)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    cr.save()
    for pth in clip:
        pth.add(cr)
    cr.clip()
    B.fill_outlines(cr, outs, q.P(q.M["plume_dk"]).line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["plume_dk"], lw=lwb, outline=False, size=9.0, rim=0.0)
    cr.restore()


def _tufts(q, P, sides):
    """Feather ear-tufts swept up and back (they flatten in the yawn)."""
    if not sides:
        return
    cr = q.cr
    tw = 0.06 * math.sin(q.t * 1.4) - 0.5 * q.S["yawn"]
    outs, shapes = [], []
    for s in sides:
        sp = [P((s * 18.0, -26.0, -6.0)), P((s * 24.0, -40.0 - tw * 10, -14.0)), P((s * 26.0, -50.0 - tw * 12, -28.0))]
        sh, so = B.taper_paths(cr, sp, 15.0, 2.0, q.lw * 0.9)
        shapes.append(sh)
        outs.append(so)
    pal = q.P(q.M["plume_dk"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["plume_dk"], lw=q.lw * 0.9, outline=False, size=10.0, rim=0.8)


def _cap(q, P, nz, D):
    """The royal post's blue felt courier cap, tilted back on his head, a stiff little brim,
    a long feather in the band and a brass post-horn badge in front."""
    cr = q.cr
    sw = 0.06 * math.sin(q.t * 1.3) + 0.05 * B.wobble(q.t, math.floor(q.t / 4.0) * 4.0 + 0.5, 3.0, 4.0)
    feather = [P((14.0, -40.0, -10.0)), P((22.0, -55.0, -26.0)), P((26.0 + sw * 40, -62.0, -48.0)), P((24.0 + sw * 60, -59.0, -68.0))]
    behind_f = D((22.0, -50.0, -24.0)) < D((0.0, -40.0, 0.0))
    if behind_f:
        _feather(q, feather)
    dome = _bp(P, (0.0, -36.0, -8.0), 24.0, 10.0, 24.0, 14) + _bp(P, (0.0, -30.0, -8.0), 25.0, 4.0, 25.0, 12)
    brim = _bp(P, (0.0, -29.0, 14.0), 18.0, 2.5, 11.0, 10)
    shp, pal = F.hull_union(q, [dome, brim], q.M["cap"], 30.0, rim=0.8)
    if q.detail >= 1:
        band = F.front_arc(q, F.head_xf(q, HS)[3]((0.0, -32.0, -8.0)), 25.0 * HS, 25.0 * HS, 9)
        B.detail_lines(cr, [band], q.lw * 1.3, core.shade(pal.lit, 0.35), 0.9, taper=(0.6, 1.0, 0.6))
    if nz((0.0, -0.4, 1.0)) > -0.2:         # brass post-horn badge
        b = P((0.0, -34.0, 17.0))
        bp = q.P(q.M["badge"])
        r = 4.2 * HS
        cr.new_path()
        core.circle(cr, b[0], b[1], r)
        B.flat(cr, Path(cr), bp.lit, q.lw * 0.6, bp.line)
        if q.detail >= 1:
            cr.new_path()
            cr.arc(b[0] - 0.5, b[1] + 0.5, r * 0.55, 0.3, math.pi * 1.4)
            cr.set_line_width(max(0.8, q.lw * 0.5))
            core.src(cr, bp.line)
            cr.stroke()
    if not behind_f:
        _feather(q, feather)


def _feather(q, pts):
    cr = q.cr
    shp, so = B.taper_paths(cr, pts, 9.0, 3.0, q.lw * 0.8)
    pal = q.shade(shp, q.M["feather"], lw=q.lw * 0.8, outline=so, size=8.0, rim=0.5)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        core.src(cr, GRIFFIN_COLORS["feather_tip"])
        core.tapered(cr, pts[2:], 10.0, 4.0)
        cr.fill()
        cr.restore()
        B.detail_lines(cr, [pts], q.lw * 0.6, pal.line, 0.5, taper=(0.6, 1.0, 0.2))


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def _sheet_bread(cr, frame):
    cr.save()
    cr.rotate(-frame.angle)
    core.src(cr, "#6a3e1c")
    core.ellipse(cr, 0, -4, 24, 15)
    cr.fill()
    core.src(cr, "#c88a48")
    core.ellipse(cr, -1, -6, 22, 12.5)
    cr.fill()
    core.src(cr, "#f3e2bd")
    core.ellipse(cr, 9, -3, 9, 7)
    cr.fill()
    cr.restore()


def _sheet_bread_beak(cr, frame):
    """A torn piece of crusty bread held crosswise in the beak (sheet stand-in for the prop)."""
    core.src(cr, "#6a3e1c")
    core.ellipse(cr, 0, 2, 24, 10)
    cr.fill()
    core.src(cr, "#c88a48")
    core.ellipse(cr, -1, 0.5, 22, 8)
    cr.fill()
    core.src(cr, "#f3e2bd")
    core.ellipse(cr, 13, 2, 8, 6)
    cr.fill()


def lineup():
    return [B.LineupItem("griffin", lambda cr, x, y, sc: draw_griffin(cr, x, y, sc, GriffinPose(facing=1, sit=1.0), t=0.4), 260.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    for label, pose in (("sit 3/4 left", GriffinPose(facing=-1, sit=1.0)), ("sit front", GriffinPose(facing=0, sit=1.0)),
                        ("sit 3/4 right", GriffinPose(facing=1, sit=1.0)), ("sit profile", GriffinPose(facing=1, turn=0.75, sit=1.0)),
                        ("sit back 3/4", GriffinPose(facing=1, turn=2.6, sit=1.0))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 360, 470, floor=440)
            draw_griffin(cr, 185, 452, 0.9, p, neutral, t=0.4)
        add(label, 360, 470, fn, "turnaround & walk (x0.9)")
    for label, ph in (("walk 0.00", 0.0), ("walk 0.25", 0.25), ("walk 0.50", 0.5), ("walk 0.75", 0.75)):
        def fn(cr, ph=ph):
            F.sheet_bg(cr, 420, 330, floor=300)
            draw_griffin(cr, 150, 312, 0.82, GriffinPose(facing=1, walk=1.0, phase=ph), neutral, t=ph)
        add(label, 420, 330, fn, "turnaround & walk (x0.9)")

    moods = [("tired (default)", dict()), ("droopy, look down", dict(look=(0.2, 0.6))), ("yawn 0.5", dict(yawn=0.5)),
             ("YAWN", dict(yawn=1.0)), ("warm", dict(mood="warm")), ("happy", dict(mood="happy")),
             ("surprised", dict(mood="surprised")), ("beak: bread", dict(mood="happy", beak_open=0.35, beak_hold=_sheet_bread_beak)),
             ("front", dict(facing=0)), ("front: yawn", dict(facing=0, yawn=1.0)), ("3/4 left: warm", dict(facing=-1, mood="warm")),
             ("profile", dict(facing=1, turn=0.75))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        turn = kw.pop("turn", -0.3 if facing == 1 else (0.3 if facing == -1 else 0.0))
        pose = GriffinPose(facing=facing, turn=turn, sit=1.0, **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 230, 230)
            s0, c0 = core.frame(4, 4)
            r0 = draw_griffin(c0, 0.0, 0.0, 1.35, p, neutral, t=0.4)
            draw_griffin(cr, 115 - r0.head[0], 130 - r0.head[1], 1.35, p, neutral, t=0.4)
        add(label, 230, 230, fn, "faces")

    beats = [("sitting down 0.3", GriffinPose(facing=-1, sit=0.3)), ("sitting down 0.6", GriffinPose(facing=-1, sit=0.6)),
             ("beside the bench", GriffinPose(facing=-1, sit=1.0, look=(-0.3, 0.2))),
             ("takes bread (talon)", GriffinPose(facing=-1, sit=1.0, mood="warm", talon=Arm("reach", phase=1.0, hold=_sheet_bread))),
             ("bread in his beak", GriffinPose(facing=-1, sit=1.0, mood="happy", beak_open=0.3, beak_hold=_sheet_bread_beak)),
             ("yawn + stretch", GriffinPose(facing=-1, sit=1.0, yawn=1.0))]
    for label, pose in beats:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 340, 420, floor=390)
            if p.sit > 0.9:
                F.sheet_bench(cr, 280, 402, 0.76, w=200)
            draw_griffin(cr, 200, 402, 0.76, p, neutral, t=0.4)
        add(label, 340, 420, fn, "actions (S7) & lights")
    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 170, 300, name, floor=272)
            draw_griffin(cr, 98, 284, 0.55, GriffinPose(facing=-1, turn=0.25, sit=1.0), L[name], t=0.4)
        add(name, 170, 300, fn, "actions (S7) & lights")
    return items
