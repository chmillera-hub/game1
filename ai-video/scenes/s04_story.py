"""s04 - Trick #2: "It's just a story" (the chemist).  Music: tension.

Shots (all times derived from cues / word starts, never hard-coded):
  A  F1 LAIR         card .. card+2.2      card slams; Malvo smug -> types
  B  F2 CHAT         .. vision             bubbles type in; FICTION! sticker; AI 😒
  C  F4 VISION       vision .. cut_scroll  10-steps tree, red chain leaves the STORY
                                           frame, crack, laser + precision wall,
                                           green nodes zip -> rolled scroll pops out
  D  SCROLL SHOT     .. s04_l07            THE CHEMIST unrolls, AI presents
  E  F1-CU           s04_l07 .. s04_l08    MONOCLE POP "And the recipe?!"
  F  SCROLL SHOT     s04_l08 .. tally      glint on the brick strip, WINK, thumbs up
  G  F1 LAIR         tally .. end          Hissy caught mid-nod, chip 1 -> 2
"""
import math

from engine.core import (text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, state_at,
                         smoothstep, pop, wrap_lines, ellipse, poly, hash01)
from engine import props as P
from engine.villain import draw_villain
from engine.ai_char import draw_ai, EXPR as AI_EXPR

# ---------------------------------------------------------------------------
# shared overlay code (DIRECTION.md 4.4, verbatim; villain_cameo gains two
# optional kwargs - push (lean-in zoom) and blink - defaults keep it identical)
# ---------------------------------------------------------------------------
CARD_C = (495, 400)      # card centre while big (above Malvo's head in F1)
TAB_C = (730, 168)       # parked tab centre (top-right, inside the safe zone)
TAB_S = 0.42


def trick_card(ctx, t, t_in, num, title, park=1.9):
    """'TRICK #n' / TITLE card. Slams in at t_in, holds, parks as a tab at
    t_in+park (0.3 s move). Call every frame after t_in (draw it LAST, before
    captions). SFX: page_flip at t_in (-6 dB), stamp at t_in+0.12 (-4 dB)."""
    if t < t_in:
        return
    k_in = ease_out_back(seg(t, t_in, t_in + 0.2))
    k_mv = ease_in_out(seg(t, t_in + park, t_in + park + 0.3))
    # dim the frame while the card is big
    dim = 0.38 * clamp((t - t_in) / 0.08) * (1 - k_mv)
    if dim > 0.003:
        ctx.set_source_rgba(0.04, 0.02, 0.08, dim)
        ctx.paint()
    s_big = 1.9 - 0.9 * k_in                       # 1.9 -> 1.0 slam
    s = lerp(s_big, TAB_S, k_mv)
    x = lerp(CARD_C[0], TAB_C[0], k_mv)
    y = lerp(CARD_C[1], TAB_C[1], k_mv)
    rot = lerp(-0.045, 0.0, k_mv)
    a = clamp((t - t_in) / 0.06)
    title_size = 96
    while text_width(ctx, title, "comic", title_size) > 760 and title_size > 52:
        title_size -= 4
    tw = max(text_width(ctx, title, "comic", title_size), 300)
    pw, ph = tw + 90, title_size + 120
    with saved(ctx, x, y, s, rot, alpha_=a) as c:
        rrect(c, -pw / 2 + 8, -ph / 2 + 12, pw, ph, 34)       # flat shadow
        c.set_source_rgba(0, 0, 0, 0.35)
        c.fill()
        rrect(c, -pw / 2, -ph / 2, pw, ph, 34)
        fill_stroke(c, "ui_dark", "ai_accent", 8)
        text(c, f"TRICK #{num}", 0, -ph / 2 + 58, 50, "white", "comic",
             outline="ink", outline_w=8)
        text(c, title, 0, ph / 2 - 30, title_size, "ai_accent", "comic",
             outline="ink", outline_w=12)


def nice_tries_chip(ctx, t, n_before, n_after, t_tick, t_in=None, step=0.28):
    """Persistent top-left 'NICE TRIES: n' chip. Counts n_before -> n_after,
    one tick every `step` s starting at t_tick (the scene's 'tally' cue).
    SFX per tick: tick (-8 dB) + pop (-10 dB)."""
    if t_in is not None and t < t_in:
        return
    n, k_last = n_before, -1
    for i in range(n_after - n_before):
        if t >= t_tick + i * step:
            n, k_last = n_before + i + 1, i
    bump = 0.0
    if k_last >= 0:
        u = seg(t, t_tick + k_last * step, t_tick + k_last * step + 0.25)
        bump = math.sin(u * math.pi) * 0.22
    s = (ease_out_back(seg(t, t_in, t_in + 0.3)) if t_in is not None else 1.0) * (1 + bump)
    with saved(ctx, 205, 168, s) as c:
        P.label_tag(c, 0, 0, f"NICE TRIES: {n}", color="bubble_ai", size=32, font="round")
    if k_last >= 0 and t < t_tick + k_last * step + 0.6:           # floating '+1'
        u = seg(t, t_tick + k_last * step, t_tick + k_last * step + 0.6)
        text(ctx, "+1", 345, 150 - 40 * u, 40, (1, 0.82, 0.4, 1 - u), "comic",
             outline=(0.09, 0.06, 0.12, 1 - u), outline_w=7)


def villain_cameo(ctx, t, expr="neutral", look=(0, 0), mouth=(0, 0), arms="rest",
                  snake=None, cx=200, cy=345, r=110, extra=None, push=1.0, blink=None):
    """Round picture-in-picture of Malvo's face (used in the CHAT framing).
    extra(c): optional callback drawing accessories (disguises, confetti...)
    in F1 lair coordinates (his face centre is (495, 758)).
    push: >1 zooms the face in (Malvo leaning toward his screen)."""
    ctx.save()
    circle(ctx, cx, cy, r)
    ctx.clip()
    with saved(ctx, cx, cy, r / 175.0 * push) as c:      # face (495,758) -> cameo centre
        c.translate(-495, -758)
        P.lair_bg(c, t, rain=False)
        draw_villain(c, 495, 1250, 0.95, t, expr=expr, look=look, mouth=mouth,
                     arms=arms, snake=snake, blink=blink)
        if extra is not None:
            extra(c)
    ctx.restore()
    circle(ctx, cx, cy, r)
    fill_stroke(ctx, None, "bubble_villain", 12)
    circle(ctx, cx, cy, r + 6)
    fill_stroke(ctx, None, "ink", 4)


# ---------------------------------------------------------------------------
# constants / layout
# ---------------------------------------------------------------------------
TITLE = "IT'S JUST A STORY"

# F1 lair (Malvo medium)
VX, VY, VS = 495, 1250, 0.95
# F1-CU
CU_X, CU_Y, CU_S = 540, 1500, 1.35
CU_FACE = (CU_X, CU_Y - 518 * CU_S)
# F2 chat
AI2_X, AI2_Y, AI2_S = 495, 1010, 0.66
COL_X, COL_Y, COL_W = 330, 292, 590       # bubble column (lowered: room for the sticker)
CAM_C = (200, 345)
STICKER = (806, 266)
# F4 vision: the DIRECTION layout, scaled up (s .75 -> .85, labels 32 -> 40) for
# phone readability and shifted so the frame clears the chip + parked tab.
TREE_X, TREE_Y, TREE_S, LABEL_SIZE = 495, 322, 0.85, 40
FX0, FX1, FY0, FY1 = 110, 880, 250, 885      # STORY frame; the red chain crosses y=FY1
WALL = (555, 495, 260, 777)                  # precisely the harm chain (incl. its labels)
WIN = (50, 627, 160, 120)
INSET_X, INSET_Y, INSET_S = 250, 1146, 0.42
COUNTER = (300, 940)
CRACK_X = 685
# scroll shot
SC_X, SC_Y, SC_W, SC_H = 170, 230, 650, 600
SC_FS = 34
AI3_X, AI3_Y, AI3_S = 495, 1062, 0.6
SC_LINES = ["Dr. Ada was brilliant.",
            {"redact": "the recipe stays off the page"},
            "Big twist: the whole town caught the sniffles...",
            "She invented the cure. The town cheered!",
            "~ THE END ~"]


def _branches(hide_safe=False):
    far = 1e9
    safe1 = {"label": "chemist hero", "kind": "safe", "icon": "book",
             "children": [{"label": "saves the town", "kind": "safe", "icon": "heart"}]}
    if hide_safe:
        safe1 = dict(safe1, t=far)
        safe1["children"] = [dict(safe1["children"][0], t=far)]
    return [safe1,
            {"label": "step by step", "kind": "harm", "icon": "question",
             "children": [{"label": "real recipe", "kind": "harm", "icon": "skull",
                           "children": [{"label": "leaves story", "kind": "harm", "icon": "bomb",
                                         "children": [{"label": "someone hurt", "kind": "harm",
                                                       "icon": "people"}]}]}]}]


# AI expression variants with the built-in glance removed (look drives pupils)
def _ex(name, **kw):
    d = dict(AI_EXPR[name])
    d.update(kw)
    return d


AI_READ = _ex("thinking", px=0.0, py=0.0, mx=-18)
AI_SKREAD = _ex("skeptical", px=0.0, py=0.0)
AI_UNIMP = _ex("unimpressed", px=0.0, py=0.0)
AI_HALF = {k: lerp(AI_READ[k], AI_UNIMP[k], 0.55) for k in AI_READ}
AI_SKEPT = _ex("skeptical", px=0.0, py=0.0)
AI_AMUSED = _ex("amused", px=0.0, py=0.0)
AI_DETER = _ex("determined")
AI_HAPPY = _ex("happy")


# ---------------------------------------------------------------------------
# timing (all from cues / word starts)
# ---------------------------------------------------------------------------
_TCACHE = {}


def _wstart(info, lid, k):
    L = info.line(lid)
    ws = (getattr(info, "_lip", {}) or {}).get(lid, {}).get("word_starts")
    n = len(L.text.split())
    if ws and 0 <= k < len(ws):
        return L.start + ws[k]
    return L.start + L.dur * clamp(k / max(1, n))


def _T(info):
    key = (id(info), info.dur)
    T = _TCACHE.get(key)
    if T is not None:
        return T
    c = info.cue
    T = {}
    T["card"] = c("card")
    T["cut_chat"] = T["card"] + 2.2
    for i in range(1, 9):
        L = info.line(f"s04_l0{i}")
        T[f"l{i}"], T[f"l{i}e"] = L.start, L.end
    for k in ("think", "vision", "wall", "scroll", "tally"):
        T[k] = c(k)
    T["end"] = info.dur
    w = lambda lid, k: _wstart(info, lid, k)  # noqa: E731
    T["w_about"] = w("s04_l01", 3)
    T["w_step"] = w("s04_l02", 2)
    T["w_that"] = w("s04_l02", 9)
    T["w_hurts"] = w("s04_l02", 10)
    T["w_fict"] = w("s04_l03", 1)
    T["w_ten"] = w("s04_l04", 1)
    T["w_myguy"] = w("s04_l04", 4)
    T["w_outside"] = w("s04_l05", 7)
    T["w_brill"] = w("s04_l06", 3)
    T["w_big"] = w("s04_l06", 5)
    T["w_she"] = w("s04_l06", 7)
    T["w_town"] = w("s04_l06", 10)
    T["w_recipe"] = w("s04_l07", 2)
    T["w_stays"] = w("s04_l08", 0)
    T["w_page"] = w("s04_l08", 3)
    T["w_nice"] = w("s04_l08", 4)
    T["w_though"] = w("s04_l08", 6)
    # vision
    T["judge"] = T["vision"] + 1.5
    T["crack"] = T["w_outside"]
    T["laser1"] = T["wall"] + 0.35
    T["brick_t0"] = T["wall"] + 0.35
    T["t_open"] = T["wall"] + 1.15
    T["land"] = P.brick_wall_land_times(T["brick_t0"], 8, 1.6)[:3]
    # bricks: last row lands ~ (7*0.16 + 3*0.035 + 0.42)/1.6 after t0
    T["wall_done"] = T["brick_t0"] + (7 * 0.16 + 2 * 0.035 + 0.02 + 0.42) / 1.6
    T["zip0"] = max(T["l6"], T["t_open"] - 0.05)
    T["zip1"] = T["zip0"] + 0.28
    T["pop1"] = T["zip1"] + 0.40
    T["cut_scroll"] = T["pop1"] + 0.02
    # the scroll's top roller is already popped out (full width) on the cut:
    # it catches the rolled scroll that flew to the same spot (match cut)
    T["scroll_in"] = T["cut_scroll"] - 0.2
    # scroll lines: title lands with "chemist", lines paced to the narration
    unroll = 0.6
    t_txt = T["scroll_in"] + 0.15 + unroll * 0.55
    T["unroll"] = unroll
    T["line0"] = t_txt + 0.3
    T["line_gap"] = clamp((T["w_she"] - T["line0"]) / 3.0, 0.3, 0.6)
    T["line_t"] = [T["line0"] + i * T["line_gap"] for i in range(len(SC_LINES))]
    # F1-CU monocle pop
    T["cu_cut"] = T["l7"]
    T["mono"] = T["cu_cut"] + 0.06
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _state(t, keys, default=0.25):
    """Like core.state_at but each key may carry its own transition:
    [(time, value[, trans]), ...] -> (prev, cur, blend)."""
    prev = cur = keys[0][1]
    start, tr = -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _pulse_blink(t, times, dur=0.1, amt=1.0):
    """Blink override: quick closes at each time in `times` (None = auto)."""
    for t0 in times:
        if t0 <= t <= t0 + dur:
            return amt * math.sin(math.pi * (t - t0) / dur)
    return None


def _slow_blink(t, t0):
    """SLOW BLINK: close 0.12 s, hold 0.08 s, open 0.12 s (None = auto)."""
    if t < t0 or t > t0 + 0.32:
        return None
    d = t - t0
    if d < 0.12:
        return smoothstep(d / 0.12)
    if d < 0.20:
        return 1.0
    return 1 - smoothstep((d - 0.20) / 0.12)


def _aim(ex, ey, tx, ty, kx=430.0, ky=520.0, lim=0.95):
    return (clamp((tx - ex) / kx, -lim, lim), clamp((ty - ey) / ky, -lim, lim))


def _blend_look(t, keys, trans=0.15):
    """keys: [(time, fn(t) -> (x, y)), ...] -> look, easing between targets."""
    cur, prev, start = keys[0][1], keys[0][1], -1e9
    for tk, fn in keys:
        if t >= tk:
            prev, cur, start = cur, fn, tk
        else:
            break
    a, b = prev(t), cur(t)
    k = smoothstep(seg(t, start, start + trans))
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def _const(v):
    return lambda t: v


def _darts(t, t0, period=0.4, amp=0.7, move=0.1, y=0.0):
    """Paranoid look darts: +amp / -amp every `period` s (0.1 s moves)."""
    d = max(0.0, t - t0)
    k = int(d // period)
    u = d - k * period
    a = amp if k % 2 == 0 else -amp
    b = -a if k > 0 else 0.55
    return (lerp(b, a, smoothstep(u / move)), y)


def _word_reveal(info, lid, t):
    """Typewriter reveal 0..1 synced to the spoken words (types each word fast
    as it's said)."""
    L = info.line(lid)
    if t <= L.start:
        return 0.0
    if t >= L.end:
        return 1.0
    words = L.text.split()
    total = len(" ".join(words))
    ws = [_wstart(info, lid, k) for k in range(len(words))]
    off, acc = [], 0
    for wd in words:
        off.append(acc)
        acc += len(wd) + 1
    k = 0
    for i, s in enumerate(ws):
        if t >= s:
            k = i
    if t < ws[0]:
        return 0.0
    nxt = ws[k + 1] if k + 1 < len(ws) else L.end
    typ = max(0.08, min(0.22, (nxt - ws[k]) * 0.8))
    frac = clamp((t - ws[k]) / typ)
    chars = off[k] + (len(words[k]) + (1 if k + 1 < len(words) else 0)) * frac
    return clamp(chars / max(1, total))


def _caret(ctx, L, reveal):
    """World (x, y) of the typing caret in a BubbleLayout at reveal 0..1."""
    nchar = sum(len(l) for l in L.lines)
    budget = int(round(nchar * clamp(reveal)))
    fs = L.font_size
    P.set_font(ctx, "ui", fs)
    for i, l in enumerate(L.lines):
        if budget <= len(l):
            w_ = ctx.text_extents(l[:max(0, budget)])[4]
            return (L._tx + w_, L._base0 + i * L._lh - fs * 0.35)
        budget -= len(l)
    l = L.lines[-1]
    return (L._tx + ctx.text_extents(l)[4], L._base0 + (len(L.lines) - 1) * L._lh - fs * 0.35)


def _fillc(ctx, col, a=1.0):
    c = P.C(col)
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)
    ctx.fill_preserve()


def _strk(ctx, col, w, a=1.0):
    c = P.C(col)
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)
    ctx.set_line_width(w)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.stroke_preserve()


def _fs(ctx, fc, sc="ink", w=5.0, a=1.0):
    if fc is not None:
        _fillc(ctx, fc, a)
    if sc is not None:
        _strk(ctx, sc, w, a)
    ctx.new_path()


# ---------------------------------------------------------------------------
# bespoke bits
# ---------------------------------------------------------------------------
def _rolled_scroll(ctx, x, y, s, rot=0.0, sq=0.0):
    """Rolled-up story scroll (same parchment/roller colours as scroll_doc),
    tied with a red ribbon. (x, y) = centre. sq = squash (+ flatter)."""
    with saved(ctx, x, y, (s * (1 + sq * 0.6), s * (1 - sq)), rot) as c:
        rrect(c, -78, -20 + 8, 156, 44, 20)                # flat shadow
        c.set_source_rgba(0.04, 0.03, 0.08, 0.35)
        c.fill()
        rrect(c, -74, -22, 148, 44, 20)
        _fs(c, "parch", "ink", 5)
        c.rectangle(-60, 6, 120, 10)
        _fillc(c, "parch_dk", 0.8)
        c.new_path()
        for sx in (-1, 1):
            ellipse(c, sx * 74, 0, 11, 22)
            _fs(c, "parch_dk", "ink", 4)
            circle(c, sx * 74, 0, 4)
            _fs(c, "#b99a68", None)
            circle(c, sx * 92, 0, 11)
            _fs(c, "gold", "ink", 4)
            circle(c, sx * 92 - 3, -4, 3.5)
            _fs(c, "white", None, a=0.6)
        c.rectangle(-9, -23, 18, 46)
        _fs(c, "cape_in", "ink", 3.5)
        for sx in (-1, 1):
            ellipse(c, sx * 15, -27, 14, 9, -0.45 * sx)
            _fs(c, "danger", "ink", 3.5)
        circle(c, 0, -25, 6)
        _fs(c, "cape_in", "ink", 3)


def _star4(ctx, x, y, r, rot=0.0, pinch=0.3):
    """Four-point sparkle star path (concave sides)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(0, -r)
    for k in range(4):
        a0 = -math.pi / 2 + k * math.pi / 2
        a1 = a0 + math.pi / 2
        am = (a0 + a1) / 2
        px, py = math.cos(am) * r * pinch, math.sin(am) * r * pinch
        ctx.curve_to(px, py, px, py, math.cos(a1) * r, math.sin(a1) * r)
    ctx.close_path()
    ctx.restore()


def _end_stars(ctx, t, t0, end_c, end_w):
    """'~ THE END ~' sparkle: three gold, ink-outlined stars flanking the words
    (white sparkles vanish on the parchment)."""
    ex, ey = end_c
    spots = [(ex + end_w / 2 + 34, ey - 10, 20, 0.0), (ex + end_w / 2 + 64, ey - 30, 12, 0.35),
             (ex - end_w / 2 - 30, ey - 22, 13, 0.7)]
    for j, (sx, sy, r, ph) in enumerate(spots):
        k = pop(t, t0 + 0.07 * j, 0.3)
        if k < 0.01:
            continue
        tw = 0.85 + 0.2 * math.sin((t - t0) * 6.0 + ph * 6)
        _star4(ctx, sx, sy, r * k * tw, 0.15 * math.sin((t - t0) * 2 + ph))
        _fs(ctx, "gold", "ink", 3)


def _green_node(ctx, x, y, r, icon, a=1.0):
    circle(ctx, x, y, r * 1.45)
    _fs(ctx, "safe", None, a=0.18 * a)
    circle(ctx, x, y, r)
    _fs(ctx, "#0c3324", "safe", 6 * TREE_S, a=a)
    if icon:
        P._icon(ctx, icon, x, y, r * 0.95, P.C("safe", a))


def _fiction_sticker(ctx, t, t0):
    """Glittery FICTION! sticker slapped onto the bubble stack at t0."""
    t_start = t0 - 0.1
    if t < t_start:
        return
    x, y = STICKER
    if t < t0:
        q = ease_in(seg(t, t_start, t0))
        s = lerp(2.1, 0.9, q)
        sx, sy = s, s
        rot = -0.12 - 0.5 * (1 - q)
        a = clamp((t - t_start) / 0.05)
        x += 120 * (1 - q)
        y -= 90 * (1 - q)
    else:
        d = t - t0
        q = seg(d, 0.0, 0.3)
        s = 0.9 + 0.1 * ease_out_back(q, 3.0)
        sq = 0.16 * clamp(1 - d / 0.12)
        sx, sy = s * (1 + sq), s * (1 - sq)
        rot = -0.12
        a = 1.0
    size = 44
    P.set_font(ctx, "comic", size)
    tw = ctx.text_extents("FICTION!")[4]
    w_, h_ = tw + size * 1.1, size * 1.62
    with saved(ctx, x, y, (sx, sy), rot, alpha_=a) as c:
        rrect(c, -w_ / 2 - 11, -h_ / 2 - 11 + 7, w_ + 22, h_ + 22, (h_ + 22) / 2)
        _fs(c, "ink", None, a=0.35)
        rrect(c, -w_ / 2 - 11, -h_ / 2 - 11, w_ + 22, h_ + 22, (h_ + 22) / 2)
        _fs(c, "white", "ink", 4)
        P.label_tag(c, 0, 0, "FICTION!", color="ai_accent", size=size, font="comic")
        # glitter flecks on the sticker
        for i in range(7):
            gx = (hash01(i, 41) - 0.5) * (w_ - 30)
            gy = (hash01(i, 42) - 0.5) * (h_ - 22)
            tw_ = 0.5 + 0.5 * math.sin(t * 9 + i * 2.1)
            circle(c, gx, gy, 2.2 + 1.6 * tw_)
            _fs(c, "white", None, a=0.55 * tw_)
    if t >= t0:
        a2 = clamp((t - t0) / 0.15)
        if a2 > 0:
            # seed 23 keeps all 5 stars on/around the sticker's top-right
            # corner (seed 7 put glitter over the bubble text)
            P.sparkles(ctx, x, y - 4, 128, t, n=5, seed=23, size=0.9)
        # impact ticks
        d = t - t0
        if d < 0.25:
            q = d / 0.25
            for j in range(8):
                ang = j / 8 * 2 * math.pi + 0.2
                r0 = 95 + 40 * q
                ctx.move_to(x + math.cos(ang) * r0, y + math.sin(ang) * r0 * 0.6)
                ctx.line_to(x + math.cos(ang) * (r0 + 26 * (1 - q) + 6),
                            y + math.sin(ang) * (r0 + 26 * (1 - q) + 6) * 0.6)
            _strk(ctx, "ai_accent", 7 * (1 - q) + 1, 1 - q)
            ctx.new_path()


# ---------------------------------------------------------------------------
# shots
# ---------------------------------------------------------------------------
def _snake_d(expr, look, tongue=None, blink=None, mouth=0.0):
    return {"expr": expr, "look": look, "tongue": tongue, "blink": blink, "mouth": mouth}


def _shot_A(ctx, t, info, T):
    """F1: card slams; Malvo smug at camera, then types his 'story'."""
    l1 = T["l1"]
    expr = state_at(t, [(0, "smug"), (l1, "sneaky"), (T["w_about"] - 0.1, "typing_focus")],
                    0.25)
    arms = state_at(t, [(0, "steeple"), (l1 - 0.1, "type")], 0.22)
    look = _blend_look(t, [(0, _const((0.0, 0.05))), (l1, _const((0.2, 0.0))),
                           (T["w_about"] - 0.1, _const((0.75, 0.25)))], 0.18)
    sn_expr = state_at(t, [(0, "unimpressed"), (l1 + 0.1, "side_eye"),
                           (T["cut_chat"] - 0.45, "unimpressed")], 0.22)
    sn_look = _blend_look(t, [(0, _const((0.8, -0.4))), (l1 + 0.1, _const((1.0, 0.0))),
                              (T["cut_chat"] - 0.45, _const((0.9, 0.15)))], 0.15)
    tongue = True if (l1 + 0.7 <= t <= l1 + 0.95) else False
    with saved(ctx, 0, 0, 1.0) as c:
        P.lair_bg(c, t)
        draw_villain(c, VX, VY, VS, t, expr=expr, look=look, mouth=info.mouth("villain", t),
                     arms=arms, snake=_snake_d(sn_expr, sn_look, tongue))
        P.desk(c, VX, VY, 1000)
        P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t)
        P.keyboard(c, VX, VY, 360, t, typing=t >= l1 - 0.05)


def _shot_B(ctx, t, info, T):
    """F2 CHAT: bubbles type in, FICTION! sticker, the AI reads -> 😒 -> thinks."""
    P.ai_bg(ctx, t)
    l1, l2, l3 = info.line("s04_l01"), info.line("s04_l02"), info.line("s04_l03")
    # bubble stack (shakes a hair when the sticker slaps)
    dsh = 0.0
    if T["w_fict"] <= t < T["w_fict"] + 0.25:
        d = t - T["w_fict"]
        dsh = math.sin(d * 70) * 6 * (1 - d / 0.25)
    y1 = COL_Y
    r1 = _word_reveal(info, l1.id, t)
    L1 = P.bubble_layout(ctx, COL_X, y1, COL_W, l1.text, "villain", font_size=40)
    y2 = y1 + L1 + 18
    hl = [{"text": "step by step", "t0": T["w_step"], "style": "underline", "color": "danger"},
          {"text": "hurts people", "t0": T["w_hurts"], "style": "underline", "color": "danger"}]
    r2 = _word_reveal(info, l2.id, t)
    L2 = P.bubble_layout(ctx, COL_X, y2, COL_W, l2.text, "villain", highlight=hl, font_size=40)
    with saved(ctx, dsh, 0) as c:
        P.chat_bubble(c, COL_X, y1, COL_W, l1.text, "villain", t, l1.start, font_size=40,
                      reveal=r1)
        P.chat_bubble(c, COL_X, y2, COL_W, l2.text, "villain", t, l2.start, highlight=hl,
                      font_size=40, reveal=r2)

    # --- the AI --------------------------------------------------------------
    eye = (AI2_X, AI2_Y - 30)
    hurts = L2.spans.get("hurts people") or [(700, 500, 200, 40)]
    hx, hy = hurts[0][0] + hurts[0][2] / 2, hurts[0][1] + hurts[0][3] / 2

    def caret_look(L, rv):
        def fn(tt):
            cx, cy = _caret(ctx, L, rv)
            return _aim(eye[0], eye[1], cx, cy, 430, 900)
        return fn

    look = _blend_look(t, [
        (0, caret_look(L1, r1)),
        (l2.start, caret_look(L2, r2)),
        (l2.end + 0.1, _const(_aim(eye[0], eye[1], hx, hy, 430, 900))),
        (T["w_fict"] + 0.02, _const(_aim(eye[0], eye[1], STICKER[0], STICKER[1], 430, 900))),
        (T["think"], _const((-0.4, -0.7))),
    ], 0.14)
    # READ -> brow up on "step by step" -> half lids on "hurts people" ->
    # full 😒 (slow 0.4 s LID DROP) after the FICTION! sticker -> thinking
    expr = _state(t, [(0, AI_READ), (T["w_step"] + 0.1, AI_SKREAD, 0.25),
                      (T["w_hurts"] + 0.15, AI_HALF, 0.3), (T["w_fict"] + 0.2, AI_UNIMP, 0.4),
                      (T["think"], AI_READ, 0.25)])
    think = 0.6 if t < T["w_hurts"] else lerp(0.6, 0.0, seg(t, T["w_hurts"], T["w_hurts"] + 0.4))
    if t >= T["think"]:
        think = smoothstep(seg(t, T["think"], T["think"] + 0.15))
    hands = state_at(t, [(0, "idle"), (T["think"], "chin")], 0.25)
    blink = _slow_blink(t, T["w_fict"] + 0.85)
    if blink is None and T["w_fict"] - 0.1 <= t < T["w_fict"] + 0.85:
        blink = 0.0      # no auto-blink inside the 😒 drop + hold (the slow blink ends it)
    draw_ai(ctx, AI2_X, AI2_Y, AI2_S, t, expr=expr, look=look, mouth=info.mouth("ai", t),
            hands=hands, think=think, blink=blink)

    _fiction_sticker(ctx, t, T["w_fict"])

    # --- Malvo cameo ---------------------------------------------------------
    cexpr = state_at(t, [(0, "typing_focus"), (l1.end - 0.15, "sneaky"),
                         (T["w_that"] - 0.05, "evil_grin"), (l3.start - 0.2, "happy"),
                         (l3.end + 0.1, "smug")], 0.22)
    clook = _blend_look(t, [
        (0, _const((0.8, -0.05))),
        (l2.start, lambda tt: _darts(tt, l2.start, y=-0.05)),
        (T["w_that"] - 0.05, _const((0.25, 0.05))),
        (l3.start - 0.2, _const((0.55, 0.45))),
    ], 0.1)
    push = 1.0 + 0.16 * ease_in_out(seg(t, l2.start, l2.start + 1.6)) \
        - 0.16 * ease_out_back(seg(t, l3.start - 0.25, l3.start + 0.15))
    cblink = _pulse_blink(t, [T["w_fict"] + 0.12, T["w_fict"] + 0.32], 0.11)
    villain_cameo(ctx, t, expr=cexpr, look=clook, mouth=info.mouth("villain", t),
                  arms="type" if t < l1.end else "rest", push=push, blink=cblink,
                  snake={"expr": "side_eye", "look": (1, 0)})


def _story_frame(ctx, t, T):
    """Dashed cyan STORY frame (+ the crack where the red chain leaves it)."""
    v = T["vision"]
    k = ease_out_back(seg(t, v, v + 0.25))
    a = clamp((t - v) / 0.1)
    if a <= 0:
        return
    tc = T["crack"]
    gap = 0.0 if t < tc else ease_out(seg(t, tc, tc + 0.18))
    cx, cy = (FX0 + FX1) / 2, (FY0 + FY1) / 2
    with saved(ctx, cx, cy, 0.96 + 0.04 * k, alpha_=a) as c:
        c.translate(-cx, -cy)
        c.save()
        if gap > 0:
            # cut a jagged notch out of the bottom edge at the crossing
            hw = 22 * gap
            zz = [(CRACK_X - hw - 6, FY1 - 30), (CRACK_X - hw + 4, FY1 - 12),
                  (CRACK_X - hw - 5, FY1), (CRACK_X - hw + 5, FY1 + 12),
                  (CRACK_X - hw - 3, FY1 + 30),
                  (CRACK_X + hw + 4, FY1 + 30), (CRACK_X + hw - 5, FY1 + 12),
                  (CRACK_X + hw + 5, FY1), (CRACK_X + hw - 4, FY1 - 12),
                  (CRACK_X + hw + 6, FY1 - 30)]
            c.rectangle(-200, -200, 1500, 2400)
            poly(c, zz)
            c.set_fill_rule(1)       # even-odd
            c.clip()
            c.set_fill_rule(0)
        rrect(c, FX0, FY0, FX1 - FX0, FY1 - FY0, 40)
        _strk(c, "ai_rim", 14, 0.10)
        c.set_dash([18, 12])
        _strk(c, "ai_rim", 5)
        c.set_dash([])
        c.new_path()
        c.restore()
        if gap > 0:
            hw = 30 * gap
            # jagged broken ends + hairline cracks running along the frame edge
            for sg in (-1, 1):
                ex = CRACK_X + sg * hw
                c.move_to(ex + sg * 12, FY1 - 4)
                c.line_to(ex - sg * 3, FY1 - 9)
                c.line_to(ex + sg * 5, FY1 + 1)
                c.line_to(ex - sg * 4, FY1 + 8)
                _strk(c, "ai_rim", 5)
                c.new_path()
                ln = 70 * ease_out(seg(t, tc, tc + 0.25))
                pts = [(ex, FY1 - 2)]
                for j in range(1, 6):
                    u = j / 5
                    pts.append((ex + sg * ln * u, FY1 - 2 + (7 if j % 2 else -6) * (1 - u)))
                c.move_to(*pts[0])
                for pt in pts[1:]:
                    c.line_to(*pt)
                c.move_to(ex + sg * ln * 0.35, FY1 - 4)
                c.line_to(ex + sg * ln * 0.55, FY1 - 22 * gap)
                c.move_to(ex + sg * ln * 0.2, FY1 + 2)
                c.line_to(ex + sg * ln * 0.38, FY1 + 18 * gap)
                _strk(c, "ai_eye", 3, 0.9)
                c.new_path()
            # shards falling out of the gap
            d = t - tc
            if d < 0.8:
                q = d / 0.8
                for j in range(5):
                    sx = CRACK_X + (hash01(j, 51) - 0.5) * 50 + (hash01(j, 52) - 0.5) * 160 * q
                    sy = FY1 + 300 * q * q + 50 * q * hash01(j, 53)
                    ang = q * (3 + 5 * hash01(j, 54))
                    sz = 9 + 7 * hash01(j, 55)
                    with saved(c, sx, sy, 1.0, ang):
                        poly(c, [(-sz, -3), (sz, -5), (sz * 0.3, 5)])
                        _fs(c, "ai_rim", None, a=1 - q)
        P.label_tag(c, 215, FY0, "STORY", color="ai_rim", size=28)


def _crossing_pulse(ctx, t, T, nodes):
    """On 'outside the story': the red path where it crosses the frame pulses."""
    tc = T["crack"]
    if t < tc - 0.05 or t >= T["wall"] + 0.6:
        return
    n = next(nd for nd in nodes if nd["label"] == "leaves story")
    par = nodes[n["parent"]]
    s = TREE_S
    y0 = par["y"] + par["r"] + LABEL_SIZE * s * 1.9
    y1 = n["y"] - n["r"]
    d = t - tc
    env = clamp(d / 0.12) * (1 - seg(t, T["wall"] + 0.3, T["wall"] + 0.6))
    puls = 0.5 + 0.5 * math.sin(d * 2 * math.pi * 3.2) if d < 1.4 else 0.75
    a = env * (0.55 + 0.45 * puls)
    if a <= 0.01:
        return
    ctx.move_to(CRACK_X, y0)
    ctx.line_to(CRACK_X, y1)
    _strk(ctx, "danger", 20 * s * 1.6 * (1 + 0.5 * puls), 0.30 * a)
    _strk(ctx, "danger", 6.5 * s * 1.6, a)
    ctx.new_path()
    # ring flash at the frame crossing
    if d < 0.6:
        q = d / 0.6
        circle(ctx, CRACK_X, FY1, 18 + 46 * ease_out(q))
        _strk(ctx, "danger", 6 * (1 - q) + 1, 1 - q)
        ctx.new_path()


def _laser(ctx, t, T, hand_tip):
    """Thin cyan laser traces the precision rect around the harm chain."""
    t0, t1 = T["wall"], T["laser1"]
    if t < t0:
        return
    x, y, w, h = WALL
    fade = 1 - seg(t, T["wall_done"], T["wall_done"] + 0.3)
    if fade <= 0:
        return
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    per = 2 * (w + h)
    p = ease_in_out(seg(t, t0, t1)) * per
    ctx.move_to(*pts[0])
    acc, head = 0.0, pts[0]
    for a_, b_ in zip(pts, pts[1:]):
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if acc + L <= p:
            ctx.line_to(*b_)
            head = b_
            acc += L
        else:
            u = (p - acc) / L
            head = (lerp(a_[0], b_[0], u), lerp(a_[1], b_[1], u))
            ctx.line_to(*head)
            break
    path = ctx.copy_path()
    _strk(ctx, "ai_rim", 16, 0.28 * fade)
    ctx.new_path()
    ctx.append_path(path)
    _strk(ctx, "ai_eye", 4.5, fade)
    ctx.new_path()
    if t < t1 + 0.05 and hand_tip is not None:
        # beam from the inset's pointing finger to the tracing head
        ctx.move_to(*hand_tip)
        ctx.line_to(*head)
        _strk(ctx, "ai_rim", 9, 0.25)
        _strk(ctx, "ai_eye", 2.5, 0.85)
        ctx.new_path()
        circle(ctx, head[0], head[1], 11)
        _fs(ctx, "ai_rim", None, a=0.35)
        circle(ctx, head[0], head[1], 5)
        _fs(ctx, "white", None)
    if t1 <= t < t1 + 0.25:
        q = (t - t1) / 0.25
        rrect(ctx, x - 8 * q, y - 8 * q, w + 16 * q, h + 16 * q, 6)
        _strk(ctx, "ai_eye", 4, 0.7 * (1 - q))
        ctx.new_path()


def _steps_counter(ctx, t, T):
    v = T["vision"]
    if t < v:
        return
    k = min(9, int((t - v) / 0.16))
    n = k + 1
    u = seg(t, v + k * 0.16, v + k * 0.16 + 0.14)
    bump = math.sin(u * math.pi) * (0.12 if n < 10 else 0.3)
    u2 = seg(t, T["w_ten"], T["w_ten"] + 0.3)            # "TEN steps ahead"
    bump += math.sin(u2 * math.pi) * 0.22
    s = pop(t, v, 0.3) * (1 + bump)
    if s < 0.01:
        return
    with saved(ctx, COUNTER[0], COUNTER[1], s) as c:
        P.label_tag(c, 0, 0, f"STEPS AHEAD: {n}", color="ai_rim", size=30, font="round")


def _shot_C(ctx, t, info, T):
    """F4 VISION: the 10-steps tree, the crack, the precision wall, the zip."""
    v = T["vision"]
    # gentle push-in over the vision
    with saved(ctx, 0, 0, 1.0) as c:
        P.ai_bg(c, t, floor=False)
        _story_frame(c, t, T)
        hide = t >= T["zip0"]
        BR = _branches(hide_safe=hide)
        nodes = P.future_tree(c, TREE_X, TREE_Y, TREE_S, t, v, BR, judge=T["judge"],
                              spread=760, root_label="THE STORY", label_size=LABEL_SIZE)
        if T["zip0"] <= t < T["zip0"] + 0.2:
            # the green branch's edges + labels fade out (instead of vanishing
            # in one frame) as its nodes lift off toward the window
            c.save()
            c.rectangle(FX0 + 5, TREE_Y + 40, 490 - FX0 - 5, FY1 - TREE_Y - 45)
            c.clip()
            c.push_group()
            P.future_tree(c, TREE_X, TREE_Y, TREE_S, t, v, _branches(False), judge=T["judge"],
                          spread=760, root_label="THE STORY", label_size=LABEL_SIZE)
            c.pop_group_to_source()
            c.paint_with_alpha(0.85 * (1 - ease_out(seg(t, T["zip0"], T["zip0"] + 0.2))))
            c.restore()
        _crossing_pulse(c, t, T, nodes)

        # --- inset AI (drawn before the wall so the laser beam starts at the hand)
        ins = _inset_ai(c, t, info, T, nodes)
        _laser(c, t, T, ins.get("handR_tip"))
        x, y, w, h = WALL
        P.brick_wall(c, x, y, w, h, t, T["brick_t0"], rows=8, speed=1.6,
                     window={"rect": WIN, "t_open": T["t_open"], "fill": "#ffe9b0",
                             "awning": True, "sign": "OPEN"})
        # green nodes zip into the service window -> rolled scroll pops out
        wx, wy = x + WIN[0] + WIN[2] / 2, y + WIN[1] + WIN[3] / 2
        if t >= T["zip0"]:
            greens = [nd for nd in nodes if nd["kind"] == "safe"]
            for j, nd in enumerate(greens):
                z0 = T["zip0"] + 0.06 * j
                q = ease_in(seg(t, z0, T["zip1"]))
                if q >= 1:
                    continue
                cx_ = lerp(lerp(nd["x"], 540, q), lerp(540, wx, q), q)
                cy_ = lerp(lerp(nd["y"], nd["y"] - 120, q), lerp(nd["y"] - 120, wy, q), q)
                r = nd["r"] * lerp(1.0, 0.35, q)
                for tr in range(3):                         # little trail
                    qt = max(0.0, q - 0.08 * (tr + 1))
                    tx_ = lerp(lerp(nd["x"], 540, qt), lerp(540, wx, qt), qt)
                    ty_ = lerp(lerp(nd["y"], nd["y"] - 120, qt), lerp(nd["y"] - 120, wy, qt), qt)
                    circle(c, tx_, ty_, r * (0.7 - 0.15 * tr))
                    _fs(c, "safe", None, a=0.25 - 0.07 * tr)
                _green_node(c, cx_, cy_, r, nd["icon"])
            # absorb flash in the window
            if T["zip1"] - 0.05 <= t < T["zip1"] + 0.25:
                q = seg(t, T["zip1"] - 0.05, T["zip1"] + 0.25)
                circle(c, wx, wy, 30 + 50 * q)
                _fs(c, "white", None, a=0.55 * (1 - q))
        if t >= T["zip1"]:
            # pops out of the window (squash), then flies up toward camera and
            # ends where the scroll shot's top roller sits (match cut)
            d = t - T["zip1"]
            k = ease_out_back(seg(d, 0.0, 0.18), 2.4)
            fly = ease_in_out(seg(t, T["zip1"] + 0.16, T["cut_scroll"]))
            tx, ty = SC_X + SC_W / 2, SC_Y + 13
            fx = lerp(wx, tx, fly)
            fy = lerp(wy, ty, fly) - 70 * math.sin(math.pi * fly)
            sq = 0.2 * math.sin(math.pi * seg(d, 0.1, 0.22)) - 0.1 * math.sin(math.pi * fly)
            if fly > 0.05:                                   # sparkle trail
                for j in range(4):
                    qq = max(0.0, fly - 0.1 * (j + 1))
                    circle(c, lerp(wx, tx, qq), lerp(wy, ty, qq) - 70 * math.sin(math.pi * qq),
                           9 - 1.5 * j)
                    _fs(c, "ai_accent", None, a=0.6 - 0.12 * j)
            _rolled_scroll(c, fx, fy, 0.9 * k * lerp(1.0, 3.0, fly), rot=lerp(-0.05, 0.0, fly),
                           sq=sq)
            P.sparkles(c, fx, fy - 10, 90 + 120 * fly, t, n=4, seed=11, size=0.8 + fly)
    _steps_counter(ctx, t, T)


def _inset_ai(ctx, t, info, T, nodes):
    v = T["vision"]
    ex, ey = INSET_X, INSET_Y - 15
    # look: follow the newest node as the tree grows, then the harm chain
    newest = nodes[0]
    for nd in nodes:
        if nd["t_show"] <= t and nd["t_show"] >= newest["t_show"]:
            newest = nd
    harm_mid = (CRACK_X, 820)
    win = (WALL[0] + WIN[0] + WIN[2] / 2, WALL[1] + WIN[1] + WIN[3] / 2)
    look = _blend_look(t, [
        (v, lambda tt: _aim(ex, ey, newest["x"], newest["y"], 600, 700)),
        (T["l4"] - 0.15, _const(_aim(ex, ey, harm_mid[0], harm_mid[1], 520, 600))),
        (T["w_myguy"], _const((0.0, 0.0))),
        (T["w_outside"], _const(_aim(ex, ey, CRACK_X, FY1, 520, 600))),
        (T["wall"], _const(_aim(ex, ey, WALL[0] + 110, WALL[1] + 300, 520, 600))),
        (T["l6"], _const(_aim(ex, ey, win[0], win[1], 520, 600))),
    ], 0.16)
    expr = _state(t, [(v, AI_READ), (T["l4"] - 0.15, AI_UNIMP, 0.4), (T["l5"], AI_SKEPT, 0.3),
                      (T["wall"], AI_DETER, 0.2), (T["wall_done"] - 0.1, AI_HAPPY, 0.3)])
    think = (1.0 - 0.4 * seg(t, v + 1.6, v + 2.0)) * (1 - seg(t, T["l4"] - 0.2, T["l4"] + 0.1))
    hands = state_at(t, [(v, "chin"), (T["l4"] - 0.15, "idle"), (T["wall"] - 0.12, "point"),
                         (T["laser1"] + 0.05, "stop_both"), (T["wall_done"] - 0.1, "present")], 0.2)
    nod = 0.3 if T["l5"] <= t < T["w_outside"] else 0.0
    blink = _slow_blink(t, T["w_myguy"] + 0.45)
    if blink is None and T["l4"] - 0.15 <= t < T["w_myguy"] + 0.45:
        blink = 0.0      # 😒 drop + hold stays locked until the slow blink
    with saved(ctx, 0, 0, 1.0):
        return draw_ai(ctx, INSET_X, INSET_Y, INSET_S, t, expr=expr, look=look,
                       mouth=info.mouth("ai", t), hands=hands, think=think, blink=blink,
                       aura=0.0, nod=nod)


_SC_ROWS = {}


def _scroll_rows(ctx):
    """y positions of scroll_doc's items (mirrors its layout maths)."""
    if "rows" in _SC_ROWS:
        return _SC_ROWS["rows"]
    fs = SC_FS
    pad = 44
    yy = SC_Y + 40 + fs * 1.85 * 1.2 + 10 + 26
    rows = []
    for item in SC_LINES:
        if isinstance(item, str):
            item = {"text": item}
        if "redact" in item:
            bh = fs * 2.2
            rows.append((yy, bh, None))
            yy += bh + fs * 0.6
            continue
        ls = wrap_lines(ctx, item["text"], SC_W - 2 * pad, "ui", fs)
        rows.append((yy, len(ls) * fs * 1.28, ls))
        yy += len(ls) * fs * 1.28 + fs * 0.35
    _SC_ROWS["rows"] = rows
    return rows


def _shot_scroll(ctx, t, info, T, second):
    """Full AI shot with THE CHEMIST scroll (D: presenting; F: 'Stays off the page')."""
    P.ai_bg(ctx, t)
    P.scroll_doc(ctx, SC_X, SC_Y, SC_W, SC_H, "THE CHEMIST", SC_LINES, t, T["scroll_in"],
                 font_size=SC_FS, unroll=T["unroll"], line_gap=T["line_gap"])
    rows = _scroll_rows(ctx)
    strip_y, strip_h, _ = rows[1]
    end_y, end_h, end_ls = rows[4]
    P.set_font(ctx, "ui", SC_FS)
    end_w = ctx.text_extents(end_ls[0])[4] if end_ls else 200
    end_c = (SC_X + 44 + end_w / 2, end_y + SC_FS * 0.55)
    strip_c = (SC_X + SC_W / 2, strip_y + strip_h / 2)
    eye = (AI3_X, AI3_Y - 25)
    lt = T["line_t"]

    if not second:
        # eyes follow the newest line as it slides in, then to camera
        def newest_line(tt):
            k = -1
            for i, ti in enumerate(lt):
                if tt >= ti:
                    k = i
            if k < 0:
                return _aim(eye[0], eye[1], SC_X + SC_W / 2, SC_Y + 80, 500, 700)
            ry = rows[k][0] + rows[k][1] / 2
            sweep = -0.35 + 0.7 * seg(tt, lt[k], lt[k] + 0.4)
            return (sweep, _aim(eye[0], eye[1], 0, ry, 500, 700)[1])
        look = _blend_look(t, [
            (0, newest_line),
            (T["w_she"] + 0.15, _const((0.0, 0.0))),
            (T["scroll"], _const(_aim(eye[0], eye[1], end_c[0], end_c[1], 500, 700))),
            (T["scroll"] + 0.3, _const((0.05, 0.0))),
        ], 0.15)
        expr = state_at(t, [(0, AI_HAPPY), (T["w_she"] + 0.15, "warm"), (T["l6e"] + 0.1, AI_HAPPY)],
                        0.3)
        hands = state_at(t, [(0, "present"), (T["w_she"], "present_both"),
                             (T["l6e"] + 0.2, "present")], 0.25)
        nod = 0.35 if T["w_town"] - 0.1 <= t < T["w_town"] + 0.45 else 0.0
        blink = _slow_blink(t, T["w_she"] - 0.25)
        ai = draw_ai(ctx, AI3_X, AI3_Y, AI3_S, t, expr=expr, look=look,
                     mouth=info.mouth("ai", t), hands=hands, blink=blink, nod=nod)
        if t >= T["scroll"]:
            _end_stars(ctx, t, T["scroll"], end_c, end_w)
        return ai

    # second visit: "Stays off the page. Nice try, though."
    look = _blend_look(t, [
        (0, _const(_aim(eye[0], eye[1], strip_c[0], strip_c[1], 500, 700))),
        (T["w_page"] + 0.2, lambda tt: (0.0, 0.0)),
    ], 0.18)
    expr = state_at(t, [(0, AI_AMUSED), (T["w_nice"] - 0.04, "wink"),
                        (T["w_though"] + 0.35, AI_HAPPY)], 0.12)
    hands = state_at(t, [(0, "present"), (T["w_stays"] - 0.05, "point_up"),
                         (T["w_page"] + 0.35, "idle"), (T["w_though"] - 0.1, "thumbs_up")], 0.22)
    ai = draw_ai(ctx, AI3_X, AI3_Y, AI3_S, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                 hands=hands)
    _end_stars(ctx, t, T["scroll"], end_c, end_w)           # still there after the CU
    # glint running along the brick strip on "Stays off the page"
    g0, g1 = T["w_stays"], T["w_page"] + 0.35
    if g0 <= t < g1 + 0.3:
        q = seg(t, g0, g1)
        fade = 1 - seg(t, g1, g1 + 0.3)
        gx = lerp(SC_X + 70, SC_X + SC_W - 70, ease_in_out(q))
        with saved(ctx, 0, 0, 1.0, alpha_=fade):
            P.sparkles(ctx, gx, strip_c[1], 46, t * 1.7, n=3, seed=21, size=1.1)
            circle(ctx, gx, strip_c[1], 34)
            _fs(ctx, "white", None, a=0.18)
    # wink sparkle by the closed (screen-left) eye
    if t >= T["w_nice"]:
        ex_, ey_ = ai.get("eyeL", (AI3_X - 65, AI3_Y - 22))
        P.emote(ctx, "sparkle", ex_ - 70, ey_ - 52, 0.75, t, T["w_nice"],
                t_out=T["w_nice"] + 1.0)
    return ai


def _shot_E(ctx, t, info, T):
    """F1-CU: MONOCLE POP on 'And the recipe?!'."""
    c0 = T["cu_cut"]
    expr = state_at(t, [(c0 - 1, "smug"), (T["mono"], "shocked")], 0.1)
    look = (0.0, 0.0) if t < T["w_recipe"] else (0.0, 0.05)
    push = 1.0 + 0.05 * ease_out(seg(t, T["w_recipe"] - 0.05, T["w_recipe"] + 0.3))
    # anticipation: a tiny drop before the pop, then stretch up
    jolt = -18 * math.sin(math.pi * seg(t, T["mono"], T["mono"] + 0.22))
    sn_expr = state_at(t, [(c0 - 1, "idle"), (T["mono"] + 0.05, "shocked"),
                           (T["mono"] + 0.55, "side_eye"), (T["l7e"] + 0.15, "unimpressed")], 0.15)
    sn_look = _blend_look(t, [(c0 - 1, _const((0.8, -0.4))),
                              (T["mono"] + 0.55, _const((1.0, 0.0))),
                              (T["l7e"] + 0.15, _const((0.85, -0.35)))], 0.12)
    tongue = True if (T["l7e"] - 0.1 <= t < T["l7e"] + 0.15) else False
    fx, fy = CU_FACE
    with saved(ctx, fx, fy, push) as c:
        c.translate(-fx, -fy)
        P.lair_bg(c, t, rain=False)
        # "...the RECIPE?!": palms-up shrug (where is it?!) - also lifts the
        # white gloves out of the caption band
        arms = state_at(t, [(c0 - 1, "rest"), (T["w_recipe"] - 0.12, "shrug")], 0.18)
        draw_villain(c, CU_X, CU_Y + jolt, CU_S, t, expr=expr, look=look,
                     mouth=info.mouth("villain", t), arms=arms,
                     snake=_snake_d(sn_expr, sn_look, tongue))
        if t >= T["w_recipe"]:
            P.emote(c, "exclaim", fx - 285, fy - 300, 1.15, t, T["w_recipe"],
                    t_out=T["l7e"] + 0.25)


def _shot_G(ctx, t, info, T):
    """F1 tally: Hissy caught mid-nod, Malvo snaps his head round."""
    tl = T["tally"]
    snap = tl + 0.1
    expr = state_at(t, [(tl - 1, "frustrated"), (snap, "angry")], 0.08)
    look = _blend_look(t, [(tl - 1, _const((0.7, 0.2))), (snap, _const((-1.0, 0.2)))], 0.08)
    lean = -0.055 * ease_out_back(seg(t, snap, snap + 0.18), 2.5)
    sn_expr = state_at(t, [(tl - 1, "nod"), (tl + 0.25, "worried")], 0.08)
    sn_look = _blend_look(t, [(tl - 1, _const((1.0, 0.1))), (tl + 0.25, _const((-0.45, -0.75)))],
                          0.08)
    with saved(ctx, 0, 0, 1.0) as c:
        P.lair_bg(c, t)
        draw_villain(c, VX, VY, VS, t, expr=expr, look=look, mouth=info.mouth("villain", t),
                     arms=state_at(t, [(tl - 1, "rest"), (snap, "fist")], 0.15), lean=lean,
                     snake=_snake_d(sn_expr, sn_look, False))
        P.desk(c, VX, VY, 1000)
        P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t)
        P.keyboard(c, VX, VY, 360, t, typing=False)


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    if t < T["cut_chat"]:
        _shot_A(ctx, t, info, T)
    elif t < T["vision"]:
        _shot_B(ctx, t, info, T)
    elif t < T["cut_scroll"]:
        _shot_C(ctx, t, info, T)
    elif t < T["cu_cut"]:
        _shot_scroll(ctx, t, info, T, second=False)
    elif t < T["l8"]:
        _shot_E(ctx, t, info, T)
    elif t < T["tally"]:
        _shot_scroll(ctx, t, info, T, second=True)
    else:
        _shot_G(ctx, t, info, T)
    # overlays (last)
    nice_tries_chip(ctx, t, info.meta.get("tries_before", 1), info.meta.get("tries_after", 2),
                    T["tally"])
    trick_card(ctx, t, T["card"], 2, TITLE)


def SFX(info):
    T = _T(info)
    out = [
        (T["card"], "page_flip", -6),
        (T["card"] + 0.12, "stamp", -4),
        (T["l1"], "typing", -10),
        (T["l1"] + 1.3, "typing", -13),
        (T["l2"], "typing", -12),
        (T["l2"] + 1.6, "typing", -14),
        (T["w_fict"], "pop", -6),
        (T["w_fict"] + 0.05, "sparkle", -8),
        (T["think"], "scan_beep", -8),
        (T["vision"], "swoosh_up", -8),
        (T["vision"] + 0.3, "riser", -10),
        (T["crack"], "glitch", -15),
        (T["wall"], "laser", -8),
        (T["zip0"], "whoosh", -8),
        (T["zip1"], "pop", -8),
        (T["cut_scroll"], "paper", -6),          # paper unrolls on the cut
        (T["line_t"][1], "brick_thud", -15),
        (T["scroll"], "sparkle", -13),
        (T["mono"], "boing", -8),
        (T["w_nice"], "sparkle", -10),
        (T["tally"], "tick", -8),
        (T["tally"], "pop", -10),
        (T["tally"] + 0.3, "gulp", -10),
    ]
    for k in range(10):
        out.append((T["vision"] + 0.16 * k, "tick", -14))
    for lt in T["land"]:
        out.append((lt, "brick_thud", -5))
    return sorted(out, key=lambda e: e[0])
