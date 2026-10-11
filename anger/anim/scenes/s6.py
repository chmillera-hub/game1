"""S6 - The friend (BIBLE section 4, S6; continues from S5's handoff, section 9) - rev 2.

Rev 2: a narrator speaks over the action (never on screen) and every narration is paired with what we see; the
dialogue is slower; the friend is SMALLER (~1.37x Anger's standing height: FS = 0.7 of the rig's 1600) so it
plausibly can't climb out either; its sassy retreat is four big stomps that carry it well back toward the dark,
and it stays back there through m05, the wipe and the awkward silence; the smirk is a warm one (the rig's
smirk now relaxes the brows and lifts the cheeks - nothing here pushes the brows down on top of it).

Anger sleeps against the wall (snoring from the dark). n33 "He did not sleep for long." Drip... drip... saliva
lands on his cheek (falling into the close-up from above - we do not see the source); a twitch, a frown, a
sleepy swat; n34 "Something warm... and wet..." (another drop lands on "wet") "...was dripping on his face."
One exhausted eye opens and looks up: a pink tongue, dripping, right above his face - he jolts awake: THE
FRIEND leans over him, dumb grin, beady eyes. "What the hell are you?!" - "That's my friend. He's saying hi (a
little wave). I think he likes you." - plop, on his head - n35 "Anger shuffled out from under the drool." -
"Tell your friend to give me a little space." (plip - a drop just misses him in the long pause) "Please." -
n36 "The creature did not like that." (its grin falls, its eyes narrow) - it huffs, crosses its arms and
stomps backward four times (on the stomp SFX / music; the ground shakes, grit falls). m05 - n37 "Anger wiped
the slobber from his face." - the awkward silence (n38; the friend squints and taps its foot far away; he
pretends not to notice) - a05 - the voice laughs for way too long (one eyebrow, crossed arms) - m07 - a06
(flat) - the friend snorts and giggles behind its paws - the tiniest, warm smirk - he notices, clears his
throat - dead serious again; n39 "For one brief moment, Anger had almost smiled." - the end card with n40.

render(canvas, t) is a pure function of absolute time t; anger_pose / friend_pose run continuously through
every cut, shots pick cameras. All times come from build/timeline.json names; phrase boundaries inside lines
from build/lipsync.json (s5.phrases); contact-locked SFX offsets from build/sfx_timing_notes.md.

Staging: Anger propped against the wall (pelvis s5.SIT_X, facing screen-left toward the dark). The friend stands
at his feet, a little deeper in the grotto (drawn behind him), leaning over him (lean + lean_down) with its tongue
(tongue_layer="skip", drawn in front of him) hanging above his face; its x and tongue length are SOLVED against
the rig at import (loom_place) so the tongue tip hangs right above his face whatever the tongue's shape. The
stomps carry it to FX1 (well left of his feet, toward the hermit's darkness); the rig's stomp travel is used, so
the planted feet never slide; its legs return to a normal stance at a cut. The first three drops fall from above
the close-up (their source is never seen: the friend's body is only drawn from the reveal on); the later ones
form at F.tongue_tip, fall with gravity and land on him exactly on time.

Shot list (absolute times only for orientation)
  A  199.56 -> drip1-0.55   S5's medium-wide creeping in: asleep; n33
  B  -> sees_tongue         ECU (static): drip1 (twitch), drip2 (frown), the swat; n34 + drip3 on "wet";
                            side_eye_open
  C  -> startled            LOW CLOSE: his face low in frame, the tongue above it, a drop forming
  D  -> a03-0.1             WIDE REVEAL (shake): he jolts awake - the friend leans over him
  E  -> m04-0.1             MEDIUM-CLOSE Anger looking up: a03; the drop stretching above him
  F  -> m04 "likes you"     the FRIEND and its little wave ("He's saying hi.")
  G  -> n36-0.15            TWO-SHOT: plop on his head; n35 shift_away; a04 (plip) ... "Please."
  H  -> sass-0.1            the FRIEND's face: n36 - the grin falls, the eyes narrow
  I  -> 4th stomp+0.6       the DISTANCE WIDE: huff, arms crossed, four stomps back (shake, grit)
  J1 -> m05 "Treat him"     MEDIUM Anger: "Hey, he can hear you, buddy." (he looks over at it)
  J2 -> m05 "We go way"     the distance wide
  J3 -> n37-0.1             the friend, smug, nodding ("We go way back, okay?")
  K  -> awkward             CLOSE Anger: n37 - a weary eye roll, he wipes his face
  L  -> 3rd tap+0.55        the distance wide: awkward silence, squint, crossed arms, foot taps; n38
  M  -> laugh-0.08          MEDIUM Anger: his eyes slide back once, then away; a05
  N  -> laugh+3.47          MEDIUM-CLOSE Anger: one eyebrow up, arms crossed (the laugh)
  O  -> laugh+6.47          the distance wide: the friend looks between the dark and Anger
  P  -> m07-0.1             CLOSE Anger, holding the brow; the laugh dies
  Q1 -> m07 "But now"       slow PUSH-IN on Anger
  Q2 -> m07 "How do you"    the friend far back, grinning, nodding ("...stuck in here with us.")
  Q3 -> snort-0.3           CLOSE Anger: "How do you feel about that?" - the beat - a06 (flat)
  R  -> anger_smirk-0.13    the FRIEND: snort, paws over the mouth, giggle (bounces on the SFX pulses)
  S  -> serious             ECU Anger: the tiniest warm smirk; he notices; throat clear
  T  -> end_card            heroic low-angle MEDIUM: dead serious, chin-lift on the horn tag; n39
  U  -> end                 END CARD: the dark grotto, the two of them far apart (the friend still giggling),
                            "ANGER", n40; fade out over the last ~1 s
Push-ins stay inside one of env's tile-resolution buckets so they never refill the tile cache mid-shot;
close-ups draw the set at half resolution (s5.SOFT_BG_ZOOM).
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
                            dress_anger, lit_pose, phrases, pick, pulse, render_world, scene_lights, sfx_time)
from config import H

# =========================================================================== timing (all from names)
T0, T1 = scene_span("s6")
S, E = line_start, line_end


def _ph(lid, i, default, gap=0.3):
    """Start of the i-th phrase of a line (lip-sync silences >= gap split phrases), or `default`."""
    p = phrases(lid, gap)
    return p[i][0] if -len(p) <= i < len(p) else default


N33 = S("n33")
DRIP1, DRIP2 = beat("drip1"), beat("drip2")
LAND1 = sfx_time("saliva_drip", DRIP1 - 0.05) + 0.02          # saliva_drip: the drop lands +0.02
LAND2 = sfx_time("saliva_drip", DRIP2 - 0.05) + 0.02
WAVE = beat("hand_wave")
N34, N34E = S("n34"), E("n34")
LAND3 = N34 + 1.75                                             # "Something warm... and WET..."
SIDE = beat("side_eye_open")
SEES = beat("sees_tongue")
STARTLED = beat("startled")                                    # startle_sting: hit on the beat, gasp +0.04..+0.35
A03, A03E = S("a03"), E("a03")
M04, M04E = S("m04"), E("m04")
M04_HI = _ph("m04", 1, M04 + 1.5)                              # "He's saying hi."
M04_LIKES = _ph("m04", 2, M04 + 3.1)                           # "I think he likes you."
LIKES_LAND = min(M04_LIKES + 0.55, M04E - 0.3)                 # plop on his head
N35, N36 = S("n35"), S("n36")
SHIFT = beat("shift_away")
SCRAPE2 = sfx_time("armor_scrape", SHIFT - 0.05)
SETTLE2 = SCRAPE2 + 0.62
A04, A04E = S("a04"), E("a04")
_P04 = phrases("a04", 0.3)
A04_PLEASE = _P04[-1][0] if len(_P04) > 1 else A04E - 0.7     # "...Please." after the long pause
A04_PAUSE = _P04[-2][1] if len(_P04) > 1 else A04_PLEASE - 1.0
MISS_LAND = lerp(A04_PAUSE, A04_PLEASE, 0.45)                  # plip: a drop just misses him in the pause
SASS = beat("sass")
HUFF = sfx_time("creature_huff", SASS - 0.05)                  # air blast peak +0.09
STOMPS = [s["start"] for s in timeline()["sfx"] if s["name"] == "stomp" and s["start"] >= SASS - 1e-6][:4]
N_STOMPS = len(STOMPS)
STOMP_DT = STOMPS[1] - STOMPS[0]                               # 0.7 s: one stomp cycle
STOMP_PH0 = STOMPS[0] - F.STOMP_HIT * STOMP_DT                 # phase 0 of the stomp cycles
M05, M05E = S("m05"), E("m05")
M05_RESPECT = _ph("m05", -2, M05 + 2.3)                        # "Treat him with some respect."
M05_BACK = _ph("m05", -1, M05 + 4.4)                           # "We go way back, okay?"
N37 = S("n37")
WIPE = beat("wipe_saliva")                                     # the hand comes up on the beat
AWK = beat("awkward")
TAP0 = sfx_time("foot_tap_heavy", AWK - 0.05)
TAPS = [TAP0 + k for k in range(5)]                            # foot_tap_heavy: taps exactly 0/1/2/3/4 s
TAP_PH0 = TAP0 - F.TAP_HIT                                     # phase 0 (1 s per tap)
A05, A05E = S("a05"), E("a05")
A05_WELL = _ph("a05", -2, A05 + 0.5)
A05_HOW = _ph("a05", -1, A05 + 2.0)
LAUGH = beat("laugh_start")
M06E = E("m06")
M07, M07E = S("m07"), E("m07")
M07_STUCK = _ph("m07", 1, M07 + 4.3)                           # "But now it seems you're stuck in here with us."
M07_HOW = _ph("m07", 2, M07 + 7.5)                             # "How do you feel about that?"
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

# =========================================================================== the friend: size, loom, retreat
FS = 0.7                               # 1600 * 0.7 = 1120 tall: ~1.37x Anger standing (820)
FY = 1120.0                            # its floor line (a little deeper than his: drawn behind him)
F_TURN = 0.15
LOOM_LEAN, LOOM_LD = 15.0, 0.32        # leaning over him (body lean, lean_down)
TIP_ABOVE = 170.0                      # the tongue tip hangs this far above his near cheek
FX1_TARGET = -640.0                    # where the four stomps leave it: well clear of his feet, by the dark


def _loom_q(x, tongue):
    q = Pose(x=x, y=FY, scale=FS, facing=1.0, turn=F_TURN, lean=LOOM_LEAN)
    q.extra = dict(expr="dumb_grin", tongue=tongue, lean_down=LOOM_LD)
    return q


@lru_cache(maxsize=1)
def loom_place():
    """(x, tongue) for the friend so its tongue tip hangs TIP_ABOVE over his near cheek (solved against the rig
    so a reshaped tongue still lands right)."""
    p = Pose(x=SIT_X, y=FLOOR, facing=-1.0, turn=0.3, arm_l=REST_NEAR, arm_r=REST_FAR)
    cheeks = []
    for st in ("sleep", "prop_sit"):
        p.extra = dict(state=st, sword=None, shield="back")
        cheeks.append(A.face_pos(p, 35.0, 17.0, 0.0))
    tx = 0.5 * (cheeks[0][0] + cheeks[1][0])
    ty = 0.5 * (cheeks[0][1] + cheeks[1][1]) - TIP_ABOVE
    best = None
    for x in range(120, 461, 10):
        for k in range(2, 51):
            tg = k / 50.0
            tp = F.tongue_tip(_loom_q(x, tg), 0.0)
            if tp is None:
                continue
            d = math.hypot(tp[0] - tx, tp[1] - ty) + 6.0 * tg
            if best is None or d < best[0]:
                best = (d, x, tg)
    _, x0, tg0 = best
    for x in [x0 + dx for dx in range(-9, 10, 3)]:
        for tg in [tg0 + dk / 100.0 for dk in range(-3, 4)]:
            if tg <= 0.01:
                continue
            tp = F.tongue_tip(_loom_q(x, tg), 0.0)
            if tp is None:
                continue
            d = math.hypot(tp[0] - tx, tp[1] - ty) + 6.0 * tg
            if d < best[0]:
                best = (d, x, tg)
    return float(best[1]), float(best[2])


FX0, TONGUE = loom_place()
STEP = (FX0 - FX1_TARGET) / (N_STOMPS * FS)       # local units per sassy stomp (rig default 60: these are big)


def _stomp_travel():
    q = Pose(x=FX0, y=FY, scale=FS, facing=1.0)
    q.extra = dict(legs="stomp", phase=float(N_STOMPS), stomp_step=STEP)
    return F.stomp_offset(q)


FX1 = FX0 + _stomp_travel()


# =========================================================================== the friend's performance
def _gig(t):
    """Giggle shoulder-bounce envelope synced to creature_giggle's pulses (0..1)."""
    v = 0.0
    for o in GIG_PULSES:
        v = max(v, pulse(t, GIGGLE + o - 0.03, 0.035, 0.07))
    return v


def _gig_end(t):
    """Silent leftover giggles for the end card."""
    v = 0.0
    for o in (1.6, 1.72, 1.85, 2.0, 3.6, 3.72, 3.86):
        v = max(v, pulse(t, END_CARD + o, 0.04, 0.08))
    return v


F_LEAN_DOWN = Track([(N36 + 1.0, LOOM_LD), (N36 + 1.6, 0.18, "io"), (SASS + 0.08, 0.18), (SASS + 0.55, 0.0, "io")])
F_LEAN = Track([(N36 + 1.0, LOOM_LEAN), (N36 + 1.6, 10.0, "io"), (SASS + 0.05, 10.0), (SASS + 0.55, 0.0, "io")])
F_TONGUE = Track([(N36 + 0.2, TONGUE), (N36 + 0.85, 0.0, "in")])
F_LOOK = Gaze([
    (T0, 0.15, 0.0),
    (SHIFT + 0.35, 0.3, 0.05, 0.12),
    (SASS + 0.1, 0.55, 0.15, 0.08),
    (STOMPS[-1] + 0.5, 0.75, 0.4, 0.15),        # from back there: at him (right, below)
    (M05 + 0.4, -0.75, 0.05, 0.1),              # its eyes go to the dark when the voice speaks for it
    (M05 + 1.4, 0.75, 0.4, 0.1),
    (LAUGH + 0.55, -0.9, 0.05, 0.12),           # between the dark and Anger
    (LAUGH + 2.3, 0.75, 0.4, 0.12),
    (LAUGH + 4.0, -0.9, 0.05, 0.12),
    (LAUGH + 5.5, 0.75, 0.4, 0.12),
    (LAUGH + 6.9, -0.85, 0.05, 0.12),
    (M07 + 0.4, 0.7, 0.38, 0.12),
])
F_HEAD_TURN = Track([(LAUGH + 0.5, 0.0), (LAUGH + 0.8, -0.16), (LAUGH + 2.25, -0.16), (LAUGH + 2.55, 0.1),
                     (LAUGH + 3.95, 0.1), (LAUGH + 4.25, -0.16), (LAUGH + 5.45, -0.16), (LAUGH + 5.75, 0.1),
                     (LAUGH + 6.85, 0.1), (LAUGH + 7.15, -0.14), (M07 + 0.35, -0.14), (M07 + 0.7, 0.06)])


def _expr_weights(t):
    """Blend dict of the friend's expression presets at t."""
    if t < N36 + 0.1:
        return {"dumb_grin": 1.0}
    if t < SASS:
        n = smoothstep((t - N36 - 0.1) / 0.5)                     # the grin falls...
        se = smoothstep((t - N36 - 1.2) / 0.6)                    # ...then the eyes narrow
        return {"dumb_grin": 1.0 - n, "neutral": n * (1.0 - se), "side_eye": n * se}
    if t < M05 + 1.5:
        hf = window(t, SASS, SASS + 0.75, 0.06, 0.35)
        return {"side_eye": 1.0 - 0.55 * hf, "huff": 0.55 * hf}
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
    ge = window(t, END_CARD + 1.4, END_CARD + 4.2, 0.3, 0.5)
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
    ce = window(t, END_CARD + 1.3, END_CARD + 4.3, 0.3, 0.5)
    cv = max(cv, ce)
    return {"rest": 1.0 - cv, "cover_mouth": cv} if cv < 1.0 else "cover_mouth"


def friend_pose(t) -> Pose:
    q = Pose(x=FX0, y=FY, scale=FS, facing=1.0, turn=F_TURN)
    q.lean = F_LEAN(t) + 0.8 * math.sin(2 * math.pi * 0.21 * t)
    ex = dict(tongue=F_TONGUE(t), lean_down=F_LEAN_DOWN(t), tongue_layer="skip", shadow=0.3)
    ex["expr"] = _expr_weights(t)
    ex["arms"] = _arms(t)
    # legs: stand / four stomps (the rig carries it back; planted feet stay put) / after the cut on J1 a normal
    # stance at the new spot, and the foot taps
    if t < STOMP_PH0:
        ex["legs"] = "stand"
    elif t < CUT_J1:
        ex["legs"] = "stomp"
        ex["phase"] = clamp((t - STOMP_PH0) / STOMP_DT, 0.0, float(N_STOMPS))
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
                  + 0.1 * window(t, M05_RESPECT + 0.2, WIPE, 0.4, 0.6)
                  + 0.12 * (pulse(t, M07_STUCK + 0.9, 0.12, 0.2) + pulse(t, M07_STUCK + 1.45, 0.12, 0.2))
                  - 0.08 * window(t, N36 + 1.0, SASS, 0.5, 0.2))           # offended: chin pulled in
    q.head_tilt = 4.0 * window(t, M04_HI, M04E + 0.5, 0.4, 0.6)
    q.head_turn = F_HEAD_TURN(t)
    q.smile = 0.25 * window(t, M07_STUCK + 0.6, M07_HOW, 0.4, 0.5)            # "stuck in here with us" :)
    lx, ly = F_LOOK(t)
    q.look_x, q.look_y = lx, ly
    q.extra = ex
    return q


@lru_cache(maxsize=None)
def _fhead(t):
    return F.head_center(friend_pose(t), t)


# =========================================================================== saliva drops
G_FALL = 2300.0                        # stage units / s^2
DROP_SIZE = 1.8


def tip_anchor(t):
    """Stage point the forming drop hangs from: under the end of the tongue."""
    q = friend_pose(t)
    tp = F.tongue_tip(q, t)
    if tp is None:
        return None
    return (tp[0], tp[1] + 22.0 * FS)


class Drop:
    """One drop: forms at the tongue from `form` (grows + stretches), detaches at `release`, falls with gravity
    and lands on target(t) exactly at `land` (then a small splat). source='above': it falls from SRC_ABOVE over
    its target (the close-up drops: the source is never seen) and only its fall is drawn."""

    SRC_ABOVE = 330.0

    def __init__(self, form, land, target, stretch_max=0.55, form_ease=1.0, source="tongue"):
        self.form, self.land, self.target = form, land, target
        self.smax = stretch_max
        self.form_ease = form_ease
        self.source = source
        tg = target(land)
        if source == "tongue":
            a = tip_anchor(land - 0.4)
            bulb = self._bulb(a, self.smax)
            dy = max(20.0, tg[1] - bulb[1])
        else:
            dy = self.SRC_ABOVE
        self.fall = math.sqrt(2.0 * dy / G_FALL)
        self.release = land - self.fall
        if source == "tongue":
            self.p0 = self._bulb(tip_anchor(self.release), self.smax)
        else:
            self.p0 = (tg[0], tg[1] - dy)

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
        if t < min(self.form, self.release) or t > self.land + 0.45:
            return
        if t < self.release:
            if self.source != "tongue":
                return
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
            if self.source == "tongue" and t - self.release < 0.12:
                a = tip_anchor(t)
                if a is not None:
                    k = 1.0 - (t - self.release) / 0.12
                    c.drawLine(a[0], a[1], a[0], a[1] + 34.0 * k, _line("#DDEFF2", 2.0, 0.6 * k * light))
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


# =========================================================================== cuts (needed by the poses)
CUT_B = LAND1 - 0.58
CUT_C = SEES - 0.06
CUT_E = A03 - 0.1
CUT_F = M04 - 0.1
CUT_G = M04_LIKES - 0.35
CUT_H = N36 - 0.15
CUT_I = SASS - 0.1
CUT_J1 = STOMPS[-1] + 0.6              # the friend's legs return to a normal stance on this cut
CUT_J2 = M05_RESPECT - 0.12
CUT_J3 = M05_BACK - 0.15
CUT_K = N37 - 0.1
CUT_M = TAPS[2] + 0.55
CUT_N = LAUGH - 0.08
CUT_O = LAUGH + 3.47
CUT_P = LAUGH + 6.47
CUT_Q = M07 - 0.1
CUT_Q2 = M07_STUCK - 0.12
CUT_Q3 = M07_HOW - 0.12
CUT_R = SNORT - 0.3
CUT_S = SMIRK - 0.13
SLIDE_BACK = CUT_M + 0.6               # awkward: his eyes slide back to it once...
SLIDE_AWAY = SLIDE_BACK + 0.75         # ...and away again


# =========================================================================== Anger's performance
AR = A.ARMS
NEAR_CHEEK = (35.0, 17.0)              # face_pos coords (x0 > 0 = his LEFT = the side nearer the camera)
BROW_SPOT = (17.0, -40.0)              # drip2: on the forehead above the near brow (-> the frown)
CHEEK_LOW = (30.0, 26.0)               # drip3
CROWN = (6.0, -64.0)


def look_dir(src, dst, k=0.95):
    """Gaze (look_x, look_y) from stage point src toward dst."""
    a = math.atan2(dst[1] - src[1], dst[0] - src[0])
    return k * math.cos(a), k * math.sin(a)


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
ROLL2 = WIPE - 0.48                    # the weary eye roll just before the wipe (n37)

ARM_NEAR = ArmSeq([(T0, REST_NEAR), (WAVE - 0.45, REST_NEAR), (WAVE - 0.08, SWAT_UP, "io"),
                   (WAVE + 0.1, SWAT_THRU, "out"), (WAVE + 0.45, SWAT_DROP, "io"), (WAVE + 1.0, REST_NEAR, "io"),
                   (STARTLED, REST_NEAR), (STARTLED + 0.12, JOLT_NEAR, "out"), (STARTLED + 0.9, REST_NEAR, "io"),
                   (WIPE, REST_NEAR), (WIPE + 0.28, WIPE_A, "io"), (WIPE + 0.62, WIPE_B, "io"),
                   (WIPE + 1.1, REST_NEAR, "io")])
ARM_FAR = ArmSeq([(T0, REST_FAR), (STARTLED, REST_FAR), (STARTLED + 0.14, JOLT_FAR, "out"),
                  (STARTLED + 1.0, REST_FAR, "io")])
CROSS = Track([(LAUGH + 1.75, 0.0), (LAUGH + 2.6, 1.0, "io")])

# ---- breathing (asleep: slow and deep; awake: normal); integrated from S5's start so it runs on seamlessly
_RATE6 = Track([(T0, 0.15), (STARTLED, 0.15), (STARTLED + 0.3, 0.26), (STARTLED + 4.0, 0.21)])
_AMP6 = Track([(T0, 1.45), (STARTLED, 1.45), (STARTLED + 0.3, 1.0), (STARTLED + 4.0, 0.95)])
BREATH = Breath(
    s5.T0, T1,
    rate=lambda t: s5.BREATH.rate(t) if t < T0 else _RATE6(t),
    amp=lambda t: s5.BREATH.amp(t) if t < T0 else _AMP6(t),
    override=Track([(STARTLED, 0.0), (STARTLED + 0.3, 1.4, "out"), (STARTLED + 1.4, 0.6),
                    (A04, 0.0), (A04 + 0.45, 1.0, "in"), (A04 + 1.0, 0.6),
                    (CLEAR, 0.3), (CLEAR + 0.18, -0.6), (CLEAR + 0.3, 0.2), (CLEAR + 0.42, -1.0, "out"),
                    (CLEAR + 0.9, 0.0)]),
    weight=Track([(STARTLED - 0.02, 0.0), (STARTLED + 0.05, 1.0), (STARTLED + 1.4, 1.0), (STARTLED + 2.4, 0.0),
                  (A04 - 0.2, 0.0), (A04 + 0.05, 1.0), (A04 + 1.0, 1.0), (A04 + 1.8, 0.0),
                  (CLEAR - 0.15, 0.0), (CLEAR + 0.02, 1.0), (CLEAR + 0.9, 1.0), (CLEAR + 1.5, 0.0)]),
    seed=s5.BREATH.seed,
)

# ---- eyes / face
LID = Track([(T0, 0.0), (SIDE, 0.0), (SIDE + 0.45, 0.42, "io"), (SEES + 0.32, 0.42), (SEES + 0.5, 0.58),
             (STARTLED, 0.58), (STARTLED + 0.06, 1.0, "out"), (STARTLED + 0.6, 1.0), (STARTLED + 1.15, 0.86),
             (LIKES_LAND + 0.25, 0.86), (LIKES_LAND + 0.45, 0.12, "io"), (LIKES_LAND + 0.8, 0.12),
             (SHIFT + 0.05, 0.62), (A04 + 0.6, 0.74), (A04_PAUSE + 0.15, 0.74), (A04_PAUSE + 0.35, 0.62),
             (A04_PLEASE, 0.64), (N36, 0.7), (SASS + 0.3, 0.8), (M05_BACK, 0.74), (M05_BACK + 0.5, 0.68),
             (ROLL2 + 0.3, 0.72), (WIPE + 0.24, 0.32), (WIPE + 0.66, 0.32), (WIPE + 0.95, 0.8), (A05, 0.8),
             (A05 + 0.3, 0.86), (LAUGH + 0.6, 0.86), (LAUGH + 1.9, 0.82), (M07, 0.82), (A06 - 0.4, 0.8),
             (A06, 0.68), (A06E + 0.4, 0.68), (SNORT + 0.4, 0.68), (SNORT + 0.55, 0.8), (SMIRK, 0.8),
             (SMIRK + 0.4, 0.78), (NOTICE, 0.78), (NOTICE + 0.08, 0.9, "out"), (SERIOUS, 0.86),
             (SERIOUS + 0.5, 0.9)])
ONE_EYE = Track([(T0, 0.0), (SIDE - 0.05, 0.0), (SIDE, 1.0, "step"), (STARTLED + 0.02, 1.0), (STARTLED + 0.1, 0.0)])
EYE_WIDE = Track([(STARTLED, 0.0), (STARTLED + 0.05, 1.0, "out"), (STARTLED + 0.55, 0.9), (STARTLED + 1.25, 0.0),
                  (SEES + 0.32, 0.0)])


def _gaze_keys():
    """Anger's eye-line. Directions toward the friend are computed from where it actually is."""
    head = (SIT_X + 40.0, 715.0)

    def to_friend(t, k=0.95):
        return look_dir(head, _fhead(round(t, 2)), k)

    keys = [
        (T0, 0.05, 0.45),
        (SIDE + 0.05, -0.32, -0.62, 0.35, "io"),     # exhausted, sideways, up
        (SEES + 0.18, -0.18, -0.92, 0.1),            # on the tongue / the drop
        (STARTLED + 0.03, *to_friend(STARTLED + 0.5), 0.06),     # up at the friend's face
        (STARTLED + 1.2, *to_friend(STARTLED + 1.5, 0.9), 0.1),
        (M04 + 0.3, -0.96, 0.04, 0.09),              # "That's my friend." -> the dark
        (M04_HI + 0.25, 0.3, -0.92, 0.1),            # the wave (its paw is up to his right)
        (M04_LIKES + 0.1, -0.14, -0.9, 0.08),        # the drop above
        (SHIFT + 0.3, *to_friend(SHIFT + 0.5, 0.88), 0.1),
        (SASS + 0.42, *to_friend(SASS + 0.6), 0.12),             # it straightens up
    ]
    for h in STOMPS:                                  # tracking it back
        keys.append((h - 0.05, *to_friend(h + 0.2), 0.3, "io"))
    keys += [
        (M05 + 0.3, -0.97, 0.02, 0.09),              # "Hey, he can hear you, buddy." -> the dark
        (M05 + 1.3, *to_friend(M05 + 1.3), 0.1),      # ...over at it
        (ROLL2 + 1.0, -0.3, 0.2, 0.25, "io"),
        (AWK + 0.35, 0.72, -0.22, 0.45, "io"),       # pretending not to notice (off into the distance)
        (SLIDE_BACK, *to_friend(SLIDE_BACK), 0.3, "io"),       # ...slides back once
        (SLIDE_AWAY, 0.74, -0.2, 0.38, "io"),        # ...and away again
        (A05_WELL - 0.15, *to_friend(A05_WELL), 0.1),          # "Well."
        (A05_HOW + 0.55, -0.96, 0.04, 0.08),         # "you guys" (the dark)
        (A05_HOW + 1.15, *to_friend(A05_HOW + 1.2), 0.08),
        (LAUGH + 0.22, -0.92, 0.04, 0.09),           # the laugh (the dark)
        (LAUGH + 5.3, -0.95, 0.07, 0.07),
        (M07 + 0.2, -0.9, 0.03, 0.07),
        (A06 - 0.3, -0.88, 0.06, 0.07),
        (SNORT + 0.42, *to_friend(SNORT + 0.5), 0.09),         # the snort (a beat late)
        (NOTICE, -0.15, 0.32, 0.07),                 # he notices: eyes flick down
        (NOTICE + 0.55, -0.55, 0.12, 0.09),
        (SERIOUS + 0.12, -0.62, -0.12, 0.12),        # heroic middle distance
    ]
    return keys


GAZE = None


def _gaze():
    global GAZE
    if GAZE is None:
        GAZE = Gaze(_gaze_keys())
    return GAZE


BLINKS = [STARTLED + 1.3, A03E + 0.15, M04 + 0.28, M04_HI + 0.22, A04 + 1.0, A04_PLEASE - 0.12, STOMPS[0] + 0.03,
          M05 + 0.27, M05_RESPECT + 0.33, M05_BACK + 0.9, AWK + 0.32, TAPS[1] + 0.5, SLIDE_AWAY + 0.9,
          A05_WELL - 0.18, A05_HOW + 0.52, LAUGH + 0.2, LAUGH + 4.0, LAUGH + 7.1, M07 + 2.6, M07_STUCK + 1.2,
          M07E + 0.5, A06E + 0.6, SNORT + 0.4, NOTICE + 0.62, SERIOUS + 1.35, SERIOUS + 3.6, END_CARD + 1.6,
          END_CARD + 3.9]

HEAD_NOD = Track([(T0, -0.05), (STARTLED, -0.05), (STARTLED + 0.4, 0.3, "out"), (STARTLED + 1.2, 0.22),
                  (M04 + 0.2, 0.22), (M04 + 0.5, 0.06), (M04_HI + 0.15, 0.06), (M04_HI + 0.45, 0.2), (SHIFT, 0.2),
                  (SHIFT + 0.5, 0.12), (A04, 0.14), (SASS + 0.3, 0.14), (SASS + 0.7, 0.2), (STOMPS[-1], 0.1),
                  (M05, 0.1), (M05 + 0.4, 0.04), (M05 + 1.2, 0.04), (M05 + 1.5, 0.08), (ROLL2, 0.08),
                  (WIPE + 0.5, 0.04), (AWK + 0.3, 0.04), (AWK + 0.8, 0.1), (A05, 0.1), (A05 + 0.4, 0.08),
                  (LAUGH + 0.2, 0.08), (LAUGH + 0.5, 0.0), (A06 - 0.3, 0.0), (A06 + 0.3, -0.04), (SNORT + 0.4, -0.04),
                  (SNORT + 0.7, 0.05), (NOTICE, 0.05), (NOTICE + 0.2, -0.02), (SERIOUS + 0.12, -0.02),
                  (SERIOUS + 0.95, 0.14, "io")])
HEAD_TURN = Track([(T0, -0.02), (STARTLED, -0.02), (STARTLED + 0.3, 0.08), (SHIFT + 0.1, 0.08), (SETTLE2, -0.04),
                   (SASS + 0.6, -0.04), (STOMPS[-1], 0.08), (AWK + 0.25, 0.08), (AWK + 0.9, -0.16, "io"),
                   (A05 - 0.05, -0.16), (A05 + 0.35, 0.08, "io"), (LAUGH + 0.2, 0.08), (LAUGH + 0.6, 0.12),
                   (SNORT + 0.4, 0.12), (SNORT + 0.7, 0.1), (SERIOUS + 0.1, 0.1), (SERIOUS + 0.9, 0.1)])
HEAD_TILT = Track([(T0, 0.0), (SHIFT + 0.08, 0.0), (SETTLE2, -5.0), (A04E + 0.4, -3.0), (WIPE + 0.15, -3.0),
                   (WIPE + 0.5, 2.0), (WIPE + 1.0, 0.0)])
BROW_FURROW = Track([(T0, 0.0), (LAND2 + 0.28, 0.0), (LAND2 + 0.55, 0.55, "out"), (WAVE + 0.6, 0.45),
                     (SIDE + 0.5, 0.3), (STARTLED, 0.3), (STARTLED + 0.1, 0.0), (STARTLED + 1.0, 0.0),
                     (STARTLED + 1.4, 0.28), (A03 + 0.3, 0.32), (M04, 0.25), (SHIFT, 0.3), (A04 + 0.3, 0.35),
                     (SASS, 0.3), (M05, 0.22), (AWK, 0.12), (A05, 0.18), (LAUGH, 0.15), (M07, 0.2),
                     (M07_STUCK + 0.4, 0.2), (M07_STUCK + 0.8, 0.32), (A06 - 0.5, 0.2), (A06, 0.1),
                     (SMIRK - 0.3, 0.05), (SMIRK + 0.1, 0.0), (NOTICE + 0.1, 0.0), (NOTICE + 0.3, 0.28),
                     (SERIOUS + 0.3, 0.32)])
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
    p.bounce = (-11.0 * jolt + 2.5 * stomp_b - 3.0 * pulse(t, SETTLE2, 0.04, 0.12)
                - 3.0 * pulse(t, CLEAR + 0.38, 0.04, 0.1))
    hh = pulse(t, CLEAR + 0.02, 0.14, 0.12)
    hm = pulse(t, CLEAR + 0.37, 0.05, 0.13)
    p.shoulders_up = 0.6 * jolt + 0.22 * hh + 0.32 * hm
    # ---- face
    lx, ly = _gaze()(t)
    # the weary eye roll before the wipe: up and around to the right
    u = (t - ROLL2) / 0.48
    if 0.0 < u < 1.6:
        a = math.pi * (0.78 - 0.95 * ease_in_out(min(1.0, u)))
        rx, ry = 0.85 * math.cos(a), -0.97 * math.sin(a)
        w = smoothstep(u / 0.15) * (1.0 - smoothstep((u - 1.0) / 0.6))
        lx, ly = lerp(lx, rx, w), lerp(ly, ry, w)
    p.look_x, p.look_y = lx, ly
    lid = LID(t) * blinks(t, BLINKS)
    p.lid_l = p.lid_r = lid
    tw1 = pulse(t, LAND1 + 0.28, 0.05, 0.16)          # drip1: a tiny twitch of the closed lids
    tw2 = pulse(t, LAND2 + 0.3, 0.06, 0.25)           # drip2: the frown (BROW_FURROW) + lips pressed
    tw3 = pulse(t, LAND3 + 0.3, 0.07, 0.3)            # drip3: a scrunch
    p.squint = clamp(SQUINT(t) + 0.55 * tw1 + 0.3 * tw2 + 0.5 * tw3)
    p.eye_wide = EYE_WIDE(t)
    p.pupil = 1.0 - 0.18 * window(t, SEES + 0.3, STARTLED + 1.0, 0.25, 0.5)
    p.head_nod = HEAD_NOD(t) + 0.28 * jolt - 0.1 * hh - 0.14 * hm
    p.head_turn = HEAD_TURN(t)
    p.head_tilt = (HEAD_TILT(t) - 1.6 * tw1 - 1.2 * tw2 - 2.0 * tw3
                   + 2.5 * window(t, WAVE - 0.3, WAVE + 0.6, 0.2, 0.4))
    p.brow_raise = 0.85 * pulse(t, STARTLED + 0.02, 0.05, 0.45) + 0.1 * window(t, SIDE, STARTLED, 0.4, 0.05)
    p.brow_furrow = BROW_FURROW(t) + 0.15 * tw1 + 0.25 * tw3
    p.brow_worry = 0.12 * window(t, SIDE, STARTLED, 0.4, 0.05)
    mo, mr = mouth("anger", t)
    gasp = window(t, STARTLED + 0.04, STARTLED + 0.35, 0.05, 0.15)
    mo = max(mo, 0.36 * gasp)
    mr = max(mr, 0.4 * gasp)
    mo = max(mo, 0.06 * pulse(t, CLEAR + 0.02, 0.12, 0.1))         # "hhrr" (the "HM" is mouth-closed)
    p.mouth_open, p.mouth_round = mo, mr
    p.smile = (-0.18 * tw2 - 0.15 * tw3 - 0.1 * window(t, LAND2 + 0.3, SIDE + 0.5, 0.2, 0.6)
               - 0.06 * window(t, SERIOUS, T1, 0.4, 0.1))
    p.smirk = SMIRK_T(t)                            # the rig warms the whole face for it (brows relax, cheeks lift)
    rb = RAISED(t)
    p.extra = dict(state="prop_sit", state_b="sleep", mix=mix, sword=None, shield="back", bruised=1.0,
                   one_eye=ONE_EYE(t), knee_up=0.55, rim_dir=-105.0, cross_arms=CROSS(t),
                   brow_l=1.0 * rb, brow_r=-0.3 * rb, smirk_suppress=SUPPRESS(t))
    return p


# =========================================================================== drops (positions + timing)
def _face_pt(spot):
    return lambda t: A.face_pos(anger_pose(t), spot[0], spot[1], t)


def _lap_pt(t):
    q = anger_pose(t)
    hc = A.head_center(q, t)
    a = tip_anchor(t)
    return ((a[0] if a else hc[0] - 40.0), hc[1] + 285.0)


DROPS = []


def _make_drops():
    if not DROPS:
        DROPS.extend([
            Drop(LAND1 - 1.0, LAND1, _face_pt(NEAR_CHEEK), source="above"),
            Drop(LAND2 - 1.0, LAND2, _face_pt(BROW_SPOT), source="above"),
            Drop(LAND3 - 1.0, LAND3, _face_pt(CHEEK_LOW), source="above"),
            Drop(SEES - 0.6, LIKES_LAND, _face_pt(CROWN), stretch_max=0.6, form_ease=0.55),
            Drop(A04 + 0.4, MISS_LAND, _lap_pt, stretch_max=0.5),
        ])
    return DROPS


def wet_spots(c, t, light=1.0):
    """Saliva left on him: cheek (drip1, drip3), forehead (drip2), crown (the plop) - gone when he wipes."""
    if t >= WIPE + 0.62:
        return
    q = anger_pose(t)
    fade = 1.0 - smoothstep((t - WIPE - 0.32) / 0.26)
    for land, spot, sz in ((LAND1, NEAR_CHEEK, 1.0), (LAND2, BROW_SPOT, 0.85), (LAND3, CHEEK_LOW, 0.9),
                           (LIKES_LAND, CROWN, 1.25)):
        if t < land:
            continue
        age = t - land
        x, y = A.face_pos(q, spot[0], spot[1], t)
        a = 0.8 * fade * light
        spread = smoothstep(age / 0.12)
        r = 5.2 * sz * (0.6 + 0.4 * spread)
        c.drawOval(skia.Rect(x - r * 1.35, y - r * 0.75, x + r * 1.35, y + r * 0.75), _fill("#CFE6EA", 0.5 * a))
        c.drawCircle(x - r * 0.5, y - r * 0.2, r * 0.3, _fill("#FFFFFF", 0.85 * a))
        for dx0, dy0 in ((-2.1, -0.9), (1.9, 0.6)):           # two tiny satellite droplets from the splat
            qx, qy = A.face_pos(q, spot[0] + dx0 * 5.0 * sz, spot[1] + dy0 * 5.0 * sz, t)
            c.drawCircle(qx, qy, 1.4 * sz * spread, _fill("#E8F6F8", 0.8 * a))


# =========================================================================== shots / cameras
@lru_cache(maxsize=None)
def _face(t):
    return A.head_center(anger_pose(t), t)


@lru_cache(maxsize=None)
def _cheek(t):
    return A.face_pos(anger_pose(t), NEAR_CHEEK[0], NEAR_CHEEK[1], t)


def _cu_sleep(t=None):
    return cam_at(_cheek(round(LAND1, 2)), 3.3, 372.0, 615.0)


def _cam_a(t):
    """S5's closing medium-wide, creeping in (zoom kept inside one env tile bucket, (1.19, 1.41])."""
    a = s5.cam_f()
    f = _face(round(T0, 2))
    b = cam_at(f, 1.4, *a.to_screen(*f))
    return drift(a, b, t, T0, CUT_B + 0.4, ease=lambda x: smoothstep(x) * 0.5 + x * 0.5)


def _cam_c(t):
    """Low close: his face low in frame, the tongue hanging into it from above (its mouth stays out of frame)."""
    return cam_at(_face(round(SEES, 2)), 3.0, 392.0, 905.0)


def _fit(pts, margin=(130.0, 150.0), zmax=2.0, sy_bias=0.0):
    """Camera that frames all stage points pts with screen margins (px)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    z = min(zmax, (720.0 - 2 * margin[0]) / max(w, 1.0), (1280.0 - 2 * margin[1]) / max(h, 1.0))
    return Camera(0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)) + sy_bias / z, z)


def _cam_d(t):
    """The reveal: the friend leaning over him (its head and his face, its feet, his legs)."""
    fh = _fhead(round(STARTLED + 0.5, 2))
    f = _face(round(STARTLED + 0.5, 2))
    return _fit([fh, (fh[0], fh[1] - 300.0 * FS), f, (FX0 - 420.0 * FS, FY), (SIT_X + 160.0, FLOOR)],
                margin=(40.0, 170.0), sy_bias=60.0)


def _cam_e(t):
    return cam_at(_face(round(A03 + 0.6, 2)), 1.6, 410.0, 700.0)


def _cam_f(t):
    """The friend and its little wave (the waving paw is out to the right of its head)."""
    tw = M04_HI + 0.6
    q = friend_pose(tw)
    fh = _fhead(round(tw, 2))
    paw = F.hand_pos(q, "l", tw)
    f = _face(round(tw, 2))
    return _fit([fh, (fh[0], fh[1] - 260.0 * FS), paw, f], margin=(70.0, 260.0), zmax=1.3)


def _cam_g(t):
    f = _face(round(A04 + 1.0, 2))
    fh = _fhead(round(A04 + 1.0, 2))
    return _fit([f, (f[0], f[1] + 200.0), fh], margin=(150.0, 210.0), zmax=1.4, sy_bias=-40.0)


def _cam_h(t):
    return cam_at(_fhead(round(N36 + 1.0, 2)), 1.45, 360.0, 560.0)


def distance_wide(t=None):
    """The friend back by the dark, Anger by the wall: the whole width between them."""
    fh = _fhead(round(AWK + 1.0, 2))
    f = _face(round(AWK + 1.0, 2))
    return _fit([(FX1 - 430.0 * FS, FY + 10.0), (fh[0], fh[1] - 330.0 * FS), (SIT_X + 170.0, FLOOR + 10.0), f],
                margin=(14.0, 230.0), zmax=0.9, sy_bias=-60.0)


def _cam_j1(t):
    return cam_at(_face(round(M05 + 1.0, 2)), 1.55, 455.0, 560.0)


def _friend_far(t0):
    return cam_at(_fhead(round(t0, 2)), 1.0, 360.0, 480.0)


def _cam_k(t):
    return cam_at(_face(round(WIPE, 2)), 2.3, 372.0, 540.0)


def _cam_m(t):
    return cam_at(_face(round(A05, 2)), 1.55, 455.0, 560.0)


def _cam_n(t):
    return cam_at(_face(round(LAUGH + 2.5, 2)), 1.9, 400.0, 520.0)


def _cam_p(t):
    return cam_at(_face(round(LAUGH + 7.0, 2)), 2.36, 380.0, 530.0)


def _cam_q(t):
    f = _face(round(M07 + 2.0, 2))
    a = cam_at(f, 2.03, 400.0, 552.0)            # slow creep inside one env tile bucket (2.0, 2.38]
    b = cam_at(f, 2.2, 390.0, 540.0)
    return drift(a, b, t, CUT_Q, CUT_Q2, ease=lambda x: 0.6 * smoothstep(x) + 0.4 * x)


def _cam_q3(t):
    return cam_at(_face(round(A06, 2)), 2.37, 380.0, 532.0)


def _cam_r(t):
    return cam_at(_fhead(round(GIGGLE + 0.5, 2)), 1.0, 360.0, 520.0)


def _cam_s(t):
    f = _face(round(SMIRK + 0.5, 2))
    return cam_at((f[0], f[1] + 22.0), 3.0, 372.0, 560.0)


def _cam_t(t):
    f = _face(round(SERIOUS + 1.0, 2))
    a = cam_at(f, 1.43, 400.0, 470.0)
    b = cam_at(f, 1.55, 400.0, 470.0)
    c = drift(a, b, t, SERIOUS, END_CARD, ease=lambda x: x)
    return Camera(c.cx, c.cy, c.zoom, 1.6, 0.0)


def _cam_u(t):
    a = distance_wide()
    b = Camera(a.cx, a.cy - 40.0, a.zoom * 0.95)
    return drift(a, b, t, END_CARD, T1, ease=lambda x: x)


SHOTS = [
    (T0, _cam_a),
    (CUT_B, _cu_sleep),
    (CUT_C, _cam_c),
    (STARTLED, _cam_d),
    (CUT_E, _cam_e),
    (CUT_F, _cam_f),
    (CUT_G, _cam_g),
    (CUT_H, _cam_h),
    (CUT_I, distance_wide),
    (CUT_J1, _cam_j1),
    (CUT_J2, distance_wide),
    (CUT_J3, lambda t: _friend_far(M05_BACK + 0.5)),
    (CUT_K, _cam_k),
    (AWK, distance_wide),
    (CUT_M, _cam_m),
    (CUT_N, _cam_n),
    (CUT_O, distance_wide),
    (CUT_P, _cam_p),
    (CUT_Q, _cam_q),
    (CUT_Q2, lambda t: _friend_far(M07_STUCK + 1.0)),
    (CUT_Q3, _cam_q3),
    (CUT_R, _cam_r),
    (CUT_S, _cam_s),
    (SERIOUS, _cam_t),
    (END_CARD, _cam_u),
]


def camera(t):
    cam = pick(SHOTS, t)
    ev = [(STARTLED + 0.01, 7.0, 0.45)] + [(h, 18.0, 0.6) for h in STOMPS] + [(h, 3.0, 0.25) for h in TAPS]
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
    f_key = Light(fh[0], fh[1] + 60.0, 680.0 * FS, 0.28 * (1.0 - 0.85 * end_k), "#A2B6DA", "point")
    f_low = Light(q.x + 120.0 * FS, FY - 150.0, 700.0 * FS, 0.18 * (1.0 - 0.85 * end_k), "#8FA6D0", "point")
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
            for k, (x0, x1) in enumerate(((-900.0, -420.0), (-300.0, 60.0), (160.0, 520.0), (600.0, 900.0))):
                fx.dust_fall(c, t, x0, x1, top, amount=grit, seed=70 + k, length=1900.0, size=2.6)
        for d in drops:
            d.draw(c, t)
        if STOMPS[0] - 0.1 <= t < CUT_J1 + 2.2:
            for i, h in enumerate(STOMPS):
                age = t - h
                if 0.0 <= age < 2.2:
                    side = "l" if i % 2 == 0 else "r"
                    fp = F.foot_pos(friend_pose(h), side, h)
                    fx.dust_cloud(c, t, fp[0], FY + 6.0, age, size=1.0, seed=40 + i, n=12, alpha=0.6, life=2.0)

    render_world(canvas, t, cam, anger=p, friend=q, friend_mod=F, lit_fx=lit_fx, amb=amb, lights=lights,
                 dust=0.12, grit=grit, friend_body=show_body, friend_tongue=show_tongue)
    if t >= END_CARD:
        a = smoothstep((t - END_CARD - 0.25) / 1.1)
        fx.draw_title(canvas, t, "ANGER", alpha=a, cy=0.5 * H)
        fade_overlay(canvas, smoothstep((t - (T1 - 1.0)) / 1.0))


# =========================================================================== sfx
def sfx_events():
    """Motion-locked sounds not in the timeline: Anger's plate shifts and the extra drops."""
    ev = [
        ("armor_shift", WAVE - 0.38, -21.0),                 # the sleepy swat
        ("armor_shift", WAVE + 0.75, -22.0),                 # ...the arm flops back
        ("saliva_drip", LAND3 - 0.02, -12.0),                # drip3 ("...and wet...")
        ("armor_shift", STARTLED + 0.03, -15.0),             # the jolt
        ("saliva_drip", LIKES_LAND - 0.02, -13.0),           # plop on his head
        ("saliva_drip", MISS_LAND - 0.02, -16.0),            # plip (just misses him)
        ("armor_shift", WIPE + 0.02, -18.0),                 # the wipe
        ("armor_shift", LAUGH + 1.78, -17.0),                # crosses his arms
        ("armor_shift", CLEAR + 0.36, -22.0),                # the "HM" chest pump
    ]
    return [{"name": n, "start": round(s, 3), "gain_db": g} for n, s, g in ev]
