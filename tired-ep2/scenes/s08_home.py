"""s08 — home (Episode 2 ending). Dawn, his bedroom.

Shot list (all times derive from cues / line timing; see _T and _render()):
  S1  dawn   wide on the quiet dawn room (a bird past the window), slow dolly toward
             the door: the latch, the door swings in on the three of them (filthy
             Tiredness, baby Joy dozing on his shoulder, Curiosity peeking from behind
             his legs). He looks over at the bed, sighs, trudges in; Curiosity at his heels.
  S2  flop   at the bed, head end of the frame: he turns to the pillow, a slow
             blink, a breath in (anticipation), falls like a plank, the mattress
             bounces (springs), his feet kick up and settle. The baby is flung off
             his shoulder, hangs a beat, tumbles onto his back and giggles on the bounce. Slow push-in
             on his face for "Worst. Day. Ever." (muffled into the pillow).
  S3  pile   Curiosity looks up, crouches, hops onto his back, settles into a curl;
             the baby clambers on top of Curiosity and curls up.
  S4  smile  close-up of the trio: his eyes slide toward the warm weight on his
             back, a tiny real smile, the eyes close.
  E1  phone  (same close-up) the phone on the nightstand buzzes; the camera eases
             over to it; eyes still shut, his bandaged arm gropes out for it.
  E2  insert the phone: "you ok?"; his thumb taps "zzz"; send.
  S6  sleep  slow pull-back: all three asleep, purring, sunrise growing, zzz.
      title  end card over the sleeping trio (captions hidden), held.
"""
import math

import cairocffi as cairo

from engine import core, sets, human, creatures, fx, props
from engine.core import clamp, lerp, seg, smoothstep, tween, ease_in, ease_out, ease_in_out, ease_out_back

M = sets.BEDROOM_MARKS
S_T = 0.75                    # Tiredness (the set's char_scale)
S_C = 0.6                     # Curiosity
S_B = 0.58                    # baby Joy
BED_Y = M["bed_top_y"]        # 1165
HIP_X = 1455                  # lying: hips here puts his head on the pillow
HIP_Y = 1117                  # pelvis height lying: chest, hips and thighs sunk ~20 px into the bed
LEG_REST = (-1.2, -1.32)      # knee bend: thighs on the mattress, knees at the footboard, shins hang off
LIE = {"base": "lie_front", "plant": 0, "hip_h": 0, "ll_p": 0.22, "lr_p": 0.14,
       "ll_k": LEG_REST[0], "lr_k": LEG_REST[1], "ll_a": -0.6, "lr_a": -0.6}
CHAIR_DX = 320                # the gaming chair pushed back to the desk, away from the foot of the bed
STAND = (1505, 1470)          # where he stands before the flop (feet)
DOOR_FEET = (305, 1336)       # in the doorway
CUR_FLOOR = (1672, 1542)      # Curiosity sits at his heels, at the foot of the bed
PERCH = (1395, 1102)          # Curiosity's perch base on his back
BABY_BACK = (1294, 1084)      # baby sitting on his upper back
G_CUR, G_BABY = 1.4, 1.7      # rim/eye glow: keeps the dark creatures readable on his navy hoodie
PHONE = M["phone"]            # (985, 1112)
PHONE_S = 0.42
PHONE_ROT = 0.04
Z_INS = 580.0 / (props.PHONE_W * PHONE_S)    # insert zoom: docked phone = 580 px wide
TKW = dict(outfit="sewer", bandage="l", power=0.5, headphones=None, hood=0.0)
CAD = 0.66                    # trudge: walk cycle played at 66 %
LEAN = {"base": "walk", "lean": 0.07, "hunch": 0.35, "nod": 0.1}
_ANTIC = {"base": "stand", "lean": -0.06, "hunch": 0.55, "nod": -0.08}   # the breath in, before the fall


def _lk(x, y, flip):
    """screen-space gaze -> the human rig's (character space under flip)."""
    return (-x if flip else x, y)


class _T:
    """Every key time of the scene, derived from cues / line timing."""

    def __init__(self, info):
        c = info.cue
        ln = info.line("s08_l01")
        self.F = c("flop")
        self.L0, self.L1 = ln.start, ln.end
        self.P, self.S, self.PH = c("pile"), c("smile"), c("phone")
        self.Z, self.TT, self.END = c("sleep"), c("title"), info.dur
        self.words = [info.word_time("s08_l01", k) for k in range(3)]
        # S1 door / walk
        self.D0 = 0.42                      # latch
        self.D1 = self.D0 + 0.65            # door open enough to see him (swings flat by D1 + 0.3)
        self.W0 = max(self.D1 + 0.55, self.F - 1.25)   # first step
        # S2 flop
        self.A0 = self.F + 0.55             # breath in (anticipation)
        self.A1 = self.F + 0.95             # tips over
        self.I = self.A1 + 0.30             # body hits the mattress
        self.OPEN = self.I + 1.0            # his eyes drag back open
        # S3 pile
        self.C0 = self.P + 0.55             # Curiosity crouches
        self.C1 = self.C0 + 0.3             # take-off
        self.C2 = self.C1 + 0.45            # lands on his back
        self.C3 = self.C2 + 0.15            # settles (stand -> perch)
        self.B0 = self.C3 + 0.55            # baby hops onto Curiosity
        self.B1 = self.B0 + 0.38            # baby lands
        # E: phone
        self.MSG = self.PH + 0.15           # "you ok?" arrives (buzz)
        self.GROPE = self.PH + 0.6          # his hand sets off
        self.TOUCH = self.PH + 1.2          # hand lands on the phone
        self.INS = self.PH + 1.35           # cut to the insert
        self.TYPE = self.PH + 1.5           # first key
        self.SEND = self.TYPE + 0.48 + 0.5  # 3 keys 0.24 apart, then send
        self.DROP = self.SEND + 0.35        # the hand slides off, dangles


# ----------------------------------------------------------------------------
# anchors of a pose drawn at the origin (for exact hip placement in the fall)
# ----------------------------------------------------------------------------
_DUMMY = []
_OFFS = {}


def _offs(pose, key, turn, flip=True):
    k = (key, round(turn, 3), flip)
    if k not in _OFFS:
        if not _DUMMY:
            _DUMMY.append(cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)))
        a = human.draw_person(_DUMMY[0], "tired", 0.0, 0.0, S_T, 0.0, pose=pose, turn=turn, flip=flip,
                              shadow=False, drift=False, **TKW)
        _OFFS[k] = {n: a[n][:2] for n in ("hip", "shoulder_l", "neck", "head")}
    return _OFFS[k]


def _fall_pose(k):
    """stand -> flop -> lie_front as one 0..1 move (k quantised for caching)."""
    k = round(clamp(k) * 50) / 50
    if k < 0.5:
        return (_ANTIC, "flop", k * 2), k
    return ("flop", LIE, (k - 0.5) * 2), k


# ----------------------------------------------------------------------------
# the bed bounce (mattress squash + body lift), matched to the bed_flop springs
# ----------------------------------------------------------------------------
def _bounce(t, T):
    u = t - T.I
    if u < -0.02 or u > 1.0:
        return 0.0, 0.0
    sq = tween(u, [(-0.02, 0.0), (0.06, 1.0), (0.2, 0.0), (0.36, 0.55), (0.48, 0.0), (0.6, 0.25),
                   (0.72, 0.0), (0.82, 0.08), (0.95, 0.0)])
    lift = tween(u, [(0.06, 0.0), (0.2, 13.0), (0.36, 0.0), (0.48, 5.0), (0.6, 0.0), (0.72, 2.0),
                     (0.82, 0.0)])
    return sq, lift


def _bed_squash(t, T):
    sq, _ = _bounce(t, T)
    # Curiosity landing on his back gives the mattress a little dip too
    sq += 0.18 * math.sin(math.pi * seg(t, T.C2 - 0.02, T.C2 + 0.3))
    return round(clamp(sq) * 20) / 20


def _walk_dist(t, t0, v):
    """distance of a walk that eases in over 0.3 s from t0 at speed v."""
    tau = t - t0
    if tau <= 0:
        return 0.0
    if tau < 0.3:
        s = tau / 0.3
        return v * 0.3 * (s ** 3 - s ** 4 / 2)
    return v * (tau - 0.15)


# ----------------------------------------------------------------------------
# Tiredness
# ----------------------------------------------------------------------------
def _tired(t, T, info):
    """-> (x, y, kwargs) in bedroom world coordinates."""
    kw = dict(TKW)
    face = {}
    if t < T.F:
        # ---- S1: doorway, sigh, trudge in (facing right)
        v = human.cycle_speed("tired", "walk", 0.85) * S_T
        d = _walk_dist(t, T.W0, v * CAD)
        x = DOOR_FEET[0] + d
        y = DOOR_FEET[1] + 0.32 * d
        sig = smoothstep(seg(t, T.D1 + 0.35, T.D1 + 0.8))            # the sigh: shoulders drop
        hunch = 0.15 + 0.25 * math.sin(math.pi * seg(t, T.D1 + 0.05, T.D1 + 0.45)) - 0.1 * sig
        stand = {"base": "stand", "hunch": hunch, "nod": 0.06 + 0.1 * sig, "lean": 0.03 * sig}
        k = smoothstep(seg(t, T.W0, T.W0 + 0.3))
        pose = (stand, LEAN, k) if k > 0 else stand
        kw["pose_t"] = max(0.0, d / v)
        turn = tween(t, [(T.D1, 0.12), (T.D1 + 0.25, 0.4), (T.W0, 0.45), (T.W0 + 0.3, 0.85)])
        look = tween(t, [(T.D1 + 0.05, (0.0, 0.05)), (T.D1 + 0.2, (0.85, 0.12)), (T.W0 + 0.4, (0.85, 0.12)),
                         (T.W0 + 0.7, (0.25, 0.05))])
        face["lid"] = 0.08 * sig
        face["head_nod"] = 0.05 * sig
        blink = tween(t, [(T.D1 + 0.45, 0.0), (T.D1 + 0.6, 1.0), (T.D1 + 0.82, 1.0), (T.D1 + 1.05, 0.0)]) \
            if T.D1 + 0.45 < t < T.D1 + 1.05 else None
        kw.update(pose=pose, turn=turn, flip=False, expr="bored", look=_lk(*look, False), face=face,
                  blink=blink)
        return x, y, kw

    flip = True
    kw["flip"] = flip
    sq, lift = _bounce(t, T)
    if t < T.A1:
        # ---- S2: at the bed, turning to the pillow, slow blink, breath in
        turn = tween(t, [(T.F, 0.15), (T.F + 0.45, 0.8)])
        b = smoothstep(seg(t, T.A0, T.A1))
        pose = {"base": "stand", "lean": -0.06 * b, "hunch": 0.2 + 0.35 * b, "nod": 0.08 - 0.16 * b}
        if b >= 1:
            pose = _ANTIC
        look = tween(t, [(T.F, (-0.2, 0.1)), (T.F + 0.12, (-0.95, 0.35))])
        blink = tween(t, [(T.F + 0.5, 0.0), (T.F + 0.85, 1.0)], ease_in_out) if t > T.F + 0.5 else None
        face["lid"] = 0.06
        face["curve"] = 0.12 * smoothstep(seg(t, T.F + 0.6, T.A1))     # "finally"
        kw.update(pose=pose, turn=turn, expr="bored", look=_lk(*look, flip), blink=blink, face=face)
        return STAND[0], STAND[1], kw
    if t < T.I:
        # ---- the fall: hips travel a little dive arc onto the bed
        kf = ease_in(seg(t, T.A1, T.I))
        pose, kq = _fall_pose(kf)
        turn = 0.8 * (1 - min(1.0, 2 * kq))
        o = _offs(pose, ("fall", kq), turn)
        o0 = _offs(_ANTIC, "antic", 0.8)
        h0 = (STAND[0] + o0["hip"][0], STAND[1] + o0["hip"][1])
        h1 = (HIP_X, HIP_Y)
        hx = lerp(h0[0], h1[0], kq)
        hy = lerp(h0[1], h1[1], kq) - 34 * math.sin(math.pi * kq)
        face.update(squash=-0.08 * kq, lid=0.1)
        kw.update(pose=pose, turn=turn, expr="bored", blink=1.0, face=face)
        return hx - o["hip"][0], hy - o["hip"][1], kw

    # ---- lying on the bed from here on
    y = HIP_Y + 19 * sq - lift
    # follow-through: the dangling shins swing up off the end of the bed and settle
    u = max(0.0, t - T.I)
    sw = 0.75 * math.exp(-u / 0.32) * math.sin(u * 2 * math.pi * 1.5) if u < 2.0 else 0.0
    pose = dict(LIE, ll_k=LEG_REST[0] + sw, lr_k=LEG_REST[1] + 0.85 * sw, ll_a=-0.6 + 0.3 * sw,
                lr_a=-0.6 + 0.3 * sw)
    if t < T.OPEN:
        mash = tween(t - T.I, [(0.0, 0.0), (0.06, 1.0), (0.3, 0.55), (0.9, 0.35)])
        face.update(squash=0.16 * mash, cheek=0.5 * mash, press=0.35 * mash, jaw=-0.15 * mash)
        blink = 1.0
        look = (0.0, 0.0)
    else:
        blink = tween(t, [(T.OPEN, 1.0), (T.OPEN + 0.35, 0.0)]) if t < T.OPEN + 0.35 else None
        face.update(cheek=0.25, jaw=-0.08, squash=0.05)
        look = (-0.15, 0.1)
    # ---- the line: muffled into the pillow, dull lids sinking word by word
    w0, w1, w2 = T.words
    if T.OPEN <= t < T.P:
        face["lid"] = 0.05 + 0.05 * smoothstep(seg(t, w1, w1 + 0.2)) + 0.05 * smoothstep(seg(t, w2, w2 + 0.2))
        face["brow"] = -0.06 * smoothstep(seg(t, w0, w0 + 0.2)) - 0.08 * smoothstep(seg(t, w2, w2 + 0.25))
        face["brow_ang"] = 0.15 * smoothstep(seg(t, w1, w1 + 0.3))
        face["press"] = 0.3 * smoothstep(seg(t, T.L1 + 0.05, T.L1 + 0.3))
        face["frown"] = 0.15 * smoothstep(seg(t, T.L1 + 0.05, T.L1 + 0.3))
        if w2 + 0.15 < t < w2 + 1.05:     # slow blink on "Ever."
            blink = tween(t, [(w2 + 0.15, 0.0), (w2 + 0.45, 1.0), (w2 + 0.7, 1.0), (w2 + 1.05, 0.0)])
        look = tween(t, [(T.OPEN, (-0.15, 0.1)), (T.L0, (-0.3, 0.12))])
    kw["mouth"] = info.mouth("tired", t)
    if T.P <= t < T.S:
        # Curiosity lands on his back: "oof", then the eyes slide toward the weight
        oof = math.sin(math.pi * seg(t, T.C2 - 0.02, T.C2 + 0.35))
        face.update(lid=0.08 + 0.3 * oof, cheek=0.25 + 0.3 * oof, press=0.25 * (1 - oof))
        look = tween(t, [(T.C2 + 0.35, (-0.3, 0.1)), (T.C2 + 0.6, (0.75, -0.35)), (T.B1 + 0.2, (0.75, -0.35)),
                         (T.B1 + 0.5, (0.1, 0.0))])
    if T.S <= t < T.PH:
        # S4: the tiny real smile, eyes close
        k1 = smoothstep(seg(t, T.S + 0.9, T.S + 1.4))
        face.update(cheek=0.25, jaw=-0.06, curve=0.8 * k1, width=0.12 * k1, lower=0.4 * k1,
                    lid=0.02 - 0.05 * smoothstep(seg(t, T.S + 0.45, T.S + 0.7)))
        look = tween(t, [(T.S + 0.35, (0.0, 0.0)), (T.S + 0.5, (0.7, -0.3)), (T.S + 1.1, (0.7, -0.3)),
                         (T.S + 1.3, (0.15, 0.05))])
        if t > T.S + 1.45:
            blink = tween(t, [(T.S + 1.45, 0.0), (T.S + 2.0, 1.0)], ease_in_out)
    if t >= T.PH:
        # eyes stay shut from here; buzz -> a pinch of the brows, then the smile returns
        blink = 1.0
        pin = math.sin(math.pi * seg(t, T.MSG, T.MSG + 0.9))
        face.update(cheek=0.25, jaw=-0.06, curve=0.8 - 0.65 * pin, width=0.12, lower=0.4 - 0.2 * pin,
                    brow=-0.15 * pin, brow_in=0.5 * pin, press=0.4 * pin)
        if t >= T.Z:
            face.update(curve=0.55, lower=0.3, open=0.06 * smoothstep(seg(t, T.Z + 0.6, T.Z + 1.4)),
                        press=0.0, brow=0.0, brow_in=0.0)
        # reach for the phone, tap, slide off, dangle
        tgt = (1006, 1104)
        if t < T.DROP:
            # a lazy grope: the arm lifts off the pillow, drifts out and pats down on the phone
            kg = seg(t, T.GROPE, T.TOUCH)
            w = ease_in_out(kg)
            lift = -70 * math.sin(math.pi * kg) ** 1.5     # dips under his chin (keeps the shut eyes in view)
            pat = 6 * math.sin(math.pi * seg(t, T.TOUCH - 0.02, T.TOUCH + 0.14))
            tap = 0.0
            for kt in (T.TYPE, T.TYPE + 0.24, T.TYPE + 0.48, T.SEND - 0.05):
                tap = max(tap, math.sin(math.pi * seg(t, kt - 0.06, kt + 0.06)))
            kw["reach"] = {"l": (tgt[0], tgt[1] - lift + pat + 5 * tap, w)}
        else:
            kd = ease_in_out(seg(t, T.DROP, T.DROP + 0.55))
            kw["reach"] = {"l": (lerp(tgt[0], 1036, kd), lerp(tgt[1], 1212, kd), 1.0)}
    face["head_tilt"] = face.get("head_tilt", 0.0) - 0.22 * smoothstep(seg(t, T.I + 0.1, T.I + 0.6))
    kw.update(pose=pose, turn=0.0, expr="bored", look=_lk(*look, flip), blink=blink, face=face)
    return HIP_X, y, kw


def _draw_tired(ctx, t, T, info):
    x, y, kw = _tired(t, T, info)
    if t >= T.I and t < T.I + 0.12:
        # squash on impact (about the mattress contact line)
        k = math.sin(math.pi * seg(t, T.I, T.I + 0.12))
        with core.saved(ctx, x, BED_Y, (1 + 0.04 * k, 1 - 0.07 * k)):
            return human.draw_person(ctx, "tired", 0, (y - BED_Y) / (1 - 0.07 * k), S_T, t, **kw)
    return human.draw_person(ctx, "tired", x, y, S_T, t, **kw)


# ----------------------------------------------------------------------------
# Curiosity
# ----------------------------------------------------------------------------
def _cur(t, T):
    """-> (x, y, kwargs) in bedroom world coordinates."""
    if t < T.F:
        # S1: peeking from behind his legs, then trotting at his heels
        tw = T.W0 + 0.25
        v = human.cycle_speed("tired", "walk", 0.85) * S_T * CAD
        d = _walk_dist(t, tw, v)
        x, y = 222 + d, 1322 + 0.32 * d
        mix = smoothstep(seg(t, tw, tw + 0.3))
        kw = dict(pose="walk", pose_from="sit", pose_mix=mix, pose_t=d / (creatures.SPEC_WALK_SPEED * S_C),
                  flip=False, expr="curious" if t < T.D1 + 0.5 else "calm",
                  face=tween(t, [(tw, 0.25), (tw + 0.4, 0.85)]),
                  look=tween(t, [(T.D1, (0.5, -0.1)), (T.D1 + 0.5, (0.3, -0.7)), (tw, (0.6, -0.2))]),
                  ears=tween(t, [(T.D1, 0.6), (T.D1 + 0.5, 0.75)]))
        if mix <= 0:
            kw.update(pose="sit", pose_from=None, pose_mix=1.0)
        return x, y, kw
    x, y = CUR_FLOOR
    kw = dict(flip=True, pose="sit", expr="calm")
    if t < T.P:
        # S2: at his heels, looking up at him; the impact flicks its ears; its eyes
        # follow the flying baby, then rest on his face
        kw["face"] = 0.55
        kw["look"] = tween(t, [(T.F, (-0.3, -0.92)), (T.A1, (-0.3, -0.92)), (T.I + 0.05, (-0.45, -0.85)),
                               (T.I + 0.45, (-0.75, -0.65)), (T.I + 0.9, (-0.85, -0.5))])
        kw["ears"] = tween(t, [(T.I - 0.02, 0.55), (T.I + 0.1, 0.95), (T.I + 0.7, 0.62)])
        kw["tilt"] = 0.12 * smoothstep(seg(t, T.L0 + 0.3, T.L0 + 0.8))
        return x, y, kw
    if t < T.C1:
        # S3: decides (ears up), crouches
        kw["look"] = tween(t, [(T.P, (-0.85, -0.5)), (T.P + 0.3, (-0.5, -0.85))])
        kw["ears"] = tween(t, [(T.P + 0.15, 0.6), (T.P + 0.35, 0.9)], ease_out_back)
        kw["tail_curl"] = 0.5 * smoothstep(seg(t, T.P + 0.2, T.P + 0.6))
        kw["face"] = tween(t, [(T.P, 0.35), (T.P + 0.4, 0.6)])
        m = smoothstep(seg(t, T.C0, T.C1))
        if m > 0:
            kw.update(pose="crouch", pose_from="sit", pose_mix=m)
        return x, y, kw
    if t < T.C2:
        # the hop: a parabola from the floor to his back, stretched in the air
        k = seg(t, T.C1, T.C2)
        x = lerp(CUR_FLOOR[0], PERCH[0], k)
        y = lerp(CUR_FLOOR[1], PERCH[1], k) - 150 * math.sin(math.pi * k)
        kw.update(pose="stand", pose_from="crouch", pose_mix=smoothstep(seg(k, 0.0, 0.3)), ears=0.8,
                  look=(-0.6, 0.2), tail_curl=0.3, face=0.9)
        kw["_rot"] = lerp(0.35, -0.25, k)
        kw["_stretch"] = 1 + 0.12 * math.sin(math.pi * k)
        return x, y, kw
    x, y = PERCH
    if t < T.C3:
        kw.update(pose="crouch", pose_from="stand", pose_mix=smoothstep(seg(t, T.C2, T.C3)), ears=0.7,
                  look=(-0.5, 0.2), face=0.9)
        kw["_squash"] = math.sin(math.pi * seg(t, T.C2, T.C3))
        return x, y, kw
    m = smoothstep(seg(t, T.C3, T.C3 + 0.55))
    kw.update(pose="perch", pose_from="crouch" if m < 1 else None, pose_mix=m,
              expr="content" if t < T.S + 0.6 else "calm",
              tail_curl=0.45 * (1 - smoothstep(seg(t, T.S, T.S + 1.0))))
    return x, y, kw


def _draw_cur(ctx, t, T):
    x, y, kw = _cur(t, T)
    rot = kw.pop("_rot", 0.0)
    st = kw.pop("_stretch", 1.0)
    sq = kw.pop("_squash", 0.0)
    if rot or st != 1.0 or sq:
        with core.saved(ctx, x, y, (1.0 / st ** 0.5 * (1 + 0.1 * sq), st * (1 - 0.14 * sq)),
                        rot if not kw.get("flip") else -rot):
            return creatures.draw_specimen(ctx, 0, 0, S_C, t, glow=G_CUR, **kw)
    return creatures.draw_specimen(ctx, x, y, S_C, t, glow=G_CUR, **kw)


# ----------------------------------------------------------------------------
# baby Joy
# ----------------------------------------------------------------------------
def _baby_on_shoulder(ta, flip):
    sx, sy = ta["shoulder_l"][:2]
    hx, hy = ta["head"][:2]
    out = 1 if sx > hx else -1                     # away from the head
    return sx + out * 18, sy - 58


def _draw_baby(ctx, t, T, ta):
    if t < T.F:
        bx, by = _baby_on_shoulder(ta, False)
        wake = t > T.D1 + 0.3
        return creatures.draw_specimen(ctx, bx, by, S_B, t, baby=True, glow=G_BABY, pose="held",
                                       expr="calm" if wake else "sleepy",
                                       look=(0.6, 0.1) if wake else None, face=0.6)
    if t < T.A1:
        bx, by = _baby_on_shoulder(ta, True)
        return creatures.draw_specimen(ctx, bx, by, S_B, t, baby=True, glow=G_BABY, pose="held", flip=True,
                                       expr="curious" if t > T.F + 0.4 else "calm", look=(-0.7, 0.3), face=0.7)
    # he drops away under it: the baby springs up off his shoulder, hangs a beat
    # (startled), then tumbles down onto his back; a spring hop; giggles
    land = T.I + 0.16
    hang = T.A1 + 0.2
    o = _offs(_ANTIC, "antic", 0.8)
    b0 = _baby_on_shoulder({"shoulder_l": (STAND[0] + o["shoulder_l"][0], STAND[1] + o["shoulder_l"][1]),
                            "head": (STAND[0] + o["head"][0], STAND[1] + o["head"][1])}, True)
    b1 = (b0[0] + 26, b0[1] - 78)
    if t < hang:
        k = ease_out(seg(t, T.A1, hang))
        x, y = lerp(b0[0], b1[0], k), lerp(b0[1], b1[1], k)
        st = 1 + 0.12 * math.sin(math.pi * seg(t, T.A1, T.A1 + 0.12))
        with core.saved(ctx, x, y, (1 / st, st)):
            return creatures.draw_specimen(ctx, 0, 0, S_B, t, baby=True, glow=G_BABY, pose="held",
                                           flip=True, expr="startled", look=(-0.6, 0.6), face=0.7)
    if t < land:
        k = seg(t, hang, land)
        x = lerp(b1[0], BABY_BACK[0], ease_in_out(k))
        y = lerp(b1[1], BABY_BACK[1] - 30 * S_B, ease_in(k)) - 40 * math.sin(math.pi * k)
        r = -1.6 * math.pi * k
        return creatures.draw_specimen(ctx, x, y + 60 * S_B, S_B, t, baby=True, glow=G_BABY, pose="tumble",
                                       roll=r, flip=True)
    x, y = BABY_BACK
    hop = 34 * math.sin(math.pi * seg(t, T.I + 0.3, T.I + 0.6))
    sq = math.sin(math.pi * seg(t, land, land + 0.14)) + 0.6 * math.sin(math.pi * seg(t, T.I + 0.6, T.I + 0.72))
    if t < T.B0:
        if t < T.I + 0.3:
            expr = "startled"
        elif t < T.I + 1.25:
            expr = "giggle"            # the spring bounce is the best thing ever
        elif t < T.P:
            expr = "curious"
        elif t < T.C1:
            expr = "calm"
        else:
            expr = "curious"
        # sits facing right with its head turned back to his face; when Curiosity jumps
        # up beside it the head swings round to look at Curiosity
        look = tween(t, [(T.C1, (-0.8, 0.25)), (T.C1 + 0.25, (0.7, 0.05))])
        fc = tween(t, [(T.C1, -0.7), (T.C1 + 0.3, 0.8)])
        with core.saved(ctx, x, y - hop, (1 + 0.12 * sq, 1 - 0.16 * sq)):
            return creatures.draw_specimen(ctx, 0, 0, S_B, t, baby=True, glow=G_BABY, pose="sit", flip=False,
                                           expr=expr, look=look, face=fc)
    return None


def _draw_baby_top(ctx, t, T, ca):
    """the baby's climb from his back onto Curiosity, then curled up on top."""
    tx, ty = ca["top"][:2]
    if t < T.B1:
        k = seg(t, T.B0, T.B1)
        x = lerp(BABY_BACK[0], tx, k)
        y = lerp(BABY_BACK[1], ty, k) - 70 * math.sin(math.pi * k)
        st = 1 + 0.1 * math.sin(math.pi * k)
        with core.saved(ctx, x, y, (1 / st, st)):
            return creatures.draw_specimen(ctx, 0, 0, S_B, t, baby=True, glow=G_BABY, pose="sit", flip=False,
                                           expr="calm", look=(0.5, 0.3), face=0.8)
    sk = seg(t, T.B1, T.B1 + 0.22)
    if sk < 1:
        sq = math.sin(math.pi * sk)
        with core.saved(ctx, tx, ty, (1 + 0.15 * sq, 1 - 0.25 * sq)):
            if sk < 0.5:
                return creatures.draw_specimen(ctx, 0, 0, S_B, t, baby=True, glow=G_BABY, pose="sit", flip=False,
                                               expr="sleepy", face=0.8)
            return creatures.draw_specimen(ctx, 0, 0, S_B, t, baby=True, glow=G_BABY, pose="curl", flip=False)
    return creatures.draw_specimen(ctx, tx, ty, S_B, t, baby=True, glow=G_BABY, pose="curl", flip=False)


# ----------------------------------------------------------------------------
# set helpers
# ----------------------------------------------------------------------------
def _set_state(t, T):
    msgs = (("them", "you ok?", T.MSG), ("me", "zzz", T.SEND))
    on = T.MSG - 0.05 <= t < T.Z + 1.6
    buzz = 0.0
    if T.MSG <= t < T.MSG + 1.15:
        u = t - T.MSG
        buzz = 1.0 if (u < 0.48 or 0.62 <= u < 1.1) else 0.0
    sr = smoothstep(seg(t, T.Z, T.TT + 1.8))
    return dict(light="dawn", phone_fn=props.phone_chat_screen(msgs) if on else None, phone_on=on,
                phone_buzz=buzz, bed_squash=_bed_squash(t, T), sunrise=sr, chair_dx=CHAIR_DX,
                chair_empty=True)


def _shade(ctx, t, st):
    return sets.shaded(ctx, sets.bedroom, t, layer="shade", light="dawn", sunrise=st["sunrise"])


def _cam_lerp(a, b, k):
    return tuple(lerp(p, q, k) for p, q in zip(a, b))


# ----------------------------------------------------------------------------
# shots
# ----------------------------------------------------------------------------
def _shot_door(ctx, t, T, info):
    st = _set_state(t, T)
    # the latch gives, the door cracks open, then swings in and settles flat
    op = tween(t, [(T.D0 + 0.03, 0.0), (T.D0 + 0.2, 0.14), (T.D1, 0.62), (T.D1 + 0.3, 1.0)])
    cam = _cam_lerp((800, 1060, 0.82), (650, 1015, 1.0), ease_in_out(seg(t, 0.3, T.F + 0.3)))
    inside = t >= T.W0 + 0.12
    with core.camera(ctx, *cam):
        sets.bedroom(ctx, t, door_open=op, **st)
        _birds(ctx, t, BIRDS_S1)
        if inside:
            sets.bedroom(ctx, t, layer="fg", door_open=op, parts=("door",), light="dawn")
        if op > 0.02:
            dx, dt_, dw, dh = M["door"]
            ctx.save()
            if not inside:
                ctx.rectangle(dx, dt_, dw, dh + 6)
                ctx.rectangle(-400, 1336, 3200, 1000)
                ctx.clip()
            _draw_cur(ctx, t, T)
            with _shade(ctx, t, st):
                ta = _draw_tired(ctx, t, T, info)
            _draw_baby(ctx, t, T, ta)
            ctx.restore()
        if not inside:
            sets.bedroom(ctx, t, layer="fg", door_open=op, parts=("door",), light="dawn")


def _blanket_lip(ctx, t, T, st):
    """The duvet hugging his underside: a strip of blanket drawn over his lower edge
    from the chest to the knees, with dent creases under the hips, so he lies IN the
    bed instead of on top of it. Graded with the set's own dawn light; it moves with
    the mattress squash and forms on impact."""
    if t < T.I - 0.01:
        return
    k = smoothstep(seg(t, T.I - 0.01, T.I + 0.08))
    sq = st["bed_squash"]
    dy = 19 * sq
    rise = 10 * k                                   # how far the duvet puffs up around him
    top = [(1262, 1196), (1300, 1190), (1350, 1188), (1405, 1190), (1455, 1194), (1505, 1189),
           (1548, 1180), (1578, 1172), (1596, 1175)]
    top = [(x, y + dy - rise * (0.7 + 0.3 * math.sin(x * 0.045))) for x, y in top]
    bot = 1212 + dy
    C = sets.C
    INK_ = core.PAL["ink"]

    def draw(c):
        core.smooth_path(c, [(1250, bot)] + top + [(1600, top[-1][1] + 18), (1598, bot)])
        c.close_path()
        core.fill(c, C["blanket"])
        core.smooth_path(c, [(1255, top[0][1] + 6)] + top[1:])
        core.stroke(c, INK_, 5)
        core.smooth_path(c, [(p[0], p[1] + 9) for p in top[1:-1]])
        core.stroke(c, core.alpha(C["blanket_hi"], 0.55 * k), 5)
        # dent creases fanning out from under the hips (and a small one under the chest)
        for (x0, x1, y1) in ((1438, 1398, 1207), (1474, 1516, 1206), (1318, 1290, 1208)):
            c.move_to(x0, 1196 + dy - rise * 0.4)
            c.curve_to(x0 + (x1 - x0) * 0.3, 1200 + dy, x1 - (x1 - x0) * 0.2, y1 + dy - 4, x1, y1 + dy)
            core.stroke(c, core.alpha(C["blanket_sh"], k), 5)

    kq = round(clamp(st["sunrise"]) * 10) / 10
    try:
        sets._bd_graded(ctx, True, kq, draw)        # the bed's own dawn grade (cool dim + sun beams)
    except AttributeError:                          # (fallback if the private helper ever moves)
        draw(ctx)


def _warm(t, T):
    """the sunbeam warming his back once they curl up (grows with the sunrise)."""
    return 0.3 * smoothstep(seg(t, T.C3, T.C3 + 1.2)) + 0.12 * smoothstep(seg(t, T.Z, T.TT + 1.5))


def _shot_bed(ctx, t, T, info, cam, birds=None):
    st = _set_state(t, T)
    with core.camera(ctx, *cam):
        sets.bedroom(ctx, t, **st)
        if birds:
            _birds(ctx, t, birds)
        with _shade(ctx, t, st):
            ta = _draw_tired(ctx, t, T, info)
        _blanket_lip(ctx, t, T, st)
        wa = _warm(t, T)
        if wa > 0.005:
            core.radial_glow(ctx, PERCH[0], PERCH[1] - 40, 200, "#ffcf9a", wa)
        ca = _draw_cur(ctx, t, T)
        if t < T.B0:
            _draw_baby(ctx, t, T, ta)
        else:
            _draw_baby_top(ctx, t, T, ca)
    return st


SKIN, SKIN_SH, INK = "#c08a62", "#a06e4c", "#1d1626"


def _thumb_hand(ctx, t, T):
    """His hand in the insert (screen space): a loose fist resting against the
    docked phone's right edge, the thumb tapping the reply, then sliding away."""
    keys = [T.TYPE, T.TYPE + 0.24, T.TYPE + 0.48, T.SEND]
    press = 0.0
    for kt in keys:
        press = max(press, math.sin(math.pi * seg(t, kt - 0.07, kt + 0.06)))
    settle = 1 - ease_out(seg(t, T.INS - 0.12, T.INS + 0.16))
    away = ease_in(seg(t, T.DROP, T.DROP + 0.4))
    ox, oy = 330 * away, 260 * away + 14 * settle
    tip = tween(t, [(T.TYPE + 0.56, (676, 1178)), (T.SEND - 0.2, (744, 1186))])
    base = (868 + ox, 1196 + oy)
    tip = (tip[0] + ox - 5 * press, tip[1] + oy + 7 * press)
    # forearm + bandage (the sleeve is pushed up), coming in from the bed (right)
    ax0, ay0 = 930 + ox, 1262 + oy
    ax1, ay1 = 1180 + ox, 1372 + oy
    ang = math.atan2(ay1 - ay0, ax1 - ax0)
    nx, ny = -math.sin(ang), math.cos(ang)
    wd = 62
    core.poly(ctx, [(ax0 + nx * wd, ay0 + ny * wd), (ax1 + nx * (wd + 8), ay1 + ny * (wd + 8)),
                    (ax1 - nx * (wd + 8), ay1 - ny * (wd + 8)), (ax0 - nx * wd, ay0 - ny * wd)])
    core.fill_stroke(ctx, SKIN, INK, 9)
    for j, f in enumerate((0.42, 0.55, 0.68)):
        bx_, by_ = lerp(ax0, ax1, f), lerp(ay0, ay1, f)
        core.poly(ctx, [(bx_ + nx * (wd + 3) - 22, by_ + ny * (wd + 3) - 8), (bx_ + nx * (wd + 3) + 22, by_ + ny * (wd + 3) + 8),
                        (bx_ - nx * (wd + 3) + 22, by_ - ny * (wd + 3) + 8), (bx_ - nx * (wd + 3) - 22, by_ - ny * (wd + 3) - 8)])
        core.fill_stroke(ctx, "#f4f1e8" if j != 1 else "#e6e1d6", INK, 6)
    # loose fist (knuckles to the left, against the phone)
    fx_, fy_ = 900 + ox, 1250 + oy
    core.ellipse(ctx, fx_, fy_, 108, 92, -0.25)
    core.fill_stroke(ctx, SKIN, INK, 9)
    for k in range(3):
        cx_ = fx_ - 70 + 6 * k
        cy_ = fy_ - 14 + 36 * k
        core.ellipse(ctx, cx_, cy_, 44, 22, -0.15)
        core.fill_stroke(ctx, SKIN, INK, 7)
    ctx.move_to(fx_ - 20, fy_ - 60)
    ctx.curve_to(fx_ + 20, fy_ - 40, fx_ + 50, fy_ - 10, fx_ + 60, fy_ + 30)
    core.stroke(ctx, SKIN_SH, 6)
    # the thumb: a tapered capsule from the top of the fist to the tip, nail up
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    L = math.hypot(dx, dy)
    a = math.atan2(dy, dx)
    with core.saved(ctx, base[0], base[1], 1.0, a):
        r0, r1 = 34, 27
        ctx.move_to(0, -r0)
        ctx.line_to(L - r1, -r1)
        ctx.arc(L - r1, 0, r1, -math.pi / 2, math.pi / 2)
        ctx.line_to(0, r0)
        ctx.arc(0, 0, r0, math.pi / 2, 3 * math.pi / 2)
        ctx.close_path()
        core.fill_stroke(ctx, SKIN, INK, 9)
        core.ellipse(ctx, L - r1 - 6, -6, 19, 14)
        core.fill_stroke(ctx, "#e7c3a6", SKIN_SH, 4)
        ctx.move_to(L * 0.38, -r0 + 10)
        ctx.curve_to(L * 0.42, -6, L * 0.42, 6, L * 0.38, r0 - 10)
        core.stroke(ctx, SKIN_SH, 5)
    # touch feedback on the glass
    if press > 0.2:
        core.circle(ctx, tip[0] - 14, tip[1] + 4, 22 + 26 * press)
        core.stroke(ctx, core.alpha("#4f8ef7", 0.5 * press), 4)


def _shot_insert(ctx, t, T, info):
    st = _set_state(t, T)
    st["phone_on"] = False
    st["phone_fn"] = None
    with core.camera(ctx, PHONE[0], PHONE[1], Z_INS, 0.0, 540, 730):
        sets.bedroom(ctx, t, **st)
        w, h = props.PHONE_W * PHONE_S, props.PHONE_H * PHONE_S
        ctx.save()
        ctx.translate(*PHONE)
        ctx.rotate(PHONE_ROT)
        fx.phone_screen(ctx, -w / 2, -h / 2, w, h, t, [(T.MSG, "in", "you ok?")],
                        typing=(T.TYPE, "zzz", 0.24, T.SEND), clock="6:12")
        ctx.restore()
        with _shade(ctx, t, st):
            ctx.save()
            ctx.translate(*PHONE)
            ctx.scale(1 / Z_INS, 1 / Z_INS)
            ctx.translate(-540, -730)
            _thumb_hand(ctx, t, T)
            ctx.restore()


def _birds(ctx, t, flights):
    """little dark birds gliding past outside the window (world coords, clipped to the
    glass). flights = [(t0, dur, x0, y0, x1, y1, size), ...]"""
    wx, wy, ww, wh = M["window"]
    live = [f for f in flights if f[0] <= t <= f[0] + f[1]]
    if not live:
        return
    ctx.save()
    ctx.rectangle(wx + 14, wy + 14, ww - 28, 300)
    ctx.clip()
    for (t0, dur, x0, y0, x1, y1, sz) in live:
        k = (t - t0) / dur
        x, y = lerp(x0, x1, k), lerp(y0, y1, k) + 6 * math.sin(k * 7.0)
        flap = math.sin((t - t0) * 2 * math.pi * 3.2)
        dyw = sz * (0.25 + 0.45 * flap)
        ctx.move_to(x - sz, y - dyw)
        ctx.curve_to(x - sz * 0.5, y - dyw * 0.6, x - sz * 0.15, y - sz * 0.05, x, y + sz * 0.12)
        ctx.curve_to(x + sz * 0.15, y - sz * 0.05, x + sz * 0.5, y - dyw * 0.6, x + sz, y - dyw)
        core.stroke(ctx, "#5a4a6a", max(2.0, sz * 0.22))
    ctx.restore()


BIRDS_S1 = [(0.05, 1.5, 1140, 600, 1480, 545, 13)]
BIRDS_S6 = [(0.4, 2.6, 1120, 640, 1490, 560, 12), (0.9, 2.9, 1105, 690, 1480, 615, 9)]


def render(ctx, t, info):
    T = _T(info)
    core.bg(ctx, "#2b1d4a")
    _render(ctx, t, T, info)
    # a breath of darkness between the control room and the dawn
    fade = 1 - smoothstep(seg(t, 0.0, 0.32))
    if fade > 0.004:
        ctx.set_source_rgba(0.04, 0.03, 0.07, fade)
        ctx.paint()


def _render(ctx, t, T, info):
    if t < T.F:
        _shot_door(ctx, t, T, info)
        return
    if t < T.P:
        # push in on his face as the bounce settles (Curiosity drops out of the bottom of
        # the frame before the caption comes up)
        k = ease_in_out(seg(t, T.I + 0.6, T.L0 + 0.35))
        k2 = ease_in_out(seg(t, T.L0 + 0.35, T.P))
        cam = _cam_lerp(_cam_lerp((1392, 1100, 1.25), (1222, 965, 1.72), k), (1210, 975, 1.8), k2)
        _shot_bed(ctx, t, T, info, cam)
        return
    if t < T.S:
        _shot_bed(ctx, t, T, info, (1392, 1185, 1.32))
        return
    if t < T.INS:
        kp = ease_in_out(seg(t, T.S, T.S + 2.2))          # slow push onto his face for the smile
        k = ease_in_out(seg(t, T.MSG + 0.1, T.MSG + 0.85))  # then ease over to the buzzing phone
        cam = _cam_lerp(_cam_lerp((1295, 1062, 1.98), (1268, 1068, 2.14), kp), (1112, 1085, 1.95), k)
        _shot_bed(ctx, t, T, info, cam)
        return
    if t < T.Z:
        _shot_insert(ctx, t, T, info)
        return
    k = ease_in_out(seg(t, T.Z, T.TT + 1.2))
    cam = _cam_lerp((1300, 1000, 1.2), (1262, 880, 0.98), k)
    st = _shot_bed(ctx, t, T, info, cam, [(T.Z + b[0],) + b[1:] for b in BIRDS_S6])
    # zzz over the sleepers (stops before the title's own z's)
    if t < T.TT + 0.4:
        with core.camera(ctx, *cam):
            a = 1 - smoothstep(seg(t, T.TT, T.TT + 0.4))
            if a > 0.01:
                core.fade_group(ctx, a, lambda c: fx.emote(c, "zzz", 1215, 960, 0.8, t, T.Z + 0.5))
    if t >= T.TT:
        fx.end_card(ctx, t, T.TT, subtitle="Episode 2: Lights Out")


def caption_y(t, info):
    if t >= info.cue("title"):
        return None
    return 1450


def SFX(info):
    from audio import sfx
    T = _T(info)
    ev = []
    ev += sfx.loop_events("birds_dawn", 0.0, info.dur, -9.0, 0.3)
    # S1: latch, the sigh, slow steps on the wooden floor
    ev.append((T.D0, "latch_click", 0.0, -0.5))
    ev.append((T.D1 + 0.3, "sigh", 0.0, -0.3))
    v = human.cycle_speed("tired", "walk", 0.85) * S_T
    # steps on the real foot contacts (cycle phase = distance / speed; contacts every half cycle)
    n = 1
    while True:
        lo, hi = T.W0, T.W0 + 4.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if _walk_dist(mid, T.W0, v * CAD) < 0.5 * n * v:
                lo = mid
            else:
                hi = mid
        if hi > T.F - 0.05:
            break
        ev.append((hi, "footstep", -6.0 + (1.0 if n % 2 else 0.0), -0.3))
        n += 1
    ev.append((T.W0 + 0.08, "footstep", -9.0, -0.35))     # the first heavy shuffle
    # S2: the flop
    ev.append((T.F + 0.03, "footstep", -8.0, 0.1))         # arrives at the bed
    ev.append((T.A0, "cloth_rustle", -4.0, 0.15))
    ev.append((T.A1 + 0.04, "critter_squeak", -7.0, 0.2))  # the baby, left hanging
    ev.append((T.I - 0.03, "bed_flop", 0.0, 0.1))
    ev.append((T.I + 0.28, "baby_giggle", -3.0, -0.1))
    ev.append((T.L1 + 0.1, "sigh", -2.0, -0.1))
    # S3: the pile
    ev.append((T.P + 0.2, "ears_perk", 0.0, 0.2))
    ev.append((T.C1 - 0.03, "scratch_wood", -6.0, 0.3))    # paws push off the floor
    ev.append((T.C2 - 0.02, "cloth_rustle", -2.0, 0.0))
    ev.append((T.C3 + 0.3, "creature_purr", 2.0, 0.1))
    ev.append((T.B1, "baby_coo", -4.0, -0.1))
    # E: phone
    ev.append((T.MSG, "phone_buzz", -3.0, -0.4))
    for k in range(3):
        ev.append((T.TYPE + 0.24 * k, "mouse_click", -3.0, -0.2))
    ev.append((T.SEND, "text_send", 0.0, -0.1))
    # S6: the purring trio
    for k, pan in enumerate((-0.3, 0.0, 0.3)):
        ev.append((T.Z + 0.3 + 0.5 * k, "creature_purr", 3.0, pan))
    ev.append((T.Z + 2.2, "creature_purr", 2.0, 0.1))
    ev.append((T.Z + 3.7, "creature_purr", -1.0, -0.1))
    return ev
