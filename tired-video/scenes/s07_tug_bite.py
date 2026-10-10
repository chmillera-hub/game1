"""s07 — Tug-of-war and the bite (music "chaos").

Bedroom, continuing s06 (Emb at the desk pressing the sweater lump, Tiredness
standing mid-room, headphones round his neck, chair empty, door open from the
s05 burst, laundry scattered / closet open from the s05 search).

Shot list (all times derive from cues; see _cues()):
  A  scoop        desk medium: Emb scoops the bundle into the cage, slaps the door shut
  B  latch        insert: the latch only half-catches and wiggles (l01 starts)
  C  back away    pan: Emb backs toward the door, cage in hand, small wave; Tiredness's
                  eyes track him; butt bumps the door, it clicks shut, he freezes; l02
  D  Tiredness    close: unamused, slow blink, one brow up a hair
  E  door/burst   door medium: he opens the door, Impulsivity is sitting RIGHT there;
                  its pupils snap together on the cage; it lunges and clamps the handle
  F  tug          wide: tug-of-war; Tiredness strolls in behind, arms crossed, unimpressed
  G  squint       close: he leans in over the cage and squints
  H  eyes         insert: two big shiny eyes look back out of the sweater
  I  creak/bite   close: latch slips, door creaks open, lids lift +10%; the thing
                  launches onto his forearm and chomps (2-frame freeze); delayed register
  J  scream       take: eyes squeezed SHUT, mouth huge, arm shaking, the thing drops off
  K  runout       wide: he scream-runs out, the door slams
  L  window       his window: he runs across the lawn outside (muffled)
  M  catch        Emb dives on the thing, stuffs it in the cage, latches it firmly;
                  Impulsivity has let go and sits
  N  stare        Emb and Impulsivity stare; his face slowly falls; push-in; l04 facepalm
"""
import math

import cairocffi as cairo

from engine import core, sets, props, fx, creatures, human
from engine.core import seg, tween, state_at, clamp, lerp, ease_out_back, ease_in_out, ease_out, ease_in
from engine.human import draw_person, cycle_speed, W as HW, A as HA, IK as HIK, HK as HHK
from audio import sfx

M = sets.BEDROOM_MARKS
S = 0.75                 # people in the bedroom
IMP_S = 1.0              # Impulsivity
CAGE_S = 0.62            # pet carrier
THING_S = 0.5            # the thing
FLOOR = M["stand_y"]     # 1520 feet line
TUG_Y = 1540
UP_Y = 1474              # upstage feet line (Tiredness behind the tug)
DESK_Y = M["desk_top_y"]
H_EMB = human.metrics("embar")["height"]
H_TIR = human.metrics("tired")["height"]
BR = dict(laundry_scattered=True, closet_open=1.0, chair_empty=True, chair_spin=1.1)
HP = "neck"              # Tiredness's headphones (round his neck since the s05 reveal)

CAGE_DESK = (2170.0, DESK_Y - 278 * CAGE_S)   # cage anchor (handle top) on the desk
IMP_X = 470.0
EMB_TUG_X = 935.0
TIR_UP_X = 800.0
DOOR_BUMP_X = 405.0
KNIT = "#c9524a"

_DS = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2)
_DC = cairo.Context(_DS)


def _measure_person(who, s, t, **kw):
    kw["shadow"] = False
    kw.pop("hold", None)
    return draw_person(_DC, who, 0.0, 0.0, s, t, **kw)


def _measure_imp(s, t, **kw):
    kw.pop("hold", None)
    return creatures.draw_impulsivity(_DC, 0.0, 0.0, s, t, **kw)


# ----------------------------------------------------------------------------
# timing
# ----------------------------------------------------------------------------
def _cues(info):
    q = info.cue
    L = {k: info.line(k) for k in ("s07_l01", "s07_l02", "s07_l03", "s07_l03b", "s07_l04")}
    c = dict(scoop=q("scoop"), doorClose=q("doorClose"), open=q("open"), burst=q("burst"),
             tug=q("tug"), squint=q("squint"), creak=q("creak"), bite=q("bite"),
             runout=q("runout"), catch=q("catch"), stare=q("stare"), end=info.dur)
    for k, short in (("s07_l01", "l01"), ("s07_l02", "l02"), ("s07_l03", "l03"),
                     ("s07_l03b", "l03b"), ("s07_l04", "l04")):
        c[short] = L[k].start
        c[short + "e"] = L[k].end
    c["A1"] = max(c["scoop"] + 0.62, c["l01"] - 0.2)
    c["B1"] = min(c["l01"] + 0.5, c["doorClose"] - 1.1)
    c["bump"] = c["doorClose"] + 0.1
    c["C1"] = min(c["l02"] + 0.45, c["open"] - 0.55)
    c["G1"] = c["creak"] - 0.42
    c["J1"] = c["runout"] - 0.08
    c["K1"] = c["l03b"] - 0.05
    return c


# ----------------------------------------------------------------------------
# small drawing helpers
# ----------------------------------------------------------------------------
def _room(ctx, t, layer="bg", door=0.0, **kw):
    st = dict(BR)
    st.update(kw)
    sets.bedroom(ctx, t, layer=layer, door_open=door, **st)


def _inside(kind, t, wig=0.3, look=(0.3, -0.3), blink=None):
    """inside_fn for the cage (cage units, origin = interior floor centre)."""
    def fn(c):
        if kind in ("bundle", "peek", "empty"):
            creatures.draw_sweater_lump(c, -6, 0, 0.56, t, wiggle=wig, color=KNIT)
        if kind == "peek":
            creatures.draw_thing(c, 46, -34, 0.95, t, state="peek", look=look, blink=blink)
            # a fold of knit over its chin so it peeks OUT of the sweater
            c.move_to(-10, -6)
            c.curve_to(20, -40, 70, -34, 96, -4)
            c.line_to(96, 4)
            c.line_to(-10, 4)
            c.close_path()
            core.fill_stroke(c, KNIT, core.PAL["ink"], 5)
        if kind == "thing":
            creatures.draw_sweater_lump(c, -40, 0, 0.42, t, wiggle=0.0, color=KNIT)
            creatures.draw_thing(c, 40, 0, 0.9, t, state="cage_inside", look=look, blink=blink)
    return fn


def _cage(ctx, x, y, t, door=0.0, latch="half", rattle=0.0, inside=None, rot=0.0, s=CAGE_S):
    props.cage(ctx, x, y, s, t, door=door, latch=latch, rattle=rattle, inside_fn=inside, rot=rot)


def _cage_pt(ax, ay, rot, lx, ly, s=CAGE_S):
    """world point of cage-local (lx, ly) for a cage anchored at (ax, ay) rotated rot."""
    cr, sr = math.cos(rot), math.sin(rot)
    return ax + (lx * cr - ly * sr) * s, ay + (lx * sr + ly * cr) * s


def _ticks(ctx, x, y, s, t, amt=1.0, seed=0):
    """little ink 'jiggle' ticks either side of a point."""
    if amt <= 0.02:
        return
    for side in (-1, 1):
        for k in range(2):
            ph = math.sin(t * 22 + k * 1.7 + seed) * 0.5 + 0.5
            ox = x + side * (22 + k * 14 + ph * 4) * s
            ctx.move_to(ox, y - (12 + k * 4) * s)
            ctx.line_to(ox + side * 7 * s, y)
            ctx.line_to(ox, y + (12 + k * 4) * s)
            core.stroke(ctx, core.alpha("ink", amt), 3.5 * s)


def _shake(t, t0, dur, amp, seed=3):
    return core.shake(t, t0, dur, amp, seed)


def _blinkdip(t, t0, close=0.3, hold=0.15, open_=0.32):
    """slow judgement blink 0..1."""
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0),
                     (t0 + close + hold + open_, 0.0)])


def _sum_face(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _fk(t, keys, trans=0.25):
    """keyframed face dicts -> blended dict (state_at with dict values)."""
    prev, cur, start = keys[0][1], keys[0][1], -1e9
    for tk, d in keys:
        if t >= tk:
            prev, cur, start = cur, d, tk
        else:
            break
    k = core.smoothstep(seg(t, start, start + trans))
    out = {}
    for key in set(prev) | set(cur):
        out[key] = lerp(prev.get(key, 0.0), cur.get(key, 0.0), k)
    return out


# expressions (dict exprs use EXPR conventions)
STRAIN = dict(brow=0.55, brow_ang=0.62, brow_in=0.2, lid=0.12, lower=0.25, pupil=0.62,
              teeth=1.0, open=0.2, width=1.28, curve=-0.42, wobble=0.25, cheek=0.25, flare=0.5,
              squash=0.04)
SCREAM_SHUT = dict(brow=0.7, brow_ang=0.85, brow_in=0.35, lid=1.0, lower=0.6, open=1.0,
                   width=1.5, lip_low=0.7, curve=-0.4, tongue=0.85, teeth=0.7, lip_up=0.45, squash=-0.24,
                   flare=0.7, cheek=0.25)


# ----------------------------------------------------------------------------
# Emb poses
# ----------------------------------------------------------------------------
_TY_DESK = (FLOOR - DESK_Y) / S / H_EMB
P_PRESS = {"base": "cover_sweater", "al_ty": _TY_DESK, "ar_ty": _TY_DESK, "hold": 2.0,
           "al_tz": 0.26, "ar_tz": 0.28}
P_LIFT = {"base": "cover_sweater", "hold": 2.0, "lean": 0.6, "al_ty": _TY_DESK + 0.1,
          "ar_ty": _TY_DESK + 0.12, "al_tz": 0.36, "ar_tz": 0.38, "al_h": "grip", "ar_h": "grip"}
P_SHOVE = {"base": "cover_sweater", "hold": 2.0, "lean": 0.86, "al_ty": _TY_DESK + 0.06,
           "ar_ty": _TY_DESK + 0.07, "al_tz": 0.56, "ar_tz": 0.58, "al_h": "grip", "ar_h": "grip"}
P_SLAP = {"base": "cover_sweater", "lean": 0.7, "al_ty": 0.62, "al_tz": 0.12, "al_tx": 0.12,
          "al_h": "open", "ar_ty": _TY_DESK + 0.06, "ar_tz": 0.6, "ar_h": "flat"}
P_RECOIL = {"base": "awkward", "lean": -0.04}

# carrying the cage: r hand at the side (near hand when facing right with flip=True)
_CAGE_R = dict(HA("r", 0.02, 0.12, 0.05, h="grip", tf=1.0), ar_ik=0.0, ar_th=0.0, hold=1.0)
P_BACKWALK = dict({"base": "walk", "period": 0.36},
                  **HIK("l", 0.14, 0.62, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                  al_w=HW(0.0, 0.42, 0.0), lean=-0.1, hunch=0.55, **_CAGE_R)
P_FREEZE = dict({"base": "stand"}, **HIK("l", 0.14, 0.6, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                hunch=1.0, lean=-0.06, nod=0.04, breath=0.2, sway=0.0, **_CAGE_R)
P_SHEEP = dict({"base": "stand", "period": 0.32},
               **HHK("l", 70, -40, "claw", layer="mid", bend=-1.0, wa=-1.9, wabs=0.7),
               al_fing=HW(0.0, 0.6, 0.0), hunch=0.6, tilt=-0.12, nod=0.08, lean=0.03,
               lift=HW(2.0, 2.0, 0.0), **_CAGE_R)
P_REACH = dict({"base": "stand"}, **HIK("l", 0.1, 0.52, 0.42, "grip", wa=0.2, wabs=0.6),
               lean=0.12, **_CAGE_R)
P_PULL = dict({"base": "stand"}, **HIK("l", 0.08, 0.54, 0.3, "grip", wa=0.2, wabs=0.6),
              lean=-0.14, **_CAGE_R)
P_GAWK = dict({"base": "stand"}, **HIK("l", 0.12, 0.6, 0.2, "open", tf=-1.0, wa=-1.3, wabs=0.85),
              hunch=0.9, lean=-0.1, breath=0.2, sway=0.0, **_CAGE_R)
P_KNOCKED = {"base": "tug", "hold": 0.0, "lean": -0.5}

# tug, with lower hands so the cage reaches the dog's mouth
P_TUG = {"base": "tug", "period": 1.2, "lean": HW(-0.52, 0.1, 0.0), "al_ty": 0.34, "ar_ty": 0.37,
         "hold": 0.0, "tilt": HW(0.04, 0.05, 0.25)}

# catch / crouch with both hands low in front
P_CROUCH_READY = {"base": "crouch", "lean": 0.45, **HIK("l", 0.1, 0.35, 0.3, "claw"),
                  **HIK("r", 0.1, 0.35, 0.32, "claw")}
P_DIVE = {"base": "catch", "lean": 0.55, "lift": 40.0}
P_GRAB = {"base": "crouch", **HIK("l", 0.06, 0.13, 0.42, "claw"), **HIK("r", 0.06, 0.15, 0.44, "claw"),
          "hold": 2.0}
P_STUFF = {"base": "crouch", **HIK("l", 0.04, 0.2, 0.62, "claw"), **HIK("r", 0.04, 0.22, 0.64, "claw"),
           "hold": 2.0, "lean": 0.85}
P_SHUT = {"base": "crouch", **HIK("l", 0.05, 0.22, 0.55, "flat", wa=0.2, wabs=0.6),
          **HIK("r", 0.05, 0.26, 0.6, "flat", wa=0.2, wabs=0.6), "lean": 0.8}
P_KNEEL = {"base": "crouch", **HIK("l", 0.05, 0.2, 0.5, "flat", wa=0.3, wabs=0.6),
           **HIK("r", 0.05, 0.24, 0.52, "flat", wa=0.3, wabs=0.6), "lean": 0.62, "neck": -0.05,
           "nod": -0.1}
P_FACEPALM = {"base": "crouch", **HIK("l", 0.05, 0.2, 0.5, "flat", wa=0.3, wabs=0.6),
              **HHK("r", -6, -28, "flat", layer="front", wa=-1.9, wabs=0.8),
              "lean": 0.5, "nod": 0.24, "tilt": -0.1, "hunch": 0.5, "neck": 0.2}

# Tiredness
T_CROSS = "arms_crossed"
T_LEAN = {"base": "arms_crossed", "lean": 0.62, "neck": 0.34, "nod": -0.12, "hunch": 0.3,
          "ll_p": 0.3, "ll_k": 0.45, "lr_p": 0.18, "lr_k": 0.38}
T_UPRIGHT = {"base": "arms_crossed", "lean": -0.06, "chest": -0.05, "nod": -0.05}
T_JERK = {"base": "arm_jerk", "period": 0.11, "ar_p": HW(0.6, 0.1, 0.0), "ar_o": HW(1.3, 0.12, 0.3),
          "ar_e": HW(1.2, 0.18, 0.15), "ar_eo": -0.5, "dx": HW(0.0, 4.0, 0.1),
          "tilt": HW(0.1, 0.03, 0.2), "lean": -0.12, "hunch": 0.85}
T_WALK = "walk"


# ----------------------------------------------------------------------------
# A — scoop (desk medium)
# ----------------------------------------------------------------------------
def shot_scoop(ctx, t, info, c):
    u = t - c["scoop"]
    ex, ey = M["desk_lean_feet"]
    cam = (1985 - 10 * seg(u, 0, 0.9), 1040, 1.28 + 0.04 * seg(u, 0, 0.9))
    pose = state_at(u, [(-1, P_PRESS), (0.14, P_LIFT), (0.31, P_SHOVE), (0.45, P_SLAP),
                        (0.6, P_RECOIL)], 0.12)
    turn = tween(u, [(0.55, 0.8), (0.8, 0.45)])
    look = tween(u, [(0.0, (0.5, 0.55)), (0.14, (0.8, 0.2)), (0.5, (0.8, 0.25)),
                     (0.6, (-0.85, 0.0))], ease_out)
    face = _sum_face({"head_turn": -0.3 * ease_in_out(seg(u, 0.68, 0.85))},
                     {"press": 0.3 * seg(u, 0.6, 0.7)})
    expr = state_at(u, [(-1, "nervous_smile"), (0.14, "panic"), (0.6, "nervous_smile")], 0.12)
    door = tween(u, [(0.47, 1.0), (0.55, 0.0), (0.6, 0.1), (0.66, 0.0)], ease_in)
    rattle = 0.0
    if u > 0.36:
        rattle = 0.7 * (1 - seg(u, 0.56, 0.95))
    a0 = _measure_person("embar", S, t, pose=pose, turn=turn, pose_t=u)
    hx = ex + (a0["hand_l"][0] + a0["hand_r"][0]) * 0.5
    hy = ey + (a0["hand_l"][1] + a0["hand_r"][1]) * 0.5
    a_rest = _measure_person("embar", S, 0.0, pose=P_PRESS, turn=0.8, pose_t=0.0)
    lump_x = ex + (a_rest["hand_l"][0] + a_rest["hand_r"][0]) * 0.5
    inside = None
    if u >= 0.44:
        inside = _inside("bundle", t, wig=0.75 * (1 - seg(u, 0.5, 1.2)) + 0.25)
    ax, ay = CAGE_DESK
    in_x, in_y = _cage_pt(ax, ay, 0.0, 0, 234)

    def bundle(cx_, cy_, sc, wig, rot=0.0):
        with core.saved(ctx, cx_, cy_, 1.0, rot):
            creatures.draw_sweater_lump(ctx, 0, 0, sc, t, wiggle=wig, color=KNIT)

    def hold_fn(cx_, side, x, y, ang):
        if 0.14 <= u < 0.38:
            bundle(x, y + 26, 0.44, 0.6, -0.15 * seg(u, 0.14, 0.38))

    sh = _shake(t, c["scoop"] + 0.55, 0.22, 6)
    with core.camera(ctx, cam[0] + sh[0], cam[1] + sh[1], cam[2]):
        _room(ctx, t, door=0.45)
        if u < 0.14:
            bundle(lump_x, DESK_Y, 0.44, 0.55)
        _cage(ctx, ax, ay, t, door=door, latch="half" if u > 0.5 else "open", rattle=rattle,
              inside=inside)
        a = draw_person(ctx, "embar", ex, ey, S, t, pose=pose, expr=expr, look=look, turn=turn,
                        face=face, pose_t=u, hold=hold_fn, mouth=info.mouth("embar", t),
                        blush=0.5, sweat=0.6)
        if 0.38 <= u < 0.47:
            k = ease_in(seg(u, 0.38, 0.47))
            bundle(lerp(hx, in_x, k), lerp(hy + 26, in_y, k), lerp(0.44, 0.3, k), 0.9)
            fx.motion_lines(ctx, lerp(hx, in_x, k) - 40, lerp(hy, in_y, k) - 10, 0.0, 120, t, 0.8)
        if u >= 0.55:
            lx, ly = _cage_pt(ax, ay, 0.0, 150, 160)
            _ticks(ctx, lx, ly, 1.2, t, 1 - seg(u, 0.7, 0.85))


# ----------------------------------------------------------------------------
# B — latch insert
# ----------------------------------------------------------------------------
def shot_latch(ctx, t, info, c):
    u = t - c["A1"]
    ax, ay = CAGE_DESK
    lx, ly = _cage_pt(ax, ay, 0.0, 118, 158)
    z = 3.0 + 0.3 * ease_in_out(seg(u, 0, 0.8))
    with core.camera(ctx, lx - 70, ly + 10, z):
        _room(ctx, t, door=0.45)
        _cage(ctx, ax, ay, t, door=0.0, latch="half", rattle=0.12 * (1 - seg(u, 0, 0.35)),
              inside=_inside("bundle", t, wig=0.45))
        _ticks(ctx, lx + 8, ly, 0.75, t, 0.9)


# ----------------------------------------------------------------------------
# C — back away to the door, bump, freeze, "Heh heh"
# ----------------------------------------------------------------------------
_BACK_RATE = 1.35


def _emb_back_x(t, c):
    v = abs(cycle_speed("embar", "walk", -0.7)) * S * _BACK_RATE
    tb = c["bump"]
    return DOOR_BUMP_X + v * max(0.0, tb - t)


def _door_c(t, c):
    tb = c["bump"]
    return tween(t, [(tb - 0.02, 0.45), (tb + 0.1, 0.0), (tb + 0.15, 0.04), (tb + 0.2, 0.0)], ease_in)


def shot_back(ctx, t, info, c):
    tb = c["bump"]
    ex = _emb_back_x(t, c)
    if t < tb:
        pose = P_BACKWALK
        pt = (tb - t) * _BACK_RATE
    else:
        pose = state_at(t, [(-1, P_BACKWALK), (tb, P_FREEZE), (c["l02"], P_SHEEP)],
                        0.1 if t < c["l02"] else 0.22)
        pt = t - tb
    bump_k = seg(t, tb, tb + 0.06) * (1 - seg(t, tb + 0.06, tb + 0.3))
    ex_draw = ex + 10 * bump_k
    # expressions
    expr = state_at(t, [(-1, "nervous_smile"), (tb, "alarmed"), (c["l02"], "sheepish")],
                    0.08 if t < c["l02"] else 0.2)
    look = tween(t, [(c["B1"], (0.85, 0.05)), (tb + 0.12, (0.85, 0.05)), (tb + 0.25, (-1.0, 0.1)),
                     (c["l02"] - 0.1, (-1.0, 0.1)), (c["l02"] + 0.12, (0.75, 0.2))], ease_out)
    face = _fk(t, [(-1, {}), (tb, {"press": 0.7, "pupil": -0.35, "lid": -0.1, "brow": 0.2,
                                   "eye_size": 0.06}),
                   (c["l02"], {"blush": 0.1})], 0.1)
    blush = tween(t, [(tb, 0.45), (tb + 0.3, 0.7), (c["l02"], 0.6)])
    # Tiredness, watching him go
    tx, ty = 1450.0, FLOOR
    rel = (ex - tx) / 600.0
    t_look = (clamp(rel * 0.9, -1.0, 0.2), 0.08)
    t_head = clamp(rel * 0.35, -0.4, 0.1)
    # camera follows Emb, then pushes in on the freeze
    px = clamp(ex + 150, 600, 1250)
    zoom = 0.95 + 0.33 * ease_in_out(seg(t, tb + 0.1, c["C1"]))
    cx = lerp(px, ex + 60, seg(t, tb, c["C1"]) ** 0.7)
    cy = 1040 - 70 * seg(t, tb, c["C1"])
    sh = _shake(t, tb, 0.18, 5)
    with core.camera(ctx, cx + sh[0], cy + sh[1], zoom):
        _room(ctx, t, door=_door_c(t, c))
        if tx - 300 < cx + 540 / zoom + 300:
            # head follows the pupils ~0.15 s later: sample the eye target slightly earlier
            rel_l = (_emb_back_x(t - 0.15, c) - tx) / 600.0
            draw_person(ctx, "tired", tx, ty, S, t, pose=T_CROSS, expr="unamused", turn=-0.55,
                        look=t_look, face={"head_turn": clamp(rel_l * 0.35, -0.4, 0.1)},
                        headphones=HP, mouth=info.mouth("tired", t))
        draw_person(ctx, "embar", ex_draw, FLOOR, S, t, pose=pose, pose_t=pt, expr=expr, look=look,
                    face=face, turn=-0.7, flip=True, blush=blush, sweat=0.5,
                    mouth=info.mouth("embar", t), hold=_hold_cage(t, door=0.0, latch="half"))
        if tb <= t < tb + 0.5:
            fx.tap_marks(ctx, ex_draw - 70, FLOOR - 410, 0.8, t, tb, taps=1, angle=math.pi, label=None)


def _hold_cage(t, door=0.0, latch="half", rattle=0.0, inside="bundle", wig=0.4):
    def fn(ctx, side, x, y, ang):
        _cage(ctx, x, y, t, door=door, latch=latch, rattle=rattle,
              inside=_inside(inside, t, wig=wig) if inside else None)
    return fn


# ----------------------------------------------------------------------------
# D — Tiredness reaction close-up
# ----------------------------------------------------------------------------
def shot_tired(ctx, t, info, c):
    u = t - c["C1"]
    tx, ty = 1450.0, FLOOR
    z = 2.05 + 0.12 * seg(u, 0, 0.8)
    bl = _blinkdip(t, c["C1"] + 0.12, 0.3, 0.14, 0.3)
    face = _fk(u, [(-1, {"head_turn": -0.35}), (0.62, {"head_turn": -0.35, "lid": 0.07, "brow_r": 0.12})],
               0.25)
    with core.camera(ctx, 1395, 965, z):
        _room(ctx, t, door=0.0)
        draw_person(ctx, "tired", tx, ty, S, t, pose=T_CROSS, expr="unamused", turn=-0.55,
                    look=(-0.85, 0.06), face=face, blink=bl if bl > 0.01 else None,
                    headphones=HP, mouth=info.mouth("tired", t))


# ----------------------------------------------------------------------------
# E — open the door; Impulsivity; burst
# ----------------------------------------------------------------------------
def _imp_lunge_c(t, c):
    b = c["burst"]
    return tween(t, [(b + 0.12, (150.0, 1130.0)), (b + 0.3, (296.0, 1286.0)),
                     (b + 0.5, (370.0, 1330.0))], ease_out)


def shot_door(ctx, t, info, c):
    o, b = c["open"], c["burst"]
    u = t - o
    # Emb: reach, pull the door open stepping back, gawk, get blasted
    ex = tween(t, [(o + 0.05, 470.0), (o + 0.42, 600.0), (b + 0.3, 600.0), (b + 0.5, 700.0)], ease_out)
    pose = state_at(t, [(-1, P_REACH), (o + 0.08, P_PULL), (o + 0.42, P_GAWK), (b + 0.3, P_KNOCKED)],
                    0.14)
    door = tween(t, [(o + 0.08, 0.0), (o + 0.42, 0.56), (b + 0.12, 0.56), (b + 0.2, 1.0)], ease_in_out)
    expr = state_at(t, [(-1, "nervous_smile"), (o + 0.42, "frozen_shock"), (b + 0.3, "terrified")], 0.1)
    look = tween(t, [(o, (-0.9, 0.0)), (o + 0.42, (-1.0, 0.05)), (b + 0.12, (-1.0, 0.05)),
                     (b + 0.3, (-0.9, 0.3))])
    face = {"head_turn": -0.15 * seg(t, o + 0.5, o + 0.65)}
    blush = tween(t, [(o + 0.42, 0.55), (o + 0.7, 0.05)])
    imp_lunge = t >= b + 0.12
    clamp_on = t >= b + 0.3
    lunge_c = _imp_lunge_c(t, c)
    sh = _shake(t, b + 0.3, 0.32, 10)
    zoom = 1.12 + 0.06 * seg(t, o, b) - 0.1 * ease_out(seg(t, b + 0.12, b + 0.4))
    cx = 520 + 40 * ease_out(seg(t, b + 0.12, b + 0.5))

    def imp_hall():
        if imp_lunge:
            return
        snap = seg(t, b, b + 0.1)
        if t < b:
            creatures.draw_impulsivity(ctx, M["hall_feet"][0], M["hall_feet"][1] + 4, IMP_S, t,
                                       pose="sit", pant=1.0)
        else:
            # pupils snap together onto the cage: the tripwire goes off
            tgt = (0.9, 0.45)
            ll = (lerp(creatures.IMP_DERP_L[0], tgt[0], snap), lerp(creatures.IMP_DERP_L[1], tgt[1], snap))
            lr = (lerp(creatures.IMP_DERP_R[0], tgt[0], snap), lerp(creatures.IMP_DERP_R[1], tgt[1], snap))
            creatures.draw_impulsivity(ctx, M["hall_feet"][0], M["hall_feet"][1] + 4, IMP_S, t,
                                       pose="sit", expr="focused" if snap > 0.6 else "derp",
                                       look_l=ll, look_r=lr, pant=0.0)

    with core.camera(ctx, cx + sh[0], 1060 + sh[1], zoom):
        _room(ctx, t, layer="back", door=door)
        imp_hall()
        _room(ctx, t, layer="room", door=door)
        cage_hold = None if clamp_on else _hold_cage(t, latch="half", rattle=0.3 * seg(t, b, b + 0.3))
        a = draw_person(ctx, "embar", ex, FLOOR, S, t, pose=pose, expr=expr, look=look, turn=-0.7,
                        face=face, blush=blush, sweat=0.7, mouth=info.mouth("embar", t),
                        hold=cage_hold, glint=seg(t, o + 0.42, o + 0.5) * (1 - seg(t, o + 0.5, o + 0.62)))
        if imp_lunge:
            ctx.save()
            ctx.rectangle(M["door"][0], -2000, 6000, 6000)
            ctx.clip()
            ia = creatures.draw_impulsivity(ctx, lunge_c[0], lunge_c[1], IMP_S, t, pose="lunge",
                                            expr="excited", pose_t=t - (b + 0.12))
            ctx.restore()
            fx.motion_lines(ctx, lunge_c[0] - 330, lunge_c[1] - 40, 0.55, 300, t,
                            1.0 - seg(t, b + 0.4, b + 0.5))
            if clamp_on:
                mx, my = ia["mouth"]
                hx, hy = a["hand_r"][0], a["hand_r"][1]
                _cage(ctx, (mx + hx) * 0.5, (my + hy) * 0.5, t, latch="half", rattle=0.8, rot=-0.2,
                      inside=_inside("bundle", t, wig=0.9))
                fx.impact_star(ctx, mx + 20, my - 10, 0.5, t, b + 0.3, dur=0.3, spikes=9)
        if t < b + 0.12:
            pass
        if o + 0.42 <= t < b:
            fx.emote(ctx, "exclaim", a["top"][0] + 10, a["top"][1] - 50, 0.8, t, o + 0.5, dur=0.6)


# ----------------------------------------------------------------------------
# F/G/H/I — the tug (shared world staging)
# ----------------------------------------------------------------------------
TIR_TUG = (1150.0, 1600.0)      # downstage-right, watching
TIR_PEER = (968.0, 1600.0)      # half-squat right next to the cage
T_PEER = {"base": "arms_crossed", "lean": 0.6, "neck": 0.3, "nod": -0.1,
          "ll_p": 1.1, "ll_o": 0.24, "ll_k": 1.9, "ll_a": 0.15,
          "lr_p": 0.85, "lr_o": 0.2, "lr_k": 1.95, "lr_a": 0.25}
T_RISE = {"base": "arms_crossed", "lean": -0.08, "chest": -0.06, "nod": -0.06, "lift": 6.0}


def _tug_rig(t, c, freeze_t=None):
    """Solve the tug: Imp's mouth holds the handle, Emb's hands grip the cage's
    right side. Returns dict(imp_t, mouth, rot, emb_x, emb_pt)."""
    it = t if freeze_t is None else freeze_t
    ia = _measure_imp(IMP_S, it, pose="tug")
    mx, my = IMP_X + ia["mouth"][0], TUG_Y + ia["mouth"][1]
    ept = it * 2.2 * 1.2
    ea = _measure_person("embar", S, it, pose=P_TUG, turn=-0.85, pose_t=ept)
    hx = (ea["hand_l"][0] + ea["hand_r"][0]) * 0.5
    hy = (ea["hand_l"][1] + ea["hand_r"][1]) * 0.5
    gx, gy = 158.0, 150.0
    R = math.hypot(gx, gy) * CAGE_S
    phi = math.atan2(gy, gx)
    dy = (TUG_Y + hy) - my
    ang = math.asin(clamp(dy / R, -0.98, 0.98))
    rot = ang - phi
    dx = R * math.cos(ang)
    emb_x = mx + dx - hx
    return dict(imp_t=it, mouth=(mx, my), rot=rot, emb_x=emb_x, emb_pt=ept)


def _draw_tug(ctx, t, c, info, rig, tired_fn=None, cage_door=0.0, latch="half", inside="bundle",
              rattle=0.4, emb_expr=None, emb_look=(-0.8, 0.25), emb_face=None, imp_expr="derp",
              imp_look=(None, None), wig=0.6, ins_look=(0.4, -0.3), ins_blink=None, emb_t=None,
              upstage_fn=None):
    """bg must be drawn. upstage_fn before the tuggers, tired_fn (downstage) after."""
    it = rig["imp_t"]

    def cage_cb(cx_, a):
        mx, my = a["mouth"]
        _cage(cx_, mx, my, t, door=cage_door, latch=latch, rattle=rattle, rot=rig["rot"],
              inside=_inside(inside, t, wig=wig, look=ins_look, blink=ins_blink) if inside else None)

    if upstage_fn:
        upstage_fn()
    ia = creatures.draw_impulsivity(ctx, IMP_X, TUG_Y, IMP_S, it, pose="tug", expr=imp_expr,
                                    look_l=imp_look[0], look_r=imp_look[1],
                                    hold=lambda c_, a: cage_cb(c_, a))
    # the cage BODY again over the lolling tongue (the handle stays between the jaws)
    mx, my = ia["mouth"]
    rj = rattle * (0.07 * math.sin(t * 47) + 0.04 * math.sin(t * 31 + 1.3)) if rattle > 0 else 0.0
    ctx.save()
    m0 = ctx.get_matrix()
    ctx.translate(mx, my)
    ctx.rotate(rig["rot"] + rj)
    ctx.scale(CAGE_S, CAGE_S)
    ctx.rectangle(-175, 36, 350, 260)
    ctx.set_matrix(m0)
    ctx.clip()
    cage_cb(ctx, ia)
    ctx.restore()
    et = t if emb_t is None else emb_t
    a = draw_person(ctx, "embar", rig["emb_x"], TUG_Y, S, et, pose=P_TUG, pose_t=rig["emb_pt"],
                    turn=-0.85, expr=emb_expr or STRAIN, look=emb_look, face=emb_face,
                    blush=0.6, sweat=0.9, mouth=info.mouth("embar", t))
    ta = tired_fn() if tired_fn else None
    return a, ta


def shot_tug(ctx, t, info, c):
    u = t - c["tug"]
    rig = _tug_rig(t, c)
    # Tiredness strolls in downstage and stops, arms crossed, unimpressed
    w0, w1 = c["tug"] + 0.1, c["tug"] + 0.95
    v = abs(cycle_speed("tired", "walk", -0.9)) * S
    tx = TIR_TUG[0] + v * clamp(w1 - t, 0.0, w1 - w0)
    walking = t < w1
    tpose = state_at(t, [(-1, T_WALK), (w1, T_CROSS)], 0.3)
    bl = _blinkdip(t, c["tug"] + 1.35, 0.34, 0.12, 0.34)
    # pupils ride the shaking cage, head follows late
    cage_c = _cage_pt(rig["mouth"][0], rig["mouth"][1], rig["rot"], 0, 150)
    lk = (-0.95, 0.12 + 0.06 * math.sin(t * 2.2 * math.tau))
    t_face = {"head_turn": -0.12 * seg(t, w1 + 0.1, w1 + 0.4), "lid": 0.06 * seg(t, c["tug"] + 1.8, c["squint"])}

    def tired_fn():
        return draw_person(ctx, "tired", tx, TIR_TUG[1], S, t, pose=tpose,
                           pose_t=(t - w0) if walking else 0.0, turn=-0.75, expr="unamused",
                           look=lk, headphones=HP, face=t_face, blink=bl if bl > 0.01 else None,
                           mouth=info.mouth("tired", t))

    z = 0.98 + 0.07 * ease_in_out(seg(u, 0, 2.0))
    cx = 780 + 25 * seg(u, 0, 2.0)
    sh = _shake(t, c["tug"], 0.25, 6)
    with core.camera(ctx, cx + sh[0], 1080 + sh[1], z):
        _room(ctx, t, door=1.0)
        a, _ = _draw_tug(ctx, t, c, info, rig, tired_fn=tired_fn, rattle=0.55,
                         emb_look=(-0.9, 0.3))
        hx, hy = a["top"]
        fx.sweat_fly(ctx, a["head"][0] + 40, a["head"][1] - 30, 0.7, t, c["tug"] + 0.5, seed=2, side=1)
        fx.sweat_fly(ctx, a["head"][0] + 40, a["head"][1] - 30, 0.7, t, c["tug"] + 1.3, seed=5, side=1)


def _peer_pose(t, t0):
    """stand -> rise (anticipation) -> half-squat lean with a soft overshoot."""
    u = t - t0
    if u < 0.1:
        return (T_CROSS, T_RISE, ease_in_out(seg(u, 0.0, 0.1)))
    k = seg(u, 0.1, 0.5)
    return (T_RISE, T_PEER, clamp(ease_out_back(k, 1.2), 0.0, 1.06))


CLOSE_CAM = (790.0, 1190.0, 2.15)


def shot_squint(ctx, t, info, c):
    u = t - c["squint"]
    rig = _tug_rig(t, c)
    pose = _peer_pose(t, c["squint"])
    expr = state_at(u, [(-1, "unamused"), (0.42, "squint")], 0.28)
    look = tween(u, [(0.0, (-0.95, 0.15)), (0.3, (-0.9, 0.35))])
    face = {"head_turn": -0.1, "lid": -0.16 * seg(u, 0.3, 0.6), "lower": 0.12 * seg(u, 0.4, 0.7),
            "head_nod": 0.06 * seg(u, 0.2, 0.5)}

    def tired_fn():
        return draw_person(ctx, "tired", TIR_PEER[0], TIR_PEER[1], S, t, pose=pose, turn=-0.75,
                           expr=expr, look=look, face=face, headphones=HP,
                           mouth=info.mouth("tired", t))

    z = CLOSE_CAM[2] + 0.1 * ease_in_out(seg(u, 0, 0.8))
    with core.camera(ctx, CLOSE_CAM[0], CLOSE_CAM[1], z):
        _room(ctx, t, door=1.0)
        _draw_tug(ctx, t, c, info, rig, tired_fn=tired_fn, rattle=0.35, emb_look=(-0.6, 0.5))


def shot_eyes(ctx, t, info, c):
    u = t - c["G1"]
    rig = _tug_rig(t, c)
    ax, ay = rig["mouth"]
    ix, iy = _cage_pt(ax, ay, rig["rot"], 34, 168)
    bl = tween(u, [(0.0, 1.0), (0.1, 1.0), (0.18, 0.0), (0.34, 0.0), (0.38, 1.0), (0.42, 0.0)])
    z = 6.2 + 0.5 * seg(u, 0, 0.42)
    with core.camera(ctx, ix, iy, z, rot=-rig["rot"]):
        _room(ctx, t, door=1.0)
        _draw_tug(ctx, t, c, info, rig, rattle=0.1, inside="peek", wig=0.05, ins_look=(0.55, -0.25),
                  ins_blink=bl, emb_look=(-0.6, 0.5))


def _bite_point(a):
    wx, wy = a["wrist_r"]
    hx, hy, ang = a["hand_r"]
    return (wx + (wx - hx) * 0.7, wy + (wy - hy) * 0.7 - 6)


def shot_creak(ctx, t, info, c):
    cr, bi = c["creak"], c["bite"]
    # 2-frame freeze on the chomp
    tf = bi + 0.12
    te = t
    if tf <= t < tf + 2.0 / 24:
        te = tf
    rig = _tug_rig(te, c)
    door = tween(te, [(cr + 0.08, 0.0), (cr + 0.72, 0.78)], ease_in_out)
    latch = "half" if te < cr + 0.05 else "open"
    lift = seg(te, cr + 0.22, cr + 0.44)
    look = tween(te, [(cr, (-0.9, 0.35)), (cr + 0.18, (-0.85, 0.6)), (bi, (-0.85, 0.6)),
                      (tf + 0.12, (-0.75, 0.7)), (tf + 0.22, (-0.2, 0.95))], ease_out)
    face = {"head_turn": -0.1, "head_nod": 0.06, "lid": -0.16 - 0.12 * lift, "lower": 0.12 * (1 - lift),
            "brow": 0.18 * lift,
            "brow_r": 0.12 * lift, "pupil": -0.3 * seg(te, tf + 0.1, tf + 0.25),
            "press": 0.4 * seg(te, tf + 0.1, tf + 0.25)}
    expr = state_at(te, [(-1, "squint"), (cr + 0.22, "bored")], 0.2)
    pose = (T_RISE, T_PEER, 1.0)
    st = {}

    def tired_fn():
        st["a"] = draw_person(ctx, "tired", TIR_PEER[0], TIR_PEER[1], S, te, pose=pose, turn=-0.75,
                              expr=expr, look=look, face=face, headphones=HP,
                              mouth=info.mouth("tired", t))
        return st["a"]

    inside = "peek" if te < bi else "empty"
    z = CLOSE_CAM[2] + 0.1 + 0.08 * seg(te, cr, bi)
    sh = _shake(t, tf, 0.2, 5)
    with core.camera(ctx, CLOSE_CAM[0] + sh[0], CLOSE_CAM[1] + sh[1], z):
        _room(ctx, te, door=1.0)
        _draw_tug(ctx, te, c, info, rig, tired_fn=tired_fn, rattle=0.2, cage_door=door, latch=latch,
                  inside=inside, emb_look=(-0.6, 0.5), wig=0.05, ins_look=(0.7, -0.35))
        if te >= bi:
            ta = st["a"]
            bx, by = _bite_point(ta)
            ox, oy = _cage_pt(rig["mouth"][0], rig["mouth"][1], rig["rot"], 20, 170)
            if te < tf:
                k = ease_out(seg(te, bi, tf))
                px, py = lerp(ox, bx, k), lerp(oy, by, k) - 70 * math.sin(k * math.pi)
                ang = math.atan2(by - oy, bx - ox)
                with core.saved(ctx, px, py, 1.0, ang * 0.5):
                    creatures.draw_thing(ctx, 0, 0, THING_S, te, state="leap")
            else:
                creatures.draw_thing(ctx, bx, by, THING_S, te, state="bite")
                fx.impact_star(ctx, bx + 6, by - 8, 0.32, te, tf, dur=0.28, spikes=9)
        if cr + 0.08 <= te < cr + 0.8:
            hx_, hy_ = _cage_pt(rig["mouth"][0], rig["mouth"][1], rig["rot"], -112, 158)
            _ticks(ctx, hx_, hy_, 0.6, te, 0.5)


# ----------------------------------------------------------------------------
# J — the scream (a cartoon take on a radial burst)
# ----------------------------------------------------------------------------
_BURST_C = (380, 800)


def _burst_bg(c):
    c.rectangle(-50, -50, core.W + 100, core.H + 100)
    core.fill(c, "#ff9466")
    cx, cy = _BURST_C
    n = 24
    for i in range(0, n, 2):
        a0 = i / n * math.tau
        a1 = (i + 1) / n * math.tau
        c.move_to(cx, cy)
        c.line_to(cx + math.cos(a0) * 2600, cy + math.sin(a0) * 2600)
        c.line_to(cx + math.cos(a1) * 2600, cy + math.sin(a1) * 2600)
        c.close_path()
        core.fill(c, "#ffb47e")
    core.radial_glow(c, cx, cy, 560, "#fff0c4", 0.6)


def _squeeze(ctx, a, s, t, skin="t_skin"):
    """Eyes SQUEEZED shut: replace the rig's closed lids with bold > < chevrons."""
    (lx, ly), (rx, ry) = a["eye_l"], a["eye_r"]
    if lx > rx:
        (lx, ly), (rx, ry) = (rx, ry), (lx, ly)
    j = 1.0 + 0.08 * math.sin(t * 40)
    for ex, ey, sd in ((lx, ly, 1), (rx, ry, -1)):
        core.ellipse(ctx, ex, ey + 5 * s, 30 * s, 19 * s)
        core.fill(ctx, skin)
        w, h = 17 * s * j, 11 * s * j
        ctx.move_to(ex - sd * w, ey - h)
        ctx.line_to(ex + sd * w * 0.9, ey + 1 * s)
        ctx.line_to(ex - sd * w, ey + h)
        core.stroke(ctx, "ink", 6.0 * s)
        # one tension crease off the outer corner
        ctx.move_to(ex - sd * (w + 9 * s), ey - 3 * s)
        ctx.line_to(ex - sd * (w + 17 * s), ey - 7 * s)
        core.stroke(ctx, "ink", 3.2 * s)
    # pinch line between the brows
    mx = (lx + rx) * 0.5
    my = min(ly, ry) - 34 * s
    ctx.move_to(mx - 4 * s, my - 9 * s)
    ctx.curve_to(mx + 1 * s, my - 2 * s, mx + 1 * s, my + 4 * s, mx - 4 * s, my + 10 * s)
    core.stroke(ctx, "ink", 3.0 * s)


def shot_scream(ctx, t, info, c):
    t3, t3e = c["l03"], c["l03e"]
    u = t - t3
    core.cached(ctx, "s07_burst_bg", -50, -50, core.W + 100, core.H + 100, _burst_bg)
    sh = _shake(t, t3, 0.55, 16)
    z = 1.0 + 0.14 * (1 - ease_out_back(seg(u, 0.0, 0.2)))
    drop = t3e - 0.42
    s2 = 1.7
    x0, y0 = 380, 2240
    with core.saved(ctx, _BURST_C[0] + sh[0], _BURST_C[1] + sh[1], z):
        ctx.translate(-_BURST_C[0], -_BURST_C[1])
        a = draw_person(ctx, "tired", x0, y0, s2, t, pose=T_JERK, turn=-0.25, expr=SCREAM_SHUT,
                        mouth=info.mouth("tired", t), headphones=HP,
                        face={"head_tilt": 0.05 * math.sin(t * 38), "squash": -0.04 * math.sin(t * 19)})
        bx, by = _bite_point(a)
        ts = THING_S * s2 / S
        if t < drop:
            creatures.draw_thing(ctx, bx, by, ts, t, state="bite")
        else:
            k = seg(t, drop, drop + 0.4)
            with core.saved(ctx, bx + 60 * k, by + 1300 * k * k, 1.0, 2.0 * k):
                creatures.draw_thing(ctx, 0, 0, ts, t, state="struggle")
        hx, hy = a["head"]
        _squeeze(ctx, a, s2, t)
    # scream lines around the head
    sx = _BURST_C[0] + (hx - _BURST_C[0]) * z
    sy = _BURST_C[1] + (hy - _BURST_C[1]) * z
    for i in range(7):
        ang = -math.pi * 0.92 + i * math.pi * 0.84 / 6
        r0 = 330 + 22 * math.sin(t * 30 + i * 1.3)
        ctx.move_to(sx + math.cos(ang) * r0, sy - 40 + math.sin(ang) * r0)
        ctx.line_to(sx + math.cos(ang) * (r0 + 100), sy - 40 + math.sin(ang) * (r0 + 100))
        core.stroke(ctx, "ink", 13)


# ----------------------------------------------------------------------------
# K — run out, door slams
# ----------------------------------------------------------------------------
def _run_path(c):
    p0 = TIR_PEER
    p1 = (430.0, 1585.0)
    p2 = (M["doorway_feet"][0] + 30, M["doorway_feet"][1] + 10)
    v = abs(cycle_speed("tired", "scream_run", -1.0)) * S
    d1 = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    d2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    return p0, p1, p2, v, d1 / v, d2 / v


def shot_runout(ctx, t, info, c):
    t0 = c["J1"]
    u = t - t0
    p0, p1, p2, v, s1, s2 = _run_path(c)
    if u < s1:
        k = u / s1
        tx, ty = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
    else:
        k = min(1.0, (u - s1) / s2)
        tx, ty = lerp(p1[0], p2[0], k), lerp(p1[1], p2[1], k)
    in_door = u >= s1 + s2 * 0.35
    gone = u >= s1 + s2 + 0.1
    slam = t0 + s1 + s2 + 0.12
    door = tween(t, [(slam - 0.08, 1.0), (slam, 0.0), (slam + 0.05, 0.05), (slam + 0.1, 0.0)], ease_in)
    rig = _tug_rig(t, c, freeze_t=c["J1"])
    sh = _shake(t, slam, 0.25, 9)
    # Emb's and Imp's eyes follow him out
    e_look = (-1.0, 0.0) if u > 0.1 else (0.6, 0.4)
    imp_l = (-0.9, -0.1) if u > 0.25 else None

    def tired(tx_, ty_):
        return draw_person(ctx, "tired", tx_, ty_, S, t, pose="scream_run", pose_t=u, turn=-1.1,
                           expr=SCREAM_SHUT, mouth=info.mouth("tired", t), headphones=HP)

    with core.camera(ctx, 690 + sh[0], 1050 + sh[1], 0.86):
        if in_door:
            _room(ctx, t, layer="back", door=door)
            if not gone:
                tired(tx, ty)
            _room(ctx, t, layer="room", door=door)
        else:
            _room(ctx, t, door=door)
        _draw_tug(ctx, t, c, info, rig, rattle=0.0, cage_door=0.78, latch="open", inside="empty",
                  emb_expr="terrified", emb_look=e_look, wig=0.0, imp_look=(imp_l, None))
        creatures.draw_thing(ctx, 840, TIR_PEER[1] - 10, THING_S, t, state="sit",
                             look=(-0.7, -0.2) if u > 0.2 else (0.3, -0.5))
        if not in_door:
            tired(tx, ty)
            fx.motion_lines(ctx, tx + 90, ty - 360, 0.0, 220, t, 1.0)
        if t >= slam:
            fx.dust_puff(ctx, 330, 1335, 0.8, t, slam, dur=0.5)
            fx.impact_star(ctx, 470, 900, 0.5, t, slam, dur=0.3, word="SLAM!")


# ----------------------------------------------------------------------------
# L — his window: running across the lawn (muffled)
# ----------------------------------------------------------------------------
def shot_window(ctx, t, info, c):
    t0 = c["K1"]
    u = t - t0
    s2 = 0.3
    v = abs(cycle_speed("tired", "scream_run", 1.0)) * s2
    x = 150 + v * u
    y = 1452
    with core.camera(ctx, 540 + 40 * seg(u, 0, 1.4), 1180, 1.12):
        sets.street_view(ctx, t, bird=False)
        ctx.save()
        ctx.rectangle(198, 0, 905 - 198, 1528)
        ctx.clip()
        draw_person(ctx, "tired", x, y, s2, t, pose="scream_run", pose_t=u, turn=1.0,
                    expr=SCREAM_SHUT, mouth=info.mouth("tired", t), headphones=HP)
        ctx.restore()


# ----------------------------------------------------------------------------
# M — catch;  N — stare, facepalm
# ----------------------------------------------------------------------------
CAGE_FLOOR = (690.0, TUG_Y - 278 * CAGE_S + 4)


def shot_catch(ctx, t, info, c):
    m = c["catch"]
    u = t - m
    ex = tween(u, [(0.1, 960.0), (0.4, 880.0)], ease_out)
    pose = state_at(u, [(-1, P_CROUCH_READY), (0.1, P_DIVE), (0.36, P_GRAB), (0.62, P_STUFF),
                        (0.88, P_SHUT), (1.15, P_KNEEL)], 0.12)
    lift = 60 * math.sin(math.pi * seg(u, 0.1, 0.4))
    expr = state_at(u, [(-1, "determined"), (0.36, "panic"), (0.88, "determined"),
                        (1.15, "relieved")], 0.12)
    look = tween(u, [(0.0, (-0.6, 0.6)), (0.36, (-0.4, 0.8)), (0.62, (-0.8, 0.6)), (1.2, (-0.8, 0.5))])
    door = tween(u, [(0.82, 0.72), (0.92, 0.0)], ease_in)
    latch = "open" if u < 1.02 else "closed"
    ax, ay = CAGE_FLOOR
    st = {}
    thing_x = tween(u, [(0.0, 830.0), (0.2, 790.0)])

    def hold_fn(cx_, side, x, y, ang):
        if 0.36 <= u < 0.74:
            creatures.draw_thing(cx_, x, y + 10, THING_S, t, state="struggle")
        st["h"] = (x, y)

    inside = "bundle" if u < 0.74 else "thing"
    sh = _shake(t, m + 0.92, 0.2, 6)
    with core.camera(ctx, 690 + sh[0], 1100 + sh[1], 1.05):
        _room(ctx, t, door=0.0)
        creatures.draw_impulsivity(ctx, IMP_X - 30, TUG_Y, IMP_S, t, pose="sit", pant=1.0)
        _cage(ctx, ax, ay, t, door=door, latch=latch, rattle=0.4 * seg(u, 0.74, 0.8) * (1 - seg(u, 1.0, 1.3)),
              inside=_inside(inside, t, wig=0.2, look=(0.6, -0.2)))
        if u < 0.36:
            creatures.draw_thing(ctx, thing_x, TUG_Y + 4, THING_S, t,
                                 state="sit" if u < 0.12 else "hiss", look=(0.8, -0.3))
        a = draw_person(ctx, "embar", ex, TUG_Y, S, t, pose=pose, turn=-0.8, expr=expr, look=look,
                        blush=0.55, sweat=0.8,
                        mouth=info.mouth("embar", t), hold=hold_fn, pose_t=u)
        if 0.74 <= u < 0.82 and "h" in st:
            k = seg(u, 0.74, 0.82)
            ix, iy = _cage_pt(ax, ay, 0.0, 0, 200)
            creatures.draw_thing(ctx, lerp(st["h"][0], ix, k), lerp(st["h"][1], iy, k), THING_S * (1 - 0.3 * k),
                                 t, state="struggle")
        if u >= 1.02:
            lx, ly = _cage_pt(ax, ay, 0.0, 130, 158)
            fx.tap_marks(ctx, lx + 10, ly, 0.6, t, m + 1.02, taps=1, angle=0.0, label="click")
        if 0.1 <= u < 0.45:
            fx.motion_lines(ctx, ex + 120, TUG_Y - 300, math.pi, 200, t, 1.0)


def shot_stare(ctx, t, info, c):
    s0 = c["stare"]
    u = t - s0
    t4 = c["l04"]
    ax, ay = CAGE_FLOOR
    ex = 880.0
    pose = state_at(t, [(-1, P_KNEEL), (t4 - 0.12, P_FACEPALM)], 0.28)
    # his face slowly falls: relieved -> blank -> dread
    face = _fk(u, [(-1, {"curve": 0.25}), (0.35, {"curve": 0.05, "lid": -0.05}),
                   (0.9, {"curve": -0.25, "brow_ang": 0.45, "brow": 0.25, "pupil": -0.25, "lid": -0.08,
                          "press": 0.3}),
                   (1.5, {"curve": -0.42, "brow_ang": 0.7, "brow": 0.35, "pupil": -0.35, "lid": -0.1,
                          "frown": 0.4, "press": 0.15})], 0.5)
    expr = state_at(u, [(-1, "relieved"), (0.35, "neutral"), (t4 - s0, "sad")], 0.4)
    look = (-0.9, -0.15) if t < t4 else (-0.3, 0.5)
    blush = tween(u, [(0, 0.45), (1.6, 0.15)])
    # Impulsivity: frozen grin; one eye slowly slides onto Emb
    ll = tween(u, [(0.3, creatures.IMP_DERP_L), (1.9, (0.85, 0.1))])
    z = 1.08 + 0.42 * ease_in_out(seg(u, 0, info.dur - s0))
    cx = 690 - 10 * seg(u, 0, 3)
    with core.camera(ctx, cx, 1150, z):
        _room(ctx, t, door=0.0)
        creatures.draw_impulsivity(ctx, IMP_X - 30, TUG_Y, IMP_S, t, pose="sit", pant=1.0, look_l=ll)
        _cage(ctx, ax, ay, t, door=0.0, latch="closed", inside=_inside("thing", t, look=(0.7, -0.3)))
        draw_person(ctx, "embar", ex, TUG_Y, S, t, pose=pose, turn=-0.8, expr=expr, look=look,
                    face=face, blush=blush, sweat=0.6, mouth=info.mouth("embar", t))


# ----------------------------------------------------------------------------
SHOTS = [("A1", shot_scoop), ("B1", shot_latch), ("C1", shot_back), ("open", shot_tired),
         ("tug", shot_door), ("squint", shot_tug), ("G1", shot_squint), ("creak", shot_eyes),
         ("l03", shot_creak), ("J1", shot_scream), ("K1", shot_runout), ("catch", shot_window),
         ("stare", shot_catch), ("end", shot_stare)]


def render(ctx, t, info):
    c = _cues(info)
    for key, fn in SHOTS:
        if t < c[key]:
            fn(ctx, t, info, c)
            return
    SHOTS[-1][1](ctx, t, info, c)


def SFX(info):
    c = _cues(info)
    return []
