"""s04 — "Not my problem" (music: lonely).

A quiet HushCorp service tunnel lit by dim emergency lamps. Tiredness trudges out
of the dark side tunnel (the way back to the shaft and the pods), pushes his hood
back in the first light, drops onto a crate and gives up. Curiosity points back
toward the pods and tugs his sleeve; he tells it, gently, that its family is not
his problem. The hurt lands on Curiosity's face (ears lowering degree by degree,
tears), it lets go of his sleeve and walks off alone into the dark side tunnel,
looking back once. Alone with a drip, he looks at his bandage (a faint teal
glow), groans, and follows.

All timing comes from info.cue(...) / info.line(...) / info.word_time(...).
World = sets.service_tunnel (people and creature at s=0.75).

Shots (see _shot_times / _cam)
  S1  arrive   0 .. l01.end+.3      wide on the side-tunnel mouth, pan + push-in: he
                                    walks out of the dark, hood back under the first
                                    lamp, turns, drops onto the crate; Curiosity
                                    follows out of the tunnel; "Okay. I'm done."
  S2  slump    .. l02 word 7        his medium: head hangs, rubs his face, l02 part 1
  S3  listen   .. tug-.1            Curiosity: ears shoot up at "go home", pleading,
                                    eyes slide back toward the tunnel
  S4  point    .. l03-.15           two-shot: points back to the tunnel, looks back at
                                    him, hop-turns, takes his sleeve, gentle tugs
  S5  sorry    .. l04-.15           closer two-shot: "Look. I'm sorry..." (gentle);
                                    beat: his eyes slide away, the head follows
  S6  problem  .. l04.end+.15       his close-up, not looking at it
  S7  hurt     .. leave+.1          Curiosity CU: body sags, ears lower degree by
                                    degree, tears, lets go of the sleeve
  S8a leave    .. at the mouth      wide: it walks away alone; he never looks up
  S8b back     .. alone+1.65        the mouth: it stops, looks back once, goes dark
  S9  alone    .. l05.end+.1        his medium: drip; lifts the bandaged forearm, a
                                    faint teal glow, lip press, looks down the tunnel;
                                    "...Ugh." with his eyes shut
  S10 follow   .. end               stands up and trudges after it
"""
import math

import cairocffi as cairo

from engine import core, sets, human, fx
from engine import creatures as CR
from engine.core import clamp, lerp, seg, smoothstep, ease_in_out, ease_out, ease_in, tween

M = sets.TUNNEL_MARKS
S = 0.75                       # people / creature scale in the tunnel world
SEAT_X, FEET_Y = 1080, 1500    # Tiredness on the seat crate (ground point)
CUR_X = 735                    # Curiosity's spot beside him (screen-left = toward the tunnel)
CUR_Y = 1506                   # a hair in front of his feet line (it is drawn after him)
WALK_RATE = 0.8                # his trudge (fraction of the walk cycle rate)
MOUTH_X0 = 470                 # Curiosity's corridor-floor point in front of the side tunnel
VP = M["far_end"]              # side tunnel vanishing point (300, 1010)
CUR_V = CR.SPEC_WALK_SPEED * S  # its foot-locked speed at cycle rate 1

# sit_crate with longer shins so his soles reach the floor in front of the set's crate
_SITP = {"base": "sit_crate", "ll_p": 1.5, "lr_p": 1.48, "ll_k": 1.45, "lr_k": 1.42}
_WALK_FRONT = {"base": "walk", "al_layer": "front"}   # near arm over the head for the hood push


def _sitp(**kw):
    d = dict(_SITP)
    d.update(kw)
    return d


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def _tw(t, keys, ease=ease_in_out):
    return tween(t, keys, ease)


def _bump(t, t0, t1, amp=1.0):
    """0 -> amp -> 0 smooth bump over [t0, t1]."""
    if t <= t0 or t >= t1:
        return 0.0
    return amp * math.sin(math.pi * (t - t0) / (t1 - t0)) ** 2


def _ramp(t, t0, t1, ease=smoothstep):
    return ease(seg(t, t0, t1))


def _track(t, keys):
    """keys [(t, value, trans), ...] -> (prev, cur, k) with per-key transitions."""
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, 0.25
    for k in keys:
        if t >= k[0]:
            prev, cur, start, tr = cur, k[1], k[0], (k[2] if len(k) > 2 else 0.25)
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _pose_of(tr):
    a, b, k = tr
    if k >= 0.999 or a is b or a == b:
        return b
    if k <= 0.001:
        return a
    return (a, b, k)


def _addf(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _slow_blink(t, b0, hold):
    return _tw(t, [(b0, 0.0), (b0 + 0.3, 1.0), (b0 + 0.3 + hold, 1.0), (b0 + 0.68 + hold, 0.0)])


def _depth(k, x0=MOUTH_X0):
    """Side-tunnel depth k (0 = corridor floor in front of the mouth) -> (x, y, scale)."""
    f = 1.0 / (1.0 + 5.0 * k)
    return VP[0] + (x0 - VP[0]) * f, VP[1] + (CUR_Y - VP[1]) * f, f


_PROBE = None


def _probe_ctx():
    global _PROBE
    if _PROBE is None:
        _PROBE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))
    _PROBE.identity_matrix()
    return _PROBE


# ----------------------------------------------------------------------------
# timing (all from cues)
# ----------------------------------------------------------------------------
def _times(info):
    c = info.cue
    T = dict(
        l01=c("s04_l01"), l01e=c("s04_l01.end"), slump=c("slump"),
        l02=c("s04_l02"), l02e=c("s04_l02.end"), tug=c("tug"),
        l03=c("s04_l03"), l03e=c("s04_l03.end"), beat=c("beat"),
        l04=c("s04_l04"), l04e=c("s04_l04.end"), hurt=c("hurt"),
        leave=c("leave"), alone=c("alone"), l05=c("s04_l05"), l05e=c("s04_l05.end"),
        follow=c("follow"), end=c("end"),
    )
    wt = info.word_time
    T["w_done"] = wt("s04_l01", -1)
    T["w_okay"] = wt("s04_l01", 0)
    T["w_build"] = wt("s04_l02", 5)
    T["w_I2"] = wt("s04_l02", 7)          # "I just want to go home and sleep."
    T["w_home"] = wt("s04_l02", 12)
    T["w_sleep"] = wt("s04_l02", -1)
    T["w_look"] = wt("s04_l03", 0)
    T["w_sorry"] = wt("s04_l03", 2)
    T["w_family"] = wt("s04_l03", -1)
    T["w_not"] = wt("s04_l04", 2)
    T["w_problem"] = wt("s04_l04", -1)
    # --- arrival (S1): walk ends at the crate, turn, drop
    T["stop"] = min(1.9, T["l01"] - 1.3)
    T["sit0"] = T["stop"] + 0.35
    T["land"] = T["sit0"] + 0.5
    T["c_out"] = 0.75                              # Curiosity out of the side tunnel
    T["c_arr"] = T["land"] - 0.2                   # ... and beside the crate
    # --- shots
    T["s2"] = T["l01e"] + 0.3
    T["s3"] = T["w_I2"] - 0.12
    T["s4"] = T["tug"] - 0.1
    T["s5"] = T["l03"] - 0.15
    T["s6"] = T["l04"] - 0.15
    T["s7"] = T["l04e"] + 0.15
    T["s8"] = T["leave"] + 0.1
    T["s9"] = T["alone"] + 1.65
    T["s10"] = T["l05e"] + 0.1
    # --- Curiosity's point / turn / tug (S4)
    t4 = T["s4"]
    T["pt_up"] = t4                                # paw rises
    T["pt_look"] = t4 + 0.5                        # head turns back to him
    T["pt_down"] = max(t4 + 1.05, T["l03"] - 1.5)  # paw lowers
    T["hop"] = T["pt_down"] + 0.2                  # hop-turn (flip at hop + 0.12)
    T["grab0"] = T["hop"] + 0.27                   # rises into the sleeve tug
    T["grab"] = T["grab0"] + 0.3                   # sleeve in its teeth
    # --- hurt (S7)
    T["rel0"] = T["leave"] - 1.2                   # lets go of the sleeve
    # --- leave (S8)
    t8 = T["s8"]
    T["lv_walk"] = t8 + 0.55
    T["lv_mouth"] = T["lv_walk"] + 0.125 + (CUR_X - MOUTH_X0) / (CUR_V * 1.5)
    T["s8b"] = T["lv_mouth"] - 0.3
    T["lv_stop"] = T["lv_mouth"] + 0.55
    T["lv_back"] = T["lv_stop"] + 0.05             # looks back
    T["lv_fwd"] = T["lv_back"] + 1.0               # turns forward again
    T["lv_gone"] = T["lv_fwd"] + 0.9
    # --- alone (S9) / follow (S10)
    t9 = T["s9"]
    T["arm0"] = t9 + 0.15
    T["glow"] = t9 + 0.75
    T["press"] = t9 + 1.25
    T["arm1"] = t9 + 1.55
    T["look_tn"] = min(t9 + 1.75, T["l05"] - 0.55)
    T["up0"] = T["l05e"] - 0.15                    # anticipation, then stands
    T["up1"] = T["up0"] + 0.85
    T["walk2"] = T["up1"] - 0.05
    return T


_TC = {}


def _T(info):
    k = (id(info), info.dur, info.cue("s04_l01"))
    if k not in _TC:
        _TC.clear()
        _TC[k] = _times(info)
    return _TC[k]


# ----------------------------------------------------------------------------
# TIREDNESS
# ----------------------------------------------------------------------------
def _tired_walk_speed():
    return human.cycle_speed("tired", "walk", 1.0) * S * WALK_RATE


def _tired(t, T, info, cur_mouth=None):
    """World-space draw kwargs for Tiredness at time t."""
    v = _tired_walk_speed()
    stop = T["stop"]
    x_stop = SEAT_X - 20
    kw = dict(outfit="sewer", bandage=True, power=0.6, headphones=None)
    reach = {}

    # ---------------- arrival: walk out of the dark, hood back, turn, sit -------------
    if t < T["land"] + 0.6:
        pt_walk = WALK_RATE * min(t, stop) + 0.29
        x = x_stop - v * (stop - min(t, stop))
        if t < stop:
            pose = _WALK_FRONT if 0.15 < t < 1.55 else "walk"
        else:
            # stop: walk (frozen) -> stand -> sit, turning to face left (toward the tunnel)
            k1 = _ramp(t, stop, stop + 0.3)
            k2 = _ramp(t, T["sit0"], T["land"], ease_in)
            if k2 <= 0.0:
                pose = _pose_of(("walk", "stand", k1))
            else:
                pose = _pose_of(("stand", _sitp(), k2))
            x = lerp(x_stop, SEAT_X, _ramp(t, stop + 0.05, T["sit0"] + 0.2))
        turn = _tw(t, [(stop - 0.05, 1.0), (stop + 0.3, 0.15), (T["sit0"] + 0.25, -0.6)])
        hood = _tw(t, [(0.5, 1.0), (1.2, 0.0)])
        # hood push-back: near (l) hand up to the hood top, sweeping back over the crown
        if 0.15 < t < 1.65:
            hp = seg(t, 0.5, 1.2)
            ang = lerp(1.25, 2.45, smoothstep(hp))
            w = _ramp(t, 0.15, 0.5) * (1.0 - _ramp(t, 1.2, 1.6))
            hx, hy = x + 41, FEET_Y - 581                  # head centre while walking (turn 1, s .75)
            r = 94
            reach["l"] = (hx + r * math.cos(ang), hy - 30 - r * math.sin(ang), w)
        expr = _track(t, [(0.0, "annoyed"), (0.95, "squint", 0.3), (1.65, "bored", 0.4),
                          (T["land"], "sigh", 0.2), (T["land"] + 0.5, "bored", 0.3)])
        look = _tw(t, [(1.2, (0.25, 0.15)), (stop - 0.15, (0.35, 0.45)), (stop + 0.2, (-0.2, 0.6)),
                       (T["land"], (-0.25, 0.6)), (T["land"] + 0.5, (-0.1, 0.45))])
        face = {"lid": 0.07 * _bump(t, 0.95, 1.7)}
        if t >= T["land"]:
            pose = _sitp(nod=0.34 + _bump(t, T["land"], T["land"] + 0.5, 0.12),
                         hunch=0.65 + _bump(t, T["land"], T["land"] + 0.6, 0.12))
        return dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pt_walk, turn=turn, expr=_pose_of(expr),
                    look=look, face=face, hood=hood, reach=reach or None, blink=None,
                    mouth=info.mouth("tired", t))

    # ---------------- seated ---------------------------------------------------
    x = SEAT_X
    turn = -0.6
    # head carriage (sit_crate base: nod .34, lean .5, hunch .65)
    nod = _tw(t, [(T["land"] + 0.5, 0.34), (T["w_okay"], 0.28), (T["w_done"], 0.4),
                  (T["l01e"] + 0.3, 0.36),
                  (T["slump"] + 0.05, 0.36), (T["slump"] + 0.55, 0.6),        # head hangs
                  (T["l02"] - 0.25, 0.55), (T["l02"] + 0.15, 0.3),            # lifts, looks ahead
                  (T["w_build"], 0.27), (T["w_build"] + 0.4, 0.31),
                  (T["w_sleep"], 0.3), (T["w_sleep"] + 0.5, 0.36),
                  (T["s4"] + 0.3, 0.33),
                  (T["l03"], 0.38), (T["l03e"], 0.4),
                  (T["beat"] + 0.25, 0.36), (T["l04"], 0.33),
                  (T["l04e"] + 0.2, 0.4),
                  (T["s8"], 0.44), (T["lv_back"], 0.46), (T["s9"], 0.42),
                  (T["arm0"] + 0.1, 0.3), (T["arm1"], 0.32),
                  (T["look_tn"] + 0.15, 0.25),
                  (T["l05"], 0.22), (T["l05"] + 0.35, 0.08), (T["l05e"], 0.3),     # groan: head back
                  (T["up0"] + 0.25, 0.42), (T["up1"], 0.2)])
    lean = _tw(t, [(T["slump"] + 0.05, 0.5), (T["slump"] + 0.55, 0.58), (T["l02"] - 0.25, 0.55),
                   (T["l02"] + 0.15, 0.5), (T["up0"], 0.5), (T["up0"] + 0.3, 0.68)])
    hunch = _tw(t, [(T["l01e"], 0.65), (T["slump"] + 0.55, 0.75), (T["l02"] + 0.2, 0.65),
                    (T["l05"], 0.65), (T["l05"] + 0.4, 0.5), (T["l05e"] + 0.1, 0.72)])
    pose = _sitp(nod=nod, lean=lean, hunch=hunch)

    # slump: both hands up to rub his face (arms on the front layer the whole time:
    # they start and end at the knees, clear of the hanging head, so nothing pops)
    rub_w = _ramp(t, T["slump"] + 0.5, T["slump"] + 0.95) * (1 - _ramp(t, T["l02"] - 0.45, T["l02"] - 0.1))
    if T["slump"] + 0.45 < t < T["l02"] - 0.05:
        rb = math.sin((t - T["slump"]) * 2 * math.pi * 1.6) * 7 * _ramp(t, T["slump"] + 0.9, T["slump"] + 1.1)
        reach["l"] = (957 + rb, 1128 - rb * 0.3, rub_w)
        reach["r"] = (1008 - rb * 0.8, 1121 + rb * 0.3, rub_w)
        pose = dict(pose, al_layer="front", ar_layer="front")

    # tug: his far (l) hand is pulled out by the sleeve in Curiosity's teeth
    if cur_mouth is not None:
        gw = _ramp(t, T["grab"] - 0.12, T["grab"] + 0.12) * (1 - _ramp(t, T["rel0"] + 0.05, T["rel0"] + 0.5, ease_in))
        if gw > 0.0:
            mx, my = cur_mouth
            reach["l"] = (mx - 12, my + 17, gw)

    # alone: lifts the bandaged (near, r) forearm to look at it
    aw = _ramp(t, T["arm0"], T["arm0"] + 0.5) * (1 - _ramp(t, T["arm1"], T["arm1"] + 0.45))
    if aw > 0.0:
        reach["r"] = (948, 1206 + 4 * math.sin(t * 1.3), aw)

    # standing up and trudging after it
    pose_t = None
    if t >= T["up0"] + 0.25:
        k = _ramp(t, T["up0"] + 0.25, T["up1"], ease_out)
        pose = _pose_of((pose, "stand", k))
        turn = lerp(-0.6, -1.0, k)
        if t >= T["walk2"]:
            pose = _pose_of(("stand", "walk", _ramp(t, T["walk2"], T["walk2"] + 0.3)))
            x = SEAT_X - _tired_walk_speed() * max(0.0, t - T["walk2"] - 0.15)
        pose_t = WALK_RATE * max(0.0, t - T["walk2"]) + 0.5

    # --- eyes (pupils lead, the head follows ~0.15 s later via head_turn)
    look = _tw(t, [
        (T["land"] + 0.5, (-0.1, 0.45)), (T["w_okay"], (-0.15, 0.5)), (T["l01e"], (-0.1, 0.6)),
        (T["l02"], (-0.05, 0.3)), (T["w_I2"], (0.1, 0.35)), (T["w_sleep"] + 0.3, (0.0, 0.5)),
        # S4: follows the pointing paw toward the tunnel, then back to the creature
        (T["pt_up"] + 0.15, (-0.25, 0.5)), (T["pt_up"] + 0.35, (-0.9, 0.15)),
        (T["pt_look"] + 0.25, (-0.9, 0.15)), (T["pt_look"] + 0.45, (-0.55, 0.6)),
        (T["grab"], (-0.55, 0.65)), (T["grab"] + 0.3, (-0.6, 0.85)),       # down at the sleeve
        (T["w_look"] - 0.2, (-0.6, 0.85)), (T["w_look"] + 0.1, (-0.55, 0.65)),
        (T["l03e"], (-0.55, 0.62)),
        # beat: pupils slide away first, the head follows
        (T["beat"] + 0.1, (-0.5, 0.6)), (T["beat"] + 0.3, (0.65, 0.45)),
        (T["l04"], (0.7, 0.5)), (T["l04e"], (0.6, 0.6)),
        (T["s8"], (0.2, 0.7)), (T["s9"], (0.1, 0.6)),
        # alone: at the bandage, then down the dark tunnel
        (T["arm0"], (0.0, 0.55)), (T["arm0"] + 0.25, (-0.4, 0.55)),
        (T["arm1"], (-0.4, 0.55)), (T["look_tn"], (-0.3, 0.4)), (T["look_tn"] + 0.2, (-1.0, 0.05)),
        (T["l05"], (-1.0, 0.05)), (T["l05e"] + 0.2, (-0.7, 0.2)), (T["up1"], (-0.6, 0.25))])
    head_turn = _tw(t, [(T["beat"] + 0.3, 0.0), (T["beat"] + 0.55, 0.28), (T["l04e"] + 0.3, 0.22),
                        (T["s8"], 0.05),
                        (T["look_tn"] + 0.15, 0.0), (T["look_tn"] + 0.45, -0.3), (T["l05e"], -0.2)])
    head_tilt = _tw(t, [(T["l03"] - 0.2, 0.0), (T["l03"] + 0.3, -0.05), (T["l03e"] + 0.3, -0.03),
                        (T["beat"] + 0.4, 0.0)])

    # --- expressions (keyed, 0.25-0.4 s transitions)
    expr = _track(t, [
        (0.0, "bored"),
        (T["w_okay"] - 0.1, "deadpan", 0.25), (T["l01e"] + 0.2, "bored", 0.3),
        (T["slump"] + 0.05, "sigh", 0.3),
        (T["l02"] - 0.2, "bored", 0.3), (T["w_I2"], "sad", 0.4),
        (T["pt_up"] + 0.1, "unamused", 0.3), (T["grab"], "bored", 0.3),
        (T["l03"] - 0.3, "sad", 0.35),
        (T["beat"] + 0.2, "deadpan", 0.35),
        (T["l04e"] + 0.2, "bored", 0.4),
        (T["arm0"] + 0.2, "sad", 0.4),
        (T["l05"] - 0.05, "sigh", 0.25), (T["l05e"] + 0.1, "annoyed", 0.3), (T["up1"], "bored", 0.4)])
    face = _addf(
        {"head_turn": head_turn, "head_tilt": head_tilt},
        # gentle on "sorry": inner brows up a hair
        {"brow_ang": _tw(t, [(T["l03"] - 0.1, 0.0), (T["w_sorry"], 0.28), (T["l03e"] + 0.1, 0.2),
                             (T["beat"] + 0.4, 0.0)]),
         "lid": _tw(t, [(T["l01e"], 0.0), (T["l01e"] + 0.3, 0.06), (T["slump"], 0.06), (T["l02"], 0.0),
                        (T["beat"] + 0.5, 0.0), (T["l04"] + 0.2, 0.08), (T["l04e"] + 0.4, 0.12),
                        (T["s8"] + 0.2, 0.06)])},
        # lip presses
        {"press": _bump(t, T["beat"] + 0.45, T["l04"] - 0.05, 0.45)
         + _bump(t, T["l04e"] + 0.05, T["l04e"] + 0.85, 0.5)
         + _bump(t, T["press"], T["press"] + 0.75, 0.55) + _bump(t, T["slump"] - 0.3, T["slump"] + 0.2, 0.3)},
        # alone: inner brows up a hair at the glow
        {"brow_ang": _bump(t, T["glow"] - 0.1, T["arm1"] + 0.6, 0.22)
         + _bump(t, T["l02"] - 0.1, T["l02e"] + 0.4, 0.16)},
        {"frown": _bump(t, T["l04e"] + 0.1, T["s7"] + 0.3, 0.25)},
    )
    # slow blinks on judgement beats; eyes shut through the groan
    blink = None
    for (b0, hold) in ((T["w_sleep"] + 0.05, 0.25), (T["w_done"] + 0.15, 0.15), (T["l04e"] + 0.35, 0.3)):
        if b0 - 0.05 <= t <= b0 + 0.75 + hold:
            blink = _slow_blink(t, b0, hold)
    if T["l05"] - 0.1 <= t <= T["l05e"] + 0.3:
        blink = _tw(t, [(T["l05"] - 0.1, 0.0), (T["l05"] + 0.15, 1.0), (T["l05e"] - 0.1, 1.0),
                        (T["l05e"] + 0.3, 0.0)])
    return dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pose_t, turn=turn, expr=_pose_of(expr), look=look,
                face=face, hood=0.0, reach=reach or None, blink=blink, mouth=info.mouth("tired", t))


# ----------------------------------------------------------------------------
# CURIOSITY
# ----------------------------------------------------------------------------
def _cur_base(t):
    return dict(x=CUR_X, y=CUR_Y, s=S, pose="sit", expr="calm", flip=False, face=None,
                look=(0.45, -0.55), ears=0.5, tears=None, tilt=0.0, tail_curl=0.0, glow=1.0,
                pose_t=None, pose_from=None, pose_mix=1.0, point_angle=0.0, blink=None,
                sq=(1.0, 1.0), lift=0.0, alpha=1.0, clip=False, dark=0.0, tt=t, sleeve=False)


def _cur(t, T):
    """World-space draw kwargs for Curiosity."""
    d = _cur_base(t)
    if t < T["s4"]:
        return _cur_s1_s3(t, T, d)
    if t < T["grab0"]:
        return _cur_s4(t, T, d)
    if t < T["s8"]:
        return _cur_hold(t, T, d)
    return _cur_leave(t, T, d)


def _cur_s1_s3(t, T, d):
    # S1: follows him out of the dark side tunnel, trots to its spot, sits
    to, ta = T["c_out"], T["c_arr"]
    if t < to:
        k = 0.17 * (1.0 - seg(t, 0.0, to))
        x, y, f = _depth(k)
        d.update(x=x, y=y, s=S * f, clip=k > 0.11, dark=0.55 * smoothstep(seg(k, 0.0, 0.17)))
        d["pose"] = "walk"
        d["pose_t"] = t * 1.6
        d["glow"] = 0.8
    elif t < ta:
        u = seg(t, to, ta)
        e = u * (1.0 - 0.35 * u) / 0.65                # decelerating (ease-out) distance
        d["x"] = lerp(MOUTH_X0, CUR_X, clamp(e))
        d["pose"] = "walk"
        d["pose_t"] = to * 1.6 + (d["x"] - MOUTH_X0) / CUR_V
    else:
        d["pose_from"], d["pose"] = "stand", "sit"
        d["pose_mix"] = seg(t, ta, ta + 0.4)
    d["look"] = _tw(t, [(1.0, (0.6, -0.15)), (ta, (0.5, -0.5)), (T["land"], (0.45, -0.6))])
    d["tilt"] = _tw(t, [(T["land"] + 0.2, 0.0), (T["land"] + 0.5, -0.12), (T["l01"], -0.12),
                        (T["w_done"], 0.0), (T["w_done"] + 0.4, 0.06), (T["slump"] + 0.6, 0.08)])
    d["ears"] = _tw(t, [(T["land"], 0.55), (T["w_done"], 0.55), (T["w_done"] + 0.5, 0.44)])
    # S3: "go home" -> the ears shoot up; "sleep" -> worried, pleading; eyes slide to the tunnel
    if t >= T["w_home"] - 0.05:
        d["ears"] = lerp(0.44, 0.92, core.ease_out_back(seg(t, T["w_home"] - 0.05, T["w_home"] + 0.2)))
        d["expr"] = "surprised_soft"
        if t >= T["w_sleep"] + 0.15:
            d["ears"] = lerp(0.92, 0.6, _ramp(t, T["w_sleep"] + 0.15, T["w_sleep"] + 0.6))
        if t >= T["w_sleep"] + 0.33:       # switch on the blink (masks the lid change)
            d["expr"] = "pleading"
        d["look"] = _tw(t, [(T["w_sleep"] + 0.45, (0.4, -0.65)), (T["l02e"] - 0.05, (-0.85, -0.05)),
                            (T["l02e"] + 0.5, (-0.9, -0.1))])
        d["face"] = _tw(t, [(T["l02e"] + 0.05, 1.0), (T["l02e"] + 0.45, 0.3)])
        d["tilt"] = _tw(t, [(T["w_home"], 0.06), (T["w_home"] + 0.2, -0.06), (T["l02e"], -0.04)])
    if T["w_home"] - 0.4 < t < T["w_sleep"] + 0.2:
        d["blink"] = 0.0
    if abs(t - T["w_sleep"] - 0.33) < 0.15:
        d["blink"] = _tw(t, [(T["w_sleep"] + 0.22, 0.0), (T["w_sleep"] + 0.3, 1.0),
                             (T["w_sleep"] + 0.36, 1.0), (T["w_sleep"] + 0.46, 0.0)])
    return d


def _cur_s4(t, T, d):
    # S4: points back toward the tunnel, looks back at him, hop-turns, rises to the sleeve
    d["expr"] = "pleading"
    if t < T["hop"] + 0.12:
        d["flip"] = True
        if t < T["pt_down"]:
            d["pose_from"], d["pose"] = "sit", "point"
            d["pose_mix"] = seg(t, T["pt_up"], T["pt_up"] + 0.32)
        else:
            d["pose_from"], d["pose"] = "point", "sit"
            d["pose_mix"] = seg(t, T["pt_down"], T["pt_down"] + 0.2)
        d["point_angle"] = 0.22 - _bump(t, T["pt_look"] + 0.35, T["pt_look"] + 0.6, 0.12)
        d["face"] = _tw(t, [(T["pt_up"], 0.85), (T["pt_look"], 0.85), (T["pt_look"] + 0.3, -1.0),
                            (T["hop"], -1.0), (T["hop"] + 0.12, 0.0)])
        # screen-space look: down the tunnel first, then back up at him
        d["look"] = _tw(t, [(T["pt_up"] + 0.1, (-0.85, -0.2)), (T["pt_look"] - 0.1, (-0.85, -0.2)),
                            (T["pt_look"] + 0.12, (0.6, -0.55))])
        d["ears"] = _tw(t, [(T["pt_up"], 0.62), (T["pt_up"] + 0.3, 0.72), (T["pt_look"] + 0.3, 0.6)])
    else:
        d["flip"] = False
        d["face"] = _tw(t, [(T["hop"] + 0.12, 0.0), (T["grab0"] + 0.2, 0.75)])
        d["look"] = (0.55, -0.6)
        d["ears"] = 0.6
    # the hop-turn: squash, hop (flip at the apex), land
    h0 = T["hop"]
    if h0 + 0.04 < t < h0 + 0.22:
        d["lift"] = 18 * math.sin(math.pi * seg(t, h0 + 0.04, h0 + 0.22))
    sq = -_bump(t, h0 - 0.06, h0 + 0.06, 0.08) + _bump(t, h0 + 0.06, h0 + 0.18, 0.06) \
        - _bump(t, h0 + 0.2, h0 + 0.32, 0.07)
    d["sq"] = (1.0 - sq * 0.6, 1.0 + sq)
    return d


def _cur_hold(t, T, d):
    """Holding his sleeve in its teeth through l03 / l04, then the hurt and the release."""
    d["flip"] = False
    d["expr"] = "pleading"
    if t < T["grab"]:
        d["pose_from"], d["pose"] = "sit", "tug_sleeve"
        d["pose_mix"] = seg(t, T["grab0"], T["grab"])
        d["face"] = _tw(t, [(T["hop"] + 0.12, 0.0), (T["grab0"] + 0.2, 0.75)])
    else:
        d["pose"] = "tug_sleeve"
        d["face"] = 0.75
    d["sleeve"] = t >= T["grab0"] + 0.15
    # gentle tugs, slowing to a still hold at "Look." (a time-warped clock drives the yank)
    tl = T["w_look"] - 0.05
    if t >= tl:
        a = min(t - tl, 0.45)
        d["tt"] = tl + a - (a * a) / (2 * 0.45) * 0.88 + max(0.0, t - tl - 0.45) * 0.12
    d["ears"] = _tw(t, [(T["grab"], 0.6), (T["w_sorry"], 0.6), (T["w_sorry"] + 0.5, 0.68),
                        (T["beat"] + 0.25, 0.68), (T["beat"] + 0.8, 0.6)])
    d["look"] = _tw(t, [(T["grab"], (0.55, -0.6)), (T["beat"] + 0.2, (0.55, -0.6)),
                        (T["beat"] + 0.5, (0.65, -0.5))])
    # ---- the hurt: ONE expression held (teary from tears=0), continuous controls ramp
    th = T["w_problem"]
    if t >= T["s7"] - 0.4:          # switched off screen (S6 is his close-up)
        d["expr"] = "teary"
        d["tears"] = (lerp(0.0, 0.6, smoothstep(seg(t, T["s7"] + 0.4, T["rel0"] - 0.1)))
                      + lerp(0.0, 0.3, smoothstep(seg(t, T["rel0"] + 0.25, T["s8"]))))
    if t >= th:
        k = seg(t, th, T["rel0"] + 0.35)
        d["ears"] = lerp(0.6, 0.03, ease_in_out(k))
        d["look"] = _tw(t, [(T["s7"] + 0.6, (0.65, -0.5)), (T["s7"] + 1.6, (0.2, 0.55))])
        d["tilt"] = _tw(t, [(T["s7"] + 0.75, 0.0), (T["s7"] + 1.8, 0.14), (T["s8"] - 0.4, 0.24)])
        d["face"] = _tw(t, [(T["rel0"] + 0.55, 0.75), (T["s8"] - 0.05, 0.15)])
        # the pull goes out of its body: it sags toward sitting, still holding on
        d["pose_from"], d["pose"] = "tug_sleeve", "sit"
        d["pose_mix"] = 0.38 * smoothstep(seg(t, T["s7"] + 0.3, T["rel0"]))
    if t >= T["rel0"]:
        d["pose_from"], d["pose"] = "tug_sleeve", "sit"
        d["pose_mix"] = lerp(0.38, 1.0, seg(t, T["rel0"], T["rel0"] + 0.45))
        d["sleeve"] = d["pose_mix"] < 0.48
    return d


def _cur_leave(t, T, d):
    # S8: gets up, walks away alone into the side tunnel, stops, looks back once, goes
    d["flip"] = True
    d["expr"] = "sad"
    d["ears"] = 0.05
    d["tears"] = 0.55
    d["look"] = (-0.2, 0.35)
    d["tilt"] = 0.12
    d["glow"] = 0.9
    t8 = T["s8"]
    d["face"] = _tw(t, [(t8, 0.15), (t8 + 0.4, 1.0)])
    vw = CUR_V * 1.5
    if t < T["lv_walk"]:
        d["pose_from"], d["pose"] = "sit", "stand"
        d["pose_mix"] = seg(t, t8 + 0.1, T["lv_walk"])
        d["tilt"] = 0.18
        return d
    tw_ = t - T["lv_walk"]
    acc = 0.25
    dist = vw * (tw_ - acc / 2 if tw_ > acc else tw_ * tw_ / (2 * acc))
    corr = CUR_X - MOUTH_X0
    if dist < corr:
        d["x"] = CUR_X - dist
        d["pose"] = "walk"
        d["pose_t"] = dist / CUR_V
        d["pose_from"], d["pose_mix"] = "stand", seg(tw_, 0.0, 0.3)
        return d
    # in the side tunnel: k from the mouth into the dark (stop + look back on the way)
    pt0 = corr / CUR_V
    if t < T["lv_stop"]:
        u = seg(t, T["lv_mouth"], T["lv_stop"])
        k = 0.09 * (u * (2.0 - u))
        pt = pt0 + (t - T["lv_mouth"]) * 1.2
    elif t < T["lv_fwd"] + 0.15:
        k = 0.09
        pt = pt0 + (T["lv_stop"] - T["lv_mouth"]) * 1.2
    else:
        k = 0.09 + 0.75 * seg(t, T["lv_fwd"] + 0.15, T["lv_gone"] + 0.4) ** 1.3
        pt = pt0 + (T["lv_stop"] - T["lv_mouth"]) * 1.2 + (t - T["lv_fwd"] - 0.15) * 1.2
    x, y, f = _depth(k)
    d.update(x=x, y=y, s=S * f, pose="walk", pose_t=pt)
    mix_stand = _ramp(t, T["lv_stop"] - 0.3, T["lv_stop"]) * (1 - _ramp(t, T["lv_fwd"], T["lv_fwd"] + 0.3))
    if mix_stand > 0.0:
        d["pose_from"], d["pose"], d["pose_mix"] = "walk", "stand", mix_stand
    # the look back (pupils first, then the head)
    d["face"] = _tw(t, [(T["lv_back"] + 0.1, 1.0), (T["lv_back"] + 0.45, -1.0), (T["lv_fwd"], -1.0),
                        (T["lv_fwd"] + 0.3, 1.0)])
    d["look"] = _tw(t, [(T["lv_back"], (-0.2, 0.35)), (T["lv_back"] + 0.2, (0.75, -0.2)),
                        (T["lv_fwd"], (0.7, -0.15)), (T["lv_fwd"] + 0.2, (-0.3, 0.3))])
    d["ears"] = _tw(t, [(T["lv_back"] + 0.2, 0.05), (T["lv_back"] + 0.5, 0.16), (T["lv_fwd"], 0.12),
                        (T["lv_fwd"] + 0.3, 0.04)])
    if T["lv_back"] + 0.27 <= t < T["lv_fwd"] + 0.15:
        d["expr"] = "teary"
        d["tears"] = 0.62
    d["clip"] = k > 0.11
    d["dark"] = 0.6 * smoothstep(seg(k, 0.05, 0.5))
    d["glow"] = lerp(0.9, 0.3, smoothstep(seg(k, 0.09, 0.6)))
    d["alpha"] = 1.0 - smoothstep(seg(k, 0.4, 0.8))
    if T["lv_back"] - 0.3 < t < T["lv_fwd"] + 0.4:      # no auto blink; one slow blink at the end
        d["blink"] = _tw(t, [(T["lv_fwd"] - 0.3, 0.0), (T["lv_fwd"] - 0.15, 1.0),
                             (T["lv_fwd"] + 0.0, 1.0), (T["lv_fwd"] + 0.15, 0.0)])
    return d


# ----------------------------------------------------------------------------
# drawing
# ----------------------------------------------------------------------------
_HOOD_COL = core.PAL["t_hoodie"]


def _sleeve_cuff(arm):
    """hold callback for tug_sleeve: a bit of his hoodie cuff between the jaws."""
    def fn(ctx, a):
        mx, my = a["mouth"]
        k = a["s"]
        ang = 0.9
        if arm is not None:
            (wx, wy), (ex, ey) = arm
            ang = math.atan2(ey - wy, ex - wx)
        with core.saved(ctx, mx, my, k, ang):
            core.rrect(ctx, -28, -17, 70, 34, 13)
            core.fill_stroke(ctx, _HOOD_COL, core.PAL["ink"], 5)
            ctx.move_to(-12, -13)
            ctx.line_to(-14, 13)
            core.stroke(ctx, core.PAL["t_hoodie_dk"], 4)
    return fn


def _mouth_path(c):
    mx, mt, mw, mh = M["mouth"]
    wall = M["wall_y"]
    c.move_to(mx, wall + 6)
    c.line_to(mx, mt + 110)
    c.curve_to(mx, mt, mx + mw, mt, mx + mw, mt + 110)
    c.line_to(mx + mw, wall + 6)
    c.close_path()


def _draw_cur(ctx, t, c, arm=None):
    hold = _sleeve_cuff(arm) if c["sleeve"] else None
    kw = dict(pose=c["pose"], expr=c["expr"], look=c["look"], glow=c["glow"], blink=c["blink"],
              flip=c["flip"], pose_t=c["pose_t"], face=c["face"], point_angle=c["point_angle"],
              hold=hold, tilt=c["tilt"], ears=c["ears"], tail_curl=c["tail_curl"], tears=c["tears"],
              pose_from=c["pose_from"], pose_mix=c["pose_mix"])

    def draw(cx):
        x, y = c["x"], c["y"]
        sx, sy = c["sq"]
        if sx != 1.0 or sy != 1.0 or c["lift"]:
            with core.saved(cx, x, y - c["lift"], (sx, sy)):
                return CR.draw_specimen(cx, 0, 0, c["s"], c["tt"], **kw)
        return CR.draw_specimen(cx, x, y, c["s"], c["tt"], **kw)

    if c["alpha"] <= 0.01:
        return {}
    if c["clip"]:
        ctx.save()
        _mouth_path(ctx)
        ctx.clip()
    grouped = c["alpha"] < 0.999 or c["dark"] > 0.01
    if grouped:
        ctx.push_group()
    out = draw(ctx) or {}
    if grouped:
        if c["dark"] > 0.01:     # deep in the side tunnel: darken the body (eyes re-lit below)
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ATOP)
            ctx.set_source_rgba(0.01, 0.015, 0.03, c["dark"])
            ctx.paint()
            ctx.restore()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(c["alpha"])
        if c["dark"] > 0.01 and out:
            r = 44 * c["s"]
            for e in ("eye_l", "eye_r"):
                if e in out:
                    core.radial_glow(ctx, out[e][0], out[e][1], r, "power", 1.1 * c["alpha"] * c["dark"])
    if c["clip"]:
        ctx.restore()
    return out


def _cur_mouth(t, c):
    """Curiosity's mouth anchor (world) for this frame, from a probe draw."""
    if not c["sleeve"]:
        return None
    a = _draw_cur(_probe_ctx(), t, dict(c, sleeve=False, clip=False, alpha=1.0, dark=0.0))
    return a.get("mouth")


def _bandage_glow(ctx, a, amt):
    """Faint teal glow along the bandaged forearm (their connection)."""
    if amt <= 0.01:
        return
    (ex, ey), (wx, wy) = a["elbow_r"][:2], a["wrist_r"][:2]
    mx, my = (ex * 0.55 + wx * 0.45), (ey * 0.55 + wy * 0.45)
    core.radial_glow(ctx, mx, my, 120 * S, "power", 0.24 * amt)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for w, al in ((30, 0.07), (16, 0.09), (7, 0.13)):
        ctx.move_to(ex + (wx - ex) * 0.12, ey + (wy - ey) * 0.12)
        ctx.line_to(ex + (wx - ex) * 0.88, ey + (wy - ey) * 0.88)
        core.stroke(ctx, core.alpha("power", al * amt), w * S)
    ctx.restore()


# ----------------------------------------------------------------------------
# shots
# ----------------------------------------------------------------------------
def _cam(t, T):
    """(shot id, cx, cy, zoom) for time t."""
    if t < T["s2"]:
        kx = ease_in_out(seg(t, 0.0, T["stop"] + 0.5))
        kz = ease_in_out(seg(t, 0.35, T["l01"] + 0.1))
        return 1, lerp(600, 935, kx), lerp(1150, 1180, kz), lerp(1.0, 1.75, kz)
    if t < T["s3"]:
        k = smoothstep(seg(t, T["s2"], T["s3"]))
        return 2, 1045, 1120, lerp(2.7, 2.82, k)
    if t < T["s4"]:
        return 3, 742, 1310, 3.1
    if t < T["s5"]:
        return 4, 850, 1250, 1.85
    if t < T["s6"]:
        k = smoothstep(seg(t, T["s5"], T["s6"]))
        return 5, 880, 1285, lerp(2.15, 2.22, k)
    if t < T["s7"]:
        return 6, 1030, 1110, 3.4
    if t < T["s8"]:
        k = smoothstep(seg(t, T["s7"], T["s8"]))
        return 7, 745, 1300, lerp(3.3, 3.45, k)
    if t < T["s8b"]:
        return 8, 700, 1160, 0.95
    if t < T["s9"]:
        return 81, 432, 1238, 2.4
    if t < T["s10"]:
        k = smoothstep(seg(t, T["s9"], T["s10"]))
        return 9, 1000, 1150, lerp(2.25, 2.4, k)
    k = ease_in_out(seg(t, T["s10"] + 0.6, T["end"]))
    return 10, lerp(870, 720, k), 1150, 1.12


def render(ctx, t, info):
    T = _T(info)
    shot, cx, cy, zoom = _cam(t, T)
    c = _cur(t, T)
    p = _tired(t, T, info, _cur_mouth(t, c))
    drip = t >= T["s8"] - 0.5
    t_set = t + ((1.82 - (T["s9"] + 0.5)) % 2.6)     # a drip lands just after the "alone" cut
    bandage_amt = 0.0
    if T["glow"] <= t <= T["arm1"] + 0.4:
        bandage_amt = 0.6 * _tw(t, [(T["glow"], 0.0), (T["glow"] + 0.4, 1.0), (T["glow"] + 0.8, 0.5),
                                    (T["arm1"] + 0.3, 0.0)])

    with core.camera(ctx, cx, cy, zoom):
        sets.service_tunnel(ctx, t_set, drip=drip)
        with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
            pk = {k: v for k, v in p.items() if k not in ("x", "y")}
            a = human.draw_person(ctx, "tired", p["x"], p["y"], S, t, **pk)
            _draw_cur(ctx, t, c, arm=(a["wrist_l"][:2], a["elbow_l"][:2]))
        if bandage_amt > 0:
            _bandage_glow(ctx, a, bandage_amt)
    fx.vignette(ctx, 0.3, inner=0.62)


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    T = _times(info)
    ev = []
    period = 0.5 / WALK_RATE
    # trudging steps on concrete (walk heel strikes at cycle phase .27 + n/2), the hood,
    # the drop onto the crate
    for n in range(0, 8):
        ts = (0.31 + 0.5 * n - 0.29) / WALK_RATE
        if 0.0 <= ts < T["stop"] + 0.05:
            ev.append((ts, "footstep", -7.0, -0.3 + 0.1 * n))
    ev.append((T["stop"] + 0.3, "footstep", -11.0, 0.05))
    ev.append((0.55, "cloth_rustle", -5.0, -0.3))
    ev.append((T["land"] - 0.02, "body_thud", -13.0, 0.05))
    ev.append((T["land"] + 0.02, "chair_creak", -9.0, 0.05))
    # slump: sigh, hands rubbing his face
    ev.append((T["slump"] + 0.05, "sigh", 0.0, 0.0))
    ev.append((T["slump"] + 0.6, "cloth_rustle", -8.0, 0.0))
    # Curiosity: ears perk at "go home", a pleading chitter at the point, the hop, the sleeve
    ev.append((T["w_home"] - 0.03, "ears_perk", -2.0, -0.2))
    ev.append((T["pt_up"] + 0.05, "creature_chitter", -5.0, -0.25))
    ev.append((T["hop"] + 0.2, "footstep", -16.0, -0.2))
    ev.append((T["grab"] - 0.05, "cloth_rustle", -8.0, -0.15))
    # the hurt: a small sad coo as it lets go
    ev.append((T["rel0"] + 0.2, "creature_chirp_sad", -8.0, -0.1))
    ev.append((T["rel0"] + 0.15, "cloth_rustle", -12.0, 0.0))
    # alone: the drip (synced to the visible drip), the bandage's faint "ping"
    for n in range(-3, 3):
        tv = T["s9"] + 0.5 + n * 2.6
        if T["s8"] - 0.5 <= tv < T["end"] - 0.3:
            g = -3.0 if n == 0 else (-9.0 if n > 0 else -11.0)
            ev.append((tv, "drip", g, -0.3))
    ev.append((T["glow"] + 0.05, "sonar_ping_small", -11.0, 0.1))
    # getting up and trudging after it
    ev.append((T["up0"] + 0.3, "chair_creak", -8.0, 0.05))
    ev.append((T["up0"] + 0.4, "cloth_rustle", -8.0, 0.0))
    for n in range(0, 12):
        tw = T["walk2"] + (0.81 + 0.5 * n - 0.5) / WALK_RATE
        if tw < T["end"] - 0.1:
            ev.append((tw, "footstep", -8.0, -0.15))
    return [e for e in ev if 0.0 <= e[0] < T["end"]]
