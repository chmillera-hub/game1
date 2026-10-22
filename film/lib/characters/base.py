"""base.py -- THE SHARED RIG KIT. Every creature module builds on this so the cast reads as one film.

Contents
  Light, LIGHTS, Mat, palette()            scene lighting -> per-material color palettes
  Path / capture(), shade(), flat(),        the house SHADING RECIPE (outline-under, cel shadow,
  outline_under(), detail_line(), occlusion()   rim light, soft form gradient, occlusion)
  Proj, v3 math, ik2(), ik3()               "3D-lite": joints posed in 3D, projected with yaw
  tube(), limb()                            seamless tapered limbs with rounded joints
  hand(), HandFrame                         4-digit cartoon hands/paws/claws with hold callbacks
  Expr, MOODS, expr(), eye(), brow_shape(), mouth()      the face kit (all creatures share eyes)
  breathing(), auto_blink(), sway(), spring(), wobble(), chain(), lagged()   secondary motion
  walk_cycle()                              phase -> hip bob, foot plants, arm swing
  contact_shadow()                          soft ground shadow
  SheetItem                                 character-sheet convention (see API.md)

Units: every rig draws in its own local units = screen px at scale 1.0, origin at the anchor
(feet center standing / seat point sitting), y down. Angles in radians.
"""

import functools
import math
from dataclasses import dataclass, field, replace

import cairocffi as cairo
from cairocffi import cairo as _lib
from cairocffi import ffi as _ffi

from .. import core
from ..core import clamp, col, lerp, smooth

TAU = math.tau

# House line weight: 2.2 px for a character ~500 px tall (0.45% of height); never thinner than
# MIN_LINE_PX on screen so small/far characters keep their silhouettes.
LINE = 2.2
MIN_LINE_PX = 1.0


# ========================================================================================
# Light & materials
# ========================================================================================

def _unit(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


@dataclass(frozen=True)
class Light:
    """How a scene lights its characters. All colors are float RGB tuples.

    key        multiplies the material color on lit areas (1,1,1 = neutral white light)
    ambient    multiplies the material color in shadow (darker + usually cooler)
    rim        color of the thin rim/edge light; rim_strength 0..1
    direction  unit vector pointing TOWARD the key light, screen space (y down): (-0.6,-0.8) =
               light from the upper left
    rim_direction  toward the rim light (None: from above, opposite side of the key)
    shadow_size    scales the width of shadow crescents (1 = house default)
    bounce / bounce_strength   subtle reflected ground light on the underside (warm grass, wet street)
    """
    key: tuple = (1.0, 0.97, 0.93)
    ambient: tuple = (0.56, 0.60, 0.78)
    rim: tuple = (1.0, 0.96, 0.88)
    rim_strength: float = 0.45
    direction: tuple = (-0.55, -0.83)
    rim_direction: tuple = None
    exposure: float = 1.0
    shadow_size: float = 1.0
    bounce: tuple = None
    bounce_strength: float = 0.0
    name: str = "neutral"

    def rim_dir(self):
        if self.rim_direction is not None:
            return _unit(self.rim_direction)
        kx = self.direction[0]
        return _unit((-0.75 * (1 if kx >= 0 else -1), -0.66))

    def key_dir(self):
        return _unit(self.direction)

    def with_(self, **kw):
        return replace(self, **kw)

    @staticmethod
    def lerp(a, b, u):
        """Blend two lights (for light changes inside a shot: dusk -> lantern)."""
        u = clamp(u)

        def lt(x, y):
            return tuple(p + (q - p) * u for p, q in zip(x, y))

        bounce = None
        if a.bounce or b.bounce:
            bounce = lt(a.bounce or b.bounce, b.bounce or a.bounce)
        return Light(lt(a.key, b.key), lt(a.ambient, b.ambient), lt(a.rim, b.rim),
                     lerp(a.rim_strength, b.rim_strength, u), _unit(lt(a.direction, b.direction)),
                     None if a.rim_direction is None and b.rim_direction is None else
                     _unit(lt(a.rim_dir(), b.rim_dir())),
                     lerp(a.exposure, b.exposure, u), lerp(a.shadow_size, b.shadow_size, u),
                     bounce, lerp(a.bounce_strength, b.bounce_strength, u), f"{a.name}>{b.name}")


# Scene light presets (see the SPEC palette table). Scenes may tweak with .with_(...)
LIGHTS = {
    "neutral": Light(),
    # S1 cold green-cyan will-o'-wisp lamps overhead
    "washhouse": Light(key=(0.80, 1.00, 0.96), ambient=(0.30, 0.46, 0.50), rim=(0.62, 1.0, 0.90),
                       rim_strength=0.6, direction=(0.25, -0.97), rim_direction=(-0.8, -0.6),
                       name="washhouse"),
    # S2 over-bright clinical white/mint light-orbs
    "apothecary": Light(key=(1.06, 1.08, 1.04), ambient=(0.66, 0.76, 0.76), rim=(0.92, 1.0, 0.96),
                        rim_strength=0.4, direction=(0.2, -0.98), name="apothecary"),
    # S3 rainy night: deep navy ambient, sodium-orange lantern key
    "street_night": Light(key=(1.08, 0.76, 0.48), ambient=(0.24, 0.31, 0.52), rim=(1.0, 0.66, 0.32),
                          rim_strength=0.7, direction=(0.62, -0.78), rim_direction=(-0.7, -0.7),
                          bounce=(0.35, 0.45, 0.75), bounce_strength=0.18, name="street_night"),
    # S4 tavern door: hot magenta/amber
    "tavern": Light(key=(1.12, 0.80, 0.62), ambient=(0.52, 0.30, 0.50), rim=(1.0, 0.45, 0.75),
                    rim_strength=0.65, direction=(-0.7, -0.7), name="tavern"),
    # S5 town square evening: grey-blue stone, cold crystal glows
    "square": Light(key=(0.86, 0.91, 1.02), ambient=(0.40, 0.46, 0.62), rim=(0.62, 0.86, 1.0),
                    rim_strength=0.5, direction=(-0.4, -0.92), name="square"),
    # S6 dusk garden: violet ambient, peach low sun
    "dusk": Light(key=(1.10, 0.88, 0.74), ambient=(0.54, 0.46, 0.68), rim=(1.0, 0.78, 0.58),
                  rim_strength=0.6, direction=(-0.86, -0.5), bounce=(0.45, 0.5, 0.3),
                  bounce_strength=0.1, name="dusk"),
    # S7 golden hour
    "golden": Light(key=(1.18, 0.94, 0.64), ambient=(0.60, 0.50, 0.58), rim=(1.0, 0.82, 0.46),
                    rim_strength=0.8, direction=(-0.9, -0.42), bounce=(0.5, 0.45, 0.25),
                    bounce_strength=0.12, name="golden"),
    # S7 later: blue hour
    "blue_hour": Light(key=(0.74, 0.80, 1.0), ambient=(0.36, 0.38, 0.60), rim=(0.78, 0.82, 1.0),
                       rim_strength=0.4, direction=(-0.6, -0.8), name="blue_hour"),
    # S8 night garden, one warm lantern overhead
    "lantern_night": Light(key=(1.12, 0.84, 0.54), ambient=(0.22, 0.26, 0.46), rim=(1.0, 0.74, 0.42),
                           rim_strength=0.6, direction=(0.15, -0.99), rim_direction=(0.0, -1.0),
                           name="lantern_night"),
}


@dataclass(frozen=True)
class Mat:
    """A material: base color + how it takes light.
    sss       warm translucency in shadows (skin, ears, wing membranes, belly) 0..1
    shadow_k  >1 deeper shadows (wool, velvet), <1 lighter (pale glossy things)
    sheen     strength of a small specular highlight (horn, claws, glass, leather)
    line_k    outline darkness relative to the shadow tone (lower = darker)
    """
    base: tuple
    sss: float = 0.0
    shadow_k: float = 1.0
    sheen: float = 0.0
    line_k: float = 0.55

    @staticmethod
    def of(c, **kw):
        return Mat(tuple(col(c)[:3]), **kw)


@dataclass(frozen=True)
class Palette:
    lit: tuple
    shadow: tuple
    line: tuple
    deep: tuple
    rim: tuple
    hi: tuple
    base: tuple


_WARM = (1.0, 0.55, 0.42)
KEY_TINT = 0.55


@functools.lru_cache(maxsize=4096)
def palette(light, mat):
    """Colors of material `mat` under `light` (cached)."""
    if not isinstance(mat, Mat):
        mat = Mat.of(mat)
    b = mat.base
    k = light.key
    e = light.exposure
    # the key light TINTS the lit side (55%) rather than fully multiplying it, so characters
    # keep their identity colors under strongly colored lights; shadows take the ambient fully
    lit = tuple(clamp(b[i] * (1.0 + (k[i] - 1.0) * KEY_TINT) * e) for i in range(3))
    amb = light.ambient
    sk = mat.shadow_k if mat.shadow_k > 0 else 1.0
    shadow = tuple(clamp(b[i] * amb[i] * e / sk) for i in range(3))
    if mat.sss > 0:
        warm = tuple(clamp(b[i] * _WARM[i] * 1.1) for i in range(3))
        shadow = core.mix(shadow, warm, mat.sss * 0.45)[:3]
    line = core.saturate(tuple(v * mat.line_k for v in shadow), 0.25)[:3]
    deep = tuple(v * 0.7 for v in shadow)
    hi = core.tint(lit, 0.45)[:3]
    return Palette(lit, shadow, line, deep, tuple(light.rim), hi, tuple(b))


def pal(light, c, **kw):
    """Shortcut: palette for a plain color (kw -> Mat fields)."""
    return palette(light, Mat.of(c, **kw))


# ========================================================================================
# Paths and the shading recipe
# ========================================================================================


class Path:
    """A captured cairo path (raw C struct) that can be re-appended many times, cheaply,
    optionally shifted. Coordinates are in the user space active when it was captured."""
    __slots__ = ("p",)

    def __init__(self, cr):
        self.p = _ffi.gc(_lib.cairo_copy_path(cr._pointer), _lib.cairo_path_destroy)
        cr.new_path()

    def add(self, cr, dx=0.0, dy=0.0):
        if dx or dy:
            cr.translate(dx, dy)
            _lib.cairo_append_path(cr._pointer, self.p)
            cr.translate(-dx, -dy)
        else:
            _lib.cairo_append_path(cr._pointer, self.p)
        return self

    def extents(self, cr):
        self.add(cr)
        e = cr.path_extents()
        cr.new_path()
        return e


def capture(cr):
    """Capture (and clear) the current path."""
    return Path(cr)


# ---- shape builders that also return a DILATED outline path ----------------------------
# Filling a dilated copy in the line color before the shape is ~3x cheaper than stroking the
# shape (cairo's curve stroker is CPU heavy). Each returns (shape: Path, outline: Path) to pass
# to shade(cr, shape, ..., outline=outline).

def offset_closed(pts, d):
    """Offset a closed polygon outward by d (either winding)."""
    n = len(pts)
    area = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    sgn = d if area > 0 else -d
    out = []
    for i in range(n):
        px, py = pts[i - 1]
        qx, qy = pts[(i + 1) % n]
        tx, ty = qx - px, qy - py
        L = math.hypot(tx, ty) or 1e-9
        out.append((pts[i][0] + ty / L * sgn, pts[i][1] - tx / L * sgn))
    return out


def smooth_paths(cr, pts, lw, tension=0.85):
    """Smooth closed curve through pts + its outline (offset by lw)."""
    cr.new_path()
    core.smooth_closed(cr, pts, tension)
    shape = Path(cr)
    core.smooth_closed(cr, offset_closed(pts, lw), tension)
    return shape, Path(cr)


def hull_paths(cr, pts, lw, tension=0.85):
    """Convex hull of pts as a smooth closed curve + its outline. Returns (shape, outline, hull)."""
    hull = core.convex_hull(pts)
    s, o = smooth_paths(cr, hull, lw, tension)
    return s, o, hull


def ellipse_paths(cr, cx, cy, rx, ry, lw, angle=0.0):
    cr.new_path()
    core.ellipse(cr, cx, cy, rx, ry, angle)
    shape = Path(cr)
    core.ellipse(cr, cx, cy, rx + lw, ry + lw, angle)
    return shape, Path(cr)


def taper_paths(cr, pts, w0, w1, lw, cap=True, profile=None):
    """core.tapered ribbon + its outline (widths + 2*lw)."""
    cr.new_path()
    core.tapered(cr, pts, w0, w1, profile=profile, cap=cap)
    shape = Path(cr)
    if profile is not None:
        core.tapered(cr, pts, w0 + 2 * lw, w1 + 2 * lw, profile=lambda s: profile(s) + 2 * lw, cap=cap)
    else:
        core.tapered(cr, pts, w0 + 2 * lw, w1 + 2 * lw, cap=cap)
    return shape, Path(cr)


def fill_outlines(cr, outlines, color):
    """Fill several outline paths at once (a union's silhouette line)."""
    cr.new_path()
    for o in outlines:
        o.add(cr)
    core.src(cr, color)
    cr.fill()


def build(cr, fn, *a, **kw):
    """Run a path-building function and capture the result: build(cr, core.ellipse, x, y, rx, ry)."""
    cr.new_path()
    fn(cr, *a, **kw)
    return Path(cr)


def local_dir(cr, v):
    """Screen-space direction -> unit vector in the current user space (handles mirroring)."""
    x, y = cr.device_to_user_distance(v[0], v[1])
    n = math.hypot(x, y) or 1.0
    return x / n, y / n


def device_scale(cr):
    """How many screen px one user unit is (uniform scale assumed)."""
    x, y = cr.user_to_device_distance(1.0, 0.0)
    return math.hypot(x, y)


LINE_GROW = 0.5     # close-ups: how fast the on-screen ink line grows with zoom past 1.0


def line_for(line, dev, k=1.0):
    """THE house line width, in LOCAL units, for every outlined drawing (cast and props).

    line  the width in local units at scale 1.0 (e.g. LINE)
    dev   screen px per local unit (scale * device_scale(cr) for most rigs)
    k     local units per scale-1 px (1 for most rigs; 1/SIZE_K or 1/fit for calibrated builds)

    Never thinner than MIN_LINE_PX on screen (far figures keep their silhouettes). Past scale
    1.0 -- a close-up or a camera push -- the ink line thickens at only LINE_GROW of the
    drawing's rate (a 3x close-up gets a 2x line, not a 3x marker outline), so the line reads
    the same fine weight across shot sizes, as in a hand-inked 2D feature. Continuous in dev:
    no popping during camera moves."""
    dev = max(dev, 1e-6)
    zoom = dev * k
    if zoom > 1.0:
        line = line * (1.0 + LINE_GROW * (zoom - 1.0)) / zoom
    return max(line, MIN_LINE_PX / dev)


def line_w(cr, lw):
    """A line width in user units for the current transform (line_for with k=1): never below
    MIN_LINE_PX on screen, and only half-growing in close-ups. For props drawn inside hold
    callbacks, where 1 unit = 1 px of the holder at scale 1.0."""
    s = device_scale(cr)
    return line_for(lw, s) if s > 0 else lw


def outline_under(cr, path, lw, color, exclude=None):
    """Stroke `path` at 2*lw BEFORE filling it: after the fill only the outer half (lw) remains,
    so overlapping sub-paths (unions) get one seamless silhouette line. exclude: a single-contour
    Path inside which no outline is drawn (e.g. fingers' outline not crossing the palm)."""
    if lw <= 0:
        return
    if exclude is not None:
        cr.save()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.rectangle(-1e5, -1e5, 2e5, 2e5)
        exclude.add(cr)
        cr.clip()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    path.add(cr)
    cr.set_line_width(2.0 * lw)
    core.src(cr, color)
    cr.stroke()
    if exclude is not None:
        cr.restore()


# the ground-bounce band (dusk, golden, street_night lights) is drawn only on parts at least this
# thick (local units = px at scale 1): on fingers, claws, horns and tail tips the faint 6 px band
# is invisible but cost a full extra fill (~35% of a character's draw under those lights)
BOUNCE_MIN_SIZE = 40.0


@functools.lru_cache(maxsize=8192)
def _rim_tone(p, rs, f):
    """Rim light ADDS light in proportion to how bright the material is (a dark coat gets a
    subtle sheen, pale horns a strong one), over the tone beneath it (f = 1: shadow side)."""
    under = core.mix(p.lit, p.shadow, f)
    k = rs * (0.3 + 0.7 * core.luma(p.base) ** 0.7)
    return tuple(min(1.0, u + c * k) for u, c in zip(under[:3], p.rim[:3]))


def shade(cr, path, mat, light, lw=LINE, *, shadow=1.0, rim=1.0, outline=True, size=None,
          bounce=1.0, line_color=None, alpha=1.0, soft=None):
    """THE HOUSE SHADING RECIPE. Draws `path` (a Path) as a lit cel-shaded form, solid fills only
    (gradients cost ~5x more per part):

      1. outline-under: stroke 2*lw in the palette line color (only the outer half survives)
      2. clip to the shape; paint the RIM tone (rim color blended over the tone beneath it)
      3. fill the shape shifted AWAY from the rim light with the SHADOW tone -> a rim band of
         ~1.6 line widths survives on the edge facing the rim light
      4. fill it shifted TOWARD the key light (and away from the rim) with the LIT tone ->
         a crisp shadow crescent (~20% of `size`) remains on the side away from the key
      5. BOUNCE (only if the light has it): faint band on the underside

    outline: True = stroke-under (works for any path), False = none, or a Path made by one of
    the *_paths() builders (a dilated copy, filled -- ~3x cheaper than stroking; preferred).
    size: part size in user units (default: min side of the path extents). shadow / rim /
    bounce scale those layers (0 disables). Unions of overlapping sub-paths are fine for every
    step except bounce. `soft` is accepted for compatibility and ignored.
    Returns the Palette used. Cost ~0.2-0.5 ms per part depending on area."""
    p = palette(light, mat if isinstance(mat, Mat) else Mat.of(mat))
    rs = light.rim_strength * rim
    bs = light.bounce_strength * bounce if light.bounce else 0.0
    path.add(cr)
    if size is None:
        x0, y0, x1, y1 = cr.path_extents()
        size = min(x1 - x0, y1 - y0)
    if isinstance(outline, Path):
        cr.new_path()
        outline.add(cr)
        core.src(cr, line_color if line_color is not None else p.line, alpha if alpha < 1 else None)
        cr.fill()
    elif outline and lw > 0:
        cr.set_line_width(2.0 * lw)
        core.src(cr, line_color if line_color is not None else p.line, alpha if alpha < 1 else None)
        cr.stroke()
    else:
        cr.new_path()
    if alpha < 1.0:
        cr.push_group()
    cr.save()
    path.add(cr)
    cr.clip()
    lx, ly = local_dir(cr, light.direction)
    d = max(0.0, shadow) * light.shadow_size * 0.2 * size
    if rs > 0.01:
        rx, ry = local_dir(cr, light.rim_dir())
        rw = clamp(size * 0.09, max(lw, 0.6) * 0.6, max(lw, 0.6) * 1.6)   # thin parts: thin rim
        f = clamp(0.5 - 0.5 * (rx * lx + ry * ly))          # 1 = rim falls on the shadow side
        core.src(cr, _rim_tone(p, round(clamp(rs), 2), round(f, 2)))
        cr.paint()
        path.add(cr, -rx * rw, -ry * rw)
        core.src(cr, p.shadow)
        cr.fill()
        path.add(cr, lx * d - rx * rw, ly * d - ry * rw)
    else:
        core.src(cr, p.shadow)
        cr.paint()
        path.add(cr, lx * d, ly * d)
    core.src(cr, p.lit)
    cr.fill()
    if bs > 0.01 and size >= BOUNCE_MIN_SIZE:
        bx, by = local_dir(cr, (0.0, 1.0))
        bw = max(lw, 0.6) * 2.6
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        path.add(cr)
        path.add(cr, -bx * bw, -by * bw)
        core.src(cr, core.tint(core.mul(p.base, light.bounce), 0.2), clamp(bs))
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    cr.restore()
    if alpha < 1.0:
        cr.pop_group_to_source()
        cr.paint_with_alpha(alpha)
    return p


def flat(cr, path, color, lw=0.0, line=None):
    """Plain fill with an optional outline-under (small details: claws, buttons, pupils)."""
    if lw > 0 and line is not None:
        path.add(cr)
        cr.set_line_width(2 * lw)
        core.src(cr, line)
        cr.stroke()
    path.add(cr)
    core.src(cr, color)
    cr.fill()


def detail_line(cr, pts, w, color, alpha=1.0, taper=(0.15, 1.0, 0.15), samples=6):
    """An inked internal line (folds, creases, scale marks, fur strokes): a smooth tapered ribbon
    through pts whose width follows taper=(start, middle, end) multipliers of w."""
    a, m, b = taper

    def prof(s):
        return w * (a + (m - a) * (s / 0.5) if s < 0.5 else m + (b - m) * ((s - 0.5) / 0.5))

    core.tapered(cr, pts, w, w, profile=prof, samples=samples, cap=True)
    core.src(cr, color, alpha)
    cr.fill()


def detail_lines(cr, lines, w, color, alpha=1.0, taper=(0.15, 1.0, 0.15)):
    """Many inked lines of one style in a single fill (much cheaper than detail_line per line).
    lines: list of point lists."""
    a, m, b = taper

    def prof(s):
        return w * (a + (m - a) * (s / 0.5) if s < 0.5 else m + (b - m) * ((s - 0.5) / 0.5))

    cr.new_path()
    for pts in lines:
        if len(pts) >= 2:
            core.tapered(cr, pts, w, w, profile=prof, cap=True)
    core.src(cr, color, alpha)
    cr.fill()


def occlusion(cr, x, y, rx, ry, color, alpha=0.4, clip=None):
    """Soft ambient-occlusion blot (where forms meet: under the chin, armpits, collar).
    clip: optional Path to keep it inside a form."""
    if clip is not None:
        cr.save()
        clip.add(cr)
        cr.clip()
    c = col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / max(rx, 1e-3))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, rx)
    g.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(0.6, c[0], c[1], c[2], alpha * 0.4)
    g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
    cr.set_source(g)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()
    if clip is not None:
        cr.restore()


def sheen(cr, x, y, rx, ry, angle=0.0, alpha=0.6, color=(1, 1, 1)):
    """Small soft specular highlight (horns, claws, glass, eyes, wet noses)."""
    c = col(color)
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(1.0, ry / max(rx, 1e-3))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, rx)
    g.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
    cr.set_source(g)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()


# ========================================================================================
# 3D-lite: pose joints in 3D, project to the screen with a yaw (turn) and a slight camera
# elevation. Body space: X = character's left (screen right at yaw 0), Y = down, Z = forward
# (toward the camera at yaw 0). yaw > 0 turns the character to face screen-right.
# ========================================================================================


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_len(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def v_norm(a):
    n = v_len(a) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def v_lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)


def m_rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def m_rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def m_rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def m_mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def m_vec(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


M_ID = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


class Proj:
    """Orthographic projection of body space onto the character's local 2D drawing space.

    yaw: turn about the vertical axis (+ faces screen-right). elev: camera looks down by this
    angle (small, ~0.1): points nearer the camera sit slightly lower, so feet/hems read round."""
    __slots__ = ("yaw", "elev", "c", "s", "se", "ce")

    def __init__(self, yaw=0.0, elev=0.1):
        self.yaw, self.elev = yaw, elev
        self.c, self.s = math.cos(yaw), math.sin(yaw)
        self.se, self.ce = math.sin(elev), math.cos(elev)

    def __call__(self, p):
        """-> (x, y, depth) ; depth > 0 is nearer the camera."""
        x = p[0] * self.c + p[2] * self.s
        z = -p[0] * self.s + p[2] * self.c
        return (x, p[1] * self.ce + z * self.se, z)

    def xy(self, p):
        x = p[0] * self.c + p[2] * self.s
        z = -p[0] * self.s + p[2] * self.c
        return (x, p[1] * self.ce + z * self.se)

    def depth(self, p):
        return -p[0] * self.s + p[2] * self.c

    def ellipse(self, center, a, c):
        """Projected half-width of a horizontal ellipse (half-axes a along X, c along Z) and its
        center (x, y): the silhouette of a cross-section."""
        x, y = self.xy(center)
        hw = math.sqrt((a * self.c) ** 2 + (c * self.s) ** 2)
        return x, y, hw


def ik2(sx, sy, tx, ty, l1, l2, bend=1.0):
    """2D two-bone IK. Returns (elbow_x, elbow_y, wrist_x, wrist_y); the wrist is pulled in if
    the target is out of reach. bend=+1/-1 picks which side the elbow goes."""
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    dmax = (l1 + l2) * 0.999
    dmin = abs(l1 - l2) + 1e-3
    if d > dmax:
        tx, ty = sx + dx / d * dmax, sy + dy / d * dmax
        d = dmax
    elif d < dmin:
        d = dmin if d > 1e-6 else dmin
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = (dx / (math.hypot(dx, dy) or 1.0), dy / (math.hypot(dx, dy) or 1.0))
    ex = sx + ux * a - uy * h * bend
    ey = sy + uy * a + ux * h * bend
    return ex, ey, tx, ty


def ik3(S, T, l1, l2, pole):
    """3D two-bone IK: shoulder S, target T, bone lengths, `pole` = direction the elbow should
    point. Returns (elbow, wrist) with the wrist pulled in if T is out of reach."""
    d_vec = v_sub(T, S)
    d = v_len(d_vec)
    dmax = (l1 + l2) * 0.999
    if d > dmax:
        T = v_add(S, v_mul(d_vec, dmax / d))
        d = dmax
    d = max(d, abs(l1 - l2) + 1e-3)
    u = v_norm(v_sub(T, S))
    pn = v_sub(pole, v_mul(u, v_dot(pole, u)))
    if v_len(pn) < 1e-6:
        pn = (0.0, 1.0, 0.0) if abs(u[1]) < 0.9 else (0.0, 0.0, 1.0)
        pn = v_sub(pn, v_mul(u, v_dot(pn, u)))
    pn = v_norm(pn)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    E = v_add(S, v_add(v_mul(u, a), v_mul(pn, h)))
    return E, T


# ========================================================================================
# Limbs: tube() builds ONE closed contour around a spine -> no seams at joints
# ========================================================================================


def tube_outline(pts, radii, samples=5, tension=0.8, extra=(0.0,), cap_start=True, cap_end=True):
    """Outline polygons (one per value in `extra`, added to every radius) around a spine."""
    if len(pts) > 2:
        sp = core.spline(pts, n=samples, tension=tension)
    else:
        sp = [core.lerp_pt(pts[0], pts[1], k / 4.0) for k in range(5)]
    nseg = len(pts) - 1
    m = len(sp)
    rs, tn = [], []
    for i in range(m):
        f = i / (m - 1) * nseg
        j = min(int(f), nseg - 1)
        u = f - j
        rs.append(radii[j] + (radii[j + 1] - radii[j]) * u)
        if i == 0:
            tx, ty = sp[1][0] - sp[0][0], sp[1][1] - sp[0][1]
        elif i == m - 1:
            tx, ty = sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1]
        else:
            tx, ty = sp[i + 1][0] - sp[i - 1][0], sp[i + 1][1] - sp[i - 1][1]
        L = math.hypot(tx, ty) or 1e-9
        tn.append((tx / L, ty / L))
    outs = []
    for ex in extra:
        left, right = [], []
        for i in range(m):
            tx, ty = tn[i]
            r = rs[i] + ex
            lp = (sp[i][0] - ty * r, sp[i][1] + tx * r)
            rp = (sp[i][0] + ty * r, sp[i][1] - tx * r)
            # de-loop: an offset point must not move backwards along the spine
            if left and ((lp[0] - left[-1][0]) * tx + (lp[1] - left[-1][1]) * ty) < 0:
                lp = left[-1]
            if right and ((rp[0] - right[-1][0]) * tx + (rp[1] - right[-1][1]) * ty) < 0:
                rp = right[-1]
            left.append(lp)
            right.append(rp)
        out = list(left)
        if cap_end:
            a0 = math.atan2(left[-1][1] - sp[-1][1], left[-1][0] - sp[-1][0])
            r = rs[-1] + ex
            out += [(sp[-1][0] + math.cos(a0 - math.pi * k / 4) * r, sp[-1][1] + math.sin(a0 - math.pi * k / 4) * r)
                    for k in (1, 2, 3)]
        out += right[::-1]
        if cap_start:
            a0 = math.atan2(right[0][1] - sp[0][1], right[0][0] - sp[0][0])
            r = rs[0] + ex
            out += [(sp[0][0] + math.cos(a0 - math.pi * k / 4) * r, sp[0][1] + math.sin(a0 - math.pi * k / 4) * r)
                    for k in (1, 2, 3)]
        pts2 = [out[0]]
        for q in out[1:]:
            if abs(q[0] - pts2[-1][0]) + abs(q[1] - pts2[-1][1]) > 0.35:
                pts2.append(q)
        outs.append(pts2)
    return outs


def tube(cr, pts, radii, samples=5, tension=0.8, cap_start=True, cap_end=True):
    """Build a smooth closed outline around the polyline `pts` with radius radii[i] at each
    point (round caps, rounded joints, inner side de-looped). One contour -> no seams at
    joints. For a 2-segment limb pass (shoulder, elbow, wrist)."""
    if len(pts) < 2:
        return
    core.smooth_closed(cr, tube_outline(pts, radii, samples, tension, (0.0,), cap_start, cap_end)[0], tension=0.9)


def tube_paths(cr, pts, radii, lw, samples=5, tension=0.8, cap_start=True, cap_end=True):
    """tube() + its dilated outline, from one spine computation -> (shape, outline)."""
    a, b = tube_outline(pts, radii, samples, tension, (0.0, lw), cap_start, cap_end)
    cr.new_path()
    core.smooth_closed(cr, a, tension=0.9)
    shape = Path(cr)
    core.smooth_closed(cr, b, tension=0.9)
    return shape, Path(cr)


def limb(cr, a, b, c, ra, rb, rc, **kw):
    """Two-segment limb a->b->c with radii (shoulder/hip, elbow/knee, wrist/ankle). Builds path."""
    tube(cr, [a, b, c], [ra, rb, rc], **kw)


# ========================================================================================
# Hands
# ========================================================================================

# finger curl per finger (index, middle, ring; 0 straight .. 1 fist), fan spread (rad),
# thumb (angle rad from the hand axis toward the thumb side, curl 0..1)
HAND_POSES = {
    "relaxed": dict(curl=(0.22, 0.30, 0.38), spread=0.10, thumb=(-0.55, 0.20)),
    "open":    dict(curl=(0.02, 0.00, 0.04), spread=0.24, thumb=(-1.05, 0.0)),
    "flat":    dict(curl=(0.00, 0.00, 0.02), spread=0.03, thumb=(-0.32, 0.0)),
    "fist":    dict(curl=(1.00, 1.00, 1.00), spread=0.00, thumb=(-0.10, 0.70)),
    "point":   dict(curl=(0.00, 0.95, 1.00), spread=0.04, thumb=(-0.25, 0.60)),
    "grip":    dict(curl=(0.70, 0.74, 0.80), spread=0.02, thumb=(-0.20, 0.50)),
    "cup":     dict(curl=(0.40, 0.45, 0.50), spread=0.04, thumb=(-0.45, 0.25)),
    "pinch":   dict(curl=(0.55, 0.80, 0.90), spread=0.04, thumb=(-0.20, 0.45)),
    "back":    dict(curl=(0.10, 0.08, 0.12), spread=0.03, thumb=(-0.30, 0.08)),
    "offer":   dict(curl=(0.10, 0.08, 0.12), spread=0.14, thumb=(-0.85, 0.05)),
}


@dataclass
class HandFrame:
    """Where a hand is, in the CALLER's coordinates: grip point (x, y), the direction the
    fingers point (angle, rad), the drawing scale, and fingertip positions (index first).
    Props attach here: draw the stone/book/bread at (x, y) rotated by angle."""
    x: float
    y: float
    angle: float
    scale: float
    tips: list = field(default_factory=list)
    palm: tuple = (0.0, 0.0)
    flip: bool = False


def hand(cr, x, y, angle, size, pose, mat, light, lw=LINE, *, flip=False, claw=None,
         claw_len=0.085, pad=None, show_palm=False, hold=None, stamp=None, fingers=3,
         finger_len=1.0, finger_w=1.0, thumb=True, palm_w=1.0, curl_add=0.0, back_detail=None,
         knuckles=True, detail=2, hold_behind=False):
    """Draw a cartoon hand/paw (3 fingers + thumb by default, the house standard).

    (x, y) wrist center, angle = direction from wrist toward the fingers, size = wrist-to-
    fingertip length (straight). pose: a HAND_POSES name or dict. flip mirrors the thumb side.
    claw: claw color (None = no claws). pad: palm-pad color shown when show_palm. hold(cr, f):
    callback drawing a held prop between the palm and the curled fingers -- cr is set to a frame
    at the grip point with +x along the fingers, 1 unit = 1 user unit of the caller.
    hold_behind=True draws the prop BEHIND the whole hand instead (same frame) -- for a prop
    pressed to the body under the back of the hand, e.g. the speaking stone held to an ear.
    stamp(cr): callback drawn on the BACK of the hand (e.g. the SMILE stamp), un-mirrored.
    detail: 2 full, 1 no knuckle ticks, 0 silhouette + claws only (small/far characters).
    Returns a HandFrame in the caller's coordinates.
    """
    P = HAND_POSES[pose] if isinstance(pose, str) else pose
    curls = [clamp(c + curl_add) for c in P["curl"]]
    spread = P["spread"]
    th_ang, th_curl = P["thumb"]
    p = palette(light, mat if isinstance(mat, Mat) else Mat.of(mat))
    s = size
    fy = -1.0 if flip else 1.0
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(s, s * fy)
    lwu = lw / s
    # ---- geometry (units of hand length; wrist at 0, knuckles at kx; +y = little-finger side)
    kx = 0.42
    pw = 0.15 * palm_w
    palm_pts = [(-0.03, -pw * 0.80), (kx * 0.5, -pw * 1.0), (kx, -pw * 0.92), (kx + 0.035, -pw * 0.2),
                (kx + 0.03, pw * 0.45), (kx - 0.01, pw * 1.0), (kx * 0.5, pw * 1.02), (-0.03, pw * 0.82),
                (-0.06, 0.0)]
    fl = 0.56 * finger_len
    fw = 0.062 * finger_w
    lens = (0.95, 1.0, 0.86)
    nf = fingers
    fingers_geo = []
    for i in range(nf):
        u = (i - (nf - 1) / 2.0) / max(1.0, (nf - 1) / 2.0) if nf > 1 else 0.0   # -1 index .. +1 ring
        base = (kx - 0.03, u * pw * 0.66 - 0.005)
        L = fl * lens[min(i, 2)]
        c = curls[min(i, len(curls) - 1)]
        a0 = u * spread
        a1 = a0 + c * 1.35
        a2 = a1 + c * 1.5
        j1 = (base[0] + math.cos(a0) * L * 0.52, base[1] + math.sin(a0) * L * 0.52)
        j2 = (j1[0] + math.cos(a1) * L * 0.48, j1[1] + math.sin(a1) * L * 0.48)
        r0 = fw * (1.05 - 0.08 * abs(u))
        fingers_geo.append((base, j1, j2, r0, a1, a2))
    tb = (0.11, -pw * 0.78)
    ta0 = th_ang
    tj1 = (tb[0] + math.cos(ta0) * 0.21, tb[1] + math.sin(ta0) * 0.21)
    ta1 = ta0 + th_curl * 1.5 + 0.2
    tj2 = (tj1[0] + math.cos(ta1) * 0.15, tj1[1] + math.sin(ta1) * 0.15)
    tr = fw * 1.12

    def add_fingers(d=0.0):
        for (b0, j1, j2, r0, _a1, _a2) in fingers_geo:
            core.capsule(cr, b0[0], b0[1], r0 + d, j1[0], j1[1], r0 * 0.9 + d)
            core.capsule(cr, j1[0], j1[1], r0 * 0.9 + d, j2[0], j2[1], r0 * 0.78 + d)

    def add_thumb(d=0.0):
        if thumb:
            core.capsule(cr, tb[0], tb[1], tr + d, tj1[0], tj1[1], tr * 0.88 + d)
            core.capsule(cr, tj1[0], tj1[1], tr * 0.88 + d, tj2[0], tj2[1], tr * 0.72 + d)

    palm_off = offset_closed(palm_pts, lwu)
    if hold is not None and hold_behind:
        cr.save()
        cr.translate(kx + 0.08, 0.06)
        cr.scale(1.0 / s, 1.0 / s * fy)
        hold(cr, HandFrame(0.0, 0.0, angle, s, [], (0.0, 0.0), flip))
        cr.restore()
    cr.new_path()
    core.smooth_closed(cr, palm_pts)
    palm_only = Path(cr)
    if hold is None or hold_behind:
        # one union: dilated sub-paths filled as the outline, then the shaded union
        core.smooth_closed(cr, palm_off)
        add_thumb(lwu)
        add_fingers(lwu)
        core.src(cr, p.line)
        cr.fill()
        core.smooth_closed(cr, palm_pts)
        add_thumb()
        add_fingers()
        shade(cr, Path(cr), mat, light, lwu, rim=0.0, size=0.3, outline=False)
    else:
        core.smooth_closed(cr, palm_off)
        add_thumb(lwu)
        core.src(cr, p.line)
        cr.fill()
        core.smooth_closed(cr, palm_pts)
        add_thumb()
        shade(cr, Path(cr), mat, light, lwu, rim=0.0, size=0.3, outline=False)
        # the prop sits in the curl of the fingers: callback frame = grip point, +x along the
        # fingers, unscaled and un-mirrored (rotate by -frame.angle for gravity-aligned props)
        cr.save()
        cr.translate(kx + 0.08, 0.06)
        cr.scale(1.0 / s, 1.0 / s * fy)
        hold(cr, HandFrame(0.0, 0.0, angle, s, [], (0.0, 0.0), flip))
        cr.restore()
        # fingers over the prop: their outline must not cross the palm
        cr.save()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.rectangle(-50, -50, 100, 100)
        palm_only.add(cr)
        cr.clip()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
        add_fingers(lwu)
        core.src(cr, p.line)
        cr.fill()
        cr.restore()
        add_fingers()
        shade(cr, Path(cr), mat, light, lwu, rim=0.0, outline=False, size=0.25)
    # inked finger separations + knuckle ticks (one fill)
    cr.new_path()
    for i in range(nf - 1 if detail >= 1 else 0):
        (b0, j1a, _j2a, r0, a1a, _), (b1, j1b, _j2b, _r1, a1b, _) = fingers_geo[i], fingers_geo[i + 1]
        m0 = ((b0[0] + b1[0]) / 2 - 0.05, (b0[1] + b1[1]) / 2)
        m1 = ((j1a[0] + j1b[0]) / 2, (j1a[1] + j1b[1]) / 2)
        m2 = (m1[0] + (math.cos(a1a) + math.cos(a1b)) * 0.035, m1[1] + (math.sin(a1a) + math.sin(a1b)) * 0.035)
        core.tapered(cr, [m0, m1, m2], lwu * 0.4, lwu * 1.1,
                     profile=lambda q: lwu * (0.3 + 1.0 * math.sin(math.pi * min(1.0, q * 1.1))))
    if knuckles and not show_palm and detail >= 2:
        for (b0, j1, _j2, r0, a1, _a2) in fingers_geo:
            nx, ny = -math.sin(a1), math.cos(a1)
            cx_, cy_ = j1[0] - math.cos(a1) * r0 * 0.15, j1[1] - math.sin(a1) * r0 * 0.15
            core.tapered(cr, [(cx_ - nx * r0 * 0.55, cy_ - ny * r0 * 0.55), (cx_ + math.cos(a1) * r0 * 0.12, cy_ + math.sin(a1) * r0 * 0.12),
                              (cx_ + nx * r0 * 0.55, cy_ + ny * r0 * 0.55)], lwu * 0.2, lwu * 0.2,
                         profile=lambda q: lwu * (0.15 + 0.75 * math.sin(math.pi * q)))
    core.src(cr, p.line, 0.85)
    cr.fill()
    # palm pads (when the palm faces us)
    if show_palm and pad is not None:
        pp = palette(light, Mat.of(pad, sss=0.4))
        core.src(cr, pp.lit)
        core.ellipse(cr, kx * 0.5, 0.01, 0.15, pw * 0.72)
        for (b0, j1, j2, r0, _a1, _a2) in fingers_geo:
            core.circle(cr, j2[0], j2[1], r0 * 0.6)
        cr.fill()
    # claws: small curved cones continuing each fingertip, bending toward the palm (one path)
    if claw is not None:
        cp = palette(light, Mat.of(claw, sheen=0.5))
        cr.new_path()
        tips_c = [(j2, a2, r0 * 0.78) for (_b, _j1, j2, r0, _a1, a2) in fingers_geo]
        if thumb:
            tips_c.append((tj2, ta1, tr * 0.72))
        for (tp, ca, rr) in tips_c:
            dx_, dy_ = math.cos(ca), math.sin(ca)
            nx, ny = -dy_, dx_
            bx, by = tp[0] + dx_ * rr * 0.35, tp[1] + dy_ * rr * 0.35
            wv = rr * 0.85
            Lc = claw_len
            tipx, tipy = bx + dx_ * Lc + nx * Lc * 0.35, by + dy_ * Lc + ny * Lc * 0.35
            cr.move_to(bx - nx * wv, by - ny * wv)
            cr.curve_to(bx - nx * wv + dx_ * Lc * 0.6, by - ny * wv + dy_ * Lc * 0.6,
                        tipx - nx * Lc * 0.1, tipy - ny * Lc * 0.1, tipx, tipy)
            cr.curve_to(bx + nx * wv * 0.4 + dx_ * Lc * 0.5, by + ny * wv * 0.4 + dy_ * Lc * 0.5,
                        bx + nx * wv, by + ny * wv, bx + nx * wv, by + ny * wv)
            cr.close_path()
        cpath = Path(cr)
        flat(cr, cpath, cp.lit, lwu * 0.7, cp.line)
    if back_detail is not None:
        back_detail(cr, kx, pw)
    if stamp is not None:
        cr.save()
        cr.translate(kx * 0.5, 0.0)
        cr.scale(1.0 / s, fy / s)
        stamp(cr)
        cr.restore()
    # frame back to caller coords
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def tocaller(px, py):
        dx, dy = m.transform_point(px, py)
        return inv.transform_point(dx, dy)

    gx, gy = tocaller(kx + 0.08, 0.06)
    tips = [tocaller(g[2][0], g[2][1]) for g in fingers_geo]
    return HandFrame(gx, gy, angle, s, tips, tocaller(kx * 0.5, 0.0), flip)


# ========================================================================================
# Face kit
# ========================================================================================


@dataclass(frozen=True)
class Expr:
    """Facial expression parameters shared by every creature (each rig maps them to its face).

    brow_in / brow_out  inner / outer brow end height (-1 down .. +1 up)
    brow_y              raise the whole brow (-1 .. +1); brow_asym: + raises the near brow only
    lid                 upper lid closure 0 (wide) .. 1 (closed); lid_bot lower lid raise (squint)
    lid_tilt            + droopy/sad (outer corners lower), - angry (inner corners lower)
    smile               mouth corners -1 frown .. +1 smile; open = extra mouth opening 0..1
    mouth               '' (normal), 'o', 'laugh', 'sneer', 'sigh', 'teeth', 'flat'
    cheek               cheek raise 0..1 (happy squash); pupil = pupil scale
    """
    brow_in: float = 0.0
    brow_out: float = 0.0
    brow_y: float = 0.0
    brow_asym: float = 0.0
    lid: float = 0.22
    lid_bot: float = 0.06
    lid_tilt: float = 0.0
    smile: float = 0.0
    open: float = 0.0
    mouth: str = ""
    cheek: float = 0.0
    pupil: float = 1.0

    def blend(self, other, u):
        u = clamp(u)
        vals = {}
        for f in ("brow_in", "brow_out", "brow_y", "brow_asym", "lid", "lid_bot", "lid_tilt", "smile",
                  "open", "cheek", "pupil"):
            vals[f] = lerp(getattr(self, f), getattr(other, f), u)
        vals["mouth"] = other.mouth if u >= 0.5 else self.mouth
        return Expr(**vals)

    def with_(self, **kw):
        return replace(self, **kw)


MOODS = {
    "neutral":   Expr(),
    "tired":     Expr(brow_in=0.18, brow_out=-0.12, lid=0.46, lid_bot=0.08, lid_tilt=0.22, smile=-0.08),
    "sad":       Expr(brow_in=0.75, brow_out=-0.35, brow_y=0.05, lid=0.42, lid_bot=0.1, lid_tilt=0.55, smile=-0.45),
    "lonely":    Expr(brow_in=0.55, brow_out=-0.25, lid=0.5, lid_bot=0.1, lid_tilt=0.45, smile=-0.25),
    "raised":    Expr(brow_in=0.55, brow_out=0.5, brow_y=0.55, lid=0.06, lid_bot=0.0, smile=0.0, pupil=0.9),
    "surprised": Expr(brow_in=0.8, brow_out=0.7, brow_y=0.85, lid=0.0, lid_bot=0.0, open=0.35, mouth="o", pupil=0.8),
    "worried":   Expr(brow_in=0.9, brow_out=-0.1, brow_y=0.25, lid=0.2, lid_bot=0.12, lid_tilt=0.3, smile=-0.3),
    "happy":     Expr(brow_in=0.15, brow_out=0.25, brow_y=0.25, lid=0.2, lid_bot=0.38, lid_tilt=-0.05, smile=0.75, cheek=0.6),
    "warm":      Expr(brow_in=0.25, brow_out=0.1, brow_y=0.1, lid=0.32, lid_bot=0.25, lid_tilt=0.1, smile=0.45, cheek=0.35),
    "laugh":     Expr(brow_in=0.35, brow_out=0.3, brow_y=0.45, lid=0.72, lid_bot=0.6, lid_tilt=-0.1, smile=1.0, open=0.85, mouth="laugh", cheek=1.0),
    "skeptical": Expr(brow_in=-0.35, brow_out=0.15, brow_asym=0.7, lid=0.38, lid_bot=0.12, smile=-0.12),
    "angry":     Expr(brow_in=-0.85, brow_out=0.3, brow_y=-0.2, lid=0.3, lid_bot=0.15, lid_tilt=-0.6, smile=-0.5),
    "bored":     Expr(brow_in=-0.05, brow_out=-0.1, brow_y=-0.25, lid=0.62, lid_bot=0.05, smile=-0.1),
    "sneer":     Expr(brow_in=-0.6, brow_out=0.2, brow_asym=-0.3, lid=0.35, lid_bot=0.2, lid_tilt=-0.3, smile=-0.2, mouth="sneer"),
    "sigh":      Expr(brow_in=0.45, brow_out=-0.2, brow_y=-0.05, lid=0.62, lid_bot=0.1, lid_tilt=0.4, smile=-0.2, open=0.25, mouth="sigh"),
    "kind":      Expr(brow_in=0.3, brow_out=0.05, brow_y=0.15, lid=0.28, lid_bot=0.22, lid_tilt=0.15, smile=0.4, cheek=0.3),
}


def expr(mood="neutral", **overrides):
    """Expression from a mood name (MOODS) or an Expr, with field overrides."""
    e = mood if isinstance(mood, Expr) else MOODS[mood]
    return replace(e, **overrides) if overrides else e


def eye(cr, cx, cy, rx, ry, light, lw=LINE, *, angle=0.0, look=(0.0, 0.0), lid=0.22, lid_bot=0.06,
        tilt=0.0, outer=1.0, blink=0.0, squint_arc=0.0, iris="#D99A2B", iris_hi=None, pupil="#1d120c",
        pupil_size=0.5, pupil_aspect=1.0, sclera="#F3EEE4", skin="#3E6E73", iris_size=0.66,
        foreshort=1.0, crease=0.35, bags=0.0, lash=1.0, lash_flick=0.0, highlight=1.0, line=None,
        lid_shade=0.12, pupil_scale=1.0, hide_lid=False):
    """THE SHARED EYE. Every creature's eyes are built with this so the cast matches.

    (cx, cy) center of the eye opening, rx/ry its radii. outer = +1 if the OUTER corner is
    toward +x (screen right) else -1. lid 0..1 upper lid, lid_bot lower lid raise, tilt + sad
    droop / - angry. blink 0..1 overrides closure. squint_arc 0..1 turns a closed eye into the
    happy '^' arc. look (-1..1, -1..1) moves the iris. foreshort < 1 squeezes a far eye.
    skin = lid/skin color. Construction (STYLE.md): sclera with a lid shadow band, big iris with
    darker limbal ring and lighter lower half, pupil, 2 catchlights, a heavy upper lid line, a
    thin lower lid line, a lid crease. Draws on top of the head; returns nothing.
    """
    sk = palette(light, Mat.of(skin, sss=0.2))
    line_c = line if line is not None else sk.line
    # the upper lid follows the iris: looking down lowers it, looking up lifts it a little
    lid = clamp(lid + 0.28 * max(0.0, look[1]) - 0.10 * max(0.0, -look[1]))
    closed = clamp(max(lid, blink))
    cr.save()
    cr.translate(cx, cy)
    if angle:
        cr.rotate(angle)
    cr.scale(foreshort * outer, 1.0)     # local x: + toward the outer corner
    n = 9
    xs = [-rx + 2 * rx * i / (n - 1) for i in range(n)]

    def y_eye(x, top):
        k = max(0.0, 1.0 - (x / rx) ** 2)
        return (-1 if top else 1) * ry * math.sqrt(k)

    def y_top(x):
        u = x / rx
        base = -ry + 2.0 * ry * closed
        arch = -0.38 * ry * (1.0 - u * u) * (1.0 - closed * 0.85)
        sl = tilt * 0.42 * ry * u * (1.0 - closed * 0.4)          # + tilt lowers the outer side
        return max(y_eye(x, True), base + arch + sl)

    def y_bot(x):
        u = x / rx
        base = ry - 2.0 * ry * lid_bot
        arch = 0.32 * ry * (1.0 - u * u) * (1.0 - lid_bot)
        return min(y_eye(x, False), base + arch - ry * 0.0)

    top = [(x, y_top(x)) for x in xs]
    bot = [(x, y_bot(x)) for x in xs]
    visible = closed < 0.97 and any(b[1] - a[1] > 0.6 for a, b in zip(top, bot))
    # eye socket (opening) path
    cr.new_path()
    core.ellipse(cr, 0, 0, rx, ry)
    sock = Path(cr)
    if visible:
        cr.save()
        sock.add(cr)
        cr.clip()
        # visible eyeball region
        cr.move_to(*top[0])
        for pt in top[1:]:
            cr.line_to(*pt)
        for pt in reversed(bot):
            cr.line_to(*pt)
        cr.close_path()
        cr.clip()
        # sclera with the upper-lid shadow band
        sc = core.col(sclera)
        g = cairo.LinearGradient(0, -ry, 0, ry)
        sh = core.mix(sc, sk.shadow, 0.55)
        ytop_mid = y_top(0.0)
        f = clamp((ytop_mid + ry) / (2 * ry))
        g.add_color_stop_rgb(0.0, *sh[:3])
        g.add_color_stop_rgb(clamp(f + 0.02), *sh[:3])
        g.add_color_stop_rgb(clamp(f + 0.28), *core.mix(sc, sh, 0.15)[:3])
        g.add_color_stop_rgb(1.0, *sc[:3])
        cr.set_source(g)
        cr.paint()
        # iris
        ir = ry * iris_size
        ix = look[0] * rx * 0.42 * outer / max(0.4, foreshort)
        ix = clamp(ix, -rx + ir * 0.6, rx - ir * 0.6)
        iy = look[1] * ry * 0.38 + ry * 0.06
        ic = core.col(iris)
        ih = core.col(iris_hi) if iris_hi else core.tint(ic, 0.35)
        idark = core.shade(ic, 0.55)
        gi = cairo.RadialGradient(ix, iy + ir * 0.35, ir * 0.05, ix, iy, ir)
        gi.add_color_stop_rgb(0.0, *ih[:3])
        gi.add_color_stop_rgb(0.55, *ic[:3])
        gi.add_color_stop_rgb(0.86, *core.shade(ic, 0.25)[:3])
        gi.add_color_stop_rgb(1.0, *idark[:3])
        cr.set_source(gi)
        core.circle(cr, ix, iy, ir)
        cr.fill()
        # pupil
        pr = ir * pupil_size * pupil_scale
        core.src(cr, pupil)
        core.ellipse(cr, ix, iy, pr * pupil_aspect, pr)
        cr.fill()
        # lid shadow over the iris top
        g2 = cairo.LinearGradient(0, ytop_mid, 0, ytop_mid + ry * 0.55)
        dk = sk.deep
        g2.add_color_stop_rgba(0.0, dk[0], dk[1], dk[2], 0.55)
        g2.add_color_stop_rgba(1.0, dk[0], dk[1], dk[2], 0.0)
        cr.set_source(g2)
        cr.paint()
        # catchlights (toward the key light, up-outer) + a small opposite one
        if highlight > 0:
            kx_ = -0.35 * outer
            hx, hy = ix + ir * (0.32 + kx_ * 0.2), iy - ir * 0.42
            cr.set_source_rgba(1, 1, 1, 0.92 * highlight)
            core.ellipse(cr, hx, hy, ir * 0.30, ir * 0.24, -0.4)
            core.circle(cr, ix - ir * 0.35, iy + ir * 0.38, ir * 0.1)
            cr.fill()
        cr.restore()
        # lid skin: the heavy upper lid (darkening toward its edge) + the lower lid, one fill
        if not hide_lid:
            cr.save()
            sock.add(cr)
            cr.clip()
            core.polygon(cr, [(-rx * 1.2, -ry * 1.3), (rx * 1.2, -ry * 1.3)] + top[::-1])
            core.polygon(cr, [(-rx * 1.2, ry * 1.3), (rx * 1.2, ry * 1.3)] + bot[::-1])
            g3 = cairo.LinearGradient(0, -ry, 0, ry)
            yt = clamp((y_top(0) + ry) / (2 * ry))
            g3.add_color_stop_rgb(0.0, *sk.lit[:3])
            g3.add_color_stop_rgb(yt, *core.shade(sk.lit, lid_shade)[:3])
            g3.add_color_stop_rgb(min(1.0, yt + 0.02), *sk.lit[:3])
            cr.set_source(g3)
            cr.fill()
            cr.restore()
        # lid lines: heavy upper (lash line), thin lower
        # heavy upper lash line + thin lower lid line (one fill)
        cr.new_path()
        wt = lw * 1.7 * lash
        core.tapered(cr, top, wt, wt, profile=lambda u: wt * (0.35 + 0.65 * min(1.0, u / 0.5) if u < 0.5 else 1.0 - (0.4 - 0.4 * lash_flick) * (u - 0.5) / 0.5))
        wb = lw * 0.7
        core.tapered(cr, bot[2:], wb, wb, profile=lambda u: wb * (0.1 + 0.9 * min(1.0, u / 0.5) if u < 0.5 else 1.0 - 0.6 * (u - 0.5) / 0.5))
        if lash_flick > 0:
            ex, ey = top[-1]
            core.tapered(cr, [(ex - rx * 0.1, ey), (ex + rx * 0.22 * lash_flick, ey - ry * 0.25 * lash_flick)], lw * 1.4, lw * 0.15)
        core.src(cr, line_c)
        cr.fill()
    else:
        # closed eye: lid covers the socket; the lid line becomes a soft arc
        if not hide_lid:
            sock.add(cr)
            core.src(cr, sk.lit)
            cr.fill()
        k = squint_arc
        if k >= 0.5:      # happy '^' arc: bulges upward
            pts = [(x, -ry * 0.35 * (1.0 - (x / rx) ** 2) + ry * 0.15) for x in xs]
        else:             # relaxed closed: gentle downward curve
            pts = [(x, ry * 0.28 * (1.0 - (x / rx) ** 2) - ry * 0.02) for x in xs]
        detail_line(cr, pts, lw * 1.6, line_c, 1.0, taper=(0.3, 1.0, 0.5))
    # crease above the lid (heavy-lidded / tired)
    if crease > 0:
        cy2 = -ry * 1.12
        pts = [(x, cy2 - 0.18 * ry * (1 - (x / rx) ** 2) + tilt * 0.3 * ry * (x / rx)) for x in xs[1:-1]]
        detail_line(cr, pts, lw * 0.8, line_c, 0.55 * crease, taper=(0.1, 1.0, 0.2))
    if bags > 0:
        pts = [(x, ry * 1.18 + 0.12 * ry * (1 - (x / rx) ** 2)) for x in xs[2:-1]]
        detail_line(cr, pts, lw * 0.7, line_c, 0.45 * bags, taper=(0.1, 1.0, 0.1))
    cr.restore()


def brow_shape(x_in, x_out, y, e, side_sign=1.0, span=1.0):
    """Brow end points from an Expr: returns ((x_in, y_in), (x_out, y_out)) given the neutral
    inner/outer x and baseline y (y down). Rigs then draw ridges/fur/eyebrows along it.
    side_sign: +1 near/right brow, -1 far/left (for brow_asym)."""
    asym = e.brow_asym * (1.0 if side_sign > 0 else -0.35)
    lift = (e.brow_y + asym) * span
    yi = y - (e.brow_in * 0.55 + lift) * span
    yo = y - (e.brow_out * 0.45 + lift) * span
    return (x_in, yi), (x_out, yo)


def mouth(cr, x, y, w, light, lw=LINE, *, e=None, talk=0.0, skin="#C98C6A", lip=None,
          inside="#5A1E24", tongue="#C4566A", teeth="#F4EEE2", upper_teeth=True, line=None, angle=0.0):
    """A generic cartoon mouth for front/3-4 faces (gnome, lioness, troll, orc, faun...).
    (x, y) mouth center, w = width. Expression e (smile/open/mouth shape) + talk 0..1 from
    timeline.talk(). Draws a closed line or an open mouth shape with tongue and teeth."""
    e = e or Expr()
    sp = palette(light, Mat.of(skin))
    lc = line if line is not None else sp.line
    op = clamp(max(talk * 0.9, e.open))
    sm = e.smile
    hw = w * 0.5 * (1.0 + 0.15 * sm + (0.25 if e.mouth == "laugh" else 0.0) - (0.35 if e.mouth == "o" else 0.0))
    corner_y = -sm * w * 0.16
    cr.save()
    cr.translate(x, y)
    if angle:
        cr.rotate(angle)
    if op < 0.04:
        pts = [(-hw, corner_y), (-hw * 0.5, w * 0.03 + corner_y * 0.25), (0, w * 0.04),
               (hw * 0.5, w * 0.03 + corner_y * 0.25), (hw, corner_y)]
        if e.mouth == "sneer":
            pts[-1] = (hw, corner_y - w * 0.12)
            pts[-2] = (hw * 0.5, w * 0.0)
        detail_line(cr, pts, lw * 1.25, lc, 1.0, taper=(0.4, 1.0, 0.4))
        cr.restore()
        return
    h = w * (0.08 + 0.55 * op) * (1.15 if e.mouth == "laugh" else 1.0)
    top_mid = -h * 0.18 + (w * 0.02 if e.mouth != "sneer" else -w * 0.05)
    bot_mid = h * 0.82
    if e.mouth == "o":
        hw = max(hw, h * 0.45)
    cr.new_path()
    cr.move_to(-hw, corner_y)
    cr.curve_to(-hw * 0.6, top_mid, hw * 0.6, top_mid, hw, corner_y - (w * 0.1 if e.mouth == "sneer" else 0))
    cr.curve_to(hw * 0.75, bot_mid * (1.0 + 0.2 * max(0, sm)), -hw * 0.75, bot_mid * (1.0 + 0.2 * max(0, sm)), -hw, corner_y)
    cr.close_path()
    mp = Path(cr)
    flat(cr, mp, inside, lw, lc)
    cr.save()
    mp.add(cr)
    cr.clip()
    core.src(cr, tongue)
    core.ellipse(cr, 0, bot_mid * 0.95, hw * 0.62, h * 0.42)
    cr.fill()
    if upper_teeth and teeth:
        core.src(cr, teeth)
        cr.rectangle(-hw * 0.7, top_mid - h, hw * 1.4, h * 1.05 + h * 0.18 * 0.5)
        cr.fill()
    cr.restore()
    cr.restore()


# ========================================================================================
# Secondary motion (all pure functions of t -- deterministic)
# ========================================================================================


def breathing(t, rate=0.22, seed=0):
    """Idle breath -1..1 (exhale..inhale), ~13 breaths/min with a little irregularity."""
    ph = t * rate * TAU + seed * 1.7 + 0.35 * math.sin(t * rate * 1.3 + seed)
    return math.sin(ph)


def auto_blink(t, seed=0, interval=(2.4, 5.2), dur=0.18, double_chance=0.2):
    """Lid closure 0..1 from automatic blinks (fast close, slower open; occasional double)."""
    cell = 4.0
    k = math.floor(t / cell)
    best = 0.0
    for c in (k - 1, k):
        start = c * cell + core.hash01(c, seed + 3) * (cell - dur * 2.5)
        for j, off in enumerate((0.0, dur * 1.35)):
            if j == 1 and core.hash01(c, seed + 7) > double_chance:
                break
            u = (t - (start + off)) / dur
            if 0.0 <= u <= 1.0:
                v = smooth(u / 0.35) if u < 0.35 else 1.0 - smooth((u - 0.45) / 0.55) if u > 0.45 else 1.0
                best = max(best, v)
    return best


def sway(t, freq=0.3, seed=0):
    """Smooth organic idle drift -1..1 (layered noise)."""
    return core.fbm1(t * freq, 3, seed)


def spring(t, t0, freq=2.2, damping=0.45):
    """Step response 0 -> 1 starting at t0 with overshoot and settle (follow-through)."""
    if t <= t0:
        return 0.0
    dt = t - t0
    w = TAU * freq
    z = clamp(damping, 0.05, 0.99)
    wd = w * math.sqrt(1.0 - z * z)
    return 1.0 - math.exp(-z * w * dt) * (math.cos(wd * dt) + z / math.sqrt(1 - z * z) * math.sin(wd * dt))


def wobble(t, t0, freq=3.0, decay=4.0):
    """Damped oscillation after an impulse at t0: starts at 0, peaks ~1, rings down."""
    if t <= t0:
        return 0.0
    dt = t - t0
    return math.sin(TAU * freq * dt) * math.exp(-decay * dt) * 1.35


def lagged(f, t, delay):
    """Evaluate a pose driver at an earlier time -- the trailing part follows the lead."""
    return f(t - delay)


def follow(f, t, delay, gain=1.0):
    """How far a lagging part trails its driver: gain * (f(t - delay) - f(t))."""
    return gain * (f(t - delay) - f(t))


def chain(t, n, freq=0.45, delay=0.12, amp=1.0, seed=0, grow=1.6):
    """Angles (rad) for an n-link chain (tail, scarf end, hood tip, cloak hem): a traveling wave
    whose amplitude grows toward the tip (grow = tip/base amplitude)."""
    out = []
    for i in range(n):
        u = i / max(1, n - 1)
        a = amp * (1.0 + (grow - 1.0) * u) / n
        tt = t - i * delay
        out.append(a * (0.75 * math.sin(TAU * freq * tt + seed) + 0.25 * core.noise1(tt * freq * 2.0, seed + i)))
    return out


# ========================================================================================
# Walk cycle
# ========================================================================================


@dataclass
class WalkPose:
    hip_dy: float          # vertical bob (y down; + = lower)
    hip_sway: float        # side to side (-1..1)
    lean: float            # forward lean amount 0..1
    feet: list             # per foot: (forward offset, lift, toe angle, planted)
    arms: list             # per arm swing (-1..1; + = forward)
    head_bob: float        # lagged bob for the head
    phase: float


def walk_cycle(phase, stride=1.0, lift=1.0, bob=1.0, swing=1.0):
    """Generic biped walk. phase 0..1 = one full stride (two steps); compute it from distance:
    phase = distance_travelled / stride_length so planted feet never slide.

    feet[k] = (dz, lift, toe, planted): dz = forward offset of foot k from the hip in units of
    `stride` (+0.25 ahead .. -0.25 behind), lift >= 0 in units of `lift`, toe = foot pitch
    (+ toe up at heel strike, - heel up at push-off). foot 0 is planted at phase 0."""
    phase = phase % 1.0
    feet = []
    for k in range(2):
        u = (phase + 0.5 * k) % 1.0
        if u < 0.5:                       # stance: slides back linearly with the ground
            v = u / 0.5
            dz = stride * (0.25 - 0.5 * v)
            toe = 0.25 * (1.0 - smooth(v / 0.18)) - 0.35 * smooth((v - 0.75) / 0.25)
            feet.append((dz, 0.0, toe, True))
        else:                             # swing: arc forward
            v = (u - 0.5) / 0.5
            e = core.inout_sine(v)
            dz = stride * (-0.25 + 0.5 * e)
            lf = lift * math.sin(math.pi * min(1.0, v * 1.08)) ** 1.2
            toe = -0.35 * (1.0 - smooth(v / 0.3)) + 0.25 * smooth((v - 0.7) / 0.3)
            feet.append((dz, lf, toe, False))
    hip_dy = bob * math.cos(4 * math.pi * phase)
    head_bob = bob * math.cos(4 * math.pi * (phase - 0.06))
    sway_ = math.sin(TAU * phase)
    arms = [swing * math.sin(TAU * phase + math.pi * 0.0) * -1.0, swing * math.sin(TAU * phase)]
    return WalkPose(hip_dy, sway_, 1.0, feet, arms, head_bob, phase)


# ========================================================================================
# Ground contact
# ========================================================================================


def contact_shadow(cr, x, y, rx, ry=None, alpha=0.35, color=(0.02, 0.03, 0.06)):
    """Soft elliptical shadow where a character meets the ground (draw it BEFORE the character)."""
    ry = rx * 0.22 if ry is None else ry
    c = col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / max(rx, 1e-3))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, rx)
    g.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(0.45, c[0], c[1], c[2], alpha * 0.75)
    g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
    cr.set_source(g)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()


# ========================================================================================
# Character sheet convention
# ========================================================================================


@dataclass
class SheetItem:
    """One cell on a character sheet: render.py --sheet lays these out on pages.
    draw(cr) draws inside the box (0, 0, w, h) (origin top-left). label is printed below."""
    label: str
    w: int
    h: int
    draw: object
    group: str = ""


# Planned heights at scale 1.0, in px: ground -> the TOP of the silhouette in the default
# standing pose (horns and ears included; hats, hood tips and held props NOT included; the
# griffin sits on its haunches; the pixie is measured feet -> crown, wings excluded). ONE
# scale for the whole cast: characters sharing a depth plane get the same `scale`, so they
# come out at these relative sizes. The line-up page (character_sheet_lineup.png, made by
# render.py --sheet) draws every creature that has a lineup() hook against these marks and
# prints its measured top. The standard bench seat is BENCH_SEAT_H = 125.
CAST_HEIGHTS = {
    "troll": 660, "minotaur": 600, "dragon": 520, "orc": 480, "elf": 470, "lioness": 450,
    "satyr": 430, "faun": 410, "harpy": 400, "griffin": 380, "dwarf": 300, "goblin": 260,
    "kobold": 220, "bard": 156, "gnome": 160, "pixie": 90, "pigeon": 42,
}
BENCH_SEAT_H = 125.0


@dataclass
class LineupItem:
    """One creature on the cast line-up page: draw(cr, x, ground_y, scale) draws it standing
    (default pose, 3/4 facing right, neutral light) with its feet at (x, ground_y). width =
    its footprint in px at scale 1.0 (for spacing). A module's lineup() returns a list."""
    name: str
    draw: object
    width: float = 200.0


# ========================================================================================
# Shared helpers added for the supporting cast (gnome, elf, lioness, troll, pigeon, ...)
# ========================================================================================


def ellipsoid_pts(project, c, rx, ry, rz, n=10):
    """Silhouette points of an ellipsoid (three orthogonal rings) through `project`, any
    callable 3D -> 2D: a body projection (`proj.xy`) or a head-space one. Feed them to
    hull_paths / core.convex_hull for round volumes that turn continuously (cf. dragon._blob)."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        ca, sa = math.cos(a), math.sin(a)
        pts.append(project((c[0] + ca * rx, c[1] + sa * ry, c[2])))
        pts.append(project((c[0] + ca * rx, c[1], c[2] + sa * rz)))
        pts.append(project((c[0], c[1] + ca * ry, c[2] + sa * rz)))
    return pts


# Character-sheet backdrops per scene light (top, bottom), shared by every cast module's sheets.
SHEET_BG = {
    "neutral": ("#6f7a86", "#4b545e"), "washhouse": ("#1d3a3d", "#0e1f22"),
    "apothecary": ("#d9e6e0", "#a9bdb6"), "street_night": ("#1b2340", "#0b1022"),
    "tavern": ("#5a2440", "#2a1020"), "square": ("#4a5668", "#2c3442"),
    "dusk": ("#a98aa6", "#e0a98a"), "golden": ("#e6b070", "#a8704a"),
    "blue_hour": ("#3a4a78", "#1e2848"), "lantern_night": ("#141c34", "#070a16"),
}


def sheet_bg(cr, w, h, light="neutral", floor=None):
    """Fill a sheet cell (0, 0, w, h) with the backdrop for a LIGHTS preset name; `floor` (y)
    darkens a ground band below it."""
    top, bot = SHEET_BG.get(light, SHEET_BG["neutral"])
    core.vgrad(cr, 0, 0, w, h, [top, bot])
    if floor is not None:
        cr.set_source_rgba(0, 0, 0, 0.12)
        cr.rectangle(0, floor, w, h - floor)
        cr.fill()
