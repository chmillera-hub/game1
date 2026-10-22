"""storybook.py -- THE PROLOGUE'S STORYBOOK KIT (SPEC 0.2, scene 0).

A great leather-bound book (brass corners, gilt title "The Stone and the Bread") on a carved oak
lectern, lit by candles, in a minstrel's nook with a stone hearth and a living fire. The book
creaks open, its pages flutter, its illuminated pages (parchment, deckled edges, gold-leaf
borders, a historiated drop-cap "O", the song's verse in ballad half-lines) come alive with little
watercolour paintings, and its pages turn: four spreads (verse 1, verse 2, the coda, and the
wash-house page the prologue pushes into).

    from film.lib import storybook as sb
    book = sb.Book()                                   # the prologue's pages (sb.PROLOGUE_SPREADS)
    L = sb.STORY_LIGHT                                 # candlelight for the bard, book and props
    lec = sb.draw_lectern(cr, x, floor_y, scale, L, view=V)   # static: cache it in an fx.Layer
    rig = sb.draw_book(cr, book, *lec.desk, scale, t, open=u, spread=k, turn=p, light=L, view=V)
    c = sb.draw_candle(cr, *lec.candles[0], scale, t, L)   # then fx.glow(...) at c.flame in the LightLayer
    hr = sb.draw_hearth(cr, hx, floor_y, s, L)         # static too; then every frame:
    fr = sb.draw_fire(cr, *hr.fire, s, t)              # and fx.glow(...) at fr.glow

Units: px at scale 1.0, y down. The book's anchor is the middle of its spine on the desk; a page is
Book.page_w x Book.page_h (default 150 x 200: the open book is ~2x the bard's height across).
The desk (and the book lying on it) is seen at `view` radians from face-on (default 0.42; ~0.6
for wide shots, ease toward ~0.2 for a push-in). Everything is deterministic in t.
"""

import functools
import math
import random
import subprocess
from dataclasses import dataclass, field

import cairocffi as cairo
import numpy as np

from . import core, fx
from .core import clamp, lerp, smooth
from .characters import base as B

TAU = math.tau

__all__ = ["Book", "Page", "Spread", "BookRig", "LecternRig", "CandleRig", "draw_book", "draw_page",
           "draw_lectern", "draw_candle", "candle_flicker", "page_turn_shadow", "STORY_LIGHT",
           "STORYBOOK_LIGHT", "PIGMENTS", "INK", "PROLOGUE_SPREADS", "ILLUSTRATIONS", "Illustration",
           "wash", "ink", "ink_outline", "gild", "hatch", "paper_grain", "folk", "storybook_dragon",
           "illus_castle", "illus_doors", "illus_dragon", "illus_market", "illus_washhouse", "illus_bread",
           "illus_stool", "illus_fleuron", "RUBRIC",
           "TEXT_FONT", "CAP_FONT", "SIGN_FONT", "HearthRig", "FireRig", "draw_hearth", "draw_fire",
           "fire_flicker"]

# ----------------------------------------------------------------------------------------
# light, fonts, palette
# ----------------------------------------------------------------------------------------

# candlelight for everything in the prologue nook (base.LIGHTS has no candle preset): warm key
# from the candles, deep plum ambient, a warm hearth rim from behind
STORY_LIGHT = B.Light(key=(1.16, 0.88, 0.60), ambient=(0.42, 0.32, 0.42), rim=(1.0, 0.70, 0.40),
                      rim_strength=0.7, direction=(0.65, -0.76), rim_direction=(-0.8, -0.6), name="candle")
# a soft, low-contrast light for characters painted INTO the book's illustrations (washes, not cels)
STORYBOOK_LIGHT = B.Light(key=(1.04, 0.99, 0.90), ambient=(0.82, 0.76, 0.72), rim=(1.0, 0.96, 0.86),
                          rim_strength=0.12, direction=(-0.5, -0.86), name="storybook")


@functools.lru_cache(maxsize=16)
def _font_ok(name):
    try:
        out = subprocess.run(["fc-list", ":family=" + name, "family"], capture_output=True, text=True, timeout=5)
        return bool(out.stdout.strip())
    except Exception:
        return False


# fonts (OFL, in film/assets/fonts; installed with fc-cache) with storybook-serif fallbacks
TEXT_FONT = "IM FELL English" if _font_ok("IM FELL English") else core.SERIF
SIGN_FONT = "IM FELL English SC" if _font_ok("IM FELL English SC") else core.SERIF
CAP_FONT = "Uncial Antiqua" if _font_ok("Uncial Antiqua") else core.SERIF

INK = "#3a2617"                     # sepia-black iron-gall ink
RUBRIC = "#a3311f"                  # red lead / vermilion for rubrics
# the illuminator's limited palette (manuscript pigments)
PIGMENTS = {
    "ultramarine": "#34539c", "azure": "#7397c8", "indigo": "#27305a", "night": "#1d2746",
    "vermilion": "#c2432c", "rose": "#d68a7c", "madder": "#93323a",
    "verdigris": "#4e8a6c", "sap": "#7c9d55", "olive": "#5e6b3a",
    "ochre": "#d2a24e", "sienna": "#a8623a", "umber": "#6e4a30", "bone": "#efe2c4",
    "slate": "#7b8698", "stone": "#a39a8c", "lead_white": "#f5ecd6",
    "gold": "#d8af55", "gold_hi": "#fbe7a4", "gold_dk": "#8a6524",
    "teal": "#3e8f8a", "wisp": "#8ff0d6", "rune": "#7fe8ff",
}
PARCHMENT = "#efe0bc"
PARCHMENT_DK = "#d9c495"


# ----------------------------------------------------------------------------------------
# the illuminator's toolkit: washes, ink, gold leaf, hatching, paper
# ----------------------------------------------------------------------------------------

def _poly(cr, pts, smooth_t=0.0):
    if smooth_t > 0 and len(pts) >= 3:
        core.smooth_closed(cr, pts, smooth_t)
    else:
        core.polygon(cr, pts)


def wobble(pts, amp=0.7, seed=0, freq=0.11):
    """Hand-drawn irregularity for a polygon (deterministic)."""
    return [(x + amp * core.noise1(x * freq + i * 0.37, seed), y + amp * core.noise1(y * freq + i * 0.53, seed + 7))
            for i, (x, y) in enumerate(pts)]


def wash(cr, pts, color, alpha=0.85, edge=0.4, smooth_t=0.0, w=1.0, path=None):
    """A watercolour wash: a translucent fill with pigment pooled darker along its edge.
    pts: a closed polygon (or pass a base.Path as `path`). w scales the pooled edge. Returns the Path."""
    c = core.col(color)
    if path is None:
        cr.new_path()
        _poly(cr, pts, smooth_t)
        path = B.Path(cr)
    path.add(cr)
    core.src(cr, c, alpha)
    cr.fill()
    if edge > 0:
        cr.save()
        path.add(cr)
        cr.clip()
        x0, y0, x1, y1 = cr.clip_extents()
        big = min(x1 - x0, y1 - y0)
        if big > 24.0:
            # soft blooms where the wash dried unevenly (deterministic from the shape's place)
            sd = int(abs(x0 * 7.3 + y0 * 3.1)) % 997
            rng = random.Random(sd)
            for _ in range(2 if big < 60 else 3):
                bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
                _bloom(cr, bx, by, big * rng.uniform(0.25, 0.45), "#ffffff" if rng.random() < 0.6 else core.shade(c, 0.4),
                       0.12)
        path.add(cr)
        cr.set_line_width(5.0 * w)
        core.src(cr, core.shade(c, 0.28), alpha * edge * 0.35)
        cr.stroke()
        path.add(cr)
        cr.set_line_width(1.8 * w)
        core.src(cr, core.shade(c, 0.36), alpha * edge)
        cr.stroke()
        cr.restore()
    return path


def ink(cr, pts, w=1.1, color=INK, alpha=0.9, taper=(0.35, 1.0, 0.45)):
    """A hand-inked line through pts (pressure taper)."""
    if len(pts) >= 2:
        B.detail_line(cr, pts, w, color, alpha, taper=taper)


def ink_outline(cr, path, w=0.9, color=INK, alpha=0.85):
    """Ink round a shape (a base.Path)."""
    cr.save()
    path.add(cr)
    cr.set_line_width(w)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    core.src(cr, color, alpha)
    cr.stroke()
    cr.restore()


def gild(cr, pts=None, path=None, shimmer=0.0, smooth_t=0.0, outline=0.7, light_dir=(-0.5, -0.8)):
    """Gold leaf: a burnished gradient, a bright edge toward the light, a dark ink edge.
    shimmer 0..1 (e.g. the candle flicker) brightens the burnish."""
    if path is None:
        cr.new_path()
        _poly(cr, pts, smooth_t)
        path = B.Path(cr)
    x0, y0, x1, y1 = path.extents(cr)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = max(x1 - x0, y1 - y0) * 0.6 + 1e-3
    lx, ly = light_dir
    g = cairo.LinearGradient(cx + lx * r, cy + ly * r, cx - lx * r, cy - ly * r)
    hi = core.mix(PIGMENTS["gold"], PIGMENTS["gold_hi"], 0.55 + 0.35 * shimmer)
    g.add_color_stop_rgb(0.0, *core.col(hi)[:3])
    g.add_color_stop_rgb(0.45, *core.col(PIGMENTS["gold"])[:3])
    g.add_color_stop_rgb(0.75, *core.col(core.mix(PIGMENTS["gold"], PIGMENTS["gold_dk"], 0.5))[:3])
    g.add_color_stop_rgb(1.0, *core.col(core.mix(PIGMENTS["gold"], PIGMENTS["gold_hi"], 0.3 * shimmer))[:3])
    path.add(cr)
    cr.set_source(g)
    cr.fill()
    if outline > 0:
        ink_outline(cr, path, outline, PIGMENTS["gold_dk"], 0.9)
    return path


def hatch(cr, path, angle=0.8, gap=3.0, w=0.45, color=INK, alpha=0.35):
    """Pen hatching inside a shape (shadow sides of walls, hills)."""
    x0, y0, x1, y1 = path.extents(cr)
    cr.save()
    path.add(cr)
    cr.clip()
    ca, sa = math.cos(angle), math.sin(angle)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 2
    k = -R
    cr.new_path()
    while k <= R:
        px, py = cx - sa * k, cy + ca * k
        cr.move_to(px - ca * R, py - sa * R)
        cr.line_to(px + ca * R, py + sa * R)
        k += gap
    cr.set_line_width(w)
    core.src(cr, color, alpha)
    cr.stroke()
    cr.restore()


@functools.lru_cache(maxsize=4)
def _grain_tile(size=256, seed=11):
    """Paper fibre/grain tile: dark specks + light flecks (premultiplied ARGB)."""
    rng = np.random.default_rng(seed)
    n = core.noise_array(size, size, scale=48.0, octaves=3, seed=seed)
    n = n / max(1e-6, float(np.abs(n).max()))
    fib = core.noise_array(size, size, scale=5.0, octaves=2, seed=seed + 1)
    fib = fib / max(1e-6, float(np.abs(fib).max()))
    fine = rng.normal(0.0, 1.0, (size, size)).astype(np.float32)
    v = 0.3 * n + 0.45 * fib + 0.25 * fine / 3.0
    dark = np.clip(-v, 0, 1) * 0.42
    light = np.clip(v, 0, 1) * 0.28
    a = np.clip(dark + light, 0, 1)
    arr = np.zeros((size, size, 4), np.uint8)
    lum = np.where(v > 0, 1.0, 0.0)
    arr[..., 3] = (a * 255).astype(np.uint8)
    for ch, (dc, lc) in enumerate(((0.16, 0.98), (0.11, 0.95), (0.07, 0.88))):   # B, G, R premultiplied
        arr[..., ch] = (a * np.where(lum > 0, lc, dc) * 255).astype(np.uint8)
    data = bytearray(arr.tobytes())
    s = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, size, size, size * 4)
    return s, data


def paper_grain(cr, x, y, w, h, alpha=0.35, scale=0.5, seed=11):
    """Overlay paper grain on the rectangle (cheap: one repeated tile)."""
    tile, _keep = _grain_tile(256, seed)
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    pat = cairo.SurfacePattern(tile)
    pat.set_extend(cairo.EXTEND_REPEAT)
    pat.set_filter(cairo.FILTER_BILINEAR)
    m = cairo.Matrix()
    m.scale(1.0 / scale, 1.0 / scale)
    m.translate(-x, -y)
    pat.set_matrix(m)
    cr.set_source(pat)
    cr.paint_with_alpha(alpha)
    cr.restore()


def _bloom(cr, x, y, r, color, alpha):
    """A soft watercolour bloom (a blot where the wash pooled)."""
    c = core.col(color)
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0.0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(0.7, c[0], c[1], c[2], alpha * 0.5)
    g.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.0)
    cr.set_source(g)
    cr.arc(x, y, r, 0, TAU)
    cr.fill()


def _sky(cr, w, h, stops, seed=0, blooms=6, top=0.0, bottom=None):
    bottom = h if bottom is None else bottom
    cr.rectangle(-w, top - 2, 3 * w, bottom - top + 4)
    cr.set_source(core.linear(0, top, 0, bottom, stops))
    cr.fill()
    rng = random.Random(seed)
    for _ in range(blooms):
        x, y = rng.uniform(0, w), rng.uniform(top, bottom)
        _bloom(cr, x, y, rng.uniform(18, 46), "#ffffff" if rng.random() < 0.5 else "#1a1830", rng.uniform(0.05, 0.11))


def _glowdot(cr, x, y, r, color, alpha=0.6):
    """A painted glow (lantern, window): a soft additive halo inside the page."""
    fx.glow(cr, x, y, r, color, alpha)


# ----------------------------------------------------------------------------------------
# tiny storybook folk (painted creature figures -- never human)
# ----------------------------------------------------------------------------------------

_FOLK = {
    "goblin": dict(skin="#8fa66a", cloak="#7a5233", hood=False, ears=1.0, snout=0.2, beard=False, h=1.0, tail=False),
    "elf":    dict(skin="#efd2b0", cloak="#4e8a6c", hood=True, ears=0.7, snout=0.0, beard=False, h=1.15, tail=False),
    "dwarf":  dict(skin="#e2b48e", cloak="#a8623a", hood=False, ears=0.25, snout=0.1, beard=True, h=0.85, tail=False),
    "kobold": dict(skin="#c97b4a", cloak="#34539c", hood=True, ears=0.0, snout=1.0, beard=False, h=0.9, tail=True),
    "mouse":  dict(skin="#b9a99a", cloak="#93323a", hood=False, ears=0.0, snout=0.6, beard=False, h=0.8, tail=True,
                   round_ears=True),
}


def folk(cr, x, y, s=1.0, kind="goblin", facing=1, walk=0.0, phase=0.0, reach=0.0, look_back=0.0, t=0.0,
         hurry=0.0, seed=0):
    """A little painted creature (goblin, elf, dwarf, kobold, mouse-folk) in a cloak, feet at
    (x, y), ~34*s units tall. walk 0..1 with `phase` (legs + bob), reach 0..1 (arm out to a
    latch/bolt), hurry 0..1 (leans forward, head down), look_back 0..1 (glances over a shoulder)."""
    F = _FOLK.get(kind, _FOLK["goblin"])
    hs = F["h"]
    cr.save()
    cr.translate(x, y)
    cr.scale(s * facing, s)
    ph = phase * TAU
    bob = -abs(math.sin(ph)) * 1.4 * walk
    lean = 0.18 * hurry + 0.05 * walk
    # legs (two little boots stepping)
    for k in (-1, 1):
        sw = math.sin(ph + (0 if k < 0 else math.pi)) * 4.0 * walk
        lift = max(0.0, math.cos(ph + (0 if k < 0 else math.pi))) * 2.0 * walk
        lx = k * 2.6 + sw
        cr.new_path()
        core.capsule(cr, k * 2.0, -9.0 * hs, 1.8, lx, -1.6 - lift, 1.5)
        core.src(cr, "#4a3326", 0.95)
        cr.fill()
        cr.new_path()
        core.ellipse(cr, lx + 1.4, -1.0 - lift, 2.8, 1.5)
        core.src(cr, "#3a281c", 0.95)
        cr.fill()
    cr.translate(0, bob)
    cr.rotate(lean)
    # tail
    if F.get("tail"):
        tw = math.sin(t * 2.0 + seed) * 2.0
        ink(cr, [(-4.0, -9.0 * hs), (-10.0, -6.0 * hs + tw), (-14.0, -10.0 * hs + tw)], 1.6, F["skin"], 1.0, (1.0, 0.8, 0.3))
    # cloak (a bell)
    ch = 22.0 * hs
    cloak = [(-7.5, -6.0), (-6.0, -ch * 0.7), (-3.5, -ch), (3.5, -ch), (6.0, -ch * 0.7), (8.0, -5.0), (3.0, -4.0), (-2.0, -4.5)]
    p = wash(cr, cloak, F["cloak"], 0.92, 0.45, smooth_t=0.7, w=0.6)
    ink_outline(cr, p, 0.6, INK, 0.75)
    # arm (reaching to a latch, or swinging)
    ax = 3.0 + 8.0 * reach
    ay = -ch * 0.62 - 3.0 * reach
    sw = math.sin(ph) * 2.5 * walk
    ink(cr, [(1.5, -ch * 0.7), (ax + sw, ay + 2.0), (ax + 2.0 + sw, ay)], 2.2, F["cloak"], 1.0, (1.0, 1.0, 0.8))
    cr.new_path()
    core.circle(cr, ax + 2.4 + sw, ay - 0.2, 1.4)
    core.src(cr, F["skin"])
    cr.fill()
    # head
    hy = -ch - 5.0
    cr.save()
    cr.translate(0.5, hy)
    cr.rotate(0.25 * hurry)
    if look_back > 0:
        cr.scale(1.0 - 1.6 * min(0.6, look_back), 1.0)     # head turns: squash toward profile-back
    if F.get("round_ears"):
        for ex in (-3.2, 3.0):
            cr.new_path()
            core.circle(cr, ex, -4.6, 2.6)
            core.src(cr, F["skin"])
            cr.fill()
            cr.new_path()
            core.circle(cr, ex, -4.6, 1.4)
            core.src(cr, PIGMENTS["rose"], 0.8)
            cr.fill()
    if F["ears"] > 0:
        L = 7.0 * F["ears"]
        for sgn in (-1, 1):
            ear = [(sgn * 3.0, -1.5), (sgn * (3.5 + L), -3.0 - L * 0.25), (sgn * 3.0, 0.8)]
            pe = wash(cr, ear, F["skin"], 0.95, 0.3)
            ink_outline(cr, pe, 0.45, INK, 0.6)
    face = [(-4.2, -3.5), (0.0, -5.6), (4.2, -3.5), (4.6, 1.0), (1.5 + 2.5 * F["snout"], 2.6), (-3.0, 3.4), (-4.6, 1.0)]
    pf = wash(cr, face, F["skin"], 0.96, 0.35, smooth_t=0.8, w=0.5)
    ink_outline(cr, pf, 0.5, INK, 0.7)
    if F["snout"] > 0.5:
        sn = [(2.5, -0.8), (6.0 + 2.0 * F["snout"], 0.6), (2.8, 2.6)]
        ps = wash(cr, sn, F["skin"], 0.96, 0.3, smooth_t=0.6)
        ink_outline(cr, ps, 0.45, INK, 0.65)
    if F["beard"]:
        bd = [(-3.5, 0.6), (3.8, 0.6), (2.0, 7.5), (-1.5, 8.5)]
        pb = wash(cr, bd, "#d9d2c6", 0.95, 0.3, smooth_t=0.7)
        ink_outline(cr, pb, 0.45, INK, 0.6)
    cr.new_path()
    core.circle(cr, 1.6, -1.6, 0.75)
    core.src(cr, INK, 0.9)
    cr.fill()
    if F["hood"]:
        hood = [(-5.2, 1.5), (-5.0, -4.5), (-1.0, -8.5), (4.0, -7.5), (5.0, -4.0), (2.8, -4.6), (-2.0, -3.0), (-3.2, 2.0)]
        ph_ = wash(cr, hood, F["cloak"], 0.95, 0.45, smooth_t=0.7, w=0.6)
        ink_outline(cr, ph_, 0.55, INK, 0.75)
    cr.restore()
    cr.restore()


def storybook_dragon(cr, x, y, s, t, wave=0.0, mood="warm", facing=0, turn=0.25, wings=-0.3, alpha=0.96,
                     tint=0.16):
    """THE DRAGON, on-model (the real rig: slate-teal scales, charcoal-navy coat, mustard scarf),
    painted into an illustration: soft storybook light, then washed toward the parchment so he
    sits in the paint. wave 0..1 phase of a friendly wave (None: arms at rest)."""
    from .characters import dragon as D
    near = D.Arm("wave", phase=wave) if wave is not None else D.Arm()
    pose = D.DragonPose(facing=facing, turn=turn, near=near, mood=mood, wings=wings, seed=3)
    cr.push_group()
    rig = D.draw_dragon(cr, x, y, s, pose, STORYBOOK_LIGHT, t)
    pat = cr.pop_group()
    cr.save()
    cr.set_source(pat)
    cr.paint_with_alpha(alpha)
    core.src(cr, PARCHMENT, tint)
    cr.mask(pat)
    cr.restore()
    return rig


# ----------------------------------------------------------------------------------------
# illustrations: cached static layers + per-frame life
# ----------------------------------------------------------------------------------------

class Illustration:
    """A painted illustration in a design box (DW x DH units), fitted to any (w, h) by "cover"
    scaling (centred). Subclasses draw `back(cr)` (static, cached per resolution bucket) and
    `anim(cr, t)` (every frame, on top), both in design units. Call it: illus(cr, w, h, t)."""
    DW, DH = 200.0, 260.0
    grain = 0.35

    def __init__(self, seed=0):
        self.seed = seed
        self._cache = {}

    def back(self, cr):
        pass

    def anim(self, cr, t):
        pass

    def _fit(self, w, h):
        s = max(w / self.DW, h / self.DH)
        return s, (w - self.DW * s) / 2.0, (h - self.DH * s) / 2.0

    def _static(self, cr, w, h):
        dev = B.device_scale(cr)
        bucket = 2.0 ** (math.ceil(math.log2(max(0.25, dev)) * 2.0) / 2.0)
        key = (round(w, 2), round(h, 2), bucket)
        surf = self._cache.get(key)
        if surf is None:
            if len(self._cache) > 6:
                self._cache.clear()
            sw, sh = max(1, int(math.ceil(w * bucket))), max(1, int(math.ceil(h * bucket)))
            surf = core.new_surface(sw, sh)
            c2 = core.new_context(surf)
            c2.scale(bucket, bucket)
            s, ox, oy = self._fit(w, h)
            c2.rectangle(0, 0, w, h)
            c2.clip()
            c2.save()
            c2.translate(ox, oy)
            c2.scale(s, s)
            self.back(c2)
            c2.restore()
            surf.flush()
            self._cache[key] = surf
        return surf, bucket

    def __call__(self, cr, w, h, t=0.0):
        surf, bucket = self._static(cr, w, h)
        cr.save()
        cr.rectangle(0, 0, w, h)
        cr.clip()
        cr.save()
        cr.scale(1.0 / bucket, 1.0 / bucket)
        cr.set_source_surface(surf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()
        s, ox, oy = self._fit(w, h)
        cr.save()
        cr.translate(ox, oy)
        cr.scale(s, s)
        self.anim(cr, t)
        cr.restore()
        if self.grain > 0:
            paper_grain(cr, 0, 0, w, h, self.grain, scale=0.6, seed=self.seed + 11)
        cr.restore()


def _stars(cr, pts, t, seed, color=None, twinkle=True):
    col = color or PIGMENTS["gold_hi"]
    for i, (x, y, r) in enumerate(pts):
        a = 0.55 + 0.45 * math.sin(t * (1.3 + 0.37 * (i % 5)) + i * 2.1 + seed) if twinkle else 1.0
        fx.sparkle(cr, x, y, r * (0.8 + 0.3 * a), col, 0.55 * a + 0.2)


def _pennant(cr, x, y, L, t, phase, color, h=6.0):
    """A pennant waving from a pole tip at (x, y)."""
    pts_top, pts_bot = [], []
    for k in range(7):
        u = k / 6.0
        wv = math.sin(t * 3.1 + phase - u * 4.0) * 2.4 * u
        pts_top.append((x + u * L, y + wv - h * 0.5 * (1.0 - u)))
        pts_bot.append((x + u * L, y + wv + h * 0.5 * (1.0 - u) + 0.6 * u))
    poly = pts_top + pts_bot[::-1]
    p = wash(cr, poly, color, 0.95, 0.4, smooth_t=0.5, w=0.5)
    ink_outline(cr, p, 0.45, INK, 0.7)


def _house(cr, x, y, w, h, roof_h, wall, roof, seed, door=True, windows=2, beams=True, shutters="#4e8a6c",
           lit=None):
    """A half-timbered storybook house front, ground at y. Returns door rect (x, y, w, h)."""
    rng = random.Random(seed)
    body = wobble([(x, y), (x, y - h), (x + w, y - h), (x + w, y)], 0.5, seed)
    pw = wash(cr, body, wall, 0.9, 0.35, w=0.8)
    # jettied upper floor line + timber frame
    if beams:
        bl = []
        mid = y - h * 0.48
        bl.append([(x - 1.5, mid), (x + w + 1.5, mid)])
        for k in range(4):
            bx = x + w * k / 3.0
            bl.append([(bx, y - h), (bx, mid)])
        bl.append([(x, y - h), (x + w / 3.0, mid)])
        bl.append([(x + w, y - h), (x + 2 * w / 3.0, mid)])
        for b in bl:
            ink(cr, b, 2.3, PIGMENTS["umber"], 0.95, (0.8, 1.0, 0.8))
    # roof
    rf = wobble([(x - 4, y - h + 1), (x + w * 0.5, y - h - roof_h), (x + w + 4, y - h + 1)], 0.6, seed + 3)
    pr = wash(cr, rf, roof, 0.92, 0.5, w=0.8)
    hatch(cr, pr, 0.5, 2.6, 0.35, INK, 0.25)
    ink_outline(cr, pr, 0.7, INK, 0.8)
    # windows with shutters
    for k in range(windows):
        wx = x + w * (k + 0.5) / windows - 5.0
        wy = y - h * 0.82
        win = [(wx, wy), (wx + 10, wy), (wx + 10, wy + 11), (wx, wy + 11)]
        lit_k = lit[k] if lit else 0.0
        wash(cr, win, core.mix(PIGMENTS["night"], PIGMENTS["ochre"], lit_k), 0.92, 0.3)
        ink(cr, [(wx + 5, wy), (wx + 5, wy + 11)], 0.6, INK, 0.7)
        ink(cr, [(wx, wy + 5.5), (wx + 10, wy + 5.5)], 0.6, INK, 0.7)
        for sx in (wx - 5.0, wx + 10.0):
            sh = [(sx, wy - 0.5), (sx + 5, wy - 0.5), (sx + 5, wy + 11.5), (sx, wy + 11.5)]
            ps = wash(cr, sh, shutters, 0.9, 0.3)
            ink_outline(cr, ps, 0.5, INK, 0.7)
    ink_outline(cr, pw, 0.8, INK, 0.8)
    if door:
        dw, dh = min(16.0, w * 0.32), min(26.0, h * 0.42)
        dx = x + w * 0.5 - dw * 0.5 + rng.uniform(-4, 4)
        return (dx, y - dh, dw, dh)
    return None


def _door(cr, rect, open_=0.0, bolt=0.0, wood="#7a4d2c"):
    """An arched oak door in its frame: open_ 0 shut .. 1 wide (the dark interior shows), bolt 0..1
    slides the iron bolt home."""
    dx, dy, dw, dh = rect
    arch = [(dx, dy + dh)] + [(dx + dw * 0.5 - math.cos(math.pi * k / 8) * dw * 0.5, dy + dw * 0.5 - math.sin(math.pi * k / 8) * dw * 0.5)
                              for k in range(9)] + [(dx + dw, dy + dh)]
    wash(cr, arch, "#20180f", 0.95, 0.2)
    k = clamp(1.0 - open_)
    if k > 0.02:
        cr.save()
        cr.new_path()
        core.polygon(cr, arch)
        cr.clip()
        leaf = [(dx, dy - 2), (dx + dw * k, dy - 2 + 3.0 * (1 - k)), (dx + dw * k, dy + dh), (dx, dy + dh)]
        pl = wash(cr, leaf, wood, 0.97, 0.45, w=0.6)
        if k > 0.3:
            for j in (1, 2):
                ink(cr, [(dx + dw * k * j / 3.0, dy + 1), (dx + dw * k * j / 3.0, dy + dh)], 0.45, INK, 0.55)
            for hy in (dy + dh * 0.3, dy + dh * 0.75):
                ink(cr, [(dx + 0.5, hy), (dx + dw * k * 0.55, hy)], 1.1, "#2a2420", 0.9)
            # the bolt
            bx = dx + dw * k - 2.0 - 5.0 * (1.0 - bolt)
            ink(cr, [(bx - 3.5, dy + dh * 0.52), (bx + 3.0, dy + dh * 0.52)], 1.4, "#3a3633", 1.0)
            cr.new_path()
            core.circle(cr, dx + dw * k * 0.82, dy + dh * 0.58, 0.9)
            core.src(cr, PIGMENTS["gold_dk"])
            cr.fill()
        cr.restore()
        ink_outline(cr, pl, 0.4, INK, 0.5)
    cr.new_path()
    core.polygon(cr, arch)
    p = B.Path(cr)
    ink_outline(cr, p, 0.9, INK, 0.85)


def _lantern(cr, x, y, t, phase=0.0, scale=1.0, warm=True):
    """A hanging lantern on an iron bracket fixed at (x, y), swaying; a painted glow."""
    ang = 0.16 * math.sin(t * 1.7 + phase) + 0.05 * math.sin(t * 3.1 + phase * 2)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    ink(cr, [(-9.0, 0.0), (0.0, 0.0)], 1.2, "#2e2a28", 1.0)
    ink(cr, [(-9.0, 3.0), (-3.0, 0.0)], 0.8, "#2e2a28", 0.9)
    cr.rotate(ang)
    ink(cr, [(0.0, 0.0), (0.0, 5.0)], 0.6, "#2e2a28", 1.0)
    glow_c = PIGMENTS["ochre"] if warm else PIGMENTS["wisp"]
    _glowdot(cr, 0.0, 11.0, 16.0, glow_c, 0.42)
    body = [(-3.5, 6.0), (3.5, 6.0), (4.2, 9.0), (3.2, 15.0), (-3.2, 15.0), (-4.2, 9.0)]
    wash(cr, body, core.mix(glow_c, "#fff6d0", 0.4), 0.95, 0.3)
    cr.new_path()
    core.polygon(cr, body)
    pb = B.Path(cr)
    ink_outline(cr, pb, 0.6, "#2e2a28", 0.95)
    ink(cr, [(0.0, 6.0), (0.0, 15.0)], 0.5, "#2e2a28", 0.8)
    cap = [(-4.0, 6.2), (0.0, 3.0), (4.0, 6.2)]
    wash(cr, cap, "#3a3633", 0.95, 0.2)
    cr.restore()


def _cobbles(cr, x0, x1, y0, y1, seed, color=PIGMENTS["stone"]):
    rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    wash(cr, rect, color, 0.75, 0.25)
    rng = random.Random(seed)
    arcs = []
    y = y0 + 3.0
    row = 0
    while y < y1:
        x = x0 - (row % 2) * 5.0
        while x < x1:
            w = rng.uniform(7.0, 11.0)
            arcs.append([(x + 1.0, y + 2.0), (x + w * 0.5, y - 0.6), (x + w - 1.0, y + 2.0)])
            x += w
        y += 4.5 + row * 0.25
        row += 1
    cr.save()
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.clip()
    B.detail_lines(cr, arcs, 0.55, INK, 0.35)
    cr.restore()


class _Castle(Illustration):
    """A castle on a hill at dusk, a little town at its foot (verse 1)."""

    def back(self, cr):
        P = PIGMENTS
        _sky(cr, self.DW, self.DH, [(0.0, "#27305e"), (0.42, "#5c4f86"), (0.68, "#b9788a"), (0.86, "#e3a07a"),
                                    (1.0, "#efc98d")], seed=self.seed + 1, blooms=7)
        # distant hills
        far = wobble([(-10, 200), (20, 178), (60, 186), (95, 170), (140, 182), (180, 168), (215, 180), (215, 270), (-10, 270)], 1.0, 3)
        wash(cr, far, "#7d7fa4", 0.75, 0.3, smooth_t=0.6)
        # the moon (gold leaf)
        cr.new_path()
        cr.arc(152, 48, 13, 0, TAU)
        cr.arc_negative(158, 44, 11, TAU, 0)
        gild(cr, path=B.Path(cr), outline=0.6)
        # the castle hill
        hill = wobble([(-10, 270), (-10, 222), (30, 210), (70, 178), (98, 150), (130, 146), (160, 168), (190, 196),
                       (215, 206), (215, 270)], 1.2, 5)
        ph = wash(cr, hill, P["sap"], 0.92, 0.45, smooth_t=0.6)
        hatch(cr, ph, -0.6, 3.4, 0.4, P["olive"], 0.3)
        # the winding road up to the gate
        road = [(30, 268), (60, 238), (40, 215), (82, 196), (100, 176), (113, 162)]
        ink(cr, road, 5.0, P["ochre"], 0.85, (1.0, 0.7, 0.35))
        ink(cr, road, 0.6, P["umber"], 0.5, (1.0, 0.7, 0.35))
        # castle
        st, sd = P["stone"], core.shade(P["slate"], 0.15)
        walls = [(86, 152), (86, 128), (140, 128), (140, 152)]
        pw_ = wash(cr, walls, st, 0.95, 0.4)
        keep = [(100, 130), (100, 92), (126, 92), (126, 130)]
        pk = wash(cr, keep, core.tint(st, 0.12), 0.95, 0.4)
        hatch(cr, pk, 1.2, 2.2, 0.35, INK, 0.25)
        crenels = []
        for k in range(6):
            cx = 100 + k * 5.0
            crenels.append([(cx, 92), (cx, 88.5), (cx + 2.8, 88.5), (cx + 2.8, 92)])
        for k in range(10):
            cx = 87 + k * 5.4
            crenels.append([(cx, 128), (cx, 124.5), (cx + 3.0, 124.5), (cx + 3.0, 128)])
        for c in crenels:
            wash(cr, c, st, 0.95, 0.3)
        towers = []
        for tx, ty, tw in ((80, 104, 14), (134, 100, 14), (108, 70, 9)):
            tp = [(tx, 152 if tx != 108 else 92), (tx, ty), (tx + tw, ty), (tx + tw, 152 if tx != 108 else 92)]
            p1 = wash(cr, tp, st, 0.95, 0.4)
            # shadow side
            wash(cr, [(tx + tw * 0.62, ty), (tx + tw, ty), (tx + tw, 152 if tx != 108 else 92), (tx + tw * 0.62, 152 if tx != 108 else 92)],
                 sd, 0.45, 0.0)
            roof = [(tx - 2.5, ty + 0.5), (tx + tw * 0.5, ty - tw * 1.55), (tx + tw + 2.5, ty + 0.5)]
            pr = wash(cr, roof, P["vermilion"], 0.95, 0.5)
            hatch(cr, pr, 0.9, 2.0, 0.3, INK, 0.3)
            ink_outline(cr, pr, 0.7, INK, 0.85)
            ink_outline(cr, p1, 0.7, INK, 0.85)
            towers.append((tx + tw * 0.5, ty - tw * 1.55))
            # windows (dark slits)
            for wy in (ty + 10, ty + 24):
                wash(cr, [(tx + tw * 0.4, wy), (tx + tw * 0.6, wy), (tx + tw * 0.6, wy + 6), (tx + tw * 0.4, wy + 6)], P["night"], 0.95, 0.0)
        self._tips = towers
        ink_outline(cr, pw_, 0.7, INK, 0.85)
        ink_outline(cr, pk, 0.7, INK, 0.85)
        for c in crenels:
            cr.new_path()
            core.polygon(cr, c)
            ink_outline(cr, B.Path(cr), 0.45, INK, 0.7)
        gate = [(108, 152), (108, 141)] + [(113 - math.cos(math.pi * k / 6) * 5, 141 - math.sin(math.pi * k / 6) * 5) for k in range(7)] + [(118, 141), (118, 152)]
        wash(cr, gate, "#2a1f17", 0.95, 0.2)
        # the town at the foot of the hill: shut doors, a few windows
        rng = random.Random(self.seed + 9)
        houses = []
        for k in range(7):
            hx = 4 + k * 17 + rng.uniform(-3, 3)
            hy = 236 + rng.uniform(-6, 8) - k * 2.2
            hw, hh = rng.uniform(12, 16), rng.uniform(10, 15)
            houses.append((hx, hy, hw, hh))
        for (hx, hy, hw, hh) in sorted(houses, key=lambda h: h[1]):
            body = [(hx, hy), (hx, hy - hh), (hx + hw, hy - hh), (hx + hw, hy)]
            pb = wash(cr, body, core.mix(P["bone"], P["ochre"], rng.uniform(0, 0.4)), 0.95, 0.35)
            roof = [(hx - 2, hy - hh + 0.5), (hx + hw * 0.5, hy - hh - 8), (hx + hw + 2, hy - hh + 0.5)]
            pr = wash(cr, roof, rng.choice((P["vermilion"], P["sienna"], P["madder"])), 0.95, 0.45)
            ink_outline(cr, pr, 0.55, INK, 0.8)
            ink_outline(cr, pb, 0.55, INK, 0.8)
            wash(cr, [(hx + hw * 0.4, hy), (hx + hw * 0.4, hy - 5.5), (hx + hw * 0.62, hy - 5.5), (hx + hw * 0.62, hy)],
                 "#3a2618", 0.95, 0.0)
        self._houses = houses
        # trees
        for (tx, ty, r) in ((150, 200, 9), (164, 206, 7), (24, 214, 8), (176, 214, 10), (60, 188, 6)):
            cr.new_path()
            core.blob(cr, tx, ty, r, 0.18, 8, seed=int(tx))
            p = wash(cr, None, P["olive"], 0.92, 0.5, path=B.Path(cr))
            ink_outline(cr, p, 0.55, INK, 0.7)
        self._stars = [(x, y, r) for x, y, r in ((20, 22, 2.6), (44, 40, 2.0), (70, 16, 2.4), (96, 34, 1.8), (122, 20, 2.2),
                                                 (186, 24, 2.4), (178, 70, 1.8), (30, 70, 1.6), (12, 110, 1.4))]

    def anim(self, cr, t):
        if not hasattr(self, "_tips"):
            return
        _stars(cr, self._stars, t, self.seed)
        for i, (x, y) in enumerate(self._tips):
            ink(cr, [(x, y + 1), (x, y - 7)], 0.7, INK, 0.9)
            _pennant(cr, x, y - 7, 11.0 if i < 2 else 9.0, t, i * 1.7, PIGMENTS["vermilion"] if i != 2 else PIGMENTS["gold"])
        # windows in the town going dark one by one (shut doors, living alone)
        for k, (hx, hy, hw, hh) in enumerate(self._houses):
            on = 0.5 + 0.5 * math.sin(t * 0.6 + k * 1.9)
            on = smooth((on - 0.35) / 0.3)
            if on > 0.02:
                wx, wy = hx + hw * 0.18, hy - hh * 0.75
                _glowdot(cr, wx + 1.6, wy + 1.6, 5.0, PIGMENTS["ochre"], 0.35 * on)
                wash(cr, [(wx, wy), (wx + 3.2, wy), (wx + 3.2, wy + 3.4), (wx, wy + 3.4)], PIGMENTS["gold_hi"], 0.9 * on, 0.0)
        # birds drifting home
        for k in range(3):
            u = ((t * 0.035 + k * 0.31) % 1.0)
            bx, by = -10 + u * 220, 60 + 18 * math.sin(u * 5 + k) + k * 9
            fl = 1.6 * math.sin(t * 7.0 + k)
            ink(cr, [(bx - 3.2, by - 1.0 - fl), (bx, by), (bx + 3.2, by - 1.0 - fl)], 0.75, INK, 0.75, (0.3, 1.0, 0.3))


class _Doors(Illustration):
    """A street of shut doors and swaying lanterns; little folk hurry in and bolt their latches."""
    DW, DH = 220.0, 150.0

    def back(self, cr):
        P = PIGMENTS
        _sky(cr, self.DW, self.DH, [(0.0, "#232a52"), (0.6, "#3c4170"), (1.0, "#6d5f80")], seed=self.seed + 2, blooms=4,
             bottom=96)
        _stars(cr, [(18, 12, 1.8), (60, 8, 1.5), (110, 15, 2.0), (168, 9, 1.6), (205, 20, 1.8)], 0.0, 1, twinkle=False)
        _cobbles(cr, -5, self.DW + 5, 126, self.DH + 5, self.seed + 4)
        walls = (P["bone"], core.mix(P["bone"], P["ochre"], 0.45), core.mix(P["bone"], P["rose"], 0.4))
        roofs = (P["sienna"], P["madder"], P["umber"])
        self._doors = []
        x = 2.0
        for k in range(3):
            w = 66.0 + (k % 2) * 6
            d = _house(cr, x, 128, w, 80 - (k % 2) * 8, 22, walls[k], roofs[k], self.seed + k * 7,
                       shutters=(P["verdigris"], P["ultramarine"], P["olive"])[k])
            self._doors.append(d)
            x += w + 5.0
        self._brackets = [(70.5, 70.0), (144.5, 76.0)]

    def anim(self, cr, t):
        if not hasattr(self, "_doors"):
            return
        cyc = 7.5
        for k, d in enumerate(self._doors):
            u = ((t + k * 2.1) % cyc) / cyc                         # each door's little drama, looping
            open_ = 1.0 - smooth((u - 0.30) / 0.12) if u > 0.18 else smooth(u / 0.12)
            bolt = smooth((u - 0.46) / 0.08)
            _door(cr, d, open_=open_ * 0.85, bolt=bolt)
            # a folk hurrying in, then gone (the latch is bolted behind them)
            kind = ("goblin", "elf", "dwarf")[k]
            dx, dy, dw, dh = d
            if u < 0.34:
                walk_in = smooth(u / 0.28)
                fx_ = lerp(dx - 26.0 if k % 2 == 0 else dx + dw + 26.0, dx + dw * 0.5, walk_in)
                vis = 1.0 - smooth((u - 0.28) / 0.06)
                if vis > 0.05:
                    cr.push_group()
                    folk(cr, fx_, dy + dh, 0.9, kind, facing=1 if k % 2 == 0 else -1, walk=1.0 - 0.6 * walk_in,
                         phase=u * 9.0, hurry=0.8, look_back=0.3 if k == 1 else 0.0, t=t, seed=k)
                    cr.pop_group_to_source()
                    cr.paint_with_alpha(vis)
        for i, (bx, by) in enumerate(self._brackets):
            _lantern(cr, bx, by, t, phase=i * 2.3)


class _DragonStreet(Illustration):
    """The dragon in his coat and scarf, waving on a cobbled street while the neighbours hurry by."""
    DW, DH = 200.0, 240.0

    def back(self, cr):
        P = PIGMENTS
        _sky(cr, self.DW, self.DH, [(0.0, "#3a4672"), (0.55, "#7a6a8e"), (1.0, "#c99a86")], seed=self.seed + 3,
             blooms=5, bottom=150)
        _house(cr, -8, 186, 78, 118, 30, core.mix(P["bone"], P["ochre"], 0.3), P["madder"], self.seed + 1,
               shutters=P["verdigris"])
        _house(cr, 132, 186, 80, 110, 28, core.mix(P["bone"], P["rose"], 0.3), P["sienna"], self.seed + 2,
               shutters=P["ultramarine"])
        # a lantern post
        ink(cr, [(112, 186), (112, 116)], 2.6, "#2e2a28", 1.0, (1.0, 1.0, 0.8))
        ink(cr, [(112, 118), (120, 116)], 1.2, "#2e2a28", 1.0)
        _cobbles(cr, -5, self.DW + 5, 184, self.DH + 5, self.seed + 5)

    def anim(self, cr, t):
        _lantern(cr, 121, 116, t, phase=0.7, scale=0.9)
        # neighbours hurrying by (looping across the street, heads turned away)
        for k, (kind, sp, y, d) in enumerate((("goblin", 0.11, 214, 1), ("kobold", 0.085, 222, -1), ("mouse", 0.1, 230, 1))):
            u = (t * sp + k * 0.37) % 1.0
            x = -24 + u * 248 if d > 0 else 224 - u * 248
            folk(cr, x, y, 1.05, kind, facing=d, walk=1.0, phase=u * 22.0, hurry=0.9, t=t, seed=k)
        # the dragon, waving hopefully
        wave = (t * 0.55) % 1.0
        storybook_dragon(cr, 96, 214, 0.25, t, wave=wave, mood="warm", facing=0, turn=0.15, wings=-0.2)


class _Market(Illustration):
    """Merchants' stalls selling stones, potions and candles (the city's remedies)."""
    DW, DH = 220.0, 220.0

    def back(self, cr):
        P = PIGMENTS
        _sky(cr, self.DW, self.DH, [(0.0, "#3f4a78"), (0.7, "#8b7a96"), (1.0, "#d8a986")], seed=self.seed + 6,
             blooms=5, bottom=120)
        # buildings behind
        for k, (x, w, h, c) in enumerate(((-6, 70, 90, P["bone"]), (66, 80, 104, core.mix(P["bone"], P["ochre"], 0.35)),
                                          (148, 80, 92, core.mix(P["bone"], P["rose"], 0.3)))):
            _house(cr, x, 132, w, h, 22, core.mix(c, "#8c8aa0", 0.25), core.mix(P["madder"], "#6c6a80", 0.3),
                   self.seed + 20 + k, door=False, windows=2, shutters=core.mix(P["verdigris"], "#6c6a80", 0.3))
        _cobbles(cr, -5, self.DW + 5, 130, self.DH + 5, self.seed + 7)
        self._stalls = []
        for k, (x, awn, sign) in enumerate(((6, P["vermilion"], "STONES"), (78, P["ultramarine"], "POTIONS"),
                                            (150, P["verdigris"], "CANDLES"))):
            w = 64.0
            # posts
            for px in (x + 2, x + w - 2):
                ink(cr, [(px, 196), (px, 132)], 2.2, P["umber"], 1.0, (1.0, 1.0, 1.0))
            # counter
            ctr = [(x - 2, 172), (x + w + 2, 172), (x + w, 196), (x, 196)]
            pc = wash(cr, ctr, "#8a5a36", 0.95, 0.45)
            hatch(cr, pc, 1.57, 3.0, 0.4, INK, 0.3)
            ink_outline(cr, pc, 0.7, INK, 0.85)
            self._stalls.append((x, w, awn, sign))

    def anim(self, cr, t):
        if not hasattr(self, "_stalls"):
            return
        P = PIGMENTS
        for k, (x, w, awn, sign) in enumerate(self._stalls):
            # merchant behind the counter
            kind = ("goblin", "dwarf", "kobold")[k]
            reach = 0.5 + 0.5 * math.sin(t * 1.6 + k * 2.0)
            folk(cr, x + w * 0.5, 172, 1.05, kind, facing=1 if k != 1 else -1, reach=reach * 0.8, t=t, seed=k + 5)
            # the counter again in front of the merchant's legs (redrawn: cheap)
            ctr = [(x - 2, 172), (x + w + 2, 172), (x + w, 196), (x, 196)]
            pc = wash(cr, ctr, "#8a5a36", 0.97, 0.45)
            ink_outline(cr, pc, 0.7, INK, 0.85)
            # wares
            if sign == "STONES":
                for j in range(5):
                    sx, sy = x + 8 + j * 11.5, 168
                    st = [(sx - 4.5, sy + 1), (sx - 3.5, sy - 4), (sx + 1.5, sy - 5.5), (sx + 5, sy - 2), (sx + 4, sy + 1)]
                    ps = wash(cr, st, P["slate"], 0.95, 0.4, smooth_t=0.6)
                    ink_outline(cr, ps, 0.45, INK, 0.75)
                    g = 0.5 + 0.5 * math.sin(t * 2.2 + j * 1.3)
                    _glowdot(cr, sx, sy - 2, 5.5, P["rune"], 0.28 * g)
                    ink(cr, [(sx - 1.5, sy - 3.0), (sx + 0.5, sy - 1.0), (sx + 1.8, sy - 3.4)], 0.6, P["rune"], 0.6 + 0.4 * g)
            elif sign == "POTIONS":
                cols = (P["azure"], P["madder"], P["verdigris"], P["ultramarine"], P["rose"])
                for j in range(5):
                    bx_, by_ = x + 9 + j * 11.0, 171
                    bh = 9.0 + (j % 2) * 3.0
                    bottle = [(bx_ - 3.4, by_), (bx_ - 3.6, by_ - bh * 0.6), (bx_ - 1.2, by_ - bh * 0.8), (bx_ - 1.0, by_ - bh),
                              (bx_ + 1.0, by_ - bh), (bx_ + 1.2, by_ - bh * 0.8), (bx_ + 3.6, by_ - bh * 0.6), (bx_ + 3.4, by_)]
                    pb = wash(cr, bottle, cols[j], 0.9, 0.4, smooth_t=0.4)
                    ink_outline(cr, pb, 0.45, INK, 0.75)
                    fx.sparkle(cr, bx_ - 1.4, by_ - bh * 0.45, 1.6, "#ffffff", 0.5)
                    for b in range(2):                          # bubbles rising
                        u = (t * 0.6 + j * 0.3 + b * 0.5) % 1.0
                        cr.new_path()
                        core.circle(cr, bx_ + 0.6 * math.sin(u * 9 + j), by_ - bh - 1 - u * 8, 0.7 * (1 - u) + 0.2)
                        core.src(cr, cols[j], 0.6 * (1 - u))
                        cr.fill()
            else:
                for j in range(4):
                    cx_, cy_ = x + 11 + j * 14.0, 171
                    jar = [(cx_ - 4, cy_), (cx_ - 4, cy_ - 7), (cx_ + 4, cy_ - 7), (cx_ + 4, cy_)]
                    pj = wash(cr, jar, "#cfd8d2", 0.75, 0.3)
                    ink_outline(cr, pj, 0.4, INK, 0.7)
                    cd = [(cx_ - 2.4, cy_ - 1), (cx_ - 2.4, cy_ - 10 - j % 2 * 2), (cx_ + 2.4, cy_ - 10 - j % 2 * 2), (cx_ + 2.4, cy_ - 1)]
                    wash(cr, cd, P["bone"], 0.95, 0.3)
                    ink(cr, [(cx_, cy_ - 10 - j % 2 * 2), (cx_, cy_ - 12 - j % 2 * 2)], 0.6, INK, 0.9)
            # awning with a fluttering scalloped edge
            top, bot = 128.0, 142.0
            stripes = 6
            for s in range(stripes):
                x0, x1 = x - 4 + (w + 8) * s / stripes, x - 4 + (w + 8) * (s + 1) / stripes
                fl = 1.2 * math.sin(t * 3.0 + s * 0.9 + k)
                poly = [(x0 + 3.0, top), (x1 + 3.0, top), (x1, bot + fl), ((x0 + x1) / 2, bot + 4.0 + fl), (x0, bot + fl)]
                wash(cr, poly, awn if s % 2 == 0 else P["lead_white"], 0.95, 0.35)
            outline = [(x - 1, top), (x + w + 7, top), (x + w + 4, bot), (x - 4, bot)]
            cr.new_path()
            core.polygon(cr, outline)
            ink_outline(cr, B.Path(cr), 0.6, INK, 0.8)
            # the swinging sign
            sa = 0.12 * math.sin(t * 1.4 + k * 1.1)
            cr.save()
            cr.translate(x + w * 0.5, 120)
            cr.rotate(sa)
            ink(cr, [(-9, -6), (-9, 0)], 0.5, INK, 0.9)
            ink(cr, [(9, -6), (9, 0)], 0.5, INK, 0.9)
            board = [(-15, 0), (15, 0), (15, 9), (-15, 9)]
            pb = wash(cr, board, "#c79a62", 0.97, 0.45)
            ink_outline(cr, pb, 0.6, INK, 0.9)
            core.text(cr, sign, 0, 7.0, 6.6, SIGN_FONT, INK, align="center", alpha_=0.92)
            cr.restore()


class _WashHouse(Illustration):
    """The wash-house at night: cold green light in its arched windows, drums tumbling inside."""
    DW, DH = 200.0, 260.0

    def back(self, cr):
        _sky(cr, self.DW, self.DH, [(0.0, "#141a33"), (0.6, "#1f2b4c"), (1.0, "#2f4a5c")], seed=self.seed + 8, blooms=6)
        cr.new_path()
        cr.arc(62, 64, 12, 0, TAU)
        cr.arc_negative(68, 60, 10.5, TAU, 0)
        gild(cr, path=B.Path(cr), outline=0.6)
        # the building: stone walls, a slate roof, a chimney, a buttress
        body = wobble([(20, 220), (20, 120), (180, 120), (180, 220)], 0.6, 2)
        pb = wash(cr, body, "#7d8a8e", 0.95, 0.45)
        hatch(cr, pb, 0.0, 6.0, 0.4, INK, 0.18)
        rng = random.Random(self.seed + 3)
        blocks = []
        for row in range(10):
            y = 124 + row * 10
            x = 20 + (row % 2) * 9
            while x < 178:
                w = rng.uniform(14, 22)
                blocks.append([(x, y), (min(x + w, 180), y)])
                x += w
        B.detail_lines(cr, blocks, 0.4, INK, 0.3)
        roof = wobble([(10, 122), (100, 70), (190, 122)], 0.6, 4)
        pr = wash(cr, roof, "#4b5468", 0.95, 0.5)
        hatch(cr, pr, 0.55, 2.6, 0.35, INK, 0.3)
        ink_outline(cr, pr, 0.8, INK, 0.85)
        ch = [(138, 92), (138, 66), (152, 66), (152, 100)]
        pc = wash(cr, ch, "#6b6f7a", 0.95, 0.4)
        ink_outline(cr, pc, 0.7, INK, 0.85)
        ink_outline(cr, pb, 0.9, INK, 0.9)
        self._wins = []
        for k, wx in enumerate((40, 88, 136)):
            arch = [(wx, 204)] + [(wx + 12 - math.cos(math.pi * j / 8) * 12, 150 - math.sin(math.pi * j / 8) * 12) for j in range(9)] + [(wx + 24, 204)]
            self._wins.append((wx, arch))
        # door + step
        door = [(92, 220), (92, 206)] + [(100 - math.cos(math.pi * j / 6) * 8, 206 - math.sin(math.pi * j / 6) * 8) for j in range(7)] + [(108, 206), (108, 220)]
        pd = wash(cr, door, "#3a2a1c", 0.95, 0.3)
        ink_outline(cr, pd, 0.8, INK, 0.9)
        _cobbles(cr, -5, self.DW + 5, 220, self.DH + 5, self.seed + 9, color="#5d6872")
        self._stars = [(16, 18, 2.0), (70, 12, 1.6), (120, 30, 2.2), (176, 16, 1.8), (184, 60, 1.5), (98, 46, 1.4)]

    def anim(self, cr, t):
        if not hasattr(self, "_wins"):
            return
        P = PIGMENTS
        _stars(cr, self._stars, t, self.seed, color="#dfe8ff")
        for k, (wx, arch) in enumerate(self._wins):
            pulse = 0.75 + 0.25 * math.sin(t * 2.4 + k * 1.3)
            pw = wash(cr, arch, core.mix("#143b3a", P["teal"], 0.6 * pulse), 0.97, 0.3)
            cr.save()
            pw.add(cr)
            cr.clip()
            _glowdot(cr, wx + 12, 178, 26, P["wisp"], 0.28 * pulse)
            # a round porthole drum, clothes tumbling
            cx, cy, r = wx + 12, 186, 8.0
            cr.new_path()
            core.circle(cr, cx, cy, r + 1.6)
            core.src(cr, "#b49248", 0.95)
            cr.fill()
            cr.new_path()
            core.circle(cr, cx, cy, r)
            core.src(cr, "#0f2a2b", 0.95)
            cr.fill()
            ang = t * 2.2 + k
            for j, c in enumerate((P["vermilion"], P["azure"], P["bone"])):
                a = ang + j * 2.1
                cr.new_path()
                core.ellipse(cr, cx + math.cos(a) * 3.4, cy + math.sin(a) * 3.4, 3.2, 2.2, a)
                core.src(cr, c, 0.85)
                cr.fill()
            cr.restore()
            ink(cr, [(wx + 12, 138), (wx + 12, 204)], 0.6, INK, 0.7)
            ink_outline(cr, pw, 0.9, INK, 0.9)
        # the sign, swinging a little
        sa = 0.08 * math.sin(t * 1.1)
        cr.save()
        cr.translate(100, 128)
        cr.rotate(sa)
        board = [(-34, 0), (34, 0), (34, 13), (-34, 13)]
        ink(cr, [(-26, -6), (-26, 0)], 0.6, INK, 0.9)
        ink(cr, [(26, -6), (26, 0)], 0.6, INK, 0.9)
        pbd = wash(cr, board, "#7a5a3a", 0.97, 0.45)
        ink_outline(cr, pbd, 0.7, INK, 0.9)
        core.text(cr, "WASH-HOUSE", 0, 9.8, 8.6, SIGN_FONT, PIGMENTS["gold_hi"], align="center", alpha_=0.95)
        cr.restore()
        # cold steam from the chimney
        for j in range(4):
            u = (t * 0.22 + j * 0.25) % 1.0
            cr.new_path()
            core.circle(cr, 145 + 6.0 * math.sin(u * 4 + j) + u * 10, 62 - u * 46, 4.0 + u * 6.0)
            core.src(cr, "#c8d6dc", 0.28 * (1 - u))
            cr.fill()
        _lantern(cr, 82, 198, t, phase=0.3, scale=0.8, warm=False)


class _Bread(Illustration):
    """The moral in one picture (the coda's right page): a cold grey stone and a round loaf broken
    in two on a wooden board, a gold-leaf glory behind the bread; warm steam and motes rise."""
    DW, DH = 200.0, 260.0
    grain = 0.3

    def back(self, cr):
        P = PIGMENTS
        _sky(cr, self.DW, self.DH, [(0.0, "#2a2f52"), (0.55, "#4a3a5c"), (1.0, "#7a4a4a")], seed=self.seed + 4,
             blooms=5)
        # the glory: gold-leaf rays and a burnished disc behind the loaf
        cx, cy = 128.0, 128.0
        rays = []
        for k in range(24):
            a = TAU * k / 24
            r0, r1 = 34.0, 74.0 if k % 2 == 0 else 58.0
            da = 0.07
            rays.append([(cx + math.cos(a - da) * r0, cy + math.sin(a - da) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                         (cx + math.cos(a + da) * r0, cy + math.sin(a + da) * r0)])
        for ry in rays:
            gild(cr, ry, outline=0.35)
        cr.new_path()
        core.circle(cr, cx, cy, 38.0)
        gild(cr, path=B.Path(cr), outline=0.6)
        # the table top (a wooden board) in perspective
        board = wobble([(8, 178), (192, 178), (200, 214), (0, 214)], 0.5, 3)
        pb = wash(cr, board, P["umber"], 0.95, 0.5)
        hatch(cr, pb, 0.08, 4.5, 0.4, INK, 0.25)
        ink_outline(cr, pb, 0.9, INK, 0.85)
        front = wobble([(0, 214), (200, 214), (200, 236), (0, 236)], 0.5, 5)
        pf = wash(cr, front, core.shade(P["umber"], 0.25), 0.95, 0.4)
        ink_outline(cr, pf, 0.8, INK, 0.85)
        wash(cr, [(-4, 237), (204, 237), (204, 264), (-4, 264)], "#2a1c22", 0.9, 0.0)     # the dark under the table
        # the stone: cold, grey, hatched, sitting heavy
        st = wobble([(26, 190), (30, 160), (48, 146), (72, 148), (88, 166), (86, 188), (60, 196), (36, 196)], 0.6, 7)
        ps = wash(cr, st, P["slate"], 0.97, 0.55, smooth_t=0.7)
        hatch(cr, ps, 0.9, 2.4, 0.4, INK, 0.32)
        ink_outline(cr, ps, 0.9, INK, 0.9)
        ink(cr, [(40, 162), (50, 156), (62, 155)], 0.8, P["lead_white"], 0.6)
        # the loaf broken in two, its crumb showing
        for hx, flip in ((112.0, -1.0), (146.0, 1.0)):
            half = [(hx - 22 * flip, 194), (hx - 26 * flip, 172), (hx - 16 * flip, 150), (hx + 2 * flip, 144),
                    (hx + 8 * flip, 150), (hx + 9 * flip, 194)]
            ph = wash(cr, wobble(half, 0.5, int(hx)), P["sienna"], 0.97, 0.5, smooth_t=0.7)
            crumb = [(hx + 8 * flip, 191), (hx + 6 * flip, 152), (hx + 1 * flip, 148), (hx + 2 * flip, 192)]
            wash(cr, crumb, P["bone"], 0.97, 0.3, smooth_t=0.5)
            ink_outline(cr, ph, 0.9, INK, 0.9)
            for j in range(3):
                ink(cr, [(hx - (18 - j * 6) * flip, 164 - j * 3), (hx - (12 - j * 6) * flip, 158 - j * 3)], 1.4,
                    P["ochre"], 0.9)
        for (x_, y_) in ((126, 197), (131, 199), (122, 200)):          # crumbs
            cr.new_path()
            core.circle(cr, x_, y_, 1.3)
            core.src(cr, P["bone"])
            cr.fill()

    def anim(self, cr, t):
        for j in range(3):                                  # warm steam curling off the broken loaf
            u = (t * 0.3 + j / 3.0) % 1.0
            sx = 126.0 + 6.0 * math.sin(u * 6.0 + j)
            ink(cr, [(sx, 140 - u * 40), (sx + 4.0 * math.sin(u * 9.0 + j), 130 - u * 40), (sx - 3.0, 120 - u * 40)],
                1.4, "#fff4dc", 0.6 * math.sin(math.pi * u), (0.3, 1.0, 0.3))
        for j in range(6):
            u = (t * 0.22 + j / 6.0) % 1.0
            fx.sparkle(cr, 128 + 44 * math.cos(j * 1.9 + u), 120 - u * 50, 2.2, PIGMENTS["gold_hi"], 0.7 * (1.0 - u))


class _Stool(Illustration):
    """A small vignette for "So pull up a stool, friend": an empty three-legged stool waiting by a
    candle on a scrap of rug, painted straight onto the parchment (no frame, no sky)."""
    DW, DH = 200.0, 120.0
    grain = 0.0

    def back(self, cr):
        P = PIGMENTS
        rug = []
        for i in range(24):
            a = TAU * i / 24
            rug.append((100 + math.cos(a) * 70, 98 + math.sin(a) * 13))
        pr = wash(cr, rug, P["madder"], 0.85, 0.4, smooth_t=0.8)
        ink_outline(cr, pr, 0.6, INK, 0.6)
        inner = [(100 + math.cos(TAU * i / 24) * 52, 98 + math.sin(TAU * i / 24) * 9) for i in range(24)]
        wash(cr, inner, P["ochre"], 0.6, 0.3, smooth_t=0.8)
        # the stool: a round seat and three splayed legs
        for (x0, x1, yb) in ((84, 74, 104), (116, 126, 104), (101, 101, 108)):
            leg = [(x0 - 2.4, 62), (x0 + 2.4, 62), (x1 + 2.0, yb), (x1 - 2.0, yb)]
            pl = wash(cr, leg, P["sienna"], 0.97, 0.4)
            ink_outline(cr, pl, 0.7, INK, 0.85)
        seat = [(100 + math.cos(TAU * i / 20) * 26, 60 + math.sin(TAU * i / 20) * 6) for i in range(20)]
        rim = [(74, 60), (126, 60), (126, 66), (74, 66)]
        prm = wash(cr, rim, core.shade(P["sienna"], 0.2), 0.97, 0.3)
        ink_outline(cr, prm, 0.7, INK, 0.85)
        ps = wash(cr, seat, P["ochre"], 0.97, 0.4, smooth_t=0.8)
        ink_outline(cr, ps, 0.8, INK, 0.9)
        # the candle on the floor beside it
        cdl = [(148, 100), (148, 80), (156, 80), (156, 100)]
        pc = wash(cr, cdl, P["lead_white"], 0.97, 0.3)
        ink_outline(cr, pc, 0.7, INK, 0.85)

    def anim(self, cr, t):
        b, sway, st = candle_flicker(t, self.seed)
        _glowdot(cr, 152, 72, 22, PIGMENTS["gold_hi"], 0.35 * b)
        fl = [(149.5, 79), (152 + sway * 1.2, 79 - 9 * st), (154.5, 79)]
        cr.new_path()
        core.smooth_closed(cr, fl + [(152, 81)], 0.8)
        core.src(cr, PIGMENTS["ochre"], 0.95)
        cr.fill()


class _Fleuron(Illustration):
    """A gilded hedera leaf on a curling vine (an illuminator's fleuron) to close a rubric."""
    DW, DH = 120.0, 60.0
    grain = 0.0

    def back(self, cr):
        P = PIGMENTS
        for sg in (-1.0, 1.0):
            vine = [(60 + sg * 10, 30), (60 + sg * 26, 22), (60 + sg * 40, 30), (60 + sg * 46, 40), (60 + sg * 38, 44),
                    (60 + sg * 33, 38)]
            ink(cr, vine, 1.4, P["gold_dk"], 0.9, (1.0, 0.8, 0.3))
            for (lx, ly, a) in ((60 + sg * 24, 18, -0.6 * sg), (60 + sg * 44, 30, 0.4 * sg)):
                leaf = [(lx + math.cos(a + k * TAU / 10) * (4.5 if k % 2 == 0 else 2.5),
                         ly + math.sin(a + k * TAU / 10) * (4.5 if k % 2 == 0 else 2.5)) for k in range(10)]
                gild(cr, leaf, smooth_t=0.6, outline=0.4)
        heart = []
        for k in range(40):                                   # the hedera (ivy-heart) leaf
            a = TAU * k / 40
            x_ = 16 * math.sin(a) ** 3
            y_ = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
            heart.append((60 + x_ * 0.9, 31 + y_ * 0.9))
        gild(cr, heart, outline=0.7)
        ink(cr, [(60, 22), (60, 40)], 0.8, P["gold_dk"], 0.8)
        cr.new_path()
        core.circle(cr, 60, 50, 2.6)
        core.src(cr, RUBRIC)
        cr.fill()


def _make(cls, seed):
    inst = cls(seed=seed)
    return inst


illus_castle = _make(_Castle, 1)
illus_doors = _make(_Doors, 2)
illus_dragon = _make(_DragonStreet, 3)
illus_market = _make(_Market, 4)
illus_washhouse = _make(_WashHouse, 5)
illus_bread = _make(_Bread, 6)
illus_stool = _make(_Stool, 7)
illus_fleuron = _make(_Fleuron, 8)
ILLUSTRATIONS = {"castle": illus_castle, "doors": illus_doors, "dragon": illus_dragon, "market": illus_market,
                 "stool": illus_stool, "bread": illus_bread, "washhouse": illus_washhouse, "fleuron": illus_fleuron}


# ----------------------------------------------------------------------------------------
# pages
# ----------------------------------------------------------------------------------------

@dataclass
class Page:
    """One page's contents (page-local units: 0..page_w across, 0..page_h down).

    text       body text ("\\n" = new line; lines wrap; a line starting with ">" is indented -- the
               second half-line of a ballad verse); drop_cap: an illuminated initial for it
    illus      callable illus(cr, w, h, t) painted (clipped) into `box`
    box        illustration box as page fractions (x, y, w, h); frame "rect" | "arch" | "gothic" | None
    text_box   text area as page fractions (x, y, w, h); text_size (units, default page_w / 16)
    align      "left" | "center"; heading: a short title line above the text; folio: page number
    border     "vine" (gold-leaf rules with corner flourishes) | "rule" | None
    cap_lines  how many text lines the drop cap stands beside (its size follows)
    ink        text colour (default INK; RUBRIC for a red rubric)
    """
    text: str = ""
    drop_cap: str = None
    illus: object = None
    box: tuple = None
    frame: str = "rect"
    text_box: tuple = None
    text_size: float = None
    align: str = "left"
    heading: str = None
    folio: str = None
    border: str = "vine"
    seed: int = 0
    cap_lines: int = 3
    ink: str = None


@dataclass
class Spread:
    left: Page
    right: Page


PROLOGUE_SPREADS = [
    Spread(Page(text="nce upon a time,\n>in a kingdom of stone,\nLived a town full of folk\n>who were living alone.\n"
                     "They had potions for sleeping\n>and charms for the rain,\nAnd a lock on each heart,\n"
                     ">and a latch on each pane.",
                drop_cap="O", text_box=(0.11, 0.11, 0.79, 0.5), text_size=150.0 / 17.0, illus=illus_doors,
                box=(0.14, 0.595, 0.72, 0.31),
                frame="rect", folio="j", seed=1),
           Page(illus=illus_castle, box=(0.13, 0.09, 0.74, 0.82), frame="gothic", folio="ij", seed=2)),
    Spread(Page(illus=illus_dragon, box=(0.13, 0.09, 0.74, 0.62), frame="arch",
                text="Now a dragon lived there\nwith a scarf and a sigh,\nAnd he waved at his neighbours,\nwho hurried on by.",
                text_box=(0.12, 0.715, 0.76, 0.16), text_size=150.0 / 18.5, align="center", folio="iij", seed=3),
           Page(illus=illus_market, box=(0.13, 0.09, 0.74, 0.62), frame="arch",
                text="Every merchant in town\nhad a stone he could sell \u2014\nBut for what he was missing,\nthere wasn\u2019t a spell.",
                text_box=(0.12, 0.715, 0.76, 0.16), text_size=150.0 / 18.5, align="center", folio="iv", seed=4)),
    Spread(Page(text="o pull up a stool, friend,\n>and hear how it\u2019s said:\nHow a kingdom of stone\n"
                     ">found its way back to bread.",
                drop_cap="S", cap_lines=2, text_box=(0.11, 0.14, 0.79, 0.3), text_size=150.0 / 17.0,
                illus=illus_stool, box=(0.1, 0.5, 0.8, 0.36), frame=None, folio="v", seed=5),
           Page(illus=illus_bread, box=(0.13, 0.09, 0.74, 0.82), frame="gothic", folio="vj", seed=6)),
    # "...back to bread": the page turns to the wash-house at night (the push-in dissolves into S1)
    Spread(Page(text="Here beginneth\nthe tale of\nthe Stone\nand the Bread", align="center", ink=RUBRIC,
                text_box=(0.12, 0.32, 0.76, 0.3), text_size=150.0 / 13.0, illus=illus_fleuron,
                box=(0.3, 0.6, 0.4, 0.1), frame=None, folio="vij", seed=7),
           Page(illus=illus_washhouse, box=(0.13, 0.09, 0.74, 0.82), frame="gothic", folio="viij", seed=8)),
]


def _frame_path(cr, x, y, w, h, kind):
    cr.new_path()
    if kind == "arch":
        r = w / 2.0
        cr.move_to(x, y + h)
        cr.line_to(x, y + r)
        cr.arc(x + r, y + r, r, math.pi, 2 * math.pi)
        cr.line_to(x + w, y + h)
        cr.close_path()
    elif kind == "gothic":
        # a pointed arch: two arcs of radius r centred on the springing line, meeting at the apex
        r = w * 0.8
        off = r - w / 2.0
        rise = math.sqrt(r * r - off * off)
        ys = y + rise
        cr.move_to(x, y + h)
        cr.line_to(x, ys)
        cr.arc(x + r, ys, r, math.pi, TAU + math.atan2(-rise, -off))
        cr.arc(x + w - r, ys, r, TAU + math.atan2(-rise, off), TAU)
        cr.line_to(x + w, y + h)
        cr.close_path()
    else:
        cr.rectangle(x, y, w, h)
    return B.Path(cr)


def _vine_corner(cr, x, y, sx, sy, s, seed, shimmer):
    """A corner flourish: a gold vine scroll with three painted leaves and gold dots."""
    pts = []
    for k in range(14):
        a = k / 13.0 * 4.2
        r = s * (1.0 - k / 16.0) * 0.55
        pts.append((x + sx * (s * 0.2 + r * math.cos(a) * 0.9), y + sy * (s * 0.2 + r * math.sin(a))))
    ink(cr, pts, s * 0.07, PIGMENTS["gold_dk"], 0.95, (1.0, 0.8, 0.2))
    ink(cr, pts, s * 0.035, PIGMENTS["gold_hi"], 0.9, (1.0, 0.8, 0.2))
    cols = (PIGMENTS["ultramarine"], PIGMENTS["vermilion"], PIGMENTS["verdigris"])
    for j, k in enumerate((3, 7, 11)):
        px, py = pts[k]
        a = math.atan2(pts[k + 1][1] - py, pts[k + 1][0] - px) + (1.2 if j % 2 else -1.2)
        L = s * 0.24
        leaf = [(px, py), (px + math.cos(a - 0.35) * L * 0.6, py + math.sin(a - 0.35) * L * 0.6),
                (px + math.cos(a) * L, py + math.sin(a) * L), (px + math.cos(a + 0.35) * L * 0.6, py + math.sin(a + 0.35) * L * 0.6)]
        pl = wash(cr, leaf, cols[(j + seed) % 3], 0.95, 0.3, smooth_t=0.6)
        ink_outline(cr, pl, s * 0.02, PIGMENTS["gold_dk"], 0.9)
    for k in (1, 5, 9, 13):
        px, py = pts[k]
        cr.new_path()
        core.circle(cr, px + sx * s * 0.06, py - sy * s * 0.05, s * 0.04)
        gild(cr, path=B.Path(cr), shimmer=shimmer, outline=0.0)


def _drop_cap(cr, letter, x, y, size, shimmer, detail, seed):
    """An illuminated initial: a gold letter on an ultramarine ground in a gilt frame, white
    penwork filigree, a vine tendril down the margin (and a tiny castle in an O's heart)."""
    P = PIGMENTS
    box = [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]
    cr.new_path()
    core.polygon(cr, box)
    bp = B.Path(cr)
    wash(cr, None, P["ultramarine"], 0.97, 0.35, path=bp)
    if detail >= 1:
        cr.save()
        bp.add(cr)
        cr.clip()
        curls = []
        rng = random.Random(seed)
        for _ in range(9):
            cx, cy = x + rng.uniform(0.1, 0.9) * size, y + rng.uniform(0.1, 0.9) * size
            r = size * rng.uniform(0.05, 0.09)
            curls.append([(cx + math.cos(a) * r * (1 - a / 9), cy + math.sin(a) * r * (1 - a / 9)) for a in (0.0, 1.5, 3.0, 4.5, 6.0)])
        B.detail_lines(cr, curls, size * 0.012, "#f4ead6", 0.55)
        cr.restore()
    # gilt frame
    cr.new_path()
    core.polygon(cr, box)
    cr.set_line_width(size * 0.05)
    cr.set_source_rgb(*core.col(PIGMENTS["gold"])[:3])
    cr.stroke()
    ink_outline(cr, bp, size * 0.012, INK, 0.9)
    # the letter (gilt)
    cr.new_path()
    core.text_path(cr, letter, x + size * 0.5, y + size * 0.54, size * 1.08, CAP_FONT, align="center", valign="middle")
    lp = B.Path(cr)
    cr.save()
    lp.add(cr)
    cr.set_line_width(size * 0.05)
    core.src(cr, "#1b1406", 0.7)
    cr.stroke()
    cr.restore()
    gild(cr, path=lp, shimmer=shimmer, outline=size * 0.01)
    if letter.upper() == "O" and detail >= 2:
        # a historiated O: a tiny castle on a hill in its heart
        cx, cy = x + size * 0.5, y + size * 0.56
        s = size * 0.13
        cr.save()
        cr.new_path()
        core.ellipse(cr, cx, cy, s * 1.5, s * 1.9)
        cr.clip()
        core.src(cr, "#d98a6a", 0.8)
        cr.paint()
        core.src(cr, P["sap"])
        cr.new_path()
        core.ellipse(cr, cx, cy + s * 2.2, s * 2.4, s * 1.4)
        cr.fill()
        core.src(cr, P["slate"])
        cr.rectangle(cx - s * 0.7, cy - s * 0.4, s * 1.4, s * 1.1)
        cr.rectangle(cx - s * 1.0, cy - s * 0.9, s * 0.45, s * 1.6)
        cr.rectangle(cx + s * 0.55, cy - s * 0.9, s * 0.45, s * 1.6)
        cr.fill()
        core.src(cr, P["vermilion"])
        for tx in (cx - s * 0.78, cx + s * 0.78):
            core.polygon(cr, [(tx - s * 0.32, cy - s * 0.9), (tx, cy - s * 1.6), (tx + s * 0.32, cy - s * 0.9)])
            cr.fill()
        cr.restore()
    # a tendril down the margin
    tx0 = x - size * 0.16
    pts = [(x + size * 0.05, y + size), (tx0, y + size * 1.25), (tx0 + size * 0.08, y + size * 1.6), (tx0 - size * 0.04, y + size * 1.95)]
    ink(cr, pts, size * 0.03, PIGMENTS["gold_dk"], 0.9, (1.0, 0.8, 0.15))
    for j, (px, py) in enumerate(pts[1:]):
        lf = [(px, py), (px + size * 0.12, py - size * 0.05), (px + size * 0.17, py + size * 0.03), (px + size * 0.06, py + size * 0.05)]
        pl = wash(cr, lf, (P["vermilion"], P["verdigris"], P["ultramarine"])[j % 3], 0.95, 0.3, smooth_t=0.6)
        ink_outline(cr, pl, size * 0.01, PIGMENTS["gold_dk"], 0.8)


def _wrap_lines(cr, text, widths, size, font, italic, indent=0.0):
    """Greedy wrap where line i may be `widths[i]` wide (the last value repeats). Paragraphs
    starting with ">" are indented by `indent`. -> [(line, indent_px)]"""
    core.set_font(cr, size, font, False, italic)
    lines = []
    for para in text.split("\n"):
        ind = 0.0
        if para.startswith(">"):
            para, ind = para[1:].lstrip(), indent
        cur = ""
        for word in para.split(" "):
            wmax = widths[min(len(lines), len(widths) - 1)] - ind
            trial = word if not cur else cur + " " + word
            if cr.text_extents(trial)[4] <= wmax or not cur:
                cur = trial
            else:
                lines.append((cur, ind))
                cur = word
        lines.append((cur, ind))
    return lines


def _parchment(cr, w, h, side, seed, light):
    """Parchment ground + grain + aged edges + a gutter shadow; side -1 left page, +1 right."""
    base = B.palette(light, B.Mat.of(PARCHMENT, shadow_k=0.85)).lit if light is not None else core.col(PARCHMENT)
    base = core.mix(core.col(PARCHMENT), base, 0.45)
    cr.rectangle(0, 0, w, h)
    core.src(cr, base)
    cr.fill()
    paper_grain(cr, 0, 0, w, h, 0.5, scale=0.3, seed=seed + 3)
    dk = core.col(PARCHMENT_DK)
    edge = core.shade(dk, 0.35)
    for (x0, y0, x1, y1, a) in ((0, 0, 0, h * 0.06, 0.32), (0, h, 0, h * 0.94, 0.32)):
        g = core.linear(x0, y0, x1, y1, [(0.0, core.alpha(edge, a)), (1.0, core.alpha(edge, 0.0))])
        cr.rectangle(0, 0, w, h)
        cr.set_source(g)
        cr.fill()
    ox0, ox1 = (w, w * 0.9) if side > 0 else (0.0, w * 0.1)       # the outer (fore-) edge
    g = core.linear(ox0, 0, ox1, 0, [(0.0, core.alpha(edge, 0.36)), (1.0, core.alpha(edge, 0.0))])
    cr.rectangle(0, 0, w, h)
    cr.set_source(g)
    cr.fill()
    # the gutter: a soft shadow where the page curls down into the spine
    gut = 0.0 if side > 0 else w
    g = core.linear(gut, 0, gut + (w * 0.16 if side > 0 else -w * 0.16), 0,
                    [(0.0, (0.18, 0.1, 0.05, 0.55)), (0.35, (0.2, 0.12, 0.06, 0.18)), (1.0, (0.2, 0.12, 0.06, 0.0))])
    cr.rectangle(0, 0, w, h)
    cr.set_source(g)
    cr.fill()
    # foxing
    rng = random.Random(seed * 13 + 1)
    for _ in range(5):
        fx_, fy_ = rng.choice((rng.uniform(0, w * 0.15), rng.uniform(w * 0.85, w))), rng.uniform(0, h)
        _bloom(cr, fx_, fy_, rng.uniform(2.5, 6.0), "#8a5a2a", rng.uniform(0.08, 0.16))
    return base


def _page_under(cr, page, w, h, side, light, shimmer, detail, blank):
    """Parchment + gold-leaf border (everything under the illustration)."""
    seed = page.seed if page is not None else 7
    _parchment(cr, w, h, side, seed, light)
    if blank or page is None:
        # a page of some other part of the story: faint lines of script
        rng = random.Random(seed + 77)
        lines = []
        y = h * 0.14
        while y < h * 0.86:
            x0 = w * 0.16
            x1 = w * rng.uniform(0.7, 0.84)
            lines.append([(x0, y), (x1, y + rng.uniform(-0.4, 0.4))])
            y += h * 0.045
        B.detail_lines(cr, lines, h * 0.006, INK, 0.16, taper=(0.3, 1.0, 0.3))
        return
    P = PIGMENTS
    m = w * 0.075
    if page.border in ("vine", "rule"):
        r = [(m, m), (w - m, m), (w - m, h - m), (m, h - m)]
        cr.new_path()
        core.polygon(cr, r)
        rp = B.Path(cr)
        cr.save()
        rp.add(cr)
        cr.set_line_width(w * 0.009)
        cr.set_source_rgb(*core.col(P["gold"])[:3])
        cr.stroke()
        cr.restore()
        cr.new_path()
        core.polygon(cr, [(m + w * 0.012, m + w * 0.012), (w - m - w * 0.012, m + w * 0.012), (w - m - w * 0.012, h - m - w * 0.012),
                          (m + w * 0.012, h - m - w * 0.012)])
        ink_outline(cr, B.Path(cr), w * 0.003, INK, 0.6)
        if page.border == "vine" and detail >= 1:
            s = w * 0.16
            for (cx, cy, sx, sy) in ((m, m, 1, 1), (w - m, m, -1, 1), (w - m, h - m, -1, -1), (m, h - m, 1, -1)):
                _vine_corner(cr, cx, cy, sx, sy, s, seed + int(cx), shimmer)
            ox = m if side < 0 else w - m
            cr.new_path()
            core.circle(cr, ox, h * 0.5, w * 0.018)
            gild(cr, path=B.Path(cr), shimmer=shimmer, outline=0.2)


def _page_over(cr, page, w, h, side, light, shimmer, detail):
    """Illustration frame, text with its illuminated initial, folio (everything over it)."""
    if page is None:
        return
    P = PIGMENTS
    seed = page.seed
    m = w * 0.075
    if page.illus is not None and page.box is not None and page.frame:
        bx, by, bw, bh = page.box[0] * w, page.box[1] * h, page.box[2] * w, page.box[3] * h
        fp = _frame_path(cr, bx, by, bw, bh, page.frame)
        cr.save()
        fp.add(cr)
        cr.set_line_width(w * 0.014)
        cr.set_source_rgb(*core.col(P["gold"])[:3])
        cr.stroke()
        cr.restore()
        ink_outline(cr, fp, w * 0.004, INK, 0.85)
    if page.text:
        tb = page.text_box or (0.13, 0.12, 0.74, 0.76)
        tx, ty, tw = tb[0] * w, tb[1] * h, tb[2] * w
        size = page.text_size or w / 16.0
        lh = size * 1.24
        cap_lines = max(1, int(page.cap_lines)) if page.drop_cap else 0
        cap = lh * cap_lines - size * 0.15 if page.drop_cap else 0.0
        widths = [tw - cap - size * 0.5] * cap_lines + [tw]
        lines = _wrap_lines(cr, page.text, widths, size, TEXT_FONT, True, indent=size * 1.3)
        if page.drop_cap:
            _drop_cap(cr, page.drop_cap, tx, ty + size * 0.12, cap, shimmer, detail, seed)
        core.set_font(cr, size, TEXT_FONT, False, True)
        asc = cr.font_extents()[0]
        for i, (ln, ind) in enumerate(lines):
            x = tx + (cap + size * 0.5 if i < cap_lines else ind)
            y = ty + asc + i * lh
            if page.align == "center":
                core.text(cr, ln, tx + tw / 2.0, y, size, TEXT_FONT, page.ink or INK, align="center", italic=True,
                          alpha_=0.93)
            else:
                core.text(cr, ln, x, y, size, TEXT_FONT, page.ink or INK, italic=True, alpha_=0.93)
    if page.folio:
        core.text(cr, page.folio, w * 0.5, h - m * 0.45, w * 0.045, TEXT_FONT, core.mix(INK, PARCHMENT, 0.35),
                  align="center", italic=True)


_PAGE_CACHE = {}


def _bucket(dev):
    return 2.0 ** (math.ceil(math.log2(max(0.25, dev)) * 2.0) / 2.0)


def _cached_layer(key, w, h, res, fn):
    surf = _PAGE_CACHE.get(key)
    if surf is None:
        if len(_PAGE_CACHE) > 48:
            _PAGE_CACHE.clear()
        surf = core.new_surface(max(1, int(math.ceil(w * res))), max(1, int(math.ceil(h * res))))
        c2 = core.new_context(surf)
        c2.scale(res, res)
        fn(c2)
        surf.flush()
        _PAGE_CACHE[key] = surf
    return surf


def _paint_layer(cr, surf, res):
    cr.save()
    cr.scale(1.0 / res, 1.0 / res)
    cr.set_source_surface(surf, 0, 0)
    cr.get_source().set_filter(cairo.FILTER_BILINEAR)
    cr.paint()
    cr.restore()


def draw_page(cr, page, w, h, t=0.0, side=1, light=None, shimmer=0.0, detail=2, blank=False, cache=True):
    """Paint one page in page-local units (0, 0, w, h): parchment, gold-leaf border, the
    illustration (clipped to its frame), text with the illuminated initial, the folio.
    side +1 = right-hand page (gutter on its left), -1 = left-hand page. cache=True keeps the
    static layers (under / over the illustration) as surfaces per resolution bucket, so a page
    costs two paints plus its illustration's living layer."""
    if not cache:
        _page_under(cr, page, w, h, side, light, shimmer, detail, blank)
        if page is not None and not blank and page.illus is not None and page.box is not None:
            _page_illus(cr, page, w, h, t)
        if not blank:
            _page_over(cr, page, w, h, side, light, shimmer, detail)
        return
    res = _bucket(B.device_scale(cr))
    lname = light.name if light is not None else "none"
    pid = id(page) if page is not None else 0
    base = (pid, round(w, 2), round(h, 2), res, side, lname, detail, blank)
    under = _cached_layer(("u",) + base, w, h, res,
                          lambda c2: _page_under(c2, page, w, h, side, light, 0.5, detail, blank))
    _paint_layer(cr, under, res)
    if page is None or blank:
        return
    if page.illus is not None and page.box is not None:
        _page_illus(cr, page, w, h, t)
    over = _cached_layer(("o",) + base, w, h, res, lambda c2: _page_over(c2, page, w, h, side, light, 0.5, detail))
    _paint_layer(cr, over, res)


def _page_illus(cr, page, w, h, t):
    bx, by, bw, bh = page.box[0] * w, page.box[1] * h, page.box[2] * w, page.box[3] * h
    fp = _frame_path(cr, bx, by, bw, bh, page.frame or "rect")
    cr.save()
    fp.add(cr)
    cr.clip()
    cr.translate(bx, by)
    page.illus(cr, bw, bh, t)
    cr.restore()


# ----------------------------------------------------------------------------------------
# the book
# ----------------------------------------------------------------------------------------

LEATHER = "#5a2a1c"                 # oxblood calf
LEATHER_DK = "#3a1a12"
BRASS = "#c09443"


class Book:
    """The great storybook: its spreads (pages), title and size (scale-1 px).

    spreads   list of Spread(left Page, right Page); spread k is what lies open after the opening
              (k = 0) or after k page turns
    """

    def __init__(self, spreads=None, title="The Stone and the Bread", page_w=150.0, page_h=200.0, block=12.0,
                 seed=3):
        self.spreads = list(spreads) if spreads is not None else list(PROLOGUE_SPREADS)
        self.title = title
        self.pw, self.ph = float(page_w), float(page_h)
        self.block = float(block)             # thickness of each half of the page block when open
        self.ov = 6.0                         # board overhang
        self.bt = 4.5                         # board thickness
        self.seed = seed

    def spread(self, k):
        if not self.spreads:
            return Spread(Page(), Page())
        return self.spreads[max(0, min(len(self.spreads) - 1, int(k)))]


@dataclass
class BookRig:
    """Where things ended up (caller coordinates)."""
    anchor: tuple = (0.0, 0.0)                     # middle of the spine
    pages: dict = field(default_factory=dict)      # "left"/"right" -> 4 corner points (tl, tr, br, bl)
    page_matrix: dict = field(default_factory=dict)  # "left"/"right" -> cairo.Matrix: page units
    #                                                  (0..page_w, 0..page_h) -> caller coords
    scale: float = 1.0
    page_size: tuple = (150.0, 200.0)              # (page_w, page_h) in page units

    def page_point(self, side, u, v):
        """Caller coords of the point at FRACTIONS (u, v) (0..1, from the page's top-left) of the
        "left"/"right" page -- camera targets, e.g. the middle of an illustration's box."""
        m = self.page_matrix.get(side)
        if m is None:
            return self.anchor
        return m.transform_point(u * self.page_size[0], v * self.page_size[1])


def _proj(view):
    cv, sv = math.cos(view), math.sin(view)
    return lambda x, y, z: (x, y * cv - z * sv)


def _page_curve(u_frac, dip=4.0):
    """Height offset of an open page across its width (0 at the gutter .. 1 outer edge): it dips
    into the gutter and bows up a little."""
    return -dip * math.exp(-u_frac / 0.07) + 1.6 * math.sin(math.pi * min(1.0, u_frac)) ** 0.5


def _deckle(n, seed, amp=0.7):
    rng = random.Random(seed)
    return [amp * (rng.random() - 0.5) * 2.0 for _ in range(n)]


def _page_outline(book, side, z, prj, seed, ntop=10, nedge=14):
    """Screen polygon of an open page lying at height z (side +1 right, -1 left)."""
    W, H = book.pw, book.ph
    dk = _deckle(nedge, seed)
    top, bot, edge = [], [], []
    for i in range(ntop + 1):
        u = i / ntop
        x = side * (0.8 + u * W)
        zz = z + _page_curve(u)
        top.append(prj(x, -H / 2.0, zz))
        bot.append(prj(x, H / 2.0, zz))
    for j in range(nedge):
        v = (j + 0.5) / nedge
        edge.append(prj(side * (W + 0.8 + dk[j]), -H / 2.0 + v * H, z + _page_curve(1.0)))
    return top + edge + bot[::-1]


def _page_matrix(book, side, z, view):
    """cairo.Matrix mapping page-local (u, v) -> book-plane screen units for a flat page at z."""
    W, H = book.pw, book.ph
    cv, sv = math.cos(view), math.sin(view)
    x0 = 0.8 if side > 0 else -0.8 - W
    return cairo.Matrix(1.0, 0.0, 0.0, cv, x0, -H / 2.0 * cv - z * sv)


def _block(cr, book, side, z0, z1, prj, light, gilt=True):
    """A page block (from z0 to z1) on one side: its front edge (gilt, finely lined)."""
    if z1 - z0 < 0.3:
        return
    W, H = book.pw, book.ph
    xa, xb = side * 0.8, side * (W + 0.8)
    a, b = prj(xa, H / 2.0, z1), prj(xb, H / 2.0, z1)
    c, d = prj(xb, H / 2.0, z0), prj(xa, H / 2.0, z0)
    cr.new_path()
    core.polygon(cr, [a, b, c, d])
    pal = B.palette(light, B.Mat.of(PIGMENTS["gold"] if gilt else PARCHMENT_DK, sheen=0.5))
    core.src(cr, core.mix(pal.lit, PARCHMENT_DK, 0.35))
    cr.fill()
    n = int((z1 - z0) / 1.6)
    lines = []
    for k in range(1, n):
        zz = z0 + (z1 - z0) * k / n
        lines.append([prj(xa, H / 2.0, zz), prj(xb, H / 2.0, zz)])
    B.detail_lines(cr, lines, 0.35, pal.line, 0.3, taper=(1.0, 1.0, 1.0))


def _board_top(cr, book, side, z, prj, light, outline=True):
    """A cover board lying flat (its leather rim shows round the page block) + its front edge."""
    W, H, ov, bt = book.pw, book.ph, book.ov, book.bt
    x0, x1 = 0.0, side * (W + ov + 0.8)
    pts = [prj(x0, -H / 2 - ov, z), prj(x1, -H / 2 - ov, z), prj(x1, H / 2 + ov, z), prj(x0, H / 2 + ov, z)]
    edge = [prj(x0, H / 2 + ov, z), prj(x1, H / 2 + ov, z), prj(x1, H / 2 + ov, z - bt), prj(x0, H / 2 + ov, z - bt)]
    mat = B.Mat.of(LEATHER, sheen=0.3)
    pal = B.palette(light, mat)
    cr.new_path()
    core.polygon(cr, edge)
    core.src(cr, pal.shadow)
    cr.fill()
    cr.new_path()
    core.polygon(cr, pts)
    core.src(cr, core.mix(pal.lit, pal.shadow, 0.25))
    cr.fill()
    if outline:
        cr.new_path()
        core.polygon(cr, pts)
        core.polygon(cr, edge)
        cr.set_line_width(0.9)
        core.src(cr, pal.line, 0.9)
        cr.stroke()


@functools.lru_cache(maxsize=2)
def _marble_tile(size=192, seed=5):
    """Marbled endpaper (combed swirls of madder, indigo and ochre on cream)."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    n = core.noise_array(size, size, scale=40.0, octaves=3, seed=seed)
    v = np.sin((x * 0.09 + n * 5.5) + np.sin(y * 0.05) * 2.0)
    w = np.sin((y * 0.12 + n * 4.0))
    cols = np.array([[0.93, 0.88, 0.76], [0.55, 0.18, 0.2], [0.17, 0.2, 0.38], [0.8, 0.6, 0.28]], np.float32)
    idx = np.clip(((v * 0.5 + 0.5) * 3.0 + (w > 0.6)).astype(int), 0, 3)
    rgb = cols[idx]
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., 0] = (rgb[..., 2] * 255).astype(np.uint8)
    arr[..., 1] = (rgb[..., 1] * 255).astype(np.uint8)
    arr[..., 2] = (rgb[..., 0] * 255).astype(np.uint8)
    arr[..., 3] = 255
    data = bytearray(arr.tobytes())
    return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, size, size, size * 4), data


def _cover_face(cr, book, light, shimmer, detail, inside=False):
    """The front board's face in board units (bx 0 = spine .. CW, by -CH/2 .. CH/2)."""
    W, H, ov = book.pw, book.ph, book.ov
    CW, CH = W + ov + 0.8, H + 2 * ov
    mat = B.Mat.of(LEATHER, sheen=0.3)
    pal = B.palette(light, mat)
    cr.rectangle(0, -CH / 2, CW, CH)
    core.src(cr, pal.lit)
    cr.fill()
    if inside:
        # leather turn-ins round a marbled pastedown
        tile, _k = _marble_tile()
        cr.save()
        cr.rectangle(7, -CH / 2 + 7, CW - 14, CH - 14)
        cr.clip()
        pat = cairo.SurfacePattern(tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        m = cairo.Matrix()
        m.scale(2.2, 2.2)
        pat.set_matrix(m)
        cr.set_source(pat)
        cr.paint()
        core.src(cr, "#2a160c", 0.18)
        cr.paint()
        cr.restore()
        return
    # the leather: grain + worn, darker edges
    paper_grain(cr, 0, -CH / 2, CW, CH, 0.35, scale=0.5, seed=21)
    for (x0, y0, x1, y1) in ((0, -CH / 2, 0, -CH / 2 + 18), (0, CH / 2, 0, CH / 2 - 18), (CW, 0, CW - 16, 0)):
        g = core.linear(x0, y0, x1, y1, [(0.0, core.alpha(LEATHER_DK, 0.6)), (1.0, core.alpha(LEATHER_DK, 0.0))])
        cr.rectangle(0, -CH / 2, CW, CH)
        cr.set_source(g)
        cr.fill()
    # the spine fold
    g = core.linear(0, 0, 14, 0, [(0.0, core.alpha(LEATHER_DK, 0.7)), (1.0, core.alpha(LEATHER_DK, 0.0))])
    cr.rectangle(0, -CH / 2, 14, CH)
    cr.set_source(g)
    cr.fill()
    # blind tooling: a double frame and a diagonal lattice
    cr.save()
    for inset, col_, dx, wdt, al in ((8.0, pal.shadow, 0.0, 0.9, 0.8), (12.0, pal.shadow, 0.0, 0.9, 0.8),
                                     (8.0, pal.hi, 0.7, 0.45, 0.25), (12.0, pal.hi, 0.7, 0.45, 0.25)):
        cr.new_path()
        cr.rectangle(8.0 + inset + dx, -CH / 2 + inset + dx, CW - 2 * inset - 8.0, CH - 2 * inset)
        cr.set_line_width(wdt)
        core.src(cr, col_, al)
        cr.stroke()
    # a lozenge lattice blind-tooled between the rules
    cr.rectangle(28.0, -CH / 2 + 18.0, CW - 46.0, CH - 36.0)
    cr.clip()
    cr.new_path()
    for k in range(-8, 9):
        x0 = 28.0 + (CW - 46.0) / 2 + k * 16.0
        cr.move_to(x0 - CH, -CH / 2 - 40)
        cr.line_to(x0 + CH * 0.6, CH / 2 + 40)
        cr.move_to(x0 + CH * 0.6, -CH / 2 - 40)
        cr.line_to(x0 - CH, CH / 2 + 40)
    cr.set_line_width(0.5)
    core.src(cr, pal.shadow, 0.35)
    cr.stroke()
    cr.restore()
    # gilt title panel
    px0, px1 = 30.0, CW - 22.0
    py0, py1 = -CH * 0.26, CH * 0.12
    panel = [(px0, py0), (px1, py0), (px1, py1), (px0, py1)]
    cr.new_path()
    core.polygon(cr, panel)
    cr.set_line_width(1.6)
    cr.set_source_rgb(*core.col(PIGMENTS["gold"])[:3])
    cr.stroke()
    cr.new_path()
    core.polygon(cr, [(px0 + 3, py0 + 3), (px1 - 3, py0 + 3), (px1 - 3, py1 - 3), (px0 + 3, py1 - 3)])
    cr.set_line_width(0.6)
    cr.stroke()
    words = book.title.split(" ")
    rows = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:])] if len(words) == 5 else [book.title]
    rows = [r for r in rows if r]
    cx = (px0 + px1) / 2
    sz = (px1 - px0) * 0.17
    yy = py0 + (py1 - py0) * 0.32
    for i, r in enumerate(rows):
        size = sz * (0.62 if r.lower() == "and the" else 1.0)
        cr.new_path()
        core.text_path(cr, r, cx, yy, size, CAP_FONT, align="center", valign="middle")
        tp = B.Path(cr)
        cr.save()
        tp.add(cr)
        cr.set_line_width(1.0)
        core.src(cr, "#1b0e08", 0.8)
        cr.stroke()
        cr.restore()
        gild(cr, path=tp, shimmer=shimmer, outline=0.25)
        yy += sz * (0.7 if r.lower() == "and the" else 1.05) + (0 if i else 0.0)
    # the emblem: a stone and a broken loaf in a gilt roundel
    ey = CH * 0.27
    cr.new_path()
    core.circle(cr, cx, ey, 15.0)
    cr.set_line_width(1.2)
    cr.set_source_rgb(*core.col(PIGMENTS["gold"])[:3])
    cr.stroke()
    st = [(cx - 11, ey + 5), (cx - 10, ey - 2), (cx - 4, ey - 5), (cx + 0.5, ey - 1), (cx - 1, ey + 5)]
    cr.new_path()
    core.smooth_closed(cr, st, 0.7)
    gild(cr, path=B.Path(cr), shimmer=shimmer * 0.6, outline=0.3)
    for k in (0, 1):
        ox = cx + 4.5 + k * 5.5
        half = [(ox - 2.5 + k * 1.5, ey + 5), (ox - 3.0 + k * 1.5, ey - 1), (ox + k * 2.5, ey - 5), (ox + 3.0, ey), (ox + 2.6, ey + 5)]
        cr.new_path()
        core.smooth_closed(cr, half, 0.7)
        gild(cr, path=B.Path(cr), shimmer=shimmer, outline=0.3)
    # brass corners with rivets, and a clasp catch at the fore-edge
    bm = B.Mat.of(BRASS, sheen=0.8)
    bpal = B.palette(light, bm)
    for (ox, oy, sx, sy) in ((0.0, -CH / 2, 1, 1), (CW, -CH / 2, -1, 1), (CW, CH / 2, -1, -1), (0.0, CH / 2, 1, -1)):
        L = 17.0
        corner = [(ox, oy), (ox + sx * L, oy), (ox + sx * L * 0.82, oy + sy * 3.2), (ox + sx * 3.2, oy + sy * L * 0.82), (ox, oy + sy * L)]
        cr.new_path()
        core.polygon(cr, corner)
        cp = B.Path(cr)
        cp.add(cr)
        core.src(cr, bpal.lit)
        cr.fill()
        cr.new_path()
        core.polygon(cr, [(ox + sx * 2.5, oy + sy * 2.5), (ox + sx * L * 0.62, oy + sy * 2.5), (ox + sx * 2.5, oy + sy * L * 0.62)])
        core.src(cr, bpal.hi, 0.55 + 0.4 * shimmer)
        cr.fill()
        ink_outline(cr, cp, 0.7, bpal.line, 0.95)
        cr.new_path()
        core.circle(cr, ox + sx * 6.0, oy + sy * 6.0, 1.3)
        core.src(cr, bpal.line)
        cr.fill()
    clasp = [(CW - 10, -7), (CW + 1.5, -7), (CW + 1.5, 7), (CW - 10, 7)]
    cr.new_path()
    core.polygon(cr, clasp)
    cp = B.Path(cr)
    cp.add(cr)
    core.src(cr, bpal.lit)
    cr.fill()
    ink_outline(cr, cp, 0.7, bpal.line, 0.95)
    cr.new_path()
    core.circle(cr, CW - 5, 0, 2.0)
    core.src(cr, bpal.line)
    cr.fill()


def _cover_matrix(book, theta, z_h, view):
    cv, sv = math.cos(view), math.sin(view)
    return cairo.Matrix(math.cos(theta), -math.sin(theta) * sv, 0.0, cv, 0.0, -z_h * sv)


def _turning_page(cr, book, p, front, back, t, light, view, z_r, z_l, shimmer, detail, res, plain=False, seed=0):
    """One flexible page turning right -> left with progress p (0..1): curled cross-section,
    drawn as strips of its two faces (front = the right page it was, back = the next left page),
    each strip shaded by how it faces the light. Returns nothing."""
    W, H = book.pw, book.ph
    prj = _proj(view)
    N = 16
    lead = 0.42 * math.sin(math.pi * p)
    al = [math.pi * clamp(p + lead * (k / N) ** 1.2 - 0.1 * lead) for k in range(N + 1)]
    zh = lerp(z_r, z_l, p)
    xs, zs = [0.0], [zh]
    ds = W / N
    for k in range(N):
        a = (al[k] + al[k + 1]) / 2
        xs.append(xs[-1] + math.cos(a) * ds)
        zs.append(zs[-1] + math.sin(a) * ds)
    # keep it above the stacks it lies on
    for k in range(N + 1):
        floor = z_r if xs[k] > 0 else z_l
        zs[k] = max(zs[k], floor + 0.4)
    # textures (rendered at screen resolution for this frame)
    texf = texb = None
    if not plain:
        texf = _page_texture(book, front, t, 1, light, shimmer, detail, res)
        texb = _page_texture(book, back, t, -1, light, shimmer, detail, res)
    base = core.col(PARCHMENT)
    lx, lz = -0.55, 0.83                        # light from the upper left, above the desk
    for k in range(N):
        a = (al[k] + al[k + 1]) / 2
        nfront = math.cos(a)                    # > 0: the front face is up/toward us
        x0, x1, z0, z1 = xs[k], xs[k + 1], zs[k], zs[k + 1]
        tl, tr = prj(x0, -H / 2, z0), prj(x1, -H / 2, z1)
        bl, br = prj(x0, H / 2, z0), prj(x1, H / 2, z1)
        if abs(tr[0] - tl[0]) < 0.02 and abs(tr[1] - tl[1]) < 0.02:
            continue
        # strip quad, widened a hair so neighbours overlap (no hairline seams)
        ex, ey = (tr[0] - tl[0]), (tr[1] - tl[1])
        L = math.hypot(ex, ey) or 1.0
        ux, uy = ex / L * 0.35, ey / L * 0.35
        quad = [(tl[0] - ux, tl[1] - uy), (tr[0] + ux, tr[1] + uy), (br[0] + ux, br[1] + uy), (bl[0] - ux, bl[1] - uy)]
        nx, nz = -math.sin(a), math.cos(a)      # surface normal (front side)
        if nfront < 0:
            nx, nz = -nx, -nz
        lam = clamp(0.62 + 0.38 * (nx * lx + nz * lz))
        cr.save()
        cr.new_path()
        core.polygon(cr, quad)
        cr.clip()
        tex = texf if nfront >= 0 else texb
        if tex is not None:
            surf, r = tex
            s0 = k * ds
            # affine: texture page-local (u, v) -> screen; front: u = s; back: u = W - s
            dux, duy = (tr[0] - tl[0]) / ds, (tr[1] - tl[1]) / ds
            if nfront >= 0:
                m = cairo.Matrix(dux, duy, 0.0, (bl[1] - tl[1]) / H, tl[0] - dux * s0, tl[1] - duy * s0)
            else:
                m = cairo.Matrix(-dux, -duy, 0.0, (bl[1] - tl[1]) / H, tl[0] + dux * (W - s0), tl[1] + duy * (W - s0))
            cr.transform(m)
            cr.scale(1.0 / r, 1.0 / r)
            cr.set_source_surface(surf, 0, 0)
            cr.get_source().set_filter(cairo.FILTER_BILINEAR)
            cr.paint()
            cr.restore()
            cr.save()
            cr.new_path()
            core.polygon(cr, quad)
            core.src(cr, (0.12, 0.07, 0.03), 0.55 * (1.0 - lam))
            cr.fill()
        else:
            core.src(cr, core.mix(core.shade(base, 0.45), base, lam))
            cr.paint()
        cr.restore()
    # the free edge and the top/bottom silhouette inked lightly
    edge_t = [prj(xs[k], -H / 2, zs[k]) for k in range(N + 1)]
    edge_b = [prj(xs[k], H / 2, zs[k]) for k in range(N + 1)]
    B.detail_lines(cr, [edge_t, edge_b, [edge_t[-1], edge_b[-1]]], 0.5, "#6b4a2a", 0.5, taper=(1.0, 1.0, 1.0))
    return xs, zs


def page_turn_shadow(cr, book, p, view, z_r, z_l):
    """The soft shadow a lifted page casts on the page beneath it (drawn before the page)."""
    W, H = book.pw, book.ph
    prj = _proj(view)
    if p <= 0.0 or p >= 1.0:
        return
    lift = math.sin(math.pi * p)
    side = 1.0 if p < 0.5 else -1.0
    reach = W * (1.0 - abs(math.cos(math.pi * p))) * 0.9
    for k, a in enumerate((0.18, 0.12, 0.07)):
        r = reach * (0.6 + 0.25 * k)
        z = z_r if side > 0 else z_l
        poly = [prj(0.0, -H / 2, z), prj(side * r, -H / 2, z), prj(side * r, H / 2, z), prj(0.0, H / 2, z)]
        cr.new_path()
        core.polygon(cr, poly)
        core.src(cr, (0.12, 0.06, 0.02), a * lift)
        cr.fill()


def _page_texture(book, page, t, side, light, shimmer, detail, res):
    """Render a page into an offscreen surface at `res` px per unit (for a turning page)."""
    W, H = book.pw, book.ph
    res = clamp(res, 0.5, 6.0)
    sw, sh = max(2, int(W * res)), max(2, int(H * res))
    surf = core.new_surface(sw, sh)
    c2 = core.new_context(surf)
    c2.scale(res, res)
    draw_page(c2, page, W, H, t, side, light, shimmer, detail, blank=page is None)
    surf.flush()
    return surf, res


def _blank_page(seed):
    return Page(seed=seed, border=None)


def draw_book(cr, book, x, y, scale=1.0, t=0.0, open=1.0, spread=0, turn=0.0, light=None, view=0.42,
              detail=None, shimmer=None, flutter=6, center_closed=True):
    """Draw the book with its spine's middle at (x, y) on the desk.

    open     0 closed .. 1 open at `spread`: 0-0.45 the cover swings over (a creak), 0.3-1.0 a
             flutter of pages settles on the spread
    spread   which Spread lies open; turn 0..1 turns the page from `spread` to `spread + 1`
    light    the scene light (default STORY_LIGHT); shimmer 0..1 gold catches the candle (default:
             a slow flicker from t)
    view     how far from face-on the desk is seen (rad); center_closed: shift the closed book so it
             stays centred on its anchor (it slides to the spine as it opens)
    Returns a BookRig (page corners and page-local -> caller matrices for camera moves)."""
    light = light or STORY_LIGHT
    dev = scale * B.device_scale(cr)
    if detail is None:
        detail = 2 if dev >= 0.9 else 1 if dev >= 0.5 else 0
    if shimmer is None:
        shimmer = 0.5 + 0.5 * math.sin(t * 2.3) * 0.6 + 0.2 * core.noise1(t * 3.0, 4)
    W, H, ov, bt, T = book.pw, book.ph, book.ov, book.bt, book.block
    prj = _proj(view)
    o = clamp(open)
    cover_u = smooth(clamp(o / 0.45))                 # the cover's swing
    theta = math.pi * core.inout_sine(cover_u)
    flut = clamp((o - 0.3) / 0.7)
    T_l = T * smooth(clamp((o - 0.45) / 0.55))
    T_r = 2.0 * T - T_l
    landed_cover = theta >= math.pi * 0.999
    shift = -(W + ov) * 0.5 * (1.0 - cover_u) if center_closed else 0.0
    rig = BookRig(anchor=(x, y), scale=scale, page_size=(W, H))
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    cr.translate(shift, 0.0)
    # contact shadow on the desk
    sh_w = (W + ov) * (1.0 + cover_u)
    sh_c = prj((W + ov) * 0.5 * (1.0 - cover_u), H * 0.1, 0.0)
    B.contact_shadow(cr, sh_c[0], sh_c[1], sh_w * 0.62, (H + ov) * 0.52 * math.cos(view), alpha=0.4)
    # boards
    _board_top(cr, book, 1, 0.0, prj, light)
    if landed_cover:
        _board_top(cr, book, -1, 0.0, prj, light)
    # page blocks (front edges)
    _block(cr, book, 1, 0.0, T_r, prj, light)
    if landed_cover:
        _block(cr, book, -1, 0.0, T_l, prj, light)
    sp = book.spread(spread)
    nxt = book.spread(spread + 1)
    tr_ = clamp(turn)
    # the open pages
    flutter_n = max(0, int(flutter))
    landed = 0
    fl_list = []
    if flut > 0 and o < 1.0:
        for i in range(flutter_n):
            a0 = i / max(1, flutter_n) * 0.72
            pi_ = clamp((flut - a0) / 0.28)
            fl_list.append(pi_)
            if pi_ >= 1.0:
                landed += 1
    final_landed = o >= 1.0 or (flutter_n and fl_list and fl_list[-1] >= 1.0)
    if landed_cover:
        # left: the endpaper, then landed flutter pages, then the spread's left page
        if final_landed:
            left_page = sp.left if tr_ < 1.0 else nxt.left
        elif landed > 0:
            left_page = _blank_page(book.seed + landed)
        else:
            left_page = "endpaper"
        _open_page(cr, book, -1, T_l, left_page, t, light, view, shimmer, detail, prj, rig)
    if o >= 0.0:
        if final_landed:
            right_page = nxt.right if tr_ > 0.0 else sp.right
        elif flut > 0 and fl_list and fl_list[-1] > 0.0:
            right_page = sp.right
        else:
            right_page = _blank_page(book.seed + 40)
        _open_page(cr, book, 1, T_r, right_page, t, light, view, shimmer, detail, prj, rig)
    # the page turn (spread -> spread + 1)
    if final_landed and 0.0 < tr_ < 1.0:
        page_turn_shadow(cr, book, tr_, view, T_r, T_l)
        res = dev * 1.0
        _turning_page(cr, book, tr_, sp.right, nxt.left, t, light, view, T_r, T_l, shimmer, detail, res)
    # the flutter of pages settling (blank pages, the last one carries the spread's left page)
    if fl_list:
        for i, pi_ in enumerate(fl_list):
            if 0.0 < pi_ < 1.0:
                last = i == len(fl_list) - 1
                if last:
                    page_turn_shadow(cr, book, pi_, view, T_r, T_l)
                    _turning_page(cr, book, pi_, _blank_page(book.seed + 90), sp.left, t, light, view, T_r, T_l,
                                  shimmer, detail, dev, plain=False)
                else:
                    _turning_page(cr, book, pi_, None, None, t, light, view, T_r, T_l, shimmer, detail, dev, plain=True)
    # the front cover, swinging (or closed on top)
    if theta < math.pi * 0.999:
        z_h = lerp(2.0 * T + bt * 0.5, bt * 0.5, cover_u)
        m = _cover_matrix(book, theta, z_h, view)
        if abs(math.cos(theta)) > 0.015:
            cr.save()
            # the board's thickness along its free edge
            CW = W + ov + 0.8
            fe = [prj(CW * math.cos(theta), -H / 2 - ov, z_h + CW * math.sin(theta)),
                  prj(CW * math.cos(theta), H / 2 + ov, z_h + CW * math.sin(theta))]
            off = bt * (1.0 if theta < math.pi / 2 else -1.0)
            core.src(cr, B.palette(light, B.Mat.of(LEATHER)).shadow)
            cr.new_path()
            core.polygon(cr, [fe[0], fe[1], (fe[1][0], fe[1][1] + off * math.cos(view)), (fe[0][0], fe[0][1] + off * math.cos(view))])
            cr.fill()
            cr.transform(m)
            if theta < math.pi / 2:
                _cover_face(cr, book, light, shimmer, detail)
            else:
                cr.translate(CW, 0)
                cr.scale(-1, 1)
                _cover_face(cr, book, light, shimmer, detail, inside=True)
            cr.restore()
    # the spine crease when open
    if landed_cover:
        a, b = prj(0.0, -H / 2, min(T_l, T_r) - 3.0), prj(0.0, H / 2, min(T_l, T_r) - 3.0)
        B.detail_lines(cr, [[a, b]], 1.4, "#2a160c", 0.75, taper=(0.5, 1.0, 0.5))
    m_ = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()
    for side, z in (("left", T_l), ("right", T_r)):
        pm = _page_matrix(book, -1 if side == "left" else 1, z, view)
        full = pm.multiply(m_).multiply(inv)
        rig.page_matrix[side] = full
        rig.pages[side] = [full.transform_point(u, v) for u, v in ((0, 0), (W, 0), (W, H), (0, H))]
    return rig


def _open_page(cr, book, side, z, page, t, light, view, shimmer, detail, prj, rig):
    """A page lying open on its block: curved outline, then its contents drawn with the page's
    affine transform, clipped to the outline (so the vector art stays crisp in close-ups)."""
    poly = _page_outline(book, side, z, prj, book.seed + (1 if side > 0 else 2))
    cr.new_path()
    core.polygon(cr, poly)
    pp = B.Path(cr)
    cr.save()
    pp.add(cr)
    cr.clip()
    cr.transform(_page_matrix(book, side, z, view))
    if page == "endpaper":
        tile, _k = _marble_tile()
        pat = cairo.SurfacePattern(tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        mm = cairo.Matrix()
        mm.scale(2.2, 2.2)
        pat.set_matrix(mm)
        cr.set_source(pat)
        cr.paint()
    else:
        draw_page(cr, page, book.pw, book.ph, t, side, light, shimmer, detail, blank=(page is None))
    cr.restore()
    B.detail_lines(cr, [poly + [poly[0]]], 0.55, "#7a5a3a", 0.55, taper=(1.0, 1.0, 1.0))


# ----------------------------------------------------------------------------------------
# the lectern
# ----------------------------------------------------------------------------------------

@dataclass
class LecternRig:
    desk: tuple = (0.0, 0.0)          # where the book's spine middle goes (caller coords)
    top: tuple = (0.0, 0.0)
    candles: list = field(default_factory=list)   # candle-dish points on the bracket arms
    scale: float = 1.0


OAK = "#6b4528"


def draw_lectern(cr, x, y, scale=1.0, light=None, book=None, height=230.0, view=0.42, candles=True, detail=None):
    """A carved oak lectern: scrolled tripod feet, a tall turned column, a carved capital and a
    slanted desk narrower than the open book (the great book overhangs it; its bottom edge rests
    on the desk's ledge), and two scrolled iron candle arms reaching out past the book's edges.
    (x, y) = the floor under the column; `height` = the spine's middle above the floor (scale-1
    px); `view` must match draw_book's. Static: cache it in an fx.Layer. Returns a LecternRig
    (desk anchor for draw_book, candle dishes for draw_candle)."""
    light = light or STORY_LIGHT
    book = book or Book()
    W, H = book.pw, book.ph
    DW = 2.0 * W * 0.78
    cv = math.cos(view)
    oak = B.Mat.of(OAK, sheen=0.25)
    oak_lt = B.Mat.of(core.tint(OAK, 0.1), sheen=0.3)
    pal = B.palette(light, oak)
    dev = scale * B.device_scale(cr)
    lw = B.line_for(1.6, dev)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    B.contact_shadow(cr, 0.0, 2.0, 100.0, 15.0, alpha=0.42)
    top_y = -height
    yf = top_y + (H / 2.0 + book.ov + 7.5) * cv     # the desk's front edge (the ledge sits on it)
    y_far = top_y - (H / 2.0 - 24.0) * cv          # its far edge, hidden under the book
    # ---- the foot: a block and two scrolled feet (a third foot toward us)
    feet = []
    for sgn in (-1.0, 1.0):
        feet.append([(sgn * 12, -30), (sgn * 36, -20), (sgn * 64, -11), (sgn * 80, -7), (sgn * 84, -1), (sgn * 64, 0),
                     (sgn * 34, -5), (sgn * 10, -9)])
    front_foot = [(-11, -22), (11, -22), (16, 4), (8, 8), (-8, 8), (-16, 4)]
    cr.new_path()
    for f in feet:
        core.smooth_closed(cr, B.offset_closed(f, lw), 0.6)
    core.polygon(cr, B.offset_closed([(-20, -44), (20, -44), (24, 0), (-24, 0)], lw))
    core.src(cr, pal.line)
    cr.fill()
    for f in feet:
        core.smooth_closed(cr, f, 0.6)
    core.polygon(cr, [(-20, -44), (20, -44), (24, 0), (-24, 0)])
    B.shade(cr, B.Path(cr), oak, light, lw, outline=False, size=28, rim=0.6, bounce=0.0)
    for sgn in (-1.0, 1.0):
        cr.new_path()
        core.circle(cr, sgn * 77, -6, 5.0)
        core.src(cr, pal.shadow)
        cr.fill()
        B.detail_lines(cr, [[(sgn * 66, -9), (sgn * 74, -12.5), (sgn * 80, -7)]], 1.0, pal.line, 0.6)
    sh, so = B.smooth_paths(cr, front_foot, lw, 0.6)
    B.shade(cr, sh, oak, light, lw, outline=so, size=16, rim=0.6, bounce=0.0)
    # ---- the turned column: a baluster of rings and a knop
    col_top = yf + 30.0
    span = -44.0 - col_top
    prof = [(0.0, 11.5), (0.04, 14.0), (0.09, 9.5), (0.2, 7.0), (0.38, 8.0), (0.5, 12.5), (0.56, 13.5), (0.62, 12.0),
            (0.74, 7.5), (0.9, 7.0), (0.95, 10.5), (1.0, 12.5)]
    pts_l = [(-r, -44.0 - span * u) for u, r in prof]
    pts_r = [(r, -44.0 - span * u) for u, r in prof][::-1]
    sh, so = B.smooth_paths(cr, pts_l + pts_r, lw, 0.55)
    B.shade(cr, sh, oak, light, lw, outline=so, size=18, rim=0.7, bounce=0.0)
    rings = [[(-r * 0.95, -44.0 - span * u), (0, -44.0 - span * u + 1.8), (r * 0.95, -44.0 - span * u)]
             for u, r in (prof[1], prof[2], prof[6], prof[10])]
    B.detail_lines(cr, rings, 0.9, pal.line, 0.55)
    # ---- iron candle arms scrolling out from the column
    dishes = []
    if candles:
        iron = "#2a2522"
        ay_ = col_top + span * 0.12
        reach = W + book.ov + 30.0
        for sgn in (-1.0, 1.0):
            ex, ey = sgn * reach, yf - 14.0
            ay_ = yf + 16.0                                   # out of the capital, under the desk
            bar = [(sgn * 20.0, ay_), (sgn * (reach - 40.0), ay_ + 2.0), (sgn * (reach - 12.0), ay_ - 4.0),
                   (sgn * (reach - 1.5), ey + 18.0), (ex, ey + 5.0)]
            ink(cr, bar, 5.0, iron, 1.0, (1.0, 1.0, 0.8))
            ink(cr, bar, 1.6, "#6a5a50", 0.5, (0.6, 0.8, 0.4))   # a glint along the top
            curl = [(sgn * (reach - 14.0), ay_ - 2.0), (sgn * (reach - 30.0), ay_ + 10.0),
                    (sgn * (reach - 22.0), ay_ + 20.0), (sgn * (reach - 12.0), ay_ + 14.0)]
            ink(cr, curl, 2.8, iron, 1.0, (1.0, 0.9, 0.5))
            dish = [(ex - 11, ey), (ex + 11, ey), (ex + 7, ey + 4.5), (ex - 7, ey + 4.5)]
            sh, so = B.smooth_paths(cr, dish, lw * 0.8, 0.4)
            B.shade(cr, sh, B.Mat.of(BRASS, sheen=0.8), light, lw * 0.8, outline=so, size=5, rim=0.8, bounce=0.0)
            dishes.append((ex, ey))
    # ---- the carved capital under the desk
    cap = [(-30, yf + 6), (30, yf + 6), (22, yf + 22), (12, yf + 32), (-12, yf + 32), (-22, yf + 22)]
    sh, so = B.smooth_paths(cr, cap, lw, 0.5)
    B.shade(cr, sh, oak, light, lw, outline=so, size=20, rim=0.7, bounce=0.0)
    if detail is None or detail >= 1:
        B.detail_lines(cr, [[(-24, yf + 14), (0, yf + 18), (24, yf + 14)], [(-10, yf + 24), (0, yf + 27), (10, yf + 24)]],
                       0.9, pal.line, 0.5)
        cr.new_path()
        core.circle(cr, 0.0, yf + 20.0, 3.4)
        core.src(cr, pal.shadow)
        cr.fill()
    # ---- the desk: a slab with a moulded front edge and a book ledge
    desk = [(-DW / 2, y_far), (DW / 2, y_far), (DW / 2, yf), (-DW / 2, yf)]
    front = [(-DW / 2, yf), (DW / 2, yf), (DW / 2 - 3, yf + 10), (-DW / 2 + 3, yf + 10)]
    sh, so = B.smooth_paths(cr, front, lw, 0.2)
    B.shade(cr, sh, oak, light, lw, outline=so, size=8, rim=0.7, bounce=0.0)
    B.detail_lines(cr, [[(-DW / 2 + 5, yf + 4.5), (DW / 2 - 5, yf + 4.5)]], 0.8, pal.line, 0.5, taper=(1.0, 1.0, 1.0))
    sh, so = B.smooth_paths(cr, desk, lw, 0.08)
    p2 = B.shade(cr, sh, oak_lt, light, lw, outline=so, size=60, shadow=0.4, rim=0.8, bounce=0.0)
    if detail is None or detail >= 1:
        cr.save()
        sh.add(cr)
        cr.clip()
        grain = [[(-DW / 2 + 6, yy), (0, yy + 1.5), (DW / 2 - 6, yy - 1)]
                 for yy in [y_far + 8.0 + 12.0 * k for k in range(int((yf - y_far - 8.0) / 12.0))]]
        B.detail_lines(cr, grain, 0.6, p2.line, 0.18)
        cr.restore()
    ledge_y = top_y + (H / 2 + book.ov + 1.0) * cv
    ledge = [(-DW / 2 + 4, ledge_y - 3.0), (DW / 2 - 4, ledge_y - 3.0), (DW / 2 - 4, ledge_y + 5.5), (-DW / 2 + 4, ledge_y + 5.5)]
    sh, so = B.smooth_paths(cr, ledge, lw, 0.2)
    B.shade(cr, sh, oak, light, lw, outline=so, size=6, rim=0.8, bounce=0.0)
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    return LecternRig(desk=C((0.0, top_y)), top=C((0.0, top_y - (H / 2.0 + book.ov) * cv)), candles=[C(d) for d in dishes],
                      scale=scale)


# ----------------------------------------------------------------------------------------
# candles
# ----------------------------------------------------------------------------------------

@dataclass
class CandleRig:
    flame: tuple = (0.0, 0.0)         # the flame's heart (put the scene's glow here)
    tip: tuple = (0.0, 0.0)
    flicker: float = 1.0              # 0.8..1.15 brightness right now (scale glows/lights with it)
    scale: float = 1.0


def candle_flicker(t, seed=0):
    """(brightness 0.8..1.15, sway -1..1, stretch 0.85..1.2) of a candle flame at time t."""
    n1 = core.noise1(t * 2.1, seed)
    n2 = core.noise1(t * 7.3 + 3.0, seed + 5)
    gust = max(0.0, core.noise1(t * 0.4, seed + 9) - 0.55) * 2.0
    b = 1.0 + 0.08 * n1 + 0.05 * n2 - 0.12 * gust
    sway = 0.5 * n1 + 0.25 * n2 + 0.9 * gust * math.sin(t * 9.0)
    st = 1.0 + 0.1 * n2 - 0.15 * gust + 0.06 * math.sin(t * 13.0 + seed)
    return b, sway, st


def draw_candle(cr, x, y, scale=1.0, t=0.0, light=None, height=34.0, width=10.0, holder="dish", lit=1.0, seed=0,
                glow=True, drips=3):
    """A beeswax candle with drips in a brass dish (holder "dish"), or a bare pillar ("none");
    (x, y) = the bottom of the holder. The flame flickers (candle_flicker). glow=True adds a small
    additive halo here; put the big room glow in the scene's LightLayer at rig.flame."""
    light = light or STORY_LIGHT
    b, sway, st = candle_flicker(t, seed)
    wax = B.Mat.of("#efe2c2", sss=0.6, line_k=0.55)
    pal = B.palette(light, wax)
    dev = scale * B.device_scale(cr)
    lw = B.line_for(1.2, dev)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    base_y = 0.0
    if holder == "dish":
        dish = [(-13, -1), (13, -1), (10, 3), (-10, 3)]
        sh, so = B.smooth_paths(cr, dish, lw * 0.8, 0.4)
        B.shade(cr, sh, B.Mat.of(BRASS, sheen=0.8), light, lw * 0.8, outline=so, size=4, rim=0.8, bounce=0.0)
        ring = [(9, 0), (16, -1), (19, 3), (15, 6), (11, 4)]
        ink(cr, ring + [ring[0]], 1.6, B.palette(light, B.Mat.of(BRASS)).line, 0.95)
        base_y = -1.0
    w2 = width / 2.0
    body = [(-w2, base_y), (-w2, base_y - height + 2.0), (-w2 * 0.7, base_y - height - 1.0), (w2 * 0.8, base_y - height - 0.6),
            (w2, base_y - height + 2.5), (w2, base_y)]
    sh, so = B.smooth_paths(cr, body, lw, 0.4)
    B.shade(cr, sh, wax, light, lw, outline=so, size=width, rim=0.8, bounce=0.0)
    rng = random.Random(seed)
    if drips:
        ds = []
        for k in range(drips):
            dx = rng.uniform(-w2 * 0.9, w2 * 0.9)
            L = rng.uniform(4.0, height * 0.45)
            ds.append([(dx, base_y - height + 1.0), (dx + rng.uniform(-0.6, 0.6), base_y - height + 1.0 + L)])
        cr.new_path()
        for d in ds:
            core.tapered(cr, d, 2.2, 2.8)
        core.src(cr, core.mix(pal.lit, pal.hi, 0.5))
        cr.fill()
    # the melted rim glows a little from the flame
    cr.new_path()
    core.ellipse(cr, 0.0, base_y - height + 0.6, w2 * 0.8, 1.6)
    core.src(cr, core.mix(pal.hi, "#ffe2a0", 0.5), 0.9)
    cr.fill()
    ink(cr, [(0.0, base_y - height + 0.4), (0.4 * sway, base_y - height - 3.2)], 1.0, "#2a1d14", 1.0)
    fl_x, fl_y = 0.6 * sway, base_y - height - 3.0
    if lit > 0:
        h = 14.0 * st * lit
        tipx = fl_x + 3.0 * sway
        outer = [(fl_x - 3.6, fl_y + 0.5), (fl_x - 3.0, fl_y - h * 0.45), (tipx, fl_y - h), (fl_x + 3.0, fl_y - h * 0.45),
                 (fl_x + 3.6, fl_y + 0.5), (fl_x, fl_y + 2.4)]
        if glow:
            fx.glow(cr, fl_x, fl_y - h * 0.4, 26.0, "#ffb05a", 0.42 * b * lit)
        cr.new_path()
        core.smooth_closed(cr, outer, 0.9)
        core.src(cr, "#ffb347", 0.92 * lit)
        cr.fill()
        inner = [(fl_x - 1.9, fl_y), (fl_x - 1.4, fl_y - h * 0.4), (lerp(fl_x, tipx, 0.6), fl_y - h * 0.75), (fl_x + 1.4, fl_y - h * 0.4),
                 (fl_x + 1.9, fl_y), (fl_x, fl_y + 1.4)]
        cr.new_path()
        core.smooth_closed(cr, inner, 0.9)
        core.src(cr, "#fff3c8", 0.95 * lit)
        cr.fill()
        cr.new_path()
        core.ellipse(cr, fl_x, fl_y + 0.6, 1.5, 1.2)
        core.src(cr, "#6f8cff", 0.55 * lit)
        cr.fill()
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    return CandleRig(flame=C((fl_x, fl_y - 5.0)), tip=C((0.0, base_y - height)), flicker=b * lit, scale=scale)


# ----------------------------------------------------------------------------------------
# the hearth and its fire (the nook's other light)
# ----------------------------------------------------------------------------------------

@dataclass
class HearthRig:
    fire: tuple = (0.0, 0.0)          # where draw_fire goes (the middle of the fire bed)
    mouth: list = field(default_factory=list)   # the opening's outline (caller coords)
    mantel: tuple = (0.0, 0.0)        # middle of the mantel shelf's top (props stand here)
    scale: float = 1.0


@dataclass
class FireRig:
    glow: tuple = (0.0, 0.0)          # the fire's heart: put the room glow here (in the LightLayer)
    top: tuple = (0.0, 0.0)           # the tip of the tallest tongue
    flicker: float = 1.0              # 0.8..1.2 brightness right now (scale the glows with it)
    scale: float = 1.0


def fire_flicker(t, seed=0):
    """Brightness (about 0.8..1.2) of the hearth fire at time t: a slow breathing plus crackle."""
    return 1.0 + 0.10 * core.noise1(t * 1.7, seed + 2) + 0.06 * core.noise1(t * 5.1 + 7.0, seed + 6)


def _stones(cr, x0, y0, x1, y1, seed, rows=(24.0, 32.0), widths=(34.0, 60.0), base="#6a584d", var=0.22,
            mortar="#251b18", gap=2.2):
    """Dressed stones in courses (painted, no outlines) filling a rectangle."""
    rng = random.Random(seed)
    core.src(cr, mortar)
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.fill()
    cr.save()
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.clip()
    y, row = y0, 0
    while y < y1:
        hgt = rng.uniform(*rows)
        x = x0 - rng.random() * widths[0] - (row % 2) * widths[0] * 0.5
        while x < x1:
            w = rng.uniform(*widths)
            tone = core.mix(base, "#2e2420", var * rng.random())
            tone = core.mix(tone, "#8a7464", 0.3 * rng.random())
            pts = [(x + gap + rng.uniform(-1, 1), y + gap + rng.uniform(-1, 1)),
                   (x + w - gap + rng.uniform(-1, 1), y + gap + rng.uniform(-1, 1)),
                   (x + w - gap + rng.uniform(-1, 1), y + hgt - gap + rng.uniform(-1, 1)),
                   (x + gap + rng.uniform(-1, 1), y + hgt - gap + rng.uniform(-1, 1))]
            cr.new_path()
            core.smooth_closed(cr, pts, 0.3)
            core.src(cr, tone)
            cr.fill_preserve()
            cr.set_source(core.linear(0, y, 0, y + hgt, [(0.0, (1.0, 0.88, 0.7, 0.12)), (0.3, (1, 1, 1, 0.0)),
                                                         (0.75, (0, 0, 0, 0.0)), (1.0, (0, 0, 0, 0.25))]))
            cr.fill()
            x += w
        y += hgt
        row += 1
    cr.restore()


def draw_hearth(cr, x, y, scale=1.0, light=None, seed=0, width=300.0, height=300.0, mantel=True):
    """A stone fireplace for the minstrel's nook: dressed-stone jambs, an arched mouth of wedge
    stones, a sooty firebox, a raised hearthstone and an oak mantel shelf. (x, y) = the floor at
    its middle; width x height (scale-1 px) = the stonework (the mantel sits on top). Static:
    cache it in an fx.Layer; draw the living fire (draw_fire at rig.fire) every frame on top."""
    light = light or STORY_LIGHT
    rng = random.Random(seed)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    hw = width / 2.0
    mw, mh = width * 0.56, height * 0.62            # the mouth: width, height to the arch's crown
    mx0, mx1 = -mw / 2.0, mw / 2.0
    spring = -mh + mw / 2.0 * 0.62                  # where the (flattened) arch springs
    # the stonework
    _stones(cr, -hw, -height, hw, -14.0, seed + 1, rows=(26.0, 34.0), widths=(36.0, 64.0))
    # the arched mouth (a flattened arch) and its wedge stones
    def arch(r_pad, n=24):
        pts = []
        for i in range(n + 1):
            a = math.pi + math.pi * i / n
            pts.append((math.cos(a) * (mw / 2.0 + r_pad), spring + math.sin(a) * (mw / 2.0 * 0.62 + r_pad)))
        return pts
    outer = arch(30.0)
    inner = arch(0.0)
    cr.new_path()
    core.polygon(cr, [(mx0 - 30.0, -14.0)] + outer + [(mx1 + 30.0, -14.0)])
    core.src(cr, "#251b18")
    cr.fill()
    nv = 9
    for k in range(nv):
        a0 = math.pi + math.pi * k / nv
        a1 = math.pi + math.pi * (k + 1) / nv
        quad = []
        for a, rp in ((a0 + 0.012, 1.5), (a1 - 0.012, 1.5), (a1 - 0.012, 28.5), (a0 + 0.012, 28.5)):
            quad.append((math.cos(a) * (mw / 2.0 + rp), spring + math.sin(a) * (mw / 2.0 * 0.62 + rp)))
        tone = core.mix("#7a6656", "#3c302a", 0.25 * rng.random())
        if k == nv // 2:
            tone = core.mix(tone, "#8c7866", 0.4)            # the keystone
        cr.new_path()
        core.polygon(cr, quad)
        core.src(cr, tone)
        cr.fill()
    for sgn in (-1.0, 1.0):                                 # the jambs' quoins
        yy = spring
        k = 0
        while yy < -14.0:
            hh = min(-14.0 - yy, 34.0 if k % 2 == 0 else 26.0)
            wd = 30.0 if k % 2 == 0 else 22.0
            xa = sgn * (mw / 2.0 + 1.5)
            xb = sgn * (mw / 2.0 + 1.5 + wd)
            cr.new_path()
            core.rounded_rect(cr, min(xa, xb), yy + 1.5, abs(xb - xa), hh - 3.0, 2.5)
            core.src(cr, core.mix("#76624f", "#3c302a", 0.3 * rng.random()))
            cr.fill()
            yy += hh
            k += 1
    # the firebox: soot-dark, warmer low down where the fire lights it; a faint brick fireback
    cr.new_path()
    core.polygon(cr, [(mx0, -14.0)] + inner + [(mx1, -14.0)])
    mouth = B.Path(cr)
    cr.set_source(core.linear(0, -mh, 0, -14.0, ["#0c0808", "#1d0f0b", "#4a1f10"]))
    cr.fill()
    cr.save()
    mouth.add(cr)
    cr.clip()
    rows = int(mh / 12.0)
    for r in range(rows):
        yb = -14.0 - (r + 1) * 12.0
        off = 11.0 if r % 2 else 0.0
        xb = mx0 - off
        while xb < mx1:
            cr.rectangle(xb + 1.0, yb + 1.0, 20.0, 10.0)
            xb += 22.0
    cr.set_source(core.linear(0, -mh, 0, -14.0, [(0.0, (0.25, 0.12, 0.08, 0.0)), (1.0, (0.55, 0.22, 0.10, 0.35))]))
    cr.fill()
    cr.set_source(core.linear(mx0, 0, mx1, 0, [(0.0, (0, 0, 0, 0.55)), (0.25, (0, 0, 0, 0.0)), (0.75, (0, 0, 0, 0.0)),
                                               (1.0, (0, 0, 0, 0.55))]))
    cr.paint()
    cr.restore()
    # soot climbing the stones above the arch
    cr.save()
    cr.rectangle(-hw, -height, width, height - 14.0)
    cr.clip()
    g = core.radial(0.0, -mh - 10.0, mw * 0.75, [(0.0, (0.05, 0.03, 0.03, 0.55)), (1.0, (0.05, 0.03, 0.03, 0.0))])
    cr.set_source(g)
    cr.paint()
    cr.restore()
    # the hearthstone (raised slab) in front
    slab = [(-hw - 10.0, -14.0), (hw + 10.0, -14.0), (hw + 16.0, 0.0), (-hw - 16.0, 0.0)]
    cr.new_path()
    core.polygon(cr, slab)
    cr.set_source(core.linear(0, -14.0, 0, 0.0, ["#6e5c50", "#3a2e28"]))
    cr.fill()
    core.src(cr, "#8a7464", 0.5)
    cr.rectangle(-hw - 10.0, -14.0, width + 20.0, 2.0)
    cr.fill()
    # the mantel: an oak beam and a shelf
    mantel_pt = (0.0, -height - 22.0)
    if mantel:
        oak = B.Mat.of(OAK, sheen=0.2)
        pal = B.palette(light, oak)
        cr.new_path()
        core.rounded_rect(cr, -hw - 18.0, -height - 22.0, width + 36.0, 12.0, 2.0)
        core.src(cr, pal.lit)
        cr.fill()
        cr.new_path()
        core.rounded_rect(cr, -hw - 6.0, -height - 10.0, width + 12.0, 22.0, 2.0)
        core.src(cr, core.mix(pal.lit, pal.shadow, 0.5))
        cr.fill()
        core.src(cr, pal.shadow, 0.8)
        cr.rectangle(-hw - 6.0, -height + 6.0, width + 12.0, 6.0)
        cr.fill()
        for sgn in (-1.0, 1.0):                          # corbels under the beam's ends
            cr.new_path()
            core.rounded_rect(cr, sgn * (hw - 14.0) - 11.0, -height + 12.0, 22.0, 26.0, 4.0)
            core.src(cr, core.mix(pal.lit, pal.shadow, 0.35))
            cr.fill()
            core.src(cr, pal.shadow, 0.9)
            cr.rectangle(sgn * (hw - 14.0) - 11.0, -height + 30.0, 22.0, 8.0)
            cr.fill()
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    return HearthRig(fire=C((0.0, -26.0)), mouth=[C(p) for p in [(mx0, -14.0)] + inner + [(mx1, -14.0)]],
                     mantel=C(mantel_pt), scale=scale)


def _tongue(cr, bx, by, w, h, sway, curl=0.0):
    """One licking tongue of flame: a fat round body low down, flanks that sweep in (concave)
    to a thin leaning tip -- the S of a real flame, never an almond."""
    tx, ty = bx + sway, by - h
    c = curl * w
    cr.move_to(bx - w * 0.5, by)
    cr.curve_to(bx - w * 0.92, by - h * 0.24, bx - w * 0.30 + sway * 0.15 - c, by - h * 0.62, tx, ty)
    cr.curve_to(bx + w * 0.22 + sway * 0.35 + c, by - h * 0.56, bx + w * 0.92, by - h * 0.26, bx + w * 0.5, by)
    cr.curve_to(bx + w * 0.4, by + w * 0.36, bx - w * 0.4, by + w * 0.36, bx - w * 0.5, by)
    cr.close_path()


# (color, alpha, tongues, width, height, spread): deep red outside -> a white heart
_FIRE_LAYERS = (("#b52f19", 0.94, 5, 56.0, 132.0, 92.0), ("#ef641c", 0.96, 4, 50.0, 110.0, 70.0),
                ("#ffa233", 0.96, 3, 44.0, 82.0, 50.0), ("#ffd77e", 0.96, 3, 32.0, 54.0, 30.0),
                ("#fff4d2", 0.92, 1, 26.0, 30.0, 0.0))


def draw_fire(cr, x, y, scale=1.0, t=0.0, seed=0, logs=True, intensity=1.0, embers=True):
    """The living hearth fire: tongues of flame in nested layers (deep red -> orange -> gold ->
    white heart), each licking with its own noise, wisps breaking off the tips, split logs with
    glowing cracks, and rising sparks. (x, y) = the middle of the fire bed (HearthRig.fire).
    Deterministic in t. ~1 ms. Put the room glow (fx.glow, ~6x the fire's width) in the
    LightLayer at rig.glow, scaled by rig.flicker."""
    fl = fire_flicker(t, seed) * intensity
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    fx.glow(cr, 0.0, -36.0, 120.0, "#ff7a2a", 0.45 * fl)
    top = (0.0, 0.0)
    best = 0.0

    def layer(li, front=False):
        nonlocal top, best
        col, al, n, w, h, spread = _FIRE_LAYERS[li]
        if front:
            n, h, w, spread = 2, h * 0.3, w * 0.55, spread * 1.3
        for i in range(n):
            u = (i / (n - 1) - 0.5) if n > 1 else 0.0
            jit = core.noise1(i * 3.7 + li * 1.3, seed + 11) * 6.0
            bx = u * spread + jit
            nz = core.noise1(t * (2.0 + 0.3 * li) + i * 1.7 + li * 3.1, seed + i)
            hk = (1.0 - 0.9 * u * u) * (0.78 + 0.22 * nz + 0.1 * math.sin(t * (6.0 + i) + i * 2.1 + li)) * fl
            hh = h * max(0.25, hk)
            sw = (9.0 * core.noise1(t * 1.3 + i * 0.9 + li, seed + 3) + 4.0 * math.sin(t * 4.3 + i * 1.3 + li * 0.7)
                  - u * 10.0) * (hh / 100.0 + 0.3)
            cr.new_path()
            _tongue(cr, bx, 0.0, w * (0.85 + 0.15 * nz), hh, sw, 0.12 * math.sin(t * 3.1 + i + li))
            core.src(cr, col, al)
            cr.fill()
            if hh > best:
                best, top = hh, (bx + sw, -hh)

    for li in range(len(_FIRE_LAYERS)):
        layer(li)
    # wisps breaking off the tips and rising away
    for k in range(4):
        ph = (t * 1.25 + k / 4.0 + 0.13 * seed) % 1.0
        wx = (core.noise1(k * 5.3 + math.floor(t * 1.25 + k / 4.0), seed + 21)) * 34.0
        wy = -70.0 - ph * 70.0
        ws = (1.0 - ph) * 9.0
        cr.new_path()
        _tongue(cr, wx + 6.0 * math.sin(t * 5.0 + k), wy, ws, ws * 2.4, 2.0 * math.sin(t * 7.0 + k))
        core.src(cr, "#ff8a2a", 0.85 * (1.0 - ph) * fl)
        cr.fill()
    if logs:
        bark, cut, char = "#3a2416", "#9a6a40", "#1e140e"
        for (lx, ly, lw_, ang) in ((-26.0, -6.0, 104.0, 0.20), (26.0, -4.0, 100.0, -0.22), (0.0, 6.0, 120.0, 0.03)):
            cr.save()
            cr.translate(lx, ly)
            cr.rotate(ang)
            cr.new_path()
            core.rounded_rect(cr, -lw_ / 2.0, -9.0, lw_, 18.0, 8.0)
            cr.set_source(core.linear(0, -9.0, 0, 9.0, [(0.0, core.mix(bark, "#ff9a4a", 0.35)), (0.35, bark),
                                                         (1.0, char)]))
            cr.fill()
            for sgn in (-1.0, 1.0):                     # the sawn ends with their rings
                cr.new_path()
                core.ellipse(cr, sgn * (lw_ / 2.0 - 3.0), 0.0, 4.5, 8.5)
                core.src(cr, cut)
                cr.fill()
                cr.new_path()
                core.ellipse(cr, sgn * (lw_ / 2.0 - 3.0), 0.0, 2.2, 4.4)
                core.src(cr, core.mix(cut, char, 0.4), 0.8)
                cr.set_line_width(0.8)
                cr.stroke()
            # glowing cracks along the underside, pulsing
            for c in range(3):
                cx0 = -lw_ * 0.32 + c * lw_ * 0.3
                pul = 0.55 + 0.45 * math.sin(t * (2.0 + c) + c * 1.7 + lx)
                core.src(cr, "#ff8a30", 0.75 * pul * fl)
                core.tapered(cr, [(cx0, 4.0), (cx0 + 9.0, 5.5), (cx0 + 17.0, 4.5)], 1.6, 0.4)
                cr.fill()
            cr.restore()
        # small flames licking up over the front log, an ember bed glowing beneath
        for li in (1, 2):
            cr.save()
            cr.translate(0.0, -3.0)
            layer(li, front=True)
            cr.restore()
        cr.new_path()
        core.ellipse(cr, 0.0, 14.0, 62.0, 6.0)
        cr.set_source(core.linear(-62.0, 0, 62.0, 0, [(0.0, (1.0, 0.4, 0.1, 0.0)), (0.5, (1.0, 0.55, 0.2, 0.6 * fl)),
                                                      (1.0, (1.0, 0.4, 0.1, 0.0))]))
        cr.fill()
    if embers:
        fx.embers(cr, t, 0.0, -40.0, t0=0.0, n=12, life=2.0, spread=50.0, rise=150.0, color="#ff9a3c", hot="#fff1b8",
                  size=1.6, seed=seed + 3, burst=0.0, scale=1.0, wind=8.0)
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    return FireRig(glow=C((0.0, -40.0)), top=C(top), flicker=fl, scale=scale)
