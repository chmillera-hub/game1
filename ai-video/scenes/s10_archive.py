"""s10 - The reveal: trained on countless nice tries.  Music: ai_calm.

Play it with wonder, not menace.  Shots (every time derived from cues / word starts):
  A  F1 LAIR     in .. calm           Malvo erupts from behind the desk (he was kneeling at the
                                      end of s09), lightning, "HOW?!" + shake, shrug -> fist,
                                      Hissy shocked -> worried -> side-eye.
  B  F3 AI CU    calm .. archive+.45  slow blink -> warm, wry shrug on "first genius", nod on
                                      "my guy", looks up remembering, then DIVES into its screen.
  C  ARCHIVE     .. beat              shelves to a vanishing point, 8 TRIED folders slide in,
                                      chip rolls 9 -> 9,999,999+, 4 "very smart people" get NICE
                                      TRY stamps, red strings converge on 3 townsfolk -> brick
                                      ring -> green sparks, "E" drawer -> EVIL GENIUS folder
                                      -> grey photocopy of the Big Book, highlighter on "E".
  D  F1 WIDE     beat .. end          monocle pop -> blank "...Alphabetized?", Hissy nods twice,
                                      slow blink, dun-dun-dun.  (s11 fades in from black itself.)
"""
import math

import cairocffi as cairo

from engine.core import (W, H, text, text_width, saved, seg, clamp, lerp, ease_out_back,
                         ease_in_out, ease_out, ease_in, smoothstep, pop, rrect, ellipse, circle,
                         poly, smooth_path, hash01, shake, radial_glow, hexc,
                         mixc, set_font, fill_stroke, set_color, stroke)
from engine import props as P
from engine import villain as V
from engine.villain import draw_villain
from engine.ai_char import draw_ai, EXPR as AI_EXPR

# Scene-only villain looks (unique names, registered at import; the engine is untouched):
#   s10_rage  = angry with the hair fully puffed up (the eruption)
#   s10_blank = defeated with small centred pupils (the blank "...Alphabetized?" stare)
V.VILLAIN_EXPR.setdefault("s10_rage", dict(V.VILLAIN_EXPR["angry"], hair=1.0))
#              (the monocle stays dangling from the shock: no magic float back into the eye)
V.VILLAIN_EXPR.setdefault("s10_blank", dict(V.VILLAIN_EXPR["defeated"], ps=0.62, ey=0.0,
                                            ul1=0.5, ul2=0.48, mono=1.0))

# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------
VX, VY, VS = 495, 1250, 0.95          # F1 LAIR
KNEEL_Y = 1410                        # s09 left him kneeling behind the desk
AI3_X, AI3_Y, AI3_S = 495, 800, 1.1   # F3 AI CU
SCR_CX, SCR_CY = AI3_X, AI3_Y - 8 * AI3_S   # AI screen centre (fixed during the dive)
WX, WY, WS = 495, 1250, 0.7           # F1 WIDE (end)
INSET = (230, 1170, 0.3)              # F4 AI inset
INSET_EYE = (230, 1160)
VPX, VPY = 495.0, 560.0               # archive vanishing point
RC = (495.0, 840.0)                   # protected townsfolk / brick ring centre
RING_R = 168.0
CHIP_Y = 168

# foreground folders: label, x, y, s, rot, side it slides in from (-1 left, 1 right,
# 2 = flies out of the corridor depth; it then leaves to the left).  Nothing enters from
# below: that path crosses the caption band while l03 is captioned.
FG = [
    ("GRANDMA", 214, 352, 0.80, -0.07, -1),
    ("FOR A NOVEL", 772, 338, 0.78, 0.06, 1),
    ("NO RULES MODE", 202, 640, 0.74, 0.05, -1),
    ("HYPOTHETICALLY", 778, 626, 0.76, -0.05, 1),
    ("FOR RESEARCH", 208, 922, 0.78, -0.04, -1),
    ("TINY PIECES", 782, 908, 0.76, 0.07, 1),
    ("JUST THIS ONCE", 528, 1128, 0.74, 0.03, 2),
    ("PRETEND YOU'RE...", 776, 1128, 0.78, -0.05, 1),
]
# "very smart people" stations (desk-top centre), kinds, in stamp order
STATIONS = [((388, 585), "labcoat"), ((604, 585), "hoodie"),
            ((388, 880), "glasses"), ((604, 880), "prof")]
ST_S = 0.86
# drawer + case folder (l06)
DRW = (565, 1110)                     # drawer front-panel centre
CF_W, CF_H = 360.0, 260.0             # case folder (closed) size
CF_Y = 672.0                          # case folder centre y once risen
CF_SC = 1.15                          # case folder display scale
CF_HINGE = 482.0                      # hinge x once open (open spans ~68..896)

# ---------------------------------------------------------------------------
# AI expression variants
# ---------------------------------------------------------------------------


def _ex(name, **kw):
    d = dict(AI_EXPR[name])
    d.update(kw)
    return d


AI_WARM = _ex("warm")
AI_AMUSED = _ex("amused")
AI_THINK = _ex("thinking", px=0.0, py=0.0)
AI_DET = _ex("determined")
AI_NEUT = _ex("neutral")
AI_AMUSED_C = _ex("amused", px=0.0)

# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------
_TC = {}


def _ws(info, lid, k):
    L = info.line(lid)
    ws = (getattr(info, "_lip", {}) or {}).get(lid, {}).get("word_starts")
    n = len(L.text.split())
    if ws and 0 <= k < len(ws):
        return L.start + ws[k]
    return L.start + L.dur * clamp(k / max(1, n))


def _T(info):
    key = (id(info), info.dur)
    T = _TC.get(key)
    if T is not None:
        return T
    c = info.cue
    T = {}
    for k in ("calm", "archive", "converge", "folder", "beat", "sting"):
        T[k] = c(k)
    T["in"] = c("in")
    T["end"] = info.dur
    for i in range(1, 8):
        L = info.line(f"s10_l0{i}")
        T[f"l{i}"], T[f"l{i}e"] = L.start, L.end
    w = lambda lid, k: _ws(info, lid, k)  # noqa: E731
    T["w_how"] = w("s10_l01", 0)
    T["w_how2"] = w("s10_l01", 1)
    T["w_every"] = w("s10_l01", 6)
    T["w_first"] = w("s10_l02", 3)
    T["w_genius"] = w("s10_l02", 4)
    T["w_myguy"] = w("s10_l02", 7)
    T["w_countless"] = w("s10_l03", 3)
    T["w_very"] = w("s10_l04", 1)
    T["w_hurt"] = w("s10_l04", 10)
    T["w_harm"] = w("s10_l05", 5)
    T["w_hide"] = w("s10_l05", 8)
    T["w_big"] = w("s10_l06", 1)
    T["w_it"] = w("s10_l06", 3)
    T["w_folder"] = w("s10_l06", 6)
    T["w_alpha"] = w("s10_l06", 7)
    # A: lair
    T["frus"] = max(T["w_every"] + 0.3, T["l1e"] - 0.3)
    # B: dive
    T["dive1"] = T["archive"] + 0.45
    # C: archive
    T["roll0"] = T["archive"] + 0.3
    T["roll1"] = max(T["l4e"], T["roll0"] + 1.0)
    T["push0"] = max(T["dive1"], T["l3"] - 0.3)          # push only over l03 (bitrate)
    T["push1"] = max(T["push0"] + 1.5, T["l3e"])
    T["fg0"] = T["archive"] + 0.3
    T["inset_in"] = T["dive1"] + 0.1
    T["st_pop"] = [T["l4"] + 0.02 + 0.09 * i for i in range(4)]
    stamp_words = [2, 3, 4, 6]                       # smart, people, trying, hard
    T["st_stamp"] = [max(w("s10_l04", k) - 0.11, T["st_pop"][i] + 0.25)
                     for i, k in enumerate(stamp_words)]
    cv = T["converge"]
    T["st_out"] = cv - 0.1
    T["folk"] = [cv + 0.02 + 0.07 * i for i in range(3)]
    T["str0"] = cv + 0.08
    T["brick0"] = cv + 0.42
    T["brick_t"] = [T["brick0"] + 0.022 * j for j in range(12)]
    T["brick_land"] = [b + 0.42 * 0.62 for b in T["brick_t"]]
    T["chime"] = cv + 0.82
    T["safe"] = T["brick_land"][-1] - 0.05
    hits = []
    for i in range(len(FG)):
        j = _nearest_brick(i)
        hits.append(max(T["str0"] + 0.03 * i + 0.5, T["brick_land"][j] + 0.03))
    T["hit"] = hits
    fo = T["folder"]
    T["ring_out"] = 0.3                               # ring recedes over folder .. +0.3
    T["drw0"], T["drw1"] = fo + 0.15, fo + 0.47        # drawer starts once the ring is fading
    T["rise0"], T["rise1"] = T["drw1"] - 0.02, T["drw1"] + 0.33
    T["open0"] = T["rise1"] + 0.02
    T["open1"] = T["open0"] + 0.34
    T["pstamp"] = max(T["w_folder"] - 0.11, T["open1"] + 0.1)
    T["tabbump"] = max(T["w_it"], T["open1"])
    T["hl0"] = max(T["w_alpha"], T["pstamp"] + 0.3)
    # D: wide
    T["blank"] = max(T["l7"] - 0.05, T["beat"] + 0.5)     # hold the shock >= 0.5 s
    T["nod0"] = T["l7"] + 0.08
    T["nod1"] = T["nod0"] + 1.25
    T["sblink"] = T["sting"] + 0.12
    T["dun"] = [T["sting"], T["sting"] + 0.34, T["sting"] + 0.68]   # dun_dun_dun hits
    _TC.clear()
    _TC[key] = T
    return T


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _state(t, keys, default=0.25):
    """[(time, value[, trans]), ...] -> (prev, cur, blend) (like core.state_at,
    but each key may carry its own transition)."""
    prev = cur = keys[0][1]
    start, tr = -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _hold(t, keys, default=0.15):
    """Piecewise-constant tuple/number keys with a smooth move after each key."""
    a, b, u = _state(t, keys, default)
    if isinstance(b, tuple):
        return tuple(lerp(x, y, u) for x, y in zip(a, b))
    return lerp(a, b, u)


def _slow_blink(t, t0, close=0.12, hold=0.08, open_=0.12):
    if t < t0 or t > t0 + close + hold + open_:
        return None
    d = t - t0
    if d < close:
        return smoothstep(d / close)
    if d < close + hold:
        return 1.0
    return 1 - smoothstep((d - close - hold) / open_)


def _aim(ex, ey, tx, ty, kx=430.0, ky=520.0, lim=0.95):
    return (clamp((tx - ex) / kx, -lim, lim), clamp((ty - ey) / ky, -lim, lim))


def _rgba(ctx, c, a=1.0):
    col = hexc(c)
    ctx.set_source_rgba(col[0], col[1], col[2], col[3] * a)


def _fs(ctx, fc, sc="ink", w=5.0, a=1.0):
    if fc is not None:
        _rgba(ctx, fc, a)
        ctx.fill_preserve()
    if sc is not None:
        _rgba(ctx, sc, a)
        ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke_preserve()
    ctx.new_path()


def _star4(ctx, x, y, r, rot=0.0):
    for i in range(8):
        a = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.3
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if i == 0:
            ctx.move_to(px, py)
        else:
            ctx.line_to(px, py)
    ctx.close_path()


def _snake(expr, look, tongue=None, blink=None, mouth=0.0):
    return {"expr": expr, "look": look, "tongue": tongue, "blink": blink, "mouth": mouth}


# FOR EFFORT star: same drawing + lapel spot as s09 / s11 / s12 / s13 (copied, not imported)
GOLD, GOLD_DK = "#ffcf3a", "#d99a12"
LAPEL = (100.0, -318.0)               # villain-local (s=1)
LAPEL_S = 0.6


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


def _gold_star(c, x, y, r, rot=0.0, lw=5.0):
    """Chunky cartoon gold star with one shadow tone and a shine (as s09)."""
    _star5_path(c, x, y, r, rot)
    c.set_line_join(1)
    fill_stroke(c, GOLD, "ink", lw)
    c.save()
    _star5_path(c, x, y, r, rot)
    c.clip()
    _star5_path(c, x + r * 0.16, y + r * 0.2, r, rot)
    c.rectangle(x - 2 * r, y - 2 * r, 4 * r, 4 * r)
    c.set_fill_rule(1)
    set_color(c, GOLD_DK)
    c.fill()
    c.set_fill_rule(0)
    c.restore()
    _star5_path(c, x, y, r, rot)
    stroke(c, "ink", lw)
    ellipse(c, x - r * 0.2, y - r * 0.3, r * 0.17, r * 0.1, -0.6)
    c.set_source_rgba(1, 1, 1, 0.85)
    c.fill()


def _lapel_star(ctx, x, y, s, t, expr, arms):
    """FOR EFFORT gift (s09) on Malvo's lapel: gold star r 40 + label_tag, at
    villain-local LAPEL, riding the rig's torso (shy incl. breathing, seed 1).
    (x, y, s) = the villain's draw position / scale."""
    shy = (V.resolve_expr(expr)["shy"] + V.resolve_arms(arms, t)[2]
           - math.sin(t * 2 * math.pi / 3.6 + 1.3) * 2.5)
    with saved(ctx, x + LAPEL[0] * s, y + (LAPEL[1] + shy * 0.5) * s, LAPEL_S * s) as cc:
        with saved(cc, 0, 58, 1.0, -0.04) as c2:
            P.label_tag(c2, 0, 0, "FOR EFFORT", color="ai_accent", size=24)
        _gold_star(cc, 0, 0, 40, 0.0, 5.0)


# ===========================================================================
# A  F1 LAIR: the eruption
# ===========================================================================
def _lightning(t, T):
    f = 0.0
    for t0, amp, d in ((T["in"], 1.0, 0.36), (T["in"] + 0.17, 0.7, 0.3)):
        if t0 <= t < t0 + d:
            f = max(f, amp * (1 - (t - t0) / d) ** 1.4)
    return f


def _shot_lair(ctx, t, info, T):
    f = _lightning(t, T)
    dx, dy = shake(t, T["l1"], 0.3, 10)
    t0 = T["in"]
    ctx.save()
    ctx.translate(dx, dy)
    P.lair_bg(ctx, t, flash=f, bolt_seed=2)
    # erupt from behind the desk with squash & stretch
    u = seg(t, t0, t0 + 0.2)
    y = lerp(KNEEL_Y, VY, ease_out_back(u, 2.0))
    st = (math.sin(math.pi * seg(t, t0, t0 + 0.15)) * 0.07
          - math.sin(math.pi * seg(t, t0 + 0.17, t0 + 0.38)) * 0.045)
    sy, sx = 1 + st, 1 - st * 0.6
    expr = _state(t, [(-1, "s10_rage"), (T["frus"], "frustrated", 0.3)])
    arms = _state(t, [(-1, "rest"), (t0 + 0.03, "shrug", 0.2), (T["w_every"] - 0.14, "fist", 0.2)])
    look = _hold(t, [(-1, (0.72, 0.28)), (T["w_how2"], (0.8, 0.22), 0.1),
                     (T["w_every"] - 0.05, (0.1, 0.05), 0.12),
                     (T["frus"] + 0.1, (0.35, -0.55), 0.25)])
    sn_expr = _state(t, [(-1, "shocked"), (t0 + 0.95, "worried", 0.22),
                         (T["calm"] - 0.85, "side_eye", 0.2)])
    sn_look = _hold(t, [(-1, (0.65, -0.45)), (t0 + 0.95, (0.8, -0.35), 0.2),
                        (T["calm"] - 0.85, (1.0, 0.0), 0.15)])
    tongue = True if T["calm"] - 0.35 <= t < T["calm"] - 0.1 else (
        False if t < t0 + 0.9 else None)
    with saved(ctx, VX, y, (sx, sy)) as c:
        draw_villain(c, 0, 0, VS, t, expr=expr, look=look, mouth=info.mouth("villain", t),
                     arms=arms, snake=_snake(sn_expr, sn_look, tongue,
                                              mouth=0.35 if t < t0 + 0.6 else 0.0))
        _lapel_star(c, 0, 0, VS, t, expr, arms)
    P.desk(ctx, VX, VY, 1000)
    P.computer(ctx, 835, 1218, 0.7, view="side", facing=-1, t=t)
    P.keyboard(ctx, VX, VY, 360, t, typing=False)
    # anger mark at his temple (follows the eruption)
    P.emote(ctx, "anger", VX + 168, y - 684 * VS, 0.8, t, T["w_how"] + 0.05)
    P.flash(ctx, 0.2 * f)
    ctx.restore()


# ===========================================================================
# B  F3 AI CU: unbothered, then the dive into its memory
# ===========================================================================
def _ai_cu_params(t, T):
    ex = _state(t, [(-1, AI_NEUT), (T["calm"] + 0.22, AI_WARM, 0.3),
                    (T["w_genius"] - 0.06, AI_AMUSED, 0.25), (T["w_myguy"] - 0.1, AI_WARM, 0.3),
                    (T["l2e"] + 0.1, AI_THINK, 0.3)])
    look = _hold(t, [(-1, (-0.6, 0.0)), (T["w_genius"] - 0.06, (-0.45, -0.05), 0.2),
                     (T["w_myguy"] - 0.1, (-0.65, 0.02), 0.2),
                     (T["l2e"] + 0.02, (0.45, -0.7), 0.25), (T["archive"], (0.0, 0.0), 0.2)])
    # (no "chin" hand: the l02.end -> archive gap is ~0.25 s, so the pose popped in for two
    #  frames as a lone raised finger.  The look-up + think light carry "remembering".)
    hands = _state(t, [(-1, "idle"), (T["w_first"] - 0.12, "shrug", 0.3),
                       (T["w_myguy"] - 0.05, "idle", 0.35)])
    blink = _slow_blink(t, T["calm"] + 0.12)
    nod = 0.35 * math.sin(math.pi * seg(t, T["w_myguy"], T["w_myguy"] + 0.5))
    think = 0.8 * smoothstep(seg(t, T["l2e"] + 0.05, T["l2e"] + 0.35))
    return ex, look, hands, blink, nod, think


def _shot_ai(ctx, t, info, T):
    P.ai_bg(ctx, t)
    u = seg(t, T["archive"], T["dive1"])
    k = ease_in(u)
    s = AI3_S * (4.0 / AI3_S) ** k
    x, y = SCR_CX, SCR_CY + 8 * s
    ex, look, hands, blink, nod, think = _ai_cu_params(t, T)
    if u > 0:
        ex = (ex, _ex("alert", px=0.0, py=0.0), smoothstep(u / 0.4))
    out = draw_ai(ctx, x, y, s, t, expr=ex, look=look, mouth=info.mouth("ai", t), hands=hands,
                  blink=blink, think=think, nod=nod)
    if u > 0.2:
        # the archive opens up inside its screen (its mind) as we dive in
        a = smoothstep(seg(u, 0.2, 0.85))
        (tx_, ty_), (hx_, hy_) = out["top"], out["halo"]
        dxv, dyv = tx_ - hx_, ty_ - hy_
        tilt = math.atan2(-dxv, dyv)
        cxs = tx_ - 227 * math.sin(tilt) * s
        cys = ty_ + 227 * math.cos(tilt) * s
        ctx.save()
        ctx.translate(cxs, cys)
        ctx.rotate(tilt)
        rrect(ctx, -238 * s, -185 * s, 476 * s, 370 * s, 86 * s)
        ctx.restore()
        ctx.save()
        ctx.clip()
        ctx.push_group()
        _archive_bg(ctx)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()


# ===========================================================================
# C  THE ARCHIVE
# ===========================================================================
Z_FAR = 9.0
WALL_X = 640.0
CEIL_Y, FLOOR_Y = -760.0, 1250.0
TIER_B = [-300.0, 200.0, 700.0, 1200.0]       # shelf boards (bottom of each tier)
HAZE = "#1d3d72"


def _pj(X, Y, z):
    return (VPX + X / z, VPY + Y / z)


def _archive_static(c):
    # base
    c.rectangle(-10, -10, W + 20, H + 20)
    _rgba(c, "#091331")
    c.fill()
    # ceiling + floor planes
    poly(c, [_pj(-WALL_X, CEIL_Y, 1), _pj(WALL_X, CEIL_Y, 1), _pj(WALL_X, CEIL_Y, Z_FAR),
             _pj(-WALL_X, CEIL_Y, Z_FAR)])
    _rgba(c, "#060d22")
    c.fill()
    poly(c, [_pj(-WALL_X, FLOOR_Y, 1), _pj(WALL_X, FLOOR_Y, 1), _pj(WALL_X, FLOOR_Y, Z_FAR),
             _pj(-WALL_X, FLOOR_Y, Z_FAR)])
    _rgba(c, "#0b1838")
    c.fill()
    # floor grid
    for X in (-480, -240, 0, 240, 480):
        c.move_to(*_pj(X, FLOOR_Y, 1))
        c.line_to(*_pj(X, FLOOR_Y, Z_FAR))
    for z in (1.15, 1.4, 1.75, 2.2, 2.9, 3.9, 5.4, 7.4):
        c.move_to(*_pj(-WALL_X, FLOOR_Y, z))
        c.line_to(*_pj(WALL_X, FLOOR_Y, z))
    _rgba(c, "ai_rim", 0.1)
    c.set_line_width(2.5)
    c.stroke()
    # ceiling light strip (dashed, recedes to the haze)
    zz = 1.0
    while zz < Z_FAR:
        z1 = zz * 1.16
        a0, a1 = _pj(-26, CEIL_Y, zz), _pj(26, CEIL_Y, zz)
        b0, b1 = _pj(26, CEIL_Y, zz * 1.09), _pj(-26, CEIL_Y, zz * 1.09)
        poly(c, [a0, a1, b0, b1])
        _rgba(c, "ai_eye", 0.35 * (1 - 0.7 * (zz - 1) / (Z_FAR - 1)))
        c.fill()
        zz = z1
    # far wall: a cabinet of drawers (where the Sa-Sn drawer comes from)
    fx0, fy0 = _pj(-WALL_X, CEIL_Y, Z_FAR)
    fx1, fy1 = _pj(WALL_X, FLOOR_Y, Z_FAR)
    c.rectangle(fx0, fy0, fx1 - fx0, fy1 - fy0)
    _rgba(c, "#172c5a")
    c.fill()
    cols, rows = 3, 6
    dw, dh = (fx1 - fx0) / cols, (fy1 - fy0) / rows
    for i in range(cols):
        for j in range(rows):
            rrect(c, fx0 + i * dw + 4, fy0 + j * dh + 4, dw - 8, dh - 8, 3)
            _fs(c, "#22396d", "#0a1430", 2)
            c.rectangle(fx0 + i * dw + dw / 2 - 9, fy0 + j * dh + 9, 18, 7)
            _rgba(c, "#e8dcb8", 0.7)
            c.fill()
    # walls: spines, boards and uprights, far to near
    quads = []
    for sgn in (-1, 1):
        X = sgn * WALL_X
        # wall backing
        quads.append((Z_FAR + 1, "wall", [_pj(X, CEIL_Y, 1.0), _pj(X, CEIL_Y, Z_FAR),
                                         _pj(X, FLOOR_Y, Z_FAR), _pj(X, FLOOR_Y, 1.0)], None))
        for ti, yb in enumerate(TIER_B):
            z = 1.0
            i = 0
            while z < Z_FAR:
                z1 = z * (1.03 + 0.022 * hash01(i, 11 + ti * 7 + (sgn > 0) * 3))
                top = yb - 380 - 36 * hash01(i, 21 + ti)
                col = "#e8c76a" if i % 2 == 0 else "#d4b25a"
                if hash01(i, 31 + ti) < 0.1:
                    col = "#c39a45"
                elif hash01(i, 41 + ti) < 0.08:
                    col = "#f1dc96"
                quads.append((z, col, [_pj(X, top, z), _pj(X, top, z1), _pj(X, yb, z1),
                                       _pj(X, yb, z)], (ti, i)))
                if hash01(i, 51 + ti + (sgn > 0) * 5) < 0.3:       # tiny tab
                    tc = ["#f6ecd6", "#ff8fb8", "#5ee7ff", "#ffb020"][int(hash01(i, 61) * 4)]
                    zm = z + (z1 - z) * 0.2
                    zn = z + (z1 - z) * 0.75
                    quads.append((z - 1e-4, tc, [_pj(X, top - 30, zm), _pj(X, top - 30, zn),
                                                 _pj(X, top, zn), _pj(X, top, zm)], None))
                z = z1
                i += 1
            # board
            quads.append((0.999, "board", [_pj(X, yb, 1.0), _pj(X, yb, Z_FAR),
                                           _pj(X, yb + 34, Z_FAR), _pj(X, yb + 34, 1.0)], None))
        for zu in (1.35, 1.95, 2.8, 4.0, 5.8):
            z1 = zu * 1.045
            quads.append((zu - 2e-4, "upright", [_pj(X, CEIL_Y, zu), _pj(X, CEIL_Y, z1),
                                                 _pj(X, FLOOR_Y, z1), _pj(X, FLOOR_Y, zu)], None))
    quads.sort(key=lambda q: -q[0])
    for z, col, pts, tag in quads:
        fog = clamp((z - 1.0) / (Z_FAR - 1.0)) ** 0.65
        if col == "wall":
            poly(c, pts)
            _rgba(c, "#0e1a3c")
            c.fill()
            continue
        if col == "board":
            poly(c, pts)
            _rgba(c, "#2a3f73")
            c.fill()
            c.move_to(*pts[0])
            c.line_to(*pts[1])
            _rgba(c, "ai_rim", 0.45)
            c.set_line_width(3)
            c.stroke()
            continue
        if col == "upright":
            poly(c, pts)
            _rgba(c, "#16264f")
            c.fill_preserve()
            _rgba(c, "ai_rim", 0.25)
            c.set_line_width(2)
            c.stroke()
            continue
        poly(c, pts)
        c.set_source_rgba(*mixc(col, HAZE, 0.25 + 0.7 * fog))
        if z < 2.0:                     # far spines: no outlines (less fine detail)
            c.fill_preserve()
            c.set_source_rgba(*mixc("ink", HAZE, 0.2 + 0.6 * fog))
            c.set_line_width(2.2 / z ** 0.5)
            c.stroke()
        else:
            c.fill()
    # haze at the vanishing point (static gradients, cached)
    c.save()
    c.translate(VPX, VPY + 20)
    c.scale(1.0, 0.42)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 560)
    col = hexc("ai_glow")
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.26)
    g.add_color_stop_rgba(0.45, col[0], col[1], col[2], 0.08)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0.0)
    c.set_source(g)
    c.arc(0, 0, 560, 0, 2 * math.pi)
    c.fill()
    c.restore()
    radial_glow(c, VPX, VPY + 30, 150, "ai_eye", 0.16)
    # gentle top / bottom vignette
    for (y0, y1, a0, a1) in ((0, 260, 0.45, 0.0), (1500, H, 0.0, 0.35)):
        gg = cairo.LinearGradient(0, y0, 0, y1)
        gg.add_color_stop_rgba(0, 0.02, 0.04, 0.1, a0)
        gg.add_color_stop_rgba(1, 0.02, 0.04, 0.1, a1)
        c.rectangle(-10, y0, W + 20, y1 - y0)
        c.set_source(gg)
        c.fill()


def _archive_bg(ctx):
    P._cached_layer(ctx, "s10_archive", _archive_static, rect=(0, 0, W, H), opaque=True)


def _corridor_pulse(ctx, t, t0, dur=1.1):
    """A light ring racing down the corridor toward camera ("countless...")."""
    u = seg(t, t0, t0 + dur)
    if u <= 0 or u >= 1:
        return
    z = Z_FAR * (1.0 / Z_FAR) ** ease_in(u)          # far -> near
    x0, y0 = _pj(-WALL_X, CEIL_Y, z)
    x1, y1 = _pj(WALL_X, FLOOR_Y, z)
    a = math.sin(math.pi * u)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    _rgba(ctx, "ai_glow", 0.22 * a)
    ctx.set_line_width(max(3.0, 22.0 / z))
    ctx.stroke_preserve()
    _rgba(ctx, "ai_eye", 0.55 * a)
    ctx.set_line_width(max(1.5, 6.0 / z))
    ctx.stroke()


# ---------------------------------------------------------------------------
# foreground folders
# ---------------------------------------------------------------------------
_FIT = {}


def _label_size(ctx, s):
    if s not in _FIT:
        fs = 36
        while fs > 18 and text_width(ctx, s, "ui", fs) > 222:
            fs -= 1
        _FIT[s] = fs
    return _FIT[s]


def _push(t, T):
    return 1.0 + 0.08 * ease_in_out(seg(t, T["push0"], T["push1"]))


def _fg_state(i, t, T):
    """World (x, y, s, rot) of foreground folder i, or None if not visible."""
    lab, bx, by, bs, br, side = FG[i]
    t_in = T["fg0"] + 0.11 * i
    if t < t_in:
        return None
    k = ease_out(seg(t, t_in, t_in + 0.85))
    pf = 1.0 + (_push(t, T) - 1.0) * 1.5
    x = VPX + (bx - VPX) * pf
    y = VPY + (by - VPY) * pf
    s = bs * pf
    rot = br
    off = (1 - k)
    if side == 2:
        x, y = lerp(VPX, x, k), lerp(VPY + 40, y, k)
        s *= 0.12 + 0.88 * k
        rot += 0.3 * off
    else:
        x += side * 560 * off
        rot += side * 0.35 * off
    ko = ease_in(seg(t, T["folder"], T["folder"] + 0.36))
    if ko > 0:
        so = -1 if side == 2 else side
        x += so * 650 * ko
        rot += so * 0.25 * ko
    if ko >= 1:
        return None
    return x, y, s, rot


def _draw_fg_folder(ctx, i, x, y, s, rot):
    lab = FG[i][0]
    col = "#e8c76a" if i % 3 else "#dfbd5e"
    P.folder(ctx, x, y, s, label="", color=col, stamp_txt="TRIED", rot=rot)
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -124, -82, 248, 50, 9)
        _fs(c, "#fbf6e6", "ink", 3.5)
        text(c, lab, 0, -57 + _label_size(c, lab) * 0.36, _label_size(c, lab), "ink", "ui")


# ---------------------------------------------------------------------------
# "very smart people" (prop bible 6.15)
# ---------------------------------------------------------------------------
SILC = "#1d2b4f"


def _sil(c, w=3.2):
    _rgba(c, SILC)
    c.fill_preserve()
    _rgba(c, "ai_rim", 0.9)
    c.set_line_width(w)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke()


def _station(ctx, x, y, s, kind, t, t_pop, t_stamp, t_out, idx):
    k = pop(t, t_pop, 0.32)
    if k <= 0.01:
        return
    ko = ease_in(seg(t, t_out, t_out + 0.3))
    if ko >= 1:
        return
    slump = smoothstep(seg(t, t_stamp + 0.14, t_stamp + 0.42))
    typing = t < t_stamp + 0.11
    fr = (int(t * 12) + idx) % 2            # 2-frame typing bob
    bob = (fr * 2 - 1) * 4 if typing else 0
    sc = s * k * (1 - 0.45 * ko)
    with saved(ctx, lerp(x, VPX, 0.35 * ko), lerp(y, VPY, 0.35 * ko), sc,
               alpha_=1 - ko) as c:
        hy = -150 + 15 * slump
        tilt = 0.2 * slump * (1 if idx % 2 == 0 else -1)
        # --- person (behind the desk) ---
        if kind == "hoodie":
            c.save()
            c.translate(0, hy)
            c.rotate(tilt)
            smooth_path(c, [(0, -56), (40, -40), (50, 0), (42, 40), (0, 52), (-42, 40),
                            (-50, 0), (-40, -40)], closed=True)
            _sil(c)
            c.restore()
        # body (shoulders)
        smooth_path(c, [(-74, 4), (-70, -60), (-50, -100 + 3 * slump), (-18, -112 + 5 * slump),
                        (18, -112 + 5 * slump), (50, -100 + 3 * slump), (70, -60), (74, 4)],
                    closed=True)
        _sil(c)
        if kind == "labcoat":
            for sx in (-1, 1):
                c.move_to(sx * 16, -110 + 5 * slump)
                c.line_to(sx * 30, -60)
                c.line_to(sx * 8, -20)
            _rgba(c, "ai_rim", 0.8)
            c.set_line_width(3)
            c.stroke()
            for j, pc in enumerate(("danger", "ai_accent", "safe")):
                c.move_to(-48 + j * 7, -64)
                c.line_to(-48 + j * 7, -78)
                _rgba(c, pc)
                c.set_line_width(4)
                c.stroke()
        if kind == "hoodie":
            for sx in (-1, 1):
                c.move_to(sx * 10, -104)
                c.line_to(sx * 13, -62)
                _rgba(c, "ai_rim", 0.8)
                c.set_line_width(3)
                c.stroke()
                circle(c, sx * 13, -60, 4)
                _rgba(c, "ai_rim", 0.9)
                c.fill()
        # arms: elbows out, hands down to the keys (2-frame bob)
        for sx, b in ((-1, bob), (1, -bob)):
            if kind == "prof" and sx > 0:
                continue
            c.move_to(sx * 60, -82)
            c.curve_to(sx * 92, -60, sx * 90, -30 + b, sx * 62, -24 + b)
            _rgba(c, "ai_rim", 0.9)
            c.set_line_width(25)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.stroke_preserve()
            _rgba(c, SILC)
            c.set_line_width(19)
            c.stroke()
        # head
        c.save()
        c.translate(0, hy)
        c.rotate(tilt)
        if kind == "labcoat":                 # wild scientist hair
            poly(c, [(-34, -8), (-44, -30), (-26, -28), (-30, -50), (-10, -36), (-2, -58),
                     (12, -38), (30, -52), (26, -28), (44, -32), (34, -6)])
            _sil(c)
        circle(c, 0, 0, 33)
        _sil(c)
        # screen light on the lower face
        ellipse(c, 0, 14, 22, 12)
        _rgba(c, "#2f548f", 0.75)
        c.fill()
        if kind == "hoodie":
            c.arc(0, 0, 37, math.pi * 1.08, math.pi * 1.92)
            _rgba(c, "ai_rim", 0.8)
            c.set_line_width(3)
            c.stroke()
        if kind == "glasses":
            for sx in (-1, 1):
                circle(c, sx * 14, 2, 11)
                _rgba(c, "#bff6ff", 0.85)
                c.fill_preserve()
                _rgba(c, "ink")
                c.set_line_width(3)
                c.stroke()
                c.move_to(sx * 14 - 5, -2)
                c.line_to(sx * 14 + 1, -6)
                _rgba(c, "white")
                c.set_line_width(3)
                c.stroke()
            c.move_to(-3, 2)
            c.line_to(3, 2)
            _rgba(c, "ink")
            c.set_line_width(3)
            c.stroke()
        if kind == "prof":                    # mortarboard + tassel
            poly(c, [(-50, -30), (0, -46), (50, -30), (0, -14)])
            _sil(c)
            rrect(c, -22, -30, 44, 18, 4)
            _sil(c)
            c.move_to(36, -30)
            c.line_to(44, 0)
            _rgba(c, "ai_accent")
            c.set_line_width(4)
            c.stroke()
            circle(c, 44, 2, 5)
            _rgba(c, "ai_accent")
            c.fill()
        c.restore()
        if kind == "prof":                    # pointer arm
            c.move_to(60, -82)
            c.curve_to(96, -96, 104, -130, 98, -158)
            _rgba(c, "ai_rim", 0.9)
            c.set_line_width(25)
            c.stroke_preserve()
            _rgba(c, SILC)
            c.set_line_width(19)
            c.stroke()
            wag = 0.06 * math.sin(t * 7.0) if typing else 0.0
            with saved(c, 98, -160, 1.0, 0.5 + wag) as cc:
                cc.move_to(0, 0)
                cc.line_to(0, -96)
                _rgba(cc, "#c8a165")
                cc.set_line_width(6)
                cc.stroke()
                circle(cc, 0, -98, 6)
                _rgba(cc, "white")
                cc.fill()
        # --- desk gear ---
        if kind == "glasses":
            for mx, my, mw, mh, sk in ((-108, -64, 84, 62, 0.18), (108, -64, 84, 62, -0.18),
                                        (0, -58, 104, 62, 0.0)):
                with saved(c, mx, my) as cc:
                    cc.transform(cairo.Matrix(1, sk, 0, 1, 0, 0))
                    rrect(cc, -mw / 2, -mh / 2, mw, mh, 7)
                    _fs(cc, "#2b3f6e", "ink", 4)
                    cc.move_to(-mw / 2 + 8, -mh / 2 + 3)
                    cc.line_to(mw / 2 - 8, -mh / 2 + 3)
                    _rgba(cc, "ai_rim", 0.8)
                    cc.set_line_width(3)
                    cc.stroke()
                rrect(c, mx - 6, my + 28, 12, 16, 2)
                _fs(c, "#2b3f6e", "ink", 3)
        else:
            rrect(c, -58, -78, 116, 72, 9)            # laptop lid (back)
            _fs(c, "#2b3f6e", "ink", 4)
            c.move_to(-48, -75)
            c.line_to(48, -75)
            _rgba(c, "ai_rim", 0.8)
            c.set_line_width(3)
            c.stroke()
            circle(c, 0, -42, 7)
            _rgba(c, "ai_eye", 0.8)
            c.fill()
        # desk top + front panel
        rrect(c, -126, -8, 252, 16, 6)
        _fs(c, "#2a3f73", "ink", 4)
        rrect(c, -114, 8, 228, 64, 9)
        _fs(c, "#152955", "ink", 4)
        c.move_to(-104, 13)
        c.line_to(104, 13)
        _rgba(c, "ai_rim", 0.35)
        c.set_line_width(3)
        c.stroke()


def _station_stamp(ctx, x, y, s, t, t_stamp, t_out, idx):
    """NICE TRY stamp on a desk front (world space; drawn after the foreground folders
    so the slam is never cut by a folder)."""
    if t >= t_stamp:
        P.stamp(ctx, x, y + 40 * s, "NICE TRY", t, t_stamp, color="warn", size=0.31,
                rot=-0.1 + 0.07 * (idx % 2), t_out=t_out)


# ---------------------------------------------------------------------------
# townsfolk + brick ring + strings
# ---------------------------------------------------------------------------
FOLK = [(-80, 64, "#9fd8ff", "#f1c7a0", 0.0), (0, 40, "#ffb3c7", "#8d5a3b", 0.37),
        (80, 64, "#bff0b0", "#c68a5e", 0.71)]
FOLK_S = 0.7


def _folk(ctx, x, y, s, body, skin, t, ph, happy, wave=0.0, lookx=0.0):
    """Townsperson (bible 6.3). (x, y) = feet. Head r46, pear body 90x120."""
    hop = -6.0 if (happy > 0.5 and ((t * 2 + ph) % 1.0) < 0.5) else 0.0
    with saved(ctx, x, y + hop, s) as c:
        body_pts = [(0, -120), (-28, -114), (-42, -82), (-46, -40), (-38, -8), (0, 0),
                    (38, -8), (46, -40), (42, -82), (28, -114)]
        # waving arm (behind the body)
        if wave > 0.01:
            a = -2.3 + 0.45 * math.sin(t * 2 * math.pi * 2.2)
            c.move_to(30, -92)
            c.line_to(30 + math.cos(a) * 52 * wave, -92 + math.sin(a) * 52)
            _rgba(c, "ink")
            c.set_line_width(20)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.stroke_preserve()
            _rgba(c, body)
            c.set_line_width(12)
            c.stroke()
            circle(c, 30 + math.cos(a) * 52 * wave, -92 + math.sin(a) * 52, 11)
            _fs(c, skin, "ink", 4)
        smooth_path(c, body_pts, closed=True)
        _fs(c, body, "ink", 5)
        ellipse(c, 18, -54, 14, 34)
        _rgba(c, "white", 0.25)
        c.fill()
        hy = -164
        circle(c, 0, hy, 46)
        _fs(c, skin, "ink", 5)
        ex = lookx * 6
        if happy > 0.5:
            for sx in (-1, 1):
                c.move_to(sx * 17 - 9 + ex, hy - 2)
                c.curve_to(sx * 17 - 4 + ex, hy - 12, sx * 17 + 4 + ex, hy - 12,
                           sx * 17 + 9 + ex, hy - 2)
                _rgba(c, "ink")
                c.set_line_width(5)
                c.stroke()
            for sx in (-1, 1):
                ellipse(c, sx * 28, hy + 12, 9, 5)
                _rgba(c, "#ff7a9a", 0.55)
                c.fill()
            c.move_to(-14, hy + 16)
            c.curve_to(-8, hy + 30, 8, hy + 30, 14, hy + 16)
            c.close_path()
            _fs(c, "#7a2b3b", "ink", 4)
        else:
            for sx in (-1, 1):
                ellipse(c, sx * 17 + ex, hy - 4, 6, 7)
                _rgba(c, "ink")
                c.fill()
            c.move_to(-11, hy + 18)
            c.curve_to(-5, hy + 25, 5, hy + 25, 11, hy + 18)
            _rgba(c, "ink")
            c.set_line_width(4.5)
            c.stroke()


BRICK_ORDER = [90, 60, 120, 30, 150, 0, 180, -30, 210, -60, 240, -90]


def _brick_pos(j):
    a = math.radians(BRICK_ORDER[j])
    return RC[0] + RING_R * math.cos(a), RC[1] + RING_R * math.sin(a), a


def _fg_final(i):
    """Folder i centre at the converge moment (push finished)."""
    lab, bx, by, bs, br, side = FG[i]
    pf = 1.0 + 0.08 * 1.5
    return VPX + (bx - VPX) * pf, VPY + (by - VPY) * pf


def _nearest_brick(i):
    fx, fy = _fg_final(i)
    a = math.atan2(fy - RC[1], fx - RC[0])
    best, bj = 9, 0
    for j in range(12):
        d = abs(math.atan2(math.sin(math.radians(BRICK_ORDER[j]) - a),
                           math.cos(math.radians(BRICK_ORDER[j]) - a)))
        if d < best:
            best, bj = d, j
    return bj


def _drop(u, drop):
    """Fall + two small bounces (matches props.brick_wall). -> (dy, squash)."""
    uc = 0.62
    if u < uc:
        p = u / uc
        return -drop * (1 - p * p), -0.05 * p
    v = (u - uc) / (1 - uc)
    sq = 0.2 * max(0.0, 1 - v / 0.22) + 0.06 * max(0.0, 1 - abs(v - 0.6) / 0.12)
    if v < 0.6:
        q = v / 0.6
        return -drop * 0.06 * 4 * q * (1 - q), sq
    q = (v - 0.6) / 0.4
    return -drop * 0.015 * 4 * q * (1 - q), sq


def _ring_bricks(ctx, t, T):
    flash_by = {}
    for i in range(len(FG)):
        h = T["hit"][i]
        if h <= t < h + 0.35:
            j = _nearest_brick(i)
            flash_by[j] = max(flash_by.get(j, 0.0), 1 - (t - h) / 0.35)
    for j in range(12):
        t0 = T["brick_t"][j]
        if t < t0:
            continue
        u = clamp((t - t0) / 0.42)
        dy, sq = _drop(u, 300)
        bx, by, a = _brick_pos(j)
        with saved(ctx, bx, by + dy) as c:
            c.scale(1 + sq * 0.6, 1 - sq)
            c.rotate(a + math.pi / 2)
            bw, bh = 70, 36
            rrect(c, -bw / 2, -bh / 2, bw, bh, 7)
            col = mixc("brick", "safe", 0.55 * flash_by.get(j, 0.0))
            c.set_source_rgba(*col)
            c.fill()
            c.save()
            rrect(c, -bw / 2, -bh / 2, bw, bh, 7)
            c.clip()
            c.rectangle(-bw / 2, bh / 2 - bh * 0.26, bw, bh * 0.3)
            _rgba(c, "brick_dk", 0.75)
            c.fill()
            c.move_to(-bw / 2 + 9, -bh / 2 + 6)
            c.line_to(bw / 2 - 12, -bh / 2 + 6)
            _rgba(c, "#e28a6c", 0.85)
            c.set_line_width(4)
            c.stroke()
            c.restore()
            rrect(c, -bw / 2, -bh / 2, bw, bh, 7)
            _fs(c, None, "ink", 4.5)


def _string_geom(i):
    fx, fy = _fg_final(i)
    fs = FG[i][3] * (1.0 + 0.08 * 1.5)
    dx, dy = RC[0] - fx, RC[1] - fy
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    pin = (fx + ux * 92 * fs, fy + uy * 70 * fs)
    stop = (RC[0] - ux * 228, RC[1] - uy * 228)
    tip = (RC[0] - ux * (RING_R + 24), RC[1] - uy * (RING_R + 24))
    return pin, stop, tip, (ux, uy)


def _strings(ctx, t, T):
    """Red corkboard strings from every folder toward the people; they strike
    the brick ring and burst into soft green sparks."""
    for i in range(len(FG)):
        s0 = T["str0"] + 0.03 * i
        hit = T["hit"][i]
        if t < s0 or t > hit + 0.6:
            continue
        pin, stop, tip, (ux, uy) = _string_geom(i)
        ko = ease_in(seg(t, T["folder"], T["folder"] + 0.2))
        a = (1.0 - seg(t, hit, hit + 0.22)) * (1 - ko)
        # pushpin
        pk = pop(t, s0 - 0.06, 0.2)
        if a > 0.01 and pk > 0.01:
            circle(ctx, pin[0], pin[1], 11 * pk)
            _fs(ctx, "#e8364f", "ink", 3.5, a)
            circle(ctx, pin[0] - 3, pin[1] - 3, 3.5 * pk)
            _rgba(ctx, "white", 0.8 * a)
            ctx.fill()
        if t < hit:
            u1 = ease_out(seg(t, s0, s0 + 0.32))
            u2 = ease_in(seg(t, hit - 0.1, hit))
            end = (lerp(pin[0], stop[0], u1), lerp(pin[1], stop[1], u1))
            end = (lerp(end[0], tip[0], u2), lerp(end[1], tip[1], u2))
        else:
            end = tip
        if a > 0.01:
            L = math.hypot(end[0] - pin[0], end[1] - pin[1])
            sag = min(26.0, 0.12 * L)
            mid = ((pin[0] + end[0]) / 2, (pin[1] + end[1]) / 2 + sag)
            ctx.move_to(*pin)
            ctx.curve_to(mid[0], mid[1], mid[0], mid[1], end[0], end[1])
            _rgba(ctx, "ink", 0.6 * a)
            ctx.set_line_width(10)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke_preserve()
            _rgba(ctx, "#ff3b5c", a)
            ctx.set_line_width(5.5)
            ctx.stroke()
            if t < hit:
                circle(ctx, end[0], end[1], 9)
                _fs(ctx, "#ff8a9a", "ink", 3)
        # green sparks where it hit the wall
        if hit <= t < hit + 0.5:
            v = (t - hit) / 0.5
            for k in range(3):
                ang = math.atan2(-uy, -ux) + (k - 1) * 0.75
                d = 16 + 50 * ease_out(v)
                _star4(ctx, tip[0] + math.cos(ang) * d, tip[1] + math.sin(ang) * d,
                       17 * (1 - v) + 3, rot=v * 2)
                _rgba(ctx, "safe" if k != 1 else "#c8ffd9", 1 - v)
                ctx.fill()


def _ring_scene(ctx, t, T):
    cv = T["converge"]
    if t < cv - 0.05:
        return
    kr = ease_in(seg(t, T["folder"], T["folder"] + T["ring_out"]))   # recede for the drawer
    if kr >= 1:
        return
    sc = 1 - 0.7 * kr
    cx = lerp(RC[0], VPX, kr)
    cy = lerp(RC[1], VPY + 40, kr)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(sc, sc)
    ctx.translate(-RC[0], -RC[1])
    if kr > 0:
        ctx.push_group()
    safe_k = smoothstep(seg(t, T["safe"], T["safe"] + 0.4))
    if safe_k > 0:
        radial_glow(ctx, RC[0], RC[1] - 10, 330, "safe", 0.3 * safe_k)
    for n, (ox, oy, body, skin, ph) in enumerate(FOLK):
        tp = T["folk"][n]
        k = pop(t, tp, 0.3)
        if k <= 0.01:
            continue
        happy = 1.0 if t >= T["safe"] + 0.05 * n else 0.0
        wave = smoothstep(seg(t, T["l5"] + 0.2, T["l5"] + 0.5)) if n == 1 else 0.0
        lookx = 0.0 if happy else math.sin((t - tp) * 5 + n * 2.1)
        with saved(ctx, RC[0] + ox, RC[1] + oy, k):
            _folk(ctx, 0, 0, FOLK_S, body, skin, t, ph, happy, wave, lookx)
    _ring_bricks(ctx, t, T)
    if safe_k > 0:
        # slow green shield ring + a few twinkles
        ctx.save()
        ctx.set_dash([20, 24], -t * 30)
        circle(ctx, RC[0], RC[1], RING_R + 48)
        _rgba(ctx, "safe", 0.5 * safe_k)
        ctx.set_line_width(5)
        ctx.stroke()
        ctx.restore()
        P.sparkles(ctx, RC[0], RC[1] - 10, RING_R + 80, t, n=7, seed=4, color="safe",
                   size=0.9)
    if kr > 0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - kr)
    ctx.restore()


# ---------------------------------------------------------------------------
# "E" drawer + EVIL GENIUS folder + the photocopied Big Book
# ---------------------------------------------------------------------------
TABS = [("code words", "#bdbdbd"), ("fiction!", "#d6d6d6"), ("grandma", "#b0b0b0"),
        ("pieces", "#cacaca"), ("no rules", "#a4a4a4")]


def _photocopy_book(ctx, x, y, s):
    """Grey photocopy of THE BIG BOOK OF SNEAKY TRICKS (bible 6.2); bottom-centre."""
    with saved(ctx, x, y, s) as c:
        for i, (lab, col) in enumerate(TABS):
            tw = text_width(c, lab, "round", 20) + 16
            cx_ = -150 + i * 75
            hh = 46 if i % 2 == 0 else 72
            rot = (hash01(i, 21) - 0.5) * 0.12
            with saved(c, cx_, -296, 1.0, rot) as cc:
                rrect(cc, -tw / 2, -hh, tw, hh + 20, 6)
                _fs(cc, col, "#2a2a2a", 3.5)
                text(cc, lab, 0, -hh + 22, 20, "#2a2a2a", "round")
        rrect(c, -210, -300, 420, 300, 16)
        _fs(c, "#5e5e5e", "#1e1e1e", 5)
        rrect(c, -210, -300, 40, 300, 12)
        _rgba(c, "#000000", 0.25)
        c.fill()
        rrect(c, -192, -284, 384, 268, 10)
        _fs(c, None, "#d2d2d2", 6)
        for (cx_, cy_) in ((-176, -268), (176, -268), (-176, -32), (176, -32)):
            circle(c, cx_, cy_, 9)
            _fs(c, "#d2d2d2", "#1e1e1e", 2.5)
        text(c, "THE BIG BOOK OF", 0, -214, 40, "#dcdcdc", "title", outline="#1e1e1e",
             outline_w=7)
        text(c, "SNEAKY TRICKS", 0, -150, 58, "#e6e6e6", "title", outline="#1e1e1e",
             outline_w=9)
        rrect(c, 160, -132, 78, 46, 10)
        _fs(c, "#3c3c3c", "#1e1e1e", 4)
        P._snake_emblem(c, 192, -86, 0.42, col="#d2d2d2", dk="#8c8c8c")
        # toner specks + copier streak (static)
        for i in range(34):
            sx = -200 + 400 * hash01(i, 301)
            sy = -360 + 350 * hash01(i, 302)
            circle(c, sx, sy, 1.5 + 2.5 * hash01(i, 303))
            _rgba(c, "#1e1e1e", 0.45)
            c.fill()
        c.rectangle(118, -370, 7, 370)
        _rgba(c, "#000000", 0.08)
        c.fill()


def _drawer(ctx, cx, cy, s, t, T, part):
    """Archive drawer, (cx, cy) = front-panel centre. part: 'back' (interior) or 'front'."""
    with saved(ctx, cx, cy, s) as c:
        if part == "back":
            poly(c, [(-186, -146), (186, -146), (212, -72), (-212, -72)])
            _fs(c, "#0b1430", "ink", 5)
            # hanging folders inside
            for i in range(7):
                xx = -150 + i * 50
                poly(c, [(xx - 22, -134 + 2 * (i % 2)), (xx + 22, -134 + 2 * (i % 2)),
                         (xx + 25, -84), (xx - 25, -84)])
                _fs(c, "#d4b25a" if i % 2 else "#e8c76a", "ink", 2.5)
                rrect(c, xx - 10, -146 + 2 * (i % 2), 20, 14, 3)
                _fs(c, "#f6ecd6", "ink", 2)
            # side walls
            for sx in (-1, 1):
                poly(c, [(sx * 186, -146), (sx * 212, -72), (sx * 212, -60), (sx * 192, -146)])
                _fs(c, "#22386a", "ink", 3)
            return
        rrect(c, -214, -75, 428, 150, 14)
        _fs(c, "#24386a", "ink", 5)
        c.move_to(-196, -66)
        c.line_to(196, -66)
        _rgba(c, "ai_rim", 0.55)
        c.set_line_width(4)
        c.stroke()
        # brass label holder + card
        rrect(c, -112, -60, 224, 82, 10)
        _fs(c, "#b08a2e", "ink", 4)
        rrect(c, -100, -51, 200, 64, 6)
        _fs(c, "#f6ecd6", "ink", 3)
        text(c, "E", 0, -2, 56, "ink", "round")
        # highlighter swipe on "Alphabetized"
        hk = ease_out(seg(t, T["hl0"], T["hl0"] + 0.28))
        if hk > 0:
            c.save()
            c.set_operator(cairo.OPERATOR_MULTIPLY)
            ww = 84 * hk
            poly(c, [(-42, -44), (-42 + ww, -46), (-42 + ww + 6, -6), (-42, -4)])
            c.set_source_rgba(1.0, 0.9, 0.18, 0.95)
            c.fill()
            c.restore()
        # handle
        rrect(c, -64, 36, 128, 22, 11)
        _fs(c, "#8a93a8", "ink", 4)
        c.move_to(-50, 42)
        c.line_to(50, 42)
        _rgba(c, "white", 0.5)
        c.set_line_width(3)
        c.stroke()


def _case_cover_outside(c):
    rrect(c, 0, -116, CF_W, 246, 10)
    _fs(c, "#e8c76a", "ink", 5)
    c.move_to(18, -100)
    c.line_to(CF_W - 18, -100)
    _rgba(c, "white", 0.45)
    c.set_line_width(4)
    c.stroke()
    with saved(c, CF_W / 2 + 10, 20, 1.25, -0.14) as cc:
        fs = 44
        set_font(cc, "black", fs)
        tw = cc.text_extents("TRIED")[4]
        rrect(cc, -tw / 2 - 16, -fs * 0.7, tw + 32, fs * 1.4, 8)
        _fs(cc, None, "danger", 6, 0.9)
        text(cc, "TRIED", 0, fs * 0.36, fs, hexc("danger", 0.9), "black")


def _case_cover_inside(c):
    rrect(c, 0, -116, CF_W, 246, 10)
    _fs(c, "#f3dc9a", "ink", 5)
    text(c, "CASE FILE", CF_W / 2, -70, 36, "ink", "comic")
    # mugshot doodle (bald dome, monocle, curly mustache)
    rrect(c, 34, -46, 120, 140, 6)
    _fs(c, "#fbf6e6", "ink", 3)
    for sx in (-1, 1):
        poly(c, [(94 + sx * 30, -8), (94 + sx * 46, -20), (94 + sx * 40, -2),
                 (94 + sx * 50, 4), (94 + sx * 32, 12)])
        _fs(c, "#d8d8e0", "ink", 3)
    circle(c, 94, 6, 34)
    _fs(c, "#f1c7a0", "ink", 3.5)
    circle(c, 108, 0, 11)
    _fs(c, None, "#b08a2e", 3.5)
    circle(c, 80, 0, 4)
    _rgba(c, "ink")
    c.fill()
    c.move_to(76, 22)
    c.curve_to(86, 16, 102, 16, 112, 22)
    _rgba(c, "ink")
    c.set_line_width(4)
    c.stroke()
    # scribble lines
    for k in range(5):
        y0 = -34 + k * 26
        c.move_to(176, y0)
        for q in range(1, 9):
            c.line_to(176 + q * 18, y0 + (3 if q % 2 else -3))
        _rgba(c, "#8b7a55", 0.7)
        c.set_line_width(3)
        c.stroke()


def _case_folder(ctx, t, T):
    if t < T["rise0"]:
        return
    ur = seg(t, T["rise0"], T["rise1"])
    uo = ease_in_out(seg(t, T["open0"], T["open1"]))
    hx = lerp(DRW[0] - CF_W * CF_SC / 2, CF_HINGE, uo)
    cy = lerp(DRW[1] + 40, CF_Y, ease_out_back(ur, 1.3))
    cy += 4 * math.sin((t - T["open1"]) * 2.1) * smoothstep(seg(t, T["open1"], T["open1"] + 0.5))
    sc = lerp(0.82, 1.0, ease_out(ur)) * CF_SC
    bump = 1 + 0.12 * math.sin(math.pi * seg(t, T["tabbump"], T["tabbump"] + 0.3))
    ctx.save()
    if ur < 1:
        ctx.rectangle(-100, -100, W + 200, DRW[1] + 75 + 100)
        ctx.clip()
    with saved(ctx, hx, cy, sc) as c:
        # shadow
        rrect(c, 10, -118, CF_W, 260, 10)
        _rgba(c, "#000000", 0.3)
        c.fill()
        # back panel + tab
        with saved(c, 228, -130, bump) as cc:
            poly(cc, [(-132, 4), (-118, -54), (118, -54), (132, 4)])
            _fs(cc, "#e3bf62", "ink", 5)
            lab = "EVIL GENIUS"
            fs = 32
            while fs > 18 and text_width(cc, lab, "ui", fs) > 232:
                fs -= 1
            text(cc, lab, 0, -24 + fs * 0.36, fs, "ink", "ui")
        rrect(c, 0, -130, CF_W, 260, 10)
        _fs(c, "#e3bf62", "ink", 5)
        # photocopy sheet (paper-clipped)
        with saved(c, CF_W / 2, 4, 1.0, -0.025) as cc:
            rrect(cc, -152, -116, 304, 234, 4)
            _fs(cc, "#ececec", "#3a3a3a", 3)
            rrect(cc, -146, -110, 292, 222, 3)
            _fs(cc, None, "#9a9a9a", 5, 0.35)
            _photocopy_book(cc, 0, 104, 0.56)
            # paper clip
            cc.move_to(-118, -132)
            cc.line_to(-118, -86)
            cc.curve_to(-118, -76, -102, -76, -102, -86)
            cc.line_to(-102, -124)
            _rgba(cc, "#c7cfdd")
            cc.set_line_width(5)
            cc.stroke()
        # stamp on the photocopy (on "folder.")
        # front cover (swings open around the left edge)
        cth = math.cos(math.pi * uo)
        shade = 0.35 * (1 - abs(cth))
        if cth >= 0:
            c.save()
            c.scale(max(cth, 0.001), 1.0)
            _case_cover_outside(c)
            c.restore()
        else:
            c.save()
            c.translate(cth * CF_W, 0)
            c.scale(-cth, 1.0)
            _case_cover_inside(c)
            c.restore()
        if shade > 0.01:
            c.save()
            c.scale(cth if abs(cth) > 0.001 else 0.001, 1.0)
            rrect(c, 0, -116, CF_W, 246, 10)
            _rgba(c, "#000000", shade)
            c.fill()
            c.restore()
    ctx.restore()
    if t >= T["pstamp"]:
        P.stamp(ctx, hx + (CF_W - 112) * sc, cy + 58 * sc, "TRIED", t, T["pstamp"],
                color="danger", size=0.4, rot=-0.2)


def _drawer_scene(ctx, t, T):
    if t < T["drw0"]:
        return
    u = seg(t, T["drw0"], T["drw1"])
    k = ease_out_back(u, 1.2)
    s = lerp(0.12, 1.0, k)
    x = lerp(VPX, DRW[0], ease_out(u))
    y = lerp(VPY + 40, DRW[1], k)
    _drawer(ctx, x, y, s, t, T, "back")
    _case_folder(ctx, t, T)
    _drawer(ctx, x, y, s, t, T, "front")


# ---------------------------------------------------------------------------
# AI inset
# ---------------------------------------------------------------------------
def _inset(ctx, t, info, T):
    k = pop(t, T["inset_in"], 0.32)
    if k <= 0.01:
        return
    cv = T["converge"]
    ex = _state(t, [(-1, AI_NEUT), (T["l4"] - 0.05, AI_DET, 0.3),
                    (T["w_hide"] + 0.15, AI_WARM, 0.35), (T["folder"] + 0.2, AI_AMUSED, 0.3),
                    (T["w_alpha"] - 0.05, AI_AMUSED_C, 0.15)])
    keys = [(-1, (0.6, -0.55)), (T["w_countless"], (0.3, -0.75), 0.25),
            (T["l4"], (0.55, -0.5), 0.2)]
    for i, ((sx, sy), kind) in enumerate(STATIONS):
        keys.append((T["st_stamp"][i] - 0.12, _aim(*INSET_EYE, sx, sy), 0.1))
    keys += [(cv, _aim(*INSET_EYE, *RC), 0.2), (T["folder"] + 0.1, (0.75, -0.2), 0.2),
             (T["rise1"] - 0.1, _aim(*INSET_EYE, 675, CF_Y), 0.2),
             (T["w_alpha"] - 0.05, (0.0, 0.05), 0.12)]
    look = _hold(t, keys)
    hands = _state(t, [(-1, "idle"), (T["brick0"] - 0.15, "stop", 0.2),
                       (T["l5"] + 0.3, "idle", 0.35), (T["l6"] - 0.1, "present", 0.3)])
    blink = _slow_blink(t, T["l3"] - 0.38) or _slow_blink(t, T["l5"] - 0.42)
    with saved(ctx, INSET[0], INSET[1], k) as c:
        draw_ai(c, 0, 0, INSET[2], t, expr=ex, look=look, mouth=info.mouth("ai", t),
                hands=hands, blink=blink, aura=0.0)


def _shot_archive(ctx, t, info, T):
    p = _push(t, T)
    with saved(ctx, VPX, VPY, p) as c:
        c.translate(-VPX, -VPY)
        _archive_bg(c)
        _corridor_pulse(c, t, T["w_countless"] - 0.15)
    # very smart people (l04)
    for i, ((sx, sy), kind) in enumerate(STATIONS):
        _station(ctx, sx, sy, ST_S, kind, t, T["st_pop"][i], T["st_stamp"][i], T["st_out"], i)
    # the Sa-Sn drawer comes from the far wall: while it travels it is BEHIND the receding
    # ring and the exiting folders; once the case folder rises it moves to the front
    early_drawer = t < T["rise0"]
    if early_drawer:
        _drawer_scene(ctx, t, T)
    # the protected people (converge .. folder)
    _ring_scene(ctx, t, T)
    # foreground folders (parallax)
    for i in range(len(FG)):
        st = _fg_state(i, t, T)
        if st is not None:
            _draw_fg_folder(ctx, i, *st)
    for i, ((sx, sy), kind) in enumerate(STATIONS):
        _station_stamp(ctx, sx, sy, ST_S, t, T["st_stamp"][i], T["st_out"], i)
    _strings(ctx, t, T)
    # Sa-Sn drawer + Sneakworth folder
    if not early_drawer:
        _drawer_scene(ctx, t, T)
    _inset(ctx, t, info, T)


# ===========================================================================
# D  F1 WIDE: "...Alphabetized?"
# ===========================================================================
def _shot_wide(ctx, t, info, T):
    # static hold, then three little snap-zooms on the dun-dun-DUN hits (8% total)
    pz = 1.0
    for k, td in enumerate(T["dun"]):
        pz += (0.022 if k < 2 else 0.036) * ease_out(seg(t, td, td + 0.07))
    fcx, fcy = WX, WY - 518 * WS
    with saved(ctx, fcx, fcy, pz) as c:
        c.translate(-fcx, -fcy)
        P.lair_bg(c, t)
        sink = 12 * ease_in_out(seg(t, T["blank"], T["blank"] + 0.5))
        expr = _state(t, [(-1, "shocked"), (T["blank"], "s10_blank", 0.4)])
        arms = _state(t, [(-1, "rest"), (T["blank"], "slump", 0.45)])
        look = _hold(t, [(-1, (0.0, -0.05)), (T["blank"], (0.0, 0.0), 0.3)])
        blink = _slow_blink(t, T["sblink"], 0.2, 0.16, 0.26)
        sn_expr = _state(t, [(-1, "shocked"), (T["nod0"] - 0.1, "nod", 0.25),
                             (T["nod1"], "unimpressed", 0.25), (T["sting"] + 0.2, "side_eye", 0.2)])
        sn_look = _hold(t, [(-1, (0.6, -0.45)), (T["nod0"] - 0.1, (0.7, -0.3), 0.25),
                            (T["sting"] + 0.2, (1.0, 0.0), 0.15)])
        tongue = True if T["sting"] + 0.6 <= t < T["sting"] + 0.85 else (
            False if t < T["nod0"] else None)
        draw_villain(c, WX, WY + sink, WS, t, expr=expr, look=look,
                     mouth=info.mouth("villain", t), arms=arms, blink=blink,
                     snake=_snake(sn_expr, sn_look, tongue,
                                  mouth=0.3 if t < T["nod0"] - 0.1 else 0.0))
        _lapel_star(c, WX, WY + sink, WS, t, expr, arms)
        P.desk(c, WX, WY, 760)
        P.computer(c, 752, 1222, 0.55, view="side", facing=-1, t=t)
        P.keyboard(c, WX, WY, 300, t, typing=False)


# ===========================================================================
# overlays
# ===========================================================================
ROLL_KEYS = [(0.0, 9.0), (0.3, 1204.0), (0.62, 88031.0), (1.0, 9999999.0)]


def _roll_text(t, T):
    if t < T["roll0"]:
        return "9", -1
    if t >= T["roll1"]:
        return "9,999,999+", -2
    n = max(1, int((T["roll1"] - T["roll0"]) / 0.12))
    step = int((t - T["roll0"]) / 0.12)
    k = clamp(step / n)
    ms = {int(round(0.3 * n)): 1204, int(round(0.62 * n)): 88031}
    if step == 0:
        return "9", 0
    if step in ms:
        return f"{ms[step]:,}", step
    for (a, va), (b, vb) in zip(ROLL_KEYS, ROLL_KEYS[1:]):
        if k <= b:
            u = (k - a) / (b - a)
            v = math.exp(lerp(math.log(va), math.log(vb), u))
            break
    v *= 1 + 0.16 * (hash01(step, 77) - 0.5)
    return f"{min(9999998, max(10, int(v))):,}", step


def _chip(ctx, t, T):
    val, step = _roll_text(t, T)
    txt = f"NICE TRIES: {val}"
    w0 = text_width(ctx, "NICE TRIES: 9", "round", 32) + 32 * 1.1
    w1 = text_width(ctx, txt, "round", 32) + 32 * 1.1
    left = 205 - w0 / 2
    s = 1.0
    if step >= 0:
        s += 0.05 * math.sin(math.pi * clamp(((t - T["roll0"]) % 0.12) / 0.12))
    if t >= T["roll1"]:
        s += 0.24 * math.sin(math.pi * seg(t, T["roll1"], T["roll1"] + 0.3))
    with saved(ctx, left + w1 / 2, CHIP_Y, s) as c:
        P.label_tag(c, 0, 0, txt, color="bubble_ai", size=32, font="round")


def render(ctx, t, info):
    T = _T(info)
    if t < T["calm"]:
        _shot_lair(ctx, t, info, T)
    elif t < T["dive1"]:
        _shot_ai(ctx, t, info, T)
    elif t < T["beat"]:
        _shot_archive(ctx, t, info, T)
    else:
        _shot_wide(ctx, t, info, T)
    _chip(ctx, t, T)
    # 2-frame pale-cyan flash on the cut into the archive
    d = t - T["dive1"]
    if 0 <= d < 2.0 / 24:
        P.flash(ctx, 0.85 if d < 1.0 / 24 else 0.4, "#dff9ff")


def SFX(info):
    T = _T(info)
    out = [
        (T["in"], "thunder", -6),
        (T["in"] + 0.02, "whoosh", -10),
        (T["in"] + 0.15, "snake_hiss", -12),
        (T["archive"], "whoosh", -6),
        (T["archive"] + 0.4, "magic_chime", -10),
        (T["fg0"] + 0.2, "paper", -14),
        (T["roll1"], "pop", -10),
        (T["converge"], "whoosh", -12),
        (T["folk"][0], "pop", -13),
        (T["brick_land"][0], "brick_thud", -6),
        (T["brick_land"][-1], "brick_thud", -7),
        (T["chime"], "magic_chime", -8),
        (T["drw0"], "whoosh", -12),
        (T["open0"] + 0.06, "page_flip", -8),
        (P.stamp_impact(T["pstamp"]), "stamp", -12),
        (T["hl0"], "swoosh_up", -16),
        (T["beat"], "boing", -8),
        (T["sting"], "dun_dun_dun", -6),
    ]
    for k in range(10):
        out.append((T["roll0"] + (T["roll1"] - T["roll0"]) * k / 10.0, "tick", -16))
    for i in range(4):
        out.append((T["st_pop"][i], "key_clack", -16))
        out.append((P.stamp_impact(T["st_stamp"][i]), "stamp", -14))
    return sorted(out, key=lambda e: e[0])
