"""S1 - "The ask" (BIBLE section 4, S1: 11 shots).

Rae shuffles in after a 14-hour shift, flops onto the bench and - almost as an afterthought - asks
Quill for a symphony "if you ever have time". He composes it in 0.4 s.

render(canvas, t) is a pure function of absolute time t. Both performances (rae_pose / quill_pose)
run continuously through every cut, so cuts never pop an action; each shot only chooses a camera.
All times are derived from named beats / line starts / SFX placements in build/timeline.json.

Staging note: Rae sits at x 230, Quill stands at x 545. In this side-by-side portrait staging a
zoom-1.5 single would clip the other character at the frame edge, so the Rae singles use zoom 1.8-1.9
(left edge x >= 62 keeps the door's teal edge light out of frame, right edge < Quill's nearest point at
x ~478) and the Quill singles zoom 1.8 / 2.4-2.55 / 2.8 (left edge clear of Rae, bottom above her lap).
Shot 10 gets a 0.7 s reaction close-up of Rae between q04 and q05 (the flat stare is the joke).
"""
from __future__ import annotations

import math

import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Track, auto_blink, beat, breathe, clamp, ease_in_out, glow, line_end, line_start,
                       mouth, noise1, scene_span, smoothstep, timeline)
from anim.rig import ArmPose, Pose

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s1")


def _sfx(name):
    for s in timeline()["sfx"]:
        if s["name"] == name and T0 - 1e-6 <= s["start"] < T1:
            return s["start"]
    raise KeyError(name)


DOOR_OPEN = beat("rae_door_open")
ENTERS = beat("rae_enters")
SITS = beat("rae_sits")
QTURN = beat("quill_turns")
SIP1 = beat("rae_sip1")
QPROC = beat("quill_process_start")
SIP2 = beat("rae_sip2")
DONE = beat("quill_done_chime")
FREEZE = beat("rae_freeze")

FOOT = _sfx("footsteps_4")            # heel strikes inside the SFX file at +0.00 / +0.62 / +1.30 / +1.95
STRIKES = [FOOT + o for o in (0.0, 0.62, 1.30, 1.95)]
DOOR_SHUT = _sfx("door_close")        # panel slides, thunk at +0.67
IMPACT = _sfx("bench_sit")            # bum hits the cushion
SIGH = _sfx("sigh_breath")            # inhale at +0.2, exhale peak at +0.56
SIP_SND = _sfx("sip")                 # slurp +0.2 .. +0.6

S, E = line_start, line_end

# ---------------------------------------------------------------- shot list (cut times)
CUT_R01 = SITS + 0.6                  # 2  medium Rae: "Ugh. Long shift."
CUT_QTURN = QTURN                     # 3  medium Quill: turn (cut on the turn) + q01
CUT_R02 = E("q01") + 0.15             # 4  medium Rae: r02, lazy mug point
CUT_SIP1 = SIP1 - 0.2                 # 5  two-shot: sip, both look at the stars
CUT_PUSH = S("r03") - 0.1             # 6  slow push-in on Rae r03-r05
CUT_QCU = E("r05") + 0.13             # 7  close-up Quill: "Certainly." + processing
CUT_SIP2 = SIP2 - 0.1                 # 8  two-shot: sip, done chime, "Done."
CUT_FREEZE = FREEZE - 0.04            # 9  close-up Rae: frozen mid-sip, r06, r07
CUT_DEADPAN = E("r07") + 0.2          # 10 medium close-up Quill: q04 deadpan
CUT_REACT = E("q04") - 0.12           # 10b close-up Rae: flat stare (on his last word "...time.")
CUT_Q05 = S("q05") - 0.06             # 10c medium close-up Quill: q05 "Would you like to hear it?"
CUT_TOAST = E("q05") + 0.35           # 11 medium Rae: r08 skeptical toast -> S2

# ---------------------------------------------------------------- reference geometry
RAE_X, QUILL_X, QUILL_X0 = 230.0, 545.0, 560.0
SEAT_Y = env.BENCH_SEAT_Y
A, QA = R.ARMS, Q.ARMS
BB = QA["behind_back"]
LIGHT = env.char_light(1.0)           # matches what the room / S2 use at light 1

_rh = R.head_center(Pose(x=RAE_X, facing=1, turn=0.35, sit=1.0, seat_y=SEAT_Y))       # ~ (258, 714)
_qh = Q.head_center(Pose(x=QUILL_X, facing=-1, turn=0.35))                           # ~ (522, 454)


def _cam_on(head, zoom, sx, sy):
    """Camera that puts stage point `head` at screen fraction (sx, sy)."""
    return Camera(head[0] + (0.5 - sx) * 720 / zoom, head[1] + (0.5 - sy) * 1280 / zoom, zoom)


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


def arm_add(a: ArmPose, ds=0.0, de=0.0, dw=0.0) -> ArmPose:
    return ArmPose(a.shoulder + ds, a.elbow + de, a.wrist + dw, a.hand, a.across, a.behind)


def gaze(keys, dur=0.11):
    """Saccade track. keys: [(t, (lx, ly)) or (t, (lx, ly), dur)] - eyes snap there over `dur` (fast out)."""
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
    """0..1 closure from a list of (start, duration) blinks: fast close, slower open."""
    best = 0.0
    for b0, d in times:
        x = (t - b0) / d
        if 0.0 <= x < 1.0:
            v = math.sin(min(1.0, x / 0.38) * math.pi / 2) if x < 0.38 else math.cos((x - 0.38) / 0.62 * math.pi / 2)
            best = max(best, v)
    return best


# =========================================================================== Rae: walk-in
# Four tired steps land on the four footsteps_4 heel strikes; a fifth, silent step follows and she pivots on it
# as she drops onto the bench. The pelvis x is SOLVED from the rig's own leg geometry so the planted foot never skates:
# while a foot is planted, x(t) = anchor - (that ankle's offset from the pelvis). Seated feet sit ~117 units in
# front of the pelvis at turn 0.35, more than four steps can cover from the doorway, so she sits facing the room
# (turn T_SIT, feet nearly under her knees) and then swivels toward Quill, swinging her legs round.
STEP5 = STRIKES[3] + 0.38                                    # silent last step lands
SIT_START = STEP5 - 0.04                                     # knees start to give as it lands
SIT_DONE = IMPACT - 0.02
PH_END = 2.22                                                # back foot still closing in as she lands
T_SIT = 0.15                                                 # pivots on the planted foot toward the room as she drops
SWIVEL = (IMPACT + 0.1, IMPACT + 0.95)                       # legs swing round toward Quill


def _herm(t, t0, t1, p0, p1, m0, m1):
    h = t1 - t0
    u = clamp((t - t0) / h)
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * h * m0 + (-2 * u3 + 3 * u2) * p1
            + (u3 - u2) * h * m1)


def walk_phase(t):
    """Heel strikes (foot lp = 0) land on the footstep SFX at phase 0, .5, 1, 1.5; the pivot step lands at 2.0."""
    s0, s1_, s2, s3 = STRIKES
    if t <= s0:
        return (t - s0) * 0.5 / (s1_ - s0)
    if t <= s1_:
        return 0.5 * (t - s0) / (s1_ - s0)
    if t <= s2:
        return 0.5 + 0.5 * (t - s1_) / (s2 - s1_)
    if t <= s3:
        return 1.0 + 0.5 * (t - s2) / (s3 - s2)
    m_in = 0.5 / (s3 - s2)
    m_mid = (PH_END - 1.5) / (SIT_DONE - s3)
    if t <= STEP5:
        return _herm(t, s3, STEP5, 1.5, 2.0, m_in, m_mid)
    return _herm(min(t, SIT_DONE), STEP5, SIT_DONE, 2.0, PH_END, m_mid, 0.0)


def _sit_ease(u):
    """knees give (slow), then gravity takes over into the cushion."""
    u = clamp(u)
    return 0.16 * smoothstep(u / 0.4) if u < 0.4 else 0.16 + 0.84 * ((u - 0.4) / 0.6) ** 2


def r_sit(t):
    return _sit_ease((t - SIT_START) / (SIT_DONE - SIT_START)) if t < SIT_DONE else 1.0


r_turn = Track([(T0, 0.45), (STEP5 - 0.02, 0.45), (SIT_DONE - 0.04, T_SIT, "io"), (SWIVEL[0], T_SIT),
                (SWIVEL[1], 0.35, "io")])


def _leg_pose(t):
    return Pose(x=0.0, y=env.FLOOR_Y, facing=1.0, turn=r_turn(t), sit=r_sit(t), seat_y=SEAT_Y,
                walk=walk_phase(t) if t < SIT_DONE else None)


def _ankle_dx(t, o):
    """Stage x of ankle o (-1 near, +1 far) relative to the pelvis, straight from the rig's leg solve."""
    L = R._solve(_leg_pose(t), None).legs[o]
    return L.ankle[0]


def _planted(ph):
    return -1 if (ph % 1.0) < 0.5 else 1


def _phase_time(ph):
    lo, hi = T0 - 2.0, SIT_DONE
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if walk_phase(mid) < ph:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _build_walk():
    """Anchors per planted-foot segment: [(t_start, foot, anchor_x)], shifted so the seated pelvis is at RAE_X."""
    ph0 = walk_phase(T0 - 1.0)
    k = math.floor(ph0 / 0.5) + 1
    segs = [(-1e9, _planted(ph0), 0.0)]
    while k * 0.5 <= walk_phase(SIT_DONE - 1e-4) + 1e-9:
        te = _phase_time(k * 0.5)
        _, o_prev, a_prev = segs[-1]
        x = a_prev - _ankle_dx(te, o_prev)
        o_new = _planted(k * 0.5 + 1e-6)
        segs.append((te, o_new, x + _ankle_dx(te, o_new)))
        k += 1
    _, o_l, a_l = segs[-1]
    shift = RAE_X - (a_l - _ankle_dx(SIT_DONE - 1e-6, o_l))
    return [(ts, o, a + shift) for ts, o, a in segs]


WALK_SEGS = _build_walk()


def walk_x(t):
    if t >= SIT_DONE:
        return RAE_X
    for ts, o, a in reversed(WALK_SEGS):
        if t >= ts:
            return a - _ankle_dx(t, o)
    return RAE_X


# =========================================================================== Rae: performance tracks
HOLD = A["hold_mug"]
SIP = A["sip"]
RAISE = A["mug_raise"]
MUGPOINT = ArmPose(shoulder=38.0, elbow=60.0, wrist=-8.0, hand="hold", across=0.0)    # lazy "you" with the mug
REST = A["rest"]
SHRUG_L = ArmPose(shoulder=16.0, elbow=64.0, wrist=-14.0, hand="palm_up", across=0.0)    # lazy "meh": palm flips up on her thigh
LAP_L = ArmPose(shoulder=15.0, elbow=55.0, wrist=0.0, hand="relaxed")     # far hand resting on her thigh

# freeze: time warp that stops all idle motion while Rae is frozen mid-sip
FRZ_END = FREEZE + 1.38            # thaw: the mug starts to come down


def warp(t):
    """Idle-motion clock: stops dead in the freeze, then quietly catches up with real time by the end of the
    scene (breathing ~10 % faster for a while) so the S2 handoff breathes in phase."""
    if t < FREEZE:
        return t
    if t < FRZ_END:
        return FREEZE
    return t - (FRZ_END - FREEZE) * (1.0 - smoothstep((t - FRZ_END) / (T1 - 0.4 - FRZ_END)))



r_bounce = Track([
    (SIT_DONE, 0.0), (IMPACT + 0.07, 10.0, "out"), (IMPACT + 0.24, -2.5, "io"), (IMPACT + 0.42, 1.0, "io"),
    (IMPACT + 0.6, 0.0, "io"),
    # tiny settle as she leans in on r07, and a bob on "Okay."
    (S("r08") + 0.5, 0.0), (S("r08") + 0.62, 2.0, "out"), (S("r08") + 0.85, 0.0, "io"),
])

r_lean = Track([
    (T0, 4.0), (SIT_DONE, 4.0), (IMPACT + 0.12, 9.0, "out"), (IMPACT + 0.45, 2.0, "io"),
    (SIGH + 0.3, 1.0), (SIGH + 0.75, -8.5, "io"), (S("r01") + 0.25, -7.0, "io"), (S("r01") + 0.5, -7.2),
    (E("r01"), -1.0, "io"),
    (E("r01") + 0.6, 0.0, "io"),
    (S("r02"), 0.0), (S("r02") + 0.4, 2.5, "io"), (S("r02") + 1.7, 2.0), (S("r02") + 2.3, 0.0, "io"),
    (S("r04") + 3.3, 0.0), (S("r04") + 3.8, 2.0, "io"), (E("r04") + 0.6, 0.5, "io"),
    (E("r06") + 0.3, 0.5), (S("r07") - 0.05, 3.0, "io"), (S("r07") + 0.45, 10.0, "io"), (E("r07") + 0.3, 9.0),
    (S("q04") + 2.3, 9.0), (S("q04") + 3.6, 2.0, "io"),
    (CUT_TOAST, 1.0), (S("r08") + 0.1, 0.0, "io"), (S("r08") + 1.0, 2.5, "io"), (T1, 2.0, "io"),
])

r_shoulders = Track([
    (T0, 0.0), (SIGH + 0.05, 0.0), (SIGH + 0.4, 0.32, "io"), (SIGH + 0.95, 0.0, "io"),
    (S("r05") + 0.95, 0.0), (S("r05") + 1.15, 0.22, "out"), (S("r05") + 1.55, 0.0, "io"),        # "I don't know"
    (S("r08") - 0.1, 0.0), (S("r08") + 0.12, 0.5, "out"), (S("r08") + 0.5, 0.08, "io"), (S("r08") + 0.9, 0.0, "io"),
])

r_nod = Track([
    (T0, -0.28), (SIT_DONE, -0.22), (IMPACT + 0.12, -0.5, "out"), (IMPACT + 0.4, -0.2, "io"),
    (SIGH + 0.05, -0.2), (SIGH + 0.35, -0.1, "io"), (SIGH + 0.75, 0.86, "io"),                # head lolls back on the sigh
    (S("r01") + 0.22, 0.78, "io"), (S("r01") + 0.45, 0.8, "io"), (S("r01") + 1.0, 0.18, "io"),  # forward on "Long shift"
    (S("q01") + 1.0, 0.18), (S("q01") + 1.6, 0.1, "io"),
    (S("r02") + 1.5, 0.1), (S("r02") + 1.85, 0.42, "io"), (S("r02") + 2.45, 0.12, "io"),       # eye roll lifts the chin
    # head follows the eyes: stars ~ +0.5 (chin up), Quill ~ +0.12, lowered ~ -0.24
    (SIP1 - 0.42, 0.12), (SIP1 - 0.02, 0.48, "io"), (SIP_SND + 0.6, 0.54, "io"), (SIP_SND + 1.1, 0.46, "io"),
    (S("r03") - 0.02, 0.46), (S("r03") + 0.24, 0.16, "io"), (S("r03") + 0.46, 0.16),          # "Hey..." to Quill
    (S("r03") + 0.9, 0.5, "io"),                                                               # "...random thought."
    (S("r04") + 1.25, 0.47), (S("r04") + 1.65, 0.1, "io"), (S("r04") + 2.25, 0.12),          # dips on "seriously"
    (S("r04") + 2.75, 0.44, "io"), (S("r04") + 3.1, 0.44), (S("r04") + 3.55, 0.1, "io"),     # "...could you write me"
    (S("r04") + 4.1, 0.15, "io"), (E("r04") + 0.3, 0.15), (E("r04") + 0.75, 0.5, "io"),      # "symphony?" -> stars
    (S("r05") + 0.3, 0.55, "io"), (S("r05") + 1.0, 0.5, "io"), (S("r05") + 1.3, 0.38, "io"),  # searching; "I don't know"
    (S("r05") + 2.45, 0.36), (S("r05") + 3.35, -0.22, "io"),                                   # "Feeling really small"
    (E("r05") + 0.8, -0.26), (SIP2 + 0.4, 0.15, "io"),
    (FREEZE + 0.01, 0.15),                                                                  # (frozen: warp holds)
    (FRZ_END, 0.15), (S("r06") + 0.1, 0.0, "io"),
    (S("r07") + 0.62, 0.02), (S("r07") + 0.7, -0.38, "out"), (S("r07") + 0.98, 0.02, "io"),  # emphatic nod on HAD
    (E("r07") + 0.3, 0.0), (S("q04") + 0.5, 0.05, "io"),
    (S("r08") + 0.48, 0.05), (S("r08") + 0.6, -0.14, "out"), (S("r08") + 0.85, 0.06, "io"),   # nod on "Okay."
    (S("r08") + 1.2, 0.1, "io"), (T1, 0.1),
])

r_tilt = Track([
    (T0, 2.0), (SIGH + 0.3, 1.0), (SIGH + 0.8, -7.0, "io"), (S("r01") + 0.5, -7.0), (S("r01") + 1.1, -3.0, "io"),
    (S("r02") + 0.2, -2.0, "io"), (S("r02") + 1.6, -1.0), (S("r02") + 2.0, 3.0, "io"), (E("r02") + 0.3, 0.0, "io"),
    (S("r03") + 0.3, -2.5, "io"), (S("r04") + 1.3, -2.5), (S("r04") + 2.0, 1.5, "io"), (S("r04") + 3.4, 2.0),
    (S("r04") + 3.9, 4.0, "io"), (E("r04") + 0.5, 1.0, "io"),
    (S("r05") + 1.0, -1.0, "io"), (S("r05") + 1.5, -4.0, "io"), (S("r05") + 3.0, -3.0), (E("r05"), -1.5, "io"),
    (FREEZE, 0.0, "io"), (FRZ_END, 0.0), (S("r06") + 0.05, -5.0, "io"), (S("r07") - 0.1, -4.0),
    (S("r07") + 0.4, 1.0, "io"), (E("r07") + 0.4, 0.0, "io"),
    (S("q05") + 0.3, 0.0), (S("q05") + 1.0, -2.0, "io"),
    (S("r08") - 0.05, -2.0), (S("r08") + 0.2, -6.0, "out"), (S("r08") + 0.6, -3.0, "io"), (S("r08") + 1.0, -3.0),
    (S("r08") + 1.3, -3.5, "io"), (T1, -3.0, "io"),
])

r_hturn = Track([          # (- = head back toward the window / camera, + = toward Quill)
    (T0, 0.0), (SIP1 - 0.42, 0.0), (SIP1, -0.05, "io"),
    (S("r03") - 0.02, -0.05), (S("r03") + 0.24, 0.03, "io"), (S("r03") + 0.46, 0.03), (S("r03") + 0.9, -0.05, "io"),
    (S("r04") + 1.3, -0.05), (S("r04") + 1.46, 0.0, "io"), (S("r04") + 1.63, -0.09, "io"),    # small head shake:
    (S("r04") + 1.8, -0.02, "io"), (S("r04") + 1.98, -0.04, "io"),                             # "no rush, seriously"
    (S("r04") + 3.1, -0.05), (S("r04") + 3.55, 0.06, "io"), (E("r04") + 0.3, 0.06), (E("r04") + 0.75, -0.05, "io"),
    (S("r05") + 2.45, -0.05), (S("r05") + 3.35, 0.0, "io"),
    (S("r07") - 0.1, 0.0), (S("r07") + 0.4, 0.05, "io"), (E("r07") + 0.6, 0.0, "io"),
])

# eyes: half-lidded tired -> soft/wistful -> frozen -> skeptical
r_lid = Track([
    (T0, 0.46), (IMPACT - 0.05, 0.46), (IMPACT + 0.05, 0.22, "out"), (IMPACT + 0.35, 0.48, "io"),
    (SIGH + 0.15, 0.48), (SIGH + 0.45, 0.0, "io"), (S("r01") + 0.52, 0.0), (S("r01") + 0.85, 0.42, "io"),
    (E("r01") + 0.4, 0.46), (S("r02") + 0.3, 0.5, "io"),
    (S("r02") + 1.36, 0.5), (S("r02") + 1.52, 0.84, "io"), (S("r02") + 2.2, 0.8),             # lids open for the eye roll
    (S("r02") + 2.55, 0.52, "io"),
    (SIP1 - 0.42, 0.52), (SIP1 - 0.05, 0.88, "io"), (SIP_SND + 0.2, 0.8, "io"),             # stars: lids open
    (S("r03"), 0.88, "io"), (S("r03") + 0.2, 0.72, "io"), (S("r03") + 0.5, 0.72), (S("r03") + 0.9, 0.9, "io"),
    (S("r04") + 1.3, 0.9), (S("r04") + 1.65, 0.6, "io"), (S("r04") + 2.3, 0.62), (S("r04") + 2.75, 0.88, "io"),
    (S("r04") + 3.1, 0.88), (S("r04") + 3.45, 0.74, "io"), (S("r04") + 3.8, 0.74), (S("r04") + 4.15, 0.84, "io"),
    (E("r04") + 0.6, 0.9, "io"), (S("r05") + 2.45, 0.88), (S("r05") + 3.35, 0.58, "io"),
    (SIP2, 0.55), (SIP2 + 0.4, 0.62, "io"),
    (FREEZE + 0.25, 0.62), (FREEZE + 0.8, 0.8, "io"),                                    # realisation widens them
    (S("r06") - 0.1, 0.8), (S("r06") + 0.15, 0.9, "io"), (S("r07"), 0.92), (S("r07") + 0.65, 1.0, "io"),
    (E("r07") + 0.3, 0.95), (S("q04") + 2.5, 0.92), (S("q04") + 3.8, 0.78, "io"),
    (S("r08") - 0.4, 0.74), (S("r08") + 1.0, 0.72, "io"), (T1, 0.72),
])

RAE_BLINKS = [
    (STRIKES[0] + 0.25, 0.28), (STRIKES[2] + 0.2, 0.3),
    (E("r01") - 0.14, 0.2), (S("q01") + 1.1, 0.18), (S("q01") + 2.9, 0.2),
    (S("r02") + 0.22, 0.38),                                   # slow, unimpressed blink on "Don't count"
    (S("r02") + 2.2, 0.2),                                     # closes the eye roll on "...real"
    (SIP1 - 0.42, 0.17),                                       # head turns to the stars
    (S("r03") + 0.42, 0.17), (S("r04") + 0.95, 0.18), (S("r04") + 2.6, 0.18), (S("r04") + 3.18, 0.17),
    (E("r04") + 0.32, 0.18), (S("r05") + 1.5, 0.18), (S("r05") + 2.62, 0.36),
    (SIP2 - 0.02, 0.18),
    (FREEZE + 1.0, 0.45),                                      # the one slow blink inside the freeze
    (E("r06") + 0.35, 0.17), (S("q04") + 0.55, 0.18), (S("q04") + 2.5, 0.18),
    (E("q04") + 0.12, 0.36),                                   # slow, flat blink in her reaction close-up
    (S("r08") + 0.45, 0.16), (S("r08") + 1.7, 0.18),
]

# gaze (screen space): +x toward Quill, -y up. Stars = up and a little back toward the window centre.
STARS = (-0.18, -1.0)
QUILL = (0.62, -0.36)
ROLL_T = (S("r02") + 1.52, S("r02") + 2.16)                           # "It makes them real." - eye roll
ROLL = [QUILL, (0.36, -1.0), (-0.12, -1.0), (-0.45, -0.78), (0.45, -0.35)]
r_look = gaze([
    (T0, (0.1, 0.42)),
    (STRIKES[1] + 0.2, (0.25, 0.48)), (STRIKES[3] - 0.1, (0.3, 0.55)),    # eyes on the bench as she arrives
    (IMPACT + 0.3, (0.05, 0.2)),
    (S("r01") + 0.75, (0.45, -0.25), 0.2), (E("r01") - 0.12, QUILL),
    (S("q01") + 1.5, (0.6, -0.33)), (S("q01") + 3.3, QUILL),
    (ROLL_T[1] - 0.02, ROLL[-1], 0.01),                                   # (eye roll path overrides before this)
    (SIP1 - 0.44, STARS, 0.2),                                            # breaks off to the stars (cut follows)
    (S("r03") + 0.05, (0.58, -0.4)), (S("r03") + 0.45, STARS),           # "Hey..." glance, back to the stars
    (S("r04") + 0.9, (-0.04, -0.94)),
    (S("r04") + 1.6, (0.22, 0.16), 0.16),                                # dips on "seriously"
    (S("r04") + 2.5, (-0.12, -0.96), 0.18),                              # "whenever"
    (S("r04") + 3.15, QUILL),                                            # "could you write me a symphony?"
    (E("r04") + 0.3, STARS),
    (S("r05") + 0.25, (-0.02, -0.98)), (S("r05") + 0.55, (-0.32, -0.86)),  # searching the stars
    (S("r05") + 1.0, (-0.12, -0.98)), (S("r05") + 1.6, (0.04, -0.72), 0.3),
    (S("r05") + 2.65, (0.22, 0.32), 0.45),                              # "Feeling really small" - eyes lower
    (E("r05") + 0.5, (0.3, 0.42)),
    (SIP2 - 0.02, (0.1, -0.5)),
    (FREEZE + 0.26, (0.9, -0.3), 0.62),                                 # only the eyes slide toward Quill
    (S("r06") + 0.3, QUILL),
    (S("r07") + 0.1, (0.66, -0.32)),
    (S("q04") + 1.4, (0.55, -0.4)), (S("q04") + 2.6, QUILL),
    (S("r08") + 0.3, (0.5, -0.5)), (S("r08") + 0.8, QUILL),
])


def _catmull(pts, u):
    """Point on a Catmull-Rom curve through pts at u in 0..1 (uniform segments)."""
    n = len(pts) - 1
    f = clamp(u) * n
    i = min(int(f), n - 1)
    a = f - i
    p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
    p3 = pts[min(i + 2, n)]
    return tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * a + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * a * a
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * a ** 3) for k in range(2))


def rae_look(t):
    if ROLL_T[0] <= t < ROLL_T[1]:
        return _catmull(ROLL, smoothstep((t - ROLL_T[0]) / (ROLL_T[1] - ROLL_T[0])))
    return r_look(t)


r_smile = Track([
    (T0, -0.12), (SIGH + 0.4, -0.25, "io"), (E("r01"), -0.2), (E("r01") + 0.4, -0.08, "io"),
    (S("r02") - 0.1, -0.05), (S("r02") + 0.3, 0.28, "io"), (S("r02") + 1.6, 0.26), (S("r02") + 2.0, 0.12, "io"),
    (SIP1 + 1.4, 0.12), (S("r03"), 0.14, "io"), (S("r04") + 1.25, 0.1),
    (S("r04") + 1.6, 0.36, "io"), (S("r04") + 2.9, 0.3), (S("r04") + 3.4, 0.16, "io"),
    (S("r05"), 0.08, "io"), (S("r05") + 2.6, 0.05), (S("r05") + 3.4, -0.06, "io"),
    (SIP2, 0.0, "io"), (FRZ_END, 0.0), (S("r06"), -0.15, "io"), (S("r07"), -0.1),
    (S("q04") + 2.5, -0.1), (S("q04") + 3.8, 0.0, "io"),
    (CUT_TOAST, 0.0), (S("r08"), 0.08, "io"), (S("r08") + 1.0, 0.1, "io"), (T1, 0.1),
])
r_smirk = Track([
    (T0, 0.0), (S("r02") + 0.3, 0.18, "io"), (S("r02") + 2.0, 0.05, "io"),
    (S("r04") + 1.6, 0.22, "io"), (S("r04") + 3.0, 0.05, "io"), (S("r05"), 0.0, "io"),
    (S("q05") + 1.0, 0.0), (CUT_TOAST + 0.35, 0.35, "io"), (S("r08") + 0.5, 0.42, "io"),
    (S("r08") + 0.8, 0.5), (S("r08") + 1.2, 0.7, "io"), (T1, 0.7),
])
r_brow_raise = Track([
    (T0, -0.15), (SIGH + 0.3, -0.05), (S("r01") + 0.2, 0.1, "io"), (E("r01"), -0.15, "io"),
    (S("q01") + 2.0, -0.1), (S("q01") + 2.4, 0.15, "io"), (E("q01"), 0.0, "io"),                  # "fourteen hours"
    (S("r02") + 0.4, 0.15, "io"), (S("r02") + 1.5, 0.05), (S("r02") + 1.75, 0.3, "io"), (E("r02"), 0.05, "io"),
    (SIP1 + 1.0, 0.12, "io"), (S("r04"), 0.12), (S("r04") + 0.5, 0.25, "io"), (S("r04") + 1.2, 0.15, "io"),
    (S("r04") + 3.5, 0.18), (S("r04") + 4.1, 0.42, "io"), (E("r04") + 0.6, 0.15, "io"),           # "...symphony?"
    (S("r05"), 0.2), (S("r05") + 2.6, 0.12), (S("r05") + 3.4, 0.05, "io"),
    (SIP2, 0.0), (FREEZE + 0.3, 0.0), (FREEZE + 0.9, 0.16, "io"),
    (FRZ_END, 0.16), (S("r06") + 0.05, 0.45, "out"), (S("r07"), 0.4), (S("r07") + 0.65, 0.6, "io"),
    (E("r07") + 0.3, 0.45, "io"), (S("q04") + 2.5, 0.4), (S("q04") + 3.8, 0.1, "io"),
    (CUT_TOAST, 0.05), (S("r08"), 0.32, "io"), (S("r08") + 0.6, 0.15, "io"), (T1, 0.1),
])
r_brow_worry = Track([
    (T0, 0.22), (SIGH + 0.4, 0.3, "io"), (E("r01"), 0.15, "io"), (S("r02"), 0.05, "io"),
    (SIP1 + 0.8, 0.15, "io"), (S("r04") + 1.3, 0.15), (S("r04") + 1.6, 0.25, "io"), (S("r04") + 2.8, 0.12, "io"),
    (S("r05"), 0.2, "io"), (S("r05") + 2.6, 0.22), (S("r05") + 3.4, 0.42, "io"), (E("r05") + 0.8, 0.35),
    (SIP2 + 0.5, 0.1, "io"), (FREEZE, 0.1), (FRZ_END, 0.1), (S("r06"), 0.0, "io"),
])
r_brow_furrow = Track([
    (T0, 0.0), (SIGH + 0.4, 0.22, "io"), (E("r01"), 0.0, "io"),
    (FRZ_END, 0.0), (S("r06") + 0.05, 0.5, "out"), (S("r07"), 0.42), (S("r07") + 0.65, 0.5, "io"),
    (E("r07") + 0.4, 0.38, "io"), (S("q04") + 2.5, 0.35), (S("q04") + 3.8, 0.12, "io"),
    (CUT_TOAST, 0.15), (S("r08") + 0.3, 0.05, "io"), (S("r08") + 1.2, 0.2, "io"), (T1, 0.2),
])
r_eye_wide = Track([(T0, 0.0), (S("r07") + 0.55, 0.0), (S("r07") + 0.7, 0.28, "out"), (E("r07") + 0.5, 0.0, "io")])
r_mouth_x = Track([       # breath / jaw extras on top of lip-sync
    (T0, 0.05), (IMPACT, 0.05), (IMPACT + 0.08, 0.18, "out"), (IMPACT + 0.4, 0.04, "io"),
    (SIGH + 0.15, 0.04), (SIGH + 0.35, 0.16, "io"), (SIGH + 0.75, 0.1, "io"), (S("r01"), 0.0, "io"),
    (E("r01"), 0.0), (E("r01") + 0.3, 0.04, "io"), (S("r02"), 0.0),
    (SIP1, 0.0), (FREEZE, 0.0), (FRZ_END, 0.0),
    (E("r06"), 0.0), (E("r06") + 0.15, 0.1, "io"), (S("r07") - 0.05, 0.0, "io"),        # lips stay parted after "What?"
    (E("r07"), 0.0), (E("r07") + 0.2, 0.06, "io"), (S("q04") + 1.0, 0.0, "io"),
])

# right arm (mug hand) and left arm
_mp = MUGPOINT
r_arm_r = ArmSeq([
    (T0, HOLD), (S("r02") + 0.05, HOLD), (S("r02") + 0.5, _mp, "io"),
    (S("r02") + 0.95, arm_add(_mp, 3, -6)), (S("r02") + 1.12, arm_add(_mp, -2, 4), "io"),       # waggle on "Quill"
    (S("r02") + 1.3, arm_add(_mp, 1, -3), "io"), (S("r02") + 1.5, _mp, "io"),
    (S("r02") + 1.7, _mp), (S("r02") + 2.35, HOLD, "io"),
    (SIP1, HOLD), (SIP1 + 0.42, SIP, "io"), (SIP_SND + 0.62, SIP), (SIP_SND + 1.15, HOLD, "io"),
    (SIP2, HOLD), (SIP2 + 0.42, SIP, "io"),
    (FRZ_END, SIP), (FRZ_END + 0.42, HOLD, "io"),
    (S("r08") + 0.72, HOLD), (S("r08") + 1.2, RAISE, "out"),
])
r_arm_l = ArmSeq([          # far arm: swings on the walk, then rests on her far thigh; comes up for the shrug on "Sure."
    (T0, REST), (SIT_START, REST), (IMPACT + 0.3, LAP_L, "io"),
    (S("r08") - 0.16, LAP_L), (S("r08") + 0.14, SHRUG_L, "out"),
    (S("r08") + 0.5, SHRUG_L), (S("r08") + 0.95, LAP_L, "io"),
])
# overlapping action on the mug arm when she lands, and while walking (mug sways a hair)
r_arm_lag = Track([(SIT_DONE, 0.0), (IMPACT + 0.1, 9.0, "out"), (IMPACT + 0.32, -3.0, "io"), (IMPACT + 0.55, 0.0, "io")])


def rae_pose(t: float) -> Pose:
    tw = warp(t)                         # idle-motion clock (stops during the freeze)
    sit = r_sit(t)
    walking = sit < 0.999
    if walking:
        x = walk_x(t)
        ph = walk_phase(t)
    else:
        x, ph = RAE_X, None
    # head micro-motion (restrained, organic)
    idle = 1.0 if sit > 0.99 else 0.4
    nod = r_nod(t) + idle * 0.035 * noise1(tw * 0.45, 3)
    tilt = r_tilt(t) + idle * 1.3 * noise1(tw * 0.38, 5)
    if walking:
        tilt += 1.6 * math.sin(2 * math.pi * (ph or 0.0))          # weary sway with the gait
    lid = r_lid(t) * (1.0 - blink_amt(t, RAE_BLINKS))
    lx, ly = rae_look(t)
    # micro saccades: tiny eye drift so held gazes stay alive (frozen during the freeze)
    lx += 0.025 * noise1(tw * 1.7, 9)
    ly += 0.02 * noise1(tw * 1.5, 13)
    mo, mr = mouth("rae", t)
    arm_r = r_arm_r(t)
    lag = r_arm_lag(t)
    if lag:
        arm_r = arm_add(arm_r, ds=-lag * 0.5, de=lag)
    if walking and t < SIT_START:
        arm_r = arm_add(arm_r, ds=1.5 * math.sin(2 * math.pi * (ph or 0.0) + 0.6))
    return Pose(
        x=x, y=env.FLOOR_Y, facing=1.0, turn=r_turn(t), sit=sit, seat_y=SEAT_Y, walk=ph,
        lean=r_lean(t), head_tilt=tilt, head_nod=nod, head_turn=r_hturn(t),
        breath=breathe(tw, 0.2, 2),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly, squint=0.06 + 0.12 * max(0.0, r_smile(t)),
        eye_wide=r_eye_wide(t),
        brow_raise=r_brow_raise(t), brow_worry=r_brow_worry(t), brow_furrow=r_brow_furrow(t),
        mouth_open=r_mouth_x(t) + 0.8 * mo, mouth_round=mr, smile=r_smile(t), smirk=r_smirk(t),
        shoulders_up=r_shoulders(t), bounce=r_bounce(t),
        arm_r=arm_r, arm_l=r_arm_l(t), mug="r", **LIGHT,
    )


# =========================================================================== Quill: performance tracks
TURN_START = QTURN - 0.19
# the rig eases yaw with smoothstep over back 0.75..0.25, so a linear ramp over that band = one smooth turn
TURN_DUR = 1.1
q_back = Track([(T0, 1.0), (TURN_START - 0.01, 1.0), (TURN_START, 0.75, "step"), (TURN_START + TURN_DUR, 0.25, "lin"),
                (TURN_START + TURN_DUR + 0.01, 0.0, "step")])
q_hturn = Track([
    (T0, 0.0), (DOOR_OPEN + 0.12, 0.0), (DOOR_OPEN + 0.62, 0.27, "io"),        # hears the door: glance over the shoulder
    (STRIKES[3], 0.27), (IMPACT + 0.25, 0.04, "io"),                            # ...and back to the stars as she sits
    (TURN_START - 0.15, 0.0), (TURN_START + 0.3, 0.2, "io"), (TURN_START + 0.75, 0.0, "io"),   # head leads the turn
    (TURN_START + 1.05, 0.03, "io"), (TURN_START + 1.5, 0.0, "io"),
    (SIP1 - 0.05, 0.0), (SIP1 + 0.6, 0.1, "io"), (S("r04") + 3.3, 0.1), (S("r04") + 3.8, 0.0, "io"),
])
q_nod = Track([
    (T0, 0.12), (TURN_START, 0.12), (TURN_START + 1.0, 0.0, "io"),
    (S("q01") + 1.6, 0.0), (S("q01") + 1.9, -0.06, "io"), (S("q01") + 2.4, 0.0, "io"),
    (SIP1 - 0.05, 0.0), (SIP1 + 0.6, 0.28, "io"), (S("r04") + 3.3, 0.28), (S("r04") + 3.8, 0.0, "io"),
    (QPROC + 0.1, 0.0), (QPROC + 0.5, 0.06, "io"),
    (DONE - 0.05, 0.06), (DONE + 0.15, -0.08, "out"), (DONE + 0.5, 0.0, "io"),             # "complete" tick
    (S("q03") + 0.05, 0.0), (S("q03") + 0.2, -0.05, "io"), (S("q03") + 0.5, 0.0, "io"),
    (S("q04") + 0.05, 0.0), (S("q04") + 0.2, -0.1, "io"), (S("q04") + 0.5, 0.0, "io"),       # "I did."
    (S("q05"), 0.0), (S("q05") + 0.4, 0.04, "io"), (T1, 0.0, "io"),
])
q_tilt = Track([
    (T0, 0.0), (S("q01") + 3.3, 0.0), (S("q01") + 3.75, 7.0, "io"), (E("q01") + 0.8, 7.0),
    (E("q01") + 1.8, 1.0, "io"),
    (S("q04") + 2.5, 1.0), (S("q04") + 3.2, 3.0, "io"),
    (S("q05") - 0.12, 3.0), (S("q05") + 0.42, 10.0, "io"), (E("q05") + 1.2, 10.0), (T1 - 0.4, 3.0, "io"),
])
q_look = gaze([
    (T0, (0.0, -0.2)),
    (TURN_START + 0.35, (-0.42, 0.22), 0.16),
    (SIP1 - 0.08, (-0.42, -0.5)),                    # to the window/stars with Rae
    (S("r04") + 3.15, (-0.42, 0.22)),
    (QPROC + 0.08, (-0.12, -0.08), 0.3),             # unfocus while composing
    (DONE + 0.02, (-0.42, 0.22)),
    (S("q04") + 1.0, (-0.38, 0.25)), (S("q04") + 2.4, (-0.45, 0.22)),
], dur=0.09)
q_brow = Track([
    (T0, 0.0), (S("q01") + 1.55, 0.0), (S("q01") + 1.8, 0.14, "io"), (S("q01") + 3.0, 0.08, "io"),
    (E("q01") + 0.5, 0.0, "io"),
    (CUT_QCU + 0.2, 0.0), (CUT_QCU + 0.45, 0.12, "io"), (QPROC + 0.6, 0.08, "io"), (DONE, 0.1),
    (DONE + 0.15, 0.2, "out"), (E("q03") + 0.4, 0.06, "io"),
    (S("q04") + 0.7, 0.06), (S("q04") + 1.0, 0.26, "io"), (S("q04") + 1.7, 0.06, "io"),      # "four TENTHS"
    (S("q05") + 0.15, 0.05), (S("q05") + 0.55, 0.32, "io"), (E("q05") + 1.4, 0.28), (T1, 0.05, "io"),
])
q_process = Track([(QPROC - 0.02, 0.0), (QPROC + 0.42, 1.0, "io"), (DONE - 0.5, 1.0), (DONE - 0.04, 0.0, "io")])
q_glow = Track([
    (T0, 0.12), (QPROC, 0.12), (QPROC + 0.42, 0.75, "io"), (DONE - 0.5, 0.7), (DONE - 0.04, 0.35, "io"),
    (DONE + 0.05, 1.0, "out"), (DONE + 0.6, 0.22, "io"), (E("q03") + 1.0, 0.12, "io"), (T1, 0.102),
])
q_lid = Track([(T0, 1.0), (S("q04") - 0.1, 1.0), (S("q04") + 0.3, 0.88, "io"), (E("q05") + 0.6, 0.88),
               (T1 - 0.3, 1.0, "io")])
q_smile = Track([(T0, 0.0), (S("q03") - 0.05, 0.0), (S("q03") + 0.2, 0.1, "io"), (E("q03") + 0.8, 0.0, "io"),
                 (S("q05") + 0.4, 0.0), (S("q05") + 0.9, 0.06, "io")])


def quill_pose(t: float) -> Pose:
    x = QUILL_X0 if t < CUT_R01 else QUILL_X          # 15-unit cheat while he is off screen (shot 2)
    mo, mr = mouth("quill", t)
    lid = q_lid(t)
    lid = None if lid > 0.999 else lid * auto_blink(t, seed=0, rate=4.6, robotic=True)   # keep his periodic blink
    lx, ly = q_look(t)
    return Pose(
        x=x, y=env.FLOOR_Y, facing=-1.0, turn=0.35, back=q_back(t),
        head_turn=q_hturn(t), head_nod=q_nod(t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=q_tilt(t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly, brow_raise=q_brow(t), smile=q_smile(t),
        mouth_open=0.9 * mo, mouth_round=mr, glow=q_glow(t), process=q_process(t),
        arm_r=BB, arm_l=BB, **LIGHT,
    )


# =========================================================================== door
door = Track([(T0, 0.0), (DOOR_OPEN, 0.0), (DOOR_OPEN + 0.55, 1.0, "out"),
              (DOOR_SHUT, 1.0), (DOOR_SHUT + 0.67, 0.0, "in")])


# =========================================================================== cameras
WIDE_A = Camera(296, 684, 0.72)
WIDE_B = Camera(300, 694, 0.755)
# Rae singles: left frame edge >= x 62 (keeps the door's teal edge light at x 40-56 out of frame), right edge
# < x 478 (Quill's nearest point), so they cannot be wider than zoom ~1.75.
RAE_MED = Camera(62 + 360 / 1.9, _rh[1] + (0.5 - 0.33) * 1280 / 1.9, 1.9)    # head ~(0.52, 0.33), shoes in frame
QUILL_MED = _cam_on(_qh, 1.8, 0.44, 0.36)                  # left frame edge ~ x 346, bottom above Rae's lap
TWO = Camera(412, 792, 1.0)                                # left edge x 52: door edge light out of frame
PUSH_A = Camera(64 + 360 / 1.8, _rh[1] + (0.5 - 0.36) * 1280 / 1.8, 1.8)    # opens on her whole figure
PUSH_B = _cam_on((_rh[0], _rh[1] - 4), 2.3, 0.5, 0.41)
QUILL_CU = _cam_on(_qh, 2.8, 0.55, 0.42)                   # looking room on the left (he faces Rae)
DEADPAN_A = _cam_on(_qh, 2.4, 0.54, 0.38)
DEADPAN_B = _cam_on(_qh, 2.55, 0.54, 0.385)
RAE_TOAST = Camera(62 + 360 / 1.8, _rh[1] + (0.5 - 0.34) * 1280 / 1.8, 1.8)    # a touch wider: room for the shrug
RAE_CU = _cam_on((_rh[0] + 4, _rh[1] + 8), 2.5, 0.46, 0.42)
RAE_REACT = _cam_on((_rh[0] + 6, _rh[1] + 4), 2.45, 0.46, 0.4)


def _drift(a: Camera, b: Camera, t, t0, t1, ease=ease_in_out):
    return Camera.lerp(a, b, ease(clamp((t - t0) / (t1 - t0))))


def _nudge(cam: Camera, dx=0.0, dy=0.0, dz=1.0):
    return Camera(cam.cx + dx, cam.cy + dy, cam.zoom * dz)


def camera(t: float) -> Camera:
    if t < CUT_R01:                                       # 1 WIDE: entrance, door, plop
        return _drift(WIDE_A, WIDE_B, t, T0, CUT_R01)
    if t < CUT_QTURN:                                     # 2 MEDIUM Rae r01
        return _drift(_nudge(RAE_MED, 0, 6, 0.985), RAE_MED, t, CUT_R01, CUT_QTURN)
    if t < CUT_R02:                                       # 3 MEDIUM Quill: turn + q01
        return _drift(_nudge(QUILL_MED, 6, 4, 0.98), _nudge(QUILL_MED, 0, 0, 1.02), t, CUT_QTURN, CUT_R02)
    if t < CUT_SIP1:                                      # 4 MEDIUM Rae r02
        return _drift(_nudge(RAE_MED, 0, 0, 1.0), _nudge(RAE_MED, 2, -2, 1.025), t, CUT_R02, CUT_SIP1)
    if t < CUT_PUSH:                                      # 5 TWO-SHOT sip, stars
        return _drift(TWO, _nudge(TWO, 0, -6, 1.012), t, CUT_SIP1, CUT_PUSH)
    if t < CUT_QCU:                                       # 6 slow push-in on Rae
        return _drift(PUSH_A, PUSH_B, t, CUT_PUSH, CUT_QCU)
    if t < CUT_SIP2:                                      # 7 CLOSE-UP Quill
        return _drift(QUILL_CU, _nudge(QUILL_CU, 0, -1, 1.025), t, CUT_QCU, CUT_SIP2)
    if t < CUT_FREEZE:                                    # 8 TWO-SHOT done
        return _drift(_nudge(TWO, -4, 4, 1.03), _nudge(TWO, -2, 2, 1.045), t, CUT_SIP2, CUT_FREEZE)
    if t < CUT_DEADPAN:                                   # 9 CLOSE-UP Rae (camera holds dead still in the freeze)
        follow = smoothstep((t - (S("r07") - 0.1)) / 0.9)
        return Camera(RAE_CU.cx + 14 * follow, RAE_CU.cy + 5 * follow, RAE_CU.zoom * (1 - 0.04 * follow))
    if t < CUT_REACT:                                     # 10 MEDIUM CLOSE-UP Quill deadpan (slow creep in)
        return _drift(DEADPAN_A, DEADPAN_B, t, CUT_DEADPAN, CUT_TOAST)
    if t < CUT_Q05:                                       # 10b CLOSE-UP Rae: flat stare, one slow blink
        return _drift(RAE_REACT, _nudge(RAE_REACT, 0, 0, 1.01), t, CUT_REACT, CUT_Q05)
    if t < CUT_TOAST:                                     # 10c back on Quill: "Would you like to hear it?"
        return _drift(DEADPAN_A, DEADPAN_B, t, CUT_DEADPAN, CUT_TOAST)
    return _drift(RAE_TOAST, _nudge(RAE_TOAST, 4, -6, 1.05), t, CUT_TOAST, T1)   # 11 MEDIUM Rae: toast


# =========================================================================== render
def _door_clip_rect(d):
    """Stage rect of the (partly) open door panel still covering the doorway: Rae is behind it."""
    return skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(d), env.FLOOR_Y + 4)


def render(canvas, t):
    cam = camera(t)
    d = door(t)
    rp = rae_pose(t)
    qp = quill_pose(t)
    canvas.save()
    cam.apply(canvas, t)
    env.draw_lounge(canvas, t, light=1.0, door=d)
    Q.draw(canvas, qp, t)
    if rp.x < 200 and d < 0.999:
        canvas.save()
        canvas.clipRect(_door_clip_rect(d), skia.ClipOp.kDifference, True)
        R.draw(canvas, rp, warp(t))
        canvas.restore()
    else:
        R.draw(canvas, rp, warp(t))
    env.draw_lounge_front(canvas, t, light=1.0, door=d)
    # soft eye flash on the done chime where his irises are small on screen (two-shot)
    fl = clamp(1.0 - (t - DONE) / 0.45) if DONE <= t < DONE + 0.45 else 0.0
    if fl > 0 and cam.zoom < 2.0:
        hx, hy = Q.head_center(qp)
        glow(canvas, hx, hy, 34, "#B9FFF5", 0.55 * fl * fl)
    canvas.restore()
    # opening: S0 cuts out of a warm-white flash; fade from it
    a = 1.0 - smoothstep((t - T0) / 0.5)
    if a > 0:
        fx.draw_flash(canvas, a)
