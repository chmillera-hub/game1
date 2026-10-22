"""pixie.py -- THE PIXIE (S5, speaker CROWD): "Ew. What is he doing?"

A tiny, sneering young fae: a big head on a sliver of a body, soft lilac skin, long pointed
leaf ears poking out of a spiky magenta crop (her signature accent), slanted green-gold eyes
that look down her little upturned nose, a jagged leaf tunic with a petal collar, curled leaf
shoes, and four dragonfly wings that never stop buzzing (each drawn as a fan of translucent
motion-blurred copies with a speed arc through the tips). She hovers, films the fight with a
scrying crystal almost as big as her head, then lowers it to sneer.

    from film.lib import characters as ch
    p = ch.PixiePose(facing=-1, hover=150, talk=timeline.talk(5, t, "CROWD"),
                     near=ch.Arm("raise_crystal_film", hold=ch.crystal_hold(face=-1.0, size=1.7)),
                     far=ch.Arm("hip"))
    rig = ch.draw_pixie(cr, x, ground_y, 1.6, p, ch.LIGHTS["square"], t)

Scale 1.0: feet -> top of the hair spikes / ear tips = PIXIE_HEIGHT = 90 px standing (wings
extra). Anchor (x, y) = the GROUND point below her; `hover` lifts her feet that many body px
above it (she bobs). Her level of detail follows her on-screen size, not the scale (she is
tiny): full detail only when she is >= ~220 px tall on screen.
"""

import math
from dataclasses import dataclass

from .. import core
from ..core import clamp
from . import base as B
from . import _folk as F
from .base import Mat, Path, v_add, v_sub
from .dragon import Arm

__all__ = ["PixiePose", "PixieRig", "draw_pixie", "PIXIE_HEIGHT", "PIXIE_COLORS", "PIXIE_GESTURES", "pixie_mats",
           "pixie_wing_buzz"]

PIXIE_HEIGHT = 90.0
HS = 0.5
PIXIE_LINE = B.LINE * 0.8            # tiny creature: a slightly finer outline (cf. the pigeon)
FACE_LINE = 0.6                       # her face features use a finer line still
TAU = math.tau

PIXIE_COLORS = {
    "skin": "#CDBDEB",       # soft lilac
    "hair": "#D2367E",       # spiky magenta -- the signature accent
    "ear_in": "#E49AC0",
    "blush": "#E77FA8",
    "tunic": "#3F7A4A",      # leaf green
    "tunic_dk": "#2C5A38",
    "petal": "#F0A8C8",      # petal collar
    "shoe": "#5E8A3A",
    "wing": "#C8F6FF",       # iridescent, translucent
    "wing_edge": "#7E6FD8",
    "wing_hi": "#FFE6F6",
    "eye": "#8CC04A",        # green-gold
    "eye_hi": "#E6F59A",
    "mouth": "#4A1E3A",
    "tongue": "#D46A8C",
}

PIXIE_BUILD = F.Build(
    pelvis_h=34.5, hip_w=4.5, thigh=13.2, shin=12.8, ankle_h=3.5,
    sh_y=17.0, sh_z=0.0, sh_w=7.5, upper_arm=11.5, forearm=10.5, hand_len=8.5,
    neck_y=18.5, neck_z=0.5, neck_len=2.0, head_up=11.5, head_fwd=1.0,
    hunch=0.1, hunch_fwd=2.0, stride=36.0, lift=5.0, bob=1.2, breath=0.5,
    sit_drop=3.0, sit_back=2.0, sway=0.7, knee_out=0.2,
    fit=0.978)   # scale 1.0 -> base.CAST_HEIGHTS (measured on the lineup)

_MATS = {}


def pixie_mats():
    if not _MATS:
        C = PIXIE_COLORS
        _MATS.update({
            "skin": Mat.of(C["skin"], sss=0.5, shadow_k=1.05),
            "hair": Mat.of(C["hair"], sheen=0.35),
            "tunic": Mat.of(C["tunic"]),
            "petal": Mat.of(C["petal"], sss=0.4),
            "shoe": Mat.of(C["shoe"]),
            "wing": Mat.of(C["wing"], shadow_k=1.2),
        })
    return _MATS


@dataclass
class PixiePose(F.FolkPose):
    """FolkPose (see _folk.FolkPose / DragonPose) plus:
    hover    feet above the ground anchor, body px (0 = standing on the ground)
    buzz     0..1 wing flutter (the blur fan); 0 = wings still and spread
    bob      hovering bob amplitude (body px)
    Defaults: mood "sneer", chin up (head_nod 0.12) -- she looks down her nose at everyone.
    Extra gesture: Arm("hip") (hand on the hip, elbow out)."""
    mood: object = "sneer"
    head_nod: float = 0.12
    hover: float = 0.0
    buzz: float = 1.0
    bob: float = 3.0


PixieRig = F.FolkRig


def _g_raise_crystal(q, sk, side, arm):
    """Her head is huge: the crystal goes up and well out to the side of it (from behind, its
    face shows past her crop)."""
    AL = q.b.upper_arm + q.b.forearm
    hc = q.S["head_c"]
    return F.G((sk[0] + side * 0.45 * AL, hc[1] - 0.10 * AL, hc[2] + 0.40 * AL), "grip", -0.9, "front",
               (side * 1.0, 0.9, -0.2), "up")


PIXIE_GESTURES = dict(F.GESTURES)
PIXIE_GESTURES.update({"raise_crystal_film": _g_raise_crystal, "raise_crystal": _g_raise_crystal})


def pixie_wing_buzz(t, seed=0):
    """The flap angle offset (rad) of her wings at time t (fast, deterministic, aperiodic)."""
    return 0.35 * math.sin(t * TAU * 11.0 + seed) + 0.15 * math.sin(t * TAU * 17.3 + 1.3 * seed)


def _skel(q):
    S = F.skeleton(q)
    # hovering: the legs dangle, toes pointed, a slow kick
    if q.pose.hover > 2.0:
        for f in S["feet"]:
            s = f["side"]
            k = 0.25 * math.sin(q.t * 2.3 + s * 1.7 + q.pose.seed)
            hip = f["hip"]
            ank = v_add(hip, (s * 1.2, q.b.thigh + q.b.shin - 2.5 - 4.0 * abs(k), 4.0 + 8.0 * k * s))
            f["knee"], f["ankle"] = B.ik3(hip, ank, q.b.thigh, q.b.shin, (s * 0.2, 0.0, 1.0))
            f["toe"] = -0.6
            f["ground"] = (f["ankle"][0], f["ankle"][1] + q.b.ankle_h, f["ankle"][2])
        S["knee"] = [S["feet"][0]["knee"], S["feet"][1]["knee"]]
    return S


def draw_pixie(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the pixie (anchor = ground point below her; pose.hover lifts her). Returns a
    PixieRig (rig.points: "crystal" = the crystal's centre when one is held via crystal_hold,
    "wings" = the wing root)."""
    pose = pose or PixiePose()
    dev = scale * B.device_scale(cr) * PIXIE_HEIGHT
    if detail is None:
        detail = 2 if dev >= 220 else 1 if dev >= 110 else 0
    bob = pose.bob * math.sin(t * TAU * 0.9 + pose.seed) if pose.hover > 0 else 0.0
    lift = (pose.hover + bob) * scale
    if pose.shadow and pose.hover > 0 and (parts is None or "body" in parts):
        a = 0.28 * clamp(1.0 - pose.hover / 400.0)
        B.contact_shadow(cr, x, y, 14.0 * scale * (1.0 + pose.hover / 200.0), 3.5 * scale, alpha=a)
    q = F.begin(cr, x, y - lift, scale, pose.with_(shadow=pose.shadow and pose.hover <= 0), light, t, detail,
                PIXIE_BUILD, pixie_mats(), parts, line=PIXIE_LINE, skel=_skel)
    q.pose = pose
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far, PIXIE_GESTURES) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    away = math.cos(q.yaw) < -0.15         # seen from behind: the wings are in front of her
    if q.want("back") and not away:
        _wings(q)
    if q.want("body") and pose.shadow and pose.hover <= 0:
        F.contact(q, 12.0)
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
    if q.want("front") and away:
        _wings(q)
    rig = F.base_rig(q, head)
    rig.hand_near = hands.get(q.near) or _hand_guess(q, A[q.near])
    rig.hand_far = hands.get(q.far) or _hand_guess(q, A[q.far])
    rig.points["wings"] = q.proj.xy(q.S["T"]((0.0, -0.8 * q.b.sh_y, -3.5)))
    rig = F.end(q, rig)
    for arm in (pose.near, pose.far):       # a crystal_hold's cold glow lights her face
        h = arm.hold
        if getattr(h, "center_dev", None) is not None and (parts is None or "front" in parts):
            h.light(cr)
            rig.points["crystal"] = cr.device_to_user(*h.center_dev)
    return rig


def _hand_guess(q, A):
    el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    d = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    return B.HandFrame(wr[0] + d[0] * 5, wr[1] + d[1] * 5, math.atan2(d[1], d[0]), 1.0, [], wr, False)


# ----------------------------------------------------------------------------------------
# wings: four dragonfly wings, a buzzing blur
# ----------------------------------------------------------------------------------------

# (length, width, elevation (rad, + = up), sweep back (rad), leading edge up?)
_WINGS = ((40.0, 9.5, 0.55, 0.45, True), (32.0, 9.0, -0.42, 0.60, False))
# unit wing outline: (along root->tip, across: + = leading edge)
_WING_SHAPE = ((0.0, 0.0), (0.10, 0.30), (0.36, 0.52), (0.68, 0.50), (0.90, 0.34), (1.0, 0.04),
               (0.96, -0.22), (0.78, -0.38), (0.45, -0.40), (0.16, -0.22))


def _wings(q):
    """Two wings per side (fore + hind) rooted between the shoulder blades, swept back. While
    buzzing each wing is a fan of 3 translucent copies spread over its beat (+ a faint speed arc
    through the tips): the fast-flutter blur. Translucent, with violet edges and veins and a
    little magenta wing-spot."""
    cr, proj, S, pose, t = q.cr, q.proj, q.S, q.pose, q.t
    T = S["T"]
    o = T((0.0, 0.0, 0.0))
    d0 = proj.depth(o)
    buzz = clamp(pose.buzz)
    flap = pixie_wing_buzz(t, pose.seed) * (0.25 + 0.75 * buzz)
    spread = 0.34 * buzz
    copies = ((-1.0, 0.13), (1.0, 0.13), (0.0, 0.30)) if buzz > 0.05 else ((0.0, 0.42),)
    wl = q.P(q.M["wing"]).lit
    wc = core.col(PIXIE_COLORS["wing"])
    fill = (wc[0] * 0.55 + wl[0] * 0.45, wc[1] * 0.55 + wl[1] * 0.45, wc[2] * 0.55 + wl[2] * 0.45)
    ec = core.col(PIXIE_COLORS["wing_edge"])
    hc = core.col(PIXIE_COLORS["hair"])
    lw = max(q.lw * 0.42, 0.5)
    # far side first (seen from behind the near side is in front)
    order = (q.far, q.near) if math.cos(q.yaw) >= 0 else (q.near, q.far)
    arcs = []
    for s in order:
        root_l = (s * 1.2, -0.80 * q.b.sh_y, -3.0)
        rp = proj.xy(T(root_l))
        for (length, width, el0, sweep, lead_up) in _WINGS:
            n = v_sub(T((s * math.sin(sweep), 0.0, math.cos(sweep))), o)
            face = abs(proj.depth(v_add(o, n)) - d0)
            w2 = width * (0.30 + 0.70 * face)
            tips = []
            for c, alpha in copies:
                el = el0 + flap * (1.0 if lead_up else -0.8) + c * spread
                dl = (s * math.cos(el) * math.cos(sweep), -math.sin(el), -math.cos(el) * math.sin(sweep))
                tp = proj.xy(T(v_add(root_l, (dl[0] * length, dl[1] * length, dl[2] * length))))
                dx, dy = tp[0] - rp[0], tp[1] - rp[1]
                L = math.hypot(dx, dy) or 1.0
                ux, uy = dx / L, dy / L
                nx, ny = -uy, ux
                if (ny < 0) != lead_up:      # + across = leading edge: up for the fore wing
                    nx, ny = -nx, -ny
                pts = [(rp[0] + ux * L * a + nx * w2 * b_, rp[1] + uy * L * a + ny * w2 * b_) for a, b_ in _WING_SHAPE]
                cr.new_path()
                core.smooth_closed(cr, pts, 0.8)
                cr.set_source_rgba(fill[0], fill[1], fill[2], alpha * (0.75 + 0.25 * face))
                if c == 0.0:
                    cr.fill_preserve()
                    cr.set_line_width(lw)
                    cr.set_source_rgba(ec[0], ec[1], ec[2], 0.55 + 0.25 * face)
                    cr.stroke()
                    if q.detail >= 1:
                        # veins + the wing-spot
                        def W2(a, b_):
                            return (rp[0] + ux * L * a + nx * w2 * b_, rp[1] + uy * L * a + ny * w2 * b_)
                        veins = [[W2(0.04, 0.05), W2(0.45, 0.30), W2(0.90, 0.20)], [W2(0.06, -0.02), W2(0.5, -0.12), W2(0.88, -0.10)]]
                        if q.detail >= 2:
                            veins += [[W2(0.30, 0.28), W2(0.36, -0.30)], [W2(0.62, 0.32), W2(0.66, -0.28)]]
                        cr.set_line_width(lw * 0.7)
                        cr.set_source_rgba(ec[0], ec[1], ec[2], 0.4)
                        for v in veins:
                            cr.move_to(*v[0])
                            for p in v[1:]:
                                cr.line_to(*p)
                        cr.stroke()
                        sp = W2(0.86, 0.36)
                        cr.set_source_rgba(hc[0], hc[1], hc[2], 0.75)
                        core.ellipse(cr, sp[0], sp[1], 2.2, 1.3)
                        cr.fill()
                        if q.detail >= 2:   # an iridescent glint along the leading edge
                            a0, a1 = W2(0.25, 0.40), W2(0.75, 0.40)
                            hi = core.col(PIXIE_COLORS["wing_hi"])
                            cr.set_source_rgba(hi[0], hi[1], hi[2], 0.5)
                            cr.set_line_width(lw * 1.6)
                            cr.move_to(*a0)
                            cr.line_to(*a1)
                            cr.stroke()
                else:
                    cr.fill()
                tips.append(tp)
            if len(tips) == 3 and q.detail >= 1:
                arcs.append((tips[0], tips[2], tips[1]))
    if arcs:
        # speed arcs through the beating tips
        cr.set_line_width(lw * 0.7)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.16 * buzz)
        for a, m, b_ in arcs:
            cr.move_to(*a)
            cr.curve_to(m[0] * 1.0, m[1], m[0], m[1], b_[0], b_[1])
        cr.stroke()


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _legs(q):
    """Thin legs (one union) and curled leaf shoes (one union)."""
    cr, proj, M = q.cr, q.proj, q.M
    F.legs(q, [3.3, 2.5, 2.1], M["skin"], 6.0, contour=False, rim=0.3)
    groups = []
    tips = []
    for f in q.S["feet"]:
        a = f["ankle"]
        toe = f["toe"]
        c, sn = math.cos(toe), math.sin(toe)
        g = (a[0], a[1] + q.b.ankle_h, a[2])
        groups.append(F.blob_pts(proj, (g[0], g[1] - 2.5, g[2] + 2.5 * c), 3.2, 2.7, 5.4, 10))
        tip = proj.xy((g[0], g[1] - 5.5 + 3.5 * sn, g[2] + 10.0 * c))
        tips.append((proj.xy((g[0], g[1] - 2.5, g[2] + 5.0 * c)), tip))
    shp, pal = F.hull_union(q, groups, M["shoe"], 6.0, rim=0.0)
    outs, shapes = [], []
    for a, b_ in tips:                      # the curled toe points
        sh, so = B.taper_paths(cr, [a, ((a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2 + 1.0), b_], 3.6, 0.7, q.lw * 0.7)
        shapes.append(sh)
        outs.append(so)
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    core.src(cr, pal.lit)
    cr.fill()


def _torso(q):
    """A leaf tunic with a jagged hem and a pink petal collar."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    T = S["T"]
    br = S["br"]
    pel = S["pelvis"]
    sy = q.b.sh_y
    rings = [(T((0.0, -sy * 0.98, 0.5)), 5.0, 4.0), (T((0.0, -sy * 0.82, 0.5)), 8.0 + br * 0.2, 5.2), (T((0.0, -sy * 0.5, 1.0)), 7.0, 5.2),
             (T((0.0, -sy * 0.18, 0.5)), 5.8, 4.5), (v_add(pel, (0.0, 4.5, 0.0)), 9.5, 7.0)]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=2.2)
    hem = F.hem_curve(q, *rings[-1], n=9)
    if q.detail >= 1:                       # leaf points along the hem
        hem = [(x, y + (2.6 if i % 2 else 0.0)) for i, (x, y) in enumerate(hem)]
    shp, pal = F.smooth_shape(q, left + hem + right[::-1] + top, M["tunic"], 12.0, tension=0.6, rim=0.6)
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        c = proj.xy(T((0.0, -sy * 0.4, 6.0)))
        b_ = proj.xy(v_add(pel, (0.0, 5.0, 6.5)))
        B.detail_lines(cr, [[c, b_]], q.lw * 0.6, pal.line, 0.5)
        cr.restore()
    # petal collar
    nb = S["neck_base"]
    pts = []
    for i in range(10):
        a = TAU * i / 10
        r = 7.5 if i % 2 else 5.0
        pts.append(proj.xy(v_add(nb, (math.sin(a) * r, 1.6 + (1.8 if i % 2 else 0.0), math.cos(a) * r * 0.8))))
    F.smooth_shape(q, pts, M["petal"], 6.0, tension=0.5, rim=0.0)


def _arm(q, A):
    M, proj = q.M, q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    F.limb(q, [sh, el, wr], [2.5, 2.0, 1.7], M["skin"], 5.0, rim=0.3)
    return F.hand(q, A, M["skin"], size=q.b.hand_len, finger_w=1.15, palm_w=1.15)


# ----------------------------------------------------------------------------------------
# head (head space x HS) -- big, chibi: a magenta crop is the skull, the face a lilac patch
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


# hair spikes: (direction in head space, length) -- the crown and the back of the crop
_SPIKES = ((-0.95, -0.42, -0.25, 44.0), (-0.62, -0.80, -0.20, 46.0), (-0.18, -0.98, -0.30, 47.0),
           (0.30, -0.95, -0.35, 46.0), (0.72, -0.66, -0.30, 45.0), (0.97, -0.20, -0.30, 42.0),
           (-0.25, -0.55, -0.80, 44.0), (0.35, -0.50, -0.80, 44.0), (0.0, -0.15, -1.0, 41.0))


def _head(q, draw=True):
    cr, M, pose, S, proj = q.cr, q.M, q.pose, q.S, q.proj
    e = F.expr_of(pose)
    P, nz, D, W = F.head_xf(q, HS)
    hyaw = S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    eye_pos = {s: (s * 12.5, -1.0, 24.5) for s in (-1.0, 1.0)}
    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P((0.0, 15.0, 25.0)), "nose": P((0.0, 6.0, 29.0)),
           "eyes": [P(eye_pos[s]) for s in (far, near)], "top": P((0.0, -44.0, -8.0))}
    if not draw:
        return pts
    lw = q.lw
    pal = q.P(M["skin"])
    front = nz((0.0, 0.0, 1.0))
    facing_away = front < -0.25
    behind = {s: D((s * 28.0, -4.0, -2.0)) < D((0.0, -4.0, -2.0)) - 1.0 for s in (-1.0, 1.0)}
    _ears(q, P, e, [s for s in (-1.0, 1.0) if behind[s]])
    # the crop: skull + spikes, one union (hair-coloured -- the face patch goes on top)
    groups = [_bp(P, (0.0, -6.0, -2.0), 31.0, 30.0, 31.0, 16)]
    for (dx, dy, dz, ln) in _SPIKES:
        k = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz)
        d = (dx * k, dy * k, dz * k)
        px = (d[1], -d[0], 0.0) if abs(d[2]) < 0.9 else (0.0, d[2], -d[1])
        pk = 1.0 / (math.hypot(px[0], math.hypot(px[1], px[2])) or 1.0)
        px = (px[0] * pk * 7.0, px[1] * pk * 7.0, px[2] * pk * 7.0)
        c0 = (d[0] * 24.0, -6.0 + d[1] * 24.0, -2.0 + d[2] * 24.0)
        tip = (d[0] * ln, -6.0 + d[1] * ln, -2.0 + d[2] * ln)
        groups.append([P(v_add(c0, px)), P(v_sub(c0, px)), P(tip)])
    F.hull_union(q, groups, M["hair"], 30.0, tension=0.55, rim=0.8)
    # neck (skin) under the crop
    F.hull_union(q, [F.blob_pts(proj, S["neck_base"], 2.4, 3.0, 2.4, 8) + F.blob_pts(proj, S["neck_top"], 2.2, 2.0, 2.2, 8)],
                 M["skin"], 6.0, rim=0.0)
    if not facing_away:
        # the face patch: brow to chin, cheek to cheek -- its top edge is the hairline, notched
        # by the spiky fringe (the crop shows through the notches)
        locks = _fringe_locks(q, P, nz, near)
        if locks:
            cr.save()
            x0, y0, x1, y1 = cr.clip_extents()
            cr.new_path()
            cr.rectangle(x0, y0, x1 - x0, y1 - y0)
            for lk in locks:
                core.polygon(cr, lk)
            cr.set_fill_rule(1)              # even-odd: everything but the locks
            cr.clip()
            cr.set_fill_rule(0)
        face, _ = F.hull_union(q, [_bp(P, (0.0, 2.0, 9.0), 27.0, 27.0, 21.0, 16), _bp(P, (0.0, 13.5, 13.0), 15.0, 10.5, 13.5, 10)],
                               M["skin"], 16.0, shadow=0.5)
        if locks:
            cr.restore()
            cr.save()
            face.add(cr)
            cr.clip()
            cr.new_path()
            for lk in locks:
                core.polygon(cr, lk)
            cr.set_line_width(q.lw * 1.6)
            cr.set_line_join(1)
            core.src(cr, q.P(M["hair"]).line)
            cr.stroke()
            cr.restore()
        lw0 = q.lw
        q.lw = lw0 * FACE_LINE
        if q.detail >= 1:                   # cheek blush
            bc = core.col(PIXIE_COLORS["blush"])
            for s in (-1.0, 1.0):
                if nz((s * 0.6, 0.1, 0.8)) > 0.1:
                    c = P((s * 15.0, 9.0, 22.0))
                    cr.set_source_rgba(bc[0], bc[1], bc[2], 0.22)
                    core.ellipse(cr, c[0], c[1], 3.4, 2.0)
                    cr.fill()
        eyes = []
        for s in (far, near):
            ec = F.eye_at(q, P, nz, s, e, eye_pos[s], 12.0 * HS, 13.5 * HS, iris=PIXIE_COLORS["eye"],
                          iris_hi=PIXIE_COLORS["eye_hi"], skin=PIXIE_COLORS["skin"], pupil="#1d120c",
                          crease=0.0, line=pal.line, normal=(s * 0.4, -0.05, 0.9), lash=1.4, lash_flick=1.0,
                          iris_size=0.70, pupil_aspect=0.85)
            eyes.append(ec or P(eye_pos[s]))
        pts["eyes"] = eyes
        # a tiny upturned button nose + the mouth (a lopsided sneer when closed)
        if nz((0.0, 0.2, 1.0)) > -0.2:
            n0, n1 = P((0.0, 3.0, 29.5)), P((0.0, 8.0, 31.0))
            B.detail_lines(cr, [[n0, n1, (n1[0] + 1.2 * near, n1[1] - 0.4)]], lw * 0.8, pal.line, 0.75, taper=(0.2, 1.0, 0.6))
            F.mouth_at(q, P, nz, (near * 1.5, 15.5, 25.0), 12.5 * HS, e, talk, skin=PIXIE_COLORS["skin"],
                       inside=PIXIE_COLORS["mouth"], tongue=PIXIE_COLORS["tongue"], line=pal.line)
        _brows(q, P, nz, e, near)
        q.lw = lw0
    else:
        pts["eyes"] = []
    _ears(q, P, e, [s for s in (-1.0, 1.0) if not behind[s]])
    return pts


def _ears(q, P, e, sides):
    """Long pointed leaf ears swept up and back out of the crop (they twitch; flatten a little
    when she sneers), a pink inner fold."""
    if not sides:
        return
    cr = q.cr
    lw = q.lw * 0.9
    outs, shapes, inner = [], [], []
    for s in sides:
        tw = 0.06 * math.sin(q.t * 3.1 + s) + 0.12 * B.wobble(q.t, math.floor(q.t / 2.5) * 2.5 + 0.7 * (s + 1), 7.0, 8.0)
        up = 1.0 - 0.25 * max(0.0, -e.brow_in)
        tip = (s * 58.0, -29.0 * up - tw * 16.0, -12.0)
        pts = [P((s * 25.0, -11.0, 0.0)), P((s * 40.0, -18.0 * up - tw * 6.0, -5.0)), P(tip),
               P((s * 46.0, -7.0 - tw * 4.0, -8.0)), P((s * 33.0, 2.0, -4.0)), P((s * 25.0, 5.0, -1.0))]
        sh, so = B.smooth_paths(cr, pts, lw, 0.75)
        shapes.append(sh)
        outs.append(so)
        if q.detail >= 1:
            inner.append([P((s * 29.0, -6.0, -1.0)), P((s * 41.0, -14.0 * up - tw * 5.0, -5.5)), P((s * 55.0, -24.0 * up - tw * 13.0, -10.0)),
                          P((s * 42.0, -6.0 - tw * 4.0, -7.0)), P((s * 31.0, 0.0, -3.0))])
    pal = q.P(q.M["skin"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["skin"], lw=lw, outline=False, size=10.0, rim=0.3)
    if inner:
        ic = core.col(PIXIE_COLORS["ear_in"])
        cr.new_path()
        for p in inner:
            core.smooth_closed(cr, p, 0.8)
        cr.set_source_rgba(ic[0], ic[1], ic[2], 0.55)
        cr.fill()


def _fringe_locks(q, P, nz, near):
    """The spiky fringe: four lock triangles (2D) flicked across the forehead toward the far
    side, from above the hairline down to just over the brows."""
    if nz((0.0, -0.4, 1.0)) < -0.1:
        return []
    sw = 0.8 * math.sin(q.t * 2.0)
    k = -near
    out = []
    for x0, x1, drop in ((-21.0, -10.0, 5.5), (-11.0, 0.0, 9.0), (-1.0, 10.0, 8.0), (9.0, 20.0, 5.0)):
        zc = lambda x: 22.0 * math.sqrt(max(0.05, 1.0 - (x / 30.0) ** 2))
        a = (x0, -31.0, zc(x0) - 4.0)
        b_ = (x1, -31.0, zc(x1) - 4.0)
        xm = (x0 + x1) * 0.5 + k * 5.5 + sw
        tip = (xm, -26.0 + drop + 0.004 * xm * xm * 0.0, zc(xm) + 2.0)
        out.append([P(a), P(tip), P(b_)])
    return out


def _brows(q, P, nz, e, near):
    cr = q.cr
    lwb = q.lw * 0.75
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.1:
            continue
        pts = F.brow_pts(P, s, e, near, 4.0, 21.0, -15.5, 27.0, 20.0, 12.0, 10.0)
        sh, so = B.taper_paths(cr, pts, 3.6, 1.4, lwb)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    hp = q.P(q.M["hair"])
    B.fill_outlines(cr, outs, hp.line)
    for sh in shapes:
        sh.add(cr)
    core.src(cr, core.mix(hp.lit, hp.shadow, 0.45))
    cr.fill()


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def lineup():
    return [B.LineupItem("pixie", lambda cr, x, y, sc: draw_pixie(cr, x, y, sc, PixiePose(facing=1, buzz=0.0), t=0.4), 70.0)]


def sheet_items():
    from .crowd import crystal_hold, demo_thumb
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    for label, pose in (("3/4 left", PixiePose(facing=-1, hover=20)), ("front", PixiePose(facing=0, hover=20)),
                        ("3/4 right", PixiePose(facing=1, hover=20)), ("profile", PixiePose(facing=1, turn=0.75, hover=20)),
                        ("back", PixiePose(facing=2, hover=20)),
                        ("wings still, hand on hip", PixiePose(facing=1, turn=-0.3, buzz=0.0, hover=20, near=Arm("hip"), far=Arm("hip")))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 260, 330, floor=300)
            draw_pixie(cr, 130, 312, 2.4, p, neutral, t=0.4)
        add(label, 260, 330, fn, "turnaround & faces (x2.4)")

    moods = [("SNEER (default)", dict()), ("'Ew.' (talk)", dict(talk=0.8)), ("disgusted", dict(mood="sneer", smile=-0.6, talk=0.3)),
             ("bored", dict(mood="bored")), ("surprised", dict(mood="surprised", head_nod=0.0)), ("smug", dict(mood="skeptical", smile=0.3)),
             ("laugh", dict(laugh=1.0)), ("front: sneer", dict(facing=0)), ("3/4 left: talk", dict(facing=-1, talk=0.7))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        pose = PixiePose(facing=facing, turn=-0.3 if facing == 1 else (0.3 if facing == -1 else 0.0), hover=0.0, **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 200, 200)
            s0, c0 = core.frame(4, 4)
            r0 = draw_pixie(c0, 0.0, 0.0, 5.0, p, neutral, t=0.4)
            draw_pixie(cr, 100 - r0.head[0], 112 - r0.head[1], 5.0, p, neutral, t=0.4)
        add(label, 200, 200, fn, "turnaround & faces (x2.4)")

    acts = [("filming (crystal up, back of it)", PixiePose(facing=1, turn=-0.4, hover=40, mood="sneer", far=Arm("hip"),
                                                        near=Arm("raise_crystal_film", hold=crystal_hold(face=-1.0, size=1.7)))),
            ("filming, seen from behind", PixiePose(facing=2, turn=-0.4, hover=40,
                                                    near=Arm("raise_crystal_film", hold=crystal_hold(face=1.0, thumb=demo_thumb, size=1.7)))),
            ("lowers it: 'Ew.'", PixiePose(facing=1, turn=-0.3, hover=40, talk=0.8, mood="sneer", far=Arm("hip"),
                                           near=Arm("lower_crystal", hold=crystal_hold(face=0.6, glow=0.4, size=1.7)))),
            ("points, sneering", PixiePose(facing=1, turn=-0.2, hover=40, talk=0.5, near=Arm("point"), far=Arm("hip"))),
            ("arms crossed", PixiePose(facing=0, turn=0.3, hover=40, mood="skeptical", near=Arm("arms_crossed"), far=Arm("arms_crossed")))]
    for label, pose in acts:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 300, 380, "square", floor=350)
            draw_pixie(cr, 150, 362, 2.4, p, L["square"], t=0.4)
        add(label, 300, 380, fn, "actions & lights")
    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 170, 260, name, floor=232)
            draw_pixie(cr, 85, 244, 1.8, PixiePose(facing=-1, turn=0.25, hover=10, far=Arm("hip")), L[name], t=0.4)
        add(name, 170, 260, fn, "actions & lights")
    for label, sc in (("film: x1 (90 px)", 1.0), ("x0.7", 0.7)):
        def fn(cr, sc=sc):
            F.sheet_bg(cr, 170, 260, "square", floor=232)
            hold = crystal_hold(face=-1.0, size=1.7)
            draw_pixie(cr, 85, 244, sc, PixiePose(facing=-1, hover=60, near=Arm("raise_crystal_film", hold=hold)),
                       L["square"], t=0.4)
        add(label, 170, 260, fn, "actions & lights")
    return items
