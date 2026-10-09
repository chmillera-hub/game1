"""S3 - "Snap back" (BIBLE section 4, S3).

The symphony's last mote goes out; silence; SNAP - the lights slam back on. Rae, on her knees and
still wet-eyed, blinks rapidly, gasps, wipes her eyes with her sleeve, looks around and points at
Quill: "WHAT the heck was THAT?!". Quill politely concludes she did not care for it. She scrambles up
("No, I-- that's not--"), drops back onto the bench and grabs her mug while he interrupts: he composed
eight. Eight holo-cards fan out from his palm (No. 1 softly lit, "the one you heard"); her face: dawning
dread.

render(canvas, t) is a pure function of absolute time t. The performances (rae_pose / quill_pose) run
continuously through every cut; each shot only picks a camera. Times derive from named beats / lines /
SFX in build/timeline.json. The last shot (Rae close-up) runs on into S4 until its first cut (card2),
so anim/scenes/s4.py reuses render() for that stretch, plus the shared helpers defined here (fan, arm
tracks, gaze, blinks, cameras).

Shot list (absolute times are only for orientation):
  0  s3 start -> snap          S2's last shot held for the silent beat (rendered by anim.scenes.s2)
  1  snap -> r10 "WHAT"        hard cut to a slightly tighter MEDIUM CLOSE of Rae on her knees (light 1, two
                               frames of overexposure, damped camera jolt; Quill's hanging hand kept out right):
                               rapid blinks, gasp, sleeve wipe, looks around, "Wait. What--", finger cocks
  2  -> q06                    TWO-SHOT (cut on the pointing thrust): "WHAT the heck was THAT?!" - she points up
                               at him, forearm clear of her face
  3  -> r11                    MEDIUM Quill (her finger still in frame): "Ah. You did not care for it."
  4  -> palm raise             MEDIUM-WIDE: she lifts her hand off her thigh, scrambles up (eased, leaning
                               toward him, hands waving), drops back onto the bench, grabs her mug;
                               "That is quite all right."
  5  -> "...the others"        (same shot) tilts up into the PRESENTATION 3-shot: "I composed eight." palm up,
                               the cards fan out, No. 1 glows
  6  -> card2 (in S4)          CLOSE-UP Rae: dawning dread, slow push-in
"""
from __future__ import annotations

import math
from functools import lru_cache

import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Layer, Track, auto_blink, beat, breathe, clamp, ease_in_out, ease_out, glow, lerp,
                       line_end, line_start, mouth, noise1, scene_span, smoothstep, timeline)
from anim.rig import ArmPose, Pose
from config import H, W

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s3")
S, E = line_start, line_end


def sfx_time(name, after):
    """First placement of SFX `name` at or after `after`."""
    for s in timeline()["sfx"]:
        if s["name"] == name and s["start"] >= after - 1e-6:
            return s["start"]
    raise KeyError(name)


SNAP = beat("snap")
GASP = sfx_time("gasp_breath", T0)          # breath peak ~ +0.1
CARDS = beat("cards_appear")
CARD2 = beat("card2")

R10, R10E = S("r10"), E("r10")
PT = R10 + 0.75                             # second "WHAT" - the finger lands
THAT = R10 + 1.3                            # "...was THAT?!"
Q06 = S("q06")
R11, R11E = S("r11"), E("r11")
Q07 = S("q07")
EIGHT = Q07 + 1.25                          # "I composed eight."
BEST = Q07 + 2.85                           # "I selected the best one..."
OTHERS = Q07 + 4.8                          # "...but perhaps you will prefer one of the others."

# ---------------------------------------------------------------- cuts
CUT_TWO = PT - 0.1                          # 2  cut on the pointing thrust
CUT_QMED = Q06 - 0.2                        # 3  medium Quill
CUT_WIDE = R11 - 0.2                        # 4  medium-wide scramble
CUT_FAN = CARDS - 0.75                      # 5  (same shot) the camera tilts up with the cards
CUT_DREAD = OTHERS - 0.3                    # 6  close-up Rae (runs into S4)
CUT_C2 = CARD2 - 0.05                       # first cut of S4

# ---------------------------------------------------------------- geometry
FLOOR = float(env.FLOOR_Y)
SEAT_Y = float(env.BENCH_SEAT_Y)
KNEEL_X, SEAT_X, QX = 255.0, 230.0, 545.0
MUG_SPOT = (330.0, SEAT_Y)                  # where S2 left the mug on the bench
LIGHT = env.char_light(1.0)
A, QA = R.ARMS, Q.ARMS
PRESENT_POSE = Pose(x=QX, y=FLOOR, facing=-1.0, turn=0.35, arm_r=QA["present"], arm_l=QA["rest"])
FAN = Q.hand_pos(PRESENT_POSE, "r")         # holo-card fan anchor (shared with S4 / S5)


def cam_on(head, zoom, sx, sy):
    """Camera at `zoom` that puts stage point `head` at screen fraction (sx, sy)."""
    return Camera(head[0] + (0.5 - sx) * W / zoom, head[1] + (0.5 - sy) * H / zoom, zoom)


def drift(a: Camera, b: Camera, t, t0, t1, ease=ease_in_out):
    return Camera.lerp(a, b, ease(clamp((t - t0) / max(1e-6, t1 - t0))))


def nudge(cam: Camera, dx=0.0, dy=0.0, dz=1.0):
    return Camera(cam.cx + dx, cam.cy + dy, cam.zoom * dz)


# =========================================================================== small animation helpers
class ArmSeq:
    """Keyframed ArmPose sequence [(t, ArmPose[, ease])]; the hand shape switches mid-blend."""

    def __init__(self, keys):
        self.keys = sorted([(k[0], k[1], k[2] if len(k) > 2 else "io") for k in keys], key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for i in range(1, len(ks)):
            if t < ks[i][0]:
                t0, a0, _ = ks[i - 1]
                t1, a1, e = ks[i]
                return ArmPose.blend(a0, a1, Track.EASES[e]((t - t0) / (t1 - t0)))
        return ks[-1][1]


def arm(a: ArmPose, **kw) -> ArmPose:
    d = dict(shoulder=a.shoulder, elbow=a.elbow, wrist=a.wrist, hand=a.hand, across=a.across, behind=a.behind)
    d.update(kw)
    return ArmPose(**d)


def arm_add(a: ArmPose, ds=0.0, de=0.0, dw=0.0) -> ArmPose:
    return arm(a, shoulder=a.shoulder + ds, elbow=a.elbow + de, wrist=a.wrist + dw)


def gaze(keys, dur=0.1):
    """Saccade track [(t, (lx, ly)[, dur])]: the eyes jump there over `dur` (fast out), then hold."""
    ks = [(keys[0][0] - 1.0, keys[0][1])]
    prev = keys[0][1]
    for k in keys:
        t, v = k[0], k[1]
        d = k[2] if len(k) > 2 else dur
        ks.append((t, prev, "lin"))
        ks.append((t + d, v, "out" if d <= 0.2 else "io"))
        prev = v
    return Track(ks)


def blink_amt(t, times, base=0.16):
    """0..1 lid closure from [(start, dur)] / [start]: fast close, slower open."""
    best = 0.0
    for b in times:
        b0, d = (b, base) if not isinstance(b, tuple) else b
        x = (t - b0) / d
        if 0.0 <= x < 1.0:
            v = math.sin(min(1.0, x / 0.38) * math.pi / 2) if x < 0.38 else math.cos((x - 0.38) / 0.62 * math.pi / 2)
            best = max(best, v)
    return best


def pulse(t, t0, rise, fall):
    """0 -> 1 -> 0 bump starting at t0 (fast rise, eased fall)."""
    if t < t0 or t > t0 + rise + fall:
        return 0.0
    if t < t0 + rise:
        return ease_out((t - t0) / rise)
    return 1.0 - ease_in_out((t - t0 - rise) / fall)


def jolt(t, t0, amp=1.0, dur=0.45, freq=7.5):
    """Damped shake (sx, sy, zoom factor) for a camera jolt at t0."""
    dt = t - t0
    if dt < 0 or dt > dur:
        return 0.0, 0.0, 1.0
    k = math.exp(-dt / (dur * 0.28))
    return (amp * 4.0 * k * math.sin(2 * math.pi * freq * dt + 0.6),
            amp * 9.0 * k * math.cos(2 * math.pi * freq * 1.13 * dt),
            1.0 + amp * 0.03 * k)


def smoothed(fn, t, n=6, step=0.07):
    """Average of fn(t - i*step) - a soft follow for cameras."""
    xs = ys = 0.0
    for i in range(n):
        x, y = fn(t - i * step)
        xs += x
        ys += y
    return xs / n, ys / n


# =========================================================================== holo-card fan (shared with S4)
FOCUS_POS = (366.0, 488.0)                  # where a selected card comes to rest (between them, upper third)
FOCUS_SCALE = 0.84
# fx.card_fan_layout geometry: the default arc raised 60 units and closed 2-4 degrees at the ends, so the
# lowest card clears the top of Rae's hair puff (seated) - and stays above Rae close-ups - while No. 8
# clears Quill's forehead.
FAN_GEOM = dict(radius=300.0, center=(-26.0, 0.0), angles=(-50.0, 8.0), card_scale=0.36)


def draw_fan(c, t, progress, alpha=1.0, focus=None, states=None, wobble=None, fold=None, pops=None,
             dim=0.4, hidden=(), focus_pos=FOCUS_POS, focus_scale=FOCUS_SCALE, alphas=None):
    """The eight holo-cards fanned from the palm anchor FAN (fx.card_fan_layout geometry, identical to
    fx.draw_card_fan defaults). focus: {number: 0..1} cards pulled to focus_pos and enlarged (several may
    be in flight while one returns and the next comes out); the others dim. states: {number: 0..1} glow.
    wobble / fold: {number: amount}. pops: {number: extra scale} (select overshoot). alphas: per-card alpha."""
    if alpha <= 0.003 or progress <= 0:
        return
    focus = {k: v for k, v in (focus or {}).items() if v > 0.0005}
    states = states or {}
    wobble = wobble or {}
    fold = fold or {}
    pops = pops or {}
    alphas = alphas or {}
    lay = fx.card_fan_layout(FAN[0], FAN[1], progress, **FAN_GEOM)
    fmax = max(focus.values()) if focus else 0.0
    order = sorted(lay, key=lambda L: focus.get(L[0], 0.0))
    for (num, x, y, rot, scl, vis) in order:
        if num in hidden:
            continue
        f = ease_in_out(clamp(focus.get(num, 0.0)))
        fo = ease_in_out(clamp(fmax)) * (1.0 - f)            # how much another card has the spotlight
        if f > 0:
            x = lerp(x, focus_pos[0], f)
            y = lerp(y, focus_pos[1], f) - 22.0 * math.sin(math.pi * f)   # a little lift on the way
            rot = lerp(rot, 0.0, f)
            scl = lerp(scl, focus_scale, f)
        scl *= 1.0 + pops.get(num, 0.0)
        a = alpha * vis * alphas.get(num, 1.0) * lerp(1.0, dim, fo)
        st = max(states.get(num, 0.0) * (1.0 - fo), f)
        fx.draw_holo_card(c, t, x, y, scl, num, fx.CARD_TITLES.get(num, ""), fx.CARD_ICONS.get(num, "symphony"),
                          st, a, wobble=wobble.get(num, 0.0), fold=fold.get(num, 0.0), rot=rot)


def card_xy(num, progress=1.0):
    for L in fx.card_fan_layout(FAN[0], FAN[1], progress, **FAN_GEOM):
        if L[0] == num:
            return L[1], L[2]
    return FAN


def select_flash(c, t, t0, x, y, scale=1.0):
    """holo_select: a quick bright bloom + expanding ring at a card that is being selected."""
    dt = t - t0
    if dt < 0 or dt > 0.6:
        return
    a = (1.0 - dt / 0.6) ** 2
    glow(c, x, y, 80 * scale, "#7FFFE9", 0.22 * a)
    glow(c, x, y, 28 * scale, "#E8FFFB", 0.4 * a * (1.0 - dt / 0.6))


def palm_burst(c, t, t0, x, y):
    """Light gathering in the palm as the cards spring out of it."""
    dt = t - t0
    if dt < -0.25 or dt > 1.1:
        return
    a = smoothstep((dt + 0.25) / 0.25) * (1.0 - smoothstep(dt / 1.1))
    glow(c, x, y - 6, 70, "#7FFFE9", 0.45 * a)
    glow(c, x, y - 6, 22, "#E8FFFB", 0.7 * a)


# =========================================================================== Rae: S3 performance
CHEST = arm(A["hand_on_chest"], wrist=10.0)                       # S2's last arm pose
THIGH_L_S2 = ArmPose(shoulder=12.0, elbow=26.0, wrist=4.0, hand="relaxed")
# far hand resting on her thigh while kneeling: this shoulder / elbow range keeps the rig's knee magnet fully
# engaged through the gasp (no jump between thigh and shin, no draw-order flip)
THIGH_L = ArmPose(shoulder=8.0, elbow=26.0, wrist=6.0, hand="relaxed")
LAP_L = ArmPose(shoulder=3.0, elbow=46.0, wrist=8.0, hand="relaxed")
LAP_R = ArmPose(shoulder=6.0, elbow=58.0, wrist=4.0, hand="relaxed", across=0.15)
HOLD = A["hold_mug"]
CLUTCH = arm(HOLD, shoulder=14.0, elbow=104.0, across=0.32)        # mug pulled in close (wary)
WIPE = A["wipe_eye"]
POINT_UP = ArmPose(shoulder=98.0, elbow=40.0, wrist=-6.0, hand="point")     # up at him, forearm clear of her face
POINT_COCK = ArmPose(shoulder=72.0, elbow=92.0, wrist=8.0, hand="point")    # finger cocked beside her cheek
HANDS_UP = A["hands_up"]
WAVE_R = arm(HANDS_UP, shoulder=36.0, elbow=96.0)
WAVE_L = arm(HANDS_UP, shoulder=40.0, elbow=80.0)

GRAB_T = Q07 + 0.95                         # fingers close on the mug (bench -> hand)
REACH_T = GRAB_T - 0.42


def _rae_tracks():
    SN, GS = SNAP, GASP
    d = {}
    # ---------------- body: kneeling -> scramble up -> drop onto the bench edge
    d["kneel"] = Track([(T0, 1.0), (R11 - 0.2, 1.0), (R11 + 0.34, 0.0, "io")])
    d["sit"] = Track([(T0, 1.0), (R11 - 0.2, 1.0), (R11 + 0.34, 0.1, "io"), (R11 + 0.8, 0.07),
                      (R11 + 1.22, 1.0, "in")])
    d["x"] = Track([(T0, KNEEL_X), (R11 - 0.2, KNEEL_X), (R11 + 0.34, KNEEL_X + 16.0, "io"), (R11 + 0.8, KNEEL_X + 12.0),
                    (R11 + 1.22, SEAT_X, "io")])
    d["turn"] = Track([(T0, 0.3), (SN + 1.3, 0.3), (SN + 1.5, 0.24), (SN + 1.75, 0.34), (R10, 0.3),
                       (R11 + 0.3, 0.3), (R11 + 0.6, 0.22), (R11 + 1.25, 0.35), (CUT_C2 + 1, 0.35)])
    d["lean"] = Track([(T0, 0.5), (SN, 0.5), (SN + 0.06, -5.0, "out"), (SN + 0.3, -2.0), (GS, -2.0),
                       (GS + 0.1, -6.5, "out"), (GS + 0.5, -2.0), (SN + 0.9, 3.0), (SN + 1.25, 7.0),
                       (SN + 1.45, 2.0), (SN + 1.8, 0.0), (PT - 0.25, 2.5), (PT, -3.5, "out"), (THAT, -3.0),
                       (THAT + 0.08, -1.0, "out"), (THAT + 0.3, -2.5), (Q06 + 0.4, -2.0), (Q06 + 1.0, 2.0),
                       (R11 - 0.3, 3.0), (R11 - 0.04, 12.0), (R11 + 0.36, 7.0), (R11 + 0.8, 2.0),
                       (R11 + 1.05, -3.0), (R11 + 1.3, 4.0), (R11 + 1.55, 1.0), (REACH_T, 1.5), (GRAB_T - 0.2, 5.0), (GRAB_T, 1.0),
                       (GRAB_T + 0.45, 2.0),
                       (EIGHT + 0.6, 3.0), (CARDS, 3.0), (CARDS + 0.15, -3.5, "out"), (CARDS + 0.9, -1.0),
                       (OTHERS, 0.0), (OTHERS + 1.5, 2.5), (CUT_C2 + 1, 2.5)])
    d["bounce"] = Track([(T0, 0.0), (SN, 0.0), (SN + 0.05, -4.0, "out"), (SN + 0.3, 0.5), (SN + 0.5, 0.0),
                         (GS, 0.0), (GS + 0.1, -3.0, "out"), (GS + 0.45, 0.0),
                         (R11 + 1.2, 0.0), (R11 + 1.28, 9.0, "out"), (R11 + 1.48, -2.0), (R11 + 1.72, 0.0),
                         (CARDS, 0.0), (CARDS + 0.1, -2.5, "out"), (CARDS + 0.5, 0.0)])
    d["shoulders"] = Track([(T0, 0.02), (SN, 0.02), (SN + 0.05, 0.35, "out"), (GS, 0.3), (GS + 0.1, 0.55, "out"),
                            (GS + 0.6, 0.18), (SN + 1.6, 0.08), (PT - 0.2, 0.1), (PT, 0.3, "out"), (THAT + 0.4, 0.22),
                            (Q06 + 0.8, 0.12), (R11, 0.3), (R11 + 0.8, 0.35), (R11 + 1.4, 0.08), (CARDS, 0.1),
                            (CARDS + 0.1, 0.35, "out"), (CARDS + 0.8, 0.18), (OTHERS + 0.8, 0.28),
                            (CUT_C2 + 1, 0.25)])
    # ---------------- head
    d["nod"] = Track([(T0, 0.4), (SN, 0.4), (SN + 0.06, 0.14, "out"), (SN + 0.35, 0.1), (GS, 0.1),
                      (GS + 0.1, 0.3, "out"), (GS + 0.45, 0.12), (SN + 0.85, 0.05), (SN + 1.15, -0.25),
                      (SN + 1.4, -0.2), (SN + 1.6, 0.05), (R10 + 0.2, 0.1), (PT, 0.02), (THAT, 0.0),
                      (THAT + 0.08, -0.14, "out"), (THAT + 0.3, 0.02), (Q06 + 0.8, 0.0), (R11, -0.05),
                      (R11 + 0.6, 0.0), (R11 + 1.4, 0.05), (REACH_T, -0.05), (GRAB_T, -0.3), (GRAB_T + 0.5, 0.0),
                      (EIGHT + 0.5, 0.06), (CARDS, 0.08), (CARDS + 0.4, 0.3), (BEST + 0.6, 0.3),
                      (OTHERS + 0.6, 0.15), (OTHERS + 1.8, 0.18), (OTHERS + 1.95, 0.02, "out"), (OTHERS + 2.3, 0.12),
                      (CUT_C2 + 1, 0.12)])
    d["tilt"] = Track([(T0, 3.5), (SN, 3.5), (SN + 0.1, 0.0, "out"), (SN + 1.35, 1.0), (SN + 1.5, -5.0),
                       (SN + 1.7, 4.0), (R10, 1.0), (R10 + 0.35, -6.0), (PT - 0.1, -4.0), (PT + 0.1, 2.0),
                       (THAT + 0.3, 3.0), (Q06 + 0.5, -2.0), (Q06 + 1.3, -5.0), (R11, -2.0), (R11 + 0.7, 2.0),
                       (R11 + 1.4, 0.0), (EIGHT + 0.3, 0.0), (EIGHT + 1.0, -5.0), (CARDS + 0.4, 3.0),
                       (BEST + 1.0, 4.0), (OTHERS + 0.5, -1.0), (CUT_C2 + 1, -2.0)])
    d["hturn"] = Track([(T0, 0.0), (SN + 1.3, 0.0), (SN + 1.45, -0.14), (SN + 1.62, 0.1), (SN + 1.82, 0.0),
                        (R11 + 0.3, 0.0), (R11 + 0.55, 0.06), (R11 + 0.8, -0.04), (R11 + 1.1, 0.0)])
    # ---------------- eyes
    d["lid"] = Track([(T0, 0.8), (SN, 0.8), (SN + 0.04, 1.0, "out"), (SN + 0.8, 1.0), (SN + 0.88, 0.12),
                      (SN + 1.28, 0.15), (SN + 1.38, 0.95), (R10, 0.9), (R10 + 0.15, 0.8), (R10 + 0.55, 0.85),
                      (PT - 0.05, 1.0), (Q06 + 0.5, 0.95), (Q06 + 1.3, 0.85), (R11, 1.0), (R11 + 1.4, 0.9),
                      (EIGHT, 0.9), (EIGHT + 0.6, 1.0), (CARDS + 1.0, 1.0), (BEST + 1.2, 0.92), (OTHERS, 0.95),
                      (OTHERS + 1.2, 1.0), (CUT_C2 + 1, 1.0)])
    d["wide"] = Track([(T0, 0.0), (SN, 0.0), (SN + 0.04, 0.55, "out"), (GS, 0.4), (GS + 0.08, 0.85, "out"),
                       (GS + 0.6, 0.3), (SN + 0.85, 0.0), (SN + 1.4, 0.0), (SN + 1.55, 0.25), (R10, 0.15),
                       (R10 + 0.2, 0.0), (PT - 0.08, 0.0), (PT, 1.0, "out"), (THAT + 0.6, 0.9), (Q06 + 0.6, 0.35),
                       (Q06 + 1.2, 0.15), (R11, 0.45, "out"), (R11 + 1.3, 0.2), (EIGHT + 0.5, 0.2),
                       (EIGHT + 1.0, 0.4), (CARDS, 0.35), (CARDS + 0.12, 0.65, "out"), (CARDS + 1.0, 0.35),
                       (BEST + 1.0, 0.15), (OTHERS + 0.4, 0.2), (OTHERS + 1.6, 0.62), (CUT_C2 + 1, 0.55)])
    d["blinks"] = [(SN + 0.06, 0.1), (SN + 0.17, 0.1), (SN + 0.27, 0.08), (SN + 0.62, 0.12),   # flutter, GASP, blink
                   (SN + 1.42, 0.15), (R10 + 0.42, 0.13), (Q06 + 0.05, 0.16), (Q06 + 1.15, 0.15),
                   (R11 + 0.05, 0.13), (R11 + 1.32, 0.17), (EIGHT + 0.95, 0.13), (EIGHT + 1.12, 0.12),
                   (BEST + 0.5, 0.16), (OTHERS + 0.95, 0.32), (OTHERS + 2.4, 0.16)]
    d["pupil"] = Track([(T0, 1.32), (SN, 1.32), (SN + 0.08, 0.86, "out"), (SN + 1.6, 0.95), (PT, 0.88),
                        (Q06 + 1.0, 1.0), (CARDS, 1.0), (CARDS + 0.5, 1.18), (OTHERS, 1.1), (OTHERS + 1.5, 0.92),
                        (CUT_C2 + 1, 0.92)])
    d["squint"] = Track([(T0, 0.1), (SN, 0.1), (SN + 0.05, 0.0), (SN + 0.88, 0.0), (SN + 1.0, 0.45),
                         (SN + 1.3, 0.4), (SN + 1.42, 0.05), (R10 + 0.1, 0.18), (PT - 0.1, 0.12), (PT, 0.0),
                         (Q06 + 1.2, 0.12), (R11, 0.0)])
    # gaze (screen space): +x toward Quill, -y up
    d["gaze"] = gaze([
        (T0, (0.21, -0.51)),
        (SN + 0.02, (0.1, -0.22)), (SN + 0.36, (0.0, -0.12)), (SN + 0.52, (0.16, -0.3)),       # darting, dazed
        (GS + 0.05, (0.08, -0.42)),
        (SN + 0.86, (0.15, 0.35), 0.2),                                                        # into the sleeve
        (SN + 1.42, (-0.68, -0.12)), (SN + 1.6, (0.12, -0.66)), (SN + 1.78, (0.45, -0.4)),     # looks around
        (R10 + 0.3, (0.58, -0.55)),                                                            # "What--" at him
        (Q06 + 1.0, (0.5, -0.45)), (Q06 + 1.25, (0.58, -0.55)),
        (R11 + 0.25, (0.55, -0.32)), (R11 + 1.3, (0.52, -0.28)),
        (REACH_T - 0.1, (0.42, 0.52)),                                                         # the mug
        (GRAB_T + 0.3, (0.6, -0.34)),                                                          # back to him
        (CARDS - 0.12, (0.42, -0.2)), (CARDS + 0.12, (0.4, -0.75), 0.18),                      # the burst
        (CARDS + 0.55, (0.12, -0.85), 0.35), (BEST + 0.35, (-0.3, -0.7), 0.25),                # ... No. 1
        (OTHERS + 0.25, (-0.12, -0.8), 0.22), (OTHERS + 0.75, (0.12, -0.82), 0.3),             # counting them
        (OTHERS + 1.25, (0.38, -0.8), 0.3), (OTHERS + 1.75, (0.6, -0.4), 0.2),                 # ... to him
    ])
    # ---------------- brows / mouth
    d["brow_raise"] = Track([(T0, 0.26), (SN, 0.26), (SN + 0.05, 0.85, "out"), (GS + 0.1, 0.95), (SN + 0.85, 0.35),
                             (SN + 1.4, 0.4), (SN + 1.6, 0.55), (R10, 0.4), (R10 + 0.3, 0.35), (R10 + 0.5, 0.55),
                             (PT - 0.05, 0.6), (PT, 1.0, "out"), (THAT + 0.5, 0.95), (Q06 + 0.5, 0.7),
                             (Q06 + 1.2, 0.5), (R11, 0.85, "out"), (R11 + 1.3, 0.45), (EIGHT, 0.4),
                             (EIGHT + 0.9, 0.7), (CARDS + 0.2, 0.85), (BEST + 0.8, 0.55), (OTHERS + 0.3, 0.5),
                             (OTHERS + 1.4, 0.62), (CUT_C2 + 1, 0.6)])
    d["worry"] = Track([(T0, 0.6), (SN, 0.6), (SN + 0.06, 0.25), (SN + 0.85, 0.5), (SN + 1.4, 0.2),
                        (R10 + 0.4, 0.1), (PT, 0.15), (Q06 + 0.5, 0.25), (Q06 + 1.2, 0.4), (R11, 0.6),
                        (R11 + 1.3, 0.45), (EIGHT, 0.35), (CARDS, 0.35), (BEST + 0.8, 0.45), (OTHERS + 0.3, 0.5),
                        (OTHERS + 1.6, 0.8), (CUT_C2 + 1, 0.8)])
    d["furrow"] = Track([(T0, 0.0), (SN + 1.4, 0.0), (R10, 0.15), (R10 + 0.3, 0.45), (R10 + 0.55, 0.5),
                         (PT, 0.15), (Q06 + 0.5, 0.25), (Q06 + 1.2, 0.45), (R11, 0.15), (R11 + 1.4, 0.05),
                         (EIGHT + 0.5, 0.25), (CARDS, 0.0), (OTHERS + 1.4, 0.12), (CUT_C2 + 1, 0.12)])
    d["open"] = Track([(T0, 0.1), (SN, 0.1), (SN + 0.06, 0.24, "out"), (GS, 0.18), (GS + 0.08, 0.78, "out"),
                       (GS + 0.4, 0.45), (SN + 0.85, 0.1), (SN + 1.3, 0.04), (R10, 0.0), (R10E, 0.0),
                       (R10E + 0.15, 0.22), (Q06 + 0.8, 0.14), (Q06 + 1.3, 0.05), (R11, 0.0), (R11E, 0.0),
                       (R11E + 0.2, 0.15), (Q07 + 1.0, 0.04), (CARDS, 0.04), (CARDS + 0.15, 0.32, "out"),
                       (CARDS + 1.0, 0.15), (BEST + 1.5, 0.1), (OTHERS + 1.2, 0.06), (OTHERS + 1.7, 0.16), (CUT_C2 + 1, 0.12)])
    d["round"] = Track([(T0, 0.0), (SN + 0.06, 0.2), (GS + 0.08, 0.6), (GS + 0.4, 0.4), (SN + 1.0, 0.0),
                        (R10E + 0.15, 0.35), (Q06 + 1.3, 0.1), (CARDS + 0.15, 0.55), (CARDS + 1.0, 0.3),
                        (OTHERS, 0.1)])
    d["smile"] = Track([(T0, 0.16), (SN, 0.16), (SN + 0.06, 0.0, "out"), (SN + 1.4, -0.08), (PT, 0.0),
                        (Q06 + 0.6, -0.1), (Q06 + 1.3, -0.2), (R11, -0.1), (R11 + 1.4, -0.12), (EIGHT, -0.05),
                        (CARDS, -0.05), (BEST + 0.8, -0.1), (OTHERS + 0.4, -0.15), (OTHERS + 1.8, -0.38),
                        (CUT_C2 + 1, -0.38)])
    d["tremble"] = Track([(T0, 0.25), (SN, 0.25), (SN + 0.1, 0.0), (OTHERS + 1.2, 0.0), (OTHERS + 2.2, 0.16),
                          (CUT_C2 + 1, 0.16)])
    # ---------------- tears: S2's two wet trails go with the sleeve
    WIPE_MID = SN + 1.08
    d["wipe_mid"] = WIPE_MID
    d["tears"] = Track([(T0, 0.74), (SN, 0.74), (SN + 0.5, 0.66), (WIPE_MID, 0.62), (WIPE_MID + 0.02, 0.32),
                        (Q06, 0.28), (R11 + 1.4, 0.24), (OTHERS + 1.0, 0.3), (CUT_C2 + 1, 0.34)])
    d["shine"] = Track([(T0, 0.75), (SN, 0.75), (SN + 0.1, 0.3), (SN + 1.4, 0.15), (CARDS, 0.15),
                        (CARDS + 0.4, 0.55), (OTHERS, 0.4), (CUT_C2 + 1, 0.3)])
    d["blush"] = Track([(T0, 0.2), (SN + 1.0, 0.16), (R11, 0.2), (R11 + 0.5, 0.32), (R11 + 2.0, 0.18),
                        (CUT_C2 + 1, 0.16)])
    d["sniffle"] = Track([(T0, 0.26), (SN + 1.0, 0.3), (CUT_C2 + 1, 0.32)])
    # ---------------- arms
    d["arm_r"] = ArmSeq([
        (T0, CHEST), (SN, CHEST), (SN + 0.08, arm(CHEST, wrist=16.0, elbow=122.0), "out"),
        (GS + 0.1, arm(CHEST, shoulder=16.0, wrist=18.0, elbow=124.0), "out"), (SN + 0.62, CHEST),
        (SN + 0.88, arm(WIPE, across=0.22, wrist=8.0), "io"),                         # sleeve to the eyes
        (SN + 1.22, arm(WIPE, across=0.55, wrist=30.0, elbow=126.0), "io"),             # drag across
        (SN + 1.64, ArmPose(shoulder=22.0, elbow=64.0, wrist=0.0, hand="open", across=0.1), "io"),
        (PT - 0.6, ArmPose(shoulder=26.0, elbow=58.0, wrist=0.0, hand="open", across=0.1)),
        (PT - 0.16, POINT_COCK, "io"), (PT, POINT_UP, "out"),                          # cock ... THRUST
        (THAT - 0.05, POINT_UP), (THAT + 0.07, arm_add(POINT_UP, 4.0, -2.0), "out"),    # jab on "THAT"
        (THAT + 0.3, POINT_UP, "io"), (R10E + 0.05, arm_add(POINT_UP, -3.0, 3.0)),
        (R10E + 0.6, ArmPose(shoulder=44.0, elbow=52.0, wrist=-6.0, hand="open"), "io"),   # the finger drops
        (R11 - 0.25, ArmPose(shoulder=30.0, elbow=60.0, wrist=-4.0, hand="open")),
        (R11 + 0.15, WAVE_R, "io"),
        (R11 + 0.35, arm_add(WAVE_R, 10.0, -16.0, -10.0)), (R11 + 0.55, arm_add(WAVE_R, -6.0, 8.0, 8.0)),
        (R11 + 0.75, arm_add(WAVE_R, 9.0, -14.0, -8.0)), (R11 + 0.95, arm_add(WAVE_R, -4.0, 6.0, 6.0)),
        (R11 + 1.3, LAP_R, "io"),
        (REACH_T, LAP_R),
    ])
    d["arm_l"] = ArmSeq([
        (T0, THIGH_L_S2), (SN, THIGH_L_S2), (SN + 0.12, THIGH_L, "out"),
        (GS + 0.12, arm(THIGH_L, shoulder=6.0, elbow=30.0, wrist=8.0), "io"),
        (SN + 0.9, arm(THIGH_L, shoulder=7.0, elbow=27.0, wrist=8.0)), (PT - 0.2, THIGH_L),
        (PT + 0.1, arm(THIGH_L, shoulder=6.0, elbow=22.0), "out"),
        (R11 - 0.5, arm(THIGH_L, shoulder=6.0, elbow=24.0, hand="open")),
        (R11 - 0.06, ArmPose(shoulder=8.0, elbow=86.0, wrist=6.0, hand="open"), "io"),  # elbow first: hand clears the leg
        (R11 + 0.36, WAVE_L, "io"), (R11 + 0.5, arm_add(WAVE_L, -8.0, 14.0, 8.0)),
        (R11 + 0.6, arm_add(WAVE_L, 8.0, -12.0, -8.0)), (R11 + 0.8, arm_add(WAVE_L, -6.0, 10.0, 6.0)),
        (R11 + 1.0, WAVE_L), (R11 + 1.3, arm(LAP_L, shoulder=8.0, elbow=80.0)), (R11 + 1.62, LAP_L, "io"),
    ])
    return d


_RT = _rae_tracks()


def _rae_body(t) -> Pose:
    """Rae without face / right arm (used by the mug pick-up solver)."""
    d = _RT
    return Pose(x=d["x"](t), y=FLOOR, facing=1.0, turn=d["turn"](t), sit=d["sit"](t), seat_y=SEAT_Y,
                kneel=d["kneel"](t), lean=d["lean"](t), bounce=d["bounce"](t), shoulders_up=d["shoulders"](t),
                breath=breathe(t, 0.22, 2), arm_l=d["arm_l"](t), **LIGHT)


_SOLVED = {}


def solve_mug_arm(t_grab: float, target=MUG_SPOT, body_fn=None, base=None):
    """Right-arm ArmPose (hand 'hold') whose held mug sits exactly on `target` at time t_grab (memoised)."""
    base = base or HOLD
    key = (round(t_grab, 4), tuple(target), body_fn, base.shoulder, base.elbow, base.wrist, base.across)
    if key not in _SOLVED:
        _SOLVED[key] = _solve_mug_arm(t_grab, target, body_fn or _rae_body, base)
    return _SOLVED[key]


def _solve_mug_arm(t_grab, target, body_fn, base):
    body = body_fn(t_grab)
    best = None
    for ac in (0.0, 0.12, 0.22):
        for sh in range(-20, 110, 4):
            for el in range(-10, 140, 4):
                a = arm(base, shoulder=float(sh), elbow=float(el), across=ac)
                mp = R.mug_pose(body.copy(arm_r=a, mug="r"))
                if mp is None:
                    continue
                err = math.hypot(mp[0] - target[0], mp[1] - target[1]) + 0.05 * abs(mp[3])
                if best is None or err < best[0]:
                    best = (err, float(sh), float(el), ac)
    err, sh, el, ac = best
    step = 2.0
    while step > 0.02:
        improved = False
        for dsh, de in ((step, 0), (-step, 0), (0, step), (0, -step)):
            a = arm(base, shoulder=sh + dsh, elbow=el + de, across=ac)
            mp = R.mug_pose(body.copy(arm_r=a, mug="r"))
            e2 = math.hypot(mp[0] - target[0], mp[1] - target[1]) + 0.05 * abs(mp[3])
            if e2 < err - 1e-6:
                err, sh, el, improved = e2, sh + dsh, el + de, True
                break
        if not improved:
            step *= 0.5
    return arm(base, shoulder=sh, elbow=el, across=ac)


def _rae_arm_r(t):
    if t < REACH_T:
        return _RT["arm_r"](t)
    grab = solve_mug_arm(GRAB_T)
    reach = arm(grab, hand="open", shoulder=grab.shoulder + 6.0, elbow=grab.elbow - 6.0)
    if t < GRAB_T - 0.1:
        return ArmPose.blend(LAP_R, reach, ease_in_out((t - REACH_T) / (GRAB_T - 0.1 - REACH_T)))
    if t < GRAB_T:
        return ArmPose.blend(reach, grab, ease_in_out((t - GRAB_T + 0.1) / 0.1))
    if t < GRAB_T + 0.12:
        return grab
    if t < GRAB_T + 0.6:
        return ArmPose.blend(grab, HOLD, ease_in_out((t - GRAB_T - 0.12) / 0.48))
    if t < OTHERS + 0.9:
        return HOLD
    return ArmPose.blend(HOLD, CLUTCH, ease_in_out((t - OTHERS - 0.9) / 0.9))


def rae_mug_on_bench(t):
    """S2 left the mug on the bench; she picks it up at GRAB_T."""
    return t < GRAB_T


def rae_pose(t: float) -> Pose:
    d = _RT
    lid = d["lid"](t) * (1.0 - blink_amt(t, d["blinks"]))
    lx, ly = d["gaze"](t)
    still = 1.0 - 0.75 * (1.0 - smoothstep((t - SNAP - 0.7) / 0.5)) if t > SNAP else 1.0
    lx += 0.022 * noise1(t * 1.7, 9) * still
    ly += 0.018 * noise1(t * 1.5, 13) * still
    mo, mr = mouth("rae", t)
    wm = d["wipe_mid"]
    trails = 1.0 if t < wm else 0.0
    nod = d["nod"](t) + 0.03 * noise1(t * 0.45, 3)
    tilt = d["tilt"](t) + 1.2 * noise1(t * 0.38, 5)
    # nervous micro-tremor in the first second after the snap
    if SNAP <= t < SNAP + 1.0:
        k = 1.0 - (t - SNAP)
        tilt += 1.2 * k * math.sin((t - SNAP) * 41.0)
    return Pose(
        x=d["x"](t), y=FLOOR, facing=1.0, turn=d["turn"](t), sit=d["sit"](t), seat_y=SEAT_Y, kneel=d["kneel"](t),
        lean=d["lean"](t), head_tilt=tilt, head_nod=nod, head_turn=d["hturn"](t) + 0.015 * noise1(t * 0.5, 4),
        breath=breathe(t, 0.22, 2) * (1.6 if t < SNAP + 2.5 else 1.0),
        lid_l=lid, lid_r=lid * (0.99 + 0.01 * noise1(t * 0.7, 3)), look_x=lx, look_y=ly, pupil=d["pupil"](t),
        squint=d["squint"](t), eye_wide=d["wide"](t),
        brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t), brow_furrow=d["furrow"](t),
        mouth_open=d["open"](t) + 0.82 * mo, mouth_round=clamp(d["round"](t) + mr), smile=d["smile"](t),
        mouth_tremble=d["tremble"](t), tears=d["tears"](t), tear_l=trails, tear_r=trails, eye_shine=d["shine"](t),
        blush=d["blush"](t), sniffle=d["sniffle"](t),
        shoulders_up=d["shoulders"](t), bounce=d["bounce"](t),
        arm_r=_rae_arm_r(t), arm_l=d["arm_l"](t), mug=None if rae_mug_on_bench(t) else "r", **LIGHT,
    )


# =========================================================================== Quill: S3 performance
GEST = QA["gesture_small"]
PRESENT = QA["present"]
QREST = QA["rest"]
RAISE_T0 = CARDS - 0.62                      # anticipation dip, then the palm comes up as the cards spring out


def _quill_tracks():
    d = {}
    SN = SNAP
    d["arm_r"] = ArmSeq([
        (T0, QREST), (Q07 + 0.15, QREST), (Q07 + 0.6, GEST, "io"),
        (Q07 + 0.8, arm_add(GEST, 3.0, -6.0, -8.0), "io"), (Q07 + 1.05, GEST, "io"),        # "quite all right"
        (RAISE_T0, arm_add(GEST, -3.0, -4.0)), (RAISE_T0 + 0.2, arm_add(GEST, -6.0, -10.0, 4.0), "io"),
        (CARDS - 0.02, arm_add(PRESENT, 3.0, 6.0, -6.0), "out"), (CARDS + 0.35, PRESENT, "io"),
    ])
    d["arm_l"] = ArmSeq([(T0, QREST)])
    d["tilt"] = Track([(T0, 7.0), (SN, 7.0), (SN + 0.25, 4.0), (SN + 1.0, 4.0), (SN + 1.5, 8.0), (R10, 7.0),
                       (PT + 0.2, 3.0), (Q06, 2.0), (Q06 + 0.6, 1.0), (Q06 + 1.4, -2.0), (R11 + 0.4, 2.0),
                       (Q07, 3.0), (Q07 + 0.9, 5.0), (CARDS, 2.0), (BEST + 0.8, 1.0), (OTHERS, 3.0),
                       (OTHERS + 1.0, 7.0), (CUT_C2 + 1, 7.0)])
    d["nod"] = Track([(T0, -0.06), (SN + 0.3, 0.0), (PT, 0.0), (PT + 0.12, 0.05), (PT + 0.4, 0.0),
                      (Q06 + 0.05, 0.0), (Q06 + 0.2, -0.12, "out"), (Q06 + 0.5, -0.02), (Q06 + 0.9, -0.2),
                      (R11, -0.12), (R11 + 0.5, 0.0), (Q07 + 0.5, -0.06), (Q07 + 0.9, 0.0), (CARDS, 0.06),
                      (BEST + 0.3, 0.0), (BEST + 0.5, -0.08), (BEST + 0.9, 0.0), (CUT_C2 + 1, 0.0)])
    d["hturn"] = Track([(T0, 0.0), (CARDS + 0.2, 0.0), (CARDS + 0.7, -0.08), (BEST + 0.6, -0.12),
                        (OTHERS + 0.1, -0.04), (OTHERS + 0.6, 0.0)])
    d["brow"] = Track([(T0, 0.12), (SN, 0.12), (SN + 0.3, 0.05), (SN + 1.5, 0.15), (PT, 0.12), (THAT, 0.25),
                       (Q06, 0.1), (Q06 + 0.6, 0.0), (R11 + 0.3, 0.12), (Q07, 0.05), (EIGHT, 0.12),
                       (CARDS, 0.2), (BEST + 0.9, 0.08), (OTHERS + 0.8, 0.22), (CUT_C2 + 1, 0.15)])
    d["worry"] = Track([(T0, 0.0), (Q06 + 0.5, 0.0), (Q06 + 0.9, 0.3), (R11 + 0.6, 0.22), (Q07 + 0.8, 0.05),
                        (Q07 + 1.6, 0.0)])
    d["smile"] = Track([(T0, 0.1), (SN, 0.1), (SN + 0.3, 0.0), (Q07 + 0.2, 0.0), (Q07 + 0.7, 0.08),
                        (Q07 + 1.6, 0.02), (OTHERS + 0.8, 0.06), (CUT_C2 + 1, 0.06)])
    d["glow"] = Track([(T0, 0.3), (SN, 0.3), (SN + 0.15, 0.12), (CARDS - 0.1, 0.12), (CARDS + 0.1, 0.55),
                       (CARDS + 1.2, 0.2), (CUT_C2 + 1, 0.16)])
    d["lid"] = Track([(T0, 1.0), (Q06 + 0.6, 1.0), (Q06 + 1.0, 0.86), (R11 + 0.3, 0.95), (Q07, 1.0)])
    d["gaze"] = gaze([
        (T0, (-0.48, 0.42)),
        (SN + 1.45, (-0.44, 0.34)), (SN + 1.8, (-0.48, 0.4)),
        (Q06 + 0.95, (-0.3, 0.68), 0.25),                                    # "...care for it" - gaze lowers
        (R11 - 0.05, (-0.5, 0.36)), (R11 + 0.3, (-0.58, 0.18), 0.18),         # follows her up ...
        (R11 + 1.15, (-0.44, 0.26), 0.25),                                   # ... and down
        (CARDS - 0.25, (-0.3, 0.6)), (CARDS + 0.15, (-0.55, 0.15), 0.2),      # palm -> the fan opening
        (CARDS + 0.6, (-0.72, 0.02), 0.3),
        (BEST + 0.15, (-0.86, 0.18)),                                        # No. 1
        (OTHERS - 0.1, (-0.44, 0.26)),                                       # back to her
    ], dur=0.09)
    return d


_QT = _quill_tracks()


def quill_pose(t: float) -> Pose:
    d = _QT
    mo, mr = mouth("quill", t)
    lid = d["lid"](t)
    blink = auto_blink(t, seed=0, rate=4.6, robotic=True)
    lx, ly = d["gaze"](t)
    return Pose(
        x=QX, y=FLOOR, facing=-1.0, turn=0.35,
        head_turn=d["hturn"](t), head_nod=d["nod"](t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=d["tilt"](t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=lid * blink, lid_r=lid * blink, look_x=lx, look_y=ly, brow_raise=d["brow"](t),
        brow_worry=d["worry"](t), smile=d["smile"](t), mouth_open=0.9 * mo, mouth_round=mr, glow=d["glow"](t),
        arm_r=d["arm_r"](t), arm_l=d["arm_l"](t), **LIGHT,
    )


# =========================================================================== fan state
FAN_OPEN = Track([(CARDS - 0.04, 0.0), (CARDS + 1.3, 1.0, "lin")])
CARD1_GLOW = Track([(CARDS + 0.6, 0.0), (BEST + 0.25, 0.0), (BEST + 0.7, 0.6, "io")])


def draw_fan_s3(c, t):
    p = FAN_OPEN(t)
    if p <= 0:
        return
    draw_fan(c, t, p, states={1: CARD1_GLOW(t)})
    if BEST + 0.25 <= t < BEST + 1.0:
        x, y = card_xy(1)
        select_flash(c, t, BEST + 0.25, x, y, 0.45)


# =========================================================================== cameras
@lru_cache(maxsize=1)
def _kneel_face():
    p = Pose(x=KNEEL_X, y=FLOOR, facing=1.0, turn=0.3, sit=1.0, kneel=1.0, seat_y=SEAT_Y, head_nod=0.42)
    return R.head_center(p)


@lru_cache(maxsize=1)
def _seat_face():
    return R.head_center(Pose(x=SEAT_X, y=FLOOR, facing=1.0, turn=0.35, sit=1.0, seat_y=SEAT_Y))


QFACE = Q.head_center(Pose(x=QX, y=FLOOR, facing=-1.0, turn=0.35))
SNAP_ZOOM = 2.25
Q_HAND_X0 = Q.hand_pos(Pose(x=QX, y=FLOOR, facing=-1.0, turn=0.35, arm_l=QA["rest"]), "l")[0] - 18.0


def _face_cam(fx_, fy_, z, sx, sy):
    """Camera at zoom z that puts stage point (fx_, fy_) at screen pixel (sx, sy)."""
    return Camera(fx_ + (W / 2 - sx) / z, fy_ + (H / 2 - sy) / z, z)


def _rae_head(t):
    return R.head_center(rae_pose(min(t, CUT_C2 + 0.5)))


@lru_cache(maxsize=1)
def _snap_head():
    return smoothed(_rae_head, SNAP, 6, 0.08)


def camera(t: float) -> Camera:
    if t < CUT_TWO:                                        # 1 MCU Rae on her knees + jolt
        # the snap is a hard cut: a slightly tighter reframe of S2's closing shot, with Quill's hanging hand
        # (stage x ~ 433..463) kept just outside the right edge even when the soft follow drifts right
        fk = _kneel_face()
        z = SNAP_ZOOM
        base = _face_cam(fk[0], fk[1], z, 372.0, 505.0)
        hx, hy = smoothed(_rae_head, t, 6, 0.08)
        h0 = _snap_head()
        follow = 0.5
        cx = base.cx + follow * (hx - h0[0])
        cx_max = Q_HAND_X0 - W / 2 / (z * 1.07)
        cx = min(cx, cx_max - 6.0 * (1.0 - math.exp(-max(0.0, cx - cx_max + 6.0) / 6.0)))   # soft clamp
        cam = Camera(cx, base.cy + follow * (hy - h0[1]), z)
        push = smoothstep((t - (R10 - 0.1)) / (CUT_TWO - R10 + 0.1))
        cam.zoom *= 1.0 + 0.07 * push
        jx, jy, jz = jolt(t, SNAP, 0.8, 0.5)
        return Camera(cam.cx + jx, cam.cy + jy, cam.zoom * jz)
    if t < CUT_QMED:                                       # 2 TWO-SHOT: the point
        a = Camera(400.0, 724.0, 1.22)
        b = Camera(403.0, 718.0, 1.26)
        jx, jy, jz = jolt(t, CUT_TWO + 0.1, 0.35, 0.35)
        cam = drift(a, b, t, CUT_TWO, CUT_QMED)
        return Camera(cam.cx + jx, cam.cy + jy, cam.zoom * jz)
    if t < CUT_WIDE:                                       # 3 MEDIUM Quill
        a = _face_cam(QFACE[0], QFACE[1], 2.0, 386.0, 470.0)          # her puff out of frame left (even leaning in)
        return drift(a, nudge(a, -2.0, -2.0, 1.03), t, CUT_QMED, CUT_WIDE)
    if t < CUT_DREAD:                                      # 4 MEDIUM-WIDE: scramble, sit, mug ...
        if t < CUT_FAN:
            return drift(Camera(362.0, 770.0, 1.16), Camera(366.0, 760.0, 1.2), t, CUT_WIDE, CUT_FAN)
        b = Camera(360.0, 646.0, 1.25)                     # ... 5 tilts up with the cards into the 3-shot
        if t < CARDS + 0.9:                                # (same framing family as S4's presentation shots)
            return drift(Camera(366.0, 760.0, 1.2), b, t, CUT_FAN, CARDS + 0.9)
        return drift(b, Camera(358.0, 640.0, 1.29), t, CARDS + 0.9, CUT_DREAD)
    # 6 CLOSE-UP Rae: dawning dread (slow push; runs into S4 until card2). Tight enough that Quill's
    #   presenting hand (x > ~400) stays out of frame and only the glow of the lowest card grazes the top.
    fs = _seat_face()
    u = clamp((t - CUT_DREAD) / (CUT_C2 - CUT_DREAD))
    hx, hy = smoothed(_rae_head, t, 6, 0.1)
    z = lerp(3.12, 3.32, ease_in_out(u))
    return _face_cam(lerp(fs[0], hx, 0.5), lerp(fs[1], hy, 0.5), z, 356.0, 540.0)


def shot_name(t):
    for name, b in (("rae_snap", CUT_TWO), ("two_point", CUT_QMED), ("quill_med", CUT_WIDE),
                    ("wide_scramble_fan", CUT_DREAD)):
        if t < b:
            return name
    return "rae_dread"


# =========================================================================== render
def draw_stage(c, t, cam, rp, qp, mug_on_bench, fan_fn):
    """Lounge -> mug on bench -> Quill -> Rae -> lounge front -> holo-cards (stage space)."""
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, t, light=1.0)
    if mug_on_bench:
        R.draw_mug(c, MUG_SPOT[0], MUG_SPOT[1], 1.0, 0.0, False)
    Q.draw(c, qp, t)
    R.draw(c, rp, t)
    env.draw_lounge_front(c, t, light=1.0)
    if fan_fn is not None:
        fan_fn(c, t)
    c.restore()


def _fan_fx(c, t):
    palm_burst(c, t, CARDS, FAN[0], FAN[1])
    draw_fan_s3(c, t)


def render(canvas, t):
    if t < SNAP:
        # the silent beat after the last mote: S2's last shot continues until the snap
        from anim.scenes import s2
        s2.render(canvas, t)
        return
    cam = camera(t)
    # the snap: the lights slam on - two frames of overexposure (gain, not a milky wash) falling away fast
    dt = t - SNAP
    k = 1.0 - dt / 0.11 if dt < 0.11 else 0.0
    if k > 0:
        g = 1.0 + 0.5 * k * k
        cf = skia.ColorFilters.Matrix([g, 0, 0, 0, 0.04 * k * k, 0, g, 0, 0, 0.03 * k * k,
                                       0, 0, g, 0, 0.015 * k * k, 0, 0, 0, 1, 0])
        with Layer(canvas, cf=cf):
            draw_stage(canvas, t, cam, rae_pose(t), quill_pose(t), rae_mug_on_bench(t), _fan_fx)
        glow(canvas, W * 0.5, H * 0.32, 760, "#FFEBCF", 0.26 * k * k)
    else:
        draw_stage(canvas, t, cam, rae_pose(t), quill_pose(t), rae_mug_on_bench(t), _fan_fx)
