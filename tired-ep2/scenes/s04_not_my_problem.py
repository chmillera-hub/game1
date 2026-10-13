"""s04 — "Not my problem" (music: lonely).  Revision 4 (rev 3 + a new end: it walks on alone; Emb).

A quiet CalmCorp service tunnel lit by dim emergency lamps. Tiredness trudges out
of the dark side tunnel (the way back to the shaft and the pods), reaches back and
pulls his hood off in the first light, drops onto a crate. He is not dismissive,
he is overwhelmed: no bandwidth, he fell out of a building today, he has to take
care of himself first ... "But I don't want to abandon you." (its ears lift: a
flicker of hope). Curiosity points back toward the pods and takes his sleeve in its
paws. He means it when he says what CalmCorp is doing is wrong, but he can't see a
way without somebody getting hurt. "Maybe even me." (a scared inward look, a
swallow, his hand tightens). It hears "not right now": the ears lower degree by
degree, it lets go and walks into the dark side tunnel, stops, looks back once.
Alone with a drip, he looks at his bandage (a faint teal glow), groans ... and lifts
his head: its two teal eyes glow a little way down the tunnel. (rev 4:) Its gaze drops
away and it turns and walks on down the tunnel alone, to free its family without him
(gently visible in the dark: soft eye glow, the teal rim catching a little light),
glances back over its shoulder once, goes on deeper. He watches it go: "Okay. I'll
help. Hell or high water." A sad glance at his hands. "...I hope we make it out of
this." A light moves down the tunnel; he notices. Down the tunnel Emb comes the other
way with his torch; the beam swings and lands on it: it stops in the beam, ears up,
tilts its head, takes a curious step toward him; Emb jolts back into the wall, the
beam shaking: "Oh my God! What IS that thing?!" (it crouches low, ears flat, wary in
his beam, as s05 opens). His head snaps toward it; he sighs, gets up and walks into
the tunnel toward them.

All timing comes from info.cue(...) / info.line(...) / info.word_time(...).
World = sets.service_tunnel (people and creature at s=0.75).

Shots (see _times / _cam)
  S1  arrive   0 .. l01.end+.3      wide on the side-tunnel mouth, pan + push-in: walks
                                    out of the dark, pulls the hood back, drops onto the
                                    crate; Curiosity follows and sits; l01
  S2  slump    .. l02b-.2           his medium: head hangs, the near hand rubs his eyes
  S3  me       .. "before"-.12      two-shot: near hand to his chest on "me"
  S3b listen   .. l02b.end+.1       Curiosity CU: "...anyone else" -> eyes to the tunnel
  S3c abandon  .. l02c.end+.1       two-shot, slow push-in: his eyes drop away; on "But"
                                    pupils lead back to it, the head follows; quiet. Its
                                    eyes come back to him, ears dip ... "abandon you":
                                    ears lift (hope). Then its eyes go to the tunnel
  S4  point    .. l03-.15           two-shot: points down the tunnel, hop-turns up and
                                    takes his sleeve cuff in both paws, one gentle tug
  S5  wrong    .. l04-.15           closer two-shot: "...is wrong"; ears up with hope
  S6  hurt-who .. hurt-.1           his CU: "...somebody getting hurt"; "Maybe even me.":
                                    the camera eases down to take in his near hand; eyes
                                    drop + unfocus, ("scared" pause:) a swallow, the
                                    hand tightens into a fist on his knee, hold
  S7  hurt     .. leave+.1          Curiosity CU: ears lower degree by degree, tears,
                                    it lets go, turns its head away
  S8a leave / S8b back              it walks into the side tunnel, stops, looks back once
  S9  alone    .. l05.end+.1        his medium: drip; bandage glow; "...Ugh." eyes shut
  S10 follow   .. walkoff+.42       two-plane wide: the head hangs, then lifts to its two
                                    teal eyes in the dark (fx.eyes_in_dark); on 'walkoff'
                                    its gaze drops away, the pair turns away (cut on it)
  S10b walkoff .. walkoff+2.55      closer down the side tunnel: it walks on alone (dark,
                                    rim + eye glow), glances back over its shoulder, on
  S10c watch   .. "I'll"-.12        two-plane: he watches it go (it is small, deeper,
                                    still walking): brows up; "Okay."
  S11 commit   .. hush+1.0          his medium, slow push-in (rev 3): "I'll help. Hell or
                                    high water."; 'glance' at his hands and back; l06b;
                                    the after-beat; a warm light flickers in from the
                                    tunnel: he notices (pupils, head turns, lids lift a hair)
  S12 meet     .. "What"-.1         down the side tunnel (medium-far): Emb comes up it with
                                    his torch, stops; the beam swings onto it: it stops in
                                    the beam, ears up, curious tilt, a curious step; Emb
                                    jolts back into the wall (push in), "Oh my God!", it
                                    crouches low, ears flat (wary)
  S14 sighup   .. standing          his medium (rises with him): "What IS that thing?!":
                                    the head snaps toward it; a visible sigh, lean
                                    forward, hands on knees, push up
  S15 go       .. end               wide, panning left: he walks to the side tunnel and a
                                    few steps into it; deep inside, Emb against the wall,
                                    his beam on it crouched
"""
import math
import os

import cairocffi as cairo

from engine import core, sets, human, fx, props
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

# sit_crate with longer shins so his soles reach the floor in front of the set's crate.
# Arm layers are pinned (no per-frame layer decisions while hands reach).
_SITP = {"base": "sit_crate", "ll_p": 1.5, "lr_p": 1.48, "ll_k": 1.45, "lr_k": 1.42,
         "al_layer": "mid", "ar_layer": "mid"}
# the walk with its own voted layers pinned: far (r) arm behind the body, near (l) arm
# over the torso but UNDER the head (the hood pull happens behind the head)
_WALKP = {"base": "walk", "al_layer": "mid", "ar_layer": "back"}
_STAND_WL = {"base": "stand", "al_layer": _WALKP.get("al_layer", ""), "ar_layer": _WALKP.get("ar_layer", "")}   # anatomy pass

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
        l05=c("s04_l05"), l05e=c("s04_l05.end"), follow=c("follow"), walkoff=c("walkoff"),
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
    # (Emb, on screen in the tunnel) "Oh my God! What IS that thing?!"
    T["w07_god"] = wt("s04_l07", 2)
    T["w07_what"] = wt("s04_l07", 3)
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
    # --- follow (S10 two-plane) .. walkoff (S10b closer on the side tunnel: it walks on down the
    # tunnel alone, glances back once; S10c two-plane: he watches it go, "Okay.") .. l06 / glance /
    # l06b (S11 his medium) .. hush: he notices a light (S11) .. the encounter down the tunnel
    # (S12: Emb's beam finds it, it is curious, Emb jolts back, "Oh my God!") .. "What IS that
    # thing?!" (S14 his medium: the snap, the sigh, the get-up) .. go (S15 wide)
    T["lift"] = T["follow"] + 0.05                 # pupils to the tunnel, the head lifts after
    # rev 3's S10 drift ran to its cut at "I'll": keyed the same way from 'follow' (so 'follow'
    # is untouched), the walkoff cut comes before it ends
    T["s10cam1"] = T["follow"] + 1.1 + (T["w06_ill"] - T["l06"]) - 0.12
    W = T["walkoff"]
    T["wo_d"] = T["l06"] - T["follow"] - 1.1        # the time 'walkoff' inserted before l06
    # where rev 3's keys after 'follow' sat (l06 came 1.1 s after 'follow'): its follow beat is
    # replayed exactly up to 'walkoff', the new keys continue from its values there
    T["r3_okay"] = T["w06_okay"] - T["wo_d"]
    T["r3_help"] = T["w06_help"] - T["wo_d"]
    T["wo_turn"] = W + 0.08                        # its gaze drops, the pair turns away (two-plane)
    T["s10b"] = W + 0.42                           # cut on the turn: closer on the side tunnel
    T["wo_walk"] = T["s10b"]                       # standing, turned away, first step deeper
    T["wo_back"] = W + 1.3                         # glance back over its shoulder ...
    T["wo_fwd"] = W + 2.15                         # ... and on, deeper
    T["s10c"] = W + 2.55                           # two-plane: he watches it go
    T["s11"] = T["w06_ill"] - 0.12
    T["gl0"] = T["glance"] + 0.08                  # sad glance down at his hands ...
    T["gl1"] = T["gl0"] + 0.75                     # ... and back to it, going away down the tunnel
    T["s11e"] = max(T["l06be"] - 0.1, T["q6b"] + 0.3)    # end of rev 3's S11 push-in (then held)
    H = T["hush"]
    T["e_on"] = H + 0.2                            # Emb's torch comes along the tunnel, deep down
    T["light"] = H + 0.3                           # ... its light reaches the corridor
    T["notice"] = H + 0.42                         # he notices (pupils, lids, head forward)
    # rev 3's old S13 cut (two-plane) after l06b: his after-beat eased toward it; kept up to the light
    T["s13_r3"] = max(T["l06be"] + 2.0 - 0.95, T["s11e"] + 1.25)
    T["s12"] = H + 1.0                             # cut: down the tunnel, the encounter
    T["e_stop"] = H + 1.6                          # Emb stops (two eyes in the dark?)
    T["bm_sw"] = H + 1.62                          # the beam swings ...
    T["bm_on"] = H + 2.0                           # ... and lands on it
    T["c_stop"] = T["bm_on"] + 0.05                # it stops in the beam, ears up
    T["c_tilt"] = T["bm_on"] + 0.5                 # a curious head tilt
    T["c_step"] = T["bm_on"] + 1.0                 # a curious step toward him
    T["c_step1"] = T["c_step"] + 0.42
    T["e_jolt"] = max(T["c_step1"] + 0.15, T["l07"] - 0.7)    # Emb jolts back, the beam shaking
    T["e_back1"] = T["e_jolt"] + 0.55              # ... backs into the wall
    T["c_flat"] = T["l07"] + 0.08                  # the yell: ears flat, it crouches (wary)
    T["s14"] = T["w07_what"] - 0.1                 # cut: Tiredness, "What IS that thing?!"
    T["snap"] = T["s14"] + 0.08                    # his head snaps toward it
    sg = T["sighup"]
    T["up_c"] = max(T["go"] + 0.15, sg + 1.7)      # standing (he starts to walk on 'go')
    T["up_b"] = T["up_c"] - 0.75                   # push up off his knees
    T["up_a"] = T["up_b"] - 0.3                    # anticipation: leans forward, hands to knees
    T["inh"] = max(T["l07e"] + 0.25, sg - 0.2)     # inhale (shoulders up) ...
    T["exh"] = T["inh"] + 0.3                      # ... the exhale (shoulders drop)
    T["exh1"] = min(T["exh"] + 0.55, T["up_a"] - 0.02)
    T["walk0"] = T["up_c"] + 0.2                   # (turns to the tunnel first, then walks)
    T["s15"] = T["up_c"] - 0.12
    return T


def _r3w(T, k0, v0, k1, v1):
    """rev 3's value at 'walkoff' of a key pair (k0, v0) -> (k1, v1) that spanned it."""
    return _tw(T["walkoff"], [(k0, v0), (k1, v1)])


def _r3v(T, k0, v0, v1, dt=0.0):
    """rev 3 eased this value from (k0, v0) toward v1 at its old S13 cut (+dt) after l06b. Its
    value at the light (T["notice"]), where the rev-4 keys take over."""
    return _tw(T["notice"], [(k0, v0), (T["s13_r3"] + dt, v1)])


def _r3c(t, T, val, k0, v0, v1, dt=0.0, until=0.0):
    """... and rev 3's own curve from k0 up to the light (+until), so the after-beat of l06b
    plays exactly as it did."""
    if k0 <= t < T["notice"] + until:
        return _tw(min(t, T["notice"]), [(k0, v0), (T["s13_r3"] + dt, v1)])
    return val


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
                pose = _pose_of((_WALKP, _STAND_WL, k1))   # same arm layers: no hand jump mid-blend
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
                  (T["walkoff"] + 0.3, 0.24), (T["walkoff"] + 1.2, 0.28),             # it goes: sinks a hair
                  (T["s10c"] + 0.1, 0.28),                                          # ... lifts it again
                  (T["w06_okay"] - 0.02, 0.24), (T["w06_okay"] + 0.18, 0.3), (T["w06_okay"] + 0.45, 0.25),
                  (T["w06_help"], 0.25), (T["w06_help"] + 0.15, 0.31), (T["w06_help"] + 0.45, 0.25),
                  (T["w06_water"], 0.25), (T["w06_water"] + 0.2, 0.3), (T["l06e"], 0.26),
                  (T["gl0"] + 0.12, 0.26), (T["gl0"] + 0.4, 0.38),                # glance down ...
                  (T["gl1"], 0.38), (T["gl1"] + 0.3, 0.27),                         # ... and back
                  (T["l06b"] + 0.2, 0.28), (T["l06be"], 0.33),
                  (T["notice"] + 0.08, _r3v(T, T["l06be"], 0.33, 0.36)),
                  (T["notice"] + 0.42, 0.25),                                       # a light: head lifts
                  (T["snap"], 0.25), (T["snap"] + 0.12, 0.15), (T["snap"] + 0.3, 0.2),   # the snap
                  (T["l07e"], 0.21),
                  (T["inh"], 0.21), (T["exh"], 0.16), (T["exh1"], 0.42),            # sigh: head sinks
                  (T["up_a"] + 0.05, 0.42), (T["up_b"], 0.24)])                     # looks ahead, rises
    nod = _r3c(t, T, nod, T["l06be"], 0.33, 0.36, until=0.08)
    lean = _tw(t, [(T["slump"] + 0.05, 0.5), (T["slump"] + 0.55, 0.58), (T["hand_dn"], 0.58),
                   (T["hand_dn1"], 0.5),
                   (T["notice"], 0.5), (T["notice"] + 0.4, 0.53),                       # peers at it
                   (T["snap"], 0.53), (T["snap"] + 0.1, 0.4), (T["snap"] + 0.45, 0.46),   # jolt back
                   (T["inh"], 0.46), (T["exh"], 0.43), (T["exh1"], 0.56),
                   (T["up_a"], 0.56), (T["up_b"], 0.84)])                        # anticipation
    hunch = _tw(t, [(T["l01e"], 0.65), (T["slump"] + 0.55, 0.75), (T["hand_dn1"], 0.65),
                    (T["l04e"], 0.65), (T["l04b"] - 0.15, 0.8),                # held breath
                    (T["drop4b"] + 0.4, 0.77), (T["fist0"], 0.76), (T["fist1"], 0.81),
                    (T["s7"] + 0.4, 0.72), (T["s8"], 0.68),
                    (T["l05"], 0.65), (T["l05"] + 0.4, 0.5), (T["l05e"] + 0.1, 0.72),
                    (T["lift"] + 0.6, 0.66), (T["walkoff"], _r3w(T, T["lift"] + 0.6, 0.66, T["r3_help"], 0.6)),
                    (T["lift"] + 0.6 + T["wo_d"], 0.66),                              # (back for l06)
                    (T["w06_help"], 0.6), (T["l06e"], 0.62),
                    (T["gl0"] + 0.4, 0.68), (T["l06b"] + 0.3, 0.72),
                    (T["notice"], _r3v(T, T["l06b"] + 0.3, 0.72, 0.68)), (T["notice"] + 0.35, 0.68),
                    (T["snap"], 0.68), (T["snap"] + 0.12, 0.8), (T["snap"] + 0.45, 0.74),
                    (T["inh"], 0.74), (T["exh"], 1.0),                          # sigh: shoulders up ...
                    (T["exh1"], 0.36),                                          # ... and they drop
                    (T["up_b"], 0.5)])
    hunch = _r3c(t, T, hunch, T["l06b"] + 0.3, 0.72, 0.68)
    if T["lift"] + 0.6 <= t < T["walkoff"]:          # the follow beat exactly as rev 3
        hunch = _tw(t, [(T["lift"] + 0.6, 0.66), (T["r3_help"], 0.6)])
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
        (T["notice"], _r3v(T, T["gl1"] + 0.15, (-1.0, 0.04), (-1.0, 0.05))),
        (T["notice"] + 0.12, (-1.1, -0.12)),                                        # the light, deeper
        (T["snap"] - 0.02, (-1.1, -0.12)), (T["snap"] + 0.07, (-1.1, -0.14)),      # the voice
        (T["l07e"], (-1.05, -0.08)),
        (T["exh"], (-0.95, 0.1)), (T["exh1"], (-0.8, 0.45)),                       # sigh: eyes drop
        (T["up_a"] + 0.1, (-0.8, 0.45)), (T["up_a"] + 0.3, (-1.0, 0.0))])           # then ahead
    look = _r3c(t, T, look, T["gl1"] + 0.15, (-1.0, 0.04), (-1.0, 0.05))
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
                        (T["notice"] + 0.12, _r3v(T, T["gl1"] + 0.4, -0.3, -0.24)),
                        (T["notice"] + 0.45, -0.42),
                        (T["snap"], -0.42), (T["snap"] + 0.1, -0.7), (T["snap"] + 0.25, -0.62),
                        (T["l07e"], -0.58),
                        (T["exh1"], -0.4), (T["up_b"], -0.3), (T["up_c"], -0.15)])
    head_turn = _r3c(t, T, head_turn, T["gl1"] + 0.4, -0.3, -0.24, until=0.12) + shake
    head_tilt = _tw(t, [(T["lk"] + 0.15, 0.0), (T["lk"] + 0.55, -0.045), (T["q2c"] + 0.2, -0.045),
                        (T["pt_up"] + 0.4, 0.0),
                        (T["l03"] - 0.2, 0.0), (T["l03"] + 0.3, -0.05), (T["l03e"] + 0.3, -0.03),
                        (T["beat"] + 0.4, 0.0),
                        (T["l06b"], 0.0), (T["l06b"] + 0.5, -0.04),
                        (T["notice"], _r3v(T, T["l06b"] + 0.5, -0.04, -0.03)),
                        (T["notice"] + 0.4, -0.015), (T["snap"], 0.0)])
    head_tilt = _r3c(t, T, head_tilt, T["l06b"] + 0.5, -0.04, -0.03)

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
                   (T["q6b"] + 0.4, 0.15), (T["notice"], _r3v(T, T["q6b"] + 0.4, 0.15, 0.0, 0.4)),
                   (T["notice"] + 0.35, 0.0)])
    fear = _r3c(t, T, fear, T["q6b"] + 0.4, 0.15, 0.0, dt=0.4)
    if fear > 0.005 and ex_ == "sad":
        ex_ = ("sad", "terrified", fear)
    sw = T["swal"]
    face = _addf(
        {"head_turn": head_turn, "head_tilt": head_tilt},
        # inner brows up: overwhelmed / sincere / worried
        {"brow_ang": _r3c(t, T, _tw(t, [(T["l01"] - 0.3, 0.0), (T["l01"] + 0.1, 0.16), (T["l01e"] + 0.3, 0.1),
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
                             (T["walkoff"], _r3w(T, T["lift"] + 0.6, 0.16, T["r3_okay"], 0.14)),
                             (T["walkoff"] + 0.9, 0.27),                                   # it goes alone
                             (T["s10c"] + 0.1, 0.27),
                             (T["w06_okay"], 0.14), (T["w06_help"], 0.07), (T["l06e"], 0.08),
                             (T["gl0"] + 0.25, 0.24), (T["gl1"] + 0.3, 0.18),
                             (T["l06b"] + 0.2, 0.3), (T["w6b_this"], 0.34), (T["q6b"] + 0.5, 0.24),
                             (T["notice"], _r3v(T, T["q6b"] + 0.5, 0.24, 0.2, 0.3)),
                             (T["notice"] + 0.3, 0.17),
                             (T["snap"], 0.17), (T["snap"] + 0.15, 0.1),
                             (T["exh1"], 0.12), (T["up_c"], 0.08)]),
                          T["q6b"] + 0.5, 0.24, 0.2, dt=0.3)
                     if not (T["lift"] + 0.6 <= t < T["walkoff"])
                     else _tw(t, [(T["lift"] + 0.6, 0.16), (T["r3_okay"], 0.14)]),
         "lid": _tw(t, [(T["l01e"], 0.0), (T["l01e"] + 0.3, 0.05), (T["slump"], 0.05), (T["l02"], 0.0),
                        (T["lk"], 0.0), (T["w2c_dont"], 0.04), (T["q2c"] + 0.3, 0.04), (T["pt_up"] + 0.4, 0.0),
                        (T["beat"] + 0.5, 0.0), (T["l04"] + 0.2, 0.06),
                        (T["l04e"] + 0.2, 0.06), (T["l04e"] + 0.5, -0.07),           # lids lift a hair
                        (T["w4b_me"] + 0.2, -0.05), (T["drop4b"] + 0.4, 0.04),      # ... then drop
                        (T["fist1"], 0.06), (T["s8"] + 0.2, 0.06), (T["s9"], 0.0),
                        (T["w06_okay"], 0.0), (T["w06_help"], 0.04), (T["gl1"] + 0.3, 0.03),
                        (T["notice"], 0.03), (T["notice"] + 0.15, -0.08),               # the light
                        (T["snap"], -0.08), (T["snap"] + 0.1, -0.1), (T["l07e"], -0.06),  # small start
                        (T["exh"], 0.0)]),
         # "Maybe even me. ...": the eyes go unfocused (inward)
         "focus": -0.6 * _ramp(t, T["drop4b"], T["drop4b"] + 0.45) * (1 - _ramp(t, T["s7"] + 0.6, T["s8"]))},
        # the swallow: chin dips and bobs back, lips pressed, the brows twitch up
        {"head_nod": _bump(t, sw, sw + 0.3, 0.06) - _bump(t, sw + 0.22, sw + 0.55, 0.015)
         - 0.13 * _ramp(t, T["snap"], T["snap"] + 0.1) * (1 - _ramp(t, T["l07e"], T["exh1"]))
         # after the groan the head hangs; on 'follow' he lifts it to the eyes in the dark
         + _tw(t, [(T["l05e"] + 0.05, 0.0), (T["l05e"] + 0.5, 0.15), (T["lift"] + 0.12, 0.15),
                   (T["lift"] + 0.6, -0.03), (T["gl0"] + 0.1, -0.03), (T["gl0"] + 0.4, 0.0)]),
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
         + _bump(t, T["gl0"] + 0.1, T["gl1"] + 0.3, 0.35) + _bump(t, T["q6b"] + 0.03, T["q6b"] + 0.8, 0.45)
         + _bump(t, T["walkoff"] + 0.05, T["walkoff"] + 0.9, 0.3)},
        # the sigh: a visible exhale ("hah")
        {"open": _bump(t, T["exh"] - 0.05, T["exh1"], 0.24)},
        # alone: inner brows up a hair at the glow
        {"brow_ang": _bump(t, T["glow"] - 0.1, T["arm1"] + 0.6, 0.22)},
        # Emb's yell: brows jump up (a small start); before it, a light down the tunnel: a hair up
        {"brow": _bump(t, T["snap"], T["l07e"] + 0.3, 0.3)
         + 0.16 * _ramp(t, T["notice"], T["notice"] + 0.3) * (1 - _ramp(t, T["snap"], T["snap"] + 0.3))},
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
        if b0 <= t <= b0 + 0.26:                               # (one plain blink keeps it alive)
            blink = _tw(t, [(b0, 0.0), (b0 + 0.08, 1.0), (b0 + 0.12, 1.0), (b0 + 0.26, 0.0)])
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
    if T["walkoff"] + 1.7 <= t < T["walkoff"] + 1.98:         # (one plain blink while it goes)
        b0 = T["walkoff"] + 1.7
        blink = _tw(t, [(b0, 0.0), (b0 + 0.08, 1.0), (b0 + 0.12, 1.0), (b0 + 0.28, 0.0)])
    if T["gl1"] + 0.1 <= t < T["q6b"] + 0.5:                   # held on it through l06b
        blink = 0.0
    if T["notice"] - 0.05 <= t < T["s12"]:                     # eyes on the light
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
                wait=False, free=False, warm=0.0, halo=0.0)


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
    if t < T["s10b"]:
        return _cur_wait(t, T, d)
    return _cur_go(t, T, d)


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
    toward the mouth, waiting (only its eyes really show: fx.eyes_in_dark over a dark body)."""
    x, y, f = _depth(K_WAIT)
    d.update(x=x, y=y, s=S * f, pose="sit", flip=False, face=0.15, expr="sad", ears=0.18,
             look=(0.35, -0.1), tilt=0.06, glow=0.4, dark=0.86, clip=True, wait=True, blink=1.0)
    return d


def _wait_eyes(t, T):
    """(look, lid, blink, gap_k, dx) of its eyes in the dark (S10 two-plane): they meet his look
    (a little hope) ... then on 'walkoff' its gaze drops away down the tunnel, the lids sink and
    the pair turns away (narrower, sliding deeper): it is going on alone (cut on the turn)."""
    W = T["walkoff"]
    r3 = [(T["lift"] + 0.5, (0.35, 0.0)), (T["s11e"] + 1.25 - T["wo_d"], (0.38, 0.03))]   # rev 3 (follow)
    look = _tw(t, [(T["s10"], (0.25, 0.05)), (T["lift"] + 0.3, (0.25, 0.05)),
                   (T["lift"] + 0.5, (0.35, 0.0)), (W, _tw(W, r3)), (W + 0.22, (-0.4, 0.3))])
    if T["lift"] + 0.5 <= t < W:
        look = _tw(t, r3)
    lid = _tw(t, [(T["lift"] + 0.45, 0.36), (T["lift"] + 0.8, 0.28), (W + 0.1, 0.28), (W + 0.35, 0.42)])
    blink = 0.0
    gap_k = _tw(t, [(W + 0.12, 1.0), (T["s10b"], 0.76)])
    dx = _tw(t, [(W + 0.12, 0.0), (T["s10b"], -14.0)])
    return look, lid, blink, gap_k, dx


# ---- walkoff .. the end: it walks on down the side tunnel alone, then meets Emb ------------
K_WO = 0.045                   # depth it gains per second of steps (cycle rate 1) walking away
X_WO = 60.0                    # ... and how far across (mouth-floor px) it drifts per second of steps
X1A, X1B, X1C = 500.0, 455.0, 432.0     # its lane (mouth-floor x) as it crosses toward Emb (S12) ...
K1A, K1B, K1C = 0.485, 0.5, 0.507       # ... and its depth there (stops in the beam / the step)
EX0, EXW = 175.0, 138.0        # Emb's lane coming up the tunnel, and backed against its (left) wall
KE0, KE1, KE2 = 1.15, 0.95, 1.0     # Emb's depth: out of the deep dark -> stops -> backs up
EMB_FLASH_S = 0.5              # his torch prop at S (as in s05)


def _integ(t, keys):
    """Integral up to t of a piecewise-linear rate [(t, r), ...] (0 before, held after)."""
    acc = 0.0
    for (a, ra), (b, rb) in zip(keys, keys[1:]):
        if t <= a:
            return acc
        if t < b:
            u = t - a
            return acc + (ra + 0.5 * (rb - ra) * u / (b - a)) * u
        acc += 0.5 * (ra + rb) * (b - a)
    return acc + keys[-1][1] * max(0.0, t - keys[-1][0])


def _wo_rate(T):
    return [(T["s10b"], 0.0), (T["s10b"] + 0.25, 0.72), (T["wo_back"], 0.72), (T["wo_back"] + 0.25, 0.45),
            (T["wo_fwd"], 0.45), (T["wo_fwd"] + 0.3, 0.7)]


def _c1_pos(t, T):
    """(x0, k) of its walk across the tunnel toward Emb (S12), then the curious step, the recoil."""
    x0 = _tw(t, [(T["s12"], X1A), (T["c_stop"] + 0.2, X1B)], ease_out)
    k = _tw(t, [(T["s12"], K1A), (T["c_stop"] + 0.2, K1B)], ease_out)
    if t > T["c_step"]:
        u = ease_in_out(seg(t, T["c_step"], T["c_step1"]))
        x0, k = lerp(X1B, X1C, u), lerp(K1B, K1C, u)
    if t > T["c_flat"]:
        x0 += 9.0 * ease_out(seg(t, T["c_flat"], T["c_flat"] + 0.3))      # flinches back a hair
    return x0, k


def _cur_go(t, T, d):
    """walkoff: standing, turned away, it walks on down the dark side tunnel alone (gently
    visible: soft eye glow, the teal rim catching a little light), glances back over its
    shoulder once, goes on deeper; through his lines it keeps going (slower). hush (S12): it
    crosses toward a light coming up the tunnel; Emb's beam lands on it: it stops in the beam,
    ears up, a curious head tilt, a curious step toward him; Emb jolts back; the yell: ears
    flat, it crouches low, wary, in his beam (as s05 opens)."""
    W = T["walkoff"]
    d.update(flip=True, expr="sad", ears=0.18, glow=0.9, dark=0.58, clip=True, free=True, halo=0.09,
             face=0.55, look=(-0.4, 0.3), tilt=0.08, pose="walk")
    ph = _integ(t, _wo_rate(T))
    if t < T["s12"]:
        # deeper, and a little across toward the middle of the tunnel (its side-on steps carry it)
        k = K_WAIT + K_WO * ph
        x0 = MOUTH_X0 - X_WO * ph
        if t >= T["s11"]:              # (off screen through his lines: on, slower, to where S12 finds it)
            ph1 = _integ(T["s11"], _wo_rate(T))
            u = seg(t, T["s11"], T["s12"])
            k, x0 = lerp(K_WAIT + K_WO * ph1, K1A, u), lerp(MOUTH_X0 - X_WO * ph1, X1A, u)
        x, y, f = _depth(k, x0)
        d.update(x=x, y=y, s=S * f, pose_t=ph)
        if t < T["s10b"] + 0.3:        # first step out of the stand
            d["pose_from"], d["pose_mix"] = "stand", seg(t, T["s10b"], T["s10b"] + 0.3)
        # the glance back over its shoulder (pupils first, then the head), then on
        b0, b1 = T["wo_back"], T["wo_fwd"]
        d["face"] = _tw(t, [(b0 + 0.08, 0.55), (b0 + 0.38, -1.0), (b1, -1.0), (b1 + 0.3, 0.55)])
        d["look"] = _tw(t, [(b0, (-0.4, 0.3)), (b0 + 0.18, (0.75, -0.2)), (b1 - 0.05, (0.72, -0.16)),
                            (b1 + 0.15, (-0.4, 0.3))])
        d["ears"] = _tw(t, [(b0 + 0.2, 0.18), (b0 + 0.5, 0.27), (b1 - 0.1, 0.24), (b1 + 0.4, 0.14)])
        d["tilt"] = _tw(t, [(b0 + 0.1, 0.08), (b0 + 0.4, 0.02), (b1, 0.02), (b1 + 0.35, 0.13)])
        if b0 - 0.2 < t < b1 + 0.3:
            d["blink"] = 0.0
        if t >= T["s10c"] - 0.2:
            d["dark"] = 0.62
            d["glow"] = 0.85
        return d
    # ---- S12: across toward the light; the beam lands; stops; curious; the step; wary crouch
    x0, k = _c1_pos(t, T)
    x, y, f = _depth(k, x0)
    xs0 = _depth(K1A, X1A)[0]
    d.update(x=x, y=y, s=S * f, pose_t=(xs0 - x) / (CUR_V * f))     # foot-locked to its travel
    on, cs = T["bm_on"], T["c_stop"]
    lit = ease_out(seg(t, on - 0.04, on + 0.14))
    d["dark"] = lerp(0.62, 0.12, lit)
    d["warm"] = 0.16 * lit
    d["halo"] = 0.09 * (1.0 - lit)
    d["glow"] = lerp(0.85, 0.95, lit)
    if t >= cs:
        d["pose_from"], d["pose"], d["pose_mix"] = "walk", "stand", seg(t, cs, cs + 0.25)
    if T["c_step"] < t < T["c_step1"] + 0.2:                  # the curious step
        d["pose_from"], d["pose"] = "stand", "walk"
        d["pose_mix"] = 0.85 * _bump(t, T["c_step"] - 0.05, T["c_step1"] + 0.2)
    cf = T["c_flat"]
    if t >= cf:                                               # the yell: it crouches low, wary
        d["pose_from"], d["pose"] = "stand", "crouch"
        d["pose_mix"] = 0.55 * ease_out(seg(t, cf, cf + 0.25)) + 0.08 * _bump(t, cf + 0.9, cf + 2.2)
    # face: head turned toward him (forward = screen-left, up the tunnel)
    d["face"] = _tw(t, [(cs, 0.55), (cs + 0.3, 0.9), (cf, 0.95), (cf + 0.2, 1.0)])
    d["look"] = _tw(t, [(on, (-0.4, 0.3)), (on + 0.12, (-0.6, -0.45)), (cf, (-0.62, -0.45)),
                        (cf + 0.12, (-0.85, -0.4))])
    tl, ts = T["c_tilt"], T["c_step"]
    ears = _tw(t, [(on, 0.18), (on + 0.3, 0.84)], ease_out)
    if t >= T["e_jolt"]:
        ears = _tw(t, [(T["e_jolt"], 0.84), (T["e_jolt"] + 0.15, 0.7)])
    if t >= cf:
        ears = _tw(t, [(cf, 0.7), (cf + 0.22, 0.04)]) + (0.015 * math.sin(t * 23.0) if t > cf + 0.3 else 0.0)
    d["ears"] = ears
    if t >= on + 0.05:
        d["expr"] = "surprised_soft"
    if t >= tl:
        d["expr"] = "curious"
    if t >= T["e_jolt"] + 0.1:
        d["expr"] = "wide"
    d["tilt"] = _tw(t, [(tl, 0.0), (tl + 0.3, -0.08), (ts + 0.2, -0.08), (ts + 0.5, -0.03),
                        (T["e_jolt"] + 0.1, 0.0), (cf, 0.0), (cf + 0.25, 0.1)])
    d["tail_curl"] = _tw(t, [(tl + 0.1, 0.0), (tl + 0.5, 0.22), (T["e_jolt"], 0.22), (T["e_jolt"] + 0.2, 0.0)])
    # a blink at the glare; eyes locked wide on him once he yells
    b = on + 0.14
    if b <= t < b + 0.2:
        d["blink"] = _tw(t, [(b, 0.0), (b + 0.07, 1.0), (b + 0.1, 1.0), (b + 0.2, 0.0)])
    if t >= T["e_jolt"]:
        d["blink"] = 0.0
    return d


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
    if c["halo"] > 0.005:        # (rev 4) a soft teal shine around it in the dark
        core.radial_glow(ctx, c["x"] - 30 * c["s"], c["y"] - 150 * c["s"], 330 * c["s"], "power", c["halo"])
    grouped = c["alpha"] < 0.999 or c["dark"] > 0.01 or c["warm"] > 0.01
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
        if c["warm"] > 0.01:     # (rev 4) in Emb's torch beam: a warm tint
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ATOP)
            core.set_color(ctx, core.alpha("#ffcf8a", c["warm"]))
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
    if t < T["s10b"]:     # S10 two-plane: him on the crate, its eyes in the dark side tunnel
        k = smoothstep(seg(t, T["s10"], T["s10cam1"]))
        return 10, lerp(690, 684, k), 1140, lerp(1.19, 1.22, k)
    if t < T["s10c"]:     # S10b closer down the side tunnel: it walks on alone, glances back once
        k = ease_in_out(seg(t, T["s10b"], T["s10c"]))
        return 101, lerp(352, 348, k), lerp(1136, 1128, k), lerp(3.0, 3.15, k)
    if t < T["s11"]:      # S10c two-plane: he watches it go ... "Okay."
        k = smoothstep(seg(t, T["s10c"], T["s11"]))
        return 102, lerp(684, 680, k), 1140, lerp(1.22, 1.24, k)
    if t < T["s12"]:      # S11 his medium: "I'll help...", the glance, "...I hope...", a light
        k = ease_in_out(seg(t, T["s11"], T["s11e"]))
        return 11, lerp(975, 985, k), lerp(1160, 1140, k), lerp(2.35, 2.7, k)
    if t < T["s14"]:      # S12 down the side tunnel: the encounter; Emb's jolt: a push in on "Oh my God!"
        k = ease_in_out(seg(t, T["s12"], T["e_jolt"]))
        k2 = ease_out(seg(t, T["e_jolt"], T["e_jolt"] + 0.6))
        return (12, lerp(lerp(320, 315, k), 306, k2), lerp(lerp(1076, 1069, k), 1052, k2),
                lerp(lerp(3.6, 3.9, k), 4.45, k2))
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


# ----------------------------------------------------------------------------
# rev 4: Embarrassment coming up the side tunnel with his torch (the encounter)
# ----------------------------------------------------------------------------
def _depth_p(k, x0, y0=FEET_Y):
    """Side-tunnel depth k on lane x0 (mouth-floor x) -> (x, y, scale) for a person."""
    f = 1.0 / (1.0 + 5.0 * k)
    return VP[0] + (x0 - VP[0]) * f, VP[1] + (y0 - VP[1]) * f, f


_E_GRIP = {"ar_h": "grip", "ar_layer": "front", "al_layer": "mid"}     # (arm layers pinned: no flicker)
_EMB_WALK = dict(_E_GRIP, base="walk")
_EMB_STAND = dict(_E_GRIP, base="stand", al_h="relaxed")
_EMB_FROZEN = dict(_E_GRIP, base="stand", al_h="splay", hunch=0.5, lean=-0.04)
_EMB_JOLT = dict(_E_GRIP, base="stand", al_h="splay", hunch=0.9, lean=-0.14, lift=16)
_EMB_WALL = dict(_E_GRIP, base="stand", al_h="splay", lean=-0.14, chest=-0.12, neck=-0.1, hunch=0.95)


def _emb(t, T, c):
    """Embarrassment's state (world), or None before he comes up the tunnel. c = the creature
    (his beam finds it and stays on it)."""
    if t < T["e_on"]:
        return None
    on, st, sw, bm, jt, b1 = T["e_on"], T["e_stop"], T["bm_sw"], T["bm_on"], T["e_jolt"], T["e_back1"]
    u = seg(t, on, st)
    k = lerp(KE0, KE1, 1.0 - (1.0 - u) ** 1.6)            # walks up the tunnel, slowing to a stop
    x0 = EX0
    if t > jt:                                             # jolts back, shuffles back into the wall
        v = ease_in_out(seg(t, jt + 0.06, b1))
        k, x0 = lerp(KE1, KE2, v), lerp(EX0, EXW, v)
    x, y, f = _depth_p(k, x0)
    sE = S * f
    pt = (t - on) * 0.95
    # body
    if t < st:
        pose = _EMB_WALK
    elif t < bm + 0.1:
        pose = _pose_of((_EMB_WALK, _EMB_STAND, smoothstep(seg(t, st, st + 0.3))))
    elif t < jt:
        pose = _pose_of((_EMB_STAND, _EMB_FROZEN, smoothstep(seg(t, bm + 0.1, bm + 0.4))))
    elif t < jt + 0.12:
        pose = _pose_of((_EMB_FROZEN, _EMB_JOLT, ease_out(seg(t, jt, jt + 0.12))))
    else:
        pose = _pose_of((_EMB_JOLT, _EMB_WALL, smoothstep(seg(t, jt + 0.2, b1))))
        pose = dict(pose) if isinstance(pose, dict) else pose
    bob = 0.0
    if jt + 0.12 < t < b1:                                 # two shuffling steps back
        bob = 9.0 * abs(math.sin(math.pi * 2.0 * seg(t, jt + 0.12, b1)))
    turn = _tw(t, [(st, 0.05), (st + 0.35, 0.3), (jt, 0.3), (jt + 0.15, 0.42), (b1, 0.45)])
    # face
    expr = "neutral"
    if t >= bm + 0.08:
        expr = "frozen_shock"
    if t >= jt:
        expr = "terrified"
    look = _tw(t, [(on, (0.1, 0.5)), (st - 0.1, (0.1, 0.5)), (st + 0.05, (0.45, 0.42)),
                   (bm, (0.5, 0.55)), (bm + 0.1, (0.55, 0.62))])
    face = {"brow_ang": _tw(t, [(on, 0.22), (st, 0.22), (st + 0.2, 0.3)]),
            "brow": 0.2 * _ramp(t, st, st + 0.2)}
    if t >= jt:
        face.update(head_tilt=0.015 * math.sin(t * 19.0), wobble=0.35,
                    squash=-0.07 * _bump(t, jt, jt + 0.3))
    blink = None
    if bm - 0.05 <= t < T["l07e"] + 0.4:
        blink = 0.0
    # the torch hand (world reach target) and the near hand
    if t < st:
        hr = (x + 70 * sE, y - (520 + 10 * math.sin(pt * 2 * math.pi)) * sE)
    elif t < jt:
        hr = (x + lerp(70, 92, _ramp(t, st, bm)) * sE, y - lerp(520, 585, _ramp(t, st, bm)) * sE)
    else:
        hr = (x + lerp(92, 80, _ramp(t, jt, jt + 0.15)) * sE, y - lerp(585, 640, _ramp(t, jt, jt + 0.15)) * sE)
    reach = {"r": hr}
    if t >= jt:
        w = _ramp(t, jt, jt + 0.12)
        reach["l"] = (lerp(x - 55 * sE, x - 95 * sE, _ramp(t, jt + 0.2, b1)),
                      lerp(y - 660 * sE, y - 520 * sE, _ramp(t, jt + 0.2, b1)), w)
    # the beam: down at the floor ahead as he walks, then it swings and lands on the creature
    tx, ty = c["x"] - 30 * c["s"], c["y"] - 125 * c["s"]
    lx0, ly0 = hr
    a_t = math.atan2(ty - ly0, tx - lx0)
    a_w = 1.74 + 0.05 * math.sin(pt * 2 * math.pi)
    if t < sw:
        aim = a_w
    else:
        aim = lerp(a_w, a_t, core.ease_out_back(seg(t, sw, bm), 1.4))
    if t >= jt:                                            # his hands shake
        tr = 1.0 - 0.45 * _ramp(t, T["l07e"], T["l07e"] + 1.0)
        aim += tr * (0.07 * math.sin(t * 31.0) + 0.045 * math.sin(t * 47.0 + 1.3) * _bump(t, jt, jt + 0.6, 1.5)
                     + 0.03 * math.sin(t * 13.0 + 0.4))
    reach_len = math.hypot(tx - lx0, ty - ly0)
    L = lerp(64.0, max(90.0, reach_len * 1.5), smoothstep(seg(t, sw, bm)))
    spread = lerp(0.75, 0.72, smoothstep(seg(t, sw, bm)))
    pw = _ramp(t, on, on + 0.3)
    return dict(x=x, y=y - bob * sE, s=sE, pose=pose, pose_t=pt, turn=turn, expr=expr, look=look, face=face,
                blink=blink, reach=reach, aim=aim, L=L, spread=spread, power=pw,
                glasses_tilt=0.07 * _ramp(t, jt, jt + 0.15), drift=t < bm, flicker=0.3 * _ramp(t, jt, jt + 0.2))


def _draw_emb(ctx, t, E, info):
    """Emb (darkened, lit by his own torch spill) -> (anchors, lens, angle)."""
    sE = E["s"]
    ks = sE / S
    out = {}

    def hold(c, side, hx, hy, ang):
        if side != "r":
            return
        r = props.flashlight(c, hx, hy, EMB_FLASH_S * ks, rot=E["aim"], on=1.0)
        out["lens"] = r["lens"]

    ctx.push_group()
    a = human.draw_person(ctx, "embar", E["x"], E["y"], sE, t, pose=E["pose"], pose_t=E["pose_t"],
                          turn=E["turn"], expr=E["expr"], look=E["look"], face=E["face"], blink=E["blink"],
                          mouth=info.mouth("embar", t), blush=0.1, hold=hold, hold_sides="r",
                          hold_layer="front", reach=E["reach"], pocket_side="near", drift=E["drift"],
                          glasses_tilt=E["glasses_tilt"], shadow=False)
    lx, ly = out.get("lens", a["hand_r"][:2])
    # the dark of the tunnel on him, lifted near his torch (its spill lights his front)
    g = cairo.RadialGradient(lx, ly, 0, lx, ly, 950 * sE)
    g.add_color_stop_rgba(0.0, 0.01, 0.015, 0.03, 0.18)
    g.add_color_stop_rgba(0.5, 0.01, 0.015, 0.03, 0.46)
    g.add_color_stop_rgba(1.0, 0.01, 0.015, 0.03, 0.7)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source(g)
    ctx.paint()
    g2 = cairo.RadialGradient(lx, ly, 0, lx, ly, 520 * sE)
    g2.add_color_stop_rgba(0.0, 1.0, 0.8, 0.55, 0.2 * E["power"])
    g2.add_color_stop_rgba(1.0, 1.0, 0.8, 0.55, 0.0)
    ctx.set_source(g2)
    ctx.paint()
    ctx.restore()
    pat = ctx.pop_group()
    return a, pat, (lx, ly)


def _beam_cone(ctx, lx, ly, ang, L, spread, power):
    """His torch beam in the dark side tunnel: a soft warm cone from the lens (smooth radial
    falloff, soft sides) and the pool of light where it hits the floor."""
    if power <= 0.01:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for sp, al in ((1.0, 0.035), (0.8, 0.045), (0.6, 0.055), (0.4, 0.06), (0.22, 0.06)):
        h = 0.5 * spread * sp
        ctx.move_to(lx - sa * 1.5, ly + ca * 1.5)
        ctx.arc(lx, ly, L, ang - h, ang + h)
        ctx.line_to(lx + sa * 1.5, ly - ca * 1.5)
        ctx.close_path()
        g = cairo.RadialGradient(lx, ly, 0, lx, ly, L)
        g.add_color_stop_rgba(0.0, 1.0, 0.9, 0.72, 2.2 * al * power)
        g.add_color_stop_rgba(0.35, 1.0, 0.86, 0.62, 1.1 * al * power)
        g.add_color_stop_rgba(0.8, 1.0, 0.83, 0.58, 0.6 * al * power)
        g.add_color_stop_rgba(1.0, 1.0, 0.83, 0.58, 0.0)
        ctx.set_source(g)
        ctx.fill()
    # the pool on the floor where it lands
    px, py = lx + ca * L * 0.84, ly + sa * L * 0.84
    ctx.save()
    ctx.translate(px, py)
    ctx.scale(1.0, 0.3)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 0.5 * L)
    g.add_color_stop_rgba(0.0, 1.0, 0.85, 0.6, 0.16 * power)
    g.add_color_stop_rgba(0.6, 1.0, 0.85, 0.6, 0.06 * power)
    g.add_color_stop_rgba(1.0, 1.0, 0.85, 0.6, 0.0)
    ctx.arc(0, 0, 0.5 * L, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()
    ctx.restore()


def _tunnel_end(ctx, t, T, info, c, E):
    """rev 4, walkoff .. end: (the side tunnel) Emb + his beam, then the creature in front."""
    ctx.save()
    _mouth_path(ctx)
    ctx.clip()
    if E is not None and E["power"] > 0.01:
        ea, pat, (lx, ly) = _draw_emb(ctx, t, E, info)
        pw = E["power"] * (1.0 - 0.25 * E["flicker"] * (0.5 + 0.5 * math.sin(t * 9.0) * math.sin(t * 3.7)))
        _beam_cone(ctx, lx, ly, E["aim"], E["L"], E["spread"], pw)
        ctx.set_source(pat)
        ctx.paint()
        ks = E["s"] / S
        px, py = ea["pocket"][:2]
        props.recorder(ctx, px + 6 * ks, py + 10 * ks, 0.9 * ks, t, led=None, glow=0.55, only_led=True)
        core.radial_glow(ctx, lx, ly, 46 * ks, "#fff0c8", 0.6 * E["power"])
    ctx.restore()
    return _draw_cur(ctx, t, c)


def _corridor_light(ctx, t, T):
    """S11: his torch light coming up the side tunnel reaches the corridor (he notices it)."""
    a = _ramp(t, T["light"], T["light"] + 0.3) * (1.0 - _ramp(t, T["bm_sw"] - 0.1, T["bm_sw"] + 0.2))
    if a <= 0.005:
        return
    a *= 0.85 + 0.15 * math.sin((t - T["e_on"]) * 2 * math.pi * 0.95)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    core.radial_glow(ctx, 700 + 30 * math.sin(t * 1.7), 1060, 460, "#ffcf8a", 0.24 * a)
    core.radial_glow(ctx, 760, 1180, 260, "#ffcf8a", 0.08 * a)
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
        if c["free"]:
            # (rev 4) walkoff .. end: it walks on down the side tunnel; Emb comes up it
            E = _emb(t, T, c) if shot not in (11, 14) else None
            ca = _tunnel_end(ctx, t, T, info, c, E)
            with sets.shaded(ctx, sets.service_tunnel, t_set, layer="shade"):
                a = _draw_tired(ctx, t, p)
            if shot == 11:
                _corridor_light(ctx, t, T)
            if bandage_amt > 0:
                _bandage_glow(ctx, a, bandage_amt)
        else:
            _render_rev3(ctx, t, T, c, p, t_set, bandage_amt)
    fx.vignette(ctx, 0.3, inner=0.62)


def _render_rev3(ctx, t, T, c, p, t_set, bandage_amt):
    """Everything up to the walkoff cut (as in rev 3)."""
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
    # (rev 4) hush: Emb's steps coming up the side tunnel (deep, to the left), he stops, the beam
    # swings onto it (its ears perk, a curious little chitter), his jolt: shoes scuff back, his
    # back bumps the wall; the yell: it flinches down low
    n = 0
    while T["e_on"] + (0.2 + 0.5 * n) / 0.95 < T["e_stop"] - 0.15:       # his walk's heel strikes
        ev.append((T["e_on"] + (0.2 + 0.5 * n) / 0.95, "footstep", -21.0 + 1.2 * n, -0.4))
        n += 1
    ev.append((T["e_stop"] - 0.02, "footstep", -17.0, -0.35))
    ev.append((T["bm_sw"] + 0.05, "cloth_rustle", -16.0, -0.3))
    ev.append((T["c_stop"] + 0.08, "ears_perk", -9.0, 0.1))
    ev.append((T["c_tilt"] + 0.05, "creature_chitter", -14.0, 0.1))
    ev.append((T["e_jolt"], "cloth_rustle", -10.0, -0.3))
    ev.append((T["e_jolt"] + 0.2, "footstep", -14.0, -0.35))
    ev.append((T["e_jolt"] + 0.42, "footstep", -15.0, -0.35))
    ev.append((T["e_back1"] - 0.03, "body_thud", -17.0, -0.35))
    ev.append((T["c_flat"] + 0.04, "scurry", -19.0, 0.05))
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
