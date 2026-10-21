"""orc.py -- THE ORC (S5 fighter): the one who stops fighting, drops his arms and hugs.

A broad, top-heavy brute with a soft heart: moss-green skin, a huge underbite jaw with two ivory
tusks, a heavy brow, long pointed ears, a black topknot, a red leather jerkin laced up the
front (his signature accent), a leather belt, leather bracers, dark wool breeches and fur-cuffed
boots. Silhouette: an inverted triangle -- huge shoulders and forearms on a narrow waist and
short legs, a small head jutting forward -- capped by two swept-back ears.

    from film.lib import characters as ch
    pose = ch.OrcPose(facing=1, mood="angry", stance=0.6, near=ch.Arm("shove", phase=u),
                      far=ch.Arm("shove", phase=u))
    rig = ch.draw_orc(cr, x, ground_y, 0.7, pose, ch.LIGHTS["square"], t)

    # the whole S5 fight -> stop -> hug -> hug-back beat, both fighters, z-correct:
    ch.draw_brawl(cr, cx, ground_y, 0.7, ch.LIGHTS["square"], t)          # see draw_brawl

Scale 1.0: standing, ground -> crown = ORC_HEIGHT = 480 px (ears and topknot included).
Anchor (x, y) = ground point below the pelvis (below the seat when sitting). Built on the
shared part-B biped rig (_folk.py): continuous turn incl. back views, walk, sit, gestures.
"""

import math
from dataclasses import dataclass

from .. import core
from ..core import clamp, lerp
from . import base as B
from . import _folk as F
from .base import Mat, Path, v_add, v_lerp
from .dragon import Arm

__all__ = ["OrcPose", "OrcRig", "draw_orc", "draw_brawl", "brawl_state", "orc_walk_phase", "ORC_HEIGHT",
           "ORC_COLORS", "ORC_GESTURES", "orc_mats"]

ORC_HEIGHT = 480.0
HS = 1.4                                   # head space -> body px

ORC_COLORS = {
    "skin": "#738F45",       # moss green
    "skin_dk": "#5B7834",    # brow ridge, inner ear, nose
    "jerkin": "#A1362A",     # red leather -- the signature accent
    "lace": "#4A2418",       # rawhide lacing
    "belt": "#4A3222",
    "buckle": "#9C9682",     # dull iron
    "breeches": "#4C4842",   # dark grey-brown wool
    "boots": "#3E2C22",
    "fur": "#A08A6C",        # boot cuffs
    "bracer": "#5C3D28",
    "hair": "#2B2624",
    "tusk": "#EDE3C8",
    "eye": "#A8743A",        # warm hazel
    "eye_hi": "#E8B86A",
    "nail": "#3A382F",
    "mouth": "#4A1E22",
    "tongue": "#B8505E",
}

ORC_BUILD = F.Build(
    pelvis_h=205.0, hip_w=30.0, thigh=98.0, shin=94.0, ankle_h=20.0,
    sh_y=156.0, sh_z=2.0, sh_w=78.0, upper_arm=95.0, forearm=90.0, hand_len=74.0,
    neck_y=172.0, neck_z=8.0, neck_len=16.0, head_up=16.0, head_fwd=12.0,
    hunch=0.5, hunch_fwd=18.0, stride=170.0, lift=22.0, bob=5.0, breath=0.2,
    sit_drop=16.0, sit_back=10.0, sway=2.5, knee_out=0.25)

_MATS = {}


def orc_mats():
    if not _MATS:
        C = ORC_COLORS
        _MATS.update({
            "skin": Mat.of(C["skin"], sss=0.35),
            "skin_dk": Mat.of(C["skin_dk"], sss=0.3),
            "jerkin": Mat.of(C["jerkin"], sheen=0.3, line_k=0.5),
            "lace": Mat.of(C["lace"]),
            "belt": Mat.of(C["belt"], sheen=0.3),
            "buckle": Mat.of(C["buckle"], sheen=0.7),
            "breeches": Mat.of(C["breeches"], shadow_k=1.1),
            "boots": Mat.of(C["boots"], sheen=0.35),
            "fur": Mat.of(C["fur"], shadow_k=1.1),
            "bracer": Mat.of(C["bracer"], sheen=0.3),
            "hair": Mat.of(C["hair"], sheen=0.3),
            "tusk": Mat.of(C["tusk"], sheen=0.5, line_k=0.45),
        })
    return _MATS


@dataclass
class OrcPose(F.FolkPose):
    """FolkPose (see _folk.FolkPose / DragonPose) plus:
    snarl     0..1 lip curl that bares the tusks (fighting)
    hug_reach / hug_w / hug_d / hug_y   the "hug" gesture's partner: distance from the orc's
              pelvis to the partner's torso centre, the partner's half-width and half-depth
              there, and the hug height above the orc's pelvis (draw_brawl sets these)
    ears      -1 flattened back .. +1 perked (added to the mood's ear set)
    """
    mood: object = "neutral"
    snarl: float = 0.0
    hug_reach: float = 100.0
    hug_w: float = 78.0
    hug_d: float = 50.0
    hug_y: float = 118.0
    hug_y_far: float = None
    ears: float = 0.0


OrcRig = F.FolkRig
ORC_GESTURES = dict(F.GESTURES)


def orc_walk_phase(distance_px, scale=1.0, yaw=1.0):
    """Walk phase from the screen distance travelled (OrcPose(walk=1, phase=...))."""
    return F.walk_phase(ORC_BUILD, distance_px, scale, yaw)


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_orc(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the orc with its anchor at (x, y). Returns an OrcRig (attach points in caller
    coordinates). parts: None = everything, or a subset of ("back", "body", "mid", "head",
    "front") to interleave with another creature (draw_brawl does this for the hug)."""
    pose = pose or OrcPose()
    q = F.begin(cr, x, y, scale, pose, light, t, detail, ORC_BUILD, orc_mats(), parts)
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far, ORC_GESTURES) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    if q.want("body") and pose.shadow:
        F.contact(q, 74.0)
    for s in (q.far, q.near):
        if lay[s] == "back" and q.want("back"):
            hands[s] = _arm(q, A[s])
    if q.want("body"):
        _legs(q)
        _torso(q)
    for s in (q.far, q.near):
        if lay[s] == "mid" and q.want("mid"):
            hands[s] = _arm(q, A[s])
    head = _head(q, draw=q.want("head"))
    for s in (q.far, q.near):
        if lay[s] == "front" and q.want("front"):
            hands[s] = _arm(q, A[s])
    rig = F.base_rig(q, head)
    rig.hand_near = hands.get(q.near) or _hand_guess(q, A[q.near])
    rig.hand_far = hands.get(q.far) or _hand_guess(q, A[q.far])
    rig.points["layers"] = lay
    return F.end(q, rig)


def _hand_guess(q, A):
    el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    d = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    a = math.atan2(d[1], d[0])
    return B.HandFrame(wr[0] + d[0] * 30, wr[1] + d[1] * 30, a, 1.0, [], wr, False)


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _legs(q):
    """Both breeches legs (one union) and both fur-cuffed boots (one union each)."""
    M = q.M
    _shp, pal = F.legs(q, [30.0, 21.0, 15.5], M["breeches"], 46.0)
    if q.detail >= 2:                       # a crease over each knee
        lines = []
        for f in q.S["feet"]:
            hip, kn, an = F.leg_spine(q, f)
            ux, uy = core.normalize((an[0] - hip[0], an[1] - hip[1]))
            lines.append([(kn[0] - uy * 12 - ux * 8, kn[1] + ux * 12 - uy * 8), (kn[0] - uy * 3, kn[1] + ux * 3),
                          (kn[0] + uy * 7 + ux * 6, kn[1] - ux * 7 + uy * 6)])
        B.detail_lines(q.cr, lines, q.lw * 0.8, pal.line, 0.4)
    F.feet(q, M["boots"], size=30.0, length=52.0, width=17.0, height=20.0, shaft=48.0, shaft_r=17.5)
    groups = []
    for f in q.S["feet"]:                   # fur cuffs round the boot tops (one union)
        top = v_lerp(f["ankle"], f["knee"], 48.0 / q.b.shin)
        groups.append(F.blob_pts(q.proj, top, 21.5, 7.5, 21.5, 12))
    if q.detail >= 1:
        F.hull_union(q, groups, M["fur"], 14.0, rim=0.0, bounce=0.0)


def _front_arc(q, c, a, cz, n=9, extend=1.0):
    """Projected points of the half of a horizontal ring facing the camera (left -> right)."""
    phc = -q.yaw
    out = []
    for i in range(n):
        ph = phc - math.pi / 2 * extend + math.pi * extend * i / (n - 1)
        out.append(q.proj.xy((c[0] + math.sin(ph) * a, c[1], c[2] + math.cos(ph) * cz)))
    out.sort(key=lambda p: p[0])
    return out


def _torso(q):
    """The red leather jerkin (laced V over the chest), its seams, the belt and buckle."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    T = S["T"]
    br, h = S["br"], S["hunch"]
    nb = S["neck_base"]
    sit = q.sit
    hem_c = v_add(S["pelvis"], (0.0, 28.0 - 18.0 * sit, 4.0 + 34.0 * sit))
    rings = [
        (T((0.0, -160.0 + 6 * h, 8.0 + 10 * h)), 52.0, 36.0),       # 0 over the shoulders
        (T((0.0, -140.0 + 4 * h, 4.0)), 78.0 + br, 46.0),           # 1 shoulders
        (T((0.0, -112.0, 9.0)), 80.0 + 1.5 * br, 52.0 + br),        # 2 chest
        (T((0.0, -76.0, 7.0)), 64.0, 48.0),                         # 3 ribs
        (T((0.0, -40.0, 4.0)), 53.0, 43.0),                         # 4 waist
        (v_add(S["pelvis"], (0.0, 0.0, 0.0)), 57.0, 44.0),          # 5 hips
        (hem_c, 62.0 + 6 * sit, 48.0),                              # 6 hem
    ]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=26.0)
    hem = F.hem_curve(q, *rings[-1], n=8, wave=1.0, phase=q.t * 1.3)
    shp, pal = F.smooth_shape(q, left + hem + right[::-1] + top, M["jerkin"], 120.0, shadow=0.6)
    front = proj.depth((0.0, 0.0, 1.0))
    cr.save()
    shp.add(cr)
    cr.clip()
    if front > 0.05:
        # the laced V: chest skin between two leather edges, rawhide criss-cross
        def R3(phi, ring):
            c, a, cz = rings[ring]
            return proj.xy((c[0] + math.sin(phi) * a, c[1], c[2] + math.cos(phi) * cz))
        nbp = proj.xy(nb)
        L0, R0 = R3(-0.45, 0), R3(0.45, 0)
        bot = R3(0.0, 3)
        Lm, Rm = core.lerp_pt(R3(-0.2, 2), bot, 0.2), core.lerp_pt(R3(0.2, 2), bot, 0.2)
        cr.new_path()
        core.smooth_closed(cr, [(L0[0], nbp[1] - 40), L0, Lm, bot, Rm, R0, (R0[0], nbp[1] - 40)], 0.6)
        v = Path(cr)
        sp = q.P(M["skin"])
        v.add(cr)
        core.src(cr, sp.shadow)
        cr.fill()
        kx, ky = B.local_dir(cr, q.light.direction)
        v.add(cr, kx * 5.0, ky * 5.0)
        core.src(cr, core.mix(sp.lit, sp.shadow, 0.3))
        cr.fill()
        ink = [[L0, Lm, bot], [R0, Rm, bot]]
        B.detail_lines(cr, ink, q.lw * 1.15, pal.line, 0.95, taper=(0.6, 1.0, 0.4))
        if q.detail >= 1:
            laces = []
            for k in range(3):
                u0, u1 = 0.18 + 0.26 * k, 0.31 + 0.26 * k
                laces += [[core.lerp_pt(L0, bot, u0), core.lerp_pt(R0, bot, u1)],
                          [core.lerp_pt(L0, bot, u1), core.lerp_pt(R0, bot, u0)]]
            B.detail_lines(cr, laces, q.lw * 1.15, q.P(M["lace"]).lit, 1.0, taper=(0.8, 1.0, 0.8))
    if q.detail >= 2:
        # side seams + cinch folds above and below the belt
        lines = []
        for phi in (-1.25, 1.25):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.1:
                lines.append([proj.xy(v_add(rings[k][0], (math.sin(phi) * rings[k][1] * 0.97, 0.0, math.cos(phi) * rings[k][2] * 0.97)))
                              for k in (1, 2, 3)])
        for phi in (-0.7, -0.25, 0.3, 0.75):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.2:
                c4, a4, z4 = rings[4]
                p0 = proj.xy(v_add(c4, (math.sin(phi) * a4, -16.0, math.cos(phi) * z4)))
                p1 = proj.xy(v_add(c4, (math.sin(phi * 1.1) * a4, -2.0, math.cos(phi) * z4)))
                lines.append([p0, p1])
        if lines:
            B.detail_lines(cr, lines, q.lw * 0.85, pal.line, 0.45, taper=(0.1, 1.0, 0.3))
    cr.restore()
    # belt: the visible front half of a band round the waist, and a dull iron buckle
    c4, a4, z4 = rings[4]
    c5, a5, z5 = rings[5]
    yb = v_lerp(c4, c5, 0.55)
    up = _front_arc(q, v_add(yb, (0.0, -9.0, 0.0)), lerp(a4, a5, 0.5) + 3.0, lerp(z4, z5, 0.5) + 3.0)
    lo = _front_arc(q, v_add(yb, (0.0, 9.0, 0.0)), lerp(a4, a5, 0.6) + 3.5, lerp(z4, z5, 0.6) + 3.5)
    belt, bo = B.smooth_paths(cr, up + lo[::-1], q.lw, 0.6)
    bpal = q.shade(belt, M["belt"], outline=bo, size=18.0, rim=0.0)
    bp = proj((yb[0], yb[1], yb[2] + lerp(z4, z5, 0.5) + 4.0))
    if bp[2] > 4.0:
        w = 11.0 * max(0.35, proj.c)
        cr.new_path()
        core.rounded_rect(cr, bp[0] - w, bp[1] - 11.0, 2 * w, 22.0, 4.0)
        B.flat(cr, Path(cr), q.P(M["buckle"]).lit, q.lw * 0.8, q.P(M["buckle"]).line)
        if q.detail >= 2:
            B.detail_lines(cr, [[(bp[0] - w * 0.55, bp[1] - 5), (bp[0] - w * 0.55, bp[1] + 5)],
                                [(bp[0] - w * 0.6, bp[1]), (bp[0] + w * 1.2, bp[1])]], q.lw * 1.0, bpal.line, 0.9)


def _arm(q, A):
    """Bare green arm (Popeye forearm) + a snug leather bracer + a big hand."""
    cr, M, proj = q.cr, q.M, q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fm = core.lerp_pt(el, wr, 0.4)
    shp, pal = F.limb(q, [sh, el, fm, wr], [25.0, 17.0, 20.5, 14.0], M["skin"], 40.0)
    if q.detail >= 2:                       # deltoid line + elbow crease
        ux, uy = core.normalize((el[0] - sh[0], el[1] - sh[1]))
        nx, ny = -uy, ux
        B.detail_lines(cr, [[(sh[0] + ux * 18 + nx * 17, sh[1] + uy * 18 + ny * 17), (sh[0] + ux * 32 + nx * 6, sh[1] + uy * 32 + ny * 6),
                             (sh[0] + ux * 38 - nx * 5, sh[1] + uy * 38 - ny * 5)]], q.lw * 0.8, pal.line, 0.4)
        F.elbow_folds(q, sh, el, wr, 15.0, pal, 0.35)
    if q.detail >= 2:                       # leather bracer: wrist half of the forearm
        F.band(q, shp, core.lerp_pt(el, wr, 0.52), core.lerp_pt(el, wr, 0.97), 18.0, M["bracer"], 34.0)
    return F.hand(q, A, M["skin"], size=78.0, finger_w=1.35, palm_w=1.25)


# ----------------------------------------------------------------------------------------
# head (head space x HS: X his left, Y down, Z forward; centre = skull centre)
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    """Head-space ellipsoid -> its exact projected silhouette (points for hulls)."""
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


def _ear_pts(q, s, e):
    t = q.t
    perk = clamp(0.55 + 0.45 * (e.brow_y + 0.5 * e.smile - 0.6 * max(0.0, e.lid_tilt)) + 0.4 * q.pose.ears, 0.0, 1.0)
    flat_ = clamp(-e.brow_in - 0.2, 0.0, 1.0) * 0.6          # angry: ears pinned back
    tw = 0.06 * math.sin(t * 1.3 + s * 2.0) + 0.1 * B.wobble(t, math.floor(t / 4.0) * 4.0 + 1.3 + s * 0.4, 5.0, 6.0)
    drop = lerp(20.0, -6.0, perk) + tw * 16.0
    tip = (s * (60.0 - 8.0 * flat_), -32.0 + drop, -26.0 - 12.0 * flat_)
    pts = [(s * 31.0, -17.0, -4.0), (s * 44.0, -24.0 + drop * 0.45, -12.0 - 7 * flat_), tip,
           (s * 47.0, -6.0 + drop * 0.5, -14.0 - 6 * flat_), (s * 30.0, 6.0, -8.0)]
    inner = [(s * 33.5, -11.0, -4.0), (s * 44.0, -18.0 + drop * 0.45, -10.0), v_lerp(tip, (s * 44.0, -12.0, -11.0), 0.35),
             (s * 44.0, -7.0 + drop * 0.45, -10.0), (s * 33.5, 1.0, -6.0)]
    return pts, inner


def _ears(q, P, e, sides):
    """Pointed ears (one union for the given sides) swept back and up; they droop when sad
    and pin back when angry."""
    if not sides:
        return
    cr, lw = q.cr, q.lw * 0.95
    outs, shapes, inners = [], [], []
    for s in sides:
        pts, inner = _ear_pts(q, s, e)
        sh, so = B.smooth_paths(cr, [P(p) for p in pts], lw, 0.75)
        shapes.append(sh)
        outs.append(so)
        inners.append([P(p) for p in inner])
    pal = q.P(q.M["skin"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["skin"], lw=lw, outline=False, size=22.0, rim=0.7)
    if q.detail >= 1:
        cr.new_path()
        for inner in inners:
            core.smooth_closed(cr, inner, 0.8)
        core.src(cr, q.P(q.M["skin_dk"]).shadow, 0.5)
        cr.fill()


def _head(q, draw=True):
    cr, M, pose, S, proj = q.cr, q.M, q.pose, q.S, q.proj
    e = F.expr_of(pose)
    P, nz, D, W = F.head_xf(q, HS)
    hyaw = S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    jaw_open = clamp(talk * 0.85 + e.open * 0.9)
    ja = jaw_open * 0.28
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):                               # rotate about the jaw hinge (0, 2, -8)
        y, z = v[1] - 2.0, v[2] + 8.0
        return (v[0], 2.0 + y * cj + z * sj, -8.0 - y * sj + z * cj)

    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P(J((0.0, 14.0, 30.0))), "nose": P((0.0, 2.0, 38.0)),
           "eyes": [P((s * 16.0, -14.0, 27.0)) for s in (far, near)], "top": P((0.0, -47.0, -6.0))}
    if not draw:
        return pts
    lw = q.lw
    pal = q.P(M["skin"])
    ear_behind = {s: D((s * 32.0, -4.0, -6.0)) < D((0.0, -4.0, -6.0)) - 3.0 for s in (-1.0, 1.0)}
    _ears(q, P, e, [s for s in (-1.0, 1.0) if ear_behind[s]])
    _topknot(q, P, D, behind=True)
    # ---- one union: neck + cranium + jowls + jaw + chin + muzzle (one outline, one shading)
    nb, nt = S["neck_base"], S["neck_top"]
    neck = F.blob_pts(proj, v_add(nb, (0.0, 2.0, 6.0)), 31.0, 10.0, 25.0, 12) + F.blob_pts(proj, nt, 29.0, 10.0, 25.0, 12)
    groups = (neck, _bp(P, (0.0, -17.0, -6.0), 34.0, 30.0, 32.0, 16), _bp(P, (0.0, 3.0, 2.0), 37.0, 17.0, 26.0),
              [P(J(p)) for p in ((0.0, 20.0, 8.0),)] and (F.ellipsoid2d(lambda v: P(J(v)), (0.0, 20.0, 8.0), 35.0, 14.0, 27.0)
                                                         + F.ellipsoid2d(lambda v: P(J(v)), (0.0, 26.0, 24.0), 25.0, 10.0, 13.0)),
              _bp(P, (0.0, 9.0, 23.0), 21.0, 8.0, 10.0, 12))
    hulls = [core.convex_hull(g) for g in groups]
    cr.new_path()
    for hh in hulls:
        core.smooth_closed(cr, B.offset_closed(hh, lw), 0.85)
    core.src(cr, pal.line)
    cr.fill()
    paths = []
    for hh in hulls:
        core.smooth_closed(cr, hh, 0.85)
        paths.append(Path(cr))
    for pth in paths:
        pth.add(cr)
    q.shade(Path(cr), M["skin"], outline=False, size=96.0)
    head_clip = paths[1:]
    # mouth interior (talking / shouting): between the upper lip and the dropped jaw
    if jaw_open > 0.04 and nz((0.0, 0.1, 1.0)) > -0.2:
        ip = [P((sd * 20.0, 12.5, z)) for sd in (-1.0, 1.0) for z in (15.0, 27.0)] + [P((0.0, 13.0, 31.0))]
        ip += [P(J((sd * 18.0, 15.0, z))) for sd in (-1.0, 1.0) for z in (15.0, 27.0)] + [P(J((0.0, 16.0, 30.0)))]
        mh = core.convex_hull(ip)
        cr.new_path()
        core.smooth_closed(cr, B.offset_closed(mh, lw * 0.8), 0.8)
        core.src(cr, pal.line)
        cr.fill()
        core.smooth_closed(cr, mh, 0.8)
        mp = Path(cr)
        mp.add(cr)
        core.src(cr, B.pal(q.light, ORC_COLORS["mouth"]).lit)
        cr.fill()
        cr.save()
        mp.add(cr)
        cr.clip()
        tg = P(J((0.0, 17.0, 24.0)))
        core.src(cr, B.pal(q.light, ORC_COLORS["tongue"], sss=0.4).lit)
        core.ellipse(cr, tg[0], tg[1] + 2, 15.0, 4.0 + 6.0 * jaw_open)
        cr.fill()
        cr.restore()
        q.shade(paths[4], M["skin"], outline=False, size=30.0, rim=0.0)     # upper lip over it
    _mouth_line(q, P, J, nz, e, jaw_open, pal)
    _nose(q, P, nz, pal)
    if q.detail >= 1 and (e.smile > 0.2 or e.cheek > 0.25):
        a, b = P((near * 14.0, 4.0, 30.0)), P((near * 22.0, 14.0, 22.0))
        B.detail_line(cr, [a, ((a[0] + b[0]) / 2 + near * 2, (a[1] + b[1]) / 2), b], lw * 0.9, pal.line, 0.5 * max(e.smile, e.cheek))
    # ---- eyes (hooded under the brow), brow ridges (one union), the scar
    eyes = []
    for s in (far, near):
        ec = F.eye_at(q, P, nz, s, e, (s * 16.0, -14.0, 27.0), 11.0 * HS, 13.0 * HS, iris=ORC_COLORS["eye"],
                      iris_hi=ORC_COLORS["eye_hi"], skin=ORC_COLORS["skin"], pupil="#22140c", lid_add=0.2,
                      crease=0.25 if q.detail >= 2 else 0.0, bags=0.25 if q.detail >= 2 else 0.0, line=pal.line,
                      lid_shade=0.16)
        eyes.append(ec or P((s * 16.0, -14.0, 27.0)))
    pts["eyes"] = eyes
    _brows(q, P, nz, e, near, head_clip)
    _tusks(q, P, J, nz, near)
    _ears(q, P, e, [s for s in (-1.0, 1.0) if not ear_behind[s]])
    _topknot(q, P, D, behind=False)
    return pts


def _mouth_line(q, P, J, nz, e, jaw_open, pal):
    """Closed: the line between the upper lip and the jutting lower lip, corners driven by
    the smile (a snarl pulls them down). Open mouths are drawn as an interior instead."""
    if jaw_open >= 0.04:
        return
    sm = e.smile - 0.4 * q.pose.snarl
    lines = []
    for s in (-1.0, 1.0):
        if nz((s * 0.6, 0.1, 0.7)) < -0.1:
            continue
        lines.append([P((s * 23.0, 13.0 - sm * 9.0, 18.0)), P((s * 12.0, 14.5 - sm * 3.0, 28.0)), P((0.0, 15.0 + sm * 1.0, 31.0))])
    if lines:
        B.detail_lines(q.cr, lines, q.lw * 1.25, pal.line, 1.0, taper=(0.5, 1.0, 0.9))
    if q.detail >= 1:                       # the jutting lower lip's soft shadow
        B.detail_lines(q.cr, [[P(J((-14.0, 21.0, 29.0))), P(J((0.0, 23.0, 33.0))), P(J((14.0, 21.0, 29.0)))]],
                       q.lw * 0.9, pal.line, 0.35, taper=(0.1, 1.0, 0.1))


def _nose(q, P, nz, pal):
    """A broad, flat nose with flared nostrils (its own small form over the muzzle)."""
    if nz((0.0, 0.0, 1.0)) < -0.35:
        return
    pts = _bp(P, (0.0, 0.0, 33.0), 11.0, 7.5, 7.0, 12) + _bp(P, (0.0, -9.0, 30.0), 4.5, 4.5, 4.0, 8)
    pts += [P((s * 11.5, 3.5, 29.0)) for s in (-1.0, 1.0)]
    shp, so, _ = B.hull_paths(q.cr, pts, q.lw * 0.9, 0.85)
    np_ = q.shade(shp, q.M["skin"], lw=q.lw * 0.9, outline=so, size=14.0, rim=0.0)
    lines = []
    for s in (-1.0, 1.0):
        if nz((s * 0.5, 0.4, 0.75)) > -0.05:
            lines.append([P((s * 3.5, 4.5, 37.5)), P((s * 7.5, 5.0, 35.5))])
    if lines:
        B.detail_lines(q.cr, lines, q.lw * 1.6, np_.line, 0.9, taper=(1.0, 0.8, 0.3))
    if q.detail >= 2:
        B.sheen(q.cr, *P((0.0, -3.0, 39.0)), 4.0, 2.5, alpha=0.25)


def _brows(q, P, nz, e, near, clip):
    """Both heavy brow ridges (darker skin) as one union, pushed by the Expr; clipped to the
    head so the far one never pokes out of the silhouette."""
    cr = q.cr
    lwb = q.lw * 0.9
    outs, shapes = [], []

    def prof(u):
        return 13.5 * (1.0 - 0.45 * u) * (0.72 + 0.28 * math.sin(math.pi * min(1.0, u * 1.2)))

    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.1:
            continue
        pts = F.brow_pts(P, s, e, near, 3.0, 31.0, -26.5, 34.0, 23.0, 15.0, 13.0)
        sh, so = B.taper_paths(cr, pts, 12.0, 6.0, lwb, profile=prof)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    cr.save()
    for pth in clip:
        pth.add(cr)
    cr.clip()
    B.fill_outlines(cr, outs, q.P(q.M["skin_dk"]).line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["skin_dk"], lw=lwb, outline=False, size=10.0, rim=0.0)
    cr.restore()


def _tusks(q, P, J, nz, near):
    """Two ivory tusks rising from the jutting lower jaw beside the nose (they ride the jaw)."""
    cr = q.cr
    lift = 2.5 * q.pose.snarl
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.35, 0.0, 0.9)) < -0.25:
            continue
        a = P(J((s * 14.0, 19.0, 30.0)))
        m = P(J((s * 15.0, 12.0 - lift, 32.0)))
        b = P(J((s * 17.5, 6.5 - lift, 32.0)))
        sh, so = B.taper_paths(cr, [a, m, b], 8.0, 2.4, q.lw * 0.85)
        shapes.append(sh)
        outs.append(so)
    if shapes:
        B.fill_outlines(cr, outs, q.P(q.M["tusk"]).line)
        for sh in shapes:
            sh.add(cr)
        q.shade(Path(cr), q.M["tusk"], lw=q.lw * 0.85, outline=False, size=8.0, rim=0.0)


def _topknot(q, P, D, behind):
    """A short black mohawk crest from the brow ridge over the crown to the nape, its top edge
    tufted; the loose tuft at the back sways a beat behind the head (secondary motion)."""
    is_behind = D((0.0, -48.0, -6.0)) < D((0.0, -20.0, 0.0)) - 30.0
    if is_behind != behind:
        return
    sw = 1.2 * math.sin(q.t * 1.6 + q.pose.seed) + 2.0 * B.sway(q.t, 0.5, q.pose.seed + 9)
    spine3 = [(0.0, -37.0, 20.0), (0.0, -47.0, 8.0), (0.0, -51.0, -8.0), (0.0, -47.0, -23.0), (0.0, -37.0, -34.0),
              (sw * 0.3, -24.0, -40.0)]
    sp = [P(p) for p in spine3]
    hc = P((0.0, -14.0, -6.0))
    widths = (6.0, 13.0, 15.0, 14.0, 10.0, 4.0)
    tufts = (0.0, 5.0, 7.0, 7.0, 5.0, 0.0) if q.detail >= 1 else (0.0,) * 6
    outer, inner = [], []
    for i, p in enumerate(sp):
        j0, j1 = max(0, i - 1), min(len(sp) - 1, i + 1)
        tx, ty = core.normalize((sp[j1][0] - sp[j0][0], sp[j1][1] - sp[j0][1]))
        nx, ny = -ty, tx
        if (p[0] - hc[0]) * nx + (p[1] - hc[1]) * ny < 0:
            nx, ny = -nx, -ny
        w = widths[i] * HS * 0.5
        outer.append((p[0] + nx * w, p[1] + ny * w))
        inner.append((p[0] - nx * w * 0.7, p[1] - ny * w * 0.7))
        if 0 < i < len(sp) - 1 and tufts[i] > 0:     # a tuft between this sample and the next
            m = ((p[0] + sp[i + 1][0]) / 2, (p[1] + sp[i + 1][1]) / 2)
            outer.append((m[0] + nx * (w + tufts[i] * HS) - tx * 3.0, m[1] + ny * (w + tufts[i] * HS) - ty * 3.0))
    pts = outer + inner[::-1]
    cr = q.cr
    shp, so = B.smooth_paths(cr, pts, q.lw, 0.55)
    pal = q.shade(shp, q.M["hair"], outline=so, size=14.0, rim=0.9)
    if q.detail >= 2:
        B.detail_lines(cr, [sp[1:5]], q.lw * 0.8, core.tint(pal.lit, 0.25), 0.5, taper=(0.1, 1.0, 0.1))


# ----------------------------------------------------------------------------------------
# the fight and the hug (S5): both fighters, z-correct
# ----------------------------------------------------------------------------------------

def brawl_state(t, t_stop=8.5, t_hug=9.6, hug_back=(11.0, 15.0), seed=0):
    """The S5 choreography as plain numbers (scene time t, local seconds): the orc's and the
    minotaur's x offsets from the pair centre (body px at scale 1, + toward the minotaur), who
    is shoving / staggering and how far, and the stop / hug / hug-back blends. draw_brawl()
    draws it; scenes may read it too (cheers on each shove, the camera, the sound cues)."""
    period = 2.1                                    # shoves alternate: orc, minotaur, orc, ...
    k = math.floor(t / period)
    u = (t - k * period) / period
    orc_turn = (k % 2 == 0)
    fight = t < t_stop
    st = {"fight": fight, "shove_index": k, "shover": "orc" if orc_turn else "minotaur"}
    shove = clamp(u / 0.75)                          # the active shover's arm phase 0..1
    recoil = core.out_cubic(clamp((u - 0.42) / 0.22)) * (1.0 - core.inout_sine(clamp((u - 0.62) / 0.38)))
    stepin = math.sin(math.pi * clamp(u / 0.62))
    gap = 300.0                                      # arm's length apart while squaring up
    ox, mx = -gap * 0.45, gap * 0.55
    if fight:
        if orc_turn:
            ox += 34.0 * stepin
            mx += 64.0 * recoil
        else:
            mx -= 34.0 * stepin
            ox -= 64.0 * recoil
        st.update(orc_shove=shove if orc_turn else None, mino_shove=None if orc_turn else shove,
                  orc_stagger=0.0 if orc_turn else recoil, mino_stagger=recoil if orc_turn else 0.0, phase=u,
                  impact=clamp(1.0 - abs(u - 0.47) / 0.08))
    else:
        st.update(orc_shove=None, mino_shove=None, orc_stagger=0.0, mino_stagger=0.0, phase=0.0, impact=0.0)
    stop = core.inout_sine(clamp((t - t_stop) / 0.5))
    step = core.inout_sine(clamp((t - t_hug + 0.5) / 1.0))
    hug = core.inout_sine(clamp((t - t_hug) / 1.1))
    hb = core.inout_sine(clamp((t - hug_back[0]) / max(0.1, hug_back[1] - hug_back[0])))
    st.update(stop=stop, step=step, hug=hug, hug_back=hb)
    if not fight:
        # he walks into the hug: the gap closes to body contact (minotaur's belly, orc's chest)
        ox = lerp(-gap * 0.45, -44.0, step)
        mx = lerp(gap * 0.55, 50.0, step)
    st.update(orc_x=ox, mino_x=mx)
    return st


def draw_brawl(cr, cx, y, scale=1.0, light=None, t=0.0, *, t_stop=8.5, t_hug=9.6, hug_back=(11.0, 15.0),
               orc_left=True, detail=None, orc_talk=0.0, mino_talk=0.0, state=None):
    """The orc and the minotaur, the whole S5 beat, drawn in the right interleaved order.

    0 .. t_stop   they shove each other in turn (angry, squared up, stepping in / staggering)
    t_stop        the orc stops; his arms drop; his face falls
    t_hug         he steps in and hugs the minotaur (head against his chest, eyes closed)
    hug_back      (t0, t1): the stunned minotaur slowly hugs him back, bowing his head over him
    The pair is centred on cx (orc on the left facing right when orc_left). Returns
    (orc_rig, minotaur_rig)."""
    from . import minotaur as MN
    st = state or brawl_state(t, t_stop, t_hug, hug_back)
    sgn = 1.0 if orc_left else -1.0
    L = light or B.LIGHTS["square"]
    stop, hug, hb, step = st["stop"], st["hug"], st["hug_back"], st["step"]
    # ---- orc pose
    if st["fight"]:
        if st["orc_shove"] is not None:
            oa = Arm("shove", phase=st["orc_shove"])
        elif st["orc_stagger"] > 0.02:
            oa = Arm("stagger", amt=clamp(st["orc_stagger"] * 2.0), prev="guard", phase=st["phase"])
        else:
            oa = Arm("guard")
        o_pose = OrcPose(facing=sgn, mood="angry", snarl=0.5, stance=0.5 * sgn, hunch=0.7,
                         lean=0.35 if st["orc_shove"] is not None else -0.45 * st["orc_stagger"],
                         near=oa, far=oa, seed=3)
    else:
        arm_amt = clamp((t - t_stop) / 0.45)
        o_near = Arm("slump", amt=arm_amt, prev="guard")
        o_far = Arm("slump", amt=arm_amt, prev="guard")
        mood2 = "kind"
        if hug > 0.0:
            o_near = Arm("hug", amt=hug, prev="slump", phase=0.0)
            o_far = Arm("hug", amt=hug, prev="slump", phase=0.0)
        o_pose = OrcPose(facing=sgn, mood="sad", mood2=mood2, mood_mix=hug, stance=0.5 * sgn * (1 - stop),
                         hunch=lerp(0.7, 0.85, stop) - 0.1 * hug, lean=0.38 * hug,
                         head_tilt=0.22 * hug * sgn, head_turn=-0.32 * hug * sgn, head_nod=-0.25 * stop - 0.1 * hug,
                         look=(0.0, 0.5 * stop),
                         blink=clamp((hug - 0.5) * 2.5) if hug > 0.5 else None, near=o_near, far=o_far, seed=3,
                         hug_reach=(st["mino_x"] - st["orc_x"]) / 0.84, hug_w=74.0, hug_d=52.0, hug_y=112.0)
    o_pose = o_pose.with_(talk=orc_talk)
    # ---- minotaur pose
    if st["fight"]:
        if st["mino_shove"] is not None:
            ma = Arm("shove", phase=st["mino_shove"])
        elif st["mino_stagger"] > 0.02:
            ma = Arm("stagger", amt=clamp(st["mino_stagger"] * 2.0), prev="guard", phase=st["phase"])
        else:
            ma = Arm("guard")
        m_pose = MN.MinotaurPose(facing=-sgn, mood="angry", stance=0.5 * -sgn, hunch=0.6,
                                 lean=0.35 if st["mino_shove"] is not None else -0.45 * st["mino_stagger"],
                                 near=ma, far=ma, seed=5, shove_y=60.0)
    else:
        # stunned: guard drops to arms held out in surprise, then slowly round the orc
        surprise = core.inout_sine(clamp((t - t_hug) / 0.6))
        lower = clamp((t - t_stop - 0.25) / 0.6)              # confused: the guard comes down
        m_near = Arm("rest", amt=lower, prev="guard")
        m_far = Arm("rest", amt=lower, prev="guard")
        if surprise > 0.0:
            m_near = Arm("surprised", amt=surprise, prev="rest")
            m_far = Arm("surprised", amt=surprise, prev="rest")
        if hb > 0.0:
            # once he holds on: two slow pats on the orc's back every few seconds
            u = (t - hug_back[1] - 0.4) % 4.0 if t > hug_back[1] + 0.4 else 9.0
            pat = 0.16 * math.sin(math.pi * u / 0.34) ** 2 if u < 0.68 else 0.0
            m_near = Arm("hug", amt=hb, prev="surprised", phase=pat)
            m_far = Arm("hug", amt=hb, prev="surprised", phase=0.0)
        m_pose = MN.MinotaurPose(facing=-sgn, turn=0.55 * hb * sgn, mood="angry", mood2="surprised", mood_mix=surprise,
                                 hunch=0.6 - 0.2 * surprise + 0.35 * hb, head_nod=-0.45 * hb, head_tilt=-0.32 * hb * sgn,
                                 head_turn=0.5 * hb * sgn,
                                 near=m_near, far=m_far, seed=5, stance=0.5 * -sgn * (1 - stop),
                                 blink=clamp((hb - 0.6) * 2.5) if hb > 0.6 else None,
                                 hug_reach=(st["mino_x"] - st["orc_x"]) / 0.84, hug_w=66.0, hug_d=46.0, hug_y=-6.0,
                                 hug_y_far=78.0)
        if hb > 0.0:
            m_pose = m_pose.with_(mood="surprised", mood2="kind", mood_mix=hb)
    m_pose = m_pose.with_(talk=mino_talk)
    rock = 3.5 * hug * math.sin((t - t_hug) * math.tau * 0.21) if not st["fight"] else 0.0   # they sway together
    ox, mx = cx + sgn * (st["orc_x"] + rock) * scale, cx + sgn * (st["mino_x"] + rock) * scale
    hugging = (not st["fight"]) and hug > 0.05
    if not hugging:
        # apart: plain draws, the one nearer the camera (lower anchor) last
        m_rig = MN.draw_minotaur(cr, mx, y, scale, m_pose, L, t, detail)
        o_rig = draw_orc(cr, ox, y + 1.0, scale, o_pose, L, t, detail)
        return o_rig, m_rig
    # interleaved: both back arms, the minotaur's body and (bowed) head, then the orc -- his head
    # nestled against the minotaur's chest, under his chin, his near arm round the minotaur's
    # waist -- and last the minotaur's near arm wrapped over the orc's back
    MN.draw_minotaur(cr, mx, y, scale, m_pose, L, t, detail, parts=("back",))
    draw_orc(cr, ox, y + 1.0, scale, o_pose, L, t, detail, parts=("back",))
    MN.draw_minotaur(cr, mx, y, scale, m_pose, L, t, detail, parts=("body", "mid", "head"))
    o_rig = draw_orc(cr, ox, y + 1.0, scale, o_pose, L, t, detail, parts=("body", "mid", "head", "front"))
    m_rig = MN.draw_minotaur(cr, mx, y, scale, m_pose, L, t, detail, parts=("front",))
    return o_rig, m_rig


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("orc", lambda cr, x, y, sc: draw_orc(cr, x, y, sc, OrcPose(facing=1), t=0.4), 230.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    # ---- turnaround (scale 1.0 = 480 px) + a continuous turn (back views included)
    for label, pose in (("3/4 left", OrcPose(facing=-1)), ("front", OrcPose(facing=0)),
                        ("3/4 right", OrcPose(facing=1)), ("profile", OrcPose(facing=1, turn=0.75)),
                        ("back 3/4", OrcPose(facing=1, turn=2.6)), ("back", OrcPose(facing=2))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 290, 560, floor=520)
            draw_orc(cr, 145, 532, 1.0, p, neutral, t=0.4)
        add(label, 290, 560, fn, "turnaround")
    for tv in (-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4, 3.6):
        def fn(cr, tv=tv):
            F.sheet_bg(cr, 210, 300, floor=272)
            draw_orc(cr, 105, 284, 0.52, OrcPose(facing=0, turn=tv), neutral, t=0.4 + 0.3 * tv)
        add(f"turn {tv:+.1f}", 210, 300, fn, "turnaround")

    # ---- faces
    moods = [("neutral", dict()), ("angry", dict(mood="angry")), ("angry + snarl", dict(mood="angry", snarl=1.0)),
             ("sad (stops)", dict(mood="sad")), ("kind", dict(mood="kind")), ("worried", dict(mood="worried")),
             ("surprised", dict(mood="surprised")), ("happy", dict(mood="happy")), ("talk", dict(mood="neutral", talk=0.8)),
             ("shout", dict(mood="angry", talk=1.0)), ("eyes closed (hug)", dict(mood="kind", blink=1.0)),
             ("laugh", dict(laugh=1.0)), ("front: angry", dict(mood="angry", facing=0)),
             ("front: kind", dict(mood="kind", facing=0)), ("3/4 left: sad", dict(mood="sad", facing=-1)),
             ("profile: angry", dict(mood="angry", facing=1, turn=0.75))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        turn = kw.pop("turn", -0.3 if facing == 1 else (0.3 if facing == -1 else 0.0))
        pose = OrcPose(facing=facing, turn=turn, **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 220, 220)
            s0, c0 = core.frame(4, 4)
            r0 = draw_orc(c0, 0.0, 0.0, 1.5, p, neutral, t=0.4)
            draw_orc(cr, 110 - r0.head[0], 122 - r0.head[1], 1.5, p, neutral, t=0.4)
        add(label, 220, 220, fn, "faces")

    # ---- fight beats (S5) one by one
    beats = [("guard (squared up)", OrcPose(facing=1, mood="angry", snarl=0.6, stance=0.6, hunch=0.7, near=Arm("guard"), far=Arm("guard"))),
             ("shove: wind-up", OrcPose(facing=1, mood="angry", snarl=0.8, stance=0.6, hunch=0.7, near=Arm("shove", phase=0.3), far=Arm("shove", phase=0.3))),
             ("shove: thrust", OrcPose(facing=1, mood="angry", snarl=1.0, stance=0.6, hunch=0.7, lean=0.4, near=Arm("shove", phase=0.5), far=Arm("shove", phase=0.5))),
             ("shoved: stagger", OrcPose(facing=1, mood="surprised", stance=0.3, lean=-0.5, near=Arm("stagger", phase=0.2), far=Arm("stagger", phase=0.6))),
             ("stops: arms drop", OrcPose(facing=1, mood="sad", hunch=0.85, head_nod=-0.3, look=(0.0, 0.5), near=Arm("slump"), far=Arm("slump"))),
             ("hug (arms only)", OrcPose(facing=1, mood="kind", blink=1.0, head_tilt=0.22, lean=0.38, near=Arm("hug"), far=Arm("hug"))),
             ("walk 0.0", OrcPose(facing=1, walk=1.0, phase=0.0, mood="angry")),
             ("walk 0.5", OrcPose(facing=1, walk=1.0, phase=0.5, mood="angry")),
             ("cheer", OrcPose(facing=0, turn=0.3, mood="happy", near=Arm("cheer"), far=Arm("rest"))),
             ("sit (bench)", OrcPose(facing=1, turn=-0.3, sit=1.0, mood="kind", near=Arm("knees"), far=Arm("knees")))]
    for label, pose in beats:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 300, 440, floor=412)
            if p.sit > 0.5:
                F.sheet_bench(cr, 150, 424, 0.72)
            draw_orc(cr, 140, 424, 0.72, p, neutral, t=0.4)
        add(label, 300, 440, fn, "fight beats")
    # ---- the whole S5 beat with the minotaur (draw_brawl): fight -> stop -> hug -> hug back
    for tt in (1.2, 3.0, 8.8, 10.4, 12.0, 13.5, 16.0, 24.0):
        def fn(cr, tt=tt):
            F.sheet_bg(cr, 440, 450, "square", floor=424)
            draw_brawl(cr, 220, 436, 0.6, L["square"], tt)
        add(f"draw_brawl t={tt:.1f}", 440, 450, fn, "S5: fight -> hug (draw_brawl)")

    # ---- lights + film scale
    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 210, 440, name, floor=412)
            draw_orc(cr, 105, 424, 0.72, OrcPose(facing=1, turn=-0.25, mood="angry" if name == "square" else "neutral"), L[name], t=0.4)
        add(name, 210, 440, fn, "lights & film scale")
    for label, h in (("450 px", 450.0), ("300 px", 300.0), ("200 px", 200.0)):
        sc = h / ORC_HEIGHT

        def fn(cr, sc=sc):
            F.sheet_bg(cr, 240, 500, "square", floor=470)
            draw_orc(cr, 120, 482, sc, OrcPose(facing=1, mood="angry", snarl=0.5, near=Arm("guard"), far=Arm("guard")), L["square"], t=0.4)
        add(label, 240, 500, fn, "lights & film scale")
    return items
