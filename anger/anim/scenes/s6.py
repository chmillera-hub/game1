"""S6 - The friend (BIBLE section 4, S6; continues from S5's handoff, section 9).

Anger sleeps against the wall (snoring from the dark). Drip... drip... saliva lands on his cheek (the drops fall
from above frame - we do not see the source); a twitch, a frown, a sleepy swat; one exhausted eye opens and looks
up: a huge pink tongue, dripping, right above his face - he jolts awake: THE FRIEND looms over him, dumb grin,
beady eyes. "What the hell are you?" - "That's my friend. He's saying hi (a little wave). I think he likes you." -
plop, on his head - he shifts out from under the drips - "Tell your friend to give me a little space. (plip)
Please." - the friend side-eyes him, huffs, crosses its arms and stomps backward with sass (three stomps on the
music, the ground shakes, dust falls). "Hey, he can hear you, buddy..." - he rolls his eyes and wipes his face.
Awkward silence (the friend squints, taps its foot; Anger pretends not to notice). "Well. How are you guys gonna
get out of here?" - the voice laughs for way too long (one eyebrow, crossed arms) - "...How do you feel about
that?" - "Well... I guess I'll die then." - the friend snorts and giggles behind its paws - the tiniest smirk -
he notices, clears his throat - dead serious again - the end card.

Deadpan: static frames, silences that sit, reactions a beat late, tiny faces. render(canvas, t) is a pure
function of absolute time t; anger_pose / friend_pose run continuously through every cut, shots pick cameras.
All times come from build/timeline.json names; contact-locked SFX offsets from build/sfx_timing_notes.md.
Shared helpers (light, renderer, gaze / blink / breath, camera helpers) come from anim.scenes.s5.
Push-ins stay inside one of env's tile-resolution buckets (quarter octaves) so they never refill the tile cache
mid-shot; close-ups draw the set at half resolution (s5.SOFT_BG_ZOOM).

Staging: Anger propped against the wall (pelvis at s5.SIT_X, facing screen-left toward the dark). The friend
(char_friend, scale FS ~ 2x his height) stands at his feet, a little deeper in the grotto (drawn behind him),
leaning down over him (lean_down) with its tongue (tongue_layer="skip", drawn in front of him) hanging above his
face. Its stomps carry it back toward the dark (screen-left). The saliva drops are drawn here (fx.saliva_drop):
they form at F.tongue_tip, fall with gravity and land on Anger (A.face_pos) exactly on the SFX hit frames.
The friend's body is only drawn from the reveal on (in the sleep close-ups the source stays unseen).

Shot list (absolute times only for orientation)
  A  163.96 -> 165.3    S5's medium-wide, creeping in: asleep, snoring from the dark
  B  -> sees_tongue     ECU (static): drip1 (twitch), drip2 (frown), the sleepy swat (hand_wave), side_eye_open
  C  -> startled        LOW CLOSE: his face low in frame, the tongue hanging into frame above it, a drop forming
  D  -> +1.3            WIDE REVEAL (shake): he jolts awake - the friend looms, filling the frame
  E  -> m04-0.1         MEDIUM-CLOSE Anger looking up (a03), the drop stretching above him
  F  -> m04 gap 2       the FRIEND (low angle): "That's my friend. He's saying hi." - a little wave
  G  -> sass-0.08       TWO-SHOT: "...I think he likes you." (plop on his head), shift_away, a04 (plip) "Please."
  H  -> 190.55          WIDE: the sass - side-eye, huff, arms crossed, three stomps (shake, dust); m05
  I  -> wipe-0.25       the friend, smug, nodding ("We go way back, okay?")
  J  -> awkward         CLOSE Anger: eye roll + wipes his face
  K  -> 196.1           WIDE two-shot (awkward silence): squint, arms crossed, foot taps; he looks away
  L  -> laugh-0.08      MEDIUM Anger: eyes slide back once, then away; a05
  M  -> 205.4           MEDIUM-CLOSE Anger: one eyebrow up, arms crossed (the laugh)
  N  -> 208.4           WIDE two-shot: the friend looks between the dark and Anger
  O  -> m07-0.1         CLOSE Anger, holding the brow; the laugh dies
  P  -> snort-0.3       slow PUSH-IN on Anger through m07; the beat; a06 (flat)
  Q  -> anger_smirk-0.13  the FRIEND: snort, paws over the mouth, giggle (shoulder bounces on the pulses)
  R  -> serious         ECU Anger: the tiniest smirk; he notices; throat clear
  S  -> end_card        heroic low-angle MEDIUM: dead serious, a tiny chin-lift on the horn tag
  T  -> end             END CARD: the dark grotto (the friend still giggling), "ANGER", fade out over ~1 s
"""
from __future__ import annotations

import math
from functools import lru_cache

import skia

from anim import char_anger as A
from anim import char_friend as F
from anim import fx
from anim.core import (Camera, Track, beat, clamp, col, ease_in_out, fade_overlay, lerp, line_end, line_start,
                       mouth, scene_span, smoothstep, timeline, window)
from anim.light import Light
from anim.rig import ArmPose, Pose
from anim.scenes import s5
from anim.scenes.s5 import (AMB, FLOOR, REST_FAR, REST_NEAR, SIT_X, ArmSeq, Breath, Gaze, blinks, cam_at, drift,
                            dress_anger, lit_pose, pick, pulse, render_world, scene_lights, sfx_time)
from config import H

# =========================================================================== timing (all from names)
T0, T1 = scene_span("s6")
S, E = line_start, line_end

SLEEPING = beat("sleeping")
DRIP1, DRIP2 = beat("drip1"), beat("drip2")
LAND1 = sfx_time("saliva_drip", DRIP1 - 0.05) + 0.02          # saliva_drip: the drop lands +0.02
LAND2 = sfx_time("saliva_drip", DRIP2 - 0.05) + 0.02
WAVE = beat("hand_wave")
SIDE = beat("side_eye_open")
SEES = beat("sees_tongue")
STARTLED = beat("startled")                                    # startle_sting: hit on the beat, gasp +0.04..+0.35
A03, A03E = S("a03"), E("a03")
M04, M04E = S("m04"), E("m04")
M04_HI, M04_LIKES = M04 + 1.29, M04 + 2.71                     # "He's saying hi." / "I think he likes you."
SHIFT = beat("shift_away")
SCRAPE2 = sfx_time("armor_scrape", SHIFT - 0.05)
SETTLE2 = SCRAPE2 + 0.62
A04, A04E = S("a04"), E("a04")
A04_PLEASE = A04 + 2.08                                        # "...Please." (lip-sync gap 182.85-183.06)
SASS = beat("sass")
HUFF = sfx_time("creature_huff", SASS - 0.05)
HUFF_PEAK = HUFF + 0.09
STOMPS = [s["start"] for s in timeline()["sfx"] if s["name"] == "stomp" and s["start"] >= SASS - 1e-6][:3]
STOMP_DT = STOMPS[1] - STOMPS[0]                               # 0.7 s: one stomp cycle
STOMP_PH0 = STOMPS[0] - F.STOMP_HIT * STOMP_DT                 # phase 0 of the stomp cycles
STOMP_END = STOMP_PH0 + 3 * STOMP_DT
M05, M05E = S("m05"), E("m05")
M05_RESPECT, M05_BACK = M05 + 1.75, M05 + 3.46                 # "Treat him with some respect." / "We go way back"
WIPE = beat("wipe_saliva")
AWK = beat("awkward")
TAP0 = sfx_time("foot_tap_heavy", AWK - 0.05)
TAPS = [TAP0 + k for k in range(5)]                            # foot_tap_heavy: taps exactly 0/1/2/3/4 s
TAP_PH0 = TAP0 - F.TAP_HIT                                     # phase 0 (1 s per tap)
A05, A05E = S("a05"), E("a05")
LAUGH = beat("laugh_start")
M06E = E("m06")
M07, M07E = S("m07"), E("m07")
M07_STUCK, M07_HOW = M07 + 3.79, M07 + 6.37
A06, A06E = S("a06"), E("a06")
SNORT = beat("snort")
SNORT_SFX = sfx_time("creature_snort", SNORT - 0.05)           # wet "gk" +0.30, "pff" +0.42..0.75
GIGGLE = sfx_time("creature_giggle", SNORT)
GIG_PULSES = [0.09, 0.21, 0.33, 0.48, 0.59, 0.95, 1.06, 1.17, 1.30, 1.41, 1.54, 1.66, 1.99, 2.14, 2.25, 2.38]
GIG_INTAKES = [0.76, 1.84]
GIG_SIGH = (2.42, 2.85)
SMIRK = beat("anger_smirk")
NOTICE = beat("notices_smirk")
CLEAR = sfx_time("anger_throat_clear", NOTICE - 0.05)          # "hhrr" 0-0.30 (pk .18), "HM" 0.36-0.78 (pk .42)
SERIOUS = beat("serious")
END_CARD = beat("end_card")

# =========================================================================== the friend: placement
FX0, FY, FS = 240.0, 1120.0, 1.05      # looming spot (tongue tip right above his face), floor, scale (~2x him)
F_TURN = 0.15
LOOM_LEAN = 14.0
TONGUE = 0.16
STEP = 160.0                           # local units per sassy stomp (the rig default is 60: these are big ones)


def _stomp_travel():
    q = Pose(x=FX0, y=FY, scale=FS, facing=1.0)
    q.extra = dict(legs="stomp", phase=3.0, stomp_step=STEP)
    return F.stomp_offset(q)


FX1 = FX0 + _stomp_travel()            # where the three stomps leave it (back toward the dark)

# =========================================================================== saliva drops
G_FALL = 2300.0                        # stage units / s^2
DROP_SIZE = 2.1


def tip_anchor(t):
    """Stage point the forming drop hangs from: under the end of the tongue."""
    q = friend_pose(t)
    tp = F.tongue_tip(q, t)
    if tp is None:
        return None
    return (tp[0], tp[1] + 30.0 * FS)


class Drop:
    """One drop: forms at the tongue from `form` (grows + stretches), detaches at `release`, falls with gravity
    and lands on target(t) exactly at `land` (then a small splat)."""

    def __init__(self, form, land, target, stretch_max=0.55, form_ease=1.0):
        self.form, self.land, self.target = form, land, target
        self.smax = stretch_max
        self.form_ease = form_ease
        a = tip_anchor(land - 0.4)
        bulb = self._bulb(a, self.smax)
        tg = target(land)
        dy = max(20.0, tg[1] - bulb[1])
        self.fall = math.sqrt(2.0 * dy / G_FALL)
        self.release = land - self.fall
        self.a_rel = tip_anchor(self.release)
        self.p0 = self._bulb(self.a_rel, self.smax)

    @staticmethod
    def _bulb(a, st):
        s = DROP_SIZE
        ln = s * (3 + 70 * st ** 1.3)
        rb = s * (6.5 + 2.0 * st)
        return (a[0], a[1] + ln + rb * 0.85)

    def stretch(self, t):
        u = clamp((t - self.form) / max(0.05, self.release - self.form))
        return self.smax * (u ** self.form_ease)

    def draw(self, c, t, light=1.0):
        if t < self.form or t > self.land + 0.45:
            return
        if t < self.release:
            a = tip_anchor(t)
            if a is None:
                return
            u = clamp((t - self.form) / 0.35)
            fx.saliva_drop(c, a[0], a[1], size=DROP_SIZE * (0.35 + 0.65 * smoothstep(u)), stretch=self.stretch(t),
                           alpha=0.95 * light, color="#DDEFF2")
            return
        if t < self.land:
            u = (t - self.release) / self.fall
            tg = self.target(t)
            x = lerp(self.p0[0], tg[0], smoothstep(u))
            y = lerp(self.p0[1], tg[1], u * u)
            # a thin snapped strand recoiling to the tongue for a moment
            if t - self.release < 0.12:
                a = tip_anchor(t)
                k = 1.0 - (t - self.release) / 0.12
                c.drawLine(a[0], a[1], a[0], a[1] + 40.0 * k, _line("#DDEFF2", 2.0, 0.6 * k * light))
            fx.saliva_drop(c, x, y, size=DROP_SIZE, detached=True, alpha=0.95 * light, color="#DDEFF2")
            return
        # splat: a few tiny droplets popping out of the impact
        age = t - self.land
        tg = self.target(t)
        for i in range(5):
            ang = math.radians(-160 + 140 * i / 4)
            sp = 110.0 + 40.0 * (i % 2)
            x = tg[0] + math.cos(ang) * sp * age
            y = tg[1] + math.sin(ang) * sp * age + 900.0 * age * age
            a = (1.0 - age / 0.45) * 0.8 * light
            c.drawCircle(x, y, 2.2, _fill("#E8F6F8", a))


def _fill(color, a):
    p = skia.Paint(AntiAlias=True)
    p.setColor(col(color, clamp(a)))
    return p


def _line(color, w, a):
    p = skia.Paint(AntiAlias=True, StrokeWidth=w, Style=skia.Paint.kStroke_Style)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setColor(col(color, clamp(a)))
    return p


# =========================================================================== Anger's performance
AR = A.ARMS
NEAR_CHEEK = (35.0, 17.0)              # face_pos coords (x0 > 0 = his LEFT = the side nearer the camera)
BROW_SPOT = (17.0, -40.0)              # drip2: on the forehead above the near brow (-> the frown)
CROWN = (6.0, -64.0)

# ---- body
SLEEP_MIX = Track([(STARTLED + 0.01, 1.0), (STARTLED + 0.15, 0.0, "out")])
X_SHIFT = Track([(SHIFT + 0.06, 0.0), (SETTLE2 - 0.02, 34.0, "io")])
LEAN = Track([(SHIFT + 0.06, 0.0), (SHIFT + 0.4, -5.0, "io"), (SETTLE2, -4.0), (SETTLE2 + 0.25, -3.2)])

SWAT_UP = ArmPose(shoulder=85.0, elbow=110.0, wrist=0.0, hand="open", across=0.4)        # paw at the cheek
SWAT_THRU = ArmPose(shoulder=104.0, elbow=66.0, wrist=-22.0, hand="open", across=0.05)    # ...flung out
SWAT_DROP = ArmPose(shoulder=60.0, elbow=56.0, wrist=0.0, hand="relaxed")
JOLT_NEAR = ArmPose(shoulder=52.0, elbow=74.0, wrist=0.0, hand="open")
JOLT_FAR = ArmPose(shoulder=42.0, elbow=46.0, wrist=0.0, hand="open")
WIPE_A = ArmPose(shoulder=88.0, elbow=112.0, wrist=4.0, hand="open", across=0.42)        # palm on the near cheek
WIPE_B = ArmPose(shoulder=70.0, elbow=118.0, wrist=16.0, hand="open", across=0.3)         # ...dragged down/out
WIPE_T = WIPE + 0.3                    # the wipe starts after the eye roll

ARM_NEAR = ArmSeq([(T0, REST_NEAR), (WAVE - 0.45, REST_NEAR), (WAVE - 0.08, SWAT_UP, "io"),
                   (WAVE + 0.1, SWAT_THRU, "out"), (WAVE + 0.45, SWAT_DROP, "io"), (WAVE + 1.0, REST_NEAR, "io"),
                   (STARTLED, REST_NEAR), (STARTLED + 0.12, JOLT_NEAR, "out"), (STARTLED + 0.9, REST_NEAR, "io"),
                   (WIPE_T, REST_NEAR), (WIPE_T + 0.28, WIPE_A, "io"), (WIPE_T + 0.62, WIPE_B, "io"),
                   (WIPE_T + 1.1, REST_NEAR, "io")])
ARM_FAR = ArmSeq([(T0, REST_FAR), (STARTLED, REST_FAR), (STARTLED + 0.14, JOLT_FAR, "out"),
                  (STARTLED + 1.0, REST_FAR, "io")])
CROSS = Track([(LAUGH + 1.75, 0.0), (LAUGH + 2.6, 1.0, "io")])

# ---- breathing (asleep: slow and deep; awake: normal)
_RATE6 = Track([(T0, 0.15), (STARTLED, 0.15), (STARTLED + 0.3, 0.26), (STARTLED + 4.0, 0.21)])
_AMP6 = Track([(T0, 1.45), (STARTLED, 1.45), (STARTLED + 0.3, 1.0), (STARTLED + 4.0, 0.95)])
# integrated from S5's start with S5's rates before the boundary, so the breathing phase runs on seamlessly
BREATH = Breath(
    s5.T0, T1,
    rate=lambda t: s5.BREATH.rate(t) if t < T0 else _RATE6(t),
    amp=lambda t: s5.BREATH.amp(t) if t < T0 else _AMP6(t),
    override=Track([(STARTLED, 0.0), (STARTLED + 0.3, 1.4, "out"), (STARTLED + 1.4, 0.6), (CLEAR, 0.3),
                    (CLEAR + 0.18, -0.6), (CLEAR + 0.3, 0.2), (CLEAR + 0.42, -1.0, "out"), (CLEAR + 0.9, 0.0)]),
    weight=Track([(STARTLED - 0.02, 0.0), (STARTLED + 0.05, 1.0), (STARTLED + 1.4, 1.0), (STARTLED + 2.4, 0.0),
                  (CLEAR - 0.15, 0.0), (CLEAR + 0.02, 1.0), (CLEAR + 0.9, 1.0), (CLEAR + 1.5, 0.0)]),
    seed=s5.BREATH.seed,
)

# ---- eyes / face
LID = Track([(T0, 0.0), (SIDE, 0.0), (SIDE + 0.45, 0.42, "io"), (SEES + 0.32, 0.42), (SEES + 0.5, 0.58),
             (STARTLED, 0.58), (STARTLED + 0.06, 1.0, "out"), (STARTLED + 0.6, 1.0), (STARTLED + 1.15, 0.86),
             (M04_LIKES + 0.75, 0.86), (M04_LIKES + 0.95, 0.12, "io"), (M04_LIKES + 1.3, 0.12),
             (SHIFT + 0.05, 0.62), (A04 + 0.4, 0.74), (M05_BACK, 0.74), (M05_BACK + 0.5, 0.68),
             (WIPE + 0.3, 0.7), (WIPE_T + 0.24, 0.32), (WIPE_T + 0.66, 0.32), (WIPE_T + 0.95, 0.8), (A05, 0.8),
             (A05 + 0.3, 0.86), (LAUGH + 0.6, 0.86), (LAUGH + 1.9, 0.82), (M07, 0.82), (A06 - 0.4, 0.8),
             (A06, 0.68), (A06E + 0.4, 0.68), (SNORT + 0.4, 0.68), (SNORT + 0.55, 0.8), (SMIRK, 0.8),
             (SMIRK + 0.4, 0.74), (NOTICE, 0.74), (NOTICE + 0.08, 0.9, "out"), (SERIOUS, 0.86),
             (SERIOUS + 0.5, 0.9)])
ONE_EYE = Track([(T0, 0.0), (SIDE - 0.05, 0.0), (SIDE, 1.0, "step"), (STARTLED + 0.02, 1.0), (STARTLED + 0.1, 0.0)])
EYE_WIDE = Track([(STARTLED, 0.0), (STARTLED + 0.05, 1.0, "out"), (STARTLED + 0.55, 0.9), (STARTLED + 1.25, 0.0),
                  (SEES + 0.32, 0.0)])
GAZE = Gaze([
    (T0, 0.05, 0.45),
    (SIDE + 0.05, -0.32, -0.62, 0.35, "io"),     # exhausted, sideways, up
    (SEES + 0.18, -0.18, -0.92, 0.1),            # on the tongue / the drop
    (STARTLED + 0.03, -0.3, -0.95, 0.06),        # up at the friend's face
    (STARTLED + 1.2, -0.24, -0.88, 0.1),
    (M04 + 0.3, -0.96, 0.04, 0.09),              # "That's my friend." -> the dark
    (M04_HI + 0.25, -0.2, -0.95, 0.1),           # the wave
    (M04_LIKES + 0.1, -0.14, -0.9, 0.08),        # the drop above
    (SHIFT + 0.3, -0.32, -0.82, 0.1),
    (SASS + 0.42, -0.18, -1.0, 0.12),            # it straightens up
    (STOMPS[0] - 0.05, -0.36, -0.95, 0.3, "io"),  # tracking it back
    (STOMPS[1] - 0.05, -0.52, -0.9, 0.3, "io"),
    (STOMPS[2] - 0.05, -0.66, -0.85, 0.3, "io"),
    (M05 + 0.3, -0.97, 0.02, 0.09),              # "Hey, he can hear you, buddy." -> the dark
    (M05_RESPECT + 0.35, -0.68, -0.82, 0.1),     # back to the friend
    (WIPE + 0.95, -0.3, 0.2, 0.25, "io"),
    (AWK + 0.35, 0.72, -0.22, 0.45, "io"),       # pretending not to notice (off into the distance)
    (TAPS[2] + 0.35, -0.62, -0.7, 0.3, "io"),    # ...slides back once
    (TAPS[2] + 1.05, 0.74, -0.2, 0.38, "io"),    # ...and away again
    (A05 + 0.05, -0.62, -0.72, 0.1),             # "Well."
    (A05 + 1.0, -0.96, 0.04, 0.08),              # "you guys" (the dark)
    (A05 + 1.6, -0.64, -0.7, 0.08),
    (LAUGH + 0.22, -0.92, 0.04, 0.09),           # the laugh (the dark)
    (LAUGH + 5.3, -0.95, 0.07, 0.07),
    (M07 + 0.2, -0.9, 0.03, 0.07),
    (A06 - 0.3, -0.88, 0.06, 0.07),
    (SNORT + 0.42, -0.74, -0.62, 0.09),          # the snort (a beat late)
    (NOTICE, -0.15, 0.32, 0.07),                 # he notices: eyes flick down
    (NOTICE + 0.55, -0.55, 0.12, 0.09),
    (SERIOUS + 0.12, -0.62, -0.12, 0.12),        # heroic middle distance
])
BLINKS = [STARTLED + 1.3, A03E + 0.15, M04 + 0.28, M04_HI + 0.22, A04 + 1.0, A04_PLEASE - 0.12, STOMPS[0] + 0.03,
          M05 + 0.27, M05_RESPECT + 0.33, M05_BACK + 0.9, AWK + 0.32, TAPS[1] + 0.5, TAPS[4] + 0.3,
          A05 + 0.02, A05 + 0.97, LAUGH + 0.2, LAUGH + 4.0, LAUGH + 7.1, M07 + 2.6, M07 + 5.6, M07E + 0.5,
          A06E + 0.6, SNORT + 0.4, NOTICE + 0.62, SERIOUS + 1.35, END_CARD + 1.6, END_CARD + 3.4]

HEAD_NOD = Track([(T0, -0.05), (STARTLED, -0.05), (STARTLED + 0.4, 0.3, "out"), (STARTLED + 1.2, 0.22), (M04 + 0.2, 0.22),
                  (M04 + 0.5, 0.06), (M04_HI + 0.15, 0.06), (M04_HI + 0.45, 0.2), (SHIFT, 0.2), (SHIFT + 0.5, 0.12),
                  (A04, 0.14), (SASS + 0.3, 0.14), (SASS + 0.7, 0.22), (M05, 0.22), (M05 + 0.4, 0.06),
                  (M05_RESPECT + 0.3, 0.06), (M05_RESPECT + 0.6, 0.16), (WIPE, 0.16), (WIPE + 0.5, 0.06),
                  (AWK + 0.3, 0.06), (AWK + 0.8, 0.1), (A05, 0.1), (A05 + 0.4, 0.12), (LAUGH + 0.2, 0.12),
                  (LAUGH + 0.5, 0.0), (A06 - 0.3, 0.0), (A06 + 0.3, -0.04), (SNORT + 0.4, -0.04),
                  (SNORT + 0.7, 0.08), (NOTICE, 0.08), (NOTICE + 0.2, -0.02), (SERIOUS + 0.12, -0.02),
                  (SERIOUS + 0.95, 0.14, "io")])
HEAD_TURN = Track([(T0, -0.02), (STARTLED, -0.02), (STARTLED + 0.3, 0.08), (SHIFT + 0.1, 0.08), (SETTLE2, -0.04),
                   (AWK + 0.25, -0.04), (AWK + 0.9, -0.16, "io"), (A05 - 0.05, -0.16), (A05 + 0.35, 0.06, "io"),
                   (LAUGH + 0.2, 0.06), (LAUGH + 0.6, 0.12), (SNORT + 0.4, 0.12), (SNORT + 0.7, 0.06),
                   (SERIOUS + 0.1, 0.06), (SERIOUS + 0.9, 0.1)])
HEAD_TILT = Track([(T0, 0.0), (SHIFT + 0.08, 0.0), (SETTLE2, -5.0), (A04E + 0.4, -3.0), (WIPE_T + 0.15, -3.0),
                   (WIPE_T + 0.5, 2.0), (WIPE_T + 1.0, 0.0)])
BROW_FURROW = Track([(T0, 0.0), (LAND2 + 0.28, 0.0), (LAND2 + 0.55, 0.55, "out"), (WAVE + 0.6, 0.45),
                     (SIDE + 0.5, 0.3), (STARTLED, 0.3), (STARTLED + 0.1, 0.0), (STARTLED + 1.0, 0.0),
                     (STARTLED + 1.4, 0.28), (A03 + 0.3, 0.32), (M04, 0.25), (SHIFT, 0.3), (A04 + 0.3, 0.35),
                     (SASS, 0.3), (M05, 0.22), (AWK, 0.12), (A05, 0.18), (LAUGH, 0.15), (M07, 0.2),
                     (M07_STUCK + 0.4, 0.2), (M07_STUCK + 0.8, 0.32), (A06 - 0.5, 0.2), (A06, 0.1),
                     (SMIRK, 0.05), (NOTICE + 0.1, 0.05), (NOTICE + 0.3, 0.28), (SERIOUS + 0.3, 0.32)])
SQUINT = Track([(SHIFT - 0.1, 0.0), (SHIFT + 0.25, 0.45), (A04 + 0.5, 0.35), (SASS + 0.2, 0.3), (SASS + 0.8, 0.12),
                (M05, 0.08), (AWK, 0.05)])
RAISED = Track([(LAUGH + 0.55, 0.0), (LAUGH + 2.0, 1.0, "io"), (M06E + 0.25, 1.0), (M06E + 1.0, 0.0, "io")])
SMIRK_T = Track([(SMIRK + 0.02, 0.0), (SMIRK + 0.45, 0.38, "io"), (NOTICE + 0.05, 0.38), (NOTICE + 0.22, 0.0, "io")])
SUPPRESS = Track([(NOTICE, 0.0), (NOTICE + 0.08, 1.0, "out"), (NOTICE + 0.45, 0.6), (CLEAR + 0.9, 0.0)])


def anger_pose(t) -> Pose:
    """Anger at absolute time t in S6 (stage coords)."""
    mix = SLEEP_MIX(t)
    p = Pose(x=SIT_X + X_SHIFT(t), y=FLOOR, facing=-1.0, turn=0.3, arm_l=ARM_NEAR(t), arm_r=ARM_FAR(t))
    p.lean = LEAN(t)
    p.breath = BREATH(t)
    # ---- jolts: the startle; the ground shaking under the stomps; the shift's settle; the throat clear
    jolt = pulse(t, STARTLED + 0.01, 0.07, 0.3)
    stomp_b = sum(math.exp(-(t - h) / 0.09) * math.sin((t - h) * 40.0) for h in STOMPS if 0.0 <= t - h < 0.5)
    p.bounce = -11.0 * jolt + 3.5 * stomp_b - 3.0 * pulse(t, SETTLE2, 0.04, 0.12) - 3.0 * pulse(t, CLEAR + 0.38, 0.04, 0.1)
    hh = pulse(t, CLEAR + 0.02, 0.14, 0.12)
    hm = pulse(t, CLEAR + 0.37, 0.05, 0.13)
    p.shoulders_up = 0.6 * jolt + 0.22 * hh + 0.32 * hm
    # ---- face
    lx, ly = GAZE(t)
    # the eye roll before the wipe (quick, weary): up and around to the right
    u = (t - WIPE) / 0.5
    if 0.0 < u < 1.6:
        a = math.pi * (0.78 - 0.95 * ease_in_out(min(1.0, u)))
        rx, ry = 0.85 * math.cos(a), -0.97 * math.sin(a)
        w = smoothstep(u / 0.15) * (1.0 - smoothstep((u - 1.0) / 0.6))
        lx, ly = lerp(lx, rx, w), lerp(ly, ry, w)
    p.look_x, p.look_y = lx, ly
    lid = LID(t) * blinks(t, BLINKS)
    # drip1: a tiny twitch of the closed lids (squeeze), drip2's frown is in BROW_FURROW
    p.lid_l = p.lid_r = lid
    tw1 = pulse(t, LAND1 + 0.28, 0.05, 0.16)
    tw2 = pulse(t, LAND2 + 0.3, 0.06, 0.25)
    p.squint = clamp(SQUINT(t) + 0.55 * tw1 + 0.3 * tw2 + 0.1 * SMIRK_T(t) / 0.38)
    p.eye_wide = EYE_WIDE(t)
    p.pupil = 1.0 - 0.18 * window(t, SEES + 0.3, STARTLED + 1.0, 0.25, 0.5)
    p.head_nod = HEAD_NOD(t) + 0.28 * jolt - 0.1 * hh - 0.14 * hm
    p.head_turn = HEAD_TURN(t)
    p.head_tilt = HEAD_TILT(t) - 1.6 * tw1 - 1.2 * tw2 + 2.5 * window(t, WAVE - 0.3, WAVE + 0.6, 0.2, 0.4)
    p.brow_raise = 0.85 * pulse(t, STARTLED + 0.02, 0.05, 0.45) + 0.1 * window(t, SIDE, STARTLED, 0.4, 0.05)
    p.brow_furrow = BROW_FURROW(t) + 0.15 * tw1
    p.brow_worry = 0.12 * window(t, SIDE, STARTLED, 0.4, 0.05)
    mo, mr = mouth("anger", t)
    gasp = window(t, STARTLED + 0.04, STARTLED + 0.35, 0.05, 0.15)
    mo = max(mo, 0.36 * gasp)
    mr = max(mr, 0.4 * gasp)
    mo = max(mo, 0.06 * pulse(t, CLEAR + 0.02, 0.12, 0.1))         # "hhrr" (the "HM" is mouth-closed)
    p.mouth_open, p.mouth_round = mo, mr
    p.smile = -0.18 * tw2 - 0.1 * window(t, LAND2 + 0.3, SIDE + 0.5, 0.2, 0.6) - 0.06 * window(t, SERIOUS, T1, 0.4, 0.1)
    p.smirk = SMIRK_T(t)
    rb = RAISED(t)
    ex = dict(state="prop_sit", state_b="sleep", mix=mix, sword=None, shield="back", bruised=1.0,
              one_eye=ONE_EYE(t), knee_up=0.55, rim_dir=-105.0, cross_arms=CROSS(t),
              brow_l=1.0 * rb, brow_r=-0.3 * rb, smirk_suppress=SUPPRESS(t))
    p.extra = ex
    return p


# =========================================================================== the friend's performance
def _gig(t):
    """Giggle shoulder-bounce envelope synced to creature_giggle's pulses (0..1) and its intakes/sigh."""
    v = 0.0
    for o in GIG_PULSES:
        v = max(v, pulse(t, GIGGLE + o - 0.03, 0.035, 0.07))
    return v


def _gig_end(t):
    """Silent leftover giggles for the end card."""
    v = 0.0
    for o in (1.3, 1.42, 1.55, 1.7, 3.0, 3.12, 3.26):
        v = max(v, pulse(t, END_CARD + o, 0.04, 0.08))
    return v


F_LEAN_DOWN = Track([(SASS + 0.08, 1.0), (SASS + 0.6, 0.0, "io")])
F_LEAN = Track([(SASS + 0.05, LOOM_LEAN), (SASS + 0.6, 0.0, "io")])
F_TONGUE = Track([(T0, 0.05), (SIDE + 0.3, 0.05), (SEES - 0.1, TONGUE, "io"), (SASS + 0.02, TONGUE),
                  (SASS + 0.32, 0.0, "in")])
F_LOOK = Gaze([
    (T0, 0.15, 0.0),
    (SHIFT + 0.35, 0.3, 0.05, 0.12),
    (SASS + 0.1, 0.55, 0.15, 0.08),
    (M05 + 0.4, -0.7, 0.0, 0.1),               # its eyes go to the dark when the voice speaks for it
    (M05 + 1.2, 0.55, 0.2, 0.1),
    (AWK - 0.3, 0.45, 0.25, 0.1),
    (LAUGH + 0.55, -0.9, 0.0, 0.12),            # between the dark and Anger
    (LAUGH + 2.3, 0.65, 0.2, 0.12),
    (LAUGH + 4.0, -0.9, 0.0, 0.12),
    (LAUGH + 5.5, 0.65, 0.2, 0.12),
    (LAUGH + 6.9, -0.85, 0.0, 0.12),
    (M07 + 0.4, 0.55, 0.15, 0.12),
    (M07_STUCK + 0.2, 0.6, 0.22, 0.1),
])
F_HEAD_TURN = Track([(LAUGH + 0.5, 0.0), (LAUGH + 0.8, -0.16), (LAUGH + 2.25, -0.16), (LAUGH + 2.55, 0.1),
                     (LAUGH + 3.95, 0.1), (LAUGH + 4.25, -0.16), (LAUGH + 5.45, -0.16), (LAUGH + 5.75, 0.1),
                     (LAUGH + 6.85, 0.1), (LAUGH + 7.15, -0.14), (M07 + 0.35, -0.14), (M07 + 0.7, 0.06)])


def _expr_weights(t):
    """Blend dict of the friend's expression presets at t."""
    if t < SASS:
        return {"dumb_grin": 1.0}
    if t < M05 + 1.5:
        se = smoothstep((t - SASS) / 0.22)
        hf = window(t, SASS, SASS + 0.75, 0.06, 0.35)
        return {"dumb_grin": 1.0 - se, "side_eye": se * (1.0 - 0.55 * hf), "huff": 0.55 * hf}
    if t < WIPE + 0.3:
        sm = smoothstep((t - M05_RESPECT) / 0.4)
        return {"side_eye": 1.0 - sm, "smug": sm}
    if t < A05 + 0.4:
        sq = smoothstep((t - WIPE - 0.3) / 0.4)
        return {"smug": 1.0 - sq, "squint": sq}
    if t < SNORT:
        q = smoothstep((t - A05 - 0.4) / 0.6)
        g = smoothstep((t - LAUGH - 1.6) / 1.2) * (1.0 - smoothstep((t - A06 + 0.2) / 0.6))
        return {"squint": 1.0 - q, "neutral": q * (1.0 - g), "dumb_grin": q * g}
    sn = window(t, SNORT, GIGGLE + 0.12, 0.1, 0.12)
    gg = smoothstep((t - GIGGLE + 0.05) / 0.15) * (1.0 - smoothstep((t - GIGGLE - GIG_SIGH[1] - 0.6) / 0.8))
    ge = window(t, END_CARD + 1.1, END_CARD + 3.6, 0.3, 0.5)
    gg = max(gg, ge)
    rest = max(0.0, 1.0 - sn - gg)
    return {"snort": sn, "giggle": gg, "dumb_grin": rest}


def _arms(t):
    if t < SASS + 0.25:
        if M04_HI + 0.1 < t < M04_LIKES + 0.1:
            w = 0.8 * window(t, M04_HI + 0.15, M04_LIKES, 0.3, 0.4)
            return {"rest": 1.0 - w, "wave": w}
        return "rest"
    if t < LAUGH + 1.0:
        c = smoothstep((t - SASS - 0.25) / 0.38)
        if c >= 1.0:
            tp = window(t, AWK - 0.2, A05 + 0.3, 0.3, 0.3)
            return {"cross": 1.0 - tp, "tap": tp} if tp > 0 else "cross"
        return {"rest": 1.0 - c, "cross": c}
    if t < SNORT + 0.2:
        r = smoothstep((t - LAUGH - 1.0) / 0.6)
        return {"cross": 1.0 - r, "rest": r} if r < 1.0 else "rest"
    cv = smoothstep((t - SNORT - 0.2) / 0.32) * (1.0 - smoothstep((t - GIGGLE - GIG_SIGH[1] - 0.5) / 0.6))
    ce = window(t, END_CARD + 1.0, END_CARD + 3.7, 0.3, 0.5)
    cv = max(cv, ce)
    return {"rest": 1.0 - cv, "cover_mouth": cv} if cv < 1.0 else "cover_mouth"


def friend_pose(t) -> Pose:
    q = Pose(x=FX0, y=FY, scale=FS, facing=1.0, turn=F_TURN)
    q.lean = F_LEAN(t) + 0.8 * math.sin(2 * math.pi * 0.21 * t)
    ex = dict(tongue=F_TONGUE(t), lean_down=F_LEAN_DOWN(t), tongue_layer="skip", shadow=0.3)
    ex["expr"] = _expr_weights(t)
    ex["arms"] = _arms(t)
    # legs: stand / three stomps / (after the cut at `awkward`) foot taps at the new spot
    if t < STOMP_PH0:
        ex["legs"] = "stand"
    elif t < AWK:
        ex["legs"] = "stomp"
        ex["phase"] = clamp((t - STOMP_PH0) / STOMP_DT, 0.0, 3.0)
        ex["stomp_step"] = STEP
    else:
        q.x = FX1
        ph = t - TAP_PH0
        if 0.0 <= ph < 5.0:
            ex["legs"] = "foot_tap"
            ex["phase"] = ph
        else:
            ex["legs"] = "stand"
    # puffs: the huff (air blast peak +0.09) and the snort's "pff" (+0.42..0.75)
    if HUFF <= t < HUFF + 1.0:
        ex["puff"] = clamp((t - HUFF - 0.03) / 0.95)
    elif SNORT_SFX + 0.38 <= t < SNORT_SFX + 1.3:
        ex["puff"] = clamp((t - SNORT_SFX - 0.4) / 0.85)
    else:
        ex["puff"] = 0.0
    # giggle: drive the shoulder bounce ourselves (pulses of the SFX); the rig's own hop kept tiny
    g_on = window(t, GIGGLE - 0.1, GIGGLE + GIG_SIGH[1], 0.05, 0.3)
    ex["giggle"] = 0.12 * g_on
    gb = _gig(t) + 0.8 * _gig_end(t)
    intake = sum(window(t, GIGGLE + o - 0.04, GIGGLE + o + 0.12, 0.05, 0.08) for o in GIG_INTAKES)
    sigh = window(t, GIGGLE + GIG_SIGH[0], GIGGLE + GIG_SIGH[1], 0.1, 0.3)
    snort_jerk = pulse(t, SNORT_SFX + 0.28, 0.04, 0.12)
    q.bounce = -16.0 * gb + 10.0 * sigh - 8.0 * intake - 14.0 * snort_jerk
    q.shoulders_up = 0.35 * gb + 0.3 * intake - 0.3 * sigh
    q.head_nod = (0.12 * snort_jerk + 0.06 * gb
                  + 0.14 * (pulse(t, M05_BACK + 0.12, 0.12, 0.18) + pulse(t, M05_BACK + 0.62, 0.12, 0.18))
                  + 0.1 * window(t, M05_RESPECT + 0.2, WIPE, 0.4, 0.6))
    q.head_tilt = 4.0 * window(t, M04_HI, M04E + 0.5, 0.4, 0.6)
    q.head_turn = F_HEAD_TURN(t)
    lx, ly = F_LOOK(t)
    q.look_x, q.look_y = lx, ly
    q.extra = ex
    return q


# =========================================================================== drops (positions + timing)
def _face_pt(spot):
    return lambda t: A.face_pos(anger_pose(t), spot[0], spot[1], t)


def _lap_pt(t):
    q = anger_pose(t)
    hc = A.head_center(q, t)
    return (tip_anchor(t)[0], hc[1] + 285.0)


DROPS = []


def _make_drops():
    if not DROPS:
        DROPS.extend([
            Drop(LAND1 - 1.15, LAND1, _face_pt(NEAR_CHEEK), stretch_max=0.3),
            Drop(LAND2 - 1.05, LAND2, _face_pt(BROW_SPOT), stretch_max=0.3),
            Drop(SEES - 0.6, M04_LIKES + 0.55, _face_pt(CROWN), stretch_max=0.62, form_ease=0.55),
            Drop(A04 + 0.35, A04_PLEASE - 0.14, _lap_pt, stretch_max=0.5),
        ])
    return DROPS


def wet_spots(c, t, light=1.0):
    """Saliva left on him: cheek (drip1), forehead (drip2), crown (the third drop) - gone when he wipes."""
    if t >= WIPE_T + 0.62:
        return
    q = anger_pose(t)
    fade = 1.0 - smoothstep((t - WIPE_T - 0.32) / 0.26)
    for land, spot, sz, seed in ((LAND1, NEAR_CHEEK, 1.0, 1), (LAND2, BROW_SPOT, 0.85, 2),
                                 (M04_LIKES + 0.55, CROWN, 1.25, 3)):
        if t < land:
            continue
        age = t - land
        x, y = A.face_pos(q, spot[0], spot[1], t)
        a = 0.8 * fade * light
        spread = smoothstep(age / 0.12)
        r = 5.2 * sz * (0.6 + 0.4 * spread)
        c.drawOval(skia.Rect(x - r * 1.35, y - r * 0.75, x + r * 1.35, y + r * 0.75), _fill("#CFE6EA", 0.5 * a))
        c.drawCircle(x - r * 0.5, y - r * 0.2, r * 0.3, _fill("#FFFFFF", 0.85 * a))
        # two tiny satellite droplets from the splat
        for k, (dx0, dy0) in enumerate(((-2.1, -0.9), (1.9, 0.6))):
            qx, qy = A.face_pos(q, spot[0] + dx0 * 5.0 * sz, spot[1] + dy0 * 5.0 * sz, t)
            c.drawCircle(qx, qy, 1.4 * sz * spread, _fill("#E8F6F8", 0.8 * a))


# =========================================================================== shots / cameras
@lru_cache(maxsize=None)
def _face(t):
    return A.head_center(anger_pose(t), t)


@lru_cache(maxsize=None)
def _cheek(t):
    return A.face_pos(anger_pose(t), NEAR_CHEEK[0], NEAR_CHEEK[1], t)


@lru_cache(maxsize=None)
def _fhead(t):
    return F.head_center(friend_pose(t), t)


CUT_C = SEES - 0.06
CUT_E = STARTLED + 1.3
CUT_F = M04 - 0.1
CUT_G = M04_HI + 1.25
CUT_H = SASS - 0.08
CUT_I = M05_BACK - 0.21
CUT_J = WIPE - 0.25
CUT_L = TAPS[2] - 0.93
CUT_M = LAUGH - 0.08
CUT_N = LAUGH + 3.47
CUT_O = LAUGH + 6.47
CUT_P = M07 - 0.1
CUT_Q = SNORT - 0.3
CUT_R = SMIRK - 0.13
CUT_S = SERIOUS
CUT_B = LAND1 - 1.66                   # cut into the extreme close-up (the drop falls in ~1.5 s later)


def _cu_sleep():
    c = _cheek(round(LAND1, 2))
    return cam_at(c, 3.3, 372.0, 615.0)


def _cam_a(t):
    """S5's closing medium-wide, creeping in (zoom kept inside one env tile bucket, (1.19, 1.41])."""
    a = s5.cam_f()
    f = _face(round(T0, 2))
    b = cam_at(f, 1.4, *a.to_screen(*f))
    return drift(a, b, t, T0, CUT_B + 0.4, ease=lambda x: smoothstep(x) * 0.5 + x * 0.5)


def _cam_c(t):
    f = _face(round(SEES, 2))
    return cam_at(f, 2.4, 392.0, 880.0)


def _cam_d(t):
    return Camera(392.0, 470.0, 0.56)


def _cam_e(t):
    f = _face(round(A03, 2))
    return cam_at(f, 1.6, 410.0, 640.0)


def _cam_f(t):
    """The friend and its little wave (its waving paw is far out to the right of its head)."""
    return Camera(640.0, 430.0, 0.5)


def _cam_g(t):
    f = _face(round(A04, 2))
    return cam_at((f[0] - 40.0, f[1]), 0.98, 360.0, 640.0)


def wide_two():
    """Two-shot wide after the stomps: the friend's face at the left, Anger at the right."""
    return Camera(130.0, 430.0, 0.52)


def _cam_h(t):
    return Camera(150.0, 410.0, 0.56)


def _cam_i(t):
    h = _fhead(round(M05_BACK, 2))
    return cam_at(h, 0.95, 320.0, 470.0)


def _cam_j(t):
    f = _face(round(WIPE, 2))
    return cam_at(f, 2.3, 372.0, 540.0)


def _cam_l(t):
    f = _face(round(A05, 2))
    return cam_at(f, 1.55, 445.0, 560.0)


def _cam_m(t):
    f = _face(round(LAUGH + 2.5, 2))
    return cam_at(f, 1.9, 400.0, 520.0)


def _cam_o(t):
    f = _face(round(LAUGH + 7.0, 2))
    return cam_at(f, 2.4, 380.0, 530.0)


def _cam_p(t):
    f = _face(round(M07 + 3.0, 2))
    a = cam_at(f, 2.03, 400.0, 552.0)            # slow creep inside one env tile bucket (2.0, 2.38]
    b = cam_at(f, 2.37, 380.0, 532.0)
    return drift(a, b, t, CUT_P, M07E + 0.3, ease=lambda x: 0.6 * smoothstep(x) + 0.4 * x)


def _cam_q(t):
    h = _fhead(round(GIGGLE + 0.5, 2))
    return cam_at(h, 0.9, 360.0, 520.0)


def _cam_r(t):
    f = _face(round(SMIRK + 0.5, 2))
    return cam_at((f[0], f[1] + 22.0), 3.0, 372.0, 560.0)


def _cam_s(t):
    f = _face(round(SERIOUS + 1.0, 2))
    a = cam_at(f, 1.43, 400.0, 470.0)
    b = cam_at(f, 1.52, 400.0, 470.0)
    c = drift(a, b, t, CUT_S, END_CARD, ease=lambda x: x)
    return Camera(c.cx, c.cy, c.zoom, 1.6, 0.0)


def _cam_t(t):
    a = Camera(175.0, 380.0, 0.54)
    b = Camera(175.0, 340.0, 0.505)
    return drift(a, b, t, END_CARD, T1, ease=lambda x: x)


SHOTS = [
    (T0, _cam_a),
    (CUT_B, lambda t: _cu_sleep()),
    (CUT_C, _cam_c),
    (STARTLED, _cam_d),
    (CUT_E, _cam_e),
    (CUT_F, _cam_f),
    (CUT_G, _cam_g),
    (CUT_H, _cam_h),
    (CUT_I, _cam_i),
    (CUT_J, _cam_j),
    (AWK, lambda t: wide_two()),
    (CUT_L, _cam_l),
    (CUT_M, _cam_m),
    (CUT_N, lambda t: wide_two()),
    (CUT_O, _cam_o),
    (CUT_P, _cam_p),
    (CUT_Q, _cam_q),
    (CUT_R, _cam_r),
    (CUT_S, _cam_s),
    (END_CARD, _cam_t),
]


def camera(t):
    cam = pick(SHOTS, t)
    ev = [(STARTLED + 0.01, 7.0, 0.45)] + [(h, 13.0, 0.6) for h in STOMPS] + [(h, 2.0, 0.25) for h in TAPS]
    ev = [e for e in ev if 0.0 <= t - e[0] < e[2]]
    if ev:
        cam = fx.camera_shake(cam, t, ev, seed=61)
    return cam


# =========================================================================== render
def _grit(t):
    """Dust falling from the ceiling after each stomp (stomp: dust falls 0.35-1.6)."""
    return max([window(t, h + 0.35, h + 1.6, 0.15, 0.5) for h in STOMPS] + [0.0])


def show_body_t(t):
    return t >= STARTLED


def render(canvas, t):
    cam = camera(t)
    q = friend_pose(t)
    fh = F.head_center(q, t)
    end_k = smoothstep((t - END_CARD) / 1.4)                       # the end card darkens the grotto
    f_key = Light(fh[0], fh[1] + 60.0, 640.0 * FS, 0.26 * (1.0 - 0.85 * end_k), "#A2B6DA", "point")
    f_low = Light(q.x + 120.0 * FS, FY - 150.0, 620.0 * FS, 0.16 * (1.0 - 0.85 * end_k), "#8FA6D0", "point")
    p = anger_pose(t)
    hc = A.head_center(p, t)
    lights = scene_lights(t, extra=[f_key, f_low] if show_body_t(t) else [], strength=1.0 - 0.7 * end_k, head=hc)
    amb = AMB - 0.045 * end_k
    dress_anger(p, hc, lights, amb=amb, rim=0.6 - 0.15 * end_k)
    lit_pose(q, fh, lights, amb=amb, rim=0.35 + 0.35 * end_k, rim_color="#8FB4D0", tint_amt=0.2 + 0.25 * end_k,
             base=0.62 - 0.25 * end_k)
    show_body = show_body_t(t)
    show_tongue = t >= CUT_C
    drops = _make_drops()

    grit = _grit(t)

    def lit_fx(c):
        wet_spots(c, t)
        if grit > 0.01:
            # grit shaken loose from the dark above, falling through the frame
            top = cam.cy - (H / 2) / cam.zoom - 40.0
            for k, (x0, x1) in enumerate(((-420.0, -40.0), (60.0, 420.0), (520.0, 900.0))):
                fx.dust_fall(c, t, x0, x1, top, amount=grit, seed=70 + k, length=1500.0, size=2.4)
        for d in drops:
            d.draw(c, t)
        if t >= STOMPS[0] - 0.1 and t < AWK:
            for i, h in enumerate(STOMPS):
                age = t - h
                if 0.0 <= age < 2.2:
                    side = "l" if i % 2 == 0 else "r"
                    fp = F.foot_pos(q, side, t)
                    fx.dust_cloud(c, t, fp[0], FY + 6.0, age, size=1.1, seed=40 + i, n=12, alpha=0.6, life=2.0)

    render_world(canvas, t, cam, anger=p, friend=q, friend_mod=F, lit_fx=lit_fx, amb=amb, lights=lights,
                 dust=0.12, grit=grit, friend_body=show_body, friend_tongue=show_tongue)
    if t >= END_CARD:
        a = smoothstep((t - END_CARD - 0.25) / 1.1)
        button = END_CARD + 3.6                              # the endcard cue's dry button
        fx.draw_title(canvas, t, "ANGER", alpha=a, cy=0.5 * H, glow=1.0 + 0.6 * pulse(t, button, 0.03, 0.3))
        fade_overlay(canvas, smoothstep((t - (T1 - 1.0)) / 1.0))


# =========================================================================== sfx
def sfx_events():
    """Motion-locked sounds not in the timeline: Anger's plate shifts and the two extra drops."""
    ev = [
        ("armor_shift", WAVE - 0.38, -21.0),                 # the sleepy swat
        ("armor_shift", WAVE + 0.75, -22.0),                 # ...the arm flops back
        ("armor_shift", STARTLED + 0.03, -15.0),             # the jolt
        ("saliva_drip", M04_LIKES + 0.55 - 0.02, -13.0),     # plop on his head
        ("saliva_drip", A04_PLEASE - 0.14 - 0.02, -16.0),    # plip (just misses him)
        ("armor_shift", WIPE_T + 0.02, -18.0),               # the wipe
        ("armor_shift", LAUGH + 1.78, -17.0),                # crosses his arms
        ("armor_shift", CLEAR + 0.36, -22.0),                # the "HM" chest pump
    ]
    return [{"name": n, "start": round(s, 3), "gain_db": g} for n, s, g in ev]
