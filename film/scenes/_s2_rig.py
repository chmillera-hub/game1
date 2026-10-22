"""_s2_rig.py -- private helpers for SCENE 2 (the apothecary). Not a scene (leading underscore).

Scene-local extensions of the lioness rig and the S2 props, built ON the library without editing
it (file ownership: film/lib/** belongs to the library authors):

  lio_arm(...)         draws ONE of her arms (sleeve + cuff + paw + whatever the paw holds) on its
                       own, exactly as draw_lioness draws it -- so a paw that is over the counter
                       top can be laid again over the counter WITHOUT dragging any apron pixels
                       along (the old reveal cut circles out of her whole figure).
  lio_joints(...)      her shoulder / elbow / wrist of one arm in caller coordinates (no drawing).
  screen_gaze(x)       context manager: inside it every eye uses x as a SCREEN-space look (the
                       shared rigs mirror the gaze of any eye whose outer corner is screen-left).
  LionessArmS2         LionessArm + steady (no forearm flips) and hang (a droop that turns with
                       her) -- see the section below.
  LionessPoseS2        LionessPose + three S2-only fields used by the frozen-smile take:
                         grin (0..1)      the polite smile locks into a rigid, wide, toothy grin
                                          with the cheeks pushed up (a "polite rictus");
                         whisker_snap     None = the rig's own whiskers; a number (-1..1) bends
                                          every whisker by that much (+ = tips up, ~14 deg at 1)
                                          -- a two-frame snap is two frames of +-1;
                         whisker_fan      0..1 the whiskers splay stiff and wide (tension).
                       The rig ignores fields it does not know; two private drawing hooks of the
                       lioness module (_mouth, _whiskers) are wrapped at import time and fall
                       straight through to the originals for every pose without these fields, so
                       nothing else that draws the lioness can change.
  draw_label_big(...)  the remedies' labels re-lettered for the screen: bigger plates and bolder,
                       larger caps (the prop kit's labels are ~6-8 px tall at film scale).
  draw_book_cover(...) the coloring book standing: the prop kit's own cover (one book across
                       scenes), with its "for Adults" set larger to read at film scale.
  draw_sack_layers(..) the open paper sack in two layers (back wall | front body) so a whole
                       column of remedies can go INTO its mouth between them.

Everything here uses the library's private internals (lioness._skeleton/_solve_arm/_arm/_mouth/
_whiskers, _cast_kit, props._Ctx/_poly_paths/_rrect_paths/_mandala): if the library changes
shape, this fails loudly instead of drawing something subtly wrong.
"""

import math
from dataclasses import dataclass

import numpy as np

from film.lib import core, props as P
from film.lib.characters import base as B
from film.lib.characters import lioness as LIO
from film.lib.characters import _cast_kit as K
from film.lib.core import clamp, lerp

TAU = math.tau


# ========================================================================================
# the lioness: one arm on its own, joints, the frozen-smile extension
# ========================================================================================

@dataclass
class LionessPoseS2(LIO.LionessPose):
    grin: float = 0.0
    whisker_snap: float = None
    whisker_fan: float = 0.0


def _ctx(cr, x, y, scale, pose, light, t, detail=None):
    """Exactly draw_lioness's preamble (same order: the caller matrix is captured first)."""
    light = light or B.LIGHTS["neutral"]
    q = K.Q(cr, light, LIO.lioness_mats(), t, pose)
    yaw = K.yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = B.Proj(yaw, pose.elev)
    q.proj = proj
    sc = scale * LIO.SIZE_K
    dev = q.lod(sc, detail)
    q.lw = B.line_for(LIO.LINE / LIO.SIZE_K, dev, 1.0 / LIO.SIZE_K)
    return q, yaw, proj, sc


def _side_arm(pose, yaw, which):
    near_side = -1.0 if yaw >= 0 else 1.0
    if which == "near":
        return near_side, pose.near
    return -near_side, pose.far


def lio_arm(cr, x, y, scale, pose, light, t, which, draw=True, parts="all"):
    """Draw one arm of the lioness (sleeve, cuff, paw and its held prop) exactly where and how
    draw_lioness(cr, x, y, scale, pose, light, t) draws it. which = "near" | "far"; parts =
    "all" | "sleeve" (sleeve + cuff) | "hand" (the paw alone: laid again over a prop).
    Returns (HandFrame or None, [shoulder, elbow, wrist]) in caller coordinates."""
    q, yaw, proj, sc = _ctx(cr, x, y, scale, pose, light, t)
    cr.save()
    cr.translate(x, y)
    cr.scale(sc, sc)
    S = LIO._skeleton(pose, t, yaw)
    q.S = S
    side, arm = _side_arm(pose, yaw, which)
    A = LIO._solve_arm(q, S, side, arm)
    hf = LIO._arm(q, A, side, parts=parts) if draw else None
    ex = K.Exporter(cr)
    cr.restore()
    ex.ready(cr)
    joints = [ex(proj.xy(A[k])) for k in ("sh", "el", "wr")]
    if hf is not None:
        ex.hand(hf, sc)
    return hf, joints


def lio_joints(x, y, scale, pose, t, which):
    """[shoulder, elbow, wrist] of one arm in caller coordinates (a dry run, nothing drawn)."""
    _s, scr = core.frame(4, 4)
    return lio_arm(scr, x, y, scale, pose, None, t, which, draw=False)[1]


class HeadFrame:
    """Head-space point -> caller coordinates for the lioness drawn at (x, y, scale)."""

    def __init__(self, x, y, scale, pose, t):
        yaw = K.yaw_of(pose.facing, pose.turn)
        self.proj = B.Proj(yaw, pose.elev)
        S = LIO._skeleton(pose, t, yaw)
        self.RH, self.HC = S["RH"], S["head_c"]
        self.k = scale * LIO.SIZE_K
        self.x, self.y = x, y

    def __call__(self, v):
        w = B.m_vec(self.RH, v)
        px, py = self.proj.xy((self.HC[0] + w[0] * LIO.HS, self.HC[1] + w[1] * LIO.HS, self.HC[2] + w[2] * LIO.HS))
        return (self.x + px * self.k, self.y + py * self.k)


# ---- the frozen-smile hooks (wrapped once; they fall through for every other pose) ----

_ORIG_MOUTH = LIO._mouth
_ORIG_WHISKERS = LIO._whiskers


def _mouth_s2(q, P_, nz, e, jaw, near, fur, pale):
    g = clamp(getattr(q.pose, "grin", 0.0) or 0.0)
    if g <= 0.001 or jaw > 0.05:
        return _ORIG_MOUTH(q, P_, nz, e, jaw, near, fur, pale)
    cr, lw = q.cr, q.lw
    lc = q.P(q.M["mark"]).lit
    top = P_((0.0, 11.0, 36.0))
    if nz((0.0, 0.4, 0.9)) < -0.2:
        return P_((0.0, 16.0, 35.0))
    # the corners pulled out and up into the cheeks; the upper lip stays a soft cat "w"; a
    # crescent of clenched teeth between it and the lower lip: a smile with nothing behind it
    cw, cy_ = lerp(10.5, 15.5, g), lerp(17.5 - e.smile * 3.5, 12.0, g)
    mid_y = lerp(16.0, 17.2, g)
    low_y = lerp(16.5, 23.0, g)
    L, R = P_((-cw, cy_, 30.0)), P_((cw, cy_, 30.0))
    upper = [L, P_((-cw * 0.5, mid_y + 0.6, 33.8)), P_((0.0, mid_y, 35.4)), P_((cw * 0.5, mid_y + 0.6, 33.8)), R]
    lower = [R, P_((cw * 0.55, low_y - 0.8, 33.6)), P_((0.0, low_y, 35.0)), P_((-cw * 0.55, low_y - 0.8, 33.6)), L]
    cr.new_path()
    core.smooth_closed(cr, upper + lower[1:-1], 0.55)
    mouth = B.Path(cr)
    cr.save()
    mouth.add(cr)
    cr.clip()
    core.src(cr, "#efe8dc")
    cr.paint()
    # the teeth: a dark seam between the rows and little tooth gaps, a shadow under the lip
    gap = [P_((-cw * 0.8, lerp(cy_, low_y, 0.42), 31.5)), P_((0.0, lerp(mid_y, low_y, 0.5), 35.2)),
           P_((cw * 0.8, lerp(cy_, low_y, 0.42), 31.5))]
    B.detail_lines(cr, [gap], lw * 0.9, "#5e2a2c", 0.85, taper=(0.3, 1.0, 0.3))
    ticks = []
    for i in (-2, -1, 0, 1, 2):
        u = i / 2.6
        a = P_((u * cw, mid_y + 0.4 + abs(u) * (cy_ - mid_y) * 0.9, 34.6 - abs(u) * 4.0))
        b = P_((u * cw * 0.98, lerp(mid_y, low_y, 0.48) + abs(u) * (cy_ - mid_y) * 0.5, 34.8 - abs(u) * 4.0))
        ticks.append([a, b])
    B.detail_lines(cr, ticks, lw * 0.45, "#b9aa9a", 0.9, taper=(0.6, 1.0, 0.6))
    B.detail_lines(cr, [[P_((-cw, cy_ + 0.6, 30.0)), P_((0.0, mid_y + 1.5, 35.4)), P_((cw, cy_ + 0.6, 30.0))]],
                   lw * 1.6, "#b8a48c", 0.45, taper=(0.2, 1.0, 0.2))
    cr.restore()
    lines = [[top, P_((0.0, mid_y, 35.4))], upper, lower]
    B.detail_lines(cr, lines, lw * 1.1, lc, 0.95, taper=(0.4, 1.0, 0.4))
    # the cheeks pushed up: a tight crease off each corner (the grin's tension)
    creases = []
    for s, c in ((-1.0, L), (1.0, R)):
        if nz((s * 0.6, 0.3, 0.7)) > -0.25:
            creases.append([c, P_((s * (cw + 2.6), cy_ - 2.2, 28.5)), P_((s * (cw + 3.4), cy_ - 5.2, 27.0))])
    if creases:
        B.detail_lines(cr, creases, lw * 0.9, lc, 0.7 * g, taper=(1.0, 0.8, 0.1))
    return P_((0.0, mid_y, 35.0))


def _whiskers_s2(q, P_, nz, near):
    snap = getattr(q.pose, "whisker_snap", None)
    fan = clamp(getattr(q.pose, "whisker_fan", 0.0) or 0.0)
    if snap is None and fan <= 0.0:
        return _ORIG_WHISKERS(q, P_, nz, near)
    snap = snap or 0.0
    cr, t = q.cr, q.t
    pads, wh = [], []
    for s in (-1.0, 1.0):
        if nz((s * 0.6, 0.2, 0.75)) < -0.15:
            continue
        for row in range(3):
            for col in range(3 - (row == 2)):
                pads.append(P_((s * (6.0 + col * 3.6), 9.5 + row * 3.2, 35.0 - col * 1.5)))
        if q.detail >= 1:
            for k, (dy, spread) in enumerate(((-2.0, -0.12), (1.0, 0.0), (4.0, 0.14))):
                # stiff and splayed (fan), then the whole fan bends up / down (snap)
                sp = spread * (1.0 + 1.1 * fan)
                bend = -snap * (7.0 + 1.5 * k)
                a = P_((s * 11.0, 11.0 + dy * 0.6, 32.5))
                b = P_((s * (40.0 + 3.0 * fan), 8.0 + dy * 3.0 + sp * 30.0 + bend, 30.0))
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 2.5 * (1.0 - 0.6 * fan))
                wh.append([a, m, b])
    core.src(cr, q.P(q.M["mark"]).lit, 0.75)
    for p in pads:
        core.circle(cr, p[0], p[1], 1.05 * LIO.HS)
    cr.fill()
    if wh:
        B.detail_lines(cr, wh, q.lw * 0.6, core.mix(q.P(q.M["pale"]).hi, (1, 1, 1), 0.2), 0.95, taper=(1.0, 0.7, 0.15))


LIO._mouth = _mouth_s2
LIO._whiskers = _whiskers_s2


# ========================================================================================
# eyelines: a pose's look-x is SCREEN space (+x = screen right), for both eyes, here
# ========================================================================================
# Every rig passes look=(pose.look[0] * outer, ...) to base.eye, and base.eye multiplies by
# `outer` again inside its mirrored frame, so each iris moves toward its own outer corner: an eye
# whose outer corner is screen-left (the dragon's visible eye when he faces right; the lioness's
# far eye when she faces left) looks the WRONG way, and two visible eyes diverge (cross-eyed).
# Inside screen_gaze(look_x) every eye uses look_x as a screen-space gaze. The mapping is probed
# from base.eye itself, so this stays right if the library is fixed later (either way round).
# Outside the context manager base.eye is untouched for everyone.

_ORIG_EYE = B.eye
_GAZE = []                   # a stack: the screen-space look-x of the character being drawn
_EYE_SCREEN = []             # [True] if base.eye's look-x is screen space, [False] if outer-relative


def _eye_is_screen_space():
    if not _EYE_SCREEN:
        xs = []
        for lx in (-1.0, 1.0):
            surf = core.new_surface(96, 64)
            c = core.new_context(surf)
            c.set_source_rgb(1.0, 1.0, 1.0)
            c.paint()
            _ORIG_EYE(c, 48.0, 32.0, 26.0, 22.0, B.LIGHTS["neutral"], 1.0, look=(lx, 0.0), lid=0.0, lid_bot=0.0,
                      outer=-1.0, iris="#000000", iris_hi="#000000", pupil="#000000", sclera="#ffffff",
                      skin="#ffffff", line="#ffffff", highlight=0.0, crease=0.0, lash=0.0, lid_shade=0.0)
            surf.flush()
            h, stride = surf.get_height(), surf.get_stride()
            px = np.frombuffer(surf.get_data(), np.uint8).reshape(h, stride // 4, 4)[:, :surf.get_width(), 1]
            ys_, xs_ = np.nonzero(px < 80)                  # the dark iris (green channel of BGRA)
            xs.append(float(xs_.mean()) if len(xs_) else 0.0)
        _EYE_SCREEN.append(xs[1] > xs[0])
    return _EYE_SCREEN[0]


def _eye_gaze(*a, **kw):
    if _GAZE and "look" in kw:
        lx = _GAZE[-1]
        outer = kw.get("outer", 1.0)
        kw["look"] = (lx if _eye_is_screen_space() else lx * outer, kw["look"][1])
    return _ORIG_EYE(*a, **kw)


B.eye = _eye_gaze


class screen_gaze:
    """with screen_gaze(pose.look[0]): draw_dragon(...) -- both eyes look screen-left (-) or
    screen-right (+) as the pose says."""

    def __init__(self, look_x):
        self.look_x = float(look_x)

    def __enter__(self):
        _GAZE.append(self.look_x)
        return self

    def __exit__(self, *exc):
        _GAZE.pop()
        return False


# ========================================================================================
# the lioness's arms: a steady forearm (no flips) and a hand droop that turns with her
# ========================================================================================
# The library solves each arm in 3D with a fixed elbow pole (out, down and a little back). In a
# 3/4 view that bends the arm in DEPTH, so when the wrist passes close to the elbow on screen the
# projected forearm shrinks to a few px, its direction flips and the paw (drawn along it) spins
# half round in one frame. LionessArmS2 arms (the library ignores the extra fields):
#   steady  0..1: when the projected forearm gets short, the elbow is eased toward a 2D elbow
#           bent in the PICTURE plane (down and toward her back), so the forearm keeps a length
#           and only ever rotates in the picture plane: continuous by construction.
#   hang    None = the gesture's own hand droop, faded to nothing as she passes the front view
#           (the library flips its sign at yaw 0: a 57-degree twist in one frame mid-turn);
#           a number = the droop in radians (the scene keeps it continuous).

#   ang     None, or a screen angle (rad) the paw points along (cuff and hand), blended in by
#   ang_w   0..1 -- for a paw whose forearm points at the camera (an item carried at her chest
#           through a turn): its projected direction is noise, so the scene steers the paw.

@dataclass
class LionessArmS2(LIO.LionessArm):
    steady: float = 0.0
    hang: float = None
    ang: float = None
    ang_w: float = 0.0


_ORIG_SOLVE = LIO._solve_arm
HANG_YAW = 0.7               # the droop fades in over this much yaw either side of the front view


def _xy_to_body(pr, p, depth):
    """Rig 2D (projected) point at a camera depth -> body space (inverse of Proj)."""
    X = p[0] * pr.c - depth * pr.s
    Z = p[0] * pr.s + depth * pr.c
    Y = (p[1] - depth * pr.se) / pr.ce
    return (X, Y, Z)


def _elbow_2d(s2, w2, yaw, l1, l2):
    """A 2D elbow for shoulder s2 -> wrist w2: two-bone IK in the picture plane with the bones a
    little foreshortened, bent toward her back and down (the side swaps smoothly through the
    front view, where the arm is shown straight)."""
    dx, dy = w2[0] - s2[0], w2[1] - s2[1]
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return (s2[0], s2[1] + l1)
    ux, uy = dx / d, dy / d
    sgn = -clamp(yaw / 0.6, -1.0, 1.0)          # facing left: + (the elbow on the down/back side)
    if d >= l1 + l2:
        a, h = d * l1 / (l1 + l2), 0.0
    else:
        dd = max(d, abs(l1 - l2) + 1e-3)
        a = (l1 * l1 - l2 * l2 + dd * dd) / (2.0 * dd)
        h = math.sqrt(max(0.0, l1 * l1 - a * a))
    nx, ny = uy, -ux                              # cross(u, n) < 0: the down/back side facing left
    return (s2[0] + ux * a + nx * h * sgn, s2[1] + uy * a + ny * h * sgn)


def _solve_arm_s2(q, S, side, arm):
    A = _ORIG_SOLVE(q, S, side, arm)
    if not isinstance(arm, LionessArmS2):
        return A
    yaw = q.yaw
    step = 1.0 if yaw >= 0 else -1.0
    if arm.hang is not None:
        A["hang"] = arm.hang * (1.0 if side < 0 else -1.0) * step
    else:
        A["hang"] = A["hang"] * clamp(abs(yaw) / HANG_YAW, 0.0, 1.0)
    k = clamp(arm.steady)
    if k > 0.0:
        pr = q.proj
        s2, w2, e2 = pr.xy(A["sh"]), pr.xy(A["wr"]), pr.xy(A["el"])
        fl = math.hypot(w2[0] - e2[0], w2[1] - e2[1])
        wgt = k * (1.0 - core.smoothstep(0.3 * LIO.FOREARM, 0.55 * LIO.FOREARM, fl))
        if wgt > 1e-4:
            e_ref = _elbow_2d(s2, w2, yaw, LIO.UPPER_ARM * 0.86, LIO.FOREARM * 0.86)
            e_new = (lerp(e2[0], e_ref[0], wgt), lerp(e2[1], e_ref[1], wgt))
            dep = lerp(pr.depth(A["el"]), 0.5 * (pr.depth(A["sh"]) + pr.depth(A["wr"])), wgt)
            A = dict(A, el=_xy_to_body(pr, e_new, dep))
    return A


LIO._solve_arm = _solve_arm_s2

_ORIG_ARM = LIO._arm


def _arm_s2(q, A, side, parts="all", hold=True):
    """lioness._arm (sleeve, cuff, paw) with the paw's direction steered (LionessArmS2.ang)."""
    arm = A["arm"]
    if not isinstance(arm, LionessArmS2) or arm.ang is None or arm.ang_w <= 1e-4:
        return _ORIG_ARM(q, A, side, parts, hold)
    cr, proj, M = q.cr, q.proj, q.M
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    ang = core.lerp_angle(math.atan2(fdy, fdx), arm.ang, clamp(arm.ang_w))
    fdx, fdy = math.cos(ang), math.sin(ang)
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
    hp = A["hand"]
    hang = ang + A["hang"] * (1 if side < 0 else -1) * (1 if q.yaw >= 0 else -1)
    flip = (side > 0) == (q.yaw >= 0)
    show_palm = hp in ("open", "offer") and arm.gesture in ("present", "place")
    return B.hand(cr, wr[0] + fdx * 6.0, wr[1] + fdy * 6.0, hang, LIO.HAND_LEN, hp, M["fur"], q.light_nb, q.lw,
                  flip=flip, claw=None, pad=LIO.LIONESS_COLORS["pad"], show_palm=show_palm,
                  hold=arm.hold if hold else None, finger_w=1.15, palm_w=1.1, detail=q.detail)


LIO._arm = _arm_s2


# ========================================================================================
# props: legible labels, the re-set book cover, the open sack in two layers
# ========================================================================================

INK = P.PROP_COLORS["ink"]


def _plate(q, cx, cy, w, h, curve, rule):
    """A pasted parchment label on a curved glass body (the prop kit's shape, bigger)."""
    cr = q.cr
    n = 7
    top = [(cx - w / 2 + w * i / (n - 1), cy - h / 2 + curve * (1 - (2 * i / (n - 1) - 1) ** 2)) for i in range(n)]
    bot = [(cx + w / 2 - w * i / (n - 1), cy + h / 2 + curve * (1 - (2 * (n - 1 - i) / (n - 1) - 1) ** 2)) for i in range(n)]
    ls, lo = P._poly_paths(cr, top + bot, q.lw * 0.8)
    pl = q.shade(ls, "parchment", min(h, 9.0), outline=lo, rim=0.4)
    if q.detail >= 1:
        cr.new_path()
        core.polygon(cr, B.offset_closed(top + bot, -1.6))
        cr.set_line_width(0.7)
        core.src(cr, rule, 0.8)
        cr.stroke()
    return pl


def _word(cr, s, x, y, cap, maxw, ink, condense=1.0, family=None, spacing=0.0):
    """One line of bold storybook caps, cap height `cap`, squeezed to maxw (a sign-painter's
    condensed letter when it would not fit), centred on (x, y)."""
    family = family or P.FONTS.label
    size = cap / 0.70
    adv = core.measure(cr, s, size, family, True, False, spacing)[0]
    sx = condense
    if adv * sx > maxw:
        sx = maxw / adv
    if sx < 0.82:                          # never squeeze past a believable condensed letter
        size *= sx / 0.82
        sx = 0.82
    cr.save()
    cr.translate(x, y)
    cr.scale(sx, 1.0)
    core.text(cr, s, 0.0, 0.0, size, family, ink, align="center", valign="cap", bold=True, spacing=spacing,
              outline=(ink, size * 0.012))
    cr.restore()


def draw_label_big(cr, name, x, y, scale, light, angle=0.0, detail=None):
    """The label of a remedy drawn at (x, y, scale, angle) (its bottom-centre anchor), re-lettered
    to read at film scale. Call right after drawing the remedy with label=False."""
    q = P._Ctx(cr, x, y, scale, angle, light, detail)
    if name == "sleep":
        pl = _plate(q, 0.0, -25.5, 45.0, 31.0, 2.4, P.PROP_COLORS["apoth_green"])
        if q.detail >= 1:
            ink = core.mix(INK, pl.shadow, 0.1)
            _word(cr, "SLEEP", 0.0, -32.2, 8.4, 38.0, ink)
            _word(cr, "DRAUGHT", 0.0, -18.4, 7.2, 42.0, ink, condense=0.88)
            P._label_icon(cr, "moon_white", 12.5, -45.5)      # the painted crescent on the shoulder
    elif name == "vitamins":
        pl = _plate(q, 0.0, -24.0, 47.5, 21.0, 1.6, "#a07a2a")
        if q.detail >= 1:
            ink = core.mix(INK, pl.shadow, 0.1)
            _word(cr, "VITAMINS", 0.0, -23.2, 8.2, 44.5, ink, condense=0.86)
    elif name == "calm":
        pl = _plate(q, 0.0, -18.5, 44.0, 20.0, 2.0, "#7a5aa8")
        if q.detail >= 1:
            ink = core.mix(INK, pl.shadow, 0.1)
            _word(cr, "CALM", 0.0, -17.6, 10.6, 39.0, ink, condense=0.92, spacing=0.6)
    q.end()


def draw_book_cover(cr, x, y, scale, light, angle=0.0, detail=None):
    """The coloring book standing, cover to us (anchor = the cover's centre). This IS the prop
    kit's cover (props.draw_coloring_book(state="closed"): the same parchment, ruled gold frame,
    MINDFUL / COLORING title, rose-window mandala and italic "for Adults"), so it is one book from
    the apothecary to the bench (S6); only "for Adults" is set larger: the kit letters it for
    close-ups, and here the joke has to read at film scale."""
    q = P._Ctx(cr, x, y, scale, angle, light, detail)
    C = P.PROP_COLORS
    w, h = P.BOOK_W, P.BOOK_H
    bs, bo = P._rrect_paths(cr, -w / 2 + 2.0, -h / 2 + 2.5, w + 1.5, h + 1.0, 2.0, q.lw)
    q.shade(bs, "page", 6.0, outline=bo, rim=0.4)
    cs, co = P._rrect_paths(cr, -w / 2, -h / 2, w, h, 2.5, q.lw)
    pc = q.shade(cs, "book_cover", 22.0, outline=co)
    ss, so = P._rrect_paths(cr, -w / 2 - 1.0, -h / 2, 7.0, h, 2.0, q.lw)
    q.shade(ss, "book_spine", 7.0, outline=so, rim=0.6)
    # props._cover_art(q, x0, y0, ww, h, pc), line for line, with the subtitle enlarged
    x0, y0, ww = -w / 2 + 6.0, -h / 2, w - 6.0
    ink = core.mix(C["ink"], pc.shadow, 0.1)
    cx = x0 + ww / 2
    if q.detail >= 1:
        cr.new_path()
        cr.rectangle(x0 + 3.0, y0 + 3.0, ww - 6.0, h - 6.0)
        cr.set_line_width(0.8)
        core.src(cr, C["gold_ink"], 0.85)
        cr.stroke()
    mr = ww * 0.26
    my = y0 + h * 0.56
    if q.detail >= 1:
        core.circle(cr, cx, my, mr * 1.02)
        core.src(cr, core.mix(pc.lit, C["rose_ink"], 0.12))
        cr.fill()
        P._mandala(cr, cx, my, mr, C["rose_ink"], 0.9, 0.75, rings=3, petals=10)
        P._mandala(cr, cx, my, mr * 0.55, C["teal_ink"], 0.9, 0.7, rings=2, petals=8)
        core.circle(cr, cx, my, mr * 0.1)
        core.src(cr, C["gold_ink"])
        cr.fill()
    else:
        core.circle(cr, cx, my, mr)
        core.src(cr, core.mix(pc.lit, C["rose_ink"], 0.4))
        cr.fill()
    fam = P.FONTS.label
    P._label(cr, "MINDFUL", cx, y0 + h * 0.13, h * 0.125, ink, fam, spacing=0.3)
    P._label(cr, "COLORING", cx, y0 + h * 0.27, h * 0.11, ink, fam, spacing=0.2)
    if q.detail >= 1:
        P._label(cr, "for Adults", cx, y0 + h * 0.895, h * 0.13, core.mix(ink, C["rose_ink"], 0.4), P.FONTS.text,
                 italic=True, maxw=ww - 7.0)
    q.end()


BOOK_UP_H = P.BOOK_H + 3.5          # the standing book's height incl. the page block below the cover


def draw_book_up(cr, x, y, scale, light, angle=0.0, detail=None):
    """The book standing on its bottom edge (anchor = bottom centre), like draw_remedy("book_up")."""
    ca, sa = math.cos(angle), math.sin(angle)
    hy = -P.BOOK_H * 0.5 * scale
    draw_book_cover(cr, x - hy * sa, y + hy * ca, scale, light, angle)


def _paper(light, damp=0.0):
    return P.prop_mats()["paper"]


SACK_BACK = [(-27.0, 6.0), (-14.0, -1.0), (0.0, -3.0), (14.0, -1.5), (27.0, 5.0), (24.0, 14.0), (-24.0, 14.0)]
SACK_BODY = [(-27.0, 8.0), (-14.0, 12.5), (0.0, 10.0), (14.0, 13.0), (27.0, 7.5), (30.0, 30.0), (33.0, 62.0),
             (31.5, 82.0), (22.0, 86.5), (0.0, 87.5), (-22.0, 86.5), (-31.5, 82.0), (-33.0, 64.0), (-30.5, 30.0)]
SACK_MOUTH_Y = 9.0                 # the front lip (sack-local units below the grip)


def _sack_xf(q, bulge):
    """Squash the sack about its bottom (bulge > 0: it swallows something and swells)."""
    if bulge:
        cr = q.cr
        cr.translate(0.0, 87.0)
        cr.scale(1.0 + 0.10 * bulge, 1.0 - 0.06 * bulge)
        cr.translate(0.0, -87.0)


def draw_sack_back(cr, x, y, scale, light, bulge=0.0):
    """The open sack's back wall (the inside of its mouth). Anchor = the grip on the neck, as
    props.draw_apothecary_bag."""
    q = P._Ctx(cr, x, y, scale, 0.0, light)
    _sack_xf(q, bulge)
    bs, bo = P._poly_paths(cr, SACK_BACK, q.lw, 0.6)
    q.shade(bs, B.Mat.of(core.shade(P.PROP_COLORS["paper"], 0.25), shadow_k=0.9, line_k=0.5), 14.0, outline=bo, rim=0.3)
    q.end()


def draw_sack_front(cr, x, y, scale, light, bulge=0.0, puff=0.0):
    """The open sack's front body with its folds and the block-printed green cross."""
    C = P.PROP_COLORS
    q = P._Ctx(cr, x, y, scale, 0.0, light)
    _sack_xf(q, bulge)
    body = SACK_BODY
    if puff:
        body = [(px * (1.0 + 0.05 * puff) if py < 20 else px, py - (2.5 * puff if py < 15 else 0.0)) for px, py in body]
    paper = P.prop_mats()["paper"]
    bs, bo = B.smooth_paths(cr, body, q.lw, 0.62)
    pb = q.shade(bs, paper, 62.0, outline=bo)
    if q.detail >= 1:
        folds = [[(-22.0, 20.0), (-25.0, 52.0), (-26.0, 80.0)], [(20.0, 24.0), (23.0, 58.0)],
                 [(-24.0, 86.0), (-17.0, 77.0), (-7.0, 85.0)], [(24.0, 86.0), (18.0, 78.0), (8.0, 85.0)]]
        if q.detail >= 2:
            folds += [[(-12.0, 68.0), (-3.0, 74.0), (8.0, 71.0)]]
        B.detail_lines(cr, folds, q.lw * 0.8, pb.line, 0.45)
    green = B.palette(q.light, B.Mat.of(C["apoth_green"]))
    cr.save()
    cr.translate(1.0, 55.0)
    cr.rotate(-0.05)
    arm, th = 12.5, 4.8
    cross = [(-th, -arm), (th, -arm), (th, -th), (arm, -th), (arm, th), (th, th), (th, arm), (-th, arm), (-th, th),
             (-arm, th), (-arm, -th), (-th, -th)]
    core.polygon(cr, cross)
    core.src(cr, core.mix(green.lit, green.shadow, 0.12), 0.95)
    cr.fill()
    if q.detail >= 2:
        core.src(cr, pb.lit, 0.35)
        for i in range(10):
            core.circle(cr, (core.hash01(i, 61) - 0.5) * 2 * arm, (core.hash01(i, 62) - 0.5) * 2 * th,
                        0.5 + 0.7 * core.hash01(i, 63))
        cr.fill()
        core.src(cr, green.hi, 0.18)
        core.polygon(cr, [(px * 0.6 - 1.4, py * 0.6 - 1.4) for px, py in cross])
        cr.fill()
    cr.restore()
    q.end()


def sack_mouth_world(x, y, scale, bulge=0.0):
    """World y of the sack's front lip (its mouth) for a sack anchored at (x, y, scale)."""
    k = 1.0 - 0.06 * bulge
    return y + (87.0 + (SACK_MOUTH_Y - 87.0) * k) * scale
