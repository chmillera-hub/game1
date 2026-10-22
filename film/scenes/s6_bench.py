"""s6_bench.py -- SCENE 6, THE BENCH (30 s). The turn of the film.

A nearly empty castle garden at dusk. A tiny gnome grandmother feeds the pigeons at one end of a
bench; the lonely dragon sits down at the other. The empty space between them is the subject
until she says something dry and true and he laughs -- for the first time in the film -- and the
first warm light, which comes from HIM, spreads out into the evening.

Every time below is the CURRENT value; the code derives each one from timeline beats, lines and
word times (constants at the top), so the staging follows the audio if the timeline changes.
The set is the shared location module film/scenes/_garden.py (S7 and S8 reuse it; this scene
never edits it -- every S6-only look lives here).

EMOTIONAL LINE (SPEC 0.3)
  two lonely creatures at the two ends of one bench -> an awkward, funny silence (the pigeons
  watch it like a tennis match) -> he takes out the remedy he was handed (a coloring book) ->
  she recognises it: she was handed the same kind of stones -> his deadpan list -> she crosses
  the gap (two little hops along the seat) -> the cat story, honest and funny and lonely too ->
  a held look -> the punchline -> HE LAUGHS -> warmth spreads out from him into the light.

COLOUR / VALUE SCRIPT
  Dusk: violet sky, a peach glow low on the LEFT where the sun has just set, long soft shadows
  falling right; the garden graded cool violet-green. The cast out-contrasts the set: the dusk
  key from the low sun on the left and a COOL lavender rim from the sky on the right cut both
  of them out of the background, while the bench is lit a step dimmer and duskier than they
  are (bench_light). Warm notes are withheld -- only her faded-red hood, his mustard scarf and
  the horizon -- until the laugh (27.2 s): golden embers fountain from his mouth with a glow
  that pulses on each laugh pulse, the light reaches HER face from his side, warm rims come up
  on the sides of their faces that face each other (the light lives in the space BETWEEN
  them), and THE WORLD CHANGES: the garden's golden-hour paint blooms in over the dusk through
  a soft circle that grows out from his mouth across the whole frame (_golden_bloom: the
  hedges go green-gold, the sky peach, the bench honey) while the cast's and the bench's light
  warm toward golden. It stays: golden motes hang between them to the last frame, so the cut
  to S7's golden hour is warmth continuing, not a jump.

SHOTS (hard cuts on action; eased moves + a gentle breathing drift; never a frozen frame)
  A  0.00-3.55  "she is alone" -> OPENS CLOSE ON HER, PULLS BACK TO THE WIDE.
     cam (815,770) z2.30, held while she tosses her crumbs (release 0.71) -- a small figure at
     one end of a long, empty bench, the castle above, the pigeons pecking: the image of the
     whole film's loneliness -- then from 0.85 an eased pull-back to (917,627) z1.10 just as he
     trudges in at the right edge (drooped wings, the paper apothecary sack swinging -- open at
     the neck as he carried it in S3 and S4, the coloring book's corner peeking out): the
     reveal widens on him, the oak framing the left, the castle on its hill above the bench, the
     unlit iron lantern on the right. She clocks him at 1.75 (eyes, then head; back to her
     pigeons). He stops (2.80), turns front and lowers himself, setting the sack down by his foot.
  B  3.55-12.45 "the gap" -> LOW TWO-SHOT WITH A GALLERY.  cam (870,800) z2.12 -> z2.20.
     Cut on the sit. The bench across the frame, she on the left, he on the right, the EMPTY
     middle with the castle above it -- and along the bottom of the frame, close to the lens,
     a row of four big pigeons: the spectators (grounded by their own soft contact shadows and
     long dusk shadows on their foreground plane). 3.75: the seat takes his weight (creak, sag,
     her bounce, hood flop, spectacles jump) and the gallery startles (hop, flap). An "umpire"
     pigeon flies in (4.10) and lands on the middle of the backrest (4.85): the umpire's chair.
     s6_pause 4.0-9.0, THE TENNIS MATCH: every small thing either of them does snaps every head
     that way in sync (anticipation dip, fast turn, overshoot, settle) -- and bird 3 is always a
     beat late. Him (4.25) -> her "hmph", eyes shut, nose up (5.25) -> his scoot + creak (6.05)
     -> her boots shoot out at the lens, soles to us, as she sits back with a bounce (6.75) ->
     his sigh, a curl of smoke (7.35) -> her sniff (7.90) -> they
     glance at each other at the same moment (8.25) and look away fast; the pigeons, out of
     options, turn and stare into the lens -- and blink, all together (8.70). Hold to 9.0.
     s6_book 9.0-12.0: the sack rustles (every head snaps to him); he leans down, pulls out
     MINDFUL COLORING FOR ADULTS (9.42: it rises out of the sack from where its corner stood,
     turning to face us), sits up with it, opens it (to 10.08), flips four pages
     without joy (10.12-11.40), shuts it and lobs it onto the seat into the gap (lands 12.00);
     every head follows its arc. The camera eases in a touch toward the book business.
  C  12.45-15.24 "over the spectacles" -> MEDIUM CLOSE-UP on her.  z5.95 -> 6.12.
     Her face on the left third, looking right (lead room toward the book and him). s6_glance
     12.6: eyes slide to the book, the spectacles slide down her nose, one judging blink, a
     bored-skeptical peer over the rims. s6_l1 "They tell you to try that too?" -- a lazy flick
     of the hand toward the book and a nod on "that" (the hand eases off her lap, turns down
     and out toward the book, and settles back: _g_s6_flick); chin down, eyes up to him over
     the rims on "too?" with a smirk.
  D  15.24-18.56 "the list" -> MEDIUM CLOSE-UP on him.  z4.3 -> 4.45.
     His face on the right two-thirds, the umpire pigeon small at the left watching him. s6_l2
     "Candles. Vitamins. Yoga." -- deadpan, eyes down to the book (off left); a slow blink before
     "Vitamins."; on "Yoga." his eyes come up to her with the smallest tilt and shrug (no blink:
     the look lands).
  E  18.56-30.00 "the cat" -> TWO-SHOT that closes in as they connect.  z3.0 -> 3.3 by "I got
     the cat", 4.7 by the beat (both faces big: the held look is the shot), 4.9 into the snort,
     released to 3.75 as the laugh throws his head back, breathing out to 3.3 at the end. From
     shot D on the book on the seat is graded a stop down (BOOK_DIM: her long dusk shadow lies
     across the seat), so their faces stay the brightest values and the caption band stays calm.
     Cut BEFORE she moves: two quick hops along the seat toward him (18.68, 18.87) -- she crosses
     the gap, in the frame that shows it. His body has opened toward her.
     s6_l3 "They told me to get a cat. I got the cat." -- she looks up and away, remembering; in
     her pause after "...get a cat." HE LEANS IN to listen (lean_in: his head comes down toward
     hers -- he crosses the rest of the gap), and the umpire pigeon, in the way of his snout,
     sidesteps twice along the crest board and ruffles its feathers; back to him, deadpan, on
     "I got the cat." (21.44). His brows go up.
     THE BEAT 22.49-23.62, a held look, the camera still: she stares at him over her spectacles,
     one slow dry blink; he waits, leaning in, and holds her stare (no blink of his own); the
     umpire turns to him for an answer, then back.
     s6_l4 "The cat sleeps through every story about my day." -- her eyes half-close on "sleeps",
     a tiny head shake through "every story", a smirk on "day". HIS BUILD (build_stages): on
     "sleeps" the corner of his mouth goes and his cheeks push his lower lids up (GRIN); through
     "every story" he holds it in -- his eyes slide away, his chin dips, his shoulders start to
     shake; on "day" his eyes come back to her and the grin breaks wide; the snort (26.95): a
     jerk of the head, a hitch of the shoulders, eyes squeezed, a puff of smoke and sparks
     blown from his nose.
     s6_laugh 27.19: HE LAUGHS -- he rocks back out of the lean, head back, eyes squeezed,
     shoulders shaking, one hand holding his belly (the faded SMILE print from S4 on its back)
     while the other slaps his knee on two pulses, wings lifting, a fountain of golden
     embers; the bench rocks, the umpire startles up and lands back on the middle. She melts: a
     silent chuckle, hand to her heart, spectacles pushed up, chin up. The golden hour blooms
     out from him over the garden (see the colour script) and settles; they end smiling at each
     other -- his eyes open and soft, his head tipped toward her.

ACTING NOTES (thought -> glance -> breath -> line; eyes lead, the head follows, the body last)
  Her: dry wit, twinkly, never mocking. She notices him long before she admits it. Each line
  starts with a look and lands on one small specific gesture (the flick at the book, eyes over
  the rims, the deadpan, the smirk on "day"). Blinks are acted (on thought changes), never on a
  look that must land, never across a cut (checked at import).
  Him: weary, polite, closed (front-on, hunched, wings drooped); he turns toward her only as she
  earns it. The laugh is built, not switched on: twitch -> grin -> snort -> burst -> warmth.

PERIOD: a castle garden of a storybook kingdom -- wrought-iron-and-oak bench, an iron candle
lantern (unlit: S7 lights it), gravel walk, clipped box hedges, wattle-edged flower beds, the
castle with pennants on its hill, a paper apothecary sack tied with twine, wool, linen, felt.
Nothing modern on screen.

CONTINUITY -> S7 (film/scenes/_garden.py): she ends at G.SEATS_S6_END (u 0.3), he at u 0.83; the
book lies on the seat at u 0.55, the umpire stands on the middle of the backrest, the sack on
the gravel at his feet, open (G.S6_END_PROPS); his wings relaxed-up, both smiling, him turned
to her. The back of his right hand carries the SMILE print from S4, faded (STAMP_INK 0.55).
The book on the seat is props' "flat" book squashed to FLAT_K = 0.75 in depth, its front face
on the seat's front edge (book_rest / book_front in setup) -- copy that to match it exactly.
The light at the last frame: the dusk garden with the golden-hour garden bloomed over it
(GOLD_NEAR 0.5 around them, GOLD_FAR 0.3 at the edges) and the cast lit Light.lerp(dusk,
golden, 0.5) with warm rims toward each other -- S7's golden hour continues from there.

SOUND: SFX_CUES (module level) lists every on-screen event with its local time, computed from
the same constants the animation uses (footsteps on the walk cycle's heel strikes).
"""

import bisect
import math

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.characters import gnome as _GN          # her arm lengths (UPPER_ARM, FOREARM) for _g_s6_flick
from film.lib.characters import dragon as _DR         # its _brow_ridge, wrapped in draw_dragon (the far eye's clip)
from film.scenes import _garden as G
from film.scenes import _s6_eye
from film.scenes import _s6_rig as R6

SCENE = 6
DUR = tl.scene(SCENE).duration

# ----------------------------------------------------------------------------------------
# timing: timeline beats and lines; scene beats are offsets from them
# ----------------------------------------------------------------------------------------
B_SIT, B_PAUSE, B_BOOK, B_GLANCE = tl.beat("s6_sit"), tl.beat("s6_pause"), tl.beat("s6_book"), tl.beat("s6_glance")
B_LAUGH = tl.beat("s6_laugh")
L1, L2, L3, L4 = tl.line("s6_l1"), tl.line("s6_l2"), tl.line("s6_l3"), tl.line("s6_l4")
LAUGH = tl.line("s6_laugh")


def _word(line_id, k):
    """Start time of word k of a line (aligned to the speech envelope)."""
    return tl.word_times(line_id)[k][1]


W_THAT, W_TOO = _word("s6_l1", 5), _word("s6_l1", 6)
W_VITAMINS, W_YOGA = _word("s6_l2", 1), _word("s6_l2", 2)
W_CAT1, W_I = _word("s6_l3", 6), _word("s6_l3", 7)
W_SLEEPS, W_EVERY, W_DAY = _word("s6_l4", 2), _word("s6_l4", 4), _word("s6_l4", 8)

# A -- the walk in and the sit: she is alone through her toss (the crumbs land, the pigeons
# start pecking); he comes into view at the frame's right edge at ~1.3 s, as the camera starts
# to pull back, trudging at his S3 pace (~150 world px/s), and sits at the other end
T_WALK_END = B_SIT.t + 1.5             # he arrives in front of his end of the bench
T_TURN0, T_TURN1 = T_WALK_END - 0.15, T_WALK_END + 0.55
T_SIT0 = T_WALK_END + 0.1
T_LAND = B_SIT.t + 2.3                 # the seat takes his weight: creak, sag, her bounce
T_BAG = T_LAND - 0.06                  # the sack touches down beside his foot
CUT_B = T_LAND - 0.2                   # cut on the action into the two-shot
T_TOSS_G0, T_TOSS_G1 = 0.15, 1.35      # her crumb toss (release at phase 0.47)
T_TUCK1 = T_TOSS_G1 + 0.5              # ... then the rest of her bread goes back in her satchel
T_CRUMBS = T_TOSS_G0 + 0.47 * (T_TOSS_G1 - T_TOSS_G0)
T_NOTICE = B_SIT.t + 0.25              # she clocks him (eyes first)

# B -- the pause: the pigeon tennis match (volleys; each sends every head to that side)
P0, P1 = B_PAUSE.t, B_PAUSE.end
V_HIM0 = T_LAND + 0.5                  # all heads to the newcomer
V_HMPH = P0 + 1.15                     # her "hmph": chin up
V_SHIFT = P0 + 1.85                    # his weight shift (creak)
V_KICK = P0 + 2.45                     # her boots swing
V_SIGH = P0 + 3.0                      # his sigh (smoke)
V_SNIFF = P0 + 3.5                     # her sniff
V_GLANCE = P0 + 3.85                   # both glance at each other: the pigeons look at us ...
GLANCE_HOLD = 0.4                      # ... the two looks meet and hold (then snap away)
T_SYNC_BLINK = V_GLANCE + 0.62         # ... all four staring (the late one too), they blink together;
                                       # the stare holds ~0.75 s, to the sack's rustle at s6_book
T_UMP0 = T_LAND + 0.35                 # the umpire pigeon flies in ...
T_UMP1 = T_UMP0 + 0.75                 # ... and lands on the backrest

# B -- the book
T_REACH = B_BOOK.t
T_BAGOPEN = T_REACH + 0.28             # his hand rummages in the (open) sack: a paper rustle
T_GRAB = T_REACH + 0.42
T_HOLD = T_REACH + 0.8
T_OPEN0, T_OPEN1 = T_HOLD, T_HOLD + 0.28
T_FAR0, T_FAR1 = T_OPEN0 - 0.15, T_OPEN1 + 0.1   # his far hand meets the left page as it opens
T_FLIPS = [T_OPEN1 + 0.04 + 0.32 * k for k in range(4)]
FLIP_D = 0.3
T_CLOSE0, T_CLOSE1 = B_BOOK.end - 0.58, B_BOOK.end - 0.36
T_TOSS0 = T_CLOSE1                     # he lowers the shut book toward the seat beside him ...
T_RELEASE = B_BOOK.end - 0.14          # ... lets go of it a hand's breadth above the seat ...
T_BOOKLAND = B_BOOK.end                # ... and it plops flat onto the seat, into the gap
TOSS_K = 0.5                           # how far toward flat the book has tipped when he lets go

# shots
CUT_C = B_GLANCE.t - 0.15
CUT_D = L2.start - 0.15
CUT_E = L2.end - 0.05                  # cut BEFORE she moves: the hops read in the two-shot

# E -- after his list she shuffles closer along the seat (two little hops): she crosses the gap
SCOOT_HOPS = ((CUT_E + 0.12, 0.16), (CUT_E + 0.31, 0.16))
T_SCOOT0 = SCOOT_HOPS[0][0]
T_SCOOT1 = SCOOT_HOPS[1][0] + SCOOT_HOPS[1][1]

# acted blinks (local s): thought changes, after looks; never on a look that must land
DRAGON_BLINKS = [0.9, 2.3, T_LAND + 0.9, V_SHIFT + 0.55, V_GLANCE + 0.6, T_HOLD + 0.55, T_BOOKLAND + 0.12,
                 B_GLANCE.t + 1.5, L2.start - 0.5, W_I - 0.3, W_EVERY - 0.08,
                 LAUGH.end + 1.2]
GNOME_BLINKS = [1.0, 3.1, T_LAND + 1.15, V_SHIFT + 0.4, V_GLANCE + 0.55, T_HOLD + 0.9,
                T_BOOKLAND + 0.1, B_GLANCE.t + 0.36, L2.start + 1.3, W_I - 0.16, W_EVERY - 0.1, LAUGH.end + 0.7]

T_BEAT0, T_BEAT1 = L3.end, L4.start
T_SNORT = LAUGH.start - 0.24
T_EMBERS = LAUGH.start + 0.03
# E -- in her pause after "...get a cat." he leans in; the umpire sidesteps out of his way
T_LEAN0 = W_CAT1 + 0.5
UMP_HOPS = (T_LEAN0 + 0.02, T_LEAN0 + 0.21)       # two little sideways hops (0.16 s each)
UMP_STEP = 17.0                                  # world px per hop (toward her)


def _laugh_peaks():
    """Times of the laugh's pulses (local maxima of his speech envelope during s6_laugh)."""
    ts = [LAUGH.start + k / 96.0 for k in range(int((LAUGH.end - LAUGH.start) * 96.0) + 1)]
    v = [tl.talk(SCENE, x, "MAN") for x in ts]
    return [ts[i] for i in range(1, len(v) - 1) if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] > 0.5]


LAUGH_PEAKS = _laugh_peaks() or [LAUGH.start + 0.15 + 0.22 * k for k in range(5)]
SLAPS = LAUGH_PEAKS[1:4:2] if len(LAUGH_PEAKS) >= 4 else LAUGH_PEAKS[:2]     # 2nd and 4th pulse
T_SLAP0, T_SLAP1 = SLAPS[0] - 0.32, SLAPS[-1] + 0.45

# ----------------------------------------------------------------------------------------
# the set and the cast's places
# ----------------------------------------------------------------------------------------
SC = G.SCALE
BENCH = G.BENCH1
U_GNOME = G.SEATS["gnome"]
U_GNOME2 = G.SEATS_S6_END["gnome"]      # after she shuffles closer
U_DRAGON = G.SEATS["dragon"]
U_BOOK = G.S6_END_PROPS["book_u"]       # where the book lands on the seat (in the gap)
PIGEON_Y = (950.0, 990.0)
WALK_FROM = 410.0                       # he starts this far right of his seat (off-frame, walking in)
WALK_TURN = -0.5                        # facing -1 + turn: near profile while walking (yaw -1.3)
SIT_TURN = 0.92                         # seated, nearly front-on (yaw ~-0.45): closed
TALK_TURN = 0.38                        # turned toward her by the end (yaw ~-0.77)


def _bench_rig():
    return _STATE["bench"]


_STATE = {}


# ----------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------

def _r(t, a, b, e="inout_sine"):
    return core.ramp(t, a, b, e)


def _win(t, a, b, fi=0.2, fo=0.3):
    return core.window(t, a, b, fi, fo)


def _pulse(t, t0, up=0.12, down=0.35):
    """0 -> 1 -> 0: a quick accent at t0."""
    if t < t0 or t > t0 + up + down:
        return 0.0
    if t < t0 + up:
        return core.inout_sine((t - t0) / up)
    return 1.0 - core.inout_sine((t - t0 - up) / down)


def _bump(t, t0, dur):
    """sin bump 0 -> 1 -> 0 over dur from t0."""
    u = (t - t0) / dur
    return math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0


def _blink_at(t, times, dur=0.18):
    """Lid closure from a list of deliberate blink times (fast close, slower open)."""
    best = 0.0
    for tb in times:
        u = (t - tb) / dur
        if 0.0 <= u <= 1.0:
            best = max(best, core.smooth(u / 0.35) if u < 0.35 else 1.0 if u < 0.45 else 1.0 - core.smooth((u - 0.45) / 0.55))
    return best


def _track(t, keys, ease="inout_sine"):
    return core.track(t, keys, ease)


def _v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)


def _unit(v):
    n = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / n, v[1] / n)


# ----------------------------------------------------------------------------------------
# lights and the warmth
# ----------------------------------------------------------------------------------------
# his face after the laugh: a warm smile with smiling eyes (cheeks up, soft lids)
AFTER_LAUGH = ch.Expr(brow_in=0.4, brow_out=0.18, brow_y=0.32, lid=0.22, lid_bot=0.32, lid_tilt=0.08, smile=0.85,
                      open=0.0, mouth="", cheek=0.75, pupil=1.12)
# the grin he can't hold in (s6_l4): cheeks pushing his lower lids up into a squint, brows soft
GRIN = ch.Expr(brow_in=0.3, brow_out=0.1, brow_y=0.14, lid=0.34, lid_bot=0.4, lid_tilt=-0.04, smile=0.9,
               open=0.0, mouth="", cheek=0.85, pupil=1.0)


def build_stages(t):
    """The laugh's build, three overlapping 0..1 stages: the twitch ("sleeps"), holding it in
    ("every story"), breaking through ("day")."""
    return (_r(t, W_SLEEPS + 0.04, W_SLEEPS + 0.42), _r(t, W_EVERY - 0.05, W_EVERY + 0.35),
            _r(t, W_DAY - 0.06, W_DAY + 0.22))


# her startle when the seat takes his weight: brows up, eyes wide -- MOUTH SHUT (she says
# nothing: STYLE 8, mouths move only on dialogue); the bounce, the jumping spectacles and the
# hood flop sell it
STARTLE = B.MOODS["surprised"].with_(open=0.0, mouth="", smile=-0.15, pupil=0.75)
# her silent chuckle: a closed-mouth smile, the eyes squeezed into happy crescents
CHUCKLE = ch.Expr(brow_in=0.3, brow_out=0.25, brow_y=0.4, lid=0.58, lid_bot=0.62, lid_tilt=-0.12, smile=1.0, open=0.0,
                  mouth="", cheek=1.0)
L_DUSK = G.light_for("dusk")
L_GOLD = G.light_for("golden")
WARM_RIM = (1.0, 0.74, 0.40)
# the cast before the laugh: the dusk key from the low sun (left) and a COOL rim from the violet
# sky on the right -- it separates them from the set without spending a warm note
COOL_RIM, COOL_RIM_K = (0.76, 0.74, 1.0), 0.8
# the bench before the laugh: dusky, a step under the cast in value and saturation
BENCH_COOL = dict(key=(0.96, 0.86, 0.9), k_exposure=0.88)


def warmth(t):
    """0 before the laugh -> 1: the warmth that enters the light from the embers."""
    return core.ramp(t, T_EMBERS + 0.05, T_EMBERS + 2.6, "inout_sine")


def spread(t):
    """0 -> 1: how far the warm light has spread out from the embers (fast, then settling)."""
    return core.ramp(t, T_EMBERS, T_EMBERS + 3.0, "out_cubic")


GOLD_CAST = 0.5                  # how far the cast's light warms toward golden after the laugh
GOLD_SET = 0.42                  # ... and the bench / props
GOLD_NEAR, GOLD_FAR = 0.5, 0.3   # the garden's golden bloom: near the embers / the far frame


def light_for(t, who):
    """The light on one of them. Dusk; after the laugh the key warms toward golden and a warm
    rim comes up on the side that faces the other one (the light lives BETWEEN them)."""
    w = warmth(t)
    cast = L_DUSK.with_(rim=COOL_RIM, rim_strength=COOL_RIM_K)
    if w <= 0.0:
        return cast
    side = 1.0 if who == "gnome" else -1.0           # toward the warm source
    base = ch.Light.lerp(cast, L_GOLD, GOLD_CAST * w)
    rd0 = cast.rim_dir()
    rd1 = _unit((side, -0.3))
    rd = _unit((core.lerp(rd0[0], rd1[0], w), core.lerp(rd0[1], rd1[1], w)))
    return base.with_(rim=core.lerp_tuple(COOL_RIM, WARM_RIM, w),
                      rim_strength=core.lerp(COOL_RIM_K, 1.0, w), rim_direction=rd,
                      exposure=1.0 + 0.05 * w)


def light_at(t):
    """The set's light on props (the book, the sack, the birds): dusk warming after the laugh."""
    w = warmth(t)
    return L_DUSK if w <= 0.0 else ch.Light.lerp(L_DUSK, L_GOLD, GOLD_SET * w)


def bench_light(t):
    """The bench: dusky and a step darker than the cast before the laugh; the warmth soaks into
    the wood after it (the warm pool lands on the seat between them)."""
    L = light_at(t)
    cool = 1.0 - warmth(t)
    return L.with_(key=core.lerp_tuple(L.key, BENCH_COOL["key"], cool),
                   exposure=L.exposure * core.lerp(1.0, BENCH_COOL["k_exposure"], cool))


# ----------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------
Cam = core.Camera
CAM_B0 = Cam(870.0, 800.0, 2.12)


def _react(u):
    """Ease for a camera move thrown by an action (the laugh): a one-frame kick-in, then a long
    out-cubic settle -- it reacts to the burst instead of anticipating it."""
    return core.out_cubic(u) * core.smoothstep(0.0, 0.08, u)          # the gallery two-shot (the gallery is placed against it)
T_PULL0 = 1.15                            # A: the pull-back starts once her crumbs are down: it finds him
SHOTS = [
    ("A", 0.0, CUT_B, [(0.0, Cam(754.0, 846.0, 2.92)), (T_PULL0, Cam(756.0, 845.0, 2.88)),
                       (CUT_B - 0.1, Cam(916.0, 628.0, 1.1), "inout_sine"), (CUT_B, Cam(917.0, 627.0, 1.096))]),
    ("B", CUT_B, CUT_C, [(CUT_B, CAM_B0), (P1, Cam(871.0, 799.0, 2.15)),
                         (T_HOLD + 0.4, Cam(880.0, 797.0, 2.19)), (CUT_C, Cam(878.0, 797.0, 2.2))]),
    ("C", CUT_C, CUT_D, [(CUT_C, Cam(781.0, 792.0, 5.95)), (CUT_D, Cam(780.0, 791.0, 6.12))]),
    ("D", CUT_D, CUT_E, [(CUT_D, Cam(946.0, 698.0, 4.3)), (CUT_E, Cam(944.0, 697.0, 4.45))]),
    ("E", CUT_E, DUR + 0.01, [(CUT_E, Cam(880.0, 744.0, 3.0)), (L3.start + 0.2, Cam(878.0, 743.0, 3.06)),
                              (W_I - 0.25, Cam(876.0, 742.0, 3.3)),
                              (T_BEAT0 + 0.35, Cam(872.0, 740.0, 4.7)), (T_BEAT1, Cam(872.0, 740.0, 4.76)),
                              (T_SNORT - 0.3, Cam(873.0, 740.0, 4.9)),
                              (LAUGH.start + 0.02, Cam(873.0, 740.0, 4.9)),      # held through the snort ...
                              (LAUGH.start + 0.66, Cam(884.0, 726.0, 3.75), _react),  # ... thrown back by the burst
                              (DUR, Cam(876.0, 738.0, 3.3))]),
]
DRIFT_PX = {"A": 1.8, "B": 2.6, "C": 4.0, "D": 4.0, "E": 4.0}     # breathing drift, in screen px


def _check_blinks():
    """No acted blink may straddle a cut (a closed eye on the first frame of a shot reads as
    a glitch): every blink ends >= 0.15 s before a cut or starts >= 0.15 s after it."""
    cuts = [a for _n, a, _b, _k in SHOTS[1:]]
    for name, times in (("dragon", DRAGON_BLINKS), ("gnome", GNOME_BLINKS)):
        for tb in times:
            for c in cuts:
                if tb - 0.15 < c < tb + 0.18 + 0.15:
                    raise ValueError(f"s6: {name} blink at {tb:.2f} straddles the cut at {c:.2f}")


def shot_at(t):
    for name, a, b, keys in SHOTS:
        if a <= t < b:
            return name, keys
    return SHOTS[-1][0], SHOTS[-1][3]


def camera(t):
    name, keys = shot_at(t)
    cam = Cam.track(t, keys)
    return name, cam.drift(t, amp=DRIFT_PX[name] / cam.zoom, freq=0.11, seed=6)


# ----------------------------------------------------------------------------------------
# the dragon: walk in, sit, the pause, the book, the list, the laugh
# ----------------------------------------------------------------------------------------
# custom gestures (registered with the dragon's gesture table; per-frame targets in _GX)
_GX = {"bag_mouth": (60.0, -90.0, 60.0), "yaw": -0.45}
BOOK_NEAR = (20.0, 30.0, 104.0)          # near-hand grip on the book's right edge (from his chest, body px)
BOOK_SPAN = 104.0                        # screen distance from that grip to the book's left edge (body px)


def _g_s6_set_bag(sk, side, c):
    # sitting down, the sack is lowered to the gravel beside his near foot
    return (side * 92.0, -118.0, 34.0), "grip", 0.0, "front"


def _g_s6_bag(sk, side, c):
    return _GX["bag_mouth"], "pinch", 0.0, "front"


def _g_s6_book(sk, side, c):
    # the near hand holds the book's right edge before his chest (the book extends screen-left)
    return _v_add(c["chest"], (side * BOOK_NEAR[0], BOOK_NEAR[1], BOOK_NEAR[2])), "grip", 0.0, "front"


def _g_s6_book_far(sk, side, c):
    # the far hand steadies the book's left edge from behind: BOOK_SPAN to screen-left of the
    # near grip at the same depth (through the current body yaw)
    yaw = _GX["yaw"]
    dx = -BOOK_SPAN
    near = _v_add(c["chest"], (-side * BOOK_NEAR[0], BOOK_NEAR[1], BOOK_NEAR[2]))
    tgt = _v_add(near, (dx * math.cos(yaw), 10.0, dx * math.sin(yaw)))
    # + a correction solved in setup() so the grip lands exactly on the open book's left edge
    return _v_add(tgt, _GX.get("book_far_fix", (0.0, 0.0, 0.0))), "grip", 0.0, "front"


def _g_s6_slap(sk, side, c):
    # the laughing knee slap: the flat hand comes down on his near KNEE -- out past his other hand,
    # which stays on his lap, so the slap reads -- lifted by phase (0 = on the knee)
    kn = c["knee"][0 if side < 0 else 1]
    base = _v_add(kn, (side * 14.0, -21.0, 24.0))
    lift = c["phase"]
    return _v_add(base, (side * 6.0 * lift, -46.0 * lift, 14.0 * lift)), "flat", 0.25, "mid"


def _g_s6_belly(sk, side, c):
    # laughing, his other hand comes off his lap to hold his belly (it clears the knee for the slaps)
    return _v_add(c["chest"], (side * 6.0, 48.0, 32.0)), "relaxed", 0.1, "mid"


def _g_s6_toss(sk, side, c):
    # the shut book lowered toward the seat beside him (target solved per frame in _GX)
    return _GX.get("toss", _v_add(c["chest"], (-40.0, 70.0, 112.0))), "grip", 0.0, "front"


for _name, _fn in (("s6_set_bag", _g_s6_set_bag), ("s6_bag", _g_s6_bag), ("s6_book", _g_s6_book),
                   ("s6_book_far", _g_s6_book_far), ("s6_toss", _g_s6_toss), ("s6_slap", _g_s6_slap),
                   ("s6_belly", _g_s6_belly)):
    ch.DRAGON_GESTURES[_name] = _fn
# the far hand turns right round between his thigh and the open book's left edge (its forearm
# swings end-on to the lens on the way): ease its screen angle over the whole reach (_s6_rig)
R6.STEER_ALWAYS.add("s6_book_far")

_ELEV = 0.12


_BASE_EYE = B.eye
_BASE_BROW = _DR._brow_ridge
_EYE_Q = []                      # the eye call waiting for its brow ridge (see draw_dragon)


def _eye_deferred(cr, *a, **kw):
    """Stands in for base.eye inside ch.draw_dragon: remember the call and its transform; the
    brow ridge drawn right after it paints it (_brow_then)."""
    _EYE_Q.append((cr, cr.get_matrix(), a, kw))


def _flush_eye(head=None):
    while _EYE_Q:
        cr, m, a, kw = _EYE_Q.pop(0)
        cr.save()
        cr.set_matrix(m)
        cr.new_path()
        if head:
            _s6_eye.eye_far(cr, head, *a, **kw)
        else:
            _s6_eye.eye(cr, *a, **kw)
        cr.restore()


def _brow_then(q, P_, nz, s, e, near, clip=None):
    """dragon._head draws each eye and then its brow ridge -- the far ridge with the head's
    silhouette paths as its clip: the waiting eye is painted here (same z-order), the far one
    with its bulge past those paths drawn as an outlined lid (_s6_eye.eye_far)."""
    _flush_eye(clip)
    return _BASE_BROW(q, P_, nz, s, e, near, clip)


def draw_dragon(cr, x, y, scale, pose, light, t):
    """ch.draw_dragon with this scene's eyes (_s6_eye) for his big 3/4 close-ups (zoom 4-5).
    The library's eye fills the lid with one flat tone, and his far eye's socket bulges past the
    head's outline: as the lids closed the far one became a flat, unoutlined dome with an ink
    line over the sky, the near one a smooth untextured patch from eye to brow. Here the lids
    inside the head are his own scales (no fill, no corner slivers), and the far eye's bulge past
    the head is a lid of scales with an ink contour that runs into the head's outline, so a
    blink is the lash line coming down over the eyeball and the closed eye a lid arc on his
    scales. (Scene-local swaps, restored at once.)"""
    B.eye = _eye_deferred
    _DR._brow_ridge = _brow_then
    del _EYE_Q[:]
    try:
        # (_s6_rig: arm hand-offs without elbow pops, the held-in laugh's shoulders, the feet)
        with R6.dragon_patch(shrug=shoulder_shrug(t), feet=feet_override(t)):
            return ch.draw_dragon(cr, x, y, scale, pose, light, t)
    finally:
        _flush_eye()                 # (an eye with no ridge after it: none in the library today)
        B.eye = _BASE_EYE
        _DR._brow_ridge = _BASE_BROW


def tremble_env(t):
    """0..1: how hard he is holding the laugh in -- from "every story", fullest on "day", gone
    when it bursts."""
    _b1, b2, b3 = build_stages(t)
    return (0.45 * b2 + 0.55 * b3) * (1.0 - _r(t, LAUGH.start - 0.05, LAUGH.start + 0.1))


def giggle(t):
    """The held-in laugh's hitches: ~3.4 a second, quick up and down, animated on 2s (12 fps
    steps) -- a cartoon shudder, not a per-frame jitter."""
    tq = math.floor(t * 12.0) / 12.0
    return max(0.0, math.sin((tq - W_EVERY) * math.tau * 3.4)) ** 0.7


def shoulder_shrug(t):
    """Hunch units for his SHOULDERS only (R6.RIG['shrug'], applied after the head is placed):
    the held-in laugh makes them hitch up while his head stays steady."""
    k = tremble_env(t)
    return -0.26 * k * giggle(t) if k > 0.0 else 0.0


FEET_STEPS = {-1.0: (0.1, 0.27), 1.0: (0.3, 0.27)}     # side -> (start after T_LAND, duration)


def feet_override(t):
    """{side: (u, lift)} for his feet while he sits (R6.RIG['feet']), or None (the library's
    own). The library slides the feet forward over the gravel as sit passes 0.55; here they
    stay planted where he stood while he lowers himself, and once the bench has his weight he
    steps them forward into the seated pose, one and then the other, with a small lift."""
    if t < T_SIT0 or t > T_LAND + 0.8:
        return None
    out = {}
    for side, (d0, dur) in FEET_STEPS.items():
        u = core.clamp((t - T_LAND - d0) / dur)
        out[side] = (core.inout_sine(u), 9.0 * math.sin(math.pi * u))
    return out


def draw_gnome(cr, x, y, scale, pose, light, t):
    """ch.draw_gnome with this scene's arm hand-offs (_s6_rig: no elbow pops)."""
    with R6.gnome_patch():
        return ch.draw_gnome(cr, x, y, scale, pose, light, t)


def _world_to_body(wx, wy, ax, ay, yaw, depth):
    """A world point -> the dragon's body space (anchor (ax, ay), scale SC, yaw) at camera depth."""
    xb, yb = (wx - ax) / SC, (wy - ay) / SC
    c, s = math.cos(yaw), math.sin(yaw)
    X = c * xb - s * depth
    Z = s * xb + c * depth
    Y = (yb - depth * math.sin(_ELEV)) / math.cos(_ELEV)
    return (X, Y, Z)


def walk_dist(t):
    """World px he has walked by t (0 .. WALK_FROM at T_WALK_END): a steady pace, easing into
    the stop over the last 22 % of the walk. (The footstep cues use it too.)"""
    u = core.clamp(t / T_WALK_END)
    k = 0.78
    s = u / k * 0.86 if u < k else 0.86 + 0.14 * core.out_quad((u - k) / (1 - k))
    return WALK_FROM * min(1.0, s)


def dragon_anchor(t):
    """World anchor (ground point under his pelvis) and walk distance travelled."""
    x1, y1 = _bench_rig().place(U_DRAGON)
    x0 = x1 + WALK_FROM
    x = x0 - walk_dist(t)
    # his weight shift scoots him a hair along the seat
    x += 6.0 * _r(t, V_SHIFT, V_SHIFT + 0.3, "out_back") - 2.0 * _r(t, V_SHIFT + 0.3, V_SHIFT + 0.7)
    return x, y1, x0 - x


def bench_sag(t):
    """The seat's give under him: a dip at the landing that rings down to a slight sag; the
    shift and the laugh rock it again."""
    s = 0.0
    if t > T_LAND:
        s += 0.3 * core.ramp(t, T_LAND, T_LAND + 0.25) + 0.75 * B.wobble(t, T_LAND, 3.1, 4.6) / 1.35
    s += 0.55 * B.wobble(t, V_SHIFT + 0.05, 3.4, 5.0) / 1.35
    s += 0.25 * B.wobble(t, LAUGH.start + 0.05, 5.5, 2.2) / 1.35 * (1.0 - core.ramp(t, LAUGH.end - 0.2, LAUGH.end + 0.5))
    return s


def slap_lift(t):
    """0 (hand on the thigh) .. 1 (raised): up fast, slam down on each slap time."""
    lift = 0.0
    for ts in SLAPS:
        if ts - 0.24 <= t < ts - 0.06:
            lift = max(lift, core.out_quad((t - (ts - 0.24)) / 0.18))
        elif ts - 0.06 <= t < ts:
            lift = max(lift, 1.0 - core.in_quad((t - (ts - 0.06)) / 0.06))
    return lift


def dragon_turn(t):
    """His body turn: near profile walking in, front-on and closed on the bench, opening to her;
    the laugh throws him back toward the front for a moment."""
    turn = _track(t, [(T_TURN0, WALK_TURN), (T_TURN1, SIT_TURN), (L2.start - 0.3, SIT_TURN),
                      (L2.start + 0.7, 0.62), (L3.start + 0.2, 0.6), (W_I - 0.1, 0.5), (W_I + 0.55, TALK_TURN)])
    turn += 0.16 * _win(t, LAUGH.start - 0.02, LAUGH.end + 0.2, 0.18, 0.7)
    return turn


def lean_in(t):
    """0..1: he leans in to listen to the cat story -- a little on "cat", then, in her pause
    before "I got the cat.", all the way (closing the distance as she earns it); rocks back with
    the laugh, and settles still turned to her (leaning only a little: the umpire is back)."""
    k = _track(t, [(L3.start + 0.1, 0.0), (W_CAT1 + 0.1, 0.12), (T_LEAN0, 0.2), (W_I - 0.1, 0.7),
                   (W_I + 0.5, 0.78), (L4.start, 0.82), (W_DAY, 0.86), (LAUGH.start - 0.02, 0.88),
                   (LAUGH.start + 0.3, -0.12), (LAUGH.end - 0.1, -0.05), (LAUGH.end + 0.9, 0.18), (DUR, 0.2)])
    return k


def dragon_pose(t):
    """(x, y, DragonPose) at time t (world coordinates)."""
    x, y, dist = dragon_anchor(t)
    turn = dragon_turn(t)
    walk = 1.0 - _r(t, T_WALK_END - 0.32, T_WALK_END + 0.04)
    phase = ch.dragon_walk_phase(dist, SC, -1, WALK_TURN)
    # sit: lower (ease) then the last bit drops (the plop)
    if t < T_SIT0:
        sit = 0.0
    elif t < T_LAND - 0.18:
        sit = 0.86 * core.inout_sine((t - T_SIT0) / (T_LAND - 0.18 - T_SIT0))
    else:
        sit = 0.86 + 0.14 * core.in_quad(core.clamp((t - (T_LAND - 0.18)) / 0.18))
    land = B.wobble(t, T_LAND, 2.4, 4.0) / 1.35
    hunch = 0.62 + 0.12 * land
    lean = 0.18 * land
    lean += 0.32 * math.sin((t - V_SHIFT) * math.tau * 2.2) * _bump(t, V_SHIFT, 0.5)
    # the book: lean down to the sack, then sit back up
    lean += 0.42 * _win(t, T_REACH, T_HOLD + 0.1, 0.32, 0.38)
    # the cat story: he leans in to listen (his head comes down toward her), rocks back laughing
    k_in = lean_in(t)
    lean += 0.9 * k_in
    hunch += 0.14 * max(0.0, k_in)
    # moods
    mood, mood2, mix = "tired", "lonely", 0.45 * (1.0 - _r(t, L3.start, L4.start))
    smile = None
    sigh = 0.65 * _win(t, V_SIGH - 0.05, V_SIGH + 0.75, 0.25, 0.4)
    # listening to the cat: brows up on "I got the cat", waiting through the beat
    raised = 0.45 * _win(t, W_I + 0.15, L4.start + 0.6, 0.3, 0.6)
    if raised > 0:
        mood2, mix = "raised", raised
    # THE LAUGH IS BUILT, NOT SWITCHED ON (s6_l4): on "sleeps" the corner of his mouth goes and
    # his cheeks push his lower lids up; through "every story" he holds it in -- his eyes slide
    # away, his chin dips, the grin won't stop, his shoulders start to shake; on "day" his eyes
    # come back to her and the grin breaks wide; the snort (build_fx) -- then the burst
    b1, b2, b3 = build_stages(t)
    hold_in = b2 * (1.0 - b3)
    build = 0.5 * b1 + 0.3 * b2 + 0.2 * b3
    if build > 0:
        mood2, mix = GRIN, build
        smile = 0.5 * b1 + 0.25 * b2 + 0.2 * b3 + 0.05 * _r(t, T_SNORT - 0.1, T_SNORT + 0.1)
    # ...his shoulders hitch with it (shoulder_shrug: the shoulders only, via _s6_rig); the head
    # rides along just a little (~3 px at the close-up's zoom), so his eyes stay readable
    hunch += 0.012 * giggle(t) * tremble_env(t)
    # the snort: a jerk of the head, a hitch of the shoulders (and a puff from his nose, in draw)
    snort = _pulse(t, T_SNORT, 0.06, 0.28)
    lean -= 0.12 * snort
    hunch -= 0.14 * _pulse(t, T_SNORT + 0.01, 0.06, 0.3)
    # the laugh rides the laugh audio: it bursts on, and subsides as the sound ends (the mouth is
    # closed ~0.1 s after the audio, then the big closed smile stays)
    laugh = core.ramp(t, LAUGH.start - 0.05, LAUGH.start + 0.16, "out_cubic") * (1.0 - core.ramp(t, LAUGH.end - 0.32, LAUGH.end + 0.1, "inout_sine"))
    after = _r(t, LAUGH.end - 0.3, LAUGH.end + 0.7)
    if after > 0:
        # after the laugh: smiling eyes (cheeks up, lids soft), not wide surprise
        mood, mood2, mix = "warm", AFTER_LAUGH, 0.85 * after
        smile = core.lerp(smile if smile is not None else 0.4, 0.72, after)
    # eyes / head
    look = _track(t, [(0.0, (-0.3, 0.35)), (T_NOTICE + 0.25, (-0.3, 0.35)), (T_NOTICE + 0.4, (-0.65, 0.05)),
                      (T_NOTICE + 0.95, (-0.6, 0.05)), (T_NOTICE + 1.15, (-0.2, 0.45)),
                      (T_LAND + 0.4, (0.0, 0.3)), (T_LAND + 0.6, (-0.25, 0.75)),     # the pigeons stare at him
                      (T_LAND + 1.4, (-0.25, 0.75)), (T_LAND + 1.6, (0.15, 0.25)),
                      (V_GLANCE - 0.05, (0.15, 0.25)), (V_GLANCE + 0.08, (-0.9, 0.05)),
                      (V_GLANCE + GLANCE_HOLD, (-0.9, 0.05)), (V_GLANCE + GLANCE_HOLD + 0.12, (0.3, 0.15)),
                      (T_REACH - 0.15, (0.3, 0.15)), (T_REACH + 0.05, (0.35, 0.85)),     # down at the sack
                      (T_HOLD - 0.1, (0.0, 0.75)), (T_HOLD + 0.1, (-0.15, 0.6)),        # the book
                      (T_RELEASE, (-0.2, 0.6)), (T_RELEASE + 0.15, (-0.55, 0.55)),      # follows it
                      (T_BOOKLAND + 0.4, (-0.55, 0.55)), (T_BOOKLAND + 0.7, (0.1, 0.3)),
                      (W_TOO - 0.05, (0.1, 0.3)), (W_TOO + 0.12, (-0.75, 0.35)),        # "too?" -> her
                      (L2.start - 0.25, (-0.75, 0.35)), (L2.start - 0.05, (-0.5, 0.6)),  # the list: to the book
                      (W_YOGA - 0.12, (-0.5, 0.6)), (W_YOGA + 0.05, (-0.85, 0.32)),     # "Yoga." -> her
                      (L3.start, (-0.85, 0.35)), (W_I + 0.4, (-0.8, 0.5)), (DUR, (-0.8, 0.5))])
    # holding the laugh in: the eyes slide away from her (down, to the other side), then back on "day"
    away = _r(t, W_EVERY - 0.06, W_EVERY + 0.14) * (1.0 - _r(t, W_DAY - 0.12, W_DAY + 0.06))
    look = core.lerp_tuple(look, (0.4, 0.42), away)
    head_turn = _track(t, [(0.0, 0.0), (V_GLANCE, 0.0), (V_GLANCE + 0.12, -0.32), (V_GLANCE + GLANCE_HOLD + 0.02, -0.32),
                           (V_GLANCE + GLANCE_HOLD + 0.16, 0.08), (V_GLANCE + GLANCE_HOLD + 0.6, 0.0), (W_TOO + 0.05, 0.0), (W_TOO + 0.3, -0.12),
                           (L3.start, -0.15), (DUR, -0.15)])
    head_turn -= 0.12 * max(0.0, k_in)
    head_nod = _track(t, [(0.0, -0.25), (T_WALK_END, -0.2), (T_LAND + 0.5, -0.2), (T_LAND + 0.7, -0.35),
                          (T_LAND + 1.4, -0.35), (T_LAND + 1.6, -0.15), (T_REACH, -0.15), (T_REACH + 0.3, -0.45),
                          (T_HOLD, -0.35), (T_BOOKLAND + 0.6, -0.15), (L3.start, -0.05), (DUR, -0.05)])
    head_nod -= 0.2 * max(0.0, k_in)
    # ...the head follows the eyes away a beat later, chin down; back up to her on "day"
    away_h = _r(t, W_EVERY + 0.08, W_EVERY + 0.4) * (1.0 - _r(t, W_DAY, W_DAY + 0.3))
    head_turn += 0.14 * away_h
    head_nod -= 0.16 * away_h
    head_nod += 0.32 * snort
    head_tilt = 0.07 * _pulse(t, W_YOGA, 0.15, 0.6) + 0.06 * _win(t, T_BEAT0 + 0.2, L4.start + 0.4, 0.3, 0.5)
    head_tilt += 0.07 * after                                     # tender, toward her
    hunch += 0.1 * _pulse(t, W_YOGA + 0.05, 0.15, 0.45)        # the tiny shrug
    # blinks are acted: on thought changes, never on a look that must land ("Yoga.", the beat)
    blink = _blink_at(t, DRAGON_BLINKS)
    if abs(t - (W_VITAMINS - 0.28)) < 0.2:                         # the slow blink before "Vitamins."
        blink = max(blink, math.sin(math.pi * core.clamp((t - (W_VITAMINS - 0.48)) / 0.4)))
    # (no blink in the held look: he holds her stare; only she blinks, slow and dry)
    blink = max(blink, 0.8 * _pulse(t, T_SNORT - 0.02, 0.05, 0.22))          # the snort squeezes his eyes
    # wings: drooped (lonely) -> lifted (happy) after the laugh
    wings = -0.82 + 1.2 * _r(t, LAUGH.start, LAUGH.end + 0.6)
    wings += 0.18 * B.wobble(t, T_LAND, 2.6, 3.5) / 1.35
    tail_curl = 0.35 + 0.5 * _r(t, LAUGH.start, LAUGH.end + 0.5)
    tail_swing = 0.35 * math.sin(t * 2.2) * _r(t, LAUGH.start + 0.2, LAUGH.end + 0.5)
    # arms
    near, far = _dragon_arms(t)
    # the seat gives under him: his seat (pelvis) rides the bench's sag; his feet stay on the gravel
    seat_h = P.BENCH_SEAT_H - _STATE["garden"].seat_dip(U_DRAGON, bench_sag(t), sag_u=U_DRAGON) / SC * core.ramp(
        t, T_LAND - 0.02, T_LAND)
    pose = ch.DragonPose(facing=-1, turn=turn, sit=sit, seat_h=seat_h, walk=walk, phase=phase, lean=lean, hunch=hunch,
                         head_turn=head_turn, head_tilt=head_tilt, head_nod=head_nod, look=look, mood=mood,
                         mood2=mood2, mood_mix=mix, talk=tl.talk(SCENE, t, "MAN"), smile=smile, laugh=laugh,
                         sigh=sigh, blink=blink, wings=wings, tail_curl=tail_curl, tail_swing=tail_swing,
                         tail_drag=0.2 * (1.0 - _r(t, T_SIT0, T_LAND)), near=near, far=far, seed=6)
    return x, y, pose


# ---- the hand props ---------------------------------------------------------------------

def _bag_cb(t, swing):
    # the sack as he carried it through S3 and S4: open at the neck, the coloring book's corner
    # and the SLEEP DRAUGHT peeking out (S7 and S8 draw it open too)
    hold = P.bag_hold(L_DUSK.with_(exposure=0.8), t, swing, state="open")

    def cb(cr, f):
        hold(cr, f)
        _CAPTURE["bag_grip"] = cr.user_to_device(0.0, 0.0)
    return cb


_CAPTURE = {}


def book_state(t):
    """What the book looks like in his hand: (state, flip, page, mix) where mix is the
    closed<->open crossfade (1 = open)."""
    page, flip = 0, 0.0
    for k, tf in enumerate(T_FLIPS):
        if t >= tf + FLIP_D:
            page = k + 1
        elif t >= tf:
            flip = core.inout_sine((t - tf) / FLIP_D)
            page = k
    opened = _r(t, T_OPEN0, T_OPEN1) * (1.0 - _r(t, T_CLOSE0, T_CLOSE1))
    return flip, page % 3, opened


# the coloring book lying on the seat: props' "flat" book is seen from higher up (elev 0.32) than
# the bench (0.12), so it is drawn squashed in depth to sit in the seat's perspective (the cover
# still reads), with its front face on the seat's front edge and a contact shadow under it
FLAT_K = 0.75                    # depth squash of the flat book
BOOK_DIM = 0.72                  # shots D/E: the book on the seat a stop under the faces
FLAT_FRONT = 18.74               # props' flat book: anchor -> bottom of its front face (book units)
SEAT_FRONT_Z = 40.0              # the seat's front edge, ahead of the sitters' line (bench units)


def book_lay(cr, k):
    """Tip a book drawn about its centre toward lying flat on the seat (k 0 upright .. 1 flat):
    a little roll on the way, then the cover foreshortens into the seat's perspective; at k = 1
    it is the seated flat book's cover mapping (props' flat top face x FLAT_K), so the hand-off at
    the landing is seamless."""
    if k <= 0.0:
        return
    cr.rotate(-0.3 * math.sin(math.pi * min(1.0, k)))
    cr.transform(cairo.Matrix(1.0, 0.042 * k, -0.18 * k, 1.0 - 0.768 * k, 0.0, 0.0))


def _draw_book_in_hand(cr, t, light, lift, lay=0.0):
    """The coloring book in his near hand (callback frame: grip, upright, 1 unit = body px).
    lift 0..1: hanging from his fingers (just pulled out) -> held by its right edge.
    Opening: the cover swings up about the spine, then the left page unfolds; closing reverses.
    lay 0..1: the shut book tips toward flat as he lowers it to the seat."""
    flip, page, opened = book_state(t)
    hang = 1.0 - lift
    spine = -56.0                                   # the spine (the closed book's left edge)

    def closed():
        cx = core.lerp(-24.0, 4.0, hang)
        cy = core.lerp(-4.0, 34.0, hang)
        _CAPTURE["book_frame"] = cr.get_matrix()
        if hang > 0.0 and lay <= 0.0:
            # just pulled out of the sack: at the grab it stands exactly where the sack's book
            # corner stood (same spot, same lean, turned edge-on to us -- foreshortened), then it
            # swings round to face us and hangs from his fingers as he lifts it
            e = core.smooth(lift)
            dx, dy = _STATE.get("book_corr", (0.0, 0.0))
            cr.save()
            cr.translate(cx + dx * (1.0 - e), cy + dy * (1.0 - e))
            cr.rotate(-0.25 * hang)
            cr.scale(core.lerp(BOOK_IN_SACK_FS, 1.0, e), 1.0)
            _CAPTURE["closed_center"] = cr.user_to_device(0.0, 0.0)
            _CAPTURE["closed_quad"] = [cr.user_to_device(px, py) for px, py in
                                       ((-34.0, -37.0), (34.0, -37.0), (34.0, 37.0), (-34.0, 37.0))]
            P.draw_coloring_book(cr, 0.0, 0.0, 1.0, light, t, state="closed")
            cr.restore()
            return
        if lay > 0.0:
            cr.save()
            cr.translate(cx, cy)
            book_lay(cr, lay)
            P.draw_coloring_book(cr, 0.0, 0.0, 1.0, light, t, state="closed")
            cr.restore()
            return
        P.draw_coloring_book(cr, cx, cy, 1.0, light, t, angle=-0.25 * hang, state="closed")

    def open_book(f=0.0):
        P.draw_coloring_book(cr, spine, -4.0, 1.0, light, t, state="open", flip=f, page=page)

    if opened <= 0.0:
        closed()
    elif opened >= 1.0:
        open_book(flip)
    else:
        # the right-hand page is where the closed book was
        cr.save()
        cr.rectangle(spine, -80.0, 120.0, 160.0)
        cr.clip()
        open_book()
        cr.restore()
        k = math.cos(math.pi * opened)
        cr.save()
        if k > 0.0:                                 # the cover lifts, foreshortening onto the spine
            cr.translate(spine, 0.0)
            cr.scale(max(0.02, k), 1.0)
            cr.translate(-spine, 0.0)
            closed()
        else:                                       # the left page unfolds from the spine
            cr.rectangle(spine - 120.0, -80.0, 120.0, 160.0)
            cr.clip()
            cr.translate(spine, 0.0)
            cr.scale(max(0.02, -k), 1.0)
            cr.translate(-spine, 0.0)
            open_book()
        cr.restore()
    _CAPTURE["book_center"] = cr.user_to_device(-24.0, -4.0)


def _book_cb(t, light, lift, lay=0.0):
    def cb(cr, f):
        cr.save()
        cr.rotate(-f.angle)
        if T_GRAB <= t and not _book_out(t):
            # still in the sack: the sack draws it (in this frame) between its walls, see _draw_bag
            _CAPTURE["sack_book"] = (cr.get_matrix(), (t, light, lift, lay))
        else:
            _draw_book_in_hand(cr, t, light, lift, lay)
        cr.restore()
    return cb


def _book_out(t):
    """True once the grabbed book is clear of the sack (T_BOOK_OUT, solved in setup)."""
    return t >= _STATE.get("t_book_out", T_GRAB)


def toss_lay(t):
    """0 -> TOSS_K: the shut book tips toward flat while he lowers it."""
    return TOSS_K * _r(t, T_TOSS0 + 0.02, T_RELEASE)


STAMP_INK = 0.55                 # the SMILE print (P.smile_stamp, as S4 stamps it) -- 0.9 fresh in S4, fading


def _dragon_arms(t):
    light = light_at(t)
    swing = 0.12 * math.sin(ch.dragon_walk_phase(dragon_anchor(t)[2], SC, -1, WALK_TURN) * math.tau)
    # near arm: the sack, then the book
    if t < T_SIT0:
        near = ch.Arm("carry_bag", hold=_bag_cb(t, swing))
    elif t < T_BAG:
        near = ch.Arm("s6_set_bag", amt=_r(t, T_SIT0, T_BAG), prev="carry_bag", hold=_bag_cb(t, 0.0))
    elif t < T_REACH:
        near = ch.Arm("rest", amt=_r(t, T_BAG + 0.04, T_BAG + 0.55), prev="s6_set_bag", hand="relaxed")
    elif t < T_GRAB:
        near = ch.Arm("s6_bag", amt=_r(t, T_REACH, T_GRAB - 0.04), prev="rest")
    elif t < T_HOLD:
        lift = _r(t, T_GRAB, T_HOLD)
        near = ch.Arm("s6_book", amt=lift, prev="s6_bag", hold=_book_cb(t, light, lift))
    elif t < T_TOSS0:
        near = ch.Arm("s6_book", hold=_book_cb(t, light, 1.0))
    elif t < T_RELEASE:
        near = ch.Arm("s6_toss", amt=_r(t, T_TOSS0, T_RELEASE - 0.01), prev="s6_book", hand="grip",
                      hold=_book_cb(t, light, 1.0, toss_lay(t)))
    elif t < T_SLAP0:
        # lets go: the fingers open, the hand lifts off and drifts back to his lap
        u = _r(t, T_RELEASE + 0.02, T_RELEASE + 0.55)
        near = ch.Arm("rest", amt=u, prev="s6_toss", hand=_hand_mix("open", "relaxed", (u - 0.2) / 0.6))
    else:
        # the laugh: he slaps his knee on two of its pulses, then the hand settles back
        near = ch.Arm("s6_slap", amt=_win(t, T_SLAP0, T_SLAP1, 0.12, 0.35), prev="rest", phase=slap_lift(t))
    # far arm (his RIGHT hand, still printed SMILE from the tavern door, S4 -- the ink fading):
    # takes the left cover as the book opens, lets go as it closes; holds his belly in the laugh
    stamp = P.smile_stamp(ink=STAMP_INK)
    if T_FAR0 <= t < T_CLOSE0:
        far = ch.Arm("s6_book_far", amt=_r(t, T_FAR0, T_FAR1), prev="rest", stamp=stamp)
    elif T_CLOSE0 <= t < T_CLOSE1 + 0.45:
        far = ch.Arm("rest", amt=_r(t, T_CLOSE0, T_CLOSE1 + 0.4), prev="s6_book_far", stamp=stamp)
    elif T_SLAP0 - 0.1 <= t < T_SLAP1 + 0.5:
        # the laugh: the far hand holds his belly while the near one slaps his knee
        far = ch.Arm("s6_belly", amt=_win(t, T_SLAP0 - 0.1, T_SLAP1 + 0.5, 0.25, 0.5), prev="rest", stamp=stamp)
    else:
        far = ch.Arm("rest", stamp=stamp)
    return near, far



# ----------------------------------------------------------------------------------------
# the gnome
# ----------------------------------------------------------------------------------------

# her lazy flick at the book on "that" (shot C). GnomeArm(screen=...) replaces the amt blend with
# the screen target (the hand would teleport out and back), so the reach is a scene gesture: the
# wrist travels from EXACTLY where her resting hand lies (the library's "rest" target) to a point
# a little way toward the book, on an eased arc, and the fingers open on the way (a blended hand
# pose, never a swap). The far arm uses it for the whole of shot C (u = 0 is the rest pose), so
# the elbow's IK pole only changes on the cuts.
_GXN = {}                        # per-frame state: her anchor, yaw, the flick's u and its world goal
_G_REST = ch.GNOME_GESTURES["rest"]


def _hand_mix(a, b, u):
    """A hand pose between two base.HAND_POSES (base.hand takes the dict): fingers that open or
    curl over frames instead of swapping shape on one frame."""
    pa, pb = B.HAND_POSES[a], B.HAND_POSES[b]
    u = core.clamp(u)
    return {"curl": tuple(core.lerp(x, y, u) for x, y in zip(pa["curl"], pb["curl"])),
            "spread": core.lerp(pa["spread"], pb["spread"], u),
            "thumb": (core.lerp(pa["thumb"][0], pb["thumb"][0], u), core.lerp(pa["thumb"][1], pb["thumb"][1], u))}


def _wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _g_s6_flick(sk, side, c):
    tgt0, hp0, ha0, z0 = _G_REST(sk, side, c)
    u = _GXN.get("u", 0.0)
    if u <= 0.0 or "goal" not in _GXN:
        return tgt0, hp0, ha0, z0
    # the goal (world px) -> her body space at her shoulder's depth + 16 (as GnomeArm.screen does)
    yaw, el = _GXN["yaw"], ch.GnomePose().elev
    proj = B.Proj(yaw, el)
    cs, sn, se, ce = proj.c, proj.s, proj.se, proj.ce
    lx, ly = (_GXN["goal"][0] - _GXN["x"]) / SC, (_GXN["goal"][1] - _GXN["y"]) / SC
    depth = -sk[0] * sn + sk[2] * cs + 16.0
    goal = (lx * cs - depth * sn, (ly - depth * se) / ce, lx * sn + depth * cs)
    e = core.inout_sine(u)
    # the wrist swings out on a low arc (it dips a little and comes forward over her knee)
    arc = math.sin(math.pi * e)
    tgt = (tgt0[0] + (goal[0] - tgt0[0]) * e, tgt0[1] + (goal[1] - tgt0[1]) * e + 3.0 * arc,
           tgt0[2] + (goal[2] - tgt0[2]) * e + 4.0 * arc)

    # mid-swing her forearm points almost at the lens, where its 2D direction (which aims the
    # hand) is unstable: steer the hand's screen angle instead -- it turns smoothly from the
    # resting hand's angle to the flick's, the short way round (through "down"), never a spin
    def fore_ang(w):
        elb, wr = B.ik3(sk, w, _GN.UPPER_ARM, _GN.FOREARM, (side * 0.9, 0.8, -0.35))
        a_, b_ = proj.xy(elb), proj.xy(wr)
        return math.atan2(b_[1] - a_[1], b_[0] - a_[0])
    k = (1.0 if side < 0 else -1.0) * (1.0 if yaw >= 0 else -1.0)      # gnome._arm's hand-angle sign
    h0 = fore_ang(tgt0) + ha0 * k
    h1 = fore_ang(goal)
    want = h0 + _wrap(h1 - h0) * e
    hang = _wrap(want - fore_ang(tgt)) * k
    return tgt, _hand_mix("relaxed", "offer", e / 0.7), hang, z0


ch.GNOME_GESTURES["s6_flick"] = _g_s6_flick

# the crumb toss's END pose (the library evaluates a blend's `prev` at phase 0, i.e. the toss's
# start on her lap -- the hand used to jump back there on the hand-off)
_G_TOSS = ch.GNOME_GESTURES["toss_crumbs"]
ch.GNOME_GESTURES["s6_toss_end"] = lambda sk, side, c: _G_TOSS(sk, side, dict(c, phase=1.0))
GNOME_INWARD = 1.0               # her near hand is screen-left of her chest: the piece's torn face (setup checks)


def _tuck_hold(k, light):
    """Her bread piece in the hand (as GnomeArm(bread="piece") draws it), sinking into the
    satchel's mouth as k goes 0 -> 1 (it shrinks away under the hand)."""
    def cb(cr, f):
        if k >= 0.97:
            return
        cr.save()
        cr.rotate(-f.angle)
        cr.translate(0.0, 7.0 * k)
        ch.gnome_bread(cr, GNOME_INWARD * 3.0, -3.0, ch.GNOME_LOAF * (1.0 - k), light, "piece", face=GNOME_INWARD, seed=3)
        cr.restore()
    return cb


def _gnome_yaw(turn):
    """GnomePose yaw for facing +1 (API: turn x0.6 rad on top of the facing, clamped to +-1.45)."""
    return core.clamp(1.0 + 0.6 * turn, -1.45, 1.45)


def gnome_seat(t):
    """Her place on the bench (fraction u) and the hop height (0..1) of her two-hop shuffle."""
    prog, hop = 0.0, 0.0
    for t0, d in SCOOT_HOPS:
        u = core.clamp((t - t0) / d)
        prog += 0.5 * core.inout_sine(u)
        hop = max(hop, math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0)
    return core.lerp(U_GNOME, U_GNOME2, prog), hop


def gnome_pose(t):
    """(x, y, GnomePose): she sits at the left end; dy carries her bounce when he lands."""
    u_seat, shuffle = gnome_seat(t)
    x, y = _bench_rig().place(u_seat)
    hop = 10.0 * _bump(t, T_LAND + 0.04, 0.34) + 3.0 * _bump(t, T_LAND + 0.38, 0.18) + 6.0 * shuffle
    hop += 3.5 * _bump(t, V_KICK - 0.05, 0.3)               # a little bounce as her boots shoot out
    y -= hop
    y += _STATE["garden"].seat_dip(u_seat, bench_sag(t), sag_u=U_DRAGON)
    yaw_turn = _track(t, [(0.0, -0.5), (T_NOTICE, -0.5), (T_NOTICE + 0.6, -0.62), (T_LAND, -0.62),
                          (T_LAND + 0.8, -1.15), (CUT_C - 0.1, -1.15), (CUT_C, -0.82), (T_SCOOT0, -0.82),
                          (T_SCOOT1, -0.55), (W_I, -0.42), (DUR, -0.36)])
    look = _track(t, [(0.0, (0.5, 0.75)), (T_NOTICE, (0.5, 0.75)), (T_NOTICE + 0.12, (0.95, -0.05)),
                      (T_NOTICE + 0.75, (0.95, -0.05)), (T_NOTICE + 0.9, (0.45, 0.65)),
                      (T_LAND, (0.45, 0.65)), (T_LAND + 0.08, (0.75, -0.35)),            # startled: at him
                      (T_LAND + 0.55, (0.85, -0.05)), (T_LAND + 1.1, (0.85, -0.05)),   # the side-eye
                      (T_LAND + 1.3, (0.1, 0.25)),
                      (V_HMPH - 0.05, (0.1, 0.25)), (V_HMPH + 0.1, (-0.3, -0.25)), (V_HMPH + 0.6, (-0.3, -0.25)),
                      (V_HMPH + 0.8, (0.1, 0.25)),
                      (V_GLANCE - 0.05, (0.1, 0.25)), (V_GLANCE + 0.08, (0.95, -0.15)),
                      (V_GLANCE + GLANCE_HOLD, (0.95, -0.15)), (V_GLANCE + GLANCE_HOLD + 0.1, (-0.15, 0.2)),
                      (T_REACH + 0.2, (-0.15, 0.2)), (T_REACH + 0.35, (1.0, 0.25)),    # sidelong at the book business
                      (T_BOOKLAND - 0.1, (1.0, 0.25)), (T_BOOKLAND + 0.05, (0.75, 0.75)),
                      (CUT_C, (0.7, 0.7)),                                              # C opens on her, eyes on the book
                      (B_GLANCE.t, (0.7, 0.7)), (B_GLANCE.t + 0.16, (0.85, -0.72)),     # the glance: at HIM, over the rims
                      (W_THAT - 0.12, (0.85, -0.72)), (W_THAT - 0.02, (0.9, 0.95)),    # "that": down to the book
                      (W_TOO - 0.06, (0.9, 0.95)), (W_TOO + 0.06, (0.85, -0.8)),        # "too?": back up to him
                      (L3.start, (0.8, -0.7)), (L3.start + 0.25, (-0.28, -0.36)),      # remembering the cat: up
                      (W_I - 0.12, (-0.36, -0.3)), (W_I + 0.05, (0.85, -0.65)),        # and away (never the lens),
                                                                                       # then deadpan to him
                      (LAUGH.start + 0.2, (0.85, -0.65)), (LAUGH.start + 0.9, (0.8, -0.25)),  # chin up: she melts
                      (DUR, (0.8, -0.25))])
    head_turn = _track(t, [(0.0, 0.0), (T_NOTICE + 0.1, 0.0), (T_NOTICE + 0.3, 0.15), (T_NOTICE + 0.75, 0.15),
                           (T_NOTICE + 1.0, 0.0), (V_HMPH, 0.0), (V_HMPH + 0.16, -0.45), (V_HMPH + 0.62, -0.45),
                           (V_HMPH + 0.95, 0.0), (V_GLANCE, 0.0), (V_GLANCE + 0.12, 0.52),
                           (V_GLANCE + GLANCE_HOLD, 0.5), (V_GLANCE + GLANCE_HOLD + 0.13, -0.14), (T_REACH + 0.3, 0.08), (CUT_C, 0.0), (B_GLANCE.t + 0.12, 0.0),
                           (B_GLANCE.t + 0.4, 0.25), (W_TOO, 0.25), (W_TOO + 0.25, 0.12), (L3.start + 0.1, 0.05),
                           (L3.start + 0.4, -0.18), (W_I - 0.1, -0.18), (W_I + 0.15, 0.08), (DUR, 0.08)])
    # the little head shake on "through every story"
    head_turn += 0.07 * math.sin((t - W_SLEEPS) * math.tau * 2.2) * _win(t, W_SLEEPS + 0.3, W_EVERY + 0.6, 0.2, 0.3)
    head_nod = _track(t, [(0.0, -0.3), (T_NOTICE, -0.3), (T_NOTICE + 0.3, -0.05), (T_NOTICE + 0.9, -0.3),
                          (T_LAND, -0.3), (T_LAND + 1.3, -0.05), (V_HMPH, -0.05), (V_HMPH + 0.14, 0.55),
                          (V_HMPH + 0.62, 0.5), (V_HMPH + 0.9, -0.05), (B_GLANCE.t + 0.1, -0.05),
                          (B_GLANCE.t + 0.4, -0.3), (W_TOO, -0.3), (W_TOO + 0.2, -0.42), (L2.start + 0.4, -0.4),
                          (L2.end, -0.2), (L3.start, -0.12),
                          (T_BEAT0 + 0.1, -0.12), (T_BEAT0 + 0.4, -0.24), (LAUGH.start + 0.2, -0.2),
                          (LAUGH.start + 0.9, 0.14), (DUR, 0.1)])
    head_nod += 0.4 * _pulse(t, V_SNIFF, 0.08, 0.32) - 0.15 * _pulse(t, W_THAT, 0.12, 0.3)
    # her silent chuckle with him: small quick nods (the shoulders shake with them)
    chuckle = _win(t, LAUGH.start + 0.25, LAUGH.end + 0.35, 0.2, 0.5)
    head_nod += 0.1 * chuckle * math.sin((t - LAUGH.start) * math.tau * 4.4)
    head_tilt = (-0.08 * _win(t, V_HMPH, V_HMPH + 0.9, 0.15, 0.3) + 0.06 * _win(t, T_BEAT0, L4.start + 0.3, 0.3, 0.5)
                 + 0.07 * _win(t, B_GLANCE.t + 0.15, W_THAT, 0.3, 0.3))
    specs = 0.35 * _win(t, T_LAND + 0.05, T_LAND + 1.0, 0.08, 0.6)
    specs += _track(t, [(B_GLANCE.t + 0.04, 0.0), (B_GLANCE.t + 0.28, 0.85), (W_TOO, 0.85), (W_TOO + 0.15, 0.97),
                        (T_SCOOT0, 0.95), (T_SCOOT1, 0.55), (L3.start + 0.3, 0.3), (T_BEAT0, 0.3),
                        (T_BEAT0 + 0.3, 0.8), (LAUGH.start + 0.1, 0.8), (LAUGH.start + 0.5, 0.15), (DUR, 0.15)])
    specs = core.clamp(specs)
    # mood: the strongest of the moments wins the blend
    mood, smile = "kind", None
    windows = [
        (STARTLE, _win(t, T_LAND + 0.05, T_LAND + 0.7, 0.06, 0.4)),
        ("skeptical", 0.6 * _win(t, T_LAND + 0.5, T_LAND + 1.3, 0.2, 0.3) + 0.35 * _win(t, T_BEAT0, L4.start + 0.4, 0.25, 0.5)),
        ("bored", 0.55 * _win(t, B_GLANCE.t, W_TOO + 0.05, 0.25, 0.12)),                 # peering at the book
        ("raised", 0.4 * _win(t, W_TOO, L2.start + 0.4, 0.12, 0.4) + 0.3 * _win(t, W_YOGA, W_YOGA + 0.9, 0.15, 0.4)
         + 0.35 * _win(t, T_SNORT, LAUGH.start + 0.3, 0.1, 0.2)),
    ]
    mood2, mix = max(windows, key=lambda m: m[1])
    if mix <= 0:
        mood2 = None
    smirk = (0.35 * _win(t, V_HMPH, V_HMPH + 0.9, 0.12, 0.3) + 0.3 * _win(t, W_TOO, L2.start, 0.15, 0.4)
             + 0.25 * _win(t, W_I, L4.start, 0.2, 0.3) + 0.45 * _r(t, W_DAY - 0.2, W_DAY + 0.2) * (1.0 - _r(t, LAUGH.start, LAUGH.start + 0.4)))
    melt = _r(t, LAUGH.start + 0.1, LAUGH.start + 0.6)
    laugh = 0.0                      # she has no laugh in the audio: her chuckle is silent, mouth closed
    chk = _win(t, LAUGH.start + 0.25, LAUGH.end + 0.35, 0.2, 0.5)
    if melt > 0:
        mood, mood2, mix = "warm", "happy", melt * 0.9
        if chk > 0:                  # the silent chuckle: eyes squeezed to happy crescents
            mood2 = B.MOODS["happy"].blend(CHUCKLE, chk)
        smile = 0.55 + 0.4 * melt
    blink = _blink_at(t, GNOME_BLINKS)
    if T_BEAT0 + 0.5 < t < T_BEAT0 + 0.85:                          # one slow, dry blink in the beat
        blink = math.sin(math.pi * (t - (T_BEAT0 + 0.5)) / 0.35)
    if V_HMPH + 0.05 < t < V_HMPH + 0.75:                               # "hmph": eyes shut, nose up
        blink = core.smooth((t - V_HMPH - 0.05) / 0.08) * (1.0 - core.smooth((t - V_HMPH - 0.62) / 0.13))
    if W_SLEEPS < t < W_SLEEPS + 0.35:                                 # eyes half-close on "sleeps"
        blink = 0.55 * math.sin(math.pi * (t - W_SLEEPS) / 0.35)
    # arms: the crumb toss at the start; the lazy flick at the book on "that"; a hand to her
    # heart in the laugh
    near = ch.GnomeArm("rest")
    if t < T_TOSS_G1:
        near = ch.GnomeArm("toss_crumbs", phase=core.ramp(t, T_TOSS_G0, T_TOSS_G1), bread="piece")
    elif t < T_TUCK1:
        # the last of her bread goes back in the satchel: from where the flick's follow-through
        # ended, her hand dips to the satchel's mouth and the piece sinks in (S7: the loaf is
        # still in there, peeking out)
        u = _r(t, T_TOSS_G1, T_TUCK1 - 0.02)
        near = ch.GnomeArm("reach_satchel", amt=u, prev="s6_toss_end", hand=_hand_mix("open", "pinch", (u - 0.25) / 0.5),
                           hold=_tuck_hold(core.ramp(t, T_TUCK1 - 0.17, T_TUCK1 - 0.02, "in_quad"), light_for(t, "gnome")))
    elif t < T_TUCK1 + 0.5:
        u = _r(t, T_TUCK1, T_TUCK1 + 0.5)
        near = ch.GnomeArm("rest", amt=u, prev="reach_satchel", hand=_hand_mix("pinch", "relaxed", (u - 0.2) / 0.6))
    far = ch.GnomeArm("rest")
    if CUT_C <= t < CUT_D and "book_rest" in _STATE:
        # a lazy flick of the hand toward the book: the forearm lifts off her lap, the fingers
        # open, a little way toward it (low, small -- not a point across the bench), then back
        # down (_g_s6_flick: eased out of the resting hand and back into it)
        bx, by = _STATE["book_rest"]
        _GXN.update(x=x, y=y, yaw=_gnome_yaw(yaw_turn), u=_win(t, W_THAT - 0.3, W_TOO + 0.1, 0.22, 0.4),
                    goal=(x + 0.15 * (bx - x), y - 110.0))
        far = ch.GnomeArm("s6_flick")
    hc = _win(t, LAUGH.start + 0.35, LAUGH.end + 1.0, 0.35, 0.5)
    if hc > 0:
        far = ch.GnomeArm("hand_on_chest", amt=hc, prev="rest")
    # her volley in the tennis match: both boots shoot out toward the lens (soles to us) as she
    # sits back, then drop and swing it off. legs_out is capped at 0.5: past ~0.7 the library's
    # shins swing in under the skirt's drape at this near-front yaw and the boots vanish
    boots = _win(t, V_KICK - 0.06, V_KICK + 0.42, 0.09, 0.24)
    legs_out = 0.5 * boots
    kick = _win(t, V_KICK + 0.28, V_KICK + 1.05, 0.15, 0.35) + 0.8 * _win(t, T_SCOOT0, T_SCOOT1 + 0.2, 0.08, 0.3)
    hood = 0.9 * B.wobble(t, T_LAND + 0.05, 2.2, 2.6) / 1.35 + 0.35 * B.wobble(t, V_HMPH + 0.1, 2.4, 3.0) / 1.35
    hood += 0.3 * B.wobble(t, V_KICK + 0.04, 2.6, 3.0) / 1.35
    hood += 0.35 * chuckle * math.sin((t - LAUGH.start) * math.tau * 4.4 - 0.8)
    for h0, hd in SCOOT_HOPS:
        hood += 0.45 * B.wobble(t, h0 + hd, 2.6, 3.2) / 1.35
    lean = 0.35 * shuffle - 0.25 * _win(t, V_KICK - 0.06, V_KICK + 0.42, 0.1, 0.3)
    # the glance: a quick lean toward him with the look, the hood tip flops, her lenses flash
    lean += 0.16 * _win(t, V_GLANCE, V_GLANCE + GLANCE_HOLD + 0.1, 0.1, 0.16)
    hood += 0.5 * B.wobble(t, V_GLANCE + 0.1, 2.6, 3.2) / 1.35 + 0.45 * B.wobble(t, V_GLANCE + GLANCE_HOLD + 0.12, 2.6, 3.2) / 1.35
    glint = core.ramp(t, V_GLANCE + 0.08, V_GLANCE + 0.36) if V_GLANCE + 0.08 <= t <= V_GLANCE + 0.36 else None
    pose = ch.GnomePose(facing=1, turn=yaw_turn, sit=1.0, look=look, head_turn=head_turn, head_nod=head_nod,
                        head_tilt=head_tilt, lean=lean, legs_out=legs_out, mood=mood, mood2=mood2, mood_mix=mix, smile=smile, smirk=smirk,
                        talk=tl.talk(SCENE, t, "OLD_WOMAN"), laugh=laugh, blink=blink, specs=specs,
                        glint=glint, near=near, far=far, kick=kick, hood_swing=hood, satchel="loaf",
                        satchel_side=-1, seed=11)
    return x, y, pose



# her crumbs: the library's toss (ch.gnome_toss_crumbs) with a wider, flatter throw, so the
# pinch arcs OUT toward the pigeons before it falls instead of dribbling off her lap (body px/s
# at scale 1; x along the way she faces)
CRUMB_VX, CRUMB_VY = (70.0, 250.0), (-230.0, -110.0)


def _crumb_kw(rel, ground_y, n, seed=0):
    f = rel.facing
    return dict(n=n, seed=seed, vx=(f * CRUMB_VX[0], f * CRUMB_VX[1]), vy=CRUMB_VY, ground_y=ground_y,
                scale=rel.scale, release=0.1)


def crumb_landings(t0, rel, ground_y, n=10):
    """[(x_rest, t_rest, y)] of toss_crumbs (as ch.gnome_crumb_landings)."""
    h = rel.hand_near
    return [(lx, tr, ground_y) for lx, tr in fx.crumb_landings(t0, h.x, h.y, **_crumb_kw(rel, ground_y, n))]


def toss_crumbs(cr, t, t0, rel, ground_y, n=10, flock=None):
    """The crumbs she flicks at t0 from her hand at the release (rig `rel`); the ones the pigeons
    have pecked up are gone (as ch.gnome_toss_crumbs)."""
    h = rel.hand_near
    kw = _crumb_kw(rel, ground_y, n)
    gone = []
    if flock is not None:
        gone = [lx for k, (lx, _tr) in enumerate(fx.crumb_landings(t0, h.x, h.y, **kw)) if flock.crumb_eaten(k, t)]
    cr.save()
    if gone:
        cr.new_path()
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)          # everything but small discs round the eaten
        cr.rectangle(-1e5, -1e5, 2e5, 2e5)
        for lx in gone:
            cr.new_sub_path()
            cr.arc(lx, ground_y, 9.0 * rel.scale, 0.0, math.tau)
        cr.clip()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    fx.crumbs(cr, t, t0, h.x, h.y, size=3.0, color=ch.GNOME_COLORS["crumb"], crust=ch.GNOME_COLORS["crust"], **kw)
    cr.restore()


# ----------------------------------------------------------------------------------------
# the pigeons: a scripted little troupe (natural business + the synchronized swivel)
# ----------------------------------------------------------------------------------------

def _swivel_track():
    """[(t, target)] for the shared head swivel (+1 him / screen-right, -1 her, 0 the lens).
    The pause is a tennis match that speeds up; in the dialogue the heads follow the speaker
    (and in the beat the umpire looks to him for an answer, then back to her)."""
    return [(V_HIM0, 1.0), (V_HMPH + 0.06, -1.0), (V_SHIFT + 0.06, 1.0), (V_KICK + 0.06, -1.0),
            (V_SIGH + 0.08, 1.0), (V_SNIFF + 0.06, -1.0), (V_GLANCE + 0.08, 0.0), (T_REACH + 0.04, 1.0),
            (B_GLANCE.t, -1.0), (L2.start - 0.05, 1.0), (L3.start - 0.05, -1.0), (T_BEAT0 + 0.45, 1.0),
            (L4.start + 0.02, -1.0), (LAUGH.start - 0.1, 1.0)]


SWIVEL = _swivel_track()
SNAP = 0.15                       # the turn itself
LATE = {2: (V_HMPH, 0.36), 4: (V_GLANCE, 0.3)}     # bird -> (volley, delay): always one beat late


def _snap_curve(u):
    """A head snap 0 -> 1: tiny anticipation, fast turn, overshoot, settle (u in seconds/SNAP)."""
    if u <= 0.0:
        return 0.0
    if u < 0.25:
        return -0.06 * math.sin(math.pi * u / 0.25)
    v = (u - 0.25) / 0.75
    if v < 1.0:
        return core.out_back(v, 1.9)
    return 1.0


def swivel_at(t, bird):
    """The sync head swivel value for one bird at t (with its little lag). Each volley snaps
    from wherever the head was at that moment (no pops even when volleys overlap)."""
    lag = 0.012 * bird
    v = SWIVEL[0][1]
    for k, (tk, target) in enumerate(SWIVEL):
        d = lag + (LATE[bird][1] if bird in LATE and abs(LATE[bird][0] - tk) < 0.2 else 0.0)
        if t < tk + d:
            break
        u = (t - tk - d) / SNAP
        v = v + (target - v) * _snap_curve(u) if k > 0 else target
    return core.clamp(v, -1.0, 1.0)


class Troupe:
    """Five pigeons on the walk in front of the bench and one 'umpire' on its backrest.

    Each bird has segments (t0, t1, kind, xa, ya, xb, yb, facing) like ch.PigeonFlock's, and
    a weight for the shared swivel over time. crumb_eaten(k, t) lets toss_crumbs hide
    the crumbs they have pecked up."""

    def __init__(self, landings, perch):
        self.crumbs = landings          # [(x, t_rest, y)]
        self.eaten = {}
        self.birds = []
        sp = [(752.0, 979.0, 1), (803.0, 956.0, -1), (851.0, 986.0, 1), (898.0, 960.0, -1), (940.0, 982.0, -1)]
        self.spots = sp
        starts = [(700.0, 990.0, 1), (770.0, 952.0, 1), (905.0, 990.0, -1), (850.0, 958.0, 1), (1165.0, 968.0, -1)]
        order = sorted(range(len(landings)), key=lambda k: landings[k][0])
        claimed = set()
        for i in range(5):
            x0, y0, f0 = starts[i]
            gx, gy, gf = sp[i]
            segs = []
            t = 0.0
            if i == 4:      # the scurrier: pecking in his path, hurries off as he comes
                segs.append((0.0, 0.85, "peck", x0, y0, x0, y0, f0))
                segs.append((0.85, 1.75, "walk", x0, y0, gx, gy, -1))
                t = 1.75
                x0, y0 = gx, gy
            else:
                segs.append((0.0, 0.5 + 0.2 * i, "peck" if i % 2 == 0 else "idle", x0, y0, x0, y0, f0))
                t = 0.5 + 0.2 * i
            # go for the nearest unclaimed crumb near the bird's spot, peck it up
            best = None
            for k in order:
                if k in claimed:
                    continue
                cx, ct, cy = landings[k]
                d = abs(cx - gx)
                if d < 70.0 and (best is None or d < best[0]):
                    best = (d, k)
            if best is not None:
                k = best[1]
                claimed.add(k)
                cx, ct, cy = landings[k]
                f = 1 if cx >= x0 else -1
                tx = cx - f * 22.0 * SC
                t_go = max(t, ct - 0.25)
                dur = max(0.3, (abs(tx - x0) + abs(gy - y0)) / (60.0 * SC))
                segs.append((t, t_go, "idle", x0, y0, x0, y0, f0))
                segs.append((t_go, t_go + dur, "walk", x0, y0, tx, gy, f))
                segs.append((t_go + dur, t_go + dur + 0.84, "peck", tx, gy, tx, gy, f))
                self.eaten[k] = t_go + dur + 0.7
                t = t_go + dur + 0.84
                x0, y0, f0 = tx, gy, f
            # back to its spot for the match
            if abs(x0 - gx) > 2.0 and t < T_LAND - 0.3:
                f = 1 if gx >= x0 else -1
                dur = max(0.3, abs(gx - x0) / (55.0 * SC))
                segs.append((t, min(T_LAND - 0.05, t + dur), "walk", x0, y0, gx, gy, f))
                t = min(T_LAND - 0.05, t + dur)
                x0, y0, f0 = gx, gy, gf
            if t < T_LAND:
                segs.append((t, T_LAND + 0.03 * i, "peck" if i in (0, 3) else "idle", x0, y0, x0, y0, f0))
            # the startle when the bench creaks: a hop and a flap, then stand and watch
            ts = T_LAND + 0.03 * i
            segs.append((ts, ts + 0.42, "hop", x0, y0, x0 + gf * 6.0, y0, f0))
            segs.append((ts + 0.42, ts + 1.0, "flap", x0 + gf * 6.0, y0, x0 + gf * 6.0, y0, gf))
            # the laugh startles them again
            tl0 = LAUGH.start + 0.08 + 0.04 * i
            xs = x0 + gf * 6.0
            segs.append((ts + 1.0, tl0, "idle", xs, y0, xs, y0, gf))
            segs.append((tl0, tl0 + 0.85, "flap", xs, y0, xs, y0, gf))
            segs.append((tl0 + 0.85, LAUGH.end + 1.1 + 0.2 * i, "idle", xs, y0, xs, y0, gf))
            segs.append((LAUGH.end + 1.1 + 0.2 * i, DUR + 1.0, "peck", xs, y0, xs, y0, gf))
            self.birds.append({"segs": segs, "seed": 61 + i * 7, "t0s": [s[0] for s in segs]})
        # the umpire: flies in from up right and perches on the middle of the backrest; when the
        # dragon leans in it sidesteps twice toward her (making room for his head); the laugh
        # startles it up and it settles back on the middle (S7 picks it up there)
        ux, uy = perch
        h1, h2 = UMP_HOPS
        x1, x2 = ux - UMP_STEP, ux - 2.0 * UMP_STEP
        # (it comes in high from the right, above his horns, and drops onto its chair over the
        # empty middle of the bench -- never crossing his head)
        segs = [(T_UMP0, T_UMP1, "fly", ux + 300.0, uy - 420.0, ux, uy, -1),
                (T_UMP1, T_UMP1 + 0.45, "land", ux, uy, ux, uy, -1),
                (T_UMP1 + 0.45, h1, "idle", ux, uy, ux, uy, -1),
                (h1, h1 + 0.16, "hop", ux, uy, x1, uy, -1),
                (h1 + 0.16, h2, "idle", x1, uy, x1, uy, -1),
                (h2, h2 + 0.16, "hop", x1, uy, x2, uy, -1),
                (h2 + 0.16, LAUGH.start + 0.1, "idle", x2, uy, x2, uy, -1),
                (LAUGH.start + 0.1, LAUGH.start + 0.95, "flaphop", x2, uy, ux, uy, -1),
                (LAUGH.start + 0.95, DUR + 1.0, "idle", ux, uy, ux, uy, -1)]
        self.birds.append({"segs": segs, "seed": 101, "t0s": [s[0] for s in segs], "umpire": True})

    def crumb_eaten(self, k, t):
        e = self.eaten.get(k)
        return e is not None and t >= e

    def sync_weight(self, t, i):
        w = _r(t, T_LAND + 0.32, T_LAND + 0.5) * (1.0 - _r(t, LAUGH.start + 0.05, LAUGH.start + 0.2))
        w = max(w, 0.85 * _r(t, LAUGH.start + 1.0, LAUGH.start + 1.4) * (1.0 - _r(t, LAUGH.end + 0.9 + 0.2 * i,
                                                                                     LAUGH.end + 1.3 + 0.2 * i)))
        return w

    def look_at(self, t, i, x):
        """The shared look for bird i at t (screen -1..1): the swivel track, except while the
        book flies, when every head follows it (blended in and out, never a pop)."""
        v = swivel_at(t, i)
        wb = core.ramp(t, T_RELEASE - 0.05, T_RELEASE + 0.1) * (1.0 - core.ramp(t, T_BOOKLAND + 0.45, T_BOOKLAND + 0.7))
        if wb > 0.0:
            bx = _book_flight(t)[0] if t < T_BOOKLAND else _STATE["book_rest"][0]
            v = core.lerp(v, core.clamp((bx - x) / 60.0, -1.0, 1.0), core.smooth(wb))
        return v

    def pose_at(self, b, i, t):
        segs = b["segs"]
        if t < segs[0][0]:
            if b.get("umpire"):
                return None
            s = segs[0]
            return (s[3], s[4], ch.PigeonPose(facing=s[7], seed=b["seed"]))
        j = bisect.bisect_right(b["t0s"], t) - 1
        t0, t1, kind, xa, ya, xb, yb, f = segs[j]
        u = core.clamp((t - t0) / max(1e-6, t1 - t0))
        seed = b["seed"]
        stride = ch.pigeon_stride(SC)
        if kind == "walk":
            x, y = core.lerp(xa, xb, u), core.lerp(ya, yb, u)
            dist = abs(x - xa) + abs(y - ya)
            p = ch.PigeonPose(facing=f, walk=1.0, phase=dist / max(1e-6, stride), seed=seed)
        elif kind == "peck":
            x, y = xa, ya
            p = ch.PigeonPose(facing=f, peck=((t - t0) / 0.42) % 1.0, seed=seed)
        elif kind == "hop":
            x, y = core.lerp(xa, xb, u), ya
            p = ch.PigeonPose(facing=f, hop=u, flap=0.6 * math.sin(math.pi * u), seed=seed)
        elif kind == "flap":
            x, y = xa, ya
            p = ch.PigeonPose(facing=f, flap=math.sin(math.pi * u), lift=9.0 * math.sin(math.pi * u), seed=seed)
        elif kind == "flaphop":                       # startled up, flutters, lands a little way off
            x, y = core.lerp(xa, xb, core.smooth(u)), core.lerp(ya, yb, u)
            p = ch.PigeonPose(facing=f, flap=math.sin(math.pi * u), lift=16.0 * math.sin(math.pi * u), seed=seed)
        elif kind == "fly":
            # across fast and high, then down onto the perch: x settles before the height does
            x = core.lerp(xa, xb, core.out_cubic(u))
            y = yb
            lift = (yb - ya) * (1.0 - u) ** 1.25
            p = ch.PigeonPose(facing=f, fly=1.0, lift=lift / SC, seed=seed)
        elif kind == "land":
            x, y = xb, yb
            p = ch.PigeonPose(facing=f, flap=1.0 - u, lift=4.0 * (1.0 - u), seed=seed)
        else:
            x, y = xa, ya
            nod = core.noise1((t + seed) * 0.6, seed)
            look = f * (1.0 - 1.1 * core.smooth((abs(nod) - 0.45) / 0.2)) if abs(nod) > 0.45 else None
            p = ch.PigeonPose(facing=f, look=look, puff=0.3 * max(0.0, core.noise1(t * 0.3, seed + 5)), seed=seed)
        return (x, y, self._turn_hop(segs, j, t, p))

    TURN = 0.08                       # half a hop-turn (s)

    def _turn_hop(self, segs, j, t, p):
        """Wherever a bird changes facing between two segments it turns in a little hop: the
        body flips at the top of it with the head swivelled to the lens (no profile pop)."""
        for k in (j, j + 1):
            if 0 < k < len(segs) and segs[k][7] != segs[k - 1][7] and abs(t - segs[k][0]) < self.TURN:
                u = (t - (segs[k][0] - self.TURN)) / (2.0 * self.TURN)
                return p.with_(hop=max(p.hop, u), flap=max(p.flap, 0.35 * math.sin(math.pi * u)), look=0.0)
        return p

    def states(self, t):
        out = []
        for i, b in enumerate(self.birds):
            st = self.pose_at(b, i, t)
            if st is None:
                continue
            x, y, p = st
            w = self.sync_weight(t, i)
            if b.get("umpire"):
                # just landed: its head comes round from its flight facing to the match (no pop)
                w *= core.ramp(t, T_UMP1, T_UMP1 + 0.22, "inout_sine")
            if w > 0.0 and p.fly < 0.5:
                nat = p.look if p.look is not None else float(p.facing)
                tgt = self.look_at(t, i, x)
                look = core.lerp(nat, tgt, w)
                # a pecking bird lifts its head to watch (the dip shrinks with the weight)
                peck = p.peck
                if peck > 0:
                    dip = math.sin(math.pi * peck) ** 1.5 * (1.0 - w)
                    peck = math.asin(min(1.0, dip ** (1.0 / 1.5))) / math.pi if dip > 1e-4 else 0.0
                p = p.with_(look=look, peck=peck, puff=p.puff * (1.0 - w))
            # the coo after the laugh: chests puff
            p = p.with_(puff=max(p.puff, 0.7 * _win(t, LAUGH.end + 0.3 + 0.1 * i, LAUGH.end + 1.4 + 0.1 * i, 0.2, 0.4)))
            if b.get("umpire"):
                # an indignant ruffle after it has had to make room for him
                hop_end = UMP_HOPS[1] + 0.16
                p = p.with_(puff=max(p.puff, 0.85 * _win(t, hop_end, hop_end + 0.7, 0.08, 0.4)))
            out.append((x, y, p, b.get("umpire", False)))
        return out


def _book_flight(t):
    """The book's short fall after he lets go: (x, y, lay 0..1) -- it drops (gravity: y ~ u^2)
    and finishes tipping flat as it lands."""
    x0, y0 = _STATE["book_release"]
    x1, y1 = _STATE["book_rest"]
    u = core.clamp((t - T_RELEASE) / (T_BOOKLAND - T_RELEASE))
    x = core.lerp(x0, x1, core.out_quad(u))
    y = core.lerp(y0, y1, u * u)
    return x, y, core.lerp(TOSS_K, 1.0, core.out_quad(u))



# ----------------------------------------------------------------------------------------
# the gallery (shot B): four pigeons on the gravel close to the lens -- the spectators
# ----------------------------------------------------------------------------------------
# bird -> [(volley time, delay)]: bird 3 (index 2) is always a beat late
GALLERY_LATE = {2: [(V_HMPH, 0.3), (V_SNIFF, 0.22), (V_GLANCE, 0.2)]}
GALLERY_PF = 1.42                 # their plane's parallax (in front of the bench plane)


def gallery_swivel(t, i):
    """The synchronized head swivel for gallery bird i (screen -1 her .. +1 him, 0 the lens):
    every volley snaps from wherever the head was (no pops when volleys overlap)."""
    late = GALLERY_LATE.get(i, ())
    v = SWIVEL[0][1]
    for k, (tk, target) in enumerate(SWIVEL):
        d = 0.015 * i
        for (tv, dl) in late:
            if abs(tv - tk) < 0.2:
                d += dl
        if t < tk + d:
            break
        u = (t - tk - d) / SNAP
        v = v + (target - v) * _snap_curve(u) if k > 0 else target
    return core.clamp(v, -1.0, 1.0)


class Gallery:
    """Shot B's spectators: a row of four big pigeons along the bottom of the frame, between
    the two players, on a foreground plane (parallax GALLERY_PF). Placed against the shot's
    first camera (screen positions -> plane coordinates), so the slow push-in gives them real
    foreground parallax. They peck, startle at the creak, then watch the match."""

    # (screen x of the feet, screen y of the feet, facing, on-screen height px) at CAM_B0.
    # A pigeon reaches ~0.77 h behind its feet (tail) and ~0.61 h ahead (beak): spaced so the two
    # middle birds' tails (2 faces left, 3 faces right) clear each other by ~20 px and the beaks
    # of 1-2 and 3-4 don't touch -- four clean silhouettes, no accidental X between them
    SPOTS = [(646.0, 1014.0, 1, 128.0), (818.0, 1004.0, -1, 122.0), (1036.0, 1017.0, 1, 131.0),
             (1208.0, 1008.0, -1, 125.0)]

    def __init__(self, cam_ref):
        pf = GALLERY_PF
        z = cam_ref.zoom ** pf
        cx = core.W / 2 + (cam_ref.x - core.W / 2) * pf
        cy = core.H / 2 + (cam_ref.y - core.H / 2) * pf
        self.birds = []
        for i, (sx, sy, f, hpx) in enumerate(self.SPOTS):
            self.birds.append({"x": cx + (sx - core.W / 2) / z, "y": cy + (sy - core.H / 2) / z,
                               "f": f, "sc": hpx / ch.PIGEON_HEIGHT / z, "seed": 201 + 13 * i})

    def pose(self, i, t, cam):
        b = self.birds[i]
        x, y, f, seed = b["x"], b["y"], b["f"], b["seed"]
        ts = T_LAND + 0.035 * i                       # the creak startles them
        p = ch.PigeonPose(facing=f, seed=seed)
        if t < ts:
            if i in (0, 2):
                p = p.with_(peck=((t - CUT_B + 0.17 * i) / 0.46) % 1.0)
        elif t < ts + 0.4:
            u = (t - ts) / 0.4
            p = p.with_(hop=u, flap=0.8 * math.sin(math.pi * u))
            x += f * 7.0 * core.out_quad(u) / b["sc"] * 0.0
        elif t < ts + 0.95:
            u = (t - ts - 0.4) / 0.55
            p = p.with_(flap=math.sin(math.pi * u) * (1.0 - u), lift=6.0 * math.sin(math.pi * u))
        # watching: the shared swivel (blended in as they settle)
        w = _r(t, ts + 0.3, ts + 0.55)
        if w > 0.0:
            v = gallery_swivel(t, i)
            # while the book flies, every head follows it (screen direction from this bird)
            wb = core.ramp(t, T_RELEASE - 0.05, T_RELEASE + 0.1)
            if wb > 0.0:
                bx = _book_flight(t)[0] if t < T_BOOKLAND else _STATE["book_rest"][0]
                bsx, _ = cam.to_screen(bx, 800.0, 1.0)
                sx, _ = cam.to_screen(x, y, GALLERY_PF)
                v = core.lerp(v, core.clamp((bsx - sx) / 140.0, -1.0, 1.0), core.smooth(wb))
            nat = float(f)
            p = p.with_(look=core.lerp(nat, v, w), peck=p.peck * (1.0 - w))
        # the stare into the lens ends in one synchronized blink
        if T_SYNC_BLINK <= t < T_SYNC_BLINK + 0.2:
            p = p.with_(blink=math.sin(math.pi * (t - T_SYNC_BLINK) / 0.2))
        elif w > 0.5:
            p = p.with_(blink=0.0)
        # a puffed chest now and then while they wait; the shared head-tilt "huh?" in the stare
        p = p.with_(puff=0.25 * max(0.0, core.noise1(t * 0.35, seed + 3)),
                    tilt=0.22 * _win(t, V_GLANCE + 0.2, P1 + 0.1, 0.18, 0.25))
        return x, y, p

    def draw(self, cr, t, cam, light, g=None):
        with cam.view(cr, GALLERY_PF):
            poses = [(i, b) + self.pose(i, t, cam) for i, b in sorted(enumerate(self.birds), key=lambda ib: ib[1]["y"])]
            # grounded like everything else in the shot: a soft dark-violet contact shadow under
            # each bird and a long dusk shadow falling right on their own (foreground) plane; both
            # thin out while a bird is up in a startle hop or flap
            for i, b, x, y, p in poses:
                sc, f = b["sc"], p.facing
                up = (p.lift + 13.0 * math.sin(math.pi * core.clamp(p.hop))) * sc
                k = 1.0 - 0.6 * core.clamp(up / (16.0 * sc))
                cx = x - f * 3.5 * sc                       # under the body (it sits a little behind the feet)
                if g is not None:
                    g.long_shadow(cr, cx, y + 0.5 * sc, 32.0 * sc, 30.0 * sc, "dusk", alpha=k)
                B.contact_shadow(cr, cx, y + 0.8 * sc, 25.0 * sc, 5.2 * sc, alpha=0.62 * k, color="#1b1530")
            for i, b, x, y, p in poses:
                ch.draw_pigeon(cr, x, y, b["sc"], p, light, t)


# ----------------------------------------------------------------------------------------
# sound cues (the sound designer synthesizes foley from these; times follow the animation)
# ----------------------------------------------------------------------------------------

def _pan_of(x_world, t):
    _name, cam = camera(t)
    sx, _sy = cam.to_screen(x_world, 900.0)
    return round(core.clamp((sx - 960.0) / 960.0, -1.0, 1.0), 2)


def _sfx_cues():
    cues = []
    xg = BENCH.x + (U_GNOME - 0.5) * (BENCH.length - 60.0) * SC
    xd = BENCH.x + (U_DRAGON - 0.5) * (BENCH.length - 60.0) * SC
    # his footsteps on the gravel: one per half walk cycle while walking
    stride = ch.dragon_stride(SC, -1, WALK_TURN)
    t = 0.05
    last = -1
    while t < T_WALK_END + 0.1:
        x0 = xd + WALK_FROM
        dist = walk_dist(t)
        step = int((dist / stride) * 2.0)
        if step != last and last >= 0:
            cues.append((round(t, 3), "footstep", {"gain": 0.45, "pan": _pan_of(x0 - dist, t), "surface": "gravel"}))
        last = step
        t += 1.0 / 48.0
    cues += [
        (round(T_CRUMBS, 3), "crumbs", {"gain": 0.35, "pan": _pan_of(xg + 30, T_CRUMBS)}),
        (round(T_CRUMBS + 0.75, 3), "pigeon_coo", {"gain": 0.3, "pan": -0.15}),
        (round(T_SIT0 + 0.2, 3), "cloth_rustle", {"gain": 0.4, "pan": _pan_of(xd, T_SIT0)}),
        (round(T_BAG, 3), "paper_slide", {"gain": 0.3, "pan": _pan_of(xd + 50, T_BAG), "size": 0.5}),
        (round(T_LAND, 3), "bench_creak", {"gain": 1.0, "pan": _pan_of(xd, T_LAND), "size": 1.0}),
        (round(T_LAND + 0.4, 3), "bench_creak", {"gain": 0.45, "pan": _pan_of(xg, T_LAND + 0.4), "size": 0.5}),
        # the gallery right by the lens startles: close, full-bodied flaps
        (round(T_LAND + 0.04, 3), "pigeon_flap", {"gain": 0.85, "pan": -0.1, "size": 0.8}),
        (round(T_LAND + 0.14, 3), "pigeon_flap", {"gain": 0.7, "pan": 0.15, "size": 0.7}),
        (round(T_UMP0 + 0.2, 3), "pigeon_flap", {"gain": 0.4, "pan": 0.2}),
        (round(T_UMP1, 3), "pigeon_flap", {"gain": 0.55, "pan": 0.05}),
        (round(V_HMPH, 3), "cloth_rustle", {"gain": 0.18, "pan": -0.45, "size": 0.3}),
        (round(V_SHIFT, 3), "bench_creak", {"gain": 0.55, "pan": _pan_of(xd, V_SHIFT), "size": 0.6}),
        (round(V_KICK, 3), "cloth_rustle", {"gain": 0.2, "pan": -0.45, "size": 0.3}),
        (round(V_SIGH, 3), "sigh", {"gain": 0.45, "pan": _pan_of(xd, V_SIGH)}),
        (round(V_SIGH + 0.12, 3), "smoke_puff", {"gain": 0.3, "pan": _pan_of(xd, V_SIGH)}),
        (round(T_SYNC_BLINK + 0.25, 3), "pigeon_coo", {"gain": 0.4, "pan": 0.0}),
        (round(T_REACH, 3), "paper_slide", {"gain": 0.45, "pan": _pan_of(xd + 60, T_REACH)}),
        (round(T_BAGOPEN, 3), "cloth_rustle", {"gain": 0.3, "pan": _pan_of(xd + 60, T_BAGOPEN), "size": 0.4}),
        (round(T_OPEN0 + 0.05, 3), "book_open", {"gain": 0.5, "pan": _pan_of(xd - 20, T_OPEN0)}),
    ]
    for tf in T_FLIPS:
        cues.append((round(tf + 0.1, 3), "page_turn", {"gain": 0.4, "pan": _pan_of(xd - 20, tf)}))
    cues += [
        (round(T_CLOSE0 + 0.08, 3), "book_close", {"gain": 0.5, "pan": _pan_of(xd - 20, T_CLOSE0)}),
        (round(T_BOOKLAND, 3), "item_set_down", {"gain": 0.55, "pan": _pan_of(BENCH.x + 20, T_BOOKLAND), "surface": "wood"}),
        (round(T_BOOKLAND + 0.02, 3), "tap_wood", {"gain": 0.25, "pan": _pan_of(BENCH.x + 20, T_BOOKLAND)}),
        (round(T_SCOOT0 + 0.02, 3), "cloth_rustle", {"gain": 0.3, "pan": -0.3, "size": 0.4}),
        (round(SCOOT_HOPS[0][0] + SCOOT_HOPS[0][1], 3), "bench_creak", {"gain": 0.3, "pan": -0.25, "size": 0.3}),
        (round(SCOOT_HOPS[1][0] + SCOOT_HOPS[1][1], 3), "bench_creak", {"gain": 0.3, "pan": -0.15, "size": 0.3}),
        # he leans in to listen (his coat), and the umpire hops out of his way (two wing flicks)
        (round(T_LEAN0, 3), "cloth_rustle", {"gain": 0.22, "pan": _pan_of(xd - 60.0, T_LEAN0), "size": 0.4}),
        (round(UMP_HOPS[0] + 0.02, 3), "pigeon_flap", {"gain": 0.16, "pan": _pan_of(BENCH.x, UMP_HOPS[0]), "size": 0.2}),
        (round(UMP_HOPS[1] + 0.02, 3), "pigeon_flap", {"gain": 0.16, "pan": _pan_of(BENCH.x - 20.0, UMP_HOPS[1]), "size": 0.2}),
        (round(LAUGH.start + 0.02, 3), "cloth_rustle", {"gain": 0.3, "pan": _pan_of(xd - 40.0, LAUGH.start), "size": 0.5}),
        (round(T_SNORT, 3), "smoke_puff", {"gain": 0.4, "pan": 0.35, "size": 0.3}),
        (round(T_SNORT + 0.02, 3), "ember_crackle", {"gain": 0.25, "pan": 0.35, "size": 0.2}),
        (round(T_EMBERS, 3), "ember_crackle", {"gain": 0.75, "pan": 0.35, "size": 1.0}),
        (round(T_EMBERS + 0.55, 3), "ember_crackle", {"gain": 0.4, "pan": 0.35, "size": 0.6}),
        (round(LAUGH.start + 0.1, 3), "wing_flutter", {"gain": 0.45, "pan": 0.45}),
        (round(LAUGH.start + 0.1, 3), "pigeon_flap", {"gain": 0.5, "pan": 0.0}),
        (round(LAUGH.start + 0.15, 3), "bench_creak", {"gain": 0.35, "pan": 0.35, "size": 0.5}),
        (round(LAUGH.end + 0.5, 3), "pigeon_coo", {"gain": 0.4, "pan": -0.1}),
    ]
    for ts in SLAPS:                         # the knee slaps: a flat hand on his coat
        cues.append((round(ts, 3), "cloth_rustle", {"gain": 0.32, "pan": _pan_of(xd - 30.0, ts), "size": 0.45}))
    cues += [
        (round(LAUGH.end + 1.1, 3), "pigeon_coo", {"gain": 0.3, "pan": 0.2}),
    ]
    return sorted([c for c in cues if 0.0 <= c[0] < DUR], key=lambda c: c[0])


SFX_CUES = _sfx_cues()
_check_blinks()


# ----------------------------------------------------------------------------------------
# setup: cache the garden, precompute the props' hand-offs and the pigeons
# ----------------------------------------------------------------------------------------

def _scratch():
    return core.frame(8, 8)[1]


def _bag_contents_no_book(q):
    """props' open-sack contents minus the coloring book (he has taken it out): just the SLEEP
    DRAUGHT's neck and cork (mirrors props._bag_contents)."""
    cr = q.cr
    ns, no = P._rrect_paths(cr, 13.0, -16.0, 10.0, 28.0, 3.0, q.lw)
    q.shade(ns, "blue_glass", 10.0, outline=no, rim=0.6)
    cs, co = P._rrect_paths(cr, 13.5, -25.0, 9.0, 10.0, 2.0, q.lw)
    q.shade(cs, "cork", 9.0, outline=co, rim=0.5)


# the open sack without the book relies on two private props helpers; if they ever change,
# fall back to the library's open sack (the book's corner then still peeks out -- cosmetic)
_CAN_EMPTY_BAG = hasattr(P, "_bag_contents") and hasattr(P, "_rrect_paths")

# the hand-off sack -> hand: the book corner props draws in the open sack stands centred at
# BOOK_IN_SACK (sack units: the visible quad is ~31 wide incl. its spine, leaning ~0.2 rad), i.e.
# the real book (64 wide) turned nearly edge-on: foreshortened to BOOK_IN_SACK_FS
BOOK_IN_SACK = (-5.5, 10.0)
BOOK_IN_SACK_FS = 0.48
# until it is clear of the sack the grabbed book is drawn by the sack (between its back wall and
# its front: still IN it), in the frame his hand gives it; then his hand draws it (_book_out)


def setup():
    st = {}
    _STATE.clear()
    g = G.Garden(kinds=("dusk", "golden"))
    _STATE["garden"] = g
    st["g"] = g
    _STATE["bench"] = g.bench(1)
    _STATE["far_walk"] = {k: _far_walk_layer(k) for k in ("dusk", "golden")}
    st["light"] = fx.LightLayer()
    st["gallery"] = Gallery(CAM_B0)
    # the gnome's crumbs: her rig at the release
    gx, gy, gp = gnome_pose(T_CRUMBS)
    with R6.gnome_patch():
        rel = ch.gnome_rig_at(gx, gy, SC, gp, T_CRUMBS, L_DUSK)
    ground = 968.0
    landings = crumb_landings(T_CRUMBS, rel, ground, n=10)
    st["crumb_rel"] = rel
    st["crumb_ground"] = ground
    # the umpire's perch: the top of the crest board, mid-bench
    perch = _bench_rig()._pt(0.0, -(P.BENCH_SEAT_H + 108.0 + 9.0), -48.0 - 0.22 * 117.0)
    st["troupe"] = Troupe(landings, perch)
    # hand-offs: where the sack is let go, where the book leaves his hand
    for tt in (T_BAG - 1e-3,):
        x, y, pose = dragon_pose(tt)
        draw_dragon(_scratch(), x, y, SC, pose, L_DUSK, tt)
    bx, by = _CAPTURE.get("bag_grip", (BENCH.x + 200.0, BENCH.y - 60.0))
    bag_ground = BENCH.y + 16.0
    _STATE["bag_drop"] = (bx, by)
    _STATE["bag_rest"] = (bx, bag_ground - 86.5 * SC)
    # the sack's mouth (for the s6_bag reach)
    _STATE["bag_mouth_world"] = (bx + 2.0, bag_ground - 86.5 * SC - 4.0)
    fx_, fy_ = _bench_rig()._pt((U_BOOK - 0.5) * (BENCH.length - 60.0), -P.BENCH_SEAT_H, SEAT_FRONT_Z)
    _STATE["book_front"] = (fx_, fy_)
    _STATE["book_rest"] = (fx_, fy_ - FLAT_FRONT * SC * FLAT_K)
    _solve_toss()
    _solve_book_far()
    _solve_book_in_sack()
    _solve_book_out()
    # where the warmth starts: his mouth as the laugh bursts (a scratch draw: every frame must
    # render on its own, in any order)
    _STATE["ember_origin"] = _far_grip(T_EMBERS).mouth
    _STATE["sigh_nose"] = _far_grip(V_SIGH + 0.1).nose
    return st


DROP = 20.0          # world px the book falls after he lets go (~10 cm: 0.14 s of free fall)


def _solve_toss():
    """Where his wrist must go so the held book hangs DROP px above its resting spot on the seat
    at the moment he lets go: a few fixed-point steps on the measured book centre (scratch
    draws, once). Sets the release point the fall starts from."""
    bx, by = _STATE["book_rest"]
    want = (bx + 3.0, by - DROP)
    goal = (want[0] + 24.0 * SC, want[1] + 30.0 * SC)
    tt = T_RELEASE - 1e-3
    got = want
    for _ in range(4):
        _STATE["toss_goal"] = goal
        _CAPTURE.pop("book_center", None)
        _far_grip(tt)
        got = _CAPTURE.get("book_center", want)
        goal = (goal[0] + (want[0] - got[0]), goal[1] + (want[1] - got[1]))
    _STATE["toss_goal"] = goal
    _CAPTURE.pop("book_center", None)
    _far_grip(tt)
    _STATE["book_release"] = _CAPTURE.get("book_center", got)


def _far_grip(tt):
    _set_gesture_targets(tt)
    x, y, pose = dragon_pose(tt)
    rig = draw_dragon(_scratch(), x, y, SC, pose, L_DUSK, tt)
    return rig


def _solve_book_far():
    """The far hand must hold the open book's LEFT edge (the near hand holds its right edge):
    solve a body-space correction for the s6_book_far target with two Newton steps on the
    measured grip (a few scratch draws, once)."""
    tt = T_OPEN1 + 0.3
    _GX["book_far_fix"] = (0.0, 0.0, 0.0)
    rig = _far_grip(tt)
    nx, ny = rig.hand_near.x, rig.hand_near.y
    goal = (nx - 117.0 * SC, ny + 4.0 * SC)            # the left page's outer edge, a little below centre
    for _ in range(2):
        f0 = _far_grip(tt).hand_far
        fx0, fy0 = f0.x, f0.y
        fix = _GX["book_far_fix"]
        _GX["book_far_fix"] = (fix[0] + 10.0, fix[1], fix[2])
        f1 = _far_grip(tt).hand_far
        _GX["book_far_fix"] = (fix[0], fix[1] + 10.0, fix[2])
        f2 = _far_grip(tt).hand_far
        a11, a21 = (f1.x - fx0) / 10.0, (f1.y - fy0) / 10.0
        a12, a22 = (f2.x - fx0) / 10.0, (f2.y - fy0) / 10.0
        det = a11 * a22 - a12 * a21
        ex, ey = goal[0] - fx0, goal[1] - fy0
        if abs(det) < 1e-6:
            _GX["book_far_fix"] = fix
            break
        dx_ = (a22 * ex - a12 * ey) / det
        dy_ = (-a21 * ex + a11 * ey) / det
        _GX["book_far_fix"] = (fix[0] + dx_, fix[1] + dy_, fix[2])


def _solve_book_in_sack():
    """The correction (book-callback units) that puts the just-grabbed book's centre on the
    sack's book corner at T_GRAB (one scratch draw; it decays as he lifts the book out)."""
    _STATE["book_corr"] = (0.0, 0.0)
    tt = T_GRAB + 1e-3
    _CAPTURE.pop("closed_center", None)
    _far_grip(tt)
    if "closed_center" not in _CAPTURE or "book_frame" not in _CAPTURE:
        return
    cx0, cy0 = _CAPTURE["closed_center"]
    bx, by, ang = _bag_place(tt)
    ox, oy = BOOK_IN_SACK[0] * SC, BOOK_IN_SACK[1] * SC
    wx = bx + ox * math.cos(ang) - oy * math.sin(ang)
    wy = by + ox * math.sin(ang) + oy * math.cos(ang)
    m = cairo.Matrix(*_CAPTURE["book_frame"].as_tuple())
    m.invert()
    _STATE["book_corr"] = m.transform_distance(wx - cx0, wy - cy0)


def _solve_book_out():
    """The first frame on which the grabbed book is entirely clear of the sack (above its back
    rim or beside it): from then on his hand draws it (scratch draws over the lift, once)."""
    _STATE["t_book_out"] = 1e9                      # capture-only while solving
    out = T_HOLD
    f0 = int(math.ceil(T_GRAB * core.FPS))
    for f in range(f0, int(T_HOLD * core.FPS) + 1):
        tt = f / core.FPS
        _CAPTURE.pop("sack_book", None)
        _CAPTURE.pop("closed_quad", None)
        _far_grip(tt)
        if "sack_book" not in _CAPTURE:
            continue
        m, args = _CAPTURE["sack_book"]
        sc_cr = _scratch()
        sc_cr.set_matrix(m)
        _draw_book_in_hand(sc_cr, *args)
        quad = _CAPTURE.get("closed_quad")
        if not quad:                                 # it hangs straight now: no sack-pose any more
            out = tt
            break
        bx, by, ang = _bag_place(tt)
        ca, sa = math.cos(-ang), math.sin(-ang)
        loc = [(((qx - bx) * ca - (qy - by) * sa) / SC, ((qx - bx) * sa + (qy - by) * ca) / SC) for qx, qy in quad]
        if max(p[1] for p in loc) < -4.0 or max(p[0] for p in loc) < -34.0 or min(p[0] for p in loc) > 34.0:
            out = tt
            break
    _STATE["t_book_out"] = out


def _set_gesture_targets(t):
    """Per-frame targets for the custom gestures (body space of the dragon at t)."""
    x, y, _d = dragon_anchor(t)
    yaw = max(-1.45, min(1.45, -1.0 + 0.6 * dragon_turn(t)))
    _GX["yaw"] = yaw
    mx, my = _STATE.get("bag_mouth_world", (x + 60.0, y - 70.0))
    tgt = _world_to_body(mx, my - 26.0, x, y, yaw, 40.0)
    _GX["bag_mouth"] = tgt
    # the set-down: the wrist goes where the held book hangs just above its spot on the seat
    gx_, gy_ = _STATE.get("toss_goal", (x - 100.0, y - 120.0))
    _GX["toss"] = _world_to_body(gx_, gy_, x, y, yaw, 14.0)


# ----------------------------------------------------------------------------------------
# draw
# ----------------------------------------------------------------------------------------

SACK_EXPOSURE = 0.62             # the cream sack sits a stop under the faces (in his shadow, on the gravel)
SACK_BOTTOM = 87.0               # props: the sack's bottom hangs 87 below its grip


def _bag_place(t):
    """(x, y, angle) of the sack on the gravel (after T_BAG): it drops the last bit, wobbles as
    it lands and again as he pulls the book out."""
    x, y = _STATE["bag_rest"]
    dx, dy = _STATE["bag_drop"]
    u = core.clamp((t - T_BAG) / 0.12)
    yy = core.lerp(dy, y, core.in_quad(u))
    ang = 0.07 * B.wobble(t, T_BAG + 0.12, 3.0, 5.0) / 1.35
    ang += 0.05 * B.wobble(t, T_GRAB + 0.05, 3.5, 4.0) / 1.35
    return dx, yy, ang


def _draw_bag(cr, t, light):
    """The apothecary sack: in his hand until T_BAG, then standing on the gravel at his feet --
    open all along (as he carried it in S3 and S4; S7 and S8 draw it open). From T_GRAB the book
    is out of it; while it is still coming out (_book_out) the sack draws it, in his hand's frame."""
    if t < T_BAG:
        return
    light = light.with_(exposure=light.exposure * SACK_EXPOSURE)
    dx, yy, ang = _bag_place(t)
    # grounded: a contact shadow under its base on the gravel (it comes in as the sack touches
    # down), and a soft occlusion where its bottom meets the stones (drawn after it, below)
    k = core.ramp(t, T_BAG, T_BAG + 0.12)
    bot = (dx - math.sin(ang) * SACK_BOTTOM * SC, yy + math.cos(ang) * SACK_BOTTOM * SC)
    B.contact_shadow(cr, bot[0] + 3.0 * SC, bot[1] + 1.0, 42.0 * SC, 8.0 * SC, alpha=0.6 * k, color="#1b1530")
    if t >= T_GRAB and _CAN_EMPTY_BAG:
        inside = _CAPTURE.get("sack_book") if not _book_out(t) else None

        def contents(q):
            _bag_contents_no_book(q)
            if inside is not None:                   # the book on its way out, between the walls
                m, args = inside
                q.cr.save()
                q.cr.set_matrix(m)
                _draw_book_in_hand(q.cr, *args)
                q.cr.restore()
        orig = P._bag_contents
        P._bag_contents = contents
        try:
            P.draw_apothecary_bag(cr, dx, yy, SC, light, t, angle=ang, state="open")
        finally:
            P._bag_contents = orig
    else:
        P.draw_apothecary_bag(cr, dx, yy, SC, light, t, angle=ang, state="open")
    B.occlusion(cr, bot[0], bot[1] - 5.0 * SC, 40.0 * SC, 13.0 * SC, "#1b1530", alpha=0.42 * k)



def _draw_free_book(cr, t, light):
    """The book after the lob: flying, then lying on the seat between them."""
    if t < T_RELEASE:
        return
    if t < T_BOOKLAND:
        x, y, lay = _book_flight(t)
        cr.save()
        cr.translate(x, y)
        book_lay(cr, lay)
        P.draw_coloring_book(cr, 0.0, 0.0, SC, light, t, state="closed")
        cr.restore()
        return
    x, y = _STATE["book_rest"]
    dip = _STATE["garden"].seat_dip(U_BOOK, bench_sag(t), sag_u=U_DRAGON)
    y += dip
    bounce = 2.5 * _bump(t, T_BOOKLAND, 0.12)
    x += 3.0 * core.ramp(t, T_BOOKLAND, T_BOOKLAND + 0.15, "out_quad")
    # contact shadow on the slats under its front edge (it fades in as it lands)
    fx_, fy_ = _STATE["book_front"]
    k = core.ramp(t, T_BOOKLAND - 0.04, T_BOOKLAND + 0.1) * (1.0 - 0.5 * _bump(t, T_BOOKLAND, 0.12))
    B.contact_shadow(cr, x + 1.0, fy_ + dip - 1.5, 30.0 * SC, 4.5 * SC, alpha=0.42 * k)
    cr.save()
    cr.translate(x, y - bounce)
    cr.scale(1.0, FLAT_K)
    P.draw_coloring_book(cr, 0.0, 0.0, SC, light, t, angle=0.0, state="flat")
    cr.restore()



# ----------------------------------------------------------------------------------------
# the laugh: embers and the warmth that spreads from them
# ----------------------------------------------------------------------------------------

def _laugh_fire(cr, t, drig):
    """The laugh's puff: the library's embers plus a fuller fountain that drifts toward her
    (the first warm light that comes from him), gold in front of his teal scales."""
    ch.dragon_embers(cr, t, T_EMBERS, drig, n=34, life=2.0, intensity=1.0)
    ch.dragon_embers(cr, t, T_EMBERS + 0.5, drig, n=18, life=1.7, intensity=0.7)
    mx, my = drig.mouth
    for sgn, seed, t0 in ((-1.0, 41, 0.04), (1.0, 42, 0.04), (-1.0, 43, 0.62)):
        fx.embers(cr, t, mx - 10.0 * SC, my + 2.0 * SC, t0=T_EMBERS + t0, n=14, life=2.6, spread=80.0, rise=150.0,
                  color="#ff8a1e", hot="#ffe9a0", size=3.2, seed=seed, burst=0.45, scale=SC,
                  wind=-110.0 + sgn * 45.0, alpha=1.0, solid=True)


# the far end of the gravel walk, behind his end of the bench, runs up to the gap in the back
# hedge and stopped there in a squared-off cut: magnified in the close shots it read as a flat
# slab of masonry. This dressing (cached, world plane, over the garden's own walk) gives that far
# stretch the depth of field the hedges beside it already have, lets it fade into the hedge's
# dusk shade, and carries it on through the gap, narrowing into the haze toward the castle.
FAR_WALK_FADE = (800.0, 872.0)   # world y: the soft walk covers the sharp one above the first, gone below the second


def _far_walk_layer(kind):
    pal = env.palette(kind)
    base = core.mix(core.mix(pal["ground"], pal["stone"], 0.5), "#b4a282", 0.4)    # (env.draw_gravel_path's)
    shade = G._SHADOW_COL.get(kind, "#2a1f3e")

    def walk_shape(cr):
        sp = core.spline(G.PATH, 8)
        w0, w1 = G.PATH_W
        cr.new_path()
        core.tapered(cr, sp, w0, w1, profile=lambda s_: core.lerp(w0, w1, s_ ** 1.2), cap=False)

    def fn(cr):
        cr.push_group()
        env.draw_gravel_path(cr, G.PATH, G.PATH_W, kind, seed=6)
        # on through the gap: a narrowing strip of the same gravel, hazing into the far lawn
        x0, y0 = G.PATH[0]
        core.tapered(cr, [(x0, y0 + 3.0), (x0 - 4.0, y0 - 26.0), (x0 - 7.0, y0 - 58.0)], G.PATH_W[0] * 1.02, 16.0)
        cr.set_source(core.linear(0.0, y0 + 3.0, 0.0, y0 - 58.0, [core.alpha(env.haze_toward(base, pal["haze"], 0.35), 1.0),
                                                                  core.alpha(env.haze_toward(base, pal["haze"], 0.8), 0.0)]))
        cr.fill()
        # the far stretch lies in the hedge's dusk shade (darker the further it goes)
        cr.save()
        walk_shape(cr)
        cr.clip()
        cr.rectangle(1000.0, 700.0, 300.0, 200.0)
        cr.set_source(core.linear(0.0, y0, 0.0, FAR_WALK_FADE[1], [core.alpha(shade, 0.42), core.alpha(shade, 0.0)]))
        cr.fill()
        cr.restore()
        cr.pop_group_to_source()
        cr.mask(core.linear(0.0, FAR_WALK_FADE[0], 0.0, FAR_WALK_FADE[1], [(0.0, (0, 0, 0, 1.0)), (1.0, (0, 0, 0, 0.0))]))

    lay = env.layer(fn, blur=3.5)
    gr = G.GRADE[kind]
    G._grade_layer(lay, gr["ground"], gr["ground_v"])
    return lay


def _golden_bloom(cr, cam, t, g):
    """The warmth reaches the world: the garden's golden-hour paint blooms in over the dusk,
    through a soft circle that grows out from his mouth (from the first ember) across the frame
    and stays -- the dusk is warmed, not replaced (GOLD_NEAR near them, GOLD_FAR at the edges)."""
    s = spread(t)
    if s <= 0.0:
        return
    k = core.smooth(core.clamp((t - T_EMBERS) / 0.5))
    ox, oy = cam.to_screen(*_STATE["ember_origin"])
    R = core.lerp(160.0, 2700.0, s)
    a_c, a_f = GOLD_NEAR * k, GOLD_FAR * k
    pat = cairo.RadialGradient(ox, oy, 0.0, ox, oy, R)
    pat.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, a_c)
    pat.add_color_stop_rgba(0.42, 0.0, 0.0, 0.0, core.lerp(a_c, a_f, 0.35))
    pat.add_color_stop_rgba(0.78, 0.0, 0.0, 0.0, a_f)
    pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
    cr.push_group()
    g.paint_back(cr, cam, t, "golden")
    with cam.view(cr, 1.0):
        _STATE["far_walk"]["golden"].paint(cr)
    cr.pop_group_to_source()
    cr.mask(pat)
    cr.set_source_rgb(0.0, 0.0, 0.0)


def _warm_light(lc, t, drig):
    """Warmth enters the light (world units, inside the camera view of the light layer): the
    embers' own glow at his mouth, pulsing with the laugh; their light reaching HER face; a
    broad warm glow over the two of them that grows and stays; a warm pool on the bench."""
    if t < T_SNORT:
        return
    w = warmth(t)
    mx, my = drig.mouth
    fx_, fy_ = _STATE["gnome_face"]
    cx, cy = (mx + fx_) * 0.5, (my + fy_) * 0.5
    # the snort's spark, then the laugh's fire: a bright glow at his mouth on the laugh pulses
    burst = _win(t, T_SNORT, T_SNORT + 0.25, 0.05, 0.18) * 0.5
    burst = max(burst, _win(t, T_EMBERS - 0.03, LAUGH.end + 0.4, 0.08, 0.9))
    pulse = 0.75 + 0.25 * max([_pulse(t, p - 0.04, 0.05, 0.25) for p in LAUGH_PEAKS] + [0.0])
    if burst > 0.0:
        fx.glow(lc, mx - 8.0, my - 4.0, 120.0, "#ffb050", 0.45 * burst * pulse, core_r=22.0, core_alpha=0.35)
    if w > 0.0:
        # it reaches her: her face warms from his side
        fx.glow(lc, fx_ + 6.0, fy_ - 4.0, 95.0, "#ffbf72", 0.16 * w)
        # the warmth that stays: a broad soft light over both of them, and on the seat
        fx.glow(lc, cx, cy + 20.0, 420.0, "#ffb468", 0.09 * w)
        fx.light_pool(lc, cx + 10.0, BENCH.y - 100.0, 330.0, 74.0, "#ffb070", 0.06 * w)


_LUTS = {}


def _warm_grade(cr, t):
    """A gentle global warm curve that ramps in as the warmth spreads (mids gain a little red
    and gold and lose a little blue; black and white stay put, hues stay on-model).
    Quantised so the LUTs are cached."""
    k = round(core.clamp(0.3 * spread(t) + 0.7 * warmth(t)) * 20.0) / 20.0
    if k <= 0.0:
        return
    if k not in _LUTS:
        _LUTS[k] = fx.make_lut(r=lambda x, k=k: x + 0.04 * k * math.sin(math.pi * x),
                               g=lambda x, k=k: x + 0.012 * k * math.sin(math.pi * x),
                               b=lambda x, k=k: x - 0.028 * k * math.sin(math.pi * x))
    fx.grade_lut(cr, _LUTS[k])


def _air(cr, t, shot, drig):
    """Life in the air (world coordinates, action plane): pollen drifting in the last light,
    midges dancing round the unlit lantern (S7 lights it), and after the laugh golden motes
    that linger between them -- the warmth stays."""
    if shot in ("A", "B"):
        fx.dust(cr, t, (560.0, 560.0, 760.0, 330.0), n=16 if shot == "A" else 10, color="#ffe6c4", alpha=0.32,
                size=(0.8, 1.6), seed=17, drift=(5.0, -2.5), twinkle=0.7)
    else:
        # close shots: a few soft motes catch the last light (big and slow: near the lens)
        fx.dust(cr, t, (640.0, 600.0, 420.0, 240.0), n=9, color="#ffe2c0", alpha=0.26,
                size=(0.5, 0.9), seed=19, drift=(2.0, -1.2), twinkle=0.6)
    if shot == "A":
        lx, ly = G.LANTERN[0] - 50.0, G.LANTERN[1] - G.LANTERN_HEIGHT * G.LANTERN_SCALE + 40.0
        cr.save()
        for i in range(9):
            a = t * (2.1 + 0.7 * core.hash01(i, 5)) + i * 2.3
            r = 9.0 + 7.0 * core.hash01(i, 6)
            px = lx + math.cos(a) * r + 6.0 * core.noise1(t * 1.7 + i, 7)
            py = ly + math.sin(a * 1.3) * r * 0.55 + 5.0 * core.noise1(t * 1.9 + i, 8)
            core.src(cr, "#2b2436", 0.75)
            core.circle(cr, px, py, 0.9)
            cr.fill()
        cr.restore()
    if t > T_EMBERS + 0.6:
        k = core.ramp(t, T_EMBERS + 0.6, T_EMBERS + 2.0)
        gx, gy = _STATE["gnome_head"]
        mx, my = drig.mouth
        x0, x1 = min(gx, mx) - 30.0, max(gx, mx) + 10.0
        fx.dust(cr, t, (x0, my - 50.0, x1 - x0, gy - my + 110.0), n=16, color="#ffc46a", alpha=0.6 * k,
                size=(0.5, 1.0), seed=23, drift=(-2.5, -4.0), twinkle=0.8)


# ----------------------------------------------------------------------------------------
# draw
# ----------------------------------------------------------------------------------------

def draw(cr, t, st):
    g = st["g"]
    shot, cam = camera(t)
    L = light_at(t)
    Lg = light_for(t, "gnome")
    Ld = light_for(t, "dragon")
    _set_gesture_targets(t)
    gx, gy, gpose = gnome_pose(t)
    dx, dy, dpose = dragon_pose(t)
    sag = bench_sag(t)
    birds = st["troupe"].states(t)
    _STATE["gnome_head"] = (gx, gy - 150.0)
    _STATE["gnome_face"] = (gx + 8.0, gy - 146.0)

    # ---- the set (after the laugh the golden hour blooms in over the dusk, out from his mouth)
    g.paint_back(cr, cam, t, "dusk")
    with cam.view(cr, 1.0):
        _STATE["far_walk"]["dusk"].paint(cr)
    _golden_bloom(cr, cam, t, g)
    if shot in ("A", "B"):
        casters = [(gx, gy + 2.0, 40.0, 150.0), (dx, dy, 95.0, 330.0 if dpose.sit < 0.5 else 300.0)]
        if shot == "A":
            casters += [(x, y, 22.0, 30.0, 0.6) for (x, y, p, ump) in birds if not ump]
        g.shadow_pass(cr, cam, "dusk", casters)

    with cam.view(cr, 1.0):
        if shot in ("A", "B"):
            g.draw_lantern(cr, t, L, lit=0.0)
        Lb = bench_light(t)
        g.draw_bench(cr, t, Lb, part="back", sag=sag, sag_u=U_DRAGON)
        if t >= T_RELEASE:                     # falling / lying on the seat: behind his hand and knees
            # from his close-up on, the remedy drops out of the light (her long dusk shadow lies
            # across the seat): the cream cover must not out-shine their faces at the bottom of
            # the two-shot, where the captions run
            Lb_book = L if shot in ("A", "B", "C") else bench_light(t).with_(exposure=bench_light(t).exposure * BOOK_DIM)
            _draw_free_book(cr, t, Lb_book)
        for (x, y, p, ump) in birds:
            if ump:                                    # he rides the crest board as the bench rocks
                y += g.seat_dip(0.5, sag, sag_u=U_DRAGON, height=P.BENCH_SEAT_H + 117.0)
                ch.draw_pigeon(cr, x, y, SC, p, L, t)
        draw_gnome(cr, gx, gy, SC, gpose, Lg, t)
        drig = draw_dragon(cr, dx, dy, SC, dpose, Ld, t)
        if shot == "A":
            toss_crumbs(cr, t, T_CRUMBS, st["crumb_rel"], st["crumb_ground"], n=10, flock=st["troupe"])
        g.draw_bench(cr, t, Lb, part="front", sag=sag, sag_u=U_DRAGON)
        _draw_bag(cr, t, L)
        if shot == "A":
            for (x, y, p, ump) in sorted(birds, key=lambda b: b[1]):
                if not ump:
                    ch.draw_pigeon(cr, x, y, SC * (1.0 + 0.0015 * (y - PIGEON_Y[0])), p, L, t)
        # breath and fire
        if V_SIGH < t < V_SIGH + 3.2:
            # the sigh's curl of smoke: pale lavender-grey so it reads against the hedge, left
            # where he breathed it out (drifting toward her)
            sx, sy = _STATE["sigh_nose"]
            fx.smoke(cr, t, V_SIGH + 0.1, sx - 4.0, sy + 2.0, n=9, dur=2.3, rise=42.0, drift=(-62.0, 4.0), size=6.5,
                     color="#d4d0e2", alpha=0.6, seed=7, scale=SC)
        if T_SNORT <= t < T_SNORT + 1.3:
            # the snort: a puff blown out of his nostrils (toward her) with the first few sparks in it
            nx_, ny_ = drig.nose
            fx.smoke(cr, t, T_SNORT, nx_ - 4.0, ny_ + 1.0, n=5, dur=0.95, rise=14.0, drift=(-34.0, 3.0), size=3.6,
                     color="#d8cfc8", alpha=0.5, seed=12, scale=SC, spread=0.25)
            fx.embers(cr, t, nx_ - 3.0, ny_, t0=T_SNORT, n=8, life=0.8, spread=22.0, rise=46.0,
                      color="#ff9a30", hot="#ffe9a0", size=2.1, seed=9, burst=0.05, scale=SC, wind=-60.0, solid=True)
        if t >= T_EMBERS:
            _laugh_fire(cr, t, drig)
        _air(cr, t, shot, drig)

    if shot == "B":
        st["gallery"].draw(cr, t, cam, L_DUSK.with_(exposure=0.86, rim_strength=0.85), g)
    g.paint_fg(cr, cam, t, "dusk", alpha=1.0 if shot == "A" else 0.0)

    # ---- the warm grade (after the laugh)
    _warm_grade(cr, t)

    # ---- light
    lc = st["light"].begin()
    g.light(lc, cam, t, "dusk")
    with cam.view(lc, 1.0):
        # a soft last-light key on the bench: the subject is the brightest area of the frame
        fx.glow(lc, BENCH.x + 40.0, BENCH.y - 160.0, 520.0, "#ffd8b8", 0.08)
        _warm_light(lc, t, drig)
    w = warmth(t)
    pk = dict(G.POST["dusk"])
    pk["bloom_strength"] = pk["bloom_strength"] + 0.14 * w
    pk["vignette_color"] = core.lerp_tuple(pk["vignette_color"], (0.08, 0.04, 0.02), w)
    fx.post(cr, t, light=st["light"], **pk)
