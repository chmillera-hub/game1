"""s0_prologue.py -- SCENE 0, THE PROLOGUE: "A Kingdom of Stone" (the bard's song, ~43 s).

THE IDEA. A storyteller's invitation. Before the film shows us a cold kingdom it shows us the one
warm room in it: a candlelit minstrel's nook where a twinkly cockatrice bard opens a great book and
sings. The prologue is the film's thesis in miniature -- a town of locked doors, a dragon who waves
and is passed by, merchants selling stones -- told in the warmest possible light, so the cold that
follows (S1-S5) reads as the exception and the warmth of the bread (S6-S8) as a homecoming. It
ends by pulling a stool up for *us* and turning the page to the wash-house: the tale begins.

TIMING. Local time == song time. Every time below comes from film/timeline.json (lines s0_l1..10,
beats s0_*) and film/assets/song/song_timing.json (word times, strokes, beats, chords, marks); the
numbers in brackets are today's values, for reading only -- the code never hard-codes them.

SHOT LIST (one continuous camera inside the nook, two cuts at musical seams):

 A1  THE NOOK, PUSH PAST THE CANDLE  0 -> s0_bookopen [2.86]. Fade up from black on a near candle
     flame (a fat beeswax pillar close to the lens at frame left, soft focus: the first light of the
     film). Slow dolly forward past it (its own plane, parallax 2.4: it sweeps out of frame left)
     toward the great closed book on its carved lectern, the gilt title THE STONE AND THE BREAD
     catching a sweep of candle sheen. Frame left of centre:
     the bard on his milking stool in 3/4, head cocked, tuning a peg and listening (the tuning
     strokes), then the run and the flourish [2.56] -- eyes to the book first, the head follows.
     Centre: an empty stool on the rug (it is ours; it pays off on "pull up a stool"). Eye-trace:
     candle flame -> gilt title -> bard -> back to the book.
 A2  THE BOOK CREAKS OPEN  s0_bookopen [2.86] -> s0_l1 "in" [5.84]. The cover swings over, the
     pages flutter and settle (the last one lands carrying the drop-cap page), a puff of gold motes
     and a bloom of warm light off the parchment. The bard, delighted, turns to US, draws a breath
     on the vamp and sings "Once upon a time," straight to camera (we see the singer start). The
     camera keeps creeping in (zoom ~1.44 -> 1.56), holding bard + book as a two-shot.
 A3  THE DIVE  "in a kingdom of stone" [5.7 -> 7.1]. The camera swoops into the right-hand page
     and lands inside the painted castle on "STONE" (the bard sweeps out of frame left in one clean
     move during the fast middle of the ease). The castle's windows light one by one on "kingdom".
 A4  INSIDE THE PAGE (verse 1)  [7.1 -> "pane" 16.74]. Book of Kells / Cartoon Saloon painting:
     gold-leaf moon and stars, Kells cloud-curls, indigo->peach dusk. "Lived a town full of folk":
     tilt down the hill to a street of half-timbered houses; lone silhouettes appear in lamplit
     windows ("living alone"), two folk cross without a word (one turns his face away).
     "potions for sleeping": potions glint on the sills, one window sips and yawns ink z's;
     "charms for the rain": rune charms swing, painted rain begins, the folk hurry home.
     "And a LOCK on each heart": push in as the doors slam shut (ink impact strokes), heart-shaped
     lock plates bolt and glint on "heart"; "and a LATCH on each pane": tilt up as the shutters
     swing shut and latch one after another (all six before "pane"), lamplight leaking between
     the slats. The street's ground stays above y ~880 so the action clears the caption band.
 B   THE LONG NOTE  cut on "paaane" [16.74] -> s0_l5 [18.59]. Wide two-shot: the bard holds the
     note eyes closed (rapture), opens them, and watches the page turn ITSELF on the interlude
     downbeat [17.595] -- the book is alive. A breath between verses.
 C1  THE DRAGON'S PAGE (verse 2)  cut on "Now" [18.59]. Close on the left picture: the dragon --
     on-model, the real rig painted in (slate-teal, charcoal-navy coat, mustard scarf) -- alone on
     a dusk street, the verse writing itself above him. Push in for "with a scarf and a SIGH" (a
     curl of grey smoke), "And he WAVED at his neighbours" (an eager, hopeful wave), ease back for
     "who HURRIED on by" (goblin, kobold and mouse-folk hurry past heads down, one glances and
     speeds up; the wave sinks).
 C2  THE MARKET  "Every merchant in town" [25.3]: glide right to the stalls STONES / POTIONS /
     CANDLES (painted signs). On "STONE" the goblin hoists a rune-stone that flares cold; on
     "sell" the dwarf and kobold hold up a sleeping draught and a spell-candle. "But for what he
     was missing": pull back to the whole spread -- the merchants hold their cold, glowing wares out
     across the gutter, the cold light spilling onto the dragon's page; "there wasn't a spell":
     they lower them and shrug; the dragon turns away, head down, a smaller sigh.
     The verse is written in at the TOP of each page (as it is sung) so the deep shots keep the
     caption band clear of page lettering (no text on text).
 C3  THE PULL-BACK  "spell" [31.28] -> s0_l9 [32.67]. Out of the book in one ease, back to the
     nook; on coda_look_up [31.38] the bard lifts his eyes to the lens; the page turns on the
     lute's break [32.19] to the coda spread (the empty-stool vignette, the stone and the loaf).
 C4  THE INVITATION  "So pull up a STOOL" -- push in on the bard: a glance and a nod at the empty
     stool beside him, eyes back to us on "FRIEND", a sly smile, and the WINK on "and hear HOW
     it's said" (a gold "ting!" at his eye). "How a kingdom of stone" -- he turns back to the book;
     the camera eases out to the two-shot.
 C5  BACK TO BREAD  the page turns on "BREAD" [38.94]: the leaf passes vertical while the bard
     holds "breeead" eyes closed, and lands on the final chord [39.77]; push into the wash-house
     picture (cold teal windows, the small dragon trudging to the
     door with his laundry sack; the lectern candle slides out of frame as we enter the picture):
     he reaches the door, it swings open spilling cold wisp-light on him, he steps into it -- and
     the picture fades to black over s0_out [41.97 -> 43.17]. S1 fades up inside.

ACTING (thought -> glance -> breath -> line). Eyes lead, head 0.15-0.25 s later, body last.
 - Tuning: head cocked toward the pegbox, eyes half-lidded, listening; a pleased little nod when
   the string comes true (the harmonics). Flourish: eyes flick to the book, then the head.
 - Before "Once": a look to camera on the vamp, an inhale (beak closed, chest up), then sing.
 - Long notes ("pane", "spell", "bread"): eyes close, brows lift, head tips up (rapture).
 - The coda: "pull up a stool" -- eyes to the stool, head nod toward it, back to us on "friend";
   "hear HOW" -- the wink; "kingdom of stone" -- eyes return to the book (he's reading it to us).
 - The music drives the body: strum hand hits on every stroke time (anticipation, 75 ms sweep,
   follow-through), the fret hand slides to each chord change (all on beats; most on
   downbeats), head bob + left-boot tap on the beat grid, groove by section. Beak from the
   vocal envelope timeline.talk(0, t, "BARD") (no voiceover lines in S0), vowel shapes from the
   syllables; the beak is shut through the intro, interlude, break and outro.

COLOR / VALUE. Dominant warm amber (candle) over deep plum-brown darks; one cool accent (the
moonlit window and a faint blue-violet moon shaft across the back wall) so the warm reads warm.
The room's falloff is baked into cached light maps round the real flame positions and laid over
the set and the actors alike, so the lectern foot, the stools and his boots sink into the dark. Klaus lighting on the bard: warm key from the
lectern candles (screen right), hearth-orange rim from the left, a big soft cast shadow of him
playing along on the stone wall. The subject is always the brightest, most contrasted area: in
A1 the candle flame and the gilt title; in A2 the opened pages; in B/C3-C5 the bard's face and the
pages. Inside the book: the painted pages' own palettes (dusk indigo/peach, cold teal for the
stones and the wash-house) under a gentle candle wash; gold leaf glints as the light and camera
move (small burnished specular slides, not lens stars). Grain 3.5 %, plum vignette.

PERIOD. Stone walls, a hearth, beeswax candles in iron prickets, a carved oak lectern, a frame drum
and recorder on wall pegs, a moonlit leaded window, a woven rug, a stack of old books; storybook
lettering only (IM FELL, Uncial). Inside the pages: half-timbered houses, iron lanterns, market
awnings, painted signs. Nothing modern; nobody human (goblins, kobolds, elves, mouse- and
hare-folk, a dwarf, the dragon, the cockatrice).

SOUND (SFX_CUES at the bottom, computed from the same event times): the near flame, the cover's
creak + landing + page flutter, the painted doors' muffled slams, six shutter latches, three page
turns, the rune-stone's flare, the wink's chime, the wash-house door opening.
"""

import math
import random

import cairocffi as cairo

from film.lib import core, fx
from film.lib import storybook as sb
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.core import clamp, lerp, smooth
from film.scenes import _s0_pages as PG

SCENE = 0
W, H = core.W, core.H
TAU = math.tau
L_CANDLE = sb.STORY_LIGHT
# the bard's own light: the lectern candle burns right beside his head (a near-horizontal warm key
# from screen right), the hearth rims him hot orange from the left
L_BARD = L_CANDLE.with_(direction=(0.9, -0.42), rim=(1.0, 0.6, 0.28), rim_strength=1.45,
                        rim_direction=(-0.9, -0.42))

# ----------------------------------------------------------------------------------------
# timing: everything derives from timeline.json beats/lines and the song's own word times
# ----------------------------------------------------------------------------------------
DUR = tl.scene(SCENE).duration
SONG = PG.SONG
T_FLOURISH = tl.beat("s0_flourish").t
T_OPEN = tl.beat("s0_bookopen").t
T_VAMP = tl.beat("s0_vamp").t
T_TURN1 = tl.beat("s0_page_turn_v2").t
T_LOOKUP = tl.beat("s0_coda_look_up").t
T_BREAK = tl.beat("s0_break").t
T_FINAL = tl.beat("s0_final_chord").t
_OUT = tl.beat("s0_out")
T_OUT0, T_OUT1 = _OUT.t, (_OUT.end if _OUT.end is not None else DUR)
_OPEN_B = tl.beat("s0_open")
T_FADEIN = _OPEN_B.end if _OPEN_B.end is not None else 2.0
LN = {k: tl.line(f"s0_l{k}") for k in range(1, 11)}


def wt(k, word, nth=0):
    """Sung start time of `word` in lyric line k (song_timing.json), falling back to the line start."""
    return SONG.at(f"s0_l{k}", word, nth, LN[k].start)


OPEN_DUR = 1.3                                   # open 0 -> 1 (the cover lands at 0.45 of it)
T_COVER_LAND = T_OPEN + 0.45 * OPEN_DUR
TURN_DUR = 0.85
T_TURN2 = T_BREAK                                # verse 2 -> the coda spread, on the lute's roll as we pull out
T_TURN3 = wt(10, "bread")                         # "...back to BREAD": the page turns to the wash-house
TURN3_DUR = max(0.6, T_FINAL - T_TURN3)          # ...and lands with the final chord
T_CUT_B = wt(4, "pane")                           # cut to the bard on his long note
T_CUT_C = LN[5].start                             # cut back into the book: "Now a dragon..."
T_WINK = wt(9, "how")                             # "...and hear HOW it's said"
T_STOOL = wt(9, "stool")
T_FRIEND = wt(9, "friend")

EV = dict(castle_lights=wt(1, "kingdom"), folk_walk=wt(2, "Lived"), cross=wt(2, "alone"), alone=wt(2, "who"),
          potions=wt(3, "potions"), sleeping=wt(3, "sleeping"), charms=wt(3, "charms"), rain=wt(3, "the") - 0.1,
          lock=wt(4, "lock"), heart=wt(4, "heart"), latch=wt(4, "latch"), pane=wt(4, "pane"),
          sigh=wt(5, "sigh"), wave=wt(6, "waved"), neighbours=wt(6, "neighbours"), hurried=wt(6, "hurried"),
          by=wt(6, "by"), stone=wt(7, "stone"), sell=wt(7, "sell"), but=wt(8, "But"), missing=wt(8, "missing"),
          wasnt=wt(8, "wasn't"), spell=wt(8, "spell"), wash_walk=T_TURN3 - 0.4, wash_door=DUR - 1.05)

# ----------------------------------------------------------------------------------------
# the set (world px at zoom 1; y down). The nook: stone wall, hearth (left, off the frame's
# edge in most shots), the bard on his stool, the lectern + great book, an empty stool "for you".
# ----------------------------------------------------------------------------------------
WALL_Y = 800.0
BARD_X, BARD_Y, BARD_SC = 800.0, 985.0, 3.0
LECT_X, LECT_Y, LECT_SC, LECT_HT = 1330.0, 930.0, 1.55, 230.0
DESK = (LECT_X, LECT_Y - LECT_HT * LECT_SC)
HEARTH_X, HEARTH_SC = 205.0, 1.45
WIN_X, WIN_Y, WIN_W, WIN_H = 1700.0, 150.0, 150.0, 250.0
STOOL_X, STOOL_Y = 1068.0, 968.0                  # the empty stool (pull up a stool, friend)
STACK_X, STACK_Y = 1740.0, 1004.0                 # old books + a candle stub (right)
FG_CANDLE = (886.5, 782.9)                        # the near candle's flame (on its own plane, parallax FG_P)
FG_P = 2.4                                        # close to the lens: it sweeps out of frame left as we push in
WALL_P = 0.95
SHADOW_K = 1.5                                    # the bard's wall shadow: x his size, about the candle
WALL = {"stone_a": "#5a443a", "stone_b": "#46352f", "mortar": "#1f1617", "beam": "#33231a",
        "floor_hi": "#5b3f2c", "floor_lo": "#24170f"}
M = dict(w=2400, h=1500, x=-240, y=-200)          # cached-layer margin (camera moves never show an edge)

VIEW_WIDE, VIEW_BOOK = 0.55, 0.24                 # the desk angle: wide shots / pushed into the page
GILT = {}                                         # id(page) -> gilt polylines (page units)

# the room's light sources (world px), filled in by setup() from the lectern / hearth rigs
SRC = {"cand_l": (1042.0, 640.0), "cand_r": (1618.0, 640.0), "fire": (205.0, 784.0),
       "stack": (1750.0, 850.0), "moon": (1796.0, 234.0)}
DARK = "#0a0510"                                  # the nook's darkness: deep plum-violet, never grey
CANDLE_C, HEARTH_C, MOON_C = "#ff9440", "#ff6a24", "#7f9cf0"


def light_map(cr, rect, dark_a, holes, washes):
    """Paint the room's static light onto a cached layer: darken everything in `rect` toward DARK
    (alpha dark_a) except soft pools round the light sources (holes: [(x, y, r, k, squash)]: k is
    how much darkness the pool lifts), then wash the pools with their light's colour (washes:
    [(x, y, r, colour, alpha, squash)], additive). One-off cost (setup)."""
    x0, y0, w, h = rect
    cr.push_group()
    core.src(cr, DARK, dark_a)
    cr.rectangle(x0, y0, w, h)
    cr.fill()
    cr.set_operator(cairo.OPERATOR_DEST_OUT)
    for (x, y, r, k, sq) in holes:
        cr.save()
        cr.translate(x, y)
        cr.scale(1.0, sq)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, r)
        for off, f in ((0.0, 1.0), (0.18, 0.92), (0.4, 0.62), (0.65, 0.28), (0.85, 0.08), (1.0, 0.0)):
            g.add_color_stop_rgba(off, 0, 0, 0, k * f)
        cr.set_source(g)
        cr.paint()
        cr.restore()
    cr.pop_group_to_source()
    cr.paint()
    for (x, y, r, c, a, sq) in washes:
        cr.save()
        cr.translate(x, y)
        cr.scale(1.0, sq)
        fx.glow(cr, 0.0, 0.0, r, c, a)
        cr.restore()


# ----------------------------------------------------------------------------------------
# the nook's static art (cached once in setup)
# ----------------------------------------------------------------------------------------

def _stone_wall(cr, x0, y0, x1, y1, seed, rows=(54, 70)):
    rng = random.Random(seed)
    core.src(cr, WALL["mortar"])
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.fill()
    y, row = y0, 0
    while y < y1:
        hgt = rng.uniform(*rows)
        x = x0 - rng.random() * 80 - (row % 2) * 45
        while x < x1:
            w = rng.uniform(90, 170)
            tone = core.mix(WALL["stone_a"], WALL["stone_b"], rng.random())
            tone = core.mix(tone, "#6a5244", 0.25 * rng.random())
            pts = [(x + 5 + rng.uniform(-2, 2), y + 5 + rng.uniform(-2, 2)), (x + w - 5 + rng.uniform(-2, 2), y + 4 + rng.uniform(-2, 2)),
                   (x + w - 4 + rng.uniform(-2, 2), y + hgt - 5 + rng.uniform(-2, 2)), (x + 4 + rng.uniform(-2, 2), y + hgt - 4 + rng.uniform(-2, 2))]
            cr.new_path()
            core.smooth_closed(cr, pts, 0.35)
            sp = B.Path(cr)
            sp.add(cr)
            core.src(cr, tone)
            cr.fill()
            cr.save()
            sp.add(cr)
            cr.clip()
            cr.set_source(core.linear(0, y, 0, y + hgt, [(0.0, (1.0, 0.86, 0.66, 0.10)), (0.25, (1, 1, 1, 0.0)),
                                                         (0.8, (0, 0, 0, 0.0)), (1.0, (0, 0, 0, 0.28))]))
            cr.paint()
            for _ in range(2):
                sb._bloom(cr, rng.uniform(x, x + w), rng.uniform(y, y + hgt), rng.uniform(10, 26), "#000000", 0.08)
            cr.restore()
            x += w
        y += hgt
        row += 1


def _wall_music(cr, x, y):
    """The bard's frame drum and recorder hung on two wall pegs (the song's other instruments)."""
    for px, py in ((x, y), (x + 120, y + 14)):
        core.src(cr, "#140d0a", 0.5)
        core.circle(cr, px + 3, py + 4, 7.5)
        cr.fill()
        core.src(cr, "#3a2618")
        core.circle(cr, px, py, 6.5)
        cr.fill()
    dx, dy, r = x, y + 76, 50.0
    core.src(cr, "#5e3c26", 0.95)
    cr.set_line_width(2.2)
    cr.move_to(x - 2, y + 4)
    cr.line_to(dx - 16, dy - r + 3)
    cr.move_to(x + 2, y + 4)
    cr.line_to(dx + 16, dy - r + 3)
    cr.stroke()
    core.src(cr, "#140d0a", 0.45)
    core.circle(cr, dx + 7, dy + 9, r + 2)
    cr.fill()
    core.src(cr, "#7a4c2a")
    core.circle(cr, dx, dy, r)
    cr.fill()
    cr.set_source(core.radial(dx - 12, dy - 14, r * 0.95, ["#eedcae", "#d9bf86", "#b8975e"]))
    core.circle(cr, dx, dy, r - 7.0)
    cr.fill()
    for k in range(4):
        a = 0.4 + k * TAU / 4
        jx, jy = dx + math.cos(a) * (r - 3.5), dy + math.sin(a) * (r - 3.5)
        core.src(cr, "#3a2416")
        cr.rectangle(jx - 6, jy - 3, 12, 6)
        cr.fill()
        core.src(cr, "#d9b45a")
        core.circle(cr, jx, jy, 3.4)
        cr.fill()
    rx_, ry_ = x + 120, y + 14
    core.src(cr, "#5e3c26", 0.95)
    cr.set_line_width(2.0)
    cr.move_to(rx_, ry_ + 3)
    cr.line_to(rx_ + 4, ry_ + 22)
    cr.stroke()
    cr.save()
    cr.translate(rx_ + 4, ry_ + 22)
    cr.rotate(-0.12)
    core.src(cr, "#140d0a", 0.45)
    core.rounded_rect(cr, 1.0, 6.0, 14.0, 172.0, 7.0)
    cr.fill()
    cr.set_source(core.linear(-7.0, 0, 7.0, 0, ["#7d4e28", "#c8945a", "#8a5a30"]))
    cr.new_path()
    core.tapered(cr, [(0.0, 0.0), (0.0, 168.0)], 13.0, 10.0)
    cr.fill()
    cr.set_source(core.linear(-7.0, 0, 7.0, 0, ["#5e3a20", "#8a5a30", "#5e3a20"]))
    core.rounded_rect(cr, -7.5, -2.0, 15.0, 16.0, 4.0)
    cr.fill()
    core.rounded_rect(cr, -7.0, 150.0, 14.0, 20.0, 4.0)
    cr.fill()
    core.src(cr, "#2a160c")
    cr.rectangle(-4.0, 16.0, 8.0, 3.0)
    cr.fill()
    for k in range(7):
        core.circle(cr, 0.0, 52.0 + k * 13.0, 2.3)
        cr.fill()
    cr.restore()


def _window(cr):
    wx, wy, ww, wh = WIN_X, WIN_Y, WIN_W, WIN_H
    cr.new_path()
    cr.move_to(wx, wy + wh)
    cr.line_to(wx, wy + ww / 2)
    cr.arc(wx + ww / 2, wy + ww / 2, ww / 2, math.pi, 2 * math.pi)
    cr.line_to(wx + ww, wy + wh)
    cr.close_path()
    win = B.Path(cr)
    core.src(cr, "#1a1414")
    cr.set_line_width(26)
    win.add(cr)
    cr.stroke()
    win.add(cr)
    cr.set_source(core.linear(0, wy, 0, wy + wh, ["#26386a", "#132040"]))
    cr.fill()
    cr.save()
    win.add(cr)
    cr.clip()
    fx.glow(cr, wx + 96, wy + 84, 150, "#9db8f0", 0.45)
    core.src(cr, "#e6eeff", 0.9)
    core.circle(cr, wx + 96, wy + 84, 20)
    cr.fill()
    core.src(cr, "#140e10", 0.95)
    cr.rectangle(wx + ww / 2 - 4, wy, 8, wh)
    for k in range(1, 4):
        cr.rectangle(wx, wy + ww / 2 + k * (wh - ww / 2) / 4 - 3, ww, 6)
    cr.fill()
    cr.restore()
    core.src(cr, "#3b2c26")
    cr.rectangle(wx - 30, wy + wh, ww + 60, 22)
    cr.fill()


def _rug(cr, cx, cy, rx, ry):
    cr.save()
    cr.translate(cx, cy)
    cr.scale(1.0, ry / rx)
    core.src(cr, "#d8c08a", 0.55)
    for k in range(90):
        a = TAU * k / 90
        cr.move_to(math.cos(a) * rx * 0.99, math.sin(a) * rx * 0.99)
        cr.line_to(math.cos(a) * rx * 1.05, math.sin(a) * rx * 1.05)
    cr.set_line_width(3.0)
    cr.stroke()
    for r, c in ((rx, "#4a1a1f"), (rx * 0.95, "#8e2a2a"), (rx * 0.83, "#c09040"), (rx * 0.80, "#25304e")):
        cr.new_path()
        cr.arc(0, 0, r, 0, TAU)
        core.src(cr, c)
        cr.fill()
    core.src(cr, "#d8b060")
    for k in range(30):
        a = TAU * (k + 0.5) / 30
        mx, my = math.cos(a) * rx * 0.89, math.sin(a) * rx * 0.89
        tx, ty = -math.sin(a), math.cos(a)
        cr.move_to(mx + tx * 14, my + ty * 14)
        cr.line_to(mx + math.cos(a) * 9, my + math.sin(a) * 9)
        cr.line_to(mx - tx * 14, my - ty * 14)
        cr.line_to(mx - math.cos(a) * 9, my - math.sin(a) * 9)
        cr.close_path()
    cr.fill()
    for (sx, c) in ((rx * 0.42, "#c09040"), (rx * 0.37, "#8e2a2a"), (rx * 0.2, "#25304e")):
        cr.move_to(-sx * 1.5, 0)
        cr.line_to(0, -sx)
        cr.line_to(sx * 1.5, 0)
        cr.line_to(0, sx)
        cr.close_path()
        core.src(cr, c)
        cr.fill()
    cr.restore()


def _book_stack(cr, x, y):
    rng = random.Random(8)
    core.src(cr, "#000000", 0.35)
    core.ellipse(cr, x + 8, y + 4, 128, 16)
    cr.fill()
    yy = y
    for k, (w, h, c) in enumerate(((214, 38, "#5a2a20"), (190, 32, "#2e4038"), (200, 36, "#6a4224"))):
        dx = rng.uniform(-14, 14)
        x0 = x - w / 2 + dx
        cr.save()
        cr.translate(x0 + w / 2, yy - h / 2)
        cr.rotate(rng.uniform(-0.025, 0.025))
        core.src(cr, core.mix(c, "#000000", 0.25))
        core.rounded_rect(cr, -w / 2, -h / 2, w, h, 6)
        cr.fill()
        core.src(cr, c)
        core.rounded_rect(cr, -w / 2, -h / 2, w, h * 0.28, 4)
        core.rounded_rect(cr, -w / 2, h / 2 - h * 0.26, w, h * 0.26, 4)
        cr.fill()
        core.src(cr, "#cdb98c")
        cr.rectangle(-w / 2 + 10, -h / 2 + h * 0.3, w - 34, h * 0.42)
        cr.fill()
        core.src(cr, "#9a8460", 0.5)
        for j in range(3):
            cr.rectangle(-w / 2 + 10, -h / 2 + h * (0.36 + j * 0.11), w - 34, 1.0)
        cr.fill()
        core.src(cr, core.mix(c, "#000000", 0.1))
        core.rounded_rect(cr, w / 2 - 26, -h / 2, 26, h, 9)
        cr.fill()
        core.src(cr, "#c8a050", 0.85)
        for bx in (w / 2 - 19, w / 2 - 9):
            cr.rectangle(bx, -h / 2 + 3, 2.5, h - 6)
        cr.fill()
        cr.restore()
        yy -= h
    return (x, yy)


def draw_wall(cr, store):
    """The back wall plane (parallax WALL_P): stone, ceiling beam, hearth, mantel, the drum and
    recorder on their pegs, the night window; the painted light falloff."""
    _stone_wall(cr, -260, -220, W + 260, WALL_Y + 8, 4)
    core.src(cr, WALL["beam"])
    cr.rectangle(-260, -220, W + 520, 260)
    cr.fill()
    cr.set_source_rgba(1, 0.8, 0.6, 0.07)
    cr.rectangle(-260, 36, W + 520, 4)
    cr.fill()
    hr = sb.draw_hearth(cr, HEARTH_X, WALL_Y + 22, HEARTH_SC, L_CANDLE, seed=1)
    store["hearth"] = hr
    SRC["fire"] = hr.fire
    mx, my = hr.mantel
    core.src(cr, "#7a4a30")
    cr.new_path()
    core.smooth_closed(cr, [(mx - 120, my), (mx - 128, my - 30), (mx - 118, my - 52), (mx - 106, my - 54), (mx - 96, my - 32),
                            (mx - 102, my)], 0.8)
    cr.fill()
    for (bx, bw, bh, c) in ((mx + 70, 22, 64, "#3c4a3a"), (mx + 94, 18, 56, "#6a2a22")):
        core.src(cr, c)
        cr.rectangle(bx, my - bh, bw, bh)
        cr.fill()
        core.src(cr, "#c8a050", 0.6)
        cr.rectangle(bx + 2, my - bh + 10, bw - 4, 3)
        cr.rectangle(bx + 2, my - 14, bw - 4, 3)
        cr.fill()
    _wall_music(cr, 950, 250)
    _window(cr)
    # the ceiling falls away into darkness above the candles
    cr.set_source(core.linear(0, -220, 0, 560, [(0.0, (0.03, 0.01, 0.02, 0.9)), (1.0, (0.03, 0.01, 0.02, 0.0))]))
    cr.rectangle(-260, -220, W + 520, 780)
    cr.fill()
    # the light: pools round the candles, the book, the hearth and the moonlit window
    (clx, cly), (crx, cry) = SRC["cand_l"], SRC["cand_r"]
    hx, hy = hr.fire
    sx_, sy_ = SRC["stack"]
    mx_, my_ = SRC["moon"]
    shx, shy = clx + (BARD_X - 10.0 - clx) * SHADOW_K, cly + (600.0 - cly) * SHADOW_K
    light_map(cr, (-260, -220, W + 520, H + 440), 0.62,
              holes=[(shx + 40, shy + 10, 380, 0.8, 1.15), (clx, cly, 480, 0.92, 1.0), (crx, cry, 440, 0.88, 1.0), ((clx + crx) / 2, cly - 30, 400, 0.6, 0.9),
                     (hx + 40, hy - 90, 840, 0.92, 0.8), (sx_, sy_, 300, 0.6, 1.0), (BARD_X + 60, 690, 300, 0.32, 1.1),
                     (mx_, my_ + 30, 210, 0.6, 1.2)],
              washes=[(shx + 40, shy + 10, 360, CANDLE_C, 0.1, 1.15), (clx, cly, 460, CANDLE_C, 0.13, 1.0),
                      (crx, cry, 420, CANDLE_C, 0.11, 1.0),
                      (hx + 30, hy - 80, 780, HEARTH_C, 0.2, 0.8), (sx_, sy_, 260, CANDLE_C, 0.08, 1.0),
                      (mx_, my_ + 20, 240, MOON_C, 0.12, 1.2)])


def draw_floor(cr, store):
    """The floor plane (parallax 1, the actors' plane): planks running toward us, the rug, the
    book stack."""
    core.vgrad(cr, -260, WALL_Y, W + 520, H - WALL_Y + 300, [WALL["floor_hi"], WALL["floor_lo"]])
    cr.set_source_rgba(0, 0, 0, 0.32)
    for k in range(-22, 24):
        cr.move_to(960 + k * 44, WALL_Y)
        cr.line_to(960 + k * 150, H + 260)
    cr.set_line_width(2.0)
    cr.stroke()
    cr.set_source(core.linear(0, WALL_Y - 6, 0, WALL_Y + 34, [(0, (0, 0, 0, 0.6)), (1, (0, 0, 0, 0))]))
    cr.rectangle(-260, WALL_Y - 6, W + 520, 40)
    cr.fill()
    _rug(cr, BARD_X + 120, BARD_Y + 10, 360, 74)
    store["stack_top"] = _book_stack(cr, STACK_X, STACK_Y)
    # the floor falls into darkness away from the candles (pools squashed into floor perspective)
    (clx, _), (crx, _) = SRC["cand_l"], SRC["cand_r"]
    hx = SRC["fire"][0]
    light_map(cr, (-260, WALL_Y - 10, W + 520, H), 0.6,
              holes=[((clx + crx) / 2, LECT_Y, 620, 0.85, 0.3), (BARD_X + 80, BARD_Y, 520, 0.8, 0.32),
                     (hx + 80, WALL_Y + 60, 760, 0.88, 0.36), (STACK_X, STACK_Y - 20, 340, 0.62, 0.35)],
              washes=[((clx + crx) / 2, LECT_Y - 10, 600, CANDLE_C, 0.11, 0.3), (BARD_X + 80, BARD_Y, 480, CANDLE_C, 0.09, 0.3),
                      (hx + 120, WALL_Y + 70, 820, HEARTH_C, 0.14, 0.34)])


def draw_room_shade(cr):
    """The room's light falloff as one world-anchored darkness field, painted OVER the set AND the
    actors (lectern column, stools, the bard's legs) so everything falls off with its distance from
    the flames: candle-height things glow, the floor and the corners sink into plum dark."""
    (clx, cly), (crx, cry) = SRC["cand_l"], SRC["cand_r"]
    hx, hy = SRC["fire"]
    sx_, sy_ = SRC["stack"]
    light_map(cr, (-260, -220, W + 520, H + 440), 0.62,
              holes=[(clx, cly, 520, 1.0, 1.0), (crx, cry, 470, 1.0, 1.0), ((clx + crx) / 2, cly - 40, 420, 1.0, 0.85),
                     (clx + (BARD_X - 10.0 - clx) * SHADOW_K + 40, cly + (600.0 - cly) * SHADOW_K, 360, 0.65, 1.15),
                     (BARD_X + 70, cly + 20, 380, 0.75, 1.0), (hx + 120, hy - 60, 900, 0.7, 0.8),
                     (sx_, sy_, 300, 0.8, 1.0)],
              washes=[])


def draw_fg_candle(cr):
    """The near candle (its own plane, parallax FG_P, cached and blurred = out of focus): a fat
    beeswax pillar on an iron pricket whose stem runs out of the bottom of frame. Seen against the
    room it is a dark warm silhouette -- except its crown, where the wax glows translucent round
    the wick, and an orange rim from the hearth down its left side. The flame is drawn per frame."""
    x, y = FG_CANDLE
    top = y + 16.0                                  # the wax rim
    w, h = 76.0, 210.0
    iron = "#160d0b"
    # the pricket: a stem out of frame, a drip dish, a collar
    core.src(cr, iron)
    core.rounded_rect(cr, x - 9.0, top + h - 6.0, 18.0, 520.0, 7.0)
    cr.fill()
    cr.new_path()
    core.ellipse(cr, x, top + h + 6.0, 70.0, 15.0)
    cr.fill()
    core.rounded_rect(cr, x - 44.0, top + h - 8.0, 88.0, 20.0, 9.0)
    cr.fill()
    # the wax body: dark, a little warmer toward the lit crown
    body = [(x - w / 2, top + 6.0), (x - w / 2 + 1.0, top + h), (x + w / 2 - 1.0, top + h), (x + w / 2, top + 4.0)]
    cr.new_path()
    core.smooth_closed(cr, body, 0.15)
    bp = B.Path(cr)
    cr.set_source(core.linear(0, top, 0, top + h, [(0.0, "#7a4a24"), (0.22, "#3a2214"), (1.0, "#1c100b")]))
    cr.fill()
    cr.save()
    bp.add(cr)
    cr.clip()
    # translucent crown: the flame lights the wax from inside
    cr.set_source(core.radial(x, top - 4.0, 88.0, [(0.0, (1.0, 0.86, 0.52, 0.95)), (0.45, (1.0, 0.62, 0.26, 0.55)),
                                                     (1.0, (1.0, 0.5, 0.2, 0.0))]))
    cr.paint()
    # the hearth's rim down the left edge
    cr.set_source(core.linear(x - w / 2, 0, x - w / 2 + 16.0, 0, [(0.0, (1.0, 0.52, 0.2, 0.55)), (1.0, (1.0, 0.5, 0.2, 0.0))]))
    cr.rectangle(x - w / 2, top, 16.0, h)
    cr.fill()
    cr.restore()
    # drips down the side
    core.src(cr, "#8a5a2c", 0.9)
    for dx_, dl in ((-24.0, 54.0), (-6.0, 30.0), (14.0, 76.0), (27.0, 38.0)):
        core.rounded_rect(cr, x + dx_ - 4.0, top + 2.0, 8.0, dl, 4.0)
        cr.fill()
    # the wax pool on top (lit)
    cr.new_path()
    core.ellipse(cr, x, top + 4.0, w / 2 - 3.0, 8.0)
    core.src(cr, "#ffd89a", 0.95)
    cr.fill()
    # the wick stub
    core.src(cr, "#2a1608")
    cr.rectangle(x - 1.6, top - 9.0, 3.2, 12.0)
    cr.fill()


def fg_flame(cr, x, y, s, t, alpha=1.0):
    """The near candle's flame at screen (x, y) (its base), s = on-screen scale: a soft teardrop
    (blue root, gold body, white heart) that flickers, leans and stretches with candle_flicker."""
    b, sway, stretch = sb.candle_flicker(t, 9)
    hgt = 46.0 * s * stretch
    wid = 15.0 * s
    lean = 5.0 * s * sway
    tip = (x + lean, y - hgt)

    def tear(k, dy=0.0):
        return [(x - wid * k, y - hgt * 0.28 * k + dy), (x - wid * 0.62 * k + lean * 0.4, y - hgt * 0.62 * k + dy),
                (tip[0] * k + x * (1 - k), y - hgt * k + dy), (x + wid * 0.62 * k + lean * 0.4, y - hgt * 0.62 * k + dy),
                (x + wid * k, y - hgt * 0.28 * k + dy), (x, y + wid * 0.55 * k + dy)]
    fx.glow(cr, x + lean * 0.5, y - hgt * 0.45, 70.0 * s * b, "#ffb455", 0.55 * alpha)
    for k, c, a in ((1.0, "#ff9a3c", 0.85), (0.74, "#ffd27a", 0.95), (0.46, "#fff3d0", 1.0)):
        cr.new_path()
        core.smooth_closed(cr, tear(k, -hgt * 0.04 * (1 - k)), 0.6)
        core.src(cr, c, a * alpha)
        cr.fill()
    cr.new_path()
    core.ellipse(cr, x, y - hgt * 0.06, wid * 0.42, wid * 0.32)
    core.src(cr, "#5a78ff", 0.45 * alpha)
    cr.fill()


# ----------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------

def view_for_zoom(z):
    """The desk angle follows the camera: the further we push in, the more face-on the page
    (the camera rises over the book as it dives into it)."""
    return lerp(VIEW_WIDE, VIEW_BOOK, smooth((z - 1.95) / (3.9 - 1.95)))


def page_world(side, u, v, view):
    """World point of page fraction (u, v) on the open book's left/right page at `view` (the same
    affine map storybook.draw_book uses for an open page lying on its block)."""
    book_w, book_h, T = 150.0, 200.0, 12.0
    cv, sv = math.cos(view), math.sin(view)
    x0 = 0.8 if side == "right" else -0.8 - book_w
    px = x0 + u * book_w
    py = v * book_h * cv - book_h / 2.0 * cv - T * sv
    return DESK[0] + LECT_SC * px, DESK[1] + LECT_SC * py


def Wk(x, y, z):
    return ("w", x, y, z)


def Pk(side, u, v, dev):
    return ("p", side, u, v, dev)


def _resolve(spec):
    if spec[0] == "w":
        return core.Camera(spec[1], spec[2], spec[3])
    _, side, u, v, dev = spec
    z = dev / LECT_SC
    x, y = page_world(side, u, v, view_for_zoom(z))
    return core.Camera(x, y, z)


def _cam_lerp(a, b, u):
    """Interpolate two cameras as a dolly about the one world point both frames agree on (so a
    push-in radiates from its target and never swings); near-equal zooms move linearly."""
    z0, z1 = a.zoom, b.zoom
    if abs(math.log(z1 / z0)) < 0.04:
        return core.Camera(lerp(a.x, b.x, u), lerp(a.y, b.y, u), lerp(z0, z1, u))
    z = z0 * (z1 / z0) ** u
    px = (b.x * z1 - a.x * z0) / (z1 - z0)
    py = (b.y * z1 - a.y * z0) / (z1 - z0)
    return core.Camera(px - (px - a.x) * z0 / z, py - (py - a.y) * z0 / z, z)


# (time, spec, easing into this key). Three shots: A (0 -> T_CUT_B), B (-> T_CUT_C), C (-> end).
SHOT_A = [
    (0.0, Wk(1075, 700, 1.18)),
    (T_OPEN - 0.1, Wk(1118, 688, 1.44), "inout_sine"),          # push past the near candle to the closed book
    (T_COVER_LAND - 0.12, Wk(1124, 684, 1.48), "linear"),        # ...creeping on while the cover swings
    (wt(1, "in") - 0.15, Wk(1140, 676, 1.56), "inout_sine"),     # hold the two-shot: "Once upon a time," to us
    (wt(1, "stone") + 0.1, Pk("right", 0.5, 0.245, 10.4), "inout_cubic"),  # THE DIVE: into the castle on "stone"
    (LN[2].start + 0.35, Pk("right", 0.5, 0.25, 10.5), "linear"),
    (wt(2, "alone"), Pk("right", 0.5, 0.755, 10.8), "inout_sine"),     # tilt down the hill to the town
    (wt(4, "And"), Pk("right", 0.5, 0.775, 11.0), "inout_sine"),        # settle in the street
    (wt(4, "lock") + 0.05, Pk("right", 0.53, 0.8, 13.5), "inout_sine"),  # push in as the doors SLAM on "lock"
    (wt(4, "heart") + 0.2, Pk("right", 0.54, 0.8, 14.2), "linear"),     # creep: the heart-locks bolt and glint
    (wt(4, "latch") - 0.05, Pk("right", 0.5, 0.73, 14.0), "inout_sine"),  # tilt up: the shutters LATCH, one by one
    (T_CUT_B, Pk("right", 0.5, 0.73, 14.4), "linear"),
]
SHOT_B = [
    (T_CUT_B, Wk(1100, 688, 1.5)),                                 # the storyteller again (A2's two-shot)
    (T_CUT_C, Wk(1112, 684, 1.56), "linear"),
]
SHOT_C = [
    (T_CUT_C, Pk("left", 0.98, 0.54, 5.0)),                               # cut to the spread: verse 2 writes itself
    (wt(5, "dragon"), Pk("left", 0.9, 0.55, 5.3), "inout_sine"),          #   at the top, the dragon alone below
    (wt(5, "sigh") - 0.15, Pk("left", 0.47, 0.605, 9.0), "inout_sine"),   # push in on him for "...and a SIGH"
    (wt(6, "waved") + 0.25, Pk("left", 0.47, 0.61, 8.6), "inout_sine"),   # the hopeful wave (verse out of frame)
    (wt(6, "hurried") - 0.1, Pk("left", 0.52, 0.70, 6.8), "inout_sine"),  # ease back: the neighbours hurry by
    (wt(6, "by") + 0.2, Pk("left", 0.53, 0.70, 6.7), "linear"),           #   (the verse above is out of frame)
    (wt(7, "merchant"), Pk("right", 0.47, 0.66, 7.2), "inout_sine"),      # glide to the market: "Every merchant..."
    (wt(7, "stone") - 0.1, Pk("right", 0.3, 0.6, 8.6), "inout_sine"),     # in on the stone-seller for "STONE"
    (wt(7, "sell"), Pk("right", 0.46, 0.66, 7.4), "inout_sine"),          # ...all three hold up their wares
    (wt(8, "wasn't"), Pk("right", -0.02, 0.58, 4.6), "inout_sine"),       # pull back: the dragon AND the stalls
    (LN[9].start + 0.15, Wk(1062, 742, 1.45), "inout_sine"),              # out of the book, back to the bard
    (T_WINK - 0.15, Wk(872, 772, 2.15), "inout_sine"),                    # push in on him: the stool, the wink
    (LN[9].end + 0.1, Wk(874, 770, 2.2), "linear"),
    (T_TURN3 - 0.4, Wk(1095, 690, 1.62), "inout_sine"),                   # ease back: him and the book
    (T_FINAL + 0.1, Wk(1108, 682, 1.67), "inout_sine"),                   # the page turns, the final chord
    (T_OUT0 - 0.25, Pk("right", 0.6, 0.66, 7.4), "inout_cubic"),          # push into the wash-house page...
    (DUR, Pk("right", 0.74, 0.82, 16.0), "inout_sine"),                   # ...after him to the door as it goes black
                                                                          #   (the lectern candle slides out right)
]


def camera_at(t):
    keys = SHOT_A if t < T_CUT_B else SHOT_B if t < T_CUT_C else SHOT_C
    if t <= keys[0][0]:
        cam = _resolve(keys[0][1])
    else:
        cam = _resolve(keys[-1][1])
        for i in range(1, len(keys)):
            if t < keys[i][0]:
                k0, k1 = keys[i - 1], keys[i]
                u = core.ease(k1[2] if len(k1) > 2 else "inout_sine", (t - k0[0]) / (k1[0] - k0[0]))
                cam = _cam_lerp(_resolve(k0[1]), _resolve(k1[1]), u)
                break
    # a breathing drift, constant in screen px whatever the zoom
    dx = 2.4 * core.fbm1(t * 0.18, 2, 11) / cam.zoom
    dy = 1.6 * core.fbm1(t * 0.18, 2, 17) / cam.zoom
    return core.Camera(cam.x + dx, cam.y + dy, cam.zoom)


# ----------------------------------------------------------------------------------------
# the book's state: opening, the three page turns
# ----------------------------------------------------------------------------------------

def book_state(t):
    """-> (open, spread, turn)."""
    o = clamp((t - T_OPEN) / OPEN_DUR)
    for (t0, d, k) in ((T_TURN1, TURN_DUR, 0), (T_TURN2, TURN_DUR, 1), (T_TURN3, TURN3_DUR, 2)):
        if t0 <= t < t0 + d:
            return 1.0, k, core.inout_sine((t - t0) / d)
    if t < T_TURN1:
        return o, 0, 0.0
    if t < T_TURN2:
        return 1.0, 1, 0.0
    if t < T_TURN3:
        return 1.0, 2, 0.0
    return 1.0, 3, 0.0


# ----------------------------------------------------------------------------------------
# the bard's staging (the music itself -- strums, chords, beat, singing -- comes from bard_song)
# ----------------------------------------------------------------------------------------

def _bump(t, t0, rise, hold, fall):
    """0 -> 1 -> 0: eases up over `rise` from t0, holds, eases down over `fall`."""
    return smooth((t - t0) / rise) * (1.0 - smooth((t - (t0 + rise + hold)) / fall))


def bard_pose(t):
    """The bard's performance. The MUSIC (strum hand on every stroke, fret hand to each chord, head
    bob + foot tap on the beat grid, groove by section, tuning, vowels, long-note rapture) comes
    from the song timing via bard_song; the beak opens from the vocal envelope in timeline.json
    (timeline.talk(0, t, "BARD")); the ACTING (where he looks, when, and what he feels) is staged
    here, eyes leading the head by ~0.15-0.2 s."""
    song = ch.bard_song(t)
    tune = song.get("tune", 0.0)
    # -- intro: tuning (head cocked, listening), a pleased little nod when the harmonics ring true
    pleased = _bump(t, 1.62, 0.18, 0.12, 0.3)
    # -- the run + flourish: eyes to the book, the head follows; delight as the cover swings open
    eyes_book = smooth((t - 2.25) / 0.18) * (1.0 - smooth((t - 3.5) / 0.2))
    head_book = smooth((t - 2.42) / 0.3) * (1.0 - smooth((t - 3.6) / 0.35))
    delight = _bump(t, T_OPEN - 0.05, 0.25, 0.45, 0.4)
    # -- the vamp: he turns to US (eyes first), sits up and breathes in, then sings the first line
    #    to camera until the camera has dived into the page
    to_us = smooth((t - 3.62) / 0.35) * (1.0 - smooth((t - 6.6) / 0.4))
    inhale = _bump(t, 3.62, 0.25, 0.12, 0.3)
    # -- the long note "paaane": eyes closed (rapture from the song); on the release he opens them
    #    and catches the page turning itself
    watch = smooth((t - (LN[4].end - 0.02)) / 0.22) * (1.0 - smooth((t - (T_CUT_C + 0.2)) / 0.3))
    # -- the coda: up to us on "spell", eyes to the empty stool on "pull up a stool" (a nod at it),
    #    back to us on "friend", the wink on "HOW", then back to the book for the last line
    up = smooth((t - T_LOOKUP) / 0.5)
    stool_eyes = smooth((t - (wt(9, "pull") - 0.12)) / 0.18) * (1.0 - smooth((t - (T_FRIEND - 0.15)) / 0.2))
    stool_head = smooth((t - (wt(9, "pull") + 0.05)) / 0.3) * (1.0 - smooth((t - (T_FRIEND - 0.02)) / 0.3))
    to_book_end = smooth((t - (LN[10].start - 0.1)) / 0.45)
    # singing TO us: the head stays in 3/4 (a full-front beak points down the lens and its gape
    # vanishes), the eyes swing the rest of the way to meet the lens
    gaze = max(to_us * (1.0 - head_book), up * (1.0 - 0.8 * stool_head) * (1.0 - to_book_end))
    look_cam = 0.6 * gaze
    look_x = (0.8 * eyes_book * (1.0 - to_us) + 0.8 * watch + 0.6 * stool_eyes
              + 0.8 * to_book_end * (1.0 - stool_eyes) - 0.32 * gaze)
    look_y = -0.12 * eyes_book + 0.7 * stool_eyes - 0.05 * watch
    head_turn = 0.38 * head_book * (1.0 - to_us) + 0.3 * watch + 0.22 * stool_head + 0.35 * to_book_end
    nod = (0.12 * pleased - 0.3 * math.sin(math.pi * clamp((t - (T_STOOL - 0.2)) / 0.5)) * stool_head
           + 0.16 * inhale + 0.08 * delight)
    # the wink snaps shut on "HOW" and snaps open again (the rig's half-shut wink frame reads as a
    # patch over the eye, and a real wink is that fast anyway)
    wink = 1.0 if T_WINK <= t < T_WINK + 0.42 else 0.0
    # -- the face
    mood, mood2, mix_ = "twinkle", "listen", tune
    if delight > 0.01:
        mood2, mix_ = "happy", 0.7 * delight
    elif watch > 0.01:
        mood2, mix_ = "raised", 0.55 * watch
    if T_FRIEND - 0.1 < t < LN[10].start:
        mood, mood2, mix_ = "warm", "sly", smooth((t - (wt(9, "hear") - 0.1)) / 0.25)
    rap = song.get("rapture", 0.0) * (1.0 - 0.85 * up * (1.0 - to_book_end))
    # the beak: the vocal envelope from the timeline (BARD lines; none are voice-over), with the
    # rig's narrow "e" opened up a touch so every syllable reads
    sing = tl.talk(SCENE, t, "BARD")
    v = (song.get("vowel") or "a")[:1]
    if v in ("e", "i"):
        sing *= 0.8 / 0.55
    elif v == "o":
        sing *= 0.9 / 0.8
    sing = clamp(sing) ** 0.7            # soft singing still opens the beak legibly
    song = dict(song, rapture=rap, sing=sing)
    return ch.BardPose(sit=1.0, facing=1, turn=-0.45, look_cam=look_cam, look=(look_x, look_y), head_turn=head_turn,
                       head_nod=nod, lean=-0.1 * inhale, mood=mood, mood2=mood2, mood_mix=mix_, wink=wink,
                       tail_swing=-0.6, seed=2, **song)


# ----------------------------------------------------------------------------------------
# setup + draw
# ----------------------------------------------------------------------------------------

def setup():
    st = {"light": fx.LightLayer()}
    store = {}
    st["book"] = PG.make_book(EV)
    for sp_ in st["book"].spreads:
        for pg in (sp_.left, sp_.right):
            GILT[id(pg)] = _page_gilt(pg)
    scratch = core.frame(4, 4)[1]
    lrig = sb.draw_lectern(scratch, LECT_X, LECT_Y, LECT_SC, L_CANDLE, st["book"], height=LECT_HT, view=VIEW_WIDE)
    st["lectern_candles"] = lrig.candles
    # where the flames really are (the room's light sources) -- before the lit layers are painted
    for key, c in zip(("cand_l", "cand_r"), lrig.candles):
        SRC[key] = sb.draw_candle(scratch, c[0], c[1], LECT_SC, t=0.0, light=L_CANDLE, height=40.0).flame
    st["wall"] = fx.Layer(lambda c: draw_wall(c, store), blur=1.1, opaque=True, **M)
    st["floor"] = fx.Layer(lambda c: draw_floor(c, store), blur=0.6, **M)
    st["fg"] = fx.Layer(draw_fg_candle, blur=6.0, x=FG_CANDLE[0] - 130, y=FG_CANDLE[1] - 70, w=260, h=880)
    st.update(store)
    st["shade"] = fx.Layer(draw_room_shade, blur=24.0, res=0.25, **M)
    sx, sy = st["stack_top"]
    SRC["stack"] = sb.draw_candle(scratch, sx + 10, sy, 1.9, t=0.0, light=L_CANDLE, height=22.0, width=12.0).flame
    return st


# ---- gold leaf that glints as the light and the camera move -------------------------------

def _flat_loop(build):
    """Flatten a path built by build(cr) into one polyline (page units)."""
    surf, c = core.frame(4, 4)
    c.new_path()
    build(c)
    pts = []
    for kind, xy in c.copy_path_flat():
        if kind in (cairo.PATH_MOVE_TO, cairo.PATH_LINE_TO) and xy:
            pts.append(tuple(xy))
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def _page_gilt(page):
    """The gilt lines of one of our pages, as page-unit polylines: the border rule and the gold
    frame of its illustration (if it has one)."""
    w, h = 150.0, 200.0
    m = w * 0.075
    loops = [[(m, m), (w - m, m), (w - m, h - m), (m, h - m), (m, m)]]
    art = getattr(page, "illus", None)
    if isinstance(art, PG.PageArt) and art.box is not None and art.frame:
        bx, by, bw, bh = art.box[0] * w, art.box[1] * h, art.box[2] * w, art.box[3] * h
        loops.append(_flat_loop(lambda c: sb._frame_path(c, bx, by, bw, bh, art.frame)))
    return loops


def _along_loop(pts, s0, s1, n=10):
    """Points of the closed polyline between arc-length fractions s0..s1 (may wrap)."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    out = []
    for k in range(n + 1):
        u = ((s0 + (s1 - s0) * k / n) % 1.0) * total
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= u:
                f = (u - acc) / max(1e-6, L)
                out.append((lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)))
                break
            acc += L
    return out


def draw_glints(cr, t, cam, brig, book, spread, vis):
    """Burnished gold leaf: a short specular streak slides along each gilt rule of the open pages.
    Where it sits on the loop follows the camera (a specular moves when the eye moves) and drifts
    with the candle; its brightness breathes with the flame. A streak + a tight warm bloom, never a
    lens star."""
    if vis <= 0.01:
        return
    fl = sb.candle_flicker(t, 3)[0]
    sp = book.spread(spread)
    for side, page in (("left", sp.left), ("right", sp.right)):
        M_ = brig.page_matrix.get(side)
        if M_ is None:
            continue
        for k, loop in enumerate(GILT.get(id(page), [])):
            if len(loop) < 3:
                continue
            base = 0.37 * k + (0.13 if side == "right" else 0.61)
            sc = base + 0.03 * t + 0.00042 * cam.x + 0.00031 * cam.y
            a = vis * (0.6 + 0.4 * math.sin(t * 0.8 + k + (0.0 if side == "right" else 2.0))) * clamp(fl - 0.05)
            if a < 0.05:
                continue
            pts = [M_.transform_point(*p) for p in _along_loop(loop, sc - 0.03, sc + 0.03, 14)]
            wpx = (1.35 if k == 0 else 2.1) * LECT_SC        # the gilt rule's own width (world px)
            B.detail_line(cr, pts, wpx * 0.9, "#fff1c2", 0.85 * a, taper=(0.02, 1.0, 0.02))
            mx, my = pts[len(pts) // 2]
            fx.glow(cr, mx, my, wpx * 4.0, "#ffd98a", 0.45 * a)


def cover_glint(cr, t, t0, t1):
    """Before the book opens: a sheen of candlelight sweeps across the closed cover and its gilt
    title, with a twinkle where it crosses the letters."""
    if not t0 < t < t1:
        return
    u = (t - t0) / (t1 - t0)
    W_, H_, ov = 150.0, 200.0, 6.0
    CW, CH = W_ + ov + 0.8, H_ + 2 * ov
    cv, sv = math.cos(VIEW_WIDE), math.sin(VIEW_WIDE)
    z_h = 2.0 * 12.0 + 4.5 * 0.5
    shift = -(W_ + ov) * 0.5

    def C(bx, by):
        return DESK[0] + LECT_SC * (bx + shift), DESK[1] + LECT_SC * (by * cv - z_h * sv)
    poly = [C(0, -CH / 2), C(CW, -CH / 2), C(CW, CH / 2), C(0, CH / 2)]
    a = math.sin(math.pi * u)
    sx = lerp(-40.0, CW + 40.0, core.inout_sine(u))
    cr.save()
    cr.new_path()
    core.polygon(cr, poly)
    cr.clip()
    g = cairo.LinearGradient(*C(sx - 34, -CH / 2), *C(sx + 34, CH / 2))
    g.add_color_stop_rgba(0.0, 1.0, 0.85, 0.55, 0.0)
    g.add_color_stop_rgba(0.5, 1.0, 0.88, 0.6, 0.22 * a)
    g.add_color_stop_rgba(1.0, 1.0, 0.85, 0.55, 0.0)
    cr.set_source(g)
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.paint()
    cr.restore()
    # the sheen catches the gilt letters as it crosses them: a soft warm bloom riding the title
    tx, ty = C(min(CW - 30.0, max(34.0, sx)), -CH * 0.12)
    fx.glow(cr, tx, ty, 26.0 * LECT_SC, "#ffd98a", 0.32 * a)
    fx.sparkle(cr, tx, ty, 3.2 * LECT_SC, "#fff6d8", 0.6 * a, angle=0.6 * u)


def drop_cap_glint(cr, t, t0, brig):
    """'Once': the illuminated O catches the light as the first word is sung."""
    if not t0 - 0.05 < t < t0 + 1.1:
        return
    u = (t - t0 + 0.05) / 1.15
    a = math.sin(math.pi * clamp(u * 1.4)) * (1.0 - u * 0.4)
    M_ = brig.page_matrix.get("left")
    if M_ is None:
        return
    size = 150.0 / 17.0
    cap = size * 1.24 * 3 - size * 0.15
    x0, y0 = 150.0 * 0.11, 200.0 * 0.11 + size * 0.12
    cx, cy = M_.transform_point(x0 + cap * 0.32, y0 + cap * 0.3)
    fx.glow(cr, cx, cy, 30.0 * LECT_SC, "#ffd98a", 0.35 * a)
    fx.sparkle(cr, cx, cy, 4.0 * LECT_SC * (0.6 + 0.4 * a), "#fffbe8", 0.8 * a, angle=0.8 * u)


# ---- the storyteller's shadow on the wall (Klaus: light is shape) --------------------------

SHADOW_RES = 0.25


def draw_bard_shadow(cr, st, cam, pose, t, strength=1.0):
    """The bard's silhouette thrown big and soft onto the stone wall by the lectern candle burning
    beside his head (Klaus: light is shape): his silhouette projected from the flame (scaled about
    it, so the plume and head rise on the wall to his left), drawn at quarter resolution, blurred,
    and laid on the wall as plum shadow. It plays the lute along with him and wavers with the
    flame."""
    from PIL import Image, ImageFilter
    sw_, sh_ = int(W * SHADOW_RES), int(H * SHADOW_RES)
    surf = st.get("_shadow_surf")
    if surf is None:
        surf = core.new_surface(sw_, sh_)
        st["_shadow_surf"] = surf
    c2 = cairo.Context(surf)
    c2.set_operator(cairo.OPERATOR_CLEAR)
    c2.paint()
    c2.set_operator(cairo.OPERATOR_OVER)
    c2.scale(SHADOW_RES, SHADOW_RES)
    c2.transform(cam.matrix(1.0))
    # projected from the flame: the flame's own sway moves the shadow (a living light)
    b, sway, stretch = sb.candle_flicker(t + 0.9, 2)
    lx, ly = SRC["cand_l"]
    lx += 6.0 * sway
    k = SHADOW_K * (1.0 + 0.025 * sway)
    c2.translate(lx, ly)
    c2.scale(k, k)
    c2.translate(-lx, -ly)
    ch.draw_bard(c2, BARD_X, BARD_Y, BARD_SC, pose.with_(shadow=False), L_CANDLE, t, detail=0)
    surf.flush()
    img = Image.frombuffer("RGBA", (sw_, sh_), bytes(surf.get_data()), "raw", "BGRA", surf.get_stride(), 1)
    alpha = img.getchannel("A").filter(ImageFilter.GaussianBlur(2.6))
    data = bytearray(sw_ * sh_ * 4)
    data[3::4] = alpha.tobytes()
    mask = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, sw_, sh_, sw_ * 4)
    cr.save()
    with cam.view(cr, WALL_P):                       # only on the wall, above the floor line
        cr.rectangle(-400, -400, W + 800, WALL_Y + 406)    # down to the floor line
    cr.identity_matrix()
    cr.clip()
    cr.scale(1.0 / SHADOW_RES, 1.0 / SHADOW_RES)
    core.src(cr, "#0e0409", (0.5 + 0.08 * (b - 1.0)) * strength)
    cr.mask_surface(mask, 0, 0)
    cr.restore()


def wink_ting(cr, t, t0, rig, dur=0.6):
    """The wink's 'ting!': a four-point sparkle popping at the winking (near) eye's outer corner,
    with a smaller one trailing it (bard_twinkle puts it on the comb for a right-facing head)."""
    if not t0 <= t <= t0 + dur or not rig.eyes:
        return
    u = (t - t0) / dur
    s = rig.scale
    ex, ey = rig.eyes[-1]
    side = -1.0 if rig.yaw >= 0 else 1.0                  # the outer corner of the near eye
    pop = core.out_back(clamp(u / 0.25)) * (1.0 - smooth((u - 0.55) / 0.45))
    fx.sparkle(cr, ex + side * 16.0 * s, ey - 13.0 * s, 10.0 * s * pop, "#fff6d8", 0.95 * pop, angle=0.5 * u)
    p2 = math.sin(math.pi * clamp((u - 0.18) / 0.6))
    fx.sparkle(cr, ex + side * 25.0 * s, ey - 4.0 * s, 5.0 * s * p2, "#ffe7a8", 0.8 * p2, angle=-0.4 * u)


def _on_screen(cam, x0, y0, x1, y1, p=1.0, pad=40):
    ax, ay = cam.to_screen(x0, y0, p)
    bx, by = cam.to_screen(x1, y1, p)
    return not (max(ax, bx) < -pad or min(ax, bx) > W + pad or max(ay, by) < -pad or min(ay, by) > H + pad)


def draw(cr, t, st):
    cam = camera_at(t)
    z = cam.zoom
    view = view_for_zoom(z)
    k_book = smooth((z - 2.6) / (4.2 - 2.6))          # 0 in the nook .. 1 deep in the book
    deep = z > 4.6
    flames = []
    # ---- the wall (parallax), the hearth fire
    if not deep:
        with cam.view(cr, WALL_P):
            st["wall"].paint(cr)
            if _on_screen(cam, HEARTH_X - 260, WALL_Y - 400, HEARTH_X + 260, WALL_Y + 40, WALL_P):
                fire = sb.draw_fire(cr, *st["hearth"].fire, HEARTH_SC, t=t, seed=1)
            else:
                fire = sb.FireRig(glow=st["hearth"].fire, flicker=sb.fire_flicker(t, 1))
        bard_vis = _on_screen(cam, BARD_X - 190, BARD_Y - 480, BARD_X + 230, BARD_Y + 30)
        st["_pose"] = bard_pose(t) if bard_vis else None
        if st["_pose"] is not None and z < 2.6:
            draw_bard_shadow(cr, st, cam, st["_pose"], t, strength=1.0 - smooth((z - 2.0) / 0.6))
        with cam.view(cr, 1.0):
            st["floor"].paint(cr)
    else:
        st["_pose"] = None
        core.src(cr, "#140a0c")
        cr.paint()
        fire = sb.FireRig(glow=st["hearth"].fire, flicker=sb.fire_flicker(t, 1))
    o, spread, turn = book_state(t)
    with cam.view(cr, 1.0):
        # ---- the lectern (drawn with the current desk angle) and the great book
        if not deep:
            sb.draw_lectern(cr, LECT_X, LECT_Y, LECT_SC, L_CANDLE, st["book"], height=LECT_HT, view=view)
        brig = sb.draw_book(cr, st["book"], DESK[0], DESK[1], LECT_SC, t=t, open=o, spread=spread, turn=turn,
                            light=L_CANDLE, view=view)
        cover_glint(cr, t, 0.9, T_OPEN + 0.1)
        if o >= 1.0:
            gv = 1.0
            for t0_ in (T_TURN1, T_TURN2, T_TURN3):
                gv = min(gv, smooth(abs(t - t0_) / 0.25) if t < t0_ else 1.0)
                if t0_ <= t < t0_ + (TURN3_DUR if t0_ == T_TURN3 else TURN_DUR) + 0.2:
                    gv = 0.0
            draw_glints(cr, t, cam, brig, st["book"], spread, gv)
        drop_cap_glint(cr, t, LN[1].start + 0.02, brig)
        for i, c in enumerate(st["lectern_candles"]):
            if _on_screen(cam, c[0] - 60, c[1] - 120, c[0] + 60, c[1] + 20):
                cd = sb.draw_candle(cr, c[0], c[1], LECT_SC, t=t + i * 0.9, light=L_CANDLE, seed=i + 2, height=40.0)
                flames.append(cd)
        if not deep:
            # the empty stool, waiting for you
            if _on_screen(cam, STOOL_X - 90, STOOL_Y - 110, STOOL_X + 90, STOOL_Y + 20):
                ch.draw_bard_stool(cr, STOOL_X, STOOL_Y, BARD_SC, L_CANDLE, yaw=0.55)
            # the bard
            if st.get("_pose") is not None:
                pose = st["_pose"]
                ch.draw_bard_stool(cr, BARD_X, BARD_Y, BARD_SC, L_BARD, yaw=ch.bard_yaw(pose))
                rig = ch.draw_bard(cr, BARD_X, BARD_Y, BARD_SC, pose, L_BARD, t)
                st["_rig"] = rig
                wink_ting(cr, t, T_WINK + 0.06, rig)
            sx, sy = st["stack_top"]
            if _on_screen(cam, sx - 60, sy - 120, sx + 60, sy + 20):
                flames.append(sb.draw_candle(cr, sx + 10, sy, 1.9, t=t + 2.1, light=L_CANDLE, seed=7, height=22.0,
                                             width=12.0, drips=4))
        # the room's falloff over everything (fades out as we dive into the page)
        if not deep:
            st["shade"].paint(cr, alpha=1.0 - k_book)
        # gold motes rising off the open pages (the pages come alive)
        if o > 0.3:
            (lx0, ly0), (rx1, ry1) = brig.pages["left"][0], brig.pages["right"][2]
            md = 0.45 * clamp((o - 0.3) / 0.4) * (1.0 - 0.75 * k_book)
            if md > 0.01:
                fx.dust(cr, t, (lx0, ly0 - 60, rx1 - lx0, ry1 - ly0 + 40), n=22, color="#ffe3a0", alpha=md,
                        size=(1.0 / max(1.0, z / 2.0), 2.6 / max(1.0, z / 2.0)), seed=5, drift=(3.0, -12.0), twinkle=1.0)
    # ---- the near candle we push past (its own plane close to the lens, out of focus)
    fgx, fgy = cam.to_screen(FG_CANDLE[0], FG_CANDLE[1], FG_P)
    fz = z ** FG_P
    fg_vis = fgx > -180 and t < 8.0
    if fg_vis:
        with cam.view(cr, FG_P):
            st["fg"].paint(cr)
        fg_flame(cr, fgx, fgy, fz * 0.72, t)
    # ---- light: candles, the hearth, a pool on the open book, moonlight, the bard's floor pool
    lc = st["light"].begin()
    zf = min(z, 3.0)
    for cd in flames:
        sxy = cam.to_screen(*cd.flame)
        fx.glow(lc, sxy[0], sxy[1], 210 * zf * cd.flicker, "#ffaa55", 0.26)
        fx.glow(lc, sxy[0], sxy[1] - 4 * zf, 46 * zf * cd.flicker, "#ffe2b0", 0.5)
    hx, hy = cam.to_screen(*fire.glow, WALL_P)
    fx.glow(lc, hx, hy, min(1400, 900 * z ** WALL_P) * fire.flicker, "#ff7a30", 0.34 * (1 - k_book))
    if o > 0.2:
        bx = (brig.pages["left"][0][0] + brig.pages["right"][1][0]) / 2
        by = (brig.pages["left"][0][1] + brig.pages["left"][3][1]) / 2
        sbx, sby = cam.to_screen(bx, by)
        fl = sb.candle_flicker(t, 3)[0]
        fx.light_pool(lc, sbx, sby, min(1500, 520 * z), min(900, 280 * z), "#ffcf8a",
                      lerp(0.08, 0.16, k_book) * clamp((o - 0.2) / 0.3) * fl)
    if not deep:
        mx, my = cam.to_screen(WIN_X + 75, WIN_Y + 120, WALL_P)
        fx.glow(lc, mx, my, 300 * z, "#7f9fe0", 0.12)
        # the moon's shaft: the one cool note in the warm room (fades as we dive into the book)
        sx0, sy0 = cam.to_screen(WIN_X + 75, WIN_Y + 150, WALL_P)
        sx1, sy1 = cam.to_screen(WIN_X - 170, WALL_Y + 150, 1.0)
        fx.light_shaft(lc, sx0, sy0, sx1, sy1, 120 * z, 330 * z, "#8aa6f0", 0.07 * (1.0 - k_book), soft=3,
                       fade_start=0.0, fade_end=0.85)
        px, py = cam.to_screen(BARD_X + 60, BARD_Y + 5)
        fx.light_pool(lc, px, py, 420 * z, 90 * z, "#ffa060", 0.14)
        rig = st.get("_rig") if st.get("_pose") is not None else None
        if rig is not None:
            # light wrap: the candle beside him lifts his lit side (face, ruff, the lute's belly)
            hx_, hy_ = rig.head
            wx, wy = cam.to_screen(hx_ + 70.0, hy_ + 60.0)
            fl = sb.candle_flicker(t + 0.9, 2)[0]
            fx.glow(lc, wx, wy, 300 * z, "#ffb070", 0.11 * fl)
    if fg_vis:
        fl = sb.candle_flicker(t, 9)[0]
        fx.glow(lc, fgx, fgy - 18 * fz, 300 * fz * fl, "#ffa850", 0.3)
    fx.post(cr, t, light=st["light"], bloom_strength=lerp(0.6, 0.28, k_book), threshold=lerp(0.8, 0.92, k_book),
            bloom_radius=2.4, grain=0.035, vignette=lerp(0.55, 0.42, k_book), vignette_color=(0.06, 0.02, 0.04))
    # ---- the fades (the near candle's flame is the first and last thing we see)
    if t < T_FADEIN:
        fx.fade(cr, 1.0 - core.inout_sine(clamp(t / T_FADEIN)))
    if t > T_OUT0:
        fx.fade(cr, core.inout_sine(clamp((t - T_OUT0) / (T_OUT1 - T_OUT0))))
    if fg_vis and t < T_FADEIN:
        # the near flame burns through the fade: the first light of the film
        u = 1.0 - core.inout_sine(clamp(t / T_FADEIN))
        fg_flame(cr, fgx, fgy, fz * 0.72, t, alpha=u)
        fx.glow(cr, fgx, fgy - 18 * fz, 160 * fz, "#ffa850", 0.35 * u)


# ----------------------------------------------------------------------------------------
# sound: discrete on-screen events for the foley pass (times as the animation uses them)
# ----------------------------------------------------------------------------------------

def _sfx_cues():
    """Every cue is computed from the same event times the animation uses (EV, the book's turn
    times, the wink), offset for where each synthesized sound has its attack: door_close hits
    0.16 s after its cue, book_open lands its cover 0.58 s in, a heavy page_turn's swish peaks
    ~0.25 s in and flaps down at ~0.45 s (the visible leaf lands 0.85 s after the turn starts)."""
    pan_house = (-0.45, 0.0, 0.45)                    # the three painted houses, left to right on screen
    cues = [
        (0.3, "candle_flicker", {"gain": 0.5, "pan": -0.4}),                     # the near flame: the first light
        (T_COVER_LAND - 0.58, "book_open", {"gain": 0.9, "pan": 0.25}),            # creak, the cover lands, pages flutter
        (EV["stone"] - 0.35, "rune_glow", {"gain": 0.25, "pan": -0.1, "dist": 0.5}),  # the rune-stone flares cold
        (T_WINK + 0.04, "crystal_chime", {"gain": 0.3, "pan": -0.1}),              # the wink's "ting!"
        (EV["wash_door"] + 0.02, "door_open", {"gain": 0.45, "pan": 0.2, "dist": 0.5}),  # he opens the wash-house door
    ]
    # "a LOCK on each heart": the three painted doors slam shut, 40 ms apart (shut at lock + 0.04 k + 0.09)
    for k in range(3):
        cues.append((EV["lock"] + 0.04 * k + 0.09 - 0.16, "door_close",
                     {"gain": 0.3 - 0.05 * k, "pan": pan_house[k], "dist": 0.65}))
    # "a LATCH on each pane": six shutters latch one after another (latched 0.3 s after each starts)
    for i in range(6):
        cues.append((EV["latch"] - PG.LATCH_LEAD + PG.LATCH_STEP * i + 0.3, "tap_wood",
                     {"count": 1, "gain": 0.18, "pan": pan_house[i // 2] + (0.08 if i % 2 else -0.08), "dist": 0.55}))
    # the three page turns (the leaf lands TURN_DUR after each starts)
    for t0, d, g in ((T_TURN1, TURN_DUR, 0.8), (T_TURN2, TURN_DUR, 0.6), (T_TURN3, TURN3_DUR, 0.8)):
        cues.append((t0 + d - 0.55, "page_turn", {"heavy": True, "gain": g, "pan": 0.3}))
    return sorted(cues, key=lambda c: c[0])


SFX_CUES = _sfx_cues()
