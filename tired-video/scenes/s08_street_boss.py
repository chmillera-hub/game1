"""s08 — street & boss ("The vans are already here").  Music: tension.

Emb steps out of the front door with the cage and finds two black HushCorp
vans, two still agents and the Boss waiting on the lawn.  Fake-cool, a glance
at the damage, attention, the cage held up.  Behind her back a pink slip
slides out between her fingers; her eyes slide to Tiredness (who dives into a
hedge); her tablet confirms "KNOWN ASSOCIATE: EMBARRASSMENT"; the slip is
tucked away.  "Get in the van."  He scurries in; the door slams.

Geography: the house set (front view, camera on the street) for Emb's shots
and her POV; the reverse angle (from the porch toward the street) uses the
street_view set without the window frame, with the vans parked at the curb
and the Boss + agents just inside his (open) gate.

All timing comes from info cues / line word timings.
"""
import math

import cairocffi as cairo

from engine import core, sets, props, fx
from engine.core import (tween, seg, clamp, lerp, state_at, ease_out_back, ease_in_out, ease_out,
                         ease_in, smoothstep, hash01)
from engine.human import draw_person, cycle_speed, IK
from engine.creatures import draw_thing
from audio import sfx

HM = sets.HOUSE_MARKS
SC = sets.C
INK = core.PAL["ink"]
BROKEN = 2                 # s03 smashed ground-floor window 3 (the rightmost)

# ---------------------------------------------------------------- street (reverse) world
VAN_A = (300.0, 1240.0)
VAN_B = (1010.0, 1236.0)
VAN_S = 0.27
DOOR_X0 = VAN_A[0] + (-590) * VAN_S          # van A sliding-door opening (world x range)
DOOR_X1 = VAN_A[0] + 30 * VAN_S
DOOR_FLOOR = VAN_A[1] - 200 * VAN_S
BOSS = (600.0, 1446.0)
BOSS_S = 0.40
BOSS_HEAD = 892                               # eye line above the ground at s=1
AG_L = (428.0, 1404.0)
AG_R = (792.0, 1400.0)
AG_S = 0.355
GATE = (150.0, 300.0)      # open section of his picket fence (street world x range)

# ---------------------------------------------------------------- house (front) world
EMB_S = 0.46
EMB_X0, EMB_Y0, EMB_Y1 = 1548.0, 1444.0, 1456.0
EMB_HEAD = 896                                # eye line above the ground at s=1
WALK_TURN = 0.2
CAGE_REL = 0.86                               # cage scale relative to Emb's s

# ---------------------------------------------------------------- poses
# carry_front arms (both hands on the cage sides, hold 2)
_CARRY_ARMS = {**IK("l", 0.13, 0.5, 0.2, "grip", wa=1.1, wabs=0.8),
               **IK("r", 0.13, 0.5, 0.2, "grip", wa=1.1, wabs=0.8), "hold": 2.0}
CARRY = {**_CARRY_ARMS, "lean": -0.05, "hunch": 0.3}
WALK_CARRY = {"base": "walk", **_CARRY_ARMS, "lean": 0.0, "hunch": 0.35, "coat_trail": 0.25}
ATTN = {"base": "attention", "ar_h": "grip", "hold": 1.0}
HOLDUP = {**IK("l", 0.13, 0.6, 0.36, "grip", wa=1.1, wabs=0.8),
          **IK("r", 0.13, 0.6, 0.36, "grip", wa=1.1, wabs=0.8), "hold": 2.0,
          "hunch": 0.6, "lean": 0.08}
CARRY_LOW = {**IK("l", 0.13, 0.42, 0.2, "grip", wa=1.1, wabs=0.8),
             **IK("r", 0.13, 0.42, 0.2, "grip", wa=1.1, wabs=0.8), "hold": 2.0, "hunch": 0.4}
SCURRY = {"base": "run_panic", **_CARRY_ARMS, "hunch": 0.75, "lean": 0.3, "coat_trail": 1.0}
SCURRY_RATE = 1.6          # legs spin faster than a normal panic run (speed scaled to match)
# Tiredness: running, clutching his bitten forearm (hold_arm arms on run legs)
RUN_HOLD = {"base": "run", "al_p": 0.12, "al_o": -0.1, "al_e": 0.95, "al_eo": -1.0, "al_w": 0.0,
            "al_h": "relaxed", "ar_p": 0.2, "ar_o": 0.1, "ar_e": 1.0, "ar_eo": 0.0, "ar_w": 0.0,
            "ar_ik": 1.0, "ar_grab": 1.0, "ar_h": "grip", "ar_layer": "front", "hunch": 0.55}
TIRED_KW = dict(headphones="neck")


# ============================================================================ timing
def _wt(info, lid, k):
    """Scene time of word k of line `lid` (lip-sync word starts; even split fallback)."""
    ln = info.line(lid)
    lip = getattr(info, "_lip", None) or {}
    ws = (lip.get(lid) or {}).get("word_starts") or []
    if len(ws) > k:
        return ln.start + ws[k]
    n = max(1, len(ln.text.split()))
    return ln.start + ln.dur * min(k, n) / n


_TCACHE = {}


def _times(info):
    key = (id(info), info.dur, info.cue("consider"))
    T = _TCACHE.get(key)
    if T is not None:
        return T
    c = info.cue
    T = {}
    for k, n in (("l01", "s08_l01"), ("l02", "s08_l02"), ("l03", "s08_l03"), ("l04", "s08_l04"),
                 ("l05", "s08_l05"), ("l06", "s08_l06")):
        T[k] = c(n)
        T[k + "e"] = c(n + ".end")
    T["vans"], T["jaw"], T["debris"], T["eye"], T["cons"] = (c("vans"), c("jawDrop"), c("debris"),
                                                             c("eyeContact"), c("consider"))
    T["end"] = info.dur
    # --- shot cuts
    T["c2"] = T["vans"] + 0.24                       # OTS reveal (vans + Boss)
    T["jd"] = max(T["jaw"] + 0.14, T["c2"] + 0.66)   # the jaw drop lands on the sting's 3rd hit
    T["c3"] = _wt(info, "s08_l02", 2)                # "You are in control" -> Emb CU
    T["tag_in"] = T["c2"] + 0.1
    T["tag_out"] = T["c3"] - 0.36
    T["c4"] = T["debris"] + 0.32                     # damage pan
    T["c5"] = max(T["c4"] + 0.5, T["eye"] - 0.3)     # back on Emb: eyes return
    T["c6"] = T["eye"]                               # Boss ECU: eyes meet
    T["c7"] = min(T["eye"] + 0.34, T["l03"] - 0.04)  # Emb snaps to attention
    T["c8"] = _wt(info, "s08_l03", 2)                # "How you doing?" -> Boss MCU (no reaction)
    T["c9"] = _wt(info, "s08_l03", 5)                # "Yeah, it's all good!" -> Emb
    T["lift"] = _wt(info, "s08_l03", 9)              # "Got the thing right here."
    T["c10"] = T["l03e"] + 0.12                      # tighter on Emb + cage
    T["hiss"] = _wt(info, "s08_l04", 3)              # "afraid"
    T["c11"] = _wt(info, "s08_l04", 5)               # "Heh heh" -> behind her back: the slip
    cd = T["l05"] - T["cons"]                        # the consider pause
    T["c12"] = T["cons"] + 0.016 * cd                # Boss MCU: eyes slide to Tiredness
    T["c13"] = T["c12"] + 0.161 * cd                 # her POV: Tiredness trips into a hedge
    T["c14"] = T["c13"] + 0.29 * cd                  # behind her back: tablet glows, slip tucked
    T["t_on"] = T["c14"] + 0.04                      # the tablet wakes
    T["t_check"] = T["t_on"] + 0.55                  # ... KNOWN ASSOCIATE: EMBARRASSMENT  [check]
    T["tuck"] = T["c14"] + 0.88                      # the slip slides back down out of sight
    T["c15"] = T["l05"] - 0.44                       # Boss CU: eyes back, lid narrows, "Get in the van."
    T["c16"] = T["l05e"] + 0.1                       # wide: he scurries into the van
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


# ============================================================================ helpers
_DRY = []


def _dry():
    if not _DRY:
        _DRY.append(cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)))
    return _DRY[0]


def _cage(ctx, x, y, cs, t, rot=0.0, rattle=0.0, state="cage_inside", look=(0.0, -0.4)):
    def inside(c):
        draw_thing(c, 0, 0, 1.0, t, state, look=look)
    props.cage(ctx, x, y, cs, t, latch="closed", rattle=rattle, inside_fn=inside, rot=rot)


def _emb(ctx, x, y, s, t, pose, grip, cage=None, **kw):
    """Draw Emb with the cage. grip 1 = both hands on its sides (hold-2 poses),
    0 = hanging from the right hand by the handle (hold-1 poses); fractional
    values blend the cage between the two grips (dry run for the anchors)."""
    cage = dict(cage or {})
    rot = cage.pop("rot", 0.0)
    cs = s * CAGE_REL
    if 0.0 < grip < 1.0:
        a = draw_person(_dry(), "embar", x, y, s, t, pose=pose, shadow=False, **kw)
        hr, hl = a["hand_r"], a["hand_l"]
        p1 = (hr[0], hr[1])
        p2 = ((hr[0] + hl[0]) / 2, (hr[1] + hl[1]) / 2 - 150 * cs)
        px, py = lerp(p1[0], p2[0], grip), lerp(p1[1], p2[1], grip)

        def hold(c, side, hx, hy, ang):
            _cage(c, px, py, cs, t, rot=rot, **cage)
    elif grip >= 1.0:
        def hold(c, side, hx, hy, ang):
            a_ = ang if abs(ang) < 1.0 else 0.0
            _cage(c, hx, hy - 150 * cs, cs, t, rot=rot + a_ * 0.6, **cage)
    else:
        def hold(c, side, hx, hy, ang):
            _cage(c, hx, hy, cs, t, rot=rot, **cage)
    return draw_person(ctx, "embar", x, y, s, t, pose=pose, hold=hold, **kw)


def _swing(t, t0, amp=0.22, f=7.5, decay=3.2):
    """Damped pendulum swing of the hanging cage after a jolt at t0."""
    if t < t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-decay * u) * math.sin(f * u)


def _emb_walk(t, T):
    """Emb's porch position (x, y) during/after the walk out."""
    t_stop = T["vans"] - 0.05
    v = cycle_speed("embar", "walk", WALK_TURN) * EMB_S
    tw = clamp(t, 0.0, t_stop)
    x = EMB_X0 + v * tw
    if t > t_stop:                                 # ease into the stop as the legs settle
        u = clamp((t - t_stop) / 0.25)
        x += v * 0.25 * (u - u * u / 2)
    y = lerp(EMB_Y0, EMB_Y1, smoothstep(clamp(t / max(0.1, t_stop))))
    return x, y


def _emb_rest(T):
    return _emb_walk(T["vans"] + 1.0, T)


def _house_bg(ctx, t, door_open=0.0):
    sets.house_exterior(ctx, t, "bg", broken=BROKEN, door_open=door_open, damage=1.0, rock=False)


def _house_fg(ctx, t, parts=("fence",)):
    sets.house_exterior(ctx, t, "fg", broken=BROKEN, damage=1.0, rock=False, parts=parts)


def _gate(ctx):
    """Paint his garden gate standing open in the street_view fence (reverse angle)."""
    x0, x1 = GATE
    ctx.rectangle(x0, 1264, x1 - x0, 38)
    core.fill(ctx, SC["walk"])
    ctx.rectangle(x0, 1300, x1 - x0, 44)
    core.fill(ctx, SC["grass"])
    props.line(ctx, [(x0 + 50, 1264), (x0 + 36, 1300)], SC["walk_sh"], 3)
    for px in (x0 - 16, x1 - 6):
        props.rect(ctx, px, 1250, 22, 94, SC["fence"], 3.5)
        props.rect(ctx, px - 5, 1240, 32, 14, SC["fence"], 3.0, r=4)
    # gate panel swung open toward the lawn, hinged on the right post
    hx = x1 - 8
    for k in range(3):
        a0 = hx - 12 - k * 24
        b = 1342 + k * 13
        props.polyf(ctx, [(a0, b), (a0, b - 60), (a0 - 10, b - 76), (a0 - 20, b - 60), (a0 - 20, b + 3)],
                    SC["fence_sh"], 3.0)
    props.polyf(ctx, [(hx, 1300), (hx - 80, 1328), (hx - 80, 1340), (hx, 1312)], SC["fence_sh"], 3.0)


def _van_a(ctx, t, door, bounce=0.0, layer="all"):
    props.black_van(ctx, VAN_A[0], VAN_A[1], VAN_S, door=door, t=t, layer=layer, bounce=bounce)


def _street_bg(ctx, t, van_door=0.0, bounce=0.0, van_a=True):
    sets.street_view(ctx, t, "bg", frame=False, leaf=False, bird=False)
    _gate(ctx)
    props.black_van(ctx, VAN_B[0], VAN_B[1], VAN_S, t=t)
    if van_a:
        _van_a(ctx, t, van_door, bounce)


def _agents(ctx, t):
    draw_person(ctx, "guard", AG_L[0], AG_L[1], AG_S, t, pose="attention", expr="cold",
                look=(0.12, 0.0), turn=0.25, seed=1, face={"lid": 0.08})
    draw_person(ctx, "guard", AG_R[0], AG_R[1], AG_S, t, pose="attention", expr="stern",
                look=(-0.1, 0.0), turn=-0.3, seed=2, face={"lid": 0.1})


def _boss(ctx, t, look=(0.12, 0.0), face=None, mouth=(0.0, 0.0)):
    return draw_person(ctx, "boss", BOSS[0], BOSS[1], BOSS_S, t, pose="stand", expr="cold",
                       look=look, face=face, mouth=mouth, turn=0.12)


def _boss_cam(dy_frac, zoom, dx=10.0):
    """Camera on the Boss's face: dy_frac = eye-line offset (frame px) from centre."""
    hx, hy = BOSS[0] + dx, BOSS[1] - BOSS_S * BOSS_HEAD
    return (hx, hy - dy_frac / zoom, zoom)


# ============================================================================ SH1 porch walk-out
def _emb_face_l01(t, T, info):
    """Worried muttering, eyes on the cage; darts on 'Nobody saw anything'."""
    w0, w1, w2, w4 = (_wt(info, "s08_l01", k) for k in (0, 1, 2, 4))
    lx = tween(t, [(w2 - 0.05, 0.0), (w2 + 0.05, -0.75), (w2 + 0.24, -0.75), (w2 + 0.32, 0.7),
                   (w2 + 0.52, 0.7), (w4 + 0.1, 0.08)], ease_in_out)
    ly = tween(t, [(w2 - 0.05, 0.85), (w2 + 0.05, 0.12), (w4 - 0.05, 0.12), (w4 + 0.12, 0.8)])
    nod = 0.0
    for w in (w0, w1):
        nod += 0.09 * math.sin(math.pi * seg(t, w, w + 0.32))
    # vans: pupils lift first, the head follows 0.15 s later
    up = ease_out(seg(t, T["vans"], T["vans"] + 0.12))
    hup = ease_out_back(seg(t, T["vans"] + 0.15, T["vans"] + 0.4))
    look = (lerp(lx, 0.05, up), lerp(ly, -0.3, up))
    face = {"head_nod": nod + 0.14 * (1 - hup) - 0.06 * hup, "brow_ang": 0.25 * (1 - up),
            "brow": 0.3 * up, "lid": -0.1 * up, "pupil": -0.18 * up, "wobble": 0.3 * (1 - up)}
    return look, face


def shot_walk(ctx, t, info, T):
    ex, ey = _emb_walk(t, T)
    door = 1.0 - ease_in(seg(t, 0.95, 1.5))
    if t > 1.5:
        door = 0.035 * math.exp(-9 * (t - 1.5)) * abs(math.sin((t - 1.5) * 24))
    k = smoothstep(seg(t, 0.0, T["c2"]))
    cam = (lerp(1580, 1630, k), lerp(1214, 1200, k), lerp(2.05, 2.22, k))
    t_stop = T["vans"] - 0.05
    wk = 1.0 - smoothstep(seg(t, t_stop, t_stop + 0.25))
    pose = (CARRY, WALK_CARRY, wk) if wk < 1 else WALK_CARRY
    look, face = _emb_face_l01(t, T, info)
    expr = state_at(t, [(0, "guilty"), (T["vans"], "neutral")], 0.2)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t, door)
        _emb(ctx, ex, ey, EMB_S, t, pose, 1.0, pose_t=t, expr=expr, look=look, face=face,
             mouth=info.mouth("embar", t), turn=WALK_TURN, blush=0.3, sweat=0.25)
        _house_fg(ctx, t)


# ============================================================================ SH2 OTS reveal + jaw drop
def _emb_ots_face(t, T):
    jd = T["jd"]
    a = seg(t, jd - 0.08, jd)                       # anticipation squash
    d = ease_out_back(seg(t, jd, jd + 0.17), 2.2)   # the drop (overshoot + settle)
    close = ease_out(seg(t, T["l02"] - 0.06, T["l02"] + 0.08))
    k = d * (1 - close)
    return {"open": 1.0 * k, "lip_low": 0.8 * k, "squash": 0.07 * math.sin(math.pi * a) - 0.3 * k,
            "pupil": -0.5 * d, "iris": -0.35 * d, "eye_size": 0.16 * d, "brow": 0.85 * d,
            "brow_ang": 0.3 * d, "press": 0.55 * close, "wobble": 0.5 * close, "lid": -0.12 * d,
            "head_nod": -0.06 * d}


def shot_ots(ctx, t, info, T):
    u = seg(t, T["c2"], T["c3"])
    z = lerp(1.72, 1.8, smoothstep(u))
    hx, hy = BOSS[0], BOSS[1] - BOSS_S * BOSS_HEAD
    cam = (hx + (540 - 410) / z, hy + (960 - 700) / z, z)       # her face at ~(410, 700)
    with core.camera(ctx, *cam):
        _street_bg(ctx, t)
        _agents(ctx, t)
        _boss(ctx, t, look=(0.3, 0.02))
    # foreground: Emb's head and shoulders, 3/4 facing into the frame (screen space)
    sh = core.shake(t, T["jd"], 0.3, 7, seed=5)
    face = _emb_ots_face(t, T)
    blush = lerp(0.3, 0.1, seg(t, T["jd"], T["jd"] + 0.35)) + 0.25 * seg(t, T["l02"], T["c3"])
    a = _emb(ctx, 850 + sh[0], 2290 + sh[1], 1.16, t, CARRY_LOW, 1.0, expr="surprised",
             look=(-0.3, -0.04), face=face, mouth=info.mouth("embar", t), turn=-1.2,
             blush=blush, sweat=0.35)
    if t >= T["jd"]:
        fx.sweat_fly(ctx, a["top"][0] - 30, a["top"][1] + 110, 1.2, t, T["jd"] + 0.02, seed=3, n=4)
    fx.name_tag(ctx, "THE BOSS", "HushCorp", t, T["tag_in"], T["tag_out"], x=90, y=170, color="boss")


# ============================================================================ Emb CU (SH3, SH5)
def shot_emb_cu(ctx, t, info, T, part):
    ex, ey = _emb_rest(T)
    if part == "l02":
        u = seg(t, T["c3"], T["c4"])
    else:
        u = seg(t, T["c5"], T["c6"])
    z = 4.4 * lerp(1.0, 1.035, u)
    hx, hy = ex + 2, ey - EMB_S * EMB_HEAD
    cam = (hx, hy + (960 - 700) / z, z)               # his eyes at ~y 700
    # fake-cool assembles piece by piece: lids, then one brow, then the smirk
    a0 = T["c3"]
    kl = smoothstep(seg(t, a0 + 0.05, a0 + 0.25))
    kb = smoothstep(seg(t, a0 + 0.22, a0 + 0.42))
    ks = ease_out_back(seg(t, a0 + 0.4, a0 + 0.62))
    face = {"lid": 0.24 * kl - 0.3 * (1 - kl), "brow_l": 0.36 * kb, "brow_r": -0.08 * kb,
            "curve": 0.3 * ks, "smirk": 0.5 * ks, "wobble": 0.28 + 0.1 * math.sin(t * 9),
            "press": 0.35 * (1 - ks), "head_tilt": -0.06 * kb, "pupil": -0.3 + 0.18 * kl}
    # debris: pupils slide right, head follows 0.15 s later; back again in SH5
    d0 = T["debris"]
    px = tween(t, [(d0, 0.0), (d0 + 0.12, 0.85), (T["c5"], 0.85), (T["c5"] + 0.14, 0.0)])
    hxt = tween(t, [(d0 + 0.15, 0.0), (d0 + 0.32, 0.22), (T["c5"] + 0.12, 0.22), (T["c5"] + 0.3, 0.0)])
    face["head_turn"] = hxt
    if part == "back":
        face["pupil"] = -0.12 - 0.22 * seg(t, T["c6"] - 0.12, T["c6"])   # eyes meet hers
    blush = lerp(0.32, 0.62, seg(t, T["c3"], T["l02e"] + 0.2))
    g0 = _wt(info, "s08_l02", 5)
    glint = math.sin(math.pi * seg(t, g0, g0 + 0.32))
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        _emb(ctx, ex, ey, EMB_S, t, CARRY, 1.0, expr="fake_cool", look=(px, -0.05), face=face,
             mouth=info.mouth("embar", t), turn=WALK_TURN, blush=blush, sweat=0.45, glint=glint)


# ============================================================================ SH4 damage pan
def shot_damage(ctx, t, info, T):
    u = ease_in_out(seg(t, T["c4"], T["c5"] + 0.02))
    cam = (lerp(1985, 2585, u), lerp(1205, 1385, u), lerp(1.5, 1.08, u))
    with core.cache_steps(2):
        with core.camera(ctx, *cam):
            _house_bg(ctx, t)
            # Tiredness, far back on the lawn, still running laps holding his arm (silent)
            s = 0.36
            v = cycle_speed("tired", "run", 1.0) * s
            tx = 1760 + v * (t - T["c4"])
            draw_person(ctx, "tired", tx, 1572, s, t, pose=RUN_HOLD, pose_t=t - T["c4"], expr="pain",
                        face={"open": 0.25, "teeth": 1.0}, turn=1.0, **TIRED_KW)
            _house_fg(ctx, t)


# ============================================================================ Boss shots (reverse)
def shot_boss(ctx, t, info, T, kind):
    face, mouth = None, (0.0, 0.0)
    door = 0.0
    if kind == "ecu":                 # eyes meet (SH6)
        u = seg(t, T["c6"], T["c7"])
        cam = _boss_cam(-20, lerp(8.6, 9.0, u), dx=2)
        look, face = (0.0, 0.0), {"lid": 0.02}
    elif kind == "mcu":               # "How you doing?" — nothing (SH8)
        u = seg(t, T["c8"], T["c9"])
        cam = _boss_cam(-260, lerp(3.6, 3.68, u))
        look = (0.18, 0.0)
    elif kind == "slide":             # eyes slide to Tiredness (SH12)
        u = seg(t, T["c12"], T["c13"])
        cam = _boss_cam(-250, lerp(3.9, 3.97, u), dx=16)
        k = ease_in_out(seg(t, T["c12"] + 0.1, T["c12"] + 0.3))
        look = (lerp(0.18, -0.9, k), lerp(0.0, 0.06, k))
        face = {"head_turn": -0.035 * smoothstep(seg(t, T["c12"] + 0.25, T["c12"] + 0.5))}
    else:                             # "Get in the van." (SH15)
        u = seg(t, T["c15"], T["c16"])
        cam = _boss_cam(-170, lerp(5.2, 5.32, u), dx=14)
        k = ease_in_out(seg(t, T["c15"] + 0.04, T["c15"] + 0.22))
        look = (lerp(-0.9, 0.16, k), lerp(0.06, 0.0, k))
        nl = ease_in_out(seg(t, T["c15"] + 0.22, T["c15"] + 0.44))
        face = {"head_turn": -0.035 * (1 - k), "lid": 0.08 * nl, "lower": 0.1 * nl, "press": 0.15 * nl}
        mouth = info.mouth("boss", t)
        door = ease_in_out(seg(t, T["l05"] + 0.3, T["l05"] + 0.8))
    with core.camera(ctx, *cam):
        _street_bg(ctx, t, van_door=door)
        _agents(ctx, t)
        _boss(ctx, t, look=look, face=face, mouth=mouth)


# ============================================================================ SH7 / SH9 / SH10 Emb medium
def shot_emb_med(ctx, t, info, T, part):
    ex, ey = _emb_rest(T)
    snap = T["c7"] + 0.06
    ks = ease_out_back(seg(t, snap, snap + 0.13), 2.0)
    lift0 = T["lift"] - 0.06
    kl = ease_out_back(seg(t, lift0, lift0 + 0.32), 1.5)
    dip = math.sin(math.pi * seg(t, lift0 - 0.16, lift0 + 0.02))
    if t < snap:
        pose, grip = CARRY, 1.0
    elif t < lift0:
        pose, grip = ((CARRY, ATTN, ks), clamp(1 - ks)) if ks < 1 else (ATTN, 0.0)
    else:
        pose, grip = (ATTN, HOLDUP, kl), clamp(kl)
    if part == "attn":
        u = seg(t, T["c7"], T["c8"])
        z = lerp(2.2, 2.26, u)
        cam = (ex + 8, ey - EMB_S * 560, z)
    elif part == "l03":
        u = smoothstep(seg(t, T["c9"], T["c10"]))
        z = lerp(2.26, 2.5, u)
        cam = (ex + 8, ey - EMB_S * lerp(560, 650, u), z)
    else:
        u = seg(t, T["c10"], T["c11"])
        z = lerp(3.05, 3.15, u)
        cam = (ex + 10, ey - EMB_S * 760, z)
    # stretch on the snap (chin up), then settle; the cage swings on its handle
    lift_px = 16 * math.sin(math.pi * seg(t, snap, snap + 0.2))
    rot = _swing(t, snap + 0.03, 0.3, 8.0, 3.5) if grip < 0.5 else 0.0
    rattle = 0.0
    th_state, th_look = "cage_inside", (0.0, -0.4)
    if t >= T["hiss"] - 0.05:
        rattle = 0.5 * (1 - seg(t, T["hiss"] + 0.15, T["hiss"] + 0.6))
        th_state = "hiss" if t < T["hiss"] + 0.75 else "cage_inside"
    expr = state_at(t, [(0, "fake_cool"), (snap, "frozen_shock"), (T["l03"] + 0.03, "nervous_smile")], 0.15)
    face = {"pupil": -0.12, "wobble": 0.35}
    # frantic little eye darts while he smiles
    dart = 0.0
    for i in range(16):
        tk = T["l03"] + 0.35 + i * 0.43
        if tk > t:
            break
        dart = (hash01(i, 81) - 0.5) * 0.8
    lx = dart if t > T["l03"] + 0.3 else 0.0
    ly = -0.06
    if T["hiss"] - 0.04 < t < T["hiss"] + 0.55:
        lx, ly = 0.75, 0.5                      # a glance at the hissing cage
    hh = _wt(info, "s08_l04", 5)
    bob = 6 * abs(math.sin((t - hh) * math.pi / 0.16)) if hh <= t <= T["l04e"] else 0.0
    face["head_nod"] = -0.08 * ks * (1 - kl) - 0.02
    blush = lerp(0.6, 0.82, seg(t, T["l03"], T["lift"]))
    sweat = lerp(0.5, 0.8, seg(t, T["l03"], T["l04"]))
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        a = _emb(ctx, ex, ey - lift_px + bob - 5 * dip, EMB_S, t, pose, grip, expr=expr, look=(lx, ly),
                 face=face, mouth=info.mouth("embar", t), turn=WALK_TURN * 0.5, blush=blush, sweat=sweat,
                 cage=dict(rot=rot, rattle=rattle, state=th_state, look=th_look))
        if t >= snap:
            fx.sweat_fly(ctx, a["top"][0], a["top"][1] + 40, 0.5, t, snap, seed=7, n=3)
        if blush > 0.7:
            fx.heat_squiggles(ctx, a["top"][0], a["top"][1] - 6, 0.5, t, (blush - 0.7) / 0.3 * 0.6)


# ============================================================================ SH11 / SH14 behind her back
SKIN = core.PAL["b_skin"]
SKIN_SH = core.mixc(core.PAL["b_skin"], "#b98a7c", 0.55)
SUIT, SUIT_DK, SLEEVE = "#2a2d3a", "#1b1d27", "#363a4e"


def _finger(ctx, x0, y0, ang, ln, w=26):
    with core.saved(ctx, x0, y0, 1.0, ang):
        core.rrect(ctx, -w * 0.4, -w / 2, ln + w * 0.4, w, w / 2)
        core.fill_stroke(ctx, SKIN, INK, 5)
        core.rrect(ctx, ln - w * 0.62, -w * 0.3, w * 0.5, w * 0.6, w * 0.25)   # nail
        core.fill(ctx, core.mixc(SKIN, "#ffffff", 0.45))


def _hand_over_edge(ctx, x, y, ang, s, lens=(60, 68, 62, 48), spread=27, gap=None):
    """Back of a hand whose fingers curl over an edge: palm at (x, y), fingers along ang."""
    with core.saved(ctx, x, y, s, ang):
        for i, ln in enumerate(lens):
            oy = (i - 1.5) * spread
            if gap is not None and i >= gap:
                oy += 12
            _finger(ctx, 36, oy, 0.07 * (i - 1.5), ln, 28)
        core.smooth_path(ctx, [(-44, -44), (20, -50), (48, -40), (54, 0), (48, 44), (14, 52), (-44, 42)],
                         closed=True, tension=0.5)
        core.fill_stroke(ctx, SKIN, INK, 5.5)
        for i in range(4):                     # knuckle dimples
            oy = (i - 1.5) * spread + (12 if gap is not None and i >= gap else 0)
            props.curve(ctx, [(30, oy - 7), (37, oy), (30, oy + 7)], SKIN_SH, 3)
        props.curve(ctx, [(-24, -28), (-2, -8), (-10, 24)], SKIN_SH, 3)


def _cuff(ctx, x, y, ang, s):
    with core.saved(ctx, x, y, s, ang):
        core.rrect(ctx, -30, -50, 34, 100, 10)
        core.fill_stroke(ctx, "#f4f6fa", INK, 5)
        core.circle(ctx, -13, 0, 8)
        core.fill_stroke(ctx, core.PAL["hush"], INK, 3)


def _sleeve(ctx, pts, w):
    core.smooth_path(ctx, pts)
    core.stroke(ctx, INK, w + 11, cap="butt")
    core.smooth_path(ctx, pts)
    core.stroke(ctx, SLEEVE, w, cap="butt")


def _back_insert(ctx, t, info, T, part):
    if part == "slip":
        u = seg(t, T["c11"], T["c12"])
    else:
        u = seg(t, T["c14"], T["c15"])
    # backdrop: the lawn and house beyond her (house set), barely visible at the edges
    with core.camera(ctx, 1590 - 30 * u, 1300, 1.3):
        _house_bg(ctx, t)
    ctx.save()
    sc = lerp(1.0, 1.04, u)
    breath = 3 * math.sin(t * math.tau / 2.4)
    ctx.translate(540, 960 + breath)
    ctx.scale(sc, sc)
    ctx.translate(-540, -960)
    # the jacket back: shoulder blades (top) down past the hem
    core.smooth_path(ctx, [(70, -80), (90, 420), (150, 900), (175, 1150), (140, 1500), (120, 2100),
                           (960, 2100), (940, 1500), (905, 1150), (930, 900), (990, 420), (1010, -80)],
                     closed=True, tension=0.35)
    core.fill_stroke(ctx, SUIT, INK, 7)
    core.smooth_path(ctx, [(780, -80), (860, 420), (850, 900), (845, 1150), (880, 1500), (900, 2100),
                           (960, 2100), (940, 1500), (905, 1150), (930, 900), (990, 420), (1010, -80)],
                     closed=True, tension=0.35)
    core.fill(ctx, core.alpha(SUIT_DK, 0.5))
    props.line(ctx, [(540, -80), (540, 1380)], SUIT_DK, 7)
    props.polyf(ctx, [(540, 1380), (518, 2100), (562, 2100)], SUIT_DK, 5)
    props.curve(ctx, [(150, 1420), (540, 1445), (930, 1420)], INK, 6)
    # tablet (left hand) and slip (right hand)
    tx, ty, tw, th = 245, 800, 590, 442
    # forearms come in from her sides behind the tablet edges
    _sleeve(ctx, [(-90, 560), (40, 860), (200, 1000)], 132)
    _sleeve(ctx, [(1170, 470), (1040, 640), (865, 735)], 128)
    _cuff(ctx, 205, 1004, 0.25, 1.0)
    _cuff(ctx, 872, 732, 2.75, 1.0)
    # the slip rises from between the right hand's fingers (drawn behind the hand)
    if part == "slip":
        ks = ease_out(seg(t, T["c11"] + 0.16, T["c11"] + 0.62))
    else:
        ks = 1.0 - ease_in_out(seg(t, T["tuck"], T["tuck"] + 0.2))
    if ks > 0.002:
        ctx.save()
        with core.saved(ctx, 772, 742, 1.0, 0.17):
            ctx.rectangle(-300, -600, 600, 600)
            ctx.clip()
            props.pink_slip(ctx, 0, lerp(160, -128, ks), 1.32, 0.0)
        ctx.restore()
    if part == "slip" or t < T["t_on"]:
        core.rrect(ctx, tx - 22, ty - 22, tw + 44, th + 44, 34)
        core.fill_stroke(ctx, "#20232c", INK, 6)
        core.rrect(ctx, tx, ty, tw, th, 18)
        core.fill(ctx, "#0e1820")
        props.polyf(ctx, [(tx + 60, ty), (tx + 150, ty), (tx + 40, ty + th), (tx - 50 + 40, ty + th)],
                    (1, 1, 1, 0.05), 0)
        props.hush_logo(ctx, tx + tw / 2, ty + th + 2, 7, lw=0, ring=False)
    else:
        t_on = T["t_on"]
        glow = ease_out(seg(t, t_on, t_on + 0.3))
        core.radial_glow(ctx, tx + tw / 2, ty + th / 2, 600, "#bdf4ff", 0.2 * glow)
        fx.tablet_screen(ctx, tx, ty, tw, th, t, t_on=t_on, t_check=T["t_check"])
    # left hand: fingers curled over the tablet's left edge
    _hand_over_edge(ctx, 226, 1012, 0.05, 1.18)
    # right hand on the top-right corner, fingers draped over the top edge
    tw_ = 0.05 * math.sin(math.pi * seg(t, T["tuck"] - 0.04, T["tuck"] + 0.26)) if part != "slip" else 0.0
    _hand_over_edge(ctx, 800, 752, 2.05 + tw_, 1.18, lens=(40, 46, 44, 34), gap=2)
    ctx.restore()


def shot_back(ctx, t, info, T, part):
    _back_insert(ctx, t, info, T, part)


# ============================================================================ SH13 her POV: hedge dive
def shot_pov(ctx, t, info, T):
    t0 = T["c13"]
    d = T["c14"] - t0
    u = seg(t, t0, T["c14"])
    cam = (lerp(1408, 1396, u), 1270, lerp(1.12, 1.15, u))
    ex, ey = _emb_rest(T)
    s = 0.42
    v = cycle_speed("tired", "run", -1.0) * s       # negative (moving left)
    x_start = 1655.0
    t_trip = t0 + 0.4 * d
    t_land = t_trip + 0.2
    hx, hy = HM["hedge_trip"]
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        # Emb on the porch, cage held up, frozen grin (he doesn't notice a thing)
        _emb(ctx, ex, ey, EMB_S, t, HOLDUP, 1.0, expr="nervous_smile", look=(0.05, -0.05),
             face={"wobble": 0.6, "pupil": -0.2}, turn=WALK_TURN * 0.5, blush=0.82, sweat=0.8,
             cage=dict(rot=0.015 * math.sin(t * 13)))
        if t < t_trip:
            x = x_start + v * (t - t0)
            draw_person(ctx, "tired", x, 1640, s, t, pose=RUN_HOLD, pose_t=t - t0, expr="pain",
                        face={"open": 0.25, "teeth": 1.0}, turn=-1.0, **TIRED_KW)
        elif t < t_land:
            x0 = x_start + v * (t_trip - t0)
            k = seg(t, t_trip, t_land)
            x = lerp(x0, hx + 30, k)
            y = lerp(1640, hy - 20, k) - 70 * math.sin(math.pi * k)
            draw_person(ctx, "tired", x, y, s, t, pose={"base": "fall", "rot": -0.4 - 0.9 * ease_in(k)},
                        expr="pain", turn=-1.0, **TIRED_KW)
            if k > 0.5:
                _house_fg(ctx, t, parts=("hedge",))
        else:
            kick = t - t_land
            amp = 0.35 * (0.6 + 0.4 * math.exp(-2 * kick))
            pose = {"base": "heap", "ll_p": 0.9 + amp * math.sin(kick * 19),
                    "lr_p": 0.35 + amp * math.sin(kick * 19 + 2.0)}
            draw_person(ctx, "tired", hx + 10, hy - 2, s, t, pose=pose, expr="dazed", flip=True,
                        **TIRED_KW)
            _house_fg(ctx, t, parts=("hedge",))
            for i in range(6):               # a few leaves knocked loose
                k = seg(t, t_land, t_land + 0.8 + 0.25 * hash01(i, 5))
                if 0 < k < 1:
                    lx = hx - 80 + hash01(i, 6) * 220 + (hash01(i, 7) - 0.5) * 140 * k
                    ly = hy - 100 - 150 * math.sin(math.pi * min(1.0, k * 1.3)) * (0.5 + 0.5 * hash01(i, 8)) + 90 * k
                    props.leaf(ctx, lx, ly, 0.45, k * 5 + i, SC["leaf"])


# ============================================================================ SH16 he scurries into the van
EMB_PATH = [(965.0, 1505.0, 0.45), (640.0, 1384.0, 0.385), (238.0, 1296.0, 0.32), (226.0, 1262.0, 0.30)]


def _path_pos(dist):
    """Position + scale after `dist` screen-x px of travel along EMB_PATH."""
    P = EMB_PATH
    rem = dist
    for (x0, y0, s0), (x1, y1, s1) in zip(P, P[1:]):
        L = abs(x1 - x0) + 1e-6
        if rem <= L:
            k = rem / L
            return lerp(x0, x1, k), lerp(y0, y1, k), lerp(s0, s1, k), False
        rem -= L
    x, y, s = P[-1]
    return x, y, s, True


def _run_state(t, t_go):
    """Integrate the scurry so the planted foot keeps pace while he shrinks into depth."""
    sp1 = abs(cycle_speed("embar", "run_panic", -1.1)) * SCURRY_RATE
    dist, tt, dt = 0.0, t_go, 1.0 / 96
    while tt < t:
        x, y, s_, done = _path_pos(dist)
        if done:
            return x, y, s_, tt
        dist += sp1 * s_ * min(dt, t - tt)
        tt += dt
    x, y, s_, done = _path_pos(dist)
    return x, y, s_, (t if done else None)


def _van_times(T):
    t_go = T["c16"] + 0.05
    _, _, _, arr = _run_state(T["end"] + 2.0, t_go)
    t_in = arr + 0.16
    return t_go, arr, t_in, t_in + 0.1


def shot_van(ctx, t, info, T):
    t_go, t_arr, t_in, t_slam = _van_times(T)
    x, y, s, _ = _run_state(t, t_go)
    cam = (500, 1225, 1.3)
    door = 1.0 - ease_in(seg(t, t_slam - 0.32, t_slam))
    bounce = 0.0
    if t >= t_slam:
        uu = t - t_slam
        bounce = math.exp(-5 * uu) * math.cos(uu * 26)
    expr = "nervous_smile" if t < T["l06"] else "alarmed"
    kw = dict(expr=expr, look=(-0.45, 0.0), face={"wobble": 0.35}, mouth=info.mouth("embar", t),
              blush=0.72, sweat=0.7, turn=-1.1)
    with core.camera(ctx, *cam):
        sets.street_view(ctx, t, "bg", frame=False, leaf=True, bird=False)
        _gate(ctx)
        props.black_van(ctx, VAN_B[0], VAN_B[1], VAN_S, t=t)
        if t >= t_arr:
            _van_a(ctx, t, door, bounce, layer="interior")
            if t < t_in + 0.1:
                k = seg(t, t_arr, t_in)
                hx = x - 14 * k
                hy = lerp(y, DOOR_FLOOR + 8, ease_out(k)) - 40 * math.sin(math.pi * k)
                fade = 1.0 - 0.85 * seg(t, t_arr + 0.05, t_in + 0.1)
                core.fade_group(ctx, fade, lambda c: _emb(
                    c, hx, hy, s * (1 - 0.1 * k), t, ("crawl" if k > 0.5 else SCURRY), 1.0 if k <= 0.5 else 0.0,
                    pose_t=(t - t_go) * SCURRY_RATE, **kw))
            _van_a(ctx, t, door, bounce, layer="body")
        else:
            _van_a(ctx, t, 1.0)
        # people, far to near (feet y): the agents, Emb (while outside), the Boss
        k1 = ease_in_out(seg(t, t_go + 0.2, t_go + 0.5))
        k2 = ease_in_out(seg(t, t_slam + 0.15, t_slam + 0.4))
        items = [(AG_L[1], lambda: draw_person(ctx, "guard", AG_L[0], AG_L[1], AG_S, t, pose="attention",
                                               expr="cold", look=(0.12, 0.0), turn=0.25, seed=1,
                                               face={"lid": 0.08})),
                 (AG_R[1], lambda: draw_person(ctx, "guard", AG_R[0], AG_R[1], AG_S, t, pose="attention",
                                               expr="stern", look=(-0.1, 0.0), turn=-0.3, seed=2,
                                               face={"lid": 0.1})),
                 # the Boss doesn't move; her eyes follow him to the van and come back
                 (BOSS[1], lambda: _boss(ctx, t, look=(lerp(0.16, -0.75, k1 * (1 - k2)), 0.0)))]
        if t_go <= t < t_arr:
            def emb_run():
                _emb(ctx, x, y, s, t, SCURRY, 1.0, pose_t=(t - t_go) * SCURRY_RATE,
                     cage=dict(rot=0.07 * math.sin((t - t_go) * 22)), **kw)
                fx.motion_lines(ctx, x + 150 * s, y - 520 * s, 0.3, 420 * s, t, 0.8, seed=3)
            items.append((y, emb_run))
        for _, fn in sorted(items, key=lambda it: it[0]):
            fn()


# ============================================================================ render
def render(ctx, t, info):
    T = _times(info)
    if t < T["c2"]:
        shot_walk(ctx, t, info, T)
    elif t < T["c3"]:
        shot_ots(ctx, t, info, T)
    elif t < T["c4"]:
        shot_emb_cu(ctx, t, info, T, "l02")
    elif t < T["c5"]:
        shot_damage(ctx, t, info, T)
    elif t < T["c6"]:
        shot_emb_cu(ctx, t, info, T, "back")
    elif t < T["c7"]:
        shot_boss(ctx, t, info, T, "ecu")
    elif t < T["c8"]:
        shot_emb_med(ctx, t, info, T, "attn")
    elif t < T["c9"]:
        shot_boss(ctx, t, info, T, "mcu")
    elif t < T["c10"]:
        shot_emb_med(ctx, t, info, T, "l03")
    elif t < T["c11"]:
        shot_emb_med(ctx, t, info, T, "l04")
    elif t < T["c12"]:
        shot_back(ctx, t, info, T, "slip")
    elif t < T["c13"]:
        shot_boss(ctx, t, info, T, "slide")
    elif t < T["c14"]:
        shot_pov(ctx, t, info, T)
    elif t < T["c15"]:
        shot_back(ctx, t, info, T, "tablet")
    elif t < T["c16"]:
        shot_boss(ctx, t, info, T, "van")
    else:
        shot_van(ctx, t, info, T)


# ============================================================================ SFX
def SFX(info):
    T = _times(info)
    ev = []
    # SH1: footsteps on the porch boards (walk contacts), the door clicks shut behind him
    t_stop = T["vans"] - 0.05
    k = 0
    while 0.25 + 0.5 * k < t_stop:
        ev.append((0.25 + 0.5 * k, "footstep", -5.0, 0.05))
        k += 1
    ev.append((0.35, "cage_rattle", -16.0, 0.05))
    ev.append((1.5, "door_bang", -15.0, -0.05))
    ev.append((1.52, "latch_click", -2.0, -0.05))
    # SH2: the reveal sting; the jaw drop lands on its third hit
    ev.append((T["c2"] - 0.02, "dun_dun_dun", -5.0))
    ev.append((T["jd"], "boing", -13.0, 0.25))
    # SH3: fake-cool glasses glint on "control"
    ev.append((_wt(info, "s08_l02", 5) - 0.3, "sparkle", -17.0, 0.2))
    # SH4: a quick pan
    ev.append((T["c4"] - 0.2, "whoosh", -17.0, 0.3))
    # SH6: eyes meet — his heart skips
    ev.append((T["c6"], "heartbeat", -7.0))
    # SH7: snap to attention (cloth snap, the cage swings on its handle)
    snap = T["c7"] + 0.06
    ev.append((snap - 0.05, "whoosh", -14.0))
    ev.append((snap, "cloth_rustle", -4.0))
    ev.append((snap + 0.05, "cage_rattle", -10.0, 0.15))
    # SH9: the cage lifted up; SH10: the thing hisses inside
    ev.append((T["lift"], "cage_rattle", -9.0))
    ev.append((T["hiss"] - 0.03, "critter_hiss", -3.0, 0.1))
    ev.append((T["hiss"], "cage_rattle", -7.0, 0.1))
    # SH11: the pink slip slides out between her fingers
    ev.append((T["c11"] + 0.1, "paper", -7.0))
    # SH13: Tiredness trips into the hedge (far, small)
    d = T["c14"] - T["c13"]
    t_trip = T["c13"] + 0.4 * d
    ev.append((t_trip + 0.18, "body_thud", -9.0, -0.35))
    ev.append((t_trip + 0.2, "cloth_rustle", -6.0, -0.35))
    # SH14: the tablet wakes, the check mark, the slip tucked away
    ev.append((T["t_on"], "scan_beep", -6.0))
    ev.append((T["t_check"] + 0.05, "puzzle_click", -6.0))
    ev.append((T["tuck"] - 0.45, "paper", -11.0))
    # SH15: the van door slides open behind her as she says it
    ev.append((T["l05"] + 0.3, "whoosh", -18.0, -0.3))
    # SH16: he scurries across the lawn and dives in; the door slams, the van rocks
    t_go, t_arr, t_in, t_slam = _van_times(T)
    ev.append((t_go, "footsteps_run", -7.0, 0.1))
    ev.append((t_in - 0.02, "body_thud", -12.0, -0.3))
    ev.append((t_slam - 0.54, "van_door", -2.0, -0.3))
    return ev
