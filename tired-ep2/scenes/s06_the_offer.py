"""s06 — The offer ("lullaby").

The keycard opens the control room. The tall chair turns: the Boss was
waiting. She knew the moment it bit him, and she offers him the one thing he
wants: go home, sleep, never be bothered again. He is tempted (a daydream of
his bed). He looks down at Curiosity, its ears droop... "But for once... I'm
not tired." His lids open FULLY for the first time in both episodes.

All timing comes from info.cue / info.line / info.word_time.
"""
import math

import cairocffi as cairo

from engine import core, sets, props, human, creatures, fx
from engine.core import (tween, seg, smoothstep, lerp, ease_in_out, ease_out, ease_in,
                         ease_out_back)
from audio import sfx

M = sets.CONTROL_MARKS
SC = M["char_scale"]                 # 0.75: people in this set
SCUR = 0.68                          # Curiosity (dog-sized next to him)
CHAIR = M["chair"]                   # (1700, 1500)
BOSS_GY = human.ground_from_seat("boss", M["boss_seat"][1], SC)
DOORS = M["doors"]                   # (430, 480, 360, 820)

DOOR_T = (680, 1330)                 # Tiredness standing in the doorway (behind the room layer)
DOOR_C = (506, 1330)                 # Curiosity sitting beside him
STEP_T = (694, 1368)                 # first step onto the room floor (the wide starts here)
STEP_C = (548, 1368)
STAND_T = (855, 1500)                # where he faces the Boss (= s07 smash_feet, left of the case)
STAND_C = (722, 1500)                # Curiosity at his left, a little behind him

TURN_T = 0.7                         # facing the Boss (screen-right)
BOSS_LOOK = (-0.82, -0.1)
TIRED_LOOK = (0.8, 0.1)              # at her (seated, her eyes are a little below his)

# The Boss steeples her fingertips in front of her chest (seated).
STEEPLE = {"base": "sit_chair",
           "al_ik": 1.0, "al_tx": -0.004, "al_ty": 0.47, "al_tz": 0.2, "al_h": "flat", "al_wa": -1.45,
           "al_wabs": 0.9, "al_layer": "front",
           "ar_ik": 1.0, "ar_tx": -0.004, "ar_ty": 0.47, "ar_tz": 0.2, "ar_h": "flat", "ar_wa": -1.45,
           "ar_wabs": 0.9, "ar_layer": "front"}


# ----------------------------------------------------------------------------
# timing (derived from cues, cached per timeline)
# ----------------------------------------------------------------------------
class _K:
    pass


_KCACHE = {}


def _timing(info):
    key = (info.id, round(info.dur, 4), tuple(sorted(info.cues.items())))
    k = _KCACHE.get(key)
    if k is not None:
        return k
    k = _K()
    c = info.cue
    L = info.line
    k.end = info.dur
    # --- doors (scene start): beep -> reader green -> heavy doors slide open
    k.beep = c("doors") + 0.3
    k.green = k.beep + 0.34
    k.open0 = k.beep + 0.55
    k.open1 = k.open0 + 1.6
    k.look_in = k.open1 - 0.15          # they look into the room
    # --- chair: the wide (they walk in), the chair starts to turn
    k.chair = c("chair")
    k.s2 = k.chair + 0.2
    k.walk0 = k.s2                     # cut on action: the first step onto the room floor
    spd = human.cycle_speed("tired", "walk", 0.55) * SC
    k.walk_dur = (STAND_T[0] - STEP_T[0]) / spd
    k.walk1 = k.walk0 + k.walk_dur
    k.cur_spd = (STAND_C[0] - STEP_C[0]) / k.walk_dur / (creatures.SPEC_WALK_SPEED * SCUR)
    k.l01, k.l01e = L("s06_l01").start, L("s06_l01").end
    k.ct0 = k.s2 + 0.35                 # chair starts turning (slow, heavy)
    k.s3 = k.l01 - 1.05                 # cut to the chair (ct ~0.3: the reveal plays here)
    k.ct1 = k.l01 - 0.12                # settled, facing him
    # --- dialogue
    k.l02, k.l02e = L("s06_l02").start, L("s06_l02").end
    k.l03, k.l03e = L("s06_l03").start, L("s06_l03").end
    k.w_bit = info.word_time("s06_l03", 5)
    k.w_you3 = info.word_time("s06_l03", 6)
    k.bandage = c("bandage")
    k.l04, k.l04e = L("s06_l04").start, L("s06_l04").end
    k.l05, k.l05e = L("s06_l05").start, L("s06_l05").end
    k.w_sleep = info.word_time("s06_l05", 4)
    k.l06, k.l06e = L("s06_l06").start, L("s06_l06").end
    k.tempt = c("tempt")
    k.look = c("look")
    k.l07, k.l07e = L("s06_l07").start, L("s06_l07").end
    k.w_sound = info.word_time("s06_l07", 2)
    k.droop = c("droop")
    k.l08, k.l08e = L("s06_l08").start, L("s06_l08").end
    k.w_but = info.word_time("s06_l08", 0)
    k.w_im = info.word_time("s06_l08", 3)
    k.w_not = info.word_time("s06_l08", 4)
    k.eyes_open = c("eyes_open")
    # --- shot list (cut times)
    k.s4 = k.l01e + 0.25                # Tiredness MCU: reaction + l02
    k.s5 = k.l02e + 0.3                 # Boss MCU: l03
    k.s6 = k.l03e + 0.3                 # Tiredness MS: the bandage
    k.s7 = k.l04 - 0.15                 # Boss: the offer (l04 + "Walk away. Go home.")
    k.s8 = k.w_sleep - 0.12             # Tiredness listening ("Sleep as long as you like.")
    k.s9 = k.l06 - 0.15                 # Boss: "Nobody will ever bother you again."
    k.s10 = k.l06e + 0.2                # Tiredness: tempt (daydream)
    k.s11 = k.look + 0.7                # two-shot: he looks down at Curiosity; l07
    k.s12 = k.droop                     # Curiosity CU: the droop
    k.s13 = k.droop + 1.5               # Tiredness: decision + l08 (slow push-in)
    k.s14 = k.eyes_open + 1.3           # Boss CU: lids narrow
    # --- acting beats
    k.band0 = k.bandage + 0.05          # pupils to the bandage
    k.band_up = k.bandage + 0.15        # forearm rises
    k.band_back = k.bandage + 1.12      # pupils back to her
    k.dream0 = k.tempt - 0.25
    k.dream1 = k.look - 0.15            # bubble dissolves as he looks down
    k.cur_up = k.s11 + 0.2              # Curiosity looks up at him
    k.decide = k.s13 + 0.25             # lip press, then resolve
    k.narrow = k.s14 + 0.4
    _KCACHE[key] = k
    return k


def _shot(t, k):
    cuts = [(0.0, 1), (k.s2, 2), (k.s3, 3), (k.s4, 4), (k.s5, 5), (k.s6, 6), (k.s7, 7), (k.s8, 8),
            (k.s9, 9), (k.s10, 10), (k.s11, 11), (k.s12, 12), (k.s13, 13), (k.s14, 14)]
    sh, t0 = 1, 0.0
    for tc, n in cuts:
        if t >= tc:
            sh, t0 = n, tc
    return sh, t0


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def tw(t, keys, ease=ease_in_out):
    return tween(t, keys, ease)


def slow_blink(t, t0, close=0.35, hold=0.35, open_=0.45):
    """0..1 lid value of a slow blink starting at t0, or None outside it."""
    if t < t0 or t > t0 + close + hold + open_:
        return None
    return tw(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0), (t0 + close + hold + open_, 0.0)])


def chair_turn(t, k):
    if t < k.ct0:
        return 0.0
    if t < k.s3:
        return 0.3 * ease_in(seg(t, k.ct0, k.s3)) ** 0.75
    return lerp(0.3, 0.8, ease_out(seg(t, k.s3, k.ct1)))


def boss_body_turn(ct):
    psi = math.pi * (1 - ct)                # 0 = chair facing camera
    return -min(1.6, math.degrees(psi) / 49.0)


def _chair(ctx, ct, part):
    cx, cy = CHAIR
    ctk = round(ct, 3)
    sets.sprite(ctx, ("s06_chair", part, ctk), cx - 330, cy - 1080 * SC, 660, 1100 * SC,
                lambda c: props.boss_chair(c, cx, cy, SC, ctk, part=part, dir=-1))


def _doorway_light(ctx, draw):
    """Characters standing in the doorway: backlit by the warm tunnel."""
    ddx, ddt, ddw, ddh = DOORS
    ctx.push_group()
    draw()
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.rectangle(-800, -200, 3800, 2600)
    core.fill(ctx, core.alpha("#05060b", 0.36))
    core.radial_glow(ctx, ddx + ddw * 0.3, ddt + 160, 520, "#ffa64a", 0.22)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint()


def _eye_glow(ctx, a, r, amt, keys=("eye_l", "eye_r")):
    if amt <= 0.01:
        return
    for kk in keys:
        if kk in a:
            ex, ey = a[kk][0], a[kk][1]
            core.radial_glow(ctx, ex, ey, r, "power", amt)


# ----------------------------------------------------------------------------
# Tiredness
# ----------------------------------------------------------------------------
def tired_kw(t, k, info):
    # ---------------- where / body
    if t < k.walk0:
        x, y = DOOR_T
        pose, pose_t, turn = "stand", None, 0.35
    elif t < k.walk1:
        p = seg(t, k.walk0, k.walk1)
        x, y = lerp(STEP_T[0], STAND_T[0], p), lerp(STEP_T[1], STAND_T[1], p)
        pose, pose_t, turn = "walk", t - k.walk0, 0.55
    else:
        x, y = STAND_T
        kb = smoothstep(seg(t, k.walk1, k.walk1 + 0.32))
        pose = ("walk", "stand", kb) if kb < 1 else "stand"
        pose_t = k.walk_dur
        turn = lerp(0.55, TURN_T, smoothstep(seg(t, k.walk1 - 0.1, k.walk1 + 0.5)))
    # tempted sway (a slow loose roll about the hips)
    sway_amt = smoothstep(seg(t, k.tempt - 0.2, k.tempt + 0.8)) * (1 - smoothstep(seg(t, k.look, k.look + 0.5)))
    if sway_amt > 0.001 and t >= k.walk1 + 0.4:
        ph = (t - k.tempt) / 2.6
        sigh_k = tw(t, [(k.tempt + 0.2, 0.0), (k.tempt + 0.5, 1.0), (k.tempt + 1.3, 1.0), (k.tempt + 1.9, 0.6)])
        pose = {"base": "stand", "rot": 0.028 * sway_amt * math.sin(2 * math.pi * ph),
                "side": 0.02 * sway_amt * math.sin(2 * math.pi * ph + 0.6),
                "hunch": 0.18 * sigh_k, "nod": 0.05 * sigh_k}
    # "I'm not tired": the slouch leaves his spine (shoulders square, chin up a hair)
    straight = smoothstep(seg(t, k.w_not - 0.05, k.w_not + 0.8))
    if straight > 0.001 and pose == "stand":
        pose = {"base": "stand", "posture": 1 - 0.55 * straight, "hunch": -0.15 * straight}
    # the bandaged forearm lifts so he can look at it
    reach = None
    wr = tw(t, [(k.band_up, 0.0), (k.band_up + 0.42, 1.0), (k.band_back + 0.15, 1.0),
                (k.band_back + 0.6, 0.0)])
    if wr > 0.001:
        reach = {"r": (STAND_T[0] + 120, STAND_T[1] - 315, wr, 0.9)}

    # ---------------- expression
    open_k = ease_out_back(seg(t, k.w_not - 0.02, k.w_not + 0.3), 1.2)
    open_s = smoothstep(seg(t, k.w_not - 0.02, k.w_not + 0.3))
    if t < k.w_not - 0.02:
        expr = "neutral"
    elif open_s < 1:
        expr = ("neutral", "determined", open_s)
    else:
        expr = "determined"

    lid = tw(t, [(0, 0.0), (k.look_in, 0.0), (k.look_in + 0.25, -0.06), (k.look_in + 1.4, -0.02),
                 (k.s4 + 0.05, -0.02), (k.s4 + 0.3, -0.09), (k.l02e + 0.2, -0.07), (k.l02e + 0.7, -0.03),
                 (k.l03, -0.03), (k.w_bit + 0.1, -0.05),
                 (k.w_sleep + 0.05, 0.0), (k.w_sleep + 0.35, 0.1), (k.l06, 0.11), (k.l06e, 0.15),
                 (k.tempt, 0.13), (k.tempt + 1.3, 0.19), (k.look - 0.25, 0.17), (k.look + 0.2, -0.03),
                 (k.l07, -0.02), (k.l07e, 0.05), (k.droop + 1.4, 0.0), (k.decide + 0.4, -0.04),
                 (k.w_but - 0.1, -0.04), (k.w_but + 0.25, 0.02)])
    lid += -0.11 * open_k               # the payoff: FULLY open (with a hair of overshoot)
    brow = tw(t, [(0, 0.0), (k.look_in, 0.0), (k.look_in + 0.25, 0.1), (k.look_in + 1.4, 0.04),
                  (k.s4 + 0.05, 0.04), (k.s4 + 0.3, 0.16), (k.l02e + 0.5, 0.1), (k.l03, 0.08),
                  (k.w_bit + 0.1, 0.16), (k.bandage + 1.4, 0.08),
                  (k.w_sleep, 0.05), (k.tempt, 0.08), (k.look, 0.08), (k.look + 0.3, 0.14),
                  (k.decide, 0.14), (k.decide + 0.5, 0.1), (k.w_but, 0.0), (k.w_not, 0.0),
                  (k.w_not + 0.3, 0.12)])
    brow_ang = tw(t, [(0, 0.0), (k.s4 + 0.05, 0.05), (k.s4 + 0.3, 0.2), (k.l02e + 0.5, 0.12),
                      (k.w_bit, 0.12), (k.w_bit + 0.25, 0.25), (k.bandage + 1.4, 0.15),
                      (k.w_sleep, 0.12), (k.tempt, 0.18), (k.look, 0.18), (k.look + 0.35, 0.34),
                      (k.l07e, 0.38), (k.decide, 0.38), (k.decide + 0.35, 0.45),
                      (k.w_but - 0.15, 0.1), (k.w_im, -0.05), (k.w_not, -0.05), (k.w_not + 0.3, 0.2)])
    curve = tw(t, [(0, -0.08), (k.w_sleep, -0.08), (k.l06e, 0.02), (k.tempt + 0.3, 0.06),
                   (k.tempt + 1.4, 0.24), (k.look, 0.22), (k.look + 0.4, 0.0),
                   (k.w_sound, 0.04), (k.l07e, 0.12), (k.l07e + 0.6, 0.06), (k.decide, 0.0),
                   (k.w_but, -0.04)])
    press = tw(t, [(0, 0.12), (k.l02e + 0.1, 0.12), (k.l02e + 0.4, 0.38), (k.l03 + 0.5, 0.25),
                   (k.bandage, 0.2), (k.band_back + 0.3, 0.35), (k.l04, 0.2),
                   (k.w_sleep, 0.12), (k.tempt, 0.0), (k.look + 0.3, 0.1), (k.l07, 0.1),
                   (k.decide, 0.1), (k.decide + 0.25, 0.5), (k.w_but - 0.2, 0.35), (k.w_but, 0.12)])
    head_turn = tw(t, [(k.look - 0.03, 0.0), (k.look + 0.4, -0.48), (k.w_but - 0.05, -0.48),
                       (k.w_but + 0.35, 0.0)])
    head_nod = tw(t, [(0, 0.0), (k.band0 + 0.12, 0.0), (k.band0 + 0.45, 0.15), (k.band_back + 0.12, 0.15),
                      (k.band_back + 0.5, 0.0), (k.tempt, 0.0), (k.tempt + 1.2, 0.06),
                      (k.look - 0.03, 0.06), (k.look + 0.4, 0.16), (k.w_but - 0.05, 0.16),
                      (k.w_but + 0.35, -0.02), (k.w_not + 0.3, -0.04)])
    head_tilt = 0.05 * sway_amt * math.sin(2 * math.pi * (t - k.tempt) / 2.6 + 1.1)
    head_tilt += tw(t, [(k.s4, 0.0), (k.s4 + 0.3, -0.03), (k.l02e + 0.6, 0.0)])
    # gaze: pupils lead, the head follows ~0.15 s later
    lx, ly = TIRED_LOOK
    look = tw(t, [(0, (0.45, 0.0)), (k.look_in, (0.45, 0.0)), (k.look_in + 0.2, (0.85, -0.12)),
                  (k.walk0, (0.75, 0.05)), (k.ct0 + 0.5, (0.75, 0.05)), (k.ct0 + 0.7, (0.9, -0.05)),
                  (k.walk1 + 0.3, (lx, ly)),
                  (k.band0, (lx, ly)), (k.band0 + 0.16, (0.38, 0.9)), (k.band_back, (0.38, 0.9)),
                  (k.band_back + 0.16, (lx, ly)),
                  (k.w_sleep + 0.25, (lx, ly)), (k.w_sleep + 0.65, (0.35, -0.42)),
                  (k.l06, (0.5, -0.25)), (k.l06e, (0.55, -0.2)), (k.tempt + 0.4, (0.3, -0.5)),
                  (k.look - 0.18, (0.3, -0.5)), (k.look - 0.02, (-0.55, 0.8)),
                  (k.w_sound - 0.1, (-0.55, 0.8)), (k.w_sound + 0.12, (0.15, 0.75)),
                  (k.l07e + 0.25, (0.15, 0.75)), (k.l07e + 0.45, (-0.55, 0.8)),
                  (k.w_but - 0.22, (-0.55, 0.8)), (k.w_but - 0.06, (lx, ly - 0.04))])
    focus = -0.35 * smoothstep(seg(t, k.tempt, k.tempt + 1.0)) * (1 - smoothstep(seg(t, k.look, k.look + 0.2)))
    # the tempted exhale (sigh SFX at tempt + 0.25)
    sigh_open = tw(t, [(k.tempt + 0.22, 0.0), (k.tempt + 0.38, 0.13), (k.tempt + 0.95, 0.07),
                       (k.tempt + 1.25, 0.0)])
    face = {"lid": lid, "brow": brow, "brow_ang": brow_ang, "curve": curve, "press": press, "open": sigh_open,
            "head_turn": head_turn, "head_nod": head_nod, "head_tilt": head_tilt, "focus": focus}
    # ---------------- blinks
    blink = None
    if k.tempt - 0.2 <= t < k.look + 0.6:
        blink = 0.0                       # no random blinks in the dream: one slow heavy blink only
    for b0, cl, ho, op in ((k.w_sleep + 0.85, 0.35, 0.3, 0.5), (k.tempt + 1.0, 0.4, 0.4, 0.5)):
        v = slow_blink(t, b0, cl, ho, op)
        if v is not None:
            blink = v
    if t >= k.w_but - 0.3:
        blink = 0.0                       # he holds her gaze; the eyes stay open
    power = lerp(0.6, 0.9, smoothstep(seg(t, k.w_not, k.w_not + 0.45)))
    return dict(x=x, y=y, pose=pose, pose_t=pose_t, turn=turn, expr=expr, face=face, look=look,
                blink=blink, power=power, reach=reach, open_k=open_s)


def draw_tired(ctx, t, k, info, kw=None):
    kw = kw or tired_kw(t, k, info)
    return human.draw_person(ctx, "tired", kw["x"], kw["y"], SC, t, pose=kw["pose"], pose_t=kw["pose_t"],
                             expr=kw["expr"], look=kw["look"], face=kw["face"], turn=kw["turn"],
                             mouth=info.mouth("tired", t), blink=kw["blink"], power=kw["power"],
                             outfit="sewer", bandage=True, headphones=None, hood=0.0, reach=kw["reach"],
                             seed=6)


# ----------------------------------------------------------------------------
# Curiosity
# ----------------------------------------------------------------------------
def cur_kw(t, k):
    pose, pose_from, pose_mix, pose_t = "sit", None, 1.0, None
    if t < k.walk0:
        x, y = DOOR_C
    elif t < k.walk1:
        p = seg(t, k.walk0, k.walk1)
        x, y = lerp(STEP_C[0], STAND_C[0], p), lerp(STEP_C[1], STAND_C[1], p)
        pose, pose_t = "walk", (t - k.walk0) * k.cur_spd
    else:
        x, y = STAND_C
        m = seg(t, k.walk1, k.walk1 + 0.45)
        if m < 1:
            pose, pose_from, pose_mix = "sit", "walk", m
            pose_t = k.walk_dur * k.cur_spd
    if t < k.s11:
        expr, tears = "calm", 0.0
    else:
        expr = "teary"
        tears = tw(t, [(k.droop + 0.15, 0.0), (k.droop + 1.2, 0.42)])
    ears = tw(t, [(0, 0.5), (k.look_in - 0.05, 0.5), (k.look_in + 0.2, 0.78), (k.walk0, 0.62),
                  (k.ct0 + 0.45, 0.6), (k.ct0 + 0.8, 0.36), (k.l01e, 0.34), (k.l03e, 0.3),
                  (k.s11, 0.32), (k.cur_up + 0.3, 0.36), (k.l07 + 0.3, 0.33), (k.l07e, 0.22),
                  (k.droop + 0.1, 0.2), (k.droop + 1.35, 0.03)])
    look = tw(t, [(0, (0.7, 0.0)), (k.look_in - 0.05, (0.7, 0.0)), (k.look_in + 0.12, (0.9, -0.15)),
                  (k.walk0, (0.85, 0.05)), (k.ct0 + 0.5, (0.85, 0.05)), (k.ct0 + 0.65, (0.92, -0.25)),
                  (k.cur_up, (0.92, -0.25)), (k.cur_up + 0.15, (0.42, -0.88)),
                  (k.droop + 0.45, (0.42, -0.88)), (k.droop + 0.75, (0.2, 0.6))])
    tilt = tw(t, [(k.cur_up + 0.1, 0.0), (k.cur_up + 0.35, -0.12), (k.droop + 0.5, -0.12),
                  (k.droop + 0.95, 0.14)])
    return dict(x=x, y=y, pose=pose, pose_from=pose_from, pose_mix=pose_mix, pose_t=pose_t, expr=expr,
                tears=tears, ears=ears, look=look, tilt=tilt)


def draw_cur(ctx, t, k, kw=None):
    kw = kw or cur_kw(t, k)
    return creatures.draw_specimen(ctx, kw["x"], kw["y"], SCUR, t, form=1.0, pose=kw["pose"],
                                   pose_from=kw["pose_from"], pose_mix=kw["pose_mix"], pose_t=kw["pose_t"],
                                   expr=kw["expr"], tears=kw["tears"], ears=kw["ears"], look=kw["look"],
                                   tilt=kw["tilt"], glow=0.75)


# ----------------------------------------------------------------------------
# The Boss
# ----------------------------------------------------------------------------
def boss_kw(t, k, info):
    ct = chair_turn(t, k)
    look = tw(t, [(0, BOSS_LOOK), (k.w_bit - 0.05, BOSS_LOOK), (k.w_bit + 0.12, (-0.72, 0.55)),
                  (k.w_you3 + 0.15, (-0.72, 0.55)), (k.w_you3 + 0.32, BOSS_LOOK)])
    lid = tw(t, [(0, 0.0), (k.l04 - 0.2, 0.0), (k.l04 + 0.4, 0.035), (k.l06e + 0.2, 0.035),
                 (k.s13, 0.0), (k.narrow, 0.0), (k.narrow + 0.35, 0.075)])
    lower = tw(t, [(k.narrow, 0.0), (k.narrow + 0.35, 0.12)])
    curve = tw(t, [(0, 0.0), (k.l04 - 0.3, 0.0), (k.l04 + 0.5, 0.12), (k.l06, 0.15), (k.l06e, 0.22),
                   (k.s13, 0.06), (k.narrow, 0.0)])
    brow_ang = tw(t, [(0, 0.0), (k.l04 - 0.3, 0.0), (k.l04 + 0.5, 0.14), (k.l06e + 0.3, 0.18), (k.s13, 0.0)])
    brow = tw(t, [(0, 0.0), (k.l04 - 0.3, 0.0), (k.l04 + 0.5, 0.05), (k.l06e + 0.3, 0.07), (k.s13, 0.0)])
    smirk = tw(t, [(k.w_you3, 0.0), (k.w_you3 + 0.25, -0.14), (k.s6 + 0.4, -0.14), (k.l04 - 0.3, 0.0)])
    head_tilt = tw(t, [(0, 0.0), (info.word_time("s06_l01", 5), 0.0), (k.l01e, 0.025), (k.l03, 0.01),
                       (k.l04, 0.0), (k.l05, -0.02), (k.l06e, -0.03), (k.s13, -0.01)])
    blink = 0.0 if t >= k.s14 else None
    return dict(ct=ct, look=look, blink=blink,
                face={"lid": lid, "lower": lower, "curve": curve, "brow_ang": brow_ang, "smirk": smirk,
                      "head_tilt": head_tilt, "brow": brow})


def draw_boss_and_chair(ctx, t, k, info, kw=None):
    kw = kw or boss_kw(t, k, info)
    ct = kw["ct"]
    _chair(ctx, ct, "behind")
    a = None
    alpha = smoothstep(seg(ct, 0.16, 0.25))
    if alpha > 0.001:
        def boss(c=ctx):
            return human.draw_person(c, "boss", CHAIR[0], BOSS_GY, SC, t, pose=STEEPLE, expr="cold",
                                     turn=boss_body_turn(ct), look=kw["look"], face=kw["face"],
                                     mouth=info.mouth("boss", t), blink=kw["blink"], seed=3)
        with sets.shaded(ctx, sets.control_room, t, layer="shade"):
            if alpha < 0.999:
                ctx.push_group()
                a = boss()
                ctx.pop_group_to_source()
                ctx.paint_with_alpha(alpha)
            else:
                a = boss()
    _chair(ctx, ct, "front")
    return a


# ----------------------------------------------------------------------------
# cameras
# ----------------------------------------------------------------------------
def camera_for(sh, t, t0, k):
    if sh == 1:                                   # inside, facing the doors
        return tw(t, [(0.0, (636, 1012, 1.04)), (k.s2, (646, 1000, 1.1))])
    if sh == 2:                                   # geography wide
        return tw(t, [(t0, (1255, 1000, 0.71)), (k.s3, (1268, 998, 0.735))])
    if sh == 3:                                   # the chair turns: the Boss
        return tw(t, [(t0, (1690, 1112, 1.5)), (k.l01, (1690, 1145, 1.95)), (k.s4, (1690, 1150, 2.05))])
    if sh == 4:                                   # Tiredness MCU
        return tw(t, [(t0, (922, 1015, 2.25)), (k.s5, (918, 1005, 2.33))])
    if sh == 5:                                   # Boss MCU (closer)
        return tw(t, [(t0, (1688, 1145, 2.6)), (k.s6, (1687, 1136, 2.75))])
    if sh == 6:                                   # Tiredness MS: the bandage
        return tw(t, [(t0, (935, 1075, 1.9)), (k.s7, (938, 1068, 1.96))])
    if sh == 7:                                   # Boss: the offer
        return tw(t, [(t0, (1688, 1160, 2.4)), (k.s8, (1687, 1146, 2.6))])
    if sh == 8:                                   # Tiredness listening
        return tw(t, [(t0, (920, 1000, 2.3)), (k.s9, (916, 990, 2.4))])
    if sh == 9:                                   # Boss: the sweetest line
        return tw(t, [(t0, (1687, 1140, 2.7)), (k.s10, (1686, 1124, 2.95))])
    if sh == 10:                                  # tempt: room above his head for the dream
        return tw(t, [(t0, (935, 935, 2.12)), (k.s11, (928, 922, 2.32))])
    if sh == 11:                                  # two-shot with Curiosity (his head top stays at y~165)
        z = tw(t, [(t0, 1.88), (k.s12, 1.92)])
        return (808, 772 + 800 / z, z)
    if sh == 12:                                  # Curiosity CU
        z = tw(t, [(t0, 3.8), (k.s13, 3.95)])
        return (740, 1335 + 70 / z, z)
    if sh == 13:                                  # decision + payoff: slow push-in
        return tw(t, [(t0, (925, 1010, 2.35)), (k.l08, (922, 1000, 2.45)), (k.s14, (896, 944, 3.9))])
    # 14: Boss CU
    return tw(t, [(t0, (1678, 1055, 3.3)), (k.end, (1677, 1050, 3.42))])


# what each shot needs drawn (skip characters that are off screen)
NEEDS = {1: "TC", 2: "TCB", 3: "B", 4: "T", 5: "B", 6: "T", 7: "B", 8: "T", 9: "B", 10: "T", 11: "TC",
         12: "C", 13: "T", 14: "B"}


# ----------------------------------------------------------------------------
# render
# ----------------------------------------------------------------------------
def render(ctx, t, info):
    k = _timing(info)
    sh, t0 = _shot(t, k)
    cx, cy, zoom = camera_for(sh, t, t0, k)
    need = NEEDS[sh]
    doors_open = ease_in_out(seg(t, k.open0, k.open1))
    reader = "green" if t >= k.green else "red"
    core.bg(ctx, "#05070b")
    ta = ca = None
    tkw = tired_kw(t, k, info) if "T" in need else None
    with core.camera(ctx, cx, cy, zoom):
        doorway = sh == 1
        if doorway:
            # back (warm tunnel) -> the two in the doorway -> room (with the sliding doors)
            sets.control_room(ctx, t, layer="back")

            def pair():
                nonlocal ta, ca
                ca = draw_cur(ctx, t, k)
                ta = draw_tired(ctx, t, k, info, tkw)
            _doorway_light(ctx, pair)
            # their eyes glow in the doorway; drawn BEFORE the room layer so the closed doors hide them
            _eye_glow(ctx, ca, 26, 0.2)
            _eye_glow(ctx, ta, 28, 0.1)
            ca = ta = None
            sets.control_room(ctx, t, layer="room", doors_open=doors_open, reader=reader, chair=False)
            _chair(ctx, 0.0, "behind")
            _chair(ctx, 0.0, "front")
        else:
            sets.control_room(ctx, t, layer="bg", doors_open=doors_open, reader=reader, chair=False)
            if need == "T" and zoom > 1.8:
                # focus pull: the bright pod window behind his head steps back a little
                wx, wy, ww, wh = M["window"]
                ctx.rectangle(wx, wy, ww, wh)
                core.fill(ctx, core.alpha("#04070c", 0.3))
            if "B" in need:
                draw_boss_and_chair(ctx, t, k, info)
            else:
                ct = chair_turn(t, k)
                _chair(ctx, ct, "behind")
                _chair(ctx, ct, "front")
            if "T" in need or "C" in need:
                with sets.shaded(ctx, sets.control_room, t, layer="shade"):
                    # Curiosity sits a hair in front of him (never crosses him: no z flicker)
                    if "T" in need:
                        ta = draw_tired(ctx, t, k, info, tkw)
                    if "C" in need:
                        ca = draw_cur(ctx, t, k)
        # glows stay bright over the room's shade
        if ca is not None:
            _eye_glow(ctx, ca, 26, 0.2)
        if ta is not None:
            ok = tkw["open_k"]
            _eye_glow(ctx, ta, 28 + 4 * ok, 0.1 + 0.12 * ok)
            if t >= k.w_not and sh == 13:
                fx.eye_glint(ctx, ta["eye_r"][0] + 6, ta["eye_r"][1] - 8, 0.55, t, k.w_not + 0.12, 0.5)
            # the bandage: a faint teal pulse while he looks at it (the bite = their connection)
            gk = tw(t, [(k.band_up + 0.25, 0.0), (k.band_up + 0.6, 1.0), (k.band_back, 0.7),
                        (k.band_back + 0.45, 0.0)])
            if gk > 0.01:
                ex, ey = ta["elbow_r"]
                wx, wy = ta["wrist_r"]
                core.radial_glow(ctx, lerp(ex, wx, 0.55), lerp(ey, wy, 0.55), 70, "power", 0.32 * gk)
    # ---------------- screen space
    if sh == 10 and ta is not None:
        hx, hy = ta["top"]
        sx = 540 + (hx - cx) * zoom
        sy = 960 + (hy - cy) * zoom
        fx.daydream(ctx, 598, 372, 0.86, t, k.dream0, k.dream1, fx.dream_bed,
                    tail=(sx + 52, sy - 12), seed=4)


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    k = _timing(info)
    ev = []
    ev.append((k.beep - 0.06, "keycard_beep", -3, 0.15))
    ev.append((k.open0 - 0.12, "door_slide", 0, 0.0))
    ev.append((k.ct0 + 0.05, "chair_creak", -7, 0.45))
    ev.append((k.s3 + 0.08, "chair_creak", -5, 0.3))
    for i in range(3):
        ev.append((k.walk0 + 0.5 * i, "footstep", -9, -0.25 + 0.1 * i))
    ev.append((k.look_in, "ears_perk", -3, -0.3))        # Curiosity's ears up at the doorway
    ev.append((k.band_up, "cloth_rustle", -8, -0.1))
    ev.append((k.cur_up + 0.05, "creature_chitter", -11, -0.2))   # a small hopeful "huh?" up at him
    ev.append((k.tempt + 0.25, "sigh", -3, -0.05))
    ev.append((k.droop + 0.35, "creature_chirp_sad", -7, -0.15))
    ev += sfx.loop_events("pod_hum", 0.0, info.dur, -15, 0.0)
    return ev
