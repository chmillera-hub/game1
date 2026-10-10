"""s10 - "A normal friend visit" (music: awkward).

Porch: Tiredness opens the door (bandage, deadpan). Emb, too loud, performs for
the recorder blinking in his coat pocket, panics about "arms", trips on the
GO AWAY mat, the recorder clatters out, "Pocket calculator!", "...Cool.", he
walks off stiffly, the door closes on one narrowing eye.  Bedroom (dusk): he
types HUSHCORP, the site + visitor-entrance pin, monitor-lit face, lids lift.

All timing comes from info cues / line word starts (never hard-coded).
"""
import math

from engine import core, sets, props, fx, human
from engine.core import (clamp, lerp, seg, tween, state_at, ease_out_back, ease_in_out, ease_out,
                         ease_in, smoothstep, hash01, noise1)
from audio import sfx

HM = sets.HOUSE_MARKS
BM = sets.BEDROOM_MARKS
SH = 0.45                 # people on the house set
SB = 0.85                 # Tiredness at the desk (bedroom)
INK = core.PAL["ink"]
H_T = human.CHARS["tired"]["height"]
H_E = human.CHARS["embar"]["height"]

# porch stage (house world px)
EMB_X0, EMB_Y = 1452.0, 1456.0
TIR_X0, TIR_Y = 1622.0, 1440.0
MAT = (1548.0, 1463.0, 0.34)          # doormat x, y, s
REC_REST = (1530.0, 1474.0)           # where the recorder ends up (on the mat)
DOOR_OPEN = 0.86                      # door panel open amount while they talk
DOOR_GAP = 0.34                       # door almost shut: one eye in the gap


# ----------------------------------------------------------------------------
# timing
# ----------------------------------------------------------------------------
def _ws(info, lid, k):
    """Scene time of word k of line lid (lip-sync word starts; proportional fallback)."""
    ln = info.line(lid)
    env = info._lip.get(lid) or {}
    w = env.get("word_starts") or []
    if 0 <= k < len(w):
        return ln.start + w[k]
    n = max(1, len(ln.text.split()))
    return ln.start + ln.dur * clamp(k / n)


def _speech_end(info, lid, thr=0.12):
    ln = info.line(lid)
    env = info._lip.get(lid) or {}
    o = env.get("open") or []
    idx = [i for i, v in enumerate(o) if v > thr]
    return ln.start + (idx[-1] / 100.0 if idx else ln.dur * 0.8)


_KCACHE = {}


def keys(info):
    kid = (id(info), info.dur)
    if kid in _KCACHE:
        return _KCACHE[kid]
    c = info.cue
    L = {i: info.line("s10_l0%d" % i) for i in range(1, 7)}
    k = {}
    k["open0"] = c("knock") + 0.30
    k["open1"] = k["open0"] + 0.42
    k["L1"], k["L1e"] = L[1].start, L[1].end
    k["w1"] = [_ws(info, "s10_l01", i) for i in range(12)]
    k["sh2"] = k["w1"][5] - 0.06                      # "As a friend!"  -> Emb MCU
    k["L2"], k["L2e"] = L[2].start, L[2].end
    k["w2"] = [_ws(info, "s10_l02", i) for i in range(12)]
    k["sh3"] = k["L2"] - 0.10                         # "How's the arm?" -> two-shot + point
    k["sh4"] = k["w2"][3] - 0.06                      # "I mean, what arm?" -> Emb CU
    k["look"] = c("look")
    k["L3"], k["L3e"] = L[3].start, L[3].end
    k["okay_end"] = _speech_end(info, "s10_l03")
    k["trip"] = c("trip")                             # foot snags the mat
    k["turn0"] = k["L3e"] - 0.02
    k["pop"] = k["trip"] + 0.12                       # recorder pops out of the pocket
    k["land"] = k["pop"] + 0.34                       # ...and lands on the mat
    k["both"] = c("both")
    k["ins0"] = k["land"] - 0.12                      # insert: the landing
    k["ins1"] = k["both"] + 0.24
    k["L4"], k["L4e"] = L[4].start, L[4].end
    k["grab"] = k["L4"] + 0.20
    k["up"] = k["grab"] + 0.24
    k["stuff0"] = k["L4e"] - 0.08
    k["stuff1"] = k["stuff0"] + 0.30
    k["pretend"] = c("pretend")
    k["L5"], k["L5e"] = L[5].start, L[5].end
    k["cool_end"] = _speech_end(info, "s10_l05")
    k["leave"] = c("leave")
    k["sh10"] = k["L5e"] + 0.12                       # wide: Emb walking off
    k["S"] = c("search")
    k["sh11"] = k["S"] - 0.90                         # door gap close-up
    k["dc0"] = k["sh11"] - 0.20                       # door starts closing
    k["dc1"] = k["sh11"] + 0.30                       # ...gap reached
    k["dc2"] = k["S"] - 0.14                          # click shut
    k["L6"], k["L6e"] = L[6].start, L[6].end
    k["w6"] = [_ws(info, "s10_l06", i) for i in range(7)]
    k["b2"] = k["S"] + 0.55                           # screen insert 1
    k["b3"] = k["L6"] + 0.30                          # monitor-lit face
    k["b4"] = k["L6"] + 1.45                          # screen insert 2 (site + pin)
    k["resolve"] = c("resolve")
    k["b5"] = min(k["L6e"] - 0.1, k["resolve"] - 0.3)  # resolve push-in
    k["lift"] = k["resolve"] + 0.05
    k["t_type"] = k["S"] + 0.30
    k["char_dt"] = 0.10
    k["t_results"] = k["t_type"] + 8 * k["char_dt"] + 0.37
    k["t_site"] = k["t_results"] + 1.40
    k["end"] = info.dur
    _KCACHE.clear()
    _KCACHE[kid] = k
    return k


def _search(ctx, x, y, w, h, t, k):
    fx.search_screen(ctx, x, y, w, h, t, k["t_type"], "HUSHCORP", t_results=k["t_results"],
                     t_site=k["t_site"], char_dt=k["char_dt"])


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def ikw(who, side, px, py, turn, tz=0.12, **kw):
    """IK dict for a target given in rig px (s=1) relative to the ground point."""
    H = human.CHARS[who]["height"]
    phi = clamp(turn, -1.6, 1.6) * 0.86
    sgn = -1 if side == "l" else 1
    tx = (px - tz * H * math.sin(phi)) / (sgn * H * max(0.25, math.cos(phi)))
    return human.IK(side, tx, -py / H, tz, **kw)


def _slow_blink(t, t0, close=0.3, hold=0.18, opn=0.35):
    return tween(t, [(t0, 0.0), (t0 + close, 1.0), (t0 + close + hold, 1.0), (t0 + close + hold + opn, 0.0)])


def _fsum(*ds):
    out = {}
    for d in ds:
        for kk, v in d.items():
            out[kk] = out.get(kk, 0.0) + v
    return out


def _door(t, k):
    """Front door opening amount."""
    if t < k["dc0"]:
        return DOOR_OPEN * ease_out(seg(t, k["open0"], k["open1"]))
    if t < k["dc2"]:
        return tween(t, [(k["dc0"], DOOR_OPEN), (k["dc1"], DOOR_GAP), (k["dc2"] - 0.05, DOOR_GAP - 0.02)])
    return lerp(DOOR_GAP - 0.02, 0.0, ease_in(seg(t, k["dc2"] - 0.05, k["dc2"])))


def _door_edge_x(op):
    q = sets.door_quad(1480, 990, 1430, 220, op, (1300, 900), D=2600, toward=False)
    return q[1][0]


def _led(t, t0=0.0):
    return 1.0 if ((t - t0) % 1.0) < 0.5 else 0.12


# ----------------------------------------------------------------------------
# Embarrassment on the porch
# ----------------------------------------------------------------------------
def _emb(t, k, info):
    """-> (x, y, kwargs, flags)"""
    w1, w2 = k["w1"], k["w2"]
    turn = 0.62
    x = EMB_X0
    flags = {"rec": "pocket"}
    if t >= k["sh10"] - 0.04:
        return _emb_leave(t, k, info)
    # ---------------------------------------------------------------- poses
    knock_bob = 0.0
    for tk in (0.0, 0.17):            # the two raps of the knock SFX
        p = seg(t, tk - 0.07, tk + 0.07)
        knock_bob += math.sin(p * math.pi) * 0.35 if 0 < p < 1 else 0.0
    P_KNOCK = {"base": "stand", "ar_p": 1.35, "ar_o": 0.1, "ar_e": 0.9 - knock_bob, "ar_h": "fist",
               "lean": 0.05 + knock_bob * 0.05, "hunch": 0.4, "turn": 0.15}
    P_STIFF = {"base": "awkward", "hunch": 0.75}
    wv = math.sin(max(0.0, t - w1[0]) * 2 * math.pi * 2.6) * 0.22
    P_WAVE = {"base": "awkward", "ar_ik": 0.0, "ar_p": 0.25, "ar_o": 0.25, "ar_e": 2.45, "ar_eo": -0.5 + wv,
              "ar_h": "open", "ar_tf": -1.0, "hunch": 0.65, "lift": 6 * abs(wv) / 0.22}
    P_POCKET = {"base": "awkward", "nod": 0.2, "neck": 0.18, "tilt": 0.1, "lean": 0.07, "hunch": 0.95,
                "chest": 0.06}
    P_POINT = {"base": "stand", "hunch": 0.5, "lean": 0.08,
               **ikw("embar", "r", (1598 - EMB_X0) / SH, (1250 - EMB_Y) / SH, 0.62, 0.2, h="point", wa=0.35,
                     wabs=0.9)}
    # hands clutching the pocket (pocket ~ 545 rig px up, a little to the right)
    P_COVER = {"base": "stand", "hunch": 0.85, "lean": 0.07, "nod": 0.05,
               **ikw("embar", "r", 66, -612, turn, 0.15, h="flat", layer="front", wa=-1.9, wabs=0.6),
               **ikw("embar", "l", 84, -585, turn, 0.18, h="flat", layer="front", wa=-1.2, wabs=0.6)}
    P_PLEAD = dict(P_COVER, lean=0.14, nod=-0.02, hunch=1.0)
    P_RELIEF = {"base": "stand", "hunch": 0.15, "lean": -0.02, "chest": -0.04,
                **ikw("embar", "r", 66, -605, turn, 0.15, h="flat", layer="front", wa=-1.9, wabs=0.6)}
    P_TRIP = {"base": "stand", "lean": 0.5, "hunch": 0.5, "al_p": 1.7, "al_o": 0.5, "al_e": 0.3, "al_h": "splay",
              "ar_p": 1.9, "ar_o": 0.6, "ar_e": 0.4, "ar_h": "splay", "ll_p": 0.7, "ll_k": 0.5,
              "lr_p": -0.6, "lr_k": 1.1, "lift": 16, "sway": 0.0}
    P_BAL = {"base": "stand", "lean": 0.34, "hunch": 0.75, "al_p": 0.7, "al_o": 1.1, "al_e": 0.6, "al_h": "splay",
             "ar_p": 0.8, "ar_o": 1.0, "ar_e": 0.7, "ar_h": "splay", "ll_p": 0.45, "ll_k": 0.8,
             "lr_p": -0.12, "lr_k": 0.6, "sway": 0.0}
    P_FROZEN = dict(P_BAL, lean=0.3, hunch=0.95, al_p=0.55, ar_p=0.6, breath=0.2)
    P_DIVE = {"base": "pick_up", "sway": 0.0}
    P_UP = {"base": "present", "hunch": 0.7, "lean": 0.1, "ar_p": 0.55, "ar_e": 1.25, "tilt": -0.05}
    P_STUFF = {"base": "stand", "hunch": 0.6,
               **ikw("embar", "r", 70, -640, 0.75, 0.15, h="grip", layer="front", wa=-1.9, wabs=0.5)}
    pat = abs(math.sin(max(0.0, t - k["stuff1"]) * 2 * math.pi * 2.2)) * 0.02
    P_PAT = {"base": "stand", "hunch": 0.45, "chest": -0.03,
             **ikw("embar", "r", 66, -612 - pat * H_E, 0.75, 0.15, h="flat", layer="front", wa=-1.9, wabs=0.6)}

    pose_keys = [(-1.0, P_KNOCK), (k["open0"] + 0.08, P_STIFF), (w1[0] - 0.05, P_WAVE), (w1[2] - 0.05, P_POCKET),
                 (k["w1"][8] + 0.05, P_STIFF), (k["L2"] - 0.05, P_POINT), (w2[3] - 0.02, P_COVER),
                 (w2[7], P_PLEAD), (k["L2e"] + 0.3, P_COVER), (k["okay_end"] - 0.15, P_RELIEF)]
    trans = 0.22
    # ---------------------------------------------------------------- trip & snatch
    if t >= k["turn0"]:
        tt0, ttr = k["turn0"], k["trip"]
        # spin to leave (screen-left)
        turn = lerp(0.62, -0.85, ease_in_out(seg(t, tt0, ttr + 0.02)))
        x = EMB_X0 - 14 * ease_in(seg(t, ttr - 0.06, ttr + 0.04))
        if t < ttr:
            pose = ("stand", {"base": "walk"}, smoothstep(seg(t, tt0, ttr)))
        elif t < k["pop"] + 0.12:
            pose = ({"base": "walk"}, P_TRIP, ease_out(seg(t, ttr, ttr + 0.12)))
        else:
            pose = (P_TRIP, P_BAL, ease_out_back(seg(t, k["pop"] + 0.12, k["pop"] + 0.34)))
        # lurch left during the trip, settle
        x -= 52 * ease_out(seg(t, ttr, k["pop"] + 0.3))
        x -= 12 * ease_out(seg(t, k["pop"] + 0.2, k["land"] + 0.1))
        if t >= k["land"] + 0.05:
            pose = (P_BAL, P_FROZEN, smoothstep(seg(t, k["land"] + 0.05, k["land"] + 0.3)))
        if t >= k["L4"] - 0.04:
            # snatch: spin back to the right and dive for it
            g0 = k["L4"] - 0.04
            turn = lerp(-0.85, 0.75, ease_in_out(seg(t, g0, k["grab"])))
            xg = REC_REST[0] - 58
            xs = x
            x = lerp(xs, xg, ease_in_out(seg(t, g0 + 0.02, k["grab"])))
            x = lerp(x, xg - 18, ease_out(seg(t, k["grab"] + 0.05, k["up"] + 0.2)))
            pre = {"base": "stand", "lift": 8, "hunch": 0.9, "sway": 0.0}  # tiny anticipation rise
            if t < g0 + 0.06:
                pose = (P_FROZEN, pre, seg(t, g0, g0 + 0.06))
            elif t < k["grab"]:
                pose = (pre, P_DIVE, ease_in(seg(t, g0 + 0.06, k["grab"])))
            elif t < k["stuff0"]:
                pose = (P_DIVE, P_UP, ease_out_back(seg(t, k["grab"] + 0.04, k["up"])))
                flags["rec"] = "hand"
            elif t < k["stuff1"]:
                pose = (P_UP, P_STUFF, smoothstep(seg(t, k["stuff0"], k["stuff0"] + 0.22)))
                flags["rec"] = "hand" if t < k["stuff0"] + 0.2 else "pocket"
            else:
                pose = (P_STUFF, P_PAT, smoothstep(seg(t, k["stuff1"], k["stuff1"] + 0.15)))
                turn = 0.75
                go = k["cool_end"] + 0.08
                if t >= go:
                    turn = lerp(0.75, -0.95, ease_in_out(seg(t, go, go + 0.22)))
                    pose = (P_PAT, {"base": "walk"}, smoothstep(seg(t, go, go + 0.2)))
                    x -= 120 * ease_in(seg(t, go + 0.1, k["sh10"]))
        else:
            if t >= k["pop"]:
                flags["rec"] = "air" if t < k["land"] else "floor"
            if t >= k["land"]:
                flags["rec"] = "floor"
    else:
        pose = state_at(t, pose_keys, trans)

    # ---------------------------------------------------------------- face
    look = (0.85, -0.05)          # at Tiredness (to his right, a bit lower)
    lk = [(0.0, (0.95, 0.0)), (k["open0"] + 0.15, (0.85, 0.1)),
          (w1[2] - 0.02, (0.85, 0.1)), (w1[2] + 0.12, (0.35, 1.05)),        # "Just checking in!" -> pocket
          (w1[8] + 0.02, (0.35, 1.05)), (w1[8] + 0.16, (0.9, 0.0)),          # "...normal friend visit!" -> him
          (k["L1e"] + 0.05, (0.9, 0.0)), (k["L1e"] + 0.13, (0.3, 1.0)),      # dart to pocket
          (k["L1e"] + 0.28, (0.3, 1.0)), (k["L1e"] + 0.36, (0.9, 0.0)),
          (k["L2"] + 0.05, (0.9, 0.05)), (k["L2"] + 0.22, (0.85, 0.75)),    # "How's the arm?" -> his arm
          (w2[3] - 0.05, (0.85, 0.75)), (w2[3] + 0.05, (0.3, 1.05)),         # "I mean" -> pocket!
          (w2[5] - 0.02, (0.3, 1.05)), (w2[5] + 0.08, (0.92, -0.05)),        # "what arm?" -> him
          (w2[8] - 0.02, (0.92, -0.05)), (w2[8] + 0.07, (0.3, 1.0)),         # dart
          (w2[9] + 0.05, (0.3, 1.0)), (w2[9] + 0.13, (0.95, -0.05)),
          (w2[11] - 0.02, (0.95, -0.05)), (w2[11] + 0.07, (0.35, 1.0)),      # "arms." -> pocket
          (k["L2e"] + 0.1, (0.35, 1.0)), (k["L2e"] + 0.22, (0.92, 0.0))]
    look = tween(t, lk, ease_in_out)
    expr_keys = [(-1.0, "nervous_smile"), (k["open0"] + 0.1, "nervous_smile"), (w1[2] - 0.05, "surprised"),
                 (w1[8], "nervous_smile"), (k["L2"] - 0.05, "sad"), (w2[3] - 0.05, "panic"),
                 (w2[7] - 0.05, "pleading"), (k["L2e"] + 0.25, "nervous_smile"),
                 (k["okay_end"] - 0.12, "relieved")]
    expr = state_at(t, expr_keys, 0.2)
    face = {"brow": 0.25 * seg(t, k["open0"], k["open1"]) - 0.25 * seg(t, k["L1"] + 0.3, k["L1"] + 0.6)}
    face["eye_size"] = 0.1 * math.sin(math.pi * seg(t, k["open0"] + 0.1, k["open1"] + 0.25))
    # too loud: chin to the pocket while bellowing "Just checking in!"
    pk = seg(t, w1[2] - 0.1, w1[2] + 0.12) - seg(t, w1[8] - 0.05, w1[8] + 0.15)
    face["head_nod"] = 0.2 * pk
    face["head_turn"] = 0.14 * pk
    face["squash"] = -0.05 * pk
    face["lid"] = -0.16 * pk                 # eyes wide on the "microphone"
    face["brow"] = face["brow"] + 0.35 * pk
    face["open"] = 0.12 * pk                 # bellowing
    blush = tween(t, [(0.0, 0.3), (k["L2"], 0.4), (w2[3], 0.62), (k["L2e"], 0.6), (k["okay_end"], 0.38)])
    sweat = tween(t, [(0.0, 0.25), (w2[3], 0.7), (k["okay_end"], 0.5)])
    glint = 0.0
    # trip / both / snatch acting
    if t >= k["turn0"]:
        look = (-0.95, 0.15)
        expr = state_at(t, [(k["turn0"] - 1, "relieved"), (k["trip"], "alarmed"), (k["land"] - 0.02, "frozen_shock"),
                            (k["L4"] - 0.04, "panic"), (k["up"] - 0.05, "nervous_smile"),
                            (k["stuff1"], "fake_cool")], 0.12)
        face = {"squash": -0.08 * math.sin(math.pi * seg(t, k["trip"], k["trip"] + 0.25))}
        if t >= k["land"] - 0.05:
            # head snaps back over his shoulder to the recorder on the mat
            hk = ease_out_back(seg(t, k["land"] - 0.05, k["land"] + 0.12))
            face["head_turn"] = 1.15 * hk * (1 - seg(t, k["L4"] - 0.04, k["L4"] + 0.1))
            look = (lerp(-0.95, 0.75, hk), lerp(0.15, 0.85, hk))
            face["eye_size"] = 0.12 * hk
            face["pupil"] = -0.15 * hk
        if t >= k["L4"] - 0.04:
            look = tween(t, [(k["L4"], (0.6, 0.9)), (k["up"], (0.1, -0.2)), (k["up"] + 0.2, (0.95, -0.05)),
                             (k["stuff0"], (0.95, -0.05)), (k["stuff0"] + 0.1, (0.3, 1.0)),
                             (k["stuff1"], (0.3, 1.0)), (k["stuff1"] + 0.12, (0.95, 0.0))])
            face = {"eye_size": 0.1 * seg(t, k["up"] - 0.05, k["up"] + 0.1), "width": 0.15 * seg(t, k["up"], k["up"] + 0.2)}
            glint = math.sin(math.pi * seg(t, k["up"] + 0.35, k["up"] + 0.6))
        blush = tween(t, [(k["turn0"], 0.38), (k["land"], 0.55), (k["both"] + 0.5, 1.0), (k["up"], 0.9),
                          (k["stuff1"], 0.72)])
        sweat = tween(t, [(k["turn0"], 0.5), (k["land"], 1.0), (k["stuff1"], 0.8)])
    blink = 0.0 if (k["open0"] - 0.15 <= t < k["open1"] + 0.5 or k["trip"] - 0.2 <= t < k["L4"]) else None
    kw = dict(pose=pose, expr=expr, look=look, face=face, turn=turn, blush=blush, sweat=sweat, glint=glint,
              mouth=info.mouth("embar", t), blink=blink)
    return x, EMB_Y, kw, flags


P_SWALK = {"base": "walk", "al_p": 0.0, "al_o": 0.07, "al_e": 0.03, "al_h": "flat", "ar_p": 0.0, "ar_o": 0.07,
           "ar_e": 0.03, "ar_h": "flat", "twist": 0.0, "posture": 0.25, "chest": -0.07, "hunch": 0.15,
           "neck": -0.05}


def _bump(t, t0, dur, rise=0.09):
    """0 -> 1 (snappy) -> hold -> 0."""
    return seg(t, t0, t0 + rise) * (1 - seg(t, t0 + dur - rise, t0 + dur))


def _emb_leave(t, k, info):
    """Walking off stiffly across the lawn (screen-left), glancing back twice."""
    t0 = k["sh10"] - 0.1
    sp = abs(human.cycle_speed("embar", "walk", -1.0)) * SH
    x = 1528.0 - sp * max(0.0, t - t0)
    g1, g2 = k["sh10"] + 0.28, k["sh10"] + 0.82
    gl = max(_bump(t, g1, 0.36), _bump(t, g2, 0.3))
    face = {"head_turn": 1.45 * gl, "eye_size": 0.06 * gl}
    look = (lerp(-0.9, 0.85, gl), lerp(0.0, -0.25, gl))
    expr = ("nervous_smile", "nervous_smile", 1.0)
    kw = dict(pose=P_SWALK, pose_t=t - t0, expr=expr, look=look, face=face, turn=-1.0, blush=0.6, sweat=0.6,
              glint=0.0, mouth=(0.0, 0.0))
    return x, 1600.0, kw, {"rec": "pocket"}


# ----------------------------------------------------------------------------
# Tiredness in the doorway
# ----------------------------------------------------------------------------
def _tired_door(t, k, info):
    turn = -0.42
    x = TIR_X0
    op = _door(t, k)
    # l hand on the inside edge of the door (he holds it), r arm hangs: bandage visible
    pose = {"base": "stand", "hunch": 0.2, "al_p": 0.06, "al_o": 0.1, "al_e": 0.25,
            "ar_p": 0.16, "ar_o": 0.12, "ar_e": 0.42}
    if t >= k["dc0"] - 0.3:
        # takes the door edge and leans to the closing gap, keeping one eye on Emb
        lean_k = smoothstep(seg(t, k["dc0"], k["dc1"]))
        x = lerp(TIR_X0, 1690.0, lean_k)
        ex = _door_edge_x(op)
        hx = (ex + 4 - x) / SH
        hold = smoothstep(seg(t, k["dc0"] - 0.3, k["dc0"]))
        pose = (pose, dict(pose, side=-0.12 * lean_k, tilt=-0.1 * lean_k,
                           **ikw("tired", "l", hx, -470, turn, 0.04, h="grip", layer="back", wa=-1.5, wabs=0.4)),
                hold)
    at_emb = (-0.78, -0.12)
    lk = [(0.0, at_emb), (k["look"] + 0.12, at_emb), (k["look"] + 0.29, (0.42, 0.95)),   # -> bandage
          (k["look"] + 0.62, (0.42, 0.95)), (k["look"] + 0.79, at_emb)]                    # -> back to Emb
    look = tween(t, lk)
    face = {}
    # head follows the eyes ~0.15 s later
    hdn = tween(t, [(k["look"] + 0.25, 0.0), (k["look"] + 0.47, 0.14), (k["look"] + 0.75, 0.14),
                    (k["look"] + 0.97, 0.0)])
    face["head_nod"] = hdn
    face["head_turn"] = 0.12 * hdn / 0.14
    face["head_tilt"] = 0.08 * smoothstep(seg(t, k["look"] + 0.92, k["look"] + 1.22)) * \
        (1 - smoothstep(seg(t, k["L3e"] + 0.1, k["L3e"] + 0.4)))
    # one brow lifts a hair on "A normal friend visit!"; drops on "How's the arm"
    face["brow_r"] = 0.28 * seg(t, k["w1"][9], k["w1"][9] + 0.3) * (1 - seg(t, k["w2"][7], k["w2"][7] + 0.35))
    face["lid"] = 0.06 * seg(t, k["w2"][3], k["w2"][3] + 0.3) * (1 - seg(t, k["look"], k["look"] + 0.2))
    face["press"] = 0.25 * seg(t, k["L3e"], k["L3e"] + 0.2)
    blink = None
    if k["w1"][2] - 0.05 <= t < k["w1"][2] + 0.95:
        blink = _slow_blink(t, k["w1"][2] + 0.05)       # slow judgement blink at "Just checking in!"
    expr = "bored"
    if t >= k["turn0"]:
        # watch Emb turn and stumble; then the recorder
        rec_look = (-0.42, 0.92)
        look = tween(t, [(k["turn0"], at_emb), (k["trip"] + 0.1, (-0.95, 0.1)), (k["pop"] + 0.08, (-0.6, -0.35)),
                         (k["land"] - 0.02, rec_look)], ease_out)
        face["lid"] = tween(t, [(k["land"] - 0.1, 0.0), (k["land"] + 0.02, -0.09), (k["both"] + 0.35, -0.09),
                                (k["both"] + 0.75, 0.07)])          # small surprise -> lids LOWER: he gets it
        face["press"] = 0.3 * seg(t, k["both"] + 0.35, k["both"] + 0.75)
        face["head_nod"] = 0.08 * seg(t, k["land"], k["land"] + 0.2)
        if t >= k["L4"]:
            look = tween(t, [(k["L4"], rec_look), (k["grab"] + 0.05, (-0.55, 0.85)), (k["up"] + 0.05, (-0.75, -0.25)),
                             (k["up"] + 0.35, (-0.72, -0.12))])
            face["head_nod"] = 0.08 * (1 - seg(t, k["grab"], k["up"] + 0.2))
            # pretend: pupils to the pocket, hold, back to his face
            pocket_look = (-0.88, 0.42)
            if t >= k["pretend"] - 0.1:
                look = tween(t, [(k["pretend"] - 0.1, (-0.72, -0.12)), (k["pretend"] + 0.08, pocket_look),
                                 (k["L5"] - 0.02, pocket_look), (k["L5"] + 0.16, (-0.74, -0.1))])
            fnod = 0.07 * math.sin(math.pi * seg(t, k["L5"] + 0.25, k["cool_end"] + 0.2))
            face["head_nod"] += fnod
            face["brow_l"] = 0.22 * seg(t, k["L5"] + 0.2, k["L5"] + 0.45) * (1 - seg(t, k["L5e"], k["L5e"] + 0.4))
            face["press"] = 0.3 * (1 - seg(t, k["L5"], k["L5"] + 0.1)) + 0.35 * seg(t, k["cool_end"], k["cool_end"] + 0.2)
            if k["cool_end"] + 0.15 <= t < k["cool_end"] + 1.1:
                blink = _slow_blink(t, k["cool_end"] + 0.2, 0.35, 0.2, 0.4)
        if t >= k["L5e"]:
            # watches Emb walk off; eyes narrow as the door closes
            look = tween(t, [(k["L5e"], (-0.74, -0.1)), (k["sh10"] + 0.2, (-1.0, 0.05)), (k["dc1"], (-1.0, 0.12))])
            nk = smoothstep(seg(t, k["dc0"] - 0.3, k["dc1"] + 0.15))
            face = {"lid": 0.07 - 0.03 * nk, "lower": 0.32 * nk, "brow": -0.22 * nk, "brow_ang": -0.25 * nk,
                    "press": 0.35, "head_turn": 0.3 * nk}
            if t >= k["dc1"] + 0.2:
                face["look_x"] = -0.1
    # looking down drops his heavy lids: keep the iris readable
    face["lid"] = face.get("lid", 0.0) - 0.13 * clamp((look[1] - 0.3) / 0.6)
    kw = dict(pose=pose, expr=expr, look=look, face=face, turn=turn, blink=blink,
              mouth=info.mouth("tired", t), headphones="neck", bandage=True)
    return x, TIR_Y, kw


# ----------------------------------------------------------------------------
# porch world drawing
# ----------------------------------------------------------------------------
def _rec_air(t, k):
    p0 = (EMB_X0 - 44.0, 1176.0)
    p1 = REC_REST
    if t < k["land"]:
        u = seg(t, k["pop"], k["land"])
        x = lerp(p0[0], p1[0] - 6, u)
        y = lerp(p0[1], p1[1], u * u) - 210 * math.sin(math.pi * u) * (1 - u * 0.25)
        return x, y, -u * math.tau * 1.6
    u = seg(t, k["land"], k["land"] + 0.18)
    hop = 16 * math.sin(math.pi * u)
    x = lerp(p1[0] - 6, p1[0], ease_out(u))
    rot = lerp(0.6, 0.14, ease_out(u))
    return x, p1[1] - hop, rot


def _draw_porch(ctx, t, k, info):
    op = _door(t, k)
    sets.house_exterior(ctx, t, "back")
    tx, ty, tkw = _tired_door(t, k, info)
    ta = None
    if op > 0.03:
        ta = human.draw_person(ctx, "tired", tx, ty, SH, t, **tkw)
    sets.house_exterior(ctx, t, "house", door_open=op)
    sets.house_exterior(ctx, t, "fg", door_open=op, parts=("door",))
    if ta is not None and t >= k["dc0"] and op < 0.6:
        # his fingers curled round the door edge
        ex = _door_edge_x(op)
        for i in range(4):
            fy = 1192 + i * 11
            core.ellipse(ctx, ex - 1, fy, 6.5, 5.2)
            core.fill_stroke(ctx, core.PAL["t_skin"], INK, 2.2)
    bunch = ease_out_back(seg(t, k["trip"] - 0.02, k["trip"] + 0.16)) if t >= k["trip"] - 0.02 else 0.0
    props.doormat(ctx, MAT[0], MAT[1], MAT[2], bunch=bunch)
    ex_, ey_, ekw, flags = _emb(t, k, info)
    ea = human.draw_person(ctx, "embar", ex_, ey_, SH, t, **ekw)
    if flags["rec"] == "pocket":
        px, py = ea["pocket"]
        rs = SH * 1.7                      # only_led draws at the device's LED spot (+30, -12)*s: re-centre
        props.recorder(ctx, px - 30 * rs, py + 12 * rs, rs, t, led=_led(t), glow=1.0, only_led=True)
    elif flags["rec"] == "hand":
        hx, hy, ang = ea["hand_r"]
        props.recorder(ctx, hx + 4, hy - 14, SH * 1.0, t, led=_led(t, k["land"]), glow=0.6, rot=-0.08)
    else:
        rx, ry, rr = _rec_air(t, k)
        props.recorder(ctx, rx, ry, SH * 0.95, t, led=_led(t, k["land"]), glow=0.8 if t >= k["land"] else 0.3,
                       rot=rr)
        if k["land"] <= t < k["land"] + 0.28:
            _impact_ticks(ctx, REC_REST[0], REC_REST[1] + 10, SH * 1.4, seg(t, k["land"], k["land"] + 0.28))
    return ea, ta


def _impact_ticks(ctx, x, y, s, u):
    a = 1 - u
    for i, ang in enumerate((-2.5, -1.9, -1.25, -0.65)):
        r0, r1 = (34 + 40 * u) * s, (58 + 52 * u) * s
        ctx.move_to(x + math.cos(ang) * r0, y + math.sin(ang) * r0 * 0.8)
        ctx.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1 * 0.8)
        core.stroke(ctx, core.alpha(INK, a), 6 * s)


# ----------------------------------------------------------------------------
# insert: the recorder lands on the GO AWAY mat
# ----------------------------------------------------------------------------
def _insert_bg(c):
    core.vgradient(c, "#6a4a3a", "#3a2a26", 0, 0, 1080, 520)       # dim hall floor through the doorway
    c.rectangle(0, 300, 1080, 70)
    core.fill(c, "#f4eee0")                                        # threshold
    c.move_to(0, 300); c.line_to(1080, 300)
    core.stroke(c, INK, 5)
    # porch boards in perspective
    c.rectangle(0, 370, 1080, 1550)
    core.fill(c, "#d9cdb8")
    yy = 370.0
    for i in range(9):
        yy += 60 + i * 26
        c.move_to(-20, yy); c.line_to(1100, yy)
        core.stroke(c, "#b8a888", 4)
    for i in range(-6, 8):
        c.move_to(540 + i * 70, 370); c.line_to(540 + i * 230, 1920)
        core.stroke(c, (0.72, 0.66, 0.53, 0.35), 3)
    c.move_to(0, 370); c.line_to(1080, 370)
    core.stroke(c, INK, 4)


def _draw_insert(ctx, t, k):
    core.cached(ctx, "s10_ins_bg", 0, 0, 1080, 1920, _insert_bg)
    # his sweatpant cuffs + fuzzy slippers on the threshold (top right)
    for sx in (690, 820):
        core.poly(ctx, [(sx - 52, -20), (sx + 52, -20), (sx + 56, 318), (sx - 56, 318)])
        core.fill_stroke(ctx, core.PAL["t_pants"], INK, 5)
    for i, sx in enumerate((690, 820)):
        core.ellipse(ctx, sx, 330, 70, 40)
        core.fill_stroke(ctx, core.PAL["t_slipper"], INK, 5)
        core.ellipse(ctx, sx + 6, 316, 46, 20)
        core.fill(ctx, "#a9cdf3")
    props.doormat(ctx, 540, 1030, 1.9, bunch=0.7, rot=-0.02)
    # the recorder drops in from the top, lands, hops, settles
    tl = k["land"]
    if t < tl:
        u = seg(t, k["ins0"], tl)
        x, y, rot, sq = lerp(620, 525, u), lerp(-80, 800, u * u), -2.2 * (1 - u), 1.0
    else:
        u = seg(t, tl, tl + 0.2)
        hop = 70 * math.sin(math.pi * u)
        x, y = lerp(525, 548, ease_out(u)), 800 - hop
        rot = lerp(0.5, 0.12, ease_out(u))
        sq = 1 - 0.18 * math.sin(math.pi * seg(t, tl, tl + 0.07))
    # contact shadow
    if t >= tl - 0.05:
        core.ellipse(ctx, x, 878, 150, 24)
        core.fill(ctx, (0.11, 0.08, 0.15, 0.25))
    with core.saved(ctx, x, y + 70, (1.0 / sq ** 0.5, sq)):
        props.recorder(ctx, 0, -70, 2.9, t, led=_led(t, tl), glow=0.9, rot=rot)
    if tl <= t < tl + 0.3:
        _impact_ticks(ctx, 548, 850, 2.4, seg(t, tl, tl + 0.3))
    fx.vignette(ctx, 0.35, inner=0.6)


# ----------------------------------------------------------------------------
# bedroom (dusk), screen inserts, monitor-lit face
# ----------------------------------------------------------------------------
def _dim(ctx, a, col=(0.10, 0.07, 0.16)):
    ctx.save()
    ctx.identity_matrix()
    ctx.rectangle(0, 0, 4000, 4000)
    ctx.set_source_rgba(col[0], col[1], col[2], a)
    ctx.fill()
    ctx.restore()


def _screen_glow_col(t, k):
    sk = seg(t, k["t_site"] + 0.2, k["t_site"] + 0.6)
    return core.mixc("#e6f0ff", "#a6e2dc", sk)


def _draw_bedroom(ctx, t, k, info):
    sx, sy = BM["chair_seat"]
    dxc = 60
    sets.bedroom(ctx, t, "bg", light_on=False, chair_dx=dxc,
                 screen_fn=lambda c, tt: _search(c, 0, 0, 640, 400, tt, k))
    gy = human.ground_from_seat("tired", sy, SB)
    ty_ = (gy - 1100) / SB / H_T
    pose = {"base": "type", "al_ty": ty_, "ar_ty": ty_, "al_tz": 0.32, "ar_tz": 0.32, "lean": 0.12,
            "neck": 0.06, "nod": 0.0}
    scan = 0.25 * math.sin((t - k["S"]) * 5.0)
    human.draw_person(ctx, "tired", sx + dxc, gy, SB, t, pose=pose, pose_t=t - k["S"], expr="bored", turn=1.0,
                      headphones="neck", bandage=True, look=(0.9, -0.15 + 0.05 * scan),
                      face={"lid": 0.02})
    sets.bedroom(ctx, t, "fg", parts=("desk", "chair"), chair_dx=dxc)
    _dim(ctx, 0.42)
    with sets.bedroom_monitor_space(ctx) as c:
        _search(c, 0, 0, 640, 400, t, k)
    ctx.save()
    ctx.set_operator(core.cairo.OPERATOR_SCREEN)
    core.radial_glow(ctx, 1950, 900, 520, _screen_glow_col(t, k), 0.28)
    ctx.restore()


def _monitor_insert(ctx, t, k, push=1.0, focus=(495, 660)):
    core.cached(ctx, "s10_mon_bg", 0, 0, 1080, 1920, _mon_bg)
    with core.camera(ctx, focus[0], focus[1], push, 0, focus[0], focus[1]):
        # bezel
        core.rrect(ctx, 40, 300, 910, 690, 34)
        core.fill_stroke(ctx, "#1f1b29", INK, 6)
        core.rrect(ctx, 52, 312, 886, 666, 26)
        core.fill(ctx, "#2b2638")
        _search(ctx, 70, 330, 850, 630, t, k)
        core.rrect(ctx, 70, 330, 850, 630, 22)
        core.stroke(ctx, INK, 5)
        # small power LED + stand
        core.circle(ctx, 905, 980, 6)
        core.fill(ctx, "#7af0a0")


def _mon_bg(c):
    core.vgradient(c, "#2a2140", "#171222", 0, 0, 1080, 1920)
    core.radial_glow(c, 495, 650, 720, "#9fc8ff", 0.22)
    # monitor neck + base
    core.poly(c, [(450, 990), (540, 990), (560, 1150), (430, 1150)])
    core.fill_stroke(c, "#241f30", INK, 5)
    core.ellipse(c, 495, 1160, 230, 34)
    core.fill_stroke(c, "#241f30", INK, 5)
    # desk edge + RGB keyboard strip
    c.rectangle(0, 1170, 1080, 750)
    core.fill(c, "#2c2236")
    c.move_to(0, 1170); c.line_to(1080, 1170)
    core.stroke(c, INK, 5)
    core.rrect(c, 160, 1215, 680, 70, 14)
    core.fill_stroke(c, "#1b1724", INK, 4)
    for i, col in enumerate(("#ff6fae", "#8f7bff", "#46d0ff", "#7af0a0", "#ffd45e")):
        core.rrect(c, 182 + i * 128, 1268, 120, 8, 4)
        core.fill(c, core.alpha(col, 0.7))


def _pov_bg(c):
    """Dark bedroom behind him, seen from the monitor: chair back, string lights, window."""
    core.vgradient(c, "#2b2440", "#18121f", 0, 0, 1080, 1920)
    # window (dusk) up left
    core.rrect(c, -40, 180, 330, 420, 10)
    core.fill_stroke(c, "#3e4f86", INK, 5)
    c.move_to(125, 180); c.line_to(125, 600)
    c.move_to(-40, 390); c.line_to(290, 390)
    core.stroke(c, INK, 5)
    core.radial_glow(c, 125, 380, 260, "#8ea6ff", 0.18)
    # string lights (soft bokeh)
    for i in range(9):
        x = 60 + i * 120
        y = 150 + 40 * math.sin(i * 0.9)
        col = ("#ffd27a", "#ff8fb8", "#8fe0ff")[i % 3]
        core.radial_glow(c, x, y, 46, col, 0.45)
        core.circle(c, x, y, 9)
        core.fill(c, core.alpha(col, 0.85))
    # gaming chair back
    core.rrect(c, 230, 420, 620, 1200, 150)
    core.fill_stroke(c, "#2d2540", INK, 7)
    core.rrect(c, 330, 500, 420, 1100, 110)
    core.fill(c, "#6a4fb8")
    core.rrect(c, 395, 560, 290, 1000, 80)
    core.fill(c, "#7c63cc")


def _draw_pov(ctx, t, k, info, push):
    core.cached(ctx, "s10_pov_bg", 0, 0, 1080, 1920, _pov_bg)
    with core.camera(ctx, 540, 820, push, 0, 540, 820):
        s = 2.55
        gx, gy = 545, 2270
        lift = smoothstep(seg(t, k["lift"], k["lift"] + 0.45))
        lean = 0.1 + 0.06 * seg(t, k["w6"][5], k["w6"][6]) - 0.12 * lift
        pose = {"base": "sit_chair", "lean": lean, "hunch": 0.35 - 0.25 * lift, "neck": 0.1 - 0.1 * lift,
                "nod": -0.04 - 0.04 * lift, "al_p": 0.2, "ar_p": 0.2, "al_e": 0.5, "ar_e": 0.5}
        # reading: pupils scan in small steps; on "record me?" they stop and look up into the screen
        ph = (t - k["b3"]) * 1.6
        scan_x = -0.35 + 0.7 * (ph % 1.0) if t < k["w6"][5] else 0.0
        look = (scan_x * (1 - lift), 0.18 - 0.2 * lift)
        expr = state_at(t, [(-1, "bored"), (k["lift"], "determined")], 0.4)
        face = {"lid": 0.06 * seg(t, k["w6"][5], k["w6"][6]) + 0.1 * lift,  # determined lid ~0.2, not fully open
                "brow": -0.12 * seg(t, k["w6"][5], k["w6"][6]),
                "brow_in": -0.15 * seg(t, k["w6"][5], k["w6"][6]),
                "press": 0.3 * lift, "head_nod": -0.03 * lift}
        blink = None
        if k["b5"] + 0.08 <= t < k["lift"]:
            blink = _slow_blink(t, k["b5"] + 0.08, 0.28, 0.12, 0.3)
        human.draw_person(ctx, "tired", gx, gy, s, t, pose=pose, expr=expr, look=look, face=face, turn=0.08,
                          headphones="neck", bandage=True, mouth=info.mouth("tired", t), blink=blink, shadow=False)
    # monitor light from the camera side: cool wash on the face
    ctx.save()
    ctx.set_operator(core.cairo.OPERATOR_SCREEN)
    core.radial_glow(ctx, 540, 760, 700, _screen_glow_col(t, k), 0.2)
    ctx.restore()
    fx.vignette(ctx, 0.55, inner=0.55)


# ----------------------------------------------------------------------------
# shots
# ----------------------------------------------------------------------------
def _shot(t, k):
    seq = [(-1.0, "s1"), (k["sh2"], "s2"), (k["sh3"], "s3"), (k["sh4"], "s4"), (k["look"], "s5"),
           (k["L3e"], "s6"), (k["ins0"], "ins"), (k["ins1"], "s8"), (k["pretend"], "s9"),
           (k["sh10"], "s10"), (k["sh11"], "s11"), (k["S"], "b1"), (k["b2"], "b2"), (k["b3"], "b3"),
           (k["b4"], "b4"), (k["b5"], "b5")]
    cur, t0 = seq[0][1], 0.0
    nxt = k["end"]
    for i, (ts, name) in enumerate(seq):
        if t >= ts:
            cur, t0 = name, ts
            nxt = seq[i + 1][0] if i + 1 < len(seq) else k["end"]
    return cur, t0, nxt


def _porch_cam(name, t, t0, t1, k):
    u = seg(t, t0, t1)
    if name == "s1":
        return (1540, 1210, lerp(2.02, 2.14, ease_in_out(u)))
    if name == "s2":
        return (1450, 1150, lerp(3.5, 3.62, u))
    if name == "s3":
        return (1546, 1222, 2.18)
    if name == "s4":
        return (1448, 1128, lerp(3.8, 4.0, ease_in_out(u)))
    if name == "s5":
        return (1612, 1168, lerp(3.2, 3.32, u))
    if name == "s6":
        return (1528, 1322, 2.0)
    if name == "s8":
        zk = ease_in_out(seg(t, t0, k["L4"]))
        z = lerp(2.0, 2.28, zk)
        z = lerp(z, 2.12, ease_in_out(seg(t, k["L4"], k["up"] + 0.3)))
        cy = 1478 - 330 / z
        return (1530, cy, z)
    if name == "s9":
        return (1624, 1150, lerp(3.6, 3.75, u))
    if name == "s10":
        return (lerp(1468, 1340, ease_in_out(u)), 1330, 1.5)
    if name == "s11":
        return (1652, 1125, lerp(3.3, 3.5, u))
    return (1540, 1210, 2.1)


def render(ctx, t, info):
    k = keys(info)
    name, t0, t1 = _shot(t, k)
    if name.startswith("s"):
        cam = _porch_cam(name, t, t0, t1, k)
        with core.camera(ctx, *cam):
            _draw_porch(ctx, t, k, info)
    elif name == "ins":
        _draw_insert(ctx, t, k)
    elif name == "b1":
        with core.camera(ctx, 1745, 1035, lerp(1.85, 1.95, seg(t, t0, t1))):
            _draw_bedroom(ctx, t, k, info)
    elif name == "b2":
        _monitor_insert(ctx, t, k, lerp(1.0, 1.05, seg(t, t0, t1)), (495, 640))
    elif name == "b3":
        _draw_pov(ctx, t, k, info, lerp(1.0, 1.06, seg(t, t0, t1)))
    elif name == "b4":
        _monitor_insert(ctx, t, k, lerp(1.04, 1.16, ease_in_out(seg(t, t0, t1))), (300, 800))
    elif name == "b5":
        _draw_pov(ctx, t, k, info, lerp(1.04, 1.22, ease_in_out(seg(t, t0, k["end"]))))


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    k = keys(info)
    ev = [(0.0, "knock", 3.0, 0.1),
          (k["open0"] - 0.02, "latch_click", 1.0, 0.15),
          (k["sh4"] + 0.08, "cloth_rustle", -1.0),
          (k["turn0"] + 0.05, "cloth_rustle", -2.0),
          (k["trip"], "footstep", 1.0, -0.2),
          (k["trip"] + 0.05, "whoosh", -12.0, -0.2),
          (k["pop"] + 0.16, "footstep", -1.0, -0.3),
          (k["land"], "puzzle_click", 4.0),
          (k["land"] + 0.18, "key_clack", 2.0),
          (k["grab"] - 0.12, "whoosh", -13.0),
          (k["grab"], "cloth_rustle", -1.0),
          (k["stuff0"] + 0.18, "cloth_rustle", -2.0),
          (k["dc2"], "latch_click", 3.0, 0.2),
          (k["dc2"] + 0.01, "door_bang", -16.0, 0.2),
          (k["S"] + 0.05, "chair_creak", -6.0, 0.2)]
    # Emb's stiff footsteps on the path while walking off
    for i in range(3):
        ev.append((k["sh10"] + 0.15 + i * 0.5, "footstep", -6.0, -0.35))
    # typing HUSHCORP + Enter, mouse click on the result
    for i, tt in enumerate(fx.type_times(k["t_type"], "HUSHCORP", k["char_dt"])):
        ev.append((tt, "key_clack", -3.0, 0.15))
    ev.append((k["t_type"] + 8 * k["char_dt"] + 0.08, "key_clack", 1.0, 0.15))
    ev.append((k["t_results"] + 0.95, "mouse_click", 0.0, 0.15))
    return ev
