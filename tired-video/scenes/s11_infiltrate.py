"""s11 — infiltration ("The printer guy"). Music: tension.

Shot list (all times derived from cues / line ids; see _T):
  A  lobby       wide -> push to the counter two-shot. He walks in (beige polo,
                 lanyard, clipboard), stops. l01 "I'm here to fix the printer."
  B  l02         receptionist close-up, flat "Which printer?" (one brow, slow blink)
  C  l03         Tiredness close-up, flat "All of them." (tiny nod, lid drop)
  D  stare/l04   two-shot, deadpan mirror: held stare + SYNCHRONISED slow blink.
                 "...Godspeed." -> his tiny nod, turnstile beep
  E  walk        turnstiles green, he strolls behind the gates and behind the
                 Guard, who stretch-yawns, eyes shut, and then looks the wrong way
  F  lab         LAB 7 door slides open, he steps in; the wall screen blinks on,
                 his pupils go up to it, head follows
  G  screen      insert: SPECIMEN ZERO / ESCAPED / LAST SEEN: SEWER LINE 7
  H  terrarium   insert: critters exactly like the thing press on the glass,
                 "CARRIER / BITE TRANSFERS TRAITS"
  I  realize     close-up: eyes label -> bandage -> label, lids lift +15%
  J  lean/alarm  he steadies himself on the console; hand lands on the button.
                 Alarm: red wash + beacons. His pupils slide to his hand.
  K  l05         close-up in the red light: "Oh no." (flat)
  L  l06         LAB 7 door slams open, two guards burst in, lead guard points
  M  bolt        back on him: squash, then he zips off (motion lines, dust)
  N  chase       corridor (camera is outside the near window): flailing tired
                 run toward camera, guards behind
  O  window      he slams into the glass: splat, cracks, shatter + flash
  O2 fall        tower exterior: bursts out of the hole with shards, tumbling
  P  l07         falling medium against the dusk sky: deadpan to camera
  Q  powers      irises flash teal, aura, time slows, cat-twist to feet-first
  R  impact      POV: the city rushes up to the manhole, flash
  S  black       true black (fx.black) to the end; captions hidden
"""
import math

from engine import core, sets, props, fx
from engine.core import tween, seg, clamp, lerp, ease_out_back, ease_in_out, ease_out, ease_in, state_at
from engine.human import draw_person, cycle_speed
from engine.creatures import draw_thing
from audio import sfx as _sfx

LB = sets.LOBBY_MARKS
LA = sets.LAB_MARKS
TW = sets.TOWER_MARKS
OUT = "printer"

# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
_TC = {}


def _T(info):
    key = (id(info), info.dur)
    T = _TC.get(key)
    if T is not None:
        return T
    c = info.cue
    T = dict(
        lobby=c("lobby"),
        l01=c("s11_l01"), l01e=c("s11_l01.end"),
        l02=c("s11_l02"), l02e=c("s11_l02.end"),
        l03=c("s11_l03"), l03e=c("s11_l03.end"),
        stare=c("stare"),
        l04=c("s11_l04"), l04e=c("s11_l04.end"),
        walk=c("walk"), lab=c("lab"), screen=c("screen"), terr=c("terrarium"),
        realize=c("realize"), lean=c("lean"), alarm=c("alarm"),
        l05=c("s11_l05"), l05e=c("s11_l05.end"),
        l06=c("s11_l06"), l06e=c("s11_l06.end"),
        chase=c("chase"), window=c("window"), fall=c("fall"),
        l07=c("s11_l07"), l07e=c("s11_l07.end"),
        powers=c("powers"), impact=c("impact"), black=c("black"), end=info.dur,
    )
    # shot boundaries
    T["cutB"] = T["l02"] - 0.08
    T["cutC"] = T["l02e"] + 0.32
    T["cutD"] = T["stare"]
    T["beep"] = T["walk"] - 0.12
    T["cutE"] = T["walk"]
    T["cutF"] = T["lab"]
    T["cutG"] = T["screen"]
    T["cutH"] = T["terr"]
    T["cutI"] = T["realize"]
    T["cutJ"] = T["lean"]
    T["press"] = T["lean"] + 0.42
    T["cutK"] = T["l05"]
    T["cutL"] = T["l06"] - 0.06
    T["cutM"] = T["l06e"] - 0.28
    T["cutN"] = T["chase"]
    T["hit"] = T["window"]
    T["cutO2"] = T["window"] + 0.24
    T["cutP"] = T["l07"]
    T["cutQ"] = T["powers"]
    T["cutR"] = T["impact"]
    T["flash"] = T["black"] - 2.0 / 24
    _TC.clear()
    _TC[key] = T
    return T


def _lead(t, keys, lag=0.15):
    """Eyes lead, head follows: returns (look, head_offset) from look keyframes."""
    look = tween(t, keys)
    head = tween(t - lag, keys)
    return look, head


def _slow_blink(t, t0, close=0.3, hold=0.2, open_=0.4):
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0), (t0 + close + hold + open_, 0.0)])


# ---------------------------------------------------------------------------
# props / callbacks
# ---------------------------------------------------------------------------
def _clip_hold(s, rot=0.05, dy=95):
    def cb(ctx, side, x, y, ang):
        props.clipboard(ctx, x, y + dy * s, s * 0.85, rot)
    return cb


def _critters(t, T):
    """Terrarium critters (exactly like the thing): stare at camera, one presses on the glass."""
    def fn(ctx, x, y, w, h, tt):
        fl = y + h - 34
        k = ease_out_back(seg(t, T["terr"] + 0.12, T["terr"] + 0.45))
        # left one sits and stares at camera
        draw_thing(ctx, x + 72, fl, 0.82, t, state="sit", look=(0.1, 0.15))
        # right one is busy with the wheel, then turns its head to camera, late
        lk = tween(t, [(T["terr"] + 0.45, (0.9, -0.2)), (T["terr"] + 0.7, (-0.15, 0.15))])
        draw_thing(ctx, x + 312, fl, 0.82, t + 1.3, state="sit", look=lk, flip=True)
        # middle: hops up, paws on the glass (closest to us)
        draw_thing(ctx, x + 192, fl + 10 * (1 - k), 0.98, t + 0.7, state="cage_inside",
                   look=tween(t, [(T["terr"], (0.0, 0.3)), (T["terr"] + 0.5, (0.0, 0.1))]))
    return fn


def _screen_fn(T):
    def fn(ctx, x, y, w, h, t):
        fx.lab_screen(ctx, x, y, w, h, t, T["lab"] + 0.45, off=True)
    return fn


# ---------------------------------------------------------------------------
# A-D  lobby
# ---------------------------------------------------------------------------
TX_DESK = 300          # Tiredness at the counter
RX = 662               # receptionist x (behind the counter)
R_GROUND = 1070 + 405 * 0.75  # her desk height lands on the counter top


def _tired_lobby_kw(t, T):
    """Tiredness at the counter (positions / pose / face), shared by A, C, D."""
    v = cycle_speed("tired", "walk", 0.9) * 0.75
    ta = T["lobby"] + 0.95                 # arrival
    if t < ta:
        x = TX_DESK - v * (ta - t)
        pose = {"base": "walk", "hold": 1, "ar_h": "grip"}
        pt = t - ta + 2.0                  # arrive on a contact
    else:
        k = seg(t, ta, ta + 0.28)
        x = TX_DESK + 18 * ease_out(k)
        pose = ({"base": "walk", "hold": 1, "ar_h": "grip"}, "hold_side", k)
        pt = ta - ta + 2.0 + (t - ta) * (1 - k)
    # clipboard raise on "printer" (l01 last word) and settle
    up = tween(t, [(T["l01"] + 0.9, 0.0), (T["l01"] + 1.15, 1.0), (T["l01e"] + 0.5, 1.0),
                   (T["l01e"] + 0.85, 0.0)])
    if t >= ta + 0.28:
        pose = ("hold_side", {"base": "hold_side", "ar_p": 0.45, "ar_e": 1.25, "ar_o": 0.05}, up)
    # eyes: forward, then to her; small nods on beats
    look = tween(t, [(0.0, (0.6, 0.05)), (T["l01"], (0.55, 0.12))])
    nod = tween(t, [(T["l03"] - 0.05, 0.0), (T["l03"] + 0.12, 0.07), (T["l03"] + 0.4, 0.0),
                    (T["l04e"] + 0.05, 0.0), (T["l04e"] + 0.22, 0.09), (T["l04e"] + 0.55, 0.02)])
    lid = tween(t, [(T["l03e"] - 0.25, 0.0), (T["l03e"] + 0.05, 0.08)])
    face = {"head_nod": nod, "lid": lid}
    blink = None
    sb = T["stare"] + 0.28
    if sb - 0.05 <= t <= sb + 1.0:
        blink = _slow_blink(t, sb, 0.32, 0.18, 0.38)
    return dict(x=x, y=1500, pose=pose, pose_t=pt, turn=0.9, expr="bored", look=look,
                mouth=None, face=face, blink=blink, hold=_clip_hold(0.75, rot=0.05 + 0.1 * up))


def _recep_kw(t, T, info):
    ta = T["lobby"] + 0.95
    # typing on her (hidden) screen, then pupils up to him, head follows
    look, head = _lead(t, [(0.0, (-0.2, 0.75)), (ta - 0.1, (-0.2, 0.75)), (ta + 0.12, (-0.6, 0.05))], 0.15)
    nod = 0.12 * clamp(head[1])
    brow_r = tween(t, [(T["l02"] - 0.05, 0.0), (T["l02"] + 0.15, 0.22), (T["l02e"] + 0.3, 0.22),
                       (T["l02e"] + 0.6, 0.05)])
    gnod = tween(t, [(T["l04"] + 0.25, 0.0), (T["l04"] + 0.45, 0.08), (T["l04"] + 0.8, 0.0)])
    face = {"head_nod": nod + gnod, "brow_r": brow_r, "head_turn": 0.08 * (head[0] + 0.6)}
    blink = None
    b1 = T["l02e"] + 0.15
    if b1 - 0.05 <= t <= b1 + 0.9:
        blink = _slow_blink(t, b1, 0.25, 0.12, 0.3)
    sb = T["stare"] + 0.28
    if sb - 0.05 <= t <= sb + 1.0:
        blink = _slow_blink(t, sb, 0.32, 0.18, 0.38)
    # types (bored) until he arrives; her hands stop a beat after her eyes go up
    pose = ("type", "sit_desk", seg(t, ta + 0.05, ta + 0.3))
    return dict(pose=pose, expr="bored", look=look, mouth=info.mouth("recep", t), face=face,
                blink=blink)


def shot_lobby(ctx, t, T, info, cam):
    tk = _tired_lobby_kw(t, T)
    tk["mouth"] = info.mouth("tired", t)
    rk = _recep_kw(t, T, info)
    pose = rk.pop("pose")
    with core.camera(ctx, *cam):
        sets.lobby(ctx, t, "bg", turnstile_open=0.0, turnstile_light="red")
        draw_person(ctx, "recep", RX, R_GROUND, 0.75, t, pose=pose, turn=-0.75, counter=False, **rk)
        sets.lobby(ctx, t, "fg", parts=("counter",))
        x, y = tk.pop("x"), tk.pop("y")
        draw_person(ctx, "tired", x, y, 0.75, t, outfit=OUT, bandage=True, **tk)


def cam_A(t, T):
    k = ease_in_out(seg(t, T["lobby"] + 0.45, T["l01"] + 1.7))
    return (lerp(545, 500, k), lerp(1020, 1010, k), lerp(1.22, 1.7, k))


def cam_D(t, T):
    k = ease_in_out(seg(t, T["cutD"], T["walk"]))
    return (lerp(500, 498, k), lerp(1010, 990, k), lerp(1.72, 1.86, k))


# ---------------------------------------------------------------------------
# E  walk past the guard
# ---------------------------------------------------------------------------
GX, GY, GS = 1598, 1500, 0.82      # the Guard, behind his desk
WALK_Y = 1690                       # Tiredness strolls in front of the desk, under his nose


def _guard_yawn(t, t0):
    """Stretch-yawn (fists up, bent elbows), eyes squeezed, then looks the wrong way."""
    p_in = seg(t, t0, t0 + 0.4)
    p_out = seg(t, t0 + 1.3, t0 + 1.62)
    stretch = {"base": "hands_up_small", "al_h": "fist", "ar_h": "fist", "al_p": 0.25, "ar_p": 0.25,
               "chest": -0.12, "nod": -0.14, "hunch": 0.9, "lean": -0.06}
    if t < t0 + 1.3:
        pose = ("stand", stretch, ease_in_out(p_in))
    else:
        pose = (stretch, "stand", ease_in_out(p_out))
    yawn = clamp(p_in * 1.3) * (1 - ease_in_out(p_out))
    expr = ("neutral", "yawn", yawn)
    after = seg(t, t0 + 1.55, t0 + 1.8)
    look = tween(t, [(t0 + 1.6, (0.0, 0.0)), (t0 + 1.82, (-0.8, 0.05))])
    face = {"lid": 0.28 * after, "head_turn": -0.28 * seg(t, t0 + 1.72, t0 + 2.0),
            "press": 0.35 * after, "jaw": 0.15 * math.sin(max(0.0, t - t0 - 1.6) * 14) * (1 - seg(t, t0 + 1.6, t0 + 2.0))}
    return pose, expr, look, face


def shot_walk(ctx, t, T, info):
    t0 = T["walk"]
    cam = (1430, 1170, 1.15)
    v = cycle_speed("tired", "walk", 1.0) * 0.75
    x = 1120 + v * (t - t0)
    gp, ge, gl, gf = _guard_yawn(t, t0 + 0.2)
    # his pupils slide up to the yawning guard as he passes, then back (head never turns)
    look = tween(t, [(t0, (0.65, 0.05)), (t0 + 1.0, (0.65, 0.05)), (t0 + 1.15, (0.2, -0.55)),
                     (t0 + 1.55, (0.2, -0.55)), (t0 + 1.7, (0.65, 0.05))])
    with core.camera(ctx, *cam):
        sets.lobby(ctx, t, "bg", turnstile_open=ease_out(seg(t, T["beep"], T["beep"] + 0.4)),
                   turnstile_light="green")
        draw_person(ctx, "guard", GX, GY, GS, t, pose=gp, expr=ge, look=gl, face=gf, turn=0.1)
        sets.lobby(ctx, t, "fg", parts=("guard",))
        draw_person(ctx, "tired", x, WALK_Y, 0.75, t, pose={"base": "walk", "hold": 1, "ar_h": "grip"},
                    pose_t=t - t0 + 0.25, turn=1.0, expr="bored", look=look, outfit=OUT, bandage=True,
                    hold=_clip_hold(0.75))


# ---------------------------------------------------------------------------
# F-M  lab
# ---------------------------------------------------------------------------
def _lab_bg(ctx, t, T, alarm=0.0, pressed=0.0, door=0.0):
    sets.lab(ctx, t, "bg", alarm=alarm, button_pressed=pressed, critters_fn=_critters(t, T),
             screen_fn=_screen_fn(T), door_open=door)


def _alarm_amt(t, T):
    return ease_out(seg(t, T["alarm"], T["alarm"] + 0.3))


def shot_lab_door(ctx, t, T, info):
    t0 = T["lab"]
    cam = tween(t, [(t0, (1905, 1010, 1.0)), (T["screen"], (1885, 990, 1.05))])
    door = ease_in_out(seg(t, t0 + 0.0, t0 + 0.35))
    v = cycle_speed("tired", "walk", 1.0) * 0.75
    tw0, tw1 = t0 + 0.22, t0 + 0.92
    if t < tw0:
        x, pose, pt = 2232, "hold_side", 0.0
    elif t < tw1:
        x = 2232 - v * (t - tw0)
        pose, pt = {"base": "walk", "hold": 1, "ar_h": "grip"}, t - tw0 + 0.5
    else:
        k = seg(t, tw1, tw1 + 0.25)
        x = 2232 - v * (tw1 - tw0) - 14 * ease_out(k)
        pose, pt = ({"base": "walk", "hold": 1, "ar_h": "grip"}, "hold_side", k), tw1 - tw0 + 0.5
    look, head = _lead(t, [(t0, (-0.6, 0.0)), (t0 + 0.42, (-0.6, 0.0)), (t0 + 0.58, (-0.55, -0.85))], 0.15)
    face = {"head_nod": -0.14 * clamp(-head[1]), "lid": -0.06 * clamp(-head[1])}
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T, door=door)
        draw_person(ctx, "tired", x, 1500, 0.75, t, pose=pose, pose_t=pt, turn=-1.0, expr="bored",
                    look=look, face=face, outfit=OUT, bandage=True, hold=_clip_hold(0.75))


def shot_screen(ctx, t, T, info):
    k = seg(t, T["screen"], T["terr"])
    cam = (1733, lerp(822, 812, k), lerp(1.33, 1.42, ease_in_out(k)))
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T)


def shot_terrarium(ctx, t, T, info):
    """Starts on the last specimen tank beside the terrarium, pushes in to the critters + label."""
    k = ease_in_out(seg(t, T["terr"], T["terr"] + 0.75))
    k2 = seg(t, T["terr"] + 0.75, T["realize"])
    cam = (lerp(990, 1124, k), lerp(985, 1005, k), lerp(1.45, 2.35, k) + 0.1 * k2)
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T)


REAL_X = 1420


def shot_realize(ctx, t, T, info):
    R = T["realize"]
    k = ease_in_out(seg(t, R, T["lean"]))
    cam = (lerp(1396, 1398, k), lerp(972, 962, k), lerp(2.7, 2.9, k))
    # forearm comes up into view, eyes: label -> bandage -> label; lids lift
    arm = ease_out_back(seg(t, R + 0.2, R + 0.55))
    keys = [(R, (-0.85, 0.2)), (R + 0.32, (-0.85, 0.2)), (R + 0.5, (-0.12, 0.62)),
            (R + 0.92, (-0.12, 0.62)), (R + 1.05, (-0.85, 0.15))]
    look, head = _lead(t, keys, 0.15)
    wide = ease_out(seg(t, R + 1.08, R + 1.35))
    face = {"head_nod": 0.13 * clamp(head[1]) - 0.03 * wide, "head_turn": -0.12 * clamp(-head[0]),
            "lid": -0.16 * wide, "pupil": -0.28 * wide, "brow": 0.28 * wide, "press": 0.25 * wide}
    pose = ("stand", {"ar_ik": 1.0, "ar_tx": 0.02, "ar_ty": 0.70, "ar_tz": 0.32, "ar_h": "relaxed",
                      "ar_layer": "front", "nod": 0.05}, arm)
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T)
        draw_person(ctx, "tired", REAL_X, 1500, 0.75, t, pose=pose, turn=-0.55, expr="bored", look=look,
                    face=face, outfit=OUT, bandage=True)


CON_X = 1592
_REACH = {"ar_ik": 1.0, "ar_tx": 0.304, "ar_ty": 0.528, "ar_tz": 0.0, "ar_h": "flat", "side": 0.18,
          "lean": -0.04, "ll_k": 0.08, "lr_k": 0.14}


def _console_tired(t, T):
    """Tiredness at the console (shots J, M): woozy step back, hand finds the console
    blindly (eyes still on the terrarium) and lands right on the button."""
    L, Pr = T["lean"], T["press"]
    step = ease_in_out(seg(t, L, L + 0.34))
    x = lerp(CON_X - 52, CON_X, step)
    wob = math.sin(math.pi * step)
    stag = {"base": "stand", "rot": 0.05 * wob, "lean": -0.1 * wob, "dy": 12 * wob,
            "ll_k": 0.18 * wob, "lr_k": 0.12 * wob, "side": 0.12 * wob}
    reach = ease_out_back(seg(t, L + 0.1, Pr), 1.2)
    reach_open = dict(_REACH, ar_h="splay", ar_ty=0.58)
    if t < Pr:
        pose = (stag, reach_open, reach)
    else:
        # weight drops onto the arm, then settles
        dip = math.sin(math.pi * seg(t, Pr, Pr + 0.22))
        pose = dict(_REACH, dy=9 * dip, side=0.18 + 0.05 * dip)
    a0 = T["alarm"]
    keys = [(L, (-0.85, 0.12)), (a0 + 0.12, (-0.85, 0.12)), (a0 + 0.38, (0.75, 0.6))]
    look, head = _lead(t, keys, 0.16)
    face = {"head_turn": 0.18 * clamp(head[0]) - 0.1 * (1 - clamp(head[0] + 0.85)),
            "head_nod": 0.08 * clamp(head[1]),
            "lid": -0.14 * (1 - seg(t, a0 + 0.2, a0 + 0.5)), "pupil": -0.2 * (1 - seg(t, a0, a0 + 0.4))}
    return x, pose, look, face


def shot_console(ctx, t, T, info):
    L = T["lean"]
    al = _alarm_amt(t, T)
    pressed = ease_out(seg(t, T["press"] - 0.03, T["press"] + 0.06))
    k = ease_in_out(seg(t, T["alarm"], T["cutK"]))
    cam = (lerp(1680, 1672, k), lerp(1166, 1150, k), lerp(1.38, 1.48, k))
    x, pose, look, face = _console_tired(t, T)
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T, alarm=al, pressed=pressed)
        draw_person(ctx, "tired", x, 1500, 0.75, t, pose=pose, turn=-0.5, expr="bored", look=look,
                    face=face, outfit=OUT, bandage=True)
        sets.lab(ctx, t, "fg", alarm=al)


def shot_ohno(ctx, t, T, info):
    a0 = T["l05"]
    cam = (1612, 972, tween(t, [(a0, 2.6), (T["cutL"], 2.78)]))
    x, pose, look, face = _console_tired(t, T)
    # pupils: down at the hand -> slowly back up toward camera, resigned lid drop
    look = tween(t, [(a0, (0.75, 0.6)), (a0 + 0.35, (0.75, 0.6)), (a0 + 0.6, (0.15, 0.1))])
    face = {"head_turn": tween(t, [(a0 + 0.45, 0.14), (a0 + 0.7, 0.03)]),
            "head_nod": tween(t, [(a0 + 0.45, 0.06), (a0 + 0.7, 0.0)]),
            "lid": tween(t, [(T["l05e"] - 0.3, 0.0), (T["l05e"] + 0.05, 0.1)])}
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T, alarm=1.0, pressed=1.0)
        draw_person(ctx, "tired", x, 1500, 0.75, t, pose=pose, turn=-0.5, expr="bored", look=look,
                    mouth=info.mouth("tired", t), face=face, outfit=OUT, bandage=True)
        sets.lab(ctx, t, "fg", alarm=1.0)


def shot_guards(ctx, t, T, info):
    t0 = T["cutL"]
    cam = (2110, 1040, 1.12)
    door = ease_out(seg(t, t0 - 0.04, t0 + 0.12))
    b1 = ease_out_back(seg(t, t0 + 0.04, t0 + 0.32), 1.3)
    b2 = ease_out_back(seg(t, t0 + 0.16, t0 + 0.46), 1.2)
    gx1 = lerp(2290, 2150, b1)
    gx2 = lerp(2470, 2372, b2)
    run1 = {"base": "run", "lean": 0.1}
    pt1 = (run1, ("stand", "point", ease_out_back(seg(t, t0 + 0.26, t0 + 0.44))), seg(t, t0 + 0.2, t0 + 0.32))
    pt2 = (run1, {"base": "stand", "lean": 0.06, "hunch": 0.3}, seg(t, t0 + 0.34, t0 + 0.48))
    # landing squash of the lead guard as he plants
    land = math.sin(math.pi * seg(t, t0 + 0.26, t0 + 0.44))
    face1 = {"brow": -0.15, "squash": 0.07 * land, "lid": -0.05}
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T, alarm=1.0, pressed=1.0, door=door)
        draw_person(ctx, "guard", gx2, 1500, 0.75, t, pose=pt2, pose_t=t - t0, flip=True, turn=0.6,
                    expr="alarmed", look=(-0.8, 0.05), seed=3)
        draw_person(ctx, "guard", gx1, 1500, 0.75, t, pose=pt1, pose_t=t - t0 + 0.2, flip=True, turn=0.55,
                    expr="annoyed", look=(-0.85, 0.05), face=face1, mouth=info.mouth("guard", t))
        sets.lab(ctx, t, "fg", alarm=1.0)
        fx.dust_puff(ctx, gx1, 1500, 0.6, t, t0 + 0.3, seed=2)


def shot_bolt(ctx, t, T, info):
    t0 = T["cutM"]
    cam = (1672, 1150, 1.48)
    ant = seg(t, t0, t0 + 0.14)
    go = seg(t, t0 + 0.16, t0 + 0.5)
    v = cycle_speed("tired", "run_panic", 1.0) * 0.75
    if t < t0 + 0.16:
        x = CON_X
        pose = (_REACH, {"base": "stand", "lean": -0.1, "hunch": 1.0, "dy": 18}, ease_out(ant))
        turn, flip, pt = -0.5, False, 0.0
    else:
        x = CON_X - v * (t - t0 - 0.16) * 1.15
        pose, turn, flip, pt = "run_panic", -1.0, False, t - t0
    look = tween(t, [(t0 - 0.2, (0.85, 0.0)), (t0 + 0.12, (-0.8, 0.0))])
    face = {"squash": 0.12 * ant * (1 - go), "lid": -0.1 * ant}
    with core.camera(ctx, *cam):
        _lab_bg(ctx, t, T, alarm=1.0, pressed=1.0 - go)
        if t >= t0 + 0.16:
            fx.motion_lines(ctx, x + 120, 1080, math.pi, 420, t, 1.0, seed=4)
            fx.dust_puff(ctx, CON_X, 1500, 0.8, t, t0 + 0.16, seed=5)
        draw_person(ctx, "tired", x, 1500, 0.75, t, pose=pose, pose_t=pt, turn=turn, flip=flip,
                    expr="bored", look=look, face=face, outfit=OUT, bandage=True)
        sets.lab(ctx, t, "fg", alarm=1.0)


# ---------------------------------------------------------------------------
# N-O  corridor chase + window
# ---------------------------------------------------------------------------
def _runner_z(t, T):
    """Tiredness depth in the corridor (far -> near the camera/window)."""
    k = seg(t, T["chase"], T["hit"])
    return lerp(0.9, -0.06, k ** 0.85)


def _glass_overlay(ctx, a=1.0):
    """The near window we are looking through: two faint reflection streaks."""
    for (x0, w) in ((150, 120), (330, 50)):
        ctx.move_to(x0, 0)
        ctx.line_to(x0 + w, 0)
        ctx.line_to(x0 + w - 520, core.H)
        ctx.line_to(x0 - 520, core.H)
        ctx.close_path()
        core.fill(ctx, (1, 1, 1, 0.07 * a))


def _cracks(ctx, cx, cy, k, seed=3):
    if k <= 0:
        return
    for i in range(11):
        a = i / 11 * math.tau + core.hash01(i, seed) * 0.4
        L = (260 + 520 * core.hash01(i, seed + 1)) * k
        pts = [(cx, cy)]
        for j in range(1, 5):
            jit = (core.hash01(i * 7 + j, seed + 2) - 0.5) * 0.35
            pts.append((cx + math.cos(a + jit) * L * j / 4, cy + math.sin(a + jit) * L * j / 4))
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        core.stroke(ctx, (1, 1, 1, 0.9), 5)
    for r in (70, 170, 300):
        rr = r * k
        ctx.new_sub_path()
        n = 12
        for j in range(n + 1):
            a = j / n * math.tau
            q = rr * (0.85 + 0.3 * core.hash01(j + r, seed))
            (ctx.move_to if j == 0 else ctx.line_to)(cx + math.cos(a) * q, cy + math.sin(a) * q)
        core.stroke(ctx, (1, 1, 1, 0.6), 3.5)


def _screen_shards(ctx, t, t0, cx, cy):
    """Big shards bursting toward the camera (screen space, <= 12)."""
    if t < t0:
        return
    tau = t - t0
    for i in range(12):
        a = i / 12 * math.tau + core.hash01(i, 9) * 0.5
        sp = 900 + 900 * core.hash01(i, 10)
        x = cx + math.cos(a) * sp * tau
        y = cy + math.sin(a) * sp * tau + 600 * tau * tau
        sz = (40 + 60 * core.hash01(i, 11)) * (1 + 2.5 * tau)
        rot = tau * (4 + 6 * core.hash01(i, 12))
        al = clamp(1 - tau / 0.5)
        if al <= 0:
            continue
        with core.saved(ctx, x, y, sz, rot):
            core.poly(ctx, [(-0.6, -0.5), (0.7, -0.2), (0.1, 0.8)])
            core.fill_stroke(ctx, (0.85, 0.95, 1.0, 0.75 * al), (1, 1, 1, al), 0.06)


def shot_chase(ctx, t, T, info):
    t0 = T["chase"]
    z = _runner_z(t, T)
    x, y, s = sets.corridor_scale(z, 0.08)
    gz1 = lerp(1.0, 0.22, seg(t, t0 + 0.25, T["hit"]) ** 0.9)
    gz2 = lerp(1.05, 0.34, seg(t, t0 + 0.45, T["hit"]) ** 0.9)
    hit = T["hit"]
    with core.camera(ctx, 540, 960, 1.0):
        sets.corridor(ctx, t, "bg", alarm=1.0, window_broken=0.0)
        gs = []
        for (gz, lane, sd, tt0) in ((gz2, 0.42, 3, t0 + 0.45), (gz1, -0.38, 0, t0 + 0.25)):
            if t >= tt0:
                gx, gy, gsc = sets.corridor_scale(gz, lane)
                gs.append((gz, gx, gy, gsc, sd))
        for gz, gx, gy, gsc, sd in sorted(gs, key=lambda q: -q[0]):
            draw_person(ctx, "guard", gx, gy, gsc, t, pose="run", pose_t=t * 1.0 + sd * 0.13, turn=0.12,
                        expr="annoyed", look=(0.0, 0.0), seed=sd, face={"brow": -0.2})
        # Tiredness: flailing tired run, deadpan face
        draw_person(ctx, "tired", x, y, s, t, pose={"base": "run_panic", "lean": 0.12}, pose_t=t - t0,
                    turn=0.1, expr="bored", look=(0.0, 0.05), face={"open": 0.12, "lid": 0.05},
                    outfit=OUT, bandage=True)
    # faint red over the people too
    p = 0.5 + 0.5 * math.sin(t * math.tau * 0.8)
    ctx.rectangle(0, 0, core.W, core.H)
    core.fill(ctx, (1.0, 0.16, 0.24, 0.05 + 0.04 * p))
    _glass_overlay(ctx)


def shot_crash(ctx, t, T, info):
    """He slams into the glass we look through: splat, cracks, burst."""
    hit = T["hit"]
    t_burst = hit + 0.12
    z = -0.06
    x, y, s = sets.corridor_scale(z, 0.08)
    sq = 1.0 - seg(t, t_burst - 0.02, t_burst + 0.06)
    with core.camera(ctx, 540, 960, 1.0):
        sets.corridor(ctx, t, "bg", alarm=1.0)
        # guards skid behind
        for (gz, lane, sd) in ((0.36, 0.42, 3), (0.24, -0.38, 0)):
            gx, gy, gsc = sets.corridor_scale(gz, lane)
            draw_person(ctx, "guard", gx, gy, gsc, t, pose={"base": "stand", "lean": -0.15}, turn=0.1,
                        expr="alarmed", look=(0.0, -0.1), seed=sd)
        a = draw_person(ctx, "tired", x, y + 30 * sq, s * (1 + 0.06 * sq), t,
                        pose={"base": "run_panic", "lean": 0.05}, pose_t=0.11, turn=0.08, expr="bored",
                        look=(0.0, 0.0), face={"squash": 0.22 * sq, "width": 0.25 * sq, "lid": 0.12},
                        outfit=OUT, bandage=True)
    fc = a["face"]
    _cracks(ctx, fc[0], fc[1], ease_out(seg(t, hit, hit + 0.08)))
    if t >= t_burst:
        # pane gone: flash + flying glass
        _screen_shards(ctx, t, t_burst, fc[0], fc[1])
    else:
        _glass_overlay(ctx, 1.4)
    fx.flash(ctx, t, t_burst, frames=2, peak=0.85)


# ---------------------------------------------------------------------------
# O2-Q  exterior fall
# ---------------------------------------------------------------------------
def _fall_pos(t, T):
    t0 = T["cutO2"]
    k = seg(t, t0, T["l07"])
    p0, p1, p2 = TW["fall_path"]
    # quadratic bezier along the path
    x = (1 - k) ** 2 * p0[0] + 2 * k * (1 - k) * p1[0] + k * k * p2[0]
    y = (1 - k) ** 2 * p0[1] + 2 * k * (1 - k) * p1[1] + k * k * p2[1]
    return x, y


def shot_exterior(ctx, t, T, info):
    t0 = T["cutO2"]
    k = ease_in_out(seg(t, t0, T["l07"]))
    cam = (lerp(690, 560, k), lerp(800, 960, k), lerp(1.55, 1.3, k))
    x, y = _fall_pos(t, T)
    rot = -0.6 - 2.2 * seg(t, t0, T["l07"])
    with core.camera(ctx, *cam):
        sets.tower_exterior(ctx, t, "bg")
        draw_person(ctx, "tired", x, y + 120, 0.45, t, pose={"base": "fall", "rot": rot}, pose_t=t - t0,
                    expr=("bored", "alarmed", 0.35), look=(0.0, 0.3), outfit=OUT, bandage=True,
                    shadow=False)
        sets.tower_exterior(ctx, t, "fg")
        ox, oy = TW["shard_origin"]
        props.shards(ctx, t, t0, ox, oy, seed=4, n=12, s=0.8, floor_y=2600, dir=-1, spread=1.2)
        fx.motion_lines(ctx, x + 40, y - 40, math.atan2(150, -260), 260, t, 0.8, seed=8)


def _fall_rot(t, T):
    """Body roll while falling (tumble), slowed by the powers, then twist upright."""
    P = T["powers"]
    tw0, tw1 = P + 0.3, P + 1.0
    base = -0.5 + 0.35 * math.sin((t - T["l07"]) * 1.7)
    if t < P:
        return base
    b0 = -0.5 + 0.35 * math.sin((P - T["l07"]) * 1.7)
    slow = b0 - 0.12 * (t - P)
    k = ease_out_back(seg(t, tw0, tw1), 1.2)
    # cat twist: go the long way round (a full roll) to upright
    target = -2 * math.pi
    return lerp(slow, target, k) if t >= tw0 else slow


_PROBE = None


def _draw_hip_at(ctx, who, hx, hy, s, t, **kw):
    """Draw a person so that the HIP anchor lands on (hx, hy) (airborne poses)."""
    global _PROBE
    if _PROBE is None:
        import cairocffi as cairo
        _PROBE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 2, 2))
    a0 = draw_person(_PROBE, who, 0.0, 0.0, s, t, **kw)
    hx0, hy0 = a0["hip"]
    return draw_person(ctx, who, hx - hx0, hy - hy0, s, t, **kw)


def _probe_hip(hx, hy, s, t, kw):
    """Anchors for a person drawn so the HIP lands on (hx, hy); '_x', '_y' = where to draw."""
    global _PROBE
    if _PROBE is None:
        import cairocffi as cairo
        _PROBE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24, 2, 2))
    a0 = draw_person(_PROBE, "tired", 0.0, 0.0, s, t, **kw)
    dx, dy = hx - a0["hip"][0], hy - a0["hip"][1]
    out = {k: ((v[0] + dx, v[1] + dy) if isinstance(v, tuple) and len(v) >= 2 and k != "speed" else v)
           for k, v in a0.items() if k in ("hip", "head", "eye_l", "eye_r", "face")}
    out["_x"], out["_y"] = dx, dy
    return out


def _cloud_rush(ctx, tm, t0, alpha=0.5):
    """Three soft clouds streaming up past the faller (screen space)."""
    for i in range(3):
        ph = ((tm - t0) * 0.62 + i / 3 + 0.15) % 1.0
        yy = 2150 - ph * 2700
        xx = [80, 860, 420][i]
        sc = [1.5, 1.1, 0.8][i]
        with core.saved(ctx, xx, yy, (sc * 1.4, sc * 0.45)):
            sets._cloud(ctx, 0, 0, 1.0, (1.0, 0.80, 0.74, alpha))


def shot_fall_close(ctx, t, T, info):
    L7, P = T["l07"], T["powers"]
    pw = ease_out(seg(t, P, P + 0.14))
    slowk = ease_out(seg(t, P, P + 0.3))
    # slowed clock for everything that streams (time slows on the powers)
    tm = t if t < P else P + (t - P) * lerp(1.0, 0.16, slowk)
    rot = _fall_rot(t, T)
    tw0, tw1 = P + 0.3, P + 1.0
    tuck = seg(t, tw0 - 0.05, tw0 + 0.2) * (1 - seg(t, tw1 - 0.25, tw1))
    land = seg(t, tw1 - 0.25, tw1 + 0.1)
    fallp = {"base": "fall", "rot": rot}
    flipp = {"base": "flip", "rot": rot}
    landp = {"base": "crouch", "plant": 0.0, "rot": rot, "ar_ik": 0.0, "ar_p": 0.9, "ar_o": 1.0,
             "ar_e": 0.4, "al_ik": 0.0, "al_p": 0.9, "al_o": 1.0, "al_e": 0.4, "al_h": "open", "ar_h": "open"}
    if t < tw1 - 0.25:
        pose = (fallp, flipp, ease_in_out(tuck))
    else:
        pose = (flipp, landp, ease_out_back(land))
    # screen placement: hips around (470, 980), gentle drift; pull back a bit for the twist
    sc = tween(t, [(L7, 1.5), (P, 1.58), (P + 0.25, 1.58), (P + 1.0, 1.32)])
    hx = 490 + 26 * math.sin(tm * 0.9)
    hy = tween(t, [(L7, 1010), (P, 990), (P + 1.0, 940)]) + 16 * math.sin(tm * 1.3)
    # eyes: down at the city -> to the viewer for the punchline; on powers: forward, then down
    look = tween(t, [(L7, (0.1, 0.9)), (L7 + 0.45, (0.1, 0.9)), (L7 + 0.7, (0.0, 0.0))])
    if t >= P:
        look = tween(t, [(P, (0.0, 0.0)), (P + 0.55, (0.0, 0.0)), (P + 0.8, (0.0, 0.85))])
    lid = tween(t, [(T["l07e"] - 0.75, 0.0), (T["l07e"] - 0.3, 0.12)])
    lid -= 0.32 * pw
    face = {"lid": lid, "pupil": -0.15 * pw, "brow": tween(t, [(L7 + 0.1, 0.0), (L7 + 0.3, 0.12),
                                                            (L7 + 0.9, 0.0)]) - 0.05 * pw,
            "head_nod": -0.05 * (1 - pw)}
    expr = ("bored", "determined", ease_out(seg(t, P + 0.15, P + 0.45))) if t >= P else "bored"
    with core.camera(ctx, 200, 720, 1.55):
        sets.tower_exterior(ctx, t, "bg")
    _cloud_rush(ctx, tm, L7)
    intensity = 1.0 - 0.7 * slowk
    for side, sd in ((-1, 6), (1, 7)):
        fx.motion_lines(ctx, hx + side * 300, hy - 480, math.pi / 2, 560, tm, intensity,
                        color="#fff1f0", seed=sd, spread=200, n=3)
    # clipboard drifting away up and out (it falls slower than him)
    kc = seg(t, L7 - 0.1, L7 + 1.7)
    if kc < 1:
        props.clipboard(ctx, lerp(hx + 260, hx + 420, kc), lerp(hy - 380, hy - 1500, kc ** 1.25), 1.0,
                        0.4 + 1.6 * (tm - L7))
    kw = dict(pose=pose, pose_t=tm - L7, expr=expr, look=look, mouth=info.mouth("tired", t), face=face,
              power=pw, outfit=OUT, bandage=True, shadow=False)
    a = _probe_hip(hx, hy, sc, t, kw)
    # re-centre so the hip-head midpoint sits on (hx, hy - 260*sc/1.5): the head never leaves frame
    mx0 = (a["hip"][0] + a["head"][0]) / 2
    my0 = (a["hip"][1] + a["head"][1]) / 2
    a = _probe_hip(hx + (hx - mx0), hy + (hy - 260 * sc / 1.5 - my0), sc, t, kw)
    if pw > 0:
        (ox, oy), (hdx, hdy) = a["hip"], a["head"]
        ang = math.atan2(hdx - ox, -(hdy - oy))
        L_ = math.hypot(hdx - ox, hdy - oy)
        mx, my = (ox + hdx) / 2, (oy + hdy) / 2
        with core.saved(ctx, mx, my, 1.0, ang):
            fx.power_aura(ctx, 0, 0, 300 * sc / 1.5, L_ * 1.25 + 260, t, pw * 0.9, pulse=0.3)
    a = draw_person(ctx, "tired", a["_x"], a["_y"], sc, t, **kw)
    if t >= P:
        fx.time_slow(ctx, t, 0.85 * slowk, cx=hx, cy=hy - 200)
        el, er = a["eye_l"], a["eye_r"]
        fx.eye_glint(ctx, el[0], el[1], 1.2, t, P + 0.02, 0.42)
        fx.eye_glint(ctx, er[0], er[1], 1.2, t, P + 0.07, 0.42)


def shot_impact(ctx, t, T, info):
    I = T["impact"]
    k = ease_in(seg(t, I, T["black"]))
    with core.camera(ctx, 540, 960, 1.0):
        sets.city_fall(ctx, t, "bg", approach=0.3 + 0.68 * k)
    fx.time_slow(ctx, t, 0.5 * (1 - seg(t, I, I + 0.2)))
    fx.vignette(ctx, 0.55 + 0.3 * k, color="#0b2a33", inner=0.5)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    if t >= T["black"]:
        fx.black(ctx)
        return
    if t < T["cutB"]:
        shot_lobby(ctx, t, T, info, cam_A(t, T))
    elif t < T["cutC"]:
        shot_lobby(ctx, t, T, info, (613, 975, tween(t, [(T["cutB"], 2.9), (T["cutC"], 3.0)])))
    elif t < T["cutD"]:
        shot_lobby(ctx, t, T, info, (356, 975, tween(t, [(T["cutC"], 2.9), (T["cutD"], 3.0)])))
    elif t < T["cutE"]:
        shot_lobby(ctx, t, T, info, cam_D(t, T))
    elif t < T["cutF"]:
        shot_walk(ctx, t, T, info)
    elif t < T["cutG"]:
        shot_lab_door(ctx, t, T, info)
    elif t < T["cutH"]:
        shot_screen(ctx, t, T, info)
    elif t < T["cutI"]:
        shot_terrarium(ctx, t, T, info)
    elif t < T["cutJ"]:
        shot_realize(ctx, t, T, info)
    elif t < T["cutK"]:
        shot_console(ctx, t, T, info)
    elif t < T["cutL"]:
        shot_ohno(ctx, t, T, info)
    elif t < T["cutM"]:
        shot_guards(ctx, t, T, info)
    elif t < T["cutN"]:
        shot_bolt(ctx, t, T, info)
    elif t < T["hit"]:
        shot_chase(ctx, t, T, info)
    elif t < T["cutO2"]:
        shot_crash(ctx, t, T, info)
    elif t < T["cutP"]:
        shot_exterior(ctx, t, T, info)
    elif t < T["cutR"]:
        shot_fall_close(ctx, t, T, info)
    else:
        shot_impact(ctx, t, T, info)
        fx.flash(ctx, t, T["flash"], frames=2)


def caption_y(t, info):
    T = _T(info)
    if t >= T["black"] - 0.05:
        return None
    return 1450


def SFX(info):
    T = _T(info)
    ev = []
    # lobby: the last steps in (walk contacts at phase .3/.8), then a soft settle
    ta = T["lobby"] + 0.95
    ev += [(ta - 0.7, "footstep", -4, -0.35), (ta - 0.2, "footstep", -4, -0.3),
           (ta + 0.12, "footstep", -10, -0.3)]
    ev.append((T["l01"] + 0.92, "cloth_rustle", -8, -0.2))       # clipboard lift
    ev.append((T["beep"], "receive", -7, 0.35))                     # turnstile: access granted
    # walk past the yawning guard
    for k in range(5):
        ev.append((T["walk"] + 0.05 + 0.5 * k, "footstep", -6, -0.4 + 0.18 * k))
    ev.append((T["walk"] + 0.2, "yawn", 0, 0.25))
    # lab
    ev.append((T["lab"], "whoosh", -13, 0.4))                      # sliding lab door
    ev.append((T["lab"] + 0.45, "scan_beep", -9, -0.2))            # wall screen wakes up
    ev += [(T["lab"] + 0.52, "footstep", -7, 0.3), (T["lab"] + 1.0, "footstep", -9, 0.2)]
    ev.append((T["terr"] + 0.14, "critter_squeak", -5, -0.15))
    ev.append((T["terr"] + 0.7, "critter_squeak", -10, 0.2))
    ev.append((T["realize"] + 1.08, "heartbeat", -2, 0.0))
    ev.append((T["realize"] + 1.62, "heartbeat", -6, 0.0))
    ev.append((T["lean"] + 0.24, "footstep", -5, 0.1))
    ev.append((T["press"], "puzzle_click", -1, 0.2))
    ev.append((T["press"] + 0.01, "stamp", -9, 0.2))
    ev += _sfx.loop_events("alarm", T["alarm"], T["hit"] + 0.3, -6, 0.0)
    # guards burst in
    ev.append((T["cutL"] - 0.04, "whoosh", -9, 0.4))
    ev.append((T["cutL"] + 0.06, "footsteps_run", -5, 0.4))
    ev.append((T["cutM"] + 0.16, "smear_zip", -6, -0.3))
    # chase (he gets closer: louder)
    ev.append((T["chase"], "footsteps_run", -7, 0.0))
    ev.append((T["chase"] + 0.95, "footsteps_run", -1, 0.0))
    ev.append((T["chase"] + 0.35, "footsteps_run", -10, -0.2))
    # window crash + fall
    ev.append((T["hit"], "glass_crash_big", 0, 0.0))
    ev.append((T["cutO2"] + 0.04, "wind_fall", -2, -0.2))
    ev.append((T["l07"] + 0.7, "wind_fall", -11, 0.0))
    ev.append((T["powers"], "power_surge", 0, 0.0))
    ev.append((T["flash"], "impact_heavy", 0, 0.0))
    return ev
