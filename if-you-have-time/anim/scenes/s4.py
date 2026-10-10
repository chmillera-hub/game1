"""S4 - "The others, played quickly" (BIBLE section 4, S4 + sections 10 / 11, REVISIONS 3 and 4).

Quill breezes through the menu - each cardN beat his palm gives a small flick, the card slides out to be
read and the rest dim - while Rae, still seated and mostly silent, just absorbs them. Her reactions are
small and natural (no improv), REVISION 3: kazoo - she lifts her mug a little toward him (a tiny toast) with a
small smile and nods gently in time (half-time, on the kazoo's strong beats); arcade - her foot taps and her
head bobs clearly on every beat; lo-fi - rain on the window; her eyes come up to Quill (head following a
touch) in quiet recognition of the comfort, one small nod. REVISION 4: card 5 is a WHALE SONG ("And five. A
whale song. With drums.") - the card folds down into his palm and a small holographic whale (fx.draw_whale_holo)
swims up out of it and circles above his palm for the 5 s cue; Rae: eyebrows up, a surprised, delighted little
smile, a glance up to Quill, a small nod (it is majestic and a bit absurd); the whale dives back into his palm
and the card re-forms. The light stays normal throughout (no lo-fi dusk, no lullaby warmth); her far tear
streak dries away through the kazoo and the arcade piece (s3.far_tear). Then: "You can just send them to my
device. I gotta get going." - she stands, a little abruptly, mug in hand, walks briskly to the door, which
opens for her, and is gone; the door shuts.

render(canvas, t) is a pure function of absolute time t; times derive from named beats / lines / music
cues / SFX. The poses run continuously through the cuts (each shot only picks a camera); S3's last pose
eases into this scene's performance (anim.scenes.s3.inherit). Shared helpers live in anim.scenes.s3.

Shot list (orientation only):
  P2   card2 -> kazoo+0.1          PRESENTATION TWO-SHOT (S3's shot continues): "Number two..." card 2 slides out
  K    kazoo                       Rae MEDIUM: the little mug toast toward him, a small smile, gentle nods in time
  Q3   card3-0.35 -> chip          Quill MEDIUM + card 3: "Three. For an arcade cabinet."
  C    chip                        Rae MEDIUM-WIDE (feet in frame): her foot taps and her head bobs on the beat
  Q4   card4-0.35 -> lo-fi         Quill MEDIUM + card 4 (deadpan): "Four. Lo-fi beats... to quietly fall apart to."
  L    lo-fi                       WIDE "album cover": rain on the window (normal light); she looks up at it
  LR   lo-fi +2.2                  Rae MEDIUM CLOSE: her eyes come up to Quill - quiet recognition, one small nod
  Q5   card5-0.35 -> whale-0.1     Quill MEDIUM + card 5: "And five. A whale song. With drums."
  W    whale_start-0.1             WIDE TWO-SHOT: card 5 folds into his palm, the holo-whale swims up out of it;
                                   Rae's eyebrows go up, she sits back a touch
  WR   whale +1.35                 MEDIUM TWO-SHOT favouring Rae (frame left; his palm, the whale and his face frame
                                   right): the delighted little smile, a glance up to Quill, a small nod, eyes back
                                   to the whale
  WQ   whale +3.95                 MEDIUM Quill + whale: the last call; it dives back into his palm, card 5
                                   re-forms; he looks to her for the verdict
  R11  whale end+0.15 -> up+0.45   Rae MEDIUM: "You can just send them to my device. I gotta get going."; she
                                   stands up, a little abruptly (cut on the turn)
  X    -> S5                       WIDE (door + Quill): brisk walk to the door, it opens for her, she is through,
                                   it shuts; Quill's palm (and the cards) still up
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
from anim.core import (Camera, Track, auto_blink, beat, breathe, clamp, ease_in, ease_in_out, ease_out, glow, lerp,
                       line_end, line_start, mouth, music_cue, music_env, music_onsets, noise1, scene_span,
                       smoothstep)
from anim.rig import ArmPose, Pose
from anim.scenes import s3
from anim.scenes.s3 import (FAN, FLOOR, SEAT_X, SEAT_Y, ArmSeq, _face_cam, arm, arm_add, blink_amt, bump,
                            char_lighting, drift, draw_fan, gaze, inherit, select_flash, sfx_time, smoothed)
from config import FPS, MUSIC_ENV, H, W

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s4")
S, E = line_start, line_end

C2, C3, C4, C5 = beat("card2"), beat("card3"), beat("card4"), beat("card5")
KZ0, KZ1 = music_cue("alt_kazoo")["start"], music_cue("alt_kazoo")["end"]
CH0, CH1 = music_cue("alt_chip")["start"], music_cue("alt_chip")["end"]
LF0, LF1 = music_cue("alt_lofi")["start"], music_cue("alt_lofi")["end"]
WH0, WH1 = beat("whale_start"), music_cue("alt_whale")["end"]      # the whale song (alt_whale, 5 s)
UP = beat("rae_up")
WALK = beat("rae_walk")
EXIT = beat("rae_exit_door")
DOOR_O = sfx_time("door_open", WALK - 0.5)     # the panel starts to slide with the sfx
DOOR_C = sfx_time("door_close", EXIT - 0.5)
SHUT = beat("door_shut")                       # (door_close.wav thunk)

Q08, Q08E = S("q08"), E("q08")
Q09, Q09E = S("q09"), E("q09")
Q10, Q10E = S("q10"), E("q10")
Q11, Q11E = S("q11"), E("q11")
R11, R11E = S("r11"), E("r11")
# word landmarks inside lines (read off the lip-sync envelopes)
KAZOO_W = Q08 + 1.9                     # "...Solo kazoo."
FALL_APART = Q10 + 1.9                  # "...to quietly fall apart to."
WHALE_W = Q11 + 0.62                    # "...A whale song."
DRUMS_W = Q11 + 1.58                    # "...With drums."
SEND_W = R11 + 0.95                     # "...send them to my device."
DEVICE_E = R11 + 1.7                    # (end of the first sentence; a breath)
GOING = R11 + 1.96                      # "I gotta get going."


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


KAZOO_BEATS = cue_beats("alt_kazoo") or [KZ0 + 0.535 * k for k in range(9)]
CHIP_BEATS = cue_beats("alt_chip") or [CH0 + 0.4 * k for k in range(11)]
LOFI_BEATS = cue_beats("alt_lofi") or [LF0 + 0.75 * k for k in range(7)]

# ---------------------------------------------------------------- cuts
CUT_K = s3.CUT_K                        # (= kazoo start + 0.1) out of S3's presentation shot, onto her face
CUT_Q3 = C3 - 0.35
CUT_C = CH0 + 0.05                      # on the chip downbeat
CUT_Q4 = C4 - 0.35
CUT_L = LF0 + 0.05
CUT_LR = LF0 + 2.2
CUT_Q5 = C5 - 0.35
CUT_W = WH0 - 0.1                       # card 5 folds into his palm on the cut
CUT_WR = WH0 + 1.35                     # (her brows are up from the wide; the delight blooms here)
CUT_WQ = WH0 + 3.95
CUT_R11 = WH1 + 0.15
CUT_X = UP + 0.45                       # cut on the turn: she is up, the walk starts

SHOTS = [("P2", T0), ("K", CUT_K), ("Q3", CUT_Q3), ("C", CUT_C), ("Q4", CUT_Q4), ("L", CUT_L), ("LR", CUT_LR),
         ("Q5", CUT_Q5), ("W", CUT_W), ("WR", CUT_WR), ("WQ", CUT_WQ), ("R11", CUT_R11), ("X", CUT_X)]


def shot_at(t):
    cur = SHOTS[0]
    nxt = T1 + 1.0
    for i, (name, a) in enumerate(SHOTS):
        if t >= a:
            cur = (name, a)
            nxt = SHOTS[i + 1][1] if i + 1 < len(SHOTS) else T1 + 1.0
    return cur[0], cur[1], nxt


# =========================================================================== lighting
# REVISION 4: normal light throughout (no lo-fi dusk, no lullaby warmth). The lo-fi gag is only the rain on the
# window glass, coming in on the wide and ebbing away during "And five".
RAIN = Track([(LF0 - 0.25, 0.0), (LF0 + 1.6, 1.0, "io"), (LF1 + 0.2, 1.0), (LF1 + 2.0, 0.0, "io")])
NORMAL_LIGHT = char_lighting(1.0)


def room(t):
    """(light, warm, rain) of the lounge."""
    return 1.0, 0.0, RAIN(t)


def lighting(t):
    return dict(NORMAL_LIGHT)


# =========================================================================== Rae: arms
A = R.ARMS
HOLD = A["hold_mug"]
LAP_L = s3.LAP_L
TOAST_R = ArmPose.blend(HOLD, A["mug_raise"], 0.5)     # kazoo: the mug lifted a little toward him (tiny toast)
TOAST_TINK = arm_add(TOAST_R, 4.0, -2.0)                # ... the little "cheers" accent at the top
CARRY_R = arm(HOLD, shoulder=18.0, elbow=92.0, across=0.26)
REST_L = ArmPose(shoulder=4.0, elbow=10.0, wrist=0.0, hand="relaxed")

# ---------------------------------------------------------------- standing up + the walk out
X_UP = SEAT_X + 32.0                    # pelvis once upright (feet under her)
RISE1 = UP + 0.42                       # (a little abrupt)
CYCLE = R.WALK_ADVANCE
PH0 = 0.25                              # walk phase with both feet under her (no stance pop on the cut)
WALK_RATE = 1.35                        # cycles per second (brisk)
WALK_ACC = 0.35
IN_DOOR = DOOR_O + 1.0                  # door fully open and her trailing edge left of the right jamb:
#                                         from here she is behind the door plane (the closing panel covers her)


def walk_phase(t):
    """None (not walking) / phase in cycles: brisk walk from rae_walk, eased in over WALK_ACC."""
    if t < CUT_X:
        return None
    if t < WALK:
        return PH0
    u = t - WALK
    if u < WALK_ACC:
        s_ = u / WALK_ACC
        return PH0 + WALK_RATE * WALK_ACC * (s_ ** 3 - 0.5 * s_ ** 4)
    return PH0 + WALK_RATE * (0.5 * WALK_ACC + (u - WALK_ACC))


def rae_x(t):
    ph = walk_phase(t)
    if ph is None:
        return lerp(SEAT_X, X_UP, ease_in_out(clamp((t - UP) / (RISE1 - UP))))
    return X_UP - (ph - PH0) * CYCLE


def rae_sit(t):
    if t < UP:
        return 1.0
    u = clamp((t - UP) / (RISE1 - UP))
    return 1.0 - smoothstep(u)


def rae_facing(t):
    return 1.0 if t < CUT_X else -1.0


# =========================================================================== Rae: body / face tracks
QU = (0.58, -0.42)                      # Quill's face, seated
CARD = (0.44, -0.74)                    # the card out in front of him, seated
MID = (0.18, -0.06)
DOOR = (-0.62, 0.02)                    # standing, facing the door (screen-left)
WIN = (-0.32, -0.62)                    # up at the rain on the window behind her
WHALEG = (0.5, -0.46)                   # the holo-whale above his palm (up and to the right of her)
DOWN = (0.12, 0.36)                     # eyes lowered, absorbing
QU_UP = (0.5, -0.62)                    # up at his face (standing over her): the head lifts with it
# kazoo: the toast (the mug comes up toward him as the music starts, held while she nods along, then down)
TOAST0 = KZ0 + 0.5
TOAST1 = TOAST0 + 0.5
TOAST2 = KZ0 + 2.95
TOAST3 = TOAST2 + 0.75
KZ_NODS = [b for b in KAZOO_BEATS[2::2] if b < KZ0 + 3.6]  # gentle half-time nods (the strong beats)
# lo-fi: quiet recognition - her eyes come up to Quill
LOOK0 = LF0 + 2.7
ACK_NOD = LOOK0 + 0.95
LOOK1 = LF0 + 4.75                      # ... and drift back down as the piece fades
# whale song: eyebrows up (surprise), a delighted little smile, a glance up to Quill, a small nod, back to the whale
SURPRISE = WH0 + 0.3                    # the whale's first call over the drums: brows up, eyes a touch wider
DELIGHT = WH0 + 0.85                    # ... the delighted little smile blooms
GLANCE = WH0 + 2.35                     # up to Quill
SNOD = GLANCE + 0.4                     # the small nod (majestic. and a bit absurd.)
BACK = WH0 + 3.45                       # eyes back to the whale


def _rae_tracks():
    d = {}
    # ---------------- body
    d["lean"] = Track([
        (T0, 2.0), (TOAST0, 2.2), (TOAST1, 3.6), (TOAST2, 3.4), (TOAST3, 2.6), (KZ1, 3.0), (CH0, 2.0), (CH1, 2.5),
        (LF0, 2.0), (LF0 + 1.2, -1.5), (CUT_LR + 0.3, 0.0), (LOOK0 + 0.6, 1.5),
        (LF1, 2.0), (C5, 2.0), (WH0 + 0.1, 2.0), (SURPRISE + 0.2, 0.4, "out"), (DELIGHT + 0.6, 2.4),
        (GLANCE + 0.3, 3.2), (WH1, 3.0), (R11, 3.0),
        (DEVICE_E, 3.0), (R11E, 4.2), (UP, 4.0), (UP + 0.16, 15.0, "out"), (RISE1, 4.0, "io"), (CUT_X, 3.0),
        (WALK + 0.4, 4.0), (T1 + 1, 4.0)])
    d["bounce"] = Track([(T0, 0.0), (RISE1 - 0.02, 0.0), (RISE1 + 0.12, 3.0, "out"), (CUT_X, 0.0), (T1 + 1, 0.0)])
    d["shoulders"] = Track([
        (T0, 0.1), (KZ0 + 0.5, 0.08), (TOAST1, 0.12), (TOAST3, 0.08), (CH0, 0.08), (LF0 + 1.0, 0.16),
        (LOOK0 + 0.5, 0.12), (LF1, 0.16), (C5, 0.12), (WH0 + 0.1, 0.12), (SURPRISE + 0.2, 0.2, "out"),
        (DELIGHT + 0.6, 0.1), (WH1, 0.12), (R11, 0.22),
        (DEVICE_E, 0.24), (R11E, 0.32), (UP + 0.1, 0.34), (CUT_X, 0.2), (T1 + 1, 0.22)])
    d["turn"] = Track([(T0, 0.3), (UP, 0.3), (RISE1, 0.16, "io"), (CUT_X - 0.001, 0.14),
                       (CUT_X, 0.2, "step"), (WALK + 0.45, 0.4, "io"), (T1 + 1, 0.4)])
    # ---------------- head
    d["nod"] = Track([
        (T0, -0.1), (C2 + 0.4, -0.12), (KAZOO_W, -0.08), (TOAST0, -0.04), (TOAST1, 0.04), (TOAST2, 0.02),
        (KZ1, -0.02), (CH0, 0.0), (C4, -0.06), (FALL_APART + 0.3, 0.02), (LF0 + 0.4, 0.02), (LF0 + 1.3, -0.16),
        (CUT_LR, -0.14), (LOOK0, -0.16), (LOOK0 + 0.75, 0.17), (LOOK1, 0.12), (LOOK1 + 0.6, -0.06),
        (C5, -0.08), (WHALE_W + 0.2, -0.04), (WH0 + 0.1, -0.02), (SURPRISE + 0.25, 0.1, "out"),      # chin up
        (DELIGHT + 0.6, 0.06), (GLANCE - 0.05, 0.06), (GLANCE + 0.3, 0.2), (BACK, 0.07), (BACK + 0.4, 0.04),
        (WH1, 0.04), (R11, 0.04), (DEVICE_E, 0.06),
        (GOING + 0.3, 0.12), (R11E, 0.12), (UP, 0.08), (RISE1, 0.14), (CUT_X, 0.18), (T1 + 1, 0.2)])
    d["tilt"] = Track([
        (T0, 0.0), (C2 + 0.5, 1.5), (TOAST0, 2.0), (TOAST1 + 0.3, 4.0), (KZ1, 4.0), (C3, 1.0), (CH0 + 1.0, 2.0),
        (C4, 0.0), (LF0 + 1.3, -4.0), (CUT_LR, -2.0), (LOOK0, -1.0), (LOOK0 + 0.9, 3.5), (LF1, 3.0), (C5, 2.0),
        (DRUMS_W, 2.0), (DRUMS_W + 0.5, 4.5), (WH0 + 0.1, 4.0), (SURPRISE + 0.3, 1.0), (DELIGHT + 0.8, 5.0),
        (GLANCE + 0.4, 3.0), (BACK + 0.4, 6.0), (WH1, 5.0), (R11, 2.0), (R11E, 0.0), (UP, 0.0), (CUT_X, -2.0),
        (T1 + 1, -2.0)])
    d["hturn"] = Track([
        (T0, 0.02), (TOAST0, 0.02), (TOAST1, 0.05), (TOAST3, 0.02), (LF0 + 0.3, 0.02), (LF0 + 1.3, -0.12),
        (CUT_LR, -0.04), (LOOK0 + 0.1, -0.03), (LOOK0 + 0.9, 0.11), (LOOK1 + 0.6, 0.02), (WH0, 0.02),
        (SURPRISE + 0.3, 0.05), (GLANCE - 0.05, 0.04), (GLANCE + 0.3, 0.12), (BACK + 0.4, 0.05), (WH1, 0.04),
        (UP, 0.0),
        (UP + 0.3, -0.12, "io"), (CUT_X - 0.001, -0.14), (CUT_X, 0.0, "step"), (T1 + 1, 0.0)])
    # ---------------- eyes
    d["lid"] = Track([
        (T0, 0.92), (KZ0 + 1.0, 0.88), (KZ1, 0.86), (CH0, 0.9), (C4, 0.92), (LF0 + 1.0, 0.84), (CUT_LR, 0.76),
        (LOOK0, 0.74), (LOOK0 + 0.45, 0.95), (LOOK1, 0.9), (LOOK1 + 0.5, 0.8), (C5, 0.88), (WH0 + 0.1, 0.9),
        (SURPRISE + 0.15, 1.0, "out"), (DELIGHT + 0.5, 0.97), (GLANCE, 0.95), (GLANCE + 0.2, 1.0),
        (SNOD + 0.5, 0.94), (BACK, 0.95), (WH1, 0.92),
        (R11, 0.88), (UP, 0.9), (CUT_X, 0.86), (T1 + 1, 0.86)])
    d["blinks"] = [
        (C2 + 0.05, 0.3), (KAZOO_W + 0.1, 0.35), (TOAST2 + 0.2, 0.4), (C3 + 0.1, 0.3), (CH0 + 2.2, 0.3),
        (C4 + 0.1, 0.32), (FALL_APART + 0.6, 0.4), (CUT_L + 0.9, 0.35), (LOOK0 + 1.85, 0.5), (C5 + 0.1, 0.3),
        (DRUMS_W + 0.75, 0.3), (DELIGHT + 0.35, 0.22), (BACK - 0.1, 0.3), (R11 + 0.6, 0.3), (GOING - 0.05, 0.25),
        (UP + 0.08, 0.16), (WALK + 0.9, 0.15), (EXIT - 0.3, 0.15)]
    d["pupil"] = Track([(T0, 1.12), (KZ0, 1.1), (LF0, 1.15), (LOOK0 + 0.4, 1.2), (WH0, 1.15),
                        (SURPRISE + 0.3, 1.32), (WH1, 1.22), (R11, 1.05), (T1 + 1, 1.0)])
    d["squint"] = Track([
        (T0, 0.06), (KZ0 + 0.4, 0.06), (TOAST1, 0.24), (KZ1, 0.18), (CH0, 0.1), (CH0 + 2.0, 0.16),
        (C4, 0.06), (LF0 + 1.5, 0.1), (LOOK0 + 0.5, 0.18), (LF1, 0.12), (C5, 0.06), (WH0 + 0.1, 0.06),
        (SURPRISE + 0.2, 0.0), (DELIGHT + 0.6, 0.08), (GLANCE + 0.4, 0.1), (WH1, 0.1), (R11, 0.08),
        (T1 + 1, 0.06)])
    d["gaze"] = gaze([
        (T0, (0.2, -0.76)),
        (C2 + 0.04, CARD, 0.14), (Q08 + 1.2, QU, 0.14), (KAZOO_W - 0.05, CARD, 0.14),
        (TOAST0 - 0.1, QU, 0.16),                                              # the toast: to him
        (KZ0 + 2.35, CARD, 0.25), (KZ0 + 3.7, (0.3, -0.5), 0.3),
        (C3 + 0.04, CARD, 0.14), (Q09 + 1.0, QU), (CH0 + 0.3, CARD, 0.2), (CH0 + 1.8, MID, 0.3),
        (CH0 + 2.9, (0.32, 0.8), 0.22),                                         # ... her own foot
        (CH0 + 3.5, CARD, 0.2),
        (C4 + 0.04, CARD, 0.14), (Q10 + 1.0, QU), (FALL_APART + 0.25, (0.3, -0.1), 0.25),
        (LF0 + 0.5, WIN, 0.5),                                                  # the rain
        (LF0 + 1.7, DOWN, 0.45),
        (LOOK0, QU_UP, 0.42),                                                   # quiet recognition: up to him
        (LOOK1, (0.24, 0.2), 0.5),
        (C5 + 0.04, CARD, 0.14), (WHALE_W + 0.1, QU, 0.14), (DRUMS_W + 0.45, CARD, 0.2),
        (WH0 - 0.05, (0.42, -0.1), 0.2),                                       # the card folding into his palm
        (WH0 + 0.3, WHALEG, 0.22),                                             # the whale rising out of it
        (GLANCE, QU_UP, 0.16),                                                 # the glance up to him
        (BACK, WHALEG, 0.22), (WH1 - 0.45, (0.42, -0.08), 0.3),                # ... it dives into his palm
        (WH1 + 0.2, (0.3, 0.12), 0.3),
        (R11 - 0.15, QU, 0.14),                                                 # "You can just send them..."
        (DEVICE_E - 0.1, (0.28, 0.1), 0.18), (DEVICE_E + 0.12, QU, 0.12),
        (GOING + 0.15, (0.12, 0.3), 0.2), (R11E - 0.3, (-0.2, 0.2), 0.25),      # "I gotta get going."
        (UP + 0.1, (-0.5, 0.1), 0.14), (CUT_X, DOOR), (WALK + 0.8, (-0.66, 0.08)),
    ])
    # ---------------- brows / mouth
    d["brow_raise"] = Track([
        (T0, 0.32), (C2 + 0.3, 0.36), (KAZOO_W, 0.3), (KAZOO_W + 0.3, 0.5), (TOAST1, 0.42), (KZ1, 0.28),
        (C3, 0.32), (CH0 + 1.0, 0.2), (C4, 0.3), (FALL_APART, 0.3), (FALL_APART + 0.4, 0.45), (LF0, 0.35),
        (LF0 + 1.3, 0.4), (CUT_LR, 0.24), (LOOK0, 0.22), (LOOK0 + 0.5, 0.48), (LOOK1, 0.36), (LF1, 0.3),
        (C5, 0.3), (WHALE_W + 0.1, 0.3), (WHALE_W + 0.45, 0.46), (DRUMS_W + 0.6, 0.4), (WH0 + 0.1, 0.36),
        (SURPRISE + 0.22, 0.95, "out"), (DELIGHT + 0.6, 0.82), (GLANCE, 0.74), (GLANCE + 0.25, 0.86),
        (BACK + 0.3, 0.66), (WH1, 0.5),
        (R11, 0.36), (DEVICE_E, 0.3), (GOING + 0.3, 0.4), (R11E, 0.32), (UP, 0.35), (T1 + 1, 0.3)])
    d["worry"] = Track([
        (T0, 0.45), (KZ0, 0.35), (TOAST1, 0.26), (KZ1, 0.34), (CH0, 0.3), (C4, 0.32), (FALL_APART + 0.4, 0.55),
        (LF0 + 1.5, 0.6), (CUT_LR + 0.3, 0.66), (LOOK0 + 0.6, 0.56), (LF1, 0.6), (C5, 0.45), (WH0 + 0.1, 0.4),
        (SURPRISE + 0.3, 0.12), (DELIGHT + 0.8, 0.08), (WH1, 0.2), (R11, 0.6),
        (GOING, 0.62), (R11E, 0.64), (UP, 0.55), (T1 + 1, 0.5)])
    d["furrow"] = Track([(T0, 0.0), (GOING, 0.0), (GOING + 0.4, 0.08), (R11E, 0.05), (T1 + 1, 0.06)])
    d["wide"] = Track([(T0, 0.0), (WH0 + 0.1, 0.0), (SURPRISE + 0.18, 0.32, "out"), (DELIGHT + 0.5, 0.1),
                       (GLANCE + 0.2, 0.14), (BACK + 0.4, 0.06), (WH1, 0.0)])
    d["open"] = Track([
        (T0, 0.06), (KZ0 + 1.0, 0.04), (CH0, 0.03), (LF0, 0.04), (LOOK0 + 0.5, 0.06), (WH0 + 0.1, 0.05),
        (SURPRISE + 0.22, 0.2, "out"), (DELIGHT + 0.5, 0.1), (GLANCE + 0.5, 0.08), (WH1, 0.05),
        (R11 - 0.2, 0.03), (R11E, 0.02), (R11E + 0.25, 0.08), (UP, 0.06),
        (T1 + 1, 0.04)])
    d["smile"] = Track([
        (T0, 0.12), (KAZOO_W, 0.1), (KAZOO_W + 0.5, 0.16), (TOAST0, 0.2), (TOAST1, 0.34), (TOAST3, 0.3),
        (KZ1, 0.26), (C3, 0.16), (CH0 + 0.8, 0.12), (CH0 + 3.1, 0.24), (CH1, 0.18), (C4, 0.1),
        (FALL_APART + 0.4, 0.04), (LF0 + 1.5, 0.0), (CUT_LR + 0.3, -0.04), (LOOK0 + 0.3, -0.02),
        (LOOK0 + 1.0, 0.14), (LOOK1, 0.12), (LF1, 0.08), (C5, 0.08), (WHALE_W + 0.4, 0.14), (DRUMS_W + 0.5, 0.1),
        (WH0 + 0.1, 0.08), (SURPRISE + 0.2, 0.04), (DELIGHT, 0.12), (DELIGHT + 0.6, 0.52), (GLANCE + 0.3, 0.58),
        (BACK + 0.3, 0.48), (WH1, 0.36), (WH1 + 0.5, 0.22),
        (R11, 0.06), (DEVICE_E, 0.06), (GOING + 0.4, 0.02), (R11E, 0.0), (UP, -0.04), (T1 + 1, -0.04)])
    d["smirk"] = Track([(DELIGHT, 0.0), (DELIGHT + 0.7, 0.1), (BACK + 0.3, 0.12), (WH1, 0.06), (R11, 0.0)])
    d["tremble"] = Track([(T0, 0.06), (LF0 + 1.5, 0.08), (CUT_LR + 0.3, 0.16), (LOOK0 + 1.0, 0.1), (LF1, 0.1),
                          (WH0, 0.08), (SURPRISE + 0.3, 0.02), (WH1, 0.04), (R11, 0.1), (T1 + 1, 0.1)])
    # (the welling ebbs a little through the kazoo and the arcade piece, with the far streak drying - s3.far_tear)
    d["tears"] = Track([(T0, 0.5), (KZ1, 0.44), (CH1, 0.36), (LF0 + 1.5, 0.48), (LOOK0 + 0.6, 0.58), (LF1, 0.52),
                        (WH0, 0.44), (DELIGHT + 0.6, 0.38), (WH1, 0.38), (R11, 0.42), (T1 + 1, 0.42)])
    d["shine"] = Track([(T0, 0.6), (TOAST1, 0.72), (CH0, 0.5), (LF0 + 1.5, 0.65), (LOOK0 + 0.5, 0.78),
                        (WH0, 0.6), (SURPRISE + 0.3, 0.9), (WH1, 0.72), (R11, 0.55), (T1 + 1, 0.5)])
    d["blush"] = Track([(T0, 0.2), (TOAST1, 0.26), (CH0, 0.2), (DELIGHT + 0.6, 0.3), (R11, 0.32), (T1 + 1, 0.3)])
    d["sniffle"] = Track([(T0, 0.38), (CH1, 0.36), (LF1, 0.44), (WH1, 0.42), (T1 + 1, 0.5)])
    # ---------------- arcade foot tap (rig: 2.5 Hz sine on the draw clock; see TAP_SHIFT) + head bob
    d["tap"] = Track([(CH0 + 0.6, 0.0), (CH0 + 1.6, 0.75, "io"), (CH1 - 0.6, 0.85), (CH1 + 0.15, 0.0, "io")])
    d["bob"] = Track([(CH0 + 0.5, 0.0), (CH0 + 1.4, 1.0, "io"), (CH1 - 0.5, 1.0), (CH1 + 0.1, 0.0, "io")])
    d["kz_nod"] = Track([(TOAST0 + 0.2, 0.0), (TOAST1 + 0.1, 1.0, "io"), (TOAST2 + 0.3, 1.0),
                         (TOAST3 + 0.4, 0.0, "io")])
    # ---------------- arms
    d["arm_l"] = ArmSeq([
        (T0, LAP_L), (UP - 0.05, LAP_L), (RISE1, arm(REST_L, shoulder=10.0, elbow=24.0), "io"), (CUT_X, REST_L),
        (T1 + 1, REST_L)])
    d["arm_r"] = ArmSeq([
        (T0, HOLD), (TOAST0, HOLD), (TOAST1 - 0.08, TOAST_TINK, "io"), (TOAST1 + 0.22, TOAST_R, "io"),
        (TOAST2, TOAST_R), (TOAST3, HOLD, "io"),
        (UP, HOLD), (RISE1, CARRY_R, "io"), (T1 + 1, CARRY_R)])
    return d


_RT = _rae_tracks()


def _bob(t, beats, width=0.14, alt=False):
    """Head-bob pulse train: 0..1 dip peaking 0.06 s after each beat. alt: successive beats alternate sign."""
    v = 0.0
    for k, b in enumerate(beats):
        dt = t - b - 0.06
        w = width * 0.55 if dt < 0 else width
        if -2.4 * w < dt < 2.4 * w:
            p = math.exp(-(dt / w) ** 2)
            if alt:
                v += p if k % 2 == 0 else -p
            else:
                v = max(v, p)
    return v


# rig foot tap is a fixed 2.5 Hz sine on the draw clock: shift Rae's draw clock so the heel lands on the beats
_B0 = CHIP_BEATS[0] if CHIP_BEATS else CH0
TAP_SHIFT = ((0.5 - (2.5 * _B0) % 1.0) / 2.5) % 0.4


def _dip(t, t0, down=0.17, up=0.38):
    """0 -> 1 -> 0 head dip starting at t0: quick down, slower recover (a nod on a beat)."""
    x = t - t0
    if x <= 0.0 or x >= down + up:
        return 0.0
    if x < down:
        return math.sin(0.5 * math.pi * x / down) ** 2
    return 0.5 + 0.5 * math.cos(math.pi * (x - down) / up)


def _kazoo_nods(t):
    """Gentle half-time nods (chin down) on the kazoo's strong beats while the mug is up: 0..1."""
    return max((_dip(t, b - 0.04, 0.2, 0.42) for b in KZ_NODS), default=0.0)


def _slow_nod(t, t0, depth=0.12, down=0.45, up=0.65):
    """One small, slow acknowledging nod (chin down) starting at t0: head_nod offset (<= 0)."""
    return -depth * _dip(t, t0, down, up)


def rae_pose(t: float) -> Pose:
    d = _RT
    ph = walk_phase(t)
    lid = d["lid"](t) * (1.0 - blink_amt(t, d["blinks"]))
    lx, ly = d["gaze"](t)
    lx += 0.02 * noise1(t * 1.3, 9)
    ly += 0.016 * noise1(t * 1.1, 13)
    mo, mr = mouth("rae", t)
    nod = d["nod"](t) + 0.025 * noise1(t * 0.4, 3)
    tilt = d["tilt"](t) + 1.0 * noise1(t * 0.33, 5)
    bounce = d["bounce"](t)
    shoulders = d["shoulders"](t)
    lean = d["lean"](t)
    # kazoo: gentle nods in time while the mug is up (a small toast)
    kn = d["kz_nod"](t)
    if kn > 0:
        pk = _kazoo_nods(t)
        nod -= 0.2 * kn * pk
        bounce += 2.4 * kn * pk
    # arcade: a clear head bob on every beat (chin dips, the body gives a little), with the foot tap
    bb = d["bob"](t)
    if bb > 0:
        pb = _bob(t, CHIP_BEATS, 0.11)
        nod -= 0.24 * bb * pb
        bounce += 3.4 * bb * pb
        lean += 1.4 * bb * pb
        tilt += 2.6 * bb * _bob(t, CHIP_BEATS, 0.13, alt=True)
    # lo-fi: one small nod of recognition at him; whale song: the small nod after the glance up to him
    nod += _slow_nod(t, ACK_NOD, 0.1, 0.42, 0.6) + _slow_nod(t, SNOD, 0.12, 0.3, 0.5)
    # whale song: the little intake of breath of the surprise
    br = breathe(t, 0.2, 2) + 0.7 * bump(t, SURPRISE - 0.05, 0.7)
    p = Pose(
        x=rae_x(t), y=FLOOR, facing=rae_facing(t), turn=d["turn"](t), sit=rae_sit(t) if ph is None else 0.0,
        seat_y=SEAT_Y, walk=ph, lean=lean, bounce=bounce, shoulders_up=shoulders, breath=br,
        head_tilt=tilt, head_nod=nod, head_turn=d["hturn"](t) + 0.012 * noise1(t * 0.45, 4),
        lid_l=lid, lid_r=lid * (0.99 + 0.01 * noise1(t * 0.7, 3)), look_x=lx, look_y=ly, pupil=d["pupil"](t),
        squint=d["squint"](t), eye_wide=d["wide"](t), brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t),
        brow_furrow=d["furrow"](t),
        mouth_open=clamp(d["open"](t) + 0.8 * mo), mouth_round=clamp(mr), smile=d["smile"](t), smirk=d["smirk"](t),
        mouth_tremble=d["tremble"](t), tears=d["tears"](t), tear_l=s3.far_tear(t), tear_r=0.0,
        eye_shine=d["shine"](t), blush=d["blush"](t), sniffle=d["sniffle"](t), foot_tap=d["tap"](t),
        arm_r=d["arm_r"](t), arm_l=d["arm_l"](t), mug="r", **lighting(t),
    )
    return inherit(p, _S3_RAE, t, T0)


_S3_RAE = s3.rae_pose(T0)


# =========================================================================== the holo-whale (card 5)
PALM_UP = 10.0                          # the projector glow sits this far above his palm centre (hand_pos)
PALM_CARD = (FAN[0] - 4.0, FAN[1] - 46.0)   # where card 5 folds down into his palm
WHALE_SCALE = 0.95                      # fx.draw_whale_holo: ~120 long, orbit +-95 x +-45 at scale 1
WHALE_IN = CUT_W                        # card 5 folds down into his palm (from the cut) ...
WHALE_RISE = WH0 + 0.08                 # ... the whale swims up out of it with the first call
WHALE_DIVE = WH1 - 0.8                  # it dives back into his palm with the last notes ...
WHALE_OUT = WH1 - 0.05                  # ... and card 5 lights up again in its slot in the fan


def whale_state(t):
    """(scale, alpha) of the holographic whale above Quill's palm, or None (pure in t). fx.draw_whale_holo swims
    its own slow orbit; it grows up out of the palm and shrinks back into it, its projector staying on the palm."""
    if t < WHALE_RISE or t > WH1 + 0.12:
        return None
    s = t - WHALE_RISE
    rise = ease_out(clamp(s / 0.9))
    dive = ease_in(clamp((t - WHALE_DIVE) / 0.8))
    sc = WHALE_SCALE * (0.22 + 0.78 * rise) * (1.0 - 0.75 * dive)
    a = smoothstep(s / 0.3) * (1.0 - smoothstep((t - (WH1 - 0.35)) / 0.42))
    return sc, a


def whale_palm(t):
    """The projector point: just above Quill's actual palm (it follows the little launch lift of his hand)."""
    hx, hy = Q.hand_pos(quill_pose(t), "r")
    return hx, hy - PALM_UP


def _whale_fn():
    return getattr(fx, "draw_whale_holo", None)


def draw_whale(c, t):
    """The holo-whale above his palm (drawn with the cards). Nothing if fx does not have it."""
    ws = whale_state(t)
    fn = _whale_fn()
    if ws is None or fn is None:
        return
    sc, a = ws
    if a <= 0.003:
        return
    px, py = whale_palm(t)
    low = music_env("alt_whale", t, "low")            # the drums light the projector a little (0 without envelope)
    if low > 0.0:
        glow(c, px, py, 46.0, "#7FFFE9", 0.16 * low * a)
    fn(c, t, px, py - 70.0 * sc, scale=sc, alpha=a)


# =========================================================================== Quill
QA = Q.ARMS
PRESENT = QA["present"]
QREST = QA["rest"]
BEHIND = QA["behind_back"]
LISTEN = arm_add(PRESENT, -3.0, -5.0, 2.0)          # palm settles a touch while a piece plays
SEL = [(2, C2), (3, C3), (4, C4), (5, C5)]
PLAY_END = {2: KZ1, 3: CH1, 4: LF1, 5: WH1}
CUES = {2: "alt_kazoo", 3: "alt_chip", 4: "alt_lofi", 5: "alt_whale"}


def _quill_tracks():
    d = {}
    keys = [(T0, PRESENT)]
    for num, ts in SEL:
        keys += [(ts - 0.3, LISTEN if ts > T0 + 0.1 else PRESENT), (ts - 0.02, PRESENT, "io"),
                 (ts + 0.08, arm_add(PRESENT, 2.0, 6.0, -16.0), "out"), (ts + 0.32, PRESENT, "io")]
        if num < 5:
            keys += [(ts + 2.4, PRESENT), (ts + 3.3, LISTEN, "io")]
    # the whale: a small lift of the palm launches it; the palm holds it up, steady; it dives back in
    keys += [(WH0 - 0.06, PRESENT), (WH0 + 0.1, arm_add(PRESENT, 3.0, 7.0, -10.0), "out"),
             (WH0 + 0.5, PRESENT, "io"), (WHALE_DIVE, PRESENT), (WH1 - 0.2, arm_add(PRESENT, -1.5, -3.0, 4.0), "io"),
             (WH1 + 0.4, PRESENT, "io"), (T1 + 1, PRESENT)]
    d["arm_r"] = ArmSeq(keys)
    d["arm_l"] = ArmSeq([(T0, BEHIND), (T1 + 1, BEHIND)])
    d["tilt"] = Track([
        (T0, 6.0), (C2 + 0.3, 3.0), (KAZOO_W, 5.0), (KZ0 + 1.5, 8.0), (KZ1, 6.0), (C3, 3.0), (Q09E, 5.0),
        (CH0 + 2.0, 7.0), (CH1, 9.0), (C4, 3.0), (FALL_APART + 0.3, 5.0), (LF0 + 2.0, 6.0), (C5, 3.0),
        (WHALE_W + 0.3, 5.0), (WH0 + 0.5, 6.5), (GLANCE, 5.0), (WH1, 6.0), (R11, 4.0), (R11E, 6.0), (UP, 4.0),
        (T1, 1.0), (T1 + 1, 1.0)])
    d["nod"] = Track([
        (T0, 0.0), (C2 + 0.05, 0.06), (C2 + 0.45, 0.0), (C3, 0.06), (C3 + 0.4, 0.0), (C4, 0.06), (C4 + 0.4, 0.0),
        (FALL_APART + 0.9, 0.0), (FALL_APART + 1.1, -0.06), (FALL_APART + 1.4, 0.0), (C5, 0.06), (C5 + 0.4, 0.0),
        (DRUMS_W + 0.1, 0.0), (DRUMS_W + 0.3, -0.06), (DRUMS_W + 0.6, 0.0),           # "With drums." (deadpan)
        (WH0 + 0.5, 0.06), (GLANCE + 0.15, 0.06), (GLANCE + 0.35, -0.05), (GLANCE + 0.7, 0.03),   # meets her glance
        (WH1, 0.02), (R11, 0.0), (DEVICE_E, 0.0), (DEVICE_E + 0.2, -0.06),
        (DEVICE_E + 0.55, 0.0), (GOING + 0.4, 0.0), (GOING + 0.6, 0.05), (R11E + 0.2, 0.0), (T1 + 1, 0.0)])
    d["hturn"] = Track([(T0, 0.0), (UP, 0.0), (UP + 0.4, 0.04), (WALK + 0.9, 0.1), (EXIT, 0.16), (T1 + 1, 0.16)])
    d["brow"] = Track([
        (T0, 0.14), (C2, 0.1), (KAZOO_W, 0.16), (KZ0 + 1.0, 0.2), (KZ1, 0.14), (C3, 0.12), (CH0 + 3.0, 0.18),
        (C4, 0.1), (FALL_APART, 0.12), (C5, 0.08), (WH0 + 0.5, 0.16), (WH1 + 0.1, 0.16), (WH1 + 0.4, 0.28),
        (R11, 0.2), (GOING, 0.24), (UP, 0.3), (WALK + 0.6, 0.22), (T1 + 1, 0.2)])
    d["smile"] = Track([(T0, 0.05), (KZ0 + 1.5, 0.07), (C3, 0.04), (FALL_APART + 1.0, 0.06), (C5, 0.04),
                        (WH0 + 1.0, 0.04), (WH0 + 1.7, 0.13), (WH1, 0.1), (R11, 0.03), (UP, 0.0), (T1 + 1, 0.0)])
    d["glow"] = Track([(T0, 0.18), (WH0, 0.18), (WH0 + 0.6, 0.32), (WH1, 0.26), (R11, 0.18), (T1 + 1, 0.18)])
    RAE_S = s3.RAE_S
    CARDV = (-0.6, 0.06)
    WHALEQ = (-0.3, 0.42)                           # the whale above his palm
    d["gaze"] = gaze([
        (T0, RAE_S),
        (C2 - 0.1, CARDV), (Q08 + 1.1, RAE_S), (KZ0 + 2.0, (-0.38, 0.26)), (KZ1, RAE_S),
        (C3 - 0.1, CARDV), (Q09 + 0.9, RAE_S), (CH0 + 2.9, (-0.36, 0.7), 0.14), (CH0 + 3.6, RAE_S),   # her foot
        (C4 - 0.1, CARDV), (Q10 + 0.8, RAE_S), (FALL_APART - 0.1, CARDV), (FALL_APART + 0.6, RAE_S),
        (C5 - 0.1, CARDV), (WHALE_W - 0.05, RAE_S), (DRUMS_W + 0.65, (-0.36, 0.5), 0.14),    # card -> his palm
        (WH0 + 0.2, WHALEQ, 0.2), (WH0 + 1.05, RAE_S, 0.2),                    # the whale; then her reaction
        (CUT_WQ - 0.05, WHALEQ, 0.2), (WH1 + 0.1, RAE_S, 0.2),                 # the dive; then: the verdict?
        (UP + 0.12, (-0.5, 0.0), 0.12), (WALK + 0.4, (-0.66, 0.06), 0.2), (WALK + 1.2, (-0.8, 0.08), 0.25),
        (EXIT - 0.1, (-0.88, 0.08), 0.2),
    ], dur=0.09)
    return d


_QT = _quill_tracks()
_S3_QUILL = s3.quill_pose(T0)


def quill_pose(t: float) -> Pose:
    d = _QT
    mo, mr = mouth("quill", t)
    blink = auto_blink(t, seed=0, rate=4.6, robotic=True)
    lx, ly = d["gaze"](t)
    p = Pose(
        x=s3.QX, y=FLOOR, facing=-1.0, turn=0.35,
        head_turn=d["hturn"](t), head_nod=d["nod"](t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=d["tilt"](t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=blink, lid_r=blink, look_x=lx, look_y=ly, brow_raise=d["brow"](t),
        smile=d["smile"](t), mouth_open=0.9 * mo, mouth_round=mr, glow=d["glow"](t),
        arm_r=d["arm_r"](t), arm_l=d["arm_l"](t), **lighting(t),
    )
    return inherit(p, _S3_QUILL.copy(lid_l=None, lid_r=None), t, T0)


# =========================================================================== holo-cards
FOCUS_Q = (388.0, 474.0)                # beside his face (cards 3-5 are presented in Quill's mediums)
FOCUS = {2: s3.FOCUS_POS, 3: FOCUS_Q, 4: FOCUS_Q, 5: FOCUS_Q}
RETURN = {2: KZ1 - 0.6, 3: CH1 - 0.5, 4: LF1 - 0.6}     # each card glides back to its slot as its piece fades
FADE0 = SHUT - 0.2                      # the cards begin to fade as the door shuts (S5 finishes the fade)


def _card5_fold(t):
    """0..1: card 5 folding down into his palm for the whale."""
    return smoothstep((t - WHALE_IN) / 0.42)


def _focus_pos(t):
    """Per-card focus positions; card 5 travels from beside his face down into his palm."""
    f = dict(FOCUS)
    k = _card5_fold(t)
    if k > 0:
        f[5] = (lerp(FOCUS_Q[0], PALM_CARD[0], k), lerp(FOCUS_Q[1], PALM_CARD[1], k))
    return f


def _focus(t):
    """Selected card out in front from its select until its piece fades. Card 5: once it has folded into his palm
    (invisible) its focus eases off while the whale swims - the rest of the fan brightens back gently and the card
    re-forms in its own slot after the dive (no card flying through her single)."""
    f = {}
    for num, ts in SEL:
        a = smoothstep((t - ts) / 0.45)
        if num in RETURN:
            a *= 1.0 - smoothstep((t - RETURN[num]) / 0.6)
        else:
            a *= 1.0 - smoothstep((t - (WHALE_IN + 0.6)) / 1.2)
        if a > 0:
            f[num] = a
    return f


def _pops(t):
    p = {}
    for num, ts in SEL:
        dt = t - ts
        if 0 <= dt < 0.7:
            p[num] = 0.09 * math.sin(math.pi * clamp(dt / 0.7)) * (1 - dt / 0.7)
    return p


def _playing(t):
    """0..1 music pulse of the focused card while its piece plays."""
    for num, ts in SEL:
        m = music_cue(CUES[num])
        if m["start"] - 0.1 <= t <= m["end"] + 0.3:
            # (core.music_env reads frame 0 for the last frame before the cue - int() truncates toward zero - so
            # the pulse is gated to the cue itself; otherwise the card jumps a frame early)
            return num, (music_env(CUES[num], t) * smoothstep((t - m["start"]) / 0.16) if t >= m["start"] else 0.0)
    return None, 0.0


def fan_state(t):
    st = {"focus": _focus(t), "pops": _pops(t)}
    states = {1: 0.5 * (1.0 - smoothstep((t - C2) / 0.5))}
    num, env_ = _playing(t)
    if num is not None and num in st["focus"]:
        st["pops"][num] = st["pops"].get(num, 0.0) + 0.04 * env_
    st["states"] = states
    alphas = {}
    # whale song: the fan fades right back around the whale (a ghost of the menu); card 5 folds into his palm, and
    # re-forms in its slot after the dive
    lull = smoothstep((t - WHALE_IN) / 0.8) * (1.0 - smoothstep((t - WHALE_OUT) / 0.8))
    if lull > 0:
        for n in range(1, 9):
            alphas[n] = lerp(1.0, 0.22, lull)
    fold = _card5_fold(t)
    back = smoothstep((t - WHALE_OUT) / 0.5)
    c5 = max(1.0 - smoothstep((t - (WHALE_IN + 0.2)) / 0.32), back)
    alphas[5] = alphas.get(5, 1.0) * c5
    st["pops"][5] = st["pops"].get(5, 0.0) - 0.62 * fold * (1.0 - back)
    st["alphas"] = alphas
    st["alpha"] = 1.0 - 0.18 * smoothstep((t - FADE0) / (T1 - FADE0))
    st["focus_pos"] = _focus_pos(t)
    return st


def _fan_args(st):
    return dict(alpha=st["alpha"], focus=st["focus"], states=st["states"], pops=st["pops"], alphas=st["alphas"],
                focus_pos=st.get("focus_pos", FOCUS))


# Rae's singles frame her face, not the menu: a card that never gets at least FRAG_MIN of its body inside the
# frame during such a shot would only be a stray corner at the edge, so it is left out of that shot altogether
# (decided once per shot, so nothing pops while the camera moves). In Quill's mediums only slivers go.
RAE_SINGLES = ("K", "C", "LR", "WR", "R11")
FRAG_MIN = 0.8
QUILL_SINGLES = ("Q3", "Q4", "Q5", "WQ")
SLIVER_MAX = 0.6


def _inside(pts, n=10):
    """Fraction of the screen-space quad pts (4 corners) that lies inside the frame (n x n samples)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    k = 0
    for i in range(n):
        u = (i + 0.5) / n
        ax, ay = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        bx, by = x3 + (x2 - x3) * u, y3 + (y2 - y3) * u
        for j in range(n):
            v = (j + 0.5) / n
            x, y = ax + (bx - ax) * v, ay + (by - ay) * v
            k += (0.0 <= x < W and 0.0 <= y < H)
    return k / (n * n)


@lru_cache(maxsize=None)
def _stray_cards(name, a, b):
    if name not in RAE_SINGLES and name not in QUILL_SINGLES:
        return frozenset()
    need = FRAG_MIN if name in RAE_SINGLES else SLIVER_MAX
    f0, f1 = math.ceil(a * FPS - 1e-6), math.ceil(b * FPS - 1e-6) - 1
    frames = sorted({round(f0 + (f1 - f0) * i / 7) for i in range(8)})
    best = {}
    for f in frames:
        t = f / FPS
        cam = camera(name, t, a, b)
        for (num, x, y, rot, scl, al, stt) in s3.fan_cards(1.0, **_fan_args(fan_state(t))):
            if al <= 0.02:
                continue
            fr = _inside([cam.to_screen(px, py) for px, py in s3.card_corners(x, y, rot, scl, stt)])
            best[num] = max(best.get(num, 0.0), fr)
    return frozenset(n for n in range(1, 9) if best.get(n, 0.0) < need)


# Rae's singles where all that would show of Quill is the fingertips of his offered hand at the right edge
# (x >= ~387): he is left out of those frames rather than leaving a stray white blob there
HAND_ONLY = ("K", "LR", "R11")
# ... and Quill's mediums, where all that would show of Rae is her mug hand in the bottom-left corner
MUG_ONLY = ("Q3", "Q4", "Q5")


def draw_cards(c, t, shot=None):
    """The fan (+ note sparkles from the playing card, select flashes, the holo-whale). shot = (name, a, b)."""
    st = fan_state(t)
    stray = _stray_cards(*shot) if shot is not None else frozenset()
    if stray:
        st["alphas"] = {n: (0.0 if n in stray else st["alphas"].get(n, 1.0)) for n in range(1, 9)}
    for num, cue in ((2, "alt_kazoo"), (3, "alt_chip"), (4, "alt_lofi")):
        m = music_cue(cue)
        if m["start"] - 0.1 <= t <= m["end"] + 1.5 and num not in stray:
            fx_, fy_ = FOCUS[num]
            fx.draw_note_sparkles(c, t, music_onsets(cue), area=(fx_ - 80, fy_ - 150, fx_ + 80, fy_ - 60),
                                  seed=num, life=1.3, color="teal_glow", alpha=0.55, size=0.7)
    draw_fan(c, t, 1.0, **_fan_args(st))
    for num, ts in SEL:
        if ts <= t < ts + 0.6 and num not in stray:
            select_flash(c, t, ts + 0.05, *FOCUS[num], 0.8)
    if CH0 - 0.1 <= t <= CH1 + 0.3 and 3 not in stray:          # a few 8-bit sparkles around the arcade card
        amt = smoothstep((t - CH0) / 0.6) * (1.0 - smoothstep((t - CH1) / 0.3))
        fx_, fy_ = FOCUS[3]
        fx.draw_pixel_sparkles(c, t, area=(fx_ - 120, fy_ - 150, fx_ + 110, fy_ + 120), amount=amt, seed=31,
                               px=6.0, count=5)
    draw_whale(c, t)                    # the whale above his palm (card 5 became it)


# =========================================================================== door
def door(t):
    if t < DOOR_O:
        return 0.0
    if t < DOOR_C:
        return 1.0 - (1.0 - clamp((t - DOOR_O) / 0.55)) ** 3
    return 1.0 - clamp((t - DOOR_C) / (SHUT - DOOR_C)) ** 2           # slides shut, thunk at door_shut


def door_clip_rect(d):
    """Stage rect of the (partly) open door panel still covering the doorway."""
    return skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(d), FLOOR + 4)


# =========================================================================== cameras
SEAT_FACE = s3.seat_face()
QFACE = s3.QFACE


def _rae_head(t):
    return R.head_center(rae_pose(t))


def _follow_cam(t, z, sx, sy, k=0.5, ky=None, step=0.1):
    """Camera at zoom z holding Rae's (smoothed) face near screen (sx, sy), following k of her head motion."""
    hx, hy = smoothed(_rae_head, t, 5, step)
    ky = k if ky is None else ky
    return _face_cam(lerp(SEAT_FACE[0], hx, k), lerp(SEAT_FACE[1], hy, ky), z, sx, sy)


def camera(name, t, a, b):
    u = clamp((t - a) / max(1e-3, b - a))
    if name == "P2":                    # S3's presentation two-shot continues
        return s3.present_cam(t)
    if name == "K":                     # Rae medium: the smile, the nods
        return _follow_cam(t, 2.05 * (1.0 + 0.05 * ease_in_out(u)), 336.0, 500.0, 0.5)
    if name in ("Q3", "Q5"):            # Quill medium + the card beside him (Rae just out left)
        return drift(_face_cam(QFACE[0], QFACE[1], 1.85, 412.0, 420.0),
                     _face_cam(QFACE[0], QFACE[1], 1.93, 414.0, 424.0), t, a, b)
    if name == "Q4":                    # a touch closer for the deadpan
        return drift(_face_cam(QFACE[0], QFACE[1], 2.0, 420.0, 430.0),
                     _face_cam(QFACE[0], QFACE[1], 2.08, 421.0, 432.0), t, a, b)
    if name == "C":                     # Rae medium-wide: the whole figure, her feet in frame
        return drift(Camera(318.0, 800.0, 1.42), Camera(318.0, 798.0, 1.46), t, a, b)
    if name == "L":                     # "lo-fi beats to quietly fall apart to": the album-cover wide
        return drift(Camera(352.0, 650.0, 1.04), Camera(340.0, 656.0, 1.1), t, a, b)
    if name == "LR":                    # Rae medium close: the eye wipe
        return _follow_cam(t, 2.55 * (1.0 + 0.04 * ease_in_out(u)), 340.0, 500.0, 0.5)
    if name == "W":                     # whale song: the wide two-shot - the whale rises between them
        return drift(Camera(380.0, 676.0, 1.08), Camera(382.0, 668.0, 1.13), t, a, b)
    if name == "WR":                    # Rae medium (frame left); his palm, the whale and his face frame right
        return _follow_cam(t, 1.62 * (1.0 + 0.04 * ease_in_out(u)), 200.0, 600.0, 0.5)
    if name == "WQ":                    # Quill + the whale: the last call and the dive (Rae just out left)
        return drift(Camera(510.0, 566.0, 2.0), Camera(510.0, 560.0, 2.08), t, a, b)
    if name == "R11":                   # Rae medium: "You can just..." - follows her up as she stands
        return _follow_cam(t, 1.95, 330.0, 470.0, 0.45, 0.6)
    if name == "X":                     # wide: the door (x -140..60) and Quill (x 545) both readable
        return drift(Camera(198.0, 700.0, 0.82), Camera(200.0, 704.0, 0.84), t, a, b)
    return Camera()


# =========================================================================== render
def render(canvas, t):
    name, a, b = shot_at(t)
    cam = camera(name, t, a, b)
    light, warm, rain = room(t)
    dr = door(t)
    rp = rae_pose(t)
    qp = quill_pose(t)
    c = canvas
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, t, light=light, door=dr, rain=rain, warm=warm)
    if name not in HAND_ONLY:
        Q.draw(c, qp, t)
    # once she is on her feet her head is up among the cards: the holograms hang BEHIND her from the cut
    # before she rises (seated, nothing overlaps, so the switch never shows)
    cards_behind = t >= CUT_R11
    if cards_behind:
        draw_cards(c, t, (name, a, b))
    if name in MUG_ONLY:
        pass
    elif t >= IN_DOOR:
        # through the doorway she is behind the door plane: the closing panel covers her, and nothing of her
        # shows right of the right-hand jamb
        c.save()
        c.clipRect(door_clip_rect(dr), skia.ClipOp.kDifference, True)
        c.clipRect(skia.Rect(env.DOOR_X1, -2000, 4000, 4000), skia.ClipOp.kDifference, True)
        R.draw(c, rp, t)
        c.restore()
    else:
        R.draw(c, rp, t + TAP_SHIFT if name == "C" else t)
    env.draw_lounge_front(c, t, light=light, door=dr, warm=warm)
    if not cards_behind:
        draw_cards(c, t, (name, a, b))
    c.restore()
