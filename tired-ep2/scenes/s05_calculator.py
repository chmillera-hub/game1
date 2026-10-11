"""s05 -- the pocket calculator ("awkward").

The service tunnel junction (sets.service_tunnel, TUNNEL_MARKS): the dark side
tunnel to SHAFT A on the left, the lamp-lit corridor toward CONTROL on the right.
Embarrassment walks OUT of the dark side tunnel (from the powerless shaft) with
his flashlight; Tiredness and Curiosity stand in the corridor to the right.

Shot list (every time is derived from cues / line timings, see shots()):
  S1  0 .. steps+0.5     junction, slow push-in: Curiosity alone, ears low, staring into the
                         dark tunnel; Tiredness walks in from the right and stops; it looks back
                         up at him, surprised then hopeful (ears half up); he glances down, then
                         looks away, hands into the hoodie pocket. Footsteps in the tunnel:
                         ears shoot up, both look; warm torchlight grows inside the mouth.
  S2  .. l01 word 1      wide: Curiosity scrambles backwards behind his legs; Embarrassment walks
                         out of the dark, torch on the floor; he stops, turns, the beam swings up
                         onto Tiredness's face; Emb jolts (startle, blush 0.5). "Tiredness?!"
  S3  .. l01.end+0.4     Emb medium: "...What are you doing down here?" (whisper-shout, one
                         glance back over his shoulder)
  S4  .. l02.end+0.35    Tiredness medium in the beam, squinting: "Hi." (lazy wave) "Long story."
  S5  .. l03.end+0.1     two-shot: the beam drifts down his legs and finds one big eye peeking
                         out; both freeze. "Is that... Specimen Zero?"
  S6  .. l04 "glowing"   Emb close: eyes climb from the creature to Tiredness's eyes, puzzled brow
  S7  .. l05.end+0.3     Tiredness close, teal eyes: "I fell out of a window." lid drop, lip press
  S8  .. led             Emb close: the long slow blink
  S9  .. conflict        three-shot: the LED blinks in his pocket; Emb's eyes slide down to it,
                         then Tiredness's, then Curiosity's
  S10 .. click+0.75      Emb close (slow push): recorder in his palm; at it / at Tiredness / at
                         it, blush up then down, a breath, the thumb press: click, LED dark
  S11 .. l06.end+0.3     two-shot: "Huh. My pocket calculator just stopped working." -- calm,
                         he shows the dead recorder; Curiosity creeps out from behind the legs
  S12 .. l07-0.25        Tiredness + Curiosity: his faintest smile; it glances, then grins
  S13 .. l07.end         two-shot: "The control room is on level nine. Take my keycard." handoff
  S14 .. l08             insert: the keycard (LVL 9) in his bandaged hand, a glint
  S15 .. l08.end+0.35    Emb close: "And Tiredness? Be careful." sincere, slow, steady eyes
  S16 .. end             two-shot: a small nod; he turns toward CONTROL and sets off;
                         Curiosity looks after him
"""
import math

import cairocffi as cairo

from engine import core, human, creatures, sets, fx, props
from engine.core import seg, clamp, lerp, smoothstep, ease_in_out, ease_out, ease_out_back, state_at

M = sets.TUNNEL_MARKS
S = 0.75                 # people (the set's char_scale)
SC = 0.74                # Curiosity
FY = M["feet_y"]         # 1500
XT = 790                 # Tiredness's spot (facing left)
XE = 325                 # Embarrassment's spot in front of the tunnel mouth (facing right)
C0 = 610                 # Curiosity at the start: at the junction, looking into the tunnel
CH = 785                 # hiding behind his legs (head peeks out on the left)
C1 = 640                 # out again, sitting by his front foot
MOUTH = M["mouth"]       # (90, 560, 420, 740)
WALL_Y = M["wall_y"]
TK = dict(outfit="sewer", bandage=True, headphones=None, hood=0.0, power=0.6)
T_FACE = (XT - 64, 912)          # Tiredness's face (beam target)
CUR_EYE = (CH - 82, 1318)        # Curiosity's peeking (visible) eye
FLASH_S = 0.42
REC_S = 0.52
WARM = "#ffe9c4"


# --------------------------------------------------------------------------- small helpers
def tw(t, keys):
    """Keyframes [(t, v[, ease]), ...]; the ease of a key applies to the segment ending
    there (default ease_in_out). Values may be tuples."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t < b[0]:
            e = b[2] if len(b) > 2 else ease_in_out
            u = e((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 1.0
            if isinstance(a[1], (tuple, list)):
                return tuple(lerp(p, q, u) for p, q in zip(a[1], b[1]))
            return lerp(a[1], b[1], u)
    return keys[-1][1]


def fk(t, table):
    return {key: tw(t, ks) for key, ks in table.items()}


def addf(*ds):
    out = {}
    for d in ds:
        for key, v in d.items():
            out[key] = out.get(key, 0.0) + v
    return out


def mouth_path(c):
    mx, mt, mw, mh = MOUTH
    c.move_to(mx, WALL_Y)
    c.line_to(mx, mt + 110)
    c.curve_to(mx, mt, mx + mw, mt, mx + mw, mt + 110)
    c.line_to(mx + mw, WALL_Y)
    c.close_path()


def lit_tunnel(c):
    sets._tn_static(c)          # the undimmed concrete: what a torch reveals


# --------------------------------------------------------------------------- timing
def K(info):
    c = info.cue
    L = info.line
    k = dict(dur=info.dur, steps=c("steps"), notice=c("notice"), blink=c("blink"), led=c("led"),
             conflict=c("conflict"), click=c("click"), smile=c("smile"), card=c("card"), nod=c("nod"))
    for i in range(1, 9):
        ln = L(f"s05_l0{i}")
        k[f"l{i}"], k[f"l{i}e"] = ln.start, ln.end
    w = info.word_time
    k["l1_what"] = w("s05_l01", 1)
    k["l1_down"] = w("s05_l01", 5)
    k["l2_hi"] = w("s05_l02", 0)
    k["l2_story"] = w("s05_l02", 2)
    k["l3_spec"] = w("s05_l03", 2)
    k["l4_eyes"] = w("s05_l04", 4)
    k["l4_glow"] = w("s05_l04", 5)
    k["l5_win"] = w("s05_l05", 5)
    k["l6_pocket"] = w("s05_l06", 2)
    k["l6_calc"] = w("s05_l06", 3)
    k["l6_stop"] = w("s05_l06", 5)
    k["l7_nine"] = w("s05_l07", 6)
    k["l7_take"] = w("s05_l07", 7)
    k["l7_card"] = w("s05_l07", 9)
    k["l8_be"] = w("s05_l08", 2)
    st = k["steps"]
    # Tiredness walk-in
    k["t_stop"] = min(1.3, st - 1.0)
    # Embarrassment comes out of the tunnel
    k["e0"] = st - 0.05
    k["e1"] = st + 1.45                    # at the mouth (k depth 0)
    k["e_turn"] = k["e1"] - 0.05
    k["swing0"], k["swing1"] = k["e1"] + 0.1, k["e1"] + 0.38
    k["jolt"] = k["swing1"] + 0.05
    # Curiosity scramble
    k["c_up"] = st + 0.42
    k["c_mv0"], k["c_mv1"] = st + 0.54, st + 1.0
    k["c_sit"] = st + 1.0
    k["c_found"] = k["notice"] + 0.72      # the beam lands on it
    # the recorder
    cf = k["conflict"]
    k["r_reach"] = cf + 0.1
    k["r_grab"] = cf + 0.45
    k["r_up"] = cf + 0.95
    k["r_look_t"] = cf + 1.65              # eyes to Tiredness
    k["r_look_b"] = cf + 2.4               # back to the recorder
    k["r_breath"] = cf + 2.8
    k["press"] = k["click"] + 0.04
    k["led_off"] = k["press"] + 0.1
    k["r_pocket"] = k["l6e"] + 0.05
    k["r_gone"] = k["r_pocket"] + 0.38
    # keycard
    k["k_reach"] = k["l7_take"] - 0.6
    k["k_have"] = k["k_reach"] + 0.35
    k["k_out"] = k["k_have"] + 0.5
    k["k_take0"] = k["k_out"] + 0.18
    k["k_take"] = k["k_take0"] + 0.36
    k["k_back"] = k["k_take"] + 0.12
    # Curiosity comes out
    k["c_out0"] = k["click"] + 0.95
    k["c_out1"] = k["c_out0"] + 1.3
    # the end
    k["nod0"] = k["nod"] + 0.22
    k["go_turn"] = k["nod"] + 1.05
    k["go_walk"] = k["go_turn"] + 0.35
    # shots
    k["S2"] = st + 0.5
    k["S3"] = k["l1_what"] - 0.07
    k["S4"] = k["l1e"] + 0.4
    k["S5"] = k["l2e"] + 0.35
    k["S6"] = k["l3e"] + 0.1
    k["S7"] = k["l4_glow"] - 0.05
    k["S8"] = k["l5e"] + 0.3
    k["S9"] = k["led"]
    k["S10"] = k["conflict"]
    k["S11"] = k["click"] + 0.75
    k["S12"] = k["l6e"] + 0.3
    k["S13"] = k["l7"] - 0.25
    k["S14"] = k["l7e"] - 0.05
    k["S15"] = k["l8"] - 0.05
    k["S16"] = k["l8e"] + 0.35
    return k


_KC = {}


def keys_for(info):
    sig = (info.id, round(info.dur, 4))
    if sig not in _KC:
        _KC.clear()
        _KC[sig] = K(info)
    return _KC[sig]


# --------------------------------------------------------------------------- shots / cameras
def shots(k):
    st = k["steps"]
    return [
        ("S1", 0.0, lambda t: tw(t, [(0.0, (592, 1190, 1.55)), (0.3, (594, 1189, 1.55)),
                                     (1.7, (688, 1152, 1.62)), (k["S2"], (694, 1150, 1.66))])),
        ("S2", k["S2"], lambda t: tw(t, [(k["S2"], (505, 1090, 1.22)), (k["S3"], (515, 1092, 1.27))])),
        ("S3", k["S3"], lambda t: (470, 950, 2.3)),
        ("S4", k["S4"], lambda t: (735, 1010, 2.3)),
        ("S5", k["S5"], lambda t: (565, 1135, 1.46)),
        ("S6", k["S6"], lambda t: (450, 905, 2.6)),
        ("S7", k["S7"], lambda t: (700, 955, 2.6)),
        ("S8", k["S8"], lambda t: (450, 905, 2.6)),
        ("S9", k["S9"], lambda t: (562, 1108, 1.7)),
        ("S10", k["S10"], lambda t: tw(t, [(k["S10"], (392, 925, 2.75)), (k["S11"], (388, 922, 3.0))])),
        ("S11", k["S11"], lambda t: (555, 1185, 1.75)),
        ("S12", k["S12"], lambda t: (758, 1150, 1.85)),
        ("S13", k["S13"], lambda t: (570, 1230, 1.6)),
        ("S14", k["S14"], None),
        ("S15", k["S15"], lambda t: (450, 905, 2.6)),
        ("S16", k["S16"], lambda t: tw(t, [(k["S16"], (580, 1170, 1.5)), (k["dur"], (598, 1166, 1.56))])),
    ]


def shot_at(t, k):
    sh = shots(k)
    cur = sh[0]
    for s_ in sh:
        if t >= s_[1]:
            cur = s_
    return cur


def view_rect(cam, pad=60):
    cx, cy, z = cam
    return (cx - 540 / z - pad, cy - 960 / z - pad, 1080 / z + 2 * pad, 1920 / z + 2 * pad)


_SR = {}


def shade_rect(k, name):
    """World rect covering a shot's whole framing (camera start .. end)."""
    key = (round(k["dur"], 4), name)
    if key not in _SR:
        sh = shots(k)
        i = [s_[0] for s_ in sh].index(name)
        t0 = sh[i][1]
        t1 = sh[i + 1][1] - 0.01 if i + 1 < len(sh) else k["dur"]
        rs = [view_rect(sh[i][2](tt), pad=40) for tt in (t0, (t0 + t1) / 2, t1)]
        x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs)
        x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
        _SR[key] = (x0, y0, x1 - x0, y1 - y0)
    return _SR[key]


# --------------------------------------------------------------------------- Tiredness
STAND_T = "stand"
POCKET_T = "hands_pockets"
# a lazy hello: the near hand comes out of the hoodie pocket for one small bent-elbow wave,
# the other hand stays in the pocket (wave_small's arm on top of hands_pockets)
WAVE_T = {"base": "hands_pockets", "period": 0.7, "ar_p": 0.35, "ar_o": 1.2, "ar_e": 2.3,
          "ar_eo": human.W(-1.1, 0.15, 0.0), "ar_w": human.W(0.0, 0.18, 0.1), "ar_h": "open",
          "ar_tf": -1.0, "ar_hide": 0.0, "hunch": 0.3}
# on the way up / down the hand swings out to the side first, so it never crosses his face
WAVE_MID = {"base": "hands_pockets", "ar_p": 0.25, "ar_o": 1.35, "ar_e": 1.25, "ar_eo": -0.6,
            "ar_h": "open", "ar_tf": -1.0, "ar_hide": 0.0, "hunch": 0.3}


def tired_state(t, k):
    st = k["steps"]
    v = abs(human.cycle_speed("tired", "walk", -0.9, "sewer")) * S
    ts = k["t_stop"]
    d = dict(x=XT, y=FY, turn=-0.7, pose=STAND_T, pose_t=None, expr="bored", look=(0, 0),
             blink=None, face={}, reach=None, drift=True, card=False)
    # ---- walk in, stop
    if t < ts:
        d["x"] = XT + v * (ts - t)
        d["turn"] = -0.9
    pt = min(t, ts) - ts + 2.0
    # ---- body poses
    keys = [(-1, "walk"), (ts, STAND_T), (ts + 0.6, POCKET_T)]
    hi = k["l2_hi"]
    keys += [(hi - 0.32, WAVE_MID), (hi - 0.14, WAVE_T), (hi + 0.56, WAVE_MID), (hi + 0.74, POCKET_T)]
    keys += [(k["k_take0"] - 0.45, STAND_T)]
    keys += [(k["go_walk"], "walk")]
    pose = state_at(t, keys, 0.3)
    if pose[1] in (WAVE_T, WAVE_MID) or pose[0] in (WAVE_T, WAVE_MID):
        pose = state_at(t, keys, 0.18)
        d["pose_t"] = max(0.0, t - (hi - 0.14))
    elif pose[1] == "walk" and t >= k["go_walk"]:
        d["pose_t"] = t - k["go_walk"]
    else:
        d["pose_t"] = pt
    d["pose"] = pose
    if t < ts + 0.3:
        d["turn"] = tw(t, [(ts - 0.05, -0.9), (ts + 0.3, -0.7)])
    # ---- leaving at the end: turn toward CONTROL, set off
    if t >= k["go_turn"]:
        d["turn"] = tw(t, [(k["go_turn"], -0.7), (k["go_walk"], 0.85)])
        if t >= k["go_walk"]:
            vr = abs(human.cycle_speed("tired", "walk", 0.85, "sewer")) * S
            d["x"] = XT + vr * smoothstep(seg(t, k["go_walk"], k["go_walk"] + 0.3)) * (t - k["go_walk"])
    # ---- the keycard: reach, take, hold it up to read it
    kt0, kt = k["k_take0"], k["k_take"]
    if kt0 - 0.1 <= t:
        ch = emb_card_hand(kt0 + 0.02, k)
        hold_pt = (XT - 85, 1095)
        if t < kt:
            w = smoothstep(seg(t, kt0, kt))
            d["reach"] = {"r": (ch[0] + 22, ch[1] - 2, w)}
        elif t < k["go_turn"]:
            p = tw(t, [(kt, (ch[0] + 22, ch[1] - 2)), (kt + 0.45, hold_pt)])
            d["reach"] = {"r": (p[0], p[1], 1.0)}
        else:
            w = 1 - smoothstep(seg(t, k["go_turn"], k["go_turn"] + 0.35))
            d["reach"] = {"r": (hold_pt[0], hold_pt[1], w)}
        d["card"] = t >= kt
    # ---- expression
    d["expr"] = state_at(t, [(0, "bored"), (k["l2"] - 0.2, "deadpan"), (k["S6"], "bored"),
                             (k["smile"], "soft_smile"), (k["S13"], "bored")], 0.3)
    f = {}
    # walk-in -> stop, look at it, soft brows; then look away + lip press
    look = tw(t, [(0.0, (-0.45, 0.5)), (ts, (-0.55, 0.75)), (ts + 0.55, (-0.6, 0.8)),
                  (ts + 0.75, (0.75, -0.2)), (st + 0.1, (0.8, -0.15)),
                  (st + 0.25, (-1.0, 0.0)),                          # the footsteps: to the tunnel
                  (st + 0.75, (-0.95, 0.05)), (st + 0.9, (-0.3, 0.9)),  # glance down: it hides
                  (st + 1.15, (-0.35, 0.9)), (st + 1.3, (-0.95, 0.0)),
                  (k["jolt"] - 0.1, (-0.95, -0.05)), (k["jolt"] + 0.1, (-0.8, 0.2))])
    f.update(fk(t, {
        "brow_ang": [(ts, 0.0), (ts + 0.3, 0.18), (ts + 0.75, 0.0)],
        "press": [(ts + 0.6, 0.0), (ts + 0.9, 0.4), (st + 0.2, 0.4), (st + 0.4, 0.0)],
        "head_turn": [(ts + 0.85, 0.0), (ts + 1.05, 0.3), (st + 0.35, 0.3), (st + 0.55, -0.12)],
        "head_nod": [(ts - 0.3, 0.1), (ts + 0.4, 0.14), (ts + 0.9, -0.02), (st + 0.4, 0.0)],
    }))
    f["lid"] = tw(t, [(st + 0.2, 0.0), (st + 0.35, -0.08), (st + 1.0, -0.05)])
    # the beam in his face: squint, flinch, head away (until the beam drifts down)
    b_on = smoothstep(seg(t, k["swing1"] - 0.08, k["swing1"] + 0.1)) * \
        (1 - smoothstep(seg(t, k["notice"] + 0.25, k["notice"] + 0.65)))
    d["squint"] = b_on
    if b_on > 0:
        f["lower"] = f.get("lower", 0) + 0.24 * b_on
        f["lid"] = f.get("lid", 0) + 0.03 * b_on
        f["brow"] = f.get("brow", 0) - 0.18 * b_on
        f["head_turn"] = f.get("head_turn", 0) + 0.12 * b_on
        f["head_nod"] = f.get("head_nod", 0) + 0.04 * b_on
    if t >= k["jolt"]:
        look = (-0.75, 0.15)
    # l02: "Hi." chin lift; "Long story." eyes slide off and back; press after
    if t >= k["l2"] - 0.3:
        look = tw(t, [(k["l2"] - 0.3, (-0.75, 0.15)), (k["l2_story"] + 0.05, (-0.75, 0.15)),
                      (k["l2_story"] + 0.25, (0.55, -0.1)), (k["l2e"] - 0.05, (0.55, -0.05)),
                      (k["l2e"] + 0.2, (-0.8, 0.1))])
        f = addf(f, fk(t, {
            "head_nod": [(hi - 0.05, 0.0), (hi + 0.12, -0.12), (hi + 0.5, 0.0)],
            "press": [(k["l2e"], 0.0), (k["l2e"] + 0.25, 0.35), (k["S5"] + 0.4, 0.15)],
        }))
    # notice: follow the beam down to it, back up at Emb: "uh-oh"
    nt = k["notice"]
    if t >= nt:
        look = tw(t, [(nt, (-0.8, 0.1)), (nt + 0.35, (-0.75, 0.3)), (nt + 0.75, (-0.15, 1.0)),
                      (nt + 1.25, (-0.15, 1.0)), (nt + 1.45, (-0.85, 0.05)),
                      (k["l3_spec"], (-0.85, 0.05)), (k["l3_spec"] + 0.15, (-0.15, 0.95)),
                      (k["l3_spec"] + 0.55, (-0.15, 0.95)), (k["l3_spec"] + 0.7, (-0.85, 0.05))])
        f = addf(f, fk(t, {
            "head_nod": [(nt + 0.45, 0.0), (nt + 0.8, 0.12), (nt + 1.3, 0.12), (nt + 1.6, 0.0)],
            "brow_ang": [(nt + 1.3, 0.0), (nt + 1.6, 0.22), (k["l4"], 0.1)],
            "press": [(nt + 1.3, 0.0), (nt + 1.6, 0.3), (k["l4"], 0.15)],
        }))
    # l04 / l05: steady on Emb; deadpan answer, lid drop + press after
    if t >= k["l4"] - 0.2:
        look = tw(t, [(k["l4"] - 0.2, (-0.85, 0.05)), (k["l5e"] + 0.2, (-0.85, 0.05)),
                      (k["l5e"] + 0.45, (-0.7, 0.25)), (k["led"] + 0.25, (-0.75, 0.2)),
                      (k["led"] + 0.45, (-1.0, 0.45))])
        f = addf(f, fk(t, {
            "lid": [(k["l5e"], 0.0), (k["l5e"] + 0.35, 0.09), (k["led"], 0.07), (k["led"] + 0.5, 0.0)],
            "press": [(k["l5e"], 0.0), (k["l5e"] + 0.3, 0.35), (k["led"], 0.2), (k["led"] + 0.4, 0.0)],
            "head_turn": [(k["led"] + 0.4, 0.0), (k["led"] + 0.62, -0.12)],
            "head_nod": [(k["led"] + 0.4, 0.0), (k["led"] + 0.62, 0.08)],
        }))
    # conflict / click / l06: watching Emb (the recorder, then his face); a brow lifts on
    # "calculator" -- he gets it; the corner of the mouth starts to go
    if t >= k["conflict"]:
        look = tw(t, [(k["conflict"], (-1.0, 0.45)), (k["click"] + 0.5, (-1.0, 0.4)),
                      (k["click"] + 0.8, (-0.9, 0.05))])
        f = addf(f, fk(t, {
            "head_turn": [(k["click"] + 0.6, 0.0), (k["click"] + 0.85, 0.12)],
            "head_nod": [(k["click"] + 0.6, 0.0), (k["click"] + 0.85, -0.08)],
            "brow_r": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, 0.3), (k["smile"], 0.12)],
            "brow_l": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, 0.08), (k["smile"], 0.0)],
            "lid": [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.25, -0.05), (k["smile"], 0.04)],
        }))
    # smile: the faintest smile, soft eyes (soft_smile expr + small deltas)
    s12 = k["S12"]
    if t >= s12 - 0.6:
        f = addf(f, fk(t, {
            "curve": [(s12 - 0.6, -0.15), (s12 - 0.05, -0.15), (s12 + 0.5, 0.06)],
            "smirk": [(s12 - 0.05, 0.0), (s12 + 0.45, -0.28), (k["S13"], -0.22), (k["S13"] + 0.4, 0.0)],
            "lid": [(s12, 0.0), (s12 + 0.5, 0.06)],
        }))
        if t < k["S13"]:
            look = tw(t, [(s12 - 0.6, (-0.9, 0.05)), (s12 + 0.85, (-0.9, 0.05)),
                          (s12 + 1.0, (-0.45, 0.75)), (k["S13"], (-0.45, 0.75))])
            f = addf(f, fk(t, {"head_nod": [(s12 + 0.9, 0.0), (s12 + 1.1, 0.06)]}))
    # l07: on Emb, then on the card he takes; reads it
    if t >= k["S13"]:
        look = tw(t, [(k["S13"], (-0.9, 0.05)), (k["k_out"], (-0.9, 0.1)), (k["k_out"] + 0.2, (-0.9, 0.5)),
                      (k["k_take"] + 0.1, (-0.85, 0.55)), (k["k_take"] + 0.35, (-0.6, 0.85)),
                      (k["l8"] - 0.1, (-0.6, 0.85)), (k["l8"] + 0.1, (-0.9, 0.05))])
        f = addf(f, fk(t, {
            "head_nod": [(k["k_take"], 0.0), (k["k_take"] + 0.35, 0.12), (k["l8"] - 0.1, 0.12),
                         (k["l8"] + 0.15, 0.0)],
            "lid": [(k["l8_be"], 0.0), (k["l8_be"] + 0.3, -0.06), (k["nod"], -0.04)],
        }))
    # nod, then off toward CONTROL
    n0 = k["nod0"]
    if t >= k["nod"] - 0.2:
        look = tw(t, [(k["nod"] - 0.2, (-0.9, 0.05)), (k["go_turn"] - 0.05, (-0.9, 0.1)),
                      (k["go_turn"] + 0.15, (0.6, 0.0))])
        f = addf(f, fk(t, {
            "head_nod": [(n0, 0.0), (n0 + 0.24, 0.24), (n0 + 0.66, 0.02)],
            "curve": [(n0 + 0.3, 0.0), (n0 + 0.6, 0.12)],
        }))
    d["look"] = look
    d["face"] = f
    return d


# --------------------------------------------------------------------------- Embarrassment
EMB_BASE = {"base": "stand", "ar_h": "grip", "al_h": "relaxed", "ar_layer": "mid"}
EMB_WALK = {"base": "walk", "ar_h": "grip", "ar_layer": "mid"}
EMB_JOLT = {"base": "stand", "ar_h": "grip", "ar_layer": "mid", "al_h": "open", "hunch": 0.75, "lean": -0.12, "lift": 14}
EMB_NERV = {"base": "stand", "ar_h": "grip", "ar_layer": "mid", "al_h": "relaxed", "hunch": 0.25}
EMB_PINCH = {"base": "stand", "ar_h": "grip", "ar_layer": "mid", "al_h": "pinch"}
EMB_CUP = {"base": "stand", "ar_h": "grip", "ar_layer": "mid", "al_h": "cup", "al_tf": -1}
EMB_CUPB = {"base": "stand", "ar_h": "grip", "ar_layer": "mid", "al_h": "cup", "al_tf": -1, "hunch": 0.22}


def emb_depth(t, k):
    """Depth into the side tunnel (tunnel_depth k): 0.85 deep -> 0 at the mouth."""
    u = seg(t, k["e0"], k["e1"])
    return 0.85 * (1 - (0.55 * u + 0.45 * ease_out(u)))


def emb_card_hand(t, k):
    """World point of his left (near) palm while handing over the card."""
    return tw(t, [(k["k_have"], (300, 1000)), (k["k_out"], (583, 1068))])


def embar_state(t, k):
    st = k["steps"]
    d = dict(x=XE, y=FY, s=S, turn=0.7, pose=EMB_BASE, pose_t=None, expr="neutral", look=(0.9, 0.0),
             blink=None, blush=0.1, face={}, reach={}, drift=True, glasses_dy=0.0, dim=0.0,
             inside=False, visible=True, aim=None, beam=1.0, rec=None, card=None, led=None,
             led_glow=0.55, sweat=0.0)
    # ---- out of the tunnel
    if t < k["e1"]:
        kd = emb_depth(t, k)
        lane = (XE - (M["mouth"][0] + M["mouth"][2] / 2)) / (M["mouth"][2] * 0.3)
        x, y, f = sets.tunnel_depth(kd, lane)
        d.update(x=x, y=y, s=S * f, turn=0.15, pose=EMB_WALK, pose_t=t - k["e0"])
        d["dim"] = 0.88 * (1 - smoothstep(seg(f, 0.32, 0.8)))
        d["inside"] = f < 0.59
        d["visible"] = t >= k["e0"]
        d["look"] = tw(t, [(k["e0"], (0.15, 0.5)), (k["e0"] + 0.7, (0.4, 0.45)), (k["e1"], (0.6, 0.2))])
        d["face"] = {"brow_ang": 0.25, "press": 0.2}
        sc = d["s"]
        d["reach"] = {"r": (x + 92 * sc / S, y - 335 * sc / S, 1.0)}
        sweep = 0.16 * math.sin((t - k["e0"]) * 4.2)
        d["aim_ang"] = 1.05 + sweep
        return d
    # ---- stop, turn toward them; the beam swings up onto his face; the jolt
    pose_keys = [(-1, EMB_WALK), (k["e1"], EMB_BASE), (k["jolt"], EMB_JOLT), (k["jolt"] + 0.16, EMB_NERV),
                 (k["l1e"] + 0.3, EMB_BASE)]
    cf = k["conflict"]
    pose_keys += [(k["r_reach"], EMB_PINCH), (k["r_grab"] + 0.15, EMB_CUP),
                  (k["r_breath"], EMB_CUPB), (k["r_breath"] + 0.55, EMB_CUP),
                  (k["r_pocket"], EMB_PINCH), (k["r_gone"] + 0.1, EMB_BASE),
                  (k["k_reach"], EMB_PINCH), (k["k_have"] + 0.1, EMB_CUP), (k["k_back"], EMB_BASE)]
    p = state_at(t, pose_keys, 0.22)
    if t < k["jolt"] + 0.3 and (p[1] is EMB_JOLT or p[0] is EMB_JOLT):
        p = (p[0], p[1], smoothstep(seg(t, k["jolt"], k["jolt"] + 0.07)) if p[1] is EMB_JOLT else p[2])
    d["pose"] = p
    if p[0] is EMB_WALK:
        d["pose_t"] = 0.0            # walk frozen on a contact while it blends out
    d["turn"] = tw(t, [(k["e_turn"], 0.15), (k["e_turn"] + 0.3, 0.7), (cf, 0.7), (cf + 0.35, 0.45),
                       (k["click"] + 0.45, 0.45), (k["click"] + 0.75, 0.7)])
    # ---- the flashlight hand (right = far hand) + where the beam points
    face_aim = T_FACE
    floor_aim = (610, 1478)
    nt = k["notice"]
    aim = tw(t, [(k["swing0"], (560, 1420)), (k["swing1"], face_aim), (nt + 0.12, face_aim),
                 (k["c_found"], CUR_EYE), (k["l4"] + 0.05, CUR_EYE), (k["l4"] + 0.65, floor_aim),
                 (cf, floor_aim), (cf + 0.35, (520, 1495)), (k["click"] + 0.5, (520, 1495)),
                 (k["click"] + 0.8, (470, 1498))])
    # startle wobble
    j = t - k["jolt"]
    if 0 <= j < 0.6:
        aim = (aim[0], aim[1] + 34 * math.sin(j * 30) * (1 - j / 0.6) ** 2)
    d["aim"] = aim
    hand_r = tw(t, [(k["e1"], (XE + 92, 1165)), (k["swing0"], (XE + 95, 1150)), (k["swing1"], (XE + 112, 1022)),
                    (nt + 0.12, (XE + 112, 1022)), (k["c_found"], (XE + 105, 1070)),
                    (k["l4"] + 0.05, (XE + 105, 1070)), (k["l4"] + 0.65, (XE + 98, 1118)),
                    (cf, (XE + 98, 1118)), (cf + 0.35, (XE + 90, 1130))])
    gx, gy = hand_r
    ang = math.atan2(aim[1] - gy, aim[0] - gx)
    d["aim_ang"] = ang
    d["reach"] = {"r": (gx, gy, 1.0, ang)}
    # ---- left (near) hand: jolt to the chest, the recorder, the keycard
    pocket = (XE - 15 + 4, FY - 502 + 6) if t < cf + 0.2 or t > k["click"] + 0.6 else (XE - 23 + 4, FY - 502 + 6)
    jt = k["jolt"]
    wl = tw(t, [(jt, 0.0), (jt + 0.1, 1.0, ease_out), (jt + 0.5, 1.0), (jt + 0.9, 0.0)])
    if wl > 0:
        d["reach"]["l"] = (XE + 30, 1012, wl)
    if k["r_reach"] - 0.05 <= t < k["r_gone"] + 0.45:
        palm = tw(t, [(k["r_grab"], pocket), (k["r_up"], (XE + 24, 1002)),
                      (k["click"] + 0.6, (XE + 26, 1000)), (k["l6_pocket"] - 0.1, (XE + 92, 1000)),
                      (k["l6_stop"], (XE + 98, 996)), (k["r_pocket"], (XE + 98, 996)),
                      (k["r_gone"], (pocket[0] + 2, pocket[1] - 6))])
        w = tw(t, [(k["r_reach"], 0.0), (k["r_grab"], 1.0), (k["r_gone"], 1.0), (k["r_gone"] + 0.4, 0.0)])
        ha = tw(t, [(k["r_grab"], -1.2), (k["r_up"], -0.25), (k["r_pocket"], -0.25), (k["r_gone"], -1.2)])
        d["reach"]["l"] = (palm[0], palm[1], w, ha)
        if k["r_grab"] <= t < k["r_gone"]:
            led = 1.0 if (t % 1.0) < 0.45 else 0.15
            if t >= k["led_off"]:
                led = 0.0
            rot = tw(t, [(k["r_grab"], -0.9), (k["r_up"], -0.12), (k["l6_stop"], -0.12),
                         (k["l6_stop"] + 0.3, -0.32), (k["r_pocket"], -0.3), (k["r_gone"], -1.2)])
            d["rec"] = dict(led=led, rot=rot, button=tw(t, [(k["press"], 0.0), (k["press"] + 0.08, 1.0, ease_out),
                                                            (k["press"] + 0.32, 1.0), (k["press"] + 0.5, 0.25)]))
    if k["k_reach"] - 0.05 <= t < k["k_back"] + 0.6:
        ch = emb_card_hand(t, k)
        palm = tw(t, [(k["k_reach"], (pocket[0], pocket[1] + 4)), (k["k_have"], (pocket[0], pocket[1] + 4)),
                      (k["k_out"], (583, 1068)), (k["k_take"], (583, 1068)), (k["k_back"] + 0.5, (XE + 20, 1150))])
        w = tw(t, [(k["k_reach"], 0.0), (k["k_reach"] + 0.3, 1.0), (k["k_take"] + 0.1, 1.0), (k["k_back"] + 0.5, 0.0)])
        ha = tw(t, [(k["k_have"], -1.2), (k["k_out"], -0.15)])
        d["reach"]["l"] = (palm[0], palm[1], w, ha)
        if k["k_have"] <= t < k["k_take"]:
            d["card"] = dict(rot=tw(t, [(k["k_have"], -1.0), (k["k_out"], 0.08)]),
                             s=tw(t, [(k["k_have"], 0.12), (k["k_have"] + 0.25, 0.19)]))
    # ---- the LED in his chest pocket (blinks until he takes the recorder out)
    if t < k["r_grab"]:
        hot = smoothstep(seg(t, k["led"], k["led"] + 0.25))
        d["led"] = 1.0 if (t % 1.0) < 0.45 else 0.12 - 0.07 * hot
        d["led_glow"] = 0.55 + 0.9 * hot
        d["led_s"] = 0.9 + 0.3 * hot
        d["led_pos"] = pocket
    # ---- expression, eyes, blush
    d["expr"] = state_at(t, [(0, "neutral"), (jt, "surprised"), (k["l1e"] + 0.3, "neutral"),
                             (k["c_found"] + 0.02, "frozen_shock"), (k["l3"] - 0.08, "awe"),
                             (k["l4"] - 0.05, "curious"), (k["l5"], "neutral"), (k["blink"], "deadpan"),
                             (k["led"], "neutral"), (k["led_off"] + 0.35, "deadpan"),
                             (k["l6e"] + 0.3, "neutral"), (k["S15"], "neutral"), (k["nod0"] + 0.4, "soft_smile")],
                         0.18)
    if t >= k["c_found"] and t < k["l3"] - 0.08:
        d["expr"] = "frozen_shock"
    d["blush"] = tw(t, [(jt, 0.12), (jt + 0.35, 0.5), (k["l1e"] + 0.4, 0.45), (k["l2e"], 0.35),
                        (k["c_found"], 0.35), (k["l3e"], 0.42), (k["l5e"], 0.3), (k["led"], 0.22),
                        (k["r_look_t"], 0.22), (k["r_look_t"] + 0.6, 0.62), (k["r_look_b"] + 0.2, 0.6),
                        (k["r_breath"] + 0.5, 0.25), (k["click"], 0.18), (k["l6"], 0.1),
                        (k["S15"], 0.12)])
    d["sweat"] = tw(t, [(k["c_found"], 0.0), (k["c_found"] + 0.4, 0.25), (k["l5e"], 0.2), (k["blink"] + 1.2, 0.0)])
    d["glasses_dy"] = tw(t, [(jt, 0.0), (jt + 0.06, 7.0), (jt + 0.45, 2.0), (k["l1e"], 0.0)])
    f = {}
    look = (0.9, -0.05)
    if t < k["l1e"] + 0.3:
        look = tw(t, [(k["e1"], (0.6, 0.2)), (k["swing0"], (0.8, 0.35)), (k["swing1"], (0.95, -0.1)),
                      (k["l1_down"] - 0.12, (0.95, -0.05)), (k["l1_down"], (-1.25, 0.1)),
                      (k["l1_down"] + 0.42, (-1.25, 0.1)), (k["l1_down"] + 0.6, (0.95, -0.05))])
        f.update(fk(t, {
            "head_turn": [(k["l1_down"] + 0.05, 0.0), (k["l1_down"] + 0.2, -0.75), (k["l1_down"] + 0.5, -0.75),
                          (k["l1_down"] + 0.72, 0.0)],
            "brow": [(jt, 0.0), (jt + 0.1, 0.35), (k["l1e"], 0.25), (k["l1e"] + 0.5, 0.1)],
            "brow_ang": [(jt, 0.0), (jt + 0.2, 0.25), (k["l1e"] + 0.5, 0.25)],
            "squash": [(jt, 0.0), (jt + 0.06, -0.08), (jt + 0.3, 0.0)],
            "head_nod": [(k["l1_what"] - 0.1, 0.0), (k["l1_what"] + 0.2, 0.06), (k["l1e"], 0.04)],
        }))
    nt = k["notice"]
    if k["l1e"] + 0.3 <= t < k["l4"]:
        look = tw(t, [(k["l1e"] + 0.3, (0.95, -0.05)), (nt + 0.05, (0.95, -0.05)),
                      (nt + 0.3, (0.8, 0.55)), (k["c_found"], (0.75, 0.95)), (k["l4"], (0.75, 0.95))])
        f.update(fk(t, {
            "brow_r": [(k["l2_story"], 0.0), (k["l2_story"] + 0.3, 0.3), (nt, 0.25), (nt + 0.3, 0.0)],
            "press": [(k["l2e"], 0.0), (k["l2e"] + 0.25, 0.3), (nt, 0.25), (nt + 0.3, 0.0)],
            "brow_ang": [(k["l1e"] + 0.3, 0.25), (k["l2"], 0.1)],
            "head_nod": [(nt + 0.15, 0.0), (nt + 0.45, 0.14), (k["l3"], 0.14), (k["l3e"], 0.18)],
            "head_turn": [(nt + 0.15, 0.0), (nt + 0.45, 0.1)],
        }))
    if k["l4"] <= t < k["led"]:
        look = tw(t, [(k["l4"], (0.75, 0.95)), (k["l4"] + 0.12, (0.75, 0.95)), (k["l4"] + 0.32, (0.95, -0.12)),
                      (k["l5e"], (0.95, -0.1)), (k["blink"], (0.9, -0.05))])
        f.update(fk(t, {
            "head_nod": [(k["l4"] + 0.2, 0.18), (k["l4"] + 0.48, 0.0)],
            "head_turn": [(k["l4"] + 0.2, 0.1), (k["l4"] + 0.48, 0.0)],
            "brow_l": [(k["l4_eyes"], 0.0), (k["l4_eyes"] + 0.25, 0.2)],
            "brow_ang": [(k["l5"], 0.0), (k["l5_win"], 0.0), (k["l5_win"] + 0.3, 0.2), (k["blink"], 0.12)],
            "open": [(k["blink"] + 0.1, 0.0), (k["blink"] + 0.5, 0.1), (k["led"], 0.06)],
            "head_tilt": [(k["blink"] + 0.1, 0.0), (k["blink"] + 0.9, 0.07), (k["led"], 0.05)],
        }))
        # the long slow blink
        b0 = k["blink"] + 0.18
        if b0 <= t < b0 + 1.35:
            d["blink"] = tw(t, [(b0, 0.0), (b0 + 0.42, 1.0), (b0 + 0.9, 1.0), (b0 + 1.32, 0.0)])
    led = k["led"]
    if led <= t < k["S11"]:
        look = tw(t, [(led, (0.9, -0.05)), (led + 0.22, (0.9, -0.05)), (led + 0.38, (-0.2, 1.15)),
                      (k["r_up"] - 0.1, (-0.1, 1.1)), (k["r_up"] + 0.15, (0.25, 1.05)),
                      (k["r_look_t"], (0.25, 1.05)), (k["r_look_t"] + 0.15, (1.0, -0.05)),
                      (k["r_look_b"], (1.0, -0.05)), (k["r_look_b"] + 0.15, (0.25, 1.05)),
                      (k["click"] + 0.5, (0.25, 1.05)), (k["click"] + 0.68, (1.0, -0.05))])
        f.update(fk(t, {
            "head_nod": [(led + 0.3, 0.0), (led + 0.55, 0.2), (k["r_look_t"] + 0.1, 0.2),
                         (k["r_look_t"] + 0.3, 0.02), (k["r_look_b"] + 0.1, 0.02), (k["r_look_b"] + 0.3, 0.18),
                         (k["click"] + 0.6, 0.18), (k["click"] + 0.85, 0.0)],
            "head_turn": [(k["r_look_t"] + 0.1, 0.0), (k["r_look_t"] + 0.3, 0.15),
                          (k["r_look_b"] + 0.1, 0.15), (k["r_look_b"] + 0.3, 0.0)],
            "brow_ang": [(k["r_up"], 0.0), (k["r_up"] + 0.4, 0.3), (k["r_look_t"] + 0.3, 0.45),
                         (k["r_breath"], 0.35), (k["r_breath"] + 0.6, 0.05), (k["click"] + 0.6, 0.0)],
            "press": [(k["r_look_b"] + 0.2, 0.0), (k["r_look_b"] + 0.5, 0.45), (k["r_breath"] + 0.3, 0.45),
                      (k["r_breath"] + 0.7, 0.0)],
            "brow": [(k["r_breath"], 0.0), (k["r_breath"] + 0.4, 0.12), (k["r_breath"] + 0.9, 0.0)],
            "lid": [(k["press"], 0.0), (k["press"] + 0.3, 0.08)],
        }))
        if k["r_look_t"] <= t < k["r_look_b"]:
            d["drift"] = False
    if k["S11"] <= t < k["l7"] - 0.3:
        look = tw(t, [(k["S11"], (1.0, -0.05)), (k["l6_pocket"], (1.0, -0.05)), (k["l6_pocket"] + 0.15, (0.6, 0.6)),
                      (k["l6_calc"] + 0.2, (0.6, 0.6)), (k["l6_calc"] + 0.35, (1.0, -0.05))])
        f.update(fk(t, {
            "smirk": [(k["l6_stop"], 0.0), (k["l6e"], 0.3), (k["l6e"] + 1.2, 0.15)],
            "lid": [(k["S11"], 0.08), (k["l6e"] + 0.4, 0.04)],
            "head_tilt": [(k["l6_calc"], 0.0), (k["l6_stop"], 0.05), (k["l6e"] + 0.3, 0.0)],
        }))
        d["drift"] = False
    if t >= k["l7"] - 0.3:
        look = tw(t, [(k["l7"] - 0.3, (1.0, -0.05)), (k["l7_nine"] - 0.3, (1.0, -0.05)),
                      (k["l7_nine"] - 0.15, (1.15, -0.25)), (k["l7_nine"] + 0.25, (1.15, -0.25)),
                      (k["l7_nine"] + 0.4, (1.0, -0.05)), (k["k_reach"], (1.0, -0.05)),
                      (k["k_reach"] + 0.12, (-0.2, 1.0)), (k["k_have"], (-0.2, 1.0)),
                      (k["k_have"] + 0.15, (1.0, -0.02))])
        f.update(fk(t, {
            "head_turn": [(k["l7_nine"] - 0.2, 0.0), (k["l7_nine"], 0.12), (k["l7_nine"] + 0.4, 0.0)],
            "head_nod": [(k["k_reach"], 0.0), (k["k_reach"] + 0.2, 0.12), (k["k_have"] + 0.1, 0.12),
                         (k["k_have"] + 0.3, 0.0), (k["l8_be"], 0.0), (k["l8_be"] + 0.25, 0.07),
                         (k["l8e"] + 0.2, 0.0)],
            "brow_ang": [(k["l8"] - 0.4, 0.0), (k["l8"], 0.3), (k["l8e"] + 0.6, 0.25), (k["nod0"] + 0.4, 0.05)],
            "brow": [(k["l8"] - 0.4, 0.0), (k["l8"], 0.1)],
            "lid": [(k["l8"] - 0.4, 0.0), (k["l8"], -0.04)],
        }))
        if t >= k["l8"] - 0.4:
            d["drift"] = False
            sb = k["l8e"] + 0.25
            if sb <= t < sb + 1.0:
                d["blink"] = tw(t, [(sb, 0.0), (sb + 0.3, 1.0), (sb + 0.5, 1.0), (sb + 0.85, 0.0)])
    # the freeze: no blinks, no saccades
    if k["c_found"] <= t < k["l3"] + 0.2:
        d["blink"] = 0.0
        d["drift"] = False
    d["look"] = look
    d["face"] = f
    return d


# --------------------------------------------------------------------------- Curiosity
def cur_state(t, k):
    st = k["steps"]
    d = dict(x=C0, pose="sit", pose_from=None, pose_mix=1.0, pose_t=None, face=1.0, expr="sad",
             ears=0.15, look=(-0.85, -0.1), tilt=0.0, tail_curl=0.0, blink=None, glow=0.95, glint=None)
    ts = k["t_stop"]
    # ---- alone, hears him, looks back: surprised -> hopeful; then the footsteps
    if t < k["c_up"]:
        d["face"] = tw(t, [(0.78, 1.0), (1.18, -1.0), (st + 0.12, -1.0), (st + 0.36, 1.0, ease_out)])
        d["expr"] = "sad" if t < 0.96 else ("hopeful" if t < st + 0.24 else "wide")
        d["ears"] = tw(t, [(0.0, 0.15), (0.45, 0.15), (0.6, 0.32, ease_out), (1.02, 0.34),
                           (1.3, 0.62, ease_out_back), (ts + 0.95, 0.62), (ts + 1.4, 0.5),
                           (st + 0.1, 0.5), (st + 0.26, 1.0, ease_out_back)])
        d["look"] = tw(t, [(0.0, (-0.85, -0.1)), (0.78, (-0.8, -0.1)), (1.05, (0.4, -0.75)),
                           (ts + 0.4, (0.45, -0.85)), (st + 0.12, (0.45, -0.85)), (st + 0.3, (-0.9, 0.0))])
        d["tilt"] = tw(t, [(1.1, 0.0), (1.5, 0.08), (st, 0.08), (st + 0.2, -0.04)])
        d["blink"] = 0.0 if (t < 0.7 or 0.9 < t < 1.6) else None
        return d
    # ---- the scramble backwards behind his legs
    if t < k["c_sit"] + 0.3:
        mv0, mv1 = k["c_mv0"], k["c_mv1"]
        rate = (CH - C0) / (mv1 - mv0) / (creatures.SPEC_WALK_SPEED * SC)
        d["expr"] = "wide"
        d["ears"] = tw(t, [(k["c_up"], 1.0), (k["c_up"] + 0.4, 0.3)])
        d["look"] = (-0.9, -0.1)
        if t < mv0:
            d.update(pose="stand", pose_from="sit", pose_mix=seg(t, k["c_up"], mv0))
        elif t < mv1:
            d.update(pose="walk", pose_from="stand", pose_mix=seg(t, mv0, mv0 + 0.08),
                     pose_t=-(t - mv0) * rate)
            d["x"] = C0 + (CH - C0) * seg(t, mv0, mv1)
        else:
            d.update(x=CH, pose="sit", pose_from="walk", pose_mix=seg(t, mv1, mv1 + 0.28),
                     pose_t=-(mv1 - mv0) * rate)
        return d
    # ---- hiding (peeking left at Emb), found by the beam, watching
    d["x"] = CH
    d["expr"] = "wide" if t < k["S6"] else "curious"
    cf = k["c_found"]
    d["ears"] = tw(t, [(k["c_sit"], 0.3), (cf, 0.32), (cf + 0.25, 0.06, ease_out), (k["S6"], 0.1),
                       (k["S6"] + 0.01, 0.45), (k["click"] + 0.15, 0.45), (k["click"] + 0.4, 0.62, ease_out_back)])
    d["look"] = tw(t, [(k["c_sit"], (-0.9, -0.2)), (cf - 0.2, (-0.9, -0.25)), (cf, (-0.85, -0.45)),
                       (k["l3_spec"] + 0.15, (-0.85, -0.45)), (k["l3_spec"] + 0.32, (0.3, -1.0)),
                       (k["l3e"] - 0.05, (0.3, -1.0)), (k["l3e"] + 0.12, (-0.85, -0.45)),
                       (k["l5"] + 0.3, (-0.85, -0.45)), (k["l5"] + 0.5, (0.3, -1.0)),
                       (k["l5e"] - 0.2, (0.3, -1.0)), (k["l5e"], (-0.85, -0.4)),
                       (k["led"] + 0.85, (-0.85, -0.4)), (k["led"] + 1.0, (-0.95, -0.55))])
    d["tilt"] = tw(t, [(k["led"] + 0.95, 0.0), (k["led"] + 1.15, -0.1)])
    if cf - 0.05 <= t < k["l3e"] + 0.2:
        d["blink"] = 0.0
    d["glow"] = tw(t, [(cf - 0.1, 0.9), (cf + 0.05, 1.2), (cf + 0.8, 1.0)])
    if t >= cf:
        d["glint"] = cf
    # ---- after the click: creeps out to his front foot, sits; then the grin
    o0, o1 = k["c_out0"], k["c_out1"]
    if t >= k["S11"]:
        d["expr"] = "hopeful"
        d["ears"] = tw(t, [(k["S11"], 0.6), (k["l6_calc"], 0.6), (k["l6_calc"] + 0.3, 0.66)])
        d["look"] = tw(t, [(k["S11"], (-0.9, -0.45)), (o1, (-0.9, -0.5))])
        d["tilt"] = tw(t, [(k["l6_calc"], 0.0), (k["l6_calc"] + 0.3, -0.14), (k["l6e"] + 0.3, -0.05)])
        if t < o0:
            pass
        elif t < o1:
            rate = (CH - C1) / (o1 - o0) / (creatures.SPEC_WALK_SPEED * SC)
            if t < o0 + 0.15:
                d.update(pose="stand", pose_from="sit", pose_mix=seg(t, o0 - 0.05, o0 + 0.15))
            else:
                d.update(pose="walk", pose_from="stand", pose_mix=seg(t, o0 + 0.15, o0 + 0.25),
                         pose_t=(t - o0 - 0.15) * rate)
            d["x"] = CH - (CH - C1) * smoothstep(seg(t, o0 + 0.05, o1)) if t < o0 + 0.15 else \
                CH - (CH - C1) * seg(t, o0 + 0.05, o1)
        else:
            d.update(x=C1, pose="sit", pose_from="walk", pose_mix=seg(t, o1, o1 + 0.3),
                     pose_t=(o1 - o0 - 0.15) * (CH - C1) / (o1 - o0) / (creatures.SPEC_WALK_SPEED * SC))
    if t >= k["S12"]:
        s12 = k["S12"]
        d["face"] = 0.25
        d["look"] = tw(t, [(s12, (-0.6, -0.6)), (s12 + 0.15, (-0.6, -0.6)), (s12 + 0.32, (0.55, -0.85))])
        d["tilt"] = 0.0
        grin = s12 + 0.62
        if t < grin + 0.3:
            d["blink"] = 0.0
        d["expr"] = "proud" if t >= grin else "hopeful"
        d["ears"] = tw(t, [(k["S12"], 0.66), (grin, 0.66), (grin + 0.22, 0.86, ease_out_back)])
        d["tail_curl"] = tw(t, [(grin, 0.0), (grin + 0.5, 0.75)])
    if t >= k["S13"]:
        d["expr"] = "curious"
        d["face"] = tw(t, [(k["S13"], 0.3), (k["go_turn"], 0.3), (k["go_turn"] + 0.35, -1.0)])
        d["ears"] = tw(t, [(k["S13"], 0.6), (k["k_out"], 0.6), (k["k_out"] + 0.2, 0.78, ease_out_back),
                           (k["k_take"] + 0.6, 0.66)])
        d["tail_curl"] = tw(t, [(k["S13"], 0.5), (k["S13"] + 1.0, 0.25)])
        d["look"] = tw(t, [(k["S13"], (-0.85, -0.55)), (k["k_out"], (-0.85, -0.55)),
                           (k["k_out"] + 0.15, (0.05, -1.0)), (k["k_take"] + 0.2, (0.05, -1.0)),
                           (k["k_take"] + 0.45, (0.55, -0.85)), (k["l8"], (-0.85, -0.55)),
                           (k["nod0"] + 0.2, (-0.85, -0.55)), (k["nod0"] + 0.35, (0.6, -0.8)),
                           (k["go_turn"] + 0.2, (0.6, -0.8)), (k["go_turn"] + 0.35, (0.8, -0.5))])
        if t >= k["go_turn"]:
            d["expr"] = "hopeful"
            d["ears"] = tw(t, [(k["go_turn"], 0.66), (k["go_turn"] + 0.25, 0.85, ease_out_back)])
    return d


# --------------------------------------------------------------------------- drawing
def _flash_cb(state, lens_out):
    ang = state["aim_ang"]
    sc = state["s"]

    def hold(c, side, x, y, a):
        if side != "r":
            return
        r = props.flashlight(c, x, y, FLASH_S * sc / S, rot=ang, on=1.0)
        lens_out["lens"] = r["lens"]
        lens_out["angle"] = ang
    return hold


def _cone_path(c, x, y, ang, L, spread):
    a0, a1 = ang - spread / 2, ang + spread / 2
    c.move_to(x, y)
    c.line_to(x + L * math.cos(a0), y + L * math.sin(a0))
    c.arc(x, y, L, a0, a1)
    c.close_path()


def _beam_on_chars(c, lens, ang, L, spread, amt):
    """Torchlight on whatever is already in the (character) group: ATOP, so only the
    characters brighten. Three nested soft cones."""
    if amt <= 0.01:
        return
    x, y = lens
    col = core.hexc(WARM)
    c.save()
    c.set_operator(cairo.OPERATOR_ATOP)
    for sp, a in ((1.0, 0.07), (0.72, 0.07), (0.45, 0.08)):
        g = cairo.RadialGradient(x, y, 0, x, y, L)
        g.add_color_stop_rgba(0.0, col[0], col[1], col[2], a * amt * 1.3)
        g.add_color_stop_rgba(0.55, col[0], col[1], col[2], a * amt)
        g.add_color_stop_rgba(1.0, col[0], col[1], col[2], 0.0)
        _cone_path(c, x, y, ang, L, spread * sp)
        c.set_source(g)
        c.fill()
    c.restore()


def _tunnel_torch(c, e, lens):
    """Torchlight while he is still inside the side tunnel: a warm pool on the floor ahead
    and a faint haze wedge, clipped to the mouth (plus the floor just in front of it)."""
    if lens is None:
        return
    sc = e["s"] / S
    x, y = e["x"], e["y"]
    a = e["aim_ang"]
    px, py = x + 120 * sc + 70 * sc * math.cos(a) * 0.4, y + 40 * sc
    br = 0.35 + 0.65 * smoothstep(seg(sc, 0.2, 0.75))
    lx, ly = lens

    def paint(cc):
        core.radial_glow(cc, px, py, 330 * sc + 60, "#ffcf8a", 0.32 * br)
        core.radial_glow(cc, px, py, 150 * sc + 30, "#fff2d6", 0.42 * br)
        g = cairo.LinearGradient(lx, ly, px, py)
        wc = core.hexc("#ffe2b0")
        g.add_color_stop_rgba(0, wc[0], wc[1], wc[2], 0.22 * br)
        g.add_color_stop_rgba(1, wc[0], wc[1], wc[2], 0.04)
        cc.move_to(lx, ly)
        cc.line_to(px - 170 * sc, py)
        cc.line_to(px + 170 * sc, py)
        cc.close_path()
        cc.set_source(g)
        cc.fill()
    w_out = smoothstep(seg(sc, 0.5, 0.72))
    if w_out < 0.99:
        c.save()
        mouth_path(c)
        c.clip()
        core.fade_group(c, 1 - w_out, paint)
        c.restore()
    if w_out > 0.01:
        core.fade_group(c, w_out, paint)


def draw_world(ctx, t, k, cam, shot_name, exact=True):
    T = tired_state(t, k)
    E = embar_state(t, k)
    Cr = cur_state(t, k)
    sets.service_tunnel(ctx, t, "bg")
    lens = {}
    anchors = {}

    def draw_cur():
        anchors["cur"] = creatures.draw_specimen(
            ctx, Cr["x"], FY, SC, t, form=1.0, pose=Cr["pose"], expr=Cr["expr"], look=Cr["look"],
            glow=Cr["glow"], blink=Cr["blink"], flip=True, pose_t=Cr["pose_t"], face=Cr["face"],
            tilt=Cr["tilt"], ears=Cr["ears"], tail_curl=Cr["tail_curl"], pose_from=Cr["pose_from"],
            pose_mix=Cr["pose_mix"])

    def draw_emb():
        if not E["visible"]:
            return
        hold = _flash_cb(E, lens)

        def body(c):
            anchors["emb"] = human.draw_person(
                c, "embar", E["x"], E["y"], E["s"], t, pose=E["pose"], expr=E["expr"], look=E["look"],
                mouth=info_mouth("embar", t), face=E["face"], turn=E["turn"], blink=E["blink"],
                blush=E["blush"], sweat=E["sweat"], hold=hold, hold_sides="r", hold_layer="back",
                reach=E["reach"], pocket_side="near", drift=E["drift"], glasses_dy=E["glasses_dy"])
        if E["inside"] or E["dim"] > 0.01:
            ctx.save()
            if E["inside"]:
                mouth_path(ctx)
                ctx.rectangle(MOUTH[0] - 40, WALL_Y, MOUTH[2] + 80, 300)
                ctx.clip()
            sc = E["s"]
            bb = (E["x"] - 260 * sc, E["y"] - 1150 * sc, 520 * sc, 1200 * sc)
            sets.dimmed(ctx, bb, E["dim"], body)
            ctx.restore()
        else:
            body(ctx)
        a = anchors.get("emb")
        if a is None:
            return
        # props in his near (left) hand: drawn on top of the hand
        hx, hy, ha = a["hand_l"]
        if E["rec"] is not None:
            r = E["rec"]
            props.recorder(ctx, hx + 2, hy - 10, REC_S, t, led=r["led"], glow=0.5 if r["led"] > 0.5 else 0.0,
                           rot=r["rot"], button=r["button"])
            _thumb(ctx, hx, hy, r, t, k)
        if E["card"] is not None:
            props.keycard(ctx, hx + 4, hy - 7, E["card"]["s"], rot=E["card"]["rot"])

    def draw_tired():
        anchors["tired"] = human.draw_person(
            ctx, "tired", T["x"], T["y"], S, t, pose=T["pose"], expr=T["expr"], look=T["look"],
            mouth=info_mouth("tired", t), face=T["face"], turn=T["turn"], blink=T["blink"],
            pose_t=T["pose_t"], reach=T["reach"], drift=T["drift"], **TK)
        if T["card"]:
            hx, hy, _ = anchors["tired"]["hand_r"]
            props.keycard(ctx, hx - 6, hy - 6, 0.19, rot=tw(t, [(k["k_take"], 0.08), (k["k_take"] + 0.45, -0.18)]))

    # ---- characters into groups lit by the tunnel shade (+ the torch), then the cone.
    # Curiosity (always behind Tiredness in this staging) gets only half the shade: the
    # indigo body would otherwise sink into the dim tunnel.
    srect = shade_rect(k, shot_name)

    def shade(a):
        # the set's static "shade" layer, cached per shot over the shot's framing (the
        # set's own sprite is drawn live in close-ups: it is bigger than its cache limit)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        sets.sprite(ctx, ("s05_shade", shot_name), *srect,
                    lambda c: sets.service_tunnel(c, 0.0, "shade"), alpha=a)
        ctx.restore()
    ctx.push_group()
    draw_cur()
    shade(0.5)
    pat_c = ctx.pop_group()
    ctx.push_group()
    draw_emb()
    draw_tired()
    shade(1.0)
    beam = None
    if "lens" in lens and E["aim"] is not None:
        lx, ly = lens["lens"]
        ax, ay = E["aim"]
        L = clamp(math.hypot(ax - lx, ay - ly) * 1.22, 320, 1000)
        pw = smoothstep(seg(t, k["e1"], k["e1"] + 0.18))
        beam = (lx, ly, lens["angle"], L, 0.5, pw)
        _beam_on_chars(ctx, (lx, ly), lens["angle"], L, 0.56, pw)
    pat = ctx.pop_group()
    if beam is not None:
        # the torch on Curiosity too (it lands on it at "notice")
        ctx.push_group()
        ctx.set_source(pat_c)
        ctx.paint()
        _beam_on_chars(ctx, beam[:2], beam[2], beam[3], 0.56, beam[5])
        pat_c = ctx.pop_group()
    # torch light on the set
    if E["visible"] and t < k["e1"] + 0.15 and "lens" in lens:
        a_in = 1 - smoothstep(seg(t, k["e1"] - 0.02, k["e1"] + 0.15))
        if a_in > 0.01:
            ctx.push_group()
            _tunnel_torch(ctx, E, lens["lens"])
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a_in)
    if beam is not None:
        lx, ly, ang, L, sp, pw = beam
        fx.flashlight(ctx, lx, ly, ang, L, sp, t, lit_tunnel, key=("s05_lit", shot_name),
                      rect=view_rect(cam), power=pw, warm=0.35, haze=0.05, lens=False, exact=exact)
    ctx.set_source(pat_c)
    ctx.paint()
    ctx.set_source(pat)
    ctx.paint()
    # ---- emissive bits on top: the pocket LED, Curiosity's eyeshine
    if E["visible"] and E.get("led") is not None and "emb" in anchors:
        px, py = anchors["emb"]["pocket"]
        props.recorder(ctx, px + 6, py + 10, E.get("led_s", 0.9) * E["s"] / S, t, led=E["led"],
                       glow=E["led_glow"], only_led=True)
    # ---- his teal eyes stay bright (the rig's own glow is dimmed by the shade pass)
    if "tired" in anchors:
        a = anchors["tired"]
        op = (1 - a["blink"]) * (1 - 0.7 * T["squint"])
        if op > 0.02:
            for e_ in ("eye_l", "eye_r"):
                ex, ey = a[e_]
                core.radial_glow(ctx, ex, ey, 30, core.PAL["power"], 0.2 * op)
    jt = k["jolt"]
    if jt <= t < jt + 0.8 and "emb" in anchors:
        tx_, ty_ = anchors["emb"]["top"]
        fx.emote(ctx, "exclaim", tx_ + 42, ty_ - 62, 0.85, t, jt, dur=0.75)
    if Cr["glint"] is not None and "cur" in anchors:
        ex, ey = anchors["cur"]["eye_l"]
        fx.eye_glint(ctx, ex, ey, 0.7, t, Cr["glint"], dur=0.5)
    return anchors


def _thumb(ctx, hx, hy, r, t, k):
    """His thumb coming over the recorder's top button for the off click (custom shape)."""
    p0 = k["press"] - 0.35
    if not (p0 <= t < k["press"] + 0.75):
        return
    u = tw(t, [(p0, 0.0), (k["press"] - 0.05, 1.0), (k["press"] + 0.45, 1.0), (k["press"] + 0.75, 0.0)])
    dn = tw(t, [(k["press"] - 0.05, 0.0), (k["press"] + 0.06, 1.0, ease_out), (k["press"] + 0.32, 1.0),
                (k["press"] + 0.5, 0.0)])
    rs = REC_S
    rot = r["rot"]
    bx, by = props.RECORDER_BUTTON
    cx, cy = hx + 2, hy - 10
    ca, sa = math.cos(rot), math.sin(rot)

    def L(px, py):
        return (cx + (px * ca - py * sa) * rs, cy + (px * sa + py * ca) * rs)
    tip = L(bx + 4, by - 26 + 14 * dn)
    base = L(-78, 6)
    tx, ty = lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for w, col in ((30 * rs + 8, core.PAL["ink"]), (30 * rs + 1.5, core.PAL["e_skin"])):
        ctx.move_to(*base)
        ctx.line_to(tx, ty)
        core.set_color(ctx, col)
        ctx.set_line_width(w)
        ctx.stroke()
    core.circle(ctx, tx + 2 * rs, ty - 3 * rs, 7 * rs)
    core.fill(ctx, core.mixc(core.PAL["e_skin"], "#ffffff", 0.35))
    ctx.restore()


# lip-sync access (set per frame in render)
_INFO = [None]


def info_mouth(who, t):
    return _INFO[0].mouth(who, t)


# --------------------------------------------------------------------------- the card insert
def _capsule(ctx, p0, p1, w, fillc, ink, lw):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for ww, col in ((w + 2 * lw, ink), (w, fillc)):
        ctx.move_to(*p0)
        ctx.line_to(*p1)
        core.set_color(ctx, col)
        ctx.set_line_width(ww)
        ctx.stroke()


def draw_insert(ctx, t, k):
    """S14: the keycard in his (bandaged) hand, close. Screen space: a dim, defocused
    tunnel wall behind, a custom big hand (the rig's hands are not built for this size)."""
    t0 = k["S14"]
    u = seg(t, t0, k["S15"])
    with core.camera(ctx, 820, 1000, 3.1 + 0.15 * u):
        sets.service_tunnel(ctx, t, "bg", drip=False)
    ctx.rectangle(0, 0, core.W, core.H)
    core.fill(ctx, core.alpha("#0b0b12", 0.5))
    fx.vignette(ctx, 0.75, inner=0.35)
    core.radial_glow(ctx, 160, 1250, 760, "#ffcf8a", 0.10)      # Emb's torch on the floor, off left
    bob = 3 * math.sin((t - t0) * 2.4)
    cx, cy = 470 + 12 * u, 770 + bob - 16 * u
    rot = tw(t, [(t0, -0.16), (t0 + 0.6, -0.08), (k["S15"], -0.06)])
    cs = 1.72 + 0.06 * u
    ink = core.PAL["ink"]
    skin, skin_sh = core.PAL["t_skin"], core.PAL["t_skin_sh"]
    lw = 6
    # ---- behind the card: forearm (bandage, pushed-up sleeve), palm, curled fingers
    with core.saved(ctx, cx, cy, 1.0, rot):
        wr, el = (372, 238), (760, 1060)
        ang = math.atan2(el[1] - wr[1], el[0] - wr[0])
        _capsule(ctx, wr, el, 176, skin, ink, lw)
        for i in range(3):                     # the white wrap
            a_ = 0.24 + 0.15 * i
            px, py = lerp(wr[0], el[0], a_), lerp(wr[1], el[1], a_)
            with core.saved(ctx, px, py, 1.0, ang + math.pi / 2):
                core.rrect(ctx, -100, -38, 200, 80, 22)
                core.fill_stroke(ctx, "#f3f1ea" if i != 1 else "#e6e3da", ink, 5)
                ctx.move_to(-70, -8); ctx.line_to(60, 12)
                core.stroke(ctx, core.alpha("#b8b2a4", 0.8), 4)
        with core.saved(ctx, lerp(wr[0], el[0], 0.9), lerp(wr[1], el[1], 0.9), 1.0, ang + math.pi / 2):
            core.rrect(ctx, -128, -90, 256, 240, 46)           # navy sleeve pushed up to the elbow
            core.fill_stroke(ctx, core.PAL["t_hoodie"], ink, lw)
            ctx.move_to(-110, -40); ctx.line_to(110, -50)
            core.stroke(ctx, core.PAL["t_hoodie_dk"], 6)
        core.ellipse(ctx, 338, 118, 112, 142, -0.35)            # palm / back of the hand
        core.fill_stroke(ctx, skin, ink, lw)
        for i, fy_ in enumerate((-118, -52, 14)):              # curled fingers behind the card edge
            core.ellipse(ctx, 318, fy_, 62, 34, 0.12)
            core.fill_stroke(ctx, skin_sh if i % 2 else skin, ink, 5)
    props.keycard(ctx, cx, cy, cs, rot=rot, glint=smoothstep(seg(t, t0 + 0.35, t0 + 1.05)))
    # ---- in front: the thumb pressing on the card face
    with core.saved(ctx, cx, cy, 1.0, rot):
        base, tip = (402, 262), (276, 158)
        _capsule(ctx, base, tip, 74, skin, ink, lw)
        core.ellipse(ctx, tip[0] + 6, tip[1] + 4, 24, 17, math.atan2(tip[1] - base[1], tip[0] - base[0]))
        core.fill_stroke(ctx, core.mixc(skin, "#ffffff", 0.38), core.alpha(ink, 0.6), 3)
        ctx.move_to(300, 168); ctx.curve_to(285, 150, 280, 140, 268, 132)
        core.stroke(ctx, core.alpha(ink, 0.5), 4)


# --------------------------------------------------------------------------- render
def render(ctx, t, info):
    _INFO[0] = info
    k = keys_for(info)
    name, t0, camf = shot_at(t, k)
    if camf is None:
        draw_insert(ctx, t, k)
        return
    cam = camf(t)
    moving = name in ("S1", "S2", "S10", "S16")
    with core.camera(ctx, *cam):
        draw_world(ctx, t, k, cam, name, exact=not moving)


# --------------------------------------------------------------------------- sound
def SFX(info):
    k = keys_for(info)
    ev = []
    st = k["steps"]
    # Tiredness's slippers arriving (walk contacts every 0.5 s, ending on the stop)
    ts = k["t_stop"]
    for n in range(3, -1, -1):
        tt = ts - 0.5 * n
        if tt >= 0.0:
            ev.append((tt, "footstep", -10 + (0 if n == 0 else -2), 0.25))
    ev.append((0.58, "ears_perk", -4, -0.1))
    ev.append((1.22, "creature_chitter", -9, -0.1))
    # footsteps out of the side tunnel (echoing, getting closer)
    e0, e1 = k["e0"], k["e1"]
    tt = e0                     # his walk contacts (pose_t multiples of 0.5 s)
    while tt < e1 + 0.05:
        g = lerp(-18, -7, seg(tt, e0, e1))
        ev.append((tt, "footstep", g, -0.55))
        tt += 0.5
    ev.append((st + 0.22, "ears_perk", -2, -0.2))
    ev.append((k["c_mv0"] + 0.05, "scurry", -10, 0.1))
    ev.append((k["jolt"], "cloth_rustle", -6, -0.4))
    # the beam finds it
    ev.append((k["c_found"] + 0.02, "critter_squeak", -12, 0.05))
    # recorder: out of the pocket, the decision, the click
    ev.append((k["r_reach"] + 0.15, "cloth_rustle", -8, -0.3))
    ev.append((k["press"] + 0.04, "recorder_click", 2, -0.2))
    ev.append((k["r_pocket"] + 0.1, "cloth_rustle", -12, -0.3))
    # Curiosity creeps out; grins
    ev.append((k["c_out0"] + 0.2, "scratch_wood", -18, 0.0))
    ev.append((k["S12"] + 0.62, "creature_chitter", -6, 0.0))
    # keycard out of the coat, handed over
    ev.append((k["k_reach"] + 0.1, "cloth_rustle", -9, -0.3))
    # off toward CONTROL
    gw = k["go_walk"]
    for i in range(3):
        if gw + 0.5 * i < info.dur - 0.1:
            ev.append((gw + 0.5 * i, "footstep", -11 - 2 * i, 0.35))
    # the tunnel drip (same drip as s04, synced to the visual landing: 2.6 s cycle, lands at 70 %)
    tt = 0.7 * 2.6
    while tt < info.dur:
        ev.append((tt, "drip", -17, 0.35))
        tt += 2.6 * 2
    return ev
