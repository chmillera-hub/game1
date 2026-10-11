"""s02 -- "Close your eyes" (TIREDNESS Ep2: Lights Out).

Pitch dark on the shaft catwalk (continues s01's last frame: Curiosity's big
eyes low-left at its empty pod, Tiredness's faint eyes high-right). He gives up
and sits on the plinth of the empty pod; Curiosity hops up beside him and SHOWS
him the sense first: eyes shut, a little tremble, a teal pulse. He thinks it is
having a fit. It rolls its eyes and pulls his hood over his eyes; he peeks out
from under the rim with one eye; it pointedly shuts its eyes and pulses again.
"Oh." He lets the hood drop, it nods, and his own first ping lights the world.
Smug, he strides off down the stair... and walks face-first into a low pipe.

All timing comes from info.cue()/info.line(); nothing is hard-coded to the
audio. Shots (scene-local):
  S1  dark ....... two pairs of eyes, l01, he sits down (eyes drop)
  S2  climb ...... Curiosity hops up beside him onto its hind legs; DEMO: it shuts its
                   eyes (its light goes out), trembles, and sends out its own pulse
  S3  fit ........ tight two-shot, l02 "Uh... what are you doing? Are you okay?" (a
                   second pulse on "doing?"; it opens its eyes, flat, on "okay?")
  S4  roll ....... CU Curiosity: a very sassy eye-roll with a head toss
  S5  hood ....... two-shot CU: it yanks the hood over his eyes; annoyance, a sigh; PEEK:
                   a finger lifts the rim, one eye peeks; it shuts its eyes, pulses again
  S6  oh ......... CU on him: "Oh." (the peeking eye widens), LOOK: the eye wanders the dark
  S7  nod ........ two-shot: "So I just... close my eyes?" -- the rim drops; it nods
  S8  ping ....... wide: HIS first ping (eyes closed under the hood) reveals the catwalk;
                   a second one follows his head; he stands up proud on "Finally."
  S9  smug ....... CU "A superpower I'm actually good at." (+ a proud ping)
  S10 roll2 ...... CU Curiosity's slow eye-roll at his smugness
  S11 walk ....... tracking: confident stride, pings, down the stair -> BONK
  S12 bonk ....... CU held beat, dazed: "...Mostly good at."
  S13 giggle ..... CU Curiosity on the stair hides its smile behind a paw
"""
import math

import cairocffi as cairo

from engine import core, human, sets, fx
from engine import creatures as CR
from engine.core import (tween, seg, clamp, lerp, smoothstep, ease_in_out, ease_out, ease_in,
                         ease_out_back, state_at)

M = sets.CATWALK_MARKS
S = 0.75                                   # character scale on the catwalk
SW = 0.8                                   # sense scale (world px), shared by every ping
PLINTH_Y = 1280                            # top of the pod plinths (base caps)
T_X0 = 1240                                # Tiredness where s01 leaves him (right of the pod)
T_X = 1090                                 # ... sits here on the empty pod's plinth
T_GSEAT = PLINTH_Y + human.CRATE_H["tired"] * S      # ground y for sit_crate on the plinth
C_X0 = 750                                 # Curiosity where s01 leaves it (left of its pod, faces right)
C_XP = 935                                 # ... hops up onto the plinth here (at his left, faces right)
C_XS = 900                                 # ... and sits back on it here (from the "oh" shot on)
C_XS2 = 868                                # ... shuffling back a step when he stands up
FEET = M["feet_y"]                         # 1500
LAND = M["landing_feet_y"]                 # 1770
BONK_X = M["bonk_feet"][0]                 # -44: feet x when his face meets the pipe
PIPE = M["bonk_pipe"]                      # (-90, 1150) contact point
ST_TOP_X, ST_RUN, ST_RISE = 640, 86, 45
STEP_C = 2                                 # the stair tread Curiosity stops on (giggle)
DARK_RGB = (0.012, 0.027, 0.043)
TEAL = (0.247, 0.949, 0.878)
S01_DARK_CAM = (1010, 1105, 1.35)          # s01's last framing (lights out, two pairs of eyes)

# the hood peek (a finger lifts the rim so ONE eye shows): the rig's hood is symmetric, so
# the lifted part is a second render with the rim higher, shown through an arch-shaped window
HOOD_PEEK = 0.70                           # rim of the second render: well above the eye
try:
    _HOOD_TOP = human._dk(human.PAL["t_hoodie"], 0.1)          # outfit "sewer" hoodie
    _HOOD_DK = human.PAL["t_hoodie_dk"]
    _INK = human.PAL["ink"]
except Exception:                          # palette moved: fall back to the measured colours
    _HOOD_TOP, _HOOD_DK, _INK = "#33416f", "#252f52", "#1d1424"
# the peek hand: index finger out, placed with world-space `reach`. The arm stays in the rig's
# "mid" layer (under the head: no shoulder popping over his jaw); only the hand is drawn again
# over the head, from a front-layer copy clipped to a small disc around it
ARM_PEEK = {"ar_h": "point"}
HAND_R = 40.0                              # that disc's radius (px at s=1)
FINGER = 25.0                              # grip point -> index fingertip (px at s=1)
FINGER_ANG = -2.5                          # finger direction in the eye-line frame (up-left)
PEEK_FX = 0.72                             # fingertip: this many eye-spacings outside the eye centre


def _sleeper(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s, t, seed=seed)


def _baby(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s * 1.6, t, seed=seed, baby=True)


# same set state as the end of s01: plate wiped clean, camera swivelled to them, LED on
SET_KW = dict(sleeper_fn=_sleeper, sleeper_fns={"JOY": _baby}, sleeper_key="s02_sleepers",
              cam_face=1.0, cam_angle=0.37, plate_dust=1.0, plate_wipe=1.0)


def kf(t, keys, ease=ease_in_out):
    return tween(t, keys, ease)


def bump(t, t0, t1):
    """0 -> 1 -> 0 over [t0, t1] (sine)."""
    return math.sin(math.pi * seg(t, t0, t1))


# ---------------------------------------------------------------------------
# timing (all derived from cues)
# ---------------------------------------------------------------------------
class K:
    pass


_KC = {}


def timing(info):
    key = (info.id, tuple(sorted(info.cues.items())))
    k = _KC.get(key)
    if k is not None:
        return k
    k = K()
    c = info.cue
    L = info.line
    k.L1, k.L1e = L("s02_l01").start, L("s02_l01").end
    k.NUDGE = c("nudge")
    k.DEMO = c("demo")
    k.L2, k.L2e = L("s02_l02").start, L("s02_l02").end
    k.ROLL = c("roll")
    k.HOOD = c("hood")
    k.PEEK = c("peek")
    k.L3, k.L3e = L("s02_l03").start, L("s02_l03").end
    k.LOOK = c("look")
    k.L4, k.L4e = L("s02_l04").start, L("s02_l04").end
    k.NOD = c("nod")
    k.PING = c("ping")
    k.L5, k.L5e = L("s02_l05").start, L("s02_l05").end
    k.SMUG = c("smug")
    k.WALK = c("walk")
    k.BONK = c("bonk")
    k.L6, k.L6e = L("s02_l06").start, L("s02_l06").end
    k.END = info.dur

    def word(lid, i, default):
        try:
            if len(info.line(lid).caption.split()) > abs(i):
                return info.word_time(lid, i)
        except Exception:
            pass
        return default
    # Tiredness sits down right after l01 (a step back onto the plinth)
    k.sit0 = k.L1e + 0.12
    k.sit1 = k.sit0 + 0.85
    # Curiosity hops up onto the plinth beside him
    k.hop0 = max(k.sit1 + 0.12, k.NUDGE + 0.35)      # anticipation crouch starts
    k.hop1 = k.hop0 + 0.22                            # take-off
    k.hop2 = k.hop1 + 0.30                            # lands on its hind legs
    # DEMO: it shuts its eyes, charges up (a little tremble) and pulses
    k.dm_close = k.DEMO + 0.12                        # lids close over 0.3 s
    k.dm_charge = k.DEMO + 0.5
    k.dm_pulse = k.DEMO + 1.0
    k.dm_pulse2 = max(k.dm_pulse + 1.7, word("s02_l02", 4, k.L2 + 1.0) - 0.05)   # on "doing?"
    k.dm_charge2 = k.dm_pulse2 - 0.4
    k.w_okay = word("s02_l02", 5, k.L2 + 1.45)        # "Are you okay?"
    k.dm_open = k.w_okay + 0.15                       # it opens its eyes: a flat look
    # the sassy eye-roll (CR.EYEROLL_DUR = 1.25 s)
    k.roll0 = max(k.L2e + 0.12, k.ROLL - 0.3)
    # the hood pull
    k.hd0 = k.HOOD + 0.08
    k.hd1 = k.hd0 + 0.8                               # hood fully over his eyes
    k.sigh = k.hd1 + 0.3
    # PEEK: the hand comes up, a finger lifts the rim, one eye peeks out
    k.pk0 = max(k.PEEK + 0.08, k.sigh + 0.7)
    k.pk1 = k.pk0 + 0.5                               # fingertip under the rim
    k.pk2 = k.pk1 + 0.3                               # rim lifted
    k.pk_see = k.pk2 + 0.2                            # Curiosity spots the eye ...
    k.pk_close = k.pk_see + 0.32                      # ... and pointedly shuts its own
    k.pk_pulse = min(k.pk_close + 0.42, k.L3 - 0.55)  # and pulses
    # "look": the one eye wanders the dark, then back to it
    k.lk1 = k.LOOK + 0.05
    k.lk2 = k.lk1 + 0.65
    k.lk3 = k.lk2 + 0.55
    # l04: the rim drops back down on "close"; the hand settles in his lap
    k.dr0 = word("s02_l04", 3, k.L4 + 0.9)
    k.dr1 = k.dr0 + 0.28
    k.dr2 = k.dr0 + 0.9
    # the nod; then his first own ping (+ a second one following his head)
    k.n0 = k.NOD + 0.1
    k.p1 = k.PING + 0.45
    k.p2 = k.PING + 1.4
    # he stands up into l05; the CU cut on "A superpower..."
    k.stand0 = k.L5 - 0.35
    k.stand1 = k.stand0 + 0.75
    k.smug_cu = max(k.stand1 + 0.3, word("s02_l05", 1, k.stand1 + 0.4) - 0.08)
    k.w_super = word("s02_l05", 2, k.L5 + 1.2)
    k.w_actually = word("s02_l05", 4, k.L5 + 1.8)
    # the walk: one constant confident stride, timed so the face meets the pipe at BONK
    k.v = abs(human.cycle_speed("tired", "walk_eyes_closed", -1.0)) * S
    k.tgo = k.BONK - (T_X - BONK_X) / k.v
    k.turn0 = max(k.WALK + 0.05, k.tgo - 0.5)
    # Curiosity follows once he has passed it (hops down, trots)
    k.chop0 = k.tgo + (T_X - (C_XS2 - 150)) / k.v
    k.chop1 = k.chop0 + 0.36
    k.cv = 2.2 * CR.SPEC_WALK_SPEED * S
    # post-bonk
    k.giggle0 = k.L6e + 0.25
    # shot cuts
    k.cut_fit = k.L2 - 0.1
    k.cut_roll = k.L2e + 0.08
    k.cut_oh = k.L3 - 0.22
    k.cut_nod = k.L4 - 0.1
    # Curiosity settles down off its hind legs (a little hop) while his eye wanders the dark
    k.c_sit0 = k.lk1 + 0.1
    k.c_sit1 = k.c_sit0 + 0.32
    k.shots = _shots(k)
    _KC.clear()
    _KC[key] = k
    return k


# ---------------------------------------------------------------------------
# Tiredness
# ---------------------------------------------------------------------------
def stair_y(x):
    """Ground y along deck -> stair -> landing (walking left)."""
    yy = FEET + ST_RISE * ((ST_TOP_X - x) / ST_RUN + 0.5)
    return clamp(yy, FEET, LAND)


def walk_y(x):
    if x >= 700:
        return lerp(T_GSEAT, FEET, smoothstep(seg(x, T_X, 700)))
    return stair_y(x)


def sit_pose(t, k):
    """sit_crate with an animated slump: slumped -> engaged -> straighter after his ping."""
    up = smoothstep(seg(t, k.p1 - 0.1, k.p1 + 0.4))
    lift2 = kf(t, [(k.DEMO - 0.3, 0.0), (k.DEMO + 0.3, 0.3), (k.L2, 0.32), (k.L2 + 0.3, 0.45),
                   (k.HOOD + 0.4, 0.45), (k.hd1 + 0.15, 0.1), (k.sigh + 0.2, 0.0),
                   (k.pk0, 0.0), (k.pk1, 0.32), (k.dr0, 0.32), (k.dr2, 0.2)])
    a = max(lift2, 0.0) * (1 - up)
    # the demo pulse makes him flinch back a little (and the second one, less)
    fl = 0.7 * bump(t, k.dm_pulse - 0.02, k.dm_pulse + 0.7) + 0.4 * bump(t, k.dm_pulse2 - 0.02, k.dm_pulse2 + 0.6)
    lean = lerp(lerp(0.5, 0.36, a), 0.22, up) - 0.12 * fl
    lean += 0.07 * smoothstep(seg(t, k.w_okay - 0.2, k.w_okay + 0.3)) * (1 - smoothstep(seg(t, k.L2e, k.HOOD)))
    nod = lerp(lerp(0.34, 0.12, a), 0.0, up)
    neck = lerp(0.32, 0.2, max(a, up))
    sg = bump(t, k.sigh - 0.1, k.sigh + 0.8)                     # sigh: shoulders drop
    return {"base": "sit_crate", "lean": lean + 0.05 * sg, "nod": nod + 0.06 * sg, "neck": neck,
            "hunch": 0.65 + 0.2 * sg}


PROUD = {"base": "stand", "chest": -0.1, "nod": -0.12, "neck": -0.08, "posture": 0.4, "hunch": 0.1}


def peek_amount(t, k):
    """0 = rim down over both eyes, 1 = lifted over his screen-right eye (a bit more on "Oh.")."""
    return kf(t, [(k.pk1 - 0.02, 0.0), (k.pk2, 1.0), (k.L3 - 0.05, 1.0), (k.L3 + 0.2, 1.18),
                  (k.L3e + 0.4, 1.18), (k.L3e + 0.8, 1.05), (k.dr0, 1.05), (k.dr1, 0.0)])


def arm_amount(t, k):
    """0 = hands clasped on his knees, 1 = the r hand up at the hood rim."""
    return kf(t, [(k.pk0, 0.0), (k.pk1, 1.0), (k.dr0 + 0.1, 1.0), (k.dr2, 0.0)])


def tired_state(t, k, info):
    st = dict(x=T_X, y=FEET, pose="stand", pose_t=None, turn=0.25, expr="bored", face={},
              look=(0.0, 0.0), blink=None, hood=0.0, mouth=info.mouth("tired", t), peek=0.0, bface=None)
    f = st["face"]
    # ---------------- standing in the dark (where s01 left him), l01, sits down
    if t < k.sit1:
        st["x"] = T_X0
        st["turn"] = -0.15
        st["look"] = kf(t, [(0.0, (-0.55, 0.3)), (0.5, (-0.55, 0.3)), (0.85, (-0.1, 0.0)), (1.25, (-0.1, 0.0)),
                            (1.55, (0.45, -0.05)), (2.0, (0.2, 0.0)),
                            (k.L1 + 1.1, (0.2, 0.0)), (k.L1 + 1.4, (-0.6, 0.0)), (k.L1 + 1.75, (-0.6, 0.0)),
                            (k.L1 + 2.05, (0.55, -0.05)), (k.L1e - 0.05, (0.55, -0.05)),
                            (k.sit0 + 0.2, (0.0, 0.45)), (k.sit1, (0.1, 0.2))])
        b0 = k.L1 + 0.45                                   # the slow, flat blink on "Great."
        bl = max(math.sin(math.pi * seg(t, 1.05, 1.25)), math.sin(math.pi * seg(t, k.L1e - 0.35, k.L1e - 0.15)))
        st["blink"] = max(bl, kf(t, [(b0, 0.0), (b0 + 0.25, 1.0), (b0 + 0.55, 1.0), (b0 + 0.9, 0.0)]))
        if t >= k.sit0:
            kk = seg(t, k.sit0, k.sit1)
            st["pose"] = ("stand", sit_pose(t, k), smoothstep(seg(kk, 0.15, 0.85)))
            st["x"] = lerp(T_X0, T_X, ease_in_out(seg(kk, 0.0, 0.55)))      # a step back onto the plinth
            st["y"] = lerp(FEET, T_GSEAT, ease_in_out(seg(kk, 0.05, 0.8)))
            st["turn"] = lerp(-0.15, 0.25, smoothstep(seg(kk, 0.1, 0.8)))
            st["expr"] = "sigh"
            f["squash"] = 0.06 * math.sin(math.pi * seg(kk, 0.78, 1.0))      # the plop
        return st
    # ---------------- seated on the plinth
    if t < k.stand0:
        st["y"] = T_GSEAT
        sp = sit_pose(t, k)
        ka = arm_amount(t, k)
        st["pose"] = sp
        st["turn"] = 0.25
        st["expr"] = state_at(t, [(0.0, "bored"), (k.dm_close + 0.2, "neutral"), (k.L2 - 0.15, "neutral"),
                                  (k.roll0 + 0.3, "unamused"), (k.HOOD + 0.1, "annoyed"),
                                  (k.sigh - 0.1, "sigh"), (k.sigh + 0.8, "unamused"),
                                  (k.L3 - 0.1, "neutral"), (k.L4 - 0.15, "curious"),
                                  (k.L4e + 0.2, "neutral")], 0.25)
        # ---- eyes (before the hood): pupils lead, head follows ~0.15 s later
        st["look"] = kf(t, [(k.sit1, (0.1, 0.2)), (k.hop2 - 0.05, (0.1, 0.15)), (k.hop2 + 0.15, (-0.85, -0.1)),
                            (k.dm_pulse + 0.15, (-0.85, -0.1)), (k.dm_pulse + 0.4, (0.35, -0.35)),   # the ring flies past
                            (k.dm_pulse + 0.85, (0.35, -0.3)), (k.dm_pulse + 1.15, (-0.85, -0.12)),  # ... back to it
                            (k.L2e, (-0.8, -0.2)), (k.roll0 + 0.2, (-0.8, -0.2)),
                            (k.hd0 - 0.05, (-0.7, -0.3)), (k.hd0 + 0.25, (-0.25, -0.9))])
        f["head_turn"] = kf(t, [(k.hop2 + 0.15, 0.0), (k.hop2 + 0.45, -0.42),
                                (k.dm_pulse + 0.3, -0.42), (k.dm_pulse + 0.6, -0.2), (k.dm_pulse + 1.0, -0.2),
                                (k.dm_pulse + 1.3, -0.42), (k.HOOD, -0.42),
                                (k.hd0 + 0.3, -0.12), (k.hd1 + 0.2, -0.05), (k.sigh + 0.6, -0.05),
                                (k.pk1, -0.3), (k.pk_pulse + 0.4, -0.3), (k.pk_pulse + 0.7, -0.15),   # ring passes
                                (k.L3 + 0.1, -0.32), (k.lk1 + 0.15, -0.32), (k.lk1 + 0.5, -0.05),    # look: out ...
                                (k.lk2 + 0.15, -0.05), (k.lk2 + 0.45, -0.5), (k.lk3 + 0.2, -0.35),  # ... and back
                                (k.L4 + 0.6, -0.35), (k.NOD + 0.1, -0.42),
                                (k.p1 + 0.3, -0.42), (k.p1 + 0.55, -0.3),                          # his ping
                                (k.p2 - 0.3, -0.3), (k.p2 - 0.05, -0.62), (k.p2 + 0.5, -0.62),       # head follows
                                (k.stand0, -0.4)])
        f["head_tilt"] = kf(t, [(k.dm_charge, 0.0), (k.dm_pulse - 0.1, 0.05), (k.L2 + 0.4, 0.07),
                                (k.w_okay, 0.07), (k.w_okay + 0.3, 0.11), (k.L2e + 0.2, 0.11), (k.HOOD, 0.0),
                                (k.pk1, 0.0), (k.pk2, 0.05), (k.L3, 0.05), (k.L3 + 0.3, -0.03),
                                (k.lk1, -0.03), (k.lk1 + 0.4, 0.06), (k.lk2 + 0.4, -0.06), (k.L4 + 0.5, 0.0),
                                (k.L4 + 0.9, 0.0), (k.L4 + 1.3, -0.1), (k.L4e + 0.6, -0.1), (k.NOD + 1.0, -0.03)])
        # brows: one up while it shuts its eyes ("...what?"), worried through l02
        f["brow_l"] = kf(t, [(k.dm_close + 0.1, 0.0), (k.dm_close + 0.4, 0.3), (k.L2 - 0.2, 0.3),
                             (k.L2 + 0.2, 0.0)])
        f["brow_ang"] = kf(t, [(k.L2 - 0.3, 0.0), (k.L2 + 0.1, 0.45), (k.w_okay, 0.45), (k.w_okay + 0.25, 0.65),
                               (k.L2e + 0.1, 0.6), (k.roll0 + 0.3, 0.6), (k.roll0 + 0.6, 0.0)])
        f["brow"] = kf(t, [(k.L2 - 0.3, 0.0), (k.L2 + 0.1, 0.2), (k.w_okay + 0.25, 0.35), (k.L2e + 0.2, 0.3),
                           (k.roll0 + 0.6, 0.0),
                           (k.p1 - 0.05, 0.0), (k.p1 + 0.25, 0.65), (min(k.p2 + 0.4, k.stand0 - 0.05), 0.65),
                           (k.stand0, 0.3)])
        # the demo pulse: a small startle (lids lift a little, pupils shrink, head pulls back)
        st_k = kf(t, [(k.dm_pulse - 0.02, 0.0), (k.dm_pulse + 0.08, 1.0), (k.dm_pulse + 0.6, 0.85),
                      (k.dm_pulse + 1.3, 0.25), (k.L2, 0.25), (k.dm_pulse2, 0.25), (k.dm_pulse2 + 0.08, 0.7),
                      (k.dm_pulse2 + 0.7, 0.3), (k.L2e + 0.3, 0.2), (k.roll0 + 0.6, 0.0)])
        ok_k = kf(t, [(k.w_okay - 0.1, 0.0), (k.w_okay + 0.2, 1.0), (k.L2e + 0.2, 1.0), (k.roll0 + 0.5, 0.0)])
        f["lid"] = -0.12 * st_k - 0.05 * ok_k
        f["lid_ang"] = 0.3 * ok_k                  # softer, worried eyes
        f["pupil"] = -0.3 * st_k + 0.15 * ok_k
        f["squash"] = -0.06 * bump(t, k.dm_pulse - 0.02, k.dm_pulse + 0.3)
        f["frown"] = kf(t, [(k.L2 - 0.2, 0.0), (k.L2 + 0.1, 0.18), (k.w_okay, 0.12), (k.L2e, 0.1),
                            (k.roll0 + 0.3, 0.1), (k.hd0 + 0.1, 0.1), (k.hd0 + 0.4, 0.35), (k.sigh, 0.35),
                            (k.sigh + 0.5, 0.1), (k.L3 - 0.2, 0.1), (k.L3, 0.0)])
        f["asym"] = kf(t, [(k.L2 - 0.2, 0.0), (k.L2 + 0.15, -0.35), (k.w_okay, -0.35), (k.w_okay + 0.2, 0.0)])
        f["press"] = kf(t, [(k.roll0 + 0.3, 0.0), (k.roll0 + 0.6, 0.35), (k.hd0, 0.35), (k.hd0 + 0.3, 0.55),
                            (k.sigh - 0.15, 0.55), (k.sigh, 0.0), (k.sigh + 0.8, 0.0), (k.pk1, 0.35),
                            (k.pk_pulse, 0.35), (k.pk_pulse + 0.3, 0.0),
                            (k.lk1, 0.0), (k.lk1 + 0.3, 0.25), (k.lk3, 0.25), (k.L4 - 0.1, 0.0),
                            (k.L4e + 0.3, 0.0), (k.L4e + 0.6, 0.25), (k.PING + 0.1, 0.25), (k.PING + 0.3, 0.4),
                            (k.p1, 0.4), (k.p1 + 0.15, 0.0)])
        f["open"] = kf(t, [(k.L3 - 0.1, 0.0), (k.L3, 0.0), (k.L3e + 0.1, 0.0), (k.L3e + 0.3, 0.1),
                           (k.lk1, 0.1), (k.lk1 + 0.3, 0.0),
                           (k.p1 + 0.05, 0.0), (k.p1 + 0.3, 0.14), (k.p2, 0.14), (k.p2 + 0.3, 0.22),
                           (k.L5 - 0.1, 0.22), (k.L5, 0.0)])
        f["smirk"] = kf(t, [(k.L4e + 0.2, 0.0), (k.L4e + 0.5, 0.12), (k.NOD + 0.6, 0.12),
                            (k.NOD + 0.9, 0.0)])
        # ---- the hood: yanked up, then (peek) a finger lifts the rim, dropped again on "close"
        st["hood"] = kf(t, [(k.hd0, 0.0), (k.hd0 + 0.38, 0.45), (k.hd1, 1.0)])
        f["head_nod"] = (0.2 * bump(t, k.hd1 - 0.3, k.hd1 + 0.4)
                         - 0.05 * bump(t, k.dm_pulse - 0.02, k.dm_pulse + 0.5)
                         - 0.04 * smoothstep(seg(t, k.pk1, k.pk2)) * (1 - smoothstep(seg(t, k.dr0, k.dr2)))
                         + 0.08 * bump(t, k.dr0, k.dr0 + 0.6)                 # the rim drops: a little dip
                         - 0.06 * smoothstep(seg(t, k.p1 - 0.05, k.p1 + 0.35)))
        p = peek_amount(t, k)
        if p > 0.0:
            st["peek"] = p
            # the peeking eye (screen-right) in the lifted-rim render
            lk = kf(t, [(k.pk2 - 0.2, (-0.7, 0.05)), (k.pk_pulse + 0.15, (-0.75, 0.0)),
                        (k.pk_pulse + 0.4, (0.55, -0.25)), (k.L3 - 0.25, (0.35, -0.2)),     # follows the ring out
                        (k.L3, (-0.8, 0.05)),                                              # "Oh." back to it
                        (k.lk1, (-0.8, 0.05)), (k.lk1 + 0.2, (0.8, -0.15)), (k.lk2, (0.8, -0.15)),   # the dark
                        (k.lk2 + 0.2, (-0.92, 0.3)), (k.lk3, (-0.85, 0.25))])
            wide = kf(t, [(k.L3 - 0.1, 0.0), (k.L3 + 0.12, 1.0), (k.L3e + 0.5, 1.0), (k.lk1, 0.55),
                          (k.lk3, 0.4)])
            skept = kf(t, [(k.pk2, 1.0), (k.pk_pulse, 1.0), (k.pk_pulse + 0.4, 0.4), (k.L3, 0.0)])
            bf = dict(f)
            bf.update({"lid": 0.04 * skept - 0.2 * wide, "pupil": 0.18 * wide - 0.1 * skept,
                       "brow_r": 0.4 * wide - 0.15 * skept, "hl": 0.25 * wide})
            st["bface"] = bf
            st["blook"] = lk
            # lets the eye close as the rim drops ("close my eyes?")
            st["bblink"] = kf(t, [(k.dr0 - 0.05, 0.0), (k.dr0 + 0.15, 1.0)]) if t > k.dr0 - 0.05 else None
        if ka > 0.0:
            # the r hand leaves the clasp, swings out to the side and up to the rim (a pose blend:
            # the rig switches the draw order once, mid-path, where the hand is clear of the head
            # and of the other hand); the finger goes where the rim lifts
            g = peek_frame(t, st, p)
            st["peek_geo"] = g
            (x0, y0, a0), (x2, y2) = g["hand0"], g["grip"]
            x1, y1 = max(x0, x2) + 75 * S / 0.75, (y0 + y2) / 2 + 25 * S / 0.75
            u = ka
            hx = (1 - u) ** 2 * x0 + 2 * u * (1 - u) * x1 + u * u * x2
            hy = (1 - u) ** 2 * y0 + 2 * u * (1 - u) * y1 + u * u * y2
            fa = g["fang"]
            while fa - a0 > math.pi:
                fa -= 2 * math.pi
            while fa - a0 < -math.pi:
                fa += 2 * math.pi
            st["pose"] = (sp, dict(sp, **ARM_PEEK), ka)
            st["pose_front"] = (dict(sp, ar_layer="front"), dict(sp, ar_layer="front", **ARM_PEEK), ka)
            st["arm"] = ka
            st["reach"] = {"r": (hx, hy, 1.0, lerp(a0, fa, smoothstep(u)))}
        return st
    # ---------------- stands up into l05, proud; then turns and walks
    st["hood"] = 1.0
    if t < k.turn0:
        st["y"] = T_GSEAT
        kk = seg(t, k.stand0, k.stand1)
        sp = sit_pose(t, k)
        sp = dict(sp, lean=sp["lean"] + 0.18 * math.sin(math.pi * seg(kk, 0.0, 0.45)))   # lean in, push up
        st["pose"] = (sp, PROUD, smoothstep(seg(kk, 0.25, 1.0)))
        st["turn"] = lerp(0.25, 0.1, smoothstep(kk))
        f["head_turn"] = lerp(-0.4, 0.12, smoothstep(seg(kk, 0.2, 1.0)))       # chin up, away from it
        st["expr"] = "deadpan"
        sm = smoothstep(seg(t, k.w_actually - 0.1, k.w_actually + 0.5))
        f["smirk"] = 0.18 + 0.32 * sm
        f["curve"] = 0.15 * sm
        f["brow"] = lerp(0.3, 0.0, smoothstep(kk))
        f["head_tilt"] = kf(t, [(k.stand1, 0.0), (k.stand1 + 0.4, 0.05)])
        f["head_nod"] = -0.06 * (1 - smoothstep(kk)) - 0.04 * smoothstep(seg(t, k.L5 + 0.4, k.L5 + 0.9))
        return st
    f.update({"smirk": 0.4, "curve": 0.12})
    st["expr"] = "deadpan"
    if t < k.tgo:                                       # turns on the spot to face left
        kk = seg(t, k.turn0, k.tgo)
        st["y"] = T_GSEAT
        st["pose"] = PROUD
        st["turn"] = lerp(0.1, -1.0, ease_in_out(kk))
        f["head_nod"] = -0.04
        return st
    if t < k.BONK:                                      # the confident stride
        x = T_X - k.v * (t - k.tgo)
        st["x"], st["y"] = x, walk_y(x)
        st["pose"] = "walk_eyes_closed"
        st["pose_t"] = t - k.tgo
        st["turn"] = -1.0
        return st
    # ---------------- BONK: no anticipation; whiplash back, a stunned hold, slow settle
    tb = t - k.BONK
    st["turn"] = -1.0
    snap = ease_out(seg(tb, 0.0, 0.07))
    peak = snap * (1 - smoothstep(seg(tb, 0.07, 0.35)))          # the whiplash
    held = snap * (1 - smoothstep(seg(tb, 0.7, 1.5)))            # the stunned hold
    knock = 0.55 * held + 0.45 * peak
    rock = 34 * ease_out(seg(tb, 0.0, 0.14)) - 12 * smoothstep(seg(tb, 0.75, 1.5))
    st["x"] = BONK_X + rock
    st["y"] = LAND
    rel = smoothstep(seg(tb, 0.7, 1.5))
    recoil = {"base": "stand", "lean": -0.3 * knock, "rot": 0.2 * knock, "chest": -0.25 * knock,
              "nod": -0.45 * knock + 0.05 * rel, "neck": -0.4 * knock, "tilt": 0.22 * knock,
              "posture": 0.6, "hunch": 0.2 + 0.3 * knock,
              "al_p": 0.05 + 0.7 * knock, "ar_p": 0.05 + 0.55 * knock,
              "al_o": 0.1 + 0.3 * knock, "ar_o": 0.1 + 0.3 * knock,
              "al_e": 0.2 + 0.3 * knock, "ar_e": 0.2 + 0.3 * knock}
    st["pose"] = ("walk_eyes_closed", recoil, smoothstep(seg(tb, 0.0, 0.05)))
    st["pose_t"] = k.BONK - k.tgo
    f["squash"] = 0.22 * math.sin(math.pi * seg(tb, 0.0, 0.12)) - 0.06 * math.sin(math.pi * seg(tb, 0.1, 0.3))
    f["head_tilt"] = math.sin(tb * 5.0) * 0.07 * (1 - seg(tb, 0.6, 2.4)) * seg(tb, 0.2, 0.4)   # dazed wobble
    st["expr"] = state_at(t, [(k.BONK, "pain"), (k.BONK + 0.45, "dazed"), (k.L6 - 0.35, "deadpan")], 0.2)
    f.update({"smirk": 0.0, "curve": 0.0})
    f["wobble"] = 0.4 * (1 - seg(tb, 0.5, 1.2)) * seg(tb, 0.3, 0.45)
    f["press"] = kf(t, [(k.L6 - 0.4, 0.0), (k.L6 - 0.1, 0.3), (k.L6e + 0.1, 0.3), (k.L6e + 0.5, 0.45)])
    f["frown"] = kf(t, [(k.L6 - 0.4, 0.0), (k.L6, 0.15)])
    return st


def _draw_person(ctx, t, st, hood=None, face=None, look=None, blink="st", pose=None, reach="st"):
    return human.draw_person(ctx, "tired", st["x"], st["y"], S, t, pose=st["pose"] if pose is None else pose,
                             pose_t=st["pose_t"],
                             turn=st["turn"], expr=st["expr"], face=face if face is not None else st["face"],
                             look=look if look is not None else st["look"],
                             mouth=st["mouth"], blink=st["blink"] if blink == "st" else blink,
                             hood=st["hood"] if hood is None else hood, power=0.6,
                             outfit="sewer", bandage=True, headphones=None, shadow=False,
                             reach=st.get("reach") if reach == "st" else reach)


def _loc(O, ux, uy, P):
    dx, dy = P[0] - O[0], P[1] - O[1]
    return (dx * ux + dy * uy, -dx * uy + dy * ux)


def peek_frame(t, st, p):
    """The lifted rim in the peek eye's local frame (x along the eye line toward screen-right,
    y down; origin = the screen-right eye), from two cheap solves with the arm down:
    the hood-down rim (yA), the second render's higher rim (yB), the tent peak at the finger."""
    a = _draw_person(_dummy(), t, st, reach=None)
    b = _draw_person(_dummy(), t, st, hood=HOOD_PEEK, reach=None)
    el, er = a["eye_l"], a["eye_r"]
    ang = math.atan2(er[1] - el[1], er[0] - el[0])
    ux, uy = math.cos(ang), math.sin(ang)
    O = er
    ed = math.hypot(er[0] - el[0], er[1] - el[1])
    yA = _loc(O, ux, uy, a["hood_rim"])[1] + 2.6 * S
    yB = _loc(O, ux, uy, b["hood_rim"])[1] + 2.6 * S
    hmax = max(0.0, yA - (yB + 5.0 * S))
    h = hmax * clamp(p / 1.25, 0.0, 1.0)
    Fx = PEEK_FX * ed
    fx_, fy_ = Fx, yA - h - 4.0 * S                          # fingertip, tucked just under the hem
    gl = (fx_ - FINGER * S * math.cos(FINGER_ANG), fy_ - FINGER * S * math.sin(FINGER_ANG))
    grip = (O[0] + gl[0] * ux - gl[1] * uy, O[1] + gl[0] * uy + gl[1] * ux)
    return dict(O=O, ang=ang, ed=ed, yA=yA, yB=yB, h=h, hmax=hmax, Fx=Fx, xl=-0.85 * ed, xr=Fx + 0.5 * ed,
                grip=grip, fang=ang + FINGER_ANG, eye_b=b["eye_r"], hand0=a["hand_r"])


def _tent_at_finger(g, a, p):
    """Re-key the tent to the finger actually drawn (the reach may fall a few px short)."""
    O, ang = g["O"], g["ang"]
    ux, uy = math.cos(ang), math.sin(ang)
    hx, hy, hang = a["hand_r"]
    tip = (hx + FINGER * S * math.cos(hang), hy + FINGER * S * math.sin(hang))
    tx, ty = _loc(O, ux, uy, tip)
    g = dict(g)
    g["Fx"] = clamp(tx, 0.3 * g["ed"], 0.95 * g["ed"])
    g["xr"] = g["Fx"] + 0.5 * g["ed"]
    g["h"] = clamp(g["yA"] - ty - 4.0 * S, 0.0, g["hmax"]) * smoothstep(clamp(p / 0.15))
    return g


def _arch(g):
    xl, xr, Fx, yA, h = g["xl"], g["xr"], g["Fx"], g["yA"], g["h"]

    def arch(x):
        if x <= xl or x >= xr:
            return yA
        u = (x - xl) / (Fx - xl) if x < Fx else (xr - x) / (xr - Fx)
        return yA - h * math.sin(0.5 * math.pi * u) ** 1.3
    xs = [xl + (Fx - xl) * i / 16 for i in range(16)] + [Fx + (xr - Fx) * i / 8 for i in range(9)]
    return arch, xs


def _bface_kw(st):
    bl = st.get("bblink")
    return dict(hood=HOOD_PEEK, face=st.get("bface") or st["face"], look=st.get("blook"),
                blink=st["blink"] if bl is None else bl)


def _hand_disc(ctx, a):
    hx, hy, hang = a["hand_r"]
    cx_, cy_ = hx + 0.45 * FINGER * S * math.cos(hang), hy + 0.45 * FINGER * S * math.sin(hang)
    ctx.arc(cx_, cy_, HAND_R * S, 0, 2 * math.pi)


def _window_path(ctx, g, arch, xs, local=True):
    """The lifted-rim window (under the tent, down to just below the hood-down rim)."""
    O, ang, yA = g["O"], g["ang"], g["yA"]
    ux, uy = math.cos(ang), math.sin(ang)
    pts = [(xs[0], yA + 2.5 * S)] + [(x, arch(x)) for x in xs] + [(xs[-1], yA + 2.5 * S)]
    if not local:
        pts = [(O[0] + x * ux - y * uy, O[1] + x * uy + y * ux) for (x, y) in pts]
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()


def _hand_over(ctx, t, st, a, g=None, arch=None, xs=None):
    """Redraw only his r hand over the head: a front-layer copy clipped to a disc at the hand
    (inside the lifted-rim window the copy is the lifted-rim one, so no hood patch shows)."""
    al = smoothstep(clamp((st.get("arm", 0.0) - 0.5) / 0.4))     # eases on as the hand nears the hood
    if al <= 0.0:
        return
    if g is None:
        ctx.save()
        _hand_disc(ctx, a)
        ctx.clip()
        ctx.push_group()
        _draw_person(ctx, t, st, pose=st["pose_front"])
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)
        ctx.restore()
        return
    ctx.save()
    _hand_disc(ctx, a)
    ctx.clip()
    ctx.push_group()
    ctx.save()
    hx, hy = a["hand_r"][:2]
    ctx.rectangle(hx - 400, hy - 400, 800, 800)
    _window_path(ctx, g, arch, xs, local=False)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.clip()
    _draw_person(ctx, t, st, pose=st["pose_front"])
    ctx.restore()
    ctx.save()
    _window_path(ctx, g, arch, xs, local=False)
    ctx.clip()
    _draw_person(ctx, t, st, pose=st["pose_front"], **_bface_kw(st))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(al)
    ctx.restore()


def draw_tired(ctx, t, st):
    a = _draw_person(ctx, t, st)
    hand = st.get("arm", 0.0) > 0.5 and st.get("pose_front")
    p = st.get("peek", 0.0)
    g = st.get("peek_geo")
    if g is not None and p > 0.005 and a.get("hood_rim"):
        g = _tent_at_finger(g, a, p)
    if g is None or p <= 0.005 or g["h"] < 0.5 or not a.get("hood_rim"):
        if hand:
            _hand_over(ctx, t, st, a)
        return a
    # ---- the lifted rim: a second render with the rim above the eye, through a tent window
    O, ang, ed, yA, h = g["O"], g["ang"], g["ed"], g["yA"], g["h"]
    ux, uy = math.cos(ang), math.sin(ang)
    arch, xs = _arch(g)
    xl, xr = g["xl"], g["xr"]
    span = xr - xl
    D = 0.85 * ed
    hb = 11.0 * S
    # tight clip (world) around the window + its soft skirt: the second render is costly
    corners = [(xl - 0.4 * span, yA - h - hb - 12 * S), (xr + 0.4 * span, yA - h - hb - 12 * S),
               (xl - 0.4 * span, yA + D + 2), (xr + 0.4 * span, yA + D + 2)]
    wc = [(O[0] + x * ux - y * uy, O[1] + x * uy + y * ux) for (x, y) in corners]
    bx0, by0 = min(q[0] for q in wc), min(q[1] for q in wc)
    bx1, by1 = max(q[0] for q in wc), max(q[1] for q in wc)
    ctx.save()
    ctx.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
    ctx.clip()
    ctx.push_group()
    _draw_person(ctx, t, st, **_bface_kw(st))
    pat = ctx.pop_group()
    # mask: the window (hard, under the tent) + a soft blend of the face shading below the rim
    ctx.push_group()
    ctx.save()
    ctx.translate(*O)
    ctx.rotate(ang)
    _window_path(ctx, g, arch, xs)
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.fill()
    ctx.push_group()
    ctx.rectangle(xl - 0.4 * span, yA - 1.0, 1.8 * span, D)
    gx = cairo.LinearGradient(xl - 0.4 * span, 0, xr + 0.4 * span, 0)
    gx.add_color_stop_rgba(0.0, 0, 0, 0, 0)
    gx.add_color_stop_rgba(0.3, 0, 0, 0, 1)
    gx.add_color_stop_rgba(0.7, 0, 0, 0, 1)
    gx.add_color_stop_rgba(1.0, 0, 0, 0, 0)
    ctx.set_source(gx)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_DEST_IN)
    gy = cairo.LinearGradient(0, yA, 0, yA + D)
    gy.add_color_stop_rgba(0.0, 0, 0, 0, min(1.0, h / (6.0 * S)))
    gy.add_color_stop_rgba(1.0, 0, 0, 0, 0)
    ctx.set_source(gy)
    ctx.paint()
    ctx.pop_group_to_source()
    ctx.paint()
    ctx.restore()
    mask = ctx.pop_group()
    ctx.set_source(pat)
    ctx.mask(mask)
    ctx.restore()

    def arch_path():
        ctx.move_to(xs[0], arch(xs[0]))
        for x in xs[1:]:
            ctx.line_to(x, arch(x))
    # the lifted hem: a soft shadow under it, (the finger), the rolled hem band, the ink edge
    ctx.save()
    ctx.translate(*O)
    ctx.rotate(ang)
    arch_path()
    ctx.set_source_rgba(0.07, 0.06, 0.13, 0.35 * min(1.0, h / (10 * S)))
    ctx.set_line_width(14 * S)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.restore()
    if hand:                                   # the finger hooks under the lifted hem
        _hand_over(ctx, t, st, a, g, arch, xs)
    ctx.save()
    ctx.translate(*O)
    ctx.rotate(ang)
    arch_path()
    for x in reversed(xs):
        ctx.line_to(x, arch(x) - hb)
    ctx.close_path()
    core.set_color(ctx, _HOOD_DK)
    ctx.fill()
    arch_path()
    core.set_color(ctx, _INK)
    ctx.set_line_width(5.5 * S)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.restore()
    a = dict(a)
    a["peek_eye"] = g["eye_b"]
    return a


_DUMMY = None


def _dummy():
    global _DUMMY
    if _DUMMY is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        _DUMMY = cairo.Context(surf)
        _DUMMY.scale(0.002, 0.002)
    return _DUMMY


def tired_anchors(t, k, info, st=None):
    """Anchors of Tiredness at time t without drawing to the frame."""
    st = st or tired_state(t, k, info)
    return _draw_person(_dummy(), t, st)


# ---------------------------------------------------------------------------
# Curiosity
# ---------------------------------------------------------------------------
def cur_state(t, k):
    st = dict(x=C_X0, y=FEET, pose="sit", flip=False, expr="calm", look=(0.6, -0.55), face=None,
              tilt=0.0, ears=0.6, tail_curl=0.0, reach=0.0, pose_t=None, glow=1.0, blink=None,
              sy=1.0, rot=0.0, pose_from=None, pose_mix=1.0, look_target=None, eyes=1.0)
    # ---------------- on the deck, watching him in the dark (s01 ends on "wide")
    if t < k.hop0:
        st["look_target"] = "eyes"
        st["expr"] = "wide" if t < 0.6 else ("calm" if t < k.L1 + 1.0 else "curious")
        st["ears"] = kf(t, [(0.0, 0.9), (0.6, 0.9), (1.0, 0.62), (k.L1 + 1.0, 0.62), (k.L1 + 1.3, 0.68)])
        return st
    # ---------------- the hop up onto the plinth: crouch, jump straight up, land on its hind legs
    if t < k.hop2:
        if t < k.hop1:
            kk = seg(t, k.hop0, k.hop1)
            st["pose"] = "crouch"
            st["pose_from"], st["pose_mix"] = "sit", smoothstep(kk / 0.6)
            st["sy"] = 1.0 - 0.12 * smoothstep(kk)
            st["look"] = (0.3, -0.7)
            st["ears"] = 0.7
            return st
        kk = seg(t, k.hop1, k.hop2)
        st["pose"] = "reach_up"
        st["x"] = lerp(C_X0, C_XP, kk)
        st["y"] = lerp(FEET, PLINTH_Y, ease_out(kk)) - 70 * math.sin(math.pi * kk)
        st["sy"] = 1.0 + 0.14 * math.sin(math.pi * min(1.0, kk * 1.4))
        st["look"] = (0.4, -0.6)
        st["ears"] = 0.85
        return st
    # ---------------- up on its hind legs beside him (paws at its chest): the demo, the roll,
    #                  the hood yank, the pointed pulse at his peeking eye
    st["x"], st["y"] = C_XP, PLINTH_Y
    if t < k.c_sit0:
        st["pose"] = "reach_up"
        land = seg(t, k.hop2, k.hop2 + 0.32)
        sy = 0.84 + 0.16 * ease_out_back(land) if land < 1 else 1.0
        # demo: charge up (a little crouch + tremble), the pulse stretches it tall, settle
        ch = smoothstep(seg(t, k.dm_charge, k.dm_pulse)) * (1 - smoothstep(seg(t, k.dm_pulse, k.dm_pulse + 0.06)))
        ch2 = smoothstep(seg(t, k.dm_charge2, k.dm_pulse2)) * (1 - smoothstep(seg(t, k.dm_pulse2, k.dm_pulse2 + 0.06)))
        ch3 = smoothstep(seg(t, k.pk_pulse - 0.3, k.pk_pulse)) * (1 - smoothstep(seg(t, k.pk_pulse, k.pk_pulse + 0.06)))
        chg = max(ch, 0.7 * ch2, 0.5 * ch3)
        pop = 0.0
        for (tp, g) in ((k.dm_pulse, 1.0), (k.dm_pulse2, 0.7), (k.pk_pulse, 0.6)):
            u = seg(t, tp, tp + 0.5)
            if 0 < u < 1:
                pop = max(pop, g * math.sin(math.pi * u) * (1 - u) * 1.6)
        st["sy"] = sy - 0.05 * chg + 0.08 * pop
        trem = chg * (3.0 * math.sin(t * 2 * math.pi * 17.0) + 1.5 * math.sin(t * 2 * math.pi * 23.0 + 1.0))
        rr = kf(t, [(k.hop2, 0.0), (k.hop2 + 0.3, 0.06), (k.dm_pulse - 0.05, 0.02),
                    (k.dm_pulse + 0.12, 0.3), (k.dm_pulse + 0.7, 0.08), (k.dm_pulse2 - 0.05, 0.04),
                    (k.dm_pulse2 + 0.12, 0.22), (k.dm_pulse2 + 0.6, 0.06),
                    (k.HOOD - 0.15, 0.06),
                    # grab high (1.0), then yank down / forward over his eyes (0.42)
                    (k.hd0 + 0.25, 1.0), (k.hd0 + 0.4, 1.0), (k.hd1, 0.42), (k.hd1 + 0.25, 0.5),
                    (k.hd1 + 0.6, 0.1), (k.pk_pulse - 0.05, 0.06), (k.pk_pulse + 0.12, 0.2),
                    (k.pk_pulse + 0.6, 0.06)])
        st["reach"] = clamp(rr)
        st["x"] = C_XP + trem + kf(t, [(k.hd0 + 0.35, -4.0), (k.hd1, 30.0), (k.hd1 + 0.6, 0.0)])
        st["tilt"] = kf(t, [(k.hd0 + 0.3, -0.1), (k.hd1 - 0.1, 0.22), (k.hd1 + 0.5, 0.0)])
        # eyes: shut for the demo (its light goes out), open flat on "okay?", shut again (pointedly)
        st["eyes"] = kf(t, [(k.dm_close, 1.0), (k.dm_close + 0.3, 0.0), (k.dm_open, 0.0), (k.dm_open + 0.22, 1.0)])
        if k.dm_close <= t < k.dm_open + 0.22:
            st["blink"] = 1.0 - st["eyes"]
        st["ears"] = kf(t, [(k.hop2, 0.85), (k.hop2 + 0.6, 0.75), (k.dm_close, 0.75), (k.dm_close + 0.3, 0.88),
                            (k.dm_pulse - 0.05, 0.92), (k.dm_pulse + 0.1, 1.0), (k.dm_pulse + 0.8, 0.85),
                            (k.dm_pulse2 + 0.1, 0.95), (k.dm_open - 0.05, 0.86),
                            (k.dm_open + 0.25, 0.55), (k.roll0, 0.55), (k.roll0 + 0.2, 0.62),
                            (k.roll0 + 0.7, 0.36), (k.roll0 + 1.3, 0.42), (k.hd0, 0.75), (k.hd1 + 0.6, 0.78),
                            (k.pk_see - 0.05, 0.7), (k.pk_see + 0.12, 0.95), (k.pk_close, 0.9),
                            (k.pk_pulse + 0.1, 1.0), (k.L3, 0.85), (k.L3 + 0.3, 0.92)])
        st["expr"] = "calm"
        st["look_target"] = "eyes"
        if k.dm_close + 0.3 <= t < k.dm_open:
            st["expr"] = "content"                 # eyes shut (closed arcs), purring: "watch this"
            st["blink"] = None
        if k.dm_open <= t < k.roll0:
            st["expr"] = "annoyed"                 # opens its eyes: a flat look at him
        elif k.roll0 <= t < k.roll0 + CR.EYEROLL_DUR + 0.15:
            st["expr"] = "eyeroll"                 # very sassy: lids drop, roll, a head toss
            st["pose_t"] = t - k.roll0
            ru = seg(t, k.roll0, k.roll0 + CR.EYEROLL_DUR)
            st["rot"] = -0.11 * bump(ru, 0.1, 0.85) + 0.05 * bump(ru, 0.75, 1.0)   # a head toss
            st["sy"] *= 1.0 - 0.04 * bump(ru, 0.7, 1.0)          # the "hmph" shoulder drop
        elif k.roll0 + CR.EYEROLL_DUR + 0.15 <= t < k.HOOD:
            st["expr"] = "annoyed"
        if k.L2 - 0.5 <= t < k.hd0:
            st["look_target"] = "eyes"
        if k.hd0 <= t < k.hd1 + 0.1:
            st["look_target"] = "hood"
            if t >= k.hd0 + 0.3:
                st["expr"] = "annoyed"             # effort: flat focused lids
        if k.hd1 + 0.45 <= t < k.hd1 + 1.05:
            st["expr"] = "proud"                   # job done
        if t >= k.hd1 + 1.05:
            st["look_target"] = "peek" if t >= k.pk2 - 0.1 else "hood"
            if k.pk_see <= t < k.pk_close:
                st["expr"] = "annoyed"             # caught him peeking: a flat look at the eye
            elif k.pk_close <= t < k.L3 + 0.2:
                st["expr"] = "proud"               # pointedly shuts its eyes, chin up, and pulses
                st["eyes"] = 0.0
            elif t >= k.L3 + 0.2:
                st["expr"] = "hopeful"             # he gets it
        st["tail_curl"] = kf(t, [(k.hd1 + 0.4, 0.0), (k.hd1 + 0.9, 0.55), (k.pk_see, 0.55), (k.pk_see + 0.2, 0.2),
                                 (k.L3 + 0.2, 0.2), (k.L3 + 0.7, 0.7)])
        if k.dm_close <= t < k.dm_open:
            st["tail_curl"] = 0.25 * smoothstep(seg(t, k.dm_pulse, k.dm_pulse + 0.5))
        return st
    if t < k.c_sit1:                      # the hop down onto its haunches (pose switch mid-air)
        kk = seg(t, k.c_sit0, k.c_sit1)
        st["pose"] = "reach_up" if kk < 0.5 else "sit"
        st["x"] = lerp(C_XP, C_XS, ease_in_out(kk))
        st["y"] = PLINTH_Y - 34 * math.sin(math.pi * kk)
        st["sy"] = 1.0 + 0.08 * math.sin(math.pi * kk)
        st["expr"] = "hopeful"
        st["ears"] = 0.9
        st["tail_curl"] = 0.7
        st["look_target"] = "eyes"
        return st
    # ---------------- sitting on the plinth beside him
    st["x"] = C_XS
    st["pose"] = "sit"
    st["look_target"] = "eyes"
    land = seg(t, k.c_sit1, k.c_sit1 + 0.3)
    if land < 1.0:
        st["sy"] = 0.9 + 0.1 * ease_out_back(land)
    sc = seg(t, k.stand0 + 0.1, k.stand0 + 0.42)          # he stands up: it shuffles back a step
    st["x"] = lerp(C_XS, C_XS2, ease_in_out(sc))
    st["y"] = PLINTH_Y - 16 * math.sin(math.pi * sc)
    st["ears"] = kf(t, [(k.c_sit1, 0.9), (k.cut_nod, 0.85), (k.L4 + 0.9, 0.8), (k.L4e, 0.88),
                        (k.NOD - 0.1, 0.88), (k.NOD + 0.2, 0.95), (k.stand0 + 0.1, 0.95), (k.stand0 + 0.3, 0.7),
                        (k.stand0 + 0.7, 0.85), (k.L5 + 1.0, 0.75), (k.L5e - 0.6, 0.6), (k.SMUG, 0.5)])
    st["tail_curl"] = kf(t, [(k.c_sit1, 0.7), (k.cut_nod, 0.6), (k.NOD, 0.6), (k.NOD + 0.4, 0.75), (k.L5 + 1.0, 0.6),
                             (k.L5e - 0.5, 0.25), (k.SMUG, 0.15)])
    st["expr"] = "hopeful"
    if k.L4 + 0.9 <= t < k.L4e + 0.2:
        st["expr"] = "curious"                # "So I just... close my eyes?" -- it waits, head tilted
    if k.L5 + 0.5 <= t < k.L5e - 0.9:
        st["expr"] = "calm"
    if k.L5e - 0.9 <= t < k.SMUG:
        st["expr"] = "annoyed"                # his smugness wears thin
    n0 = k.n0                                 # the nod: two firm dips + a bob
    st["tilt"] = kf(t, [(n0, 0.0), (n0 + 0.28, 0.72), (n0 + 0.55, -0.08), (n0 + 0.82, 0.58), (n0 + 1.12, 0.0)])
    st["sy"] = st["sy"] - 0.035 * max(0.0, st["tilt"])
    if t < k.SMUG:
        return st
    if t < k.tgo + 0.2:
        st["expr"] = "eyeroll"
        st["pose_t"] = t - (k.SMUG + 0.12)
        st["ears"] = 0.48
        return st
    # ---------------- follows him: watches him pass, hops down, trots after him
    st["expr"] = "calm"
    if t < k.chop0:
        st["look_target"] = "eyes"
        return st
    st["look_target"] = None
    st["flip"] = True
    if t < k.chop1:
        kk = seg(t, k.chop0, k.chop1)
        st["pose"] = "stand"
        st["x"] = lerp(C_XS2, C_XS2 - 90, kk)
        st["y"] = lerp(PLINTH_Y, FEET, ease_in(kk)) - 60 * math.sin(math.pi * kk)
        st["sy"] = 1.0 + 0.1 * math.sin(math.pi * kk)
        st["look"] = (-0.8, 0.2)
        return st
    tw = t - k.chop1                      # trotting: walk cycle at 2.2x (feet planted at this speed)
    x_stop = M["stair_steps"][STEP_C][0]
    x0 = C_XS2 - 90
    x = max(x_stop, x0 - k.cv * tw)
    t_stop = k.chop1 + (x0 - x_stop) / k.cv
    st["x"] = x
    st["y"] = (stair_y(x) if x < 700 else FEET) if t < t_stop else M["stair_steps"][STEP_C][1]
    if t < t_stop:
        st["pose"] = "walk"
        st["pose_t"] = tw * 2.2
        st["look"] = (-0.8, 0.15)
        st["ears"] = kf(t, [(k.BONK, 0.7), (k.BONK + 0.12, 0.95), (k.BONK + 1.0, 0.8)])
        return st
    st["pose"] = "sit"
    st["pose_from"], st["pose_mix"] = "stand", smoothstep(seg(t, t_stop, t_stop + 0.4))
    st["look"] = (-0.8, 0.3)
    st["ears"] = 0.8
    st["expr"] = "calm"
    if t >= k.giggle0 - 0.35:
        st["pose"] = "cover_mouth"
        st["pose_t"] = t - (k.giggle0 - 0.35)
        st["pose_from"] = None
        st["expr"] = "calm"               # cover_mouth + calm = the stifled giggle
        st["ears"] = 0.7
        st["tail_curl"] = 0.6
    return st


def draw_cur(ctx, t, st, hold=None):
    x, y, sy = st["x"], st["y"], st.get("sy", 1.0)
    rot = st.get("rot", 0.0)
    sx = 1.0 / math.sqrt(max(0.5, sy))
    m0 = ctx.get_matrix()
    hold_fn = None
    if hold is not None:
        def hold_fn(c, a):
            c.save()
            c.set_matrix(m0)              # never squash / rotate what the callback draws (him)
            hold(c, a)
            c.restore()
    xf = sy != 1.0 or rot != 0.0
    if xf:
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(rot)
        ctx.scale(sx, sy)
        ctx.translate(-x, -y)
    a = CR.draw_specimen(ctx, x, y, S, t, form=1.0, pose=st["pose"], expr=st["expr"], look=st["look"],
                         glow=st["glow"], flip=st["flip"], pose_t=st["pose_t"], face=st["face"],
                         tilt=st["tilt"], ears=st["ears"], tail_curl=st["tail_curl"], reach=st["reach"],
                         blink=st["blink"], hold=hold_fn, pose_from=st["pose_from"], pose_mix=st["pose_mix"])
    if xf:
        ctx.restore()
        cr, sr = math.cos(rot), math.sin(rot)

        def tf(v):
            dx, dy = (v[0] - x) * sx, (v[1] - y) * sy
            return (x + dx * cr - dy * sr, y + dx * sr + dy * cr)
        a = {kk: (tf(v) if isinstance(v, tuple) and len(v) == 2
                  and all(isinstance(q, (int, float)) for q in v) else v) for kk, v in a.items()}
    return a


def cur_anchors(t, k, st=None):
    st = st or cur_state(t, k)
    return draw_cur(_dummy(), t, st)


def _resolve_look(cst, ta):
    """Curiosity's screen-space gaze at his hood / eyes / peeking eye (from his real anchors)."""
    lt = cst.get("look_target")
    if lt is None:
        return cst
    st = dict(cst)
    hx, hy = ta["head"]
    if lt == "hood":
        hx, hy = ta["top"][0], (ta["top"][1] + hy) / 2
    elif lt == "peek":
        hx, hy = ta.get("peek_eye") or ta["eye_r"]
    ex = st["x"] + (-55 if st["flip"] else 55)
    ey = st["y"] - {"reach_up": 250, "sit": 180}.get(st["pose"], 150)
    base = aim((ex, ey), (hx, hy), 0.85)
    if st["expr"] == "eyeroll":
        base = (base[0] * 0.5, base[1] * 0.5)
    st["look"] = base
    return st


# ---------------------------------------------------------------------------
# the sense: Curiosity's demo pulses from its head, then his pings from under the hood
# ---------------------------------------------------------------------------
_PC = {}


def pings_for(k, info):
    p = _PC.get(id(k))
    if p is not None:
        return p
    times = [(k.dm_pulse, "cur", 0.85), (k.dm_pulse2, "cur", 0.7),       # the demo ("look: eyes shut")
             (k.pk_pulse, "cur", 0.8),                                    # pointedly, at his peeking eye
             (k.p1, "tired", 1.0), (k.p2, "tired", 0.85),                 # HIS first whoom, then his head turn
             (k.w_super, "tired", 0.9),                                   # "superpower": a proud ping
             (k.tgo + 0.12, "tired", 0.55), (k.tgo + 1.12, "tired", 0.55),   # small ones guiding his steps
             (k.BONK + 0.42, "tired", 0.6)]                               # dazed, too late: there's the pipe
    out = []
    for (t0, who, kk) in times:
        if who == "cur":
            b = cur_anchors(t0, k)
            px, py = mid(b["eye_l"], b["eye_r"])
            py -= 10 * S
        else:
            a = tired_anchors(t0, k, info)
            hx, hy = a["hood_rim"] or a["head"]
            tx, ty = a["top"]
            px, py = (hx + tx) / 2, (hy * 0.6 + ty * 0.4)
        out.append((t0, px, py, kk))
    _PC.clear()
    _PC[id(k)] = out
    return out


def ping_flash(ctx, t, pings):
    """The ping flash at the source, on top of his hood / its head (the fx one sits behind)."""
    for (t0, px, py, kk) in pings:
        pc = (t - t0) / 0.5
        if not (0 <= pc < 1):
            continue
        g = 0.5 + 0.5 * kk
        a = (1 - pc) ** 1.5
        core.radial_glow(ctx, px, py, 150 * SW * g, TEAL, 0.5 * a)
        core.circle(ctx, px, py, (40 + 110 * ease_out(pc)) * SW * g)
        core.stroke(ctx, (0.75, 1.0, 0.97, 0.7 * a), 4 * SW * (1 - pc) + 1.5)


# ---------------------------------------------------------------------------
# shots
# ---------------------------------------------------------------------------
CUR_HEAD = (944, 1029)                     # Curiosity's head on its hind legs on the plinth (world)


def _shots(k):
    """[(t0, t1, name, cam(t) -> (cx, cy, zoom), sense)]"""
    T = []

    def add(t0, t1, name, cam, sense=True):
        T.append((t0, t1, name, cam, sense))
    s1_end = k.hop0 - 0.05
    c0 = S01_DARK_CAM
    add(0.0, s1_end, "dark", lambda t: (lerp(c0[0], 1030, smoothstep(seg(t, 0.0, s1_end))),
                                        lerp(c0[1], 1110, smoothstep(seg(t, 0.0, s1_end))),
                                        lerp(c0[2], 1.43, smoothstep(seg(t, 0.0, s1_end)))), False)
    add(s1_end, k.cut_fit, "climb",
        lambda t: (lerp(955, 1030, smoothstep(seg(t, k.hop1, k.hop2 + 0.5))), 1060, 1.85))
    add(k.cut_fit, k.cut_roll, "fit", lambda t: (1040, lerp(1000, 994, seg(t, k.cut_fit, k.cut_roll)), 2.3))
    add(k.cut_roll, k.HOOD, "roll", lambda t: (CUR_HEAD[0] + 10, CUR_HEAD[1] - 44, 3.0))   # plate text cropped
    add(k.HOOD, k.cut_oh, "hood",
        lambda t: (lerp(1050, 1070, smoothstep(seg(t, k.hd1, k.pk1))), 968, 2.4))   # pans to keep his hand in
    add(k.cut_oh, k.cut_nod, "oh", lambda t: (1072, 960, 2.55))
    add(k.cut_nod, k.PING, "nod", lambda t: (1040, 1060, 1.6))

    def ping_cam(t):
        # (the lit pod plate stays just above the caption band)
        return (990, lerp(1030, 1000, smoothstep(seg(t, k.stand0, k.stand1 + 0.2))), 1.15)
    add(k.PING, k.smug_cu, "ping", ping_cam)
    add(k.smug_cu, k.SMUG, "smug", lambda t: (T_X + 130, lerp(800, 785, seg(t, k.smug_cu, k.SMUG)), 2.35))
    add(k.SMUG, k.WALK, "roll2", lambda t: (C_XS2 + 60, 1090, 2.5))
    walk_end = k.BONK + 1.25

    def walk_cam(t):
        # lead room: the camera runs a little ahead of him, so the pipe comes into view
        x = T_X - k.v * clamp(t - k.tgo, 0.0, k.BONK - k.tgo)
        cx = lerp(T_X - 60, x - 90, smoothstep(seg(t, k.tgo - 0.3, k.tgo + 0.9)))
        cx = max(cx, -124.0)
        cy = lerp(1000, 1260, smoothstep(seg(x, 760, 60)))
        dx, dy = core.shake(t, k.BONK, 0.5, 14, seed=5)
        return (cx - dx / 1.3, cy - dy / 1.3, 1.3)
    add(k.WALK, walk_end, "walk", walk_cam)
    add(walk_end, k.giggle0, "bonk", lambda t: (-70, lerp(1205, 1195, seg(t, walk_end, k.giggle0)), 2.2))
    sx_, sy_ = M["stair_steps"][STEP_C]
    add(k.giggle0, k.END + 1.0, "giggle", lambda t: (sx_ + 25, sy_ - 170, 2.35))
    return T


def shot_at(k, t):
    for sh in k.shots:
        if sh[0] <= t < sh[1]:
            return sh
    return k.shots[-1]


def shot_rect(k, sh):
    """World rect covering a shot's whole camera path (for the sense bake)."""
    t0, t1, name, cam, _ = sh
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    n = 12
    for i in range(n + 1):
        cx, cy, z = cam(lerp(t0, min(t1, k.END), i / n))
        hw, hh = 540 / z + 40, 960 / z + 40
        x0, y0 = min(x0, cx - hw), min(y0, cy - hh)
        x1, y1 = max(x1, cx + hw), max(y1, cy + hh)
    return (round(x0), round(y0), round(x1 - x0), round(y1 - y0))


# ---------------------------------------------------------------------------
# light: characters in the dark, lit by Curiosity's eyes, his own glow and the pings
# ---------------------------------------------------------------------------
def _lowres(ctx, bbox, paint_fn, scale=0.25, content=cairo.FORMAT_ARGB32):
    """Render paint_fn(c) (world coords) into a quarter-res bitmap covering
    bbox and return it as a smooth pattern for the current user space.
    Soft light fields don't need full resolution: this is ~16x cheaper."""
    m = ctx.get_matrix()
    xs, ys = [], []
    for (px, py) in ((bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1]),
                     (bbox[0], bbox[1] + bbox[3]), (bbox[0] + bbox[2], bbox[1] + bbox[3])):
        dx, dy = ctx.user_to_device(px, py)
        xs.append(dx)
        ys.append(dy)
    x0, y0 = math.floor(min(xs)), math.floor(min(ys))
    w = max(2, int(math.ceil((max(xs) - x0) * scale)) + 2)
    h = max(2, int(math.ceil((max(ys) - y0) * scale)) + 2)
    surf = cairo.ImageSurface(content, w, h)
    c = cairo.Context(surf)
    c.scale(scale, scale)
    c.translate(-x0, -y0)
    c.transform(m)
    pm = c.get_matrix()
    paint_fn(c)
    surf.flush()
    pat = cairo.SurfacePattern(surf)
    pat.set_matrix(pm)
    pat.set_filter(cairo.FILTER_BILINEAR)
    pat.set_extend(cairo.EXTEND_PAD)
    return pat


def _radial(c, x, y, r, rgb, a, mid_=0.62):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *rgb, a)
    g.add_color_stop_rgba(0.4, *rgb, a * mid_)
    g.add_color_stop_rgba(1, *rgb, 0)
    c.set_source(g)
    c.arc(x, y, r, 0, 2 * math.pi)
    c.fill()


def light_chars(ctx, draw_fn, lights_fn, base=0.9, bbox=None):
    """Draw the characters into a group, darken them ATOP with a mask that
    has soft holes at the light sources, then tint teal near them. `bbox`
    (world rect) clips the group: the cost scales with its area."""
    if bbox is not None:
        ctx.save()
        ctx.rectangle(*bbox)
        ctx.clip()
    ctx.push_group()
    info = draw_fn(ctx)
    lights, tints = lights_fn(info)
    bb = bbox or (-2000, -2000, 8000, 8000)

    def mask_fn(c):
        c.set_source_rgba(0, 0, 0, base)
        c.paint()
        c.set_operator(cairo.OPERATOR_DEST_OUT)
        for (x, y, r, a) in lights:
            if a > 0.01 and r > 1:
                _radial(c, x, y, r, (0, 0, 0), a)

    def tint_fn(c):
        for (x, y, r, a) in tints:
            if a > 0.01 and r > 1:
                _radial(c, x, y, r, TEAL, a, 0.5)
    mask = _lowres(ctx, bb, mask_fn)
    tint = _lowres(ctx, bb, tint_fn) if any(a > 0.01 for (_, _, _, a) in tints) else None
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source_rgba(*DARK_RGB, 1.0)
    ctx.mask(mask)
    if tint is not None:
        ctx.set_source(tint)
        ctx.paint()
    ctx.pop_group_to_source()
    ctx.paint()
    if bbox is not None:
        ctx.restore()
    return info


def char_bbox(tst, cst, ta):
    """World rect around both characters (clips the light groups)."""
    tx, ty = tst["x"], tst["y"]
    top = ta["top"][1]
    rects = [(tx - 300, top - 120, 600, ty - top + 200), (cst["x"] - 330, cst["y"] - 520, 660, 600)]
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def aim(src, dst, mag=0.85):
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    d = math.hypot(dx, dy) or 1.0
    return (dx / d * mag, dy / d * mag)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def deep_dark(t, k, name):
    """Extra darkness over the set (s01 ends under a 0.62 wash; our eyes adjust a little)."""
    if name == "dark":
        return lerp(0.62, 0.45, smoothstep(seg(t, 0.4, k.hop0)))
    return 0.4


def dark_set(c, t, k, deep, rail=False):
    # the pipe shivers after the bonk (it has died out by the cut to the close-up)
    sets.catwalk(c, t, power=0.0, cam_led=1.0, pipe_wobble=1.0 if 0.0 <= t - k.BONK < 1.25 else 0.0,
                 pipe_wobble_t0=k.BONK, **SET_KW)
    if rail:     # in sense shots the deck rail sits in the dark world (the echo reveals it)
        sets.catwalk(c, t, layer="fg", power=0.0, parts=("rail",))
    if deep > 0.005:
        c.set_source_rgba(*DARK_RGB, deep)
        c.paint()


def lit_set(c):
    sets.catwalk(c, 0.0, lit=True, cam_led=0.0, **SET_KW)
    sets.catwalk(c, 0.0, layer="fg", lit=True)


CLOSE = ("fit", "hood", "oh", "smug", "bonk", "roll")


def render(ctx, t, info):
    k = timing(info)
    pings = pings_for(k, info)
    sh = shot_at(k, t)
    t0, t1, name, cam, sense = sh
    cx, cy, zoom = cam(t)
    tst = tired_state(t, k, info)
    ta = tired_anchors(t, k, info, tst)            # where his head is (Curiosity's gaze, bbox)
    if tst.get("peek_geo"):                        # its gaze needs the peeking eye's real spot
        ta = dict(ta)
        ta["peek_eye"] = tst["peek_geo"]["eye_b"]
    cst = _resolve_look(cur_state(t, k), ta)
    deep = deep_dark(t, k, name)
    post = 0.0
    if name == "dark":           # as in s01: one near-black wash over set, characters and rail
        post, deep = deep, 0.0
    core.bg(ctx, "#03070b")
    with core.camera(ctx, cx, cy, zoom):
        # ---- the world: darkness + the sense
        if sense and fx.sense_active(t, pings, s=SW):
            fx.sense_reveal(ctx, t, pings, lit_set, lambda c: dark_set(c, t, k, deep, True), key=("s02", name),
                            rect=shot_rect(k, sh), s=SW)
        else:
            dark_set(ctx, t, k, deep)

        # ---- characters: Curiosity behind (on the plinth / following), him in front;
        #      in reach_up he is drawn inside its pose so its near paw lands on his hood
        def draw_chars(c):
            res = {}
            if cst["pose"] == "reach_up":
                def hold(cc, a):
                    res["t"] = draw_tired(cc, t, tst)
                res["c"] = draw_cur(c, t, cst, hold=hold)
                if "t" not in res:
                    res["t"] = draw_tired(c, t, tst)
            else:
                res["c"] = draw_cur(c, t, cst)
                res["t"] = draw_tired(c, t, tst)
            return res

        close = name in CLOSE

        def lights_fn(res):
            a, b = res["t"], res["c"]
            L, Tn = [], []
            ce = mid(b["eye_l"], b["eye_r"])
            eo = cst.get("eyes", 1.0)
            if name == "dark":
                L.append((ce[0], ce[1], 90, 0.3))
            else:
                # its open eyes light the faces; shut, only its soft teal halo is left
                L += [(b["eye_l"][0], b["eye_l"][1], 30, eo), (b["eye_r"][0], b["eye_r"][1], 30, eo),
                      (ce[0], ce[1], 250, lerp(0.5, 0.62, eo))]
                Tn.append((ce[0], ce[1], 330, lerp(0.16, 0.2, eo)))
            hood = tst["hood"]
            if hood < 0.6 and name != "dark":
                for e in ("eye_l", "eye_r"):          # his teal irises glow (not the skin around)
                    L.append((a[e][0], a[e][1], 15, 0.75 * (1 - hood / 0.6)))
                    Tn.append((a[e][0], a[e][1], 26, 0.3 * (1 - hood / 0.6)))
            if a.get("peek_eye") and tst.get("peek", 0.0) > 0.3:     # the one peeking eye glints
                ex, ey = a["peek_eye"]
                pk = clamp((tst["peek"] - 0.3) / 0.5)
                L.append((ex, ey, 26, 0.7 * pk))
                Tn.append((ex, ey, 34, 0.3 * pk))
            if a.get("hood_rim") and hood > 0.5:
                hx, hy = a["hood_rim"]
                hk = seg(hood, 0.5, 1.0)
                L.append((hx, hy + 14, 115 if close else 85, (0.55 if close else 0.42) * hk))
                Tn.append((hx, hy + 10, 130, 0.25 * hk))
            # the BONK! burst flashes light on him for a moment (the hit reads in the dark)
            if 0.0 <= t - k.BONK < 0.6:
                fl = 1 - seg(t, k.BONK, k.BONK + 0.6)
                L.append((PIPE[0] + 20, PIPE[1] + 60, 520, 0.75 * fl))
                Tn.append((PIPE[0] + 20, PIPE[1] + 60, 300, 0.12 * fl))
            # the pings light whoever the band passes
            for an, cxy in ((a, a["hip"]), (b, b["center"])):
                hx, hy = an["head"]
                sx_, sy_ = (cxy[0] + hx) / 2, (cxy[1] + hy) / 2
                sa = fx.sense_at(t, pings, sx_, sy_, s=SW) if sense else 0.0
                if sa > 0.01:
                    L.append((sx_, sy_, 480, 0.6 * sa))
                    Tn.append((sx_, sy_, 480, 0.22 * sa))
            return L, Tn

        res = light_chars(ctx, draw_chars, lights_fn, base=0.86 if name == "dark" else 0.9,
                          bbox=char_bbox(tst, cst, ta))
        # foreground: the deck rail in front of them (no-ping shots, as in s01) and the
        # stair stringer + handrail over legs on the stair
        if not sense:
            sets.catwalk(ctx, t, layer="fg", power=0.0, parts=("rail",))
        elif not fx.sense_active(t, pings, s=SW):
            sets.catwalk(ctx, t, layer="fg", power=0.0, parts=("rail",))
        if name in ("walk", "giggle"):
            sets.catwalk(ctx, t, layer="fg", power=0.0, parts=("stair",))
        # the opening: the same near-black wash as s01's last frame, then the two pairs of eyes
        if name == "dark":
            a, b = res["t"], res["c"]
            ctx.set_source_rgba(*DARK_RGB, post)
            ctx.paint()
            te = mid(a["eye_l"], a["eye_r"])
            tdist = math.hypot(a["eye_r"][0] - a["eye_l"][0], a["eye_r"][1] - a["eye_l"][1])
            ts_ = S * 1.25
            bt = tst["blink"] if tst["blink"] is not None else a.get("blink", 0.0)
            fx.eyes_in_dark(ctx, te[0], te[1], ts_, t, "tired", blink=bt, gap=tdist / ts_,
                            look=(tst["look"][0] * 0.5, tst["look"][1] * 0.5), amount=0.9, seed=5)
            ce = mid(b["eye_l"], b["eye_r"])
            cdist = math.hypot(b["eye_r"][0] - b["eye_l"][0], b["eye_r"][1] - b["eye_l"][1])
            cs = S * 0.95
            lk = cst["look"] or (0.5, -0.5)
            fx.eyes_in_dark(ctx, ce[0], ce[1], cs, t, "curiosity", look=(lk[0] * 0.6, lk[1] * 0.6),
                            gap=cdist / cs, tilt=-0.12 if cst["expr"] == "curious" else 0.0, seed=3)
        if sense:
            ping_flash(ctx, t, pings)
        # ---- the bonk
        if t >= k.BONK:
            a = res["t"]
            fx.bonk_star(ctx, PIPE[0] - 14, PIPE[1] + 22, 0.95, t, k.BONK, dur=0.75)
            hx, hy = a["top"]
            fx.dizzy_stars(ctx, hx + 8, hy + 6, 0.55, t, t0=k.BONK + 0.3, dur=2.2)


# ---------------------------------------------------------------------------
# sound
# ---------------------------------------------------------------------------
def SFX(info):
    k = timing(info)
    ev = []
    # he steps back and sits on the plinth (cloth + a soft bump)
    ev.append((k.sit0 + 0.15, "cloth_rustle", 0, 0.1))
    ev.append((k.sit0 + 0.7, "body_thud", -12, 0.1))
    # Curiosity hops up: claws, a soft landing, a curious chitter as it looks at him
    ev.append((k.hop1 - 0.02, "scratch_wood", -4, -0.25))
    ev.append((k.hop2, "footstep", -9, -0.2))
    ev.append((k.hop2 + 0.45, "creature_chitter", -7, -0.2))
    # the demo: a concentrating purr under the tremble, then its own (smaller) pulses
    ev.append((k.dm_charge - 0.25, "creature_purr", -7, -0.2))
    ev.append((k.dm_charge2 - 0.2, "creature_purr", -13, -0.2))
    # the eye-roll: ears flick, then the hood: cloth, his sigh
    ev.append((k.roll0 + 0.7, "ears_perk", -6, -0.2))
    ev.append((k.hd0, "cloth_rustle", 2, 0.0))
    ev.append((k.sigh - 0.05, "sigh", 1, 0.1))
    # the peek: the rim lifted, caught (its ears), the rim dropping again
    ev.append((k.pk1 - 0.05, "cloth_rustle", -9, 0.1))
    ev.append((k.pk_see + 0.05, "ears_perk", -3, -0.2))
    ev.append((k.dr0, "cloth_rustle", -7, 0.1))
    ev.append((k.c_sit1 - 0.02, "footstep", -13, -0.25))         # it hops down onto its haunches
    # the sense: its pulses small, his first ones the big signature whoom
    pings = pings_for(k, info)
    for i, (t0, x, y, kk) in enumerate(pings):
        if i < 3:
            ev.append((t0, "sonar_ping_small", -1 if i != 1 else -7, -0.15))
        elif kk >= 0.75:
            ev.append((t0, "sonar_ping", 0 if i == 3 else -3, 0.0))
        else:
            ev.append((t0, "sonar_ping_small", -4 if t0 < k.BONK else -2, 0.0))
    # "Oh." -> its ears perk; the nod
    ev.append((k.L3 + 0.25, "ears_perk", 0, -0.2))
    ev.append((k.n0 + 0.25, "ears_perk", 2, -0.2))
    # stands up
    ev.append((k.stand0 + 0.2, "cloth_rustle", -2, 0.1))
    ev.append((k.stand0 + 0.42, "footstep", -15, -0.25))         # it shuffles back a step
    # the confident stride: one step per heel strike of walk_eyes_closed (pose_t 0.17 + n * 0.525)
    per = 1.05 / 2
    tt = k.tgo + 0.17
    i = 0
    while tt < k.BONK - 0.05:
        ev.append((tt, "footstep", -3 if i % 2 else -5, -0.1))
        tt += per
        i += 1
    # Curiosity hops down + trots after him
    ev.append((k.chop1, "footstep", -10, 0.3))
    ev.append((k.chop1 + 0.1, "scurry", -12, 0.3))
    # BONK
    ev.append((k.BONK, "pipe_bonk", 2, -0.15))
    # the stifled giggle behind its paw
    ev.append((k.giggle0 + 0.05, "creature_chitter", -5, 0.2))
    return ev


# Director: lift the deep shadows a little so the dark reads on a phone screen
# (applied when the segment is encoded; previews/sheets show the raw render).
POST_FILTER = "curves=all='0/0 0.06/0.115 0.2/0.30 0.5/0.6 1/1'"
