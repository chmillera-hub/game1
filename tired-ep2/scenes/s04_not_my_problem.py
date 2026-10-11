"""s04 — "Not my problem" (music: lonely).  Revision 2 (honest, caring, overwhelmed).

A quiet HushCorp service tunnel lit by dim emergency lamps. Tiredness trudges out
of the dark side tunnel (the way back to the shaft and the pods), reaches back and
pulls his hood off in the first light, drops onto a crate. He is not dismissive,
he is overwhelmed: he tells Curiosity he has no bandwidth, that he fell out of a
building today, that he has to take care of himself first. Curiosity points back
toward the pods and takes his sleeve in its paws. He means it when he says what
HushCorp is doing to its family is wrong (its ears lift with hope), but he can't
see a way to help without somebody getting hurt. "Maybe me." It hears "not right
now": the ears lower degree by degree, tears, it lets go of his sleeve and walks
into the dark side tunnel, stops a short way in and looks back once. Alone with a
drip, he looks at his bandage (a faint teal glow), groans, and follows; its two
teal eyes are still glowing a little way down the tunnel. It waited.

All timing comes from info.cue(...) / info.line(...) / info.word_time(...).
World = sets.service_tunnel (people and creature at s=0.75).

Shots (see _times / _cam)
  S1  arrive   0 .. l01.end+.3      wide on the side-tunnel mouth, pan + push-in: he
                                    walks out of the dark, reaches BEHIND his head and
                                    pulls the hood back (arm stays behind the head),
                                    drops onto the crate; Curiosity follows and sits,
                                    looking up hopefully; l01 to it (head tilt at
                                    "bandwidth", eyes drop on "right now")
  S2  slump    .. l02b-.2           his medium: head hangs, the NEAR (bandaged) hand
                                    comes up to rub his eyes (elbow low, only the hand
                                    on the face), stays on his brow through "I fell out
                                    of a building today", drops on "I'm overwhelmed"
  S3  me       .. "before"-.12      two-shot: "I have to take care of me first..."
                                    (near hand to his chest on "me")
  S3b listen   .. l02b.end+.1       Curiosity CU: "...anyone else" -> its eyes and head
                                    go to the tunnel (its family), ears lift
  S4  point    .. l03-.15           two-shot: points down the tunnel, looks back at him,
                                    hop-turns up onto its hind legs and takes his
                                    sleeve cuff in BOTH PAWS (his hand hangs below
                                    them), one gentle tug that stops at "Look."
  S5  wrong    .. l04-.15           closer two-shot: he looks at it and means it; firm
                                    little nod on "wrong"; its ears lift with hope;
                                    beat: his eyes slide away, the head follows
  S6  hurt-who .. l04b.end+.35      his CU, not looking at it ("...somebody getting
                                    hurt"); realisation; slow push-in on "Maybe me.
                                    ...I need time to think." (quiet fear, eyes close)
  S7  hurt     .. leave+.1          Curiosity CU: ears lower degree by degree, tears,
                                    the gaze sinks, it lets go (paws back to its chest),
                                    his hand slides out of frame; it turns its head away
  S8a leave    .. at the mouth      wide: it walks away alone; he never looks up
  S8b back     .. look-back+.45     the mouth: it walks in, stops a short way in, looks
                                    back once, turns and goes on into the dark
  S9  alone    .. l05.end+.1        his medium: drip; lifts the bandaged forearm, a
                                    faint teal glow, lip press, looks down the tunnel;
                                    "...Ugh." with his eyes shut
  S10 follow   .. end               stands up and trudges after it; the camera drifts
                                    to the tunnel: two teal eyes glowing in the dark a
                                    little way down (fx.eyes_in_dark). It waited.
"""
import math
import os

import cairocffi as cairo

from engine import core, sets, human, fx
from engine import creatures as CR
from engine.core import clamp, lerp, seg, smoothstep, ease_in_out, ease_out, ease_in, tween

M = sets.TUNNEL_MARKS
S = 0.75                       # people / creature scale in the tunnel world
SEAT_X, FEET_Y = 1080, 1500    # Tiredness on the seat crate (ground point)
CUR_X = 735                    # Curiosity's sitting spot beside him (screen-left = toward the tunnel)
CUR_Y = 1506                   # a hair in front of his feet line (it is drawn after him)
TUG_X = 765                    # up on its hind legs at his sleeve (it hops a little closer)
TUG_RK = 0.28                  # reach_up "reach" while holding his cuff
HAND_OFF = (2.0, 24.0)         # his hand hangs below its paws (paws on the cuff)
HAND_ANG = 1.9                 # ... pointing down and a little toward it
WALK_RATE = 0.8                # his trudge (fraction of the walk cycle rate)
FOLLOW_RATE = 0.58             # ... slower and reluctant when he follows it (ends short of the mouth)
MOUTH_X0 = 470                 # Curiosity's corridor-floor point in front of the side tunnel
VP = M["far_end"]              # side tunnel vanishing point (300, 1010)
CUR_V = CR.SPEC_WALK_SPEED * S  # its foot-locked speed at cycle rate 1
LEAVE_RATE = 1.55              # its walk-away cycle rate
K_STOP = 0.09                  # a short way into the side tunnel: it stops and looks back
K_WAIT = 0.32                  # a little further down: it sits in the dark and waits

# sit_crate with longer shins so his soles reach the floor in front of the set's crate.
# Arm layers are pinned (no per-frame layer decisions while hands reach).
_SITP = {"base": "sit_crate", "ll_p": 1.5, "lr_p": 1.48, "ll_k": 1.45, "lr_k": 1.42,
         "al_layer": "mid", "ar_layer": "mid"}
# the walk with its own voted layers pinned: far (r) arm behind the body, near (l) arm
# over the torso but UNDER the head (the hood pull happens behind the head)
_WALKP = {"base": "walk", "al_layer": "mid", "ar_layer": "back"}

_STRICT = bool(os.environ.get("S04_STRICT"))


def _sitp(**kw):
    d = dict(_SITP)
    d.update(kw)
    return d


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def _tw(t, keys, ease=ease_in_out):
    for a, b in zip(keys, keys[1:]):
        if b[0] < a[0]:
            if _STRICT:
                raise ValueError(f"s04 tween keys out of order: {a[0]:.3f} > {b[0]:.3f}")
            keys = sorted(keys, key=lambda k: k[0])
            break
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
        l02=c("s04_l02"), l02e=c("s04_l02.end"), l02b=c("s04_l02b"), l02be=c("s04_l02b.end"),
        tug=c("tug"), l03=c("s04_l03"), l03e=c("s04_l03.end"), beat=c("beat"),
        l04=c("s04_l04"), l04e=c("s04_l04.end"), l04b=c("s04_l04b"), l04be=c("s04_l04b.end"),
        hurt=c("hurt"), leave=c("leave"), alone=c("alone"),
        l05=c("s04_l05"), l05e=c("s04_l05.end"), follow=c("follow"), end=c("end"),
    )
    wt = info.word_time
    # "I don't have the bandwidth for this right now."
    T["w01_bw"] = wt("s04_l01", 4)
    T["w01_right"] = wt("s04_l01", 7)
    T["w01_now"] = wt("s04_l01", -1)
    # "I fell out of a building today. I'm overwhelmed."
    T["w02_today"] = wt("s04_l02", 6)
    T["w02_im"] = wt("s04_l02", 7)
    # "I have to take care of me first... before I can take care of anyone else."
    T["w2b_take"] = wt("s04_l02b", 3)
    T["w2b_me"] = wt("s04_l02b", 6)
    T["w2b_before"] = wt("s04_l02b", 8)
    T["w2b_anyone"] = wt("s04_l02b", 14)
    # "Look. What they're doing to your family is wrong."
    T["w03_look"] = wt("s04_l03", 0)
    T["w03_family"] = wt("s04_l03", 6)
    T["w03_wrong"] = wt("s04_l03", -1)
    # "But I don't see a way to help without somebody getting hurt."
    T["w04_dont"] = wt("s04_l04", 2)
    T["w04_way"] = wt("s04_l04", 5)
    T["w04_somebody"] = wt("s04_l04", 9)
    T["w04_hurt"] = wt("s04_l04", -1)
    # "Maybe me. ...I need time to think."
    T["w4b_me"] = wt("s04_l04b", 1)
    T["w4b_I"] = wt("s04_l04b", 2)
    T["w4b_think"] = wt("s04_l04b", -1)
    # --- arrival (S1): walk ends at the crate, turn, drop
    T["stop"] = min(1.9, T["l01"] - 1.3)
    T["sit0"] = T["stop"] + 0.35
    T["land"] = T["sit0"] + 0.5
    T["c_out"] = 0.75                              # Curiosity out of the side tunnel
    T["c_arr"] = T["land"] - 0.2                   # ... and beside the crate
    # --- shots
    T["s2"] = T["l01e"] + 0.3
    T["s3"] = T["l02b"] - 0.2
    T["s3b"] = T["w2b_before"] - 0.12
    T["s4"] = T["l02be"] + 0.1
    T["s5"] = T["l03"] - 0.15
    T["s6"] = T["l04"] - 0.15
    T["s7"] = T["l04be"] + 0.35
    T["s8"] = T["leave"] + 0.1
    # --- slump (S2): the near hand to his face
    T["rub0"] = T["slump"] + 0.4
    T["rub1"] = T["rub0"] + 0.45
    T["rub_end"] = min(T["rub1"] + 0.6, T["l02"] + 0.1)
    T["hand_dn"] = T["w02_im"] - 0.3
    T["hand_dn1"] = T["hand_dn"] + 0.45
    # --- S3: near hand to his chest on "me"
    T["chest0"] = T["w2b_take"] - 0.1
    T["chest1"] = T["chest0"] + 0.45
    T["chest_off"] = T["w2b_before"] + 0.15
    T["chest_off1"] = T["chest_off"] + 0.5
    # --- Curiosity's point / hop / paws on the sleeve (S4)
    t4 = T["s4"]
    T["pt_up"] = t4                                # paw rises
    T["pt_look"] = t4 + 0.5                        # head turns back to him
    T["pt_down"] = max(t4 + 1.05, min(t4 + 1.2, T["l03"] - 1.5))   # paw lowers
    T["hop"] = T["pt_down"] + 0.18                 # hop-turn (flip + up onto the hind legs)
    T["flipT"] = T["hop"] + 0.12
    T["grab0"] = T["hop"] + 0.28                   # landed upright, paws reach for the cuff
    T["grab"] = T["grab0"] + 0.32                  # paws on his cuff
    T["tug_stop"] = T["w03_look"] - 0.05           # the tugs stop when he speaks
    # --- hurt (S7)
    T["rel0"] = T["leave"] - 1.2                   # lets go of the sleeve
    T["rel1"] = T["rel0"] + 0.5
    T["away"] = T["leave"] - 0.4                   # head turns away, down
    # --- leave (S8)
    t8 = T["s8"]
    T["lv_walk"] = t8 + 0.15
    T["lv_mouth"] = T["lv_walk"] + 0.125 + (TUG_X - MOUTH_X0) / (CUR_V * LEAVE_RATE)
    T["s8b"] = T["lv_mouth"] - 0.3
    T["lv_stop"] = T["lv_mouth"] + 0.5
    T["lv_back"] = T["lv_stop"] + 0.05             # looks back
    T["lv_fwd"] = T["lv_back"] + 1.0               # turns forward again
    T["lv_deep"] = T["lv_fwd"] + 1.35              # ... and goes on to where it waits
    # --- alone (S9) / follow (S10)
    T["s9"] = T["lv_fwd"] + 0.45
    T["s10"] = T["l05e"] + 0.1
    t9 = T["s9"]
    T["arm0"] = t9 + 0.15
    T["glow"] = t9 + 0.65
    T["press"] = t9 + 1.1
    T["arm1"] = min(t9 + 1.4, T["l05"] - 0.65)
    T["look_tn"] = min(t9 + 1.6, T["l05"] - 0.5)
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


def _probe_person(x, y, t, kw):
    kw = {k: v for k, v in kw.items() if k not in ("reach", "mouth", "x", "y")}
    return human.draw_person(_probe_ctx(), "tired", x, y, S, t, **kw)


def _tired(t, T, info, paws=None):
    """World-space draw kwargs for Tiredness at time t (paws = Curiosity's grip point)."""
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
            pose = _WALKP
        else:
            # stop: walk (frozen) -> stand -> sit, turning to face left (toward the tunnel)
            k1 = _ramp(t, stop, stop + 0.3)
            k2 = _ramp(t, T["sit0"], T["land"], ease_in)
            if k2 <= 0.0:
                pose = _pose_of((_WALKP, "stand", k1))
            else:
                pose = _pose_of(("stand", _sitp(), k2))
            x = lerp(x_stop, SEAT_X, _ramp(t, stop + 0.05, T["sit0"] + 0.2))
        turn = _tw(t, [(stop - 0.05, 1.0), (stop + 0.3, 0.15), (T["sit0"] + 0.25, -0.6)])
        hood = _tw(t, [(0.5, 1.0), (1.2, 0.0)])
        expr = _track(t, [(0.0, "bored"), (0.95, "squint", 0.3), (1.65, "bored", 0.4),
                          (T["land"], "sigh", 0.2), (T["land"] + 0.5, "bored", 0.3)])
        look = _tw(t, [(1.2, (0.25, 0.15)), (stop - 0.15, (0.35, 0.45)), (stop + 0.2, (-0.2, 0.6)),
                       (T["land"], (-0.25, 0.6)), (T["land"] + 0.5, (-0.3, 0.6))])
        face = {"lid": 0.07 * _bump(t, 0.95, 1.7)}
        if t >= T["land"]:
            pose = _sitp(nod=0.34 + _bump(t, T["land"], T["land"] + 0.5, 0.12),
                         hunch=0.65 + _bump(t, T["land"], T["land"] + 0.6, 0.12))
        out = dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pt_walk, turn=turn, expr=_pose_of(expr),
                   look=look, face=face, hood=hood, blink=None, mouth=info.mouth("tired", t))
        # hood pull: the near (l) hand reaches up BEHIND his head (arm layer "mid": under
        # the head), takes the top of the hood and pulls it back off over the crown
        if 0.15 < t < 1.62:
            w = _ramp(t, 0.15, 0.5) * (1.0 - _ramp(t, 1.2, 1.6))
            ang = lerp(1.65, 3.0, smoothstep(seg(t, 0.5, 1.2)))
            hx, hy = _probe_person(x, FEET_Y, t, out)["head"]
            r = 92
            reach["l"] = (hx + r * math.cos(ang), hy - 25 - r * math.sin(ang), w)
        out["reach"] = reach or None
        return out

    # ---------------- seated ---------------------------------------------------
    x = SEAT_X
    turn = -0.6
    # head carriage (sit_crate base: nod .34, lean .5, hunch .65)
    nod = _tw(t, [(T["land"] + 0.3, 0.34), (T["l01"] - 0.1, 0.3), (T["w01_now"], 0.3),
                  (T["w01_now"] + 0.4, 0.38),
                  (T["slump"] + 0.05, 0.38), (T["slump"] + 0.55, 0.62),       # head hangs
                  (T["l02"] - 0.1, 0.6), (T["l02"] + 0.3, 0.52),              # talks into his hand
                  (T["hand_dn"], 0.5), (T["w02_im"] + 0.15, 0.3),             # "I'm overwhelmed"
                  (T["l02e"], 0.32), (T["l02e"] + 0.5, 0.35),
                  (T["w2b_me"] - 0.1, 0.32), (T["w2b_me"] + 0.15, 0.38), (T["w2b_before"], 0.32),
                  (T["l02be"], 0.34),
                  (T["pt_up"] + 0.3, 0.32), (T["grab"] - 0.1, 0.34), (T["grab"] + 0.3, 0.42),  # at the paws
                  (T["l03"] - 0.1, 0.42), (T["l03"] + 0.2, 0.36),
                  (T["w03_wrong"], 0.36), (T["w03_wrong"] + 0.15, 0.45),     # firm little nod
                  (T["w03_wrong"] + 0.45, 0.36),
                  (T["beat"] + 0.3, 0.36), (T["l04"], 0.33),
                  (T["w04_somebody"], 0.33), (T["w04_hurt"], 0.4),
                  (T["l04e"] + 0.2, 0.4), (T["l04b"] - 0.1, 0.35),             # realisation: lifts
                  (T["w4b_I"], 0.38), (T["w4b_think"] + 0.5, 0.47),           # sinks
                  (T["s8"], 0.46), (T["s9"], 0.42),
                  (T["arm0"] + 0.1, 0.3), (T["arm1"], 0.32),
                  (T["look_tn"] + 0.15, 0.25),
                  (T["l05"], 0.22), (T["l05"] + 0.35, 0.08), (T["l05e"], 0.3),     # groan: head back
                  (T["up0"] + 0.25, 0.42), (T["up1"], 0.2)])
    lean = _tw(t, [(T["slump"] + 0.05, 0.5), (T["slump"] + 0.55, 0.58), (T["hand_dn"], 0.58),
                   (T["hand_dn1"], 0.5), (T["up0"], 0.5), (T["up0"] + 0.3, 0.68)])
    hunch = _tw(t, [(T["l01e"], 0.65), (T["slump"] + 0.55, 0.75), (T["hand_dn1"], 0.65),
                    (T["l04e"], 0.65), (T["l04b"] - 0.15, 0.8),                # held breath
                    (T["w4b_think"] + 0.4, 0.7), (T["s8"], 0.68),
                    (T["l05"], 0.65), (T["l05"] + 0.4, 0.5), (T["l05e"] + 0.1, 0.72)])
    pose = _sitp(nod=nod, lean=lean, hunch=hunch)

    # slump: the NEAR (r, bandaged) hand comes up beside his jaw to rub his near eye
    # (upper arm below the head, forearm along the side of the face): only the hand is on
    # the face. Front layer only between rest and rest (the layer flips at the knee).
    if T["rub0"] < t < T["hand_dn1"]:
        pose = dict(pose, ar_layer="front")
        pb = _probe_person(x, FEET_Y, t, dict(kw, pose=pose, turn=turn))
        ex, ey = pb["eye_r"][:2]
        hx0, hy0 = pb["hand_r"][:2]
        shx, shy = pb["shoulder_r"][:2]
        env = _bump(t, T["rub1"] - 0.05, T["rub_end"] + 0.1)
        ph = (t - T["rub1"]) * 2 * math.pi * 1.6
        tx_, ty_ = ex + 28 + 6 * math.sin(ph) * env, ey - 6 + 4 * math.cos(ph) * env
        mx_, my_ = ex + 72, ey + 96              # beside the jaw: it never sweeps over the mouth
        u = _ramp(t, T["rub0"], T["rub1"]) * (1 - _ramp(t, T["hand_dn"], T["hand_dn1"]))
        bx = (1 - u) ** 2 * hx0 + 2 * u * (1 - u) * mx_ + u * u * tx_
        by = (1 - u) ** 2 * hy0 + 2 * u * (1 - u) * my_ + u * u * ty_
        w = _ramp(t, T["rub0"], T["rub0"] + 0.12) * (1 - _ramp(t, T["hand_dn1"] - 0.12, T["hand_dn1"]))
        a_def = math.atan2(by - shy, bx - shx)
        d_ang = (-2.25 - a_def + math.pi) % (2 * math.pi) - math.pi
        reach["r"] = (bx, by, w, a_def + d_ang * smoothstep(seg(u, 0.5, 1.0)))

    # S3: the near hand to his chest on "me"
    ch_w = _ramp(t, T["chest0"], T["chest1"]) * (1 - _ramp(t, T["chest_off"], T["chest_off1"]))
    if ch_w > 0.0:
        pb = _probe_person(x, FEET_Y, t, dict(kw, pose=pose, turn=turn))
        nx_, ny_ = pb["neck"][:2]
        reach["r"] = (nx_ - 6, ny_ + 44, ch_w)

    # the tug: his far (l) hand is held by Curiosity's paws at the cuff (hand hangs below)
    if paws is not None:
        gw = _ramp(t, T["grab0"] + 0.05, T["grab"]) * (1 - _ramp(t, T["rel0"] + 0.05, T["rel1"], ease_in))
        if gw > 0.0:
            px, py = paws
            reach["l"] = (px + HAND_OFF[0], py + HAND_OFF[1], gw, HAND_ANG)

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
            x = SEAT_X - _tired_walk_speed() / WALK_RATE * FOLLOW_RATE * max(0.0, t - T["walk2"] - 0.15)
        pose_t = FOLLOW_RATE * max(0.0, t - T["walk2"]) + 0.5

    # --- eyes (pupils lead, the head follows ~0.15 s later via head_turn)
    look = _tw(t, [
        (T["land"] + 0.1, (-0.3, 0.6)), (T["l01"] - 0.3, (-0.5, 0.6)),             # at it
        (T["w01_right"], (-0.5, 0.6)), (T["w01_right"] + 0.25, (-0.15, 0.85)),     # eyes drop
        (T["l01e"] + 0.3, (-0.1, 0.8)),
        (T["l02"], (0.05, 0.75)), (T["w02_im"], (0.05, 0.75)), (T["w02_im"] + 0.2, (-0.5, 0.5)),
        (T["l02e"] + 0.3, (-0.5, 0.55)), (T["l02b"] - 0.15, (-0.55, 0.62)),
        # S4: follows the pointing paw toward the tunnel, then back to the creature
        (T["pt_up"] + 0.15, (-0.6, 0.55)), (T["pt_up"] + 0.35, (-0.9, 0.15)),
        (T["pt_look"] + 0.25, (-0.9, 0.15)), (T["pt_look"] + 0.45, (-0.55, 0.62)),
        (T["grab"], (-0.55, 0.65)), (T["grab"] + 0.3, (-0.5, 0.85)),       # down at its paws
        (T["w03_look"] - 0.2, (-0.5, 0.85)), (T["w03_look"] + 0.1, (-0.55, 0.62)),   # at its face
        (T["l03e"], (-0.55, 0.6)),
        # beat: pupils slide away first, the head follows
        (T["beat"] + 0.1, (-0.5, 0.6)), (T["beat"] + 0.3, (0.65, 0.45)),
        (T["l04"], (0.7, 0.5)), (T["w04_somebody"], (0.65, 0.55)), (T["w04_hurt"], (0.45, 0.8)),
        (T["l04e"] + 0.2, (0.45, 0.8)), (T["l04e"] + 0.45, (0.12, 0.45)),          # unfocused stare
        (T["w4b_me"], (0.15, 0.5)), (T["w4b_I"], (0.3, 0.8)),
        (T["s8"], (0.2, 0.75)), (T["s9"], (0.1, 0.6)),
        # alone: at the bandage, then down the dark tunnel
        (T["arm0"], (0.0, 0.55)), (T["arm0"] + 0.25, (-0.4, 0.55)),
        (T["arm1"], (-0.4, 0.55)), (T["look_tn"], (-0.3, 0.4)), (T["look_tn"] + 0.2, (-1.0, 0.05)),
        (T["l05"], (-1.0, 0.05)), (T["l05e"] + 0.2, (-0.7, 0.2)), (T["up1"], (-0.6, 0.25))])
    # small honest head shakes: "...right now" and "I don't see a way"
    shake = (0.06 * math.sin((t - T["w01_right"]) * 2 * math.pi * 1.25)
             * _bump(t, T["w01_right"] - 0.1, T["l01e"] + 0.15)
             + 0.05 * math.sin((t - T["w04_dont"]) * 2 * math.pi * 1.3)
             * _bump(t, T["w04_dont"] - 0.1, T["w04_way"] + 0.7))
    head_turn = _tw(t, [(T["beat"] + 0.3, 0.0), (T["beat"] + 0.55, 0.28), (T["l04e"] + 0.3, 0.24),
                        (T["l04e"] + 0.6, 0.12), (T["s8"], 0.05),
                        (T["look_tn"] + 0.15, 0.0), (T["look_tn"] + 0.45, -0.3), (T["l05e"], -0.2)]) + shake
    head_tilt = _tw(t, [(T["l03"] - 0.2, 0.0), (T["l03"] + 0.3, -0.05), (T["l03e"] + 0.3, -0.03),
                        (T["beat"] + 0.4, 0.0)])

    # --- expressions: honest and overwhelmed, never dismissive
    expr = _track(t, [
        (0.0, "bored"),
        (T["l01"] - 0.3, "sad", 0.35),
        (T["slump"] + 0.05, "sigh", 0.3),
        (T["l02"] - 0.15, "sad", 0.3),
        (T["arm0"] + 0.2, "sad", 0.4),
        (T["l05"] - 0.05, "sigh", 0.25), (T["l05e"] + 0.1, "unamused", 0.3), (T["up1"], "bored", 0.4)])
    ex_ = _pose_of(expr)
    # "Maybe me.": a quiet edge of fear (a little of "terrified" over "sad")
    fear = _tw(t, [(T["l04e"] + 0.15, 0.0), (T["l04e"] + 0.5, 0.22), (T["w4b_me"] + 0.3, 0.28),
                   (T["w4b_think"], 0.18), (T["l04be"] + 0.4, 0.0)])
    if fear > 0.005 and ex_ == "sad":
        ex_ = ("sad", "terrified", fear)
    face = _addf(
        {"head_turn": head_turn, "head_tilt": head_tilt},
        # inner brows up: overwhelmed / sincere / worried
        {"brow_ang": _tw(t, [(T["l01"] - 0.3, 0.0), (T["l01"] + 0.1, 0.16), (T["l01e"] + 0.3, 0.1),
                             (T["slump"], 0.0), (T["w02_im"] - 0.1, 0.0), (T["w02_im"] + 0.2, 0.24),
                             (T["l02e"] + 0.4, 0.16), (T["l02b"], 0.22), (T["l02be"] + 0.2, 0.16),
                             (T["l03"] - 0.1, 0.16), (T["w03_look"] + 0.1, 0.28),
                             (T["w03_wrong"] - 0.05, 0.24), (T["w03_wrong"] + 0.15, 0.08),
                             (T["beat"] + 0.4, 0.14), (T["l04"] + 0.2, 0.24),
                             (T["l04e"] + 0.2, 0.26), (T["l04e"] + 0.5, 0.36), (T["w4b_think"], 0.32),
                             (T["s8"], 0.15), (T["s9"], 0.0)]),
         "lid": _tw(t, [(T["l01e"], 0.0), (T["l01e"] + 0.3, 0.05), (T["slump"], 0.05), (T["l02"], 0.0),
                        (T["beat"] + 0.5, 0.0), (T["l04"] + 0.2, 0.06),
                        (T["l04e"] + 0.2, 0.06), (T["l04e"] + 0.5, -0.07),           # lids lift a hair
                        (T["w4b_me"] + 0.2, -0.05), (T["w4b_I"] + 0.1, 0.1), (T["l04be"] + 0.5, 0.12),
                        (T["s8"] + 0.2, 0.06), (T["s9"], 0.0)])},
        # "is wrong": a firm little knit (he means it)
        {"frown": _bump(t, T["w03_wrong"] - 0.1, T["beat"] + 0.6, 0.22)},
        # lip presses
        {"press": _bump(t, T["beat"] + 0.45, T["l04"] - 0.05, 0.45)
         + _bump(t, T["l04e"] + 0.1, T["l04b"] - 0.02, 0.55)
         + _bump(t, T["l04be"] + 0.05, T["l04be"] + 0.9, 0.4)
         + _bump(t, T["press"], T["press"] + 0.75, 0.55) + _bump(t, T["slump"] - 0.3, T["slump"] + 0.2, 0.3)},
        # alone: inner brows up a hair at the glow
        {"brow_ang": _bump(t, T["glow"] - 0.1, T["arm1"] + 0.6, 0.22)},
    )
    # slow blinks on judgement beats; eyes shut while rubbing and through the groan
    blink = None
    for (b0, hold) in ((T["l01e"] + 0.05, 0.15), (T["l02e"] + 0.1, 0.2), (T["w03_wrong"] + 0.55, 0.1)):
        if b0 - 0.05 <= t <= b0 + 0.75 + hold:
            blink = _slow_blink(t, b0, hold)
    if T["rub0"] + 0.1 <= t <= T["rub_end"] + 0.4:
        blink = _tw(t, [(T["rub0"] + 0.1, 0.0), (T["rub1"] - 0.05, 1.0), (T["rub_end"], 1.0),
                        (T["rub_end"] + 0.4, 0.0)])
    if T["w4b_think"] - 0.1 <= t <= T["l04be"] + 0.75:      # "...time to think": eyes close, slowly
        blink = _tw(t, [(T["w4b_think"] - 0.1, 0.0), (T["w4b_think"] + 0.4, 1.0),
                        (T["l04be"] + 0.25, 1.0), (T["l04be"] + 0.75, 0.0)])
    if T["l05"] - 0.1 <= t <= T["l05e"] + 0.3:
        blink = _tw(t, [(T["l05"] - 0.1, 0.0), (T["l05"] + 0.15, 1.0), (T["l05e"] - 0.1, 1.0),
                        (T["l05e"] + 0.3, 0.0)])
    return dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pose_t, turn=turn, expr=ex_, look=look,
                face=face, hood=0.0, reach=reach or None, blink=blink, mouth=info.mouth("tired", t))


# ----------------------------------------------------------------------------
# CURIOSITY
# ----------------------------------------------------------------------------
def _cur_base(t):
    return dict(x=CUR_X, y=CUR_Y, s=S, pose="sit", expr="calm", flip=False, face=None,
                look=(0.45, -0.55), ears=0.5, tears=None, tilt=0.0, tail_curl=0.0, glow=1.0,
                pose_t=None, pose_from=None, pose_mix=1.0, point_angle=0.0, blink=None,
                sq=(1.0, 1.0), lift=0.0, rot=0.0, alpha=1.0, clip=False, dark=0.0, reach=1.0,
                wait=False)


def _cur(t, T):
    """World-space draw kwargs for Curiosity."""
    d = _cur_base(t)
    if t < T["s4"]:
        return _cur_s1_s3(t, T, d)
    if t < T["grab0"]:
        return _cur_s4(t, T, d)
    if t < T["s8"]:
        return _cur_hold(t, T, d)
    if t < T["s9"]:
        return _cur_leave(t, T, d)
    return _cur_wait(t, T, d)


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
    # sitting, it looks up at him hopefully (calm -> hopeful switched on a blink)
    tb = T["land"] + 0.25
    if t >= tb + 0.07:
        d["expr"] = "hopeful"
    if abs(t - tb - 0.07) < 0.12:
        d["blink"] = _tw(t, [(tb - 0.05, 0.0), (tb + 0.03, 1.0), (tb + 0.11, 1.0), (tb + 0.19, 0.0)])
    d["look"] = _tw(t, [(1.0, (0.6, -0.15)), (ta, (0.5, -0.5)), (T["land"], (0.45, -0.6)),
                        (T["w01_right"], (0.45, -0.6)), (T["w01_now"] + 0.2, (0.35, -0.35)),
                        (T["l01e"] + 0.3, (0.4, -0.45))])
    # "bandwidth": a puzzled little head tilt; "right now": the ears dip
    d["tilt"] = _tw(t, [(T["land"] + 0.2, 0.0), (T["w01_bw"] - 0.05, 0.0), (T["w01_bw"] + 0.25, -0.16),
                        (T["w01_right"], -0.14), (T["w01_now"] + 0.35, 0.03), (T["s2"], 0.04)])
    d["ears"] = _tw(t, [(T["land"], 0.55), (tb + 0.2, 0.66), (T["w01_right"], 0.66),
                        (T["w01_now"] + 0.45, 0.5)])
    if t >= T["s2"]:                   # off screen (S2 is on him): soft, worried listening
        d["look"] = _tw(t, [(T["s2"], (0.4, -0.45)), (T["s3"], (0.45, -0.6))])
        d["ears"] = 0.5
        d["tilt"] = 0.04
    # S3 (two-shot): "...take care of me first": the ears dip a little, a sympathetic tilt
    if t >= T["s3"]:
        d["ears"] = _tw(t, [(T["w2b_me"], 0.5), (T["w2b_me"] + 0.5, 0.42)])
        d["tilt"] = _tw(t, [(T["w2b_take"], 0.04), (T["w2b_take"] + 0.4, 0.1)])
    # S3b (its CU): "...anyone else" -> its family: eyes slide to the tunnel, the head
    # follows, the ears lift
    if t >= T["s3b"]:
        ta_ = T["w2b_anyone"]
        d["look"] = _tw(t, [(ta_ - 0.1, (0.45, -0.6)), (ta_ + 0.15, (-0.85, -0.1))])
        d["face"] = _tw(t, [(ta_ + 0.05, 1.0), (ta_ + 0.55, -0.6)])
        d["ears"] = 0.42 + 0.2 * core.ease_out_back(seg(t, ta_ + 0.05, ta_ + 0.4))
        d["tilt"] = _tw(t, [(ta_, 0.1), (ta_ + 0.35, -0.05)])
        if ta_ - 0.3 < t < ta_ + 0.5:
            d["blink"] = 0.0
    return d


def _cur_s4(t, T, d):
    # S4: points back toward the tunnel, looks back at him, hop-turns up onto its hind legs
    d["expr"] = "pleading"
    if t < T["flipT"]:
        d["flip"] = True
        if t < T["pt_down"]:
            d["pose_from"], d["pose"] = "sit", "point"
            d["pose_mix"] = seg(t, T["pt_up"], T["pt_up"] + 0.32)
        else:
            d["pose_from"], d["pose"] = "point", "sit"
            d["pose_mix"] = seg(t, T["pt_down"], T["pt_down"] + 0.18)
        d["point_angle"] = 0.22 - _bump(t, T["pt_look"] + 0.35, T["pt_look"] + 0.6, 0.12)
        d["face"] = _tw(t, [(T["pt_up"], 0.85), (T["pt_look"], 0.85), (T["pt_look"] + 0.3, -1.0)])
        # screen-space look: down the tunnel first, then back up at him
        d["look"] = _tw(t, [(T["pt_up"] + 0.1, (-0.85, -0.2)), (T["pt_look"] - 0.1, (-0.85, -0.2)),
                            (T["pt_look"] + 0.12, (0.6, -0.55))])
        d["ears"] = _tw(t, [(T["pt_up"], 0.62), (T["pt_up"] + 0.3, 0.72), (T["pt_look"] + 0.3, 0.6)])
    else:
        _cur_upright(t, T, d)
        d["reach"] = 0.0
    _hop(t, T, d)
    return d


def _hop(t, T, d):
    """The hop-turn: squash, hop (flip + up onto the hind legs at the apex), stretch, land."""
    h0 = T["hop"]
    if h0 + 0.04 < t < h0 + 0.24:
        d["lift"] = 18 * math.sin(math.pi * seg(t, h0 + 0.04, h0 + 0.24))
    if t < T["flipT"]:
        sq = -_bump(t, h0 - 0.08, h0 + 0.06, 0.09) + _bump(t, h0 + 0.06, h0 + 0.12, 0.05)
        d["sq"] = (1.0 - sq * 0.6, 1.0 + sq)
        d["x"] = CUR_X
    else:
        # reach_up is ~100 px (s=1) taller than sit: it rises out of the hop instead of popping
        k = seg(t, T["flipT"], T["flipT"] + 0.3)
        sy = lerp(0.72, 1.0, core.ease_out_back(k, 1.2))
        sx = lerp(1.1, 1.0, smoothstep(k))
        d["sq"] = (sx, sy)
        d["x"] = lerp(CUR_X, TUG_X, smoothstep(seg(t, T["hop"], T["flipT"] + 0.12)))


def _cur_upright(t, T, d):
    d["flip"] = False
    d["pose"] = "reach_up"
    d["x"] = TUG_X
    d["face"] = 1.0
    d["look"] = (0.5, -0.55)
    d["ears"] = 0.6


def _cur_hold(t, T, d):
    """Up on its hind legs holding his sleeve cuff in both paws through l03 / l04 / l04b,
    then the hurt and the release."""
    _cur_upright(t, T, d)
    d["expr"] = "pleading"
    _hop(t, T, d)
    d["reach"] = _tw(t, [(T["grab0"], 0.0), (T["grab"], TUG_RK), (T["rel0"], TUG_RK), (T["rel1"], 0.0)])
    # one gentle tug (lean back from the feet, 1.1 Hz), a second one fades out at "Look."
    if t > T["grab"]:
        yank = 0.5 - 0.5 * math.cos(2 * math.pi * 1.1 * (t - T["grab"]))
        amp = 1.0 - _ramp(t, T["tug_stop"] - 0.05, T["tug_stop"] + 0.4)
        d["rot"] = -0.07 * yank * amp
    # "...your family is wrong." -> hope: ears up, tail tip hooks (expr switch on a blink)
    tw_ = T["w03_wrong"]
    d["ears"] = _tw(t, [(T["grab"], 0.6), (T["w03_family"], 0.6), (T["w03_family"] + 0.4, 0.66)])
    if t >= tw_ + 0.12:
        d["ears"] = lerp(0.66, 0.8, core.ease_out_back(seg(t, tw_ + 0.12, tw_ + 0.42)))
        if t >= T["beat"] + 0.45:
            d["ears"] = lerp(0.8, 0.66, ease_in_out(seg(t, T["beat"] + 0.45, T["beat"] + 1.1)))
    if t >= tw_ + 0.3:
        d["expr"] = "hopeful"
    if abs(t - tw_ - 0.3) < 0.12:
        d["blink"] = _tw(t, [(tw_ + 0.2, 0.0), (tw_ + 0.27, 1.0), (tw_ + 0.33, 1.0), (tw_ + 0.42, 0.0)])
    d["tail_curl"] = _tw(t, [(tw_ + 0.15, 0.0), (tw_ + 0.6, 0.28), (T["beat"] + 0.5, 0.28),
                             (T["s6"] - 0.1, 0.06), (T["s6"] + 0.2, 0.0)])
    d["tilt"] = _tw(t, [(T["beat"] + 0.4, 0.0), (T["beat"] + 0.9, -0.07), (T["s6"], -0.05)])
    d["look"] = _tw(t, [(T["grab"], (0.5, -0.55)), (T["beat"] + 0.25, (0.5, -0.55)),
                        (T["beat"] + 0.6, (0.6, -0.48))])
    # ---- off screen during his CU: ONE expression for the hurt (teary from tears=0)
    if t >= T["s6"] + 0.3:
        d["expr"] = "teary"
        d["tail_curl"] = 0.0
        d["ears"] = _tw(t, [(T["s6"] + 0.3, 0.66), (T["l04e"], 0.58), (T["l04be"], 0.5)])
        d["tears"] = 0.0
    # ---- the hurt (S7): ears lower degree by degree, the eyes glisten, the gaze sinks,
    # it lets go (paws back to its chest), the head turns away
    if t >= T["s7"] - 0.1:
        d["ears"] = lerp(0.5, 0.03, ease_in_out(seg(t, T["s7"] + 0.1, T["rel0"] + 0.45)))
        d["tears"] = (lerp(0.0, 0.6, smoothstep(seg(t, T["s7"] + 0.3, T["rel0"])))
                      + lerp(0.0, 0.22, smoothstep(seg(t, T["rel0"] + 0.2, T["s8"]))))
        d["look"] = _tw(t, [(T["s7"] + 0.8, (0.6, -0.48)), (T["s7"] + 1.7, (0.25, 0.5)),
                            (T["away"], (0.25, 0.5)), (T["away"] + 0.3, (-0.4, 0.55))])
        d["tilt"] = _tw(t, [(T["s7"] + 0.9, -0.05), (T["s7"] + 1.9, 0.14), (T["s8"] - 0.2, 0.26)])
        d["face"] = _tw(t, [(T["away"], 1.0), (T["s8"], 0.25)])
        if T["s7"] < t < T["rel0"]:
            d["blink"] = 0.0 if t < T["rel0"] - 0.8 else None
    return d


def _cur_leave(t, T, d):
    # S8: (turned away across the cut) walks away alone into the side tunnel, stops a short
    # way in, looks back once, turns and goes on into the dark
    d["flip"] = True
    d["expr"] = "sad"
    d["ears"] = 0.05
    d["tears"] = 0.55
    d["look"] = (-0.2, 0.35)
    d["tilt"] = 0.12
    d["glow"] = 0.9
    d["face"] = 1.0
    d["x"] = TUG_X
    vw = CUR_V * LEAVE_RATE
    if t < T["lv_walk"]:
        d["pose"] = "stand"
        d["tilt"] = 0.18
        return d
    tw_ = t - T["lv_walk"]
    acc = 0.25
    dist = vw * (tw_ - acc / 2 if tw_ > acc else tw_ * tw_ / (2 * acc))
    corr = TUG_X - MOUTH_X0
    if dist < corr:
        d["x"] = TUG_X - dist
        d["pose"] = "walk"
        d["pose_t"] = dist / CUR_V
        d["pose_from"], d["pose_mix"] = "stand", seg(tw_, 0.0, 0.3)
        return d
    # in the side tunnel: k from the mouth into the dark (stop + look back on the way)
    pt0 = corr / CUR_V
    pts = pt0 + (T["lv_stop"] - T["lv_mouth"]) * 1.2
    if t < T["lv_stop"]:
        u = seg(t, T["lv_mouth"], T["lv_stop"])
        k = K_STOP * (u * (2.0 - u))
        pt = pt0 + (t - T["lv_mouth"]) * 1.2
    elif t < T["lv_fwd"] + 0.15:
        k = K_STOP
        pt = pts
    else:
        u = seg(t, T["lv_fwd"] + 0.15, T["lv_deep"])
        k = lerp(K_STOP, K_WAIT, smoothstep(u))
        pt = pts + (t - T["lv_fwd"] - 0.15) * 1.0
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
    d["dark"] = _tw(t, [(T["lv_fwd"] + 0.15, 0.02), (T["lv_deep"], 0.7)])
    d["glow"] = lerp(0.9, 0.4, smoothstep(seg(k, K_STOP, K_WAIT)))
    if T["lv_back"] - 0.3 < t < T["lv_fwd"] + 0.4:      # no auto blink; one slow blink at the end
        d["blink"] = _tw(t, [(T["lv_fwd"] - 0.3, 0.0), (T["lv_fwd"] - 0.15, 1.0),
                             (T["lv_fwd"] + 0.0, 1.0), (T["lv_fwd"] + 0.15, 0.0)])
    return d


def _cur_wait(t, T, d):
    """It never really left: sitting in the dark a little way down the side tunnel, turned
    toward the mouth, waiting (only its eyes really show: fx.eyes_in_dark over a dark body)."""
    x, y, f = _depth(K_WAIT)
    d.update(x=x, y=y, s=S * f, pose="sit", flip=False, face=0.15, expr="sad", ears=0.18,
             look=(0.35, -0.1), tilt=0.06, glow=0.4, dark=0.86, clip=True, wait=True, blink=1.0)
    return d


def _wait_eyes(t, T):
    """(look, lid, blink, amount) of its eyes in the dark. They widen when he gets up."""
    hope = _ramp(t, T["up0"] + 0.3, T["up1"] + 0.5)
    look = _tw(t, [(T["s10"], (0.25, 0.05)), (T["up1"], (0.45, -0.05)), (T["end"], (0.4, -0.08))])
    lid = lerp(0.36, 0.16, hope)
    tb = T["up1"] + 0.95
    blink = _tw(t, [(tb, 0.0), (tb + 0.18, 1.0), (tb + 0.3, 1.0), (tb + 0.5, 0.0)])
    return look, lid, blink


# ----------------------------------------------------------------------------
# drawing
# ----------------------------------------------------------------------------
def _mouth_path(c):
    mx, mt, mw, mh = M["mouth"]
    wall = M["wall_y"]
    c.move_to(mx, wall + 6)
    c.line_to(mx, mt + 110)
    c.curve_to(mx, mt, mx + mw, mt, mx + mw, mt + 110)
    c.line_to(mx + mw, wall + 6)
    c.close_path()


def _to_world(c, p):
    """Rig-local anchor (drawn at 0,0 inside the creature's transform) -> world."""
    sx, sy = c["sq"]
    ca, sa = math.cos(c["rot"]), math.sin(c["rot"])
    lx, ly = p[0] * sx, p[1] * sy
    return (c["x"] + lx * ca - ly * sa, c["y"] - c["lift"] + lx * sa + ly * ca)


def _cur_kw(c):
    return dict(pose=c["pose"], expr=c["expr"], look=c["look"], glow=c["glow"], blink=c["blink"],
                flip=c["flip"], pose_t=c["pose_t"], face=c["face"], point_angle=c["point_angle"],
                tilt=c["tilt"], ears=c["ears"], tail_curl=c["tail_curl"], tears=c["tears"],
                pose_from=c["pose_from"], pose_mix=c["pose_mix"], reach=c["reach"])


def _cur_anchors(t, c):
    with core.saved(_probe_ctx(), c["x"], c["y"] - c["lift"], c["sq"], c["rot"]) as cx:
        a = CR.draw_specimen(cx, 0, 0, c["s"], t, **_cur_kw(c))
    return {k: _to_world(c, v) for k, v in a.items() if isinstance(v, tuple) and len(v) >= 2}


def _draw_cur(ctx, t, c):
    if c["alpha"] <= 0.01:
        return {}
    if c["clip"]:
        ctx.save()
        _mouth_path(ctx)
        ctx.clip()
    grouped = c["alpha"] < 0.999 or c["dark"] > 0.01
    if grouped:
        ctx.push_group()
    with core.saved(ctx, c["x"], c["y"] - c["lift"], c["sq"], c["rot"]) as cx:
        a = CR.draw_specimen(cx, 0, 0, c["s"], t, **_cur_kw(c)) or {}
    out = {k: _to_world(c, v) for k, v in a.items() if isinstance(v, tuple) and len(v) >= 2}
    if grouped:
        if c["dark"] > 0.01:     # in the side tunnel: darken the body (eyes re-lit below)
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ATOP)
            ctx.set_source_rgba(0.01, 0.015, 0.03, c["dark"])
            ctx.paint()
            ctx.restore()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(c["alpha"])
        if c["dark"] > 0.01 and out and not c["wait"]:
            r = 44 * c["s"]
            for e in ("eye_l", "eye_r"):
                if e in out:
                    core.radial_glow(ctx, out[e][0], out[e][1], r, "power", 1.1 * c["alpha"] * c["dark"])
    if c["clip"]:
        ctx.restore()
    return out


def _cur_paws(t, T):
    """Curiosity's grip point on his cuff (world), frozen once it lets go."""
    if not (T["grab0"] <= t <= T["rel1"] + 0.05):
        return None
    tp = min(t, T["rel0"] + 0.05)
    a = _cur_anchors(tp, _cur(tp, T))
    return a.get("paws")


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
    if t < T["s3b"]:
        k = smoothstep(seg(t, T["s3"], T["s3b"]))
        return 3, 885, 1265, lerp(2.12, 2.18, k)
    if t < T["s4"]:
        k = smoothstep(seg(t, T["s3b"], T["s4"]))
        return 31, 742, 1310, lerp(3.05, 3.15, k)
    if t < T["s5"]:
        return 4, 850, 1250, 1.85
    if t < T["s6"]:
        k = smoothstep(seg(t, T["s5"], T["s6"]))
        return 5, 880, 1285, lerp(2.15, 2.22, k)
    if t < T["s7"]:
        k = ease_in_out(seg(t, T["l04e"], T["l04be"] + 0.2))     # slow push-in on "Maybe me."
        return 6, lerp(1030, 1000, k), lerp(1110, 1098, k), lerp(3.4, 3.85, k)
    if t < T["s8"]:
        k = smoothstep(seg(t, T["s7"], T["s8"]))
        return 7, 770, 1300, lerp(3.3, 3.45, k)
    if t < T["s8b"]:
        return 8, 700, 1160, 0.95
    if t < T["s9"]:
        return 81, 432, 1238, 2.4
    if t < T["s10"]:
        k = smoothstep(seg(t, T["s9"], T["s10"]))
        return 9, 1000, 1150, lerp(2.25, 2.4, k)
    k = ease_in_out(seg(t, T["s10"] + 0.5, T["end"]))
    return 10, lerp(830, 690, k), 1150, 1.12


def render(ctx, t, info):
    T = _T(info)
    shot, cx, cy, zoom = _cam(t, T)
    c = _cur(t, T)
    paws = _cur_paws(t, T)
    p = _tired(t, T, info, paws)
    drip = t >= T["s8"] - 0.5
    t_set = t + ((1.82 - (T["s9"] + 0.5)) % 2.6)     # a drip lands just after the "alone" cut
    bandage_amt = 0.0
    if T["glow"] <= t <= T["arm1"] + 0.4:
        bandage_amt = 0.6 * _tw(t, [(T["glow"], 0.0), (T["glow"] + 0.4, 1.0), (T["glow"] + 0.8, 0.5),
                                    (T["arm1"] + 0.3, 0.0)])

    with core.camera(ctx, cx, cy, zoom):
        sets.service_tunnel(ctx, t_set, drip=drip)
        pk = {k: v for k, v in p.items() if k not in ("x", "y")}
        behind = c["y"] < FEET_Y - 20              # Curiosity deep in the side tunnel: behind him
        split = c["wait"]                          # its glowing eyes go between it and him
        with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
            ca = {}
            if behind:
                ca = _draw_cur(ctx, t, c)
            if not split:
                a = human.draw_person(ctx, "tired", p["x"], p["y"], S, t, **pk)
                if not behind:
                    ca = _draw_cur(ctx, t, c)
        if split:
            if "eye_l" in ca and "eye_r" in ca:
                # its two teal eyes, still glowing in the dark down the side tunnel
                (x1, y1), (x2, y2) = ca["eye_l"][:2], ca["eye_r"][:2]
                se = c["s"] * 1.25
                gap = max(95.0, math.hypot(x2 - x1, y2 - y1) / se)
                look, lid, blink = _wait_eyes(t, T)
                ctx.save()
                _mouth_path(ctx)
                ctx.clip()
                fx.eyes_in_dark(ctx, (x1 + x2) / 2, (y1 + y2) / 2, se, t, kind="curiosity",
                                blink=blink, look=look, gap=gap, lid=lid, tilt=0.05)
                ctx.restore()
            with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
                a = human.draw_person(ctx, "tired", p["x"], p["y"], S, t, **pk)
        if bandage_amt > 0:
            _bandage_glow(ctx, a, bandage_amt)
    fx.vignette(ctx, 0.3, inner=0.62)


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    T = _times(info)
    ev = []
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
    # slump: sigh, the hand up to his face
    ev.append((T["slump"] + 0.05, "sigh", 0.0, 0.0))
    ev.append((T["rub0"] + 0.1, "cloth_rustle", -9.0, 0.05))
    ev.append((T["chest0"] + 0.15, "cloth_rustle", -13.0, 0.05))
    # Curiosity: ears lift at "anyone else", a pleading chitter at the point, the hop,
    # its paws on his sleeve, the tug; ears up with hope at "wrong"
    ev.append((T["w2b_anyone"] + 0.08, "ears_perk", -4.0, -0.2))
    ev.append((T["pt_up"] + 0.05, "creature_chitter", -5.0, -0.25))
    ev.append((T["grab0"] - 0.02, "footstep", -17.0, -0.2))
    ev.append((T["grab"] - 0.05, "cloth_rustle", -8.0, -0.15))
    ev.append((T["grab"] + 0.4, "cloth_rustle", -13.0, -0.1))
    ev.append((T["w03_wrong"] + 0.12, "ears_perk", -7.0, -0.2))
    # the hurt: a small sad coo as it lets go
    ev.append((T["rel0"] + 0.2, "creature_chirp_sad", -8.0, -0.1))
    ev.append((T["rel0"] + 0.1, "cloth_rustle", -12.0, 0.0))
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
        tw = T["walk2"] + (0.81 + 0.5 * n - 0.5) / FOLLOW_RATE
        if tw < T["end"] - 0.1:
            ev.append((tw, "footstep", -8.0, -0.15))
    return [e for e in ev if 0.0 <= e[0] < T["end"]]
