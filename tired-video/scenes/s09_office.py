"""s09 — HushCorp office: "Feelings aren't data."

The cold glass office. The Boss looms in her tall chair behind a huge empty
desk; Embarrassment sits in a comically low guest chair, knees up, looking
up. Shot / reverse-shot dialogue, two inserts (the sweat "plip" on the carpet,
the pink slip under her finger) and a desk slide of the recorder.

All timing is derived from info cues / line + word starts (never hard-coded).
Shot list (scene-local, labels = cue/word anchors):
  wide_a    0            .. l02            establishing push-in; Emb explains with his hands
  boss_a    l02          .. "sweating"+.15 she interrupts; never blinks; eyes slide down on "sweating"
  emb_sweat               .. sweat+.12     Emb sweats, looks down on "carpet", a drop gathers and falls
  carpet    sweat+.12    .. sweat+.62     insert: the drop hits the carpet. plip.
  wide_b                  .. "He"-.1       he looks back up; she taps the tablet; Tiredness's photo flickers on the glass
  emb_photo               .. slide         "He touched it." realisation; l05 protective lean forward
  slide     slide        .. l07-.2        her hand flicks the recorder; it glides across the desk (pan)
  emb_rec                 .. l08          "Is that... a tracker?"
  boss_b    l08          .. "Or"-.12      "A recorder. Every word he says."
  slip                    .. l08.end+.1   insert (top-down): pink slip slides in under her fingertip, tap on "desk"
  emb_guilt               .. l10-.1       "That doesn't feel right..." eyes down, slide to the photo, back
  boss_c                  .. gulp-.05     reading the tablet, never looks up; swipe on "data"
  emb_gulp                .. end          gulp, takes the recorder, pockets it; red LED blinks through the coat
"""
import math

from engine import core, sets, props, fx, human
from engine.core import (state_at, tween, seg, clamp, lerp, smoothstep, ease_in_out, ease_out,
                         ease_in, ease_out_back)
from engine.human import draw_person, ground_from_seat

M = sets.OFFICE_MARKS
S = M["char_scale"]                                  # 0.75
BOSS_X, _BOSS_SEAT_Y = M["boss_seat"]
BOSS_GY = ground_from_seat("boss", _BOSS_SEAT_Y, S)  # feet line behind the desk
EMB_X, EMB_GY = M["guest_chair"]
DESK_Y = M["desk_top_y"]
# the marks slide from x 1110; start nearer her hand but clear of her body, stop within his reach
REC_A, REC_B = (1040, M["desk_slide"][0][1]), (556, M["desk_slide"][1][1])
REC_S = 0.85                                         # recorder size in the world
REC_HALF_H = 29 * REC_S
# the drop lands just in front of his shoes (a touch nearer the camera than the feet line)
DROP_X, DROP_Y = M["sweat_floor"][0] + 28, M["sweat_floor"][1] + 24
HOLO = (300, 520, 400, 330)                          # photo on the glass (world rect)
TAB_X, TAB_Y = 955, DESK_Y                           # tablet stand base on the desk
TAB_S = 0.5
EMB_H = human.metrics("embar")["height"] * S
BOSS_H = human.metrics("boss")["height"] * S

CAPTION_Y = 1450


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
class _T:
    pass


_TCACHE = {}


def _word(info, lid, k):
    ln = info.line(lid)
    ws = getattr(info, "_lip", {}).get(lid, {}).get("word_starts")
    n = len(ln.text.split())
    if ws and 0 <= k < len(ws):
        return ln.start + ws[k]
    return ln.start + ln.dur * k / max(1, n)


def _timing(info):
    key = (info.id, round(info.dur, 4), tuple(sorted(info.cues.items())))
    T = _TCACHE.get(key)
    if T is not None:
        return T
    T = _T()
    T.dur = info.dur
    for i in range(1, 11):
        ln = info.line(f"s09_l{i:02d}")
        setattr(T, f"l{i}", ln.start)
        setattr(T, f"e{i}", ln.end)
    w = lambda i, k: _word(info, f"s09_l{i:02d}", k)  # noqa: E731
    T.w = w
    T.sweat = info.cue("sweat")
    T.slide = info.cue("slide")
    T.gulp = info.cue("gulp")
    # beats
    T.l1_know, T.l1_how, T.l1_but = w(1, 1), w(1, 2), w(1, 5)
    T.l2_wreck = w(2, 5)
    T.l3_sweating, T.l3_carpet = w(3, 3), w(3, 6)
    T.drop0 = T.sweat - 0.42          # the drop starts gathering on his chin
    T.drop_off = T.sweat + 0.02       # it lets go
    T.plip = T.sweat + 0.26           # it hits the carpet
    T.l4_friend, T.l4_the, T.l4_he = w(4, 1), w(4, 2), w(4, 5)
    T.tap = T.l4_the - 0.16           # two taps on the tablet between "friend." and "The"
    T.holo = T.tap + 0.3              # photo flickers on
    T.l5_harm, T.l5_barely = w(5, 2), w(5, 4)
    T.push = T.slide + 0.15           # her two-finger push
    T.release = T.push + 0.3
    T.rec_stop = T.release + 0.75
    T.l7_tracker = w(7, 3)
    T.l8_every, T.l8_or, T.l8_clean, T.l8_desk = w(8, 2), w(8, 6), w(8, 9), w(8, 12)
    T.slip_in = T.l8_or - 0.02
    T.l9_feel, T.l9_right = w(9, 2), w(9, 3)
    T.l10_data = w(10, 2)
    T.swipe = T.l10_data + 0.05
    g = T.gulp
    T.gulp_fx = g + 0.04
    T.reach0, T.grab = g + 0.5, g + 0.8
    T.tuck = g + 1.15
    T.led0 = T.tuck + 0.04
    # shots
    T.shots = [
        (0.0, "wide_a"),
        (T.l2, "boss_a"),
        (T.l3_sweating + 0.15, "emb_sweat"),
        (T.sweat + 0.12, "carpet"),
        (T.sweat + 0.62, "wide_b"),
        (T.l4_he - 0.1, "emb_photo"),
        (T.slide, "slide"),
        (T.rec_stop - 0.28, "emb_rec"),
        (T.l8, "boss_b"),
        (T.l8_or - 0.12, "slip"),
        (T.e8 + 0.1, "emb_guilt"),
        (T.l10 - 0.1, "boss_c"),
        (T.gulp - 0.05, "emb_gulp"),
    ]
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


def _shot(t, T):
    cur, t0, nxt = T.shots[0][1], 0.0, T.dur
    for i, (ts, name) in enumerate(T.shots):
        if t >= ts:
            cur, t0 = name, ts
            nxt = T.shots[i + 1][0] if i + 1 < len(T.shots) else T.dur
    return cur, t0, nxt


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def tw(t, keys, ease=ease_in_out):
    return tween(t, keys, ease)


def bump(t, t0, t1, t2, t3):
    """0 -> 1 (t0..t1) hold -> 0 (t2..t3), eased."""
    return smoothstep(seg(t, t0, t1)) * (1 - smoothstep(seg(t, t2, t3)))


def lean_at(t, keys):
    return tween(t, keys, ease_in_out)


_IK_CACHE = {}


def _ik_fit(who, x, y, s, pose, side, target, turn, flip=False, it=8):
    """Find (tx, ty, tz) so the `side` hand lands on target (caller coords).

    A few secant steps against the real rig (drawn into a 1x1 dummy surface),
    cached per key. Returns the pose dict with the IK keys set."""
    key = (who, round(x, 1), round(y, 1), s, repr(sorted(pose.items())), side,
           (round(target[0], 1), round(target[1], 1)), turn, flip)
    if key in _IK_CACHE:
        return _IK_CACHE[key]
    import cairocffi as cairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    c = cairo.Context(surf)
    H = human.metrics(who)["height"] * s
    p = dict(pose)
    pre = f"a{side}_"
    p[pre + "ik"] = 1.0
    tx = p.get(pre + "tx", 0.1)
    ty = p.get(pre + "ty", (y - target[1]) / H)
    tz = p.get(pre + "tz", 0.3)
    if isinstance(ty, str):
        ty = (y - target[1]) / H
    fsign = -1.0 if (turn < 0) != flip else 1.0

    def hand(tz_, ty_):
        q = dict(p)
        q[pre + "tz"], q[pre + "ty"], q[pre + "tx"] = tz_, ty_, tx
        a = draw_person(c, who, x, y, s, 0.0, pose=q, turn=turn, flip=flip, shadow=False, drift=False,
                        blink=0.0)
        return a[f"hand_{side}"][:2]

    best = None
    for _ in range(it):
        hx, hy = hand(tz, ty)
        ex, ey = target[0] - hx, target[1] - hy
        err = math.hypot(ex, ey)
        if best is None or err < best[0]:
            best = (err, tz, ty)
        if err < 1.5:
            break
        # full 2x2 jacobian, damped Newton step
        d = 0.02
        ax, ay = hand(tz + d, ty)
        bx, by = hand(tz, ty + d)
        j11, j21 = (ax - hx) / d, (ay - hy) / d
        j12, j22 = (bx - hx) / d, (by - hy) / d
        det = j11 * j22 - j12 * j21
        if abs(det) < 1e-6:
            break
        dtz = (j22 * ex - j12 * ey) / det
        dty = (-j21 * ex + j11 * ey) / det
        m = max(abs(dtz), abs(dty))
        if m > 0.15:
            dtz, dty = dtz * 0.15 / m, dty * 0.15 / m
        tz = clamp(tz + dtz, -0.4, 0.9)
        ty = clamp(ty + dty, -0.2, 1.4)
    if best is not None:
        _, tz, ty = best
    p[pre + "tz"], p[pre + "ty"], p[pre + "tx"] = tz, ty, tx
    _IK_CACHE[key] = p
    return p


# ---------------------------------------------------------------------------
# portrait for the hologram (module level => stable cache key)
# ---------------------------------------------------------------------------
_PORT = {}


def _tired_portrait(ctx, cx, cy, s):
    """Head-and-shoulders surveillance photo of Tiredness (bored, headphones round
    his neck), drawn with the real rig."""
    rs = 0.95 * s
    if "dy" not in _PORT:
        import cairocffi as cairo
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        a = draw_person(c, "tired", 0, 0, 1.0, 0.0, pose="stand", expr="bored", headphones="neck",
                        shadow=False, drift=False, blink=0.0)
        _PORT["dy"] = a["head"][1]
        _PORT["dx"] = a["head"][0]
    hx, hy = cx, cy - 4 * s
    draw_person(ctx, "tired", hx - _PORT["dx"] * rs, hy - _PORT["dy"] * rs, rs, 0.0, pose="stand",
                expr="bored", headphones="neck", shadow=False, drift=False, blink=0.0,
                look=(0.0, 0.05), face={"lid": 0.06})


# ---------------------------------------------------------------------------
# EMBARRASSMENT
# ---------------------------------------------------------------------------
LOW = {"base": "sit_chair", "ll_p": 2.1, "ll_k": 2.5, "lr_p": 2.05, "lr_k": 2.45, "breath": 1.2}


def _P(**kw):
    d = dict(LOW)
    d.update(kw)
    return d


E_KNEES = _P(hunch=0.25)
E_HUNCH = _P(hunch=0.75, lean=0.06, nod=0.06,
             **{"al_ik": 1.0, "al_tx": 0.02, "al_ty": 0.23, "al_tz": 0.26, "al_h": "relaxed",
                "ar_ik": 1.0, "ar_tx": 0.0, "ar_ty": 0.22, "ar_tz": 0.27, "ar_h": "relaxed",
                "al_layer": "front", "ar_layer": "front", "al_wa": 1.3, "al_wabs": 0.5,
                "ar_wa": 1.3, "ar_wabs": 0.5})
E_PEER = _P(hunch=0.55, lean=0.14, nod=0.12)
E_CHEST = _P(hunch=0.4, lean=0.04,
             **{"al_ik": 1.0, "al_tx": 0.03, "al_ty": 0.36, "al_tz": 0.13, "al_h": "flat", "al_wa": -1.4,
                "al_wabs": 0.7, "al_layer": "front",
                "ar_ik": 1.0, "ar_tx": 0.02, "ar_ty": 0.34, "ar_tz": 0.14, "ar_h": "flat", "ar_wa": -1.4,
                "ar_wabs": 0.7, "ar_layer": "front"})
E_OPEN = _P(hunch=0.7, lean=0.02, tilt=0.06,
            **{"al_p": 0.15, "al_o": 0.25, "al_e": 1.7, "al_eo": 0.45, "al_w": -0.25, "al_h": "open", "al_tf": -1.0,
               "ar_p": 0.15, "ar_o": 0.25, "ar_e": 1.7, "ar_eo": 0.45, "ar_w": -0.25, "ar_h": "open",
               "ar_tf": -1.0})
E_FWD = _P(hunch=0.55, lean=0.14,
           **{"al_ik": 1.0, "al_tx": 0.1, "al_ty": 0.4, "al_tz": 0.3, "al_h": "open", "al_tf": -1.0,
              "al_wa": -1.3, "al_wabs": 0.8,
              "ar_ik": 1.0, "ar_tx": 0.1, "ar_ty": 0.42, "ar_tz": 0.32, "ar_h": "open", "ar_tf": -1.0,
              "ar_wa": -1.3, "ar_wabs": 0.8})
E_PLEAD = _P(hunch=0.5, lean=0.22, nod=-0.04,
             **{"al_ik": 1.0, "al_tx": -0.005, "al_ty": 0.3, "al_tz": 0.2, "al_h": "flat", "al_wa": -1.45,
                "al_wabs": 0.9, "al_layer": "front",
                "ar_ik": 1.0, "ar_tx": -0.005, "ar_ty": 0.3, "ar_tz": 0.2, "ar_h": "flat", "ar_wa": -1.45,
                "ar_wabs": 0.9, "ar_layer": "front"})
E_HARMLESS = _P(hunch=0.45, lean=0.26, tilt=0.05,
                **{"al_p": 0.35, "al_o": 0.3, "al_e": 1.45, "al_eo": 0.5, "al_w": -0.2, "al_h": "open",
                   "al_tf": -1.0, "ar_p": 0.4, "ar_o": 0.3, "ar_e": 1.4, "ar_eo": 0.5, "ar_w": -0.2,
                   "ar_h": "open", "ar_tf": -1.0})
E_PRESENT = _P(hunch=0.55, lean=0.18, tilt=-0.04,
               **{"al_ik": 1.0, "al_tx": 0.02, "al_ty": 0.25, "al_tz": 0.25, "al_h": "relaxed", "al_layer": "front",
                  "ar_p": 0.55, "ar_o": 0.55, "ar_e": 1.2, "ar_eo": 0.35, "ar_w": -0.35, "ar_h": "open",
                  "ar_tf": -1.0})
E_RECOIL = _P(hunch=0.95, lean=-0.07, nod=0.04,       # hands drawn up under his chin, like a scared mouse
              **{"al_ik": 1.0, "al_tx": 0.0, "al_ty": 0.36, "al_tz": 0.15, "al_h": "relaxed", "al_wa": -1.6,
                 "al_wabs": 0.7, "al_layer": "front",
                 "ar_ik": 1.0, "ar_tx": 0.01, "ar_ty": 0.37, "ar_tz": 0.17, "ar_h": "relaxed", "ar_wa": -1.6,
                 "ar_wabs": 0.7, "ar_layer": "front"})
# after pocketing: guiltily rubbing the back of his neck with the far hand (keeps the pocket in view),
# the near hand limp on the seat
E_SLUMP = _P(hunch=0.65, lean=0.08, nod=0.1, tilt=-0.08,
             **{"al_ik": 1.0, "al_tx": 0.06, "al_ty": 0.08, "al_tz": -0.04, "al_h": "relaxed", "al_wa": 1.6,
                "al_wabs": 0.4,
                "ar_ik": 1.0, "ar_th": 1.0, "ar_hx": 70, "ar_hy": -40, "ar_h": "claw", "ar_layer": "back",
                "ar_bend": -1.0, "ar_wa": -1.9, "ar_wabs": 0.7})
E_WRING = _P(hunch=0.65, lean=0.05, nod=0.05,
             **{"al_ik": 1.0, "al_tx": 0.0, "al_ty": 0.3, "al_tz": 0.22, "al_h": "relaxed", "al_wa": 1.4,
                "al_wabs": 0.6, "al_layer": "front",
                "ar_ik": 1.0, "ar_tx": -0.01, "ar_ty": 0.29, "ar_tz": 0.23, "ar_h": "relaxed", "ar_wa": 1.4,
                "ar_wabs": 0.6, "ar_layer": "front"})


# at turn=+1 the NEAR arm is "l"
def _emb_reach_pose(target):
    base = dict(E_HUNCH)
    base.update({"al_h": "grip", "al_layer": "front", "al_wa": 0.2, "al_wabs": 0.5, "lean": 0.4,
                 "al_tx": 0.1, "al_tz": 0.45, "al_ty": 0.4, "hunch": 0.45})
    return _ik_fit("embar", EMB_X, EMB_GY, S, base, "l", target, 1.0)


def _emb_pocket_pose(target):
    base = dict(E_HUNCH)
    base.update({"al_h": "grip", "al_layer": "front", "al_wa": -1.0, "al_wabs": 0.5, "lean": 0.06,
                 "al_tx": 0.0, "al_tz": 0.18, "al_ty": 0.3})
    return _ik_fit("embar", EMB_X, EMB_GY, S, base, "l", target, 1.0)


_EMB_POCKET = {}


def _emb_pocket_xy():
    if "p" not in _EMB_POCKET:
        import cairocffi as cairo
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        a = draw_person(c, "embar", EMB_X, EMB_GY, S, 0.0, pose=E_HUNCH, turn=1.0, shadow=False,
                        drift=False, blink=0.0)
        _EMB_POCKET["p"] = a["pocket"][:2]
    return _EMB_POCKET["p"]


# gaze targets (look vectors) for Emb (turn=1, low chair)
LK_BOSS = (0.72, -0.42)
LK_PHOTO = (0.22, -1.05)
LK_FLOOR = (0.25, 1.0)
LK_REC = (0.62, 0.42)
LK_POCKET = (0.05, 0.95)


def _emb_state(t, T):
    """All of Embarrassment's acting: pose, expression, eyes, face deltas."""
    g = T.gulp
    # ---------------- pose
    pk = [(0.0, E_KNEES), (T.l1 - 0.28, E_CHEST), (T.l1_how - 0.06, E_OPEN), (T.l1_but - 0.08, E_FWD),
          (T.l2 + 0.25, E_HUNCH),
          (T.l3_carpet + 0.05, E_PEER), (T.sweat + 0.66, E_HUNCH),
          (T.l5 - 0.12, E_PLEAD), (T.l5_harm - 0.08, E_HARMLESS), (T.l5_barely - 0.1, E_PRESENT),
          (T.e5 + 0.15, E_WRING),
          (T.rec_stop - 0.06, E_RECOIL), (T.e7 + 0.25, E_WRING)]
    pose = state_at(t, pk, 0.26)
    # ---- gulp: reach, grab, pocket
    rec_xy = (REC_B[0], DESK_Y - REC_HALF_H)
    if t >= T.reach0 - 0.2:
        reach = _emb_reach_pose((rec_xy[0] - 6, rec_xy[1] + 4))
        pocket = _emb_pocket_pose(_emb_pocket_xy())
        if t < T.grab:
            k = ease_out_back(seg(t, T.reach0, T.grab), 1.2)
            antic = bump(t, T.reach0 - 0.2, T.reach0 - 0.05, T.reach0 - 0.05, T.reach0 + 0.05)
            base = dict(E_WRING)
            base["lean"] = E_WRING["lean"] - 0.06 * antic
            pose = (base, reach, k)
        elif t < T.tuck:
            pose = (reach, pocket, ease_in_out(seg(t, T.grab + 0.04, T.tuck)))
        else:
            pat = dict(pocket)
            pat["lean"] = pocket["lean"] + 0.02 * math.sin(seg(t, T.tuck, T.tuck + 0.2) * math.pi * 2)
            pose = (pat, E_SLUMP, ease_in_out(seg(t, T.tuck + 0.18, T.tuck + 0.55)))

    # ---------------- expression
    ek = [(0.0, "nervous_smile"), (T.l1 - 0.2, "pleading"), (T.l1_but, "nervous_smile"),
          (T.l2 + 0.12, "terrified"),
          (T.l3_carpet + 0.1, "guilty"),
          (T.plip + 0.05, "frozen_shock"),
          (T.sweat + 0.62, "guilty"),
          (T.holo + 0.25, "surprised"),
          (T.l4_he + 0.15, "terrified"),
          (T.l5 - 0.15, "pleading"), (T.l5_harm, "nervous_smile"), (T.l5_barely, "nervous_smile"),
          (T.e5 + 0.4, "terrified"),
          (T.l7 - 0.05, "terrified"),
          (T.e7 + 0.3, "guilty"),
          (T.e8 + 0.1, "guilty"),
          (T.l10 - 0.1, "sad"),
          (g + 0.0, "terrified"), (g + 0.5, "guilty")]
    expr = state_at(t, ek, 0.22)

    # ---------------- eyes (pupils lead, the head follows ~0.15 s later)
    lk = [(0.0, LK_BOSS),
          (T.l3_carpet - 0.05, LK_BOSS), (T.l3_carpet + 0.12, LK_FLOOR),
          (T.sweat + 0.6, LK_FLOOR), (T.sweat + 0.72, LK_BOSS),
          (T.l4_friend + 0.15, LK_BOSS),
          (T.holo + 0.12, LK_BOSS), (T.holo + 0.26, LK_PHOTO),
          (T.l4_he + 0.25, LK_PHOTO), (T.l4_he + 0.4, LK_BOSS),
          (T.e5 + 0.25, LK_BOSS), (T.e5 + 0.38, LK_REC),   # her hand moves to the recorder
          (T.slide, LK_REC),
          (T.l7 - 0.15, LK_REC), (T.l7_tracker - 0.12, LK_REC), (T.l7_tracker, LK_BOSS),
          (T.e8 + 0.1, LK_REC),
          (T.l9_feel - 0.05, LK_REC), (T.l9_feel + 0.12, LK_PHOTO),
          (T.l9_right + 0.42, LK_PHOTO), (T.l9_right + 0.62, LK_REC),
          (g - 0.05, LK_BOSS), (g + 0.35, LK_BOSS), (g + 0.48, LK_REC),
          (T.grab + 0.08, LK_REC), (T.grab + 0.2, LK_POCKET)]
    look = tw(t, lk)
    hk = [(a + 0.15, b) for a, b in lk]
    head_look = tw(t, hk)
    face = {
        "head_turn": 0.12 * head_look[0] - 0.05,
        "head_nod": 0.16 * head_look[1],
    }

    # ---------------- blush / sweat
    blush = tw(t, [(0, 0.3), (T.l1, 0.35), (T.l2 + 0.2, 0.5), (T.l3_sweating, 0.58), (T.plip, 0.62),
                   (T.plip + 0.15, 0.78), (T.sweat + 0.8, 0.62), (T.holo, 0.55), (T.l4_he + 0.2, 0.18),
                   (T.l5, 0.32), (T.e5, 0.45), (T.l7, 0.5), (T.e7, 0.55), (T.l8_clean, 0.6),
                   (T.l9, 0.3), (T.e9, 0.22), (g, 0.3), (g + 0.5, 0.42)])
    sweat = tw(t, [(0, 0.25), (T.l2, 0.35), (T.l2_wreck, 0.55), (T.l3_sweating, 0.85), (T.plip + 0.3, 0.85),
                   (T.l4_he, 0.5), (T.e5, 0.45), (T.l7, 0.6), (T.e8, 0.65), (T.e9, 0.45), (g, 0.5)])

    # ---------------- subtle face keys
    # l01: eager brows, mouth spread
    face["brow"] = tw(t, [(0, 0.1), (T.l1, 0.25), (T.l2, 0.3), (T.l2 + 0.25, 0.15)])
    # interrupted: lips press, swallowed word
    face["press"] = (0.5 * bump(t, T.l2 + 0.1, T.l2 + 0.3, T.l3_sweating, T.l3_sweating + 0.3)
                     + 0.6 * bump(t, T.plip + 0.15, T.plip + 0.3, T.sweat + 0.75, T.sweat + 0.95)
                     + 0.45 * bump(t, T.e9 + 0.05, T.e9 + 0.25, g - 0.1, g)
                     + 0.5 * bump(t, T.tuck + 0.2, T.tuck + 0.4, T.dur, T.dur + 1))
    # the plip: eyes widen, pupils shrink (horror at his own sweat)
    face["eye_size"] = (0.12 * bump(t, T.plip, T.plip + 0.08, T.sweat + 0.6, T.sweat + 0.8)
                        + 0.14 * bump(t, T.l4_he + 0.1, T.l4_he + 0.25, T.l4_he + 0.9, T.l4_he + 1.2))
    face["pupil"] = (-0.3 * bump(t, T.plip, T.plip + 0.08, T.sweat + 0.6, T.sweat + 0.8)
                     - 0.35 * bump(t, T.l4_he + 0.1, T.l4_he + 0.25, T.l4_he + 0.9, T.l4_he + 1.2)
                     - 0.2 * bump(t, T.l7_tracker, T.l7_tracker + 0.12, T.e7 + 0.2, T.e7 + 0.5)
                     + 0.15 * bump(t, T.l9_feel + 0.1, T.l9_feel + 0.3, T.l9_right + 0.4, T.l9_right + 0.6))
    # realisation: mouth falls open a little
    face["open"] = (0.22 * bump(t, T.l4_he + 0.15, T.l4_he + 0.3, T.l5 - 0.3, T.l5 - 0.1)
                    + 0.12 * bump(t, T.l7 - 0.18, T.l7 - 0.05, T.l7 + 0.05, T.l7 + 0.1))
    # l09: worried brows (inner up), lid drop of self-doubt, a slow blink
    face["brow_ang"] = (0.35 * bump(t, T.l9 - 0.2, T.l9 + 0.1, T.e9 + 0.4, T.e9 + 0.8)
                        + 0.25 * bump(t, T.l5 - 0.15, T.l5, T.l5_harm, T.l5_harm + 0.2)
                        + 0.3 * bump(t, g + 0.4, g + 0.7, T.dur, T.dur + 1))
    face["lid"] = (0.12 * bump(t, T.l9, T.l9 + 0.3, T.e9 + 0.2, T.e9 + 0.5)
                   + 0.1 * bump(t, T.tuck + 0.1, T.tuck + 0.4, T.dur, T.dur + 1))
    # gulp: head squash on the swallow
    face["squash"] = 0.09 * math.sin(math.pi * seg(t, T.gulp_fx, T.gulp_fx + 0.32))
    # protective lean: anticipation back, then forward with overshoot
    lean_add = (-0.06 * bump(t, T.l5 - 0.35, T.l5 - 0.18, T.l5 - 0.18, T.l5 - 0.08)
                + 0.1 * (ease_out_back(seg(t, T.l5 - 0.1, T.l5 + 0.25), 2.5) - 1) * seg(t, T.l5 - 0.1, T.l5 - 0.09)
                * (1 - seg(t, T.l5 + 0.25, T.l5 + 0.26)))
    face["head_tilt"] = (0.05 * bump(t, T.l5_barely - 0.05, T.l5_barely + 0.15, T.e5, T.e5 + 0.3)
                         - 0.04 * bump(t, T.l9, T.l9 + 0.3, T.e9, T.e9 + 0.3))
    # forced blinks: slow judgement blink at the end of l09 (on himself)
    blink = None
    b0 = T.l9_right + 0.66
    if b0 - 0.05 < t < b0 + 0.9:
        blink = tween(t, [(b0, 0.0), (b0 + 0.22, 1.0), (b0 + 0.45, 1.0), (b0 + 0.75, 0.0)])
    if T.l4_he + 0.05 < t < T.l4_he + 1.0:
        blink = 0.0           # wide-eyed realisation: no blink
    glint = (bump(t, T.holo, T.holo + 0.06, T.holo + 0.18, T.holo + 0.45)
             + 0.8 * bump(t, T.l7_tracker, T.l7_tracker + 0.06, T.l7_tracker + 0.12, T.l7_tracker + 0.4))
    return dict(pose=pose, expr=expr, look=look, face=face, blush=blush, sweat=sweat, blink=blink,
                glint=min(1.0, glint), lean_add=lean_add)


def _draw_emb(ctx, t, T, info):
    st = _emb_state(t, T)
    pose = st["pose"]
    la = st.pop("lean_add")
    if abs(la) > 1e-4:
        pose = {"base": pose, "lean": la} if isinstance(pose, str) else _with_lean(pose, la)
    a = draw_person(ctx, "embar", EMB_X, EMB_GY, S, t, pose=pose, expr=st["expr"], look=st["look"],
                    mouth=info.mouth("embar", t), face=st["face"], turn=1.0, blush=st["blush"],
                    sweat=st["sweat"], blink=st["blink"], glint=st["glint"])
    return a


def _with_lean(pose, la):
    if isinstance(pose, tuple):
        a, b, k = pose
        return (_with_lean(a, la), _with_lean(b, la), k)
    if isinstance(pose, str):
        return {"base": pose, "lean": la}
    d = dict(pose)
    d["lean"] = d.get("lean", 0.0) + la
    return d


# ---------------------------------------------------------------------------
# THE BOSS
# ---------------------------------------------------------------------------
_TY_DESK = (BOSS_GY - DESK_Y + 6) / BOSS_H
_TY_STEEPLE = (BOSS_GY - 1062) / BOSS_H
# steepled fingers in front of her chest, elbows on the desk: the still villain pose
B_REST = {"base": "sit_chair", "lean": 0.05, "breath": 0.35, "sway": 0.12, "hunch": -0.1,
          "al_ik": 1.0, "al_tx": -0.012, "al_ty": _TY_STEEPLE, "al_tz": 0.13, "al_h": "flat",
          "al_wa": -1.5, "al_wabs": 0.85, "al_layer": "front",
          "ar_ik": 1.0, "ar_tx": -0.012, "ar_ty": _TY_STEEPLE, "ar_tz": 0.13, "ar_h": "flat",
          "ar_wa": -1.5, "ar_wabs": 0.85, "ar_layer": "front"}


# one hand busy (tap / push / read): the other rests flat on the desk by her body
B_FREE = dict(B_REST)
B_FREE.update({"ar_ty": (BOSS_GY - DESK_Y + 4) / BOSS_H, "ar_tz": 0.1, "ar_tx": 0.02, "ar_h": "relaxed",
               "ar_wa": 0.5, "ar_wabs": 0.8})


def _tab_screen_pt(dx=0.0, dy=0.0):
    """A point on the tablet's screen (world)."""
    return (TAB_X - 6 + dx, TAB_Y - 62 + dy)


def _boss_tap_pose(lift=0.0, dx=0.0):
    """Index finger on (or `lift` px above) the tablet screen. Only call with a
    few fixed values (each one is an IK solve, cached)."""
    p = dict(B_FREE)
    p.update({"al_h": "point", "al_wa": 0.15, "al_wabs": 0.7})
    x, y = _tab_screen_pt(dx)
    return _ik_fit("boss", BOSS_X, BOSS_GY, S, p, "l", (x + 10, y - lift), -1.1)


def _boss_push_pose(x):
    """Two fingers resting on top of the recorder (at desk x), sliding it."""
    p = dict(B_FREE)
    p.update({"al_h": "flat", "al_wa": 0.0, "al_wabs": 0.95, "lean": 0.14, "al_tx": 0.06})
    return _ik_fit("boss", BOSS_X, BOSS_GY, S, p, "l", (x + 22, DESK_Y - 2 * REC_HALF_H - 7), -1.1)


PUSH_D = 110


def _rec_x(t, T):
    """The recorder's x on the desk (world)."""
    if t < T.push:
        return REC_A[0] + 6 * bump(t, T.push - 0.25, T.push - 0.1, T.push - 0.1, T.push)
    if t < T.release:
        return lerp(REC_A[0], REC_A[0] - PUSH_D, ease_in(seg(t, T.push, T.release)))
    x0 = REC_A[0] - PUSH_D
    k = seg(t, T.release, T.rec_stop)
    # constant deceleration glide: x = x0 - D*(2k - k^2)
    return x0 - (x0 - REC_B[0]) * (2 * k - k * k)


def _boss_state(t, T):
    # ---------------- pose / hands
    pose = B_REST
    # double tap on the tablet (between "friend." and "The")
    if T.tap - 0.45 < t < T.tap + 0.75:
        up = _boss_tap_pose(28)
        dn = _boss_tap_pose(0)
        if t < T.tap - 0.1:
            pose = (B_REST, up, ease_in_out(seg(t, T.tap - 0.45, T.tap - 0.1)))
        elif t < T.tap + 0.3:
            k = seg(t, T.tap - 0.1, T.tap + 0.3)
            # down (tap 1 at T.tap), up, down (tap 2 at T.tap+0.16), up
            v = tween(t, [(T.tap - 0.1, 0.0), (T.tap, 1.0), (T.tap + 0.08, 0.35), (T.tap + 0.16, 1.0),
                          (T.tap + 0.3, 0.0)])
            pose = (up, dn, v)
        else:
            pose = (up, B_REST, ease_in_out(seg(t, T.tap + 0.3, T.tap + 0.75)))
    # the recorder push
    if T.e5 - 0.1 < t < T.release + 0.6:
        p0 = _boss_push_pose(REC_A[0])
        p1 = _boss_push_pose(REC_A[0] - PUSH_D)
        if t < T.push - 0.25:
            pose = (B_REST, p0, ease_in_out(seg(t, T.e5 - 0.1, T.slide - 0.05)))
        elif t < T.release:
            k = (REC_A[0] - _rec_x(t, T)) / PUSH_D
            pose = (p0, p1, clamp(k, -0.1, 1.0))
        else:
            pose = (p1, B_REST, ease_in_out(seg(t, T.release + 0.05, T.release + 0.6)))
    # l10: reading the tablet, one finger on the screen; swipe on "data."
    r0 = T.e9 - 0.2
    if t > r0:
        rd0 = _boss_tap_pose(0.0, 8)
        rd1 = _boss_tap_pose(0.0, -26)
        if t < T.swipe + 0.25:
            rd = (rd0, rd1, ease_in_out(seg(t, T.swipe, T.swipe + 0.22)))
        else:
            rd = (rd1, rd0, ease_in_out(seg(t, T.swipe + 0.25, T.swipe + 0.6)))
        if t < r0 + 0.5:
            pose = (pose, rd, ease_in_out(seg(t, r0, r0 + 0.5)))
        else:
            pose = rd
    # ---------------- eyes
    lk_emb = (-0.82, 0.38)
    lk_down = (-0.9, 0.62)       # down at his sweat / the carpet
    lk_tab = (-0.55, 0.92)
    lk = [(0.0, lk_emb),
          (T.l3_sweating - 0.06, lk_emb), (T.l3_sweating + 0.08, lk_down),
          (T.l3_carpet + 0.1, lk_down), (T.l3_carpet + 0.3, lk_emb),
          (T.e9 - 0.25, lk_emb), (T.e9 - 0.05, lk_tab)]
    look = tw(t, lk)
    face = {
        # her only "moves": a 2 px lid narrowing on judgement words
        "lid": (0.06 * bump(t, T.l2_wreck, T.l2_wreck + 0.25, T.e2 + 0.3, T.e2 + 0.7)
                + 0.07 * bump(t, T.l8_every - 0.05, T.l8_every + 0.25, T.l8_or, T.l8_or + 0.4)
                + 0.04 * bump(t, T.l1_but, T.l1_but + 0.2, T.l2 + 0.4, T.l2 + 0.7)),
        "head_nod": 0.07 * smoothstep(seg(t, T.e9 - 0.15, T.e9 + 0.2)),
        "press": 0.25 * (1 - smoothstep(seg(t, T.l2 - 0.1, T.l2))) + 0.2 * bump(t, T.e8, T.e8 + 0.3, T.l10 - 0.2, T.l10),
    }
    blink = None
    if T.l1_but < t < T.sweat + 0.6:
        blink = 0.0              # she does not blink
    return dict(pose=pose, look=look, face=face, blink=blink)


def _draw_boss(ctx, t, T, info):
    st = _boss_state(t, T)
    return draw_person(ctx, "boss", BOSS_X, BOSS_GY, S, t, pose=st["pose"], expr="cold", look=st["look"],
                       mouth=info.mouth("boss", t), face=st["face"], turn=-1.1, blink=st["blink"])


# ---------------------------------------------------------------------------
# props
# ---------------------------------------------------------------------------
def _tablet_screen(ctx, sx, sy, sw, sh, t, T=None, scroll=0.0):
    fx.tablet_screen(ctx, sx - scroll * sw, sy, sw, sh, t, portrait_fn=_tired_portrait, t_on=None,
                     glow=False, bezel=False)
    if scroll > 0.001:
        ctx.rectangle(sx + sw * (1 - scroll), sy, sw * scroll + 2, sh)
        core.fill(ctx, "#dff4ff")
        props.hush_logo(ctx, sx + sw * (1.5 - scroll), sy + sh * 0.45, min(sw, sh) * 0.18, lw=0)


def _draw_tablet(ctx, t, T):
    """Tablet on a little stand, angled toward the Boss (screen faces right)."""
    glow = 0.4 + 0.6 * bump(t, T.tap - 0.02, T.tap + 0.04, T.tap + 0.25, T.tap + 0.7)
    scroll = ease_in_out(seg(t, T.swipe + 0.02, T.swipe + 0.3))
    # stand
    core.poly(ctx, [(TAB_X + 18, TAB_Y), (TAB_X - 4, TAB_Y), (TAB_X + 26, TAB_Y - 52), (TAB_X + 34, TAB_Y - 50)])
    core.fill_stroke(ctx, "#3a3d4c", "ink", 3.5)
    with core.saved(ctx, TAB_X, TAB_Y - 62, (0.62 * TAB_S, TAB_S), -0.18):
        props.tablet(ctx, 0, 0, 1.0, 0.0, t, glow=glow,
                     screen_fn=lambda c, sx, sy, sw, sh, tt: _tablet_screen(c, sx, sy, sw, sh, tt, T, scroll))
    # tap ring
    for k, tt in enumerate((T.tap, T.tap + 0.16)):
        p = seg(t, tt, tt + 0.35)
        if 0 < p < 1:
            x, y = _tab_screen_pt()
            core.ellipse(ctx, x, y, 8 + 26 * ease_out(p), 6 + 20 * ease_out(p))
            core.stroke(ctx, core.alpha("#7fe9ff", 1 - p), 3)


def _rec_pos(t, T, a_emb=None):
    """(x, y, visible) of the recorder in the world."""
    if t < T.grab or a_emb is None:
        return _rec_x(t, T), DESK_Y - REC_HALF_H, True
    if t < T.tuck:
        hx, hy, ang = a_emb["hand_l"]
        return hx, hy, True
    return 0, 0, False


def _rec_led(t, T):
    if t < T.led0:
        return None
    return 1.0 if ((t - T.led0) % 0.5) < 0.28 else 0.12


def _draw_recorder_desk(ctx, t, T):
    if t < T.grab:
        x = _rec_x(t, T)
        rock = 0.0
        if t > T.rec_stop:
            rock = 0.06 * math.sin(seg(t, T.rec_stop, T.rec_stop + 0.35) * math.pi * 2) * (
                1 - seg(t, T.rec_stop, T.rec_stop + 0.35))
        # little contact shadow
        core.ellipse(ctx, x, DESK_Y + 1, 40 * REC_S, 4)
        core.fill(ctx, core.alpha("ink", 0.18))
        props.recorder(ctx, x, DESK_Y - REC_HALF_H, REC_S, t, rot=rock)
        # speed lines while gliding fast
        if T.release < t < T.rec_stop - 0.25:
            sp = 1 - seg(t, T.release, T.rec_stop - 0.25)
            fx.motion_lines(ctx, x + 45 * REC_S, DESK_Y - REC_HALF_H, 0.0, 120 * sp, t, intensity=sp,
                            n=3, width=7, seed=9)


def _draw_drop(ctx, t, T, a_emb):
    """The sweat drop: gathers on his chin, lets go, falls; then the plip."""
    if T.drop0 < t < T.plip and a_emb is not None:
        mx, my = a_emb["mouth"]
        cx, cy = mx - 4, my + 30 * S
        if t < T.drop_off:
            k = seg(t, T.drop0, T.drop_off)
            r = (3 + 6 * ease_out(k)) * S * 1.4
            stretch = 1 + 0.6 * smoothstep(seg(k, 0.6, 1.0))
            _drop_shape(ctx, cx, cy + r * stretch * 0.6, r, stretch)
        else:
            k = (t - T.drop_off) / max(1e-3, T.plip - T.drop_off)
            y = lerp(cy, DROP_Y - 8, k * k)
            x = lerp(cx, DROP_X, k)
            _drop_shape(ctx, x, y, 9 * S * 1.4, 1.4)
    # splash
    p = seg(t, T.plip, T.plip + 0.35)
    if 0 < p < 1:
        for j in range(4):
            ang = math.pi * (0.15 + 0.7 * j / 3)
            d = 26 * ease_out(p)
            hgt = 30 * math.sin(math.pi * p) * (0.7 + 0.3 * (j % 2))
            x = DROP_X + math.cos(ang) * d * 1.3 * (1 if j >= 2 else -1) * (1.0 if j in (0, 3) else 0.5)
            y = DROP_Y - 4 - hgt
            core.circle(ctx, x, y, 3.2 * (1 - p * 0.6))
            core.fill_stroke(ctx, fx.SWEAT_BLUE, "ink", 1.6)
        core.ellipse(ctx, DROP_X, DROP_Y, 6 + 24 * ease_out(p), 2 + 6 * ease_out(p))
        core.stroke(ctx, core.alpha(fx.SWEAT_BLUE, 1 - p), 2.5)
    # a tiny comic "plip" for the muted viewer
    q = seg(t, T.plip, T.plip + 0.6)
    if 0 < q < 1:
        k = ease_out_back(seg(q, 0, 0.3), 2.2)
        a = 1 - smoothstep(seg(q, 0.7, 1.0))
        with core.saved(ctx, DROP_X + 34, DROP_Y - 30 - 8 * q, 0.22 * k, -0.12, alpha_=a):
            core.text(ctx, "plip", 0, 0, 120, "#ffffff", "comic", "center", outline="#1d1626",
                      outline_w=16)


def _drop_shape(ctx, x, y, r, stretch=1.0):
    ctx.move_to(x, y - r * 2.1 * stretch)
    ctx.curve_to(x + r * 0.5, y - r * 1.2 * stretch, x + r * 1.05, y - r * 0.4, x + r, y + r * 0.1)
    ctx.arc(x, y, r, 0.1, math.pi - 0.1)
    ctx.curve_to(x - r * 1.05, y - r * 0.4, x - r * 0.5, y - r * 1.2 * stretch, x, y - r * 2.1 * stretch)
    ctx.close_path()
    core.fill_stroke(ctx, fx.SWEAT_BLUE, "ink", max(1.5, r * 0.32))
    core.ellipse(ctx, x - r * 0.35, y - r * 0.2, r * 0.22, r * 0.38, -0.3)
    core.fill(ctx, (1, 1, 1, 0.85))


def _wet_spot(ctx, t, T):
    if t > T.plip:
        a = 0.3 * smoothstep(seg(t, T.plip, T.plip + 0.2))
        core.ellipse(ctx, DROP_X, DROP_Y, 13, 3.5)
        core.fill(ctx, core.alpha("#6f7d8c", a))


# ---------------------------------------------------------------------------
# the world (everything in world coordinates)
# ---------------------------------------------------------------------------
def _draw_world(ctx, t, T, info, want_emb=True, want_boss=True):
    sets.office(ctx, t, "bg")
    _wet_spot(ctx, t, T)
    if t >= T.holo:
        fx.hologram_photo(ctx, *HOLO, t, T.holo, portrait_fn=_tired_portrait)
    if want_boss:
        _draw_boss(ctx, t, T, info)
    sets.office(ctx, t, "fg")
    _draw_tablet(ctx, t, T)
    _draw_recorder_desk(ctx, t, T)
    a = None
    if want_emb:
        a = _draw_emb(ctx, t, T, info)
        # recorder in his hand / LED through the coat
        if T.grab <= t < T.tuck:
            hx, hy, ang = a["hand_l"]
            props.recorder(ctx, hx + 4, hy - 6, REC_S * 0.95, t, rot=-0.25)
        if t >= T.led0:
            px, py = a["pocket"][:2]
            props.recorder(ctx, px - 30 * 1.4 + 4, py + 18, 1.4, t, led=_rec_led(t, T),
                           glow=0.6, only_led=True)
        _draw_drop(ctx, t, T, a)
        # gulp emote at his throat
        if T.gulp_fx <= t < T.gulp_fx + 0.6:
            hx, hy = a["head"]
            fx.emote(ctx, "gulp", hx + 112 * S, hy + 150 * S, 0.62, t, T.gulp_fx, dur=0.55)
    else:
        _draw_drop(ctx, t, T, None)
    return a


def _view_x(cam):
    cx, cy, z = cam
    return cx - 540 / z, cx + 540 / z


def _cam(name, t, t0, t1, T):
    k = seg(t, t0, t1)
    e = ease_in_out(k)
    if name == "wide_a":
        return (lerp(805, 790, e), lerp(1060, 1075, e), lerp(0.84, 0.91, e))
    if name == "boss_a":
        return (lerp(1112, 1120, e), lerp(985, 975, e), lerp(1.9, 2.06, e))
    if name == "emb_sweat":
        return (lerp(415, 410, e), lerp(1095, 1110, e), lerp(1.95, 2.02, e))
    if name == "carpet":
        return (DROP_X + 8, 1552, 4.0)
    if name == "wide_b":
        return (lerp(800, 790, e), lerp(1050, 1045, e), lerp(0.88, 0.92, e))
    if name == "emb_photo":
        return (lerp(470, 480, e), lerp(985, 1000, e), lerp(1.5, 1.62, e))
    if name == "slide":
        xr = _rec_x(t - 0.06, T)
        cx = clamp(xr + 40, 800, 985)
        return (cx, 1095, 1.75)
    if name == "emb_rec":
        return (lerp(478, 470, e), lerp(1062, 1066, e), lerp(2.0, 2.1, e))
    if name == "boss_b":
        return (lerp(1112, 1118, e), lerp(985, 978, e), lerp(2.0, 2.1, e))
    if name == "emb_guilt":
        return (lerp(392, 386, e), lerp(1052, 1058, e), lerp(2.2, 2.36, e))
    if name == "boss_c":
        return (lerp(1060, 1068, e), lerp(1000, 992, e), lerp(1.8, 1.9, e))
    if name == "emb_gulp":
        e2 = ease_in_out(seg(t, T.tuck - 0.3, T.dur))
        return (lerp(475, 430, e2), lerp(1105, 1175, e2), lerp(1.62, 2.05, e2))
    return (700, 1060, 0.95)


# ---------------------------------------------------------------------------
# insert: the pink slip (top-down on the desk, screen space)
# ---------------------------------------------------------------------------
def _slip_bg(c):
    c.rectangle(0, 0, core.W, core.H)
    core.fill(c, "#eef2f6")
    # cold reflections of the glass wall on the desk
    for x0, w0, a in ((80, 150, 0.55), (300, 60, 0.45), (760, 190, 0.5)):
        core.poly(c, [(x0, 0), (x0 + w0, 0), (x0 + w0 - 260, 1260), (x0 - 260, 1260)])
        core.fill(c, (1, 1, 1, a))
    # desk front edge + carpet below
    c.rectangle(0, 1260, core.W, 26)
    core.fill(c, "#d3dbe4")
    c.move_to(0, 1260)
    c.line_to(core.W, 1260)
    core.stroke(c, "ink", 5)
    c.rectangle(0, 1286, core.W, core.H - 1286)
    core.fill(c, "#b9c3cd")
    c.move_to(0, 1286)
    c.line_to(core.W, 1286)
    core.stroke(c, "ink", 4)


def _draw_slip_insert(ctx, t, T, info):
    core.cached(ctx, ("s09_slip_bg",), 0, 0, core.W, core.H, _slip_bg)
    k = ease_out(seg(t, T.slip_in, T.slip_in + 0.55))
    settle = ease_out_back(seg(t, T.slip_in + 0.4, T.slip_in + 0.7), 2.0)
    tap_up = bump(t, T.l8_desk - 0.2, T.l8_desk - 0.06, T.l8_desk - 0.06, T.l8_desk + 0.02)
    press = bump(t, T.l8_desk + 0.0, T.l8_desk + 0.04, T.l8_desk + 0.12, T.l8_desk + 0.3)
    ss = 2.35
    sx = lerp(1300, 480, k) - 8 * press
    sy = lerp(860, 790, k) + 4 * press
    rot = lerp(0.22, -0.07, k) + 0.015 * (1 - settle)
    # soft shadow + slip
    with core.saved(ctx, sx + 16, sy + 20, ss, rot):
        core.rrect(ctx, -95, -110, 190, 220, 6)
        core.fill(ctx, core.alpha("ink", 0.13))
    props.pink_slip(ctx, sx, sy, ss, rot)
    # her hand: index fingertip pinning the slip's right edge (clear of the title)
    cr, sr = math.cos(rot), math.sin(rot)
    lx, ly = 74 * ss, 34 * ss
    tip = (sx + cr * lx - sr * ly, sy + sr * lx + cr * ly - 36 * tap_up)
    z = 2.8
    C = human.CHARS["boss"]
    hs = C["hand"] * z
    inkw = 5.5 * z
    ang = math.pi + 0.32                    # pointing left (slightly up): her arm comes in from bottom-right
    ca, sa = math.cos(ang), math.sin(ang)
    ysign = -1.0
    hx, hy = 1.44, 0.34                     # 'point' fingertip in hand units
    offx = (ca * hx - sa * ysign * hy) * hs
    offy = (sa * hx + ca * ysign * hy) * hs
    wx, wy = tip[0] - offx, tip[1] - offy
    rr = C["arm_r"]
    ex, ey = wx - ca * C["arm"][1] * z, wy - sa * C["arm"][1] * z     # elbow (off frame)
    # cast shadow of the forearm on the desk
    human._capsule(ctx, wx + 24, wy + 30, rr[2] * z, ex + 24, ey + 30, rr[1] * z)
    core.fill(ctx, core.alpha("ink", 0.1))
    # sleeve
    human._capsule(ctx, wx, wy, rr[2] * z * 1.05, ex, ey, rr[1] * z * 1.1)
    core.fill_stroke(ctx, core.PAL["b_suit"], "ink", inkw)
    # shirt cuff
    dx, dy = -ca, -sa
    human._capsule(ctx, wx + dx * 6, wy + dy * 6, rr[2] * z * 1.0, wx + dx * 22, wy + dy * 22, rr[2] * z * 1.02)
    core.fill_stroke(ctx, "#e9ecf2", "ink", inkw * 0.8)
    hv = human._hand_vec("point")
    human._draw_hand(ctx, core.PAL["b_skin"], core.PAL["ink"], (wx, wy), ang, hv, ysign, hs, inkw)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _timing(info)
    name, t0, t1 = _shot(t, T)
    if name == "slip":
        _draw_slip_insert(ctx, t, T, info)
        return
    cam = _cam(name, t, t0, t1, T)
    vx0, vx1 = _view_x(cam)
    want_emb = vx0 < EMB_X + 260
    want_boss = vx1 > BOSS_X - 330
    with core.camera(ctx, *cam):
        _draw_world(ctx, t, T, info, want_emb, want_boss)


# ---------------------------------------------------------------------------
# sound
# ---------------------------------------------------------------------------
def SFX(info):
    T = _timing(info)
    ev = [
        (T.l1 - 0.3, "chair_creak", -12, -0.3),           # he shifts forward to explain
        (T.l1 - 0.25, "cloth_rustle", -10, -0.3),
        (T.plip, "pop", -4, -0.1),                          # plip
        (T.tap, "tick", -6, 0.3), (T.tap + 0.16, "tick", -8, 0.3),
        (T.holo - 0.02, "glitch", -10, -0.2),              # photo flickers on
        (T.l5 - 0.12, "chair_creak", -10, -0.3),            # protective lean
        (T.push, "puzzle_click", -10, 0.3),                 # her flick
        (T.release - 0.05, "whoosh", -16, 0.0),             # the glide
        (T.rec_stop - 0.05, "puzzle_click", -14, -0.3),     # it stops
        (T.slip_in, "paper", -8, 0.2),                      # pink slip slides in
        (T.l8_desk + 0.02, "tick", -6, 0.0),                # fingertip tap
        (T.swipe, "page_flip", -14, 0.3),                   # swipe on the tablet
        (T.gulp_fx, "gulp", -2, -0.2),
        (T.reach0 + 0.05, "cloth_rustle", -8, -0.2),
        (T.tuck - 0.05, "cloth_rustle", -6, -0.2),
        (T.led0, "tick", -16, -0.2),                        # the LED starts
    ]
    return [e for e in ev if 0 <= e[0] < info.dur]
