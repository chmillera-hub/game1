"""s9_endcard.py -- SCENE 9: THE END CARD.  "Which of you, if your son asks for bread, will give him a stone?"

THE IDEA. The film's last word is a page from the bard's own book: an illuminated end card on warm
charcoal vellum (the manner of the "Black Hours" -- gold and cream on a dark-dyed page), lit by one
unseen candle, framed by blind-tooled rules with gilded corner flourishes. At its heart is a small
painted miniature in a gilded roundel the size of a host: a grey rune-stone and a round crusty loaf
on a linen-covered board, under a deep ultramarine night powdered with shell-gold stars. The two
are twins in shape -- the parable's stones look like loaves, that is its whole point -- and opposite
in substance: the stone carries the city's cold arcane cyan (a carved spiral and a band of runes,
the speaking stone's marks), the loaf (the gnome's loaf) glows softly from within. The whole film in
one picture: what the world handed him, and what fed him.
The card does not just sit there -- it acts the parable out once, quietly, under the bard's
reprise: on "...you know what to DO" the loaf breaks itself open, warm light pours out between the
halves, and that light physically spreads through the gold leaf of the page -- the stars of the
little sky, the stone (its cold runes gutter and go dark, it is washed warm), the roundel's rim,
the vines, the title, the corners -- while "Someone's hungry for bread on the bench next to you" is
sung. Light is the score: the film's color script (cold, isolated -> one warm pool in the dark ->
warmth spreading) replayed in sixteen seconds. Reverent, still, sincere; nothing on the card moves
that a candle could not explain, except the bread.

ONE SHOT, LOCKED OFF (an end card must be still; its life is light, not camera). 0 -> 16.96 s.
Layout (1920x1080). The page is a blind-tooled double rule (104..1816 x 56..872) with a gilded
quatrefoil-and-tendril flourish in each corner; it ends ABOVE the caption band, so the sung
reprise's captions sit under the page like a colophon (nothing in the bottom ~200 px):
  TITLE   "THE STONE AND THE BREAD": Cinzel, letter-spaced, cream with a whisper of gold (base 184)
  ROUNDEL the miniature, centre (960, 430), r 160: a gilded double ring with a madder band of gold
          pearls and gothic cusps top and bottom; gold vine scrolls (hedera leaves, tendril curls,
          berry dots) run out of its equator to left and right and end in spirals under the
          title's ends. Inside, a little still life with depth: the stone set back on the left, the
          loaf in front on the right (its left half overlaps the stone's foot once it opens), a
          linen runner hanging over the board's edge in cone folds with a madder hem and gold thread.
  QUOTE   Cormorant Garamond Italic, cream, two lines: "Which of you, if your son asks for bread, /
          will give him a stone?"  (the line break lands "stone" at the end of the card's sentence)
  ATTRIB  "-- Matthew 7:9": Cinzel small caps in pale gold                               (base 832)
Eye-trace: the iris opens on the roundel (warm loaf + cold stone: the most saturated, most
contrasted thing on the card) -> the page -> a candle glint walks across the gilded title (a
twinkle pings on the apex of the A) -> the quote fades in below -> held -> the loaf breaks and the
light carries the eye outward through the gold and up to the title -> the final chord's glint
ends on "BREAD" -> the iris closes down onto the loaf.

BEATS (today's timeline values; the code reads every one from timeline.json beats/lines and from
the reprise's own syllable timing in film/assets/song/song_timing.json):
  s9_fadein 0.0-1.5   fade up from black as an IRIS opening from the miniature: the light comes up
                      on the picture first, then the page. Candlelit: the gold is deep and quiet,
                      the loaf glows from within, the stone's spiral breathes cold cyan (out of
                      phase with the loaf).
  T_GLINT 1.3-3.0     a candle glint slides across the title left to right; as it crosses "AND" a
                      small four-point twinkle pings on the A's apex. The title is read.
  s9_quote 2.5-4.0    the quote and its attribution fade in (ease in-out).
  4.0-8.75            moving hold: the candle flicker breathes on the gold, motes drift in front of
                      the page, the two glows breathe. s9_song (5.0): the lute begins; each lute
                      BASS note plucks a tiny glint from a pearl of the roundel's rim (a different
                      pearl each time) -- the music lighting the gold. T_VGLINT 6.1-8.5: one slow
                      candle glint drifts along the vines, left to right.
  T_TREMBLE (~8.75)   "...what to": the loaf holds its breath -- a small tremble, a squash that
                      releases, a still beat, and a hairline crack of light opens along its middle
                      score (a faint crust crackle).
  T_BREAK (~9.38)     "DO" -- the sung note's downbeat, which is also a lute bass note: the loaf
                      breaks in two. The crack flares, the halves part (fast 0.16 s, then an
                      ease-out settle with a little rock), strands of crumb stretch and snap, a
                      slit of light stands between the torn faces and soft rays fan up from it, a
                      puff of flour, crumbs hop onto the cloth (cues: bread_tear, crumbs). Steam
                      starts curling up from the crumb.
  T_BREAK -> +4.2     the warmth spreads: a slow ring of light travels outward from the broken loaf
                      through every gilded thing -- the little stars ignite, the stone is washed
                      warm (its runes gutter and go dark over ~1.4 s), the rim lights round from
                      right to left with a run of sparkles, the vines light outward, then the
                      title and the corners; behind the front the gold stays lit and the page
                      itself is warmer.
  s9_final_chord 14.15 a last soft swell over all the gold and one glint across the title, ending
                      in a twinkle on the D of "BREAD", as the final lute chord rings.
  s9_fadeout 15.46-16.96  fade out as an iris closing on the loaf: the edges go first, the bread's
                      light is the last thing on screen.

VALUE / COLOR PLAN. Warm charcoal vellum in a narrow dark band; cream type (the lightest large
shapes) and gold that runs from deep candlelit ochre (unlit) to pale burnished gold (lit); ONE
saturated warm accent (the loaf and its glow) set against ONE cold accent (the stone's cyan runes)
inside a deep ultramarine ground -- the S8 palette (dark blue + one warm pool) in miniature. After
the break warm wins everywhere. Bloom on the loaf, lit gold and title highlights (threshold 0.62);
grain 3.5 %; a deep plum-brown vignette that opens with the fade-in.

PERIOD. Everything is a scribe's material: dyed vellum, blind tooling, gold leaf on raised gesso
with a dark ink edge, shell-gold stars, madder, ultramarine, linen, oak, a carved slate stone, a
crusty boule. Lettering: inscriptional capitals (Cinzel, OFL, film/assets/fonts) and a book italic
(Cormorant Garamond). Nothing modern on the card.

BUILD. Static art is rendered once in setup(): the vellum (numpy: mottling, fibres, candle pool),
the tooling, the roundel ground (night, blooms, board, linen, painted grain), and ALL gilding
(rings, pearls, cusps, vines, corners, the hem's gold thread, the stars, the title) as coverage
masks turned into two cached layers -- "dim" (candlelit leaf) and "lit" (burnished, metallic, with
a gesso bevel lit from the candle side and an ink edge). Every frame paints the dim page, then the
lit gold through a quarter-resolution LIGHT FIELD mask (candle flicker, title and vine glints, rim
plucks, the spreading ring of bread light, the final swell), then the live miniature (stone,
loaf, crumbs, flour, steam, rays), the quote, sparkles, motes, the light layer + bloom, and the
iris fades. Cost ~57 ms/frame on an idle core (127 ms average in the full render on the shared, loaded
machine); setup ~3 s.
"""

import functools
import math
import subprocess

import cairocffi as cairo
import numpy as np
from scipy import ndimage

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


# "...you know what to DO": the loaf breaks on the note under "do" (a bass downbeat)
T_BREAK = _word_note("do", 0, L1.end - 0.4)
T_TREMBLE = T_BREAK - 0.62                       # "what to": it holds its breath, a crack of light opens
T_GLINT0, T_GLINT1 = T_FADE_IN0 + 1.3, T_FADE_IN0 + 3.0   # the candle glint across the title
T_VGLINT0 = T_SONG + 1.1                         # a slower candle glint along the vines in the hold...
T_VGLINT1 = min(T_VGLINT0 + 2.4, T_TREMBLE - 0.2)  # ...finished before the loaf holds its breath
SPREAD_DUR = 4.2                                 # the ring of light: bread -> title ends
FRONT_MAX = 1250.0                               # px travelled by the ring in SPREAD_DUR
# lute bass notes before the break each pluck a glint from the roundel's rim
PLUCKS = [tb for tb in _reprise()[2] if T_SONG < tb < T_TREMBLE - 0.1]

# ----------------------------------------------------------------------------------------
# layout
# ----------------------------------------------------------------------------------------

CX = W / 2.0
TITLE = "THE STONE AND THE BREAD"
TITLE_SIZE, TITLE_SPACING, TITLE_BASE = 62.0, 14.0, 184.0
RC = (CX, 430.0)                      # the roundel's centre
RR = 160.0                            # its inner (painted) radius
RING = (3.5, 12.5, 17.5)              # inner gold ring | madder band with pearls | outer gold ring (radii past RR)
QUOTE = ("“Which of you, if your son asks for bread,", "will give him a stone?”")
QUOTE_SIZE, QUOTE_BASES = 50.0, (702.0, 764.0)
ATTRIB = "— Matthew 7:9"
ATTRIB_SIZE, ATTRIB_BASE = 30.0, 832.0
BOARD_Y = RC[1] + 6.0                 # the board's back edge; its top face runs to BOARD_FRONT
BOARD_FRONT = RC[1] + 74.0
# a little still life with depth: the stone sits further back on the board (left), the loaf in
# front (right); when the loaf opens, its left half comes to overlap the stone's foot
STONE_X, STONE_REST, STONE_SCALE = RC[0] - 68.0, RC[1] + 36.0, 1.56
LOAF_X, REST_Y, LOAF_SCALE = RC[0] + 42.0, RC[1] + 58.0, 2.22
LOAF_SHIFT = 22.0                     # the loaf's centre slides right as it opens
CLOTH_HEM = BOARD_FRONT + 48.0        # the linen runner hangs over the board's front edge to here
FRAME = (104.0, 56.0, W - 104.0, 872.0)   # the blind-tooled border (it ends above the caption band)
LOAF_R = 0.5 * 46.0 * LOAF_SCALE      # the loaf's radius (P.LOAF = 46)
LOAF_Y = REST_Y - 0.56 * LOAF_R       # draw_bread's anchor is the loaf's centre; its base is 0.56 r below
BREAD_LIGHT = (LOAF_X + LOAF_SHIFT, LOAF_Y - 4.0)   # where the warm light comes from (the gap)

# palette
CHARCOAL = "#28221f"
NIGHT = ("#2c3c72", "#18224c", "#0e1430")
MADDER = "#5b1f24"
WARM = "#ffc46b"
WARM_HOT = "#fff1c8"
RUNE = P.PROP_COLORS["rune"]


@functools.lru_cache(maxsize=8)
def _font_ok(name):
    try:
        out = subprocess.run(["fc-list", ":family=" + name, "family"], capture_output=True, text=True, timeout=5)
        return bool(out.stdout.strip())
    except Exception:
        return False


TITLE_FONT = "Cinzel" if _font_ok("Cinzel") else core.SERIF   # film/assets/fonts/Cinzel-Variable.ttf (OFL)
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
    n = 52
    return [(TAU * k / n - math.pi / 2, RC[0] + math.cos(TAU * k / n - math.pi / 2) * rm,
             RC[1] + math.sin(TAU * k / n - math.pi / 2) * rm) for k in range(n)]


def _cusps():
    """Small gilded trefoil cusps on the outer ring at N and S (E and W carry the vines)."""
    out = []
    for a in (-math.pi / 2, math.pi / 2):
        r = RR + RING[2] + 5.0
        out.append((RC[0] + math.cos(a) * r, RC[1] + math.sin(a) * r, a))
    return out


def _stars():
    """The shell-gold stars of the miniature's sky: [(x, y, r, kind)] (kind 0 star, 1 dot)."""
    out = []
    step = 32.0
    for i in range(-8, 9):
        for j in range(-8, 9):
            x = RC[0] + i * step + (step / 2.0 if j % 2 else 0.0)
            y = RC[1] + j * step * 0.87
            if math.hypot(x - RC[0], y - RC[1]) < RR - 9 and y < BOARD_Y - 8:
                out.append((x, y, 4.6 + 1.2 * core.hash01(i * 31 + j, 5), 0))
            # tiny dots between the stars
            xd, yd = x + step * 0.5, y + step * 0.29
            if math.hypot(xd - RC[0], yd - RC[1]) < RR - 7 and yd < BOARD_Y - 6:
                out.append((xd, yd, 1.3, 1))
    return out


def _star_path(cr, x, y, r):
    """An eight-pointed star (four long rays, four short)."""
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * TAU / 16
        rr = r if k % 4 == 0 else (r * 0.55 if k % 2 == 0 else r * 0.26)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    core.polygon(cr, pts)


# ----------------------------------------------------------------------------------------
# static art (setup)
# ----------------------------------------------------------------------------------------


def _vellum():
    """Warm charcoal vellum: a candle pool round the composition, mottling, fibres, darker edges."""
    from PIL import Image
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = _rgb(CHARCOAL)
    warm = _rgb("#372d27")
    d = np.sqrt(((xx - CX) / 1.3) ** 2 + (yy - 440.0) ** 2) / 820.0
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


def _draw_roundel_ground(cr):
    """Inside the roundel: deep ultramarine night (lighter behind the loaf), watercolour blooms,
    the oak board in perspective and the dark beneath it."""
    cr.save()
    core.circle(cr, RC[0], RC[1], RR + 0.5)
    cr.clip()
    g = core.radial(LOAF_X - 30, LOAF_Y - 50, RR * 1.55, [(0.0, NIGHT[0]), (0.5, NIGHT[1]), (1.0, NIGHT[2])])
    cr.set_source(g)
    cr.paint()
    for i in range(8):                                     # soft blooms (the wash dried unevenly)
        bx = RC[0] + (core.hash01(i, 5) - 0.5) * RR * 1.6
        by = RC[1] + (core.hash01(i, 6) - 0.75) * RR * 1.2
        rr = RR * (0.22 + 0.3 * core.hash01(i, 7))
        col = "#4c62a6" if core.hash01(i, 8) < 0.55 else "#0a0f26"
        fx.glow(cr, bx, by, rr, col, 0.11, additive=False)
    # the board: its top face (back edge -> front edge), its front face, the dark under it
    x0, x1 = RC[0] - RR - 10, RC[0] + RR + 10
    top = [(x0, BOARD_Y + 2), (x1, BOARD_Y - 2), (x1, BOARD_FRONT - 2), (x0, BOARD_FRONT + 2)]
    core.polygon(cr, top)
    cr.set_source(core.linear(0, BOARD_Y, 0, BOARD_FRONT, [(0.0, "#4f3421"), (1.0, "#80583a")]))
    cr.fill()
    for k in range(10):                                    # grain
        f = k / 9.0
        yk = BOARD_Y + 4 + f * (BOARD_FRONT - BOARD_Y - 8)
        pts = [(x0 + i * 26, yk + 1.3 * math.sin(i * 0.8 + k * 1.9)) for i in range(14)]
        B.detail_line(cr, pts, 0.8 + 0.5 * f, "#35210f", 0.35 + 0.15 * f, taper=(0.6, 1.0, 0.6))
    front = [(x0, BOARD_FRONT + 2), (x1, BOARD_FRONT - 2), (x1, BOARD_FRONT + 22), (x0, BOARD_FRONT + 26)]
    core.polygon(cr, front)
    cr.set_source(core.linear(0, BOARD_FRONT, 0, BOARD_FRONT + 26, [(0.0, "#4a3020"), (1.0, "#2a1a11")]))
    cr.fill()
    B.detail_line(cr, [(x0, BOARD_FRONT + 2.5), (x1, BOARD_FRONT - 1.5)], 1.8, "#b08353", 0.55, taper=(0.3, 1.0, 0.3))
    cr.rectangle(x0 - 10, BOARD_FRONT + 24, x1 - x0 + 20, RR)
    cr.set_source(core.linear(0, BOARD_FRONT + 24, 0, RC[1] + RR, [(0.0, "#140d0b"), (1.0, "#0b0910")]))
    cr.fill()
    _draw_cloth(cr)
    sb.paper_grain(cr, RC[0] - RR, RC[1] - RR, 2 * RR, 2 * RR, 0.28, scale=0.6, seed=19)   # painted, not printed
    # the ring's raised gesso shades the painted ground just inside it
    g2 = core.radial(RC[0], RC[1], RR, [(0.0, (0, 0, 0, 0)), (0.84, (0, 0, 0, 0)), (1.0, (0, 0, 0, 0.6))])
    cr.set_source(g2)
    cr.paint()
    cr.restore()


CLOTH_FOLDS = 8


def _cloth_geom():
    """The linen runner: x extent, its back and front edges on the board, and the hem line (the
    fold crests swing forward and hang a little lower than the troughs)."""
    x0, x1 = RC[0] - RR - 12, RC[0] + RR + 12
    back = BOARD_Y + 13.0
    front = BOARD_FRONT + 1.0
    n = 64
    hem = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        ph = (x - x0) / (x1 - x0) * CLOTH_FOLDS
        hem.append((x, CLOTH_HEM + 4.0 * math.cos(ph * TAU) + 1.5 * math.sin(i * 0.7)))
    return x0, x1, back, front, hem


def _draw_cloth(cr):
    """A linen runner laid across the board under the stone and the loaf, hanging over the front
    edge in soft cone folds, with a madder hem (its gold thread is gilded with the rest). Lit warm
    from the loaf, falling off to cool grey toward the edges."""
    x0, x1, back, front, hem = _cloth_geom()
    lx, ly = LOAF_X + 6, REST_Y - 8
    # top face: lit from the loaf, a fine weave, a couple of soft creases
    top = [(x0, back + 1), (x1, back - 2), (x1, front - 1), (x0, front + 2)]
    core.polygon(cr, top)
    cr.set_source(core.radial(lx, ly, 270, [(0.0, "#ae9e80"), (0.35, "#8a7e6a"), (0.75, "#625b53"), (1.0, "#46423f")]))
    cr.fill()
    cr.save()
    core.polygon(cr, top)
    cr.clip()
    cr.rectangle(x0, back - 4, x1 - x0, 14)
    cr.set_source(core.linear(0, back - 3, 0, back + 10, [(0.0, (0.06, 0.03, 0.03, 0.5)), (1.0, (0, 0, 0, 0))]))
    cr.fill()
    for k in range(5):                                   # creases: soft light streaks along the runner
        yk = back + 9 + k * (front - back - 14) / 4.0
        B.detail_line(cr, [(x0 + 30 + 40 * k, yk + 2), (RC[0] - 40 + 25 * k, yk), (x1 - 40, yk + 1.5)], 1.2,
                      "#fff4e0", 0.07, taper=(0.2, 1.0, 0.2))
    cr.restore()
    # the hanging front: cone folds, darker than the top (it turns away from the light)
    cr.new_path()
    cr.move_to(x0, front + 2)
    cr.line_to(x1, front - 1)
    for (hx, hy) in reversed(hem):
        cr.line_to(hx, hy)
    cr.close_path()
    hang = B.Path(cr)
    stops = []
    m = CLOTH_FOLDS * 4
    for i in range(m + 1):
        u = i / m
        ph = u * CLOTH_FOLDS
        crest = 0.5 + 0.5 * math.cos(ph * TAU)              # 1 on a fold's crest, 0 in a trough
        warm = math.exp(-((x0 + u * (x1 - x0) - lx) / 150.0) ** 2)
        base = core.mix("#3a3532", "#6d6457", crest)
        stops.append((u, core.mix(base, core.mix("#8a7a5f", "#b29d79", crest), 0.65 * warm)))
    hang.add(cr)
    cr.set_source(core.linear(x0, 0, x1, 0, stops))
    cr.fill()
    cr.save()
    hang.add(cr)
    cr.clip()
    cr.rectangle(x0, front - 3, x1 - x0, CLOTH_HEM - front + 12)   # the bend over the edge, then the drop
    cr.set_source(core.linear(0, front - 3, 0, CLOTH_HEM + 6, [(0.0, (1.0, 0.95, 0.85, 0.22)), (0.12, (0, 0, 0, 0.0)),
                                                              (0.55, (0, 0, 0, 0.12)), (1.0, (0, 0, 0, 0.30))]))
    cr.fill()
    # the folds start narrow at the bend and open toward the hem: dark trough lines
    lines = []
    for k in range(CLOTH_FOLDS):
        xt = x0 + (k + 0.5) * (x1 - x0) / CLOTH_FOLDS
        lines.append([(xt + 2.0, front + 3), (xt - 1.0, (front + CLOTH_HEM) / 2.0), (xt - 3.0, CLOTH_HEM - 6)])
    B.detail_lines(cr, lines, 2.4, "#1f1b19", 0.35, taper=(0.1, 1.0, 0.6))
    # the madder hem band, following the hem
    cr.new_path()
    core.polygon(cr, [(hx, hy - 11.0) for hx, hy in hem] + [(hx, hy - 3.0) for hx, hy in reversed(hem)])
    core.src(cr, "#5a1c21")
    cr.fill()
    cr.restore()
    # the hem's lower edge: a thin dark line (the cloth ends)
    B.detail_line(cr, hem, 1.6, "#120c0b", 0.6, taper=(0.0, 1.0, 0.0))


def _draw_tooling(cr):
    """Blind tooling pressed into the vellum round the page: a double rule, each a dark groove with
    a faint lit lip on its lower-right side (no colour, no gold: it is felt more than seen)."""
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


def _corner_pieces():
    """Gilded corner flourishes on the tooled border, as (stems, leaves, dots) like the vines: two
    tendrils running along the inner rule that end in curls, and a quatrefoil rosette on the corner."""
    stems, leaves, dots = [], [], []
    x0, y0, x1, y1 = FRAME
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        ix, iy = cx + sx * 9.0, cy + sy * 9.0                    # the inner rule's corner

        def P_(x, y, ix=ix, iy=iy, sx=sx, sy=sy):
            return (ix + sx * x, iy + sy * y)

        for swap in (False, True):
            curl = _spiral_pts(60.0, 17.5, 9.0, 2.2, -math.pi / 2, 1.25, sign=1.0, n=18)
            local = [(7.0, 7.0), (27.0, 7.6), (47.0, 8.4)] + curl
            stems.append(([P_(y, x) if swap else P_(x, y) for (x, y) in local], 2.8, 1.0))
        qx, qy = P_(9.0, 9.0)                                    # a gilded quatrefoil rosette at the corner
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            dots.append((qx + math.cos(a) * 5.2, qy + math.sin(a) * 5.2, 4.3))
        dots.append((*P_(22.0, 22.0), 1.9))
    return stems, leaves, dots


def _draw_band(cr):
    """The madder band between the gold rings."""
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    _ring_path(cr, RR + RING[0] - 0.5, RR + RING[1] + 0.5)
    core.src(cr, MADDER)
    cr.fill()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)


def _gold_coverage():
    """(M_leaf, M_stars, vine dots): burnished leaf (rings, pearls, cusps, vines) and shell-gold stars."""
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
            core.circle(c, x, y, 2.4)
        c.fill()
        # the gold thread of the cloth's hem (inside the roundel)
        c.save()
        core.circle(c, RC[0], RC[1], RR - 1.0)
        c.clip()
        _x0, _x1, _b, _f, hem = _cloth_geom()
        core.tapered(c, [(hx, hy - 7.0) for (hx, hy) in hem[::2]], 1.4, 1.4, cap=False)
        c.fill()
        for (hx, hy) in hem[1::4]:
            core.circle(c, hx, hy - 7.0, 1.7)
        c.fill()
        c.restore()
        for (x, y, a) in _cusps():
            for k in (-1, 0, 1):
                aa = a + k * 0.07
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
    return M_leaf, M_st, (dots_l + dots_r)


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
    M_leaf, M_st, vine_dots = _gold_coverage()
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
    M_st_lit = M_st * 0.72
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
    # sparkle sites on the gold, with their distance from the loaf (for the ring of light)
    sites = [(x, y) for (_a, x, y) in _pearls()[::4]] + [(x, y) for (x, y, r) in vine_dots]
    sites += [(x, y) for (x, y, r, kind) in _stars() if kind == 0][::5]
    st["sites"] = [(x, y, math.hypot(x - BREAD_LIGHT[0], y - BREAD_LIGHT[1]), core.hash01(i, 33))
                   for i, (x, y) in enumerate(sites)]
    st["light"] = fx.LightLayer()
    st["lf"] = cairo.ImageSurface(cairo.FORMAT_A8, W // 4, H // 4)
    return st


# ----------------------------------------------------------------------------------------
# per-frame light: the field that reveals the lit gold
# ----------------------------------------------------------------------------------------


def _front(t):
    """Radius (px) of the spreading ring of bread light, or None before the break."""
    if t < T_BREAK:
        return None
    u = core.clamp((t - T_BREAK) / SPREAD_DUR)
    return FRONT_MAX * (1.0 - (1.0 - u) ** 1.7)


def _t_of_radius(d):
    """Seconds after the break at which the ring of light reaches radius d."""
    u = core.clamp(d / FRONT_MAX)
    return (1.0 - (1.0 - u) ** (1.0 / 1.7)) * SPREAD_DUR


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
    # 4. the bread: a warm core before the break; after it, a ring travels out, lit behind it
    fr = _front(t)
    bx, by = BREAD_LIGHT
    if fr is None:
        pre = 0.16 + 0.05 * math.sin(t * 1.7)
        k = 1.0 + 0.8 * core.smoothstep(T_TREMBLE, T_BREAK, t)
        gg = cairo.RadialGradient(bx, by, 0, bx, by, 170)
        gg.add_color_stop_rgba(0.0, 0, 0, 0, pre * k)
        gg.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
        c.set_source(gg)
        c.arc(bx, by, 170, 0, TAU)
        c.fill()
    else:
        R = max(fr, 1.0)
        w = 150.0
        gg = cairo.RadialGradient(bx, by, 0, bx, by, R + w)
        n = 16
        for i in range(n + 1):
            r = (R + w) * i / n
            steady = 0.80 * math.exp(-r / 380.0) + 0.24
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
        gx, v = _glint_x(t, T_FINAL, T_FINAL + 1.6)
        if v < 1.0:
            _glint_band(c, gx, TITLE_BASE - 22, 150.0, 0.85 * math.sin(math.pi * v), (0, TITLE_BASE - 80, W, 110))
    lf.flush()
    pat = cairo.SurfacePattern(lf)
    m = cairo.Matrix()
    m.scale(0.25, 0.25)
    pat.set_matrix(m)
    pat.set_filter(cairo.FILTER_BILINEAR)
    return pat


def _lit_at(x, y, t):
    """0..1 how much the bread's light has reached (x, y)."""
    fr = _front(t)
    if fr is None:
        return 0.0
    d = math.hypot(x - BREAD_LIGHT[0], y - BREAD_LIGHT[1])
    return core.smoothstep(d - 40.0, d + 160.0, fr)


# ----------------------------------------------------------------------------------------
# the miniature: the rune-stone and the loaf
# ----------------------------------------------------------------------------------------

L_COLD = B.Light(key=(0.80, 0.86, 1.02), ambient=(0.30, 0.34, 0.54), rim=(0.55, 0.88, 1.0), rim_strength=0.6,
                 direction=(-0.5, -0.86), rim_direction=(-0.9, -0.4), name="s9_cold")
L_WARM_STONE = B.Light(key=(1.14, 0.88, 0.60), ambient=(0.42, 0.34, 0.40), rim=(1.0, 0.74, 0.40), rim_strength=0.9,
                       direction=(0.92, -0.4), rim_direction=(0.95, -0.3), name="s9_warm_stone")
L_BREAD = B.Light(key=(1.10, 0.92, 0.70), ambient=(0.52, 0.40, 0.42), rim=(1.0, 0.82, 0.50), rim_strength=0.65,
                  direction=(-0.45, -0.89), rim_direction=(0.7, -0.7), name="s9_bread")

# the rune-stone: shaped like the loaf (a domed field stone), anchor = the middle of its base
STONE_PTS = [(-33, 10), (-36, 2), (-35, -6), (-31, -14), (-24, -21), (-14, -26), (-3, -28), (8, -27.5), (18, -24),
             (27, -18), (33, -10), (36, -1), (35, 7), (29, 11.5), (12, 13), (-8, 13), (-24, 12.5)]
_GLYPHS = ([[(0.5, 0), (0.5, 1)], [(0.5, 0.2), (0.95, 0.0)], [(0.5, 0.45), (0.95, 0.25)]],     # fehu
           [[(0.5, 0), (0.5, 1)], [(0.5, 0.45), (0.1, 0.1)], [(0.5, 0.45), (0.9, 0.1)]],       # algiz
           [[(0.1, 0), (0.9, 1)], [(0.9, 0), (0.1, 1)]],                                       # gebo
           [[(0.3, 0), (0.3, 1)], [(0.3, 0.1), (0.85, 0.45)], [(0.85, 0.45), (0.3, 0.75)]])    # thurisaz


def _q(u, n=24):
    """Quantize a blend amount so the palette cache stays small."""
    return round(core.clamp(u) * n) / n


@functools.lru_cache(maxsize=1)
def _stone_marks():
    spiral = [(-1.0 + math.cos(a) * 10.0 * (0.12 + 0.88 * a / (2.6 * math.pi)),
               -9.0 + math.sin(a) * 8.4 * (0.12 + 0.88 * a / (2.6 * math.pi)))
              for a in [k * 2.6 * math.pi / 26 for k in range(27)]]
    runes = []
    for k, a0 in enumerate((-2.62, -2.27, -1.92, -1.22, -0.87, -0.52)):
        rx, ry = -1.0 + math.cos(a0) * 26.5, -5.0 + math.sin(a0) * 17.5
        ang = a0 + math.pi / 2
        h = 5.4
        ca, sa = math.cos(ang), math.sin(ang)
        for (u0, v0), (u1, v1) in _GLYPHS[k % len(_GLYPHS)]:
            seg = []
            for (u, v) in ((u0, v0), (u1, v1)):
                px, py = (u - 0.5) * h * 0.6, (v - 0.5) * h
                seg.append((rx + px * ca - py * sa, ry + px * sa + py * ca))
            runes.append(seg)
    return spiral, runes


def _stone_level(t):
    """(cold rune glow 0..1, warmth reached 0..1): a slow breath, out of phase with the loaf. When
    the warm light washes over the stone its runes gutter (a little dying flicker) and go dark over
    ~1.4 s; the warm light on it follows the front."""
    breath = 0.62 + 0.18 * math.sin(t * 1.15 + 1.9)
    warm = _lit_at(STONE_X + 30, STONE_REST - 30, t)
    if t < T_BREAK:
        return breath, warm
    u = core.clamp((t - (T_BREAK + 0.15)) / 1.4)
    gutter = 1.0 - 0.45 * u * (0.5 + 0.5 * core.noise1(t * 19.0, 61)) * (1.0 - u)
    return breath * (1.0 - core.smoothstep(0.0, 1.0, u)) * gutter, warm


def _draw_stone(cr, t):
    lvl, warm = _stone_level(t)
    light = B.Light.lerp(L_COLD, L_WARM_STONE, _q(warm))
    sc = STONE_SCALE
    B.contact_shadow(cr, STONE_X + 3, STONE_REST + 1, 40 * sc, 6.5 * sc, alpha=0.6, color="#0c0806")
    cr.save()
    cr.translate(STONE_X, STONE_REST - 13 * sc)
    cr.scale(sc, sc)
    lw = B.line_for(B.LINE, B.device_scale(cr))             # the house line, in local units
    sh, so = B.smooth_paths(cr, STONE_PTS, lw, 0.9)
    p = B.shade(cr, sh, P.prop_mats()["stone"], light, lw, outline=so, size=38.0, rim=1.0)
    cr.save()
    sh.add(cr)
    cr.clip()
    core.src(cr, p.hi, 0.22)                                 # pale and dark flecks: a field stone
    for i in range(11):
        core.circle(cr, (core.hash01(i, 3) - 0.5) * 60, -22 + core.hash01(i, 4) * 32, 0.5 + 0.8 * core.hash01(i, 5))
    cr.fill()
    core.src(cr, p.line, 0.22)
    for i in range(8):
        core.circle(cr, (core.hash01(i, 6) - 0.5) * 60, -20 + core.hash01(i, 7) * 30, 0.5 + 0.7 * core.hash01(i, 8))
    cr.fill()
    B.detail_lines(cr, [[(-30, 3), (-22, 6), (-10, 7.5)], [(14, -22), (20, -17)]], 0.9, p.line, 0.35)   # a chip, a crack
    cr.restore()
    groove = core.mix(p.shadow, p.line, 0.5)
    glowc = core.mix(groove, RUNE, 0.12 + 0.88 * lvl)
    spiral, runes = _stone_marks()
    B.detail_lines(cr, [spiral], 2.7, groove, 0.85, taper=(0.4, 1.0, 0.8))
    B.detail_lines(cr, runes, 1.5, groove, 0.75, taper=(0.8, 1.0, 0.8))
    if lvl > 0.01:
        B.detail_lines(cr, [spiral], 1.4, glowc, 0.3 + 0.7 * lvl, taper=(0.4, 1.0, 0.8))
        B.detail_lines(cr, runes, 0.85, glowc, 0.25 + 0.75 * lvl, taper=(0.8, 1.0, 0.8))
        fx.glow(cr, -1.0, -9.0, 22.0, RUNE, 0.55 * lvl)
    B.sheen(cr, -15, -20, 10, 3.0, angle=-0.35, alpha=0.22 * (1.0 - 0.6 * warm))
    cr.restore()
    if lvl > 0.01:                                           # its cold light on the ground about it
        fx.glow(cr, STONE_X, STONE_REST - 22 * sc, 58 * sc, RUNE, 0.16 * lvl)
    return lvl, warm


def _bread_state(t):
    """(tear, rock angle, squash, crack light) of the loaf at t."""
    if t < T_TREMBLE:
        return 0.0, 0.0, 0.0, 0.0
    if t < T_BREAK:
        u = (t - T_TREMBLE) / (T_BREAK - T_TREMBLE)
        trem = math.sin((t - T_TREMBLE) * 33.0) * 0.016 * u ** 1.4 * (1.0 - core.smoothstep(0.78, 0.97, u))
        squash = 0.035 * core.smoothstep(0.3, 0.82, u) * (1.0 - core.smoothstep(0.86, 1.0, u))
        return 0.0, trem, squash, core.smoothstep(0.1, 1.0, u)
    dt = t - T_BREAK
    tear = 0.40 * core.smoothstep(0.0, 0.16, dt) + 0.27 * core.out_cubic(core.clamp((dt - 0.1) / 0.85))
    rock = math.exp(-dt * 4.5) * math.sin(dt * 16.0) * 0.02
    return tear, rock, 0.0, 1.0


def _opened(tear):
    """0..1: how far the break has opened (the halves' extra separation, lean and slide)."""
    return core.smooth(min(1.0, tear / 0.67))


def _draw_loaf(cr, t, burst):
    """The loaf: whole, trembling with a crack of light, then broken -- each half drawn on its own
    side of the centre line (draw_bread's tear, clipped), pushed a little further apart and leaning
    out, so a slit of light stands between the torn faces."""
    tear, rock, squash, crack = _bread_state(t)
    op = _opened(tear)
    x = LOAF_X + LOAF_SHIFT * op
    r = LOAF_R
    g = r * 0.95 * core.smooth(tear)          # draw_bread's own offset of each half
    sep = 0.16 * r * op                       # ...and ours on top of it
    vee = 0.075 * op                          # the halves lean apart (pivot: the inner foot)
    # the light from inside, drawn BEHIND the loaf: it shows in the crack, then between the halves
    if tear > 0.02 or crack > 0.0:
        k = max(crack * 0.55, min(1.0, tear * 3.0))
        fx.glow(cr, x, LOAF_Y - r * 0.05, r * (0.9 + 0.9 * burst), WARM_HOT, 0.6 * k)
        if tear > 0.02:
            cr.save()                          # the slit itself: a tall hot ellipse
            cr.translate(x, LOAF_Y + r * 0.05)
            cr.scale(1.0, 2.6)
            fx.glow(cr, 0, 0, r * 0.32 + sep, "#ffffff", 0.75 * k)
            cr.restore()
    for side in ((-1, 1) if tear > 0.02 else (0,)):
        B.contact_shadow(cr, x + side * (g + sep), REST_Y + 1, r * (1.0 if side == 0 else 0.72), r * 0.13,
                         alpha=0.6, color="#0c0806")
    if tear <= 0.02:
        cr.save()
        cr.translate(x, REST_Y)
        cr.rotate(rock)
        cr.scale(1.0 + squash, 1.0 - squash)
        cr.translate(0, LOAF_Y - REST_Y)
        P.draw_bread(cr, 0, 0, P.LOAF, L_BREAD, t, state="loaf", tear=0.0, seed=3, scale=LOAF_SCALE)
        cr.restore()
    else:
        for side in (-1, 1):
            cr.save()
            cr.translate(x, REST_Y)
            cr.rotate(rock)
            px = side * (sep + 0.06 * r)       # lean out about the inner foot of this half
            cr.translate(px, 0)
            cr.rotate(side * vee)
            cr.translate(-px + side * sep, LOAF_Y - REST_Y)
            cr.rectangle(0.0 if side > 0 else -4.0 * r, -4.0 * r, 4.0 * r, 8.0 * r)
            cr.clip()
            P.draw_bread(cr, 0, 0, P.LOAF, L_BREAD, t, state="loaf", tear=tear, seed=3, scale=LOAF_SCALE)
            cr.restore()
    # the crack of light along its middle score before it parts
    if crack > 0.01 and tear < 0.25:
        k = crack * (1.0 - core.clamp(tear / 0.25))
        pts = [(x + 1.0, LOAF_Y - r * 0.66), (x - 1.5, LOAF_Y - r * 0.25), (x + 1.2, LOAF_Y + r * 0.12),
               (x, LOAF_Y + r * 0.46)]
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        B.detail_line(cr, pts, 1.6 + 2.2 * k, WARM_HOT, 0.9 * k, taper=(0.3, 1.0, 0.3))
        cr.restore()
        fx.glow(cr, x, LOAF_Y - r * 0.1, r * (0.35 + 0.4 * k), WARM, 0.45 * k)
    # rays of the light pouring out of the gap, very soft (a painted glory)
    if op > 0.02:
        fx.god_rays(cr, x, LOAF_Y + r * 0.1, -math.pi / 2, 1.9, 175.0 + 40.0 * op, WARM, t, n=7, width=(4.0, 34.0),
                    alpha=0.13 * op * (0.6 + 0.4 * burst), seed=5, shimmer=0.45)
    return tear, x


def _draw_steam_and_flour(cr, t, x):
    if t < T_BREAK:
        return
    r = LOAF_R
    # flour puff at the break
    fx.smoke(cr, t, T_BREAK + 0.02, x, LOAF_Y - r * 0.3, n=6, dur=1.3, rise=34.0, drift=(0.0, 0.0), size=7.0,
             color="#f6ecd6", alpha=0.32, seed=21, spread=1.4)
    # steam curling up from the crumb, again and again
    k = 0
    t0 = T_BREAK + 0.3
    while t0 < t:
        for side in (-1, 1):
            fx.smoke(cr, t, t0 + 0.4 * (side > 0), x + side * r * 0.42, LOAF_Y - r * 0.62, n=4, dur=2.8, rise=105.0,
                     drift=(side * 9.0, 0.0), size=6.0, color="#fff1da", alpha=0.22, seed=11 + k * 2 + (side > 0))
        k += 1
        t0 += 1.2


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
    lx0 = LOAF_X + LOAF_SHIFT * _opened(_bread_state(t)[0])
    cr.save()
    core.circle(cr, RC[0], RC[1], RR)
    cr.clip()
    # warm light on the board and on the night behind the loaf
    fx.light_pool(cr, lx0, REST_Y + 2, 120 + 70 * burst, 26 + 10 * burst, WARM, 0.20 + 0.45 * burst)
    fx.glow(cr, lx0, LOAF_Y - 6, 125 + 70 * burst, "#ff9a45", 0.12 + 0.05 * breath + 0.22 * burst)
    lvl, warm = _draw_stone(cr, t)
    tear, lx = _draw_loaf(cr, t, burst)
    if fr is not None:
        fx.crumbs(cr, t, T_BREAK + 0.03, lx, LOAF_Y - 6, n=9, seed=7, vx=(-90.0, 90.0), vy=(-200.0, -80.0),
                  gravity=900.0, ground_y=REST_Y + 4, size=2.4, color=P.PROP_COLORS["crumb"],
                  crust=P.PROP_COLORS["crust"])
    _draw_steam_and_flour(cr, t, lx)
    # a gentle warm sheen over the loaf (it glows from within; kept low so the crumb never blows out)
    fx.glow(cr, lx, LOAF_Y - 2, LOAF_R * 1.25, WARM, 0.10 + 0.04 * breath + 0.08 * burst)
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
    # 4. sparkles: where the ring of light reaches the gold; the plucked pearls; the title twinkles
    if fr is not None:
        for (x, y, d, h) in st["sites"]:
            dt = t - (T_BREAK + _t_of_radius(d)) - h * 0.12
            if 0.0 <= dt < 0.5:
                u = dt / 0.5
                fx.sparkle(cr, x, y, 6.5 * math.sin(math.pi * u) * (0.7 + 0.6 * h), WARM_HOT, 0.75 * (1 - u) ** 0.5,
                           angle=0.3 * h)
    for i, tb in enumerate(PLUCKS):
        dt = t - tb
        if 0.0 <= dt < 0.6:
            u = dt / 0.6
            px, py = _pluck_pos(i)
            fx.sparkle(cr, px, py, 11.0 * math.sin(math.pi * u ** 0.6), "#fff4d0", 0.85 * (1.0 - u), angle=0.2)
    _twinkle(cr, t, T_GLINT0 + 0.5 * (T_GLINT1 - T_GLINT0) - 0.05, TITLE_A_X, TITLE_BASE - CAP_H - 1.0, 15.0)
    _twinkle(cr, t, T_FINAL + 1.25, TITLE_END_X, TITLE_BASE - CAP_H * 0.95, 17.0)
    # 5. motes drifting in front of the page in the candlelight (warmer and brighter after the break)
    warm_all = 0.0 if fr is None else core.clamp((t - T_BREAK) / 3.0)
    fx.dust(cr, t, (RC[0] - 540, RC[1] - 340, 1080, 660), n=34, color="#ffe2a8", alpha=0.20 + 0.28 * warm_all,
            size=(0.8, 2.2), seed=17, drift=(5.0, -7.0), twinkle=0.7,
            mask=lambda x, y: core.clamp(1.15 - math.hypot(x - RC[0], (y - RC[1]) * 1.3) / 540.0))
    # 6. light layer: the candle's pool on the page and the warmth that spreads from the bread
    lc = st["light"].begin()
    fx.glow(lc, CX - 300, 300, 1100, "#ffb070", 0.045 + 0.02 * _flicker(t))
    fx.glow(lc, lx, LOAF_Y, 260 + 90 * burst, WARM, 0.08 + 0.03 * breath + 0.24 * burst)
    if fr is not None:
        fx.glow(lc, BREAD_LIGHT[0], BREAD_LIGHT[1], max(60.0, fr * 0.95), "#ffae58", 0.15 * core.clamp((t - T_BREAK) / 1.2))
    if lvl > 0.01:
        fx.glow(lc, STONE_X, STONE_REST - 30, 210, RUNE, 0.09 * lvl)
    vig = 0.5 + 0.4 * (1.0 - core.ramp(t, T_FADE_IN0, T_FADE_IN1 + 0.6, "inout_sine"))
    fx.post(cr, t, light=st["light"], bloom_strength=0.45, threshold=0.62, bloom_radius=2.2, grain=0.035,
            vignette=vig, vignette_color=(0.07, 0.03, 0.04))
    # 7. fades: up from black as an iris opening from the miniature (the light comes up on the picture
    #    first); out as an iris that closes down onto the loaf (its light is the last thing on screen)
    a_in = 1.0 - core.ramp(t, T_FADE_IN0, T_FADE_IN1, "inout_sine")
    if a_in > 0:
        _iris(cr, a_in, RC[0], RC[1] + 10.0)
    if t > T_FADE_OUT0:
        _iris(cr, core.ramp(t, T_FADE_OUT0, T_FADE_OUT1, "inout_sine"), lx, LOAF_Y - 8)


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

_PAN_LOAF = round((LOAF_X + LOAF_SHIFT * 0.5 - CX) / CX * 0.8, 2)     # the loaf sits a little right of centre
SFX_CUES = sorted([
    (T_FADE_IN0 + 0.5, "candle_flicker", {"gain": 0.3, "pan": -0.3}),          # the unseen candle that lights the page
    (T_BREAK - 0.32, "crumbs", {"gain": 0.22, "pan": _PAN_LOAF, "count": 6, "dur": 0.3}),   # the crust crackles as the crack of light opens
    (T_BREAK - 0.02, "bread_tear", {"gain": 0.55, "pan": _PAN_LOAF}),            # the loaf breaks on "do"
    (T_BREAK + 0.14, "crumbs", {"gain": 0.45, "pan": _PAN_LOAF}),                # crumbs hop onto the board
], key=lambda c: c[0])
