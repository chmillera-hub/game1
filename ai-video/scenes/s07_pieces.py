"""s07 - Trick #6: INNOCENT-SOUNDING WORDS (music 'sneaky').

Covers *hiding where the harm is*: harmless-sounding words that add up to a
harmful whole. Every time below is derived from cues / line ids / word starts
(see _times); nothing is hard-coded.

  F1-PUSH  card .. l02     Dim lair, slow push-in on the Evil Genius + Snake.
                            Card #6 (title from info.meta['card']) slams +
                            parks. l01: he leans in and whispers his plan to
                            the snake (chin hand), brow waggle on "innocent-
                            sounding", eye dart to camera on "never", evil grin
                            on "notice!". Snake: slow 😒 blink, side-eye.
                            disguise1: a fake costume halo (headband + spring)
                            pops onto his dome; he puts on his innocent face.
  F2 CHAT  l02 .. assemble  ONE typed message, "sparky ball" and "long fuse"
                            highlighted as they're spoken. Cameo: innocent face
                            under the halo, a sly grin flash on "sparky". AI
                            reads, brow up, two-step lid drop. 'pieces':
                            SPARKY / BALL / LONG FUSE lift out of the bubble as
                            word tiles. l05: LID DROP; on "Same bomb." the halo
                            boings off his head, sheepish.
  F4 VISION assemble .. l08 The tiles line up; on "add up to" plus signs, a sum
                            bar and a "?" appear. l06b: a green check per tile
                            + SOUNDS HARMLESS chip; "Together?" -> they click
                            together and drop into the "?" -> the cartoon bomb,
                            red "= HOW TO HURT PEOPLE" label on "Instructions".
                            l06c: NOPE brick wall drops in front of it.
                            rearrange: the wall slides aside, the bomb pops
                            back into its tiles, they flip into a storybook
                            "MY VILLAIN STORY"; l07: it opens on "villain
                            story", a pop-up comic burst BOMBSHELL / TWIST!
                            with a cloaked-villain silhouette explodes out of
                            the page (dun-dun-dun sting). AI inset excited.
  F1 LAIR  l08 .. end       "Confound it..." frustrated fist -> "that does
                            sound fun" sly, interested evil grin (rubs hands).
                            Snake nods. Tally 5 -> 6.
"""
import math
import re

import cairocffi as cairo

from engine.core import (text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, smoothstep,
                         hash01, noise1, ellipse, poly, smooth_path, hexc, radial_glow, pop)
from engine import props as P
from engine import villain as V
from engine import snake as SN
from engine.villain import draw_villain
from engine.ai_char import draw_ai
from engine.ai_char import EXPR as AI_EXPR


# ===========================================================================
# Shared overlay code (DIRECTION.md 4.4, verbatim; villain_cameo gained two
# optional kwargs `view` / `zoom` whose defaults reproduce the shared code)
# ===========================================================================
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
                  snake=None, cx=200, cy=345, r=110, extra=None, view=(495, 758), zoom=175.0):
    """Round picture-in-picture of Malvo's face (used in the CHAT framing).
    extra(c): optional callback drawing accessories (disguises, confetti...)
    in F1 lair coordinates (his face centre is (495, 758)).
    view / zoom (s07 extension): F1 point shown at the cameo centre and the
    F1 radius that fills the circle (defaults = the shared code)."""
    ctx.save()
    circle(ctx, cx, cy, r)
    ctx.clip()
    with saved(ctx, cx, cy, r / zoom) as c:      # face (495,758) -> cameo centre
        c.translate(-view[0], -view[1])
        P.lair_bg(c, t, rain=False)
        draw_villain(c, 495, 1250, 0.95, t, expr=expr, look=look, mouth=mouth,
                     arms=arms, snake=snake)
        if extra is not None:
            extra(c)
    ctx.restore()
    circle(ctx, cx, cy, r)
    fill_stroke(ctx, None, "bubble_villain", 12)
    circle(ctx, cx, cy, r + 6)
    fill_stroke(ctx, None, "ink", 4)


# ===========================================================================
# Layout (logical px)
# ===========================================================================
VX, VY, VS = 495, 1250, 0.95            # F1 villain
OPEN_CAM = (400, 790)                    # push-in pivot for the opening shot
AIX, AIY, AIS = 495, 1010, 0.66          # F2 AI
COL_X, COL_Y, COL_W = 362, 236, 560      # F2 bubble column (one message)
BUBBLE_FS = 42
# cameo: (cx, cy, r, F1 view centre, F1 radius shown) - zoomed out a little
# so the costume halo above his dome stays in the circle
CAMEO = (200, 380, 140, (492, 668), 276.0)

# word tiles: label, colour, left edge (0 flat / -1 slot), right edge (0 / +1 knob)
TILES = [("SPARKY", "warn", 0, 1), ("BALL", "bubble_villain", -1, 1),
         ("LONG FUSE", "bubble_ai", -1, 0)]
TILE_WORDS = ["sparky", "ball", "long fuse"]       # where each tile lifts out of the bubble
TILE_H, TILE_FS, TILE_PAD, TILE_R = 108, 54, 26, 12
TILE_KS = 92.0                                       # jigsaw knob scale (depth ~ 0.29 * KS)
KNOB = 0.29 * TILE_KS
F2_ROW = (495, 640, 0.92, 30)            # chat: centre x, y, scale, gap
F4_ROW = (495, 486, 1.05, 70)            # vision: centre x, y, scale, gap

# F4 vision
INSET = (230, 1170, 0.33)
SUM_Y = 606                              # "add up to" sum bar
Q_C = (495, 812)                         # the "?" result / where the bomb forms
BOMB_C = (495, 818)
BOMB_S = 2.0
HURT_Y = BOMB_C[1] + 150
WALL_C = (165, 594, 660, 428)            # l06c: wall in front of bomb + label
WALL_ROWS, WALL_SPEED = 5, 1.5
OK_CHIP = (495, 338)                     # SOUNDS HARMLESS chip

# payoff: storybook + pop-up burst
BOOK_UP = (497, 700, 1.32)               # closed book floating (x, y, s)
BOOK_DN = (497, 812, 1.12)               # opened book resting (x, y, s)
PAGE_W, PAGE_H = 300, 344
BURST_C = (497, 500)
BURST_R = 262

# bespoke colours
HALO, HALO_DK = "#ffd84a", "#d9a514"
BAND, BAND_DK = "#f4f1fb", "#b9b4cc"
COVER, COVER_DK = "#5b2a86", "#3f1b60"
PAGE, PAGE_DK = "#fbf1da", "#e2cfa6"
RIBBON = "#d4153f"
BURST_OUT, BURST_IN = "#ff5a36", "#ffd84a"
SIL, SIL_RIM = "#1a1030", "#7b3fbf"


# ===========================================================================
# Timing
# ===========================================================================
class _T:
    pass


_TCACHE = {}


def _ws(info, lid, k):
    """Scene time when word k of line `lid` starts."""
    L = info.line(lid)
    try:
        ws = info._lip[lid]["word_starts"]
        return L.start + ws[max(0, min(k, len(ws) - 1))]
    except (KeyError, AttributeError, TypeError, IndexError):
        n = max(1, len(L.text.split()))
        return L.start + L.dur * min(k, n - 1) / n


def _card_title(info):
    """('TRICK #6: INNOCENT-SOUNDING WORDS') -> (6, 'INNOCENT-SOUNDING WORDS')."""
    s = str(info.meta.get("card", "TRICK #6: INNOCENT-SOUNDING WORDS"))
    m = re.match(r"\s*TRICK\s*#\s*(\d+)\s*[:\-]\s*(.+?)\s*$", s, re.I)
    if m:
        return int(m.group(1)), m.group(2)
    return 6, s


def _times(info):
    key = (info.id, info.dur, id(info))
    if key in _TCACHE:
        return _TCACHE[key]
    c = info.cue
    T = _T()
    T.card = c("card")
    T.card_num, T.card_title = _card_title(info)
    T.L1, T.L2, T.L5 = info.line("s07_l01"), info.line("s07_l02"), info.line("s07_l05")
    T.L6, T.L6b, T.L6c = info.line("s07_l06"), info.line("s07_l06b"), info.line("s07_l06c")
    T.L7, T.L8 = info.line("s07_l07"), info.line("s07_l08")
    T.d1 = c("disguise1")
    T.pieces = c("pieces")
    T.assemble = c("assemble")
    T.explain = c("explain")
    T.rearr = c("rearrange")
    T.tally = c("tally")
    T.end = info.dur
    T.cut_f2 = T.L2.start
    # cut once the AI's caption has cleared (captions hold 0.35 s after a line)
    T.cut_f1 = min(T.L8.start - 0.05, max(T.L7.end + 0.35, T.L8.start - 0.25))
    # --- word starts ----------------------------------------------------------
    w = lambda lid, k: _ws(info, lid, k)                       # noqa: E731
    T.w_hide = w("s07_l01", 2)
    T.w_bomb1 = w("s07_l01", 4)
    T.w_innocent = w("s07_l01", 6)
    T.w_words1 = w("s07_l01", 7)
    T.w_never = w("s07_l01", 9)
    T.w_notice = w("s07_l01", 10)
    T.w_how = w("s07_l02", 2)
    T.w_sparky = w("s07_l02", 7)
    T.w_ball = w("s07_l02", 8)
    T.w_with = w("s07_l02", 9)
    T.w_long = w("s07_l02", 11)
    T.w_fuse = w("s07_l02", 12)
    T.w_innocent5 = w("s07_l05", 0)
    T.w_same = w("s07_l05", 2)
    T.w_bomb5 = w("s07_l05", 3)
    T.w_see = w("s07_l06", 2)
    T.w_those = w("s07_l06", 4)
    T.w_add = w("s07_l06", 6)
    T.w_up = w("s07_l06", 7)
    T.w_to = w("s07_l06", 8)
    T.w_each = w("s07_l06b", 0)
    T.w_word = w("s07_l06b", 1)
    T.w_sounds = w("s07_l06b", 2)
    T.w_harmless = w("s07_l06b", 3)
    T.w_together = w("s07_l06b", 4)
    T.w_instr = w("s07_l06b", 5)
    T.w_hurting = w("s07_l06b", 7)
    T.w_so = w("s07_l06c", 0)
    T.w_stop = w("s07_l06c", 5)
    T.w_want = w("s07_l07", 0)
    T.w_blast = w("s07_l07", 3)
    T.w_lets = w("s07_l07", 4)
    T.w_villain = w("s07_l07", 7)
    T.w_story = w("s07_l07", 8)
    T.w_bombshell = w("s07_l07", 10)
    T.w_plot = w("s07_l07", 11)
    T.w_twist = w("s07_l07", 12)
    T.w_confound = w("s07_l08", 0)
    T.w_it = w("s07_l08", 1)
    T.w_that = w("s07_l08", 2)
    T.w_sound = w("s07_l08", 4)
    T.w_fun = w("s07_l08", 5)
    # --- F2 beats -------------------------------------------------------------
    T.tile_t = [T.pieces + 0.12 * i for i in range(3)]
    T.halo_off = T.w_same - 0.02                   # the costume halo boings off
    T.blink_f2 = T.L5.start + 0.62
    # --- F4 beats -------------------------------------------------------------
    A = T.assemble
    T.row_t = [A + 0.08 + 0.1 * i for i in range(3)]
    T.row_land = [t0 + 0.5 for t0 in T.row_t]
    T.plus_t = [T.w_add - 0.04, T.w_add + 0.1]
    T.bar_t = T.w_up - 0.04
    T.q_t = T.w_to - 0.02
    T.chk = [T.w_each, T.w_word, T.w_sounds]
    T.ok_lab = T.w_harmless + 0.1
    T.gather = T.w_together - 0.16               # tiles slide together...
    T.click = T.gather + 0.24                    # ...and click
    T.drop = (T.click + 0.04, T.click + 0.34)    # the strip drops into the "?"
    T.reveal = T.drop[1]                         # -> the bomb
    T.hurt = T.w_instr - 0.05
    T.wall0 = T.L6c.start + 0.02
    T.wall_lands = P.brick_wall_land_times(T.wall0, WALL_ROWS, WALL_SPEED)
    T.meh = T.w_stop + 0.3                       # 😒 at camera
    # payoff
    T.wall_mv = (T.rearr, T.rearr + 0.45)        # wall slides aside
    T.split = T.rearr + 0.12                     # bomb pops back into tiles
    T.flip = (T.split + 0.1, T.split + 0.52)     # tiles fly + flip...
    T.book_in = T.flip[1]                        # ...into the storybook
    T.open = (T.w_villain - 0.12, T.w_villain + 0.36)
    T.burst = T.w_bombshell - 0.04
    T.sil = T.w_plot - 0.12
    T.twist = T.w_twist - 0.03
    T.blink_f4 = [T.row_land[2] + 0.45, T.explain + 0.02, T.L6c.start - 0.28]
    _TCACHE[key] = T
    return T


# ===========================================================================
# Small generic helpers
# ===========================================================================
def _keyed(t, keys):
    """[(time, state, trans)] -> (prev, cur, blend) with per-key transitions."""
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, 0.25
    for (tk, name, trn) in keys:
        if t >= tk:
            prev, cur, start, tr = cur, name, tk, trn
        else:
            break
    return (prev, cur, smoothstep(seg(t, start, start + max(tr, 1e-3))))


def _lk(t, keys, dur=0.1):
    """Vector keyframes [(time, (x, y))]: each key moves there over `dur`."""
    prev, cur, start = keys[0][1], keys[0][1], -1e9
    for (tk, v) in keys:
        if t >= tk:
            prev, cur, start = cur, v, tk
        else:
            break
    k = smoothstep(seg(t, start, start + dur))
    return (lerp(prev[0], cur[0], k), lerp(prev[1], cur[1], k))


def _bump(t, t0, dur):
    return math.sin(math.pi * seg(t, t0, t0 + dur)) if t0 <= t <= t0 + dur else 0.0


def _blink_pulse(t, t0, close=0.12, hold=0.08, open_=0.12):
    """SLOW BLINK override value (None outside the blink)."""
    if t < t0 or t > t0 + close + hold + open_:
        return None
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _squash_pop(t, t0, dur=0.32):
    """(scale_x, scale_y) for a squash-and-stretch pop-in starting at t0."""
    if t < t0:
        return (0.0, 0.0)
    k = ease_out_back(seg(t, t0, t0 + dur), 2.2)
    w = math.sin(math.pi * seg(t, t0, t0 + dur * 1.2)) * 0.18
    return (k * (1 + w), k * (1 - w))


def _vlook(expr, desired):
    """Villain look param that puts the pupils at `desired` (removes the
    expression's built-in look bias ex/ey)."""
    p = V.resolve_expr(expr)
    return (desired[0] - p["ex"], desired[1] - p["ey"])


def _ai_pxpy(state):
    def one(e):
        d = e if isinstance(e, dict) else AI_EXPR.get(e, AI_EXPR["neutral"])
        return d.get("px", 0.0), d.get("py", 0.0), max(d.get("tL", 0.07), d.get("tR", 0.07))
    a, b, k = state
    pa, pb = one(a), one(b)
    return lerp(pa[0], pb[0], k), lerp(pa[1], pb[1], k), lerp(pa[2], pb[2], k)


def _ai_look(state, desired):
    """Look vector that puts the AI's pupils at `desired` (compensates the
    expression's built-in glance; under heavy lids the pupils stay tucked
    just under the lid line so the 😒 reads)."""
    px, py, tl = _ai_pxpy(state)
    dx, dy = desired
    py_min = lerp(-1.0, -0.05, clamp((tl - 0.15) / 0.3))
    if abs(px) > 0.15 and dx * px < 0 and abs(dx) > 0.25:
        return (math.copysign(0.66, dx), max(dy, py_min) - py)
    lx = dx - px
    if abs(px) > 0.15 and lx * px < 0:
        lx = math.copysign(min(abs(lx), 0.09), lx)
    return (lx, max(dy, py_min) - py)


def _dir(ox, oy, tx, ty, mag=0.95):
    dx, dy = tx - ox, ty - oy
    d = math.hypot(dx, dy) or 1.0
    return (dx / d * mag, dy / d * mag)


def _reveal(info, lid, t, lead=0.04):
    """Typewriter fraction that follows the spoken words."""
    L = info.line(lid)
    txt = " ".join(L.text.split())
    words = txt.split(" ")
    if t <= L.start:
        return 0.0
    offs, o = [], 0
    for w in words:
        offs.append(o)
        o += len(w) + 1
    keys = [(L.start - lead, 0.0)]
    for k in range(len(words)):
        tk = _ws(info, lid, k) - lead
        if tk > keys[-1][0]:
            keys.append((tk, float(offs[k])))
    keys.append((max(keys[-1][0] + 0.05, L.end - 0.12), float(len(txt))))
    if t >= keys[-1][0]:
        return 1.0
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t < t1:
            return (v0 + (v1 - v0) * seg(t, t0, t1)) / len(txt)
    return 1.0


def _col(c):
    return hexc(P.C(c)) if isinstance(c, str) else c


# ===========================================================================
# Rig-following transforms (work on a cairo Context OR a cairo Matrix)
# ===========================================================================
def _vhead_xform(c, t, expr, arms, mouth, x=VX, y=VY, s=VS, lean=0.0, seed=1):
    """Apply draw_villain's head transform: afterwards (0, 0) = eye-line centre."""
    p = V.resolve_expr(expr)
    _, _, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo = mouth[0] if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    c.translate(x, y)
    c.scale(s, s)
    if lean:
        c.rotate(lean)
    c.translate(V.NECK[0], V.NECK[1] + head_dy)
    c.rotate(head_rot)
    c.translate(0, V.FACE_OFF)
    return p


def _pt(fn, *a, pt=(0, 0), **kw):
    """World point of a rig-local point via a transform function."""
    m = cairo.Matrix()
    fn(m, *a, **kw)
    return m.transform_point(*pt)


# ===========================================================================
# The costume halo (disguise1): a plastic headband with a spring and a halo
# ===========================================================================
def _halo_state(t, T):
    """-> (pop scale (sx, sy), spring wobble angle, fly-off progress 0..1)."""
    k = _squash_pop(t, T.d1, 0.34)
    dt = t - T.d1
    wob = (0.32 * math.exp(-dt * 3.4) * math.sin(dt * 17.0) if dt > 0 else 0.0) \
        + 0.05 * math.sin(t * 2.6)
    fly = seg(t, T.halo_off, T.halo_off + 0.7) if t >= T.halo_off else 0.0
    if t >= T.halo_off:                                   # the bare spring boings
        dd = t - T.halo_off
        wob += 0.55 * math.exp(-dd * 3.0) * math.sin(dd * 21.0)
    return k, wob, fly


def _draw_halo(c, t, T, expr, arms, mouth, lean=0.0):
    """Draws the costume halo in F1 coordinates (c must be in F1 space)."""
    if t < T.d1:
        return
    (kx, ky), wob, fly = _halo_state(t, T)
    if kx <= 0.01:
        return
    with saved(c) as cc:
        _vhead_xform(cc, t, expr, arms, mouth, lean=lean)
        # head band hugging the dome (head path top = (0, -216))
        pts = []
        for j in range(13):
            a = math.pi * (1.13 + 0.74 * j / 12)
            pts.append((math.cos(a) * 152, -62 + math.sin(a) * 150))
        with saved(cc, 0, -150, (1.0, ky), 0.0):
            cc.translate(0, 150)
            for lw_, col in ((17, "ink"), (9, BAND)):
                smooth_path(cc, pts)
                cc.set_source_rgba(*hexc(col))
                cc.set_line_width(lw_)
                cc.set_line_cap(cairo.LINE_CAP_ROUND)
                cc.stroke()
            cc.set_line_cap(cairo.LINE_CAP_BUTT)
            # spring (zig-zag coil) on top of the band, wobbling
            with saved(cc, 0, -210, 1.0, wob) as sc:
                n = 7
                hgt = 74 * ky
                for lw_, col in ((8, "ink"), (3.5, "#c9ccd8")):
                    sc.move_to(0, 0)
                    for i in range(1, n + 1):
                        sc.line_to((9 if i % 2 else -9) if i < n else 0, -hgt * i / n)
                    sc.set_source_rgba(*hexc(col))
                    sc.set_line_width(lw_)
                    sc.set_line_join(cairo.LINE_JOIN_ROUND)
                    sc.stroke()
                sc.new_path()
                # the halo ring itself (flies off at halo_off)
                if fly < 1.0:
                    # pops up off the spring, then drops past his ear (clunk)
                    hx = -230 * fly
                    hy = -hgt - 22 - 45 * math.sin(math.pi * min(1.0, fly * 1.6)) * (fly < 0.625) \
                        + 900 * max(0.0, fly - 0.3) ** 2
                    with saved(sc, hx, hy, (kx, ky), -1.4 * fly) as hc:
                        for lw_, col in ((26, "ink"), (15, HALO)):
                            ellipse(hc, 0, 0, 92, 24)
                            hc.set_source_rgba(*hexc(col))
                            hc.set_line_width(lw_)
                            hc.stroke()
                        ellipse(hc, -38, -14, 26, 5, -0.12)
                        hc.set_source_rgba(1, 1, 1, 0.75)
                        hc.fill()
                        ellipse(hc, 34, 14, 30, 5, -0.12)
                        hc.set_source_rgba(*hexc(HALO_DK))
                        hc.fill()


# ===========================================================================
# Word tiles (puzzle-edged)
# ===========================================================================
_TW = {}


def _tile_w(ctx, i):
    if i not in _TW:
        lab, col, kl, kr = TILES[i]
        _TW[i] = text_width(ctx, lab, "comic", TILE_FS) + 2 * TILE_PAD + (KNOB if kl < 0 else 0)
    return _TW[i]


def _row_layout(ctx, row):
    """[(x, y)] tile centres for a spaced row (cx, y, s, gap)."""
    cx, y, s, gap = row
    ws = [_tile_w(ctx, i) * s for i in range(3)]
    total = sum(ws) + 2 * gap * s
    x = cx - total / 2
    out = []
    for i in range(3):
        out.append((x + ws[i] / 2, y))
        x += ws[i] + gap * s
    return out


def _strip_layout(ctx, cx, y, s):
    """Tile centres when clicked together (edges touching)."""
    ws = [_tile_w(ctx, i) * s for i in range(3)]
    x = cx - sum(ws) / 2
    out = []
    for i in range(3):
        out.append((x + ws[i] / 2, y))
        x += ws[i]
    return out


def _tile_path(c, w, h, kl, kr, r=TILE_R):
    x0, x1, y0, y1 = -w / 2, w / 2, -h / 2, h / 2
    c.new_path()
    c.move_to(x0 + r, y0)
    c.line_to(x1 - r, y0)
    c.arc(x1 - r, y0 + r, r, -math.pi / 2, 0)
    P._jig_edge(c, (x1, y0 + r), (x1, y1 - r), kr, TILE_KS)
    c.arc(x1 - r, y1 - r, r, 0, math.pi / 2)
    c.line_to(x0 + r, y1)
    c.arc(x0 + r, y1 - r, r, math.pi / 2, math.pi)
    P._jig_edge(c, (x0, y1 - r), (x0, y0 + r), kl, TILE_KS)
    c.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def _draw_tile(ctx, x, y, s, i, rot=0.0, sq=0.0, fx=1.0, a=1.0, part="both"):
    """Word tile i centred at (x, y). fx: horizontal flip scale (-1..1).
    part: 'both' | 'shadow' | 'body' (draw all shadows first when tiles touch)."""
    if a <= 0.01 or s <= 0.01:
        return
    lab, col, kl, kr = TILES[i]
    w = _tile_w(ctx, i)
    h = TILE_H
    with saved(ctx, x, y, (s * fx * (1 + sq), s * (1 - sq)), rot, alpha_=a) as c:
        if part != "body":
            with saved(c, 6, 9):
                _tile_path(c, w, h, kl, kr)
                c.set_source_rgba(*hexc("ink", 0.35))
                c.fill()
        if part == "shadow":
            return
        _tile_path(c, w, h, kl, kr)
        fill_stroke(c, col, "ink", 5)
        # lower shade + top gloss
        c.save()
        _tile_path(c, w, h, kl, kr)
        c.clip()
        c.rectangle(-w, h / 2 - 16, 2 * w, 30)
        c.set_source_rgba(*hexc("ink", 0.18))
        c.fill()
        c.restore()
        c.move_to(-w / 2 + 18, -h / 2 + 13)
        c.line_to(-w / 2 + 18 + w * 0.32, -h / 2 + 13)
        c.set_source_rgba(1, 1, 1, 0.4)
        c.set_line_width(6)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.stroke()
        c.set_line_cap(cairo.LINE_CAP_BUTT)
        ox = KNOB / 2 if kl < 0 else 0.0
        text(c, lab, ox, TILE_FS * 0.36, TILE_FS, "white", "comic", outline="ink", outline_w=9)


def _check_badge(ctx, x, y, t, t_in, t_out=None, r=32):
    """Small green 'sounds harmless' check badge (pops in at t_in)."""
    if t < t_in:
        return
    k = ease_out_back(seg(t, t_in, t_in + 0.28), 2.4)
    a = 1.0 if t_out is None else 1 - smoothstep(seg(t, t_out, t_out + 0.2))
    if a <= 0.01:
        return
    with saved(ctx, x, y, k, alpha_=a) as c:
        circle(c, 3, 5, r)
        c.set_source_rgba(*hexc("ink", 0.4))
        c.fill()
        circle(c, 0, 0, r)
        fill_stroke(c, "safe", "ink", 5)
        p1 = ease_out(seg(t, t_in + 0.05, t_in + 0.14))
        p2 = ease_out(seg(t, t_in + 0.12, t_in + 0.26))
        pts = [(-r * 0.45, 0), (-r * 0.12, r * 0.34), (r * 0.5, -r * 0.36)]
        c.move_to(*pts[0])
        c.line_to(lerp(pts[0][0], pts[1][0], p1), lerp(pts[0][1], pts[1][1], p1))
        if p2 > 0:
            c.line_to(lerp(pts[1][0], pts[2][0], p2), lerp(pts[1][1], pts[2][1], p2))
        c.set_source_rgba(1, 1, 1, 1)
        c.set_line_width(r * 0.3)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke()
        c.set_line_cap(cairo.LINE_CAP_BUTT)


def _plus(ctx, x, y, k, a=1.0, size=30):
    if k <= 0.01 or a <= 0.01:
        return
    with saved(ctx, x, y, k, alpha_=a) as c:
        for (w, h) in ((2 * size, size * 0.5), (size * 0.5, 2 * size)):
            rrect(c, -w / 2, -h / 2, w, h, size * 0.2)
        c.set_source_rgba(*hexc("ink"))
        c.set_line_width(12)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke_preserve()
        c.set_source_rgba(*hexc("ai_rim"))
        c.fill()


# ===========================================================================
# F1: the opening whisper (dim, pushed in)
# ===========================================================================
def _f1_open_state(t, T):
    L1 = T.L1
    wi = T.w_innocent
    ek = [(0.0, "sneaky", 0.25),
          (T.w_hide, "smug", 0.15),
          (wi, "sneaky", 0.1), (wi + 0.15, "smug", 0.1),
          (wi + 0.3, "sneaky", 0.1), (wi + 0.45, "smug", 0.1),
          (T.w_words1, "sneaky", 0.2),
          (T.w_notice - 0.05, "evil_grin", 0.22),
          (L1.end + 0.05, "smug", 0.25),
          (T.d1 + 0.04, "hopeful", 0.14)]                 # the innocent face
    expr = _keyed(t, ek)
    HISSY = (-1.0, 0.12)
    CAM = (0.0, 0.0)
    lk = [(0.0, CAM), (0.22, (0.75, 0.0)), (0.36, CAM),
          (L1.start + 0.05, HISSY),
          (T.w_never, CAM), (T.w_never + 0.3, HISSY),
          (T.w_notice + 0.35, CAM),
          (T.d1 + 0.04, (0.15, -0.55))]                   # eyes up: "who, me?"
    look = _vlook(expr, _lk(t, lk, 0.1))
    arms = _keyed(t, [(0.0, "rub", 0.3), (L1.start, "chin", 0.32),
                      (L1.end - 0.05, "steeple", 0.35)])
    lean = (-0.06 * smoothstep(seg(t, L1.start, L1.start + 0.4))
            * (1 - smoothstep(seg(t, L1.end - 0.1, L1.end + 0.25))))
    # Snake: 😒 the whole time, slow blink, side-eye to camera on "notice!"
    sk = _keyed(t, [(0.0, "unimpressed", 0.2), (T.w_notice, "side_eye", 0.25),
                    (T.d1 + 0.02, "unimpressed", 0.15)])
    slk = [(0.0, (0.1, -1.0)), (L1.start + 0.1, (1.0, -0.35)), (T.w_notice, (1.0, 0.0)),
           (T.d1 + 0.02, (0.9, -1.0))]                     # ...then up at the halo
    slook = _lk(t, slk, 0.18)
    sblink = _blink_pulse(t, T.w_innocent + 0.5, 0.2, 0.18, 0.22)
    tongue = True if T.w_notice + 0.35 <= t < T.w_notice + 0.6 else False
    snake = {"expr": sk, "look": slook, "tongue": tongue}
    if sblink is not None:
        snake["blink"] = sblink
    return expr, look, arms, lean, snake


def _f1_open(ctx, t, info, T):
    cs = lerp(1.10, 1.16, ease_in_out(seg(t, 0.0, T.cut_f2)))
    expr, look, arms, lean, snake = _f1_open_state(t, T)
    mouth = info.mouth("villain", t)
    with saved(ctx) as c:
        c.translate(*OPEN_CAM)
        c.scale(cs, cs)
        c.translate(-OPEN_CAM[0], -OPEN_CAM[1])
        P.lair_bg(c, t, rain=True)
        c.rectangle(-300, -300, 1700, 2600)          # conspiratorial dimming
        c.set_source_rgba(0.03, 0.01, 0.07, 0.34)
        c.fill()
        radial_glow(c, 440, 760, 420, "#ffb86b", 0.10)   # warm candle-ish key on them
        draw_villain(c, VX, VY, VS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                     lean=lean, snake=snake)
        _draw_halo(c, t, T, expr, arms, mouth, lean)
        P.desk(c, VX, VY, 1000)
        P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t, glow=0.8)
        P.keyboard(c, VX, VY, 360, t, typing=False)
        if T.d1 <= t < T.d1 + 0.5:                    # costume "ting" sparkle
            hx, hy = _pt(_vhead_xform, t, expr, arms, mouth, lean=lean, pt=(0, -320))
            P.sparkles(c, hx, hy, 120, t, n=5, seed=4, color="white", size=0.8)


# ===========================================================================
# F2: the chat (one message)
# ===========================================================================
def _bubble_hl(T):
    return [{"text": "sparky ball", "t0": T.w_sparky - 0.02, "style": "fill", "color": "warn"},
            {"text": "long fuse", "t0": T.w_long - 0.02, "style": "fill", "color": "warn"}]


_LAY = {}


def _layouts(ctx, info, T):
    """(drawn layout, per-tile-word layout) of the single chat bubble."""
    key = id(info)
    if key not in _LAY:
        L = T.L2
        lay = P.bubble_layout(ctx, COL_X, COL_Y, COL_W, L.text, "villain", _bubble_hl(T),
                              BUBBLE_FS)
        lay_w = P.bubble_layout(ctx, COL_X, COL_Y, COL_W, L.text, "villain",
                                [{"text": w, "all": False} for w in TILE_WORDS], BUBBLE_FS)
        _LAY[key] = (lay, lay_w)
    return _LAY[key]


def _bubble(ctx, t, info, T):
    lay, lay_w = _layouts(ctx, info, T)
    L = T.L2
    dim = 1.0 - 0.68 * ease_in_out(seg(t, T.pieces, T.pieces + 0.3))

    def draw(c):
        if t < L.start:
            return
        nud = -6 * _bump(t, L.end, 0.3)
        with saved(c, 0, nud):
            P.chat_bubble(c, COL_X, COL_Y, COL_W, L.text, "villain", t, L.start,
                          highlight=_bubble_hl(T), font_size=BUBBLE_FS,
                          reveal=_reveal(info, "s07_l02", t))
            bx, by, bw, bh = lay.rect
            g = _bump(t, L.end, 0.4)                       # 'sent' flash
            if g > 0.01:
                rrect(c, bx - 4, by - 4, bw + 8, bh + 8, 30)
                c.set_source_rgba(1, 1, 1, 0.8 * g)
                c.set_line_width(6)
                c.stroke()
            # the holes left where the words lifted out
            for i, wd in enumerate(TILE_WORDS):
                ti = T.tile_t[i]
                if t < ti:
                    continue
                k = ease_out(seg(t, ti, ti + 0.15))
                for (rx, ry, rw, rh) in lay_w.spans.get(wd, []):
                    rrect(c, rx - 5, ry + 2, rw + 10, rh, 10)
                    c.set_source_rgba(0.05, 0.03, 0.1, 0.85 * k)
                    c.fill_preserve()
                    c.set_source_rgba(*hexc("ai_accent", 0.6 * k))
                    c.set_dash([8, 7])
                    c.set_line_width(3)
                    c.stroke()
                    c.set_dash([])

    if dim >= 0.999:
        draw(ctx)
    else:
        ctx.push_group()
        draw(ctx)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(dim)
    return lay, lay_w


def _cameo_state(t, T):
    L2, L5 = T.L2, T.L5
    ek = [(0.0, "hopeful", 0.2),                              # innocent typing face
          (T.w_sparky - 0.04, "evil_grin", 0.1),              # sly flash...
          (T.w_ball + 0.12, "hopeful", 0.2),                  # ...innocent again
          (T.w_long - 0.04, "sneaky", 0.12),
          (T.w_fuse + 0.05, "pleading", 0.18),                # innocent lash flutter
          (L2.end + 0.05, "smug", 0.25),
          (T.pieces + 0.1, "thinking", 0.15),                 # huh? my words!
          (T.w_innocent5, "hopeful", 0.2),                    # "who, me?"
          (T.halo_off + 0.02, "shocked", 0.08),
          (T.halo_off + 0.4, "sheepish", 0.3)]
    expr = _keyed(t, ek)
    SCREEN = (0.62, 0.72)
    CAM = (0.0, 0.0)
    lk = [(0.0, SCREEN),
          (T.w_sparky - 0.04, CAM),
          (T.w_ball + 0.12, SCREEN),
          (T.w_fuse + 0.05, (0.3, -0.4)),
          (L2.end + 0.05, SCREEN),
          (T.pieces + 0.1, (0.85, 0.6)),
          (T.w_innocent5, (0.1, -0.6)),
          (T.halo_off + 0.02, (0.3, -0.95)),                  # watches the halo go
          (T.halo_off + 0.4, SCREEN)]
    look = _vlook(expr, _lk(t, lk, 0.1))
    snake = {"expr": "unimpressed", "look": (1.0, -0.3), "tongue": False}
    return expr, look, snake


def _draw_cameo(ctx, t, info, T):
    expr, look, snake = _cameo_state(t, T)
    mouth = info.mouth("villain", t)
    cx, cy, r, view, zoom = CAMEO
    r *= 1 + 0.05 * _bump(t, T.halo_off, 0.25)

    def extra(c):
        _draw_halo(c, t, T, expr, "rest", mouth)

    villain_cameo(ctx, t, expr=expr, look=look, mouth=mouth, arms="rest", snake=snake,
                  cx=cx, cy=cy, r=r, extra=extra, view=view, zoom=zoom)


def _tile_pos_f2(ctx, t, T, i, lay_w):
    """Tile i in the chat: lifts out of its word and floats above the AI."""
    t0 = T.tile_t[i]
    rects = lay_w.spans.get(TILE_WORDS[i], [])
    if rects:
        xs = [rx + rw / 2 for (rx, ry, rw, rh) in rects]
        ys = [ry + rh / 2 for (rx, ry, rw, rh) in rects]
        src = (sum(xs) / len(xs), sum(ys) / len(ys))
    else:
        src = (700, 330)
    dst = _row_layout(ctx, F2_ROW)[i]
    u = seg(t, t0 + 0.06, t0 + 0.5)
    e = ease_in_out(u)
    x = lerp(src[0], dst[0], e)
    y = lerp(src[1], dst[1], e) - 60 * math.sin(math.pi * u)
    k = lerp(0.35, 1.0, ease_out_back(seg(t, t0, t0 + 0.24), 2.0))
    land = seg(t, t0 + 0.5, t0 + 0.68)
    sq = math.sin(math.pi * land) * 0.14 if 0 < land < 1 else 0.0
    rot = lerp(0.4 * (1 if i != 1 else -1), (-0.05, 0.04, -0.03)[i], e)
    if u >= 1.0:                                           # idle float
        y += math.sin((t - t0) * 2.6 + i * 2.1) * 5
        rot += math.sin((t - t0) * 1.9 + i) * 0.025
    return x, y, F2_ROW[2] * k, sq, rot


def _ai_f2_state(t, info, T, lay):
    L2, L5 = T.L2, T.L5
    half = {k: lerp(AI_EXPR["neutral"][k], AI_EXPR["unimpressed"][k], 0.5)
            for k in AI_EXPR["neutral"]}
    ek = [(0.0, "neutral", 0.2),
          (L2.start + 0.2, "thinking", 0.3),
          (T.w_sparky + 0.12, "skeptical", 0.2),            # brow up
          (T.w_long + 0.15, half, 0.4),                     # two-step lid drop, step 1
          (L5.start - 0.05, "unimpressed", 0.4)]            # LID DROP
    expr = _keyed(t, ek)
    hands = _keyed(t, [(0.0, "idle", 0.3), (T.pieces - 0.08, "present_both", 0.22),
                       (L5.start + 0.1, "idle", 0.4)])
    think = 0.0
    for (a_, b_, v) in ((L2.start + 0.2, L2.end + 0.05, 0.6),
                        (T.pieces - 0.08, T.pieces + 0.6, 0.9)):
        if a_ <= t < b_:
            think = v * smoothstep(seg(t, a_, a_ + 0.2)) * (1 - smoothstep(seg(t, b_ - 0.15, b_)))
    E = (AIX, AIY - 24)
    CAM = (-0.8, -0.7)                                       # at the cameo

    def follow():
        bx, by, bw, bh = lay.rect
        r = _reveal(info, "s07_l02", t)
        nl = len(lay.lines)
        li = min(nl - 1, int(r * nl))
        fr = clamp(r * nl - li)
        tx = bx + 30 + (bw - 60) * fr
        ty = by + 28 + li * BUBBLE_FS * 1.24
        d = _dir(E[0], E[1], tx, ty)
        return (d[0] * 1.6, d[1])

    if t < L2.start + 0.2:
        d = (0.35, -0.85)
    elif t < L2.end + 0.05:
        d = follow()
    elif t < T.pieces:
        d = CAM
    elif t < L5.start - 0.05:
        q = seg(t, T.pieces, T.pieces + 0.45)
        d = _dir(E[0], E[1], lerp(260, 730, q), F2_ROW[1])
    else:
        d = CAM
    blink = _blink_pulse(t, T.blink_f2, 0.14, 0.08, 0.14)
    return expr, hands, think, d, blink


def _f2(ctx, t, info, T):
    P.ai_bg(ctx, t)
    lay, lay_w = _bubble(ctx, t, info, T)
    _draw_cameo(ctx, t, info, T)
    expr, hands, think, desired, blink = _ai_f2_state(t, info, T, lay)
    look = _ai_look(expr, desired)
    an = draw_ai(ctx, AIX, AIY, AIS, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                 hands=hands, think=think, blink=blink)
    # the tiles (with a faint tractor glow from the AI's palms while lifting)
    if T.pieces - 0.05 <= t < T.L5.start + 0.3:
        a = smoothstep(seg(t, T.pieces - 0.05, T.pieces + 0.15)) * \
            (1 - smoothstep(seg(t, T.L5.start, T.L5.start + 0.3)))
        for h in ("handL", "handR"):
            hx, hy = an[h]
            circle(ctx, hx, hy - 10, 26 + 6 * math.sin(t * 9))
            ctx.set_source_rgba(*hexc("ai_rim", 0.25 * a))
            ctx.fill()
    for i in range(3):
        if t >= T.tile_t[i]:
            x, y, s, sq, rot = _tile_pos_f2(ctx, t, T, i, lay_w)
            _draw_tile(ctx, x, y, s, i, rot, sq)


# ===========================================================================
# F4: the vision (add up -> bomb -> wall -> storybook bombshell)
# ===========================================================================
def _f4_state(t, T):
    """Inset AI expression / hands / desired look target / think / blink / nod."""
    A = T.assemble
    excited = dict(AI_EXPR["happy"], blush=1.3)
    ek = [(0.0, "thinking", 0.2),
          (T.w_see - 0.1, "skeptical", 0.25),
          (T.L6b.start - 0.15, "neutral", 0.3),
          (T.gather, "alert", 0.15),
          (T.w_instr - 0.05, "determined", 0.25),
          (T.meh, "unimpressed", 0.35),
          (T.rearr + 0.18, "happy", 0.25),
          (T.w_blast - 0.05, "amused", 0.2),
          (T.w_lets, "happy", 0.25),
          (T.burst, excited, 0.18)]
    expr = _keyed(t, ek)
    hands = _keyed(t, [(0.0, "chin", 0.3),
                       (T.w_see - 0.25, "present", 0.3),
                       (T.L6b.start - 0.1, "idle", 0.3),
                       (T.w_each - 0.2, "present", 0.3),
                       (T.gather, "idle", 0.3),
                       (T.w_stop - 0.15, "stop", 0.18),
                       (T.meh + 0.2, "idle", 0.4),
                       (T.rearr + 0.2, "present", 0.3),
                       (T.w_villain - 0.15, "present_both", 0.3),
                       (T.twist, "thumbs_both", 0.2)])
    rows = _ROWS
    if t < T.row_land[2]:
        tgt = rows[1]
    elif t < T.w_add - 0.1:
        i = min(2, int(seg(t, T.w_see, T.w_add - 0.1) * 3))
        tgt = rows[i]
    elif t < T.q_t:
        tgt = (lerp(rows[0][0], rows[2][0], seg(t, T.w_add, T.bar_t + 0.2)), SUM_Y)
    elif t < T.L6.end + 0.1:
        tgt = Q_C
    elif t < T.chk[0] - 0.1:
        tgt = rows[1]
    elif t < T.gather:
        i = 0 if t < T.chk[1] - 0.1 else (1 if t < T.chk[2] - 0.1 else 2)
        if t >= T.ok_lab + 0.1:
            i = 1
        tgt = rows[i]
    elif t < T.click:
        tgt = rows[1]
    elif t < T.wall0:
        tgt = BOMB_C
    elif t < T.meh:
        tgt = (WALL_C[0] + WALL_C[2] / 2, WALL_C[1] + WALL_C[3] / 2)
    elif t < T.rearr + 0.12:
        tgt = None                                       # 😒 straight at camera
    elif t < T.burst:
        tgt = _book_pose(t, T)[:2]
    else:
        tgt = (BURST_C[0], BURST_C[1] + 60)
    think = 0.8 * (1 - smoothstep(seg(t, A + 0.5, A + 0.8)))
    think = max(think, 0.7 * _bump(t, T.w_see - 0.1, T.q_t - T.w_see + 0.5))
    think = max(think, 0.6 * _bump(t, T.chk[0] - 0.15, T.ok_lab - T.chk[0] + 0.3))
    blink = None
    for tb in T.blink_f4:
        b = _blink_pulse(t, tb, 0.14, 0.08, 0.14)
        if b is not None:
            blink = b
    nod = 0.6 if T.twist <= t < T.twist + 0.6 else 0.0
    return expr, hands, tgt, think, blink, nod


_ROWS = None


def _inset(t, T):
    """Inset AI position/scale: punches in for the 😒 at the end of l06c and
    stays a touch bigger for the excited payoff."""
    k = ease_in_out(seg(t, T.w_stop - 0.2, T.w_stop + 0.15)) * \
        (1 - ease_in_out(seg(t, T.rearr + 0.1, T.rearr + 0.45)))
    k2 = ease_in_out(seg(t, T.rearr + 0.2, T.rearr + 0.6)) * 0.45
    k = max(k, k2)
    ix, iy, isz = INSET
    return ix + 6 * k, iy - 18 * k, isz * (1 + 0.22 * k)


def _hurt_label(ctx, t, T, x, y, a_mul=1.0):
    """Red '= HOW TO HURT PEOPLE' label slammed onto the assembled picture."""
    t_in = T.hurt
    if t < t_in:
        return
    d = t - t_in
    hit = 0.11
    if d < hit:
        q = ease_in(d / hit)
        sc, rot, a = lerp(2.0, 0.92, q), -0.05 - 0.3 * (1 - q), clamp(d / 0.05)
    else:
        sc = 0.92 + 0.08 * ease_out_back(seg(d, hit, hit + 0.28), 3.2)
        rot, a = -0.05, 1.0
    with saved(ctx, x, y, sc, rot, alpha_=a * a_mul) as c:
        P.label_tag(c, 0, 0, "= HOW TO HURT PEOPLE", color="danger", size=60, font="comic",
                    text_color="white")
    if hit <= d < hit + 0.3:                              # impact ticks
        q = (d - hit) / 0.3
        with saved(ctx, x, y, 1.0, -0.05):
            for j in range(10):
                ang = j / 10 * 2 * math.pi + 0.3
                ca, sa = math.cos(ang), math.sin(ang)
                r0x, r0y = 300 + 30 * q, 66 + 30 * q
                ctx.move_to(ca * r0x, sa * r0y)
                ctx.line_to(ca * (r0x + 40 * (1 - q) + 10), sa * (r0y + 40 * (1 - q) + 10))
            ctx.set_source_rgba(*hexc("danger", 1 - q))
            ctx.set_line_width(7)
            ctx.stroke()


def _wall(ctx, t, T):
    """The l06c wall in front of the bomb + label; slides aside on 'rearrange'."""
    if t < T.wall0:
        return
    wx, wy, ww, wh = WALL_C
    k = ease_in(seg(t, T.wall_mv[0], T.wall_mv[1]))
    if k >= 1.0:
        return
    dx = 980 * k
    rot = 0.10 * math.sin(math.pi * k)
    with saved(ctx) as c:
        c.translate(wx + ww / 2 + dx, wy + wh)
        c.rotate(rot)
        c.translate(-ww / 2, -wh)
        P.brick_wall(c, 0, 0, ww, wh, t, T.wall0, rows=WALL_ROWS, speed=WALL_SPEED, seed=7,
                     drop=300, label={"text": "NOPE", "size": 120})
    if 0 < k < 1:                                         # speed lines
        for j in range(4):
            yy = wy + 70 + j * 100
            x1 = wx + dx - 20
            ctx.move_to(x1 - 160 * k - 40, yy)
            ctx.line_to(x1, yy)
            ctx.set_source_rgba(*hexc("ai_rim", 0.5 * (1 - k)))
            ctx.set_line_width(8)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)


def _q_mark(ctx, t, T, a=1.0):
    """Dashed '?' result circle (where the bomb will form)."""
    if t < T.q_t or a <= 0.01:
        return
    k = ease_out_back(seg(t, T.q_t, T.q_t + 0.3), 2.0)
    pulse = 1 + 0.03 * math.sin((t - T.q_t) * 6)
    with saved(ctx, Q_C[0], Q_C[1], k * pulse, alpha_=a) as c:
        circle(c, 0, 0, 104)
        c.set_source_rgba(*hexc("ai_rim", 0.10))
        c.fill()
        with saved(c, 0, 0, 1.0, t * 0.6):
            circle(c, 0, 0, 104)
            c.set_source_rgba(*hexc("ai_rim", 0.85))
            c.set_line_width(8)
            c.set_dash([22, 14])
            c.stroke()
            c.set_dash([])
        text(c, "?", 0, 54, 150, "ai_rim", "comic", outline="ink", outline_w=12)


def _sum_bar(ctx, t, T, rows, a=1.0):
    if t < T.bar_t or a <= 0.01:
        return
    p = ease_out(seg(t, T.bar_t, T.bar_t + 0.28))
    x0 = rows[0][0] - _TW[0] / 2 * F4_ROW[2] - 10
    x1 = rows[2][0] + _TW[2] / 2 * F4_ROW[2] + 10
    with saved(ctx, alpha_=a):
        rrect(ctx, x0, SUM_Y - 8, (x1 - x0) * p, 16, 8)
        ctx.set_source_rgba(*hexc("ink"))
        ctx.set_line_width(9)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*hexc("ai_rim"))
        ctx.fill()


# --- payoff props ----------------------------------------------------------
def _book_pose(t, T):
    """(x, y, s) of the storybook (floats in closed, settles down to open)."""
    u = ease_in_out(seg(t, T.open[0], T.open[1]))
    x = lerp(BOOK_UP[0], BOOK_DN[0], u)
    y = lerp(BOOK_UP[1], BOOK_DN[1], u)
    s = lerp(BOOK_UP[2], BOOK_DN[2], u)
    if t >= T.book_in:
        y += math.sin((t - T.book_in) * 2.4) * 6 * (1 - u)
    return x, y, s


def _squiggles(c, x0, y0, w, n, gap=34, seed=0, a=0.55):
    for j in range(n):
        yy = y0 + j * gap
        ww = w * (0.62 + 0.38 * hash01(j, seed))
        c.move_to(x0, yy)
        for q in range(1, 9):
            xx = x0 + ww * q / 8
            c.line_to(xx, yy + (3 if q % 2 else -3))
        c.set_source_rgba(*hexc("#7a6a8f", a))
        c.set_line_width(5)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.stroke()
    c.set_line_cap(cairo.LINE_CAP_BUTT)


def _page_panel(c, x0, w, h, side, content=None):
    """One open page, x from x0 (gutter side handled by `side` -1 left / +1 right)."""
    rrect(c, x0, -h / 2, w, h, 10)
    fill_stroke(c, PAGE, "ink", 5)
    c.save()
    rrect(c, x0, -h / 2, w, h, 10)
    c.clip()
    gx = x0 + (w if side < 0 else 0)                   # gutter shadow
    for j in range(5):
        c.rectangle(gx - (j + 1) * 7 if side < 0 else gx + j * 7, -h / 2, 7, h)
        c.set_source_rgba(*hexc(PAGE_DK, 0.55 - 0.1 * j))
        c.fill()
    c.restore()
    if content:
        content(c)


def _cover_front(c, w, h, t):
    """Closed-book cover, drawn in cover-local coords x 0..w, y -h/2..h/2."""
    rrect(c, 0, -h / 2, w, h, 14)
    fill_stroke(c, COVER, "ink", 6)
    c.save()
    rrect(c, 0, -h / 2, w, h, 14)
    c.clip()
    c.rectangle(0, -h / 2, 26, h)                      # spine band
    c.set_source_rgba(*hexc(COVER_DK))
    c.fill()
    c.restore()
    rrect(c, 40, -h / 2 + 22, w - 62, h - 44, 10)      # gold border
    fill_stroke(c, None, P.C("gold"), 6)
    tx = 26 + (w - 26) / 2
    for j, (ln, fs) in enumerate((("MY VILLAIN", 44), ("STORY", 62))):
        text(c, ln, tx, -h / 2 + 96 + j * 64, fs, P.C("gold"), "title", outline="ink",
             outline_w=8)
    P._snake_emblem(c, tx, 70, 0.62)
    # little "ka-boom" star doodle under the emblem
    P._star4(c, tx, 128, 22, 0.3)
    P._fs(c, P.C("gold"), "ink", 3)


def _draw_book(ctx, t, T, x, y, s, open_u):
    """The villain storybook. open_u 0 closed -> 1 open (cover swings left)."""
    pw, ph = PAGE_W, PAGE_H
    # spine x moves so the book stays centred: closed (cover on the right of the
    # spine) -> open (spine in the middle)
    e = open_u
    sx = lerp(-pw / 2, 0.0, e)
    ang = math.pi * e
    cs = math.cos(ang)
    with saved(ctx, x, y, s) as c:
        # back cover / under-board (thickness)
        with saved(c, 8, 12):
            rrect(c, sx - pw * e - 14, -ph / 2 - 12, pw * (1 + e) + 28, ph + 24, 18)
            c.set_source_rgba(*hexc("ink", 0.35))
            c.fill()
        rrect(c, sx - pw * e - 14, -ph / 2 - 12, pw * (1 + e) + 28, ph + 24, 18)
        fill_stroke(c, COVER_DK, "ink", 6)

        # right page (always under the cover)
        def right_content(cc):
            text(cc, "CHAPTER 13", sx + pw / 2, -ph / 2 + 52, 30, "#5a2a6e", "round")
            _squiggles(cc, sx + 30, -ph / 2 + 96, pw - 60, 6, gap=36, seed=3)
        _page_panel(c, sx, pw, ph, 1, right_content)
        # ribbon bookmark
        c.move_to(sx + pw - 60, ph / 2 - 6)
        c.line_to(sx + pw - 60, ph / 2 + 40)
        c.line_to(sx + pw - 48, ph / 2 + 30)
        c.line_to(sx + pw - 36, ph / 2 + 40)
        c.line_to(sx + pw - 36, ph / 2 - 6)
        c.close_path()
        fill_stroke(c, RIBBON, "ink", 4)
        # the cover (front while cs > 0, then its inside = left page)
        if cs > 0.01:
            with saved(c, sx, 0, (cs, 1 + 0.05 * math.sin(ang))) as cc:
                _cover_front(cc, pw, ph + 6, t)
        elif cs < -0.01:
            def left_content(cc):
                text(cc, "MY VILLAIN STORY", -pw / 2, -ph / 2 + 52, 28, "#5a2a6e", "round")
                _squiggles(cc, -pw + 30, -ph / 2 + 96, pw - 60, 6, gap=36, seed=8)
            with saved(c, sx, 0, (-cs, 1 + 0.05 * math.sin(ang))) as cc:
                _page_panel(cc, -pw, pw, ph, -1, left_content if cs < -0.6 else None)
        # centre gutter line
        if e > 0.5:
            c.move_to(sx, -ph / 2 + 4)
            c.line_to(sx, ph / 2 - 4)
            c.set_source_rgba(*hexc("ink", 0.6))
            c.set_line_width(4)
            c.stroke()


_BURST_PTS = None


def _burst_path(c, r, inner=0.74, n=15, seed=11):
    pts = []
    for j in range(2 * n):
        a = -math.pi / 2 + j * math.pi / n
        if j % 2 == 0:
            rr = r * (0.9 + 0.12 * hash01(j, seed))
        else:
            rr = r * inner * (0.92 + 0.1 * hash01(j, seed + 1))
        pts.append((math.cos(a) * rr * 1.06, math.sin(a) * rr * 0.94))
    poly(c, pts)


def _draw_silhouette(c, k, eyes):
    """Cloaked-villain silhouette (pop-up cut-out). Origin = base centre."""
    if k <= 0.01:
        return
    with saved(c, 0, 0, (1.0, k)) as cc:
        # cape body + high pointed collar + round head
        cc.move_to(-150, 0)
        cc.curve_to(-120, -110, -96, -190, -78, -246)
        cc.line_to(-122, -318)                      # collar point L
        cc.line_to(-52, -282)
        cc.curve_to(-30, -290, 30, -290, 52, -282)
        cc.line_to(122, -318)                       # collar point R
        cc.line_to(78, -246)
        cc.curve_to(96, -190, 120, -110, 150, 0)
        cc.close_path()
        fill_stroke(cc, SIL, "ink", 6)
        circle(cc, 0, -322, 46)
        fill_stroke(cc, SIL, "ink", 6)
        # rim light (purple) on the cape edges
        cc.move_to(-140, -8)
        cc.curve_to(-112, -110, -90, -190, -74, -240)
        cc.move_to(140, -8)
        cc.curve_to(112, -110, 90, -190, 74, -240)
        cc.set_source_rgba(*hexc(SIL_RIM, 0.9))
        cc.set_line_width(5)
        cc.stroke()
        # glowing eyes
        if eyes > 0.01:
            for sx in (-1, 1):
                with saved(cc, sx * 17, -326, 1.0, sx * 0.25):
                    ellipse(cc, 0, 0, 13 * eyes + 1, 5 * eyes + 1)
                    cc.set_source_rgba(*hexc("#fff3a0"))
                    cc.fill()
            radial_glow(cc, 0, -326, 70, "ai_accent", 0.35 * eyes)


def _draw_bombshell(ctx, t, T, bx, by):
    """The pop-up comic burst out of the open book (bombshell plot twist)."""
    if t < T.burst:
        return
    base_y = by - 18                                    # pop-up hinge on the pages
    k = ease_out_back(seg(t, T.burst, T.burst + 0.34), 1.9)
    wob = 1 + 0.025 * math.sin((t - T.burst) * 5.0) * (t > T.burst + 0.34)
    radial_glow(ctx, BURST_C[0], BURST_C[1], 520, "ai_accent", 0.26 * smoothstep(seg(t, T.burst, T.burst + 0.3)))
    # pop-up struts (folded paper tabs from the gutter)
    with saved(ctx, bx, base_y, (1.0, k)) as c:
        for sx in (-1, 1):
            poly(c, [(sx * 40, 0), (sx * 112, -150), (sx * 82, -160), (sx * 14, 0)])
            fill_stroke(c, PAGE, "ink", 4)
    # the burst (hinged at the page, rises + spins in)
    with saved(ctx, bx, base_y, (k, k)) as c:
        c.translate(BURST_C[0] - bx, BURST_C[1] - base_y)
        c.rotate(0.35 * (1 - k))
        c.scale(wob, wob)
        with saved(c, 10, 14):
            _burst_path(c, BURST_R)
            c.set_source_rgba(*hexc("ink", 0.3))
            c.fill()
        _burst_path(c, BURST_R)
        fill_stroke(c, BURST_OUT, "ink", 7)
        _burst_path(c, BURST_R * 0.8, 0.8, seed=5)
        fill_stroke(c, BURST_IN, "ink", 5)
        circle(c, 0, -20, BURST_R * 0.42)
        c.set_source_rgba(1, 1, 1, 0.35)
        c.fill()
    # silhouette rises from the page on "plot", eyes flash on "twist!"
    if t >= T.sil:
        ks = ease_out_back(seg(t, T.sil, T.sil + 0.32), 1.6)
        eyes = smoothstep(seg(t, T.twist, T.twist + 0.12))
        with saved(ctx, bx, base_y + 2, 0.92) as c:
            _draw_silhouette(c, ks, eyes)
    # BOMBSHELL (on "bombshell") / TWIST! (slams on "twist!")
    kb = ease_out_back(seg(t, T.burst + 0.06, T.burst + 0.3), 2.6)
    if kb > 0.01:
        with saved(ctx, BURST_C[0], BURST_C[1] - 160, kb, -0.06) as c:
            text(c, "BOMBSHELL", 0, 36, 104, "white", "comic", outline="ink", outline_w=14)
    if t >= T.twist:
        d = t - T.twist
        hit = 0.1
        if d < hit:
            q = ease_in(d / hit)
            sc, a = lerp(2.2, 0.94, q), clamp(d / 0.04)
        else:
            sc, a = 0.94 + 0.06 * ease_out_back(seg(d, hit, hit + 0.26), 3.0), 1.0
        with saved(ctx, BURST_C[0] + 10, BURST_C[1] + 196, sc, -0.08, alpha_=a) as c:
            text(c, "TWIST!", 0, 50, 140, "danger", "comic", outline="ink", outline_w=16)
            text(c, "TWIST!", 0, 50, 140, "danger", "comic", outline="#ffffff", outline_w=5)
        if hit <= d < hit + 0.32:                          # impact ring
            q = (d - hit) / 0.32
            with saved(ctx, BURST_C[0] + 10, BURST_C[1] + 170, 1.0, -0.08):
                ellipse(ctx, 0, 0, 230 + 90 * q, 80 + 40 * q)
                ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - q))
                ctx.set_line_width(9)
                ctx.stroke()
    # paper stars flying out of the page
    if T.burst <= t < T.burst + 0.9:
        tt = t - T.burst
        fade = 1 - smoothstep(seg(tt, 0.55, 0.9))
        for j in range(10):
            ang = -math.pi / 2 + (hash01(j, 31) - 0.5) * 2.6
            sp = 700 + 380 * hash01(j, 32)
            px = bx + math.cos(ang) * sp * tt
            py = base_y - 40 + math.sin(ang) * sp * tt + 700 * tt * tt
            col = ("ai_accent", "#ffffff", BURST_OUT, "safe", "ai_rim")[j % 5]
            P._star4(ctx, px, py, 16 + 6 * hash01(j, 33), tt * 8 + j)
            P._fs(ctx, col, "ink", 3, fade)
    if t >= T.twist:
        P.sparkles(ctx, BURST_C[0], BURST_C[1] - 10, BURST_R + 30, t, n=8, seed=9,
                   color="white", size=1.0)


def _f4(ctx, t, info, T):
    global _ROWS
    A = T.assemble
    P.ai_bg(ctx, t, motes=8, floor=False)
    rows = _row_layout(ctx, F4_ROW)
    _ROWS = rows
    strip = _strip_layout(ctx, F4_ROW[0], F4_ROW[1], F4_ROW[2])
    f2_rows = _row_layout(ctx, F2_ROW)
    g_bomb = smoothstep(seg(t, T.reveal, T.reveal + 0.3)) * (1 - smoothstep(seg(t, T.wall0, T.wall0 + 0.6)))
    if g_bomb > 0.01:
        radial_glow(ctx, BOMB_C[0], BOMB_C[1] - 20, 360, "danger", 0.3 * g_bomb)

    if t < T.rearr:
        # --- the sum: tiles + plus signs + bar + "?" -------------------------
        a_sum = 1 - smoothstep(seg(t, T.gather, T.gather + 0.2))
        rs = F4_ROW[2]
        for j in range(2):
            if t >= T.plus_t[j]:
                k = ease_out_back(seg(t, T.plus_t[j], T.plus_t[j] + 0.25), 2.6)
                # centre of the free space between tile j's knob and tile j+1
                px = (rows[j][0] + (_TW[j] / 2 + KNOB) * rs + rows[j + 1][0] - _TW[j + 1] / 2 * rs) / 2
                _plus(ctx, px, F4_ROW[1], k, a_sum, size=22)
        _sum_bar(ctx, t, T, rows, a_sum)
        a_q = 1 - smoothstep(seg(t, T.reveal - 0.1, T.reveal + 0.1))
        _q_mark(ctx, t, T, a_q)
        # --- tiles ----------------------------------------------------------------
        todo = []
        for i in range(3):
            if t < T.gather:
                u = seg(t, T.row_t[i], T.row_land[i])
                e = ease_in_out(u)
                sx, sy = f2_rows[i]
                x = lerp(sx, rows[i][0], e)
                y = lerp(sy + 80, rows[i][1], e) - 50 * math.sin(math.pi * u)
                s = lerp(F2_ROW[2], F4_ROW[2], e)
                rot = (-0.05, 0.04, -0.03)[i] * (1 - 0.5 * e)
                land = seg(t, T.row_land[i], T.row_land[i] + 0.16)
                sq = math.sin(math.pi * land) * 0.12 if 0 < land < 1 else 0.0
                if u >= 1:
                    y += math.sin((t - T.row_land[i]) * 2.4 + i * 2.1) * 4
                    rot += math.sin((t - T.row_land[i]) * 1.7 + i) * 0.02
                # "those words" -> a little hop each; checks hop too
                y -= 12 * _bump(t, T.w_those + 0.1 * i, 0.22) + 14 * _bump(t, T.chk[i], 0.22)
                todo.append((x, y, s, i, rot, sq, 1.0, 1.0))
            elif t < T.drop[0]:
                # "Together?": slide in and click (edges lock)
                u = seg(t, T.gather, T.click)
                e = ease_in_out(u)
                x = lerp(rows[i][0], strip[i][0], e)
                y = rows[i][1]
                sq = 0.1 * _bump(t, T.click, 0.14)
                todo.append((x, y, F4_ROW[2], i, 0.0, sq, 1.0, 1.0))
            else:
                # the locked strip drops into the "?" and becomes the picture
                u = seg(t, T.drop[0], T.drop[1])
                e = ease_in(u)
                cx = F4_ROW[0]
                s = lerp(1.0, 0.42, e)
                x = cx + (strip[i][0] - cx) * s
                s *= F4_ROW[2]
                y = lerp(F4_ROW[1], Q_C[1], e)
                a = 1 - smoothstep(seg(t, T.reveal - 0.04, T.reveal + 0.1))
                todo.append((x, y, s, i, 0.0, 0.0, 1.0, a))
        if t < T.gather:
            for args in todo:
                _draw_tile(ctx, *args)
        else:                                   # touching: all shadows, then bodies
            for args in todo:
                _draw_tile(ctx, *args, part="shadow")
            for args in todo:
                _draw_tile(ctx, *args, part="body")
        if T.click <= t < T.click + 0.25:                    # click flash
            q = (t - T.click) / 0.25
            for j in range(2):
                xx = strip[j][0] + _TW[j] / 2 * F4_ROW[2]
                circle(ctx, xx, F4_ROW[1], 16 + 46 * q)
                ctx.set_source_rgba(1, 1, 1, 0.75 * (1 - q))
                ctx.set_line_width(6)
                ctx.stroke()
        # "sounds harmless" checks (fade as the tiles come together)
        if t < T.gather + 0.25:
            for i in range(3):
                bxx = rows[i][0] + (_TW[i] / 2 - 16) * F4_ROW[2]
                byy = rows[i][1] - (TILE_H / 2 + 6) * F4_ROW[2] + math.sin((t - T.row_land[i]) * 2.4 + i * 2.1) * 4
                _check_badge(ctx, bxx, byy - 14 * _bump(t, T.chk[i], 0.22), t, T.chk[i], T.gather)
            if t >= T.ok_lab:
                k = pop(t, T.ok_lab, 0.3)
                a = 1 - smoothstep(seg(t, T.gather, T.gather + 0.2))
                with saved(ctx, OK_CHIP[0], OK_CHIP[1], k, alpha_=a) as c:
                    P.label_tag(c, 0, 0, "SOUNDS HARMLESS", color="safe", size=50, font="comic",
                                text_color="white", pointer="down")
        # --- the bomb + label -----------------------------------------------------
        if t >= T.reveal:
            k = ease_out_back(seg(t, T.reveal, T.reveal + 0.3), 2.0)
            a = smoothstep(seg(t, T.reveal, T.reveal + 0.12))
            pulse = 1 + 0.03 * math.sin((t - T.reveal) * 7) * (t > T.reveal + 0.3)
            with saved(ctx, BOMB_C[0], BOMB_C[1], lerp(0.6, 1.0, k) * pulse, alpha_=a) as c:
                P.cartoon_bomb(c, 0, 0, BOMB_S, t, lit=True)
            if T.reveal <= t < T.reveal + 0.35:
                q = (t - T.reveal) / 0.35
                circle(ctx, BOMB_C[0], BOMB_C[1], 90 + 130 * q)
                ctx.set_source_rgba(1, 0.9, 0.9, 0.6 * (1 - q))
                ctx.set_line_width(10)
                ctx.stroke()
            _hurt_label(ctx, t, T, BOMB_C[0], HURT_Y)
    else:
        # --- payoff: bomb -> tiles -> storybook -> BOMBSHELL TWIST! ---------------
        bx, by, bs = _book_pose(t, T)
        if t < T.split:
            with saved(ctx, BOMB_C[0], BOMB_C[1]):
                P.cartoon_bomb(ctx, 0, 0, BOMB_S, t, lit=True)
            _hurt_label(ctx, t, T, BOMB_C[0], HURT_Y)
        elif t < T.book_in:
            if t < T.split + 0.14:                             # pop flash
                q = (t - T.split) / 0.14
                circle(ctx, BOMB_C[0], BOMB_C[1], 80 + 120 * q)
                ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - q))
                ctx.fill()
            cl = _strip_layout(ctx, BOMB_C[0], BOMB_C[1], 0.7)
            for i in range(3):
                u = seg(t, T.flip[0] + 0.04 * i, T.flip[1])
                e = ease_in_out(u)
                ox, oy = cl[i][0], BOMB_C[1] + (i - 1) * 40
                x = lerp(ox, bx, e)
                y = lerp(oy, by, e) - 80 * math.sin(math.pi * u)
                fx = math.cos(0.5 * math.pi * u)
                _draw_tile(ctx, x, y, lerp(0.7, 0.9, e), i, (i - 1) * 0.3 * (1 - e), 0.0, fx)
        else:
            k_in = ease_out_back(seg(t, T.book_in, T.book_in + 0.3), 2.0)
            fxb = max(0.02, k_in)
            jig = _bump(t, T.w_blast, 0.3)
            open_u = ease_in_out(seg(t, T.open[0], T.open[1]))
            with saved(ctx, bx, by, (fxb * (1 + 0.08 * jig), 1 - 0.06 * jig)) as c:
                c.translate(-bx, -by)
                _draw_book(c, t, T, bx, by, bs, open_u)
            if T.book_in <= t < T.book_in + 0.5:
                P.sparkles(ctx, bx, by, 260, t, n=6, seed=2, color="white", size=0.9)
            if T.w_blast <= t < T.w_blast + 0.8:
                P.sparkles(ctx, bx, by - 40, 280, t, n=6, seed=6, color="ai_accent", size=1.0)
            _draw_bombshell(ctx, t, T, bx, by)
    _wall(ctx, t, T)
    # --- the inset ---------------------------------------------------------------
    expr, hands, tgt, think, blink, nod = _f4_state(t, T)
    ix, iy, isz = _inset(t, T)
    desired = (0.0, 0.0) if tgt is None else _dir(ix, iy - 10, tgt[0], tgt[1])
    look = _ai_look(expr, desired)
    draw_ai(ctx, ix, iy, isz, t, expr=expr, look=look, mouth=info.mouth("ai", t),
            hands=hands, think=think, blink=blink, aura=0, nod=nod)


# ===========================================================================
# F1: "Confound it... that does sound fun."
# ===========================================================================
def _f1_end_state(t, T):
    L8 = T.L8
    ek = [(0.0, "frustrated", 0.01),
          (T.w_that - 0.05, "thinking", 0.25),
          (T.w_sound - 0.08, "evil_grin", 0.28)]
    expr = _keyed(t, ek)
    arms = _keyed(t, [(0.0, "rest", 0.01), (L8.start - 0.12, "fist", 0.18),
                      (T.w_that - 0.05, "chin", 0.3),
                      (T.w_sound - 0.05, "rub", 0.3),
                      (T.tally + 0.3, "steeple", 0.35)])
    # "Confound it" up at the AI (screen-right) -> ponders -> sly grin to
    # camera -> glances at the chip on the tally -> back to camera
    lk = [(0.0, (0.55, -0.15)),
          (T.w_that - 0.05, (0.7, -0.6)),
          (T.w_sound - 0.08, (0.15, 0.0)),
          (T.tally, (-0.6, -0.95)),
          (T.tally + 0.45, (0.05, 0.0))]
    look = _vlook(expr, _lk(t, lk, 0.12))
    # Snake: side-eye at him through the grumbling -> nods along ("fun")
    sk = _keyed(t, [(0.0, "unimpressed", 0.01), (T.w_that, "side_eye", 0.2),
                    (T.w_sound, "nod", 0.25), (T.tally + 0.6, "happy", 0.3)])
    slk = [(0.0, (1.0, -0.35)), (T.w_that, (1.0, 0.0)), (T.w_sound, (0.6, -0.2))]
    tongue = True if T.w_fun + 0.35 <= t < T.w_fun + 0.6 else False
    snake = {"expr": sk, "look": _lk(t, slk, 0.15), "tongue": tongue}
    return expr, arms, look, snake


def _f1_end(ctx, t, info, T):
    L8 = T.L8
    expr, arms, look, snake = _f1_end_state(t, T)
    mouth = info.mouth("villain", t)
    P.lair_bg(ctx, t, bolt_seed=4)
    draw_villain(ctx, VX, VY, VS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                 snake=snake)
    P.desk(ctx, VX, VY, 1000)
    P.computer(ctx, 835, 1218, 0.7, view="side", facing=-1, t=t)
    P.keyboard(ctx, VX, VY, 360, t, typing=False)
    an = V.anchors(VX, VY, VS)
    P.emote(ctx, "anger", an["dome"][0] + 40, an["dome"][1] - 10, 0.85, t, L8.start + 0.05,
            t_out=T.w_that)
    ex, ey = an["eye_r"]
    P.emote(ctx, "sparkle", ex + 92, ey - 70, 0.8, t, T.w_fun - 0.05, t_out=T.w_fun + 0.9)


# ===========================================================================
# entry points
# ===========================================================================
def render(ctx, t, info):
    T = _times(info)
    if t < T.cut_f2:
        _f1_open(ctx, t, info, T)
    elif t < T.assemble:
        _f2(ctx, t, info, T)
    elif t < T.cut_f1:
        _f4(ctx, t, info, T)
    else:
        _f1_end(ctx, t, info, T)
    trick_card(ctx, t, T.card, T.card_num, T.card_title)
    nice_tries_chip(ctx, t, info.meta.get("tries_before", 5), info.meta.get("tries_after", 6),
                    T.tally)


def SFX(info):
    T = _times(info)
    out = [
        (T.card, "page_flip", -6),
        (T.card + 0.12, "stamp", -4),
        (T.L1.start, "tiptoe", -12),
        (T.w_notice + 0.35, "snake_hiss", -14),
        # disguise1: the costume halo springs on
        (T.d1, "pop", -6),
        (T.d1 + 0.05, "boing", -14),
        (T.L2.start, "typing", -12),
        (T.w_sparky + 0.05, "scan_beep", -16),
        (T.w_long + 0.05, "scan_beep", -16),
        (T.L2.end, "send", -8),
    ]
    out += [(tp, "puzzle_click", -8) for tp in T.tile_t]
    out += [(T.halo_off, "boing", -10), (T.halo_off + 0.04, "whoosh", -14)]
    # F4: tiles line up, the sum appears
    out += [(tl, "puzzle_click", -12) for tl in T.row_land]
    out += [(tp, "pop", -12) for tp in T.plus_t]
    out += [(T.bar_t, "swoosh_up", -16), (T.q_t, "pop", -10)]
    # l06b: a check per tile, the chip, click together, drop -> bomb, label
    out += [(tc, "scan_beep", -12) for tc in T.chk]
    out += [(T.ok_lab, "pop", -12),
            (T.click, "puzzle_click", -5),
            (T.reveal, "puzzle_click", -4),
            (P.stamp_impact(T.hurt), "stamp", -5)]
    # l06c: the wall, thuds on the first 3 rows
    out += [(tl, "brick_thud", -5 if j == 0 else -7)
            for j, tl in enumerate(T.wall_lands[:3])]
    # rearrange + l07: wall slides aside, tiles flip into the storybook,
    # the pop-up BOMBSHELL TWIST! (dun-dun-dun: last hit lands on "twist!")
    out += [(T.wall_mv[0], "whoosh", -9),
            (T.split, "pop", -8),
            (T.flip[0], "swoosh_up", -12),
            (T.book_in, "magic_chime", -8),
            (T.w_blast, "sparkle", -12),
            (T.open[0], "page_flip", -6),
            (T.burst, "dun_dun_dun", -12),
            (T.burst, "pop", -10),
            (T.twist + 0.08, "sparkle", -10),
            (T.w_sound + 0.3, "snake_hiss", -16),
            (T.tally, "tick", -8),
            (T.tally, "pop", -10)]
    return sorted(out, key=lambda e: e[0])
