"""_cast_kit.py -- small private helpers shared by the supporting-cast rigs (gnome, elf, lioness,
troll). Not a creature module (the leading underscore keeps it out of the auto-import); the
public rig kit is base.py and these helpers only build on it.

    Q            per-draw context: palettes, the house shade() with the ground-bounce band off
                 by default (invisible on small parts, it doubles the cost of a shade() call)
    union / union_paths   several convex shapes / built (shape, outline) pairs -> ONE outline
                 fill + ONE shading pass
    flat         outline + one lit fill: the cheap recipe for parts a few px wide
    caps         a 2-3 joint limb as capsules (two arcs each; far cheaper than tube_paths)
    tube         base.tube_outline wound like hulls/ellipses, so it can join a union
    circle_pts   a projected sphere (orthographic) is a circle: hull points without 3D sampling
    yaw_of, screen_to_body, Exporter (rig points back to caller coordinates)
    sheet_bench  a sheet-only stand-in for the props kit's bench
"""

import math

from .. import core
from ..core import clamp
from . import base as B
from .base import Mat, Path

TAU = math.tau


class Q:
    """Per-draw context. Set the attributes a rig needs; P(mat) caches palettes for this light."""

    def __init__(self, cr, light, mats, t, pose):
        self.cr, self.light, self.M, self.t, self.pose = cr, light, mats, t, pose
        self.pal = {}
        self.light_nb = light.with_(bounce_strength=0.0) if light.bounce_strength else light
        self.lw = B.LINE
        self.detail = 2
        self.micro = False
        self.caller = cr.get_matrix()       # caller -> device, captured before the rig transform

    def P(self, mat):
        p = self.pal.get(mat)
        if p is None:
            p = self.pal[mat] = B.palette(self.light, mat)
        return p

    def shade(self, path, mat, lw=None, **kw):
        kw.setdefault("bounce", 0.0)
        return B.shade(self.cr, path, mat, self.light, self.lw if lw is None else lw, **kw)

    def lod(self, scale, detail=None, micro_at=1.4):
        """Level of detail from the on-screen scale (STYLE.md section 10) + line weight."""
        dev = scale * B.device_scale(self.cr)
        self.detail = detail if detail is not None else (2 if dev >= 0.9 else 1 if dev >= 0.55 else 0)
        self.micro = self.detail >= 2 and dev >= micro_at
        return dev


def union(q, hulls, mat, size, lw=None, flat_tone=None, **kw):
    """Convex point sets -> one silhouette (outline filled once), shaded once (flat_tone=k: one
    flat fill instead, lit mixed k toward shadow -- for small or mostly hidden parts). Returns
    the Path."""
    cr = q.cr
    lw = q.lw if lw is None else lw
    p = q.P(mat)
    cr.new_path()
    for h in hulls:
        core.smooth_closed(cr, B.offset_closed(h, lw), 0.85)
    core.src(cr, p.line)
    cr.fill()
    for h in hulls:
        core.smooth_closed(cr, h, 0.85)
    path = Path(cr)
    if flat_tone is not None:
        core.src(cr, core.mix(p.lit, p.shadow, flat_tone) if flat_tone else p.lit)
        cr.fill()
    else:
        q.shade(path, mat, lw=lw, outline=False, size=size, **kw)
    return path


def union_paths(q, pairs, mat, size, lw=None, flat_tone=None, **kw):
    """Like union, for built (shape, outline) pairs wound the same way (hulls, ellipses, caps,
    tube). flat_tone=k draws one flat fill (lit mixed k toward shadow) instead of shading."""
    cr = q.cr
    p = q.P(mat)
    cr.new_path()
    for _sh, o in pairs:
        o.add(cr)
    core.src(cr, p.line)
    cr.fill()
    for sh, _o in pairs:
        sh.add(cr)
    path = Path(cr)
    if flat_tone is not None:
        path.add(cr)
        core.src(cr, core.mix(p.lit, p.shadow, flat_tone) if flat_tone else p.lit)
        cr.fill()
    else:
        q.shade(path, mat, lw=q.lw if lw is None else lw, outline=False, size=size, **kw)
    return path


def flat(q, shape, outline, mat, tone=0.0):
    """Small parts: outline + one lit fill (tone > 0 mixes toward the shadow tone)."""
    cr = q.cr
    p = q.P(mat)
    outline.add(cr)
    core.src(cr, p.line)
    cr.fill()
    shape.add(cr)
    core.src(cr, core.mix(p.lit, p.shadow, tone) if tone else p.lit)
    cr.fill()
    return p


def caps(cr, pts, radii, lw):
    """A limb as capsules, wound like hulls/ellipses -> (shape, outline)."""
    cr.new_path()
    for (a, b), ra, rb in zip(zip(pts, pts[1:]), radii, radii[1:]):
        core.capsule(cr, a[0], a[1], ra, b[0], b[1], rb)
    shape = Path(cr)
    for (a, b), ra, rb in zip(zip(pts, pts[1:]), radii, radii[1:]):
        core.capsule(cr, a[0], a[1], ra + lw, b[0], b[1], rb + lw)
    return shape, Path(cr)


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def tube(cr, pts, radii, lw, samples=4, tension=0.8):
    """base.tube_paths wound like convex hulls / ellipses (base.tube_outline winds the other
    way), so a tube can join hulls in ONE union without the overlap cancelling out."""
    a, b = B.tube_outline(pts, radii, samples, tension, (0.0, lw))
    if signed_area(a) < 0.0:
        a, b = a[::-1], b[::-1]
    cr.new_path()
    core.smooth_closed(cr, a, 0.9)
    shape = Path(cr)
    core.smooth_closed(cr, b, 0.9)
    return shape, Path(cr)


def circle_pts(c, r, n=10, sy=1.0):
    """Points round a projected sphere (orthographic: a circle) for hulls."""
    return [(c[0] + math.cos(TAU * i / n) * r, c[1] + math.sin(TAU * i / n) * r * sy) for i in range(n)]


def yaw_of(facing, turn):
    base = {1: 1.0, -1: -1.0, 0: 0.0}.get(int(facing), 0.0)
    return clamp(base + turn * 0.6, -1.45, 1.45)


def facing_dir(yaw):
    """The screen-facing direction in body space (3/4 right: forward and toward her left)."""
    sy = math.sin(yaw)
    return (math.copysign(math.cos(yaw), sy) * abs(sy), 0.0, 1.0 + (abs(sy) - 1.0) * abs(sy))


def screen_to_body(q, proj, pt, depth):
    """Caller coordinates -> body space at camera depth `depth` (inverse of the projection).
    Call inside the rig transform (q.caller was captured before it)."""
    inv = q.cr.get_matrix()
    inv.invert()
    dx, dy = q.caller.transform_point(pt[0], pt[1])
    lx, ly = inv.transform_point(dx, dy)
    X = lx * proj.c - depth * proj.s
    Z = lx * proj.s + depth * proj.c
    Y = (ly - depth * proj.se) / proj.ce
    return (X, Y, Z)


class Exporter:
    """Maps rig-local points to the caller's coordinates. Create it right before cr.restore()
    of the rig transform: ex = Exporter(cr); cr.restore(); ex.ready(cr); ex(p)."""

    def __init__(self, cr):
        self.m = cr.get_matrix()
        self.inv = None

    def ready(self, cr):
        self.inv = cr.get_matrix()
        self.inv.invert()

    def __call__(self, p):
        dx, dy = self.m.transform_point(p[0], p[1])
        return self.inv.transform_point(dx, dy)

    def hand(self, hf, scale):
        if hf is not None:
            hf.x, hf.y = self((hf.x, hf.y))
            hf.tips = [self(tp) for tp in hf.tips]
            hf.palm = self(hf.palm)
            hf.scale *= scale
        return hf


def sheet_bench(cr, x, ground, sc, seat_h=B.BENCH_SEAT_H, w=240.0, light=None, back=True):
    """Sheet-only stand-in for the props kit's wrought-iron and oak bench (seat at seat_h)."""
    light = light or B.LIGHTS["neutral"]
    iron = B.palette(light, Mat.of("#3a3a40"))
    oak = B.palette(light, Mat.of("#8a5f3a"))
    y = ground - seat_h * sc
    core.src(cr, iron.lit)
    for lx in (x - w * 0.42, x + w * 0.42):
        cr.rectangle(lx - 3 * sc, y, 6 * sc, seat_h * sc)
    if back:
        for lx in (x - w * 0.42, x + w * 0.42):
            cr.rectangle(lx - 3 * sc, y - 95 * sc, 6 * sc, 95 * sc)
    cr.fill()
    if back:
        for k in range(2):
            core.src(cr, oak.shadow)
            cr.rectangle(x - w / 2, y - (88 - 26 * k) * sc, w, 16 * sc)
            cr.fill()
    core.src(cr, oak.lit)
    cr.rectangle(x - w / 2, y - 7 * sc, w, 11 * sc)
    cr.fill()
    core.src(cr, oak.shadow)
    cr.rectangle(x - w / 2, y + 4 * sc, w, 3 * sc)
    cr.fill()


def head_frame(draw, pose, scale, light, t=0.4):
    """Where a rig's head lands for this pose (dry run on a scratch surface) -- for sheets."""
    _s, c = core.frame(4, 4)
    return draw(c, 0.0, 0.0, scale, pose, light, t).head
