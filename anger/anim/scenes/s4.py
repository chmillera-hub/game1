"""S4 - The depths (BIBLE section 4 S4, section 9 handoffs S3->S4 and S4->S5).

render(canvas, t) is a pure function of the absolute time t; every time comes from a named beat, a line or an
SFX placement (+ the hit offsets in build/sfx_timing_notes.md). Set: env.draw_depths (wall face on the RIGHT at
WALL_X, the deep shadow on screen-left = the hermit). Anger lies where S3 left him: on his back, facing -1, head
toward the right wall (pelvis at s3.LIE_X), his sword stuck in the wall above him (s3.draw_stuck_sword).

Staging of the monster: it creeps in BEHIND him (floor y 1110: its head and jaws above his face, the drool
falls onto his armour), lunges; the thrown rock clonks it mid-lunge and it drops KO in FRONT of him (floor
y 1215: its head by his shoulder, its tail stretched to the left into the dark) - the glove grabs that tail.

Shot list (absolute times only for orientation):
  1  s4 start -> groan-0.1       WIDE (continues S3's last framing): dazed, blurred, doubled vision; push in
  2  -> assess+0.65              CLOSE-UP: the groan (mm / uh / effort / creaky) with the blur clearing
  3  -> assess+2.1               INSERT: his gauntlet on the gravel - the fingers twitch
  4  -> assess+4.0               CLOSE-UP: a wince; his eyes go around the dark
  5  -> eyes_again+1.6           POV pan across the grotto: shadows ... the glowing eyes; the scurry
  6  -> wake_noise               CLOSE-UP: eyes track it; pass_out: the lids close, the frame dims (not black)
  7  -> wake_noise+0.6           INSERT: pebbles shift in the dark
  8  -> one_arm                  CLOSE-UP: the eyes open
  9  -> monster_approach         MEDIUM: he tries to rise - only one arm moves
  10 -> monster_approach+1.6     POV into the dark: four eyes approach (front creep), the growl
  11 -> arm_up-0.1               CLOSE-UP: eye-line on it, the jaw sets
  12 -> monster_reveal           MEDIUM two-shot: it creeps in behind him; he raises his one arm, weakly
  13 -> drool_drip-0.1           POV CLOSE-UP: the head looms, the jaw opens on the hiss
  14 -> monster_lunge            CLOSE-UP: the drool drop lands by his face; minimal flinch; stoic
  15 -> one_eye_open             MEDIUM two-shot: lunge - the rock from screen-left - CLONK - KO, rock bounces
  16 -> m01                      CLOSE-UP: ONE eye opens: the monster out cold next to him; eye darts
  17 -> hermit_start+0.1         MEDIUM-WIDE: m01 from the dark at screen-left; his eye goes to the voice
  18 -> glove_grab-0.25          CLOSE-UP: m02; the eye flicks to the monster and back
  19 -> crunch-0.1               WIDE: the glove reaches out of the dark, grabs the tail, drags it away
  20 -> crunch+0.65              MEDIUM-WIDE: crunching from the dark (specks)
  21 -> s4 end                   CLOSE-UP: no idea how to react - tiny winces on the bone snaps, a slow blink,
                                 the ceiling; ends looking toward the dark, one eye open
"""
from __future__ import annotations

import math

import skia

from anim import char_anger as A
from anim import char_crawler as C
from anim import env, fx, light
from anim.core import (Camera, Layer, beat, clamp, ease_in, ease_in_out, ease_out, fade_overlay, hash01, lerp,
                       light_filter, line_end, line_start, noise1, paint, scene_span, smoothstep)
from anim.light import Light
from anim.rig import ArmPose, Pose
from anim.scenes import s3
from anim.scenes.s3 import FILL_COLD, cam_mix, cam_on_rot, dress, face_life, finish, sfx_time
from config import H, W

AR = A.ARMS
T0, T1 = scene_span("s4")

# =========================================================================== timing (all from names)
DAZED = beat("dazed")
ASSESS = beat("assess")
EYES_AGAIN = beat("eyes_again")
PASS_OUT = beat("pass_out")
WAKE = beat("wake_noise")
ONE_ARM = beat("one_arm")
APPROACH = beat("monster_approach")
ARM_UP = beat("arm_up")
REVEAL = beat("monster_reveal")
LUNGE = beat("monster_lunge")
ROCK_HIT = beat("rock_hit")
ONE_EYE = beat("one_eye_open")
HERMIT = beat("hermit_start")
GLOVE = beat("glove_grab")
CRUNCH = beat("crunch")
CRUNCH_END = beat("crunch_end")
M01, M01E = line_start("m01"), line_end("m01")
M02, M02E = line_start("m02"), line_end("m02")
GROAN = sfx_time("anger_groan", T0)          # mm until +0.15, "uh" 0.2-1.7, effort 0.35-0.45, creaky 1.4-1.95
SCURRY = sfx_time("scurry", T0)
PEBBLES = sfx_time("pebbles_shift", T0)
GROWL = sfx_time("monster_growl", T0)        # phrases +0.1-1.7 and +1.95-4.05
HISS = sfx_time("monster_hiss", T0)          # the jaw opens ON it
DROOL = sfx_time("drool_drip", T0)
DROOL_LAND = DROOL + 0.40
WHOOSH = sfx_time("rock_whoosh", T0)
BONK = sfx_time("rock_bonk", T0)
ROCK_B1, ROCK_B2, ROCK_REST = BONK + 0.42, BONK + 0.62, BONK + 0.95
THUD = sfx_time("body_thud", T0)
FLOP = THUD + 0.13
GRIP_CLOSE = sfx_time("tail_grab", T0) + 0.08
_DR = sfx_time("drag", T0)
TUGS = [_DR, _DR + 0.62, _DR + 1.20]
_CR = sfx_time("crunching", T0)
CHOMPS = [_CR + d for d in (0.0, 0.38, 0.75, 1.15, 1.52, 1.95, 2.33, 2.75)]
SNAPS = [CHOMPS[0], CHOMPS[2], CHOMPS[4]]
SLURP, GULP = _CR + 2.95, _CR + 3.30

# ---------------------------------------------------------------- cuts
CUT2 = GROAN - 0.1
CUT3 = ASSESS + 0.65
CUT4 = ASSESS + 2.1
CUT5 = ASSESS + 4.0
CUT6 = EYES_AGAIN + 1.6
CUT7 = WAKE
CUT8 = WAKE + 0.6
CUT9 = ONE_ARM
CUT10 = APPROACH
CUT11 = APPROACH + 1.6
CUT12 = ARM_UP - 0.1
CUT13 = REVEAL
CUT14 = DROOL - 0.1
CUT15 = LUNGE
CUT16 = ONE_EYE
CUT17 = M01
CUT18 = HERMIT + 0.1
CUT19 = GLOVE - 0.25
CUT19B = TUGS[0] + 0.3
CUT20 = CRUNCH - 0.1
CUT21 = CRUNCH + 0.65

# =========================================================================== geometry
LIE_X, LIE_Y = s3.LIE_X, s3.LIE_Y
CR_S = 0.9                        # crawler scale
BACK_Y = 1110.0                   # crawler floor behind him
FRONT_Y = 1215.0                  # crawler floor in front of him
X_SNARL = 108.0                   # crawler (side) while it snarls over him
X_APP0 = -240.0                   # where it is when it comes out of the dark (side view)
X_KO = 190.0                      # where it lies KO
LUNGE_HIT = 0.42                  # lunge phase at the clonk


def _pose(**kw):
    ex = kw.pop("extra", {})
    p = Pose(**kw)
    p.extra = dict(ex)
    return p


def _pulse(t, t0, rise, hold, fall):
    """0 -> 1 -> 0 envelope."""
    if t < t0:
        return 0.0
    a = t - t0
    if a < rise:
        return smoothstep(a / rise)
    a -= rise
    if a < hold:
        return 1.0
    a -= hold
    return 1.0 - smoothstep(a / fall)


def _sacc(t, keys):
    """Saccade track: keys = [(t, value)], a quick move (0.09 s) at each key, then hold."""
    v = keys[0][1]
    for i in range(1, len(keys)):
        tk, vk = keys[i]
        if t >= tk:
            v0 = keys[i - 1][1]
            u = ease_out(clamp((t - tk) / 0.09))
            v = tuple(a + (b - a) * u for a, b in zip(v0, vk)) if isinstance(vk, tuple) else lerp(v0, vk, u)
    return v


# =========================================================================== Anger
def _groan_mouth(t):
    """(mouth_open, extra effort 0..1, creak 0..1) for the anger_groan SFX."""
    a = t - GROAN
    if a < 0 or a > 2.1:
        return 0.0, 0.0, 0.0
    if a < 0.18:                              # "mm": lips pressed, effort building
        return 0.0, 0.35 * smoothstep(a / 0.15), 0.0
    op = 0.38 * smoothstep((a - 0.18) / 0.12)
    eff = 0.35 + 0.65 * _pulse(a, 0.3, 0.06, 0.12, 0.35)
    op += 0.14 * _pulse(a, 0.3, 0.06, 0.12, 0.4)
    creak = smoothstep((a - 1.35) / 0.15) * (1 - smoothstep((a - 1.9) / 0.15))
    op *= 1.0 - 0.6 * smoothstep((a - 1.35) / 0.3)
    op *= 1.0 - smoothstep((a - 1.85) / 0.2)
    eff *= 1.0 - smoothstep((a - 1.6) / 0.4)
    return op, eff, creak


def _look_track(t):
    """Gaze (look_x, look_y) over the whole scene (screen directions: -x = the dark on the left, -y = up)."""
    keys = [(T0, (0.0, -0.2)),
            (ASSESS + 2.35, (0.0, -0.9)),            # up the shaft
            (ASSESS + 2.95, (-0.7, -0.4)),            # the dark left
            (ASSESS + 3.55, (0.5, -0.6)),             # the wall
            (ASSESS + 4.1, (-0.9, 0.0)),              # (POV) ... back to the dark
            (EYES_AGAIN + 1.65, (-0.95, -0.15)),      # tracking where it went
            (EYES_AGAIN + 2.3, (-0.6, -0.5)),
            (PASS_OUT + 0.4, (-0.2, -0.3)),
            (WAKE + 0.95, (-0.9, -0.1)),              # eyes open, find the noise
            (WAKE + 1.5, (-0.3, -0.7)),
            (ONE_ARM + 0.2, (0.2, -0.4)),             # tries to move: looks at his own arm
            (ONE_ARM + 0.9, (-0.4, 0.1)),
            (APPROACH + 1.75, (-1.0, -0.2)),          # it is coming (from the left)
            (ARM_UP + 0.3, (-0.7, -0.6)),
            (REVEAL + 0.15, (-0.5, -1.0)),            # the jaws above him
            (DROOL_LAND + 0.3, (-0.6, -0.8)),
            (ONE_EYE + 0.5, (-0.75, 0.25)),           # the monster, out cold, next to him
            (ONE_EYE + 1.05, (-1.0, -0.2)),           # ... the dark
            (ONE_EYE + 1.55, (-0.75, 0.25)),          # ... the monster
            (M01 + 0.35, (-1.0, -0.05)),              # the voice
            (M02 + 0.95, (-0.7, 0.3)),                # "MY lunch": the monster
            (M02 + 1.6, (-1.0, -0.05)),               # back to the voice
            (GLOVE + 0.15, (-0.85, 0.25)),            # the glove / the monster sliding away
            (TUGS[2] + 0.2, (-1.0, 0.1)),
            (CHOMPS[3], (-0.5, -0.6)),                # the ceiling
            (GULP + 0.2, (-0.3, -0.85)),
            (CRUNCH_END + 0.15, (-0.95, -0.1))]       # toward the dark
    return _sacc(t, keys)


def anger_pose(t):
    """Anger's whole S4 performance (depths coords)."""
    # ---- body state: crumpled -> (tries to move) -> lie_back
    mix = smoothstep((t - (ONE_ARM + 0.15)) / 1.0)
    base = "crumpled"
    # ---- the near (left) arm: twitching fingers, the one-arm try, the weak raise, the sinking
    arm_l = ArmPose(shoulder=-6.0, elbow=22.0, wrist=0.0, hand="relaxed")
    arm_r = ArmPose(shoulder=4.0, elbow=18.0, wrist=10.0, hand="relaxed")
    hand = "relaxed"
    for k, tw in enumerate((ASSESS + 0.85, ASSESS + 1.25, ASSESS + 1.55, ASSESS + 1.8)):
        if tw <= t < tw + (0.16 if k != 2 else 0.3):
            hand = ("claw", "open", "claw", "relaxed")[k]
    arm_l = ArmPose(arm_l.shoulder + 4.0 * _pulse(t, ASSESS + 1.5, 0.15, 0.2, 0.3), arm_l.elbow, arm_l.wrist
                    + 8.0 * _pulse(t, ASSESS + 0.85, 0.08, 0.1, 0.2), hand)
    try_ = _pulse(t, ONE_ARM + 0.3, 0.45, 0.25, 0.5)
    arm_l = ArmPose.blend(arm_l, ArmPose(shoulder=40.0, elbow=60.0, wrist=6.0, hand="claw"), 0.8 * try_)
    raise_ = smoothstep((t - ARM_UP) / 0.75) * (1.0 - smoothstep((t - (FLOP + 0.25)) / 0.9))
    trem = 3.0 * noise1(t * 9.0, 301) + 2.0 * noise1(t * 3.1, 302)
    wr = ArmPose(shoulder=AR["weak_raise"].shoulder + trem, elbow=AR["weak_raise"].elbow + trem * 0.6,
                 wrist=AR["weak_raise"].wrist, hand="claw")
    arm_l = ArmPose.blend(arm_l, wr, raise_)
    ex = dict(state=base, state_b="lie_back", mix=mix, arms_w=0.0, sword=None, shield="back", bruised=1.0)
    # ---- face
    gx, gy = _look_track(t)
    lx, ly, br = face_life(t, 41)
    dz = 1.0 - smoothstep((t - (ASSESS + 1.8)) / 3.5)
    dz = max(dz, 0.6 * _pulse(t, PASS_OUT - 0.2, 0.8, 3.0, 1.5))
    dz *= 1.0 - smoothstep((t - APPROACH) / 1.0) * 0.85
    lid = lerp(0.55, 0.85, smoothstep((t - (ASSESS + 1.9)) / 1.5))
    # pass out: slow close ... wake: open with a flutter
    po = ease_in_out(clamp((t - (PASS_OUT + 0.15)) / 1.3))
    wk = smoothstep((t - (WAKE + 0.35)) / 0.45)
    flutter = 0.25 * _pulse(t, WAKE + 0.55, 0.05, 0.05, 0.12)
    closed = po * (1 - wk)
    lid = lid * (1 - closed) - flutter * wk * (1 - closed)
    # the groan
    mo, eff, creak = _groan_mouth(t)
    # wince when he tries to move (assess) and on the one-arm try
    wince = _pulse(t, ASSESS + 2.15, 0.12, 0.25, 0.5) + 0.8 * _pulse(t, ONE_ARM + 0.45, 0.15, 0.3, 0.5)
    # approach: jaw set, breath shallow; drool flinch; brace for the bite (eyes shut)
    tense = smoothstep((t - (APPROACH + 1.7)) / 0.5) * (1 - smoothstep((t - ONE_EYE) / 0.6))
    flinch = _pulse(t, DROOL_LAND + 0.06, 0.05, 0.08, 0.25)
    resign = _pulse(t, LUNGE - 0.75, 0.25, 0.1, 0.35)          # one slow blink before it lunges
    shut = smoothstep((t - (LUNGE + 0.04)) / 0.1) * (1 - smoothstep((t - (ONE_EYE + 0.05)) / 0.35))
    squeeze = shut * (0.55 + 0.25 * _pulse(t, BONK + 0.04, 0.04, 0.1, 0.3)) * (1 - smoothstep((t - (FLOP + 0.6))
                                                                                                 / 0.8) * 0.7)
    one = smoothstep((t - (ONE_EYE + 0.03)) / 0.3)
    # crunch: tiny winces on the bone snaps, a slow blink
    snap = sum(_pulse(t, s_ + 0.1, 0.04, 0.06, 0.2) for s_ in SNAPS)
    slow_blink = _pulse(t, CHOMPS[5] - 0.05, 0.25, 0.12, 0.35)
    slurp = _pulse(t, SLURP + 0.12, 0.15, 0.3, 0.4)
    gulp = _pulse(t, GULP + 0.1, 0.1, 0.2, 0.3)

    bl = A.blink(t)
    lid_v = lid * bl * (1 - 0.7 * resign) * (1 - shut) * (1 - 0.55 * flinch) * (1 - 0.8 * slow_blink)
    lid_v *= 1.0 - 0.35 * snap - 0.12 * gulp
    lid_v = max(lid_v, 0.0)
    if one > 0:      # only the near eye: open to a wary slit-and-a-half
        lid_v = max(lid_v, one * 0.72 * bl * (1 - 0.8 * slow_blink) * (1 - 0.35 * snap - 0.12 * gulp)
                    * (1 - 0.5 * flinch))
    p = _pose(x=LIE_X, y=LIE_Y, facing=-1.0, turn=0.32, arm_l=arm_l, arm_r=arm_r, extra=ex)
    p.extra["dazed"] = clamp(dz)
    p.extra["one_eye"] = one
    p.extra["grimace"] = clamp(0.1 + 0.6 * eff + 0.5 * wince + 0.35 * squeeze + 0.2 * snap)
    p.extra["strain"] = clamp(0.6 * eff + 0.3 * try_)
    # gaze: the track is in WORLD screen directions (-x = the dark on the left, -y = the ceiling); lying on his
    # back with the crown to the right, the rig's head-local axes map as: look_x = world y, look_y = -world x
    look_x = clamp(gy + ly * (1 - closed), -1.0, 1.0)
    look_y = clamp(-gx + lx * (1 - closed), -1.2, 1.2)
    p = p.copy(lid_l=lid_v, lid_r=lid_v, look_x=look_x, look_y=look_y,
               mouth_open=clamp(mo + 0.05 * closed + 0.04 * dz),
               mouth_round=0.35 * (mo > 0.05) * (1 - creak),
               mouth_tremble=0.6 * creak + 0.15 * tense,
               squint=clamp(0.25 * eff + 0.45 * wince + 0.5 * squeeze + 0.25 * flinch + 0.15 * snap),
               brow_worry=clamp(0.25 * dz + 0.45 * eff + 0.3 * wince - 0.15 * tense),
               brow_furrow=clamp(0.15 + 0.3 * eff + 0.4 * wince + 0.45 * tense + 0.35 * squeeze + 0.1 * one
                                 + 0.25 * snap),
               brow_raise=br + 0.12 * slurp - 0.15 * tense,
               smile=-0.15 - 0.2 * tense - 0.25 * snap - 0.1 * gulp,
               head_turn=0.05 * noise1(t * 0.3, 44) - 0.08 * flinch + 0.06 * one - 0.1 * closed,
               head_nod=0.12 * (gy < -0.5) - 0.15 * squeeze,
               head_tilt=-6.0 * flinch,
               breath=None if tense < 0.5 else 0.15 * math.sin(2 * math.pi * 0.9 * t))
    return p


def anger_lit(p, t, amb, L, rim=0.6):
    hc = A.head_center(p, t)
    return dress(p, hc, amb, L, rim=rim, rim_dir=-100.0)


# =========================================================================== the crawler
def _drag_pull(t):
    """How far the glove has dragged it left (stage units)."""
    v = 0.0
    for k, tg in enumerate(TUGS):
        v += 210.0 * ease_out(clamp((t - tg) / 0.32))
    if t > TUGS[2] + 0.35:
        a = t - (TUGS[2] + 0.35)
        v += 380.0 * a + 300.0 * a * a
    return v


def _lunge_dx():
    b = ease_out(clamp((LUNGE_HIT - 0.35) / 0.3))
    return (C.LUNGE_REACH * b) * CR_S


def crawler_pose(t):
    """(pose, layer) of the crawler in the depths two-shots; layer 'back' (behind Anger) / 'front' / None."""
    if t < APPROACH:
        return None, None
    if t < REVEAL:          # creep in from the dark, behind him
        v = C.ADVANCE["creep"] * CR_S / 1.3
        x = X_SNARL - (REVEAL - t) * v * (1.0 - 0.35 * smoothstep((t - (REVEAL - 0.8)) / 0.8))
        ph = (x - X_APP0) / (C.ADVANCE["creep"] * CR_S)
        p = _pose(x=x, y=BACK_Y, scale=CR_S, facing=1.0, head_tilt=-4.0,
                  extra=dict(state="creep", state2="snarl", mix=smoothstep((t - (REVEAL - 0.5)) / 0.5), phase=ph,
                             jaw=0.12, drool=0.5))
        return p, "back"
    if t < LUNGE:           # snarl over him
        jaw = lerp(0.18, 0.88, ease_out(clamp((t - HISS) / 0.12)))
        jaw -= 0.25 * _pulse(t, HISS + 1.15, 0.3, 0.6, 0.6)
        jaw += 0.06 * noise1(t * 6.0, 311)
        p = _pose(x=X_SNARL, y=BACK_Y, scale=CR_S, facing=1.0,
                  head_tilt=4.0 * _pulse(t, HISS, 0.1, 0.8, 0.5) + 2.0 * noise1(t * 0.8, 312),
                  extra=dict(state="snarl", jaw=clamp(jaw), drool=0.55, tongue=0.6))
        return p, "back"
    if t < BONK:            # the lunge
        u = clamp((t - LUNGE) / (BONK - LUNGE))
        ph = 0.35 * smoothstep(u / 0.6) + (LUNGE_HIT - 0.35) * ease_in(clamp((u - 0.6) / 0.4))
        p = _pose(x=X_SNARL, y=BACK_Y, scale=CR_S, facing=1.0, extra=dict(state="lunge", phase=ph))
        return p, "back"
    # clonk -> KO: it drops down in FRONT of him (the hit knocks it off its line)
    a = t - BONK
    m = smoothstep(a / 0.38)
    dx = _lunge_dx()
    x0 = X_SNARL + dx
    x = lerp(x0, X_KO, ease_out(clamp(a / 0.42)))
    fall = clamp(a / (THUD - BONK))
    y = lerp(BACK_Y - 30.0, FRONT_Y, fall * fall) if a < (THUD - BONK) else FRONT_Y
    flop = 9.0 * _pulse(t, FLOP - 0.02, 0.05, 0.02, 0.15)
    ex = dict(state="lunge", phase=LUNGE_HIT, state2="ko", mix=m)
    # the lunge carries its own forward travel: shift the pose so the blend does not slide
    x_l = x - dx * (1 - m)
    if t >= GLOVE - 0.05:   # dragged away by the tail
        pull = _drag_pull(t)
        dm = smoothstep((t - (TUGS[0] - 0.05)) / 0.25)
        ex = dict(state="ko", state2="dragged", mix=dm, tail_to=glove_point(t))
        p = _pose(x=X_KO - pull, y=FRONT_Y, scale=CR_S, facing=1.0, extra=ex)
        return p, "front"
    p = _pose(x=x_l, y=y - flop, scale=CR_S, facing=1.0,
              head_tilt=28.0 * _pulse(t, BONK, 0.03, 0.08, 0.4), extra=ex)
    p.extra["twitch"] = 1.0 if t > FLOP + 0.6 else 0.0
    return p, "front"


def ko_tail_tip():
    p = _pose(x=X_KO, y=FRONT_Y, scale=CR_S, facing=1.0, extra=dict(state="ko"))
    return C.tail_tip(p, GLOVE)


def glove_point(t):
    """The glove's grip point: reaches the KO tail tip out of the dark, then pulls."""
    tx, ty = ko_tail_tip()
    if t < GLOVE:
        u = ease_out(clamp((t - CUT19) / (GLOVE - CUT19)))
        return lerp(tx - 520.0, tx - 4.0, u), lerp(ty - 70.0, ty - 6.0, u)
    pull = _drag_pull(t + 0.06)
    return tx - 4.0 - pull, ty - 6.0 - 12.0 * smoothstep((t - TUGS[0]) / 0.3)


def glove_grip(t):
    return smoothstep((t - (GRIP_CLOSE - 0.08)) / 0.1)


def draw_crawler(c, t, p, amb, L):
    hc = C.head_pos(p, t)
    r, g, b = light.light_at(hc[0], hc[1], amb, L)
    m = max(r, g, b, 1e-3)
    q = p.copy(light=1.1, tint=(int(255 * r / m), int(255 * g / m), int(255 * b / m)), tint_amt=0.12, rim=0.7,
               rim_color=s3.RIM_COLD)
    C.draw(c, q, t)


# =========================================================================== the rock
ROCK_FROM = (-460.0, 640.0)


def _rock_hit_point():
    p, _ = crawler_pose(BONK - 1e-3)
    hx, hy = C.head_pos(p, BONK - 1e-3)
    return hx - 14.0, hy - 16.0


def rock_state(t):
    """(x, y, angle) of the thrown rock, or None."""
    if t < WHOOSH or t > T1:
        return None
    hx, hy = _rock_hit_point()
    if t < BONK:
        u = (t - WHOOSH) / (BONK - WHOOSH)
        x = lerp(ROCK_FROM[0], hx, u)
        y = lerp(ROCK_FROM[1], hy, u) - 120.0 * math.sin(math.pi * u) * 0.6
        return x, y, -900.0 * (t - WHOOSH)
    floor = FRONT_Y + 22.0
    g = 2600.0
    t1 = ROCK_B1 - BONK
    vx = 300.0
    vy = (floor - hy - 0.5 * g * t1 * t1) / t1
    ang0 = -900.0 * (BONK - WHOOSH)
    if t < ROCK_B1:
        a = t - BONK
        return hx + vx * a, hy + vy * a + 0.5 * g * a * a, ang0 + 500.0 * a
    x1 = hx + vx * t1
    if t < ROCK_B2:
        a = t - ROCK_B1
        d = ROCK_B2 - ROCK_B1
        vb = 0.5 * g * d
        return x1 + 190.0 * a, floor - (vb * a - 0.5 * g * a * a), ang0 + 500.0 * t1 + 420.0 * a
    x2 = x1 + 190.0 * (ROCK_B2 - ROCK_B1)
    a = min(t, ROCK_REST) - ROCK_B2
    d = ROCK_REST - ROCK_B2
    k = 1.0 - (1.0 - a / d) ** 2
    return x2 + 45.0 * k, floor, ang0 + 500.0 * t1 + 420.0 * (ROCK_B2 - ROCK_B1) + 120.0 * k


def _rock_path():
    pts = []
    for i in range(9):
        a = i / 9 * math.tau
        r = 21.0 * (0.8 + 0.3 * hash01(i, 321))
        pts.append((math.cos(a) * r * 1.15, math.sin(a) * r * 0.9))
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    path.close()
    return path


_ROCK = None


def draw_rock(c, t):
    global _ROCK
    st = rock_state(t)
    if st is None:
        return
    if _ROCK is None:
        _ROCK = _rock_path()
    x, y, ang = st
    if t < BONK:   # motion ghosts
        for k in (3, 2, 1):
            g = rock_state(t - k * 0.018)
            if g:
                c.save()
                c.translate(g[0], g[1])
                c.rotate(g[2])
                c.drawPath(_ROCK, paint("#6A6474", 0.16 * (4 - k)))
                c.restore()
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.drawPath(_ROCK, paint("#5E5868"))
    c.save()
    c.clipPath(_ROCK, doAntiAlias=True)
    c.drawCircle(-7, -8, 13, paint("#8E8698", 0.8))
    c.drawCircle(9, 9, 15, paint("#3A3442", 0.7))
    c.restore()
    c.drawPath(_ROCK, paint("#0E0C12", 0.9, stroke=2.0))
    c.restore()


def draw_clonk(c, t):
    """EMISSIVE: a brief white impact star at the clonk."""
    a = t - BONK
    if not (0 <= a < 0.16):
        return
    hx, hy = _rock_hit_point()
    k = 1 - a / 0.16
    for i in range(7):
        ang = i / 7 * math.tau + 0.4
        r0, r1 = 14 + 30 * (1 - k), 30 + 55 * (1 - k * 0.5)
        c.drawLine(hx + math.cos(ang) * r0, hy + math.sin(ang) * r0, hx + math.cos(ang) * r1,
                   hy + math.sin(ang) * r1, paint("#FFF4D8", 0.9 * k, stroke=3.0))
    from anim.core import glow
    glow(c, hx, hy, 60, "#FFF0D0", 0.6 * k)


# =========================================================================== the drool drop
def drool_target(t):
    """Where the special drool drop lands: his gorget / pauldron right by his face."""
    p = anger_pose(t)
    return A.face_pos(p, -34.0, 104.0, t)


def draw_drool(c, t):
    """The long strand from its jaw that lets go at DROOL and lands at DROOL_LAND (+ the splat after)."""
    p, layer = crawler_pose(min(t, LUNGE - 0.01))
    if p is None or t < DROOL - 0.6 or t > LUNGE + 0.2:
        return
    mx, my = C.mouth_pos(p, t)
    mx -= 6.0
    tx, ty = drool_target(DROOL_LAND)
    if t < DROOL:          # the strand stretches
        st = clamp((t - (DROOL - 0.6)) / 0.6)
        fx.saliva_drop(c, mx, my + 6, size=0.9, stretch=st)
    elif t < DROOL_LAND:   # it lets go and falls
        u = (t - DROOL) / (DROOL_LAND - DROOL)
        x = lerp(mx, tx, u)
        y = lerp(my + 50, ty, u * u)
        fx.saliva_drop(c, x, y, size=1.3, detached=True)
        fx.saliva_drop(c, mx, my + 6, size=0.7, stretch=0.3 * (1 - u))
    # the splat (lit) stays on the armour
    if t >= DROOL_LAND:
        a = t - DROOL_LAND
        k = 1.0 - 0.5 * smoothstep(a / 1.5)
        sp = 1.0 + 0.6 * ease_out(clamp(a / 0.12))
        c.drawOval(skia.Rect(tx - 13 * sp, ty - 5 * sp, tx + 13 * sp, ty + 5 * sp), paint("m_drool", 0.6 * k))
        c.drawOval(skia.Rect(tx - 13 * sp, ty - 5 * sp, tx + 13 * sp, ty + 5 * sp),
                   paint("#20302E", 0.4 * k, stroke=1.2))
        c.drawCircle(tx - 4, ty - 2, 3.0, paint("#FFFFFF", 0.8 * k))
        if a < 0.3:
            for i in range(4):
                ang = math.pi * (1.1 + 0.8 * i / 3)
                d = 26 * ease_out(a / 0.3)
                c.drawCircle(tx + math.cos(ang) * d, ty + math.sin(ang) * d * 0.5 - 30 * a + 120 * a * a, 2.0,
                             paint("m_drool", 0.8 * (1 - a / 0.3)))


# =========================================================================== the world
DEP_AMB = 0.11


def scene_lights(t, p):
    L = s3.bottom_lights(t)
    hc = A.head_center(p, t)
    L.append(Light(hc[0] - 140, hc[1] + 20, 620.0, 0.2, FILL_COLD, "point"))   # soft cold fill
    return L


_BG = {}
_BG_OVERSCAN = 0.84


def _draw_bg_cached(c, cam, cam0):
    """The (static) depths set for a ROLLED close-up: rendered once per shot at its start camera (zoomed out a
    little for overscan) and then only scaled / shifted on screen (an axis-aligned blit) as the camera pushes
    in - a rolled draw of the set every frame costs ~35 ms. Pure function of the camera: identical output."""
    key = (round(cam0.cx, 2), round(cam0.cy, 2), round(cam0.zoom, 4), round(cam0.rot, 3))
    ent = _BG.get(key)
    if ent is None:
        camc = Camera(cam0.cx, cam0.cy, cam0.zoom * _BG_OVERSCAN, cam0.rot)
        surf = skia.Surface(W, H)
        lc = surf.getCanvas()
        lc.clear(skia.ColorBLACK)
        lc.save()
        camc.apply(lc, 0.0)
        s3.draw_flat(lc, lambda cc: env.draw_depths(cc, 0.0, dust=0.0), camc.zoom)
        lc.restore()
        if len(_BG) > 6:
            _BG.clear()
        ent = _BG[key] = (camc, surf.makeImageSnapshot())
    camc, img = ent
    k = cam.zoom / camc.zoom
    r = math.radians(cam.rot)
    dx, dy = camc.cx - cam.cx, camc.cy - cam.cy
    bx = (1 - k) * W / 2 + cam.zoom * (dx * math.cos(r) - dy * math.sin(r))
    by = (1 - k) * H / 2 + cam.zoom * (dx * math.sin(r) + dy * math.cos(r))
    c.save()
    c.resetMatrix()
    c.translate(bx, by)
    c.scale(k, k)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint())
    c.restore()


def draw_world(c, t, cam, *, anger=True, crawler=True, glove=True, rock=True, dust=None, extra=None,
               amb=DEP_AMB, vig=0.5, dim=0.0, emissive_extra=None, lights_extra=(), bg0=None):
    p = anger_pose(t)
    L = scene_lights(t, p) + list(lights_extra)
    if glove and CUT19 <= t < CRUNCH + 0.5:      # a breath of light where the glove comes out of the dark
        gx, gy = glove_point(t)
        L.append(Light(gx + 40.0, gy - 30.0, 420.0, 0.3, "#9A8A78", "point"))
    cp, layer = crawler_pose(t) if crawler else (None, None)
    dd = lerp(0.75, 0.3, clamp((t - T0) / 12.0)) if dust is None else dust
    if bg0 is not None and abs(cam.rot) > 0.5 and abs(cam.rot - bg0.rot) < 1e-6:
        _draw_bg_cached(c, cam, bg0)
        c.save()
        cam.apply(c, t)
    else:
        c.save()
        cam.apply(c, t)
        s3.draw_flat(c, lambda cc: env.draw_depths(cc, t, dust=dd), cam.zoom)
    s3.draw_stuck_sword(c, t)
    if abs(cam.rot) < 0.5:          # (big soft sprites: far too slow to blit rolled; it has settled by then)
        s3.impact_dust(c, t)
    if cp is not None and layer == "back":
        draw_crawler(c, t, cp, amb, L)
    if anger:
        A.draw(c, anger_lit(p, t, amb, L), t)
    if crawler:
        draw_drool(c, t)
    gp = None
    if glove and CUT19 <= t < CRUNCH + 0.5:
        gp = glove_point(t)
        with Layer(c, cf=light_filter(0.8)):
            C.draw_glove(c, gp[0], gp[1], 0.95, grip=glove_grip(t), angle=4.0, layer="back")
    if cp is not None and layer == "front":
        draw_crawler(c, t, cp, amb, L)
    if gp is not None:
        with Layer(c, cf=light_filter(0.8)):
            C.draw_glove(c, gp[0], gp[1], 0.95, grip=glove_grip(t), angle=4.0, layer="front")
    if rock:
        draw_rock(c, t)
    if extra is not None:
        extra(c)
    c.restore()

    def emit(cc):
        env.draw_fungi_glow(cc, t, "depths", exclude=s3.LIE_EXCLUDE)
        s3.draw_gouge_glow(cc, t)
        if cp is not None:
            C.draw_eyes(cc, cp, t)
        draw_clonk(cc, t)
        if emissive_extra is not None:
            emissive_extra(cc)
    finish(c, cam, t, amb, L, emissive=emit, vig=vig)
    if dim > 0:
        fade_overlay(c, dim, "#020308")


FACE_ROT = -68.0      # face close-ups: the camera rolls so his (lying) face reads nearly upright


def face_cam(t, zoom, sx=0.5, sy=0.45, dx=0.0, dy=0.0, at=None, rot=FACE_ROT):
    p = anger_pose(t if at is None else at)
    hc = A.head_center(p, t if at is None else at)
    return cam_on_rot((hc[0] + dx, hc[1] + dy), zoom, sx, sy, rot)


def cu(t, cut, end, z0, z1, sx=0.5, sy=0.45, dx=0.0, dy=0.0):
    """Face close-up framed at the cut, with a slow push from z0 to z1: (camera, start camera)."""
    u = ease_in_out(clamp((t - cut) / (end - cut)))
    return face_cam(cut, lerp(z0, z1, u), sx, sy, dx, dy), face_cam(cut, z0, sx, sy, dx, dy)


def _blur(c, t, amount):
    if amount > 0.01:
        fx.blur_vision(c, amount, t, ghost=1.0, edge=0.6)


def _blur_amt(t):
    """Dazed vision: ramps in from S3's clean frame, peaks on `dazed`, clears through the groan / assess."""
    up = smoothstep((t - T0) / (DAZED - T0 + 0.1))
    down = 1.0 - smoothstep((t - (GROAN + 0.4)) / 4.5)
    return clamp(lerp(0.15, 0.85, up) * down)


# =========================================================================== shots
def shot1(c, t):
    u = ease_in_out(clamp((t - T0) / (CUT2 - T0)))
    a = Camera(352.0, 830.0, 1.09)                     # = S3's last framing
    b = face_cam(t, 1.55, 0.55, 0.5, rot=-30.0)        # a slow, woozy roll as his vision swims
    cam = cam_mix(a, b, u * 0.85)
    draw_world(c, t, cam, crawler=False, vig=0.55)
    _blur(c, t, _blur_amt(t))


def shot2(c, t):
    cam, c0 = cu(t, CUT2, CUT3, 2.5, 2.75, 0.5, 0.46, dx=-10)
    draw_world(c, t, cam, crawler=False, vig=0.6, bg0=c0)
    _blur(c, t, _blur_amt(t))


def shot3(c, t):
    p = anger_pose(t)
    hx, hy = A.hand_pos(p, "l", t)
    u = ease_in_out(clamp((t - CUT3) / (CUT4 - CUT3)))
    cam = Camera(hx + 20 - 10 * u, hy - 30, lerp(3.0, 3.2, u))

    def pebbles(cc):   # a few grains roll off as the fingers scrape
        for i, tw in enumerate((ASSESS + 0.85, ASSESS + 1.55)):
            fx.debris(cc, t, t - tw - 0.03, (hx + 22, hy + 14), seed=330 + i, kind="stone", n=4, speed=90,
                      direction=-40, spread=60, size=0.35, gravity=1500, floor_y=hy + 30, life=1.2)
    draw_world(c, t, cam, crawler=False, vig=0.55, extra=pebbles)
    _blur(c, t, _blur_amt(t) * 0.7)


def shot4(c, t):
    cam, c0 = cu(t, CUT4, CUT5, 2.35, 2.5, 0.52, 0.47, dx=-8)
    draw_world(c, t, cam, crawler=False, vig=0.55, bg0=c0)
    _blur(c, t, _blur_amt(t))


def lurker_pose(t):
    """The eyes again: lurking in the dark at the back-left, then the scurry away (side, small)."""
    if t < SCURRY - 0.05:
        p = _pose(x=-80.0, y=1112.0, scale=0.45, facing=1.0, look_x=0.6, look_y=0.1,
                  extra=dict(state="lurk", body_alpha=0.5))
        return p
    a = t - (SCURRY - 0.05)
    x = -80.0 + 520.0 * a + 120.0 * a * a          # darts out across the rubble (through the fungus light)
    ph = (x + 80.0) / (C.ADVANCE["scurry"] * 0.5)
    return _pose(x=x, y=1132.0, scale=0.5, facing=1.0, extra=dict(state="scurry", phase=ph))


def shot5(c, t):
    """POV: a slow, woozy pan across the dark grotto; the eyes; the scurry."""
    u = ease_in_out(clamp((t - CUT5) / (EYES_AGAIN - 0.2 - CUT5)))
    a = Camera(760.0, 640.0, 0.9, rot=-4.0)
    b = Camera(90.0, 920.0, 1.0, rot=2.0)
    cam = cam_mix(a, b, u)
    cam = Camera(cam.cx + 6 * noise1(t * 0.5, 351), cam.cy + 5 * noise1(t * 0.45, 352), cam.zoom, cam.rot)
    lp = lurker_pose(t)
    show = t >= EYES_AGAIN

    def lurker(cc):
        if show and lp.extra["state"] != "lurk":
            C.draw(cc, lp.copy(light=1.0, rim=0.9, rim_color=s3.RIM_COLD), t)

    def lurk_eyes(cc):
        if not show:
            return
        k = smoothstep((t - EYES_AGAIN) / 0.35)
        if lp.extra["state"] == "lurk":
            q = lp.copy(lid_l=k * A.blink(t + 1.3) if k < 1 else None, lid_r=k if k < 1 else None)
            C.draw_eyes(cc, q, t)
        else:
            C.draw_eyes(cc, lp, t)
    draw_world(c, t, cam, anger=False, crawler=False, extra=lurker, emissive_extra=lurk_eyes, vig=0.6,
               amb=0.1)
    _blur(c, t, 0.12)


def shot6(c, t):
    """Close-up: eyes track the scurry; pass out (the lids close, the frame dims); dark hold."""
    cam, c0 = cu(t, CUT6, CUT7, 2.45, 2.85, 0.5, 0.46, dx=-8)
    dim = 0.55 * smoothstep((t - (PASS_OUT + 0.3)) / 1.6)
    amb = lerp(DEP_AMB, 0.085, smoothstep((t - PASS_OUT) / 1.5))
    draw_world(c, t, cam, crawler=False, vig=lerp(0.55, 0.85, dim / 0.55), amb=amb, dim=dim, bg0=c0)
    _blur(c, t, 0.45 * smoothstep((t - (PASS_OUT + 0.2)) / 1.2))


def shot7(c, t):
    """Insert: pebbles shift in the dark (the noise that wakes him)."""
    cam = Camera(268.0, 1150.0, 2.4)
    rocks = [(238.0, 1166.0, 9.0), (252.0, 1172.0, 6.0), (264.0, 1162.0, 7.5), (226.0, 1176.0, 5.0)]

    def pebbles(cc):
        for i, (x0, y0, r) in enumerate(rocks):
            a = max(0.0, t - (PEBBLES + 0.03 * i))
            d = 60.0 * (1 - math.exp(-a / 0.25)) * (0.6 + 0.4 * hash01(i, 341))
            x = x0 + d
            y = y0 + 0.3 * d - (8.0 * abs(math.sin(a * 14.0)) * math.exp(-a / 0.2))
            cc.save()
            cc.translate(x, y)
            cc.rotate(700.0 * (1 - math.exp(-a / 0.25)) * (1 if i % 2 else -1))
            cc.drawOval(skia.Rect(-r, -r * 0.75, r, r * 0.75), paint("#4A4452"))
            cc.drawOval(skia.Rect(-r * 0.6, -r * 0.6, r * 0.2, r * 0.0), paint("#8A8296", 0.6))
            cc.drawOval(skia.Rect(-r, -r * 0.75, r, r * 0.75), paint("#0E0C12", 0.8, stroke=1.2))
            cc.restore()
        fx.dust_fall(cc, t, 222.0, 262.0, 1158.0, amount=_pulse(t, PEBBLES, 0.05, 0.25, 0.3), seed=343,
                     length=30, size=0.8)
    dim = 0.25 * (1 - smoothstep((t - WAKE) / 0.6))
    draw_world(c, t, cam, crawler=False, extra=pebbles, vig=0.6, amb=0.1, dim=dim)


def shot8(c, t):
    cam, c0 = cu(t, CUT8, CUT9, 2.55, 2.62, 0.5, 0.46, dx=-8)
    dim = 0.3 * (1 - smoothstep((t - CUT8) / 0.7))
    draw_world(c, t, cam, crawler=False, vig=0.6, dim=dim, bg0=c0)


def shot9(c, t):
    u = ease_in_out(clamp((t - CUT9) / (CUT10 - CUT9)))
    cam = cam_mix(Camera(330.0, 985.0, 1.3), Camera(345.0, 990.0, 1.38), u)
    draw_world(c, t, cam, crawler=False, vig=0.55)


def approach_front_pose(t):
    """POV into the dark: the crawler front view, creeping toward the camera."""
    u = clamp((t - CUT10) / (CUT11 - CUT10))
    sc = lerp(0.3, 0.62, u * u * 0.4 + u * 0.6)
    y = lerp(1088.0, 1150.0, u)
    ph = (t - CUT10) / 1.2
    return _pose(x=-170.0 + 30 * u, y=y, scale=sc, facing=1.0, look_x=0.15, look_y=0.25,
                 extra=dict(state="creep", view="front", phase=ph, jaw=0.15, drool=0.5))


def shot10(c, t):
    cam = Camera(-150.0, 990.0, 1.15)
    cam = Camera(cam.cx + 4 * noise1(t * 0.6, 361), cam.cy + 3 * noise1(t * 0.5, 362), cam.zoom)
    cp = approach_front_pose(t)

    def crawler(cc):
        draw_crawler(cc, t, cp, 0.1, [])

    def eyes(cc):
        C.draw_eyes(cc, cp, t)
    draw_world(c, t, cam, anger=False, crawler=False, extra=crawler, emissive_extra=eyes, vig=0.6, amb=0.1)


def shot11(c, t):
    cam, c0 = cu(t, CUT11, CUT12, 2.6, 2.75, 0.5, 0.46, dx=-8)
    draw_world(c, t, cam, crawler=False, vig=0.6, bg0=c0)


def shot12(c, t):
    u = ease_in_out(clamp((t - CUT12) / (CUT13 - CUT12)))
    cam = cam_mix(Camera(250.0, 960.0, 0.98), Camera(300.0, 950.0, 1.08), u)
    draw_world(c, t, cam, vig=0.55)


def snarl_front_pose(t):
    jaw = lerp(0.2, 0.92, ease_out(clamp((t - HISS) / 0.12))) + 0.05 * noise1(t * 7.0, 371)
    return _pose(x=360.0, y=1330.0, scale=1.75, facing=1.0, look_x=0.0, look_y=0.35,
                 extra=dict(state="snarl", view="front", jaw=clamp(jaw), drool=1.0, tongue=0.85))


def shot13(c, t):
    """POV close-up: the head looms over him; the jaw opens ON the hiss."""
    u = ease_in_out(clamp((t - CUT13) / (CUT14 - CUT13)))
    cp = snarl_front_pose(t)
    hx, hy = C.head_pos(snarl_front_pose(CUT13), CUT13)
    cam = cam_on_rot((hx, hy + 60), 1.25 + 0.12 * u, 0.5, 0.4, 0.0)
    cam = fx.camera_shake(cam, t, [(HISS, 6.0, 0.4)], seed=37)

    def crawler(cc):
        draw_crawler(cc, t, cp, 0.11, [Light(360.0, 700.0, 700.0, 0.25, FILL_COLD, "point")])

    def eyes(cc):
        C.draw_eyes(cc, cp, t)
    draw_world(c, t, cam, anger=False, crawler=False, extra=crawler, emissive_extra=eyes, vig=0.6, amb=0.1)


def shot14(c, t):
    cam, c0 = cu(t, CUT14, CUT15, 2.1, 2.25, 0.55, 0.55, dx=-40)
    draw_world(c, t, cam, vig=0.55, bg0=c0)


def shot15(c, t):
    u = ease_in_out(clamp((t - CUT15) / (CUT16 - CUT15)))
    cam = cam_mix(Camera(300.0, 930.0, 1.0), Camera(320.0, 960.0, 1.06), u)
    cam = fx.camera_shake(cam, t, [(BONK, 14.0, 0.45), (THUD, 8.0, 0.3)], seed=41)
    draw_world(c, t, cam, vig=0.55)


def shot16(c, t):
    cam, c0 = cu(t, CUT16, CUT17, 2.0, 2.2, 0.6, 0.45, dx=-60, dy=20)
    draw_world(c, t, cam, vig=0.55, bg0=c0)


def shot17(c, t):
    u = ease_in_out(clamp((t - CUT17) / (CUT18 - CUT17)))
    cam = cam_mix(Camera(200.0, 960.0, 0.86), Camera(215.0, 965.0, 0.9), u)
    draw_world(c, t, cam, vig=0.5)


def shot18(c, t):
    cam, c0 = cu(t, CUT18, CUT19, 2.35, 2.55, 0.55, 0.42, dx=-10)
    draw_world(c, t, cam, vig=0.55, bg0=c0)


def shot19(c, t):
    """Close: the glove reaches out of the dark and closes on the tail; the first tug."""
    tx, ty = ko_tail_tip()
    u = ease_in_out(clamp((t - CUT19) / (CUT19B - CUT19)))
    cam = Camera(tx + 60.0 - 40.0 * u, ty - 60.0, 1.45)
    draw_world(c, t, cam, vig=0.55)


def shot19b(c, t):
    """Wide: dragged away into the darkness; his one eye follows it."""
    u = ease_in_out(clamp((t - CUT19B) / (CUT20 - CUT19B)))
    cam = cam_mix(Camera(110.0, 1030.0, 0.63), Camera(80.0, 1035.0, 0.65), u)
    draw_world(c, t, cam, vig=0.5)


def shot20(c, t):
    cam = Camera(150.0, 990.0, 0.9)

    def specks(cc):
        for i, ch in enumerate(CHOMPS[:3]):
            fx.crunch_specks(cc, t, -40.0, 1120.0, t - ch - 0.03, seed=380 + i, n=7, size=1.0, direction=-35)
    draw_world(c, t, cam, vig=0.5, extra=specks)


def shot21(c, t):
    cam, c0 = cu(t, CUT21, T1, 2.15, 2.5, 0.56, 0.44, dx=-20)
    draw_world(c, t, cam, vig=0.55, bg0=c0)


SHOTS = [(T0, shot1), (CUT2, shot2), (CUT3, shot3), (CUT4, shot4), (CUT5, shot5), (CUT6, shot6), (CUT7, shot7),
         (CUT8, shot8), (CUT9, shot9), (CUT10, shot10), (CUT11, shot11), (CUT12, shot12), (CUT13, shot13),
         (CUT14, shot14), (CUT15, shot15), (CUT16, shot16), (CUT17, shot17), (CUT18, shot18), (CUT19, shot19),
         (CUT19B, shot19b), (CUT20, shot20), (CUT21, shot21)]


def shot_at(t):
    fn = SHOTS[0][1]
    for t0, f in SHOTS:
        if t >= t0:
            fn = f
    return fn


def render(canvas, t):
    shot_at(t)(canvas, t)


# =========================================================================== motion-locked SFX
def sfx_events():
    return [
        {"name": "armor_shift", "start": round(ASSESS + 2.1, 3), "gain_db": -20.0},     # the wince (tries to move)
        {"name": "armor_shift", "start": round(ONE_ARM + 0.3, 3), "gain_db": -16.0},    # tries to rise
        {"name": "armor_shift", "start": round(ARM_UP + 0.05, 3), "gain_db": -18.0},    # the weak raise
        {"name": "armor_shift", "start": round(FLOP + 0.3, 3), "gain_db": -20.0},       # the arm sinks
    ]
