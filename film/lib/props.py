"""props.py -- THE PROPS KIT: every recurring object in the film, in the house style.

    from film.lib import props as P
    from film.lib import characters as ch
    L = ch.LIGHTS["street_night"]
    pose = ch.DragonPose(facing=1, walk=1, phase=ph,
                         near=ch.Arm("hand_to_ear", hold=P.stone_hold(L, "pulsing", amp, t)),
                         far=ch.Arm("carry_bag", hold=P.bag_hold(L, swing=0.1 * math.sin(ph * math.tau))))
    rig = ch.draw_dragon(cr, x, ground_y, 0.8, pose, L, t)
    P.stone_glow(cr, rig.hand_near.x, rig.hand_near.y, 0.8, P.stone_level("pulsing", amp, t), t)

Conventions (STYLE.md applies throughout):
  * Units are px at scale 1.0 = the cast's scale (the dragon stands 520 px tall), y down, angles
    in radians. Every draw call is `draw_<prop>(cr, x, y, scale=1.0, light=None, t=0.0, ...,
    detail=None)`; each docstring names its ANCHOR and its size at scale 1.0.
  * Props a character touches (stone, bag, note, remedies, book, bread, stamp, tankard, benches,
    stool, till, plaque) get the dilated-fill outline and `B.shade` with the scene light. Set
    dressing (shelves, tables, lantern strings, wisp lamps, lantern posts, drums, hanging signs)
    gets no outline: painterly tones only, and it can be cached in an `fx.Layer`.
  * `light` is a `B.Light` (default LIGHTS["neutral"]). Pass the scene's preset.
  * Level of detail from the on-screen size like the cast: 2 at >= 0.9, 1 at >= 0.55, else 0.
  * `*_hold(...)` returns a hold callback for any character's hand (`Arm(..., hold=cb)`). Its
    frame is the grip point, +x along the fingers, 1 unit = 1 px at scale 1.0 of the holder.
  * Light that falls on the world (lamp halos, pools, the stone's glow on a face) comes from the
    `*_light(lc, ...)` helpers: draw them into the scene's `fx.LightLayer`.
  * Deterministic: everything animated is a pure function of `t` (and a seed).
"""

import functools
import math
import subprocess
from dataclasses import dataclass, field

import cairocffi as cairo

from . import core, fx
from .core import clamp, lerp, smooth, TAU
from .characters import base as B
from .characters.base import Mat, Path

__all__ = [
    # hand props
    "STONE_W", "STONE_H", "draw_speaking_stone", "stone_level", "stone_hold", "stone_glow", "stone_light",
    "BAG_W", "BAG_H", "draw_apothecary_bag", "bag_hold",
    "NOTE_W", "NOTE_H", "draw_note", "note_hold",
    "REMEDIES", "draw_remedy", "draw_sleep_draught", "draw_vitamins", "draw_calm_candle", "remedy_hold",
    "candle_glow", "pile_layout",
    "BOOK_W", "BOOK_H", "draw_coloring_book", "book_hold",
    "LOAF", "draw_bread", "bread_hold", "draw_crumbs",
    "draw_stamp", "stamp_hold", "draw_smile_mark", "smile_stamp",
    # furniture and set
    "draw_till", "BENCH_SEAT_H", "BENCH_DEPTH", "BENCH_LEN", "BenchRig", "draw_garden_bench",
    "STOOL_SEAT_H", "draw_stool", "draw_washhouse_bench",
    "draw_lantern_post", "lantern_light", "draw_tumbling_drum", "drum_body", "drum_porthole", "drum_light",
    "draw_plaque", "draw_hanging_sign", "sign_light",
    "draw_lantern_string", "lantern_string_light",
    "draw_shelves", "draw_tankard", "tankard_hold", "draw_tavern_table",
    "draw_wisp_lamp", "wisp_light", "draw_hourglass", "draw_music_note",
    "PropRig", "PROP_COLORS", "prop_mats", "FONTS",
]


# ----------------------------------------------------------------------------------------
# colors, materials, fonts
# ----------------------------------------------------------------------------------------

PROP_COLORS = {
    # the speaking stone: cold slate with arcane cyan runes (the city hands him stones)
    "stone": "#5B6166", "stone_dk": "#3A3F44", "rune": "#5FE0FF", "rune_hot": "#DFFBFF",
    # paper, parchment and ink
    "paper": "#F1ECDF", "parchment": "#EBDDB8", "parchment_dk": "#CFB888", "ink": "#33261C",
    "apoth_green": "#3E9A5C", "twine": "#B08A5A",
    # remedies
    "blue_glass": "#3563B0", "draught": "#2A4FA0", "cork": "#B08455", "wax_seal": "#2B3A78",
    "jar_glass": "#A9D8C8", "berry_a": "#D6F27A", "berry_b": "#C7A6FF", "berry_c": "#9FF0D8",
    "linen": "#E8DFC8", "tumbler": "#C9D8E8", "wax": "#B9A3D6", "flame_cool": "#D8D0FF",
    "flame_warm": "#FFB347",
    # the coloring book
    "book_cover": "#E9DCB8", "book_spine": "#5A3A5A", "rose_ink": "#B0506A", "teal_ink": "#2F7F86",
    "gold_ink": "#B8913F", "page": "#F4ECD8", "line_art": "#4A3C46",
    # bread (the gnome's loaf colours: one loaf in the whole film)
    "crust": "#C47A36", "crust_hi": "#EDBF73", "crust_dk": "#8A4E22", "crumb": "#F2DFB4",
    # the SMILE stamp
    "stamp_wood": "#8A5A34", "stamp_die": "#5A3A3A", "smile_ink": "#F2559A",
    # metals and woods
    "brass": "#B8913F", "brass_lt": "#F2DC98", "brass_dk": "#5A4520", "iron": "#2E3236",
    "iron_hi": "#5C646C", "oak": "#8A5F3A", "oak_lt": "#B07E4E", "oak_dk": "#5E3F24",
    "pewter": "#8E979C", "ale": "#C88A2E", "foam": "#F4EBD8", "ivory": "#EDE3C8",
    # lights
    "candle": "#FFD27A", "candle_hot": "#FFF4CF", "wisp": "#4DFFC4", "wisp_core": "#E6FFF7",
}

_MATS = {}


def prop_mats():
    """Materials (base.Mat) for the props, keyed like PROP_COLORS (cached)."""
    if not _MATS:
        C = PROP_COLORS
        _MATS.update({
            "stone": Mat.of(C["stone"], sheen=0.3, shadow_k=1.1, line_k=0.5),
            "paper": Mat.of(C["paper"], shadow_k=0.82, line_k=0.5),
            "parchment": Mat.of(C["parchment"], shadow_k=0.85, line_k=0.5),
            "blue_glass": Mat.of(C["blue_glass"], sheen=0.6, sss=0.3),
            "jar_glass": Mat.of(C["jar_glass"], sheen=0.6, shadow_k=0.85, line_k=0.45),
            "tumbler": Mat.of(C["tumbler"], sheen=0.6, shadow_k=0.85, line_k=0.45),
            "cork": Mat.of(C["cork"], line_k=0.5),
            "linen": Mat.of(C["linen"], shadow_k=0.85, line_k=0.5),
            "wax": Mat.of(C["wax"], sss=0.5, shadow_k=0.9),
            "book_cover": Mat.of(C["book_cover"], shadow_k=0.85, line_k=0.5),
            "book_spine": Mat.of(C["book_spine"], line_k=0.55),
            "page": Mat.of(C["page"], shadow_k=0.8, line_k=0.5),
            "crust": Mat.of(C["crust"], sheen=0.25, sss=0.2),
            "crust_hi": Mat.of(C["crust_hi"]),
            "crumb": Mat.of(C["crumb"], sss=0.55, shadow_k=0.85, line_k=0.5),
            "stamp_wood": Mat.of(C["stamp_wood"], sheen=0.2),
            "stamp_die": Mat.of(C["stamp_die"]),
            "brass": Mat.of(C["brass"], sheen=0.7),
            "iron": Mat.of(C["iron"], sheen=0.3, line_k=0.7),
            "oak": Mat.of(C["oak"], sheen=0.15),
            "oak_dk": Mat.of(C["oak_dk"]),
            "pewter": Mat.of(C["pewter"], sheen=0.6),
            "ivory": Mat.of(C["ivory"], shadow_k=0.85),
            "green_paint": Mat.of("#2F5A4A", sheen=0.1),
        })
    return _MATS


@functools.lru_cache(maxsize=16)
def _font_ok(name):
    try:
        out = subprocess.run(["fc-list", ":family=" + name, "family"], capture_output=True, text=True, timeout=5)
        return bool(out.stdout.strip())
    except Exception:
        return False


@functools.lru_cache(maxsize=1)
def _fonts():
    return {
        "label": "IM FELL English SC" if _font_ok("IM FELL English SC") else core.SERIF,
        "text": "IM FELL English" if _font_ok("IM FELL English") else core.SERIF,
        "sign": "Uncial Antiqua" if _font_ok("Uncial Antiqua") else core.SERIF,
        "hand": core.HAND,
    }


class _FontNames:
    """FONTS.label (storybook small caps), FONTS.text (storybook serif), FONTS.sign (uncial),
    FONTS.hand (handwriting): the period-correct lettering of every in-world label and sign."""
    label = property(lambda self: _fonts()["label"])
    text = property(lambda self: _fonts()["text"])
    sign = property(lambda self: _fonts()["sign"])
    hand = property(lambda self: _fonts()["hand"])


FONTS = _FontNames()


# ----------------------------------------------------------------------------------------
# shared machinery: per-draw context, path builders, rigs
# ----------------------------------------------------------------------------------------

class PropRig:
    """Attach points returned by a prop, in the CALLER's coordinates (attribute access)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return "PropRig(" + ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items()) + ")"


class _Ctx:
    """Per-draw context: enters the prop's local frame (translate, rotate, scale), picks the
    level of detail and the house line weight from the on-screen size, caches palettes and maps
    local points back to the caller's coordinates."""

    def __init__(self, cr, x, y, scale=1.0, angle=0.0, light=None, detail=None, line=1.0):
        self.cr = cr
        cr.save()
        cr.translate(x, y)
        if angle:
            cr.rotate(angle)
        if scale != 1.0:
            cr.scale(scale, scale)
        self.local = cr.get_matrix()
        dev = B.device_scale(cr)
        self.dev = dev
        self.detail = detail if detail is not None else (2 if dev >= 0.9 else 1 if dev >= 0.55 else 0)
        self.lw = max(B.LINE * line, B.MIN_LINE_PX / max(dev, 1e-6))
        self.light = light or B.LIGHTS["neutral"]
        self.M = prop_mats()
        self.pal = {}
        self._inv = None

    def P(self, mat):
        if isinstance(mat, str):
            mat = self.M[mat]
        p = self.pal.get(mat)
        if p is None:
            p = self.pal[mat] = B.palette(self.light, mat)
        return p

    def shade(self, path, mat, size, outline=None, **kw):
        if isinstance(mat, str):
            mat = self.M[mat]
        kw.setdefault("bounce", 0.0)
        return B.shade(self.cr, path, mat, self.light, self.lw, outline=outline if outline is not None else False,
                       size=size, **kw)

    def end(self):
        self.cr.restore()
        inv = self.cr.get_matrix()
        inv.invert()
        self._inv = inv

    def C(self, p):
        """Local point -> caller coordinates (call after end())."""
        dx, dy = self.local.transform_point(p[0], p[1])
        return self._inv.transform_point(dx, dy)


def _rrect_paths(cr, x, y, w, h, r, lw):
    """Rounded rectangle + its dilated outline (the house outline is a filled offset copy)."""
    cr.new_path()
    core.rounded_rect(cr, x, y, w, h, r)
    shape = Path(cr)
    core.rounded_rect(cr, x - lw, y - lw, w + 2 * lw, h + 2 * lw, r + lw if isinstance(r, (int, float)) else
                      tuple(v + lw for v in r))
    return shape, Path(cr)


def _poly_paths(cr, pts, lw, smooth_t=None):
    """Polygon (or smooth closed curve when smooth_t is given) + its dilated outline."""
    if smooth_t is not None:
        return B.smooth_paths(cr, pts, lw, smooth_t)
    cr.new_path()
    core.polygon(cr, pts)
    shape = Path(cr)
    core.polygon(cr, B.offset_closed(pts, lw))
    return shape, Path(cr)


def _outline_fill(cr, outlines, color):
    """Fill several dilated outlines at once (one union silhouette line)."""
    B.fill_outlines(cr, outlines, color)


def _ellipse_pts(cx, cy, rx, ry, n=24, a0=0.0, a1=TAU, angle=0.0):
    ca, sa = math.cos(angle), math.sin(angle)
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n if a1 - a0 >= TAU - 1e-9 else n - 1)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def _fit(cr, s, size, family, maxw, spacing=0.0, italic=False):
    """The largest font size <= size at which s fits in maxw."""
    if maxw is None:
        return size
    w = core.measure(cr, s, size, family, False, italic, spacing)[0]
    return size if w <= maxw else size * maxw / max(w, 1e-6)


def _label(cr, s, x, y, size, color, family=None, alpha=1.0, spacing=0.0, italic=False, maxw=None):
    """Centred single-line label, vertically centred on the capital height; shrinks to maxw."""
    family = family or FONTS.label
    size = _fit(cr, s, size, family, maxw, spacing, italic)
    core.text(cr, s, x, y, size, family, color, align="center", valign="cap",
              spacing=spacing, italic=italic, alpha_=alpha)


def _add(cr, color, alpha=None):
    """Additive solid source (glows that live in the frame, not in the LightLayer)."""
    cr.set_operator(cairo.OPERATOR_ADD)
    core.src(cr, color, alpha)


# ========================================================================================
# 1. THE SPEAKING STONE (S3 "phone")
# ========================================================================================

STONE_W, STONE_H = 70.0, 34.0        # long axis along +x (held to the ear: +x points up the fingers)


@functools.lru_cache(maxsize=4)
def _stone_outline(n=30):
    """A smooth river pebble: a touch egg-shaped (fuller toward -x), flattened sides and two
    gentle irregular swellings so it reads as a found stone, not a made object."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        c, s = math.cos(a), math.sin(a)
        rx = STONE_W * 0.5 * (1.0 - 0.03 * c)
        ry = STONE_H * 0.5 * (1.0 - 0.10 * c) * (1.0 + 0.05 * math.sin(2 * a + 0.7) + 0.03 * math.sin(3 * a))
        pts.append((rx * math.copysign(abs(c) ** 0.84, c), ry * math.copysign(abs(s) ** 0.8, s)))
    return tuple(pts)


# Cistercian numerals: the medieval monks' digits, a stave with ticks -- period-true "runes"
# that are also real numbers (key k shows the numeral k). Strokes in a unit quadrant (0..1).
_CIST = {1: [((0, 0), (1, 0))], 2: [((0, 1), (1, 1))], 3: [((0, 0), (1, 1))], 4: [((0, 1), (1, 0))],
         5: [((0, 0), (1, 0)), ((0, 1), (1, 0))], 6: [((1, 0), (1, 1))],
         7: [((0, 0), (1, 0)), ((1, 0), (1, 1))], 8: [((0, 1), (1, 1)), ((1, 0), (1, 1))],
         9: [((0, 0), (1, 0)), ((0, 1), (1, 1)), ((1, 0), (1, 1))]}

# a few Elder Futhark-like glyphs (stroke lists in a unit box, y down) for the rune band
_RUNES = [
    [((0.5, 0), (0.5, 1)), ((0.5, 0.2), (0.95, 0.0)), ((0.5, 0.45), (0.95, 0.25))],          # fehu
    [((0.5, 0), (0.5, 1)), ((0.5, 0), (0.0, 0.3)), ((0.5, 0), (1.0, 0.3))],                  # tiwaz
    [((0.1, 0), (0.9, 1)), ((0.9, 0), (0.1, 1))],                                          # gebo
    [((0.5, 0), (0.5, 1)), ((0.5, 0.45), (0.1, 0.1)), ((0.5, 0.45), (0.9, 0.1))],              # algiz
    [((0.3, 0), (0.3, 1)), ((0.3, 0.1), (0.85, 0.45)), ((0.85, 0.45), (0.3, 0.75))],          # thurisaz
    [((0.5, 0), (0.5, 1))],                                                                # isa
    [((0.2, 0), (0.2, 1)), ((0.8, 0), (0.8, 1)), ((0.2, 0.3), (0.8, 0.55))],                  # hagalaz
    [((0.2, 1), (0.5, 0)), ((0.5, 0), (0.8, 1)), ((0.35, 0.55), (0.65, 0.55))],               # (a spear)
]


def _cistercian(k, cx, cy, h):
    """Stroke list (point pairs) of Cistercian numeral k (1..9) centred at (cx, cy), height h."""
    top = cy - h * 0.5
    q = h * 0.42
    x0 = cx - q * 0.35
    strokes = [[(x0, top), (x0, cy + h * 0.5)]]
    for (a, b) in _CIST.get(k, []):
        strokes.append([(x0 + a[0] * q, top + a[1] * q), (x0 + b[0] * q, top + b[1] * q)])
    return strokes


def _rune_strokes(k, cx, cy, h, ang=0.0):
    """Strokes of rune k (see _RUNES) centred at (cx, cy), height h, rotated by ang."""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for (a, b) in _RUNES[k % len(_RUNES)]:
        seg = []
        for (u, v) in (a, b):
            px, py = (u - 0.5) * h * 0.6, (v - 0.5) * h
            seg.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
        out.append(seg)
    return out


def stone_level(state="idle", amp=0.0, t=0.0):
    """Glow level 0..1 of the stone. state: "off", "idle" (a slow faint breathing), "active"
    (lit, a gentle shimmer), "pulsing" (follows the voice: amp = timeline.talk(3, t, "PHONE")),
    or a number (used as is)."""
    if isinstance(state, (int, float)):
        return clamp(float(state))
    if state == "off":
        return 0.0
    if state == "idle":
        return 0.16 + 0.07 * (0.5 + 0.5 * math.sin(t * 1.3))
    if state == "active":
        return 0.72 + 0.06 * core.noise1(t * 5.0, 11)
    if state == "pulsing":
        return clamp(0.34 + 0.66 * clamp(amp) + 0.05 * core.noise1(t * 9.0, 12))
    return 0.2


def draw_speaking_stone(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, state="idle", amp=0.0,
                        pressed=None, face="front", detail=None):
    """The speaking stone: a smooth palm-sized slate pebble. Front: nine carved rune keys in a
    keypad grid (Cistercian numerals 1-9: real medieval digits that look like runes) and a spiral
    "mouth" at its +x end that pulses with the voice. Back: one big carved spiral. Both: a band
    of small runes round the edge, glowing cold cyan when it is awake.

    Anchor (x, y) = the stone's centre; size STONE_W x STONE_H = 70 x 34 at scale 1.0, long axis
    along +x (rotated by `angle`). state/amp: see stone_level(). pressed = key 1..9 shown lit.
    face: "front" (keys) or "back" (what shows round his hand when it is held to the ear).
    Returns PropRig(center, mouth, level, glow_r)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    lvl = stone_level(state, amp, t)
    C = PROP_COLORS
    pts = list(_stone_outline())
    sh, so = B.smooth_paths(cr, pts, q.lw, 0.9)
    p = q.shade(sh, "stone", STONE_H * 0.9, outline=so)
    groove = core.mix(p.shadow, p.line, 0.45)                 # carved strokes (unlit)
    glow = core.mix(groove, C["rune"], 0.15 + 0.85 * lvl)      # carved strokes lit from within
    if q.detail >= 2:                                         # mottling: paler and darker flecks
        core.src(cr, p.hi, 0.22)
        for i in range(8):
            core.circle(cr, (core.hash01(i, 3) - 0.5) * 54, (core.hash01(i, 4) - 0.5) * 22, 0.7 + 1.1 * core.hash01(i, 5))
        cr.fill()
        core.src(cr, p.shadow, 0.35)
        for i in range(6):
            core.circle(cr, (core.hash01(i, 6) - 0.5) * 50, (core.hash01(i, 7) - 0.5) * 20, 0.6 + 0.9 * core.hash01(i, 8))
        cr.fill()
    # the rune band: small glyphs on an inner ring (they show at the ends when it is held)
    if q.detail >= 1:
        band = []
        ring = B.offset_closed(pts, -5.2)
        idx = [2, 6, 9, 13, 17, 21, 24, 28] if face == "front" else [1, 4, 8, 11, 16, 19, 23, 26]
        for k, i in enumerate(idx):
            px, py = ring[i % len(ring)]
            qx, qy = ring[(i + 1) % len(ring)]
            band += _rune_strokes(k + (3 if face == "back" else 0), px, py, 5.6, math.atan2(qy - py, qx - px))
        B.detail_lines(cr, band, 1.5, groove, 0.7, taper=(0.8, 1.0, 0.8))
        B.detail_lines(cr, band, 0.9, glow, 0.25 + 0.75 * lvl, taper=(0.8, 1.0, 0.8))
    if face == "front":
        # nine carved key dimples + numeral glyphs (keypad layout: 1 2 3 / 4 5 6 / 7 8 9)
        kx, ky, kr = 11.0, 8.2, 3.6
        cr.new_path()
        for r in range(3):
            for c in range(3):
                core.circle(cr, -7.0 + (c - 1) * kx, (r - 1) * ky, kr + 0.7)
        core.src(cr, p.line, 0.5)
        cr.fill()
        cr.new_path()
        for r in range(3):
            for c in range(3):
                core.circle(cr, -7.0 + (c - 1) * kx + 0.35, (r - 1) * ky + 0.45, kr)
        core.src(cr, core.mix(p.shadow, p.lit, 0.35))
        cr.fill()
        if q.detail >= 1:
            strokes, hot_strokes = [], []
            for r in range(3):
                for c in range(3):
                    k = r * 3 + c + 1
                    s_ = _cistercian(k, -7.0 + (c - 1) * kx + 0.4, (r - 1) * ky + 0.3, kr * 1.45)
                    (hot_strokes if pressed == k else strokes).extend(s_)
            B.detail_lines(cr, strokes, 1.25, glow, 0.6 + 0.4 * lvl, taper=(0.8, 1.0, 0.8))
            if hot_strokes:
                B.detail_lines(cr, hot_strokes, 1.4, C["rune_hot"], 1.0, taper=(0.8, 1.0, 0.8))
        if pressed:
            r, c = divmod(int(pressed) - 1, 3)
            fx.glow(cr, -7.0 + (c - 1) * kx, (r - 1) * ky, 11.0, C["rune"], 0.95)
    # the spiral mouth: where the voice comes out, pulsing with it
    mx = 24.0 if face == "front" else 0.0
    mr = 5.0 if face == "front" else 10.0
    if q.detail >= 1:
        spiral = [(mx + math.cos(a) * mr * (0.15 + 0.85 * a / (2.6 * math.pi)),
                   math.sin(a) * mr * (0.15 + 0.85 * a / (2.6 * math.pi))) for a in
                  [k * 2.6 * math.pi / 24 for k in range(25)]]
        B.detail_lines(cr, [spiral], 1.9 if face == "front" else 2.4, groove, 0.75, taper=(0.4, 1.0, 0.8))
        B.detail_lines(cr, [spiral], 1.0 if face == "front" else 1.3, glow, 0.2 + 0.8 * lvl, taper=(0.4, 1.0, 0.8))
    if lvl > 0.05:
        fx.glow(cr, mx, 0.0, mr * 2.4, C["rune"], 0.5 * lvl)
    B.sheen(cr, -13.0, -8.0, 11.0, 3.2, angle=-0.12, alpha=0.22)
    q.end()
    return PropRig(center=q.C((0.0, 0.0)), mouth=q.C((mx, 0.0)), level=lvl, glow_r=46.0 * scale)


def stone_hold(light=None, state="idle", amp=0.0, t=0.0, pressed=None, face="back"):
    """Hold callback for the dragon's `hand_to_ear` (drawn BEHIND his hand, +x up the fingers;
    the stone's ends and glow show past the palm). Draw the glow with stone_glow() after him."""
    def cb(cr, f):
        draw_speaking_stone(cr, 4.0, 0.0, 1.0, light, t, 0.0, state, amp, pressed, face)
    return cb


def stone_glow(cr, x, y, scale=1.0, level=0.5, t=0.0, color=None, motes=True):
    """The stone's cold light on and around the hand: a soft cyan halo plus a few rune motes
    drifting up. Draw it AFTER the character, at rig.hand_near (x, y). level from stone_level()."""
    if level <= 0.01:
        return
    c = color or PROP_COLORS["rune"]
    fx.glow(cr, x, y, 46 * scale * (0.7 + 0.3 * level), c, 0.42 * level)
    fx.glow(cr, x, y, 16 * scale, PROP_COLORS["rune_hot"], 0.25 * level)
    if motes:
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        for i in range(5):
            life = 1.6 + 0.6 * core.hash01(i, 71)
            u = ((t + core.hash01(i, 72) * life) % life) / life
            mx = x + (core.hash01(i, 73) - 0.5) * 40 * scale + 6 * scale * math.sin(t * 2.0 + i)
            my = y - u * 60 * scale
            a = level * math.sin(math.pi * u) * 0.8
            core.src(cr, PROP_COLORS["rune_hot"], a)
            core.circle(cr, mx, my, max(0.6, 1.4 * scale * (1.0 - 0.5 * u)))
            cr.fill()
        cr.restore()


def stone_light(lc, x, y, scale=1.0, level=0.5):
    """The stone's spill for the scene's LightLayer: a wide cold halo that tints his face."""
    if level > 0.01:
        fx.glow(lc, x, y, 170 * scale, PROP_COLORS["rune"], 0.22 * level)


# ========================================================================================
# 2. THE APOTHECARY BAG (S3 in his far hand; the coloring book comes out of it in S6)
# ========================================================================================

BAG_W, BAG_H = 64.0, 100.0           # the grip (the tied neck) is 14 below the top of the paper ruff


def draw_apothecary_bag(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, state="tied", swing=0.0,
                        damp=0.0, detail=None):
    """The apothecary's sack: stiff white paper gathered at the neck and tied with twine, a
    green cross block-printed on its belly, bulging a little over the bottles inside.

    Anchor (x, y) = the grip point on the tied neck; the sack hangs down along +y (rotate with
    `angle`; `swing` adds a pendulum angle about the grip). Size BAG_W x BAG_H = 64 x 100 at
    scale 1.0 (the crumpled paper ruff rises 14 above the grip, the bottom is 86 below it).
    state "tied" (as carried) or "open" (untied, its mouth open: the coloring book and the
    SLEEP DRAUGHT peek out -- S6). damp 0..1 greys and spots it (S3 rain).
    Returns PropRig(grip, bottom, mouth)."""
    q = _Ctx(cr, x, y, scale, angle + swing, light, detail)
    C = PROP_COLORS
    paper = q.M["paper"] if damp < 0.05 else Mat.of(core.mix(C["paper"], "#a0a8b2", 0.28 * damp), shadow_k=0.85, line_k=0.5)
    pp = B.palette(q.light, paper)
    if state == "open":
        # the back wall of the open mouth, then the contents, then the front wall
        back = [(-27.0, 6.0), (-14.0, -1.0), (0.0, -3.0), (14.0, -1.5), (27.0, 5.0), (24.0, 14.0), (-24.0, 14.0)]
        bs, bo = _poly_paths(cr, back, q.lw, 0.6)
        q.shade(bs, Mat.of(core.shade(C["paper"], 0.25), shadow_k=0.9, line_k=0.5), 14.0, outline=bo, rim=0.3)
        _bag_contents(q)
        body = [(-27.0, 8.0), (-14.0, 12.5), (0.0, 10.0), (14.0, 13.0), (27.0, 7.5), (30.0, 30.0), (33.0, 62.0),
                (31.5, 82.0), (22.0, 86.5), (0.0, 87.5), (-22.0, 86.5), (-31.5, 82.0), (-33.0, 64.0), (-30.5, 30.0)]
    else:
        body = [(-8.0, 2.0), (8.0, 2.0), (12.0, 11.0), (24.0, 22.0), (31.5, 40.0), (33.0, 64.0), (31.5, 82.0),
                (22.0, 86.5), (0.0, 87.5), (-22.0, 86.5), (-31.5, 82.0), (-33.0, 62.0), (-30.5, 38.0),
                (-23.0, 21.0), (-11.5, 11.0)]
    bs, bo = B.smooth_paths(cr, body, q.lw, 0.62)
    pb = q.shade(bs, paper, 62.0, outline=bo)
    if q.detail >= 1:
        if state == "open":
            folds = [[(-22.0, 20.0), (-25.0, 52.0), (-26.0, 80.0)], [(20.0, 24.0), (23.0, 58.0)],
                     [(-24.0, 86.0), (-17.0, 77.0), (-7.0, 85.0)], [(24.0, 86.0), (18.0, 78.0), (8.0, 85.0)]]
        else:
            # gathered folds radiating from the tied neck
            folds = [[(-6.0, 10.0), (-15.0, 28.0), (-21.0, 50.0)], [(-1.0, 12.0), (-4.0, 30.0), (-6.0, 38.0)],
                     [(5.0, 10.0), (13.0, 26.0), (19.0, 46.0)], [(9.0, 12.0), (22.0, 30.0), (27.0, 44.0)],
                     [(-24.0, 86.0), (-17.0, 77.0), (-7.0, 85.0)], [(24.0, 86.0), (18.0, 78.0), (8.0, 85.0)]]
        if q.detail >= 2:
            folds += [[(-12.0, 68.0), (-3.0, 74.0), (8.0, 71.0)]]
        B.detail_lines(cr, folds, q.lw * 0.8, pb.line, 0.45)
    # the block-printed green cross, a hair askew
    green = B.palette(q.light, Mat.of(core.mix(C["apoth_green"], "#7f8c86", 0.3 * damp)))
    cr.save()
    cr.translate(1.0, 55.0)
    cr.rotate(-0.05)
    arm, th = 12.5, 4.8
    cross = [(-th, -arm), (th, -arm), (th, -th), (arm, -th), (arm, th), (th, th), (th, arm), (-th, arm), (-th, th),
             (-arm, th), (-arm, -th), (-th, -th)]
    core.polygon(cr, cross)
    core.src(cr, core.mix(green.lit, green.shadow, 0.12), 0.95)
    cr.fill()
    if q.detail >= 2:                                   # uneven ink of a wooden printing block
        core.src(cr, pb.lit, 0.35)
        for i in range(10):
            core.circle(cr, (core.hash01(i, 61) - 0.5) * 2 * arm, (core.hash01(i, 62) - 0.5) * 2 * th, 0.5 + 0.7 * core.hash01(i, 63))
        cr.fill()
        core.src(cr, green.hi, 0.18)
        core.polygon(cr, [(px * 0.6 - 1.4, py * 0.6 - 1.4) for px, py in cross])
        cr.fill()
    cr.restore()
    if state != "open":
        # the crumpled paper ruff above the knot (it shows above the fist)
        ruff = [(-9.0, 3.0), (-13.0, -4.0), (-10.5, -9.0), (-12.0, -14.0), (-5.0, -11.0), (-1.0, -15.0),
                (3.5, -10.5), (9.0, -14.5), (8.5, -8.0), (13.5, -5.0), (9.0, 3.0)]
        rs, ro = B.smooth_paths(cr, ruff, q.lw, 0.5)
        pr = q.shade(rs, paper, 14.0, outline=ro, rim=0.6)
        if q.detail >= 1:
            B.detail_lines(cr, [[(-6.0, 1.0), (-7.0, -8.0)], [(1.0, 1.5), (1.5, -9.0)], [(6.0, 1.0), (7.5, -7.0)]],
                           q.lw * 0.75, pr.line, 0.5)
        # the twine: two turns round the neck, a knot and loose ends
        tw = B.palette(q.light, Mat.of(C["twine"]))
        turns = [[(-10.0, 4.6), (0.0, 6.2), (10.0, 4.4)], [(-10.5, 7.6), (0.0, 9.4), (10.5, 7.2)]]
        ends = [[(9.0, 6.0), (13.0, 12.0), (12.0, 19.0)], [(9.0, 6.0), (15.5, 9.5), (19.0, 15.5)]]
        B.detail_lines(cr, turns + ends, 2.8, tw.line, 0.95, taper=(1.0, 1.0, 0.8))
        B.detail_lines(cr, turns + ends, 1.6, tw.lit, 1.0, taper=(1.0, 1.0, 0.6))
        core.circle(cr, 9.5, 6.2, 2.4)
        core.src(cr, tw.line)
        cr.fill()
        core.circle(cr, 9.2, 5.8, 1.5)
        core.src(cr, tw.lit)
        cr.fill()
    if damp > 0.1 and q.detail >= 1:                    # rain spots soaked into the paper
        core.src(cr, core.mix(pb.shadow, "#7b8794", 0.5), 0.35 * damp)
        for i in range(10):
            core.ellipse(cr, (core.hash01(i, 21) - 0.5) * 52, 22 + core.hash01(i, 22) * 60,
                         1.5 + 2.5 * core.hash01(i, 23), 1.2 + 2.0 * core.hash01(i, 24))
        cr.fill()
    q.end()
    return PropRig(grip=q.C((0.0, 0.0)), bottom=q.C((0.0, 87.0)), mouth=q.C((0.0, 6.0)))


def _bag_contents(q):
    """What peeks out of the open sack: the coloring book's corner and the SLEEP DRAUGHT's neck."""
    cr = q.cr
    C = PROP_COLORS
    bs, bo = _poly_paths(cr, [(-21.0, 14.0), (-19.0, -22.0), (7.0, -27.0), (10.0, 12.0)], q.lw)
    pc = q.shade(bs, "book_cover", 30.0, outline=bo)
    ss, so = _poly_paths(cr, [(-21.0, 14.0), (-19.0, -22.0), (-14.0, -23.0), (-16.0, 14.0)], q.lw)
    q.shade(ss, "book_spine", 6.0, outline=so, rim=0.5)
    if q.detail >= 1:
        core.circle(cr, -3.0, -6.0, 8.0)
        core.src(cr, core.mix(pc.lit, C["rose_ink"], 0.15))
        cr.fill()
        _mandala(cr, -3.0, -6.0, 8.0, C["rose_ink"], 0.85, 0.6, rings=2, petals=8)
    ns, no = _rrect_paths(cr, 13.0, -16.0, 10.0, 28.0, 3.0, q.lw)
    q.shade(ns, "blue_glass", 10.0, outline=no, rim=0.6)
    cs, co = _rrect_paths(cr, 13.5, -25.0, 9.0, 10.0, 2.0, q.lw)
    q.shade(cs, "cork", 9.0, outline=co, rim=0.5)


def bag_hold(light=None, t=0.0, swing=0.0, state="tied", damp=0.0):
    """Hold callback for `carry_bag`: the sack hangs straight down from the fist whatever the
    hand's angle (swing adds a pendulum angle, e.g. 0.12 * sin(walk phase * tau))."""
    def cb(cr, f):
        cr.save()
        cr.rotate(-f.angle)
        draw_apothecary_bag(cr, 0.0, 2.0, 1.0, light, t, 0.0, state, swing, damp)
        cr.restore()
    return cb


# ========================================================================================
# 3. THE NOTE (S2): "Something for loneliness?"
# ========================================================================================

NOTE_W, NOTE_H = 80.0, 50.0
NOTE_TEXT = ("Something for", "loneliness?")


def _note_edge(x0, x1, y, n, seed, amp=0.9):
    """A torn/deckled paper edge from x0 to x1 at height y."""
    return [(lerp(x0, x1, i / (n - 1)), y + (core.hash01(i, seed) - 0.5) * 2 * amp) for i in range(n)]


def _note_side(x, y0, y1, n, seed, amp=0.7):
    return [(x + (core.hash01(i, seed) - 0.5) * 2 * amp, lerp(y0, y1, i / (n - 1))) for i in range(n)]


def draw_note(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, unfold=1.0, text=NOTE_TEXT, detail=None):
    """The little parchment note, handwritten in iron-gall ink: "Something for / loneliness?".

    Anchor (x, y) = the centre of the open note (= the fold line); size NOTE_W x NOTE_H = 80 x 50
    at scale 1.0 (folded: 80 x 25, the lower half). unfold 0 (folded in half, the blank back of
    the top flap showing) .. 1 (open flat): animate it for the reveal -- the flap swings up
    through edge-on at 0.5. For the S2 insert close-up draw it big (scale 5-7).
    Returns PropRig(center, top, bottom)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    hw, hh = NOTE_W * 0.5, NOTE_H * 0.5
    u = clamp(unfold)
    fam, ink = FONTS.hand, C["ink"]
    fs_ = 12.0
    left_lo = _note_side(-hw, 0.0, hh, 4, 13)
    right_lo = _note_side(hw, hh, 0.0, 4, 14)
    bottom = _note_edge(hw, -hw, hh, 11, 5, 0.9)
    if u >= 0.995:
        # open flat: one sheet, a soft crease across the middle
        top = _note_edge(-hw, hw, -hh, 11, 9, 0.9)
        sheet = top + _note_side(hw, -hh, hh, 6, 15) + bottom + _note_side(-hw, hh, -hh, 6, 16)
        ns, no = _poly_paths(cr, sheet, q.lw)
        pn = q.shade(ns, "parchment", 12.0, outline=no)
        if q.detail >= 1:
            B.detail_lines(cr, [[(-hw + 2.0, 0.6), (0.0, 1.0), (hw - 2.0, 0.4)]], q.lw * 0.7, pn.line, 0.3)
            _note_text(cr, text[0], 0.0, -hh * 0.42, fs_, fam, ink, pn, seed=1)
            _note_text(cr, text[1] if len(text) > 1 else "", 0.0, hh * 0.5, fs_ * 1.08, fam, ink, pn, seed=2)
            if q.detail >= 2:                       # a little ink blot from a hesitant quill
                core.src(cr, ink, 0.55)
                core.ellipse(cr, hw * 0.72, hh * 0.62, 1.3, 1.0)
                cr.fill()
        q.end()
        return PropRig(center=q.C((0.0, 0.0)), top=q.C((0.0, -hh)), bottom=q.C((0.0, hh)))
    # lower half (always face up)
    low = [(-hw, 0.0), (hw, 0.0)] + right_lo[1:-1] + bottom + left_lo[1:-1]
    ls, lo = _poly_paths(cr, low, q.lw)
    pl = q.shade(ls, "parchment", 10.0, outline=lo)
    if q.detail >= 1 and u > 0.45:
        _note_text(cr, text[1] if len(text) > 1 else "", 0.0, hh * 0.5, fs_ * 1.08, fam, ink, pl, seed=2)
    # the top flap: its free edge at y = -hh * cos(pi * (1 - u)) (+hh when folded down)
    ey = -hh * math.cos(math.pi * (1.0 - u))
    if abs(ey) > 0.4:
        k = abs(ey) / hh
        edge = [(px, ey + (py - ey) * k) for px, py in _note_edge(-hw, hw, ey, 11, 9, 0.9)]
        flap = [(-hw, 0.0), (-hw + 0.4, ey * 0.5)] + edge + [(hw - 0.3, ey * 0.5), (hw, 0.0)]
        fs, fo = _poly_paths(cr, flap, q.lw)
        inside = ey < 0
        mat = q.M["parchment"] if inside else Mat.of(core.shade(C["parchment"], 0.07), shadow_k=0.85, line_k=0.5)
        pf = q.shade(fs, mat, min(10.0, max(abs(ey), 4.0)), outline=fo)
        if inside and q.detail >= 1 and k > 0.15:
            cr.save()
            fs.add(cr)
            cr.clip()
            cr.scale(1.0, k)
            _note_text(cr, text[0], 0.0, -hh * 0.42, fs_, fam, ink, pf, seed=1)
            cr.restore()
        elif not inside and q.detail >= 2:
            # the folded edge: a faint second (lower) layer edge peeking under the flap's edge
            B.detail_lines(cr, [[(-hw + 3.0, ey - 2.0), (hw - 3.0, ey - 1.6)]], q.lw * 0.6, pf.line, 0.35)
        B.detail_lines(cr, [[(-hw + 1.0, 0.0), (hw - 1.0, 0.0)]], q.lw * 0.8, pl.line, 0.35 + 0.35 * (1 - u))
    q.end()
    return PropRig(center=q.C((0.0, 0.0)), top=q.C((0.0, min(ey, 0.0))), bottom=q.C((0.0, hh)))


def _note_text(cr, s, x, y, size, fam, ink, pal, seed=0, clip=None):
    """Handwriting with a little life: per-word baseline wobble and a faint ink bleed."""
    if not s:
        return
    words = s.split(" ")
    core.set_font(cr, size, fam)
    widths = [cr.text_extents(w_)[4] for w_ in words]
    space = cr.text_extents(" ")[4]
    total = sum(widths) + space * (len(words) - 1)
    px = x - total / 2
    for i, (w_, ww) in enumerate(zip(words, widths)):
        dy = (core.hash01(i, seed + 40) - 0.5) * size * 0.08
        rot = (core.hash01(i, seed + 41) - 0.5) * 0.05
        sz = size * (1.12 if w_.endswith("?") else 1.0)
        with core.at(cr, px, y + dy, rot):
            core.text(cr, w_, 0.4, 0.5, sz, fam, ink, alpha_=0.18)        # the ink bleed
            core.text(cr, w_, 0.0, 0.0, sz, fam, ink, alpha_=0.92)
        px += ww + space


def note_hold(light=None, t=0.0, unfold=0.0, angle=0.0, upright=False):
    """Hold callback: the folded note pinched or flat under the fingers (slide_note, read_note).
    upright=True keeps it level on screen."""
    def cb(cr, f):
        cr.save()
        if upright:
            cr.rotate(-f.angle)
        draw_note(cr, 12.0, -8.0 if unfold < 0.5 else 0.0, 1.0, light, t, angle, unfold)
        cr.restore()
    return cb


# ========================================================================================
# 4. THE REMEDIES (S2): SLEEP DRAUGHT, VITAMINS, CALM candle
# ========================================================================================

# name -> (width, height) at scale 1.0; the anchor of every remedy is its bottom centre
REMEDIES = {"sleep": (50.0, 81.0), "vitamins": (48.0, 62.0), "calm": (47.0, 53.0), "book": (70.0, 30.0)}


def _glass_body(q, pts, mat, size, tension=0.8):
    """A glass shape: outline + cel tones, then a pale inner wall line and the window glint."""
    sh, so = B.smooth_paths(q.cr, pts, q.lw, tension)
    p = q.shade(sh, mat, size, outline=so)
    return sh, p


def _glints(cr, pts_list, alpha=0.75):
    """White specular glints (glass, varnish): each a small tapered stroke."""
    B.detail_lines(cr, pts_list, 2.2, (1, 1, 1), alpha, taper=(0.2, 1.0, 0.3))


def draw_sleep_draught(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, detail=None, label=True):
    """SLEEP DRAUGHT: a round blue glass flask, corked and sealed with midnight wax, a parchment
    label with a crescent moon. Anchor (x, y) = bottom centre (where it stands); 50 x 78 at
    scale 1.0. Returns PropRig(top, center, label)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    cr_ = cr
    R, cy = 24.0, -27.0
    bulb = [(math.cos(a) * R, cy + math.sin(a) * R) for a in [math.pi * 0.5 + (i / 22) * TAU for i in range(22)]]
    # flatten the base, run the neck up from the shoulders
    bulb = [(px, min(py, -1.0)) for px, py in bulb]
    # build bulb + neck as one union silhouette
    cr_.new_path()
    core.smooth_closed(cr_, bulb, 0.9)
    core.rounded_rect(cr_, -6.0, -64.0, 12.0, 20.0, 2.5)
    union = Path(cr_)
    core.smooth_closed(cr_, B.offset_closed(bulb, q.lw), 0.9)
    core.rounded_rect(cr_, -6.0 - q.lw, -64.0 - q.lw, 12.0 + 2 * q.lw, 20.0 + 2 * q.lw, 2.5 + q.lw)
    out = Path(cr_)
    p = q.shade(union, "blue_glass", 34.0, outline=out)
    # the draught inside (deeper blue), a meniscus line and a faint inner glow
    cr_.save()
    union.add(cr_)
    cr_.clip()
    liq = B.palette(q.light, Mat.of(C["draught"], sss=0.3))
    lvl = -40.0 + 0.8 * math.sin(t * 1.7)
    cr_.rectangle(-30, lvl, 60, 40)
    core.src(cr_, core.mix(liq.lit, liq.shadow, 0.35))
    cr_.fill()
    core.ellipse(cr_, 0.0, lvl, 19.5, 2.2)
    core.src(cr_, liq.hi, 0.55)
    cr_.fill()
    if q.detail >= 1:
        # inner wall (the glass is thick): a pale band just inside the right edge
        core.src(cr_, p.hi, 0.25)
        cr_.arc(0.0, cy, R - 3.0, -0.9, 0.9)
        cr_.arc_negative(0.0, cy, R - 6.0, 0.9, -0.9)
        cr_.close_path()
        cr_.fill()
        # a few rising bubbles
        core.src(cr_, liq.hi, 0.6)
        for i in range(4):
            u = ((t * 0.35 + core.hash01(i, 31)) % 1.0)
            core.circle(cr_, -10 + 20 * core.hash01(i, 32), -4 - u * 30, 1.0 + 0.6 * core.hash01(i, 33))
        cr_.fill()
    cr_.restore()
    # lip, cork and the wax seal
    ls, lo = _rrect_paths(cr_, -8.0, -66.0, 16.0, 5.0, 2.0, q.lw)
    q.shade(ls, "blue_glass", 5.0, outline=lo, rim=0.5)
    ck = [(-5.5, -65.0), (-6.5, -74.0), (-5.0, -77.5), (5.0, -77.5), (6.5, -74.0), (5.5, -65.0)]
    cs, co = _poly_paths(cr_, ck, q.lw, 0.6)
    q.shade(cs, "cork", 11.0, outline=co, rim=0.6)
    seal = [(-7.0, -72.0), (-6.0, -79.5), (0.0, -81.0), (6.0, -79.5), (7.5, -72.0), (5.0, -69.5), (4.0, -73.0),
            (0.0, -74.5), (-3.0, -73.5), (-5.0, -68.5)]
    ws, wo = B.smooth_paths(cr_, seal, q.lw, 0.7)
    q.shade(ws, Mat.of(C["wax_seal"], sheen=0.5), 8.0, outline=wo, rim=0.6)
    if label:
        _remedy_label(q, 0.0, -25.0, 40.0, 25.0, ("SLEEP", "DRAUGHT"), None, curve=2.2)
        if q.detail >= 1:                       # a crescent moon and stars painted on the shoulder
            _label_icon(cr_, "moon_white", 9.0, -43.5)
    _glints(cr_, [[(-17.0, -38.0), (-19.5, -30.0), (-18.5, -21.0)], [(-3.5, -60.0), (-3.6, -50.0)]], 0.7)
    q.end()
    return PropRig(top=q.C((0.0, -81.0)), center=q.C((0.0, cy)), label=q.C((0.0, -25.0)))


def _remedy_label(q, cx, cy, w, h, lines, icon=None, curve=0.0, color=None):
    """A parchment label pasted on a curved glass body (curve = how much it bows), with 1-2 lines
    of storybook small caps (auto-fitted) and a tiny painted icon: "moon" (top-left corner),
    "sun" (left of the word) or "sprig" (both sides)."""
    cr = q.cr
    C = PROP_COLORS
    n = 7
    top = [(cx - w / 2 + w * i / (n - 1), cy - h / 2 + curve * (1 - (2 * i / (n - 1) - 1) ** 2)) for i in range(n)]
    bot = [(cx + w / 2 - w * i / (n - 1), cy + h / 2 + curve * (1 - (2 * (n - 1 - i) / (n - 1) - 1) ** 2)) for i in range(n)]
    ls, lo = _poly_paths(cr, top + bot, q.lw * 0.8)
    pl = q.shade(ls, "parchment", min(h, 9.0), outline=lo, rim=0.4)
    if q.detail < 1:
        return
    ink = core.mix(C["ink"], pl.shadow, 0.15)
    border = B.offset_closed(top + bot, -1.8)
    cr.new_path()
    core.polygon(cr, border)
    cr.set_line_width(0.6)
    core.src(cr, color or C["apoth_green"], 0.75)
    cr.stroke()
    fam = FONTS.label
    yb = cy + curve * 0.7
    if len(lines) == 1:
        side = 9.0 if icon in ("sun", "sprig") else 0.0
        dx = side * 0.5 if icon == "sun" else 0.0
        _label(cr, lines[0], cx + dx, yb, min(h * 0.46, 10.5), ink, fam, maxw=w - 6.0 - side * (2 if icon == "sprig" else 1))
        if icon == "sun" and q.detail >= 2:
            _label_icon(cr, "sun", cx - w / 2 + 6.5, yb)
        elif icon == "sprig" and q.detail >= 2:
            _label_icon(cr, "sprig", cx - w / 2 + 6.5, yb)
            _label_icon(cr, "sprig", cx + w / 2 - 6.5, yb)
    else:
        _label(cr, lines[0], cx + (2.5 if icon == "moon" else 0.0), yb - h * 0.19, h * 0.31, ink, fam, spacing=0.3,
               maxw=w - 12.0)
        _label(cr, lines[1], cx, yb + h * 0.2, h * 0.28, ink, fam, maxw=w - 6.0)
        if icon == "moon" and q.detail >= 2:
            _label_icon(cr, "moon", cx - w / 2 + 6.0, yb - h * 0.2)


def _label_icon(cr, icon, x, y):
    """Tiny painted label icons centred at (x, y): moon (sleep), sun (vitamins), sprig (calm)."""
    if icon in ("moon", "moon_white"):
        core.src(cr, "#3d4f8a" if icon == "moon" else "#e8eefc", 0.85)
        cr.new_path()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        core.circle(cr, x, y, 3.0)
        core.circle(cr, x + 1.4, y - 0.9, 2.5)
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
        core.circle(cr, x - 6.0, y + 1.0, 0.7)
        core.circle(cr, x - 3.6, y - 2.4, 0.5)
        cr.fill()
    elif icon == "sun":
        core.src(cr, "#c08a2a", 0.9)
        core.circle(cr, x, y, 2.2)
        cr.fill()
        cr.set_line_width(0.7)
        for k in range(8):
            ang = k * TAU / 8
            cr.move_to(x + math.cos(ang) * 3.2, y + math.sin(ang) * 3.2)
            cr.line_to(x + math.cos(ang) * 4.6, y + math.sin(ang) * 4.6)
        cr.stroke()
    elif icon == "sprig":
        cr.set_line_width(0.6)
        core.src(cr, "#5e7a4a", 0.9)
        cr.move_to(x - 4.0, y + 2.0)
        cr.curve_to(x - 1.0, y + 1.0, x + 1.0, y - 0.5, x + 4.0, y - 2.5)
        cr.stroke()
        core.src(cr, "#8a6ac0", 0.95)
        for k in range(4):
            core.ellipse(cr, x - 1.5 + k * 1.8, y + 0.2 - k * 0.9, 1.0, 0.65, -0.5)
        cr.fill()


def draw_vitamins(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, detail=None, glow=1.0, label=True):
    """VITAMINS: a squat glass jar of softly glowing berry-pills under a linen cover tied with
    twine. Anchor = bottom centre; 46 x 62 at scale 1.0. glow 0..1 (they shimmer by
    themselves). Returns PropRig(top, center, label)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    cr_ = cr
    body = [(-21.0, -2.0), (-23.5, -12.0), (-23.5, -38.0), (-19.5, -46.0), (-16.0, -48.5), (16.0, -48.5),
            (19.5, -46.0), (23.5, -38.0), (23.5, -12.0), (21.0, -2.0), (12.0, 0.0), (-12.0, 0.0)]
    sh, so = B.smooth_paths(cr_, body, q.lw, 0.55)
    p = q.shade(sh, "jar_glass", 40.0, outline=so)
    # the glowing berries inside, piled to ~3/4 height
    cr_.save()
    sh.add(cr_)
    cr_.clip()
    gl = clamp(glow)
    if gl > 0:
        fx.glow(cr_, 0.0, -18.0, 30.0, "#b8ff9a", 0.35 * gl)
    cols = (C["berry_a"], C["berry_a"], C["berry_b"])
    berries = []
    for i in range(16):
        row = i // 4
        bx = -15.0 + (i % 4) * 10.0 + (5.0 if row % 2 else 0.0) + (core.hash01(i, 51) - 0.5) * 3
        by = -7.0 - row * 8.5 + (core.hash01(i, 52) - 0.5) * 2
        if row == 3 and abs(bx) > 14:
            continue
        berries.append((bx, by, 4.6 + core.hash01(i, 53) * 1.0, cols[i % 3], i))
    for bx, by, r, c, i in berries:
        bp = B.palette(q.light, Mat.of(c, sss=0.5))
        tw = 0.75 + 0.25 * math.sin(t * (1.3 + core.hash01(i, 54)) + i * 1.7)
        core.circle(cr_, bx, by, r + 0.6)
        core.src(cr_, bp.line, 0.8)
        cr_.fill()
        core.circle(cr_, bx, by, r)
        core.src(cr_, core.mix(bp.shadow, bp.lit, 0.55 + 0.45 * gl * tw))
        cr_.fill()
        if q.detail >= 1:
            core.circle(cr_, bx - r * 0.35, by - r * 0.35, r * 0.3)
            core.src(cr_, (1, 1, 1), 0.55 * tw)
            cr_.fill()
            core.src(cr_, bp.line, 0.75)                  # the little crown of a berry
            for k in range(3):
                a_ = -math.pi / 2 + (k - 1) * 0.7
                core.circle(cr_, bx + math.cos(a_) * r * 0.25 + r * 0.15, by - r * 0.55 + math.sin(a_) * r * 0.1, r * 0.13)
            cr_.fill()
    if q.detail >= 1:                               # inner wall band of the thick glass
        core.src(cr_, p.hi, 0.22)
        cr_.rectangle(14.5, -44.0, 4.0, 40.0)
        cr_.fill()
    cr_.restore()
    # the rim and the linen cover, tied with twine
    rs, ro = _rrect_paths(cr_, -18.5, -52.0, 37.0, 5.5, 2.5, q.lw)
    q.shade(rs, "jar_glass", 5.0, outline=ro, rim=0.5)
    cover = [(-21.0, -47.0), (-19.0, -55.0), (-12.0, -60.5), (0.0, -62.0), (12.0, -60.5), (19.0, -55.0),
             (21.0, -47.0), (16.0, -44.5), (12.5, -47.5), (8.0, -44.0), (3.5, -47.0), (-1.5, -44.0),
             (-6.0, -47.0), (-10.5, -44.0), (-15.0, -47.0), (-18.0, -44.5)]
    ls, lo = B.smooth_paths(cr_, cover, q.lw, 0.55)
    pc = q.shade(ls, "linen", 14.0, outline=lo, rim=0.7)
    tw_ = B.palette(q.light, Mat.of(C["twine"]))
    B.detail_lines(cr_, [[(-19.5, -51.0), (0.0, -50.0), (19.5, -51.0)]], 2.4, tw_.line, 0.9, taper=(0.9, 1.0, 0.9))
    B.detail_lines(cr_, [[(-19.5, -51.0), (0.0, -50.0), (19.5, -51.0)]], 1.4, tw_.lit, 1.0, taper=(0.9, 1.0, 0.9))
    if q.detail >= 2:
        B.detail_lines(cr_, [[(14.0, -50.5), (18.0, -45.0), (17.0, -41.0)], [(14.0, -50.5), (21.0, -47.0), (23.5, -43.0)]],
                       1.3, tw_.lit, 1.0, taper=(0.9, 1.0, 0.5))
        B.detail_lines(cr_, [[(-12.0, -57.0), (-4.0, -55.5)], [(4.0, -58.0), (11.0, -56.0)]], q.lw * 0.7, pc.line, 0.4)
    if label:
        _remedy_label(q, 0.0, -24.0, 41.0, 17.0, ("VITAMINS",), "sun", curve=1.6, color="#a07a2a")
    _glints(cr_, [[(-17.0, -40.0), (-18.0, -30.0)], [(-14.0, -10.0), (-15.0, -6.0)]], 0.65)
    q.end()
    return PropRig(top=q.C((0.0, -62.0)), center=q.C((0.0, -25.0)), label=q.C((0.0, -25.0)))


def _flame(cr, x, y, h, w, t, seed=0, color="#FFB347", core_color="#FFF4CF", lit=1.0, alpha=1.0):
    """A flickering teardrop candle flame based at (x, y), height h, width w (pure function of t).
    Drawn with soft gradients (a light source) and ADD."""
    if lit <= 0.01:
        return (x, y)
    fl = 1.0 + 0.10 * core.noise1(t * 7.0, seed) + 0.05 * math.sin(t * 23.0 + seed)
    sway = 0.18 * core.noise1(t * 2.3, seed + 5) + 0.06 * math.sin(t * 11.0 + seed)
    hh = h * fl * (0.4 + 0.6 * lit)
    ww = w * (0.85 + 0.15 * fl) * (0.6 + 0.4 * lit)
    tipx, tipy = x + sway * hh, y - hh
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    for k, (sc, c, a) in enumerate(((1.0, color, 0.75), (0.55, core_color, 0.95))):
        cr.new_path()
        bx, by = x, y - hh * 0.18 * sc
        cr.move_to(tipx * sc + x * (1 - sc), tipy * sc + y * (1 - sc))
        cr.curve_to(x + ww * sc * 0.9, y - hh * 0.45 * sc, x + ww * sc * 0.75, by + ww * 0.7 * sc, x, by + ww * 0.75 * sc)
        cr.curve_to(x - ww * sc * 0.75, by + ww * 0.7 * sc, x - ww * sc * 0.9, y - hh * 0.45 * sc,
                    tipx * sc + x * (1 - sc), tipy * sc + y * (1 - sc))
        cc = core.col(c)
        pat = cairo.RadialGradient(x, y - hh * 0.25 * sc, 0, x, y - hh * 0.25 * sc, hh * 0.8 * sc + 1e-3)
        pat.add_color_stop_rgba(0.0, cc[0], cc[1], cc[2], a * alpha * lit)
        pat.add_color_stop_rgba(1.0, cc[0], cc[1], cc[2], a * alpha * lit * 0.35)
        cr.set_source(pat)
        cr.fill()
    cr.restore()
    return (x + sway * hh * 0.4, y - hh * 0.45)


def draw_calm_candle(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, lit=1.0, flame="cool", detail=None,
                     label=True):
    """CALM: a lavender candle in a glass tumbler with a painted band label and a sprig.

    Anchor = bottom centre; 46 x 50 at scale 1.0 (the flame adds ~16). lit 0..1 (0: a dark
    wick and a thread of smoke). flame "cool" (a pale lavender spell-flame: the remedies are
    stones, not kindness) or "warm". Draw its halo with candle_glow(). Returns PropRig(top,
    flame, center, label)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    cr_ = cr
    body = [(-16.0, 0.0), (-21.0, -4.0), (-23.5, -18.0), (-22.5, -36.0), (-19.0, -44.0), (-18.5, -48.0),
            (18.5, -48.0), (19.0, -44.0), (22.5, -36.0), (23.5, -18.0), (21.0, -4.0), (16.0, 0.0)]
    sh, so = B.smooth_paths(cr_, body, q.lw, 0.6)
    p = q.shade(sh, "tumbler", 40.0, outline=so)
    cr_.save()
    sh.add(cr_)
    cr_.clip()
    wax = B.palette(q.light, q.M["wax"])
    top_w = -30.0
    cr_.rectangle(-25.0, top_w, 50.0, 30.0)
    core.src(cr_, core.mix(wax.lit, wax.shadow, 0.25))
    cr_.fill()
    core.ellipse(cr_, 0.0, top_w, 20.5, 3.6)
    core.src(cr_, wax.hi if lit > 0.5 else wax.lit)
    cr_.fill()
    core.ellipse(cr_, 0.0, top_w + 0.6, 12.0, 1.9)          # the melt pool
    core.src(cr_, core.mix(wax.lit, "#ffffff", 0.25 * lit), 0.8)
    cr_.fill()
    if q.detail >= 1:
        core.src(cr_, p.hi, 0.25)                          # thick glass base
        core.ellipse(cr_, 0.0, -3.0, 19.0, 3.5)
        cr_.fill()
    cr_.restore()
    # the rolled glass lip, then the wick
    rs, ro = _rrect_paths(cr_, -21.0, -52.5, 42.0, 5.5, 2.7, q.lw)
    q.shade(rs, "tumbler", 5.0, outline=ro, rim=0.6)
    B.detail_lines(cr_, [[(0.0, top_w), (0.4, top_w - 4.5), (1.4, top_w - 6.5)]], 1.6, "#2a2018", 1.0, taper=(1, 1, 0.6))
    fpt = (0.0, top_w - 6.0)
    if label:
        _remedy_label(q, 0.0, -17.0, 42.0, 15.0, ("CALM",), "sprig", curve=2.0, color="#7a5aa8")
    _glints(cr_, [[(-18.0, -42.0), (-19.0, -26.0)], [(15.5, -40.0), (16.0, -34.0)]], 0.6)
    if lit > 0.01:
        fcol = C["flame_cool"] if flame == "cool" else C["flame_warm"]
        fcore = "#FFFFFF" if flame == "cool" else C["candle_hot"]
        fpt = _flame(cr_, 0.6, top_w - 5.0, 15.0, 4.2, t, 3, fcol, fcore, lit)
    elif q.detail >= 1:
        fx.smoke(cr_, (t % 3.0), 0.0, 1.4, top_w - 7.0, n=4, dur=2.4, rise=26.0, drift=(4.0, 0.0), size=1.6,
                 color="#b8b0c0", alpha=0.35, seed=4)
    q.end()
    return PropRig(top=q.C((0.0, -52.0)), flame=q.C(fpt), center=q.C((0.0, -25.0)), label=q.C((0.0, -17.0)))


def candle_glow(cr, rig, scale=1.0, t=0.0, flame="cool", strength=1.0):
    """The CALM candle's halo (draw after the candle, or into the LightLayer). rig = its PropRig."""
    c = PROP_COLORS["flame_cool"] if flame == "cool" else PROP_COLORS["candle"]
    fl = 0.9 + 0.1 * core.noise1(t * 6.0, 3)
    fx.glow(cr, rig.flame[0], rig.flame[1], 46 * scale, c, 0.35 * strength * fl)


def draw_remedy(cr, name, x, y, scale=1.0, light=None, t=0.0, angle=0.0, detail=None, **kw):
    """Dispatch by name: "sleep" (SLEEP DRAUGHT), "vitamins", "calm" (candle), "book" (the
    coloring book lying flat). Anchor = bottom centre."""
    if name == "sleep":
        return draw_sleep_draught(cr, x, y, scale, light, t, angle, detail, **kw)
    if name == "vitamins":
        return draw_vitamins(cr, x, y, scale, light, t, angle, detail, **kw)
    if name == "calm":
        return draw_calm_candle(cr, x, y, scale, light, t, angle, detail=detail, **kw)
    if name == "book":
        return draw_coloring_book(cr, x, y - 5.0 * scale, scale, light, t, angle, state="flat", detail=detail, **kw)
    raise ValueError(f"unknown remedy {name!r}")


def remedy_hold(name, light=None, t=0.0, upright=True, **kw):
    """Hold callback putting a remedy in any hand (the lioness's `place`): the grip is round
    the item's middle; upright=True keeps it standing straight."""
    w, h = REMEDIES.get(name, (60.0, 20.0))

    def cb(cr, f):
        cr.save()
        if upright:
            cr.rotate(-f.angle)
        draw_remedy(cr, name, 0.0, h * 0.45 if name != "book" else 10.0, 1.0, light, t, **kw)
        cr.restore()
    return cb


def pile_layout(n=4):
    """A neat, absurdly tall S2 counter pile: [(name, dx, dy)] offsets (scale 1.0) from the pile's
    bottom centre for the first n items, in the order the pharmacist sets them down (SLEEP
    DRAUGHT, VITAMINS, CALM, the book on top), each dy = the surface it stands on."""
    lay = [("sleep", -30.0, 0.0), ("vitamins", 24.0, 0.0), ("calm", 24.0, -62.0), ("book", -4.0, -112.0)]
    return lay[:max(0, min(n, 4))]


# ========================================================================================
# 5. THE COLORING BOOK (S2 item 4, S6): MINDFUL COLORING FOR ADULTS
# ========================================================================================

BOOK_W, BOOK_H = 64.0, 72.0           # one page / the closed cover


def _mandala(cr, cx, cy, r, color, alpha=1.0, w=0.9, seed=0, rings=3, petals=12):
    """Line-art mandala / rose window: concentric rings of petals (one batched ink fill)."""
    lines = []
    for k in range(rings):
        rr0 = r * (0.22 + 0.78 * k / max(1, rings))
        rr1 = r * (0.22 + 0.78 * (k + 1) / max(1, rings))
        n = petals if k % 2 == 0 else petals // 2 * 2
        off = (math.pi / n) * (k % 2)
        for i in range(n):
            a = off + TAU * i / n
            a0, a1 = a - math.pi / n * 0.95, a + math.pi / n * 0.95
            mid = (rr0 + rr1) * 0.5
            lines.append([(cx + math.cos(a0) * rr0, cy + math.sin(a0) * rr0),
                          (cx + math.cos(a - 0.04) * (mid + (rr1 - rr0) * 0.25), cy + math.sin(a - 0.04) * (mid + (rr1 - rr0) * 0.25)),
                          (cx + math.cos(a) * rr1, cy + math.sin(a) * rr1),
                          (cx + math.cos(a + 0.04) * (mid + (rr1 - rr0) * 0.25), cy + math.sin(a + 0.04) * (mid + (rr1 - rr0) * 0.25)),
                          (cx + math.cos(a1) * rr0, cy + math.sin(a1) * rr0)])
        lines.append(_ellipse_pts(cx, cy, rr1, rr1, 28) + [_ellipse_pts(cx, cy, rr1, rr1, 28)[0]])
    lines.append(_ellipse_pts(cx, cy, r * 0.12, r * 0.12, 12) + [_ellipse_pts(cx, cy, r * 0.12, r * 0.12, 12)[0]])
    B.detail_lines(cr, lines, w, color, alpha, taper=(0.8, 1.0, 0.8))


def _cover_art(q, x0, y0, w, h, pal):
    """The cover: storybook title, a rose-window mandala in rose/teal/gold inks, a ruled frame."""
    cr = q.cr
    C = PROP_COLORS
    ink = core.mix(C["ink"], pal.shadow, 0.1)
    cx = x0 + w / 2
    if q.detail >= 1:
        cr.new_path()
        cr.rectangle(x0 + 3.0, y0 + 3.0, w - 6.0, h - 6.0)
        cr.set_line_width(0.8)
        core.src(cr, C["gold_ink"], 0.85)
        cr.stroke()
    mr = w * 0.26
    my = y0 + h * 0.56
    if q.detail >= 1:
        core.circle(cr, cx, my, mr * 1.02)
        core.src(cr, core.mix(pal.lit, C["rose_ink"], 0.12))
        cr.fill()
        _mandala(cr, cx, my, mr, C["rose_ink"], 0.9, 0.75, rings=3, petals=10)
        _mandala(cr, cx, my, mr * 0.55, C["teal_ink"], 0.9, 0.7, rings=2, petals=8)
        core.circle(cr, cx, my, mr * 0.1)
        core.src(cr, C["gold_ink"])
        cr.fill()
    else:
        core.circle(cr, cx, my, mr)
        core.src(cr, core.mix(pal.lit, C["rose_ink"], 0.4))
        cr.fill()
    fam = FONTS.label
    _label(cr, "MINDFUL", cx, y0 + h * 0.13, h * 0.125, ink, fam, spacing=0.3)
    _label(cr, "COLORING", cx, y0 + h * 0.27, h * 0.11, ink, fam, spacing=0.2)
    if q.detail >= 1:
        _label(cr, "for Adults", cx, y0 + h * 0.9, h * 0.085, core.mix(ink, C["rose_ink"], 0.4), FONTS.text,
               italic=True)


def _page_art(q, x0, y0, w, h, pal, seed, colored=0.0):
    """An inside page: one big line-art mandala (uncoloured, or a few petals filled in)."""
    cr = q.cr
    C = PROP_COLORS
    cx, cy = x0 + w / 2, y0 + h * 0.5
    r = min(w, h) * 0.38
    if colored > 0 and q.detail >= 1:
        cols = (C["rose_ink"], C["teal_ink"], C["gold_ink"])
        for i in range(int(6 * colored)):
            a = TAU * i / 10 + seed
            core.src(cr, core.mix(cols[i % 3], pal.lit, 0.45), 0.8)
            core.ellipse(cr, cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62, r * 0.16, r * 0.1, a)
            cr.fill()
    if q.detail >= 1:
        _mandala(cr, cx, cy, r, C["line_art"], 0.75, 0.6, seed=seed, rings=3 + seed % 2, petals=8 + 2 * (seed % 3))
    else:
        core.circle(cr, cx, cy, r)
        cr.set_line_width(0.8)
        core.src(cr, C["line_art"], 0.5)
        cr.stroke()


def draw_coloring_book(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, state="closed", flip=0.0,
                       page=0, colored=0.0, detail=None):
    """MINDFUL COLORING FOR ADULTS: a parchment-covered coloring book with a rose-window mandala.

    Anchor (x, y) = the book's centre (closed: the cover's centre; open: the middle of the
    spine). Page / cover size BOOK_W x BOOK_H = 64 x 72 at scale 1.0 (open: 128 wide).
    state: "closed" (front cover), "back" (back cover), "open" (two line-art pages), "flat"
    (lying on a counter, seen from a little above: 66 x ~22, anchor = centre of its top face).
    flip 0..1 (state "open"): the right-hand page turns over to the left (flip through it).
    page selects which mandalas show; colored 0..1 fills a few petals (someone tried)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    w, h = BOOK_W, BOOK_H
    if state in ("closed", "back"):
        # the page block edge shows on the right/bottom: a slab behind the cover
        bs, bo = _rrect_paths(cr, -w / 2 + 2.0, -h / 2 + 2.5, w + 1.5, h + 1.0, 2.0, q.lw)
        q.shade(bs, "page", 6.0, outline=bo, rim=0.4)
        cs, co = _rrect_paths(cr, -w / 2, -h / 2, w, h, 2.5, q.lw)
        pc = q.shade(cs, "book_cover", 22.0, outline=co)
        ss, so = _rrect_paths(cr, -w / 2 - 1.0, -h / 2, 7.0, h, 2.0, q.lw)
        q.shade(ss, "book_spine", 7.0, outline=so, rim=0.6)
        if state == "closed":
            _cover_art(q, -w / 2 + 6.0, -h / 2, w - 6.0, h, pc)
        elif q.detail >= 1:
            _mandala(cr, 3.0, 0.0, 12.0, C["rose_ink"], 0.6, 0.6, rings=2, petals=8)
        q.end()
        return PropRig(center=q.C((0.0, 0.0)), top=q.C((0.0, -h / 2)))
    if state == "flat":
        _book_flat(q, w, h, angle_yaw=-0.18)
        q.end()
        return PropRig(center=q.C((0.0, 0.0)), top=q.C((0.0, -h * 0.5 * math.sin(0.32))))
    # ---- open: two pages either side of the spine, then the turning page
    cs, co = _rrect_paths(cr, -w - 2.5, -h / 2 - 2.0, 2 * w + 5.0, h + 4.0, 3.0, q.lw)
    q.shade(cs, "book_spine", 10.0, outline=co, rim=0.4)
    for side in (-1, 1):
        x0 = -w if side < 0 else 0.0
        pts = [(x0 + (1.0 if side < 0 else 0.0), -h / 2 + (1.5 if side < 0 else 0.5)),
               (x0 + w * 0.5, -h / 2 - 0.5), (x0 + w - (0.0 if side < 0 else 1.0), -h / 2 + (0.5 if side < 0 else 1.5)),
               (x0 + w - (0.0 if side < 0 else 1.0), h / 2 - (0.5 if side < 0 else 1.0)), (x0 + w * 0.5, h / 2 + 0.6),
               (x0 + (1.0 if side < 0 else 0.0), h / 2 - (1.0 if side < 0 else 0.5))]
        ps, po = _poly_paths(cr, pts, q.lw * 0.8)
        pp = q.shade(ps, "page", 14.0, outline=po, rim=0.4)
        _page_art(q, x0, -h / 2, w, h, pp, page * 2 + (0 if side < 0 else 1), colored if side < 0 else 0.0)
    # the gutter shadow
    if q.detail >= 1:
        pat = core.linear(-8.0, 0.0, 8.0, 0.0, [(0.0, (0, 0, 0, 0.0)), (0.5, (0.15, 0.08, 0.1, 0.32)), (1.0, (0, 0, 0, 0.0))])
        cr.rectangle(-8.0, -h / 2, 16.0, h)
        cr.set_source(pat)
        cr.fill()
    f = clamp(flip)
    if 0.0 < f < 1.0:
        _turning_page(q, w, h, f, page)
    q.end()
    return PropRig(center=q.C((0.0, 0.0)), left=q.C((-w / 2, 0.0)), right=q.C((w / 2, 0.0)))


def _book_flat(q, w, h, angle_yaw=-0.18, elev=0.32, thick=8.0):
    """The book lying on a counter, seen from a little above: a projected box. Its top face is
    an affine image of the cover, so the cover art is drawn through that matrix."""
    cr = q.cr
    C = PROP_COLORS
    c, s_ = math.cos(angle_yaw), math.sin(angle_yaw)
    se, ce = math.sin(elev), math.cos(elev)

    def P(X, Y, Z):
        xr, zr = X * c + Z * s_, -X * s_ + Z * c
        return (xr, Y * ce + zr * se)

    hw, hd = w / 2, h / 2
    top = [P(-hw, 0, -hd), P(hw, 0, -hd), P(hw, 0, hd), P(-hw, 0, hd)]
    front = [P(-hw, 0, hd), P(hw, 0, hd), P(hw, thick, hd), P(-hw, thick, hd)]
    side_x = hw if s_ > 0 else -hw
    side = [P(side_x, 0, hd), P(side_x, 0, -hd), P(side_x, thick, -hd), P(side_x, thick, hd)]
    # the page block (front face, plus the right side when it shows), then the spine, then the cover
    fs, fo = _poly_paths(cr, front, q.lw)
    pf = q.shade(fs, "page", thick, outline=fo, rim=0.3)
    if q.detail >= 1:
        lines = []
        for k in (0.35, 0.65):
            a_, b_ = P(-hw + 1, thick * k + 1, hd), P(hw - 1, thick * k + 1, hd)
            lines.append([a_, b_])
        B.detail_lines(cr, lines, 0.6, pf.line, 0.45)
    ss, so = _poly_paths(cr, side, q.lw)
    q.shade(ss, "book_spine" if side_x < 0 else "page", thick, outline=so, rim=0.4)
    ts, to = _poly_paths(cr, top, q.lw)
    pc = q.shade(ts, "book_cover", h * se, outline=to)
    cr.save()
    ts.add(cr)
    cr.clip()
    # (u, v) on the cover -> P(u, 0, v): x = u c + v s, y = (-u s + v c) se  (an affine map)
    cr.transform(cairo.Matrix(c, -s_ * se, s_, c * se, 0.0, 0.0))
    _cover_art(q, -w / 2 + 6.0, -h / 2, w - 6.0, h, pc)
    spine = [(-w / 2 - 1.0, -h / 2), (-w / 2 + 6.0, -h / 2), (-w / 2 + 6.0, h / 2), (-w / 2 - 1.0, h / 2)]
    core.polygon(cr, spine)
    core.src(cr, B.palette(q.light, q.M["book_spine"]).lit)
    cr.fill()
    cr.restore()


def _turning_page(q, w, h, f, page):
    """A page turning about the spine: its free edge sweeps from +w to -w (x = w cos(pi f)),
    bowing as it goes; the front face shows first, then its back."""
    cr = q.cr
    c = math.cos(math.pi * f)
    ex = w * c
    lift = math.sin(math.pi * f)
    bow = 10.0 * lift
    top = -h / 2 - 4.0 * lift
    bot = h / 2 - 1.5 * lift
    pts = [(0.0, -h / 2), (ex * 0.55 + bow * 0.4 * (1 if c >= 0 else -1), top - 2.0 * lift), (ex, top + 1.0 * lift),
           (ex - 2.5 * lift * (1 if c >= 0 else -1), (top + bot) * 0.5), (ex, bot), (ex * 0.55, bot + 2.0 * lift),
           (0.0, h / 2)]
    # the shadow it throws on the page beneath
    cr.save()
    sx = 1 if c >= 0 else -1
    pat = core.linear(0.0, 0.0, ex * 1.2 + sx * 1e-3, 0.0, [(0.0, (0.1, 0.05, 0.1, 0.25 * lift)), (1.0, (0.1, 0.05, 0.1, 0.0))])
    cr.rectangle(min(0.0, ex * 1.3), -h / 2, abs(ex) * 1.3 + 1.0, h)
    cr.set_source(pat)
    cr.fill()
    cr.restore()
    if abs(ex) < 1.5:
        B.detail_lines(cr, [[(0.0, -h / 2 - 4.0), (0.0, h / 2)]], 2.0, B.palette(q.light, q.M["page"]).line, 0.9)
        return
    ps, po = B.smooth_paths(cr, pts, q.lw * 0.8, 0.6)
    pp = q.shade(ps, "page", min(14.0, abs(ex) * 0.6), outline=po, rim=0.6)
    if q.detail >= 1 and abs(ex) > 10:
        cr.save()
        ps.add(cr)
        cr.clip()
        cr.scale(abs(c), 1.0)
        x0 = 0.0 if c >= 0 else -w
        _page_art(q, x0, -h / 2, w, h, pp, page * 2 + (1 if c >= 0 else 2))
        cr.restore()


def book_hold(light=None, t=0.0, state="open", flip=0.0, page=0, colored=0.0):
    """Two-hand callback for the dragon's `hold_book` (called once at the midpoint between his
    grips, upright): the open book facing the camera. state "closed" shows the cover."""
    def cb(cr, f):
        draw_coloring_book(cr, 0.0, -6.0, 1.0, light, t, 0.0, state, flip, page, colored)
    return cb


# ========================================================================================
# 6. THE BREAD (S6-S8): one round crusty loaf for the whole film (the gnome's colours)
# ========================================================================================

LOAF = 46.0            # loaf diameter at scale 1.0 (= the gnome's GNOME_LOAF)


def _loaf_pts(r, n=22):
    """The boule's silhouette: a high domed top, a flatter base (matches the gnome's loaf)."""
    pts = []
    for i in range(n):
        a = math.pi + math.pi * i / (n - 1)
        pts.append((math.cos(a) * r, math.sin(a) * r * 0.8 + r * 0.12))
    pts += [(r * 0.97, r * 0.3), (r * 0.72, r * 0.5), (0.0, r * 0.56), (-r * 0.72, r * 0.5), (-r * 0.97, r * 0.3)]
    return pts


def _crumb_face(q, pts, seed, holes=9, rim=None):
    """The torn, fluffy inside of the loaf filling the closed outline `pts`: a ragged pale face
    (a crust-coloured rim first when `rim` > 0), airy holes (each a dark pit with a lit lower
    lip) and pulled tufts along its edge."""
    cr = q.cr
    n = len(pts)
    cx = sum(px for px, _ in pts) / n
    cy = sum(py for _, py in pts) / n
    rag = []
    for i, (px, py) in enumerate(pts):
        k = 1.0 + 0.06 * math.sin(i * 2.7 + seed) + (0.07 if i % 3 == 0 else 0.0)
        rag.append((cx + (px - cx) * k, cy + (py - cy) * k))
    if rim:
        crust_rim = [(cx + (px - cx) * (1 + rim), cy + (py - cy) * (1 + rim)) for px, py in pts]
        rs, ro = B.smooth_paths(cr, crust_rim, q.lw, 0.75)
        q.shade(rs, "crust", 8.0, outline=ro)
    fs, fo = B.smooth_paths(cr, rag, q.lw * 0.8, 0.75)
    xs = [px for px, _ in rag]
    ys = [py for _, py in rag]
    w_, h_ = max(xs) - min(xs), max(ys) - min(ys)
    p = q.shade(fs, "crumb", min(w_, h_) * 0.6, outline=fo if not rim else False)
    if q.detail >= 1:
        cr.save()
        fs.add(cr)
        cr.clip()
        pits = []
        for i in range(holes if q.detail >= 2 else max(3, holes // 2)):
            hx = cx + (core.hash01(i, seed + 41) - 0.5) * w_ * 0.8
            hy = cy + (core.hash01(i, seed + 42) - 0.5) * h_ * 0.8
            hr = (0.035 + 0.05 * core.hash01(i, seed + 43)) * min(w_, h_) * 1.4 + 0.4
            pits.append((hx, hy, hr * 1.3, hr * 0.85, (core.hash01(i, seed + 44) - 0.5) * 1.2))
        cr.new_path()
        for hx, hy, a_, b_, ang in pits:
            core.ellipse(cr, hx, hy, a_, b_, ang)
        core.src(cr, core.mix(p.shadow, p.line, 0.25), 0.85)
        cr.fill()
        for hx, hy, a_, b_, ang in pits:          # the lit lower lip of each pit
            core.ellipse(cr, hx + a_ * 0.15, hy + b_ * 0.45, a_ * 0.75, b_ * 0.4, ang)
        core.src(cr, p.hi, 0.7)
        cr.fill()
        cr.restore()
    return p


def draw_bread(cr, x, y, size=LOAF, light=None, t=0.0, angle=0.0, state="loaf", face=1.0, tear=0.0, seed=0,
               scale=1.0, detail=None):
    """The round crusty loaf (golden boule, three scored ears, a dusting of flour).

    Anchor (x, y) = the loaf's centre; `size` = its diameter in px at scale 1.0 (LOAF = 46, the
    gnome's loaf; pieces are about 0.45 of it). state:
      "loaf"   the whole boule; tear 0..1 pulls it apart into two halves with strands of crumb
      "half"   a torn half; its fluffy torn face points toward `face` (+1 = +x, -1 = -x)
      "piece"  a torn chunk: crust cap on top, soft crumb below (what gets handed out); seed varies it
      "crumb"  a crumb
    Outlined + house shading (it is touched). Returns PropRig(center, top, tear)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    r = size * 0.5
    if state == "loaf" and tear > 0.02:
        g = r * 0.95 * smooth(tear)
        spin = 0.14 * smooth(tear)
        phi = 0.15 + 0.8 * smooth(tear)
        for side in (-1, 1):
            cr.save()
            cr.translate(side * g, r * 0.04 * smooth(tear))
            cr.rotate(side * spin)
            _bread_half(q, r, -side, seed + (side > 0), phi)
            cr.restore()
        # the strands of crumb that stretch, then snap (~0.6)
        if tear < 0.65 and q.detail >= 1:
            pc = q.P("crumb")
            k = 1.0 - tear / 0.65
            strands = [[(-g * 0.6, r * (-0.3 + 0.22 * i)), (0.0, r * (-0.28 + 0.22 * i) + r * 0.05 * k),
                        (g * 0.6, r * (-0.3 + 0.22 * i))] for i in range(4)]
            B.detail_lines(cr, strands, r * 0.16 * k + 0.6, pc.line, 0.8)
            B.detail_lines(cr, strands, r * 0.11 * k + 0.4, pc.lit, 1.0)
    elif state == "half":
        _bread_half(q, r, face, seed, 0.95)
    elif state == "piece":
        _bread_piece(q, r, face, seed)
    elif state == "crumb":
        _bread_crumb(q, r * 0.12, seed)
    else:
        _bread_loaf(q, r, seed)
    q.end()
    return PropRig(center=q.C((0.0, 0.0)), top=q.C((0.0, -r * 0.7)), tear=q.C((0.0, 0.0)))


def _bread_loaf(q, r, seed):
    cr = q.cr
    C = PROP_COLORS
    sh, so = B.smooth_paths(cr, _loaf_pts(r), q.lw, 0.85)
    p = q.shade(sh, "crust", r * 1.4, outline=so)
    cr.save()
    sh.add(cr)
    cr.clip()
    # the darker bake underneath and the flour-dusted top
    core.ellipse(cr, 0.0, r * 0.62, r * 1.2, r * 0.32)
    core.src(cr, B.palette(q.light, Mat.of(C["crust_dk"])).lit, 0.5)
    cr.fill()
    if q.detail >= 1:
        hi = q.P("crust_hi")
        cr.new_path()
        for k in (-1, 0, 1):
            x0 = k * r * 0.42
            dy = abs(k) * r * 0.11
            core.tapered(cr, [(x0 - r * 0.22, -r * 0.40 + dy), (x0, -r * 0.60 + dy), (x0 + r * 0.22, -r * 0.42 + dy)],
                         r * 0.14, r * 0.14, profile=lambda u: r * 0.15 * math.sin(math.pi * u) + 0.4)
        sc = Path(cr)
        sc.add(cr, 0.0, r * 0.05)
        core.src(cr, p.line, 0.7)
        cr.fill()
        sc.add(cr)
        core.src(cr, hi.lit)
        cr.fill()
    if q.detail >= 2:
        core.src(cr, "#f7efdc", 0.55)                       # flour
        for i in range(12):
            core.circle(cr, (core.hash01(i, seed + 77) - 0.5) * r * 1.6, -r * 0.6 + core.hash01(i, seed + 78) * r * 0.4,
                        r * 0.03 + 0.35)
        cr.fill()
        core.src(cr, p.line, 0.35)                          # blisters
        for i in range(6):
            core.circle(cr, (core.hash01(i, seed + 79) - 0.5) * r * 1.5, -r * 0.1 + core.hash01(i, seed + 80) * r * 0.45,
                        r * 0.025 + 0.3)
        cr.fill()
    cr.restore()
    B.sheen(cr, -r * 0.35, -r * 0.5, r * 0.3, r * 0.13, angle=-0.4, alpha=0.3)


def _bread_half(q, r, face, seed, phi=0.95):
    """A torn half seen turned toward us by phi (0 = its torn face edge-on, pi/2 = face-on): the
    crusty outside of the half dome on one side and the fluffy cross-section facing `face`."""
    cr = q.cr
    sx = 1.0 if face >= 0 else -1.0
    cs, ks = max(0.3, math.cos(phi)), max(0.06, math.sin(phi))
    cr.save()
    cr.scale(sx, 1.0)                       # authored with the torn face toward +x
    # the crust shell: the outside of the half dome, foreshortened by cos(phi)
    lp = _loaf_pts(r)
    top_arc = [(px * cs, py) for px, py in lp[:22] if px <= 0.0]          # left half of the dome
    base = [(px * cs, py) for px, py in lp[22:] if px <= 0.0]             # its base, right -> left
    shell = top_arc + [(r * 0.05, -r * 0.5), (r * 0.08, 0.0), (r * 0.05, r * 0.44)] + base
    sh, so = B.smooth_paths(cr, shell, q.lw, 0.8)
    p = q.shade(sh, "crust", r * 1.1, outline=so)
    if q.detail >= 1:
        hi = q.P("crust_hi")
        cr.save()
        sh.add(cr)
        cr.clip()
        cr.new_path()
        x0 = -r * 0.42 * cs
        core.tapered(cr, [(x0 - r * 0.2 * cs, -r * 0.38), (x0, -r * 0.57), (x0 + r * 0.2 * cs, -r * 0.42)], r * 0.13,
                     r * 0.13, profile=lambda u: r * 0.14 * math.sin(math.pi * u) + 0.4)
        sc = Path(cr)
        sc.add(cr, 0.0, r * 0.05)
        core.src(cr, p.line, 0.7)
        cr.fill()
        sc.add(cr)
        core.src(cr, hi.lit)
        cr.fill()
        core.ellipse(cr, -r * 0.3, r * 0.62, r * 0.9, r * 0.28)
        core.src(cr, B.palette(q.light, Mat.of(PROP_COLORS["crust_dk"])).lit, 0.45)
        cr.fill()
        cr.restore()
    # the cross-section: the dome's profile squeezed by sin(phi), its crust a thin rim
    sec = [((px + r) * ks * 0.5 + r * 0.02, py) for px, py in _loaf_pts(r * 0.93)]
    _crumb_face(q, sec, seed, holes=10, rim=0.06)
    cr.restore()


def _bread_piece(q, r, face, seed):
    """A torn chunk (~0.5 r): ragged crumb with a crust cap over the top."""
    cr = q.cr
    s_ = r * 0.5
    pts = []
    for i in range(10):
        a = TAU * i / 10
        rag = 1.0 + 0.2 * (core.hash01(i, seed + 11) - 0.5)
        pts.append((math.cos(a) * s_ * 1.15 * rag, math.sin(a) * s_ * 0.85 * rag))
    sh, so = B.smooth_paths(cr, pts, q.lw * 0.85, 0.8)
    pc = q.shade(sh, "crumb", s_, outline=so)
    cr.save()
    sh.add(cr)
    cr.clip()
    cap = [(-s_ * 1.5, -s_ * 1.5), (s_ * 1.5, -s_ * 1.5), (s_ * 1.5, -s_ * 0.18 * face), (s_ * 0.5, -s_ * 0.42),
           (-s_ * 0.5, -s_ * 0.26), (-s_ * 1.5, s_ * 0.1 * face)]
    crust = q.P("crust")
    cr.new_path()
    core.polygon(cr, cap)
    core.src(cr, crust.line)
    cr.fill()
    core.polygon(cr, [(px, py - q.lw * 0.7) for px, py in cap])
    core.src(cr, crust.lit)
    cr.fill()
    if q.detail >= 1:
        core.src(cr, core.mix(pc.shadow, pc.line, 0.2), 0.8)
        for i in range(4):
            core.ellipse(cr, (core.hash01(i, seed + 3) - 0.5) * s_ * 1.3, s_ * 0.2 + core.hash01(i, seed + 4) * s_ * 0.45,
                         s_ * 0.11 + 0.3, s_ * 0.08 + 0.3)
        cr.fill()
        if q.detail >= 2:
            core.src(cr, PROP_COLORS["crust_hi"], 0.8)
            core.ellipse(cr, -s_ * 0.3, -s_ * 0.62, s_ * 0.35, s_ * 0.1, -0.1)
            cr.fill()
    cr.restore()


def _bread_crumb(q, r, seed):
    cr = q.cr
    pts = [(math.cos(k * TAU / 5) * r * (0.7 + 0.5 * core.hash01(k, seed + 8)),
            math.sin(k * TAU / 5) * r * (0.7 + 0.5 * core.hash01(k, seed + 9))) for k in range(5)]
    core.polygon(cr, pts)
    core.src(cr, q.P("crust").lit)
    cr.fill()
    core.polygon(cr, [(px * 0.6 - r * 0.15, py * 0.6 - r * 0.15) for px, py in pts])
    core.src(cr, q.P("crumb").lit)
    cr.fill()


def bread_hold(state="piece", light=None, size=LOAF, face=1.0, seed=0, upright=True, rest="palm"):
    """Hold callback putting the bread in ANY hand (the dragon, the faun, the griffin, the dwarf
    receiving a piece). state "piece" | "half" | "loaf"; upright keeps it level. rest="palm"
    sits it ON an open palm (hand_out_offer: it rests in the cupped hand, above the fingers);
    rest="grip" puts it in a closed grip."""
    lift = {"piece": 0.34, "half": 0.42, "loaf": 0.5}.get(state, 0.4) * size if rest == "palm" else 0.0

    def cb(cr, f):
        cr.save()
        if upright:
            cr.rotate(-f.angle)
        if state == "piece":
            draw_bread(cr, -2.0, -4.0 - lift, size, light, 0.0, 0.0, "piece", face, seed=seed)
        elif state == "half":
            draw_bread(cr, -size * 0.1, -size * 0.12 - lift, size, light, 0.0, 0.0, "half", face, seed=seed)
        else:
            draw_bread(cr, 0.0, -size * 0.2 - lift, size, light, 0.0, 0.0, "loaf", seed=seed)
        cr.restore()
    return cb


def draw_crumbs(cr, pts, scale=1.0, light=None, seed=0, size=3.0):
    """Crumbs lying still (on a bench, the gravel): pts = [(x, y), ...] in caller coordinates.
    For crumbs in flight use fx.crumbs (and fx.crumb_landings for the pigeons)."""
    light = light or B.LIGHTS["neutral"]
    crust = B.palette(light, prop_mats()["crust"])
    crumb = B.palette(light, prop_mats()["crumb"])
    for i, (px, py) in enumerate(pts):
        r = size * scale * (0.6 + 0.8 * core.hash01(i, seed + 7))
        pp = [(px + math.cos(k * TAU / 5 + i) * r * (0.7 + 0.5 * core.hash01(i * 5 + k, seed + 8)),
               py + math.sin(k * TAU / 5 + i) * r * 0.75 * (0.7 + 0.5 * core.hash01(i * 5 + k, seed + 9))) for k in range(5)]
        core.polygon(cr, pp)
        core.src(cr, crust.lit)
        cr.fill()
        core.polygon(cr, [(px + (a - px) * 0.6 - r * 0.15, py + (b - py) * 0.6 - r * 0.15) for a, b in pp])
        core.src(cr, crumb.lit)
        cr.fill()


# ========================================================================================
# 7. THE SMILE STAMP (S4): the wooden stamp and its pink ink
# ========================================================================================

def draw_stamp(cr, x, y, scale=1.0, light=None, t=0.0, angle=0.0, ink=1.0, detail=None):
    """The tavern's wooden stamp: a turned oak knob, a block, and a felt die wet with pink ink
    (SMILE is cut into it in mirror-writing: it shows only as its print, draw_smile_mark).

    Anchor (x, y) = the middle of the die's face (the bottom); upright, 60 wide x 54 tall at
    scale 1.0. Returns PropRig(die, grip)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    wood = Mat.of(C["stamp_wood"], sheen=0.25)
    # turned handle: knob + collar + neck (one union)
    knob = [(-10.0, -52.0), (10.0, -52.0), (12.5, -44.0), (8.0, -36.0), (5.5, -33.0), (6.5, -27.0), (9.0, -22.0),
            (-9.0, -22.0), (-6.5, -27.0), (-5.5, -33.0), (-8.0, -36.0), (-12.5, -44.0)]
    ks, ko = B.smooth_paths(cr, knob, q.lw, 0.7)
    pk = q.shade(ks, wood, 20.0, outline=ko)
    if q.detail >= 1:
        B.detail_lines(cr, [[(-7.0, -35.5), (0.0, -34.5), (7.0, -35.5)]], q.lw * 0.8, pk.line, 0.5)
    bs, bo = _rrect_paths(cr, -30.0, -22.0, 60.0, 15.0, 3.0, q.lw)
    pb = q.shade(bs, wood, 15.0, outline=bo)
    if q.detail >= 2:
        B.detail_lines(cr, [[(-25.0, -15.5), (-4.0, -14.5), (20.0, -15.8)], [(-18.0, -11.0), (10.0, -10.4)]],
                       q.lw * 0.6, pb.line, 0.35)
    ds, do = _rrect_paths(cr, -28.0, -7.5, 56.0, 7.5, 1.5, q.lw)
    q.shade(ds, Mat.of(C["stamp_die"]), 7.0, outline=do, rim=0.4)
    if ink > 0:
        core.src(cr, C["smile_ink"], 0.9 * ink)
        core.rounded_rect(cr, -27.0, -2.4, 54.0, 2.6, 1.0)
        cr.fill()
    B.sheen(cr, -4.0, -46.0, 5.0, 2.4, alpha=0.3)
    q.end()
    return PropRig(die=q.C((0.0, 0.0)), grip=q.C((0.0, -34.0)))


def stamp_hold(light=None, t=0.0, ink=1.0, die_down=True):
    """Hold callback: the stamp gripped by its neck, die down (die_down keeps it upright)."""
    def cb(cr, f):
        cr.save()
        if die_down:
            cr.rotate(-f.angle)
        draw_stamp(cr, 0.0, 34.0, 1.0, light, t, 0.0, ink)
        cr.restore()
    return cb


_MARK_W, _MARK_H = 64.0, 30.0


@functools.lru_cache(maxsize=24)
def _smile_mask(text, seed, k):
    """The stamp's print as an alpha mask (k px per unit): a double border, the word in heavy
    storybook capitals with a little smile under it, then the imperfections of a hand-pressed
    stamp -- uneven pressure, speckled gaps, a slightly furry edge. Cached per (text, seed, k)."""
    import numpy as np
    from PIL import Image, ImageFilter
    W, H = int(_MARK_W * k), int(_MARK_H * k)
    surf = core.new_surface(W, H)
    c = core.new_context(surf)
    c.scale(k, k)
    c.set_source_rgb(1, 1, 1)
    c.set_line_width(2.4)
    core.rounded_rect(c, 2.5, 2.5, _MARK_W - 5.0, _MARK_H - 5.0, 5.0)
    c.stroke()
    c.set_line_width(0.9)
    core.rounded_rect(c, 6.0, 6.0, _MARK_W - 12.0, _MARK_H - 12.0, 3.0)
    c.stroke()
    fam = FONTS.label
    size = _fit(c, text, 14.0, fam, _MARK_W - 18.0, 1.2)
    core.text_path(c, text, _MARK_W / 2, _MARK_H * 0.44, size, fam, align="center", valign="cap", spacing=1.2)
    c.fill_preserve()
    c.set_line_width(0.8)                        # embolden the carved letters
    c.stroke()
    c.set_line_width(1.1)
    c.move_to(_MARK_W / 2 - 7.0, _MARK_H * 0.70)
    c.curve_to(_MARK_W / 2 - 3.0, _MARK_H * 0.79, _MARK_W / 2 + 3.0, _MARK_H * 0.79, _MARK_W / 2 + 7.0, _MARK_H * 0.70)
    c.stroke()
    surf.flush()
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(H, surf.get_stride() // 4, 4)[:, :W, 3].astype(np.float32) / 255.0
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # uneven pressure: one corner pressed lighter
    ang = rng.uniform(0, TAU)
    press = 0.78 + 0.22 * np.cos(ang) * (xx / W - 0.5) * 2 + 0.22 * np.sin(ang) * (yy / H - 0.5) * 2
    noise = core.noise_array(W, H, scale=max(2.0, 3.0 * k), octaves=3, seed=seed + 5)
    speck = np.clip((noise - 0.38) * 6.0, 0.0, 1.0)
    a = a * np.clip(press - speck * 0.75, 0.1, 1.0)
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.35 * k))
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = np.asarray(im)
    data = bytearray(arr.tobytes())
    out = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, W, H, W * 4)
    return out, data


def draw_smile_mark(cr, x, y, scale=1.0, angle=-0.12, ink=1.0, seed=0, text="SMILE", color=None):
    """The stamp's pink ink print: SMILE in a double border, slightly rotated, unevenly inked.

    Anchor (x, y) = its centre; 64 x 30 at scale 1.0 (on the back of the dragon's hand use
    scale ~0.4, see smile_stamp()). ink 0..1 fades it (a fresh print is ~0.9). Cost ~0.1 ms
    (the print is a cached mask)."""
    if ink <= 0.01:
        return
    dev = scale * B.device_scale(cr)
    k = 2 ** max(0, min(4, math.ceil(math.log2(max(dev, 1e-3) * 1.2))))
    mask, _keep = _smile_mask(text, int(seed), int(k))
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(scale / k, scale / k)
    core.src(cr, color or PROP_COLORS["smile_ink"], clamp(ink) * 0.92)
    cr.mask_surface(mask, -_MARK_W * k / 2, -_MARK_H * k / 2)
    cr.restore()


def smile_stamp(size=0.52, angle=-0.1, ink=1.0, seed=0):
    """`stamp=` callback for the dragon's look_at_hand: the SMILE print on the back of his hand
    (hand-aligned units, x along the fingers)."""
    def cb(cr):
        draw_smile_mark(cr, 2.0, 0.5, size, angle, ink, seed)
    return cb


# ========================================================================================
# 8. THE BRASS TILL (S2): bell, keys, crank, pop-up flags and a curling parchment receipt
# ========================================================================================

def _ribbon_spine(x0, y0, length, ang0=-math.pi / 2, curl=5.5, step=3.0, power=2.2, ref=110.0):
    """Centre line of a strip that rises from (x0, y0) and curls more and more toward its end:
    the turning angle grows as (s / ref) ** power * curl."""
    pts = [(x0, y0)]
    x, y = x0, y0
    n = max(2, int(length / step))
    for i in range(1, n + 1):
        s_ = length * i / n
        th = ang0 - curl * (s_ / ref) ** power
        x += math.cos(th) * length / n
        y += math.sin(th) * length / n
        pts.append((x, y))
    return pts


def draw_till(cr, x, y, scale=1.0, light=None, t=0.0, ring=None, receipt=0.0, pressed=None, drawer=0.0,
              detail=None):
    """The apothecary's brass till: an engraved brass cabinet on an oak plinth, eight ivory keys
    (Cistercian numerals, like the speaking stone), a side crank, a bell on a curly bracket,
    little number flags that pop up when it rings, and a parchment receipt that curls out.

    Anchor (x, y) = bottom centre (it stands on the counter); about 136 wide x 130 tall at scale
    1.0 (+ the receipt). ring = the time (local s) the key went down: the bell rocks and dings,
    the flags pop. receipt 0..1 = how far the strip has come out (animate after the ring).
    pressed = key 1..8 held down; drawer 0..1 opens the cash drawer.
    Returns PropRig(key, bell, slot, receipt_end)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    brass = q.M["brass"]
    since = (t - ring) if ring is not None else -1.0
    # the receipt (behind the crest, in front of the cabinet top)
    rec_len = 96.0 * clamp(receipt)
    # ---- the oak plinth + the cash drawer
    ps, po = _rrect_paths(cr, -58.0, -19.0, 116.0, 19.0, 4.0, q.lw)
    pp = q.shade(ps, "oak", 19.0, outline=po)
    dy = 7.0 * smooth(clamp(drawer))
    if drawer > 0.02:
        core.src(cr, pp.line)
        cr.rectangle(-40.0, -15.5, 80.0, 4.0 + dy)
        cr.fill()
        if q.detail >= 1:                        # coins glint in the open drawer
            core.src(cr, C["brass_lt"], 0.9)
            for i in range(4):
                core.ellipse(cr, -26 + i * 15, -13.0 + dy * 0.6, 4.5, 1.6)
            cr.fill()
    ds, do = _rrect_paths(cr, -40.0, -15.0 + dy, 80.0, 12.0, 2.0, q.lw * 0.8)
    pd = q.shade(ds, "oak_dk", 12.0, outline=do, rim=0.5)
    core.circle(cr, 0.0, -9.0 + dy, 2.6)
    core.src(cr, B.palette(q.light, brass).lit)
    cr.fill()
    # ---- the cabinet (trapezoid, rounded shoulders) + the arched crest: one brass union
    cab = [(-52.0, -19.0), (52.0, -19.0), (47.0, -84.0), (44.0, -92.0), (36.0, -95.0), (-36.0, -95.0),
           (-44.0, -92.0), (-47.0, -84.0)]
    crest = [(-30.0, -93.0), (-30.0, -104.0), (-22.0, -114.0), (-8.0, -119.0), (8.0, -119.0), (22.0, -114.0),
             (30.0, -104.0), (30.0, -93.0)]
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(cab, q.lw), 0.35)
    core.smooth_closed(cr, B.offset_closed(crest, q.lw), 0.6)
    core.src(cr, B.palette(q.light, brass).line)
    cr.fill()
    if rec_len > 1.0:
        _receipt(q, -38.0, -95.0, rec_len)
    cr.new_path()
    core.smooth_closed(cr, cab, 0.35)
    core.smooth_closed(cr, crest, 0.6)
    pb = q.shade(Path(cr), brass, 70.0)
    if q.detail >= 1:
        # engraved filigree on the front panel and the crest
        scrolls = []
        for sx in (-1, 1):
            scrolls.append([(sx * 6.0, -58.0), (sx * 18.0, -66.0), (sx * 30.0, -60.0), (sx * 34.0, -70.0), (sx * 26.0, -78.0),
                            (sx * 18.0, -72.0)])
            scrolls.append([(sx * 8.0, -104.0), (sx * 18.0, -110.0), (sx * 25.0, -104.0)])
        scrolls.append([(-40.0, -50.0), (0.0, -51.5), (40.0, -50.0)])
        B.detail_lines(cr, scrolls, q.lw * 0.75, pb.line, 0.55)
        # the number-flag slot in the crest
        core.src(cr, pb.line)
        core.rounded_rect(cr, -20.0, -104.0, 40.0, 4.5, 1.5)
        cr.fill()
    # pop-up flags (they rise out of the crest's slot when it rings)
    pop = smooth(clamp(since / 0.18)) if since >= 0 else 0.0
    if pop > 0.01:
        for i, k in enumerate((3, 1, 7)):
            fh = 13.0 * pop * (1.0 - 0.1 * i)
            fxx = -13.0 + i * 13.0
            fs_, fo_ = _rrect_paths(cr, fxx - 5.5, -103.0 - fh, 11.0, fh, 1.5, q.lw * 0.7)
            q.shade(fs_, "ivory", 8.0, outline=fo_, rim=0.5)
            if q.detail >= 1 and fh > 7:
                B.detail_lines(cr, _cistercian(k, fxx + 0.5, -103.0 - fh * 0.55, 7.0), 1.0, C["ink"], 0.85)
        core.src(cr, pb.line)
        core.rounded_rect(cr, -20.0, -104.0, 40.0, 4.5, 1.5)
        cr.fill()
    # ---- the key bed and eight ivory keys
    ks, ko = _rrect_paths(cr, -46.0, -46.0, 92.0, 27.0, 4.0, q.lw * 0.8)
    pk = q.shade(ks, brass, 27.0, outline=ko, rim=0.5)
    ivory = q.P("ivory")
    key_pts = []
    for row in range(2):
        for col_ in range(4):
            k = row * 4 + col_ + 1
            kx_, ky_ = -27.0 + col_ * 18.0, -38.0 + row * 12.0
            down = 1.8 if pressed == k else 0.0
            key_pts.append((kx_, ky_ + down))
            core.circle(cr, kx_, ky_ + 1.2, 6.3)
            core.src(cr, pk.line)
            cr.fill()
            core.circle(cr, kx_, ky_ + down, 5.3)
            core.src(cr, ivory.lit if not down else ivory.shadow)
            cr.fill()
            if q.detail >= 1:
                B.detail_lines(cr, _cistercian(k, kx_ + 0.4, ky_ + down, 6.0), 0.9, C["ink"], 0.8)
    # ---- the crank on the right side
    cs_, co_ = B.tube_paths(cr, [(50.0, -60.0), (62.0, -60.0), (66.0, -48.0), (66.0, -38.0)], [3.0, 2.8, 2.6, 2.6], q.lw)
    q.shade(cs_, "iron", 6.0, outline=co_, rim=0.6)
    gs, go = B.ellipse_paths(cr, 66.0, -33.0, 4.6, 8.0, q.lw)
    q.shade(gs, "oak_dk", 8.0, outline=go, rim=0.6)
    core.circle(cr, 50.0, -60.0, 4.5)
    core.src(cr, pb.lit)
    cr.fill()
    # ---- the bell on its curly bracket (it rocks when struck)
    bs, bo = B.tube_paths(cr, [(0.0, -118.0), (0.0, -126.0), (5.0, -132.0), (0.0, -138.0)], [2.2, 2.0, 1.8, 1.6], q.lw)
    q.shade(bs, brass, 4.0, outline=bo, rim=0.6)
    rock = 0.0
    if since >= 0:
        rock = 0.38 * B.wobble(t, ring, freq=5.5, decay=3.5)
    cr.save()
    cr.translate(0.0, -137.0)
    cr.rotate(rock)
    bell = [(-3.0, 0.0), (3.0, 0.0), (6.0, 5.0), (8.5, 12.0), (10.5, 15.0), (-10.5, 15.0), (-8.5, 12.0), (-6.0, 5.0)]
    bs2, bo2 = B.smooth_paths(cr, bell, q.lw, 0.6)
    pbell = q.shade(bs2, brass, 14.0, outline=bo2)
    core.circle(cr, 0.0, 16.5, 2.2)
    core.src(cr, pbell.line)
    cr.fill()
    B.sheen(cr, -3.5, 7.0, 2.5, 4.0, angle=0.3, alpha=0.5)
    cr.restore()
    if 0.0 <= since < 0.8 and q.detail >= 1:
        # the "ding": curved sound strokes either side of the bell, and a glint
        u = since / 0.8
        a = (1.0 - u) ** 1.5
        arcs = []
        for sx in (-1, 1):
            for k in range(2):
                rr = 16.0 + 7.0 * k + 10.0 * u
                arcs.append([(sx * rr * math.cos(a_), -128.0 + rr * math.sin(a_)) for a_ in
                             [(-0.5 + j * 0.25) * (1 if sx > 0 else -1) + (0 if sx > 0 else math.pi) for j in range(5)]])
        B.detail_lines(cr, arcs, 1.6, pb.line, 0.8 * a)
        fx.sparkle(cr, 9.0, -134.0, 9.0 * a + 1.0, "#fff6d0", a)
    q.end()
    end = _ribbon_spine(-38.0, -95.0, rec_len, -math.pi / 2 - 0.1, 4.2, 3.0, 1.7, 70.0)[-1] if rec_len > 1.0 else (-38.0, -95.0)
    return PropRig(key=q.C(key_pts[1]), bell=q.C((0.0, -128.0)), slot=q.C((-38.0, -95.0)), receipt_end=q.C(end))


def _receipt(q, x0, y0, length):
    """The parchment receipt: a strip rising from the slot and curling back over itself, with
    rows of tiny rune numerals and a ruled total near its end."""
    cr = q.cr
    spine = _ribbon_spine(x0, y0, length, ang0=-math.pi / 2 - 0.1, curl=4.2, power=1.7, ref=70.0)
    rs, ro = B.taper_paths(cr, spine, 10.5, 10.5, q.lw * 0.8, cap=False)
    pr = q.shade(rs, "parchment", 5.0, outline=ro, rim=0.4)
    if q.detail >= 1:
        marks = []
        acc = 0.0
        for i in range(1, len(spine)):
            (ax, ay), (bx, by) = spine[i - 1], spine[i]
            seg = math.hypot(bx - ax, by - ay)
            acc += seg
            if 10.0 < acc < length - 4.0 and i % 3 == 0:
                tx, ty = (bx - ax) / (seg or 1), (by - ay) / (seg or 1)
                nx, ny = -ty, tx
                wl = 4.0 + 3.0 * core.hash01(i, 5)
                marks.append([(bx + nx * -3.4, by + ny * -3.4), (bx + nx * (-3.4 + wl * 0.8), by + ny * (-3.4 + wl * 0.8))])
        B.detail_lines(cr, marks, 0.8, PROP_COLORS["ink"], 0.6)


# ========================================================================================
# 9. BENCHES AND THE STOOL (projected with B.Proj like the cast, so sitters line up)
# ========================================================================================

BENCH_SEAT_H = B.BENCH_SEAT_H      # 125: seat top above the ground at the sitter's position
BENCH_DEPTH = 84.0                 # seat depth (front edge 42 in front of a sitter's anchor)
BENCH_LEN = 440.0                  # default length: four of the cast, or two with room between


@dataclass
class BenchRig:
    """Where to put the sitters on a bench (all in the caller's coordinates).

    place(u)  the GROUND anchor for a sitter at fraction u (0 = the left end, 1 = the right end
              of the bench in its own X): pass it as draw_<creature>(cr, *rig.place(u), ...)
              with pose.sit = 1 and seat_h = rig.seat_h.
    seat(u)   the point on the seat surface there (pose.anchor = "seat").
    """
    origin: tuple = (0.0, 0.0)
    scale: float = 1.0
    yaw: float = 0.0
    elev: float = 0.12
    length: float = BENCH_LEN
    seat_h: float = BENCH_SEAT_H
    ends: list = field(default_factory=list)
    back_top: tuple = (0.0, 0.0)
    _m: object = None

    def _pt(self, X, Y, Z=0.0):
        p = B.Proj(self.yaw, self.elev).xy((X, Y, Z))
        return self._m(p)

    def place(self, u):
        return self._pt((u - 0.5) * (self.length - 60.0), 0.0)

    def seat(self, u):
        return self._pt((u - 0.5) * (self.length - 60.0), -self.seat_h)


def _norm_ccw(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return pts if a >= 0 else pts[::-1]


def _tube_pair(pts, radii, lw, samples=5, tension=0.8):
    """Tube outline polygons (shape, dilated outline) wound the same way, so many of them can
    form ONE union (one outline fill, one shading pass) without winding holes."""
    a, b = B.tube_outline(pts, radii, samples, tension, (0.0, lw))
    return _norm_ccw(a), _norm_ccw(b)


def _union_shade(q, pairs, mat, size, rim=1.0, smooth_t=0.9):
    """Fill the outlines of several (shape, outline) polygon pairs at once, then shade their
    union in one pass (the house recipe for one material)."""
    cr = q.cr
    if not pairs:
        return None
    cr.new_path()
    for _a, o in pairs:
        core.smooth_closed(cr, o, smooth_t)
    p = q.P(mat)
    core.src(cr, p.line)
    cr.fill()
    for a, _o in pairs:
        core.smooth_closed(cr, a, smooth_t)
    return q.shade(Path(cr), mat, size, rim=rim)


def _box_hull(proj, x0, x1, y0, y1, z0, z1):
    pts = [proj.xy((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    return core.convex_hull(pts)


def _plank(q, proj, x0, x1, y0, y1, z0, z1, mat, grain=True, top_face=True):
    """A wooden board as a projected box: outline + cel tones, a lighter top face, grain."""
    cr = q.cr
    hull = _box_hull(proj, x0, x1, y0, y1, z0, z1)
    off = _norm_ccw(B.offset_closed(_norm_ccw(hull), q.lw))
    cr.new_path()
    core.polygon(cr, off)
    p = q.P(mat)
    core.src(cr, p.line)
    cr.fill()
    core.polygon(cr, hull)
    size = max(4.0, min(abs(y1 - y0), abs(z1 - z0)) * 1.2)
    p = q.shade(Path(cr), mat, size, rim=0.7)
    if top_face and q.light.direction[1] < 0:
        top = [proj.xy((x0, y0, z0)), proj.xy((x1, y0, z0)), proj.xy((x1, y0, z1)), proj.xy((x0, y0, z1))]
        core.polygon(cr, top)
        core.src(cr, p.hi, 0.28)
        cr.fill()
    if grain and q.detail >= 2:
        lines = []
        for k in range(2):
            zz = lerp(z0, z1, 0.3 + 0.4 * k)
            yy = y0 + (y1 - y0) * 0.02
            a_ = proj.xy((lerp(x0, x1, 0.05 + 0.1 * k), yy, zz))
            b_ = proj.xy((lerp(x0, x1, 0.55 + 0.3 * k), yy, zz))
            lines.append([a_, b_])
        B.detail_lines(cr, lines, q.lw * 0.6, p.line, 0.35)
    return p


def _plane_matrix(proj, origin, U, V):
    """cairo Matrix mapping (u, v) on a flat 3D board (origin + u U + v V) to the projected 2D
    plane: B.Proj is linear, so any flat face projects affinely and can be drawn in its own
    coordinates (carvings, lettering, cut-outs)."""
    ox, oy = proj.xy(origin)
    ux, uy = proj.xy(U)
    vx, vy = proj.xy(V)
    return cairo.Matrix(ux, uy, vx, vy, ox, oy)


def _quatrefoil(cx, cy, r, n=28, rev=False):
    """A Gothic quatrefoil cut-out (four lobes) as points."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        rr = r * (0.62 + 0.38 * abs(math.cos(2 * a)) ** 0.7)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts[::-1] if rev else pts


def _crest_board(q, proj, L, seat_h, oak, holes=3):
    """The bench's carved top back board: an arched top edge, three quatrefoil cut-outs (you see
    through them), drawn in the board's own plane through an affine matrix."""
    cr = q.cr
    hb0, hb1 = 74.0, 108.0                         # board from 74 to 108 above the seat (+ the arch)
    zb = lambda v: -48.0 - 0.22 * v                # noqa: E731  (the reclined back plane)
    origin = (0.0, -seat_h, zb(0.0))
    U = (1.0, 0.0, 0.0)
    V = (0.0, -1.0, -0.22)                         # up the reclined board
    m = _plane_matrix(proj, origin, U, V)
    w = L / 2 - 4.0
    top = [(-w + w * 2 * i / 24, hb1 + 9.0 * math.sin(math.pi * i / 24) ** 1.5) for i in range(25)]
    outer = [(-w, hb0)] + top + [(w, hb0)]
    lw = q.lw
    cr.save()
    cr.transform(m)
    sgn_out = 1.0
    holes = 5 if L > 300 else 3
    step = 2 * w * 0.78 / (holes - 1)
    hole_pts = [_quatrefoil(-w * 0.78 + k * step, (hb0 + hb1) * 0.5 + 2.5, 13.5) for k in range(holes)]
    # orientation: the holes are wound against the board so nonzero filling leaves them open
    outer_ccw = _norm_ccw(outer)
    o_off = _norm_ccw(B.offset_closed(outer_ccw, lw))
    holes_cw = [_norm_ccw(h)[::-1] for h in hole_pts]
    holes_in = [_norm_ccw(B.offset_closed(_norm_ccw(h), -lw))[::-1] for h in hole_pts]
    cr.new_path()
    core.polygon(cr, o_off)
    for h in holes_in:
        core.smooth_closed(cr, h, 0.9)
    pal = q.P(oak)
    core.src(cr, pal.line)
    cr.fill()
    core.polygon(cr, outer_ccw)
    for h in holes_cw:
        core.smooth_closed(cr, h, 0.9)
    p = q.shade(Path(cr), oak, 20.0, rim=0.7)
    if q.detail >= 2:
        B.detail_lines(cr, [[(-w * 0.9, hb0 + 5.0), (-w * 0.2, hb0 + 4.0)], [(w * 0.15, hb1 - 4.0), (w * 0.85, hb1 - 2.0)]],
                       lw * 0.6, p.line, 0.35)
    cr.restore()
    return sgn_out


def _spiral(cx, cy, r0, turns=1.25, a0=0.0, n=14, sign=1.0):
    """A wrought-iron scroll: an inward spiral (2D points)."""
    out = []
    for i in range(n + 1):
        u = i / n
        a = a0 + sign * u * turns * TAU
        rr = r0 * (1.0 - 0.75 * u)
        out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return out


def _end_frame(xe, sh):
    """Wrought-iron end frame of a garden bench at X = xe, as bars of 3D points (Z forward),
    grouped by where they sit in depth order: "post" (the back leg rising into the scrolled
    back post, and the seat rail: behind the backrest), "leg" (the front leg and its foot
    scroll: under the seat) and "arm" (the armrest, its scroll and support: above the seat)."""
    g = {"post": [], "leg": [], "arm": []}
    g["post"].append(([(xe, 0.0, -38.0), (xe, -40.0, -43.0), (xe, -sh, -46.0), (xe, -sh - 40.0, -54.0),
                       (xe, -sh - 80.0, -62.0), (xe, -sh - 104.0, -68.0)], 3.8))
    sc = _spiral(-62.0, -sh - 112.0, 9.0, 1.1, a0=math.pi * 0.5, n=12, sign=-1.0)
    g["post"].append(([(xe, -sh - 104.0, -68.0)] + [(xe, y_, z_) for z_, y_ in sc], 3.0))
    g["post"].append(([(xe, -sh + 9.0, -46.0), (xe, -sh + 9.0, 0.0), (xe, -sh + 9.0, 44.0)], 3.4))
    g["leg"].append(([(xe, 0.0, 50.0), (xe, -22.0, 44.0), (xe, -64.0, 41.0), (xe, -sh + 6.0, 44.0)], 3.8))
    fs = _spiral(56.0, -8.0, 7.0, 1.0, a0=math.pi * 0.25, n=10, sign=1.0)
    g["leg"].append(([(xe, 0.0, 50.0)] + [(xe, y_, z_) for z_, y_ in fs], 2.6))
    g["arm"].append(([(xe, -sh - 52.0, -56.0), (xe, -sh - 56.0, -20.0), (xe, -sh - 52.0, 20.0),
                      (xe, -sh - 45.0, 44.0)], 3.6))
    asc = _spiral(44.0, -sh - 36.0, 9.0, 1.2, a0=-math.pi * 0.5, n=12, sign=1.0)
    g["arm"].append(([(xe, -sh - 45.0, 44.0)] + [(xe, y_, z_) for z_, y_ in asc], 3.0))
    g["arm"].append(([(xe, -sh - 36.0, 44.0), (xe, -sh - 14.0, 45.0), (xe, -sh + 6.0, 44.0)], 3.2))
    return g


def draw_garden_bench(cr, x, y, scale=1.0, light=None, t=0.0, yaw=0.0, elev=0.12, length=BENCH_LEN,
                      seat_h=BENCH_SEAT_H, part="all", detail=None, crumbs=0):
    """The garden bench (S6-S8): oak slats on wrought-iron end frames with scrolled arms.

    Anchor (x, y) = the ground point at the middle of the bench, below the seat (the same
    point a sitter at u = 0.5 is anchored to). Built in 3D and projected with B.Proj(yaw, elev)
    exactly like the cast, so it turns continuously: yaw 0 = front view, +-0.5 = 3/4 front,
    +-1.45 = side view (the iron scrolls in profile). At scale 1.0: seat top seat_h = 125 above
    the ground (BENCH_SEAT_H), seat depth BENCH_DEPTH = 84 (front edge 42 in front of the
    sitter's anchor, backrest 46 behind it), back top ~245, length BENCH_LEN = 400 (param).
    part: "all", "back" (everything but the NEAR end's front leg and arm) and "front" (just
    those): draw "back", then the sitters, then "front" (in the front view there is no near
    end: "back" is the whole bench). crumbs = n crumbs lying on the seat.
    Returns a BenchRig: rig.place(u) / rig.seat(u) for sitters."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    proj = B.Proj(yaw, elev)
    L = length
    xe = L / 2 - 16.0
    near = None if abs(yaw) <= 0.02 else (-xe if yaw > 0 else xe)    # yaw > 0: the -X end is nearer
    oak = Mat.of("#8E6A44", sheen=0.15)
    iron = q.M["iron"]
    frames = {e: _end_frame(e, seat_h) for e in (-xe, xe)}

    def pairs(bars):
        return [_tube_pair([proj.xy(p3) for p3 in pts], [rad] * len(pts), q.lw) for pts, rad in bars]

    if part in ("all", "back"):
        _union_shade(q, pairs(frames[-xe]["post"] + frames[xe]["post"]), iron, 8.0, rim=0.6)
        _crest_board(q, proj, L, seat_h, oak)                 # the carved top board, then two slats
        for hh in (52.0, 26.0):
            zb = -48.0 - 0.22 * hh
            _plank(q, proj, -L / 2 + 6, L / 2 - 6, -seat_h - hh - 10.0, -seat_h - hh + 10.0, zb - 3.0, zb + 3.0, oak,
                   top_face=False)
        far_ends = [e for e in (-xe, xe) if e != near]
        _union_shade(q, pairs(sum((frames[e]["leg"] for e in far_ends), [])), iron, 8.0, rim=0.6)
        for k in range(4):                                    # seat slats, back to front
            z0 = -42.0 + k * 22.0
            _plank(q, proj, -L / 2, L / 2, -seat_h - 6.0, -seat_h + 1.0, z0, z0 + 18.0, oak)
        if crumbs:
            pts = [proj.xy(((core.hash01(i, 5) - 0.5) * L * 0.8, -seat_h - 6.5, (core.hash01(i, 6) - 0.5) * 60))
                   for i in range(crumbs)]
            draw_crumbs(cr, pts, 1.0, q.light, seed=3, size=2.2)
        _union_shade(q, pairs(sum((frames[e]["arm"] for e in far_ends), [])), iron, 8.0, rim=0.6)
        # the scrolled iron apron under the front edge of the seat (it reads in every view)
        apron = []
        span = xe - 26.0
        for sx in (-1.0, 1.0):
            for k in range(2):
                cx_ = sx * span * (0.28 + 0.5 * k)
                sc = _spiral(0.0, 0.0, 9.0, 1.15, a0=math.pi, n=12, sign=sx)
                pts = [(cx_ - sx * 22.0, -seat_h + 6.0, 43.0), (cx_ - sx * 8.0, -seat_h + 14.0, 43.0)]
                pts += [(cx_ + px * sx, -seat_h + 16.0 + py, 43.0) for px, py in sc]
                apron.append((pts, 2.2))
        apron.append(([(-span, -seat_h + 6.0, 43.0), (span, -seat_h + 6.0, 43.0)], 2.4))
        _union_shade(q, pairs(apron), iron, 6.0, rim=0.5)
    if part in ("all", "front") and near is not None:
        _union_shade(q, pairs(frames[near]["leg"] + frames[near]["arm"]), iron, 8.0, rim=0.6)
    q.end()
    rig = BenchRig(origin=q.C((0.0, 0.0)), scale=scale, yaw=yaw, elev=elev, length=L, seat_h=seat_h)
    rig._m = q.C
    rig.ends = [q.C(proj.xy((e, 0.0, 0.0))) for e in (-xe, xe)]
    rig.back_top = q.C(proj.xy((0.0, -seat_h - 104.0, -70.0)))
    return rig


STOOL_SEAT_H = 72.0                # the S1 stool: deliberately far too small for him


def draw_stool(cr, x, y, scale=1.0, light=None, t=0.0, yaw=0.3, elev=0.16, seat_h=STOOL_SEAT_H, radius=42.0,
               part="all", wobble=0.0, detail=None):
    """The little three-legged milking stool (S1), far too small for the dragon.

    Anchor (x, y) = the ground point below the seat centre (the sitter's anchor). seat top
    seat_h = 72 above the ground, seat radius 42 at scale 1.0; three splayed legs. part "back"
    (the two back legs + the seat) / "front" (the front leg) / "all". wobble rocks it a little
    (e.g. B.wobble(t, t_sit) * 0.04 when he sits down)."""
    q = _Ctx(cr, x, y, scale, wobble, light, detail)
    proj = B.Proj(yaw, elev)
    wood = Mat.of("#8a6038", sheen=0.2)
    th = 13.0
    legs = []
    for k in range(3):
        a = math.pi * 0.5 + k * TAU / 3 + 0.25
        top = (math.cos(a) * radius * 0.5, -seat_h + th, math.sin(a) * radius * 0.5)
        foot = (math.cos(a) * radius * 1.22, 0.0, math.sin(a) * radius * 1.22)
        legs.append((proj.depth(foot), top, foot))
    legs.sort(key=lambda L_: L_[0])

    def leg(top, foot):
        mid = tuple((a_ + b_) / 2 for a_, b_ in zip(top, foot))
        return _tube_pair([proj.xy(top), proj.xy(mid), proj.xy(foot)], [5.0, 4.4, 3.8], q.lw)

    if part in ("all", "back"):
        _union_shade(q, [leg(tp, ft) for d, tp, ft in legs[:2]], wood, 10.0, rim=0.6)
        # the seat: side band (a short cylinder) then the top
        side = [proj.xy((math.cos(a) * radius, -seat_h + (th if math.sin(a) > -0.05 else 0.0), math.sin(a) * radius))
                for a in [i * TAU / 32 for i in range(32)]]
        topp = [proj.xy((math.cos(a) * radius, -seat_h, math.sin(a) * radius)) for a in [i * TAU / 32 for i in range(32)]]
        hull = core.convex_hull(side + topp)
        _union_shade(q, [(_norm_ccw(hull), _norm_ccw(B.offset_closed(_norm_ccw(hull), q.lw)))],
                     Mat.of("#6e4a2a"), th * 2, rim=0.4, smooth_t=0.5)
        ts, to = B.smooth_paths(cr, topp, q.lw, 0.9)
        pt = q.shade(ts, wood, 16.0, outline=to, rim=0.9)
        if q.detail >= 2:
            g = [proj.xy((radius * (u - 0.5) * 1.3, -seat_h - 0.2, radius * 0.1 * (k - 1))) for k in range(3) for u in (0.1, 0.9)]
            B.detail_lines(cr, [[g[0], g[1]], [g[2], g[3]]], q.lw * 0.7, pt.line, 0.4)
    if part in ("all", "front"):
        _union_shade(q, [leg(tp, ft) for d, tp, ft in legs[2:]], wood, 10.0, rim=0.6)
    q.end()
    return PropRig(seat=q.C(proj.xy((0.0, -seat_h, 0.0))), ground=q.C((0.0, 0.0)))


def draw_washhouse_bench(cr, x, y, scale=1.0, light=None, t=0.0, yaw=0.0, elev=0.12, length=260.0,
                         seat_h=BENCH_SEAT_H, detail=None):
    """The wash-house's plain plank bench (the elf's, S1): a medieval "form" -- a thick oak plank
    on two splayed slab ends with V-cut feet, wedged through the top, a stretcher between them.
    Anchor = the ground point below the middle of the seat; seat top 125 above the ground, 56
    deep, `length` long at scale 1.0. Returns a BenchRig."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    proj = B.Proj(yaw, elev)
    oak = Mat.of("#7c5636", sheen=0.15)
    L = length
    ends = sorted((-L / 2 + 34.0, L / 2 - 34.0), key=lambda e: proj.depth((e, 0, 0)))
    for xe in ends:
        # a slab end splayed outward a little: built from its four corners in 3D
        sx = 1.0 if xe > 0 else -1.0
        hull = core.convex_hull([proj.xy(p3) for p3 in (
            (xe - 9.0, -seat_h + 10.0, -22.0), (xe + 9.0, -seat_h + 10.0, -22.0), (xe - 9.0, -seat_h + 10.0, 22.0),
            (xe + 9.0, -seat_h + 10.0, 22.0), (xe - 9.0 + sx * 10.0, 0.0, -26.0), (xe + 9.0 + sx * 10.0, 0.0, -26.0),
            (xe - 9.0 + sx * 10.0, 0.0, 26.0), (xe + 9.0 + sx * 10.0, 0.0, 26.0))])
        _union_shade(q, [(_norm_ccw(hull), _norm_ccw(B.offset_closed(_norm_ccw(hull), q.lw)))], oak, 14.0, rim=0.6,
                     smooth_t=0.2)
        if q.detail >= 1:                                  # the V-cut between its feet
            a_ = proj.xy((xe + sx * 10.0 + 9.0 * sx, 0.0, -9.0))
            b_ = proj.xy((xe + sx * 7.0 + 9.0 * sx, -20.0, 0.0))
            c_ = proj.xy((xe + sx * 10.0 + 9.0 * sx, 0.0, 9.0))
            core.src(cr, B.palette(q.light, oak).line, 0.9)
            core.polygon(cr, [a_, b_, c_])
            cr.fill()
    _plank(q, proj, -L / 2 + 40.0, L / 2 - 40.0, -seat_h * 0.4 - 6.0, -seat_h * 0.4 + 6.0, -5.0, 5.0, oak, grain=False)
    p = _plank(q, proj, -L / 2, L / 2, -seat_h - 2.0, -seat_h + 11.0, -28.0, 28.0, oak)
    if q.detail >= 1:                                      # the wedged tenons through the top
        for xe in ends:
            core.polygon(cr, [proj.xy((xe - 6.0, -seat_h - 2.2, -6.0)), proj.xy((xe + 6.0, -seat_h - 2.2, -6.0)),
                              proj.xy((xe + 6.0, -seat_h - 2.2, 6.0)), proj.xy((xe - 6.0, -seat_h - 2.2, 6.0))])
        core.src(cr, p.shadow, 0.8)
        cr.fill()
    q.end()
    rig = BenchRig(origin=q.C((0.0, 0.0)), scale=scale, yaw=yaw, elev=elev, length=L, seat_h=seat_h)
    rig._m = q.C
    rig.ends = [q.C(proj.xy((e, 0.0, 0.0))) for e in (-L / 2, L / 2)]
    return rig


# ========================================================================================
# 10. LIGHTS: the iron lantern post, wisp lamps, strings of paper lanterns
# ========================================================================================

def _solid(cr, color, alpha=None):
    core.src(cr, color, alpha)
    cr.fill()


def _tones(light, c, **kw):
    """(lit, shadow, deep, rim) tones of a set-dressing colour under the scene light."""
    p = B.palette(light, Mat.of(c, **kw))
    return p.lit, p.shadow, p.deep, p.rim


def draw_lantern_post(cr, x, y, scale=1.0, light=None, t=0.0, lit=1.0, kind="warm", style="crook", side=1,
                      height=600.0, seed=0, detail=None):
    """An iron lantern post: a flared foot, a twisted-iron column and a glass-and-iron lantern
    with a candle in it (kind "warm") or a caged magic wisp (kind "wisp", cold green-cyan).

    Anchor (x, y) = the foot on the ground. style "crook": the lantern hangs from a scrolled arm
    on the `side` (+1 right / -1 left) of the post, its centre ~height-50 above the ground;
    "top": it sits on the post's head (centre ~height+30). height = 600 at scale 1.0 (the dragon
    is 520). lit 0..1 (S7: animate it to light up). Set dressing: no outline, it can be cached
    in a Layer when nothing else on it moves -- but the flame flickers, so draw the lantern part
    per frame. Light it with lantern_light(lc, rig, ...). Returns PropRig(lamp, flame, top, ground)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    il, ish, ideep, irim = _tones(q.light, C["iron"])
    H = height
    # the foot: a flared bell with two mouldings
    foot = [(-30.0, 0.0), (-26.0, -8.0), (-14.0, -20.0), (-10.0, -34.0), (-12.0, -40.0), (-9.0, -48.0),
            (9.0, -48.0), (12.0, -40.0), (10.0, -34.0), (14.0, -20.0), (26.0, -8.0), (30.0, 0.0)]
    core.smooth_open(cr, foot)
    cr.close_path()
    _solid(cr, il)
    core.polygon(cr, [(2.0, 0.0), (30.0, 0.0), (26.0, -8.0), (14.0, -20.0), (10.0, -34.0), (12.0, -40.0),
                      (9.0, -48.0), (3.0, -48.0)])
    _solid(cr, ish, 0.85)
    # the column, tapering, a twisted bar: diagonal light stripes
    top_y = -H + 40.0
    col = [(-7.5, -46.0), (7.5, -46.0), (5.0, top_y), (-5.0, top_y)]
    core.polygon(cr, col)
    _solid(cr, il)
    core.polygon(cr, [(1.5, -46.0), (7.5, -46.0), (5.0, top_y), (1.0, top_y)])
    _solid(cr, ish, 0.8)
    if q.detail >= 1:
        cr.save()
        core.polygon(cr, col)
        cr.clip()
        core.src(cr, core.mix(il, irim, 0.5), 0.55)
        yy = -50.0
        while yy > top_y:
            cr.move_to(-8.0, yy)
            cr.line_to(8.0, yy - 9.0)
            cr.line_to(8.0, yy - 12.0)
            cr.line_to(-8.0, yy - 3.0)
            cr.close_path()
            yy -= 16.0
        cr.fill()
        cr.restore()
    for ry in (-60.0, -H * 0.5, top_y + 10.0):                # collars
        core.rounded_rect(cr, -9.0, ry - 3.0, 18.0, 6.0, 2.5)
        _solid(cr, il)
        core.rounded_rect(cr, -9.0, ry - 3.0, 18.0, 2.0, 1.0)
        _solid(cr, irim, 0.35)
    if style == "top":
        lx, ly = 0.0, top_y - 46.0
        cup = [(-16.0, top_y + 2.0), (16.0, top_y + 2.0), (8.0, top_y + 12.0), (-8.0, top_y + 12.0)]
        core.polygon(cr, cup)
        _solid(cr, il)
    else:
        # the scrolled arm, then the lantern hanging from its tip
        sx = 1.0 if side >= 0 else -1.0
        arm = [(0.0, top_y + 4.0), (sx * 22.0, top_y - 10.0), (sx * 50.0, top_y - 14.0), (sx * 72.0, top_y - 8.0)]
        arm_sp = core.spline(arm, 6)
        core.tapered(cr, arm_sp, 7.0, 6.0)
        _solid(cr, il)
        sc = _spiral(sx * 72.0 + sx * 0.0, top_y + 2.0, 10.0, 1.2, a0=-math.pi / 2, n=14, sign=sx)
        core.tapered(cr, [arm_sp[-1]] + sc, 5.5, 2.5)
        _solid(cr, il)
        brace = _spiral(sx * 22.0, top_y + 14.0, 12.0, 1.0, a0=math.pi, n=12, sign=-sx)
        core.tapered(cr, [(0.0, top_y + 40.0)] + brace, 4.0, 2.0)
        _solid(cr, il)
        core.circle(cr, 0.0, top_y - 2.0, 7.0)                # the post's finial
        _solid(cr, il)
        lx, ly = sx * 58.0, top_y + 52.0
        cr.set_line_width(2.2)                               # the hook and ring
        core.src(cr, ideep)
        cr.move_to(lx, top_y - 12.0)
        cr.line_to(lx, ly - 46.0)
        cr.stroke()
    rig_l = _lantern(q, lx, ly, t, lit, kind, seed)
    q.end()
    return PropRig(lamp=q.C((lx, ly)), flame=q.C(rig_l), top=q.C((0.0, top_y)), ground=q.C((0.0, 0.0)),
                   kind=kind, lit=lit)


def _flicker(t, seed=0, amount=1.0):
    """Candle flicker 0..1+ (pure function of t)."""
    return 1.0 + amount * (0.07 * core.noise1(t * 7.3, seed) + 0.04 * math.sin(t * 19.0 + seed) + 0.03 * core.noise1(t * 23.0, seed + 3))


def _lantern(q, lx, ly, t, lit, kind, seed, w=44.0):
    """The hexagonal glass-and-iron lantern centred at (lx, ly): roof with finial and ring, three
    visible panes (lit from inside), a candle or a wisp, a tapered drip base."""
    cr = q.cr
    C = PROP_COLORS
    il, ish, ideep, irim = _tones(q.light, C["iron"])
    cr.save()
    cr.translate(lx, 0.0)                 # draw the lantern about its own vertical axis
    lx0, lx = lx, 0.0
    hw = w / 2
    top, bot = ly - 30.0, ly + 24.0
    warm = kind != "wisp"
    glow_c = C["candle"] if warm else C["wisp"]
    hot_c = C["candle_hot"] if warm else C["wisp_core"]
    lv = clamp(lit) * _flicker(t, seed) if warm else clamp(lit) * (0.9 + 0.1 * core.noise1(t * 11.0, seed))
    # glass: dark when unlit, glowing from the flame when lit
    glass = [(-hw, top), (hw, top), (hw * 0.86, bot), (-hw * 0.86, bot)]
    core.polygon(cr, glass)
    _solid(cr, core.mix("#14202a", core.mix(glow_c, "#ffffff", 0.15), clamp(lv)))
    if lv > 0.02:
        cr.save()
        core.polygon(cr, glass)
        cr.clip()
        fx.glow(cr, lx, ly + 2.0, w * 0.9, hot_c, 0.85 * lv)
        cr.restore()
        if warm:
            core.rounded_rect(cr, lx - 4.0, ly - 2.0, 8.0, 18.0, 2.0)          # the candle
            _solid(cr, core.mix("#e9dcc0", "#fff1cf", lv))
            _flame(cr, lx, ly - 3.0, 13.0, 3.8, t, seed + 5, C["flame_warm"], C["candle_hot"], clamp(lit))
        else:
            wx = lx + 2.0 * core.noise1(t * 3.0, seed + 7)
            wy = ly + 2.0 * core.noise1(t * 2.6, seed + 8)
            fx.glow(cr, wx, wy, 13.0, C["wisp_core"], lv, core_r=5.0)
    else:
        core.polygon(cr, [(-hw * 0.6, top + 4.0), (-hw * 0.3, top + 4.0), (-hw * 0.5, bot - 4.0), (-hw * 0.75, bot - 4.0)])
        _solid(cr, (0.6, 0.7, 0.8), 0.18)
    # iron frame: side posts + the two pane mullions + rims
    for px in (-hw, -hw * 0.38, hw * 0.38, hw):
        k = 0.86 if abs(px) > hw * 0.9 else 0.9
        cr.move_to(px - 2.0, top)
        cr.line_to(px + 2.0, top)
        cr.line_to(px * k + 2.0, bot)
        cr.line_to(px * k - 2.0, bot)
        cr.close_path()
    _solid(cr, il)
    # the roof: a flared hexagonal cap with a finial and a ring
    roof = [(-hw - 6.0, top + 2.0), (-hw + 2.0, top - 6.0), (-6.0, top - 20.0), (6.0, top - 20.0), (hw - 2.0, top - 6.0),
            (hw + 6.0, top + 2.0)]
    core.polygon(cr, roof)
    _solid(cr, il)
    core.polygon(cr, [(0.0, top - 20.0), (6.0, top - 20.0), (hw - 2.0, top - 6.0), (hw + 6.0, top + 2.0), (0.0, top + 2.0)])
    _solid(cr, ish, 0.8)
    core.polygon(cr, [(-hw - 6.0, top + 2.0), (-hw + 2.0, top - 6.0), (-6.0, top - 20.0), (-3.0, top - 20.0), (-hw + 5.0, top - 5.0),
                      (-hw - 2.0, top + 2.0)])
    _solid(cr, irim, 0.3)
    core.circle(cr, lx, top - 24.0, 4.5)
    _solid(cr, il)
    cr.set_line_width(2.4)
    core.src(cr, il)
    cr.arc(lx, top - 32.0, 5.0, 0, TAU)
    cr.stroke()
    # the drip base
    base = [(-hw * 0.9, bot - 2.0), (hw * 0.9, bot - 2.0), (hw * 0.55, bot + 9.0), (0.0, bot + 16.0), (-hw * 0.55, bot + 9.0)]
    core.polygon(cr, base)
    _solid(cr, il)
    core.polygon(cr, [(0.0, bot - 2.0), (hw * 0.9, bot - 2.0), (hw * 0.55, bot + 9.0), (0.0, bot + 16.0)])
    _solid(cr, ish, 0.8)
    if lv > 0.02:                       # firelight catches the iron edges
        core.rounded_rect(cr, -hw - 6.0, top + 0.5, 2 * hw + 12.0, 2.5, 1.0)
        _solid(cr, glow_c, 0.45 * lv)
    cr.restore()
    return (lx0, ly - 8.0)


def lantern_light(lc, rig, scale=1.0, t=0.0, strength=1.0, ground_y=None, pool=1.0):
    """The lantern's light for the scene's LightLayer: a big soft halo round the lamp and, if
    ground_y is given (caller coordinates), a pool of light on the ground below it.
    rig = the PropRig from draw_lantern_post."""
    lv = clamp(rig.lit) * strength
    if lv <= 0.01:
        return
    warm = rig.kind != "wisp"
    c = PROP_COLORS["candle"] if warm else PROP_COLORS["wisp"]
    fl = _flicker(t, 0, 0.6) if warm else 1.0
    lx, ly = rig.lamp
    fx.glow(lc, lx, ly, 330 * scale, c, 0.30 * lv * fl)
    fx.glow(lc, lx, ly, 90 * scale, PROP_COLORS["candle_hot"] if warm else PROP_COLORS["wisp_core"], 0.35 * lv * fl)
    if ground_y is not None and pool > 0:
        fx.light_pool(lc, lx, ground_y, 340 * scale, 70 * scale, c, 0.42 * lv * fl * pool)


def draw_wisp_lamp(cr, x, y, scale=1.0, light=None, t=0.0, seed=0, top=None, intensity=1.0, detail=None):
    """A will-o'-wisp caged in iron (S1 wash-house): a curved-bar cage hanging on a chain from
    the vault, a cold green-cyan wisp floating inside, flickering and buzzing.

    Anchor (x, y) = the cage centre; cage 40 x 56 at scale 1.0; the chain runs up to `top`
    (caller y; default 220 px above). Set dressing (no outline). Returns PropRig(center, level)
    -> wisp_light(lc, rig, scale) for the halo and the floor pool."""
    C = PROP_COLORS
    ty = (y - 220 * scale) if top is None else top
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    il, ish, ideep, irim = _tones(q.light, C["iron"])
    # flicker and the occasional buzzing dip
    buzz = core.noise1(t * 0.9, seed + 2)
    lv = intensity * (0.86 + 0.08 * core.noise1(t * 9.0, seed) + 0.04 * math.sin(t * 50.0 + seed))
    if buzz > 0.55:
        lv *= 0.6 + 0.4 * abs(math.sin(t * 31.0))
    bob = 2.0 * math.sin(t * 1.3 + seed)
    # chain
    cr.set_line_width(2.6)
    core.src(cr, ideep)
    cr.move_to(0.0, (ty - y) / scale)
    cr.line_to(0.0, -36.0)
    cr.stroke()
    if q.detail >= 1:
        core.src(cr, il)
        yy = -38.0
        while yy > (ty - y) / scale:
            core.ellipse(cr, 0.0, yy, 2.0, 3.6)
            yy -= 9.0
        cr.set_line_width(1.2)
        cr.stroke()
    # back bars of the cage
    bars_back = [-0.45, 0.45]
    cr.set_line_width(3.0)
    core.src(cr, ish)
    for k in bars_back:
        cr.move_to(0.0, -26.0)
        cr.curve_to(k * 44.0, -20.0, k * 44.0, 18.0, 0.0, 26.0)
    cr.stroke()
    # the wisp
    wx, wy = 1.5 * core.noise1(t * 2.0, seed + 5), bob
    fx.glow(cr, wx, wy, 34.0, C["wisp"], 0.55 * lv)
    fx.glow(cr, wx, wy, 11.0, C["wisp_core"], 0.95 * lv, core_r=4.5)
    if q.detail >= 1:
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        for i in range(3):
            a = t * (1.6 + 0.3 * i) + i * 2.1 + seed
            core.src(cr, C["wisp_core"], 0.7 * lv)
            core.circle(cr, wx + math.cos(a) * 9.0, wy + math.sin(a) * 6.0, 1.2)
            cr.fill()
        cr.restore()
    # front bars, rings, cap and finial
    cr.set_line_width(3.2)
    core.src(cr, il)
    for k in (-1.0, 0.0, 1.0):
        cr.move_to(0.0, -26.0)
        cr.curve_to(k * 30.0, -22.0, k * 30.0, 20.0, 0.0, 26.0)
    cr.stroke()
    core.ellipse(cr, 0.0, 0.0, 21.5, 4.0)
    cr.set_line_width(2.4)
    cr.stroke()
    core.src(cr, core.mix(il, C["wisp"], 0.35 * lv), 0.9)   # wisp light on the front bars
    for k in (-1.0, 1.0):
        cr.move_to(k * 2.0, -20.0)
        cr.curve_to(k * 20.0, -14.0, k * 20.0, 12.0, k * 2.0, 20.0)
    cr.set_line_width(1.2)
    cr.stroke()
    cap = [(-14.0, -24.0), (-8.0, -33.0), (8.0, -33.0), (14.0, -24.0)]
    core.polygon(cr, cap)
    _solid(cr, il)
    core.circle(cr, 0.0, 30.0, 4.0)
    _solid(cr, il)
    q.end()
    return PropRig(center=q.C((wx, wy)), level=lv, scale=scale)


def wisp_light(lc, rig, scale=None, floor_y=None, strength=1.0):
    """A wisp lamp's cold light for the LightLayer: halo (+ a pool on the floor at floor_y)."""
    s_ = rig.scale if scale is None else scale
    x, y = rig.center
    fx.glow(lc, x, y, 280 * s_, PROP_COLORS["wisp"], 0.24 * rig.level * strength)
    if floor_y is not None:
        fx.light_pool(lc, x, floor_y, 380 * s_, 80 * s_, "#6fffd0", 0.28 * rig.level * strength)


_LANTERN_COLORS = {"tavern": ("#E2507A", "#F2A03D", "#D8463A", "#F07AA0", "#F5C04A"),
                   "warm": ("#F2A03D", "#F5C04A", "#E8783A"),
                   "cold": ("#7FD8E8", "#A8F0D8", "#B8C8FF")}


def draw_lantern_string(cr, p0, p1, t=0.0, scale=1.0, light=None, n=9, sag=0.16, seed=0, palette="tavern", lit=1.0,
                        swing=1.0, detail=None):
    """A string of small candle-lit paper lanterns sagging between two points (the tavern's
    "string lights"): the cord hangs in a gentle catenary that sways, each round ribbed paper
    lantern swings on its own little string and flickers.

    p0, p1 = the two fixings (caller coordinates). sag = dip as a fraction of the span (or px if
    > 1). n lanterns, each ~22 x 26 at scale 1.0. palette "tavern" (hot magenta/amber),
    "warm" or "cold", or a list of colours. Set dressing (no outline). Returns
    [(x, y, colour, level), ...] -> lantern_string_light(lc, those, scale)."""
    light = light or B.LIGHTS["neutral"]
    cols = _LANTERN_COLORS.get(palette, palette) if isinstance(palette, str) else palette
    (x0, y0), (x1, y1) = p0, p1
    span = math.hypot(x1 - x0, y1 - y0)
    dip = sag * span if sag <= 1.0 else sag
    sw_x = swing * 4.0 * math.sin(t * 0.7 + seed) * scale
    sw_y = swing * 3.0 * math.sin(t * 1.1 + seed * 1.7) * scale

    def cord(u):
        bx, by = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        k = 4.0 * u * (1.0 - u)
        return bx + sw_x * k, by + (dip + sw_y) * k

    det = detail if detail is not None else (2 if scale * B.device_scale(cr) >= 0.9 else 1)
    pts = [cord(i / 30) for i in range(31)]
    cr.save()
    cr.set_line_width(max(1.0, 1.6 * scale))
    core.src(cr, "#1a1216", 0.9)
    core.smooth_open(cr, pts)
    cr.stroke()
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        cx, cy = cord(u)
        ang = swing * 0.10 * math.sin(t * 1.3 + i * 0.7 + seed)
        c = cols[(i + seed) % len(cols)]
        lv = clamp(lit) * _flicker(t, seed * 31 + i, 1.4)
        hx, hy = cx + math.sin(ang) * 8.0 * scale, cy + math.cos(ang) * 8.0 * scale
        cr.set_line_width(max(0.8, 0.9 * scale))
        core.src(cr, "#1a1216", 0.8)
        cr.move_to(cx, cy)
        cr.line_to(hx, hy)
        cr.stroke()
        lx, ly = cx + math.sin(ang) * 21.0 * scale, cy + math.cos(ang) * 21.0 * scale
        _paper_lantern(cr, lx, ly, scale, ang, c, lv, light, det)
        out.append((lx, ly, c, lv))
    cr.restore()
    return out


def _paper_lantern(cr, x, y, s, ang, c, lv, light, det):
    """One round ribbed paper lantern centred at (x, y), glowing from its candle."""
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    cr.scale(s, s)
    lit_c = core.mix(B.palette(light, Mat.of(c)).shadow, core.tint(c, 0.35), clamp(lv))
    core.ellipse(cr, 0.0, 0.0, 11.0, 12.5)
    core.src(cr, lit_c)
    cr.fill()
    if lv > 0.02:
        pat = core.radial(0.0, 1.5, 11.0, [(0.0, core.alpha(core.tint(c, 0.85), 0.95 * lv)), (0.55, core.alpha(core.tint(c, 0.4), 0.6 * lv)),
                                            (1.0, core.alpha(c, 0.0))])
        cr.set_source(pat)
        core.ellipse(cr, 0.0, 0.0, 11.0, 12.5)
        cr.fill()
    if det >= 1:
        cr.set_line_width(0.9)
        core.src(cr, core.shade(c, 0.45), 0.55)
        for k in (-0.55, 0.0, 0.55):
            cr.move_to(k * 6.0, -11.5)
            cr.curve_to(k * 14.0, -4.0, k * 14.0, 4.0, k * 6.0, 11.5)
        cr.stroke()
    core.src(cr, "#2a1a1a")
    core.rounded_rect(cr, -6.0, -14.5, 12.0, 4.0, 1.5)
    core.rounded_rect(cr, -5.0, 11.0, 10.0, 3.5, 1.5)
    cr.fill()
    cr.restore()


def lantern_string_light(lc, lanterns, scale=1.0, strength=1.0):
    """Glow halos for a lantern string (from draw_lantern_string) -- into the LightLayer, or
    straight into the frame with a smaller strength."""
    for (x, y, c, lv) in lanterns:
        fx.glow(lc, x, y, 60 * scale, core.tint(c, 0.2), 0.45 * lv * strength)


# ========================================================================================
# 11. S3 HOLD MUSIC: the flipping hourglass and floating notes (cold rune-light)
# ========================================================================================

def draw_hourglass(cr, x, y, scale=1.0, light=None, t=0.0, period=4.0, flip_time=0.6, glow=1.0, label="on hold",
                   color=None, detail=None):
    """The little floating hourglass of S3's "on hold": brass frame, two glass bulbs, the sand
    running out, and every `period` seconds it flips over (eased, flip_time s) and starts again.
    A small ribbon below reads `label` in storybook italic, glowing in the stone's cold rune
    light. Anchor = its centre; 34 x 56 at scale 1.0 (+ the ribbon)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    rc = color or C["rune"]
    ph = t % period
    flip = smooth(clamp((ph - (period - flip_time)) / flip_time))
    k = clamp(ph / (period - flip_time))               # how much sand has run
    bob = 2.0 * math.sin(t * 1.6)
    cr.translate(0.0, bob)
    if glow > 0:
        fx.glow(cr, 0.0, 0.0, 44.0, rc, 0.35 * glow)
    cr.save()
    cr.rotate(math.pi * flip)
    br, bs_, _bd, brim = _tones(q.light, C["brass"])
    # bulbs (glass) and sand
    top_b = [(-12.0, -24.0), (12.0, -24.0), (12.0, -18.0), (2.0, -3.0), (-2.0, -3.0), (-12.0, -18.0)]
    bot_b = [(-2.0, 3.0), (2.0, 3.0), (12.0, 18.0), (12.0, 24.0), (-12.0, 24.0), (-12.0, 18.0)]
    core.src(cr, (0.75, 0.9, 1.0), 0.18)
    core.smooth_closed(cr, top_b, 0.6)
    cr.fill()
    core.smooth_closed(cr, bot_b, 0.6)
    cr.fill()
    sand = "#e8c98a"
    # sand left in the top bulb: a shrinking pile above the neck
    if k < 0.98:
        lvl = -3.0 - 15.0 * (1.0 - k)
        cr.save()
        core.smooth_closed(cr, top_b, 0.6)
        cr.clip()
        cr.move_to(-14.0, lvl)
        cr.curve_to(-6.0, lvl + 2.0, 6.0, lvl + 2.0, 14.0, lvl)
        cr.line_to(14.0, 0.0)
        cr.line_to(-14.0, 0.0)
        cr.close_path()
        core.src(cr, sand)
        cr.fill()
        cr.restore()
        core.src(cr, sand)
        cr.rectangle(-0.6, -3.0, 1.2, 22.0 - 12.0 * k)        # the falling thread
        cr.fill()
    # the heap growing in the bottom bulb
    hh = 3.0 + 13.0 * k
    cr.save()
    core.smooth_closed(cr, bot_b, 0.6)
    cr.clip()
    cr.move_to(-14.0, 24.0)
    cr.line_to(-14.0, 24.0 - hh * 0.35)
    cr.curve_to(-6.0, 24.0 - hh * 0.6, -3.0, 24.0 - hh, 0.0, 24.0 - hh)
    cr.curve_to(3.0, 24.0 - hh, 6.0, 24.0 - hh * 0.6, 14.0, 24.0 - hh * 0.35)
    cr.line_to(14.0, 24.0)
    cr.close_path()
    core.src(cr, sand)
    cr.fill()
    cr.restore()
    cr.set_line_width(1.0)
    core.src(cr, (1, 1, 1), 0.45)
    cr.move_to(-9.0, -21.0)
    cr.curve_to(-10.0, -15.0, -6.0, -10.0, -4.0, -7.0)
    cr.stroke()
    # brass plates and posts
    for py in (-27.0, 27.0):
        core.rounded_rect(cr, -16.0, py - 3.0, 32.0, 6.0, 2.5)
        core.src(cr, br)
        cr.fill()
    for px in (-14.0, 14.0):
        core.rounded_rect(cr, px - 1.6, -25.0, 3.2, 50.0, 1.5)
        core.src(cr, bs_)
        cr.fill()
    cr.restore()
    if label:
        rw = 46.0
        ry = 40.0
        core.src(cr, core.mix("#1b2a3a", rc, 0.25), 0.85)
        cr.move_to(-rw / 2 - 6.0, ry - 6.0)
        cr.line_to(rw / 2 + 6.0, ry - 6.0)
        cr.line_to(rw / 2 + 2.0, ry)
        cr.line_to(rw / 2 + 6.0, ry + 6.0)
        cr.line_to(-rw / 2 - 6.0, ry + 6.0)
        cr.line_to(-rw / 2 - 2.0, ry)
        cr.close_path()
        cr.fill()
        core.glow_text(cr, label, 0.0, ry, 9.5, FONTS.text, core.tint(rc, 0.5), glow=rc, radius=3.0, glow_alpha=0.8 * glow,
                       align="center", valign="cap", italic=True)
    q.end()
    return PropRig(center=q.C((0.0, bob)))


def draw_music_note(cr, x, y, size=1.0, t=0.0, color=None, alpha=1.0, kind="semiminim", angle=0.0, glow=True):
    """A floating music note in medieval mensural style (diamond heads, a stem, maybe a flag),
    glowing cold like the stone's runes: the hold loop's four notes in S3.
    Anchor = the note head; ~14 x 38 at size 1.0. kind "minim" (hollow head), "semiminim"
    (filled), "fusa" (filled + flag)."""
    c = color or PROP_COLORS["rune"]
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(size, size)
    if glow:
        fx.glow(cr, 0.0, -10.0, 26.0, c, 0.4 * alpha)
    hot = core.tint(c, 0.55)
    head = [(-7.0, 0.0), (0.0, -5.5), (7.0, 0.0), (0.0, 5.5)]
    core.polygon(cr, head)
    core.src(cr, hot, alpha)
    if kind == "minim":
        cr.fill()
        core.polygon(cr, [(-3.2, 0.0), (0.0, -2.4), (3.2, 0.0), (0.0, 2.4)])
        core.src(cr, core.shade(c, 0.6), alpha)
    cr.fill()
    cr.rectangle(5.4, -30.0, 1.8, 30.0)
    core.src(cr, hot, alpha)
    cr.fill()
    if kind == "fusa":
        cr.move_to(7.2, -30.0)
        cr.curve_to(14.0, -24.0, 15.0, -18.0, 11.0, -12.0)
        cr.curve_to(12.0, -18.0, 10.0, -22.0, 7.2, -24.0)
        cr.close_path()
        cr.fill()
    cr.restore()


# ========================================================================================
# 12. THE ENCHANTED TUMBLING DRUM (S1 "dryer")
# ========================================================================================

DRUM_R = 92.0                           # lid radius at scale 1.0; the axle is 130 above the ground
_CLOTH = ("#B5524A", "#E4D9BE", "#4F6FA8", "#E9E4D6", "#7E9E62", "#C8923E", "#8A5E96", "#3E5E6E")


def _drum_geom(scale, vp_local, depth):
    R = DRUM_R
    cy = -R - 38.0
    if vp_local is not None:
        dx, dy = (vp_local[0] - 0.0) * 0.16, (vp_local[1] - cy) * 0.16
    else:
        dx, dy = depth
    return R, cy, dx, dy


def _vp_local(cr, x, y, scale, vp):
    if vp is None:
        return None
    return ((vp[0] - x) / scale, (vp[1] - y) / scale)


def drum_body(cr, x, y, scale=1.0, light=None, t=0.0, seed=0, speed=1.0, vp=None, depth=(62.0, -24.0), rumble=1.0,
              detail=None):
    """The drum minus its lid: the oak cradle and the barrel (staves turning, brass hoops).
    Same anchor/arguments as draw_tumbling_drum. Returns (lid centre, R) in caller coords."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    R, cy, dx, dy = _drum_geom(scale, _vp_local(cr, x, y, scale, vp), depth)
    Rb = R * 0.9
    jx = rumble * 0.9 * core.noise1(t * 21.0, seed)
    jy = rumble * 0.7 * core.noise1(t * 24.0, seed + 9)
    ol, osh, odeep, orim = _tones(q.light, C["oak"])
    bl, bsh, bdeep, brim = _tones(q.light, C["brass"])
    B.contact_shadow(cr, dx * 0.5, 2.0 + dy * 0.3, R * 1.3, 15.0, alpha=0.5)
    # the cradle: an oak A-frame at the back and one at the front
    for (ox, oy, gy) in ((dx, cy + dy, dy * 0.85), (0.0, cy, 0.0)):
        for sx in (-1.0, 1.0):
            core.polygon(cr, [(ox + sx * R * 0.38, oy + R * 0.66), (ox + sx * R * 0.38 + sx * 13.0, oy + R * 0.6),
                              (ox + sx * R * 0.92 + sx * 12.0, gy), (ox + sx * R * 0.92 - sx * 4.0, gy)])
            _solid(cr, odeep if ox != 0.0 else osh)
        core.rounded_rect(cr, ox - R * 0.75, oy + R * 0.92 + (gy - oy - R * 0.92) * 0.45, R * 1.5, 9.0, 3.0)
        _solid(cr, odeep if ox != 0.0 else osh)
    cr.save()
    cr.translate(jx, jy)
    # the barrel: hull of the front and back rims
    ring = [(math.cos(a) * R, cy + math.sin(a) * R) for a in [i * TAU / 36 for i in range(36)]]
    back = [(dx + math.cos(a) * Rb, cy + dy + math.sin(a) * Rb) for a in [i * TAU / 36 for i in range(36)]]
    hull = core.convex_hull(ring + back)
    core.polygon(cr, hull)
    _solid(cr, ol)
    cr.save()
    core.polygon(cr, hull)
    cr.clip()
    # shadow on the underside, rim light on top
    cr.move_to(-R * 2, cy + R * 0.35)
    cr.line_to(dx + R * 2, cy + dy + R * 0.35)
    cr.line_to(dx + R * 2, cy + R * 3)
    cr.line_to(-R * 2, cy + R * 3)
    cr.close_path()
    _solid(cr, osh)
    # turning staves on the visible side band
    dn = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dn, dy / dn
    rot = t * TAU * 0.3 * speed + seed
    if q.detail >= 1:
        cr.set_line_width(2.2)
        core.src(cr, odeep, 0.65)
        for i in range(20):
            a = rot + i * TAU / 20
            ca, sa = math.cos(a), math.sin(a)
            if ca * ux + sa * uy <= 0.05:
                continue
            cr.move_to(ca * R, cy + sa * R)
            cr.line_to(dx + ca * Rb, cy + dy + sa * Rb)
        cr.stroke()
    # brass hoops: the visible arcs only
    a_mid = math.atan2(uy, ux)
    for u in (0.3, 0.74):
        hx, hy, hr = dx * u, cy + dy * u, lerp(R, Rb, u)
        cr.new_path()
        cr.arc(hx, hy, hr - 1.0, a_mid - math.pi / 2, a_mid + math.pi / 2)
        cr.set_line_width(8.0)
        core.src(cr, bdeep)
        cr.stroke()
        cr.arc(hx, hy, hr - 1.6, a_mid - math.pi / 2, a_mid + math.pi / 2)
        cr.set_line_width(4.0)
        core.src(cr, bl)
        cr.stroke()
    cr.restore()
    cr.restore()
    q.end()
    return q.C((jx, cy + jy)), R * scale


def _garment(cr, kind, s, col_, line_c, seed):
    """One piece of laundry, centred at the origin, size ~s (already rotated by the caller)."""
    if kind == 0:          # a shirt/tunic: body + sleeves
        core.blob(cr, 0.0, 0.0, s, 0.22, 7, seed=seed)
        core.src(cr, col_)
        cr.fill()
        core.ellipse(cr, -s * 0.9, -s * 0.35, s * 0.55, s * 0.28, -0.5)
        core.ellipse(cr, s * 0.9, -s * 0.3, s * 0.55, s * 0.28, 0.5)
        cr.fill()
        core.src(cr, line_c, 0.5)
        core.ellipse(cr, 0.0, -s * 0.62, s * 0.3, s * 0.14)
        cr.fill()
    elif kind == 1:        # a sock / stocking: an L-shaped tube, maybe striped
        core.tapered(cr, [(-s * 0.9, -s * 0.4), (0.0, -s * 0.1), (s * 0.4, s * 0.5), (s * 0.95, s * 0.55)], s * 0.55, s * 0.5)
        core.src(cr, col_)
        cr.fill()
        if seed % 2 == 0:
            core.src(cr, core.tint(col_, 0.6), 0.85)
            for k in range(3):
                core.tapered(cr, [(-s * 0.7 + k * s * 0.45, -s * 0.55 + k * s * 0.18), (-s * 0.55 + k * s * 0.45, -s * 0.1 + k * s * 0.18)],
                             s * 0.16, s * 0.16)
            cr.fill()
    elif kind == 2:        # a kerchief: a soft square
        core.rounded_rect(cr, -s * 0.75, -s * 0.75, s * 1.5, s * 1.5, s * 0.3)
        core.src(cr, col_)
        cr.fill()
        core.src(cr, line_c, 0.45)
        core.rounded_rect(cr, -s * 0.55, -s * 0.55, s * 1.1, s * 1.1, s * 0.2)
        cr.set_line_width(max(0.8, s * 0.07))
        cr.stroke()
    else:                  # a long scarf / sash
        core.tapered(cr, [(-s * 1.2, 0.0), (-s * 0.3, -s * 0.35), (s * 0.4, s * 0.2), (s * 1.2, -s * 0.1)], s * 0.5, s * 0.45)
        core.src(cr, col_)
        cr.fill()


def drum_porthole(cr, x, y, scale=1.0, light=None, t=0.0, seed=0, speed=1.0, glow=1.0, rumble=1.0, vp=None,
                  depth=(62.0, -24.0), runes=1.0, detail=None, n_clothes=7):
    """The drum's lid: a brass ring with rivets, a rune-engraved bezel (cold teal, breathing),
    and the round glass porthole with someone's laundry tumbling behind it (lifted up the rising
    side, then tumbling down through the middle), suds and glints. Same anchor as
    draw_tumbling_drum. Returns PropRig(center, radius, glow)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    R, cy, dx, dy = _drum_geom(scale, _vp_local(cr, x, y, scale, vp), depth)
    jx = rumble * 0.9 * core.noise1(t * 21.0, seed)
    jy = rumble * 0.7 * core.noise1(t * 24.0, seed + 9)
    cr.translate(jx, jy)
    bl, bsh, bdeep, brim = _tones(q.light, C["brass"])
    hi = core.tint(bl, 0.45)
    # outer brass ring: lit with a shadow crescent toward the lower right
    core.circle(cr, 0.0, cy, R)
    _solid(cr, bsh)
    cr.save()
    core.circle(cr, 0.0, cy, R)
    cr.clip()
    core.circle(cr, -R * 0.06, cy - R * 0.06, R * 0.98)
    _solid(cr, bl)
    cr.restore()
    core.circle(cr, 0.0, cy, R * 0.86)
    _solid(cr, bdeep)
    if q.detail >= 1:
        core.src(cr, hi)
        for k in range(16):
            a = k / 16 * TAU
            core.circle(cr, math.cos(a) * R * 0.93, cy + math.sin(a) * R * 0.93, 2.6)
        cr.fill()
    # the bezel round the glass, with its runes
    core.circle(cr, 0.0, cy, R * 0.83)
    _solid(cr, bl)
    cr.save()
    core.circle(cr, 0.0, cy, R * 0.83)
    cr.clip()
    core.circle(cr, R * 0.05, cy + R * 0.05, R * 0.83)
    _solid(cr, bsh, 0.7)
    cr.restore()
    pulse = 0.5 + 0.5 * math.sin(t * 1.4 + seed * 1.3)
    if q.detail >= 1 and runes > 0:
        strokes = []
        for k in range(12):
            a = k / 12 * TAU + 0.13
            strokes += _rune_strokes(k + seed, math.cos(a) * R * 0.765, cy + math.sin(a) * R * 0.765, 9.0, a + math.pi / 2)
        B.detail_lines(cr, strokes, 1.8, bdeep, 0.8)
        B.detail_lines(cr, strokes, 1.1, "#9fffe0", (0.3 + 0.55 * pulse) * runes * glow)
    # the hinge (left) and the latch (right)
    core.rounded_rect(cr, -R * 1.02, cy - 16.0, 16.0, 32.0, 4.0)
    _solid(cr, bsh)
    core.rounded_rect(cr, R * 0.88, cy - 8.0, 18.0, 16.0, 4.0)
    _solid(cr, bl)
    # glass + the laundry
    pr = R * 0.68
    cr.save()
    core.circle(cr, 0.0, cy, pr)
    cr.clip()
    cr.set_source(core.radial(0.0, cy + pr * 0.2, pr * 1.25, [(0.0, "#1f6a5c"), (0.6, "#0b2729"), (1.0, "#031010")]))
    cr.paint()
    if glow > 0:
        fx.glow(cr, 0.0, cy + pr * 0.1, pr * 1.1, C["wisp"], 0.22 * glow)
    w = TAU * 0.42 * speed
    items = []
    for i in range(n_clothes):
        ph = core.hash01(i, seed + 1)
        u = (t * w / TAU + ph) % 1.0
        if u < 0.62:                                   # carried up the rising side
            a = math.pi / 2 - (u / 0.62) * math.pi * 0.95
            rr = pr * (0.62 + 0.08 * core.hash01(i, seed + 2))
            px, py = math.cos(a) * rr, math.sin(a) * rr
        else:                                          # tumbling down through the middle
            v = (u - 0.62) / 0.38
            a0 = math.pi / 2 - math.pi * 0.95
            sx_, sy_ = math.cos(a0) * pr * 0.66, math.sin(a0) * pr * 0.66
            ex_, ey_ = -pr * 0.15 + core.jitter(i, pr * 0.2, seed), pr * 0.62
            px = lerp(sx_, ex_, v)
            py = lerp(sy_, ey_, v * v)
        spin = t * (1.5 + core.hash01(i, seed + 3) * 2.0) * (1 if i % 2 else -1) + i
        kind = int(core.hash01(i, seed + 4) * 4)
        col_ = _CLOTH[int(core.hash01(i, seed + 5) * len(_CLOTH))]
        items.append((py, px, spin, kind, col_, i))
    items.sort()
    for py, px, spin, kind, col_, i in items:
        c2 = core.mix(col_, "#1b4c46", 0.38)            # seen through tinted glass
        cr.save()
        cr.translate(px, cy + py)
        cr.rotate(spin)
        _garment(cr, kind, pr * (0.2 + 0.07 * core.hash01(i, seed + 6)), c2, core.shade(c2, 0.4), seed + i)
        cr.restore()
    # suds round the bottom, a few rising bubbles
    if q.detail >= 1:
        core.src(cr, "#cfeee6", 0.30)
        for k in range(14):
            a = math.pi * (0.15 + 0.7 * k / 13)
            core.circle(cr, math.cos(a) * pr * 0.82 + 3 * math.sin(t * 3 + k), cy + math.sin(a) * pr * 0.82, pr * (0.1 + 0.05 * core.hash01(k, seed)))
        cr.fill()
        core.src(cr, "#dffff6", 0.45)
        for k in range(5):
            u = (t * 0.6 + core.hash01(k, seed + 8)) % 1.0
            core.circle(cr, (core.hash01(k, seed + 9) - 0.5) * pr, cy + pr * 0.7 - u * pr * 1.4, 1.6 + 1.2 * core.hash01(k, seed + 10))
        cr.fill()
    # glass glints and the inner shadow of the bezel
    core.src(cr, (1, 1, 1), 0.22)
    core.ellipse(cr, -pr * 0.36, cy - pr * 0.44, pr * 0.42, pr * 0.16, -0.6)
    cr.fill()
    core.src(cr, (1, 1, 1), 0.12)
    core.ellipse(cr, pr * 0.42, cy + pr * 0.48, pr * 0.2, pr * 0.07, -0.6)
    cr.fill()
    cr.restore()
    cr.new_path()
    cr.arc(0.0, cy, pr, 0, TAU)
    cr.set_line_width(3.0)
    core.src(cr, bdeep)
    cr.stroke()
    q.end()
    return PropRig(center=q.C((0.0, cy)), radius=pr * scale, glow=glow * (0.6 + 0.4 * pulse))


def draw_tumbling_drum(cr, x, y, scale=1.0, light=None, t=0.0, seed=0, speed=1.0, glow=1.0, rumble=1.0, vp=None,
                       depth=(62.0, -24.0), detail=None):
    """An enchanted tumbling drum (the S1 "dryer"): an oak barrel on its side in an oak cradle,
    brass hoops, its staves turning by themselves; a brass lid with a round glass porthole where
    a stranger's laundry tumbles (per-drum `seed`, `speed`), faint cold runes breathing on the
    bezel, a slight rumble.

    Anchor (x, y) = the ground point below the lid's centre; lid radius DRUM_R = 92, axle 130 above
    the ground at scale 1.0; the barrel recedes by `depth` (local px) -- or toward a vanishing
    point `vp` (caller coords) so a row of drums shares one perspective. Set dressing: no
    outline. Cost ~3-4 ms at scale 1; cache nothing (it moves). Returns the porthole PropRig
    (center, radius, glow) -> drum_light(lc, rig)."""
    drum_body(cr, x, y, scale, light, t, seed, speed, vp, depth, rumble, detail)
    return drum_porthole(cr, x, y, scale, light, t, seed, speed, glow, rumble, vp, depth, 1.0, detail)


def drum_light(lc, rig, strength=1.0):
    """A drum's cold porthole glow for the LightLayer (spills on the floor and the sitter)."""
    x, y = rig.center
    fx.glow(lc, x, y, rig.radius * 3.2, PROP_COLORS["wisp"], 0.22 * rig.glow * strength)


# ========================================================================================
# 13. SIGNS: the painted plaque (SELF-SERVICE) and the hanging shop signs
# ========================================================================================

def _notched_board(w, h, notch=9.0, n=6):
    """A tavern-board outline centred at the origin: a rectangle whose corners are cut by
    concave quarter-circle notches (clockwise from the top edge)."""
    pts = []
    for cx, cy, a0 in ((w / 2, -h / 2, math.pi), (w / 2, h / 2, 1.5 * math.pi), (-w / 2, h / 2, 0.0),
                       (-w / 2, -h / 2, 0.5 * math.pi)):
        for i in range(n + 1):
            a = a0 - (math.pi / 2) * i / n
            pts.append((cx + math.cos(a) * notch, cy + math.sin(a) * notch))
    return pts


def draw_plaque(cr, x, y, text="SELF-SERVICE", scale=1.0, light=None, t=0.0, taps=(), swing=0.0, size=34.0,
                paint="#2F5A4A", letter="#EFE3C2", detail=None):
    """A painted wooden plaque hanging from a nail by a cord (S1: SELF-SERVICE): a notched oak
    board painted deep green, a cream border and storybook uncial lettering with the board's
    grain and a little worn paint showing through.

    Anchor (x, y) = the nail. The board hangs ~22 below it; its width follows the text (about
    300 x 74 for SELF-SERVICE at scale 1.0). taps = times (local s) it was tapped: each one sets
    it rocking on its nail (the elf's two taps); swing adds an angle. Outlined (it is touched).
    Returns PropRig(nail, center, tap_point)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    fam = FONTS.sign
    tw = core.measure(cr, text, size, fam)[0]
    w, h = tw + 54.0, size * 1.55 + 20.0
    rock = swing + sum(0.055 * B.wobble(t, t0, freq=2.2, decay=2.8) for t0 in taps)
    # the nail and cord
    core.circle(cr, 0.0, 0.0, 3.4)
    core.src(cr, "#2a2622")
    cr.fill()
    cr.save()
    cr.rotate(rock)
    top = 22.0
    tw_ = B.palette(q.light, Mat.of(C["twine"]))
    B.detail_lines(cr, [[(-w * 0.32, top + 6.0), (0.0, 0.0), (w * 0.32, top + 6.0)]], 2.2, tw_.line, 0.95, taper=(1, 1, 1))
    B.detail_lines(cr, [[(-w * 0.32, top + 6.0), (0.0, 0.0), (w * 0.32, top + 6.0)]], 1.2, tw_.lit, 1.0, taper=(1, 1, 1))
    cy = top + h / 2
    pts = [(px, py + cy) for px, py in _notched_board(w, h, 10.0)]
    bs, bo = _poly_paths(cr, pts, q.lw)
    paint_m = Mat.of(paint, sheen=0.1)
    pb = q.shade(bs, paint_m, 16.0, outline=bo)
    oak = B.palette(q.light, q.M["oak"])
    if q.detail >= 1:
        # wear: bare wood showing at the edges, grain lines through the paint
        cr.save()
        bs.add(cr)
        cr.clip()
        core.src(cr, oak.lit, 0.55)
        for i in range(14):
            ex = (core.hash01(i, 31) - 0.5) * w
            ey = cy + (h / 2 - 3.0) * (1 if core.hash01(i, 32) > 0.5 else -1)
            core.ellipse(cr, ex, ey, 4.0 + 6.0 * core.hash01(i, 33), 1.6 + 1.2 * core.hash01(i, 34))
        cr.fill()
        B.detail_lines(cr, [[(-w / 2, cy - h * 0.3 + k * h * 0.2), (w / 2, cy - h * 0.28 + k * h * 0.2 + 2.0)] for k in range(4)],
                       0.8, pb.line, 0.25)
        cr.restore()
        border = B.offset_closed(pts, -6.0)
        cr.new_path()
        core.polygon(cr, border)
        cr.set_line_width(1.6)
        core.src(cr, B.palette(q.light, Mat.of(letter)).lit, 0.85)
        cr.stroke()
        for sx in (-1, 1):                           # small painted flourishes
            core.circle(cr, sx * (w / 2 - 15.0), cy, 2.4)
        cr.fill()
    # the lettering: a shadow line (paint thickness) and the cream letters
    lt = B.palette(q.light, Mat.of(letter))
    core.text(cr, text, 1.2, cy + 1.4, size, fam, pb.line, align="center", valign="cap", alpha_=0.8)
    core.text(cr, text, 0.0, cy, size, fam, lt.lit, align="center", valign="cap")
    if q.detail >= 2:                                # flecks of paint worn off the letters
        core.src(cr, pb.lit, 0.7)
        for i in range(10):
            core.circle(cr, (core.hash01(i, 41) - 0.5) * tw, cy + (core.hash01(i, 42) - 0.5) * size * 0.6,
                        0.6 + 0.9 * core.hash01(i, 43))
        cr.fill()
    cr.restore()
    q.end()
    ca, sa = math.cos(rock), math.sin(rock)
    tap = (w * 0.28 * ca - (cy + h * 0.25) * sa, w * 0.28 * sa + (cy + h * 0.25) * ca)
    return PropRig(nail=q.C((0.0, 0.0)), center=q.C((-cy * sa, cy * ca)), tap_point=q.C(tap), size=(w * scale, h * scale))


_SIGNS = {
    "apothecary": dict(text=("APOTHECARY",), shape="arch", paint="#E9E0C8", ink="#2E6A48", emblem="cross"),
    "flagon": dict(text=("THE MERRY", "FLAGON"), shape="shield", paint="#6A2232", ink="#E8C46A", emblem="tankard"),
    "washhouse": dict(text=("WASH-HOUSE",), shape="board", paint="#2C4A62", ink="#E6EEF0", emblem="tub"),
}


def _emblem(cr, kind, cx, cy, s, ink, paint, glow=0.0):
    """Painted sign emblems: "cross" (the apothecary's green cross), "tankard" (a foaming
    flagon), "tub" (a washtub with bubbles)."""
    if kind == "cross":
        a, th = 15.0 * s, 5.6 * s
        cross = [(-th, -a), (th, -a), (th, -th), (a, -th), (a, th), (th, th), (th, a), (-th, a), (-th, th), (-a, th),
                 (-a, -th), (-th, -th)]
        core.polygon(cr, [(cx + px * 1.18, cy + py * 1.18) for px, py in cross])
        core.src(cr, core.shade(paint, 0.25), 0.5)
        cr.fill()
        core.polygon(cr, [(cx + px, cy + py) for px, py in cross])
        core.src(cr, ink)
        cr.fill()
        if glow > 0:
            fx.glow(cr, cx, cy, 34.0 * s, "#5fff9a", 0.5 * glow)
    elif kind == "tankard":
        core.rounded_rect(cr, cx - 10 * s, cy - 8 * s, 20 * s, 22 * s, 3 * s)
        core.src(cr, ink)
        cr.fill()
        cr.set_line_width(3.4 * s)
        cr.arc(cx + 11 * s, cy + 3 * s, 6 * s, -math.pi / 2, math.pi / 2)
        cr.stroke()
        core.blob(cr, cx, cy - 10 * s, 11.5 * s, 0.2, 7, seed=4, sy=0.55)
        core.src(cr, "#F4EBD8")
        cr.fill()
        core.src(cr, core.shade(ink, 0.45))
        for k in (-1, 1):
            cr.rectangle(cx + k * 5 * s - 0.8 * s, cy - 4 * s, 1.6 * s, 16 * s)
        cr.fill()
        if glow > 0:
            fx.glow(cr, cx, cy, 34.0 * s, "#ffb050", 0.4 * glow)
    elif kind == "tub":
        core.polygon(cr, [(cx - 15 * s, cy - 4 * s), (cx + 15 * s, cy - 4 * s), (cx + 11 * s, cy + 12 * s), (cx - 11 * s, cy + 12 * s)])
        core.src(cr, ink)
        cr.fill()
        core.src(cr, core.shade(ink, 0.4))
        cr.rectangle(cx - 13 * s, cy + 1 * s, 26 * s, 2.2 * s)
        cr.fill()
        core.src(cr, "#cfefff")
        for k, (bx, by, br) in enumerate(((-6, -9, 4.5), (3, -12, 5.5), (10, -7, 3.5), (-1, -18, 3.0))):
            core.circle(cr, cx + bx * s, cy + by * s, br * s)
        cr.fill()
        if glow > 0:
            fx.glow(cr, cx, cy, 34.0 * s, "#5fe0ff", 0.45 * glow)


def draw_hanging_sign(cr, x, y, kind="apothecary", scale=1.0, light=None, t=0.0, side=1, text=None, emblem=None,
                      paint=None, ink=None, swing=1.0, glow=0.0, seed=0, detail=None):
    """A painted shop sign hanging from a scrolled wrought-iron wall bracket, rocking gently.

    kind: "apothecary" (cream arch, green cross, APOTHECARY), "flagon" (burgundy shield, gold
    tankard, THE MERRY FLAGON), "washhouse" (blue board, washtub and bubbles), or None with your
    own text=(line1[, line2]), emblem, paint, ink. Anchor (x, y) = where the bracket meets the
    wall; the arm reaches 150 toward `side` (+1 right / -1 left) and the board (~120 x 120)
    hangs below it, at scale 1.0. glow 0..1 lights the emblem from within (S8, far away).
    Set dressing: no outline (draw it in an fx.Layer if it does not swing)."""
    spec = dict(_SIGNS.get(kind, _SIGNS["apothecary"]))
    if text is not None:
        spec["text"] = tuple(text) if isinstance(text, (list, tuple)) else (text,)
    if emblem is not None:
        spec["emblem"] = emblem
    if paint is not None:
        spec["paint"] = paint
    if ink is not None:
        spec["ink"] = ink
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    sx = 1.0 if side >= 0 else -1.0
    il, ish, ideep, irim = _tones(q.light, C["iron"])
    # the bracket: wall plate, arm, the scrolled brace under it
    core.rounded_rect(cr, -6.0, -14.0, 12.0, 60.0, 3.0)
    _solid(cr, il)
    arm = [(0.0, 0.0), (sx * 150.0, 0.0)]
    core.tapered(cr, arm, 6.0, 5.0)
    _solid(cr, il)
    core.tapered(cr, [(sx * 150.0, 0.0)] + _spiral(sx * 156.0, -8.0, 8.0, 1.1, a0=math.pi / 2, n=10, sign=-sx), 4.5, 2.0)
    _solid(cr, il)
    brace = [(0.0, 42.0), (sx * 30.0, 30.0), (sx * 60.0, 12.0), (sx * 92.0, 2.0)]
    core.tapered(cr, core.spline(brace, 5), 4.4, 3.4)
    _solid(cr, il)
    core.tapered(cr, [(sx * 30.0, 30.0)] + _spiral(sx * 40.0, 18.0, 10.0, 1.15, a0=math.pi * 0.8, n=12, sign=sx), 3.4, 1.8)
    _solid(cr, il)
    # the board, rocking from its two rings
    rock = swing * (0.035 * math.sin(t * 1.2 + seed) + 0.015 * core.noise1(t * 0.6, seed + 4))
    bx = sx * 82.0
    cr.save()
    cr.translate(bx, 4.0)
    cr.rotate(rock)
    pl, psh, pdeep, prim = _tones(q.light, spec["paint"], shadow_k=0.9)
    ink_c = B.palette(q.light, Mat.of(spec["ink"])).lit
    w, h = 116.0, 104.0
    top = 14.0
    for rx in (-w * 0.3, w * 0.3):
        cr.set_line_width(2.0)
        core.src(cr, ideep)
        cr.arc(rx, 4.0, 4.5, 0, TAU)
        cr.move_to(rx, 8.0)
        cr.line_to(rx, top + 2.0)
        cr.stroke()
    shape = spec["shape"]
    if shape == "arch":
        board = [(-w / 2, top + 30.0)] + [(math.cos(a) * w / 2, top + 30.0 - math.sin(a) * 30.0) for a in
                                           [math.pi - math.pi * i / 16 for i in range(17)]] + [(w / 2, top + h), (-w / 2, top + h)]
    elif shape == "shield":
        board = [(-w / 2, top), (w / 2, top), (w / 2, top + h * 0.55), (w * 0.3, top + h * 0.85), (0.0, top + h + 6.0),
                 (-w * 0.3, top + h * 0.85), (-w / 2, top + h * 0.55)]
    else:
        board = [(px, py + top + h / 2) for px, py in _notched_board(w, h, 9.0)]
    core.smooth_closed(cr, board, 0.25) if shape == "shield" else core.polygon(cr, board)
    _solid(cr, psh)
    cr.save()
    core.polygon(cr, board)
    cr.clip()
    core.polygon(cr, [(px - 3.0, py - 3.0) for px, py in board])
    _solid(cr, pl)
    if q.detail >= 1:
        core.src(cr, pdeep, 0.35)
        for k in range(5):
            cr.rectangle(-w / 2, top + 10.0 + k * h / 5.0, w, 1.0)
        cr.fill()
    cr.restore()
    # a thin painted border
    if q.detail >= 1:
        cr.new_path()
        core.polygon(cr, B.offset_closed(board, -5.0))
        cr.set_line_width(1.6)
        core.src(cr, ink_c, 0.75)
        cr.stroke()
    lines = spec["text"]
    fam = FONTS.sign if kind != "apothecary" else FONTS.label
    em_y = top + h * 0.40
    if len(lines) == 1:
        em_y = top + h * (0.44 if shape == "arch" else 0.40)
        _emblem(cr, spec["emblem"], 0.0, em_y, 1.15, ink_c, spec["paint"], glow)
        _label(cr, lines[0], 0.0, top + h * 0.80, 17.0, ink_c, fam, maxw=w - 20.0)
    else:
        em_y = top + h * 0.42
        _label(cr, lines[0], 0.0, top + h * 0.14, 14.0, ink_c, fam, maxw=w - 24.0)
        _emblem(cr, spec["emblem"], 0.0, em_y, 1.2, ink_c, spec["paint"], glow)
        _label(cr, lines[1], 0.0, top + h * 0.69, 18.0, ink_c, fam, maxw=w * 0.56)
    cr.restore()
    q.end()
    return PropRig(board=q.C((bx, top + h * 0.5)), emblem=q.C((bx, em_y)), glow=glow)


def sign_light(lc, rig, scale=1.0, color=None, strength=1.0):
    """A glowing sign's halo for the LightLayer (S8: small, cold, far away)."""
    if rig.glow > 0.01:
        fx.glow(lc, rig.emblem[0], rig.emblem[1], 120 * scale, color or "#7fe8ff", 0.25 * rig.glow * strength)


# ========================================================================================
# 14. THE APOTHECARY'S SHELVES, TANKARDS, TAVERN TABLES
# ========================================================================================

_GLASS = ("#3E7A5A", "#8A5A24", "#3563B0", "#9A8A62", "#6A3E7A", "#B8D0C8", "#A04A2E")
_FILL = ("#C8B06A", "#6A8A3A", "#B04A3A", "#E2D8C0", "#5A3A2A", "#8A6AC0", "#D88A3A")


def _shelf_item(cr, kind, x, base, w, h, glass, fill, lvl, light, seed, det):
    """One painterly jar or bottle standing on a shelf at (x, base): a glass body with its
    contents, a stopper/cover, a small label and a glint (set dressing: no outline)."""
    gl, gsh, gdeep, grim = _tones(light, glass)
    fl, fsh, fdeep, frim = _tones(light, fill)
    if kind == "flask":                                     # round flask with a neck
        r = w / 2
        body = [(x + math.cos(a) * r, base - r + math.sin(a) * r * 0.95) for a in [i * TAU / 20 for i in range(20)]]
        neck = (x - r * 0.28, base - h, r * 0.56, h - r * 1.6)
        core.polygon(cr, body)
        core.rounded_rect(cr, *neck, 1.5)
        _solid(cr, gsh)
        cr.save()
        core.polygon(cr, body)
        cr.clip()
        cr.rectangle(x - r, base - r * 2 * lvl, 2 * r, r * 2)
        _solid(cr, core.mix(fl, gsh, 0.35))
        cr.restore()
        top = base - h
    elif kind == "bottle":                                  # square-shouldered bottle
        core.rounded_rect(cr, x - w / 2, base - h * 0.72, w, h * 0.72, w * 0.18)
        core.rounded_rect(cr, x - w * 0.18, base - h, w * 0.36, h * 0.3, 1.5)
        _solid(cr, gsh)
        core.rounded_rect(cr, x - w / 2 + 1.5, base - h * 0.72 * lvl, w - 3.0, h * 0.72 * lvl - 1.5, w * 0.15)
        _solid(cr, core.mix(fl, gsh, 0.35))
        top = base - h
    elif kind == "jar":                                     # wide jar with a cloth cover
        core.rounded_rect(cr, x - w / 2, base - h * 0.85, w, h * 0.85, w * 0.15)
        _solid(cr, gsh)
        core.rounded_rect(cr, x - w / 2 + 1.5, base - h * 0.85 * lvl, w - 3.0, h * 0.85 * lvl - 1.5, w * 0.12)
        _solid(cr, core.mix(fl, gsh, 0.25))
        if det >= 1:                                        # herbs / berries / powder texture
            core.src(cr, fdeep, 0.5)
            for k in range(4):
                core.circle(cr, x + (core.hash01(k, seed) - 0.5) * w * 0.7, base - h * 0.85 * lvl * core.hash01(k, seed + 1),
                            w * 0.06 + 0.5)
            cr.fill()
        cl, csh, _cd, _cr = _tones(light, "#E8DFC8")
        core.blob(cr, x, base - h * 0.88, w * 0.58, 0.12, 7, seed=seed, sy=0.32)
        _solid(cr, cl)
        core.rounded_rect(cr, x - w * 0.52, base - h * 0.86, w * 1.04, 2.4, 1.0)
        _solid(cr, "#8a6a42")
        top = base - h
    else:                                                   # "pot": squat glazed earthenware pot
        pl, psh, pdeep, prim = _tones(light, glass)
        core.blob(cr, x, base - h * 0.45, w * 0.55, 0.06, 9, seed=seed, sy=0.85)
        _solid(cr, pl)
        cr.save()
        core.blob(cr, x, base - h * 0.45, w * 0.55, 0.06, 9, seed=seed, sy=0.85)
        cr.clip()
        core.circle(cr, x + w * 0.25, base - h * 0.3, w * 0.55)
        _solid(cr, psh)
        cr.restore()
        core.rounded_rect(cr, x - w * 0.36, base - h * 0.98, w * 0.72, h * 0.16, 2.0)
        _solid(cr, pdeep)
        top = base - h
    if kind in ("flask", "bottle"):                         # cork or wax stopper
        core.rounded_rect(cr, x - w * 0.16, top - 5.0, w * 0.32, 6.5, 1.5)
        _solid(cr, _tones(light, "#B08455")[0] if seed % 3 else _tones(light, "#7a2a2a")[0])
    if det >= 1 and kind != "pot" and h > 22:               # a small label
        ly = base - h * 0.42
        core.rounded_rect(cr, x - w * 0.36, ly - h * 0.11, w * 0.72, h * 0.22, 1.0)
        _solid(cr, _tones(light, "#E9DFC4")[0])
        if det >= 2:
            core.src(cr, "#5a4a3a", 0.6)
            cr.rectangle(x - w * 0.24, ly - 1.0, w * 0.48, 1.2)
            cr.fill()
    if kind != "pot":                                       # glint
        core.src(cr, (1, 1, 1), 0.35)
        cr.rectangle(x - w * 0.36, base - h * 0.62, max(1.2, w * 0.08), h * 0.36)
        cr.fill()
    return top


def draw_shelves(cr, x, y, w=420.0, h=420.0, scale=1.0, light=None, t=0.0, rows=4, seed=0, depth=34.0, gaps=(),
                 herbs=True, detail=None):
    """A wall of dark-oak apothecary shelves, filled procedurally (deterministic per seed) with
    flasks, bottles, covered jars and glazed pots of tinctures, herbs and powders; bundles of
    dried herbs hanging from the top board.

    Anchor (x, y) = the TOP-LEFT of the unit; w x h at scale 1.0 (the lioness is 450 tall: four
    rows of ~105). gaps = [(row, slot)] left empty (where she took something). Set dressing: no
    outline -- cache it in an fx.Layer (it is static). Returns PropRig(boards=[y of each shelf top])."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    C = PROP_COLORS
    ol, osh, odeep, orim = _tones(q.light, "#5A3C24")
    bl, bsh, bdeep, brim = _tones(q.light, "#3A2618")
    core.rounded_rect(cr, 0.0, 0.0, w, h, 4.0)              # the back panel
    _solid(cr, bdeep)
    if q.detail >= 1:
        core.src(cr, bsh, 0.5)
        for k in range(int(w // 46)):
            cr.rectangle(8.0 + k * 46.0, 0.0, 1.2, h)
        cr.fill()
    gap = h / rows
    boards = []
    for r in range(rows):
        by = gap * (r + 1) - 12.0
        boards.append(by)
        slot_x = 18.0
        k = 0
        while slot_x < w - 30.0:
            hh = 26.0 + core.hash01(r * 50 + k, seed) * (gap - 46.0)
            ww = 18.0 + core.hash01(r * 50 + k, seed + 1) * 24.0
            kind = ("flask", "bottle", "jar", "pot")[int(core.hash01(r * 50 + k, seed + 2) * 4)]
            if kind == "flask":
                ww = max(ww, 24.0)
                hh = max(hh, ww * 1.5)
            if (r, k) not in gaps:
                # its shadow on the back panel, then the item
                core.src(cr, (0, 0, 0), 0.22)
                core.rounded_rect(cr, slot_x + 3.0, by - hh * 0.95, ww, hh * 0.95, 3.0)
                cr.fill()
                _shelf_item(cr, kind, slot_x + ww / 2, by, ww, hh, _GLASS[int(core.hash01(r * 50 + k, seed + 3) * len(_GLASS))],
                            _FILL[int(core.hash01(r * 50 + k, seed + 4) * len(_FILL))],
                            0.35 + 0.55 * core.hash01(r * 50 + k, seed + 5), q.light, seed + r * 50 + k, q.detail)
            slot_x += ww + 6.0 + core.hash01(r * 50 + k, seed + 6) * 8.0
            k += 1
        # the shelf board: its top face (seen from a little below or above) and its front edge
        core.src(cr, ol)
        cr.rectangle(-6.0, by, w + 12.0, 12.0)
        cr.fill()
        core.src(cr, orim, 0.35)
        cr.rectangle(-6.0, by, w + 12.0, 2.0)
        cr.fill()
        core.src(cr, (0, 0, 0), 0.25)
        cr.rectangle(-6.0, by + 12.0, w + 12.0, 5.0)
        cr.fill()
    # side posts and the top board
    for px in (-10.0, w - 2.0):
        cr.rectangle(px, -8.0, 12.0, h + 8.0)
    core.src(cr, osh)
    cr.fill()
    cr.rectangle(-14.0, -14.0, w + 28.0, 14.0)
    core.src(cr, ol)
    cr.fill()
    if herbs:
        for k in range(int(w // 120) + 1):
            hx = 50.0 + k * 120.0 + core.jitter(k, 14.0, seed + 9)
            sway = 0.04 * math.sin(t * 0.6 + k)
            _herb_bundle(cr, hx, 0.0, 1.0, sway, q.light, seed + k)
    q.end()
    return PropRig(boards=[q.C((0.0, b_))[1] for b_ in boards])


def _herb_bundle(cr, x, y, s, sway, light, seed):
    """A bundle of dried herbs hanging head-down on a string: tied stalks fanning out into
    small leafy heads (lavender, sage, tansy)."""
    head_c = ("#7E8A4E", "#8A6A9E", "#B09A4A")[seed % 3]
    sl, ssh, sdeep, srim = _tones(light, "#7A6A3A")
    hl, hsh, hdeep, hrim = _tones(light, head_c)
    cr.save()
    cr.translate(x, y)
    cr.rotate(sway)
    cr.scale(s, s)
    cr.set_line_width(1.2)
    core.src(cr, "#3a2a1a")
    cr.move_to(0.0, 0.0)
    cr.line_to(0.0, 12.0)
    cr.stroke()
    stalks = []
    heads = []
    for k in range(7):
        a = (k - 3) * 0.11 + core.jitter(k, 0.04, seed)
        L_ = 34.0 + 10.0 * core.hash01(k, seed)
        end = (math.sin(a) * L_, 14.0 + math.cos(a) * L_)
        stalks.append([(0.0, 14.0), (math.sin(a) * L_ * 0.5, 14.0 + L_ * 0.5), end])
        heads.append(end)
    B.detail_lines(cr, stalks, 1.3, sdeep, 0.9, taper=(1.0, 1.0, 0.6))
    for hx, hy in heads:
        core.ellipse(cr, hx, hy - 2.0, 3.2, 6.0, 0.0)
    _solid(cr, hl)
    core.src(cr, hdeep, 0.5)
    for hx, hy in heads[::2]:
        core.ellipse(cr, hx + 1.0, hy - 1.0, 1.6, 4.0)
    cr.fill()
    core.rounded_rect(cr, -3.5, 11.0, 7.0, 5.0, 1.5)
    _solid(cr, "#8a6a42")
    cr.restore()


def draw_tankard(cr, x, y, scale=1.0, light=None, t=0.0, kind="wood", foam=1.0, angle=0.0, flip=False, outline=True,
                 detail=None):
    """A tavern tankard of ale: kind "wood" (oak staves, two iron hoops) or "pewter"; a head of
    foam slopping over the rim. Anchor = bottom centre; 38 wide (+16 handle) x 50 (+ foam) at
    scale 1.0; the handle is on +x (flip=True: on -x). outline=False for far-away set dressing.
    Returns PropRig(handle, top)."""
    q = _Ctx(cr, x, y, scale, angle, light, detail)
    C = PROP_COLORS
    if flip:
        cr.scale(-1.0, 1.0)
    mat = q.M["oak"] if kind == "wood" else q.M["pewter"]
    lw = q.lw if outline else 0.0
    body = [(-17.0, 0.0), (-19.0, -50.0), (19.0, -50.0), (17.0, 0.0)]
    handle = [(17.0, -42.0), (31.0, -40.0), (33.0, -24.0), (24.0, -12.0), (17.5, -12.0)]
    hs, ho = B.tube_paths(cr, handle, [4.5, 4.2, 4.2, 4.0, 4.0], max(lw, 0.01), samples=4)
    if outline:
        q.shade(hs, mat, 8.0, outline=ho, rim=0.6)
    else:
        hs.add(cr)
        _solid(cr, q.P(mat).lit)
    bs, bo = _poly_paths(cr, body, max(lw, 0.01))
    p = q.shade(bs, mat, 34.0, outline=bo if outline else False)
    if q.detail >= 1:
        if kind == "wood":
            B.detail_lines(cr, [[(k * 7.0, -2.0), (k * 7.5, -48.0)] for k in (-2, -1, 0, 1, 2)], 0.9, p.line, 0.45)
            il, ish, ideep, irim = _tones(q.light, C["iron"])
            for hy in (-10.0, -40.0):
                core.rounded_rect(cr, -19.5 + (0.6 if hy > -20 else 0.0), hy - 2.5, 39.0, 5.0, 1.5)
                _solid(cr, ish)
                core.rounded_rect(cr, -19.0, hy - 2.5, 38.0, 1.6, 0.8)
                _solid(cr, irim, 0.5)
        else:
            B.detail_lines(cr, [[(-18.0, -8.0), (18.0, -8.0)], [(-18.6, -44.0), (18.6, -44.0)]], 1.2, p.line, 0.5)
            B.sheen(cr, -9.0, -28.0, 4.0, 14.0, alpha=0.4)
    if foam > 0.01:
        fs = [(-21.0, -48.0), (-23.0, -55.0), (-14.0, -60.0 - 4 * foam), (-3.0, -63.0 - 5 * foam), (9.0, -61.0 - 4 * foam),
              (20.0, -57.0), (22.0, -50.0), (14.0, -47.0), (12.0, -40.0), (8.0, -46.0), (-8.0, -47.0), (-13.0, -42.0), (-16.0, -47.0)]
        fsh, fo = B.smooth_paths(cr, fs, max(lw, 0.01), 0.8)
        pf = q.shade(fsh, Mat.of(C["foam"], shadow_k=0.85), 10.0, outline=fo if outline else False)
        if q.detail >= 2:
            core.src(cr, pf.shadow, 0.5)
            for k in range(5):
                core.circle(cr, -12.0 + k * 6.0, -54.0 - 3 * math.sin(k * 1.7), 1.4)
            cr.fill()
    q.end()
    return PropRig(handle=q.C((-29.0 if flip else 29.0, -28.0)), top=q.C((0.0, -60.0)))


def tankard_hold(light=None, t=0.0, kind="wood", foam=1.0, side=1, tilt=0.0):
    """Hold callback: the fist round the tankard's handle, the mug upright beside the fist on
    `side` (+1: toward the fingertips' screen side). tilt leans it (a toast: -0.3)."""
    def cb(cr, f):
        cr.save()
        cr.rotate(-f.angle + tilt)
        flip = side < 0
        draw_tankard(cr, -29.0 * side + 0.0, 28.0, 1.0, light, t, kind, foam, flip=not flip)
        cr.restore()
    return cb


def draw_tavern_table(cr, x, y, scale=1.0, light=None, t=0.0, yaw=0.0, elev=0.28, length=420.0, depth=110.0,
                      height=115.0, clutter=True, seed=0, detail=None):
    """A long trestle table of dark oak (S4 inside): a thick top on two X-trestles and a
    stretcher, with tankards and a candle stub on it. Anchor = the ground point below the
    middle of the table; top `height` = 115 above the ground at scale 1.0 (the cast's tankards
    land at elbow height). Projected with B.Proj(yaw, elev) like the benches.
    Returns PropRig(top_center, top_y)."""
    q = _Ctx(cr, x, y, scale, 0.0, light, detail)
    proj = B.Proj(yaw, elev)
    oak = Mat.of("#5E3F24", sheen=0.2)
    L, D, H = length, depth, height
    for xe in sorted((-L / 2 + 50.0, L / 2 - 50.0), key=lambda e: proj.depth((e, 0, 0))):
        for zs in (-1, 1):
            a3 = (xe, 0.0, zs * D * 0.42)
            b3 = (xe, -H + 10.0, -zs * D * 0.3)
            pr_ = _tube_pair([proj.xy(a3), proj.xy(b3)], [6.0, 6.0], q.lw)
            _union_shade(q, [pr_], oak, 12.0, rim=0.5)
    _plank(q, proj, -L / 2 + 50.0, L / 2 - 50.0, -H * 0.45 - 5.0, -H * 0.45 + 5.0, -6.0, 6.0, oak, grain=False)
    _plank(q, proj, -L / 2, L / 2, -H - 9.0, -H + 2.0, -D / 2, D / 2, oak)
    if clutter:
        n = max(2, int(L // 120))
        for k in range(n):
            u = (k + 0.5) / n + core.jitter(k, 0.06, seed)
            px, py = proj.xy(((u - 0.5) * L * 0.9, -H - 9.0, core.jitter(k, D * 0.3, seed + 1)))
            draw_tankard(cr, px, py, 0.75, q.light, t, "wood" if (k + seed) % 2 else "pewter", 1.0, flip=k % 2 == 0,
                         outline=True, detail=q.detail)
        cx, cy = proj.xy((L * 0.08, -H - 9.0, -D * 0.2))
        core.rounded_rect(cr, cx - 5.0, cy - 16.0, 10.0, 16.0, 2.0)
        _solid(cr, _tones(q.light, "#E9DCC0")[0])
        _flame(cr, cx, cy - 16.0, 12.0, 3.4, t, seed + 3, PROP_COLORS["flame_warm"], PROP_COLORS["candle_hot"], 1.0)
    q.end()
    return PropRig(top_center=q.C(proj.xy((0.0, -H - 9.0, 0.0))), top_y=q.C(proj.xy((0.0, -H - 9.0, 0.0)))[1])
