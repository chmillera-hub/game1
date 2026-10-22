"""s3_stone.py -- Scene 3: THE SPEAKING STONE.   Emotion: lonely, drifting.

THE IDEA. He calls the one number left -- and the city answers with a menu. Loneliness is just
another option between billing and new accounts, and the answer to it is "please hold": four
tinny notes going round and round an hourglass. He walks home through the rain lit by the cold
stone at his ear, past warm windows and warm lamps that light the street but not him, and stops
in a pool of lamplight that surrounds him without reaching him: a cold figure in a warm pool,
still on hold. (The image rhymes with S8, where one warm lamp shelters a whole crowded bench.)

FOUR SHOTS, hard cuts on the story's turns (times are the current timeline's; the code derives
every one from timeline.json lines, beats and word times):

 A  0.00-6.45  "the menu" -- ESTABLISHING CRANE, then a side-on tracking wide.
    Opens high in the rain on the far side's gables (a few warm attic windows: lives behind shut
    shutters) and the castle on its hill against a faint break in the cloud; the crane comes down
    (-0.55 -> 2.0, eased) past the roofs onto the wet street, where he is already walking out of
    a lamp's pool (warm on his horns) toward the next. Then it trucks with him at walking pace
    (his head at screen x ~646, look room ahead), the world sliding past in seven parallax planes
    (sky .05, castle .12, roofs .3, far side .5, street strips .56/.74/1.0/1.35).
    s3_l1 (1.0) / s3_l2 (3.6): a spark leaves the stone and each word is WRITTEN in light beside
    his head, syllable-timed to the voice (illuminated uncial, glowing cold cyan, an enlarged
    initial F, a dark halo for legibility, a scribe's swash after each line, cold streaks of its
    reflection down the wet cobbles); the older line cools and dims. Acting: heard it all before
    -- heavy lids, eyes ahead and down; a weary glance up into the rain (2.6), a heavy blink
    after "press two" (5.4), a shiver in the cold (5.9: shoulders up, head trembles).
 B  6.45-13.47 "for loneliness... please hold" -- MEDIUM, tracking beside him at eye level
    (zoom 2.2 -> 2.34, a breath of push as the hold begins); the far side melts to soft shapes
    and warm bokeh. Cut in on the third option: the two options already heard sit small and dim
    above; the third is written big. "loneliness" (6.77) lands at 7.09 with a pop, a flash and a
    burst of cold sparks: HOPE -- his eyes lift to the word, wide, no blink, brows up, wings lift a
    little, his walk falters. "please hold" (8.06): the eyes drift down, a slow blink, the head
    drops, the hunch deepens, the wings sag. 9.3: the menu breaks into motes that stream into the
    HOLD EMBLEM ahead of his face: a small hourglass (it runs out every two loops and flips as
    the loop comes round again: 12.45 / 15.45 / 18.45) under a banderole lettered "On hold", and
    the music box's four notes riding round it on a tilted ring of light -- one turn per loop,
    each note flaring and pinging as it comes round to the front EXACTLY as the music box plays
    it (B A F# E, e e e q. from film/audio/motif.py: the four bunch on one side of the ring and
    the long E leaves the rest of it empty before it all comes round again). From 10.0 he looks
    at it; he slows (the walk is integrated from his speed: no foot ever slides), passes under
    the lamp (its gold runs along his horns and head), and stops at 13.25.
 C  13.47-17.00 "I've been on hold my whole life" -- MEDIUM CLOSE-UP under the lamp (zoom 3.5
    -> 3.68, a slow push), his face on the left third, the emblem on the right; he has turned a
    little toward us. Cut on the thought: eyes drop to the wet stones (13.35) -> glance up at the
    hourglass (13.75) -> breath, the hunch eases (13.96) -> s3_l4 (14.3), small and tired, to
    himself: eyes on the hourglass for "I've been on hold", sliding down and away on "my whole
    life". 16.4: a long closed-mouth exhale; his breath steams in the cold and drifts forward.
    Lit like Klaus: the lamp is above and BEHIND him -- a warm rim along his horns and crown;
    everything the camera sees of his front is cold, washed cyan by the stone.
 D  17.00-20.00 s3_lantern -- THE FINAL WIDE: the camera has pulled back across the street and
    keeps rising and pulling away (zoom 0.9 -> 0.74) while the street sinks into the night round
    the lamp's pool (a radial falloff; the lamp, its cone of lit rain, its gold pool and glints,
    him and the emblem keep their light). A few warm windows across the street, none for him.
    Last image: a small cold figure in a warm pool of lamplight, the stone at his ear, the steam
    of his breath thinning away, the four notes still going round.

COLOUR / VALUE. Deep navy night and rain (the far side graded down to 5-15 % value, sunk in a
night falloff and a rain haze) against sodium-gold lamp light: halos, volumetric cones of lit
rain, gold pools with specular glints, long broken reflections on the wet street, and a few
candle-lit panes. One cold accent: the speaking stone's cyan (its glow at his ear, its light on
his face, the rune text, the notes, the hourglass). Warm light is the world's, never his: it
rims him, it never reaches his front. The subject is always the brightest, most contrasted
thing: the lamp-pool + his face in the wides, the text or the emblem + his face in the close
shots. Eye-trace: text above-right of his head in A and B; the emblem on the right in B and C;
him in the lamp's pool in D.

THE PERIOD WORLD. Half-timbered houses with jettied storeys and carved bargeboards, shuttered
shop fronts, leaded diamond-pane windows lit by candles, arched plank doors and iron door lamps,
painted hanging signs (a baker's loaf among them), the castle on its hill, cobbles, iron
lantern posts with candle flames. The "phone" is a slate rune-stone; its menu is illuminated
script; the timer is an hourglass; the hold music is a music box's tune written as medieval
mensural notes.

CRAFT. Cached layers (sky with the town's glow on the cloud base, castle hill, roofline, the far
side drawn twice so its lit windows can be chosen -- never behind the line being spoken in the
wide -- the whole wet street painted once and cut into parallax strips, reflections, pool
glints) graded in setup to a deep navy; soft depth-of-field copies of the far side for the close
shots. Per frame: the lamp posts, the dragon (drawn ONCE into an offscreen buffer that is
composited, mirrored for his reflection in the wides, and used as the mask for the lamp's warm
top-light), contact and lamp shadows, rain in three world-locked depths (drop counts fixed per
shot, streak width and length matched to each shot's magnification) turning gold inside the
lamps' halos and cones, splashes, step splashes, puddle ripples, mist, rain bursting on his
horns, a drip off his snout once he stands still, the rune text, the dissolve, the hold emblem,
the background light layer behind him and the front light layer (the stone's spill on his face),
bloom, grain, vignette. SFX_CUES come from the same walk integrator, word schedule, beat
constants and hourglass clock the picture uses.
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
NOTE_ONSET = tuple(float(HOLD_EV[k][0] - T_HOLD) for k in range(4))    # within the loop: 0 .25 .5 .75
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
T_DISSOLVE0 = max(L3.end + 0.55, T_HOLD - 0.7)   # the menu dissolves into the hold emblem
T_DISSOLVE1 = T_HOLD + 0.02

# =============================================================================================
# the walk: he drifts along the street, slows when the music box starts, stops under the lamp
# =============================================================================================
SC = 0.85                       # the dragon and everything in his depth plane (posts, puddles)
GY = 905.0                      # his ground line (world == screen at the opening frame)
X0 = 600.0                      # his world x at t = 0
STEP_T = 0.62                   # seconds per step: a tired walk
TURN_WALK, TURN_TALK = 0.40, -0.12
V0 = ch.dragon_stride(SC, 1, TURN_WALK) / (2.0 * STEP_T)
T_SLOW0 = T_HOLD + 0.2                          # the music box starts ... he slows ...
T_STOP = min(T_HOLD + 3.25, L4.start - 1.05)     # ... and stops under the lantern
T_LOOKDOWN = T_STOP + 0.1                       # thought: the eyes drop to the wet stones
T_GLANCE = L4.start - 0.55                      # glance: up at the hourglass
T_BREATH = L4.start - 0.34                      # breath
T_SIGH = L4.end + 0.15                          # the long exhale after the line (+ steam)
T_RAINLOOK = L1.end + 0.25                      # between the options: a weary glance up into the rain
T_SHIVER = 0.5 * (L2.end + L3.start) - 0.1       # ... and a shiver in the cold
SHIVER_HZ = 4.8                                 # 5 frames a cycle: a clean tremble, no aliasing

# s3_l4 is said "small and tired, to himself". The envelope is normalised per line, so his
# mutter would get a full jaw flap: compress it (talk' = k * talk ** gamma), and let the lips
# meet on the bilabials -- the b of "been", the m of "my" -- where the voice dips at those words.
L4_TALK = (0.42, 1.35)


def _lip_closures(line, words=("been", "my")):
    """Local times of the lip closures: the envelope's minimum just before each bilabial word."""
    env_ = list(line.env)
    if not env_:
        return ()
    fps = tl.fps()
    out = []
    for w, a, _b in tl.word_times(line.id):
        if re.sub(r"[^a-z]", "", w.lower()) not in words:
            continue
        k0 = max(0, int((a - 0.16 - line.start) * fps))
        k1 = min(len(env_) - 1, int((a + 0.06 - line.start) * fps))
        if k1 >= k0:
            k = min(range(k0, k1 + 1), key=lambda i: env_[i])
            out.append(line.start + k / fps)
    return tuple(out)


L4_CLOSE = _lip_closures(L4)


def man_talk(t):
    """His mouth: the voice's envelope, muttered, with the lips meeting on the bilabials."""
    a = tl.talk(SCENE, t, "MAN")
    if a <= 0.0:
        return 0.0
    if L4.start - 0.3 <= t <= L4.end + 0.4:
        a = L4_TALK[0] * a ** L4_TALK[1]
        for tc in L4_CLOSE:
            a *= 1.0 - 0.92 * core.window(t, tc - 0.085, tc + 0.055, 0.035, 0.03)
    return a


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
# SHOTS. Four set-ups, hard cuts on the story's turns:
#   A  wide: the crane comes down out of the rain onto the street and tracks him (the menu)
#   B  medium, tracking beside him: "For loneliness... please hold." -> the hold loop; he slows
#      and stops under the lamp
#   C  medium close-up under the lamp: thought, glance, breath, "I've been on hold my whole life."
#   D  the final wide: the crane rises away and leaves him small in the lamp's pool
# =============================================================================================
T_CUT1 = L3.start - 0.15                        # cut in on the third option
T_CUT2 = T_STOP + 0.22                          # cut in when he has stopped
T_CUT3 = max(T_LANTERN, L4.end + 0.6)           # s3_lantern: cut wide


def shot_at(t):
    if t < T_CUT1:
        return "A"
    if t < T_CUT2:
        return "B"
    if t < T_CUT3:
        return "C"
    return "D"


HEAD_DX, HEAD_DY = 26.0, -373.0      # his head centre relative to his anchor (scale 0.85, hunched)


def _cam_put(wx, wy, sx, sy, zoom):
    """The camera that shows world point (wx, wy) at screen (sx, sy) with this zoom."""
    return core.Camera(wx - (sx - W / 2) / zoom, wy - (sy - H / 2) / zoom, zoom)


# A -- the crane comes down out of the rain and the roofs, onto the street, already tracking him
CAM_LAG = 0.3
SX_A, SY_A = 646.0, 532.0             # his head on screen while the camera tracks
CRANE_R = 730.0                       # how high the crane starts (screen px at his plane)
T_CRANE = (-0.55, 2.0)


def crane_a(t):
    return CRANE_R * (1.0 - core.inout_sine(ramp(t, T_CRANE[0], T_CRANE[1])))


def zoom_a(t):
    return lerp(1.0, 1.05, core.inout_sine(ramp(t, T_CRANE[1] - 0.4, T_CUT1)))


def cam_a(t):
    wx = walk_x(t - CAM_LAG) + V0 * CAM_LAG + HEAD_DX
    return _cam_put(wx, GY + HEAD_DY, SX_A, SY_A + crane_a(t), zoom_a(t))


# B -- medium, side-on, tracking beside him (eye line at his eyes): the third option, the hold
LAG_B = 0.38
SX_B, SY_B = 560.0, 468.0


def zoom_b(t):
    z = lerp(2.2, 2.34, core.inout_sine(ramp(t, T_CUT1, T_PLEASE + 0.9)))
    return z * lerp(1.0, 1.035, core.inout_sine(ramp(t, T_HOLD, T_CUT2)))


def cam_b(t):
    wx = walk_x(t - LAG_B) + V0 * LAG_B + HEAD_DX
    return _cam_put(wx, GY + HEAD_DY, SX_B, SY_B, zoom_b(t))


# C -- close shot under the lamp, a NEW set-up (not a punch-in on B's axis): the camera has come
# round toward his face (TURN_C swings him ~22 deg toward us) and in to 1.7x B's size; his face
# on the left third, the hold emblem on the right, a little above his eye line
SX_C, SY_C = 700.0, 470.0
FACE_DX, FACE_DY = 50.0, -350.0        # his face (between the eyes and the mouth) from his anchor, turned


def zoom_c(t):
    return lerp(4.05, 4.25, core.inout_sine(ramp(t, T_CUT2, T_CUT3)))


def cam_c(t):
    return _cam_put(X_STOP + FACE_DX, GY + FACE_DY, SX_C, SY_C, zoom_c(t))


# D -- the crane rises and pulls away: small, cold, in the warm pool, still on hold
D_KEYS = ((790.0, 812.0, 0.9), (800.0, 905.0, 0.74))


def cam_d(t):
    u = core.inout_sine(ramp(t, T_CUT3, DUR + 0.6))
    (sx0, sy0, z0), (sx1, sy1, z1) = D_KEYS
    return _cam_put(X_STOP, GY, lerp(sx0, sx1, u), lerp(sy0, sy1, u), z0 * (z1 / z0) ** u)


def camera_base(t):
    s = shot_at(t)
    return cam_a(t) if s == "A" else cam_b(t) if s == "B" else cam_c(t) if s == "C" else cam_d(t)


def camera(t):
    c = camera_base(t)
    return c.drift(t, amp=2.2 / c.zoom ** 0.5, freq=0.11, seed=3)


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
    for k in range(-1, int(DUR * 10) + 1):
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
BAG_EXPOSURE = 0.52


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
# the rune text: per-shot layouts (screen space), kept clear of every bright thing behind it
# =============================================================================================
FONT_INI = P.FONTS.sign            # the illuminated initial: Uncial Antiqua (the Book of Kells' hand)
INI_SIZE = 69.0
FONT = P.FONTS.text                # the words: IM FELL English -- a period book face that reads at a
FS = 52.0                          # glance (uncial t/g/w read as c/3/ɯ, and these lines have no captions)
LH = 64.0                          # line spacing
TEXT_T = (L1.start - 0.4, T_DISSOLVE1 + 0.3)
TA_DX, TA_DY = 146.0, -166.0       # shot A: the first baseline relative to his head on screen
TB_DX = 168.0                      # shot B: the text block's left edge relative to his head
TB_Y3, TB_S3 = -126.0, 1.24        # shot B: the third option, big, above his eye line
TB_Y1, TB_S1, TB_A1 = -262.0, 0.7, 0.62   # shot B: the two options already heard, small and dim


def text_layout(t):
    """[(ox, oy, scale, alpha) or None] per menu line, in screen px, for the shot at t."""
    s = shot_at(t)
    if s == "A":
        hx, hy = SX_A, SY_A + crane_a(t)
        return [(hx + TA_DX, hy + TA_DY + k * LH, 1.0, 1.0) for k in range(3)]
    if s == "B":
        hx, hy = SX_B, SY_B
        old = [(hx + TB_DX, hy + TB_Y1 + k * LH * TB_S1, TB_S1, TB_A1) for k in range(2)]
        return old + [(hx + TB_DX, hy + TB_Y3, TB_S3, 1.0)]
    return [None, None, None]


def _text_boxes(t):
    """Screen rect of the menu line being spoken at t (the one at full strength: lit windows are
    kept out from behind it; the older, dimmed lines may pass in front of a lit pane)."""
    k = -1
    for li, ln in enumerate(PHONE_LINES):
        if t >= ln.start - 0.4:
            k = li
    if k < 0:
        return []
    lay = text_layout(t)[k]
    if lay is None:
        return []
    ox, oy, s, _a = lay
    return [(ox - 50.0, oy - 60.0 * s, 980.0 * s + 60.0, 80.0 * s)]


# =============================================================================================
# set painting (static: cached in setup)
# =============================================================================================
KIND = "rain_night"
PAL = env.palette(KIND)
NIGHT = "#03060f"
NAVY = "#050b1c"


def _grade(surf, gain=(1.0, 1.0, 1.0), gamma=1.0, lift=(0.0, 0.0, 0.0)):
    """Grade a cached layer in place (setup only): c' = lift + c ** gamma * gain, on the
    un-premultiplied colour, so the night is deep navy, not grey murk. RGB tuples."""
    surf.flush()
    w, h, stride = surf.get_width(), surf.get_height(), surf.get_stride()
    a = np.ndarray((h, stride // 4, 4), dtype=np.uint8, buffer=surf.get_data())[:, :w, :]
    px = a.astype(np.float32) / 255.0
    al = px[..., 3:4]
    c = np.where(al > 1e-4, px[..., :3] / np.maximum(al, 1e-4), 0.0)       # B G R
    g = np.array(gain[::-1], np.float32)
    lf = np.array(lift[::-1], np.float32)
    c = np.clip(lf + np.power(np.clip(c, 0.0, 1.0), gamma) * g, 0.0, 1.0) * al
    a[..., :3] = (c * 255.0 + 0.5).astype(np.uint8)
    surf.mark_dirty()


class SoftCopy:
    """A depth-of-field copy of a cached layer (same placement, extra blur): the far side of
    the street for the close shots."""

    def __init__(self, layer, radius, res=0.5):
        self.x, self.y, self.res = layer.x, layer.y, layer.res * res
        src = layer.surface
        if res != 1.0:
            sw, sh = max(1, int(src.get_width() * res)), max(1, int(src.get_height() * res))
            small = core.new_surface(sw, sh)
            c = cairo.Context(small)
            c.scale(res, res)
            c.set_source_surface(src, 0, 0)
            c.get_source().set_filter(cairo.FILTER_GOOD)
            c.paint()
            small.flush()
            src = small
        self.surface = fx.blur_surface(src, radius * self.res)

    def paint(self, cr, alpha=1.0):
        cr.save()
        cr.translate(self.x, self.y)
        cr.scale(1.0 / self.res, 1.0 / self.res)
        cr.set_source_surface(self.surface, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.rectangle(0, 0, self.surface.get_width(), self.surface.get_height())
        if alpha >= 0.999:
            cr.fill()
        else:
            cr.clip()
            cr.paint_with_alpha(alpha)
        cr.restore()


SKY_GLOW = [0.0, 0.0]                  # world (sky plane) of the cloud-break behind the castle (setup)


def _draw_sky(cr, rect):
    """The overcast lid of rain cloud, its underside faintly lit by the sleeping town: lighter low
    down behind the roofs (so the roofline, the chimneys and the castle stand dark against it),
    and a pale thinning of the cloud behind the castle on its hill."""
    x, y, w, h = rect
    env.draw_sky(cr, x, y, w, h, kind=KIND, horizon=470.0, seed=5)
    cr.rectangle(x, y, w, h)
    cr.set_source(core.linear(0, y, 0, 520.0, [(0.0, core.alpha(NIGHT, 0.55)), (0.45, core.alpha(NIGHT, 0.2)),
                                              (1.0, core.alpha(NIGHT, 0.0))]))
    cr.fill()
    cr.rectangle(x, y, w, h)
    cr.set_source(core.linear(0, 120.0, 0, 560.0, [(0.0, core.alpha("#3a4c74", 0.0)), (0.55, core.alpha("#3a4c74", 0.32)),
                                                  (1.0, core.alpha("#46587e", 0.42))]))
    cr.fill()
    gx, gy = SKY_GLOW
    cr.save()
    cr.translate(gx, gy)
    cr.scale(1.0, 0.55)
    cr.set_source(core.radial(0.0, 0.0, 520.0, [(0.0, core.alpha("#6f84ad", 0.5)), (0.35, core.alpha("#55688f", 0.3)),
                                               (1.0, core.alpha("#3a4c74", 0.0))]))
    cr.arc(0.0, 0.0, 520.0, 0.0, TAU)
    cr.fill()
    cr.restore()


# the castle on its hill above the roofs: placed where the crane's opening frame finds it
CASTLE_SC = 0.4


def _draw_castle(cr, rect, cx, cy):
    x, y, w, h = rect
    env.draw_hills(cr, x, w, cy + 110.0, kind=KIND, layers=2, height=(30.0, 90.0), seed=8, trees=True,
                   fields=False, bottom=y + h)
    env.draw_castle_hill(cr, cx, cy, CASTLE_SC, kind=KIND, hill_w=900, hill_h=420, seed=2, windows=7, road=False)
    env.draw_haze(cr, x, cy - 260.0, w, y + h - cy + 260.0, PAL["haze"], 0.0, 0.55)


def _draw_roofs(cr, rect):
    x, y, w, h = rect
    env.draw_roofline(cr, x, x + w, 600.0, 0.24, KIND, seed=4, lit=0.2, haze=0.3, spire=False)
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
    """Does a point of the houses' plane pass behind the rune text while it is up in the wide
    (shot A: the far side is sharp there; in the close shots it is a soft blur behind the dark
    halo of the letters)?"""
    for k in range(int(TEXT_T[0] * 10), int(T_CUT1 * 10) + 1):
        tt = k / 10.0
        sx, sy = camera_base(tt).to_screen(px[0], px[1], PX_HOUSES)
        for (bx, by, bw, bh) in _text_boxes(tt):
            if bx - 40 <= sx <= bx + bw + 40 and by - 40 <= sy <= by + bh + 40:
                return True
    return False


def _draw_houses(cr, rect, out):
    """The far side of the street, built twice (dark / every window lit) so the lit windows can
    be chosen: none may ever pass behind the floating text."""
    x, y, w, h = rect
    rigs = _houses_rows(cr, rect, 0.0)
    # env.draw_house reports its windows through the full CTM (device px of this cached layer),
    # not in world coordinates: map them back (scene-local workaround for the library bug)
    inv = cr.get_matrix()
    inv.invert()
    for r in rigs:
        r.windows = [(inv.transform_point(*c), ww, wh, wl) for (c, ww, wh, wl) in r.windows]
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
            if core.hash01(hi * 17 + wi, 64) < (0.5 if ground_floor else 0.55 if attic else 0.4):
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
                              [core.alpha(NAVY, 0.6), core.alpha(NAVY, 0.44), core.alpha(NAVY, 0.28)]))
    cr.paint()
    cr.restore()
    for (wx, wy, ww, wh, arched) in chosen:                  # the chosen panes: candlelight
        cr.save()
        _window_path(cr, wx, wy, ww + 1.0, wh + 1.0, arched)
        cr.clip()
        cr.set_source_surface(lit_s, x, y)
        cr.paint_with_alpha(0.9)
        cr.restore()
    env.draw_haze(cr, x, y, w, HOUSE_Y - y + 10.0, PAL["haze"], 0.06, 0.04)
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
        cr.set_source(core.linear(0, HOUSE_Y, 0, 1150.0, [core.alpha(NIGHT, 0.18), core.alpha(NIGHT, 0.55)]))
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

# grading of the cached planes (gain, gamma): deep navy night, darker up high and far away
GRADE = {"sky": ((0.86, 0.95, 1.18), 1.0), "castle": ((0.72, 0.82, 1.05), 1.1), "roofs": ((0.72, 0.82, 1.08), 1.12),
         "houses": ((0.78, 0.86, 1.08), 1.16), "band": ((0.8, 0.88, 1.06), 1.1)}


def setup():
    st = {"light_bg": fx.LightLayer(), "light": fx.LightLayer()}
    c0 = cam_a(0.0)
    cxw, cyw = c0.to_world(1490.0, 250.0, PX_CASTLE)
    SKY_GLOW[:] = c0.to_world(1490.0, 210.0, PX_SKY)
    st["sky"] = _layer(_draw_sky, PX_SKY, blur=3.0, opaque=True, margin=200.0)
    st["castle"] = _layer(lambda cr, r: _draw_castle(cr, r, cxw, cyw), PX_CASTLE, blur=2.2)
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
    for key in ("sky", "castle", "roofs", "houses"):
        gain, gamma = GRADE[key]
        _grade(st[key].surface, gain, gamma)
    for key in ("band_a1", "band_a2", "band_b", "band_c"):
        gain, gamma = GRADE["band"]
        _grade(st[key].surface, gain, gamma)
    # depth of field for the close shots: the far side melts into soft shapes and warm bokeh
    st["houses_b"] = SoftCopy(st["houses"], 2.2, res=0.5)
    st["houses_c"] = SoftCopy(st["houses"], 5.0, res=0.5)
    st["bands_c"] = [SoftCopy(st[k], 4.0, res=0.5) for k in ("band_a1", "band_a2")]
    st["post_refl"] = _layer(lambda cr, r: env.draw_wet_reflections(cr, plights, stretch=0.62, width=1.6, alpha=1.35),
                             PX_B, ys=(POST_Y - 10.0, 1400.0))
    pools = [(r.lamp[0], r.ground[1] + 6.0) for r in st["post_rigs"]]
    st["glints"] = _layer(lambda cr, r: _pool_glints(cr, pools), PX_B, ys=(POST_Y - 80.0, 1100.0))
    st["mist"] = env.Mist(-400.0, HOUSE_Y - 140.0, 7000.0, 220.0, PAL["haze"], 0.14, seed=3, speed=10.0)
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
    return st


# =============================================================================================
# the dragon's acting
# =============================================================================================

E_RAISED = B.expr("raised")
E_SAD = B.expr("sad")
E_SAD_HEAVY = E_SAD.with_(lid=0.62, lid_bot=0.3)   # under the lamp: too tired to lift his lids
E_SIGH = B.expr("sigh", open=0.0)          # the exhale, mouth shut
TURN_C = -0.62                             # shot C: the camera has come round toward his face


def _k(t, keys, ease="inout_sine"):
    return core.track(t, keys, ease)


def dragon_pose(t, stone_cb, bag_cb):
    walk = walk_amt(t)
    ph = walk_phase(t)
    # eyes: ahead and down while he walks; up to "loneliness"; down at "please hold"; a look at
    # the hold loop; down (thought) -> up at the hourglass (glance: the eyes lead, then settle a
    # little as the head comes up after them) -> the line -> down and away
    look = _k(t, [(0.0, (0.35, 0.3)), (T_RAINLOOK, (0.35, 0.3)), (T_RAINLOOK + 0.2, (0.2, -0.8)),
                  (T_RAINLOOK + 0.75, (0.25, -0.75)), (T_RAINLOOK + 1.05, (0.35, 0.3)),
                  (T_LONELY - 0.12, (0.35, 0.3)), (T_LONELY + 0.12, (0.75, -0.5)),
                  (T_PLEASE - 0.05, (0.7, -0.4)), (T_PLEASE + 0.35, (0.25, 0.55)),
                  (T_HOLD - 0.3, (0.3, 0.45)), (T_HOLD + 0.1, (0.8, -0.2)), (T_HOLD + 1.9, (0.75, -0.15)),
                  (T_HOLD + 2.4, (0.3, 0.5)), (T_LOOKDOWN + 0.3, (0.2, 0.75)), (T_GLANCE - 0.05, (0.2, 0.75)),
                  (T_GLANCE + 0.2, (0.85, -0.27)), (T_GLANCE + 0.6, (0.82, -0.13)), (L4.start + 0.9, (0.8, -0.1)),
                  (L4.start + 1.3, (0.2, 0.55)), (L4.end + 0.6, (0.1, 0.7))])
    # the head follows the eyes 0.1-0.2 s later (keys strictly in time order: core.track needs it)
    nod = _k(t, [(0.0, -0.1), (T_RAINLOOK + 0.1, -0.1), (T_RAINLOOK + 0.4, 0.12), (T_RAINLOOK + 0.8, 0.1),
                 (T_RAINLOOK + 1.2, -0.1), (T_LONELY, -0.1), (T_LONELY + 0.35, 0.08), (T_PLEASE + 0.1, 0.05),
                 (T_PLEASE + 0.7, -0.24), (T_HOLD + 0.1, -0.1), (T_HOLD + 0.6, -0.02), (T_STOP - 0.4, -0.22),
                 (T_LOOKDOWN + 0.35, -0.32), (T_GLANCE + 0.1, -0.31), (T_GLANCE + 0.45, -0.04),
                 (L4.start + 1.1, -0.07), (L4.start + 1.6, -0.22), (T_SIGH + 0.3, -0.3), (DUR, -0.34)])
    head_turn = _k(t, [(0.0, 0.0), (T_LONELY, 0.0), (T_LONELY + 0.3, 0.12), (T_PLEASE + 0.5, 0.0),
                       (T_GLANCE, -0.05), (T_GLANCE + 0.3, 0.08), (L4.start + 1.4, -0.12), (DUR, -0.15)])
    hunch = _k(t, [(0.0, 0.55), (T_PLEASE + 0.2, 0.55), (T_PLEASE + 0.9, 0.66), (T_STOP, 0.68),
                   (T_BREATH, 0.66), (T_BREATH + 0.3, 0.5), (L4.end, 0.56), (T_SIGH + 0.8, 0.8), (DUR, 0.82)])
    # the shiver: the shoulders jerk up into the scarf, tremble (4.8 Hz, dying away) and settle;
    # the wings clamp and quiver with them; the head only rides along
    shiver = core.window(t, T_SHIVER, T_SHIVER + 0.8, 0.07, 0.45)
    u_sh = t - T_SHIVER
    trem = math.sin(TAU * SHIVER_HZ * u_sh) * math.exp(-u_sh / 0.32) * clamp(u_sh / 0.06) if u_sh > 0 else 0.0
    hunch += 0.2 * shiver + 0.07 * trem
    # a slight wistful tilt as he looks up at the hourglass and says it
    tilt = 0.012 * trem + 0.07 * core.window(t, T_GLANCE + 0.25, L4.start + 1.5, 0.6, 0.7)
    # hope at "loneliness" (brows up), deflation at "please hold"; sadder through the hold; under
    # the lamp his lids get heavy (the glance up stays half-lidded); after the line a closed-mouth
    # exhale (the mouth moves only when he speaks)
    if t < T_PLEASE + 0.1:
        mood2, mix = E_RAISED, 0.5 * core.window(t, T_LONELY - 0.05, T_PLEASE + 0.1, 0.25, 0.25)
    else:
        sad = _k(t, [(T_PLEASE + 0.1, 0.0), (T_PLEASE + 0.8, 0.55), (T_HOLD + 1.0, 0.5),
                     (T_STOP, 0.6), (L4.start, 0.62), (L4.end, 0.62)])
        sig = 0.5 * core.window(t, T_SIGH, DUR + 5.0, 0.7, 0.1) - 0.15 * ramp(t, T_SIGH + 1.4, T_SIGH + 2.6, "inout_sine")
        mix = min(1.0, sad + sig)
        heavy = core.smoothstep(T_STOP - 0.6, T_LOOKDOWN + 0.3, t)
        e_sad = E_SAD.blend(E_SAD_HEAVY, heavy) if heavy > 0.0 else E_SAD
        mood2 = e_sad.blend(E_SIGH, sig / max(1e-6, sad + sig)) if sig > 0 else e_sad
    blink = B.auto_blink(t, 2)
    blink = max(blink, core.window(t, T_PLEASE + 0.18, T_PLEASE + 0.72, 0.16, 0.24))      # the slow blink
    blink = max(blink, 0.85 * core.window(t, L2.end + 0.05, L2.end + 0.5, 0.15, 0.2))      # heard it all
    if T_LONELY - 0.3 < t < T_PLEASE:                                                     # hope: eyes wide
        blink = 0.0
    # wings held tight (the rig's most compact fold is its lowest droop): a little lift of hope
    # at "loneliness", a quiver in the shiver
    wings = _k(t, [(0.0, -1.0), (T_LONELY, -1.0), (T_LONELY + 0.3, -0.8), (T_PLEASE + 0.5, -1.0)])
    wings = min(-0.75, wings + 0.12 * abs(trem))
    swing = 0.11 * math.sin(ph * TAU) * walk + 0.06 * B.wobble(t, T_STOP, 1.4, 1.2)
    turn = _turn(t) + (TURN_C if shot_at(t) == "C" else 0.0)
    return ch.DragonPose(facing=1, turn=turn, walk=walk, phase=ph, lean=0.05 * walk, hunch=hunch,
                         head_turn=head_turn, head_nod=nod - 0.12 * shiver, head_tilt=tilt, look=look,
                         mood="tired", mood2=mood2,
                         mood_mix=mix, talk=man_talk(t), blink=blink,
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


class RuneText:
    """The three menu lines as illuminated uncial script: an enlarged glowing initial, then each
    word written on by a point of light (a left-to-right wipe with a spark at the nib) on the
    word's own syllable-timed onset. Older lines cool and dim; "loneliness" lands with a pulse.
    Laid out per shot by text_layout() (screen space: origin, scale, alpha per line)."""

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
                    adv = core.measure(cr, ini, INI_SIZE, FONT_INI)[0]
                    toks.append(dict(s=ini, x=x - 4.0, size=INI_SIZE, t0=a - 0.06, t1=a + 0.12, kind="initial",
                                     font=FONT_INI))
                    x += adv - 4.0
                    adv = core.measure(cr, rest, FS, FONT)[0]
                    toks.append(dict(s=rest, x=x, size=FS, t0=a + 0.06, t1=b, kind="word", font=FONT))
                    x += adv
                else:
                    lonely = core_w.lower().startswith("lonel")
                    if lonely:
                        x += 6.0                                  # room for its pulse
                    adv = core.measure(cr, core_w, FS, FONT)[0] * (1.06 if lonely else 1.0)
                    toks.append(dict(s=core_w, x=x, size=FS, t0=a, t1=b, kind="lonely" if lonely else "word",
                                     font=FONT))
                    x += adv
                if dots:                                          # the ellipsis: the long wait
                    nxt = WORDS[ln.id][wi + 1][1] if wi + 1 < len(WORDS[ln.id]) else b + 0.6
                    gap = max(0.3, nxt - b)
                    dw = core.measure(cr, ".", FS, FONT)[0]
                    for k in range(3):
                        td = b + (k + 0.6) * gap / 3.6
                        toks.append(dict(s=".", x=x + 2.0 + k * (dw + 3.0), size=FS, t0=td, t1=td + 0.08, kind="dot",
                                         font=FONT))
                    x += 3 * (dw + 3.0) + 4.0
                x += core.measure(cr, " ", FS, FONT)[0] * 1.15
            last = [tk for tk in toks if tk["kind"] in ("word", "lonely")][-1]
            end_x = last["x"] + core.measure(cr, last["s"], last["size"], last["font"])[0] * (1.06 if last["kind"] == "lonely" else 1.0)
            for tk in toks:
                tk["w"] = core.measure(cr, tk["s"], tk["size"], tk["font"])[0]
            self.lines.append(dict(toks=toks, start=ln.start, end=ln.end, width=x, end_x=end_x,
                                   t_end=WORDS[ln.id][-1][2]))

    def draw(self, cr, t, layout, stone_xy, front):
        if t < TEXT_T[0] or t > TEXT_T[1]:
            return
        fade_all = 1.0 - core.smoothstep(T_DISSOLVE0, T_DISSOLVE1 - 0.15, t)
        for li, line in enumerate(self.lines):
            lay = layout[li]
            if lay is None or t < line["toks"][0]["t0"] - 0.3:
                continue
            ox, oy, s, la = lay
            nxt = self.lines[li + 1]["toks"][0]["t0"] if li + 1 < len(self.lines) else 1e9
            cool = core.smoothstep(nxt - 0.1, nxt + 0.5, t)        # an older line cools and dims
            line_a = (1.0 - 0.45 * cool) * fade_all * la
            if line_a <= 0.01:
                continue
            by = 2.0 * math.sin(t * 1.3 + li * 1.7)
            bx = 3.0 * math.sin(t * 0.9 + li)
            sxy = None
            if stone_xy is not None:
                sxy = ((stone_xy[0] - ox) / s, (stone_xy[1] - oy) / s)
            for c in (cr, front):
                c.save()
                c.translate(ox, oy)
                c.scale(s, s)
            try:
                for tok in line["toks"]:
                    self._token(cr, t, tok, bx, by, line_a, cool, sxy, front)
                self._filler(cr, t, line, bx, by, line_a)
            finally:
                cr.restore()
                front.restore()

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
        dur = clamp((tok["t1"] - t0) * 0.85, 0.1, 0.32) if kind != "dot" else 0.12   # == T_LONELY_LAND
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
        size = tok["size"]
        scale = 1.0
        glow_a = (0.75 + 0.6 * hot) * (1.0 - 0.35 * cool)
        wv = tok["w"]
        if kind == "lonely":                                     # it lands with a beat: when the
            v = t - (t0 + dur)                                   # nib finishes, a pop and a flash
            if v < 0.0:
                scale = 1.06
            else:
                scale = 1.06 + 0.13 * math.exp(-v / 0.22) * math.cos(v * 11.0)
                glow_a *= 1.0 + 1.3 * math.exp(-v / 0.55)
                fx.glow(front, x + wv / 2, by - FS * 0.35, 260.0, RUNE, 0.28 * math.exp(-v / 0.6) * a)
                if v < 1.6:                                      # a few cold motes lift off the word and
                    w_ = clamp(v / 1.6)                          # drift away (a sigh of light, not glitter)
                    a2 = core.smoothstep(0.0, 0.2, v) * (1.0 - w_) ** 1.6 * a
                    for j in range(5):
                        hx = core.hash01(j, 77)
                        px = x + wv * (0.12 + 0.76 * hx) + 10.0 * math.sin(v * 1.7 + j) * w_
                        py = by - FS * (0.45 + 0.4 * core.hash01(j, 78)) - (22.0 + 26.0 * core.hash01(j, 79)) * core.out_sine(w_)
                        fx.glow(cr, px, py, 7.0, RUNE, 0.32 * a2)
                        fx.glow(cr, px, py, 2.0, RUNE_HOT, 0.55 * a2)
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
        core.glow_text(cr, tok["s"], x, by, size, tok["font"], INK_DARK, glow=INK_DARK, radius=13.0,
                       glow_alpha=0.78 * a, additive=False, alpha_=0.0)
        core.glow_text(cr, tok["s"], x, by, size, tok["font"], col, glow=RUNE, radius=9.0, glow_alpha=glow_a * a,
                       alpha_=a, passes=2 if kind in ("initial", "lonely") else 1)
        cr.restore()
        if u < 1.0:                                              # the nib's spark
            fx.glow(cr, edge, by - size * 0.3, 18.0, RUNE, 0.6 * a)
            fx.sparkle(cr, edge, by - size * 0.3, 9.0, RUNE_HOT, 0.8 * a, angle=t * 3.0)


# =============================================================================================
# THE HOLD EMBLEM: the hourglass marked "On hold", with the music box's four notes riding round
# it on a little carousel of light -- one turn per loop, each note flaring as it comes round to
# the front exactly when the music box plays it (B A F# E, e e e q.: the four notes bunch on one
# side of the ring and the long E leaves the other side empty -- the rest before it all comes
# round again). It floats ahead of his face, in his plane, so every shot sees the same thing.
# =============================================================================================
EMB_DX, EMB_UP = 232.0, 44.0         # from his head (world px at his plane)
EMB_DX_C, EMB_UP_C = 182.0, 22.0     # shot C's angle: nearer (foreshortened) and nearer his eye line
EMB_SCALE = {"A": 1.0, "B": 1.0, "C": 0.84}   # screen-size balance per shot ...
EMB_D = 1.42                         # ... and the final wide counter-scales it as the camera pulls away
RING_RX, RING_RY, RING_TILT = 56.0, 13.0, -0.07
NOTE_H = (-12.0, -6.0, 2.0, 7.0)     # each pitch rides at its own height: B high ... E low
NOTE_SIZE = 0.7
HG_SC = 0.86
T_WIND0 = T_HOLD - 0.75              # the carousel winds up from rest ...
T_HG_POP = T_DISSOLVE0 + 0.42        # ... the hourglass condenses out of the menu's motes ...
T_NOTE_POP = tuple(T_DISSOLVE0 + 0.5 + 0.07 * k for k in range(4))   # ... and the notes
T_BANNER = (T_HOLD - 0.1, T_HOLD + 0.45)


def emblem_center(t):
    """World (his plane): ahead of his face, keeping pace a moment behind him, bobbing a little."""
    c = shot_at(t) == "C"
    x = walk_x(t - 0.15) + HEAD_DX + (EMB_DX_C if c else EMB_DX)
    y = GY + HEAD_DY - (EMB_UP_C if c else EMB_UP) + 4.0 * math.sin(t * 0.8) + 2.0 * math.sin(t * 1.9 + 1.0)
    return x, y


def ring_angle(t):
    w = TAU / LOOP
    if t >= T_HOLD:
        return w * (t - T_HOLD)
    d = T_HOLD - T_WIND0
    if t <= T_WIND0:
        return -w * d / 2.0
    u = t - T_WIND0
    return -w * d / 2.0 + w * u * u / (2.0 * d)


def _ring_pt(cx, cy, a, dy=0.0):
    x, y = RING_RX * math.cos(a), RING_RY * math.sin(a) + dy
    c, s = math.cos(RING_TILT), math.sin(RING_TILT)
    return cx + x * c - y * s, cy + x * s + y * c


def note_pos(t, k):
    """(x, y, depth) of note k on the ring at t (depth +1 = front)."""
    cx, cy = emblem_center(t)
    a = math.pi / 2 + ring_angle(t) - TAU * NOTE_ONSET[k] / LOOP
    x, y = _ring_pt(cx, cy, a, NOTE_H[k])
    return x, y, math.sin(a)


def emblem_targets(t):
    """World points the dissolving menu's motes fly to: the four notes, then the hourglass."""
    out = [note_pos(t, k)[:2] for k in range(4)]
    out.append(emblem_center(t))
    return out


def _ring_track(cr, cx, cy, front_half, alpha):
    if alpha <= 0.01:
        return
    n = 40
    a0, a1 = (0.0, math.pi) if front_half else (math.pi, TAU)
    pts = [_ring_pt(cx, cy, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    core.smooth_open(cr, pts)
    cr.set_line_width(4.0)
    core.src(cr, RUNE, 0.12 * alpha)
    cr.stroke()
    core.smooth_open(cr, pts)
    cr.set_line_width(1.3)
    core.src(cr, RUNE_DIM, 0.42 * alpha)
    cr.stroke()
    cr.restore()


def _draw_note(cr, front, t, k, x, y, depth, appear):
    fl = note_flash(t, k) if t >= T_HOLD - 0.02 else 0.0
    persp = 0.84 + 0.16 * depth
    size = NOTE_SIZE * persp * (1.0 + 0.42 * fl) * (0.55 + 0.45 * core.out_back(appear))
    alpha = appear * min(1.0, 0.42 + 0.22 * (depth + 1.0) + 0.6 * fl)
    # a short comet trail along the ring behind the note
    if appear > 0.5:
        cr.save()
        cr.set_operator(cairo.OPERATOR_ADD)
        for j in range(1, 5):
            tt = t - 0.035 * j
            px, py, _d = note_pos(tt, k)
            core.circle(cr, px, py, 2.2 * persp)
            core.src(cr, RUNE, 0.12 * alpha * (1.0 - j / 5.0))
            cr.fill()
        cr.restore()
    P.draw_music_note(cr, x, y, size, t, RUNE_HOT if fl > 0.35 else RUNE, alpha, "minim" if k == 3 else "semiminim",
                      0.08 * math.sin(t * 2.0 + k), True)
    if k == 3:                                   # the long note's dot
        core.circle(cr, x + 15.0 * size, y - 2.0, 2.6 * size)
        core.src(cr, RUNE_HOT, alpha)
        cr.fill()
    if fl > 0.04:
        fx.glow(cr, x, y - 10.0, 30.0 * persp, RUNE, 0.45 * fl * appear)
        fx.glow(front, x, y - 10.0, 80.0, RUNE, 0.26 * fl * appear)
        # the ping: a thin ring of light widening off the note as it sounds
        u = 1.0 - fl
        if u < 0.7:
            cr.save()
            cr.set_operator(cairo.OPERATOR_ADD)
            cr.set_line_width(1.0)
            core.src(cr, RUNE_HOT, 0.3 * fl * appear)
            core.ellipse(cr, x, y, 7.0 + 16.0 * u, (7.0 + 16.0 * u) * 0.45)
            cr.stroke()
            cr.restore()


def _banner(cr, t, cx, cy, appear):
    """A little banderole under the hourglass, unfurling, lettered "On hold" in glowing uncial."""
    u = core.out_cubic(appear)
    if u <= 0.01:
        return
    w = 92.0 * u
    hh = 9.5
    y = cy + 45.0
    wave = 3.0
    pts_top, pts_bot = [], []
    n = 16
    for i in range(n + 1):
        v = i / n
        x = cx - w / 2 + w * v
        dy = wave * math.sin(v * TAU * 1.0 + t * 1.4)
        pts_top.append((x, y - hh + dy))
        pts_bot.append((x, y + hh + dy))
    # forked tails folding back behind each end
    lx, ly = pts_top[0][0], (pts_top[0][1] + pts_bot[0][1]) / 2
    rx, ry = pts_top[-1][0], (pts_top[-1][1] + pts_bot[-1][1]) / 2
    for (ex, ey, sg) in ((lx, ly, -1.0), (rx, ry, 1.0)):
        core.polygon(cr, [(ex, ey - hh + 2.0), (ex + sg * 14.0 * u, ey - hh + 5.0), (ex + sg * 8.0 * u, ey),
                          (ex + sg * 14.0 * u, ey + hh + 5.0), (ex, ey + hh + 2.0)])
        core.src(cr, "#0a1a2c", 0.8 * appear)
        cr.fill()
    cr.move_to(*pts_top[0])
    for p in pts_top[1:]:
        cr.line_to(*p)
    for p in reversed(pts_bot):
        cr.line_to(*p)
    cr.close_path()
    path = cr.copy_path()
    core.src(cr, "#0d2236", 0.88 * appear)
    cr.fill()
    cr.append_path(path)
    cr.set_line_width(1.2)
    core.src(cr, RUNE, 0.55 * appear)
    cr.stroke()
    if u > 0.55:
        a = clamp((u - 0.55) / 0.45)
        core.glow_text(cr, "On hold", cx, y + 5.2 + wave * math.sin(0.5 * TAU + t * 1.4), 16.0, FONT, RUNE_HOT,
                       glow=RUNE, radius=4.0, glow_alpha=0.75 * a * appear, align="center", alpha_=a * appear)


def emblem_scale(t):
    """The emblem's size about its centre: smaller in the close shot, and in the final wide
    growing against the pull-back so the hourglass and the four notes still read at the end."""
    s = shot_at(t)
    if s == "D":
        return EMB_D * D_KEYS[0][2] / max(0.4, camera_base(t).zoom)
    return EMB_SCALE[s]


def draw_emblem(cr, t, front):
    """(his plane; front = the light layer in the same view)"""
    if t < T_DISSOLVE0 + 0.3:
        return
    cx, cy = emblem_center(t)
    k = emblem_scale(t)
    for c in (cr, front):
        c.save()
        c.translate(cx, cy)
        c.scale(k, k)
        c.translate(-cx, -cy)
    try:
        _draw_emblem(cr, t, front, cx, cy)
    finally:
        cr.restore()
        front.restore()


def _draw_emblem(cr, t, front, cx, cy):
    ring_a = core.smoothstep(T_WIND0 - 0.1, T_HOLD + 0.2, t)
    notes = []
    for k in range(4):
        ap = core.smoothstep(T_NOTE_POP[k] - 0.12, T_NOTE_POP[k] + 0.18, t)
        if ap <= 0.0:
            continue
        x, y, d = note_pos(t, k)
        notes.append((d, k, x, y, ap))
    notes.sort()
    # the soft cold light of the whole thing
    fx.glow(front, cx, cy, 120.0, RUNE, 0.1 * ring_a)
    for (d, k, x, y, ap) in notes:                     # behind the hourglass
        if d < 0.0:
            _draw_note(cr, front, t, k, x, y, d, ap)
    _ring_track(cr, cx, cy, False, ring_a)
    hp = core.smoothstep(T_HG_POP - 0.12, T_HG_POP + 0.3, t)
    if hp > 0:
        fx.glow(cr, cx, cy, 46.0, RUNE, 0.18 * hp)
        P.draw_hourglass(cr, cx, cy, HG_SC * (0.6 + 0.4 * core.out_back(hp)), L_COLD, t - T_HOLD, period=HG_PERIOD,
                         flip_time=HG_FLIP, glow=hp, label=None)
    _ring_track(cr, cx, cy, True, ring_a)
    for (d, k, x, y, ap) in notes:                     # in front of it
        if d >= 0.0:
            _draw_note(cr, front, t, k, x, y, d, ap)
    _banner(cr, t, cx, cy, core.smoothstep(T_BANNER[0], T_BANNER[1], t))


_MOTES = []


def _motes(text):
    """The dissolve: each mote leaves a letter of the menu and flies into a note of the loop
    (or into the hourglass), arriving as that piece condenses."""
    if not _MOTES:
        rng = np.random.default_rng(29)
        boxes = []
        for li, line in enumerate(text.lines):
            for tok in line["toks"]:
                if tok["kind"] in ("dot",):
                    continue
                boxes.append((li, tok["x"], max(8.0, tok["w"])))
        wsum = sum(b[2] for b in boxes)
        for i in range(70):
            r = rng.random() * wsum
            for (li, bx, bw) in boxes:
                r -= bw
                if r <= 0:
                    break
            k = i % 5
            born = T_DISSOLVE0 + 0.3 * rng.random()
            land = T_NOTE_POP[k] if k < 4 else T_HG_POP
            arrive = max(born + 0.3, land - 0.05 + 0.1 * rng.random())
            _MOTES.append(dict(li=li, x=bx + bw * rng.random(), y=-FS * (0.15 + 0.5 * rng.random()), k=k,
                               born=born, arrive=arrive, lift=40.0 + 120.0 * rng.random(), size=0.7 + 0.6 * rng.random()))
    return _MOTES


def draw_dissolve(cr, t, cam, text, layout):
    if t < T_DISSOLVE0 or t > T_HOLD + 0.6:
        return
    tg = emblem_targets(t)
    for m in _motes(text):
        if t < m["born"] or t > m["arrive"] + 0.15:
            continue
        lay = layout[m["li"]]
        if lay is None:
            continue
        ox, oy, s, _a = lay
        u = clamp((t - m["born"]) / (m["arrive"] - m["born"]))
        e = core.inout_sine(u)
        sx, sy = ox + m["x"] * s, oy + m["y"] * s
        ex, ey = cam.to_screen(*tg[m["k"]], PX_B)
        cx, cy = (sx + ex) / 2, min(sy, ey) - m["lift"]
        px = (1 - e) ** 2 * sx + 2 * (1 - e) * e * cx + e * e * ex
        py = (1 - e) ** 2 * sy + 2 * (1 - e) * e * cy + e * e * ey
        a = clamp(u * 6.0) * (1.0 - clamp((t - m["arrive"]) / 0.15))
        r = m["size"] * cam.zoom ** 0.5
        fx.glow(cr, px, py, 9.0 * r, RUNE, 0.55 * a)
        fx.glow(cr, px, py, 3.0 * r, RUNE_HOT, 0.9 * a)


def hourglass_flips():
    """Local times at which the hourglass starts a flip."""
    out = []
    k = 1
    while T_HOLD + k * HG_PERIOD - HG_FLIP < DUR:
        out.append(T_HOLD + k * HG_PERIOD - HG_FLIP)
        k += 1
    return out


# =============================================================================================
# rain: world-locked drops in three depths, lit up inside the lamps' glow; per shot, the counts
# and widths are set so the rain reads the same on screen at every focal length
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


# (parallax, drops per tile at zoom 1, speed, streak length, width on screen px, alpha, seed)
RAIN_FAR = (0.62, 170, 1000.0, 16.0, 0.9, 0.15, 11)
RAIN_MID = (1.0, 150, 1500.0, 30.0, 1.4, 0.22, 12)
RAIN_NEAR = (PX_NEAR, 26, 2300.0, 70.0, 2.4, 0.2, 13)


SHOT_ZOOM = {"A": 1.0, "B": 2.25, "C": 4.15, "D": 0.82}    # nominal: drop counts are fixed per shot
CONE_K = {"A": 1.0, "B": 0.42, "C": 0.3, "D": 1.0}           # the lamps' cones of lit air, per shot


def rain_params(spec, zoom, shot, near_len_cap=None):
    """World parameters that keep a rain depth's look on screen at this zoom: the same number of
    drops in frame (counted at the shot's nominal zoom, so no drop ever re-rolls mid-shot),
    streaks thin but long (motion blur grows with the magnification)."""
    p, n, speed, length, width, alpha, seed = spec
    zp = zoom ** p
    zn = SHOT_ZOOM[shot] ** p
    n2 = int(round(n * zn * zn))
    w2 = width * zp ** 0.35 / zp
    if near_len_cap is not None:
        length = min(length, near_len_cap / zp)
    return p, n2, speed, length, w2, alpha, seed


def lamp_light(lc, rig, t, flick, front=False, boost=1.0, cone=1.0):
    """A street lamp's light in the rain: the halo, a soft cone of lit rain-air down to the
    cobbles, and the warm pool it throws on the wet stones (boost > 1: the final wide)."""
    lx, ly = rig.lamp
    gy = rig.ground[1] + 6.0
    if front:                                         # the haze of the cone in front of him
        fx.light_shaft(lc, lx, ly + 22.0, lx, gy, 50.0, 470.0, "#ffbe6e", 0.05 * flick * boost, soft=3,
                       fade_start=1.0, fade_end=0.7)
        return
    P.lantern_light(lc, rig, POST_SC, t, 1.0)
    fx.light_shaft(lc, lx, ly + 22.0, lx, gy, 46.0, 520.0, "#ffbe6e", 0.3 * flick * boost * cone, soft=4,
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
    sy0 = cam.to_screen(0.0, y0, p)[1]
    sy1 = cam.to_screen(0.0, y1, p)[1]
    if sy0 > H + 20 or sy1 < -20:
        return
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
DS_W, DS_H = 700, 780                  # covers the box at the wide shots' zooms (<= 1.12)
_DS = {}


def _dsurf(key, w, h):
    surf = _DS.get(key)
    if surf is None:
        surf = _DS[key] = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return surf


def render_dragon(cam, t, xd, pose, light, full=False):
    """Draw him ONCE into an offscreen buffer (screen pixels, integer offset): the same image is
    composited into the frame, mirrored for his reflection in the wet street, and used as the
    mask for the lamp's top-light and the pool's bounce. full=True: a frame-sized buffer (the
    close shots). Returns (surface, ox, oy, rig)."""
    z = cam.zoom
    if full:
        ox = oy = 0
        surf = _dsurf("dragon_full", W, H)
    else:
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
    sw, sh = surf.get_width(), surf.get_height()
    small = _dsurf(("edge", sw, sh), sw // 2 + 2, sh // 2 + 2)
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

def draw_rain_on_him(cr, t, rig, zoom=1.0):
    """(his plane) Pure function of t: a few drops burst on his upper contours every second, and
    every ~1.6 s a drop gathers at his snout tip, swells and falls."""
    hx, hy = rig.head
    tx, ty = rig.top
    hits = [(tx - 6.0, ty + 4.0), (hx - 30.0, hy + 2.0), (hx - 52.0, hy + 46.0), (hx - 70.0, hy + 92.0),
            (rig.hand_near.x + 6.0, rig.hand_near.y - 30.0)]
    r0 = 1.3 if zoom < 1.5 else 0.9
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
            core.circle(cr, px, py, r0)
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
            core.circle(cr, nx + 3.4, ny + 5.5 + r * 0.6, r * 0.3)
            core.src(cr, "#ffffff", 0.5)
            cr.fill()
        else:                                                 # falling
            v = (u - 0.75) / 0.25
            yy = ny + 9.0 + 900.0 * (v * per * 0.25) ** 2
            if yy < GY:
                core.ellipse(cr, nx + 4.0, yy, 1.6, 3.4)
                core.src(cr, "#cfe2fa", 0.5)
                cr.fill()


def draw_breath(cr, t, rig):
    """(his plane) The exhale after his line: his breath steams out of his nostrils in the cold
    night air, drifts forward and up, curls and thins away (a breath, not a smoker's puff)."""
    nx, ny = rig.nose
    fx.smoke(cr, t, T_SIGH + 0.06, nx + 2.0, ny + 1.0, n=10, dur=2.5, rise=44.0, drift=(36.0, 2.0), size=8.5,
             color="#cfdcec", alpha=0.62, seed=17, scale=SC, spread=0.6)
    fx.smoke(cr, t, T_SIGH + 0.18, nx - 2.0, ny + 3.0, n=6, dur=2.0, rise=30.0, drift=(22.0, 6.0), size=6.0,
             color="#dde7f3", alpha=0.45, seed=29, scale=SC, spread=0.4)


def draw_text_reflection(lc, t, text, layout, gy_s, z=1.0):
    """(screen space, the light layer) The glowing menu mirrored in the wet street: under every
    written word a soft cold streak runs down the wet cobbles from his ground line, flickering
    with the rain (the higher the line, the fainter and longer its streak)."""
    if t < TEXT_T[0] or t > TEXT_T[1]:
        return
    fade_all = 1.0 - core.smoothstep(T_DISSOLVE0, T_DISSOLVE1 - 0.15, t)
    for li, line in enumerate(text.lines):
        lay = layout[li]
        if lay is None:
            continue
        ox, _oy, s, la = lay
        nxt = text.lines[li + 1]["toks"][0]["t0"] if li + 1 < len(text.lines) else 1e9
        a = (1.0 - 0.45 * core.smoothstep(nxt - 0.1, nxt + 0.5, t)) * fade_all * la
        for k, tk in enumerate(line["toks"]):
            if tk["kind"] not in ("word", "lonely") or t < tk["t0"]:
                continue
            on = clamp((t - tk["t0"]) / 0.3)
            wv = tk["w"] * s
            xx = ox + tk["x"] * s + wv / 2
            fl = 0.65 + 0.35 * core.noise1(t * 2.5 + k * 1.9 + li * 7.0, 41)
            boost = 1.6 if tk["kind"] == "lonely" else 1.0
            y0 = gy_s + 6.0 * z
            L = (130.0 + 40.0 * (2 - li)) * z
            fx.light_shaft(lc, xx, y0, xx, y0 + L, wv * 0.55, wv * 0.75, RUNE, 0.2 * a * fl * on * boost, soft=2,
                           fade_start=1.0, fade_end=1.0)


# =============================================================================================
# per-frame drawing
# =============================================================================================

def draw(cr, t, st):
    shot = shot_at(t)
    cam = camera(t)
    z = cam.zoom
    close = shot in ("B", "C")
    xd = walk_x(t)
    flick = 0.85 + 0.15 * (0.5 + 0.5 * core.noise1(t * 6.0, 4))
    light = dragon_light(xd)
    amp = stone_amp(t)
    state = "pulsing" if (amp > 0.02 or t >= T_HOLD) else "active"
    lvl = P.stone_level(state, amp, t)
    stone_cb = P.stone_hold(light, state, amp, t)

    # the sack: soaked grey paper in the night, kept down near his face's value (the brightest
    # things on the figure stay his eyes, his face and the stone)
    bag_light = B.Light.lerp(light, L_COLD, 0.5).with_(exposure=BAG_EXPOSURE)

    def bag_cb(swing):
        return P.bag_hold(bag_light, t, swing, state="open", damp=1.0)

    pose = dragon_pose(t, stone_cb, bag_cb)
    dsurf, dox, doy, rig = render_dragon(cam, t, xd, pose, light, full=close)
    gy_s = cam.to_screen(xd, GY, PX_B)[1]
    k_lamp = lamp_k(xd)
    wide = core.smoothstep(T_CUT3, T_CUT3 + 1.2, t) if shot == "D" else 0.0

    # ---------------- far to near: sky, castle, roofs, the far side, the wet street
    with cam.view(cr, PX_SKY):
        st["sky"].paint(cr)
    with cam.view(cr, PX_CASTLE):
        st["castle"].paint(cr)
    with cam.view(cr, PX_ROOFS):
        st["roofs"].paint(cr)
    with cam.view(cr, PX_HOUSES):
        (st["houses_c"] if shot == "C" else st["houses_b"] if shot == "B" else st["houses"]).paint(cr)
    if shot == "C":
        for lay, p in zip(st["bands_c"], (PX_A1, PX_A2)):
            with cam.view(cr, p):
                lay.paint(cr)
    else:
        for key, p in (("band_a1", PX_A1), ("band_a2", PX_A2), ("band_b", PX_B), ("band_c", PX_C)):
            if shot == "B" and p > 0.8:
                continue
            with cam.view(cr, p):
                st[key].paint(cr)
    with cam.view(cr, PX_HOUSES):
        st["house_refl"].paint(cr, alpha=0.9 * flick)
    if not close:
        with cam.view(cr, PX_B):
            st["post_refl"].paint(cr, alpha=flick)
            st["glints"].paint(cr, alpha=0.75 + 0.25 * flick)
            for i, pd in enumerate(PUDDLES_B):
                env.puddle_ripples(cr, t, *pd, n=4, seed=60 + i, alpha=0.3)
        with cam.view(cr, PX_C):
            for i, pd in enumerate(PUDDLES_C):
                env.puddle_ripples(cr, t, *pd, n=6, seed=70 + i, alpha=0.3)
        draw_reflection(cr, dsurf, dox, doy, gy_s, z)
    with cam.view(cr, 0.75):
        st["mist"].draw(cr, t)

    # the final wide: the street sinks into the night round the lamp (its light, him and the
    # loop are drawn after this and keep their brightness)
    if wide > 0.0:
        cx, cy = cam.to_screen(xd - 40.0, GY - 300.0, PX_B)
        cr.save()
        cr.translate(cx - 1920.0 * z / 0.8, cy - 1080.0 * z / 0.8)
        cr.scale(4.0 * z / 0.8, 4.0 * z / 0.8)
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
            lamp_light(lb, r, t, flick, boost=1.0 + 0.4 * wide * (i == 1), cone=CONE_K[shot])
    st["light_bg"].composite(cr)

    draw_rain_layer(cr, cam, t, *rain_params(RAIN_FAR, z, shot))                                 # far rain
    draw_splashes(cr, cam, t, PX_A2, 790.0, 850.0, 26, 6.0, 0.35, 21)

    # ---------------- his plane: the lamp posts, the dragon, the stone's glow
    with cam.view(cr, PX_B):
        lp = L_SET.with_(exposure=0.5) if shot == "C" else L_SET
        posts = [P.draw_lantern_post(cr, x, y, POST_SC, lp, t, height=POST_H, side=1, seed=s_,
                                     detail=0 if close else None)
                 for (x, y, s_) in POSTS]
        if not close:
            draw_shadows(cr, rig, xd, k_lamp)
    lamps = [(p.lamp[0], p.lamp[1], 300.0, p.ground[1] + 6.0) for p in posts]
    if close:          # the close shots: the lamp's lit rain falls round and behind him, his face stays clear
        draw_rain_layer(cr, cam, t, *rain_params(RAIN_MID, z, shot), lamps)
    composite_dragon(cr, dsurf, dox, doy)
    # the lamp overhead: warm light along his upper contours (strongest on horns and head), and a
    # faint warm bounce off its pool on his lower edges -- his front stays cold
    head_y = cam.to_screen(xd, GY - 470.0 * SC, PX_B)[1]
    ez = min(z, 1.5)
    edge_light(cr, dsurf, dox, doy, 2.5 * ez, 6.5 * ez, "#ffb963", (0.55 if close else 0.7) * k_lamp,
               (head_y, gy_s, 1.0, 0.25))
    if not close:
        edge_light(cr, dsurf, dox, doy, 0.0, -4.0 * z, "#e0924e", 0.3 * k_lamp, (head_y, gy_s, 0.0, 1.0))
    with cam.view(cr, PX_B):
        draw_rain_on_him(cr, t, rig, z)
        P.stone_glow(cr, rig.hand_near.x, rig.hand_near.y, SC, lvl, t)
        if t > T_SIGH:                          # the long exhale: his breath steams in the cold
            draw_breath(cr, t, rig)
    if not close:
        draw_rain_layer(cr, cam, t, *rain_params(RAIN_MID, z, shot), lamps)                    # rain round him
        draw_splashes(cr, cam, t, PX_B, 850.0, 1000.0, 30, 9.0, 0.45, 22)
        draw_splashes(cr, cam, t, PX_C, 960.0, 1180.0, 22, 13.0, 0.45, 23)
        with cam.view(cr, PX_B):
            draw_step_splashes(cr, t)

    # ---------------- the stone's voice and the hold emblem, then the nearest rain over all
    lc = st["light"].begin()
    with cam.view(lc, PX_B):
        P.stone_light(lc, rig.hand_near.x, rig.hand_near.y, SC, lvl)
        if shot == "C":
            ex_, ey_ = rig.eyes[0]
            fx.glow(lc, 0.5 * (ex_ + rig.hand_near.x), ey_ + 8.0, 105.0, "#a6dcff", 0.13 + 0.05 * lvl)
        for r in posts:
            lamp_light(lc, r, t, flick, front=True, boost=CONE_K[shot])
    with cam.view(cr, PX_B):
        with cam.view(lc, PX_B):
            draw_emblem(cr, t, lc)
    layout = text_layout(t)
    sx, sy = cam.to_screen(rig.hand_near.x, rig.hand_near.y, PX_B)
    if shot == "A":
        draw_text_reflection(lc, t, st["text"], layout, gy_s, z)
    st["text"].draw(cr, t, layout, (sx, sy), lc)
    draw_dissolve(cr, t, cam, st["text"], layout)
    draw_rain_layer(cr, cam, t, *rain_params(RAIN_NEAR, z, shot, near_len_cap=260.0))
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
    # as "loneliness" lands; the menu breaking into the hold emblem
    for ln in PHONE_LINES[:2]:                       # (line 3's shimmer is the "loneliness" swell)
        t0 = WORDS[ln.id][0][1]
        lay = text_layout(t0)[PHONE_LINES.index(ln)]
        pan = round(clamp(((lay[0] + 300.0) - W / 2) / (W / 2) * 0.8, -0.9, 0.9), 3)
        cues.append((round(t0 - 0.06, 3), "rune_glow", {"gain": 0.22, "dur": 0.7, "pan": pan}))
    lay = text_layout(T_LONELY)[2]
    pan_l = round(clamp(((lay[0] + 330.0 * lay[2]) - W / 2) / (W / 2) * 0.8, -0.9, 0.9), 3)
    cues.append((round(T_LONELY_LAND - 0.45, 3), "rune_glow", {"gain": 0.42, "dur": 1.0, "midi": 76, "pan": pan_l}))
    cues.append((round(T_LONELY_LAND, 3), "crystal_chime", {"gain": 0.3, "midi": 88, "pan": pan_l}))   # it lands
    ex, ey = emblem_center(T_HG_POP)
    cues.append((round(T_DISSOLVE0 + 0.15, 3), "rune_glow", {"gain": 0.25, "dur": 0.9, "midi": 88,
                                                            "pan": _pan_at(T_HG_POP, ex, ey)}))
    # the shiver: wet wool and leather
    cues.append((round(T_SHIVER + 0.02, 3), "cloth_rustle", {"gain": 0.3, "pan": _pan_at(T_SHIVER, walk_x(T_SHIVER)),
                                                            "size": 0.4, "dur": 0.45}))
    # the hourglass flips over every two loops
    for tf in hourglass_flips():
        hx, hy = emblem_center(tf)
        cues.append((round(tf + 0.05, 3), "hourglass_flip", {"gain": 0.4, "pan": _pan_at(tf, hx, hy)}))
    # after his line: the long exhale, and its breath of steam in the cold
    cues.append((round(T_SIGH + 0.05, 3), "sigh", {"gain": 0.4, "pan": _pan_at(T_SIGH, X_STOP)}))
    cues.append((round(T_SIGH + 0.3, 3), "smoke_puff", {"gain": 0.12, "pan": _pan_at(T_SIGH, X_STOP + 60.0)}))
    return sorted(cues, key=lambda c: c[0])


SFX_CUES = _sfx_cues()
