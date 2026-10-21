"""minotaur.py -- THE MINOTAUR (S5 fighter, and a tavern regular): shoves, staggers, is hugged,
stands stunned, then slowly hugs back.

A towering bull-headed brawler: chestnut fur, a broad cream muzzle with a dusky nose, a curly
forelock, big crescent horns (ivory, darkening to the tips), floppy ears under them, a grey
wool tunic whose hood is down and bunched round his neck like a cowl (its point hangs down his
back), rolled sleeves over furred forearms, a leather belt, dark breeches with linen leg wraps,
cloven hooves and a tufted tail. Silhouette: a tall barrel crowned by a wide crescent -- a "T".

    from film.lib import characters as ch
    pose = ch.MinotaurPose(facing=-1, mood="angry", near=ch.Arm("shove", phase=u), far=ch.Arm("shove", phase=u))
    rig = ch.draw_minotaur(cr, x, ground_y, 0.7, pose, ch.LIGHTS["square"], t)
    # with the orc, the whole S5 beat (fight -> stop -> hug -> hug back): ch.draw_brawl(...)

Scale 1.0: standing, ground -> horn tips = MINOTAUR_HEIGHT = 600 px (poll ~560, eyes ~520).
Anchor (x, y) = ground point below the pelvis (below the seat when sitting). Built on the
shared part-B biped rig (_folk.py): continuous turn incl. back views, walk, sit, gestures.
`variant` recolours him for the crowd (crowd.py uses it for the tavern minotaur).
"""

import math
from dataclasses import dataclass

from .. import core
from ..core import clamp, lerp
from . import base as B
from . import _folk as F
from .base import Mat, Path, v_add, v_lerp
from .dragon import Arm

__all__ = ["MinotaurPose", "MinotaurRig", "draw_minotaur", "minotaur_walk_phase", "MINOTAUR_HEIGHT",
           "MINOTAUR_COLORS", "MINOTAUR_VARIANTS", "MINOTAUR_GESTURES", "minotaur_mats"]

MINOTAUR_HEIGHT = 600.0
HS = 1.45

MINOTAUR_COLORS = {
    "fur": "#7A5034",        # chestnut
    "fur_dk": "#4E3222",     # forelock, brows, tail tuft
    "muzzle": "#D9C3A1",     # cream
    "nose": "#5C4044",       # dusky nose pad
    "horn": "#E6D7B5",       # ivory ...
    "horn_tip": "#6E5C48",   # ... darkening to the tips
    "tunic": "#7C8087",      # grey wool (the hooded tunic)
    "tunic_dk": "#5E6268",   # hood lining
    "belt": "#4A3424",
    "buckle": "#B8913F",     # brass
    "breeches": "#463A31",
    "wraps": "#9C927E",      # linen leg wraps
    "hoof": "#2E2723",
    "inner_ear": "#C99A8E",
    "eye": "#7E4A2A",
    "eye_hi": "#C98A50",
    "mouth": "#4A2228",
    "tongue": "#B8566A",
}

# recolours for the crowd (fur, muzzle, tunic, horn)
MINOTAUR_VARIANTS = {
    "chestnut": {},
    "black": {"fur": "#3A302C", "fur_dk": "#221B18", "muzzle": "#B9A58E", "tunic": "#6E4A3A", "tunic_dk": "#4E3428"},
    "dun": {"fur": "#A7865E", "fur_dk": "#6E5438", "muzzle": "#E6D6BC", "tunic": "#4F5E4A", "tunic_dk": "#3A4636"},
    "brindle": {"fur": "#6A4A3A", "fur_dk": "#3E2A22", "tunic": "#7A5A3A", "tunic_dk": "#5A402A", "horn": "#D8C8A4"},
}

MINOTAUR_BUILD = F.Build(
    pelvis_h=262.0, hip_w=36.0, thigh=124.0, shin=118.0, ankle_h=26.0,
    sh_y=196.0, sh_z=0.0, sh_w=86.0, upper_arm=112.0, forearm=104.0, hand_len=82.0,
    neck_y=212.0, neck_z=10.0, neck_len=24.0, head_up=18.0, head_fwd=16.0,
    hunch=0.35, hunch_fwd=16.0, stride=204.0, lift=26.0, bob=6.0, breath=0.17,
    sit_drop=18.0, sit_back=12.0, sway=2.5, knee_out=0.2)

_MATS = {}


def minotaur_mats(variant="chestnut"):
    m = _MATS.get(variant)
    if m is None:
        C = dict(MINOTAUR_COLORS)
        C.update(MINOTAUR_VARIANTS.get(variant, {}))
        m = _MATS[variant] = {
            "fur": Mat.of(C["fur"], sss=0.2),
            "fur_dk": Mat.of(C["fur_dk"], sheen=0.2),
            "muzzle": Mat.of(C["muzzle"], sss=0.4, shadow_k=1.1),
            "nose": Mat.of(C["nose"], sheen=0.5),
            "horn": Mat.of(C["horn"], sheen=0.5, line_k=0.45),
            "horn_tip": Mat.of(C["horn_tip"], sheen=0.5),
            "tunic": Mat.of(C["tunic"], shadow_k=1.1),
            "tunic_dk": Mat.of(C["tunic_dk"], shadow_k=1.1),
            "belt": Mat.of(C["belt"], sheen=0.3),
            "buckle": Mat.of(C["buckle"], sheen=0.8),
            "breeches": Mat.of(C["breeches"], shadow_k=1.1),
            "wraps": Mat.of(C["wraps"]),
            "hoof": Mat.of(C["hoof"], sheen=0.5),
            "inner_ear": Mat.of(C["inner_ear"], sss=0.5),
            "C": C,
        }
    return m


@dataclass
class MinotaurPose(F.FolkPose):
    """FolkPose (see _folk.FolkPose / DragonPose) plus:
    hug_reach / hug_w / hug_d / hug_y   the "hug" gesture's partner (draw_brawl sets them)
    shove_y     "shove" aim: hands at this height above his pelvis (None = his own chest);
                a shorter opponent's chest is lower
    tail_swing  -1..1 sideways sweep of the tail
    variant     a MINOTAUR_VARIANTS name (crowd recolours)
    """
    mood: object = "neutral"
    hug_reach: float = 96.0
    hug_w: float = 72.0
    hug_d: float = 48.0
    hug_y: float = 80.0
    hug_y_far: float = None
    shove_y: float = None
    tail_swing: float = 0.0
    variant: str = "chestnut"


MinotaurRig = F.FolkRig


def _g_surprised(q, sk, side, arm):
    """Stunned (being hugged): arms lifted out from the sides, hands open, not touching."""
    AL = F._AL(q)
    return F.G(v_add(sk, (side * 0.40 * AL, 0.06 * AL, -0.02 * AL)), "open", 0.0, "auto", (side * 0.6, 1.0, -0.5), "in")


MINOTAUR_GESTURES = dict(F.GESTURES)
MINOTAUR_GESTURES["surprised"] = _g_surprised


def minotaur_walk_phase(distance_px, scale=1.0, yaw=1.0):
    return F.walk_phase(MINOTAUR_BUILD, distance_px, scale, yaw)


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_minotaur(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the minotaur with its anchor at (x, y). Returns a MinotaurRig. parts: None =
    everything, or a subset of ("back", "body", "mid", "head", "front") (see draw_brawl)."""
    pose = pose or MinotaurPose()
    q = F.begin(cr, x, y, scale, pose, light, t, detail, MINOTAUR_BUILD, minotaur_mats(pose.variant), parts)
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far, MINOTAUR_GESTURES) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    if q.want("body") and pose.shadow:
        F.contact(q, 84.0)
    for s in (q.far, q.near):
        if lay[s] == "back" and q.want("back"):
            hands[s] = _arm(q, A[s])
    if q.want("body"):
        tail_front = math.cos(q.yaw) < -0.2           # seen from behind: the tail is in front
        if not tail_front:
            _tail(q)
        _legs(q)
        _torso(q)
        if tail_front:
            _tail(q)
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
    rig.points["horn_tips"] = head.get("horn_tips", [])
    return F.end(q, rig)


def _hand_guess(q, A):
    el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    d = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    return B.HandFrame(wr[0] + d[0] * 34, wr[1] + d[1] * 34, math.atan2(d[1], d[0]), 1.0, [], wr, False)


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _legs(q):
    """Breeches (both legs, one union), linen leg wraps, cloven hooves (one union)."""
    cr, M, proj = q.cr, q.M, q.proj
    shp, pal = F.legs(q, [34.0, 24.0, 17.0], M["breeches"], 52.0)
    if q.detail >= 1:                       # leg wraps: a band over each shin + criss-cross ink
        wp = None
        for f in q.S["feet"]:
            hip, kn, an = F.leg_spine(q, f)
            wp = F.band(q, shp, core.lerp_pt(kn, an, 0.42), core.lerp_pt(kn, an, 1.0), 19.0, M["wraps"], 30.0,
                        seams=False)
        if q.detail >= 2 and wp is not None:
            lines = []
            for f in q.S["feet"]:
                hip, kn, an = F.leg_spine(q, f)
                ux, uy = core.normalize((an[0] - kn[0], an[1] - kn[1]))
                nx, ny = -uy, ux
                for k in range(4):
                    m = core.lerp_pt(kn, an, 0.48 + 0.13 * k)
                    r = lerp(19.0, 15.0, 0.48 + 0.13 * k) * 0.95
                    lines.append([(m[0] + nx * r, m[1] + ny * r - 4), (m[0] - nx * r, m[1] - ny * r + 4)])
            B.detail_lines(cr, lines, q.lw * 0.8, wp.line, 0.55)
    groups = []
    for f in q.S["feet"]:
        g, _P = F.foot_groups(q, f, length=36.0, width=19.0, height=26.0)
        groups += g
    hp = F.hull_union(q, groups, M["hoof"], 26.0, rim=0.6)[1]
    if q.detail >= 1 and proj.depth((0.0, 0.0, 1.0)) > 0.2:      # the cloven split
        lines = []
        for f in q.S["feet"]:
            a = f["ankle"]
            g0 = proj.xy((a[0], -10.0, a[2] + 16.0))
            g1 = proj.xy((a[0], -1.0, a[2] + 26.0))
            lines.append([g0, g1])
        B.detail_lines(cr, lines, q.lw * 1.0, core.tint(hp.lit, 0.3), 0.7)


def _torso(q):
    """The grey wool tunic (to mid-thigh), belt and brass buckle, and the bunched hood."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    T = S["T"]
    br, h = S["br"], S["hunch"]
    sit = q.sit
    pel = S["pelvis"]
    walk = S["walk"]
    sw = walk * math.sin(TAU_ * S["wc"].phase * 2)
    kn = v_lerp(S["knee"][0], S["knee"][1], 0.5)
    hem_c = v_lerp(v_add(pel, (sw * 3.0, 70.0, 2.0 - walk * 6.0)), v_add(v_lerp(pel, kn, 0.75), (0.0, 22.0, 4.0)), clamp(sit / 0.7))
    rings = [
        (T((0.0, -186.0 + 8 * h, 8.0 + 10 * h)), 62.0, 42.0),       # 0 over the shoulders
        (T((0.0, -166.0 + 5 * h, 3.0)), 92.0 + br, 52.0),           # 1 shoulders
        (T((0.0, -132.0, 12.0)), 90.0 + 1.5 * br, 60.0 + br),       # 2 barrel chest
        (T((0.0, -86.0, 12.0)), 80.0, 58.0),                        # 3 belly
        (T((0.0, -44.0, 6.0)), 68.0, 50.0),                         # 4 waist
        (v_add(pel, (0.0, 4.0, 0.0)), 70.0, 50.0),                  # 5 hips
        (v_lerp(v_add(pel, (0.0, 4.0, 0.0)), hem_c, 0.55), 76.0 + 4 * sit, 54.0),   # 6 thighs
        (hem_c, 82.0 + 8 * sit, 58.0),                              # 7 hem
    ]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=30.0)
    hem = F.hem_curve(q, *rings[-1], n=9, wave=1.4, phase=q.t * 1.1 + walk * S["wc"].phase * 6)
    shp, pal = F.smooth_shape(q, left + hem + right[::-1] + top, M["tunic"], 130.0, shadow=0.6)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        lines = []
        # hanging folds from the belt to the hem, on the faces turned to us
        c5, a5, z5 = rings[5]
        c7, a7, z7 = rings[7]
        for phi in (-1.0, -0.4, 0.35, 0.95):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < 0.15:
                continue
            p0 = proj.xy(v_add(c5, (math.sin(phi) * a5 * 0.95, 16.0, math.cos(phi) * z5 * 0.95)))
            p1 = proj.xy(v_add(c7, (math.sin(phi * 1.08) * a7 * 0.97, -2.0, math.cos(phi) * z7 * 0.97)))
            lines.append([p0, ((p0[0] + p1[0]) / 2 + 2.0 * math.sin(phi * 3), (p0[1] + p1[1]) / 2), p1])
        if q.detail >= 2:                   # chest drape folds under the cowl
            c2, a2, z2 = rings[2]
            for phi in (-0.5, 0.5):
                if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.3:
                    p0 = proj.xy(v_add(c2, (math.sin(phi) * a2 * 0.6, -18.0, math.cos(phi) * z2)))
                    p1 = proj.xy(v_add(c2, (math.sin(phi) * a2 * 0.45, 20.0, math.cos(phi) * z2)))
                    lines.append([p0, p1])
        if lines:
            B.detail_lines(cr, lines, q.lw * 1.0, pal.line, 0.45, taper=(0.05, 0.9, 0.4))
        cr.restore()
    c4, a4, z4 = rings[4]
    c5, a5, z5 = rings[5]
    F.belt(q, v_lerp(c4, c5, 0.5), lerp(a4, a5, 0.5) + 3.0, lerp(z4, z5, 0.5) + 3.0, 10.0, M["belt"], M["buckle"], 12.0)
    _cowl(q, rings)


def _cowl(q, rings):
    """The hood, down: a thick bunched collar of grey wool round the neck, its point hanging
    down his back (secondary motion)."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    nb = S["neck_base"]
    R = S["R"]
    sw = B.chain(q.t, 3, freq=0.32, delay=0.18, amp=0.4, seed=q.pose.seed + 2)
    # the point hanging behind (drawn first: under the collar roll)
    from .base import m_vec
    back = [v_add(nb, m_vec(R, (0.0, 4.0, -40.0))), v_add(nb, m_vec(R, (sw[0] * 20, 40.0, -50.0))),
            v_add(nb, m_vec(R, (sw[1] * 34, 80.0, -50.0))), v_add(nb, m_vec(R, (sw[2] * 44, 112.0, -46.0)))]
    pts2 = [proj.xy(p) for p in back]
    groups = []
    if proj.depth((0.0, 0.0, -1.0)) > -0.75:            # visible unless seen nearly head-on
        tip, tso = B.taper_paths(cr, pts2, 64.0, 6.0, q.lw)
        pal = q.shade(tip, M["tunic"], outline=tso, size=40.0, rim=0.6)
        if q.detail >= 2:
            B.detail_lines(cr, [[pts2[0], pts2[1], pts2[2]]], q.lw * 0.9, pal.line, 0.4, taper=(0.1, 1.0, 0.1))
    # the bunched roll round the neck: two overlapping thick rings (one union)
    for (dy, rad, rz, th) in ((2.0, 60.0, 50.0, 21.0), (-16.0, 50.0, 42.0, 18.0)):
        c = v_add(nb, m_vec(R, (0.0, dy, -2.0)))
        ring = [proj.xy((c[0] + math.sin(TAU_ * i / 14) * rad, c[1] + 3.0 * math.sin(TAU_ * i / 7), c[2] + math.cos(TAU_ * i / 14) * rz))
                for i in range(14)]
        xs = [r[0] for r in ring]
        ys = [r[1] for r in ring]
        cx_, cy_ = sum(xs) / 14, sum(ys) / 14
        rx = (max(xs) - min(xs)) / 2 + th
        ry = (max(ys) - min(ys)) / 2 + th
        groups.append((cx_, cy_, rx, ry))
    cr.new_path()
    for (cx_, cy_, rx, ry) in groups:
        core.superellipse(cr, cx_, cy_, rx + q.lw, ry + q.lw, 2.4, steps=24)
    pal = q.P(M["tunic"])
    core.src(cr, pal.line)
    cr.fill()
    for (cx_, cy_, rx, ry) in groups:
        core.superellipse(cr, cx_, cy_, rx, ry, 2.4, steps=24)
    roll = Path(cr)
    q.shade(roll, M["tunic"], outline=False, size=34.0, shadow=0.8)
    if q.detail >= 1:                       # the folds of the bunched wool
        cx_, cy_, rx, ry = groups[0]
        lines = []
        for k in range(5):
            a = -0.9 + 0.45 * k
            x0 = cx_ + math.sin(a) * rx * 0.8
            lines.append([(x0 - 4, cy_ - ry * 0.55), (x0 + 2, cy_), (x0 - 2, cy_ + ry * 0.6)])
        B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.4, taper=(0.1, 1.0, 0.2))


TAU_ = math.tau


def _tail(q):
    """A bull's tail from under the back of the tunic: thin, swinging, with a dark tuft."""
    cr, proj, S, t = q.cr, q.proj, q.S, q.t
    pel = S["pelvis"]
    wav = B.chain(t, 5, freq=0.4, delay=0.18, amp=0.6, seed=q.pose.seed + 7, grow=2.5)
    swing = q.pose.tail_swing + 0.25 * B.sway(t * 0.7, 0.5, q.pose.seed + 3)
    base = v_add(pel, (0.0, 30.0, -44.0))
    pts = []
    acc = 0.0
    for i in range(6):
        u = i / 5.0
        if i:
            acc += wav[min(i - 1, 4)]
        lift = 1.0 - q.sit * 0.5
        p = v_add(base, ((swing * 60.0 * u * u + acc * 70.0 * u), 150.0 * u * lift + 10 * u, -20.0 * u - 30.0 * math.sin(u * 2.4)))
        pts.append(proj.xy(p))
    shp, so = B.tube_paths(cr, pts, [7.0, 6.0, 5.0, 4.5, 4.0, 3.5], q.lw, samples=3)
    q.shade(shp, q.M["fur"], outline=so, size=10.0, rim=0.5)
    tip, prev = pts[-1], pts[-2]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    ca, sa = math.cos(a), math.sin(a)
    tuft = [(tip[0] + x * ca - y * sa, tip[1] + x * sa + y * ca) for x, y in ((-6, 0), (4, -9), (22, -6), (30, 0), (22, 6), (4, 9))]
    ts, tso = B.smooth_paths(cr, tuft, q.lw, 0.9)
    q.shade(ts, q.M["fur_dk"], outline=tso, size=14.0, rim=0.4)


def _arm(q, A):
    """Rolled grey sleeve to below the elbow, a furred forearm and a big hand."""
    cr, M, proj = q.cr, q.M, q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fm = core.lerp_pt(el, wr, 0.4)
    arm, apal = F.limb(q, [sh, el, fm, wr], [27.0, 20.0, 21.5, 15.0], M["fur"], 42.0)
    # the sleeve over the upper arm, its rolled cuff just below the elbow
    cut = core.lerp_pt(el, wr, 0.22)
    sl, spal = F.limb(q, [sh, el, cut], [31.0, 24.5, 24.5], M["tunic"], 46.0)
    if q.detail >= 1:
        ux, uy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
        nx, ny = -uy, ux
        F.band(q, sl, core.lerp_pt(el, cut, 0.05), (cut[0] + ux * 2, cut[1] + uy * 2), 25.0, M["tunic_dk"], 30.0)
        if q.detail >= 2:
            F.elbow_folds(q, sh, el, cut, 20.0, spal, 0.4)
            # fur tufts at the forearm's edge
            lines = []
            for k in range(3):
                m = core.lerp_pt(el, wr, 0.45 + 0.18 * k)
                lines.append([(m[0] + nx * 19, m[1] + ny * 19), (m[0] + nx * 23 + ux * 6, m[1] + ny * 23 + uy * 6)])
            B.detail_lines(cr, lines, q.lw * 0.9, apal.line, 0.6)
    return F.hand(q, A, M["fur"], size=82.0, finger_w=1.35, palm_w=1.3, pad=MINOTAUR_COLORS["muzzle"])


# ----------------------------------------------------------------------------------------
# head (head space x HS: X his left, Y down, Z forward)
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


def _horn(q, P, s, pal_cache):
    """A big crescent horn: out from the side of the poll, then up and forward; ivory with a
    darker tip (second tone clipped inside). Returns its tip (2D)."""
    cr = q.cr
    spine = [(s * 24.0, -27.0, -6.0), (s * 46.0, -34.0, -8.0), (s * 64.0, -45.0, -4.0), (s * 72.0, -58.0, 4.0),
             (s * 68.0, -66.0, 12.0)]
    pts = [P(p) for p in spine]
    lwh = q.lw * 0.95

    def prof(u):
        return 21.0 * HS * (1.0 - u) ** 0.85 + 3.0

    shp, so = B.taper_paths(cr, pts, 30.0, 3.0, lwh, profile=prof)
    pal = q.shade(shp, q.M["horn"], lw=lwh, outline=so, size=16.0, rim=0.8)
    cr.save()
    shp.add(cr)
    cr.clip()
    tp = q.P(q.M["horn_tip"])
    tip_pts = pts[2:]
    core.tapered(cr, [core.lerp_pt(pts[2], pts[3], 0.2)] + tip_pts[1:], 30.0, 8.0)
    core.src(cr, core.mix(tp.lit, tp.shadow, 0.3))
    cr.fill()
    if q.detail >= 2:                       # growth rings near the base
        sp = core.spline(pts[:3], n=3)
        lines = []
        for k in (1, 3, 5):
            if k + 1 < len(sp):
                p0, p1 = sp[k], sp[k + 1]
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                L = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / L, dx / L
                w = prof(k / 12.0) * 0.5
                lines.append([(p0[0] - nx * w, p0[1] - ny * w), (p0[0] + dx / L * 2, p0[1] + dy / L * 2), (p0[0] + nx * w, p0[1] + ny * w)])
        B.detail_lines(cr, lines, q.lw * 0.7, pal.line, 0.45)
    cr.restore()
    return pts[-1]


def _ear(q, P, s, e, nz):
    """Floppy ear sticking out sideways under the horn: droops when sad, lifts when alert."""
    t = q.t
    perk = clamp(0.5 + 0.5 * (e.brow_y + 0.4 * e.smile - 0.6 * max(0.0, e.lid_tilt)), 0.0, 1.0)
    tw = 0.07 * math.sin(t * 1.1 + s * 1.7) + 0.12 * B.wobble(t, math.floor(t / 5.0) * 5.0 + 2.1 + s * 0.5, 5.0, 6.0)
    drop = lerp(18.0, -6.0, perk) + tw * 18.0
    tip = (s * 66.0, 2.0 + drop, -10.0)
    pts = [P((s * 33.0, -10.0, -4.0)), P((s * 52.0, -10.0 + drop * 0.4, -10.0)), P(tip),
           P((s * 52.0, 10.0 + drop * 0.5, -10.0)), P((s * 34.0, 8.0, -6.0))]
    lwf = q.lw * 0.95
    shp, so = B.smooth_paths(q.cr, pts, lwf, 0.85)
    q.shade(shp, q.M["fur"], lw=lwf, outline=so, size=20.0, rim=0.6)
    if q.detail >= 1 and nz((s * 0.3, 0.0, 0.9)) > -0.2:
        inner = [P((s * 37.0, -5.0, -3.0)), P((s * 52.0, -4.0 + drop * 0.4, -8.0)), P(v_lerp(tip, (s * 50.0, 0.0, -9.0), 0.3)),
                 P((s * 52.0, 6.0 + drop * 0.45, -8.0)), P((s * 37.0, 4.0, -4.0))]
        cr = q.cr
        cr.new_path()
        core.smooth_closed(cr, inner, 0.85)
        core.src(cr, q.P(q.M["inner_ear"]).lit)
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
    ja = jaw_open * 0.3
    cj, sj = math.cos(ja), math.sin(ja)

    def J(v):                               # lower jaw hinge at (0, 14, 0)
        y, z = v[1] - 14.0, v[2]
        return (v[0], 14.0 + y * cj + z * sj, -y * sj + z * cj)

    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P(J((0.0, 33.0, 38.0))), "nose": P((0.0, 20.0, 50.0)),
           "eyes": [P((s * 19.0, -8.0, 27.0)) for s in (far, near)], "top": P((0.0, -38.0, -4.0))}
    if not draw:
        return pts
    lw = q.lw
    pal = q.P(M["fur"])
    behind = {s: D((s * 30.0, -20.0, -6.0)) < D((0.0, -20.0, -6.0)) - 3.0 for s in (-1.0, 1.0)}
    tips = {}
    for s in (-1.0, 1.0):                   # far horn + far ear behind the head
        if behind[s]:
            _ear(q, P, s, e, nz)
            tips[s] = _horn(q, P, s, None)
    # ---- the head: neck (bull neck) + cranium + cheeks + jaw, one union
    nb, nt = S["neck_base"], S["neck_top"]
    groups = (F.blob_pts(proj, v_add(nb, (0.0, 0.0, 6.0)), 40.0, 12.0, 34.0) + F.blob_pts(proj, nt, 36.0, 12.0, 32.0),
              _bp(P, (0.0, -12.0, -6.0), 34.0, 27.0, 31.0, 16), _bp(P, (0.0, 8.0, 8.0), 36.0, 22.0, 26.0),
              F.ellipsoid2d(lambda v: P(J(v)), (0.0, 30.0, 18.0), 24.0, 11.0, 22.0))
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
    q.shade(Path(cr), M["fur"], outline=False, size=100.0)
    # ---- mouth interior (behind the muzzle), then the cream muzzle (own form + outline)
    if jaw_open > 0.04 and nz((0.0, 0.3, 1.0)) > -0.25:
        ip = [P((sd * 18.0, 28.0, z)) for sd in (-1.0, 1.0) for z in (20.0, 38.0)] + [P((0.0, 29.0, 46.0))]
        ip += [P(J((sd * 16.0, 31.0, z))) for sd in (-1.0, 1.0) for z in (20.0, 36.0)] + [P(J((0.0, 32.0, 42.0)))]
        mh = core.convex_hull(ip)
        cr.new_path()
        core.smooth_closed(cr, B.offset_closed(mh, lw * 0.8), 0.8)
        core.src(cr, pal.line)
        cr.fill()
        core.smooth_closed(cr, mh, 0.8)
        core.src(cr, B.pal(q.light, MINOTAUR_COLORS["mouth"]).lit)
        cr.fill()
        tg = P(J((0.0, 31.0, 32.0)))
        core.src(cr, B.pal(q.light, MINOTAUR_COLORS["tongue"], sss=0.4).lit)
        core.ellipse(cr, tg[0], tg[1], 13.0, 3.0 + 5.0 * jaw_open)
        cr.fill()
    if nz((0.0, 0.25, 1.0)) < -0.15:         # facing away: the muzzle is hidden by the skull
        pts["eyes"] = []
        _forelock(q, P, nz, D)
        for s in (-1.0, 1.0):
            if not behind[s]:
                _ear(q, P, s, e, nz)
                tips[s] = _horn(q, P, s, None)
        pts["horn_tips"] = [tips[s] for s in (-1.0, 1.0) if s in tips]
        return pts
    muz = _bp(P, (0.0, 17.0, 30.0), 26.0, 17.0, 18.0, 14) + _bp(P, (0.0, 22.0, 40.0), 22.0, 13.0, 12.0, 12)
    msh, mso, _ = B.hull_paths(cr, muz, lw, 0.85)
    mpal = q.shade(msh, M["muzzle"], outline=mso, size=40.0, rim=0.5)
    # nose pad + nostrils
    fz = nz((0.0, 0.1, 1.0))
    if fz > -0.3:
        npad = _bp(P, (0.0, 15.0, 49.0), 16.0, 8.0, 5.0, 12)
        cr.new_path()
        core.smooth_closed(cr, core.convex_hull(npad), 0.85)
        npal = q.P(M["nose"])
        core.src(cr, npal.lit)
        cr.fill()
        lines = []
        for s in (-1.0, 1.0):
            if nz((s * 0.5, 0.2, 0.8)) > -0.05:
                lines.append([P((s * 4.0, 15.0, 54.0)), P((s * 9.0, 16.0, 52.0)), P((s * 11.0, 19.0, 50.0))])
        if lines:
            B.detail_lines(cr, lines, lw * 2.0, npal.line, 0.95, taper=(1.0, 0.9, 0.3))
        if q.detail >= 2:
            B.sheen(cr, *P((-3.0, 12.0, 53.0)), 5.0, 2.5, alpha=0.4)
    # mouth line along the muzzle's underside (closed)
    if jaw_open < 0.04:
        sm = e.smile
        lines = []
        for s in (-1.0, 1.0):
            if nz((s * 0.6, 0.4, 0.6)) < -0.1:
                continue
            lines.append([P((s * 21.0, 28.0 - sm * 6.0, 26.0)), P((s * 12.0, 30.5 - sm * 2.0, 40.0)), P((0.0, 31.0, 45.0))])
        if lines:
            B.detail_lines(cr, lines, lw * 1.2, mpal.line, 1.0, taper=(0.5, 1.0, 0.9))
    # ---- eyes, brows, forelock
    eyes = []
    for s in (far, near):
        ec = F.eye_at(q, P, nz, s, e, (s * 19.0, -8.0, 26.0), 11.5 * HS, 13.5 * HS, iris=MINOTAUR_COLORS["eye"],
                      iris_hi=MINOTAUR_COLORS["eye_hi"], skin=M["C"]["fur"], pupil="#1d120c", lid_add=0.06,
                      crease=0.3 if q.detail >= 2 else 0.0, bags=0.3 if q.detail >= 2 else 0.0, line=pal.line,
                      normal=(s * 0.5, -0.1, 0.86))
        eyes.append(ec or P((s * 19.0, -8.0, 26.0)))
    pts["eyes"] = eyes
    _brows(q, P, nz, e, near, paths[1:])
    _forelock(q, P, nz, D)
    for s in (-1.0, 1.0):
        if not behind[s]:
            _ear(q, P, s, e, nz)
            tips[s] = _horn(q, P, s, None)
    pts["horn_tips"] = [tips[s] for s in (-1.0, 1.0) if s in tips]
    return pts


def _brows(q, P, nz, e, near, clip):
    """Thick fur brows (dark), both in one union, pushed by the Expr."""
    cr = q.cr
    lwb = q.lw * 0.85
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.1:
            continue
        pts = F.brow_pts(P, s, e, near, 6.0, 33.0, -23.0, 33.0, 22.0, 14.0, 12.0)
        sh, so = B.taper_paths(cr, pts, 13.0, 6.0, lwb)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    cr.save()
    for pth in clip:
        pth.add(cr)
    cr.clip()
    B.fill_outlines(cr, outs, q.P(q.M["fur_dk"]).line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["fur_dk"], lw=lwb, outline=False, size=9.0, rim=0.0)
    cr.restore()


def _forelock(q, P, nz, D):
    """A curly dark forelock tumbling between the horns onto the brow."""
    if nz((0.0, -0.6, 0.8)) < -0.4:
        return
    cr = q.cr
    sw = 2.0 * math.sin(q.t * 1.3 + q.pose.seed)
    curls = []
    for (x, y, z, r) in ((-10.0, -36.0, 10.0, 9.0), (1.0, -38.0, 11.0, 10.0), (11.0, -35.0, 9.0, 8.5), (-4.0, -31.0, 18.0, 7.5),
                         (6.0, -30.0, 18.0, 6.5)):
        c = P((x + sw * 0.2, y, z))
        curls.append((c, r * HS * 0.62))
    cr.new_path()
    for c, r in curls:
        core.circle(cr, c[0], c[1], r + q.lw * 0.9)
    pal = q.P(q.M["fur_dk"])
    core.src(cr, pal.line)
    cr.fill()
    for c, r in curls:
        core.circle(cr, c[0], c[1], r)
    q.shade(Path(cr), q.M["fur_dk"], outline=False, size=10.0, rim=0.7)
    if q.detail >= 2:
        lines = [[(c[0] - r * 0.5, c[1] + r * 0.1), (c[0], c[1] - r * 0.35), (c[0] + r * 0.45, c[1])] for c, r in curls[:3]]
        B.detail_lines(cr, lines, q.lw * 0.7, pal.line, 0.6)


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("minotaur", lambda cr, x, y, sc: draw_minotaur(cr, x, y, sc, MinotaurPose(facing=1), t=0.4), 260.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    for label, pose in (("3/4 left", MinotaurPose(facing=-1)), ("front", MinotaurPose(facing=0)),
                        ("3/4 right", MinotaurPose(facing=1)), ("profile", MinotaurPose(facing=1, turn=0.75)),
                        ("back 3/4", MinotaurPose(facing=1, turn=2.6)), ("back", MinotaurPose(facing=2))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 290, 640, floor=600)
            draw_minotaur(cr, 145, 612, 0.95, p, neutral, t=0.4)
        add(label, 290, 640, fn, "turnaround")

    moods = [("neutral", dict()), ("angry", dict(mood="angry")), ("angry, bellowing", dict(mood="angry", talk=1.0)),
             ("surprised (hugged)", dict(mood="surprised")), ("worried", dict(mood="worried")),
             ("kind", dict(mood="kind")), ("eyes closed (hug back)", dict(mood="kind", blink=1.0, head_nod=-0.4)),
             ("sad", dict(mood="sad")), ("laugh", dict(laugh=1.0)), ("front: angry", dict(mood="angry", facing=0)),
             ("front: surprised", dict(mood="surprised", facing=0)), ("3/4 left: kind", dict(mood="kind", facing=-1)),
             ("profile", dict(mood="neutral", facing=1, turn=0.75)), ("skeptical", dict(mood="skeptical"))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        turn = kw.pop("turn", -0.3 if facing == 1 else (0.3 if facing == -1 else 0.0))
        pose = MinotaurPose(facing=facing, turn=turn, **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 240, 240)
            s0, c0 = core.frame(4, 4)
            r0 = draw_minotaur(c0, 0.0, 0.0, 1.1, p, neutral, t=0.4)
            draw_minotaur(cr, 120 - r0.head[0], 150 - r0.head[1], 1.1, p, neutral, t=0.4)
        add(label, 240, 240, fn, "faces")

    beats = [("guard", MinotaurPose(facing=-1, mood="angry", stance=-0.6, hunch=0.6, near=Arm("guard"), far=Arm("guard"))),
             ("shove: thrust", MinotaurPose(facing=-1, mood="angry", talk=0.8, stance=-0.6, hunch=0.6, lean=0.4, near=Arm("shove", phase=0.5), far=Arm("shove", phase=0.5))),
             ("shoved: stagger", MinotaurPose(facing=-1, mood="surprised", lean=-0.5, near=Arm("stagger", phase=0.3), far=Arm("stagger", phase=0.7))),
             ("stunned (being hugged)", MinotaurPose(facing=-1, mood="surprised", near=Arm("surprised"), far=Arm("surprised"))),
             ("hug back (arms only)", MinotaurPose(facing=-1, mood="kind", blink=1.0, hunch=0.8, head_nod=-0.5, near=Arm("hug"), far=Arm("hug"))),
             ("walk", MinotaurPose(facing=-1, walk=1.0, phase=0.3)),
             ("tankard (tavern)", MinotaurPose(facing=0, turn=0.4, laugh=0.8, near=Arm("tankard", phase=0.8), far=Arm("rest"), variant="black")),
             ("sit", MinotaurPose(facing=1, turn=-0.3, sit=1.0, near=Arm("knees"), far=Arm("knees"), variant="dun"))]
    for label, pose in beats:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 300, 460, floor=432)
            if p.sit > 0.5:
                F.sheet_bench(cr, 150, 444, 0.62)
            draw_minotaur(cr, 150, 444, 0.62, p, neutral, t=0.4)
        add(label, 300, 460, fn, "actions")

    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 210, 460, name, floor=432)
            draw_minotaur(cr, 105, 444, 0.62, MinotaurPose(facing=-1, turn=0.25), L[name], t=0.4)
        add(name, 210, 460, fn, "lights & variants")
    for v in MINOTAUR_VARIANTS:
        def fn(cr, v=v):
            F.sheet_bg(cr, 210, 460, "tavern", floor=432)
            draw_minotaur(cr, 105, 444, 0.62, MinotaurPose(facing=1, turn=-0.3, variant=v, mood="happy"), L["tavern"], t=0.4)
        add(f"variant: {v}", 210, 460, fn, "lights & variants")
    return items
