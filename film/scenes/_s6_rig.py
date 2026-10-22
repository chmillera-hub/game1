"""_s6_rig.py -- Scene 6's draw-scoped adjustments to the library rigs (dragon and gnome).

Scene-local, like _s6_eye: each patch is installed only around this scene's own draw calls
(dragon_patch() / gnome_patch() context managers) and restored at once; the library is not
edited and other scenes never see these. They rely only on the documented pose/Arm API plus
the solver/skeleton entry points the scene already wraps.

1. ARM HAND-OFFS WITHOUT ELBOW POPS (dragon and gnome)
   The library picks an arm's IK pole from the gesture NAME ("rest" has its own pole, every
   other gesture a shared one). A blend Arm(g, amt, prev=p) therefore starts, at amt ~ 0, at
   p's TARGET but with g's POLE: every hand-off between "rest" and another gesture swung the
   elbow round the shoulder-wrist axis on a single frame (and re-aimed the hand, which follows
   the forearm). pole_blend() keeps the blended wrist target and carries the elbow round that
   axis from the side p's pole puts it on to the side g's pole puts it on, by the same eased u
   as the target blend -- so amt 0 is exactly p's pose and amt 1 exactly g's.

2. HAND ANGLE WHILE THE FOREARM POINTS AT THE LENS (dragon)
   The hand's screen angle follows the projected forearm. When a blend swings the forearm
   end-on to the camera, that 2D direction is undefined and the hand spun ~180 degrees on one
   frame (the far hand reaching for the open book). While the projected forearm is short, the
   hand's screen angle is eased between the two end poses' angles instead (the short way).

3. THE DRAGON'S SKELETON (per draw: RIG["shrug"], RIG["feet"])
   shrug  hunch units added to the SHOULDERS ONLY (coat shoulders and upper back, wing roots,
          the arms' shoulder joints) after the head and neck are placed: his shoulders can
          shake with a held-in laugh while his head stays steady (in the library, hunch and
          lean carry the head with them).
   feet   {side: (u, lift)} overrides the seated feet: u 0 = where they stood (planted under
          him), 1 = the library's seated place; lift raises the foot (body px). Lets the
          scene keep the feet planted while he lowers himself and then step them forward once
          the bench has his weight, instead of sliding them over the gravel.
"""

import contextlib
import math
from dataclasses import replace

from film.lib import core
from film.lib.characters import base as B
from film.lib.characters import dragon as _DR
from film.lib.characters import gnome as _GN

RIG = {"shrug": 0.0, "feet": None}

_BASE = {"dragon_solve": _DR._solve_arm, "dragon_skel": _DR._skeleton, "gnome_solve": _GN._solve_arm}


def _wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _perp_dir(p, sh, n):
    """Unit direction of p - sh with its component along n removed (None if degenerate)."""
    v = B.v_sub(p, sh)
    v = B.v_sub(v, B.v_mul(n, B.v_dot(v, n)))
    L = B.v_len(v)
    return None if L < 1e-6 else B.v_mul(v, 1.0 / L)


def _rotate_about(v, n, ang):
    """Rodrigues: v rotated by ang about the unit axis n."""
    c, s = math.cos(ang), math.sin(ang)
    k = B.v_cross(n, v)
    d = B.v_dot(n, v)
    return B.v_add(B.v_add(B.v_mul(v, c), B.v_mul(k, s)), B.v_mul(n, d * (1.0 - c)))


STEER_ALWAYS = set()          # gesture names whose blends ease the hand's screen angle all the way


def pole_blend(base, upper, fore, steer=False):
    """A solver wrapping the library's _solve_arm(q, S, side, arm): see the module doc (1, 2).
    Gestures named in STEER_ALWAYS (as gesture or prev) ease the hand's screen angle over the
    whole blend, not only while the forearm is end-on (a reach whose hand turns right round)."""

    def solve(q, S, side, arm):
        A = base(q, S, side, arm)
        amt = arm.amt
        if amt >= 1.0 or arm.prev == arm.gesture or arm.target is not None or getattr(arm, "screen", None) is not None:
            return A
        u = core.inout_sine(core.clamp(amt))
        sh, wr = A["sh"], A["wr"]
        axis = B.v_sub(wr, sh)
        dist = B.v_len(axis)
        if dist < 1e-6:
            return A
        n = B.v_mul(axis, 1.0 / dist)
        # the elbow sides the two gestures' poles choose, for this very wrist
        Ap = base(q, S, side, replace(arm, gesture=arm.prev, amt=1.0, target=wr))
        Ag = base(q, S, side, replace(arm, amt=1.0, target=wr))
        dp, dg = _perp_dir(Ap["el"], sh, n), _perp_dir(Ag["el"], sh, n)
        if dp is not None and dg is not None:
            ang = math.atan2(B.v_dot(B.v_cross(dp, dg), n), B.v_dot(dp, dg))
            if abs(ang) > 1e-4:
                d = _rotate_about(dp, n, ang * u)
                a_len = B.v_dot(B.v_sub(A["el"], sh), n)          # the elbow circle, from the solve
                r = B.v_len(B.v_sub(B.v_sub(A["el"], sh), B.v_mul(n, a_len)))
                A["el"] = B.v_add(B.v_add(sh, B.v_mul(n, a_len)), B.v_mul(d, r))
        if steer:
            _steer_hand(q, S, side, arm, A, u, base, fore)
        return A

    return solve


def _screen_hand(q, A, k):
    e, w = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    return math.atan2(w[1] - e[1], w[0] - e[0]) + A["hang"] * k, math.hypot(w[0] - e[0], w[1] - e[1])


def _steer_hand(q, S, side, arm, A, u, base, fore):
    k = (1.0 if side < 0 else -1.0) * (1.0 if q.yaw >= 0 else -1.0)
    a_nat, flen = _screen_hand(q, A, k)
    w = 1.0 - core.smoothstep(0.32, 0.6, flen / fore)
    if arm.gesture in STEER_ALWAYS or arm.prev in STEER_ALWAYS:
        w = 1.0
    if w <= 0.0:
        return
    a_p, _ = _screen_hand(q, base(q, S, side, replace(arm, gesture=arm.prev, amt=1.0)), k)
    a_g, _ = _screen_hand(q, base(q, S, side, replace(arm, amt=1.0)), k)
    want = a_p + _wrap(a_g - a_p) * u
    final = a_nat + _wrap(want - a_nat) * w
    e, wr = q.proj.xy(A["el"]), q.proj.xy(A["wr"])
    A["hang"] = (final - math.atan2(wr[1] - e[1], wr[0] - e[0])) * k


_dragon_solve = pole_blend(lambda *a: _BASE["dragon_solve"](*a), _DR.UPPER_ARM, _DR.FOREARM, steer=True)
_gnome_solve = pole_blend(lambda *a: _BASE["gnome_solve"](*a), _GN.UPPER_ARM, _GN.FOREARM)


def _dragon_skeleton(pose, t, sit, seat_h):
    S = _BASE["dragon_skel"](pose, t, sit, seat_h)
    d = RIG["shrug"]
    if d:
        S["hunch"] = S["hunch"] + d                     # the coat's shoulders + upper back, the wing roots
        off = B.m_vec(S["R"], (0.0, 12.0 * d, 14.0 * d))  # the arms' shoulder joints, as hunch moves them
        S["shoulders"] = {s: B.v_add(p, off) for s, p in S["shoulders"].items()}
    feet = RIG["feet"]
    if feet is not None:
        pole_y = core.lerp(0.15, -0.35, core.smooth(sit))
        for f in S["feet"]:
            s = f["side"]
            u, lift = feet.get(s, (1.0, 0.0))
            stand = (s * (_DR.HIP_W + 2.0), -_DR.ANKLE_H, 2.0)
            seat = (s * (_DR.HIP_W + 9.0), -_DR.ANKLE_H, 66.0 + 0.28 * seat_h)
            a = B.v_lerp(stand, seat, core.clamp(u))
            a = (a[0], a[1] - lift, a[2])
            knee, ank = B.ik3(f["hip"], a, _DR.THIGH, _DR.SHIN, (s * 0.15, pole_y, 1.0))
            f["knee"], f["ankle"] = knee, ank
        S["knee"] = [S["feet"][0]["knee"], S["feet"][1]["knee"]]
    return S


@contextlib.contextmanager
def dragon_patch(shrug=0.0, feet=None):
    """Install the scene's arm solver and skeleton around one ch.draw_dragon call."""
    old = (_DR._solve_arm, _DR._skeleton)
    RIG["shrug"], RIG["feet"] = shrug, feet
    _DR._solve_arm, _DR._skeleton = _dragon_solve, _dragon_skeleton
    try:
        yield
    finally:
        _DR._solve_arm, _DR._skeleton = old
        RIG["shrug"], RIG["feet"] = 0.0, None


@contextlib.contextmanager
def gnome_patch():
    """Install the scene's arm solver around one ch.draw_gnome / ch.gnome_rig_at call."""
    old = _GN._solve_arm
    _GN._solve_arm = _gnome_solve
    try:
        yield
    finally:
        _GN._solve_arm = old
