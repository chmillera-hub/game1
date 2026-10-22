"""_s2_rig.py -- private helpers for SCENE 2 (the apothecary). Not a scene (leading underscore).

Scene-local extensions of the lioness rig and the S2 props, built ON the library without editing
it (file ownership: film/lib/** belongs to the library authors):

  lio_arm(...)         draws ONE of her arms (sleeve + cuff + paw + whatever the paw holds) on its
                       own, exactly as draw_lioness draws it -- so a paw that is over the counter
                       top can be laid again over the counter WITHOUT dragging any apron pixels
                       along (the old reveal cut circles out of her whole figure).
  lio_joints(...)      her shoulder / elbow / wrist of one arm in caller coordinates (no drawing).
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
  draw_book_cover(...) the coloring book standing, with a re-set cover: a bigger title and FOR
                       ADULTS in capitals on a little banner.
  draw_sack_layers(..) the open paper sack in two layers (back wall | front body) so a whole
                       column of remedies can go INTO its mouth between them.

Everything here uses the library's private internals (lioness._skeleton/_solve_arm/_arm/_mouth/
_whiskers, _cast_kit, props._Ctx/_poly_paths/_rrect_paths/_mandala): if the library changes
shape, this fails loudly instead of drawing something subtly wrong.
"""

import math
from dataclasses import dataclass

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


def lio_arm(cr, x, y, scale, pose, light, t, which, draw=True):
    """Draw one arm of the lioness (sleeve, cuff, paw and its held prop) exactly where and how
    draw_lioness(cr, x, y, scale, pose, light, t) draws it. which = "near" | "far".
    Returns (HandFrame or None, [shoulder, elbow, wrist]) in caller coordinates."""
    q, yaw, proj, sc = _ctx(cr, x, y, scale, pose, light, t)
    cr.save()
    cr.translate(x, y)
    cr.scale(sc, sc)
    S = LIO._skeleton(pose, t, yaw)
    q.S = S
    side, arm = _side_arm(pose, yaw, which)
    A = LIO._solve_arm(q, S, side, arm)
    hf = LIO._arm(q, A, side) if draw else None
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
            _word(cr, "DRAUGHT", 0.0, -18.6, 6.4, 40.0, ink, condense=0.9)
            P._label_icon(cr, "moon_white", 12.5, -45.5)      # the painted crescent on the shoulder
    elif name == "vitamins":
        pl = _plate(q, 0.0, -24.0, 46.0, 19.0, 1.6, "#a07a2a")
        if q.detail >= 1:
            ink = core.mix(INK, pl.shadow, 0.1)
            _word(cr, "VITAMINS", 0.0, -23.0, 7.2, 42.0, ink, condense=0.88)
    elif name == "calm":
        pl = _plate(q, 0.0, -18.5, 44.0, 20.0, 2.0, "#7a5aa8")
        if q.detail >= 1:
            ink = core.mix(INK, pl.shadow, 0.1)
            _word(cr, "CALM", 0.0, -17.6, 10.6, 39.0, ink, condense=0.92, spacing=0.6)
    q.end()


def draw_book_cover(cr, x, y, scale, light, angle=0.0, detail=None):
    """The coloring book standing, cover to us (anchor = the cover's centre), its cover re-set for
    the screen: MINDFUL / COLORING big across the top, a smaller rose window, and FOR ADULTS in
    capitals on a little ribbon banner. Mirrors props.draw_coloring_book(state="closed")."""
    q = P._Ctx(cr, x, y, scale, angle, light, detail)
    C = P.PROP_COLORS
    w, h = P.BOOK_W, P.BOOK_H
    bs, bo = P._rrect_paths(cr, -w / 2 + 2.0, -h / 2 + 2.5, w + 1.5, h + 1.0, 2.0, q.lw)
    q.shade(bs, "page", 6.0, outline=bo, rim=0.4)
    cs, co = P._rrect_paths(cr, -w / 2, -h / 2, w, h, 2.5, q.lw)
    pc = q.shade(cs, "book_cover", 22.0, outline=co)
    ss, so = P._rrect_paths(cr, -w / 2 - 1.0, -h / 2, 7.0, h, 2.0, q.lw)
    q.shade(ss, "book_spine", 7.0, outline=so, rim=0.6)
    x0, y0, ww = -w / 2 + 6.0, -h / 2, w - 6.0
    cx = x0 + ww / 2
    ink = core.mix(C["ink"], pc.shadow, 0.1)
    if q.detail >= 1:
        cr.new_path()
        cr.rectangle(x0 + 2.5, y0 + 2.5, ww - 5.0, h - 5.0)
        cr.set_line_width(0.8)
        core.src(cr, C["gold_ink"], 0.85)
        cr.stroke()
        mr, my = ww * 0.2, y0 + h * 0.555
        core.circle(cr, cx, my, mr * 1.03)
        core.src(cr, core.mix(pc.lit, C["rose_ink"], 0.12))
        cr.fill()
        P._mandala(cr, cx, my, mr, C["rose_ink"], 0.9, 0.7, rings=3, petals=10)
        P._mandala(cr, cx, my, mr * 0.55, C["teal_ink"], 0.9, 0.65, rings=2, petals=8)
        core.circle(cr, cx, my, mr * 0.12)
        core.src(cr, C["gold_ink"])
        cr.fill()
        _word(cr, "MINDFUL", cx, y0 + h * 0.135, 7.0, ww - 8.0, ink, spacing=0.4)
        _word(cr, "COLORING", cx, y0 + h * 0.275, 6.2, ww - 7.0, ink, spacing=0.2)
        # FOR ADULTS on a little rose ribbon banner with forked tails
        by, bh, bw = y0 + h * 0.855, 10.0, ww - 6.0
        pts = [(cx - bw / 2, by - bh / 2), (cx + bw / 2, by - bh / 2), (cx + bw / 2 + 3.5, by + bh / 2 + 1.0),
               (cx + bw / 2 - 1.5, by + bh / 2 - 0.5), (cx - bw / 2 + 1.5, by + bh / 2 - 0.5), (cx - bw / 2 - 3.5, by + bh / 2 + 1.0)]
        rs, ro = P._poly_paths(cr, pts, q.lw * 0.7)
        q.shade(rs, B.Mat.of("#c9566e", line_k=0.55), 6.0, outline=ro, rim=0.4)
        _word(cr, "FOR ADULTS", cx, by - 0.2, 4.6, bw - 4.0, "#fbf3e2", condense=0.94, spacing=0.25)
    else:
        core.circle(cr, cx, y0 + h * 0.56, ww * 0.2)
        core.src(cr, core.mix(pc.lit, C["rose_ink"], 0.4))
        cr.fill()
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
