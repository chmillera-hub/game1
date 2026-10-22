"""s2_apothecary.py -- SCENE 2: THE APOTHECARY.   Emotion: kind but useless.

THE IDEA. Too shy to say it aloud, he has written it down. He asks a kind, competent creature
for help with the one thing she has no product for -- and she answers the only way her world
allows: with things. She is genuinely warm (never a villain); that is the tragedy and the joke.
Two walls stand between them: the long dark counter (the barrier, always in frame), and the
column of remedies she builds on it -- a single, absurdly neat totem of products balanced one on
another (a jar on a cork!), which by the end rises above both their heads and literally blocks
their eye line. To ask his real question he has to lean round it.

COLOUR / VALUE PLAN. After the dark teal wash-house, a hard cut into GLARE: over-bright,
clinical, high-key mint-white. Limewashed plaster, pale flagstones, a wall of glass jars washed
pale by the light (screen-lightened + hazed: the background lives in a narrow high-value band,
held just below the orbs so the light sources stay the brightest things in frame). The light
comes from caged arcane orbs on chains -- white-hot cores in dark iron armillary cages, mint
halos, rune rings, one that stutters like a dying fluorescent -- with soft pools of downlight
and soft-edged specular smears on the waxed counter, a cool top-rim on every head, bloom with a
wide halo, and a cold teal-grey vignette (never a muddy black). Against all that pale: his charcoal coat is the darkest shape in the frame, his mustard
scarf the only warm note (warm light is for kindness -- there is none to be had here), and the
remedies are the saturated, glittering accents (cobalt draught, glowing vitamin berries,
lavender candle, the rose-window book): the "stones" sparkle. The counter is heavy dark carved
oak (linenfold) -- the one dark mass across the bottom of every shot, under the captions.
Period: timber posts, a low oak beam hung with drying herbs he must stoop under, a leaded
diamond-pane window on the rainy night (S3's rain waiting outside), a carved APOTHECARY board
with the green cross, a brass till with ivory rune keys and a bell, parchment, glass, iron.

SHOTS (every time is derived from timeline.json beats/lines; the numbers are today's values)
 A1  0 -> s2_note (3.0)   TWO-SHOT ACROSS THE COUNTER. Camera a little above counter height, so
     the polished counter top reads as a plane between them; slow drift-in 1.0 -> 1.035.
     He stands at the counter's end, stooped under the herbs, the folded note pinched at his
     chest; she waits at her station, paws on the oak, a professional smile.
     THOUGHT -> GLANCE -> BREATH -> ACT: 0.45 his eyes flick up to her and straight back down;
     a breath (he straightens a hair); 1.05 the hand goes down -- leaning in, a horn brushes the
     low tansy bundle (it swings off his horn) -- the note touches the oak ON s2_slide; a careful
     push with flat claws (elbow still soft), he lets go (+0.35) and the note glides on by itself
     and stops in front of her (+0.75); his eyes follow it, then up to her: hope. She steps over
     to him, leans, her far paw pinches the note, lifts it; both paws take it up to read.
     Eye-trace: his face -> his hand -> the cream note on the dark oak -> her face.
 B   s2_note (3.0 - 6.0)  INSERT, HER POINT OF VIEW (hard cut): the note between her paws (thumbs
     pinching the front, fingers behind) unfolds (3.06-3.46): "Something for / loneliness?" in
     his hand, big and legible for 2.5 s. Beyond it, out of focus (a live quarter-res redraw,
     blurred), he waits under the herbs, his amber eyes just above the note's edge; a shy
     glance down and back. Slow push-in 1.0 -> 1.06.
 A2  s2_note.end (6.0) - s2_stare (16.5)  TWO-SHOT; from s2_items - 0.6 a slow push toward the
     growing column (zoom -> 1.2). She lowers the note and looks OVER her half-moon spectacles
     at him: the meaning lands -- sympathy (brows knit up, eyes wide open, head tipped). s2_nod:
     a slow, kind nod with a cat's slow blink ("I see you") -- and he brightens (brows up, a shy
     smile, wings lift): she understood! She tucks the note into her apron pocket and goes to
     work, eager ("I know just the thing!") -- open-eyed and bright, never a smug squint.
     s2_items: four trips, each set-down landing ON its beat with a settle. Her paw really holds
     what it carries: the wrist targets for every shelf grab and set-down are solved through the
     rig in setup() so the GRIP lands on the item's middle (no paw floating below a bottle).
     Every item comes in to her chest BEFORE she turns and rides round with her body through an
     11-frame turn (the arm's depth follows the true 3D carry point round the turn and on up over
     the column, so the elbow never flips and the paw never spins; carried items move <= ~60 px
     a frame), and a fast frame trails two faint multiples (a smear), never a jump:
       s2_item1 SLEEP DRAUGHT  turn to the shelf behind her, reach, back, set down.
       s2_item2 VITAMINS       glide to the far shelf and back; she balances the jar ON THE
                               DRAUGHT'S CORK -- it wobbles, holds. (Absurdly neat.)
       s2_item3 CALM candle    reach up to the high shelf, bring it down to her chest BEFORE she
                               turns, then in above the column from a step further off, and
                               down onto the jar's cover.
       s2_item4 MINDFUL COLORING FOR ADULTS  she ducks below the counter, comes up WITH it (held at
                               her chest, it rises at her speed), on tiptoe stands it on the
                               candle's rim: the column now towers over her head; it teeters
                               (one full wobble), her paw hovers beside it at its height, one
                               tap (+0.84, the book squashes two frames) squares it -- and a
                               little "ta-da!": the open paw sweeps out beside the tower.
     He watches like a tennis match (eyes lead, head ~0.2 s behind); at each thunk his eyes
     drop to the column and climb its new height -- his gaze rises with the tower; a blink on
     each landing. After the vitamins he tries once more -- "Actually, I..." -- an inhale, a paw
     to his own chest, brows up, mouth shut; she has already turned for the high shelf, and it
     all goes out of him. Brows sink from hope to resignation; wings droop further every item.
 C   s2_stare (16.5) - end   LOW ANGLE ON THE TOWER (hard cut). Camera at counter height: the
     counter top edge-on, the column huge in the middle rising above both heads, labels big;
     the rigs drawn with a negative camera elevation (hems curve up: seen from below) and the
     room behind keystoned (verticals converge upward), soft; the beam, herbs and orbs overhead.
     The tower blocks their eye line. Slow push 1.0 -> 1.035 with a breathing drift.
     s2_stare: he stares up at the top of the tower. She beams at it.
     s2_l1 PHARMACIST "Try these. Lots of people swear by them." -- warm, encouraging: her far paw
       presents the tower, eyes to the tower then to him, a reassuring nod on "swear by them".
       His eyes go to her as she starts, then climb the tower again.
     THOUGHT -> GLANCE -> BREATH -> s2_l2 MAN "Do any of them talk back?": his eyes travel down
       the tower (thought), find her (glance, 0.38 s before), a breath lifts him and he leans to
       see round the tower; the line quiet and sincere (small mouth), brows up, eyes on her.
 D   s2_pause - 0.25 .. s2_ring - 0.14   MCU ON HER (a punch-in on the low angle, slow push): the
     listening smile -- then on s2_pause it LOCKS (two frames) into a rigid, toothy polite grin,
     cheeks up, lids wide, pupils pinned, a tiny pull-back; nothing moves but the whiskers (two
     hard two-frame snaps) and her eyes: a dart to her shelves (nothing there for this) and back.
     In the silence an orb stutters (the light on her face buzzes). ~0.7 s held. A double blink
     reboots her, eyes to the till.
 E   s2_ring - 0.14 .. s2_ring + 0.52   INSERT, THE TILL: her paw comes down from above and the
     index fingertip lands ON key 2 exactly at s2_ring (solved: the hand is placed from the tip);
     the key sinks, the bell rocks and dings, the number flags pop, the parchment receipt curls up
     out of its slot; the paw lifts away and the receipt keeps coming. Under the insert we HEAR
     his sigh begin and her bag the whole tower at speed (a paper sack snapped open, clinks, the
     book's thud, the sack plunked down a frame before the cut).
 C'  s2_ring + 0.52 .. end   BACK TO THE LOW TWO-SHOT: the tower is gone; the white sack with the
     green cross stands where it stood (book and draught peeking out), still settling; her paw on
     it gives it one satisfied pat, a proud little nod to him. He looks down at it; the exhale:
     head and shoulders sink and stay sunk, a curl of smoke from his nostrils. Held ~1 s to the
     hard cut (S3: he walks home in the rain with it).

ACTING NOTES. Dragon: shy, careful, too big for the room (hunched, wings low, stooped under the
herbs), never snarky; eyes lead, the head follows. Lioness: tidy, graceful, quick professional
paws, sincerely kind; reaches stay comfortable (she steps to the work -- no straight-arm
lunges). Expressions blend continuously (expr_track: no pops). Mouths move only on their own
lines (timeline.talk); his line is quiet, so his mouth opens small; the sigh is a closed-mouth
nose exhale.

CRAFT. Cached layers (walls, shelves, beam, counter, herb bundles, the keystoned shot-C room);
per frame: both rigs, the remedies (on the shelves they are tinted into the hazed shelf plane;
as she carries one into the counter's light the haze lifts), the orbs, rain beyond the glass,
dust motes in the glare, contact shadows on the counter, specular glints on glass, a
quarter-res LightLayer (orb halos, hot spots, pools, head light), bloom, grain, vignette.
Captions sit over the dark counter front: no faces or key action in the bottom 180 px.
SFX_CUES (bottom of the file) are built from the same constants the animation uses.
"""

import dataclasses
import math

import cairocffi as cairo
import numpy as np
from PIL import Image, ImageFilter

from film.lib import core, fx, env, props as P, timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.characters import dragon as DRAGON_MOD
from film.lib.characters import lioness as LIO_MOD
from film.lib.characters import _cast_kit as CK
from film.lib.core import clamp, lerp, ramp, smooth
from film.scenes import _s2_rig as R2

SCENE = 2
W, H = core.W, core.H
TAU = math.tau

# ----------------------------------------------------------------------------------------
# timing: everything from the timeline (beats + lines); scene beats are derived from them
# ----------------------------------------------------------------------------------------
DUR = tl.scene(SCENE).duration
T_SLIDE = tl.beat("s2_slide").t
T_NOTE0, T_NOTE1 = tl.beat("s2_note").t, tl.beat("s2_note").end
T_NOD = tl.beat("s2_nod").t
T_ITEMS0, T_ITEMS1 = tl.beat("s2_items").t, tl.beat("s2_items").end
T_ITEM = [tl.beat(f"s2_item{k}").t for k in (1, 2, 3, 4)]
T_STARE = tl.beat("s2_stare").t
LN1, LN2 = tl.line("s2_l1"), tl.line("s2_l2")
T_PAUSE = tl.beat("s2_pause").t
T_RING = tl.beat("s2_ring").t

CUT_B, CUT_A2, CUT_C = T_NOTE0, T_NOTE1, T_STARE      # insert, back to the two-shot, low angle

T_REL = T_SLIDE + 0.35           # his claws let go of the note (his elbow still soft) ...
T_GO = T_SLIDE + 0.75            # ... it glides on by itself and comes to rest in front of her
T_HORN = T_SLIDE - 0.28          # as he leans in, a horn brushes the tansy bundle above him
T_TAP = T_ITEM[3] + 0.84         # she squares the teetering book with one tap (after one full teeter)

# ----------------------------------------------------------------------------------------
# light + palette
# ----------------------------------------------------------------------------------------
L = ch.LIGHTS["apothecary"]
# the orbs hang overhead: a cool white top-rim on everyone (stronger on the dark-coated dragon)
LD = L.with_(rim_strength=0.78, rim_direction=(-0.25, -0.97))
LL = L.with_(rim_strength=0.6, rim_direction=(0.3, -0.95))

C = {
    "plaster": "#dbe8e2", "plaster_hi": "#f4faf6", "plaster_lo": "#b4cac1",
    "timber": "#7d6c58", "timber_dk": "#54483a", "timber_lt": "#a08f78",
    "floor": "#c4cfc9", "floor_lo": "#97a59e", "joint": "#82918a",
    "oak": "#4b3427", "oak_dk": "#2e1f17", "oak_lt": "#6e5140", "oak_top": "#563e30", "oak_hi": "#a88a70",
    "orb": "#f6fffc", "orb_glow": "#a8f0d6", "mint": "#9df0d0",
    "night": "#1b2a44", "night_lo": "#101a2e", "lead": "#3a4a52",
    "haze": "#e6f3ee", "shelf_haze": "#cfe2da", "smoke": "#5d666e",
}
VIG = (0.05, 0.12, 0.11)          # the vignette darkens toward a cold teal-grey, never a muddy black

# ----------------------------------------------------------------------------------------
# shot A geometry (world = screen at zoom 1)
# ----------------------------------------------------------------------------------------
SC = 1.55                         # everyone (and everything they touch) in the action plane
FLOOR_D = 1062.0                  # the dragon's ground (customer side)
CTOP = 772.0                      # the counter top's FRONT edge
CDEPTH = 74.0                     # the counter top seen from a little above: a real plane
CBACK = CTOP - CDEPTH             # its back edge (698)
FLAT = 0.43                       # foreshortening of anything lying flat on the counter
CX0 = 548.0                       # the counter's left end (right at his elbow: he can reach the note)
DRAGON_X = 440.0
HOME = 1110.0                     # her station at the counter
PILE_X = 905.0                    # the column's base, on the counter top (mid-depth)
PILE_Y = CTOP - 34.0
NOTE_Y = CTOP - 22.0              # the note slides along the front of the counter top
NOTE_START_X, NOTE_REST_X = 625.0, 762.0
NOTE_REL_X = 685.0                # where his claws let go: a careful push, then the note glides
TILL_X, TILL_Y = 1505.0, CBACK + 24.0
SHELF_X, SHELF_Y, SHELF_W, SHELF_H = 770.0, 92.0, 760.0, 400.0   # scale-1 units (x SC on screen)
BEAM_Y = 58.0                     # underside of the low ceiling beam
ORBS = [(1000.0, 150.0, 0), (1470.0, 136.0, 1), (1860.0, 156.0, 2)]
WINDOW_A = (60.0, 330.0, 170.0, 400.0)

# the lioness stands behind the counter: ground chosen so her on_counter paws rest on its top
_ELEV_C, _ELEV_S = math.cos(LIO_MOD.ELEV), math.sin(LIO_MOD.ELEV)
_K_LIO = SC * LIO_MOD.SIZE_K
LIO_Y = CBACK + 25.0 + ((200.0 / LIO_MOD.SIZE_K + 4.0) * _ELEV_C - 58.0 * _ELEV_S) * _K_LIO

_gap = SHELF_H / 4.0
BOARDS = [SHELF_Y + (_gap * (r + 1) - 12.0) * SC for r in range(4)]     # shelf-board tops (screen y)


# ----------------------------------------------------------------------------------------
# set dressing
# ----------------------------------------------------------------------------------------

def _plaster(cr, x, y, w, h, seed=0):
    core.vgrad(cr, x, y, w, h, [C["plaster_hi"], C["plaster"], C["plaster_lo"]])
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    env.texture(cr, "plaster", 0.22, scale=1.3, offset=(seed * 37.0, seed * 11.0))
    cr.restore()


def _timber(cr, x, y, w, h, vertical=True, color=None):
    core.src(cr, color or C["timber"])
    cr.rectangle(x, y, w, h)
    cr.fill()
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    env.texture(cr, "wood", 0.28, scale=1.0, sx=0.25 if vertical else 4.0, sy=4.0 if vertical else 0.25)
    if vertical:
        core.src(cr, C["timber_lt"], 0.6)
        cr.rectangle(x, y, 4, h)
        cr.fill()
        core.src(cr, C["timber_dk"], 0.6)
        cr.rectangle(x + w - 7, y, 7, h)
        cr.fill()
    else:
        core.src(cr, C["timber_dk"], 0.7)
        cr.rectangle(x, y + h - 9, w, 9)
        cr.fill()
        core.src(cr, C["timber_lt"], 0.5)
        cr.rectangle(x, y, w, 3)
        cr.fill()
    cr.restore()


def _window(cr, x, y, w, h):
    """A tall leaded window: the rainy night outside, interior light caught in the diamond panes."""
    r = w / 2

    def opening(c, d=0.0):
        c.new_path()
        c.move_to(x - d, y + h)
        c.line_to(x - d, y + r)
        c.arc(x + r, y + r, r + d, math.pi, 0)
        c.line_to(x + w + d, y + h)
        c.close_path()
    opening(cr, 14.0)
    core.src(cr, C["plaster_lo"])
    cr.fill()
    opening(cr, 4.0)
    core.src(cr, C["timber_dk"])
    cr.fill()
    opening(cr)
    cr.save()
    cr.clip()
    core.vgrad(cr, x, y, w, h, [C["night_lo"], C["night"], "#26365a"])
    cr.set_line_width(2.6)
    core.src(cr, C["lead"])
    step = 30.0
    for k in range(-14, 18):
        cr.move_to(x + k * step, y)
        cr.line_to(x + k * step + h * 0.55, y + h)
        cr.move_to(x + k * step, y)
        cr.line_to(x + k * step - h * 0.55, y + h)
    cr.stroke()
    core.src(cr, (0.85, 1.0, 0.95), 0.10)
    cr.paint()
    for k in range(6):
        core.src(cr, (1, 1, 1), 0.12)
        core.ellipse(cr, x + w * 0.66, y + 70 + k * 62, 5, 13)
        cr.fill()
    cr.restore()
    core.src(cr, C["timber_lt"])
    cr.rectangle(x - 18, y + h - 2, w + 36, 14)
    cr.fill()
    core.src(cr, C["timber_dk"], 0.5)
    cr.rectangle(x - 18, y + h + 12, w + 36, 6)
    cr.fill()


def window_rain(cr, t, x, y, w, h, n=26, seed=5):
    """The rain outside the leaded window: thin streaks falling behind the glass."""
    r = w / 2
    cr.save()
    cr.new_path()
    cr.move_to(x, y + h)
    cr.line_to(x, y + r)
    cr.arc(x + r, y + r, r, math.pi, 0)
    cr.line_to(x + w, y + h)
    cr.close_path()
    cr.clip()
    cr.set_line_width(1.4)
    for i in range(n):
        sp = 520.0 + 260.0 * core.hash01(i, seed)
        ph = core.hash01(i, seed + 1)
        yy = y - 40.0 + ((t * sp + ph * (h + 80.0)) % (h + 80.0))
        xx = x + core.hash01(i, seed + 2) * (w + 30.0) - 15.0 - (yy - y) * 0.12
        core.src(cr, "#9fb6d8", 0.30 + 0.25 * core.hash01(i, seed + 3))
        cr.move_to(xx, yy)
        cr.line_to(xx - 3.2, yy + 24.0)
        cr.stroke()
    cr.restore()


def _hot_spot(cr, x, y, r, a):
    """Baked orb light on the limewash: a soft, slightly egg-shaped bloom of brightness."""
    pat = core.radial(x, y, r, [(0.0, (1.0, 1.0, 1.0, a)), (0.35, (0.96, 1.0, 0.98, a * 0.45)),
                                (1.0, (0.92, 1.0, 0.96, 0.0))])
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, 1.25)
    cr.translate(-x, -y)
    cr.set_source(pat)
    cr.arc(x, y, r, 0, TAU)
    cr.fill()
    cr.restore()


def draw_back_A(cr):
    """The back wall: limewashed plaster between oak posts, a leaded window on the rainy night,
    pale flagstones on the customer side; the orbs' glare baked into the plaster."""
    _plaster(cr, -90, -80, 2100, 1240)
    for ox, oy, _s in ORBS:
        _hot_spot(cr, ox, oy + 40.0, 520.0, 0.55)
    _hot_spot(cr, 420.0, 120.0, 420.0, 0.35)
    _window(cr, *WINDOW_A)
    for x, w in ((300, 44), (712, 46), (1650, 46)):
        _timber(cr, x, -80, w, 1100)
    _timber(cr, -90, 700, 2100, 32, vertical=False)
    core.vgrad(cr, -90, 950, 2100, 290, [C["floor_lo"], C["floor"]])
    cr.set_line_width(2.0)
    core.src(cr, C["joint"], 0.5)
    for k in range(4):
        yy = 968 + k * k * 12 + k * 28
        cr.move_to(-90, yy)
        cr.line_to(2010, yy)
    for k in range(-6, 14):
        cr.move_to(960 + k * 150 * 0.3, 950)
        cr.line_to(960 + k * 150, 1240)
    cr.stroke()
    # the floor catches the glare too: a pale sheen under the customer's side
    _hot_spot(cr, 470.0, 1010.0, 380.0, 0.22)


def draw_shelves_A(cr):
    """The wall of jars behind the counter (prop-kit shelves), washed pale by the glare."""
    rig = P.draw_shelves(cr, SHELF_X, SHELF_Y, w=SHELF_W, h=SHELF_H, scale=SC, light=L, rows=4, seed=7, herbs=False)
    cr.save()
    cr.rectangle(SHELF_X - 40, SHELF_Y - 40, SHELF_W * SC + 80, SHELF_H * SC + 80)
    cr.clip()
    cr.set_operator(cairo.OPERATOR_SCREEN)
    core.src(cr, "#9fbcb2", 0.52)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)
    # glare from the orbs washes the upper shelves paler (the orbs themselves stay the hottest)
    for ox, oy, _s in ORBS:
        _hot_spot(cr, ox, oy + 70.0, 400.0, 0.26)
    cr.restore()
    env.draw_haze(cr, SHELF_X - 40, SHELF_Y - 40, SHELF_W * SC + 80, SHELF_H * SC + 80, C["haze"], 0.2, 0.07)
    return rig


def draw_beam(cr):
    """The low ceiling beam across the top of frame (the herbs hang from it)."""
    _timber(cr, -90, -80, 2100, BEAM_Y + 80, vertical=False, color=C["timber_dk"])
    core.src(cr, (0, 0, 0), 0.10)
    cr.rectangle(-90, BEAM_Y, 2100, 10)
    cr.fill()


def _glint(cr, x, y, w, a=1.0):
    for k, (al, ww, hh) in enumerate(((0.16, 1.0, 2.6), (0.42, 0.55, 1.2))):
        pat = core.linear(x - w * ww, y, x + w * ww, y, [(0.0, (1, 1, 1, 0.0)), (0.5, (0.93, 1.0, 0.97, al * a)),
                                                           (1.0, (1, 1, 1, 0.0))])
        cr.set_source(pat)
        core.ellipse(cr, x, y, w * ww, hh)
        cr.fill()


def _soft_blob(cr, x, y, rx, ry, color, alpha, additive=False):
    """A soft elliptical smear that fades to nothing at its rim (no hard edge anywhere)."""
    c = core.col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / rx)
    pat = core.radial(0.0, 0.0, rx, [(0.0, (c[0], c[1], c[2], alpha)), (0.35, (c[0], c[1], c[2], alpha * 0.6)),
                                      (0.7, (c[0], c[1], c[2], alpha * 0.18)), (1.0, (c[0], c[1], c[2], 0.0))])
    if additive:
        cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source(pat)
    cr.arc(0.0, 0.0, rx, 0, TAU)
    cr.fill()
    cr.restore()


def draw_counter_top(cr):
    """The polished oak top: a real plane from the back edge to the front lip, with the orbs
    mirrored in it as long soft streaks and a darker band where it meets the shelves' shadow."""
    x1 = 2100.0
    core.vgrad(cr, CX0, CBACK, x1 - CX0, CDEPTH, [C["oak_dk"], C["oak_top"], C["oak_lt"]])
    cr.save()
    cr.rectangle(CX0, CBACK, x1 - CX0, CDEPTH)
    cr.clip()
    env.texture(cr, "wood", 0.2, sx=5.0, sy=0.22)
    # reflections of the orbs in the waxed top: soft vertical smears with a hot core (a polished
    # surface seen at a grazing angle stretches what hangs above it into streaks)
    for ox, _oy, _s in ORBS:
        rx = ox + (ox - 960.0) * 0.06
        _soft_blob(cr, rx, CBACK + CDEPTH * 0.62, 30.0, CDEPTH * 0.62, "#e8fff6", 0.20)
        _soft_blob(cr, rx, CBACK + CDEPTH * 0.6, 9.0, CDEPTH * 0.34, "#ffffff", 0.32)
        _glint(cr, rx, CBACK + CDEPTH * 0.55, 54.0, 0.8)
    # the back edge: a crisp dark line where the top meets the shelf shadow
    core.src(cr, (0, 0, 0), 0.25)
    cr.rectangle(CX0, CBACK, x1 - CX0, 3)
    cr.fill()
    cr.restore()


def _linenfold(cr, x, y, w, h):
    """A carved linenfold panel: the classic medieval 'folded cloth' carving."""
    core.src(cr, C["oak_dk"])
    core.rounded_rect(cr, x, y, w, h, 5)
    cr.fill()
    core.src(cr, C["oak"])
    core.rounded_rect(cr, x + 5, y + 5, w - 10, h - 10, 4)
    cr.fill()
    n = 4
    fw = (w - 22) / n
    for i in range(n):
        fx0 = x + 11 + i * fw
        core.src(cr, C["oak_lt"], 0.75)
        core.rounded_rect(cr, fx0 + fw * 0.12, y + 22, fw * 0.32, h - 44, fw * 0.16)
        cr.fill()
        core.src(cr, C["oak_dk"], 0.6)
        core.rounded_rect(cr, fx0 + fw * 0.56, y + 22, fw * 0.3, h - 44, fw * 0.15)
        cr.fill()
    core.src(cr, C["oak_hi"], 0.25)
    cr.rectangle(x + 5, y + 5, w - 10, 2)
    cr.fill()


def draw_counter_front(cr):
    """The counter's front: a thick rounded lip catching the glare, then carved dark-oak linenfold."""
    x1 = 2100.0
    core.vgrad(cr, CX0 - 10, CTOP - 2, x1 - CX0 + 10, 26, [C["oak_hi"], C["oak_lt"], C["oak_dk"]])
    core.vgrad(cr, CX0, CTOP + 24, x1 - CX0, 1240 - CTOP, [C["oak"], C["oak_dk"]])
    cr.save()
    cr.rectangle(CX0, CTOP + 24, x1 - CX0, 1240 - CTOP)
    cr.clip()
    env.texture(cr, "wood", 0.2, sx=0.3, sy=3.0)
    core.src(cr, (0, 0, 0), 0.35)
    cr.rectangle(CX0, CTOP + 24, x1 - CX0, 10)
    cr.fill()
    px = CX0 + 26
    while px < x1:
        _linenfold(cr, px, CTOP + 50, 168, 196)
        px += 196
    cr.restore()
    # the lip's highlight streaks (the orbs again) and the shadowed end post
    for ox, _oy, _s in ORBS:
        _glint(cr, ox + (ox - 960.0) * 0.08, CTOP + 5.0, 90.0, 0.9)
    core.src(cr, C["oak_dk"])
    cr.rectangle(CX0 - 10, CTOP + 24, 12, 1240 - CTOP)
    cr.fill()


# ----------------------------------------------------------------------------------------
# living set dressing: herbs and the caged light-orbs
# ----------------------------------------------------------------------------------------

HERB_KINDS = {   # stem colour, head colour, head shape
    "lavender": ("#6c6a46", "#8c78b6", "spike"),
    "sage": ("#6a7052", "#97a78c", "leaf"),
    "yarrow": ("#6e6a4a", "#e4dec6", "umbel"),
    "rosemary": ("#5a5a3c", "#5a7452", "needle"),
    "tansy": ("#6a6a42", "#d0ae4c", "button"),
}


def _herb_art(cr, length, kind, light, seed):
    """One dense bundle of dried herbs hanging head-down, tied at (0, 0) (cached as a layer)."""
    stem_c, head_c, shape = HERB_KINDS[kind]
    sp = B.palette(light, B.Mat.of(stem_c))
    hp = B.palette(light, B.Mat.of(head_c))
    n = 17
    stems, heads, leaves = [], [], []
    for k in range(n):
        u = (k - (n - 1) / 2) / ((n - 1) / 2)
        a = u * 0.17 + core.jitter(k, 0.035, seed)
        Lk = length * (0.72 + 0.28 * core.hash01(k, seed + 1))
        bend = core.jitter(k, 6.0, seed + 2)
        p0, p1 = (u * 4.0, 14.0), (math.sin(a) * Lk * 0.55 + bend * 0.5, 14 + Lk * 0.55)
        p2 = (math.sin(a) * Lk + bend, 14 + math.cos(a) * Lk)
        stems.append([p0, p1, p2])
        heads.append((p2, a, k))
        for j in range(3):
            v = 0.35 + 0.18 * j + 0.05 * core.hash01(k * 7 + j, seed + 3)
            lx = p0[0] + (p2[0] - p0[0]) * v
            ly = p0[1] + (p2[1] - p0[1]) * v
            leaves.append((lx, ly, (1 if (k + j) % 2 else -1), a))
    B.detail_lines(cr, stems, 1.7, sp.shadow, 1.0, taper=(1.0, 1.0, 0.7))
    if shape in ("leaf", "needle", "spike"):
        for lx, ly, sgn, a in leaves:
            core.ellipse(cr, lx + sgn * 4.5, ly, 5.5 if shape == "leaf" else 3.2, 2.2, sgn * 0.9 - a)
        core.src(cr, core.mix(sp.shadow, hp.shadow, 0.5))
        cr.fill()
    for (hx, hy), a, k in heads:
        if shape == "spike":
            for j in range(6):
                core.ellipse(cr, hx + math.sin(a) * j * 3.6, hy - 14 + j * 4.2, 3.0, 3.9, -a)
        elif shape == "leaf":
            core.ellipse(cr, hx - 4, hy - 8, 5.0, 11.5, -a - 0.45)
            core.ellipse(cr, hx + 4, hy - 4, 5.0, 11.5, -a + 0.45)
        elif shape == "umbel":
            core.ellipse(cr, hx, hy, 10.5, 6.0, -a)
        elif shape == "needle":
            core.ellipse(cr, hx, hy - 12, 3.4, 16, -a)
        else:
            core.circle(cr, hx, hy, 5.2)
            core.circle(cr, hx + 5, hy - 7, 4.0)
    core.src(cr, hp.shadow)
    cr.fill()
    for (hx, hy), a, k in heads:
        if k % 3 == 2:
            continue
        if shape == "spike":
            for j in range(0, 6, 2):
                core.ellipse(cr, hx + math.sin(a) * j * 3.6 - 1.0, hy - 15 + j * 4.2, 1.9, 2.6, -a)
        elif shape == "umbel":
            core.ellipse(cr, hx - 2, hy - 1.5, 7.0, 3.6, -a)
        elif shape == "leaf":
            core.ellipse(cr, hx - 5, hy - 10, 2.6, 8.0, -a - 0.45)
        elif shape == "needle":
            core.ellipse(cr, hx - 1, hy - 14, 1.6, 11, -a)
        else:
            core.circle(cr, hx - 1.4, hy - 1.4, 3.0)
    core.src(cr, hp.lit)
    cr.fill()
    # the twine binding and its loop to the nail
    core.src(cr, "#8a7050")
    core.rounded_rect(cr, -7.5, 8.0, 15.0, 11.0, 3.0)
    cr.fill()
    core.src(cr, "#5a4632")
    cr.set_line_width(1.6)
    cr.move_to(-7.5, 12.0)
    cr.line_to(7.5, 12.5)
    cr.move_to(0.0, 8.0)
    cr.curve_to(-5.0, 2.0, 5.0, -3.0, 0.0, -4.0)
    cr.stroke()


class Herb:
    """A cached herb bundle that sways about its tie point."""

    def __init__(self, length, kind, seed, scale=1.0, blur=0.0):
        self.length, self.scale = length, scale
        pad = 40.0

        def art(c):
            c.scale(scale, scale)
            _herb_art(c, length, kind, L, seed)
        self.layer = fx.Layer(art, w=(2 * pad + 60) * scale, h=(length + 60) * scale,
                              x=-(pad + 30) * scale, y=-12 * scale, blur=blur)

    def draw(self, cr, x, y, sway):
        cr.save()
        cr.translate(x, y)
        cr.rotate(sway)
        self.layer.paint(cr)
        cr.restore()


# where the bundles hang on the beam (x, length, kind, seed): low enough that he must stoop
HERBS_A = [(52, 270, "sage", 1), (140, 300, "lavender", 2), (228, 250, "yarrow", 3), (318, 288, "rosemary", 4),
           (408, 206, "lavender", 5), (494, 236, "tansy", 6), (580, 204, "sage", 7), (664, 226, "yarrow", 8)]


def herb_sway(t, i, kick=None):
    s = 0.03 * math.sin(t * 0.7 + i * 1.3) + 0.018 * core.noise1(t * 0.4, i + 3)
    if kick is not None and t >= kick[0]:
        s += kick[1] * B.wobble(t, kick[0], freq=1.3, decay=1.4)
    return s


def draw_orb(cr, x, y, t, seed, scale=1.0, flick=0.0, chain_top=None):
    """A hanging light-orb: a white-hot disc with a thin, saturated mint rim, set in a dark ring
    (the cage's shadowed inside: it separates the core from the glare behind it, so the orb reads
    as a hard light source, not an empty globe) inside a heavy black-iron armillary cage -- a
    domed crown with a ring on the chain, a drop finial below -- and a ring of glowing runes
    orbiting it. Cold arcane light (never warm): the over-bright, clinical 'fluorescents' of this
    world. Returns the core centre."""
    sw = 0.018 * math.sin(t * 0.9 + seed * 1.7)
    top = (y - 80.0 * scale) if chain_top is None else chain_top
    x = x + (y - top) * sw
    lv = 1.0 - flick
    r = 19.0 * scale
    R = r * 1.55                                     # the cage
    iron, iron_hi = "#1a2124", "#5d6c71"
    crown_y = y - R - 2.0 * scale
    ring_y = crown_y - 13.0 * scale
    # the chain, down to the crown's ring
    cr.set_line_width(2.8 * scale)
    core.src(cr, iron)
    y_end = ring_y - 5.0 * scale
    n = max(2, int((y_end - top) / (9.0 * scale)))
    for k in range(n):
        u0, u1 = k / n, (k + 0.8) / n
        cr.move_to(lerp(x - (y - top) * sw, x, u0), lerp(top, y_end, u0))
        cr.line_to(lerp(x - (y - top) * sw, x, u1), lerp(top, y_end, u1))
    cr.stroke()
    rot = t * 0.35 + seed
    # back half of the cage's turning meridians
    cr.set_line_width(3.4 * scale)
    core.src(cr, iron, 0.9)
    cr.save()
    cr.translate(x, y)
    for k in range(3):
        a = rot + k * math.pi / 3
        rx = abs(math.cos(a)) * R + 0.5
        cr.save()
        cr.scale(max(rx, 0.6) / R, 1.0)
        cr.arc(0, 0, R, math.pi, TAU) if k % 2 else cr.arc(0, 0, R, 0, math.pi)
        cr.restore()
        cr.stroke()
    cr.restore()
    # the halo, then the dark inner ring, then the hard white disc with its saturated rim
    fx.glow(cr, x, y, r * 4.6, "#7fe8c2", 0.42 * lv)
    fx.glow(cr, x, y, r * 2.4, "#c8fff0", 0.22 * lv)
    pat = core.radial(x, y, R * 0.98, [(0.0, (0.06, 0.13, 0.12, 0.0)), (0.66, (0.06, 0.13, 0.12, 0.0)),
                                       (0.74, (0.06, 0.13, 0.12, 0.48)), (0.9, (0.06, 0.13, 0.12, 0.3)),
                                       (1.0, (0.06, 0.13, 0.12, 0.0))])
    cr.set_source(pat)
    core.circle(cr, x, y, R * 0.98)
    cr.fill()
    core.circle(cr, x, y, r * 1.1)
    core.src(cr, core.mix("#22d39a", "#4a6a62", flick), 1.0)
    cr.fill()
    pat = core.radial(x, y, r * 0.98, [(0.0, (1, 1, 1, 1)), (0.62, (1, 1, 1, 1)), (0.86, core.alpha("#f2fffa", 1.0)),
                                       (1.0, core.alpha("#c4f7e4", 1.0))])
    cr.set_source(pat)
    core.circle(cr, x, y, r * 0.98)
    cr.fill()
    if lv < 0.999:
        # the stutter: the core greys down for a frame or two
        core.src(cr, "#7f9a92", 0.6 * (1.0 - lv))
        core.circle(cr, x, y, r)
        cr.fill()
    cr.save()
    cr.translate(x, y)
    # the front meridians and a heavy equator band
    core.src(cr, iron)
    cr.set_line_width(4.2 * scale)
    cr.save()
    cr.scale(1.0, 0.32)
    cr.arc(0, 0, R, 0, math.pi)
    cr.restore()
    cr.stroke()
    cr.set_line_width(3.4 * scale)
    for k in range(3):
        a = rot + k * math.pi / 3
        rx = abs(math.cos(a)) * R + 0.5
        cr.save()
        cr.scale(max(rx, 0.6) / R, 1.0)
        cr.arc(0, 0, R, 0, math.pi) if k % 2 else cr.arc(0, 0, R, math.pi, TAU)
        cr.restore()
        cr.stroke()
    # the crown: a domed iron cap the meridians meet in, a ring for the chain; a drop finial below
    cw, ch_ = R * 0.62, R * 0.36
    cr.new_path()
    cr.move_to(-cw, crown_y - y + ch_ * 0.35)
    cr.curve_to(-cw, crown_y - y - ch_ * 0.9, cw, crown_y - y - ch_ * 0.9, cw, crown_y - y + ch_ * 0.35)
    cr.close_path()
    core.src(cr, iron)
    cr.fill_preserve()
    core.src(cr, iron_hi, 0.55)
    cr.set_line_width(1.2 * scale)
    cr.stroke()
    cr.set_line_width(3.0 * scale)
    core.src(cr, iron)
    cr.arc(0, ring_y - y + 1.0 * scale, 5.0 * scale, 0, TAU)
    cr.stroke()
    cr.new_path()
    cr.move_to(-4.0 * scale, R - 1.0 * scale)
    cr.curve_to(-4.5 * scale, R + 6.0 * scale, -1.5 * scale, R + 11.0 * scale, 0.0, R + 14.0 * scale)
    cr.curve_to(1.5 * scale, R + 11.0 * scale, 4.5 * scale, R + 6.0 * scale, 4.0 * scale, R - 1.0 * scale)
    cr.close_path()
    cr.fill()
    # the rune ring: bold glyphs orbiting the core on a faint track (bright in front, dim behind)
    core.src(cr, "#bdf8e2", 0.22 * lv)
    cr.set_line_width(1.2 * scale)
    cr.save()
    cr.scale(1.0, 0.22)
    cr.arc(0, 0, r * 2.4, 0, TAU)
    cr.restore()
    cr.stroke()
    cr.set_line_width(2.3 * scale)
    for k in range(8):
        a = t * 0.7 + seed + TAU * k / 8
        px, py = math.cos(a) * r * 2.4, math.sin(a) * r * 0.53
        front = math.sin(a) > 0
        core.src(cr, "#d2fff0" if front else "#9fdcc6", (0.95 if front else 0.32) * lv)
        g = 1.25 * scale
        cr.move_to(px - 2.8 * g, py - 3.6 * g)
        cr.line_to(px + 1.6 * g, py + 3.6 * g)
        cr.move_to(px + 2.8 * g, py - 3.6 * g)
        cr.line_to(px - 0.6 * g, py)
        cr.stroke()
    cr.restore()
    return (x, y)


# The 'buzzing fluorescent' nod: one orb that is IN FRAME stutters, at quiet moments -- once in the
# two-shot while she pockets his note, and once in the frozen-smile silence (shot D: the light on
# her face stutters with it). (shot, orb seed, start time)
STUTTERS = [("A", 1, 7.18), ("C", 0, None)]


def orb_flicker(t, seed, shot="A"):
    """How far orb `seed` has dimmed (0..1) at t in that shot's world."""
    for sh, sd, t0 in STUTTERS:
        if sh != shot or sd != seed:
            continue
        t0 = T_BUZZ if t0 is None else t0
        u = t - t0
        if 0.0 <= u < 0.3:
            # two quick dips and a half-hearted catch: bzz-bzzt
            return 0.62 * max(bump(u, 0.0, 0.03, 0.05), bump(u, 0.1, 0.02, 0.04), 0.5 * bump(u, 0.19, 0.03, 0.06))
    return 0.0


# ========================================================================================
# animation helpers
# ========================================================================================

def kf(t, keys, ease="inout_sine"):
    return core.track(t, keys, ease)


def _ease_arc(a, b, u, arc=0.0):
    """Screen-space move from a to b with an inout ease and a sideways arc (hands never travel
    in straight lines). arc > 0 bows the path up (for left-to-right moves)."""
    e = core.inout_sine(clamp(u))
    x, y = lerp(a[0], b[0], e), lerp(a[1], b[1], e)
    if arc:
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        k = math.sin(math.pi * e) * arc
        x, y = x + (dy / n) * k, y - (dx / n) * k * (1 if dx >= 0 else -1)
    return (x, y)


def expr_track(t, keys):
    """[(t, mood name | Expr), ...] -> an Expr blended smoothly between consecutive keys (repeat a key
    to hold it). Expressions never switch identity in one frame."""
    ks = [(k[0], B.expr(k[1]) if isinstance(k[1], str) else k[1]) for k in keys]
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, e0), (t1, e1) in zip(ks, ks[1:]):
        if t < t1:
            return e0.blend(e1, smooth((t - t0) / max(1e-6, t1 - t0)))
    return ks[-1][1]


def mix_expr(a, b, u):
    a = B.expr(a) if isinstance(a, str) else a
    b = B.expr(b) if isinstance(b, str) else b
    return a.blend(b, u)


def bump(t, t0, rise, fall, hold=0.0):
    """0 -> 1 -> 0 envelope starting at t0 (rise, hold, fall seconds)."""
    return core.window(t, t0, t0 + rise + hold + fall, rise, fall)


def hand_blend(a, b, u):
    """A hand shape part-way between two HAND_POSES (base.hand takes a dict), so fingers curl and
    uncurl over time instead of swapping shape in one frame."""
    pa = B.HAND_POSES[a] if isinstance(a, str) else a
    pb = B.HAND_POSES[b] if isinstance(b, str) else b
    u = clamp(u)
    if u <= 0.0:
        return a
    if u >= 1.0:
        return b
    return {"curl": tuple(lerp(x, y, u) for x, y in zip(pa["curl"], pb["curl"])),
            "spread": lerp(pa["spread"], pb["spread"], u),
            "thumb": tuple(lerp(x, y, u) for x, y in zip(pa["thumb"], pb["thumb"]))}


class Holder:
    """A hold(cr, frame) callback drawing a prop in a hand at exactly world scale `scale` (any
    rig's internal scale is compensated), upright, with its anchor `anchor` world px from the
    grip. magnet=(wx, wy, w): pull the anchor toward that world point by w (0..1), so pick-ups
    and set-downs land exactly where the prop rests before / after. `cam` maps world -> screen
    (a core.Camera, or an object with .zoom and .matrix())."""

    def __init__(self, draw_fn, cam, scale, anchor=(0.0, 0.0), magnet=None, upright=True, angle=0.0):
        self.draw_fn, self.cam, self.scale, self.anchor = draw_fn, cam, scale, anchor
        self.magnet, self.upright, self.angle = magnet, upright, angle
        self.world = None                    # where the anchor ended up (world coordinates)
        self.matrix, self.at = None, (0.0, 0.0)
        self.prev = None                     # the anchor's world position a frame ago (smear)

    def __call__(self, cr, f):
        cr.save()
        if self.upright:
            cr.rotate(-f.angle)
        m = cr.get_matrix()
        unit_dev = math.hypot(m.xx, m.yx)
        zoom = self.cam.zoom
        cr.scale(zoom / unit_dev, zoom / unit_dev)      # now 1 unit = 1 world px
        m = cr.get_matrix()
        inv = self.cam.matrix(1.0)
        inv.invert()
        gx, gy = inv.transform_point(*m.transform_point(0.0, 0.0))
        ax, ay = self.anchor
        if self.magnet is not None and self.magnet[2] > 0.0:
            w = clamp(self.magnet[2])
            ax += (self.magnet[0] - (gx + ax)) * w
            ay += (self.magnet[1] - (gy + ay)) * w
        self.world = (gx + ax, gy + ay)
        if self.angle:
            cr.translate(ax, ay)
            cr.rotate(self.angle)
            cr.translate(-ax, -ay)
        self.matrix, self.at = cr.get_matrix(), (ax, ay)
        if self.prev is not None and self.upright and not self.angle:
            # a fast move gets two faint multiples trailing it (a 2D animator's smear): the eye
            # reads one object travelling, not a jump
            dx, dy = self.prev[0] - self.world[0], self.prev[1] - self.world[1]
            d = math.hypot(dx, dy)
            if d > SMEAR_PX:
                k = clamp((d - SMEAR_PX) / 40.0)
                for f_, a_ in ((0.62, 0.16), (0.32, 0.3)):
                    cr.push_group()
                    self.draw_fn(cr, ax + dx * f_, ay + dy * f_)
                    cr.pop_group_to_source()
                    cr.paint_with_alpha(a_ * k)
        self.draw_fn(cr, ax, ay)
        cr.restore()

    def redraw(self, cr, below=None):
        """Draw the prop again exactly where the hand put it (e.g. over a counter clip): only the
        part below screen-y `below` (world) if given. Call after the holding character is drawn."""
        if getattr(self, "matrix", None) is None:
            return
        cr.save()
        if below is not None:
            cr.rectangle(-4000.0, below, 10000.0, 8000.0)
            cr.clip()
        cr.set_matrix(self.matrix)
        self.draw_fn(cr, *self.at)
        cr.restore()


# ----------------------------------------------------------------------------------------
# the remedies and the column
# ----------------------------------------------------------------------------------------

SMEAR_PX = 30.0          # a carried prop moving further than this in a frame trails two multiples
REM_H = {"sleep": 83.0, "vitamins": 64.0, "calm": 54.5, "book_up": 75.5}
# The column, in the order she builds it: (name, anchor y above the draught's base, scale-1
# units). The vitamin jar balances ON THE DRAUGHT'S CORK, the candle sits on the jar's linen
# dome, the coloring book stands on the candle's rim (its anchor is 6.5 above its lowest edge).
COLUMN = [("sleep", 0.0), ("vitamins", -82.0), ("calm", -145.5), ("book_up", -206.5)]
SEATS = [0.0, -82.0, -145.5, -200.0]       # the joint each item rests on (its contact point)
COLUMN_TOP = -282.0                        # the top of the standing book


def _draw_item_raw(cr, name, x, y, scale, t, angle, light):
    # the prop kit's labels are lettered for close-ups (6-8 px tall at this scale): every remedy
    # is drawn without its label and re-lettered for the screen (_s2_rig: bigger plates, bold
    # caps; the book's cover re-set with FOR ADULTS in capitals on a banner)
    if name == "calm":
        # unlit shop stock: draw_calm_candle shows a dying thread of smoke on a 3 s loop after
        # its flame goes out; at t=2.99 it has fully faded, so the stock candle never smokes
        rig = P.draw_calm_candle(cr, x, y, scale, light, 2.99, angle, lit=0.0, label=False)
        R2.draw_label_big(cr, "calm", x, y, scale, light, angle)
        return rig
    if name == "book_up":
        R2.draw_book_up(cr, x, y, scale, light, angle)                        # upright (no lean)
        return None
    rig = P.draw_remedy(cr, name, x, y, scale, light, t, angle, label=False)
    R2.draw_label_big(cr, name, x, y, scale, light, angle)
    return rig


def draw_item(cr, name, x, y, scale, t, angle=0.0, light=L, haze=0.0, sparkle=0.0):
    """One remedy standing on its bottom centre (x, y). haze > 0 tints it into the pale, glared
    shelf plane (only its own pixels: drawn into a tight group used as the wash's mask);
    sparkle > 0 adds the orbs' specular glint on its glass."""
    if haze <= 0.01:
        _draw_item_raw(cr, name, x, y, scale, t, angle, light)
    else:
        cr.save()
        cr.rectangle(x - 70.0 * scale, y - 110.0 * scale, 140.0 * scale, 130.0 * scale)
        cr.clip()
        cr.push_group()
        _draw_item_raw(cr, name, x, y, scale, t, angle, light)
        pat = cr.pop_group()
        cr.set_source(pat)
        cr.paint()
        core.src(cr, C["shelf_haze"], clamp(haze))
        cr.mask(pat)
        cr.restore()
    if sparkle > 0.01 and name != "book_up":
        off = {"sleep": (-11.0, -34.0), "vitamins": (-14.0, -40.0), "calm": (-15.0, -30.0)}[name]
        ca, sa = math.cos(angle), math.sin(angle)
        sx = x + (off[0] * ca - off[1] * sa) * scale
        sy = y + (off[0] * sa + off[1] * ca) * scale
        fx.sparkle(cr, sx, sy, 7.0 * scale, "#ffffff", sparkle, 0.3)


def twinkle(t, seed, period=3.1):
    """A specular glint that flares now and then (deterministic): 0..1."""
    ph = (t + core.hash01(seed, 71) * period) % period
    return bump(ph, 0.0, 0.12, 0.35) * (0.6 + 0.4 * core.hash01(int((t + core.hash01(seed, 71) * period) // period), seed))


def joint_angles(t):
    """The column's joints (rad): 0 = its base on the counter, 1 = the cork, 2 = the jar's dome,
    3 = the candle's rim. Each landing sets the joint below it rocking; the book teeters until
    her tap squares it."""
    a0 = (0.006 * B.wobble(t, T_ITEM[0], freq=4.0, decay=8.0) + 0.012 * B.wobble(t, T_ITEM[1], freq=2.4, decay=3.5)
          + 0.012 * B.wobble(t, T_ITEM[2], freq=2.2, decay=3.5) + 0.016 * B.wobble(t, T_ITEM[3], freq=1.5, decay=1.8))
    a1 = 0.06 * B.wobble(t, T_ITEM[1], freq=1.7, decay=2.6)                  # the jar balancing on the cork
    a2 = 0.03 * B.wobble(t, T_ITEM[2], freq=2.3, decay=3.4)
    a3 = 0.0
    if t >= T_ITEM[3]:
        teeter = 0.075 * B.wobble(t, T_ITEM[3], freq=1.35, decay=1.5)
        if t >= T_TAP:
            at_tap = 0.075 * B.wobble(T_TAP, T_ITEM[3], freq=1.35, decay=1.5)
            teeter = at_tap * (1.0 - smooth((t - T_TAP) / 0.07)) + 0.012 * B.wobble(t, T_TAP, freq=6.0, decay=11.0)
            a0 += 0.004 * B.wobble(t, T_TAP, freq=5.0, decay=9.0)
        a3 = teeter
    return (a0, a1, a2, a3)


def settle_dy(t, k):
    """A landed item's tiny squash-settle (scale-1 px): it arrives a hair high and sinks in."""
    tk = T_ITEM[k]
    if t < tk:
        return 0.0
    return -2.5 * (1.0 - smooth((t - tk) / 0.07))


def column_xf(cr, t, k, base, scale, angles=None):
    """Transform cr to item k's seat in the column (base = the draught's bottom centre)."""
    a = joint_angles(t) if angles is None else angles
    cr.translate(base[0], base[1])
    cr.rotate(a[0])
    for j in range(1, k + 1):
        cr.translate(0.0, (SEATS[j] - SEATS[j - 1]) * scale)
        cr.rotate(a[j])


def column_point(t, k, local, base, scale, angles=None):
    """World position of a point given in item k's seat frame (scale-1 units)."""
    m = cairo.Matrix()
    a = joint_angles(t) if angles is None else angles
    m.translate(base[0], base[1])
    m.rotate(a[0])
    for j in range(1, k + 1):
        m.translate(0.0, (SEATS[j] - SEATS[j - 1]) * scale)
        m.rotate(a[j])
    return m.transform_point(local[0] * scale, local[1] * scale)


def item_anchor_local(k):
    """Item k's anchor in its seat frame (scale-1 units)."""
    return (0.0, COLUMN[k][1] - SEATS[k])


def draw_column(cr, t, n_on, base, scale, light=L, skip=(), sparkle=True, shadow=True):
    """The items already on the column (indices < n_on, not in skip), bottom to top."""
    ang = joint_angles(t)
    if shadow:
        B.contact_shadow(cr, base[0], base[1] + 1.5 * scale, 30.0 * scale, 5.0 * scale, alpha=0.42)
    for k in range(n_on):
        if k in skip:
            continue
        name = COLUMN[k][0]
        cr.save()
        column_xf(cr, t, k, base, scale, ang)
        ax, ay = item_anchor_local(k)
        if k == 3:
            # the tap that squares it: two frames squashed sideways against her fingertip
            sq = bump(t, T_TAP - 0.01, 0.02, 0.05, 0.035)
            if sq > 0.0:
                cr.scale(1.0 - 0.055 * sq, 1.0 + 0.025 * sq)
        if k > 0:
            # a soft contact shade where it rests on the item below
            B.occlusion(cr, 0.0, 2.0 * scale, 14.0 * scale, 4.0 * scale, (0.1, 0.12, 0.12), 0.25)
        draw_item(cr, name, ax * scale, (ay + settle_dy(t, k)) * scale, scale, t, 0.0, light,
                  sparkle=twinkle(t, 11 + k) if sparkle else 0.0)
        cr.restore()


def n_on_column(t):
    return sum(1 for tk in T_ITEM if t >= tk)


def draw_note_flat(cr, x, y, scale, t, unfold=0.0, tilt=FLAT, angle=0.0, light=L):
    """The note lying on the counter: its plane foreshortened by tilt (1 = facing us)."""
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, max(0.05, tilt))
    P.draw_note(cr, 0.0, 0.0, scale, light, t, angle, unfold)
    cr.restore()


# ========================================================================================
# THE LIONESS: choreography (shot A world)
# ========================================================================================
LIO_SIZE_K = LIO_MOD.SIZE_K
I0, I1, I2, I3 = T_ITEM

# Her faces. A cat with heavy lids and a raised lower lid reads smug or sly, so every warm
# expression here keeps the eyes OPEN: the kindness is in the brows and the mouth.
LIO_WELCOME = B.Expr(brow_in=0.3, brow_out=0.12, brow_y=0.2, lid=0.14, lid_bot=0.1, lid_tilt=0.08, smile=0.36, cheek=0.2)
LIO_READ = B.Expr(brow_in=0.35, brow_out=0.22, brow_y=0.3, lid=0.17, lid_bot=0.05, lid_tilt=0.05, smile=0.04)
LIO_SYMPATHY = B.Expr(brow_in=0.9, brow_out=-0.05, brow_y=0.3, lid=0.1, lid_bot=0.04, lid_tilt=0.34, smile=0.12,
                      pupil=1.15)
LIO_KIND = B.Expr(brow_in=0.55, brow_out=0.06, brow_y=0.26, lid=0.12, lid_bot=0.08, lid_tilt=0.2, smile=0.44,
                  cheek=0.25, pupil=1.1)
LIO_BUSY = B.Expr(brow_in=0.22, brow_out=0.34, brow_y=0.34, lid=0.08, lid_bot=0.14, lid_tilt=-0.02, smile=0.56,
                  cheek=0.38)
LIO_STEADY = B.Expr(brow_in=0.7, brow_out=0.1, brow_y=0.35, lid=0.04, lid_bot=0.04, lid_tilt=0.1, smile=0.2, pupil=0.85)
LIO_PROUD = B.Expr(brow_in=0.2, brow_out=0.36, brow_y=0.36, lid=0.1, lid_bot=0.2, lid_tilt=-0.04, smile=0.66, cheek=0.5)
PICK_X = 905.0                    # she steps over to him to take the note
PLACE_X = PILE_X + 185.0          # where she stands to set things on the column: an easy, open reach
                                  # (closer in, her paw would be right under her shoulder and spin)
PLACE3_X = PILE_X + 205.0         # the candle goes on at her face height: a step further off, so her
                                  # big head never hides the paw (her far arm draws under it)
BOOK_X = PILE_X + 195.0           # she crowns the column with the book from a step off (a long reach on
                                  # tiptoe), so there is room for her paw between the book and her face
TAP_X = PILE_X + 212.0            # the book teeters: she eases back a little more, and the paw that
                                  # steadies it hovers BESIDE the book, clear of her face
SHELF_SPOT = {"sleep": (1218.0, BOARDS[2]), "vitamins": (1352.0, BOARDS[2]), "calm": (1262.0, BOARDS[1])}
SHELF_STAND = {"sleep": 1150.0, "vitamins": 1284.0, "calm": 1168.0}
R_ARM, L_ARM = -1.0, 1.0          # her right arm (fetches, facing left it is the FAR arm), her left arm

T_PICK = T_GO + 0.3               # her right paw closes on the note on the counter
T_READ = T_GO + 0.62              # both paws hold it up to read (read_note)
T_LOWER = CUT_A2 + 0.35           # back in the two-shot: she lowers it, looks over her specs
T_SWITCH = T_NOD + 0.5            # the note passes to her left paw ...
T_POCKET = T_SWITCH + 0.48        # ... which tucks it into her apron pocket (behind the counter)
T_BACK = T_POCKET + 0.37

# each fetch: (t_grab, t_set) -- the item rests on its shelf before t_grab, rides in her right
# paw between, and is on the column from t_set (= its s2_itemN beat: the thunk). The paw keeps
# hold of it for HOLD_AFTER more (the magnet pins it to its seat) and only then opens.
TRIPS = [(I0 - 1.12, I0), (I1 - 1.12, I1), (I2 - 1.22, I2), (I3 - 1.25, I3)]
HOLD_AFTER = 0.1
BOOK_DUCK0, BOOK_DUCK1 = I3 - 1.48, I3 - 0.95     # she ducks below the counter for the book
CARRY_IN = 0.36           # after the grab, the item is in at her chest (she still faces the shelf)

# Her turns, (t0, from yaw, to yaw, duration): out to the shelves in ~9 frames; back WITH an item in
# ~11, starting only as it comes in to her chest, so it rides round with her body (it never swings
# across her on its own). The eyes lead by ~0.22 s and the head by ~0.13 s, with a little dip of
# anticipation before each turn.
TURNS = [(T_POCKET - 0.14, -1.0, 1.15, 0.4), (TRIPS[0][0] + 0.24, 1.15, -1.05, 0.54),     # trip 1: out, back
         (I0 + 0.14, -1.05, 1.15, 0.38), (TRIPS[1][0] + 0.24, 1.15, -1.05, 0.54),           # trip 2
         (I1 + 0.14, -1.05, 1.12, 0.38), (TRIPS[2][0] + 0.4, 1.12, -1.05, 0.52)]            # trip 3


def _turn_end(i):
    return TURNS[i][0] + TURNS[i][3]


def _yaw_keys():
    keys = [(0.0, -1.0)]
    for t0, a, b, d in TURNS:
        keys += [(t0, a), (t0 + d, b)]
    return keys + [(DUR, -1.05)]


LIO_YAW = _yaw_keys()
LIO_X = [(0.0, HOME), (T_GO - 0.3, HOME), (T_GO + 0.12, PICK_X),
         (T_SWITCH, PICK_X), (TURNS[0][0], PICK_X + 20.0),
         (TURNS[0][0] + 0.48, SHELF_STAND["sleep"]), (TRIPS[0][0] + 0.18, SHELF_STAND["sleep"]),
         (I0 - 0.16, PLACE_X), (I0 + 0.16, PLACE_X),
         (TRIPS[1][0] - 0.08, SHELF_STAND["vitamins"]), (TRIPS[1][0] + 0.18, SHELF_STAND["vitamins"]),
         (I1 - 0.16, PLACE_X), (I1 + 0.16, PLACE_X),
         (TRIPS[2][0] - 0.3, SHELF_STAND["calm"]), (TRIPS[2][0] + 0.36, SHELF_STAND["calm"]),
         (I2 - 0.2, PLACE3_X), (I2 + 0.32, PLACE3_X), (BOOK_DUCK0 + 0.3, BOOK_X),
         (I3 + 0.06, BOOK_X), (I3 + 0.42, TAP_X), (T_ITEMS1, TAP_X + 4.0)]
LIO_LIFT = [(0.0, 0.0), (TRIPS[2][0] - 0.38, 0.0), (TRIPS[2][0] - 0.1, -12.0), (TRIPS[2][0] + 0.15, -12.0),
            (TRIPS[2][0] + 0.4, 0.0), (BOOK_DUCK0, 0.0), (BOOK_DUCK0 + 0.28, 105.0), (BOOK_DUCK1 - 0.18, 105.0),
            (BOOK_DUCK1 + 0.26, 0.0), (I3 - 0.55, -15.0), (I3 + 0.1, -15.0), (I3 + 0.42, -6.0),
            (T_TAP + 0.25, -6.0), (T_TAP + 0.6, 0.0)]
LIO_LEAN = [(0.0, 0.0), (T_GO - 0.15, 0.0), (T_PICK, 0.32), (T_READ, 0.05), (BOOK_DUCK0, 0.0),
            (BOOK_DUCK0 + 0.28, 0.6), (BOOK_DUCK1 - 0.18, 0.6), (BOOK_DUCK1 + 0.26, 0.0)]


def lio_screen(x0, y0, yaw, p, scale=SC, elev=LIO_MOD.ELEV):
    """Body-space point of the lioness drawn at (x0, y0, scale) -> world."""
    pr = B.Proj(yaw, elev)
    px, py = pr.xy(p)
    k = scale * LIO_SIZE_K
    return (x0 + px * k, y0 + py * k)


def lio_gesture(x0, y0, yaw, pose, t, side, g, phase=0.0, scale=SC):
    """World position of a library gesture's wrist target (so blends happen in screen space).
    Uses the rig's own skeleton (private API: if the rig changes, this fails loudly)."""
    S = LIO_MOD._skeleton(pose, t, yaw)
    tgt = LIO_MOD.LIONESS_GESTURES[g](S["shoulders"][side], side, dict(S["ctx"], phase=phase))[0]
    return lio_screen(x0, y0, yaw, tgt, scale, pose.elev)


def lio_shoulder(x0, y0, yaw, pose, t, side, scale=SC):
    S = LIO_MOD._skeleton(pose, t, yaw)
    return lio_screen(x0, y0, yaw, S["shoulders"][side], scale, pose.elev)


def paw_track(t, keys, resolve):
    """A paw's path through keys [(t, spec, hand[, arc])]: spec = a gesture name (resolved on the
    CURRENT body, so it rides along with her), a world point, or a callable(t) -> point. Returns
    (gesture_name or None, world point or None, hand pose). Between two keys of the same gesture
    the gesture itself is returned (the rig's own idle applies); otherwise an eased, arcing
    screen-space path from wherever the paw is to wherever it is going -- nothing ever snaps.
    The hand shape blends over the segment's last quarter (fingers curl / open, never pop)."""
    def real(s):
        return isinstance(s, str) and s in LIO_GESTURE_NAMES

    if t <= keys[0][0]:
        k = keys[0]
        return (k[1], None, k[2]) if real(k[1]) else (None, resolve(k[1], t), k[2])
    for a, b in zip(keys, keys[1:]):
        if t < b[0]:
            u = (t - a[0]) / max(1e-6, b[0] - a[0])
            hand = a[2] if a[2] == b[2] else hand_blend(a[2], b[2], smooth((u - 0.55) / 0.45))
            if real(a[1]) and a[1] == b[1]:
                return a[1], None, hand
            arc = b[3] if len(b) > 3 else 14.0
            return None, _ease_arc(resolve(a[1], t), resolve(b[1], t), u, arc), hand
    k = keys[-1]
    return (k[1], None, k[2]) if real(k[1]) else (None, resolve(k[1], t), k[2])


LIO_GESTURE_NAMES = frozenset(LIO_MOD.LIONESS_GESTURES)


def grip_h(name):
    """Where her paw holds an item: its middle (scale-1 units above the anchor)."""
    return 34.5 if name == "book_up" else REM_H[name] * 0.45


def seat_anchor(t, k, base=(PILE_X, PILE_Y), scale=SC):
    """World position of item k's anchor when it sits on the column."""
    return column_point(t, k, item_anchor_local(k), base, scale)


def _carry_high(t, k):
    """Item k held just right of the column and clear above its current top, ready to be set on it
    from above (the column stands in front of her: anything carried lower passes behind it)."""
    ax, ay = seat_anchor(t, k)
    return (ax + 62.0, ay - grip_h(COLUMN[k][0]) * SC - 8.0)


GRIP_OFF = {}             # setup(): wrist target minus grip point at each shelf grab / set-down
TAP_OFF = {}              # setup(): wrist target minus the middle fingertip of the flat paw at the tap


def _shelf_wrist(k):
    """The wrist target that closes her grip on item k's middle where it stands on its shelf."""
    name = COLUMN[k][0]
    sx, sy = SHELF_SPOT[name]
    ox, oy = GRIP_OFF.get(("shelf", k), (-6.0, 30.0))
    return (sx + ox, sy - grip_h(name) * SC + oy)


def _shelf_lift(k):
    """Just lifted off its shelf (the item clears the board before it travels)."""
    wx, wy = _shelf_wrist(k)
    return (wx - 4.0, wy - 16.0)


def _seat_wrist(t, k, dx=24.0, dy=26.0):
    """The wrist target that puts her grip on item k's middle as it sits on the column (solved through
    the rig, so the paw really holds it); (dx - 24, dy - 26) is a small approach offset."""
    ax, ay = seat_anchor(t, k)
    ox, oy = GRIP_OFF.get(("seat", k), (24.0, 26.0))
    return (ax + ox + (dx - 24.0), ay - grip_h(COLUMN[k][0]) * SC + oy + (dy - 26.0))


def _carry_body(t, drop=0.0):
    """Her right paw carrying something in front of her: a point in her BODY space, from the
    facing direction, so through a turn it rides round with her (it never hops from one hip to the
    other), low enough to stay clear of her collar and big head. -> (point, skeleton, x, y0, yaw, pose)"""
    x, y0, yaw, pose = lio_state_A(t)
    S = LIO_MOD._skeleton(pose, t, yaw)
    f = CK.facing_dir(yaw)
    p = B.v_add(S["chest"], (R_ARM * 10.0 + f[0] * 30.0, 36.0 + drop, 30.0 + f[2] * 12.0))
    return p, S, x, y0, yaw, pose


def _carry_pt(t, drop=0.0):
    p, _S, x, y0, yaw, pose = _carry_body(t, drop)
    return lio_screen(x, y0, yaw, p, SC, pose.elev)


def _carry_depth(t, drop=0.0):
    """The carry point's TRUE camera depth ahead of her right shoulder (body units). Given to the
    arm together with the projected point, it puts the paw exactly on the 3D carry point, so the
    arm moves smoothly with her body through the turn (the screen-space depth guess flips the elbow
    -- and spins the paw half round in one frame -- when the paw passes close to her shoulder)."""
    p, S, _x, _y0, yaw, pose = _carry_body(t, drop)
    pr = B.Proj(yaw, pose.elev)
    return pr.depth(p) - pr.depth(S["shoulders"][R_ARM])


CARRY_OUT = {0: (0.22, 0.04), 1: (0.22, 0.04), 2: (0.2, 0.04)}   # (start, end) of the hand-back, before ts


def _carry_phase(t):
    """(weight 0..1, drop, dz): how far her right paw's depth follows the true carry point (plus dz
    body units further forward) -- fully through each carry and on up over the column, easing in
    from the shelf and handing back to the reach depth only on the way DOWN to the set-down, where
    the paw is far from her shoulder and depth hardly moves it. Handed back while the paw still
    rose past her shoulder, the projected forearm swung through the view axis and the paw (and
    what it held) spun round in a frame or two."""
    for k in range(3):
        tg, ts = TRIPS[k]
        t0 = tg + (0.0 if k == 2 else 0.08)
        t_in = tg + (0.42 if k == 2 else CARRY_IN)
        t_out, t_end = ts - CARRY_OUT[k][0], ts - CARRY_OUT[k][1]
        drop = -14.0 if k == 2 else 0.0
        if t0 <= t < t_end:
            w = smooth((t - t0) / (t_in - t0)) * (1.0 - smooth((t - t_out) / (t_end - t_out)))
            return w, drop, 0.0
    tg = TRIPS[3][0]
    a, b, c = BOOK_DUCK1 - 0.18, BOOK_DUCK1 + 0.26, I3 - 0.2
    if tg <= t < c:
        b2 = b + 0.12
        w = smooth((t - tg) / (a - tg)) * (1.0 - smooth((t - b2) / (c - b2)))
        drop = lerp(60.0, 0.0, core.inout_sine(clamp((t - a) / (b - a))))
        # the book comes up past her shoulder held a little further out in front of her, so her
        # forearm turns from down to up over five frames instead of flipping in one
        dz = 15.0 * smooth((t - a) / (b - a))
        return w, drop, dz
    return 0.0, 0.0, 0.0


def _r_depth(x, y0, yaw, pose, t, target, base=30.0):
    """Her right paw's camera depth (body units ahead of its shoulder) for a screen target: one
    that keeps the elbow comfortably bent. A target close to the shoulder ON SCREEN is reached
    forward, toward the camera -- otherwise the arm folds back along the view axis, the projected
    forearm shrinks to nothing and the paw spins (the grip jumped 120 px in one frame)."""
    sx, sy = lio_shoulder(x, y0, yaw, pose, t, R_ARM)
    k = SC * LIO_SIZE_K
    d2 = math.hypot(target[0] - sx, (target[1] - sy) / _ELEV_C) / k
    # keep the arm ~85 % extended (3D reach 120 of its 142): folded tighter, the elbow drops below
    # a rising wrist and the forearm -- and the paw with what it holds -- swings round in a frame
    want = math.sqrt(max(0.0, REACH_3D ** 2 - d2 ** 2))
    return max(base, min(100.0, want))


REACH_3D = 120.0


def _solve_A(t, goal, hand="grip", point="grip", iters=8):
    """Shot A: the (wrist target - goal) offset that puts her right paw's grip point (or, with
    point="tip", its middle fingertip) exactly on `goal` (world) at time t: a damped Newton solve
    through the real rig, drawn off-screen (the paw's angle depends on the wrist, so a plain
    fixed-point update can oscillate). Asserts the residual is under 3 px."""
    x, y0, yaw, lp = lio_state_A(t)
    _s, scr = core.frame(8, 8)

    def measure(w):
        arm = ch.LionessArm("place", screen=w, hand=hand, depth=_r_depth(x, y0, yaw, lp, t, w))
        near, far = (arm, ch.LionessArm("rest")) if yaw >= 0 else (ch.LionessArm("rest"), arm)
        rig = ch.draw_lioness(scr, x, y0, SC, lp.with_(near=near, far=far), LL, t)
        hf = rig.hand_near if yaw >= 0 else rig.hand_far
        if point == "index":
            return hf.tips[0]
        return hf.tips[1] if point == "tip" else (hf.x, hf.y)
    w = newton2(measure, (goal[0] + 24.0, goal[1] + 26.0), goal, iters)
    return (w[0] - goal[0], w[1] - goal[1])


def newton2(measure, w, goal, iters=8, tol=0.4, check=3.0):
    """Find w with measure(w) == goal (2D) by damped Newton steps with a finite-difference Jacobian."""
    for _ in range(iters):
        p = measure(w)
        ex, ey = goal[0] - p[0], goal[1] - p[1]
        if math.hypot(ex, ey) < tol:
            return w
        px = measure((w[0] + 2.0, w[1]))
        py = measure((w[0], w[1] + 2.0))
        a, b = (px[0] - p[0]) / 2.0, (py[0] - p[0]) / 2.0
        c, d = (px[1] - p[1]) / 2.0, (py[1] - p[1]) / 2.0
        det = a * d - b * c
        if abs(det) < 1e-6:
            sx, sy = ex * 0.5, ey * 0.5
        else:
            sx, sy = (d * ex - b * ey) / det, (-c * ex + a * ey) / det
        n = math.hypot(sx, sy)
        if n > 60.0:
            sx, sy = sx * 60.0 / n, sy * 60.0 / n
        w = (w[0] + 0.85 * sx, w[1] + 0.85 * sy)
    p = measure(w)
    res = math.hypot(goal[0] - p[0], goal[1] - p[1])
    assert res < check, f"paw solve did not converge: residual {res:.1f} px"
    return w


def _glide(t):
    """Her walk amount: an eased envelope of her speed (it never snaps on with the first step),
    capped low -- her legs are hidden behind the counter; she glides with her paws held (the rig
    lets the arms hang and swing only above walk 0.3)."""
    acc = 0.0
    for dt in (-0.14, -0.07, 0.0, 0.07, 0.14):
        acc += abs(kf(t + dt + 0.03, LIO_X) - kf(t + dt - 0.03, LIO_X)) / 0.06
    return 0.28 * core.smoothstep(30.0, 240.0, acc / 5.0)


def _look_y_keys():
    """Her vertical gaze through the trips: the shelf, then the landing spot, then a glance to him."""
    shelf_y = (0.25, 0.25, -0.7, 0.75)
    keys = [(T_ITEMS0 - 0.3, -0.12)]
    for k, (tg, ts) in enumerate(TRIPS):
        ay = seat_anchor(ts, k)[1] - REM_H[COLUMN[k][0]] * 0.5 * SC
        land = clamp((ay - 420.0) / 300.0, -0.8, 0.6)
        keys += [(tg - 0.5, shelf_y[k]), (tg + 0.06, shelf_y[k]), (tg + 0.22, land), (ts, land),
                 (ts + 0.14, -0.08)]
    return sorted(keys)


def lio_state_A(t):
    """(x, y0, yaw, pose) of the lioness in shot A at time t (arms not set yet)."""
    x = kf(t, LIO_X)
    yaw = kf(t, LIO_YAW)
    lift = kf(t, LIO_LIFT)
    # a little dip of anticipation before each turn
    lift += 5.0 * sum(bump(t, t0 - 0.12, 0.1, 0.16) for t0, _a, _b, _d in TURNS)
    walk = _glide(t)
    dist = 0.0
    for (t0, v0), (t1, v1) in zip(LIO_X, LIO_X[1:]):
        if t <= t0:
            break
        dist += abs(kf(min(t, t1), LIO_X) - v0)
    stride = ch.lioness_stride(SC, 1, 0.75)
    phase = (dist / max(1.0, stride)) % 1.0
    facing, turn = -1, (yaw + 1.0) / 0.6
    # the head leads every turn (and the eyes lead the head)
    hturn = clamp(0.82 * (kf(t + 0.13, LIO_YAW) - yaw), -1.0, 1.0)
    talk = tl.talk(SCENE, t, "PHARMACIST")
    # her face and eyes. One continuous expression track (no switches): professional welcome ->
    # reading -> the meaning lands (sympathy: brows knit up, eyes open) -> a kind nod with a cat's
    # slow blink -> "I know just the thing!" (bright, eager, eyes wide -- never a smug squint)
    mood = expr_track(t, [(0.0, LIO_WELCOME), (T_PICK, LIO_WELCOME), (T_READ, LIO_READ), (CUT_A2, LIO_READ),
                          (T_LOWER, mix_expr(LIO_READ, LIO_SYMPATHY, 0.85)), (T_LOWER + 0.12, LIO_SYMPATHY),
                          (T_NOD - 0.05, LIO_SYMPATHY), (T_NOD + 0.45, LIO_KIND), (T_BACK - 0.1, LIO_KIND),
                          (T_ITEMS0 + 0.15, LIO_BUSY)])
    look, specs, nod, tilt, blink = (-0.55, 0.05), 0.0, 0.0, 0.0, None
    if T_SLIDE - 0.1 <= t < T_GO + 0.3:
        look = (-0.55, 0.7)                                  # the note coming across the counter
    elif T_GO + 0.3 <= t < T_LOWER:
        look = (-0.1, 0.55)                                  # reading it
        specs = smooth((t - (T_READ - 0.2)) / 0.25)
    if CUT_A2 <= t:
        specs = 1.0 - smooth((t - (T_LOWER - 0.15)) / 0.35)
        look = core.lerp_tuple((-0.1, 0.55), (-0.62, -0.18), smooth((t - (T_LOWER - 0.2)) / 0.3))
        # the head tips in sympathy, then the slow, kind nod -- with a slow blink (a cat's "I see you")
        tilt = 0.09 * bump(t, T_LOWER - 0.05, 0.3, 0.45, T_NOD - T_LOWER + 0.2)
        nod = -0.75 * bump(t, T_NOD - 0.1, 0.32, 0.5, 0.1)
        if T_NOD - 0.06 <= t < T_NOD + 0.62:
            blink = bump(t, T_NOD - 0.04, 0.17, 0.3, 0.1)
    if t >= T_ITEMS0 - 0.3:
        # the eyes lead her turns (sideways: toward where she is about to face); vertically they go
        # to the shelf, then the landing spot, then a quick smile to him after each set-down
        lx = 0.55 * clamp(kf(t + 0.22, LIO_YAW) / 1.1, -1.0, 1.0)
        ly = kf(t, LOOK_Y)
        look = core.lerp_tuple(look, (lx, ly), smooth((t - (T_ITEMS0 - 0.3)) / 0.3))
        tg2 = TRIPS[2][0]
        nod = 0.4 * bump(t, tg2 - 0.5, 0.2, 0.25, 0.3)       # up to the high shelf
        nod += 0.35 * bump(t, TRIPS[3][0] + 0.3, 0.3, 0.3, I3 - TRIPS[3][0] - 0.6)
        if I3 <= t < T_TAP + 0.1:
            look = core.lerp_tuple(look, (-0.42, -0.5), smooth((t - I3) / 0.2))   # watching the book teeter
            mood = expr_track(t, [(I3, LIO_BUSY), (I3 + 0.25, LIO_STEADY), (T_TAP, LIO_STEADY)])
            nod = 0.3 * smooth((t - I3) / 0.25)
        elif t >= T_TAP + 0.1:
            look = core.lerp_tuple((-0.42, -0.5), (-0.6, -0.05), smooth((t - (T_TAP + 0.1)) / 0.4))
            mood = expr_track(t, [(T_TAP + 0.1, LIO_STEADY), (T_TAP + 0.4, LIO_PROUD)])
            nod = 0.3 * (1.0 - smooth((t - (T_TAP + 0.1)) / 0.4))
    pose = ch.LionessPose(facing=facing, turn=turn, walk=walk, phase=phase, talk=talk, mood=mood, look=look,
                          specs=specs, head_nod=nod, head_tilt=tilt, head_turn=hturn, blink=blink,
                          lean=kf(t, LIO_LEAN), seed=2, tail_swing=0.25 * math.sin(t * 0.8))
    return x, LIO_Y + lift, yaw, pose


def lio_arms_A(t, x, y0, yaw, pose, cam, note_cb):
    """Both paws in shot A -> (near LionessArm, far LionessArm, held item index or None)."""
    def resolve_r(spec, tt):
        return lio_resolve(spec, tt, x, y0, yaw, pose, R_ARM)

    def resolve_l(spec, tt):
        return lio_resolve(spec, tt, x, y0, yaw, pose, L_ARM)

    held = None
    hold_r = hold_l = None
    # ---- the note: her right paw picks it up, both read it, her left paw pockets it
    if T_PICK - 0.02 <= t < T_READ:
        hold_r = note_cb
    # ---- the items in her right paw (pinned to their seat for HOLD_AFTER while the paw opens)
    for k, (tg, ts) in enumerate(TRIPS):
        if tg <= t < ts + HOLD_AFTER:
            held = k
            name = COLUMN[k][0]
            if k < 3:
                sx, sy = SHELF_SPOT[name]
                mag_from = (sx, sy, 1.0 - smooth((t - tg) / 0.3))
            else:
                mag_from = None
            ax, ay = seat_anchor(t, k)
            u_set = smooth((t - (ts - 0.18)) / 0.18)
            magnet = (ax, ay, u_set) if u_set > 0 else mag_from
            haze = 0.5 * (1.0 - smooth((t - tg) / 0.45)) if k < 3 else 0.0
            hold_r = Holder(lambda c, px, py, n=name, hz=haze: draw_item(c, n, px, py, SC, t, 0.0, L, hz),
                            cam, SC, (0.0, grip_h(name) * SC), magnet)
    g_r, p_r, h_r = paw_track(t, RIGHT_KEYS, resolve_r)
    g_l, p_l, h_l = paw_track(t, LEFT_KEYS, resolve_l)
    if T_SWITCH <= t < T_POCKET + 0.02:
        hold_l = note_cb
    two = T_READ <= t < T_SWITCH
    if two:
        # both paws on the note (the library's two-hand hold draws it between them)
        r = ch.LionessArm("read_note", screen=p_r, hold=note_cb, hand="pinch")
        lft = ch.LionessArm("read_note", screen=p_l, hand="pinch")
    else:
        # coming down off the tower after the tap, the paw stays out in front of her (more depth):
        # the arm stays long, so the elbow never flips over as the wrist passes under the shoulder
        dep = 30.0 + 30.0 * bump(t, T_TAP + 0.1, 0.12, 0.12, CUT_C - T_TAP - 0.34)
        if p_r is not None:
            dep = _r_depth(x, y0, yaw, pose, t, p_r, dep)
            wc, drop, dz = _carry_phase(t)
            if wc > 0.0:
                dep = lerp(dep, _carry_depth(t, drop) + dz, wc)
        r = ch.LionessArm(g_r or "place", screen=p_r, hand=_no_pad(h_r), hold=hold_r, depth=dep)
        lft = ch.LionessArm(g_l or "place", screen=p_l, hand=_no_pad(h_l), hold=hold_l)
    near, far = (r, lft) if yaw >= 0 else (lft, r)
    return near, far, held


_HELD_PREV = {}


def held_world(t):
    """Where the item in her paw was (world) at time t: a dry run of the rig (cached by frame)."""
    key = round(t * 24.0)
    if key in _HELD_PREV:
        return _HELD_PREV[key]
    _s, scr = core.frame(8, 8)
    cam = cam_A(t)
    x, y0, yaw, lp = lio_state_A(t)
    near, far, held = lio_arms_A(t, x, y0, yaw, lp, cam, None)
    pos = None
    if held is not None:
        with cam.view(scr, 1.0):
            ch.draw_lioness(scr, x, y0, SC, lp.with_(near=near, far=far), LL, t)
        for a in (near, far):
            if isinstance(a.hold, Holder) and a.hold.world is not None:
                pos = a.hold.world
    if len(_HELD_PREV) > 64:
        _HELD_PREV.clear()
    _HELD_PREV[key] = pos
    return pos


def _no_pad(hand):
    """The same hand shape as a dict: the rig shows the palm pad only while the hand is exactly the
    named "open" / "offer" pose, so a paw blending through one flashed a pink pad for a frame or
    three (the pick, every shelf reach, every release). Shot A never shows her palm."""
    if isinstance(hand, str) and hand in ("open", "offer"):
        return dict(B.HAND_POSES[hand])
    return hand


def lio_resolve(spec, t, x, y0, yaw, pose, side, scale=SC):
    if isinstance(spec, str):
        if spec == "carry":
            return lio_gesture(x, y0, yaw, pose, t, side, "place", 0.0, scale)
        if spec == "read_low":
            p = lio_gesture(x, y0, yaw, pose, t, side, "read_note", 0.0, scale)
            return (p[0], p[1] + 34.0)
        return lio_gesture(x, y0, yaw, pose, t, side, spec, 0.0, scale)
    if callable(spec):
        return spec(t)
    return spec


def _note_pick_wrist(t):
    return (NOTE_REST_X - 2.0, NOTE_Y + 16.0)


def _pocket(t):
    x, y0, yaw, pose = lio_state_A(t)
    return (x + 30.0, CBACK + 40.0)


# the book's right edge at mid-height, in its seat frame (scale-1 units): where her fingertips
# land when she squares it
BOOK_EDGE = (33.0, -6.5 - 36.0)


def _book_edge(t, dx=0.0, dy=0.0):
    return column_point(t, 3, (BOOK_EDGE[0] + dx, BOOK_EDGE[1] + dy), (PILE_X, PILE_Y), SC)


def _tap_wrist(t, dx=0.0, dy=0.0, at=None):
    ex, ey = _book_edge(t if at is None else at, dx, dy)
    ox, oy = TAP_OFF.get("tap", (42.0, 52.0))
    return (ex + ox, ey + oy)


def _hover_book(t):
    """Beside the teetering book at its own height, ready: the paw follows it a little (nervous)."""
    return _tap_wrist(t, 15.0, 2.5 * math.sin(t * 8.0))


def _tap_book(t):
    return _tap_wrist(t, 0.0, 0.0, at=T_TAP)          # the fingertips meet the book's edge


def _tap_press(t):
    # the press: the finger bends against the edge, its tip 2.5 px into it (solved through the rig:
    # near this pose the fingertip swings ~3x as far as the wrist moves)
    ex, ey = _book_edge(T_TAP_PRESS)
    ox, oy = TAP_OFF.get("press", TAP_OFF.get("tap", (42.0, 52.0)))
    return (ex + ox, ey + oy)


T_TAP_PRESS = T_TAP + 2.0 / 24.0


def _tada(t):
    return (PILE_X + 108.0, 535.0)                    # "ta-da!": an open paw presenting the tower


# the poking finger bends a little against the book for the two frames of the press
PRESSED = {"curl": (0.22, 0.95, 1.0), "spread": 0.04, "thumb": (-0.25, 0.6)}


def _carry3(t):
    """The candle rides a little higher at her chest (it goes up onto the column after the turn)."""
    return _carry_pt(t, -14.0)


def _carry_low(t):
    """Low at her chest while she is still ducked: below the counter's back edge, out of sight."""
    return _carry_pt(t, 60.0)


def _under_counter(t):
    x, y0, yaw, pose = lio_state_A(t)
    return (x - 40.0, CTOP + 60.0)


def _above_top(t):
    ax, ay = seat_anchor(t, 3)
    return (ax + 30.0, ay - grip_h("book_up") * SC - 58.0)


def _shelf(k):
    return lambda tt: _shelf_wrist(k)


def _lift(k):
    return lambda tt: _shelf_lift(k)


def _seat(k, dx=24.0, dy=26.0):
    return lambda tt: _seat_wrist(tt, k, dx, dy)


RIGHT_KEYS = [
    (0.0, "on_counter", "flat"), (T_GO - 0.25, "on_counter", "flat"),
    (T_PICK - 0.06, _note_pick_wrist, "open", 18.0), (T_PICK, _note_pick_wrist, "pinch"),
    (T_READ, "read_note", "pinch", 20.0), (T_LOWER - 0.2, "read_note", "pinch"),
    (T_LOWER, "read_low", "pinch"), (T_SWITCH, "read_low", "pinch"),
    (T_SWITCH + 0.36, "rest", "relaxed", 10.0),
    # trip 1: the sleep draught from the shelf behind her. It comes in to her chest BEFORE she turns
    # and rides round with her body through the turn; then out over the counter and down onto it
    # from ABOVE (over the counter's back edge)
    (TRIPS[0][0] - 0.3, "rest", "relaxed"), (TRIPS[0][0] - 0.05, _shelf(0), "open", 20.0),
    (TRIPS[0][0], _shelf(0), "grip"), (TRIPS[0][0] + 0.08, _lift(0), "grip", 0.0),
    (TRIPS[0][0] + CARRY_IN, _carry_pt, "grip", 8.0), (_turn_end(1), _carry_pt, "grip"),
    (I0 - 0.14, _seat(0, 24.0, 26.0 - 64.0), "grip", 6.0),
    (I0, _seat(0), "grip", 0.0), (I0 + HOLD_AFTER, _seat(0), "open"),
    (I0 + 0.3, _seat(0, 40.0, 26.0 - 46.0), "relaxed", 0.0), (I0 + 0.55, "rest", "relaxed", 8.0),
    # trip 2: the vitamins from the far shelf -- balanced ON THE CORK ("steady...")
    (TRIPS[1][0] - 0.3, "rest", "relaxed"), (TRIPS[1][0] - 0.05, _shelf(1), "open", 20.0),
    (TRIPS[1][0], _shelf(1), "grip"), (TRIPS[1][0] + 0.08, _lift(1), "grip", 0.0),
    (TRIPS[1][0] + CARRY_IN, _carry_pt, "grip", 10.0), (_turn_end(3), _carry_pt, "grip"),
    (I1 - 0.14, _seat(1, 26.0, 8.0), "grip", 6.0),
    (I1, _seat(1), "grip", 0.0), (I1 + HOLD_AFTER, _seat(1), "open"),
    (I1 + 0.26, _seat(1, 40.0, 12.0), "relaxed", 4.0), (I1 + 0.4, "rest", "relaxed", 14.0),
    # trip 3: the CALM candle from the high shelf (on tiptoe), down to her chest BEFORE she turns
    # (it rides round with her, held a little higher), then in above the column from a step
    # further off, and down onto the jar's cover
    (TRIPS[2][0] - 0.36, "rest", "relaxed"), (TRIPS[2][0] - 0.05, _shelf(2), "open", 26.0),
    (TRIPS[2][0], _shelf(2), "grip"), (TRIPS[2][0] + 0.42, _carry3, "grip", 12.0),
    (_turn_end(5), _carry3, "grip"),
    (I2 - 0.13, lambda tt: _carry_high(tt, 2), "grip", 8.0),
    (I2, _seat(2), "grip", 0.0), (I2 + HOLD_AFTER, _seat(2), "open"),
    (I2 + 0.3, lambda tt: _carry_pt(tt, -30.0), "relaxed", 8.0), (I2 + 0.5, "rest", "relaxed", 6.0),
    # trip 4: she ducks for the book, brings it in to her chest while still down (hidden behind the
    # counter), and it comes up WITH her as she rises; on tiptoe she crowns the column with it. It
    # teeters: she steps back half a step and her paw hovers BESIDE it at its height; one tap
    # squares it; ta-da!
    (BOOK_DUCK0, "rest", "relaxed"), (TRIPS[3][0] - 0.06, _under_counter, "open", 10.0),
    (TRIPS[3][0], _under_counter, "grip"), (BOOK_DUCK1 - 0.18, _carry_low, "grip", 6.0),
    (BOOK_DUCK1 + 0.26, _carry_pt, "grip"),
    (I3 - 0.2, _above_top, "grip", 20.0), (I3, _seat(3, 26.0, 18.0), "grip", 0.0),
    (I3 + HOLD_AFTER, _seat(3, 30.0, 16.0), "open"),
    (I3 + 0.45, _hover_book, "open", 10.0), (T_TAP - 0.14, _hover_book, "point"),
    (T_TAP, _tap_book, "point", 0.0), (T_TAP_PRESS, _tap_press, PRESSED, 0.0),
    (T_TAP + 0.2, lambda tt: _tap_wrist(tt, 22.0, -8.0), "open", 0.0),
    (T_TAP + 0.42, _tada, "offer", -18.0), (CUT_C, "rest", "relaxed", -12.0),
]
LEFT_KEYS = [
    (0.0, "on_counter", "flat"), (T_PICK + 0.05, "on_counter", "flat"),
    (T_READ, "read_note", "pinch", 16.0), (T_LOWER - 0.2, "read_note", "pinch"),
    (T_LOWER, "read_low", "pinch"), (T_SWITCH, "read_low", "pinch"),
    (T_POCKET, _pocket, "pinch", -24.0), (T_BACK, "rest", "relaxed", 10.0),
]
LOOK_Y = _look_y_keys()


def note_holder_lio(t, cam):
    """His note in her paws: lifted off the counter (magnet from where it lay, flat -> upright),
    read (two paws), then handed to the left paw and down into the apron pocket."""
    unfold = 0.0 if t < CUT_B else 1.0
    tilt = lerp(FLAT, 1.0, smooth((t - T_PICK) / 0.25))
    # her pinch closes on the note's front edge: the note rides rigidly with the paw from where it
    # lay (the anchor is solved at T_PICK; the magnet only absorbs the last pixel)
    gx, gy = NOTE_PROBE.get("pick", (NOTE_REST_X, NOTE_Y))
    anchor = (NOTE_REST_X - gx, NOTE_Y - gy) if t < T_READ else (0.0, 0.0)
    mag = (NOTE_REST_X, NOTE_Y, 1.0 - smooth((t - T_PICK) / 0.1))
    rd = NOTE_PROBE.get("read")
    if rd is not None and T_READ - 0.16 <= t < T_READ:
        mag = (rd[0], rd[1], smooth((t - (T_READ - 0.16)) / 0.16))
    sw = NOTE_PROBE.get("switch")
    if sw is not None and T_SWITCH <= t < T_SWITCH + 0.16:
        mag = (sw[0], sw[1], 1.0 - smooth((t - T_SWITCH) / 0.16))
    if T_READ <= t < T_SWITCH:
        mag = None

    def draw(c, ax, ay):
        draw_note_flat(c, ax, ay, SC, t, unfold, tilt)
    if T_READ <= t < T_SWITCH:
        # the library's two-hand hold: drawn upright at the midpoint of the paws (no magnet)
        def two(c, f):
            draw_note_flat(c, 0.0, 0.0, SC / (SC * LIO_SIZE_K) * 1.0, t, unfold, 1.0)
        return two
    return Holder(draw, cam, SC, anchor, mag)


NOTE_PROBE = {}          # setup(): her grip at the pick; the two-paw note at T_READ and T_SWITCH (world)


# ========================================================================================
# THE DRAGON: choreography (shot A world)
# ========================================================================================

DRAGON_YAW = 1.0 + 0.6 * 0.12          # facing=1, turn=0.12
D_NEAR = -1.0                           # his near arm is his right (body -X) when facing right

# his faces in A2: the nod lifts him (she understood!) -- brows up, eyes open, a shy smile
D_LIFTED = B.Expr(brow_in=0.55, brow_out=0.42, brow_y=0.5, lid=0.1, lid_bot=0.12, lid_tilt=0.05, smile=0.32,
                  cheek=0.3, pupil=1.12)
# "Actually, I--": brows up and knit, eyes wide, mouth shut (he never gets the words out)
D_ASK = B.Expr(brow_in=0.8, brow_out=0.2, brow_y=0.45, lid=0.08, lid_bot=0.04, lid_tilt=0.22, smile=-0.06, pupil=1.08)
# shot C: the question, asked straight -- brows up and knit, eyes open and on her, no edge at all
D_SINCERE = B.Expr(brow_in=0.72, brow_out=0.0, brow_y=0.32, lid=0.15, lid_bot=0.05, lid_tilt=0.3, smile=-0.04,
                   pupil=1.14)
D_WAIT = B.Expr(brow_in=0.62, brow_out=0.1, brow_y=0.36, lid=0.12, lid_bot=0.06, lid_tilt=0.24, smile=0.0, pupil=1.1)
ASK0 = T_ITEM[1] + 0.32                 # the claw comes up just as she turns away for the high shelf ...
ASK1 = T_ITEM[2] - 0.85                 # ... and sinks back while she reaches up for the candle


def dragon_body(sx, sy, depth, x0=DRAGON_X, y0=FLOOR_D, scale=SC, yaw=DRAGON_YAW, elev=DRAGON_MOD.ELEV):
    """World point -> the dragon's body space at the given camera depth."""
    pr = B.Proj(yaw, elev)
    xl, yl = (sx - x0) / scale, (sy - y0) / scale
    X = xl * pr.c - depth * pr.s
    Z = xl * pr.s + depth * pr.c
    Y = (yl - depth * pr.se) / pr.ce
    return (X, Y, Z)


def note_slide_x(t):
    """The note's x on the counter: his careful push (s2_slide .. T_REL), then it glides on by
    itself and stops in front of her (T_GO): uniform friction, velocity continuous at the release."""
    if t <= T_SLIDE:
        return NOTE_START_X
    d = T_GO - T_REL
    v0 = 2.0 * (NOTE_REST_X - NOTE_REL_X) / d
    if t < T_REL:
        u = (t - T_SLIDE) / (T_REL - T_SLIDE)
        k = v0 * (T_REL - T_SLIDE) / (NOTE_REL_X - NOTE_START_X)        # f'(1): match the glide's speed
        b = k - 2.0
        return NOTE_START_X + (NOTE_REL_X - NOTE_START_X) * ((1.0 - b) * u * u + b * u ** 3)
    if t < T_GO:
        tau = t - T_REL
        return NOTE_REL_X + v0 * tau - 0.5 * (v0 / d) * tau * tau
    return NOTE_REST_X


def column_gaze(t):
    """Where the top of the column is (world), for his eyes to climb."""
    n = n_on_column(t)
    if n == 0:
        return (PILE_X, PILE_Y - 20.0)
    k = n - 1
    top = column_point(t, k, (0.0, item_anchor_local(k)[1] - REM_H[COLUMN[k][0]]), (PILE_X, PILE_Y), SC)
    return top


def dragon_pose_A(t, cam):
    """The dragon in shot A -> DragonPose (his near arm carries the note until he lets go)."""
    talk = tl.talk(SCENE, t, "MAN")
    base = ch.DragonPose(facing=1, turn=0.12, hunch=0.92, mood="tired", talk=talk, wings=-0.55, seed=1,
                         tail_curl=0.5, tail_swing=0.15 * math.sin(t * 0.5))
    S = DRAGON_MOD._skeleton(base, t, 0.0, base.seat_h)
    sk = S["shoulders"][D_NEAR]
    rest = B.v_add(sk, (D_NEAR * 12.0, 172.0, 16.0))
    hold_p = B.v_add(sk, (D_NEAR * -4.0, 66.0, 86.0))
    # ---- A1: eyes (quick darts), head and face blend
    look = core.track(t, [(0.0, (0.25, 0.8)), (0.45, (0.25, 0.8)), (0.58, (0.85, -0.12)), (0.86, (0.85, -0.12)),
                          (1.0, (0.3, 0.8)), (1.05, (0.3, 0.8)), (1.2, (0.45, 0.85)), (T_SLIDE, (0.5, 0.85)),
                          (T_SLIDE + 0.1, (0.58, 0.8)), (T_REL, (0.62, 0.8)), (T_GO - 0.08, (0.76, 0.74)),
                          (T_GO + 0.04, (0.8, 0.45)), (T_GO + 0.16, (0.85, -0.05)), (CUT_B, (0.85, -0.02))])
    nod = core.track(t, [(0.0, -0.15), (0.45, -0.15), (0.62, -0.04), (0.86, -0.04), (1.05, -0.18), (1.3, -0.25),
                         (T_SLIDE, -0.3), (T_GO - 0.1, -0.27), (T_GO + 0.1, -0.22), (T_GO + 0.55, -0.05)])
    # the breath before he acts: a small rise and settle (0.85 .. 1.15)
    br = bump(t, 0.82, 0.16, 0.2)
    lean = core.track(t, [(0.0, 0.0), (1.05, 0.0), (T_SLIDE, 0.22), (T_REL, 0.34), (T_REL + 0.12, 0.34),
                          (T_REL + 0.62, 0.0)])
    hunch = 0.92 - 0.1 * br
    wings = -0.55
    shy = mix_expr("lonely", "worried", 0.35)
    hope = mix_expr("lonely", "raised", 0.32)
    hoping = mix_expr("lonely", "raised", 0.45)
    puzzled = mix_expr("lonely", "skeptical", 0.35)
    deflate = mix_expr("lonely", "tired", 0.35)
    resigned = mix_expr("lonely", "tired", 0.6)
    face = expr_track(t, [(0.0, shy), (T_GO, shy), (T_GO + 0.5, hope), (T_NOD - 0.1, hope), (T_NOD + 0.45, D_LIFTED),
                          (T_ITEMS0 + 0.4, D_LIFTED), (I0 + 0.1, hoping), (I0 + 0.5, puzzled), (I1 + 0.2, puzzled),
                          (ASK0 + 0.22, D_ASK), (ASK1, D_ASK), (ASK1 + 0.45, deflate),
                          (I2 + 0.45, mix_expr("lonely", "tired", 0.45)), (I3 + 0.5, resigned)])
    ht = 0.1 * clamp(look[0])
    if t >= CUT_A2:
        # ---- A2: he watches her read (hope), the nod lifts him, then the tennis match
        def follow(tt):
            lx = kf(tt, LIO_X)
            return clamp((lx - (DRAGON_X + 120.0)) / 900.0, -0.2, 1.0)
        look = (0.85, -0.05)
        if t >= T_ITEMS0 - 0.3:
            # eyes follow her along the shelves; at every thunk they drop to the column and climb
            # its new height -- his gaze rises with the tower
            thunk = max(bump(t, tk - 0.1, 0.1, 0.55, 0.25) for tk in T_ITEM)
            gx, gy = column_gaze(t)
            hx, hy = DRAGON_X + 190.0, 330.0
            tower = (clamp((gx - hx) / 520.0, 0.2, 1.0), clamp((gy - hy) / 240.0, -0.95, 0.9))
            track_look = (0.35 + 0.65 * follow(t), 0.12)
            track_look = core.lerp_tuple(track_look, tower, thunk)
            if t >= I3 - 0.05:
                track_look = core.lerp_tuple(track_look, tower, smooth((t - (I3 - 0.05)) / 0.3))
            look = core.lerp_tuple(look, track_look, smooth((t - (T_ITEMS0 - 0.3)) / 0.3))
        sink = sum(smooth((t - tk) / 0.6) for tk in T_ITEM) / 4.0
        lift = bump(t, T_NOD, 0.3, 0.7, 1.2)                       # she understood!
        # "Actually, I--": an inhale as the claw comes up; it all goes out of him as she turns away
        inhale = bump(t, ASK0 - 0.05, 0.25, 0.5, ASK1 - ASK0 - 0.2)
        wings = -0.5 + 0.38 * lift - 0.45 * sink + 0.12 * inhale
        hunch = 0.92 - 0.1 * lift + 0.06 * sink - 0.08 * inhale
        nod = -0.06 + 0.12 * lift - 0.06 * sink + 0.07 * inhale
        if t >= T_ITEMS0 - 0.3:
            thunk = max(bump(t, tk - 0.05, 0.08, 0.3) for tk in T_ITEM)
            nod -= 0.06 * thunk
            # his head tilts back as the tower climbs past his eye line
            gx, gy = column_gaze(t)
            nod += 0.22 * clamp((360.0 - gy) / 160.0, 0.0, 1.0) * smooth((t - I2) / 0.6)
        ht = 0.1 + 0.3 * clamp((DRAGON_X + 120.0 + 900.0 * follow(t - 0.22) - (DRAGON_X + 300.0)) / 1100.0, -0.3, 1.0)
        if t >= I3 - 0.05:
            ht = lerp(ht, 0.22, smooth((t - (I3 - 0.05)) / 0.4))
        # a flinch as the book teeters (lean back), and a blink at every landing
        lean = -0.1 * bump(t, I3 + 0.05, 0.15, 0.6, 0.2)
    blink = None
    for tk in T_ITEM + [T_TAP]:
        if tk - 0.02 <= t < tk + 0.2:
            blink = bump(t, tk - 0.02, 0.06, 0.12)
    pose = base.with_(look=look, mood=face, mood2=None, mood_mix=0.0, lean=lean, head_nod=nod, wings=wings,
                      head_turn=ht, hunch=hunch, blink=blink)
    # ---- his near arm: A1 the note; A2 a self-soothing tug at his scarf while the pile grows
    hand, tgt, holder = None, None, None
    if t < CUT_B:
        if t < 1.05:
            tgt = B.v_add(hold_p, (0.0, -3.0 * math.sin(t * 5.0) - 10.0 * br, 0.0))
            hand = "pinch"
        elif t < T_SLIDE:
            u = (t - 1.05) / (T_SLIDE - 1.05)
            c0 = dragon_body(NOTE_START_X - 58.0, NOTE_Y - 10.0, 60.0)
            e = core.inout_sine(u)
            tgt = B.v_add(B.v_lerp(hold_p, c0, e), (0.0, -16.0 * math.sin(math.pi * e), 10.0 * math.sin(math.pi * e)))
            hand = "pinch" if u < 0.7 else "flat"
        elif t < T_REL + 0.12:
            # the push: claws flat on the note; at the release they stay on the oak a beat
            tgt = dragon_body(note_slide_x(min(t, T_REL)) - 58.0, NOTE_Y - 10.0, 60.0)
            hand = "flat"
        elif t < T_REL + 0.57:
            u = (t - (T_REL + 0.12)) / 0.45
            a = dragon_body(NOTE_REL_X - 58.0, NOTE_Y - 10.0, 60.0)
            e = core.inout_sine(u)
            tgt = B.v_add(B.v_lerp(a, rest, e), (0.0, -30.0 * math.sin(math.pi * e), -10.0 * math.sin(math.pi * e)))
            hand = "relaxed"
        if tgt is not None and t < T_SLIDE:
            # the folded note pinched in his claws; it tips flat as it meets the counter
            tilt = lerp(1.0, FLAT, smooth((t - 1.25) / 0.25))
            w = smooth((t - 1.3) / 0.2)
            holder = Holder(lambda c, ax, ay: draw_note_flat(c, ax, ay, SC, t, 0.0, tilt), cam, SC,
                            (14.0, -6.0), (NOTE_START_X, NOTE_Y, w))
    else:
        # A2: "Actually, I--" -- one claw comes up in front of his chest (the start of a correction),
        # hangs there while she turns away for the high shelf, then curls and sinks back. The gesture
        # stays the rig's own "rest" (same elbow pole, same layer) with a target, so nothing pops.
        ask = smooth((t - ASK0) / 0.3) * (1.0 - smooth((t - ASK1) / 0.55))
        if ask > 0.0005:
            # his paw to his own chest -- "I..." -- the start of the explanation he never gets out
            on_chest = B.v_add(S["chest"], (D_NEAR * 16.0, 14.0 - 5.0 * bump(t, ASK0 + 0.28, 0.12, 0.3), 60.0))
            e = core.inout_sine(ask)
            tgt = B.v_add(B.v_lerp(rest, on_chest, e), (0.0, 0.0, 22.0 * math.sin(math.pi * e)))
            pose = pose.with_(near=ch.Arm("rest", target=tgt, hand=hand_blend("relaxed", "flat", smooth((ask - 0.2) / 0.6))))
            return pose
    if tgt is not None:
        pose = pose.with_(near=ch.Arm("slide_note", target=tgt, hand=hand, hold=holder))
    else:
        pose = pose.with_(near=ch.Arm("rest"))
    return pose


# ========================================================================================
# the lioness behind a counter: body clipped at its back edge, paws over it shown on top
# ========================================================================================

def draw_lioness_behind(cr, x, y0, scale, pose, light, t, cut_y, reveal=(False, False), under=None):
    """Draw the lioness standing behind a counter seen from a little above: everything below the
    counter's back edge (cut_y) is hidden -- except a paw that is ON the counter top (resting on
    it, picking something up or setting it down there): that ARM ALONE (sleeve, cuff, paw and
    whatever it holds, drawn on its own by _s2_rig.lio_arm exactly as the rig draws it) is laid
    again below the cut (far arm first, so the near paw stays on top), and no apron or body ever
    comes through with it. reveal = (near, far). The reveal windows (REVEAL) switch only while
    that paw is wholly above the cut line, so nothing ever pops: a paw leaves the counter by
    lifting over its back edge, then drops.
    under = (which, Holder): a flat prop held UNDER the paws (her pinch on the note, from the
    counter up to the read): drawn again over sleeves and body where the hand put it, and both
    paws laid back over it -- the order of the library's two-paw read, so nothing flips."""
    pose_nh = pose
    if under is not None:
        which_u = under[0]
        arm_u = getattr(pose, which_u)
        pose_nh = pose.with_(**{which_u: dataclasses.replace(arm_u, hold=None)})

    def paws_over(sides):
        under[1].redraw(cr)
        for w in ("far", "near"):
            if w in sides:
                R2.lio_arm(cr, x, y0, scale, pose_nh, light, t, w, parts="hand")
    cr.push_group()
    rig = ch.draw_lioness(cr, x, y0, scale, pose, light, t)
    if under is not None:
        paws_over(("far", "near"))
    pat = cr.pop_group()
    rig.group = pat                     # kept so a paw can be laid again over a prop
    cr.save()
    cr.rectangle(-4000.0, -4000.0, 10000.0, cut_y + 4000.0)
    cr.clip()
    cr.set_source(pat)
    cr.paint()
    cr.restore()
    shown = [w for w, on in (("far", reveal[1]), ("near", reveal[0])) if on]
    if shown:
        cr.save()
        cr.rectangle(-4000.0, cut_y, 10000.0, 8000.0)
        cr.clip()
        for which in shown:
            R2.lio_arm(cr, x, y0, scale, pose, light, t, which)
        if under is not None:
            paws_over(shown)
        cr.restore()
    return rig


def paint_paw(cr, pat, hf):
    """Lay one paw (with its wrist) again from a character's group, over a prop that stands in front
    of her body (the till's key under her finger, the sack under her pat)."""
    if hf is None:
        return
    a = hf.angle
    size = hf.scale
    wx, wy = hf.x - math.cos(a) * size * 0.45, hf.y - math.sin(a) * size * 0.45
    cr.save()
    cr.new_path()
    core.capsule(cr, wx, wy, size * 0.5, wx - math.cos(a) * size * 1.3, wy - math.sin(a) * size * 1.3, size * 0.5)
    cr.new_sub_path()
    cr.arc(hf.palm[0], hf.palm[1], size * 0.8, 0, TAU)
    cr.new_sub_path()
    cr.arc(hf.x, hf.y, size * 0.75, 0, TAU)
    for tx, ty in (hf.tips or ()):
        cr.new_sub_path()
        cr.arc(tx, ty, size * 0.3, 0, TAU)
    cr.clip()
    cr.set_source(pat)
    cr.paint()
    cr.restore()


# ========================================================================================
# shot A: the two-shot across the counter
# ========================================================================================

def cam_A(t):
    if t < CUT_B:
        return core.Camera.about(820.0, 560.0, lerp(1.0, 1.035, core.inout_sine(ramp(t, 0.0, CUT_B))))
    a = core.Camera.about(820.0, 560.0, 1.035)
    b = core.Camera(1012.0, 522.0, 1.2)
    return core.Camera.lerp(a, b, ramp(t, T_ITEMS0 - 0.6, CUT_C, "inout_sine"))


# When each paw is ON the counter top (in front of its back edge) and must be laid over it. Every
# window opens and closes while that paw is wholly above the cut line (checked frame by frame):
# her right paw rests there, slides to the note, picks it up and lifts it to read; it sets the
# SLEEP DRAUGHT down on the counter (coming over the back edge from above) and lifts off again.
# Her left paw rests there until it joins the note. Nothing else of hers is ever over the top: the
# note goes into her apron pocket BEHIND the counter, and the other items land high on the column.
REVEAL_R = [(-1.0, T_READ - 0.02), (I0 - 0.13, I0 + 0.3)]
REVEAL_L = [(-1.0, T_READ - 0.02)]


def _reveal_paws(t):
    """(right, left): is that paw on the counter top right now?"""
    return (any(a <= t < b for a, b in REVEAL_R), any(a <= t < b for a, b in REVEAL_L))


def draw_A(cr, t, st):
    cam = cam_A(t)
    with cam.view(cr, 0.92):
        st["back"].paint(cr)
        window_rain(cr, t, *WINDOW_A)
    with cam.view(cr, 1.0):
        st["shelves"].paint(cr)
        # remedies waiting on their shelves: tinted into the hazed, glared shelf plane
        for k in range(3):
            if t < TRIPS[k][0]:
                name = COLUMN[k][0]
                sx, sy = SHELF_SPOT[name]
                draw_item(cr, name, sx, sy, SC, t, 0.0, L, haze=0.5)
        P.draw_hanging_sign(cr, 734, 150, kind="apothecary", scale=1.05, light=L, t=t, side=1)
        st["ctop"].paint(cr)
        # the note lying on the counter top (his claws slide it; her paw comes down over it)
        if T_SLIDE <= t < T_PICK:
            nx = note_slide_x(t)
            B.contact_shadow(cr, nx, NOTE_Y + 3.0, 62.0, 5.0, alpha=0.3)
            draw_note_flat(cr, nx, NOTE_Y, SC, t, 0.0, FLAT)
        # the lioness, behind the counter
        x, y0, yaw, lp = lio_state_A(t)
        note_cb = note_holder_lio(t, cam) if T_PICK - 0.02 <= t < T_POCKET + 0.02 else None
        near, far, held = lio_arms_A(t, x, y0, yaw, lp, cam, note_cb)
        if held is not None:
            for a in (near, far):
                if isinstance(a.hold, Holder):
                    a.hold.prev = held_world(t - 1.0 / 24.0)
        lpose = lp.with_(near=near, far=far)
        rev_r, rev_l = _reveal_paws(t)
        reveal = (rev_r, rev_l) if yaw >= 0 else (rev_l, rev_r)
        under = None
        if isinstance(note_cb, Holder) and t < T_READ:
            under = ("near" if near.hold is note_cb else "far", note_cb)
        lrig = draw_lioness_behind(cr, x, y0, SC, lpose, LL, t, CBACK + 3.0, reveal, under)
        # on the counter top: the till at the back, the column (in front of her)
        B.contact_shadow(cr, TILL_X, TILL_Y + 2.0, 66.0 * SC, 6.0 * SC, alpha=0.42)
        P.draw_till(cr, TILL_X, TILL_Y, SC, L, t)
        n_on = n_on_column(t)
        if n_on:
            draw_column(cr, t, n_on, (PILE_X, PILE_Y), SC, skip=(held,) if held is not None else ())
        if T_TAP - 0.3 <= t < T_TAP + 0.24:
            # squaring the book: her fingertips meet its edge IN FRONT of it (her arm stays beside it)
            ex, ey = _book_edge(t)
            cr.save()
            cr.rectangle(ex - 140.0, ey - 120.0, 146.0, 240.0)
            cr.clip()
            R2.lio_arm(cr, x, y0, SC, lpose, LL, t, "near" if yaw >= 0 else "far")
            cr.restore()
        st["cfront"].paint(cr)
        # the dragon, in front of everything
        dp = dragon_pose_A(t, cam)
        rig = ch.draw_dragon(cr, DRAGON_X, FLOOR_D, SC, dp, LD, t)
    with cam.view(cr, 1.04):
        # a horn brushes the tansy as he leans in: it swings off his horn (to the right) and back
        kick = (T_HORN, -0.115) if t >= T_HORN else None
        for i, (hx, hl, kind, sd) in enumerate(HERBS_A):
            st["herbs"][i].draw(cr, hx, BEAM_Y, herb_sway(t, i, kick if i == 5 else None))
        st["beam"].paint(cr)
    with cam.view(cr, 1.0):
        fx.dust(cr, t, (700, 120, 1300, 600), n=30, color="#f4fffb", alpha=0.38, size=(1.0, 2.6), seed=21,
                drift=(5.0, -2.5))
        for ox, oy, sd in ORBS:
            draw_orb(cr, ox, oy, t, sd, 1.15, orb_flicker(t, sd, "A"), chain_top=BEAM_Y)
    lc = st["light"].begin()
    with cam.view(lc, 1.0):
        for ox, oy, sd in ORBS:
            lv = 1.0 - orb_flicker(t, sd, "A")
            fx.glow(lc, ox, oy, 560, "#8fe8c8", 0.22 * lv)
            fx.glow(lc, ox, oy, 150, "#f0fffa", 0.30 * lv)
            # the hard downlight: a pool on the waxed counter top under each orb
            fx.light_pool(lc, ox + (ox - 960.0) * 0.06, CBACK + CDEPTH * 0.55, 230, 34, "#effffa", 0.30 * lv)
        fx.glow(lc, 1150, -160, 1500, "#e6fff6", 0.10)
        fx.glow(lc, rig.top[0], rig.top[1] + 30.0, 240.0, "#e9fff7", 0.13)
        fx.glow(lc, lrig.top[0], lrig.top[1] + 30.0, 210.0, "#e9fff7", 0.12)
    fx.post(cr, t, light=st["light"], bloom_strength=0.75, threshold=0.9, bloom_radius=2.2, wide=0.35,
            grain=0.03, vignette=0.3, vignette_color=VIG)


# ========================================================================================
# shot B: the insert -- her point of view on the note
# ========================================================================================

NOTE_B = (975.0, 652.0)          # the note's centre in the insert
NOTE_B_SC = 8.2
DRAGON_B = (880.0, 1290.0, 2.5)  # his ground point and scale, seen from her side of the counter
HERBS_B = [(240, 230, "lavender", 2), (520, 200, "tansy", 6), (790, 236, "sage", 7), (1110, 210, "yarrow", 8),
           (1420, 246, "rosemary", 4), (1720, 220, "lavender", 5)]


def draw_herb_simple(cr, x, y, length, kind, sway, scale):
    cr.save()
    cr.translate(x, y)
    cr.rotate(sway)
    cr.scale(scale, scale)
    _herb_art(cr, length, kind, L, 3)
    cr.restore()


def _insert_background(cr):
    """What is behind him from her side of the counter: plaster, timber posts, the low beam,
    a sliver of the dark window -- drawn into the low-res buffer, then blurred."""
    _plaster(cr, 0, 0, 1920, 1080, seed=3)
    _hot_spot(cr, 980.0, 60.0, 900.0, 0.4)
    _window(cr, -40, 420, 220, 560)
    _timber(cr, 1530, 0, 80, 1080)
    _timber(cr, 340, 0, 64, 1080)
    _timber(cr, 0, 0, 1920, 90, vertical=False, color=C["timber_dk"])


def _insert_paw(cr, wx, wy, a, sgn, mats, lw):
    """One of her paws holding the note from below: fingers behind the paper (drawn first)."""
    B.hand(cr, wx, wy, a, 236.0, "relaxed", mats["fur"], LL, lw, flip=sgn < 0, thumb=False,
           pad=LIO_MOD.LIONESS_COLORS["pad"], finger_w=1.2, palm_w=1.12)


def draw_B(cr, t, st):
    """The insert: her point of view. The note between her paws fills the lower frame; beyond
    it, out of focus, he waits under the herbs -- his eyes just above the note's edge."""
    u = ramp(t, CUT_B, CUT_A2)
    cam = core.Camera.about(NOTE_B[0], NOTE_B[1] - 60.0, lerp(1.0, 1.06, core.inout_sine(u)))
    bg = st["insert_bg"]
    bctx = bg["ctx"]
    bctx.save()
    bctx.set_operator(cairo.OPERATOR_SOURCE)
    bctx.set_source_surface(bg["base"], 0, 0)
    bctx.paint()
    bctx.restore()
    bctx.save()
    bctx.scale(bg["res"], bg["res"])
    down = bump(t, T_NOTE0 + 1.25, 0.2, 0.3, 0.6)                       # a shy glance down, and back
    dp = ch.DragonPose(facing=0, turn=-0.12, hunch=0.95, mood="lonely", mood2="raised", mood_mix=0.35 * (1 - down),
                       look=(0.04, 0.05 + 0.6 * down), head_nod=-0.12 - 0.12 * down, wings=-0.6, seed=1,
                       talk=tl.talk(SCENE, t, "MAN"), near=ch.Arm("rest"), far=ch.Arm("rest"))
    ch.draw_dragon(bctx, DRAGON_B[0], DRAGON_B[1], DRAGON_B[2], dp, LD, t)
    for i, (hx, hl, kind, sd) in enumerate(HERBS_B):
        draw_herb_simple(bctx, hx, -30.0, hl, kind, herb_sway(t, i), 2.1)
    bctx.restore()
    blurred = fx.blur_surface(bg["surf"], 3.4)
    with cam.view(cr, 0.55):
        cr.save()
        cr.translate(-60.0, -40.0)
        cr.scale(1.06 / bg["res"], 1.06 / bg["res"])
        cr.set_source_surface(blurred, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()
    # ---- the note and her paws (sharp)
    with cam.view(cr, 1.0):
        unfold = smooth((t - (T_NOTE0 + 0.06)) / 0.4)
        bob = 2.5 * math.sin(t * 1.3) + 1.5 * math.sin(t * 2.9)
        nx, ny = NOTE_B[0], NOTE_B[1] + bob
        ang = -0.022 + 0.006 * math.sin(t * 0.9)
        hw, hh = P.NOTE_W * 0.5 * NOTE_B_SC, P.NOTE_H * 0.5 * NOTE_B_SC
        mats = LIO_MOD.lioness_mats()
        robe = B.palette(LL, mats["robe"])
        collar = B.palette(LL, mats["collar"])
        lw = B.line_for(B.LINE, 3.4)
        thumbs = []
        for sgn in (-1.0, 1.0):
            # each paw pinches a lower corner: the wrist below and outside, fingers up and in
            cx_, cy_ = nx + sgn * (hw - 34.0), ny + hh - 22.0 - sgn * hw * math.sin(ang)
            wx, wy = cx_ + sgn * 120.0, cy_ + 170.0
            a = math.atan2(cy_ - wy, cx_ - wx)
            B.occlusion(cr, cx_ + sgn * 8.0, cy_ - 4.0, 70.0, 46.0, (0.25, 0.2, 0.12), 0.25)
            sx, sy = wx + sgn * 90.0, wy + 330.0
            cr.new_path()
            core.capsule(cr, sx, sy, 92.0 + lw, wx + sgn * 14.0, wy + 40.0, 64.0 + lw)
            core.src(cr, robe.line)
            cr.fill()
            core.capsule(cr, sx, sy, 92.0, wx + sgn * 14.0, wy + 40.0, 64.0)
            core.src(cr, robe.lit)
            cr.fill()
            core.capsule(cr, sx + sgn * 30.0, sy, 70.0, wx + sgn * 26.0, wy + 50.0, 44.0)
            core.src(cr, robe.shadow)
            cr.fill()
            cr.new_path()
            core.ellipse(cr, wx + sgn * 6.0, wy + 26.0, 66.0 + lw, 38.0 + lw, a + math.pi / 2)
            core.src(cr, collar.line)
            cr.fill()
            core.ellipse(cr, wx + sgn * 6.0, wy + 26.0, 66.0, 38.0, a + math.pi / 2)
            core.src(cr, collar.lit)
            cr.fill()
            _insert_paw(cr, wx, wy, a, sgn, mats, lw)
            thumbs.append((sgn, cx_, cy_, a))
        P.draw_note(cr, nx, ny, NOTE_B_SC, L, t, ang, unfold)
        for sgn, cx_, cy_, a in thumbs:
            B.occlusion(cr, cx_ - sgn * 22.0, cy_ + 10.0, 46.0, 30.0, (0.3, 0.24, 0.14), 0.22)
            base = (cx_ + sgn * 40.0, cy_ + 66.0)
            tip = (cx_ - sgn * 16.0, cy_ - 4.0)
            mid = (lerp(base[0], tip[0], 0.55) + sgn * 6.0, lerp(base[1], tip[1], 0.55) + 4.0)
            ts, to = B.tube_paths(cr, [base, mid, tip], [26.0, 22.0, 17.0], lw)
            B.shade(cr, ts, mats["fur"], LL, lw, outline=to, size=40, rim=0.5)
            core.src(cr, LIO_MOD.LIONESS_COLORS["pad"], 0.55)
            core.ellipse(cr, tip[0] + sgn * 2.0, tip[1] + 3.0, 8.0, 6.0, a)
            cr.fill()
    lc = st["light"].begin()
    fx.glow(lc, 980, 40, 1000, "#cffbea", 0.2)
    fx.post(cr, t, light=st["light"], bloom_strength=0.3, threshold=0.86, grain=0.03, vignette=0.42)


# ========================================================================================
# shot C: LOW ANGLE on the tower -- it rises above both heads and blocks their eye line
# ========================================================================================

HZ = 856.0                           # the counter top, edge-on: the camera is at counter height
ELEV_C = -0.14                       # the rigs seen from a little below
SCC = 1.88                           # the dragon and the column (same depth, at the counter's front edge)
SCL = 1.66                           # the lioness, a counter's depth behind it
DRAGON_C = (452.0, HZ + 200.0 * SCC)
PILE_C = (1000.0, HZ - 3.0)        # the tower: between their faces, within her reach
LIO_C = (1300.0, HZ + 200.0 * SCL)
TILL_C = (1530.0, HZ - 2.0, 1.72)   # within reach: she steps to it, never stretches for it
BAG_C = (1006.0, HZ - 3.0)           # the filled sack stands where the tower stood (its bottom centre)
HERBS_C = [(-40, 330, "sage", 1), (70, 360, "lavender", 2), (178, 320, "yarrow", 3), (284, 270, "rosemary", 4),
           (388, 236, "lavender", 5), (488, 222, "tansy", 6), (588, 236, "sage", 7), (684, 268, "yarrow", 8)]
ORBS_C = [(1105.0, 128.0, 0), (1650.0, 110.0, 1)]

# The end, all relative to s2_pause / s2_ring. Three cuts carry it:
#   D  MCU on her (punch-in on the low angle), a beat before the smile freezes: the polite smile
#      locks into a rigid toothy grin, everything stops, the whiskers snap, her eyes dart to her
#      shelves (nothing there for this) and back, an orb buzzes in the silence; a double blink
#      reboots her ...
#   E  ... INSERT on the till: her paw comes down from above, the index fingertip lands ON key 2
#      at s2_ring (the key goes down, the bell rocks and dings, the flags pop, the receipt curls
#      out); the paw lifts away and the receipt keeps coming. Off screen we HEAR her bag it all
#      (a paper sack snapped open, clinks, a thump) ...
#   C' ... back to the low two-shot: the tower is gone; the white sack with the green cross
#      stands where it stood, book and draught peeking out; one satisfied pat, a proud nod; he
#      looks down at it and sighs a curl of smoke. Held to the cut.
CUT_D = T_PAUSE - 0.25               # MCU on her, a beat before the freeze
T_LOCK = T_PAUSE                     # the smile locks (two frames)
T_BUZZ = T_PAUSE + 0.12              # an orb stutters in the silence
T_SNAP1 = T_PAUSE + 0.27             # whisker snap up (two frames)
T_DART = T_PAUSE + 0.4               # eyes dart to her shelves ...
T_DART_BACK = T_PAUSE + 0.6          # ... and back to him
T_SNAP2 = T_PAUSE + 0.63             # whisker snap down (two frames)
T_REBOOT = T_RING - 0.31             # she snaps out of it: a double blink, a brisk breath
CUT_E = T_RING - 0.14                # INSERT: the till (three frames before the key goes down)
CUT_C2 = T_RING + 0.52               # back to the two-shot: the tower is in the sack
T_PAT = CUT_C2 + 0.1                 # one satisfied pat on the sack
T_SMOKE = CUT_C2 + 0.02              # his sigh: the smoke leaves his nostrils as he deflates
T_SIGH = CUT_C2 - 0.12               # (the sigh's exhale; the sound starts during the insert)
LIO_BAG_X = 1226.0                   # where she stands in C' (behind the sack)
D_ON_COUNTER = 62.0                  # paw depth (body units ahead of the shoulder) for things on the counter
LIO_SIZE_PX = LIO_SIZE_K * SCL       # body units -> px for her in shots C / D


def _room_C(cr):
    """The room behind them from down at counter height: the wall of jars behind her rising to
    the beam, plaster and the rainy leaded window behind him, timber posts, the APOTHECARY board."""
    _plaster(cr, -200, -200, 2400, 1500, seed=2)
    for hx, hy, hr, ha in ((1100.0, 150.0, 640.0, 0.55), (1650.0, 130.0, 560.0, 0.5), (420.0, 180.0, 520.0, 0.35)):
        _hot_spot(cr, hx, hy, hr, ha)
    _window(cr, 60.0, 250.0, 230.0, 560.0)
    for x, w in ((340, 60), (780, 62)):
        _timber(cr, x, -200, w, 1500)
    cr.save()
    cr.translate(810.0, -40.0)
    cr.scale(1.18, 1.18)
    P.draw_shelves(cr, 0.0, 0.0, w=1100.0, h=760.0, scale=1.0, light=L, rows=6, seed=9, herbs=False)
    cr.restore()
    cr.save()
    cr.rectangle(780.0, -200.0, 1500.0, 1500.0)
    cr.clip()
    cr.set_operator(cairo.OPERATOR_SCREEN)
    core.src(cr, "#9fbcb2", 0.54)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)
    for hx, hy, hr, ha in ((1100.0, 170.0, 520.0, 0.28), (1650.0, 150.0, 460.0, 0.26)):
        _hot_spot(cr, hx, hy, hr, ha)
    cr.restore()
    # the orbs' downlight leaves the wall right behind them a shade darker than the glare around
    # it: a dim ring so the hot white cores read as light sources, not as holes in the glare
    for ox, oy, _s in ORBS_C:
        _soft_blob(cr, ox, oy, 120.0, 120.0, "#2f4a44", 0.16)
    env.draw_haze(cr, -200, -200, 2400, 1500, C["haze"], 0.21, 0.05)
    P.draw_hanging_sign(cr, 815.0, 170.0, kind="apothecary", scale=1.25, light=L, t=0.0, side=1, swing=0.0)
    _timber(cr, -200, -200, 2400, 230, vertical=False, color=C["timber_dk"])     # the beam


def build_room_C():
    """Render the room once and keystone it: from counter height we look up, so its verticals
    converge toward the top (PIL quad warp), then soften it (depth of field)."""
    pad = 200
    w, h = W + 2 * pad, H + 2 * pad
    surf = core.new_surface(w, h)
    c = core.new_context(surf)
    c.translate(pad, pad)
    _room_C(c)
    surf.flush()
    img = core.surface_to_pil(surf).convert("RGB")
    k = 150.0                                      # how much wider the top row samples
    quad = (-k, 0.0, 0.0, float(h), float(w), float(h), w + k, 0.0)
    img = img.transform((w, h), Image.QUAD, quad, Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(2.4))
    out = core.pil_to_surface(img.convert("RGBA"))
    return {"surf": out, "pad": pad}


def _paint_room_C(cr, room):
    cr.save()
    cr.translate(-room["pad"], -room["pad"])
    cr.set_source_surface(room["surf"], 0, 0)
    cr.get_source().set_filter(cairo.FILTER_BILINEAR)
    cr.paint()
    cr.restore()


def _counter_C(cr):
    """The counter from counter height: the top is a line; its dark carved front fills the bottom."""
    core.vgrad(cr, -200, HZ - 4.0, 2400, 34, [C["oak_hi"], C["oak_lt"], C["oak_dk"]])
    core.vgrad(cr, -200, HZ + 30.0, 2400, 1300 - HZ, [C["oak"], C["oak_dk"]])
    cr.save()
    cr.rectangle(-200, HZ + 30.0, 2400, 1300 - HZ)
    cr.clip()
    env.texture(cr, "wood", 0.2, scale=1.2, sx=0.3, sy=3.0)
    core.src(cr, (0, 0, 0), 0.35)
    cr.rectangle(-200, HZ + 30.0, 2400, 12)
    cr.fill()
    px = -120.0
    while px < 2100:
        _linenfold(cr, px, HZ + 62.0, 196, 236)
        px += 228
    cr.restore()
    for ox in (1105.0, 1650.0, 520.0):
        _glint(cr, ox, HZ + 4.0, 120.0, 1.0)


def cam_C(t):
    u = ramp(t, CUT_C, DUR)
    c = core.Camera.about(960.0, 560.0, lerp(1.0, 1.035, core.inout_sine(u)))
    return c.drift(t, 2.5, 0.12, seed=4)


COLUMN_H_C = -COLUMN_TOP * SCC


def dragon_pose_C(t):
    """He stares up at the tower; looks to her while she talks; thought -> glance -> breath ->
    'Do any of them talk back?' leaning round the tower; waits through her frozen smile; at the
    cut back the sack is there: a long closed-mouth sigh, eyes down on it."""
    l1, l2 = LN1, LN2
    talk = tl.talk(SCENE, t, "MAN") * 0.42           # quiet and sincere: a small mouth
    top = (0.55, -0.95)                              # up at the top of the tower
    her = (1.0, 0.22)                                # her face: right of the tower, a little below his eyes
    look = top
    nod, hunch, turn, lean, ht = 0.22, 0.95, 0.12, 0.0, 0.08
    blank = mix_expr("lonely", "tired", 0.5)
    asking = D_SINCERE
    waiting = D_WAIT
    sighing = B.expr("lonely").blend(B.expr("sigh", open=0.0, mouth=""), 0.65)
    face = expr_track(t, [(CUT_C, blank), (l2.start - 0.38, blank), (l2.start - 0.08, asking), (l2.end, asking),
                          (l2.end + 0.6, waiting), (T_SIGH - 0.1, waiting), (T_SIGH + 0.3, sighing), (DUR, sighing)])
    if t >= l1.start - 0.1:
        look = core.lerp_tuple(top, her, smooth((t - (l1.start - 0.1)) / 0.2))
        nod = lerp(0.22, 0.05, smooth((t - (l1.start - 0.05)) / 0.4))
    if t >= l1.start + 1.25:
        look = core.lerp_tuple(her, (0.5, -0.6), smooth((t - (l1.start + 1.25)) / 0.3))   # back up the tower
        nod = lerp(0.05, 0.15, smooth((t - (l1.start + 1.25)) / 0.5))
    # thought (eyes travel down the tower) -> glance (to her) -> breath (he leans round it) -> line
    t_th = l1.end + 0.05
    if t >= t_th:
        look = core.lerp_tuple((0.5, -0.6), (0.5, 0.35), smooth((t - t_th) / 0.35))
        nod = lerp(0.15, 0.0, smooth((t - t_th) / 0.35))
    t_gl = l2.start - 0.38
    if t >= t_gl:
        look = core.lerp_tuple((0.5, 0.35), her, smooth((t - t_gl) / 0.14))
    br = bump(t, l2.start - 0.3, 0.16, 0.22)
    hunch -= 0.12 * br
    nod += 0.06 * br
    lean_round = smooth((t - (l2.start - 0.3)) / 0.45) * (1.0 - smooth((t - (T_SIGH - 0.2)) / 0.45))
    lean += 0.28 * lean_round
    ht += 0.25 * lean_round
    turn += 0.15 * lean_round
    # the sigh: the exhale starts just as we cut back to him (the sound's inhale was under the
    # insert); head and shoulders sink and STAY sunk, eyes down on the sack
    sigh = smooth((t - T_SIGH) / 0.55)
    hunch += 0.35 * sigh
    nod -= 0.45 * sigh
    if t >= T_SIGH - 0.1:
        look = core.lerp_tuple(her, (0.64, 0.62), smooth((t - (T_SIGH - 0.1)) / 0.3))     # down at the sack
    blink = None
    if T_SIGH + 0.5 <= t < T_SIGH + 0.75:
        blink = bump(t, T_SIGH + 0.5, 0.06, 0.14)                                      # a slow, tired blink
    return ch.DragonPose(facing=1, turn=turn, hunch=hunch, mood=face, mood2=None, mood_mix=0.0, look=look,
                         head_nod=nod, head_turn=ht, talk=talk, wings=-0.95 - 0.08 * sigh, sigh=0.0, seed=1,
                         tail_curl=0.55, lean=lean, elev=ELEV_C, blink=blink,
                         near=ch.Arm("rest"), far=ch.Arm("rest"))


# her faces in shot C (open eyes again: the kindness is in the brows and mouth)
LIO_TALK = B.Expr(brow_in=0.3, brow_out=0.3, brow_y=0.34, lid=0.1, lid_bot=0.14, lid_tilt=0.0, smile=0.5, cheek=0.35)
LIO_LISTEN = B.Expr(brow_in=0.42, brow_out=0.14, brow_y=0.26, lid=0.12, lid_bot=0.1, lid_tilt=0.12, smile=0.42,
                    cheek=0.25)
# the frozen smile: the grin stays switched on while everything behind it stops -- lids wide open,
# pupils pin-small, brows stuck up: a polite rictus (the toothy grin itself is _s2_rig's `grin`)
FROZEN_SMILE = B.Expr(brow_in=0.55, brow_out=0.36, brow_y=0.52, lid=0.0, lid_bot=0.16, lid_tilt=-0.04, smile=0.74,
                      cheek=0.6, pupil=0.5)
FAR_C, NEAR_C = -1.0, 1.0      # her far (screen-left, toward him) and near (screen-right, toward the till) arms


def lio_x_C(t):
    """Her ground x in shots C / D, and in C' behind the sack she has just filled."""
    return LIO_BAG_X if t >= CUT_C2 else LIO_C[0]


def lio_y_C(t):
    return LIO_C[1]


def seg_path(t, segs):
    """A paw path from keys [(t, point, ease, arc, depth)]: eased, arcing screen-space segments with
    the paw's depth (body units ahead of the shoulder) eased along; points and depths may be
    callables of t. Before the first key / after the last it holds. Returns (x, y, depth)."""
    def v(s, tt):
        return s(tt) if callable(s) else s
    if t <= segs[0][0]:
        p = v(segs[0][1], t)
        return (p[0], p[1], v(segs[0][4], t))
    for a, b in zip(segs, segs[1:]):
        if t < b[0]:
            u = clamp((t - a[0]) / max(1e-6, b[0] - a[0]))
            e = core.ease(b[2], u)
            pa, pb = v(a[1], t), v(b[1], t)
            x, y = lerp(pa[0], pb[0], e), lerp(pa[1], pb[1], e)
            arc = b[3]
            if arc:
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                n = math.hypot(dx, dy) or 1.0
                k = math.sin(math.pi * e) * arc
                x, y = x + (dy / n) * k, y - (dx / n) * k * (1 if dx >= 0 else -1)
            return (x, y, lerp(v(a[4], t), v(b[4], t), e))
    p = v(segs[-1][1], t)
    return (p[0], p[1], v(segs[-1][4], t))


def lio_rest_depth(t, side, pose, yaw=-1.0):
    """How far ahead of her shoulder (camera depth, body units) her resting paw is: a screen-aimed
    paw given exactly this depth sits exactly where the rig's own "rest" puts it (no pop)."""
    S = LIO_MOD._skeleton(pose, t, yaw)
    sk = S["shoulders"][side]
    tgt = LIO_MOD.LIONESS_GESTURES["rest"](sk, side, dict(S["ctx"], phase=0.0))[0]
    pr = B.Proj(yaw, pose.elev)
    return pr.depth(tgt) - pr.depth(sk)


def _snap(t, t0, sign):
    """A whisker snap: two frames bent hard, one frame of twang back, then still."""
    dt = t - t0
    if dt < 0.0:
        return 0.0
    if dt < 2.0 / 24.0:
        return sign
    return sign * 0.3 * max(0.0, 1.0 - (dt - 2.0 / 24.0) / (1.5 / 24.0))


def lio_C(t, cam=None):
    """The lioness in shots C, D and C' -> (x, y0, pose)."""
    talk = tl.talk(SCENE, t, "PHARMACIST")
    x, y0 = lio_x_C(t), lio_y_C(t)
    look = (-0.62, -0.02)
    freeze, nod, tilt, hturn, blink = 0.0, 0.0, 0.0, 0.0, None
    grin, fan, snap = 0.0, 0.0, None
    yaw = -1.0
    base = R2.LionessPoseS2(facing=-1, talk=talk, seed=2, elev=ELEV_C)
    face = expr_track(t, [(CUT_C, LIO_PROUD), (LN1.start - 0.15, LIO_PROUD), (LN1.start + 0.1, LIO_TALK),
                          (LN1.end + 0.2, LIO_TALK), (LN1.end + 0.5, LIO_LISTEN), (T_LOCK, LIO_LISTEN),
                          (T_LOCK + 0.08, FROZEN_SMILE), (T_REBOOT, FROZEN_SMILE), (T_REBOOT + 0.12, LIO_BUSY),
                          (CUT_C2, LIO_BUSY), (T_PAT + 0.15, LIO_PROUD)])
    # at the stare she admires her tower; "Try these." her far paw presents it; "Lots of people
    # swear by them." a reassuring nod
    look = (-0.35, -0.75) if t < LN1.start - 0.2 else look
    pres = smooth((t - (LN1.start - 0.35)) / 0.6) * (1.0 - smooth((t - (LN1.end - 0.55)) / 0.65))
    far = ch.LionessArm("present", amt=max(0.02, pres), prev="rest")
    near = ch.LionessArm("rest")
    if LN1.start - 0.3 <= t < LN1.end + 0.6:
        look = core.lerp_tuple((-0.62, -0.02), (-0.35, -0.6), bump(t, LN1.start - 0.2, 0.2, 0.25, 0.7))
        swear = [w for w in tl.word_times(LN1.id) if w[0].startswith("swear")]
        t_sw = swear[0][1] if swear else LN1.start + 1.9
        nod = -0.35 * bump(t, t_sw - 0.12, 0.2, 0.35, 0.05)
    # his line: she listens, smile held; her eyes flick to the tower and back as it lands
    if t >= LN2.start:
        tilt = 0.06 * smooth((t - (LN2.end - 0.2)) / 0.5) * (1.0 - smooth((t - T_LOCK) / 0.08))
    if LN2.end + 0.15 <= t < T_LOCK:
        look = core.lerp_tuple((-0.62, -0.02), (-0.3, -0.55), bump(t, LN2.end + 0.15, 0.12, 0.15, 0.2))
    # ---- D: the held beat. The smile LOCKS (two frames) into a rigid, toothy grin, cheeks up,
    # lids wide, pupils pinned, a tiny pull-back -- then nothing moves but the whiskers (two hard
    # snaps) and the eyes: a dart to her shelves (nothing there for this) and back to him
    lean = 0.0
    if t >= T_LOCK:
        lock = smooth((t - T_LOCK) / 0.07) * (1.0 - smooth((t - T_REBOOT) / 0.1))
        grin, fan = lock, lock
        freeze = core.window(t, T_LOCK, T_REBOOT - 0.02, 0.06, 0.04)
        snap = _snap(t, T_SNAP1, 1.0) + _snap(t, T_SNAP2, -1.0)
        lean = -0.13 * B.spring(t, T_LOCK, freq=3.0, damping=0.6) * (1.0 - smooth((t - T_REBOOT) / 0.15))
        dart = smooth((t - T_DART) / 0.07) * (1.0 - smooth((t - T_DART_BACK) / 0.07))
        look = core.lerp_tuple((-0.62, -0.02), (0.78, -0.32), dart)
    # ... she snaps out of it: a double blink, a brisk breath, eyes to the till
    if T_REBOOT - 0.02 <= t < T_REBOOT + 0.16:
        blink = max(bump(t, T_REBOOT - 0.015, 0.02, 0.035), bump(t, T_REBOOT + 0.075, 0.02, 0.035))
    if t >= T_REBOOT:
        look = core.lerp_tuple((-0.62, -0.02), (0.62, 0.48), smooth((t - (T_REBOOT + 0.05)) / 0.08))
        hturn = 0.16 * smooth((t - (T_REBOOT + 0.06)) / 0.12)
        nod = 0.12 * bump(t, T_REBOOT, 0.06, 0.12)
    # ---- C': she has just set the sack down: one satisfied pat, a proud little nod to him
    if t >= CUT_C2:
        hturn = 0.0
        look = core.lerp_tuple((-0.5, 0.42), (-0.62, -0.04), smooth((t - (T_PAT + 0.14)) / 0.16))
        nod = 0.14 * bump(t, T_PAT + 0.16, 0.14, 0.3, 0.12) - 0.08 * (1.0 - smooth((t - CUT_C2) / 0.25))
        far = _lio_pat_far(t, x, y0, base)
    pose = base.with_(look=look, mood=face, mood2=None, mood_mix=0.0, smile=None, freeze=freeze,
                      head_nod=nod, head_tilt=tilt, head_turn=hturn, blink=blink, near=near, far=far, lean=lean,
                      tail_swing=0.2 * math.sin(t * 0.7) * (1.0 - freeze), grin=grin, whisker_fan=fan,
                      whisker_snap=snap)
    return x, y0, pose


PAT_PROBE = {}           # setup(): her far wrist when her flat palm rests on the sack's front, below its mouth


def _sack_grip(bulge=0.0):
    """The sack's grip point (props anchor) for the sack standing at BAG_C."""
    return (BAG_C[0], BAG_C[1] - 87.0 * SCC)


def _pat_goal():
    """Her palm on the sack's front just under its rim -- clear of the green cross."""
    gx, gy = _sack_grip()
    return (gx + 6.0 * SCC, gy + 19.0 * SCC)


def _lio_pat_far(t, x, y0, base):
    """C': her far paw rests flat on the sack she has just set down, gives it one pat, then
    goes back to rest in front of her apron."""
    w = PAT_PROBE.get("wrist", _pat_goal())

    def rest(tt):
        return lio_gesture(lio_x_C(tt), lio_y_C(tt), -1.0, base, tt, FAR_C, "rest", scale=SCL)

    def rest_d(tt):
        return lio_rest_depth(tt, FAR_C, base)
    up = (w[0] + 4.0, w[1] - 26.0)
    segs = [(CUT_C2, w, "linear", 0.0, D_ON_COUNTER), (T_PAT, w, "linear", 0.0, D_ON_COUNTER),
            (T_PAT + 0.09, up, "out_quad", 0.0, D_ON_COUNTER), (T_PAT + 0.17, w, "in_quad", 0.0, D_ON_COUNTER),
            (T_PAT + 0.3, w, "linear", 0.0, D_ON_COUNTER),
            (T_PAT + 0.62, rest, "inout_sine", -10.0, rest_d)]
    px, py, dd = seg_path(t, segs)
    if t < T_PAT + 0.3:
        hand = "flat"
    else:
        hand = hand_blend("flat", "relaxed", smooth((t - (T_PAT + 0.3)) / 0.3))
    return ch.LionessArm("rest", screen=(px, py), depth=dd, hand=hand)


def sack_squash(t):
    """The sack has just been plunked down (it is still settling at the cut), and gives under the
    pat. + squashes (wider, shorter), - stretches."""
    dt = t - (CUT_C2 - 0.06)
    s = 0.07 * math.exp(-dt * 9.0) * math.cos(dt * 26.0) if dt > 0.0 else 0.0
    s += 0.045 * bump(t, T_PAT + 0.15, 0.03, 0.12)
    return s


def draw_sack_C(cr, t):
    """The filled sack on the counter (book and draught peeking out of its open mouth)."""
    sq = sack_squash(t)
    gx, gy = _sack_grip()
    bx, by = BAG_C
    B.contact_shadow(cr, bx, by + 3.0, 34.0 * SCC, 4.5 * SCC, alpha=0.45)
    cr.save()
    cr.translate(bx, by)
    cr.scale(1.0 + 0.6 * sq, 1.0 - sq)
    cr.translate(-bx, -by)
    P.draw_apothecary_bag(cr, gx, gy, SCC, L, t, 0.0, "open")
    cr.restore()


def draw_C(cr, t, st):
    """Shot C (16.5 .. CUT_D) and C' (CUT_C2 .. end): the low angle across the counter."""
    cam = cam_C(t)
    end = t >= CUT_C2
    with cam.view(cr, 0.85):
        _paint_room_C(cr, st["room_C"])
    with cam.view(cr, 0.95):
        for ox, oy, sd in ORBS_C:
            draw_orb(cr, ox, oy, t, sd, 1.3, orb_flicker(t, sd, "C"), chain_top=-60.0)
    with cam.view(cr, 1.0):
        # the lioness, behind the counter (the counter's front hides her below its top)
        x, y0, lp = lio_C(t)
        lrig = ch.draw_lioness(cr, x, y0, SCL, lp, LL, t)
        if not end:
            draw_column(cr, t, 4, PILE_C, SCC, sparkle=True)
        # the till, on the counter in front of her (in C' the receipt hangs out of it, still rocking)
        P.draw_till(cr, TILL_C[0], TILL_C[1], TILL_C[2], L, t, ring=T_RING if t >= T_RING else None,
                    receipt=ramp(t, T_RING + 0.06, T_RING + 0.62, "out_quad"))
        if end:
            draw_sack_C(cr, t)
            # her paw on the sack is in front of it: lay her far arm again over the sack (only
            # where the sack is: her arm keeps its own place against her body everywhere else)
            if t < T_PAT + 0.55:
                gx, gy = _sack_grip()
                cr.save()
                cr.rectangle(gx - 46.0 * SCC, gy - 30.0 * SCC, 92.0 * SCC, 124.0 * SCC)
                cr.clip()
                R2.lio_arm(cr, x, y0, SCL, lp, LL, t, "far")
                cr.restore()
        st["counter_C"].paint(cr)
        # the dragon, nearest the camera
        dp = dragon_pose_C(t)
        rig = ch.draw_dragon(cr, DRAGON_C[0], DRAGON_C[1], SCC, dp, LD, t)
        if t >= T_SMOKE:
            _sigh_smoke(cr, t, T_SMOKE, rig)
    with cam.view(cr, 1.06):
        for i, (hx, hl, kind, sd) in enumerate(HERBS_C):
            st["herbs_C"][i].draw(cr, hx, -10.0, herb_sway(t, i))
    with cam.view(cr, 1.0):
        fx.dust(cr, t, (650, 60, 1250, 640), n=26, color="#f4fffb", alpha=0.34, size=(1.2, 2.8), seed=33,
                drift=(4.0, -2.0))
    lc = st["light"].begin()
    with cam.view(lc, 1.0):
        _orb_light_C(lc, t)
        fx.light_pool(lc, 960, HZ - 6, 900, 34, "#e8fff6", 0.14)
        fx.glow(lc, rig.top[0], rig.top[1] + 40.0, 300.0, "#e9fff7", 0.13)
        fx.glow(lc, lrig.top[0], lrig.top[1] + 40.0, 260.0, "#e9fff7", 0.12)
    fx.post(cr, t, light=st["light"], bloom_strength=0.75, threshold=0.9, bloom_radius=2.2, wide=0.35,
            grain=0.03, vignette=0.34, vignette_color=VIG)


def _orb_light_C(lc, t):
    for ox, oy, sd in ORBS_C:
        lv = 1.0 - orb_flicker(t, sd, "C")
        fx.glow(lc, ox, oy, 640, "#8fe8c8", 0.2 * lv)
        fx.glow(lc, ox, oy, 170, "#f0fffa", 0.3 * lv)
    fx.glow(lc, 1200, -220, 1600, "#e6fff6", 0.1 * (1.0 - 0.35 * orb_flicker(t, 0, "C")))


# ========================================================================================
# shot D: MCU on her -- the frozen smile (a punch-in on the low angle)
# ========================================================================================

D_CENTER = (1205.0, 566.0)


def cam_D(t):
    u = ramp(t, CUT_D, CUT_E)
    z = lerp(2.46, 2.58, core.inout_sine(u))          # a slow push while nothing moves
    return core.Camera(D_CENTER[0], D_CENTER[1], z).drift(t, 1.2, 0.14, seed=11)


def draw_D(cr, t, st):
    cam = cam_D(t)
    with cam.view(cr, 0.85):
        _paint_room_C(cr, st["room_C"])
    with cam.view(cr, 1.0):
        x, y0, lp = lio_C(t)
        lrig = ch.draw_lioness(cr, x, y0, SCL, lp, LL, t)
        draw_column(cr, t, 4, PILE_C, SCC, sparkle=True)
        P.draw_till(cr, TILL_C[0], TILL_C[1], TILL_C[2], L, t)
        fx.dust(cr, t, (880, 330, 760, 460), n=18, color="#f4fffb", alpha=0.32, size=(0.8, 1.6), seed=41,
                drift=(3.0, -1.5))
    lc = st["light"].begin()
    with cam.view(lc, 1.0):
        _orb_light_C(lc, t)
        # the orb light on her face: it stutters with the orb (the buzz in the silence)
        fx.glow(lc, lrig.top[0] + 20.0, lrig.top[1] + 30.0, 230.0, "#e9fff7", 0.16 * (1.0 - 0.8 * orb_flicker(t, 0, "C")))
    fx.post(cr, t, light=st["light"], bloom_strength=0.7, threshold=0.9, bloom_radius=2.2, wide=0.3,
            grain=0.03, vignette=0.4, vignette_color=VIG)


# ========================================================================================
# shot E: INSERT on the till -- her paw comes down from above, the fingertip lands ON the key
# ========================================================================================

K_E = 2.8                                  # the insert's magnification of the low angle
KEY_IDX = 2                                # the key she presses (the till rig's `key` point is key 2)
KEY_LOCAL = (-9.0, -38.0)                  # key 2's centre in the till's own units (props.draw_till)
KEY_DOWN = 1.8                             # how far a pressed key sinks (till units)
TILL_E_SC = TILL_C[2] * K_E
KEY_E = (962.0, 862.0)                     # where key 2 sits on screen in the insert
TILL_E = (KEY_E[0] - KEY_LOCAL[0] * TILL_E_SC, KEY_E[1] - KEY_LOCAL[1] * TILL_E_SC)
PAW_E = LIO_MOD.HAND_LEN * LIO_SIZE_PX * K_E          # her paw's length on screen in the insert
UNIT_E = LIO_SIZE_PX * K_E                            # her body units -> insert px


def _e_from_c(x, y):
    """Shot-C world -> insert screen (the insert is the low angle, magnified about the key)."""
    kx = TILL_C[0] + KEY_LOCAL[0] * TILL_C[2]
    ky = TILL_C[1] + KEY_LOCAL[1] * TILL_C[2]
    return (KEY_E[0] + (x - kx) * K_E, KEY_E[1] + (y - ky) * K_E)


def build_insert_E():
    """The insert's background: the wall of jars behind the till, magnified, very soft (drawn
    at half resolution and blurred: the till is in sharp focus a whole room in front of it)."""
    res = 0.5
    surf = core.new_surface(int(W * res) + 40, int(H * res) + 40)
    c = core.new_context(surf)
    c.translate(20, 20)
    c.scale(res, res)
    kx = TILL_C[0] + KEY_LOCAL[0] * TILL_C[2]
    ky = TILL_C[1] + KEY_LOCAL[1] * TILL_C[2]
    c.translate(KEY_E[0], KEY_E[1])
    c.scale(K_E * 0.92, K_E * 0.92)                  # the far wall magnifies a little less (depth)
    c.translate(-kx, -ky - 40.0)
    _room_C(c)
    surf.flush()
    return {"surf": fx.blur_surface(surf, 5.5), "res": res}


def _insert_counter(cr):
    """The counter's lip and carved front under the till, at the insert's magnification."""
    kx = TILL_C[0] + KEY_LOCAL[0] * TILL_C[2]
    ky = TILL_C[1] + KEY_LOCAL[1] * TILL_C[2]
    cr.save()
    cr.translate(KEY_E[0], KEY_E[1])
    cr.scale(K_E, K_E)
    cr.translate(-kx, -ky)
    _counter_C(cr)
    cr.restore()


def cam_E(t):
    u = ramp(t, CUT_E, CUT_C2)
    return core.Camera.about(KEY_E[0], KEY_E[1] - 120.0, lerp(1.0, 1.035, core.out_sine(u)))


# her fingertip (relative to key 2's centre, insert px) through the insert: in fast from above,
# a hover, the press ON s2_ring (riding the key down), two frames pressed, the lift, out
F24 = 1.0 / 24.0
TIP_KEYS = [(T_RING - 4 * F24, (-110.0, -420.0)), (T_RING - 3 * F24, (-62.0, -226.0), "linear"),
            (T_RING - 2 * F24, (-22.0, -84.0), "linear"), (T_RING - F24, (-5.0, -24.0), "linear"),
            (T_RING, (0.0, 2.0), "in_quad"), (T_RING + 2 * F24, (0.0, 4.0), "linear"),
            (T_RING + 3 * F24, (-4.0, -16.0), "out_quad"), (T_RING + 4 * F24, (-14.0, -66.0), "linear"),
            (T_RING + 5 * F24, (-38.0, -160.0), "linear"), (T_RING + 6 * F24, (-78.0, -300.0), "linear"),
            (T_RING + 7 * F24, (-128.0, -480.0), "linear"), (T_RING + 8 * F24, (-180.0, -680.0), "linear")]
HAND_ANG_KEYS = [(T_RING - 4 * F24, 1.12), (T_RING - F24, 1.3, "out_sine"), (T_RING, 1.34, "linear"),
                 (T_RING + 2 * F24, 1.34), (T_RING + 7 * F24, 1.08, "inout_sine")]
PAW_OUT = T_RING + 8 * F24              # the paw is out of the insert


def _tip_local(angle, pose, flip):
    """Where the index fingertip is relative to the hand's base (insert px), for this angle/pose."""
    _s, scr = core.frame(8, 8)
    mats = LIO_MOD.lioness_mats()
    hf = B.hand(scr, 0.0, 0.0, angle, PAW_E, pose, mats["fur"], LL, 2.0, flip=flip, finger_w=1.15, palm_w=1.1)
    return hf.tips[0]


def draw_insert_paw(cr, t, lw):
    """Her near arm coming down into the insert: robe sleeve, the blouse's cream cuff, the paw
    (the same construction and materials as the rig's arm). The index fingertip is placed exactly
    on the key: the hand's base is solved back from the fingertip."""
    if t > PAW_OUT:
        return None
    tip_rel = core.track(t, TIP_KEYS)
    ang = core.track(t, HAND_ANG_KEYS)
    pressing = T_RING - 0.005 <= t < T_RING + 0.1
    pose = PRESSED if pressing else ("point" if t < T_RING + 0.16 else hand_blend("point", "relaxed",
                                                                                  smooth((t - (T_RING + 0.16)) / 0.2)))
    flip = True
    down = KEY_DOWN * TILL_E_SC if pressing else 0.0
    # the fingertip's visible end is a finger's half-width past the tip joint: aim the joint a hair
    # above the key face so the rounded tip covers the key's centre
    fx_, fy_ = KEY_E[0] + tip_rel[0], KEY_E[1] + tip_rel[1] + down - 0.05 * PAW_E
    tl_ = _tip_local(ang, pose, flip)
    hx, hy = fx_ - tl_[0], fy_ - tl_[1]
    # the arm comes down from above the frame as she leans in: it keeps one soft elbow bend and
    # travels WITH the paw (forearm along the hand, the upper arm a little steeper, going up out of
    # the top of the frame), so it never kinks or snakes on the way in and out
    mats = LIO_MOD.lioness_mats()
    l1, l2 = LIO_MOD.UPPER_ARM * UNIT_E * 1.2, LIO_MOD.FOREARM * UNIT_E
    fa = ang - 0.12                                   # the wrist breaks a little toward the key
    fdx, fdy = math.cos(fa), math.sin(fa)
    wx, wy = hx - fdx * 6.0 * UNIT_E, hy - fdy * 6.0 * UNIT_E
    ex, ey = wx - fdx * l2, wy - fdy * l2
    ua = fa + 0.36
    sx, sy = ex - math.cos(ua) * l1, ey - math.sin(ua) * l1
    # the rig's own sleeve construction: straight capsules shoulder -> elbow -> wrist (one union),
    # with the crease ink on the inside of the elbow
    s_, o_ = CK.caps(cr, [(sx, sy), (ex, ey), (wx, wy)], [18.0 * UNIT_E, 15.0 * UNIT_E, 13.0 * UNIT_E], lw)
    pal = B.shade(cr, s_, mats["robe"], LL, lw, outline=o_, size=40.0 * UNIT_E, rim=0.7)
    nx, ny = -fdy, fdx
    bend = (ex - sx) * (wy - ey) - (ey - sy) * (wx - ex)
    sg = 1.0 if bend > 0 else -1.0
    B.detail_lines(cr, [[(ex + nx * 6 * UNIT_E * sg - fdx * 8 * UNIT_E, ey + ny * 6 * UNIT_E * sg - fdy * 8 * UNIT_E),
                         (ex + nx * 15 * UNIT_E * sg + fdx * 4 * UNIT_E, ey + ny * 15 * UNIT_E * sg + fdy * 4 * UNIT_E)]],
                   lw * 0.8, pal.line, 0.5)
    a = math.atan2(fdy, fdx)
    cs, co = B.ellipse_paths(cr, wx - fdx * 4.0 * UNIT_E, wy - fdy * 4.0 * UNIT_E, 8.5 * UNIT_E, 15.5 * UNIT_E, lw, a)
    B.shade(cr, cs, mats["collar"], LL, lw, outline=co, size=14.0 * UNIT_E, rim=0.5)
    # a soft contact shadow of the finger on the key bed as it comes close
    near = clamp(1.0 - math.hypot(tip_rel[0], tip_rel[1]) / 120.0)
    if near > 0.0:
        B.occlusion(cr, KEY_E[0] + 6.0, KEY_E[1] + 10.0, 46.0, 22.0, (0.2, 0.14, 0.06), 0.35 * near)
    hf = B.hand(cr, hx, hy, ang, PAW_E, pose, mats["fur"], LL, lw, flip=flip, pad=LIO_MOD.LIONESS_COLORS["pad"],
                finger_w=1.15, palm_w=1.1, detail=2)
    return hf


def draw_E(cr, t, st):
    cam = cam_E(t)
    bg = st["insert_E"]
    with cam.view(cr, 0.7):
        cr.save()
        cr.translate(-20.0, -20.0)
        cr.scale(1.0 / bg["res"], 1.0 / bg["res"])
        cr.set_source_surface(bg["surf"], 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()
    with cam.view(cr, 1.0):
        # the till, big: the key goes down ON s2_ring, the bell rocks and dings, the flags pop,
        # the parchment receipt curls up out of its slot
        pressed = KEY_IDX if T_RING - 0.005 <= t < T_RING + 0.1 else None
        B.contact_shadow(cr, TILL_E[0], TILL_E[1] + 4.0, 66.0 * TILL_E_SC, 5.0 * TILL_E_SC, alpha=0.4)
        P.draw_till(cr, TILL_E[0], TILL_E[1], TILL_E_SC, L, t, ring=T_RING if t >= T_RING else None,
                    receipt=ramp(t, T_RING + 0.06, T_RING + 0.62, "out_quad"), pressed=pressed)
        dev = B.device_scale(cr)
        lw = B.line_for(LIO_MOD.LINE / LIO_SIZE_K, UNIT_E * dev, 1.0 / LIO_SIZE_K) * UNIT_E
        draw_insert_paw(cr, t, lw)
        st["counter_E"].paint(cr)
        fx.dust(cr, t, (300, 80, 1300, 700), n=22, color="#f4fffb", alpha=0.3, size=(1.4, 3.2), seed=45,
                drift=(4.0, -2.0))
    lc = st["light"].begin()
    with cam.view(lc, 1.0):
        fx.glow(lc, 1100, -260, 1500, "#e6fff6", 0.16)
        bell = (TILL_E[0], TILL_E[1] - 128.0 * TILL_E_SC)
        if t >= T_RING:
            fx.glow(lc, bell[0], bell[1], 260.0, "#f2fff8", 0.22 * math.exp(-(t - T_RING) * 4.0))
    fx.post(cr, t, light=st["light"], bloom_strength=0.6, threshold=0.88, bloom_radius=2.2, wide=0.3,
            grain=0.03, vignette=0.38, vignette_color=VIG)


def _sigh_smoke(cr, t, t0, rig):
    """The sigh: a curl of smoke from his nostrils. It has to read as smoke, not a smudge: a
    pale, thick halo (it reads over the darker shelves it rises into) around a slate core (it
    reads over the pale limewash), big soft puffs curling up and forward off the snout."""
    s = rig.scale
    for size, col, alpha in ((24.0, "#f4f8f7", 0.78), (12.5, "#46525a", 0.8)):
        fx.smoke(cr, t, t0, rig.nose[0], rig.nose[1], n=12, dur=1.9, rise=104.0, drift=(50.0 * rig.facing, -4.0),
                 size=size, color=col, alpha=alpha, seed=7, scale=s, spread=0.45)
    for size, col, alpha in ((15.0, "#f4f8f7", 0.66), (8.0, "#4f5b63", 0.72)):
        fx.smoke(cr, t, t0 + 0.05, rig.nose[0] - 6.0 * s, rig.nose[1] + 2.0 * s, n=9, dur=1.7, rise=82.0,
                 drift=(34.0 * rig.facing, 2.0), size=size, color=col, alpha=alpha, seed=9, scale=s, spread=0.35)


# ========================================================================================
# setup / draw
# ========================================================================================

def setup():
    st = {}
    st["back"] = env.layer(draw_back_A, opaque=True, blur=0.8, res=1.25)
    st["shelves"] = env.layer(draw_shelves_A, blur=1.1, res=1.25)
    st["beam"] = env.layer(draw_beam, res=1.25)
    st["ctop"] = env.layer(draw_counter_top, res=1.25)
    st["cfront"] = env.layer(draw_counter_front, res=1.25)
    st["herbs"] = [Herb(hl, kind, sd) for (_x, hl, kind, sd) in HERBS_A]
    st["light"] = fx.LightLayer()
    # her paw really holds what it carries: solve the wrist for each shelf grab and set-down
    for k in range(4):
        ax, ay = seat_anchor(T_ITEM[k], k)
        GRIP_OFF[("seat", k)] = _solve_A(T_ITEM[k], (ax, ay - grip_h(COLUMN[k][0]) * SC))
        if k < 3:
            sx, sy = SHELF_SPOT[COLUMN[k][0]]
            GRIP_OFF[("shelf", k)] = _solve_A(TRIPS[k][0], (sx, sy - grip_h(COLUMN[k][0]) * SC))
    # the tap: the flat paw's middle fingertip exactly on the book's edge
    TAP_OFF["tap"] = _solve_A(T_TAP, _book_edge(T_TAP), hand="point", point="index")
    ex, ey = _book_edge(T_TAP_PRESS)
    TAP_OFF["press"] = _solve_A(T_TAP_PRESS, (ex - 2.5, ey), hand=PRESSED, point="index")
    # where the two-paw note sits when she starts reading (T_READ) and when she lets one paw go
    # (T_SWITCH): the one-paw hand-overs are magnet-pulled to exactly these points
    for key, ts in (("pick", T_PICK), ("read", T_READ + 1e-3), ("switch", T_SWITCH - 1e-3)):
        _s, scr = core.frame(8, 8)
        cam = cam_A(ts)
        x, y0, yaw, lp = lio_state_A(ts)
        pos = {}

        def probe(c, f, pos=pos):
            pos["p"] = c.user_to_device(0.0, 0.0)
        near, far, _h = lio_arms_A(ts, x, y0, yaw, lp, cam, probe)
        with cam.view(scr, 1.0):
            ch.draw_lioness(scr, x, y0, SC, lp.with_(near=near, far=far), LL, ts)
        if "p" in pos:
            inv = cam.matrix(1.0)
            inv.invert()
            NOTE_PROBE[key] = inv.transform_point(*pos["p"])
    # the insert's out-of-focus background: a low-res buffer redrawn each frame (he breathes)
    res = 0.25
    base = core.new_surface(int(W * res), int(H * res))
    bc = core.new_context(base)
    bc.scale(res, res)
    _insert_background(bc)
    base.flush()
    surf = core.new_surface(int(W * res), int(H * res))
    st["insert_bg"] = {"res": res, "base": base, "surf": surf, "ctx": core.new_context(surf)}
    # shots C, D, C' (the low angle) and E (the till insert)
    st["room_C"] = build_room_C()
    st["counter_C"] = env.layer(_counter_C)
    st["herbs_C"] = [Herb(hl, kind, sd, scale=1.25, blur=1.2) for (_x, hl, kind, sd) in HERBS_C]
    st["insert_E"] = build_insert_E()
    st["counter_E"] = fx.Layer(_insert_counter, w=W + 200, h=H + 200, x=-100, y=-100)
    # C': her flat palm rests on the sack's front, just below its mouth (solved through the rig)
    PAT_PROBE["wrist"] = _solve_wrist(CUT_C2 + 0.01, FAR_C, _pat_goal(), "flat", point="palm")
    return st


def _solve_wrist(t, side, goal, hand, point="grip", iters=12):
    """Shots C / C': the screen (wrist) target that puts her paw's grip point -- or its palm
    centre, or its index fingertip -- exactly on `goal` (world): a damped Newton solve through the
    real rig (the paw's angle depends on the wrist, so a plain fixed-point update oscillates)."""
    x, y0 = lio_x_C(t), lio_y_C(t)
    base = ch.LionessPose(facing=-1, seed=2, elev=ELEV_C)
    _s, scr = core.frame(8, 8)

    def measure(w):
        arm = ch.LionessArm("rest", screen=w, depth=D_ON_COUNTER, hand=hand)
        pose = base.with_(far=arm) if side == FAR_C else base.with_(near=arm)
        rig = ch.draw_lioness(scr, x, y0, SCL, pose, LL, t)
        hf = rig.hand_far if side == FAR_C else rig.hand_near
        if point == "tip":
            return hf.tips[0]
        if point == "palm":
            return hf.palm
        return (hf.x, hf.y)
    return newton2(measure, (goal[0] + 20.0, goal[1] + 24.0), goal, iters)


def draw(cr, t, st):
    if t < CUT_B:
        draw_A(cr, t, st)
    elif t < CUT_A2:
        draw_B(cr, t, st)
    elif t < CUT_C:
        draw_A(cr, t, st)
    elif t < CUT_D:
        draw_C(cr, t, st)
    elif t < CUT_E:
        draw_D(cr, t, st)
    elif t < CUT_C2:
        draw_E(cr, t, st)
    else:
        draw_C(cr, t, st)


# ========================================================================================
# sound cues (local seconds, from the same constants the animation uses)
# ========================================================================================

def _pan(x):
    return round(clamp((x - 960.0) / 960.0, -1.0, 1.0), 2)


def _footsteps(t0, t1, dt=1.0 / 240.0):
    """Her soft steps behind the counter: one per half walk-cycle while she glides."""
    out = []
    prev = None
    t = t0
    stride = ch.lioness_stride(SC, 1, 0.75)
    while t < t1:
        v = (kf(t + 0.03, LIO_X) - kf(t - 0.03, LIO_X)) / 0.06
        d = 0.0
        for (a0, v0), (a1, v1) in zip(LIO_X, LIO_X[1:]):
            if t <= a0:
                break
            d += abs(kf(min(t, a1), LIO_X) - v0)
        step = math.floor(d / max(1.0, stride) * 2.0)
        if prev is not None and step != prev and abs(v) > 60.0:
            out.append((round(t, 3), "footstep", {"gain": 0.22, "pan": _pan(kf(t, LIO_X)), "size": 0.4,
                                                  "who": "lioness", "surface": "wood"}))
        prev = step
        t += dt
    return out


def _sfx_cues():
    cues = []
    px = _pan(PILE_X)
    # the slide: dry herbs brushed by a horn, the note laid down and slid across the oak
    cues.append((round(T_SLIDE - 0.08, 3), "cloth_rustle", {"gain": 0.22, "pan": _pan(505.0), "size": 0.3}))
    cues.append((round(T_SLIDE, 3), "paper_slide", {"gain": 0.6, "pan": _pan(NOTE_START_X), "dur": round(T_GO - T_SLIDE, 2)}))
    cues.append((round(T_PICK, 3), "page_turn", {"gain": 0.3, "pan": _pan(NOTE_REST_X)}))             # she lifts it
    cues.append((round(T_NOTE0 + 0.08, 3), "page_turn", {"gain": 0.7, "pan": 0.0}))                 # the unfold, close
    cues.append((round(T_POCKET - 0.1, 3), "cloth_rustle", {"gain": 0.25, "pan": _pan(PICK_X)}))     # into her apron
    cues += _footsteps(T_GO - 0.35, T_GO + 0.2) + _footsteps(T_SWITCH, T_ITEMS1)
    # the fetches: a clink as each leaves its shelf; the book comes up from under the counter
    for k, (tg, ts) in enumerate(TRIPS):
        name = COLUMN[k][0]
        if k < 3:
            cues.append((round(tg, 3), "glass_clink", {"gain": 0.28, "pan": _pan(SHELF_SPOT[name][0])}))
        else:
            cues.append((round(tg, 3), "cloth_rustle", {"gain": 0.2, "pan": _pan(PLACE_X)}))
    # the set-downs (the thunks): glass on oak, then glass on glass up the column
    cues.append((round(I0, 3), "item_set_down", {"gain": 0.8, "pan": px, "size": 0.4, "material": "sleep"}))
    cues.append((round(I1, 3), "item_set_down", {"gain": 0.75, "pan": px, "size": 0.45, "material": "vitamins"}))
    cues.append((round(I1 + 0.005, 3), "glass_clink", {"gain": 0.4, "pan": px}))                   # jar on the cork
    cues.append((round(I1 + 0.3, 3), "glass_clink", {"gain": 0.1, "pan": px}))                     # its wobble
    cues.append((round(I2, 3), "item_set_down", {"gain": 0.6, "pan": px, "size": 0.35, "material": "calm"}))
    cues.append((round(I2 + 0.005, 3), "glass_clink", {"gain": 0.35, "pan": px}))
    cues.append((round(I3, 3), "item_set_down", {"gain": 0.7, "pan": px, "size": 0.6, "material": "book"}))
    cues.append((round(I3 + 0.3, 3), "glass_clink", {"gain": 0.12, "pan": px}))                    # the teeter
    cues.append((round(T_TAP, 3), "tap_wood", {"gain": 0.4, "pan": px}))                           # squared off
    # the end. D: the silence of the frozen smile (only the orb's buzz). E: a brisk step to the till,
    # the sleeve swishes in, DING on s2_ring, the receipt rattles out, and under the insert his
    # sigh begins (its exhale lands on the cut back). Off screen she bags the whole tower at speed
    # -- a paper sack snapped open, the remedies clinking in, the book's thud -- and the sack is
    # plunked on the counter a frame before we see it there. C': one pat; the smoke puff.
    tx, bx = _pan(TILL_C[0]), _pan(BAG_C[0])
    cues.append((round(T_BUZZ, 3), "candle_flicker", {"gain": 0.5, "pan": _pan(ORBS_C[0][0])}))
    cues.append((round(T_REBOOT + 0.04, 3), "cloth_rustle", {"gain": 0.18, "pan": _pan(LIO_C[0])}))
    cues.append((round(CUT_E - 0.03, 3), "footstep", {"gain": 0.16, "pan": tx, "size": 0.4, "who": "lioness",
                                                       "surface": "wood"}))
    cues.append((round(T_RING - 3.0 / 24.0, 3), "cloth_rustle", {"gain": 0.24, "pan": tx, "dur": 0.15}))
    cues.append((round(T_RING, 3), "till_bell", {"gain": 0.9, "pan": tx}))
    cues.append((round(T_RING + 0.06, 3), "receipt", {"gain": 0.6, "pan": tx}))
    cues.append((round(T_RING + 0.1, 3), "sigh", {"gain": 0.45, "pan": _pan(DRAGON_C[0] + 200.0)}))
    cues.append((round(PAW_OUT - 0.04, 3), "cloth_rustle", {"gain": 0.42, "pan": bx, "dur": 0.18}))   # sack snapped open
    cues.append((round(PAW_OUT + 0.03, 3), "glass_clink", {"gain": 0.3, "pan": bx}))
    cues.append((round(PAW_OUT + 0.08, 3), "glass_clink", {"gain": 0.26, "pan": bx}))
    cues.append((round(PAW_OUT + 0.12, 3), "item_set_down", {"gain": 0.3, "pan": bx, "size": 0.4, "material": "book"}))
    cues.append((round(CUT_C2 - 0.04, 3), "item_set_down", {"gain": 0.72, "pan": bx, "size": 0.6, "material": "bag"}))
    cues.append((round(CUT_C2 - 0.03, 3), "cloth_rustle", {"gain": 0.32, "pan": bx}))
    cues.append((round(T_PAT + 0.15, 3), "cloth_rustle", {"gain": 0.22, "pan": bx}))                  # the pat
    cues.append((round(T_SMOKE, 3), "smoke_puff", {"gain": 0.22, "pan": _pan(DRAGON_C[0] + 250.0)}))
    return sorted(cues, key=lambda c: c[0])


SFX_CUES = _sfx_cues()
