"""S5 - "Coda" (BIBLE section 4, S5 + section 10, REVISION 3).

Rae has gone. Quill stands alone, the holo-cards fading out above his palm; he lowers his hand and looks
into the middle distance - stillness, a robotic blink, the coda piano. The door slides open again: Rae leans
back in through the opening (upper body only, a little awkward, eyes still a bit red): "Um... thanks."
CLOSE-UP Quill: "Anytime." - a subtle nod and a slight smile, his eyes warming. She withdraws; the door shuts.
Then (no send-lights any more) he holds out his palm and four small memory bubbles from the symphony - young
Rae at the car window, the hands, the kitchen at dawn, the sunset sea - rise from where she sat and gather
above it, gently orbiting; he studies them with quiet curiosity (head tilts, his eyes moving from one to the
next, a robotic blink, a faint flicker of processing in the irises): an android learning what makes music
resonate. He turns and walks off screen to the right, still carrying them, leaving the empty lounge for a
beat. Dissolve to the stars: "IF YOU HAVE TIME" and the small line "8 symphonies sent", fade to black.

render(canvas, t) is a pure function of absolute time t. Both performances run continuously through every
cut (cuts only choose a camera). All times derive from named beats and line starts/ends in
build/timeline.json. S4's last Quill pose and card fan are read from anim.scenes.s4 at the boundary.

Shot list (absolute times only for orientation):
  1 alone      quill_alone -> rae_return_door       MEDIUM-WIDE: the cards fade one by one, the palm lowers, he
                                                    gazes into the middle distance; a robotic blink; slow push in
  2 wide_in    -> r12-0.3                           WIDE (door + Quill), cut on the whoosh: the door slides open,
                                                    Rae leans in
  3 rae_med    -> quill_nod_smile-0.2               MEDIUM Rae in the doorway: "Um... thanks."
  4 q_cu       -> rae_return_close-0.12             CLOSE-UP Quill: "Anytime." - a subtle nod, a slight smile,
                                                    warm eyes
  5 wide_out   -> quill_memories+0.12               WIDE (same set-up): she withdraws, the door shuts; a beat;
                                                    his palm starts to come up (cut on the action)
  6 mem_med    -> quill_walk_off+0.38               MEDIUM Quill (slow push): the memories rise from the bench
                                                    side and gather above his palm; he studies them; he begins
                                                    to turn away (cut on the turn)
  7 walk_wide  -> end                               MEDIUM-WIDE lounge (floor line just out of frame): he walks
                                                    off screen right carrying them; the empty lounge (window,
                                                    bench, console) holds a beat; end_card: dissolve to the
                                                    starfield, title + "8 symphonies sent" (the check mark lands
                                                    a beat later), fade to black over the last 1.5 s
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Layer, Track, auto_blink, beat, breathe, clamp, ease_in_out, ease_out, glow,
                       line_end, line_start, mouth, noise1, paint, remap, scene_span, smoothstep)
from anim.rig import ArmPose, Pose
from config import H, W

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s5")
S, E = line_start, line_end

ALONE = beat("quill_alone")
DOOR_O = beat("rae_return_door")
NOD = beat("quill_nod_smile")
DOOR_C = beat("rae_return_close")
SHUT2 = beat("door_shut2")
MEM = beat("quill_memories")
WALK = beat("quill_walk_off")
ENDC = beat("end_card")
END = beat("end")
R12, R12E = S("r12"), E("r12")
Q12, Q12E = S("q12"), E("q12")
THANKS = R12 + 0.55                   # "...thanks." (after "Um...")
ANYTIME_E = Q12 + 0.56                # (the voiced part of "Anytime." ends here; the file has a short tail)

# ---------------------------------------------------------------- cuts
CUT_WIDE_IN = DOOR_O                  # cut on the whoosh
CUT_RAE = R12 - 0.3
CUT_QCU = NOD - 0.2
CUT_WIDE_OUT = DOOR_C - 0.12
CUT_MEM = MEM + 0.12                  # cut on the action: his palm is coming up
CUT_WALK = WALK + 0.38                # cut on the turn (the facing flip happens on the cut)
DISSOLVE = 1.4                        # end_card dissolve length

# ---------------------------------------------------------------- reference geometry
QUILL_X = 545.0
FLOOR = float(env.FLOOR_Y)
RAE_X = -195.0                        # pelvis in the corridor, behind the wall left of the doorway
QA, RA = Q.ARMS, R.ARMS
LIGHT = env.char_light(1.0)
TITLE_Y = 610.0
SUB_TEXT = "8 symphonies sent ✓"

_qh = Q.head_center(Pose(x=QUILL_X, facing=-1, turn=0.35))           # ~ (522, 454)


def _cam_on(head, zoom, sx, sy):
    """Camera that puts stage point `head` at screen fraction (sx, sy)."""
    return Camera(head[0] + (0.5 - sx) * W / zoom, head[1] + (0.5 - sy) * H / zoom, zoom)


# =========================================================================== small animation helpers
class ArmSeq:
    """Keyframed ArmPose sequence: [(t, ArmPose, ease), ...] (ease = how we arrive, like Track)."""

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


def arm_add(a: ArmPose, ds=0.0, de=0.0, dw=0.0, hand=None) -> ArmPose:
    return ArmPose(a.shoulder + ds, a.elbow + de, a.wrist + dw, hand or a.hand, a.across, a.behind)


def gaze(keys, dur=0.11):
    """Saccade track. keys: [(t, (lx, ly)) or (t, (lx, ly), dur)] - eyes move there over `dur`."""
    ks = []
    prev = keys[0][1]
    ks.append((keys[0][0] - 1.0, prev))
    for k in keys:
        t, v = k[0], k[1]
        d = k[2] if len(k) > 2 else dur
        ks.append((t, prev, "lin"))
        ks.append((t + d, v, "out" if d <= 0.2 else "io"))
        prev = v
    return Track(ks)


def blink_amt(t, times):
    """0..1 lid closure from (start, duration) blinks: fast close, slower open (organic, for Rae)."""
    best = 0.0
    for b0, d in times:
        x = (t - b0) / d
        if 0.0 <= x < 1.0:
            v = math.sin(min(1.0, x / 0.38) * math.pi / 2) if x < 0.38 else math.cos((x - 0.38) / 0.62 * math.pi / 2)
            best = max(best, v)
    return best


# =========================================================================== S4 -> S5 handoff
def _s4_end():
    """Quill's head / gaze / arms and the card fan exactly as S4 leaves them at the boundary (read from S4
    itself, so the handoff stays matched if S4 is re-timed); falls back to the values S4 hands over today."""
    d = dict(hturn=0.16, nod=0.0, tilt=1.0, look=(-0.88, 0.08), brow=0.2, glow=0.18, smile=0.0,
             arm_r=QA["present"], arm_l=QA["behind_back"], card_alpha=0.82, fan=None)
    try:
        from anim.scenes import s4 as _s4
        q = _s4.quill_pose(T0)
        fs = _s4.fan_state(T0)
        d.update(hturn=q.head_turn, look=(q.look_x, q.look_y), brow=q.brow_raise, glow=q.glow, smile=q.smile,
                 arm_r=q.arm_r, arm_l=q.arm_l, card_alpha=fs["alpha"], fan=fs,
                 # S4 and S5 add the same idle noise (same seeds) on top of their tracks: strip it here
                 nod=q.head_nod - 0.012 * noise1(T0 * 0.3, 41), tilt=q.head_tilt - 0.35 * noise1(T0 * 0.25, 43))
    except Exception:                 # pragma: no cover - S4 mid-edit: keep S5 renderable
        pass
    return d


Q0 = _s4_end()

# =========================================================================== Quill: arms
PRESENT = QA["present"]
REST = QA["rest"]
BEHIND = QA["behind_back"]
# wrist trails on the way down; the hand goes palm_up -> open -> relaxed in two soft steps (no single pop)
LOWER_MID = ArmPose(shoulder=12.0, elbow=40.0, wrist=10.0, hand="open")
LIFT_MID = ArmPose(shoulder=12.0, elbow=48.0, wrist=-14.0, hand="open")          # palm turning up on the way
HOLD_MEM = ArmPose(shoulder=22.0, elbow=76.0, wrist=-8.0, hand="palm_up")        # palm out, the memories above
STUDY_MEM = ArmPose(shoulder=24.0, elbow=80.0, wrist=-10.0, hand="palm_up")      # ... brought a touch closer
CARRY_IN = ArmPose(shoulder=16.0, elbow=92.0, wrist=-6.0, hand="palm_up")        # drawn in as he turns away
CARRY = ArmPose(shoulder=18.0, elbow=80.0, wrist=-8.0, hand="palm_up")           # carried in front as he walks

HAND_DOWN0 = ALONE + 0.45             # the cards are fading: the hand comes down ...
HAND_DOWN1 = ALONE + 1.55
LIFT0 = MEM - 0.05                    # the palm comes up for the memories ...
LIFT1 = MEM + 0.62
TURN0 = WALK                          # he turns away (head and eyes lead) ...
WALK0 = CUT_WALK                      # ... and walks (from the cut, facing screen-right)

q_arm_r = ArmSeq([
    (T0, Q0["arm_r"]), (HAND_DOWN0, PRESENT),
    (HAND_DOWN0 + 0.5, LOWER_MID, "in"), (HAND_DOWN1, REST, "out"),
    (LIFT0, REST), (LIFT0 + 0.3, LIFT_MID, "in"), (LIFT1, HOLD_MEM, "out"),
    (MEM + 1.6, HOLD_MEM), (MEM + 2.6, STUDY_MEM, "io"),
    (TURN0 + 0.05, STUDY_MEM), (CUT_WALK, CARRY_IN, "io"),
    (CUT_WALK + 0.55, CARRY, "io"),
])
# the other hand stays behind his back, where S4 left it (blending it out of behind_back swings the elbow out)
q_arm_l = ArmSeq([(T0, Q0["arm_l"]), (ALONE + 0.7, BEHIND, "io")])

# =========================================================================== Quill: the walk off (facing +1)
WALK_TURN = Track([(CUT_WALK, 0.12), (CUT_WALK + 0.6, 0.58, "out")])
CADENCE = 0.92                        # walk cycles per second (calm, careful: he is carrying something)
CAD_RAMP = 0.5                        # seconds to reach full cadence after the cut
PH_W0 = 0.6                           # walk phase at the cut (feet close together under him)
SWING_KEEP = 0.25                     # how much of the rig's arm swing the carrying arm keeps


@lru_cache(maxsize=None)
def _advance_q(turn_c: int) -> float:
    """Stage units Quill's pelvis travels per walk cycle at turn = turn_c / 100 (scale 1) so the planted foot
    does not skate: the ankle's backward travel during the part of the cycle it moves backward (stance), divided
    by that fraction of the cycle (char_quill has no walk_advance of its own)."""
    turn = turn_c / 100.0
    try:
        n = 96
        xs = []
        for i in range(n):
            g = Q._layout(Pose(x=0.0, y=FLOOR, facing=1.0, turn=turn, walk=i / n))
            xs.append(g.legs[1.0][2][0])
        back = sum(max(0.0, xs[i] - xs[(i + 1) % n]) for i in range(n))
        frac = sum(1 for i in range(n) if xs[(i + 1) % n] < xs[i]) / n
        return back / max(frac, 1e-3)
    except Exception:                 # pragma: no cover - rig internals changed: analytic fallback
        yaw = math.radians(turn * Q.TURN_DEG)
        return 4.0 * 361.0 * math.sin(math.radians(17.0)) * math.sin(yaw) * 0.9


def _cadence(t):
    u = clamp((t - WALK0) / CAD_RAMP)
    return CADENCE * (0.55 + 0.45 * smoothstep(u))


_WDT = 1.0 / 240.0


@lru_cache(maxsize=1)
def _walk_table():
    """(times, phase, x) sampled every 1/240 s from the cut to the end of the scene (pure, deterministic)."""
    ts = np.arange(WALK0, T1 + 0.5, _WDT)
    ph = np.empty_like(ts)
    xs = np.empty_like(ts)
    p, x = PH_W0, QUILL_X
    for i, t in enumerate(ts):
        ph[i], xs[i] = p, x
        c = _cadence(t + 0.5 * _WDT)
        p += c * _WDT
        x += c * _advance_q(int(round(100 * WALK_TURN(t + 0.5 * _WDT)))) * _WDT
    return ts, ph, xs


def walk_phase(t):
    if t < WALK0:
        return None
    ts, ph, _ = _walk_table()
    return float(np.interp(t, ts, ph))


def quill_x(t):
    if t < WALK0:
        return QUILL_X
    ts, _, xs = _walk_table()
    return float(np.interp(t, ts, xs))


def quill_facing(t):
    return -1.0 if t < CUT_WALK else 1.0


def quill_turn(t):
    if t < TURN0:
        return 0.35
    if t < CUT_WALK:
        return 0.35 - 0.23 * ease_in_out((t - TURN0) / (CUT_WALK - TURN0))
    return WALK_TURN(t)


def _carry_arm(a: ArmPose, ph):
    """Cancel most of the rig's walk arm swing on the carrying arm (char_quill: arms swing opposite to the
    same-side leg: shoulder += 12 sin(2 pi walk) (1 - shoulder/40) for the right arm)."""
    if ph is None or a.shoulder >= 40.0:
        return a
    sw = math.sin(2.0 * math.pi * ph)
    want = a.shoulder + SWING_KEEP * 12.0 * sw * (1.0 - a.shoulder / 40.0)
    s = (want - 12.0 * sw) / (1.0 - 0.3 * sw)
    return ArmPose(s, a.elbow, a.wrist, a.hand, a.across, a.behind)


# =========================================================================== memories (from the symphony)
# kind, radius, spawn point (stage: rising from the bench side, where she sat), orbit phase (deg), birth (s after
# quill_memories). Small (r 44-56); young Rae at the car window is the biggest.
MEMS = (
    ("car_window", 56.0, (262.0, 975.0), 205.0, 0.10),
    ("hands", 47.0, (332.0, 1035.0), 295.0, 0.42),
    ("kitchen_dawn", 45.0, (196.0, 905.0), 25.0, 0.74),
    ("sea_sunset", 50.0, (392.0, 1060.0), 115.0, 1.06),
)
GATHER = 1.35                         # seconds from birth to the orbit
ORBIT_OFF = (34.0, -98.0)             # orbit centre relative to the palm (x toward his facing side = forward)
ORBIT_R = (68.0, 15.0)                # flattened ring (a slow turn around a vertical axis above the palm)
ORBIT_W = 360.0 / 12.0                # deg / s


def _anchor_raw(t):
    """The palm of a reference pose (no walk bob / swing) at time t."""
    p = Pose(x=quill_x(t), y=FLOOR, facing=quill_facing(t), turn=quill_turn(t), arm_r=q_arm_r(t), arm_l=BEHIND)
    hx, hy = Q.hand_pos(p, "r")
    f = quill_facing(t)
    return hx + f * ORBIT_OFF[0], hy + ORBIT_OFF[1]


def mem_anchor(t):
    """Orbit centre: the reference palm, followed with a soft lag (samples never straddle the facing flip)."""
    lo = CUT_WALK if t >= CUT_WALK else -1e9
    xs = ys = wsum = 0.0
    for i in range(6):
        ti = max(lo, t - i * 0.05)
        w = 1.0 - i / 7.0
        x, y = _anchor_raw(ti)
        xs += w * x
        ys += w * y
        wsum += w
    return xs / wsum, ys / wsum


def _orbit_pos(i, t, c):
    ang = math.radians(MEMS[i][3] + ORBIT_W * (t - MEM))
    x = c[0] + ORBIT_R[0] * math.cos(ang)
    y = c[1] + ORBIT_R[1] * math.sin(ang) + 3.5 * math.sin(1.25 * (t - MEM) + 1.9 * i)
    return x, y, math.sin(ang)


def memories(t):
    """[(depth, kind, x, y, r, alpha, age)] of the bubbles alive at t (stage coords), back to front."""
    if t < MEM:
        return []
    c = mem_anchor(t)
    out = []
    for i, (kind, r, sp, _, born) in enumerate(MEMS):
        age = t - (MEM + born)
        if age <= 0.0:
            continue
        ox, oy, dep = _orbit_pos(i, t, c)
        u = clamp(age / GATHER)
        e = ease_in_out(u)
        # a rising arc from the spawn point that settles into the moving orbit slot
        ctrl = (sp[0] + 30.0, sp[1] - 210.0)
        bx = (1 - e) ** 2 * sp[0] + 2 * (1 - e) * e * ctrl[0] + e * e * ox
        by = (1 - e) ** 2 * sp[1] + 2 * (1 - e) * e * ctrl[1] + e * e * oy
        rr = r * (0.62 + 0.38 * ease_out(u)) * (1.0 + 0.07 * dep * e)
        a = smoothstep(age / 0.55) * (0.88 + 0.12 * dep * e)
        out.append((dep * e, kind, bx, by, rr, a, age))
    out.sort(key=lambda m: m[0])
    return out


def mem_xy(i, t):
    """Where memory i is at t (stage) - for his gaze."""
    if t < MEM:
        return mem_anchor(t)
    kind = MEMS[i][0]
    for m in memories(t):
        if m[1] == kind:
            return m[2], m[3]
    return mem_anchor(t)


def _draw_memories(c, t, k=1.0):
    for (_, kind, x, y, r, a, age) in memories(t):
        if a * k > 0.003:
            fx.draw_memory(c, t, kind, x, y, r, alpha=a * k, age=age, glow=0.0, develop=True)


# =========================================================================== Quill: face / head
Q_DOOR = (-0.72, 0.0)                 # gaze at the door (screen-left: he faces -1)
MIDDLE = (-0.12, 0.1)                 # the middle distance
q_look_keys = gaze([
    (T0, Q0["look"]),                              # still on the door she just went through (S4)
    (ALONE + 0.5, (-0.55, 0.12), 0.35),            # ... the cards, fading
    (ALONE + 1.3, MIDDLE, 0.5),                    # into the middle distance
    (DOOR_O + 0.06, Q_DOOR, 0.08),                 # whoosh: eyes to the door
    (DOOR_O + 0.6, (-0.68, -0.02)),
    (R12 + 0.1, (-0.66, 0.0)),
    (NOD + 0.1, (-0.62, 0.04), 0.2),
    (SHUT2 + 0.1, (-0.5, 0.12), 0.2),              # the thunk: eyes drop a touch
    (MEM - 0.35, (-0.36, 0.46), 0.16),             # ... down to his palm as it comes up
], dur=0.09)

# the study: eyes jump (robotically quick) from one bubble to the next and follow it as it drifts
STUDY = [(MEM + 0.3, 0), (MEM + 1.2, 1), (MEM + 1.7, 3), (MEM + 2.2, 2), (MEM + 2.7, 0)]
STUDY_END = TURN0 + 0.02              # the eyes lead the turn to screen-right
LOOK_SCALE = (210.0, 300.0)           # stage offset from his face -> look_x / look_y


def _look_at(pt, t):
    hx, hy = Q.head_center(Pose(x=quill_x(t), y=FLOOR, facing=quill_facing(t), turn=quill_turn(t)))
    return (clamp((pt[0] - hx) / LOOK_SCALE[0], -0.95, 0.95), clamp((pt[1] - hy) / LOOK_SCALE[1], -0.9, 0.9))


def _study_target(t):
    cur = None
    prev = None
    for k, (ts, i) in enumerate(STUDY):
        if t >= ts:
            prev, cur = (STUDY[k - 1] if k > 0 else None), (ts, i)
    return prev, cur


def q_look(t):
    if t < STUDY[0][0]:
        return q_look_keys(t)
    if t < STUDY_END:
        prev, (ts, i) = _study_target(t)
        tgt = _look_at(mem_xy(i, t), t)
        u = (t - ts) / 0.09
        if u < 1.0:
            src = q_look_keys(t) if prev is None else _look_at(mem_xy(prev[1], t), t)
            e = ease_out(u)
            return src[0] + (tgt[0] - src[0]) * e, src[1] + (tgt[1] - src[1]) * e
        return tgt
    # the turn away: eyes lead to screen-right (facing -1: +x), then ahead / down at the memories as he walks
    if t < CUT_WALK:
        src = _look_at(mem_xy(0, STUDY_END), STUDY_END)
        e = ease_out((t - STUDY_END) / 0.1)
        return src[0] + (0.55 - src[0]) * e, src[1] + (0.05 - src[1]) * e
    walk_keys = _walk_look()
    return walk_keys(t)


@lru_cache(maxsize=1)
def _walk_look():
    return gaze([(CUT_WALK, (0.5, 0.06)), (CUT_WALK + 0.55, (0.34, 0.3), 0.14),     # a glance at the memories
                 (CUT_WALK + 1.1, (0.6, 0.04), 0.12)], dur=0.1)                      # ... and on, out


q_hturn = Track([
    (T0, Q0["hturn"]), (ALONE + 0.6, Q0["hturn"]), (ALONE + 1.6, 0.03, "io"),
    (DOOR_O + 0.1, 0.03), (DOOR_O + 0.45, 0.15, "out"), (DOOR_O + 0.8, 0.13, "io"),
    (NOD, 0.13), (NOD + 0.6, 0.1, "io"), (SHUT2 + 0.2, 0.1), (MEM - 0.2, 0.04, "io"),
    (MEM + 1.3, 0.02), (MEM + 1.9, 0.06, "io"), (MEM + 2.6, 0.0, "io"),
    (TURN0 - 0.04, 0.0), (CUT_WALK - 0.001, -0.3, "io"),          # facing -1: negative = toward screen-right
    (CUT_WALK, 0.08, "step"), (CUT_WALK + 0.5, 0.0, "io"),
])
q_nod = Track([
    (T0, Q0["nod"]), (ALONE + 0.5, Q0["nod"]), (ALONE + 1.2, -0.08, "io"), (ALONE + 2.2, -0.04, "io"),
    (DOOR_O + 0.1, -0.04), (DOOR_O + 0.3, 0.03, "out"), (DOOR_O + 0.8, 0.0, "io"),
    (NOD + 0.12, 0.0), (NOD + 0.5, -0.13, "io"), (NOD + 1.05, 0.01, "io"),      # "Anytime." - the subtle nod
    (SHUT2 + 0.2, 0.0), (MEM - 0.3, -0.06, "io"), (MEM + 0.8, -0.12, "io"),     # down to the palm
    (MEM + 2.0, -0.1), (MEM + 2.7, -0.13, "io"), (TURN0, -0.12),
    (CUT_WALK - 0.001, -0.04, "io"), (CUT_WALK, -0.06, "step"), (CUT_WALK + 0.6, -0.02, "io"),
    (CUT_WALK + 0.9, -0.08, "io"), (CUT_WALK + 1.4, -0.02, "io"),
])
q_tilt = Track([
    (T0, Q0["tilt"]), (ALONE + 0.5, Q0["tilt"]), (ALONE + 1.6, 2.0, "io"), (DOOR_O, 2.5),
    (DOOR_O + 0.6, 4.0, "io"), (R12E, 5.0), (NOD + 0.6, 4.0, "io"), (SHUT2, 3.0),
    (MEM + 0.6, 2.0), (MEM + 1.25, 7.0, "io"), (MEM + 1.75, 3.5, "io"), (MEM + 2.25, 5.0, "io"),
    (MEM + 2.8, 9.0, "io"),                                                    # young Rae at the car window
    (TURN0 + 0.05, 8.0), (CUT_WALK, 2.0, "io"), (CUT_WALK + 0.6, 1.0, "io"),
])
q_brow = Track([
    (T0, Q0["brow"]), (ALONE + 0.4, Q0["brow"]), (ALONE + 1.4, 0.04, "io"),
    (DOOR_O + 0.05, 0.04), (DOOR_O + 0.25, 0.22, "out"), (DOOR_O + 0.9, 0.12, "io"),
    (THANKS, 0.12), (THANKS + 0.4, 0.2, "io"), (NOD + 0.6, 0.1, "io"),
    (MEM + 0.4, 0.1), (MEM + 1.0, 0.24, "io"), (MEM + 1.8, 0.16, "io"), (MEM + 2.8, 0.28, "io"),
    (CUT_WALK + 0.3, 0.12, "io"),
])
q_glow = Track([
    (T0, Q0["glow"]), (ALONE + 1.2, 0.14, "io"), (NOD, 0.16), (NOD + 0.9, 0.42, "io"), (SHUT2 + 0.5, 0.36, "io"),
    (MEM + 0.4, 0.4), (MEM + 1.2, 0.5, "io"), (TURN0, 0.46), (ENDC, 0.4, "io"),
])
q_warm = Track([(NOD - 0.05, 0.0), (NOD + 1.0, 1.0, "io"), (MEM + 0.8, 1.0), (MEM + 1.6, 0.75, "io")])
q_process = Track([(MEM + 1.0, 0.0), (MEM + 1.5, 0.3, "io"), (MEM + 2.3, 0.22), (MEM + 2.9, 0.0, "io")])
q_smile = Track([(T0, Q0["smile"]), (ALONE + 0.5, 0.0), (NOD + 0.3, 0.0), (NOD + 1.05, 0.3, "io"),
                 (SHUT2 + 0.4, 0.22, "io"), (MEM + 1.0, 0.1, "io"), (MEM + 2.9, 0.16, "io")])
q_squint = Track([(NOD + 0.3, 0.0), (NOD + 1.05, 0.12, "io"), (SHUT2 + 0.4, 0.06, "io")])
q_lid = Track([(T0, 1.0), (ALONE + 1.0, 1.0), (ALONE + 1.6, 0.95, "io"), (DOOR_O, 0.95), (DOOR_O + 0.2, 1.0, "io"),
               (NOD + 0.3, 1.0), (NOD + 1.05, 0.93, "io"), (MEM - 0.3, 0.93), (MEM + 0.4, 0.9, "io")])


def q_blink(t):
    """Robotic: perfectly periodic, both lids identical, on the same clock as S1-S4 (seed 0, every 4.6 s)."""
    return 1.0 - auto_blink(t, seed=0, rate=4.6, robotic=True)


def quill_pose(t: float) -> Pose:
    mo, mr = mouth("quill", t)
    lx, ly = q_look(t)
    # micro saccades so held gazes stay alive (tiny; he is precise)
    lx += 0.012 * noise1(t * 1.3, 51)
    ly += 0.01 * noise1(t * 1.1, 53)
    lid = q_lid(t) * (1.0 - q_blink(t))
    ph = walk_phase(t)
    return Pose(
        x=quill_x(t), y=FLOOR, facing=quill_facing(t), turn=quill_turn(t), walk=ph,
        lean=0.0 if ph is None else 1.5 * smoothstep((t - WALK0) / 0.6),
        head_turn=q_hturn(t), head_nod=q_nod(t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=q_tilt(t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly,
        brow_raise=q_brow(t), smile=q_smile(t), squint=q_squint(t),
        mouth_open=0.9 * mo, mouth_round=mr, glow=q_glow(t), process=q_process(t),
        arm_r=_carry_arm(q_arm_r(t), ph), arm_l=q_arm_l(t), **LIGHT,
    )


def quill_visible(t):
    """Off screen right (with his memories) a little after the walk: the empty lounge holds."""
    return quill_x(t) < 1000.0


# =========================================================================== Rae (leaning back in through the door)
LEAN_IN0 = DOOR_O + 0.2               # she starts leaning in while the panel is still sliding
LEAN_IN1 = DOOR_O + 0.62
OUT0 = DOOR_C - 0.05                  # she pulls back out as the panel starts to slide
OUT1 = DOOR_C + 0.36

r_lean = Track([
    (T0, 0.0), (LEAN_IN0, 0.0), (LEAN_IN1, 28.5, "out"), (LEAN_IN1 + 0.3, 26.5, "io"), (R12, 27.0, "io"),
    (R12 + 0.25, 25.5, "io"), (THANKS, 27.5, "io"), (THANKS + 0.5, 28.2, "io"), (NOD, 27.6, "io"),
    (OUT0, 27.4), (OUT1, 0.0, "in"),
])
r_tilt = Track([
    (T0, 0.0), (LEAN_IN0, 0.0), (LEAN_IN0 + 0.2, 2.0, "io"), (LEAN_IN1 + 0.15, -12.0, "out"),   # head lags the lean
    (LEAN_IN1 + 0.45, -9.5, "io"), (R12, -10.0), (R12 + 0.35, -13.0, "io"),                     # "Um..."
    (THANKS, -9.0, "io"), (THANKS + 0.6, -11.0, "io"), (OUT0, -10.5), (OUT1, -4.0, "io"),
])
r_nod = Track([
    (T0, 0.0), (LEAN_IN1, 0.05), (R12 - 0.05, 0.05), (R12 + 0.3, 0.16, "io"),                 # "Um..." eyes down
    (THANKS - 0.05, 0.1, "io"), (THANKS + 0.15, -0.06, "out"), (THANKS + 0.5, 0.04, "io"),   # "...thanks." small nod
    (R12E + 0.3, 0.06, "io"), (ANYTIME_E, 0.06), (ANYTIME_E + 0.3, 0.0, "io"),
])
r_shoulders = Track([(T0, 0.3), (R12, 0.32), (R12 + 0.3, 0.42, "io"), (THANKS + 0.4, 0.3, "io"), (OUT1, 0.4)])

MUG_HUG_R = ArmPose(shoulder=16.0, elbow=118.0, wrist=0.0, hand="hold", across=0.48)    # mug held to her chest
R_FAR = ArmPose(shoulder=18.0, elbow=118.0, wrist=14.0, hand="open", across=0.85)   # far hand cupping the mug too

RAE_BLINKS = [(LEAN_IN1 + 0.2, 0.2), (THANKS - 0.12, 0.2), (ANYTIME_E + 0.1, 0.22)]
R_AT_Q = (0.62, -0.48)                # up at Quill's face (she is leaning low in the doorway)
r_look = gaze([
    (T0, R_AT_Q),
    (R12 - 0.05, (0.3, 0.22), 0.14),                # "Um..." - eyes drop away
    (THANKS - 0.05, R_AT_Q, 0.12),                  # "...thanks." - up to him
    (NOD + 0.4, (0.58, -0.44), 0.08),
    (OUT0 + 0.05, (0.36, 0.1), 0.12),               # and away again as she goes
])
r_lid = Track([(T0, 0.84), (R12, 0.84), (R12 + 0.3, 0.72, "io"), (THANKS, 0.86, "io"), (OUT0, 0.84),
               (OUT0 + 0.2, 0.76, "io")])
r_worry = Track([(T0, 0.5), (R12 + 0.3, 0.62, "io"), (THANKS + 0.3, 0.45, "io"), (OUT1, 0.45)])
r_brow_raise = Track([(T0, 0.22), (LEAN_IN1, 0.3), (R12 + 0.3, 0.22, "io"), (THANKS, 0.34, "io"), (OUT1, 0.25)])
r_smile = Track([(T0, 0.0), (LEAN_IN1, 0.04), (R12 + 0.2, 0.06), (THANKS + 0.2, 0.16, "io"), (R12E + 0.2, 0.22, "io"),
                 (ANYTIME_E, 0.22), (ANYTIME_E + 0.4, 0.28, "io"), (OUT0, 0.26)])
r_mouth_x = Track([(T0, 0.04), (R12 - 0.05, 0.02, "io"), (R12E, 0.0), (R12E + 0.3, 0.03, "io")])


def rae_pose(t: float) -> Pose:
    lx, ly = r_look(t)
    lx += 0.025 * noise1(t * 1.5, 9)
    ly += 0.018 * noise1(t * 1.3, 13)
    lid = r_lid(t) * (1.0 - blink_amt(t, RAE_BLINKS))
    mo, mr = mouth("rae", t)
    return Pose(
        x=RAE_X, y=env.FLOOR_Y, facing=1.0, turn=0.3, lean=r_lean(t),
        head_tilt=r_tilt(t) + 1.0 * noise1(t * 0.5, 5), head_nod=r_nod(t) + 0.025 * noise1(t * 0.45, 3),
        breath=breathe(t, 0.3, 2),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly, squint=0.1,
        brow_raise=r_brow_raise(t), brow_worry=r_worry(t),
        mouth_open=r_mouth_x(t) + 0.75 * mo, mouth_round=mr, smile=r_smile(t), mouth_tremble=0.1,
        tears=0.42, sniffle=0.55, pupil=1.06, blush=0.32, eye_shine=0.35, shoulders_up=r_shoulders(t),
        arm_r=MUG_HUG_R, arm_l=R_FAR, mug="r", **LIGHT,
    )


def rae_visible(t):
    return DOOR_O < t < OUT1 + 0.05


# =========================================================================== door
door = Track([(T0, 0.0), (DOOR_O, 0.0), (DOOR_O + 0.55, 1.0, "out"), (DOOR_C, 1.0), (SHUT2, 0.0, "in")])


def _door_clip_rect(d):
    """Stage rect of the (partly) open door panel still covering the doorway: Rae is behind it."""
    return skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(d), env.FLOOR_Y + 4)


# =========================================================================== holo cards (left over from S4)
CARD_FADE = 1.5                       # the whole fan is gone 1.5 s into the scene
CARD_STAGGER = 0.09                   # No. 1 (farthest from his palm) goes first, No. 8 last


def _card_alphas(t):
    out = {}
    base = Q0["fan"]["alphas"] if Q0["fan"] else {}
    dur = CARD_FADE - 7 * CARD_STAGGER
    for n in range(1, 9):
        k = 1.0 - smoothstep((t - (T0 + CARD_STAGGER * (n - 1))) / dur)
        out[n] = base.get(n, 1.0) * k
    return out


def _draw_cards(canvas, t):
    if t > T0 + CARD_FADE + 0.05:
        return
    from anim.scenes import s3
    fs = Q0["fan"]
    al = _card_alphas(t)
    # a slow lift as they dissolve (holograms powering down)
    canvas.save()
    canvas.translate(0.0, -10.0 * smoothstep((t - T0) / CARD_FADE))
    s3.draw_fan(canvas, t, 1.0, alpha=Q0["card_alpha"], alphas=al,
                states=fs["states"] if fs else None, focus=fs["focus"] if fs else None,
                pops=fs["pops"] if fs else None)
    canvas.restore()


# =========================================================================== cameras
MED_WIDE_A = _cam_on(_qh, 1.42, 0.79, 0.31)       # Quill right third, the fading fan / empty room to the left
MED_WIDE_B = _cam_on(_qh, 1.58, 0.7, 0.32)
WIDE_DOOR = Camera(196.0, 684.0, 0.8)
RAE_MED_A = Camera(-46.0, 700.0, 2.1)
RAE_MED_B = Camera(-44.0, 698.0, 2.16)
CU_A = _cam_on((_qh[0] + 6, _qh[1] + 6), 3.2, 0.52, 0.42)
CU_B = _cam_on((_qh[0] + 6, _qh[1] + 6), 3.38, 0.52, 0.42)
OUT_A = Camera(206.0, 680.0, 0.8)                 # the door shuts (same set-up as wide_in)
MEM_A = Camera(428.0, 652.0, 1.6)                 # his face upper third, the palm + memories, the bench side
MEM_B = Camera(440.0, 626.0, 1.76)
# the lounge (window, the empty bench, the console); he exits right. The floor line sits just below the frame:
# char_quill's walk cycle sets the swinging foot down before the end of its swing (it would visibly slide
# forward on the floor), so his feet stay out of shot - thighs and shins carry the walk.
WALK_A = Camera(446.0, 548.0, 1.24)
WALK_B = Camera(441.0, 545.0, 1.26)


def _drift(a: Camera, b: Camera, t, t0, t1, ease=smoothstep):
    return Camera.lerp(a, b, ease(clamp((t - t0) / (t1 - t0))))


def shot(t):
    if t < CUT_WIDE_IN:
        return "alone"
    if t < CUT_RAE:
        return "wide_in"
    if t < CUT_QCU:
        return "rae_med"
    if t < CUT_WIDE_OUT:
        return "q_cu"
    if t < CUT_MEM:
        return "wide_out"
    if t < CUT_WALK:
        return "mem_med"
    return "walk_wide"


def camera(t: float) -> Camera:
    s = shot(t)
    if s == "alone":
        return _drift(MED_WIDE_A, MED_WIDE_B, t, T0, CUT_WIDE_IN)
    if s == "wide_in":
        return WIDE_DOOR
    if s == "rae_med":
        return _drift(RAE_MED_A, RAE_MED_B, t, CUT_RAE, CUT_QCU)
    if s == "q_cu":
        return _drift(CU_A, CU_B, t, CUT_QCU, CUT_WIDE_OUT)
    if s == "wide_out":
        return OUT_A
    if s == "mem_med":
        return _drift(MEM_A, MEM_B, t, CUT_MEM, CUT_WALK, ease_in_out)
    return _drift(WALK_A, WALK_B, t, CUT_WALK, ENDC + DISSOLVE)


# =========================================================================== render
def _draw_stage(canvas, t, cam, qp, rp, d):
    canvas.save()
    cam.apply(canvas, t)
    env.draw_lounge(canvas, t, light=1.0, door=d)
    if rp is not None:
        canvas.save()
        canvas.clipRect(_door_clip_rect(d), skia.ClipOp.kDifference, True)
        canvas.clipRect(skia.Rect(env.DOOR_X1, -2000, 4000, 4000), skia.ClipOp.kDifference, True)
        R.draw(canvas, rp, t)
        canvas.restore()
    if qp is not None:
        Q.draw(canvas, qp, t, warm=q_warm(t))
    env.draw_lounge_front(canvas, t, light=1.0, door=d)
    _draw_cards(canvas, t)
    _draw_memories(canvas, t)
    canvas.restore()


def _end_card(canvas, t):
    """Screen-space starfield (under the dissolving stage)."""
    env.draw_space(canvas, t, drift=0.55, brightness=1.0)


def render(canvas, t):
    cam = camera(t)
    qp = quill_pose(t) if quill_visible(t) else None
    rp = rae_pose(t) if rae_visible(t) else None
    d = door(t)
    diss = smoothstep(remap(t, ENDC, ENDC + DISSOLVE))
    if diss <= 0.0:
        _draw_stage(canvas, t, cam, qp, rp, d)
    else:
        _end_card(canvas, t)
        if diss < 0.999:
            with Layer(canvas, alpha=1.0 - diss):
                _draw_stage(canvas, t, cam, qp, rp, d)
    canvas.resetMatrix()
    # title + the little line (its check mark lands a beat later: "delivered"), then fade to black
    ta = smoothstep(remap(t, TITLE_IN0, TITLE_IN1))
    sa = smoothstep(remap(t, SUB_IN0, SUB_IN1))
    if ta > 0.003:
        _title(canvas, t, ta, sa)
    fb = smoothstep(remap(t, END - 1.5, END))
    if fb > 0.003:
        canvas.drawRect(skia.Rect(0, 0, W, H), paint("#000000", fb, aa=False))


# =========================================================================== end-card title
TITLE_SIZE, SUB_SIZE = 44.0, 20.0
# the title comes back as the dissolve settles, the line follows, the check mark lands a beat after the
# words - leaving ~2 s of the finished card before the fade to black
TITLE_IN0, TITLE_IN1 = ENDC + 0.7, ENDC + 2.2
SUB_IN0, SUB_IN1 = ENDC + 2.3, ENDC + 3.2
CHECK_T = ENDC + 3.5
check_a = Track([(CHECK_T, 0.0), (CHECK_T + 0.18, 1.0, "out")])
_CHECK = None


def _check_box():
    """Screen rect + centre of the trailing check mark, using fx.draw_title's sub-line layout."""
    global _CHECK
    if _CHECK is None:
        from anim.core import font
        f = font(SUB_SIZE, "Inter Display", 300)
        tr = SUB_SIZE * 0.12
        ws = [f.measureText(ch) for ch in SUB_TEXT]
        total = sum(ws) + tr * (len(SUB_TEXT) - 1)
        x0 = W / 2 - total / 2 + sum(ws[:-1]) + tr * (len(SUB_TEXT) - 1)
        base = TITLE_Y + TITLE_SIZE * 0.95 + SUB_SIZE * 0.4
        rect = skia.Rect(x0 - 3.0, base - SUB_SIZE * 1.15, x0 + ws[-1] + 7.0, base + 7.0)
        _CHECK = (rect, (x0 + ws[-1] * 0.5, base - SUB_SIZE * 0.35))
    return _CHECK


def _title(canvas, t, ta, sa):
    rect, (cx, cy) = _check_box()
    ca = check_a(t)

    def draw(sub_alpha):
        fx.draw_title(canvas, t, "IF YOU HAVE TIME", TITLE_Y, alpha=ta, size=TITLE_SIZE, sub=SUB_TEXT,
                      sub_alpha=sub_alpha, rise=8, sub_size=SUB_SIZE)

    canvas.save()
    canvas.clipRect(rect, skia.ClipOp.kDifference, True)
    draw(sa)
    canvas.restore()
    if ca > 0.003:
        canvas.save()
        canvas.clipRect(rect, skia.ClipOp.kIntersect, True)
        draw(sa * ca)
        canvas.restore()
        pulse = math.exp(-(t - CHECK_T) / 0.35) * min(1.0, (t - CHECK_T) / 0.08)
        if pulse > 0.01:
            glow(canvas, cx, cy, 30.0, "#7FFFE9", 0.45 * pulse)
