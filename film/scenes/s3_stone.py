"""s3_stone.py -- Scene 3: THE SPEAKING STONE.   Emotion: lonely, drifting.

THE IDEA. He calls the one number left -- and the city answers with a menu. Loneliness is just
another option between billing and new accounts, and the answer to it is "please hold": four
tinny notes, over and over. He walks home through the rain lit by the cold stone at his ear,
past warm lamps that light the street but not him, and stops in a pool of lamplight that
surrounds him without reaching him: a cold figure in a warm pool, still on hold. (The image
rhymes with S8, where one warm lamp shelters a whole crowded bench.)

ONE SHOT, three movements (times from timeline.json; the numbers are the current timeline's):
 A  0 - s3_hold (10.0)  SIDE-ON TRACKING SHOT, medium-wide, eye line at his shoulder (y 560).
    The camera trucks right with him at walking pace (he holds at screen x ~620, look room
    ahead); the world slides past in depth: sky 0.05, castle hill 0.12, the town behind 0.3,
    the far side of the street 0.5, four strips of wet cobbles 0.56 / 0.74 / 1.0 (his plane:
    no foot slides) / 1.35, the near side's eave and a rain barrel 1.8 (out of focus).
    Opening frame: he has just walked out of a lamp's pool (warm on his scarf and horns) into
    the cold; a downspout pours into a barrel in the soft foreground; far ahead, at the right
    edge, the lamp he will end under. As each PHONE line plays, a spark leaves the stone and
    the words are WRITTEN in light, word by word (syllable-timed to the voice's envelope):
    illuminated uncial script, glowing cold cyan, an enlarged initial F on every line (the
    machine's monotony), a dark halo behind each letter so it reads over anything. The menu
    stacks up beside his face like a page; older lines cool and dim.
      s3_l1 "For billing, press one."  s3_l2 "For a new account, press two."
      s3_l3 "For loneliness... please hold." -- "loneliness" lands with a beat: it burns
      brighter, pops (a damped scale pulse) and throws a cold flash; the ellipsis writes
      itself one dot at a time through the voice's pause; then "please hold."
    Each finished line gets a scribe's line-filler (a thin swash ending in the stone's spiral),
    and the glowing words throw cold streaks down the wet cobbles beside the lamps' gold ones.
    Acting: L1/L2 he has heard it all before (heavy lids, eyes ahead and down, tail dragging,
    wings drooped, the open apothecary sack swinging from his far hand); between the options a
    weary glance up into the rain (2.6), a heavy blink after "press two" (5.4) and a shiver in
    the cold (5.9: shoulders up, head trembles, wet-wool rustle). At "loneliness" his eyes lift
    to the word, his brows rise, his head turns a touch toward the stone and his walk falters
    half a step (hope). "please hold": a slow blink, the brows sink, the head drops, the hunch
    deepens (it was not for him after all).
 B  s3_dissolve (9.3) - stop (13.25)  The menu breaks into motes that stream into a scrap of
    four-line staff between repeat signs: four mensural notes that light up EXACTLY as the
    music box plays them (onsets from film/audio/motif.py: B A F# E, e e e q., 1.5 s loop),
    and a small hourglass marked "On hold" that runs out every two loops and flips over as
    the loop comes round again. The loop floats beside his face and follows him. He slows
    (strides shorten and slow down; the walk is integrated from his speed so the feet never
    skate) and passes under the lamp -- its light runs gold along his horns, head and shoulders
    -- and stops a stride past the post, the trailing foot setting down beside the planted one;
    the camera eases to rest a beat after him. The lamp now hangs above and BEHIND him: its
    cone of lit rain and its pool of gold on the stones surround him; on him only a warm edge of
    top-light (and a faint bounce off the wet pool) -- the front of him stays cold, lit cyan by
    the stone. Rain bursts on his horns and shoulders; a drop gathers on his snout and falls.
 C  stop - end  thought -> glance -> breath -> line, then the pull-back.
    Thought (13.35): eyes drop to the wet stones. Glance (13.75): up to the hourglass. Breath
    (13.96): the hunch eases, the chest lifts. s3_l4 MAN (14.3) "I've been on hold my whole
    life." -- small and tired, to himself: on "on hold" his eyes are on the hourglass, on "my
    whole life" they slide down and away; his body has turned a little toward us (3/4) so the
    face reads; a slow push-in (zoom 1.0 -> 1.12) holds on him. After the line (16.4): a long
    exhale -- shoulders sink, a breath of steam curls from his nostrils in the cold.
    s3_lantern (17.0 - 20.0): the camera pulls back and rises (1.12 -> 0.78) into the dark
    under the near side's eaves: the eave and a doorway post close in at the top and right,
    drips falling off them, and the street sinks into the night round the lamp (its cone, its
    pool, him and the loop keep their light) -- we leave him as we found him, watched from the
    dark: small, cold, in the warm pool, the stone still at his ear, the four notes looping.

COLOUR / VALUE PLAN. Deep navy night and rain (the far side 12-30 % value, sunk in a night
falloff and a rain haze) against sodium-gold lamp light (halos, volumetric cones of lit rain,
pools on the cobbles with warm specular glints, long broken reflections on the wet street),
a few warm windows and door lamps across the street (chosen so none ever passes behind the
text), and one cold accent: the speaking stone's cyan (its glow at his ear, its light on his
face, the rune text, the notes, the hourglass). Warm light is the world's, never his: it rims
him, it does not reach his front. Vignette deepens as the camera pulls back.

THE PERIOD WORLD. Half-timbered houses with jettied upper storeys, shuttered shop fronts,
leaded diamond-pane windows, arched plank doors, iron wall lamps, painted hanging signs (a
baker's loaf among them, shut for the night), a castle on the hill and a church spire beyond
the roofs (they show above the eaves as the camera pulls back), cobbles, a rain barrel under a
wooden downspout, iron lantern posts with candle flames. The "phone" is a slate rune-stone; its
menu is illuminated script; the timer is an hourglass; the hold music is a music box's tune
written as medieval notes.

CRAFT. Cached layers (sky, castle, roofs, the far side drawn twice so lit windows can be
chosen, the whole street painted once and cut into parallax strips, reflections, lamp-pool
glints, out-of-focus foreground); per frame: lamp posts, the dragon -- drawn ONCE into an
offscreen buffer that is composited, mirrored (1/3 res) for his reflection in the wet stones,
and used as the mask for the lamp's top-light and the pool's bounce (Klaus-style light that
touches the character) -- his contact and cast shadows, rain in three world-locked depths that
turns gold inside each lamp's halo and cone, splashes (a real one when he steps in the puddle),
puddle ripples, mist, the rune text and the hold loop, a background light layer composited
BEHIND him (so he reads dark against the lamp light) and a front light layer (the stone's cold
spill, the text's reflections), bloom, grain, vignette. SFX_CUES are computed from the same
walk integrator, word schedule, beat constants and hourglass clock the picture uses.
"""

import math
import re

import cairocffi as cairo
import numpy as np

from film.lib import core, env, fx, timeline as tl
from film.lib import props as P
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.core import clamp, lerp, ramp, smooth

SCENE = 3
TAU = math.tau
W, H = core.W, core.H

# =============================================================================================
# timing: everything from timeline.json; the scene's own beats are derived from it
# =============================================================================================
DUR = tl.scene(SCENE).duration
L1, L2, L3, L4 = (tl.line(f"s3_l{k}") for k in (1, 2, 3, 4))
PHONE_LINES = (L1, L2, L3)
T_HOLD = tl.beat("s3_hold").t
T_LANTERN = tl.beat("s3_lantern").t if tl.has_beat("s3_lantern") else DUR - 3.0


def _hold_music():
    """The music box's notes [(t, dur, midi)], its loop length and its four pitches -- from the
    film's shared motif module, so the glowing notes pulse exactly with what we hear."""
    try:
        from film.audio import motif as M
        ev = M.hold_music_events(DUR - T_HOLD, t0=T_HOLD)
        loop = sum(M.MOTIF_RHYTHM) * M.eighth_seconds(M.HOLD_TEMPO)
        notes = tuple(M.MUSIC_BOX_MOTIF)
        if ev:
            return [tuple(e) for e in ev], float(loop), notes
    except Exception:                                   # the audio package is missing
        pass
    e, notes, rhythm = 0.25, (83, 81, 78, 76), (1, 1, 1, 3)
    ev, t = [], T_HOLD
    while t < DUR:
        for m, r in zip(notes, rhythm):
            if t < DUR:
                ev.append((t, r * e, m))
            t += r * e
    return ev, e * sum(rhythm), notes


HOLD_EV, LOOP, NOTES = _hold_music()
NOTE_IDX = {m: k for k, m in enumerate(NOTES)}
HG_PERIOD = 2.0 * LOOP          # the hourglass runs out every two loops ...
HG_FLIP = 0.55                  # ... and flips, landing as the loop starts again


# ---------------------------------------------------------------------------------------------
# word timing for the rune text: phrases -> voiced stretches of the line's envelope; words ->
# syllable shares of each stretch's energy
# ---------------------------------------------------------------------------------------------
_SYL = {"for": 1, "billing": 2, "press": 1, "one": 1, "a": 1, "new": 1, "account": 2, "two": 1,
        "loneliness": 3, "please": 1, "hold": 1}


def _syllables(word):
    w = re.sub(r"[^a-z']", "", word.lower())
    if w in _SYL:
        return _SYL[w]
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


def _voiced(env_, thr=0.08, bridge=3):
    """Runs of envelope frames above thr, merging gaps of <= bridge frames (stop consonants)."""
    runs, i, n = [], 0, len(env_)
    while i < n:
        if env_[i] > thr:
            j = i
            while j < n and env_[j] > thr:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= bridge:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return merged


def word_schedule(line):
    """[(word, t_on, t_off)] in local scene time. Each phrase (split after , . ...) is matched to
    a voiced stretch of the envelope (the longest silences are the phrase breaks); inside a
    stretch a word starts where the cumulative energy reaches its share of the syllables."""
    words = line.text.split()
    if not words:
        return []
    fps = tl.fps()
    env_ = list(line.env) or [1.0] * max(2, int(line.duration * fps))
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if w[-1] in ",.?!;:…":
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    segs = _voiced(env_) or [[0, len(env_)]]
    while len(segs) > len(phrases):                 # close the shortest silence
        gi = min(range(len(segs) - 1), key=lambda k: segs[k + 1][0] - segs[k][1])
        segs[gi][1] = segs[gi + 1][1]
        del segs[gi + 1]
    if len(segs) < len(phrases):                    # not enough breaks: one stretch for all
        phrases = [words]
        segs = [[segs[0][0], segs[-1][1]]]
    out = []
    for ph, (a, b) in zip(phrases, segs):
        e = [max(0.0, v) for v in env_[a:b]] or [1.0]
        cum = np.concatenate([[0.0], np.cumsum(e)])
        tot = cum[-1] or 1.0
        syl = [_syllables(w) for w in ph]
        s_tot = float(sum(syl))
        acc = 0.0
        for w, s in zip(ph, syl):
            k0 = float(np.interp(acc / s_tot * tot, cum, np.arange(len(cum))))
            acc += s
            k1 = float(np.interp(acc / s_tot * tot, cum, np.arange(len(cum))))
            out.append((w, line.start + (a + k0) / fps, line.start + (a + k1) / fps))
    return out


WORDS = {ln.id: word_schedule(ln) for ln in PHONE_LINES}


def _word_t(line, stem, end=False):
    for w, a, b in WORDS[line.id]:
        if w.lower().startswith(stem):
            return b if end else a
    return line.end if end else line.start


T_LONELY = _word_t(L3, "lonel")                  # the word that lands with a beat ...
T_LONELY_LAND = T_LONELY + clamp((_word_t(L3, "lonel", end=True) - T_LONELY) * 0.85, 0.1, 0.32)  # ... here
T_PLEASE = _word_t(L3, "please")
T_DISSOLVE0 = max(L3.end + 0.55, T_HOLD - 0.7)   # the menu dissolves into the hold loop
T_DISSOLVE1 = T_HOLD + 0.02

# =============================================================================================
# the walk: he drifts along the street, slows when the music box starts, stops under the lamp
# =============================================================================================
SC = 0.85                       # the dragon and everything in his depth plane (posts, puddles)
GY = 905.0                      # his ground line (world == screen at the opening frame)
X0 = 600.0                      # his world x at t = 0
STEP_T = 0.62                   # seconds per step: a tired walk
TURN_WALK, TURN_TALK = 0.40, 0.06
V0 = ch.dragon_stride(SC, 1, TURN_WALK) / (2.0 * STEP_T)
T_SLOW0 = T_HOLD + 0.2                          # the music box starts ... he slows ...
T_STOP = min(T_HOLD + 3.25, L4.start - 1.05)     # ... and stops under the lantern
T_LOOKDOWN = T_STOP + 0.1                       # thought: the eyes drop to the wet stones
T_GLANCE = L4.start - 0.55                      # glance: up at the hourglass
T_BREATH = L4.start - 0.34                      # breath
T_SIGH = L4.end + 0.15                          # the long exhale after the line (+ steam)
T_RAINLOOK = L1.end + 0.25                      # between the options: a weary glance up into the rain
T_SHIVER = 0.5 * (L2.end + L3.start) - 0.1       # ... and a shiver in the cold


def _turn(t):
    return lerp(TURN_WALK, TURN_TALK, ramp(t, T_STOP - 0.35, L4.start - 0.1, "inout_sine"))


def _slow_u(t):
    return clamp((t - T_SLOW0) / (T_STOP - T_SLOW0))


def _speed_k(t):
    k = 1.0 - 0.15 * core.window(t, T_LONELY - 0.15, T_PLEASE + 0.45, 0.45, 0.7)   # the falter
    return k * (1.0 - core.inout_sine(_slow_u(t)))


def _walk_k(t):
    return (1.0 - core.inout_sine(_slow_u(t))) ** 0.55


def _integrate():
    dt = 1.0 / 480.0
    ts = np.arange(-2.0, DUR + 1.5, dt)
    spd = np.array([V0 * _speed_k(t) for t in ts])
    wk = np.array([_walk_k(t) for t in ts])
    stride = np.array([ch.dragon_stride(SC, 1, _turn(t)) for t in ts])
    dph = spd / (stride * np.maximum(wk, 0.12))
    x = np.concatenate([[0.0], np.cumsum(0.5 * (spd[1:] + spd[:-1]) * dt)])
    ph = np.concatenate([[0.0], np.cumsum(0.5 * (dph[1:] + dph[:-1]) * dt)])
    x += X0 - float(np.interp(0.0, ts, x))
    # land the stop at mid-stance (phase .25 / .75): the trailing foot sets down beside the other
    ph += (0.25 - float(np.interp(T_STOP, ts, ph))) % 0.5
    return ts, x, ph, wk


_TS, _XS, _PHS, _WKS = _integrate()


def walk_x(t):
    return float(np.interp(t, _TS, _XS))


def walk_phase(t):
    return float(np.interp(t, _TS, _PHS)) % 1.0


def walk_amt(t):
    return float(np.interp(t, _TS, _WKS))


X_STOP = walk_x(T_STOP)


def _plants():
    """Heel strikes (t, foot) whenever the phase crosses a half cycle while he walks."""
    out = []
    k = int(math.floor(_PHS[0] * 2.0)) + 1
    for i in range(1, len(_TS)):
        while _PHS[i] * 2.0 >= k:
            if _WKS[i] > 0.3 and 0.0 <= _TS[i] < DUR:
                out.append((float(_TS[i]), k % 2))
            k += 1
    return out


PLANTS = _plants()

# =============================================================================================
# the camera: a slow side-on tracking shot; it eases to rest as he stops, pushes in a touch for
# his line, then pulls back and up to leave him small in the lamp's pool of light
# =============================================================================================
CAM_LAG = 0.3
SCREEN_X_WALK = 620.0
OFFX = (W / 2 - SCREEN_X_WALK) + V0 * CAM_LAG
HEAD_DX, HEAD_DY = 26.0, -373.0      # his head centre relative to his anchor (scale 0.85, hunched)
T_CAM0 = T_STOP + CAM_LAG
T_PUSH1 = L4.end - 0.05
T_PULL0 = max(L4.end + 0.25, T_LANTERN - 0.4)     # s3_lantern: the pull-back to the final image
T_PULL1 = DUR - 0.3
ZOOM_LINE, ZOOM_WIDE = 1.12, 0.78


def _cam_put(wx, wy, sx, sy, zoom):
    """The camera that shows world point (wx, wy) at screen (sx, sy) with this zoom."""
    return core.Camera(wx - (sx - W / 2) / zoom, wy - (sy - H / 2) / zoom, zoom)


def _cam_follow(t):
    return core.Camera(walk_x(t - CAM_LAG) + OFFX, H / 2, 1.0)


K_STOP = _cam_follow(T_CAM0)
K_LINE = _cam_put(X_STOP + HEAD_DX, GY + HEAD_DY, 650.0, 505.0, ZOOM_LINE)
K_WIDE = _cam_put(X_STOP, GY, 790.0, 862.0, ZOOM_WIDE)


def camera_base(t):
    if t <= T_CAM0:
        return _cam_follow(t)
    if t <= T_PUSH1:
        return core.Camera.lerp(K_STOP, K_LINE, core.inout_sine(ramp(t, T_CAM0, T_PUSH1)))
    if t <= T_PULL0:
        return K_LINE
    return core.Camera.lerp(K_LINE, K_WIDE, core.inout_sine(ramp(t, T_PULL0, T_PULL1)))


def camera(t):
    return camera_base(t).drift(t, amp=2.2, freq=0.11, seed=3)


# ---------------------------------------------------------------------------------------------
# depth planes. The camera's eye line (horizon) is y = 560; a ground point at screen y has
# parallax (y - 560) / (905 - 560), so his feet (905) are 1.0 and the houses' feet (732) 0.5.
# ---------------------------------------------------------------------------------------------
PX_SKY, PX_CASTLE, PX_ROOFS, PX_HOUSES = 0.05, 0.12, 0.3, 0.5
PX_A1, PX_A2, PX_B, PX_C = 0.56, 0.74, 1.0, 1.35
PX_NEAR = 1.5
HOUSE_Y = 732.0                       # where the houses across the street meet it
HOUSE_SC = SC * PX_HOUSES             # one scale per depth plane


def _cobble_size(y):
    return 4.0 + 42.0 * clamp((y - HOUSE_Y) / (1200.0 - HOUSE_Y)) ** 1.25


def _extent(p, margin=140.0):
    """World rect (x, y, w, h) that the camera ever shows at parallax p (+ margin)."""
    xs, ys = [], []
    for k in range(0, int(DUR * 10) + 1):
        cam = camera_base(k / 10.0)
        for sx, sy in ((0, 0), (W, 0), (0, H), (W, H)):
            x, y = cam.to_world(sx, sy, p)
            xs.append(x)
            ys.append(y)
    x0, x1 = min(xs) - margin, max(xs) + margin
    y0, y1 = min(ys) - margin, max(ys) + margin
    return (x0, y0, x1 - x0, y1 - y0)


# the street's lantern posts (his depth plane): the one he walks out of at the start, and the
# one he stops under -- the warm light he has been walking toward all along. They stand just
# upstage of his path, the lantern on its crook arm hanging over the street; he stops a stride
# past the post, so the lamp is above and BEHIND him (it rims him; the post stays clear of him)
POST_SC = 1.0
POST_H = 740.0
POST_Y = GY - 6.0
POST_ARM = 58.0 * POST_SC                 # the crook arm's reach (props.draw_lantern_post)
POSTS = [(walk_x(-0.35) - POST_ARM, POST_Y, 0), (X_STOP - 112.0, POST_Y, 1)]

# =============================================================================================
# lights on him
# =============================================================================================
L_BASE = ch.LIGHTS["street_night"]
L_COLD = L_BASE.with_(key=(0.62, 0.72, 0.95), ambient=(0.2, 0.26, 0.47), rim=(0.55, 0.82, 1.0),
                      rim_strength=0.55, direction=(0.3, -0.95), rim_direction=(-0.8, -0.6),
                      bounce=(0.3, 0.42, 0.75), bounce_strength=0.16, name="s3_cold")
L_LAMP = L_BASE.with_(key=(1.06, 0.80, 0.56), ambient=(0.24, 0.29, 0.5), rim=(1.0, 0.66, 0.3),
                      rim_strength=0.85, direction=(-0.45, -0.89), rim_direction=(-0.6, -0.8),
                      bounce=(0.4, 0.4, 0.6), bounce_strength=0.16, name="s3_lamp")
# under the last lamp: lit from above and behind -- warm only along his top edges; the cold
# night (and the stone's cyan) on all the camera sees: a cold figure in a warm pool
L_POOL = L_COLD.with_(rim=(1.0, 0.64, 0.28), rim_strength=0.95, rim_direction=(-0.25, -0.97),
                      key=(0.7, 0.74, 0.9), name="s3_pool")
L_SET = L_BASE.with_(name="s3_set")


def dragon_light(x):
    """His light: the first lamp warms him as he walks out of its pool, the street is cold, the
    last lamp only rims him."""
    a = POSTS[0][0] + POST_ARM
    u_a = clamp(1.0 - abs(x - a) / 300.0) ** 1.3
    lt = L_COLD if u_a <= 0 else B.Light.lerp(L_COLD, L_LAMP, u_a)
    u_c = smooth(clamp((x - (X_STOP - 300.0)) / 300.0))
    if u_c > 0:
        lt = B.Light.lerp(lt, L_POOL, u_c)
    return lt


# =============================================================================================
# the rune text's box on screen (kept clear of every bright thing behind it)
# =============================================================================================
FONT = P.FONTS.sign                # Uncial Antiqua: insular uncial, the Book of Kells' hand
FS = 46.0                          # letter size
LH = 64.0                          # line spacing
TEXT_DX, TEXT_Y0 = 172.0, 366.0    # first baseline; the third line sits just above his eyes
TEXT_BOX = (SCREEN_X_WALK + TEXT_DX - 60.0, TEXT_Y0 - 70.0, 900.0, 3 * LH + 60.0)
TEXT_T = (L1.start - 0.4, T_DISSOLVE1 + 0.3)

# =============================================================================================
# set painting (static: cached in setup)
# =============================================================================================
KIND = "rain_night"
PAL = env.palette(KIND)
NIGHT = "#04070f"


def _draw_sky(cr, rect):
    x, y, w, h = rect
    env.draw_sky(cr, x, y, w, h, kind=KIND, horizon=620.0, seed=5)
    env.draw_haze(cr, x, y, w, h, NIGHT, 0.35, 0.0)


def _draw_castle(cr, rect, cx):
    x, y, w, h = rect
    env.draw_hills(cr, x, w, 520.0, kind=KIND, layers=2, height=(30.0, 80.0), seed=8, trees=True,
                   fields=False, bottom=y + h)
    env.draw_castle_hill(cr, cx, 420.0, 0.34, kind=KIND, hill_w=620, hill_h=90, seed=2, windows=7)
    env.draw_haze(cr, x, 250.0, w, y + h - 250.0, PAL["haze"], 0.0, 0.5)


def _draw_roofs(cr, rect):
    x, y, w, h = rect
    env.draw_roofline(cr, x, x + w, 600.0, 0.24, KIND, seed=4, lit=0.2, haze=0.3)
    env.draw_haze(cr, x, 150.0, w, y + h - 150.0, PAL["haze"], 0.1, 0.45)


def _houses_rows(cr, rect, lit):
    x, y, w, h = rect
    return env.draw_street_row(cr, x - 60.0, x + w + 60.0, HOUSE_Y, HOUSE_SC, KIND, seed=23, lit=lit,
                               floors=(1, 3), widths=(480.0, 760.0), alley=0.3)


def _window_path(cr, cx, cy, w, h, arched):
    if arched:
        cr.move_to(cx - w / 2, cy + h / 2)
        cr.line_to(cx - w / 2, cy - h / 2 + w / 2)
        cr.arc(cx, cy - h / 2 + w / 2, w / 2, math.pi, TAU)
        cr.line_to(cx + w / 2, cy + h / 2)
        cr.close_path()
    else:
        cr.rectangle(cx - w / 2, cy - h / 2, w, h)


def _text_sweep(px):
    """Does a point of the houses' plane pass behind the rune text while it is up?"""
    bx, by, bw, bh = TEXT_BOX
    for k in range(int(TEXT_T[0] * 10), int(TEXT_T[1] * 10) + 1):
        sx, sy = camera_base(k / 10.0).to_screen(px[0], px[1], PX_HOUSES)
        if bx - 40 <= sx <= bx + bw + 40 and by - 40 <= sy <= by + bh + 40:
            return True
    return False


def _draw_houses(cr, rect, out):
    """The far side of the street, built twice (dark / every window lit) so the lit windows can
    be chosen: none may ever pass behind the floating text."""
    x, y, w, h = rect
    rigs = _houses_rows(cr, rect, 0.0)
    lit_s = core.new_surface(int(math.ceil(w)), int(math.ceil(h)))
    lc = core.new_context(lit_s)
    lc.translate(-x, -y)
    _houses_rows(lc, rect, 1.0)
    lit_s.flush()
    chosen = []
    for hi, r in enumerate(rigs):
        for wi, ((wx, wy), ww, wh, _l) in enumerate(r.windows):
            if _text_sweep((wx, wy)):
                continue
            ground_floor = wy > HOUSE_Y - 600.0 * HOUSE_SC
            attic = wy < HOUSE_Y - 1000.0 * HOUSE_SC
            if core.hash01(hi * 17 + wi, 71) < (0.42 if ground_floor else 0.45 if attic else 0.28):
                chosen.append((wx, wy, ww, wh, ground_floor or wh < ww * 1.25))
    _dress_houses(cr, rigs, glass=False)
    # the far side's pavement: wet flagstones at the houses' feet
    cr.rectangle(x, HOUSE_Y - 3.0, w, 10.0)
    core.src(cr, core.shade(PAL["stone"], 0.35))
    cr.fill()
    cr.rectangle(x, HOUSE_Y - 3.0, w, 2.0)
    core.src(cr, core.tint(PAL["haze"], 0.15), 0.3)
    cr.fill()
    # night: the facades sink into the dark, deepest up high (the lamps relight them)
    cr.save()
    cr.rectangle(x, y, w, HOUSE_Y - y + 8.0)
    cr.clip()
    cr.set_source(core.linear(0, HOUSE_Y - 900.0 * HOUSE_SC, 0, HOUSE_Y,
                              [core.alpha(NIGHT, 0.62), core.alpha(NIGHT, 0.46), core.alpha(NIGHT, 0.3)]))
    cr.paint()
    cr.restore()
    for (wx, wy, ww, wh, arched) in chosen:                  # the chosen panes: candlelight
        cr.save()
        _window_path(cr, wx, wy, ww + 1.0, wh + 1.0, arched)
        cr.clip()
        cr.set_source_surface(lit_s, x, y)
        cr.paint_with_alpha(0.85)
        cr.restore()
    env.draw_haze(cr, x, y, w, HOUSE_Y - y + 10.0, PAL["haze"], 0.12, 0.05)
    out["lamps"] = _dress_houses(cr, rigs, glass=True)
    out["rigs"] = rigs
    out["windows"] = [(wx, wy, ww, wh) for (wx, wy, ww, wh, _a) in chosen]


def _wall_lantern(cr, x, y, s, side=1, glass=True):
    """A small iron lantern hanging from a wall bracket beside a door (the far side's door
    lamps): the iron first (night-darkened with the facade), the lit glass after (glass=True)."""
    lx = x + side * 30.0 * s
    if not glass:
        il = core.shade(P.PROP_COLORS["iron"], 0.1)
        core.src(cr, il)
        core.tapered(cr, [(x, y - 40 * s), (x + side * 18 * s, y - 42 * s), (x + side * 32 * s, y - 38 * s)],
                     5.0 * s, 4.0 * s)
        cr.fill()
        core.tapered(cr, [(x, y - 18 * s), (x + side * 12 * s, y - 30 * s), (x + side * 20 * s, y - 40 * s)],
                     3.5 * s, 2.5 * s)
        cr.fill()
        core.polygon(cr, [(lx - 14 * s, y - 24 * s), (lx, y - 36 * s), (lx + 14 * s, y - 24 * s)])
        cr.fill()
        core.polygon(cr, [(lx - 11 * s, y + 14 * s), (lx + 11 * s, y + 14 * s), (lx, y + 22 * s)])
        cr.fill()
        return (lx, y - 5 * s)
    core.polygon(cr, [(lx - 11 * s, y - 24 * s), (lx + 11 * s, y - 24 * s), (lx + 9 * s, y + 14 * s), (lx - 9 * s, y + 14 * s)])
    cr.set_source(core.linear(0, y - 24 * s, 0, y + 14 * s, ["#ffe7a8", "#ffbe5c", "#e08a34"]))
    cr.fill()
    core.src(cr, core.shade(P.PROP_COLORS["iron"], 0.1))
    for dx in (-11.0, 0.0, 11.0):
        cr.rectangle(lx + dx * s - 1.2 * s, y - 24 * s, 2.4 * s, 38 * s)
    cr.fill()
    fx.glow(cr, lx, y - 6 * s, 16 * s, "#fff4d8", 0.8)
    return (lx, y - 5 * s)


def _dress_houses(cr, rigs, glass=False):
    """Storybook dressing on the far side: door lamps (never behind the text) and a few painted
    shop signs -- among them a baker's loaf, shuttered for the night. Call it twice: before the
    night falls on the facades (iron, boards) and after it (the lamps' lit glass)."""
    s = HOUSE_SC
    lamps = []
    for i, r in enumerate(rigs):
        dx, dy, dw, dh = r.door
        side = 1 if core.hash01(i, 81) < 0.5 else -1
        lx = dx + dw + 18.0 * s if side > 0 else dx - 18.0 * s
        ly = dy + 70.0 * s
        if core.hash01(i, 82) < 0.55 and not _text_sweep((lx + side * 30.0 * s, ly)):
            lamps.append(_wall_lantern(cr, lx, ly, s, side, glass))
    if glass:
        return lamps
    signs = [("BAKER", "#7a4e26", "#f2dfb4", "loaf"), ("CHANDLER", "#3e4a5e", "#e8dcc0", None),
             ("COBBLER", "#5e3a3a", "#ecdcc8", None)]
    k = 0
    for i, r in enumerate(rigs):
        if k >= len(signs) or core.hash01(i, 83) > 0.5:
            continue
        rx, ry, rw, rh = r.rect
        bx, by = rx + rw * 0.18, HOUSE_Y - 600.0 * HOUSE_SC + 18.0
        text, paint, ink, em = signs[k]
        rig = P.draw_hanging_sign(cr, bx, by, kind="washhouse", scale=HOUSE_SC * 0.9, light=L_SET, t=0.0, side=1,
                                  text=(text,), emblem="none", paint=paint, ink=ink, swing=0.0, seed=i)
        if em == "loaf":
            P.draw_bread(cr, rig.emblem[0], rig.emblem[1], 30.0 * HOUSE_SC, L_SET, 0.0, state="loaf")
        k += 1
    return lamps


GROUND_Y0, GROUND_Y1 = HOUSE_Y + 2.0, 1268.0
_GROUND = {}


def _ground():
    """The whole wet street, painted ONCE (continuous rows, one Fresnel sheen toward the far
    kerb), then cut into horizontal strips that slide at their own parallax."""
    if "surf" not in _GROUND:
        rects = [_extent(p) for p in (PX_A1, PX_A2, PX_B, PX_C)]
        x0 = min(r[0] for r in rects)
        x1 = max(r[0] + r[2] for r in rects)
        w, h = x1 - x0, GROUND_Y1 - GROUND_Y0
        surf = core.new_surface(int(math.ceil(w)), int(math.ceil(h)))
        cr = core.new_context(surf)
        cr.translate(-x0, -GROUND_Y0)
        env.draw_cobbles(cr, x0, GROUND_Y0, w, GROUND_Y1, KIND, seed=31, wet=True, size=(4.0, 50.0), contrast=1.1)
        # night: the street darkens toward us (the lamps relight it)
        cr.rectangle(x0, GROUND_Y0, w, h)
        cr.set_source(core.linear(0, HOUSE_Y, 0, 1150.0, [core.alpha(NIGHT, 0.12), core.alpha(NIGHT, 0.45)]))
        cr.fill()
        surf.flush()
        _GROUND.update(surf=surf, x0=x0)
    return _GROUND["surf"], _GROUND["x0"]


def _band_cobbles(y0, y1, feather=12.0):
    def draw(cr, rect):
        x, _y, w, _h = rect
        surf, gx0 = _ground()
        cr.save()
        cr.rectangle(x, y0, w, y1 - y0)
        cr.clip()
        cr.set_source_surface(surf, gx0, GROUND_Y0)
        cr.paint()
        cr.restore()
        # feather the strip's far edge so it melts into the strip behind it (DEST_IN is
        # unbounded: clip to the feather first)
        cr.save()
        cr.rectangle(x, y0, w, feather)
        cr.clip()
        cr.set_operator(cairo.OPERATOR_DEST_IN)
        cr.set_source(core.linear(0, y0, 0, y0 + feather, [core.alpha("#000000", 0.0), core.alpha("#000000", 1.0)]))
        cr.paint()
        cr.restore()
    return draw


def _layer(fn, p, blur=0.0, res=1.0, opaque=False, margin=140.0, ys=None):
    """A cached layer covering everything the camera ever shows at parallax p (optionally only
    the strip ys=(y0, y1) of it: the ground bands)."""
    rect = _extent(p, margin)
    x, y, w, h = rect
    if ys is not None:
        y0, y1 = max(y, ys[0]), min(y + h, ys[1])
        y, h = y0, y1 - y0
        rect = (x, y, w, h)
    return fx.Layer(lambda cr: fn(cr, rect), w=w, h=h, x=x, y=y, blur=blur, res=res, opaque=opaque)


# puddles on his side of the street: one he steps in, one at his feet at the end
def _step_puddle():
    best = min(PLANTS, key=lambda pl: abs(pl[0] - 5.6))
    return (walk_x(best[0]) + 30.0, GY + 9.0, 64.0, 12.0), best[0]


STEP_PUDDLE, T_SPLASH = _step_puddle()
PUDDLES_B = [STEP_PUDDLE, (X_STOP + 150.0, GY + 30.0, 118.0, 17.0), (walk_x(2.6) + 260.0, GY + 22.0, 70.0, 12.0)]
PUDDLES_C = [(walk_x(6.0) + 760.0, 1012.0, 120.0, 22.0)]


def setup():
    st = {"light_bg": fx.LightLayer(), "light": fx.LightLayer()}
    st["sky"] = _layer(_draw_sky, PX_SKY, blur=3.0, opaque=True, margin=200.0)
    cxw = K_WIDE.to_world(1430.0, 230.0, PX_CASTLE)[0]
    st["castle"] = _layer(lambda cr, r: _draw_castle(cr, r, cxw), PX_CASTLE, blur=2.5)
    st["roofs"] = _layer(_draw_roofs, PX_ROOFS, blur=1.8)
    hs = {}
    st["houses"] = _layer(lambda cr, r: _draw_houses(cr, r, hs), PX_HOUSES, blur=1.0)
    st["house_windows"] = hs["windows"]
    st["house_lamps"] = hs["lamps"]
    wl = [(wx, wy, "#ffbf5f", 0.55, HOUSE_Y + 6.0) for (wx, wy, ww, wh) in hs["windows"]]
    wl += [(lx, ly, "#ffc870", 0.9, HOUSE_Y + 6.0) for (lx, ly) in hs["lamps"]]
    st["house_refl"] = _layer(lambda cr, r: env.draw_wet_reflections(cr, wl, stretch=0.42, width=0.8, alpha=1.0,
                                                                      clip=(r[0], HOUSE_Y + 6.0, r[2], 700.0)),
                              PX_HOUSES, ys=(HOUSE_Y, 1300.0))
    # the lamps, from a dry run (their glass, for reflections, pools and lit rain)
    scratch = core.frame(4, 4)[1]
    st["post_rigs"] = [P.draw_lantern_post(scratch, x, y, POST_SC, L_SET, 0.0, height=POST_H, side=1, seed=s)
                       for (x, y, s) in POSTS]
    plights = [(r.lamp[0], r.lamp[1], P.PROP_COLORS["candle"], 1.0, r.ground[1] + 4.0) for r in st["post_rigs"]]
    st["post_lights"] = plights

    def band_b(cr, rect):
        _band_cobbles(838.0, 1012.0)(cr, rect)
        for i, pd in enumerate(PUDDLES_B):
            env.draw_puddle(cr, *pd, KIND, seed=40 + i, lights=plights, stretch=0.62)

    def band_c(cr, rect):
        _band_cobbles(948.0, GROUND_Y1, feather=16.0)(cr, rect)
        for i, pd in enumerate(PUDDLES_C):
            env.draw_puddle(cr, *pd, KIND, seed=50 + i)

    st["band_a1"] = _layer(_band_cobbles(GROUND_Y0, 796.0, feather=4.0), PX_A1, ys=(HOUSE_Y, 798.0))
    st["band_a2"] = _layer(_band_cobbles(778.0, 852.0, feather=8.0), PX_A2, ys=(776.0, 854.0))
    st["band_b"] = _layer(band_b, PX_B, ys=(836.0, 1014.0))
    st["band_c"] = _layer(band_c, PX_C, ys=(946.0, GROUND_Y1 + 2.0), blur=1.2)
    _GROUND.clear()                                          # the big paint is no longer needed
    st["post_refl"] = _layer(lambda cr, r: env.draw_wet_reflections(cr, plights, stretch=0.62, width=1.6, alpha=1.35),
                             PX_B, ys=(POST_Y - 10.0, 1400.0))
    pools = [(r.lamp[0], r.ground[1] + 6.0) for r in st["post_rigs"]]
    st["glints"] = _layer(lambda cr, r: _pool_glints(cr, pools), PX_B, ys=(POST_Y - 80.0, 1100.0))
    st["mist"] = env.Mist(-400.0, HOUSE_Y - 140.0, 7000.0, 220.0, PAL["haze"], 0.18, seed=3, speed=10.0)
    st["text"] = RuneText()
    # the final wide's isolation: the night closes in round the pool of light (a quarter-res
    # radial falloff, twice the frame, painted off-centre on him)
    iso = core.new_surface(960, 540)
    ic = core.new_context(iso)
    ic.translate(480.0, 270.0)
    ic.scale(1.0, 0.8)
    ic.set_source(core.radial(0.0, 0.0, 430.0, [(0.0, core.alpha(NIGHT, 0.0)), (0.16, core.alpha(NIGHT, 0.0)),
                                               (0.42, core.alpha(NIGHT, 0.6)), (0.7, core.alpha(NIGHT, 0.85)),
                                               (1.0, core.alpha(NIGHT, 0.92))]))
    ic.paint()
    iso.flush()
    st["iso"] = iso
    st["fg_barrel"] = _layer(_draw_fg_barrel, PX_FG, blur=6.0, res=0.5, ys=(-500.0, 1500.0))
    st["fg_door"] = _layer(_draw_fg_door, PX_FG, blur=7.0, res=0.5, ys=(-1400.0, 1500.0))
    return st


# =============================================================================================
# the dragon's acting
# =============================================================================================

E_RAISED = B.expr("raised")
E_SAD = B.expr("sad")
E_SIGH = B.expr("sigh", open=0.0)          # the exhale, mouth shut


def _k(t, keys, ease="inout_sine"):
    return core.track(t, keys, ease)


def dragon_pose(t, stone_cb, bag_cb):
    walk = walk_amt(t)
    ph = walk_phase(t)
    # eyes: ahead and down while he walks; up to "loneliness"; down at "please hold"; a look at
    # the music; down (thought) -> up at the hourglass (glance) -> the line -> down and away
    look = _k(t, [(0.0, (0.35, 0.3)), (T_RAINLOOK, (0.35, 0.3)), (T_RAINLOOK + 0.2, (0.2, -0.8)),
                  (T_RAINLOOK + 0.75, (0.25, -0.75)), (T_RAINLOOK + 1.05, (0.35, 0.3)),
                  (T_LONELY - 0.12, (0.35, 0.3)), (T_LONELY + 0.12, (0.75, -0.2)),
                  (T_PLEASE - 0.05, (0.7, -0.15)), (T_PLEASE + 0.35, (0.25, 0.55)),
                  (T_HOLD + 0.35, (0.3, 0.45)), (T_HOLD + 0.7, (0.75, 0.0)), (T_HOLD + 2.0, (0.7, 0.05)),
                  (T_HOLD + 2.5, (0.3, 0.5)), (T_LOOKDOWN + 0.3, (0.2, 0.75)), (T_GLANCE - 0.05, (0.2, 0.75)),
                  (T_GLANCE + 0.2, (0.8, -0.1)), (L4.start + 0.9, (0.75, -0.05)), (L4.start + 1.3, (0.2, 0.55)),
                  (L4.end + 0.6, (0.1, 0.7))])
    nod = _k(t, [(0.0, -0.1), (T_RAINLOOK + 0.1, -0.1), (T_RAINLOOK + 0.4, 0.12), (T_RAINLOOK + 0.8, 0.1),
                 (T_RAINLOOK + 1.2, -0.1), (T_LONELY, -0.1), (T_LONELY + 0.35, 0.06), (T_PLEASE + 0.1, 0.04),
                 (T_PLEASE + 0.7, -0.24), (T_HOLD + 0.6, -0.12), (T_STOP - 0.4, -0.22), (T_LOOKDOWN + 0.5, -0.32),
                 (T_GLANCE + 0.05, -0.3), (T_GLANCE + 0.35, -0.05), (L4.start + 1.1, -0.08), (L4.start + 1.6, -0.22),
                 (T_SIGH + 0.3, -0.3), (DUR, -0.34)])
    head_turn = _k(t, [(0.0, 0.0), (T_LONELY, 0.0), (T_LONELY + 0.3, 0.12), (T_PLEASE + 0.5, 0.0),
                       (T_GLANCE, 0.0), (T_GLANCE + 0.3, 0.1), (L4.start + 1.4, -0.05), (DUR, -0.08)])
    hunch = _k(t, [(0.0, 0.55), (T_PLEASE + 0.2, 0.55), (T_PLEASE + 0.9, 0.66), (T_STOP, 0.68),
                   (T_BREATH, 0.66), (T_BREATH + 0.3, 0.5), (L4.end, 0.56), (T_SIGH + 0.8, 0.8), (DUR, 0.82)])
    shiver = core.window(t, T_SHIVER, T_SHIVER + 0.55, 0.07, 0.3)
    hunch += 0.2 * shiver
    tilt = 0.045 * math.sin(TAU * 9.0 * (t - T_SHIVER)) * shiver
    # hope at "loneliness" (brows up), deflation at "please hold"; sadder through the hold; after
    # the line a closed-mouth exhale (the mouth moves only when he speaks)
    if t < T_PLEASE + 0.1:
        mood2, mix = E_RAISED, 0.42 * core.window(t, T_LONELY - 0.05, T_PLEASE + 0.1, 0.25, 0.25)
    else:
        sad = _k(t, [(T_PLEASE + 0.1, 0.0), (T_PLEASE + 0.8, 0.55), (T_HOLD + 1.0, 0.5),
                     (T_STOP, 0.6), (L4.start, 0.62), (L4.end, 0.62)])
        sig = 0.5 * core.window(t, T_SIGH, DUR + 5.0, 0.7, 0.1) - 0.15 * ramp(t, T_SIGH + 1.4, T_SIGH + 2.6, "inout_sine")
        mix = min(1.0, sad + sig)
        mood2 = E_SAD.blend(E_SIGH, sig / max(1e-6, sad + sig)) if sig > 0 else E_SAD
    blink = B.auto_blink(t, 2)
    blink = max(blink, core.window(t, T_PLEASE + 0.18, T_PLEASE + 0.72, 0.16, 0.24))      # the slow blink
    blink = max(blink, 0.85 * core.window(t, L2.end + 0.05, L2.end + 0.5, 0.15, 0.2))      # heard it all
    wings = _k(t, [(0.0, -0.85), (T_STOP, -0.95), (T_SIGH + 0.5, -1.0)])
    swing = 0.11 * math.sin(ph * TAU) * walk + 0.06 * B.wobble(t, T_STOP, 1.4, 1.2)
    return ch.DragonPose(facing=1, turn=_turn(t), walk=walk, phase=ph, lean=0.05 * walk, hunch=hunch,
                         head_turn=head_turn, head_nod=nod - 0.12 * shiver, head_tilt=tilt, look=look,
                         mood="tired", mood2=mood2,
                         mood_mix=mix, talk=tl.talk(SCENE, t, "MAN"), blink=blink,
                         wings=wings, tail_curl=0.25, tail_drag=_k(t, [(0.0, 0.75), (T_STOP, 0.9)]),
                         damp=1.0, seed=3,
                         near=ch.Arm("hand_to_ear", hold=stone_cb),
                         far=ch.Arm("carry_bag", hold=bag_cb(swing)))


# =============================================================================================
# the stone's voice: glowing illuminated rune-text, written word by word as it speaks
# =============================================================================================
RUNE = "#5fe0ff"
RUNE_HOT = "#e9fcff"
RUNE_DIM = "#a8eeff"
INK_DARK = "#02050d"


def note_flash(t, idx=None):
    """0..1 envelope of the music box note(s) sounding at t (only note idx if given)."""
    v = 0.0
    for (t0, d, m) in HOLD_EV:
        if t0 > t:
            break
        if idx is not None and NOTE_IDX.get(m) != idx:
            continue
        u = t - t0
        if u < d + 1.2:
            v = max(v, math.exp(-u / (0.16 + 0.45 * min(d, 0.75))) * clamp(u / 0.025))
    return v


def stone_amp(t):
    """What drives the stone's runes: the voice, then the music box."""
    a = tl.talk(SCENE, t, "PHONE")
    if t >= T_HOLD:
        a = max(a, 0.6 * note_flash(t))
    return a


def _cistercian(k, cx, cy, h):
    """Strokes of the Cistercian numeral k (the stone's own digits) centred at (cx, cy)."""
    top = cy - h * 0.5
    q = h * 0.42
    x0 = cx - q * 0.35
    ticks = {1: [((0, 0), (1, 0))], 2: [((0, 1), (1, 1))]}.get(k, [])
    out = [[(x0, top), (x0, cy + h * 0.5)]]
    for (a, b) in ticks:
        out.append([(x0 + a[0] * q, top + a[1] * q), (x0 + b[0] * q, top + b[1] * q)])
    return out


class RuneText:
    """The three menu lines as illuminated uncial script: an enlarged glowing initial, then each
    word written on by a point of light (a left-to-right wipe with a spark at the nib) on the
    word's own syllable-timed onset. Older lines cool and dim; "loneliness" lands with a pulse."""

    def __init__(self):
        _s, cr = core.frame(8, 8)
        self.lines = []
        for li, ln in enumerate(PHONE_LINES):
            toks = []
            x = 0.0
            for wi, (w, a, b) in enumerate(WORDS[ln.id]):
                dots = w.endswith("…")
                core_w = w[:-1] if dots else w
                if wi == 0:                                       # the illuminated initial
                    ini, rest = core_w[0], core_w[1:]
                    adv = core.measure(cr, ini, FS * 1.5, FONT)[0]
                    toks.append(dict(s=ini, x=x - 4.0, size=FS * 1.5, t0=a - 0.06, t1=a + 0.12, kind="initial"))
                    x += adv - 6.0
                    adv = core.measure(cr, rest, FS, FONT)[0]
                    toks.append(dict(s=rest, x=x, size=FS, t0=a + 0.06, t1=b, kind="word"))
                    x += adv
                else:
                    lonely = core_w.lower().startswith("lonel")
                    if lonely:
                        x += 6.0                                  # room for its pulse
                    adv = core.measure(cr, core_w, FS, FONT)[0] * (1.06 if lonely else 1.0)
                    toks.append(dict(s=core_w, x=x, size=FS, t0=a, t1=b, kind="lonely" if lonely else "word"))
                    x += adv
                if dots:                                          # the ellipsis: the long wait
                    nxt = WORDS[ln.id][wi + 1][1] if wi + 1 < len(WORDS[ln.id]) else b + 0.6
                    gap = max(0.3, nxt - b)
                    dw = core.measure(cr, ".", FS, FONT)[0]
                    for k in range(3):
                        td = b + (k + 0.6) * gap / 3.6
                        toks.append(dict(s=".", x=x + 2.0 + k * (dw + 3.0), size=FS, t0=td, t1=td + 0.08, kind="dot"))
                    x += 3 * (dw + 3.0) + 4.0
                x += core.measure(cr, " ", FS, FONT)[0] * 1.15
            last = [tk for tk in toks if tk["kind"] in ("word", "lonely")][-1]
            end_x = last["x"] + core.measure(cr, last["s"], last["size"], FONT)[0] * (1.06 if last["kind"] == "lonely" else 1.0)
            self.lines.append(dict(toks=toks, start=ln.start, end=ln.end, width=x, end_x=end_x,
                                   t_end=WORDS[ln.id][-1][2]))

    def draw(self, cr, t, ox, oy, stone_xy, front):
        if t < TEXT_T[0] or t > TEXT_T[1]:
            return
        fade_all = 1.0 - core.smoothstep(T_DISSOLVE0, T_DISSOLVE1 - 0.15, t)
        for li, line in enumerate(self.lines):
            if t < line["toks"][0]["t0"] - 0.3:
                continue
            nxt = self.lines[li + 1]["toks"][0]["t0"] if li + 1 < len(self.lines) else 1e9
            cool = core.smoothstep(nxt - 0.1, nxt + 0.5, t)        # an older line cools and dims
            line_a = (1.0 - 0.45 * cool) * fade_all
            by = oy + li * LH + 2.0 * math.sin(t * 1.3 + li * 1.7)
            bx = ox + 3.0 * math.sin(t * 0.9 + li)
            if line_a <= 0.01:
                continue
            for tok in line["toks"]:
                self._token(cr, t, tok, bx, by, line_a, cool, stone_xy, front)
            self._filler(cr, t, line, bx, by, line_a)

    @staticmethod
    def _filler(cr, t, line, bx, by, a):
        """A scribe's line-filler after the last word: a thin swash ending in a little spiral
        (the stone's own spiral), written on as the line ends."""
        u = clamp((t - line["t_end"] - 0.02) / 0.4)
        if u <= 0.0:
            return
        x0 = bx + line["end_x"] + 14.0
        y0 = by - FS * 0.27
        L = 70.0
        pts = [(x0, y0), (x0 + L * 0.3, y0 - 5.0), (x0 + L * 0.62, y0 + 4.0), (x0 + L * 0.88, y0 - 3.0)]
        cx, cy = x0 + L + 2.0, y0 - 7.0
        for k in range(10):
            ang = math.pi * 0.85 + k * 0.42
            rr = 9.0 * (1.0 - k / 13.0)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        n = max(2, int(round(len(pts) * core.out_cubic(u))))
        seg = pts[:n]
        cr.save()
        core.tapered(cr, seg, 3.0, 0.8)
        core.src(cr, INK_DARK, 0.35 * a)
        cr.fill()
        core.tapered(cr, seg, 1.9, 0.5)
        core.src(cr, RUNE_DIM, 0.85 * a)
        cr.fill()
        cr.restore()
        if u < 1.0:
            ex, ey = seg[-1]
            fx.glow(cr, ex, ey, 12.0, RUNE, 0.5 * a)

    def _token(self, cr, t, tok, bx, by, line_a, cool, stone_xy, front):
        t0 = tok["t0"]
        if t < t0 - 0.25:
            return
        x = bx + tok["x"]
        kind = tok["kind"]
        dur = clamp((tok["t1"] - t0) * 0.85, 0.1, 0.32) if kind not in ("dot", "numeral") else 0.12   # == T_LONELY_LAND
        u = clamp((t - t0) / dur)
        # a spark travels from the stone to the start of the word, just before it is written
        if kind != "dot" and t < t0 + 0.02 and stone_xy is not None:
            v = clamp((t - (t0 - 0.24)) / 0.24)
            if v > 0:
                sx, sy = stone_xy
                ex, ey = x, by - FS * 0.35
                mx, my = (sx + ex) / 2, min(sy, ey) - 60.0
                e = core.inout_sine(v)
                px = (1 - e) ** 2 * sx + 2 * (1 - e) * e * mx + e * e * ex
                py = (1 - e) ** 2 * sy + 2 * (1 - e) * e * my + e * e * ey
                fx.glow(cr, px, py, 16.0, RUNE, 0.55 * line_a)
                fx.glow(cr, px, py, 5.0, RUNE_HOT, 0.9 * line_a)
            return
        if u <= 0:
            return
        hot = math.exp(-max(0.0, t - (t0 + dur)) / 0.45)          # just-written words burn brighter
        a = line_a
        if kind == "numeral":
            strokes = _cistercian(tok["k"], x + 10.0, by - FS * 0.33, FS * 0.62)
            B.detail_lines(cr, strokes, 5.0, RUNE, 0.35 * a * u, taper=(1.0, 1.0, 1.0))
            B.detail_lines(cr, strokes, 2.2, RUNE_HOT, 0.95 * a * u, taper=(1.0, 1.0, 1.0))
            return
        size = tok["size"]
        scale = 1.0
        glow_a = (0.75 + 0.6 * hot) * (1.0 - 0.35 * cool)
        wv = core.measure(cr, tok["s"], size, FONT)[0]
        if kind == "lonely":                                     # it lands with a beat: when the
            v = t - (t0 + dur)                                   # nib finishes, a pop and a flash
            if v < 0.0:
                scale = 1.06
            else:
                scale = 1.06 + 0.13 * math.exp(-v / 0.22) * math.cos(v * 11.0)
                glow_a *= 1.0 + 1.3 * math.exp(-v / 0.55)
                fx.glow(front, x + wv / 2, by - FS * 0.35, 280.0, RUNE, 0.34 * math.exp(-v / 0.6) * a)
                rr = 40.0 + 260.0 * core.out_cubic(clamp(v / 0.7))         # a ring of cold light
                cr.save()
                cr.set_operator(cairo.OPERATOR_ADD)
                cr.set_line_width(2.0)
                core.src(cr, RUNE, 0.22 * (1.0 - clamp(v / 0.7)) * a)
                core.ellipse(cr, x + wv / 2, by - FS * 0.35, rr, rr * 0.32)
                cr.stroke()
                cr.restore()
        col = core.mix(RUNE_DIM, RUNE_HOT, 0.6 + 0.4 * hot)
        cr.save()
        if scale != 1.0:                                         # grows from its left edge
            cr.translate(x, by - FS * 0.33)
            cr.scale(scale, scale)
            cr.translate(-x, -(by - FS * 0.33))
        edge = x - 6.0 + (wv + 14.0) * core.out_cubic(u)
        if u < 1.0:                                              # written on by a point of light
            cr.rectangle(x - 40.0, by - size * 1.4, edge - (x - 40.0), size * 2.2)
            cr.clip()
        # legibility: a soft dark halo first (painted), then the cold glow and the letters
        core.glow_text(cr, tok["s"], x, by, size, FONT, INK_DARK, glow=INK_DARK, radius=13.0,
                       glow_alpha=0.55 * a, additive=False, alpha_=0.0)
        core.glow_text(cr, tok["s"], x, by, size, FONT, col, glow=RUNE, radius=9.0, glow_alpha=glow_a * a,
                       alpha_=a, passes=2 if kind in ("initial", "lonely") else 1)
        cr.restore()
        if u < 1.0:                                              # the nib's spark
            fx.glow(cr, edge, by - size * 0.3, 18.0, RUNE, 0.6 * a)
            fx.sparkle(cr, edge, by - size * 0.3, 9.0, RUNE_HOT, 0.8 * a, angle=t * 3.0)


# =============================================================================================
# the hold: four notes on a scrap of four-line staff between repeat signs, and an hourglass
# =============================================================================================
STAFF_SP = 13.0                                     # staff line spacing
NOTE_DX = 62.0
NOTE_STEPS = (0, 1, 3, 4)                           # B5 A5 F#5 E5: diatonic steps down


def hold_anchor(t):
    """Where the hold loop floats (world, his plane): beside his face, a beat behind him."""
    xh = walk_x(t - 0.35) + 225.0
    return xh, GY - 412.0 + 6.0 * math.sin(t * 0.8)


HOLD_SC = 1.3                                     # the loop's size (its own scale about the anchor)


def draw_hold(cr, t, front):
    if t < T_DISSOLVE0 + 0.2:
        return
    ax, ay = hold_anchor(t)
    cr.save()
    cr.translate(ax, ay)
    cr.scale(HOLD_SC, HOLD_SC)
    cr.translate(-ax, -ay)
    front.save()
    front.translate(ax, ay)
    front.scale(HOLD_SC, HOLD_SC)
    front.translate(-ax, -ay)
    try:
        _draw_hold(cr, t, front, ax, ay)
    finally:
        front.restore()
        cr.restore()


def _draw_hold(cr, t, front, ax, ay):
    appear = core.smoothstep(T_HOLD - 0.25, T_HOLD + 0.25, t)
    # the staff scrap
    x0 = ax - 40.0
    x1 = ax + 3 * NOTE_DX + 40.0
    cr.save()
    cr.set_line_width(1.4)
    for k in range(4):
        y = ay + (k - 1.5) * STAFF_SP
        cr.move_to(x0, y)
        cr.line_to(x1, y)
    cr.set_source(core.linear(x0, 0, x1, 0, [(0.0, core.alpha(RUNE, 0.0)), (0.12, core.alpha(RUNE, 0.45 * appear)),
                                            (0.88, core.alpha(RUNE, 0.45 * appear)), (1.0, core.alpha(RUNE, 0.0))]))
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.stroke()
    # repeat signs: over and over
    for xs, sgn in ((x0 + 22.0, 1), (x1 - 22.0, -1)):
        core.src(cr, RUNE_HOT, 0.75 * appear)
        cr.rectangle(xs - 1.5 * sgn - (3.0 if sgn > 0 else 0.0), ay - 1.5 * STAFF_SP, 3.0, 3 * STAFF_SP)
        cr.rectangle(xs + 3.5 * sgn - 0.7, ay - 1.5 * STAFF_SP, 1.4, 3 * STAFF_SP)
        cr.fill()
        for dy in (-0.5, 0.5):
            core.circle(cr, xs + 9.0 * sgn, ay + dy * STAFF_SP, 2.4)
        cr.fill()
    cr.restore()
    # the four notes, each lighting up exactly as the music box plays it
    for k in range(4):
        first = T_HOLD + sum((0.25, 0.25, 0.25, 0.75)[:k]) * LOOP / 1.5
        pop = core.smoothstep(first - 0.05, first + 0.12, t)
        if pop <= 0:
            continue
        fl = note_flash(t, k)
        nx = ax + k * NOTE_DX
        ny = ay + (NOTE_STEPS[k] * 0.5 - 1.0) * STAFF_SP - 6.0 * fl
        size = (1.15 + 0.35 * fl) * (0.6 + 0.4 * core.out_back(pop))
        alpha = (0.45 + 0.55 * fl) * pop
        P.draw_music_note(cr, nx, ny, size, t, RUNE, alpha, "minim" if k == 3 else "semiminim", 0.0, True)
        if k == 3:                                   # the long note's dot
            core.circle(cr, nx + 15.0 * size, ny - 2.0, 2.6 * size)
            core.src(cr, RUNE_HOT, alpha)
            cr.fill()
        if fl > 0.05:
            fx.glow(front, nx, ny - 8.0, 70.0, RUNE, 0.35 * fl)
    # the hourglass: running out every two loops, flipping as the loop comes round again
    hx, hy = _note_local(t, 4)[2:]
    pop = core.smoothstep(T_HOLD - 0.1, T_HOLD + 0.3, t)
    if pop > 0:
        P.draw_hourglass(cr, hx, hy, 1.35 * (0.7 + 0.3 * core.out_back(pop)), L_COLD, t - T_HOLD, period=HG_PERIOD,
                         flip_time=HG_FLIP, glow=pop, label=None)
        core.glow_text(cr, "On hold", hx, hy + 66.0, 24.0, FONT, RUNE_HOT, glow=RUNE, radius=6.0,
                       glow_alpha=0.8 * pop, align="center", alpha_=pop)


def _note_local(t, k):
    ax, ay = hold_anchor(t)
    if k >= 4:
        return ax, ay, ax + 3 * NOTE_DX + 120.0, ay - 6.0
    return ax, ay, ax + k * NOTE_DX, ay + (NOTE_STEPS[k] * 0.5 - 1.0) * STAFF_SP


def note_world(t, k):
    """World position (his plane) of hold note k (0..3) or the hourglass (k = 4) at time t."""
    ax, ay, x, y = _note_local(t, k)
    return ax + (x - ax) * HOLD_SC, ay + (y - ay) * HOLD_SC


NOTE_FIRST = [T_HOLD + sum((0.25, 0.25, 0.25, 0.75)[:k]) * LOOP / 1.5 for k in range(4)] + [T_HOLD]
_MOTES = []


def _motes(text):
    """The dissolve: each mote leaves a letter of the menu and flies into a note of the loop
    (or into the hourglass), arriving as that note first sounds."""
    if not _MOTES:
        rng = np.random.default_rng(29)
        boxes = []
        for li, line in enumerate(text.lines):
            for tok in line["toks"]:
                if tok["kind"] in ("dot",):
                    continue
                boxes.append((li, tok["x"], max(8.0, core.measure(core.frame(4, 4)[1], tok["s"], tok["size"], FONT)[0])))
        wsum = sum(b[2] for b in boxes)
        for i in range(64):
            r = rng.random() * wsum
            for (li, bx, bw) in boxes:
                r -= bw
                if r <= 0:
                    break
            k = i % 5
            born = T_DISSOLVE0 + 0.45 * rng.random()
            arrive = max(born + 0.45, NOTE_FIRST[k] - 0.02 + 0.08 * rng.random())
            _MOTES.append(dict(li=li, x=bx + bw * rng.random(), y=-FS * (0.15 + 0.5 * rng.random()), k=k,
                               born=born, arrive=arrive, lift=40.0 + 120.0 * rng.random(), size=0.7 + 0.6 * rng.random()))
    return _MOTES


def draw_dissolve(cr, t, cam, text, ox, oy):
    if t < T_DISSOLVE0 or t > T_HOLD + 1.2:
        return
    for m in _motes(text):
        if t < m["born"] or t > m["arrive"] + 0.15:
            continue
        u = clamp((t - m["born"]) / (m["arrive"] - m["born"]))
        e = core.inout_sine(u)
        sx, sy = ox + m["x"], oy + m["li"] * LH + m["y"]
        ex, ey = cam.to_screen(*note_world(t, m["k"]), PX_B)
        cx, cy = (sx + ex) / 2, min(sy, ey) - m["lift"]
        px = (1 - e) ** 2 * sx + 2 * (1 - e) * e * cx + e * e * ex
        py = (1 - e) ** 2 * sy + 2 * (1 - e) * e * cy + e * e * ey
        a = clamp(u * 6.0) * (1.0 - clamp((t - m["arrive"]) / 0.15))
        fx.glow(cr, px, py, 9.0 * m["size"], RUNE, 0.55 * a)
        fx.glow(cr, px, py, 3.0 * m["size"], RUNE_HOT, 0.9 * a)


def hourglass_flips():
    """Local times at which the hourglass starts a flip."""
    out = []
    k = 1
    while T_HOLD + k * HG_PERIOD - HG_FLIP < DUR:
        out.append(T_HOLD + k * HG_PERIOD - HG_FLIP)
        k += 1
    return out


# =============================================================================================
# rain: world-locked drops in three depths, lit up inside the lamps' glow
# =============================================================================================
RAIN_TILE = 1100.0
RAIN_Y = (-900.0, 1500.0)
RAIN_ANGLE = 0.13
_RAIN_CACHE = {}
RAIN_C = core.mix(PAL["haze"], "#c8d8f0", 0.62)


def _rain_tile(seed, k, n):
    key = (seed, k, n)
    r = _RAIN_CACHE.get(key)
    if r is None:
        rng = np.random.default_rng(seed * 100003 + k * 7919 + 17)
        r = (rng.random(n), rng.random(n), rng.random(n), rng.random(n))
        _RAIN_CACHE[key] = r
    return r


def rain_drops(cam, p, t, n, speed, length, seed):
    """Drop segments [(x0, y0, x1, y1)] (world coords of parallax p) visible at time t."""
    x0, y0 = cam.to_world(-80.0, -80.0, p)
    x1, y1 = cam.to_world(W + 80.0, H + 80.0, p)
    dx, dy = math.sin(RAIN_ANGLE), math.cos(RAIN_ANGLE)
    span = (RAIN_Y[1] - RAIN_Y[0]) / dy
    segs = []
    for k in range(int(math.floor(x0 / RAIN_TILE)) - 1, int(math.floor(x1 / RAIN_TILE)) + 1):
        a, b, c, d = _rain_tile(seed, k, n)
        sp = speed * (0.8 + 0.4 * c)
        dd = (a * span + sp * t) % span
        px = k * RAIN_TILE + b * RAIN_TILE + dd * dx
        py = RAIN_Y[0] + dd * dy
        L = length * (0.7 + 0.6 * d)
        m = (py + L > y0) & (py < y1) & (px > x0 - 60) & (px < x1 + 60)
        for xx, yy, ll in zip(px[m], py[m], L[m]):
            segs.append((xx, yy, xx + dx * ll, yy + dy * ll))
    return segs


def stroke_segs(cr, segs, width, color, alpha):
    if not segs:
        return
    for (a, b, c, d) in segs:
        cr.move_to(a, b)
        cr.line_to(c, d)
    cr.set_line_width(width)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    core.src(cr, color, alpha)
    cr.stroke()


def _cone_path(cr, lx, ly, gy, w0=26.0, w1=260.0):
    cr.move_to(lx - w0, ly)
    cr.line_to(lx + w0, ly)
    cr.line_to(lx + w1, gy)
    cr.line_to(lx - w1, gy)
    cr.close_path()


def draw_rain_layer(cr, cam, t, p, n, speed, length, width, alpha, seed, lamps=()):
    """One depth of rain. lamps = [(x, y, r, ground_y)] in this plane: drops passing through a
    lamp's halo or its cone of light turn gold."""
    with cam.view(cr, p):
        segs = rain_drops(cam, p, t, n, speed, length, seed)
        stroke_segs(cr, segs, width, RAIN_C, alpha)
        for (lx, ly, r, gy) in lamps:
            near = [s for s in segs if (abs(s[0] - lx) < r and ly - r < s[1] < gy)]
            if not near:
                continue
            cr.save()
            cr.set_operator(cairo.OPERATOR_ADD)
            for ring, al in ((1.0, 0.2), (0.62, 0.26), (0.34, 0.32)):        # the halo round the lamp
                cr.save()
                cr.arc(lx, ly, r * ring, 0, TAU)
                cr.clip()
                stroke_segs(cr, near, width * 1.1, "#ffc46a", al * 1.6)
                cr.restore()
            for k, al in ((1.0, 0.22), (0.6, 0.22)):                          # the cone below it
                cr.save()
                _cone_path(cr, lx, ly + 20.0, gy, 26.0 * k, 250.0 * k)
                cr.clip()
                cr.rectangle(lx - 400.0, ly + 20.0, 800.0, (gy - ly) * 0.92)
                cr.clip()
                stroke_segs(cr, near, width * 1.1, "#ffc46a", al * 1.5)
                cr.restore()
            cr.restore()


def lamp_light(lc, rig, t, flick, front=False, boost=1.0):
    """A street lamp's light in the rain: the halo, a soft cone of lit rain-air down to the
    cobbles, and the warm pool it throws on the wet stones (boost > 1: the final wide)."""
    lx, ly = rig.lamp
    gy = rig.ground[1] + 6.0
    if front:                                         # the haze of the cone in front of him
        fx.light_shaft(lc, lx, ly + 22.0, lx, gy, 50.0, 470.0, "#ffbe6e", 0.05 * flick * boost, soft=3,
                       fade_start=1.0, fade_end=0.7)
        return
    P.lantern_light(lc, rig, POST_SC, t, 1.0)
    fx.light_shaft(lc, lx, ly + 22.0, lx, gy, 46.0, 520.0, "#ffbe6e", 0.3 * flick * boost, soft=4,
                   fade_start=1.0, fade_end=0.25)
    fx.light_pool(lc, lx, gy + 4.0, 360.0 * (0.9 + 0.1 * boost), 64.0, "#ffb860", 0.7 * flick * boost)
    fx.light_pool(lc, lx, gy + 2.0, 170.0, 30.0, "#ffd9a0", 0.45 * flick * boost)


def _hash_np(a, seed):
    v = (a.astype(np.uint64) * np.uint64(2654435761) + np.uint64(seed * 97531 + 12345)) & np.uint64(0xFFFFFFFF)
    v ^= v >> np.uint64(15)
    v = (v * np.uint64(2246822519)) & np.uint64(0xFFFFFFFF)
    v ^= v >> np.uint64(13)
    return (v & np.uint64(0xFFFFFF)).astype(np.float64) / float(0xFFFFFF)


def draw_splashes(cr, cam, t, p, y0, y1, n_per_tile, size, alpha, seed, tile=900.0):
    """Raindrops bursting on the street: world-locked slots in tiles along the band y0..y1."""
    with cam.view(cr, p):
        x0, _ = cam.to_world(-40.0, 0.0, p)
        x1, _ = cam.to_world(W + 40.0, 0.0, p)
        c = core.col(core.tint(RAIN_C, 0.25))
        cr.set_line_width(max(0.8, size * 0.12))
        idx = np.arange(n_per_tile)
        for k in range(int(math.floor(x0 / tile)), int(math.floor(x1 / tile)) + 1):
            base = (k + 1000) * 1000 + idx
            period = 0.45 + 0.5 * _hash_np(base, seed)
            ph = _hash_np(base, seed + 1) * period
            cyc = np.floor((t + ph) / period)
            u = ((t + ph) % period) / 0.3
            m = u < 1.0
            if not m.any():
                continue
            cid = (cyc * 131 + base).astype(np.int64)
            px = k * tile + _hash_np(cid, seed + 2) * tile
            py = y0 + _hash_np(cid, seed + 3) * (y1 - y0)
            for xx, yy, uu, ii in zip(px[m], py[m], u[m], idx[m]):
                s = size * (0.45 + 0.55 * (yy - y0) / max(1.0, y1 - y0)) * (0.7 + 0.06 * (ii % 11))
                a = alpha * (1.0 - uu) ** 1.5
                cr.set_source_rgba(c[0], c[1], c[2], a)
                core.ellipse(cr, xx, yy, s * (0.3 + uu), s * 0.28 * (0.3 + uu))
                cr.stroke()
                for sg in (-1, 1):
                    cr.arc(xx + sg * s * 0.6 * uu, yy - s * 3.5 * uu * (1.0 - uu), max(0.6, s * 0.09), 0, TAU)
                    cr.fill()


# =============================================================================================
# the lamps' pools on the wet stones, and his reflection in them
# =============================================================================================
def _pool_glints(cr, pools):
    """Warm specular glints on the crowns of the wet cobbles round each lamp's foot: what makes
    a pool of lamplight read as WET (static; painted additive with the flame's flicker)."""
    rng = np.random.default_rng(5)
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    for (lx, gy) in pools:
        for _i in range(420):
            dx = rng.normal(0.0, 165.0)
            dy = abs(rng.normal(0.0, 30.0)) * (1.0 if rng.random() < 0.8 else -0.4) + 4.0
            d = math.hypot(dx / 330.0, dy / 80.0)
            if d >= 1.0:
                continue
            a = (1.0 - d) ** 1.6 * (0.35 + 0.65 * rng.random())
            y = gy + dy
            size = _cobble_size(y)
            gw = size * (0.25 + 0.45 * rng.random())
            gh = max(0.7, size * 0.08)
            core.ellipse(cr, lx + dx, y, gw, gh)
            core.src(cr, "#ffcf86", min(1.0, 0.75 * a))
            cr.fill()
            if rng.random() < 0.3:
                core.ellipse(cr, lx + dx, y, gw * 0.35, gh * 0.8)
                core.src(cr, "#fff3d6", min(1.0, 0.8 * a))
                cr.fill()
    cr.restore()


DBOX = (340.0, 610.0, 270.0, 70.0)     # left, up, right, down margins round his anchor (px at zoom 1)
DS_W, DS_H = 700, 780                  # covers the box at the closest zoom (1.12)
_DS = {}


def _dsurf(key, w, h):
    surf = _DS.get(key)
    if surf is None:
        surf = _DS[key] = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return surf


def render_dragon(cam, t, xd, pose, light):
    """Draw him ONCE into an offscreen buffer (screen pixels, integer offset): the same image is
    composited into the frame, mirrored for his reflection in the wet street, and used as the
    mask for the lamp's top-light and the pool's bounce. Returns (surface, ox, oy, rig)."""
    z = cam.zoom
    sx, sy = cam.to_screen(xd, GY, PX_B)
    ox, oy = int(math.floor(sx - DBOX[0] * z)), int(math.floor(sy - DBOX[1] * z))
    surf = _dsurf("dragon", DS_W, DS_H)
    c = cairo.Context(surf)
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.paint()
    c.set_operator(cairo.OPERATOR_OVER)
    c.translate(-ox, -oy)
    c.transform(cam.matrix(PX_B))
    rig = ch.draw_dragon(c, xd, GY, SC, pose.with_(shadow=False), light, t)
    surf.flush()
    return surf, ox, oy, rig


def draw_shadows(cr, rig, xd, k_lamp):
    """(his plane) The contact shadow under his feet, and the short shadow the lamp above and
    behind him throws forward across its own pool of light."""
    fx_ = (rig.feet[0][0] + rig.feet[1][0]) / 2.0 - 10.0 * math.sin(rig.yaw) * SC
    w = (64.0 + 26.0 * abs(math.cos(rig.yaw))) * SC
    B.contact_shadow(cr, fx_, GY + 2.0 * SC, w, 13.0 * SC, alpha=0.4)
    if k_lamp > 0.02:
        env.draw_ground_shadow(cr, fx_ + 70.0, GY + 6.0, 120.0 * SC + 40.0, 15.0, 0.42 * k_lamp)


def composite_dragon(cr, surf, ox, oy):
    cr.set_source_surface(surf, ox, oy)
    cr.paint()


def edge_light(cr, surf, ox, oy, dx, dy, color, alpha, y_fade=None):
    """Paint `color` along the dragon's contours that face away from the offset (dx, dy) (screen
    px): the dragon minus itself shifted by (dx, dy), at half resolution (soft edges). y_fade =
    (y0, y1, a0, a1) ramps the strength over screen y. Painted OVER (a warm rim over teal must
    stay warm, never turn additive green-white)."""
    if alpha <= 0.01:
        return
    small = _dsurf("edge", DS_W // 2 + 2, DS_H // 2 + 2)
    c = cairo.Context(small)
    c.set_operator(cairo.OPERATOR_SOURCE)
    c.scale(0.5, 0.5)
    c.set_source_surface(surf, 0, 0)
    c.get_source().set_filter(cairo.FILTER_GOOD)
    c.paint()
    c.set_operator(cairo.OPERATOR_DEST_OUT)
    c.set_source_surface(surf, dx, dy)
    c.get_source().set_filter(cairo.FILTER_GOOD)
    c.paint()
    c.set_operator(cairo.OPERATOR_IN)
    core.src(c, color)
    c.paint()
    small.flush()
    cr.save()
    cr.translate(ox, oy)
    cr.scale(2.0, 2.0)
    cr.set_source_surface(small, 0, 0)
    cr.get_source().set_filter(cairo.FILTER_BILINEAR)
    if y_fade is None:
        cr.paint_with_alpha(alpha)
    else:
        y0, y1, a0, a1 = y_fade
        cr.mask(core.linear(0, (y0 - oy) / 2.0, 0, (y1 - oy) / 2.0,
                            [core.alpha("#000000", alpha * a0), core.alpha("#000000", alpha * a1)]))
    cr.restore()


def draw_reflection(cr, surf, ox, oy, gy_s, z):
    """His reflection in the wet street: the offscreen image at a third of the resolution
    (soft, as on a rough wet surface), mirrored about his ground line, fading with depth."""
    small = _dsurf("refl", DS_W // 3 + 2, DS_H // 3 + 2)
    c = cairo.Context(small)
    c.set_operator(cairo.OPERATOR_SOURCE)
    c.scale(1.0 / 3.0, 1.0 / 3.0)
    c.set_source_surface(surf, 0, 0)
    c.get_source().set_filter(cairo.FILTER_GOOD)
    c.paint()
    small.flush()
    pat = cairo.SurfacePattern(small)
    pat.set_matrix(cairo.Matrix(xx=1.0 / 3.0, yx=0.0, xy=0.0, yy=-1.0 / 3.0, x0=-ox / 3.0, y0=(2.0 * gy_s - oy) / 3.0))
    pat.set_filter(cairo.FILTER_BILINEAR)
    cr.save()
    cr.rectangle(ox, gy_s - 1.0, DS_W, 330.0 * z)
    cr.clip()
    cr.set_source(pat)
    cr.mask(core.linear(0, gy_s, 0, gy_s + 300.0 * z, [(0.0, core.alpha("#000000", 0.42)), (0.35, core.alpha("#000000", 0.18)),
                                                       (1.0, core.alpha("#000000", 0.0))]))
    cr.restore()


def lamp_k(xd):
    """How strongly a street lamp overhead lights him (0..1), by distance from the nearest lamp."""
    k = 0.0
    for (px, _py, _s) in POSTS:
        d = abs(xd + HEAD_DX - (px + POST_ARM))
        k = max(k, clamp(1.0 - (d - 60.0) / 330.0))
    return smooth(k)


# =============================================================================================
# his feet in the wet: a few droplets kick up at every heel strike, a real splash in the puddle
# =============================================================================================
STEP_FWD = 0.25 * 150.0 * SC                    # heel strike: a quarter stride ahead of the anchor


def draw_step_splashes(cr, t):
    """In his plane's view. Pure function of t (the heel strikes come from the walk integrator)."""
    for (tp, foot) in PLANTS:
        u = t - tp
        if u < 0.0 or u > 0.6:
            continue
        big = abs(tp - T_SPLASH) < 0.05
        fx_ = walk_x(tp) + STEP_FWD * math.sin(1.24) + (8.0 if foot else -4.0)
        fy = GY + 4.0
        n = 14 if big else 5
        for i in range(n):
            a = -math.pi * (0.12 + 0.76 * core.hash01(i + int(tp * 100) * 31, 17))
            v = (110.0 + 190.0 * core.hash01(i, 18 + int(tp * 10))) * (1.0 if big else 0.55)
            vx, vy = math.cos(a) * v, math.sin(a) * v
            x = fx_ + vx * u
            y = fy + vy * u + 0.5 * 1400.0 * u * u
            if y > fy + 2.0:
                continue
            al = (0.55 if big else 0.35) * (1.0 - u / 0.6)
            core.circle(cr, x, y, 1.6 if big else 1.1)
            core.src(cr, "#d6e4f7", al)
            cr.fill()
        if big:
            for k in range(2):
                w = clamp((u - 0.06 * k) / 0.5)
                if 0.0 < w < 1.0:
                    rx = 14.0 + 70.0 * core.out_cubic(w)
                    cr.set_line_width(1.4)
                    core.src(cr, "#c8daf2", 0.45 * (1.0 - w))
                    core.ellipse(cr, fx_, fy + 4.0, rx, rx * 0.2)
                    cr.stroke()


# =============================================================================================
# the rain on him: drops striking his horns, head and shoulders, a drip off the end of his snout
# =============================================================================================

def draw_rain_on_him(cr, t, rig):
    """(his plane) Pure function of t: a few drops burst on his upper contours every second, and
    every ~1.6 s a drop gathers at his snout tip, swells and falls."""
    hx, hy = rig.head
    tx, ty = rig.top
    hits = [(tx - 6.0, ty + 4.0), (hx - 30.0, hy + 2.0), (hx - 52.0, hy + 46.0), (hx - 70.0, hy + 92.0),
            (rig.hand_near.x + 6.0, rig.hand_near.y - 30.0)]
    for i in range(10):
        per = 0.55 + 0.5 * core.hash01(i, 301)
        u = ((t + per * core.hash01(i, 302)) % per) / 0.22
        if u >= 1.0:
            continue
        cyc = int((t + per * core.hash01(i, 302)) // per)
        bx, by = hits[int(core.hash01(cyc * 13 + i, 303) * len(hits))]
        bx += (core.hash01(cyc * 7 + i, 304) - 0.5) * 16.0
        for k in (-1.0, 1.0):
            px = bx + k * 9.0 * u
            py = by - 12.0 * u * (1.0 - u) * 2.0
            core.circle(cr, px, py, 1.3)
            core.src(cr, "#d6e6fa", 0.6 * (1.0 - u))
            cr.fill()
    # the snout drip (only while he is still: walking shakes it off)
    if walk_amt(t) < 0.3:
        nx, ny = rig.nose
        per = 1.6
        u = (t % per) / per
        if u < 0.75:                                          # gathering at the tip
            r = 1.0 + 2.2 * (u / 0.75)
            core.ellipse(cr, nx + 4.0, ny + 6.0 + r, r * 0.8, r)
            core.src(cr, "#cfe2fa", 0.55)
            cr.fill()
        else:                                                 # falling
            v = (u - 0.75) / 0.25
            yy = ny + 9.0 + 900.0 * (v * per * 0.25) ** 2
            if yy < GY:
                core.ellipse(cr, nx + 4.0, yy, 1.6, 3.4)
                core.src(cr, "#cfe2fa", 0.5)
                cr.fill()


def draw_text_reflection(lc, t, text, ox, oy, gy_s, z=1.0):
    """(screen space, the light layer) The glowing menu mirrored in the wet street: under every
    written word a soft cold streak runs down the wet cobbles from his ground line, flickering
    with the rain (the higher the line, the fainter and longer its streak)."""
    if t < TEXT_T[0] or t > TEXT_T[1]:
        return
    fade_all = 1.0 - core.smoothstep(T_DISSOLVE0, T_DISSOLVE1 - 0.15, t)
    _s, mc = core.frame(4, 4)
    for li, line in enumerate(text.lines):
        nxt = text.lines[li + 1]["toks"][0]["t0"] if li + 1 < len(text.lines) else 1e9
        a = (1.0 - 0.45 * core.smoothstep(nxt - 0.1, nxt + 0.5, t)) * fade_all
        for k, tk in enumerate(line["toks"]):
            if tk["kind"] not in ("word", "lonely") or t < tk["t0"]:
                continue
            on = clamp((t - tk["t0"]) / 0.3)
            wv = core.measure(mc, tk["s"], tk["size"], FONT)[0]
            xx = ox + tk["x"] + wv / 2
            fl = 0.65 + 0.35 * core.noise1(t * 2.5 + k * 1.9 + li * 7.0, 41)
            boost = 1.6 if tk["kind"] == "lonely" else 1.0
            y0 = gy_s + 6.0 * z
            L = (130.0 + 40.0 * (2 - li)) * z
            fx.light_shaft(lc, xx, y0, xx, y0 + L, wv * 0.55, wv * 0.75, RUNE, 0.2 * a * fl * on * boost, soft=2,
                           fade_start=1.0, fade_end=1.0)


# =============================================================================================
# foreground (the near side of the street, close to the camera, out of focus): a downspout
# pouring into a rain barrel frames the opening; a doorway's post and lintel slide in as the
# camera pulls back, so the film leaves him the way we found him -- watched from the dark
# =============================================================================================
PX_FG = 1.8
FG_SC = SC * PX_FG
FG_INK = "#05070d"


def _fg_x(t, sx):
    return camera_base(t).to_world(sx, H / 2, PX_FG)[0]


BARREL_X = _fg_x(0.0, 175.0)              # in frame at the start, gone by ~1.5 s
DOOR_X = _fg_x(DUR, 1790.0)              # the doorway post's inner edge in the final frame
LINTEL_Y = camera_base(DUR).to_world(W / 2, 205.0, PX_FG)[1]


def _draw_fg_barrel(cr, rect):
    s = FG_SC
    x, gy = BARREL_X, 1080.0 + 150.0
    w, h = 200.0 * s, 290.0 * s
    top = gy - h
    pts = [(x - w * 0.43, gy), (x - w * 0.5, gy - h * 0.5), (x - w * 0.43, top), (x + w * 0.43, top),
           (x + w * 0.5, gy - h * 0.5), (x + w * 0.43, gy)]
    core.smooth_closed(cr, pts, 0.55)
    core.src(cr, "#1c1612")
    cr.fill()
    cr.save()
    core.smooth_closed(cr, pts, 0.55)
    cr.clip()
    # the staves: a rounded body (dark at the sides), the joints between them
    cr.set_source(core.linear(x - w * 0.5, 0, x + w * 0.5, 0, [(0.0, core.alpha("#000000", 0.55)), (0.45, core.alpha("#000000", 0.0)),
                                                             (0.8, core.alpha("#000000", 0.15)), (1.0, core.alpha("#000000", 0.6))]))
    cr.rectangle(x - w, top, 2 * w, h)
    cr.fill()
    for k in range(-4, 5):
        xx = x + k * w * 0.1
        cr.rectangle(xx - 1.2, top, 2.4, h)
    core.src(cr, "#000000", 0.35)
    cr.fill()
    # iron hoops, each with a lit upper edge
    for hy in (0.1, 0.4, 0.82):
        cr.rectangle(x - w, top + h * hy, 2 * w, 11.0 * s)
        core.src(cr, "#101114")
        cr.fill()
        cr.rectangle(x - w, top + h * hy, 2 * w, 2.0 * s)
        core.src(cr, "#6a5a4a", 0.6)
        cr.fill()
    # the lamp behind it rims its right side warm; the sky rims the left cold
    cr.set_source(core.linear(x + w * 0.3, 0, x + w * 0.52, 0, [core.alpha("#ffb766", 0.0), core.alpha("#ffb766", 0.55)]))
    cr.rectangle(x, top, w, h)
    cr.fill()
    cr.set_source(core.linear(x - w * 0.52, 0, x - w * 0.38, 0, [core.alpha("#8fb0e0", 0.3), core.alpha("#8fb0e0", 0.0)]))
    cr.rectangle(x - w, top, w, h)
    cr.fill()
    cr.restore()
    # the brimming water at the top: dark, with a bright rim
    core.ellipse(cr, x, top + 2.0 * s, w * 0.43, 15.0 * s)
    core.src(cr, "#2a2018")
    cr.fill()
    core.ellipse(cr, x, top + 5.0 * s, w * 0.39, 11.0 * s)
    core.src(cr, "#1b2638")
    cr.fill()
    cr.set_line_width(3.0)
    core.src(cr, "#ffcf8a", 0.35)
    cr.arc(x, top + 5.0 * s, w * 0.39, -0.1, 0.9)
    cr.stroke()
    # the downspout: a wooden trough angling down off the eaves, lit along its edge
    sp = [(x - w * 0.95, -300.0), (x - w * 0.78, -300.0), (x - w * 0.08, top - 70.0 * s), (x - w * 0.25, top - 60.0 * s)]
    core.polygon(cr, sp)
    core.src(cr, "#140f0c")
    cr.fill()
    cr.move_to(x - w * 0.78, -300.0)
    cr.line_to(x - w * 0.08, top - 70.0 * s)
    cr.set_line_width(4.0)
    core.src(cr, "#ffb766", 0.3)
    cr.stroke()


def _draw_fg_door(cr, rect):
    """The near side's eave (all along the street, just above the frame until the pull-back)
    and one doorway post that the pull-back reveals at the right."""
    s = FG_SC
    x0, _y, w, _h = rect
    x = DOOR_X
    core.src(cr, FG_INK)
    cr.rectangle(x0, LINTEL_Y - 900.0, w, 900.0)                         # the eave beam
    cr.fill()
    for k in range(int(w / (420.0 * s)) + 2):                            # carved joist ends
        bx = x0 + k * 420.0 * s
        core.rounded_rect(cr, bx - 22.0 * s, LINTEL_Y - 4.0, 44.0 * s, 34.0 * s, 10.0 * s)
        cr.fill()
    cr.rectangle(x, LINTEL_Y - 900.0, 900.0, 4000.0)                     # the doorway post
    cr.fill()
    br = [(x, LINTEL_Y + 120.0 * s), (x - 70.0 * s, LINTEL_Y + 8.0 * s), (x - 260.0 * s, LINTEL_Y - 2.0),
          (x, LINTEL_Y - 2.0)]
    core.smooth_closed(cr, br, 0.4)
    cr.fill()
    # the lamp's warm light catching the wood's inner edges
    cr.set_source(core.linear(x, 0, x + 26.0 * s, 0, [core.alpha("#ffb060", 0.32), core.alpha("#ffb060", 0.0)]))
    cr.rectangle(x, LINTEL_Y + 100.0 * s, 26.0 * s, 4000.0)
    cr.fill()
    cr.set_source(core.linear(0, LINTEL_Y, 0, LINTEL_Y - 14.0 * s, [core.alpha("#ffb060", 0.2), core.alpha("#ffb060", 0.0)]))
    cr.rectangle(x0, LINTEL_Y - 14.0 * s, x - x0, 14.0 * s)
    cr.fill()


DRIP_SP = 240.0


def draw_fg(cr, cam, t, st):
    """The out-of-focus near side: the barrel (only while on screen), the eave and post, and
    water dripping off the eave in front of the lens (the gutters)."""
    with cam.view(cr, PX_FG):
        x0, y0 = cam.to_world(-200.0, -200.0, PX_FG)
        x1, y1 = cam.to_world(W + 200.0, H + 200.0, PX_FG)
        s = FG_SC
        if x0 < BARREL_X + 400.0 and t < 4.0:
            st["fg_barrel"].paint(cr)
            # the spout pours: a ragged, glinting rope of water into the barrel
            top = 1080.0 + 150.0 - 290.0 * s
            sx0, sy0 = BARREL_X - 200.0 * s * 0.12, top - 64.0 * s
            for k in range(3):
                pts = []
                for j in range(9):
                    v = j / 8.0
                    pts.append((sx0 + 8.0 * k - 6.0 + 5.0 * math.sin(t * 13.0 + j * 1.3 + k) * v,
                                sy0 + v * (top + 4.0 * s - sy0)))
                core.smooth_open(cr, pts)
                cr.set_line_width(5.0 - k)
                core.src(cr, "#cfe0f7" if k else "#ffd9a8", 0.28)
                cr.stroke()
            for k in range(6):                                 # splash where it hits the water
                a = TAU * core.hash01(k, 95) + t * 3.0
                u = (t * 2.2 + k / 6.0) % 1.0
                fx.glow(cr, sx0 + math.cos(a) * 30.0 * u, top + 2.0 * s - 40.0 * u * (1 - u), 6.0, "#d8e8ff",
                        0.35 * (1 - u))
        if y0 < LINTEL_Y + 40.0 * s and x1 > x0:
            st["fg_door"].paint(cr)
        # drips off the eave, big and soft (they fall through the frame from above it)
        k0, k1 = int(math.floor(x0 / DRIP_SP)), int(math.ceil(x1 / DRIP_SP))
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(k0, k1 + 1):
            if core.hash01(k, 90) < 0.45:
                continue
            dx = k * DRIP_SP + 80.0 * core.hash01(k, 91)
            if dx > DOOR_X - 20.0:
                continue
            per = 1.1 + 0.9 * core.hash01(k, 92)
            u = ((t + per * core.hash01(k, 93)) % per) / per
            yy = LINTEL_Y + 30.0 * s + 2200.0 * u * u
            if yy > y1 or yy + 80.0 < y0:
                continue
            cr.move_to(dx, yy)
            cr.line_to(dx, yy + 20.0 + 70.0 * u)
            cr.set_line_width(6.0)
            core.src(cr, "#b9cdea", 0.18)
            cr.stroke()


# =============================================================================================
# per-frame drawing
# =============================================================================================

def draw(cr, t, st):
    cam = camera(t)
    xd = walk_x(t)
    flick = 0.85 + 0.15 * (0.5 + 0.5 * core.noise1(t * 6.0, 4))
    light = dragon_light(xd)
    amp = stone_amp(t)
    state = "pulsing" if (amp > 0.02 or t >= T_HOLD) else "active"
    lvl = P.stone_level(state, amp, t)
    stone_cb = P.stone_hold(light, state, amp, t)

    def bag_cb(swing):
        return P.bag_hold(light, t, swing, state="open", damp=0.85)

    pose = dragon_pose(t, stone_cb, bag_cb)
    dsurf, dox, doy, rig = render_dragon(cam, t, xd, pose, light)
    gy_s = cam.to_screen(xd, GY, PX_B)[1]
    k_lamp = lamp_k(xd)

    # ---------------- far to near: sky, castle, roofs, the far side, the wet street
    with cam.view(cr, PX_SKY):
        st["sky"].paint(cr)
    with cam.view(cr, PX_CASTLE):
        st["castle"].paint(cr)
    with cam.view(cr, PX_ROOFS):
        st["roofs"].paint(cr)
    with cam.view(cr, PX_HOUSES):
        st["houses"].paint(cr)
    for key, p in (("band_a1", PX_A1), ("band_a2", PX_A2), ("band_b", PX_B), ("band_c", PX_C)):
        with cam.view(cr, p):
            st[key].paint(cr)
    with cam.view(cr, PX_HOUSES):
        st["house_refl"].paint(cr, alpha=0.9 * flick)
    with cam.view(cr, PX_B):
        st["post_refl"].paint(cr, alpha=flick)
        st["glints"].paint(cr, alpha=0.75 + 0.25 * flick)
        for i, pd in enumerate(PUDDLES_B):
            env.puddle_ripples(cr, t, *pd, n=4, seed=60 + i, alpha=0.3)
    with cam.view(cr, PX_C):
        for i, pd in enumerate(PUDDLES_C):
            env.puddle_ripples(cr, t, *pd, n=6, seed=70 + i, alpha=0.3)
    draw_reflection(cr, dsurf, dox, doy, gy_s, cam.zoom)
    with cam.view(cr, 0.75):
        st["mist"].draw(cr, t)

    # the final wide: the street sinks into the night round the lamp (its light, him and the
    # loop are drawn after this and keep their brightness)
    wide = core.smoothstep(T_PULL0, T_PULL1, t)
    if wide > 0.0:
        cx, cy = cam.to_screen(xd - 40.0, GY - 300.0, PX_B)
        cr.save()
        cr.translate(cx - 1920.0, cy - 1080.0)
        cr.scale(4.0, 4.0)
        cr.set_source_surface(st["iso"], 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint_with_alpha(0.8 * wide)
        cr.restore()

    # background light (behind him): window glows, door lamps, the street lamps' halos, cones
    # of lit rain and their pools on the stones -- he will stand dark against it
    lb = st["light_bg"].begin()
    with cam.view(lb, PX_HOUSES):
        for (wx, wy, ww, wh) in st["house_windows"]:
            fx.glow(lb, wx, wy, ww * 2.4, "#ffbf5f", 0.22 * flick)
            fx.light_pool(lb, wx, HOUSE_Y + 8.0, ww * 1.6, ww * 0.25, "#ffbf5f", 0.18)
        for i, (lx, ly) in enumerate(st["house_lamps"]):
            fl = 0.85 + 0.15 * (0.5 + 0.5 * core.noise1(t * 7.0 + i * 3.1, 9))
            fx.glow(lb, lx, ly, 120.0, "#ffbf5f", 0.3 * fl)
            fx.light_pool(lb, lx, HOUSE_Y + 6.0, 90.0, 14.0, "#ffbf5f", 0.3 * fl)
    with cam.view(lb, PX_B):
        for i, r in enumerate(st["post_rigs"]):
            lamp_light(lb, r, t, flick, boost=1.0 + 0.4 * wide * (i == 1))
    st["light_bg"].composite(cr)

    draw_rain_layer(cr, cam, t, 0.62, 170, 1000.0, 16.0, 0.9, 0.15, 11)          # far rain
    draw_splashes(cr, cam, t, PX_A2, 790.0, 850.0, 26, 6.0, 0.35, 21)

    # ---------------- his plane: the lamp posts, the dragon, the stone's glow
    with cam.view(cr, PX_B):
        posts = [P.draw_lantern_post(cr, x, y, POST_SC, L_SET, t, height=POST_H, side=1, seed=s_)
                 for (x, y, s_) in POSTS]
        draw_shadows(cr, rig, xd, k_lamp)
    composite_dragon(cr, dsurf, dox, doy)
    # the lamp overhead: warm light along his upper contours (strongest on horns and head), and a
    # faint warm bounce off its pool on his lower edges -- his front stays cold
    z = cam.zoom
    head_y = cam.to_screen(xd, GY - 470.0 * SC, PX_B)[1]
    edge_light(cr, dsurf, dox, doy, 2.5 * z, 6.5 * z, "#ffb963", 0.7 * k_lamp, (head_y, gy_s, 1.0, 0.25))
    edge_light(cr, dsurf, dox, doy, 0.0, -4.0 * z, "#e0924e", 0.3 * k_lamp, (head_y, gy_s, 0.0, 1.0))
    with cam.view(cr, PX_B):
        draw_rain_on_him(cr, t, rig)
        P.stone_glow(cr, rig.hand_near.x, rig.hand_near.y, SC, lvl, t)
        if t > T_SIGH:                          # the long exhale: steam in the cold rain
            ch.dragon_smoke(cr, t, T_SIGH + 0.2, rig, dur=2.8, alpha=0.46, light_tint="#9fb8d8")
    lamps = [(p.lamp[0], p.lamp[1], 300.0, p.ground[1] + 6.0) for p in posts]
    draw_rain_layer(cr, cam, t, PX_B, 150, 1500.0, 30.0, 1.4, 0.22, 12, lamps)      # rain round him
    draw_splashes(cr, cam, t, PX_B, 850.0, 1000.0, 30, 9.0, 0.45, 22)
    draw_splashes(cr, cam, t, PX_C, 960.0, 1180.0, 22, 13.0, 0.45, 23)
    with cam.view(cr, PX_B):
        draw_step_splashes(cr, t)

    # ---------------- the stone's voice and the hold loop, then the nearest rain over all
    lc = st["light"].begin()
    with cam.view(lc, PX_B):
        P.stone_light(lc, rig.hand_near.x, rig.hand_near.y, SC, lvl)
        for r in posts:
            lamp_light(lc, r, t, flick, front=True)
    with cam.view(cr, PX_B):
        with cam.view(lc, PX_B):
            draw_hold(cr, t, lc)
    sx, sy = cam.to_screen(rig.hand_near.x, rig.hand_near.y, PX_B)
    tx = cam.to_screen(xd, GY, PX_B)[0] + TEXT_DX
    draw_text_reflection(lc, t, st["text"], tx, TEXT_Y0, gy_s, cam.zoom)
    st["text"].draw(cr, t, tx, TEXT_Y0, (sx, sy), lc)
    draw_dissolve(cr, t, cam, st["text"], tx, TEXT_Y0)
    draw_rain_layer(cr, cam, t, PX_NEAR, 26, 2300.0, 70.0, 2.4, 0.2, 13)
    draw_fg(cr, cam, t, st)
    st["rig"] = rig
    fx.post(cr, t, light=st["light"], bloom_strength=0.5, threshold=0.62, bloom_radius=2.2, wide=0.4,
            grain=0.04, vignette=0.55 + 0.15 * wide, vignette_color=(0.0, 0.01, 0.04))


# =============================================================================================
# sound: every on-screen event that makes a noise, timed exactly as the animation does it
# =============================================================================================

def _pan_at(t, wx, wy=GY, p=PX_B):
    sx = camera_base(t).to_screen(wx, wy, p)[0]
    return round(clamp((sx - W / 2) / (W / 2) * 0.8, -0.9, 0.9), 3)


def _sfx_cues():
    cues = []
    # wet footsteps on the cobbles (heel strikes from the walk integrator); the one that lands
    # in the puddle splashes
    for (tp, foot) in PLANTS:
        g = 0.5 * clamp(walk_amt(tp) + 0.25)
        pan = _pan_at(tp, walk_x(tp))
        if abs(tp - T_SPLASH) < 0.05:
            cues.append((round(tp, 3), "splash", {"gain": 0.42, "pan": pan, "size": 0.35}))
            g *= 0.6
        cues.append((round(tp, 3), "footstep_wet", {"gain": round(g, 3), "pan": pan, "size": 0.75, "who": "dragon"}))
    # the stop: the trailing foot sets down beside the other, the wet coat settles
    t_set = T_STOP - 0.2
    cues.append((round(t_set, 3), "footstep_wet", {"gain": 0.22, "pan": _pan_at(t_set, X_STOP), "size": 0.5,
                                                  "who": "dragon"}))
    cues.append((round(T_STOP - 0.05, 3), "cloth_rustle", {"gain": 0.25, "pan": _pan_at(T_STOP, X_STOP), "size": 0.5}))
    # the stone's voice writes itself in light: a shimmer as each menu line begins, a bigger one
    # as "loneliness" lands; the menu breaking into the hold loop
    for ln in PHONE_LINES[:2]:                       # (line 3's shimmer is the "loneliness" swell)
        t0 = WORDS[ln.id][0][1]
        cues.append((round(t0 - 0.06, 3), "rune_glow", {"gain": 0.22, "dur": 0.7, "pan": _pan_at(t0, walk_x(t0) + 500.0)}))
    pan_l = _pan_at(T_LONELY, walk_x(T_LONELY) + 420.0)
    cues.append((round(T_LONELY_LAND - 0.45, 3), "rune_glow", {"gain": 0.42, "dur": 1.0, "midi": 76, "pan": pan_l}))
    cues.append((round(T_LONELY_LAND, 3), "crystal_chime", {"gain": 0.3, "midi": 88, "pan": pan_l}))   # it lands
    cues.append((round(T_DISSOLVE0 + 0.15, 3), "rune_glow", {"gain": 0.25, "dur": 0.9, "midi": 88,
                                                            "pan": _pan_at(T_DISSOLVE0, walk_x(T_DISSOLVE0) + 400.0)}))
    # the shiver: wet wool and leather
    cues.append((round(T_SHIVER + 0.02, 3), "cloth_rustle", {"gain": 0.3, "pan": _pan_at(T_SHIVER, walk_x(T_SHIVER)),
                                                            "size": 0.4, "dur": 0.45}))
    # the hourglass flips over every two loops
    for tf in hourglass_flips():
        hx, hy = note_world(tf, 4)
        cues.append((round(tf + 0.05, 3), "hourglass_flip", {"gain": 0.4, "pan": _pan_at(tf, hx, hy)}))
    # after his line: the long exhale, and its breath of steam in the cold
    cues.append((round(T_SIGH + 0.05, 3), "sigh", {"gain": 0.4, "pan": _pan_at(T_SIGH, X_STOP)}))
    cues.append((round(T_SIGH + 0.3, 3), "smoke_puff", {"gain": 0.12, "pan": _pan_at(T_SIGH, X_STOP + 60.0)}))
    return sorted(cues, key=lambda c: c[0])


SFX_CUES = _sfx_cues()
