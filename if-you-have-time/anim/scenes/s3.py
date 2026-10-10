"""S3 - "Lights up" (BIBLE section 4, S3 - REVISION 2).

The symphony is over. The lounge lights come back up to normal over about a second (no flash, no jolt).
Rae sits on the bench, wet-eyed and very still; a slow blink. Quill, casual and pleasant: "So. How did you
like it?" A long beat - she stares ahead, sniffs, dabs one eye with a knuckle - and, in a tiny whisper,
"...pretty good." (the comedy is the gap between her face and her words). "Thank you. Here are the other
ones I made." - his palm comes up and eight holo-cards fan out above it; she slowly picks her mug back up.

render(canvas, t) is a pure function of absolute time t. The performances (rae_pose / quill_pose) run
continuously through every cut; each shot only picks a camera. Times derive from named beats / lines /
SFX in build/timeline.json. S2 hands over Rae seated at x 230 with her mug on the bench at (330, 960) and
Quill at rest (BIBLE section 9): both poses are read from anim.scenes.s2 at the boundary when it imports and
eased into this scene's performance over the first ~0.9 s (fallback: the BIBLE values).

The shared helpers (arm tracks, gaze, blinks, card fan, mug solver, camera helpers, room lighting) live here;
anim/scenes/s4.py and s5.py import them. The last shot (the presentation two-shot) runs on into S4 until the
kazoo starts: s4 renders it with present_cam().

Shot list (absolute times are only for orientation):
  A  s3 start -> q06-0.32       TWO-SHOT (medium-wide): stillness; the lights come up around them; a slow blink
  B  -> q06 end+0.2             MEDIUM Quill: "So. How did you like it?" (casual, head tilt)
  C  -> cards_appear-0.4        CLOSE-UP Rae: the long beat - stares ahead, knuckle dab, sniff; whispered
                                "...pretty good."; a small involuntary smile; "Thank you." lands on her face
  D  -> (S4) kazoo start        PRESENTATION TWO-SHOT: palm up, the eight cards fan out, No. 1 softly lit;
                                she looks up at them and slowly picks her mug up off the bench
"""
from __future__ import annotations

import math
from functools import lru_cache

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Track, auto_blink, beat, breathe, clamp, ease_in_out, ease_out, glow, lerp,
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


LUP = beat("lights_up")
CARDS = beat("cards_appear")
CARD2 = beat("card2")
Q06, Q06E = S("q06"), E("q06")
R10, R10E = S("r10"), E("r10")
Q07, Q07E = S("q07"), E("q07")
SNIFF = sfx_time("sniff", T0)               # two little inhales at ~+0.07 and ~+0.3
HOW = Q06 + 0.55                            # "...How did you like it?"
THANKS = Q07                                # "Thank you."
KZ0 = None                                  # (set below from the music cue: end of the presentation shot)
try:
    from anim.core import music_cue as _mc
    KZ0 = _mc("alt_kazoo")["start"]
except Exception:                           # pragma: no cover
    KZ0 = CARD2 + 3.0

# ---------------------------------------------------------------- cuts
CUT_Q = Q06 - 0.32                          # B  medium Quill (just before he speaks)
CUT_RCU = Q06E + 0.2                        # C  close-up Rae (the long beat)
CUT_FAN = CARDS - 0.4                       # D  presentation two-shot (his palm is already on its way up)
CUT_K = KZ0 + 0.1                           # (S4) end of the presentation shot: cut to Rae on the kazoo

# ---------------------------------------------------------------- geometry
FLOOR = float(env.FLOOR_Y)
SEAT_Y = float(env.BENCH_SEAT_Y)
SEAT_X, QX = 230.0, 545.0
MUG_SPOT = (330.0, SEAT_Y)                  # where S2 leaves the mug on the bench (BIBLE section 9)
A, QA = R.ARMS, Q.ARMS
PRESENT_POSE = Pose(x=QX, y=FLOOR, facing=-1.0, turn=0.35, arm_r=QA["present"], arm_l=QA["rest"])
FAN = Q.hand_pos(PRESENT_POSE, "r")         # holo-card fan anchor (shared with S4 / S5)


# =========================================================================== camera helpers
def cam_on(head, zoom, sx, sy):
    """Camera at `zoom` that puts stage point `head` at screen fraction (sx, sy)."""
    return Camera(head[0] + (0.5 - sx) * W / zoom, head[1] + (0.5 - sy) * H / zoom, zoom)


def _face_cam(fx_, fy_, z, sx, sy):
    """Camera at zoom z that puts stage point (fx_, fy_) at screen pixel (sx, sy)."""
    return Camera(fx_ + (W / 2 - sx) / z, fy_ + (H / 2 - sy) / z, z)


def drift(a: Camera, b: Camera, t, t0, t1, ease=ease_in_out):
    return Camera.lerp(a, b, ease(clamp((t - t0) / max(1e-6, t1 - t0))))


def nudge(cam: Camera, dx=0.0, dy=0.0, dz=1.0):
    return Camera(cam.cx + dx, cam.cy + dy, cam.zoom * dz)


def smoothed(fn, t, n=6, step=0.07):
    """Average of fn(t - i*step) - a soft follow for cameras."""
    xs = ys = 0.0
    for i in range(n):
        x, y = fn(t - i * step)
        xs += x
        ys += y
    return xs / n, ys / n


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


def bump(t, t0, dur):
    """Smooth 0 -> 1 -> 0 hump over [t0, t0 + dur] (sin^2)."""
    x = (t - t0) / dur
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return math.sin(math.pi * x) ** 2


def sniff_lift(t, t0):
    """The sniff SFX's two little inhales (~+0.07 and ~+0.3): 0..1 lift of the head / shoulders."""
    return max(bump(t, t0 - 0.02, 0.26), 0.8 * bump(t, t0 + 0.2, 0.3))


# =========================================================================== room lighting
LIGHT_UP = Track([(T0, 0.25), (LUP, 0.25), (LUP + 1.05, 1.0, "smooth")])


def lights_k(t):
    """0 (S2's dark symphony lighting) .. 1 (normal) as the lights come up."""
    return smoothstep((t - LUP) / 1.05)


def char_lighting(light=1.0, warm=0.0):
    """env.char_light, with the tint hue blended (env flips it at warm 0.5) - no one-frame colour jump."""
    d = env.char_light(light, warm)
    k = smoothstep(clamp(warm))
    d["tint"] = tuple(lerp(a, b, k) for a, b in zip((20, 30, 70), (70, 35, 10)))
    return d


# =========================================================================== holo-card fan (shared with S4 / S5)
FOCUS_POS = (366.0, 488.0)                  # where a selected card comes to rest in the two-shot (upper third)
FOCUS_SCALE = 0.84
# fx.card_fan_layout geometry: the default arc raised 60 units and closed 2-4 degrees at the ends, so the
# lowest card clears the top of Rae's hair puff (seated) while No. 8 clears Quill's forehead.
FAN_GEOM = dict(radius=300.0, center=(-26.0, 0.0), angles=(-50.0, 8.0), card_scale=0.36)


def draw_fan(c, t, progress, alpha=1.0, focus=None, states=None, wobble=None, fold=None, pops=None,
             dim=0.4, hidden=(), focus_pos=FOCUS_POS, focus_scale=FOCUS_SCALE, alphas=None):
    """The eight holo-cards fanned from the palm anchor FAN (fx.card_fan_layout geometry). focus: {number: 0..1}
    cards pulled to their focus position and enlarged (several may be in flight while one returns and the next
    comes out); the others dim. focus_pos: one (x, y) or {number: (x, y)}. states: {number: 0..1} glow.
    wobble / fold: {number: amount}. pops: {number: extra scale}. alphas: per-card alpha."""
    if alpha <= 0.003 or progress <= 0:
        return
    wobble = wobble or {}
    fold = fold or {}
    for (num, x, y, rot, scl, a, st) in fan_cards(progress, alpha, focus, states, pops, dim, hidden, focus_pos,
                                                  focus_scale, alphas):
        fx.draw_holo_card(c, t, x, y, scl, num, fx.CARD_TITLES.get(num, ""), fx.CARD_ICONS.get(num, "symphony"),
                          st, a, wobble=wobble.get(num, 0.0), fold=fold.get(num, 0.0), rot=rot)


def fan_cards(progress, alpha=1.0, focus=None, states=None, pops=None, dim=0.4, hidden=(), focus_pos=FOCUS_POS,
              focus_scale=FOCUS_SCALE, alphas=None):
    """Where draw_fan puts each card (same arguments): [(num, x, y, rot, scale, alpha, state)], back to front."""
    focus = {k: v for k, v in (focus or {}).items() if v > 0.0005}
    states = states or {}
    pops = pops or {}
    alphas = alphas or {}
    lay = fx.card_fan_layout(FAN[0], FAN[1], progress, **FAN_GEOM)
    fmax = max(focus.values()) if focus else 0.0
    order = sorted(lay, key=lambda L: focus.get(L[0], 0.0))
    out = []
    for (num, x, y, rot, scl, vis) in order:
        if num in hidden:
            continue
        f = ease_in_out(clamp(focus.get(num, 0.0)))
        fo = ease_in_out(clamp(fmax)) * (1.0 - f)            # how much another card has the spotlight
        if f > 0:
            fp = focus_pos.get(num, FOCUS_POS) if isinstance(focus_pos, dict) else focus_pos
            x = lerp(x, fp[0], f)
            y = lerp(y, fp[1], f) - 22.0 * math.sin(math.pi * f)   # a little lift on the way
            rot = lerp(rot, 0.0, f)
            scl = lerp(scl, focus_scale, f)
        scl *= 1.0 + pops.get(num, 0.0)
        a = alpha * vis * alphas.get(num, 1.0) * lerp(1.0, dim, fo)
        st = max(states.get(num, 0.0) * (1.0 - fo), f)
        out.append((num, x, y, rot, scl, a, st))
    return out


def card_corners(x, y, rot, scl, st=0.0):
    """Stage-space corners of the body of a card placed by fan_cards (fx.draw_holo_card: CARD_W x CARD_H at
    scale 1, +6 % when selected)."""
    sc = scl * (1 + 0.06 * ease_in_out(clamp(st)))
    hw, hh = fx.CARD_W / 2 * sc, fx.CARD_H / 2 * sc
    cs, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(x + px * cs - py * sn, y + px * sn + py * cs) for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def card_xy(num, progress=1.0):
    for L in fx.card_fan_layout(FAN[0], FAN[1], progress, **FAN_GEOM):
        if L[0] == num:
            return L[1], L[2]
    return FAN


def select_flash(c, t, t0, x, y, scale=1.0):
    """holo_select: a quick bright bloom at a card that is being selected."""
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


# =========================================================================== mug solver (shared with S4)
_SOLVED = {}


def solve_mug_arm(t_grab: float, target, body_fn, base=None):
    """Near-arm ArmPose (hand 'hold') whose held mug stands exactly on `target` (bottom centre) on the body
    body_fn(t_grab) (memoised)."""
    base = base or A["hold_mug"]
    key = (round(t_grab, 4), tuple(target), body_fn, base.shoulder, base.elbow, base.wrist, base.across)
    if key not in _SOLVED:
        _SOLVED[key] = _solve_mug_arm(t_grab, target, body_fn, base)
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


# =========================================================================== S2 -> S3 handoff
_NUM_FIELDS = ("x", "turn", "lean", "head_tilt", "head_nod", "head_turn", "look_x", "look_y", "pupil", "squint",
               "eye_wide", "brow_raise", "brow_worry", "brow_furrow", "smile", "smirk", "mouth_tremble", "tears",
               "eye_shine", "blush", "sniffle", "shoulders_up", "bounce", "glow")


def _s2_end():
    """(rae_pose, quill_pose, mug_xy, room) as S2 leaves them at the boundary, or Nones (S2 mid-edit / renamed).
    room: dict(swirl, wb, vign, rae, quill) - S2's window state, vignette and character light levels."""
    t = T0 - 1e-4
    try:
        from anim.scenes import s2
    except Exception:
        return None, None, None, None
    rp = qp = room = None
    try:
        if hasattr(s2, "_levels") and hasattr(s2, "_rae_pose"):
            lv = s2._levels(t)
            rp, qp = s2._rae_pose(t, lv), s2._quill_pose(t, lv)
            g = (lambda k, d: lv.get(k, d)) if isinstance(lv, dict) else (lambda k, d: getattr(lv, k, d))
            room = dict(light=float(g("room", 0.25)), swirl=float(g("swirl", 0.0)), wb=float(g("wb", 1.0)),
                        vign=float(g("vign", 0.0)), rae=g("rae", None), quill=g("quill", None))
        elif hasattr(s2, "rae_pose"):
            rp, qp = s2.rae_pose(t), s2.quill_pose(t)
    except Exception:
        rp = qp = room = None
    mug = None
    try:
        bm = s2._bench_mug(t) if hasattr(s2, "_bench_mug") else None
        if bm is not None:
            mug = (float(bm[0]), float(bm[1]))
    except Exception:
        mug = None
    if rp is not None and (abs(rp.x - SEAT_X) > 12.0 or rp.sit < 0.95 or getattr(rp, "kneel", 0.0) > 0.05):
        rp = room = None            # (S2 still in its old staging: follow the BIBLE row instead)
    return rp, qp, mug, room


S2_RAE, S2_QUILL, S2_MUG, S2_ROOM = _s2_end()
if S2_MUG is not None and math.hypot(S2_MUG[0] - MUG_SPOT[0], S2_MUG[1] - MUG_SPOT[1]) < 25.0:
    MUG_SPOT = S2_MUG
INHERIT = 0.9                               # seconds over which S2's last pose eases into this scene's
_ROOM0 = S2_ROOM or dict(light=0.25, swirl=0.0, wb=1.0, vign=0.0, rae=None, quill=None)


def room(t):
    """(light, swirl, window_bright, vignette): S2's closing state (galaxy still in the window, dark room, soft
    vignette) brought back to the normal lounge as the lights come up."""
    k = lights_k(t)
    return (lerp(_ROOM0["light"], 1.0, k), _ROOM0["swirl"] * (1.0 - k), lerp(_ROOM0["wb"], 1.0, k),
            _ROOM0["vign"] * (1.0 - k))


def s3_char_light(who, t):
    """Character light fields: S2's own levels at the boundary -> the normal room (env.char_light(1))."""
    k = lights_k(t)
    end = char_lighting(1.0)
    st = _ROOM0.get(who)
    if not st:
        st = char_lighting(0.25)
    out = dict(end)
    out["light"] = lerp(float(st["light"]), end["light"], k)
    out["tint_amt"] = lerp(float(st["tint_amt"]), end["tint_amt"], k)
    out["rim"] = lerp(float(st["rim"]), end["rim"], k)
    out["tint"] = tuple(st.get("tint", end["tint"]))
    out["rim_color"] = st.get("rim_color", end["rim_color"])
    return out


def inherit(cur: Pose, prev: Pose | None, t: float, t0: float = T0, dur: float = INHERIT) -> Pose:
    """Ease from `prev` (the previous scene's last pose) into `cur` over [t0, t0 + dur]."""
    if prev is None:
        return cur
    w = 1.0 - smoothstep((t - t0) / dur)
    if w <= 0.0:
        return cur
    kw = {}
    for f in _NUM_FIELDS:
        a, b = getattr(prev, f), getattr(cur, f)
        if a is None or b is None:
            continue
        kw[f] = lerp(b, a, w)
    for f in ("lid_l", "lid_r"):
        a, b = getattr(prev, f), getattr(cur, f)
        if a is not None and b is not None:
            kw[f] = lerp(b, a, w)
    kw["arm_r"] = ArmPose.blend(cur.arm_r, prev.arm_r, w)
    kw["arm_l"] = ArmPose.blend(cur.arm_l, prev.arm_l, w)
    return cur.copy(**kw)


# =========================================================================== Rae: S3 performance
CHEST = arm(A["hand_on_chest"], wrist=10.0)                       # (fallback for S2's last arm pose)
LAP_L = ArmPose(shoulder=3.0, elbow=46.0, wrist=8.0, hand="relaxed")
LAP_R = ArmPose(shoulder=6.0, elbow=58.0, wrist=4.0, hand="relaxed", across=0.15)
HOLD = A["hold_mug"]
DAB = ArmPose(shoulder=88.0, elbow=136.0, wrist=22.0, hand="fist", across=0.11)   # knuckle at the near eye's corner
DAB_UP = ArmPose(shoulder=62.0, elbow=124.0, wrist=14.0, hand="fist", across=0.14)

R_ARM0 = S2_RAE.arm_r if S2_RAE is not None else CHEST
L_ARM0 = S2_RAE.arm_l if S2_RAE is not None else LAP_L
TEARS0 = (S2_RAE.tear_l, S2_RAE.tear_r) if S2_RAE is not None else (1.0, 1.0)

DAB0 = CUT_RCU + 0.08                       # the near hand leaves her chest ...
DAB1 = DAB0 + 0.36                          # ... knuckle at the corner of her eye
DAB2 = DAB1 + 0.34                          # (two small presses)
DAB3 = DAB2 + 0.5                           # ... back down in her lap
GRAB_T = CARDS + 1.02                       # fingers close on the mug (bench -> hand)
REACH_T = GRAB_T - 0.5
SMILE_T = R10E + 0.12                       # the small involuntary smile after "...pretty good."


def _rae_tracks():
    d = {}
    # ---------------- body: seated, very still
    d["lean"] = Track([(T0, 1.5), (LUP + 0.6, 1.5), (LUP + 1.5, 0.5), (SNIFF, 0.5), (SNIFF + 0.4, 1.0),
                       (R10 - 0.3, 1.5), (R10E + 0.5, 2.5), (CARDS, 2.0), (CARDS + 0.4, -0.5),
                       (REACH_T, 0.0), (GRAB_T - 0.1, 5.0), (GRAB_T + 0.5, 2.0), (T1 + 1, 2.0)])
    d["shoulders"] = Track([(T0, 0.08), (Q06 + 0.6, 0.08), (Q06E + 0.3, 0.12), (SNIFF + 0.6, 0.06),
                            (R10E + 0.4, 0.03), (CARDS, 0.06), (CARDS + 0.3, 0.14), (T1 + 1, 0.1)])
    d["turn"] = Track([(T0, 0.3), (T1 + 1, 0.3)])
    # ---------------- head
    d["nod"] = Track([(T0, 0.12), (LUP + 0.4, 0.12), (LUP + 1.6, 0.06), (Q06 + 0.3, 0.06), (HOW + 0.3, 0.1),
                      (CUT_RCU, 0.1), (DAB1, 0.16), (DAB3, 0.06), (R10, 0.02), (R10E, 0.06), (SMILE_T + 0.6, 0.0),
                      (THANKS + 0.4, 0.04), (CARDS + 0.1, 0.04), (CARDS + 0.5, -0.12), (REACH_T, -0.08),
                      (GRAB_T, 0.14), (GRAB_T + 0.6, -0.08), (T1, -0.1), (T1 + 1, -0.1)])
    d["tilt"] = Track([(T0, 3.0), (LUP + 1.0, 3.0), (Q06E, 2.0), (DAB1, 5.0), (DAB3, 3.0), (R10E, 4.5),
                       (SMILE_T + 0.8, 6.0), (THANKS + 0.5, 4.0), (CARDS + 0.5, 1.0), (T1, 0.0), (T1 + 1, 0.0)])
    d["hturn"] = Track([(T0, 0.0), (THANKS + 0.1, 0.0), (THANKS + 0.6, 0.04), (CARDS + 0.4, 0.02),
                        (T1 + 1, 0.02)])
    # ---------------- eyes: wet, soft, slow blinks
    d["lid"] = Track([(T0, 0.84), (LUP + 1.2, 0.88), (Q06 + 0.8, 0.9), (Q06E + 0.4, 0.88), (SNIFF + 0.5, 0.84),
                      (R10, 0.86), (R10E + 0.2, 0.86), (SMILE_T + 0.5, 0.82), (THANKS + 0.4, 0.88),
                      (CARDS + 0.3, 0.96), (CARDS + 1.2, 0.92), (T1 + 1, 0.92)])
    d["blinks"] = [(LUP + 0.42, 0.62),                          # a slow blink as the light comes up
                   (Q06 - 0.7, 0.4), (HOW + 0.35, 0.3), (SNIFF + 0.4, 0.42), (R10E + 0.3, 0.5),
                   (THANKS + 0.55, 0.55), (CARDS + 0.65, 0.42), (GRAB_T + 0.35, 0.3)]
    d["pupil"] = Track([(T0, 1.18), (LUP + 1.0, 1.05), (CARDS, 1.05), (CARDS + 0.6, 1.15), (T1 + 1, 1.12)])
    d["squint"] = Track([(T0, 0.12), (SNIFF, 0.12), (SNIFF + 0.15, 0.3), (SNIFF + 0.45, 0.14),
                         (SMILE_T, 0.14), (SMILE_T + 0.6, 0.24), (THANKS + 0.6, 0.16), (CARDS + 0.5, 0.06),
                         (T1 + 1, 0.06)])
    # gaze (screen space): +x toward Quill, -y up
    MID = (0.16, -0.08)
    QU = (0.58, -0.42)
    UPF = (0.3, -0.78)                      # the fan above them
    d["gaze"] = gaze([
        (T0, (0.18, -0.02)),
        (LUP + 0.75, MID, 0.4),                                  # (eyes settle as the room comes back)
        (Q06 + 0.35, (0.24, -0.1), 0.3),                         # hears him ... does not look
        (DAB0 + 0.1, (0.12, 0.0), 0.25),
        (DAB3 + 0.1, MID, 0.3),
        (R10E + 0.4, (0.2, -0.06), 0.4),
        (THANKS + 0.15, QU, 0.14),                               # "Thank you." - a glance at him
        (CARDS + 0.05, (0.4, -0.55), 0.14), (CARDS + 0.35, UPF, 0.3),     # the fan opening
        (REACH_T - 0.15, (0.35, 0.55), 0.16),                    # the mug
        (GRAB_T + 0.25, (0.36, -0.72), 0.2),                     # back up to the cards
        (GRAB_T + 1.2, (0.2, -0.76), 0.4),
    ])
    # ---------------- brows / mouth: soft, wet, understated
    d["brow_raise"] = Track([(T0, 0.18), (LUP + 1.0, 0.14), (HOW + 0.4, 0.2), (CUT_RCU, 0.16), (SNIFF, 0.2),
                             (R10, 0.16), (SMILE_T + 0.5, 0.22), (THANKS + 0.4, 0.2), (CARDS, 0.22),
                             (CARDS + 0.5, 0.42), (GRAB_T + 0.6, 0.32), (T1 + 1, 0.32)])
    d["worry"] = Track([(T0, 0.55), (LUP + 1.0, 0.5), (SNIFF, 0.58), (R10, 0.55), (SMILE_T + 0.6, 0.42),
                        (CARDS, 0.4), (CARDS + 0.6, 0.48), (T1 + 1, 0.45)])
    d["furrow"] = Track([(T0, 0.0), (SNIFF, 0.0), (SNIFF + 0.15, 0.12), (SNIFF + 0.6, 0.0), (T1 + 1, 0.0)])
    d["open"] = Track([(T0, 0.05), (LUP + 1.0, 0.04), (R10 - 0.2, 0.02), (R10E, 0.02), (R10E + 0.3, 0.04),
                       (CARDS + 0.2, 0.04), (CARDS + 0.5, 0.1), (CARDS + 1.5, 0.06), (T1 + 1, 0.06)])
    d["smile"] = Track([(T0, 0.08), (LUP + 1.0, 0.06), (SNIFF, 0.02), (R10E, 0.04), (SMILE_T, 0.05),
                        (SMILE_T + 0.6, 0.24), (THANKS + 0.3, 0.2), (CARDS, 0.14), (CARDS + 0.6, 0.1),
                        (T1 + 1, 0.12)])
    d["tremble"] = Track([(T0, 0.14), (LUP + 1.5, 0.1), (SNIFF, 0.16), (R10E + 0.4, 0.12), (SMILE_T + 0.6, 0.2),
                          (THANKS + 0.6, 0.1), (CARDS + 0.5, 0.06), (T1 + 1, 0.06)])
    d["tears"] = Track([(T0, 0.66), (LUP + 1.2, 0.62), (DAB2, 0.6), (DAB2 + 0.05, 0.5), (R10E, 0.58),
                        (SMILE_T + 0.6, 0.66), (CARDS + 1.0, 0.56), (T1 + 1, 0.5)])
    d["shine"] = Track([(T0, 0.6), (LUP + 1.2, 0.45), (SMILE_T + 0.6, 0.6), (CARDS, 0.5), (CARDS + 0.5, 0.75),
                        (T1 + 1, 0.6)])
    d["blush"] = Track([(T0, 0.18), (R10, 0.2), (R10E + 0.5, 0.26), (CARDS + 1.0, 0.2), (T1 + 1, 0.2)])
    d["sniffle"] = Track([(T0, 0.34), (SNIFF, 0.36), (SNIFF + 0.4, 0.42), (T1 + 1, 0.38)])
    # ---------------- arms
    d["arm_r"] = ArmSeq([
        (T0, R_ARM0), (DAB0, R_ARM0), (DAB1 - 0.12, DAB_UP, "io"), (DAB1, DAB, "out"),
        (DAB1 + 0.14, arm_add(DAB, -3.0, 3.0, 6.0), "io"), (DAB2 - 0.1, DAB, "io"),     # two small presses
        (DAB2 + 0.08, arm_add(DAB, -4.0, 2.0, 8.0), "io"),
        (DAB2 + 0.3, arm(DAB_UP, shoulder=40.0, elbow=110.0, hand="relaxed"), "io"), (DAB3, LAP_R, "io"),
        (REACH_T, LAP_R),
    ])
    d["arm_l"] = ArmSeq([(T0, L_ARM0), (T0 + INHERIT, LAP_L, "io"), (T1 + 1, LAP_L)])
    return d


_RT = _rae_tracks()


def _rae_body(t) -> Pose:
    """Rae without face / near arm (used by the mug pick-up solver)."""
    d = _RT
    return Pose(x=SEAT_X, y=FLOOR, facing=1.0, turn=d["turn"](t), sit=1.0, seat_y=SEAT_Y,
                lean=d["lean"](t), shoulders_up=d["shoulders"](t), breath=breathe(t, 0.2, 2), arm_l=d["arm_l"](t))


def _rae_arm_r(t):
    if t < REACH_T:
        return _RT["arm_r"](t)
    grab = solve_mug_arm(GRAB_T, MUG_SPOT, _rae_body)
    reach = arm(grab, hand="open", shoulder=grab.shoulder + 6.0, elbow=grab.elbow - 6.0)
    if t < GRAB_T - 0.12:
        return ArmPose.blend(LAP_R, reach, ease_in_out((t - REACH_T) / (GRAB_T - 0.12 - REACH_T)))
    if t < GRAB_T:
        return ArmPose.blend(reach, grab, ease_in_out((t - GRAB_T + 0.12) / 0.12))
    if t < GRAB_T + 0.14:
        return grab
    return ArmPose.blend(grab, HOLD, ease_in_out((t - GRAB_T - 0.14) / 0.62))


def rae_mug_on_bench(t):
    """S2 left the mug on the bench; she picks it up at GRAB_T."""
    return t < GRAB_T


def _sniff(t):
    return sniff_lift(t, SNIFF)


def rae_pose(t: float) -> Pose:
    d = _RT
    lid = d["lid"](t) * (1.0 - blink_amt(t, d["blinks"]))
    lx, ly = d["gaze"](t)
    lx += 0.02 * noise1(t * 1.3, 9)
    ly += 0.016 * noise1(t * 1.1, 13)
    mo, mr = mouth("rae", t)
    sn = _sniff(t)
    nod = d["nod"](t) + 0.025 * noise1(t * 0.4, 3) - 0.07 * sn
    tilt = d["tilt"](t) + 1.0 * noise1(t * 0.33, 5)
    # the near trail goes under her knuckle (reset at the dab, which covers it)
    tear_r = TEARS0[1] if t < DAB1 + 0.05 else 0.0
    p = Pose(
        x=SEAT_X, y=FLOOR, facing=1.0, turn=d["turn"](t), sit=1.0, seat_y=SEAT_Y,
        lean=d["lean"](t), head_tilt=tilt, head_nod=nod, head_turn=d["hturn"](t) + 0.012 * noise1(t * 0.45, 4),
        breath=breathe(t, 0.2, 2) + 0.6 * sn,
        lid_l=lid, lid_r=lid * (0.99 + 0.01 * noise1(t * 0.7, 3)), look_x=lx, look_y=ly, pupil=d["pupil"](t),
        squint=d["squint"](t), eye_wide=0.0,
        brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t), brow_furrow=d["furrow"](t),
        # the whisper: a tiny mouth (no big shapes)
        mouth_open=d["open"](t) + 0.42 * mo, mouth_round=clamp(0.6 * mr), smile=d["smile"](t),
        mouth_tremble=d["tremble"](t), tears=d["tears"](t), tear_l=TEARS0[0], tear_r=tear_r,
        eye_shine=d["shine"](t), blush=d["blush"](t), sniffle=d["sniffle"](t) + 0.1 * sn,
        shoulders_up=d["shoulders"](t) + 0.12 * sn,
        arm_r=_rae_arm_r(t), arm_l=d["arm_l"](t), mug=None if rae_mug_on_bench(t) else "r",
        **s3_char_light("rae", t),
    )
    return inherit(p, S2_RAE, t)


# =========================================================================== Quill: S3 performance
GEST = QA["gesture_small"]
PRESENT = QA["present"]
QREST = QA["rest"]
BEHIND = QA["behind_back"]
RAISE_T0 = CARDS - 0.62                      # the palm comes up as the cards spring out
RAE_S = (-0.42, 0.22)                        # his gaze on her (seated)
CARDV = (-0.62, 0.08)


def _quill_tracks():
    d = {}
    d["arm_r"] = ArmSeq([
        (T0, QREST), (RAISE_T0, QREST), (RAISE_T0 + 0.16, arm_add(QREST, -2.0, 4.0), "io"),
        (CARDS - 0.02, arm_add(PRESENT, 3.0, 6.0, -6.0), "io"), (CARDS + 0.35, PRESENT, "io"),
    ])
    # the other hand stays behind his back (S2 leaves it there); without S2's pose it goes there while she is in
    # close-up (off screen): a maitre d' with the menu
    l0 = BEHIND if (S2_QUILL is not None and S2_QUILL.arm_l.behind > 0.5) else QREST
    d["arm_l"] = ArmSeq([(T0, l0), (R10E + 0.3, l0), (R10E + 1.0, BEHIND, "io")])
    d["tilt"] = Track([(T0, 3.0), (LUP + 1.0, 3.0), (Q06, 2.0), (HOW, 2.5), (HOW + 0.5, 7.0), (Q06E + 0.6, 6.0),
                       (R10, 6.0), (R10E + 0.2, 4.0), (THANKS, 3.0), (CARDS, 2.0), (CARDS + 1.0, 4.0),
                       (T1, 6.0), (T1 + 1, 6.0)])
    d["nod"] = Track([(T0, 0.0), (LUP + 1.2, 0.0), (Q06 + 0.02, 0.0), (Q06 + 0.18, -0.08, "out"), (Q06 + 0.5, 0.0),
                      (R10E + 0.4, 0.0), (THANKS + 0.05, 0.0), (THANKS + 0.25, -0.12, "out"),     # "Thank you."
                      (THANKS + 0.7, 0.0), (CARDS, 0.06), (CARDS + 0.4, 0.0), (T1 + 1, 0.0)])
    d["hturn"] = Track([(T0, 0.0), (CARDS + 0.2, 0.0), (CARDS + 0.7, -0.06), (CARDS + 1.6, 0.0), (T1 + 1, 0.0)])
    d["brow"] = Track([(T0, 0.08), (Q06, 0.08), (HOW + 0.3, 0.22), (Q06E + 0.4, 0.14), (R10E + 0.1, 0.14),
                       (R10E + 0.4, 0.2), (THANKS + 0.6, 0.1), (CARDS, 0.16), (T1 + 1, 0.14)])
    d["smile"] = Track([(T0, 0.04), (Q06, 0.04), (HOW + 0.4, 0.08), (Q06E + 0.5, 0.05), (THANKS, 0.06),
                        (THANKS + 0.4, 0.12), (CARDS + 0.5, 0.06), (T1 + 1, 0.06)])
    d["glow"] = Track([(T0, 0.18), (LUP + 1.0, 0.14), (CARDS - 0.1, 0.14), (CARDS + 0.1, 0.5),
                       (CARDS + 1.2, 0.2), (T1 + 1, 0.18)])
    d["gaze"] = gaze([
        (T0, RAE_S),
        (LUP + 1.2, (-0.38, 0.24), 0.12),
        (Q06 + 0.1, RAE_S),
        (R10E + 0.35, (-0.44, 0.2)),
        (CARDS - 0.3, (-0.3, 0.55)), (CARDS + 0.15, (-0.55, 0.12), 0.2),    # palm -> the fan opening
        (CARDS + 0.7, (-0.72, 0.0), 0.3),
        (CARDS + 1.4, RAE_S),                                               # back to her
    ], dur=0.09)
    return d


_QT = _quill_tracks()


def quill_pose(t: float) -> Pose:
    d = _QT
    mo, mr = mouth("quill", t)
    blink = auto_blink(t, seed=0, rate=4.6, robotic=True)
    lx, ly = d["gaze"](t)
    p = Pose(
        x=QX, y=FLOOR, facing=-1.0, turn=0.35,
        head_turn=d["hturn"](t), head_nod=d["nod"](t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=d["tilt"](t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=blink, lid_r=blink, look_x=lx, look_y=ly, brow_raise=d["brow"](t), smile=d["smile"](t),
        mouth_open=0.9 * mo, mouth_round=mr, glow=d["glow"](t),
        arm_r=d["arm_r"](t), arm_l=d["arm_l"](t), **s3_char_light("quill", t),
    )
    if S2_QUILL is not None:
        p = inherit(p, S2_QUILL.copy(lid_l=None, lid_r=None), t)
    return p


# =========================================================================== fan state
FAN_OPEN = Track([(CARDS - 0.04, 0.0), (CARDS + 1.3, 1.0, "lin")])
CARD1_GLOW = Track([(CARDS + 0.9, 0.0), (CARDS + 1.6, 0.5, "io")])      # No. 1: the one she heard


def draw_fan_s3(c, t):
    p = FAN_OPEN(t)
    if p <= 0:
        return
    draw_fan(c, t, p, states={1: CARD1_GLOW(t)})


# =========================================================================== cameras
@lru_cache(maxsize=1)
def seat_face():
    return R.head_center(Pose(x=SEAT_X, y=FLOOR, facing=1.0, turn=0.3, sit=1.0, seat_y=SEAT_Y))


QFACE = Q.head_center(Pose(x=QX, y=FLOOR, facing=-1.0, turn=0.35))

TWO_A = Camera(392.0, 742.0, 1.12)          # A  the room, both of them, the bench and the window
TWO_B = Camera(392.0, 736.0, 1.15)
QMED_A = cam_on(QFACE, 1.9, 0.45, 0.37)     # B  her puff stays out of frame left
QMED_B = nudge(QMED_A, -1.0, -2.0, 1.03)
PRES_A = Camera(358.0, 652.0, 1.24)         # D  presentation two-shot (runs on into S4)
PRES_B = Camera(354.0, 642.0, 1.29)


def _rae_head(t):
    return R.head_center(rae_pose(t))


def present_cam(t):
    """D: the presentation two-shot - from the cut before cards_appear until the kazoo starts (S4)."""
    return drift(PRES_A, PRES_B, t, CUT_FAN, CUT_K)


def camera(t: float) -> Camera:
    if t < CUT_Q:                                           # A  two-shot: the lights come up
        return drift(TWO_A, TWO_B, t, T0, CUT_Q)
    if t < CUT_RCU:                                         # B  medium Quill
        return drift(QMED_A, QMED_B, t, CUT_Q, CUT_RCU)
    if t < CUT_FAN:                                         # C  close-up Rae: slow push, soft follow
        fs = seat_face()
        u = clamp((t - CUT_RCU) / (CUT_FAN - CUT_RCU))
        hx, hy = smoothed(_rae_head, t, 5, 0.1)
        z = lerp(2.75, 2.98, ease_in_out(u))
        return _face_cam(lerp(fs[0], hx, 0.45), lerp(fs[1], hy, 0.45), z, 344.0, 520.0)
    return present_cam(t)                                   # D  presentation two-shot


def shot_name(t):
    for name, b in (("two", CUT_Q), ("quill_med", CUT_RCU), ("rae_cu", CUT_FAN)):
        if t < b:
            return name
    return "present"


# =========================================================================== render
def _draw_bench_mug(c, rp):
    """Same mug draw as S2's ending (lit with Rae's light + contact shadow); plain mug as a fallback."""
    try:
        from anim.scenes import s2
        s2._draw_bench_mug(c, (MUG_SPOT[0], MUG_SPOT[1], 1.0, 0.0, False), rp)
    except (ImportError, AttributeError):
        R.draw_mug(c, MUG_SPOT[0], MUG_SPOT[1], 1.0, 0.0, False)


def draw_stage(c, t, cam, rp, qp, mug_on_bench, fan_fn, light=1.0, swirl=0.0, wb=1.0):
    """Lounge -> Quill -> Rae -> mug on bench -> lounge front -> holo-cards (stage space).

    The bench mug is drawn in front of Rae's thigh, as S2 leaves it, so the S2->S3 cut doesn't pop."""
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, t, light=light, swirl=swirl, window_bright=wb)
    Q.draw(c, qp, t)
    R.draw(c, rp, t)
    if mug_on_bench:
        _draw_bench_mug(c, rp)
    env.draw_lounge_front(c, t, light=light)
    if fan_fn is not None:
        fan_fn(c, t)
    c.restore()


def _fan_fx(c, t):
    palm_burst(c, t, CARDS, FAN[0], FAN[1])
    draw_fan_s3(c, t)


def render(canvas, t):
    light, swirl, wb, vign = room(t)
    draw_stage(canvas, t, camera(t), rae_pose(t), quill_pose(t), rae_mug_on_bench(t), _fan_fx, light, swirl, wb)
    if vign > 0.003:
        canvas.resetMatrix()
        fx.draw_vignette(canvas, vign)
