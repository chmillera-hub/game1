"""S4 - "The others" (BIBLE section 4, S4).

Quill works through the menu. Each cardN beat: his palm comes up, a small wrist flick, the card slides
to centre and enlarges (holo_select), the rest dim - and we cut to Rae while the alternate plays:
  kazoo   held-in laugh -> snort -> giggles -> the grin crumples, eyes well -> "Why is the kazoo one ALSO
          good?!" (laugh-crying, palm up + mug shrug)
  arcade  she sets the mug down and braces; pixel sparkles; her head bobs and her foot taps against her will
          (medium-wide + foot insert); "Stop. My foot is tapping." - she grips her knee
  lo-fi   she takes the mug back for comfort; rain on the window, warm dim light; she hugs herself around
          the mug, slow nods; close-up: both hands cupping the mug under her chin, lip trembling, "That is
          not fair." (the rain and the dim light ebb away inside the close-up)
  5-7     theremin cards wobble and fold away on the wail's onsets as Quill closes his hand; she flinches
          into her mug; "...Thank you."
  8       Quill + card 8; her reaction to "eleven seconds": a fortifying two-handed sip
  lullaby warm light, a tiny music box turning above his palm; she comes undone (eyes squeezed, tears,
          mug pressed to her heart, other hand on her chest), sets the mug down and rises slowly;
          "Nope. Nope nope nope." - palm out, hand on her heart; snatches the mug, backs to the door
          pointing at him, waits for it and is gone; the door shuts; the cards begin to fade.

render(canvas, t) is a pure function of absolute time t; times derive from named beats / lines / music
cues / SFX. Until the first cut (card2) the S3 close-up simply continues (anim.scenes.s3.render).
Shared helpers (fan drawing, arm tracks, gaze, blinks, mug solver) live in anim.scenes.s3.

Rig note (char_rae far arm): the far arm's draw layer flips from behind the torso to over it at across 0.25,
and its face / knee "magnets" blend over across 0.18..0.35, so a far-arm blend through that band pops. Here
the far arm crosses the band only on a cut (R4 -> L, cut on action) or inside a fast move in the wide exit
shot; everything else keeps it either low (hand on the lap / knee, palm-up gestures) or >= 0.4 (hugging,
cupping the mug, hand on chest). The mug never changes hands: it goes bench <-> near hand only.

Shot list (orientation only):
  s3 CU    S4 start -> card2       S3's close-up of Rae (dawning dread) continues
  P2       card2 -> kazoo          THREE-SHOT: "Number two..." card 2 pops out to centre
  K        kazoo                   Rae MEDIUM (cut on the first kazoo note): held-in laugh, snort, giggles;
                                   slow push into a CLOSE-UP as the grin crumples
  R12      r12                     Rae MEDIUM, a little wider: "Why is the kazoo one ALSO good?!"
  P3       card3 -> chip           THREE-SHOT: "Number three..." - she sets her mug down beside her, braces
  C        chip (+ r13)            Rae MEDIUM-WIDE (feet in frame): head bob, foot tap, grips her knee
     QI    (1.1 s insert)          the traitorous foot (insert)
  P4       card4                   Quill MEDIUM + card 4: "Number four. Lo-fi beats..." (deadpan)
  R4       "...fall apart to."     Rae MEDIUM: she eyes her mug on the bench and takes it back for comfort
  L        lo-fi                   WIDE "album cover": rain, warm dim, she curls around the mug (cut on action)
  L2       lo-fi end + r14         CLOSE-UP: cupping the mug under her chin; "That is not fair."
  P57      card5_7 -> r15          TWO-SHOT: cards 5-7 wobble and fold away, she flinches at the wail
  R15      r15                     CLOSE-UP: "...Thank you."
  P8       card8                   Quill MEDIUM + card 8: "And number eight. A lullaby."
  R8       "It is eleven seconds"  Rae MEDIUM CLOSE: a fortifying two-handed sip
  LW       lullaby start           WIDE warm two-shot: card 8 becomes a music box above his palm
  LC       lullaby                 CLOSE-UP Rae: undone
  LS       rae_stand_start         MEDIUM-WIDE: mug down on the bench, she rises slowly, hands on her heart
  LQ       lullaby end             MEDIUM Quill + music box, last notes
  N        r16 "Nope..."           MEDIUM TWO-SHOT: palm out, head shakes, first step back
  X        rae_backs_out -> end    WIDE (door + Quill): snatches the mug, backs to the door pointing,
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
from config import MUSIC_ENV

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

Q08, Q08E = S("q08"), E("q08")
R12, R12E = S("r12"), E("r12")
Q09, Q09E = S("q09"), E("q09")
R13, R13E = S("r13"), E("r13")
Q10, Q10E = S("q10"), E("q10")
R14, R14E = S("r14"), E("r14")
Q11 = S("q11")
R15, R15E = S("r15"), E("r15")
Q12 = S("q12")
R16, R16E = S("r16"), E("r16")
# word landmarks inside lines (offsets read off the lip-sync envelopes)
FALL_APART = Q10 + 2.3                  # "...to quietly fall apart to."
SPARE = Q11 + 2.45                      # "I will spare you."
ELEVEN = Q12 + 2.0                      # "It is eleven seconds long."
PALM4_DOWN = Q10 + 1.55                 # after "Lo-fi beats...": the palm comes down before Rae's medium


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

# ---------------------------------------------------------------- cuts
CUT_P2 = C2 - 0.05
CUT_K = KZ0 + 0.12                      # on the first kazoo notes: straight to her face
CUT_R12 = R12 - 0.15                    # (= the end of the kazoo) her outburst needs the hands in frame
CUT_P3 = C3 - 0.45                      # back to the room as his palm comes up for card 3
CUT_C = CH0 + 0.05
CUT_QI = CH0 + 3.1
CUT_CB = CH0 + 4.2
CUT_P4 = C4 - 0.45                      # Quill medium + card 4 ...
CUT_R4 = Q10 + 2.1                      # ... Rae medium for "...to quietly fall apart to" (reaches for her mug)
CUT_L = LF0 + 0.05                      # cut on action: she starts curling around the mug in R4
CUT_L2 = LF0 + 3.3
CUT_P57 = C57 - 0.45
CUT_R15 = R15 - 0.2
CUT_P8 = C8 - 0.6
CUT_R8 = ELEVEN - 0.1
CUT_LW = LL0 - 0.06
CUT_LC = LL0 + 1.95
CUT_LS = STAND - 0.1
CUT_LQ = STAND + 3.55
CUT_N = LL1 + 0.3
CUT_X = BACKS - 0.1

SHOTS = [("s3", T0), ("P2", CUT_P2), ("K", CUT_K), ("R12", CUT_R12), ("P3", CUT_P3), ("C", CUT_C),
         ("QI", CUT_QI), ("C", CUT_CB), ("P4", CUT_P4), ("R4", CUT_R4), ("L", CUT_L), ("L2", CUT_L2), ("P57", CUT_P57),
         ("R15", CUT_R15), ("P8", CUT_P8), ("R8", CUT_R8), ("LW", CUT_LW), ("LC", CUT_LC), ("LS", CUT_LS),
         ("LQ", CUT_LQ), ("N", CUT_N), ("X", CUT_X)]


def shot_at(t):
    cur = SHOTS[0]
    nxt = T1 + 1.0
    for i, (name, a) in enumerate(SHOTS):
        if t >= a:
            cur = (name, a)
            nxt = SHOTS[i + 1][1] if i + 1 < len(SHOTS) else T1 + 1.0
    return cur[0], cur[1], nxt


# =========================================================================== lighting
# lo-fi: dims / warms / rains in on the wide; ebbs away inside the close-up as the cue ends (no snap on the cut)
LOFI_DIM = Track([(CUT_L, 0.0), (CUT_L + 1.4, 1.0, "io"), (LF1 + 0.3, 1.0), (R14E - 0.05, 0.0, "io")])
RAIN = Track([(CUT_L, 0.0), (CUT_L + 1.8, 1.0, "io"), (LF1 + 0.3, 1.0), (R14E - 0.05, 0.0, "io")])
LULL_WARM = Track([(LL0, 0.0), (LL0 + 1.6, 1.0, "io"), (LL1 + 0.25, 1.0), (LL1 + 2.3, 0.0, "io")])
TINT_COOL, TINT_WARM = (20, 30, 70), (70, 35, 10)


def room(t):
    """(light, warm, rain) of the lounge."""
    ld = LOFI_DIM(t)
    lw = LULL_WARM(t)
    return 1.0 - 0.2 * ld, max(0.45 * ld, lw), RAIN(t)


def char_lighting(t):
    light, warm, _ = room(t)
    d = env.char_light(light, warm)
    # env.char_light flips the tint hue at warm 0.5; blend it instead (no one-frame colour jump)
    k = smoothstep(clamp(warm))
    d["tint"] = tuple(lerp(a, b, k) for a, b in zip(TINT_COOL, TINT_WARM))
    return d


# =========================================================================== Rae: arm poses
A = R.ARMS
HOLD = A["hold_mug"]
CLUTCH = s3.CLUTCH
LAP_R = s3.LAP_R
LAP_L = s3.LAP_L
MUG_RAISE = arm(A["shrug"], hand="hold", shoulder=14.0, elbow=66.0, across=-0.3)    # exasperated "why?!" shrug
LIFT_L = ArmPose(shoulder=8.0, elbow=92.0, wrist=4.0, hand="relaxed")             # far hand lifted off the thigh
PALM_OUT_L = ArmPose(shoulder=30.0, elbow=110.0, wrist=-10.0, hand="palm_up")     # "...why?!" palm up
KNEE_R = ArmPose(shoulder=24.0, elbow=34.0, wrist=6.0, hand="relaxed")            # near hand braced on her knee
GRIP_R = A["grip_knee"]
# lo-fi: near hand holds the mug to her chest / under her chin, the far arm wraps round (always across >= 0.4)
MUG_CHEST_R = ArmPose(shoulder=18.0, elbow=118.0, wrist=0.0, hand="hold", across=0.5)
MUG_CHIN_R = ArmPose(shoulder=24.0, elbow=123.0, wrist=0.0, hand="hold", across=0.45)
MUG_HUDDLE_R = ArmPose(shoulder=14.0, elbow=128.0, wrist=0.0, hand="hold", across=0.52)   # flinch: pulled in
MUG_HEART_R = ArmPose(shoulder=13.0, elbow=126.0, wrist=4.0, hand="hold", across=0.56)    # pressed to her heart
SIP_R = A["sip"]
HUG_L = ArmPose(shoulder=22.0, elbow=128.0, wrist=8.0, hand="relaxed", across=1.0)         # hugging herself
CUP_L = ArmPose(shoulder=26.0, elbow=120.0, wrist=14.0, hand="open", across=0.8)            # cupping the mug (chin)
CUP_CHEST_L = ArmPose(shoulder=18.0, elbow=118.0, wrist=14.0, hand="open", across=0.85)     # (chest height)
CUP_HEART_L = ArmPose(shoulder=15.0, elbow=124.0, wrist=14.0, hand="open", across=0.86)     # (pressed to her heart)
HUDDLE_L = ArmPose(shoulder=14.0, elbow=126.0, wrist=14.0, hand="open", across=0.86)
SIP_L = ArmPose(shoulder=50.0, elbow=110.0, wrist=10.0, hand="open", across=0.6)           # steadies it from below
CHEST_L = ArmPose(shoulder=22.0, elbow=116.0, wrist=10.0, hand="open", across=0.62)        # hand flat on her chest
CHEST_R = A["hand_on_chest"]
REST = A["rest"]
NOPE_R = ArmPose(shoulder=62.0, elbow=84.0, wrist=-34.0, hand="palm_out", across=0.0)      # palm out at him
BAL_L = ArmPose(shoulder=26.0, elbow=40.0, wrist=0.0, hand="open", across=0.0)             # out for balance (dip)
POINT_L = ArmPose(shoulder=84.0, elbow=6.0, wrist=0.0, hand="point")
CARRY_R = arm(HOLD, shoulder=20.0, elbow=96.0, across=0.3)

# ---------------------------------------------------------------- the mug: bench <-> near hand only
MUG_SIDE = (150.0, SEAT_Y)              # on the bench just behind her (her far side; the door side)
PLACE1_T = Q09 + 1.55                   # "...for an arcade cabinet": she sets it down to brace herself
PICK_T = FALL_APART + 0.35              # "...to quietly fall apart to": she takes it back for comfort
PLACE_T = STAND + 0.62                  # lullaby: sets it down before she rises
RISE0, RISE1 = STAND + 0.95, STAND + 2.45
CYCLE = R.WALK_ADVANCE
STAND_X = SEAT_X + 32.0                 # pelvis once upright (feet tucked back under her as she rises)
SIP0 = ELEVEN + 0.75                    # the fortifying sip
SIP1 = SIP0 + 0.9

# backing out: walk phase keys (phase decreases = walking backward; x tied to phase so feet never skate)
STEP0, STEP1 = R16 + 0.3, R16 + 1.05            # first backward steps during "nope nope nope"
GRAB_T = STEP1 + 0.25                           # snatches the mug off the bench
BACK0, BACK1 = GRAB_T + 0.18, EXIT - 0.12      # backing to the door while she points ("I'm getting out")
IN_DOOR = EXIT + 0.36                           # the door is ~96 % open: from here she is behind the door plane
OUT0 = IN_DOOR + 0.02                           # ... and scurries out
OUT1 = OUT0 + 0.8
# she waits for the door at phase -2.0 (both feet planted; pelvis x ~ -22: her whole silhouette stays right of
# the left jamb, x -140, while she is still in front of the wall) and is fully behind the wall at phase -3.75
WALK_KEYS = [(STEP0, 0.25), (STEP1, -0.5), (BACK0, -0.5), (BACK1, -2.0), (OUT0, -2.0), (OUT1, -3.75)]


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


RISE_X = Track([(RISE0, SEAT_X), (RISE1, STAND_X, "io")])
RISE_SIT = Track([(RISE0, 1.0), (RISE0 + 0.25, 0.92, "io"), (RISE1, 0.0, "io")])


def rae_x(t):
    ph = walk_phase(t)
    if ph is None:
        return RISE_X(t)
    return STAND_X + (ph - 0.25) * CYCLE


# =========================================================================== Rae: body / face tracks
def _rae_tracks():
    d = {}
    P2s = C2
    WIPE = CUT_QI + 0.3                      # far-cheek trail reset while we are on the foot insert
    # ---------------- body
    d["lean"] = Track([
        (T0, 2.5), (P2s, 2.5), (P2s + 0.1, 0.0, "out"), (Q08 + 2.4, 1.0), (Q08 + 2.9, -2.0),
        (KZ0 + 0.3, -2.0), (KZ0 + 0.46, -3.5), (KZ0 + 0.62, 6.0, "io"), (KZ0 + 0.88, -3.0), (KZ0 + 2.4, -1.0),
        (KZ0 + 4.5, 3.0), (KZ1, 4.0), (R12 - 0.05, 2.0), (R12 + 0.3, -5.0, "out"), (R12E, -4.0), (R12E + 0.4, 0.0),
        # P3: leans back and over to set the mug down behind her, then braces
        (PLACE1_T - 0.7, 0.5), (PLACE1_T - 0.1, -9.0), (PLACE1_T + 0.25, -8.0), (PLACE1_T + 0.8, 0.0),
        (CH0 - 0.2, 0.0), (CH0 + 0.3, -2.5), (CH0 + 3.0, 0.0), (CH1 - 0.6, 3.0),
        (R13 - 0.05, 3.0), (R13 + 0.15, 10.0, "out"), (R13 + 0.6, 8.0), (R13 + 1.6, 5.0), (R13E, 3.0),
        (C4, 3.0), (Q10 + 1.6, 1.5),
        (PICK_T - 0.55, 1.0), (PICK_T - 0.1, -9.0), (PICK_T + 0.25, -7.0), (PICK_T + 0.8, 0.0),
        (CUT_L - 0.3, 0.0), (CUT_L + 0.8, 5.0), (LF0 + 2.0, 6.0), (LF1, 7.0), (R14, 5.0), (R14E, 4.0),
        (C57, 2.0), (Q11 + 1.6, 3.0), (TH0 - 0.05, 3.0), (TH0 + 0.1, -6.0, "out"), (TH0 + 1.2, -4.0),
        (TH1, 0.0), (R15, 2.0), (R15E, 4.0), (C8, 2.0), (SIP0, 2.0), (SIP0 + 0.4, -2.0), (SIP1, -1.0),
        (SIP1 + 0.5, 2.0), (LL0, 2.0), (LL0 + 2.0, 4.0), (CUT_LC + 1.5, 7.0),
        (STAND, 4.0), (PLACE_T - 0.1, -6.0), (PLACE_T + 0.3, -1.0), (RISE0 + 0.2, 14.0), (RISE1, 2.0),
        (RISE1 + 1.0, -1.0), (LL1, -2.0), (R16 - 0.1, -2.0), (R16 + 0.14, -7.0, "out"), (STEP1, -5.0),
        (GRAB_T - 0.2, -10.0), (GRAB_T + 0.2, -4.0), (BACK1, -5.0), (OUT0, -6.0), (T1 + 1, -8.0)])
    d["bounce"] = Track([
        (T0, 0.0), (KZ0 + 0.3, 0.0), (KZ0 + 0.46, -1.0), (KZ0 + 0.62, 6.0, "io"), (KZ0 + 0.82, -2.0),
        (KZ0 + 1.0, 0.0),
        (R13 - 0.02, 0.0), (R13 + 0.1, 5.0, "out"), (R13 + 0.4, 0.0),
        (TH0 - 0.02, 0.0), (TH0 + 0.1, -5.0, "out"), (TH0 + 0.5, -2.0), (TH1, 0.0),
        (RISE1 - 0.2, 0.0), (RISE1 + 0.2, 3.0), (RISE1 + 0.6, 0.0),
        (R16 - 0.05, 0.0), (R16 + 0.1, -4.0, "out"), (R16 + 0.35, 0.0),
        (GRAB_T - 0.3, 0.0), (GRAB_T - 0.02, 40.0, "io"), (GRAB_T + 0.06, 39.0), (BACK0 + 0.2, 0.0, "io")])
    d["shoulders"] = Track([
        (T0, 0.25), (P2s, 0.25), (P2s + 0.08, 0.38, "out"), (P2s + 0.6, 0.2), (KZ0 + 0.3, 0.2),
        (KZ0 + 0.46, 0.34), (KZ0 + 0.58, 0.45, "out"),
        (KZ0 + 2.5, 0.25), (KZ0 + 4.0, 0.15), (KZ1, 0.2), (R12, 0.35), (R12E + 0.3, 0.1),
        (PLACE1_T + 0.8, 0.1), (CH0 - 0.3, 0.3), (CH0 + 0.4, 0.38), (CH0 + 3.5, 0.2), (R13, 0.4, "out"),
        (R13E, 0.2), (C4, 0.15), (CUT_L - 0.3, 0.2), (CUT_L + 1.0, 0.4), (LF0 + 2.0, 0.42), (LF1, 0.46),
        (R14E, 0.4), (C57 + 0.6, 0.22), (TH0, 0.22), (TH0 + 0.1, 0.72, "out"), (TH0 + 1.2, 0.58), (TH1 + 0.3, 0.18),
        (R15, 0.2), (LL0, 0.15), (CUT_LC, 0.32), (STAND, 0.35), (RISE1, 0.22), (R16, 0.3),
        (R16 + 0.12, 0.5, "out"), (BACK0, 0.4), (OUT0, 0.55), (T1 + 1, 0.55)])
    d["turn"] = Track([(T0, 0.35), (R12, 0.35), (R12 + 0.3, 0.26), (R12E + 0.3, 0.33),
                       (PLACE1_T - 0.6, 0.35), (PLACE1_T - 0.1, 0.28), (PLACE1_T + 0.6, 0.35),
                       (PICK_T - 0.5, 0.35), (PICK_T - 0.1, 0.28), (PICK_T + 0.6, 0.35),
                       (TH0, 0.35), (TH0 + 0.1, 0.42, "out"), (TH1, 0.35),
                       (PLACE_T - 0.5, 0.35), (PLACE_T, 0.3), (PLACE_T + 0.5, 0.35), (RISE1, 0.35),
                       (R16 - 0.05, 0.33), (R16 + 0.15, 0.26, "out"), (STEP0 + 0.2, 0.3), (GRAB_T, 0.36),
                       (T1 + 1, 0.4)])
    # ---------------- head
    d["nod"] = Track([
        (T0, 0.12), (P2s, 0.12), (P2s + 0.4, 0.3), (Q08 + 1.2, 0.25), (Q08 + 2.5, 0.1), (KZ0 + 0.3, 0.08),
        (KZ0 + 0.46, 0.18), (KZ0 + 0.63, -0.28, "io"), (KZ0 + 0.9, 0.25, "io"), (KZ0 + 1.3, 0.05),
        (KZ0 + 3.2, 0.1), (KZ0 + 4.5, 0.22), (KZ1, 0.18), (R12 + 0.3, 0.3), (R12E, 0.15),
        (PLACE1_T - 0.5, 0.15), (PLACE1_T - 0.1, 0.35), (PLACE1_T + 0.5, 0.05),
        (CH0, 0.0), (CH0 + 1.0, -0.05), (CH1, -0.02), (R13 + 0.4, -0.3), (R13 + 1.4, -0.35),
        (R13 + 1.6, 0.0), (R13E, 0.05), (Q10 + 1.0, 0.15), (PICK_T - 0.4, 0.2), (PICK_T, 0.35),
        (PICK_T + 0.6, 0.15), (LF0, 0.12), (LF0 + 1.5, 0.24), (LF1, 0.22), (R14, 0.0), (R14E, -0.12),
        (C57, 0.1), (Q11 + 1.5, -0.1), (TH0, 0.1), (TH0 + 0.1, 0.34, "out"),
        (TH1, 0.05), (R15 - 0.15, 0.05), (R15 - 0.05, -0.12, "out"), (R15 + 0.25, 0.0), (R15E, -0.2),
        (R15E + 0.4, -0.05), (ELEVEN + 0.2, -0.1), (ELEVEN + 0.5, 0.05), (SIP0 + 0.35, -0.2), (SIP1, -0.22),
        (SIP1 + 0.45, 0.1), (LL0, 0.15), (LL0 + 1.5, 0.3), (CUT_LC, -0.2), (STAND - 0.6, -0.3),
        (STAND, 0.0), (PLACE_T, -0.25), (RISE0 + 0.3, 0.05), (RISE1, 0.32), (LL1, 0.28), (R16, 0.1),
        (STEP1, 0.0), (GRAB_T, -0.1), (BACK0, 0.05), (T1 + 1, 0.05)])
    d["tilt"] = Track([
        (T0, -2.0), (P2s, -2.0), (Q08 + 2.0, -2.0), (Q08 + 2.5, -8.0), (KZ0 + 0.4, -6.0), (KZ0 + 0.65, 4.0),
        (KZ0 + 3.0, 2.0), (KZ0 + 4.5, -4.0), (KZ1, -5.0), (R12, -3.0), (R12 + 1.0, 4.0), (R12E, 2.0),
        (CH0, 0.0), (CH0 + 3.5, 3.0), (CH1, 6.0), (R13, 0.0), (R13 + 1.5, -6.0), (R13E, -4.0), (C4, -3.0),
        (Q10 + 1.6, 4.0), (Q10 + 2.6, -6.0), (LF0, -5.0), (LF0 + 3.0, -9.0), (LF1, -8.0), (R14, -4.0),
        (R14E, -6.0), (C57, -2.0), (Q11 + 1.4, -6.0), (TH0, -4.0), (TH0 + 0.1, 6.0, "out"), (TH1, 2.0),
        (R15, -4.0), (R15E, -7.0), (ELEVEN, -3.0), (SIP0, 2.0), (SIP1 + 0.4, -2.0), (LL0, -3.0),
        (CUT_LC, -6.0), (STAND, -4.0), (RISE1, 2.0), (LL1, -2.0), (R16, 0.0), (T1 + 1, -2.0)])
    # ---------------- eyes
    d["lid"] = Track([
        (T0, 1.0), (P2s, 1.0), (Q08 + 2.4, 0.95), (Q08 + 2.9, 0.78), (KZ0 + 0.3, 0.78), (KZ0 + 0.46, 0.62),
        (KZ0 + 0.58, 0.35, "out"),
        (KZ0 + 2.6, 0.45), (KZ0 + 3.4, 0.85), (KZ0 + 4.5, 0.92), (KZ1, 0.85), (R12, 0.7), (R12E, 0.7),
        (R12E + 0.4, 0.85), (CH0 - 0.3, 0.85), (CH0 + 0.3, 0.72), (CH0 + 3.0, 0.75), (CH1 - 1.2, 0.55),
        (CH1 - 0.45, 0.6), (CH1 - 0.3, 1.0, "out"), (R13 + 1.6, 0.9), (R13E, 0.8), (C4, 0.85),
        (Q10 + 1.5, 0.95), (Q10 + 3.0, 0.82), (LF0, 0.8), (LF0 + 2.0, 0.66), (LF1, 0.64), (R14, 0.78),
        (R14E, 0.7), (C57, 0.88), (Q11 + 1.6, 1.0), (TH0 - 0.05, 0.6), (TH0 + 0.06, 0.1, "out"),
        (TH1 - 0.3, 0.18), (TH1 + 0.2, 0.85), (R15, 0.6), (R15E, 0.55), (C8, 0.8), (ELEVEN, 0.78),
        (ELEVEN + 0.3, 0.92), (SIP0 + 0.3, 0.5), (SIP1, 0.45), (SIP1 + 0.4, 0.8), (LL0, 0.85),
        (LL0 + 1.6, 0.75), (CUT_LC, 0.3), (CUT_LC + 0.5, 0.06), (STAND - 0.5, 0.08), (STAND, 0.55),
        (RISE1, 0.85), (LL1, 0.8), (LL1 + 0.3, 0.9), (R16, 1.0), (T1 + 1, 1.0)])
    d["wide"] = Track([
        (T0, 0.55), (P2s, 0.55), (P2s + 0.1, 0.7, "out"), (Q08 + 1.0, 0.3), (Q08 + 2.4, 0.0),
        (KZ0 + 3.4, 0.0), (KZ0 + 4.0, 0.15), (KZ1, 0.0), (CH0, 0.0), (CH1 - 0.45, 0.0), (CH1 - 0.3, 0.7, "out"),
        (R13 + 0.4, 0.35), (R13E, 0.1), (Q10 + 0.9, 0.0), (Q10 + 1.2, 0.35, "out"), (Q10 + 2.4, 0.15),
        (LF0, 0.0), (C57, 0.1), (Q11 + 1.4, 0.6), (Q11 + 2.4, 0.2), (TH0, 0.0), (TH1 + 0.1, 0.0),
        (TH1 + 0.3, 0.2), (R15, 0.0), (ELEVEN + 0.2, 0.0), (ELEVEN + 0.45, 0.35, "out"), (SIP0, 0.1),
        (LL0, 0.0), (LL1, 0.0), (LL1 + 0.4, 0.3), (R16, 0.75, "out"),
        (R16 + 1.0, 0.5), (GRAB_T, 0.35), (OUT0 - 0.15, 0.4), (OUT0, 0.85, "out"), (T1 + 1, 0.7)])
    d["blinks"] = [
        (P2s + 0.02, 0.13), (Q08 + 1.0, 0.16), (Q08 + 2.55, 0.15), (KZ0 + 2.9, 0.2), (KZ0 + 4.2, 0.3),
        (R12E + 0.15, 0.18), (PLACE1_T + 0.45, 0.15), (CH0 + 0.2, 0.15), (CH0 + 2.2, 0.16), (R13 + 0.9, 0.15),
        (R13 + 1.65, 0.15), (C4 + 0.05, 0.14), (Q10 + 1.0, 0.14), (PICK_T + 0.5, 0.18), (LF0 + 0.9, 0.3),
        (LF0 + 3.1, 0.34), (LF1 - 0.9, 0.3), (R14E + 0.15, 0.25), (C57 + 0.02, 0.14), (Q11 + 2.2, 0.3),
        (TH1 + 0.35, 0.18), (C8 + 0.05, 0.14), (C8 + 1.6, 0.2), (ELEVEN + 0.05, 0.16), (LL0 + 0.8, 0.22),
        (STAND + 0.3, 0.25), (RISE1 + 0.6, 0.3), (LL1 + 0.35, 0.18), (R16 + 0.5, 0.12), (BACK0 + 0.4, 0.14),
        (OUT0 - 0.25, 0.12)]
    d["pupil"] = Track([(T0, 0.92), (P2s, 0.92), (P2s + 0.3, 1.1), (KZ0, 1.05), (KZ0 + 4.0, 1.2), (CH0, 1.0),
                        (LF0, 1.1), (LF0 + 3.0, 1.25), (C57, 1.0), (TH0, 0.85), (TH1, 1.0), (LL0, 1.1),
                        (LL0 + 1.5, 1.3), (LL1, 1.3), (R16, 0.9), (T1 + 1, 0.9)])
    d["squint"] = Track([
        (T0, 0.0), (KZ0 + 0.3, 0.0), (KZ0 + 0.46, 0.3), (KZ0 + 0.58, 0.7, "out"), (KZ0 + 2.6, 0.55),
        (KZ0 + 3.6, 0.2), (KZ1, 0.25), (R12, 0.45), (R12E, 0.5), (R12E + 0.5, 0.15), (CH0 - 0.3, 0.1),
        (CH0 + 0.3, 0.2), (CH1 - 1.2, 0.3), (CH1 - 0.3, 0.0), (LF0, 0.0), (LF0 + 2.5, 0.18), (R14, 0.3),
        (R14E, 0.25), (C57, 0.05), (TH0, 0.05), (TH0 + 0.06, 0.85, "out"), (TH1 - 0.2, 0.7), (TH1 + 0.2, 0.1),
        (R15, 0.35), (R15E, 0.35), (C8, 0.1), (SIP0 + 0.3, 0.3), (SIP1 + 0.4, 0.1), (LL0 + 1.6, 0.15),
        (CUT_LC + 0.4, 0.8), (STAND, 0.6), (RISE1, 0.2), (LL1, 0.15), (R16, 0.0)])
    STARS = (-0.3, -0.62)
    QU = (0.62, -0.36)              # Quill, seated
    CARD = (0.42, -0.74)            # the focused card, seated
    MUGB = (-0.55, 0.55)            # the mug on the bench behind her
    d["gaze"] = gaze([
        (T0, (0.6, -0.4)),
        (P2s + 0.04, CARD, 0.12), (Q08 + 1.4, (0.5, -0.5)), (Q08 + 1.9, CARD), (Q08 + 2.5, QU),
        (KZ0 + 0.1, CARD), (KZ0 + 0.4, (0.25, 0.15), 0.1), (KZ0 + 0.6, (0.2, 0.32), 0.1),       # snort: eyes down
        (KZ0 + 1.6, (0.4, -0.5)), (KZ0 + 2.4, (0.1, 0.1)), (KZ0 + 3.3, CARD, 0.3),
        (KZ0 + 4.6, (0.38, -0.66)), (KZ1 - 0.3, QU),
        (R12 + 0.5, (0.55, -0.45)), (R12E + 0.2, QU),
        (C3 + 0.05, CARD, 0.12), (PLACE1_T - 0.55, MUGB, 0.14), (PLACE1_T + 0.3, CARD, 0.14),
        (CH0 - 0.4, (0.55, -0.6)),
        (CH0 + 0.15, (0.0, -0.1)), (CH0 + 1.6, (0.2, -0.3)), (CH0 + 2.6, (0.05, -0.15)),
        (CH1 - 1.2, (0.2, -0.45), 0.4), (CH1 - 0.3, (0.3, 0.85), 0.12),                       # ...the FOOT
        (R13 + 0.35, (0.35, 0.9)), (R13 + 1.55, QU, 0.12), (R13E + 0.2, (0.55, -0.42)),
        (C4 + 0.03, CARD, 0.12), (Q10 + 1.6, QU), (PICK_T - 0.5, MUGB, 0.14), (PICK_T + 0.35, (0.4, -0.3), 0.2),
        (LF0 + 0.3, STARS, 0.5), (LF0 + 2.6, (-0.4, -0.5), 0.6), (LF0 + 4.5, (0.15, 0.3), 0.8),
        (LF1 - 0.4, (0.45, -0.25), 0.4), (R14 + 0.2, QU),
        (C57 + 0.03, (0.3, -0.85), 0.12), (Q11 + 1.2, (0.5, -0.8)), (Q11 + 2.5, QU),
        (TH0 + 0.6, (0.3, -0.8)), (TH1 - 0.1, (0.38, -0.82)), (TH1 + 0.25, QU),
        (R15 + 0.1, (0.45, -0.25)), (R15E + 0.1, (0.6, -0.42)),
        (C8 + 0.03, CARD, 0.12), (Q12 + 1.4, QU), (ELEVEN + 0.1, (0.55, -0.45)), (SIP0, (0.2, 0.3), 0.2),
        (SIP1 + 0.3, QU, 0.2),
        (LL0 + 0.2, (0.62, -0.48), 0.4),                                                        # the music box
        (CUT_LC - 0.4, (0.55, -0.4)), (STAND + 0.2, (0.55, -0.42)),
        (PLACE_T - 0.35, MUGB, 0.2), (PLACE_T + 0.25, (0.55, -0.3), 0.3),
        (RISE1, (0.62, -0.05), 0.4), (LL1 + 0.4, (0.6, -0.1)),
        (R16 + 0.6, (0.62, -0.12)), (GRAB_T - 0.35, (-0.6, 0.3), 0.12), (GRAB_T + 0.12, (0.62, -0.1), 0.12),
        (BACK1 + 0.08, (-0.85, 0.0), 0.12), (OUT0 - 0.12, (0.62, -0.1), 0.12),          # the door ... him
    ])
    # ---------------- brows / mouth
    d["brow_raise"] = Track([
        (T0, 0.6), (P2s, 0.6), (P2s + 0.1, 0.8, "out"), (Q08 + 1.5, 0.6), (Q08 + 2.4, 0.5), (Q08 + 2.9, 0.3),
        (KZ0 + 0.3, 0.2), (KZ0 + 0.46, 0.05), (KZ0 + 0.58, 0.55, "out"), (KZ0 + 2.5, 0.35), (KZ0 + 4.0, 0.5),
        (KZ1, 0.5), (R12, 0.6), (R12 + 0.8, 0.85), (R12E, 0.6), (C3, 0.5), (PLACE1_T + 0.6, 0.25),
        (CH0, 0.15), (CH0 + 0.3, 0.0), (CH1 - 1.2, 0.2),
        (CH1 - 0.3, 0.85, "out"), (R13, 0.4), (R13 + 1.6, 0.55), (R13E, 0.35), (Q10 + 1.2, 0.75, "out"),
        (Q10 + 3.0, 0.5), (LF0, 0.45), (LF1, 0.4), (R14, 0.5), (C57, 0.4), (Q11 + 1.4, 0.8), (Q11 + 2.6, 0.4),
        (TH0, 0.3), (TH0 + 0.08, 0.1, "out"), (TH1, 0.3), (R15, 0.45), (C8, 0.45), (ELEVEN + 0.2, 0.45),
        (ELEVEN + 0.45, 0.85, "out"), (SIP0, 0.5), (SIP1 + 0.4, 0.4), (LL0, 0.4), (LL0 + 1.5, 0.55),
        (CUT_LC, 0.35), (STAND, 0.45), (RISE1, 0.6), (R16, 0.85, "out"), (R16 + 1.2, 0.7), (OUT0, 0.9),
        (T1 + 1, 0.85)])
    d["worry"] = Track([
        (T0, 0.8), (P2s, 0.8), (Q08 + 2.4, 0.5), (Q08 + 2.9, 0.2), (KZ0 + 0.5, 0.15), (KZ0 + 2.5, 0.2),
        (KZ0 + 3.4, 0.45), (KZ0 + 4.6, 0.8), (KZ1, 0.85), (R12, 0.75), (R12E, 0.7), (R12E + 0.6, 0.5),
        (CH0, 0.35), (CH0 + 0.3, 0.0), (CH1 - 0.3, 0.3), (R13, 0.5), (R13E, 0.45), (C4, 0.4),
        (Q10 + 1.2, 0.5), (Q10 + 3.0, 0.75), (LF0 + 1.5, 0.75), (LF0 + 4.0, 0.9), (LF1, 0.92), (R14, 0.95),
        (R14E, 0.9), (C57, 0.55), (Q11 + 1.4, 0.8), (Q11 + 2.6, 0.55), (TH0, 0.5), (TH1, 0.6),
        (R15, 0.85), (R15E, 0.85), (C8, 0.6), (ELEVEN + 0.45, 0.3), (SIP1, 0.5), (LL0, 0.6), (LL0 + 1.5, 0.8),
        (CUT_LC, 1.0), (STAND, 0.95), (RISE1, 0.85), (LL1, 0.85), (R16, 0.7), (OUT0, 0.75), (T1 + 1, 0.75)])
    d["furrow"] = Track([
        (T0, 0.12), (P2s, 0.12), (Q08 + 2.4, 0.15), (Q08 + 2.9, 0.55, "out"), (KZ0 + 0.3, 0.55),
        (KZ0 + 0.46, 0.65), (KZ0 + 0.58, 0.0, "out"), (KZ1, 0.0), (R12 + 0.4, 0.2), (R12E, 0.1),
        (PLACE1_T + 0.4, 0.15), (CH0 - 0.3, 0.45), (CH0 + 0.3, 0.55),
        (CH0 + 3.0, 0.35), (CH1 - 1.2, 0.1), (CH1 - 0.3, 0.0), (R13, 0.45), (R13E, 0.4), (C4, 0.3),
        (Q10 + 1.2, 0.05), (LF0, 0.0), (R14, 0.35), (R14E, 0.3), (C57, 0.15), (TH0, 0.1),
        (TH0 + 0.08, 0.6, "out"), (TH1, 0.2), (R15, 0.0), (ELEVEN, 0.1), (SIP0, 0.3), (SIP1 + 0.4, 0.1),
        (CUT_LC, 0.2), (STAND, 0.1), (R16, 0.3), (T1 + 1, 0.25)])
    d["open"] = Track([
        (T0, 0.12), (P2s, 0.12), (Q08 + 2.4, 0.08), (Q08 + 2.9, 0.0), (KZ0 + 0.46, 0.0), (KZ0 + 0.58, 0.42, "out"),
        (KZ0 + 2.6, 0.35), (KZ0 + 3.6, 0.15), (KZ1, 0.12), (R12E, 0.1), (R12E + 0.3, 0.2), (CH0 - 0.3, 0.0),
        (CH1 - 1.2, 0.08), (CH1 - 0.3, 0.3, "out"), (R13, 0.0), (R13E, 0.0),
        (Q10 + 3.0, 0.05), (LF0, 0.06), (LF1, 0.1), (R14E, 0.1), (Q11 + 1.4, 0.15), (TH0, 0.05),
        (TH0 + 0.08, 0.35, "out"), (TH1 - 0.3, 0.3), (TH1 + 0.2, 0.08), (R15E, 0.05), (ELEVEN + 0.45, 0.12),
        (SIP0, 0.05), (LL0 + 1.5, 0.15),
        (CUT_LC + 0.5, 0.32), (STAND, 0.25), (RISE1, 0.18), (LL1, 0.15), (R16 - 0.2, 0.05),
        (R16E, 0.0), (R16E + 0.2, 0.25), (T1 + 1, 0.2)])
    d["round"] = Track([(T0, 0.0), (KZ0 + 2.6, 0.0), (KZ1, 0.1), (CH1 - 0.3, 0.6), (R13, 0.0),
                        (TH0 + 0.08, 0.0), (ELEVEN + 0.45, 0.3), (SIP0, 0.0), (CUT_LC + 0.5, 0.3), (RISE1, 0.4),
                        (R16, 0.0), (R16E + 0.2, 0.5)])
    d["smile"] = Track([
        (T0, -0.38), (P2s, -0.38), (Q08 + 2.4, -0.2), (Q08 + 2.9, -0.15), (KZ0 + 0.3, -0.12),
        (KZ0 + 0.46, 0.3), (KZ0 + 0.58, 0.95, "out"), (KZ0 + 2.6, 0.9), (KZ0 + 3.6, 0.65), (KZ0 + 4.6, 0.3),
        (KZ1, 0.35), (R12, 0.75), (R12E, 0.7), (R12E + 0.6, 0.2), (CH0 - 0.3, -0.1), (CH0 + 0.3, -0.3),
        (CH0 + 3.0, -0.15), (CH1 - 1.2, 0.35), (CH1 - 0.3, -0.05), (R13, -0.2), (R13E, -0.25), (C4, -0.2),
        (Q10 + 1.2, 0.1), (Q10 + 3.0, -0.25), (LF0, -0.25), (LF1, -0.35), (R14, -0.45), (R14E, -0.5),
        (C57, -0.2), (Q11 + 1.4, -0.35), (Q11 + 2.6, 0.05), (TH0, 0.05), (TH0 + 0.08, -0.55, "out"),
        (TH1, -0.2), (R15, 0.22), (R15E, 0.3), (C8, -0.05), (ELEVEN + 0.45, 0.05), (SIP0, -0.1),
        (SIP1 + 0.4, 0.0), (LL0, -0.05), (LL0 + 2.0, 0.08), (CUT_LC, -0.3),
        (CUT_LC + 0.6, -0.55), (STAND, -0.45), (RISE1, -0.3), (LL1, -0.25), (R16, -0.4), (T1 + 1, -0.35)])
    d["smirk"] = Track([(T0, 0.0), (Q08 + 2.4, 0.0), (Q08 + 2.9, -0.35, "out"), (KZ0 + 0.3, -0.35),
                        (KZ0 + 0.46, 0.25), (KZ0 + 0.58, 0.0, "out"), (CH0 - 0.3, 0.0), (CH0 + 0.3, -0.25),
                        (CH0 + 3.0, 0.0), (ELEVEN + 0.3, 0.0), (ELEVEN + 0.5, -0.25), (SIP0, 0.0)])
    d["tremble"] = Track([
        (T0, 0.16), (P2s + 1.0, 0.0), (KZ0 + 3.4, 0.0), (KZ0 + 4.6, 0.55), (KZ1, 0.6), (R12E, 0.4),
        (R12E + 0.8, 0.1), (CH0, 0.0), (Q10 + 3.0, 0.2), (LF0 + 1.5, 0.35), (LF1, 0.6), (R14, 0.85),
        (R14E, 0.75), (C57, 0.15), (TH1, 0.1), (R15, 0.45), (C8, 0.2), (ELEVEN, 0.1), (LL0 + 2.0, 0.4),
        (CUT_LC + 0.5, 0.85), (STAND, 0.7), (LL1, 0.6), (R16, 0.3), (T1 + 1, 0.3)])
    # ---------------- tears (trails reset off screen / on a cut to a new tear)
    d["tears"] = Track([
        (T0, 0.34), (KZ0 + 3.4, 0.3), (KZ0 + 5.0, 0.75), (R12E, 0.8), (WIPE, 0.8), (WIPE + 0.01, 0.35),
        (CH0, 0.3), (R13E, 0.3), (LF0 + 1.0, 0.4), (LF1, 0.78), (R14E, 0.85), (C57, 0.55), (R15, 0.6),
        (SIP1 + 0.5, 0.5), (LL0 + 1.5, 0.75), (CUT_LC + 0.5, 0.95), (LL1, 0.8), (T1 + 1, 0.7)])
    d["tear_l"] = Track([(KZ1 - 0.5, 0.0), (R12 + 0.2, 0.35, "out"), (R12E + 0.4, 1.0, "io"),
                         (WIPE, 1.0), (WIPE + 0.01, 0.0, "step"),
                         (CUT_LC + 0.9, 0.0), (CUT_LC + 1.7, 0.3, "out"), (STAND + 1.5, 1.0, "io")])
    d["tear_r"] = Track([(LF1 - 1.4, 0.0), (LF1 - 0.4, 0.25, "out"), (R14E + 0.2, 1.0, "io"),
                         (CUT_LC - 0.001, 1.0), (CUT_LC, 0.0, "step"),               # a new tear in the close-up
                         (CUT_LC + 0.4, 0.0), (CUT_LC + 1.1, 0.3, "out"), (STAND + 0.9, 1.0, "io")])
    d["shine"] = Track([(T0, 0.3), (KZ0 + 4.0, 0.6), (R12E, 0.5), (CH0, 0.2), (LF0 + 2.0, 0.6),
                        (C57, 0.3), (LL0 + 1.5, 0.8), (LL1, 0.7), (R16, 0.4), (T1 + 1, 0.4)])
    d["blush"] = Track([(T0, 0.16), (KZ0 + 0.5, 0.35), (R12E, 0.4), (CH0, 0.2), (R13, 0.35), (R13E + 0.5, 0.2),
                        (LF0, 0.2), (R14, 0.35), (C57, 0.25), (LL0 + 2.0, 0.4), (T1 + 1, 0.35)])
    d["sniffle"] = Track([(T0, 0.32), (KZ1, 0.45), (CH0, 0.4), (LF1, 0.55), (R15, 0.65), (LL0 + 2.0, 0.7),
                          (LL1, 0.8), (T1 + 1, 0.82)])
    # ---------------- feet / head bob (the arcade gag)
    d["tap"] = Track([(CH0 + 1.9, 0.0), (CH0 + 2.8, 0.55, "io"), (CH0 + 4.0, 0.8), (CH1, 1.0), (R13 + 0.08, 1.0),
                      (R13 + 0.22, 0.0, "out"), (R13 + 1.85, 0.0), (R13 + 1.95, 0.5, "out"), (R13 + 2.3, 0.0, "io")])
    d["bob"] = Track([(CH0 + 0.9, 0.0), (CH0 + 1.3, 0.35), (CH0 + 1.7, 0.0, "out"), (CH0 + 2.4, 0.15),
                      (CH0 + 3.6, 0.7), (CH1 - 0.4, 1.0), (CH1 - 0.3, 0.0, "out")])
    d["lofi_nod"] = Track([(LF0 + 0.6, 0.0), (LF0 + 2.0, 1.0), (LF1 - 0.3, 1.0), (LF1 + 0.4, 0.0)])
    d["laugh"] = Track([(KZ0 + 0.52, 0.0), (KZ0 + 0.62, 1.0, "out"), (KZ0 + 2.4, 0.8), (KZ0 + 3.6, 0.25),
                        (KZ0 + 4.6, 0.0), (R12 - 0.1, 0.0), (R12 + 0.1, 0.4), (R12E, 0.3), (R12E + 0.5, 0.0)])
    d["sob"] = Track([(CUT_LC + 0.2, 0.0), (CUT_LC + 0.7, 1.0), (STAND, 0.6), (RISE1, 0.2), (LL1, 0.0)])
    # ---------------- far arm (see the rig note in the module docstring)
    hug_in = ArmPose(shoulder=12.0, elbow=110.0, wrist=8.0, hand="relaxed", across=0.7)    # first frame on the wide
    d["arm_l"] = ArmSeq([
        (T0, LAP_L), (R12 - 0.12, LAP_L), (R12 + 0.16, LIFT_L, "io"),                  # elbow first, off the thigh
        (R12 + 0.44, PALM_OUT_L, "io"), (R12 + 0.9, arm_add(PALM_OUT_L, 6, -8)), (R12 + 1.2, PALM_OUT_L),
        (R12E + 0.25, LIFT_L, "io"), (R12E + 0.65, LAP_L, "io"),
        # R4 -> L, cut on action (the mug is already rising in R4): the far arm crosses the rig's layer band on
        # the cut and wraps round her on the wide
        (CUT_L - 0.001, LAP_L), (CUT_L, hug_in, "step"), (CUT_L + 0.75, HUG_L, "io"),
        (CUT_L2 - 0.25, HUG_L), (CUT_L2 + 0.55, CUP_L, "io"),
        (R14E + 0.1, CUP_L), (C57 + 0.8, CUP_CHEST_L, "io"),
        (TH0 - 0.05, CUP_CHEST_L), (TH0 + 0.12, HUDDLE_L, "out"), (TH1 - 0.3, HUDDLE_L), (TH1 + 0.45, CUP_CHEST_L),
        (SIP0 - 0.1, CUP_CHEST_L), (SIP0 + 0.42, SIP_L, "io"), (SIP1, SIP_L), (SIP1 + 0.5, CUP_CHEST_L, "io"),
        (CUT_LC + 0.15, CUP_CHEST_L), (CUT_LC + 0.85, CUP_HEART_L, "io"),
        (PLACE_T - 0.75, CUP_HEART_L), (PLACE_T - 0.35, CHEST_L, "io"),            # lets go: hand to her heart
        # exit: the hand leaves her heart in the dip for the mug (wide, fast), then points at him
        (GRAB_T - 0.42, CHEST_L), (GRAB_T - 0.12, BAL_L, "io"),
        (GRAB_T + 0.1, arm(POINT_L, shoulder=60.0, elbow=40.0)), (GRAB_T + 0.32, POINT_L, "out"),
        (BACK1 - 0.3, arm_add(POINT_L, 4, -2)), (BACK1, POINT_L),
        # waiting for the door: the arm drops while she glances back at it (so nothing reaches past the right
        # jamb when she steps behind the door plane) ...
        (BACK1 + 0.32, ArmPose(shoulder=0.0, elbow=6.0, wrist=0.0, hand="relaxed"), "io"),   # (hangs: the walk
        (OUT0 + 0.02, ArmPose(shoulder=1.0, elbow=8.0, wrist=0.0, hand="relaxed")),         # swing adds ~8 deg)
        # ... and comes back up pointing as she backs out: through the doorway, clipped by the jamb
        (OUT0 + 0.32, POINT_L, "io"), (OUT1 - 0.12, POINT_L),
        (OUT1 - 0.04, arm_add(POINT_L, 10, -4), "out"),                                  # ...and YOU
        (OUT1 + 0.22, ArmPose(shoulder=10.0, elbow=60.0, wrist=0.0, hand="relaxed"), "in"),         # whips away
    ])
    return d


_RT = _rae_tracks()


def _rae_body(t) -> Pose:
    """Rae without face / near arm (the mug solver poses the near arm on this body)."""
    d = _RT
    ph = walk_phase(t)
    return Pose(x=rae_x(t), y=FLOOR, facing=1.0, turn=d["turn"](t), sit=RISE_SIT(t) if ph is None else 0.0,
                seat_y=SEAT_Y, walk=ph, lean=d["lean"](t), bounce=d["bounce"](t),
                shoulders_up=d["shoulders"](t), breath=breathe(t, 0.22, 2), arm_l=d["arm_l"](t))


# ---------------------------------------------------------------- near arm with the bench hand-offs
MUG_EVENTS = (("place", PLACE1_T), ("grab", PICK_T), ("place", PLACE_T), ("grab", GRAB_T))


@lru_cache(maxsize=None)
def _solved(kind, t_ev):
    base = arm(HOLD, wrist=-6.0) if (kind == "grab" and t_ev == GRAB_T) else HOLD
    return s3.solve_mug_arm(t_ev, MUG_SIDE, _rae_body, base)


def _place_keys(t):
    """Keys that set the mug down at time t (on the solved pose): hover, land, release, lift away."""
    S_ = _solved("place", t)
    return [(t - 0.16, arm_add(S_, 7.0, -6.0), "io"), (t, S_, "io"), (t + 0.12, arm(S_, hand="open")),
            (t + 0.4, arm_add(arm(S_, hand="open"), 8.0, -10.0), "io")]


def _grab_keys(t):
    S_ = _solved("grab", t)
    return [(t - 0.12, arm_add(arm(S_, hand="open"), 7.0, -7.0), "io"), (t, S_, "io"), (t + 0.12, S_)]


@lru_cache(maxsize=1)
def _arm_r_seq():
    keys = [
        (T0, CLUTCH), (C2 + 1.0, CLUTCH), (C2 + 1.8, HOLD), (KZ0 + 0.3, HOLD), (KZ0 + 0.46, arm_add(HOLD, 3, 4)),
        (KZ0 + 0.62, arm_add(HOLD, 10, 12), "out"), (KZ0 + 0.98, HOLD),
        (R12 - 0.15, HOLD), (R12 + 0.2, MUG_RAISE, "out"), (R12 + 0.9, arm_add(MUG_RAISE, 6, -6)),
        (R12 + 1.25, MUG_RAISE), (R12E + 0.35, HOLD),
        # P3: sets it down behind her to brace for the next one
        (PLACE1_T - 0.62, HOLD)] + _place_keys(PLACE1_T) + [
        (PLACE1_T + 0.95, KNEE_R, "io"),
        (R13 - 0.12, arm_add(KNEE_R, 14, -10)), (R13 + 0.1, GRIP_R, "out"), (R13 + 1.8, GRIP_R),
        (R13 + 1.95, arm_add(GRIP_R, 3, 4), "out"), (R13 + 2.3, GRIP_R), (C4 + 0.6, GRIP_R), (C4 + 1.4, KNEE_R, "io"),
        # R4: takes it back for comfort
        (PICK_T - 0.62, KNEE_R)] + _grab_keys(PICK_T) + [
        (PICK_T + 0.6, HOLD, "io"),
        # lo-fi: to her chest (the wide), under her chin (the close-up)
        (CUT_L - 0.36, HOLD), (CUT_L + 0.85, MUG_CHEST_R, "io"),
        (CUT_L2 - 0.25, MUG_CHEST_R), (CUT_L2 + 0.55, MUG_CHIN_R, "io"),
        (R14E + 0.1, MUG_CHIN_R), (C57 + 0.8, MUG_CHEST_R, "io"),
        (TH0 - 0.05, MUG_CHEST_R), (TH0 + 0.12, MUG_HUDDLE_R, "out"), (TH1 - 0.3, MUG_HUDDLE_R),
        (TH1 + 0.45, MUG_CHEST_R),
        # "eleven seconds": a fortifying sip
        (SIP0 - 0.1, MUG_CHEST_R), (SIP0 + 0.42, SIP_R, "io"), (SIP1, SIP_R), (SIP1 + 0.5, MUG_CHEST_R, "io"),
        # lullaby: pressed to her heart ... set down ... both hands on her heart as she rises
        (CUT_LC + 0.15, MUG_CHEST_R), (CUT_LC + 0.85, MUG_HEART_R, "io"),
        (PLACE_T - 0.75, MUG_HEART_R), (PLACE_T - 0.4, arm(HOLD, shoulder=16.0, elbow=96.0, across=0.3), "io")
    ] + _place_keys(PLACE_T) + [
        (RISE0 + 0.4, arm(CHEST_R, shoulder=24.0), "io"), (RISE0 + 0.9, CHEST_R, "io"),
        (R16 - 0.2, CHEST_R), (R16 + 0.1, NOPE_R, "io"),                                    # "Nope."
        (R16 + 0.42, arm_add(NOPE_R, 6, -10)), (R16 + 0.62, arm_add(NOPE_R, -4, 6)), (R16 + 0.82, NOPE_R),
        (GRAB_T - 0.45, NOPE_R)] + _grab_keys(GRAB_T) + [
        (BACK0 + 0.3, CARRY_R, "io"), (T1 + 1, CARRY_R)]
    return ArmSeq(keys)


def _rae_arm_r(t):
    return _arm_r_seq()(t)


def rae_mug(t):
    """'r' (near hand) / None (on the bench)."""
    held = "r"
    for kind, te in MUG_EVENTS:
        if t >= te:
            held = None if kind == "place" else "r"
    return held


@lru_cache(maxsize=None)
def _mug_in_hand(t):
    return R.mug_pose(_raw_pose(t, mug="r"))


def bench_mug(t):
    """The mug standing on the bench between a place and the next grab: it settles flat after the release
    and tips a hair toward her fingers just before the grab, so neither hand-off pops."""
    for (k0, ta), (k1, tb) in zip(MUG_EVENTS[0::2], MUG_EVENTS[1::2]):
        if ta <= t < tb:
            mp, mg = _mug_in_hand(ta), _mug_in_hand(tb)
            ang = mp[3] * (1.0 - smoothstep((t - ta) / 0.22))
            k = smoothstep((t - (tb - 0.12)) / 0.12)
            return (lerp(mp[0], mg[0], k), lerp(mp[1], mg[1], k), mp[2], lerp(ang, mg[3], k), mp[4])
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


def _raw_pose(t: float, mug="auto") -> Pose:
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
    # sniffs: a quick lift of the head + shoulders
    for s0 in (R15 - 0.35, ELEVEN - 0.4):
        x = (t - s0) / 0.3
        if 0 <= x < 1:
            hh = math.sin(math.pi * x)
            nod -= 0.06 * hh
            shoulders += 0.08 * hh
    # "Nope nope nope": head shakes
    if R16 + 0.3 <= t < R16 + 1.15:
        u = (t - R16 - 0.3) / 0.85
        hturn += 0.16 * math.sin(2 * math.pi * 3.5 * (t - R16 - 0.3)) * math.sin(math.pi * u)
    return body.copy(
        head_tilt=tilt, head_nod=nod, head_turn=hturn, bounce=bounce, shoulders_up=shoulders, lean=lean,
        lid_l=lid, lid_r=lid * (0.99 + 0.01 * noise1(t * 0.7, 3)), look_x=lx, look_y=ly, pupil=d["pupil"](t),
        squint=squint, eye_wide=d["wide"](t), brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t),
        brow_furrow=d["furrow"](t), mouth_open=clamp(mopen + 0.82 * mo), mouth_round=clamp(d["round"](t) + mr),
        smile=d["smile"](t), smirk=d["smirk"](t), mouth_tremble=d["tremble"](t), tears=d["tears"](t),
        tear_l=d["tear_l"](t), tear_r=d["tear_r"](t), eye_shine=d["shine"](t), blush=d["blush"](t),
        sniffle=d["sniffle"](t), foot_tap=d["tap"](t), arm_r=_rae_arm_r(t),
        mug=rae_mug(t) if mug == "auto" else mug, **char_lighting(t),
    )


def rae_pose(t: float) -> Pose:
    return _raw_pose(t)


# =========================================================================== Quill
QA = Q.ARMS
PRESENT = QA["present"]
QREST = QA["rest"]
PALM_CLOSE = arm(PRESENT, hand="relaxed", wrist=8.0, elbow=PRESENT.elbow + 6)


def _raise(t_sel, lead=0.55):
    """Arm keys: palm comes up (present) to arrive just before a select at t_sel, then the flick
    (smooth eased arcs: Quill never snaps)."""
    return [(t_sel - lead, QREST), (t_sel - lead + 0.12, arm_add(QREST, -2, 4), "io"),
            (t_sel - 0.05, PRESENT, "io"), (t_sel + 0.06, arm_add(PRESENT, 2, 6, -16), "out"),
            (t_sel + 0.28, PRESENT, "io")]


def _lower(t0, dur=0.7):
    return [(t0, PRESENT), (t0 + dur, QREST, "io")]


def _quill_tracks():
    d = {}
    # palm up for each announcement, down while Rae listens (the fan hangs in the air on its own)
    keys = [(T0, PRESENT), (C2 - 0.02, PRESENT), (C2 + 0.06, arm_add(PRESENT, 2, 6, -16), "out"),
            (C2 + 0.28, PRESENT, "io")]
    keys += _lower(Q08E - 0.2, 0.6)
    keys += _raise(C3, 0.6) + _lower(Q09E - 0.25, 0.55)
    keys += _raise(C4, 0.62) + _lower(PALM4_DOWN, 0.55)            # (starts on the C shot: cut on his action)
    keys += _raise(C57, 0.62)
    # "I will spare you": the hand closes right as the wail starts - the cards fold on its onsets
    keys += [(TH0 - 0.1, PRESENT), (TH0 + 0.25, PALM_CLOSE, "io"), (TH1 + 0.05, PALM_CLOSE)]
    keys += [(TH1 + 0.1, PALM_CLOSE), (TH1 + 0.7, QREST, "io")]
    keys += _raise(C8, 0.55)
    d["arm_r"] = ArmSeq(keys)
    # the other hand goes behind his back for the presentation (off screen, on Rae's close-up) - a maitre d'
    # with the menu; it comes back to his side as she leaves (S5 opens with it at rest)
    d["arm_l"] = ArmSeq([(T0, QREST), (CUT_P2 - 0.08, QA["behind_back"], "io"), (OUT0 + 0.1, QA["behind_back"]),
                         (OUT0 + 0.9, QREST, "io")])
    d["tilt"] = Track([
        (T0, 7.0), (C2, 3.0), (Q08 + 1.0, 5.0), (Q08 + 2.4, 8.0), (KZ0 + 1.0, 10.0), (KZ1, 6.0),
        (R12 + 1.0, 9.0), (C3, 3.0), (Q09E, 6.0), (CH0 + 2.0, 8.0), (CH1, 12.0), (C4, 4.0),
        (Q10E - 1.0, 7.0), (LF0 + 2.0, 5.0), (C57, 3.0), (Q11 + 2.4, 6.0), (TH0 + 0.4, 9.0), (TH1, 6.0),
        (C8, 3.0), (Q12 + 1.6, 6.0), (Q12 + 2.6, 9.0), (LL0 + 2.0, 6.0), (STAND, 4.0), (LL1, 8.0),
        (R16 + 0.4, 3.0), (BACKS, 0.0), (T1 + 1, -2.0)])
    d["nod"] = Track([
        (T0, 0.0), (C2, 0.06), (C2 + 0.4, 0.0), (Q08 + 0.7, -0.06), (Q08 + 1.0, 0.0),
        (C3, 0.06), (C3 + 0.4, 0.0), (CUT_QI - 0.6, 0.02), (CUT_QI - 0.25, 0.18), (CUT_QI + 0.7, 0.18),
        (CUT_QI + 1.0, 0.02), (C4, 0.06), (C4 + 0.4, 0.0), (C57, 0.06), (C57 + 0.4, 0.0),
        (Q11 + 2.5, 0.0), (Q11 + 2.7, -0.08), (Q11 + 3.0, 0.0), (C8, 0.06), (C8 + 0.4, 0.0),
        (Q12 + 1.0, -0.05), (Q12 + 1.3, 0.0), (LL0 + 0.3, 0.2), (LL0 + 2.5, 0.12), (STAND + 0.4, 0.0),
        (RISE1, -0.1), (LL1, -0.06), (T1 + 1, -0.05)])
    d["hturn"] = Track([(T0, 0.0), (BACK0, 0.0), (OUT0, -0.12), (T1 + 1, -0.16)])
    d["brow"] = Track([
        (T0, 0.15), (C2, 0.1), (Q08 + 2.0, 0.18), (KZ0 + 1.0, 0.25), (KZ1, 0.2), (R12 + 1.2, 0.35),
        (C3, 0.12), (CH0 + 2.0, 0.15), (CUT_QI - 0.2, 0.32), (C4, 0.12), (Q10 + 3.0, 0.2),
        (C57, 0.1), (TH0 + 0.3, 0.3), (TH1, 0.15), (C8, 0.08), (Q12 + 2.2, 0.16), (LL0 + 1.0, 0.18),
        (STAND + 1.0, 0.3), (R16 + 0.3, 0.4), (BACKS, 0.3), (T1 + 1, 0.3)])
    d["worry"] = Track([(T0, 0.0), (CUT_LC, 0.0), (STAND + 1.0, 0.18), (LL1, 0.12), (R16 + 0.4, 0.2),
                        (T1 + 1, 0.15)])
    d["smile"] = Track([(T0, 0.06), (C2, 0.02), (KZ0 + 1.5, 0.04), (Q10 + 2.5, 0.0),
                        (Q10 + 3.2, 0.07), (Q10E + 0.6, 0.02), (Q12 + 1.2, 0.02), (Q12 + 1.8, 0.06),
                        (LL0 + 1.0, 0.08), (STAND, 0.05), (R16, 0.0)])
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
        (C2 - 0.12, CARDV), (Q08 + 0.9, RAE_S), (KZ0 + 2.0, (-0.38, 0.28)), (KZ1, RAE_S),
        (C3 - 0.12, CARDV), (Q09 + 0.95, RAE_S),
        (CUT_QI - 0.45, (-0.32, 0.9), 0.14), (CUT_QI + 0.85, (-0.4, 0.3), 0.12),       # her foot ... back up
        (C4 - 0.12, CARDV), (Q10 + 0.7, RAE_S), (Q10 + 2.2, CARDV), (Q10 + 2.6, RAE_S),
        (C57 - 0.12, (-0.55, -0.02)), (Q11 + 2.4, RAE_S), (TH0 + 0.1, (-0.55, -0.02)),
        (TH1 + 0.2, RAE_S),
        (C8 - 0.12, CARDV), (Q12 + 1.0, RAE_S), (Q12 + 1.6, CARDV), (Q12 + 2.1, RAE_S),
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
PLAY = {2: (Q08E - 0.2, C3), 3: (Q09E - 0.25, C4), 4: (PALM4_DOWN, C57)}
FOCUS8 = (388.0, 474.0)                 # cards 4 and 8 (presented in Quill's medium shots)


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
    hl = smoothstep((t - C57) / 0.4)
    for n in GONE:
        states[n] = hl
    st["states"] = states
    wob = smoothstep((t - (Q11 + 1.4)) / 0.6) * 0.55 + 0.45 * smoothstep((t - (TH0 - 0.1)) / 0.2)
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
    fpos = FOCUS8 if t >= C4 else s3.FOCUS_POS
    draw_fan(c, t, 1.0, alpha=st["alpha"], focus=st["focus"], states=st["states"], wobble=st["wobble"],
             fold=st["fold"], pops=st["pops"], hidden=st["hidden"], alphas=st["alphas"], focus_pos=fpos)
    for num, ts in SEL:
        if ts <= t < ts + 0.6:
            select_flash(c, t, ts + 0.05, fpos[0], fpos[1], 0.8)
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


def draw_world_fx(c, t, shot=""):
    """Stage-space effects drawn over the set and the characters."""
    if CH0 - 0.1 <= t <= CH1 + 0.3:
        amt = smoothstep((t - CH0) / 0.6) * (1.0 - smoothstep((t - CH1) / 0.3))
        fx.draw_pixel_sparkles(c, t, area=(-20, 420, 175, 1000), amount=amt, seed=31, px=7.0, count=6)
        fx.draw_pixel_sparkles(c, t, area=(335, 560, 520, 1000), amount=amt, seed=37, px=7.0, count=5)
        fx.draw_pixel_sparkles(c, t, area=(60, 330, 470, 520), amount=amt, seed=41, px=7.0, count=5)
        if shot != "QI":            # (the foot insert keeps the foot clean: stage-size pixels would be huge there)
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
QFACE = s3.QFACE


def _follow_cam(t, z, sx, sy, k=0.6, step=0.1):
    """Camera at zoom z holding Rae's (smoothed) face near screen (sx, sy), following k of her head motion."""
    hx, hy = smoothed(_rae_head, t, 5, step)
    return _face_cam(lerp(SEAT_FACE[0], hx, k), lerp(SEAT_FACE[1], hy, k), z, sx, sy)


def camera(name, t, a, b):
    u = clamp((t - a) / max(1e-3, b - a))
    if name in ("P2", "P3"):            # presentation three-shot: Rae left third, card centre, Quill right
        dz = 1.0
        return drift(Camera(352.0, 690.0, 1.24 * dz), Camera(351.0, 684.0, 1.27 * dz), t, a, b)
    if name == "K":                     # Rae medium: the snort ... then a slow push into her close-up
        p0, p1 = KZ0 + 2.2, KZ0 + 5.4
        v = smoothstep(clamp((t - p0) / (p1 - p0)))
        z = 2.1 * (3.0 / 2.1) ** v
        return _follow_cam(t, z, lerp(330.0, 352.0, v), lerp(500.0, 540.0, v), lerp(0.45, 0.6, v))
    if name == "R12":                   # wider Rae medium for the outburst (both hands up)
        return _follow_cam(t, 2.0 * (1.0 + 0.03 * ease_in_out(u)), 300.0, 462.0, 0.5)
    if name == "C":                     # arcade medium-wide two-shot: her feet in frame, Quill watching, card 3 up top
        return drift(Camera(350.0, 772.0, 1.3), Camera(351.0, 768.0, 1.34), t, CUT_C, CUT_P4)
    if name == "P4":                    # Quill medium + card 4 (deadpan)
        return drift(_face_cam(QFACE[0], QFACE[1], 1.85, 412.0, 420.0),
                     _face_cam(QFACE[0], QFACE[1], 1.92, 414.0, 424.0), t, a, b)
    if name == "R4":                    # Rae medium: her mug on the bench behind her is in frame, his palm is down
        return _follow_cam(t, 1.9 * (1.0 + 0.03 * ease_in_out(u)), 330.0, 470.0, 0.4)
    if name == "QI":                    # insert: the traitorous foot (shoe low in frame, shin above)
        return drift(Camera(352.0, 1070.0, 3.3), Camera(353.0, 1071.0, 3.4), t, a, b)
    if name == "L":                     # "lo-fi beats to quietly fall apart to": the album-cover wide
        return drift(Camera(352.0, 640.0, 1.04), Camera(338.0, 650.0, 1.1), t, a, b)
    if name in ("L2", "R15", "LC"):
        z0 = {"L2": 3.1, "R15": 3.12, "LC": 3.2}[name]
        return _follow_cam(t, z0 * (1.0 + 0.06 * ease_in_out(u)), 356.0, 540.0)
    if name == "R8":                    # medium close: the sip needs the mug and both hands
        return _follow_cam(t, 2.6 * (1.0 + 0.04 * ease_in_out(u)), 372.0, 510.0, 0.45)  # (his palm just out right)
    if name == "P57":
        return drift(Camera(372.0, 648.0, 1.26), Camera(371.0, 640.0, 1.3), t, a, b)
    if name == "P8":                    # Quill medium with card 8 beside him (Rae just out of frame left)
        return drift(_face_cam(QFACE[0], QFACE[1], 1.85, 412.0, 420.0),
                     _face_cam(QFACE[0], QFACE[1], 1.95, 414.0, 424.0), t, a, b)
    if name == "LW":
        return drift(Camera(372.0, 700.0, 1.04), Camera(374.0, 690.0, 1.1), t, a, b)
    if name == "LS":
        return drift(Camera(320.0, 760.0, 1.22), Camera(318.0, 730.0, 1.26), t, a, b)
    if name == "LQ":                    # Quill + music box; Rae (standing) just out left
        return drift(Camera(516.0, 560.0, 2.1), Camera(516.0, 556.0, 2.18), t, a, b)
    if name == "N":                     # medium two-shot: backing away from his offer
        return drift(Camera(392.0, 652.0, 1.3), Camera(386.0, 656.0, 1.34), t, a, b)
    if name == "X":                     # wide: the door (x -140..60) and Quill (x 545) both readable
        return drift(Camera(196.0, 700.0, 0.82), Camera(200.0, 704.0, 0.84), t, a, b)
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
            xc = env.DOOR_X1 + max(0.0, 2.2 * (rp.x + 60.0))      # (rp.x < -60 here: the jamb itself)
            c.clipRect(skia.Rect(xc, -2000, 4000, 4000), skia.ClipOp.kDifference, True)
        R.draw(c, rp, t + TAP_SHIFT)
        c.restore()
    else:
        R.draw(c, rp, t + TAP_SHIFT)
    # (until she backs through it she stands in FRONT of the door: no lintel over her hair)
    env.draw_lounge_front(c, t, light=light, door=dr, warm=warm, lintel=not (BACK1 - 0.6 < t < IN_DOOR))
    draw_world_fx(c, t, name)
    if not cards_behind:
        draw_cards(c, t)
    c.restore()
