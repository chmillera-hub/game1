"""S4 - "The others" (BIBLE section 4, S4).

Quill works through the menu. Each cardN beat: his palm comes up, a small wrist flick, the card
slides to centre and enlarges (holo_select), the rest dim - and we cut to Rae while the alternate plays:
  kazoo   snort-laugh -> the grin crumples, eyes well -> "Why is the kazoo one ALSO good?!" (laugh-crying)
  arcade  pixel sparkles; braced, then her head bobs and her foot taps against her will (medium-wide);
          "Stop. My foot is tapping." - she grips her knee
  lo-fi   rain on the window, warm dim light; she hugs herself, slow nod, lip trembling; "That is not fair."
  5-7     theremin cards wobble and fold away while the wail plays; she flinches; "...Thank you."
  lullaby warm light, a tiny music box turning above his palm; she comes undone (eyes squeezed, tears,
          mug to her chest), sets the mug down and rises; "Nope. Nope nope nope." - snatches the mug on the
          way, backs to the door pointing at him and is gone; the door shuts.

render(canvas, t) is a pure function of absolute time t; times derive from named beats / lines / music
cues / SFX. Until the first cut (card2) the S3 close-up simply continues (anim.scenes.s3.render).
Shared helpers (fan drawing, arm tracks, gaze, blinks, mug solver) live in anim.scenes.s3.

Shot list (orientation only):
  s3 CU        S4 start -> card2      (S3's close-up of Rae, dawning dread)
  P2           card2 -> kazoo         PRESENTATION 3-shot: "Number two..." card 2 pops out
  K            kazoo                  Rae MEDIUM -> slow push to CLOSE: snort-laugh, the grin crumples
  R12          r12                    TWO-SHOT: "Why is the kazoo one ALSO good?!" (he is already raising his palm)
  P3           card3 -> chip          MEDIUM Quill + card 3: "Number three. For an arcade cabinet."
  C            chip (+ r13)           Rae MEDIUM-WIDE (feet in frame): head bob, foot tap, grips her knee
     QI        (1.1 s insert)         Quill MCU: his eyes drop to her tapping foot
  P4           card4 -> lo-fi         PRESENTATION 3-shot (tighter): "Lo-fi beats... to quietly fall apart to."
  L            lo-fi                  Rae MEDIUM against the rainy window, warm dim, slow drift
  R14          r14                    CLOSE-UP Rae: "That is not fair."
  P57          card5_7 -> r15         TWO-SHOT wide: cards 5-7 wobble and fold away, Rae flinches at the wail
  R15          r15                    CLOSE-UP Rae: "...Thank you."
  P8           card8 -> lullaby       MEDIUM Quill + card 8: "...It is eleven seconds long."
  LW           lullaby start          WIDE warm two-shot: card 8 becomes a music box above his palm
  LC           lullaby                CLOSE-UP Rae: undone
  LS           rae_stand_start        MEDIUM-WIDE: mug down on the bench, she rises slowly
  LQ           lullaby end            MEDIUM Quill + music box, last notes
  N            r16 "Nope..."          MEDIUM Rae standing: hands up, head shakes, first step back
  X            rae_backs_out -> end   WIDE (door + Quill): she grabs the mug, backs to the door pointing,
                                      waits for it, scurries out; the door shuts; the cards begin to fade
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Track, auto_blink, beat, breathe, clamp, ease_in_out, ease_out, glow, lerp,
                       line_end, line_start, mouth, music_cue, music_env, music_onsets, noise1, scene_span,
                       smoothstep)
from anim.rig import ArmPose, Pose
from anim.scenes import s3
from anim.scenes.s3 import (FAN, FLOOR, SEAT_X, SEAT_Y, ArmSeq, _face_cam, arm, arm_add, blink_amt, card_xy,
                            drift, draw_fan, gaze, pulse, select_flash, sfx_time, smoothed)
from config import MUSIC_ENV, H, W

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s4")
S, E = line_start, line_end

C2, C3, C4, C57, C8 = beat("card2"), beat("card3"), beat("card4"), beat("card5_7"), beat("card8")
KZ0, KZ1 = music_cue("alt_kazoo")["start"], music_cue("alt_kazoo")["end"]
CH0, CH1 = music_cue("alt_chip")["start"], music_cue("alt_chip")["end"]
LF0, LF1 = music_cue("alt_lofi")["start"], music_cue("alt_lofi")["end"]
TH0, TH1 = music_cue("alt_theremin")["start"], music_cue("alt_theremin")["end"]
LL0, LL1 = music_cue("alt_lullaby")["start"], music_cue("alt_lullaby")["end"]
STAND = beat("rae_stand_start")
BACKS = beat("rae_backs_out")
EXIT = beat("rae_exit_door")
DOOR_SHUT = sfx_time("door_close", EXIT)


@lru_cache(maxsize=1)
def _menv():
    p = Path(MUSIC_ENV)
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


def cue_beats(cue):
    st = music_cue(cue)["start"]
    return [st + b for b in _menv().get(cue, {}).get("beats", [])]


CHIP_BEATS = cue_beats("alt_chip") or [CH0 + 0.4 * k for k in range(14)]
LOFI_BEATS = cue_beats("alt_lofi") or [LF0 + 0.75 * k for k in range(9)]
KAZ_BEATS = cue_beats("alt_kazoo") or [KZ0 + 0.54 * k for k in range(11)]
LULL_BEATS = cue_beats("alt_lullaby") or [LL0 + 0.67 * k for k in range(16)]

# ---------------------------------------------------------------- cuts
CUT_P2 = C2 - 0.05
CUT_K = KZ0 + 0.12                      # (his palm finishes coming down on the P2 shot)
CUT_R12 = S("r12") - 0.15
CUT_P3 = C3 - 0.05
CUT_C = CH0 + 0.05
CUT_QI = CH0 + 3.1
CUT_CB = CH0 + 4.2
CUT_P4 = C4 - 0.45                      # on Quill as his palm comes up for the next card
CUT_L = LF0 + 0.05
CUT_L2 = LF0 + 3.3                      # lo-fi: album-cover wide -> close-up (runs through r14)
CUT_R14 = LF1
CUT_P57 = C57 - 0.45
CUT_R15 = S("r15") - 0.2
CUT_P8 = C8 - 0.6
CUT_LW = LL0 - 0.06
CUT_LC = LL0 + 1.95
CUT_LS = STAND - 0.1
CUT_LQ = STAND + 3.55
CUT_N = LL1 + 0.3
CUT_X = BACKS - 0.1

SHOTS = [("s3", T0), ("P2K", CUT_P2), ("R12P3", CUT_R12), ("C", CUT_C), ("QI", CUT_QI),
         ("C", CUT_CB), ("P4", CUT_P4), ("L", CUT_L), ("L2", CUT_L2), ("P57", CUT_P57), ("R15", CUT_R15),
         ("P8", CUT_P8), ("LW", CUT_LW), ("LC", CUT_LC), ("LS", CUT_LS), ("LQ", CUT_LQ), ("N", CUT_N), ("X", CUT_X)]


def shot_at(t):
    cur = SHOTS[0]
    nxt = T1 + 1.0
    for i, (name, a) in enumerate(SHOTS):
        if t >= a:
            cur = (name, a)
            nxt = SHOTS[i + 1][1] if i + 1 < len(SHOTS) else T1 + 1.0
    return cur[0], cur[1], nxt


# =========================================================================== lighting
LOFI_DIM = Track([(CUT_L, 0.0), (CUT_L + 1.4, 1.0, "io"), (CUT_P57 - 0.001, 1.0), (CUT_P57, 0.0, "step")])
RAIN = Track([(CUT_L, 0.0), (CUT_L + 1.8, 1.0, "io"), (CUT_P57 - 0.001, 1.0), (CUT_P57, 0.0, "step")])
LULL_WARM = Track([(LL0, 0.0), (LL0 + 1.6, 1.0, "io"), (LL1 + 0.25, 1.0), (LL1 + 2.3, 0.0, "io")])


def room(t):
    """(light, warm, rain) of the lounge."""
    ld = LOFI_DIM(t)
    lw = LULL_WARM(t)
    return 1.0 - 0.2 * ld, max(0.45 * ld, lw), RAIN(t)


def char_lighting(t):
    light, warm, _ = room(t)
    return env.char_light(light, warm)


# =========================================================================== Rae
A = R.ARMS
HOLD = A["hold_mug"]
HOLD_L = A["hold_mug"]
CLUTCH = s3.CLUTCH
LAP_R = s3.LAP_R
LAP_L = s3.LAP_L
MUG_RAISE = arm(A["shrug"], hand="hold", shoulder=14.0, elbow=66.0, across=-0.3)    # exasperated "why?!" shrug
PALM_OUT_L = ArmPose(shoulder=30.0, elbow=110.0, wrist=-10.0, hand="palm_up")     # "...why?!" palm up
KNEE_R = ArmPose(shoulder=24.0, elbow=34.0, wrist=6.0, hand="relaxed")         # hand resting on the knee
GRIP_R = A["grip_knee"]
HUG_R = A["hug_self"]
MUG_CHEST_L = arm(HOLD, shoulder=20.0, elbow=110.0, across=0.4)                 # far hand: mug to the chest
FLINCH_R = arm(A["hands_up"], shoulder=40.0, elbow=110.0, wrist=-20.0, across=0.1)
MUG_CHEST_R = arm(HOLD, shoulder=18.0, elbow=118.0, across=0.5)                 # near hand: mug to the heart
CHEST_L = A["hand_on_chest"]
CHEST_R = A["hand_on_chest"]
REST = A["rest"]
NOPE_R = ArmPose(shoulder=46.0, elbow=110.0, wrist=-28.0, hand="palm_out", across=0.05)  # hands up: "nope"
NOPE_L = ArmPose(shoulder=36.0, elbow=116.0, wrist=-24.0, hand="palm_out")
POINT_L = ArmPose(shoulder=84.0, elbow=6.0, wrist=0.0, hand="point")
CARRY_R = arm(HOLD, shoulder=20.0, elbow=96.0, across=0.3)

PASS1_R = arm(HOLD, across=0.32, shoulder=14.0, elbow=92.0)     # mug brought to the middle of her lap
PASS2_L = arm(HOLD_L, across=0.34, shoulder=14.0, elbow=92.0)
SWAP1 = CH0 + 0.5                       # mug passed right -> left hand (bracing: right hand onto her knee)
SWAP2 = C8 + 1.75                       # mug passed back left -> right hand (after wiping her cheek)
WIPE_R0 = C8 + 0.45                     # near hand wipes the near cheek (tear_r trail goes with it)
MUG_PLACE = (150.0, SEAT_Y)             # where she sets the mug down when she rises (to her left)
PLACE_T = STAND + 0.62
RISE0, RISE1 = STAND + 0.95, STAND + 2.45
CYCLE = R.WALK_ADVANCE
STAND_X = SEAT_X + 32.0                 # pelvis once upright (feet tucked back under her as she rises)

# backing out: walk phase keys (phase decreases = walking backward; x tied to phase so feet never skate)
NOPE1 = S("r16")
STEP0, STEP1 = NOPE1 + 0.3, NOPE1 + 1.05            # first backward steps during "nope nope nope"
GRAB_T = STEP1 + 0.25                               # snatches the mug off the bench
BACK0, BACK1 = GRAB_T + 0.18, EXIT - 0.12          # backing to the door while she points ("I'm getting out")
OUT0 = EXIT + 0.12                                  # the door opens behind her -> she scurries out
OUT1 = EXIT + 0.88
IN_DOOR = EXIT + 0.3                                # from here she is behind the door plane (in the doorway)
WALK_KEYS = [(STEP0, 0.25), (STEP1, -0.5), (BACK0, -0.5), (BACK1, -2.5), (OUT0, -2.5), (OUT1, -3.75)]


def walk_phase(t):
    if t < STEP0:
        return None
    ks = WALK_KEYS
    if t >= ks[-1][0]:
        return ks[-1][1] + (t - ks[-1][0]) * (ks[-1][1] - ks[-2][1]) / (ks[-1][0] - ks[-2][0])
    for i in range(1, len(ks)):
        if t < ks[i][0]:
            t0, p0 = ks[i - 1]
            t1, p1 = ks[i]
            u = (t - t0) / (t1 - t0)
            if i == len(ks) - 1:
                u = u * (1.35 - 0.35 * u)              # bolts, then keeps going behind the wall
            else:
                u = ease_in_out(u) * 0.3 + u * 0.7
            return p0 + (p1 - p0) * u
    return ks[-1][1]


def rae_x(t):
    ph = walk_phase(t)
    if ph is None:
        return RISE_X(t)
    return STAND_X + (ph - 0.25) * CYCLE


RISE_X = Track([(RISE0, SEAT_X), (RISE1, STAND_X, "io")])
RISE_SIT = Track([(RISE0, 1.0), (RISE0 + 0.25, 0.92, "io"), (RISE1, 0.0, "io")])


def _rae_tracks():
    d = {}
    P2s = C2
    q08 = S("q08")
    r12, r12e = S("r12"), E("r12")
    r13, r13e = S("r13"), E("r13")
    r14, r14e = S("r14"), E("r14")
    r15, r15e = S("r15"), E("r15")
    r16 = S("r16")
    q10, q11, q12 = S("q10"), S("q11"), S("q12")
    WIPE = CUT_QI + 0.3                      # far-cheek trail reset while we are on the foot insert
    WIPE2 = WIPE_R0 + 0.3                    # near cheek: under her hand mid-wipe
    d["wipes"] = (WIPE, WIPE2)

    # ---------------- body
    d["lean"] = Track([
        (T0, 2.5), (P2s, 2.5), (P2s + 0.1, 0.0, "out"), (q08 + 2.4, 1.0), (q08 + 2.9, -2.0),
        (KZ0 + 0.45, -2.0), (KZ0 + 0.5, 6.0, "out"), (KZ0 + 0.75, -3.0), (KZ0 + 2.4, -1.0), (KZ0 + 4.5, 3.0),
        (KZ1, 4.0), (r12 - 0.05, 2.0), (r12 + 0.3, -5.0, "out"), (r12e, -4.0), (r12e + 0.4, 0.0),
        (CUT_P3, 1.0), (CH0, 1.0), (CH0 + 0.3, -2.0), (CH0 + 3.0, 0.0), (CH1 - 0.6, 3.0),
        (r13 - 0.05, 3.0), (r13 + 0.15, 10.0, "out"), (r13 + 0.6, 8.0), (r13 + 1.6, 5.0), (r13e, 3.0),
        (C4, 3.0), (q10 + 2.5, 1.0), (LF0, 0.0), (LF0 + 2.0, 5.0), (LF1, 6.0), (r14, 5.0), (r14e, 4.0),
        (C57, 2.0), (q11 + 1.6, 3.0), (TH0 - 0.05, 3.0), (TH0 + 0.08, -6.0, "out"), (TH0 + 1.2, -4.0),
        (TH1, 0.0), (r15, 2.0), (r15e, 4.0), (C8, 2.0), (LL0, 2.0), (LL0 + 2.0, 4.0), (CUT_LC + 1.5, 7.0),
        (STAND, 4.0), (PLACE_T - 0.1, -4.0), (PLACE_T + 0.3, 0.0), (RISE0 + 0.2, 14.0), (RISE1, 2.0),
        (RISE1 + 1.0, -1.0), (LL1, -2.0), (r16 - 0.1, -2.0), (r16 + 0.12, -7.0, "out"), (STEP1, -5.0),
        (GRAB_T - 0.2, -10.0), (GRAB_T + 0.2, -4.0), (BACK1, -5.0), (OUT0, -6.0), (T1 + 1, -8.0)])
    d["bounce"] = Track([
        (T0, 0.0), (KZ0 + 0.45, 0.0), (KZ0 + 0.5, 6.0, "out"), (KZ0 + 0.7, -2.0), (KZ0 + 0.9, 0.0),
        (r13 - 0.02, 0.0), (r13 + 0.1, 5.0, "out"), (r13 + 0.4, 0.0),
        (TH0 - 0.02, 0.0), (TH0 + 0.08, -5.0, "out"), (TH0 + 0.5, -2.0), (TH1, 0.0),
        (RISE1 - 0.2, 0.0), (RISE1 + 0.2, 3.0), (RISE1 + 0.6, 0.0),
        (r16 - 0.05, 0.0), (r16 + 0.08, -4.0, "out"), (r16 + 0.35, 0.0),
        (GRAB_T - 0.3, 0.0), (GRAB_T - 0.02, 40.0, "io"), (GRAB_T + 0.06, 39.0), (BACK0 + 0.2, 0.0, "io")])
    d["shoulders"] = Track([
        (T0, 0.25), (P2s, 0.25), (P2s + 0.08, 0.38, "out"), (P2s + 0.6, 0.2), (KZ0 + 0.5, 0.45, "out"),
        (KZ0 + 2.5, 0.25), (KZ0 + 4.0, 0.15), (KZ1, 0.2), (r12, 0.35), (r12e + 0.3, 0.1),
        (CH0, 0.1), (CH0 + 0.4, 0.35), (CH0 + 3.5, 0.2), (r13, 0.4, "out"), (r13e, 0.2),
        (C4, 0.15), (LF0, 0.2), (LF0 + 2.0, 0.42), (LF1, 0.45), (r14e, 0.35),
        (C57, 0.15), (TH0, 0.15), (TH0 + 0.08, 0.7, "out"), (TH0 + 1.2, 0.55), (TH1 + 0.2, 0.1),
        (r15, 0.15), (LL0, 0.1), (CUT_LC, 0.3), (STAND, 0.35), (RISE1, 0.2), (r16, 0.3),
        (r16 + 0.1, 0.55, "out"), (BACK0, 0.4), (OUT0, 0.55), (T1 + 1, 0.55)])
    d["turn"] = Track([(T0, 0.35), (r12, 0.35), (r12 + 0.3, 0.26), (r12e + 0.3, 0.33), (TH0, 0.35),
                       (TH0 + 0.1, 0.42, "out"), (TH1, 0.35), (RISE1, 0.35), (r16 - 0.05, 0.33),
                       (r16 + 0.15, 0.24, "out"), (STEP0 + 0.2, 0.3), (GRAB_T, 0.36), (T1 + 1, 0.4)])
    # ---------------- head
    d["nod"] = Track([
        (T0, 0.12), (P2s, 0.12), (P2s + 0.4, 0.3), (q08 + 1.2, 0.25), (q08 + 2.5, 0.1), (KZ0 + 0.45, 0.08),
        (KZ0 + 0.5, -0.32, "out"), (KZ0 + 0.75, 0.25, "io"), (KZ0 + 1.3, 0.05), (KZ0 + 3.2, 0.1),
        (KZ0 + 4.5, 0.22), (KZ1, 0.18), (r12 + 0.3, 0.3), (r12e, 0.15), (CUT_P3, 0.05),
        (CH0, 0.0), (CH0 + 1.0, -0.05), (CH1, -0.02), (r13 + 0.4, -0.3), (r13 + 1.4, -0.35),
        (r13 + 1.6, 0.0), (r13e, 0.05), (q10 + 1.0, 0.15), (LF0, 0.1), (LF0 + 1.5, 0.22), (LF1, 0.1),
        (r14, -0.05), (r14e, -0.15), (C57, 0.1), (q11 + 1.5, 0.15), (TH0, 0.1), (TH0 + 0.08, 0.32, "out"),
        (TH1, 0.05), (r15 - 0.15, 0.05), (r15 - 0.05, -0.12, "out"), (r15 + 0.25, 0.0), (r15e, -0.2),
        (r15e + 0.4, -0.05), (LL0, 0.15), (LL0 + 1.5, 0.3), (CUT_LC, -0.2), (STAND - 0.6, -0.3),
        (STAND, 0.0), (PLACE_T, -0.25), (RISE0 + 0.3, 0.05), (RISE1, 0.32), (LL1, 0.28), (r16, 0.1),
        (STEP1, 0.0), (GRAB_T, -0.1), (BACK0, 0.05), (T1 + 1, 0.05)])
    d["tilt"] = Track([
        (T0, -2.0), (P2s, -2.0), (q08 + 2.0, -2.0), (q08 + 2.5, -8.0), (KZ0 + 0.4, -6.0), (KZ0 + 0.6, 4.0),
        (KZ0 + 3.0, 2.0), (KZ0 + 4.5, -4.0), (KZ1, -5.0), (r12, -3.0), (r12 + 1.0, 4.0), (r12e, 2.0),
        (CH0, 0.0), (CH0 + 3.5, 3.0), (CH1, 6.0), (r13, 0.0), (r13 + 1.5, -6.0), (r13e, -4.0), (C4, -3.0),
        (q10 + 2.6, -6.0), (LF0, -4.0), (LF0 + 3.0, -8.0), (LF1, -7.0), (r14, -4.0), (r14e, -6.0),
        (C57, -2.0), (q11 + 1.4, -6.0), (TH0, -4.0), (TH0 + 0.1, 6.0, "out"), (TH1, 2.0), (r15, -4.0),
        (r15e, -7.0), (LL0, -3.0), (CUT_LC, -6.0), (STAND, -4.0), (RISE1, 2.0), (LL1, -2.0), (r16, 0.0),
        (T1 + 1, -2.0)])
    # ---------------- eyes
    d["lid"] = Track([
        (T0, 1.0), (P2s, 1.0), (q08 + 2.4, 0.95), (q08 + 2.9, 0.78), (KZ0 + 0.45, 0.78), (KZ0 + 0.5, 0.35, "out"),
        (KZ0 + 2.6, 0.45), (KZ0 + 3.4, 0.85), (KZ0 + 4.5, 0.92), (KZ1, 0.85), (r12, 0.7), (r12e, 0.7),
        (r12e + 0.4, 0.85), (CH0, 0.85), (CH0 + 0.3, 0.72), (CH0 + 3.0, 0.75), (CH1 - 1.2, 0.55),
        (CH1 - 0.45, 0.6), (CH1 - 0.3, 1.0, "out"), (r13 + 1.6, 0.9), (r13e, 0.8), (C4, 0.85),
        (q10 + 1.5, 0.95), (q10 + 3.0, 0.88), (LF0, 0.85), (LF0 + 2.0, 0.72), (LF1, 0.7), (r14, 0.78),
        (r14e, 0.7), (C57, 0.88), (q11 + 1.6, 1.0), (TH0 - 0.05, 0.6), (TH0 + 0.05, 0.12, "out"),
        (TH1 - 0.3, 0.2), (TH1 + 0.2, 0.85), (r15, 0.6), (r15e, 0.55), (C8, 0.8), (LL0, 0.85),
        (LL0 + 1.6, 0.75), (CUT_LC, 0.3), (CUT_LC + 0.5, 0.06), (STAND - 0.5, 0.08), (STAND, 0.55),
        (RISE1, 0.85), (LL1, 0.8), (LL1 + 0.3, 0.9), (r16, 1.0), (T1 + 1, 1.0)])
    d["wide"] = Track([
        (T0, 0.55), (P2s, 0.55), (P2s + 0.1, 0.7, "out"), (q08 + 1.0, 0.3), (q08 + 2.4, 0.0),
        (KZ0 + 3.4, 0.0), (KZ0 + 4.0, 0.15), (KZ1, 0.0), (CH0, 0.0), (CH1 - 0.45, 0.0), (CH1 - 0.3, 0.7, "out"),
        (r13 + 0.4, 0.35), (r13e, 0.1), (q10 + 0.9, 0.0), (q10 + 1.2, 0.35, "out"), (q10 + 2.4, 0.15),
        (LF0, 0.0), (C57, 0.1), (q11 + 1.4, 0.6), (q11 + 2.4, 0.2), (TH0, 0.0), (TH1 + 0.1, 0.0),
        (TH1 + 0.3, 0.2), (r15, 0.0), (LL0, 0.0), (LL1, 0.0), (LL1 + 0.4, 0.3), (r16, 0.75, "out"),
        (r16 + 1.0, 0.5), (GRAB_T, 0.35), (OUT0 - 0.15, 0.4), (OUT0, 0.85, "out"), (T1 + 1, 0.7)])
    d["blinks"] = [
        (P2s + 0.02, 0.13), (q08 + 1.0, 0.16), (q08 + 2.55, 0.15), (KZ0 + 2.9, 0.2), (KZ0 + 4.2, 0.3),
        (r12e + 0.15, 0.18), (CH0 + 0.2, 0.15), (CH0 + 2.2, 0.16), (r13 + 0.9, 0.15), (r13 + 1.65, 0.15),
        (C4 + 0.05, 0.14), (q10 + 1.0, 0.14), (q10 + 2.9, 0.22), (LF0 + 0.9, 0.3), (LF0 + 3.1, 0.34),
        (LF1 - 0.9, 0.3), (r14e + 0.15, 0.25), (C57 + 0.02, 0.14), (q11 + 2.2, 0.3), (TH1 + 0.35, 0.18),
        (C8 + 0.05, 0.14), (LL0 + 0.8, 0.22), (STAND + 0.3, 0.25), (RISE1 + 0.6, 0.3), (LL1 + 0.35, 0.18),
        (r16 + 0.5, 0.12), (BACK0 + 0.4, 0.14), (OUT0 - 0.25, 0.12)]
    d["pupil"] = Track([(T0, 0.92), (P2s, 0.92), (P2s + 0.3, 1.1), (KZ0, 1.05), (KZ0 + 4.0, 1.2), (CH0, 1.0),
                        (LF0, 1.1), (LF0 + 3.0, 1.25), (C57, 1.0), (TH0, 0.85), (TH1, 1.0), (LL0, 1.1),
                        (LL0 + 1.5, 1.3), (LL1, 1.3), (r16, 0.9), (T1 + 1, 0.9)])
    d["squint"] = Track([
        (T0, 0.0), (KZ0 + 0.45, 0.0), (KZ0 + 0.5, 0.7, "out"), (KZ0 + 2.6, 0.55), (KZ0 + 3.6, 0.2),
        (KZ1, 0.25), (r12, 0.45), (r12e, 0.5), (r12e + 0.5, 0.15), (CH0, 0.0), (CH0 + 0.3, 0.2),
        (CH1 - 1.2, 0.3), (CH1 - 0.3, 0.0), (LF0, 0.0), (LF0 + 2.5, 0.15), (r14, 0.3), (r14e, 0.25),
        (C57, 0.05), (TH0, 0.05), (TH0 + 0.06, 0.85, "out"), (TH1 - 0.2, 0.7), (TH1 + 0.2, 0.1),
        (r15, 0.35), (r15e, 0.35), (C8, 0.1), (LL0 + 1.6, 0.15), (CUT_LC + 0.4, 0.8), (STAND, 0.6),
        (RISE1, 0.2), (LL1, 0.15), (r16, 0.0)])
    STARS = (-0.3, -0.62)
    QU = (0.62, -0.36)              # Quill, seated
    CARD = (0.42, -0.74)            # the focused card, seated
    d["gaze"] = gaze([
        (T0, (0.6, -0.4)),
        (P2s + 0.04, CARD, 0.12), (q08 + 1.4, (0.5, -0.5)), (q08 + 1.9, CARD), (q08 + 2.5, QU),
        (KZ0 + 0.1, CARD), (KZ0 + 0.55, (0.2, 0.3), 0.12),                                    # snort: eyes down
        (KZ0 + 1.6, (0.4, -0.5)), (KZ0 + 2.4, (0.1, 0.1)), (KZ0 + 3.3, CARD, 0.3),
        (KZ0 + 4.6, (0.38, -0.66)), (KZ1 - 0.3, QU),
        (r12 + 0.5, (0.55, -0.45)), (r12e + 0.2, QU),
        (CH0 + 0.15, (0.0, -0.1)), (CH0 + 1.6, (0.2, -0.3)), (CH0 + 2.6, (0.05, -0.15)),
        (CH1 - 1.2, (0.2, -0.45), 0.4), (CH1 - 0.3, (0.3, 0.85), 0.12),                       # ...the FOOT
        (r13 + 0.35, (0.35, 0.9)), (r13 + 1.55, QU, 0.12), (r13e + 0.2, (0.55, -0.42)),
        (C4 + 0.03, CARD, 0.12), (q10 + 1.6, QU), (q10 + 2.8, (0.25, -0.2)),
        (LF0 + 0.3, STARS, 0.5), (LF0 + 2.6, (-0.4, -0.5), 0.6), (LF0 + 4.5, (0.1, 0.1), 0.8),
        (LF1 - 0.4, (0.45, -0.25), 0.4), (r14 + 0.2, QU),
        (C57 + 0.03, (0.3, -0.85), 0.12), (q11 + 1.2, (0.5, -0.8)), (q11 + 2.5, QU),
        (TH0 + 0.6, (0.3, -0.8)), (TH1 - 0.1, (0.38, -0.82)), (TH1 + 0.25, QU),
        (r15 + 0.1, (0.45, -0.25)), (r15e + 0.1, (0.6, -0.42)),
        (C8 + 0.03, CARD, 0.12), (q12 + 1.4, QU), (q12 + 2.7, CARD),
        (LL0 + 0.2, (0.62, -0.48), 0.4),                                                        # the music box
        (CUT_LC - 0.4, (0.55, -0.4)), (STAND + 0.2, (0.55, -0.42)),
        (PLACE_T - 0.35, (-0.5, 0.6), 0.2), (PLACE_T + 0.25, (0.55, -0.3), 0.3),
        (RISE1, (0.62, -0.05), 0.4), (LL1 + 0.4, (0.6, -0.1)),
        (r16 + 0.6, (0.62, -0.12)), (GRAB_T - 0.35, (-0.6, 0.3), 0.12), (GRAB_T + 0.12, (0.62, -0.1), 0.12),
        (OUT0 - 0.55, (-0.85, 0.0), 0.12), (OUT0 - 0.2, (0.62, -0.1), 0.12),
    ])
    # ---------------- brows / mouth
    d["brow_raise"] = Track([
        (T0, 0.6), (P2s, 0.6), (P2s + 0.1, 0.8, "out"), (q08 + 1.5, 0.6), (q08 + 2.4, 0.5), (q08 + 2.9, 0.3),
        (KZ0 + 0.45, 0.2), (KZ0 + 0.5, 0.55, "out"), (KZ0 + 2.5, 0.35), (KZ0 + 4.0, 0.5), (KZ1, 0.5),
        (r12, 0.6), (r12 + 0.8, 0.85), (r12e, 0.6), (CH0, 0.3), (CH0 + 0.3, 0.0), (CH1 - 1.2, 0.2),
        (CH1 - 0.3, 0.85, "out"), (r13, 0.4), (r13 + 1.6, 0.55), (r13e, 0.35), (q10 + 1.2, 0.75, "out"),
        (q10 + 3.0, 0.5), (LF0, 0.45), (LF1, 0.4), (r14, 0.5), (C57, 0.4), (q11 + 1.4, 0.8), (q11 + 2.6, 0.4),
        (TH0, 0.3), (TH0 + 0.08, 0.1, "out"), (TH1, 0.3), (r15, 0.45), (LL0, 0.4), (LL0 + 1.5, 0.55),
        (CUT_LC, 0.35), (STAND, 0.45), (RISE1, 0.6), (r16, 0.85, "out"), (r16 + 1.2, 0.7), (OUT0, 0.9),
        (T1 + 1, 0.85)])
    d["worry"] = Track([
        (T0, 0.8), (P2s, 0.8), (q08 + 2.4, 0.5), (q08 + 2.9, 0.2), (KZ0 + 0.5, 0.15), (KZ0 + 2.5, 0.2),
        (KZ0 + 3.4, 0.45), (KZ0 + 4.6, 0.8), (KZ1, 0.85), (r12, 0.75), (r12e, 0.7), (r12e + 0.6, 0.5),
        (CH0, 0.35), (CH0 + 0.3, 0.0), (CH1 - 0.3, 0.3), (r13, 0.5), (r13e, 0.45), (C4, 0.4),
        (q10 + 1.2, 0.5), (q10 + 3.0, 0.75), (LF0 + 1.5, 0.75), (LF0 + 4.0, 0.9), (LF1, 0.92), (r14, 0.95),
        (r14e, 0.9), (C57, 0.55), (q11 + 1.4, 0.8), (q11 + 2.6, 0.55), (TH0, 0.5), (TH1, 0.6),
        (r15, 0.85), (r15e, 0.85), (C8, 0.6), (LL0, 0.6), (LL0 + 1.5, 0.8), (CUT_LC, 1.0), (STAND, 0.95),
        (RISE1, 0.85), (LL1, 0.85), (r16, 0.7), (OUT0, 0.75), (T1 + 1, 0.75)])
    d["furrow"] = Track([
        (T0, 0.12), (P2s, 0.12), (q08 + 2.4, 0.15), (q08 + 2.9, 0.55, "out"), (KZ0 + 0.45, 0.55),
        (KZ0 + 0.5, 0.0, "out"), (KZ1, 0.0), (r12 + 0.4, 0.2), (r12e, 0.1), (CH0, 0.1), (CH0 + 0.3, 0.55),
        (CH0 + 3.0, 0.35), (CH1 - 1.2, 0.1), (CH1 - 0.3, 0.0), (r13, 0.45), (r13e, 0.4), (C4, 0.3),
        (q10 + 1.2, 0.05), (LF0, 0.0), (r14, 0.35), (r14e, 0.3), (C57, 0.15), (TH0, 0.1),
        (TH0 + 0.08, 0.6, "out"), (TH1, 0.2), (r15, 0.0), (CUT_LC, 0.2), (STAND, 0.1), (r16, 0.3),
        (T1 + 1, 0.25)])
    d["open"] = Track([
        (T0, 0.12), (P2s, 0.12), (q08 + 2.4, 0.08), (q08 + 2.9, 0.0), (KZ0 + 0.45, 0.0), (KZ0 + 0.5, 0.42, "out"),
        (KZ0 + 2.6, 0.35), (KZ0 + 3.6, 0.15), (KZ1, 0.12), (r12e, 0.1), (r12e + 0.3, 0.2), (CH0, 0.05),
        (CH0 + 0.3, 0.0), (CH1 - 1.2, 0.08), (CH1 - 0.3, 0.3, "out"), (r13, 0.0), (r13e, 0.0),
        (q10 + 3.0, 0.05), (LF0, 0.06), (LF1, 0.1), (r14e, 0.1), (q11 + 1.4, 0.15), (TH0, 0.05),
        (TH0 + 0.08, 0.35, "out"), (TH1 - 0.3, 0.3), (TH1 + 0.2, 0.08), (r15e, 0.05), (LL0 + 1.5, 0.15),
        (CUT_LC + 0.5, 0.32), (STAND, 0.25), (RISE1, 0.18), (LL1, 0.15), (r16 - 0.2, 0.05),
        (R16E(), 0.0), (R16E() + 0.2, 0.25), (T1 + 1, 0.2)])
    d["round"] = Track([(T0, 0.0), (KZ0 + 2.6, 0.0), (KZ1, 0.1), (CH1 - 0.3, 0.6), (r13, 0.0),
                        (TH0 + 0.08, 0.0), (CUT_LC + 0.5, 0.3), (RISE1, 0.4), (r16, 0.0), (R16E() + 0.2, 0.5)])
    d["smile"] = Track([
        (T0, -0.38), (P2s, -0.38), (q08 + 2.4, -0.2), (q08 + 2.9, -0.15), (KZ0 + 0.45, -0.1),
        (KZ0 + 0.5, 0.95, "out"), (KZ0 + 2.6, 0.9), (KZ0 + 3.6, 0.65), (KZ0 + 4.6, 0.3), (KZ1, 0.35),
        (r12, 0.75), (r12e, 0.7), (r12e + 0.6, 0.2), (CH0, 0.0), (CH0 + 0.3, -0.3), (CH0 + 3.0, -0.15),
        (CH1 - 1.2, 0.35), (CH1 - 0.3, -0.05), (r13, -0.2), (r13e, -0.25), (C4, -0.2), (q10 + 1.2, 0.1),
        (q10 + 3.0, -0.25), (LF0, -0.25), (LF1, -0.35), (r14, -0.45), (r14e, -0.5), (C57, -0.2),
        (q11 + 1.4, -0.35), (q11 + 2.6, 0.05), (TH0, 0.05), (TH0 + 0.08, -0.55, "out"), (TH1, -0.2),
        (r15, 0.22), (r15e, 0.3), (C8, -0.05), (LL0, -0.05), (LL0 + 2.0, 0.08), (CUT_LC, -0.3),
        (CUT_LC + 0.6, -0.55), (STAND, -0.45), (RISE1, -0.3), (LL1, -0.25), (r16, -0.4), (T1 + 1, -0.35)])
    d["smirk"] = Track([(T0, 0.0), (q08 + 2.4, 0.0), (q08 + 2.9, -0.35, "out"), (KZ0 + 0.45, -0.35),
                        (KZ0 + 0.5, 0.0, "out"), (CH0, 0.0), (CH0 + 0.3, -0.25), (CH0 + 3.0, 0.0)])
    d["tremble"] = Track([
        (T0, 0.16), (P2s + 1.0, 0.0), (KZ0 + 3.4, 0.0), (KZ0 + 4.6, 0.55), (KZ1, 0.6), (r12e, 0.4),
        (r12e + 0.8, 0.1), (CH0, 0.0), (q10 + 3.0, 0.2), (LF0 + 1.5, 0.35), (LF1, 0.6), (r14, 0.85),
        (r14e, 0.75), (C57, 0.15), (TH1, 0.1), (r15, 0.45), (C8, 0.2), (LL0 + 2.0, 0.4), (CUT_LC + 0.5, 0.85),
        (STAND, 0.7), (LL1, 0.6), (r16, 0.3), (T1 + 1, 0.3)])
    # ---------------- tears (trails reset off screen when she has wiped them: WIPE / WIPE2)
    d["tears"] = Track([
        (T0, 0.34), (KZ0 + 3.4, 0.3), (KZ0 + 5.0, 0.75), (r12e, 0.8), (WIPE, 0.8), (WIPE + 0.01, 0.35),
        (CH0, 0.3), (r13e, 0.3), (LF0 + 1.0, 0.4), (LF1, 0.78), (r14e, 0.85), (C57, 0.55), (r15, 0.6),
        (WIPE2, 0.6), (WIPE2 + 0.01, 0.4), (LL0 + 1.5, 0.75), (CUT_LC + 0.5, 0.95), (LL1, 0.8),
        (T1 + 1, 0.7)])
    d["tear_l"] = Track([(KZ1 - 0.5, 0.0), (r12 + 0.2, 0.35, "out"), (r12e + 0.4, 1.0, "io"),
                         (WIPE, 1.0), (WIPE + 0.01, 0.0, "step"),
                         (CUT_LC + 0.9, 0.0), (CUT_LC + 1.7, 0.3, "out"), (STAND + 1.5, 1.0, "io")])
    d["tear_r"] = Track([(LF1 - 1.4, 0.0), (LF1 - 0.4, 0.25, "out"), (r14e + 0.2, 1.0, "io"),
                         (WIPE2, 1.0), (WIPE2 + 0.01, 0.0, "step"),
                         (CUT_LC + 0.4, 0.0), (CUT_LC + 1.1, 0.3, "out"), (STAND + 0.9, 1.0, "io")])
    d["shine"] = Track([(T0, 0.3), (KZ0 + 4.0, 0.6), (r12e, 0.5), (CH0, 0.2), (LF0 + 2.0, 0.6),
                        (C57, 0.3), (LL0 + 1.5, 0.8), (LL1, 0.7), (r16, 0.4), (T1 + 1, 0.4)])
    d["blush"] = Track([(T0, 0.16), (KZ0 + 0.5, 0.35), (r12e, 0.4), (CH0, 0.2), (r13, 0.35), (r13e + 0.5, 0.2),
                        (LF0, 0.2), (r14, 0.35), (C57, 0.25), (LL0 + 2.0, 0.4), (T1 + 1, 0.35)])
    d["sniffle"] = Track([(T0, 0.32), (KZ1, 0.45), (CH0, 0.4), (LF1, 0.55), (r15, 0.65), (LL0 + 2.0, 0.7),
                          (LL1, 0.8), (T1 + 1, 0.82)])
    # ---------------- feet / head bob (the arcade gag)
    d["tap"] = Track([(CH0 + 1.9, 0.0), (CH0 + 2.8, 0.55, "io"), (CH0 + 4.0, 0.8), (CH1, 1.0), (r13 + 0.08, 1.0),
                      (r13 + 0.22, 0.0, "out"), (r13 + 1.85, 0.0), (r13 + 1.95, 0.5, "out"), (r13 + 2.3, 0.0, "io")])
    d["bob"] = Track([(CH0 + 0.9, 0.0), (CH0 + 1.3, 0.35), (CH0 + 1.7, 0.0, "out"), (CH0 + 2.4, 0.15),
                      (CH0 + 3.6, 0.7), (CH1 - 0.4, 1.0), (CH1 - 0.3, 0.0, "out")])
    d["lofi_nod"] = Track([(LF0 + 0.6, 0.0), (LF0 + 2.0, 1.0), (LF1 - 0.3, 1.0), (LF1 + 0.4, 0.0)])
    d["laugh"] = Track([(KZ0 + 0.48, 0.0), (KZ0 + 0.56, 1.0, "out"), (KZ0 + 2.4, 0.8), (KZ0 + 3.6, 0.25),
                        (KZ0 + 4.6, 0.0), (r12 - 0.1, 0.0), (r12 + 0.1, 0.4), (r12e, 0.3), (r12e + 0.5, 0.0)])
    d["sob"] = Track([(CUT_LC + 0.2, 0.0), (CUT_LC + 0.7, 1.0), (STAND, 0.6), (RISE1, 0.2), (LL1, 0.0)])
    # ---------------- arms
    d["arm_l"] = ArmSeq([
        (T0, LAP_L), (r12 - 0.1, LAP_L), (r12 + 0.25, PALM_OUT_L, "out"), (r12 + 0.9, arm_add(PALM_OUT_L, 6, -8)),
        (r12 + 1.2, PALM_OUT_L), (r12e + 0.3, LAP_L, "io"),
        (SWAP1 - 0.4, LAP_L), (SWAP1 - 0.05, "TAKE1"), (SWAP1 + 0.08, "TAKE1"), (SWAP1 + 0.55, HOLD_L),
        (LF0 + 0.2, HOLD_L), (LF0 + 1.2, MUG_CHEST_L), (r14e + 0.3, MUG_CHEST_L), (C57, HOLD_L),
        (SWAP2 - 0.45, HOLD_L), (SWAP2, PASS2_L), (SWAP2 + 0.1, PASS2_L), (SWAP2 + 0.55, LAP_L),
        (STAND + 0.3, LAP_L),
        (RISE1, arm(REST, shoulder=8.0, elbow=24.0)), (r16 - 0.1, arm(REST, shoulder=8.0, elbow=24.0)),
        (r16 + 0.15, NOPE_L, "out"), (r16 + 0.35, arm_add(NOPE_L, -6, 10)), (r16 + 0.55, arm_add(NOPE_L, 4, -6)),
        (GRAB_T - 0.35, NOPE_L), (GRAB_T + 0.1, arm(POINT_L, shoulder=60.0, elbow=40.0)),
        (GRAB_T + 0.32, POINT_L, "out"),
        (BACK1 - 0.3, arm_add(POINT_L, 4, -2)), (BACK1, POINT_L), (OUT0 - 0.4, arm_add(POINT_L, 8, -3)),
        (OUT0 - 0.1, POINT_L), (OUT1 - 0.12, POINT_L), (OUT1 - 0.04, arm_add(POINT_L, 10, -4), "out"),  # ...and YOU
        (OUT1 + 0.22, ArmPose(shoulder=10.0, elbow=60.0, wrist=0.0, hand="relaxed"), "in"),          # whips away
    ])
    return d


def R16E():
    return E("r16")


_RT = _rae_tracks()


_ARM_L = None


def rae_arm_l(t):
    """Left arm track with the solved hand-off pose substituted (lazy: the solve needs the body)."""
    global _ARM_L
    if _ARM_L is None:
        take1 = _take1()
        ks = [(k[0], take1 if isinstance(k[1], str) else k[1], k[2]) for k in _RT["arm_l"].keys]
        _ARM_L = ArmSeq(ks)
    return _ARM_L(t)


def _rae_body(t, arm_l=None) -> Pose:
    d = _RT
    ph = walk_phase(t)
    return Pose(x=rae_x(t), y=FLOOR, facing=1.0, turn=d["turn"](t), sit=RISE_SIT(t) if ph is None else 0.0,
                seat_y=SEAT_Y, walk=ph, lean=d["lean"](t), bounce=d["bounce"](t),
                shoulders_up=d["shoulders"](t), breath=breathe(t, 0.22, 2),
                arm_l=arm_l if arm_l is not None else rae_arm_l(t))


def _solve_side(body, side, target, base, pen=0.6):
    """ArmPose for `side` (hand 'hold', holding the mug) whose held mug sits on target (x, y); prefers a
    low, tucked elbow (a raised upper arm on the far side reads as a broken reach)."""
    best = None
    for ac in (0.0, 0.15, 0.3, 0.45, 0.6):
        for sh in range(-20, 80, 4):
            for el in range(0, 150, 4):
                a = arm(base, shoulder=float(sh), elbow=float(el), across=ac)
                p = body.copy(arm_l=a, mug="l") if side == "l" else body.copy(arm_r=a, mug="r")
                mp = R.mug_pose(p)
                if mp is None:
                    continue
                e = math.hypot(mp[0] - target[0], mp[1] - target[1]) + pen * max(0.0, sh - 6.0)
                if best is None or e < best[0]:
                    best = (e, float(sh), float(el), ac)
    e, sh, el, ac = best
    step = 2.0
    while step > 0.02:
        improved = False
        for dsh, de in ((step, 0), (-step, 0), (0, step), (0, -step)):
            a = arm(base, shoulder=sh + dsh, elbow=el + de, across=ac)
            p = body.copy(arm_l=a, mug="l") if side == "l" else body.copy(arm_r=a, mug="r")
            mp = R.mug_pose(p)
            e2 = math.hypot(mp[0] - target[0], mp[1] - target[1]) + pen * max(0.0, sh + dsh - 6.0)
            if e2 < e - 1e-6:
                e, sh, el, improved = e2, sh + dsh, el + de, True
                break
        if not improved:
            step *= 0.5
    return arm(base, shoulder=sh, elbow=el, across=ac)


@lru_cache(maxsize=1)
def _take1():
    """Left (far) hand that takes the mug from the right hand at SWAP1 without the mug moving."""
    body = _rae_body(SWAP1, arm_l=LAP_L)
    mp = R.mug_pose(body.copy(arm_r=PASS1_R, mug="r"))
    return _solve_side(body, "l", mp, HOLD_L)


@lru_cache(maxsize=1)
def _pass1():
    """Right-hand pass pose re-solved onto exactly where the left hand will hold the mug."""
    body = _rae_body(SWAP1, arm_l=_take1())
    mp = R.mug_pose(body.copy(mug="l"))
    return _solve_side(body.copy(arm_l=LAP_L), "r", mp, PASS1_R, pen=0.0)


@lru_cache(maxsize=1)
def _take2():
    """Right (near) hand that takes the mug back from the left hand at SWAP2."""
    body = _rae_body(SWAP2, arm_l=PASS2_L)
    mp = R.mug_pose(body.copy(arm_r=LAP_R, mug="l"))
    return _solve_side(body, "r", mp, HOLD)


def _place_arm():
    return s3.solve_mug_arm(PLACE_T, MUG_PLACE, _rae_body)


def _grab_arm():
    return s3.solve_mug_arm(GRAB_T, MUG_PLACE, _rae_body, arm(HOLD, wrist=-6.0))


def _arm_r_seqs():
    r12, r12e = S("r12"), E("r12")
    r13, r14e = S("r13"), E("r14")
    take2 = _take2()
    pass1 = _pass1()
    seq1 = ArmSeq([
            (T0, CLUTCH), (C2 + 1.0, CLUTCH), (C2 + 1.8, HOLD), (KZ0 + 0.45, HOLD),
            (KZ0 + 0.55, arm_add(HOLD, 10, 12), "out"), (KZ0 + 0.9, HOLD),
            (r12 - 0.15, HOLD), (r12 + 0.2, MUG_RAISE, "out"), (r12 + 0.9, arm_add(MUG_RAISE, 6, -6)),
            (r12 + 1.25, MUG_RAISE), (r12e + 0.35, HOLD),
            (CH0 - 0.2, HOLD), (SWAP1 - 0.05, pass1), (SWAP1 + 0.1, arm(pass1, hand="relaxed")),
            (SWAP1 + 0.6, KNEE_R)])
    seq2 = ArmSeq([
            (SWAP1 + 0.6, KNEE_R), (r13 - 0.12, arm_add(KNEE_R, 14, -10)),
            (r13 + 0.1, GRIP_R, "out"), (r13 + 1.8, GRIP_R), (r13 + 1.95, arm_add(GRIP_R, 3, 4), "out"),
            (r13 + 2.3, GRIP_R), (C4 + 2.0, GRIP_R), (LF0, KNEE_R), (LF0 + 1.0, HUG_R),
            (r14e + 0.3, HUG_R), (C57, LAP_R), (TH0 - 0.05, LAP_R), (TH0 + 0.12, FLINCH_R, "out"),
            (TH1 - 0.3, FLINCH_R), (TH1 + 0.3, LAP_R),
            (WIPE_R0 - 0.05, LAP_R), (WIPE_R0 + 0.22, arm(A["wipe_eye"], hand="relaxed", wrist=20.0, across=0.25)),
            (WIPE_R0 + 0.45, arm(A["wipe_eye"], hand="relaxed", wrist=32.0, across=0.4, elbow=136.0)),
            (WIPE_R0 + 0.75, LAP_R),
            (SWAP2 - 0.4, LAP_R), (SWAP2 - 0.05, arm(take2, hand="open")), (SWAP2, take2), (SWAP2 + 0.5, HOLD),
            (CUT_LC + 0.1, HOLD), (CUT_LC + 0.7, MUG_CHEST_R), (STAND, MUG_CHEST_R)])
    place = _place_arm()
    seq3 = ArmSeq([(PLACE_T + 0.22, arm(place, hand="open")), (RISE0 + 0.4, arm(CHEST_R, shoulder=24.0)),
                   (RISE0 + 0.9, CHEST_R), (S("r16") - 0.1, CHEST_R), (S("r16") + 0.15, NOPE_R, "out"),
                   (S("r16") + 0.35, arm_add(NOPE_R, 8, -10)), (S("r16") + 0.55, arm_add(NOPE_R, -4, 6)),
                   (S("r16") + 0.75, NOPE_R)])
    grab = _grab_arm()
    seq4 = ArmSeq([(GRAB_T + 0.08, grab), (BACK0 + 0.3, CARRY_R), (T1 + 1, CARRY_R)])
    return seq1, seq2, seq3, seq4, place, grab


_ARS = None


def _rae_arm_r(t):
    """Right arm, with the two mug hand-offs (bench <- hand at PLACE_T, bench -> hand at GRAB_T)."""
    global _ARS
    if _ARS is None:
        _ARS = _arm_r_seqs()
    seq1, seq2, seq3, seq4, place, grab = _ARS
    if t < SWAP1 + 0.6:
        return seq1(t)
    if t < SWAP2 + 0.5 and t >= SWAP2 - 0.05:
        return seq2(t)
    if t < STAND:
        return seq2(t)
    if t < PLACE_T:
        u = (t - STAND) / (PLACE_T - STAND)
        mid = arm(ArmPose.blend(MUG_CHEST_R, place, 0.5), shoulder=ArmPose.blend(MUG_CHEST_R, place, 0.5).shoulder + 8)
        if u < 0.5:
            return ArmPose.blend(MUG_CHEST_R, mid, ease_in_out(u / 0.5))
        return ArmPose.blend(mid, place, ease_in_out((u - 0.5) / 0.5))
    if t < PLACE_T + 0.22:
        return place if t < PLACE_T + 0.1 else arm(place, hand="open")
    if t < GRAB_T - 0.4:
        return seq3(t)
    if t < GRAB_T:
        u = ease_in_out((t - GRAB_T + 0.4) / 0.4)
        return ArmPose.blend(NOPE_R, arm(grab, hand="open") if u < 0.9 else grab, u)
    if t < GRAB_T + 0.08:
        return grab
    return seq4(t)


def rae_mug(t):
    """'r' / 'l' / None (= on the bench)."""
    if t < SWAP1:
        return "r"
    if t < SWAP2:
        return "l"
    if t < PLACE_T + 0.1:
        return "r"
    if t < GRAB_T:
        return None
    return "r"


@lru_cache(maxsize=1)
def _mug_at_place():
    return R.mug_pose(rae_pose(PLACE_T + 0.05))


@lru_cache(maxsize=1)
def _mug_at_grab():
    return R.mug_pose(rae_pose(GRAB_T + 0.01))


def bench_mug(t):
    """The mug standing on the bench between PLACE_T and GRAB_T (settles flat after the release, tips a
    hair toward her fingers just before the grab, so neither hand-off pops)."""
    if PLACE_T + 0.1 <= t < GRAB_T:
        mp, mg = _mug_at_place(), _mug_at_grab()
        ang = mp[3] * (1.0 - smoothstep((t - PLACE_T - 0.1) / 0.22))
        k = smoothstep((t - (GRAB_T - 0.12)) / 0.12)
        x = lerp(mp[0], mg[0], k)
        y = lerp(mp[1], mg[1], k)
        return (x, y, mp[2], lerp(ang, mg[3], k), mp[4])
    return None


def _bob(t, beats, width=0.16):
    """Head-bob pulse train: 0..1 dip right after each beat."""
    v = 0.0
    for b in beats:
        dt = t - b
        if -0.05 <= dt < 0.4:
            v = max(v, math.exp(-((dt - 0.06) / width) ** 2))
    return v


# rig foot tap is a fixed 2.5 Hz sine on the draw clock: shift Rae's draw clock so the heel lands on the beats
_B0 = CHIP_BEATS[0] if CHIP_BEATS else CH0
TAP_SHIFT = ((0.5 - (2.5 * _B0) % 1.0) / 2.5) % 0.4


def rae_pose(t: float) -> Pose:
    d = _RT
    body = _rae_body(t)
    lid = d["lid"](t) * (1.0 - blink_amt(t, d["blinks"]))
    lx, ly = d["gaze"](t)
    lx += 0.022 * noise1(t * 1.7, 9)
    ly += 0.018 * noise1(t * 1.5, 13)
    mo, mr = mouth("rae", t)
    nod = d["nod"](t) + 0.03 * noise1(t * 0.45, 3)
    tilt = d["tilt"](t) + 1.2 * noise1(t * 0.38, 5)
    hturn = 0.015 * noise1(t * 0.5, 4)
    bounce, shoulders, mopen, squint, lean = body.bounce, body.shoulders_up, d["open"](t), d["squint"](t), body.lean
    # kazoo giggles: shoulder-shaking little bounces with the laugh
    lg = d["laugh"](t)
    if lg > 0:
        ph = math.sin(2 * math.pi * 4.6 * (t - KZ0))
        bounce += 2.6 * lg * abs(ph)
        mopen += 0.18 * lg * (0.5 + 0.5 * ph)
        nod += 0.05 * lg * ph
        shoulders += 0.1 * lg * abs(ph)
        hturn += 0.05 * lg * math.sin(2 * math.pi * 1.1 * (t - KZ0))          # shaking her head: "no way"
    # arcade: head bob on the chip beats (she resists, it wins)
    bb = d["bob"](t)
    if bb > 0:
        pb = _bob(t, CHIP_BEATS)
        nod -= 0.16 * bb * pb
        bounce += 2.5 * bb * pb
        tilt += 3.0 * bb * pb * (1 if int((t - CH0) / 0.8) % 2 else -1)
    # lo-fi: slow, heavy nod on the beat
    ln = d["lofi_nod"](t)
    if ln > 0:
        nod -= 0.08 * ln * _bob(t, LOFI_BEATS, 0.3)
    # lullaby sobs: small hitches
    sb = d["sob"](t)
    if sb > 0:
        for h0 in (CUT_LC + 0.85, CUT_LC + 1.8, STAND - 0.35, STAND + 0.9):
            x = (t - h0) / 0.5
            if 0 <= x < 1:
                hh = math.sin(math.pi * min(1.0, x * 2.2)) * (1 - x) ** 0.5 * sb
                shoulders += 0.18 * hh
                bounce -= 2.0 * hh
                nod += 0.08 * hh
    # "Nope nope nope": head shakes
    r16 = S("r16")
    if r16 + 0.3 <= t < r16 + 1.15:
        u = (t - r16 - 0.3) / 0.85
        hturn += 0.16 * math.sin(2 * math.pi * 3.5 * (t - r16 - 0.3)) * math.sin(math.pi * u)
    # reset trails off screen once she has wiped them
    tl, tr = d["tear_l"](t), d["tear_r"](t)
    return body.copy(
        head_tilt=tilt, head_nod=nod, head_turn=hturn, bounce=bounce, shoulders_up=shoulders, lean=lean,
        lid_l=lid, lid_r=lid * (0.99 + 0.01 * noise1(t * 0.7, 3)), look_x=lx, look_y=ly, pupil=d["pupil"](t),
        squint=squint, eye_wide=d["wide"](t), brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t),
        brow_furrow=d["furrow"](t), mouth_open=clamp(mopen + 0.82 * mo), mouth_round=clamp(d["round"](t) + mr),
        smile=d["smile"](t), smirk=d["smirk"](t), mouth_tremble=d["tremble"](t), tears=d["tears"](t),
        tear_l=tl, tear_r=tr, eye_shine=d["shine"](t), blush=d["blush"](t), sniffle=d["sniffle"](t),
        foot_tap=d["tap"](t), arm_r=_rae_arm_r(t), mug=rae_mug(t), **char_lighting(t),
    )


# =========================================================================== Quill
QA = Q.ARMS
PRESENT = QA["present"]
QREST = QA["rest"]
PALM_CLOSE = arm(PRESENT, hand="relaxed", wrist=8.0, elbow=PRESENT.elbow + 6)


def _raise(t_sel, lead=0.55):
    """Arm keys: palm comes up (present) to arrive just before a select at t_sel, then the flick."""
    return [(t_sel - lead, QREST), (t_sel - lead + 0.1, arm_add(QREST, -2, 4)),
            (t_sel - 0.05, PRESENT, "out"), (t_sel + 0.06, arm_add(PRESENT, 2, 6, -16), "out"),
            (t_sel + 0.28, PRESENT, "io")]


def _lower(t0, dur=0.7):
    return [(t0, PRESENT), (t0 + dur, QREST, "io")]


def _quill_tracks():
    d = {}
    q08e, q09e, q10e = E("q08"), E("q09"), E("q10")
    # palm up for each announcement, down while Rae listens (the fan hangs in the air on its own);
    # every raise / lower happens on one of Quill's own shots (or the r12 two-shot)
    keys = [(T0, PRESENT), (C2 - 0.02, PRESENT), (C2 + 0.06, arm_add(PRESENT, 2, 6, -16), "out"),
            (C2 + 0.28, PRESENT, "io")]
    keys += _lower(q08e - 0.2, 0.6)
    keys += _raise(C3, 0.6) + _lower(q09e - 0.25, 0.55)
    keys += _raise(C4, 0.42) + _lower(q10e - 0.25, 0.55)
    keys += _raise(C57, 0.42)
    q11 = S("q11")
    keys += [(q11 + 2.45, PRESENT), (q11 + 2.9, PALM_CLOSE, "io"), (TH1 + 0.05, PALM_CLOSE)]
    keys += [(TH1 + 0.1, PALM_CLOSE), (TH1 + 0.7, QREST, "io")]
    keys += _raise(C8, 0.55)
    d["arm_r"] = ArmSeq(keys)
    d["arm_l"] = ArmSeq([(T0, QREST)])
    q12 = S("q12")
    d["tilt"] = Track([
        (T0, 7.0), (C2, 3.0), (S("q08") + 1.0, 5.0), (S("q08") + 2.4, 8.0), (KZ0 + 1.0, 10.0), (KZ1, 6.0),
        (S("r12") + 1.0, 9.0), (C3, 3.0), (q09e, 6.0), (CH0 + 2.0, 8.0), (CH1, 12.0), (C4, 4.0),
        (q10e - 1.0, 7.0), (LF0 + 2.0, 5.0), (C57, 3.0), (q11 + 2.4, 6.0), (TH0 + 0.4, 9.0), (TH1, 6.0),
        (C8, 3.0), (q12 + 1.6, 6.0), (q12 + 2.6, 9.0), (LL0 + 2.0, 6.0), (STAND, 4.0), (LL1, 8.0),
        (S("r16") + 0.4, 3.0), (BACKS, 0.0), (T1 + 1, -2.0)])
    d["nod"] = Track([
        (T0, 0.0), (C2, 0.06), (C2 + 0.4, 0.0), (S("q08") + 0.7, -0.06), (S("q08") + 1.0, 0.0),
        (C3, 0.06), (C3 + 0.4, 0.0), (CH0 + 2.6, 0.02), (CUT_QI + 0.25, 0.18), (CUT_QI + 0.7, 0.18),
        (CUT_QI + 0.95, 0.02), (C4, 0.06), (C4 + 0.4, 0.0), (C57, 0.06), (C57 + 0.4, 0.0),
        (q11 + 2.5, 0.0), (q11 + 2.7, -0.08), (q11 + 3.0, 0.0), (C8, 0.06), (C8 + 0.4, 0.0),
        (LL0 + 0.3, 0.2), (LL0 + 2.5, 0.12), (STAND + 0.4, 0.0), (RISE1, -0.1), (LL1, -0.06),
        (T1 + 1, -0.05)])
    d["hturn"] = Track([(T0, 0.0), (BACK0, 0.0), (OUT0, -0.12), (T1 + 1, -0.16)])
    d["brow"] = Track([
        (T0, 0.15), (C2, 0.1), (S("q08") + 2.0, 0.18), (KZ0 + 1.0, 0.25), (KZ1, 0.2), (S("r12") + 1.2, 0.35),
        (C3, 0.12), (CH0 + 2.0, 0.15), (CUT_QI + 0.5, 0.32), (C4, 0.12), (S("q10") + 3.0, 0.2),
        (C57, 0.1), (TH0 + 0.3, 0.3), (TH1, 0.15), (C8, 0.08), (LL0 + 1.0, 0.18), (STAND + 1.0, 0.3),
        (S("r16") + 0.3, 0.4), (BACKS, 0.3), (T1 + 1, 0.3)])
    d["worry"] = Track([(T0, 0.0), (CUT_LC, 0.0), (STAND + 1.0, 0.18), (LL1, 0.12), (S("r16") + 0.4, 0.2),
                        (T1 + 1, 0.15)])
    d["smile"] = Track([(T0, 0.06), (C2, 0.02), (KZ0 + 1.5, 0.04), (S("q10") + 2.5, 0.0),
                        (S("q10") + 3.2, 0.07), (q10e + 0.6, 0.02), (LL0 + 1.0, 0.08), (STAND, 0.05),
                        (S("r16"), 0.0)])
    d["glow"] = Track([(T0, 0.16), (C2 - 0.05, 0.16), (C2 + 0.05, 0.45, "out"), (C2 + 0.6, 0.18),
                       (C3 - 0.05, 0.16), (C3 + 0.05, 0.45, "out"), (C3 + 0.6, 0.18),
                       (C4 - 0.05, 0.16), (C4 + 0.05, 0.45, "out"), (C4 + 0.6, 0.18),
                       (C57 - 0.05, 0.16), (C57 + 0.05, 0.45, "out"), (C57 + 0.6, 0.18),
                       (C8 - 0.05, 0.16), (C8 + 0.05, 0.45, "out"), (C8 + 0.6, 0.2), (LL0 + 1.0, 0.32),
                       (LL1, 0.25), (T1 + 1, 0.18)])
    RAE_S = (-0.42, 0.22)
    CARDV = (-0.62, 0.12)
    d["gaze"] = gaze([
        (T0, RAE_S),
        (C2 - 0.12, CARDV), (S("q08") + 0.9, RAE_S), (KZ0 + 2.0, (-0.38, 0.28)), (KZ1, RAE_S),
        (C3 - 0.12, CARDV), (S("q09") + 0.95, RAE_S),
        (CUT_QI + 0.15, (-0.32, 0.9), 0.14), (CUT_QI + 0.75, (-0.4, 0.3), 0.12),       # her foot ... back up
        (C4 - 0.12, CARDV), (S("q10") + 0.7, RAE_S), (S("q10") + 2.2, CARDV), (S("q10") + 2.6, RAE_S),
        (C57 - 0.12, (-0.55, -0.02)), (S("q11") + 2.4, RAE_S), (TH0 + 0.1, (-0.55, -0.02)),
        (TH1 + 0.2, RAE_S),
        (C8 - 0.12, CARDV), (S("q12") + 1.0, RAE_S), (S("q12") + 2.0, CARDV), (S("q12") + 2.4, RAE_S),
        (LL0 + 0.1, (-0.3, 0.42), 0.2), (LL0 + 2.4, RAE_S), (LL0 + 3.8, (-0.3, 0.42)), (CUT_LC + 1.6, RAE_S),
        (RISE0 + 0.3, (-0.5, 0.1), 0.4), (RISE1, (-0.55, 0.02), 0.4),
        (GRAB_T - 0.3, (-0.7, 0.2)), (BACK0 + 0.3, (-0.75, 0.05)), (OUT0, (-0.9, 0.08), 0.3),
    ], dur=0.09)
    return d


_QT = _quill_tracks()


def quill_pose(t: float) -> Pose:
    d = _QT
    mo, mr = mouth("quill", t)
    blink = auto_blink(t, seed=0, rate=4.6, robotic=True)
    lx, ly = d["gaze"](t)
    return Pose(
        x=s3.QX, y=FLOOR, facing=-1.0, turn=0.35,
        head_turn=d["hturn"](t), head_nod=d["nod"](t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=d["tilt"](t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=blink, lid_r=blink, look_x=lx, look_y=ly, brow_raise=d["brow"](t), brow_worry=d["worry"](t),
        smile=d["smile"](t), mouth_open=0.9 * mo, mouth_round=mr, glow=d["glow"](t),
        arm_r=d["arm_r"](t), arm_l=d["arm_l"](t), **char_lighting(t),
    )


# =========================================================================== holo-cards
SEL = [(2, C2), (3, C3), (4, C4), (8, C8)]
GONE = (5, 6, 7)
FOLD_T = {5: TH0 + 0.0, 6: TH0 + 0.42, 7: TH0 + 0.82}
BOX_IN = LL0 - 0.05
BOX_OUT = LL1 - 0.2


# card -> (it flies back to its slot, glowing, as Quill lowers his palm; next select)
PLAY = {2: (E("q08") - 0.2, C3), 3: (E("q09") - 0.25, C4), 4: (E("q10") - 0.25, C57)}


def _focus(t):
    """Selected card at centre stage from its select until its music starts; then back to its slot."""
    f = {}
    for num, ts in SEL:
        back = PLAY[num][0] if num in PLAY else T1 + 99
        a = smoothstep((t - ts) / 0.45) * (1.0 - smoothstep((t - back) / 0.6))
        if num == 8:
            a *= 1.0 - smoothstep((t - BOX_IN) / 0.7)
        if a > 0:
            f[num] = a
    return f


def _playing(t):
    """{card: 0..1} highlighted in its fan slot while its music plays (until the next select)."""
    out = {}
    for num, (p0, nxt) in PLAY.items():
        a = smoothstep((t - p0 - 0.2) / 0.5) * (1.0 - smoothstep((t - nxt) / 0.4))
        if a > 0:
            out[num] = a
    return out


def _pops(t):
    p = {}
    for num, ts in SEL:
        dt = t - ts
        if 0 <= dt < 0.7:
            p[num] = 0.09 * math.sin(math.pi * clamp(dt / 0.7)) * (1 - dt / 0.7) + 0.05 * pulse(t, ts + 0.32, 0.08, 0.25)
    return p


def fan_state(t):
    st = {}
    st["focus"] = _focus(t)
    st["pops"] = _pops(t)
    c1 = 0.6 * (1.0 - smoothstep((t - C2) / 0.5))
    states = {1: c1}
    pl = _playing(t)
    plmax = max(pl.values()) if pl else 0.0
    for n, v in pl.items():
        states[n] = max(states.get(n, 0.0), v)
        st["pops"][n] = st["pops"].get(n, 0.0) + 0.28 * v
    q11 = S("q11")
    hl = smoothstep((t - C57) / 0.4)
    for n in GONE:
        states[n] = hl
    st["states"] = states
    wob = smoothstep((t - (q11 + 1.4)) / 0.6) * 0.55 + 0.45 * smoothstep((t - (TH0 - 0.1)) / 0.2)
    st["wobble"] = {n: wob * (1.0 - smoothstep((t - FOLD_T[n] - 0.5) / 0.2)) for n in GONE} if t > C57 else {}
    st["fold"] = {n: clamp((t - FOLD_T[n]) / 0.7) for n in GONE if t > FOLD_T[n]}
    st["hidden"] = tuple(n for n in GONE if t > FOLD_T[n] + 0.7)
    # while an alternate plays the rest of the fan sinks back (the playing card stays lit)
    alphas = {}
    if plmax > 0:
        for n in range(1, 9):
            alphas[n] = lerp(1.0, 0.45, plmax * (1.0 - pl.get(n, 0.0)))
    # theremin cards lit while the others dim
    if C57 <= t < TH1 + 0.6:
        for n in range(1, 9):
            if n not in GONE:
                alphas[n] = alphas.get(n, 1.0) * lerp(1.0, 0.45, hl * (1.0 - smoothstep((t - TH1) / 0.5)))
    # lullaby: the fan dims around the music box; card 8 dissolves into the box and comes back after
    lull = smoothstep((t - BOX_IN) / 0.8) * (1.0 - smoothstep((t - BOX_OUT) / 0.8))
    if lull > 0:
        for n in range(1, 9):
            alphas[n] = alphas.get(n, 1.0) * lerp(1.0, 0.4, lull)
    c8 = 1.0 - smoothstep((t - BOX_IN) / 0.55)
    c8 = max(c8, smoothstep((t - (BOX_OUT + 0.4)) / 0.7))
    alphas[8] = alphas.get(8, 1.0) * c8
    st["alphas"] = alphas
    st["pops"][8] = st["pops"].get(8, 0.0) - 0.4 * smoothstep((t - BOX_IN) / 0.55) * (1.0 - smoothstep((t - BOX_OUT) / 0.3))
    # the cards begin to fade as she leaves (S5 continues the fade)
    st["alpha"] = 1.0 - 0.15 * smoothstep((t - (DOOR_SHUT - 0.2)) / (T1 - DOOR_SHUT + 0.2))
    return st


def draw_cards(c, t):
    st = fan_state(t)
    # note sparkles from the playing card
    for num, (c0, c1) in ((2, (KZ0, KZ1)), (3, (CH0, CH1)), (4, (LF0, LF1))):
        if c0 - 0.1 <= t <= c1 + 1.5:
            cue = {2: "alt_kazoo", 3: "alt_chip", 4: "alt_lofi"}[num]
            cx_, cy_ = card_xy(num)
            fx.draw_note_sparkles(c, t, music_onsets(cue), area=(cx_ - 70, cy_ - 130, cx_ + 70, cy_ - 40),
                                  seed=num, life=1.3, color="teal_glow", alpha=0.6, size=0.7)
    draw_fan(c, t, 1.0, alpha=st["alpha"], focus=st["focus"], states=st["states"], wobble=st["wobble"],
             fold=st["fold"], pops=st["pops"], hidden=st["hidden"], alphas=st["alphas"])
    for num, ts in SEL:
        if ts <= t < ts + 0.6:
            select_flash(c, t, ts + 0.05, s3.FOCUS_POS[0], s3.FOCUS_POS[1], 0.8)
    if C57 <= t < C57 + 0.6:
        x, y = card_xy(6, 1.0)
        select_flash(c, t, C57 + 0.05, x, y, 0.7)
    # the music box above his palm (card 8 becomes it)
    bi = smoothstep((t - BOX_IN - 0.2) / 0.7) * (1.0 - smoothstep((t - BOX_OUT) / 0.6))
    if bi > 0.003:
        px, py = FAN
        sc = lerp(0.35, 0.62, ease_out(clamp((t - BOX_IN - 0.2) / 0.9)))
        sc *= 1.0 - 0.3 * smoothstep((t - BOX_OUT) / 0.6)
        glow(c, px, py - 40, 90, "#FFD9A0", 0.25 * bi)
        fx.draw_music_box(c, t, px, py - 14, sc, bi)


def draw_world_fx(c, t):
    """Stage-space effects drawn over the set and the characters."""
    if CH0 - 0.1 <= t <= CH1 + 0.3:
        amt = smoothstep((t - CH0) / 0.6) * (1.0 - smoothstep((t - CH1) / 0.3))
        fx.draw_pixel_sparkles(c, t, area=(-20, 420, 175, 1000), amount=amt, seed=31, px=7.0, count=6)
        fx.draw_pixel_sparkles(c, t, area=(335, 560, 520, 1000), amount=amt, seed=37, px=7.0, count=5)
        fx.draw_pixel_sparkles(c, t, area=(60, 330, 470, 520), amount=amt, seed=41, px=7.0, count=5)
        fx.draw_pixel_sparkles(c, t, area=(250, 1050, 520, 1150), amount=amt * smoothstep((t - CH0 - 2.0) / 0.8),
                               seed=43, px=6.0, count=4)
    if LL0 <= t <= T1:
        m = smoothstep((t - LL0) / 1.5) * (1.0 - smoothstep((t - LL1) / 2.0))
        if m > 0.003:
            fx.draw_motes(c, t, area=(-60, 200, 760, 1150), density=0.55 * m, env=music_env("alt_lullaby", t),
                          color="amber_soft", seed=12, rise=12.0, alpha=0.7)


# =========================================================================== door
def door(t):
    if t < EXIT:
        return 0.0
    if t < EXIT + 0.55:
        return ease_out((t - EXIT) / 0.55)
    if t < DOOR_SHUT:
        return 1.0
    return 1.0 - clamp((t - DOOR_SHUT) / min(0.4, T1 - DOOR_SHUT - 0.07)) ** 2     # shut by the S5 cut


def _door_clip_rect(d):
    return skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(d), FLOOR + 4)


# =========================================================================== cameras
def _rae_head(t):
    return R.head_center(rae_pose(t))


SEAT_FACE = s3._seat_face()


def camera(name, t, a, b):
    u = clamp((t - a) / max(1e-3, b - a))
    if name == "P2K":                   # 3-shot: card 2, the snort ... then one slow push into her close-up
        p0 = KZ0 + 1.6
        if t < p0:
            return drift(Camera(394.0, 610.0, 1.32), Camera(390.0, 598.0, 1.38), t, a, p0)
        v = smoothstep(clamp((t - p0) / 4.0))
        hx, hy = smoothed(_rae_head, t, 5, 0.1)
        fxx, fyy = lerp(SEAT_FACE[0], hx, 0.6 * v), lerp(SEAT_FACE[1], hy, 0.6 * v)
        z = 1.38 * (3.15 / 1.38) ** v
        sx0 = W / 2 + (SEAT_FACE[0] - 390.0) * 1.38
        sy0 = H / 2 + (SEAT_FACE[1] - 598.0) * 1.38
        return _face_cam(fxx, fyy, z, lerp(sx0, 356.0, v), lerp(sy0, 540.0, v))
    if name == "R12P3":                 # two-shot: "...ALSO good?!" - his palm is already coming up - card 3
        return drift(Camera(384.0, 668.0, 1.42), Camera(408.0, 592.0, 1.46), t, a, b)
    if name == "C":
        return drift(Camera(196.0, 762.0, 1.55), Camera(198.0, 756.0, 1.6), t, CUT_C, CUT_P4)
    if name == "QI":                                        # insert: the traitorous foot
        return drift(Camera(384.0, 1098.0, 3.5), Camera(386.0, 1100.0, 3.6), t, a, b)
    if name == "P4":
        return drift(Camera(386.0, 612.0, 1.42), Camera(384.0, 604.0, 1.5), t, a, b)
    if name == "L":                     # "lo-fi beats to quietly fall apart to": the album-cover wide
        return drift(Camera(352.0, 640.0, 1.04), Camera(330.0, 652.0, 1.1), t, a, b)
    if name in ("L2", "R15", "LC"):
        hx, hy = smoothed(_rae_head, t, 5, 0.1)
        fxx, fyy = lerp(SEAT_FACE[0], hx, 0.6), lerp(SEAT_FACE[1], hy, 0.6)
        z0 = {"L2": 3.15, "R15": 3.12, "LC": 3.2}[name]
        return _face_cam(fxx, fyy, z0 * (1.0 + 0.06 * ease_in_out(u)), 356.0, 540.0)
    if name == "P57":
        return drift(Camera(390.0, 618.0, 1.28), Camera(388.0, 610.0, 1.33), t, a, b)
    if name == "P8":
        return drift(Camera(404.0, 600.0, 1.36), Camera(406.0, 590.0, 1.46), t, a, b)
    if name == "LW":
        return drift(Camera(372.0, 700.0, 1.04), Camera(374.0, 690.0, 1.1), t, a, b)
    if name == "LS":
        return drift(Camera(320.0, 760.0, 1.22), Camera(318.0, 730.0, 1.26), t, a, b)
    if name == "LQ":                                        # Quill + music box; Rae (standing) just out left
        return drift(Camera(548.0, 560.0, 2.1), Camera(548.0, 556.0, 2.18), t, a, b)
    if name == "N":                                         # medium two-shot: backing away from his offer
        return drift(Camera(392.0, 652.0, 1.3), Camera(386.0, 656.0, 1.34), t, a, b)
    if name == "X":
        return drift(Camera(196.0, 700.0, 0.82), Camera(176.0, 706.0, 0.86), t, a, b)
    return Camera()


# =========================================================================== render
def render(canvas, t):
    name, a, b = shot_at(t)
    if name == "s3":
        s3.render(canvas, t)
        return
    cam = camera(name, t, a, b)
    light, warm, rain = room(t)
    dr = door(t)
    rp = rae_pose(t)
    qp = quill_pose(t)
    c = canvas
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, t, light=light, door=dr, rain=rain, warm=warm)
    bm = bench_mug(t)
    if bm is not None:
        R.draw_mug(c, *bm)
    Q.draw(c, qp, t)
    # once she is on her feet her head is up among the cards: the holograms hang BEHIND her from the
    # cut before she rises (no visible pop: seated, nothing overlaps)
    cards_behind = t >= CUT_LS
    if cards_behind:
        draw_cards(c, t)
    if t >= IN_DOOR and rp.x < 200:
        c.save()
        c.clipRect(_door_clip_rect(dr), skia.ClipOp.kDifference, True)
        if rp.x < env.DOOR_X1 + 60:
            # through the doorway she is behind the wall: whatever reaches past the right jamb (her
            # pointing arm) slides behind it as she goes
            xc = env.DOOR_X1 + max(0.0, 2.2 * (rp.x + 60.0))
            c.clipRect(skia.Rect(xc, -2000, 4000, 4000), skia.ClipOp.kDifference, True)
        R.draw(c, rp, t + TAP_SHIFT)
        c.restore()
    else:
        R.draw(c, rp, t + TAP_SHIFT)
    # (until she backs through it she stands in FRONT of the door: no lintel over her hair)
    env.draw_lounge_front(c, t, light=light, door=dr, warm=warm, lintel=not (BACK1 - 0.6 < t < IN_DOOR))
    draw_world_fx(c, t)
    if not cards_behind:
        draw_cards(c, t)
    c.restore()
