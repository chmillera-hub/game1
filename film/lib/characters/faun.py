"""faun.py -- THE TEEN FAUN (S7): walks past, slows down, watches, hesitates, sits, takes bread.

A gangly teenage faun: fawn fur, a soft goat muzzle with a dark nose and a wisp of a first
goatee, big curious eyes, long goat ears sticking out sideways, two little horns, a messy dark
fringe. He wears a red wool chaperon -- hood up, its short capelet over his shoulders (his
signature accent; ears and horns poke through) -- over a faded, patched sage tunic whose sleeves
he has outgrown, a brown leather satchel on a strap across his chest, and a little wooden
reed-pipe on a cord round his neck. Goat legs: shaggy thighs, backward hocks, small cloven
hooves. Silhouette: a tall thin stalk with a pointed hood, bent-back legs, slouched.

    from film.lib import characters as ch
    p = ch.FaunPose(facing=-1, walk=1.0, phase=ch.faun_walk_phase(x - x0, sc), look=(-0.6, 0.1),
                    head_turn=-0.4, near=ch.Arm("strap"))
    rig = ch.draw_faun(cr, x, ground_y, 0.9, p, ch.LIGHTS["golden"], t)

Scale 1.0: standing, ground -> horn tips = FAUN_HEIGHT = 410 px (hood point excluded).
Anchor (x, y) = ground point below the pelvis (below the seat when sitting). Seated on the
standard bench (125) his knees ride high: his legs are long for it.
"""

import math
from dataclasses import dataclass

from .. import core
from ..core import clamp, lerp
from . import base as B
from . import _folk as F
from .base import Mat, Path, m_vec, v_add, v_lerp
from .dragon import Arm

__all__ = ["FaunPose", "FaunRig", "draw_faun", "faun_walk_phase", "FAUN_HEIGHT", "FAUN_COLORS",
           "FAUN_GESTURES", "faun_mats"]

FAUN_HEIGHT = 410.0
HS = 1.25
TAU = math.tau

FAUN_COLORS = {
    "fur": "#B98B5E",        # fawn
    "fur_dk": "#8E6542",
    "muzzle": "#EAD6B6",
    "nose": "#4A3430",
    "hair": "#5E4130",       # fringe, goatee, tufts
    "horn": "#D8CCB2",
    "hoof": "#3A302A",
    "hood": "#B53D30",       # red wool chaperon -- the signature accent
    "hood_in": "#6E2620",
    "tunic": "#7D8658",      # faded sage
    "patch1": "#8A6A48",
    "patch2": "#5C7088",
    "satchel": "#7A5434",
    "strap": "#5E4028",
    "pipe": "#C49A62",       # the wooden reed-pipe
    "cord": "#5A4632",
    "inner_ear": "#D9A08E",
    "eye": "#6E8A4A",        # hazel-green
    "eye_hi": "#B8D080",
    "mouth": "#4A2228",
    "tongue": "#C4566A",
}

FAUN_BUILD = F.Build(
    pelvis_h=196.0, hip_w=20.0, thigh=70.0, shin=72.0, ankle_h=14.0, cannon=56.0, cannon_tilt=0.3,
    sh_y=118.0, sh_z=0.0, sh_w=40.0, upper_arm=78.0, forearm=74.0, hand_len=52.0,
    neck_y=132.0, neck_z=4.0, neck_len=26.0, head_up=14.0, head_fwd=8.0,
    hunch=0.55, hunch_fwd=16.0, stride=168.0, lift=22.0, bob=5.0, breath=0.25,
    sit_drop=12.0, sit_back=8.0, sway=2.0, knee_out=0.25,
    fit=0.969)   # scale 1.0 -> base.CAST_HEIGHTS (measured on the lineup)

_MATS = {}


def faun_mats():
    if not _MATS:
        C = FAUN_COLORS
        _MATS.update({
            "fur": Mat.of(C["fur"], sss=0.3),
            "fur_dk": Mat.of(C["fur_dk"], sss=0.2),
            "muzzle": Mat.of(C["muzzle"], sss=0.4, shadow_k=1.1),
            "hair": Mat.of(C["hair"], sheen=0.2),
            "horn": Mat.of(C["horn"], sheen=0.5, line_k=0.45),
            "hoof": Mat.of(C["hoof"], sheen=0.4),
            "hood": Mat.of(C["hood"], shadow_k=1.1, line_k=0.5),
            "hood_in": Mat.of(C["hood_in"]),
            "tunic": Mat.of(C["tunic"], shadow_k=1.1),
            "patch1": Mat.of(C["patch1"]),
            "patch2": Mat.of(C["patch2"]),
            "satchel": Mat.of(C["satchel"], sheen=0.3),
            "strap": Mat.of(C["strap"], sheen=0.2),
            "pipe": Mat.of(C["pipe"], sheen=0.4),
            "inner_ear": Mat.of(C["inner_ear"], sss=0.5),
        })
    return _MATS


@dataclass
class FaunPose(F.FolkPose):
    """FolkPose (see _folk.FolkPose / DragonPose) plus:
    hood     1 hood up (default) .. 0 pushed back (down round his neck); >= 0.5 draws it up
    ears     -1 drooped .. +1 perked (added to the mood's ear set)
    """
    mood: object = "neutral"
    hunch: float = None
    hood: float = 1.0
    ears: float = 0.0


FaunRig = F.FolkRig


def _g_neck_rub(q, sk, side, arm):
    """Awkward: a hand rubbing the back of his neck (hesitating). phase rubs it."""
    nb = q.S["neck_base"]
    w = 4.0 * math.sin(arm.phase * TAU * 2.0)
    return F.G(v_add(nb, (side * (12.0 + w), -14.0, -16.0)), "relaxed", -0.4, "auto", (side * 1.0, -0.6, 0.4), "fwd")


def _g_pipe(q, sk, side, arm):
    """Fiddling with the reed-pipe on its cord at his chest."""
    ch_ = q.S["chest"]
    return F.G(v_add(ch_, (side * 10.0, -6.0, 34.0)), "pinch", -1.2, "front", (side * 1.0, 1.0, -0.2), "in")


FAUN_GESTURES = dict(F.GESTURES)
FAUN_GESTURES.update({"neck_rub": _g_neck_rub, "pipe": _g_pipe})


def faun_walk_phase(distance_px, scale=1.0, yaw=1.0):
    return F.walk_phase(FAUN_BUILD, distance_px, scale, yaw)


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_faun(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the teen faun with its anchor at (x, y). Returns a FaunRig (points: "pipe",
    "satchel"). parts: None = everything, or a subset of ("back", "body", "mid", "head", "front")."""
    pose = pose or FaunPose()
    q = F.begin(cr, x, y, scale, pose, light, t, detail, FAUN_BUILD, faun_mats(), parts, height=FAUN_HEIGHT)
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far, FAUN_GESTURES) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    pts = {}
    if q.want("body") and pose.shadow:
        F.contact(q, 52.0)
    for s in (q.far, q.near):
        if lay[s] == "back" and q.want("back"):
            hands[s] = _arm(q, A[s])
    if q.want("body"):
        sat_side = -1.0                                  # satchel on his right hip
        sat_front = q.proj.depth((sat_side, 0.0, 0.25)) > -0.15
        if not sat_front:
            pts["satchel"] = _satchel(q, sat_side)
        _legs(q)
        _torso(q)
        if sat_front:
            pts["satchel"] = _satchel(q, sat_side)
        pts["pipe"] = _capelet_and_pipe(q)
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
    rig.points.update({k: v for k, v in pts.items() if v is not None})
    return F.end(q, rig)


def _hand_guess(q, A):
    el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    d = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    return B.HandFrame(wr[0] + d[0] * 24, wr[1] + d[1] * 24, math.atan2(d[1], d[0]), 1.0, [], wr, False)


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _legs(q):
    """Goat legs (both in one union): shaggy thighs, backward hocks, cloven hooves."""
    cr = q.cr
    shp, pal, spines = F.digi_legs(q, (25.0, 17.0, 8.0, 6.5), q.M["fur"], 34.0)
    if q.detail >= 1:                       # shaggy fur tufts behind the thigh and at the hock
        lines = []
        for sp in spines:
            hip, kn, hk, ft = sp
            ux, uy = core.normalize((kn[0] - hip[0], kn[1] - hip[1]))
            nx, ny = -uy, ux
            bx = -1.0 if q.proj.xy((0.0, 0.0, 1.0))[0] > q.proj.xy((0.0, 0.0, 0.0))[0] else 1.0
            if nx * bx < 0:
                nx, ny = -nx, -ny
            for k in range(3):
                m = core.lerp_pt(hip, kn, 0.45 + 0.2 * k)
                r = lerp(25.0, 17.0, 0.45 + 0.2 * k)
                lines.append([(m[0] + nx * (r - 4), m[1] + ny * (r - 4)), (m[0] + nx * (r + 3) + ux * 8, m[1] + ny * (r + 3) + uy * 8)])
            lines.append([(kn[0] + nx * 12, kn[1] + ny * 12), (kn[0] + nx * 18 + ux * 9, kn[1] + ny * 18 + uy * 9)])
        B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.55, taper=(0.9, 1.0, 0.1))
    if q.detail >= 1:                       # darker goat "socks" from the hock down
        for sp in spines:
            F.band(q, shp, core.lerp_pt(sp[1], sp[2], 0.82), sp[3], 10.0, q.M["fur_dk"], 14.0, seams=False)
    groups = []
    for f in q.S["feet"]:
        g = f["ground"]
        groups.append(F.blob_pts(q.proj, (g[0], g[1] - 7.0, g[2] + 4.0), 8.0, 7.0, 11.0, 12)
                      + F.blob_pts(q.proj, (g[0], g[1] - 2.0, g[2] + 6.0), 9.0, 2.0, 12.0, 12))
    hp = F.hull_union(q, groups, q.M["hoof"], 16.0, rim=0.5)[1]
    if q.detail >= 1 and q.proj.depth((0.0, 0.0, 1.0)) > 0.25:
        lines = [[q.proj.xy((f["ground"][0], f["ground"][1] - 8.0, f["ground"][2] + 10.0)),
                  q.proj.xy((f["ground"][0], f["ground"][1] - 1.0, f["ground"][2] + 16.0))] for f in q.S["feet"]]
        B.detail_lines(cr, lines, q.lw * 0.9, core.tint(hp.lit, 0.3), 0.7)


def _torso(q):
    """The faded, patched sage tunic (to mid-thigh) and its rope belt."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    T = S["T"]
    br, h = S["br"], S["hunch"]
    sit = q.sit
    pel = S["pelvis"]
    walk = S["walk"]
    sw = walk * math.sin(TAU * S["wc"].phase * 2)
    kn = v_lerp(S["knee"][0], S["knee"][1], 0.5)
    hem_c = v_lerp(v_add(pel, (sw * 3.0, 30.0, 2.0 - walk * 6.0)), v_add(v_lerp(pel, kn, 0.55), (0.0, 12.0, 2.0)), clamp(sit / 0.7))
    rings = [
        (T((0.0, -116.0 + 6 * h, 6.0 + 8 * h)), 34.0, 26.0),        # 0 over the shoulders
        (T((0.0, -100.0 + 4 * h, 3.0)), 47.0 + br * 0.6, 30.0),     # 1 shoulders
        (T((0.0, -76.0, 6.0)), 41.0 + br * 0.6, 30.0),              # 2 chest
        (T((0.0, -44.0, 4.0)), 35.0, 27.0),                         # 3 waist
        (v_add(pel, (0.0, 2.0, 0.0)), 39.0, 29.0),                  # 4 hips
        (hem_c, 46.0 + 8 * sit, 33.0),                              # 5 hem
    ]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=14.0)
    hem = F.hem_curve(q, *rings[-1], n=8, wave=1.6, phase=q.t * 1.4 + walk * S["wc"].phase * 6)
    shp, pal = F.smooth_shape(q, left + hem + right[::-1] + top, M["tunic"], 70.0, shadow=0.6)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        # two patches sewn on: one on his belly, one near the hem (only where they face us)
        for (phi, yk, w, hh, mat) in ((0.45, 0.62, 15.0, 13.0, M["patch1"]), (-0.6, 0.9, 13.0, 11.0, M["patch2"])):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.2:
                continue
            c3, a3, z3 = rings[3] if yk < 0.8 else rings[4]
            c5, a5, z5 = rings[5]
            cc = v_lerp(c3, c5, yk - 0.4)
            aa, zz = lerp(a3, a5, yk - 0.4), lerp(z3, z5, yk - 0.4)
            quad = []
            for (dp, dy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                ph = phi + dp * w / max(aa, 1.0)
                quad.append(proj.xy((cc[0] + math.sin(ph) * aa * 1.01, cc[1] + dy * hh, cc[2] + math.cos(ph) * zz * 1.01)))
            pp = q.P(mat)
            cr.new_path()
            core.polygon(cr, quad)
            core.src(cr, core.mix(pp.lit, pp.shadow, 0.25))
            cr.fill()
            if q.detail >= 2:                # running stitches round it
                cr.new_path()
                core.polygon(cr, quad)
                cr.set_dash([3.0, 3.0])
                cr.set_line_width(q.lw * 0.6)
                core.src(cr, pp.line, 0.8)
                cr.stroke()
                cr.set_dash([])
            B.detail_lines(cr, [quad + [quad[0]]], q.lw * 0.7, pp.line, 0.6, taper=(1.0, 1.0, 1.0))
        lines = []
        c4, a4, z4 = rings[4]
        c5, a5, z5 = rings[5]
        for phi in (-0.9, -0.2, 0.55, 1.1):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.15:
                continue
            p0 = proj.xy(v_add(c4, (math.sin(phi) * a4 * 0.95, 10.0, math.cos(phi) * z4 * 0.95)))
            p1 = proj.xy(v_add(c5, (math.sin(phi * 1.1) * a5 * 0.97, -2.0, math.cos(phi) * z5 * 0.97)))
            lines.append([p0, p1])
        if lines:
            B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.45, taper=(0.05, 0.9, 0.4))
        cr.restore()
    c3, a3, z3 = rings[3]
    c4, a4, z4 = rings[4]
    F.belt(q, v_lerp(c3, c4, 0.6), lerp(a3, a4, 0.6) + 2.0, lerp(z3, z4, 0.6) + 2.0, 4.0, M["strap"])


def _strap_pts(q):
    """The satchel strap: from his left shoulder across the chest to his right hip (3D)."""
    S = q.S
    T = S["T"]
    return [T((30.0, -108.0, 8.0)), T((14.0, -84.0, 30.0)), T((-18.0, -48.0, 28.0)), T((-38.0, -12.0, 12.0))]


def _satchel(q, side):
    """A brown leather satchel at his right hip: body, flap, a brass stud. Returns its centre."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    pel = S["pelvis"]
    sw = 3.0 * math.sin(q.t * 1.3 + 0.7) + S["walk"] * 6.0 * math.sin(TAU * S["wc"].phase * 2 + 1.0)
    c = v_add(pel, (side * 44.0, 4.0, 8.0 + sw * 0.3))
    pts = F.blob_pts(proj, v_add(c, (0.0, -10.0, 0.0)), 8.0, 4.0, 22.0, 10) + F.blob_pts(proj, v_add(c, (side * 2.0, 18.0, 0.0)), 9.0, 6.0, 24.0, 10)
    shp, pal = F.hull_union(q, [pts], M["satchel"], 30.0, rim=0.4)
    if q.detail >= 1:                       # the flap edge + a brass stud
        a, b_ = proj.xy(v_add(c, (side * 9.0, 2.0, -20.0))), proj.xy(v_add(c, (side * 9.0, 2.0, 20.0)))
        mid = proj.xy(v_add(c, (side * 10.0, 8.0, 0.0)))
        B.detail_lines(cr, [[a, mid, b_]], q.lw * 1.0, pal.line, 0.85)
        st = proj.xy(v_add(c, (side * 10.0, 8.0, 0.0)))
        core.src(cr, B.pal(q.light, "#C9A04A", sheen=0.8).lit)
        core.circle(cr, st[0], st[1], 2.6)
        cr.fill()
    return proj.xy(c)


def _capelet_and_pipe(q):
    """The strap across the chest, the reed-pipe on its cord, and the chaperon's capelet over
    the shoulders (hood down: a bunched red roll instead). Returns the pipe's 2D centre."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    nb = S["neck_base"]
    R = S["R"]
    front = proj.depth((0.0, 0.0, 1.0))
    # strap (front or back of the torso, same path)
    sp = [proj.xy(p) for p in _strap_pts(q)]
    shp, so = B.taper_paths(cr, sp, 9.0, 9.0, q.lw * 0.8, cap=False)
    q.shade(shp, M["strap"], lw=q.lw * 0.8, outline=so, size=8.0, rim=0.0)
    # capelet: a round cape over the shoulders, longer at the back, with a dagged (scalloped)
    # hem -- the chaperon's shoulder piece (with the hood down the hood lies bunched behind)
    sw = B.chain(q.t, 3, freq=0.3, delay=0.15, amp=0.3, seed=q.pose.seed + 6)
    rings = [(v_add(nb, m_vec(R, (0.0, -8.0, 0.0))), 22.0, 19.0), (v_add(nb, m_vec(R, (0.0, 12.0, -2.0))), 50.0, 36.0),
             (v_add(nb, m_vec(R, (sw[0] * 3.0, 40.0, -3.0))), 58.0, 42.0)]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=12.0)
    hem = F.hem_curve(q, *rings[-1], n=13 if q.detail >= 1 else 7)
    if q.detail >= 1:                       # dagging: every other hem point drops into a lobe
        hem = [(x, y + (9.0 if i % 2 else 0.0)) for i, (x, y) in enumerate(hem)]
    lw = q.lw
    cape, pal = F.smooth_shape(q, left + hem + right[::-1] + top, M["hood"], 50.0, tension=0.7, shadow=0.7)
    if q.detail >= 1:
        cr.save()
        cape.add(cr)
        cr.clip()
        lines = []
        for k in range(5):
            a = -1.0 + 0.5 * k
            if proj.depth((math.sin(a), 0.0, math.cos(a))) < 0.1:
                continue
            p0 = proj.xy(v_add(nb, m_vec(R, (math.sin(a) * 30.0, 2.0, math.cos(a) * 22.0))))
            p1 = proj.xy(v_add(nb, m_vec(R, (math.sin(a) * 54.0, 36.0, math.cos(a) * 40.0))))
            lines.append([p0, p1])
        B.detail_lines(cr, lines, lw * 0.9, pal.line, 0.45, taper=(0.1, 1.0, 0.3))
        cr.restore()
    pipe = None
    # reed-pipe on its cord, hanging at his chest over the capelet's opening
    if front > -0.1:
        pc = v_add(nb, m_vec(R, (3.0, 50.0, 40.0)))
        sway = 0.08 * math.sin(q.t * 1.7 + 0.4)
        a0 = proj.xy(v_add(pc, m_vec(R, (math.sin(sway) * -20.0, -18.0, 0.0))))
        a1 = proj.xy(v_add(pc, m_vec(R, (math.sin(sway) * 20.0, 18.0, 0.0))))
        cl, cr_ = proj.xy(v_add(nb, m_vec(R, (-14.0, -2.0, 22.0)))), proj.xy(v_add(nb, m_vec(R, (14.0, -2.0, 22.0))))
        B.detail_lines(cr, [[cl, a0], [cr_, a0]], lw * 0.7, FAUN_COLORS["cord"], 0.9, taper=(1.0, 1.0, 1.0))
        ps, pso = B.taper_paths(cr, [a0, a1], 8.0, 6.0, lw * 0.8)
        ppal = q.shade(ps, M["pipe"], lw=lw * 0.8, outline=pso, size=7.0, rim=0.3)
        if q.detail >= 1:                   # finger holes
            core.src(cr, ppal.line)
            for k in range(3):
                h = core.lerp_pt(a0, a1, 0.35 + 0.18 * k)
                core.circle(cr, h[0], h[1], 1.3)
            cr.fill()
        pipe = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
    return pipe


def _arm(q, A):
    """Outgrown tunic sleeve (his furry wrists show) and a hand."""
    M, proj = q.M, q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    F.limb(q, [sh, el, wr], [13.0, 9.5, 7.5], M["fur"], 18.0)
    cut = core.lerp_pt(el, wr, 0.78)
    sl, spal = F.limb(q, [sh, el, cut], [15.5, 13.0, 12.5], M["tunic"], 26.0)
    if q.detail >= 2:
        F.elbow_folds(q, sh, el, cut, 12.0, spal, 0.4)
    return F.hand(q, A, M["fur"], size=52.0, finger_w=1.0, palm_w=0.95, finger_len=1.05,
                  pad=FAUN_COLORS["muzzle"])


# ----------------------------------------------------------------------------------------
# head (head space x HS)
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


def _ears(q, P, e, sides, nz):
    """Long goat ears sticking out sideways (through slits in the hood), floppy: they droop
    when he is unsure, lift when he is curious."""
    if not sides:
        return
    cr, t = q.cr, q.t
    perk = clamp(0.5 + 0.5 * (e.brow_y + 0.4 * e.smile - 0.6 * max(0.0, e.lid_tilt)) + 0.4 * q.pose.ears, 0.0, 1.0)
    lwf = q.lw * 0.9
    outs, shapes, inners = [], [], []
    for s in sides:
        tw = 0.08 * math.sin(t * 1.4 + s * 1.9) + 0.12 * B.wobble(t, math.floor(t / 3.5) * 3.5 + 1.0 + s * 0.3, 5.0, 6.0)
        drop = lerp(16.0, -8.0, perk) + tw * 16.0
        tip = (s * 64.0, 6.0 + drop, -4.0)
        pts = [P((s * 28.0, -10.0, -2.0)), P((s * 46.0, -6.0 + drop * 0.45, -4.0)), P(tip),
               P((s * 47.0, 9.0 + drop * 0.5, -4.0)), P((s * 28.0, 6.0, -4.0))]
        sh, so = B.smooth_paths(cr, pts, lwf, 0.85)
        shapes.append(sh)
        outs.append(so)
        if nz((s * 0.3, 0.0, 0.9)) > -0.2:
            inners.append([P((s * 31.0, -5.0, -1.0)), P((s * 46.0, -2.0 + drop * 0.45, -3.0)), P(v_lerp(tip, (s * 46.0, 2.0, -4.0), 0.3)),
                           P((s * 46.0, 5.0 + drop * 0.45, -3.0)), P((s * 31.0, 3.0, -2.0))])
    pal = q.P(q.M["fur"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["fur"], lw=lwf, outline=False, size=16.0, rim=0.6)
    if q.detail >= 1 and inners:
        cr.new_path()
        for inner in inners:
            core.smooth_closed(cr, inner, 0.85)
        core.src(cr, q.P(q.M["inner_ear"]).lit)
        cr.fill()


def _horns(q, P, sides):
    """Two little goat horns curving back over his head (through the hood)."""
    if not sides:
        return
    cr = q.cr
    lwh = q.lw * 0.85
    outs, shapes, spines = [], [], []
    for s in sides:
        sp = [P((s * 10.0, -32.0, 4.0)), P((s * 12.5, -44.0, -2.0)), P((s * 13.0, -49.0, -11.0)), P((s * 12.0, -48.0, -19.0))]
        sh, so = B.taper_paths(cr, sp, 8.5 * HS, 2.2, lwh)
        shapes.append(sh)
        outs.append(so)
        spines.append(sp)
    pal = q.P(q.M["horn"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["horn"], lw=lwh, outline=False, size=9.0, rim=0.8)
    if q.detail >= 2:
        lines = []
        for sp in spines:
            for k in (0.3, 0.55):
                a = core.lerp_pt(sp[0], sp[1], k * 2) if k < 0.5 else core.lerp_pt(sp[1], sp[2], (k - 0.5) * 2)
                lines.append([(a[0] - 4, a[1] + 1), (a[0] + 4, a[1] - 1)])
        B.detail_lines(cr, lines, q.lw * 0.6, pal.line, 0.5)


def _head(q, draw=True):
    cr, M, pose, S, proj = q.cr, q.M, q.pose, q.S, q.proj
    e = F.expr_of(pose)
    P, nz, D, W = F.head_xf(q, HS)
    hyaw = S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    jaw_open = clamp(talk * 0.85 + e.open * 0.9)
    ja = jaw_open * 0.32
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):
        y, z = v[1] - 10.0, v[2]
        return (v[0], 10.0 + y * cj + z * sj, -y * sj + z * cj)

    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P(J((0.0, 22.0, 32.0))), "nose": P((0.0, 9.0, 40.0)),
           "eyes": [P((s * 15.0, -8.0, 24.0)) for s in (far, near)], "top": P((0.0, -44.0, -4.0))}
    if not draw:
        return pts
    lw = q.lw
    pal = q.P(M["fur"])
    hood_up = pose.hood >= 0.5
    facing_away = nz((0.0, 0.1, 1.0)) < -0.2
    side_behind = {s: D((s * 30.0, -4.0, -4.0)) < D((0.0, -4.0, -4.0)) - 3.0 for s in (-1.0, 1.0)}
    # back pieces first (anything between the face and the hood would show through its opening)
    _ears(q, P, e, [s for s in (-1.0, 1.0) if side_behind[s]], nz)
    if hood_up:
        _liripipe(q, P, W, D, behind=True)
    else:
        _horns(q, P, [s for s in (-1.0, 1.0) if side_behind[s]])
    # ---- the skull: neck + cranium + cheeks, one union
    nb, nt = S["neck_base"], S["neck_top"]
    groups = (F.blob_pts(proj, nb, 13.0, 8.0, 12.0) + F.blob_pts(proj, nt, 12.0, 8.0, 11.0),
              _bp(P, (0.0, -14.0, -4.0), 30.0, 28.0, 30.0, 16), _bp(P, (0.0, 4.0, 6.0), 28.0, 18.0, 22.0))
    if hood_up and not facing_away:         # the hood's dark inside, seen round the face
        face = _bp(P, (0.0, -1.0, 22.0), 34.0, 38.0, 15.0, 16)
        cr.new_path()
        core.smooth_closed(cr, face, 0.9)
        core.src(cr, q.P(M["hood_in"]).shadow)
        cr.fill()
    skull, _sp = F.hull_union(q, groups, M["fur"], 70.0)
    hole = None
    if hood_up:                             # the hood over the skull, the face showing through
        hole = _hood(q, P, nz, facing_away)
    if not facing_away:
        # eyes + brows (inside the hood's opening: clipped to it)
        if hole is not None:
            cr.save()
            cr.new_path()
            core.smooth_closed(cr, hole, 0.9)
            cr.clip()
        eyes = []
        for s in (far, near):
            ec = F.eye_at(q, P, nz, s, e, (s * 15.0, -8.0, 24.0), 11.0 * HS, 13.0 * HS, iris=FAUN_COLORS["eye"],
                          iris_hi=FAUN_COLORS["eye_hi"], skin=FAUN_COLORS["fur"], pupil="#1d120c",
                          crease=0.2 if q.detail >= 2 else 0.0, line=pal.line, normal=(s * 0.45, -0.1, 0.88))
            eyes.append(ec or P((s * 15.0, -8.0, 24.0)))
        pts["eyes"] = eyes
        _brows(q, P, nz, e, near, [skull])
        if hole is not None:
            cr.restore()
        # the pale goat muzzle + chin: protrudes from the hood, so drawn over it
        mz = [_bp(P, (0.0, 13.0, 27.0), 16.0, 12.0, 15.0), F.ellipsoid2d(lambda v: P(J(v)), (0.0, 21.0, 18.0), 15.0, 8.0, 16.0)]
        _msh, mpal = F.hull_union(q, mz, M["muzzle"], 26.0, rim=0.3)
        if jaw_open > 0.04 and nz((0.0, 0.4, 0.9)) > -0.1:
            # the open mouth at the front of the muzzle, between the lip and the dropped chin
            ip = [P((sd * 10.0, 17.0, z)) for sd in (-1.0, 1.0) for z in (26.0, 36.0)] + [P((0.0, 17.5, 40.0))]
            ip += [P(J((sd * 9.0, 19.0, z))) for sd in (-1.0, 1.0) for z in (26.0, 34.0)] + [P(J((0.0, 20.0, 37.0)))]
            mh = core.convex_hull(ip)
            cr.new_path()
            core.smooth_closed(cr, B.offset_closed(mh, lw * 0.8), 0.8)
            core.src(cr, mpal.line)
            cr.fill()
            core.smooth_closed(cr, mh, 0.8)
            mp = Path(cr)
            mp.add(cr)
            core.src(cr, B.pal(q.light, FAUN_COLORS["mouth"]).lit)
            cr.fill()
            cr.save()
            mp.add(cr)
            cr.clip()
            tg = P(J((0.0, 20.0, 31.0)))
            core.src(cr, B.pal(q.light, FAUN_COLORS["tongue"], sss=0.4).lit)
            core.ellipse(cr, tg[0], tg[1] + 1.5, 8.0, 2.0 + 3.0 * jaw_open)
            cr.fill()
            cr.restore()
        fz = nz((0.0, 0.1, 1.0))
        if fz > -0.2:                       # dark rounded nose + the split lip line
            n0 = P((0.0, 7.0, 41.0))
            nr = 6.0 * HS
            cr.new_path()
            core.ellipse(cr, n0[0], n0[1], nr * (0.55 + 0.45 * max(0.2, fz)), nr * 0.62)
            core.src(cr, B.pal(q.light, FAUN_COLORS["nose"], sheen=0.5).lit)
            cr.fill()
            if q.detail >= 2:
                B.sheen(cr, n0[0] - 1.5, n0[1] - 2.0, 2.5, 1.5, alpha=0.5)
            sm = e.smile
            lines = [[P((0.0, 11.0, 40.0)), P((0.0, 16.0, 39.0))]]
            if jaw_open < 0.04:
                for s in (-1.0, 1.0):
                    if nz((s * 0.6, 0.3, 0.7)) > -0.1:
                        lines.append([P((0.0, 16.0, 39.0)), P((s * 6.0, 18.0 - sm * 2.0, 37.0)), P((s * 12.0, 17.0 - sm * 5.0, 31.0))])
            B.detail_lines(cr, lines, lw * 1.1, mpal.line, 0.95, taper=(0.6, 1.0, 0.5))
        _goatee(q, P, J, nz)
    else:
        pts["eyes"] = []
    if hood_up:
        if not facing_away:
            _fringe(q, P, nz, under_hood=True)
        _liripipe(q, P, W, D, behind=False)
    else:
        _fringe(q, P, nz)
    _ears(q, P, e, [s for s in (-1.0, 1.0) if not side_behind[s]], nz)
    _horns(q, P, [s for s in (-1.0, 1.0) if (hood_up or not side_behind[s])])
    return pts


def _brows(q, P, nz, e, near, clip):
    cr = q.cr
    lwb = q.lw * 0.8
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.1:
            continue
        pts = F.brow_pts(P, s, e, near, 5.0, 26.0, -22.0, 30.0, 22.0, 13.0, 11.0)
        sh, so = B.taper_paths(cr, pts, 7.0, 3.0, lwb)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    cr.save()
    for pth in clip:
        pth.add(cr)
    cr.clip()
    B.fill_outlines(cr, outs, q.P(q.M["hair"]).line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["hair"], lw=lwb, outline=False, size=6.0, rim=0.0)
    cr.restore()


def _goatee(q, P, J, nz):
    """A teenager's first wisp of a goatee under the chin (it rides the jaw)."""
    if nz((0.0, 0.6, 0.6)) < -0.3:
        return
    sw = 1.5 * math.sin(q.t * 1.5 + 0.3)
    sp = [P(J((0.0, 27.0, 24.0))), P(J((sw * 0.3, 33.0, 22.0))), P(J((sw, 38.0, 18.0)))]
    shp, so = B.taper_paths(q.cr, sp, 7.0, 1.5, q.lw * 0.8)
    q.shade(shp, q.M["hair"], lw=q.lw * 0.8, outline=so, size=6.0, rim=0.0)


def _fringe(q, P, nz, under_hood=False):
    """A messy dark fringe swept to one side: one swoop over his brow peeking out of the hood
    (with the hood down, a full mop of hair over the crown)."""
    if nz((0.0, -0.4, 0.9)) < -0.3 and under_hood:
        return
    cr = q.cr
    sw = 1.0 * math.sin(q.t * 1.2 + 0.8)
    if under_hood:
        spec = (((-17.0, -31.0, 25.0), (-2.0, -27.0, 31.0), (15.0, -21.0, 28.0), 13.0),
                ((-6.0, -32.0, 27.0), (6.0, -27.0, 31.0), (19.0, -24.0, 26.0), 9.0))
    else:
        spec = (((-26.0, -30.0, 8.0), (-14.0, -44.0, 12.0), (8.0, -42.0, 16.0), 22.0),
                ((-18.0, -38.0, 16.0), (0.0, -33.0, 26.0), (17.0, -23.0, 26.0), 15.0),
                ((10.0, -44.0, 8.0), (22.0, -36.0, 10.0), (28.0, -24.0, 8.0), 13.0),
                ((-4.0, -46.0, -8.0), (-6.0, -44.0, -24.0), (-10.0, -34.0, -34.0), 18.0))
    lw = q.lw * 0.85
    outs, shapes = [], []
    for (a, m, b_, w) in spec:
        sp = [P(a), P((m[0] + sw, m[1], m[2])), P((b_[0] + sw * 1.5, b_[1], b_[2]))]
        sh, so = B.taper_paths(cr, sp, w, 2.0, lw)
        shapes.append(sh)
        outs.append(so)
    hp = q.P(q.M["hair"])
    B.fill_outlines(cr, outs, hp.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["hair"], lw=lw, outline=False, size=10.0, rim=0.6)


def _liripipe(q, P, W, D, behind):
    """The hood's long tail (liripipe): from the hood's point it hangs with gravity down his
    back to his shoulder blades, swinging a beat late. Drawn behind the head unless we look at
    his back."""
    is_behind = D((0.0, -24.0, -50.0)) < D((0.0, -24.0, 0.0))
    if is_behind != behind:
        return
    sw = B.chain(q.t, 4, freq=0.33, delay=0.17, amp=0.6, seed=q.pose.seed + 3, grow=2.0)
    top = W((0.0, -28.0, -44.0))
    acc = 0.0
    pts = [q.proj.xy(top)]
    for i in range(1, 5):
        acc += sw[i - 1]
        pts.append(q.proj.xy(v_add(top, (acc * 22.0, 24.0 * i, -9.0 * i + 1.6 * i * i))))
    shp, so = B.taper_paths(q.cr, pts, 30.0, 7.0, q.lw)
    q.shade(shp, q.M["hood"], outline=so, size=16.0, rim=0.7)


def _hood(q, P, nz, facing_away):
    """The red wool hood, up: one shape over the skull with the face opening cut out of it
    (a reversed inner contour = a hole, with its own rim line), a short liripipe point at the
    back that swings a beat late."""
    cr, lw = q.cr, q.lw
    sw = B.chain(q.t, 3, freq=0.33, delay=0.16, amp=0.5, seed=q.pose.seed + 3)
    shell = (_bp(P, (0.0, -12.0, -6.0), 39.0, 38.0, 39.0, 18) + _bp(P, (0.0, 12.0, -10.0), 30.0, 20.0, 26.0, 12)
             + [P((sw[0] * 6.0, -30.0, -52.0))])
    outer = core.convex_hull(shell)
    hole = None
    fz = nz((0.0, 0.0, 1.0))
    if not facing_away and fz > 0.05:
        hole = F.clamp_into(outer, _bp(P, (0.0, 0.0, 24.0), 30.0, 34.0, 14.0, 16), 0.94)
        if F.area2(hole) * F.area2(outer) > 0:
            hole = hole[::-1]
    pal = q.P(q.M["hood"])
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(outer, lw), 0.85)
    if hole:
        core.smooth_closed(cr, B.offset_closed(hole, -lw), 0.9)
    core.src(cr, pal.line)
    cr.fill()
    core.smooth_closed(cr, outer, 0.85)
    if hole:
        core.smooth_closed(cr, hole, 0.9)
    hood = Path(cr)
    q.shade(hood, q.M["hood"], outline=False, size=60.0, shadow=0.75)
    ret = hole
    if q.detail >= 1:                       # a seam over the crown + soft folds at the back
        lines = [[P((0.0, -48.0, 10.0)), P((0.0, -50.0, -10.0)), P((0.0, -42.0, -30.0))]]
        if q.detail >= 2:
            lines += [[P((-24.0, -30.0, -26.0)), P((-20.0, -10.0, -34.0))], [P((24.0, -30.0, -26.0)), P((20.0, -10.0, -34.0))]]
        cr.save()
        hood.add(cr)
        cr.clip()
        B.detail_lines(cr, lines, lw * 0.9, pal.line, 0.45, taper=(0.1, 1.0, 0.2))
        cr.restore()
    return ret


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def _sheet_bread(cr, frame):
    """Placeholder bread chunk (the props kit draws the real one)."""
    cr.save()
    cr.rotate(-frame.angle)
    core.src(cr, "#7a4a22")
    core.ellipse(cr, 0, -4, 17, 12)
    cr.fill()
    core.src(cr, "#c88a48")
    core.ellipse(cr, 0, -6, 15, 10)
    cr.fill()
    core.src(cr, "#f3e2bd")
    core.ellipse(cr, 5, -3, 7, 6)
    cr.fill()
    cr.restore()


def lineup():
    return [B.LineupItem("faun", lambda cr, x, y, sc: draw_faun(cr, x, y, sc, FaunPose(facing=1), t=0.4), 170.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    for label, pose in (("3/4 left", FaunPose(facing=-1)), ("front", FaunPose(facing=0)),
                        ("3/4 right", FaunPose(facing=1)), ("profile", FaunPose(facing=1, turn=0.75)),
                        ("back 3/4", FaunPose(facing=1, turn=2.6)), ("hood down", FaunPose(facing=1, hood=0.0, mood="happy")),
                        ("back, hood down", FaunPose(facing=2, hood=0.0))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 250, 500, floor=468)
            draw_faun(cr, 125, 480, 1.0, p, neutral, t=0.4)
        add(label, 250, 500, fn, "turnaround")
    for tv in (-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4, 3.6):
        def fn(cr, tv=tv):
            F.sheet_bg(cr, 200, 300, floor=272)
            draw_faun(cr, 100, 284, 0.62, FaunPose(facing=0, turn=tv), neutral, t=0.4 + 0.3 * tv)
        add(f"turn {tv:+.1f}", 200, 300, fn, "turnaround")

    moods = [("neutral", dict()), ("curious (watching)", dict(mood="raised", look=(0.6, 0.0))),
             ("unsure", dict(mood="worried", look=(0.3, 0.4))), ("bored", dict(mood="bored")),
             ("shy smile", dict(mood="warm", look=(0.4, 0.3))), ("happy", dict(mood="happy")),
             ("talk", dict(talk=0.8)), ("surprised", dict(mood="surprised")), ("laugh", dict(laugh=1.0)),
             ("blink", dict(blink=1.0)), ("front", dict(facing=0, mood="raised")), ("front: shy smile", dict(facing=0, mood="warm")),
             ("3/4 left", dict(facing=-1, mood="worried")), ("hood down: happy", dict(hood=0.0, mood="happy")),
             ("hood down: front", dict(hood=0.0, facing=0, mood="kind"))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        pose = FaunPose(facing=facing, turn=-0.3 if facing == 1 else (0.3 if facing == -1 else 0.0), **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 220, 220)
            s0, c0 = core.frame(4, 4)
            r0 = draw_faun(c0, 0.0, 0.0, 1.55, p, neutral, t=0.4)
            draw_faun(cr, 110 - r0.head[0], 118 - r0.head[1], 1.55, p, neutral, t=0.4)
        add(label, 220, 220, fn, "faces")

    beats = [("walk 0.00", FaunPose(facing=-1, walk=1.0, phase=0.0, near=Arm("strap"))),
             ("walk 0.25", FaunPose(facing=-1, walk=1.0, phase=0.25, near=Arm("strap"))),
             ("walk 0.50", FaunPose(facing=-1, walk=1.0, phase=0.5, near=Arm("strap"))),
             ("slows, watches", FaunPose(facing=-1, walk=0.5, phase=0.6, head_turn=0.5, look=(0.7, 0.1), mood="raised", near=Arm("strap"))),
             ("hesitates (neck rub)", FaunPose(facing=0, turn=0.5, mood="worried", look=(-0.4, 0.4), near=Arm("neck_rub", phase=0.3), far=Arm("strap"), stance=0.3)),
             ("fiddles with his pipe", FaunPose(facing=0, turn=-0.3, mood="worried", look=(0.2, 0.6), near=Arm("pipe"))),
             ("sits (bench)", FaunPose(facing=1, turn=-0.3, sit=1.0, mood="warm", near=Arm("knees"), far=Arm("knees"))),
             ("takes the bread", FaunPose(facing=1, turn=-0.2, sit=1.0, mood="warm", look=(0.6, 0.3), near=Arm("reach", phase=1.0, hold=_sheet_bread))),
             ("eats, hood back", FaunPose(facing=0, turn=0.3, sit=1.0, hood=0.0, mood="happy", near=Arm("eat", phase=0.85, hold=_sheet_bread)))]
    for label, pose in beats:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 240, 420, floor=392)
            if p.sit > 0.5:
                F.sheet_bench(cr, 120, 404, 0.78, w=210)
            draw_faun(cr, 120, 404, 0.78, p, neutral, t=0.4)
        add(label, 240, 420, fn, "actions (S7)")

    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 200, 420, name, floor=392)
            draw_faun(cr, 100, 404, 0.8, FaunPose(facing=-1, turn=0.25), L[name], t=0.4)
        add(name, 200, 420, fn, "lights & film scale")
    for label, h in (("370 px", 370.0), ("250 px", 250.0), ("180 px", 180.0)):
        sc = h / FAUN_HEIGHT

        def fn(cr, sc=sc):
            F.sheet_bg(cr, 200, 420, "golden", floor=392)
            draw_faun(cr, 100, 404, sc, FaunPose(facing=-1, turn=0.2, mood="raised", near=Arm("strap")), L["golden"], t=0.4)
        add(label, 200, 420, fn, "lights & film scale")
    return items
