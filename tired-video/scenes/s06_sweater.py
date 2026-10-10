"""s06 -- "Act natural" (the sweater). Bedroom, music "awkward".

Continues s05: Embarrassment sits dazed on the floor, Tiredness stands over him
(arms crossed, headphones round his neck, foot tapping). The thing sits on the
desk grooming. Emb zips to the desk and throws a sweater over it, then lies.

Shot list (all times come from cues / line words, never hard-coded):
  A  wide_spot     spot          wide two-shot; the thing grooms on the desk; Emb's
                                 pupils, then head, slide past Tiredness to it
  A2 thing_insert  spot+40%      insert: the thing licking its paw; it looks up
  B  emb_floor_cu  spot+72%      Emb close: eyes widened a hair on the desk, then
                                 snap to Tiredness + forced smile
  C  wide_tele     teleport+.2   smear zip floor -> desk, stretch/squash/settle,
                                 sweater flops over the thing; Tiredness keeps
                                 staring at the empty floor, then pupils -> head ->
                                 body turn, LATE and slow (s06_l01 plays here);
                                 slow push-in
  D  emb_med       before l02    "How's... everything? I mean... uhhh..." darts
  E  tired_med     rollEyes-.1   slow eye roll, roll_hand "go on", s06_l03 with one
                                 brow up a hair; eyes flick to the sweater on
                                 "research" and back; slow push-in
  F  emb_cu        "research"+.5 the lump stirs, his eyes dart to it; s06_l04 face
                                 flips nervous_smile -> panic -> fake_cool (+glint)
  H  emb_gesture   l05-.1        casual lean, free hand: "walking by", knock mime
  I  two_shot2     l05 "and"     shrug "nobody answered", "let myself in";
                                 Tiredness's 0.1 lid drop + lip press
  J  lump_med      shift         the lump shifts (ears under the knit), he goes
                                 rigid; jerk: arms pop up and slam it down
  K  tired_ecu     jerk+.3       THE beat: pupils slide down to the sweater, hold,
                                 slide back up. Head and eyes rock-still otherwise.
  L  emb_plead     l06+.3        pleading, hand on heart, other hand on the lump
  M  tired_close   l06 "I'm"     long look (no blinks), one very slow blink on
                                 "stare", tiny exhale, "...Sure."; slow push-in
Cut list: _shot(); camera framings: _camera().
"""
import math

from engine import core, sets, props, fx
from engine.core import (tween, state_at, seg, clamp, lerp, smoothstep, ease_out_back,
                         ease_in_out, ease_out, hash01)
from engine.human import draw_person
from engine.creatures import draw_thing, draw_sweater_lump

M = sets.BEDROOM_MARKS
CS = M["char_scale"]                     # 0.75: people in the bedroom

# ---- stage marks (bedroom world px) -----------------------------------------
EMB_FLOOR = (1180.0, 1570.0)             # sit_floor butt point (s05 landing)
TIRED = (1480.0, 1545.0)                 # Tiredness stands here all scene
EMB_DESK = (1810.0, 1423.0)              # Emb leaning over the desk
LUMP = (M["sweater_spot"][0] + 40, M["desk_top_y"])    # sweater heap on the desk (right of his hands)
THING = (M["desk_critter"][0], M["desk_top_y"] - 2)
THING_S = 0.82
LUMP_S = 1.05
CAGE = (985.0, 1602.0)                   # the cage he dropped (from s05)
ROOM = dict(door_open=1.0, closet_open=1.0, laundry_scattered=True, chair_empty=True,
            frame_fallen=True)

# look targets (screen-space gaze vectors), measured from the head anchors
T_LOOK_EMB_FLOOR = (-0.78, 0.48)         # Tiredness -> Emb on the floor
T_LOOK_EMB_DESK = (0.86, -0.18)          # Tiredness -> Emb at the desk
T_LOOK_LUMP = (0.7, 0.44)                # Tiredness -> the sweater (lids follow; keep the iris readable)
E_LOOK_TIRED = (-0.88, 0.12)             # Emb (desk) -> Tiredness
E_LOOK_LUMP = (0.3, 0.85)                # Emb (desk) -> the lump
E_LOOK_AWAY = [(-0.35, -0.75), (0.45, -0.6), (-0.6, 0.55), (0.1, -0.85)]

COVER_TY = 0.47                          # hand height (fraction) = top of the lump
COVER = {"base": "cover_sweater", "al_ty": COVER_TY, "ar_ty": COVER_TY}


# =============================================================================
# timing
# =============================================================================
_TC = {}


def _word(info, lid, i):
    """Start time of word i of line lid (from the lip-sync data; proportional fallback)."""
    l = info.line(lid)
    env = (getattr(info, "_lip", None) or {}).get(lid) or {}
    ws = env.get("word_starts")
    if ws:
        return l.start + ws[max(0, min(i, len(ws) - 1))]
    n = max(1, len(l.text.split()))
    return l.start + l.dur * min(i, n - 1) / n


def _times(info):
    key = (id(info), info.dur)
    if key in _TC:
        return _TC[key]
    c = info.cue
    T = dict(spot=c("spot"), tele=c("teleport"), rollEyes=c("rollEyes"), rollHand=c("rollHand"),
             shift=c("shift"), jerk=c("jerk"), stare=c("stare"), end=info.dur)
    for i in range(1, 8):
        lid = "s06_l%02d" % i
        T["l%d" % i] = c(lid)
        T["l%de" % i] = c(lid + ".end")
    w = lambda lid, i: _word(info, lid, i)
    # key words
    T["l01_um"] = w("s06_l01", 2)
    T["l02_mean"] = w("s06_l02", 2)
    T["l02_uh"] = w("s06_l02", 4)
    T["research"] = w("s06_l03", 4)
    T["l03_hows"] = w("s06_l03", 1)
    T["oh"] = w("s06_l04", 0)
    T["yeah1"] = w("s06_l04", 1)
    T["ithink"] = w("s06_l04", 4)
    T["yeah2"] = w("s06_l04", 6)
    T["no"] = w("s06_l04", 7)
    T["wait"] = w("s06_l04", 8)
    T["good2"] = w("s06_l04", 9)
    T["walking"] = w("s06_l05", 3)
    T["knocked"] = w("s06_l05", 7)
    T["and2"] = w("s06_l05", 8)
    T["nobody"] = w("s06_l05", 9)
    T["soI"] = w("s06_l05", 11)
    T["letme"] = w("s06_l05", 13)
    T["please2"] = w("s06_l06", 4)
    T["really"] = w("s06_l06", 6)
    T["imsorry"] = w("s06_l06", 10)
    T["please3"] = w("s06_l06", 12)
    # derived beats
    T["glance"] = T["spot"] + 0.1                      # Emb's pupils leave Tiredness
    spot_len = max(0.6, T["tele"] - T["spot"])
    T["cut_a2"] = T["spot"] + 0.4 * spot_len           # insert: the thing grooming on the desk
    T["cut_b"] = T["spot"] + 0.72 * spot_len           # back on Emb
    T["smile"] = T["cut_b"] + 0.22                     # eyes held on the desk, then a forced smile
    T["zip"] = max(T["tele"] + 0.2, T["smile"] + 0.42)  # ...and he zips
    T["t_look"] = T["zip"] + 0.5                       # Tiredness's LATE pupils
    T["t_head"] = T["t_look"] + 0.15                   # head follows (slowly)
    T["t_body"] = T["t_head"] + 0.35                   # body last
    T["cut_d"] = max(T["l1e"] + 0.13, min(T["t_body"] + 0.6, T["l2"] - 0.04))
    T["cut_e"] = T["rollEyes"] - 0.1
    T["roll_hand_on"] = T["rollHand"] + 0.22
    T["cut_f"] = min(T["research"] + 0.5, T["l4"] - 0.3)   # Emb's reaction, then l04 in the same CU
    T["cut_h"] = T["l5"] - 0.1
    T["cut_i"] = T["and2"]
    T["cut_j"] = T["shift"]
    T["cut_k"] = T["jerk"] + 0.3
    T["slide_dn"] = T["cut_k"] + 0.08
    T["slide_up"] = T["slide_dn"] + 0.68
    T["cut_l"] = max(T["l6"] + 0.3, T["slide_up"] + 0.42)
    T["cut_m"] = T["imsorry"]
    T["blink0"] = T["stare"] + 0.04
    T["exhale"] = T["blink0"] + 0.92
    _TC.clear()
    _TC[key] = T
    return T


def _shot(t, T):
    shots = [(0.0, "wide_spot"), (T["cut_a2"], "thing_insert"), (T["cut_b"], "emb_floor_cu"),
             (T["zip"], "wide_tele"),
             (T["cut_d"], "emb_med"), (T["cut_e"], "tired_med"), (T["cut_f"], "emb_cu"),
             (T["cut_h"], "emb_gesture"), (T["cut_i"], "two_shot2"),
             (T["cut_j"], "lump_med"), (T["cut_k"], "tired_ecu"), (T["cut_l"], "emb_plead"),
             (T["cut_m"], "tired_close")]
    cur, t0, nxt = shots[0][1], 0.0, T["end"]
    for i, (ts, name) in enumerate(shots):
        if t >= ts:
            cur, t0 = name, ts
            nxt = shots[i + 1][0] if i + 1 < len(shots) else T["end"]
    return cur, t0, nxt


# =============================================================================
# small helpers
# =============================================================================
def _ramp(t, t0, dur, a=0.0, b=1.0, ease=smoothstep):
    return lerp(a, b, ease(seg(t, t0, t0 + dur)))


def _bump(t, t0, t_in, hold, t_out, ease=smoothstep):
    """0 -> 1 over t_in, hold, -> 0 over t_out."""
    if t < t0:
        return 0.0
    if t < t0 + t_in:
        return ease(seg(t, t0, t0 + t_in))
    if t < t0 + t_in + hold:
        return 1.0
    return 1.0 - ease(seg(t, t0 + t_in + hold, t0 + t_in + hold + t_out))


def _addf(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _scale(d, k):
    return {kk: v * k for kk, v in d.items()}


def _darts(t, t0, t1, targets, seed, step=0.36, home=None, home_every=2):
    """Nervous eye darts: quick saccades between targets, every ~step s.
    Every `home_every`-th fixation returns to `home` (the person he talks to)."""
    if t < t0 or t > t1:
        return None
    u = (t - t0) / step
    k = int(math.floor(u))

    def tgt(j):
        if j < 0:
            return home if home is not None else targets[0]
        if home is not None and j % home_every == 0:
            return home
        return targets[int(hash01(j, seed) * len(targets)) % len(targets)]

    f = u - k
    m = smoothstep(seg(f, 0.0, 0.22))
    a, b = tgt(k - 1), tgt(k)
    return (lerp(a[0], b[0], m), lerp(a[1], b[1], m))


def _lerp2(a, b, k):
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


# =============================================================================
# character performances (shot-independent: continuity across cuts is free)
# =============================================================================
def _tired(t, T, info):
    """Kwargs for draw_person('tired', ...)."""
    x, y = TIRED
    # ---------------- pose
    keys = [(-1.0, "tap_foot"), (0.42, "arms_crossed"), (T["roll_hand_on"], "roll_hand"),
            (T["l3"] + 0.42, "arms_crossed")]
    pose = state_at(t, keys, 0.3)
    pose_t = t
    if T["roll_hand_on"] - 0.4 <= t < T["l3"] + 1.0:
        pose_t = t - T["roll_hand_on"] + 0.15
    # the stare: a tiny breath in, then the exhale (shoulders sink)
    ex = _bump(t, T["exhale"], 0.16, 0.1, 0.55)
    if t >= T["exhale"] - 0.45:
        inh = _bump(t, T["exhale"] - 0.4, 0.3, 0.1, 0.2)
        settle = smoothstep(seg(t, T["exhale"], T["exhale"] + 0.45))
        pose = {"base": "arms_crossed", "hunch": 0.15 + 0.14 * inh - 0.1 * settle, "nod": 0.04 * ex}
    # the ECU: no breathing bob or sway, so the head is rock-still and only the pupils
    # travel (switched while he is off-screen, in the shots either side of it)
    if T["cut_k"] - 0.45 <= t < T["cut_l"] + 0.05:
        pose = {"base": "arms_crossed", "breath": 0.0, "sway": 0.0}
    # ---------------- body turn: faces Emb on the floor (left), then the desk (right)
    turn = tween(t, [(T["t_body"], -0.6), (T["t_body"] + 0.55, 0.62)], ease_in_out)
    # head turn leads the body (late and slow)
    ht = tween(t, [(T["t_head"], 0.0), (T["t_head"] + 0.62, 1.0)], ease_in_out)
    ht -= (turn + 0.6) / 1.22 * 1.0           # body catches up: the net head yaw keeps going
    ht = max(ht, 0.0) if t > T["t_head"] else 0.0
    # ---------------- gaze
    look = T_LOOK_EMB_FLOOR
    look = _lerp2(look, T_LOOK_EMB_DESK, ease_in_out(seg(t, T["t_look"], T["t_look"] + 0.24)))
    # eye roll: up-right, over the top, up-left, lids sinking, back to Emb
    r0 = T["rollEyes"]
    if r0 - 0.05 <= t < r0 + 1.15:
        look = tween(t, [(r0, T_LOOK_EMB_DESK), (r0 + 0.22, (0.85, -1.05)), (r0 + 0.45, (0.0, -1.22)),
                         (r0 + 0.68, (-0.75, -0.85)), (r0 + 1.05, T_LOOK_EMB_DESK)], ease_in_out)
    # flick to the sweater on "research"
    fr = _bump(t, T["research"] + 0.02, 0.09, 0.32, 0.11)
    look = _lerp2(look, T_LOOK_LUMP, fr)
    # THE beat: down to the sweater, hold, back up
    if t >= T["slide_dn"] - 0.01:
        k = ease_in_out(seg(t, T["slide_dn"], T["slide_dn"] + 0.3)) * \
            (1.0 - ease_in_out(seg(t, T["slide_up"], T["slide_up"] + 0.28)))
        look = _lerp2(T_LOOK_EMB_DESK, T_LOOK_LUMP, k)
    # ---------------- face
    face = {}
    # looking down drops his heavy lids: lift them a touch so the iris stays visible
    dn = max(fr, ease_in_out(seg(t, T["slide_dn"], T["slide_dn"] + 0.3)) *
             (1.0 - ease_in_out(seg(t, T["slide_up"], T["slide_up"] + 0.28))))
    face = _addf(face, {"lid": -0.1 * dn})
    # the one lifted brow from s05's foot-tap, relaxing
    face = _addf(face, {"brow_r": tween(t, [(0.0, 0.2), (1.6, 0.06)])})
    # late notice: a tiny lid lift when he finally finds Emb at the desk
    face = _addf(face, {"lid": -0.06 * _bump(t, T["t_look"] + 0.1, 0.12, 0.3, 0.4)})
    # eye roll: head tilt + nod at the top, lids sink at the end
    face = _addf(face, {"head_tilt": 0.05 * _bump(t, r0 + 0.2, 0.25, 0.25, 0.4),
                        "head_nod": -0.1 * _bump(t, r0 + 0.2, 0.25, 0.1, 0.35),
                        "lid": 0.1 * _bump(t, r0 + 0.7, 0.3, max(0.1, T["l3"] - r0 - 0.4), 0.5)})
    # "go on": small impatient nods with the rolling hand
    face = _addf(face, {"head_nod": 0.035 * math.sin(max(0.0, t - T["roll_hand_on"]) * 2 * math.pi / 0.7)
                        * _bump(t, T["roll_hand_on"], 0.2, max(0.0, T["l3"] - T["roll_hand_on"]), 0.3)})
    # l03: one brow up a hair (deadpan question)
    face = _addf(face, {"brow_r": 0.16 * _bump(t, T["l03_hows"], 0.25, T["l3e"] - T["l03_hows"] + 0.4, 0.5),
                        "brow_l": -0.04 * _bump(t, T["l03_hows"], 0.25, T["l3e"] - T["l03_hows"] + 0.4, 0.5)})
    # l05 "...let myself in": 0.1 lid drop of disbelief + lip press (held to the end of the beat)
    face = _addf(face, {"lid": 0.1 * _bump(t, T["letme"] + 0.1, 0.3, T["shift"] - T["letme"], 0.5),
                        "press": 0.35 * _bump(t, T["letme"] + 0.2, 0.25, T["shift"] - T["letme"], 0.4)})
    # after the slide back up: "I saw that." lid +0.05, held through the plea
    face = _addf(face, {"lid": 0.05 * _bump(t, T["slide_up"] + 0.2, 0.3, 30, 0.1)})
    # the plea gets to him a tiny bit: inner brows up a hair during "I'm sorry. Please."
    face = _addf(face, {"brow_ang": 0.12 * _bump(t, T["imsorry"] + 0.2, 0.5, T["l7"] - T["imsorry"], 0.6)})
    # exhale: mouth parts a hair, then a closed, resigned press after "Sure."
    face = _addf(face, {"open": 0.12 * ex, "press": 0.25 * _ramp(t, T["l7e"] + 0.05, 0.35)})
    # ---------------- blinks: no auto blink where an eye beat must stay clean
    blink = None
    if T["t_look"] - 0.1 <= t < T["t_look"] + 0.5:
        blink = 0.0
    if T["rollEyes"] - 0.2 <= t < T["rollEyes"] + 1.2:
        blink = 0.0
    if T["research"] - 0.25 <= t < T["research"] + 0.7:
        blink = 0.0
    if T["cut_k"] - 0.05 <= t < T["cut_l"] + 0.1:
        blink = 0.0
    if T["cut_m"] <= t < T["blink0"] + 1.2:            # the long look, then the slow blink
        blink = tween(t, [(T["blink0"], 0.0), (T["blink0"] + 0.4, 1.0), (T["blink0"] + 0.6, 1.0),
                          (T["blink0"] + 1.0, 0.0)], ease_in_out)
    drift = not (T["cut_k"] - 0.05 <= t < T["cut_l"])  # head and eyes rock-still in the ECU
    expr = "bored" if t < T["l3"] - 0.1 else state_at(t, [(T["l3"] - 0.1, "deadpan"),
                                                           (T["l4"] + 0.2, "bored")], 0.3)
    return dict(x=x, y=y, pose=pose, pose_t=pose_t, turn=turn, expr=expr, look=look,
                face=_addf(face, {"head_turn": ht}), blink=blink, drift=drift,
                mouth=info.mouth("tired", t), headphones="neck")


def _emb(t, T, info):
    """Kwargs for draw_person('embar', ...) + extras (squash, at_desk)."""
    out = {}
    if t < T["zip"]:
        # ------------------------------------------------ on the floor (from s05)
        x, y = EMB_FLOOR
        look_desk = (0.96, -0.05)
        look_t = (0.62, -0.62)
        look = (0.15, 0.25)                                   # dazed, unfocused
        look = _lerp2(look, look_desk, ease_in_out(seg(t, T["glance"], T["glance"] + 0.12)))
        look = _lerp2(look, look_t, ease_in_out(seg(t, T["smile"] - 0.05, T["smile"] + 0.07)))
        ht = 0.32 * ease_in_out(seg(t, T["glance"] + 0.15, T["glance"] + 0.45))
        ht *= 1.0 - 0.8 * ease_in_out(seg(t, T["smile"], T["smile"] + 0.22))
        expr = state_at(t, [(-1, "dazed"), (T["glance"] + 0.08, "neutral"), (T["smile"], "nervous_smile")],
                        0.18)
        widen = _ramp(t, T["glance"] + 0.2, 0.14)
        face = {"lid": -0.13 * widen, "pupil": -0.28 * widen, "brow": 0.22 * widen,
                "head_turn": ht, "head_tilt": -0.04 * widen}
        face = _addf(face, {"press": 0.3 * widen * (1 - _ramp(t, T["smile"], 0.15))})
        blush = tween(t, [(T["smile"], 0.12), (T["smile"] + 0.3, 0.42)])
        sweat = tween(t, [(T["smile"], 0.0), (T["smile"] + 0.25, 0.4)])
        blink = 0.0 if T["glance"] - 0.1 < t < T["zip"] else None
        out.update(x=x, y=y, pose="sit_floor", turn=0.5, expr=expr, look=look, face=face, blush=blush,
                   sweat=sweat, blink=blink, at_desk=False)
        out["mouth"] = info.mouth("embar", t)
        return out

    # ---------------------------------------------------- at the desk
    x, y = EMB_DESK
    # ---- pose (nested blend tuples: the rig blends hand shapes finger by finger)
    pose = COVER
    # l05: casual lean, the free (near, screen-left) hand gestures
    g_on = _bump(t, T["l5"] - 0.05, 0.3, T["shift"] - T["l5"] - 0.05, 0.12)
    if g_on > 0.0:
        pose = (COVER, _gesture(t, T), g_on)
    # shift/jerk: arms jerk up with the lump, slam back down, aftershocks
    jk = _jerk_pose(t, T)
    if jk is not None:
        pose = jk
    # l06: one hand to his heart, the other still on the lump
    pl = _ramp(t, T["l6"] - 0.1, 0.32)
    if pl > 0.0:
        plead = dict(COVER, al_ik=1.0, al_tx=-0.005, al_ty=0.57, al_tz=0.17, al_h="flat", al_wa=-1.45,
                     al_wabs=0.9, al_layer="front", lean=0.42, hunch=0.6, nod=-0.08,
                     tilt=0.08 * _bump(t, T["please2"], 0.2, 0.6, 0.4))
        pose = (pose, plead, pl)
    # ---- arrival squash & stretch after the zip
    a = t - T["zip"]
    sq = (1.0, 1.0)
    if a < 0.45:
        if a < 0.05:
            sq = (1.32, 0.82)
        else:
            k = ease_out_back(seg(a, 0.05, 0.38), 2.4)
            sq = (lerp(0.86, 1.0, k), lerp(1.16, 1.0, k))
    out["squash"] = sq
    # ---- gaze
    look = E_LOOK_TIRED
    d = _darts(t, T["zip"] + 0.18, T["l2e"] + 0.3, [E_LOOK_LUMP] + E_LOOK_AWAY, 11, step=0.34,
               home=E_LOOK_TIRED, home_every=2)
    if d is not None:
        look = d
    if T["l01_um"] - 0.02 <= t < T["l2"] - 0.05:          # "Um." eyes up, searching
        look = _lerp2(look, (-0.3, -0.8), _bump(t, T["l01_um"], 0.1, T["l2"] - T["l01_um"] - 0.3, 0.12))
    if T["l02_uh"] - 0.05 <= t:                            # "uhhh..." eyes drift up-right away
        look = _lerp2(look, (0.5, -0.7), _bump(t, T["l02_uh"], 0.15, max(0.1, T["cut_e"] - T["l02_uh"]), 0.15))
    # "research": (seen on the cut to him) his eyes dart to the lump, and snap back
    look = _lerp2(look, E_LOOK_LUMP, _bump(t, T["cut_f"] + 0.14, 0.06, 0.2, 0.06))
    # l04 "I think." eyes up-left, unsure
    look = _lerp2(look, (-0.5, -0.7), _bump(t, T["ithink"], 0.08, max(0.05, T["yeah2"] - T["ithink"] - 0.1), 0.08))
    # l05 darts while selling the story
    d = _darts(t, T["l5"] + 0.2, T["shift"] - 0.05, [E_LOOK_LUMP, (0.2, -0.7), (-0.4, 0.6)], 23,
               step=0.42, home=E_LOOK_TIRED, home_every=2)
    if d is not None:
        look = d
    # shift: eyes snap down to the lump, then back up frozen
    look = _lerp2(look, E_LOOK_LUMP, _bump(t, T["shift"] + 0.04, 0.05, 0.22, 0.06))
    # ---- expression
    keys = [(-1, "nervous_smile"), (T["oh"] - 0.02, "surprised"), (T["yeah1"] - 0.02, "nervous_smile"),
            (T["no"] - 0.03, "panic"), (T["good2"] - 0.02, "fake_cool"), (T["l5"] + 0.2, "nervous_smile"),
            (T["soI"], "sheepish"), (T["shift"], "nervous_smile"), (T["l6"] - 0.08, "pleading")]
    expr = state_at(t, keys, 0.16)
    face = {"head_turn": -0.92, "head_nod": _accent_nods(t, info, 0.05)}
    # l02 "uhhh": the smile strains
    face = _addf(face, _scale({"press": 0.3, "wobble": 0.5, "brow_ang": 0.25},
                              _bump(t, T["l02_uh"], 0.2, max(0.1, T["cut_e"] - T["l02_uh"]), 0.3)))
    # "research": smile goes rigid
    face = _addf(face, _scale({"teeth": 0.4, "press": 0.3, "eye_size": 0.06, "pupil": -0.2},
                              _bump(t, T["research"] + 0.12, 0.1, max(0.3, T["l4"] - T["research"] - 0.4), 0.2)))
    # "Oh!": eyes pop
    face = _addf(face, _scale({"eye_size": 0.12, "brow": 0.3}, _bump(t, T["oh"], 0.08, 0.15, 0.2)))
    # "I think." worried brows
    face = _addf(face, _scale({"brow_ang": 0.45, "brow": 0.15}, _bump(t, T["ithink"], 0.12, 0.45, 0.2)))
    # "No-- wait.": big eyes, tiny pupils
    face = _addf(face, _scale({"eye_size": 0.15, "pupil": -0.35}, _bump(t, T["no"], 0.08, 0.3, 0.15)))
    # l05 "nobody answered": innocent brows
    face = _addf(face, _scale({"brow": 0.25, "brow_ang": 0.3}, _bump(t, T["nobody"], 0.15, 0.5, 0.3)))
    # shift/jerk: eyes wide, pupils tiny, grin frozen
    fz = _bump(t, T["shift"] + 0.02, 0.06, max(0.1, T["l6"] - T["shift"] - 0.3), 0.25)
    face = _addf(face, _scale({"eye_size": 0.18, "pupil": -0.45, "teeth": 0.6, "curve": 0.15,
                               "wobble": 0.35, "squash": -0.04}, fz))
    # head tilt into the plea
    face = _addf(face, {"head_tilt": 0.07 * _ramp(t, T["l6"], 0.4)})
    blush = tween(t, [(T["zip"], 0.42), (T["zip"] + 0.3, 0.5), (T["l3"], 0.5), (T["research"] + 0.1, 0.5),
                      (T["research"] + 0.4, 0.58), (T["l4"], 0.55), (T["good2"], 0.62), (T["l5"] + 0.4, 0.68),
                      (T["soI"], 0.72), (T["shift"], 0.72), (T["shift"] + 0.25, 0.8), (T["l6"], 0.8),
                      (T["l6"] + 0.6, 0.86)])
    sweat = tween(t, [(T["zip"], 0.45), (T["research"], 0.5), (T["research"] + 0.3, 0.75), (T["l5"], 0.6),
                      (T["shift"], 0.65), (T["shift"] + 0.2, 0.9)])
    glint = _bump(t, T["good2"] + 0.12, 0.08, 0.05, 0.18)
    blink = None
    if T["shift"] - 0.05 <= t < T["l6"] - 0.1:             # frozen: no blinking
        blink = 0.0
    out.update(x=x, y=y, pose=pose, turn=0.5, expr=expr, look=look, face=face, blush=blush, sweat=sweat,
               glint=glint, blink=blink, at_desk=True)
    out["mouth"] = info.mouth("embar", t)
    return out


def _accent_nods(t, info, amp):
    """Small head nods on the stressed words of Emb's current line (life while talking)."""
    l = info.active_line(t, "embar")
    if l is None:
        return 0.0
    env = (getattr(info, "_lip", None) or {}).get(l.id) or {}
    ws = env.get("word_starts") or []
    v = 0.0
    for i, w0 in enumerate(ws):
        a = t - (l.start + w0)
        if 0.0 <= a < 0.4:
            k = 0.6 + 0.4 * hash01(i, 77)
            v += amp * k * math.sin(math.pi * a / 0.4) * (1.0 if i % 2 == 0 else -0.6)
    return v


def _gesture(t, T):
    """l05 free-hand performance (the near / screen-left arm). Returns a pose dict."""
    base = dict(COVER, lean=0.5, side=-0.04, hunch=0.35)
    # rest: palm-up hand out to the side ("so, yeah")
    g1 = dict(base, al_ik=1.0, al_tx=0.22, al_ty=0.62, al_tz=0.08, al_h="open", al_tf=-1.0)
    # walking by: the hand sweeps out wider and a little lower
    g_walk = dict(base, al_ik=1.0, al_tx=0.27, al_ty=0.58, al_tz=0.02, al_h="open", al_tf=-1.0)
    # knock knock: a fist at head height, two little raps
    rap = 0.025 * (_bump(t, T["knocked"] + 0.02, 0.05, 0.0, 0.08) + _bump(t, T["knocked"] + 0.2, 0.05, 0.0, 0.08))
    g_knock = dict(base, al_ik=1.0, al_tx=0.22, al_ty=0.72, al_tz=0.12 + rap, al_h="fist", lean=0.5)
    # nobody answered: one-handed shrug, palm up, shoulders up
    g_shrug = dict(base, al_ik=1.0, al_tx=0.24, al_ty=0.52, al_tz=0.1, al_h="open", al_tf=-1.0, al_wa=2.8,
                   al_wabs=0.8, hunch=1.0, tilt=0.1)
    # so I... let myself in: the hand drifts in toward his chest, sheepish
    g_in = dict(base, al_ik=1.0, al_tx=0.12, al_ty=0.6, al_tz=0.14, al_h="relaxed", al_tf=-1.0, hunch=0.7,
                tilt=-0.06)
    keys = [(-1, g1), (T["walking"] - 0.1, g_walk), (T["knocked"] - 0.22, g_knock),
            (T["nobody"] - 0.05, g_shrug), (T["soI"] + 0.1, g_in)]
    return state_at(t, keys, 0.22)


def _jerk_pose(t, T):
    """shift -> jerk: the free hand freezes; on jerk both arms pop up with the lump,
    then slam down stiff, with two decaying aftershocks. None outside the beat."""
    s0, j0 = T["shift"], T["jerk"]
    if t < s0 - 0.02 or t > T["l6"] + 0.6:       # (the plea blend covers the hand-off)
        return None
    hold = dict(COVER, lean=0.6, hunch=0.8)
    up = dict(COVER, lean=0.58, hunch=0.95, al_ty=0.56, ar_ty=0.56, al_tx=0.14, ar_tx=0.1, al_h="splay",
              ar_h="splay", rot=-0.05)
    down = dict(COVER, lean=0.74, hunch=1.0, al_tz=0.42, ar_tz=0.44, al_h="splay", ar_h="splay",
                tilt=0.1, rot=0.04)
    if t < j0:
        # shift: he goes rigid; the gesture hand comes back to hover over the lump
        return (_gesture(t, T), hold, smoothstep(seg(t, s0, s0 + 0.14)))
    a = t - j0
    if a < 0.07:
        return (hold, up, smoothstep(a / 0.07))
    if a < 0.15:
        return (up, down, smoothstep((a - 0.07) / 0.08))
    # aftershocks: small pops back toward "up", then relax a little before the plea
    sh = 0.35 * _bump(a, 0.42, 0.05, 0.0, 0.1) + 0.2 * _bump(a, 0.7, 0.05, 0.0, 0.1)
    rel = smoothstep(seg(a, 0.9, 1.15))
    return ((down, up, sh), hold, rel)


# =============================================================================
# props: the thing grooming, the sweater lump
# =============================================================================
def _draw_thing_grooming(ctx, t, T):
    """The thing licking a paw and rubbing its cheek; near the end of the insert it
    stops, opens its eyes and looks down toward Emb on the floor."""
    x, y = THING
    stop = smoothstep(seg(t, T["cut_b"] - 0.16, T["cut_b"] - 0.06))
    lick = (0.5 + 0.5 * math.sin(t * 2 * math.pi * 2.1)) * (1 - stop)
    rot = (-0.07 + 0.09 * lick) * (1 - stop) + 0.06 * stop
    look = _lerp2((0.4, 0.2), (-0.75, 0.35), stop)
    blink = (0.85 + 0.15 * lick) * (1 - stop)
    with core.saved(ctx, x, y, 1.0, rot):
        a = draw_thing(ctx, 0, 0, THING_S, t, state="sit", look=look, blink=blink)
    if stop >= 0.99:
        return
    # a little paw rubbing the cheek (grooming)
    hx, hy = a["head"]                      # local (drawn at the origin of the rotated frame)
    ca, sa = math.cos(rot), math.sin(rot)
    px, py = 26 * THING_S, (8 + 14 * lick) * THING_S
    lx, ly = hx + px, hy + py
    wx, wy = x + lx * ca - ly * sa, y + lx * sa + ly * ca
    core.ellipse(ctx, wx, wy, 13 * THING_S, 10 * THING_S, -0.5 + 0.4 * lick)
    core.fill_stroke(ctx, core.PAL["thing_fur"], core.PAL["ink"], 3.5 * THING_S)


def _lump_wiggle(t, T):
    w = 0.06 + 0.22 * _bump(t, T["cut_f"] + 0.02, 0.12, 0.25, 0.4)          # it stirs after "research"
    w += 0.95 * _bump(t, T["shift"], 0.08, 0.32, 0.12)                     # SHIFT
    w += 0.9 * _bump(t, T["jerk"] - 0.02, 0.03, 0.04, 0.1)                 # the buck that jerks his arms
    w += 0.45 * _bump(t, T["jerk"] + 0.4, 0.04, 0.0, 0.12) + 0.3 * _bump(t, T["jerk"] + 0.68, 0.04, 0.0, 0.12)
    w += 0.18 * _bump(t, T["l6"], 0.3, T["l6e"] - T["l6"], 0.5)            # it keeps fidgeting under his hand
    return clamp(w)


def _draw_lump(ctx, t, T):
    a = t - T["zip"]
    if a < 0.0:
        return
    w = _lump_wiggle(t, T)
    # the sweater flops down over the thing: drops and settles with overshoot
    k = ease_out_back(seg(a, 0.0, 0.32), 2.0)
    sy = lerp(1.6, 1.0, k)
    sx = lerp(0.75, 1.0, k)
    # slam squash on the jerk
    sl = _bump(t, T["jerk"] + 0.07, 0.05, 0.05, 0.25)
    sy *= 1.0 - 0.22 * sl
    sx *= 1.0 + 0.08 * sl
    x, y = LUMP
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sx, sy)
    draw_sweater_lump(ctx, 0, 0, LUMP_S, t, wiggle=w, flip=True)
    ctx.restore()


def _draw_cage(ctx, t):
    props.cage(ctx, CAGE[0], CAGE[1] - 300 * 0.62, 0.62, t, door=0.0, latch="open", empty=True)


# =============================================================================
# the stage
# =============================================================================
def _chair_spin(t):
    # still drifting round from s05, coming to rest
    return 0.55 + 1.1 * ease_out(seg(t, 0.0, 2.6))


def _draw_person_sq(ctx, who, st, t, sq=(1.0, 1.0)):
    kw = {k: v for k, v in st.items() if k not in ("x", "y", "at_desk", "squash")}
    x, y = st["x"], st["y"]
    if sq != (1.0, 1.0):
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(sq[0], sq[1])
        ctx.translate(-x, -y)
        a = draw_person(ctx, who, x, y, CS, t, **kw)
        ctx.restore()
        return a
    return draw_person(ctx, who, x, y, CS, t, **kw)


def _stage(ctx, t, T, info, shot):
    sets.bedroom(ctx, t, "bg", chair_spin=_chair_spin(t), **ROOM)
    _draw_cage(ctx, t)
    tst = _tired(t, T, info)
    est = _emb(t, T, info)
    if t < T["zip"]:
        _draw_thing_grooming(ctx, t, T)
    _draw_lump(ctx, t, T)
    anchors = {}
    if est["at_desk"]:
        anchors["emb"] = _draw_person_sq(ctx, "embar", est, t, est.get("squash", (1, 1)))
        anchors["tired"] = _draw_person_sq(ctx, "tired", tst, t)
    else:
        anchors["tired"] = _draw_person_sq(ctx, "tired", tst, t)
        # dizzy stars from the s05 landing, popping out as he snaps out of it
        hx, hy = 1236.0, 990.0
        fx.dizzy_stars(ctx, hx, hy, 0.6, t, t0=-1.0, dur=1.0 + T["glance"] + 0.3, layer="back")
        a_e = _draw_person_sq(ctx, "embar", est, t)
        fx.dizzy_stars(ctx, hx, hy, 0.6, t, t0=-1.0, dur=1.0 + T["glance"] + 0.3, layer="front")
        anchors["emb"] = a_e
    # teleport smear (drawn over everyone)
    fx.smear(ctx, EMB_FLOOR[0] + 20, EMB_FLOOR[1] - 150, EMB_DESK[0] + 40, EMB_DESK[1] - 330, t, T["zip"],
             dur=0.38, width=130)
    # heat lines over Emb when he is at his reddest
    if est["at_desk"] and est["blush"] > 0.7:
        top = anchors["emb"]["top"]
        fx.heat_squiggles(ctx, top[0], top[1] + 8, 0.7, t, amount=(est["blush"] - 0.7) / 0.3 * 0.8)
    # sweat flicks when the lump shifts
    if est["at_desk"]:
        ea = anchors["emb"]
        fx.sweat_fly(ctx, ea["top"][0] - 40, ea["top"][1] + 60, 0.7, t, T["shift"] + 0.05, seed=3, n=3, side=-1)
        fx.sweat_fly(ctx, ea["top"][0] - 40, ea["top"][1] + 60, 0.7, t, T["jerk"] + 0.1, seed=8, n=3, side=0)
    return anchors


# =============================================================================
# cameras (world framings per shot)
# =============================================================================
TIRED_FACE = (1535.0, 968.0)            # his face anchor once he has turned to the desk


def _frame_on(world, screen, z):
    """Camera (cx, cy, z) that puts a world point at a screen point."""
    return (world[0] - (screen[0] - core.W / 2) / z, world[1] - (screen[1] - core.H / 2) / z, z)


def _camera(shot, t, t0, t1, T):
    u = seg(t, t0, t1)
    if shot == "wide_spot":
        # drift toward the desk as Emb's eyes go there (motivated by his look)
        k = ease_in_out(seg(t, T["glance"], t1))
        return (lerp(1585, 1600, k), lerp(1100, 1096, k), lerp(0.95, 0.97, k))
    if shot == "thing_insert":
        return _frame_on((THING[0], THING[1] - 50), (530, 960), lerp(3.3, 3.5, ease_in_out(u)))
    if shot == "emb_floor_cu":
        z = lerp(2.5, 2.62, ease_out(u))
        return (1185, 1150, z)
    if shot == "wide_tele":
        k = ease_in_out(seg(t, T["t_look"] - 0.2, t1))
        return (lerp(1625, 1690, k), lerp(1092, 1066, k), lerp(0.97, 1.12, k))
    if shot == "emb_med":
        return (1925, 990, lerp(1.85, 1.95, ease_in_out(u)))
    if shot == "tired_med":
        return (1518, 1052, lerp(2.2, 2.6, ease_in_out(u)))
    if shot == "emb_cu":
        return _frame_on((1900, 860), (545, 740), lerp(2.85, 3.15, ease_in_out(u)))
    if shot == "emb_gesture":
        return (1912, 990, lerp(1.78, 1.84, ease_in_out(u)))
    if shot == "two_shot2":
        return (1705, 1030, lerp(1.48, 1.54, ease_in_out(u)))
    if shot == "lump_med":
        return (1962, 968, lerp(2.5, 2.62, ease_out(u)))
    if shot == "tired_ecu":
        return _frame_on(TIRED_FACE, (530, 820), 4.0)
    if shot == "emb_plead":
        return _frame_on((1874, 800), (560, 760), lerp(2.65, 2.85, ease_in_out(u)))
    if shot == "tired_close":
        return _frame_on(TIRED_FACE, (525, 800), lerp(2.75, 3.3, ease_in_out(u)))
    return (1645, 1150, 0.9)


# =============================================================================
# entry points
# =============================================================================
def render(ctx, t, info):
    T = _times(info)
    shot, t0, t1 = _shot(t, T)
    cx, cy, z = _camera(shot, t, t0, t1, T)
    core.bg(ctx, "#2a2230")
    with core.camera(ctx, cx, cy, z):
        _stage(ctx, t, T, info, shot)


def SFX(info):
    T = _times(info)
    ev = []
    ev.append((0.25, "foot_tap", -3, -0.1))                       # last tap from s05
    ev.append((0.1, "chair_creak", -14, 0.3))                      # the empty chair winding down
    ev.append((T["cut_b"] - 0.13, "critter_squeak", -12, 0.45))   # the thing looks up: "eep?"
    ev.append((T["zip"], "smear_zip", 0, 0.25))
    ev.append((T["zip"] + 0.05, "cloth_rustle", 1, 0.4))         # sweater flops over it
    ev.append((T["t_body"] + 0.2, "footstep", -12, 0.0))          # Tiredness finally turns
    ev.append((T["roll_hand_on"] + 0.05, "cloth_rustle", -10, -0.2))
    ev.append((T["cut_f"] + 0.03, "cloth_rustle", -9, 0.4))       # it stirs after "research"
    ev.append((T["shift"], "cloth_rustle", 2, 0.4))
    ev.append((T["shift"] + 0.12, "critter_squeak", -9, 0.4))
    ev.append((T["jerk"], "cloth_rustle", 2, 0.35))
    ev.append((T["jerk"] + 0.1, "body_thud", -16, 0.35))          # hands slam the desk
    ev.append((T["jerk"] + 0.42, "cloth_rustle", -6, 0.35))
    ev.append((T["exhale"], "sigh", -9, -0.1))
    return ev
