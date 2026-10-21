"""dwarf.py -- THE DWARF labourer (S7): walks in from his shift, sits, DRAGS a second bench over,
takes bread. Also the template for the crowd's dwarves.

Stout and wide: a big ruddy potato nose, bushy brows over small kind eyes, a great chestnut
beard ending in two braids bound with brass rings, soot smudges, a miner's leather cap with a
little brass candle-lamp on its front. He wears a sturdy orange-brown tanned-leather work vest
(his signature accent: brass buckles, tool loops holding a hammer and tongs) over a slate wool
tunic with the sleeves rolled up, a broad belt, dark breeches and heavy boots. Silhouette: a
barrel on short legs with a triangle of beard -- seated on the bench his boots dangle.

    from film.lib import characters as ch
    p = ch.DwarfPose(facing=-1, walk=1, phase=..., near=ch.Arm("drag"), far=ch.Arm("drag"), drag=1.0)
    rig = ch.draw_dwarf(cr, x, ground_y, 0.9, p, ch.LIGHTS["golden"], t)
    rig.points["grip"]      # where his hands hold the bench (caller coords)

Scale 1.0: standing, ground -> crown = DWARF_HEIGHT = 300 px (cap and lamp excluded).
Anchor (x, y) = ground point below the pelvis (below the seat when sitting).
"""

import math
from dataclasses import dataclass

from .. import core, fx
from ..core import clamp, lerp
from . import base as B
from . import _folk as F
from .base import Mat, Path, m_vec, v_add, v_lerp
from .dragon import Arm

__all__ = ["DwarfPose", "DwarfRig", "draw_dwarf", "dwarf_walk_phase", "DWARF_HEIGHT", "DWARF_COLORS",
           "DWARF_GESTURES", "dwarf_mats", "dwarf_grip"]

DWARF_HEIGHT = 300.0
HS = 1.3
TAU = math.tau

DWARF_COLORS = {
    "skin": "#CF8F6C",
    "nose": "#D9735C",       # ruddy
    "beard": "#5E3A24",      # chestnut
    "beard_hi": "#8A5A3A",
    "ring": "#C9A04A",       # brass beard rings
    "cap": "#4A3324",        # miner's leather cap
    "lamp": "#C9A04A",       # brass candle-lamp
    "candle": "#EFE6D2",
    "vest": "#B3622A",       # orange-brown tanned leather -- the signature accent
    "buckle": "#C9A04A",
    "tunic": "#5D6C78",      # slate wool
    "breeches": "#4A3A2E",
    "boots": "#382820",
    "iron": "#6E7377",       # hammer head, tongs
    "wood": "#8A6038",       # hammer handle
    "soot": "#2A2420",
    "eye": "#5A7FA0",        # blue-grey
    "eye_hi": "#A8C8E0",
    "mouth": "#4A2228",
    "tongue": "#C4566A",
}

DWARF_BUILD = F.Build(
    pelvis_h=110.0, hip_w=27.0, thigh=56.0, shin=50.0, ankle_h=16.0,
    sh_y=116.0, sh_z=0.0, sh_w=62.0, upper_arm=62.0, forearm=58.0, hand_len=50.0,
    neck_y=124.0, neck_z=8.0, neck_len=8.0, head_up=20.0, head_fwd=10.0,
    hunch=0.25, hunch_fwd=10.0, stride=120.0, lift=16.0, bob=4.0, breath=0.24,
    sit_drop=10.0, sit_back=6.0, sway=1.6, knee_out=0.3,
    fit=0.949)   # scale 1.0 -> base.CAST_HEIGHTS (measured on the lineup)

_MATS = {}


def dwarf_mats(palette=None):
    key = tuple(sorted(palette.items())) if palette else ()
    m = _MATS.get(key)
    if m is None:
        C = dict(DWARF_COLORS)
        if palette:
            C.update(palette)
        m = _MATS[key] = {
            "skin": Mat.of(C["skin"], sss=0.4),
            "nose": Mat.of(C["nose"], sss=0.5),
            "beard": Mat.of(C["beard"], sheen=0.2),
            "ring": Mat.of(C["ring"], sheen=0.8),
            "cap": Mat.of(C["cap"], sheen=0.3),
            "lamp": Mat.of(C["lamp"], sheen=0.8),
            "vest": Mat.of(C["vest"], sheen=0.35, line_k=0.5),
            "buckle": Mat.of(C["buckle"], sheen=0.8),
            "tunic": Mat.of(C["tunic"], shadow_k=1.1),
            "breeches": Mat.of(C["breeches"], shadow_k=1.1),
            "boots": Mat.of(C["boots"], sheen=0.35),
            "iron": Mat.of(C["iron"], sheen=0.6),
            "wood": Mat.of(C["wood"]),
            "C": C,
        }
    return m


@dataclass
class DwarfPose(F.FolkPose):
    """FolkPose (see _folk.FolkPose / DragonPose) plus:
    drag      0..1 dragging a bench: leans back, digs his heels in (use Arm("drag") on both arms
              and walk backwards: phase decreasing as he goes)
    grip      (forward, height) of the bench end he holds, body px from his anchor
    lamp_lit  the candle on his cap is lit (a tiny warm flame -- e.g. S8 at night)
    soot      0..1 soot smudges on face and vest
    palette   colour overrides (crowd dwarves): keys of DWARF_COLORS
    cap       draw the miner's cap
    """
    mood: object = "neutral"
    drag: float = 0.0
    grip: tuple = (88.0, 125.0)
    lamp_lit: bool = False
    soot: float = 1.0
    palette: dict = None
    cap: bool = True


DwarfRig = F.FolkRig


def _g_drag(q, sk, side, arm):
    """Both hands low and forward, gripping the bench end (pose.grip)."""
    fwd, h = q.pose.grip
    return F.G((side * 26.0, -h, fwd), "grip", 0.5, "front", (side * 1.0, 0.6, -0.4), "in")


def _g_thumbs_belt(q, sk, side, arm):
    """Thumbs hooked in his belt (contented, standing about)."""
    pel = q.S["pelvis"]
    return F.G(v_add(pel, (side * 30.0, -26.0, 34.0)), "relaxed", 0.9, "front", (side * 1.0, 0.3, -0.6), "fwd")


DWARF_GESTURES = dict(F.GESTURES)
DWARF_GESTURES.update({"drag": _g_drag, "thumbs_belt": _g_thumbs_belt})


def dwarf_walk_phase(distance_px, scale=1.0, yaw=1.0):
    return F.walk_phase(DWARF_BUILD, distance_px, scale, yaw)


def dwarf_grip(pose, scale=1.0, yaw=None):
    """Where his hands hold the bench while dragging, relative to his anchor, in screen px
    (yaw: his body yaw, default from the pose): put the bench's near end here."""
    y = F.yaw_of(pose) if yaw is None else yaw
    fwd, h = pose.grip
    from .base import Proj
    p = Proj(y, pose.elev).xy((0.0, -h, fwd))
    k = scale * DWARF_BUILD.fit
    return (p[0] * k, p[1] * k)


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def _skeleton(q):
    """The generic biped skeleton, plus the drag: he leans back, heels dug in ahead of him."""
    p = q.pose
    if p.drag > 0:
        q.pose = p.with_(lean=p.lean - 0.75 * p.drag, stance=p.stance)
    S = F.skeleton(q)
    q.pose = p
    if p.drag > 0:
        k = clamp(p.drag)
        for f in S["feet"]:
            # heels pushed forward: the planted feet ahead of the pelvis
            f["ankle"] = v_add(f["ankle"], (0.0, 0.0, 16.0 * k))
            f["knee"], f["ankle"] = B.ik3(f["hip"], f["ankle"], q.b.thigh, q.b.shin, (f["side"] * 0.3, 0.1, 1.0))
            f["ground"] = (f["ankle"][0], 0.0, f["ankle"][2])
        S["knee"] = [S["feet"][0]["knee"], S["feet"][1]["knee"]]
    return S


def draw_dwarf(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw the dwarf with its anchor at (x, y). Returns a DwarfRig (points: "grip" while
    dragging, "lamp" the candle flame). parts: as draw_orc."""
    pose = pose or DwarfPose()
    q = F.begin(cr, x, y, scale, pose, light, t, detail, DWARF_BUILD, dwarf_mats(pose.palette), parts, skel=_skeleton,
                height=DWARF_HEIGHT)
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far, DWARF_GESTURES) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    if q.want("body") and pose.shadow:
        F.contact(q, 62.0)
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
    if "lamp" in head:
        rig.points["lamp"] = head["lamp"]
    if pose.drag > 0:
        fwd, h = pose.grip
        rig.points["grip"] = q.proj.xy((0.0, -h, fwd))
    return F.end(q, rig)


def _hand_guess(q, A):
    el, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    d = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    return B.HandFrame(wr[0] + d[0] * 22, wr[1] + d[1] * 22, math.atan2(d[1], d[0]), 1.0, [], wr, False)


# ----------------------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------------------

def _legs(q):
    """Short breeched legs (one union) and heavy boots (one union) with folded-down tops."""
    M = q.M
    F.legs(q, [24.0, 18.0, 14.0], M["breeches"], 36.0)
    shp, pal = F.feet(q, M["boots"], size=26.0, length=44.0, width=16.0, height=19.0, shaft=30.0, shaft_r=17.0)
    if q.detail >= 1:                       # the boot tops' fold + the sole line
        lines = []
        for f in q.S["feet"]:
            top = v_lerp(f["ankle"], f["knee"], 30.0 / q.b.shin)
            pts = F.front_arc(q, top, 17.5, 17.5, 7)
            lines.append(pts)
        B.detail_lines(q.cr, lines, q.lw * 1.2, core.tint(pal.lit, 0.3), 0.6, taper=(0.5, 1.0, 0.5))


def _torso(q):
    """Slate tunic (barrel belly), the orange-brown leather work vest open at the front with
    brass-buckled straps, a broad belt, tool loops with a hammer and tongs, soot."""
    cr, S, proj, M = q.cr, q.S, q.proj, q.M
    T = S["T"]
    br, h = S["br"], S["hunch"]
    sit = q.sit
    pel = S["pelvis"]
    kn = v_lerp(S["knee"][0], S["knee"][1], 0.5)
    hem_c = v_lerp(v_add(pel, (0.0, 22.0, 4.0)), v_add(v_lerp(pel, kn, 0.45), (0.0, 8.0, 6.0)), clamp(sit / 0.7))
    rings = [
        (T((0.0, -110.0 + 5 * h, 6.0 + 6 * h)), 44.0, 32.0),        # 0 over the shoulders
        (T((0.0, -96.0 + 3 * h, 4.0)), 66.0 + br * 0.8, 42.0),      # 1 shoulders
        (T((0.0, -70.0, 12.0)), 66.0 + br, 50.0 + br),              # 2 chest
        (T((0.0, -38.0, 16.0)), 64.0, 52.0),                        # 3 barrel belly
        (T((0.0, -12.0, 10.0)), 58.0, 46.0),                        # 4 belt
        (hem_c, 58.0 + 6 * sit, 44.0),                              # 5 hem
    ]
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=24.0)
    hem = F.hem_curve(q, *rings[-1], n=8)
    tun, tpal = F.smooth_shape(q, left + hem + right[::-1] + top, M["tunic"], 90.0, shadow=0.6)
    # the vest: same rings slightly larger, over everything but a strip down the front
    vr = [(c, a + 2.5, cz + 2.5) for (c, a, cz) in rings[:5]] + [(v_add(rings[4][0], (0.0, 14.0, 0.0)), rings[4][1] + 3.0, rings[4][2] + 3.0)]
    vl, vrt = F.ring_edges(q, vr)
    vtop = F.shoulder_top(q, vr[0], neck_r=26.0)
    vhem = F.hem_curve(q, *vr[-1], n=6)
    vest, vpal = F.smooth_shape(q, vl + vhem + vrt[::-1] + vtop, M["vest"], 90.0, shadow=0.6, rim=0.8)
    front = proj.depth((0.0, 0.0, 1.0))
    cr.save()
    vest.add(cr)
    cr.clip()
    if front > 0.0:
        # the vest is open down the front: the tunic shows in a strip between its edges
        edgeL, edgeR = [], []
        for k, (c, a, cz) in enumerate(vr):
            w = (0.32, 0.36, 0.30, 0.26, 0.24, 0.26)[k]
            edgeL.append(proj.xy((c[0] + math.sin(-w) * a * 1.02, c[1], c[2] + math.cos(-w) * cz * 1.02)))
            edgeR.append(proj.xy((c[0] + math.sin(w) * a * 1.02, c[1], c[2] + math.cos(w) * cz * 1.02)))
        cr.new_path()
        core.smooth_open(cr, edgeL)
        core.smooth_open(cr, edgeR[::-1], move=False)
        cr.close_path()
        strip = Path(cr)
        strip.add(cr)
        core.src(cr, tpal.shadow)
        cr.fill()
        kx, ky = B.local_dir(cr, q.light.direction)
        strip.add(cr, kx * 6.0, ky * 6.0)
        core.src(cr, core.mix(tpal.lit, tpal.shadow, 0.25))
        cr.fill()
        B.detail_lines(cr, [edgeL, edgeR], q.lw * 1.2, vpal.line, 0.95, taper=(0.8, 1.0, 0.8))
        # two brass-buckled straps across the opening
        if q.detail >= 1:
            straps = []
            for k in (1.4, 2.6):
                i = int(k)
                u = k - i
                a_ = core.lerp_pt(edgeL[i], edgeL[i + 1], u)
                b_ = core.lerp_pt(edgeR[i], edgeR[i + 1], u)
                straps.append((a_, b_))
            sp = q.P(M["vest"])
            for (a_, b_) in straps:
                cr.new_path()
                core.tapered(cr, [(a_[0] - 3, a_[1]), b_], 7.5, 7.5, cap=False)
                core.src(cr, core.mix(sp.lit, sp.shadow, 0.45))
                cr.fill()
            bk = q.P(M["buckle"])
            for (a_, b_) in straps:
                m = core.lerp_pt(a_, b_, 0.55)
                cr.new_path()
                core.rounded_rect(cr, m[0] - 5.5, m[1] - 6.0, 11.0, 12.0, 2.5)
                B.flat(cr, Path(cr), bk.lit, q.lw * 0.6, bk.line)
    if q.detail >= 2:
        # stitched seams down the vest panels + soot on the leather
        lines = []
        for phi in (-0.9, 0.9):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.15:
                lines.append([proj.xy(v_add(vr[k][0], (math.sin(phi) * vr[k][1], 0.0, math.cos(phi) * vr[k][2]))) for k in (1, 2, 3, 4)])
        if lines:
            cr.set_dash([4.0, 3.0])
            for ln in lines:
                cr.new_path()
                core.smooth_open(cr, ln)
            cr.set_line_width(q.lw * 0.6)
            core.src(cr, vpal.line, 0.6)
            cr.stroke()
            cr.set_dash([])
    if q.pose.soot > 0 and q.detail >= 1:
        c2, a2, z2 = vr[2]
        for (phi, dy, r) in ((0.8, 4.0, 9.0), (-0.65, 20.0, 7.0)):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.2:
                p0 = proj.xy(v_add(c2, (math.sin(phi) * a2, dy, math.cos(phi) * z2)))
                B.occlusion(cr, p0[0], p0[1], r * 1.6, r, DWARF_COLORS["soot"], 0.35 * q.pose.soot)
    cr.restore()
    # broad belt + brass buckle, and the tool loops (hammer, tongs) on his hips
    c3, a3, z3 = rings[3]
    c4, a4, z4 = rings[4]
    bc = v_lerp(c3, c4, 0.7)
    F.belt(q, bc, lerp(a3, a4, 0.7) + 4.0, lerp(z3, z4, 0.7) + 4.0, 7.5, M["vest"], M["buckle"], 10.0)
    _tools(q, bc, lerp(a3, a4, 0.7) + 4.0, lerp(z3, z4, 0.7) + 4.0)


def _tools(q, c, a, cz):
    """A hammer and a pair of tongs hanging from loops on his belt (they swing a little)."""
    cr, proj, M = q.cr, q.proj, q.M
    sw = 0.08 * math.sin(q.t * 1.6) + 0.1 * q.S["walk"] * math.sin(TAU * q.S["wc"].phase * 2)
    for (phi, kind) in ((1.15, "hammer"), (-1.2, "tongs")):
        p = (c[0] + math.sin(phi) * a, c[1] + 2.0, c[2] + math.cos(phi) * cz)
        if proj.depth((math.sin(phi), 0.0, math.cos(phi))) < -0.35:
            continue
        top = proj.xy(p)
        ang = math.pi / 2 + sw + (0.1 if kind == "hammer" else -0.1)
        L = 46.0 if kind == "hammer" else 40.0
        bot = (top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L)
        if kind == "hammer":
            hs, ho = B.taper_paths(cr, [top, bot], 5.5, 5.0, q.lw * 0.8)
            q.shade(hs, M["wood"], lw=q.lw * 0.8, outline=ho, size=5.0, rim=0.0)
            nx, ny = -math.sin(ang), math.cos(ang)
            head = [(bot[0] + nx * 11, bot[1] + ny * 11 - 2), (bot[0] - nx * 9, bot[1] - ny * 9 - 2),
                    (bot[0] - nx * 9, bot[1] - ny * 9 + 9), (bot[0] + nx * 11, bot[1] + ny * 11 + 9)]
            hp, hpo = B.smooth_paths(cr, head, q.lw * 0.8, 0.3)
            q.shade(hp, M["iron"], lw=q.lw * 0.8, outline=hpo, size=9.0, rim=0.6)
        elif q.detail >= 1:
            ip = q.P(M["iron"])
            for d in (-3.0, 3.0):
                nx, ny = -math.sin(ang), math.cos(ang)
                a0 = (top[0] + nx * d * 0.4, top[1] + ny * d * 0.4)
                b0 = (bot[0] + nx * d, bot[1] + ny * d)
                B.detail_lines(cr, [[a0, b0]], q.lw * 1.5, ip.line, 1.0, taper=(1.0, 1.0, 0.6))
        # the loop it hangs from
        if q.detail >= 1:
            core.src(cr, q.P(M["vest"]).line)
            core.ellipse(cr, top[0], top[1], 5.0, 3.0)
            cr.set_line_width(q.lw * 0.8)
            cr.stroke()


def _arm(q, A):
    """Rolled-up tunic sleeve, a thick hairy forearm and a big hand."""
    cr, M, proj = q.cr, q.M, q.proj
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fm = core.lerp_pt(el, wr, 0.38)
    arm, apal = F.limb(q, [sh, el, fm, wr], [19.0, 14.5, 16.0, 12.0], M["skin"], 30.0)
    cut = core.lerp_pt(el, wr, 0.12)
    sl, spal = F.limb(q, [sh, el, cut], [22.0, 18.5, 18.5], M["tunic"], 34.0)
    if q.detail >= 1:
        F.band(q, sl, core.lerp_pt(el, cut, -0.2), (cut[0], cut[1]), 19.0, M["tunic"], 22.0)
        if q.detail >= 2:                   # forearm hair
            ux, uy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
            nx, ny = -uy, ux
            lines = []
            for k in range(4):
                m = core.lerp_pt(el, wr, 0.3 + 0.15 * k)
                lines.append([(m[0] + nx * 12, m[1] + ny * 12), (m[0] + nx * 15 + ux * 5, m[1] + ny * 15 + uy * 5)])
            B.detail_lines(cr, lines, q.lw * 0.8, apal.line, 0.5)
    return F.hand(q, A, M["skin"], size=50.0, finger_w=1.4, palm_w=1.3, finger_len=0.92)


# ----------------------------------------------------------------------------------------
# head (head space x HS)
# ----------------------------------------------------------------------------------------

def _bp(P, c, rx, ry, rz, n=14):
    return F.ellipsoid2d(P, c, rx, ry, rz, n)


def _head(q, draw=True):
    cr, M, pose, S, proj = q.cr, q.M, q.pose, q.S, q.proj
    e = F.expr_of(pose)
    P, nz, D, W = F.head_xf(q, HS)
    hyaw = S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    far = -near
    talk = clamp(pose.talk)
    jaw_open = clamp(talk * 0.85 + e.open * 0.9)
    pts = {"center": P((0.0, 0.0, 0.0)), "mouth": P((0.0, 21.0, 30.0)), "nose": P((0.0, 5.0, 38.0)),
           "eyes": [P((s * 14.0, -6.0, 27.0)) for s in (far, near)], "top": P((0.0, -46.0, -4.0))}
    lamp_p = P((0.0, -49.0, 32.0))
    pts["lamp"] = lamp_p
    if not draw:
        return pts
    lw = q.lw
    pal = q.P(M["skin"])
    facing_away = nz((0.0, 0.0, 1.0)) < -0.25
    behind = {s: D((s * 30.0, -2.0, -4.0)) < D((0.0, -2.0, -4.0)) - 3.0 for s in (-1.0, 1.0)}
    _ear(q, P, [s for s in (-1.0, 1.0) if behind[s]])
    if not facing_away:                     # hair at the nape, behind the skull
        F.hull_union(q, [_bp(P, (0.0, -6.0, -16.0), 29.0, 22.0, 18.0, 12)], M["beard"], 30.0, rim=0.6)
    # ---- head union: neck + cranium + cheeks
    nb, nt = S["neck_base"], S["neck_top"]
    skull, _ = F.hull_union(q, [F.blob_pts(proj, nb, 22.0, 6.0, 18.0) + F.blob_pts(proj, nt, 20.0, 6.0, 17.0),
                                _bp(P, (0.0, -14.0, -4.0), 30.0, 30.0, 30.0, 16), _bp(P, (0.0, 6.0, 8.0), 30.0, 18.0, 24.0)],
                            M["skin"], 70.0)
    # nape hair under the cap (over the skull when we see his back)
    if facing_away:
        F.hull_union(q, [_bp(P, (0.0, -8.0, -14.0), 30.0, 22.0, 18.0, 14)], M["beard"], 30.0, rim=0.6)
    else:
        # beard (from the sideburns down over his chest, two braids) -- over the jaw
        _beard(q, P, W, nz, e, jaw_open, facing_away)
    if not facing_away:
        eyes = []
        for s in (far, near):
            ec = F.eye_at(q, P, nz, s, e, (s * 14.0, -6.0, 27.0), 9.0 * HS, 10.5 * HS, iris=DWARF_COLORS["eye"],
                          iris_hi=DWARF_COLORS["eye_hi"], skin=M["C"]["skin"], pupil="#1d120c", lid_add=0.12,
                          crease=0.3 if q.detail >= 2 else 0.0, bags=0.4 if q.detail >= 2 else 0.0, line=pal.line,
                          normal=(s * 0.4, -0.1, 0.9))
            eyes.append(ec or P((s * 14.0, -6.0, 27.0)))
        pts["eyes"] = eyes
        _nose(q, P, nz)
        _moustache(q, P, nz, e, jaw_open)
        _brows(q, P, nz, e, near, [skull])
        if pose.soot > 0 and q.detail >= 1:
            for (x, y, z, r) in ((near * 20.0, 6.0, 22.0, 7.0), (-near * 6.0, -24.0, 28.0, 5.0)):
                if nz((x / 30.0, y / 30.0, 0.8)) > 0.1:
                    c = P((x, y, z))
                    B.occlusion(cr, c[0], c[1], r * HS * 1.4, r * HS, DWARF_COLORS["soot"], 0.32 * pose.soot)
    else:
        pts["eyes"] = []
    _ear(q, P, [s for s in (-1.0, 1.0) if not behind[s]])
    if pose.cap:
        _cap(q, P, nz, D)
    return pts


def _ear(q, P, sides):
    if not sides:
        return
    groups = [_bp(P, (s * 31.0, -2.0, -4.0), 6.0, 10.0, 7.0, 10) for s in sides]
    F.hull_union(q, groups, q.M["skin"], 10.0, rim=0.5)


def _beard(q, P, W, nz, e, jaw_open, facing_away):
    """The great beard: sideburns into a full beard hanging over the chest (gravity: its tip in
    body space), ending in two braids with brass rings. One union, ink strands."""
    cr, proj, S = q.cr, q.proj, q.S
    sw = B.chain(q.t, 3, freq=0.38, delay=0.15, amp=0.4, seed=q.pose.seed + 8)
    walk_sw = S["walk"] * 3.0 * math.sin(TAU * S["wc"].phase * 2 + 0.5)
    jaw = [(s * x, y, z) for s in (-1.0, 1.0) for (x, y, z) in ((29.0, 2.0, 0.0), (27.0, 12.0, 8.0), (22.0, 22.0, 17.0))]
    jaw += [(0.0, 28.0, 26.0), (0.0, 20.0, 31.0), (0.0, 25.0, 29.0)]
    pts = [P(p) for p in jaw]
    chin = W((0.0, 26.0, 24.0))
    tip = v_add(chin, (sw[1] * 10.0 + walk_sw, 40.0 - 2.0 * jaw_open, 6.0))
    for (dx, dy) in ((-20.0, -8.0), (20.0, -8.0), (-12.0, 4.0), (12.0, 4.0)):
        pts.append(proj.xy(v_add(tip, (dx, dy, 0.0))))
    shp, pal = F.hull_union(q, [pts], q.M["beard"], 40.0, rim=0.7)
    braids = []
    for s in (-1.0, 1.0):
        b0 = v_add(tip, (s * 8.0, 0.0, 2.0))
        b1 = v_add(tip, (s * 9.0 + sw[2] * 6.0, 16.0, 4.0))
        b2 = v_add(tip, (s * 8.0 + sw[2] * 12.0, 30.0, 5.0))
        braids.append([proj.xy(b0), proj.xy(b1), proj.xy(b2)])
    outs, shapes = [], []
    for bp_ in braids:
        sh, so = B.taper_paths(cr, bp_, 9.0, 5.0, q.lw * 0.85)
        shapes.append(sh)
        outs.append(so)
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["beard"], lw=q.lw * 0.85, outline=False, size=8.0, rim=0.5)
    rp = q.P(q.M["ring"])
    if q.detail >= 1:
        for bp_ in braids:
            m = core.lerp_pt(bp_[0], bp_[1], 0.6)
            cr.new_path()
            core.ellipse(cr, m[0], m[1], 5.5, 3.5)
            B.flat(cr, Path(cr), rp.lit, q.lw * 0.6, rp.line)
        # strands
        lines = []
        for s in (-0.6, -0.2, 0.2, 0.6):
            a = P((s * 26.0, 14.0, 20.0))
            b_ = proj.xy(v_add(tip, (s * 16.0, -6.0, 0.0)))
            lines.append([a, ((a[0] + b_[0]) / 2 + s * 3, (a[1] + b_[1]) / 2), b_])
        B.detail_lines(cr, lines, q.lw * 0.8, pal.line, 0.45, taper=(0.1, 1.0, 0.2))
    return shp


def _moustache(q, P, nz, e, jaw_open):
    """Big drooping moustache under the nose; the mouth (a dark gap) shows under it when he
    talks; corners lift with the smile."""
    cr = q.cr
    if nz((0.0, 0.2, 1.0)) < -0.2:
        return
    sm = e.smile
    if jaw_open > 0.04:
        m = P((0.0, 21.0, 31.0))
        cr.new_path()
        core.ellipse(cr, m[0], m[1] + 2.0 * jaw_open, 7.0 * HS, (2.0 + 5.0 * jaw_open) * HS)
        core.src(cr, B.pal(q.light, DWARF_COLORS["mouth"]).lit)
        cr.fill()
    outs, shapes = [], []
    for s in (-1.0, 1.0):
        if nz((s * 0.5, 0.2, 0.8)) < -0.2:
            continue
        sp = [P((s * 2.0, 13.0, 34.0)), P((s * 12.0, 15.0 - sm * 3.0, 31.0)), P((s * 22.0, 22.0 - sm * 8.0, 23.0))]
        sh, so = B.taper_paths(cr, sp, 13.0, 4.0, q.lw * 0.85)
        shapes.append(sh)
        outs.append(so)
    pal = q.P(q.M["beard"])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["beard"], lw=q.lw * 0.85, outline=False, size=10.0, rim=0.6)


def _nose(q, P, nz):
    """A big ruddy potato nose."""
    if nz((0.0, 0.0, 1.0)) < -0.3:
        return
    pts = _bp(P, (0.0, 5.0, 33.0), 11.5, 10.0, 10.0, 14) + _bp(P, (0.0, -6.0, 30.0), 6.0, 7.0, 6.0, 10)
    shp, so, _ = B.hull_paths(q.cr, pts, q.lw * 0.9, 0.85)
    npal = q.shade(shp, q.M["nose"], lw=q.lw * 0.9, outline=so, size=20.0, rim=0.5)
    lines = []
    for s in (-1.0, 1.0):
        if nz((s * 0.5, 0.4, 0.75)) > -0.05:
            lines.append([P((s * 4.0, 11.0, 39.0)), P((s * 8.0, 10.5, 37.0))])
    if lines:
        B.detail_lines(q.cr, lines, q.lw * 1.4, npal.line, 0.8, taper=(1.0, 0.8, 0.3))
    if q.detail >= 2:
        B.sheen(q.cr, *P((-3.0, 1.0, 42.0)), 4.0, 2.6, alpha=0.4)


def _brows(q, P, nz, e, near, clip):
    """Huge bushy brows (beard hair), one union, pushed by the Expr."""
    cr = q.cr
    lwb = q.lw * 0.85
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.15:
            continue
        pts = F.brow_pts(P, s, e, near, 3.0, 28.0, -17.5, 32.0, 22.0, 13.0, 11.0)

        def prof(u):
            return 15.0 * (0.7 + 0.3 * math.sin(math.pi * u)) * (1.0 - 0.3 * u)

        sh, so = B.taper_paths(cr, pts + [P((s * 32.0, -12.0 - e.brow_out * 6.0, 18.0))], 14.0, 8.0, lwb, profile=prof)
        shapes.append(sh)
        outs.append(so)
    if not shapes:
        return
    B.fill_outlines(cr, outs, q.P(q.M["beard"]).line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M["beard"], lw=lwb, outline=False, size=11.0, rim=0.6)


def _cap(q, P, nz, D):
    """The miner's leather cap (a round skull cap with a stiff band) and the brass candle-lamp
    on its front -- lit, a tiny warm flame (kept for kindness: S8 at night)."""
    cr = q.cr
    # dome on a stiff band (F.dome_cap: the back of the cap never covers his face when he
    # throws his head back)
    shp, pal, _arc = F.dome_cap(q, P, D, (0.0, -24.0, -6.0), 33.0, 24.0, q.M["cap"], 50.0, brim=1.5, rim=0.9)
    if q.detail >= 1:                       # the band + a seam over the crown
        band = F.front_arc(q, F.head_xf(q, HS)[3]((0.0, -24.0, -6.0)), 34.5 * HS, 34.5 * HS, 11)
        B.detail_lines(cr, [band], q.lw * 1.2, pal.line, 0.8, taper=(0.4, 1.0, 0.4))
        if q.detail >= 2:
            B.detail_lines(cr, [[P((0.0, -42.0, 20.0)), P((0.0, -48.0, 0.0)), P((0.0, -42.0, -24.0))]], q.lw * 0.8, pal.line, 0.45)
    if nz((0.0, -0.3, 1.0)) > -0.2:
        # brass holder + candle stub on the front
        hb = P((0.0, -32.0, 31.0))
        hp_ = q.P(q.M["lamp"])
        cr.new_path()
        core.rounded_rect(cr, hb[0] - 7.5 * HS, hb[1] - 4.0 * HS, 15.0 * HS, 9.0 * HS, 3.0)
        B.flat(cr, Path(cr), hp_.lit, q.lw * 0.7, hp_.line)
        c0, c1 = P((0.0, -35.0, 32.0)), P((0.0, -44.0, 32.0))
        cs, cso = B.taper_paths(cr, [c0, c1], 7.0 * HS, 6.0 * HS, q.lw * 0.7, cap=False)
        q.shade(cs, Mat.of(DWARF_COLORS["candle"], sss=0.5), lw=q.lw * 0.7, outline=cso, size=6.0, rim=0.0)
        if q.pose.lamp_lit:
            f = P((0.0, -49.0, 32.0))
            flick = 1.0 + 0.12 * math.sin(q.t * 23.0) + 0.08 * math.sin(q.t * 37.0)
            fx.glow(cr, f[0], f[1], 22.0 * HS, "#ffb347", 0.35)
            cr.new_path()
            cr.move_to(f[0], f[1] - 7.0 * HS * flick)
            cr.curve_to(f[0] + 3.5 * HS, f[1] - 2.0 * HS, f[0] + 3.0 * HS, f[1] + 3.5 * HS, f[0], f[1] + 3.5 * HS)
            cr.curve_to(f[0] - 3.0 * HS, f[1] + 3.5 * HS, f[0] - 3.5 * HS, f[1] - 2.0 * HS, f[0], f[1] - 7.0 * HS * flick)
            core.src(cr, "#ffd27a")
            cr.fill()
            core.src(cr, "#fff6d8")
            core.ellipse(cr, f[0], f[1] + 1.0 * HS, 1.3 * HS, 2.2 * HS)
            cr.fill()


# ----------------------------------------------------------------------------------------
# character sheet + line-up
# ----------------------------------------------------------------------------------------

def _sheet_bread(cr, frame):
    cr.save()
    cr.rotate(-frame.angle)
    core.src(cr, "#7a4a22")
    core.ellipse(cr, 0, -4, 16, 11)
    cr.fill()
    core.src(cr, "#c88a48")
    core.ellipse(cr, 0, -6, 14, 9)
    cr.fill()
    core.src(cr, "#f3e2bd")
    core.ellipse(cr, 5, -3, 6, 5)
    cr.fill()
    cr.restore()


def _sheet_bench_end(cr, x, ground, sc, light, flip=False):
    """Placeholder: the near end of a bench being dragged (props draws the real one)."""
    F.sheet_bench(cr, x + (110 if not flip else -110) * sc, ground, sc, w=240 * sc, light=light)


def lineup():
    return [B.LineupItem("dwarf", lambda cr, x, y, sc: draw_dwarf(cr, x, y, sc, DwarfPose(facing=1), t=0.4), 170.0)]


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    for label, pose in (("3/4 left", DwarfPose(facing=-1)), ("front", DwarfPose(facing=0)),
                        ("3/4 right", DwarfPose(facing=1)), ("profile", DwarfPose(facing=1, turn=0.75)),
                        ("back 3/4", DwarfPose(facing=1, turn=2.6)), ("back", DwarfPose(facing=2)),
                        ("thumbs in belt", DwarfPose(facing=0, turn=0.3, mood="happy", near=Arm("thumbs_belt"), far=Arm("thumbs_belt")))):
        def fn(cr, p=pose):
            F.sheet_bg(cr, 250, 420, floor=388)
            draw_dwarf(cr, 125, 400, 1.12, p, neutral, t=0.4)
        add(label, 250, 420, fn, "turnaround")

    moods = [("neutral", dict()), ("tired (end of shift)", dict(mood="tired")), ("happy", dict(mood="happy")),
             ("kind", dict(mood="kind")), ("surprised", dict(mood="surprised")), ("skeptical", dict(mood="skeptical")),
             ("talk", dict(talk=0.8)), ("laugh", dict(laugh=1.0)), ("strain (dragging)", dict(mood="angry", talk=0.4)),
             ("front", dict(facing=0)), ("front: happy", dict(facing=0, mood="happy")), ("3/4 left: kind", dict(facing=-1, mood="kind")),
             ("lamp lit (night)", dict(lamp_lit=True, mood="warm")), ("profile", dict(facing=1, turn=0.75))]
    for label, kw in moods:
        kw = dict(kw)
        facing = kw.pop("facing", 1)
        turn = kw.pop("turn", -0.3 if facing == 1 else (0.3 if facing == -1 else 0.0))
        pose = DwarfPose(facing=facing, turn=turn, **kw)

        def fn(cr, p=pose):
            F.sheet_bg(cr, 220, 220, "lantern_night" if p.lamp_lit else "neutral")
            s0, c0 = core.frame(4, 4)
            Lx = L["lantern_night"] if p.lamp_lit else neutral
            r0 = draw_dwarf(c0, 0.0, 0.0, 1.7, p, Lx, t=0.4)
            draw_dwarf(cr, 110 - r0.head[0], 112 - r0.head[1], 1.7, p, Lx, t=0.4)
        add(label, 220, 220, fn, "faces")

    beats = [("walk 0.0", DwarfPose(facing=1, walk=1.0, phase=0.0, mood="tired")),
             ("walk 0.5", DwarfPose(facing=1, walk=1.0, phase=0.5, mood="tired")),
             ("drags a bench (lean back)", DwarfPose(facing=1, drag=1.0, walk=1.0, phase=0.2, mood="angry", talk=0.3, near=Arm("drag"), far=Arm("drag"))),
             ("drags, mid-step", DwarfPose(facing=1, drag=1.0, walk=1.0, phase=0.7, mood="angry", near=Arm("drag"), far=Arm("drag"))),
             ("sits: boots dangle", DwarfPose(facing=1, turn=-0.3, sit=1.0, mood="happy", near=Arm("knees"), far=Arm("knees"))),
             ("takes bread", DwarfPose(facing=0, turn=0.4, sit=1.0, mood="warm", near=Arm("reach", phase=1.0, hold=_sheet_bread))),
             ("eats", DwarfPose(facing=0, turn=-0.3, sit=1.0, mood="happy", talk=0.5, near=Arm("eat", phase=0.85, hold=_sheet_bread)))]
    for label, pose in beats:
        def fn(cr, p=pose):
            F.sheet_bg(cr, 260, 360, floor=330)
            if p.sit > 0.5:
                F.sheet_bench(cr, 130, 342, 0.9, w=220)
            if p.drag > 0:
                g = dwarf_grip(p, 0.9)
                F.sheet_bench(cr, 80 + g[0] + 100, 342, 0.9, w=200)
            draw_dwarf(cr, 130 if p.drag == 0 else 80, 342, 0.9, p, neutral, t=0.4)
        add(label, 260, 360, fn, "actions (S7)")

    for name in F.SHEET_LIGHTS:
        def fn(cr, name=name):
            F.sheet_bg(cr, 200, 360, name, floor=330)
            draw_dwarf(cr, 100, 342, 0.9, DwarfPose(facing=-1, turn=0.25, lamp_lit=name == "lantern_night"), L[name], t=0.4)
        add(name, 200, 360, fn, "lights & film scale")
    for label, h in (("280 px", 280.0), ("190 px", 190.0), ("130 px", 130.0)):
        sc = h / DWARF_HEIGHT

        def fn(cr, sc=sc):
            F.sheet_bg(cr, 200, 360, "golden", floor=330)
            draw_dwarf(cr, 100, 342, sc, DwarfPose(facing=-1, turn=0.2, mood="happy"), L["golden"], t=0.4)
        add(label, 200, 360, fn, "lights & film scale")
    return items
