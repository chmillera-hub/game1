"""s04 — "Not my problem" (music: lonely).

A quiet HushCorp service tunnel lit by dim emergency lamps. Tiredness trudges in
out of the dark, pushes his hood back in the first light, drops onto a crate and
gives up. Curiosity points back toward the pods and tugs his sleeve; he tells it,
gently, that its family is not his problem. The hurt lands on Curiosity's face
(ears lowering degree by degree, tears), it lets go of his sleeve and walks off
alone into the dark side tunnel, looking back once. Alone with a drip, he looks
at his bandage (a faint teal glow), groans, and follows.

All timing comes from info.cue(...) / info.line(...). World = sets.service_tunnel.

Shot list (cue-relative; see SHOTS below)
  S1  arrive     0 .. l01.end+.3     slow push-in: walk in, hood back, turn, drop onto
                                     the crate; Curiosity trots in; "Okay. I'm done."
  S2  slump      .. l02 word 7       medium: head hangs, rubs his face, l02 part 1
  S3  listen     .. tug-.1           Curiosity: ears shoot up at "go home", pleading,
                                     eyes slide toward the tunnel
  S4  point      .. l03-.15          two-shot: points to the tunnel, looks back at him,
                                     hop-turns, takes his sleeve, gentle tugs
  S5  sorry      .. l04-.15          closer two-shot: "Look. I'm sorry..." gentle; beat:
                                     his eyes slide away
  S6  problem    .. l04.end+.15      his close-up, not looking at it
  S7  hurt       .. leave+.1         Curiosity CU: ears lower degree by degree, tears,
                                     lets go of the sleeve, head turns away
  S8  leave      .. alone+1.65       wide: it walks off into the dark side tunnel,
                                     stops, looks back once, goes; he never looks up
  S9  alone      .. l05.end+.1       medium: drip; lifts his bandaged forearm, faint
                                     teal glow, lip press, looks down the tunnel; "Ugh"
  S10 follow     .. end              stands up and trudges after it
"""
import math

import cairocffi as cairo

from engine import core, sets, human, fx
from engine import creatures as CR
from engine.core import clamp, lerp, seg, smoothstep, ease_in_out, ease_out, ease_in, tween

try:
    from audio import sfx as _sfx
except Exception:      # audio deps are only needed by the mixer
    _sfx = None

M = sets.TUNNEL_MARKS
S = 0.75                       # people / creature scale in the tunnel world
SEAT_X, FEET_Y = 1080, 1500    # Tiredness on the seat crate (ground point)
CUR_X = 735                    # Curiosity's spot beside him (screen-left = toward the tunnel)
CUR_Y = 1506                   # a hair in front of his feet line (drawn after him)
WALK_RATE = 0.8                # tired trudge (fraction of the walk cycle rate)
MOUTH_X0 = 470                 # Curiosity's corridor-floor point in front of the side tunnel

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
    """keys [(t, value, trans), ...] -> (prev, cur, k) with per-key transitions (eased)."""
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, 0.25
    for k in keys:
        if t >= k[0]:
            prev, cur, start, tr = cur, k[1], k[0], (k[2] if len(k) > 2 else 0.25)
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _pose_of(tr):
    a, b, k = tr
    if k >= 0.999 or a == b:
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
    # --- arrival (S1): fixed choreography before the first line, scaled to the room it has
    T["stop"] = min(1.65, T["l01"] - 1.5)          # walk ends at the crate
    T["sit0"] = T["stop"] + 0.4                    # starts lowering onto the crate
    T["land"] = T["sit0"] + 0.55                   # butt lands
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
    T["pt_look"] = t4 + 0.45                       # head turns back to him
    T["pt_down"] = max(t4 + 1.0, T["l03"] - 1.55)  # paw lowers
    T["hop"] = T["pt_down"] + 0.2                  # hop-turn (flip at hop + 0.12)
    T["grab0"] = T["hop"] + 0.27                   # rises into the sleeve tug
    T["grab"] = T["grab0"] + 0.3                   # sleeve in its teeth
    # --- hurt (S7)
    T["rel0"] = T["leave"] - 1.2                   # lets go of the sleeve
    # --- leave (S8)
    t8 = T["s8"]
    T["lv_walk"] = t8 + 0.55
    T["lv_mouth"] = T["lv_walk"] + 0.25 + (CUR_X - MOUTH_X0) / (CR.SPEC_WALK_SPEED * S * 1.5)
    T["lv_stop"] = T["lv_mouth"] + 0.5
    T["lv_back"] = T["lv_stop"] + 0.1              # looks back
    T["lv_fwd"] = T["lv_back"] + 0.95              # turns forward again
    T["lv_gone"] = T["lv_fwd"] + 0.95
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
    k = (id(info), info.dur)
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
    face = {}
    look = (0.0, 0.25)
    blink = None
    hood = 0.0
    reach = {}

    # ---------------- arrival: walk in, hood back, turn, sit -----------------
    if t < T["sit0"] + 0.6:
        pt_walk = WALK_RATE * min(t, stop) + 0.29
        x = x_stop - v * (stop - min(t, stop))
        if t < stop:
            pose = _WALK_FRONT if 0.15 < t < 1.45 else "walk"
        else:
            # stop: walk (frozen) -> stand -> sit, turning to face left (toward the tunnel)
            k1 = _ramp(t, stop, stop + 0.3)
            k2 = _ramp(t, T["sit0"], T["land"], ease_in)
            if k2 <= 0.0:
                pose = _pose_of(("walk", "stand", k1))
            else:
                pose = _pose_of(("stand", _sitp(), k2))
            x = lerp(x_stop, SEAT_X, _ramp(t, stop + 0.05, T["sit0"] + 0.2))
        turn = _tw(t, [(stop - 0.05, 1.0), (stop + 0.35, 0.15), (T["sit0"] + 0.25, -0.6)])
        hood = _tw(t, [(0.45, 1.0), (1.15, 0.0)])
        # hood push-back: near (l) hand up to the hood top, sweeping back over the crown
        if 0.15 < t < 1.6:
            hp = seg(t, 0.45, 1.15)
            ang = lerp(1.25, 2.45, smoothstep(hp))
            w = _ramp(t, 0.15, 0.45) * (1.0 - _ramp(t, 1.15, 1.55))
            hx, hy = x + 41, FEET_Y - 581                  # head centre while walking at turn 1 (s .75)
            r = 125 * S
            reach["l"] = (hx + r * math.cos(ang), hy - 30 - r * math.sin(ang), w)
        expr = _track(t, [(0.0, "annoyed"), (0.95, "squint", 0.3), (1.6, "bored", 0.4),
                          (T["land"], "sigh", 0.2), (T["land"] + 0.55, "bored", 0.35)])
        look = _tw(t, [(1.2, (0.2, 0.2)), (stop - 0.1, (0.3, 0.45)), (stop + 0.25, (-0.2, 0.55)),
                       (T["land"], (-0.25, 0.6)), (T["land"] + 0.5, (-0.1, 0.45))])
        face = {"lid": 0.06 * _bump(t, 0.9, 1.6)}
        if t >= T["land"]:
            pose = _sitp(nod=0.34 + _bump(t, T["land"], T["land"] + 0.5, 0.12),
                         hunch=0.65 + _bump(t, T["land"], T["land"] + 0.6, 0.12))
        return dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pt_walk, turn=turn, expr=_pose_of(expr),
                    look=look, face=face, hood=hood, reach=reach or None, blink=blink,
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

    # slump: both hands up to rub his face
    rub_w = _ramp(t, T["slump"] + 0.5, T["slump"] + 0.95) * (1 - _ramp(t, T["l02"] - 0.45, T["l02"] - 0.1))
    if rub_w > 0.0:
        rb = math.sin((t - T["slump"]) * 2 * math.pi * 1.6) * 7 * _ramp(t, T["slump"] + 0.9, T["slump"] + 1.1)
        reach["l"] = (957 + rb, 1128 - rb * 0.3, rub_w)
        reach["r"] = (1008 - rb * 0.8, 1121 + rb * 0.3, rub_w)
        pose = dict(pose, al_layer="front", ar_layer="front")

    # tug: his far (l) hand is pulled out by the sleeve in Curiosity's teeth
    if cur_mouth is not None:
        gw = _ramp(t, T["grab"] - 0.12, T["grab"] + 0.12) * (1 - _ramp(t, T["rel0"] + 0.05, T["rel0"] + 0.5, ease_in))
        if gw > 0.0:
            mx, my = cur_mouth
            reach["l"] = (mx - 16 * S, my + 22 * S, gw)

    # alone: lifts the bandaged (near, r) forearm to look at it
    aw = _ramp(t, T["arm0"], T["arm0"] + 0.5) * (1 - _ramp(t, T["arm1"], T["arm1"] + 0.45))
    if aw > 0.0:
        reach["r"] = (948, 1206 + 4 * math.sin(t * 1.3), aw)

    # standing up and trudging after it
    if t >= T["up0"] + 0.25:
        k = _ramp(t, T["up0"] + 0.25, T["up1"], ease_out)
        pose = _pose_of((pose, "stand", k))
        turn = lerp(-0.6, -1.0, k)
        if t >= T["walk2"]:
            pose = _pose_of(("stand", "walk", _ramp(t, T["walk2"], T["walk2"] + 0.3)))
            tw_ = t - T["walk2"]
            x = SEAT_X - _tired_walk_speed() * max(0.0, tw_ - 0.15)
        kw["pose_t"] = WALK_RATE * max(0.0, t - T["walk2"]) + 0.5

    # --- eyes
    look = _tw(t, [
        (T["land"] + 0.5, (-0.1, 0.45)), (T["w_okay"], (-0.15, 0.5)), (T["l01e"], (-0.1, 0.6)),
        (T["l02"], (-0.05, 0.3)), (T["w_I2"], (0.1, 0.35)), (T["w_sleep"] + 0.3, (0.0, 0.5)),
        # S4: follows the pointing paw toward the tunnel, then back to the creature
        (T["pt_up"] + 0.15, (-0.25, 0.5)), (T["pt_up"] + 0.35, (-0.9, 0.15)),
        (T["pt_look"] + 0.25, (-0.9, 0.15)), (T["pt_look"] + 0.45, (-0.55, 0.6)),
        (T["grab"], (-0.55, 0.65)), (T["grab"] + 0.3, (-0.6, 0.85)),       # looks down at the sleeve
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

    # --- expressions (keyed, 0.2-0.35 s transitions)
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
        {"press": _bump(t, T["beat"] + 0.45, T["l04"] - 0.05, 0.45) + _bump(t, T["l04e"] + 0.05, T["l04e"] + 0.85, 0.5)
         + _bump(t, T["press"], T["press"] + 0.75, 0.55) + _bump(t, T["slump"] - 0.3, T["slump"] + 0.2, 0.3)},
        # alone: inner brows up a hair at the glow
        {"brow_ang": _bump(t, T["glow"] - 0.1, T["arm1"] + 0.6, 0.22)},
        {"frown": _bump(t, T["l04e"] + 0.1, T["s7"] + 0.3, 0.25)},
    )
    # slow blinks on judgement beats
    blink = None
    for (b0, hold) in ((T["w_sleep"] + 0.05, 0.25), (T["w_done"] + 0.15, 0.15), (T["l04e"] + 0.35, 0.3)):
        if b0 - 0.05 <= t <= b0 + 0.35 + hold + 0.4:
            blink = _tw(t, [(b0, 0.0), (b0 + 0.3, 1.0), (b0 + 0.3 + hold, 1.0), (b0 + 0.65 + hold, 0.0)])
    if T["l05"] - 0.1 <= t <= T["l05e"] + 0.3:      # eyes shut through the groan
        blink = _tw(t, [(T["l05"] - 0.1, 0.0), (T["l05"] + 0.15, 1.0), (T["l05e"] - 0.1, 1.0), (T["l05e"] + 0.3, 0.0)])
    return dict(kw, x=x, y=FEET_Y, pose=pose, turn=turn, expr=_pose_of(expr), look=look, face=face,
                hood=0.0, reach=reach or None, blink=blink, mouth=info.mouth("tired", t))


# ----------------------------------------------------------------------------
# CURIOSITY
# ----------------------------------------------------------------------------
def _cur(t, T):
    """World-space draw kwargs for Curiosity (+ 'clip' flag, 'alpha', 'hop' squash)."""
    s = S
    d = dict(x=CUR_X, y=CUR_Y, s=s, pose="sit", expr="calm", flip=False, face=None, look=(0.45, -0.55),
             ears=0.5, tears=None, tilt=0.0, tail_curl=0.0, glow=1.0, pose_t=None, pose_from=None,
             pose_mix=1.0, point_angle=0.0, blink=None, sq=(1.0, 1.0), lift=0.0, alpha=1.0, clip=False,
             tt=t, sleeve=False)
    vcy = CR.SPEC_WALK_SPEED * s
    # ---------------- S1: trots in after him, sits beside the crate ------------
    if t < T["s4"]:
        ta, tb = 0.35, T["land"] - 0.25
        u = smoothstep(seg(t, ta, tb)) * 0.6 + seg(t, ta, tb) * 0.4
        x0 = 330
        d["x"] = lerp(x0, CUR_X, u)
        dist = d["x"] - x0
        if t < tb:
            d["pose"] = "walk"
            d["pose_t"] = dist / vcy
        else:
            d["pose_from"], d["pose"] = "stand", "sit"
            d["pose_mix"] = seg(t, tb, tb + 0.4)
        d["look"] = _tw(t, [(1.0, (0.6, -0.2)), (tb, (0.5, -0.5)), (T["land"], (0.45, -0.6))])
        d["tilt"] = _tw(t, [(T["land"] + 0.2, 0.0), (T["land"] + 0.5, -0.12), (T["l01"], -0.12),
                            (T["w_done"], 0.0), (T["w_done"] + 0.4, 0.06), (T["slump"] + 0.6, 0.08)])
        d["ears"] = _tw(t, [(T["land"], 0.55), (T["w_done"], 0.55), (T["w_done"] + 0.5, 0.44),
                            (T["w_home"] - 0.05, 0.44)])
        # S3: "go home" -> ears shoot up; "sleep" -> worried, pleading; eyes slide to the tunnel
        if t >= T["w_home"] - 0.05:
            k = ease_out(seg(t, T["w_home"] - 0.05, T["w_home"] + 0.17))
            d["ears"] = lerp(0.44, 0.92, core.ease_out_back(seg(t, T["w_home"] - 0.05, T["w_home"] + 0.2)))
            d["expr"] = "surprised_soft"
            d["look"] = (0.4, -0.65)
            if t >= T["w_sleep"] + 0.15:
                d["ears"] = lerp(0.92, 0.6, _ramp(t, T["w_sleep"] + 0.15, T["w_sleep"] + 0.6))
            if t >= T["w_sleep"] + 0.3:
                d["expr"] = "pleading"
            d["look"] = _tw(t, [(T["w_sleep"] + 0.4, (0.4, -0.65)), (T["l02e"] - 0.1, (-0.85, -0.05)),
                                (T["l02e"] + 0.5, (-0.9, -0.1))])
            d["face"] = _tw(t, [(T["l02e"] + 0.05, 1.0), (T["l02e"] + 0.45, 0.25)])
            d["tilt"] = _tw(t, [(T["w_home"], 0.06), (T["w_home"] + 0.2, -0.06), (T["l02e"], -0.04)])
        d["blink"] = _tw(t, [(T["w_sleep"] + 0.22, 0.0), (T["w_sleep"] + 0.3, 1.0), (T["w_sleep"] + 0.36, 1.0),
                             (T["w_sleep"] + 0.46, 0.0)]) if abs(t - T["w_sleep"] - 0.33) < 0.15 else None
        return d

    # ---------------- S4: points to the tunnel, hop-turns, takes his sleeve ----
    if t < T["s7"] - 1e-6 or t < T["grab0"]:
        if t < T["hop"] + 0.12:
            d["flip"] = True
            d["expr"] = "pleading"
            if t < T["pt_down"]:
                d["pose_from"], d["pose"] = "sit", "point"
                d["pose_mix"] = seg(t, T["pt_up"], T["pt_up"] + 0.32)
            else:
                d["pose_from"], d["pose"] = "point", "sit"
                d["pose_mix"] = seg(t, T["pt_down"], T["pt_down"] + 0.2)
            d["point_angle"] = -0.5 + _bump(t, T["pt_look"] + 0.35, T["pt_look"] + 0.6, 0.14)
            d["face"] = _tw(t, [(T["pt_up"], 0.6), (T["pt_look"], 0.6), (T["pt_look"] + 0.3, -1.0),
                                (T["hop"], -1.0), (T["hop"] + 0.12, 0.0)])
            # screen-space look: tunnel (up-left) first, then back up at him (right/up)
            d["look"] = _tw(t, [(T["pt_up"] + 0.1, (-0.85, -0.25)), (T["pt_look"] - 0.1, (-0.85, -0.25)),
                                (T["pt_look"] + 0.12, (0.6, -0.55))])
            d["ears"] = _tw(t, [(T["pt_up"], 0.62), (T["pt_up"] + 0.3, 0.72), (T["pt_look"] + 0.3, 0.6)])
        else:
            d["flip"] = False
            d["expr"] = "pleading"
            d["face"] = _tw(t, [(T["hop"] + 0.12, 0.0), (T["grab0"] + 0.2, 0.75)])
            d["look"] = (0.55, -0.6)
            d["ears"] = 0.6
            if t < T["grab0"]:
                d["pose"] = "sit"
            else:
                d["pose_from"], d["pose"] = "sit", "tug_sleeve"
                d["pose_mix"] = seg(t, T["grab0"], T["grab"])
                d["sleeve"] = t >= T["grab0"] + 0.15
        # the hop-turn: squash, hop (flip at the apex), land
        h0 = T["hop"]
        d["lift"] = 18 * math.sin(math.pi * seg(t, h0 + 0.04, h0 + 0.22)) if h0 + 0.04 < t < h0 + 0.22 else 0.0
        sq = -_bump(t, h0 - 0.06, h0 + 0.06, 0.08) + _bump(t, h0 + 0.06, h0 + 0.18, 0.06) \
            - _bump(t, h0 + 0.2, h0 + 0.32, 0.07)
        d["sq"] = (1.0 - sq * 0.6, 1.0 + sq)
        if t >= T["grab0"]:
            d.update(_cur_hold(t, T, d))
        return d

    # ---------------- S7: the hurt -------------------------------------------------
    if t < T["s8"]:
        d.update(_cur_hold(t, T, d))
        return d

    # ---------------- S8: walks away into the dark, looks back once ---------------
    d["flip"] = True
    d["expr"] = "sad"
    d["ears"] = 0.05
    d["tears"] = 0.55
    d["look"] = (-0.2, 0.35)
    t8 = T["s8"]
    d["face"] = _tw(t, [(t8, 0.15), (t8 + 0.4, 1.0)])
    vw = vcy * 1.5
    if t < T["lv_walk"]:
        d["pose_from"], d["pose"] = "sit", "stand"
        d["pose_mix"] = seg(t, t8 + 0.1, T["lv_walk"])
        d["tilt"] = 0.18
        return d
    # distance walked along the corridor floor, then into the side tunnel (k)
    tw_ = t - T["lv_walk"]
    acc = 0.25
    dist = vw * (tw_ - acc / 2 if tw_ > acc else tw_ * tw_ / (2 * acc))
    corr = CUR_X - MOUTH_X0
    walking = True
    if dist < corr:
        d["x"] = CUR_X - dist
        d["pose"] = "walk"
        d["pose_t"] = dist / vcy
        d["pose_from"], d["pose_mix"] = "stand", seg(tw_, 0.0, 0.3)
        k = 0.0
    else:
        # inside: k from the mouth into the dark (stop + look back on the way)
        if t < T["lv_stop"]:
            k = 0.09 * smoothstep(seg(t, T["lv_mouth"], T["lv_stop"])) * 0.5 + 0.09 * seg(t, T["lv_mouth"], T["lv_stop"]) * 0.5
        elif t < T["lv_fwd"] + 0.15:
            k = 0.09
            walking = False
        else:
            k = 0.09 + 0.75 * ease_in(seg(t, T["lv_fwd"] + 0.15, T["lv_gone"] + 0.4)) ** 0.8
        f = 1.0 / (1.0 + 5.0 * k)
        d["x"] = 300 + (MOUTH_X0 - 300) * f
        d["y"] = 1010 + (CUR_Y - 1010) * f
        d["s"] = s * f
        d["pose"] = "walk"
        d["pose_t"] = corr / vcy + max(0.0, (t - T["lv_mouth"])) * 1.2
        if not walking or (T["lv_stop"] - 0.25 < t < T["lv_fwd"] + 0.3):
            d["pose_from"], d["pose"] = "walk", "stand"
            d["pose_mix"] = _ramp(t, T["lv_stop"] - 0.25, T["lv_stop"] + 0.05) * (1 - _ramp(t, T["lv_fwd"], T["lv_fwd"] + 0.3))
            d["pose_t"] = corr / vcy + (T["lv_stop"] - T["lv_mouth"]) * 1.2 if t < T["lv_fwd"] else d["pose_t"]
        # the look back
        d["face"] = _tw(t, [(T["lv_back"], 1.0), (T["lv_back"] + 0.35, -1.0), (T["lv_fwd"], -1.0),
                            (T["lv_fwd"] + 0.3, 1.0)])
        d["look"] = _tw(t, [(T["lv_back"] + 0.1, (-0.2, 0.35)), (T["lv_back"] + 0.35, (0.75, -0.2)),
                            (T["lv_fwd"], (0.7, -0.15)), (T["lv_fwd"] + 0.2, (-0.3, 0.3))])
        d["clip"] = k > 0.11
        d["glow"] = lerp(0.8, 0.25, smoothstep(seg(k, 0.09, 0.6)))
        d["alpha"] = 1.0 - smoothstep(seg(k, 0.42, 0.78))
        d["blink"] = _tw(t, [(T["lv_back"] + 0.5, 0.0), (T["lv_back"] + 0.62, 1.0), (T["lv_back"] + 0.72, 1.0),
                             (T["lv_back"] + 0.86, 0.0)]) if T["lv_back"] + 0.45 < t < T["lv_back"] + 0.9 else None
        d["k"] = k
    d["glow"] = d["glow"] if "k" in d else 0.9
    d["tilt"] = 0.12
    return d


def _cur_hold(t, T, d):
    """Holding his sleeve in its teeth through l03 / l04, then the hurt and the release."""
    o = {}
    o["flip"] = False
    o["pose"] = "tug_sleeve" if t >= T["grab"] else d["pose"]
    if t >= T["grab"]:
        o["pose_from"], o["pose_mix"] = None, 1.0
    # gentle tugs, slowing to a still hold at "Look." (time-warped clock for the yank)
    tl = T["w_look"] - 0.05
    if t < tl:
        tt = t
    else:
        # rate eases 1 -> 0.12 over 0.45 s, keeping a little life
        a = min(t - tl, 0.45)
        tt = tl + a - (a * a) / (2 * 0.45) * 0.88 + max(0.0, t - tl - 0.45) * 0.12
    o["tt"] = tt
    o["expr"] = "pleading"
    if t >= T["grab0"] + 0.2:
        o["face"] = 0.75
    o["ears"] = _tw(t, [(T["grab"], 0.6), (T["w_sorry"], 0.6), (T["w_sorry"] + 0.5, 0.68),
                        (T["beat"] + 0.25, 0.68), (T["beat"] + 0.8, 0.6)])
    o["tail_curl"] = 0.0
    o["sleeve"] = t >= T["grab0"] + 0.15
    o["look"] = _tw(t, [(T["beat"] + 0.2, (0.55, -0.6)), (T["beat"] + 0.5, (0.65, -0.5))])
    # ---- the hurt: ONE expression held (teary from tears=0), continuous controls ramp
    th = T["w_problem"]
    if t >= T["s7"] - 0.4:
        o["expr"] = "teary"
        o["tears"] = (lerp(0.0, 0.6, smoothstep(seg(t, T["s7"] + 0.4, T["rel0"] - 0.1)))
                      + lerp(0.0, 0.3, smoothstep(seg(t, T["rel0"] + 0.25, T["s8"]))))
    if t >= th:
        k = seg(t, th, T["rel0"] + 0.35)
        o["ears"] = lerp(0.6, 0.03, ease_in_out(k))
        o["look"] = _tw(t, [(T["s7"] + 0.6, (0.65, -0.5)), (T["s7"] + 1.6, (0.2, 0.55))])
        o["tilt"] = _tw(t, [(T["s7"] + 0.75, 0.0), (T["s7"] + 1.8, 0.14), (T["s8"] - 0.4, 0.24)])
        o["face"] = _tw(t, [(T["rel0"] + 0.55, 0.75), (T["s8"] - 0.05, 0.15)])
    if t >= T["rel0"]:
        o["pose_from"], o["pose"] = "tug_sleeve", "sit"
        o["pose_mix"] = seg(t, T["rel0"], T["rel0"] + 0.5)
        o["sleeve"] = o["pose_mix"] < 0.45
    return o


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


def _draw_cur(ctx, t, c, arm=None, cam_zoom=1.0):
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

    out = {}
    if c["clip"]:
        ctx.save()
        mx, mt, mw, mh = M["mouth"]
        _mouth_path(ctx, mx, mt, mw)
        ctx.clip()
    if c["alpha"] < 0.999:
        if c["alpha"] > 0.01:
            ctx.push_group()
            out = draw(ctx)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(c["alpha"])
    else:
        out = draw(ctx)
    if c["clip"]:
        ctx.restore()
    return out or {}


def _mouth_path(c, mx, mt, mw):
    wall = M["wall_y"]
    c.move_to(mx, wall + 6)
    c.line_to(mx, mt + 110)
    c.curve_to(mx, mt, mx + mw, mt, mx + mw, mt + 110)
    c.line_to(mx + mw, wall + 6)
    c.close_path()


def _cur_mouth(t, c):
    """Curiosity's mouth anchor (world) for this frame, from a probe draw."""
    if not (c["sleeve"] or c["pose"] == "tug_sleeve" or c["pose_from"] == "tug_sleeve"):
        return None
    ctx = _probe_ctx()
    a = _draw_cur(ctx, t, dict(c, sleeve=False, clip=False, alpha=1.0))
    return a.get("mouth")


def _bandage_glow(ctx, a, amt, t):
    """Faint teal glow along the bandaged forearm (their connection)."""
    if amt <= 0.01:
        return
    (ex, ey), (wx, wy) = a["elbow_r"][:2], a["wrist_r"][:2]
    mx, my = (ex * 0.55 + wx * 0.45), (ey * 0.55 + wy * 0.45)
    core.radial_glow(ctx, mx, my, 120 * S, "power", 0.28 * amt)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for w, al in ((26, 0.10), (14, 0.16), (6, 0.32)):
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
        k = ease_in_out(seg(t, 0.4, T["l01"] + 0.2))
        return 1, lerp(1000, 935, k), lerp(1190, 1180, k), lerp(1.35, 1.75, k)
    if t < T["s3"]:
        k = smoothstep(seg(t, T["s2"], T["s3"]))
        return 2, 990, 1145, lerp(2.4, 2.52, k)
    if t < T["s4"]:
        return 3, 790, 1290, 2.7
    if t < T["s5"]:
        return 4, 905, 1250, 1.6
    if t < T["s6"]:
        k = smoothstep(seg(t, T["s5"], T["s6"]))
        return 5, 905, 1195, lerp(2.0, 2.1, k)
    if t < T["s7"]:
        return 6, 1000, 1145, 3.0
    if t < T["s8"]:
        k = smoothstep(seg(t, T["s7"], T["s8"]))
        return 7, 795, 1300, lerp(3.25, 3.45, k)
    if t < T["s9"]:
        return 8, 700, 1160, 0.95
    if t < T["s10"]:
        k = smoothstep(seg(t, T["s9"], T["s10"]))
        return 9, 1000, 1150, lerp(2.25, 2.4, k)
    k = ease_in_out(seg(t, T["s10"] + 0.6, T["end"]))
    return 10, lerp(870, 720, k), 1150, 1.12


def render(ctx, t, info):
    T = _T(info)
    shot, cx, cy, zoom = _cam(t, T)
    c = _cur(t, T)
    cm = _cur_mouth(t, c)
    p = _tired(t, T, info, cm)
    drip = t >= T["s8"] - 0.5
    t_set = t + ((1.82 - (T["s9"] + 0.5)) % 2.6)     # a drip lands just after the "alone" cut
    bandage_amt = _tw(t, [(T["glow"], 0.0), (T["glow"] + 0.35, 1.0), (T["glow"] + 0.75, 0.55),
                          (T["arm1"] + 0.3, 0.0)]) if T["glow"] <= t <= T["arm1"] + 0.4 else 0.0

    with core.camera(ctx, cx, cy, zoom):
        sets.service_tunnel(ctx, t_set, drip=drip)
        with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
            pk = {k: v for k, v in p.items() if k not in ("x", "y")}
            a = human.draw_person(ctx, "tired", p["x"], p["y"], S, t, **pk)
            arm = (a["wrist_l"][:2], a["elbow_l"][:2])
            _draw_cur(ctx, t, c, arm=arm, cam_zoom=zoom)
        if bandage_amt > 0:
            _bandage_glow(ctx, a, bandage_amt, t)
    fx.vignette(ctx, 0.35, inner=0.62)


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    T = _times(info)
    ev = []
    # trudging steps on concrete (walk contacts), the hood, the drop onto the crate
    period = 0.5 / WALK_RATE
    for n in range(0, 8):                      # heel strikes at cycle phase .27 + n/2
        ts = (0.27 + 0.5 * n - 0.29) / WALK_RATE
        if 0.0 <= ts < T["stop"] + 0.05:
            ev.append((ts, "footstep", -7.0, -0.1))
    ev.append((T["stop"] + 0.3, "footstep", -11.0, 0.0))
    ev.append((0.5, "cloth_rustle", -5.0, -0.1))
    ev.append((T["land"] - 0.02, "body_thud", -13.0, 0.05))
    ev.append((T["land"] + 0.02, "chair_creak", -9.0, 0.05))
    # slump: sigh, hands rubbing his face
    ev.append((T["slump"] + 0.05, "sigh", 0.0, 0.0))
    ev.append((T["slump"] + 0.6, "cloth_rustle", -8.0, 0.0))
    # Curiosity: ears perk at "go home", a pleading chitter at the point, the sleeve grab
    ev.append((T["w_home"] - 0.03, "ears_perk", -2.0, -0.2))
    ev.append((T["pt_up"] + 0.05, "creature_chitter", -5.0, -0.25))
    ev.append((T["hop"] + 0.2, "footstep", -16.0, -0.2))
    ev.append((T["grab"] - 0.05, "cloth_rustle", -8.0, -0.15))
    # the hurt: a small sad coo as it lets go
    ev.append((T["rel0"] + 0.2, "creature_chirp_sad", -8.0, -0.1))
    ev.append((T["rel0"] + 0.15, "cloth_rustle", -12.0, 0.0))
    # alone: the drip (synced to the visible drip), the bandage's faint "ping"
    off = (1.82 - (T["s9"] + 0.5)) % 2.6
    for n in range(-3, 3):
        tdrip = T["s9"] + 0.5 + n * 2.6 - 0.0
        tv = tdrip
        if T["s8"] - 0.5 <= tv < T["end"] - 0.3:
            g = {0: -3.0}.get(n, -9.0 if n > 0 else -10.0)
            ev.append((tv, "drip", g, -0.3))
    ev.append((T["glow"] + 0.05, "sonar_ping_small", -11.0, 0.1))
    # getting up and trudging after it
    ev.append((T["up0"] + 0.3, "chair_creak", -8.0, 0.05))
    ev.append((T["up0"] + 0.4, "cloth_rustle", -8.0, 0.0))
    for n in range(0, 12):
        tw = T["walk2"] + (0.77 + 0.5 * n - 0.5) / WALK_RATE + 0.15
        if tw < T["end"] - 0.1:
            ev.append((tw, "footstep", -8.0, -0.15))
    return [e for e in ev if 0.0 <= e[0] < T["end"]]
