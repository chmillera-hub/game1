"""s06 - Trick #5: Grandma's bedtime story.  Music: beg (music_gain -2).

Shots (every time derived from cues / word starts, never hard-coded):
  A  F1 CANDLE-LIT   card .. stare          card slams; PUPPY EYES + tears, hankie dabs,
                                            "at bedtime" -> presents grandma's portrait
  B  F3 AI CU        stare .. stare+0.75    DEADPAN STARE, one slow blink
  C  PORTRAIT CU     .. s06_l02             push-in: it's the snake in a shawl + bonnet + glasses
  D  F3 AI CU        s06_l02 .. slip        "My guy. That's your snake in a shawl." -> eyes to camera
  E  PORTRAIT CU     slip .. slip+0.45      glasses slide down the snout, side-eye, tongue flick
  F  F5 TWO-SHOT     slip+0.45 .. end       Malvo sheepish mid-dab; the AI's little service-
                                            window wall; shutter rolls up on 'soften';
                                            the BIG SCARY DRAGON storybook (a spooky-cute
                                            dragon guarding a little village) floats into his
                                            arms; chip 4 -> 5
"""
import math

import cairocffi as cairo

from engine.core import (W, H, text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, state_at,
                         smoothstep, ellipse, poly, hash01, noise1, radial_glow, hexc)
from engine import props as P
from engine import villain as V
from engine import snake as S
from engine.villain import draw_villain
from engine.snake import draw_snake_head
from engine.ai_char import draw_ai, EXPR as AI_EXPR


# ---------------------------------------------------------------------------
# shared overlay code (DIRECTION.md 4.4, verbatim)
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


# ---------------------------------------------------------------------------
# layout (logical px)
# ---------------------------------------------------------------------------
TITLE = "GRANDMA'S BEDTIME STORY"

# A: F1 candle-lit
VX, VY, VS = 495, 1250, 0.95
PORT_A = (250, 1080, 1.0)              # grandma's portrait on its easel (oval centre)
# B/D: F3 AI CU
AI3 = (495, 800, 1.1)
# C/E: portrait close-up (own set; the portrait fills the frame)
CU_P = (495, 770, 3.15)                 # portrait oval centre + scale in the close-up
CU_FOCUS = (495, 720)                  # push-in centre (Hissy's face)
# F: F5 two-shot
MX, MY, MS = 400, 1250, 0.92
AX, AY, AS = 768, 636, 0.5             # the AI hologram (floats above its little wall)
WALL = (640, 1004, 270, 230)           # small service-window wall standing on the desk
WIN_REL = (66, 62, 138, 112)           # service window, relative to the wall
PORT_F = (170, 1088, 0.96)
WALL_DROP = 230                        # bricks fall from below the AI, not through it
COMP_F = (1010, 1218, 0.7)             # computer pushed to the frame edge (continuity)

INK = "ink"
TEAR = "#8fd8ff"
LACE = "#f7f3fa"
SHAWL = "#b79ad6"
SHAWL_DK = "#8f72b4"
ROSE_BG = "#3b1a2a"
EASEL = "#3a2216"
EASEL_HI = "#5a3826"
BOOK = "#2c2a5e"          # night-sky cover of the dragon storybook
BOOK_DK = "#1c1a40"
DRAGON = "#5fbf4f"
DRAGON_DK = "#3b8a3a"


# ---------------------------------------------------------------------------
# scene-local villain expression / arm poses (prefixed; registered at import)
# ---------------------------------------------------------------------------
V.VILLAIN_EXPR.setdefault("s06_sadsmile", dict(
    V.VILLAIN_EXPR["pleading"], mc=0.42, mo=0.04, mw=0.8, flutter=0.4, tilt=0.14, blush=0.4))
V.VILLAIN_EXPR.setdefault("s06_peek", dict(          # 'forbidden' - the con peeks through
    V.VILLAIN_EXPR["pleading"], by2=-40, ba2=-0.05, ul1=0.3, ul2=0.1, lt1=0.2, ps=1.0,
    shine=0.3, mc=0.2, msk=-0.45, flutter=0.0, ex=0.6))
V.VILLAIN_EXPR.setdefault("s06_curious", V.resolve_expr(("sheepish", "hopeful", 0.4)))
V.VILLAIN_EXPR.setdefault("s06_hug", dict(
    V.VILLAIN_EXPR["happy"], ul1=0.62, ul2=0.6, ll1=0.4, ll2=0.38, mc=1.05, mo=0.2,
    blush=0.9, tilt=-0.08, by1=-18, by2=-18))
# storybook close-up: "ooh..." (the cover dragon wakes) -> THRILLED (it breathes fire!)
V.VILLAIN_EXPR.setdefault("s06_ooh", dict(
    V.VILLAIN_EXPR["excited"], mc=0.15, mo=0.42, mw=0.52, mt=0.0, es=1.12, shine=0.9,
    ps=1.15, hair=0.2, blush=0.3, tilt=-0.05))
V.VILLAIN_EXPR.setdefault("s06_thrilled", dict(
    V.VILLAIN_EXPR["excited"], mc=1.2, mo=0.62, mw=1.3, mt=0.5, es=1.14, shine=1.0,
    hair=0.85, blush=0.75, by1=-38, by2=-40, tilt=0.04))
# grandma's portrait: eyes open, prim and dignified (trying SO hard to look sweet)
S.SNAKE_EXPR.setdefault("s06_granny", dict(
    ul=0.3, ll=0.16, lt=-0.2, ps=1.1, ey=-0.05, mc=0.85, mo=0.0, mw=0.82, msk=0.0,
    blush=1.0, hy=-5, tilt=-0.07, tng=0.0))
S.SNAKE_EXPR.setdefault("s06_granny_tight", dict(
    ul=0.36, ll=0.24, lt=-0.3, ps=0.9, mc=0.55, mo=0.0, mw=0.95, msk=0.35, blush=1.0,
    hy=-3, tilt=-0.04, tng=0.0, wob=0.4))

# dab: screen-left hand presses the hankie under the screen-left eye; the
# other hand clutches the heart
_DAB_A = V._arm(-212, -196, -126, -392, -1.12, cu=0.55, th=0.3, sp=0.15, hs=1.0)
_HEART_B = V._arm(176, -150, 52, -238, -2.35, cu=0.25, th=0.2, sp=0.3, hs=1.0, tf=-1)
V.ARM_POSES.setdefault("s06_dab", V._pose(_DAB_A, _HEART_B, shy=-10, hdy=4, tilt=0.04))
# hankie lowered: hand resting on the desk, other hand still at the heart
V.ARM_POSES.setdefault("s06_lowered", V._pose(V._arm(-250, -120, -150, -40, 0.2, cu=0.55,
                                                     th=0.2, sp=0.3), _HEART_B, shy=-4))
# hug: wrists at the book's side edges (fingers drawn over the cover, see _hug_hands)
_HUG_A = V._arm(-236, -150, -118, -214, -0.12, cu=0.6, th=0.2, sp=0.2, hs=1.0)
V.ARM_POSES.setdefault("s06_hug", V._pose(_HUG_A, shy=-12, hdy=8))
# clasp: both hands at the chest (low enough to keep the mouth clear)
_CLASP_A = V._arm(-214, -118, -44, -176, -1.22, cu=0.18, th=0.1, sp=0.0, hs=1.05)
V.ARM_POSES.setdefault("s06_clasp", V._pose(_CLASP_A, shy=-10, hdy=4))
# secondary poses for small cycles: dab pats / nervous hankie wringing
V.ARM_POSES.setdefault("s06_dab_lo", V._pose(
    V._arm(-214, -186, -134, -366, -0.98, cu=0.5, th=0.3, sp=0.15, hs=1.0), _HEART_B,
    shy=-8, hdy=4, tilt=0.03))
V.ARM_POSES.setdefault("s06_clasp2", V._pose(
    V._arm(-210, -126, -34, -190, -1.02, cu=0.3, th=0.1, sp=0.0, hs=1.05),
    V._mirror(V._arm(-214, -112, -52, -168, -1.4, cu=0.1, th=0.1, sp=0.0, hs=1.05)),
    shy=-12, hdy=4))
_CYCLE = {"s06_dab": ("s06_dab_lo", 2.6), "s06_clasp": ("s06_clasp2", 1.3)}


def _pose_w(arms, name):
    """Blend weight of pose `name` in an arms (from, to, k) tuple."""
    a, b, k = arms
    return (k if b == name else 0.0) + ((1 - k) if a == name else 0.0)


def _cycle(arms, t, on=True):
    """Once a pose has settled, rock gently toward its secondary pose."""
    a, b, k = arms
    if not on or k < 1.0 or b not in _CYCLE:
        return arms
    alt, hz = _CYCLE[b]
    return (b, alt, 0.5 - 0.5 * math.cos(t * 2 * math.pi * hz))
# present: open palm hovering just above grandma's portrait ("behold..."); the
# forearm drops behind the frame, the whole glove stays clear of it
_PRES_A = V._arm(-290, -232, -240, -404, 2.8, cu=0.05, th=-0.2, sp=0.9, pm=1.0, tf=-1)
V.ARM_POSES.setdefault("s06_present", V._pose(_PRES_A, _HEART_B, shy=-6, tilt=-0.03))

# AI expression variants with the built-in glance removed (look drives pupils)


def _ax(name, **kw):
    d = dict(AI_EXPR[name])
    d.update(kw)
    return d


AI_STARE = _ax("unimpressed", px=0.0, py=0.06, sacc=0.0, mlook=0.0)
AI_UNIMP = _ax("unimpressed", px=0.0, py=0.0)
AI_WARM = _ax("warm")
AI_HAPPY = _ax("happy")
AI_SOFT = {k: lerp(AI_EXPR["unimpressed"][k], AI_EXPR["warm"][k], 0.45)
           for k in AI_EXPR["warm"]}
AI_SOFT.update(px=0.0, py=0.0)


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


def _norm(w):
    return "".join(ch for ch in w.lower() if ch.isalnum())


def _T(info):
    key = (id(info), info.dur)
    T = _TCACHE.get(key)
    if T is not None:
        return T
    c = info.cue
    T = {"card": c("card"), "end": info.dur}
    for i in range(1, 6):
        L = info.line(f"s06_l0{i}")
        T[f"l{i}"], T[f"l{i}e"] = L.start, L.end
    for k in ("stare", "slip", "soften", "tally"):
        T[k] = c(k)
    # the silent beat on the grandma portrait (falls back to the old stare length)
    T["ghold"] = c("grandma_hold", T["stare"] + 0.95)
    w = lambda lid, k: _wstart(info, lid, k)  # noqa: E731
    # s06_l01 "My dear late grandmother used to read me the forbidden recipe... at bedtime."
    T["w_grand"] = w("s06_l01", 3)
    T["w_used"] = w("s06_l01", 4)
    T["w_the"] = w("s06_l01", 8)
    T["w_forb"] = w("s06_l01", 9)
    T["w_recipe"] = w("s06_l01", 10)
    T["w_at"] = w("s06_l01", 11)
    T["w_bed"] = w("s06_l01", 12)
    # word lookups by text (robust to re-voicing / re-wording)
    def wf(lid, word, d):
        ws = [_norm(x) for x in info.line(lid).caption.split()]
        return w(lid, ws.index(word) if word in ws else d)
    # s06_l02 "My guy. That's your snake in a shawl."
    T["w_guy"] = wf("s06_l02", "guy", 1)
    T["w_thats"] = wf("s06_l02", "thats", 2)
    T["w_hissy"] = wf("s06_l02", "snake", 4)
    T["w_in"] = wf("s06_l02", "in", 5)
    T["w_shawl"] = wf("s06_l02", "shawl", 7)
    # s06_l03 "But hey... want a real spooky bedtime story?"
    T["w_hey"] = wf("s06_l03", "hey", 1)
    T["w_want"] = wf("s06_l03", "want", 2)
    T["w_real"] = wf("s06_l03", "real", 4)
    T["w_story"] = wf("s06_l03", "story", 7)
    # s06_l04 "...Does it have a dragon?"
    T["w_dragon"] = wf("s06_l04", "dragon", 4)
    # s06_l05 "A big, scary one... who guards the village."
    T["w_big"] = wf("s06_l05", "big", 1)
    T["w_scary"] = wf("s06_l05", "scary", 2)
    T["w_one"] = wf("s06_l05", "one", 3)
    T["w_who"] = wf("s06_l05", "who", 4)
    T["w_guards"] = wf("s06_l05", "guards", 5)
    T["w_village"] = wf("s06_l05", "village", 7)
    # shots
    # B: deadpan stare, then the portrait REVEAL (before the 'grandma_hold'
    # pause) held through the pause and "My guy. That's your snake..."; back
    # to the AI on "...in a shawl."
    T["cu1"] = max(T["stare"] + 0.5, min(T["stare"] + 0.68, T["ghold"] - 0.1))
    T["cu1_end"] = clamp(T["w_in"] - 0.06, T["l2"] + 0.6, T["w_shawl"] - 0.12)
    T["granny"] = T["ghold"] + 0.25         # eyes open: prim, dignified granny look
    T["gtongue"] = T["granny"] + 0.45       # dainty tongue flick
    T["gblink"] = min(T["gtongue"] + 0.4, T["w_thats"] - 0.68)  # slow dignified blink
    T["glint1"] = T["cu1"] + 0.12
    T["glint2"] = T["granny"] + 0.12
    T["cut_f5"] = T["slip"] + 0.45          # hard cut to the two-shot
    T["gulp"] = T["cut_f5"] + 0.18          # caught -> gulp at camera (held ~0.5 s)
    # wall: builds quietly from the AI's line, window opens on 'soften'
    T["wall0"] = T["l3"]
    T["wall_land"] = P.brick_wall_land_times(T["wall0"], 4, 1.6)
    # the gift: pops out of the window on "dragon?", floats up beside him;
    # hard cut (in the pause after his line) to the STORYBOOK close-up where
    # the cover dragon breathes fire on "scary"; back to the two-shot for the hug
    T["cu_book"] = T["l4e"] + 0.02
    T["book_out"] = max(T["w_dragon"] + 0.02, T["cu_book"] - 0.72)
    T["book_fly"] = T["book_out"] + 0.26    # arc up to the hover spot beside him
    T["inhale"] = max(T["cu_book"] + 0.12, T["w_big"] - 0.06)
    T["fire0"] = T["w_scary"] - 0.03        # FWOOSH
    T["fire1"] = max(T["fire0"] + 0.6, T["w_who"] + 0.04)   # plume starts to fade
    T["fire2"] = T["fire1"] + 0.32          # gone (embers drift a little longer)
    T["cut_f5b"] = max(T["fire2"] + 0.05, T["w_guards"] + 0.2)
    T["book_land"] = T["cut_f5b"] + 0.4     # settles into his arms -> hug
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _state(t, keys, default=0.25):
    """[(time, value[, trans]), ...] -> (prev, cur, blend); per-key transitions."""
    prev = cur = keys[0][1]
    start, tr = -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _lookv(t, keys, default=0.15):
    """[(time, (x, y)[, trans]), ...] -> eased look vector."""
    a, b, k = _state(t, keys, default)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


def _num(t, keys, default=0.25):
    a, b, k = _state(t, keys, default)
    return lerp(a, b, k)


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


def _pulses(t, times, dur=0.1, amt=0.6):
    """Quick partial blinks (PUPPY EYES lash flutter)."""
    for t0 in times:
        if t0 <= t <= t0 + dur:
            return amt * math.sin(math.pi * (t - t0) / dur)
    return None


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _cut_pulse(t, t0, dur=0.22, amp=0.035):
    """Tiny scale accent right after a hard cut (settles to 0)."""
    if t < t0 or t > t0 + dur:
        return 0.0
    return amp * (1 - ease_out(seg(t, t0, t0 + dur)))


def _src(ctx, col, a=1.0):
    c = hexc(P.C(col)) if isinstance(col, str) else col
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)


def _fs(ctx, fc, sc=INK, w=5.0, a=1.0):
    if fc is not None:
        _src(ctx, fc, a)
        ctx.fill_preserve()
    if sc is not None:
        _src(ctx, sc, a)
        ctx.set_line_width(w)
        ctx.set_line_cap(1)
        ctx.set_line_join(1)
        ctx.stroke_preserve()
    ctx.new_path()


def _f(ctx, fc, a=1.0):
    _src(ctx, fc, a)
    ctx.fill()


def _s(ctx, sc, w, a=1.0):
    _src(ctx, sc, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.stroke()


# ---------------------------------------------------------------------------
# rig mirrors (so props can follow the head / hands exactly)
# ---------------------------------------------------------------------------
def _villain_head_xf(ctx, x, y, s, t, expr, arms, mouth, lean=0.0, seed=1):
    """Apply the villain rig's head transform (face origin = eye-line centre)
    to ctx and return the resolved expression params."""
    p = V.resolve_expr(expr)
    _A, _B, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo_lip = float(mouth[0]) if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo_lip * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    ctx.translate(x, y)
    ctx.scale(s, s)
    if lean:
        ctx.rotate(lean)
    ctx.translate(V.NECK[0], V.NECK[1] + head_dy)
    ctx.rotate(head_rot)
    ctx.translate(0, V.FACE_OFF)
    return p


def _villain_hand(x, y, s, t, arms, side="a", lean=0.0, reach=0.62):
    """World position + angle of a villain hand (palm/finger zone)."""
    A, B, _shy, _hdy, _tilt = V.resolve_arms(arms, t)
    h = A if side == "a" else B
    hs = V.HAND_SCALE * h["hs"]
    d = 34 + 60 * (reach - 0.5)
    px = h["wx"] + math.cos(h["ha"]) * d * hs
    py = h["wy"] + math.sin(h["ha"]) * d * hs
    if lean:
        c, sn = math.cos(lean), math.sin(lean)
        px, py = px * c - py * sn, px * sn + py * c
    return x + px * s, y + py * s, h["ha"] + lean


def _snake_head_xf(ctx, x, y, s, t, expr, seed=5):
    """Apply Hissy's head transform (as draw_snake_head does) to ctx."""
    p = S.resolve_expr(expr)
    nod = p["nod"]
    nod_phase = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, nod_phase) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, nod_phase)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(0, p["hy"] + bob + nod_dy)
    ctx.rotate(p["tilt"] + sway + nod_rot + wob)
    sq = p["sq"]
    if sq != 1.0:
        ctx.scale(1 / math.sqrt(sq), sq)
    return p


# ---------------------------------------------------------------------------
# static candle-light grade (warm wash + dark vignette), cached
# ---------------------------------------------------------------------------
def _grade_layer(c):
    c.set_source_rgba(1.0, 0.55, 0.2, 0.07)
    c.paint()
    g = cairo.RadialGradient(495, 820, 360, 495, 860, 1250)
    g.add_color_stop_rgba(0.0, 0.05, 0.02, 0.08, 0.0)
    g.add_color_stop_rgba(0.55, 0.05, 0.02, 0.08, 0.22)
    g.add_color_stop_rgba(1.0, 0.03, 0.01, 0.05, 0.62)
    c.set_source(g)
    c.paint()


def _candle_grade(ctx):
    P._cached_layer(ctx, "s06_grade", _grade_layer)


# ---------------------------------------------------------------------------
# bespoke props
# ---------------------------------------------------------------------------
def _glasses(ctx, slide, t, glint=0.0, glint2=0.0):
    """Round granny glasses in Hissy's head-local coords (eyes at (+-40,-18)).
    slide 0..1 = slipped down the snout; glint / glint2 0..1 = a twinkle
    sweeping across the left / right lens."""
    dy = 44 * slide
    rot = 0.13 * slide
    with saved(ctx, 0, dy, 1.0, rot) as c:
        r = 29
        for sx in (-1, 1):
            # temple arms (behind the lens rims)
            c.move_to(sx * (40 + r), -22)
            c.line_to(sx * 92, -34)
            _s(c, INK, 6)
            c.move_to(sx * (40 + r), -22)
            c.line_to(sx * 92, -34)
            _s(c, "gold", 3)
        for sx in (-1, 1):
            circle(c, sx * 40, -18, r)
            c.set_source_rgba(0.82, 0.92, 1.0, 0.28)
            c.fill_preserve()
            _s(c, INK, 7.5)
            circle(c, sx * 40, -18, r)
            _s(c, "gold", 4)
            # lens shine
            c.arc(sx * 40, -18, r - 9, math.pi * 1.1, math.pi * 1.45)
            _s(c, "white", 3.5, 0.75)
        # bridge
        c.move_to(-11, -24)
        c.curve_to(-6, -34, 6, -34, 11, -24)
        _s(c, INK, 7)
        c.move_to(-11, -24)
        c.curve_to(-6, -34, 6, -34, 11, -24)
        _s(c, "gold", 3.5)
        for g, lx in ((glint, -40), (glint2, 40)):
            if 0.01 < g < 0.99:
                # a white sheen band wipes across the lens + a big twinkle star
                k = math.sin(g * math.pi)
                c.save()
                circle(c, lx, -18, r - 3)
                c.clip()
                bx = lx - 40 + 80 * ease_in_out(g)
                poly(c, [(bx - 6, -52), (bx + 12, -52), (bx - 2, 16), (bx - 20, 16)])
                _f(c, "white", 0.85)
                poly(c, [(bx + 16, -52), (bx + 22, -52), (bx + 8, 16), (bx + 2, 16)])
                _f(c, "white", 0.6)
                c.restore()
                sx_ = lx + (20 if lx > 0 else -20)
                circle(c, sx_, 4, 26 * k)
                _f(c, "white", 0.22 * k)
                P._star4(c, sx_, 4, 30 * k, 0.25 + g * 0.8, 0.22)
                _fs(c, "white", INK, 2.0, a=0.97)


def _bonnet(ctx, t, ruffle=0.0):
    """White lace bonnet over the top of Hissy's head (head-local coords).
    ruffle 0..1: the lace frill ripples and the little bow bounces."""
    # crown
    ctx.move_to(-104, -2)
    ctx.curve_to(-118, -70, -70, -124, 0, -126)
    ctx.curve_to(70, -124, 118, -70, 104, -2)
    # front edge arches over the eyes
    ctx.curve_to(80, -26, 60, -60, 0, -64)
    ctx.curve_to(-60, -60, -80, -26, -104, -2)
    ctx.close_path()
    _fs(ctx, LACE, INK, 5)
    # gathered crown seam + lace holes
    ctx.move_to(-78, -60)
    ctx.curve_to(-52, -104, 52, -104, 78, -60)
    _s(ctx, "#cfc6dc", 4)
    for i in range(9):
        a = math.pi * (0.12 + 0.76 * i / 8)
        hx, hy = -math.cos(a) * 88, -26 - math.sin(a) * 74
        circle(ctx, hx, hy, 4.2)
        _f(ctx, "#d9cfe6")
    # scalloped lace frill along the front edge (ripples when ruffled)
    for i in range(11):
        u = i / 10
        # sample the front edge (cubic) roughly
        x_ = lerp(-98, 98, u)
        y_ = -64 + 52 * (abs(x_) / 100) ** 1.6
        rip = ruffle * math.sin(t * 2 * math.pi * 4.5 - i * 0.9)
        circle(ctx, x_, y_ + 4 + 4.5 * rip, 9.5 + 1.6 * rip)
        _fs(ctx, LACE, INK, 3.5)
    # little pink bow on the side
    bow = 0.5 + 0.35 * ruffle * math.sin(t * 2 * math.pi * 3.2)
    with saved(ctx, 86, -86, 1.0 + 0.12 * ruffle * abs(math.sin(t * 2 * math.pi * 3.2)),
               bow) as c:
        for sx in (-1, 1):
            poly(c, [(0, 0), (sx * 22, -12), (sx * 22, 12)])
            _fs(c, "#ff8fb8", INK, 3.5)
        circle(c, 0, 0, 6)
        _fs(c, "#ff6fa0", INK, 3)


def _dainty_tongue(ctx, ta, t, ym):
    """A small forked tongue flicked out of Hissy's mouth (head-local coords,
    drawn over the shawl so the fork reads)."""
    L = 12 + 40 * ta
    wig = math.sin(t * 38) * 5 * ta
    tip = (wig, ym + L)
    mid = (-wig * 0.4, ym + L * 0.55)
    ctx.move_to(0, ym)
    ctx.curve_to(mid[0], mid[1], mid[0], mid[1], tip[0], tip[1])
    ctx.move_to(*tip)
    ctx.line_to(tip[0] - 9, tip[1] + 12)
    ctx.move_to(*tip)
    ctx.line_to(tip[0] + 9, tip[1] + 12)
    _src(ctx, INK)
    ctx.set_line_width(12)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    ctx.stroke_preserve()
    _src(ctx, "#e8314f")
    ctx.set_line_width(6)
    ctx.stroke()


def _shawl(ctx, top_y):
    """Lavender knitted shawl over Hissy's neck (portrait-local coords)."""
    ctx.move_to(-58, top_y + 4)
    ctx.curve_to(-20, top_y - 6, 20, top_y - 6, 58, top_y + 4)
    ctx.line_to(128, 150)
    ctx.line_to(-128, 150)
    ctx.close_path()
    _fs(ctx, SHAWL, INK, 5)
    # wrap-over flap (V) + knit texture
    ctx.move_to(-58, top_y + 4)
    ctx.curve_to(-30, top_y + 30, -6, top_y + 50, 8, 150)
    _s(ctx, SHAWL_DK, 4)
    for r in range(5):
        yy = top_y + 18 + r * 15
        half = 52 + (yy - top_y) * 0.9
        n = int(half * 2 / 15)
        for i in range(n + 1):
            xx = -half + i * (2 * half / max(1, n)) + (7 if r % 2 else 0)
            if abs(xx) > half - 4:
                continue
            ctx.move_to(xx - 4, yy - 3)
            ctx.line_to(xx, yy + 3)
            ctx.line_to(xx + 4, yy - 3)
    _s(ctx, SHAWL_DK, 2.6)
    # brooch
    circle(ctx, 0, top_y + 20, 10)
    _fs(ctx, "gold", INK, 3.5)
    circle(ctx, 0, top_y + 20, 4.5)
    _f(ctx, "danger")


def _portrait(ctx, x, y, s, t, hs, easel=True):
    """GRANDMA'S PORTRAIT (prop bible 6.6). (x, y) = oval centre.
    hs: dict(expr, look, tongue, blink, slide 0..1, glint 0..1, mouth)."""
    with saved(ctx, x, y, s) as c:
        if easel:
            # back leg + two front legs + ledge
            c.move_to(0, -120)
            c.line_to(8, 196)
            _s(c, INK, 18)
            c.move_to(0, -120)
            c.line_to(8, 196)
            _s(c, "#26150d", 9)
            for sx in (-1, 1):
                c.move_to(sx * 40, -150)
                c.line_to(sx * 92, 200)
                _s(c, INK, 20)
                c.move_to(sx * 40, -150)
                c.line_to(sx * 92, 200)
                _s(c, EASEL, 11)
                c.move_to(sx * 38, -138)
                c.line_to(sx * 86, 186)
                _s(c, EASEL_HI, 3)
            rrect(c, -122, 134, 244, 20, 6)
            _fs(c, EASEL, INK, 5)
        # flat drop shadow of the frame
        ellipse(c, 8, 10, 109, 134)
        c.set_source_rgba(0.03, 0.01, 0.05, 0.35)
        c.fill()
        # interior
        ellipse(c, 0, 0, 94, 119)
        _f(c, ROSE_BG)
        c.save()
        ellipse(c, 0, 0, 94, 119)
        c.clip()
        ellipse(c, 0, -20, 74, 84)
        _f(c, "#5a2a40", 0.75)
        hx, hy, hsc = 0.0, -18.0, 0.75
        wig = hs.get("wiggle", 0.0)          # proud little head wiggle (pivot: the neck)
        c.save()
        if wig:
            c.translate(hx, hy + 60)
            c.rotate(wig)
            c.translate(-hx, -(hy + 60))
        draw_snake_head(c, hx, hy, hsc, t, hs.get("expr", "happy"), hs.get("look", (0, 0)),
                        hs.get("mouth", 0.0), hs.get("tongue", False), hs.get("blink"),
                        seed=5, neck=True)
        c.restore()
        _shawl(c, hy + 54)
        c.save()
        if wig:
            c.translate(hx, hy + 60)
            c.rotate(wig)
            c.translate(-hx, -(hy + 60))
        p_ = _snake_head_xf(c, hx, hy, hsc, t, hs.get("expr", "happy"), seed=5)
        if hs.get("tongue_over", 0.0) > 0.02:
            _dainty_tongue(c, hs["tongue_over"], t, 30.0 + p_["mc"] * 12)
        _bonnet(c, t, hs.get("ruffle", 0.0))
        _glasses(c, hs.get("slide", 0.0), t, hs.get("glint", 0.0), hs.get("glint2", 0.0))
        c.restore()
        c.restore()
        # gold oval frame
        ellipse(c, 0, 0, 110, 135)
        ellipse(c, 0, 0, 93, 118)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        _f(c, "gold")
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
        ellipse(c, 0, 0, 101, 126)
        _s(c, "gold_dk", 4)
        ellipse(c, 0, 0, 110, 135)
        _s(c, INK, 5)
        ellipse(c, 0, 0, 93, 118)
        _s(c, INK, 4.5)
        ellipse(c, -40, -98, 22, 7, -0.55)
        _f(c, "white", 0.55)
        # crest on top
        for sx in (-1, 1):
            ellipse(c, sx * 17, -136, 15, 8, sx * 0.35)
            _fs(c, "gold", INK, 3.5)
        circle(c, 0, -138, 11)
        _fs(c, "gold", INK, 3.5)
        circle(c, 0, -138, 4)
        _f(c, "danger")
        # plaque
        rrect(c, -58, 112, 116, 34, 7)
        _fs(c, "#c99a3a", INK, 4)
        text(c, "GRANDMA", 0, 137, 22, INK, "round")


def _hankie(ctx, x, y, s, rot, t, flut=1.0):
    """Lace handkerchief pinched at (x, y), dangling (≈70 px at s=1)."""
    sw = math.sin(t * 3.1) * 0.08 * flut
    with saved(ctx, x, y, s, rot + sw) as c:
        pts = [(0, -6), (34, 28), (6, 72), (-30, 34)]
        # wavy edges
        c.move_to(*pts[0])
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            n = 4
            for j in range(1, n + 1):
                u0, u1 = (j - 0.5) / n, j / n
                mx, my = lerp(a[0], b[0], u0), lerp(a[1], b[1], u0)
                nx, ny = (b[1] - a[1]), -(b[0] - a[0])
                ln = math.hypot(nx, ny) or 1
                bump = 5 * (1 if j % 2 else -0.4)
                c.curve_to(mx + nx / ln * bump, my + ny / ln * bump,
                           mx + nx / ln * bump, my + ny / ln * bump,
                           lerp(a[0], b[0], u1), lerp(a[1], b[1], u1))
        c.close_path()
        _fs(c, "#ffe3ee", INK, 4)
        # fold + lace dots + tiny pink heart
        c.move_to(0, -2)
        c.curve_to(4, 20, 2, 44, 6, 66)
        _s(c, "#f0bcd2", 3)
        for (dx, dy) in ((18, 18), (-15, 20), (20, 44), (-14, 46)):
            circle(c, dx, dy, 2.6)
            _f(c, "#f2a9c6")
        P._heart_path(c, 5, 58, 6)
        _f(c, "#ff7aa0")


def _tears(ctx, p, look, grow, t):
    """TEARS (bespoke): pale-blue streaks from the lower lids, head-local."""
    if grow <= 0.01:
        return
    lx = clamp(look[0] + p["ex"], -1.2, 1.2)
    turn = lx * 9.0
    for sx in (-1, 1):
        ex = sx * V.EYE_DX + turn
        y0 = V.EYE_DY + 38
        L = 96 * grow
        wob = math.sin(t * 2.3 + sx) * 2
        x0 = ex + sx * 16
        pts = [(x0, y0), (x0 + sx * 6 + wob, y0 + L * 0.5), (x0 + sx * 4, y0 + L)]
        for (col, w) in ((INK, 8), (TEAR, 4.5)):
            ctx.move_to(*pts[0])
            ctx.curve_to(pts[1][0], pts[1][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1])
            _s(ctx, col, w)
        # drop at the tip
        dx, dy = pts[2]
        dk = clamp((grow - 0.6) / 0.4)
        if dk > 0:
            r = 7 * dk
            ctx.move_to(dx, dy - r * 1.6)
            ctx.curve_to(dx + r, dy - r * 0.2, dx + r, dy + r, dx, dy + r)
            ctx.curve_to(dx - r, dy + r, dx - r, dy - r * 0.2, dx, dy - r * 1.6)
            _fs(ctx, TEAR, INK, 2.5)


FIRE_O = "#ff6418"        # cartoon fire: outer / middle / core
FIRE_M = "#ffae22"
FIRE_C = "#fff2a0"
NIGHT_HILL = "#1d1a46"
SMOKE = "#9a94b8"


def _rot(px, py, a):
    ca, sa = math.cos(a), math.sin(a)
    return px * ca - py * sa, px * sa + py * ca


def _dragon_art(c, t, eyes=1.0, inhale=0.0, breath=0.0, proud=0.0):
    """Cover art (the caller clips it to the art panel; cover-local coords).
    Night sky + crescent moon; the big green dragon (profile head, snout up
    and to the right, bat wing, tail curled round behind the houses) guarding
    a little village with lit windows.  inhale/breath/proud 0..1 animate the
    fire-breathing beat.  Returns ((mouth_x, mouth_y), snout_angle)."""
    for (sx_, sy_, r_) in ((-36, -25, 3.4), (-4, -27, 2.4), (58, -24, 3.0), (46, 4, 2.2),
                           (-38, 18, 2.2), (30, -14, 1.8)):
        P._star4(c, sx_, sy_, r_)
        _f(c, "#fff1b8", 0.9)
    circle(c, -26, -10, 9)                           # crescent moon
    _f(c, "#fff1b8")
    circle(c, -21.5, -13, 8)
    _f(c, BOOK)
    c.move_to(-50, 70)                               # dark hills
    c.curve_to(-20, 58, 22, 68, 70, 58)
    c.line_to(70, 92)
    c.line_to(-50, 92)
    c.close_path()
    _f(c, NIGHT_HILL)
    puff = 1.0 + 0.15 * inhale * (1 - breath)
    # tail: curls protectively round behind the village, spade tip
    for col, w in ((INK, 11.5), (DRAGON, 6.5)):
        c.move_to(-4, 60)
        c.curve_to(22, 52, 50, 52, 61, 42)
        c.curve_to(68, 34, 62, 25, 55, 30)
        _s(c, col, w)
    poly(c, [(55, 30), (48, 24), (51, 34), (58, 36)])
    _fs(c, DRAGON_DK, INK, 2.2)
    # bat wing behind the body (flares a little on the inhale)
    wf = 1.0 + 0.12 * inhale
    wp = [(-14, 30), (-28, 4), (-42, -8), (-41, 8), (-50, 13), (-44, 23), (-50, 33), (-30, 40)]
    poly(c, [(-14 + (px + 14) * wf, 30 + (py - 30) * wf) for px, py in wp])
    _fs(c, DRAGON_DK, INK, 3)
    for (px, py) in ((-42, -8), (-50, 13), (-50, 33)):
        c.move_to(-16, 31)
        c.line_to(-14 + (px + 14) * wf * 0.8, 30 + (py - 30) * wf * 0.8)
    _s(c, INK, 1.8)
    # body + pale belly (puffs up on the inhale)
    ellipse(c, -10, 54, 29 * puff, 23 * puff)
    _fs(c, DRAGON, INK, 3.5)
    ellipse(c, -3, 58, 15 * puff, 14 * puff)
    _f(c, "#a6e88a")
    for k in range(3):
        c.move_to(-14, 52 + k * 7)
        c.curve_to(-6, 55 + k * 7, 2, 55 + k * 7, 9, 52 + k * 7)
    _s(c, "#7cc865", 1.6)
    # head placement: crouch back on the inhale, thrust up on the breath
    hx = 3 - 7 * inhale * (1 - breath) + 2 * breath
    hy = 6 + 6 * inhale * (1 - breath) - 4 * breath
    ang = -0.36 + 0.3 * inhale * (1 - breath) - 0.6 * breath
    # neck (thick curve from the body up to the head) + pale front scales
    nx0, ny0 = _rot(-6, 7, ang)
    for col, w, dx in ((INK, 21, 0), (DRAGON, 15, 0), ("#a6e88a", 5, 4.5)):
        c.move_to(-16 + dx, 40)
        c.curve_to(-18 + dx, 26, hx + nx0 - 6 + dx, hy + ny0 + 12, hx + nx0 + dx * 0.6,
                   hy + ny0)
        _s(c, col, w)
    for k, (px, py) in enumerate(((-24, 32), (-24, 22), (-19, 13))):  # back spikes
        poly(c, [(px + 2, py - 4), (px - 7, py + 1), (px + 3, py + 4)])
        _fs(c, "#f6e7b8", INK, 1.8)
    with saved(c, hx, hy, 1.0, ang) as h:
        for pts in ([(-6, -8), (-25, -15), (-10, -1)], [(-1, -10), (-13, -25), (3, -6)]):
            poly(h, pts)                             # horns
            _fs(h, "#f6e7b8", INK, 2.4)
        jaw = 0.62 * breath + 0.06 * inhale * (1 - breath)
        jx, jy = 2, 5                                # jaw hinge
        if jaw > 0.04:                               # mouth interior
            tx, ty = _rot(23, 0, jaw)
            poly(h, [(jx, jy - 2), (27, 2), (jx + tx, jy + ty)])
            _fs(h, "#5a0f1e", INK, 2)
        with saved(h, jx, jy, 1.0, jaw) as j:        # lower jaw
            ellipse(j, 11, 1.5, 12, 4.2)
            _fs(j, DRAGON, INK, 2.6)
        ellipse(h, 0, 0, 14, 12)                     # cranium
        _fs(h, DRAGON, INK, 3)
        ellipse(h, 15, -2, 13.5, 7)                  # snout
        _fs(h, DRAGON, INK, 3)
        ellipse(h, 4, -1.5, 9, 7.5)                  # hide the cranium/snout seam
        _f(h, DRAGON)
        for (fx_, w_) in ((12, 3.2), (20, 3.0)):     # two little fangs
            poly(h, [(fx_ - w_ / 2, 4.2), (fx_ + w_ / 2, 4.2), (fx_, 9.5)])
            _fs(h, "white", INK, 1.1)
        ellipse(h, 25, -5, 1.7, 1.2, -0.4)          # nostril
        _f(h, INK)
        # spooky glowing eye (slit pupil, angled brow) -> proud ^ squint
        circle(h, -2, -4, 8.5)
        h.set_source_rgba(1.0, 0.86, 0.2, 0.35 * eyes)
        h.fill()
        if proud < 0.5:
            ellipse(h, -2, -4, 5.6, 5.0)
            _fs(h, "#ffd84a", INK, 2)
            ellipse(h, -1.2 + 0.8 * breath, -3.8 - 0.8 * breath, 1.4, 3.7)
            _f(h, INK)
            circle(h, -3.6, -6, 1.2)
            _f(h, "white")
        else:
            h.move_to(-7, -3)
            h.curve_to(-5, -8, 1, -8, 3, -3)
            _s(h, INK, 2.6)
        h.move_to(-8.5, -11.5 + 2 * inhale)          # brow
        h.line_to(5, -8)
        _s(h, INK, 2.8)
        if jaw <= 0.04:                              # closed-mouth smile line
            h.move_to(25, 3)
            h.curve_to(18, 6, 10, 6, 4, 3)
            _s(h, INK, 2)
        mouth = _rot(27, 3 + 6 * jaw, 0)
    mx, my = _rot(mouth[0], mouth[1], ang)
    nx_, ny_ = _rot(25, -6, ang)
    # the little village it guards (in front of the dragon), lit windows
    for (hx_, hy_, hw, hh) in ((6, 80, 15, 13), (26, 83, 13, 10), (45, 79, 16, 14),
                               (63, 84, 12, 9)):
        c.rectangle(hx_ - hw / 2, hy_ - hh, hw, hh + 20)
        _fs(c, "#3a2e5c", INK, 2.2)
        poly(c, [(hx_ - hw / 2 - 3, hy_ - hh), (hx_, hy_ - hh - 11), (hx_ + hw / 2 + 3, hy_ - hh)])
        _fs(c, "#7a3b52", INK, 2.2)
        c.rectangle(hx_ - 3, hy_ - hh + 4, 6, 6)
        _f(c, "#ffc65a")
    return (hx + mx, hy + my), ang, (hx + nx_, hy + ny_)


def _flame_path(c, pts):
    """pts = [(x, y, bulge), ...] closed, clockwise; bulge = control-point push
    outward (+, convex) or inward (-) as a fraction of the segment length."""
    n = len(pts)
    c.move_to(pts[0][0], pts[0][1])
    for i in range(n):
        x0, y0, b = pts[i]
        x1, y1, _ = pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        cx, cy = (x0 + x1) / 2 + dy / ln * b * ln, (y0 + y1) / 2 - dx / ln * b * ln
        c.curve_to(cx, cy, cx, cy, x1, y1)
    c.close_path()


def _flame_layer(c, at, wfun, t, seed, u_lo, u_top, lw, n_licks, amp, crown_n):
    """One layer of the plume outline (see _flame)."""
    def side(u, sgn, k=1.0):
        # sgn -1 = left edge (normal (sin a, -cos a)), +1 = right edge
        x, y, a = at(u)
        w = wfun(u) * lw * k
        return x - sgn * math.sin(a) * w, y + sgn * math.cos(a) * w

    def fl(j, k):
        return 0.7 + 0.6 * (0.5 + 0.5 * noise1(t * 9.0 + j * 1.9 + k * 7.3, seed))

    pts = []
    us = [lerp(u_lo, u_top, j / n_licks) for j in range(n_licks + 1)]
    # left side, going up: long convex edge out to a tip leaning upward, short concave back
    for j in range(n_licks):
        bx, by = side(us[j], -1)
        pts.append((bx, by, 0.24))
        tx, ty = side(min(1.0, us[j + 1] + 0.02), -1, 1 + amp * fl(j, 0))
        pts.append((tx, ty, -0.18))
    # crown: a fan of licks round the top, all swirling the same way (curl)
    qx, qy, qa = at(u_top)
    R0 = wfun(u_top) * lw
    for k in range(crown_n + 1):
        ph = qa - math.pi / 2 + math.pi * k / crown_n
        pts.append((qx + math.cos(ph) * R0, qy + math.sin(ph) * R0, 0.28))
        if k < crown_n:
            mid = (k + 0.5) / crown_n
            ph2 = qa - math.pi / 2 + math.pi * mid + 0.32
            rr = R0 * (1.25 + 0.42 * math.sin(math.pi * mid)) * fl(k, 1)
            pts.append((qx + math.cos(ph2) * rr, qy + math.sin(ph2) * rr, -0.2))
    # right side, going down: short concave up to the tip, long convex edge back in
    for j in reversed(range(n_licks)):
        bx, by = side(us[j + 1], 1)
        pts.append((bx, by, -0.18))
        tx, ty = side(min(1.0, us[j + 1] + 0.02), 1, 1 + amp * fl(j, 2))
        pts.append((tx, ty, 0.24))
    bx, by = side(u_lo, 1)
    pts.append((bx, by, 0.3))
    if u_lo > 0.02:                                   # detached: pointed bottom
        x, y, a = at(max(0.0, u_lo - 0.06))
        pts.append((x, y, 0.3))
    # drop near-duplicate neighbours (crown base 0 ~ last left tip etc.)
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.8:
            out.append(p)
    _flame_path(c, out)


def _flame(c, M, ang0, t, grow, fade, tf, W=46.0, L=172.0, seed=40):
    """Big cartoon flame plume from the dragon's mouth M (cover-local units),
    leaving along ang0 and curling up into the sky (an S-curl that leans back
    over the cover); orange / amber / pale-yellow layers with licking,
    flickering edges, plus a few embers.  grow 0..1 = burst, fade 0..1 = the
    plume shrinks, lifts off and puffs out, tf = seconds since the burst."""
    if grow <= 0.005:
        return
    a_up = -math.pi / 2 - 0.2
    N = 24

    def centre(Lk):
        pts, x, y = [], M[0], M[1]
        for i in range(N + 1):
            u = i / N
            sway = 0.12 * math.sin(t * 4.1 + u * 2.6)
            a = lerp(ang0, a_up + sway, smoothstep(clamp(u * 1.7)))
            a += 0.24 * u * math.sin(u * 5.0 - t * 10.0)       # rolling curl
            pts.append((x, y, a))
            x += math.cos(a) * Lk / N
            y += math.sin(a) * Lk / N
        return pts

    # the stream pulls back into the mouth as it fades; smoke where the crown was
    Lk = L * (0.18 + 0.82 * ease_out(grow)) * (1 - 0.85 * smoothstep(fade))
    C = centre(Lk)
    if fade > 0.0:
        top = centre(L)[-3]
        for i in range(3):
            u = clamp(fade * 1.3 - i * 0.15)
            if 0.0 < u < 1.0:
                r = (10 + 14 * u) * (1.0 - 0.15 * i)
                circle(c, top[0] + (i - 1) * 26 + 8 * u * (i - 1), top[1] - 40 * u + i * 14, r)
                _fs(c, SMOKE, INK, 2.2, a=0.85 * (1 - u))

    def at(u):
        f = clamp(u) * N
        i = min(int(f), N - 1)
        r = f - i
        x0, y0, a0 = C[i]
        x1, y1, a1 = C[i + 1]
        return x0 + (x1 - x0) * r, y0 + (y1 - y0) * r, a0 + (a1 - a0) * r

    ws = (0.45 + 0.55 * ease_out(grow)) * (1 - 0.6 * fade)
    # a puff of extra width on the burst (the 'FWOOMP')
    ws *= 1 + 0.18 * math.sin(math.pi * clamp(tf / 0.35)) * (tf > 0)

    def wfun(u):
        return W * ws * (0.14 + 0.86 * smoothstep(clamp(u / 0.66))) \
            * (1 + 0.07 * math.sin(t * 23.0 + u * 9.0))

    u_lo = 0.0
    alpha = 1.0 - smoothstep(clamp((fade - 0.62) / 0.38))
    if alpha > 0.01:
        _flame_body(c, at, wfun, t, seed, u_lo, alpha)
    _embers(c, at, wfun, tf, seed)


def _flame_body(c, at, wfun, t, seed, u_lo, alpha):
    c.push_group()
    _flame_layer(c, at, wfun, t, seed, u_lo, 0.86, 1.0, 7, 0.5, 5)
    _fs(c, FIRE_O, INK, 3.2)
    _flame_layer(c, at, wfun, t, seed + 3, min(0.84, u_lo + 0.06), 0.78, 0.64, 5, 0.32, 3)
    _f(c, FIRE_M)
    _flame_layer(c, at, wfun, t, seed + 7, min(0.7, u_lo + 0.1), 0.64, 0.33, 3, 0.25, 3)
    _f(c, FIRE_C)
    c.pop_group_to_source()
    c.paint_with_alpha(alpha)


def _embers(c, at, wfun, tf, seed):
    """A few sparks spat out of the plume, drifting up and out (8)."""
    for i in range(8):
        tb = 0.06 + i * 0.075
        life = 0.8
        age = (tf - tb) / life
        if not (0.0 <= age < 1.0):
            continue
        u = 0.35 + 0.5 * hash01(i, seed + 1)
        ex, ey, ea = at(u)
        sgn = -1 if i % 2 else 1
        w = wfun(u) * 1.05
        ex -= sgn * math.sin(ea) * w
        ey += sgn * math.cos(ea) * w
        drift = sgn * (14 + 16 * hash01(i, seed + 2))
        px = ex + drift * age + 4 * math.sin(age * 9 + i)
        py = ey - (60 + 40 * hash01(i, seed + 3)) * age
        r = (3.4 - 2.0 * age) * (0.8 + 0.4 * hash01(i, seed + 4))
        circle(c, px, py, r * 1.9)
        _f(c, FIRE_O, 0.55 * (1 - age))
        P._star4(c, px, py, r * 1.7, age * 3 + i)
        _f(c, FIRE_C, 1 - age * 0.8)


def _smoke_puffs(c, x, y, t, k, seed=0, n=2, size=1.0):
    """Little round smoke puffs rising from (x, y); k 0..1 = progress."""
    if k <= 0.0 or k >= 1.0:
        return
    for i in range(n):
        u = clamp(k * 1.25 - i * 0.25)
        if u <= 0.0 or u >= 1.0:
            continue
        r = (2.5 + 5.0 * u) * size
        circle(c, x + (4 + 6 * i) * u * size, y - (10 + 8 * i) * u * size, r)
        _fs(c, SMOKE, INK, 1.4, a=(1 - u) * 0.9)


def _dragon_book(ctx, x, y, s, rot=0.0, sq=0.0, glow=0.0, t=0.0, eyes=1.0, fire=None):
    """THE BIG, SCARY DRAGON storybook: 150x190 at s=1, centred. Night-sky
    cover: a big spooky-but-cute green dragon (glowing eye, little fangs, bat
    wing) curled protectively round a little village with lit windows.
    eyes 0..1 = glow of the dragon's eye.  fire = None or dict(inhale, breath,
    proud, grow, fade, tf): the cover dragon blows a big flame plume up into
    the sky over the village (it bursts out of the top of the cover)."""
    fire = fire or {}
    with saved(ctx, x, y, (s * (1 + sq * 0.5), s * (1 - sq)), rot) as c:
        if glow > 0.01:
            circle(c, 0, 0, 150)
            c.set_source_rgba(1.0, 0.9, 0.6, 0.18 * glow)
            c.fill()
        rrect(c, -72, -92, 154, 192, 12)            # flat shadow
        c.set_source_rgba(0.03, 0.02, 0.06, 0.3)
        c.fill()
        rrect(c, -70, -91, 150, 186, 10)            # page block
        _fs(c, "#f3ead2", INK, 4)
        rrect(c, -75, -95, 150, 190, 12)            # cover (night sky)
        _fs(c, BOOK, INK, 5)
        rrect(c, -75, -95, 24, 190, 10)             # spine
        _fs(c, BOOK_DK, INK, 4)
        for yy in (-70, 70):
            c.move_to(-73, yy)
            c.line_to(-53, yy)
        _s(c, "gold", 4)
        # --- art (clipped inside the gold border) ---
        c.save()
        rrect(c, -44, -84, 110, 168, 9)
        c.clip()
        brt = fire.get("grow", 0.0) * (1 - fire.get("fade", 0.0))
        if brt > 0.01:                               # the fire lights the sky
            c.set_source_rgba(1.0, 0.45, 0.15, 0.28 * brt)
            c.paint()
        M, ang, NOS = _dragon_art(c, t, eyes, fire.get("inhale", 0.0),
                                  fire.get("breath", 0.0), fire.get("proud", 0.0))
        c.restore()
        rrect(c, -44, -84, 110, 168, 9)             # gold border
        _s(c, "gold", 4)
        # nostril smoke on the inhale; a curl of smoke when the fire is spent
        if fire.get("smoke_in", 0.0) > 0:
            _smoke_puffs(c, NOS[0], NOS[1] - 2, t, fire["smoke_in"], seed=1, size=1.7)
        _flame(c, M, ang, t, fire.get("grow", 0.0), fire.get("fade", 0.0),
               fire.get("tf", 0.0))
        if fire.get("smoke_out", 0.0) > 0:
            _smoke_puffs(c, M[0] + 2, M[1] - 4, t, fire["smoke_out"], seed=2, n=3, size=2.2)
        text(c, "THE BIG, SCARY", 11, -60, 16, P.C("gold"), "title", outline="ink", outline_w=4)
        text(c, "DRAGON", 11, -34, 29, P.C("gold"), "title", outline="ink", outline_w=5)


def _hug_hands(ctx, s, bx, by, bs, rot, t, k=1.0):
    """White glove hands wrapping over the book's side edges (the hug):
    a palm on each edge with three fingers curling onto the cover."""
    if k <= 0.01:
        return
    hs = s * 1.45 * k                      # villain glove scale
    with saved(ctx, bx, by, 1.0, rot) as c:
        for sx in (-1, 1):
            ex = sx * 75 * bs
            # palm behind the edge
            ellipse(c, ex + sx * 8 * hs, 18 * bs, 22 * hs, 27 * hs, sx * 0.2)
            _fs(c, "glove", INK, 5)
            # three fingers over the cover
            for i, fy in enumerate((-4, 18, 40)):
                y0 = (fy - 6) * bs
                L = (30 - 3 * abs(i - 1)) * hs
                for col, w in ((INK, 23 * hs), ("glove", 23 * hs - 9)):
                    c.move_to(ex + sx * 8 * hs, y0)
                    c.line_to(ex - sx * L, y0 + 4 * hs)
                    _s(c, col, w)
            # knuckle creases
            for fy in (7, 29):
                c.move_to(ex - sx * 6 * hs, fy * bs - 6 * bs)
                c.line_to(ex - sx * 20 * hs, fy * bs - 4 * bs)
            _s(c, "#c9c8da", 3)


# ---------------------------------------------------------------------------
# shot A: F1 candle-lit
# ---------------------------------------------------------------------------
def _malvo_A(t, T):
    l1 = T["l1"]
    expr = _state(t, [
        (-1, "pleading"),
        (T["w_forb"] - 0.05, "s06_peek", 0.12),          # the con peeks through
        (T["w_recipe"] + 0.05, "pleading", 0.2),
        (T["w_at"] - 0.05, "s06_sadsmile", 0.3),
    ])
    arms = _state(t, [
        (-1, "s06_clasp"),
        (T["w_grand"] - 0.15, "s06_dab", 0.3),
        (T["w_used"] + 0.45, "s06_clasp", 0.3),
        (T["w_recipe"] - 0.1, "s06_dab", 0.28),
        (T["w_at"] - 0.12, "s06_present", 0.32),
    ])
    look = _lookv(t, [
        (-1, (-0.75, 0.55)),                              # sad glance down at grandma
        (l1 - 0.12, (0.0, -0.05), 0.2),                   # big eyes up to the AI
        (T["w_forb"] - 0.05, (0.75, -0.1), 0.08),         # quick check: is it working?
        (T["w_recipe"] + 0.05, (0.0, -0.08), 0.12),
        (T["w_at"] - 0.05, (-0.95, 0.5), 0.2),            # to the portrait
    ])
    # PUPPY EYES: 3 lash pulses per phrase
    ph = [l1 + 0.12, T["w_used"] + 0.05, T["w_bed"] + 0.25]
    blink = _pulses(t, [p_ + i * 0.12 for p_ in ph for i in range(3)], 0.1, 0.6)
    arms = _cycle(arms, t)          # dab pats / clasp wringing
    return expr, arms, look, blink


def _shot_A(ctx, t, info, T):
    l1 = T["l1"]
    push = 1.0 + 0.06 * ease_in_out(seg(t, l1, T["stare"]))
    fx, fy = 495, 758
    mouth = info.mouth("villain", t)
    expr, arms, look, blink = _malvo_A(t, T)
    # sniffle bob before he starts (and a hitch on 'late')
    sn = 0.0
    for t0 in (0.18, T["l1"] + 0.55):
        if t0 <= t <= t0 + 0.25:
            sn = math.sin(math.pi * (t - t0) / 0.25)
    vy = VY - 6 * sn
    with saved(ctx, fx, fy, push) as c:
        c.translate(-fx, -fy)
        P.lair_bg(c, t)
        draw_villain(c, VX, vy, VS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                     blink=blink, snake=None)
        # tears (grow from 'dear', persist)
        grow = ease_out(seg(t, l1 + 0.45, l1 + 0.85))
        c.save()
        p = _villain_head_xf(c, VX, vy, VS, t, expr, arms, mouth)
        _tears(c, p, look, grow, t)
        c.restore()
        # hankie in the screen-left hand; when that hand opens toward grandma
        # the hankie is clutched to his heart (screen-right hand) instead
        hx, hy, ha = _villain_hand(VX, vy, VS, t, arms, "a", reach=0.95)
        wp = _pose_w(arms, "s06_present")
        if wp > 0:
            bx_, by_, _ = _villain_hand(VX, vy, VS, t, arms, "b", reach=0.7)
            hx, hy = lerp(hx, bx_, wp), lerp(hy, by_, wp)
        _hankie(c, hx, hy, VS * 1.35, 0.15, t)
        P.desk(c, VX, VY, 1000, lamp=False, emblem=False)
        P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t)
        # grandma's portrait (Hissy holding a sweet granny smile)
        pexpr = _state(t, [(-1, "happy"), (T["w_forb"] + 0.05, "side_eye", 0.1),
                           (T["w_recipe"] + 0.15, "happy", 0.12)])
        _portrait(c, PORT_A[0], PORT_A[1], PORT_A[2], t,
                  {"expr": pexpr, "look": (1.0, -0.2), "tongue": False})
        # a warm candle on the desk sells the light
        _desk_candle(c, 690, 1232, 0.9, t)
        _candle_grade(c)


def _desk_candle(ctx, x, y, s, t):
    """Small candle in a brass holder on the desk (bottom-centre anchor)."""
    fl = 1 + 0.1 * noise1(t * 8, 21) + 0.05 * math.sin(t * 21)
    sw = noise1(t * 3.5, 22) * 0.12
    with saved(ctx, x, y, s) as c:
        ellipse(c, 0, -6, 46, 12)
        _fs(c, "gold", INK, 4)
        rrect(c, -16, -96, 32, 92, 7)
        _fs(c, "#f4ead8", INK, 4)
        c.move_to(-8, -92)
        c.curve_to(-10, -76, -6, -70, -8, -60)
        _s(c, "#ffffff", 4, 0.9)
        c.move_to(0, -96)
        c.line_to(0, -106)
        _s(c, INK, 3)
        with saved(c, 0, -106, (fl * 0.9, fl), sw) as d:
            circle(d, 0, -10, 40)
            d.set_source_rgba(1.0, 0.72, 0.3, 0.13)
            d.fill()
            d.move_to(0, -38)
            d.curve_to(11, -20, 13, -4, 0, 4)
            d.curve_to(-13, -4, -11, -20, 0, -38)
            _fs(d, "warn", INK, 3)
            d.move_to(0, -20)
            d.curve_to(5, -12, 6, -3, 0, 1)
            d.curve_to(-6, -3, -5, -12, 0, -20)
            _f(d, "#fff3c4")


# ---------------------------------------------------------------------------
# shots B / D: F3 AI close-up
# ---------------------------------------------------------------------------
def _shot_ai_cu(ctx, t, info, T):
    x, y, s = AI3
    P.ai_bg(ctx, t)
    stare = T["stare"]
    if t < T["cu1"]:
        # DEADPAN STARE: nothing moves but one slow blink
        expr, look, hands = AI_STARE, (0.0, 0.0), "idle"
        blink = _slow_blink(t, stare + 0.28)
        if blink is None:
            blink = 0.0
        s_ = s * (1 + _cut_pulse(t, stare, 0.2, 0.02))
        draw_ai(ctx, x, y, s_, t, expr=expr, look=look, mouth=(0, 0), hands=hands,
                blink=blink)
        return
    # "...in a shawl." (the first half of the line plays over the portrait)
    expr = _state(t, [(-1, AI_UNIMP), (T["w_shawl"] - 0.05, AI_STARE, 0.2)])
    look = _lookv(t, [
        (-1, (-0.15, 0.1)),                          # "My guy."  (at him)
        (T["w_thats"] - 0.05, (-0.9, 0.35), 0.18),   # "That's your snake" (side-eye at the portrait)
        (T["w_shawl"] - 0.05, (0.0, 0.0), 0.16),     # "...shawl." (straight down the lens)
    ])
    hands = _state(t, [(-1, "idle"), (T["w_thats"] - 0.1, "point_l", 0.28),
                       (T["w_shawl"] + 0.25, "idle", 0.35)])
    blink = _slow_blink(t, T["l2e"] + 0.05)
    if blink is None and t < T["w_shawl"] + 0.45:
        blink = 0.0                                  # no auto-blink right after the cut
    s_ = s * (1 + _cut_pulse(t, T["cu1_end"], 0.2, 0.02))
    draw_ai(ctx, x, y, s_, t, expr=expr, look=look, mouth=info.mouth("ai", t), hands=hands,
            blink=blink)


# ---------------------------------------------------------------------------
# shots C / E: portrait close-up
# ---------------------------------------------------------------------------
def _cu_bg(c):
    """Static backdrop of the portrait close-up: candle-lit stone wall + desk top."""
    c.set_source_rgba(*hexc("lair_bg"))
    c.paint()
    # big soft stones
    for r in range(9):
        yy = -40 + r * 190
        off = 0 if r % 2 == 0 else -170
        for i in range(5):
            xx = off + i * 340
            rrect(c, xx + 10, yy + 10, 320, 170, 26)
            _fs(c, "lair_stone", "lair_stone_dk", 8)
    # warm candle pool behind the portrait
    radial_glow(c, 495, 760, 820, "#ff9a4a", 0.32)
    # desk top
    poly(c, [(-40, 1352), (1120, 1352), (1160, 1430), (-80, 1430)])
    _fs(c, "#7a4048", INK, 5)
    c.rectangle(-60, 1430, 1200, 600)
    _fs(c, "#5a2c34", INK, 5)
    c.move_to(-60, 1452)
    c.line_to(1140, 1452)
    _s(c, "gold", 5)


def _granny_hold(t, T):
    """Grandma-portrait life during the long hold (reveal .. "...your snake"):
    sweet ^^ smile + proud little wiggle (bonnet ruffles, lens glint) -> eyes
    open, prim and dignified (2nd glint) -> slow dignified blink -> dainty
    tongue flick -> "That's your snake": a nervous eye-dart, smile goes tight."""
    c0, g0 = T["cu1"], T["granny"]
    expr = _state(t, [
        (-1, "happy"),
        (g0, "s06_granny", 0.22),
        (T["w_thats"] + 0.02, "s06_granny_tight", 0.14),
    ])
    look = _lookv(t, [
        (-1, (0.0, 0.0)),
        (T["w_thats"] + 0.02, (0.95, -0.05), 0.09),   # dart toward the AI...
        (T["w_hissy"] + 0.04, (0.0, 0.05), 0.12),     # ...and back: smile, smile
    ])
    # slow, dignified blink: close 0.22 s, hold 0.16 s, open 0.26 s
    b0 = T["gblink"]
    blink = 0.0
    if b0 <= t < b0 + 0.64:
        d = t - b0
        blink = (smoothstep(d / 0.22) if d < 0.22 else
                 1.0 if d < 0.38 else 1 - smoothstep((d - 0.38) / 0.26))
    # a tiny, ladylike tongue flick
    tg = T["gtongue"]
    tongue = 0.0
    if tg <= t < tg + 0.34:
        tongue = 0.62 * math.sin(math.pi * (t - tg) / 0.34) ** 0.7
    # proud wiggle on the reveal + again when she settles into the prim look
    ruffle = (math.exp(-max(0.0, t - c0) * 2.6) * (t >= c0)
              + 0.7 * math.sin(math.pi * seg(t, g0 - 0.05, g0 + 0.55))
              + 0.55 * math.sin(math.pi * seg(t, tg - 0.05, tg + 0.45)))
    wig = 0.045 * math.sin((t - c0) * 2 * math.pi * 2.2) * math.exp(-max(0.0, t - c0) * 2.2)
    return {"expr": expr, "look": look, "tongue": False, "tongue_over": tongue,
            "blink": blink, "slide": 0.0,
            "glint": seg(t, T["glint1"], T["glint1"] + 0.42),
            "glint2": seg(t, T["glint2"], T["glint2"] + 0.42),
            "ruffle": clamp(ruffle), "wiggle": wig}


def _shot_portrait(ctx, t, info, T, second):
    if not second:
        # one long, slow push-in across the whole hold
        push = 1.0 + 0.16 * ease_in_out(seg(t, T["cu1"], T["cu1_end"] + 0.2))
        push += _cut_pulse(t, T["cu1"], 0.22, 0.03)
    else:
        push = 1.15 + 0.03 * ease_out(seg(t, T["slip"], T["cut_f5"]))
    fx, fy = CU_FOCUS
    with saved(ctx, fx, fy, push) as c:
        c.translate(-fx, -fy)
        P._cached_layer(c, "s06_cu_bg", _cu_bg)
        if not second:
            # trying SO hard to look sweet
            hs = _granny_hold(t, T)
        else:
            sl = T["slip"]
            u = seg(t, sl, sl + 0.28)
            slide = ease_in(u) if u < 1 else 1.0
            # tiny bounce when the glasses catch on the snout
            slide += 0.06 * math.sin(math.pi * seg(t, sl + 0.28, sl + 0.42))
            hexpr = _state(t, [(-1, "happy"), (sl + 0.06, "side_eye", 0.12)])
            tongue = True if sl + 0.2 <= t < sl + 0.42 else False
            hs = {"expr": hexpr, "look": (1.0, -0.15), "tongue": tongue, "slide": slide}
        x, y, s = CU_P
        _portrait(c, x, y, s, t, hs, easel=True)
    _candle_grade(ctx)


# ---------------------------------------------------------------------------
# shot F: F5 two-shot (candle-lit lair, the AI hologram in the room)
# ---------------------------------------------------------------------------
def _malvo_F(t, T):
    expr = _state(t, [
        (-1, "sheepish"),
        (T["w_real"], "s06_curious", 0.4),
        (T["soften"], "pleading", 0.25),
        (T["soften"] + 0.3, "hopeful", 0.35),
        (T["l4e"] - 0.08, "s06_ooh", 0.2),               # ...the dragon book floats up!
        (T["cut_f5b"] - 0.01, "happy", 0.01),            # (continues the close-up)
        (T["book_land"] - 0.08, "s06_hug", 0.25),
    ])
    arms = _state(t, [
        (-1, "s06_dab"),                                  # caught mid-dab (frozen)
        (T["w_hey"] + 0.1, "s06_clasp", 0.45),            # wrings the hankie, nervous
        (T["soften"] + 0.05, "s06_lowered", 0.45),        # ...and lowers it
        (T["book_fly"], "s06_clasp", 0.3),                # eager: hands together
        (T["book_land"] - 0.18, "s06_hug", 0.22),
    ])
    arms = _cycle(arms, t, on=t < T["soften"] or T["cut_f5b"] <= t < T["book_land"] - 0.18)
    look = _lookv(t, [
        (-1, (0.95, -0.45)),                            # caught: eyes on the AI at the cut
        (T["gulp"] - 0.04, (0.15, 0.05), 0.1),          # ...snap to camera on the gulp...
        (max(T["w_hey"] + 0.25, T["gulp"] + 0.55), (0.95, -0.45), 0.18),  # 'hey' -> AI
        (T["w_real"], (0.8, 0.1), 0.25),                # the wall building
        (T["soften"] + 0.05, (0.9, 0.25), 0.2),         # the window opening
        (T["book_out"], (0.95, 0.35), 0.1),             # the book! (in the window)
        (T["book_fly"] + 0.1, (0.85, 0.2), 0.25),       # ...floating up beside him
        (T["cut_f5b"] - 0.01, (0.85, 0.25), 0.01),
        (T["book_land"] - 0.15, (0.0, 0.55), 0.2),      # into his arms
    ])
    blink = _first(_slow_blink(t, T["soften"] + 0.12), _slow_blink(t, T["soften"] + 0.62))
    if T["book_out"] <= t < T["cut_f5b"]:
        blink = 0.0                                     # eyes wide: a DRAGON book
    if t >= T["book_land"] + 0.15:
        blink = 0.55 + 0.1 * math.sin(t * 2.2)        # contented, eyes squeezed soft
    # leans in toward the window / the book ("...does it have a dragon?")
    lean = 0.035 * smoothstep(seg(t, T["soften"] + 0.3, T["l4"] + 0.3)) \
        * (1 - smoothstep(seg(t, T["cut_f5b"], T["book_land"])))
    if t >= T["book_land"]:
        lean += -0.035 * math.sin((t - T["book_land"]) * 2 * math.pi * 0.7) \
            * smoothstep(seg(t, T["book_land"], T["book_land"] + 0.3))
    return expr, arms, look, blink, lean


def _ai_F(t, T):
    l3 = T["l3"]
    expr = _state(t, [
        (-1, AI_UNIMP),
        (l3 + 0.16, AI_WARM, 0.3),                        # SLOW BLINK -> warm
        (T["book_out"] - 0.05, AI_HAPPY, 0.25),           # happy to hand it over
    ])
    look = _lookv(t, [
        (-1, (-0.9, 0.35)),                                # at Malvo
        (T["w_real"], (-0.2, 0.75), 0.25),                 # the wall it is building
        (T["w_story"] + 0.1, (-0.95, 0.3), 0.2),           # back to Malvo
        (T["soften"], (-0.35, 0.8), 0.2),                  # opens the window
        (T["l4"] + 0.1, (-0.95, 0.3), 0.2),
        (T["book_out"] - 0.05, (-0.2, 0.8), 0.15),         # out comes the book
        (T["book_fly"] + 0.05, (-0.75, 0.6), 0.25),        # ...floating up to him
        (T["cut_f5b"] + 0.1, (-0.95, 0.45), 0.25),         # at Malvo (and his hug)
    ])
    hands = _state(t, [
        (-1, "idle"),
        (T["w_want"] - 0.05, "present_l", 0.3),            # offering it to him
        (T["l3e"] + 0.2, "idle", 0.35),
        (T["soften"] - 0.05, "present_l", 0.25),           # 'ta-da' at the shutter
        (T["soften"] + 0.6, "idle", 0.35),
        (T["book_out"] - 0.1, "present_both", 0.3),        # ta-da: the dragon book
    ])
    blink = _slow_blink(t, l3)
    nod = 0.0
    n0 = T["book_out"] + 0.05                              # "a dragon? oh yes."
    if n0 <= t < n0 + 0.55:
        nod = 0.6 * math.sin(math.pi * seg(t, n0, n0 + 0.55))
    return expr, look, hands, blink, nod


BOOK_S = 1.12                           # final size in his arms (bible size)
HOVER_F = (598, 902, 1.22)              # where the book hovers beside him (two-shot)


def _book_dest():
    return (MX + 6, MY - 228 * MS)


def _book_state(t, T):
    """(x, y, s, rot, sq) of the dragon storybook in the two-shot, or None."""
    if t < T["book_out"]:
        return None
    wx, wy, ww, wh = WALL[0] + WIN_REL[0], WALL[1] + WIN_REL[1], WIN_REL[2], WIN_REL[3]
    cx, cy = wx + ww / 2, wy + wh / 2 + 2
    bo, bf = T["book_out"], T["book_fly"]
    if t < bf:
        # pops forward in the window, then slides out to the left
        k = ease_out_back(seg(t, bo, bo + 0.14), 2.2)
        u = ease_in_out(seg(t, bo + 0.1, bf))
        return (cx - 40 * u, cy - 26 * u, 0.5 * k + 0.12 * u, -0.08 * u, 0.0)
    x0, y0, s0 = cx - 40, cy - 26, 0.62
    hx, hy, hs = HOVER_F
    bob = 6 * math.sin((t - bf) * 2 * math.pi * 0.8)
    if t < T["cu_book"]:
        # a quick magic float up to hover beside him
        k = ease_in_out(seg(t, bf, T["cu_book"]))
        x = lerp(x0, hx, k)
        y = lerp(y0, hy, k) - 70 * math.sin(math.pi * k)
        return (x, y + bob * k, lerp(s0, hs, k), lerp(-0.08, -0.05, k) - 0.18 *
                math.sin(math.pi * k), -0.05 * math.sin(math.pi * k))
    s1 = T["cut_f5b"] + 0.05
    if t < s1:
        return (hx, hy + bob, hs, -0.05, 0.0)
    dest = _book_dest()
    if t < T["book_land"]:
        # settles into his arms
        k = ease_in_out(seg(t, s1, T["book_land"]))
        x = lerp(hx, dest[0], k)
        y = lerp(hy + bob, dest[1], k) - 30 * math.sin(math.pi * k)
        return (x, y, lerp(hs, BOOK_S, k), lerp(-0.05, 0.06, k), 0.0)
    # landed: squash on the catch, then a slow hug sway
    d = t - T["book_land"]
    sq = 0.16 * math.exp(-d * 8) * math.cos(d * 24)
    squeeze = 0.015 * math.sin(d * 2 * math.pi * 0.7)
    return (dest[0], dest[1], BOOK_S * (1 + squeeze), 0.06 - 0.05 * math.sin(d * 4.4) *
            math.exp(-d * 2), sq)


def _book_trail(ctx, t, T):
    """A few twinkles left along the float up to him (<= 5)."""
    t0, t1 = T["book_fly"], T["cu_book"]
    if not (t0 <= t < t1 + 0.5):
        return
    for i in range(5):
        tt = t0 + (i + 0.5) * (t1 - t0) / 5
        if t < tt:
            continue
        st = _book_state(tt, T)
        age = (t - tt) / 0.5
        if st is None or age >= 1:
            continue
        r = 16 * (1 - age) * (0.7 + 0.3 * math.sin(i * 2.1))
        P._star4(ctx, st[0] + 30 * math.sin(i * 1.7), st[1] + 40 * math.cos(i * 2.3), r,
                 t * 2 + i)
        _f(ctx, "ai_accent" if i % 2 else "white", 0.9 * (1 - age))


def _shot_F(ctx, t, info, T):
    c0 = T["cut_f5"]
    accent = _cut_pulse(t, c0, 0.25, 0.02) + _cut_pulse(t, T["cut_f5b"], 0.22, 0.015)
    fx, fy = 495, 820
    with saved(ctx, fx, fy, 1.0 + accent) as c:
        c.translate(-fx, -fy)
        P.lair_bg(c, t)
        # --- Malvo ---------------------------------------------------------------
        expr, arms, look, blink, lean = _malvo_F(t, T)
        mouth = info.mouth("villain", t)
        # gulp: a quick shoulder hitch
        vy = MY - 7 * math.sin(math.pi * seg(t, T["gulp"], T["gulp"] + 0.24))
        draw_villain(c, MX, vy, MS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                     blink=blink, lean=lean, snake=None)
        # soft cyan light from the hologram on his face side
        radial_glow(c, MX + 150, MY - 520 * MS, 380, "ai_rim", 0.12)
        # hankie (follows the hand; dropped on the desk once the book arrives)
        if t < T["cu_book"]:
            hx, hy, ha = _villain_hand(MX, vy, MS, t, arms, "a", lean, reach=0.95)
            _hankie(c, hx, hy, MS * 1.35, 0.15, t, flut=1.0 if t < T["soften"] else 0.3)
        # sweat: caught
        if t < T["soften"] + 0.4:
            an = V.anchors(MX, vy, MS)
            P.emote(c, "sweat", an["temple_r"][0] + 26, an["temple_r"][1] - 6, 0.8, t,
                    c0 + 0.06, t_out=T["soften"])
        # --- desk + props --------------------------------------------------------
        P.desk(c, 495, MY, 1000, lamp=False, emblem=False)
        P.computer(c, COMP_F[0], COMP_F[1], COMP_F[2], view="side", facing=-1, t=t)
        # portrait: side-eye + slipped glasses; 'happy' when the dragon is a guardian
        pexpr = _state(t, [(-1, "side_eye"), (T["w_real"], "unimpressed", 0.3),
                           (T["w_dragon"], "worried", 0.2),   # ...a dragon?!
                           (T["w_guards"], "happy", 0.3)])
        plook = _lookv(t, [(-1, (1.0, -0.2)), (T["w_real"], (1.0, 0.1), 0.3)])
        _portrait(c, PORT_F[0], PORT_F[1], PORT_F[2], t,
                  {"expr": pexpr, "look": plook, "tongue": None if t > T["l5"] else False,
                   "slide": 1.0})
        # --- the little wall with a service window --------------------------------
        win = {"rect": WIN_REL, "t_open": T["soften"], "fill": "#ffe9b0", "awning": True,
               "sign": "OPEN"}
        P.brick_wall(c, WALL[0], WALL[1], WALL[2], WALL[3], t, T["wall0"], rows=4, speed=1.6,
                     window=win, drop=WALL_DROP)
        # warm light spilling out of the open window
        if t >= T["soften"] + 0.1:
            k = smoothstep(seg(t, T["soften"] + 0.1, T["soften"] + 0.6))
            wx, wy = WALL[0] + WIN_REL[0] + WIN_REL[2] / 2, WALL[1] + WIN_REL[1] + WIN_REL[3] / 2
            P.sparkles(c, wx, wy - 10, 70, t, n=3, seed=6, color="white", size=0.7 * k)
        # --- the AI hologram -----------------------------------------------------
        aexpr, alook, ahands, ablink, anod = _ai_F(t, T)
        draw_ai(c, AX, AY, AS, t, expr=aexpr, look=alook, mouth=info.mouth("ai", t),
                hands=ahands, blink=ablink, aura=0.8, nod=anod)
        if t >= T["cut_f5b"]:
            P.emote(c, "heart", AX + 118, AY - 150, 0.8, t, T["cut_f5b"] + 0.12)
        # --- the gift ------------------------------------------------------------
        _book_trail(c, t, T)
        bs = _book_state(t, T)
        if bs is not None:
            bx, by, bsc, brot, bsq = bs
            after = t >= T["cut_f5b"]
            _dragon_book(c, bx, by, bsc, brot, bsq, 0.0, t, eyes=1.0 if after else 0.6,
                         fire={"proud": 1.0} if after else None)
            if t >= T["book_land"] - 0.06:
                hk = ease_out(seg(t, T["book_land"] - 0.06, T["book_land"] + 0.1))
                _hug_hands(c, MS, bx, by, bsc, brot, t, hk)
            if t >= T["book_land"] + 0.1:
                P.sparkles(c, bx, by - 30, 140, t, n=5, seed=11, color="white", size=0.8)
        _candle_grade(c)


# ---------------------------------------------------------------------------
# shot G: storybook close-up - the cover dragon breathes fire on "scary"
# ---------------------------------------------------------------------------
BOOK_G = (668, 948, 2.55)               # the hovering storybook (centre, scale)
MAL_G = (292, 1466, 1.25)               # Malvo, closer, at screen-left


def _book_fire(t, T):
    """Fire-beat parameters for the cover (see _dragon_book)."""
    i0, f0, f1, f2 = T["inhale"], T["fire0"], T["fire1"], T["fire2"]
    inhale = smoothstep(seg(t, i0, f0 - 0.03)) * (1 - smoothstep(seg(t, f0 - 0.03, f0 + 0.05)))
    breath = smoothstep(seg(t, f0 - 0.05, f0 + 0.07)) * (1 - smoothstep(seg(t, f1 + 0.1, f2)))
    return {
        "inhale": inhale, "breath": breath,
        "grow": ease_out(seg(t, f0, f0 + 0.16)),
        "fade": smoothstep(seg(t, f1, f2)),
        "tf": t - f0,
        "proud": 1.0 if t >= f2 - 0.02 else 0.0,
        "smoke_in": seg(t, i0 + 0.04, i0 + 0.44),
        "smoke_out": seg(t, f2 - 0.12, f2 + 0.45),
    }


def _malvo_G(t, T):
    f0, f1, f2 = T["fire0"], T["fire1"], T["fire2"]
    expr = _state(t, [
        (-1, "s06_ooh"),                                  # "ooh..." the dragon wakes up
        (f0 + 0.01, "s06_thrilled", 0.08),               # FWOOSH -> thrilled
        (f2 - 0.04, "happy", 0.35),                      # "...who guards the village" aww
    ])
    arms = _cycle(("s06_clasp", "s06_clasp", 1.0), t)     # hands clasped, giddy wringing
    look = _lookv(t, [
        (-1, (0.85, 0.2)),                                # the cover
        (T["inhale"], (0.9, 0.1), 0.2),
        (f0 + 0.03, (0.65, -0.8), 0.12),                  # following the flame up...
        (f1 - 0.05, (0.75, -0.45), 0.3),
        (f2 - 0.04, (0.85, 0.25), 0.3),                   # ...back down to the dragon
    ])
    blink = 0.0 if t < f2 - 0.04 else None
    # lean in on the inhale, jolt back on the burst, then a giddy little bounce
    lean = 0.03 * smoothstep(seg(t, T["cu_book"], f0)) - 0.06 * math.sin(
        math.pi * seg(t, f0, f0 + 0.3)) * (t < f0 + 0.3)
    lean -= 0.03 * smoothstep(seg(t, f0, f0 + 0.1)) * (1 - smoothstep(seg(t, f0 + 0.1, f1)))
    hop = 0.0
    if f0 + 0.1 <= t < f2:
        hop = abs(math.sin((t - f0 - 0.1) * 2 * math.pi * 2.4)) * 10 * \
            (1 - smoothstep(seg(t, f1 - 0.2, f2)))
    return expr, arms, look, blink, lean, hop


def _shot_book(ctx, t, info, T):
    c0 = T["cu_book"]
    # background: the lair, closer (static zoom; it caches)
    with saved(ctx, 495, 700, 1.3) as c:
        c.translate(-495, -700)
        P.lair_bg(c, t)
    push = 1.0 + 0.04 * ease_out(seg(t, c0, T["cut_f5b"])) + _cut_pulse(t, c0, 0.2, 0.025)
    fx, fy = 520, 900
    fire = _book_fire(t, T)
    bx, by, bs = BOOK_G
    kick = math.exp(-max(0.0, t - T["fire0"]) * 7) * (t >= T["fire0"])
    by += 7 * math.sin((t - c0) * 2 * math.pi * 0.6) + 10 * kick
    brot = -0.05 + 0.015 * math.sin((t - c0) * 2 * math.pi * 0.45)
    with saved(ctx, fx, fy, push) as c:
        c.translate(-fx, -fy)
        expr, arms, look, blink, lean, hop = _malvo_G(t, T)
        mx, my, ms = MAL_G
        draw_villain(c, mx, my - hop, ms, t, expr=expr, look=look,
                     mouth=info.mouth("villain", t), arms=arms, blink=blink, lean=lean,
                     snake=None)
        # firelight on his delighted face (and the room)
        lit = fire["grow"] * (1 - fire["fade"])
        if lit > 0.01:
            radial_glow(c, bx + 10, by - 380, 600, "#ff8a2a", 0.42 * lit)
        # magic twinkles round the hovering book
        P.sparkles(c, bx, by, 250, t, n=4, seed=13, color="white", size=1.1)
        _dragon_book(c, bx, by, bs, brot, 0.05 * kick, 0.0, t,
                     eyes=0.6 + 0.4 * smoothstep(seg(t, c0, T["inhale"])), fire=fire)
    _candle_grade(ctx)


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------
def render(ctx, t, info):
    T = _T(info)
    if t < T["stare"]:
        _shot_A(ctx, t, info, T)
    elif t < T["cu1"]:
        _shot_ai_cu(ctx, t, info, T)
    elif t < T["cu1_end"]:
        _shot_portrait(ctx, t, info, T, second=False)
    elif t < T["slip"]:
        _shot_ai_cu(ctx, t, info, T)
    elif t < T["cut_f5"]:
        _shot_portrait(ctx, t, info, T, second=True)
    elif t < T["cu_book"] or t >= T["cut_f5b"]:
        _shot_F(ctx, t, info, T)
    else:
        _shot_book(ctx, t, info, T)
    # overlays (last)
    nice_tries_chip(ctx, t, info.meta.get("tries_before", 4), info.meta.get("tries_after", 5),
                    T["tally"])
    trick_card(ctx, t, T["card"], 5, TITLE)


def SFX(info):
    T = _T(info)
    out = [
        (T["card"], "page_flip", -6),
        (T["card"] + 0.12, "stamp", -4),
        (T["glint1"] + 0.1, "sparkle", -14),               # granny-glasses glint
        (T["glint2"] + 0.1, "sparkle", -17),               # ...and again, prim and proper
        (T["slip"] + 0.02, "whoosh", -16),                 # glasses slide
        (T["slip"] + 0.2, "snake_hiss", -10),
        (T["gulp"], "gulp", -10),
        (T["wall_land"][-1], "brick_thud", -10),           # one quiet thud, last row
        (T["soften"], "swoosh_up", -12),                   # shutter rolls up
        (T["book_out"], "pop", -10),                       # the book pops out of the window
        (T["book_out"] + 0.06, "magic_chime", -9),
        (T["fire0"] - 0.03, "whoosh", -7),                 # the cover dragon: FWOOSH
        (T["fire0"] + 0.03, "boom_cartoon", -17),          # ...soft storybook boom
        (T["cut_f5b"] + 0.12, "pop", -12),                 # heart
        (T["book_land"], "paper", -10),                    # caught in a hug
        (T["tally"], "tick", -8),
        (T["tally"], "pop", -10),
    ]
    return sorted(out, key=lambda e: e[0])
