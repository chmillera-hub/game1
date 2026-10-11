"""s02 -- "Close your eyes" (TIREDNESS Ep2: Lights Out).

Pitch dark on the shaft catwalk (continues s01's last frame: Curiosity's big
eyes low-left at its empty pod, Tiredness's faint eyes high-right). He gives up
and sits on the plinth of the empty pod; Curiosity hops up beside him and tugs
his hood over his eyes. Eyes closed, his new sense pings the world into teal.
Smug, he strides off down the stair... and walks face-first into a low pipe.

All timing comes from info.cue()/info.line(); nothing is hard-coded to the
audio. Shots (scene-local):
  S1  dark ....... two pairs of eyes, l01, he sits down (eyes drop)
  S2  climb ...... Curiosity hops up beside him on hind legs, reaches; l02
  S3  hood ....... CU: the hood comes up and over his eyes; annoyance; sigh
  S4  ping ....... wide: silence, whoom, the first rings reveal the catwalk
  S5  look ....... "Oh." (brows lift under the hood); head turns L / R, pings follow
  S6  nod ........ "So I just... close my eyes?" -- Curiosity nods, revealed by a ping
  S7  stand ...... he stands up proud on "Finally."
  S7b smug ....... CU "A superpower I'm actually good at." (+ a proud ping)
  S8  roll ....... CU Curiosity's slow sassy eye-roll
  S9  walk ....... tracking: confident stride, pings, down the stair -> BONK
  S10 bonk ....... CU held beat, dazed: "...Mostly good at."
  S11 giggle ..... CU Curiosity on the stair hides its smile behind a paw
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
C_XS = 872                                 # ... and sits back on it here once it lets go of the hood
FEET = M["feet_y"]                         # 1500
LAND = M["landing_feet_y"]                 # 1770
BONK_X = M["bonk_feet"][0]                 # -44: feet x when his face meets the pipe
PIPE = M["bonk_pipe"]                      # (-90, 1150) contact point
ST_TOP_X, ST_RUN, ST_RISE = 640, 86, 45
STEP_C = 2                                 # the stair tread Curiosity stops on (giggle)
DARK_RGB = (0.012, 0.027, 0.043)
TEAL = (0.247, 0.949, 0.878)
S01_DARK_CAM = (1010, 1105, 1.35)          # s01's last framing (lights out, two pairs of eyes)


def _sleeper(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s, t, seed=seed)


def _baby(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s * 1.6, t, seed=seed, baby=True)


# same set state as the end of s01: plate wiped clean, camera swivelled to them, LED on
SET_KW = dict(sleeper_fn=_sleeper, sleeper_fns={"JOY": _baby}, sleeper_key="s02_sleepers",
              cam_face=1.0, cam_angle=0.37, plate_dust=1.0, plate_wipe=1.0)


def kf(t, keys, ease=ease_in_out):
    return tween(t, keys, ease)


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
    k.L2, k.L2e = L("s02_l02").start, L("s02_l02").end
    k.HOOD = c("hood")
    k.PING = c("ping")
    k.L3, k.L3e = L("s02_l03").start, L("s02_l03").end
    k.LOOK = c("look")
    k.L4, k.L4e = L("s02_l04").start, L("s02_l04").end
    k.NOD = c("nod")
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
    # "look": head left, hold, right, hold (the pings follow the head)
    k.lk1 = k.L3e + 0.95
    k.lk2 = k.lk1 + 0.3
    k.lk3 = k.lk2 + 0.8
    # Tiredness sits down right after l01 (a step back onto the plinth)
    k.sit0 = k.L1e + 0.12
    k.sit1 = k.sit0 + 0.85
    # Curiosity hops up onto the plinth beside him
    k.hop0 = max(k.sit1 + 0.12, k.NUDGE + 0.35)      # anticipation crouch starts
    k.hop1 = k.hop0 + 0.22                            # take-off
    k.hop2 = k.hop1 + 0.30                            # lands on its hind legs
    # the hood pull
    k.hd0 = k.HOOD + 0.12
    k.hd1 = k.hd0 + 0.85                              # hood fully over his eyes
    k.sigh = k.hd1 + 0.55
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
    k.chop0 = k.tgo + (T_X - (C_XS - 150)) / k.v
    k.chop1 = k.chop0 + 0.36
    k.cv = 2.2 * CR.SPEC_WALK_SPEED * S
    # post-bonk
    k.giggle0 = k.L6e + 0.25
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
    """sit_crate with an animated slump: slumped -> straighter after "Oh."."""
    up = smoothstep(seg(t, k.L3 - 0.12, k.L3 + 0.35))
    lift2 = kf(t, [(k.L2 - 0.4, 0.0), (k.L2 + 0.1, 0.45), (k.HOOD + 0.4, 0.45), (k.hd1 + 0.15, 0.1),
                   (k.sigh + 0.2, 0.0)])
    ping_lift = kf(t, [(k.PING + 0.5, 0.0), (k.PING + 0.9, 0.25), (k.PING + 1.6, 0.25),
                       (k.PING + 2.0, 0.45)])
    a = max(lift2, ping_lift * (1 - up))
    lean = lerp(lerp(0.5, 0.36, a), 0.22, up)
    nod = lerp(lerp(0.34, 0.12, a), 0.0, up)
    neck = lerp(0.32, 0.2, max(a, up))
    sg = math.sin(math.pi * seg(t, k.sigh - 0.1, k.sigh + 0.9))     # sigh: shoulders drop
    return {"base": "sit_crate", "lean": lean + 0.05 * sg, "nod": nod + 0.06 * sg, "neck": neck,
            "hunch": 0.65 + 0.2 * sg}


PROUD = {"base": "stand", "chest": -0.1, "nod": -0.12, "neck": -0.08, "posture": 0.4, "hunch": 0.1}


def tired_state(t, k, info):
    st = dict(x=T_X, y=FEET, pose="stand", pose_t=None, turn=0.25, expr="bored", face={},
              look=(0.0, 0.0), blink=None, hood=0.0, mouth=info.mouth("tired", t))
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
        st["pose"] = sit_pose(t, k)
        # (body turn stays > -0.2: below that the clasped hands swap draw order)
        st["turn"] = kf(t, [(k.L3e + 0.35, 0.25), (k.lk1 + 0.1, -0.1), (k.lk2, -0.1),
                            (k.lk3 + 0.1, 0.62), (k.L4, 0.62), (k.L4 + 0.6, 0.15)])
        st["expr"] = state_at(t, [(0.0, "bored"), (k.L2 - 0.1, "annoyed"), (k.hd0 + 0.25, "annoyed"),
                                  (k.sigh - 0.1, "sigh"), (k.sigh + 0.9, "bored"), (k.PING + 1.9, "neutral"),
                                  (k.L3 - 0.1, "surprised"), (k.L3e + 0.35, "neutral"),
                                  (k.L4 - 0.15, "curious"), (k.L4e + 0.2, "neutral")], 0.25)
        # eyes (before the hood): Curiosity lands on his LEFT -> pupils lead, head follows ~0.15 s later
        st["look"] = kf(t, [(k.sit1, (0.1, 0.2)), (k.hop2 - 0.05, (0.1, 0.15)), (k.hop2 + 0.15, (-0.85, -0.1)),
                            (k.L2 + 0.6, (-0.85, -0.15)), (k.L2e, (-0.75, -0.3)),
                            (k.hd0 - 0.05, (-0.7, -0.3)), (k.hd0 + 0.25, (-0.25, -0.9))])
        f["head_turn"] = kf(t, [(k.hop2 + 0.15, 0.0), (k.hop2 + 0.45, -0.42), (k.HOOD, -0.42),
                                (k.hd0 + 0.3, -0.12), (k.hd1 + 0.2, 0.0), (k.PING + 1.0, 0.0),
                                (k.PING + 1.4, -0.1),
                                (k.L3e + 0.3, -0.1), (k.lk1, -0.8), (k.lk2, -0.8),       # look left ...
                                (k.lk3, 0.75), (k.L4 - 0.05, 0.75),                      # ... and right
                                (k.L4 + 0.55, -0.45), (k.L5, -0.4)])                     # back to it
        f["head_tilt"] = kf(t, [(k.L2, 0.0), (k.L2 + 0.4, 0.06), (k.L2e, 0.06), (k.HOOD, 0.0),
                                (k.L3e + 0.3, 0.0), (k.lk1, 0.08), (k.lk2, 0.08),
                                (k.lk3, -0.08), (k.L4 + 0.5, 0.0),
                                (k.L4 + 0.9, 0.0), (k.L4 + 1.3, -0.1), (k.L4e + 0.6, -0.1), (k.NOD + 1.2, -0.03)])
        f["brow_l"] = kf(t, [(k.L2 + 0.2, 0.0), (k.L2 + 0.5, 0.25), (k.hd0, 0.25), (k.hd0 + 0.3, 0.0)])
        st["hood"] = kf(t, [(k.hd0, 0.0), (k.hd0 + 0.38, 0.45), (k.hd1, 1.0)])
        # the yank nods his head forward; he lifts it a hair at the first ping; settles after "Oh."
        f["head_nod"] = (0.2 * math.sin(math.pi * seg(t, k.hd1 - 0.3, k.hd1 + 0.4))
                         - 0.06 * smoothstep(seg(t, k.PING + 0.6, k.PING + 1.0))
                         + 0.06 * smoothstep(seg(t, k.L3e + 0.3, k.L3e + 0.8)))
        f["press"] = kf(t, [(k.hd0, 0.0), (k.hd0 + 0.3, 0.55), (k.sigh - 0.15, 0.55), (k.sigh, 0.0),
                            (k.sigh + 0.9, 0.0), (k.sigh + 1.2, 0.2), (k.PING + 0.5, 0.2),
                            (k.PING + 0.7, 0.0), (k.L4e + 0.3, 0.0), (k.L4e + 0.6, 0.25), (k.L5, 0.25)])
        f["open"] = kf(t, [(k.PING + 0.55, 0.0), (k.PING + 0.8, 0.12), (k.PING + 1.65, 0.12),
                           (k.PING + 1.9, 0.22), (k.L3 - 0.1, 0.22), (k.L3, 0.0),
                           (k.L3e + 0.1, 0.0), (k.L3e + 0.3, 0.12), (k.lk3 + 0.2, 0.12), (k.L4 - 0.1, 0.0)])
        f["frown"] = kf(t, [(k.hd0 + 0.1, 0.0), (k.hd0 + 0.4, 0.35), (k.sigh, 0.35), (k.sigh + 0.5, 0.1),
                            (k.PING + 0.5, 0.1), (k.PING + 0.8, 0.0)])
        f["smirk"] = kf(t, [(k.NOD + 1.0, 0.0), (k.NOD + 1.35, 0.18)])    # "hm." -- he got the nod
        return st
    # ---------------- stands up into l05, proud; then turns and walks
    st["hood"] = 1.0
    if t < k.turn0:
        st["y"] = T_GSEAT
        kk = seg(t, k.stand0, k.stand1)
        sp = sit_pose(t, k)
        sp = dict(sp, lean=sp["lean"] + 0.18 * math.sin(math.pi * seg(kk, 0.0, 0.45)))   # lean in, push up
        st["pose"] = (sp, PROUD, smoothstep(seg(kk, 0.25, 1.0)))
        st["turn"] = lerp(0.15, 0.1, smoothstep(kk))
        f["head_turn"] = lerp(-0.4, 0.12, smoothstep(seg(kk, 0.2, 1.0)))       # chin up, away from it
        st["expr"] = "deadpan"
        sm = smoothstep(seg(t, k.w_actually - 0.1, k.w_actually + 0.5))
        f["smirk"] = 0.18 + 0.32 * sm
        f["curve"] = 0.15 * sm
        f["head_tilt"] = kf(t, [(k.stand1, 0.0), (k.stand1 + 0.4, 0.05)])
        f["head_nod"] = -0.04 * smoothstep(seg(t, k.L5 + 0.4, k.L5 + 0.9))
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


def draw_tired(ctx, t, st):
    return human.draw_person(ctx, "tired", st["x"], st["y"], S, t, pose=st["pose"], pose_t=st["pose_t"],
                             turn=st["turn"], expr=st["expr"], face=st["face"], look=st["look"],
                             mouth=st["mouth"], blink=st["blink"], hood=st["hood"], power=0.6,
                             outfit="sewer", bandage=True, headphones=None, shadow=False)


_DUMMY = None


def tired_anchors(t, k, info, st=None):
    """Anchors of Tiredness at time t without drawing to the frame."""
    global _DUMMY
    if _DUMMY is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        _DUMMY = cairo.Context(surf)
        _DUMMY.scale(0.002, 0.002)
    return draw_tired(_DUMMY, t, st or tired_state(t, k, info))


# ---------------------------------------------------------------------------
# Curiosity
# ---------------------------------------------------------------------------
def cur_state(t, k):
    st = dict(x=C_X0, y=FEET, pose="sit", flip=False, expr="calm", look=(0.6, -0.55), face=None,
              tilt=0.0, ears=0.6, tail_curl=0.0, reach=0.0, pose_t=None, glow=1.0, blink=None,
              sy=1.0, pose_from=None, pose_mix=1.0, look_target=None)
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
    # ---------------- up on its hind legs beside him: reaches, pokes his hair, yanks the hood
    st["x"], st["y"] = C_XP, PLINTH_Y
    if t < k.PING:
        st["pose"] = "reach_up"
        land = seg(t, k.hop2, k.hop2 + 0.32)
        st["sy"] = 0.84 + 0.16 * ease_out_back(land) if land < 1 else 1.0
        poke = 0.05 * math.sin((t - k.hop2) * 6.0) * seg(t, k.hop2 + 0.9, k.hop2 + 1.2) * (1 - seg(t, k.L2 - 0.2, k.L2))
        r = kf(t, [(k.hop2, 0.0), (k.hop2 + 0.25, 0.05), (k.hop2 + 0.85, 0.86), (k.L2 - 0.1, 0.86),
                   (k.L2 + 0.05, 0.8), (k.L2e, 0.84), (k.hd0 - 0.1, 0.9),
                   # grab high (1.0), then yank down / forward over his eyes (0.42)
                   (k.hd0 + 0.25, 1.0), (k.hd0 + 0.4, 1.0), (k.hd1, 0.42), (k.hd1 + 0.25, 0.5),
                   (k.hd1 + 0.6, 0.12)])
        st["reach"] = clamp(r + poke)
        st["x"] = C_XP + kf(t, [(k.hd0 + 0.35, -4.0), (k.hd1, 30.0), (k.hd1 + 0.6, 0.0)])
        st["tilt"] = kf(t, [(k.hd0 + 0.3, -0.1), (k.hd1 - 0.1, 0.22), (k.hd1 + 0.5, 0.0)])
        st["ears"] = kf(t, [(k.hop2, 0.85), (k.hop2 + 0.6, 0.75), (k.L2, 0.75), (k.L2 + 0.15, 0.6),
                            (k.L2e, 0.65), (k.hd0, 0.75), (k.hd1 + 0.6, 0.78)])
        st["expr"] = "calm"
        if k.L2 + 0.05 <= t < k.hd0:
            st["expr"] = "curious"
        if k.hd0 + 0.3 <= t < k.hd1 + 0.1:
            st["expr"] = "annoyed"        # effort: flat focused lids
        if t >= k.hd1 + 0.5:
            st["expr"] = "proud"
        st["tail_curl"] = kf(t, [(k.hd1 + 0.4, 0.0), (k.hd1 + 0.9, 0.65)])
        st["look_target"] = "hood" if t < k.L2 else ("eyes" if t < k.hd0 else "hood")
        return st
    # ---------------- sitting on the plinth beside him
    st["x"] = C_XS
    st["pose"] = "sit"
    st["look_target"] = "eyes"
    st["ears"] = kf(t, [(k.PING, 0.72), (k.L3, 0.72), (k.L3 + 0.2, 0.88), (k.LOOK + 0.5, 0.8),
                        (k.NOD - 0.1, 0.8), (k.NOD + 0.2, 0.9), (k.L5 + 1.0, 0.75), (k.L5e - 0.6, 0.6),
                        (k.SMUG, 0.5)])
    st["tail_curl"] = kf(t, [(k.PING, 0.4), (k.L3, 0.4), (k.L3 + 0.4, 0.75), (k.L5 + 1.0, 0.6),
                             (k.L5e - 0.5, 0.25), (k.SMUG, 0.15)])
    st["expr"] = "calm"
    if k.L3 - 0.05 <= t < k.L3e + 0.6:
        st["expr"] = "surprised_soft"
    if k.NOD - 0.05 <= t < k.L5 + 0.5:
        st["expr"] = "hopeful"
    if k.L5e - 0.9 <= t < k.SMUG:
        st["expr"] = "annoyed"            # his smugness wears thin
    n0 = k.NOD + 0.3                      # the nod (revealed by a ping): two firm dips + a bob
    st["tilt"] = kf(t, [(n0, 0.0), (n0 + 0.3, 0.72), (n0 + 0.6, -0.08), (n0 + 0.9, 0.58), (n0 + 1.25, 0.0)])
    st["sy"] = 1.0 - 0.035 * max(0.0, st["tilt"])
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
        st["x"] = lerp(C_XS, C_XS - 90, kk)
        st["y"] = lerp(PLINTH_Y, FEET, ease_in(kk)) - 60 * math.sin(math.pi * kk)
        st["sy"] = 1.0 + 0.1 * math.sin(math.pi * kk)
        st["look"] = (-0.8, 0.2)
        return st
    tw = t - k.chop1                      # trotting: walk cycle at 2.2x (feet planted at this speed)
    x_stop = M["stair_steps"][STEP_C][0]
    x0 = C_XS - 90
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
    sx = 1.0 / math.sqrt(max(0.5, sy))
    m0 = ctx.get_matrix()
    hold_fn = None
    if hold is not None:
        def hold_fn(c, a):
            c.save()
            c.set_matrix(m0)              # never squash what the callback draws (him)
            hold(c, a)
            c.restore()
    if sy != 1.0:
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(sx, sy)
        ctx.translate(-x, -y)
    a = CR.draw_specimen(ctx, x, y, S, t, form=1.0, pose=st["pose"], expr=st["expr"], look=st["look"],
                         glow=st["glow"], flip=st["flip"], pose_t=st["pose_t"], face=st["face"],
                         tilt=st["tilt"], ears=st["ears"], tail_curl=st["tail_curl"], reach=st["reach"],
                         blink=st["blink"], hold=hold_fn, pose_from=st["pose_from"], pose_mix=st["pose_mix"])
    if sy != 1.0:
        ctx.restore()
        a = {kk: ((x + (v[0] - x) * sx, y + (v[1] - y) * sy) if isinstance(v, tuple) and len(v) == 2
                  and all(isinstance(q, (int, float)) for q in v) else v) for kk, v in a.items()}
    return a


def _resolve_look(cst, ta):
    """Curiosity's screen-space gaze at his hood / eyes (from his real anchors)."""
    lt = cst.get("look_target")
    if lt is None:
        return cst
    st = dict(cst)
    hx, hy = ta["head"]
    if lt == "hood":
        hx, hy = ta["top"][0], (ta["top"][1] + hy) / 2
    ex = st["x"] + (-55 if st["flip"] else 55)
    ey = st["y"] - {"reach_up": 250, "sit": 180}.get(st["pose"], 150)
    base = aim((ex, ey), (hx, hy), 0.85)
    if st["expr"] == "eyeroll":
        base = (base[0] * 0.5, base[1] * 0.5)
    st["look"] = base
    return st


# ---------------------------------------------------------------------------
# the sense: pings from his head
# ---------------------------------------------------------------------------
_PC = {}


def pings_for(k, info):
    p = _PC.get(id(k))
    if p is not None:
        return p
    times = [(k.PING + 0.45, 1.0), (k.PING + 1.6, 0.85),        # the first whoom, a second
             (k.lk1 - 0.1, 0.8), (k.lk3 - 0.05, 0.8),           # following his head L / R
             (k.NOD + 0.05, 0.75),                              # reveals the nod
             (k.w_super, 0.9),                                  # "superpower": a proud ping
             (k.tgo + 0.12, 0.55), (k.tgo + 1.12, 0.55),        # small ones guiding his steps
             (k.BONK + 0.42, 0.6)]                              # dazed, too late: there's the pipe
    out = []
    for (t0, kk) in times:
        a = tired_anchors(t0, k, info)
        hx, hy = a["hood_rim"] or a["head"]
        tx, ty = a["top"]
        out.append((t0, (hx + tx) / 2, (hy * 0.6 + ty * 0.4), kk))
    _PC.clear()
    _PC[id(k)] = out
    return out


def ping_flash(ctx, t, pings):
    """The ping flash at the source, on top of his hood (the fx one sits behind him)."""
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
    add(s1_end, k.HOOD, "climb", lambda t: (lerp(955, 1035, smoothstep(seg(t, k.hop1, k.hop2 + 0.5))), 1060, 1.85),
        False)
    add(k.HOOD, k.PING, "hood", lambda t: (1050, 1000, lerp(2.4, 2.55, smoothstep(seg(t, k.HOOD, k.PING)))),
        False)
    add(k.PING, k.L3 - 0.15, "ping", lambda t: (990, 900, 1.15))
    add(k.L3 - 0.15, k.L4 - 0.1, "look", lambda t: (1095, 1020, 1.75))
    add(k.L4 - 0.1, k.stand0 - 0.05, "nod", lambda t: (1040, 1060, 1.6))
    add(k.stand0 - 0.05, k.smug_cu, "stand",
        lambda t: (1045, lerp(1060, 990, smoothstep(seg(t, k.stand0, k.stand1 + 0.2))), 1.4))
    add(k.smug_cu, k.SMUG, "smug", lambda t: (T_X + 130, lerp(800, 785, seg(t, k.smug_cu, k.SMUG)), 2.35))
    add(k.SMUG, k.WALK, "roll", lambda t: (C_XS + 60, 1090, 2.5))
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


def render(ctx, t, info):
    k = timing(info)
    pings = pings_for(k, info)
    sh = shot_at(k, t)
    t0, t1, name, cam, sense = sh
    cx, cy, zoom = cam(t)
    tst = tired_state(t, k, info)
    ta = tired_anchors(t, k, info, tst)            # where his head is (Curiosity's gaze, bbox)
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

        close = name in ("hood", "look", "smug", "bonk")

        def lights_fn(res):
            a, b = res["t"], res["c"]
            L, Tn = [], []
            ce = mid(b["eye_l"], b["eye_r"])
            if name == "dark":
                L.append((ce[0], ce[1], 90, 0.3))
            else:
                L += [(b["eye_l"][0], b["eye_l"][1], 30, 1.0), (b["eye_r"][0], b["eye_r"][1], 30, 1.0),
                      (ce[0], ce[1], 250, 0.62)]
                Tn.append((ce[0], ce[1], 330, 0.2))
            hood = tst["hood"]
            if hood < 0.6 and name != "dark":
                for e in ("eye_l", "eye_r"):          # his teal irises glow (not the skin around)
                    L.append((a[e][0], a[e][1], 15, 0.75 * (1 - hood / 0.6)))
                    Tn.append((a[e][0], a[e][1], 26, 0.3 * (1 - hood / 0.6)))
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
    # Curiosity hops up: claws, a soft landing, a curious chitter as it reaches for his head
    ev.append((k.hop1 - 0.02, "scratch_wood", -4, -0.25))
    ev.append((k.hop2, "footstep", -9, -0.2))
    ev.append((k.hop2 + 0.7, "creature_chitter", -6, -0.2))
    # the hood: cloth, then his sigh
    ev.append((k.hd0, "cloth_rustle", 2, 0.0))
    ev.append((k.sigh - 0.05, "sigh", 1, 0.1))
    # the sense
    pings = pings_for(k, info)
    for i, (t0, x, y, kk) in enumerate(pings):
        if kk >= 0.75:
            ev.append((t0, "sonar_ping", 0 if i < 2 else -3, 0.0))
        else:
            ev.append((t0, "sonar_ping_small", -4 if t0 < k.BONK else -2, 0.0))
    # "Oh." -> its ears perk; the nod
    ev.append((k.L3 + 0.18, "ears_perk", 0, -0.2))
    ev.append((k.NOD + 0.35, "ears_perk", 2, -0.2))
    # stands up
    ev.append((k.stand0 + 0.2, "cloth_rustle", -2, 0.1))
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
