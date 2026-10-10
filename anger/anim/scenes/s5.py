"""S5 - The voice (BIBLE section 4, S5; handoffs section 9).

Anger, flat on his back at the bottom of the shaft where S3/S4 left him (pelvis at s3.LIE_X, head toward the
wall, shield on his back, bruised; one eye open, the monster gone; his sword still stuck in the wall above -
s3.draw_stuck_sword), heaves himself back along the floor and props himself against the rock wall (wall face on the RIGHT at env.WALL_X, the hermit's deep shadow at
screen-left - the hermit is never seen). "Who are you? How did you get here?" - silence, his eyes searching the
dark - "The food was good... but now a nap sounds even better." - a slow, weary eye roll - LOUD snoring from the
dark - a slow side-glance - he stares into nothing, "How did I get myself into this..." (muttered), a long
exhale - he gives up and closes his eyes (head tilts: `sleep`).

The comedy is that he is completely serious: static frames, silences left to sit, reactions a beat late, tiny
faces. render(canvas, t) is a pure function of absolute time t; the performance (anger_pose) runs continuously
through every cut and each shot only picks a camera. All times come from build/timeline.json names.

This module also holds the helpers shared with anim/scenes/s6.py (lighting of the grotto, the frame renderer,
gaze / blink / breathing helpers, camera helpers, the sitting position).

Shot list (absolute times only for orientation)
  A  140.31 -> a01-0.26       MEDIUM-WIDE static: on his back, one eye open; prop_up (140.61): up on an elbow,
                              one heave back along the floor (the scrape) - his back thumps into the wall (141.43)
  B  -> a01 end+2.3           MEDIUM, the dark as negative space at screen-left: a01 toward the dark, then the
                              silence - his eyes search the dark
  C  -> eye_roll-0.19         WIDE static, the dark fills the frame, Anger small at the right: m03 from the dark
  D  -> contemplate-0.09      CLOSE-UP: the slow weary eye roll (152.04); snoring starts (152.94); a slow,
                              late side-glance toward the dark
  E  -> close_eyes-0.21       slow PUSH-IN: he stares into nothing; a02 (muttered); a long exhale
  F  -> s5 end (-> S6)        MEDIUM-WIDE static: he gives up, closes his eyes, the head tilts (sleep)
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from anim import char_anger as A
from anim import env, light
from anim.core import (Camera, Track, beat, clamp, ease_in_out, ease_out, lerp, line_end, line_start, mouth,
                       scene_span, smoothstep, timeline, window)
from anim.light import Light
from anim.rig import ArmPose, Pose
from config import H, W


def _s3():
    """S3's depths staging (where the fall left him, the sword stuck in the wall) - used for continuity; the
    scene still renders if that module is unavailable."""
    try:
        from anim.scenes import s3 as m
        return m
    except Exception:  # noqa: BLE001
        return None


S3 = _s3()

# =========================================================================== timing (all from names)
T0, T1 = scene_span("s5")
S, E = line_start, line_end


def sfx_time(name, after=0.0):
    """First placement of SFX `name` in the timeline at or after `after`."""
    for s in timeline()["sfx"]:
        if s["name"] == name and s["start"] >= after - 1e-6:
            return s["start"]
    raise KeyError(name)


PROP = beat("prop_up")
SCRAPE = sfx_time("armor_scrape", T0)
SETTLE = SCRAPE + 0.62                 # armor_scrape: settle thud +0.62 (his back meets the wall)
A01, A01E = S("a01"), E("a01")
M03, M03E = S("m03"), E("m03")
M03_GAP = M03 + 1.21                   # "...but now a nap sounds even better" (lip-sync gap 149.46-149.83)
ROLL = beat("eye_roll")
SNORE = beat("snore_start")
CONTEMPLATE = beat("contemplate")
A02, A02E = S("a02"), E("a02")
CLOSE = beat("close_eyes")
SNORE_LOOP = 18.0                      # snore_loop.wav length (it tiles until `startled`)
SNORE_BREATHS = [SNORE + k * SNORE_LOOP + o for k in range(2) for o in (0.0, 4.5, 8.8, 13.6)]

# =========================================================================== geometry
FLOOR = float(env.FLOOR_Y)
LIE_X = float(getattr(S3, "LIE_X", 150.0))   # pelvis x lying on his back where S3/S4 left him (head to the wall)
SIT_X = 440.0                          # pelvis x propped against the wall (his back on the wall face)
DARK = (-120.0, 900.0)                 # where the hermit's voice comes from (deep shadow, screen-left)
AR = A.ARMS
REST_NEAR = ArmPose(shoulder=40.0, elbow=58.0, wrist=6.0, hand="relaxed")     # forearm on the raised knee
REST_FAR = ArmPose(shoulder=30.0, elbow=30.0, wrist=8.0, hand="relaxed")      # hand on the thigh
PUSH_NEAR = ArmPose(shoulder=-30.0, elbow=24.0, wrist=20.0, hand="open")      # palm planted behind the hip
PUSH_FAR = ArmPose(shoulder=-22.0, elbow=30.0, wrist=16.0, hand="open")

# =========================================================================== light (shared with S6)
AMB = 0.115
RIM = "#A6C8E6"                        # cold rim on Anger (as in S3/S4)
FILL_COLD = "#7E9CC4"
POOL = Light(480.0, 700.0, 520.0, 0.30, "#9AB0D8", "point")        # cold spill around his spot by the wall
SHAFT = Light(420.0, 0.0, 1100.0, 0.18, "#8FA6D0", "point")         # faint cold light from the hole above
LEFT = Light(60.0, 300.0, 1100.0, 0.14, "#7F96C0", "point")         # dim air over the floor at screen-left


def scene_lights(t, extra=(), strength=1.0, head=None):
    """The grotto's light: dim fungi, a cold spill by the wall, the faint shaft light, dim air at screen-left,
    and (as in S4) a soft cold fill that stays near Anger's face so he always reads."""
    L = env.depths_lights(t, strength)
    if strength > 0.01:
        k = strength
        L += [Light(b.x, b.y, b.radius, b.intensity * k, b.color, "point") for b in (POOL, SHAFT, LEFT)]
        if head is not None:
            L.append(Light(head[0] - 140.0, head[1] + 20.0, 620.0, 0.16 * k, FILL_COLD, "point"))
    return L + list(extra)


def dress_anger(p: Pose, at, lights, amb=AMB, rim=0.6, rim_dir=-100.0):
    """Anger stays drawn lit (apply_darkness darkens him like the set): his colour leans toward the light he is
    in, plus the cold rim (the same recipe as S3/S4's dress(), so the cut from S4 matches)."""
    r, g, b = light.light_at(at[0], at[1], amb, lights)
    m = max(r, g, b, 1e-3)
    p.light = 1.0
    p.tint = (int(255 * r / m), int(255 * g / m), int(255 * b / m))
    p.tint_amt = 0.14
    p.rim = rim
    p.rim_color = RIM
    p.extra["rim_dir"] = rim_dir
    return p


def lit_pose(p: Pose, at, lights, amb=AMB, rim=0.7, rim_color=RIM, tint_amt=0.18, base=0.62):
    """Pose.light / tint / rim from the light map at stage point `at` (the face), so the cel shading follows the
    darkness (apply_darkness still does the real darkening)."""
    r, g, b = light.light_at(at[0], at[1], amb, lights)
    v = max(r, g, b)
    p.light = clamp(base + 0.55 * v, base, 1.0)
    p.tint = (20, 34, 58)
    p.tint_amt = tint_amt
    p.rim = rim
    p.rim_color = rim_color
    return p


# =========================================================================== small animation helpers
def _sac(u):
    """Saccade profile: quick move with a 5 % overshoot that settles."""
    if u <= 0.0:
        return 0.0
    if u < 1.0:
        return 1.05 * ease_out(u)
    if u < 2.6:
        return 1.05 - 0.05 * smoothstep((u - 1.0) / 1.6)
    return 1.0


class Gaze:
    """keys = [(t, look_x, look_y[, dur[, kind]])]: the first key is the start value; each later key moves
    there from wherever the eyes are (kind 'sac' = saccade with a tiny settle, 'io' = slow slide)."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def __call__(self, t):
        x, y = self.keys[0][1], self.keys[0][2]
        for k in self.keys[1:]:
            if t <= k[0]:
                break
            d = k[3] if len(k) > 3 else 0.08
            kind = k[4] if len(k) > 4 else "sac"
            u = (t - k[0]) / d
            w = _sac(u) if kind == "sac" else ease_in_out(u)
            x += (k[1] - x) * w
            y += (k[2] - y) * w
        return x, y


def blink_shape(dt, dur=0.34):
    """Anger's heavy blink (1 open .. 0 shut) dt seconds after it starts (same shape as char_anger.blink)."""
    if dt < 0.0 or dt >= dur:
        return 1.0
    x = dt / dur
    if x < 0.32:
        return 1.0 - math.sin(x / 0.32 * math.pi / 2)
    if x < 0.45:
        return 0.0
    return 1.0 - math.cos((x - 0.45) / 0.55 * math.pi / 2)


def blinks(t, times, dur=0.34):
    v = 1.0
    for b in times:
        if b - 0.05 <= t <= b + dur + 0.05:
            v = min(v, blink_shape(t - b, dur))
    return v


def pulse(t, t0, attack=0.06, decay=0.25):
    """0 -> 1 -> 0 bump starting at t0."""
    d = t - t0
    if d < 0.0:
        return 0.0
    if d < attack:
        return smoothstep(d / attack)
    return math.exp(-(d - attack) / max(1e-4, decay)) * (1.0 if d < attack + 6 * decay else 0.0)


class Breath:
    """Phase-continuous breathing: rate (Hz) and amplitude Tracks, plus an override Track blended in by a weight
    Track (held breaths, sighs). Values are fed to Pose.breath (the rig's auto breath would jump in phase when a
    state blend changes its rate)."""

    def __init__(self, t0, t1, rate, amp, override=None, weight=None, seed=0.7):
        self.t0, self.t1 = t0, t1
        self.rate, self.amp, self.ov, self.w = rate, amp, override, weight
        self.seed = seed
        self._tab = None

    def _table(self):
        if self._tab is None:
            n = int((self.t1 - self.t0 + 2.0) * 240) + 2
            ts = self.t0 - 1.0 + np.arange(n) / 240.0
            rates = np.array([self.rate(x) for x in ts])
            cyc = np.concatenate([[0.0], np.cumsum((rates[1:] + rates[:-1]) * 0.5 / 240.0)])
            self._tab = (ts, cyc)
        return self._tab

    def __call__(self, t):
        ts, cyc = self._table()
        c = float(np.interp(t, ts, cyc))
        v = math.sin(2 * math.pi * c + self.seed) * self.amp(t)
        if self.ov is not None:
            w = clamp(self.w(t))
            if w > 0:
                v = lerp(v, self.ov(t), w)
        return v


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


# =========================================================================== camera helpers
def cam_at(pt, zoom, sx, sy):
    """Camera at `zoom` that puts stage point `pt` at screen pixel (sx, sy)."""
    return Camera(pt[0] + (W / 2 - sx) / zoom, pt[1] + (H / 2 - sy) / zoom, zoom)


def drift(a: Camera, b: Camera, t, t0, t1, ease=ease_in_out):
    return Camera.lerp(a, b, ease(clamp((t - t0) / max(1e-6, t1 - t0))))


def pick(shots, t):
    """shots = [(t_start, fn(t) -> Camera)] sorted; the last one that has started."""
    cur = shots[0][1]
    for ts, fn in shots:
        if t >= ts:
            cur = fn
    return cur(t)


# =========================================================================== frame renderer (shared with S6)
SOFT_BG_ZOOM = 1.95                    # close-ups: the set is drawn at half resolution (a soft, defocused rock wall)
_BG = {}


def _draw_set(c, t, dust, grit):
    env.draw_depths(c, t, dust=dust, shake=grit)
    if S3 is not None and hasattr(S3, "draw_stuck_sword"):
        S3.draw_stuck_sword(c, t)                       # his sword, still stuck in the wall up there


def _soft_set(canvas, t, cam, dust, grit):
    """Close-ups: render the set into a half-size surface and scale it up - a gentle depth-of-field softness
    behind the faces (smoother for the encoder, and a quarter of the tile-cache fill cost at the cut)."""
    surf = _BG.get("s")
    if surf is None:
        surf = _BG["s"] = skia.Surface(W // 2, H // 2)
    c = surf.getCanvas()
    c.resetMatrix()
    c.clear(skia.ColorBLACK)
    c.save()
    c.scale(0.5, 0.5)
    cam.apply(c, t)
    _draw_set(c, t, dust, grit)
    c.restore()
    canvas.save()
    canvas.resetMatrix()
    canvas.drawImageRect(surf.makeImageSnapshot(), skia.Rect(0, 0, W, H),
                         skia.SamplingOptions(skia.FilterMode.kLinear))
    canvas.restore()


def render_world(canvas, t, cam, anger=None, friend=None, friend_mod=None, lit_fx=None, emis_fx=None,
                 amb=AMB, lights=None, dust=0.15, grit=0.0, vig=0.45, friend_body=True, friend_tongue=True):
    """Lit set + characters (camera applied) -> darkness -> emissive fungi -> vignette.
    friend_mod: the friend module (anim.char_friend) when `friend` (its Pose) is given; its body is drawn behind
    Anger and its tongue (tongue_layer='skip') in front of him. lit_fx(canvas) draws lit extras (drips) last."""
    if lights is None:
        lights = scene_lights(t)
    if cam.zoom >= SOFT_BG_ZOOM:
        _soft_set(canvas, t, cam, dust, grit)
    canvas.save()
    cam.apply(canvas, t)
    if cam.zoom < SOFT_BG_ZOOM:
        _draw_set(canvas, t, dust, grit)
    if friend is not None and friend_body:
        friend_mod.draw(canvas, friend, t)
    if anger is not None:
        A.draw(canvas, anger, t)
    if friend is not None and friend_tongue:
        friend_mod.draw_tongue(canvas, friend, t)
    if lit_fx is not None:
        lit_fx(canvas)
    canvas.restore()
    canvas.resetMatrix()
    light.apply_darkness(canvas, cam, ambient=amb, lights=lights, t=t)
    canvas.save()
    cam.apply(canvas, t)
    excl = []
    if anger is not None:
        excl.append((anger.x - 470.0, FLOOR - 640.0, max(anger.x + 160.0, 700.0), FLOOR + 10.0))
    if friend is not None and friend_body:
        hw = 600.0 * friend.scale
        excl.append((friend.x - hw - 340.0 * friend.scale, friend.y - 1700.0 * friend.scale, friend.x + hw,
                     friend.y + 5.0))
    env.draw_fungi_glow(canvas, t, "depths", exclude=excl)
    if emis_fx is not None:
        emis_fx(canvas)
    canvas.restore()
    canvas.resetMatrix()
    light.vignette(canvas, vig)


# =========================================================================== Anger's performance
# ---- body
# up on an elbow, then one heave back along the floor (the scrape) until his back thumps into the wall (settle)
MIX_UP = Track([(PROP, 0.0), (PROP + 0.26, 0.34, "io"), (SCRAPE + 0.04, 0.38), (SETTLE - 0.06, 1.0, "io")])
X_UP = Track([(SCRAPE, LIE_X), (SETTLE - 0.04, SIT_X, "io")])
MIX_SLEEP = Track([(CLOSE + 0.30, 0.0), (CLOSE + 2.1, 1.0, "io")])                          # prop_sit -> sleep
# settle against the wall: the torso rocks back into it and resettles (pose.lean + = toward facing)
LEAN = Track([(SETTLE - 0.08, 0.0), (SETTLE + 0.07, -3.0, "out"), (SETTLE + 0.42, 0.8, "io"), (SETTLE + 0.85, 0.0)])

S4_NEAR = ArmPose(shoulder=-6.0, elbow=22.0, wrist=0.0, hand="relaxed")      # S4's last frame
S4_FAR = ArmPose(shoulder=4.0, elbow=18.0, wrist=10.0, hand="relaxed")
ARM_NEAR = ArmSeq([(PROP + 0.04, S4_NEAR), (PROP + 0.34, PUSH_NEAR), (SETTLE - 0.05, PUSH_NEAR),
                   (SETTLE + 0.55, REST_NEAR)])
PLANT = (SIT_X + 48.0, FLOOR - 10.0)            # where the near palm pushes off the floor while he scoots back
PLANT_W = Track([(PROP + 0.08, 0.0), (SCRAPE, 1.0, "io"), (SETTLE - 0.15, 1.0), (SETTLE + 0.3, 0.0, "io")])
ARM_FAR = ArmSeq([(PROP + 0.08, S4_FAR), (PROP + 0.38, PUSH_FAR), (SETTLE - 0.02, PUSH_FAR),
                  (SETTLE + 0.7, REST_FAR)])

# ---- breathing
BREATH = Breath(
    T0, T1,
    rate=Track([(T0, 0.24), (SETTLE + 1.4, 0.21), (CLOSE, 0.19), (CLOSE + 2.2, 0.15)]),
    amp=Track([(T0, 1.25), (SETTLE + 1.6, 0.95), (CLOSE, 0.95), (CLOSE + 2.2, 1.45)]),
    override=Track([(SETTLE - 0.3, 0.6), (SETTLE + 0.2, 1.1, "io"), (SETTLE + 1.25, -1.2, "io"),
                    (A02E + 0.05, -0.3), (A02E + 0.45, 1.25, "io"), (A02E + 1.95, -1.45, "io")]),
    weight=Track([(SETTLE - 0.5, 0.0), (SETTLE - 0.1, 1.0), (SETTLE + 1.3, 1.0), (SETTLE + 2.1, 0.0),
                  (A02E - 0.15, 0.0), (A02E + 0.1, 1.0), (A02E + 2.0, 1.0), (A02E + 3.1, 0.0)]),
)

# ---- eyes
LID = Track([(T0, 0.85), (PROP + 0.12, 0.85), (PROP + 0.3, 0.86), (SETTLE + 0.1, 0.8), (SETTLE + 0.6, 0.87),
             (M03_GAP, 0.86), (M03_GAP + 1.2, 0.74), (ROLL, 0.74), (ROLL + 0.38, 0.97), (ROLL + 0.95, 0.7),
             (ROLL + 1.4, 0.63), (SNORE + 2.0, 0.62), (CONTEMPLATE, 0.63), (CONTEMPLATE + 0.8, 0.7),
             (A02E + 0.3, 0.68), (A02E + 1.7, 0.5), (CLOSE, 0.48), (CLOSE + 0.75, 0.0, "io")])
ONE_EYE = Track([(T0, 1.0), (PROP + 0.1, 1.0), (PROP + 0.34, 0.0)])
STRAIN = Track([(PROP + 0.05, 0.0), (PROP + 0.3, 0.5), (SETTLE, 0.42), (SETTLE + 0.55, 0.0)])
GRIMACE = Track([(PROP + 0.05, 0.0), (PROP + 0.3, 0.32), (SETTLE, 0.3), (SETTLE + 0.45, 0.0)])
GAZE = Gaze([
    (T0, -0.08, 1.0),                           # lying: head-local axes (S4's last look: toward the dark)
    (PROP + 0.12, -0.35, 0.5, 0.12),            # watches where he's going
    (SETTLE + 0.25, -0.5, 0.22, 0.14),
    (SETTLE + 0.9, -0.86, 0.04),                # to the dark (blink with it)
    (A01 - 0.3, -0.9, 0.0, 0.07),
    (A01E + 0.3, -0.98, 0.17),                  # silence: searching the dark
    (A01E + 1.05, -0.7, -0.12),
    (A01E + 1.8, -0.92, 0.06),
    (M03 + 0.45, -0.86, 0.02, 0.07),
    (ROLL + 1.32, 0.05, 0.16, 0.25, "io"),      # (the roll itself is ROLL_PATH)
    (SNORE + 0.82, -0.93, 0.06, 0.5, "io"),     # slow, late side-glance at the snoring
    (CONTEMPLATE + 0.22, 0.12, 0.28, 0.65, "io"),   # into nothing
    (A02E + 0.5, 0.08, 0.36, 0.9, "io"),
    (CLOSE + 0.2, 0.05, 0.45, 0.6, "io"),
])


def roll_path(t):
    """The weary eye roll: from the dark (left), up over the top, round to the right, then down to centre.
    Returns (look_x, look_y, weight)."""
    u = (t - ROLL) / 0.95
    if u <= 0.0 or t > ROLL + 1.35:
        return 0.0, 0.0, 0.0
    a = math.pi * (1.0 - 0.95 * ease_in_out(u))
    x, y = 0.86 * math.cos(a), -0.98 * math.sin(a)
    w = smoothstep(u / 0.12) * (1.0 - smoothstep((t - ROLL - 0.95) / 0.4))
    return x, y, w


BLINKS = [T0 + 0.05 - 0.4, PROP + 0.95, SETTLE + 0.88, A01 + 1.08, A01E + 1.0, M03 + 1.9, ROLL + 1.42,
          SNORE + 2.15, CONTEMPLATE + 1.0, A02 + 1.75, A02E + 1.25]

HEAD_TURN = Track([(T0, 0.05), (SETTLE + 0.85, 0.0), (SETTLE + 1.3, 0.13), (A01E + 0.9, 0.13), (A01E + 1.6, 0.1),
                   (ROLL, 0.1), (ROLL + 0.6, 0.03), (ROLL + 1.3, 0.06), (CONTEMPLATE + 0.25, 0.06),
                   (CONTEMPLATE + 1.2, -0.05), (CLOSE, -0.05), (CLOSE + 2.0, -0.02)])
HEAD_NOD = Track([(T0, 0.0), (PROP + 0.3, -0.12), (SETTLE, -0.05), (SETTLE + 0.6, 0.0), (A01 - 0.1, 0.0),
                  (A01 + 0.3, -0.07), (A01E + 0.2, -0.02), (ROLL, -0.02), (ROLL + 0.45, 0.14),
                  (ROLL + 1.25, 0.0), (CONTEMPLATE + 0.3, 0.0), (CONTEMPLATE + 1.3, -0.1), (A02E + 0.3, -0.1),
                  (A02E + 1.9, -0.2), (CLOSE + 0.6, -0.2), (CLOSE + 1.8, -0.05)])
HEAD_TILT = Track([(ROLL, 0.0), (ROLL + 0.5, -3.0), (ROLL + 1.3, 0.0)])
BROW_RAISE = Track([(ROLL, 0.0), (ROLL + 0.4, 0.32), (ROLL + 1.1, 0.0), (A01E + 0.6, 0.0), (A01E + 0.9, 0.08),
                    (A01E + 1.7, 0.0)])
BROW_FURROW = Track([(SETTLE + 0.5, 0.0), (A01 - 0.1, 0.0), (A01 + 0.35, 0.22), (A01E + 0.3, 0.2),
                     (M03 + 0.5, 0.12), (ROLL, 0.08), (ROLL + 0.5, 0.0), (SNORE + 1.0, 0.0), (SNORE + 2.0, 0.1),
                     (CONTEMPLATE + 0.5, 0.0)])
BROW_WORRY = Track([(CONTEMPLATE, 0.0), (CONTEMPLATE + 1.0, 0.22), (A02 + 0.5, 0.32), (A02E + 0.6, 0.25),
                    (CLOSE + 0.5, 0.15), (CLOSE + 2.0, 0.0)])


def anger_pose(t) -> Pose:
    """Anger at absolute time t in S5 (stage coords)."""
    if t < SETTLE + 0.5:
        st, stb, mix = "lie_back", "prop_sit", MIX_UP(t)
    else:
        st, stb, mix = "prop_sit", "sleep", MIX_SLEEP(t)
    x = X_UP(t)
    p = Pose(x=x, y=FLOOR, facing=-1.0, turn=0.3, arm_l=ARM_NEAR(t), arm_r=ARM_FAR(t))
    p.lean = LEAN(t)
    # settle bob (his back thumps into the wall)
    p.bounce = -4.0 * pulse(t, SETTLE, 0.04, 0.12)
    p.breath = BREATH(t)
    # ---- face
    lx, ly = GAZE(t)
    rx, ry, rw = roll_path(t)
    p.look_x, p.look_y = lerp(lx, rx, rw), lerp(ly, ry, rw)
    lid = LID(t) * blinks(t, BLINKS)
    p.lid_l = p.lid_r = lid
    p.head_turn = HEAD_TURN(t) + 0.022 * math.sin(2 * math.pi * 0.85 * (t - A02)) * window(t, A02 + 0.3, A02E, 0.4, 0.4)
    p.head_nod = HEAD_NOD(t) + 0.1 * pulse(t, SETTLE, 0.04, 0.14)
    p.head_tilt = HEAD_TILT(t)
    p.brow_raise = BROW_RAISE(t)
    p.brow_furrow = BROW_FURROW(t)
    p.brow_worry = BROW_WORRY(t)
    mo, mr = mouth("anger", t)
    if A02 - 0.1 <= t <= A02E + 0.1:
        mo *= 0.68                                           # muttered
    # the long exhale through barely parted lips
    mo = max(mo, 0.07 * window(t, A02E + 0.55, A02E + 2.0, 0.3, 0.5))
    p.mouth_open, p.mouth_round = mo, mr
    p.smile = -0.08 * window(t, A02E + 0.4, CLOSE + 1.0, 0.5, 0.8)
    p.extra = dict(state=st, state_b=stb, mix=mix, sword=None, shield="back", bruised=1.0,
                   one_eye=ONE_EYE(t), strain=STRAIN(t), grimace=GRIMACE(t), knee_up=0.55, rim_dir=-105.0)
    pw = PLANT_W(t)
    if pw > 0.001:
        p.extra["reach_l"] = PLANT
        p.extra["reach_l_w"] = pw
    return p


# =========================================================================== shots
def _face(t):
    return A.head_center(anger_pose(t), t)


@lru_cache(maxsize=None)
def _face_at(t):
    return _face(t)


DUST = Track([(T0, 0.3), (T0 + 9.0, 0.15)])      # S4's settling dust thins out

CUT_B = A01 - 0.26
CUT_C = A01E + 2.3
CUT_D = ROLL - 0.19
CUT_E = CONTEMPLATE - 0.09
CUT_F = CLOSE - 0.21

CAM_A = Camera(235.0, 905.0, 0.86)
CAM_F = None                                   # set below (shared with S6's first shot)


def _cam_b(t):
    return cam_at(_face_at(round(A01, 2)), 1.75, 470.0, 470.0)


def _cam_c(t):
    return cam_at(_face_at(round(M03, 2)), 0.78, 575.0, 575.0)


def _cam_d(t):
    f = _face_at(round(ROLL, 2))
    return cam_at((f[0], f[1] + 12.0), 2.75, 372.0, 520.0)


def _cam_e(t):
    f = _face_at(round(A02, 2))
    # a slow creep (kept inside one of env's tile resolution buckets, (2.0, 2.38])
    a = cam_at((f[0], f[1] + 18.0), 2.03, 372.0, 548.0)
    b = cam_at((f[0], f[1] + 14.0), 2.36, 372.0, 525.0)
    return drift(a, b, t, CUT_E, CUT_F + 0.3, ease=lambda x: smoothstep(x) * 0.6 + x * 0.4)


def cam_f(t=None):
    """The closing medium-wide (S6 starts on the same framing)."""
    return Camera(415.0, 860.0, 1.22)


SHOTS = [
    (T0, lambda t: CAM_A),
    (CUT_B, _cam_b),
    (CUT_C, _cam_c),
    (CUT_D, _cam_d),
    (CUT_E, _cam_e),
    (CUT_F, cam_f),
]


def camera(t):
    cam = pick(SHOTS, t)
    # the settle thud against the wall: a tiny jolt
    from anim.fx import camera_shake
    return camera_shake(cam, t, [(SETTLE, 3.0, 0.32)], seed=51)


# =========================================================================== render / sfx
def render(canvas, t):
    cam = camera(t)
    p = anger_pose(t)
    hc = A.head_center(p, t)
    lights = scene_lights(t, head=hc)
    dress_anger(p, hc, lights)
    render_world(canvas, t, cam, anger=p, lights=lights, dust=DUST(t))


def sfx_events():
    """Motion-locked sounds (the prop-up scrape is already in the timeline)."""
    return [
        {"name": "armor_shift", "start": round(CLOSE + 0.55, 3), "gain_db": -21.0},   # slumps into sleep
    ]
