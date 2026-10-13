"""s03 - Flashlights ("TIREDNESS - Episode 2: Lights Out"), music "sneaky".

The lower level of the shaft, dark. Two guards with flashlights come down the
stair and search. Our two hide in FRONT of crate A while the guards walk the
lane BEHIND it (the crate is between them), then sneak after them. The gruff
guard carries a chunky key ring on his belt (tag "TOTALLY NOT THE POD KEYS", drawn here, visible
from his first appearance). Curiosity spots the keys, creeps up behind him and
slowly reaches for them; Tiredness whispers "Don't. We'll get caught."; it
sulks (eye-roll, paws back, flat look at him) and its paw grazes the keys: a
jingle. The guard heard that: he turns, it melts into a puddle; "Huh. Just
pipes."

Staging (world = sets.shaft_lower, people at s 0.75):
  stair (top-left) | crate A (1120..1706) | pallet | crate stack B | SERVICE TUNNEL
  our two: front lane FY (in front of crate A); guards: back lane BY (between
  the crates and the wall) -> the crate hides the guards' legs and shadows its
  own front face from their beams. The troll spot is on the floor just in front
  of crate A's right end, right behind the gruff guard (he stops in the gap
  between the crates), so the creature's paws can reach his keys.

Shot list (all times from cues / line times; see _T):
  est     0 .. l01-0.05     WIDE: dark; two beams click on at the stair top and
                            sweep; guards come down; our two freeze, ears up.
  stair   .. hide-0.05      MS gruff guard descending, "The boss says...": the
                            PODS key ring swings on his belt; it jingles as he stops.
  hide    .. l02-0.25       MS our two duck against crate A, quiet pings, the
                            rookie's upper body + beam pass over the crate top.
  shadow  .. sneak          MS rookie behind the crate: "I hate the dark."; the
                            gruff guard's beam throws his big shadow on the wall;
                            he jumps, lands, waves at it, it waves back, he hurries on.
  sneak   .. troll          MS-wide: gruff guard walks right over their heads; they
                            sneak after him (upright crouch), freeze when he glances
                            back; Curiosity slinks on ahead toward the gap behind him.
  troll   .. l03-0.42       MS: Curiosity low behind him looks up at him; its eyes
                            slide down to his belt and LOCK on the keys (glint, ears
                            perk), the troll grin; it creeps up two steps, rises on
                            its hind legs and slowly reaches for the keys.
  react   .. l03.end+0.3    MCU Tiredness frozen in horror; ping; whisper "Don't.
                            We'll get caught." with a tiny head shake on "Don't."
  sulk    .. l04-0.4        MS (= troll framing): paws inches from the keys; a flat
                            look at him, eye-roll, paws drawn back (grazing the keys:
                            they swing and jingle), deflates onto its haunches, flat
                            side-eye at him. The guard heard the jingle: eyes slide
                            back, brow up; 'turn': head, then body, the beam swings
                            round (slow push-in); the creature notices, ears up, and
                            at the last instant melts; the beam passes over the
                            puddle (just floor), the crate top, the pipes.
  pipes   .. reform+0.3     MS guard: "Huh. Just pipes." one-arm shrug, walks off.
  reform  .. end            two-shot: the puddle pops back up into Curiosity, smug,
                            happy wiggle; Tiredness slowly rises, exhales, lips
                            pressed, deadpan look down at it; it grins up at him.
"""
import math

import cairocffi as cairo

from engine import core, sets, human, creatures as CR, fx, props
from engine.core import tween, seg, lerp, clamp, smoothstep, ease_in_out, ease_out_back, hexc
from audio import sfx

M = sets.SHAFT_LOWER_MARKS
SC = 0.75            # people + creature scale (set char_scale)
SC2 = 0.72           # the rookie guard is a touch smaller
FY = 1640            # our two: front lane, in front of crate A (crouched heads stay below its top)
BY = 1455            # the guards' lane, behind the crates
POWER = 0.6          # Tiredness's teal irises (under the hood: the rim glow)
TX0, CX0 = 1180.0, 1335.0  # where our two hide
CXF = 1440.0               # Curiosity's freeze spot (front lane)
CXA = (1520.0, 1560.0)     # where it settles behind the gruff guard (start of 'troll')
CXR = (1610.0, 1534.0)     # where it reaches from (its paws meet his keys)
G1X = 1840.0               # where the gruff guard stops in the gap between the crates
RK_MAX = 0.5               # how far its paws get (the left edge of his key bunch)
DARKC = hexc(sets.DARK)
TEAL = core.PAL["power"]
INK = core.PAL["ink"]

# silhouettes (world) -------------------------------------------------------
OCC_A = [(1116, 1504), (1116, 1031), (1143, 996), (1710, 996), (1710, 1470), (1684, 1504)]
OCC_B = [(2056, 1504), (2056, 878), (2083, 842), (2390, 842), (2390, 1068), (2550, 1066),
         (2550, 1470), (2524, 1504)]
# crate A's front face + the floor in front of it: in the crate's shadow for a
# light behind / beside it (the guards' beams never light our two through it)
SHADOW_A = [(1104, 1032), (1702, 1032), (1726, 1500), (1800, 2800), (1000, 2800), (1096, 1500)]
# from the gruff guard's spot right of the crate the floor in front of its right
# end is in reach of his beam (the puddle in the beam = "just floor")
SHADOW_A2 = [(1104, 1032), (1702, 1032), (1702, 1500), (1470, 1500), (1330, 2800), (1000, 2800),
             (1096, 1500)]

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
HIDE_H = dict(HIDE, hunch=0.75)   # the same, shoulders up round his ears (holding his breath)
# the rookie's little wave at his own shadow (free l hand, bent elbow, palm out)
G2_WAVE = {"base": "stand", "period": 0.6, "al_p": 0.9, "al_o": 0.5, "al_e": 2.3,
           "al_eo": human.W(-0.5, 0.32, 0.0), "al_w": human.W(0.0, 0.2, 0.1), "al_h": "open",
           "al_tf": -1.0, "hunch": 0.35}
G2_ANTIC = {"base": "stand", "hunch": 1.2, "lean": -0.06, "nod": -0.05}
G2_LEAP = {"base": "leap_scared", "ar_h": "grip"}     # keeps hold of his flashlight
# the gruff guard's one-armed shrug: the flashlight (r) hand keeps the grip it has everywhere else
# (the plain shrug's open, palm-out r hand lay flat over the torch)
G1_SHRUG = {"base": "shrug", "ar_h": "relaxed", "ar_tf": 1.0}

# the key ring: clipped at the belt on the wearer's right hip toward the back
# (the near side while he faces screen-right), drawn in the l arm's z-slot so it
# sits over the hip and under the near arm, and goes behind the body with that
# arm when he faces left.
KEY_BETA = math.radians(108)
KEY_W = 72.0          # belt half-width at s=0.75
_DUMMY = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def _knee_rest(turn):
    """Top of his r knee in the HIDE crouch, as an offset from his ground point (s=SC): where his free r
    hand rests in the react MCU (the crouch's floor-bracing IK can't reach the floor, so that flat palm
    floated in mid-air beside the knee)."""
    a = human.draw_person(_DUMMY, "tired", 0.0, 0.0, SC, 0.0, pose=HIDE, turn=turn, outfit="sewer", hood=1.0,
                          shadow=False, drift=False)
    kx, ky = a["knee_r"][:2]
    return kx, ky - 35.0 * SC          # knee radius (leg_r[1] = 35 px at s=1)


_KNEE_R = {0.3: _knee_rest(0.3)}       # precomputed: the react shot's turn


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
    T["sulk"], T["turn"], T["melt"], T["reform"] = c("sulk"), c("turn"), c("melt"), c("reform")
    T["walkoff"] = c("walkoff", T["l4e"] + 0.45)
    T["jump"] = c("jump", T["l2e"] + 0.45)
    S, TR, SK = T["sneak"], T["troll"], T["sulk"]
    T["c1"], T["c2"] = 0.35, 0.6                     # flashlight clicks
    T["duck"] = T["c2"] + 0.55                       # a beam sweeps toward them: they duck (in the wide)
    T["tst"] = T["l1e"] + 0.05                       # the gruff guard stops on the lower steps
    T["tj"] = T["l2e"] + 0.1                         # the rookie jumps at his shadow
    T["g1a"], T["g1b"] = S - 0.3, TR - 0.42          # gruff guard walks right over their heads
    T["g2a"] = S - 0.28                              # the rookie hurries on, out ahead
    T["sn0"] = S + 1.25                              # Tiredness starts sneaking after him
    T["csn0"] = S + 1.05                             # Curiosity a beat earlier (it is bolder)
    T["fr0"], T["fr1"] = S + 2.0, S + 2.65           # freeze: he glances back, beam over the crate
    T["sn1"] = TR - 0.6                              # Tiredness's sneak ends
    T["carr"] = TR - 0.2                             # Curiosity arrives behind the guard
    # troll: spot the keys -> grin -> creep -> rise -> slow reach
    T["slide"] = TR + 0.3                            # its eyes slide down from his head to his belt
    T["glint"] = TR + 0.42                           # the keys glint
    T["lock"] = TR + 0.5                             # eyes lock on, ears perk
    T["grin"] = TR + 0.88                            # the troll grin
    T["cr0"], T["cr1"] = TR + 1.08, TR + 1.62        # creeps up two steps
    T["rise"] = TR + 1.76                            # up on its hind legs
    T["rch0"] = TR + 1.86                            # starts reaching
    T["react"] = T["l3s"] - 0.42                     # cut to Tiredness
    T["back"] = T["l3e"] + 0.3                       # cut back to it (the sulk shot)
    # sulk
    T["pull0"], T["pull1"] = SK + 0.12, SK + 0.72    # paws drawn back down
    T["brush"] = SK + 0.3                            # the near paw grazes the keys: they jingle
    T["sink"] = SK + 0.78                            # deflates back onto its haunches
    T["flat"] = SK + 1.25                            # the eye-roll is over: flat side-eye at him
    T["hear"] = T["brush"] + 0.45                    # the guard heard the jingle
    T["notice"] = T["turn"] + 0.75                   # it notices him turning
    T["land"] = T["melt"] + 0.55                     # beam lands where Curiosity was
    T["shrug"] = T["l4e"] - 0.2
    T["g1off"] = max(T["walkoff"], T["shrug"] + 0.6)
    T["rf0"] = T["reform"] + 0.4                     # the puddle starts rising (in the two-shot)
    T["rise0"] = T["reform"] + 0.6                   # Tiredness straightens up
    # the key ring's swings (t0, amplitude in rad, + = swings left)
    T["kicks"] = [(T["tst"], 0.16), (T["hide"] + 1.15, -0.08), (T["fr0"] - 0.08, 0.1),
                  (T["fr1"] + 0.05, -0.1), (T["g1b"], 0.14), (T["brush"], 0.36),
                  (T["turn"] + 0.45, -0.16), (T["shrug"], 0.08), (T["g1off"], -0.1)]
    T["shots"] = [("est", 0.0), ("stair", T["l1s"] - 0.05), ("hide", T["hide"] - 0.05),
                  ("shadow", T["l2s"] - 0.25), ("sneak", S), ("troll", TR),
                  ("react", T["react"]), ("sulk", T["back"]), ("pipes", T["l4s"] - 0.4),
                  ("reform", T["reform"] + 0.3)]
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
    """moves [(t0, t1, x0, x1[, v])] in time order -> (x, cycle time, walking 0..1).
    The cycle time is the travelled distance / each move's own planted-foot speed v
    (px/s), so the stride phase only advances with real travel (no foot sliding, no
    phase jumps when the facing changes)."""
    x, d, k = moves[0][2], 0.0, 0.0
    for mv in moves:
        t0, t1, a, b = mv[:4]
        v = mv[4] if len(mv) > 4 else 1.0
        if t >= t1:
            x = b
            d += abs(b - a) / v
        elif t > t0:
            x = _ramp(t, t0, t1, a, b, r)
            d += abs(x - a) / v
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
# the gruff guard's key ring ("PODS")
# ============================================================================
def _key_swing(t, T, g):
    th = 0.0
    if g.get("kw", 0.0) > 0.001:                      # two steps per 1 s walk cycle
        th += g["kw"] * 0.12 * math.sin(2 * math.pi * g["pose_t"] / 0.5 + 0.5)
    for t0, amp in T["kicks"]:
        if t > t0:
            u = t - t0
            if u < 3.0:
                th += amp * math.exp(-u / 0.55) * math.sin(2 * math.pi * u / 0.78)
    return th


def _key_clip(hip, turn, s):
    phi = math.radians(49.0) * turn
    k = s / SC
    return (hip[0] + KEY_W * k * math.sin(phi - KEY_BETA), hip[1] + 3.0 * k)


KEYS = [(-0.58, 44, "#c9a24a", "round"), (-0.2, 52, "#b9c1c9", "square"),
        (0.16, 47, "#d8b25a", "round"), (0.5, 38, "#9da6b0", "round")]


def _keyring(ctx, x, y, k, swing, rec=None):
    """A chunky key ring on a short chain from a belt clip at (x, y) (world).
    k = scale (1 at s=0.75). Hangs straight down, rotated by `swing` about the clip."""
    lw = 3.0 * k
    ctx.save()
    ctx.translate(x, y)
    core.rrect(ctx, -6.5 * k, -8 * k, 13 * k, 16 * k, 3 * k)          # belt clip
    core.fill_stroke(ctx, "#5f6873", INK, 2.6 * k)
    ctx.rotate(swing)
    # chain (3 links)
    for i in range(3):
        cy = (12 + i * 8) * k
        core.ellipse(ctx, 0, cy, 3.0 * k if i % 2 == 0 else 1.8 * k, 5.0 * k)
        core.stroke(ctx, INK, 4.2 * k, preserve=True)
        core.stroke(ctx, "#aab3bc", 1.8 * k)
    rr = 15.0 * k
    rcy = 34 * k + rr
    sway2 = -0.35 * swing                                                # the bunch lags a little
    # keys (behind the ring), fanned from its bottom
    for ang, L, col, bow in KEYS:
        ctx.save()
        ctx.translate(0, rcy + rr * 0.72)
        ctx.rotate(ang * 0.85 + sway2)
        L = L * k
        if bow == "round":
            core.circle(ctx, 0, 7.5 * k, 9.0 * k)
        else:
            core.rrect(ctx, -9 * k, -1 * k, 18 * k, 16 * k, 4 * k)
        core.fill_stroke(ctx, col, INK, lw)
        core.circle(ctx, 0, 5 * k, 2.6 * k)
        core.fill(ctx, INK)
        core.poly(ctx, [(-3.6 * k, 15 * k), (3.6 * k, 15 * k), (3.6 * k, L - 14 * k), (9.0 * k, L - 12 * k),
                        (9.0 * k, L - 7 * k), (5.5 * k, L - 5 * k), (9.0 * k, L - 2 * k), (6.0 * k, L + 2 * k),
                        (-3.6 * k, L + 2 * k)])
        core.fill_stroke(ctx, col, INK, lw * 0.9)
        ctx.move_to(-0.8 * k, 18 * k)
        ctx.line_to(-0.8 * k, L - 3 * k)
        core.stroke(ctx, core.mixc(col, "#ffffff", 0.45), 1.4 * k)
        ctx.restore()
    # the ring
    core.circle(ctx, 0, rcy, rr)
    core.stroke(ctx, INK, 7.0 * k)
    core.circle(ctx, 0, rcy, rr)
    core.stroke(ctx, "#c8d0d8", 3.4 * k)
    ctx.new_path()
    ctx.arc(0, rcy, rr, -2.5, -1.4)
    core.stroke(ctx, "#ffffff", 1.6 * k)
    # the tag, hanging in front from the ring's right side (over his trouser leg)
    ctx.save()
    ctx.translate(rr * 0.7, rcy + rr * 0.6)
    ctx.rotate(-0.08 + 0.6 * sway2)
    tw, th = 120 * k, 58 * k
    ctx.move_to(0, -2 * k)
    ctx.line_to(6 * k, 9 * k)
    core.stroke(ctx, INK, 2.4 * k)
    core.rrect(ctx, -4 * k, 7 * k, tw, th, 6 * k)
    core.fill_stroke(ctx, "#f6efd8", INK, lw)
    core.circle(ctx, 6 * k, 13 * k, 2.4 * k)
    core.fill(ctx, INK)
    # the gag: a label that protests too much
    cx_ = tw * 0.5 + 2 * k
    core.text(ctx, "TOTALLY NOT", cx_, 7 * k + 18 * k, size=12.5 * k, color="#8a1c1c", font="black")
    core.text(ctx, "THE POD", cx_, 7 * k + 34 * k, size=15 * k, color="#8a1c1c", font="black")
    core.text(ctx, "KEYS", cx_, 7 * k + 52 * k, size=17 * k, color="#8a1c1c", font="black")
    ctx.restore()
    if rec is not None:
        rec["ring"] = ctx.user_to_device(rr * 0.6, rcy - rr * 0.6)
    ctx.restore()
    if rec is not None and "ring" in rec:
        rec["ring"] = ctx.device_to_user(*rec["ring"])


# ============================================================================
# guards
# ============================================================================
def _g1(t, T):
    """The gruff guard (mustache): leads the search, says l01 / l04, wears the keys."""
    hide, S, TR, U, ML = T["hide"], T["sneak"], T["troll"], T["turn"], T["melt"]
    # down the stair (talking), a stop on the lower steps to sweep the room, then the lane
    tst = T["tst"]
    v0 = (700.0 - 120.0) / (tst - 0.11)
    vw = lambda tn: human.cycle_speed("guard", "walk", tn) * SC
    moves = [(-0.6, tst, 120.0 - 0.6 * v0, 700.0, vw(0.62)), (hide + 1.15, T["l2s"] + 0.2, 700.0, 820.0, vw(0.8)),
             (T["g1a"], T["fr0"] - 0.08, 820.0, 1480.0, vw(1.0)), (T["fr1"] + 0.05, T["g1b"], 1480.0, G1X, vw(1.0)),
             (T["g1off"], T["g1off"] + 3.2, G1X, 2750.0, vw(0.9))]
    x, d, kw = _path(t, moves)
    y = _lane_y(x)
    turn = tween(t, [(0.0, 0.62), (tst, 0.62), (tst + 0.4, 0.3), (hide + 0.9, 0.3), (hide + 1.3, 0.85),
                     (T["l2s"] + 0.1, 0.85), (T["l2s"] + 0.5, 0.5), (T["g1a"] - 0.15, 0.5), (T["g1a"] + 0.2, 1.0),
                     (T["fr0"] - 0.1, 1.0), (T["fr0"] + 0.22, -0.3), (T["fr1"] - 0.15, -0.3), (T["fr1"] + 0.12, 1.0),
                     (T["g1b"] - 0.2, 1.0), (T["g1b"] + 0.25, 0.7),
                     (U + 0.45, 0.7), (ML + 0.45, -0.75),
                     (T["shrug"] - 0.1, -0.75), (T["shrug"] + 0.25, -0.12), (T["shrug"] + 0.6, -0.12),
                     (T["g1off"] + 0.3, 0.9)])
    land = T["land"]
    ang = tween(t, [(0.0, 0.95), (1.1, 0.45), (2.2, 0.8), (3.3, 0.3), (tst + 0.2, 0.55),
                    (tst + 0.9, 1.25), (hide + 0.9, 0.75), (hide + 1.6, 0.1), (T["l2s"] + 0.2, -0.32),
                    (T["tj"] + 0.9, -0.3),
                    (T["g1a"] + 0.3, 0.25), (T["fr0"], 0.3), (T["fr0"] + 0.3, math.pi - 0.1), (T["fr1"] - 0.15, math.pi - 0.2),
                    (T["fr1"] + 0.15, 0.35), (T["g1b"], 0.45), (TR + 0.1, 0.55), (TR + 1.3, 0.4),
                    (TR + 2.4, 0.6), (T["sulk"] + 0.4, 0.52), (U + 0.4, 0.45), (ML - 0.05, 1.45),
                    (land, 1.95), (land + 0.45, 2.05),                      # the floor where it was
                    (land + 0.95, math.pi - 0.1), (land + 1.5, math.pi + 0.24),   # crate top, pipes
                    (T["l4s"] + 0.3, math.pi + 0.22),
                    (T["shrug"] - 0.05, math.pi + 0.04), (T["shrug"] + 0.3, 1.5), (T["g1off"], 1.35),
                    (T["g1off"] + 0.45, 0.4)])
    pose = ("stand", "walk", kw) if kw > 0.001 else "stand"
    ks = smoothstep(seg(t, T["shrug"], T["shrug"] + 0.25)) * (1 - smoothstep(seg(t, T["shrug"] + 0.6,
                                                                                    T["shrug"] + 0.85)))
    reach_w = 1.0
    if ks > 0.001:
        # blended over whatever he is doing: the walk-off starts before the shrug has released, and a
        # plain ("stand", shrug) blend there slid his feet, then snapped them into a full stride
        if kw > 0.001:
            # (his turn sweeps past the flashlight arm's front/back switch inside this blend: the same
            # explicit r-arm layer on every side, so the rig's arm detour can't flick it out for a frame;
            # it still goes behind him where the auto layer did, once he has turned past ~0.13)
            lay = "back" if turn > 0.13 else "mid"
            pose = (({"base": "stand", "ar_layer": lay}, {"base": "walk", "ar_layer": lay}, kw),
                    dict(G1_SHRUG, ar_layer=lay), ks)
        else:
            pose = (pose, G1_SHRUG, ks)
        # one-handed shrug: the free hand palm-up + shoulders + head; the flashlight hand
        # stays on its IK target (held low at his side) so it never jumps
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
    elif T["fr1"] <= t < T["fr1"] + 0.12:
        # head and eyes come back round WITH the body's whip-turn (fr1-0.15..fr1+0.12), not in one frame
        k = 1 - smoothstep(seg(t, T["fr1"], T["fr1"] + 0.12))
        look = (lerp(0.6, -0.85, k), lerp(0.15, 0.35, k))
        face = {"head_turn": -0.35 * k}
    if t >= TR - 0.5:
        expr = "bored"
        look = (0.7 + _wave(t, 0.7, 0.15, 3), 0.05)
        face["head_turn"] = 0.12 * math.sin((t - TR) * 1.3)
        if t >= TR + 1.6:          # a slow bored blink-and-sniff while it creeps up on him
            face["lid"] = 0.12 * smoothstep(seg(t, TR + 1.6, TR + 2.0))
    if t >= T["hear"]:
        # he heard something behind him: one brow up, eyes slide back first
        k = smoothstep(seg(t, T["hear"], T["hear"] + 0.25))
        look = (lerp(0.7, -0.8, k), lerp(0.05, -0.05, k))
        face = {"brow_l": 0.35 * k, "brow_r": 0.1 * k,
                "head_turn": lerp(0.12 * math.sin((T["hear"] - TR) * 1.3), -0.1, k)}
        expr = "bored" if k < 0.5 else "neutral"
    if t >= U:
        # the head leads the body round, but his eyes follow the beam down on the floor;
        # they only come up to the crate top once the beam gets there (after the melt)
        k = smoothstep(seg(t, U + 0.1, ML + 0.1)) * (1 - smoothstep(seg(t, ML + 0.3, ML + 0.6)))
        face["head_turn"] = lerp(-0.1, -0.4, k)
        face["head_nod"] = 0.12 * k
        look = (-0.55, 0.75)
        expr = "curious"
    if t >= land - 0.25:
        expr = "squint"
        if t < land + 0.6:
            look = (-0.55, 0.7)          # the floor where it was: nothing
        elif t < land + 1.2:
            look = (-0.7, 0.05)          # the crate top
        else:
            look = (-0.6, -0.25)         # the pipes
        face = {"brow_l": 0.15, "head_nod": 0.1 if t < land + 0.6 else 0.0}
        # finish the head's turn back from the floor over the turn branch's own release window
        # (ML+0.3..ML+0.6; this branch starts at land-0.25 = ML+0.3) instead of dropping it in one frame
        ht = -0.4 * (1 - smoothstep(seg(t, ML + 0.3, ML + 0.6)))
        if ht < -1e-4:
            face["head_turn"] = ht
    if t >= T["l4s"] - 0.1:
        expr = "deadpan"
        look = (-0.6, -0.1)
        face = {"head_tilt": 0.06 * smoothstep(seg(t, T["l4s"], T["l4s"] + 0.3))}
    if t >= T["shrug"]:
        expr = "unamused"
        face = {"brow_l": 0.25}
    if t >= T["g1off"]:
        expr = "bored"
        look = (0.6, 0.1)
        face = {}
    power = smoothstep(seg(t, T["c1"], T["c1"] + 0.08))
    # bored stance while he waits in the gap: thumb hooked in the front of his belt
    belt_w = smoothstep(seg(t, T["g1b"] + 0.15, T["g1b"] + 0.55)) * (1 - smoothstep(seg(t, T["hear"] + 0.1,
                                                                                        T["hear"] + 0.4)))
    return dict(who="guard", x=x, y=y, s=SC, turn=turn, pose=pose, pose_t=d, expr=expr,
                look=look, face=face, ang=ang, power=power, flicker=0.0, seed=0, outfit="default",
                mouth="guard", reach_w=reach_w, lane="stair" if x < 900 else "back", kw=kw, keys=True,
                belt_w=belt_w)


def _g2(t, T):
    """The rookie (scared of the dark): l02, the shadow jump."""
    S, tj = T["sneak"], T["tj"]
    v0 = (865.0 - 420.0) / (T["l1s"] - 0.2 - 0.11)
    vw = lambda tn: human.cycle_speed("guard", "walk", tn, _RK[1]) * SC2
    moves = [(-0.6, T["l1s"] - 0.2, 420.0 - 0.6 * v0, 865.0, vw(0.8)),
             (T["l1s"] - 0.2, T["l1s"] + 1.0, 865.0, 1160.0, vw(0.9)),
             (T["l1s"] + 1.0, T["l2s"] - 0.05, 1160.0, 1400.0, vw(0.3)),
             (T["g2a"], T["g2a"] + 3.3, 1400.0, 2400.0, vw(1.0))]
    x, d, kw = _path(t, moves)
    y = _lane_y(x)
    turn = tween(t, [(0.0, 0.8), (T["l1s"] + 0.3, 0.8), (T["l1s"] + 0.8, 0.5), (T["l2s"] - 0.3, 0.5),
                     (T["l2s"], 0.35), (T["g2a"] - 0.2, 0.35), (T["g2a"] + 0.15, 1.0)])
    ang = tween(t, [(0.0, 0.6), (0.9, 1.05), (1.7, 0.45), (2.6, 0.9), (3.4, 0.3), (4.3, 0.55),
                    (5.2, 0.2), (6.0, 0.5), (T["l2s"], 0.62), (tj, 0.6), (T["g2a"], 0.45),
                    (T["g2a"] + 1.0, 0.3), (T["g2a"] + 2.0, 0.6)])
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
    if T["l2s"] - 0.25 <= t < tj:      # from the shadow shot's first frame (was one frame after the cut)
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
    return dict(who="guard", x=x, y=y + dy, s=SC2, turn=turn, pose=pose, pose_t=d, expr=expr,
                look=look, face=face, ang=ang, power=power, flicker=0.6, seed=3, outfit=_RK[1],
                mouth="guard2", reach_w=reach_w, lane="stair" if x < 900 else "back", sweat=0.35)


def _draw_guard(ctx, t, info, g, dark, T=None):
    """Guard into a shaded group; returns (pattern, anchors, lens (x, y, ang), keys rec)."""
    rec = {}
    krec = {}
    s = g["s"]
    hx, hy = _hand_target(g["x"], g["y"], s, g["ang"], g["turn"])
    clip = None
    reach = {"r": (hx, hy, g["reach_w"], g["ang"])}
    if g.get("keys"):
        # where his belt is this frame (the hip bobs with the walk): a cheap anchor pass
        a0 = human.draw_person(_DUMMY, "guard", g["x"], g["y"], s, t, pose=g["pose"], pose_t=g["pose_t"],
                               turn=g["turn"], outfit=g["outfit"], seed=g["seed"], shadow=False, drift=False)
        clip = _key_clip(a0["hip"], g["turn"], s)
        swing = _key_swing(t, T, g)
        bw = g.get("belt_w", 0.0)
        if bw > 0.001:
            phi = math.radians(49.0) * g["turn"]
            # the front of his near hip (well clear of the buckle and of the keys)
            bx = a0["hip"][0] + KEY_W * (s / SC) * math.sin(phi - math.radians(52))
            reach["l"] = (bx, a0["hip"][1] + 2 * s, bw, 1.25)

    def hold(c, side, x, y, a_):
        if side == "l":
            if clip is None:
                return
            tn = g["turn"]
            if T["turn"] <= t <= T["g1off"] + 1.0 and tn < 0.4:
                # turning away: the keys slide behind his thigh gradually (the l arm, whose
                # slot they share, only switches behind the body at turn ~ -0.23, where
                # this clip already matches the thigh's edge -> no pop either way)
                e = a0["hip"][0] + lerp(-75.0, -5.0, smoothstep(clamp((tn + 0.15) / 0.55))) * (s / SC)
                c.save()
                c.rectangle(e - 3000, -6000, 3000, 12000)
                c.clip()
                _keyring(c, clip[0], clip[1], 1.3 * s / SC, swing, krec)
                c.restore()
            else:
                _keyring(c, clip[0], clip[1], 1.3 * s / SC, swing, krec)
            return
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
                                 hold=hold, hold_sides="lr" if clip is not None else "r",
                                 reach=reach,
                                 sweat=g.get("sweat", 0.0))
    pat, a = _group(ctx, dark, fn)
    return pat, a, rec.get("lens"), krec


def _cone(ctx, t, lens, g, key, rect, clip_shadow=True, length=980, spread=0.56, exact=True, shadow=None):
    if lens is None or g["power"] <= 0.01:
        return
    ctx.save()
    if clip_shadow:
        _clip_out(ctx, [shadow or SHADOW_A])
    fx.flashlight(ctx, lens[0], lens[1], lens[2], length, spread, t, LIT, key=key, rect=rect,
                  power=g["power"], flicker=g["flicker"], seed=g["seed"] + 1, lens=False, s=SC,
                  haze=0.04, exact=exact, hotspot=1.0 - 0.7 * max(0.0, math.sin(lens[2])))
    ctx.restore()


def _lens_glow(ctx, lens, g):
    if lens is None or g["power"] <= 0.01:
        return
    # the bright lens face only shows when the torch points sideways / up, not at the floor
    p = g["power"] * (1.0 - 0.75 * max(0.0, math.sin(lens[2])))
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
    duck = T["duck"]
    kd = smoothstep(seg(t, duck, duck + 0.28))
    if t < sn0 - 0.3:
        pose = ("stand", HIDE, kd) if kd < 1 else HIDE
        turn = lerp(0.15, 0.25, kd)
    elif t < sn1:
        k = smoothstep(seg(t, sn0 - 0.3, sn0))
        pose = (HIDE, "sneak", k) if k < 1 else "sneak"
        turn = lerp(0.25, 0.8, k)
        # the gruff guard glances back: he dips low and freezes mid-step
        kd2 = 0.7 * smoothstep(seg(t, fr0, fr0 + 0.16)) * (1 - smoothstep(seg(t, fr1 - 0.18, fr1)))
        if kd2 > 0.001:
            pose = ("sneak", HIDE, kd2)
    else:
        k = smoothstep(seg(t, sn1, sn1 + 0.35))
        pose = ("sneak", HIDE, k) if k < 1 else HIDE
        turn = lerp(0.8, 0.3, k)
        # horror: the shoulders creep up round his ears (held breath), drop as he exhales
        kh = smoothstep(seg(t, T["react"] - 0.15, T["react"] + 0.35)) * \
            (1 - smoothstep(seg(t, T["rise0"] - 0.3, T["rise0"] + 0.2)))
        if kh > 0.001 and k >= 1:
            pose = (HIDE, HIDE_H, kh)
        kr = ease_in_out(seg(t, T["rise0"], T["rise0"] + 1.1))
        if kr > 0:
            pose = (HIDE, "stand", kr) if kr < 1 else "stand"
            turn = lerp(0.3, 0.45, kr)
    expr = "bored"
    face = {"press": 0.15}
    # head acting under the hood (he 'looks' with the sense)
    if t < duck:
        k = smoothstep(seg(t, T["c1"] + 0.15, T["c1"] + 0.45))
        face = {"head_turn": -0.35 * k, "head_nod": -0.12 * k, "brow": 0.8 * k, "press": 0.2,
                "open": 0.08 * k}
        expr = ("bored", "alarmed", 0.35 * k)
    elif t < S + 0.3:
        # the beams pass over the crate: the hood tracks them, lips pressed
        k = smoothstep(seg(t, duck + 0.3, duck + 0.6))
        ht = -0.3 + 0.45 * smoothstep(seg(t, hide + 0.8, T["l2s"] - 0.6))
        face = {"head_turn": ht * k, "head_nod": -0.22 * k, "press": 0.6, "brow": 0.4}
        expr = "annoyed"
    elif t < T["react"] - 0.1:
        face = {"press": 0.55, "head_turn": 0.25, "head_nod": -0.1, "brow": 0.3}
        if t < sn0:     # the guard walks right over their heads
            face["head_turn"] = lerp(-0.2, 0.35, smoothstep(seg(t, S, sn0)))
            face["head_nod"] = -0.3
        kb = smoothstep(seg(t, S + 0.3, S + 0.55))
        if kb < 1:
            # ease out of the beam-tracking hold above (the hood snapped round in one frame at S+0.3)
            k0 = smoothstep(seg(t, duck + 0.3, duck + 0.6))
            prev = {"head_turn": (-0.3 + 0.45 * smoothstep(seg(t, hide + 0.8, T["l2s"] - 0.6))) * k0,
                    "head_nod": -0.22 * k0, "press": 0.6, "brow": 0.4}
            face = {kk: lerp(prev.get(kk, 0.0), face.get(kk, 0.0), kb) for kk in set(prev) | set(face)}
        if fr0 + 0.05 <= t < fr1:
            face = {"press": 0.9, "head_turn": 0.4, "head_nod": -0.15, "brow": 0.9, "width": -0.1}
        if t >= fr1 + 0.4:
            # Curiosity slinks on ahead without him: the hood follows it, lips tighten
            k = smoothstep(seg(t, fr1 + 0.4, sn1 + 0.3))
            face = {"press": lerp(0.55, 0.75, k), "head_turn": lerp(0.25, 0.5, k), "head_nod": -0.12,
                    "brow": lerp(0.3, 0.7, k)}
        expr = "annoyed"
    else:
        # react: frozen in horror (he senses it reaching): mouth a tight flat line, brows
        # up (nudging the hood rim), the head turned toward it
        R0 = T["react"]
        k = smoothstep(seg(t, R0 - 0.1, R0 + 0.12))
        # an "eek" grimace: teeth clenched, mouth stretched wide and tight
        face = {"press": 0.25, "teeth": 0.75 * k, "open": 0.1 * k, "width": 0.32 * k, "lip_up": 0.15 * k,
                "frown": 0.3 * k, "brow": lerp(0.7, 1.0, k), "head_turn": 0.4, "head_nod": -0.12 - 0.04 * k,
                "squash": -0.06 * k * (1 - seg(t, R0 + 0.12, R0 + 0.4))}
        expr = ("annoyed", "alarmed", k)
        if T["l3s"] - 0.25 <= t < T["l3s"] - 0.08:
            # ease the eek grimace into the whisper's tight lips below (was a one-frame mouth snap)
            kb = smoothstep(seg(t, T["l3s"] - 0.25, T["l3s"] - 0.08))
            w0 = T["l3s"]
            shake = 0.07 * math.sin(2 * math.pi * 2.6 * (t - w0)) * (1 - seg(t, w0, w0 + 0.6)) \
                * (t < w0 + 0.6)
            lean = 0.05 * smoothstep(seg(t, T["l3s"] + 0.45, T["l3s"] + 0.75))
            wf = {"press": 0.35, "brow": 0.85, "brow_ang": 0.5, "frown": 0.3, "width": -0.05,
                  "head_turn": 0.4 + shake, "head_nod": -0.12 + lean}
            face = {kk: lerp(face.get(kk, 0.0), wf.get(kk, 0.0), kb) for kk in set(face) | set(wf)}
            expr = (expr, ("alarmed", "annoyed", 0.4), kb)
        if t >= T["l3s"] - 0.08:
            # the whisper: lips stay tight, worried; a tiny "no" head shake on "Don't."
            w0 = T["l3s"]
            shake = 0.07 * math.sin(2 * math.pi * 2.6 * (t - w0)) * (1 - seg(t, w0, w0 + 0.6)) \
                * (t < w0 + 0.6)
            lean = 0.05 * smoothstep(seg(t, T["l3s"] + 0.45, T["l3s"] + 0.75))
            face = {"press": 0.35, "brow": 0.85, "brow_ang": 0.5, "frown": 0.3, "width": -0.05,
                    "head_turn": 0.4 + shake, "head_nod": -0.12 + lean}
            expr = ("alarmed", "annoyed", 0.4)
        if t >= T["l3e"] + 0.05:
            k2 = smoothstep(seg(t, T["l3e"] + 0.05, T["l3e"] + 0.3))
            face = {"press": 0.3, "teeth": 0.7 * k2, "open": 0.08 * k2, "width": 0.28 * k2, "frown": 0.3,
                    "brow": 0.9, "head_turn": 0.4, "head_nod": -0.08}
            expr = "alarmed"
        if t >= T["reform"] + 0.2:
            # slow exhale: cheeks puff, then release; lips pressed; then a deadpan look
            # down at it (it is on the floor to his right)
            kx = smoothstep(seg(t, T["rise0"] - 0.2, T["rise0"] + 0.9))
            face = {"press": lerp(0.9, 0.55, kx), "cheek": 0.5 * (1 - kx), "open": 0.15 * math.sin(math.pi * kx),
                    "brow": lerp(0.9, -0.2, kx), "head_turn": lerp(0.4, 0.5, kx), "head_nod": lerp(-0.08, 0.06, kx),
                    "curve": -0.1 * kx}
            expr = ("alarmed", "unamused", kx)
            if t >= T["rise0"] + 1.2:
                ks = smoothstep(seg(t, T["rise0"] + 1.2, T["rise0"] + 1.6))
                face = {"press": 0.6, "head_turn": lerp(0.5, 0.58, ks), "head_nod": lerp(0.06, 0.16, ks),
                        "head_tilt": -0.07 * ks, "brow": -0.2, "curve": -0.1}
                expr = "unamused"
    return dict(x=x, y=FY, turn=turn, pose=pose, pose_t=pt, expr=expr, face=face)


def _reach_amt(t, T):
    """Curiosity's slow reach for the keys (0..0.62), then drawn back in the sulk."""
    r = tween(t, [(T["rch0"], 0.0), (T["troll"] + 2.6, 0.36), (T["l3s"] + 0.6, RK_MAX)], smoothstep)
    if t > T["pull0"]:
        r = lerp(RK_MAX, 0.0, ease_in_out(seg(t, T["pull0"], T["pull1"])))
    return r


def _curio(t, T):
    """Curiosity: x, y, pose kwargs."""
    hide, S, TR, ML, R = T["hide"], T["sneak"], T["troll"], T["melt"], T["reform"]
    csn0, fr0, fr1 = T["csn0"], T["fr0"], T["fr1"]
    kw = dict(form=1.0, glow=0.6, flip=False)
    duck = T["duck"]
    if t < duck:
        k = ease_out_back(seg(t, T["c1"] + 0.1, T["c1"] + 0.3))
        kw.update(pose="stand", expr="surprised_soft" if t > T["c1"] + 0.1 else "calm",
                  ears=lerp(0.5, 1.0, k), face=lerp(1.0, -0.6, smoothstep(seg(t, T["c1"] + 0.1, T["c1"] + 0.4))),
                  look=(-0.5 * k, -0.4 * k))
        return CX0, FY + 12, kw
    if t < csn0 - 0.2:
        km = smoothstep(seg(t, duck + 0.02, duck + 0.32))
        kw.update(pose="perch", pose_from="stand", pose_mix=km, expr="wide", ears=lerp(1.0, 0.12, km),
                  glow=lerp(0.6, 0.4, km), look=(-0.45 + 0.7 * smoothstep(seg(t, hide + 0.8, T["l2s"] - 0.5)),
                                                  -0.7))
        if t >= S:
            kw["look"] = (lerp(-0.2, 0.6, smoothstep(seg(t, S, csn0 - 0.3))), -0.75)
        return CX0, FY + 12, kw
    # sneak along the crate front, freeze, then slink on ahead toward the gap behind
    # the gruff guard (angling in toward the crate's base line)
    carr = T["carr"]
    if t < carr:
        moves = [(csn0, fr0, CX0, CXF), (fr1 + 0.05, carr, CXF, CXA[0])]
        x, d, kmv = _path(t, moves, r=0.14)
        y = lerp(FY + 12, CXA[1], smoothstep(seg(x, CXF, CXA[0])))
        pt = d / (CR.SPEC_WALK_SPEED * SC)
        km = smoothstep(seg(t, csn0 - 0.2, csn0 + 0.1))
        kw.update(pose="walk", pose_t=pt, expr="calm", ears=0.4, glow=0.45, look=(0.5, -0.55), tilt=0.06)
        if km < 1:
            kw.update(pose_from="perch", pose_mix=km)
        if fr0 <= t < fr1 + 0.05:
            kw.update(pose="stand", pose_from="walk", pose_mix=smoothstep(seg(t, fr0, fr0 + 0.15)),
                      expr="wide", ears=0.1, look=(0.3, -0.8))
        elif t >= fr1 + 0.05:
            kw.update(expr="curious", ears=0.55, look=(0.45, -0.7))
            kr = smoothstep(seg(t, fr1 + 0.05, fr1 + 0.2))
            if kr < 1:
                kw.update(pose="walk", pose_from="stand", pose_mix=kr)
        return x, y, kw
    # ---- troll: sitting low right behind him
    keys_dir = (0.72, -0.52)          # from its eyes (sitting at CXA) up to his key ring
    if t < T["cr0"]:
        settle = smoothstep(seg(t, carr, carr + 0.3))
        look = tween(t, [(TR + 0.0, (0.3, -0.9)), (T["slide"], (0.3, -0.9)), (T["slide"] + 0.16, keys_dir)])
        expr = "calm"
        if t >= T["lock"]:
            expr = "surprised_soft"
        ears = tween(t, [(carr, 0.55), (T["lock"], 0.55), (T["lock"] + 0.18, 0.95), (T["grin"], 0.95),
                         (T["grin"] + 0.3, 0.74)], ease_out_back)
        tilt = 0.0
        tail = 0.0
        if t >= T["grin"]:
            expr = "troll"
            look = (keys_dir[0] - 0.4, keys_dir[1] + 0.08)        # the troll's own offset is added
            tilt = 0.08 * smoothstep(seg(t, T["grin"], T["grin"] + 0.25))
            tail = 0.3 * smoothstep(seg(t, T["grin"], T["grin"] + 0.4))
        kw.update(pose="sit", pose_from="walk", pose_mix=settle,
                  pose_t=(CXA[0] - CX0) / (CR.SPEC_WALK_SPEED * SC), expr=expr, look=look, ears=ears,
                  tilt=tilt, tail_curl=tail, face=lerp(1.0, 0.55, smoothstep(seg(t, T["grin"], T["grin"] + 0.3))))
        return CXA[0], CXA[1], kw
    troll_look = (keys_dir[0] - 0.4 + 0.05, keys_dir[1] + 0.08 - 0.05)
    if t < T["rise"]:
        # creeps up two slow steps, eyes locked on the keys, then settles on its haunches
        x = _ramp(t, T["cr0"], T["cr1"], CXA[0], CXR[0], 0.16)
        y = lerp(CXA[1], CXR[1], seg(x, CXA[0], CXR[0]))
        pt = (x - CXA[0]) / (CR.SPEC_WALK_SPEED * SC)
        k_in = smoothstep(seg(t, T["cr0"], T["cr0"] + 0.16))
        k_out = smoothstep(seg(t, T["cr1"] - 0.04, T["rise"] - 0.02))
        if k_out > 0:
            kw.update(pose="sit", pose_from="walk", pose_mix=k_out, pose_t=pt)
        else:
            kw.update(pose="walk", pose_from="sit", pose_mix=k_in, pose_t=pt)
        kw.update(expr="troll", look=troll_look, ears=0.7, tilt=0.12, tail_curl=0.3, face=0.55,
                  _sy=1.0 - 0.06 * k_out)
        return x, y, kw
    x, y = CXR
    SK = T["sulk"]
    if t < T["sink"] + 0.16:
        # up on its hind legs: the reach (and in the sulk the paws drawn back)
        rk = _reach_amt(t, T)
        # the rise: squashed to its sitting height at the switch, springs up, settles
        sy = tween(t, [(T["rise"], 0.72), (T["rise"] + 0.14, 1.05), (T["rise"] + 0.26, 1.0)], ease_in_out)
        if t >= T["sink"]:
            sy = lerp(1.0, 0.68, smoothstep(seg(t, T["sink"], T["sink"] + 0.16)))
        kw.update(pose="reach_up", reach=rk, expr="troll", look=(0.12, -0.25), ears=0.72, tail_curl=0.3,
                  face=0.55, _sy=sy)
        if t >= T["back"] - 0.02:
            # back from Tiredness's whisper: frozen mid-reach, grin gone, a flat look at him
            k = smoothstep(seg(t, T["back"], T["back"] + 0.12))
            kw.update(expr="annoyed", look=(-0.85 * k + 0.12 * (1 - k), 0.1), face=0.35, ears=0.6,
                      tail_curl=0.15)
        if t >= SK:
            # the eye-roll (pupils roll up and over to the left, back to him)
            kw.update(expr="eyeroll", pose_t=t - SK, look=(-0.8, 0.12), face=0.3,
                      ears=lerp(0.6, 0.32, smoothstep(seg(t, SK + 0.2, SK + 1.0))), tail_curl=0.0)
        return x, y, kw
    # back on its haunches, deflated; the roll finishes into a flat side-eye at him
    ksq = tween(t, [(T["sink"] + 0.16, 0.95), (T["sink"] + 0.38, 1.0)], ease_out_back)
    kw.update(pose="sit", expr="eyeroll", pose_t=t - SK, look=(-0.8, 0.12), face=0.3,
              ears=lerp(0.6, 0.32, smoothstep(seg(t, SK + 0.2, SK + 1.0))), tail_curl=0.0, _sy=ksq)
    if t >= T["flat"]:
        kw.update(expr="annoyed", look=(-0.85, 0.1), face=0.3, ears=0.3)
    if t >= T["notice"]:
        # it notices him turning round: ears shoot up, eyes wide, up at him
        k = ease_out_back(seg(t, T["notice"], T["notice"] + 0.2))
        kw.update(expr="wide", look=(0.45, -0.8), face=lerp(0.3, 0.8, smoothstep(seg(t, T["notice"],
                                                                                      T["notice"] + 0.25))),
                  ears=lerp(0.3, 1.0, k))
    if t < R:
        melt = tween(t, [(ML, 0.0), (ML + 0.45, 1.0)], smoothstep)
        if t > T["l4e"] + 0.1:
            melt = tween(t, [(T["l4e"] + 0.1, 1.0), (T["l4e"] + 0.4, 0.9)])
        if melt > 0:
            kw["melt"] = melt
            kw["glow"] = 0.6
        return x, y, kw
    # re-form: rises back up (springy over-stretch), smug, happy wiggle, then looks up at him
    R0 = T["rf0"]
    melt = tween(t, [(R0, 0.9), (R0 + 0.7, -0.15), (R0 + 0.95, 0.0)], ease_in_out)
    kw = dict(form=1.0, glow=0.6, flip=False)
    kw.update(pose="sit", melt=melt, expr="proud" if t > R0 + 0.35 else "calm",
              tail_curl=tween(t, [(R0 + 0.7, 0.2), (R0 + 1.2, 0.75)]),
              ears=tween(t, [(R0 + 0.6, 0.5), (R0 + 0.9, 0.8)], ease_out_back))
    wig = seg(t, R0 + 0.95, R0 + 1.85)
    if 0 < wig < 1:
        kw["tilt"] = 0.09 * math.sin(wig * 2 * math.pi * 3) * math.sin(math.pi * wig)
    if t >= R0 + 2.1:
        # the head turns to him over 0.2 s (its yaw jumped 1 -> 0.15 in one frame); the grin is on time
        kw.update(expr="troll", look=(-0.35, -0.65), ears=0.75, tail_curl=0.7,
                  face=lerp(1.0, 0.15, smoothstep(seg(t, R0 + 2.1, R0 + 2.3))))
    return x, y, kw


def _draw_curio(ctx, t, x, y, kw):
    kw = dict(kw)
    sq = kw.pop("_squash", 0.0)
    rot = kw.pop("_rot", 0.0)
    sy = kw.pop("_sy", 1.0)
    ctx.save()
    if sq or rot or sy != 1.0:
        ctx.translate(x, y)
        if rot:
            ctx.rotate(rot)
        if sq:
            ctx.scale(1 + sq, 1 - sq)
        if sy != 1.0:
            ctx.scale(1.0 + 0.4 * (1.0 - sy), sy)
        ctx.translate(-x, -y)
    a = CR.draw_specimen(ctx, x, y, SC, t, **kw)
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
TROLL_CAM = (1718, 1150, 1.75)


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
        c = (1560, 880, 1.8)
        return c + (_view(*c),)
    if name == "sneak":
        a, b = (1450, 1150, 1.15), (1570, 1150, 1.15)
        k = ease_in_out(seg(t, t0, t1))
        return (lerp(a[0], b[0], k), 1150, 1.15, _union(_view(*a), _view(*b)))
    if name == "troll":
        return TROLL_CAM + (_view(*TROLL_CAM),)
    if name == "react":
        c = (1335, 1240, 2.5)
        return c + (_view(*c),)
    if name == "sulk":
        # same framing as the troll shot; a slow push-in once he starts turning round
        a, b = TROLL_CAM, (1716, 1140, 1.88)
        k = ease_in_out(seg(t, T["turn"], t1))
        return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k), _union(_view(*a), _view(*b)))
    if name == "pipes":
        c = (1790, 985, 1.72)
        return c + (_view(*c),)
    # reform: two-shot, slow push-in
    k = ease_in_out(seg(t, t0, t1))
    a, b = (1490, 1185, 1.68), (1494, 1172, 1.78)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k), _union(_view(*a), _view(*b)))


# ============================================================================
# render
# ============================================================================
def _pings(name, t, T, head):
    if name == "hide":
        return [(T["hide"] + 0.6, head[0], head[1], 0.42), (T["hide"] + 1.45, head[0], head[1], 0.36)]
    if name == "react":
        return [(T["react"] + 0.08, head[0], head[1], 0.5)]
    return None


def _shadow_gag(ctx, t, T, g1lens, g2, g2pat_fn):
    """The rookie's big shadow on the wall, cast by the gruff guard's beam."""
    if g1lens is None:
        return
    Lx, Ly, ang = g1lens
    k = 1.8
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
    show_g1 = name in ("est", "stair", "hide", "shadow", "sneak", "troll", "sulk", "pipes")
    show_g2 = name in ("est", "stair", "hide", "shadow", "sneak")
    show_us = name in ("est", "hide", "shadow", "sneak", "react", "reform")
    show_c = name in ("est", "hide", "sneak", "troll", "sulk", "pipes", "reform")
    krec = {}
    with core.camera(ctx, cx, cy, z):
        sets.shaft_lower(ctx, t)
        # --- characters into groups first (we need the lens positions for the cones)
        pats = {}
        lenses = {}
        d1 = 0.42
        d2 = 0.42
        if name == "shadow":
            d2 = 0.22          # lit from behind by the gruff guard's beam
        if name in ("troll", "sulk"):
            d1 = 0.36          # the MS on his back / his keys: a touch more readable
        if show_g2:
            pats["g2"], _, lenses["g2"], _ = _draw_guard(ctx, t, info, g2, d2, T)
        if show_g1:
            pats["g1"], _, lenses["g1"], krec = _draw_guard(ctx, t, info, g1, d1, T)
        ta = None
        if show_us:
            dt = 0.46 if name != "reform" else 0.4
            treach = None
            if name == "react":
                tk = round(ts["turn"], 3)
                if tk not in _KNEE_R:
                    _KNEE_R[tk] = _knee_rest(tk)
                kx, ky = _KNEE_R[tk]
                treach = {"r": (ts["x"] + kx, ts["y"] + ky, 1.0)}

            def fT():
                return human.draw_person(ctx, "tired", ts["x"], ts["y"], SC, t, pose=ts["pose"],
                                         pose_t=ts["pose_t"], turn=ts["turn"], expr=ts["expr"],
                                         face=ts["face"], mouth=info.mouth("tired", t), outfit="sewer",
                                         bandage=True, power=POWER, hood=1.0, headphones=None,
                                         reach=treach)
            pats["t"], ta = _group(ctx, dt, fT)
        ca = None
        if show_c:
            dc = 0.3
            if name in ("sulk", "pipes") and ckw.get("melt", 0) and ckw["melt"] >= 0.95 and t >= T["land"]:
                dc = 0.0       # the puddle in the beam: just a flat floor shadow
            pats["c"], ca = _group(ctx, dc, lambda: _draw_curio(ctx, t, cxp, cyp, ckw))
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
                  spread=0.64 if name == "shadow" else 0.56,
                  exact=not (name == "sulk" and t >= T["turn"]),
                  shadow=SHADOW_A2 if name in ("sulk", "pipes") else None)
        if name == "shadow" and show_g2:
            def g2shape():
                human.draw_person(ctx, "guard", g2["x"], g2["y"], g2["s"], t, pose=g2["pose"],
                                  pose_t=g2["pose_t"], turn=g2["turn"], expr="neutral", outfit=g2["outfit"],
                                  reach={"r": (*_hand_target(g2["x"], g2["y"], g2["s"], g2["ang"], g2["turn"]),
                                               g2["reach_w"], g2["ang"])}, shadow=False, drift=False)
            _shadow_gag(ctx, t, T, lenses.get("g1"), g2, g2shape)
        # --- paint back to front (the guards in the back lane, then us in front)
        occ = [OCC_A, OCC_B]
        if show_g2:
            _paint(ctx, pats.get("g2"), occ if g2["lane"] == "back" else None)
        if show_g1:
            _paint(ctx, pats.get("g1"), occ if g1["lane"] == "back" else None)
        if show_us:
            _paint(ctx, pats.get("t"))
        if show_c:
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
            fx.emote(ctx, "sweatdrop", hx - 92, hy - 70, 0.45, t, T["react"] + 0.25,
                     dur=T["l3e"] - T["react"] + 0.1)
        if name == "troll":
            # the keys catch the light: a glint; then its eyes light up as they lock on
            if krec.get("ring"):
                fx.eye_glint(ctx, krec["ring"][0], krec["ring"][1], 0.8, t, T["glint"], dur=0.5,
                             halo="#fff0c8")
            if ca is not None and "eye_r" in ca:
                ex, ey = ca["eye_r"][:2]
                fx.eye_glint(ctx, ex + 4, ey - 6, 0.42, t, T["lock"] + 0.04, dur=0.36)
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
            p = g["pose"]
            walking = isinstance(p, tuple) and p[1] == "walk" and p[2] > 0.3
            if not walking:
                prev = None
                continue
            ph = int(g["pose_t"] * 2.0)          # two contacts per 1 s walk cycle
            if prev is not None and ph != prev:
                gn = gain if g["x"] < 2000 else gain - 6
                ev.append((tt, "footstep", gn, pan if g["x"] < 1200 else 0.25))
            prev = ph
    # his keys jingle as he stops on the stair (plants the sound for later)
    ev.append((T["tst"] + 0.04, "cage_rattle", -17, -0.35))
    ev.append((T["duck"] + 0.04, "cloth_rustle", -3, 0.0))
    ev.append((T["hide"] + 0.6, "sonar_ping_small", -6, 0.0))
    ev.append((T["hide"] + 1.45, "sonar_ping_small", -9, 0.0))
    # the shadow jump: scuffle, landing, a nervous cloth shuffle
    ev.append((T["tj"], "cloth_rustle", 0, 0.1))
    ev.append((T["tj"] + 0.42, "footstep", -2, 0.1))
    ev.append((T["tj"] + 0.47, "footstep", -4, 0.1))
    # troll: the glint, the ears perking as its eyes lock on (the creep itself is silent)
    ev.append((T["glint"] - 0.02, "sparkle", -15, 0.15))
    ev.append((T["lock"] + 0.02, "ears_perk", 1, 0.0))
    ev.append((T["react"] + 0.08, "sonar_ping_small", -8, 0.0))
    # sulk: its paw grazes the keys: a small jingle (what the guard hears)
    ev.append((T["brush"], "cage_rattle", -9, 0.15))
    ev.append((T["turn"] + 0.35, "cloth_rustle", -6, 0.25))
    ev.append((T["melt"], "creature_melt", 1, 0.1))
    ev.append((T["shrug"], "cloth_rustle", -5, 0.25))
    ev.append((T["rf0"] - 0.38, "creature_reform", 1, 0.1))     # its pop (~1.08 s in) = the over-stretch
    ev.append((T["rf0"] + 0.92, "ears_perk", 0, 0.1))
    ev.append((T["rise0"] - 0.1, "sigh", 1, -0.1))
    return ev


# Director: lift the deep shadows a little so the dark reads on a phone screen
# (applied when the segment is encoded; previews/sheets show the raw render).
POST_FILTER = "curves=all='0/0 0.06/0.10 0.2/0.265 0.5/0.56 1/1'"
