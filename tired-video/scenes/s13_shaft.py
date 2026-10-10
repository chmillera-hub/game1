"""s13 -- the shaft ("What they were hiding").  Music: reveal (awe/sad/sting aligned to cues).

Shot list (every time derives from cues / line timings):
  SH1  walk + l01      junction A (variant 1): Tiredness trudges right, the creature trots at
                       his heels gazing up; it beams when he looks at it.  "Oh God. Why me."
  SH2a tunnels         junction B (variant 3): same framing, same stride (deja vu).
  SH2b tunnels + l02   junction C (variant 2): he stops, turns his back to the wall and slides
                       down it to the floor, head knocking back.  "We're never getting out..."
  SH3  point           low medium on the creature: it points a paw down the dark side tunnel, "!".
  SH4  l03             MCU, deadpan: eyes slide to the tunnel and back, one brow up a hair.
  SH5  roll            CU creature: slow sassy eyeroll into a flat stare.
  SH6  annoy + l04     two-shot escalation: chitter -> bites his cuff and tugs his arm out ->
                       headbutts his shin -> poke poke -> puppy eyes; he crumbles (sigh).
                       "Fine."  It hops for joy; he gets up and follows.
  SH7  enter           inside the side tunnel: rim-lit silhouettes walk toward a growing teal light.
  SH8  enter/reveal    the shaft: they step out of the tunnel mouth, he looks up; huge pull-out.
  SH9  wide            CU: pupils widen, then his lids open FULLY (the payoff), teal glints. Hold.
  SH10 sad             two-shot: he lowers his gaze to it, sad; it gazes up at the pods, ears down.
  SH11 l05             MCU over pods of sleeping creatures: "...Is this your family?"
  SH12 nod             two-shot: it turns to him, small nod + sad chirp, leans on his leg; his
                       hand comes to rest on its head (faint smile).
  SH13 title           pull back to the wide rim-lit silhouette + end card (captions hidden).
"""
import math

import cairocffi as cairo

from engine import core, sets, fx
from engine import creatures as CR
from engine.core import (tween, seg, state_at, clamp, lerp, smoothstep, ease_out_back,
                         ease_in_out, ease_out, ease_in)
from engine.human import draw_person, cycle_speed, resolve_face
from audio import sfx as _sfx

TAU = 2 * math.pi

# ----------------------------------------------------------------------------
# staging constants
# ----------------------------------------------------------------------------
SW = sets.SEWER_MARKS
FEET = SW["walk_feet_y"]                 # 1282
TUN = SW["side_tunnel"]                  # variant -> (x, top, w, h)
WALL_X = SW["wall_lean_x"]               # 640
SP = 0.75                                # people in the sewer
KC = 0.95                                # creature scale relative to Tiredness (s12: 0.70 / 0.75)
SC = SP * KC
SH_S = sets.SHAFT_MARKS["char_scale"]    # 0.22 on the catwalk
SH_FEET = sets.SHAFT_MARKS["catwalk_feet_y"]
SH_TX = -150                             # Tiredness's spot on the catwalk

TK = dict(outfit="sewer", bandage=True, headphones=None)
CX_SEW = WALL_X + 262     # creature's sitting spot, in front of the side tunnel

TS = 0.62                                # trudge tempo
TRUDGE = ("walk", "slouch", 0.3)
TURN_W = 0.9
_V1 = cycle_speed("tired", "walk", TURN_W, "sewer") * 0.7     # px/s at s=1, tempo 1
STRIDE_T = _V1 * SP                      # px per second of pose time (sewer)
V_T = STRIDE_T * TS                      # his ground speed in the sewer
STRIDE_C = CR.SPEC_WALK_SPEED * SC       # creature px per second of pose time

SIT = {"base": "sit_floor", "lean": -0.15, "chest": 0.1, "neck": 0.15, "tilt": 0.0, "hunch": 0.7,
       "ll_p": 2.0, "ll_o": 0.3, "ll_k": 2.4, "lr_p": 1.9, "lr_o": 0.28, "lr_k": 2.35, "breath": 0.7}
SIT_TURN = 0.22


# ----------------------------------------------------------------------------
# timing
# ----------------------------------------------------------------------------
def _times(info):
    c = info.cue
    T = {k: c(k) for k in ("walk", "tunnels", "point", "roll", "annoy", "enter", "reveal",
                           "wide", "sad", "nod", "title")}
    for i in range(1, 6):
        lid = f"s13_l0{i}"
        L = info.line(lid)
        T[f"l{i}"], T[f"l{i}e"] = L.start, L.end
    T["end"] = info.dur
    T["sh2b"] = T["tunnels"] + (T["l2"] - T["tunnels"]) * 0.5
    T["sh6"] = min(T["roll"] + CR.EYEROLL_DUR + 0.12, T["l4"] - 1.4)
    T["sh8"] = T["enter"] + min(0.8, (T["reveal"] - T["enter"]) * 0.5)
    return T


def wt(info, lid, i):
    """Start time of word i of a line (lip-sync word starts; proportional fallback)."""
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts") if hasattr(info, "_lip") else None
    if ws and 0 <= i < len(ws):
        return L.start + ws[i]
    n = max(1, len(L.text.split()))
    return L.start + L.dur * i / n


def decel(t, t_stop, x_stop, v, ramp=0.4):
    """Mover at speed v that eases to a stop at x_stop at t_stop -> x."""
    if t >= t_stop:
        return x_stop
    t0 = t_stop - ramp
    if t < t0:
        return x_stop - v * (t0 - t) - v * ramp * 0.5
    u = (t - t0) / ramp
    # remaining = v*ramp * int_u^1 (1 - smoothstep)  ;  int_0^u smoothstep = u^3 - u^4/2
    rem = v * ramp * ((1 - u) - (0.5 - (u ** 3 - u ** 4 / 2)))
    return x_stop - rem


def gaze(t, keys, lag=0.15, hx=0.22, hy=0.16):
    """Eyes lead, head follows `lag` later.  -> (look, head_turn, head_nod)."""
    lk = tween(t, keys)
    hk = tween(t - lag, keys)
    return lk, hk[0] * hx, hk[1] * hy


def fsum(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def slow_blink(t, t0, close=0.35, hold=0.2, open_=0.4):
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0),
                     (t0 + close + hold + open_, 0.0)])


def squash_at(t, t0, amt=0.12, dur=0.22):
    """(sx, sy) plop squash that settles with overshoot."""
    if t < t0 or t > t0 + dur:
        return (1.0, 1.0)
    k = (t - t0) / dur
    a = amt * math.sin(k * math.pi) * (1 - k * 0.4)
    return (1 + a * 0.7, 1 - a)


def _plop(ctx, x, y, sq):
    """Context manager-ish helper: scale about a ground point."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sq[0], sq[1])
    ctx.translate(-x, -y)


# ----------------------------------------------------------------------------
# silhouettes / light casts (group masks)
# ----------------------------------------------------------------------------
def lit_group(ctx, draw_fn, sil=0.0, rim=None, rim_dx=6.0, rim_dy=0.0, cast=None):
    """Draw draw_fn(ctx) and optionally darken it into a silhouette with a rim light.

    sil 0..1: darkening; rim: colour of the un-darkened edge (light from the side the
    mask is shifted AWAY from: rim_dx > 0 keeps a strip on the right edge).
    cast: (pattern_fn, alpha) -> a light gradient multiplied into the figure only."""
    ctx.push_group()
    draw_fn(ctx)
    pat = ctx.pop_group()
    ctx.set_source(pat)
    ctx.paint()
    if cast is not None:
        grad, a = cast
        ctx.push_group()
        ctx.set_source(grad)
        ctx.paint_with_alpha(a)
        g2 = ctx.pop_group()
        ctx.set_source(g2)
        ctx.mask(pat)
    if sil > 0.001:
        ctx.push_group()
        ctx.set_source(pat)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.set_source_rgba(0.035, 0.07, 0.09, min(1.0, sil))
        ctx.paint()
        if rim is not None:
            # rim = the shape minus itself shifted away from the light
            ctx.push_group()
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.set_source(pat)
            ctx.paint()
            m0 = pat.get_matrix()
            pat.set_matrix(cairo.Matrix(x0=rim_dx, y0=rim_dy).multiply(m0))
            ctx.set_operator(cairo.OPERATOR_DEST_OUT)
            ctx.set_source(pat)
            ctx.paint()
            pat.set_matrix(m0)
            rmask = ctx.pop_group()
            ctx.set_source_rgba(*core.hexc(rim, min(1.0, 0.25 + sil)))
            ctx.mask(rmask)
        ov = ctx.pop_group()
        ctx.set_source(ov)
        ctx.paint()


# ----------------------------------------------------------------------------
# characters
# ----------------------------------------------------------------------------
def tired(ctx, x, y, s, t, info, lidcap=0.64, **kw):
    """Tiredness with lip-sync and sewer outfit.  lidcap limits how far looking DOWN
    drags his (already heavy) lids shut, so he stays visibly watching."""
    kw.setdefault("mouth", info.mouth("tired", t))
    for k, v in TK.items():
        kw.setdefault(k, v)
    if lidcap is not None:
        look = kw.get("look", (0, 0))
        face = dict(kw.get("face") or {})
        F = resolve_face("tired", kw.get("expr", "neutral"), face)
        ly = look[1] + F.get("look_y", 0.0)
        if ly > 0:
            eff = F["lid"] + 0.22 * ly
            if eff > lidcap:
                face["lid"] = face.get("lid", 0.0) - min(0.22 * ly, eff - lidcap)
                kw["face"] = face
    return draw_person(ctx, "tired", x, y, s, t, **kw)


_PROBE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2))


def spec_offsets(s, t, **kw):
    """Anchors of the creature drawn at ground (0, 0) (for placing it by an anchor)."""
    return CR.draw_specimen(_PROBE, 0.0, 0.0, s, t, **kw)


def creature(ctx, x, y, s, t, sq=(1.0, 1.0), **kw):
    if sq != (1.0, 1.0):
        _plop(ctx, x, y, sq)
        a = CR.draw_specimen(ctx, x, y, s, t, **kw)
        ctx.restore()
        return a
    return CR.draw_specimen(ctx, x, y, s, t, **kw)


def sewer_cam_y(z, feet_screen):
    return FEET - (feet_screen - 960) / z


# ----------------------------------------------------------------------------
# walker positions (shared by render and SFX so steps land on contacts)
# ----------------------------------------------------------------------------
def x_sh1(t, T):
    return TUN[1][0] - 200 - V_T * (T["tunnels"] - t)


def x_sh2a(t, T):
    return TUN[3][0] - 300 - V_T * (T["sh2b"] - t)


def x_sh2b(t, T):
    return decel(t, T["l2"] - 0.06, WALL_X, V_T, 0.42)


def _push_t(T):
    return T["l4"] + 0.42


def x_sh6(t, T):
    t_walk = _push_t(T) + 0.45
    if t <= t_walk:
        return WALL_X
    u = t - t_walk
    return WALL_X + (V_T * u * u / 0.5 if u < 0.25 else V_T * (0.125 + (u - 0.25)))


def x_sh7(t, T):
    return 520 + V_T * 1.15 * (t - T["enter"])


SH_WALK_V = _V1 / 0.7 * SH_S             # plain walk on the catwalk


def x_sh8(t, T):
    t_stop = min(T["sh8"] + 0.62, T["reveal"] - 0.2)
    return decel(t, t_stop, SH_TX, SH_WALK_V, 0.38)


# ============================================================================
# SH1  walk + l01  (junction A)
# ============================================================================
def sh1(ctx, t, T, info):
    t_end = T["tunnels"]
    xt = x_sh1(t, T)
    xc = xt - 236
    k = ease_in_out(seg(t, 0, t_end))
    z = lerp(1.5, 1.6, k)
    camx = xt - (lerp(560, 700, seg(t, 0, t_end)) - 540) / z
    camy = sewer_cam_y(z, 1420)
    l1, l1e = T["l1"], T["l1e"]
    w_why = wt(info, "s13_l01", 2)
    look, ht, hn = gaze(t, [(0, (0.2, 0.25)), (l1 - 0.42, (0.2, 0.25)), (l1 - 0.26, (-0.75, 0.55)),
                            (w_why - 0.12, (-0.75, 0.55)), (w_why + 0.08, (0.1, -0.9)),
                            (l1e + 0.02, (0.1, -0.9)), (l1e + 0.3, (0.25, 0.22))])
    weary = smoothstep(seg(t, l1 - 0.1, l1 + 0.25))
    face = {"head_turn": ht, "head_nod": hn - 0.1 * smoothstep(seg(t, w_why, w_why + 0.2))
            * (1 - smoothstep(seg(t, l1e, l1e + 0.4))),
            "brow_ang": 0.42 * weary, "frown": 0.22 * weary, "lid": 0.04 * weary,
            "brow_in": 0.15 * weary}
    expr = state_at(t, [(0, "bored"), (l1e + 0.04, "sigh"), (l1e + 0.6, "bored")], 0.22)
    blink = None
    if t < 0.95:
        blink = slow_blink(t, 0.25, 0.3, 0.12, 0.35)
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=1)
        tired(ctx, xt, FEET, SP, t, info, pose=TRUDGE, pose_t=xt / STRIDE_T, turn=TURN_W,
              expr=expr, look=look, face=face, blink=blink)
        # creature at his heels, gazing up adoringly; beams when he looks at it
        happy = l1 - 0.05 <= t < l1 + 0.55
        CR.draw_specimen(ctx, xc, FEET + 8, SC, t, pose="walk", pose_t=xc / STRIDE_C,
                         expr="content" if happy else "calm", look=(0.5, -0.85),
                         tilt=-0.08)


# ============================================================================
# SH2a / SH2b  tunnels + l02
# ============================================================================
def sh2a(ctx, t, T, info):
    v = 3
    xt = x_sh2a(t, T)
    xc = xt + 262
    z = 1.45
    with core.camera(ctx, TUN[v][0] - 170, sewer_cam_y(z, 1400), z):
        sets.sewer(ctx, t, variant=v)
        tired(ctx, xt, FEET, SP, t, info, pose=TRUDGE, pose_t=xt / STRIDE_T, turn=TURN_W,
              expr="bored", look=(0.3, 0.12), face={"lid": 0.1, "brow_ang": 0.25})
        CR.draw_specimen(ctx, xc, FEET + 8, SC, t, pose="walk", pose_t=xc / STRIDE_C,
                         expr="calm", look=(0.8, -0.05))


def sh2b(ctx, t, T, info):
    v = 2
    l2, l2e = T["l2"], T["l2e"]
    t_stop = l2 - 0.06
    xt = x_sh2b(t, T)
    c_stop = t_stop + 0.12
    xc = decel(t, c_stop, CX_SEW, V_T, 0.45)
    z = lerp(1.45, 1.55, ease_in_out(seg(t, l2, T["point"])))
    camx = TUN[v][0] - 170
    camy = sewer_cam_y(z, 1400)
    # pose: walk -> stop -> turn the back to the wall -> slide down it to the floor
    walk_w = 1 - smoothstep(seg(t, t_stop - 0.42, t_stop))
    pose_walk = (TRUDGE, "slouch", 1 - walk_w)
    t_land = l2 + 0.5
    ks = ease_in(seg(t, l2 + 0.1, t_land)) ** 0.8
    pose = (pose_walk, SIT, ks)
    turn = lerp(TURN_W, SIT_TURN, smoothstep(seg(t, l2 - 0.05, l2 + 0.25)))
    # face: head knocks back on the wall, eyes to the ceiling; then rolls forward to the creature
    w_here = wt(info, "s13_l02", 5)
    look, ht, hn = gaze(t, [(0, (0.3, 0.12)), (l2 + 0.05, (0.3, 0.12)), (l2 + 0.22, (0.05, -0.8)),
                            (w_here - 0.2, (0.05, -0.8)), (w_here + 0.1, (0.65, 0.45)),
                            (l2e + 1.0, (0.65, 0.45))], hx=0.2, hy=0.12)
    land = math.exp(-max(0.0, t - t_land) * 7) * math.sin(max(0.0, t - t_land) * 18) \
        if t > t_land else 0.0
    knock = smoothstep(seg(t, l2 + 0.25, l2 + 0.45)) * (1 - smoothstep(seg(t, w_here - 0.25,
                                                                            w_here + 0.2)))
    face = {"head_turn": ht, "head_nod": hn - 0.12 * knock + 0.08 * land,
            "head_tilt": 0.06 * knock, "brow_ang": 0.45 * smoothstep(seg(t, l2, l2 + 0.3)),
            "frown": 0.2, "brow_in": 0.12, "lid": 0.05}
    expr = state_at(t, [(0, "bored"), (l2 + 0.25, "sad"), (l2e + 0.02, "sigh"),
                        (l2e + 0.55, "sad")], 0.25)
    blink = None
    w_never = wt(info, "s13_l02", 1)
    if w_never - 0.1 < t < w_never + 0.9:
        blink = slow_blink(t, w_never, 0.3, 0.12, 0.35)
    # creature: stops, looks back at him, plops down to sit
    sit_t = l2 + 0.55
    face_c = lerp(1.0, -1.0, smoothstep(seg(t, c_stop - 0.1, c_stop + 0.2)))
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=v)
        tired(ctx, xt, FEET, SP, t, info, pose=pose, pose_t=xt / STRIDE_T, turn=turn,
              expr=expr, look=look, face=face, blink=blink)
        if t < sit_t:
            CR.draw_specimen(ctx, xc, FEET + 8, SC, t, pose="walk", pose_t=xc / STRIDE_C,
                             expr="calm", look=(-0.5, -0.6) if face_c < 0 else (0.6, -0.1),
                             face=face_c)
        else:
            creature(ctx, xc, FEET + 8, SC, t, sq=squash_at(t, sit_t, 0.14, 0.25), pose="sit",
                     expr="curious", look=(-0.6, -0.45), face=-1.0)


# ============================================================================
# SH3  point
# ============================================================================
def _slumped_tired(ctx, t, T, info, look, face, expr="sad", blink=None, extra_pose=None,
                   dx=0.0, turn=SIT_TURN):
    pose = SIT if extra_pose is None else extra_pose
    return tired(ctx, WALL_X + dx, FEET, SP, t, info, pose=pose, turn=turn, expr=expr,
                 look=look, face=face, blink=blink)


def sh3(ctx, t, T, info):
    v = 2
    tp = T["point"]
    z = 2.1
    camx, camy = 985, sewer_cam_y(z, 1290)
    # creature: looks to the tunnel, raises paw, looks back at him
    face_c = tween(t, [(tp - 0.05, -1.0), (tp + 0.12, 1.0), (tp + 0.36, 1.0), (tp + 0.52, -1.0)])
    pa = 0.9 + (-0.12 - 0.9) * ease_out_back(seg(t, tp + 0.1, tp + 0.36), 1.6)
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=v)
        _slumped_tired(ctx, t, T, info, look=(0.75, 0.25), face={"head_turn": 0.12,
                       "brow_ang": 0.4, "frown": 0.2})
        if t < tp + 0.1:
            CR.draw_specimen(ctx, CX_SEW, FEET + 8, SC, t, pose="sit", expr="curious",
                             look=(-0.5, -0.7) if face_c < 0 else (0.7, 0.0), face=face_c)
        else:
            ca = CR.draw_specimen(ctx, CX_SEW, FEET + 8, SC, t, pose="point", expr="curious",
                                  look=(-0.55, -0.6) if face_c < 0 else (0.8, 0.1), face=face_c,
                                  point_angle=pa)
            hx, hy = ca["head"]
            fx.emote(ctx, "exclaim", hx + 10, hy - 120 * SC, 0.42, t, tp + 0.2, dur=0.55)


# ============================================================================
# SH4  l03 (MCU, deadpan)
# ============================================================================
def sh4(ctx, t, T, info):
    v = 2
    l3, l3e = T["l3"], T["l3e"]
    z = 2.7
    camx, camy = WALL_X + 40, FEET - 335
    w_not = wt(info, "s13_l03", 1)
    w_out = wt(info, "s13_l03", 4)
    look, ht, hn = gaze(t, [(l3 - 0.1, (0.6, 0.5)), (w_not - 0.05, (0.6, 0.5)),
                            (w_not + 0.12, (1.0, 0.05)), (w_out - 0.12, (1.0, 0.05)),
                            (w_out + 0.06, (0.6, 0.5))], hx=0.12, hy=0.1)
    brow = 0.26 * smoothstep(seg(t, w_not + 0.15, w_not + 0.45))
    press = 0.45 * smoothstep(seg(t, l3e, l3e + 0.25))
    face = {"head_turn": ht + 0.1, "head_nod": hn, "brow_r": brow, "brow_ang": 0.12,
            "press": press, "lid": 0.04}
    blink = None
    if t > l3e - 0.05:
        blink = slow_blink(t, l3e + 0.02, 0.3, 0.12, 0.35)
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=v)
        _slumped_tired(ctx, t, T, info, look=look, face=face, expr="deadpan", blink=blink)


# ============================================================================
# SH5  roll (CU creature)
# ============================================================================
def sh5(ctx, t, T, info):
    v = 2
    tr = T["roll"]
    z = 3.0
    hx = CX_SEW + 30
    camx, camy = hx + 20, FEET - 170
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=v)
        _slumped_tired(ctx, t, T, info, look=(0.6, 0.5), face={"brow_ang": 0.12, "press": 0.4},
                       expr="deadpan")
        CR.draw_specimen(ctx, CX_SEW, FEET + 8, SC, t, pose="sit", expr="eyeroll",
                         pose_t=t - tr, face=-1.0, look=(-0.4, -0.5))


# ============================================================================
# SH6  annoy + l04 (two-shot)
# ============================================================================
def _annoy_beats(T):
    a0 = T["sh6"]
    b = T["l4"]
    span = b - a0
    # chitter, tug, headbutt, poke, plead (fractions of the span before "Fine.")
    fr = (0.0, 0.15, 0.41, 0.555, 0.665)
    return [a0 + f * span for f in fr] + [b]


def sh6(ctx, t, T, info):
    v = 2
    c0, c1, c2, c3, c4, _ = _annoy_beats(T)
    l4 = T["l4"]
    push = _push_t(T)                    # he gets up off the floor
    z = lerp(1.6, 1.72, ease_in_out(seg(t, c0, l4)))
    camx, camy = WALL_X + 140, sewer_cam_y(z, 1420)
    # ---------------- Tiredness
    pull = 0.0
    if c1 + 0.1 <= t < c2:
        yank = 0.5 + 0.5 * math.sin(TAU * 2.0 * t)
        pull = smoothstep(seg(t, c1 + 0.1, c1 + 0.22)) * (0.55 + 0.45 * yank)
    jolt = 0.0
    if c2 + 0.16 <= t < c3 + 0.4:
        u = t - (c2 + 0.16)
        jolt = math.exp(-u * 8) * math.cos(u * 22)
    crumble = smoothstep(seg(t, c4 + 0.1, l4 + 0.05))
    pose = dict(SIT)
    pose["dx"] = 10 * pull - 8 * jolt
    pose["side"] = 0.08 * pull
    pose["rot"] = -0.025 * jolt
    pose["hunch"] = SIT["hunch"] + 0.15 * crumble
    pose["lean"] = SIT["lean"] - 0.06 * crumble
    arm_k = smoothstep(seg(t, c1 + 0.06, c1 + 0.2)) * (1 - smoothstep(seg(t, c2 - 0.05, c2 + 0.1)))
    if arm_k > 0:
        pose.update({"ar_ik": arm_k, "ar_tx": 0.3 + 0.05 * pull, "ar_ty": 0.11, "ar_tz": 0.18,
                     "ar_h": "relaxed", "ar_wa": 0.2, "ar_wabs": 0.5 * arm_k})
    k_up = seg(t, push, push + 0.5)
    if k_up > 0:
        ant = math.sin(clamp(k_up / 0.5) * math.pi) * 0.25
        up = {"base": "slouch", "lean": 0.1 + ant}
        pose = (pose, up, ease_in_out(k_up))
    t_walk = push + 0.45
    xt = x_sh6(t, T)
    if t > t_walk:
        pose = (pose, TRUDGE, smoothstep(seg(t, t_walk, t_walk + 0.25)))
    turn = lerp(SIT_TURN, TURN_W, smoothstep(seg(t, push + 0.25, push + 0.6)))
    # gaze: the creature's face / the hem / the shin / the poke; then lids drop
    cface = (0.7, 0.45)
    look, ht, hn = gaze(t, [(c0, cface), (c1 + 0.08, cface), (c1 + 0.2, (0.55, 0.9)),
                            (c2, (0.55, 0.9)), (c2 + 0.14, (0.4, 1.0)), (c3 - 0.02, (0.4, 1.0)),
                            (c3 + 0.08, (0.55, 0.85)), (c4 - 0.02, (0.55, 0.85)),
                            (c4 + 0.1, cface), (push + 0.1, cface), (push + 0.45, (0.4, 0.05))],
                        hx=0.2, hy=0.14)
    face = {"head_turn": ht, "head_nod": hn + 0.08 * crumble, "lid": 0.14 * crumble,
            "brow_r": 0.22 * smoothstep(seg(t, c0 + 0.1, c0 + 0.3)) * (1 - crumble),
            "press": 0.35 * (1 - crumble), "brow_ang": 0.28 * crumble,
            "lid_r": 0.0}
    expr = state_at(t, [(0, "unamused"), (c4 + 0.14, "sigh"), (l4 - 0.05, "deadpan"),
                        (push + 0.3, "bored")], 0.28)
    blink = None
    if c2 + 0.18 < t < c2 + 0.75:
        blink = tween(t, [(c2 + 0.18, 0.0), (c2 + 0.24, 1.0), (c2 + 0.4, 1.0), (c2 + 0.6, 0.0)])
    elif l4 - 0.02 < t < push + 0.2:
        blink = slow_blink(t, l4 + 0.02, 0.3, 0.12, 0.25)
    # ---------------- draw
    with core.camera(ctx, camx, camy, z):
        sets.sewer(ctx, t, variant=v)
        a = tired(ctx, xt, FEET, SP, t, info, pose=pose, turn=turn, expr=expr, look=look,
                  face=face, blink=blink, pose_t=xt / STRIDE_T)
        foot = a["foot_r"]
        cx = CX_SEW + 70
        if t < c1:
            # chitter: stands facing him, head bobbing, little vocal ticks
            tl_ = 0.07 * math.sin(TAU * 7.0 * (t - c0)) * (1 - seg(t, c1 - 0.08, c1))
            ca = creature(ctx, cx, FEET + 8, SC, t, sq=squash_at(t, c0, 0.1, 0.2), pose="stand",
                          flip=True, expr="annoyed", look=(-0.75, -0.6), tilt=tl_ - 0.22)
            mx, my = ca["mouth"]
            fx.tap_marks(ctx, mx - 16, my - 18, 0.75, t, c0 + 0.03, taps=3, gap=0.11,
                         angle=-math.pi * 0.72, label=None, color="#e8fffb")
        elif t < c2:
            # bites his hoodie cuff and tugs him toward the tunnel
            lunge = ease_out_back(seg(t, c1, c1 + 0.12))
            wx, wy = a["wrist_r"]
            off = spec_offsets(SC, t, pose="tug", flip=True)["mouth"]
            bite_x = wx + 8 * SP - off[0]
            gx = lerp(cx, bite_x, lunge)

            def cuff(c, aa, wrist=(wx, wy)):
                mx_, my_ = aa["mouth"]
                k = SP
                # the stretched sleeve from his wrist into the jaws
                c.move_to(wrist[0] - 10 * k, wrist[1] - 22 * k)
                c.curve_to(wrist[0] + 20 * k, wrist[1] - 24 * k, mx_ - 16 * k, my_ - 16 * k,
                           mx_ + 6 * k, my_ - 10 * k)
                c.line_to(mx_ + 6 * k, my_ + 10 * k)
                c.curve_to(mx_ - 16 * k, my_ + 16 * k, wrist[0] + 20 * k, wrist[1] + 24 * k,
                           wrist[0] - 10 * k, wrist[1] + 22 * k)
                c.close_path()
                core.fill_stroke(c, core.PAL["t_hoodie"], core.PAL["ink"], 4.5 * k)
                for j in (-1, 1):
                    c.move_to(wrist[0] + 2 * k, wrist[1] + 9 * j * k)
                    c.line_to(mx_ - 4 * k, my_ + 5 * j * k)
                core.stroke(c, core.PAL["t_hoodie_dk"], 3.0 * k)
            creature(ctx, gx, FEET + 8, SC, t, pose="tug", flip=True, expr="annoyed",
                     look=(-0.4, -0.6), hold=cuff if lunge > 0.55 else None)
        elif t < c3:
            # headbutts his shin
            k = seg(t, c2, c3)
            back = math.sin(clamp(k / 0.3) * math.pi * 0.5) if k < 0.3 else 1.0
            ram = ease_in(seg(t, c2 + 0.08, c2 + 0.16)) * (1 - ease_out(seg(t, c2 + 0.22, c3)))
            shin_x = foot[0] + 14
            gx = shin_x + 150 * 0.92 * SC + 46 + 26 * back - 60 * ram
            creature(ctx, gx, FEET + 8, SC, t, sq=squash_at(t, c2, 0.1, 0.18), pose="stand",
                     flip=True, expr="annoyed", look=(-0.5, 0.1), tilt=0.32 * ram + 0.06 * back)
            if t >= c2 + 0.16:
                fx.impact_star(ctx, shin_x + 26, FEET - 120 * SP, 0.4, t, c2 + 0.16, dur=0.3,
                               spikes=9)
        elif t < c4:
            # poke poke
            k = t - c3
            jab = max(0.0, math.sin(TAU * 5.5 * k)) * (1 if k < 0.36 else 0)
            gx = foot[0] + 236 * SC - 22 * jab
            ca = creature(ctx, gx, FEET + 8, SC, t, sq=squash_at(t, c3, 0.1, 0.15), pose="point",
                          flip=True, expr="annoyed", look=(-0.6, -0.5), face=1.0,
                          point_angle=-0.3 + 0.1 * jab)
            px, py = ca.get("paw", (gx - 150 * SC, FEET - 150 * SC))
            fx.tap_marks(ctx, px - 6, py, 0.6, t, c3 + 0.045, taps=2, gap=0.18,
                         angle=math.pi * 0.95, label=None)
        elif t < push + 0.3:
            # puppy eyes; then joy at "Fine."
            gx = foot[0] + 226 * SC
            t_joy = l4 + 0.3
            joy = t >= t_joy
            sq = squash_at(t, c4, 0.1, 0.2) if not joy else squash_at(t, t_joy, 0.16, 0.3)
            hop = 0.0
            if joy:
                hop = 46 * SP * math.sin(clamp((t - t_joy) / 0.34) * math.pi)
            creature(ctx, gx, FEET + 8 - hop, SC, t, sq=sq, pose="sit", flip=True,
                     expr="content" if joy else "pleading", look=(-0.6, -0.7), face=1.0)
        else:
            # spins round and trots off toward the tunnel
            u = t - (push + 0.3)
            gx = foot[0] + 226 * SC + V_T * 1.4 * u
            creature(ctx, gx, FEET + 8, SC, t, sq=squash_at(t, push + 0.3, 0.12, 0.2),
                     pose="walk", pose_t=gx / STRIDE_C, expr="calm", look=(0.7, -0.2))


# ============================================================================
# SH7  enter (inside the side tunnel)
# ============================================================================
ST_FLOOR = 1282
ST_OPEN_X = 1010
ST_X0, ST_X1, ST_Y0, ST_Y1 = -200, 1700, -100, 2100


def _st_static(c):
    ink = core.PAL["ink"]
    c.rectangle(ST_X0, ST_Y0, ST_X1 - ST_X0, ST_Y1 - ST_Y0)
    core.fill(c, "#0c201f")
    # brick back wall (dim teal), getting lighter toward the opening
    bh, bw = 54, 124
    row = 0
    y = 330
    while y < ST_FLOOR:
        off = (bw / 2) if row % 2 else 0
        x = ST_X0 - off
        i = 0
        while x < ST_OPEN_X:
            v = core.hash01(i * 7 + row * 131, 77)
            near = clamp((x - 300) / (ST_OPEN_X - 300))
            col = core.mixc("#163633" if v > 0.25 else "#112b28", "#2a6f68", 0.55 * near * near)
            c.rectangle(x + 5, y + 5, bw - 10, bh - 10)
            core.fill(c, col)
            x += bw
            i += 1
        y += bh
        row += 1
    # low vault
    c.move_to(ST_X0, 330)
    c.line_to(ST_OPEN_X, 330)
    c.line_to(ST_OPEN_X, ST_Y0)
    c.line_to(ST_X0, ST_Y0)
    c.close_path()
    core.fill(c, "#0a1a19")
    for k in range(6):
        yy = 330 - k * 46
        c.move_to(ST_X0, yy)
        c.line_to(ST_OPEN_X, yy)
    core.stroke(c, "#14302d", 4)
    core.poly(c, [(ST_X0, 318), (ST_OPEN_X, 318), (ST_OPEN_X, 340), (ST_X0, 340)])
    core.fill_stroke(c, "#1d4440", ink, 5)
    for px in (40, 470):
        core.rrect(c, px - 40, 340, 80, ST_FLOOR - 340, 6)
        core.fill_stroke(c, "#132f2c", ink, 5)
    # pipe along the wall
    c.rectangle(ST_X0, 452, ST_OPEN_X - ST_X0, 44)
    core.fill_stroke(c, "#2a4c45", ink, 5)
    for px in range(ST_X0 + 80, ST_OPEN_X, 260):
        core.rrect(c, px - 12, 444, 24, 60, 4)
        core.fill_stroke(c, "#20403a", ink, 4)
    # floor walkway + a thin wet channel
    c.rectangle(ST_X0, ST_FLOOR, ST_X1 - ST_X0, 64)
    core.fill_stroke(c, "#24453f", ink, 5)
    c.rectangle(ST_X0, ST_FLOOR + 64, ST_X1 - ST_X0, ST_Y1 - ST_FLOOR)
    core.fill(c, "#0e2624")
    for k in range(6):
        wx = 60 + k * 230 + 60 * core.hash01(k, 3)
        c.move_to(wx, ST_FLOOR + 130 + 70 * core.hash01(k, 4))
        c.rel_line_to(110, 0)
    core.stroke(c, (0.4, 0.8, 0.75, 0.25), 5)
    # the opening at the end: blazing teal (the shaft beyond)
    ox = ST_OPEN_X
    c.move_to(ox, ST_FLOOR + 64)
    c.line_to(ox, 560)
    c.curve_to(ox + 60, 420, ox + 380, 400, ST_X1, 400)
    c.line_to(ST_X1, ST_FLOOR + 64)
    c.close_path()
    core.fill(c, "#8ff9ef")
    # far pods as glowing capsules in the light
    for k, (px, py) in enumerate(((1130, 640), (1250, 820), (1150, 1010), (1300, 590),
                                  (1290, 1050))):
        core.rrect(c, px - 34, py - 60, 68, 120, 34)
        core.fill(c, (0.25, 0.85, 0.8, 0.55))
    core.radial_glow(c, ox + 160, 880, 560, "#ffffff", 0.6)
    # jamb (arch edge)
    c.move_to(ox - 40, ST_FLOOR + 64)
    c.line_to(ox - 40, 560)
    c.curve_to(ox + 20, 380, ox + 380, 356, ST_X1, 356)
    c.line_to(ST_X1, 400)
    c.curve_to(ox + 380, 400, ox + 60, 420, ox, 560)
    c.line_to(ox, ST_FLOOR + 64)
    c.close_path()
    core.fill_stroke(c, "#163a36", ink, 6)


def _st_glow(c):
    ox = ST_OPEN_X
    core.radial_glow(c, ox + 40, 860, 820, core.PAL["power"], 0.5)
    core.ellipse(c, ox - 220, ST_FLOOR + 30, 560, 40)
    core.fill(c, core.alpha(core.PAL["power"], 0.3))


def sh7(ctx, t, T, info):
    t0, t1 = T["enter"], T["sh8"]
    k = seg(t, t0, t1)
    z = lerp(1.25, 1.3, k)
    xt = x_sh7(t, T)
    xc = xt + 270
    camx = 800 + 30 * k
    camy = ST_FLOOR - (1300 - 960) / z
    glow = 0.35 + 0.65 * ease_in(k)

    def figs(c):
        tired(c, xt, ST_FLOOR, SP, t, info, pose=TRUDGE, pose_t=xt / STRIDE_T,
              turn=TURN_W, expr="bored", look=(0.6, -0.1), face={"lid": -0.04})
        CR.draw_specimen(c, xc, ST_FLOOR + 8, SC, t, pose="walk", pose_t=xc / STRIDE_C,
                         expr="calm", look=(0.8, -0.1))

    with core.camera(ctx, camx, camy, z):
        sets.static_layer(ctx, ("s13_sidetunnel", 2), ST_X0, ST_Y0, ST_X1 - ST_X0, ST_Y1 - ST_Y0,
                          _st_static)
        ctx.push_group()
        _st_glow(ctx)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(glow)
        lit_group(ctx, figs, sil=0.8 - 0.1 * k, rim=core.PAL["power"], rim_dx=8)
    # the light swells toward the cut
    wash = smoothstep(seg(t, t1 - 0.3, t1))
    if wash > 0:
        ctx.rectangle(0, 0, core.W, core.H)
        core.fill(ctx, core.alpha("#9ffcf2", 0.4 * wash))


# ============================================================================
# shaft helpers
# ============================================================================
KC_SH = 1.1             # creature a touch closer to camera on the catwalk


def _sleeper(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s, t, seed=seed)


def shaft_bg(ctx, t):
    sets.shaft(ctx, t, sleeper_fn=_sleeper, sleeper_key="spec13")


def _shaft_people(ctx, t, T, info, xt, xc, tired_kw, crea_kw, sil=0.0, s=SH_S, crea_first=False):
    def figs(c):
        if crea_first:
            CR.draw_specimen(c, xc, SH_FEET + 3, s * KC_SH, t, **crea_kw)
        tired(c, xt, SH_FEET, s, t, info, **tired_kw)
        if not crea_first:
            CR.draw_specimen(c, xc, SH_FEET + 3, s * KC_SH, t, **crea_kw)
    if sil > 0:
        lit_group(ctx, figs, sil=sil, rim=core.PAL["power"], rim_dx=-3.0, rim_dy=3.0)
    else:
        figs(ctx)


def _pull_cam(t, ta, tb, c0, c1, ease=ease_in_out):
    """Zoom out from c0=(x,y,z) to c1 with a stable focal feel."""
    e = ease(seg(t, ta, tb))
    z0, z1 = c0[2], c1[2]
    z = math.exp(lerp(math.log(z0), math.log(z1), e))
    f = (1 / z - 1 / z0) / (1 / z1 - 1 / z0) if z1 != z0 else e
    return (lerp(c0[0], c1[0], f), lerp(c0[1], c1[1], f), z)


SIDE_C = 220            # creature offset beside him (in units of his s)
LEAN_C = 134            # ...when it leans against his leg


# ============================================================================
# SH8  arrive + reveal pull-out
# ============================================================================
def sh8(ctx, t, T, info):
    t0, tr, tw = T["sh8"], T["reveal"], T["wide"]
    cam0 = (SH_TX + 34, SH_FEET - 96, 2.8)
    cam1 = (400, 1900, 0.56)
    cx, cy, z = _pull_cam(t, tr, min(tr + 1.55, tw - 0.3), cam0, cam1)
    # Tiredness steps out of the tunnel mouth, stops, looks up
    walk_v = SH_WALK_V
    t_stop = min(t0 + 0.62, tr - 0.2)
    xt = x_sh8(t, T)
    wk = 1 - smoothstep(seg(t, t_stop - 0.38, t_stop))
    pose = ("walk", "stand", 1 - wk)
    look_up = smoothstep(seg(t, t_stop - 0.05, t_stop + 0.3))
    blink = 0.0 if t_stop - 0.3 < t < tr + 0.6 else None
    look = (lerp(0.55, 0.3, look_up), lerp(0.25, -0.85, look_up))
    # a small surprise only (+~10%): protect the full-open payoff for the close-up
    face = {"head_nod": -0.14 * look_up, "head_turn": 0.1 * look_up, "pupil": 0.2 * look_up,
            "lid": 0.12 * look_up, "brow": 0.25 * look_up, "open": 0.1 * look_up,
            "press": -0.1 * look_up, "curve": 0.08 * look_up}
    # the creature trots out ahead and sits beside him, gazing up at the pods
    c_stop = t0 + 0.4
    xc_stop = SH_TX + SIDE_C * SH_S
    xc = decel(t, c_stop, xc_stop, walk_v * 1.2, 0.3)
    sit_t = c_stop + 0.06
    with core.cache_steps(1):
        with core.camera(ctx, cx, cy, z):
            shaft_bg(ctx, t)
            tkw = dict(pose=pose, pose_t=xt / walk_v, turn=lerp(TURN_W, 0.5, look_up),
                       expr="bored",
                       look=look, face=face, blink=blink)
            if t < sit_t:
                ckw = dict(pose="walk", pose_t=xc / (CR.SPEC_WALK_SPEED * SH_S * KC_SH),
                           expr="calm", look=(0.6, -0.4))
            else:
                ckw = dict(pose="sit", expr="wide", look=(0.2, -1.0), face=1.0,
                           tilt=-0.15)
            _shaft_people(ctx, t, T, info, xt, xc, tkw, ckw,
                          sil=0.3 * smoothstep(seg(t, tr, tr + 1.2)))
            sets.shaft(ctx, t, layer="fg")


# ============================================================================
# SH9  wide: CU, lids open fully
# ============================================================================
def _cast_grad(x, y, r, a=1.0):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    pw = core.hexc(core.PAL["power"])
    g.add_color_stop_rgba(0, pw[0], pw[1], pw[2], a)
    g.add_color_stop_rgba(1, pw[0], pw[1], pw[2], 0.0)
    return g


def sh9(ctx, t, T, info):
    tw, ts = T["wide"], T["sad"]
    k = seg(t, tw, ts)
    with core.camera(ctx, 610, 1150 - 60 * ease_in_out(k), 1.45 + 0.06 * k):
        shaft_bg(ctx, t)
    fx.vignette(ctx, 0.42)
    # the payoff: pupils widen first, then the lids roll all the way open; hold
    t_open = tw + 0.3
    open_k = ease_in_out(seg(t, t_open, t_open + 0.7))
    pup = smoothstep(seg(t, tw + 0.08, tw + 0.32))
    breath = smoothstep(seg(t, t_open + 0.2, t_open + 0.8))
    face = {"pupil": 0.25 * pup + 0.1 * open_k, "lid": 0.1 * (1 - open_k) - 0.14 * open_k,
            "brow": 0.18 * open_k, "head_nod": -0.12 - 0.05 * open_k, "head_turn": 0.12,
            "hl": 0.35 * open_k, "open": 0.07 * open_k}
    expr = ("bored", "awe", open_k)
    look = (0.3, -0.6)
    blink = 0.0 if tw + 0.2 < t < ts - 0.15 else None
    s = 2.55
    x, y = 470, 680 + 800 * s
    push = 1.0 + 0.035 * k
    pose = {"base": "stand", "hunch": 0.25 * breath, "breath": 0.3}
    eyes = {}

    def fig(c):
        with core.saved(c, 540, 960, push):
            c.translate(-540, -960)
            a = tired(c, x, y, s, t, info, pose=pose, turn=0.42, expr=expr, look=look, face=face,
                      blink=blink, power=0.24 * open_k, shadow=False)
            eyes["l"], eyes["r"] = a["eye_l"], a["eye_r"]
    lit_group(ctx, fig, cast=(_cast_grad(820, 330, 760, 0.55), 0.42))
    for j, side in enumerate(("l", "r")):
        ex, ey = eyes[side]
        ex = 540 + (ex - 540) * push
        ey = 960 + (ey - 960) * push
        fx.eye_glint(ctx, ex + 12, ey - 14, 0.55, t, t_open + 0.62 + 0.05 * j, dur=0.42)


# ============================================================================
# SH10 / SH11 / SH12  catwalk two-shots (screen space over the framed shaft)
# ============================================================================
def _railing(ctx, y_deck, rail_y):
    ink = core.PAL["ink"]
    for k in range(-1, 14):
        px = k * 92 + 20
        ctx.move_to(px, y_deck)
        ctx.line_to(px, rail_y)
    core.stroke(ctx, "#4d6f7c", 9)
    ctx.move_to(-20, rail_y)
    ctx.line_to(1100, rail_y)
    core.stroke(ctx, ink, 22)
    ctx.move_to(-20, rail_y)
    ctx.line_to(1100, rail_y)
    core.stroke(ctx, "#7fa0ac", 13)
    ctx.move_to(-20, (rail_y + y_deck) / 2)
    ctx.line_to(1100, (rail_y + y_deck) / 2)
    core.stroke(ctx, "#4d6f7c", 8)


def _deck(ctx, y_deck):
    ctx.rectangle(-20, y_deck, 1120, core.H - y_deck + 20)
    core.fill(ctx, "#24404c")
    ctx.rectangle(-20, y_deck, 1120, 34)
    core.fill_stroke(ctx, "#3b5a66", core.PAL["ink"], 6)
    for k in range(0, 30):
        ctx.move_to(k * 50 - 20, y_deck + 40)
        ctx.line_to(k * 50, y_deck + 80)
    core.stroke(ctx, "#33505c", 5)


TWO_S = 1.3             # Tiredness scale in the catwalk two-shots
TWO_FEET = 1545
TWO_TX = 330


def two_shot(ctx, t, T, info, cam, tkw, ckw, push=1.0, lean=0.0):
    with core.camera(ctx, *cam):
        shaft_bg(ctx, t)
    fx.vignette(ctx, 0.32)
    cx = TWO_TX + lerp(SIDE_C, LEAN_C, lean) * TWO_S

    def figs(c):
        with core.saved(c, 540, 1100, push):
            c.translate(-540, -1100)
            _railing(c, TWO_FEET + 20, TWO_FEET - 510)
            _deck(c, TWO_FEET + 20)
            # the creature sits a step nearer camera, behind his near leg once it leans in
            CR.draw_specimen(c, cx, TWO_FEET + 14, TWO_S * KC_SH, t, **ckw)
            tired(c, TWO_TX, TWO_FEET, TWO_S, t, info, **tkw)
    lit_group(ctx, figs, cast=(_cast_grad(840, 480, 1000, 0.6), 0.3))


def sh10(ctx, t, T, info):
    ts, l5 = T["sad"], T["l5"]
    k = seg(t, ts, l5)
    # he lowers his gaze to the creature: pupils first, then the head
    look, ht, hn = gaze(t, [(ts, (0.3, -0.6)), (ts + 0.3, (0.3, -0.6)), (ts + 0.5, (0.8, 0.7))],
                        lag=0.18, hx=0.25, hy=0.22)
    sad_k = smoothstep(seg(t, ts + 0.4, ts + 0.9))
    face = {"head_turn": ht, "head_nod": hn, "lid": -0.06 * (1 - sad_k), "brow_in": 0.22 * sad_k,
            "brow_ang": 0.3 * sad_k, "brow": 0.1 * sad_k, "frown": 0.2 * sad_k,
            "pupil": 0.15, "hl": 0.3 * sad_k}
    expr = ("awe", "sad", sad_k)
    tkw = dict(pose="stand", turn=0.45, expr=expr, look=look, face=face,
               power=0.14 * (1 - sad_k), lidcap=0.56)
    # it gazes up at the pods; ears sink
    ckw = dict(pose="sit", expr="sad", look=(0.3, -1.3), face=1.0,
               tilt=lerp(-0.2, -0.12, smoothstep(seg(t, ts + 0.3, l5))))
    two_shot(ctx, t, T, info, (420, 2120, 1.22), tkw, ckw, push=1.0 + 0.025 * k)


def sh11(ctx, t, T, info):
    l5, l5e, tn = T["l5"], T["l5e"], T["nod"]
    k = seg(t, l5, tn)
    with core.camera(ctx, 840, 2490 - 30 * k, 1.75):
        shaft_bg(ctx, t)
    fx.vignette(ctx, 0.36)
    w_fam = wt(info, "s13_l05", 3)
    look, ht, hn = gaze(t, [(l5, (0.75, 0.8)), (w_fam - 0.2, (0.75, 0.8)),
                            (w_fam + 0.05, (0.55, 0.62)), (l5e + 0.4, (0.55, 0.62))],
                        hx=0.15, hy=0.12)
    face = {"head_turn": ht + 0.1, "head_nod": hn + 0.12, "brow_in": 0.25, "brow_ang": 0.38,
            "brow": 0.12, "frown": 0.18, "lid": -0.02, "hl": 0.35, "pupil": 0.14}
    blink = None
    if t > l5e - 0.1:
        blink = slow_blink(t, l5e, 0.35, 0.15, 0.4)
    s = 2.1

    def fig(c):
        with core.saved(c, 540, 960, 1.0 + 0.03 * k):
            c.translate(-540, -960)
            tired(c, 470, 680 + 800 * s, s, t, info, pose="stand", turn=0.5, expr="sad",
                  look=look, face=face, blink=blink, shadow=False, lidcap=0.56)
    lit_group(ctx, fig, cast=(_cast_grad(840, 380, 800, 0.55), 0.34))


def _hand_on_head(k):
    """Pose dict: his right hand comes down to rest on the creature's head."""
    return {"base": "stand", "lean": 0.35 * k, "side": 0.12 * k, "nod": 0.06 * k,
            "ar_ik": k, "ar_tx": 0.12, "ar_ty": 0.27, "ar_tz": 0.3, "ar_h": "relaxed",
            "ar_wa": 0.3, "ar_wabs": 0.4 * k}


def _nod_state(t, T):
    tn = T["nod"]
    face_c = tween(t, [(tn, 1.0), (tn + 0.12, 1.0), (tn + 0.34, -1.0)])
    nod = 0.0
    if t > tn + 0.42:
        u = seg(t, tn + 0.42, tn + 0.85)
        nod = 0.3 * math.sin(u * math.pi)
    lean = ease_in_out(seg(t, tn + 0.7, tn + 1.1))
    hand = ease_in_out(seg(t, tn + 0.8, tn + 1.25))
    return face_c, nod, lean, hand


def sh12(ctx, t, T, info):
    tn, tt = T["nod"], T["title"]
    k = seg(t, tn, tt)
    face_c, nod, lean, hand = _nod_state(t, T)
    look_c = (-0.6, -0.75) if face_c < 0 else (0.3, -1.0)
    content = t > tn + 1.15
    ckw = dict(pose="sit", expr="content" if content else "sad", look=look_c, face=face_c,
               tilt=nod - 0.08 * lean)
    look, ht, hn = gaze(t, [(tn, (0.8, 0.7)), (tn + 1.4, (0.75, 0.8))], hx=0.25, hy=0.2)
    face = {"head_turn": ht, "head_nod": hn + 0.05, "brow_in": 0.22, "brow_ang": 0.3 - 0.1 * hand,
            "brow": 0.1, "pupil": 0.12, "curve": 0.12 * hand, "frown": 0.15 * (1 - hand)}
    tkw = dict(pose=_hand_on_head(hand), turn=0.45, expr="sad", look=look, face=face,
               lidcap=0.56 + 0.06 * hand)
    two_shot(ctx, t, T, info, (420, 2120, 1.22), tkw, ckw, push=1.025 + 0.03 * k, lean=lean)


# ============================================================================
# SH13  title: pull back to the wide silhouette + end card
# ============================================================================
def sh13(ctx, t, T, info):
    tt = T["title"]
    cam0 = (SH_TX + 60, SH_FEET - 120, 2.7)
    cam1 = (SH_TX + 30, SH_FEET - 240, 1.55)
    cx, cy, z = _pull_cam(t, tt, tt + 2.3, cam0, cam1)
    sil = lerp(0.82, 0.9, smoothstep(seg(t, tt + 0.1, tt + 1.4)))
    tkw = dict(pose=_hand_on_head(1.0), turn=0.45, expr="sad", look=(0.75, 0.8),
               face={"brow_in": 0.18, "head_nod": 0.1, "head_turn": 0.15, "curve": 0.1})
    ckw = dict(pose="sit", expr="content", look=(-0.5, -0.8), face=-1.0, tilt=-0.08)
    with core.cache_steps(1):
        with core.camera(ctx, cx, cy, z):
            shaft_bg(ctx, t)
            # soft backlight haze behind the pair so the silhouettes read
            core.radial_glow(ctx, SH_TX + 30, SH_FEET - 110, 330, "#c8fff8", 0.34 * sil)
            _shaft_people(ctx, t, T, info, SH_TX, SH_TX + LEAN_C * SH_S, tkw, ckw, sil=sil,
                          crea_first=True)
            sets.shaft(ctx, t, layer="fg")
    fx.end_card(ctx, t, tt + 0.55)


# ============================================================================
# dispatch
# ============================================================================
def _shots(T):
    return [(0.0, sh1), (T["tunnels"], sh2a), (T["sh2b"], sh2b), (T["point"], sh3),
            (T["l3"], sh4), (T["roll"], sh5), (T["sh6"], sh6), (T["enter"], sh7),
            (T["sh8"], sh8), (T["wide"], sh9), (T["sad"], sh10), (T["l5"], sh11),
            (T["nod"], sh12), (T["title"], sh13)]


def render(ctx, t, info):
    T = _times(info)
    fn = sh1
    for t0, f in _shots(T):
        if t >= t0:
            fn = f
    core.bg(ctx, "#0b1f1d")
    fn(ctx, t, T, info)


def caption_y(t, info):
    if t >= info.cue("title") - 0.05:
        return None
    return 1450


# ============================================================================
# sound
# ============================================================================
def _steps(xfn, T, stride, t0, t1, name, gain, pan=0.0, dt=1 / 96):
    """Foot contacts = where the cycle phase (x / stride) crosses a half cycle."""
    ev = []
    prev = xfn(t0, T) / stride
    t = t0 + dt
    while t < t1:
        cur = xfn(t, T) / stride
        if math.floor(cur * 2) != math.floor(prev * 2) and cur > prev:
            ev.append((round(t, 3), name, gain, pan))
        prev = cur
        t += dt
    return ev


def SFX(info):
    T = _times(info)
    ev = []
    c0, c1, c2, c3, c4, _ = _annoy_beats(T)
    push = _push_t(T)
    # sewer room tone until we leave the main tunnel; the pods hum from the catwalk on
    ev += _sfx.loop_events("sewer_ambience", 0.0, T["enter"] + 0.6, -5)
    ev += _sfx.loop_events("pod_hum", T["enter"] + 0.2, T["reveal"], -18)
    ev += _sfx.loop_events("pod_hum", T["reveal"], T["end"], -8)
    # wet trudging steps exactly on his foot contacts
    ev += _steps(x_sh1, T, STRIDE_T, 0.0, T["tunnels"], "squish", -11, -0.1)
    ev += _steps(x_sh2a, T, STRIDE_T, T["tunnels"], T["sh2b"], "squish", -11, -0.1)
    ev += _steps(x_sh2b, T, STRIDE_T, T["sh2b"], T["l2"], "squish", -11, -0.1)
    ev += _steps(x_sh6, T, STRIDE_T, push + 0.45, T["enter"], "squish", -12, 0.0)
    ev += _steps(x_sh7, T, STRIDE_T, T["enter"], T["sh8"], "squish", -15, 0.0)
    ev += _steps(x_sh8, T, SH_WALK_V, T["sh8"], T["reveal"], "footstep", -12, -0.2)
    ev.append((1.7, "drip", -15, 0.4))
    ev.append((T["tunnels"] + 0.1, "drip", -17, -0.3))
    ev.append((T["sh2b"] + 0.15, "drip", -16, 0.3))
    # "Why me." -> sigh
    ev.append((T["l1e"] + 0.05, "sigh", -6))
    # slides down the wall
    ev.append((T["l2"] + 0.12, "cloth_rustle", -8, -0.1))
    ev.append((T["l2"] + 0.5, "body_thud", -15, -0.1))
    ev.append((T["l2e"] + 0.05, "sigh", -8))
    # the creature points: eager chirp
    ev.append((T["point"] + 0.12, "creature_chitter", -9, 0.2))
    # annoy escalation
    ev.append((c0 + 0.02, "creature_chitter", -3, 0.15))
    ev.append((c1 + 0.05, "cloth_rustle", -2, 0.1))
    ev.append((c2 + 0.16, "bonk", -13, 0.05))
    ev.append((c3 + 0.03, "tap_tap", 1, 0.05))
    ev.append((c4 + 0.12, "sigh", -4))
    ev.append((T["l4"] + 0.3, "creature_purr", 0, 0.2))
    ev.append((push + 0.05, "cloth_rustle", -10, 0.0))
    # the sad nod, the hand on its head
    ev.append((T["nod"] + 0.4, "creature_chirp_sad", 0, 0.15))
    ev.append((T["nod"] + 1.05, "cloth_rustle", -12, 0.0))
    ev.append((T["nod"] + 1.2, "creature_purr", -3, 0.1))
    return ev
