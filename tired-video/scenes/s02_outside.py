"""s02 - outside: Embarrassment lost the thing.

Shot list (all times derived from the timeline; see _T):
  A  side wall      Emb splatted in the dent (he caused s01's rumble), peels off, drops,
                    staggers dazed. Name tag EMBARRASSMENT. First "Oh God."
  B  MCU            he lifts the open EMPTY cage and stares into it ("Oh God, oh God"),
                    beat, then eyes slide up: "My boss is gonna be so mad." (blush/sweat up)
  C  medium         "I have to find this thing!" run_panic in place, frantic looks.
                    scurry: the violet blur zips past his feet; glance, dismiss, DOUBLE TAKE
                    (head snaps first, body follows), wind-up -> whip pan right.
  D1 door insert    the blur zips along the porch, flattens and slips under the door gap.
  D2 tracking run   "No no no, not in there!" he sprints across the lawn, cage flailing.
  E  porch          skid into the door, bang_door (door_bang every hit), "Tiredness!
                    Open up! It's me!" - on "me!" his eyes go up toward the bedroom.
  F  bedroom        Tiredness, headphones on, gaming and bopping, scratches his nose.
                    The bangs are faint and muffled. Notes leak from the cups.
  G  porch close    forehead on the door, he slides down it: "...He can't hear me."
"""
import math

import cairocffi as cairo

from audio import sfx
from engine import core, fx, human, props, sets
from engine.core import (
    clamp,
    ease_in,
    ease_in_out,
    ease_out,
    ease_out_back,
    lerp,
    seg,
    smoothstep,
    state_at,
    tween,
)
from engine.creatures import draw_thing
from engine.human import draw_person, ground_from_seat

HM = sets.HOUSE_MARKS
BM = sets.BEDROOM_MARKS
SH = 0.45                      # people scale in the house set
SB = 0.75                      # people scale in the bedroom
CAGE_S = 0.45

# where things stand (world px, house set)
SIDE_X, SIDE_Y = HM["side_feet"]          # (330, 1560) on the side lawn
DENT_X, DENT_Y = HM["dent"]               # (330, 1200)
SPLAT_FEET = DENT_Y + 230                 # feet line while stuck in the dent
PORCH_Y = HM["porch_feet_y"]              # 1452
DOOR_X, DOOR_TOP, DOOR_W, DOOR_H = HM["door"]
GAP_X, GAP_Y, GAP_W, GAP_H = HM["door_gap"]
BANG_X = DOOR_X - 32                      # Emb's feet when pounding (door on his right)
KNEEL_X = DOOR_X - 50                     # feet while leaning his forehead on the door
CAGE_DROP = (DOOR_X - 88, PORCH_Y - 278 * CAGE_S)   # where the cage lands on the porch

# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------


def _ws(info, lid, i):
    """Scene time of word i of line lid (from the lip-sync data; proportional fallback)."""
    ln = info.line(lid)
    ws = (getattr(info, "_lip", {}) or {}).get(lid, {}).get("word_starts") or []
    if 0 <= i < len(ws):
        return ln.start + ws[i]
    n = max(1, len(ln.text.split()))
    return ln.start + ln.dur * min(i, n) / n


def _T(info):
    c = info.cue
    T = {"dur": info.dur}
    for i in range(1, 6):
        T[f"l{i}"] = c(f"s02_l0{i}")
        T[f"l{i}e"] = c(f"s02_l0{i}.end")
    T["peel"] = c("peel")
    pd = T["l1"] - T["peel"]
    T["unstick"] = T["peel"] + min(0.45, 0.42 * pd)      # left arm pops off the wall
    T["unstick2"] = T["unstick"] + 0.17                    # right arm (with the cage)
    T["drop"] = T["unstick2"] + 0.17                       # the rest lets go
    T["land"] = T["drop"] + 0.2                            # feet hit the lawn
    T["wake"] = T["l1"] + 0.05                             # snaps out of the daze
    T["B"] = _ws(info, "s02_l01", 2)                       # 2nd "Oh" -> MCU
    T["shake"] = _ws(info, "s02_l01", 4)                   # 3rd "oh": shakes the cage
    T["boss"] = _ws(info, "s02_l02", 1)
    T["mad"] = _ws(info, "s02_l02", 6)
    T["C"] = _ws(info, "s02_l02", 7)                       # "I have to find this thing!"
    T["scurry"] = c("scurry")
    T["glance"] = T["scurry"] + 0.25                       # as it passes his feet
    T["away"] = T["glance"] + 0.18
    T["snap"] = T["away"] + 0.2
    T["body"] = T["snap"] + 0.14
    T["whip"] = min(T["body"] + 0.38, T["l3"] - 0.5)      # hold the take ~0.5 s
    T["D1"] = T["whip"] + 0.16                             # whip mid = the cut
    T["under"] = T["D1"] + 0.04                            # thing arrives on the porch
    T["D2"] = max(T["D1"] + 0.55, _ws(info, "s02_l03", 2))
    T["E"] = T["l3e"]
    T["bang"] = c("bang")
    T["me"] = _ws(info, "s02_l04", 4)
    T["F"] = c("inside")
    T["G"] = T["l5"] - 0.25
    T["scratch"] = T["F"] + 0.42
    # bang cycle: hits every 0.5 s starting exactly on the bang cue
    T["bang_t0"] = T["bang"] - 0.375
    T["last_hit"] = T["F"] + 1.1
    return T


def _hits(T):
    out, k = [], 0
    while True:
        h = T["bang"] + 0.5 * k
        if h > T["last_hit"]:
            return out
        out.append(h)
        k += 1


def _shot(t, T):
    for name in ("G", "F", "E", "D2", "D1", "C", "B"):
        if t >= T[name]:
            return name
    return "A"


# ---------------------------------------------------------------------------
# little helpers
# ---------------------------------------------------------------------------


def _osc(t, events, freq=1.7, damp=3.2):
    """Sum of damped sine kicks [(t0, amp), ...]."""
    v = 0.0
    for t0, a in events:
        if t >= t0:
            d = t - t0
            v += a * math.exp(-d * damp) * math.sin(2 * math.pi * freq * d)
    return v


class _askew:
    """Scoped wrapper: tilts Embarrassment's glasses (the rig has no 'glasses askew' input).
    Restores the rig's own function on exit, so other scenes are untouched."""

    def __init__(self, amount):
        self.k = amount
        self.orig = None

    def __enter__(self):
        if abs(self.k) < 0.01:
            return self
        self.orig = human._draw_glasses
        orig, k = self.orig, self.k

        def wrapped(ctx, C, hg, st, inkw, t):
            xl, yl = st["E_l"][0], st["E_l"][1]
            xr, yr = st["E_r"][0], st["E_r"][1]
            cx, cy = (xl + xr) / 2, (yl + yr) / 2
            ctx.save()
            ctx.translate(cx + 6 * k, cy + 9 * k)
            ctx.rotate(0.2 * k)
            ctx.translate(-cx, -cy)
            orig(ctx, C, hg, st, inkw, t)
            ctx.restore()
        human._draw_glasses = wrapped
        return self

    def __exit__(self, *a):
        if self.orig is not None:
            human._draw_glasses = self.orig


def _embar(ctx, x, y, s, t, askew=0.0, **kw):
    with _askew(askew):
        return draw_person(ctx, "embar", x, y, s, t, **kw)


def _cage_cb(t, door, rot=0.0, dy=0.0, rattle=0.0):
    def cb(ctx, side, x, y, ang):
        props.cage(ctx, x, y + dy * CAGE_S, CAGE_S, t, door=door, latch="open", rattle=rattle,
                   rot=rot, empty=True)
    return cb


def _cage_door(t, T):
    """The open cage door keeps swinging from every jolt."""
    ev = [(T["unstick2"], 0.3), (T["land"], 0.45), (T["shake"], 0.35), (T["C"], 0.3),
          (T["snap"], 0.4), (T["D2"], 0.3), (T["bang"] - 0.05, 0.35)]
    v = 0.66 + _osc(t, ev, 1.5, 2.6)
    if T["C"] <= t < T["snap"]:
        v += 0.12 * math.sin(2 * math.pi * t / 0.22)
    return clamp(v, 0.12, 1.0)


def _cam_shake(t, t0, dur=0.25, amp=6.0, seed=3):
    return core.shake(t, t0, dur, amp, seed)


# ---------------------------------------------------------------------------
# poses
# ---------------------------------------------------------------------------

SPLAT = {"base": "stand", "al_p": 0.12, "al_o": 1.85, "al_e": 0.45, "al_eo": 0.3, "al_h": "splay",
         "ar_p": 0.12, "ar_o": 1.85, "ar_e": 0.45, "ar_eo": 0.3, "ar_h": "grip",
         "ll_o": 0.34, "lr_o": 0.34, "ll_k": 0.1, "lr_k": 0.1, "sway": 0.0, "breath": 0.2,
         "posture": 0.0, "hunch": 0.25, "hold": 1}
# the left arm has popped off the wall and dangles
SPLAT_L = dict(SPLAT, al_p=0.02, al_o=0.22, al_e=0.25, al_eo=0.0, al_h="relaxed", side=0.04)
# both arms off, still stuck by the back and legs
SPLAT_LR = dict(SPLAT_L, ar_p=0.05, ar_o=0.3, ar_e=0.2, ar_eo=0.0, hunch=0.5, nod=0.12)
FALL = {"base": "stand", "al_p": 0.6, "al_o": 2.2, "al_e": 0.9, "al_h": "splay",
        "ar_p": 0.5, "ar_o": 1.6, "ar_e": 0.7, "ar_h": "grip", "ll_p": 0.3, "lr_p": -0.1,
        "ll_k": 0.5, "lr_k": 0.3, "ll_o": 0.18, "lr_o": 0.2, "lean": 0.12, "sway": 0.0, "hold": 1}
SQUAT = {"base": "stand", "ll_p": 0.75, "lr_p": 0.7, "ll_k": 1.35, "lr_k": 1.3, "ll_o": 0.25,
         "lr_o": 0.25, "ll_a": -0.2, "lr_a": -0.2, "lean": 0.35, "al_p": 0.4, "al_o": 0.6,
         "al_e": 0.6, "al_h": "splay", "ar_p": 0.3, "ar_o": 0.35, "ar_e": 0.3, "ar_h": "grip",
         "hunch": 0.6, "nod": 0.1, "sway": 0.0, "hold": 1}
HOLD_R = {"base": "hold_side", "al_p": 0.1, "al_o": 0.25, "al_e": 0.35, "al_h": "relaxed",
          "hunch": 0.5}
# both hands lift the cage to his chest to peer in
PEER = {"base": "stand", "ar_ik": 1.0, "ar_tx": 0.15, "ar_ty": 0.66, "ar_tz": 0.2, "ar_h": "grip",
        "ar_wa": 0.0, "ar_wabs": 0.3, "hold": 1,
        "al_ik": 1.0, "al_th": 1.0, "al_hx": 66, "al_hy": 96, "al_h": "relaxed", "al_layer": "front",
        "al_wa": -1.9, "al_wabs": 0.7, "al_bend": 1.0,
        "nod": 0.14, "neck": 0.14, "hunch": 0.7, "lean": 0.03, "side": 0.03}
RUN_IN_PLACE = {"base": "run_panic", "hold": 1, "ar_h": "grip"}
STAND_CAGE = {"base": "hold_side", "al_p": 0.25, "al_o": 0.45, "al_e": 0.9, "al_h": "splay",
              "hunch": 0.7}
# the take: arms jerk up, chin back
TAKE = {"base": "hold_side", "al_p": 0.4, "al_o": 0.9, "al_e": 1.2, "al_h": "splay", "hunch": 0.9,
        "lean": -0.12, "nod": -0.1, "lift": 14.0}
WINDUP = {"base": "hold_side", "lean": -0.22, "hunch": 0.8, "ll_p": 0.4, "ll_k": 0.7,
          "lr_p": -0.15, "lr_k": 0.45, "al_p": 1.25, "al_o": 0.5, "al_e": 0.8, "al_h": "splay",
          "ar_p": -0.35, "ar_o": 0.2}
RUN_CAGE = {"base": "run_panic", "hold": 1, "ar_h": "grip"}
SKID = {"base": "stand", "lean": -0.55, "chest": -0.15, "rot": -0.12,
        "ll_p": 0.75, "ll_k": 0.05, "ll_a": 0.5, "lr_p": -0.1, "lr_k": 0.7,
        "al_p": 1.6, "al_o": 1.2, "al_e": 0.5, "al_h": "splay",
        "ar_p": -0.7, "ar_o": 0.3, "ar_e": 0.3, "ar_h": "grip", "ar_layer": "back",
        "hunch": 0.7, "sway": 0.0, "hold": 1}
BANG = "bang_door"
# on "It's me!": he leans back and looks up at the bedroom window
LOOK_UP = {"base": "bang_door", "lean": -0.14, "chest": -0.12, "nod": -0.32, "neck": -0.2}
# forehead against the door, palms flat either side
HEAD_ON = {"base": "stand", "lean": 0.3, "neck": 0.38, "nod": 0.3, "hunch": 0.45,
           "al_p": 0.12, "al_o": 0.08, "al_e": 0.15, "al_h": "relaxed",
           "ar_p": 0.12, "ar_o": 0.08, "ar_e": 0.15, "ar_h": "relaxed", "sway": 0.0, "breath": 0.6}
KNEEL = {"base": "stand", "plant": 0.0, "hip_h": 0.52, "lean": 0.35, "neck": 0.35, "nod": 0.34,
         "hunch": 0.95, "ll_p": 0.1, "ll_k": 1.6, "ll_a": 0.6, "lr_p": -0.05, "lr_k": 1.65,
         "lr_a": 0.6,
         "al_p": 0.3, "al_o": 0.12, "al_e": 0.2, "al_h": "relaxed",
         "ar_p": 0.3, "ar_o": 0.1, "ar_e": 0.2, "ar_h": "relaxed", "sway": 0.0, "breath": 0.6}


# ---------------------------------------------------------------------------
# the house set
# ---------------------------------------------------------------------------


def _house_bg(ctx, t):
    sets.house_exterior(ctx, t, "bg", dent=1.0)


def _house_fg(ctx, t):
    sets.house_exterior(ctx, t, "fg", dent=1.0, parts=("fence",))


# ---------------------------------------------------------------------------
# Shot A: splat, peel, drop, stagger
# ---------------------------------------------------------------------------


def _shot_A(ctx, t, info, T):
    cam = (DENT_X, 1250, 1.7)
    dx, dy = _cam_shake(t, T["land"], 0.22, 5.0)
    with core.camera(ctx, cam[0] - dx / cam[2], cam[1] - dy / cam[2], cam[2]):
        _house_bg(ctx, t)
        _emb_A(ctx, t, info, T)
        _house_fg(ctx, t)
    # dizzy stars + name tag are screen-space-ish; stars are drawn in _emb_A


def _emb_A(ctx, t, info, T):
    us, us2, dr, ld = T["unstick"], T["unstick2"], T["drop"], T["land"]
    quiver = 0.012 * math.sin(t * 38) * (1 - seg(t, us - 0.1, us))
    cage_rot = 0.0
    if t < dr:
        # sticky peel: left arm pops off, then the right (cage swings down), then he slides
        k1 = ease_out_back(seg(t, us, us + 0.14), 2.4)
        k2 = ease_out_back(seg(t, us2, us2 + 0.14), 2.4)
        pose = ((SPLAT, SPLAT_L, k1), SPLAT_LR, k2)
        y = SPLAT_FEET + 22 * ease_in(seg(t, us2, dr))
        x = SIDE_X
        expr = "dazed"
        flat = 1 - seg(t, us2, dr)
        sx, sy = 1.0 + 0.07 * flat, 0.98 + 0.02 * (1 - flat)
        rot = quiver + 0.03 * k1 - 0.02 * k2
        shadow = False
        cage_rot = 0.35 * _osc(t, [(us2, 1.0)], 1.6, 2.5)
    elif t < ld:
        k = ease_in(seg(t, dr, ld))
        pose = (SPLAT_LR, FALL, smoothstep(seg(t, dr, dr + 0.1)))
        y = lerp(SPLAT_FEET + 22, SIDE_Y, k)
        x = SIDE_X + 8 * k
        expr = "dazed"
        sx, sy = 1.0, 1.0 + 0.05 * k          # stretch as he falls
        rot = 0.0
        shadow = True
        cage_rot = -0.3 * k
    else:
        # landing squash, then dazed stagger (stumble at turn 0 travels nowhere)
        dl = t - ld
        sq = 0.13 * math.exp(-dl * 9) * math.cos(dl * 22)
        sx, sy = 1 + sq * 0.7, 1 - sq
        x, y = SIDE_X + 8, SIDE_Y
        kq = smoothstep(seg(t, ld, ld + 0.2))
        ks = smoothstep(seg(t, ld + 0.15, ld + 0.45))
        if t < ld + 0.2:
            pose = (FALL, SQUAT, kq)
        elif t < T["wake"]:
            pose = (SQUAT, "stumble", ks)
        else:
            pose = ("stumble", HOLD_R, smoothstep(seg(t, T["wake"], T["wake"] + 0.3)))
        pose = _with_hold(pose)
        expr = state_at(t, [(0, "dazed"), (T["wake"] + 0.08, "panic")], 0.18)
        rot = 0.0
        shadow = True
        cage_rot = 0.3 * math.exp(-dl * 3) * math.sin(dl * 9)
    wake = smoothstep(seg(t, T["wake"], T["wake"] + 0.2))
    face = {"head_tilt": 0.08 * math.sin(t * 5.2) * (1 - wake), "lid_r": 0.1 * (1 - wake)}
    if t >= T["wake"]:
        # "Oh God." - eyes snap to the cage in his hand
        face.update({"pupil": -0.2 * wake, "brow_ang": 0.2 * wake, "head_nod": 0.1 * wake})
    look = (0, 0) if t < T["wake"] else tween(t, [(T["wake"], (0, 0)), (T["wake"] + 0.15, (0.7, 0.8))])
    # blink hard on waking (shake it off)
    blink = None
    if T["wake"] - 0.05 <= t < T["wake"] + 0.18:
        blink = math.sin(math.pi * seg(t, T["wake"] - 0.05, T["wake"] + 0.18))
    with core.saved(ctx, x, y, (sx, sy), rot):
        a = _embar(ctx, 0, 0, SH, t, askew=0.9, pose=pose, expr=expr, look=look,
                   mouth=info.mouth("embar", t), face=face, blush=0.15 + 0.1 * wake,
                   sweat=0.3 * wake, blink=blink, shadow=shadow, pose_t=t - ld,
                   hold=_cage_cb(t, _cage_door(t, T), cage_rot))
    hx, hy = x + a["top"][0] * sx, y + a["top"][1] * sy
    # dizzy stars while dazed
    st_t0, st_t1 = 0.12, T["wake"] + 0.1
    if t < st_t1 + 0.3:
        fx.dizzy_stars(ctx, hx, hy + 8, 0.45, t, t0=st_t0, dur=st_t1 - st_t0, layer="both")
    # little "pop" ticks where each arm unsticks
    for (tt, side) in ((us, -1), (us2, 1)):
        if tt <= t < tt + 0.35:
            fx.tap_marks(ctx, x + side * 175, SPLAT_FEET - 360, 0.45, t, tt, taps=1,
                         angle=-math.pi / 2 - side * 0.6, label=None)
    if t >= ld:
        fx.dust_puff(ctx, x, SIDE_Y + 4, 0.5, t, ld, seed=2)


def _with_hold(pose):
    """Make sure the hold flag survives a blend (the cage stays in the right hand)."""
    a, b, k = pose
    def h(p):
        if isinstance(p, dict):
            d = dict(p); d["hold"] = 1; return d
        return {"base": p, "hold": 1}
    return (h(a), h(b), k)


# ---------------------------------------------------------------------------
# Shot B: MCU - into the empty cage, then the boss dread
# ---------------------------------------------------------------------------


def _shot_B(ctx, t, info, T):
    p = seg(t, T["B"], T["C"])
    z = lerp(3.0, 3.25, ease_in_out(p))
    cam = (SIDE_X + 26, lerp(1262, 1250, p), z)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        _emb_B(ctx, t, info, T)


def _emb_B(ctx, t, info, T):
    t0 = T["B"]
    k_up = ease_out_back(seg(t, t0 - 0.12, t0 + 0.22))
    pose = (HOLD_R, PEER, k_up)
    boss = T["boss"]
    up = smoothstep(seg(t, boss - 0.05, boss + 0.18))       # pupils leave the cage
    head = smoothstep(seg(t, boss + 0.1, boss + 0.35))      # head follows ~0.15 s later
    mad = T["mad"]
    shud = math.exp(-max(0.0, t - mad) * 7) * math.sin((t - mad) * 40) if t >= mad else 0.0
    # cage shake on the 3rd "oh"
    sh = seg(t, T["shake"], T["shake"] + 0.35)
    rattle = math.sin(math.pi * sh) if 0 < sh < 1 else 0.0
    look_in = (0.55, 0.95)
    look_boss = (0.6, -0.8)
    look = tween(t, [(boss - 0.05, look_in), (boss + 0.16, look_boss)])
    # tiny eye darts while staring into the cage (he's checking every corner)
    if t < boss - 0.05:
        dart = core.noise1(t * 3.2, 11)
        look = (look[0] + 0.3 * dart, look[1])
    expr = state_at(t, [(0, "panic"), (T["l1e"] + 0.05, "alarmed"), (boss + 0.05, "terrified")], 0.25)
    face = {"head_nod": 0.16 * (1 - head) - 0.1 * head, "head_turn": 0.2 * (1 - head) + 0.1 * head,
            "head_tilt": 0.08 * (1 - head) + 0.02 * head + 0.04 * shud, "pupil": -0.12 - 0.25 * up,
            "press": 0.5 * seg(t, T["l1e"], T["l1e"] + 0.15) * (1 - up),
            "squash": 0.05 * shud, "brow_ang": 0.15}
    blush = 0.2 + 0.12 * up
    sweat = 0.35 + 0.4 * up
    glint = math.sin(math.pi * seg(t, boss + 0.05, boss + 0.3))
    door = _cage_door(t, T)
    # hands at the cage sides: lift the cage so its middle sits in his grip
    _embar(ctx, SIDE_X, SIDE_Y, SH, t, askew=0.75, pose=pose, expr=expr, look=look,
           mouth=info.mouth("embar", t), face=face, blush=blush, sweat=sweat, glint=glint,
           hold=_cage_cb(t, door, 0.0, rattle=rattle * 0.7))


# ---------------------------------------------------------------------------
# Shot C: run in place, scurry, double take, whip
# ---------------------------------------------------------------------------
C_CAM = (SIDE_X + 40, 1340, 1.9)
D1_CAM = (GAP_X + 90, 1300, 2.2)


def _whip_cam(t, T):
    t0 = T["whip"]
    p = seg(t, t0, t0 + 0.32)
    k = ease_in_out(p)
    c0 = _c_cam(t0, T)
    return (lerp(c0[0], D1_CAM[0], k), lerp(c0[1], D1_CAM[1], k), lerp(c0[2], D1_CAM[2], k))


def _thing_C(t, T):
    """The violet blur's path through shot C: (x, y, visible)."""
    t0 = T["scurry"]
    x = -60 + 1700 * (t - t0)
    return x, SIDE_Y + 30


def _c_cam(t, T):
    k = ease_out(seg(t, T["snap"], T["snap"] + 0.12))
    return (lerp(C_CAM[0], SIDE_X + 20, k), lerp(C_CAM[1], 1270, k), lerp(C_CAM[2], 2.35, k))


def _shot_C(ctx, t, info, T):
    cam = _whip_cam(t, T) if t >= T["whip"] else _c_cam(t, T)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        if T["scurry"] <= t < T["scurry"] + 0.6:
            x, y = _thing_C(t, T)
            fx.motion_lines(ctx, x - 40, y - 16, 0.0, 170, t, 1.0, seed=4, width=9)
            draw_thing(ctx, x, y, 0.5, t, "scurry", motion=1.0)
        _emb_C(ctx, t, info, T)
        _house_fg(ctx, t)


def _emb_C(ctx, t, info, T):
    t0, sn, bd = T["C"], T["snap"], T["body"]
    stop = smoothstep(seg(t, sn - 0.02, sn + 0.1))
    if t < sn:
        pose = (STAND_CAGE, RUN_IN_PLACE, smoothstep(seg(t, t0, t0 + 0.15)))
    elif t < bd + 0.06:
        pose = (RUN_IN_PLACE, TAKE, stop)
    else:
        pose = (TAKE, WINDUP, ease_in_out(seg(t, bd + 0.1, T["whip"] + 0.04)))
    pose = _with_hold(pose)
    turn = lerp(0.0, 1.0, ease_out_back(seg(t, bd, bd + 0.18), 2.2))
    # frantic look-around (pupils lead, head follows 0.12 s later)
    keys = [(t0, (0.0, 0.0)), (t0 + 0.1, (-1.0, -0.2)), (t0 + 0.4, (-1.0, -0.2)),
            (t0 + 0.52, (1.0, -0.25)), (t0 + 0.82, (1.0, -0.25)), (t0 + 0.94, (-0.95, 0.1)),
            (t0 + 1.22, (-0.95, 0.1)), (t0 + 1.34, (0.7, -0.55)), (T["scurry"] - 0.12, (0.7, -0.55)),
            (T["scurry"], (-0.95, -0.4))]
    lk = tween(t, keys)
    hk = tween(t - 0.12, keys)
    gl, aw = T["glance"], T["away"]
    if t >= gl:
        # glance down-right where it went ... dismiss ... SNAP
        g = smoothstep(seg(t, gl, gl + 0.06)) * (1 - smoothstep(seg(t, aw, aw + 0.08)))
        lk = (lerp(lk[0], 0.95, g), lerp(lk[1], 0.7, g))
        hk = (lerp(hk[0], 0.1, g), 0.0)
    snapk = seg(t, sn, sn + 0.32)
    s1 = ease_out_back(seg(t, sn, sn + 0.1), 2.5)
    if t >= sn:
        lk = (lerp(lk[0], 1.0, min(1.0, s1)), lerp(lk[1], 0.2, min(1.0, s1)))
        hk = (lerp(hk[0], 1.0, s1), 0.0)
    bump = math.sin(math.pi * snapk) if 0 < snapk < 1 else 0.0
    expr = state_at(t, [(0, "panic"), (sn, "surprised"), (bd + 0.14, "alarmed")], 0.08)
    face = {"head_turn": hk[0] * 0.6 * (1 - smoothstep(seg(t, bd, bd + 0.2))),
            "head_tilt": -0.06 * hk[0], "squash": -0.16 * bump,
            "pupil": -0.25 - 0.3 * smoothstep(seg(t, sn, sn + 0.06)),
            "eye_size": 0.28 * bump, "brow": 0.3 * bump}
    askew = 0.75 * (1 - smoothstep(seg(t, sn, sn + 0.05)))   # the snap knocks them straight
    door = _cage_door(t, T)
    run_rot = 0.3 * math.sin(2 * math.pi * (t - t0) / 0.44) * (1 - stop) if t >= t0 else 0.0
    a = _embar(ctx, SIDE_X, SIDE_Y, SH, t, askew=askew, pose=pose, turn=turn, expr=expr, look=lk,
               mouth=info.mouth("embar", t), face=face, blush=0.32, sweat=0.7, pose_t=t - t0,
               hold=_cage_cb(t, door, run_rot + 0.25 * _osc(t, [(sn, 1.0)], 2.0, 3.0)))
    # sweat flicking off with the head whips
    for i, ts in enumerate((t0 + 0.5, t0 + 0.95, t0 + 1.4, sn)):
        side = 1 if i % 2 == 0 else -1
        fx.sweat_fly(ctx, a["head"][0] + 30 * side * SH, a["head"][1] - 10, 0.45, t, ts, seed=i + 3,
                     n=3, side=side)
    if t0 <= t < sn:
        # dust kicked up by the run on the spot
        ph = ((t - t0) / 0.44) % 1.0
        fx.dust_puff(ctx, SIDE_X, SIDE_Y + 4, 0.32, t, t - ph * 0.44, seed=int((t - t0) / 0.44) % 4,
                     dur=0.44)
    if sn <= t < sn + 0.6:
        fx.emote(ctx, "exclaim", a["top"][0] + 55, a["top"][1] - 20, 0.7, t, sn, dur=0.5)


# ---------------------------------------------------------------------------
# Shot D1: the blur slips under the door
# ---------------------------------------------------------------------------


def _shot_D1(ctx, t, info, T):
    cam = _whip_cam(t, T)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        _thing_D1(ctx, t, T)
        _house_fg(ctx, t)


def _thing_D1(ctx, t, T):
    t0 = T["under"] - 0.08
    ts = 0.6
    tx0, tx1 = 1290.0, GAP_X + GAP_W * 0.4
    run_d = 0.3
    if t < t0:
        return
    run = seg(t, t0, t0 + run_d)
    if run < 1:
        x = lerp(tx0, tx1, ease_out(run))
        y = PORCH_Y + 2
        fx.motion_lines(ctx, x - 40, y - 18, 0.0, 170, t, 1.0 - run * 0.5, seed=7, width=9)
        draw_thing(ctx, x, y, ts, t, "scurry", motion=1.0 - 0.45 * run)
        return
    # flatten and slide under the gap; the door hides whatever is past the threshold
    k = seg(t, t0 + run_d, t0 + run_d + 0.2)
    x = tx1 + 10 * k
    y = lerp(PORCH_Y + 2, GAP_Y + GAP_H + 2, ease_in(k))
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(-2000, -2000, 6000, 6000)
    ctx.rectangle(GAP_X - 8, DOOR_TOP, GAP_W + 16, GAP_Y + GAP_H - DOOR_TOP)
    ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    if k < 1:
        with core.saved(ctx, x, y, (1.0 + 0.5 * ease_out(k), 1.0 - 0.78 * ease_out(k))):
            draw_thing(ctx, 0, 0, ts, t, "scurry", motion=0.4 + 0.6 * k)
    # ...the tail is last: it lies on the threshold, flicks, and whips in under the door
    tk = seg(t, t0 + run_d + 0.12, t0 + run_d + 0.42)
    if 0 < tk < 1:
        L = 70 * (1 - ease_in(seg(tk, 0.45, 1.0)))
        if L > 2:
            bx, by = tx1 - 6, GAP_Y + GAP_H + 3
            fl = 10 * math.sin(tk * 18)
            ctx.move_to(bx, by)
            ctx.curve_to(bx - L * 0.4, by + 4, bx - L * 0.7, by + fl * 0.6, bx - L, by - 6 + fl)
            core.stroke(ctx, "ink", 9)
            ctx.move_to(bx, by)
            ctx.curve_to(bx - L * 0.4, by + 4, bx - L * 0.7, by + fl * 0.6, bx - L, by - 6 + fl)
            core.stroke(ctx, core.PAL["thing_dk"], 4.5)
    ctx.restore()


# ---------------------------------------------------------------------------
# Shot D2: the sprint
# ---------------------------------------------------------------------------


def _shot_D2(ctx, t, info, T):
    t0 = T["D2"]
    spd = human.cycle_speed("embar", "run_panic", 1.0) * SH
    x = 640 + spd * (t - t0)
    cam = (x + 150, 1330, 2.0)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        door = _cage_door(t, T)
        rot = 0.35 * math.sin(2 * math.pi * (t - t0) / 0.44 + 1.0)
        face = {"head_turn": 0.15, "pupil": -0.3, "brow_ang": 0.2}
        _embar(ctx, x, HM["lawn_feet_y"], SH, t, pose=RUN_CAGE, turn=1.0, expr="panic",
               look=(0.9, -0.1), mouth=info.mouth("embar", t), face=face, blush=0.38, sweat=0.8,
               pose_t=t - t0, hold=_cage_cb(t, door, rot))
        fx.motion_lines(ctx, x - 60, HM["lawn_feet_y"] - 250, 0.0, 260, t, 0.8, seed=12, width=10)
        _house_fg(ctx, t)


# ---------------------------------------------------------------------------
# Shot E: at the door, pounding
# ---------------------------------------------------------------------------


def _e_cam(t, T):
    p = seg(t, T["bang"], T["F"])
    z = lerp(2.4, 2.8, ease_in_out(p))
    return (lerp(1540, 1515, p), lerp(1230, 1180, p), z)


def _shot_E(ctx, t, info, T):
    cam = _e_cam(t, T)
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        _dropped_cage(ctx, t, T)
        _emb_door(ctx, t, info, T)
        _house_fg(ctx, t)


def _dropped_cage(ctx, t, T):
    """The cage he lets go of when he hits the door: falls from his trailing hand, bounces."""
    ta = T["bang"] - 0.02
    if t < ta:
        return
    d = t - ta
    x0, y0 = BANG_X - 58, PORCH_Y - 205
    x1, y1 = CAGE_DROP
    k = ease_in(seg(d, 0.0, 0.17))
    hop = 9 * math.sin(math.pi * seg(d, 0.17, 0.32))
    x = lerp(x0, x1, ease_out(seg(d, 0.0, 0.25)))
    y = lerp(y0, y1, k) - hop
    rot = lerp(0.45, 0.0, ease_out(seg(d, 0.0, 0.2))) + 0.12 * _osc(d, [(0.17, 1.0)], 3.0, 6.0)
    door = clamp(0.6 + 0.4 * _osc(d, [(0.17, 1.0), (0.32, 0.5)], 1.4, 2.2), 0.1, 1.0)
    props.cage(ctx, x, y, CAGE_S, t, door=door, latch="open", rot=rot, empty=True)


def _emb_door(ctx, t, info, T):
    t0, bang = T["E"], T["bang"]
    ta = bang - 0.02
    door = _cage_door(t, T)
    if t < ta:
        # skid in from the left, cage trailing behind
        k = ease_out(seg(t, t0, ta))
        x = lerp(1338, BANG_X, k)
        pose = _with_hold((RUN_CAGE, SKID, smoothstep(seg(t, t0 - 0.02, t0 + 0.13))))
        pose_t = t - t0
        hold = _cage_cb(t, door, 0.45)
    else:
        x = BANG_X
        lu = smoothstep(seg(t, T["me"] - 0.05, T["me"] + 0.2))
        pose = (BANG, LOOK_UP, lu)
        pose_t = t - T["bang_t0"]
        hold = None
    # slam squash on arrival
    dl = t - ta
    sq = 0.1 * math.exp(-dl * 10) * math.cos(dl * 25) if dl >= 0 else 0.0
    me = T["me"]
    up = smoothstep(seg(t, me - 0.02, me + 0.15))
    look = tween(t, [(ta, (0.9, 0.0)), (me - 0.02, (0.9, -0.05)), (me + 0.12, (-0.25, -1.2))])
    expr = state_at(t, [(0, "panic"), (T["l4"], "alarmed"), (me, "pleading")], 0.2)
    face = {"brow_ang": 0.25, "pupil": -0.2, "head_turn": 0.2 - 0.4 * up,
            "head_nod": -0.3 * up, "squash": sq, "lid": -0.1 * up, "brow": 0.3 * up}
    with core.saved(ctx, x, PORCH_Y, (1 + sq * 0.6, 1 - sq)):
        a = _embar(ctx, 0, 0, SH, t, pose=pose, turn=1.1, expr=expr, look=look,
                   mouth=info.mouth("embar", t), face=face, blush=0.42 + 0.1 * up, sweat=0.85,
                   pose_t=pose_t, hold=hold)
    # impact ticks on each hit
    fxp = (x + a["hand_r"][0] + 16, PORCH_Y + a["hand_r"][1])
    for i, h in enumerate(_hits(T)):
        if h <= t < h + 0.6 and h < T["F"]:
            fx.tap_marks(ctx, fxp[0], fxp[1], 0.5, t, h, taps=1, angle=0.0,
                         label="BANG!" if i % 2 == 0 else None)
    if t0 <= t < bang + 0.6:
        fx.dust_puff(ctx, x, PORCH_Y + 4, 0.4, t, bang - 0.08, seed=5, dur=0.6)


# ---------------------------------------------------------------------------
# Shot F: meanwhile, upstairs
# ---------------------------------------------------------------------------


def _shot_F(ctx, t, info, T):
    p = seg(t, T["F"], T["G"])
    cam = (lerp(1712, 1706, p), lerp(1070, 1062, p), lerp(1.95, 2.08, ease_in_out(p)))
    with core.camera(ctx, *cam):
        sets.bedroom(ctx, t, "bg", frame_fallen=True)
        _tired_F(ctx, t, info, T)
        sets.bedroom(ctx, t, "fg", frame_fallen=True, parts=("chair",))


def _tired_F(ctx, t, info, T):
    sx, sy = BM["chair_seat"]
    gy = ground_from_seat("tired", sy, SB)
    s0, s1 = T["scratch"], T["scratch"] + 0.75
    k = smoothstep(seg(t, s0, s0 + 0.16)) * (1 - smoothstep(seg(t, s1 - 0.16, s1)))
    rub = math.sin((t - s0) * 2 * math.pi * 5.0) if s0 <= t < s1 else 0.0
    bob = 0.07 * math.sin(2 * math.pi * 1.6 * (t - T["F"]))
    if k > 0.001:
        scratch = {"base": "game", "controller": 0.0, "ar_ik": 1.0, "ar_th": 1.0,
                   "ar_hx": 4 + 8 * rub, "ar_hy": 100 + 4 * rub, "ar_h": "point", "ar_layer": "front",
                   "ar_bend": 1.0, "ar_wa": -1.57, "ar_wabs": 0.9, "nod": -0.12 + bob}
        game = {"base": "game", "controller": 0.0, "nod": -0.16 + bob}
        pose = (game, scratch, k)
    else:
        pose = {"base": "game", "nod": -0.16 + bob}
    face = {"curve": 0.16, "lid": 0.04, "head_tilt": 0.04 * math.sin(2 * math.pi * 0.8 * t) - 0.04 * k,
            "flare": 0.5 * k, "lower": 0.18 * k, "lid_r": 0.06 * k, "asym": 0.2 * k}
    a = draw_person(ctx, "tired", sx, gy, SB, t, pose=pose, turn=0.4, expr="bored",
                    look=(0.6, -0.15), face=face, headphones="on", mouth=(0, 0))
    if k > 0.001:
        # controller held in the left hand only while the right one scratches
        hl = a["hand_l"]
        with core.saved(ctx, hl[0] + 38 * SB, hl[1] - 4, SB, -0.12):
            human._draw_controller(ctx, (-60, 0), (60, 0), human.INK_W, (0.0, 0.0), core.PAL["t_skin"])
    # music leaking from the cups (it's LOUD in there)
    hx, hy = a["head"]
    fx.music_notes(ctx, hx + 75 * SB, hy - 20, 0.85, t, 0.75, direction=1, seed=3)


# ---------------------------------------------------------------------------
# Shot G: slide down the door
# ---------------------------------------------------------------------------


def _shot_G(ctx, t, info, T):
    k = ease_in_out(seg(t, T["l5"] - 0.05, T["l5e"] + 0.15))
    cam = (lerp(1462, 1468, k), lerp(1150, 1225, k), lerp(3.15, 3.3, seg(t, T["G"], T["dur"])))
    with core.camera(ctx, *cam):
        _house_bg(ctx, t)
        props.cage(ctx, CAGE_DROP[0], CAGE_DROP[1], CAGE_S, t, door=0.62, latch="open", empty=True)
        _emb_G(ctx, t, info, T)
        _house_fg(ctx, t)


def _emb_G(ctx, t, info, T):
    sl0, sl1 = T["l5"] - 0.05, T["l5e"] + 0.15
    k = ease_in_out(seg(t, sl0, sl1))
    pose = (HEAD_ON, KNEEL, k)
    x = KNEEL_X + 4 * k
    # a little "bonk" as the forehead meets the door at the cut, then pressed
    d = t - T["G"]
    sq = 0.06 * math.exp(-d * 8) * math.cos(d * 20)
    expr = state_at(t, [(0, "sad"), (T["l5e"] + 0.1, "sigh")], 0.3)
    face = {"lid": 0.28 + 0.2 * k, "head_tilt": -0.1, "brow_ang": 0.25, "squash": 0.05 + sq,
            "look_y": 0.25, "frown": 0.2}
    # a long, deflating breath out at the end
    ex = smoothstep(seg(t, sl1, sl1 + 0.4))
    _embar(ctx, x, PORCH_Y + 6 * ex, SH, t, askew=-0.55, pose=pose, turn=1.3, expr=expr,
           look=(0.7, 0.45), mouth=info.mouth("embar", t), face=face, blush=0.3, sweat=0.35)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
_SHOTS = {"A": _shot_A, "B": _shot_B, "C": _shot_C, "D1": _shot_D1, "D2": _shot_D2, "E": _shot_E,
          "F": _shot_F, "G": _shot_G}


def render(ctx, t, info):
    T = _T(info)
    sh = _shot(t, T)
    with core.cache_steps(2):
        _SHOTS[sh](ctx, t, info, T)
    # screen-space overlays
    fx.name_tag(ctx, "EMBARRASSMENT", "junior lab scientist", t, 0.4, min(3.1, T["C"] - 0.4),
                x=90, y=170, color="embar")
    if T["whip"] <= t <= T["whip"] + 0.32:
        fx.whip_pan(ctx, t, T["whip"], 0.32, direction=1)


def SFX(info):
    T = _T(info)
    ev = []
    # A: sticky peel, drop, land
    ev.append((T["unstick"], "cloth_rustle", -4, -0.3))
    ev.append((T["unstick"], "pop", -14, -0.4))
    ev.append((T["unstick2"], "pop", -13, -0.1))
    ev.append((T["land"], "body_thud", -5, -0.3))
    ev.append((T["land"] + 0.02, "cage_rattle", -9, -0.2))
    ev.append((T["land"] + 0.35, "footstep", -6, -0.3))
    ev.append((T["land"] + 0.75, "footstep", -7, -0.2))
    # B: shakes the empty cage
    ev.append((T["shake"], "cage_rattle", -5, -0.1))
    # C: running on the spot
    ev.append((T["C"] + 0.05, "footsteps_run", -7, -0.2))
    ev.append((T["C"] + 1.05, "footsteps_run", -8, -0.2))
    ev.append((T["scurry"] - 0.05, "scurry", 0, 0.0))
    ev.append((T["scurry"] + 0.12, "critter_squeak", -8, 0.4))
    ev.append((T["snap"], "whoosh", -12, 0.2))
    ev.append((T["whip"], "whoosh", -3, 0.3))
    # D1: under the door
    ev.append((T["under"] - 0.1, "scurry", -8, 0.3))
    ev.append((T["under"] + 0.26, "critter_squeak", -14, 0.2))
    # D2: sprint
    ev.append((T["D2"], "footsteps_run", -2, 0.1))
    # E: skid + slam + pounding
    ev.append((T["bang"] - 0.12, "footstep", -4, 0.2))
    for h in _hits(T):
        if h < T["F"]:
            ev.append((h, "door_bang", -1, 0.15))
        else:
            ev.append((h, "door_bang", -15, -0.5))      # through the house, upstairs
    # F: inside - game audio in the headphones
    ev.append((T["F"] + 0.05, "game_blips", -14, 0.3))
    ev += sfx.loop_events("game_music_leak", T["F"], T["G"], -4, 0.2)
    # G: slides down the door
    ev.append((T["l5"] - 0.02, "cloth_rustle", -6, 0.1))
    ev.append((T["l5e"] + 0.12, "body_thud", -14, 0.1))
    ev.append((T["bang"] + 0.15, "cage_rattle", -6, -0.1))      # the dropped cage lands
    return ev
