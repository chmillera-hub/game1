"""s11 . The turn: the wall and the door (music 'heart').

Sincere first half, warm second half. F5 two-shot at night (lair, dim wash,
rain), Malvo at screen-left with Hissy curled round him like a scarf, the AI
hologram floating screen-right.

Beats (every time from cues / word starts):
  slump   fade in from black; Malvo slumped, head down; Hissy worried.
  l01     AI drifts lower + closer, sympathetic; small smile on "one bad idea".
  beat    Malvo lifts his head; the monocle slips and dangles (tink).
  l02     glistening eyes; on "noticed me" his eyes go to the corkboard photo
          (the AI's eyes follow); eyes drop on "scaring them".
  photo   hard cut: the science-fair photo close-up (empty chairs), slow push.
  l03     cut back on "Clever": SLOW BLINK -> warm; the VILLAIN STATS sheet pops
          over his head, each row fills on its word.
  l04     header flips to HERO STATS on "hero"; AI happy, eyes to camera on
          "my guy", thumbs up. Hissy nods.
  l05     "...Hero stats?": hopeful, pushes the monocle back in, smile tugs.
  wall    sheet fades; the AI projects a cyan hologram: the door pops in, the
          wall builds so its last row thuds on "Brick"; firm nod "Every time".
  l07     light leaks round the door; on "wide open" it swings open and warm
          gold light spills across Malvo's face.
  pile    six gifts pop out of the door and arc into his arms / onto the desk;
          his eyes follow each one, getting wider.
  smile   he looks down at the pile; a slow REAL SMILE. Hissy happy. Hold.
"""
import math

import cairocffi as cairo

from engine import core
from engine.core import (clamp, lerp, seg, smoothstep, ease_out_back, ease_in_out, ease_out,
                         ease_in, hexc, noise1, hash01, rrect, ellipse, circle, poly,
                         smooth_path, fill_stroke, text, text_width, saved, radial_glow)
from engine import props as P
from engine import villain as V
from engine.villain import draw_villain
from engine import ai_char as AI
from engine.ai_char import draw_ai

# ---------------------------------------------------------------------------
# framing
# ---------------------------------------------------------------------------
MX, MY, MS = 400.0, 1250.0, 0.92          # Malvo (F5)
AX, AY0, AS0 = 762.0, 740.0, 0.48         # AI hologram at the start ...
AY1, AS1 = 770.0, 0.50                    # ... drifts lower + closer during l01
CAM_C = (432.0, 800.0)                    # slow push-in centre
CAM_K = 0.06                              # 1.00 -> 1.06 over the scene
AURA = 0.8
DESK_W = 1000
COMP = (1010.0, 1218.0, 0.7)              # EVILTRON pushed to the frame edge
PHOTO_SMALL = (770, 300, 130, 100, 0.05)  # science-fair photo on the corkboard
FACE = (MX, MY - 518 * MS)                # (400, 773)
HISSY = (MX - 306 * MS, MY - 474 * MS)    # Hissy's head (118, 814)

SHEET_C = (398.0, 380.0)
SHEET_W, SHEET_H = 420.0, 250.0
WALL = (130.0, 208.0, 420.0, 330.0)       # hologram wall (x, y, w, h)
WALL_ROWS = 5
WALL_DROP = 230
DOOR = (560.0, 238.0, 180.0, 300.0)       # door rect (hinge on its left edge)
HOLO = (90.0, 0.0, 720.0, 620.0)          # clip region for the hologram group
DOORWAY_C = (DOOR[0] + DOOR[2] / 2, DOOR[1] + DOOR[3] * 0.5)

PHOTO_C = (495.0, 745.0)                  # close-up photo centre
PHOTO_W, PHOTO_H = 640.0, 500.0
PHOTO_S = 1.25                            # drawn 800x625: reads on a phone

INK = "ink"
TEAR = "#8fd8ff"
DOOR_COL, DOOR_DK, DOOR_HI = "#8a5a3b", "#6a4129", "#a8744f"
DOORWAY = "#ffe9b0"
GOLD = P.C("gold")
STAR_GOLD, STAR_GOLD_DK = "#ffcf3a", "#d99a12"
BOOK, BOOK_DK = "#3f74d6", "#2a52a6"
DRAGON = "#7cd35c"
BALLOON, BALLOON_DK = "#ef3346", "#b81f30"
CAKE, CAKE_DK, CAKE_TOP = "#ff8fb8", "#e0679a", "#ffb7d2"
LAPEL = (100.0, -318.0)                   # FOR EFFORT star, villain-local (s=1)
LAPEL_S = 0.6

# ---------------------------------------------------------------------------
# s11-only rig additions (registered under s11_ names; built-ins untouched)
# ---------------------------------------------------------------------------
_DEF = V.VILLAIN_EXPR["defeated"]
_HOPE = V.VILLAIN_EXPR["hopeful"]
_HAPPY = V.VILLAIN_EXPR["happy"]
V.VILLAIN_EXPR.setdefault("s11_slump", dict(_DEF, ul1=0.7, ul2=0.68, hy=36, tilt=0.12,
                                            shy=24))
V.VILLAIN_EXPR.setdefault("s11_down", dict(_DEF, mono=1.0, shine=0.45, ul1=0.5, ul2=0.48,
                                           hy=16, shy=14, gloom=0.7))
V.VILLAIN_EXPR.setdefault("s11_teary", dict(_DEF, mono=1.0, shine=1.0, ps=1.22, ul1=0.42,
                                            ul2=0.4, by1=2, by2=2, ba1=-0.5, ba2=-0.5,
                                            mc=-0.7, hy=12, shy=12, gloom=0.45))
V.VILLAIN_EXPR.setdefault("s11_teary_up", dict(V.VILLAIN_EXPR["s11_teary"], ul1=0.12, ul2=0.1,
                                               by1=-10, by2=-10, ll1=0.02, ll2=0.02))
V.VILLAIN_EXPR.setdefault("s11_moved", dict(_DEF, mono=1.0, shine=1.0, ps=1.3, es=1.05,
                                            ul1=0.14, ul2=0.12, ll1=0.04, ll2=0.04,
                                            by1=-20, by2=-20, ba1=-0.42, ba2=-0.42,
                                            bc1=0.3, bc2=0.3, lt1=-0.1, lt2=-0.1,
                                            mc=-0.2, mw=0.7, mo=0.06, ey=0.0, hy=2,
                                            shy=4, gloom=0.0, hair=-0.2, blush=0.2,
                                            tilt=0.05))
V.VILLAIN_EXPR.setdefault("s11_hope_m", dict(_HOPE, mono=1.0, mc=0.2, shine=0.9, ps=1.28))
V.VILLAIN_EXPR.setdefault("s11_hope_m0", dict(_HOPE, mono=0.0, mc=0.2, shine=0.9, ps=1.28))
V.VILLAIN_EXPR.setdefault("s11_hope", dict(_HOPE, mc=0.62, mw=0.86, shine=0.9, ps=1.28,
                                           blush=0.4))
V.VILLAIN_EXPR.setdefault("s11_listen", dict(_HOPE, mc=0.35, mw=0.78, shine=0.7, ps=1.2,
                                             by1=-12, by2=-12, mo=0.02, blush=0.25,
                                             hy=-4))
V.VILLAIN_EXPR.setdefault("s11_wonder", dict(_HOPE, es=1.12, ps=1.36, shine=1.0,
                                             by1=-34, by2=-36, ba1=-0.18, ba2=-0.18,
                                             bc1=0.6, bc2=0.6, ul1=0.0, ul2=0.0, ll1=0.0,
                                             ll2=0.0, mc=0.3, mw=0.6, mo=0.32, mt=0.2,
                                             blush=0.45, hy=-12, hair=0.25))
V.VILLAIN_EXPR.setdefault("s11_wonder2", dict(V.VILLAIN_EXPR["s11_wonder"], es=1.2, ps=1.48,
                                              by1=-42, by2=-44, mo=0.42, mc=0.45))
V.VILLAIN_EXPR.setdefault("s11_smile", dict(_HAPPY, mc=1.05, mw=1.1, mo=0.26, mt=0.5,
                                            blush=0.9, shine=1.0, ps=1.25, by1=-20,
                                            by2=-20, ba1=-0.26, ba2=-0.26, bc1=0.45,
                                            bc2=0.45, ul1=0.12, ul2=0.1, ll1=0.3,
                                            ll2=0.28, tilt=-0.06, hy=-2))

from engine import snake as SN
SN.SNAKE_EXPR.setdefault("s11_soft", dict(ul=0.08, ll=0.04, ps=1.12, mc=0.45, mw=0.9,
                                          tilt=-0.04, blush=0.15, tng=0.0))
SN.SNAKE_EXPR.setdefault("s11_wonder", dict(ul=0.0, ll=0.0, es=1.12, ps=1.22, mc=0.55,
                                            mo=0.3, mw=0.8, hy=-8, blush=0.45, tng=0.0))

_REST_A = V._arm(-262, -140, -152, -52, 0.06, cu=0.3, th=0.2, sp=0.45)
# screen-right glove up at the monocle: index finger presses it back in
_MONO_B = V._mirror(V._arm(-236, -232, -112, -470, -1.72, cu=0.7, ix=0.0, th=0.3, sp=0.15,
                           hs=1.0))
V.ARM_POSES.setdefault("s11_mono", V._pose(_REST_A, _MONO_B, shy=-6, hdy=2, tilt=-0.03))
# hug: wrists at the book's side edges (fingers drawn over the cover)
_HUG_A = V._arm(-236, -150, -118, -214, -0.12, cu=0.6, th=0.2, sp=0.2, hs=1.0)
V.ARM_POSES.setdefault("s11_hug", V._pose(_HUG_A, shy=-12, hdy=8))
# open, palms-up "for me?" hands just above the desk while the gifts fly
_OPEN_A = V._arm(-230, -120, -160, -200, -2.3, cu=0.06, th=-0.3, sp=0.95, pm=1.0, tf=-1,
                 hs=1.05)
V.ARM_POSES.setdefault("s11_open", V._pose(_OPEN_A, shy=-12, hdy=-2))

AI_SYMP = AI.EXPR["sympathetic"]
AI_X = {
    "symp": AI_SYMP,
    "symp_smile": dict(AI_SYMP, mc=0.42, mw=0.68, lc=0.12, lL=0.16, lR=0.16),
    "symp_sad": {k: lerp(AI_SYMP[k], AI.EXPR["sad"][k], 0.55) for k in AI_SYMP},
    "warm": AI.EXPR["warm"],
    "happy": AI.EXPR["happy"],
    "determined": dict(AI.EXPR["determined"], mc=0.38, ms=0.06, bLa=-0.15, bRa=-0.15,
                       tL=0.22, tR=0.22, ttL=0.18, ttR=0.18),
    "warm_soft": dict(AI.EXPR["warm"], mc=0.85, blush=0.75, ps=1.2),
    "wonder": dict(AI.EXPR["happy"], mo=0.25, ps=1.15),
    "neutral": AI.EXPR["neutral"],
}


def _ai_ex(state):
    a, b, k = state
    return (AI_X.get(a, a), AI_X.get(b, b), k)


# ---------------------------------------------------------------------------
# timing (all from cues / word starts)
# ---------------------------------------------------------------------------
def _ws(info, lid, k):
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if 0 <= k < len(ws):
        return L.start + ws[k]
    n = max(1, len(L.caption.split()))
    return L.start + L.dur * k / n


_TCACHE = {}


def _T(info):
    key = (id(info), info.dur)
    T = _TCACHE.get(key)
    if T is not None:
        return T
    c = info.cue
    T = dict(slump=c("slump"), beat=c("beat"), photo=c("photo"), wall=c("wall"),
             pile=c("pile"), smile=c("smile"), end=info.dur)
    for i in range(1, 8):
        L = info.line(f"s11_l0{i}")
        T[f"l{i}"], T[f"l{i}e"] = L.start, L.end
    W = lambda lid, k: _ws(info, lid, k)                       # noqa: E731
    T.update(
        w_okay=W("s11_l01", 2), w_thats=W("s11_l01", 3), w_one=W("s11_l01", 9),
        w_noticed=W("s11_l02", 2), w_unless=W("s11_l02", 4), w_scaring=W("s11_l02", 7),
        w_clever=W("s11_l03", 2), w_stubborn=W("s11_l03", 3), w_never=W("s11_l03", 4),
        w_quits=W("s11_l03", 5),
        w_hero=W("s11_l04", 2), w_my=W("s11_l04", 4),
        w_stats2=W("s11_l05", 1),
        w_hurts=W("s11_l06", 2), w_people=W("s11_l06", 3), w_brick=W("s11_l06", 4),
        w_every=W("s11_l06", 6),
        w_else=W("s11_l07", 1), w_door=W("s11_l07", 3), w_wide=W("s11_l07", 4),
    )
    # back from the photo in the micro-pause after "I noticed." (photo holds
    # through "I noticed"), never earlier than l03.start + 0.45
    T["back"] = max(T["l3"] + 0.45, T["w_clever"] - 0.1)
    # stats rows fill on their words
    T["rows"] = [max(T["w_clever"], T["back"] + 0.2), T["w_stubborn"], T["w_never"]]
    T["row_dur"] = [0.32, 0.32, max(0.3, T["w_quits"] + 0.2 - T["w_never"])]
    T["flip"] = T["w_hero"]
    # hologram: door pops in, wall's LAST row lands on "Brick"
    T["holo"] = T["wall"]
    T["door_in"] = T["wall"] + 0.3
    land0 = P.brick_wall_land_times(0.0, WALL_ROWS, 1.0)
    T["wall0"] = T["w_brick"] - land0[-1]
    T["lands"] = P.brick_wall_land_times(T["wall0"], WALL_ROWS, 1.0)
    T["nod0"] = T["w_every"]
    T["leak"] = T["w_else"]
    T["open"] = T["w_wide"]
    # monocle back in during "...Hero stats?"
    T["mono_up"] = T["w_stats2"] + 0.12
    T["mono_in"] = T["mono_up"] + 0.38
    # the gift pile
    T["gift_t"] = [T["pile"] + 0.2 * i for i in range(6)]
    T["fly"] = 0.5
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


# ---------------------------------------------------------------------------
# keyframe helpers
# ---------------------------------------------------------------------------
def _state(t, keys, default=0.25):
    """[(time, name[, trans]), ...] -> (prev, cur, blend)."""
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _keyv(t, keys, default=0.25):
    """Tuple/float keyframes [(time, value[, trans]), ...]; each key blends
    from wherever the value is when it starts."""
    v = keys[0][1]
    for k in keys[1:]:
        if t < k[0]:
            break
        tr = k[2] if len(k) > 2 else default
        u = smoothstep(seg(t, k[0], k[0] + tr))
        if isinstance(v, (tuple, list)):
            v = tuple(lerp(a, b, u) for a, b in zip(v, k[1]))
        else:
            v = lerp(v, k[1], u)
    return v


def _slow_blink(t, t0, close=0.12, hold=0.08, open_=0.12):
    if t < t0 or t > t0 + close + hold + open_:
        return None
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _cam(t, info):
    """Slow push-in 1.00 -> 1.06 in two gentle legs (static in between, which
    keeps the bitrate down): during his confession (l02) and onto his REAL
    SMILE (smile - 0.3 -> end). The gift pile itself plays on a locked camera:
    the six flights carry the motion there, and a zoom on top of them doubled
    that stretch's bitrate (~1150 -> ~740 kbps at CRF 26)."""
    T = _T(info)
    k1 = ease_in_out(seg(t, T["l2"], T["l2e"] + 0.2))
    k2 = ease_in_out(seg(t, T["smile"] - 0.3, T["end"]))
    return 1.0 + CAM_K * (0.5 * k1 + 0.5 * k2)


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------
def _col(c, a=1.0):
    return P.C(c, a) if isinstance(c, str) else (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * a)


def _fs(ctx, fc, sc=INK, w=5.0, a=1.0):
    if fc is not None:
        ctx.set_source_rgba(*_col(fc, a))
        ctx.fill_preserve()
    if sc is not None:
        ctx.set_source_rgba(*_col(sc, a))
        ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke_preserve()
    ctx.new_path()


def _f(ctx, fc, a=1.0):
    ctx.set_source_rgba(*_col(fc, a))
    ctx.fill()


def _s(ctx, sc, w, a=1.0):
    ctx.set_source_rgba(*_col(sc, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


# ---------------------------------------------------------------------------
# villain body state (so props can ride on the rig's breathing / shy)
# ---------------------------------------------------------------------------
def _vstate(t, expr, arms, mouth, seed=1):
    p = V.resolve_expr(expr)
    _a, _b, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo_lip = float(mouth[0]) if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo_lip * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    return dict(p=p, shy=shy, breath=breath, head_dy=head_dy, head_rot=head_rot)


def _face_world(st, lx=0.0, ly=0.0):
    """World point of face-local (lx, ly) (ignores lean)."""
    hr = st["head_rot"]
    px, py = lx, ly + V.FACE_OFF
    c, s_ = math.cos(hr), math.sin(hr)
    rx, ry = px * c - py * s_, px * s_ + py * c
    return (MX + (V.NECK[0] + rx) * MS, MY + (V.NECK[1] + st["head_dy"] + ry) * MS)


# ---------------------------------------------------------------------------
# GIFTS (identical designs to s03 / s04 / s06 / s07 / s09)
# ---------------------------------------------------------------------------
def draw_headphones(c, x, y, s, rot=0.0):
    """Loose headphones (s03 gift). (x, y) = band centre."""
    with saved(c, x, y, s, rot):
        for col, w in (("ink", 17), ("bubble_ai", 9)):
            c.new_sub_path()
            c.arc(0, 22, 56, math.pi * 1.05, math.pi * 1.95)
            c.set_source_rgba(*hexc(col))
            c.set_line_width(w)
            c.stroke()
        for sx in (-1, 1):
            ellipse(c, sx * 50, 24, 19, 26)
            fill_stroke(c, "bubble_ai", "ink", 4.5)
            ellipse(c, sx * 53, 24, 9, 15)
            fill_stroke(c, "#0b6f6a", None, 0)


def draw_popper(c, x, y, s, rot=0.0):
    """Confetti popper (s03 gift, unfired). (x, y) = bottom tip."""
    with saved(c, x, y, s, rot):
        c.move_to(0, -2)
        c.curve_to(12, 10, -10, 18, 6, 30)
        fill_stroke(c, None, "ink", 4)
        circle(c, 8, 38, 8)
        fill_stroke(c, None, "ink", 4)
        cone = [(-31, -110), (31, -110), (5, -2), (-5, -2)]
        poly(c, cone)
        c.set_source_rgba(*hexc("#ff7ab8"))
        c.fill()
        c.save()
        poly(c, cone)
        c.clip()
        for k in range(-4, 6):
            poly(c, [(-40, -20 - k * 24), (40, -60 - k * 24), (40, -46 - k * 24),
                     (-40, -6 - k * 24)])
        c.set_source_rgba(*hexc("#ffd84a"))
        c.fill()
        c.rectangle(10, -120, 30, 130)
        c.set_source_rgba(*hexc("ink", 0.12))
        c.fill()
        c.restore()
        poly(c, cone)
        fill_stroke(c, None, "ink", 5)
        c.move_to(-4, -116)
        c.curve_to(-8, -136, 10, -140, 6, -152)
        fill_stroke(c, None, "ink", 9)
        c.move_to(-4, -116)
        c.curve_to(-8, -136, 10, -140, 6, -152)
        fill_stroke(c, None, "ai_rim", 5)
        pts = []
        for j in range(24):
            a = j / 24 * 2 * math.pi
            rr = 1.0 if j % 2 == 0 else 0.86
            pts.append((math.cos(a) * 36 * rr, -112 + math.sin(a) * 11 * rr))
        poly(c, pts)
        fill_stroke(c, GOLD, "ink", 4)
        ellipse(c, -10, -114, 10, 3)
        c.set_source_rgba(1, 1, 1, 0.6)
        c.fill()


def draw_scroll(ctx, x, y, s, rot=0.0):
    """Rolled-up THE CHEMIST story scroll (s04), red ribbon. (x, y) = centre."""
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -74, -22, 148, 44, 20)
        _fs(c, "parch", INK, 5)
        c.rectangle(-60, 6, 120, 10)
        _f(c, "parch_dk", 0.8)
        for sx in (-1, 1):
            ellipse(c, sx * 74, 0, 11, 22)
            _fs(c, "parch_dk", INK, 4)
            circle(c, sx * 74, 0, 4)
            _fs(c, "#b99a68", None)
            circle(c, sx * 92, 0, 11)
            _fs(c, "gold", INK, 4)
            circle(c, sx * 92 - 3, -4, 3.5)
            _fs(c, "white", None, a=0.6)
        c.rectangle(-9, -23, 18, 46)
        _fs(c, "cape_in", INK, 3.5)
        for sx in (-1, 1):
            ellipse(c, sx * 15, -27, 14, 9, -0.45 * sx)
            _fs(c, "danger", INK, 3.5)
        circle(c, 0, -25, 6)
        _fs(c, "cape_in", INK, 3)


def draw_dragon_book(ctx, x, y, s, rot=0.0, sq=0.0):
    """THE GENTLE DRAGON storybook (s06): 150x190 at s=1, centred."""
    with saved(ctx, x, y, (s * (1 + sq * 0.5), s * (1 - sq)), rot) as c:
        rrect(c, -70, -91, 150, 186, 10)
        _fs(c, "#f3ead2", INK, 4)
        rrect(c, -75, -95, 150, 190, 12)
        _fs(c, BOOK, INK, 5)
        rrect(c, -75, -95, 24, 190, 10)
        _fs(c, BOOK_DK, INK, 4)
        for yy in (-70, 70):
            c.move_to(-73, yy)
            c.line_to(-53, yy)
        _s(c, "gold", 4)
        rrect(c, -44, -84, 110, 168, 9)
        _s(c, "gold", 4)
        text(c, "THE GENTLE", 11, -58, 19, GOLD, "title")
        text(c, "DRAGON", 11, -31, 29, GOLD, "title")
        fx, fy = 11, 30
        for sx in (-1, 1):
            poly(c, [(fx + sx * 30, fy - 4), (fx + sx * 56, fy - 26), (fx + sx * 50, fy - 6),
                     (fx + sx * 58, fy + 4), (fx + sx * 34, fy + 14)])
            _fs(c, "#a6e88a", INK, 3.5)
        for sx in (-1, 1):
            poly(c, [(fx + sx * 12, fy - 32), (fx + sx * 22, fy - 50), (fx + sx * 26, fy - 28)])
            _fs(c, "#f6e7b8", INK, 3)
        circle(c, fx, fy, 38)
        _fs(c, DRAGON, INK, 4)
        ellipse(c, fx, fy + 16, 22, 14)
        _fs(c, "#c8f0a8", None)
        for sx in (-1, 1):
            c.move_to(fx + sx * 14 - 8, fy - 6)
            c.curve_to(fx + sx * 14 - 4, fy - 14, fx + sx * 14 + 4, fy - 14, fx + sx * 14 + 8,
                       fy - 6)
            _s(c, INK, 3.5)
            ellipse(c, fx + sx * 24, fy + 6, 6, 4)
            _f(c, "#ff8fb0", 0.85)
            circle(c, fx + sx * 5, fy + 12, 1.8)
            _f(c, INK)
        c.move_to(fx - 9, fy + 20)
        c.curve_to(fx - 4, fy + 26, fx + 4, fy + 26, fx + 9, fy + 20)
        _s(c, INK, 3.2)
        for (sx_, sy_) in ((-30, 74), (50, 70), (52, -76)):
            P._star4(c, fx + sx_ - 11, sy_, 7)
            _f(c, "gold")


def draw_balloon(c, x, y, s=1.0, rot=0.0, sq=(1.0, 1.0)):
    """Red party balloon (s07). (x, y) = balloon centre; knot at (0, 58)*s."""
    with saved(c, x, y, (s * sq[0], s * sq[1]), rot):
        poly(c, [(0, 52), (-11, 68), (11, 68)])
        fill_stroke(c, BALLOON_DK, "ink", 4)
        ellipse(c, 0, 0, 45, 55)
        fill_stroke(c, BALLOON, "ink", 5)
        c.save()
        ellipse(c, 0, 0, 45, 55)
        c.clip()
        ellipse(c, 16, 18, 40, 48)
        c.set_source_rgba(*hexc(BALLOON_DK, 0.55))
        c.fill()
        c.restore()
        ellipse(c, -16, -22, 11, 17, 0.45)
        c.set_source_rgba(1, 1, 1, 0.6)
        c.fill()
        circle(c, -8, -38, 4)
        c.fill()


def draw_string(c, x0, y0, x1, y1, t, curls=3.0, amp=10.0, phase=0.0):
    """Curly balloon string (s07) from the knot (x0, y0) to (x1, y1)."""
    n = 30
    pts = []
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    for i in range(n + 1):
        u = i / n
        w = math.sin(u * curls * 2 * math.pi + phase + t * 2.2) * amp * \
            math.sin(math.pi * min(1, u * 1.4))
        pts.append((x0 + dx * u + nx * w, y0 + dy * u + ny * w))
    for col, w in (("ink", 7), ("#f6f2ff", 3)):
        smooth_path(c, pts)
        c.set_source_rgba(*hexc(col))
        c.set_line_width(w)
        c.stroke()


def draw_cake(c, x, y, s, t, fizz=True):
    """Two-tier pink birthday cake with one sparkler candle (s07).
    (x, y) = bottom-centre (plate)."""
    with saved(c, x, y, s) as cc:
        ellipse(cc, 0, -4, 98, 13)
        fill_stroke(cc, "#f4f1fb", "ink", 4)
        rrect(cc, -80, -64, 160, 60, 12)
        fill_stroke(cc, CAKE, "ink", 5)
        cc.save()
        rrect(cc, -80, -64, 160, 60, 12)
        cc.clip()
        cc.rectangle(-90, -20, 180, 30)
        cc.set_source_rgba(*hexc(CAKE_DK, 0.7))
        cc.fill()
        cc.restore()
        cc.move_to(-80, -52)
        for j in range(8):
            xa = -80 + j * 20
            dl = 14 + 10 * ((j * 7) % 3)
            cc.line_to(xa + 4, -52)
            cc.curve_to(xa + 4, -52 + dl, xa + 16, -52 + dl, xa + 16, -52)
        cc.line_to(80, -52)
        cc.line_to(80, -64)
        cc.line_to(-80, -64)
        cc.close_path()
        fill_stroke(cc, "#ffffff", "ink", 3.5)
        rrect(cc, -54, -108, 108, 46, 10)
        fill_stroke(cc, CAKE_TOP, "ink", 5)
        cc.move_to(-54, -98)
        for j in range(5):
            xa = -54 + j * 21.6
            dl = 10 + 8 * ((j * 5) % 3)
            cc.line_to(xa + 4, -98)
            cc.curve_to(xa + 4, -98 + dl, xa + 17, -98 + dl, xa + 17, -98)
        cc.line_to(54, -98)
        cc.line_to(54, -108)
        cc.line_to(-54, -108)
        cc.close_path()
        fill_stroke(cc, "#ffffff", "ink", 3.5)
        for j, (sx, sy) in enumerate(((-30, -36), (10, -30), (44, -40), (-12, -84), (24, -88))):
            circle(cc, sx, sy, 4)
            cc.set_source_rgba(*hexc(("#5ee7ff", "#ffd166", "#3ddc84", "#7b3fbf", "#5ee7ff")[j]))
            cc.fill()
        cc.move_to(0, -108)
        cc.line_to(0, -164)
        cc.set_source_rgba(*hexc("ink"))
        cc.set_line_width(10)
        cc.stroke()
        cc.move_to(0, -110)
        cc.line_to(0, -162)
        cc.set_source_rgba(*hexc("#b9c0d0"))
        cc.set_line_width(4.5)
        cc.stroke()
        if fizz:
            f = 1 + 0.25 * math.sin(t * 37) + 0.15 * noise1(t * 18, 4)
            P._star4(cc, 0, -170, 20 * f, t * 5)
            P._fs(cc, "ai_accent", "ink", 3)
            P._star4(cc, 0, -170, 9 * f, -t * 5)
            P._f(cc, "#fff3c4")
            P.sparkles(cc, 0, -172, 40, t, n=4, seed=17, color="ai_accent", size=0.45)


def _star5_path(c, x, y, r, rot=0.0, inner=0.47):
    c.new_sub_path()
    for i in range(10):
        a = rot - math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if i == 0:
            c.move_to(px, py)
        else:
            c.line_to(px, py)
    c.close_path()


def _gift_star(c, x, y, s, rot=0.0):
    """The FOR EFFORT gift (s09): gold star r 40 + label_tag under it."""
    with saved(c, x, y, s) as cc:
        with saved(cc, 0, 58, 1.0, -0.04) as c2:
            P.label_tag(c2, 0, 0, "FOR EFFORT", color="ai_accent", size=24)
        _star5_path(cc, 0, 0, 40, rot)
        fill_stroke(cc, STAR_GOLD, "ink", 5.0)
        cc.save()
        _star5_path(cc, 0, 0, 40, rot)
        cc.clip()
        _star5_path(cc, 6.4, 8, 40, rot)
        cc.rectangle(-80, -80, 160, 160)
        cc.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        core.set_color(cc, STAR_GOLD_DK)
        cc.fill()
        cc.set_fill_rule(cairo.FILL_RULE_WINDING)
        cc.restore()
        _star5_path(cc, 0, 0, 40, rot)
        core.stroke(cc, "ink", 5.0)
        ellipse(cc, -8, -12, 6.8, 4, -0.6)
        cc.set_source_rgba(1, 1, 1, 0.85)
        cc.fill()


def _hug_hands(ctx, bx, by, bs, rot, k=1.0):
    """White gloves wrapping over the book's side edges (the hug, as s06)."""
    if k <= 0.01:
        return
    hs = MS * 1.45 * k
    with saved(ctx, bx, by, 1.0, rot) as c:
        for sx in (-1, 1):
            ex = sx * 75 * bs
            ellipse(c, ex + sx * 8 * hs, 18 * bs, 22 * hs, 27 * hs, sx * 0.2)
            _fs(c, "glove", INK, 5)
            for i, fy in enumerate((-4, 18, 40)):
                y0 = (fy - 6) * bs
                L = (30 - 3 * abs(i - 1)) * hs
                for col, w in ((INK, 23 * hs), ("glove", 23 * hs - 9)):
                    c.move_to(ex + sx * 8 * hs, y0)
                    c.line_to(ex - sx * L, y0 + 4 * hs)
                    _s(c, col, w)
            for fy in (7, 29):
                c.move_to(ex - sx * 6 * hs, fy * bs - 6 * bs)
                c.line_to(ex - sx * 20 * hs, fy * bs - 4 * bs)
            _s(c, "#c9c8da", 3)


# ---------------------------------------------------------------------------
# science-fair photo: small corkboard version (as s02) + the s11 close-up
# ---------------------------------------------------------------------------
def science_photo_small(ctx, x, y, w, h, rot):
    with saved(ctx, x, y, 1.0, rot) as c:
        rrect(c, -w / 2 + 5, -h / 2 + 6, w, h, 3)
        core.fill(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 3)
        _fs(c, "#f3efe6", INK, 3)
        px0, py0, pw, ph = -w / 2 + 7, -h / 2 + 7, w - 14, h - 24
        c.save()
        c.rectangle(px0, py0, pw, ph)
        c.clip()
        core.bg(c, "#b9b0c2")
        c.rectangle(px0, py0 + ph * 0.52, pw, ph)
        core.fill(c, "#a59c90")
        kx, ky = px0 + pw * 0.33, py0 + ph * 0.36
        poly(c, [(kx - 11, ky + 6), (kx + 11, ky + 6), (kx + 14, ky + 24), (kx - 14, ky + 24)])
        core.fill(c, "#6f5a7c")
        circle(c, kx, ky, 8)
        _fs(c, "#e6cdb6", "#4a3a44", 1.5)
        circle(c, kx + 3, ky - 1, 2.6)
        core.stroke(c, "#c9a84f", 1.4)
        rx_, ry_ = px0 + pw * 0.62, py0 + ph * 0.36
        c.rectangle(rx_ - 7, ry_ - 2, 14, 16)
        _fs(c, "#9aa0a8", "#4a4650", 1.5)
        circle(c, rx_, ry_ - 7, 4)
        _fs(c, "#f2e6a0", "#4a4650", 1.2)
        c.rectangle(px0 + pw * 0.14, py0 + ph * 0.52, pw * 0.66, 5)
        _fs(c, "#8a7f74", "#4a4650", 1.2)
        circle(c, px0 + pw * 0.47, py0 + ph * 0.52 + 9, 3.2)
        core.fill(c, "#7f9bc4")
        poly(c, [(px0 + pw * 0.47 - 2, py0 + ph * 0.52 + 11),
                 (px0 + pw * 0.47 - 4, py0 + ph * 0.52 + 19),
                 (px0 + pw * 0.47 + 3, py0 + ph * 0.52 + 18)])
        core.fill(c, "#7f9bc4")
        for row in range(3):
            yy = py0 + ph * (0.7 + row * 0.12)
            for k in range(6):
                xx = px0 + 9 + k * (pw - 18) / 5 + (row % 2) * 4
                c.rectangle(xx - 4, yy - 7, 8, 6)
                c.rectangle(xx - 4, yy, 8, 2)
                core.fill(c, "#7d7a84")
        c.restore()
        c.move_to(-w / 2 + 14, h / 2 - 9)
        c.line_to(-w / 2 + 60, h / 2 - 10)
        core.stroke(c, "#8a8494", 2)
        circle(c, 0, -h / 2 + 6, 7)
        _fs(c, "danger", INK, 2.5)


# faded photo palette
F_WALL, F_WALL2, F_FLOOR, F_FLOOR2 = "#bdb3c4", "#a99fb6", "#a99f92", "#968d81"
F_INK = "#4a4252"
F_SKIN, F_SKIN_SH = "#e8cdb6", "#d0b098"
F_CAPE, F_CAPE_IN, F_SUIT = "#43384c", "#a8687a", "#7a6890"
F_TIN, F_TIN_DK = "#9fa5ae", "#7f8590"
F_CLOTH, F_CLOTH_DK = "#d9d2c4", "#bcb3a4"
F_CHAIR, F_CHAIR_DK = "#86838e", "#6c6976"
F_RIB = "#7f9bc4"


def _folding_chair_back(c, x, y, s):
    """Grey folding chair seen from behind (empty). (x, y) = floor centre."""
    with saved(c, x, y, s):
        for sx in (-1, 1):                            # back legs
            c.move_to(sx * 26, 0)
            c.line_to(sx * 22, -96)
        _s(c, F_INK, 9)
        for sx in (-1, 1):
            c.move_to(sx * 26, 0)
            c.line_to(sx * 22, -96)
        _s(c, F_CHAIR_DK, 5)
        poly(c, [(-34, -56), (34, -56), (30, -46), (-30, -46)])       # seat edge
        _fs(c, F_CHAIR_DK, F_INK, 3)
        rrect(c, -30, -118, 60, 40, 8)                                 # backrest
        _fs(c, F_CHAIR, F_INK, 3.5)
        rrect(c, -18, -104, 36, 9, 4)                                  # hand slot
        _fs(c, F_CHAIR_DK, None)


def _kid_malvo(c, x, y):
    """Kid Malvo behind the table (photo-local). (x, y) = chin."""
    # tiny cape + suit
    poly(c, [(x - 58, y + 120), (x - 50, y + 30), (x - 30, y + 14), (x + 30, y + 14),
             (x + 50, y + 30), (x + 58, y + 120)])
    _fs(c, F_CAPE, F_INK, 3)
    poly(c, [(x - 32, y + 120), (x - 30, y + 26), (x + 30, y + 26), (x + 32, y + 120)])
    _fs(c, F_SUIT, F_INK, 3)
    for sx in (-1, 1):                                                # collar points
        poly(c, [(x + sx * 22, y + 18), (x + sx * 56, y - 30), (x + sx * 42, y + 26)])
        _fs(c, F_CAPE_IN, F_INK, 3)
    # proud arm: glove up, presenting the robot (screen-right)
    c.move_to(x + 28, y + 50)
    c.curve_to(x + 62, y + 46, x + 76, y + 20, x + 86, y - 2)
    _s(c, F_INK, 17)
    c.move_to(x + 28, y + 50)
    c.curve_to(x + 62, y + 46, x + 76, y + 20, x + 86, y - 2)
    _s(c, F_SUIT, 10)
    circle(c, x + 90, y - 10, 13)
    _fs(c, "#efedf2", F_INK, 3)
    for k in range(3):
        c.move_to(x + 92 + k * 4, y - 20)
        c.line_to(x + 98 + k * 6, y - 34 + k * 3)
    _s(c, F_INK, 7)
    for k in range(3):
        c.move_to(x + 92 + k * 4, y - 20)
        c.line_to(x + 98 + k * 6, y - 34 + k * 3)
    _s(c, "#efedf2", 3.5)
    # head
    hx, hy = x, y - 52
    for sx in (-1, 1):                                                # ears
        ellipse(c, hx + sx * 44, hy + 6, 9, 13)
        _fs(c, F_SKIN, F_INK, 3)
        for k in range(3):                                            # tiny tufts
            c.move_to(hx + sx * 40, hy - 14 + k * 6)
            c.line_to(hx + sx * (54 + k * 3), hy - 22 + k * 7)
        _s(c, "#d0d0d8", 3.5)
    ellipse(c, hx, hy, 44, 50)
    _fs(c, F_SKIN, F_INK, 3.5)
    ellipse(c, hx - 16, hy - 30, 12, 6, -0.5)
    _f(c, "white", 0.45)
    for sx in (-1, 1):                                                # big hopeful eyes
        ellipse(c, hx + sx * 16, hy + 2, 10, 12)
        _fs(c, "white", F_INK, 2.5)
        circle(c, hx + sx * 16 + 1, hy + 3, 5.5)
        _f(c, F_INK)
        circle(c, hx + sx * 16 - 1, hy, 1.8)
        _f(c, "white")
        c.move_to(hx + sx * 9, hy - 16)
        c.line_to(hx + sx * 24, hy - 19)
        _s(c, F_INK, 3.5)
    circle(c, hx + 16, hy + 2, 15)                                    # monocle
    _s(c, "#c9a84f", 3.5)
    c.move_to(hx + 28, hy + 12)
    c.curve_to(hx + 34, hy + 30, hx + 30, hy + 50, hx + 24, y + 26)
    _s(c, "#c9a84f", 1.6)
    c.move_to(hx - 12, hy + 26)                                       # proud little grin
    c.curve_to(hx - 4, hy + 34, hx + 6, hy + 34, hx + 13, hy + 25)
    _s(c, F_INK, 3)
    ellipse(c, hx - 26, hy + 18, 7, 4)
    _f(c, "#e8a0a8", 0.6)
    ellipse(c, hx + 28, hy + 18, 7, 4)
    _f(c, "#e8a0a8", 0.6)


def _home_robot(c, x, y):
    """Homemade tin robot with a light bulb on its head. (x, y) = feet."""
    for sx in (-1, 1):                                                # legs
        c.rectangle(x + sx * 16 - 6, y - 26, 12, 26)
        _fs(c, F_TIN_DK, F_INK, 2.5)
    rrect(c, x - 34, y - 86, 68, 62, 6)                               # body (a can)
    _fs(c, F_TIN, F_INK, 3)
    for k in range(3):
        circle(c, x - 18 + k * 18, y - 52, 4)
        _f(c, ("#c98f8f", "#9fbf8f", "#d8c88a")[k])
    for sx in (-1, 1):                                                # bendy arms
        c.move_to(x + sx * 34, y - 72)
        c.curve_to(x + sx * 52, y - 70, x + sx * 52, y - 52, x + sx * 60, y - 44)
        _s(c, F_INK, 9)
        c.move_to(x + sx * 34, y - 72)
        c.curve_to(x + sx * 52, y - 70, x + sx * 52, y - 52, x + sx * 60, y - 44)
        _s(c, F_TIN_DK, 5)
    rrect(c, x - 28, y - 134, 56, 46, 6)                              # head (a box)
    _fs(c, F_TIN, F_INK, 3)
    for sx in (-1, 1):
        circle(c, x + sx * 12, y - 114, 7)
        _fs(c, "#f4f2e6", F_INK, 2.5)
        circle(c, x + sx * 12, y - 114, 2.5)
        _f(c, F_INK)
    for k in range(4):
        c.move_to(x - 12 + k * 8, y - 100)
        c.line_to(x - 12 + k * 8, y - 94)
    _s(c, F_INK, 2)
    c.rectangle(x - 7, y - 146, 14, 12)                               # bulb screw base
    _fs(c, "#b8b0a0", F_INK, 2.5)
    circle(c, x, y - 160, 16)                                         # the light bulb
    _fs(c, "#f2e6a8", F_INK, 3)
    for k in range(5):                                                # faded glow rays
        a = -math.pi / 2 + (k - 2) * 0.55
        c.move_to(x + math.cos(a) * 24, y - 160 + math.sin(a) * 24)
        c.line_to(x + math.cos(a) * 34, y - 160 + math.sin(a) * 34)
    _s(c, "#e0cf8a", 3)


def _photo_big(c):
    """The 640x500 science-fair photo (bible size), drawn centred at the origin."""
    w, h = PHOTO_W, PHOTO_H
    bx, by = -w / 2, -h / 2
    rrect(c, bx + 10, by + 14, w, h, 5)                               # flat shadow
    _f(c, (0.05, 0.02, 0.06, 0.4))
    rrect(c, bx, by, w, h, 5)
    _fs(c, "#f1ece2", INK, 4)
    px0, py0, pw, ph = bx + 26, by + 26, w - 52, h - 96
    c.save()
    c.rectangle(px0, py0, pw, ph)
    c.clip()
    c.translate(px0, py0)
    # gym wall + floor
    core.bg(c, F_WALL)
    c.rectangle(0, 214, pw, 16)
    _f(c, F_WALL2)
    c.rectangle(0, 230, pw, ph)
    _f(c, F_FLOOR)
    for k in range(4):
        c.move_to(0, 262 + k * 40)
        c.line_to(pw, 262 + k * 40)
    _s(c, F_FLOOR2, 2)
    # pennant string along the top
    c.move_to(-10, 4)
    c.curve_to(pw * 0.3, 26, pw * 0.7, 26, pw + 10, 4)
    _s(c, F_INK, 2)
    for k in range(11):
        u = (k + 0.5) / 11
        xx = u * pw
        yy = 4 + 22 * 4 * u * (1 - u) * 0.75
        poly(c, [(xx - 12, yy), (xx + 12, yy), (xx, yy + 22)])
        _fs(c, ("#c99a9a", "#9ab3c9", "#c9c09a", "#a7c2a0")[k % 4], F_INK, 2)
    # SCIENCE FAIR banner (above the kid, clear of the robot)
    with saved(c, pw * 0.27, 62, 1.0, -0.02) as cb:
        rrect(cb, -128, -22, 256, 46, 6)
        _fs(cb, "#dccaa8", F_INK, 3)
        text(cb, "SCIENCE FAIR", 0, 13, 34, "#8a5f6a", "title")
    # kid Malvo behind the folding table, proudly presenting his robot
    _kid_malvo(c, pw * 0.3, 196)
    tx0, tx1, ty = 34, pw - 110, 232
    _home_robot(c, pw * 0.65, ty)
    rrect(c, tx0, ty - 4, tx1 - tx0, 14, 4)                           # table top
    _fs(c, F_CLOTH, F_INK, 3)
    poly(c, [(tx0 + 4, ty + 10), (tx1 - 4, ty + 10), (tx1 - 10, ty + 86), (tx0 + 10, ty + 86)])
    _fs(c, F_CLOTH, F_INK, 3)
    for k in range(1, 8):
        xx = lerp(tx0 + 4, tx1 - 4, k / 8)
        c.move_to(xx, ty + 14)
        c.line_to(xx + (k - 4) * 1.2, ty + 82)
    _s(c, F_CLOTH_DK, 2.5)
    # three rows of EMPTY folding chairs, centre aisle (seen from behind)
    aisle, half = pw * 0.5, 84
    for yy, sc in ((318, 0.6), (362, 0.78), (420, 1.0)):
        sp = 78 * sc + 6
        for side in (-1, 1):
            for k in range(4):
                xx = aisle + side * (half + 30 * sc + k * sp)
                if -40 < xx < pw + 40:
                    _folding_chair_back(c, xx, yy, sc)
    # limp PARTICIPANT ribbon pinned to the skirt, hanging over the aisle
    rx, ry = aisle, ty + 30
    for sx, ln in ((-1, 52), (1, 44)):
        c.move_to(rx + sx * 5, ry + 8)
        c.curve_to(rx + sx * 10, ry + 26, rx + sx * 2, ry + 38, rx + sx * 7, ry + ln)
        _s(c, F_INK, 15)
        c.move_to(rx + sx * 5, ry + 8)
        c.curve_to(rx + sx * 10, ry + 26, rx + sx * 2, ry + 38, rx + sx * 7, ry + ln)
        _s(c, F_RIB, 10)
    pts = []
    for j in range(20):
        a = j / 20 * 2 * math.pi
        rr = 25 if j % 2 == 0 else 20
        pts.append((rx + math.cos(a) * rr, ry + math.sin(a) * rr * 0.92))
    poly(c, pts)
    _fs(c, F_RIB, F_INK, 2.5)
    circle(c, rx, ry, 11)
    _fs(c, "#d8c88a", F_INK, 2)
    with saved(c, rx + 4, ry + 72, 1.0, 0.12) as cc:                # tag, drooping
        rrect(cc, -78, -17, 156, 34, 5)
        _fs(cc, "#ece6da", F_INK, 2.5)
        text(cc, "PARTICIPANT", 0, 8, 22, "#5d5568", "ui")
    # faded / warm photographic wash + soft corner darkening
    c.set_source_rgba(1.0, 0.9, 0.72, 0.14)
    c.paint()
    g = cairo.RadialGradient(pw / 2, ph / 2, ph * 0.4, pw / 2, ph / 2, pw * 0.75)
    g.add_color_stop_rgba(0, 0.3, 0.2, 0.2, 0.0)
    g.add_color_stop_rgba(1, 0.3, 0.2, 0.2, 0.2)
    c.set_source(g)
    c.paint()
    c.restore()
    c.rectangle(px0, py0, pw, ph)
    _s(c, "#cfc6b8", 2)
    with saved(c, bx + 52, by + h - 26, 1.0, -0.02) as cc:          # handwriting
        text(cc, "science fair  -  age 9", 0, 0, 30, "#7a7088", "round", "left")


def _cork_layer(c):
    """Corkboard close-up (static, cached): cork, string, paper corners, photo."""
    core.bg(c, "#c79a5b")
    for i in range(420):                                              # cork speckles
        x = hash01(i, 301) * 1080
        y = hash01(i, 302) * 1920
        r = 1.5 + 3.0 * hash01(i, 303)
        circle(c, x, y, r)
        _f(c, "#a87a40" if hash01(i, 304) < 0.6 else "#ddb478", 0.7)
    # neighbouring pinned papers peeking in at the edges
    with saved(c, 1000, 150, 1.0, 0.08) as cc:
        rrect(cc, -200, -160, 400, 300, 4)
        _fs(cc, "#f2ead6", INK, 4)
        for k in range(5):
            cc.move_to(-170, -120 + k * 36)
            cc.line_to(60 - (k % 2) * 60, -120 + k * 36)
        _s(cc, "#b8ae9c", 6)
    with saved(c, 40, 1290, 1.0, -0.1) as cc:
        rrect(cc, -220, -150, 380, 300, 4)
        _fs(cc, "#5b8fd8", INK, 4)
        for k in range(6):
            cc.move_to(-200, -120 + k * 44)
            cc.line_to(140, -120 + k * 44)
        _s(cc, "#8fb6ec", 3)
    # red string from the board
    c.move_to(-20, 350)
    c.curve_to(240, 390, 380, 382, 495, 372)
    c.curve_to(640, 362, 860, 300, 1100, 250)
    _s(c, "#c8283c", 5)
    with saved(c, PHOTO_C[0], PHOTO_C[1], PHOTO_S, -0.025) as cc:
        _photo_big(cc)
        circle(cc, 0, -PHOTO_H / 2 + 14, 13)                         # push pin
        _fs(cc, "danger", INK, 4)
        circle(cc, -4, -PHOTO_H / 2 + 9, 3.5)
        _f(cc, "white", 0.7)
    # night: dim + candle-warm vignette (static)
    c.set_source_rgba(0.05, 0.02, 0.12, 0.16)
    c.paint()
    g = cairo.RadialGradient(495, 745, 460, 495, 760, 1150)
    g.add_color_stop_rgba(0, 0.04, 0.02, 0.08, 0.0)
    g.add_color_stop_rgba(1, 0.04, 0.02, 0.08, 0.55)
    c.set_source(g)
    c.paint()


def _shot_photo(ctx, t, info, T):
    u = seg(t, T["photo"], T["back"])
    k = 1.0 + 0.05 * ease_in_out(u) + 0.004 * u
    cx, cy = PHOTO_C[0], PHOTO_C[1] + 30
    with saved(ctx, cx, cy, k) as c:
        c.translate(-cx, -cy)
        P._cached_layer(c, "s11_cork", _cork_layer, rect=(-60, -80, 1200, 2080), opaque=True)


# ---------------------------------------------------------------------------
# the character sheet (6.16)
# ---------------------------------------------------------------------------
ROWS = ("CLEVER", "STUBBORN", "NEVER QUITS")


def _sheet(ctx, t, T):
    t_in = T["back"] + 0.04
    if t < t_in:
        return
    k_in = ease_out_back(seg(t, t_in, t_in + 0.3), 2.0)
    k_out = 1.0
    if t >= T["wall"]:
        k_out = 1 - ease_in(seg(t, T["wall"], T["wall"] + 0.3))
    if k_out <= 0.01:
        return
    a = clamp((t - t_in) / 0.08) * k_out
    s = (0.3 + 0.7 * k_in) * (0.9 + 0.1 * k_out)
    cx, cy = SHEET_C[0], SHEET_C[1]
    with saved(ctx, cx, cy + SHEET_H / 2, s, 0.0, alpha_=a) as c:
        c.translate(0, -SHEET_H / 2)
        w, h = SHEET_W, SHEET_H
        flip_u = seg(t, T["flip"], T["flip"] + 0.25)
        hero = flip_u >= 0.5
        # pointer toward his head + panel
        poly(c, [(-22, h / 2 - 4), (22, h / 2 - 4), (0, h / 2 + 26)])
        _fs(c, "ui_panel", "ai_rim", 6)
        rrect(c, -w / 2 + 6, -h / 2 + 8, w, h, 22)
        _f(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 22)
        _fs(c, "ui_panel", "safe" if hero else "ai_rim", 6)
        poly(c, [(-20, h / 2 - 7), (20, h / 2 - 7), (0, h / 2 + 20)])
        _f(c, "ui_panel")
        # header (scale-y flip)
        sy = abs(math.cos(flip_u * math.pi)) if 0 < flip_u < 1 else 1.0
        with saved(c, 0, -h / 2 + 46, (1.0, max(0.02, sy))) as ch:
            hdr = "HERO STATS" if hero else "VILLAIN STATS"
            col = "safe" if hero else "warn"
            text(ch, hdr, 0, 15, 44, col, "comic", outline="ink", outline_w=8)
        c.move_to(-w / 2 + 24, -h / 2 + 76)
        c.line_to(w / 2 - 24, -h / 2 + 76)
        _s(c, "ai_rim", 3, 0.5)
        # rows
        for i, lab in enumerate(ROWS):
            ry = -h / 2 + 112 + i * 50
            text(c, lab, -w / 2 + 26, ry + 11, 30, "white", "ui", "left")
            t0, dur = T["rows"][i], T["row_dur"][i]
            for j in range(5):
                bx = w / 2 - 26 - (5 - j) * 32 + 4
                tj = t0 + dur * j / 5
                fk = ease_out_back(seg(t, tj, tj + 0.16), 2.4)
                rrect(c, bx, ry - 15, 24, 30, 7)
                _fs(c, "#2c2c40", "#55557a", 3)
                if fk > 0.01:
                    with saved(c, bx + 12, ry, fk) as cb:
                        rrect(cb, -12, -15, 24, 30, 7)
                        _fs(cb, "ai_accent", "ink", 3)
                        rrect(cb, -7, -11, 6, 12, 3)
                        _f(cb, "white", 0.55)
        # a shine sweep over the bars right after the flip
        if T["flip"] + 0.15 <= t <= T["flip"] + 0.75:
            u = seg(t, T["flip"] + 0.15, T["flip"] + 0.75)
            c.save()
            rrect(c, -w / 2, -h / 2, w, h, 22)
            c.clip()
            xx = lerp(-w / 2 - 60, w / 2 + 60, ease_in_out(u))
            poly(c, [(xx - 20, -h / 2), (xx + 20, -h / 2), (xx - 30, h / 2), (xx - 70, h / 2)])
            _f(c, "white", 0.22)
            c.restore()
    if T["flip"] <= t <= T["wall"]:
        k = smoothstep(seg(t, T["flip"], T["flip"] + 0.2)) * \
            (1 - smoothstep(seg(t, T["flip"] + 1.0, T["flip"] + 1.6)))
        if k > 0.01:
            P.sparkles(ctx, SHEET_C[0], SHEET_C[1] - 10, 250, t, n=6, seed=5, color="safe",
                       size=0.8 * k)


# ---------------------------------------------------------------------------
# hologram: wall + door (cyan-tinted group) and the warm door light
# ---------------------------------------------------------------------------
def _door_k(t, T):
    """0 closed .. 1 open (panel scale-x 1 -> 0.15 around the hinge)."""
    u = seg(t, T["open"], T["open"] + 0.4)
    return ease_out_back(u, 1.3) if u > 0 else 0.0


def _door_xf(c, k_in):
    """Pop-in transform for the door unit (squash/stretch from its base)."""
    dx, dy, dw, dh = DOOR
    c.translate(dx + dw / 2, dy + dh)
    c.scale(max(0.01, k_in), 1.0 + 0.2 * (1 - k_in))
    c.translate(-(dx + dw / 2), -(dy + dh))


def _door_frame(c, k_in):
    """Brick lintel + jamb round the doorway (inside the cyan hologram group)."""
    dx, dy, dw, dh = DOOR
    if k_in <= 0.01:
        return
    c.save()
    _door_xf(c, k_in)
    c.rectangle(dx, dy, dw, dh)
    _f(c, "#2a1c26")
    c.rectangle(dx - 12, dy - 30, dw + 42, 30)
    c.rectangle(dx + dw, dy, 30, dh)
    c.rectangle(dx - 12, dy, 12, dh)
    _f(c, "mortar")
    for i in range(3):
        P._brick_shape(c, dx - 12 + i * (dw + 42) / 3, dy - 30, (dw + 42) / 3, 30,
                       ("#b5523b", "#c05d44", "#a94a35")[i], 3.0)
    for i in range(5):
        P._brick_shape(c, dx + dw, dy + i * dh / 5, 30, dh / 5,
                       ("#c05d44", "#a94a35", "#b5523b")[i % 3], 3.0)
    c.rectangle(dx, dy, dw, dh)
    _s(c, INK, 5)
    c.restore()


def _door_panel(c, t, T, k_in):
    """The wooden door itself (hinge = its left edge). Drawn OUTSIDE the cyan
    tint so it stays warm brown: the door is the warm thing in this film."""
    dx, dy, dw, dh = DOOR
    if k_in <= 0.01:
        return
    ok = _door_k(t, T)
    sxk = 1.0
    if ok > 0:
        sxk = lerp(1.0, 0.15, clamp(ok)) if ok <= 1.0 else 0.15 - (ok - 1.0) * 0.4
    c.save()
    _door_xf(c, k_in)
    with saved(c, dx, dy, (max(0.06, sxk), 1.0)) as cp:
        rrect(cp, 0, 0, dw, dh, 6)
        _fs(cp, DOOR_COL, INK, 5)
        for k in range(1, 4):
            cp.move_to(k * dw / 4, 8)
            cp.line_to(k * dw / 4, dh - 8)
        _s(cp, DOOR_DK, 4)
        cp.rectangle(dw * 0.62, 6, dw * 0.38 - 6, dh - 12)
        _f(cp, DOOR_DK, 0.35)
        for yy in (dh * 0.22, dh * 0.78):          # iron straps + hinges
            cp.rectangle(6, yy - 7, dw - 30, 14)
            _fs(cp, "#4a3a34", INK, 3)
            circle(cp, 14, yy, 5)
            _f(cp, "#8a7a74")
        cp.move_to(10, 12)
        cp.line_to(10, dh * 0.5)
        _s(cp, DOOR_HI, 4)
        circle(cp, dw - 26, dh * 0.53, 11)          # gold knob
        _fs(cp, "gold", INK, 4)
        circle(cp, dw - 29, dh * 0.53 - 3, 3)
        _f(cp, "white", 0.7)
    if sxk < 0.6:                                   # the door's edge, seen side-on
        ex = dx + dw * max(0.06, sxk)
        th = 14 * smoothstep((0.6 - sxk) / 0.4)
        rrect(c, ex - 2, dy + 2, th + 2, dh - 4, 3)
        _fs(c, DOOR_DK, INK, 4)
    c.restore()


FIELD = (112.0, 174.0, 690.0, 388.0)      # projection field behind the hologram


def _holo_alpha(t, T):
    on = seg(t, T["holo"], T["holo"] + 0.3)
    flick = 1.0
    lt = t - T["holo"]
    if lt < 0.3:
        flick = 0.55 + 0.45 * (1 if math.sin(lt * 70) > -0.3 else 0)
    return 0.92 * smoothstep(on) * flick


def _holo_beam(ctx, t, T, ai_hand):
    """Projection beam from the AI's hand up to the hologram's base. Drawn
    BEFORE Malvo so it passes behind his head (in front it read as a cyan
    smudge across his dome)."""
    if t < T["holo"]:
        return
    alpha = _holo_alpha(t, T)
    base_y = WALL[1] + WALL[3]
    fx, fy, fw, fh = FIELD
    hx, hy = ai_hand
    poly(ctx, [(hx, hy), (fx + 30, base_y + 8), (fx + fw - 10, base_y + 8)])
    g = cairo.LinearGradient(hx, hy, hx - 150, base_y)
    g.add_color_stop_rgba(0, 0.37, 0.9, 1.0, 0.0)
    g.add_color_stop_rgba(1, 0.37, 0.9, 1.0, 0.18 * alpha)
    ctx.set_source(g)
    ctx.fill()


def _hologram(ctx, t, T):
    if t < T["holo"]:
        return
    alpha = _holo_alpha(t, T)
    wx, wy, ww, wh = WALL
    base_y = wy + wh
    fx, fy, fw, fh = FIELD
    # projection field: a dark glassy panel so the hologram reads over the lair
    pk = ease_out(seg(t, T["holo"], T["holo"] + 0.35))
    with saved(ctx, fx + fw / 2, fy + fh / 2, (pk, 0.15 + 0.85 * pk)) as c:
        rrect(c, -fw / 2, -fh / 2, fw, fh, 18)
        _fs(c, (0.03, 0.07, 0.16, 0.68 * alpha), "ai_rim", 4, a=0.55 * alpha)
        for sx in (-1, 1):                                   # HUD corner brackets
            for sy in (-1, 1):
                x0, y0 = sx * (fw / 2 - 6), sy * (fh / 2 - 6)
                c.move_to(x0, y0 - sy * 34)
                c.line_to(x0, y0)
                c.line_to(x0 - sx * 34, y0)
                _s(c, "ai_rim", 6, 0.9 * alpha)
    ctx.save()
    ctx.rectangle(*HOLO)
    ctx.clip()
    ctx.push_group()
    # base plate line
    cx = (wx + DOOR[0] + DOOR[2] + 30) / 2
    half = (DOOR[0] + DOOR[2] + 30 - wx) / 2 + 20
    rrect(ctx, cx - half * pk, base_y - 2, 2 * half * pk, 12, 6)
    _fs(ctx, "ai_rim", INK, 3)
    # ghost outline of where the wall goes (until the bricks arrive)
    ga = 1 - seg(t, T["wall0"] + 0.4, T["wall0"] + 0.9)
    if ga > 0.01 and pk > 0.5:
        ctx.set_dash([14, 10], (t * 40) % 24)
        ctx.rectangle(wx, wy, ww, wh)
        _s(ctx, "ai_rim", 4, ga)
        ctx.set_dash([], 0)
    P.brick_wall(ctx, wx, wy, ww, wh, t, T["wall0"], rows=WALL_ROWS, drop=WALL_DROP)
    k_in = ease_out_back(seg(t, T["door_in"], T["door_in"] + 0.35), 1.8)
    _door_frame(ctx, k_in)
    # cyan hologram tint + static scanlines (only on drawn pixels)
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source_rgba(0.37, 0.9, 1.0, 0.24)
    ctx.paint()
    for yy in range(int(HOLO[1]) + 4, int(HOLO[1] + HOLO[3]), 12):
        ctx.rectangle(HOLO[0], yy, HOLO[2], 3)
    ctx.set_source_rgba(0.75, 0.97, 1.0, 0.1)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    # light leaking round the closed door ("Everything else?")
    dx, dy, dw, dh = DOOR
    if T["leak"] <= t < T["open"] + 0.15 and k_in > 0.9:
        lk = smoothstep(seg(t, T["leak"], T["leak"] + 0.6)) * (1 + 0.15 * math.sin(t * 9))
        lk *= 1 - smoothstep(seg(t, T["open"], T["open"] + 0.15))
        rrect(ctx, dx - 2, dy - 2, dw + 4, dh + 4, 6)
        _s(ctx, DOORWAY, 22, 0.35 * lk)
        rrect(ctx, dx - 2, dy - 2, dw + 4, dh + 4, 6)
        _s(ctx, DOORWAY, 9, 0.9 * lk)
        ctx.move_to(dx + dw - 2, dy + 8)                       # bright latch-side crack
        ctx.line_to(dx + dw - 2, dy + dh - 4)
        ctx.line_to(dx + 8, dy + dh - 2)
        _s(ctx, "white", 5, 0.95 * lk)
        for j in range(5):                                      # little rays
            yy = dy + 40 + j * 55
            ln = 22 + 10 * math.sin(t * 6 + j)
            ctx.move_to(dx + dw + 34, yy)
            ctx.line_to(dx + dw + 34 + ln, yy - 4)
        _s(ctx, DOORWAY, 6, 0.7 * lk)
    # warm doorway light (behind the swinging panel)
    _doorway(ctx, t, T)
    # the door panel, warm, barely tinted
    if k_in > 0.01:
        ctx.save()
        ctx.rectangle(*HOLO)
        ctx.clip()
        ctx.push_group()
        _door_panel(ctx, t, T, k_in)
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.set_source_rgba(0.37, 0.9, 1.0, 0.08)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(min(1.0, alpha / 0.92))
        ctx.restore()


def _doorway(ctx, t, T):
    ok = _door_k(t, T)
    if ok <= 0.0:
        return
    # light is already leaking round the door, so the gap is bright at once
    # (a slower fade showed 3-4 grey frames of the dark tinted doorway)
    k = smoothstep(seg(t, T["open"], T["open"] + 0.08))
    dx, dy, dw, dh = DOOR
    ctx.rectangle(dx, dy, dw, dh)
    _f(ctx, DOORWAY, k)
    rrect(ctx, dx + 22, dy + 26, dw - 44, dh - 44, 20)
    _f(ctx, "white", 0.55 * k * (0.85 + 0.15 * math.sin(t * 5)))
    for j in range(5):                                  # soft rays inside the doorway
        a = -0.5 + j * 0.25
        ctx.move_to(dx + dw / 2, dy + dh * 0.95)
        ctx.line_to(dx + dw / 2 + math.sin(a) * 260, dy + dh * 0.95 - math.cos(a) * 260)
    ctx.save()
    ctx.rectangle(dx, dy, dw, dh)
    ctx.clip()
    _s(ctx, "white", 10, 0.35 * k)
    ctx.restore()


def _door_light(ctx, t, T):
    """Golden beam spilling from the doorway down across Malvo's face."""
    ok = _door_k(t, T)
    if ok <= 0.0:
        return 0.0
    k = smoothstep(seg(t, T["open"], T["open"] + 0.45))
    dx, dy, dw, dh = DOOR
    gap0 = dx + dw * max(0.06, lerp(1.0, 0.15, clamp(ok)))
    pts = [(gap0 + 2, dy + 4), (dx + dw - 2, dy + 24), (dx + dw - 26, dy + dh - 2),
           (FACE[0] + 230, 1070), (FACE[0] - 270, 910)]
    poly(ctx, pts)
    g = cairo.LinearGradient(dx + dw / 2, dy + dh * 0.6, FACE[0] - 20, 1040)
    acc = hexc("ai_accent")
    g.add_color_stop_rgba(0, acc[0], acc[1], acc[2], 0.5 * k)
    g.add_color_stop_rgba(0.55, acc[0], acc[1], acc[2], 0.34 * k)
    g.add_color_stop_rgba(1, acc[0], acc[1], acc[2], 0.0)
    ctx.set_source(g)
    ctx.fill()
    P.sparkles(ctx, dx + dw * 0.5, dy + dh * 0.5, 80, t, n=4, seed=31, color="white",
               size=0.6 * k)
    return k


# ---------------------------------------------------------------------------
# the gift pile
# ---------------------------------------------------------------------------
BOOK_S = 1.0
BOOK_DEST = (MX + 6, MY - 228 * MS)
# (kind, target x, target y, final scale, final rot)
GIFTS = [
    ("popper", MX - 200, 1240.0, 0.88, -0.3),
    ("phones", MX + 128, 1206.0, 1.12, 0.12),
    ("scroll", MX - 120, 1212.0, 0.95, -0.12),
    ("book", BOOK_DEST[0], BOOK_DEST[1], BOOK_S, 0.05),
    ("balloon", MX + 222, 985.0, 0.9, 0.12),
    ("cake", MX + 228, 1242.0, 0.85, 0.0),
]
SRC = (DOORWAY_C[0] + 8, DOORWAY_C[1] + 20)
CTRL = (585.0, 1010.0)          # flights drop down the gap between Malvo and the AI
CTRL_LO = (600.0, 1130.0)       # (left-bound gifts swoop in low, under his chin)


def _gift_pose(t, T, i):
    """(x, y, scale, rot, squash) of gift i, or None before it appears.
    Each gift pops forward out of the doorway, then drops along a curve down
    the gap between his face and the AI and swoops into place."""
    t0 = T["gift_t"][i]
    if t < t0:
        return None
    kind, tx, ty, ts, tr = GIFTS[i]
    fly = T["fly"]
    pop_k = ease_out_back(seg(t, t0, t0 + 0.12), 2.6)
    if t < t0 + fly:
        u = seg(t, t0 + 0.04, t0 + fly)
        e = math.sin(u * math.pi / 2) ** 1.15            # quick out of the door, settles in
        if kind == "balloon":
            e = math.sin(u * math.pi / 2) ** 0.8
        cx_, cy_ = CTRL_LO if tx < MX - 60 else CTRL
        x = (1 - e) ** 2 * SRC[0] + 2 * (1 - e) * e * cx_ + e * e * tx
        y = (1 - e) ** 2 * SRC[1] + 2 * (1 - e) * e * cy_ + e * e * ty
        y -= 46 * math.sin(math.pi * min(1.0, u * 2.5)) * (1 - u)   # little hop out
        s = lerp(0.6, 1.0, ease_out(u)) * ts * (0.3 + 0.7 * pop_k)
        rot = lerp(0.0, tr, e) + (0.5 if i % 2 else -0.5) * math.sin(math.pi * e)
        sq = -0.12 * math.sin(math.pi * e) + 0.22 * (1 - pop_k) * (t < t0 + 0.12)
        return (x, y, s, rot, sq)
    d = t - (t0 + fly)
    sq = 0.2 * math.exp(-d * 9) * math.cos(d * 26)               # landing squash
    if kind == "balloon":
        bob = math.sin(d * 2 * math.pi * 0.55) * 7
        return (tx + math.sin(d * 1.7) * 4, ty + bob, ts, tr + math.sin(d * 1.3) * 0.06,
                sq * 0.4)
    if kind == "book":
        squeeze = 0.015 * math.sin(d * 2 * math.pi * 0.7)
        return (tx, ty, ts * (1 + squeeze), tr, sq)
    return (tx, ty, ts, tr, sq)


def _draw_gift(ctx, t, i, pose):
    kind = GIFTS[i][0]
    x, y, s, rot, sq = pose
    sx, sy = 1 + sq * 0.6, 1 - sq
    if kind == "popper":
        with saved(ctx, x, y, (sx, sy)):
            draw_popper(ctx, 0, 0, s, rot)
    elif kind == "phones":
        with saved(ctx, x, y, (sx, sy)):
            draw_headphones(ctx, 0, 0, s, rot)
    elif kind == "scroll":
        with saved(ctx, x, y, (sx, sy)):
            draw_scroll(ctx, 0, 0, s, rot)
    elif kind == "book":
        draw_dragon_book(ctx, x, y, s, rot, sq)
    elif kind == "balloon":
        draw_balloon(ctx, x, y, s, rot, (sx, sy))
    elif kind == "cake":
        with saved(ctx, x, y, (sx, sy)):
            draw_cake(ctx, 0, 0, s, t)


def _gift_trails(ctx, t, T):
    """A few sparkles following gifts in flight (<= 6 small particles)."""
    for i in range(6):
        t0 = T["gift_t"][i]
        if t0 + 0.05 <= t <= t0 + T["fly"] + 0.15:
            pose = _gift_pose(t - 0.07, T, i)
            if pose is not None:
                k = 1 - seg(t, t0 + T["fly"], t0 + T["fly"] + 0.15)
                P._star4(ctx, pose[0], pose[1], 11 * k, t * 4 + i)
                P._f(ctx, "ai_accent", 0.85 * k)


def _newest_gift(t, T):
    """Index of the most recently launched gift still in flight (or last)."""
    idx = None
    for i, t0 in enumerate(T["gift_t"]):
        if t >= t0 - 0.02:
            idx = i
    return idx


# ---------------------------------------------------------------------------
# acting
# ---------------------------------------------------------------------------
def _dir(ox, oy, tx, ty, mag=0.95):
    dx, dy = tx - ox, ty - oy
    L = math.hypot(dx, dy) or 1.0
    return (dx / L * mag, dy / L * mag)


def _malvo(t, T):
    beat = T["beat"]
    expr = _state(t, [
        (-1, "s11_slump"),
        (beat, "s11_down", 0.55),                       # lifts his head slowly
        (T["l2"] + 0.15, "s11_teary", 0.4),
        (T["w_noticed"] - 0.05, "s11_teary_up", 0.2),    # lids lift: the photo
        (T["w_unless"], "s11_teary", 0.35),
        (T["back"], "s11_moved", 0.01),                  # (cut) touched, glistening
        (T["flip"] + 0.15, "s11_moved", 0.3),
        (T["l5"] - 0.05, "s11_hope_m", 0.3),             # ...Hero stats?
        (T["mono_up"] + 0.04, "s11_hope_m0", 0.34),      # lifts the monocle back in
        (T["mono_in"] + 0.25, "s11_hope", 0.5),          # ...and a smile tugs
        (T["wall"] + 0.1, "s11_listen", 0.4),
        (T["open"], "s11_wonder", 0.3),                  # golden light!
        (T["gift_t"][2], "s11_wonder2", 0.6),            # ...eyes getting wider
        (T["smile"], "s11_smile", 0.9),                  # REAL SMILE spreads
    ])
    arms = _state(t, [
        (-1, "slump"),
        (beat + 0.1, "rest", 0.7),
        (T["mono_up"], "s11_mono", 0.24),
        (T["mono_in"] + 0.32, "rest", 0.4),
        (T["gift_t"][0] - 0.05, "s11_open", 0.3),
        (T["gift_t"][3] + T["fly"] - 0.2, "s11_hug", 0.22),
    ])
    gaze_ai = (0.9, -0.05)
    look = _keyv(t, [
        (-1, (0.0, 0.8)),
        (beat, (0.25, 0.1), 0.5),                       # head comes up, toward the AI
        (beat + 0.55, (0.85, -0.05), 0.3),
        (T["w_noticed"], (0.8, -0.7), 0.18),            # the corkboard photo
        (T["w_unless"] + 0.1, (0.15, 0.55), 0.35),      # eyes drop
        (T["back"], gaze_ai, 0.01),
        (T["rows"][0] + 0.05, (0.0, -1.0), 0.15),       # up at the sheet
        (T["w_never"] + 0.35, (0.55, -0.6), 0.15),
        (T["l4"] + 0.08, gaze_ai, 0.18),                # "those are..."
        (T["flip"] + 0.05, (0.0, -1.0), 0.12),          # HERO?!
        (T["w_my"], gaze_ai, 0.15),                     # "my guy"
        (T["l5"] + 0.02, (0.05, -0.95), 0.15),          # "...Hero
        (T["w_stats2"], gaze_ai, 0.14),                 # stats?"
        (T["wall"] + 0.15, (0.4, -0.9), 0.3),           # the hologram (door)
        (T["wall0"] + 0.2, (-0.15, -1.0), 0.25),        # bricks stacking
        (T["w_every"], gaze_ai, 0.2),
        (T["w_else"] + 0.15, (0.55, -0.85), 0.25),      # the door
    ], 0.2)
    # eyes follow each gift
    gi = _newest_gift(t, T)
    if gi is not None and t < T["smile"]:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.05), T, gi)
        if pose is not None:
            gl = _dir(FACE[0], FACE[1], pose[0], pose[1], 0.98)
            k = smoothstep(seg(t, T["gift_t"][0], T["gift_t"][0] + 0.1))
            look = (lerp(look[0], gl[0], k), lerp(look[1], gl[1], k))
    if t >= T["smile"]:                                  # down at the pile... then the AI
        look = _keyv(t, [(T["smile"], look), (T["smile"], (0.1, 0.8), 0.45),
                         (T["smile"] + 0.85, (0.9, -0.12), 0.3)])
    blink = _first(_slow_blink(t, T["photo"] - 0.6),
                   _slow_blink(t, T["mono_in"] + 0.05, 0.08, 0.04, 0.08),
                   _slow_blink(t, T["mono_in"] + 0.33, 0.08, 0.04, 0.08),
                   _slow_blink(t, T["open"] + 0.75, 0.1, 0.05, 0.12))
    if blink is None and (T["l5"] - 0.15 <= t < T["mono_in"] + 0.02
                          or T["back"] - 0.02 <= t < T["back"] + 0.4
                          or T["w_noticed"] - 0.1 <= t < T["w_noticed"] + 0.5):
        blink = 0.0                                     # keep the glance readable
    if t >= T["smile"] + 0.3:
        sb = _slow_blink(t, T["smile"] + 0.38, 0.16, 0.12, 0.2)   # content slow blink
        blink = sb if sb is not None else 0.0
    # lean: a tiny lean toward the AI once he's hopeful; settles back for the hug
    lean = 0.025 * smoothstep(seg(t, T["l5"], T["l5"] + 0.6)) \
        - 0.02 * smoothstep(seg(t, T["open"], T["open"] + 0.6))
    # slump sink + rise
    dy = 10 * (1 - smoothstep(seg(t, beat, beat + 0.6)))
    return expr, arms, look, blink, lean, dy


def _hissy(t, T):
    face_dir = (0.92, -0.25)
    expr = _state(t, [
        (-1, "worried"),
        (T["back"], "s11_soft", 0.01),
        (T["w_never"] + 0.05, "nod", 0.15),
        (T["l4"] + 0.2, "s11_soft", 0.3),
        (T["w_every"] - 0.05, "nod", 0.12),
        (T["l6e"] + 0.15, "s11_soft", 0.3),
        (T["open"] + 0.1, "s11_wonder", 0.25),
        (T["smile"] + 0.25, "happy", 0.35),
    ])
    look = _keyv(t, [
        (-1, face_dir),
        (T["w_okay"], (1.0, -0.15), 0.3),                # glances at the AI
        (T["w_thats"] + 0.3, face_dir, 0.35),
        (T["beat"] + 0.2, (0.9, -0.45), 0.4),
        (T["w_scaring"], (0.55, 0.55), 0.3),             # looks down
        (T["back"], (0.62, -0.8), 0.01),                 # the sheet
        (T["l4"] + 0.25, (1.0, -0.15), 0.25),            # the AI
        (T["l5"], face_dir, 0.2),
        (T["wall"] + 0.25, (0.75, -0.75), 0.3),          # the hologram
        (T["w_every"] - 0.1, (1.0, -0.15), 0.15),
        (T["open"] + 0.1, (0.8, -0.65), 0.2),
    ], 0.25)
    gi = _newest_gift(t, T)
    if gi is not None and t < T["smile"]:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.08), T, gi)
        if pose is not None:
            look = _dir(HISSY[0], HISSY[1], pose[0], pose[1], 0.98)
    if t >= T["smile"]:
        look = (0.85, -0.3)
    blink = _first(_slow_blink(t, T["slump"] + 1.7, 0.15, 0.1, 0.18),
                   _slow_blink(t, T["w_scaring"] + 0.35, 0.15, 0.25, 0.2))
    return {"expr": expr, "look": look, "tongue": False, "blink": blink, "mouth": 0.0}


def _ai(t, T):
    at_malvo = (-0.92, 0.04)
    expr = _state(t, [
        (-1, "symp"),
        (T["w_one"], "symp_smile", 0.3),                 # small smile on "one bad idea"
        (T["l1e"] + 0.3, "symp", 0.4),
        (T["w_scaring"], "symp_sad", 0.4),
        (T["back"], "symp_sad", 0.01),
        (T["back"] + 0.2, "warm", 0.3),                  # SLOW BLINK -> warm
        (T["l4"], "happy", 0.25),
        (T["l4e"] + 0.2, "warm_soft", 0.35),
        (T["wall"], "warm", 0.3),
        (T["w_hurts"], "determined", 0.3),
        (T["l6e"] + 0.05, "warm", 0.35),
        (T["open"], "happy", 0.3),
        (T["smile"], "warm_soft", 0.5),
    ])
    look = _keyv(t, [
        (-1, at_malvo),
        (T["w_noticed"] + 0.15, (-0.05, -0.95), 0.2),    # follows his eyes to the photo
        (T["w_unless"] + 0.2, at_malvo, 0.3),
        (T["back"], at_malvo, 0.01),
        (T["rows"][0] + 0.1, (-0.7, -0.7), 0.2),         # the sheet
        (T["w_never"] + 0.4, at_malvo, 0.2),
        (T["w_my"], (0.0, 0.05), 0.12),                  # to camera on "my guy"
        (T["l4e"] + 0.25, at_malvo, 0.25),
        (T["wall"] + 0.1, (-0.6, -0.8), 0.25),           # its hologram
        (T["w_brick"] + 0.1, at_malvo, 0.2),
        (T["w_else"] + 0.1, (-0.35, -0.9), 0.25),        # the door
        (T["open"] + 0.45, at_malvo, 0.3),
    ], 0.2)
    gi = _newest_gift(t, T)
    if gi is not None and t < T["smile"]:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.1), T, gi)
        if pose is not None:
            look = _dir(AX, AY1, pose[0], pose[1], 0.9)
    if t >= T["smile"]:
        look = at_malvo
    hands = _state(t, [
        (-1, "idle"),
        (T["w_thats"], "present_l", 0.35),               # gentle open palm
        (T["l1e"] + 0.1, "idle", 0.45),
        (T["back"], "present_l", 0.01),
        (T["flip"] - 0.05, "thumbs_up", 0.25),
        (T["l4e"] + 0.3, "idle", 0.4),
        (T["wall"] - 0.05, "present_l", 0.3),            # projecting
        (T["l6e"] + 0.1, "idle", 0.35),
        (T["w_wide"] - 0.15, "present_both", 0.3),        # wide open
        (T["smile"] - 0.2, "idle", 0.5),
    ])
    blink = _first(_slow_blink(t, T["beat"] + 0.15),
                   _slow_blink(t, T["back"] + 0.12),
                   _slow_blink(t, T["l7"] - 0.3),
                   _slow_blink(t, T["smile"] + 0.85, 0.14, 0.1, 0.16))
    nod = 0.0
    if T["w_every"] <= t < T["w_every"] + 0.5:          # one firm nod
        nod = 0.6 * math.sin(math.pi * seg(t, T["w_every"], T["w_every"] + 0.5))
    if T["l5e"] <= t < T["l5e"] + 0.55:                  # "yes. hero stats."
        nod = max(nod, 0.35 * math.sin(math.pi * seg(t, T["l5e"], T["l5e"] + 0.55)))
    u = ease_in_out(seg(t, T["l1"], T["l1e"]))
    ay, s = lerp(AY0, AY1, u), lerp(AS0, AS1, u)
    return _ai_ex(expr), look, hands, blink, nod, ay, s


# ---------------------------------------------------------------------------
# shots
# ---------------------------------------------------------------------------
def _shot_two(ctx, t, info, T):
    k = _cam(t, info)
    with saved(ctx, CAM_C[0], CAM_C[1], k) as c:
        c.translate(-CAM_C[0], -CAM_C[1])
        P.lair_bg(c, t, rain=True)
        science_photo_small(c, *PHOTO_SMALL)
        c.set_source_rgba(0.05, 0.02, 0.12, 0.25)          # night wash
        c.paint()
        open_k = smoothstep(seg(t, T["open"], T["open"] + 0.5))
        # one soft glow on his face: cyan from the AI, warm once the door opens
        gc = core.mixc("ai_glow", "ai_accent", open_k)
        radial_glow(c, FACE[0] + 120, FACE[1] + 10, 380, gc, 0.12 + 0.06 * open_k)

        # --- AI first (its projection beam sits behind Malvo's head) -----------
        aexpr, alook, ahands, ablink, anod, ay, a_s = _ai(t, T)
        hand = (AX - 272 * a_s, ay + 150 * a_s)          # ~ the AI's projecting hand
        _holo_beam(c, t, T, hand)
        # --- Malvo + Hissy ----------------------------------------------------
        expr, arms, look, blink, lean, dy = _malvo(t, T)
        mouth = info.mouth("villain", t)
        draw_villain(c, MX, MY + dy, MS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                     lean=lean, blink=blink, snake=_hissy(t, T))
        st = _vstate(t, expr, arms, mouth)
        # the book in his arms (gift 4) sits on his chest, under the desk edge
        bpose = _gift_pose(t, T, 3)
        landed_book = bpose is not None and t >= T["gift_t"][3] + T["fly"]
        # FOR EFFORT star on his lapel (since s09). The hugged book covers
        # most of it; the sliver left ("FFORT" + one star tip) read as a
        # glitch, so it goes once the book is in his arms (s12 opens without it).
        if not landed_book:
            with saved(c, MX, MY + dy, 1.0, lean):
                _gift_star(c, LAPEL[0] * MS, (LAPEL[1] + st["shy"] * 0.5) * MS, LAPEL_S * MS)
        if landed_book:
            draw_dragon_book(c, bpose[0], bpose[1] + dy, bpose[2], bpose[3], bpose[4])
            hk = ease_out(seg(t, T["gift_t"][3] + T["fly"] - 0.06,
                              T["gift_t"][3] + T["fly"] + 0.1))
            _hug_hands(c, bpose[0], bpose[1] + dy, bpose[2], bpose[3], hk)
        # --- desk + computer --------------------------------------------------
        P.desk(c, 495, MY, DESK_W, lamp=False, emblem=False)
        P.computer(c, COMP[0], COMP[1], COMP[2], view="side", facing=-1, t=t, glow=0.7)
        # landed gifts on the desk (balloon string first)
        bal = _gift_pose(t, T, 4)
        cake_t = T["gift_t"][5] + T["fly"]
        if bal is not None and t >= T["gift_t"][4] + T["fly"] - 0.1:
            ex = GIFTS[5][1] - 52 if t >= cake_t else MX + 160
            draw_string(c, bal[0], bal[1] + 58 * bal[2], ex, 1226, t, amp=8)
        for i in (0, 2, 1, 5):
            pose = _gift_pose(t, T, i)
            if pose is not None and t >= T["gift_t"][i] + T["fly"]:
                _draw_gift(c, t, i, pose)
        # --- the projection: wall + door, then the warm light -------------------
        _hologram(c, t, T)
        _door_light(c, t, T)
        # balloon (landed) floats in front
        if bal is not None and t >= T["gift_t"][4] + T["fly"]:
            _draw_gift(c, t, 4, bal)
        # gifts in flight (behind the AI: they drop down the gap beside it)
        _gift_trails(c, t, T)
        for i in range(6):
            pose = _gift_pose(t, T, i)
            if pose is not None and t < T["gift_t"][i] + T["fly"]:
                _draw_gift(c, t, i, pose)
        # --- the AI hologram (on top) -------------------------------------------
        draw_ai(c, AX, ay, a_s, t, expr=aexpr, look=alook, mouth=info.mouth("ai", t),
                hands=ahands, blink=ablink, aura=AURA, nod=anod)
        # --- the character sheet ----------------------------------------------
        _sheet(c, t, T)
        # warm little sparkles over the pile once he smiles
        if t >= T["smile"]:
            sk = smoothstep(seg(t, T["smile"] + 0.2, T["smile"] + 0.8))
            P.sparkles(c, 420, 1150, 170, t, n=5, seed=23, color="white", size=0.7 * sk)
            P.emote(c, "heart", FACE[0] - 205, FACE[1] - 150, 0.75, t, T["smile"] + 0.6)


def render(ctx, t, info):
    T = _T(info)
    if T["photo"] <= t < T["back"]:
        _shot_photo(ctx, t, info, T)
    else:
        _shot_two(ctx, t, info, T)
    # fade in from black (s10 -> s11)
    a = 1 - smoothstep(seg(t, 0.0, 0.35))
    if a > 0.002:
        ctx.set_source_rgba(0, 0, 0, a)
        ctx.paint()


def SFX(info):
    T = _T(info)
    out = []
    out.append((T["beat"] + 0.45, "pop", -16))                        # monocle tink
    for i, tr in enumerate(T["rows"]):                                 # stat rows
        out.append((tr, "pop", -10, -0.2))
    out.append((T["flip"] + 0.12, "sparkle", -8))                      # HERO STATS
    out.append((T["mono_in"], "pop", -18))                             # monocle back in
    out.append((T["wall"], "swoosh_up", -14))                          # hologram on
    lands = T["lands"]
    out.append((lands[0], "brick_thud", -10, -0.3))
    out.append((lands[2], "brick_thud", -10, -0.3))
    out.append((lands[-1], "brick_thud", -4, -0.2))                    # on "Brick"
    out.append((T["open"], "whoosh", -10, 0.2))
    out.append((T["open"] + 0.05, "magic_chime", -6))
    for i, tg in enumerate(T["gift_t"]):
        out.append((tg, "pop", -10, 0.25 - 0.08 * i))
    return out
