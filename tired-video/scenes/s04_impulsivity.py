"""s04 — Impulsivity, the tripwire (living room). Music "sneaky".

Shot list (cue names from script.json; all timing derived from info):
  S1  lift/reveal  low CU: Emb in a heap under the broken window lifts his head
                   (glasses crooked), huge paws by his face; camera tilts up to
                   Impulsivity's frozen derp grin. Name tag IMPULSIVITY.
  S2  s04_l01..peek  two-shot, Emb sitting on the floor: eyes widen, pupils
                   shrink, blush drains; "It's gonna eat me" -> cover_eyes;
                   peek with one eye. Slow push-in.
  S3  derp         Impulsivity CU, frozen + panting; a fly lands on its nose.
  S4  s04_l03      two-shot: Emb slowly rises (eyes locked on it), blindly
                   grabs the cage, "easy" palm.
  S5  tiptoe       Emb tiptoes behind it; ONE of its eyes slowly tracks him.
                   He notices, freezes mid-step, then carries on.
  S6  plates       lifts the top plate, peeks under, sets it down.
  S7  drawer       slides the drawer open, peeks, closes it; glance back.
  S8  table        crouches to look under the dining table; scratch -> head snaps up.
  S9  stairs       camera pans up to the landing: a small tailed shadow slides
                   along the wall.
  S10 s04_l04      CU: "Upstairs." (whisper) + gulp.
"""
import math

import cairocffi as cairo

from engine import core, sets, props, human, creatures, fx
from engine.core import (tween, state_at, seg, clamp, lerp, smoothstep, ease_out,
                         ease_in_out, ease_out_back, noise1)
from engine.human import POSES, A
from audio import sfx

M = sets.LIVING_MARKS
WHO = "embar"
ES = 0.75                       # Embarrassment (set char_scale)
IMP_X, IMP_Y, IMP_S = 660, 1590, 1.12
CAGE_S = 0.45
CAGE_H = 278 * CAGE_S           # handle top -> feet
FRONT_Y = 1650                  # Emb lands in front of (closer to camera than) Impulsivity
CAGE_REST = (188, FRONT_Y - 108)   # handle top of the dropped cage by the window
HEAP = (270, FRONT_Y)
SIT = (270, FRONT_Y)
PL_X, PL_Y = M["plates"]
PL_S = 0.62
PLATE_REST = (PL_X, PL_Y + (-10 - 3 * 13) * PL_S)   # top plate centre
PLATE_GRIP = 50                 # hand grips the near rim, this far left of centre
TABLE_FEET = (1760, 1680)       # kneeling in front of the dining table
TABLE_CAGE = (1625, 1688)
PLATE_FEET = (1180, 1452)       # behind the coffee table, facing us
STAIRS_CAM = (2660, 640, 1.2)
FLY_S = 1.7

# ---------------------------------------------------------------------------
# poses
# ---------------------------------------------------------------------------
_CAGE_R = dict(**A("r", 0.02, 0.12, 0.08, h="grip", tf=1.0), ar_layer="back", ar_ik=0.0, hold=1.0)
_CR_LEGS = {k: v for k, v in POSES["crouch"].items() if k.startswith(("ll_", "lr_"))}


def _arms(name):
    return {k: v for k, v in POSES[name].items() if k.startswith(("al_", "ar_"))}


HEAP_P = lambda tilt: dict(base="heap", tilt=tilt)                     # noqa: E731
SIT_RECOIL = dict(base="sit_floor", lean=-0.34, hunch=0.75, chest=0.2)
SIT_COVER = dict(base="sit_floor", **_arms("cover_eyes"), hunch=0.9, nod=0.16, lean=-0.2)
SIT_PEEK = dict(base="sit_floor", **dict(_arms("peek"), ar_hx=20, ar_hy=40),   # far hand slides down:
                hunch=0.75, nod=0.04, lean=-0.22)                         # one eye peeks through
SIT_DOWN = dict(base="sit_floor", hunch=0.55, lean=-0.1)
CROUCH_GRAB = dict(base="crouch", al_ik=1.0, al_tx=0.25, al_ty=0.14, al_tz=0.24, al_h="grip",
                   al_wa=1.4, al_wabs=0.5, neck=-0.05, nod=-0.1)
NOBODY = dict(base="back_away", **A("l", 0.02, 0.1, 0.1, h="grip", tf=1.0), al_ik=0.0,
              lean=-0.1, hunch=0.8)
TIPTOE = dict(base="tiptoe", **_CAGE_R)
TIP_K = 1.75                   # tiptoe cycle speed-up (speed scales with it)


# hand on the plate rim (bent over the coffee table) / plate raised to the chest
PLATE_DOWN = dict(base="stand", **_CR_LEGS, al_ik=1.0, al_tx=0.1, al_ty=0.12, al_tz=0.2, al_h="pinch",
                  al_wa=0.3, al_wabs=0.5, **_CAGE_R, lean=0.7, nod=0.15, hunch=0.3)
PLATE_UP = dict(base="stand", al_ik=1.0, al_tx=0.25, al_ty=0.58, al_tz=0.5, al_h="pinch",
                al_wa=0.3, al_wabs=0.5, **_CAGE_R, lean=0.05, nod=0.05, hunch=0.45)


def DRAWER(o, peek):
    return dict(base="stand", al_ik=1.0, al_tx=-0.1, al_ty=0.41, al_tz=lerp(0.5, 0.35, o),
                al_h="grip", al_wa=0.0, al_wabs=0.5, **_CAGE_R, lean=0.3 + 0.32 * peek,
                nod=0.08 + 0.12 * peek, hunch=0.35)


CRAWL_PEER = dict(base="crawl", rot=0.35, neck=-0.3, nod=-0.2, sway=0.0)       # butt up, head low
CRAWL_UP = dict(base="crawl", rot=0.0, neck=0.25, nod=-0.4, sway=0.0, lean=1.0)  # head snapped up


# ---------------------------------------------------------------------------
# timing (derived from the timeline only)
# ---------------------------------------------------------------------------
class _T:
    def __init__(self, info):
        c, L = info.cue, info.line
        self.reveal = c("reveal")
        self.l1, self.l1e = L("s04_l01").start, L("s04_l01").end
        self.l2, self.l2e = L("s04_l02").start, L("s04_l02").end
        self.peek = c("peek")
        self.derp = c("derp")
        self.l3, self.l3e = L("s04_l03").start, L("s04_l03").end
        self.tip = c("tiptoe")
        self.plates = c("plates")
        self.drawer = c("drawer")
        self.table = c("table")
        self.scratch = c("scratch")
        self.stairs = c("stairs")
        self.l4, self.l4e = L("s04_l04").start, L("s04_l04").end
        self.end = info.dur
        self.c2 = self.l1 - 0.12          # cut to the reaction two-shot
        self.c10 = self.l4 - 0.2          # cut to the "Upstairs." CU
        self.grab = self.l3 + 0.62        # hand closes on the cage handle
        self.snap = self.scratch + 0.07   # head snaps up
        self.fly0 = self.derp + 0.12      # fly flight
        self.fly1 = self.derp + 0.95      # lands on the nose
        self.tag_in = self.reveal + 0.4
        self.tag_out = self.l2 + 0.3
        self.gulp = self.l4e + 0.08
        # tiptoe: walk, freeze mid-step when he notices the eye, walk on
        self.f0 = (self.plates - self.tip) - 0.6     # freeze mid-step, held to the cut
        self.f1 = 99.0
        self.shadow0 = self.stairs + 0.45
        self.shadow1 = self.stairs + 1.15


_TC = {}


def _times(info):
    key = (info.id, info.dur, tuple(sorted(info.cues.items())))
    if key not in _TC:
        _TC.clear()
        _TC[key] = _T(info)
    return _TC[key]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _F(*ds):
    out = {}
    for d in ds:
        if not d:
            continue
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _gaze(t, keys, lag=0.15, gx=0.22, gy=0.14):
    """Pupils lead, the head follows `lag` s later (look, face-deltas)."""
    lk = tween(t, keys)
    hd = tween(t - lag, keys)
    return lk, {"head_turn": hd[0] * gx, "head_nod": hd[1] * gy}


def _norm(dx, dy, m=1.0):
    d = math.hypot(dx, dy) or 1.0
    return (dx / d * m, dy / d * m)


class _Crooked:
    """Rotate Embarrassment's glasses about the bridge (the rig has no askew
    control): temporarily wraps human._draw_glasses for one draw call."""

    def __init__(self, ang):
        self.ang = ang

    def __enter__(self):
        self.orig = human._draw_glasses
        if abs(self.ang) < 1e-3:
            return
        orig, ang = self.orig, self.ang

        def crooked(ctx, C, hg, st, inkw, t):
            xl, yl = st["E_l"][0], st["E_l"][1]
            xr = st["E_r"][0]
            cx = (xl + xr) / 2
            ctx.save()
            ctx.translate(cx, yl + 22 * abs(ang))
            ctx.rotate(ang)
            ctx.translate(-cx, -yl)
            try:
                orig(ctx, C, hg, st, inkw, t)
            finally:
                ctx.restore()

        human._draw_glasses = crooked

    def __exit__(self, *a):
        human._draw_glasses = self.orig


def emb(ctx, x, y, t, glasses=0.0, s=ES, **kw):
    with _Crooked(glasses):
        return human.draw_person(ctx, WHO, x, y, s, t, **kw)


_PS = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
_PC = cairo.Context(_PS)
_PROBE = {}


def _probe_emb(key, x, y, pose, turn, t=0.0):
    if key not in _PROBE:
        _PROBE[key] = human.draw_person(_PC, WHO, x, y, ES, t, pose=pose, turn=turn, shadow=False,
                                        drift=False)
    return _PROBE[key]


def _probe_imp():
    if "imp" not in _PROBE:
        _PROBE["imp"] = creatures.draw_impulsivity(_PC, IMP_X, IMP_Y, IMP_S, 0.0, pant=0.0)
    return _PROBE["imp"]


def cage_floor(ctx, t):
    props.cage(ctx, CAGE_REST[0], CAGE_REST[1], CAGE_S, t, door=0.85, latch="open", empty=True,
               rot=0.12)


def cage_hold_cb(t, floor_y=None, swing=0.0):
    def cb(ctx, side, x, y, ang):
        yy = y
        if floor_y is not None:
            yy = min(y, floor_y - CAGE_H)
        props.cage(ctx, x, yy, CAGE_S, t, door=0.8 + 0.05 * math.sin(t * 5.1), latch="open",
                   empty=True, rot=swing)
    return cb


def draw_top_plate(ctx, x, y, rot, face=0.0):
    """Top plate; face 0 = edge-on like the stack, 1 = tilted up to look at its underside."""
    ry = lerp(15, 78, face)
    with core.saved(ctx, x, y, PL_S, rot):
        props.ell(ctx, 0, 0, 95, ry, "#f7f4ec", 4)
        if face < 0.3:
            props.ell(ctx, 0, -3, 58, 7, "#e3ddcf", 0)
            props.curve(ctx, [(-80, 4), (0, 10), (80, 4)], "#5b7fd1", 3)
        else:
            props.ell(ctx, 0, 0, 84, ry * 0.86, None, 5, sc="#5b7fd1")
            props.ell(ctx, 0, 0, 46, ry * 0.46, "#e3ddcf", 3, sc="#c9c2b2")


def living(ctx, t, top_plate=True, **kw):
    sets.living_room(ctx, t, plates=False, **kw)
    props.plates_stack(ctx, PL_X, PL_Y, PL_S, n=3, t=t)
    if top_plate:
        draw_top_plate(ctx, PLATE_REST[0], PLATE_REST[1], 0.0)


def fly_state(t, T, nose):
    """(x, y, rot, buzzing) of the fly, or None before it arrives."""
    if t < T.fly0:
        return None
    land = (nose[0] + 4 * IMP_S, nose[1] - 26 * IMP_S)
    if t < T.fly1:
        u = smoothstep(seg(t, T.fly0, T.fly1))
        p0 = (land[0] + 360, land[1] - 330)
        p1 = (land[0] - 260, land[1] - 300)
        p2 = (land[0] + 200, land[1] - 150)
        p3 = land

        def bez(u):
            v = 1 - u
            return (v ** 3 * p0[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u ** 3 * p3[0],
                    v ** 3 * p0[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u ** 3 * p3[1])
        x, y = bez(u)
        x2, y2 = bez(min(1.0, u + 0.02))
        w = (1 - u)
        x += noise1(t * 9, 3) * 16 * w
        y += noise1(t * 11, 4) * 12 * w
        rot = clamp(math.atan2(y2 - y, x2 - x + 1e-6) * 0.25, -0.5, 0.5)
        return (x, y, rot, True)
    # landed: still, with one little shuffle-turn
    sh = tween(t, [(T.fly1 + 0.45, 0.0), (T.fly1 + 0.6, 1.0)])
    return (land[0] + 3 * sh, land[1], -0.25 + 0.4 * sh, False)


def draw_imp(ctx, t, T, look_l=None, look_r=None, fly=True):
    a = creatures.draw_impulsivity(ctx, IMP_X, IMP_Y, IMP_S, t, look_l=look_l, look_r=look_r, pant=1.0)
    if fly:
        st = fly_state(t, T, a["nose"])
        if st:
            x, y, rot, buzz = st
            props.fly(ctx, x, y, FLY_S, t if buzz else 0.37, rot)
    return a


def name_tag(ctx, t, T):
    fx.name_tag(ctx, "IMPULSIVITY", "a tripwire that never goes off", t, T.tag_in, T.tag_out,
                x=90, y=170, color="imp")


# ---------------------------------------------------------------------------
# S1a: lift — CU on his face in the heap, a wall of fur beside it
# ---------------------------------------------------------------------------
def shot_lift(ctx, t, T):
    r = T.reveal
    cam = (lerp(500, 494, seg(t, 0, r)), 1592, lerp(3.15, 3.25, seg(t, 0, r)))
    tilt = tween(t, [(0.08, -1.75), (0.42, -2.32)], ease_out)
    look, hf = _gaze(t, [(0.0, (0.2, 0.3)), (0.24, (0.2, 0.3)), (0.36, (0.6, 0.6)),
                         (r - 0.12, (0.6, 0.6)), (r, (0.6, 0.6))], lag=0.15, gx=0.15, gy=0.12)
    expr = state_at(t, [(0.0, "dazed"), (0.34, "neutral")], 0.18)
    focus = seg(t, 0.32, 0.46)
    face = _F(hf, {"lower": 0.25 * focus, "brow_r": 0.4 * focus, "brow_l": -0.1 * focus,
                   "pupil": 0.15 * focus, "head_tilt": noise1(t * 1.3, 8) * 0.05 * (1 - focus)})
    blink = tween(t, [(0.0, 0.9), (0.16, 0.1), (0.22, 0.6), (0.32, 0.0)])
    with core.camera(ctx, *cam):
        living(ctx, t)
        draw_imp(ctx, t, T)
        emb(ctx, HEAP[0], HEAP[1], t, glasses=0.2, pose=HEAP_P(tilt), expr=expr, look=look, face=face,
            blink=blink, blush=0.45, sweat=0.15)
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S1b: reveal — his POV: paws, then the camera tilts up to the derp grin
# ---------------------------------------------------------------------------
def shot_pov(ctx, t, T):
    k = ease_in_out(seg(t, T.reveal + 0.04, T.reveal + 0.74))
    cam = (IMP_X, lerp(1640, 1150, k), lerp(2.5, 1.62, k))
    with core.cache_steps(2):
        with core.camera(ctx, *cam):
            living(ctx, t)
            draw_imp(ctx, t, T)


# ---------------------------------------------------------------------------
# S2: reaction two-shot (l01, l02 cover, peek)
# ---------------------------------------------------------------------------
def shot_react(ctx, t, T, info):
    cam = tween(t, [(T.c2, (430, 1290, 2.05)), (T.derp, (415, 1272, 2.36))])
    pose = state_at(t, [(T.c2, "sit_floor"), (T.l1 + 0.12, SIT_RECOIL), (T.l2 - 0.1, SIT_COVER),
                        (T.peek, SIT_PEEK)], 0.2)
    expr = state_at(t, [(T.c2, "alarmed"), (T.l1 + 0.2, "terrified")], 0.25)
    shock = tween(t, [(T.l1 + 0.18, 0.0), (T.l1 + 0.45, 1.0)])
    up = (0.7, -0.62)        # at its face (it looms above him)
    teeth = (0.62, -0.3)
    look, hf = _gaze(t, [(T.c2, up), (T.l1 + 0.65, up), (T.l1 + 0.78, teeth), (T.l1 + 1.0, teeth),
                         (T.l1 + 1.12, up), (T.peek + 0.1, up), (T.peek + 0.3, (0.68, -0.55))],
                     lag=0.15, gx=0.12, gy=0.1)
    cover = seg(t, T.l2 - 0.1, T.l2 + 0.05) * (1 - seg(t, T.peek, T.peek + 0.2))
    face = _F(hf, {"pupil": -0.45 * shock, "eye_size": 0.12 * shock, "iris": -0.15 * shock,
                   "wobble": 0.35 * shock, "brow_ang": 0.3 * shock,
                   "head_tilt": noise1(t * 7, 5) * 0.025 * shock + 0.05 * seg(t, T.peek, T.peek + 0.3),
                   "squash": -0.06 * tween(t, [(T.l1 + 0.18, 0.0), (T.l1 + 0.3, 1.0), (T.l1 + 0.55, 0.0)])})
    # one eye peeks through the fingers (screen-left eye stays shut)
    pk = seg(t, T.peek + 0.05, T.peek + 0.25)
    if pk > 0:
        face = _F(face, {"lid_l": 0.95 * pk, "lower_l": 0.5 * pk, "brow_l": -0.3 * pk, "brow_r": 0.25 * pk,
                         "eye_size": 0.08 * pk})
    blink = 1.0 if cover > 0.5 else (0.0 if t < T.peek + 0.6 else None)
    blush = tween(t, [(T.c2, 0.55), (T.l1 + 0.3, 0.52), (T.l1 + 1.0, 0.0)])
    glint = tween(t, [(T.l1 + 0.2, 0.0), (T.l1 + 0.3, 0.75), (T.l1 + 0.55, 0.0)])
    glasses = 0.2 * (1 - seg(t, T.l2 + 0.1, T.l2 + 0.35))
    with core.camera(ctx, *cam):
        living(ctx, t)
        cage_floor(ctx, t)
        draw_imp(ctx, t, T)
        emb(ctx, SIT[0], SIT[1], t, glasses=glasses, pose=pose, expr=expr, look=look, face=face, turn=0.5,
            blink=blink, blush=blush, sweat=0.2 + 0.35 * shock, glint=glint, mouth=info.mouth(WHO, t))
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S3: derp CU + fly
# ---------------------------------------------------------------------------
def shot_derp(ctx, t, T):
    cam = tween(t, [(T.derp, (IMP_X, 1170, 2.35)), (T.l3, (IMP_X, 1160, 2.55))])
    with core.camera(ctx, *cam):
        living(ctx, t)
        draw_imp(ctx, t, T)


# ---------------------------------------------------------------------------
# S4: "Okay. Nobody move." — he rises, grabs the cage blindly
# ---------------------------------------------------------------------------
def shot_rise(ctx, t, T, info):
    rc = ease_in_out(seg(t, T.l3 + 0.35, T.l3 + 1.25))
    cam = (lerp(420, 440, rc), lerp(1330, 1160, rc), lerp(1.5, 1.42, rc))
    pose = state_at(t, [(T.l3 - 1.0, SIT_PEEK), (T.l3 + 0.02, SIT_DOWN), (T.l3 + 0.24, CROUCH_GRAB),
                        (T.l3 + 0.72, NOBODY)], 0.42)
    rise = seg(t, T.l3 + 0.3, T.l3 + 1.2)
    look = (lerp(0.75, 0.8, rise), lerp(-0.55, 0.25, rise))
    face = {"brow_ang": 0.45, "brow": 0.15, "pupil": -0.25, "press": 0.2,
            "lid_l": 0.95 * (1 - seg(t, T.l3, T.l3 + 0.18)),
            "head_nod": lerp(-0.06, 0.1, rise), "head_turn": 0.12}
    expr = state_at(t, [(T.l3 - 1.0, "terrified"), (T.l3 + 0.05, "whisper")], 0.25)
    blink = None if t > T.l3 + 1.25 else 0.0
    with core.camera(ctx, *cam):
        living(ctx, t)
        if t < T.grab:
            cage_floor(ctx, t)
        draw_imp(ctx, t, T)
        a = emb(ctx, SIT[0], SIT[1], t, pose=pose, expr=expr, look=look, face=face, turn=0.5, blink=blink,
                blush=0.08, sweat=0.45, mouth=info.mouth(WHO, t))
        if t >= T.grab:
            hx, hy, _ = a["hand_l"]
            k = smoothstep(seg(t, T.grab, T.grab + 0.12))
            x = lerp(CAGE_REST[0], hx, k)
            y = lerp(CAGE_REST[1], hy, k)
            dt = t - T.grab
            swing = 0.12 * (1 - k) + 0.16 * math.sin(dt * 7.5) * math.exp(-dt * 2.8) * k
            props.cage(ctx, x, y, CAGE_S, t, door=0.8 + 0.08 * math.sin(dt * 6.0) * math.exp(-dt * 2),
                       latch="open", empty=True, rot=swing)
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S5: tiptoe behind it; one eye tracks him
# ---------------------------------------------------------------------------
def _tip_walk(u, T):
    """walk-clock (s) for scene time since the tiptoe cue (freeze mid-step)."""
    if u < T.f0:
        return u
    if u < T.f1:
        return T.f0
    return T.f0 + (u - T.f1) * 1.25


TIP_X0, TIP_Y, TIP_TURN = 200, 1385, 0.9


def shot_tiptoe(ctx, t, T):
    u = t - T.tip
    base = tween(t, [(T.tip, (540, 1060, 1.1)), (T.tip + T.f0, (680, 1060, 1.12))])
    push = ease_out(seg(u, T.f0 - 0.02, T.f0 + 0.28))
    cam = tuple(lerp(a, b, push) for a, b in zip(base, (775, 900, 1.6)))
    v = human.cycle_speed(WHO, "tiptoe", TIP_TURN) * ES * TIP_K
    wclk = _tip_walk(u, T)
    x = TIP_X0 + v * wclk
    ia = _probe_imp()
    eye_r = ia["eye_r"]          # the screen-right eye does the tracking; the left stays put
    pa = _probe_emb("tip", 0.0, TIP_Y, TIPTOE, TIP_TURN)
    hx_off, hy = pa["head"][0], pa["head"][1]
    lagx = TIP_X0 + v * _tip_walk(max(0.0, u - 0.3), T) + hx_off
    tgt = _norm(lagx - eye_r[0], hy - eye_r[1], 0.92)
    kt = smoothstep(seg(u, 0.2, 0.95))
    look_r = (lerp(creatures.IMP_DERP_R[0], tgt[0], kt), lerp(creatures.IMP_DERP_R[1], tgt[1], kt))
    noticed = seg(u, T.f0 - 0.08, T.f0 + 0.1)
    to_eye = _norm(eye_r[0] - (x + hx_off), eye_r[1] - hy, m=0.95)
    look = (lerp(0.55, to_eye[0], noticed), lerp(0.75, to_eye[1], noticed))
    face = {"brow_ang": 0.45 + 0.2 * noticed, "press": 0.35 * (1 - noticed), "pupil": -0.2 - 0.35 * noticed,
            "eye_size": 0.1 * noticed, "head_nod": 0.14, "head_turn": 0.08,
            "wobble": 0.3 * noticed}
    expr = state_at(u, [(0.0, "whisper"), (T.f0 - 0.05, "terrified")], 0.15)
    blink = 0.0 if T.f0 - 0.1 < u < T.f1 + 0.2 else None
    with core.camera(ctx, *cam):
        living(ctx, t)
        ea = emb(ctx, x, TIP_Y, t, pose=TIPTOE, pose_t=wclk * TIP_K, turn=TIP_TURN, expr=expr, look=look,
                 face=face, blink=blink, blush=0.1, sweat=0.5 + 0.4 * noticed, hold=cage_hold_cb(t))
        draw_imp(ctx, t, T, look_r=look_r)
        tx_, ty_ = ea["top"]
        fx.sweat_fly(ctx, tx_ - 10, ty_ + 40, 0.6, t, T.tip + T.f0 + 0.06, seed=4, n=3, side=0)
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S6: plates — behind the coffee table, he lifts the top plate and checks
# ---------------------------------------------------------------------------
def coffee_table_front(ctx):
    """Redraw of the set's coffee table (same geometry) so he can stand behind it."""
    C = sets.C
    props.rect(ctx, 1060, 1420, 24, 150, C["wood_dk"], 4)
    props.rect(ctx, 1356, 1420, 24, 150, C["wood_dk"], 4)
    props.polyf(ctx, [(1040, 1392), (1400, 1392), (1416, 1408), (1024, 1408)], C["wood_hi"], 4)
    props.rect(ctx, 1024, 1408, 392, 26, C["wood_sh"], 4, r=4)
    props.rect(ctx, 1290, 1372, 70, 22, "#5f86c4", 3, r=4)
    props.line(ctx, [(1060, 1520), (1380, 1520)], C["wood_dk"], 8)


def shot_plates(ctx, t, T):
    P = T.plates
    cam = tween(t, [(P, (1190, 1190, 1.6)), (T.drawer, (1190, 1180, 1.66))])
    # cut in as the plate leaves the stack; cut out as it goes back down (delicate)
    lift = tween(t, [(P - 0.08, 0.0), (P + 0.3, 1.0), (P + 0.66, 1.0), (P + 1.06, 0.0)])
    pose = (PLATE_DOWN, PLATE_UP, math.sqrt(lift))
    look, hf = _gaze(t, [(P, (0.1, 0.8)), (P + 0.25, (0.1, 0.75)), (P + 0.36, (0.15, 1.0)),
                         (P + 0.47, (0.15, 1.0)), (P + 0.53, (-0.55, -0.35)), (P + 0.66, (-0.55, -0.35)),
                         (P + 0.8, (0.1, 0.8))], lag=0.12, gx=0.14, gy=0.18)
    under = seg(t, P + 0.5, P + 0.56) * (1 - seg(t, P + 0.66, P + 0.72))
    face = _F(hf, {"brow_ang": 0.4, "brow_r": 0.3 * under, "press": 0.45 * (1 - under),
                   "pupil": -0.1, "lower": 0.25 * under})
    with core.camera(ctx, *cam):
        living(ctx, t, top_plate=False)
        a = emb(ctx, PLATE_FEET[0], PLATE_FEET[1], t, pose=pose, turn=0.15, expr="whisper", look=look,
                face=face, blush=0.1, sweat=0.45, hold=cage_hold_cb(t))
        coffee_table_front(ctx)
        props.plates_stack(ctx, PL_X, PL_Y, PL_S, n=3, t=t)
        hx, hy, _ = a["hand_l"]
        k = smoothstep(seg(lift, 0.0, 0.1))
        ff = smoothstep(seg(lift, 0.35, 1.0))
        off = (lerp(PLATE_GRIP, -18, ff), lerp(0.0, -38, ff))
        px = lerp(PLATE_REST[0], hx + off[0], k)
        py = lerp(PLATE_REST[1], hy + off[1], k)
        draw_top_plate(ctx, px, py, -0.1 * math.sin(lift * math.pi) * k - 0.25 * ff, face=ff)
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S7: drawer
# ---------------------------------------------------------------------------
DRAWER_FEET = (1600, 1540)


def shot_drawer(ctx, t, T):
    D = T.drawer
    cam = tween(t, [(D, (1690, 1005, 1.95)), (T.table, (1697, 995, 2.02))])
    o = tween(t, [(D + 0.12, 0.0), (D + 0.34, 1.0), (D + 0.66, 1.0), (D + 0.86, 0.0)], ease_out)
    pk = tween(t, [(D + 0.3, 0.0), (D + 0.42, 1.0), (D + 0.62, 1.0), (D + 0.74, 0.0)])
    look, hf = _gaze(t, [(D, (0.7, 0.55)), (D + 0.3, (0.7, 0.55)), (D + 0.42, (0.4, 0.95)),
                         (D + 0.62, (0.55, 0.95)), (D + 0.76, (0.6, 0.5)), (D + 0.84, (-0.95, -0.05)),
                         (D + 0.96, (-0.95, -0.05))], lag=0.13, gx=0.2, gy=0.15)
    face = _F(hf, {"brow_ang": 0.4, "press": 0.4 * (1 - pk), "pupil": -0.1, "brow_l": 0.2 * pk})
    expr = state_at(t, [(D, "whisper"), (D + 0.8, "alarmed")], 0.12)
    with core.camera(ctx, *cam):
        living(ctx, t, drawer_open=o)
        blink = 0.0 if D + 0.3 < t < D + 0.72 else None      # eyes stay open while he peeks in
        emb(ctx, DRAWER_FEET[0], DRAWER_FEET[1], t, pose=DRAWER(o, pk), turn=0.55, expr=expr, look=look,
            face=face, blink=blink, blush=0.1, sweat=0.45, hold=cage_hold_cb(t, floor_y=DRAWER_FEET[1] + 10))
        sets.living_room(ctx, t, layer="fg")


# ---------------------------------------------------------------------------
# S8 + S9: under the table, scratch, pan to the stairs, the shadow
# ---------------------------------------------------------------------------
def _shadow(ctx, t, T):
    if not (T.shadow0 <= t <= T.shadow1 + 0.05):
        return
    u = seg(t, T.shadow0, T.shadow1)
    x = lerp(2480, 3140, ease_in_out(u))
    y = 296 - 6 * abs(math.sin(t * math.pi / 0.22))        # scurry bob (above the railing)
    a = 0.5 * smoothstep(seg(t, T.shadow0, T.shadow0 + 0.12))
    S = 2.0                                                 # stretched big by the low light
    ctx.save()
    ctx.push_group()
    ctx.translate(x, y)
    ctx.scale(S, S * 1.15)
    core.set_color(ctx, (0, 0, 0, 1))
    core.ellipse(ctx, 0, -32, 70, 30)
    core.ellipse(ctx, 62, -46, 32, 24)
    core.circle(ctx, 52, -76, 13)
    core.circle(ctx, 76, -74, 12)
    ctx.fill()
    wv = math.sin(t * 13) * 9
    core.smooth_path(ctx, [(-62, -30), (-110, -18 + wv), (-160, -40 - wv), (-210, -24 + wv * 0.6),
                           (-250, -46)])
    core.stroke(ctx, (0, 0, 0, 1), 8)
    for i in range(4):
        lx = -36 + i * 24
        ph = math.sin(t * 28 + i * 1.7) * 8
        ctx.move_to(lx, -10)
        ctx.line_to(lx + ph, 0)
    core.stroke(ctx, (0, 0, 0, 1), 6)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def shot_table(ctx, t, T):
    Tb = T.table
    table_cam = tween(t, [(Tb, (1895, 1345, 1.5)), (T.stairs, (1905, 1335, 1.55))])
    k = ease_in_out(seg(t, T.stairs, T.stairs + 0.7))
    cam = tuple(lerp(a, b, k) for a, b in zip(table_cam, STAIRS_CAM))
    pose = state_at(t, [(Tb - 1.0, CRAWL_UP), (Tb - 0.1, CRAWL_PEER), (T.snap, CRAWL_UP)], 0.35)
    if T.snap <= t < T.snap + 0.12:
        pose = (CRAWL_PEER, CRAWL_UP, ease_out_back(seg(t, T.snap, T.snap + 0.12), 2.0))
    snap = ease_out_back(seg(t, T.snap, T.snap + 0.1), 2.2)
    look_peer = tween(t, [(Tb, (0.85, 0.35)), (Tb + 0.35, (0.95, 0.3)), (Tb + 0.65, (0.7, 0.45)),
                          (Tb + 0.95, (1.0, 0.25))])
    look = (lerp(look_peer[0], 0.55, snap), lerp(look_peer[1], -1.0, snap))
    face = {"brow_ang": 0.35 * (1 - snap), "press": 0.4 * (1 - snap), "pupil": -0.1 - 0.35 * snap,
            "eye_size": 0.14 * snap, "head_turn": 0.1, "head_tilt": -0.12 * (1 - snap),
            "brow": 0.35 * snap, "squash": -0.08 * tween(t, [(T.snap, 0.0), (T.snap + 0.08, 1.0),
                                                             (T.snap + 0.3, 0.0)])}
    expr = state_at(t, [(Tb, "whisper"), (T.snap, "alarmed")], 0.1)
    glint = tween(t, [(T.snap, 0.0), (T.snap + 0.08, 0.7), (T.snap + 0.3, 0.0)])
    blink = 0.0 if t > T.snap else None
    with core.cache_steps(2):
        with core.camera(ctx, *cam):
            living(ctx, t)
            props.cage(ctx, TABLE_CAGE[0], TABLE_CAGE[1] - CAGE_H, CAGE_S, t, door=0.8, latch="open",
                       empty=True)
            emb(ctx, TABLE_FEET[0], TABLE_FEET[1], t, pose=pose, pose_t=0.0, turn=0.9, expr=expr, look=look,
                face=face, blush=0.1, sweat=0.5, glint=glint, blink=blink)
            _shadow(ctx, t, T)
            sets.living_room(ctx, t, layer="fg", parts=("stairs",))


# ---------------------------------------------------------------------------
# S10: "Upstairs." CU + gulp
# ---------------------------------------------------------------------------
def shot_cu(ctx, t, T, info):
    pa = _probe_emb("cu", TABLE_FEET[0], TABLE_FEET[1], CRAWL_UP, 0.9)
    fxx, fyy = pa["face"]
    cam = tween(t, [(T.c10, (fxx - 50, fyy + 35, 3.15)), (T.end, (fxx - 45, fyy + 30, 3.32))])
    g = T.gulp
    gk = tween(t, [(g, 0.0), (g + 0.1, 1.0), (g + 0.3, 0.0)])
    look, hf = _gaze(t, [(T.c10, (0.55, -1.0)), (T.l4 + 0.5, (0.55, -1.0)), (T.l4e, (0.5, -0.85)),
                         (g + 0.05, (0.3, -0.5))], lag=0.15, gx=0.15, gy=0.12)
    face = _F(hf, {"brow_ang": 0.5, "brow": 0.2, "pupil": -0.35, "eye_size": 0.08,
                   "squash": 0.07 * gk, "press": 0.6 * gk + 0.25 * seg(t, g + 0.3, g + 0.5),
                   "head_nod": 0.06 * gk})
    expr = state_at(t, [(T.c10, "alarmed"), (T.l4 - 0.05, "whisper"), (T.l4e + 0.02, "terrified")], 0.15)
    glint = tween(t, [(T.l4 + 0.3, 0.0), (T.l4 + 0.4, 0.55), (T.l4 + 0.6, 0.0)])
    with core.camera(ctx, *cam):
        living(ctx, t)
        emb(ctx, TABLE_FEET[0], TABLE_FEET[1], t, pose=CRAWL_UP, pose_t=0.0, turn=0.9, expr=expr, look=look,
            face=face, blush=0.15, sweat=0.7, glint=glint, mouth=info.mouth(WHO, t))
        fx.emote(ctx, "gulp", fxx - 120, fyy + 105, 0.4, t, g, dur=0.75)


# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _times(info)
    if t < T.reveal:
        shot_lift(ctx, t, T)
    elif t < T.c2:
        shot_pov(ctx, t, T)
    elif t < T.derp:
        shot_react(ctx, t, T, info)
    elif t < T.l3:
        shot_derp(ctx, t, T)
    elif t < T.tip:
        shot_rise(ctx, t, T, info)
    elif t < T.plates:
        shot_tiptoe(ctx, t, T)
    elif t < T.drawer:
        shot_plates(ctx, t, T)
    elif t < T.table:
        shot_drawer(ctx, t, T)
    elif t < T.c10:
        shot_table(ctx, t, T)
    else:
        shot_cu(ctx, t, T, info)
    name_tag(ctx, t, T)


def SFX(info):
    T = _times(info)
    ev = []
    ev.append((0.12, "cloth_rustle", -12, -0.3))
    # panting: on screen from the reveal, quieter once he is searching
    P = sfx.LOOPS["dog_pant"]
    tt = T.reveal
    while tt < T.scratch - 1e-6:
        ev.append((round(tt, 4), "dog_pant", -9 if tt < T.plates - 0.5 else -17, -0.15))
        tt += P
    ev.append((T.l2 - 0.1, "cloth_rustle", -9, -0.2))
    ev.append((T.l3 + 0.3, "cloth_rustle", -9, -0.2))
    ev.append((T.grab, "latch_click", -6, -0.3))
    ev.append((T.tip + 0.05, "tiptoe", -6, -0.1))
    ev.append((T.tip + 1.0, "tiptoe", -9, 0.1))
    ev.append((T.tip + T.f0 + 0.04, "gulp", -12, 0.1))      # tiny dry swallow at the stare-off
    ev.append((T.plates + 0.02, "plate_clink", -10, 0.1))
    ev.append((T.plates + 0.97, "plate_clink", -13, 0.1))
    ev.append((T.drawer + 0.12, "drawer_open", -4, 0.2))
    ev.append((T.drawer + 0.66, "drawer_open", -10, 0.2))
    ev.append((T.table + 0.05, "cloth_rustle", -10, 0.2))
    ev.append((T.scratch, "scratch_wood", 2, 0.4))
    ev.append((T.stairs + 0.15, "scratch_wood", -3, 0.5))
    ev.append((T.shadow0, "scurry", -6, 0.5))
    ev.append((T.gulp, "gulp", -2, 0.0))
    return ev
