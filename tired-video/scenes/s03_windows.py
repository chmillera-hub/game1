"""s03 — windows (front of the house, bright day). Music "panic".

Embarrassment tries window 1, 2, 3 (all locked), panics, finds a rock,
apologises his way through a throw, smashes window 3, tiptoes in over the
glass and climbs in head-first (butt and kicking legs seen from outside).
The open, empty cage (from s02) hangs off his wrist, drops at the wail, is
scooped up on the tiptoe and goes in through the hole before him (s04 finds
it in the living room).

Shots (all timing derived from cues / line times):
  A  medium along the facade: dash -> heave w1 "Locked." -> lunge -> heave w2,
     rattle "Locked!" -> dash right (whip pan)
  B  w3 medium, push-in: big heave, wail "Why is everything locked?!", cage drops
  C  panic medium: wring_hands -> shake_arms (sweat flying, heat); freeze,
     pupils lock down-left, glasses glint
  D  insert: the rock on the lawn twinkles; his frozen shoes behind it
  E  medium: rises with the rock; guilty look left, look right, head tucked
  F1 wind-up "Sorry, sorry, sorry!" eyes squeezed shut (a pump per word) ->
     release, camera pulls out with the rock -> SMASH, shards, flinch
  F2 MCU: flinched, one-eye peek at the hole, then both, wince
  G  tracking medium: tiptoe over the glass, scoops the cage, whisper
     "I'll pay for that." (guilty glance at us)
  H  window medium: cage goes in, crouch, hop -> butt + kicking legs + flapping
     coat tails, slip in, beat, THUD, "oof", slow push into the hole
"""
import math

from engine import core, human, sets, props, fx
from engine.core import (tween, seg, clamp, lerp, ease_in_out, ease_out, ease_in,
                         ease_out_back, smoothstep, state_at, hash01)
from engine.human import IK, HK, A, L, P, cycle_speed

TAU = 2 * math.pi
M = sets.HOUSE_MARKS
ES = 0.45                    # Embarrassment's scale in the house world
CAGE_S = ES * 0.62           # cage scale (hand-carried)
ROCK_S = 0.6                 # lawn rock scale (sets API)
Y = 1600                     # feet line on the lawn, in front of the hedges
WIN = M["windows"]
W3X, W3Y = WIN[2][0] + WIN[2][2] / 2, WIN[2][1] + WIN[2][3] / 2     # (1985, 1145)

X0 = 1478                    # just off the porch steps (end of s02)
XW1, XW2, XW3 = 998, 1110, 1880   # feet spots: w1 facing left, w2/w3 facing right
XP = 1752                    # panic spot (backed off the window)
XT = 1700                    # pick-up / throw spot
ROCK_XY = (1616, 1624)
CAGE_REST = (1952, 1606)     # where the dropped cage lands (his right)
XTE = 1864                   # tiptoe end: scoops the cage, under window 3

E_COAT, E_COAT_SH = core.PAL["e_coat"], core.PAL["e_coat_sh"]
E_PANTS = core.PAL["e_pants"]
E_PANTS_DK = core.mixc(E_PANTS, "#000000", 0.25)
SHOE, SHOE_DK = "#7a4a2e", "#4f2f1e"
INK = core.PAL["ink"]
HOLE_DARK = "#2b2236"
HOLE_ROOM = "#4a3c58"
GLASS = "#cfe6f2"


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
_TC = {}


def _T(info):
    key = (id(info), info.dur)
    if key in _TC:
        return _TC[key]
    c, ln = info.cue, info.line
    T = dict(w1=c("win1"), w2=c("win2"), w3=c("win3"), panic=c("panic"), rock=c("rock"),
             smash=c("smash"), tip=c("tiptoe"), climb=c("climb"), heap=c("heap"), end=info.dur)
    for k, lid in (("l1", "s03_l01"), ("l2", "s03_l02"), ("l3", "s03_l03"), ("l4", "s03_l04"),
                   ("l5", "s03_l05")):
        T[k], T[k + "e"] = ln(lid).start, ln(lid).end
    # --- shot A
    T["r1e"] = T["w1"] + 0.10            # dash ends, skid
    T["k1e"] = T["w1"] + 0.25            # skid ends at window 1
    T["hv1"] = [T["w1"] + 0.36, T["w1"] + 0.60]
    T["r2s"] = T["l1e"] + 0.03           # snap turn + lunge to window 2
    T["r2e"] = T["w2"] + 0.08
    T["k2e"] = T["w2"] + 0.18
    T["hv2"] = [T["k2e"] + 0.02, T["k2e"] + 0.12]
    T["r3s"] = T["l2e"] + 0.02
    T["whip"] = T["w3"] - 0.16           # whip pan, cut at w3
    # --- shot B
    T["r4e"] = T["w3"] + 0.17
    T["k4e"] = T["w3"] + 0.27
    T["hv3"] = T["k4e"] + 0.0
    T["drop"] = T["l3"] + 0.09           # cage slides off his wrist
    # --- C/D/E
    T["ins0"] = T["rock"] + 0.34         # rock insert
    T["ins1"] = T["rock"] + 0.76
    T["lookL"] = T["ins1"] + 0.42
    T["lookR"] = T["ins1"] + 0.80
    # --- F
    T["rel"] = T["smash"] - 0.24         # rock leaves the hand
    T["F2"] = T["smash"] + 0.34          # cut to the flinch MCU
    T["peek"] = T["smash"] + 0.46
    T["tip0"] = T["tip"] + 0.14          # first tiptoe step
    T["G"] = T["tip0"] + 0.2             # cut to the tiptoe tracking shot
    T["tip1"] = T["l5e"] - 0.1           # tiptoe ends under window 3
    T["scoop"] = T["tip1"]               # dips for the cage
    T["scoop1"] = T["climb"]
    # --- H
    T["cage_in"] = T["climb"] + 0.02
    T["sill"] = T["climb"] + 0.4
    T["crouch"] = T["climb"] + 0.54
    T["hop"] = T["climb"] + 0.66
    T["slip"] = T["heap"] - 0.06
    T["gone"] = T["heap"] + 0.12
    T["thud"] = T["heap"] + 0.4
    T["words4"] = _word_starts(info, "s03_l04")
    _TC.clear()
    _TC[key] = T
    return T


def _word_starts(info, lid):
    ln = info.line(lid)
    out, last = [], -1
    t = ln.start
    while t < ln.end:
        w = info.word_at(t, lid)
        if w != last and w >= 0:
            out.append(t)
            last = w
        t += 0.01
    return out or [ln.start]


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
_PROBE = []


def _probe_ctx():
    if not _PROBE:
        import cairocffi as cairo
        _PROBE.append(cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 2, 2)))
    return _PROBE[0]


_NEG = ("look_x", "head_turn", "jaw", "asym", "smirk", "head_tilt")


def _sface(d, flip):
    """Face deltas authored in SCREEN terms -> rig terms (flip mirrors sides)."""
    if not d or not flip:
        return d
    out = {}
    for k, v in d.items():
        k2 = (k[:-2] + ("_r" if k.endswith("_l") else "_l")) if k.endswith(("_l", "_r")) else k
        if k in ("look_l", "look_r"):
            v = (-v[0], v[1])
        elif k in _NEG:
            v = -v
        out[k2] = v
    return out


def _emb(ctx, info, t, x, y, pose, expr, look=(0.0, 0.0), face=None, turn=0.0, flip=False,
         pose_t=None, blush=0.3, sweat=0.3, glint=0.0, hold=None, blink=None, s=ES):
    """Embarrassment, authored in screen terms (turn + = facing right)."""
    if flip:
        look = (-look[0], look[1])
        face = _sface(face, True)
        turn = -turn
    return human.draw_person(ctx, "embar", x, y, s, t, pose=pose, expr=expr, look=look,
                             mouth=info.mouth("embar", t), face=face, turn=turn, flip=flip,
                             pose_t=pose_t, blush=blush, sweat=sweat, glint=glint, hold=hold,
                             blink=blink)


def _cage(ctx, x, y, t, rot=0.0, s=CAGE_S, rattle=0.0):
    props.cage(ctx, x, y, s, t, door=1.0, latch="open", rattle=rattle, rot=rot, empty=True)


def _cage_hold(rot=0.0, wrist=False, rec=None):
    """hold= callback: cage by the handle in the hand, or hooked over the wrist
    (wrist=True) so the hand stays free. The rig draws it in the hold slot, so on
    the far arm it hangs behind him."""
    def cb(ctx, side, hx, hy, ang):
        if wrist:
            hx -= math.cos(ang) * 30 * ES
            hy -= math.sin(ang) * 30 * ES - 4 * ES
        if rec is not None:
            rec["p"] = (hx, hy)
        _cage(ctx, hx, hy, 0.0, rot)
    return cb


def _bump(t, t0, up=0.06, down=0.14):
    """0 -> 1 -> 0 envelope peaking at t0+up."""
    if t < t0 or t > t0 + up + down:
        return 0.0
    if t < t0 + up:
        return ease_out(seg(t, t0, t0 + up))
    return 1.0 - ease_in_out(seg(t, t0 + up, t0 + up + down))


def _travel_pt(x, x_start, pose, turn, s=ES, t0=0.0):
    """pose_t that keeps the planted foot locked for a mover at x."""
    sp = max(1.0, cycle_speed("embar", pose, turn) * s)
    return t0 + abs(x - x_start) / sp


def _dart(t, t0, pts, hold=0.16, tr=0.05):
    """Saccade look sequence: jump between pts every `hold` s."""
    if t < t0:
        return pts[0]
    i = int((t - t0) / hold)
    u = (t - t0) - i * hold
    a = pts[i % len(pts)]
    b = pts[(i + 1) % len(pts)]
    if u < hold - tr:
        return a
    k = smoothstep((u - (hold - tr)) / tr)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def _glint(t, t0, dur=0.3):
    if t < t0 or t > t0 + dur:
        return 0.0
    return math.sin(math.pi * (t - t0) / dur)


def _hole_pts():
    x, y, w, h = WIN[2]
    pts = []
    for i in range(16):
        a = i / 16 * TAU
        r = 0.62 + 0.3 * hash01(i, 2 + 5)
        pts.append((x + w / 2 + math.cos(a) * w * 0.5 * r, y + h / 2 + math.sin(a) * h * 0.5 * r))
    return pts


HOLE = _hole_pts()
HOLE_BOTTOM = max(p[1] for p in HOLE)


def _hole_path(ctx):
    core.poly(ctx, HOLE)


# ---------------------------------------------------------------------------
# poses
# ---------------------------------------------------------------------------
def heave_pose(k=0.0, sq=0.0, fist=False):
    """Both hands on the lower sash rail (sill height, in front of him); sq = knees
    bend for the yank, k = the heave (rises onto his toes, leans back)."""
    h = "fist" if fist else "grip"
    return P(IK("l", 0.0, 0.69, 0.27, h, wa=-0.5, wabs=0.6),
             IK("r", 0.03, 0.69, 0.25, h, wa=-0.5, wabs=0.6), hold=1.0,
             lean=0.22 + 0.12 * sq - 0.16 * k, hunch=0.5 + 0.35 * k, lift=7 * k, neck=0.08,
             **L("l", 0.3 + 0.25 * sq, k=0.15 + 0.6 * sq), **L("r", -0.12 + 0.2 * sq, k=0.08 + 0.6 * sq))


def heave_at(t, times, up=0.12, down=0.14):
    """(k, sq) for a list of heave times: squat 0.07 s before, yank up, settle."""
    k = sq = 0.0
    for th in times:
        sq = max(sq, _bump(t, th - 0.08, 0.07, 0.06))
        k = max(k, _bump(t, th, up * 0.5, down))
    return k, sq


RUN = "run_panic"
RUNC = {"base": "run_panic", "hold": 1.0}
SKID = P(A("l", 0.9, 0.7, 0.9, 0.2, h="splay"), A("r", 0.7, 0.5, 0.8, 0.2, h="splay"),
         L("l", -0.45, 0.1, 0.08, 0.3), L("r", 0.5, 0.1, 0.35, 0.0), hold=1.0, lean=-0.22, hunch=0.6,
         coat_trail=0.7, sway=0.0)
DEFLATE = P(A("l", 0.15, 0.1, 0.35, h="relaxed"), A("r", 0.12, 0.12, 0.3, h="relaxed"),
            hold=1.0, hunch=0.15, lean=0.12, neck=0.25, nod=0.08, **L("l", 0.1, k=0.08))
WAIL = P(HK("l", 72, -6, "claw", layer="front", wa=-1.6, wabs=0.7),
         HK("r", 72, -6, "claw", layer="front", wa=-1.6, wabs=0.7),
         hunch=0.55, neck=-0.2, nod=-0.28, lean=-0.06,
         **L("l", 0.18, 0.12, k=0.36), **L("r", -0.02, 0.12, k=0.32))
WAIL_SLUMP = P(HK("l", 76, 14, "claw", layer="front", wa=-1.6, wabs=0.7),
               HK("r", 76, 14, "claw", layer="front", wa=-1.6, wabs=0.7),
               hunch=0.8, neck=0.25, nod=0.24, lean=0.16,
               **L("l", 0.22, 0.12, k=0.42), **L("r", 0.0, 0.12, k=0.4))
WRING = "wring_hands"
SHAKE = "shake_arms"
PICK = "pick_up"
HOLD_ROCK = P(IK("r", 0.0, 0.58, 0.2, "grip", wa=1.2, wabs=0.6, layer="front"),
              IK("l", 0.03, 0.555, 0.2, "flat", wa=1.7, wabs=0.6, layer="front"),
              hunch=1.0, neck=-0.15, nod=0.12, lean=0.04, **L("l", k=0.12), **L("r", k=0.1))
THROW = P({"base": "throw"}, hunch=0.5, hold=0.0)
THROW_PUMP = P(HK("r", 95, -40, "grip", hz=-30, layer="mid", wa=-1.6, wabs=0.5),
               A("l", 1.2, 0.35, 0.3, h="open"), twist=-0.05, lean=0.02, side=0.04, hunch=0.5,
               **L("l", 0.45, 0.1, 0.2), **L("r", -0.2, 0.1, 0.25))
FOLLOW = P(A("r", 1.35, 0.25, 0.2, h="open"), A("l", 0.15, 0.3, 0.4, h="open"),
           lean=0.32, twist=0.25, hunch=0.4, **L("l", -0.3, k=0.12), **L("r", 0.5, k=0.3))
FLINCH = P({"base": "hands_up_small"}, hunch=1.0, lean=-0.14, neck=-0.1, nod=0.12,
           **L("l", 0.12, k=0.28), **L("r", -0.06, k=0.26))
TIPTOE = "tiptoe"
TIP_CAGE = {"base": "tiptoe", "hold": 1.0}
SCOOP = P({"base": "pick_up"}, hold=1.0)
CAGE_LIFT = P(IK("r", 0.04, 0.9, 0.34, "grip", wa=-0.6, wabs=0.6, layer="front"),
              IK("l", 0.08, 0.84, 0.3, "flat", wa=-0.6, wabs=0.6),
              lean=0.16, hunch=0.3, lift=10, **L("l", 0.15, k=0.05), **L("r", -0.2, k=0.0))
SILL = P(IK("l", 0.1, 0.7, 0.3, "flat", wa=0.1, wabs=0.9),
         IK("r", 0.1, 0.7, 0.3, "flat", wa=0.1, wabs=0.9),
         lean=0.3, neck=0.12, nod=-0.08, **L("l", k=0.06), **L("r", k=0.06))
SILL_CROUCH = P(SILL, lean=0.45, hunch=0.5, **L("l", 0.55, k=0.95), **L("r", 0.4, k=1.0))


# ---------------------------------------------------------------------------
# world drawing
# ---------------------------------------------------------------------------
def _house(ctx, t, T):
    broken = 2 if t >= T["smash"] else None
    sets.house_exterior(ctx, t, "bg", broken=broken, rock=False)
    if broken is not None:
        _hole_overlay(ctx, t)


def _hole_overlay(ctx, t):
    """A readable broken pane: dim room inside, glass teeth round the rim, broken muntins."""
    x, y, w, h = WIN[2]
    ctx.save()
    _hole_path(ctx)
    ctx.clip()
    ctx.rectangle(x, y, w, h)
    core.fill(ctx, HOLE_ROOM)
    core.radial_glow(ctx, x + w * 0.3, y + h * 0.35, w * 0.55, "#8a6a7a", 0.55)   # dim lamp light
    ctx.rectangle(x, y + h * 0.78, w, h * 0.3)                                    # floor shadow
    core.fill(ctx, core.alpha(HOLE_DARK, 0.8))
    # curtain edges seen inside
    core.smooth_path(ctx, [(x - 6, y), (x + w * 0.26, y), (x + w * 0.18, y + h * 0.6), (x + w * 0.24, y + h),
                           (x - 6, y + h)], closed=True)
    core.fill(ctx, "#c99a4a")
    core.smooth_path(ctx, [(x + w + 6, y), (x + w * 0.74, y), (x + w * 0.82, y + h * 0.6), (x + w * 0.76, y + h),
                           (x + w + 6, y + h)], closed=True)
    core.fill(ctx, "#c99a4a")
    ctx.restore()
    _hole_path(ctx)
    core.stroke(ctx, INK, 5)
    # glass teeth pointing in from the rim
    n = len(HOLE)
    for i in range(0, n, 2):
        p0, p1 = HOLE[i], HOLE[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        d = 0.18 + 0.22 * hash01(i, 71)
        tip = (mx + (W3X - mx) * d, my + (W3Y - my) * d)
        core.poly(ctx, [p0, tip, p1])
        core.fill_stroke(ctx, GLASS, INK, 3)
    # broken muntin stubs
    tr = "#f7efe0"
    for (ax, ay, bx, by) in ((x + w / 2, y - 2, x + w / 2, y + 26), (x + w / 2, y + h - 18, x + w / 2, y + h + 2),
                             (x - 2, y + h / 2, x + 30, y + h / 2), (x + w - 34, y + h / 2, x + w + 2, y + h / 2)):
        core.poly(ctx, [(ax, ay), (bx, by)], closed=False)
        core.stroke(ctx, INK, 12)
        core.poly(ctx, [(ax, ay), (bx, by)], closed=False)
        core.stroke(ctx, tr, 6)


def _lawn_props(ctx, t, T, draw_rock=True, draw_cage=True):
    if draw_rock and t < T["ins1"]:
        props.rock(ctx, ROCK_XY[0], ROCK_XY[1], ROCK_S)
    if draw_cage and T["drop"] <= t < T["scoop"] + 0.16:
        _cage_drop(ctx, t, T)


_DROP_PT = {}


def _cage_drop(ctx, t, T):
    """Cage sliding off his wrist at the wail, then lying on the lawn until the scoop."""
    t0 = T["drop"]
    hx, hy = _DROP_PT.get("p", (XW3 - 60, Y - 300))
    land = t0 + 0.26
    rest_y = CAGE_REST[1] - 268 * CAGE_S
    if t < land:
        u = seg(t, t0, land)
        x = lerp(hx, CAGE_REST[0], u)
        y = lerp(hy, rest_y, u * u)
        rot = 0.6 * u
    else:
        tau = t - land
        b = math.exp(-tau * 9) * abs(math.sin(tau * 20)) * 22
        x, y = CAGE_REST[0], rest_y - b
        rot = 0.45 * math.exp(-tau * 6) * math.cos(tau * 16) + 0.1
    _cage(ctx, x, y, t, rot)


def _shards(ctx, t, T):
    if t >= T["smash"]:
        props.shards(ctx, t, T["smash"], W3X - 10, W3Y + 30, seed=5, n=12, s=0.85, floor_y=Y + 14,
                     dir=-1, spread=0.42, power=0.85)
        props.shards(ctx, t, T["smash"], W3X + 10, W3Y + 40, seed=9, n=3, s=0.85, floor_y=Y + 10,
                     dir=1, spread=0.2, power=0.7)


def _rattle_marks(ctx, t, t0, x, y, w, h, seed=0, dur=0.2, big=1.0):
    if not (t0 <= t < t0 + dur):
        return
    k = 1 - seg(t, t0, t0 + dur)
    for side in (-1, 1):
        for j in range(2):
            ox = (x - 34 if side < 0 else x + w + 34) + side * j * 18
            oy = y + h * (0.4 + 0.32 * j) + 8 * hash01(j, seed)
            core.poly(ctx, [(ox, oy - 18 * big), (ox + side * 10 * big, oy), (ox, oy + 18 * big)], closed=False)
            core.stroke(ctx, core.alpha(INK, k), 5)


def _fence(ctx, t):
    sets.house_exterior(ctx, t, "fg", parts=("fence",))


# ---------------------------------------------------------------------------
# shot A — along the facade (0 .. w3)
# ---------------------------------------------------------------------------
def _emb_A(ctx, info, t, T):
    w1, l1, l1e, w2, l2, l2e = T["w1"], T["l1"], T["l1e"], T["w2"], T["l2"], T["l2e"]
    face = {}
    blush, sweat, flip = 0.3, 0.35, True
    turn, pt = -1.0, t
    if t < T["r1e"]:                       # dash left to window 1
        x = lerp(X0, XW1 + 46, t / T["r1e"])
        pose, pt = RUNC, _travel_pt(x, X0, RUN, -1.0)
        look, expr = (-0.85, -0.2), "panic"
        rot_c = 0.35 * math.sin(pt / 0.44 * TAU)
    elif t < T["k1e"]:                     # skid
        u = seg(t, T["r1e"], T["k1e"])
        x = lerp(XW1 + 46, XW1, ease_out(u))
        pose = (RUNC, SKID, smoothstep(seg(t, T["r1e"], T["r1e"] + 0.06)))
        pt = _travel_pt(XW1 + 46, X0, RUN, -1.0)
        look, expr = (-0.9, -0.35), "panic"
        rot_c = -0.4 * (1 - u)
    elif t < T["r2s"]:                     # heave, heave, "Locked."
        x = XW1
        k, sq = heave_at(t, T["hv1"])
        let_go = smoothstep(seg(t, l1 + 0.3, l1 + 0.5))
        pose = (SKID, (heave_pose(k, sq), DEFLATE, let_go), smoothstep(seg(t, T["k1e"] - 0.03, T["k1e"] + 0.07)))
        # pupils to the latch, then to us on "Locked." (head follows ~0.15 s later)
        look = tween(t, [(T["k1e"], (-0.8, -0.2)), (T["hv1"][1] + 0.1, (-0.8, -0.2)),
                         (l1 - 0.12, (-0.4, -0.55)), (l1 - 0.02, (0.35, 0.0)), (l1e - 0.12, (0.35, 0.05)),
                         (l1e - 0.05, (0.95, -0.05))])
        ht = tween(t, [(l1 + 0.04, 0.0), (l1 + 0.24, 0.6), (l1e - 0.04, 0.6), (l1e + 0.03, 0.3)])
        strain = max(k, sq, 0.5 * seg(t, T["k1e"], T["k1e"] + 0.05) * (1 - seg(t, l1 - 0.15, l1)))
        defl = smoothstep(seg(t, l1, l1 + 0.25))
        face = {"head_turn": ht, "teeth": 0.75 * strain, "press": 0.3 * strain, "lower": 0.35 * strain,
                "brow_ang": 0.4 * strain + 0.6 * defl, "cheek": 0.25 * strain, "frown": 0.4 * defl,
                "lid": 0.14 * defl, "brow": -0.12 * defl, "squash": 0.04 * sq - 0.03 * k}
        expr = state_at(t, [(0, "panic"), (l1 - 0.05, "sad")], 0.2)
        rot_c = 0.18 * k - 0.1 * sq + 0.12 * let_go * math.sin((t - l1) * 14) * math.exp(-(t - l1 - 0.3) * 4)
    elif t < T["k2e"]:                     # snap turn, lunge to window 2, skid
        flip = False
        u = seg(t, T["r2s"], T["r2e"])
        turn = 1.0
        if t < T["r2e"]:
            x = lerp(XW1, XW2 - 28, smoothstep(u))
            pose = (DEFLATE, RUNC, smoothstep(seg(t, T["r2s"], T["r2s"] + 0.05)))
            pt = _travel_pt(x, XW1, RUN, 1.0) + 0.11
        else:
            x = lerp(XW2 - 28, XW2, ease_out(seg(t, T["r2e"], T["k2e"])))
            pose = (RUNC, SKID, smoothstep(seg(t, T["r2e"], T["r2e"] + 0.05)))
            pt = _travel_pt(XW2 - 28, XW1, RUN, 1.0) + 0.11
        look, expr = (0.9, -0.25), "panic"
        blush = lerp(0.3, 0.42, u)
        rot_c = -0.35 * math.sin(u * math.pi)
    elif t < T["r3s"]:                     # yank x2, then rattles it yelling "Locked!"
        flip, turn = False, 1.0
        x = XW2
        k, sq = heave_at(t, T["hv2"], 0.08, 0.08)
        yell = smoothstep(seg(t, l2 - 0.02, l2 + 0.1))
        rat = yell * (1 - smoothstep(seg(t, l2e - 0.12, l2e)))
        jig = 0.5 + 0.5 * math.sin((t - l2) * TAU * 7.5)
        k = max(k, rat * jig)
        sq = max(sq, rat * (1 - jig) * 0.6)
        pose = (SKID, heave_pose(k, sq), smoothstep(seg(t, T["k2e"] - 0.03, T["k2e"] + 0.05)))
        look = tween(t, [(T["k2e"], (0.85, -0.3)), (l2 - 0.06, (0.85, -0.3)), (l2 + 0.02, (-0.35, -0.05)),
                         (l2e - 0.1, (-0.35, -0.05)), (l2e - 0.03, (0.95, -0.1))])
        ht = tween(t, [(l2 + 0.05, 0.0), (l2 + 0.2, -0.55), (l2e - 0.05, -0.55), (l2e + 0.04, -0.15)])
        face = {"head_turn": ht, "teeth": 0.6 * max(k, sq) * (1 - yell), "brow_ang": 0.45 + 0.25 * yell,
                "brow_in": 0.45 * yell, "lower": 0.2 * max(k, sq), "pupil": -0.2 * yell,
                "head_tilt": 0.03 * rat * math.sin((t - l2) * TAU * 7.5)}
        expr = state_at(t, [(0, "panic"), (l2 - 0.02, "alarmed")], 0.1)
        blush, sweat = 0.45, 0.45
        rot_c = 0.22 * (k - 0.5) * rat + 0.15 * k * (1 - rat)
    else:                                  # dash off to window 3 (whip)
        flip, turn = False, 1.0
        tt = t - T["r3s"]
        x = XW2 + 1150 * tt - 280 * max(0.0, 0.12 - tt)
        pose = (heave_pose(0.0), RUNC, smoothstep(seg(t, T["r3s"], T["r3s"] + 0.06)))
        pt = _travel_pt(x, XW2, RUN, 1.0)
        look, expr = (0.9, -0.15), "panic"
        blush, sweat = 0.45, 0.45
        rot_c = -0.35 * math.sin(pt / 0.44 * TAU)
    a = _emb(ctx, info, t, x, Y, pose, expr, look, face, turn, flip=flip, pose_t=pt, blush=blush,
             sweat=sweat, hold=_cage_hold(rot_c, wrist=True))
    return a, x


def _shot_A(ctx, info, t, T, dx=0.0):
    l1, l1e, l2, l2e = T["l1"], T["l1e"], T["l2"], T["l2e"]
    cx = tween(t, [(0.0, 1330), (T["k1e"] + 0.05, 948), (l1e, 952), (T["k2e"] + 0.05, 1175), (l2e, 1180),
                   (l2e + 0.3, 1430)])
    cy = tween(t, [(0.0, 1300), (T["k1e"], 1292), (l1e, 1270), (T["k2e"], 1290), (l2e, 1268)])
    z = tween(t, [(0.0, 1.95), (T["k1e"], 2.15), (l1 + 0.05, 2.35), (l1e, 2.45), (T["k2e"], 2.2),
                  (l2e - 0.1, 2.5)])
    with core.camera(ctx, cx - dx / z, cy, z):
        _house(ctx, t, T)
        a, x = _emb_A(ctx, info, t, T)
        if t < T["r1e"]:
            fx.motion_lines(ctx, x + 70, Y - 250, math.pi, 230, t, 0.9, width=9, seed=1)
        if t > T["r3s"] + 0.05:
            fx.motion_lines(ctx, x - 70, Y - 250, 0.0, 230, t, 0.9, width=9, seed=2)
        if T["r2s"] <= t < T["r2s"] + 0.12:
            fx.motion_lines(ctx, x - 50, Y - 250, 0.0, 120, t, 0.8, width=9, seed=3, n=3)
        fx.dust_puff(ctx, x - 40, Y, 0.5, t, T["r1e"], seed=1, dur=0.6)
        fx.dust_puff(ctx, x + 30, Y, 0.42, t, T["r2e"], seed=2, dur=0.5)
        for i, th in enumerate(T["hv1"]):
            _rattle_marks(ctx, t, th + 0.02, *WIN[0], seed=i)
        for i, th in enumerate(T["hv2"]):
            _rattle_marks(ctx, t, th + 0.02, *WIN[1], seed=4 + i)
        if l2 < t < l2e - 0.05:
            _rattle_marks(ctx, t, l2 + 0.2 * int((t - l2) / 0.2), *WIN[1], seed=9 + int((t - l2) / 0.2),
                          dur=0.18, big=1.3)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# shot B — window 3: heave + wail
# ---------------------------------------------------------------------------
def _emb_B(ctx, info, t, T):
    w3, l3, l3e = T["w3"], T["l3"], T["l3e"]
    blush, sweat = 0.5, 0.55
    face, cage_rot, pt = {}, None, t
    if t < T["r4e"]:
        x = lerp(1690, XW3 - 34, seg(t, w3, T["r4e"]))
        pose, pt = RUNC, _travel_pt(x, 1690, RUN, 1.0)
        turn, look, expr = 1.0, (0.9, -0.2), "panic"
        cage_rot = -0.35 * math.sin(pt / 0.44 * TAU)
    elif t < l3:
        u = seg(t, T["r4e"], T["k4e"])
        x = lerp(XW3 - 34, XW3, ease_out(u))
        k, sq = heave_at(t, [T["hv3"]], 0.1, 0.12)
        pose = (SKID, heave_pose(max(k, 0.2), sq), smoothstep(seg(t, T["r4e"] + 0.02, T["k4e"])))
        turn, look, expr = 1.0, (0.85, -0.3), "panic"
        face = {"teeth": 0.85, "press": 0.3, "lower": 0.45, "brow_ang": 0.55, "cheek": 0.3,
                "squash": 0.05 * sq}
        cage_rot = 0.3 * (1 - u) + 0.2 * k
    else:
        x = XW3
        u = smoothstep(seg(t, l3, l3 + 0.2))
        turn = lerp(1.0, 0.22, u)
        slump = smoothstep(seg(t, l3e - 0.12, l3e + 0.18))
        pose = state_at(t, [(0, heave_pose(0.3)), (l3 + 0.01, WAIL), (l3e - 0.12, WAIL_SLUMP)], 0.17)
        expr = "scream"
        sob = math.sin((t - l3) * TAU * 1.9)
        squeeze = smoothstep(seg(t, l3 + 0.05, l3 + 0.2))
        face = {"lid": 0.75 * squeeze, "lower": 0.55 * squeeze, "brow_ang": 0.9 * squeeze,
                "brow": 0.25 * squeeze, "head_nod": -0.22 * u * (1 - slump) + 0.12 * slump,
                "head_tilt": 0.07 * sob * (1 - slump), "squash": -0.07 * u * (1 - slump),
                "frown": 0.45 * slump}
        look = (0.0, 0.25 * slump)
        if t < T["drop"]:
            cage_rot = 0.2
        blush, sweat = 0.55, 0.65
    hold = _cage_hold(cage_rot, wrist=True, rec=_DROP_PT) if cage_rot is not None else None
    if hold is not None and isinstance(pose, tuple) and len(pose) == 3:
        pose = (_with_hold(pose[0]), _with_hold(pose[1]), pose[2])
    elif hold is not None:
        pose = _with_hold(pose)
    a = _emb(ctx, info, t, x, Y, pose, expr, look, face, turn, flip=False, pose_t=pt, blush=blush,
             sweat=sweat, hold=hold)
    return a, x


def _with_hold(p):
    if isinstance(p, tuple):
        return (_with_hold(p[0]), _with_hold(p[1]), p[2])
    if isinstance(p, str):
        return {"base": p, "hold": 1.0}
    d = dict(p)
    d["hold"] = 1.0
    return d


def _shot_B(ctx, info, t, T, dx=0.0):
    l3, l3e = T["l3"], T["l3e"]
    cx = tween(t, [(T["w3"], 1920), (l3, 1915), (l3e, 1895)])
    cy = tween(t, [(T["w3"], 1292), (l3, 1285), (l3e, 1245)])
    z = tween(t, [(T["w3"], 2.3), (l3, 2.35), (l3e, 2.85)])
    with core.camera(ctx, cx - dx / z, cy, z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T, draw_rock=False, draw_cage=False)
        if t < T["drop"]:
            _DROP_PT.pop("p", None)
        a, x = _emb_B(ctx, info, t, T)
        _lawn_props(ctx, t, T, draw_rock=False)
        if t < T["r4e"]:
            fx.motion_lines(ctx, x - 70, Y - 250, 0.0, 230, t, 0.9, width=9, seed=3)
        fx.dust_puff(ctx, x + 30, Y, 0.45, t, T["r4e"], seed=4, dur=0.55)
        _rattle_marks(ctx, t, T["hv3"] + 0.02, *WIN[2], seed=7, big=1.3)
        # tears flung from the squeezed eyes
        for i, ts in enumerate((l3 + 0.28, l3 + 0.6, l3 + 0.9)):
            fx.sweat_fly(ctx, a["eye_l"][0] - 8, a["eye_l"][1] + 4, 0.42, t, ts, seed=20 + i, n=2, side=-1)
            fx.sweat_fly(ctx, a["eye_r"][0] + 8, a["eye_r"][1] + 4, 0.42, t, ts + 0.05, seed=30 + i, n=2, side=1)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# shot C — panic; D — rock insert
# ---------------------------------------------------------------------------
_DART = [(-0.55, 0.1), (0.5, 0.0), (-0.35, -0.15), (0.6, 0.1), (-0.6, 0.0), (0.2, -0.2), (0.55, 0.05)]


def _emb_C(ctx, info, t, T):
    p0, rk = T["panic"], T["rock"]
    tw = p0 + 0.72
    pt = (t - p0) * 1.5 if t < tw else min(t, rk) - tw
    pose = state_at(t, [(0, WRING), (tw, SHAKE)], 0.12)
    if t < rk + 0.03:
        look = _dart(t, p0, _DART, hold=0.17)
    else:
        look = tween(t, [(rk + 0.03, _dart(rk + 0.03, p0, _DART, hold=0.17)), (rk + 0.11, (-0.72, 0.85))])
    wid = smoothstep(seg(t, rk + 0.1, rk + 0.25))
    hf = smoothstep(seg(t, rk + 0.17, rk + 0.37))
    expr = state_at(t, [(0, "panic"), (tw, "terrified"), (rk + 0.08, "surprised")], 0.12)
    face = {"wobble": 0.6 * (1 - wid), "teeth": 0.4 * (1 - wid), "pupil": -0.15 * (1 - wid) + 0.4 * wid,
            "hl": 0.6 * wid, "head_nod": 0.2 * hf, "head_turn": -0.28 * hf, "open": 0.1 * wid}
    return _emb(ctx, info, t, XP, Y, pose, expr, look, face, 0.12, pose_t=pt, blush=0.6,
                sweat=0.9, glint=_glint(t, rk + 0.12))


def _shot_C(ctx, info, t, T):
    p0, rk = T["panic"], T["rock"]
    z = tween(t, [(p0, 2.6), (rk, 2.8), (T["ins0"], 2.86)])
    cy = tween(t, [(p0, 1286), (rk, 1282)])
    cx = tween(t, [(p0, 1758), (rk, 1752)])
    with core.camera(ctx, cx, cy, z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T)
        a = _emb_C(ctx, info, t, T)
        tx, ty = a["top"]
        fx.heat_squiggles(ctx, tx, ty - 6, 0.5, t, 0.6)
        for i, ts in enumerate((p0 + 0.12, p0 + 0.42, p0 + 0.78, p0 + 1.02, p0 + 1.26)):
            ex, ey = a["eye_r"] if i % 2 else a["eye_l"]
            fx.sweat_fly(ctx, ex + (40 if i % 2 else -40) * ES, ey - 40 * ES, 0.5, t, ts, seed=40 + i, n=3,
                         side=(1 if i % 2 else -1))
        _fence(ctx, t)


def _shot_D(ctx, info, t, T):
    i0 = T["ins0"]
    z = tween(t, [(i0, 3.4), (T["ins1"], 3.65)])
    with core.camera(ctx, ROCK_XY[0] + 52, ROCK_XY[1] - 30, z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T)
        _emb_C(ctx, info, T["rock"] + 0.3, T)       # his frozen shoes behind the rock
        fx.eye_glint(ctx, ROCK_XY[0] - 14, ROCK_XY[1] - 14, 1.0, t, i0 + 0.06, dur=0.34, halo=None)
        fx.emote(ctx, "sparkle", ROCK_XY[0] + 20, ROCK_XY[1] - 44, 0.5, t, i0 + 0.08, dur=0.34)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# E / F1 — rock, guilty looks, wind-up, throw, smash ; F2 — flinch + peek MCU
# ---------------------------------------------------------------------------
def _emb_EF(ctx, info, t, T):
    i1, lL, lR, l4 = T["ins1"], T["lookL"], T["lookR"], T["l4"]
    rel, sm, pk, tp, tp0 = T["rel"], T["smash"], T["peek"], T["tip"], T["tip0"]
    x, pt = XT, t
    blush, sweat = 0.7, 0.7
    if t < l4:
        rise = ease_out_back(seg(t, i1 + 0.08, i1 + 0.36), 1.4)
        pose = (PICK, HOLD_ROCK, clamp(rise, 0, 1.08))
        hp = smoothstep(seg(t, i1 + 0.25, i1 + 0.45))
        look = tween(t, [(i1, (-0.4, 0.8)), (i1 + 0.3, (0.0, 0.15)), (lL - 0.02, (0.0, 0.15)),
                         (lL + 0.06, (-0.92, 0.05)), (lR - 0.02, (-0.92, 0.05)), (lR + 0.06, (0.92, 0.05)),
                         (l4 - 0.12, (0.92, 0.05)), (l4, (0.6, -0.3))])
        ht = tween(t, [(lL + 0.12, 0.0), (lL + 0.3, -0.4), (lR + 0.12, -0.4), (lR + 0.32, 0.4), (l4, 0.3)])
        face = {"head_turn": ht, "press": 0.55 * hp, "brow_ang": 0.6 * hp, "brow_in": 0.2 * hp,
                "lid": 0.06 * hp}
        expr = state_at(t, [(0, "surprised"), (i1 + 0.2, "guilty")], 0.2)
        turn = lerp(-0.6, 0.15, smoothstep(seg(t, i1 + 0.08, i1 + 0.36)))
        sweat = 0.75
    elif t < rel:
        wu = smoothstep(seg(t, l4, l4 + 0.22))
        pumps = 0.0
        for w in T["words4"][:-1]:
            pumps = max(pumps, _bump(t, w + 0.02, 0.1, 0.16))
        pose = (HOLD_ROCK, (THROW, THROW_PUMP, pumps * 0.85), wu)
        turn = lerp(0.15, 0.95, wu)
        expr = "pain"
        face = {"head_turn": -0.25 * wu, "head_tilt": -0.08 * wu, "brow_ang": 0.7, "teeth": 0.3,
                "squash": 0.04 * pumps}
        look = (0.3, 0.0)
        blush = 0.75
    elif t < sm:
        u = smoothstep(seg(t, rel, rel + 0.07))
        pose, turn = (THROW, FOLLOW, u), 0.95
        expr = "pain"
        face = {"head_turn": -0.25, "brow_ang": 0.7, "teeth": 0.4}
        look = (0.3, 0.0)
        blush = 0.75
    elif t < tp0:
        u = ease_out_back(seg(t, sm, sm + 0.12), 2.0)
        pose = (FOLLOW, FLINCH, clamp(u, 0, 1.1))
        turn = lerp(0.95, 0.5, smoothstep(seg(t, sm, sm + 0.15)))
        peek = smoothstep(seg(t, pk, pk + 0.12))
        both = smoothstep(seg(t, tp - 0.06, tp + 0.1))
        expr = state_at(t, [(0, "pain"), (pk, "terrified"), (tp, "guilty")], 0.12)
        # one-eye peek: the window-side (screen-right) eye cracks open, the other stays shut
        face = {"head_turn": -0.35 * (1 - both), "head_nod": 0.1 * (1 - both),
                "lid_l": 0.95 * peek * (1 - both), "lower_l": 0.55 * peek * (1 - both),
                "lid_r": -0.1 * peek, "brow_r": 0.3 * peek * (1 - both), "brow_ang": 0.6,
                "teeth": 0.5 * (1 - peek), "squash": 0.07 * (1 - seg(t, sm, sm + 0.25))}
        look = tween(t, [(sm, (0.0, 0.0)), (pk, (0.0, 0.0)), (pk + 0.1, (0.8, -0.45)), (tp - 0.05, (0.8, -0.45)),
                         (tp + 0.08, (0.45, 0.75))])
        blush = tween(t, [(sm, 0.75), (sm + 0.1, 0.9), (tp, 0.7)])
        sweat = 0.85
    else:
        x = _tip_x(t, T)
        pt = _travel_pt(x, XT, TIPTOE, 0.95)
        pose = (FLINCH, TIPTOE, smoothstep(seg(t, tp0 - 0.12, tp0 + 0.12)))
        turn, expr = 0.95, "guilty"
        look = (0.45, 0.8)
        face = {"press": 0.6, "brow_ang": 0.6, "head_nod": 0.12}
        blush = 0.65
    a = _emb(ctx, info, t, x, Y, pose, expr, look, face, turn, flip=True, pose_t=pt, blush=blush,
             sweat=sweat, glint=_glint(t, sm, 0.25) * 0.8)
    if T["ins1"] <= t < rel:
        hx, hy, _ = a["hand_r"]
        props.rock(ctx, hx, hy - 6, ROCK_S * 0.9, rot=0.2)
    return a, x


def _tip_x(t, T):
    """Tiptoe: XT -> scoop spot, dip for the cage, -> under window 3."""
    if t < T["scoop"]:
        return lerp(XT, XSC, seg(t, T["tip0"], T["scoop"]))
    if t < T["scoop1"]:
        return XSC
    return lerp(XSC, XTE, seg(t, T["scoop1"], T["tip1"]))


def _tip_pt(t, T):
    x = _tip_x(t, T)
    return _travel_pt(x, XT, TIPTOE, 0.95)


def _rock_flight(ctx, t, T, rx, ry):
    rel, sm = T["rel"], T["smash"]
    if not (rel <= t < sm):
        return
    u = seg(t, rel, sm)
    x = lerp(rx, W3X - 6, u)
    y = lerp(ry, W3Y + 5, u) - 60 * math.sin(math.pi * u)
    fx.motion_lines(ctx, x - 30, y, math.atan2(W3Y - ry, W3X - rx), 160, t, 0.9, width=8, seed=6, n=3)
    props.rock(ctx, x, y, ROCK_S * lerp(0.9, 0.7, u), rot=7 * u)


_REL_PT = {}


def _release_point(info, T):
    key = (id(info), T["rel"])
    if key not in _REL_PT:
        a, _ = _emb_EF(_probe_ctx(), info, T["rel"] - 1e-3, T)
        _REL_PT.clear()
        _REL_PT[key] = (a["hand_r"][0], a["hand_r"][1])
    return _REL_PT[key]


def _shot_EF(ctx, info, t, T):
    i1, l4, rel, sm = T["ins1"], T["l4"], T["rel"], T["smash"]
    cx = tween(t, [(i1, 1712), (l4, 1712), (rel - 0.05, 1730), (sm + 0.02, 1850)])
    cy = tween(t, [(i1, 1282), (l4, 1290), (rel - 0.05, 1300), (sm + 0.02, 1330)])
    z = tween(t, [(i1, 2.8), (l4, 2.75), (l4 + 0.45, 2.35), (rel - 0.05, 2.3), (sm + 0.02, 1.6)])
    sx, sy = core.shake(t, sm, 0.3, 9, seed=5)
    with core.camera(ctx, cx + sx / z, cy + sy / z, z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T)
        _shards(ctx, t, T)
        _emb_EF(ctx, info, t, T)
        if rel <= t < sm:
            rx, ry = _release_point(info, T)
            _rock_flight(ctx, t, T, rx, ry)
        fx.impact_star(ctx, W3X, W3Y, 0.62, t, sm, dur=0.42, word="SMASH!", seed=3)
        _fence(ctx, t)


def _shot_F2(ctx, info, t, T):
    f2, tp0 = T["F2"], T["tip0"]
    z = tween(t, [(f2, 3.1), (T["G"], 3.2)])
    cy = tween(t, [(f2, 1225), (tp0, 1225), (T["G"], 1212)])
    with core.camera(ctx, XT + 40, cy, z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T)
        _shards(ctx, t, T)
        a, _ = _emb_EF(ctx, info, t, T)
        fx.emote(ctx, "sweatdrop", a["top"][0] - 60 * ES, a["top"][1] + 70 * ES, 0.45, t, T["peek"] + 0.05)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# shot G — tiptoe over the glass, scoop the cage, whisper
# ---------------------------------------------------------------------------
def _emb_G(ctx, info, t, T):
    tp0, l5, l5e, sc, sc1 = T["tip0"], T["l5"], T["l5e"], T["scoop"], T["scoop1"]
    x = _tip_x(t, T)
    pt = _tip_pt(t, T)
    has_cage = t >= sc + 0.16
    if sc <= t < sc1:
        u = seg(t, sc, sc1)
        dip = math.sin(math.pi * u)
        pose = ((TIPTOE, TIP_CAGE, 0.0 if not has_cage else 1.0), SCOOP, dip * 0.85)
        look = (0.2, 0.9)
        face = {"brow_ang": 0.6, "press": 0.5}
        expr = "guilty"
    else:
        pose = TIP_CAGE if has_cage else TIPTOE
        # eyes on the glass, glance at the hole, guilty slide to us on "pay", back down
        look = tween(t, [(T["G"], (0.4, 0.85)), (sc - 0.15, (0.2, 0.9)), (sc1, (0.4, 0.85)),
                         (l5 - 0.1, (0.85, -0.35)), (l5 + 0.35, (0.85, -0.35)), (l5 + 0.45, (-0.2, 0.0)),
                         (l5e - 0.1, (-0.2, 0.0)), (l5e + 0.05, (0.5, 0.8))])
        ht = tween(t, [(l5 + 0.42, 0.0), (l5 + 0.6, -0.4), (l5e - 0.12, -0.4), (l5e + 0.05, 0.0)])
        expr = state_at(t, [(0, "guilty"), (l5 - 0.06, "whisper"), (l5e + 0.02, "guilty")], 0.15)
        mo = info.mouth("embar", t)[0]
        face = {"brow_ang": 0.75, "head_nod": 0.1, "head_turn": ht, "press": 0.55 * (1 - mo),
                "brow_in": 0.2}
    cage_rot = 0.15 * math.sin((t - sc) * 8) * math.exp(-max(0.0, t - sc) * 2) - 0.05
    a = _emb(ctx, info, t, x, Y, pose, expr, look, face, 0.95, flip=True, pose_t=pt, blush=0.6,
             sweat=0.6, hold=_cage_hold(cage_rot) if has_cage else None)
    return a, x


def _shot_G(ctx, info, t, T):
    x_now = _tip_x(t, T)
    cx = x_now + 85
    z = tween(t, [(T["G"], 2.05), (T["climb"], 2.2)])
    with core.camera(ctx, cx, tween(t, [(T["G"], 1300), (T["climb"], 1285)]), z):
        _house(ctx, t, T)
        _lawn_props(ctx, t, T)
        _shards(ctx, t, T)
        _emb_G(ctx, info, t, T)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# shot H — cage in, hop, butt + kicking legs, slip in, thud, "oof"
# ---------------------------------------------------------------------------
def _emb_H(ctx, info, t, T):
    cl, ci, sl, cr, hop = T["climb"], T["cage_in"], T["sill"], T["crouch"], T["hop"]
    x = XTE
    hold = None
    if t < sl:
        u = smoothstep(seg(t, cl, ci + 0.22))
        pose = (TIP_CAGE, CAGE_LIFT, u)
        hold = _cage_hold(-0.25 * u) if t < ci + 0.24 else None
        pt = _travel_pt(XTE, XT, TIPTOE, 0.95)
        expr, look = "guilty", (0.8, -0.6)
        face = {"brow_ang": 0.6, "press": 0.4}
    elif t < cr:
        pose, pt = (CAGE_LIFT, SILL, smoothstep(seg(t, sl, cr))), t
        expr, look = "determined", (0.8, -0.35)
        face = {"brow_ang": 0.4, "press": 0.6}
    else:
        k = smoothstep(seg(t, cr, cr + 0.1))
        pose, pt = (SILL, SILL_CROUCH, k), t
        expr, look = "determined", (0.8, -0.4)
        face = {"press": 0.7, "squash": 0.06 * k}
    up = ease_in(seg(t, hop, hop + 0.07))
    a = _emb(ctx, info, t, x + 60 * up, Y - 120 * up, pose, expr, look, face, 0.95, flip=True, pose_t=pt,
             blush=0.5, sweat=0.5, hold=hold)
    return a


def _cage_into_hole(ctx, t, T):
    """The cage leaves his hand and slides through the hole (clipped = inside)."""
    ci = T["cage_in"] + 0.24
    if not (ci <= t < ci + 0.5):
        return
    u = ease_in_out(seg(t, ci, ci + 0.32))
    x = lerp(W3X - 40, W3X + 10, u)
    y = lerp(W3Y - 40, W3Y - 20, u)
    ctx.save()
    _hole_path(ctx)
    ctx.clip()
    _cage(ctx, x, y, t, rot=-0.25 * (1 - u), s=CAGE_S * lerp(1.0, 0.72, u))
    _hole_path(ctx)
    core.fill(ctx, core.alpha(HOLE_DARK, 0.85 * u))
    ctx.restore()


def _butt_legs(ctx, t, T):
    """Custom: from outside, his butt stuck in the hole, legs kicking, coat tails flapping."""
    hop, sl, gone = T["hop"] + 0.07, T["slip"], T["gone"]
    if not (hop <= t < gone):
        return
    k_in = smoothstep(seg(t, sl, gone))
    k_up = ease_out_back(seg(t, hop, hop + 0.16), 1.8)
    tau = t - hop
    wig = math.sin(tau * TAU * 2.6)
    hx = W3X - 2 + 7 * wig * (1 - k_in)
    hy = W3Y + 36 + lerp(50, 0, k_up) - 30 * k_in
    tilt = 0.09 * wig * (1 - k_in)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(tilt)
    ctx.scale(ES, ES)
    sq = 1 - 0.9 * k_in          # legs fold up into the hole at the end
    # coat back going into the dark (receding, dimmed)
    core.smooth_path(ctx, [(-92, 10), (-104, -60), (-70, -150), (0, -178), (70, -150), (104, -60), (92, 10)],
                     closed=True)
    core.fill_stroke(ctx, core.mixc(E_COAT, HOLE_DARK, 0.5), INK, 9)
    core.smooth_path(ctx, [(-46, -120), (0, -150), (46, -120)])
    core.stroke(ctx, core.alpha(INK, 0.45), 6)
    # legs: thighs hang from the hips over the sill; shins kick (soles to us)
    for side, ph in ((-1, 0.0), (1, 0.5)):
        kick = 0.5 + 0.5 * math.sin(tau * TAU * 3.0 + ph * TAU)
        th_a = math.pi / 2 + side * (0.22 + 0.1 * kick)
        hip = (side * 40, 40)
        thl = 215 * sq
        knee = (hip[0] + math.cos(th_a) * thl, hip[1] + math.sin(th_a) * thl)
        sh_a = th_a + side * (0.2 + 0.85 * kick) - (math.pi * 0.85 * k_in * side)
        shl = 205 * (1 - 0.5 * kick) * sq
        ank = (knee[0] + math.cos(sh_a) * shl, knee[1] + math.sin(sh_a) * shl)
        _limb(ctx, hip, knee, 31, 26, E_PANTS)
        _limb(ctx, knee, ank, 26, 20, E_PANTS)
        _shoe_back(ctx, ank, sh_a, kick)
    # coat tails: split vent, flapping out to the sides
    fl = math.sin(tau * TAU * 4.3)
    for side in (-1, 1):
        f = fl * side
        core.smooth_path(ctx, [(side * 18, -46), (side * 102, -40), (side * (128 + 14 * f), 20 + 10 * f),
                               (side * (140 + 22 * f), 92 + 16 * f), (side * (92 + 10 * f), 84 + 8 * f),
                               (side * 70, 30)], closed=True)
        core.fill_stroke(ctx, E_COAT, INK, 9)
        core.smooth_path(ctx, [(side * 92, -10), (side * (116 + 12 * f), 66 + 12 * f)])
        core.stroke(ctx, E_COAT_SH, 7)
    # the butt: two round cheeks of slacks, up on the sill
    for side in (-1, 1):
        core.ellipse(ctx, side * 44, 6, 58, 54)
        core.fill_stroke(ctx, E_PANTS, INK, 9)
        core.ellipse(ctx, side * 56, -12, 18, 12)
        core.fill(ctx, core.mixc(E_PANTS, "#ffffff", 0.18))
    core.poly(ctx, [(0, -40), (0, 48)], closed=False)
    core.stroke(ctx, INK, 7)
    # coat hem across the waist
    core.smooth_path(ctx, [(-104, -46), (0, -60), (104, -46), (98, -30), (0, -40), (-98, -30)], closed=True)
    core.fill_stroke(ctx, E_COAT, INK, 8)
    ctx.restore()


def _limb(ctx, a, b, ra, rb, col):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
           (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)]
    core.poly(ctx, pts)
    core.fill_stroke(ctx, col, INK, 9)
    core.circle(ctx, b[0], b[1], rb - 4)
    core.fill(ctx, col)


def _shoe_back(ctx, p, ang, kick):
    """Loafer from behind: heel cup, and the sole showing more as the knee bends."""
    with core.saved(ctx, p[0], p[1], 1.0, ang - math.pi / 2):
        core.rrect(ctx, -30, -8, 60, 62, 26)
        core.fill_stroke(ctx, SHOE, INK, 8)
        so = 0.35 + 0.65 * kick
        core.rrect(ctx, -25, 52 - 46 * so, 50, 46 * so + 8, 14)
        core.fill_stroke(ctx, SHOE_DK, INK, 6)


def _oof(ctx, t, t0):
    if t < t0 or t > t0 + 0.95:
        return
    p = (t - t0) / 0.95
    k = ease_out_back(seg(p, 0, 0.22), 2.2)
    a = 1 - seg(p, 0.7, 1.0)
    if k < 0.02 or a < 0.02:
        return
    with core.saved(ctx, W3X + 26, W3Y - 20 - 50 * p, 0.62 * k, -0.12, alpha_=a):
        core.text(ctx, "oof", 0, 0, 64, "#fff7e8", "comic", "center", outline=INK, outline_w=10)


def _shot_H(ctx, info, t, T):
    cl, th = T["climb"], T["thud"]
    z = tween(t, [(cl, 2.25), (T["hop"], 2.35), (th, 2.45), (T["end"], 2.9)])
    cx = tween(t, [(cl, 1940), (T["hop"], 1972), (T["end"], 1985)])
    cy = tween(t, [(cl, 1268), (T["hop"], 1255), (T["end"], 1190)])
    sx, sy = core.shake(t, th, 0.28, 8, seed=11)
    with core.camera(ctx, cx + sx / z, cy + sy / z, z):
        _house(ctx, t, T)
        _shards(ctx, t, T)
        _lawn_props(ctx, t, T)
        if t < T["hop"] + 0.07:
            _emb_H(ctx, info, t, T)
        if T["hop"] <= t < T["hop"] + 0.3:
            fx.motion_lines(ctx, XTE + 60, Y - 260, -1.1, 220, t, 1.0, width=10, seed=8)
        _cage_into_hole(ctx, t, T)
        _butt_legs(ctx, t, T)
        fx.dust_puff(ctx, XTE + 20, Y, 0.45, t, T["hop"], seed=12, dur=0.5)
        fx.dust_puff(ctx, W3X, HOLE_BOTTOM - 6, 0.38, t, th, seed=13, dur=0.7)
        _oof(ctx, t, th + 0.04)
        _fence(ctx, t)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    dx = 0.0
    if T["whip"] <= t < T["whip"] + 0.32:
        dx, _ = fx.whip_pan_offset(t, T["whip"], 0.32, 1300, 1)
    if t < T["w3"]:
        _shot_A(ctx, info, t, T, dx)
    elif t < T["panic"]:
        _shot_B(ctx, info, t, T, dx)
    elif t < T["ins0"]:
        _shot_C(ctx, info, t, T)
    elif t < T["ins1"]:
        _shot_D(ctx, info, t, T)
    elif t < T["F2"]:
        _shot_EF(ctx, info, t, T)
    elif t < T["G"]:
        _shot_F2(ctx, info, t, T)
    elif t < T["climb"]:
        _shot_G(ctx, info, t, T)
    else:
        _shot_H(ctx, info, t, T)
    fx.whip_pan(ctx, t, T["whip"], 0.32, 1)


# ---------------------------------------------------------------------------
# sound
# ---------------------------------------------------------------------------
def SFX(info):
    T = _T(info)
    ev = []

    def steps(x0, x1, t0, t1, gain, pan, pose=RUN, turn=1.0, phase0=0.0):
        """One footstep per foot contact (cycle phase 0 / 0.5) of a foot-locked mover."""
        sp = cycle_speed("embar", pose, turn) * ES
        per = {"run_panic": 0.44, "tiptoe": 1.4}[pose]
        half = sp * per / 2
        d = 0.0
        dist = abs(x1 - x0)
        while d <= dist:
            tt = t0 + (t1 - t0) * d / max(dist, 1.0)
            if t0 <= tt < t1:
                ev.append((tt, "footstep", gain, pan))
            d += half
    steps(X0, XW1 + 46, 0.0, T["r1e"], -4, -0.2)
    steps(XW1, XW2 - 28, T["r2s"], T["r2e"], -6, 0.0)
    steps(XW2, XW2 + 300, T["r3s"] + 0.05, T["whip"] + 0.16, -6, 0.3)
    steps(1690, XW3 - 34, T["w3"], T["r4e"], -5, -0.1)
    for th in T["hv1"]:
        ev.append((th + 0.03, "door_bang", -12, -0.1))
    for th in T["hv2"]:
        ev.append((th + 0.02, "door_bang", -13, 0.0))
    n_r = int((T["l2e"] - 0.05 - T["l2"]) / 0.2)
    for i in range(n_r):
        ev.append((T["l2"] + 0.2 * i + 0.03, "door_bang", -12, 0.0))
    ev.append((T["whip"], "whoosh", -8, 0.3))
    ev.append((T["hv3"] + 0.03, "door_bang", -9, 0.1))
    ev.append((T["drop"] + 0.26, "cage_rattle", -6, -0.1))
    ev.append((T["panic"] + 0.72, "cloth_rustle", -6, 0.0))
    ev.append((T["ins0"] + 0.06, "sparkle", -9, -0.2))
    ev.append((T["ins1"] + 0.1, "cloth_rustle", -8, 0.0))
    ev.append((T["rel"] - 0.03, "whoosh", -5, 0.2))
    ev.append((T["smash"], "glass_smash", 0, 0.25))
    ev.append((T["tip0"], "tiptoe", -4, 0.0))
    ev.append((T["scoop1"] - 0.12, "cage_rattle", -12, 0.1))
    ev.append((T["cage_in"] + 0.5, "brick_thud", -16, 0.15))
    ev.append((T["hop"], "cloth_rustle", -4, 0.0))
    ev.append((T["hop"] + 0.6, "cloth_rustle", -7, 0.05))
    ev.append((T["slip"], "whoosh", -14, 0.0))
    ev.append((T["thud"], "body_thud", -2, 0.0))
    return ev
