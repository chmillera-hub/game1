"""s04 — "Not my problem" (music: lonely).  Revision 2 (honest, caring, overwhelmed).

A quiet CalmCorp service tunnel lit by dim emergency lamps. Tiredness trudges out
of the dark side tunnel (the way back to the shaft and the pods), reaches back and
pulls his hood off in the first light, drops onto a crate. He is not dismissive,
he is overwhelmed: he tells Curiosity he has no bandwidth, that he fell out of a
building today, that he has to take care of himself first. Curiosity points back
toward the pods and takes his sleeve in its paws. He means it when he says what
CalmCorp is doing to its family is wrong (its ears lift with hope), but he can't
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
MOUTH_X0 = 470                 # Curiosity's corridor-floor point in front of the side tunnel
VP = M["far_end"]              # side tunnel vanishing point (300, 1010)
CUR_V = CR.SPEC_WALK_SPEED * S  # its foot-locked speed at cycle rate 1
LEAVE_RATE = 1.55              # its walk-away cycle rate
K_STOP = 0.09                  # a short way into the side tunnel: it stops and looks back
K_WAIT = 0.32                  # a little further down: it sits in the dark and waits
K_DRIFT = 0.07                 # ... and drifts this much closer at "...I hope we make it out"

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
        l02c=c("s04_l02c"), l02ce=c("s04_l02c.end"),
        tug=c("tug"), l03=c("s04_l03"), l03e=c("s04_l03.end"), beat=c("beat"),
        l04=c("s04_l04"), l04e=c("s04_l04.end"), l04b=c("s04_l04b"), l04be=c("s04_l04b.end"),
        hurt=c("hurt"), leave=c("leave"), alone=c("alone"),
        l05=c("s04_l05"), l05e=c("s04_l05.end"), follow=c("follow"),
        l06=c("s04_l06"), l06e=c("s04_l06.end"), glance=c("glance"),
        l06b=c("s04_l06b"), l06be=c("s04_l06b.end"), hush=c("hush"),
        l07=c("s04_l07"), l07e=c("s04_l07.end"), sighup=c("sighup"), go=c("go"), end=c("end"),
    )
    T["scared"] = c("scared", T["l04be"] + 0.45)
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
    # "...But I don't want to abandon you."
    T["w2c_but"] = wt("s04_l02c", 0)
    T["w2c_dont"] = wt("s04_l02c", 2)
    T["w2c_abandon"] = wt("s04_l02c", 5)
    T["w2c_you"] = wt("s04_l02c", -1)
    T["q2c"] = _quiet(info, "s04_l02c", "tired")
    # "Look. What they're doing to your family is wrong."
    T["w03_look"] = wt("s04_l03", 0)
    T["w03_family"] = wt("s04_l03", 6)
    T["w03_wrong"] = wt("s04_l03", -1)
    # "But I don't see a way to help without somebody getting hurt."
    T["w04_dont"] = wt("s04_l04", 2)
    T["w04_way"] = wt("s04_l04", 5)
    T["w04_somebody"] = wt("s04_l04", 9)
    T["w04_hurt"] = wt("s04_l04", -1)
    # "Maybe even me. ...I need time to think."
    T["w4b_me"] = wt("s04_l04b", 2)
    T["w4b_I"] = wt("s04_l04b", 3)
    T["w4b_time"] = wt("s04_l04b", 5)
    T["w4b_think"] = wt("s04_l04b", -1)
    T["q4b"] = _quiet(info, "s04_l04b", "tired")
    # "Okay. I'll help. Hell or high water."
    T["w06_okay"] = wt("s04_l06", 0)
    T["w06_ill"] = wt("s04_l06", 1)
    T["w06_help"] = wt("s04_l06", 2)
    T["w06_hell"] = wt("s04_l06", 3)
    T["w06_water"] = wt("s04_l06", -1)
    T["q06"] = _quiet(info, "s04_l06", "tired")
    # "...I hope we make it out of this."
    T["w6b_hope"] = wt("s04_l06b", 1)
    T["w6b_this"] = wt("s04_l06b", -1)
    T["q6b"] = _quiet(info, "s04_l06b", "tired")
    # (Emb, off screen) "Oh my God! What IS that thing?!"
    T["w07_god"] = wt("s04_l07", 2)
    T["w07_is"] = wt("s04_l07", 4)
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
    T["s3c"] = T["l02be"] + 0.1                    # two-shot: "...But I don't want to abandon you."
    T["s4"] = T["l02ce"] + 0.1
    T["s5"] = T["l03"] - 0.15
    T["s6"] = T["l04"] - 0.15
    T["s7"] = T["hurt"] - 0.1
    T["s8"] = T["leave"] + 0.1
    # --- S3c: he looks away (down), then pupils lead back to it, the head follows
    T["away0"] = T["s3c"] + 0.12
    T["lk"] = T["w2c_but"] - 0.25                  # pupils back to it
    T["c_back"] = T["w2c_but"] + 0.02              # its pupils come back to him
    T["hope"] = T["w2c_abandon"] + 0.15            # the flicker of hope (ears lift)
    T["c_idea"] = max(T["hope"] + 0.75, T["s4"] - 0.42)   # eyes to the tunnel: "then come!"
    # --- S6 / l04b: eyes drop + unfocus, a swallow, the near hand tightens, hold
    T["drop4b"] = T["w4b_me"] + 0.12
    T["swal"] = T["q4b"] + 0.1
    T["fist0"] = T["swal"] + 0.32
    T["fist1"] = T["fist0"] + 0.55
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
    # --- alone (S9)
    T["s9"] = T["lv_fwd"] + 0.45
    T["s10"] = T["l05e"] + 0.1
    t9 = T["s9"]
    T["arm0"] = t9 + 0.15
    T["glow"] = t9 + 0.65
    T["press"] = t9 + 1.1
    T["arm1"] = min(t9 + 1.4, T["l05"] - 0.65)
    T["look_tn"] = min(t9 + 1.6, T["l05"] - 0.5)
    # --- follow (S10 two-plane) .. l06 / glance / l06b (S11 his medium) .. the eyes answer (S12)
    # .. hush + Emb's yell (S13 two-plane) .. sigh + get up (S14) .. go (S15 wide)
    T["lift"] = T["follow"] + 0.05                 # pupils to the tunnel, the head lifts after
    T["s11"] = T["w06_ill"] - 0.12
    T["gl0"] = T["glance"] + 0.08                  # sad glance down at his hands ...
    T["gl1"] = T["gl0"] + 0.75                     # ... and back to the eyes in the dark
    T["s12"] = max(T["l06be"] - 0.1, T["q6b"] + 0.3)
    T["ans"] = T["s12"] + 0.25                     # its slow blink + drift closer
    T["s13"] = max(T["l07"] - 0.95, T["ans"] + 1.0)
    T["snap"] = T["l07"] + 0.05                    # his head snaps / its eyes whip to the voice
    sg = T["sighup"]
    T["up_c"] = max(T["go"] + 0.15, sg + 1.7)      # standing (he starts to walk on 'go')
    T["up_b"] = T["up_c"] - 0.75                   # push up off his knees
    T["up_a"] = T["up_b"] - 0.3                    # anticipation: leans forward, hands to knees
    T["inh"] = max(T["l07e"] + 0.25, sg - 0.2)     # inhale (shoulders up) ...
    T["exh"] = T["inh"] + 0.3                      # ... the exhale (shoulders drop)
    T["exh1"] = min(T["exh"] + 0.55, T["up_a"] - 0.02)
    T["s14"] = T["inh"] - 0.15
    T["walk0"] = T["up_c"] + 0.2                   # (turns to the tunnel first, then walks)
    T["s15"] = T["up_c"] - 0.12
    return T


def _quiet(info, lid, who):
    """Scene time the speaker's mouth last moves in line `lid` (public lip-sync only)."""
    l = info.line(lid)
    t = l.end
    while t > l.start and info.mouth(who, t)[0] < 0.05:
        t -= 1.0 / 48.0
    return t


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
    kw = {k: v for k, v in kw.items() if k not in ("reach", "mouth", "x", "y", "s", "dark")}
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
                  # "...But I don't want to abandon you.": head dips away, then comes back to it
                  (T["away0"] + 0.15, 0.34), (T["away0"] + 0.5, 0.4),
                  (T["lk"] + 0.12, 0.4), (T["lk"] + 0.45, 0.33),
                  (T["pt_up"] + 0.3, 0.32), (T["grab"] - 0.1, 0.34), (T["grab"] + 0.3, 0.42),  # at the paws
                  (T["l03"] - 0.1, 0.42), (T["l03"] + 0.2, 0.36),
                  (T["w03_wrong"], 0.36), (T["w03_wrong"] + 0.15, 0.45),     # firm little nod
                  (T["w03_wrong"] + 0.45, 0.36),
                  (T["beat"] + 0.3, 0.36), (T["l04"], 0.33),
                  (T["w04_somebody"], 0.33), (T["w04_hurt"], 0.4),
                  (T["l04e"] + 0.2, 0.4), (T["l04b"] - 0.1, 0.35),             # realisation: lifts
                  (T["drop4b"] + 0.12, 0.36), (T["drop4b"] + 0.5, 0.42),       # follows the eyes down
                  (T["fist0"], 0.43), (T["fist1"] + 0.3, 0.46),
                  (T["s8"], 0.46), (T["s9"], 0.42),
                  (T["arm0"] + 0.1, 0.3), (T["arm1"], 0.32),
                  (T["look_tn"] + 0.15, 0.25),
                  (T["l05"], 0.22), (T["l05"] + 0.35, 0.08), (T["l05e"], 0.3),     # groan: head back
                  (T["l05e"] + 0.45, 0.42),                                         # ... and it drops
                  (T["lift"] + 0.12, 0.42), (T["lift"] + 0.55, 0.24),               # lifts it: the eyes
                  (T["w06_okay"] - 0.02, 0.24), (T["w06_okay"] + 0.18, 0.3), (T["w06_okay"] + 0.45, 0.25),
                  (T["w06_help"], 0.25), (T["w06_help"] + 0.15, 0.31), (T["w06_help"] + 0.45, 0.25),
                  (T["w06_water"], 0.25), (T["w06_water"] + 0.2, 0.3), (T["l06e"], 0.26),
                  (T["gl0"] + 0.12, 0.26), (T["gl0"] + 0.4, 0.38),                # glance down ...
                  (T["gl1"], 0.38), (T["gl1"] + 0.3, 0.27),                         # ... and back
                  (T["l06b"] + 0.2, 0.28), (T["l06be"], 0.33), (T["s13"], 0.36),
                  (T["snap"], 0.36), (T["snap"] + 0.12, 0.15), (T["snap"] + 0.3, 0.2),   # the snap
                  (T["l07e"], 0.21),
                  (T["inh"], 0.21), (T["exh"], 0.16), (T["exh1"], 0.42),            # sigh: head sinks
                  (T["up_a"] + 0.05, 0.42), (T["up_b"], 0.24)])                     # looks ahead, rises
    lean = _tw(t, [(T["slump"] + 0.05, 0.5), (T["slump"] + 0.55, 0.58), (T["hand_dn"], 0.58),
                   (T["hand_dn1"], 0.5),
                   (T["snap"], 0.5), (T["snap"] + 0.1, 0.4), (T["snap"] + 0.45, 0.46),   # jolt back
                   (T["inh"], 0.46), (T["exh"], 0.43), (T["exh1"], 0.56),
                   (T["up_a"], 0.56), (T["up_b"], 0.84)])                        # anticipation
    hunch = _tw(t, [(T["l01e"], 0.65), (T["slump"] + 0.55, 0.75), (T["hand_dn1"], 0.65),
                    (T["l04e"], 0.65), (T["l04b"] - 0.15, 0.8),                # held breath
                    (T["drop4b"] + 0.4, 0.77), (T["fist0"], 0.76), (T["fist1"], 0.81),
                    (T["s7"] + 0.4, 0.72), (T["s8"], 0.68),
                    (T["l05"], 0.65), (T["l05"] + 0.4, 0.5), (T["l05e"] + 0.1, 0.72),
                    (T["lift"] + 0.6, 0.66), (T["w06_help"], 0.6), (T["l06e"], 0.62),
                    (T["gl0"] + 0.4, 0.68), (T["l06b"] + 0.3, 0.72), (T["s13"], 0.68),
                    (T["snap"], 0.68), (T["snap"] + 0.12, 0.8), (T["snap"] + 0.45, 0.74),
                    (T["inh"], 0.74), (T["exh"], 0.95),                         # sigh: shoulders up ...
                    (T["exh1"], 0.42),                                          # ... and they drop
                    (T["up_b"], 0.5)])
    pose = _sitp(nod=nod, lean=lean, hunch=hunch)
    # "...I need time to think.": the near (bandaged, r) hand tightens into a fist on his knee
    kf = _ramp(t, T["fist0"], T["fist1"]) * (1 - _ramp(t, T["s8"] - 0.6, T["s8"]))
    if kf > 0.001:
        pose = _pose_of((pose, dict(pose, ar_h="fist"), kf))

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

    # sighup: hands onto his knees (anticipation), the push up off them, standing; then go
    pose_t = None
    hw = _ramp(t, T["up_a"], T["up_a"] + 0.3) * (1 - _ramp(t, T["up_b"] + 0.28, T["up_c"] - 0.08))
    if t >= T["up_b"]:
        k = _trap(seg(t, T["up_b"], T["up_c"]))
        pose = _pose_of((pose, _rise_pose(k), k))
        x = SEAT_X - _foot_shift(k)
    if hw > 0.0:
        pb = _probe_person(x, FEET_Y, t, dict(kw, pose=pose, turn=turn))
        for sd in ("l", "r"):
            kx, ky = pb["knee_" + sd][:2]
            reach[sd] = (kx + KNEE_OFF[sd][0], ky + KNEE_OFF[sd][1], hw)
    if t >= T["up_c"]:
        turn = lerp(-0.6, -1.0, _ramp(t, T["up_c"] - 0.02, T["walk0"] + 0.05))
        x_st = SEAT_X - _foot_shift(1.0)
        if t >= T["walk0"]:
            pose = _pose_of(("stand", _GOP, _ramp(t, T["walk0"], T["walk0"] + 0.3)))
            x, y_go, sc_go, pose_t, dk = _go_path(t, T, x_st)
            return _tired_go(t, T, info, kw, x, y_go, sc_go, pose, pose_t, turn, dk)
        x = x_st
        pose = "stand"

    # --- eyes (pupils lead, the head follows ~0.15 s later via head_turn)
    look = _tw(t, [
        (T["land"] + 0.1, (-0.3, 0.6)), (T["l01"] - 0.3, (-0.5, 0.6)),             # at it
        (T["w01_right"], (-0.5, 0.6)), (T["w01_right"] + 0.25, (-0.15, 0.85)),     # eyes drop
        (T["l01e"] + 0.3, (-0.1, 0.8)),
        (T["l02"], (0.05, 0.75)), (T["w02_im"], (0.05, 0.75)), (T["w02_im"] + 0.2, (-0.5, 0.5)),
        (T["l02e"] + 0.3, (-0.5, 0.55)), (T["l02b"] - 0.15, (-0.55, 0.62)),
        # "...But I don't want to abandon you.": eyes drop away, then lead back to it
        (T["away0"], (-0.55, 0.62)), (T["away0"] + 0.3, (0.3, 0.84)),
        (T["lk"], (0.3, 0.84)), (T["lk"] + 0.17, (-0.58, 0.6)),
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
        (T["w4b_me"], (0.15, 0.5)), (T["drop4b"], (0.15, 0.5)),
        (T["drop4b"] + 0.35, (0.24, 0.86)),                                         # eyes drop
        (T["s8"], (0.2, 0.75)), (T["s9"], (0.1, 0.6)),
        # alone: at the bandage, then down the dark tunnel
        (T["arm0"], (0.0, 0.55)), (T["arm0"] + 0.25, (-0.4, 0.55)),
        (T["arm1"], (-0.4, 0.55)), (T["look_tn"], (-0.3, 0.4)), (T["look_tn"] + 0.2, (-1.0, 0.05)),
        (T["l05"], (-1.0, 0.05)), (T["l05e"] + 0.3, (-0.55, 0.6)),
        # follow: lifts his eyes to the two teal eyes in the dark
        (T["lift"], (-0.55, 0.6)), (T["lift"] + 0.17, (-1.0, 0.03)),
        (T["gl0"], (-1.0, 0.03)), (T["gl0"] + 0.2, (-0.15, 0.9)),                  # glance: his hands
        (T["gl1"] - 0.05, (-0.15, 0.9)), (T["gl1"] + 0.15, (-1.0, 0.04)),           # ... back to it
        (T["s13"], (-1.0, 0.05)),
        (T["snap"] - 0.02, (-1.0, 0.05)), (T["snap"] + 0.07, (-1.1, -0.14)),        # the voice
        (T["l07e"], (-1.05, -0.08)),
        (T["exh"], (-0.95, 0.1)), (T["exh1"], (-0.8, 0.45)),                       # sigh: eyes drop
        (T["up_a"] + 0.1, (-0.8, 0.45)), (T["up_a"] + 0.3, (-1.0, 0.0))])           # then ahead
    # small honest head shakes: "...right now" and "I don't see a way"
    shake = (0.06 * math.sin((t - T["w01_right"]) * 2 * math.pi * 1.25)
             * _bump(t, T["w01_right"] - 0.1, T["l01e"] + 0.15)
             + 0.05 * math.sin((t - T["w04_dont"]) * 2 * math.pi * 1.3)
             * _bump(t, T["w04_dont"] - 0.1, T["w04_way"] + 0.7))
    head_turn = _tw(t, [(T["away0"] + 0.12, 0.0), (T["away0"] + 0.45, 0.12),     # away ...
                        (T["lk"] + 0.15, 0.12), (T["lk"] + 0.5, -0.08),            # ... and to it
                        (T["q2c"] + 0.2, -0.08), (T["pt_up"] + 0.4, 0.0),
                        (T["beat"] + 0.3, 0.0), (T["beat"] + 0.55, 0.28), (T["l04e"] + 0.3, 0.24),
                        (T["l04e"] + 0.6, 0.12), (T["s8"], 0.05),
                        (T["look_tn"] + 0.15, 0.0), (T["look_tn"] + 0.45, -0.3), (T["l05e"], -0.2),
                        (T["l05e"] + 0.45, -0.15),
                        (T["lift"] + 0.15, -0.15), (T["lift"] + 0.5, -0.32),       # head follows the eyes
                        (T["gl0"] + 0.15, -0.32), (T["gl0"] + 0.45, -0.12),
                        (T["gl1"] + 0.1, -0.12), (T["gl1"] + 0.4, -0.3),
                        (T["s13"], -0.24),
                        (T["snap"], -0.24), (T["snap"] + 0.1, -0.7), (T["snap"] + 0.25, -0.62),
                        (T["l07e"], -0.58),
                        (T["exh1"], -0.4), (T["up_b"], -0.3), (T["up_c"], -0.15)]) + shake
    head_tilt = _tw(t, [(T["lk"] + 0.15, 0.0), (T["lk"] + 0.55, -0.045), (T["q2c"] + 0.2, -0.045),
                        (T["pt_up"] + 0.4, 0.0),
                        (T["l03"] - 0.2, 0.0), (T["l03"] + 0.3, -0.05), (T["l03e"] + 0.3, -0.03),
                        (T["beat"] + 0.4, 0.0),
                        (T["l06b"], 0.0), (T["l06b"] + 0.5, -0.04), (T["s13"], -0.03), (T["snap"], 0.0)])

    # --- expressions: honest and overwhelmed, never dismissive
    expr = _track(t, [
        (0.0, "bored"),
        (T["l01"] - 0.3, "sad", 0.35),
        (T["slump"] + 0.05, "sigh", 0.3),
        (T["l02"] - 0.15, "sad", 0.3),
        (T["arm0"] + 0.2, "sad", 0.4),
        (T["l05"] - 0.05, "sigh", 0.25), (T["l05e"] + 0.1, "unamused", 0.3),
        (T["lift"] + 0.1, "sad", 0.35),                        # the eyes in the dark: it waited
        (T["w06_okay"] + 0.05, "bored", 0.4),                  # quiet resolve: tired but sure
        (T["gl0"], "sad", 0.3),                                # the sad glance
        (T["exh"], "sigh", 0.25), (T["up_a"] + 0.2, "bored", 0.35)])
    ex_ = _pose_of(expr)
    # "Maybe even me." / "...I hope we make it out": a quiet edge of fear over "sad"
    fear = _tw(t, [(T["l04e"] + 0.15, 0.0), (T["l04e"] + 0.5, 0.22), (T["w4b_me"] + 0.3, 0.28),
                   (T["w4b_think"], 0.22), (T["fist1"], 0.2), (T["s7"] + 0.4, 0.0),
                   (T["l06b"] - 0.1, 0.0), (T["w6b_hope"], 0.14), (T["w6b_this"], 0.2),
                   (T["q6b"] + 0.4, 0.15), (T["s13"] + 0.4, 0.0)])
    if fear > 0.005 and ex_ == "sad":
        ex_ = ("sad", "terrified", fear)
    sw = T["swal"]
    face = _addf(
        {"head_turn": head_turn, "head_tilt": head_tilt},
        # inner brows up: overwhelmed / sincere / worried
        {"brow_ang": _tw(t, [(T["l01"] - 0.3, 0.0), (T["l01"] + 0.1, 0.16), (T["l01e"] + 0.3, 0.1),
                             (T["slump"], 0.0), (T["w02_im"] - 0.1, 0.0), (T["w02_im"] + 0.2, 0.24),
                             (T["l02e"] + 0.4, 0.16), (T["l02b"], 0.22), (T["l02be"] + 0.2, 0.16),
                             (T["lk"], 0.17), (T["w2c_dont"], 0.28), (T["w2c_abandon"] + 0.1, 0.33),
                             (T["q2c"] + 0.4, 0.26), (T["pt_up"] + 0.5, 0.17),
                             (T["l03"] - 0.1, 0.16), (T["w03_look"] + 0.1, 0.28),
                             (T["w03_wrong"] - 0.05, 0.24), (T["w03_wrong"] + 0.15, 0.08),
                             (T["beat"] + 0.4, 0.14), (T["l04"] + 0.2, 0.24),
                             (T["l04e"] + 0.2, 0.26), (T["l04e"] + 0.5, 0.36), (T["w4b_think"], 0.32),
                             (T["fist1"], 0.34),
                             (T["s8"], 0.15), (T["s9"], 0.0),
                             (T["lift"] + 0.2, 0.0), (T["lift"] + 0.6, 0.16),
                             (T["w06_okay"], 0.14), (T["w06_help"], 0.07), (T["l06e"], 0.08),
                             (T["gl0"] + 0.25, 0.24), (T["gl1"] + 0.3, 0.18),
                             (T["l06b"] + 0.2, 0.3), (T["w6b_this"], 0.34), (T["q6b"] + 0.5, 0.24),
                             (T["s13"] + 0.3, 0.2), (T["snap"], 0.2), (T["snap"] + 0.15, 0.1),
                             (T["exh1"], 0.12), (T["up_c"], 0.08)]),
         "lid": _tw(t, [(T["l01e"], 0.0), (T["l01e"] + 0.3, 0.05), (T["slump"], 0.05), (T["l02"], 0.0),
                        (T["lk"], 0.0), (T["w2c_dont"], 0.04), (T["q2c"] + 0.3, 0.04), (T["pt_up"] + 0.4, 0.0),
                        (T["beat"] + 0.5, 0.0), (T["l04"] + 0.2, 0.06),
                        (T["l04e"] + 0.2, 0.06), (T["l04e"] + 0.5, -0.07),           # lids lift a hair
                        (T["w4b_me"] + 0.2, -0.05), (T["drop4b"] + 0.4, 0.04),      # ... then drop
                        (T["fist1"], 0.06), (T["s8"] + 0.2, 0.06), (T["s9"], 0.0),
                        (T["w06_okay"], 0.0), (T["w06_help"], 0.04), (T["gl1"] + 0.3, 0.03),
                        (T["s13"], 0.03),
                        (T["snap"], 0.03), (T["snap"] + 0.1, -0.1), (T["l07e"], -0.06),   # small start
                        (T["exh"], 0.0)]),
         # "Maybe even me. ...": the eyes go unfocused (inward)
         "focus": -0.6 * _ramp(t, T["drop4b"], T["drop4b"] + 0.45) * (1 - _ramp(t, T["s7"] + 0.6, T["s8"]))},
        # the swallow: chin dips and bobs back, lips pressed, the brows twitch up
        {"head_nod": _bump(t, sw, sw + 0.3, 0.06) - _bump(t, sw + 0.22, sw + 0.55, 0.015)
         - 0.13 * _ramp(t, T["snap"], T["snap"] + 0.1) * (1 - _ramp(t, T["l07e"], T["exh1"])),
         "squash": -0.06 * _bump(t, T["snap"] - 0.02, T["snap"] + 0.3),
         "brow_ang": _bump(t, sw - 0.05, sw + 0.5, 0.07)},
        # "is wrong": a firm little knit (he means it)
        {"frown": _bump(t, T["w03_wrong"] - 0.1, T["beat"] + 0.6, 0.22)},
        # lip presses
        {"press": _bump(t, T["beat"] + 0.45, T["l04"] - 0.05, 0.45)
         + _bump(t, T["l04e"] + 0.1, T["l04b"] - 0.02, 0.55)
         + _bump(t, sw - 0.06, sw + 0.6, 0.55) + 0.32 * _ramp(t, sw + 0.4, T["fist0"] + 0.2)
         * (1 - _ramp(t, T["s7"] + 0.4, T["s7"] + 1.0))
         + _bump(t, T["away0"] + 0.05, T["lk"] + 0.15, 0.35) + _bump(t, T["q2c"] + 0.03, T["q2c"] + 0.65, 0.3)
         + _bump(t, T["press"], T["press"] + 0.75, 0.55) + _bump(t, T["slump"] - 0.3, T["slump"] + 0.2, 0.3)
         + _bump(t, T["w06_okay"] + 0.3, T["w06_ill"] - 0.02, 0.3) + _bump(t, T["q06"] + 0.02, T["q06"] + 0.7, 0.4)
         + _bump(t, T["gl0"] + 0.1, T["gl1"] + 0.3, 0.35) + _bump(t, T["q6b"] + 0.03, T["q6b"] + 0.8, 0.45)},
        # the sigh: a visible exhale ("hah")
        {"open": _bump(t, T["exh"] - 0.05, T["exh1"], 0.24)},
        # alone: inner brows up a hair at the glow
        {"brow_ang": _bump(t, T["glow"] - 0.1, T["arm1"] + 0.6, 0.22)},
        # Emb's yell: brows jump up (a small start)
        {"brow": _bump(t, T["snap"], T["l07e"] + 0.3, 0.3)},
    )
    # slow blinks on judgement beats; eyes shut while rubbing and through the groan
    blink = None
    for (b0, hold) in ((T["l01e"] + 0.05, 0.15), (T["l02e"] + 0.1, 0.2), (T["w03_wrong"] + 0.55, 0.1)):
        if b0 - 0.05 <= t <= b0 + 0.75 + hold:
            blink = _slow_blink(t, b0, hold)
    if T["w03_family"] - 0.15 <= t < T["w03_wrong"] + 0.5:     # eyes on it through "...is wrong"
        blink = 0.0
    if T["lk"] - 0.05 <= t < T["q2c"] + 0.05:                # and through "...abandon you."
        blink = 0.0
    if T["q2c"] + 0.05 <= t < T["q2c"] + 0.62:               # a soft slow blink after it
        b0 = T["q2c"] + 0.05
        blink = _tw(t, [(b0, 0.0), (b0 + 0.22, 1.0), (b0 + 0.28, 1.0), (b0 + 0.56, 0.0)])
    if T["w4b_me"] - 0.4 <= t < T["s7"]:                       # "Maybe even me. ...": held stare
        blink = 0.0
        b0 = T["w4b_time"]
        if b0 <= t <= b0 + 0.6:                                # (one slow blink inside it)
            blink = _tw(t, [(b0, 0.0), (b0 + 0.22, 1.0), (b0 + 0.28, 1.0), (b0 + 0.58, 0.0)])
    if T["rub0"] + 0.1 <= t <= T["rub_end"] + 0.4:
        blink = _tw(t, [(T["rub0"] + 0.1, 0.0), (T["rub1"] - 0.05, 1.0), (T["rub_end"], 1.0),
                        (T["rub_end"] + 0.4, 0.0)])
    if T["l05"] - 0.1 <= t <= T["l05e"] + 0.3:
        blink = _tw(t, [(T["l05"] - 0.1, 0.0), (T["l05"] + 0.15, 1.0), (T["l05e"] - 0.1, 1.0),
                        (T["l05e"] + 0.3, 0.0)])
    if T["lift"] - 0.1 <= t < T["w06_okay"] + 0.3:            # eyes on the eyes in the dark
        blink = 0.0
    if T["w06_okay"] + 0.3 <= t < T["w06_okay"] + 0.95:       # "Okay." -> a slow, accepting blink
        b0 = T["w06_okay"] + 0.3
        blink = _tw(t, [(b0, 0.0), (b0 + 0.25, 1.0), (b0 + 0.33, 1.0), (b0 + 0.65, 0.0)])
    if T["gl1"] + 0.1 <= t < T["q6b"] + 0.5:                   # held on it through l06b
        blink = 0.0
    if T["snap"] - 0.1 <= t < T["l07e"] + 0.2:                 # alert through the yell
        blink = 0.0
    if T["exh"] <= t <= T["up_a"] + 0.25:                       # the sigh: eyes close, reopen ahead
        blink = _tw(t, [(T["exh"], 0.0), (T["exh"] + 0.3, 0.85), (T["up_a"], 0.85),
                        (T["up_a"] + 0.25, 0.0)])
    elif T["up_a"] + 0.25 < t < T["up_c"] + 0.3:              # eyes open (ahead) as he rises
        blink = 0.0
    return dict(kw, x=x, y=FEET_Y, pose=pose, pose_t=pose_t, turn=turn, expr=ex_, look=look,
                face=face, hood=0.0, reach=reach or None, blink=blink, mouth=info.mouth("tired", t))


# the walk into the side tunnel: far (l) arm swing biased forward so his hand never hides
# behind his body (the stock walk at turn -1 hides it for a third of every cycle)
_GOP = {"base": "walk", "al_p": human.W(0.25, 0.22, 0.5)}
GO_RATE = 0.76                 # tired but sure (fraction of the walk cycle rate)
GO_PH0 = 0.5                   # cycle phase where the first step starts
X_IN = 610                     # corridor-floor point where he turns into the side tunnel
K_GO = 0.05                    # how far in he gets by the end of the scene
KNEE_OFF = {"l": (-6.0, -16.0), "r": (4.0, -14.0)}     # palms on top of his knees
_FS = {}


def _trap(u, a=0.28):
    """0..1 with a trapezoid velocity (ease in over a, steady, ease out over a)."""
    u = clamp(u)
    vm = 1.0 / (1.0 - a)
    if u < a:
        return vm * u * u / (2 * a)
    if u > 1 - a:
        return 1.0 - vm * (1 - u) ** 2 / (2 * a)
    return vm * (u - a / 2)


def _rise_pose(k):
    """The stand target for the get-up: he keeps his weight forward over his feet while
    the hips rise and only straightens up at the end."""
    return {"base": "stand", "lean": 0.62 * (1.0 - smoothstep(seg(k, 0.4, 1.0)))}


def _foot_shift(k):
    """How far (px) his feet would slide forward in the sit -> stand blend: we move the
    ground point back by it so the soles stay planted while he rises."""
    if not _FS:
        base = _sitp(nod=0.24, lean=0.84, hunch=0.5)
        for i in range(21):
            kk = i / 20
            a = human.draw_person(_probe_ctx(), "tired", 0.0, FEET_Y, S, 0.0, outfit="sewer",
                                  bandage=True, pose=_pose_of((base, _rise_pose(kk), kk)), turn=-0.6)
            _FS[i] = 0.5 * (a["foot_l"][0] + a["foot_r"][0])
    u = clamp(k) * 20
    i = min(19, int(u))
    f0 = lerp(_FS[i], _FS[i + 1], u - i)
    return f0 - _FS[0]


def _go_path(t, T, x_st):
    """(x, y, scale, pose_t, dark) for the walk: left along the corridor to the side-tunnel
    mouth, then a few steps into it (shrinking along the tunnel's depth), into the dark.
    He stays to the right of its eyes (they keep showing to the end)."""
    v1 = human.cycle_speed("tired", "walk", 1.0) * S       # px per cycle at rate 1
    v = v1 * GO_RATE
    acc = 0.35

    def dist_at(tt):
        tw = max(0.0, tt - T["walk0"] - 0.05)
        return v * (tw - acc / 2 if tw > acc else tw * tw / (2 * acc))
    dist = dist_at(t)
    pose_t = GO_PH0 + dist / v1
    corr = x_st - X_IN
    e_end = dist_at(T["end"]) - corr
    if dist <= corr:
        x, y, f, kk = x_st - dist, FEET_Y, 1.0, 0.0
    else:
        kk = (dist - corr) / max(2200.0, e_end / K_GO)
        f = 1.0 / (1.0 + 5.0 * kk)
        x = VP[0] + (X_IN - VP[0]) * f
        y = VP[1] + (FEET_Y - VP[1]) * f
    dark = max(0.5 * smoothstep(1.0 - seg(x, 520, 700)), 0.62 * smoothstep(kk / K_GO))
    return x, y, S * f, pose_t, dark


def _tired_go(t, T, info, kw, x, y, sc, pose, pose_t, turn, dark):
    """Walking into the dark side tunnel after the voice (tired but sure)."""
    look = _tw(t, [(T["walk0"], (-1.0, 0.0)), (T["walk0"] + 1.2, (-1.0, -0.05)), (T["end"], (-1.0, -0.08))])
    face = {"head_turn": _tw(t, [(T["walk0"], -0.15), (T["walk0"] + 0.6, -0.08)]),
            "brow_ang": 0.08, "press": 0.2 * _ramp(t, T["walk0"] + 0.5, T["walk0"] + 1.0)}
    turn = turn - 0.15 * smoothstep(1.0 - seg(x, X_IN - 40, X_IN + 10))     # turns a little more into the tunnel
    return dict(kw, x=x, y=y, s=sc, pose=pose, pose_t=pose_t, turn=turn, expr="bored", look=look,
                face=face, hood=0.0, reach=None, blink=None, mouth=info.mouth("tired", t), dark=dark)


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
    # S3c (two-shot): "...But I don't want to abandon you." It is still gazing down the
    # tunnel (its family); on "But" its eyes come back to him (the head follows), the ears
    # dip a little (bracing for a no) ... then on "abandon you" a flicker of hope: the ears
    # lift, the head tips up. Then its eyes go to the tunnel: an idea (-> the point).
    if t >= T["s3c"]:
        cb, hp, ci = T["c_back"], T["hope"], T["c_idea"]
        d["look"] = _tw(t, [(cb, (-0.85, -0.1)), (cb + 0.16, (0.45, -0.55)),
                            (ci, (0.45, -0.58)), (ci + 0.14, (-0.85, -0.2))])
        d["face"] = _tw(t, [(cb + 0.1, -0.6), (cb + 0.45, 1.0), (ci + 0.1, 1.0), (ci + 0.38, -0.6)])
        ears = _tw(t, [(T["s3c"], 0.62), (cb - 0.2, 0.57), (cb + 0.3, 0.49), (hp, 0.49)])
        if t > hp:
            ears = lerp(0.49, 0.68, core.ease_out_back(seg(t, hp, hp + 0.38), 2.2))
        d["ears"] = ears
        d["tilt"] = _tw(t, [(cb, -0.05), (cb + 0.4, 0.05), (hp, 0.05), (hp + 0.35, -0.07),
                            (ci + 0.1, -0.07), (ci + 0.4, -0.03)])
        if cb - 0.1 < t < ci + 0.35:
            d["blink"] = 0.0
        if hp - 0.04 <= t < hp + 0.16:                 # a quick bright blink with the hope
            d["blink"] = _tw(t, [(hp - 0.04, 0.0), (hp + 0.03, 1.0), (hp + 0.07, 1.0), (hp + 0.16, 0.0)])
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
        d["ears"] = _tw(t, [(T["pt_up"], 0.68), (T["pt_up"] + 0.3, 0.72), (T["pt_look"] + 0.3, 0.6)])
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
    toward the mouth, waiting (only its eyes really show: fx.eyes_in_dark over a dark body).
    After "...I hope we make it out of this." it drifts a little closer (comfort)."""
    k = K_WAIT - K_DRIFT * ease_in_out(seg(t, T["ans"] - 0.1, T["ans"] + 1.05))
    x, y, f = _depth(k)
    d.update(x=x, y=y, s=S * f, pose="sit", flip=False, face=0.15, expr="sad", ears=0.18,
             look=(0.35, -0.1), tilt=0.06, glow=0.4, dark=0.86, clip=True, wait=True, blink=1.0)
    return d


def _wait_eyes(t, T):
    """(look, lid, blink, gap_k, dx) of its eyes in the dark: they meet his look (a little
    hope), answer "...I hope we make it out" with a slow blink, whip away toward Emb's yell
    (the pair turns: narrower, nudged toward the voice), and glance back once as he comes."""
    sn = T["snap"] + 0.02
    gb = T["walk0"] + 1.1                          # it glances back at him as he comes
    look = _tw(t, [(T["s10"], (0.25, 0.05)), (T["lift"] + 0.3, (0.25, 0.05)),
                   (T["lift"] + 0.5, (0.35, 0.0)), (T["ans"] + 1.0, (0.38, 0.03)),
                   (sn, (0.4, 0.02)), (sn + 0.1, (-0.72, -0.34)), (T["l07e"], (-0.66, -0.3)),
                   (gb, (-0.66, -0.3)), (gb + 0.14, (0.45, 0.06)), (gb + 0.7, (0.45, 0.06)),
                   (gb + 0.85, (-0.66, -0.3))])
    lid = _tw(t, [(T["lift"] + 0.45, 0.36), (T["lift"] + 0.8, 0.28),
                  (T["w06_help"] + 0.1, 0.28), (T["w06_help"] + 0.5, 0.21),
                  (T["ans"] + 1.0, 0.24),
                  (sn, 0.24), (sn + 0.08, 0.08), (T["l07e"] + 0.3, 0.14), (T["walk0"], 0.17)])
    b0 = T["ans"]
    bn = T["l07e"] + 0.45                          # one nervous blink after the yell
    blink = _tw(t, [(b0, 0.0), (b0 + 0.32, 1.0), (b0 + 0.47, 1.0), (b0 + 0.85, 0.0),
                    (bn, 0.0), (bn + 0.07, 1.0), (bn + 0.1, 1.0), (bn + 0.2, 0.0)])
    gap_k = _tw(t, [(sn, 1.0), (sn + 0.1, 0.84), (gb, 0.84), (gb + 0.14, 0.95), (gb + 0.7, 0.95),
                    (gb + 0.85, 0.85)])
    dx = _tw(t, [(sn, 0.0), (sn + 0.1, -16.0), (gb, -16.0), (gb + 0.14, 2.0), (gb + 0.7, 2.0),
                 (gb + 0.85, -16.0)])
    return look, lid, blink, gap_k, dx


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
    if t < T["s3c"]:
        k = smoothstep(seg(t, T["s3b"], T["s3c"]))
        return 31, 742, 1310, lerp(3.05, 3.15, k)
    if t < T["s4"]:      # two-shot, slow push-in: "...But I don't want to abandon you."
        k = ease_in_out(seg(t, T["s3c"], T["s4"]))
        return 32, lerp(872, 866, k), lerp(1274, 1266, k), lerp(2.3, 2.42, k)
    if t < T["s5"]:
        return 4, 850, 1250, 1.85
    if t < T["s6"]:
        k = smoothstep(seg(t, T["s5"], T["s6"]))
        return 5, 880, 1285, lerp(2.15, 2.22, k)
    if t < T["s7"]:
        # "Maybe even me. ...": a slow move down from his face to take in the near hand on
        # his knee (it tightens), the face staying big in the upper frame
        k = ease_in_out(seg(t, T["l04e"], T["fist0"] + 0.2))
        return 6, lerp(1030, 1000, k), lerp(1110, 1188, k), lerp(3.4, 3.45, k)
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
    if t < T["s11"]:      # S10 two-plane: him on the crate, its eyes in the dark side tunnel
        k = smoothstep(seg(t, T["s10"], T["s11"]))
        return 10, lerp(690, 684, k), 1140, lerp(1.19, 1.22, k)
    if t < T["s12"]:      # S11 his medium: "Okay. I'll help...", the glance, "...I hope..."
        k = ease_in_out(seg(t, T["s11"], T["s12"]))
        return 11, lerp(975, 985, k), lerp(1160, 1140, k), lerp(2.35, 2.7, k)
    if t < T["s13"]:      # S12 the eyes in the dark answer (slow blink, drift closer)
        k = smoothstep(seg(t, T["s12"], T["s13"]))
        return 12, 385, lerp(1132, 1142, k), lerp(2.6, 2.7, k)
    if t < T["s14"]:      # S13 two-plane: hush ... Emb's yell from deeper in the tunnel
        k = smoothstep(seg(t, T["s13"], T["s14"]))
        return 13, lerp(672, 668, k), 1125, lerp(1.16, 1.19, k)
    if t < T["s15"]:      # S14 his medium: the sigh, the get-up (the camera rises with him)
        k = ease_in_out(seg(t, T["up_b"] - 0.1, T["up_c"] + 0.1))
        return 14, lerp(1012, 1000, k), lerp(1140, 1062, k), 1.95
    k = ease_in_out(seg(t, T["s15"], T["end"]))       # S15 wide: he walks into the dark
    return 15, lerp(800, 610, k), 1135, 1.15


def _draw_tired(ctx, t, p):
    """Tiredness (his own scale while he walks into the tunnel's depth, darkened as the
    side tunnel's dark takes him)."""
    pk = {k: v for k, v in p.items() if k not in ("x", "y", "s", "dark")}
    sc, dk = p.get("s", S), p.get("dark", 0.0)
    if dk <= 0.01:
        return human.draw_person(ctx, "tired", p["x"], p["y"], sc, t, **pk)
    ctx.push_group()
    a = human.draw_person(ctx, "tired", p["x"], p["y"], sc, t, **pk)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source_rgba(0.01, 0.015, 0.03, dk)
    ctx.paint()
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint()
    return a


def _beam_amt(t, T):
    """Emb's shaky flashlight deep in the side tunnel: it flicks on with the stumble, sweeps
    across the depth through the yell, then stays, faint and wavering, where he is."""
    on = T["l07"] - 0.3
    return (_ramp(t, on, on + 0.12) * (1.0 - 0.6 * _ramp(t, T["l07e"] - 0.2, T["l07e"] + 0.6))
            * (0.85 + 0.15 * math.sin(t * 23.0) * math.sin(t * 7.3)))


def _beam(ctx, t, T):
    amt = _beam_amt(t, T)
    if amt <= 0.01:
        return
    u = t - (T["l07"] - 0.3)
    # it flicks across the far tunnel section (fast, shaky swings through the yell), then
    # wavers slowly
    fast = 1.0 - _ramp(t, T["l07e"] - 0.3, T["l07e"] + 0.5)
    sweep = (fast * math.sin(u * 2 * math.pi * 1.15) + (1 - fast) * 0.35 * math.sin(u * 2 * math.pi * 0.3))
    shake = 0.05 * math.sin(u * 29.0) + 0.035 * math.sin(u * 47.0 + 1.3)
    ang = 1.1 * sweep + shake                                  # 0 = straight down the tunnel at us
    sx, sy = VP[0] + 22, VP[1] - 14                             # the torch: deep, out of sight
    ctx.save()
    _mouth_path(ctx)
    ctx.clip()
    ctx.set_operator(cairo.OPERATOR_ADD)
    px, py = sx + 46 * math.sin(ang), sy + 16 + 8 * math.cos(ang)   # where it hits the far walls
    core.radial_glow(ctx, px, py, 46, "#ffcf8a", 0.6 * amt)
    core.radial_glow(ctx, sx, sy + 6, 130, "#ffb866", 0.11 * amt)   # faint spill in the depth
    L = 74.0
    for spread, al in ((0.42, 0.04), (0.3, 0.05), (0.19, 0.06), (0.09, 0.08)):
        g = cairo.RadialGradient(sx, sy, 0, sx, sy, L)
        g.add_color_stop_rgba(0.0, 1.0, 0.87, 0.65, al * amt)
        g.add_color_stop_rgba(1.0, 1.0, 0.87, 0.65, 0.0)
        ctx.move_to(sx, sy)
        for i in range(7):
            aa = ang - spread + 2 * spread * i / 6
            ctx.line_to(sx + L * math.sin(aa), sy + L * 0.6 * math.cos(aa))
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()
    ctx.restore()


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
        _beam(ctx, t, T)
        behind = c["y"] < FEET_Y - 20              # Curiosity deep in the side tunnel: behind him
        split = c["wait"]                          # its glowing eyes go between it and him
        with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
            ca = {}
            if behind:
                ca = _draw_cur(ctx, t, c)
            if not split:
                a = _draw_tired(ctx, t, p)
                if not behind:
                    ca = _draw_cur(ctx, t, c)
        if split:
            if "eye_l" in ca and "eye_r" in ca:
                # its two teal eyes, still glowing in the dark down the side tunnel
                (x1, y1), (x2, y2) = ca["eye_l"][:2], ca["eye_r"][:2]
                se = c["s"] * 1.25
                look, lid, blink, gap_k, dx = _wait_eyes(t, T)
                gap = max(95.0, math.hypot(x2 - x1, y2 - y1) / se) * gap_k
                ctx.save()
                _mouth_path(ctx)
                ctx.clip()
                fx.eyes_in_dark(ctx, (x1 + x2) / 2 + dx * se, (y1 + y2) / 2, se, t, kind="curiosity",
                                blink=blink, look=look, gap=gap, lid=lid, tilt=0.05)
                ctx.restore()
            with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
                a = _draw_tired(ctx, t, p)
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
    for n in range(-3, 9):
        tv = T["s9"] + 0.5 + n * 2.6
        if T["s8"] - 0.5 <= tv < T["end"] - 0.3 and not (T["l07"] - 0.5 < tv < T["l07e"]):
            g = -3.0 if n == 0 else (-9.0 if 0 < n < 3 else -12.0)
            ev.append((tv, "drip", g, -0.3))
    ev.append((T["glow"] + 0.05, "sonar_ping_small", -11.0, 0.1))
    # "Maybe even me. ...": the swallow
    ev.append((T["swal"] + 0.04, "gulp", -12.0, 0.05))
    # the eyes' answer: a faint purr from the dark (comfort at a distance)
    ev.append((T["ans"] + 0.15, "creature_purr", -2.0, -0.45))
    # Emb stumbles on it far down the side tunnel (just before the yell)
    ev.append((T["l07"] - 0.42, "footstep", -15.0, -0.6))
    ev.append((T["l07"] - 0.3, "footstep", -13.0, -0.6))
    ev.append((T["l07"] - 0.22, "body_thud", -21.0, -0.6))
    # the sigh, then up off the crate
    ev.append((T["exh"] - 0.03, "sigh", 1.0, 0.05))
    ev.append((T["up_a"] + 0.05, "cloth_rustle", -9.0, 0.05))
    ev.append((T["up_b"] + 0.15, "chair_creak", -9.0, 0.05))
    ev.append((T["up_c"] - 0.02, "footstep", -13.0, 0.05))
    # the walk into the side tunnel: heel strikes at cycle phase .29 + n/2
    x_st = SEAT_X - _foot_shift(1.0)
    n_prev = None
    tt = T["walk0"]
    while tt < T["end"] - 0.05:
        x, _, _, pt, dk = _go_path(tt, T, x_st)
        n_ = math.floor((pt - 0.29) / 0.5)
        if n_prev is not None and n_ != n_prev:
            ev.append((tt, "footstep", -8.0 - 6.0 * dk, clamp(0.1 + (x - 1000) / 1300, -0.5, 0.2)))
        n_prev = n_
        tt += 1.0 / 96.0
    return [e for e in ev if 0.0 <= e[0] < T["end"]]
