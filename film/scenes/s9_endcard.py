"""s9_endcard.py -- SCENE 9: THE END CARD.  "Which of you, if your son asks for bread, will give him a stone?"

THE IDEA. The film closes the bard's book on one last illuminated page: gold and cream on a dark-dyed
vellum (the manner of the "Black Hours"), lit by one unseen candle, framed by blind-tooled rules with
a hair of gold and a gilded ivy spray in each corner. At its heart a painted miniature in a gilded
roundel: under an ultramarine night powdered with shell-gold stars, the kingdom on its high horizon
(the castle on the hill; far off, the garden's bench under its lantern -- both dark), a tilted-up
millefleur meadow, and in front, on a linen cloth spread on the grass, the two things the film is
about, side by side like two strangers on a bench: a grey slate rune-stone (the city's cold cyan in
its carved spiral -- the speaking stone's marks) and the gnome's round loaf, softly warm inside. Twins
in shape (the parable's stones look like loaves), opposite in substance. And in the margin, as in
every Book of Hours, a drollery: the cockatrice minstrel himself, perched on the curl at the end of
the left vine with his lute -- he sings the reprise we hear (bookending S0: bard left, book right).
The card acts the parable out once, quietly. On "...you know what to DO" the loaf breaks itself open
like a book: the halves snap apart, lean out and turn their torn crumb to us, a V of light stands
between them (the opened loaf makes a soft heart), flour puffs, crumbs patter onto the linen. Then,
while "Someone's hungry for bread on the bench next to you" is sung, the light spreads: over the cloth
and the meadow (the flowers catch it), onto the stone beside it on "hungry" (its runes gutter out; it
is only warm grey stone now, its shadow falling away from the bread), the castle's windows light one
by one, the far lantern over the bench catches on the word "bench", then the gold of the whole page --
stars, rim, vines, title, frame -- by "you". The film's colour script (cold and alone -> one warm pool
-> warmth spreading) replayed in sixteen seconds. Nothing touches the bread: it breaks for whoever
sits beside it.

ONE SHOT, LOCKED OFF (an end card is a page: its life is light and the little minstrel, not camera).
Layout (1920x1080). The page: tooled double rule 104..1816 x 56..872 with a gold hairline between and
an ivy spray at each corner; it ends ABOVE the caption band, so the reprise's sung captions sit under
the page like a colophon (nothing in the bottom ~200 px).
  TITLE   "THE STONE AND THE BREAD": Cinzel, letter-spaced, cream with a whisper of gold (base 172)
  ROUNDEL centre (960, 430), r 184: gilded double ring, madder band of gold pearls, trefoil cusps N/S;
          gold ivy vines (hedera leaves, tendrils, berries) run from its equator to curls under the
          title's ends. Inside, back to front: stars | horizon y 372 (hills; castle left; bench and
          lantern right) | meadow in painted rows with clumps of millefleurs | the linen cloth
          (madder border, gold thread, fringe) | stone x 876 and loaf x 1026 on it (tops ~ y 427)
          | foreground flowers.
  BARD    seated on the left vine's end curl (420, 370), scale 0.62 (~100 px), 3/4 toward the roundel.
  QUOTE   Cormorant Garamond Italic, cream, two lines (bases 712 / 772)
  ATTRIB  "-- Matthew 7:9": Cinzel in pale gold (base 840)
Eye-trace: the iris opens on the roundel (warm loaf vs cold stone: the most saturated, most contrasted
thing) -> a candle glint walks the title (a twinkle on the A of AND) -> the quote fades in -> the
minstrel tunes up and begins, his gaze leading along the vine to the loaf -> the break (the flash is
the brightest thing on the card) -> the light carries the eye out through the gold, up to the title,
to the frame -> on "you" the minstrel looks at US -> the final chord's glint, his wink -> the iris
closes on the bread.

BEATS (every time read from timeline.json and the reprise's syllable timing, song_timing.json;
today's values in brackets):
  s9_fadein 0-1.5     fade up from black as an iris opening from the miniature. Candlelit: the gold
                      deep and quiet; the loaf's scoring warm; the stone's spiral breathes cold cyan.
  1.3-3.0             a candle glint slides across the title; a twinkle pings on the A of AND.
  s9_quote 2.5-4.0    the quote and attribution fade in.
  hold -> T_WHAT      moving hold: candle flicker on the gold, motes, a thread of steam off the warm
                      loaf, a few stars twinkle, the glows breathe out of phase; the minstrel watches
                      his page, then tunes a peg [3.85-4.8]; s9_song [5.0]: he plays (strums, chord
                      hand, head-bob and foot from the song's beat grid), sings from 5.87 with his
                      beak on the vocal envelope; each lute BASS note [5.63 6.56 7.50 8.44] plucks a
                      glint from a pearl of the rim; one slow glint drifts along the vines (6.1-8.5).
  T_WHAT [8.75]       "...what to": the loaf holds its breath -- a slight swell, a fine tremble, a
                      hairline crack of light opens down its middle score (a crust crackle); on "to"
                      it squashes, about to give.
  T_BREAK [9.375]     "DO" (the sung note, also a lute bass note): it breaks. Flash; the halves snap
                      apart (a 0.04 s crack), lean out about their inner feet and turn their crumb to us
                      (ease-out with a small overshoot, settled by ~0.8 s); strands of crumb stretch
                      and snap; a V of white-gold light stands in the gap, rays fan up, flour puffs;
                      crumbs land on the linen [9.89-10.17] (cues bread_tear, crumbs). The minstrel's
                      brows lift into a smile. Steam curls off the crumb from here on.
  the spread          the ring of bread light, keyed to the sung accents: the cloth, meadow and stone
                      by "hungry" [10.31] (runes gutter out over 1.2 s), castle windows one by one
                      [~10.9-11.2], the rim by "bread" [11.25], the far lantern catches ON "bench"
                      [12.23] as the vines light out, the title and frame by "you" [13.40]. The
                      minstrel turns from the loaf to us on "next to you" [12.6-13.3] and holds the last
                      note to us, eyes closed in rapture.
  s9_final_chord [14.15] a soft swell over all the gold and a last glint across the title; the
                      minstrel opens his eyes on us, warm, and winks [14.70] with a twinkle.
  s9_fadeout 15.46-16.96 an iris that closes on the loaf: edges first, the bread's light last.

ACTING. The stone never moves: heavy, cold, patient; only its runes breathe, then die. The loaf
breathes, holds its breath, trembles, gives itself (anticipation: swell, squash; the snap;
follow-through: overshoot, settle; a long warm afterglow that keeps breathing). The minstrel: eyes on
his story; a tuning peg and a breath before he plays; thought -> glance -> line: he looks to the loaf
as he sings of it, lights up when it breaks, finds us on "next to you", sings the last note TO us,
then the wink -- the storyteller's goodbye (S0's coda wink, returned).

VALUE / COLOUR PLAN. Warm charcoal vellum in a narrow dark band; cream type (the lightest large
shapes); gold from deep candlelit ochre (unlit) to pale burnished gold (lit). Inside the roundel a
cold night (ultramarine, blue-green meadow, moonlit linen) with ONE warm accent -- the loaf -- set
against ONE cold accent -- the stone's cyan: the S8 palette (dark blue + one warm pool) in miniature.
The minstrel's burgundy and chestnut stay dim in the candle until the warmth reaches him. After the
break the gap of light is the brightest point and warm wins everywhere. Bloom (threshold 0.62) on the
light, the lit gold and the title; grain 3.5 %; a plum-brown vignette that opens with the fade-in.

PERIOD. A scribe's materials: dyed vellum, blind tooling, gold leaf on raised gesso with an ink edge,
shell-gold stars, madder, ultramarine, verdigris meadow, linen with a fringe, a slate stone, a crusty
boule, a castle, a candle-lantern on an iron post, a marginal minstrel with a lute. Lettering:
inscriptional capitals (Cinzel, OFL, film/assets/fonts) and a book italic (Cormorant Garamond).

BUILD. setup() renders the vellum (numpy), the tooling, the miniature's ground (sky, hills, castle,
bench + lantern, meadow rows, tufts, flowers, cloth, painted grain) and ALL the gilding (rings,
pearls, cusps, vines, corner sprays, frame hairline, the cloth's thread, the flowers' hearts, stars,
title) as coverage masks turned into two cached layers, "dim" (in the page) and "lit" (burnished,
metallic, with a gesso bevel and an ink edge). Each frame paints the page, then the lit gold through
a quarter-res LIGHT FIELD mask (candle flicker, glints, rim plucks, star twinkles, the spreading ring
of bread light, the final swell), the live miniature (warm pools, far lights, stone, loaf, crumbs,
flour, steam, rays), the quote, the minstrel (the bard rig, driven by bard_song), sparkles, motes,
the light layer + bloom, and the iris fades. ~100 ms/frame on the shared machine.
"""

import functools
import math
import subprocess

import cairocffi as cairo
import numpy as np
from scipy import ndimage
from scipy.interpolate import PchipInterpolator

from film.lib import core, fx, props as P, storybook as sb, timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B

SCENE = 9
W, H = core.W, core.H
TAU = math.tau
DUR = tl.scene(SCENE).duration

# ----------------------------------------------------------------------------------------
# timing: every beat from timeline.json and the reprise's own syllable timing
# ----------------------------------------------------------------------------------------


def _beat(bid, t_default, end_default=None):
    if tl.has_beat(bid):
        b = tl.beat(bid)
        return b.t, (b.end if b.end is not None else end_default)
    return t_default, end_default


T_FADE_IN0, T_FADE_IN1 = _beat("s9_fadein", 0.0, 1.5)
T_QUOTE0, T_QUOTE1 = _beat("s9_quote", 2.5, 4.0)
T_SONG, _ = _beat("s9_song", 5.0)
T_FINAL, _ = _beat("s9_final_chord", DUR - 2.8)
T_FADE_OUT0, T_FADE_OUT1 = _beat("s9_fadeout", DUR - 1.5, DUR)
L1 = tl.line("s9_l1")
L2 = tl.line("s9_l2")


@functools.lru_cache(maxsize=1)
def _reprise():
    """(offset, {word: [(start, note)]}, bass note times) of the sung reprise in LOCAL scene time.
    offset maps song time -> scene time (the reprise's first sung line starts at s9_l1)."""
    try:
        R = ch.bard_song_timing()["reprise"]
        off = L1.start - float(R["lines"][0]["start"])
        words = {}
        for ln in R["lines"]:
            for w in ln.get("words", []):
                key = "".join(c for c in w["w"].lower() if c.isalpha())
                words.setdefault(key, []).append((off + float(w["start"]), off + float(w.get("note", w["start"]))))
        bass = [off + float(s["t"]) for s in R.get("strokes", []) if s.get("kind") == "bass"]
        return off, words, bass
    except Exception:
        return None, {}, []


def _word_note(word, k=0, fallback=None):
    """Scene time of the musical note under a sung word (its k-th occurrence)."""
    occ = _reprise()[1].get(word)
    if occ and len(occ) > k:
        return occ[k][1]
    return fallback


# "...you know what to DO": the loaf breaks on the note under "do" (a lute bass downbeat)
T_BREAK = _word_note("do", 0, L1.end - 0.4)
T_WHAT = min(_word_note("what", 0, T_BREAK - 0.62), T_BREAK - 0.35)    # it holds its breath, a crack opens
# the spreading light lands its stages on the sung accents of the second line
T_HUNGRY = max(T_BREAK + 0.6, _word_note("hungry", 0, L2.start + 0.5))
T_BREADW = max(T_HUNGRY + 0.4, _word_note("bread", 0, L2.start + 1.45))
T_BENCH = max(T_BREADW + 0.4, _word_note("bench", 0, L2.start + 2.45))
T_YOU2 = max(T_BENCH + 0.4, _word_note("you", 1, L2.start + 3.6))
T_NEXT = _word_note("next", 0, T_YOU2 - 0.8)                    # "...next to YOU": the bard turns to us
T_WINK = T_FINAL + 0.55                                          # eyes open on the final chord, then a wink
T_GLINT0, T_GLINT1 = T_FADE_IN0 + 1.3, T_FADE_IN0 + 3.0         # the candle glint across the title
T_VGLINT0 = T_SONG + 1.1                                         # a slow glint along the vines in the hold...
T_VGLINT1 = min(T_VGLINT0 + 2.4, T_WHAT - 0.2)                   # ...done before the loaf holds its breath
T_LAST0 = T_FINAL + 0.05                                         # the final chord's glint across the title
T_LAST1 = min(T_FINAL + 1.25, T_FADE_OUT0 - 0.05)
# lute bass notes before the break each pluck a glint from the roundel's rim
PLUCKS = [tb for tb in _reprise()[2] if T_SONG < tb < T_WHAT - 0.1]


def _spread_curve():
    """The ring of bread light: radius (px from the gap) against time, through the lyric's accents."""
    keys = [(T_BREAK, 0.0), (T_BREAK + 0.45, 85.0), (T_HUNGRY, 150.0), (T_BREADW, 250.0), (T_BENCH, 560.0),
            (T_YOU2, 900.0), (max(T_FINAL, T_YOU2 + 0.4), 1120.0), (max(DUR + 1.0, T_FINAL + 1.5), 1450.0)]
    ts, rs = [], []
    for tk, rk in keys:
        if ts and tk <= ts[-1] + 0.05:
            tk = ts[-1] + 0.05
        ts.append(tk)
        rs.append(rk)
    f = PchipInterpolator(ts, rs)
    grid = np.linspace(ts[0], ts[-1], 800)
    return f, ts[-1], grid, f(grid)


_SPREAD, _SPREAD_END, _SP_T, _SP_R = _spread_curve()
FRONT_MAX = float(_SP_R[-1])


def _front(t):
    """Radius (px) of the spreading ring of bread light, or None before the break."""
    if t < T_BREAK:
        return None
    return float(_SPREAD(min(t, _SPREAD_END)))


def _t_of_radius(d):
    """Seconds after the break at which the ring of light reaches radius d."""
    return float(np.interp(d, _SP_R, _SP_T)) - T_BREAK


# ----------------------------------------------------------------------------------------
# layout
# ----------------------------------------------------------------------------------------

CX = W / 2.0
TITLE = "THE STONE AND THE BREAD"
TITLE_SIZE, TITLE_SPACING, TITLE_BASE = 62.0, 14.0, 172.0
RC = (CX, 430.0)                      # the roundel's centre
RR = 184.0                            # its inner (painted) radius
RING = (3.5, 12.5, 17.5)              # inner gold ring | madder band with pearls | outer gold ring (radii past RR)
QUOTE = ("“Which of you, if your son asks for bread,", "will give him a stone?”")
QUOTE_SIZE, QUOTE_BASES = 50.0, (712.0, 772.0)
ATTRIB = "— Matthew 7:9"
ATTRIB_SIZE, ATTRIB_BASE = 30.0, 840.0
FRAME = (104.0, 56.0, W - 104.0, 872.0)   # the blind-tooled border (it ends above the caption band)
GOLD_RULE = 4.6                       # the gold hairline, inset between the two tooled rules
# the miniature: a high (medieval) horizon, a tilted-up meadow, the cloth in front
HORIZON = RC[1] - 58.0
CLOTH = [(RC[0] - 146.0, RC[1] + 44.0), (RC[0] + 150.0, RC[1] + 41.0),     # back-left, back-right
         (RC[0] + 194.0, RC[1] + 128.0), (RC[0] - 190.0, RC[1] + 132.0)]   # front-right, front-left
STONE_X, STONE_BASE = RC[0] - 84.0, RC[1] + 66.0       # the stone sits a little further back...
LOAF_R = 62.0                                          # ...the loaf (the gnome's boule, on-model) in front
LOAF_X, LOAF_BASE = RC[0] + 66.0, RC[1] + 75.0
LOAF_Y = LOAF_BASE - 0.56 * LOAF_R                     # the centre of the loaf's outline (its base is 0.56 r below)
BREAD_LIGHT = (LOAF_X, LOAF_Y - 0.12 * LOAF_R)         # where the warm light comes from (the gap)
CASTLE = (RC[0] - 92.0, HORIZON - 26.0)                # base centre of the castle on the left hill
LANTERN = (RC[0] + 106.0, HORIZON - 9.0)               # foot of the far garden's lantern post
PHI_MAX = 0.40                                         # how far each half turns its crumb to us (rad)
TILT_MAX = 0.28                                        # how far each half leans out about its inner foot (rad)

BARD_SCALE = 0.62                                      # the marginal minstrel (a drollery on the vine's end)

# palette
CHARCOAL = "#28221f"
NIGHT = ("#3a4c8c", "#22306a", "#121a40")
MADDER = "#5b1f24"
WARM = "#ffc46b"
WARM_HOT = "#fff1c8"
RUNE = P.PROP_COLORS["rune"]
MATS = P.prop_mats()


@functools.lru_cache(maxsize=8)
def _font_ok(name):
    try:
        out = subprocess.run(["fc-list", ":family=" + name, "family"], capture_output=True, text=True, timeout=5)
        return bool(out.stdout.strip())
    except Exception:
        return False


def _ensure_font(family, filename):
    """The title's OFL font lives in film/assets/fonts; if fontconfig does not know it yet, install it
    the way SPEC section 2 says (~/.fonts + fc-cache) so the card never silently falls back."""
    if _font_ok(family):
        return True
    try:
        import os
        import shutil
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", filename)
        dst_dir = os.path.expanduser("~/.fonts")
        if os.path.isfile(src):
            os.makedirs(dst_dir, exist_ok=True)
            if not os.path.isfile(os.path.join(dst_dir, filename)):
                shutil.copyfile(src, os.path.join(dst_dir, filename))
            subprocess.run(["fc-cache", "-f", dst_dir], capture_output=True, timeout=60)
            _font_ok.cache_clear()
    except Exception:
        pass
    return _font_ok(family)


TITLE_FONT = "Cinzel" if _ensure_font("Cinzel", "Cinzel-Variable.ttf") else core.SERIF   # OFL, film/assets/fonts
QUOTE_FONT = core.SERIF                                         # Cormorant Garamond Italic


def _font_opts(cr):
    """Unhinted outlines and metrics: letter-spaced type keeps its true spacing."""
    fo = cairo.FontOptions()
    fo.set_hint_style(cairo.HINT_STYLE_NONE)
    fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    fo.set_antialias(cairo.ANTIALIAS_GRAY)
    cr.set_font_options(fo)


@functools.lru_cache(maxsize=1)
def _title_metrics():
    """(total width, x of the A-apex of AND, x of the end of BREAD's D) for the title."""
    s, c = core.frame(8, 8)
    _font_opts(c)
    core.set_font(c, TITLE_SIZE, TITLE_FONT)

    def adv(txt):
        return core._advance(c, txt, TITLE_SPACING) + (TITLE_SPACING if txt else 0.0)

    w = core._advance(c, TITLE, TITLE_SPACING)
    x0 = CX - w / 2.0
    xa = x0 + adv("THE STONE ") + c.text_extents("A")[4] * 0.5
    xd = x0 + w - c.text_extents("D")[4] * 0.3
    return w, xa, xd


TITLE_W, TITLE_A_X, TITLE_END_X = _title_metrics()
CAP_H = TITLE_SIZE * 0.714

# ----------------------------------------------------------------------------------------
# numpy <-> cairo helpers
# ----------------------------------------------------------------------------------------


def _a8(draw, w=W, h=H):
    """Coverage mask (float32 0..1, h x w) of whatever draw(cr) fills on an A8 surface."""
    s = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
    c = cairo.Context(s)
    c.set_antialias(cairo.ANTIALIAS_GOOD)
    _font_opts(c)
    draw(c)
    s.flush()
    st = s.get_stride()
    return np.frombuffer(s.get_data(), np.uint8).reshape(h, st)[:, :w].astype(np.float32) / 255.0


def _surface(rgb, alpha=None):
    """float RGB (h, w, 3) in 0..1 (+ optional alpha) -> premultiplied ARGB32 cairo surface."""
    h, w = rgb.shape[:2]
    a = np.ones((h, w), np.float32) if alpha is None else np.clip(alpha, 0.0, 1.0)
    out = np.empty((h, w, 4), np.uint8)
    pm = np.clip(rgb, 0.0, 1.0) * a[..., None]
    out[..., 0] = np.round(pm[..., 2] * 255.0)
    out[..., 1] = np.round(pm[..., 1] * 255.0)
    out[..., 2] = np.round(pm[..., 0] * 255.0)
    out[..., 3] = np.round(a * 255.0)
    data = bytearray(out.tobytes())
    s = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h, w * 4)
    s._keep = data
    return s


def _rgb(c):
    return np.array(core.col(c)[:3], np.float32)


def _mix(a, b, u):
    """Blend two colours (arrays) by u (scalar or (h, w) array)."""
    u = np.asarray(u, np.float32)
    if u.ndim == 2:
        u = u[..., None]
    return a + (b - a) * u


class _Img:
    """A cached ARGB surface placed at (x, y) in frame coordinates."""

    def __init__(self, surf, x=0, y=0):
        self.s, self.x, self.y = surf, x, y

    def paint(self, cr, alpha=1.0):
        cr.save()
        cr.set_source_surface(self.s, self.x, self.y)
        cr.get_source().set_filter(cairo.FILTER_FAST)
        if alpha >= 0.999:
            cr.paint()
        else:
            cr.paint_with_alpha(max(0.0, alpha))
        cr.restore()

    def paint_masked(self, cr, mask_pat):
        cr.save()
        cr.rectangle(self.x, self.y, self.s.get_width(), self.s.get_height())
        cr.clip()
        cr.set_source_surface(self.s, self.x, self.y)
        cr.get_source().set_filter(cairo.FILTER_FAST)
        cr.mask(mask_pat)
        cr.restore()


def _bbox(M, pad=6):
    ys, xs = np.nonzero(M > 0.002)
    if len(xs) == 0:
        return 0, 0, 1, 1
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad + 1)
    return int(x0), int(y0), int(x1), int(y1)


def _crop_img(rgb, a, box):
    x0, y0, x1, y1 = box
    return _Img(_surface(rgb[y0:y1, x0:x1], a[y0:y1, x0:x1]), x0, y0)


# ----------------------------------------------------------------------------------------
# ornament geometry (frame coordinates)
# ----------------------------------------------------------------------------------------


def _heart_pts(x, y, size, angle, n=30):
    """A hedera (ivy-heart) leaf: its cleft at (x, y), its tip `size` away along `angle`."""
    pts = []
    for k in range(n):
        a = TAU * k / n
        hx = 16.0 * math.sin(a) ** 3
        hy = -(13.0 * math.cos(a) - 5.0 * math.cos(2 * a) - 2.0 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((hx, hy + 5.0))           # cleft at the origin, tip at +22 (y down)
    k = size / 22.0
    ca, sa = math.cos(angle - math.pi / 2), math.sin(angle - math.pi / 2)
    return [(x + (px * ca - py * sa) * k, y + (px * sa + py * ca) * k) for px, py in pts]


def _spiral_pts(cx, cy, r0, r1, a0, turns, sign=1.0, n=28):
    out = []
    for i in range(n + 1):
        u = i / n
        a = a0 + sign * turns * TAU * u
        r = r0 + (r1 - r0) * (u ** 0.9)
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


def _vine(side):
    """One side's vine scroll as (stems, leaves, dots): stems = [(pts, w0, w1)], leaves = [pts],
    dots = [(x, y, r)]. side = +1 (right of the roundel) or -1 (left, mirrored)."""
    ox, oy = RC[0] + side * (RR + RING[2] + 1.0), RC[1]

    def P_(x, y):
        return (ox + side * x, oy + y)

    stems, leaves, dots = [], [], []
    # the main stem: a gentle wave outward, ending in a spiral curl under the end of the title
    end_x = TITLE_W / 2.0 - (RR + RING[2] + 1.0) - 34.0
    main = [P_(0, 0), P_(end_x * 0.16, -11), P_(end_x * 0.34, -15), P_(end_x * 0.52, -2), P_(end_x * 0.70, 9),
            P_(end_x * 0.86, 4)]
    sc = (end_x * 0.97 - 4.0, -36.0)
    sp = _spiral_pts(0, 0, 26.0, 5.0, math.pi * 0.5, 1.55, sign=-1.0, n=30)
    spiral = [P_(sc[0] + px, sc[1] + py) for px, py in sp]
    stems.append((main + spiral, 6.5, 1.6))

    def tendril(u_x, u_y, up, size, curl_r):
        sgn = -1.0 if up else 1.0
        c = (u_x + size * 0.55, u_y + sgn * size * 0.95)
        sp2 = _spiral_pts(0, 0, curl_r, curl_r * 0.25, math.pi, 1.3, sign=(1.0 if up else -1.0), n=18)
        pts = [P_(u_x, u_y), P_(u_x + size * 0.18, u_y + sgn * size * 0.55)] + \
              [P_(c[0] + px, c[1] + py) for px, py in sp2]
        stems.append((pts, 3.2, 1.0))

    tendril(end_x * 0.24, -14.0, True, 44.0, 14.0)
    tendril(end_x * 0.44, -9.0, False, 38.0, 12.5)
    tendril(end_x * 0.62, 5.0, True, 42.0, 13.5)
    tendril(end_x * 0.80, 7.0, False, 36.0, 11.5)
    # hedera leaves on short stalks (the stalk runs on into the leaf's cleft: no dark notch)
    for (ux, uy, ang, sz) in ((end_x * 0.10, -8.0, -1.25, 23.0), (end_x * 0.34, -15.0, 1.15, 21.0),
                              (end_x * 0.53, -2.0, -1.05, 22.0), (end_x * 0.72, 9.0, 1.2, 19.0),
                              (end_x * 0.90, 0.0, -0.9, 17.0)):
        bx, by = P_(ux, uy)
        a = ang if side > 0 else math.pi - ang
        lx, ly = bx + math.cos(a) * 9.0, by + math.sin(a) * 9.0
        stems.append(([(bx, by), (lx + math.cos(a) * 5.0, ly + math.sin(a) * 5.0)], 2.6, 2.0))
        leaves.append(_heart_pts(lx, ly, sz, a))
    # berries (triplets of gold dots) and single pearls along the stem
    for (ux, uy) in ((end_x * 0.28, 17.0), (end_x * 0.47, -28.0), (end_x * 0.66, 28.0), (end_x * 0.85, -25.0)):
        bx, by = P_(ux, uy)
        for k in range(3):
            a = TAU * k / 3 + 0.5
            dots.append((bx + math.cos(a) * 4.4, by + math.sin(a) * 4.4, 2.5))
    for (ux, uy) in ((end_x * 0.05, 13.0), (end_x * 0.05, -15.0)):
        bx, by = P_(ux, uy)
        dots.append((bx, by, 2.1))
    return stems, leaves, dots


def _corner_pieces():
    """A gilded ivy spray in each corner of the page, in the vines' vocabulary: from a small
    quatrefoil on the inner rule's corner two stems run along the rules, each carrying a hedera leaf
    and ending in a curl, with a berry triplet on the diagonal."""
    stems, leaves, dots = [], [], []
    x0, y0, x1, y1 = FRAME
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ix, iy = cx + sx * 9.0, cy + sy * 9.0                    # the inner rule's corner

        def P_(x, y, ix=ix, iy=iy, sx=sx, sy=sy):
            return (ix + sx * x, iy + sy * y)

        for swap in (False, True):
            def Q(x, y, swap=swap, P_=P_):
                return P_(y, x) if swap else P_(x, y)

            def ang(a, swap=swap, sx=sx, sy=sy):
                ux, uy = math.cos(a), math.sin(a)
                if swap:
                    ux, uy = uy, ux
                return math.atan2(sy * uy, sx * ux)

            curl = _spiral_pts(96.0, 21.0, 11.0, 2.4, -math.pi / 2, 1.3, sign=1.0, n=22)
            main = [(11.0, 11.0), (32.0, 13.5), (58.0, 12.5), (82.0, 10.0)] + curl
            stems.append(([Q(x, y) for (x, y) in main], 3.4, 1.1))
            # a leaf on a short stalk, hanging inward off the stem
            bx, by = 46.0, 13.2
            a = 1.15
            lx, ly = bx + math.cos(a) * 7.0, by + math.sin(a) * 7.0
            stems.append(([Q(bx, by), Q(lx + math.cos(a) * 4.0, ly + math.sin(a) * 4.0)], 2.2, 1.8))
            leaves.append(_heart_pts(*Q(lx, ly), 17.0, ang(a)))
            # a small tendril curling up off the stem toward the rule
            tc = _spiral_pts(0, 0, 6.5, 1.6, math.pi * 0.5, 1.2, sign=-1.0, n=14)
            tpts = [(66.0, 11.5), (70.0, 4.0)] + [(74.0 + px, -1.0 + py) for px, py in tc]
            stems.append(([Q(x, y) for (x, y) in tpts], 2.0, 0.8))
        qx, qy = P_(11.0, 11.0)                                  # the quatrefoil on the corner
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            dots.append((qx + math.cos(a) * 5.4, qy + math.sin(a) * 5.4, 4.4))
        dots.append((qx, qy, 2.4))
        bx, by = P_(30.0, 30.0)                                  # berries on the diagonal
        for k in range(3):
            a = TAU * k / 3 + 0.8
            dots.append((bx + math.cos(a) * 4.2, by + math.sin(a) * 4.2, 2.4))
    return stems, leaves, dots


def _ornaments_path(cr, stems, leaves, dots):
    for pts, w0, w1 in stems:
        core.tapered(cr, pts, w0, w1, cap=True)
    for pts in leaves:
        core.smooth_closed(cr, pts, 0.6)
    for (x, y, r) in dots:
        core.circle(cr, x, y, r)


def _ring_path(cr, r0, r1):
    cr.new_sub_path()
    cr.arc(RC[0], RC[1], r1, 0, TAU)
    cr.close_path()
    cr.new_sub_path()
    cr.arc_negative(RC[0], RC[1], r0, TAU, 0)
    cr.close_path()


def _pearls():
    """Gold pearls in the madder band: [(angle, x, y)], starting at the top, clockwise."""
    rm = RR + (RING[0] + RING[1]) / 2.0
    n = 60
    return [(TAU * k / n - math.pi / 2, RC[0] + math.cos(TAU * k / n - math.pi / 2) * rm,
             RC[1] + math.sin(TAU * k / n - math.pi / 2) * rm) for k in range(n)]


def _cusps():
    """Small gilded trefoil cusps on the outer ring at N and S (E and W carry the vines)."""
    out = []
    for a in (-math.pi / 2, math.pi / 2):
        r = RR + RING[2] + 5.0
        out.append((RC[0] + math.cos(a) * r, RC[1] + math.sin(a) * r, a))
    return out


# the far hills on the high horizon: (dx from the centre, dy from HORIZON)
_HILLS = [(-206.0, 8.0), (-178.0, -5.0), (-150.0, -19.0), (-124.0, -27.0), (-98.0, -29.0), (-72.0, -22.0),
          (-46.0, -12.0), (-18.0, -8.0), (10.0, -12.0), (38.0, -16.0), (66.0, -13.0), (92.0, -9.0),
          (120.0, -10.0), (150.0, -17.0), (178.0, -11.0), (206.0, 2.0)]


def _hill_y(x):
    """y of the far hills' crest above frame x."""
    return HORIZON + float(np.interp(x - RC[0], [p[0] for p in _HILLS], [p[1] for p in _HILLS]))


def _castle_box():
    return (CASTLE[0] - 30.0, CASTLE[1] - 54.0, CASTLE[0] + 30.0, CASTLE[1] + 4.0)


def _lantern_box():
    return (LANTERN[0] - 46.0, LANTERN[1] - 48.0, LANTERN[0] + 12.0, LANTERN[1] + 4.0)


def _in_box(x, y, b, m=0.0):
    return b[0] - m <= x <= b[2] + m and b[1] - m <= y <= b[3] + m


@functools.lru_cache(maxsize=1)
def _stars():
    """The shell-gold stars of the miniature's sky: [(x, y, r, kind)] (kind 0 star, 1 dot)."""
    out = []
    step = 30.0
    for j in range(0, 8):
        for i in range(-8, 9):
            x = RC[0] + i * step + (step / 2.0 if j % 2 else 0.0)
            y = HORIZON - 30.0 - j * step * 0.87
            ok = (math.hypot(x - RC[0], y - RC[1]) < RR - 10 and y < _hill_y(x) - 12
                  and not _in_box(x, y, _castle_box(), 9) and not _in_box(x, y, _lantern_box(), 9))
            if ok:
                out.append((x, y, 4.2 + 1.2 * core.hash01(i * 31 + j, 5), 0))
            xd, yd = x + step * 0.5, y - step * 0.29          # tiny dots between the stars
            okd = (math.hypot(xd - RC[0], yd - RC[1]) < RR - 8 and yd < _hill_y(xd) - 9
                   and not _in_box(xd, yd, _castle_box(), 6) and not _in_box(xd, yd, _lantern_box(), 6))
            if okd:
                out.append((xd, yd, 1.2, 1))
    return out


def _star_path(cr, x, y, r):
    """An eight-pointed star (four long rays, four short)."""
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * TAU / 16
        rr = r if k % 4 == 0 else (r * 0.55 if k % 2 == 0 else r * 0.26)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    core.polygon(cr, pts)


def _cloth_q(u, v):
    """A point on the linen cloth: u 0..1 left -> right, v 0..1 back -> front (bilinear in the quad)."""
    bl, br, fr, fl = CLOTH
    bx, by = bl[0] + (br[0] - bl[0]) * u, bl[1] + (br[1] - bl[1]) * u
    fx_, fy_ = fl[0] + (fr[0] - fl[0]) * u, fl[1] + (fr[1] - fl[1]) * u
    return bx + (fx_ - bx) * v, by + (fy_ - by) * v


def _in_cloth(x, y, m=0.0):
    pts = CLOTH
    inside = True
    for i in range(4):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 4]
        # inward normal of a clockwise quad (y down): cross product sign
        cross = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        L = math.hypot(x1 - x0, y1 - y0)
        if cross / L < -m:
            inside = False
    return inside


@functools.lru_cache(maxsize=1)
def _flowers():
    """Millefleurs in the night meadow, in small clumps: [(x, y, size, kind)] -- off the cloth and
    the objects, sparse at the back, bigger in front of the cloth."""
    rng = np.random.default_rng(29)

    def ok(x, y, out, s):
        if math.hypot(x - RC[0], y - RC[1]) > RR - 12 or _in_cloth(x, y, 11.0) or y < _hill_y(x) + 7.0:
            return False
        if abs(x - STONE_X) < 70 and STONE_BASE - 80 < y < STONE_BASE + 12:
            return False
        if abs(x - LOAF_X) < 104 and LOAF_BASE - 86 < y < LOAF_BASE + 12:
            return False
        return not any(math.hypot(x - a, y - b) < 11.0 * max(s, c) for a, b, c, _k in out)

    out = []
    clumps = 0
    tries = 0
    n_clumps = 17
    while clumps < n_clumps and tries < 4000:
        tries += 1
        cx = RC[0] - RR + (clumps % 9 + rng.uniform(0.1, 0.9)) * (2.0 * RR / 9.0)    # one per strip, twice over
        cy = rng.uniform(HORIZON + 9.0, RC[1] + RR)
        depth = core.clamp((cy - HORIZON) / (RC[1] + RR - HORIZON))
        s = 0.6 + 1.1 * depth
        if not ok(cx, cy, out, s):
            continue
        clumps += 1
        kind = int(rng.integers(0, 3))
        for j in range(int(rng.integers(2, 5))):
            x = cx + (rng.normal(0.0, 9.0 * s) if j else 0.0)
            y = cy + (rng.normal(0.0, 3.5 * s) if j else 0.0)
            ss = s * (0.8 + 0.35 * rng.uniform())
            if ok(x, y, out, ss):
                out.append((x, y, ss, kind if rng.uniform() < 0.75 else int(rng.integers(0, 3))))
    return out


# ----------------------------------------------------------------------------------------
# static art (setup)
# ----------------------------------------------------------------------------------------


def _vellum():
    """Warm charcoal vellum: a candle pool round the composition, mottling, fibres, darker edges."""
    from PIL import Image
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = _rgb(CHARCOAL)
    warm = _rgb("#3a2f28")
    d = np.sqrt(((xx - CX) / 1.3) ** 2 + (yy - RC[1]) ** 2) / 820.0
    pool = np.clip(1.0 - d, 0.0, 1.0) ** 1.6
    img = base[None, None, :] * 0.86 + (warm - base * 0.86)[None, None, :] * pool[..., None]
    mot = core.noise_array(W, H, scale=150.0, octaves=4, seed=91)
    fib = core.noise_array(W // 2, H, scale=6.0, octaves=2, seed=92)
    fib = np.asarray(Image.fromarray(fib, "F").resize((W, H), Image.BILINEAR), np.float32)
    fine = core.noise_array(W, H, scale=2.0, octaves=1, seed=93)
    k = 1.0 + 0.055 * mot + 0.018 * fib + 0.012 * fine
    return np.clip(img * k[..., None], 0.0, 1.0)


def _gild(M, crinkle, refl, lit, light_dir=(-0.55, -0.83), soft=1.3):
    """Gold leaf on raised gesso from a coverage mask: unlit (deep, candlelit) or lit (burnished,
    metallic). A bevel from the mask's blurred gradient lights the edges facing the candle, a
    mid-frequency 'reflection' field makes it read as metal, and a dark ink edge contains it."""
    G = ndimage.gaussian_filter(M, soft)
    gy, gx = np.gradient(G)
    lx, ly = light_dir
    bev = -(gx * lx + gy * ly) * 3.4
    hi = np.clip(bev, 0.0, 1.0)
    lo = np.clip(-bev, 0.0, 1.0)
    edge = np.clip(M - ndimage.grey_erosion(M, size=(3, 3)), 0.0, 1.0)
    if lit:
        r = np.clip((refl + 0.35) / 0.9, 0.0, 1.0)
        rgb = _mix(_rgb("#a36f1f"), _rgb("#f6d274"), 0.30 + 0.70 * r)
        rgb = rgb * (1.0 + 0.07 * crinkle[..., None])
        rgb = _mix(rgb, _rgb("#fffae6"), (hi ** 0.75) * 0.95)
        rgb = _mix(rgb, _rgb("#6a4512"), lo * 0.55)
        rgb = _mix(rgb, _rgb("#5a3810"), edge * 0.55)
    else:
        r = np.clip((refl + 0.45) / 1.0, 0.0, 1.0)
        rgb = _mix(_rgb("#674b1d"), _rgb("#b38a3d"), 0.25 + 0.75 * r)
        rgb = rgb * (1.0 + 0.09 * crinkle[..., None])
        rgb = _mix(rgb, _rgb("#e6c473"), hi * 0.8)
        rgb = _mix(rgb, _rgb("#3a2a10"), lo * 0.45)
        rgb = _mix(rgb, _rgb("#2a1c0b"), edge * 0.55)
    return np.clip(rgb, 0.0, 1.0)


def _leaf_textures():
    """(crinkle, reflection): fine crinkle with the faint seams of the laid squares, and a
    mid-frequency field of what each patch of leaf reflects."""
    crink = 0.6 * core.noise_array(W, H, scale=2.5, octaves=2, seed=71) + 0.5 * core.noise_array(W, H, scale=24.0, octaves=2, seed=72)
    yy, xx = np.mgrid[0:H, 0:W]
    cell = 44
    ci = (xx // cell) * 7919 + (yy // cell) * 104729
    sq = ((ci * 2654435761) % 1000) / 1000.0 - 0.5
    seam = ((xx % cell) < 1) | ((yy % cell) < 1)
    crink = crink + 0.3 * sq - 0.45 * seam
    refl = 1.25 * core.noise_array(W, H, scale=11.0, octaves=2, seed=73)
    return crink.astype(np.float32), refl.astype(np.float32)


def _gild_text(M, lit):
    """Gilded small lettering (the attribution): legible pale gold, a soft bevel, no leaf seams."""
    G = ndimage.gaussian_filter(M, 0.8)
    gy, gx = np.gradient(G)
    bev = -(gx * -0.55 + gy * -0.83) * 3.0
    hi, lo = np.clip(bev, 0, 1), np.clip(-bev, 0, 1)
    yy = np.arange(H, dtype=np.float32)[:, None]
    v = np.broadcast_to(np.clip((yy - (ATTRIB_BASE - 22.0)) / 22.0, 0.0, 1.0), M.shape)
    if lit:
        rgb = _mix(_rgb("#fff0c2"), _rgb("#f0c25e"), v)
        rgb = _mix(rgb, _rgb("#fffbea"), hi * 0.6)
    else:
        rgb = _mix(_rgb("#e3c784"), _rgb("#b98e45"), v)
        rgb = _mix(rgb, _rgb("#f1dba0"), hi * 0.5)
    rgb = _mix(rgb, _rgb("#6b4a1c"), lo * 0.4)
    return np.clip(rgb, 0, 1)


def _title_layers(crinkle):
    """Title coverage -> (mask, dim, lit): cream with a whisper of gold; lit = burnished gold-white."""
    def draw(c):
        core.text_path(c, TITLE, CX, TITLE_BASE, TITLE_SIZE, TITLE_FONT, align="center", spacing=TITLE_SPACING)
        c.fill()
    M = _a8(draw)
    yy = np.arange(H, dtype=np.float32)[:, None]
    cap_top = TITLE_BASE - CAP_H
    v = np.broadcast_to(np.clip((yy - cap_top) / CAP_H, 0.0, 1.0), M.shape)
    G = ndimage.gaussian_filter(M, 1.0)
    gy, gx = np.gradient(G)
    bev = -(gx * -0.55 + gy * -0.83) * 3.2
    hi, lo = np.clip(bev, 0, 1), np.clip(-bev, 0, 1)
    dim = _mix(_rgb("#f2e8d1"), _rgb("#dcc490"), v ** 1.35)                     # cream -> a whisper of gold
    dim = dim * (1.0 + 0.015 * crinkle[..., None])
    dim = _mix(dim, _rgb("#9c8456"), lo * 0.35)
    lit = _mix(_rgb("#fffdf4"), _rgb("#ffcf6a"), v ** 1.0)
    lit = _mix(lit, _rgb("#ffffff"), hi * 0.6)
    lit = _mix(lit, _rgb("#b98a3a"), lo * 0.35)
    return M, np.clip(dim, 0, 1), np.clip(lit, 0, 1)


def _draw_castle(cr):
    """The castle on the far hill: a curtain wall, two towers and a keep with cone roofs and a
    pennant, cold blue-grey in the moonlight; its windows are dark (they light later)."""
    x0, y0 = CASTLE
    wall, wall_dk, roof, roof_dk = "#46538a", "#333f72", "#5a3a5e", "#432a4a"

    def R(a, b, c, d, col):
        cr.rectangle(x0 + a, y0 + b, c - a, d - b)
        core.src(cr, col)
        cr.fill()

    def merlons(a, c, y, col, w=3.0, gap=3.2):
        x = a
        while x + w <= c + 0.01:
            cr.rectangle(x0 + x, y0 + y - 3.2, w, 3.4)
            x += w + gap
        core.src(cr, col)
        cr.fill()

    def cone(a, c, y, h, col, col_dk):
        m = (a + c) / 2.0
        core.polygon(cr, [(x0 + a - 1.5, y0 + y), (x0 + m, y0 + y - h), (x0 + c + 1.5, y0 + y)])
        core.src(cr, col)
        cr.fill()
        core.polygon(cr, [(x0 + m, y0 + y), (x0 + m, y0 + y - h), (x0 + c + 1.5, y0 + y)])
        core.src(cr, col_dk)
        cr.fill()

    R(-21, -13, 21, 2, wall)                       # curtain wall
    merlons(-20, 20, -13, wall)
    R(-25, -27, -15, 2, wall)                      # left tower
    R(-20, -27, -15, 2, wall_dk)
    cone(-25, -15, -27, 12, roof, roof_dk)
    R(15, -24, 25, 2, wall)                        # right tower
    R(20, -24, 25, 2, wall_dk)
    cone(15, 25, -24, 11, roof, roof_dk)
    R(-8, -33, 8, -12, wall)                       # the keep
    R(0, -33, 8, -12, wall_dk)
    merlons(-8, 8, -33, wall)
    cone(-6, 6, -36, 12, roof, roof_dk)
    R(-6, -36, 6, -33, wall)
    cr.rectangle(x0 - 0.5, y0 - 54, 1.0, 7)         # the pennant on the keep
    core.src(cr, "#2c3155")
    cr.fill()
    core.polygon(cr, [(x0 + 0.5, y0 - 54), (x0 + 8.5, y0 - 51.5), (x0 + 0.5, y0 - 49)])
    core.src(cr, "#6e2a33")
    cr.fill()
    cr.new_path()                                   # the gate (dark)
    cr.move_to(x0 - 3.2, y0 + 2)
    cr.line_to(x0 - 3.2, y0 - 3)
    cr.arc(x0, y0 - 3, 3.2, math.pi, TAU)
    cr.line_to(x0 + 3.2, y0 + 2)
    cr.close_path()
    core.src(cr, "#161a30")
    cr.fill()
    for (wx, wy) in _CASTLE_WINDOWS:                # windows: dark slits (they light later)
        cr.rectangle(x0 + wx - 1.0, y0 + wy - 1.8, 2.0, 3.6)
    core.src(cr, "#161a30")
    cr.fill()


# window slits on the castle, relative to its base centre (they light one by one)
_CASTLE_WINDOWS = [(-3.2, -26.0), (3.2, -26.0), (0.0, -19.0), (-20.0, -19.0), (20.0, -16.0), (-12.0, -7.0),
                   (12.0, -7.0)]


def _draw_far_bench(cr):
    """Far off on the horizon, right: the garden bench under its lantern post (unlit)."""
    lx, ly = LANTERN
    col = "#1d2547"
    bx = lx - 30.0
    cr.rectangle(bx - 15, ly - 7.5, 30, 2.6)        # seat
    cr.rectangle(bx - 15, ly - 14.5, 30, 2.4)       # back rail
    for x in (bx - 13, bx + 11):                    # ends and legs
        cr.rectangle(x, ly - 15.5, 2.2, 15.5)
    core.src(cr, col)
    cr.fill()
    cr.rectangle(lx - 1.1, ly - 36, 2.2, 36)        # the post
    core.polygon(cr, [(lx - 4.0, ly - 36.5), (lx + 4.0, ly - 36.5), (lx + 2.6, ly - 45.0), (lx - 2.6, ly - 45.0)])
    core.polygon(cr, [(lx - 4.6, ly - 45.0), (lx + 4.6, ly - 45.0), (lx, ly - 49.5)])
    core.src(cr, col)
    cr.fill()
    core.polygon(cr, [(lx - 2.4, ly - 37.5), (lx + 2.4, ly - 37.5), (lx + 1.6, ly - 43.6), (lx - 1.6, ly - 43.6)])
    core.src(cr, "#2c355e")                        # the unlit glass
    cr.fill()


def _draw_cloth(cr):
    """The linen cloth spread on the grass: dim moonlit linen, a few soft creases running back, a
    madder border all round (its gold thread is gilded with the rest), a short fringe in front."""
    bl, br, fr, fl = CLOTH
    fringe = []                                         # the fringe hangs over the grass at the front
    for k in range(64):
        x, y = _cloth_q((k + 0.5) / 64.0, 1.0)
        fringe.append([(x, y - 0.5), (x + 0.6, y + 5.5 + 1.5 * core.hash01(k, 3))])
    B.detail_lines(cr, fringe, 1.6, "#4c4944", 0.9, taper=(1.0, 0.8, 0.4))
    core.polygon(cr, CLOTH)
    cr.set_source(core.linear(0, bl[1], 0, fl[1], [(0.0, "#524e4b"), (0.5, "#5c5751"), (1.0, "#625c54")]))
    cr.fill()
    cr.save()
    core.polygon(cr, CLOTH)
    cr.clip()
    B.detail_line(cr, [_cloth_q(u, 0.0) for u in (0.0, 0.5, 1.0)], 2.0, "#9a9ca2", 0.30, taper=(0.2, 1.0, 0.2))
    for u0, u1, w in ((0.24, 0.19, 1.0), (0.53, 0.52, 1.2), (0.80, 0.85, 1.0)):    # soft creases running back
        ridge = [_cloth_q(u0 + (u1 - u0) * v, v) for v in (0.1, 0.45, 0.8, 1.02)]
        shade = [(x + 4.0 + 3.0 * i, y) for i, (x, y) in enumerate(ridge)]
        B.detail_line(cr, shade, 6.0 * w, "#34333a", 0.22, taper=(0.1, 1.0, 0.5))
        B.detail_line(cr, ridge, 2.0 * w, "#8d8e93", 0.16, taper=(0.1, 1.0, 0.5))
    for poly in (_band_poly("back"), _band_poly("front"), _band_poly("left"), _band_poly("right")):
        core.polygon(cr, poly)
        core.src(cr, "#4a1a24")
        cr.fill()
    cr.restore()
    B.detail_line(cr, [bl, br], 1.3, "#22242c", 0.55, taper=(0.0, 1.0, 0.0))   # its back edge on the grass
    B.detail_line(cr, [fl, fr], 1.6, "#1e1e22", 0.6, taper=(0.0, 1.0, 0.0))    # its front edge


_BAND = (0.075, 0.135, 0.035, 0.062, 0.86, 0.915)   # back v0..v1 | sides u0..u1 | front v0..v1


def _band_poly(which):
    v0, v1, u0, u1, f0, f1 = _BAND
    if which == "back":
        return [_cloth_q(u0, v0), _cloth_q(1 - u0, v0), _cloth_q(1 - u0, v1), _cloth_q(u0, v1)]
    if which == "front":
        return [_cloth_q(u0, f0), _cloth_q(1 - u0, f0), _cloth_q(1 - u0, f1), _cloth_q(u0, f1)]
    if which == "left":
        return [_cloth_q(u0, v0), _cloth_q(u1, v0), _cloth_q(u1, f1), _cloth_q(u0, f1)]
    return [_cloth_q(1 - u1, v0), _cloth_q(1 - u0, v0), _cloth_q(1 - u0, f1), _cloth_q(1 - u1, f1)]


def _thread_lines():
    """The gold thread running along the middle of the madder border."""
    v0, v1, u0, u1, f0, f1 = _BAND
    vm, um, fm = (v0 + v1) / 2.0, (u0 + u1) / 2.0, (f0 + f1) / 2.0
    back = [_cloth_q(um + (1 - 2 * um) * k / 12.0, vm) for k in range(13)]
    front = [_cloth_q(um + (1 - 2 * um) * k / 12.0, fm) for k in range(13)]
    left = [_cloth_q(um, vm + (fm - vm) * k / 8.0) for k in range(9)]
    right = [_cloth_q(1 - um, vm + (fm - vm) * k / 8.0) for k in range(9)]
    return [back, front, left, right]


def _draw_roundel_ground(cr):
    """Inside the roundel (back to front): the ultramarine night, the far hills with the castle and
    the bench + lantern, the night meadow with sparse millefleurs, the linen cloth."""
    cr.save()
    core.circle(cr, RC[0], RC[1], RR + 0.5)
    cr.clip()
    g = core.radial(BREAD_LIGHT[0] - 40, HORIZON + 30, RR * 1.7, [(0.0, NIGHT[0]), (0.42, NIGHT[1]), (1.0, NIGHT[2])])
    cr.set_source(g)
    cr.paint()
    for i in range(9):                                     # soft blooms (the wash dried unevenly)
        bx = RC[0] + (core.hash01(i, 5) - 0.5) * RR * 1.7
        by = RC[1] - RR * 0.2 + (core.hash01(i, 6) - 0.7) * RR * 1.0
        rr = RR * (0.18 + 0.28 * core.hash01(i, 7))
        col = "#5068b0" if core.hash01(i, 8) < 0.55 else "#0a0f26"
        fx.glow(cr, bx, by, rr, col, 0.10, additive=False)
    cr.rectangle(RC[0] - RR, HORIZON - 34, 2 * RR, 34)    # a breath of haze along the horizon
    cr.set_source(core.linear(0, HORIZON - 34, 0, HORIZON, [(0.0, (0.45, 0.52, 0.78, 0.0)), (1.0, (0.45, 0.52, 0.78, 0.16))]))
    cr.fill()
    # the far hills (atmospheric: lighter and bluer than the meadow), a moonlit crest
    hills = [(RC[0] + dx, HORIZON + dy) for dx, dy in _HILLS]
    cr.new_path()
    core.smooth_open(cr, hills, 0.5)
    cr.line_to(RC[0] + 210, HORIZON + 40)
    cr.line_to(RC[0] - 210, HORIZON + 40)
    cr.close_path()
    cr.set_source(core.linear(0, HORIZON - 30, 0, HORIZON + 10, [(0.0, "#2d3b72"), (1.0, "#253262")]))
    cr.fill()
    B.detail_line(cr, hills[1:-1], 1.6, "#5b6cab", 0.35, taper=(0.1, 1.0, 0.1))
    _draw_castle(cr)
    _draw_far_bench(cr)
    # the meadow, tilted up toward a high horizon (darker and greener as it comes near)
    near = [(-210.0, 7.0), (-150.0, 1.0), (-90.0, 4.0), (-30.0, 0.0), (30.0, 3.0), (90.0, -1.0), (150.0, 2.0),
            (210.0, 6.0)]
    cr.new_path()
    core.smooth_open(cr, [(RC[0] + dx, HORIZON + dy) for dx, dy in near], 0.5)
    cr.line_to(RC[0] + 210, RC[1] + RR + 10)
    cr.line_to(RC[0] - 210, RC[1] + RR + 10)
    cr.close_path()
    cr.set_source(core.linear(0, HORIZON, 0, RC[1] + RR, [(0.0, "#2c4a4c"), (0.3, "#1f3a3c"), (1.0, "#0f1d21")]))
    cr.fill()
    cr.save()                                              # the meadow painted in rows, as an illuminator would
    core.circle(cr, RC[0], RC[1], RR)
    cr.clip()
    for k in range(9):
        y = HORIZON + 6.0 + (k ** 1.35) * 4.2
        w = 2.0 + 0.9 * k
        pts = [(RC[0] - RR + i * 40.0, y + 1.6 * math.sin(i * 1.3 + k * 2.1)) for i in range(11)]
        B.detail_line(cr, pts, w, "#3d6460" if k % 2 == 0 else "#122427", 0.22, taper=(0.3, 1.0, 0.3))
    cr.restore()
    # grass: short strokes in rows, lighter near the horizon
    rng = np.random.default_rng(31)
    blades_l, blades_d = [], []
    for _ in range(700):
        x = RC[0] + rng.uniform(-RR, RR)
        y = rng.uniform(HORIZON + 4, RC[1] + RR)
        if math.hypot(x - RC[0], y - RC[1]) > RR or _in_cloth(x, y, 2.0):
            continue
        depth = core.clamp((y - HORIZON) / (RC[1] + RR - HORIZON))
        h = 2.5 + 6.5 * depth
        lean = rng.uniform(-0.35, 0.35)
        tuft = blades_l if rng.uniform() < 0.45 else blades_d
        for b in (-1.0, 0.0, 1.0):                         # a tuft: three blades fanning out
            tuft.append([(x + b * 0.8, y), (x + (lean + 0.35 * b) * h, y - h * (1.0 - 0.18 * abs(b)))])
    B.detail_lines(cr, blades_l, 1.0, "#4b7470", 0.5, taper=(1.0, 0.8, 0.1))
    B.detail_lines(cr, blades_d, 1.0, "#0c171b", 0.55, taper=(1.0, 0.8, 0.1))
    # millefleurs: petals painted (dim in the night); their gold hearts are gilded with the rest
    petal_cols = ("#cfc6a4", "#9a3e4a", "#8a9fd0")
    for (x, y, s, kind) in _flowers():
        B.detail_line(cr, [(x, y + 2.0 * s), (x - 0.6 * s, y + 7.5 * s)], 1.0 * s, "#2c4a3f", 0.8)   # stalk
        cr.new_path()
        for k in range(5):
            a = -math.pi / 2 + k * TAU / 5
            core.circle(cr, x + math.cos(a) * 2.7 * s, y + math.sin(a) * 2.3 * s, 1.9 * s)
        core.src(cr, petal_cols[kind], 0.88)
        cr.fill()
    _draw_cloth(cr)
    sb.paper_grain(cr, RC[0] - RR, RC[1] - RR, 2 * RR, 2 * RR, 0.28, scale=0.6, seed=19)   # painted, not printed
    # the ring's raised gesso shades the painted ground just inside it
    g2 = core.radial(RC[0], RC[1], RR, [(0.0, (0, 0, 0, 0)), (0.86, (0, 0, 0, 0)), (1.0, (0, 0, 0, 0.55))])
    cr.set_source(g2)
    cr.paint()
    cr.restore()


def _draw_tooling(cr):
    """Blind tooling pressed into the vellum round the page: a double rule, each a dark groove with
    a faint lit lip on its lower-right side (no colour: felt more than seen)."""
    x0, y0, x1, y1 = FRAME
    for inset, w in ((0.0, 2.2), (9.0, 1.1)):
        rx, ry, rw, rh = x0 + inset, y0 + inset, x1 - x0 - 2 * inset, y1 - y0 - 2 * inset
        cr.rectangle(rx + 1.0, ry + 1.0, rw, rh)
        cr.set_line_width(w * 0.9)
        core.src(cr, "#4a3d34", 0.55)
        cr.stroke()
        cr.rectangle(rx, ry, rw, rh)
        cr.set_line_width(w)
        core.src(cr, "#100c0a", 0.7)
        cr.stroke()


def _draw_band(cr):
    """The madder band between the gold rings."""
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    _ring_path(cr, RR + RING[0] - 0.5, RR + RING[1] + 0.5)
    core.src(cr, MADDER)
    cr.fill()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)


def _gold_coverage():
    """(M_leaf, M_stars, sparkle sites): burnished leaf (rings, pearls, cusps, vines, corners, the
    frame hairline, the cloth's thread, the flowers' hearts) and the shell-gold stars."""
    stems_l, leaves_l, dots_l = _vine(-1)
    stems_r, leaves_r, dots_r = _vine(+1)
    stems_c, leaves_c, dots_c = _corner_pieces()

    def leaf(c):
        _ornaments_path(c, stems_l + stems_r + stems_c, leaves_l + leaves_r + leaves_c, dots_l + dots_r + dots_c)
        c.fill()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        _ring_path(c, RR, RR + RING[0])
        c.fill()
        _ring_path(c, RR + RING[1], RR + RING[2])
        c.fill()
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
        for (_a, x, y) in _pearls():
            core.circle(c, x, y, 2.3)
        c.fill()
        x0, y0, x1, y1 = FRAME                             # the gold hairline round the page
        g = GOLD_RULE
        c.rectangle(x0 + g, y0 + g, x1 - x0 - 2 * g, y1 - y0 - 2 * g)
        c.set_line_width(1.5)
        c.stroke()
        c.save()                                           # inside the roundel: thread and flower hearts
        core.circle(c, RC[0], RC[1], RR - 1.0)
        c.clip()
        for line in _thread_lines():
            core.tapered(c, line, 1.5, 1.9, cap=False)
        c.fill()
        for (x, y, s, kind) in _flowers():
            core.circle(c, x, y, 1.35 * s)
        c.fill()
        c.restore()
        for (x, y, a) in _cusps():
            for k in (-1, 0, 1):
                aa = a + k * 0.065
                r = RR + RING[2] + (5.5 if k == 0 else 3.0)
                core.circle(c, RC[0] + math.cos(aa) * r, RC[1] + math.sin(aa) * r, 4.2 if k == 0 else 3.2)
            c.fill()
    M_leaf = _a8(leaf)

    def stars(c):
        for (x, y, r, kind) in _stars():
            if kind == 0:
                _star_path(c, x, y, r)
            else:
                core.circle(c, x, y, r)
        c.fill()
    M_st = _a8(stars)
    sites = [(x, y) for (_a, x, y) in _pearls()[::5]] + [(x, y) for (x, y, r) in (dots_l + dots_r) if r > 2.2][::2]
    sites += [(x, y) for (x, y, r, kind) in _stars() if kind == 0][::4]
    sites += [(x, y) for (x, y, s, k) in _flowers()][::4]
    return M_leaf, M_st, sites


def _quote_layer():
    """The quote (cream italic) in one cached surface."""
    s = core.new_surface(W, H)
    c = core.new_context(s)
    _font_opts(c)
    for ln, yb in zip(QUOTE, QUOTE_BASES):
        core.text_path(c, ln, CX, yb, QUOTE_SIZE, QUOTE_FONT, align="center", italic=True)
        core.src(c, "#ebe0c7")
        c.fill_preserve()
        c.set_line_width(0.55)                  # a hair of extra weight so the italic survives H.264
        c.stroke()
    s.flush()
    return s


def _attrib_mask():
    def draw(c):
        core.text_path(c, ATTRIB, CX, ATTRIB_BASE, ATTRIB_SIZE, TITLE_FONT, align="center", spacing=3.0)
        c.fill()
    return _a8(draw)


def setup():
    st = {}
    crink, refl = _leaf_textures()
    page = _surface(_vellum())
    c = core.new_context(page)
    _draw_tooling(c)
    _draw_band(c)
    _draw_roundel_ground(c)
    M_leaf, M_st, sites = _gold_coverage()
    Mt, tdim, tlit = _title_layers(crink)
    gold_dim = _gild(M_leaf, crink, refl, False)
    gold_lit = _gild(M_leaf, crink, refl, True)
    st_dim = _mix(_rgb("#5c4520"), _rgb("#8c6a2e"), np.clip(refl + 0.5, 0, 1))
    st_lit = _mix(_rgb("#d9a94c"), _rgb("#ffe9a6"), np.clip(refl + 0.5, 0, 1))
    A_st = M_st * 0.55
    for rgb, a in ((st_dim, A_st), (gold_dim, M_leaf), (tdim, Mt)):
        _crop_img(rgb, a, _bbox(a)).paint(c)
    page.flush()
    st["page"] = _Img(page)
    # the lit gold: one layer (leaf + stars + title), revealed through the light field
    M_st_lit = M_st * 0.75
    A_all = np.clip(M_leaf + M_st_lit + Mt, 0.0, 1.0)
    lit_rgb = (gold_lit * M_leaf[..., None] + st_lit * M_st_lit[..., None] + tlit * Mt[..., None])
    lit_rgb = lit_rgb / np.maximum(A_all, 1e-4)[..., None]
    st["lit"] = _crop_img(lit_rgb, A_all, _bbox(A_all))
    # quote + attribution
    st["quote"] = _Img(_quote_layer())
    Ma = _attrib_mask()
    ab = _bbox(Ma)
    st["attr_dim"] = _crop_img(_gild_text(Ma, False), Ma, ab)
    st["attr_lit"] = _crop_img(_gild_text(Ma, True), Ma, ab)
    # sparkle sites on the gold, with their distance from the gap (for the ring of light)
    st["sites"] = [(x, y, math.hypot(x - BREAD_LIGHT[0], y - BREAD_LIGHT[1]), core.hash01(i, 33))
                   for i, (x, y) in enumerate(sites)]
    st["light"] = fx.LightLayer()
    st["lf"] = cairo.ImageSurface(cairo.FORMAT_A8, W // 4, H // 4)
    return st


# ----------------------------------------------------------------------------------------
# per-frame light: the field that reveals the lit gold
# ----------------------------------------------------------------------------------------


def _flicker(t):
    return 0.5 + 0.5 * (0.6 * core.noise1(t * 2.3, 41) + 0.4 * core.noise1(t * 7.1, 42))


def _glint_band(c, gx, gy, width, amt, clip):
    """A slanted soft band of candle glint centred at x = gx (tilted 20 degrees)."""
    if amt <= 0.01:
        return
    c.save()
    c.rectangle(*clip)
    c.clip()
    sl = math.tan(math.radians(20.0))
    g = cairo.LinearGradient(gx - width, gy - width * sl, gx + width, gy + width * sl)
    g.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(0.38, 0, 0, 0, amt * 0.35)
    g.add_color_stop_rgba(0.5, 0, 0, 0, amt)
    g.add_color_stop_rgba(0.62, 0, 0, 0, amt * 0.35)
    g.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
    c.set_source(g)
    c.paint()
    c.restore()


def _glint_x(t, t0, t1):
    u = core.inout_sine(core.clamp((t - t0) / (t1 - t0)))
    return CX - TITLE_W * 0.62 + u * TITLE_W * 1.24, u


def _pluck_pos(i):
    a = -math.pi / 2 + 0.9 + i * 2.4
    rm = RR + (RING[0] + RING[1]) / 2.0
    return RC[0] + math.cos(a) * rm, RC[1] + math.sin(a) * rm


@functools.lru_cache(maxsize=1)
def _twinkle_stars():
    """A handful of stars that twinkle in the hold: [(x, y, phase, rate)]."""
    big = [(x, y) for (x, y, r, k) in _stars() if k == 0]
    out = []
    for i in range(0, len(big), max(1, len(big) // 6)):
        x, y = big[i]
        out.append((x, y, core.hash01(i, 51) * TAU, 0.9 + 0.8 * core.hash01(i, 52)))
    return out


def _light_field(st, t):
    """Quarter-res A8 mask: how lit each part of the gold is at time t."""
    lf = st["lf"]
    c = cairo.Context(lf)
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.paint()
    c.set_operator(cairo.OPERATOR_ADD)
    c.scale(0.25, 0.25)
    # 1. the candle (high on the left): a faint flicker that never goes away
    fl = _flicker(t)
    g = cairo.RadialGradient(CX - 520, 120, 0, CX - 520, 120, 1500)
    g.add_color_stop_rgba(0.0, 0, 0, 0, 0.08 + 0.07 * fl)
    g.add_color_stop_rgba(1.0, 0, 0, 0, 0.01 + 0.02 * fl)
    c.set_source(g)
    c.rectangle(0, 0, W, QUOTE_BASES[0] - 60)
    c.fill()
    # 2. the candle glint walking across the title (once, after the fade-in)
    if T_GLINT0 < t < T_GLINT1:
        gx, u = _glint_x(t, T_GLINT0, T_GLINT1)
        _glint_band(c, gx, TITLE_BASE - 22, 130.0, math.sin(math.pi * u) ** 0.5, (0, TITLE_BASE - 80, W, 110))
    # 2b. in the hold, the candle's glint drifts once along the vines, left to right (gentle)
    if T_VGLINT0 < t < T_VGLINT1:
        u = core.inout_sine((t - T_VGLINT0) / (T_VGLINT1 - T_VGLINT0))
        gx = CX - TITLE_W * 0.66 + u * TITLE_W * 1.32
        _glint_band(c, gx, RC[1], 170.0, 0.5 * math.sin(math.pi * u) ** 0.7, (0, RC[1] - 120, W, 240))
    # 3. lute bass notes before the break pluck a glint from a pearl of the rim
    for i, tb in enumerate(PLUCKS):
        dt = t - tb
        if 0.0 <= dt < 0.9:
            px, py = _pluck_pos(i)
            k = math.exp(-dt * 4.0) * min(1.0, dt * 30.0)
            gg = cairo.RadialGradient(px, py, 0, px, py, 60)
            gg.add_color_stop_rgba(0.0, 0, 0, 0, 0.85 * k)
            gg.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
            c.set_source(gg)
            c.arc(px, py, 60, 0, TAU)
            c.fill()
    # 3b. a few stars twinkle in the hold (quietly; they stop once the bread's light has them)
    fade_tw = 1.0 - core.smoothstep(T_BREAK, T_BREAK + 1.6, t)
    if fade_tw > 0.0:
        for (x, y, ph, rate) in _twinkle_stars():
            k = max(0.0, math.sin(t * rate + ph)) ** 6 * 0.55 * fade_tw
            if k > 0.02:
                gg = cairo.RadialGradient(x, y, 0, x, y, 12)
                gg.add_color_stop_rgba(0.0, 0, 0, 0, k)
                gg.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
                c.set_source(gg)
                c.arc(x, y, 12, 0, TAU)
                c.fill()
    # 4. the bread: a warm core before the break; after it, a ring travels out, lit behind it
    fr = _front(t)
    bx, by = BREAD_LIGHT
    if fr is None:
        pre = 0.16 + 0.05 * math.sin(t * 1.7)
        k = 1.0 + 0.8 * core.smoothstep(T_WHAT, T_BREAK, t)
        gg = cairo.RadialGradient(bx, by, 0, bx, by, 150)
        gg.add_color_stop_rgba(0.0, 0, 0, 0, pre * k)
        gg.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
        c.set_source(gg)
        c.arc(bx, by, 150, 0, TAU)
        c.fill()
    else:
        R = max(fr, 1.0)
        w = 130.0
        gg = cairo.RadialGradient(bx, by, 0, bx, by, R + w)
        n = 18
        for i in range(n + 1):
            r = (R + w) * i / n
            steady = 0.80 * math.exp(-r / 420.0) + 0.24
            z = (r - R) / w
            ring = math.exp(-z * z * 3.0) * 0.6 * (1.0 - 0.45 * R / FRONT_MAX)
            inside = core.clamp((R - r) / (0.6 * w) + 0.5)             # 1 behind the front, 0 beyond
            gg.add_color_stop_rgba(i / n, 0, 0, 0, core.clamp(steady * inside + ring))
        c.set_source(gg)
        c.arc(bx, by, R + w, 0, TAU)
        c.fill()
        flash = math.exp(-max(0.0, t - T_BREAK) * 3.0)
        if flash > 0.02:
            g3 = cairo.RadialGradient(bx, by, 0, bx, by, 240)
            g3.add_color_stop_rgba(0.0, 0, 0, 0, 0.8 * flash)
            g3.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
            c.set_source(g3)
            c.arc(bx, by, 240, 0, TAU)
            c.fill()
    # 5. the final chord: a soft swell over all the gold + a last glint across the title
    if t > T_FINAL:
        u = core.clamp((t - T_FINAL) / 1.8)
        sw = math.sin(math.pi * min(1.0, u)) * 0.22
        c.set_source_rgba(0, 0, 0, max(0.0, sw))
        c.rectangle(0, 0, W, H)
        c.fill()
        gx, v = _glint_x(t, T_LAST0, T_LAST1)
        if 0.0 < v < 1.0:
            _glint_band(c, gx, TITLE_BASE - 22, 150.0, 0.85 * math.sin(math.pi * v), (0, TITLE_BASE - 80, W, 110))
    lf.flush()
    pat = cairo.SurfacePattern(lf)
    m = cairo.Matrix()
    m.scale(0.25, 0.25)
    pat.set_matrix(m)
    pat.set_filter(cairo.FILTER_BILINEAR)
    return pat


def _lit_at(x, y, t, soft=160.0):
    """0..1 how much the bread's light has reached (x, y)."""
    fr = _front(t)
    if fr is None:
        return 0.0
    d = math.hypot(x - BREAD_LIGHT[0], y - BREAD_LIGHT[1])
    return core.smoothstep(d - 40.0, d + soft, fr)


# ----------------------------------------------------------------------------------------
# the miniature: lights in the night, the rune-stone, the loaf
# ----------------------------------------------------------------------------------------

L_COLD = B.Light(key=(0.86, 0.90, 1.0), ambient=(0.34, 0.37, 0.48), rim=(0.62, 0.78, 0.9), rim_strength=0.22,
                 direction=(-0.55, -0.83), rim_direction=(-0.9, -0.4), name="s9_cold")
L_WARM_STONE = B.Light(key=(1.16, 0.90, 0.64), ambient=(0.44, 0.36, 0.40), rim=(1.0, 0.76, 0.42), rim_strength=0.95,
                       direction=(0.95, -0.3), rim_direction=(0.98, -0.2), name="s9_warm_stone")
L_BREAD = B.Light(key=(1.08, 0.92, 0.74), ambient=(0.48, 0.40, 0.46), rim=(1.0, 0.82, 0.52), rim_strength=0.6,
                  direction=(-0.5, -0.86), rim_direction=(0.7, -0.7), name="s9_bread")

# the rune-stone: a domed field stone the size and shape of the loaf, but hard -- a few flat
# chiselled planes and corners where the loaf is all soft curve. Anchor: the middle of its base.
STONE_PTS = [(-57, -3), (-60, -15), (-58, -29), (-52, -41), (-41, -54), (-27, -61), (-17, -66), (1, -69), (20, -66),
             (33, -60), (44, -50), (51, -42), (57, -30), (60, -16), (57, -3), (41, 2), (14, 4), (-16, 4), (-42, 2)]
STONE_TOP_PLANE = [(-45, -46), (-33, -58), (-14, -66), (8, -67), (27, -60), (19, -52), (-2, -55), (-24, -50)]
STONE_SIDE_PLANE = [(31, -57), (48, -45), (56, -31), (59, -16), (52, -17), (43, -30), (31, -45)]
_GLYPHS = ([[(0.5, 0), (0.5, 1)], [(0.5, 0.2), (0.95, 0.0)], [(0.5, 0.45), (0.95, 0.25)]],     # fehu
           [[(0.5, 0), (0.5, 1)], [(0.5, 0.45), (0.1, 0.1)], [(0.5, 0.45), (0.9, 0.1)]],       # algiz
           [[(0.1, 0), (0.9, 1)], [(0.9, 0), (0.1, 1)]],                                       # gebo
           [[(0.3, 0), (0.3, 1)], [(0.3, 0.1), (0.85, 0.45)], [(0.85, 0.45), (0.3, 0.75)]])    # thurisaz


def _q(u, n=24):
    """Quantize a blend amount so the palette cache stays small."""
    return round(core.clamp(u) * n) / n


@functools.lru_cache(maxsize=1)
def _stone_marks():
    cx, cy = -1.0, -30.0
    spiral = [(cx + math.cos(a) * 15.0 * (0.12 + 0.88 * a / (2.6 * math.pi)),
               cy + math.sin(a) * 12.5 * (0.12 + 0.88 * a / (2.6 * math.pi)))
              for a in [k * 2.6 * math.pi / 30 for k in range(31)]]
    runes = []
    for k, a0 in enumerate((-2.72, -2.36, -2.0, -1.14, -0.78, -0.42)):
        rx, ry = cx + math.cos(a0) * 38.0, cy + 2.0 + math.sin(a0) * 24.0
        ang = a0 + math.pi / 2
        h = 7.0
        ca, sa = math.cos(ang), math.sin(ang)
        for (u0, v0), (u1, v1) in _GLYPHS[k % len(_GLYPHS)]:
            seg = []
            for (u, v) in ((u0, v0), (u1, v1)):
                px, py = (u - 0.5) * h * 0.6, (v - 0.5) * h
                seg.append((rx + px * ca - py * sa, ry + px * sa + py * ca))
            runes.append(seg)
    return spiral, runes


@functools.lru_cache(maxsize=1)
def _stone_texture():
    """(dark pits, pale specks) as small surfaces in the stone's local space (x -66..66, y -78..10):
    the granular, matte grain that says slate and not dough."""
    w, h = 132, 88
    n1 = core.noise_array(w, h, scale=2.2, octaves=2, seed=81)
    n2 = core.noise_array(w, h, scale=13.0, octaves=3, seed=82)
    n3 = core.noise_array(w, h, scale=5.0, octaves=2, seed=83)
    dark = np.clip((-n1 - 0.38) * 2.6, 0.0, 1.0) * 0.55 + np.clip(-n2 - 0.1, 0.0, 1.0) * 0.30
    pale = np.clip((n1 - 0.48) * 2.6, 0.0, 1.0) * 0.45 + np.clip(n3 - 0.35, 0.0, 1.0) * 0.25
    zero = np.zeros((h, w, 3), np.float32)
    return _surface(zero + 0.05, dark), _surface(zero + 0.92, pale)


def _stone_level(t):
    """(cold rune glow 0..1, warmth reached 0..1): a slow breath, out of phase with the loaf. When
    the warm light washes over the stone its runes gutter (a little dying flicker) and go dark over
    ~1.2 s; the warm light on it follows the front."""
    breath = 0.62 + 0.18 * math.sin(t * 1.15 + 1.9)
    warm = _lit_at(STONE_X + 20, STONE_BASE - 36, t, soft=110.0)
    if warm <= 0.0:
        return breath, 0.0
    t_hit = T_BREAK + _t_of_radius(math.hypot(STONE_X + 20 - BREAD_LIGHT[0], STONE_BASE - 36 - BREAD_LIGHT[1]))
    u = core.clamp((t - t_hit) / 1.2)
    gutter = 1.0 - 0.55 * (0.5 + 0.5 * core.noise1(t * 21.0, 61)) * math.sin(math.pi * u)
    return breath * (1.0 - core.smoothstep(0.0, 1.0, u)) * gutter, warm


def _draw_stone(cr, t):
    lvl, warm = _stone_level(t)
    light = B.Light.lerp(L_COLD, L_WARM_STONE, _q(warm))
    # its shadow, thrown away from the bread once the light is on it
    if warm > 0.01:
        cr.save()
        cr.translate(STONE_X - 46.0 * warm, STONE_BASE + 1.5)
        cr.scale(1.0, 0.12)
        fx.glow(cr, 0, 0, 78.0 + 24.0 * warm, "#0b0d14", 0.55 * warm, additive=False)
        cr.restore()
    B.contact_shadow(cr, STONE_X + 2, STONE_BASE + 1, 58, 7.5, alpha=0.62, color="#0c0a0e")
    cr.save()
    cr.translate(STONE_X, STONE_BASE)
    lw = B.line_for(B.LINE, B.device_scale(cr))             # the house line
    sh, so = B.smooth_paths(cr, STONE_PTS, lw, 0.62)        # low tension: a harder, chiselled contour
    p = B.shade(cr, sh, MATS["stone"], light, lw, outline=so, size=46.0, rim=1.0)
    cr.save()
    sh.add(cr)
    cr.clip()
    core.polygon(cr, STONE_TOP_PLANE)                       # the planes it was split along
    core.src(cr, p.hi, 0.34 - 0.12 * warm)
    cr.fill()
    core.polygon(cr, STONE_SIDE_PLANE)
    core.src(cr, core.mix(p.shadow, p.line, 0.45), 0.55 - 0.3 * warm)
    cr.fill()
    B.detail_lines(cr, [[(-45, -46), (-24, -50), (-2, -55), (19, -52), (31, -57)], [(31, -45), (43, -30), (52, -17)]],
                   1.1, p.line, 0.45, taper=(0.3, 1.0, 0.3))                    # the arrises between the planes
    B.detail_lines(cr, [[(-44, -47), (-23, -51), (-2, -56), (18, -53)]], 1.0, p.hi, 0.35, taper=(0.3, 1.0, 0.3))
    tex_d, tex_p = _stone_texture()                          # the grain of the stone
    cr.set_source_surface(tex_d, -66, -78)
    cr.paint_with_alpha(0.75)
    cr.set_source_surface(tex_p, -66, -78)
    cr.paint_with_alpha(0.32 + 0.1 * warm)
    core.src(cr, p.hi, 0.30)                                 # pale and dark flecks: slate, not dough
    for i in range(16):
        core.circle(cr, (core.hash01(i, 3) - 0.5) * 100, -60 + core.hash01(i, 4) * 56, 0.5 + 0.8 * core.hash01(i, 5))
    cr.fill()
    core.src(cr, p.line, 0.30)
    for i in range(12):
        core.circle(cr, (core.hash01(i, 6) - 0.5) * 100, -58 + core.hash01(i, 7) * 54, 0.5 + 0.7 * core.hash01(i, 8))
    cr.fill()
    core.polygon(cr, [(-60, -14), (-50, -11), (-56, -4)])   # a chip off its foot, a hairline crack
    core.src(cr, p.line, 0.55)
    cr.fill()
    B.detail_lines(cr, [[(22, -64), (27, -55), (25, -47)]], 0.9, p.line, 0.45)
    cr.restore()
    groove = core.mix(p.shadow, p.line, 0.55)
    glowc = core.mix(groove, RUNE, 0.12 + 0.88 * lvl)
    spiral, runes = _stone_marks()
    B.detail_lines(cr, [spiral], 3.0, groove, 0.9, taper=(0.4, 1.0, 0.8))
    B.detail_lines(cr, runes, 1.8, groove, 0.8, taper=(0.8, 1.0, 0.8))
    if lvl > 0.01:
        B.detail_lines(cr, [spiral], 1.5, glowc, 0.3 + 0.7 * lvl, taper=(0.4, 1.0, 0.8))
        B.detail_lines(cr, runes, 1.0, glowc, 0.25 + 0.75 * lvl, taper=(0.8, 1.0, 0.8))
        fx.glow(cr, -1.0, -30.0, 30.0, RUNE, 0.42 * lvl)
    B.sheen(cr, -22, -52, 12, 3.0, angle=-0.4, alpha=0.08 * (1.0 - 0.6 * warm))
    cr.restore()
    if lvl > 0.01:                                           # its cold light on the cloth about it
        fx.light_pool(cr, STONE_X, STONE_BASE + 2, 74, 12, RUNE, 0.12 * lvl)
    return lvl, warm


# --- the loaf ------------------------------------------------------------------------------


def _loaf_pts(r, n=41):
    """The boule's silhouette (props' loaf, on-model): a high dome, a flatter base. Centre (0, 0)."""
    pts = []
    for i in range(n):
        a = math.pi + math.pi * i / (n - 1)
        pts.append((math.cos(a) * r, math.sin(a) * r * 0.8 + r * 0.12))
    pts += [(r * 0.97, r * 0.3), (r * 0.72, r * 0.5), (0.0, r * 0.56), (-r * 0.72, r * 0.5), (-r * 0.97, r * 0.3)]
    return pts


def _half_pts(r, s):
    """A torn half turned toward us by phi (s = sin phi), authored as the LEFT half with its torn face
    toward +x: the crust's silhouette on the left, the torn face's edge (squeezed by s) on the right."""
    s = max(s, 0.03)
    return [(px if px <= 0.0 else px * s, py) for (px, py) in _loaf_pts(r)]


def _section_pts(r, s, k=1.0, seed=0, rag=0.0):
    """The torn face: the loaf's cross-section squeezed to width by s, scaled by k about its centre,
    its dome edge pulled into ragged tufts (rag)."""
    cy = -0.06 * r
    out = []
    for i, (px, py) in enumerate(_loaf_pts(r)):
        kk = k
        if rag > 0.0 and py < 0.28 * r:
            kk *= 1.0 + rag * (0.55 * math.sin(i * 2.9 + seed * 1.7) + (0.9 if (i + seed) % 4 == 0 else -0.2))
        out.append((px * kk * s, cy + (py - cy) * kk))
    return out


def _loaf_state(t):
    """The loaf's performance at t: open (0 whole .. 1 broken, overshoots a little), the pre-break
    swell/squash/tremble, the crack of light, the flash and the strands of crumb."""
    s = dict(open=0.0, sx=1.0, sy=1.0, dx=0.0, crack=0.0, flash=0.0, strands=0.0, dt=-1.0)
    if t < T_WHAT:
        return s
    if t < T_BREAK:
        u = (t - T_WHAT) / (T_BREAK - T_WHAT)
        swell = 0.016 * core.smoothstep(0.0, 0.5, u) * (1.0 - core.smoothstep(0.55, 0.85, u))
        squash = 0.032 * core.smoothstep(0.55, 0.9, u)        # "to": pressed, about to give
        s["sx"] = 1.0 + swell + 0.55 * squash
        s["sy"] = 1.0 + swell - squash
        s["dx"] = math.sin((t - T_WHAT) * 47.0) * 0.8 * core.smoothstep(0.1, 0.6, u) * (1.0 - core.smoothstep(0.85, 1.0, u))
        s["crack"] = core.smoothstep(0.0, 0.95, u)
        return s
    dt = t - T_BREAK
    s["dt"] = dt
    s["open"] = 1.0 - math.exp(-dt * 7.0) * math.cos(dt * 5.0)    # a snap, a small overshoot, a settle
    s["crack"] = 1.0
    s["flash"] = math.exp(-dt * 4.5)
    s["strands"] = 1.0 - core.smoothstep(0.06, 0.26, dt)
    return s


def _half_geom(o):
    """(phi, sin phi, separation of each half's pivot, outward lean) for an opening o."""
    phi = PHI_MAX * o
    sp = math.sin(phi)
    sep = 0.72 * LOAF_R * sp + 2.0 * min(o, 1.0)       # the crumb's flat foot: the halves' feet nearly touch
    tilt = TILT_MAX * o                                # ...and they lean apart, so the gap of light is a V
    return phi, sp, sep, tilt


def _crust_art(cr, r, p, light, ears, inner_glow, seed=3):
    """Crust details over a shaded crust shape (caller clips): the darker bake underneath, the three
    scored ears (glowing faintly from within before the break), flour and blisters."""
    core.ellipse(cr, 0.0, r * 0.62, r * 1.2, r * 0.32)
    core.src(cr, B.palette(light, B.Mat.of(P.PROP_COLORS["crust_dk"])).lit, 0.5)
    cr.fill()
    hi = B.palette(light, MATS["crust_hi"])
    cr.new_path()
    for k in ears:
        x0 = k * r * 0.42
        dy = abs(k) * r * 0.11
        core.tapered(cr, [(x0 - r * 0.22, -r * 0.40 + dy), (x0, -r * 0.60 + dy), (x0 + r * 0.22, -r * 0.42 + dy)],
                     r * 0.14, r * 0.14, profile=lambda u: r * 0.15 * math.sin(math.pi * u) + 0.4)
    sc = B.Path(cr)
    sc.add(cr, 0.0, r * 0.05)
    core.src(cr, p.line, 0.7)
    cr.fill()
    sc.add(cr)
    core.src(cr, hi.lit)
    cr.fill()
    if inner_glow > 0.01:                                  # the scoring glows: it is warm inside
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        sc.add(cr)
        core.src(cr, "#ff7a30", 0.12 * inner_glow)
        cr.fill()
        cr.restore()
    core.src(cr, "#f7efdc", 0.55)                          # flour
    for i in range(14):
        core.circle(cr, (core.hash01(i, seed + 77) - 0.5) * r * 1.6, -r * 0.62 + core.hash01(i, seed + 78) * r * 0.42,
                    r * 0.025 + 0.4)
    cr.fill()
    core.src(cr, p.line, 0.35)                             # blisters
    for i in range(7):
        core.circle(cr, (core.hash01(i, seed + 79) - 0.5) * r * 1.5, -r * 0.1 + core.hash01(i, seed + 80) * r * 0.45,
                    r * 0.022 + 0.3)
    cr.fill()


def _draw_whole_loaf(cr, r, light, lw, inner_glow, crack):
    sh, so = B.smooth_paths(cr, _loaf_pts(r), lw, 0.85)
    p = B.shade(cr, sh, MATS["crust"], light, lw, outline=so, size=r * 1.4)
    cr.save()
    sh.add(cr)
    cr.clip()
    _crust_art(cr, r, p, light, (-1, 0, 1), inner_glow)
    cr.restore()
    B.sheen(cr, -r * 0.35, -r * 0.5, r * 0.3, r * 0.13, angle=-0.4, alpha=0.3)
    if crack > 0.01:                                      # a hairline of light down the middle score
        n = 7
        pts = [(1.2 * math.sin(i * 2.4 + 0.5) * (i > 0), -r * 0.66 + (r * 1.05) * i / (n - 1)) for i in range(n)]
        m = max(2, int(round(2 + (n - 2) * core.smoothstep(0.0, 0.7, crack))))
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        B.detail_line(cr, pts[:m], 1.0 + 2.4 * crack, WARM, 0.75 * crack, taper=(0.4, 1.0, 0.2))
        B.detail_line(cr, pts[:m], 0.5 + 1.1 * crack, WARM_HOT, 0.95 * crack, taper=(0.4, 1.0, 0.2))
        cr.restore()
        fx.glow(cr, 0.0, -r * 0.35, r * (0.3 + 0.35 * crack), WARM, 0.35 * crack)


def _draw_half(cr, r, sp, light_crust, light_face, lw, seed, heat):
    """One torn half, authored as the LEFT half (torn face toward +x): one silhouette with one ink
    line -- a crescent of crust on the outside, the torn crumb filling the rest, a thin crust shell
    round the crumb -- so it reads as half a loaf, not as two things."""
    outline = _half_pts(r, sp)
    sh, so = B.smooth_paths(cr, outline, lw, 0.85)
    p = B.shade(cr, sh, MATS["crust"], light_crust, lw, outline=so, size=r * 1.1)
    cr.save()
    sh.add(cr)
    cr.clip()
    cr.save()                                               # the crust's details, squeezed into the crescent
    cr.translate(-r * sp, 0.0)
    cr.scale(1.0 - sp, 1.0)
    cr.rectangle(-2.0 * r, -2.0 * r, 2.0 * r, 4.0 * r)
    cr.clip()
    _crust_art(cr, r, p, light_crust, (-1, 0), 0.0, seed=3)
    cr.restore()
    # the crust shell round the torn face (seen where the crumb stops)
    core.smooth_closed(cr, _section_pts(r, sp, 1.0), 0.8)
    core.src(cr, B.palette(light_crust, B.Mat.of(P.PROP_COLORS["crust_dk"])).lit)
    cr.fill()
    cr.restore()
    # the torn crumb: ragged, lit hot from the gap (local +x), its airy holes
    face = _section_pts(r, sp, 0.9, seed, rag=0.075)
    fs, _fo = B.smooth_paths(cr, face, lw * 0.7, 0.72)
    pc = B.shade(cr, fs, MATS["crumb"], light_face, lw, outline=False, size=r * sp * 1.1)
    xs = [x for x, _ in face]
    ys = [y for _, y in face]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cr.save()
    fs.add(cr)
    cr.clip()
    if heat > 0.01:
        cr.set_operator(cairo.OPERATOR_ADD)
        g = core.linear(x1 + 2.0, 0, x0, 0, [(0.0, (1.0, 0.80, 0.50, 0.42 * heat)), (0.3, (1.0, 0.66, 0.34, 0.14 * heat)),
                                            (1.0, (1.0, 0.6, 0.3, 0.0))])
        cr.set_source(g)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
    w_, h_ = x1 - x0, y1 - y0
    pits = []
    for i in range(11):
        hx = x0 + w_ * (0.12 + 0.76 * core.hash01(i, seed + 41))
        hy = y0 + h_ * (0.14 + 0.72 * core.hash01(i, seed + 42))
        hr = (0.6 + 1.0 * core.hash01(i, seed + 43)) * r * 0.045
        pits.append((hx, hy, hr * (0.55 + 0.6 * sp), hr * 0.85, (core.hash01(i, seed + 44) - 0.5) * 0.8))
    cr.new_path()
    for hx, hy, a_, b_, ang in pits:
        core.ellipse(cr, hx, hy, a_, b_, ang)
    core.src(cr, core.mix(pc.shadow, pc.line, 0.3), 0.8)
    cr.fill()
    for hx, hy, a_, b_, ang in pits:                        # the lit lower lip of each pit
        core.ellipse(cr, hx + a_ * 0.15, hy + b_ * 0.45, a_ * 0.75, b_ * 0.4, ang)
    core.src(cr, pc.hi, 0.75)
    cr.fill()
    cr.restore()
    # torn fibres along the crumb's top edge
    B.detail_lines(cr, [[(face[i][0], face[i][1]), (face[i][0] * 1.04 + 1.0, face[i][1] - 2.2)]
                        for i in range(8, 34, 5)], 1.0, pc.hi, 0.7)


def _draw_loaf(cr, t, burst, breath):
    """The loaf: whole and breathing; holding its breath with a crack of light; broken open."""
    s = _loaf_state(t)
    r = LOAF_R
    o = s["open"]
    lw = B.line_for(B.LINE, B.device_scale(cr))
    inner = 0.45 + 0.3 * breath + 0.5 * s["crack"]
    if o <= 0.0:
        B.contact_shadow(cr, LOAF_X + 2, LOAF_BASE + 1, r * 0.98, r * 0.13, alpha=0.62, color="#0c0a0e")
        fx.glow(cr, LOAF_X, LOAF_Y - r * 0.05, r * 1.25, "#ff9a45", 0.10 + 0.05 * breath + 0.12 * s["crack"])
        cr.save()
        cr.translate(LOAF_X + s["dx"], LOAF_BASE)
        cr.scale(s["sx"], s["sy"])
        cr.translate(0.0, LOAF_Y - LOAF_BASE)
        _draw_whole_loaf(cr, r, L_BREAD, lw, inner, s["crack"])
        cr.restore()
        return 0.0
    phi, sp, sep, tilt = _half_geom(o)
    pulse = 0.5 + 0.5 * math.sin(t * 1.9 + 0.6)                     # the light inside breathes
    heat = min(1.0, 0.72 + 0.25 * burst + 0.3 * s["flash"] + 0.06 * pulse)
    # the light inside, BEHIND the halves: it fills the gap and haloes their torn edges
    gx, gy = LOAF_X, LOAF_Y - r * 0.05
    fx.glow(cr, gx, gy - r * 0.2, r * (0.9 + 0.4 * burst + 0.06 * pulse), WARM, 0.42 + 0.3 * s["flash"] + 0.06 * pulse)
    cr.save()                                     # the V of light standing in the gap
    cr.translate(gx, LOAF_BASE)
    vh = r * 1.45 * min(o, 1.0)
    vw = math.tan(tilt) * vh + 3.0
    core.polygon(cr, [(-2.5, 0.0), (2.5, 0.0), (vw, -vh), (-vw, -vh)])
    cr.set_source(core.linear(0, 0, 0, -vh, [(0.0, (1.0, 0.98, 0.9, 0.95)), (0.55, (1.0, 0.86, 0.55, 0.8)),
                                             (1.0, (1.0, 0.75, 0.4, 0.0))]))
    cr.fill()
    cr.restore()
    for side in (-1, 1):
        B.contact_shadow(cr, LOAF_X + side * (sep + r * 0.3), LOAF_BASE + 1, r * 0.66, r * 0.12, alpha=0.6,
                         color="#0c0a0e")
    for side in (-1, 1):
        lc = L_BREAD.with_(rim=(1.0, 0.86, 0.58), rim_strength=1.0, rim_direction=(-side, -0.25))
        lf = B.Light(key=(1.0, 0.86, 0.66), ambient=(0.64, 0.47, 0.37), rim=(1.0, 0.92, 0.72), rim_strength=0.8,
                     direction=(-side * 0.95, -0.3), rim_direction=(-side, -0.1), name="s9_crumb")
        cr.save()
        cr.translate(LOAF_X + side * sep, LOAF_BASE)
        cr.rotate(side * tilt)                     # each half leans out about its inner foot
        if side > 0:
            cr.scale(-1.0, 1.0)                    # the right half is the left one, mirrored
        cr.translate(0.0, LOAF_Y - LOAF_BASE)
        _draw_half(cr, r, sp, lc, lf, lw, 7 if side < 0 else 12, heat)
        cr.restore()
    # strands of crumb stretched across the gap, snapping one by one
    if s["strands"] > 0.01:
        lines = []
        for i, yy in enumerate((-0.38, -0.16, 0.06, 0.26)):
            k = core.clamp(s["strands"] * 1.4 - 0.1 * i)
            if k <= 0.02:
                continue
            y = LOAF_Y + yy * r
            d = math.sqrt(max(0.0, 1.0 - ((yy * r - 0.12 * r) / (0.8 * r)) ** 2)) * r * sp
            xa, xb = LOAF_X - sep + d * 0.9, LOAF_X + sep - d * 0.9
            lines.append(([(xa, y), ((xa + xb) / 2, y + 2.0 * k), (xb, y)], k))
        for pts, k in lines:
            B.detail_line(cr, pts, 1.0 + 3.0 * k, P.PROP_COLORS["crumb"], 0.9 * k, taper=(1.0, 0.35, 1.0))
    # the slit of light in the gap and the soft rays it throws up
    cr.save()                                     # the white-hot slit where the crumb parted
    cr.translate(gx, LOAF_BASE - r * 0.45)
    cr.scale(1.0, 3.2)
    fx.glow(cr, 0, 0, 7.0 + 4.0 * burst, "#ffffff", 0.85)
    cr.restore()
    fx.god_rays(cr, gx, gy + r * 0.1, -math.pi / 2, 1.5, 175.0 + 50.0 * min(o, 1.0), WARM, t, n=7, width=(4.0, 34.0),
                alpha=0.13 * min(o, 1.0) * (0.6 + 0.4 * burst), seed=5, shimmer=0.45)
    if s["flash"] > 0.02:
        fx.glow(cr, gx, gy, r * 1.5, WARM_HOT, 0.65 * s["flash"])
    return sep


def _draw_crumbs_steam(cr, t, sep):
    r = LOAF_R
    k = 0                               # a fresh loaf: now and then a thread of warmth off its top
    t0 = T_FADE_IN1 - 0.5               # (the last threads finish rising after the break)
    while t0 < min(t, T_BREAK) and k < 12:
        fx.smoke(cr, t, t0, LOAF_X - 6 + 10 * core.hash01(k, 9), LOAF_Y - r * 0.66, n=3, dur=3.2, rise=70.0,
                 drift=(6.0, 0.0), size=4.0, color="#fff1da", alpha=0.07, seed=40 + k)
        k += 1
        t0 += 1.9
    if t < T_BREAK:
        return
    fx.crumbs(cr, t, T_BREAK + 0.02, LOAF_X, LOAF_Y - r * 0.2, ground_y=LOAF_BASE + 9, size=2.6,
              color=P.PROP_COLORS["crumb"], crust=P.PROP_COLORS["crust"], **CRUMB_ARGS)
    fx.smoke(cr, t, T_BREAK + 0.02, LOAF_X, LOAF_Y - r * 0.35, n=7, dur=1.3, rise=34.0, drift=(0.0, 0.0), size=7.5,
             color="#f6ecd6", alpha=0.32, seed=21, spread=1.5)
    k = 0
    t0 = T_BREAK + 0.3
    while t0 < t:                       # steam curling up off the crumb, again and again
        for side in (-1, 1):
            fx.smoke(cr, t, t0 + 0.45 * (side > 0), LOAF_X + side * (sep * 0.75), LOAF_Y - r * 0.55, n=4, dur=2.8,
                     rise=110.0, drift=(side * 10.0, 0.0), size=6.0, color="#fff1da", alpha=0.20,
                     seed=11 + k * 2 + (side > 0))
        k += 1
        t0 += 1.2


def _draw_warmth(cr, t, fr, burst, breath):
    """Warm light falling on the painted night (additive): before the break only the loaf's own
    small pool; after it, a pool that grows across the linen and the meadow with the ring."""
    s = _loaf_state(t)
    pre = 0.18 + 0.05 * breath + 0.18 * s["crack"]
    fx.light_pool(cr, LOAF_X, LOAF_BASE + 4, 120 + 30 * s["crack"], 22, WARM, pre)
    if fr is None:
        return
    k = core.clamp((t - T_BREAK) / 0.5)
    R = min(fr + 40.0, 420.0)
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.rectangle(RC[0] - RR, HORIZON - 4.0, 2 * RR, 2 * RR)        # the ground takes the light...
    cr.clip()
    g = core.radial(BREAD_LIGHT[0], BREAD_LIGHT[1] + 10, R, [(0.0, (1.0, 0.68, 0.34, 0.24 * k)),
                                                             (0.35, (1.0, 0.60, 0.28, 0.12 * k)),
                                                             (1.0, (1.0, 0.55, 0.25, 0.0))])
    cr.set_source(g)
    cr.paint()
    cr.restore()
    fx.glow(cr, BREAD_LIGHT[0], HORIZON - 10, min(R, 260.0), "#ff9a50", 0.07 * k)   # ...the sky only a breath of it
    fx.light_pool(cr, LOAF_X, LOAF_BASE + 6, 140 + 90 * k, 26 + 10 * k, WARM, 0.22 * k + 0.15 * burst)


def _draw_far_lights(cr, t):
    """The far lantern over the bench and the castle's windows catch the light as the ring passes."""
    lx, ly = LANTERN
    u = core.smoothstep(T_BENCH - 0.08, T_BENCH + 0.35, t)           # it catches on the word "bench"
    if u > 0.01:
        flare = 1.0 + 0.8 * math.exp(-max(0.0, t - T_BENCH) * 5.0) * core.smoothstep(T_BENCH - 0.08, T_BENCH + 0.05, t)
        fl = (0.85 + 0.15 * sb.candle_flicker(t, 3)[0]) * flare
        fx.glow(cr, lx, ly - 40.5, 34.0, "#ffb45a", 0.42 * u * fl)
        core.polygon(cr, [(lx - 2.4, ly - 37.5), (lx + 2.4, ly - 37.5), (lx + 1.6, ly - 43.6), (lx - 1.6, ly - 43.6)])
        core.src(cr, core.mix("#2c355e", "#ffd88a", u * fl))
        cr.fill()
        fx.light_pool(cr, lx - 24, ly, 30, 5, "#ffb45a", 0.30 * u)
    cx0, cy0 = CASTLE
    for i, (wx, wy) in enumerate(_CASTLE_WINDOWS):
        x, y = cx0 + wx, cy0 + wy
        v = _lit_at(x, y, t, soft=40.0)
        # each window catches a beat after the last, with a candle's stutter
        v = core.clamp((v - 0.12 * i / len(_CASTLE_WINDOWS)) * 1.6)
        if v <= 0.01:
            continue
        stut = 1.0 if v > 0.6 else (0.6 + 0.4 * core.noise1(t * 18.0 + i, 77))
        cr.rectangle(x - 1.0, y - 1.8, 2.0, 3.6)
        core.src(cr, core.mix("#161a30", "#ffcf7a", v * stut))
        cr.fill()
        fx.glow(cr, x, y, 6.0, "#ffb45a", 0.35 * v * stut)


# --- the bard in the margin -------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _bard_seat():
    """The top of the curl that ends the left vine: the minstrel's perch."""
    end_x = TITLE_W / 2.0 - (RR + RING[2] + 1.0) - 34.0
    ox = RC[0] - (RR + RING[2] + 1.0)
    cx, cy = ox - (end_x * 0.97 - 4.0), RC[1] - 36.0
    return cx + 2.0, cy - 26.0 + 2.5


L_BARD = ch.BARD_LIGHTS["candle"].with_(direction=(-0.55, -0.83), exposure=0.86, rim_strength=0.5,
                                        name="s9_bard_candle")            # the page's candle: dim, from above left
L_BARD_WARM = ch.BARD_LIGHTS["candle"].with_(direction=(0.95, -0.3), exposure=1.06, rim_direction=(0.9, -0.4),
                                             name="s9_bard_warm")         # the bread's warmth, from the right


def _bard_pose(t):
    """The minstrel sings the reprise from his perch: he watches his last page, tunes up, plays
    and sings to the loaf, lights up when it breaks, turns to sing "...next to YOU" to us, holds the
    last note in rapture, and winks as the light closes in on the bread."""
    off = _reprise()[0]
    song = ch.bard_song(t, "reprise", offset=off) if off is not None else {}
    look_us = core.smoothstep(T_NEXT - 0.15, T_YOU2 - 0.1, t)
    broke = core.smoothstep(T_BREAK, T_BREAK + 0.5, t) * (1.0 - look_us)
    tune = core.window(t, T_SONG - 1.15, T_SONG - 0.2, 0.25, 0.3)
    wink = core.window(t, T_WINK, T_WINK + 0.36, 0.07, 0.12)
    kw = dict(sit=1.0, seat_h=125.0, anchor="seat", facing=1, turn=-0.25, lute="play", shadow=False, seed=4,
              look=(0.55 * (1.0 - look_us), 0.3 * (1.0 - look_us)), head_turn=0.12 * (1.0 - look_us),
              head_nod=-0.12 * (1.0 - look_us), look_cam=look_us, mood="twinkle", mood2="happy",
              mood_mix=0.55 * broke, tail_swing=0.35, tail_curl=0.95, wink=wink)
    kw.update(song)
    # the last note: bliss, eyes closed... until the final chord rings -- then he opens them on us
    kw["rapture"] = kw.get("rapture", 0.0) * (1.0 - core.smoothstep(T_FINAL - 0.05, T_FINAL + 0.3, t))
    if t > T_FINAL:
        kw["mood2"], kw["mood_mix"] = "warm", 0.7 * core.smoothstep(T_FINAL, T_FINAL + 0.4, t)
    if tune > 0.0:
        kw["tune"] = max(kw.get("tune", 0.0), tune)
        kw["tune_phase"] = t * 2.2
    return ch.BardPose(**kw)


def _draw_bard(cr, t):
    x, y = _bard_seat()
    warm = _lit_at(x, y - 30, t, soft=120.0)
    light = B.Light.lerp(L_BARD, L_BARD_WARM, _q(warm))
    rig = ch.draw_bard(cr, x, y, BARD_SCALE, _bard_pose(t), light, t)
    ch.bard_twinkle(cr, t, T_WINK + 0.04, rig)
    return rig


# ----------------------------------------------------------------------------------------
# the frame
# ----------------------------------------------------------------------------------------


def draw(cr, t, st):
    _font_opts(cr)
    fr = _front(t)
    # 1. the page (vellum, roundel ground, dim gold, dim title), then the lit gold through the field
    st["page"].paint(cr)
    pat = _light_field(st, t)
    st["lit"].paint_masked(cr, pat)
    # 2. the miniature
    breath = 0.5 + 0.5 * math.sin(t * 1.7)
    burst = 0.0 if fr is None else (0.6 * math.exp(-(t - T_BREAK) * 2.0) + 0.4 * core.smoothstep(0.0, 1.4, t - T_BREAK))
    cr.save()
    core.circle(cr, RC[0], RC[1], RR)
    cr.clip()
    _draw_warmth(cr, t, fr, burst, breath)
    _draw_far_lights(cr, t)
    lvl, warm = _draw_stone(cr, t)
    sep = _draw_loaf(cr, t, burst, breath)
    _draw_crumbs_steam(cr, t, sep)
    cr.restore()
    # 3. the quote and its attribution
    qa = core.ramp(t, T_QUOTE0, T_QUOTE1, "inout_sine")
    if qa > 0.0:
        st["quote"].paint(cr, qa)
        st["attr_dim"].paint(cr, qa)
        cr.push_group()
        st["attr_lit"].paint_masked(cr, pat)
        cr.pop_group_to_source()
        cr.paint_with_alpha(qa)
    # 3b. the minstrel on his perch at the end of the left vine, singing the reprise
    _draw_bard(cr, t)
    # 4. sparkles: where the ring of light reaches the gold; the plucked pearls; the title twinkles
    if fr is not None:
        for (x, y, d, h) in st["sites"]:
            dt = t - (T_BREAK + _t_of_radius(d)) - h * 0.15
            if 0.0 <= dt < 0.5:
                u = dt / 0.5
                fx.sparkle(cr, x, y, 6.0 * math.sin(math.pi * u) * (0.7 + 0.6 * h), WARM_HOT, 0.7 * (1 - u) ** 0.5,
                           angle=0.3 * h)
    for i, tb in enumerate(PLUCKS):
        dt = t - tb
        if 0.0 <= dt < 0.6:
            u = dt / 0.6
            px, py = _pluck_pos(i)
            fx.sparkle(cr, px, py, 11.0 * math.sin(math.pi * u ** 0.6), "#fff4d0", 0.85 * (1.0 - u), angle=0.2)
    _twinkle(cr, t, T_GLINT0 + 0.5 * (T_GLINT1 - T_GLINT0) - 0.05, TITLE_A_X, TITLE_BASE - CAP_H - 1.0, 15.0)
    # 5. motes drifting in front of the page in the candlelight (warmer and brighter after the break)
    warm_all = 0.0 if fr is None else core.clamp((t - T_BREAK) / 3.0)
    fx.dust(cr, t, (RC[0] - 560, RC[1] - 360, 1120, 700), n=34, color="#ffe2a8", alpha=0.20 + 0.28 * warm_all,
            size=(0.8, 2.2), seed=17, drift=(5.0, -7.0), twinkle=0.7,
            mask=lambda x, y: core.clamp(1.15 - math.hypot(x - RC[0], (y - RC[1]) * 1.3) / 560.0))
    # 6. light layer: the candle's pool on the page and the warmth that spreads from the bread
    lc = st["light"].begin()
    fx.glow(lc, CX - 300, 300, 1100, "#ffb070", 0.045 + 0.02 * _flicker(t))
    fx.glow(lc, LOAF_X, LOAF_Y, 240 + 100 * burst, WARM, 0.07 + 0.03 * breath + 0.26 * burst)
    if fr is not None:
        fx.glow(lc, BREAD_LIGHT[0], BREAD_LIGHT[1], max(60.0, fr * 0.95), "#ffae58",
                0.13 * core.clamp((t - T_BREAK) / 1.2))
    if lvl > 0.01:
        fx.glow(lc, STONE_X, STONE_BASE - 34, 200, RUNE, 0.08 * lvl)
    vig = 0.5 + 0.4 * (1.0 - core.ramp(t, T_FADE_IN0, T_FADE_IN1 + 0.6, "inout_sine"))
    fx.post(cr, t, light=st["light"], bloom_strength=0.45, threshold=0.62, bloom_radius=2.2, grain=0.035,
            vignette=vig, vignette_color=(0.07, 0.03, 0.04))
    # 7. fades: up from black as an iris opening from the miniature (the light comes up on the picture
    #    first); out as an iris that closes down onto the loaf (its light is the last thing on screen)
    a_in = 1.0 - core.ramp(t, T_FADE_IN0, T_FADE_IN1, "inout_sine")
    if a_in > 0:
        _iris(cr, a_in, RC[0], RC[1] + 20.0)
    if t > T_FADE_OUT0:
        _iris(cr, core.ramp(t, T_FADE_OUT0, T_FADE_OUT1, "inout_sine"), LOAF_X, LOAF_Y - 8)


def _twinkle(cr, t, t0, x, y, r):
    """A four-point 'ting' on a letter: grows, rotates a little, fades (0.6 s)."""
    dt = t - t0
    if 0.0 <= dt < 0.6:
        u = dt / 0.6
        k = math.sin(math.pi * u ** 0.7)
        fx.sparkle(cr, x, y, r * k, "#fff6dc", 0.9 * k, angle=0.25 * u)


def _iris(cr, a, cx, cy):
    """A radial black wash: amount a (0 clear .. 1 black), the edges darker than the centre
    (cx, cy), so a fade toward black closes in on that point and a fade from black opens from it."""
    if a <= 0:
        return
    if a >= 0.999:
        fx.fade(cr, 1.0)
        return
    inner = a ** 1.8
    outer = min(1.0, a ** 0.45)
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, 1250)
    g.add_color_stop_rgba(0.0, 0, 0, 0, inner)
    g.add_color_stop_rgba(0.16, 0, 0, 0, inner + (outer - inner) * 0.35)
    g.add_color_stop_rgba(0.5, 0, 0, 0, outer)
    g.add_color_stop_rgba(1.0, 0, 0, 0, outer)
    cr.save()
    cr.identity_matrix()
    cr.set_source(g)
    cr.paint()
    cr.restore()


# ----------------------------------------------------------------------------------------
# sound: discrete on-screen events for the foley pass (local seconds)
# ----------------------------------------------------------------------------------------

_PAN_LOAF = round((LOAF_X - CX) / CX * 0.8, 2)     # the loaf sits a little right of centre
CRUMB_ARGS = dict(n=11, seed=7, vx=(-120.0, 120.0), vy=(-240.0, -90.0), gravity=950.0)


def _crumb_hits():
    """Scene times at which the break's crumbs first touch the linen (same maths as fx.crumbs)."""
    y0, gy = LOAF_Y - LOAF_R * 0.2, LOAF_BASE + 9
    out = []
    for i in range(CRUMB_ARGS["n"]):
        tb = T_BREAK + 0.02 + 0.12 * core.hash01(i, CRUMB_ARGS["seed"])
        v0, v1 = CRUMB_ARGS["vy"]
        vy = v0 + (v1 - v0) * core.hash01(i, CRUMB_ARGS["seed"] + 2)
        g = CRUMB_ARGS["gravity"]
        out.append(tb + (-vy + math.sqrt(vy * vy + 2 * g * (gy - y0))) / g)
    return sorted(out)


_HITS = _crumb_hits()
SFX_CUES = sorted([(round(c[0], 3), c[1], c[2]) for c in [
    (T_FADE_IN0 + 0.5, "candle_flicker", {"gain": 0.3, "pan": -0.3}),          # the unseen candle that lights the page
    (T_WHAT + 0.12, "crumbs", {"gain": 0.2, "pan": _PAN_LOAF, "count": 5, "dur": 0.3}),   # the crust crackles as the crack of light opens
    (T_BREAK - 0.02, "bread_tear", {"gain": 0.55, "pan": _PAN_LOAF}),            # the loaf breaks on "do"
    (_HITS[0] - 0.01, "crumbs", {"gain": 0.4, "pan": _PAN_LOAF, "count": 14,         # crumbs patter onto the linen
                                 "dur": round(_HITS[-1] - _HITS[0] + 0.15, 2)}),
]], key=lambda c: c[0])
