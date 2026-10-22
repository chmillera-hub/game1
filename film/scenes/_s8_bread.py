"""_s8_bread.py -- S8's bread: the last piece of her loaf (exactly S7's) and how it breaks.

The piece is the one S7 ends on: gnome_bread "piece", size PIECE (= S7's PIECE * 0.85), seed 6,
face +1, upright. draw_part() draws it whole (part 0) or one of its two torn halves (part -1:
the left half, +1: the right half) in piece units (= body px at scale 1), centred where the
whole piece is centred; the tear is a jagged line down its middle.

Everything is placed with cairo.Matrix maps from piece units to WORLD px, so a half can change
hands (and drawing layers) without moving a pixel: the receiver draws it with exactly the
giver's matrix at the hand-over, then eases it into its own hold (lerp_matrix).
"""

import math

import cairocffi as cairo

from film.lib import core
from film.lib import characters as ch
from film.lib.characters import base as B

PIECE = 52.0 * 0.85          # S7: PIECE (52) * 0.85 -- the last piece she lays in his palm
SEED = 6                     # S7's seed for it
FACE = 1.0


def _outline_pts(size=PIECE, seed=SEED):
    """gnome.py's piece silhouette (the same points it draws)."""
    r = size * 0.5
    s = r * 0.48
    pts = []
    for i in range(9):
        a = math.tau * i / 9
        rag = 1.0 + 0.16 * (core.hash01(i, seed + 11) - 0.5)
        pts.append((math.cos(a) * s * 1.15 * rag, math.sin(a) * s * 0.85 * rag))
    return pts


OUTLINE = _outline_pts()
HALF_W = max(abs(x) for x, _ in OUTLINE)
HALF_H = max(abs(y) for _, y in OUTLINE)
# the tear: a jagged line down the middle, top -> bottom (it overshoots the silhouette: clipped)
TEAR = [(0.6, -HALF_H - 4.0), (0.5, -HALF_H + 1.0), (-0.9, -5.0), (1.0, -1.3), (-0.7, 2.6), (0.5, 5.8),
        (0.1, HALF_H - 0.6), (0.1, HALF_H + 4.0)]
HINGE = (0.1, HALF_H - 0.8)          # the crust holds longest at the foot of the tear
CENTROID = {-1: (-HALF_W * 0.48, 0.3), 1: (HALF_W * 0.48, 0.3), 0: (0.0, 0.0)}


def _half_clip(cr, part):
    big = 80.0
    edge = TEAR
    side = -big if part < 0 else big
    poly = [(side, -big), (edge[0][0], -big)] + edge + [(edge[-1][0], big), (side, big)]
    cr.new_path()
    core.polygon(cr, poly)
    cr.clip()


def _silhouette(cr, grow=0.0):
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(OUTLINE, grow) if grow else OUTLINE, 0.8)


def detail_for(cr):
    ux, uy = cr.user_to_device_distance(1.0, 0.0)
    dev = math.hypot(ux, uy)
    return 2 if dev >= 0.9 else 1 if dev >= 0.55 else 0


def draw_part(cr, light, part=0, detail=None, lw=None):
    """The piece (part 0) or its left (-1) / right (+1) torn half, in piece units at the origin
    (where the whole piece is centred). A half shows its torn face: an inked ragged edge with a
    pale fluffy band of crumb just inside it."""
    if detail is None:
        detail = detail_for(cr)
    if lw is None:
        lw = B.line_w(cr, ch.GNOME_LINE)
    if part == 0:
        ch.gnome_bread(cr, 0.0, 0.0, PIECE, light, "piece", face=FACE, seed=SEED, detail=detail, lw=lw)
        return
    M = ch.gnome_mats()
    crumb = B.palette(light, M["crumb"])
    cr.save()
    _half_clip(cr, part)
    ch.gnome_bread(cr, 0.0, 0.0, PIECE, light, "piece", face=FACE, seed=SEED, detail=detail, lw=lw)
    # the torn face: a fluffy pale band just inside the tear (inside the silhouette only) ...
    cr.save()
    _silhouette(cr)
    cr.clip()
    cr.new_path()
    core.smooth_open(cr, [(x + part * lw * 0.9, y) for x, y in TEAR], 0.5)
    cr.set_line_width(lw * 1.2)
    core.src(cr, core.tint(crumb.lit, 0.35), 0.9)
    cr.stroke()
    if detail >= 1:                                     # a few torn crumb holes along it
        core.src(cr, crumb.shadow, 0.75)
        for i in range(3):
            y = -HALF_H * 0.5 + i * HALF_H * 0.55
            core.circle(cr, part * (lw * 1.6 + 0.5 * core.hash01(i, 61 + part)), y, 0.45 + 0.35 * core.hash01(i, 63))
        cr.fill()
    cr.restore()
    # ... and the ink along it (inside the dilated silhouette: it meets the outline cleanly)
    cr.save()
    _silhouette(cr, lw * 0.85)
    cr.clip()
    cr.new_path()
    core.smooth_open(cr, TEAR, 0.5)
    cr.set_line_width(lw * 0.85)
    core.src(cr, crumb.line, 0.95)
    cr.stroke()
    cr.restore()
    cr.restore()


def draw_gap(cr, light, theta, sep, strands=1.0):
    """The tear opening between the two halves while they are still joined at the foot (piece
    units, the whole piece's frame): the torn crumb seen inside the gap, and a few strands of
    crumb stretched across it (they part as the halves do)."""
    a = 1.0 - core.smoothstep(1.5, 4.0, sep)           # (once the halves are apart there is no gap)
    if (theta <= 0.0 and sep <= 0.0) or a <= 0.0:
        return
    M = ch.gnome_mats()
    crumb = B.palette(light, M["crumb"])
    hx, hy = HINGE
    pl, pr = [], []
    for x, y in TEAR[1:-1]:
        for side, out in ((-1, pl), (1, pr)):
            r = side * theta
            c, s = math.cos(r), math.sin(r)
            dx, dy = x - hx, y - hy
            out.append((hx + dx * c - dy * s + side * sep * 0.5, hy + dx * s + dy * c))
    cr.save()
    cr.new_path()
    core.polygon(cr, pl + pr[::-1])
    core.src(cr, core.mix(crumb.lit, crumb.shadow, 0.55), a)     # torn crumb, in its own shade
    cr.fill()
    if strands > 0.0:
        cr.set_line_width(0.6)
        core.src(cr, core.tint(crumb.lit, 0.25), 0.9 * strands * a)
        for k in (2, 3, 4):
            if k < len(pl):
                (x0, y0), (x1, y1) = pl[k], pr[k]
                cr.move_to(x0, y0)
                cr.curve_to(x0 + (x1 - x0) * 0.3, y0 + 0.7, x0 + (x1 - x0) * 0.7, y1 + 0.7, x1, y1)
        cr.stroke()
    cr.restore()


# ----------------------------------------------------------------------------------------
# matrices (piece units -> world px)
# ----------------------------------------------------------------------------------------

def piece_matrix(cx, cy, rot, scale):
    """Piece units -> world: centred at (cx, cy), rotated by rot (rad), scale px per unit."""
    m = cairo.Matrix()
    m.translate(cx, cy)
    if rot:
        m.rotate(rot)
    m.scale(scale, scale)
    return m


def half_matrix(whole, part, theta, sep):
    """A half's matrix from the whole piece's: rotated by part*theta about the hinge and pushed
    sep/2 apart (piece units). Its origin stays the whole piece's centre (draw_part's frame)."""
    m = cairo.Matrix()
    hx, hy = HINGE
    m.translate(part * sep * 0.5, 0.0)
    m.translate(hx, hy)
    m.rotate(part * theta)
    m.translate(-hx, -hy)
    return m.multiply(whole)


def hand_matrix(hf):
    """A HandFrame (world) as a matrix: origin at its grip, +x along the fingers (world px)."""
    m = cairo.Matrix()
    m.translate(hf.x, hf.y)
    m.rotate(hf.angle)
    return m


def relative(m, frame):
    """m expressed in `frame` (both world maps): m == relative(m, frame).multiply(frame)."""
    inv = cairo.Matrix(*frame.as_tuple())
    inv.invert()
    return m.multiply(inv)


def decompose(m):
    """(tx, ty, rot, scale, flip) of a similarity map (no shear)."""
    xx, yx, xy, yy, x0, y0 = m.as_tuple()
    det = xx * yy - xy * yx
    flip = -1.0 if det < 0 else 1.0
    sc = math.sqrt(abs(det))
    rot = math.atan2(yx, xx)
    return x0, y0, rot, sc, flip


def compose(tx, ty, rot, sc):
    return piece_matrix(tx, ty, rot, sc)


def lerp_matrix(a, b, u):
    """Blend two (unflipped) similarity maps: translation, rotation (short way) and scale."""
    if u <= 0.0:
        return cairo.Matrix(*a.as_tuple())
    if u >= 1.0:
        return cairo.Matrix(*b.as_tuple())
    ax, ay, ar, asc, _ = decompose(a)
    bx, by, br, bsc, _ = decompose(b)
    dr = (br - ar + math.pi) % math.tau - math.pi
    return compose(core.lerp(ax, bx, u), core.lerp(ay, by, u), ar + dr * u, asc * (bsc / asc) ** u)


def unrotate(m, keep=0.0):
    """m with its rotation scaled by `keep` about the piece's own centre (keep 0: upright)."""
    x, y, r, sc, _ = decompose(m)
    return compose(x, y, r * keep, sc)


def center_of(m, part=0):
    """World position of a part's centroid under the piece matrix m."""
    return m.transform_point(*CENTROID[part])


def draw_at(cr, world_m, cam_m, light, part=0, extra=None):
    """Draw a part with its world matrix through the camera map (whatever cr's current frame
    is: inside a hand's hold callback this keeps the hand's layering but not its transform)."""
    cr.save()
    cr.set_matrix(world_m.multiply(cam_m))
    draw_part(cr, light, part)
    if extra is not None:
        extra(cr)
    cr.restore()
