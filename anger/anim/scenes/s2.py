"""S2 - The cavern (BIBLE section 4, S2; env.draw_cavern + cavern_lights).

He steps through the broken door (the cavern's entry arch, left wall) into the VAST dark - tiny in his pool of
torch light - settles, raises the torch and looks around (slow pans, scanning eyes), then searches: a few
careful steps, leaning to light the ground behind the rocks.  While he peers back toward the entry (head and
eyes turned left) four glowing eyes blink open in the crevice of the right wall behind him; they skitter off.
He moves on toward the pool - the stone under his right foot tips (clack), he stumbles, the torch tumbles end
over end (one turn per whoosh crest) into the pool: splash, hiss, steam - DARK.  Dead silence, only drips: he
stands frozen and only his eyes move; a shape scuttles across behind him (crawler, silhouette + eyes); he looks
over his shoulder - nothing.  He raises the sword and creeps on toward the far archway, footfalls on the
tension cue's heartbeats (handoff to S3: creeping, sword raised, no torch, dim teal ambient).

Lighting: torch-lit part - Anger is drawn with the set and darkened by the light map (torch pool falloff);
after the torch dies he is drawn after the darkness with light / tint from light.light_at() plus a cold teal
rim (the rig keeps his eye glints readable).  Walking follows env.WALK_PATH with x tied to the gait phase and
the size from env.depth_scale (careful steps = a partial stand->walk blend: shorter, lower strides).
"""
from __future__ import annotations

import bisect
import math

import skia

from anim import char_anger as A
from anim import char_crawler as C
from anim import env, fx, light
from anim.core import (Camera, beat, clamp, ease_in_out, ease_out, lerp, line_end, line_start, noise1, scene_span,
                       smoothstep, timeline)
from anim.rig import ArmPose, Pose
from anim.scenes.s1 import STEP_NAMES, Gaze, _lowres, blinks, bump, cam_at, cue_beats, gait_track, mk_pose

T0, T1 = scene_span("s2")
AR = A.ARMS

# =========================================================================== timing (named beats)
REVEAL = beat("reveal")
SETTLE = beat("reveal_settle")
LOOK = beat("look_around")
SEARCH = beat("search_start")
EYES = beat("eyes_glow")
SCURRY = beat("eyes_scurry")
STONE = beat("stone_shift")
TFLY = beat("torch_fly")
TSPLASH = beat("torch_splash")
TOUT = beat("torch_out")
LISTEN = beat("listen")
SC_BEHIND = beat("scurry_behind")
OVER = beat("over_shoulder")
CONT = beat("continue")
CRACKS_SEEN = beat("cracks_seen")
WRONG_ROCK = beat("wrong_rock")
CRESTS = [TFLY + o for o in (0.0, 0.40, 0.76, 1.11)]      # torch_whoosh: one end-over-end turn per crest
CLACK = STONE + 0.22                                        # stone_shift clack


def _sfx_times(name):
    return [s["start"] for s in timeline()["sfx"] if s["name"] == name and T0 <= s["start"] < T1]


DRIPS = _sfx_times("drip")                                  # plinks on the beat (drop lands)
HEART = [b for b in cue_beats("tension")] or [CONT + o for o in
                                                             (0.25, 1.13, 1.98, 2.81, 3.6, 4.38, 5.13, 5.85, 6.55, 7.25,
                                                              7.95)]
DRIP_XY = (520.0, 990.0)                                    # where the stalactite drips hit the pool

# =========================================================================== the floor path (x -> y, size)
_PX = [p[0] for p in env.WALK_PATH[:8]]
_PY = [p[1] for p in env.WALK_PATH[:8]]


def path_y(x):
    if x <= _PX[0]:
        return _PY[0]
    if x >= _PX[-1]:
        return _PY[-1]
    i = bisect.bisect_right(_PX, x) - 1
    return lerp(_PY[i], _PY[i + 1], (x - _PX[i]) / (_PX[i + 1] - _PX[i]))


def path_scale(x):
    return env.depth_scale(path_y(x))


# the creep on (dark part): WALK_PATH to the pool's right edge, then a flatter line along the near floor that
# only slowly bends away toward the far side (planted feet barely drift in depth while he creeps)
_CREEP = [(620.0, 1170.0), (800.0, 1158.0), (950.0, 1128.0), (1100.0, 1080.0), (1250.0, 1016.0)]


def creep_y(x):
    if x <= _CREEP[0][0]:
        return path_y(x)
    for (xa, ya), (xb, yb) in zip(_CREEP[:-1], _CREEP[1:]):
        if x <= xb:
            return lerp(ya, yb, (x - xa) / (xb - xa))
    return _CREEP[-1][1]


def fk(turn):
    return lerp(0.3, 1.0, smoothstep(abs(turn) / 0.4))


class PathWalk:
    """x(q) along the path: dx/dq = WALK_ADVANCE * fk(turn) * mix * size(x) (feet stay planted)."""

    def __init__(self, x_ref, q_ref, turn, mix=1.0, span=(-3.0, 6.0), yfn=None):
        self.q_ref, self.x_ref = q_ref, x_ref
        yfn = yfn or creep_y
        k = A.WALK_ADVANCE * fk(turn) * mix
        dq = 0.01
        n0, n1 = int(round(-span[0] / dq)), int(round(span[1] / dq))
        fw = [x_ref]
        for _ in range(n1):
            fw.append(fw[-1] + k * env.depth_scale(yfn(fw[-1])) * dq)
        bw = [x_ref]
        for _ in range(n0):
            bw.append(bw[-1] - k * env.depth_scale(yfn(bw[-1])) * dq)
        self.tab = list(reversed(bw[1:])) + fw
        self.q0 = q_ref - n0 * dq
        self.dq = dq

    def __call__(self, q):
        f = (q - self.q0) / self.dq
        i = int(clamp(math.floor(f), 0, len(self.tab) - 2))
        return lerp(self.tab[i], self.tab[i + 1], f - i)


def place(p, x):
    """Put the pose on the path at x (y and size from the floor perspective)."""
    p.x = x
    p.y = creep_y(x)
    p.scale = env.depth_scale(p.y)
    return p


def _ankle_off(p, t, side):
    R = A._solve(p, t)
    return A._mp(R.MS, R.legs[side].ankle)[0] - p.x


# =========================================================================== performance layout
TURN_IN = 0.16           # walking out of the arch toward the camera (3/4 front)
TURN_ST = 0.3            # standing / searching
TURN_CR = 0.5            # creeping on (side-ish)
MIX_SEARCH = 0.78        # careful search steps
MIX_CREEP = 0.5          # creeping half-strides

# entry: right foot plants on the reveal beat in the arch, two more steps, stop on the right foot
WE = [REVEAL, REVEAL + 0.55]
GE = gait_track(WE, 0.0, 0.5)
XE0 = env.ENTRY_POS[0] - 6.0
PWE = PathWalk(XE0, 0.0, TURN_IN)
STOPE = (WE[-1], WE[-1] + 0.45)


def walk_pose(x, q, turn, mix, **kw):
    """Walking pose on the path (mix < 1 = careful, shorter strides: a partial stand -> walk blend)."""
    if mix >= 0.999:
        p = mk_pose(x, turn=turn, state="walk", phase=q, **kw)
    else:
        p = mk_pose(x, turn=turn, state="stand", state_b="walk", mix=mix, phase_b=q, phase=q, **kw)
    return place(p, x)


def stand_pose(x, turn, **kw):
    return place(mk_pose(x, turn=turn, state="stand", **kw), x)


def start_ref(xs, turn, mix):
    """x of a walk at phase -0.4 whose planted left foot is where the standing pose at xs has it."""
    a = _ankle_off(stand_pose(xs, turn), 0.0, "l")
    b = _ankle_off(walk_pose(xs, -0.4, turn, mix), 0.0, "l")
    return xs + a - b


def stop_x(pw, q_plant, t_plant, side, turn, mix):
    """World x of the planted foot's ankle at its plant."""
    x = pw(q_plant)
    return x + _ankle_off(walk_pose(x, q_plant, turn, mix), t_plant, side)


def stopped_x(foot, side, turn, t):
    """x of the standing pose whose `side` ankle is at world x `foot`."""
    return foot - _ankle_off(stand_pose(foot, turn), t, side)


def walk_stop(t, g, pw, stop, side, turn, mix):
    """walk -> stand with the planted foot pinned (its ankle stays put)."""
    q = g(min(t, stop[1]))
    m = smoothstep((t - stop[0] - 0.06) / (stop[1] - stop[0] - 0.06))
    foot = stop_x(pw, g.ps[-1], stop[0], side, turn, mix)
    xw = pw(q)
    p = walk_pose(xw, q, turn, mix * (1.0 - m)) if m > 0 else walk_pose(xw, q, turn, mix)
    if m > 0:
        off = _ankle_off(p, t, side)
        place(p, lerp(xw, foot - off, clamp(m * 3.0)))
    return p


XE_STAND = stopped_x(stop_x(PWE, GE.ps[-1], STOPE[0], "l", TURN_IN, 1.0), "l", TURN_IN, STOPE[1])

# final approach: right plants on STONE (on the shifting stone), left before, right before that (full walk,
# coming toward the camera)
TURN_F = 0.16
WF = [STONE - 1.1, STONE - 0.55, STONE]
GF = gait_track(WF, 0.0, 0.5)
WALKF_ON = (WF[0] - 0.4 / (0.5 / 0.55), WF[0])


def _solve_stone_x():
    """pose x at STONE such that the right ankle lands on the shifting stone."""
    x = env.SHIFT_STONE_POS[0] - 70.0
    for _ in range(4):
        off = _ankle_off(walk_pose(x, GF.ps[-1], TURN_F, 1.0), STONE, "r")
        x = env.SHIFT_STONE_POS[0] - 10.0 - off
    return x


X_STONE = _solve_stone_x()
PWF = PathWalk(X_STONE, GF.ps[-1], TURN_F, 1.0)

# the search walk: from the entry stop toward the approach's start (2 steps, stride scaled to fit)
WS = [SEARCH, SEARCH + 0.55]
GS = gait_track(WS, 0.0, 0.5)
STOPS = (WS[-1], WS[-1] + 0.45)
SEARCH_ON = (WS[0] - 0.44, WS[0])


def _search_end(mix):
    pw = PathWalk(start_ref(XE_STAND, TURN_ST, mix), -0.4, TURN_ST, mix)
    return stopped_x(stop_x(pw, GS.ps[-1], STOPS[0], "l", TURN_ST, mix), "l", TURN_ST, STOPS[1]), pw


def _approach_start():
    """Standing x from which the final approach puts the right foot on the stone."""
    xr = PWF(-0.4)
    lo, hi = xr - 200.0, xr + 200.0
    for _ in range(25):
        mid = 0.5 * (lo + hi)
        pw = PathWalk(start_ref(mid, TURN_F, 1.0), -0.4, TURN_F, 1.0)
        if pw(GF.ps[-1]) < X_STONE:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _fit_search():
    target = None
    lo, hi = 0.3, 1.0
    for _ in range(18):
        m = 0.5 * (lo + hi)
        xs, _ = _search_end(m)
        # where the final approach must start from (its own start reference)
        if target is None:
            target = _approach_start()
        if xs < target:
            lo = m
        else:
            hi = m
    m = 0.5 * (lo + hi)
    xs, pw = _search_end(m)
    return m, xs, pw


MIX_S, XS_STAND, PWS = _fit_search()
# re-anchor the final approach so it starts exactly from the search spot (the stone plant shifts by the residue)
PWF = PathWalk(start_ref(XS_STAND, TURN_F, 1.0), -0.4, TURN_F, 1.0)

# the stumble: slip on the stone (u 0.25 on the clack), recovery step at u 0.62; the left foot stays planted
STUMBLE = (STONE, STONE + (CLACK - STONE) / 0.25)
STUMBLE_END = STUMBLE[1]
L_FOOT_STONE = stop_x(PWF, GF.ps[-1] - 0.5, WF[1], "l", TURN_F, 1.0)      # left planted at WF[1]
X_DARK = stopped_x(L_FOOT_STONE, "l", TURN_ST, STUMBLE_END + 1.0)

# the creep: footfalls on the heartbeats after `continue`
WC = [h for h in HEART if h > CONT + 2.3]
GC = gait_track(WC, 0.0, 0.5)
WALKC_ON = (WC[0] - 0.4 / GC.rb, WC[0])
PWC = PathWalk(start_ref(X_DARK, TURN_CR, MIX_CREEP), -0.4, TURN_CR, MIX_CREEP)

# =========================================================================== shots
CUT_PUSH = LOOK                   # B  medium-close: looks up / around (n09 "...so vast" plays on the wide)
CUT_PAN = LOOK + 1.9              # C  wide pan: "his torchlight could not find its walls"
CUT_SEARCH = SEARCH + 0.6         # D  medium: careful steps, lights the ground ("dark, and cold, ... quiet")
CUT_EYES = EYES - 0.3             # E1 two planes: Anger peering back left, the crevice behind him (eyes open)
CUT_CREV = EYES + 0.75            # E2 close on the crevice: the eyes blink, dart, skitter off
CUT_BACK = SCURRY + 0.55          # E3 medium: Anger unaware ("He did not see the eyes.")
CUT_APPROACH = line_start("n11") + 2.3   # F  wide-ish: he moves on; in the dark the eyes "had seen him"
CUT_STONE = STONE - 0.75          # G  medium-wide: the stone tips, stumble, the torch flies
CUT_POOL = TSPLASH - 0.25         # H  insert: splash, steam, the light dies
CUT_DARK = TOUT + 0.65            # I  dark wide: "And then, there was only darkness."
CUT_STILL = line_start("n13") - 0.3      # I2 medium: "Anger stood perfectly still..."
CUT_LISTEN = line_start("n13") + 0.9     # J  close: "...and listened." only the eyes move
CUT_SCURRY = SC_BEHIND - 0.15     # K  medium: a shape scuttles across behind him
CUT_OVER = OVER - 0.05            # L  close: the look over the shoulder
CUT_POV = OVER + 0.95             # M  what he sees: "Nothing."
CUT_FACE = OVER + 2.25            # N  close: "Nothing he could see." eyes narrow, turns back
CUT_GUARD = CONT + 0.2            # O  medium: sword up, starts creeping ("So he pressed on, sword raised...")
CUT_WIDE = CONT + 3.3             # P  wide: creeping on in the vast dark
CUT_CRACKS = CRACKS_SEEN          # Q1 low medium-wide: the floor ahead of him - hairline cracks spreading
CUT_BOOTS = line_start("n15") + 4.6      # Q2 close on his boots: "...the thin cracks spreading beneath his feet"
CUTS = [CUT_PUSH, CUT_PAN, CUT_SEARCH, CUT_EYES, CUT_CREV, CUT_BACK, CUT_APPROACH, CUT_STONE, CUT_POOL, CUT_DARK,
        CUT_STILL, CUT_CRACKS, CUT_BOOTS,
        CUT_LISTEN, CUT_SCURRY, CUT_OVER, CUT_POV, CUT_FACE, CUT_GUARD, CUT_WIDE]

TORCH_LOW = ArmPose(shoulder=62.0, elbow=48.0, wrist=-40.0, hand="hold")       # lighting the ground ahead
TORCH_UP = AR["torch_up"]
TORCH_HI = AR["torch_high"]


# =========================================================================== torch flight
def _torch_release():
    """(grip x, y, draw_torch angle, scale) of the held torch at the release frame."""
    p = anger_pose(TFLY - 1e-4, force_torch=True)
    R = A._solve(p, TFLY)
    g, ang, _ = R.props["torch"]
    gx, gy = A.hand_pos(p, "l", TFLY)
    return gx, gy, -ang - 180.0, p.scale


_REL = None


def torch_flight(t):
    """Loose torch (grip x, y, angle, scale) during [TFLY, TSPLASH]."""
    global _REL
    if _REL is None:
        _REL = _torch_release()
    x0, y0, a0, s0 = _REL
    T = TSPLASH - TFLY
    tau = clamp(t - TFLY, 0.0, T)
    # end: the torch's middle enters the water at the splash point
    x1, y1 = env.TORCH_SPLASH_POS[0] - 30.0, env.TORCH_SPLASH_POS[1] - 50.0
    g = 2200.0
    vy = (y1 - y0 - 0.5 * g * T * T) / T
    x = lerp(x0, x1, tau / T)
    y = y0 + vy * tau + 0.5 * g * tau * tau
    # end over end: whole turns between the whoosh crests (clockwise = flame swings forward / down)
    ks = [c - TFLY for c in CRESTS] + [T]
    turns = [0.0, 1.0, 2.0, 3.0, 3.55]
    i = min(bisect.bisect_right(ks, tau) - 1, len(ks) - 2)
    i = max(i, 0)
    f = (tau - ks[i]) / (ks[i + 1] - ks[i])
    tr = lerp(turns[i], turns[i + 1], f)
    ang = a0 + 360.0 * tr
    sc = lerp(s0, env.depth_scale(env.TORCH_SPLASH_POS[1]) * 0.95, smoothstep(tau / T))
    return x, y, ang, sc


def torch_light_pos(t, pose):
    """(x, y, strength, size) of the torch flame light, or None."""
    if t < TFLY:
        tp = A.torch_pos(pose, t)
        return (tp[0], tp[1], 1.0, pose.scale) if tp else None
    if t < TSPLASH:
        x, y, a, s = torch_flight(t)
        ox, oy = A.torch_flame_offset(a, s)
        return x + ox, y + oy, 1.0, s
    if t < TOUT + 0.05:
        k = (t - TSPLASH) / (TOUT + 0.05 - TSPLASH)
        st = (1.0 - k) ** 1.5 * (0.55 + 0.45 * abs(math.sin(t * 37.0)))       # sputters out
        sx, sy = env.TORCH_SPLASH_POS
        return sx, sy - 30.0, 0.6 * st, 0.8
    return None


# =========================================================================== Anger's performance
GAZE = Gaze([
    (REVEAL, 0.35, 0.0), (REVEAL + 1.4, 0.55, -0.35), (SETTLE + 0.15, 0.3, -0.7, 0.14), (LOOK + 0.1, -0.7, -0.45, 0.13),
    (LOOK + 0.9, -0.55, -0.3), (LOOK + 1.6, 0.2, -0.55, 0.14), (LOOK + 2.4, 0.85, -0.25, 0.13), (LOOK + 3.2, 0.7, 0.1),
    (LOOK + 4.0, 0.9, 0.05), (SEARCH - 0.2, 0.55, 0.25), (SEARCH + 1.4, 0.45, 0.7, 0.12), (SEARCH + 2.0, 0.85, 0.6),
    (SEARCH + 2.6, 0.2, 0.75, 0.12), (SEARCH + 3.2, 0.6, 0.55),
    (EYES - 0.55, -0.85, -0.1, 0.13), (EYES + 0.5, -0.6, -0.25), (EYES + 1.2, -0.9, 0.0), (SCURRY + 0.3, -0.75, -0.15),
    (SCURRY + 0.75, 0.3, -0.6, 0.14), (SCURRY + 1.8, 0.55, -0.4), (STONE - 3.2, 0.75, 0.35, 0.12), (STONE - 2.2, 0.6, 0.25),
    (STONE - 1.2, 0.7, 0.15), (STONE + 0.1, 0.4, 0.6, 0.08), (TFLY + 0.15, 0.6, -0.5, 0.1), (TFLY + 0.6, 0.85, 0.1),
    (TSPLASH + 0.12, 0.8, 0.3),
    # the listening: only the eyes move
    (TOUT + 0.6, 0.55, 0.05), (LISTEN + 0.15, 0.62, 0.04, 0.12),
    (DRIPS[0] + 0.35, 0.95, 0.2, 0.09), (DRIPS[0] + 1.4, 0.2, 0.0, 0.16), (DRIPS[0] + 2.1, -0.62, -0.05, 0.12),
    (DRIPS[1] + 0.35, 0.85, 0.15, 0.09), (DRIPS[1] + 0.95, 0.3, -0.45, 0.12), (DRIPS[1] + 1.5, -0.4, 0.0, 0.12),
    (DRIPS[2] + 0.35, 0.7, 0.2, 0.09), (SC_BEHIND + 0.3, -0.95, 0.05, 0.08),
    (OVER + 0.1, -1.0, 0.05, 0.1), (OVER + 1.1, -0.85, -0.1), (OVER + 1.7, -1.0, 0.1), (OVER + 2.5, -0.3, 0.0, 0.14),
    (OVER + 2.95, 0.6, 0.0, 0.13), (CONT + 0.7, 0.85, -0.05), (CONT + 2.4, 0.6, 0.05), (CONT + 3.5, 0.9, -0.1),
    (CONT + 5.0, 0.75, 0.05), (CONT + 6.2, 0.95, -0.15),
])
BLINKS = [REVEAL + 1.0, SETTLE + 0.12, LOOK + 1.55, LOOK + 3.6, SEARCH + 1.35, EYES - 0.6, SCURRY + 0.72,
          STONE - 2.4, STONE + 0.3, TSPLASH + 0.55, TOUT + 1.2, LISTEN + 2.9, OVER + 2.45, CONT + 1.1, CONT + 4.6]


def _arm_track(t):
    """Torch arm: high on the way in, way up to see the vastness, low to light the ground, high again."""
    keys = [(REVEAL, TORCH_HI), (SETTLE, TORCH_HI), (SETTLE + 0.6, TORCH_UP), (SEARCH - 0.3, TORCH_UP),
            (SEARCH + 0.4, TORCH_HI), (SEARCH + 1.0, TORCH_LOW), (EYES - 0.75, TORCH_LOW), (EYES - 0.2, TORCH_HI),
            (SCURRY + 0.8, TORCH_HI), (SCURRY + 1.5, TORCH_UP), (STONE - 2.6, TORCH_UP), (STONE - 1.8, TORCH_HI)]
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t < keys[i][0]:
            k = ease_in_out((t - keys[i - 1][0]) / (keys[i][0] - keys[i - 1][0]))
            return ArmPose.blend(keys[i - 1][1], keys[i][1], k)
    return keys[-1][1]


def _face(p, t):
    lx, ly = GAZE(t)
    p.look_x, p.look_y = lx, ly
    awe = bump(t, REVEAL + 0.3, REVEAL + 1.5, LOOK + 1.5, LOOK + 3.0)
    lid = 0.86 + 0.03 * noise1(t * 0.4, 41) + 0.1 * awe
    lid -= 0.12 * bump(t, TOUT, TOUT + 0.3, TOUT + 1.0, TOUT + 1.6)          # the dark falls: a slow, flat blink-ish
    lid += 0.08 * bump(t, SC_BEHIND + 0.25, SC_BEHIND + 0.35, OVER + 1.4, OVER + 2.3)
    lid -= 0.1 * bump(t, OVER + 2.2, OVER + 2.5, CONT + 0.3, CONT + 0.9)     # narrows: nothing there
    furrow = 0.2 + 0.04 * noise1(t * 0.3, 42) - 0.15 * awe
    furrow += 0.15 * bump(t, SEARCH, SEARCH + 0.6, STONE - 0.5, STONE)
    furrow += 0.3 * bump(t, LISTEN, LISTEN + 1.0, T1, T1 + 1)
    raise_ = 0.18 * awe - 0.05
    raise_ += 0.4 * bump(t, STONE + 0.12, STONE + 0.22, STONE + 0.6, STONE + 1.0)     # caught off balance
    raise_ += 0.12 * bump(t, SC_BEHIND + 0.25, SC_BEHIND + 0.35, OVER + 0.9, OVER + 1.6)
    for d in DRIPS[:3]:                                   # each drip: a tiny brow lift, a beat after the sound
        raise_ += 0.1 * bump(t, d + 0.3, d + 0.42, d + 0.8, d + 1.3)
    p.eye_wide = 0.35 * bump(t, STONE + 0.12, STONE + 0.22, STONE + 0.5, STONE + 0.9)
    p.pupil = 1.0 + 0.25 * awe + 0.2 * bump(t, TOUT, TOUT + 0.5, T1, T1 + 1)
    p.squint = 0.15 * bump(t, SEARCH + 0.8, SEARCH + 1.2, EYES - 0.8, EYES - 0.5)
    p.smile = -0.1 - 0.08 * bump(t, TSPLASH + 0.3, TSPLASH + 0.6, TOUT + 1.0, TOUT + 1.8)
    p.mouth_open = 0.06 * awe + 0.12 * bump(t, STONE + 0.15, STONE + 0.25, STONE + 0.45, STONE + 0.8)
    p.extra["strain"] = 0.4 * bump(t, STONE + 0.2, STONE + 0.3, STUMBLE_END - 0.3, STUMBLE_END)
    p.lid_l = p.lid_r = clamp(lid) * blinks(t, BLINKS)
    p.brow_furrow = clamp(furrow)
    p.brow_raise = raise_
    p.head_tilt += 1.0 * noise1(t * 0.33, 43)
    p.head_nod += 0.04 * noise1(t * 0.27, 44)
    return p


def _head(p, t):
    """Head turns / nods: up at the vastness, around, down at the ground, back over the shoulder, ..."""
    nod = 0.25 * bump(t, SETTLE, SETTLE + 0.7, LOOK + 1.8, LOOK + 2.6)
    nod -= 0.32 * bump(t, SEARCH + 0.8, SEARCH + 1.3, EYES - 0.8, EYES - 0.4)
    nod += 0.2 * bump(t, SCURRY + 0.75, SCURRY + 1.3, STONE - 3.3, STONE - 2.6)
    nod -= 0.12 * bump(t, STONE - 2.6, STONE - 2.2, STONE - 0.6, STONE - 0.2)
    ht = -0.22 * bump(t, LOOK, LOOK + 0.6, LOOK + 1.4, LOOK + 2.0) + 0.12 * bump(t, LOOK + 2.2, LOOK + 2.8, SEARCH - 0.4, SEARCH)
    ht -= 0.55 * bump(t, EYES - 0.75, EYES - 0.3, SCURRY + 0.45, SCURRY + 0.95)          # peering back toward the entry
    ht -= 0.1 * bump(t, DRIPS[1] + 1.45, DRIPS[1] + 1.85, DRIPS[2] + 0.2, DRIPS[2] + 0.6)    # the micro head turn
    ht -= 0.7 * bump(t, OVER, OVER + 0.38, OVER + 2.5, OVER + 3.1)                        # over the shoulder
    p.head_nod += nod
    p.head_turn += ht
    p.head_tilt += 4.0 * bump(t, OVER + 0.1, OVER + 0.4, OVER + 2.5, OVER + 3.0)
    return p


def anger_pose(t, force_torch=False):
    p = None
    if t < STOPE[0]:
        # ---------------------------------------------------------------- entry steps
        q = GE(t)
        p = walk_pose(PWE(q), q, TURN_IN, 1.0)
    elif t < SEARCH_ON[0]:
        p = walk_stop(t, GE, PWE, STOPE, "l", TURN_IN, 1.0)
        if t >= STOPE[1]:
            p = stand_pose(XE_STAND, TURN_IN)
        p.turn = lerp(TURN_IN, TURN_ST, smoothstep((t - STOPE[1]) / 0.8))
    elif t < WALKF_ON[0]:
        # ---------------------------------------------------------------- search steps, then the search spot
        if t < STOPS[0]:
            q = GS(t)
            m = smoothstep((t - SEARCH_ON[0]) / (SEARCH_ON[1] - SEARCH_ON[0]))
            x = lerp(XE_STAND, PWS(q), m)
            p = walk_pose(x, q, TURN_ST, MIX_S * m)
        elif t < STOPS[1]:
            p = walk_stop(t, GS, PWS, STOPS, "l", TURN_ST, MIX_S)
        else:
            p = stand_pose(XS_STAND, TURN_ST)
        # lean in to light the ground behind the rocks
        p.lean = 11.0 * bump(t, SEARCH + 0.9, SEARCH + 1.5, EYES - 1.0, EYES - 0.5)
        p.turn = lerp(TURN_ST, TURN_F, smoothstep((t - (WALKF_ON[0] - 0.6)) / 0.6))
    elif t < STONE:
        # ---------------------------------------------------------------- the final approach
        q = GF(t)
        m = smoothstep((t - WALKF_ON[0]) / (WALKF_ON[1] - WALKF_ON[0]))
        x = lerp(XS_STAND, PWF(q), m)
        p = walk_pose(x, q, TURN_F, m)
    elif t < STUMBLE_END + 0.6:
        # ---------------------------------------------------------------- the stumble (left foot pinned)
        u = clamp((t - STUMBLE[0]) / (STUMBLE[1] - STUMBLE[0]))
        m = smoothstep((t - STONE) / 0.18)
        q = GF(min(t, STONE + 0.18))
        p = walk_pose(PWF(q), q, TURN_F, 1.0)
        p.extra.update(state_b="stumble", phase_b=u, mix=m, slip_foot="r")
        if u >= 1.0:
            ms = smoothstep((t - STUMBLE_END) / 0.5)
            p.extra.update(state="stumble", phase=1.0, state_b="stand", mix=ms)
        p.turn = lerp(TURN_F, TURN_ST, smoothstep((t - STONE - 0.3) / 1.2))
        off = _ankle_off(p, t, "l")
        place(p, lerp(p.x, L_FOOT_STONE - off, m))
    else:
        # ---------------------------------------------------------------- dark: frozen, listening, then creeping on
        if t < WALKC_ON[0]:
            p = stand_pose(X_DARK, TURN_ST)
        else:
            q = GC(t)
            m = smoothstep((t - WALKC_ON[0]) / (WALKC_ON[1] - WALKC_ON[0]))
            x = lerp(X_DARK, PWC(q), m)
            p = walk_pose(x, q, TURN_CR, MIX_CREEP * m)
        p.turn = lerp(TURN_ST, TURN_CR, smoothstep((t - CONT - 0.4) / 1.6))
        # sword comes up to the guard
        k = smoothstep((t - (CONT + 0.25)) / 0.75)
        p.arm_r = ArmPose.blend(AR["sword_low"], AR["sword_guard"], k)
        p.shoulders_up = 0.15 * smoothstep((t - CONT) / 1.0) + 0.2 * bump(t, OVER - 0.1, OVER + 0.2, OVER + 1.0, OVER + 2.0)
        # frozen: a held, shallow breath while listening
        if t < CONT:
            p.breath = 0.35 * math.sin(2 * math.pi * 0.16 * t)
    # ---------------------------------------------------------------- torch
    ex = p.extra
    if t < TFLY or force_torch:
        ex["torch"] = "l"
        p.arm_l = _arm_track(t)
    else:
        ex["torch"] = None
        p.arm_l = ArmPose.blend(AR["rest"], ArmPose(14.0, 34.0, 0.0, "fist"), smoothstep((t - CONT) / 1.0))
    p = _head(p, t)
    return _face(p, t)


# =========================================================================== floor cracks (foreshadow the collapse)
# hairline cracks in the CAVERN floor (stage coords), ahead of / under his creep at the end of S2.
# (points, growth window (g0, g1) within crack_growth(), core width at depth scale 1). Each crack spreads from
# its first point toward its last (the main one runs back toward and under his boots).
FLOOR_CRACKS = [
    ([(1062.0, 1112.0), (1030.0, 1126.0), (1004.0, 1121.0), (972.0, 1138.0), (941.0, 1143.0), (913.0, 1158.0),
      (884.0, 1160.0), (858.0, 1174.0), (829.0, 1170.0), (801.0, 1166.0), (776.0, 1173.0), (750.0, 1186.0),
      (724.0, 1190.0)], (0.0, 0.62), 3.8),
    ([(941.0, 1143.0), (953.0, 1162.0), (944.0, 1180.0), (962.0, 1198.0), (958.0, 1214.0)], (0.3, 0.75), 2.4),
    ([(884.0, 1160.0), (872.0, 1146.0), (849.0, 1142.0), (826.0, 1131.0), (803.0, 1134.0)], (0.45, 0.9), 2.0),
    ([(905.0, 1100.0), (933.0, 1092.0), (957.0, 1099.0), (990.0, 1086.0), (1012.0, 1090.0)], (0.12, 0.55), 2.1),
]
CRACK_ZONE = (700.0, 1080.0, 1080.0, 1220.0)           # bounding box of all cracks (x0, y0, x1, y1)


def crack_growth(t):
    """0..1: the cracks start spreading a little before cracks_seen and are complete at wrong_rock."""
    return clamp((t - (CRACKS_SEEN - 1.8)) / (WRONG_ROCK - CRACKS_SEEN + 1.8))   # rev 2b: a bit earlier


def draw_floor_cracks(canvas, t, growth=None, alpha=1.0):
    """Thin hairline cracks spreading through the cavern floor (STAGE coords, cavern set). Draw it in the LIT pass
    (after env.draw_cavern, before light.apply_darkness): a near-black core, a faint lighter upper lip and a
    little grit. growth None = crack_growth(t) (from cracks_seen to wrong_rock); 0 = invisible."""
    g = crack_growth(t) if growth is None else clamp(growth)
    if g <= 0.0 or alpha <= 0.0:
        return
    vis = canvas.getLocalClipBounds()
    if vis.right() < CRACK_ZONE[0] or vis.left() > CRACK_ZONE[2] or vis.bottom() < CRACK_ZONE[1] or \
            vis.top() > CRACK_ZONE[3]:
        return
    core = skia.Paint(AntiAlias=True, Color=skia.Color(6, 5, 9))
    core.setStyle(skia.Paint.kStroke_Style)
    core.setStrokeCap(skia.Paint.kRound_Cap)
    lip = skia.Paint(AntiAlias=True, Color=skia.Color(182, 176, 196))
    lip.setStyle(skia.Paint.kStroke_Style)
    lip.setStrokeCap(skia.Paint.kRound_Cap)
    grit = skia.Paint(AntiAlias=True, Color=skia.Color(150, 144, 160))
    for ci, (pts, (g0, g1), w0) in enumerate(FLOOR_CRACKS):
        f = clamp((g - g0) / (g1 - g0))
        if f <= 0.0:
            continue
        seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
        total = sum(seg)
        reach = f * total
        acc = 0.0
        for i, L in enumerate(seg):
            if acc >= reach:
                break
            a, b = pts[i], pts[i + 1]
            u = min(1.0, (reach - acc) / L)
            bx, by = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            s_ = env.depth_scale(0.5 * (a[1] + by))
            taper = 1.0 - 0.55 * (acc + 0.5 * L * u) / total            # thinner toward the spreading tip
            w = w0 * s_ * taper
            core.setStrokeWidth(max(0.7, 1.15 * w))
            core.setAlphaf(0.88 * alpha)
            canvas.drawLine(a[0], a[1], bx, by, core)
            lip.setStrokeWidth(max(0.6, 0.5 * w))
            lip.setAlphaf(0.62 * alpha)
            canvas.drawLine(a[0], a[1] - 0.9 * w - 0.6, bx, by - 0.9 * w - 0.6, lip)
            acc += L
        # grit: a few specks kicked up along the crack (only where it has already spread)
        for k in range(int(total / 18)):
            h1, h2, h3 = (math.sin((ci * 31 + k) * 12.9898 + j * 78.233) * 43758.5453 % 1.0 for j in range(3))
            d = h1 * total
            if d > reach:
                continue
            acc, i = 0.0, 0
            while i < len(seg) - 1 and acc + seg[i] < d:
                acc += seg[i]
                i += 1
            a, b = pts[i], pts[i + 1]
            u = (d - acc) / seg[i]
            s_ = env.depth_scale(a[1])
            gx = lerp(a[0], b[0], u) + (h2 - 0.5) * 16 * s_
            gy = lerp(a[1], b[1], u) + (h3 - 0.5) * 7 * s_
            grit.setAlphaf((0.25 + 0.3 * h2) * alpha)
            canvas.drawCircle(gx, gy, (0.7 + 1.1 * h3) * s_, grit)


# =========================================================================== crawler
LURK = (env.CREVICE_POS[0], env.CREVICE_POS[1] + 216.0 * env.CREVICE_SCALE)


def crawler_lurk(t):
    """The eyes in the crevice: blink open on eyes_glow, dart, skitter off on eyes_scurry."""
    if not (EYES - 0.05 <= t < SCURRY + 0.6):
        return None
    glow = smoothstep((t - EYES) / 0.12) * (1.0 - smoothstep((t - SCURRY - 0.25) / 0.25))
    dx = dy = 0.0
    if t > SCURRY:
        u = t - SCURRY
        dx = 22.0 * math.sin(u * 40.0) * math.exp(-u * 6.0) + 90.0 * ease_out(clamp((u - 0.12) / 0.4))
        dy = -40.0 * ease_out(clamp((u - 0.12) / 0.4))
    p = Pose(x=LURK[0] + dx * env.CREVICE_SCALE, y=LURK[1] + dy * env.CREVICE_SCALE, scale=env.CREVICE_SCALE)
    lids = None
    if t < EYES + 0.35:                      # they open slowly, out of sync is handled by the rig's own blinks
        lids = smoothstep((t - EYES) / 0.3)
    p.lid_l = p.lid_r = lids
    lx = 0.0
    if EYES + 0.6 < t < SCURRY:
        lx = (-0.7 if (t - EYES) % 0.9 < 0.45 else 0.6)
    p.look_x = lx
    p.extra = dict(state="lurk", eye_glow=glow, body_alpha=0.55)
    return p


WATCH = (line_start("n11") + 3.5, line_end("n11") - 0.05)       # "But the eyes... had seen him."
WATCH_POS = (700.0, 868.0)                                       # out in the dark beyond the pool


def crawler_watch(t):
    """The four eyes, watching him from the dark (eyes only, no body), on the narrator's last words of n11."""
    if not (WATCH[0] - 0.05 <= t < WATCH[1] + 0.3):
        return None
    sc = env.depth_scale(WATCH_POS[1]) * 0.85
    p = Pose(x=WATCH_POS[0], y=WATCH_POS[1] + 216.0 * sc, scale=sc)
    op = smoothstep((t - WATCH[0]) / 0.3) * (1.0 - smoothstep((t - WATCH[1]) / 0.22))
    p.lid_l = p.lid_r = op
    p.look_x, p.look_y = -0.75, 0.25                             # on him
    p.extra = dict(state="lurk", eye_glow=op, body_alpha=0.0)
    return p


def crawler_scurry(t):
    """The shape that scuttles across behind him (side view, right -> left, mostly silhouette + eyes)."""
    t0 = SC_BEHIND - 0.1
    if not (t0 <= t < t0 + 1.6):
        return None
    sc = env.depth_scale(955.0) * 0.95
    cyc = 0.26
    q = (t - t0) / cyc
    x = 980.0 - q * C.ADVANCE["scurry"] * sc
    p = Pose(x=x, y=955.0, scale=sc, facing=-1.0)
    p.extra = dict(state="scurry", phase=q)
    return p


# =========================================================================== cameras
_HREF = {}


def _head_ref(t):
    if t not in _HREF:
        _HREF[t] = A.head_center(anger_pose(t), t)
    return _HREF[t]


def camera(t):
    if t < CUT_PUSH:
        k = ease_in_out((t - REVEAL) / (CUT_PUSH - REVEAL))
        return Camera(lerp(430.0, 360.0, k), lerp(560.0, 600.0, k), lerp(0.44, 0.49, k))
    if t < CUT_PAN:
        h = _head_ref(SETTLE + 0.8)
        k = ease_in_out((t - CUT_PUSH) / (CUT_PAN - CUT_PUSH))
        return cam_at(h[0] + 60.0, h[1] + lerp(70.0, 50.0, k), lerp(1.45, 1.6, k), 0.5, 0.42)
    if t < CUT_SEARCH:
        k = ease_in_out((t - CUT_PAN) / (CUT_SEARCH - CUT_PAN))
        return Camera(lerp(120.0, 820.0, k), lerp(720.0, 660.0, k), 0.62)
    if t < CUT_EYES:
        x = anger_pose(CUT_SEARCH + 1.5).x
        k = ease_in_out((t - CUT_SEARCH) / (CUT_EYES - CUT_SEARCH))
        return Camera(x + lerp(140.0, 110.0, k), lerp(760.0, 790.0, k), lerp(0.88, 0.95, k))
    if t < CUT_CREV:
        k = ease_in_out((t - CUT_EYES) / (CUT_CREV - CUT_EYES))
        return Camera(lerp(600.0, 650.0, k), lerp(730.0, 710.0, k), lerp(0.52, 0.57, k))
    if t < CUT_BACK:
        k = ease_in_out((t - CUT_CREV) / (CUT_BACK - CUT_CREV))
        return Camera(env.CREVICE_POS[0] - 10.0, env.CREVICE_POS[1] + 30.0, lerp(2.45, 2.75, k))
    if t < CUT_APPROACH:
        h = _head_ref(CUT_BACK + 1.0)
        k = ease_in_out((t - CUT_BACK) / (CUT_APPROACH - CUT_BACK))
        return cam_at(h[0] + 70.0, h[1] + 120.0, lerp(1.2, 1.3, k), 0.5, 0.4)
    if t < CUT_STONE:
        k = ease_in_out((t - CUT_APPROACH) / (CUT_STONE - CUT_APPROACH))
        return Camera(lerp(200.0, 260.0, k), 760.0, lerp(0.6, 0.66, k))
    if t < CUT_POOL:
        return Camera(330.0, 760.0, 0.64)
    if t < CUT_DARK:
        k = ease_in_out((t - CUT_POOL) / (CUT_DARK - CUT_POOL))
        return Camera(lerp(545.0, 550.0, k), lerp(930.0, 945.0, k), lerp(1.45, 1.55, k))
    if t < CUT_STILL:
        k = ease_in_out((t - CUT_DARK) / (CUT_STILL - CUT_DARK))
        return Camera(lerp(330.0, 315.0, k), lerp(760.0, 750.0, k), lerp(0.6, 0.66, k))
    if t < CUT_LISTEN:
        h = _head_ref(CUT_STILL + 0.5)
        k = ease_in_out((t - CUT_STILL) / (CUT_LISTEN - CUT_STILL))
        return cam_at(h[0] + 20.0, h[1] + 300.0, lerp(0.86, 0.95, k), 0.5, 0.36)
    if t < CUT_SCURRY:
        h = _head_ref(CUT_LISTEN + 0.5)
        k = ease_in_out((t - CUT_LISTEN) / (CUT_SCURRY - CUT_LISTEN))
        return cam_at(h[0] + 8.0, h[1] + 12.0, lerp(2.4, 2.75, k), 0.5, 0.42)
    if t < CUT_OVER:
        h = _head_ref(SC_BEHIND)
        return cam_at(h[0] + 140.0, h[1] + 260.0, 0.92, 0.5, 0.42)
    if t < CUT_POV:
        h = _head_ref(OVER + 0.5)
        k = ease_in_out((t - CUT_OVER) / (CUT_POV - CUT_OVER))
        return cam_at(h[0] - 10.0, h[1] + 20.0, lerp(2.0, 2.12, k), 0.55, 0.42)
    if t < CUT_FACE:
        k = ease_in_out((t - CUT_POV) / (CUT_FACE - CUT_POV))
        return Camera(lerp(-330.0, -350.0, k), 820.0, lerp(0.86, 0.9, k))
    if t < CUT_GUARD:
        h = _head_ref(OVER + 2.6)
        k = ease_in_out((t - CUT_FACE) / (CUT_GUARD - CUT_FACE))
        return cam_at(h[0], h[1] + 15.0, lerp(2.5, 2.4, k), 0.5, 0.42)
    if t < CUT_WIDE:
        h = _head_ref(CONT + 1.0)
        k = ease_in_out((t - CUT_GUARD) / (CUT_WIDE - CUT_GUARD))
        return cam_at(h[0] + lerp(120.0, 190.0, k), h[1] + 250.0, lerp(1.02, 1.1, k), 0.5, 0.4)
    if t < CUT_CRACKS:
        k = ease_in_out((t - CUT_WIDE) / (CUT_CRACKS - CUT_WIDE))
        return Camera(lerp(470.0, 540.0, k), lerp(640.0, 650.0, k), lerp(0.44, 0.48, k))
    if t < CUT_BOOTS:
        # low medium-wide: the floor ahead with the hairline cracks, he creeps in from the left
        k = ease_in_out((t - CUT_CRACKS) / (CUT_BOOTS - CUT_CRACKS))
        return Camera(lerp(790.0, 830.0, k), 1030.0, lerp(0.74, 0.8, k))
    k = ease_in_out((t - CUT_BOOTS) / (T1 - CUT_BOOTS))
    return Camera(lerp(745.0, 800.0, k), 1112.0, lerp(2.05, 2.2, k))


# =========================================================================== rendering
def _ambient(t):
    if t < TOUT:
        return 0.06
    return lerp(0.065, 0.11, smoothstep((t - TOUT) / 1.4))


def _stone_tilt(t):
    if t < STONE:
        return 0.0
    u = t - STONE
    k = ease_out(clamp(u / 0.22))
    wob = 0.18 * math.sin((u - 0.22) * 22.0) * math.exp(-(u - 0.22) * 5.0) if u > 0.22 else 0.0
    return k * (1.0 - 0.4 * smoothstep((u - 0.3) / 0.8)) + wob


def _anger_bbox(p, t):
    s = p.scale
    return (p.x - 220 * s, p.y - 860 * s, p.x + 260 * s, p.y + 10)


def _draw_drips(c, t):
    for td in DRIPS:
        age = t - td
        if -0.5 < age < 0:
            # the drop falls from the dark (the plink lands on the beat)
            y = DRIP_XY[1] - 0.5 * 2600.0 * age * age
            c.drawOval(skia.Rect(DRIP_XY[0] - 2.2, y - 6.0, DRIP_XY[0] + 2.2, y + 2.0),
                       skia.Paint(AntiAlias=True, Color=skia.Color(150, 205, 220, 210)))
        elif 0 <= age < 3.0:
            fx.ripples(c, DRIP_XY[0], DRIP_XY[1], age, size=0.35, n=2, alpha=0.8, life=2.4)


def render(canvas, t):
    c = canvas
    pose = anger_pose(t)
    cam = camera(t)
    dark_mode = t >= CUT_POOL                      # Anger drawn after the darkness, lit by light_at
    tl = torch_light_pos(t, pose)
    splash_t = t - TSPLASH if t >= TSPLASH else None
    cam.apply(c, t)

    def _set(cc):
        env.draw_cavern(cc, t, stone_tilt=_stone_tilt(t), pool_splash_t=splash_t,
                        torch_pos=(tl[0], tl[1]) if (tl and t < TSPLASH) else None, drips=False)
        _draw_drips(cc, t)
    if cam.zoom >= 2.0:
        _lowres(c, cam, t, 0.5, _set)            # close-ups: soft background, cheaper tile fills
    else:
        _set(c)
    draw_floor_cracks(c, t)                      # always crisp (the boots close-up looks right at them)
    lurk = crawler_lurk(t)
    if lurk is not None:
        C.draw(c, lurk, t)
    scur = crawler_scurry(t)
    if scur is not None:
        scur.light, scur.tint, scur.tint_amt = 0.55, (10, 18, 28), 0.5
        C.draw(c, scur, t)
    if TFLY <= t < TSPLASH:
        x, y, a, s = torch_flight(t)
        A.draw_torch(c, x, y, a, t, scale=s)
    if not dark_mode:
        A.draw(c, pose, t)
    c.resetMatrix()
    amb = _ambient(t)
    lights = env.cavern_lights(t)
    if tl is not None:
        lights.append(light.torch_light(tl[0], tl[1], t, strength=tl[2], radius=light.TORCH_RADIUS * tl[3]))
    light.apply_darkness(c, cam, amb, lights=lights, t=t)
    cam.apply(c, t)
    env.draw_fungi_glow(c, t, "cavern", exclude=None if dark_mode else [_anger_bbox(pose, t)])
    if dark_mode:
        cx_, cy_ = pose.x, pose.y - 520.0 * pose.scale
        lv = light.light_at(cx_, cy_, amb, lights)
        lvl = max(lv)
        pose.light = clamp(0.1 + 0.95 * lvl, 0.26, 0.62)
        pose.tint, pose.tint_amt = (14, 34, 54), clamp(0.5 - 0.3 * lvl, 0.15, 0.5)
        pose.rim, pose.rim_color = 0.75, "#7FE0C8"
        pose.extra["rim_pos"] = (560.0, 600.0)
        A.draw(c, pose, t)
    if lurk is not None:
        C.draw_eyes(c, lurk, t)
    watch = crawler_watch(t)
    if watch is not None:
        C.draw_eyes(c, watch, t)
    if scur is not None:
        C.draw_eyes(c, scur, t)
    c.resetMatrix()
    light.vignette(c, 0.45)


# =========================================================================== motion-locked sfx
def sfx_events():
    ev = []
    n = 0

    def step(tk, gain=-12.0):
        nonlocal n
        ev.append({"name": STEP_NAMES[n % 3], "start": round(tk, 4), "gain_db": gain})
        n += 1

    for tk in WE[1:]:                    # WE[0] = the reveal plant (S1 reports nothing there; S2 does)
        step(tk)
    step(WE[0], -12.0)
    step(STOPE[1] - 0.05, -15.0)
    for tk in WS:
        step(tk, -14.0)
    step(STOPS[1] - 0.05, -16.0)
    ev.append({"name": "armor_shift", "start": round(SEARCH + 0.95, 4), "gain_db": -18.0})     # leans in
    ev.append({"name": "armor_shift", "start": round(EYES - 0.75, 4), "gain_db": -19.0})       # turns to look back
    for tk in WF:
        step(tk, -13.0)
    # stumble: the recovery stamp (stone_shift itself carries the slip)
    ev.append({"name": "armor_step_run", "start": round(lerp(STUMBLE[0], STUMBLE[1], 0.62), 4), "gain_db": -10.0})
    ev.append({"name": "armor_shift", "start": round(STUMBLE_END + 0.1, 4), "gain_db": -16.0})
    ev.append({"name": "armor_shift", "start": round(OVER + 0.05, 4), "gain_db": -20.0})       # the turn (quiet)
    ev.append({"name": "armor_shift", "start": round(CONT + 0.3, 4), "gain_db": -17.0})        # sword up
    for tk in WC:
        if tk < T1:
            step(tk, -16.0)              # careful, quiet steps on the heartbeat
    return sorted(ev, key=lambda e: e["start"])
