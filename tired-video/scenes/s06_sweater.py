"""s06 -- "Act natural" (the sweater). Bedroom, music "awkward".

Continues s05 exactly where it stops: Emb sits on the floor (705, 1552) looking
up sheepishly, Tiredness stands over him (1010) arms crossed, foot tapping, one
brow up; the cage is on the floor at 520; the chair (rolled back 300 px) has
almost stopped spinning. Ends where s07 starts: Emb leaning over the desk at
x 1815 pressing the sweater lump, Tiredness mid-room at x 1450, chair back at
the desk, still turned (spin 1.1).

Shot list (all times come from cues / line words, never hard-coded):
  A  two_spot      spot          s05's two-shot continues; Emb's pupils, then his
                                 head, slide past Tiredness toward the desk
  A2 thing_insert  spot+40%      insert: the thing grooms by the keyboard; looks up
  B  emb_floor_cu  spot+72%      Emb close: eyes widened a hair on it, then snap
                                 to Tiredness + a forced smile
  C1 two_zip       teleport+.2   ZIP: smear streaks off-frame toward the desk, poof;
                                 Tiredness keeps staring at the empty floor while
                                 "Yeah." comes from off-screen; pupils, then head
                                 turn LATE and slow
  C2 desk_wide     head turn     reveal: Emb at the desk pressing the sweater over
                                 the thing (the chair, caught in his wake, rolled
                                 back to the desk and is still turning); l01/l02;
                                 Tiredness trudges into frame and stops
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
                                 slide back up. Head rock-still (no breath/drift).
  L  emb_plead     l06+.3        pleading, hand on heart, other hand on the lump
  M  tired_close   l06 "I'm"     long look (no blinks), one very slow blink on
                                 "stare", tiny exhale, "...Sure."; slow push-in
Cut list: _shot(); camera framings: _camera().
"""
import math

import cairocffi as cairo

from engine import core, sets, props, fx, human
from engine.core import (tween, state_at, seg, clamp, lerp, smoothstep, ease_out_back,
                         ease_in_out, ease_out, hash01)
from engine.human import draw_person
from engine.creatures import draw_thing, draw_sweater_lump

M = sets.BEDROOM_MARKS
CS = M["char_scale"]                     # 0.75: people in the bedroom
DESK_Y = M["desk_top_y"]
H_EMB = human.metrics("embar")["height"]

# ---- stage marks (bedroom world px) -----------------------------------------
EMB_FLOOR = (705.0, 1552.0)              # = s05 E_FLOOR (sit_floor butt point), turn -0.1
EMB_FLOOR_TURN = -0.1
TIRED0 = (1010.0, 1538.0)                # = s05 T_BEHIND, turn -0.62
TIRED1 = (1450.0, 1526.0)                # = s07 (1450, stand line): where he trudges to
TIRED_TURN = 0.62                        # facing the desk once he has turned
EMB_DESK = (1815.0, 1520.0)              # = s07 desk_lean_feet - 65
EMB_TURN = 0.5
THING_S = 0.72
LUMP_S = 0.85
CAGE_FLOOR = (520.0, 1548.0)             # = s05 CAGE_FLOOR (it goes with him on the zip)
CAGE_S = 0.36
CHAIR_DX0 = -300.0                       # s05: he rolled the chair back when he got up
CHAIR_SPIN0 = -7.556                     # s05's chair angle at its end (almost stopped)
CHAIR_SPIN1 = 1.1 - 2 * math.pi          # s07's chair angle (1.1), reached by the wake
FRAME_FALLEN = False                     # s05 and s07 both draw the frame on the wall
ROOM = dict(closet_open=1.0, chair_empty=True, frame_fallen=FRAME_FALLEN, door_open=0.45)
# s05's clothes from the closet rummage, where they landed: (kind, colour, x, rot)
CLOTHES = [("shirt", "#ff8a4f", 905, 0.4), ("sock", "#ffffff", 1010, 1.2), ("shirt", "#7cc96a", 1095, -0.5),
           ("sock", "#f2c14e", 850, -0.9), ("shirt", "#9fd8f7", 1180, 0.2)]

# look targets (screen-space gaze vectors), measured from the head anchors
T_LOOK_EMB_FLOOR = (-0.62, 0.3)          # Tiredness -> Emb on the floor (s05's last look)
T_LOOK_EMB_DESK = (0.86, -0.18)          # Tiredness -> Emb at the desk
T_LOOK_LUMP = (0.7, 0.44)                # Tiredness -> the sweater (lids follow; keep the iris readable)
E_LOOK_TIRED = (-0.88, 0.12)             # Emb (desk) -> Tiredness
E_LOOK_LUMP = (0.3, 0.85)                # Emb (desk) -> the lump
E_LOOK_AWAY = [(-0.35, -0.75), (0.45, -0.6), (-0.6, 0.55), (0.1, -0.85)]

# ---- measured stage geometry (dummy-surface draws, cached) --------------------
_DS = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2, 2)
_DC = cairo.Context(_DS)
_MEAS = {}


def _measure(key, who, x, y, **kw):
    if key not in _MEAS:
        kw.setdefault("shadow", False)
        _MEAS[key] = draw_person(_DC, who, x, y, CS, 0.0, **kw)
    return _MEAS[key]


def _lump_surface(dx):
    """Approx. height of the still sweater heap at dx from its centre (world px)."""
    u = dx / (168.0 * LUMP_S)
    if abs(u) >= 1:
        return 0.0
    return (60.0 * (1 - u * u) ** 0.9 + 6.0) * LUMP_S


def _desk_geometry():
    if "geo" in _MEAS:
        return _MEAS["geo"]
    # first pass: where his hands land on the desk, then put the heap's peak right of them
    ty0 = (EMB_DESK[1] - (DESK_Y - 45)) / (CS * H_EMB)
    a = _measure(("cov0", ty0), "embar", *EMB_DESK, pose={"base": "cover_sweater", "al_ty": ty0, "ar_ty": ty0},
                 turn=EMB_TURN, face={"head_turn": -0.92})
    hx = (a["hand_l"][0] + a["hand_r"][0]) / 2
    lump_x = hx + 55.0
    top = DESK_Y - _lump_surface(hx - lump_x) + 4
    ty = (EMB_DESK[1] - top) / (CS * H_EMB)
    _MEAS["geo"] = (lump_x, ty)
    return _MEAS["geo"]


LUMP_X, COVER_TY = _desk_geometry()
LUMP = (LUMP_X, DESK_Y)                  # sweater heap on the desk (peak right of his hands)
THING = (LUMP_X + 8, DESK_Y - 2)         # where the thing sat grooming (the heap covers it)
COVER = {"base": "cover_sweater", "al_ty": COVER_TY, "ar_ty": COVER_TY}
EMB_HEAD = _measure("emb_desk", "embar", *EMB_DESK, pose=COVER, turn=EMB_TURN,
                    face={"head_turn": -0.92})["head"]
EMB_FLOOR_HEAD = _measure("emb_floor", "embar", *EMB_FLOOR, pose="sit_floor", turn=EMB_FLOOR_TURN)["head"]
TIRED_FACE = _measure("tired1", "tired", *TIRED1, pose="arms_crossed", turn=TIRED_TURN,
                      headphones="neck")["face"]
TIRED0_HEAD = _measure("tired0", "tired", *TIRED0, pose="arms_crossed", turn=-0.62, headphones="neck")["head"]


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
    T["l02_uh"] = w("s06_l02", 4)
    T["research"] = w("s06_l03", 4)
    T["l03_hows"] = w("s06_l03", 1)
    T["oh"] = w("s06_l04", 0)
    T["yeah1"] = w("s06_l04", 1)
    T["ithink"] = w("s06_l04", 4)
    T["yeah2"] = w("s06_l04", 6)
    T["no"] = w("s06_l04", 7)
    T["good2"] = w("s06_l04", 9)
    T["walking"] = w("s06_l05", 3)
    T["knocked"] = w("s06_l05", 7)
    T["and2"] = w("s06_l05", 8)
    T["nobody"] = w("s06_l05", 9)
    T["soI"] = w("s06_l05", 11)
    T["letme"] = w("s06_l05", 13)
    T["please2"] = w("s06_l06", 4)
    T["imsorry"] = w("s06_l06", 10)
    # derived beats
    spot_len = max(0.6, T["tele"] - T["spot"])
    T["glance"] = T["spot"] + 0.1                      # Emb's pupils leave Tiredness
    T["cut_a2"] = T["spot"] + 0.4 * spot_len           # insert: the thing grooming on the desk
    T["cut_b"] = T["spot"] + 0.72 * spot_len           # back on Emb
    T["smile"] = T["cut_b"] + 0.22                     # eyes held on the desk, then a forced smile
    T["zip"] = max(T["tele"] + 0.2, T["smile"] + 0.42)  # ...and he zips
    T["t_look"] = T["zip"] + 0.55                      # Tiredness's LATE pupils
    T["t_head"] = T["t_look"] + 0.15                   # head follows (slowly)
    T["cut_c2"] = T["t_head"] + 0.52                   # cut on the head turn: the reveal
    T["t_body"] = T["t_head"] + 0.32                   # body last (off-screen in the cut)
    T["walk0"] = T["t_body"] + 0.3                     # ...then he trudges over
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
    shots = [(0.0, "two_spot"), (T["cut_a2"], "thing_insert"), (T["cut_b"], "emb_floor_cu"),
             (T["zip"], "two_zip"), (T["cut_c2"], "desk_wide"), (T["cut_e"], "tired_med"),
             (T["cut_f"], "emb_cu"), (T["cut_h"], "emb_gesture"), (T["cut_i"], "two_shot2"),
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

    m = smoothstep(seg(u - k, 0.0, 0.22))
    a, b = tgt(k - 1), tgt(k)
    return (lerp(a[0], b[0], m), lerp(a[1], b[1], m))


def _lerp2(a, b, k):
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


# =============================================================================
# character performances (shot-independent: continuity across cuts is free)
# =============================================================================
def _tired_walk(t, T):
    """(x, y, walking?, pose_t, end) for his trudge from s05's spot to s07's."""
    x0, y0 = TIRED0
    x1, y1 = TIRED1
    v = human.cycle_speed("tired", "walk", 1.0) * CS        # feet planted at this speed
    dur = (x1 - x0) / v
    w0 = T["walk0"]
    u = clamp((t - w0) / dur)
    on = 0.0 < (t - w0) < dur
    return lerp(x0, x1, u), lerp(y0, y1, u), (1.0 if on else 0.0), max(0.0, t - w0), w0 + dur


def _tired(t, T, info):
    """Kwargs for draw_person('tired', ...)."""
    x, y, walking, wt, w_end = _tired_walk(t, T)
    # ---------------- pose
    keys = [(-1.0, "tap_foot"), (0.42, "arms_crossed"), (T["roll_hand_on"], "roll_hand"),
            (T["l3"] + 0.42, "arms_crossed")]
    pose = state_at(t, keys, 0.3)
    pose_t = t
    if T["roll_hand_on"] - 0.4 <= t < T["l3"] + 1.0:
        pose_t = t - T["roll_hand_on"] + 0.15
    if walking > 0:
        # a slow trudge, arms still folded (the legs carry the cycle)
        pose = {"base": "walk", "al_p": 0.3, "al_o": 0.16, "al_e": 1.3, "al_eo": -1.32, "al_w": 0.1,
                "al_h": "relaxed", "al_layer": "front", "ar_p": 0.32, "ar_o": 0.16, "ar_e": 1.22,
                "ar_eo": -1.25, "ar_w": 0.25, "ar_h": "fist", "ar_layer": "mid", "hunch": 0.2,
                "lean": 0.08}
        pose_t = wt
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
    turn = tween(t, [(T["t_body"], -0.62), (T["t_body"] + 0.45, 1.0)], ease_in_out)
    if t > w_end - 0.15:
        turn = tween(t, [(w_end - 0.15, 1.0), (w_end + 0.35, TIRED_TURN)], ease_in_out)
    # head turn leads the body (late and slow); the body catches up and takes it over
    ht = tween(t, [(T["t_head"], 0.0), (T["t_head"] + 0.62, 1.15)], ease_in_out)
    ht -= (turn + 0.62) / 1.62 * 1.15
    ht = max(ht, -0.4) if t > T["t_head"] else 0.0
    if t > w_end - 0.15:
        ht = 0.0
    # ---------------- gaze
    look = T_LOOK_EMB_FLOOR
    look = _lerp2(look, T_LOOK_EMB_DESK, ease_in_out(seg(t, T["t_look"], T["t_look"] + 0.24)))
    if walking > 0 or (w_end - 0.4 < t < w_end + 0.3):
        look = _lerp2(look, (0.8, 0.05), 0.6)                  # watching where he's going / at Emb
    # eye roll: up-right, over the top, up-left, lids sinking, back to Emb
    r0 = T["rollEyes"]
    if r0 - 0.05 <= t < r0 + 1.15:
        look = tween(t, [(r0, T_LOOK_EMB_DESK), (r0 + 0.22, (0.85, -1.05)), (r0 + 0.45, (0.0, -1.22)),
                         (r0 + 0.68, (-0.75, -0.85)), (r0 + 1.05, T_LOOK_EMB_DESK)], ease_in_out)
    # flick to the sweater on "research"
    fr = _bump(t, T["research"] + 0.02, 0.09, 0.32, 0.11)
    look = _lerp2(look, T_LOOK_LUMP, fr)
    # THE beat: down to the sweater, hold, back up
    slide = ease_in_out(seg(t, T["slide_dn"], T["slide_dn"] + 0.3)) * \
        (1.0 - ease_in_out(seg(t, T["slide_up"], T["slide_up"] + 0.28)))
    if t >= T["slide_dn"] - 0.01:
        look = _lerp2(T_LOOK_EMB_DESK, T_LOOK_LUMP, slide)
    # ---------------- face
    face = {}
    # looking down drops his heavy lids: lift them a touch so the iris stays visible
    face = _addf(face, {"lid": -0.1 * max(fr, slide)})
    # s05's lifted brow and pressed lips from the foot-tap, relaxing
    face = _addf(face, {"brow_r": tween(t, [(0.0, 0.42), (1.6, 0.06)]),
                        "brow_out_r": tween(t, [(0.0, 0.15), (1.6, 0.0)]),
                        "press": tween(t, [(0.0, 0.25), (1.2, 0.0)]),
                        "lid": tween(t, [(0.0, -0.08), (1.2, 0.0)])})
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
    b3 = _bump(t, T["l03_hows"], 0.25, T["l3e"] - T["l03_hows"] + 0.4, 0.5)
    face = _addf(face, {"brow_r": 0.16 * b3, "brow_l": -0.04 * b3})
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
    expr = state_at(t, [(-1, "deadpan"), (0.9, "bored"), (T["l3"] - 0.1, "deadpan"), (T["l4"] + 0.2, "bored")],
                    0.3)
    return dict(x=x, y=y, pose=pose, pose_t=pose_t, turn=turn, expr=expr, look=look,
                face=_addf(face, {"head_turn": ht}), blink=blink, drift=drift,
                mouth=info.mouth("tired", t), headphones="neck")


def _emb(t, T, info):
    """Kwargs for draw_person('embar', ...) + extras (at_desk)."""
    out = {}
    if t < T["zip"]:
        # ------------------------------------------------ on the floor (from s05)
        x, y = EMB_FLOOR
        look_t = (0.62, -0.6)                                  # up at Tiredness (s05's last look)
        look_desk = (0.97, -0.12)                              # past him, to the desk
        look = _lerp2(look_t, look_desk, ease_in_out(seg(t, T["glance"], T["glance"] + 0.12)))
        look = _lerp2(look, look_t, ease_in_out(seg(t, T["smile"] - 0.05, T["smile"] + 0.07)))
        ht = 0.36 * ease_in_out(seg(t, T["glance"] + 0.15, T["glance"] + 0.45))
        ht *= 1.0 - 0.75 * ease_in_out(seg(t, T["smile"], T["smile"] + 0.22))
        expr = state_at(t, [(-1, "sheepish"), (T["glance"] + 0.08, "neutral"), (T["smile"], "nervous_smile")],
                        0.18)
        widen = _ramp(t, T["glance"] + 0.2, 0.14)
        face = {"lid": -0.13 * widen, "pupil": -0.28 * widen, "brow": 0.22 * widen,
                "head_turn": ht, "head_tilt": -0.04 * widen}
        face = _addf(face, {"press": 0.3 * widen * (1 - _ramp(t, T["smile"], 0.15))})
        blush = tween(t, [(T["glance"], 0.5), (T["glance"] + 0.3, 0.3), (T["smile"], 0.3), (T["smile"] + 0.3, 0.45)])
        sweat = tween(t, [(T["smile"], 0.0), (T["smile"] + 0.25, 0.4)])
        blink = 0.0 if T["glance"] - 0.1 < t < T["zip"] else None
        out.update(x=x, y=y, pose="sit_floor", turn=EMB_FLOOR_TURN, expr=expr, look=look, face=face,
                   blush=blush, sweat=sweat, blink=blink, at_desk=False)
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
    # the lump stirs after "research": his eyes dart to it, and snap back
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
    blush = tween(t, [(T["zip"], 0.45), (T["zip"] + 0.3, 0.5), (T["l3"], 0.5), (T["research"] + 0.1, 0.5),
                      (T["research"] + 0.4, 0.58), (T["l4"], 0.55), (T["good2"], 0.62), (T["l5"] + 0.4, 0.68),
                      (T["soI"], 0.72), (T["shift"], 0.72), (T["shift"] + 0.25, 0.8), (T["l6"], 0.8),
                      (T["l6"] + 0.6, 0.86)])
    sweat = tween(t, [(T["zip"], 0.45), (T["research"], 0.5), (T["research"] + 0.3, 0.75), (T["l5"], 0.6),
                      (T["shift"], 0.65), (T["shift"] + 0.2, 0.9)])
    glint = _bump(t, T["good2"] + 0.12, 0.08, 0.05, 0.18)
    blink = None
    if T["shift"] - 0.05 <= t < T["l6"] - 0.1:             # frozen: no blinking
        blink = 0.0
    out.update(x=x, y=y, pose=pose, turn=EMB_TURN, expr=expr, look=look, face=face, blush=blush, sweat=sweat,
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
    """l05 free-hand performance (the near / screen-left arm). Returns a blend tuple."""
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
    up = dict(COVER, lean=0.58, hunch=0.95, al_ty=COVER_TY + 0.09, ar_ty=COVER_TY + 0.09, al_tx=0.14,
              ar_tx=0.1, al_h="splay", ar_h="splay", rot=-0.05)
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
# props: the thing grooming, the sweater lump, clothes, cage
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
    lx, ly = hx + 26 * THING_S, hy + (8 + 14 * lick) * THING_S
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


def _draw_clothes(ctx):
    for i, (kind, col, lx, rr) in enumerate(CLOTHES):
        if kind == "shirt":
            props.shirt(ctx, lx, 1548 - 30, 0.42, rr * 0.15, col, flap=0.0, t=0.0, print_=(i == 0))
        else:
            props.sock(ctx, lx, 1548 - 12, 0.75, rr, col)


def _draw_cage(ctx, t, T):
    # it leaves with him on the zip (s07 finds it on the desk)
    if t < T["zip"]:
        props.cage(ctx, CAGE_FLOOR[0], CAGE_FLOOR[1] - CAGE_S * 300, CAGE_S, t, door=0.0, latch="open", empty=True)


# =============================================================================
# the stage
# =============================================================================
def _chair(t, T):
    """(chair_dx, chair_spin): s05's chair almost at rest; Emb's zip drags it back to
    the desk and sets it turning (s07: dx 0, spin 1.1)."""
    k = ease_out(seg(t, T["zip"] + 0.04, T["zip"] + 0.7))
    dx = lerp(CHAIR_DX0, 0.0, k)
    drift = -0.06 * (1 - math.exp(-t / 1.7))
    sp = ease_out(seg(t, T["zip"] + 0.04, T["zip"] + 2.2))
    return dx, lerp(CHAIR_SPIN0 + drift, CHAIR_SPIN1, sp)


def _draw_person(ctx, who, st, t):
    kw = {k: v for k, v in st.items() if k not in ("x", "y", "at_desk")}
    return draw_person(ctx, who, st["x"], st["y"], CS, t, **kw)


def _stage(ctx, t, T, info, shot):
    cdx, cspin = _chair(t, T)
    sets.bedroom(ctx, t, "bg", chair_dx=cdx, chair_spin=cspin, **ROOM)
    _draw_clothes(ctx)
    _draw_cage(ctx, t, T)
    tst = _tired(t, T, info)
    est = _emb(t, T, info)
    if t < T["zip"]:
        _draw_thing_grooming(ctx, t, T)
    _draw_lump(ctx, t, T)
    anchors = {}
    if est["at_desk"]:
        anchors["emb"] = _draw_person(ctx, "embar", est, t)
        anchors["tired"] = _draw_person(ctx, "tired", tst, t)
    else:
        anchors["tired"] = _draw_person(ctx, "tired", tst, t)
        anchors["emb"] = _draw_person(ctx, "embar", est, t)
    # teleport smear, floor -> desk (drawn over everyone), and a little poof where the cage was
    fx.smear(ctx, EMB_FLOOR[0] + 20, EMB_FLOOR[1] - 160, EMB_DESK[0] + 40, EMB_DESK[1] - 420, t, T["zip"],
             dur=0.38, width=130)
    fx.dust_puff(ctx, CAGE_FLOOR[0], CAGE_FLOOR[1], 0.5, t, T["zip"] + 0.02, seed=4, dur=0.5)
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
def _frame_on(world, screen, z):
    """Camera (cx, cy, z) that puts a world point at a screen point."""
    return (world[0] - (screen[0] - core.W / 2) / z, world[1] - (screen[1] - core.H / 2) / z, z)


def _camera(shot, t, t0, t1, T):
    u = seg(t, t0, t1)
    if shot == "two_spot":
        # s05's closing two-shot carries on, then drifts right after Emb's look
        k = ease_in_out(seg(t, T["glance"] + 0.1, t1 + 0.2))
        return (lerp(900, 935, k), lerp(1010, 1004, k), 1.58)
    if shot == "thing_insert":
        return _frame_on((THING[0], THING[1] - 46), (530, 960), lerp(3.4, 3.6, ease_in_out(u)))
    if shot == "emb_floor_cu":
        return _frame_on(EMB_FLOOR_HEAD, (430, 760), lerp(2.55, 2.68, ease_out(u)))
    if shot == "two_zip":
        k = ease_in_out(seg(t, T["t_look"], t1))
        return (lerp(905, 940, k), lerp(1008, 1000, k), lerp(1.5, 1.56, k))
    if shot == "desk_wide":
        return _frame_on(EMB_HEAD, (800, 760), lerp(1.28, 1.34, ease_in_out(u)))
    if shot == "tired_med":
        return _frame_on(TIRED_FACE, (470, 760), lerp(2.2, 2.6, ease_in_out(u)))
    if shot == "emb_cu":
        return _frame_on((EMB_HEAD[0] + 4, EMB_HEAD[1] + 28), (545, 740), lerp(2.85, 3.15, ease_in_out(u)))
    if shot == "emb_gesture":
        return _frame_on(EMB_HEAD, (620, 720), lerp(1.78, 1.84, ease_in_out(u)))
    if shot == "two_shot2":
        return _frame_on(((TIRED_FACE[0] + EMB_HEAD[0]) / 2, (TIRED_FACE[1] + EMB_HEAD[1]) / 2), (515, 780),
                         lerp(1.48, 1.54, ease_in_out(u)))
    if shot == "lump_med":
        return _frame_on(((EMB_HEAD[0] + LUMP[0]) / 2, (EMB_HEAD[1] + LUMP[1]) / 2 - 10), (520, 930),
                         lerp(2.5, 2.62, ease_out(u)))
    if shot == "tired_ecu":
        return _frame_on(TIRED_FACE, (530, 820), 4.0)
    if shot == "emb_plead":
        return _frame_on((EMB_HEAD[0] - 22, EMB_HEAD[1] - 30), (560, 760), lerp(2.65, 2.85, ease_in_out(u)))
    if shot == "tired_close":
        return _frame_on(TIRED_FACE, (525, 800), lerp(2.75, 3.3, ease_in_out(u)))
    return (1500, 1060, 1.0)


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
    ev.append((0.25, "foot_tap", -3, 0.1))                         # last tap from s05
    ev.append((T["cut_b"] - 0.13, "critter_squeak", -12, 0.45))   # the thing looks up: "eep?"
    ev.append((T["zip"], "smear_zip", 0, 0.3))
    ev.append((T["zip"] + 0.06, "chair_creak", -6, 0.35))         # the chair caught in his wake
    ev.append((T["zip"] + 0.12, "cloth_rustle", 0, 0.5))          # sweater flops over it (off-screen)
    # Tiredness's slipper shuffle as he trudges over (one per step)
    x, y, wk, wt, w_end = _tired_walk(0.0, T)
    k, tt = 0, T["walk0"] + 0.05
    while tt < w_end - 0.1 and k < 6:
        ev.append((tt, "footstep", -14, -0.1 + 0.05 * k))
        tt += 0.5
        k += 1
    ev.append((T["roll_hand_on"] + 0.05, "cloth_rustle", -10, -0.2))
    ev.append((T["cut_f"] + 0.03, "cloth_rustle", -9, 0.4))       # it stirs after "research"
    ev.append((T["shift"], "cloth_rustle", 2, 0.4))
    ev.append((T["shift"] + 0.12, "critter_squeak", -9, 0.4))
    ev.append((T["jerk"], "cloth_rustle", 2, 0.35))
    ev.append((T["jerk"] + 0.1, "body_thud", -16, 0.35))          # hands slam the desk
    ev.append((T["jerk"] + 0.42, "cloth_rustle", -6, 0.35))
    ev.append((T["exhale"], "sigh", -9, -0.1))
    return ev
