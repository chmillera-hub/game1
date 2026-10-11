"""s03 - Flashlights ("TIREDNESS - Episode 2: Lights Out"), music "sneaky".

The lower level of the shaft, dark. Two guards with flashlights come down the
stair and search. Our two hide in FRONT of crate A while the guards walk the
lane BEHIND it (the crate is between them), sneak after the guards, then
Curiosity hops on the crate behind the gruff guard's head and trolls him;
when he turns, it melts into a puddle; "Huh. Just pipes."

Staging (world = sets.shaft_lower, people at s 0.75):
  stair (top-left) | crate A (1120..1706) | pallet | crate stack B | SERVICE TUNNEL
  our two: front lane FY (in front of crate A); guards: back lane BY (between
  the crates and the wall) -> the crate hides the guards' legs and shadows its
  own front face from their beams.

Shot list (all times from cues / line times; see _T):
  est     0 .. l01-0.05     WIDE: dark; two beams click on at the stair top and
                            sweep; guards come down; our two freeze, ears up.
  stair   .. hide-0.05      MS gruff guard descending, "The boss says..."
  hide    .. l02-0.25       MS our two duck against crate A, quiet pings, the
                            rookie's upper body + beam pass over the crate top.
  shadow  .. sneak          MS rookie behind the crate: "I hate the dark."; the
                            gruff guard's beam throws his big shadow on the wall;
                            he jumps, lands, waves at it, it waves back, he hurries on.
  sneak   .. troll          MS-wide: gruff guard walks right over their heads; they
                            sneak after him (upright crouch), freeze when the
                            rookie's beam swings back, Curiosity hops on the crate.
  troll   .. troll+1.75     MS: Curiosity on the crate right behind his head: evil
                            grin + little paw wave.
  react   .. l03.end+0.35   MCU Tiredness frozen in horror; ping; whisper "Stop that."
  turn    .. l04-0.4        MS: the guard heard; head, then body turn, the beam swings
                            round; at the last instant Curiosity melts; the beam
                            passes over: crate top, pipes.
  pipes   .. reform+0.4     MS guard: "Huh. Just pipes." one-arm shrug, walks off
                            (the rookie's beam waits at the right); puddle glints;
                            the reform begins.
  reform  .. end            two-shot: Curiosity pops back up smug, happy wiggle;
                            Tiredness slowly rises, exhales, lips pressed, deadpan look.
"""
import math

import cairocffi as cairo

from engine import core, sets, human, creatures as CR, fx, props
from engine.core import (tween, seg, lerp, clamp, smoothstep, ease_in_out, ease_out, ease_in,
                         ease_out_back, hexc)
from audio import sfx

M = sets.SHAFT_LOWER_MARKS
SC = 0.75            # people + creature scale (set char_scale)
SC2 = 0.72           # the rookie guard is a touch smaller
FY = 1640            # our two: front lane, in front of crate A (crouched heads stay below its top)
BY = 1455            # the guards' lane, behind the crates
POWER = 0.6          # Tiredness's teal irises (under the hood: the rim glow)
SEAT = (1610.0, 1016.0)   # Curiosity sitting on crate A's lid (right end)
TX0, CX0 = 1180.0, 1335.0  # where our two hide
DARKC = hexc(sets.DARK)
TEAL = core.PAL["power"]

# silhouettes (world) -------------------------------------------------------
OCC_A = [(1116, 1504), (1116, 1031), (1143, 996), (1710, 996), (1710, 1470), (1684, 1504)]
OCC_B = [(2056, 1504), (2056, 878), (2083, 842), (2390, 842), (2390, 1068), (2550, 1066),
         (2550, 1470), (2524, 1504)]
# crate A's front face + the floor in front of it: in the crate's shadow for a
# light behind / beside it (the guards' beams never light our two through it)
SHADOW_A = [(1104, 1032), (1702, 1032), (1726, 1500), (1800, 2800), (1000, 2800), (1096, 1500)]

# the rookie: no mustache, lighter skin, brown hair (registered as a new outfit key;
# nothing in the engine is changed)
_RK = ("guard", "s03_rookie")
if _RK not in human.OUTFITS:
    _gh = dict(human.CHARS["guard"]["head"])
    _gh["mustache"] = False
    human.OUTFITS[_RK] = dict(head=_gh, col=dict(skin="#c99266", skin_sh=core.mixc("#c99266", "#000000", 0.2),
                                                 hair="#4a2f1f", brow="#4a2f1f"))

# Tiredness: crouched with his back to the crate, hands braced low
HIDE = {"base": "crouch", "ar_ik": 1.0, "ar_tx": 0.2, "ar_ty": 0.02, "ar_tz": 0.05, "ar_h": "flat",
        "al_ik": 1.0, "al_tx": 0.2, "al_ty": 0.02, "al_tz": 0.05, "al_h": "flat", "lean": 0.4}
# the rookie's little wave at his own shadow (free l hand, bent elbow, palm out)
G2_WAVE = {"base": "stand", "period": 0.6, "al_p": 0.25, "al_o": 0.6, "al_e": 2.15,
           "al_eo": human.W(-0.5, 0.32, 0.0), "al_w": human.W(0.0, 0.2, 0.1), "al_h": "open",
           "al_tf": -1.0, "hunch": 0.35}
G2_ANTIC = {"base": "stand", "hunch": 1.2, "lean": -0.06, "nod": -0.05}
G2_LEAP = {"base": "leap_scared", "ar_h": "grip"}     # keeps hold of his flashlight


def LIT(c):
    sets.shaft_lower(c, 0.0, lit=True)


def DARKW(c):
    sets.shaft_lower(c, 0.0, lit=False)


# ============================================================================
# timing
# ============================================================================
_TC = {}


def _T(info):
    key = (info.id, info.dur, tuple(sorted(info.cues.items())))
    T = _TC.get(key)
    if T is not None:
        return T
    c = info.cue
    T = {"dur": info.dur}
    for i in range(1, 5):
        ln = info.line(f"s03_l0{i}")
        T[f"l{i}s"], T[f"l{i}e"] = ln.start, ln.end
    T["hide"], T["sneak"], T["troll"] = c("hide"), c("sneak"), c("troll")
    T["turn"], T["melt"], T["reform"] = c("turn"), c("melt"), c("reform")
    T["jump"] = c("jump", T["l2e"] + 0.45)
    S, TR = T["sneak"], T["troll"]
    T["c1"], T["c2"] = 0.35, 0.6                     # flashlight clicks
    T["tj"] = T["l2e"] + 0.1                         # the rookie jumps at his shadow
    T["g1a"], T["g1b"] = S - 0.3, TR - 0.42          # gruff guard walks right over their heads
    T["g2a"] = S - 0.28                              # the rookie hurries on, out ahead
    T["sn0"] = S + 0.97                              # our two start sneaking after him
    T["fr0"], T["fr1"] = S + 1.77, S + 2.42          # freeze: he glances back, beam over the crate
    T["sn1"] = TR - 0.6                              # sneak ends
    T["hop0"], T["hop1"], T["hop2"] = TR - 0.62, TR - 0.4, TR - 0.12   # crouch / take off / land
    T["wave0"] = TR + 0.12
    T["hear"] = T["l3s"] + 0.35                      # the guard hears the whisper
    T["land"] = T["melt"] + 0.55                     # beam lands where Curiosity was
    T["shrug"] = T["l4e"] - 0.12
    T["g1off"] = T["l4e"] + 0.5
    T["rise0"] = T["reform"] + 0.75                  # Tiredness straightens up
    T["shots"] = [("est", 0.0), ("stair", T["l1s"] - 0.05), ("hide", T["hide"] - 0.05),
                  ("shadow", T["l2s"] - 0.25), ("sneak", S), ("troll", TR),
                  ("react", TR + 1.75), ("turn", T["l3e"] + 0.35), ("pipes", T["l4s"] - 0.4),
                  ("reform", T["reform"] + 0.4)]
    _TC.clear()
    _TC[key] = T
    return T


def _shot(t, T):
    name, t0 = T["shots"][0]
    t1 = T["dur"]
    for i, (n, s0) in enumerate(T["shots"]):
        if t >= s0:
            name, t0 = n, s0
            t1 = T["shots"][i + 1][1] if i + 1 < len(T["shots"]) else T["dur"]
    return name, t0, t1


# ============================================================================
# helpers
# ============================================================================
def _ramp(t, t0, t1, x0, x1, r=0.22):
    """Position along a move with accel/decel ramps of r s (constant speed between)."""
    if t <= t0:
        return x0
    if t >= t1:
        return x1
    D = t1 - t0
    r = min(r, D / 2)
    v = (x1 - x0) / (D - r)
    if t < t0 + r:
        u = t - t0
        return x0 + v * u * u / (2 * r)
    if t > t1 - r:
        u = t1 - t
        return x1 - v * u * u / (2 * r)
    return x0 + v * (r / 2) + v * (t - t0 - r)


def _path(t, moves, r=0.22):
    """moves [(t0, t1, x0, x1)] in time order -> (x, travelled distance, walking 0..1)."""
    x, d, k = moves[0][2], 0.0, 0.0
    for (t0, t1, a, b) in moves:
        if t >= t1:
            x = b
            d += abs(b - a)
        elif t > t0:
            x = _ramp(t, t0, t1, a, b, r)
            d += abs(x - a)
            rr = min(r, (t1 - t0) / 2)
            k = smoothstep(seg(t, t0, t0 + rr)) * (1 - smoothstep(seg(t, t1 - rr, t1)))
            break
        else:
            break
    return x, d, k


def _stair_y(x):
    """Smooth descent line over the tread centres (stair descends to the right)."""
    return min(float(M["feet_y"]), 456.0 + (x + 150.0) * 72.0 / 70.0)


def _lane_y(x):
    if x <= 865:
        return _stair_y(x)
    return lerp(1500.0, BY, smoothstep(seg(x, 865, 985)))


def _poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def _clip_out(ctx, polys, big=(-2000, -2000, 8000, 8000)):
    ctx.new_path()
    ctx.rectangle(*big)
    for p in polys:
        _poly(ctx, p)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def _group(ctx, dark, fn):
    """Draw fn() into a group, darken it ATOP by `dark` (the room's darkness on the
    character only), return (pattern, fn's result)."""
    ctx.push_group()
    res = fn()
    if dark > 0.004:
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.set_source_rgba(DARKC[0], DARKC[1], DARKC[2], clamp(dark))
        ctx.paint()
        ctx.restore()
    return ctx.pop_group(), res


def _paint(ctx, pat, occ=None):
    if pat is None:
        return
    ctx.save()
    if occ:
        _clip_out(ctx, occ)
    ctx.set_source(pat)
    ctx.paint()
    ctx.restore()


def _wave(t, f, amp, seed=0):
    return amp * core.noise1(t * f, seed)


def _hand_target(x, y, s, ang, turn):
    """Where a guard holds his flashlight (r hand) for a beam angle: chest high and
    forward; pointing down it is held low at the screen-right side, never centred."""
    sx, sy = x + 10 * s, y - 700 * s
    L = 175 * s
    ca, sa = math.cos(ang), math.sin(ang)
    side = 0.6 * L * max(0.0, sa) * (1 - abs(ca))
    return (sx + L * ca + side, sy + L * (0.55 + 0.5 * sa))


# ============================================================================
# guards
# ============================================================================
def _g1(t, T):
    """The gruff guard (mustache): leads the search, says l01 / l04."""
    hide, S, TR, U, ML = T["hide"], T["sneak"], T["troll"], T["turn"], T["melt"]
    # down the stair (talking), a stop on the lower steps to sweep the room, then the lane
    tst = T["l1e"] + 0.05
    v0 = (700.0 - 120.0) / (tst - 0.11)
    moves = [(-0.6, tst, 120.0 - 0.6 * v0, 700.0), (hide + 1.15, T["l2s"] + 0.35, 700.0, 1000.0),
             (T["g1a"], T["fr0"] - 0.08, 1000.0, 1560.0), (T["fr1"] + 0.05, T["g1b"], 1560.0, 1860.0),
             (T["g1off"], T["g1off"] + 3.2, 1860.0, 2750.0)]
    x, d, kw = _path(t, moves)
    y = _lane_y(x)
    turn = tween(t, [(0.0, 0.62), (tst, 0.62), (tst + 0.4, 0.3), (hide + 0.9, 0.3), (hide + 1.3, 0.85),
                     (T["l2s"] + 0.1, 0.85), (T["l2s"] + 0.5, 0.5), (T["g1a"] - 0.15, 0.5), (T["g1a"] + 0.2, 1.0),
                     (T["fr0"] - 0.1, 1.0), (T["fr0"] + 0.22, -0.3), (T["fr1"] - 0.15, -0.3), (T["fr1"] + 0.12, 1.0),
                     (T["g1b"] - 0.2, 1.0), (T["g1b"] + 0.25, 0.7),
                     (U + 0.35, 0.7), (ML + 0.3, -0.75),
                     (T["shrug"] - 0.1, -0.75), (T["shrug"] + 0.25, -0.12), (T["shrug"] + 0.8, -0.12),
                     (T["g1off"] + 0.05, -0.6), (T["g1off"] + 0.4, 0.9)])
    ang = tween(t, [(0.0, 0.95), (1.1, 0.45), (2.2, 0.8), (3.3, 0.3), (tst + 0.2, 0.55),
                    (tst + 0.9, 1.25), (hide + 0.9, 0.75), (hide + 1.6, 0.1), (T["l2s"] + 0.2, -0.32),
                    (T["tj"] + 0.9, -0.3),
                    (T["g1a"] + 0.3, 0.25), (T["fr0"], 0.3), (T["fr0"] + 0.3, math.pi - 0.1), (T["fr1"] - 0.15, math.pi - 0.2),
                    (T["fr1"] + 0.15, 0.35), (T["g1b"], 0.45), (TR + 0.1, 0.55), (TR + 1.1, 0.4),
                    (TR + 2.1, 0.62), (U + 0.4, 0.45), (ML - 0.05, 1.45), (T["land"], math.pi - 0.08),
                    (T["land"] + 0.7, math.pi + 0.26), (T["land"] + 1.4, math.pi + 0.02),
                    (T["g1off"], math.pi + 0.04), (T["g1off"] + 0.45, 0.35)])
    # walk / stand / shrug
    v = human.cycle_speed("guard", "walk", turn) * SC
    pose = ("stand", "walk", kw) if kw > 0.001 else "stand"
    ks = smoothstep(seg(t, T["shrug"], T["shrug"] + 0.28)) * (1 - smoothstep(seg(t, T["shrug"] + 0.8,
                                                                                    T["shrug"] + 1.1)))
    reach_w = 1.0
    if ks > 0.001:
        pose = ("stand", "shrug", ks)
        reach_w = 1 - ks
    # face
    look = (0.6 * math.cos(ang), 0.5 * math.sin(ang))
    face = {}
    expr = "stern"
    if t >= T["l1s"] - 0.3:
        expr = "annoyed"
    if t >= hide + 0.5:
        expr = "stern"
        look = (0.55, -0.25)
    if t >= T["g1a"]:
        look = (0.6, 0.15)
    if T["fr0"] <= t < T["fr1"]:
        k = smoothstep(seg(t, T["fr0"], T["fr0"] + 0.2))
        look = (lerp(0.6, -0.85, k), 0.35 * k)
        expr = "squint"
        face = {"head_turn": -0.35 * k}
    if t >= TR - 0.5:
        expr = "bored"
        look = (0.7 + _wave(t, 0.7, 0.15, 3), 0.05)
        face["head_turn"] = 0.12 * math.sin((t - TR) * 1.3)
    if t >= T["hear"]:
        # he heard something behind him: one brow up, eyes slide back first
        k = smoothstep(seg(t, T["hear"], T["hear"] + 0.25))
        look = (lerp(0.7, -0.8, k), lerp(0.05, -0.05, k))
        face["brow_l"] = 0.35 * k
        face["brow_r"] = 0.1 * k
        face["head_turn"] = lerp(face.get("head_turn", 0.0), -0.1, k)
    if t >= U:
        k = smoothstep(seg(t, U + 0.05, U + 0.45)) * (1 - smoothstep(seg(t, ML + 0.1, ML + 0.5)))
        face["head_turn"] = lerp(-0.1, -0.55, k)     # the head leads the body round
        look = (-0.9, 0.1)
        expr = "curious"
    if t >= T["land"] - 0.25:
        expr = "squint"
        look = (-0.7, 0.25 if t < T["land"] + 0.5 else -0.15)
        face = {"brow_l": 0.15}
    if t >= T["l4s"] - 0.1:
        expr = "deadpan"
        look = (-0.6, 0.15)
        face = {"head_tilt": 0.06 * smoothstep(seg(t, T["l4s"], T["l4s"] + 0.3))}
    if t >= T["shrug"]:
        expr = "unamused"
        face = {"brow_l": 0.25}
    if t >= T["g1off"]:
        expr = "bored"
        look = (0.6, 0.1)
        face = {}
    power = smoothstep(seg(t, T["c1"], T["c1"] + 0.08))
    return dict(who="guard", x=x, y=y, s=SC, turn=turn, pose=pose, pose_t=d / max(1.0, v), expr=expr,
                look=look, face=face, ang=ang, power=power, flicker=0.0, seed=0, outfit="default",
                mouth="guard", reach_w=reach_w, lane="stair" if x < 900 else "back")


def _g2(t, T):
    """The rookie (scared of the dark): l02, the shadow jump."""
    S, tj = T["sneak"], T["tj"]
    fr0, fr1 = T["fr0"], T["fr1"]
    v0 = (865.0 - 420.0) / (T["l1s"] - 0.2 - 0.11)
    moves = [(-0.6, T["l1s"] - 0.2, 420.0 - 0.6 * v0, 865.0), (T["l1s"] - 0.2, T["l1s"] + 1.3, 865.0, 1150.0),
             (T["l1s"] + 1.3, T["l2s"] - 0.05, 1150.0, 1400.0),
             (T["g2a"], T["g2a"] + 3.3, 1400.0, 2400.0)]
    x, d, kw = _path(t, moves)
    y = _lane_y(x)
    turn = tween(t, [(0.0, 0.8), (T["l1s"] + 0.3, 0.8), (T["l1s"] + 0.8, 0.5), (T["l2s"] - 0.3, 0.5),
                     (T["l2s"], 0.35), (T["g2a"] - 0.2, 0.35), (T["g2a"] + 0.15, 1.0)])
    ang = tween(t, [(0.0, 0.6), (0.9, 1.05), (1.7, 0.45), (2.6, 0.9), (3.4, 0.3), (4.3, 0.55),
                    (5.2, 0.2), (6.0, 0.5), (T["l2s"], 0.62), (tj, 0.6), (T["g2a"], 0.45),
                    (T["g2a"] + 1.0, 0.3), (T["g2a"] + 2.0, 0.6)])
    v = human.cycle_speed("guard", "walk", turn, _RK[1]) * SC2
    pose = ("stand", "walk", kw) if kw > 0.001 else "stand"
    reach_w = 1.0
    dy = 0.0
    # the jump: anticipation (shoulders up) -> leap -> land (squash) -> frozen -> waves at it
    if tj - 0.12 <= t < tj + 1.0:
        if t < tj:
            pose = ("stand", G2_ANTIC, smoothstep(seg(t, tj - 0.12, tj)))
        elif t < tj + 0.36:
            pose = (G2_ANTIC, G2_LEAP, smoothstep(seg(t, tj, tj + 0.08)))
            reach_w = 1 - 0.75 * smoothstep(seg(t, tj, tj + 0.12))
        elif t < tj + 0.5:
            k = smoothstep(seg(t, tj + 0.36, tj + 0.46))
            pose = (G2_LEAP, G2_ANTIC, k)
            reach_w = k
            dy = 10 * math.sin(math.pi * seg(t, tj + 0.4, tj + 0.56))
        else:
            kwv = smoothstep(seg(t, tj + 0.5, tj + 0.62)) * (1 - smoothstep(seg(t, tj + 0.86, tj + 1.0)))
            pose = (G2_ANTIC, G2_WAVE, kwv) if t < tj + 0.75 else ("stand", G2_WAVE, kwv)
    expr = "neutral"
    face = {"brow_ang": 0.7, "brow": 0.25, "press": 0.35, "wobble": 0.25}
    look = (0.55 * math.cos(ang) + _wave(t, 1.8, 0.35, 11), 0.4 * math.sin(ang))
    if T["l2s"] - 0.2 <= t < tj:
        expr = "sad"
        face = {"brow_ang": 0.8, "brow": 0.3, "wobble": 0.3}
        look = (0.3 + _wave(t, 2.2, 0.3, 5), -0.1)
        if t > T["l2e"] - 0.35:        # the eyes catch the looming shape on the wall
            look = (0.9, -0.45)
    if tj <= t < tj + 0.62:
        expr = "frozen_shock"
        face = {"eye_size": 0.12}
        look = (0.9, -0.5)
    elif tj + 0.62 <= t < tj + 1.1:
        expr = "sheepish"
        look = (0.9, -0.45)
    elif tj + 1.1 <= t < tj + 1.6:
        expr = "relieved"
        look = (0.6, 0.1)
    power = smoothstep(seg(t, T["c2"], T["c2"] + 0.08))
    return dict(who="guard", x=x, y=y + dy, s=SC2, turn=turn, pose=pose, pose_t=d / max(1.0, v), expr=expr,
                look=look, face=face, ang=ang, power=power, flicker=0.6, seed=3, outfit=_RK[1],
                mouth="guard2", reach_w=reach_w, lane="stair" if x < 900 else "back", sweat=0.35)


def _draw_guard(ctx, t, info, g, dark):
    """Guard into a shaded group; returns (pattern, anchors, lens (x, y, ang))."""
    rec = {}
    s = g["s"]
    hx, hy = _hand_target(g["x"], g["y"], s, g["ang"], g["turn"])

    def light(c, side, x, y, a_):
        w = g["reach_w"]
        da = (a_ - g["ang"] + math.pi) % (2 * math.pi) - math.pi
        rot = g["ang"] + da * (1 - w)
        flip = math.cos(rot) < 0
        props.flashlight(c, x, y, s, (math.pi - rot) if flip else rot, on=g["power"], glow=0.0,
                         flip=flip)
        rec["lens"] = (x + 116 * s * math.cos(rot), y + 116 * s * math.sin(rot), rot)

    def fn():
        return human.draw_person(ctx, "guard", g["x"], g["y"], s, t, pose=g["pose"], pose_t=g["pose_t"],
                                 turn=g["turn"], expr=g["expr"], look=g["look"], face=g["face"],
                                 mouth=info.mouth(g["mouth"], t), outfit=g["outfit"], seed=g["seed"],
                                 hold=light, hold_sides="r",
                                 reach={"r": (hx, hy, g["reach_w"], g["ang"])},
                                 sweat=g.get("sweat", 0.0))
    pat, a = _group(ctx, dark, fn)
    return pat, a, rec.get("lens")


def _cone(ctx, t, lens, g, key, rect, clip_shadow=True, length=980, spread=0.56, exact=True):
    if lens is None or g["power"] <= 0.01:
        return
    ctx.save()
    if clip_shadow:
        _clip_out(ctx, [SHADOW_A])
    fx.flashlight(ctx, lens[0], lens[1], lens[2], length, spread, t, LIT, key=key, rect=rect,
                  power=g["power"], flicker=g["flicker"], seed=g["seed"] + 1, lens=False, s=SC,
                  haze=0.04, exact=exact)
    ctx.restore()


def _lens_glow(ctx, lens, g):
    if lens is None or g["power"] <= 0.01:
        return
    p = g["power"]
    ctx.save()
    if g["lane"] == "back":
        _clip_out(ctx, [OCC_A, OCC_B])
    core.radial_glow(ctx, lens[0], lens[1], 52 * g["s"] / SC, "#fff0c8", 0.55 * p)
    core.ellipse(ctx, lens[0], lens[1], 4.5, 10, lens[2])
    core.set_color(ctx, (1, 0.99, 0.95, min(1.0, 0.4 + p)))
    ctx.fill()
    ctx.restore()


# ============================================================================
# our two
# ============================================================================
def _tired(t, T):
    hide, S, TR = T["hide"], T["sneak"], T["troll"]
    sn0, fr0, fr1, sn1 = T["sn0"], T["fr0"], T["fr1"], T["sn1"]
    moves = [(sn0, fr0, TX0, TX0 + 50.0), (fr1, sn1, TX0 + 50.0, TX0 + 110.0)]
    x, d, kw = _path(t, moves, r=0.12)
    turn = 0.15
    pose = "stand"
    v = human.cycle_speed("tired", "sneak", 0.8, "sewer") * SC
    pt = d / max(1.0, v)
    # duck (a quick drop), hide, sneak (freezing mid-step), hide again, rise at the end
    kd = smoothstep(seg(t, hide + 0.02, hide + 0.3))
    if t < sn0 - 0.3:
        pose = ("stand", HIDE, kd) if kd < 1 else HIDE
        turn = lerp(0.15, 0.25, kd)
    elif t < sn1:
        k = smoothstep(seg(t, sn0 - 0.3, sn0))
        pose = (HIDE, "sneak", k) if k < 1 else "sneak"
        turn = lerp(0.25, 0.8, k)
        # the rookie's beam swings back: he dips low and freezes mid-step
        kd2 = 0.7 * smoothstep(seg(t, fr0, fr0 + 0.16)) * (1 - smoothstep(seg(t, fr1 - 0.18, fr1)))
        if kd2 > 0.001:
            pose = ("sneak", HIDE, kd2)
    else:
        k = smoothstep(seg(t, sn1, sn1 + 0.35))
        pose = ("sneak", HIDE, k) if k < 1 else HIDE
        turn = lerp(0.8, 0.3, k)
        kr = ease_in_out(seg(t, T["rise0"], T["rise0"] + 1.1))
        if kr > 0:
            pose = (HIDE, "stand", kr) if kr < 1 else "stand"
            turn = lerp(0.3, 0.45, kr)
    expr = "bored"
    face = {"press": 0.15}
    # head acting under the hood (he 'looks' with the sense)
    if t < hide:
        k = smoothstep(seg(t, T["c1"] + 0.15, T["c1"] + 0.45))
        face = {"head_turn": -0.35 * k, "head_nod": -0.12 * k, "brow": 0.8 * k, "press": 0.2,
                "open": 0.08 * k}
        expr = ("bored", "alarmed", 0.35 * k)
    elif t < S + 0.3:
        # the beams pass over the crate: the hood tracks them, lips pressed
        k = smoothstep(seg(t, hide + 0.3, hide + 0.6))
        ht = -0.3 + 0.45 * smoothstep(seg(t, hide + 0.8, T["l2s"] - 0.6))
        face = {"head_turn": ht * k, "head_nod": -0.22 * k, "press": 0.6, "brow": 0.4}
        expr = "annoyed"
    elif t < TR:
        face = {"press": 0.55, "head_turn": 0.25, "head_nod": -0.1, "brow": 0.3}
        if t < sn0:     # the guard walks right over their heads
            face["head_turn"] = lerp(-0.2, 0.35, smoothstep(seg(t, S, sn0)))
            face["head_nod"] = -0.3
        if fr0 + 0.05 <= t < fr1:
            face = {"press": 0.9, "head_turn": 0.4, "head_nod": -0.15, "brow": 0.9, "width": -0.1}
        if t >= sn1:
            face = {"press": 0.6, "head_turn": 0.45, "head_nod": -0.25, "brow": 0.3}
        expr = "annoyed"
    else:
        # frozen in horror: mouth a flat line, brows up (nudging the hood rim)
        k = smoothstep(seg(t, TR + 1.9, TR + 2.1))
        face = {"press": lerp(0.6, 0.95, k), "width": lerp(0.0, 0.12, k), "brow": lerp(0.3, 1.0, k),
                "head_turn": 0.22, "head_nod": lerp(-0.25, -0.32, k), "squash": -0.05 * k}
        expr = ("annoyed", "alarmed", k)
        if t >= T["l3s"] - 0.1:
            # "Stop that." through his teeth, a small jerk of the head toward it
            jerk = 0.08 * math.sin(math.pi * seg(t, T["l3s"] + 0.45, T["l3s"] + 0.85))
            face = {"press": 0.3, "brow": 0.6, "head_turn": 0.25 + jerk, "head_nod": -0.3,
                    "brow_ang": -0.3}
            expr = "annoyed"
        if t >= T["l3e"] + 0.2:
            face = {"press": 0.9, "width": 0.1, "brow": 0.9, "head_turn": 0.25, "head_nod": -0.3}
            expr = "alarmed"
        if t >= T["turn"] + 0.2:
            face["brow"] = 1.0
            face["press"] = 1.0
        if t >= T["land"]:
            face = {"press": 1.0, "width": 0.12, "brow": 1.0, "head_turn": 0.45, "head_nod": -0.32,
                    "cheek": 0.35}
        if t >= T["reform"] + 0.2:
            # slow exhale: cheeks puff, then release; lips pressed; deadpan look up at it
            kx = smoothstep(seg(t, T["rise0"] - 0.2, T["rise0"] + 0.9))
            face = {"press": lerp(0.9, 0.55, kx), "cheek": 0.5 * (1 - kx), "open": 0.15 * math.sin(math.pi * kx),
                    "brow": lerp(0.9, -0.2, kx), "head_turn": 0.45, "head_nod": lerp(-0.32, -0.38, kx),
                    "curve": -0.1 * kx}
            expr = ("alarmed", "unamused", kx)
            if t >= T["rise0"] + 1.2:
                ks = smoothstep(seg(t, T["rise0"] + 1.2, T["rise0"] + 1.6))
                face = {"press": 0.6, "head_turn": lerp(0.45, 0.55, ks), "head_nod": lerp(-0.38, -0.46, ks),
                        "head_tilt": -0.07 * ks, "brow": -0.2, "curve": -0.1}
                expr = "unamused"
    return dict(x=x, y=FY, turn=turn, pose=pose, pose_t=pt, expr=expr, face=face)


def _curio(t, T):
    """Curiosity: x, y, pose kwargs."""
    hide, S, TR, ML, R = T["hide"], T["sneak"], T["troll"], T["melt"], T["reform"]
    sn0, fr0, fr1 = T["sn0"], T["fr0"], T["fr1"]
    kw = dict(form=1.0, glow=0.6, flip=False)
    if t < hide:
        k = ease_out_back(seg(t, T["c1"] + 0.1, T["c1"] + 0.3))
        kw.update(pose="stand", expr="surprised_soft" if t > T["c1"] + 0.1 else "calm",
                  ears=lerp(0.5, 1.0, k), face=lerp(1.0, -0.6, smoothstep(seg(t, T["c1"] + 0.1, T["c1"] + 0.4))),
                  look=(-0.5 * k, -0.4 * k))
        return CX0, FY + 12, kw
    if t < sn0 - 0.2:
        km = smoothstep(seg(t, hide + 0.02, hide + 0.32))
        kw.update(pose="perch", pose_from="stand", pose_mix=km, expr="wide", ears=lerp(1.0, 0.12, km),
                  glow=lerp(0.6, 0.4, km), look=(-0.45 + 0.7 * smoothstep(seg(t, hide + 0.8, T["l2s"] - 0.5)),
                                                  -0.7))
        if t >= S:
            kw["look"] = (lerp(-0.2, 0.6, smoothstep(seg(t, S, sn0 - 0.3))), -0.75)
        return CX0, FY + 12, kw
    moves = [(sn0, fr0, CX0, CX0 + 70.0), (fr1, T["hop0"] - 0.02, CX0 + 70.0, CX0 + 125.0)]
    x, d, kmv = _path(t, moves, r=0.12)
    if t < T["hop0"]:
        km = smoothstep(seg(t, sn0 - 0.2, sn0 + 0.1))
        pt = d / (CR.SPEC_WALK_SPEED * SC)
        pose = "walk" if (kmv > 0.05 or (fr1 > t > fr0)) else "stand"
        kw.update(pose="walk" if t < fr0 or t > fr1 else "stand", pose_t=pt, expr="annoyed", ears=0.35,
                  glow=0.45, look=(0.5, -0.5))
        if km < 1:
            kw.update(pose="walk", pose_from="perch", pose_mix=km)
        if fr0 <= t < fr1:
            kw.update(pose="stand", pose_from="walk", pose_mix=smoothstep(seg(t, fr0, fr0 + 0.15)),
                      expr="wide", ears=0.1, look=(0.3, -0.8))
        return x, FY + 12, kw
    if t < T["hop1"]:
        # anticipation: sit back on the haunches, look up at the crate top
        k = smoothstep(seg(t, T["hop0"], T["hop0"] + 0.15))
        kw.update(pose="sit", pose_from="stand", pose_mix=k, expr="curious", ears=0.7, look=(0.3, -0.9),
                  tilt=-0.1 * k)
        return CX0 + 125.0, FY + 12, kw
    if t < T["hop2"]:
        # the leap (body centre on an arc) up onto the lid
        u = seg(t, T["hop1"], T["hop2"])
        x0, y0 = CX0 + 125.0, FY - 120
        x1, y1 = SEAT[0], SEAT[1] - 110
        bx = lerp(x0, x1, u)
        by = lerp(y0, y1, u) - 210 * 4 * u * (1 - u)
        kw.update(pose="leap", expr="wide", ears=0.85, look=(0.4, -0.2), tilt=lerp(-0.5, 0.2, u))
        return bx, by, kw
    # sitting on the lid
    land = smoothstep(seg(t, T["hop2"], T["hop2"] + 0.2))
    if t < TR:
        kw.update(pose="sit", expr="calm", ears=0.62, look=(0.6, 0.05), tail_curl=0.2)
        kw["_squash"] = 0.12 * math.sin(math.pi * seg(t, T["hop2"], T["hop2"] + 0.22))
        return SEAT[0], SEAT[1], kw
    if t < R:
        melt = tween(t, [(ML, 0.0), (ML + 0.45, 1.0)], smoothstep)
        if t > T["l4e"] + 0.1:
            melt = tween(t, [(T["l4e"] + 0.1, 1.0), (T["l4e"] + 0.4, 0.9)])
        look = None
        if t >= T["hear"]:
            look = (0.7, 0.05)
        if t >= T["turn"] + 0.3:
            look = (0.6, 0.2)
        kw.update(pose="wave", expr="troll", pose_t=t - T["wave0"], melt=melt, look=look,
                  tail_curl=0.35, glow=0.6)
        return SEAT[0], SEAT[1], kw
    # re-form: rises back up (springy over-stretch), smug, happy wiggle, then looks down at him
    melt = tween(t, [(R, 0.9), (R + 0.7, -0.15), (R + 0.95, 0.0)], ease_in_out)
    kw.update(pose="sit", melt=melt, expr="proud" if t > R + 0.35 else "calm", glow=0.6,
              tail_curl=tween(t, [(R + 0.7, 0.2), (R + 1.2, 0.75)]),
              ears=tween(t, [(R + 0.6, 0.5), (R + 0.9, 0.8)], ease_out_back))
    wig = seg(t, R + 0.95, R + 1.85)
    if 0 < wig < 1:
        kw["tilt"] = 0.09 * math.sin(wig * 2 * math.pi * 3) * math.sin(math.pi * wig)
    if t >= R + 2.1:
        kw.update(expr="troll", look=(-0.7, 0.55), ears=0.75, face=0.5, tail_curl=0.7)
    return SEAT[0], SEAT[1], kw


def _draw_curio(ctx, t, x, y, kw):
    kw = dict(kw)
    sq = kw.pop("_squash", 0.0)
    if sq:
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(1 + sq, 1 - sq)
        ctx.translate(-x, -y)
    a = CR.draw_specimen(ctx, x, y, SC, t, **kw)
    if sq:
        ctx.restore()
    return a


# ============================================================================
# cameras
# ============================================================================
def _view(cx, cy, z, pad=60):
    w, h = core.W / z, core.H / z
    return (cx - w / 2 - pad, cy - h / 2 - pad, w + 2 * pad, h + 2 * pad)


def _union(a, b):
    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
    x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
    return (x0, y0, x1 - x0, y1 - y0)


STAIR_Z = 1.8


def _stair_cam(t, T):
    x = _g1(t, T)["x"]
    y = _lane_y(x)
    return (x + 70, y - 330, STAIR_Z)


def _cam(name, t, t0, t1, T):
    """(cx, cy, zoom, rect for the fx bakes)."""
    if name == "est":
        c = (860, 1010, 0.7)
        return c + (_view(*c),)
    if name == "stair":
        a, b = _stair_cam(t0, T), _stair_cam(t1, T)
        c = _stair_cam(t, T)
        return c + (_union(_view(*a), _view(*b)),)
    if name == "hide":
        c = (1290, 1330, 1.45)
        return c + (_view(*c),)
    if name == "shadow":
        c = (1580, 880, 1.8)
        return c + (_view(*c),)
    if name == "sneak":
        a, b = (1450, 1150, 1.15), (1570, 1150, 1.15)
        k = ease_in_out(seg(t, t0, t1))
        return (lerp(a[0], b[0], k), 1150, 1.15, _union(_view(*a), _view(*b)))
    if name == "troll":
        c = (1735, 900, 1.75)
        return c + (_view(*c),)
    if name == "react":
        c = (1335, 1240, 2.5)
        return c + (_view(*c),)
    if name == "turn":
        # a slow push-in while he turns round
        k = ease_in_out(seg(t, t0, t1))
        a, b = (1745, 920, 1.65), (1735, 910, 1.8)
        return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k), _union(_view(*a), _view(*b)))
    if name == "pipes":
        c = (1830, 900, 1.85)
        return c + (_view(*c),)
    # reform: slow push-in
    k = ease_in_out(seg(t, t0, t1))
    a, b = (1455, 1010, 1.75), (1460, 990, 1.85)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k), _union(_view(*a), _view(*b)))


# ============================================================================
# render
# ============================================================================
def _pings(name, t, T, head):
    if name == "hide":
        return [(T["hide"] + 0.6, head[0], head[1], 0.42), (T["hide"] + 1.45, head[0], head[1], 0.36)]
    if name == "react":
        return [(T["troll"] + 1.85, head[0], head[1], 0.5)]
    return None


def _shadow_gag(ctx, t, T, g1lens, g2, g2pat_fn):
    """The rookie's big shadow on the wall, cast by the gruff guard's beam."""
    if g1lens is None:
        return
    Lx, Ly, ang = g1lens
    k = 1.9
    a = 0.86 * smoothstep(seg(t, T["l2s"] + 0.3, T["l2s"] + 0.9)) * (1 - smoothstep(seg(t, T["g2a"] - 0.1,
                                                                                         T["g2a"] + 0.35)))
    if a <= 0.01:
        return
    ctx.save()
    _clip_out(ctx, [OCC_A])
    ctx.new_path()
    fx._cone_path(ctx, Lx, Ly, ang, 1100, 0.56 / 2 * 1.1, 10)
    ctx.clip()
    ctx.push_group()
    ctx.save()
    ctx.translate(Lx, Ly)
    ctx.scale(k, k)
    ctx.translate(-Lx, -Ly)
    g2pat_fn()
    ctx.restore()
    mask = ctx.pop_group()
    ctx.set_source_rgba(0.02, 0.05, 0.07, a)
    ctx.mask(mask)
    ctx.restore()


def render(ctx, t, info):
    T = _T(info)
    name, t0, t1 = _shot(t, T)
    cx, cy, z, rect = _cam(name, t, t0, t1, T)
    core.bg(ctx, "#03080b")
    g1 = _g1(t, T)
    g2 = _g2(t, T)
    ts = _tired(t, T)
    cxp, cyp, ckw = _curio(t, T)
    # who is in this shot
    show_g1 = name in ("est", "stair", "hide", "shadow", "sneak", "troll", "turn", "pipes")
    show_g2 = name in ("est", "stair", "hide", "shadow", "sneak")
    show_us = name in ("est", "hide", "shadow", "sneak", "react", "reform")
    show_c = name in ("est", "hide", "sneak", "troll", "turn", "pipes", "reform", "react")
    with core.camera(ctx, cx, cy, z):
        sets.shaft_lower(ctx, t)
        # --- characters into groups first (we need the lens positions for the cones)
        pats = {}
        lenses = {}
        d1 = 0.42
        d2 = 0.42
        if name == "shadow":
            d2 = 0.22          # lit from behind by the gruff guard's beam
        if show_g2:
            pats["g2"], _, lenses["g2"] = _draw_guard(ctx, t, info, g2, d2)
        if show_g1:
            pats["g1"], _, lenses["g1"] = _draw_guard(ctx, t, info, g1, d1)
        ta = None
        if show_us:
            dt = 0.46 if name != "reform" else 0.4

            def fT():
                return human.draw_person(ctx, "tired", ts["x"], ts["y"], SC, t, pose=ts["pose"],
                                         pose_t=ts["pose_t"], turn=ts["turn"], expr=ts["expr"],
                                         face=ts["face"], mouth=info.mouth("tired", t), outfit="sewer",
                                         bandage=True, power=POWER, hood=1.0, headphones=None)
            pats["t"], ta = _group(ctx, dt, fT)
        if show_c:
            dc = 0.3
            if name in ("turn", "pipes") and ckw.get("melt", 0) and ckw["melt"] >= 0.95 and t >= T["land"]:
                dc = 0.0       # the puddle in the beam: just a flat floor shadow
            pats["c"], _ = _group(ctx, dc, lambda: _draw_curio(ctx, t, cxp, cyp, ckw))
        # --- the dark world (+ quiet sense pings from his hood)
        head = ta["head"] if ta else (ts["x"], ts["y"] - 420)
        pings = _pings(name, t, T, head)
        if pings:
            fx.sense_reveal(ctx, t, pings, LIT, DARKW, key=("s03_sense", name), rect=rect, s=1.0 / z)
        # --- flashlight cones over the dark set
        if show_g2:
            _cone(ctx, t, lenses.get("g2"), g2, ("s03_lit", name), rect)
        if show_g1:
            _cone(ctx, t, lenses.get("g1"), g1, ("s03_lit", name), rect,
                  spread=0.64 if name == "shadow" else 0.56, exact=(name != "turn"))
        if name == "shadow" and show_g2:
            def g2shape():
                human.draw_person(ctx, "guard", g2["x"], g2["y"], g2["s"], t, pose=g2["pose"],
                                  pose_t=g2["pose_t"], turn=g2["turn"], expr="neutral", outfit=g2["outfit"],
                                  reach={"r": (*_hand_target(g2["x"], g2["y"], g2["s"], g2["ang"], g2["turn"]),
                                               g2["reach_w"], g2["ang"])}, shadow=False, drift=False)
            _shadow_gag(ctx, t, T, lenses.get("g1"), g2, g2shape)
        # --- paint back to front
        occ = [OCC_A, OCC_B]
        if show_g2:
            _paint(ctx, pats.get("g2"), occ if g2["lane"] == "back" else None)
        if show_g1:
            _paint(ctx, pats.get("g1"), occ if g1["lane"] == "back" else None)
        on_crate = t >= T["hop2"] - 0.25 and show_c
        if on_crate:
            _paint(ctx, pats.get("c"))
        if show_us:
            _paint(ctx, pats.get("t"))
        if show_c and not on_crate:
            _paint(ctx, pats.get("c"))
        if name in ("est", "stair"):
            sets.shaft_lower(ctx, t, layer="fg", parts=("stair",))
        # --- glows that stay bright in the dark
        if ta is not None and ta.get("hood_rim"):
            hx, hy = ta["hood_rim"]
            core.radial_glow(ctx, hx, hy, 34, TEAL, 0.32)
        if ta is not None and name == "react":
            # horror under the hood: a big anime sweat drop on the side of the hood
            hx, hy = ta["head"][:2]
            fx.emote(ctx, "sweatdrop", hx - 92, hy - 70, 0.45, t, T["troll"] + 2.0, dur=T["l3s"] - T["troll"] - 1.7)
        if show_g2:
            _lens_glow(ctx, lenses.get("g2"), g2)
        if show_g1:
            _lens_glow(ctx, lenses.get("g1"), g1)
    fx.vignette(ctx, 0.3)


# ============================================================================
# sound
# ============================================================================
def SFX(info):
    T = _T(info)
    ev = [(T["c1"], "flashlight_click", 2, -0.5), (T["c2"], "flashlight_click", 1, -0.35)]
    ev += sfx.loop_events("pod_hum", 0.0, info.dur, -14, 0.0)
    # boots on the steel stair, then on the floor (gruff: even; rookie: lighter, quicker)
    for (fn, gain, pan) in ((_g1, -9, -0.45), (_g2, -11, -0.3)):
        prev = None
        for i in range(int(info.dur * 24)):
            tt = i / 24.0
            g = fn(tt, T)
            if g["pose"] == "stand" or not isinstance(g["pose"], tuple):
                prev = None
                continue
            ph = int(g["pose_t"] * 2.0)          # two contacts per 1 s walk cycle
            if prev is not None and ph != prev:
                gn = gain if g["x"] < 2000 else gain - 6
                ev.append((tt, "footstep", gn, pan if g["x"] < 1200 else 0.25))
            prev = ph
    ev.append((T["hide"] + 0.04, "cloth_rustle", -3, 0.0))
    ev.append((T["hide"] + 0.6, "sonar_ping_small", -6, 0.0))
    ev.append((T["hide"] + 1.45, "sonar_ping_small", -9, 0.0))
    # the shadow jump: scuffle, landing, a nervous cloth shuffle
    ev.append((T["tj"], "cloth_rustle", 0, 0.1))
    ev.append((T["tj"] + 0.42, "footstep", -2, 0.1))
    ev.append((T["tj"] + 0.47, "footstep", -4, 0.1))
    # Curiosity's hop: claws on the wood lid
    ev.append((T["hop2"] - 0.03, "scratch_wood", -6, 0.1))
    # the troll wave: a tiny smug chitter only we hear? no: silence sells it.
    ev.append((T["troll"] + 1.85, "sonar_ping_small", -8, 0.0))
    ev.append((T["turn"] + 0.35, "cloth_rustle", -6, 0.25))
    ev.append((T["melt"], "creature_melt", 1, 0.1))
    ev.append((T["shrug"], "cloth_rustle", -5, 0.25))
    ev.append((T["reform"] - 0.13, "creature_reform", 1, 0.1))
    ev.append((T["reform"] + 0.95, "ears_perk", 0, 0.1))
    ev.append((T["rise0"] - 0.1, "sigh", 1, -0.1))
    return ev
