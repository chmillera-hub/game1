"""S1 - The approach (BIBLE section 4, S1; tunnel set env.draw_tunnel).

Frame 0 is a close-up of the torch flame with Anger's grim face half-lit beside it; the camera pulls back
while the title burns in (title_in .. title_out) and he sets off. Every walking footfall lands on a taiko
hit of the "descent" cue: the walk grid walk_start + k*0.55 s, then the real (ritardando) beat times from
build/music/envelopes.json after it slows down (vines / webs / door approach).  The charge runs on its own
0.31 s taiko grid into the door burst.

Staging: the tunnel is a side view (Anger faces +1 = screen-right, torch high in his far / left hand, sword in
the right, shield on his back).  He cuts the vine curtain with three chops (blade contact 2 frames after each
chop beat = env cut times), sheathes the sword while walking on, tears the two webs with back-hand swipes of
his free right gauntlet, yanks / shoves the locked door by its iron ring, backs up, rolls his shoulders, and
charges.  The door is frontal in the tunnel's end face, so the charge is cut as (1) a tracking shot running
with him and (2) a frontal wide of the door that he slams into shoulder-first; the burst carries him into the
broken doorway (the threshold sits deeper than the tunnel floor, so he is scaled down a little there).  He
draws the sword in the settling dust and steps into the dark (handoff to S2: torch left, sword right, shield
on his back, mid-stride).

The performance is a pure function of absolute time; distances between set pieces are cheated across cuts
(each walking segment has its own x reference), feet never slide inside a shot: x is tied to the gait phase,
and the phase is pinned to the music's footfall times.
"""
from __future__ import annotations

import bisect
import json
import math
from pathlib import Path

import skia

from anim import char_anger as A
from anim import env, fx, light
from anim.core import (Camera, Track, beat, clamp, ease_in_out, ease_out, lerp, music_cue, noise1, scene_span,
                       smoothstep)
from anim.rig import ArmPose, Pose
from config import MUSIC_ENV

T0, T1 = scene_span("s1")
AR = A.ARMS
FLOOR = env.FLOOR_Y


# =========================================================================== shared helpers (also used by s2)
def cue_beats(cue):
    """Absolute beat times of a music cue (build/music/envelopes.json 'beats'), [] if unavailable."""
    try:
        d = json.loads(Path(MUSIC_ENV).read_text())[cue]
        st = music_cue(cue)["start"]
        return [round(st + b, 4) for b in d.get("beats", [])]
    except Exception:
        return []


class PhaseTrack:
    """Gait phase pinned to keys [(t, phase)] (linear between keys, constant rates outside)."""

    def __init__(self, keys, rate_before, rate_after):
        self.ts = [k[0] for k in keys]
        self.ps = [k[1] for k in keys]
        self.rb, self.ra = rate_before, rate_after

    def __call__(self, t):
        ts, ps = self.ts, self.ps
        if t <= ts[0]:
            return ps[0] - (ts[0] - t) * self.rb
        if t >= ts[-1]:
            return ps[-1] + (t - ts[-1]) * self.ra
        i = bisect.bisect_right(ts, t) - 1
        return ps[i] + (ps[i + 1] - ps[i]) * (t - ts[i]) / (ts[i + 1] - ts[i])


def gait_track(plants, ph_first, step=0.5, lead_rate=None):
    """PhaseTrack whose phase is ph_first + k*step at plants[k] (step < 0 = walking backward)."""
    keys = [(tk, ph_first + k * step) for k, tk in enumerate(plants)]
    if len(plants) > 1:
        r0 = step / (plants[1] - plants[0])
        r1 = step / (plants[-1] - plants[-2])
    else:
        r0 = r1 = step / 0.55
    return PhaseTrack(keys, lead_rate if lead_rate is not None else r0, r1)


def foot_fwd(q, side, state="walk"):
    """Forward offset (body units) of a foot in Anger's walk / run cycle at phase q (planted feet move back)."""
    if state in ("run", "charge"):
        feet = A._cycle_feet(q % 1.0, A.RUN_S, A.RUN_STANCE, 92.0, roll=46.0)
    else:
        feet = A._cycle_feet(q % 1.0, A.WALK_S, A.WALK_STANCE, 46.0)
    return feet[side][0]


# forward foot offsets of the narrow action stances (state functions in char_anger)
STANCE = {"stand": {"r": -16.0, "l": 22.0}, "chop": {"r": -34.0, "l": 26.0}, "swipe": {"r": -18.0, "l": 26.0},
          "door_push": {"r": -36.0, "l": 34.0}}


class Gaze:
    """Saccade track: keys [(t, lx, ly)] or [(t, lx, ly, dur)]: a quick move with a tiny overshoot, then hold."""

    def __init__(self, keys, dur=0.09):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.ts = [k[0] for k in self.keys]
        self.dur = dur

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2]
        i = bisect.bisect_right(self.ts, t) - 1
        k = ks[i]
        pv = ks[i - 1] if i > 0 else k
        if i > 1:      # where the previous move had actually got to (keys closer than a saccade)
            pv = (pv[0],) + self._at(i - 1, k[0])
        d = k[3] if len(k) > 3 else self.dur
        x = (t - k[0]) / d
        if x < 1.0:
            e = 1.07 * (1.0 - (1.0 - x) ** 3)
        else:
            e = 1.0 + 0.07 * (1.0 - smoothstep((x - 1.0) / 1.6))
        return lerp(pv[1], k[1], e), lerp(pv[2], k[2], e)

    def _at(self, i, t):
        k = self.keys[i]
        pv = self.keys[i - 1]
        d = k[3] if len(k) > 3 else self.dur
        x = (t - k[0]) / d
        e = 1.07 * (1.0 - (1.0 - x) ** 3) if x < 1.0 else 1.0 + 0.07 * (1.0 - smoothstep((x - 1.0) / 1.6))
        return lerp(pv[1], k[1], e), lerp(pv[2], k[2], e)


def blinks(t, times, close=0.09, hold=0.05, open_=0.2):
    """Lid multiplier 0..1 for Anger's heavy, slow blinks at the given times."""
    v = 1.0
    i = bisect.bisect_right(times, t)
    for bt in times[max(0, i - 2):i]:
        dt = t - bt
        if dt < 0:
            continue
        if dt < close:
            v = min(v, 1.0 - math.sin(dt / close * math.pi / 2))
        elif dt < close + hold:
            v = 0.0
        elif dt < close + hold + open_:
            x = (dt - close - hold) / open_
            v = min(v, 0.5 - 0.5 * math.cos(math.pi * x))
    return v


def bump(t, t0, t1, t2=None, t3=None):
    """0 -> 1 over [t0, t1], hold, 1 -> 0 over [t2, t3] (smooth)."""
    if t2 is None:
        return smoothstep((t - t0) / max(1e-6, t1 - t0))
    return smoothstep((t - t0) / max(1e-6, t1 - t0)) * (1.0 - smoothstep((t - t2) / max(1e-6, t3 - t2)))


def cam_at(px, py, zoom, sx=0.5, sy=0.5):
    """Camera that puts stage point (px, py) at screen fraction (sx, sy)."""
    return Camera(px + (0.5 - sx) * 720 / zoom, py + (0.5 - sy) * 1280 / zoom, zoom)


def mk_pose(x, y=FLOOR, scale=1.0, turn=0.45, facing=1.0, arm_l=None, arm_r=None, **extra):
    p = Pose(x=x, y=y, scale=scale, facing=facing, turn=turn,
             arm_l=arm_l if arm_l is not None else AR["torch_high"],
             arm_r=arm_r if arm_r is not None else AR["sword_low"])
    ex = dict(torch="l", sword="hand", shield="back")
    ex.update(extra)
    p.extra = ex
    return p


def sword_hilt_back(pose, t):
    """Stage point of the sheathed sword's grip over Anger's right shoulder (as char_anger draws it)."""
    R = A._solve(pose, t)
    sr = R.slot["r"]
    zb = A._tprof(10.0)[2]
    x = sr * 52.0 * R.cb - (zb + 26.0) * R.sb
    return A._mp(R.MS, A._mp(R.MC, (x, A.NECK_Y - 52.0)))


STEP_NAMES = ("armor_step", "armor_step_2", "armor_step_3")
RUN_NAMES = ("armor_step_run", "armor_step_run_2")


# =========================================================================== timing (all from named beats)
TITLE_IN, TITLE_OUT = beat("title_in"), beat("title_out")
WALK_START = beat("walk_start")
VINES = beat("vines")
CHOPS = [beat("chop1"), beat("chop2"), beat("chop3")]
CONTACT = [c + 0.083 for c in CHOPS]                 # sword_chop: blade contact 2 frames after the beat
WEBS = beat("webs")
SWIPES = [beat("web_swipe1"), beat("web_swipe2")]
DOOR_ARRIVE = beat("door_arrive")
TRIES = [beat("door_try1"), beat("door_try2")]
YANK = [b + 0.10 for b in TRIES]                     # door_locked: yank thunk +0.10, shove +0.48
SHOVE = [b + 0.48 for b in TRIES]
BACK_UP = beat("back_up")
CHARGE = beat("charge")
BURST = beat("door_burst")

_BEATS = cue_beats("descent")


def _beats(a, b, fallback):
    got = [x for x in _BEATS if a - 1e-6 <= x <= b + 1e-6]
    return got if got else fallback


# footfalls: the walk grid (taiko on every 0.55 s), then the ritardando beats as he reaches the vines
W1 = _beats(WALK_START, VINES, [WALK_START + 0.55 * k for k in range(18)])
W2 = _beats(CHOPS[2] + 0.9, WEBS, [WEBS - 0.05 - 0.5875 * k for k in (2, 1, 0)])
W3 = _beats(SWIPES[1] + 0.45, DOOR_ARRIVE, [DOOR_ARRIVE - 0.675 * k for k in (3, 2, 1, 0)])
WB = _beats(BACK_UP + 0.1, CHARGE - 0.3, [BACK_UP + 0.6 * k for k in (1, 2, 3)])
RUNP = [CHARGE + 0.31 * k for k in range(6) if CHARGE + 0.31 * k < BURST]

# ---------------------------------------------------------------- positions (stage x)
XC = 590.0                       # chop stance: the blade crosses the vine curtain (x 825..1175) around y 300
X_SW = 1900.0                    # swipe stance: the back-hand sweep crosses web A, and web B's lower half
XD = env.DOOR_RING_POS[0] - 176.0  # door stance (door_push reaches 176 forward to the ring)
X_DS = XD + 12.0                 # plain stance at the door (left foot where door_push puts it)

# walk 1: right foot plants at W1[0] (phase 0); stop on the left foot (last plant) into "stand" at XC + 4
G1 = gait_track(W1, 0.0, 0.5, lead_rate=0.5 / 0.55)
X1_STAND = XC + 4.0
X1_REF = X1_STAND + STANCE["stand"]["l"] - foot_fwd(G1.ps[-1], "l")      # x at the last plant
STOP1 = (W1[-1], W1[-1] + 0.46)


def x1(q):
    return X1_REF + (q - G1.ps[-1]) * A.WALK_ADVANCE


X_OPEN = x1(-0.4) + foot_fwd(-0.4, "l") - STANCE["stand"]["l"]     # standing spot of the opening shot
WALK1_ON = (W1[0] - 0.4 / (0.5 / 0.55), W1[0])                         # stand -> walk blend

# walk 2 (to the webs): right plants at W2[0]; stop on the right foot (last plant) into the swipe stance
G2 = gait_track(W2, 0.0, 0.5)
X2_REF = X_SW + STANCE["swipe"]["r"] - foot_fwd(G2.ps[-1], "r")
WALK2_ON = (W2[0] - 0.4 / G2.rb, W2[0])
STOP2 = (W2[-1], W2[-1] + 0.48)


def x2(q):
    return X2_REF + (q - G2.ps[-1]) * A.WALK_ADVANCE


# walk 3 (to the door): from the swipe stance, right plants first, stop on the left into the door stance
G3 = gait_track(W3, 0.0, 0.5)
WALK3_ON = (W3[0] - 0.4 / G3.rb, W3[0])
STOP3 = (W3[-1], W3[-1] + 0.46)
X3W_REF = X_SW + STANCE["swipe"]["l"] - foot_fwd(-0.4, "l")         # x at phase -0.4 (web shot)
X3D_REF = X_DS + STANCE["stand"]["l"] - foot_fwd(G3.ps[-1], "l")      # x at the last plant (door shots)

# backing up: phase decreases; touch-downs at phase = 0.1 (left) / 0.6 (right) (mod 1)
GB = gait_track(WB, 1.1, -0.5)
XB_REF = X_DS + STANCE["stand"]["l"] - foot_fwd(1.6, "l")             # x at phase 1.6 (start stance)
QB_END = GB.ps[-1] - 0.05


def xb(q):
    return XB_REF + (q - 1.6) * A.WALK_ADVANCE


# the charge: left foot plants on the first taiko (phase 0.5)
GR = gait_track(RUNP, 0.5, 0.5)
Q_IMP = GR(BURST)
X_IMP = env.DOOR_IMPACT[0] - 175.0             # his lead shoulder meets the door at DOOR_IMPACT


def xr(q):
    return X_IMP + (q - Q_IMP) * A.RUN_ADVANCE


# in the doorway after the burst
X_IN, Y_IN, S_IN = env.DOOR_X - 70.0, env.DOOR_BOTTOM + 8.0, 0.92
SETTLE = (BURST, BURST + 0.62)
REACH = (TRIES[0] - 0.62, TRIES[0] - 0.12)            # hand onto the iron ring
REL = (TRIES[1] + 0.65, TRIES[1] + 0.95)              # lets go of it
SHEATH_ANGLE = 205.0                                   # blade direction in the scabbard (deg from up)
DRAW = (BURST + 2.05, BURST + 2.45, BURST + 2.95)       # reach the hilt, sword out, down to the guard
STEP_OUT = T1                                          # first plant of S2 (right foot) on the reveal beat
STEPON = (STEP_OUT - 0.4 / (0.5 / 0.55), STEP_OUT)

# ---------------------------------------------------------------- shots (cut times)
CUT_LOW = 7.3                  # 2  low-angle profile wide
CUT_BOOTS = 10.35              # 3  boots insert on the taiko
CUT_VINES = 12.55              # 4  the vine curtain (wide), he walks up and stops
CUT_LOOKUP = VINES + 0.45      # 5  close: looks up at the vines, sword comes up
CUT_CHOP1 = CHOPS[0] - 0.2     # 6  chop 1, medium-wide low angle
CUT_CHOP2 = CONTACT[0] + 0.45  # 7  chop 2, closer (the stance resets between chops off-screen)
CUT_CHOP3 = CONTACT[1] + 0.75  # 8  chop 3, wide - the curtain falls
CUT_WEBS = CHOPS[2] + 0.67     # 9  the webs (wide): walks in, swipe 1
CUT_WEBCU = SWIPES[0] + 0.4    # 10 close: eyes flick up to web B
CUT_WEB2 = SWIPES[1] - 0.3     # 11 wide: swipe 2, walks on
CUT_DOORAPP = W3[1] + 0.05     # 12 tracking medium: the approach
CUT_DOOR = DOOR_ARRIVE         # 13 the door (frontal wide)
CUT_RING = DOOR_ARRIVE + 0.9   # 14 medium-close: eyes to the ring, the reach
CUT_TRIES = TRIES[0] - 0.05    # 15 medium: two tries, locked
CUT_FLAT = TRIES[1] + 0.78     # 16 close-up: the flat look
CUT_BACK = BACK_UP             # 17 wide side: backs up, shoulder roll, head down
CUT_RUN = CHARGE               # 18 tracking: the charge
CUT_SLAM = CHARGE + 1.05       # 19 frontal door wide: impact + burst
CUT_IN = BURST + 1.3           # 20 in the doorway: dust settles, sword drawn, steps through


# =========================================================================== door helpers
def door_state(t):
    hits = [YANK[0], SHOVE[0], YANK[1], SHOVE[1]]
    if t >= BURST:
        return "burst", t - BURST
    last = None
    for h in hits:
        if t >= h - 0.02:
            last = h
    if last is None:
        return "closed", 0.0
    return "rattle", t - (last - 0.02)


def ring_point(t):
    """Where the iron ring hangs (env's swing / door shake formulas) - the gripping hand follows it."""
    st, dt = door_state(t)
    mx, my = env.DOOR_RING_POS[0], env.DOOR_RING_POS[1] - 40
    dx = drot = 0.0
    if st == "rattle":
        e = math.exp(-dt * 2.6) * smoothstep(dt / 0.05)
        dx = math.sin(dt * math.tau * 11.0) * 4.5 * e
        drot = math.sin(dt * math.tau * 7.0 + 1.0) * 0.25 * e
        sw = math.sin(dt * 9.0) * 0.5 * math.exp(-dt * 1.4)
    else:
        sw = 0.03 * math.sin(t * 0.7)
    rx, ry = mx - math.sin(sw) * 50.0, my + math.cos(sw) * 50.0
    # door rotation about its bottom centre (degrees) + shake
    a = math.radians(drot)
    ox, oy = env.DOOR_X, env.DOOR_BOTTOM
    vx, vy = rx - ox, ry - oy
    return ox + dx + vx * math.cos(a) - vy * math.sin(a), oy + vx * math.sin(a) + vy * math.cos(a)


def door_u(t, k):
    """door_push phase for try k: pull peak (0.25) on the yank thunk, push peak (0.75) on the shove."""
    y, s = YANK[k], SHOVE[k]
    r = 0.5 / (s - y)
    if t < y:
        return clamp(0.25 - (y - t) * r * 1.0, 0.0, 1.0)
    if t < s:
        return 0.25 + (t - y) * r
    return clamp(0.75 + (t - s) * r, 0.0, 1.0)


# =========================================================================== chop / swipe phase tracks
def chop_u(t, k):
    c = CONTACT[k]
    tr = Track([(c - 0.62, 0.0, "lin"), (c - 0.2, 0.36, "lin"), (c, 0.48, "lin"), (c + 0.04, 0.5, "lin"),
                (c + 0.3, 0.72, "lin"), (c + 0.62, 1.0, "lin")])
    return tr(t)


def swipe_u(t, k):
    b = SWIPES[k]
    tr = Track([(b - 0.62, 0.0, "lin"), (b - 0.22, 0.3, "lin"), (b, 0.465, "lin"), (b + 0.06, 0.48, "lin"),
                (b + 0.32, 0.7, "lin"), (b + 0.62, 1.0, "lin")])
    return tr(t)


# =========================================================================== the performance
GAZE = Gaze([
    (0.0, 0.35, 0.3), (1.25, 0.55, -0.04), (2.62, 0.78, 0.02), (2.98, 0.52, -0.06),
    (4.7, 0.62, 0.06), (6.15, 0.85, -0.3), (6.75, 0.6, 0.0), (8.4, 0.78, 0.18), (8.9, 0.62, 0.02),
    (10.7, 0.82, -0.12), (12.35, 0.66, 0.0),
    (VINES + 0.05, 0.7, -0.55, 0.12), (VINES + 0.62, 0.55, -0.32), (CHOPS[0] - 0.42, 0.72, -0.3),
    (CHOPS[2] + 0.42, 0.6, 0.38), (CHOPS[2] + 1.1, 0.72, 0.0),
    (WEBS - 0.25, 0.78, -0.22), (SWIPES[0] - 0.4, 0.82, -0.12), (SWIPES[0] + 0.62, 0.68, -0.62, 0.12),
    (SWIPES[0] + 0.95, 0.76, -0.5), (SWIPES[1] + 0.5, 0.7, 0.0),
    (DOOR_ARRIVE + 0.12, 0.62, -0.72, 0.13), (DOOR_ARRIVE + 0.8, 0.9, 0.32, 0.13), (TRIES[0] + 0.75, 0.82, -0.05),
    (TRIES[1] - 0.25, 0.9, 0.3), (TRIES[1] + 0.95, 0.58, 0.02, 0.14), (TRIES[1] + 1.32, 0.64, -0.05),
    (BACK_UP + 0.3, 0.72, 0.0), (BACK_UP + 1.3, 0.78, -0.18), (CHARGE - 0.45, 0.82, -0.38),
    (CHARGE + 0.1, 0.85, -0.3), (BURST + 0.62, 0.7, -0.05), (BURST + 1.6, 0.92, 0.02), (DRAW[0] - 0.05, 0.6, 0.12),
    (DRAW[2] + 0.1, 0.88, 0.0),
])
BLINKS = [1.0, 2.36, 5.45, 9.25, VINES + 0.03, CHOPS[2] + 0.4, WEBS - 0.3, SWIPES[0] + 0.6, DOOR_ARRIVE + 0.1,
          TRIES[0] + 0.72, TRIES[1] + 1.15, BACK_UP + 0.95, BURST + 0.75, BURST + 1.75, DRAW[2] + 0.25]


def _face(p, t):
    """Anger's face: grim and stoic; brows/lids/mouth micro-shifts per beat, saccades, slow heavy blinks."""
    lx, ly = GAZE(t)
    p.look_x, p.look_y = lx, ly
    lid = 0.86 + 0.03 * noise1(t * 0.4, 31)
    lid -= 0.06 * bump(t, 0.0, 0.01, 1.0, 1.4)                   # heavy-lidded on the flame at first
    lid -= 0.16 * bump(t, TRIES[1] + 0.85, TRIES[1] + 1.1, BACK_UP - 0.1, BACK_UP + 0.25)   # the flat look
    lid += 0.08 * bump(t, VINES, VINES + 0.15, VINES + 0.6, VINES + 0.9)
    furrow = 0.22 + 0.04 * noise1(t * 0.3, 32)
    furrow += 0.12 * bump(t, 2.9, 3.3)
    furrow += 0.18 * bump(t, VINES + 0.4, VINES + 0.8, CHOPS[2] + 0.5, CHOPS[2] + 1.0)
    furrow += 0.12 * bump(t, TRIES[0] - 0.3, TRIES[0], TRIES[1] + 0.7, TRIES[1] + 0.9)
    furrow += 0.45 * bump(t, BACK_UP + 1.2, CHARGE - 0.2, BURST + 0.3, BURST + 1.2)
    raise_ = -0.08 * bump(t, 2.9, 3.3) + 0.12 * bump(t, VINES, VINES + 0.2, VINES + 0.5, VINES + 0.9)
    raise_ -= 0.1 * bump(t, TRIES[1] + 0.85, TRIES[1] + 1.2, BACK_UP, BACK_UP + 0.4)
    squint = 0.0
    smile = -0.1
    mo = 0.0
    grim = 0.0
    for c in CONTACT:                                      # effort on each chop + an exhale after it
        grim = max(grim, 0.55 * bump(t, c - 0.3, c - 0.05, c + 0.15, c + 0.5))
        squint = max(squint, 0.35 * bump(t, c - 0.25, c, c + 0.2, c + 0.55))
        mo = max(mo, 0.14 * bump(t, c + 0.12, c + 0.24, c + 0.45, c + 0.8))
    for b in SWIPES:
        squint = max(squint, 0.2 * bump(t, b - 0.2, b, b + 0.2, b + 0.5))
        smile = min(smile, -0.1 - 0.12 * bump(t, b - 0.5, b - 0.2, b + 0.3, b + 0.7))
    for k in range(2):
        for h in (YANK[k], SHOVE[k]):
            grim = max(grim, 0.5 * bump(t, h - 0.14, h, h + 0.12, h + 0.35))
            squint = max(squint, 0.3 * bump(t, h - 0.14, h, h + 0.12, h + 0.35))
    # charge: teeth set, squint
    grim = max(grim, 0.6 * bump(t, CHARGE - 0.05, CHARGE + 0.2, BURST + 0.1, BURST + 0.6))
    squint = max(squint, 0.4 * bump(t, CHARGE - 0.05, CHARGE + 0.2, BURST + 0.1, BURST + 0.7))
    squint = max(squint, 0.18 * bump(t, BURST + 1.2, BURST + 1.6, DRAW[0], DRAW[0] + 0.4))   # peering into the dark
    p.squint = squint
    b = blinks(t, BLINKS)
    p.lid_l = p.lid_r = clamp(lid) * b
    p.brow_furrow = clamp(furrow)
    p.brow_raise = raise_
    p.smile = smile
    p.mouth_open = mo
    p.extra["grimace"] = grim
    # tiny head adjustments
    p.head_tilt += 1.2 * noise1(t * 0.35, 33)
    p.head_nod += 0.04 * noise1(t * 0.3, 34)
    return p


def _torch_arm(t):
    """Torch hand: near the face at first, up high (far hand) from the walk on."""
    k = ease_in_out((t - 3.0) / 0.75)
    return ArmPose.blend(TORCH_OPEN, AR["torch_high"], k)


TORCH_OPEN = ArmPose(shoulder=14.0, elbow=139.0, wrist=-30.0, hand="hold", across=0.18)   # flame beside the face


TORCH_DOOR = ArmPose(shoulder=108.0, elbow=64.0, wrist=-52.0, hand="hold")    # lower: stays inside the arch


def _sword_state(t):
    """'hand' until sheathed during walk 2, 'back' until drawn in the doorway."""
    if t < SHEATHE[1] or t >= DRAW[1]:
        return "hand"
    return "back"


SHEATHE = (W2[0] + 0.15, W2[0] + 0.58, W2[0] + 1.0)     # reach the hilt, swap, hand back down


def _stop(t, g, xf, stop, side_planted, target):
    """Walk -> target stance with the planted foot fixed: returns (phase, x, mix)."""
    q = g(min(t, stop[1]))
    m = smoothstep((t - stop[0] - 0.06) / (stop[1] - stop[0] - 0.06))
    xw = xf(q)
    fw = xf(g.ps[-1]) + foot_fwd(g.ps[-1], side_planted)     # where the planted foot is
    xt = fw - STANCE[target][side_planted]
    return q, lerp(xw, xt, m), m


def _natural_sword_angle(p, t):
    """The held sword's own direction (as sword_angle: deg from up, + toward facing) for this pose."""
    ex = dict(p.extra)
    ex.pop("sword_angle", None)
    ex["sword"] = "hand"
    R = A._solve(p.copy(extra=ex), t)
    return 180.0 - R.props["sword"][1]


def _ankles_x(p, t, sides):
    R = A._solve(p, t)
    return sum(A._mp(R.MS, R.legs[sd].ankle)[0] for sd in sides) / len(sides)


def _pin(p, t, target, sides, w=1.0):
    """Shift the pose so its planted foot / feet stay at stage x `target` (cancels the action states' body
    rotation, which swings the legs about the pelvis); w blends the correction in."""
    if w <= 0.0:
        return p
    p.x += w * (target - _ankles_x(p, t, sides))
    return p


PIN_CHOP = _ankles_x(mk_pose(XC, state="chop", phase=0.0), 0.0, ("r",))
PIN_SWIPE_R = _ankles_x(mk_pose(X_SW, state="swipe", phase=0.0, sword="back", arm_r=AR["rest"]), 0.0, ("r",))
PIN_SWIPE_L = _ankles_x(mk_pose(X_SW, state="swipe", phase=0.0, sword="back", arm_r=AR["rest"]), 0.0, ("l",))
PIN_DOOR = _ankles_x(mk_pose(XD, state="door_push", phase=0.0, sword="back", arm_r=AR["rest"],
                             ring=env.DOOR_RING_POS, grip_side="r"), 0.0, ("r", "l"))


def anger_pose(t):
    p = None
    # ---------------------------------------------------------------- opening + walk 1
    if t < WALK1_ON[0]:
        p = mk_pose(X_OPEN, arm_l=_torch_arm(t), state="stand")
    elif t < STOP1[0]:
        q = G1(t)
        m = smoothstep((t - WALK1_ON[0]) / (WALK1_ON[1] - WALK1_ON[0]))
        x = lerp(X_OPEN, x1(q), m) if m < 1 else x1(q)
        p = mk_pose(x, arm_l=_torch_arm(t), state="stand", state_b="walk", mix=m, phase_b=q, phase=q)
    elif t < CUT_LOOKUP:
        q, x, m = _stop(t, G1, x1, STOP1, "l", "stand")
        p = mk_pose(x, state="walk", phase=q, state_b="stand", mix=m)
    # ---------------------------------------------------------------- the chops
    elif t < CUT_WEBS:
        if t < CONTACT[0] - 0.62:
            m = smoothstep((t - CUT_LOOKUP) / (CONTACT[0] - 0.62 - CUT_LOOKUP))
            p = mk_pose(lerp(X1_STAND, XC, m), state="stand", state_b="chop", phase_b=0.0, mix=m)
            _pin(p, t, PIN_CHOP, ("r",), m)
        else:
            k = 0
            while k < 2 and t > CONTACT[k] + 0.48:
                k += 1
            u = chop_u(t, k)
            p = mk_pose(XC, state="chop", phase=u)
            if k < 2:
                m = smoothstep((t - (CONTACT[k] + 0.48)) / 0.24)
                if m > 0:
                    p.extra.update(state_b="chop", phase_b=chop_u(t, k + 1), mix=m)
            if k > 0:
                m0 = smoothstep((t - (CONTACT[k - 1] + 0.48)) / 0.24)
                if m0 < 1:
                    p.extra.update(state="chop", phase=chop_u(t, k - 1), state_b="chop", phase_b=u, mix=m0)
            _pin(p, t, PIN_CHOP, ("r",))
    # ---------------------------------------------------------------- walk 2 + sheathe, the webs
    elif t < STOP2[0]:
        q = G2(t)
        m = smoothstep((t - WALK2_ON[0]) / (WALK2_ON[1] - WALK2_ON[0]))
        xs = x2(G2(WALK2_ON[0])) + foot_fwd(-0.4, "l") - STANCE["stand"]["l"]
        x = lerp(xs, x2(q), m)
        p = mk_pose(x, state="stand", state_b="walk", mix=m, phase_b=q, phase=q)
    elif t < SWIPES[1] - 0.62 + 0.25:
        q, x, m = _stop(t, G2, x2, STOP2, "r", "swipe")
        p = mk_pose(x, state="walk", phase=q, state_b="swipe", phase_b=swipe_u(t, 0), mix=m)
        if m >= 1.0:
            p.extra.update(state="swipe", phase=swipe_u(t, 0), state_b=None, mix=0.0)
        m2 = smoothstep((t - (SWIPES[1] - 0.62)) / 0.25)
        if m2 > 0:
            p.extra.update(state="swipe", phase=swipe_u(t, 0), state_b="swipe", phase_b=swipe_u(t, 1), mix=m2)
        _pin(p, t, PIN_SWIPE_R, ("r",), m)
    elif t < STOP3[0]:
        q = G3(t)
        xw = X3W_REF + (q + 0.4) * A.WALK_ADVANCE if t < CUT_DOORAPP else \
            X3D_REF + (q - G3.ps[-1]) * A.WALK_ADVANCE
        m = smoothstep((t - WALK3_ON[0]) / (WALK3_ON[1] - WALK3_ON[0]))
        if t < WALK3_ON[1]:
            p = mk_pose(lerp(X_SW, xw, m), state="swipe", phase=swipe_u(t, 1), state_b="walk", phase_b=q, mix=m)
            _pin(p, t, PIN_SWIPE_L, ("l",), 1.0 - smoothstep((t - (W3[0] - 0.1)) / 0.2))
        else:
            p = mk_pose(xw, state="walk", phase=q)
    # ---------------------------------------------------------------- the door
    elif t < REL[1]:
        if t < STOP3[1]:
            def xf3(q):
                return X3D_REF + (q - G3.ps[-1]) * A.WALK_ADVANCE
            q, x, m = _stop(t, G3, xf3, STOP3, "l", "stand")
            p = mk_pose(x, state="walk", phase=q, state_b="stand", mix=m)
        else:
            m = smoothstep((t - REACH[0]) / (REACH[1] - REACH[0]))
            k = 0 if t < TRIES[1] - 0.6 else 1
            u = door_u(t, k)
            rel = smoothstep((t - REL[0]) / (REL[1] - REL[0]))            # lets go of the ring
            w = m * (1.0 - rel)
            p = mk_pose(lerp(X_DS, XD, w), state="stand", state_b="door_push", phase_b=u, mix=w,
                        ring=ring_point(t), grip_side="r")
            _pin(p, t, PIN_DOOR, ("r", "l"), w)
            p.shoulders_up = 0.25 * bump(t, TRIES[1] - 0.45, TRIES[1] - 0.15, TRIES[1] + 0.1, TRIES[1] + 0.4)
    # ---------------------------------------------------------------- backing up
    elif t < CHARGE:
        if t < BACK_UP:
            # weight shifts back into the first backward step's stance (inside the close-up)
            m = smoothstep((t - REL[1]) / (BACK_UP - REL[1]))
            p = mk_pose(lerp(X_DS, xb(1.6), m), state="stand", state_b="walk", phase_b=1.6, mix=m)
        else:
            q = min(1.6, max(GB(t), QB_END))
            p = mk_pose(xb(q), state="walk", phase=q)
            # shoulder roll and the head lowers (in the braced stance)
            r0 = WB[-1] + 0.12
            p.shoulders_up = 0.75 * bump(t, r0, r0 + 0.22, r0 + 0.25, r0 + 0.5)
            p.head_tilt = -7.0 * math.sin(math.pi * clamp((t - r0) / 0.5))
            p.lean = 3.0 * math.sin(math.pi * clamp((t - r0) / 0.5)) + 6.0 * bump(t, CHARGE - 0.35, CHARGE)
            p.head_nod = -0.45 * bump(t, CHARGE - 0.42, CHARGE - 0.05)
    # ---------------------------------------------------------------- the charge
    elif t < BURST:
        q = GR(t)
        p = mk_pose(xr(q), state="charge", phase=q, lead="r", arm_r=AR["rest"])
        p.head_nod = -0.2
    # ---------------------------------------------------------------- through the door
    else:
        k = ease_out((t - SETTLE[0]) / (SETTLE[1] - SETTLE[0]))
        q = GR(min(t, BURST + 0.25))
        x = lerp(X_IMP, X_IN, k)
        y = lerp(FLOOR, Y_IN, k)
        sc = lerp(1.0, S_IN, k)
        m = smoothstep((t - BURST) / 0.55)
        straighten = smoothstep((t - BURST - 0.5) / 1.1)
        torch = ArmPose.blend(AR["run_pump"], TORCH_DOOR, smoothstep((t - BURST - 0.35) / 0.9))
        p = mk_pose(x, y=y, scale=sc, state="charge", phase=q, lead="r", state_b="stand", mix=m,
                    arm_l=torch, arm_r=AR["rest"])
        p.lean = 9.0 * (1 - straighten)
        p.head_nod = -0.3 * (1 - straighten)
        p.turn = lerp(0.45, 0.5, straighten)
        if t >= STEPON[0]:
            q2 = (t - STEP_OUT) * (0.5 / 0.55)
            ms = smoothstep((t - STEPON[0]) / (STEPON[1] - STEPON[0]))
            xw = X_IN + (STANCE["stand"]["l"] - foot_fwd(-0.4, "l") + (q2 + 0.4) * A.WALK_ADVANCE) * S_IN
            p.x = lerp(X_IN, xw, ms)
            p.extra.update(state="stand", state_b="walk", phase_b=q2, phase=q2, mix=ms)
    # ---------------------------------------------------------------- arms / props over the states
    ex = p.extra
    sw = _sword_state(t)
    ex["sword"] = sw
    if sw == "back":
        p.arm_r = AR["rest"]
    # walk 2: sheathing the sword on the move
    if SHEATHE[0] <= t < SHEATHE[2]:
        w = bump(t, SHEATHE[0], SHEATHE[1], SHEATHE[1] + 0.04, SHEATHE[2])
        p.arm_r = ArmPose.blend(AR["sword_low"], AR["rest"], smoothstep((t - SHEATHE[0]) / (SHEATHE[2] - SHEATHE[0])))
        if w > 0:
            ex["reach_r"] = sword_hilt_back(p, t)
            ex["reach_r_w"] = w
        if sw == "hand":
            k = smoothstep((t - SHEATHE[0]) / (SHEATHE[1] - SHEATHE[0]))
            ex["sword_angle"] = lerp(_natural_sword_angle(p, t), SHEATH_ANGLE, k)
    # the doorway: draws the sword
    if DRAW[0] - 0.45 <= t:
        w = bump(t, DRAW[0] - 0.45, DRAW[0], DRAW[1], DRAW[1] + 0.25)
        if w > 0:
            q = p.copy(extra=dict(ex, sword="back"))
            ex["reach_r"] = sword_hilt_back(q, t)
            ex["reach_r_w"] = w
        if t >= DRAW[1]:
            k = smoothstep((t - DRAW[1]) / (DRAW[2] - DRAW[1]))
            p.arm_r = ArmPose.blend(ArmPose(150.0, 70.0, -30.0, "hold"), AR["sword_guard"], k)
            if t > DRAW[2] + 0.15:        # lowers it as he steps through (S2 opens with the sword low)
                p.arm_r = ArmPose.blend(AR["sword_guard"], AR["sword_low"],
                                        smoothstep((t - DRAW[2] - 0.15) / 0.45))
            if k < 1.0:
                ex["sword_angle"] = lerp(SHEATH_ANGLE, _natural_sword_angle(p, t), smoothstep(k * 1.25))
        else:
            p.arm_r = AR["rest"]
    return _face(p, t)


# =========================================================================== cameras
def _hc(t):
    return A.head_center(anger_pose(t), t)


def _x_smooth(t):
    """Smooth pelvis x of the walk (no bob) for tracking cameras."""
    if t < WALK1_ON[0]:
        return X_OPEN
    if t < STOP1[0]:
        m = smoothstep((t - WALK1_ON[0]) / (WALK1_ON[1] - WALK1_ON[0]))
        return lerp(X_OPEN, x1(G1(t)), m)
    return X1_STAND


_HREF = {}


def _head_ref(t):
    """Head position at a reference time (cached) - close-ups are framed on it."""
    if t not in _HREF:
        _HREF[t] = A.head_center(anger_pose(t), t)
    return _HREF[t]


def camera(t):
    if t < CUT_LOW:
        # torch close-up -> slow pull back -> tracking with the walk
        k = ease_in_out(t / CUT_LOW)
        z = 2.3 * (0.98 / 2.3) ** k
        xs = _x_smooth(t)
        fx_ = lerp(xs + 96.0, xs + 120.0, k)
        fy_ = lerp(398.0, 600.0, k)
        return cam_at(fx_, fy_, z, 0.5, lerp(0.37, 0.5, k))
    if t < CUT_BOOTS:
        xa = _x_smooth(CUT_LOW)
        return Camera(xa + 260.0 + (_x_smooth(t) - xa) * 0.55, 730.0, 0.78)
    if t < CUT_VINES:
        return Camera(_x_smooth(t) + 40.0, 1032.0, 2.4)
    if t < CUT_LOOKUP:
        k = ease_in_out((t - CUT_VINES) / (CUT_LOOKUP - CUT_VINES))
        return Camera(lerp(690.0, 720.0, k), 650.0, lerp(0.72, 0.79, k))
    if t < CUT_CHOP1:
        h = _head_ref(CUT_LOOKUP + 0.05)
        k = ease_in_out((t - CUT_LOOKUP) / (CUT_CHOP1 - CUT_LOOKUP))
        return cam_at(h[0] + 20.0, h[1] - 25.0, lerp(2.1, 2.25, k), 0.45, 0.42)
    if t < CUT_CHOP2:
        return Camera(XC + 235.0, 650.0, 0.86)
    if t < CUT_CHOP3:
        k = ease_in_out((t - CUT_CHOP2) / (CUT_CHOP3 - CUT_CHOP2))
        return Camera(XC + 190.0, lerp(560.0, 545.0, k), lerp(1.22, 1.3, k))
    if t < CUT_WEBS:
        return Camera(XC + 320.0, 640.0, 0.7)
    if t < CUT_WEBCU:
        k = ease_in_out((t - CUT_WEBS) / (CUT_WEBCU - CUT_WEBS))
        return Camera(X_SW + lerp(40.0, 90.0, k), 620.0, 0.74)
    if t < CUT_WEB2:
        h = _head_ref(CUT_WEBCU + 0.2)
        k = ease_in_out((t - CUT_WEBCU) / (CUT_WEB2 - CUT_WEBCU))
        return cam_at(h[0] + 25.0, h[1] - 40.0, lerp(2.15, 2.25, k), 0.45, 0.45)
    if t < CUT_DOORAPP:
        k = ease_in_out((t - CUT_WEB2) / (CUT_DOORAPP - CUT_WEB2))
        return Camera(X_SW + lerp(90.0, 210.0, k), 620.0, 0.74)
    if t < CUT_DOOR:
        q = G3(t)
        xw = X3D_REF + (q - G3.ps[-1]) * A.WALK_ADVANCE
        return Camera(xw + 120.0, 560.0, 1.05)
    if t < CUT_RING:
        k = ease_in_out((t - CUT_DOOR) / (CUT_RING - CUT_DOOR))
        return Camera(3110.0, lerp(640.0, 630.0, k), lerp(0.6, 0.63, k))
    if t < CUT_TRIES:
        return cam_at(XD + 150.0, 520.0, 1.55, 0.5, 0.45)
    if t < CUT_FLAT:
        k = ease_in_out((t - CUT_TRIES) / (CUT_FLAT - CUT_TRIES))
        return Camera(lerp(3130.0, 3140.0, k), 650.0, lerp(0.92, 0.98, k))
    if t < CUT_BACK:
        h = _head_ref(CUT_FLAT + 0.3)
        k = ease_in_out((t - CUT_FLAT) / (CUT_BACK - CUT_FLAT))
        return cam_at(h[0] + 10.0, h[1] + 10.0, lerp(2.5, 2.62, k), 0.5, 0.42)
    if t < CUT_RUN:
        k = ease_in_out((t - CUT_BACK) / (CUT_RUN - CUT_BACK))
        return Camera(lerp(2960.0, 2900.0, k), 660.0, lerp(0.64, 0.7, k))
    if t < CUT_SLAM:
        xx = xr(GR(t))
        return cam_at(xx + 140.0, 560.0, 1.3, 0.5, 0.45)
    if t < CUT_IN:
        cam = Camera(3120.0, 640.0, 0.62)
        return fx.camera_shake(cam, t, [(BURST - 0.021, 38.0, 1.2), (BURST + 0.71, 10.0, 0.6)], freq=14.0, seed=3)
    k = ease_in_out((t - CUT_IN) / (T1 - CUT_IN))
    cam = Camera(lerp(3125.0, 3145.0, k), lerp(610.0, 600.0, k), lerp(1.05, 1.17, k))
    return fx.camera_shake(cam, t, [(BURST + 1.62, 6.0, 0.7)], freq=11.0, seed=5)


# =========================================================================== rendering
AMBIENT = 0.07


def _torch_radius(t):
    return lerp(230.0, light.TORCH_RADIUS, smoothstep((t - 0.2) / 4.8))


def _dust_puffs(c, t, pose):
    """Small dust puffs under the heavy footfalls (lit; drawn before the darkness)."""
    for tk in _PLANTS:
        age = t - tk[0]
        if 0 <= age < 1.4:
            fx.dust_cloud(c, t, tk[1], FLOOR + 6, age, size=0.28 * tk[2], seed=int(tk[0] * 10) % 97, n=6,
                          alpha=0.45, life=1.4, spread=0.6)


def _plant_list():
    out = []
    for i, tk in enumerate(W1):
        q = G1.ps[i]
        side = "r" if abs((q % 1.0)) < 1e-6 else "l"
        out.append((tk, x1(q) + foot_fwd(q + 0.01, side), 1.0))
    for i, tk in enumerate(W2):
        q = G2.ps[i]
        side = "r" if abs((q % 1.0)) < 1e-6 else "l"
        out.append((tk, x2(q) + foot_fwd(q + 0.01, side), 1.0))
    for i, tk in enumerate(W3):
        q = G3.ps[i]
        side = "r" if abs((q % 1.0)) < 1e-6 else "l"
        xw = X3W_REF + (q + 0.4) * A.WALK_ADVANCE if tk < CUT_DOORAPP else X3D_REF + (q - G3.ps[-1]) * A.WALK_ADVANCE
        out.append((tk, xw + foot_fwd(q + 0.01, side), 1.0))
    for i, tk in enumerate(RUNP):
        q = GR.ps[i]
        side = "r" if abs((q % 1.0)) < 1e-6 else "l"
        out.append((tk, xr(q) + foot_fwd(q + 0.01, side, "run"), 1.4))
    return out


_PLANTS = _plant_list()


_LOWRES = {}


def _lowres(c, cam, t, k, draw_fn):
    """Draw draw_fn (stage coords) into a k-scaled offscreen layer and composite it upscaled (soft FX only)."""
    w, h = int(720 * k), int(1280 * k)
    surf = _LOWRES.get((w, h))
    if surf is None:
        surf = _LOWRES[(w, h)] = skia.Surface(w, h)
    cc = surf.getCanvas()
    cc.resetMatrix()
    cc.clear(skia.ColorTRANSPARENT)
    cc.scale(k, k)
    cam.apply(cc, t)
    draw_fn(cc)
    img = surf.makeImageSnapshot()
    c.save()
    c.resetMatrix()
    c.drawImageRect(img, skia.Rect(0, 0, w, h), skia.Rect(0, 0, 720, 1280),
                    skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint())
    c.restore()


def _title(c, t):
    if t < TITLE_IN - 0.11 or t > TITLE_OUT + 0.05:
        return
    a = smoothstep((t - TITLE_IN + 0.1) / 0.18) * (1.0 - smoothstep((t - (TITLE_OUT - 0.75)) / 0.75))
    fx.draw_title(c, t, "ANGER", alpha=a)


def render(canvas, t):
    c = canvas
    pose = anger_pose(t)
    cam = camera(t)
    door, door_t = door_state(t)
    tun = dict(cut_times=tuple(CONTACT), tear_times=tuple(SWIPES), tear_dir=1.0, door=door, door_t=door_t)
    scroll = cam.cx - 360.0
    cam.apply(c, t)
    if cam.zoom >= 2.0:
        # close-ups: the set behind him at half resolution (soft background, cheaper tile fills)
        _lowres(c, cam, t, 0.5, lambda cc: env.draw_tunnel(cc, t, scroll=scroll, part="back", **tun))
    else:
        env.draw_tunnel(c, t, scroll=scroll, part="back", **tun)
    _dust_puffs(c, t, pose)
    A.draw(c, pose, t)
    if door == "burst" and door_t > 0.4:
        # the burst's front layer (dust billows, late splinters) is soft: render it at reduced resolution
        _lowres(c, cam, t, 0.5 if door_t < 1.0 and cam.zoom < 0.8 else 0.25,
                lambda cc: env.draw_tunnel(cc, t, scroll=scroll, part="front", **tun))
    else:
        env.draw_tunnel(c, t, scroll=scroll, part="front", **tun)
    c.resetMatrix()
    tp = A.torch_pos(pose, t)
    lights = []
    if tp is not None:
        lights.append(light.torch_light(tp[0], tp[1], t, radius=_torch_radius(t) * pose.scale))
    lights += env.door_lights(door, door_t)
    light.apply_darkness(c, cam, AMBIENT, lights=lights, t=t)
    c.resetMatrix()
    if door == "burst" and 0 <= door_t < 0.13:
        fx.flash(c, 0.22 * (1.0 - door_t / 0.13))
    light.vignette(c, 0.42)
    _title(c, t)


# =========================================================================== motion-locked sfx
def sfx_events():
    ev = []
    n = 0

    def step(tk, gain=-12.0):
        nonlocal n
        ev.append({"name": STEP_NAMES[n % 3], "start": round(tk, 4), "gain_db": gain})
        n += 1

    for tk in W1:
        step(tk)
    step(STOP1[1] - 0.04, -15.0)                   # the closing foot settles
    for c in CONTACT:
        step(c + 0.04, -14.0)                      # front-foot stamp of each chop
    for tk in W2:
        step(tk)
    step(STOP2[1] - 0.04, -15.0)
    ev.append({"name": "armor_shift", "start": round(SHEATHE[1] - 0.05, 4), "gain_db": -16.0})
    for tk in W3:
        step(tk)
    step(STOP3[1] - 0.04, -15.0)
    ev.append({"name": "armor_shift", "start": round(TRIES[0] - 0.55, 4), "gain_db": -17.0})
    for tk in WB:
        step(tk, -12.5)
    ev.append({"name": "armor_shift", "start": round(WB[-1] + 0.14, 4), "gain_db": -13.0})      # shoulder roll
    for i, tk in enumerate(RUNP):
        ev.append({"name": RUN_NAMES[i % 2], "start": round(tk, 4), "gain_db": -9.0})
    ev.append({"name": "armor_shift", "start": round(BURST + 0.3, 4), "gain_db": -14.0})
    ev.append({"name": "armor_step", "start": round(SETTLE[1] - 0.1, 4), "gain_db": -13.0})
    ev.append({"name": "armor_shift", "start": round(DRAW[1] - 0.05, 4), "gain_db": -15.0})
    ev.append({"name": "armor_shift", "start": round(3.05, 4), "gain_db": -19.0})                # torch comes up
    return sorted(ev, key=lambda e: e["start"])
