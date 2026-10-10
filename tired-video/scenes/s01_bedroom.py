"""s01 - bedroom. "Tiredness just wants to game."

Shot list (all times derived from cues; see _times()):
  A  open     [0, comm+.2)        medium 3/4: gaming, name tag, tiny lean into the game hop
  B  cu       [.., headphones)    face CU: crash -> pupils slide to the window (head still),
                                  hold, slide back, slow eye roll, "Ugh." + sigh
  C  hp       [headphones, shake) medium: controller to lap, headphones neck -> on, ANC pill,
                                  bliss (lids drop, faint smile, head-bob), slow push-in
  D1 shake    [shake, +.55)       wide: room shakes 0.5 s, lamp/posters/figurine/dust
  D2 react    [.., window)        close on him (lids lift, pupils shrink), eases back for the
                                  annoyed "What the actual-" half-rise; the thud cuts him off
                                  right after the voiced word, the picture frame falls
  E  window   [window, nothing)   outside looking IN: he steps up to the glass, scans L-R-L
  F  street   [nothing, +.95)     his POV: empty sunny street, leaf, bird
  G  blink    [.., l04-.4)        back on him at the glass: one slow blink
  H  flop     [.., l05-.25)       room: flops into the chair (creak), mutters l04,
                                  reaches for the controller on the desk
  I  final    [.., end)           CU: resumes the game, deadpan l05
"""
import math

import cairocffi as cairo

from engine import core, fx, human, sets
from engine.core import (clamp, ease_in, ease_in_out, ease_out, ease_out_back, lerp, seg,
                         smoothstep, state_at, tween)
from engine.human import IK, L, P
from audio import sfx

M = sets.BEDROOM_MARKS
WX = sets.WINDOW_EXT_MARKS
S = 0.75                                    # character scale in the bedroom set
SEAT_X, SEAT_Y = M["chair_seat"]
GY = human.ground_from_seat("tired", SEAT_Y, S)
TURN = 0.35                                 # 3/4 toward camera, facing the monitor (screen-right)
SKIN = core.PAL["t_skin"]
PAD_REST = (1880.0, 1103.0)                 # controller resting on the desk (shots H/I)

# ----------------------------------------------------------------------------
# poses (controller drawn by the scene so it can be put down / picked up)
# ----------------------------------------------------------------------------
_COMMON = {"hunch": 0.3, "al_ty": 0.2, "ar_ty": 0.2, "neck": 0.3, "controller": 0.0}
GAME = dict({"base": "game"}, **_COMMON)                       # thumbs mashing
HOLD = dict({"base": "sit_game"}, **_COMMON)                   # holding still
LAP = P(HOLD, {"al_ty": 0.14, "ar_ty": 0.14, "al_tz": 0.3, "ar_tz": 0.3, "lean": 0.22,
               "hunch": 0.25})
HPP = P({"base": "sit_game", "controller": 0.0, "hunch": 0.4, "lean": 0.12, "neck": 0.25},
        IK("l", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"),
        IK("r", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"))
HALF = P(HOLD, L("l", 0.38, 0.1, 0.55), L("r", 0.38, 0.1, 0.55),
         {"lean": 0.45, "hunch": 0.5, "neck": 0.12, "al_ty": 0.42, "ar_ty": 0.42,
          "al_tz": 0.3, "ar_tz": 0.3})
SIT = P({"base": "sit_chair", "hunch": 0.55, "lean": 0.0, "neck": 0.32, "nod": 0.06})
REACH = P({"base": "sit_chair", "hunch": 0.3, "lean": 0.25, "neck": 0.2},
          IK("r", 0.25, 0.58, 0.3, "grip", layer="front"))
STAND = P({"base": "slouch"})
# flop impact: limp arms flung out, legs kick up, leaning back into the chair
FLOPL = P(SIT, {"al_o": 0.55, "ar_o": 0.55, "al_e": 0.7, "ar_e": 0.7, "al_p": 0.45, "ar_p": 0.45,
                "lean": -0.2, "hunch": 0.15, "nod": -0.12, "plant": 0.0, "hip_h": "seat"},
          L("l", 1.8, 0.12, 1.1, 0.3), L("r", 1.75, 0.12, 1.15, 0.3))


def _speech_end(info, lid, thr=0.06):
    """Last moment the voice is actually open-mouthed in line `lid` (TTS tails are silent)."""
    ln = info.line(lid)
    t = ln.end
    while t > ln.start:
        if info.mouth(ln.who, t - 0.005)[0] > thr:
            return t
        t -= 0.01
    return ln.end


def _times(info):
    c, ln = info.cue, info.line
    T = dict(comm=c("commotion"), roll=c("eyeroll"), hp=c("headphones"), bliss=c("bliss"),
             shake=c("shake"), win=c("window"), noth=c("nothing"), end=info.dur)
    # the thud cuts him off right after "actual" (the line's TTS tail is silence)
    T["thud"] = min(c("thud2"), _speech_end(info, "s01_l03") + 0.03)
    T["ugh"] = _speech_end(info, "s01_l02")        # the sigh follows the voiced "Ugh"
    for k in ("01", "02", "03", "04", "05"):
        T["l" + k] = ln("s01_l" + k).start
        T["l" + k + "e"] = ln("s01_l" + k).end
    T["cutB"] = T["comm"] + 0.2
    T["cutD2"] = T["shake"] + 0.55
    T["cutG"] = T["noth"] + 0.95
    T["cutH"] = T["l04"] - 0.4
    T["cutI"] = T["l05"] - 0.25
    # headphones business (relative to the cue)
    h = T["hp"]
    T["lap0"], T["lap1"] = h + 0.08, h + 0.36          # controller down to the lap
    T["cup0"], T["cup1"] = h + 0.36, h + 0.6           # hands to the cups at the neck
    T["lift0"], T["lift1"] = h + 0.6, h + 1.05         # cups up onto the ears
    T["ret0"], T["ret1"] = h + 1.12, h + 1.42          # hands back to the controller
    T["game1"] = h + 1.62                              # back in game pose
    T["grab"] = T["l04e"] + 0.15                       # picks the controller up off the desk
    return T


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def _bump(t, t0, t1):
    """0 -> 1 -> 0 smooth bump over [t0, t1]."""
    k = seg(t, t0, t1)
    return math.sin(k * math.pi) ** 2 if 0 < k < 1 else 0.0


def _slow_blink(t, t0, close=0.3, hold=0.18, open_=0.38):
    if t < t0 or t > t0 + close + hold + open_:
        return 0.0
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0),
                     (t0 + close + hold + open_, 0.0)])


def _quick_blink(t, t0, d=0.2):
    k = seg(t, t0, t0 + d)
    return math.sin(k * math.pi) if 0 < k < 1 else 0.0


def _blink(t, T):
    """Auto blinks (same generator as the rig) with quiet windows + scripted blinks."""
    auto = core.blink_amount(t, 11, 0.22, 0.24)
    quiet = ((-1, 0.75), (T["comm"] + 0.1, T["comm"] + 0.7), (T["roll"] - 0.05, T["roll"] + 1.0),
             (T["lift0"], T["lift1"] + 0.2), (T["bliss"] + 0.1, T["bliss"] + 1.1),
             (T["shake"] - 0.1, T["shake"] + 0.75), (T["l03"] - 0.25, T["win"] + 1.6),
             (T["noth"], T["cutG"] + 1.4), (T["cutH"], T["cutH"] + 0.7))
    for a, b in quiet:
        if a <= t <= b:
            auto = 0.0
            break
    s = max(_quick_blink(t, T["l01"] + 0.82, 0.22),          # dismissive blink as eyes return
            _slow_blink(t, T["bliss"] + 0.25, 0.32, 0.2, 0.4),  # content bliss blink
            _slow_blink(t, T["cutG"] + 0.1, 0.32, 0.16, 0.36),  # the judgement blink at the glass
            _quick_blink(t, T["l03"] - 0.32, 0.18),               # annoyed blink before the line
            _quick_blink(t, T["l04"] + 1.25, 0.2),                # mid-mutter
            _quick_blink(t, T["l04e"] - 0.05, 0.2),
            _quick_blink(t, T["l05"] + 1.25, 0.2))
    return max(auto, s)


def _pad(ctx, hl, hr, thumbs=None):
    """Game controller between two hand points (caller coords), rig look-alike."""
    x0, y0 = (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2
    with core.saved(ctx, x0, y0, S):
        lh = ((hl[0] - x0) / S, (hl[1] - y0) / S)
        rh = ((hr[0] - x0) / S, (hr[1] - y0) / S)
        human._draw_controller(ctx, lh, rh, human.INK_W, thumbs or (0.0, 0.0),
                               SKIN if thumbs is not None else None)


def _pad_rest(ctx, x, y, ang=0.0):
    """Controller lying still (centre x, y)."""
    dx, dy = math.cos(ang) * 50 * S, math.sin(ang) * 50 * S
    _pad(ctx, (x - dx, y - dy + 6 * S), (x + dx, y + dy + 6 * S))


_ANCHOR_CACHE = {}


def _anchors(pose, t, turn=TURN, headphones="neck"):
    """Anchors of a pose at time t without drawing to the frame (dry run, cached)."""
    key = (repr(pose), round(t, 4), turn, headphones)
    a = _ANCHOR_CACHE.get(key)
    if a is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2)
        c = cairo.Context(surf)
        a = human.draw_person(c, "tired", SEAT_X, GY, S, t, pose=pose, turn=turn,
                              headphones=headphones, shadow=False)
        _ANCHOR_CACHE[key] = a
    return a


# ----------------------------------------------------------------------------
# Tiredness in the room: one continuous performance used by every room shot
# ----------------------------------------------------------------------------
LOOK_SCREEN = (0.72, -0.28)
LOOK_WINDOW = (-1.05, -0.38)


def _game_hop(t):
    """1 while the game hero is in the air (props.monitor_game_screen hops every 1.3 s)."""
    ph = (t % 1.3) / 1.3
    return math.sin(ph / 0.55 * math.pi) if ph < 0.55 else 0.0


def tired_room(t, T, info):
    """-> (draw_person kwargs, pad_mode) for the room shots A-D and H-I."""
    face = {}
    hp = "neck"
    hop = _game_hop(t)
    # ------------------------------------------------------------- pose
    if t < T["hp"] + 0.05:
        # gaming -> thumbs pause for the eye roll and the sigh (shoulders rise, then drop)
        # tiny lean into each game jump (only while actually gaming)
        lean_k = 1.0 - seg(t, T["roll"] - 0.1, T["roll"] + 0.1)
        rise = (tween(t, [(T["l02"] - 0.38, 0.0), (T["l02"] + 0.02, 1.0)], ease_in_out)
                - tween(t, [(T["ugh"] - 0.05, 0.0), (T["ugh"] + 0.6, 1.25)], ease_in_out))
        p = dict(HOLD if t >= T["roll"] else GAME)
        p["lean"] = 0.3 + 0.045 * hop * lean_k
        p["hunch"] = 0.3 + 0.42 * rise
        p["chest"] = 0.1 + 0.12 * rise
        p["neck"] = 0.3 - 0.1 * rise
        if t >= T["roll"] - 0.05 and t < T["roll"] + 0.15:
            pose = (GAME, p, smoothstep(seg(t, T["roll"] - 0.05, T["roll"] + 0.15)))
        else:
            pose = p
        pad = "hands"
    elif t < T["game1"]:
        if t < T["lap1"]:
            pose = (HOLD, LAP, ease_in_out(seg(t, T["lap0"], T["lap1"])))
            pad = "hands"
        elif t < T["ret0"]:
            pose = (LAP, HPP, ease_in_out(seg(t, T["cup0"], T["cup1"])))
            pad = "lap"
        elif t < T["ret1"]:
            pose = (HPP, LAP, ease_in_out(seg(t, T["ret0"], T["ret1"])))
            pad = "lap" if t < T["ret1"] - 0.02 else "hands"
        else:
            pose = (LAP, GAME, ease_in_out(seg(t, T["ret1"], T["game1"])))
            pad = "hands"
        hp = tween(t, [(T["lift0"], 0.0), (T["lift1"], 1.0)], ease_in_out)
        # the hands track the cups automatically
    elif t < T["cutH"]:
        hp = "on"
        g = dict(GAME)
        # bliss: gentle head-bob to the music (chill = 78 bpm), slightly leaning back
        bob = math.sin(2 * math.pi * (t - T["bliss"]) / (60 / 78.0))
        bk = seg(t, T["bliss"], T["bliss"] + 0.4) * (1 - seg(t, T["shake"], T["shake"] + 0.1))
        g["lean"] = 0.3 - 0.06 * bk + 0.04 * hop * (1 - bk)
        face["head_nod"] = 0.05 * bob * bk
        face["head_tilt"] = 0.03 * bob * bk
        if t < T["shake"]:
            pose = g
        else:
            # freeze the thumbs, flinch, then the annoyed half-rise
            h = dict(HOLD)
            fl = _bump(t, T["shake"], T["shake"] + 0.45)
            h["hunch"] = 0.3 + 0.25 * fl
            k_half = ease_out_back(seg(t, T["l03"] - 0.18, T["l03"] + 0.32), 1.2)
            k_half = clamp(k_half, 0, 1.15)
            hf = dict(HALF)
            th = _bump(t, T["thud"], T["thud"] + 0.35)
            hf["hunch"] = 0.5 + 0.35 * th
            hf["lean"] = 0.42 - 0.08 * th
            if t < T["shake"] + 0.12:
                pose = (g, h, smoothstep(seg(t, T["shake"], T["shake"] + 0.12)))
            elif k_half <= 0:
                pose = h
            else:
                pose = (h, hf, k_half)
        pad = "hands"
    else:
        hp = "on"
        # H: standing by the chair -> anticipation dip -> flop -> slump; reach; game
        f0 = T["cutH"]
        a0 = f0 + 0.14                      # end of the anticipation dip
        land = f0 + 0.38
        if t < a0:
            pose = (STAND, SIT, 0.12 * ease_in_out(seg(t, f0, a0)))
        elif t < land:
            pose = ((STAND, SIT, 0.12), FLOPL, ease_in(seg(t, a0, land)))
        elif t < land + 0.4:
            pose = (FLOPL, SIT, ease_out(seg(t, land, land + 0.4)))
        elif t < T["l04e"] - 0.3:
            pose = SIT
        elif t < T["grab"]:
            pose = (SIT, REACH, ease_in_out(seg(t, T["l04e"] - 0.3, T["grab"])))
        else:
            pose = (REACH, GAME, ease_in_out(seg(t, T["grab"] + 0.05, T["l05"] - 0.05)))
        pad = "desk" if t < T["grab"] else ("hand_r" if t < T["l05"] - 0.05 else "hands")
        # landing squash + chair bounce
        sq = _bump(t, land - 0.03, land + 0.2)
        face["squash"] = 0.14 * sq
        face["head_nod"] = face.get("head_nod", 0.0) - 0.08 * _bump(t, land, land + 0.45)
    # ------------------------------------------------------------- expression
    ex_keys = [(0, "bored"), (T["comm"] + 0.12, "neutral"), (T["l01"] + 0.9, "unamused"),
               (T["roll"] + 0.55, "annoyed"), (T["ugh"] - 0.05, "sigh"), (T["hp"] + 0.5, "bored"),
               (T["lift1"] - 0.05, "neutral"), (T["bliss"], "soft_smile"),
               (T["shake"], "neutral"), (T["l03"] - 0.3, "annoyed"),
               (T["thud"], "surprised"), (T["thud"] + 0.3, "unamused"),
               (T["cutH"], "unamused"), (T["l04e"] - 0.1, "deadpan"), (T["l05"], "bored")]
    expr = state_at(t, ex_keys, 0.22)
    # ------------------------------------------------------------- eyes
    jump_look = (0.0, -0.08 * hop)
    look = tween(t, [
        (0.0, LOOK_SCREEN),
        (T["comm"] + 0.22, LOOK_SCREEN), (T["comm"] + 0.42, LOOK_WINDOW),        # slide to window
        (T["l01"] + 0.62, LOOK_WINDOW), (T["l01"] + 0.88, LOOK_SCREEN),            # ...and back
        (T["roll"], LOOK_SCREEN),
        (T["roll"] + 0.22, (0.55, -1.2)), (T["roll"] + 0.42, (-0.15, -1.25)),      # slow eye roll
        (T["roll"] + 0.6, (-0.55, -0.75)), (T["roll"] + 0.85, (0.45, -0.1)),
        (T["l02e"] - 0.15, (0.45, 0.05)), (T["hp"] + 0.3, (0.55, 0.1)),            # sigh: eyes drop
        (T["cup1"], (0.6, -0.15)), (T["lift1"], LOOK_SCREEN),
        (T["shake"], LOOK_SCREEN), (T["shake"] + 0.1, (0.05, -0.95)),              # up at the lamp
        (T["shake"] + 0.5, (0.1, -0.9)), (T["shake"] + 0.72, (-0.8, -0.5)),        # ...then the window
        (T["l03"] - 0.12, (-0.85, -0.45)),
        (T["l03"] + 0.1, LOOK_WINDOW), (T["thud"], LOOK_WINDOW),
        (T["thud"] + 0.1, (-0.1, -0.95)), (T["thud"] + 0.3, (-0.6, 0.5)),          # tracks the frame
        (T["thud"] + 0.45, (-0.55, 0.6)), (T["win"], (-0.5, 0.55)),
        (T["cutH"], (0.3, -0.05)), (T["cutH"] + 0.5, (0.45, 0.02)),
        (T["l04"] + 1.0, (0.35, 0.0)), (T["l04"] + 1.6, (0.55, -0.12)),          # glances at the screen
        (T["l04e"] - 0.45, (0.5, -0.05)),
        (T["l04e"] - 0.3, (0.95, 0.15)), (T["grab"] + 0.1, (0.9, 0.2)),           # the controller
        (T["l05"] - 0.1, LOOK_SCREEN)], ease_in_out)
    in_game = t < T["roll"] or (T["lift1"] < t < T["shake"]) or t > T["l05"]
    if in_game:
        look = (look[0] + jump_look[0], look[1] + jump_look[1])
    # ------------------------------------------------------------- face deltas
    # head follows the eyes ~0.15 s late, only where the direction allows it
    ht = tween(t, [(T["l03"] - 0.1, 0.0), (T["l03"] + 0.25, -0.32), (T["thud"] + 0.05, -0.32),
                   (T["thud"] + 0.25, -0.18)], ease_in_out)
    face["head_turn"] = face.get("head_turn", 0.0) + (ht if T["shake"] <= t < T["cutH"] else 0.0)
    # eyeroll head: tilt + chin up at the top of the roll
    rk = _bump(t, T["roll"] + 0.1, T["roll"] + 0.95)
    face["head_tilt"] = face.get("head_tilt", 0.0) + 0.06 * rk
    face["head_nod"] = face.get("head_nod", 0.0) - 0.1 * rk
    lid = 0.0
    lid += 0.1 * seg(t, T["roll"] + 0.55, T["roll"] + 0.9) * (1 - seg(t, T["hp"] + 0.4, T["hp"] + 0.8))
    lid -= 0.06 * _bump(t, T["comm"] + 0.05, T["comm"] + 0.5)              # crash: tiny lift
    lid += 0.14 * seg(t, T["bliss"], T["bliss"] + 0.35) * (1 - seg(t, T["shake"], T["shake"] + 0.08))
    sk = seg(t, T["shake"], T["shake"] + 0.08) * (1 - 0.6 * seg(t, T["l03"] - 0.35, T["l03"] - 0.05))
    lid -= 0.15 * sk                                                       # shake: +15% lid lift
    face["pupil"] = -0.3 * sk
    tk = seg(t, T["thud"], T["thud"] + 0.05) * (1 - seg(t, T["thud"] + 0.3, T["win"]))
    lid -= 0.12 * tk
    face["pupil"] -= 0.3 * tk
    if t >= T["cutH"]:
        lid -= 0.04
    face["lid"] = lid
    # bliss smile, lip presses, brows
    face["curve"] = (0.22 * seg(t, T["bliss"] + 0.1, T["bliss"] + 0.5) * (1 - seg(t, T["shake"], T["shake"] + 0.1))
                     + 0.08 * (1 - seg(t, T["comm"], T["comm"] + 0.2)))       # bored-content at the start
    face["press"] = 0.35 * _bump(t, T["l01"] + 0.3, T["roll"] + 0.1)        # lip press through the yelling
    face["brow_r"] = 0.12 * _bump(t, T["l01"] + 0.6, T["roll"] + 0.3)       # one brow, unimpressed
    face["brow"] = 0.25 * sk
    if t >= T["l05"]:
        face["brow_l"] = 0.1 * _bump(t, T["l05"] + 1.05, T["l05e"] + 0.2)   # "...a GAME here."
    turn = TURN
    if t >= T["cutH"]:
        turn = tween(t, [(T["cutH"], 0.18), (T["cutH"] + 0.4, TURN)], ease_in_out)
    kw = dict(pose=pose, expr=expr, look=look, face=face, turn=turn, headphones=hp,
              blink=_blink(t, T), mouth=info.mouth("tired", t))
    return kw, pad


# ----------------------------------------------------------------------------
# room drawing
# ----------------------------------------------------------------------------
def _room_state(t, T):
    st = {}
    if T["shake"] <= t < T["win"]:
        e = _bump(t, T["shake"], T["shake"] + 0.5) ** 0.5
        e = max(e, 0.7 * _bump(t, T["thud"], T["thud"] + 0.3) ** 0.5)
        st["shake"] = e
        if t >= T["thud"]:
            st["frame_fallen"] = seg(t, T["thud"] + 0.02, T["thud"] + 0.42)
    elif t >= T["win"]:
        st["frame_fallen"] = True
    if t >= T["cutH"]:
        land = T["cutH"] + 0.38
        st["chair_spin"] = 0.16 * math.exp(-max(0.0, t - land) * 3.0) * math.sin(max(0.0, t - land) * 9.0)
    return st


def _draw_room(ctx, t, T, info, cam, extra=None):
    kw, pad = tired_room(t, T, info)
    st = _room_state(t, T)
    cx, cy, z = cam
    dx, dy = core.shake(t, T["shake"], 0.5, 9, seed=4)
    ddx, ddy = core.shake(t, T["thud"], 0.32, 16, seed=7)
    with core.camera(ctx, cx - (dx + ddx) / z, cy - (dy + ddy) / z, z):
        sets.bedroom(ctx, t, layer="bg", **st)
        if pad == "desk":
            _pad_rest(ctx, *PAD_REST)
        a = human.draw_person(ctx, "tired", SEAT_X, GY, S, t, **kw)
        if pad == "hands":
            q = human.resolve_pose(kw["pose"], "tired", t)
            _pad(ctx, a["hand_l"], a["hand_r"], (q["al_thumb"], q["ar_thumb"]))
        elif pad == "lap":
            la = _anchors(LAP, round(T["cup0"], 3))
            _pad(ctx, la["hand_l"], la["hand_r"])
        elif pad == "hand_r":
            # carried in the right hand, then both hands close on it
            k = ease_in_out(seg(t, T["grab"] + 0.05, T["l05"] - 0.05))
            hr = a["hand_r"]
            ox, oy = 55 * S, 4 * S
            hl = (lerp(hr[0] - 2 * ox, a["hand_l"][0], k), lerp(hr[1] + oy, a["hand_l"][1], k))
            _pad(ctx, hl, (hr[0], hr[1]))
        # cool monitor light spilling onto his face (static in world space)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_SCREEN)
        core.radial_glow(ctx, 1790, 1000, 290, "#a9dcff", 0.2)
        ctx.restore()
        hpv = kw["headphones"]
        if (hpv == "on" or (not isinstance(hpv, str) and hpv >= 0.999)) and t < T["cutH"]:
            _anc_glow(ctx, t, T, a)
        if extra:
            extra(ctx, a)
    return a


def _anc_glow(ctx, t, T, a):
    """Tiny 'ANC' LED + pill on the near (screen-left) ear cup after the click."""
    t0 = T["lift1"] - 0.02
    if t < t0:
        return
    hx, hy = a["head"]
    x, y = hx - 104 * S, hy + 14 * S
    led = 0.65 + 0.35 * math.cos(min(1.0, (t - t0) / 0.5) * math.pi * 2)
    core.radial_glow(ctx, x, y, 26 * S, "#9dffb8", 0.5 * led)
    core.circle(ctx, x, y, 5 * S)
    core.fill(ctx, "#3ddc84")
    # small pill label pops out beside the cup, then tucks away
    k = core.pop(t, t0 + 0.05, 0.3) * (1 - seg(t, t0 + 1.25, t0 + 1.5))
    if k > 0.01:
        with core.saved(ctx, x - 70 * S, y - 58 * S, k * S):
            core.rrect(ctx, -58, -24, 116, 48, 24)
            core.fill_stroke(ctx, "#1d1f28", core.PAL["ink"], 4)
            core.circle(ctx, -34, 0, 7)
            core.fill(ctx, "#3ddc84")
            core.text(ctx, "ANC", 12, 11, 30, "#e9fff0", "ui")


# ----------------------------------------------------------------------------
# shots
# ----------------------------------------------------------------------------
def _shot_open(ctx, t, T, info):
    k = seg(t, 0, T["cutB"])
    cam = (lerp(1738, 1730, k), lerp(1128, 1118, k), lerp(1.74, 1.82, ease_in_out(k)))
    _draw_room(ctx, t, T, info, cam)


def _shot_cu(ctx, t, T, info):
    k = ease_in_out(seg(t, T["cutB"], T["hp"]))
    cam = (lerp(1676, 1670, k), lerp(1070, 1066, k), lerp(2.55, 2.68, k))
    _draw_room(ctx, t, T, info, cam)


def _shot_hp(ctx, t, T, info):
    k = ease_in_out(seg(t, T["hp"], T["shake"]))
    cam = (lerp(1668, 1662, k), lerp(1118, 1092, k), lerp(1.9, 2.15, k))
    _draw_room(ctx, t, T, info, cam)


def _shot_shake(ctx, t, T, info):
    if t < T["cutD2"]:
        # wide: the whole wall shakes (lamp, posters, figurine, frame)
        k = ease_in_out(seg(t, T["shake"], T["cutD2"]))
        cam = (lerp(1694, 1690, k), lerp(1000, 1004, k), lerp(1.22, 1.25, k))
    else:
        # close on his reaction, then the camera eases back to make room for the
        # annoyed half-rise, the thud and the frame falling behind him
        k = ease_in_out(seg(t, T["l03"] - 0.3, T["l03"] + 0.45))
        k2 = ease_in_out(seg(t, T["l03"] + 0.45, T["win"]))
        cam = (lerp(1670, 1668, k), lerp(1066, 1036, k) - 6 * k2, lerp(2.35, 1.74, k) + 0.06 * k2)
    _draw_room(ctx, t, T, info, cam)


def _shot_flop(ctx, t, T, info):
    k = ease_in_out(seg(t, T["cutH"] + 0.6, T["cutI"]))
    cam = (lerp(1700, 1712, k), lerp(1118, 1108, k), lerp(1.72, 1.8, k))
    _draw_room(ctx, t, T, info, cam)


def _shot_final(ctx, t, T, info):
    k = ease_in_out(seg(t, T["cutI"], T["end"]))
    cam = (lerp(1690, 1684, k), lerp(1068, 1062, k), lerp(2.6, 2.75, k))
    _draw_room(ctx, t, T, info, cam)


# --- E/G: outside looking in -------------------------------------------------
LEAN = P({"base": "look_window"})


def _shot_window(ctx, t, T, info, blink_shot=False):
    if not blink_shot:
        t0 = T["win"]
        lean = ease_out_back(seg(t, t0 + 0.04, t0 + 0.5), 1.4)
        cam = (540, lerp(880, 862, seg(t, t0, T["noth"])), lerp(1.4, 1.46, seg(t, t0, T["noth"])))
    else:
        t0 = T["cutG"]
        lean = 1.0
        cam = (540, 846, lerp(1.62, 1.68, seg(t, t0, T["cutH"])))
    # he steps up and leans into the glass: smaller/lower -> close, eye line ~880 -> ~790
    s = lerp(1.22, 1.45, lean)
    fy = lerp(880, 790, lean) + s * 768
    # eyes scan left - right - left (pupils lead, head follows 0.15 s later)
    if not blink_shot:
        a0 = t0 + 0.3
        keys = [(t0, (0.0, 0.1)), (a0, (0.0, 0.1)), (a0 + 0.18, (-0.95, 0.15)), (a0 + 0.42, (-0.95, 0.15)),
                (a0 + 0.62, (0.95, 0.15)), (a0 + 0.86, (0.95, 0.15)), (a0 + 1.0, (-0.9, 0.12)),
                (a0 + 1.12, (-0.9, 0.12)), (a0 + 1.2, (-0.1, 0.25))]
        look = tween(t, keys, ease_in_out)
        hlook = tween(t - 0.15, keys, ease_in_out)
        face = {"head_turn": 0.28 * hlook[0], "lid": -0.12, "press": 0.25, "brow": 0.12}
        expr = "neutral"
        blink = 0.0
    else:
        look = (-0.05, 0.2)
        face = {"lid": 0.05 + 0.08 * seg(t, t0 + 0.5, t0 + 0.85), "press": 0.3, "frown": 0.15}
        expr = "deadpan"
        blink = _slow_blink(t, t0 + 0.1, 0.32, 0.16, 0.36)
    with core.camera(ctx, *cam):
        sets.bedroom_window_exterior(ctx, t, layer="bg")
        a = human.draw_person(ctx, "tired", 540, fy, s, t, pose=("slouch", LEAN, lean), expr=expr,
                              look=look, face=face, turn=0.0, headphones="on", blink=blink,
                              mouth=info.mouth("tired", t), shadow=False)
        sets.bedroom_window_exterior(ctx, t, layer="fg")
        # breath fog on the glass under his nose
        if lean > 0.6:
            mx, my = a["mouth"]
            br = 0.5 + 0.5 * math.sin((t - t0) * 2 * math.pi / 1.6)
            al = 0.16 * (0.4 + 0.6 * br) * clamp((lean - 0.6) / 0.4)
            core.ellipse(ctx, mx, my + 14, 62 + 10 * br, 26 + 5 * br)
            core.fill(ctx, (1, 1, 1, al))


# --- F: his POV ----------------------------------------------------------------
def _shot_street(ctx, t, T, info):
    lt = t - T["noth"]
    k = seg(t, T["noth"], T["cutG"])
    with core.camera(ctx, 540, lerp(950, 935, k), lerp(1.0, 1.04, k)):
        # leaf: start the 7 s loop so it is just leaving the tree; bird: hops on cue
        sets.street_view(ctx, lt + 1.2, layer="bg")


# ----------------------------------------------------------------------------
def render(ctx, t, info):
    T = _times(info)
    if t < T["cutB"]:
        _shot_open(ctx, t, T, info)
    elif t < T["hp"]:
        _shot_cu(ctx, t, T, info)
    elif t < T["shake"]:
        _shot_hp(ctx, t, T, info)
    elif t < T["win"]:
        _shot_shake(ctx, t, T, info)
    elif t < T["noth"]:
        _shot_window(ctx, t, T, info)
    elif t < T["cutG"]:
        _shot_street(ctx, t, T, info)
    elif t < T["cutH"]:
        _shot_window(ctx, t, T, info, blink_shot=True)
    elif t < T["cutI"]:
        _shot_flop(ctx, t, T, info)
    else:
        _shot_final(ctx, t, T, info)
    # screen space
    fx.name_tag(ctx, "TIREDNESS", "just wants to play his game", t, 0.3, 3.0, x=90, y=170,
                color="tired")


def SFX(info):
    T = _times(info)
    ev = [
        (0.12, "game_blips", -9, 0.25),                    # game through the desk speakers
        (T["comm"], "cage_rattle", -3, -0.6),              # trash cans going over outside (window side)
        (T["comm"] + 0.06, "body_thud", -10, -0.6),
        (T["comm"] + 0.35, "cage_rattle", -9, -0.7),       # ...a lid still rattling
        (T["ugh"] + 0.02, "sigh", -2, 0.0),
        (T["lap0"] + 0.05, "cloth_rustle", -5, 0.0),       # controller down to the lap
        (T["cup1"] - 0.05, "cloth_rustle", -5, 0.0),       # hands to the cups
        (T["lift1"] - 0.08, "anc_on", 0, -0.2),            # cups seat on the ears: click + hush
        (T["shake"], "house_rumble", 0, 0.0),
        (T["thud"], "body_thud", 0, -0.3),                 # the bigger thump cuts him off
        (T["thud"] + 0.42, "foot_tap", 2, -0.2),           # picture frame hits the floor
        (T["cutH"] + 0.37, "chair_creak", 2, 0.0),         # the flop lands at cutH + 0.38
        (T["cutH"] + 0.38, "body_thud", -14, 0.0),
        (T["l04e"] - 0.2, "cloth_rustle", -5, 0.2),        # reaching for the controller
        (T["grab"], "mouse_click", -1, 0.3),               # controller ticks off the desk
    ]
    # with the headphones on, the game is only a tinny leak from the cups
    ev += sfx.loop_events("game_music_leak", T["lift1"] + 0.3, T["win"] - 1.9, -3, 0.0)
    ev += sfx.loop_events("game_music_leak", T["cutH"] + 0.6, T["end"], -3, 0.0)
    return ev
