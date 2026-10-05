"""'Riso noir' look for DO NOT DISTURB: cream paper, indigo ink, a few spot colors, halftone shading,
film grain, and character animation on twos."""
import math
import numpy as np
import cairo
from toon.draw import hexc

PAPER = hexc("#efe6d2")
INK = hexc("#26244a")
LAV = hexc("#b3a6e0")
LAV_D = hexc("#8677bf")
HOOD = hexc("#6c7096")
PINK = hexc("#ff6b8f")
RED = hexc("#d91c3c")
COAT = hexc("#f7f3e8")
MUST = hexc("#f2b134")
MUST_D = hexc("#c98a1a")
TEAL = hexc("#1fa59a")
TEAL_L = hexc("#7ff0dc")
INDIGO = hexc("#3a3a7a")
NIGHT = hexc("#1d1c3d")
CORAL = hexc("#ff7b54")
MINT = hexc("#9ed8c4")
SLATE = hexc("#5d6b8a")
ALARM = hexc("#ff3b3b")
CREAM2 = hexc("#e4d8bd")

_PATTERNS = {}


def halftone(col=INK, alpha=0.35, step=11, r=2.4):
    """A repeating dot pattern to fill shadow shapes with."""
    key = (tuple(col), alpha, step, r)
    if key not in _PATTERNS:
        tile = cairo.ImageSurface(cairo.FORMAT_ARGB32, step, step)
        c = cairo.Context(tile)
        c.set_source_rgba(col[0], col[1], col[2], alpha)
        c.arc(step / 2, step / 2, r, 0, math.pi * 2)
        c.fill()
        c.arc(0, 0, r * 0.7, 0, math.pi * 2)
        c.arc(step, 0, r * 0.7, 0, math.pi * 2)
        c.arc(0, step, r * 0.7, 0, math.pi * 2)
        c.arc(step, step, r * 0.7, 0, math.pi * 2)
        c.fill()
        pat = cairo.SurfacePattern(tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        _PATTERNS[key] = (pat, tile)
    return _PATTERNS[key][0]


def shade_fill(c, alpha=0.35, col=INK):
    """Fill the current path with halftone dots (keeps nothing)."""
    c.set_source(halftone(col, alpha))
    c.fill()


def mix(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


# ------------------------------------------------------------------------------- grain
_GRAIN = []


def _make_grain(seed):
    rng = np.random.default_rng(seed)
    w, h = 540, 960
    n = rng.normal(0.0, 1.0, (h, w))
    # a little clumping
    n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1)) / 3
    v = np.clip(0.93 + n * 0.055, 0.78, 1.0)
    a = np.full((h, w), 255, np.uint8)
    g = (v * 255).astype(np.uint8)
    arr = np.dstack([g, g, g, a]).copy()
    surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, w, h)
    return surf, arr


def grain_post(c, t, shot, lt):
    if not _GRAIN:
        for s in range(3):
            _GRAIN.append(_make_grain(s))
    k = int(t * 15) % len(_GRAIN)
    surf = _GRAIN[k][0]
    c.save()
    c.scale(2, 2)
    c.set_source_surface(surf, 0, 0)
    c.get_source().set_filter(cairo.FILTER_BILINEAR)
    c.set_operator(cairo.OPERATOR_MULTIPLY)
    c.paint_with_alpha(0.55)
    c.restore()
    # warm paper wash + soft vignette
    c.save()
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, INK[0], INK[1], INK[2], 0.28)
    c.set_source(g)
    c.paint()
    c.restore()


THEME = dict(
    cap_box=(0.94, 0.90, 0.82, 0.96), cap_text=INK, cap_border=INK, shout_text=hexc("#d91c3c"),
    whisper_text=SLATE, think_box=(1, 1, 1, 0.95), think_text=INK,
    narr_box=(0.15, 0.14, 0.29, 0.9), narr_text=PAPER, cc_box=(0.15, 0.14, 0.29, 0.78), cc_text=PAPER,
    tag_font="Bungee", tag_text=(1, 1, 1), chip_box=(0.15, 0.14, 0.29, 0.7), chip_text=MUST, chip_font="Bungee",
    post=grain_post, twos=True, cc_high=True,
)
