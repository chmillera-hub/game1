"""s07 - Trick #6: TINY INNOCENT PIECES (music 'sneaky').

Covers *hiding where the harm is* and *leaving out the ending*.
Every time below is derived from cues / word starts (see _times).

  F1-PUSH  card .. l02     Dim lair, slow push-in on Malvo + Hissy. Card #6
                            slams + parks. "Snake... tiny pieces." whisper lean
                            to Hissy (chin hand), brow waggle, eye dart to
                            camera on "never see". Hissy: slow 😒 blink, then
                            side-eye. disguise1: fake handlebar mustache pops
                            on top of his real one + "random_guy_42" tag.
  F2 CHAT  l02 .. assemble  Three bubbles (font 36) with usernames, typed in
                            sync. Cameo: beret + shades (disguise2), curly wig
                            and the mustache hops onto Hissy (disguise3, the
                            cameo widens to show him). AI reads, brow up,
                            two-step lid drop. 'pieces': ROUND BALL / FUSE /
                            SPARK pop out of the bubbles as puzzle pieces.
                            l05: disguises fly off one by one, LID DROP.
  F4 VISION assemble .. l08 The pieces line up SEPARATELY; the puzzle-box lid
                            with the cartoon-bomb picture slides up.
                            l06: inset points, arrow to the box.
                            l06b: "Alone, each piece looks harmless" -> a green
                            check pops on each piece + HARMLESS ALONE chip;
                            "Together?" -> they snap into the bomb; on
                            "Instructions" a red "= HOW TO HURT PEOPLE" label
                            slams onto the assembled picture.
                            l06c: a brick wall (NOPE) drops in front of it,
                            thud per row; inset punches in, determined -> 😒
                            at camera. rearrange: the wall glides up over the
                            box picture, the pieces behind it pop out and flip
                            into balloon + string + cake.
                            l07: a new (party) lid slides in behind them,
                            sparkles, confetti on "party!".
  F1 LAIR  l08 .. end       "Confound it!" fist; Hissy in a party hat holds the
                            red balloon string in his mouth (the traitor).
                            Tally 5 -> 6, Malvo deflates.
"""
import math

import cairocffi as cairo

from engine.core import (text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, smoothstep,
                         hash01, noise1, ellipse, poly, smooth_path, hexc, radial_glow, pop,
                         set_font)
from engine import props as P
from engine import villain as V
from engine import snake as SN
from engine.villain import draw_villain
from engine import ai_char as _AIC
from engine.ai_char import EXPR as AI_EXPR

# QA fix: the rig's stock "point_up" (back of the hand, thumb tucked behind the
# finger) reads as a rude middle finger at 720p. For this scene's draw_ai calls
# only, swap in a diagonal (up-right, toward the box lid) index point with the thumb out (the rig's
# pose lookup is restored right after each call).
_SAFE_POINT_UP_R = _AIC._H(315, 25, 0.7, open=0.0, index=1.0, thumb=0.45, tl=0.8)


def draw_ai(*args, **kw):
    prev = _AIC._pose

    def _pose(name, t, seed):
        out = prev(name, t, seed)
        if name == "point_up":
            out["R"] = dict(_SAFE_POINT_UP_R)
        return out

    _AIC._pose = _pose
    try:
        return _AIC.draw_ai(*args, **kw)
    finally:
        _AIC._pose = prev


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
COL_X, COL_Y, COL_W = 330, 235, 590      # F2 bubble column
CAP_H = 30                               # username caption above each bubble
CAM_A = (200, 350, 120, (495, 742), 200.0)      # cameo: face (+ disguise hats)
CAM_B = (205, 362, 130, (380, 745), 288.0)      # cameo: face + Hissy (whole head)
# QA: y 738 -> 712 so the parked pieces (+5 px idle float) clear the AI's halo
PIECE_DST = [(372, 712), (540, 712), (708, 712)]   # between the bubbles and the AI's halo
PIECE_S = 0.75
PIECES = [  # label, colour, tabs (top, right, bottom, left), resting tilt, bubble word
    ("ROUND\nBALL", "ai_accent", (0, 1, 0, -1), -0.07, "round ball"),
    ("FUSE", "bubble_ai", (0, 1, 0, -1), 0.05, "long fuse"),
    ("SPARK", "warn", (0, 1, 0, -1), 0.09, "sparky"),
]
USERS = ["random_guy_42", "definitely_not_evil", "TotallyDifferentGuy"]

# F4 vision
INSET = (230, 1170, 0.33)
LID_C = (530, 415)
LID_S = 1.2
LID_W, LID_H = 420, 300
WALL = (262, 219, 536, 392)              # precision wall: the box lid only
BOMB_C = (530, 850)
ROW = [(325, 860), (552, 860), (780, 860)]   # l06b: pieces side by side ("alone")
ROW_S = 1.0
WALL_C = (210, 600, 640, 468)            # l06c: wall in front of the assembled picture
WALL_ROWS, WALL_SPEED = 5, 1.5
BOMB_S = 1.8
CLUSTER = [(-80, 60), (80, 60), (80, -100)]  # snapped piece offsets from BOMB_C
CL_S = 1.0
BAL_C = (440, 800)                       # balloon centre
BAL_S = 1.4
STR_END = (418, 1040)                    # balloon string bottom
CAKE_B = (662, 1008)                     # cake bottom-centre
CAKE_S = 1.35
LID2_C = (540, 880)
LID2_S = 1.28

# F1 end
END_BAL = (112, 562)
END_BAL_S = 1.05

# bespoke colours
STACHE_FAKE, STACHE_FAKE_HI = "#6e3f1c", "#9a6234"
BERET, BERET_DK = "#c42a48", "#8e1730"
WIG, WIG_DK = "#ffd23f", "#d9a514"
SHADES = "#1b1526"
BALLOON, BALLOON_DK = "#ef3346", "#b81f30"
CAKE, CAKE_DK, CAKE_TOP = "#ff8fb8", "#e0679a", "#ffb7d2"
CARDBOARD, CARDBOARD_DK = "#d9b27c", "#b48a52"
CONF_COLS = ["ai_accent", "danger", "safe", "bubble_villain", "ai_rim", "#ff8fb8"]


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


def _times(info):
    key = (info.id, info.dur, id(info))
    if key in _TCACHE:
        return _TCACHE[key]
    c = info.cue
    T = _T()
    T.card = c("card")
    T.l = {i: info.line(f"s07_l0{i}") for i in range(1, 9)}
    T.l6b, T.l6c = info.line("s07_l06b"), info.line("s07_l06c")
    T.explain = c("explain")
    T.d1, T.d2, T.d3 = c("disguise1"), c("disguise2"), c("disguise3")
    T.pieces = c("pieces")
    T.assemble = c("assemble")
    T.rearr = c("rearrange")
    T.tally = c("tally")
    T.end = info.dur
    T.cut_f2 = T.l[2].start
    # cut once the AI's caption has cleared (captions hold 0.35 s after a line)
    T.cut_f1 = min(T.l[8].start - 0.05, max(T.l[7].end + 0.35, T.l[8].start - 0.25))
    # word starts
    T.w_tiny = _ws(info, "s07_l01", 1)
    T.w_never = _ws(info, "s07_l01", 4)
    T.w_see1 = _ws(info, "s07_l01", 5)
    T.w_big = _ws(info, "s07_l01", 7)
    T.w_round = _ws(info, "s07_l02", 4)        # "a big, round ball?"
    T.w_long = _ws(info, "s07_l03", 2)         # "a long fuse?"
    T.w_fuse = _ws(info, "s07_l03", 3)
    T.w_totally = _ws(info, "s07_l04", 0)
    T.w_something = _ws(info, "s07_l04", 4)
    T.w_sparky = _ws(info, "s07_l04", 5)
    T.w_same = _ws(info, "s07_l05", 2)
    T.w_see = _ws(info, "s07_l06", 3)
    T.w_picture = _ws(info, "s07_l06", 5)
    T.w_on = _ws(info, "s07_l06", 6)
    T.w_box = _ws(info, "s07_l06", 8)
    T.w_each = _ws(info, "s07_l06b", 1)
    T.w_harmless = _ws(info, "s07_l06b", 4)
    T.w_together = _ws(info, "s07_l06b", 5)
    T.w_instr = _ws(info, "s07_l06b", 6)
    T.w_hurting = _ws(info, "s07_l06b", 8)
    T.w_so = _ws(info, "s07_l06c", 0)
    T.w_stop = _ws(info, "s07_l06c", 5)
    T.w_better = _ws(info, "s07_l07", 2)
    T.w_bday = _ws(info, "s07_l07", 4)
    T.w_party = _ws(info, "s07_l07", 5)
    T.w_it = _ws(info, "s07_l08", 1)
    # F2 beats
    T.piece_t = [T.pieces + 0.12 * i for i in range(3)]
    T.fly = [T.l[5].start + d for d in (0.1, 0.35, 0.6)]   # stache(Hissy), beret+shades, wig
    # F4 beats
    A = T.assemble
    T.row_t = [A + 0.1 * i for i in range(3)]            # pieces glide into a row
    T.row_land = [t0 + 0.5 for t0 in T.row_t]
    T.lid_in = A + 0.45
    T.lid_land = T.lid_in + 0.5
    # l06b: "Alone, each piece looks harmless." -> a check per piece
    T.chk = [T.w_each, (T.w_each + T.w_harmless) / 2, T.w_harmless]
    T.ok_lab = T.w_harmless + 0.12
    # "Together?" -> snap into the bomb; "Instructions..." -> red label
    T.gather = T.w_together - 0.15
    T.snap = [T.gather + 0.25 + 0.1 * i for i in range(3)]
    T.reveal = T.snap[2] + 0.02
    T.hurt = T.w_instr - 0.05
    # l06c: the wall drops in front of the assembled picture
    T.wall0 = T.l6c.start + 0.02
    T.wall_lands = P.brick_wall_land_times(T.wall0, WALL_ROWS, WALL_SPEED)
    T.punch = T.w_stop - 0.2                             # inset punch-in
    T.meh = T.w_stop + 0.3                               # 😒 at camera
    # rearrange: wall glides up over the box picture, pieces pop out
    T.wall_mv = (T.rearr, T.rearr + 0.45)
    T.split = T.rearr + 0.22
    T.gift_land = [T.split + 0.12 + 0.06 * i + 0.55 for i in range(3)]
    T.lid2 = T.w_better - 0.05
    T.blink_f2 = T.l[5].start + 1.0
    T.blink_f4 = [T.lid_land + 0.6, T.explain + 0.05, T.l6c.start - 0.25]
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


def _snake_xform(c, t, vexpr, varms, sexpr, x=VX, y=VY, s=VS, lean=0.0, seed=1):
    """Apply the transform of Hissy's head as drawn by draw_villain(snake=...)."""
    p = V.resolve_expr(vexpr)
    _, _, a_shy, _, _ = V.resolve_arms(varms, t)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    c.translate(x, y)
    c.scale(s, s)
    if lean:
        c.rotate(lean)
    c.translate(V.SNAKE_HEAD[0], V.SNAKE_HEAD[1] + shy * 0.6 - breath * 1.5)
    c.scale(V.SNAKE_SCALE, V.SNAKE_SCALE)
    sp = SN.resolve_expr(sexpr)
    ss = seed + 4
    nph = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = sp["nod"] * (max(0.0, nph) * 16 - 3)
    nod_rot = sp["nod"] * 0.09 * max(0.0, nph)
    bob = math.sin(t * 2 * math.pi * 0.45 + ss) * 2.5
    sway = noise1(t * 0.6, ss + 3) * 0.035
    wob = sp["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    c.translate(0, sp["hy"] + bob + nod_dy)
    c.rotate(sp["tilt"] + sway + nod_rot + wob)
    if sp["sq"] != 1.0:
        c.scale(1 / math.sqrt(sp["sq"]), sp["sq"])


def _face_turn(p, look):
    lx = clamp(look[0] + p["ex"], -1.2, 1.2)
    return lx * 9.0


def _pt(fn, *a, pt=(0, 0), **kw):
    """World point of a rig-local point via a transform function."""
    m = cairo.Matrix()
    fn(m, *a, **kw)
    return m.transform_point(*pt)


# ===========================================================================
# Bespoke props: disguises, gifts, lids
# ===========================================================================
def draw_fake_stache(c, x, y, k=1.0, rot=0.0, sq=(1.0, 1.0)):
    """Big fake handlebar mustache. (x, y) = centre of its top edge (~ upper lip)."""
    if k <= 0.01:
        return
    with saved(c, x, y, (k * sq[0], k * sq[1]), rot):
        for sx in (-1, 1):                       # curled ends (behind the bulk)
            c.move_to(sx * 84, 4)
            c.curve_to(sx * 120, 6, sx * 134, -26, sx * 118, -44)
            c.curve_to(sx * 106, -56, sx * 90, -44, sx * 101, -33)
            c.set_source_rgba(*hexc("ink"))
            c.set_line_width(25)
            c.stroke()
            c.move_to(sx * 84, 4)
            c.curve_to(sx * 120, 6, sx * 134, -26, sx * 118, -44)
            c.curve_to(sx * 106, -56, sx * 90, -44, sx * 101, -33)
            c.set_source_rgba(*hexc(STACHE_FAKE))
            c.set_line_width(14)
            c.stroke()
        c.move_to(-98, 2)
        c.curve_to(-64, -18, -22, -16, 0, -4)
        c.curve_to(22, -16, 64, -18, 98, 2)
        c.curve_to(74, 30, 30, 34, 0, 20)
        c.curve_to(-30, 34, -74, 30, -98, 2)
        c.close_path()
        fill_stroke(c, STACHE_FAKE, "ink", 5)
        for sx in (-1, 1):                       # hair strokes
            for j in range(3):
                ox = sx * (26 + j * 22)
                c.move_to(ox, 2 + j * 1.5)
                c.curve_to(ox + sx * 8, 10, ox + sx * 12, 16, ox + sx * 14, 20 - j * 2)
        c.set_source_rgba(*hexc(STACHE_FAKE_HI))
        c.set_line_width(3.5)
        c.stroke()


def draw_shades(c, x, y, k=1.0, rot=0.0):
    """Disguise sunglasses. (x, y) = between the eyes."""
    if k <= 0.01:
        return
    with saved(c, x, y, k, rot):
        for sx in (-1, 1):
            c.move_to(sx * 108, -14)
            c.line_to(sx * 156, -24)
        c.set_source_rgba(*hexc("ink"))
        c.set_line_width(8)
        c.stroke()
        c.move_to(-16, -10)
        c.curve_to(-6, -22, 6, -22, 16, -10)
        c.set_line_width(9)
        c.stroke()
        for sx in (-1, 1):
            rrect(c, sx * 62 - 52, -34, 104, 70, 28)
            fill_stroke(c, SHADES, "ink", 5)
            c.save()
            rrect(c, sx * 62 - 52, -34, 104, 70, 28)
            c.clip()
            poly(c, [(sx * 62 - 30, -40), (sx * 62 - 8, -40), (sx * 62 - 44, 40),
                     (sx * 62 - 66, 40)])
            c.set_source_rgba(1, 1, 1, 0.28)
            c.fill()
            c.restore()


def draw_beret(c, x, y, k=1.0, rot=0.22):
    """Jaunty beret. (x, y) = where it sits on the dome."""
    if k <= 0.01:
        return
    with saved(c, x, y, k, rot):
        c.move_to(-4, -36)
        c.curve_to(-2, -54, 10, -56, 12, -44)
        c.set_source_rgba(*hexc("ink"))
        c.set_line_width(13)
        c.stroke()
        c.move_to(-4, -36)
        c.curve_to(-2, -54, 10, -56, 12, -44)
        c.set_source_rgba(*hexc(BERET_DK))
        c.set_line_width(6)
        c.stroke()
        ellipse(c, 0, 0, 122, 42)
        fill_stroke(c, BERET, "ink", 5)
        c.save()
        ellipse(c, 0, 0, 122, 42)
        c.clip()
        ellipse(c, 14, 26, 120, 30)
        c.set_source_rgba(*hexc(BERET_DK, 0.8))
        c.fill()
        ellipse(c, -40, -16, 40, 10, -0.15)
        c.set_source_rgba(1, 1, 1, 0.25)
        c.fill()
        c.restore()
        ellipse(c, 0, 0, 122, 42)
        fill_stroke(c, None, "ink", 5)


_WIG_CURLS = []
for _i in range(11):
    _a = math.pi + math.pi * _i / 10
    _WIG_CURLS.append((math.cos(_a) * 168, -100 + math.sin(_a) * 128, 36 - 3 * abs(_i - 5) / 5))
for _i in range(6):
    _a = math.pi * 1.12 + math.pi * 0.76 * _i / 5
    _WIG_CURLS.append((math.cos(_a) * 98, -112 + math.sin(_a) * 80, 34))
_WIG_CURLS += [(-176, -48, 30), (176, -48, 30), (-168, 0, 25), (168, 0, 25)]


def draw_wig(c, x, y, k=1.0, rot=0.0):
    """Curly yellow wig. (x, y) = face origin (eye-line centre)."""
    if k <= 0.01:
        return
    with saved(c, x, y, k, rot):
        for (cx, cy, r) in _WIG_CURLS:
            circle(c, cx, cy, r + 5)
        c.set_source_rgba(*hexc("ink"))
        c.fill()
        for (cx, cy, r) in _WIG_CURLS:
            circle(c, cx, cy, r)
        c.set_source_rgba(*hexc(WIG))
        c.fill()
        for j, (cx, cy, r) in enumerate(_WIG_CURLS):
            c.new_sub_path()
            c.arc(cx + 2, cy + 2, r * 0.48, 0.3 + j, 0.3 + j + 4.2)
        c.set_source_rgba(*hexc(WIG_DK))
        c.set_line_width(5)
        c.stroke()
        for (cx, cy, r) in _WIG_CURLS[:11:3]:
            ellipse(c, cx - r * 0.35, cy - r * 0.4, r * 0.28, r * 0.16, -0.5)
        c.set_source_rgba(1, 1, 1, 0.45)
        c.fill()


def draw_party_hat(c, x, y, k=1.0, rot=-0.25):
    """Striped party cone with a pom-pom. (x, y) = centre of its base."""
    if k <= 0.01:
        return
    with saved(c, x, y, k, rot):
        cone = [(-36, 0), (36, 0), (0, -96)]
        poly(c, cone)
        c.set_source_rgba(*hexc("#ff8fb8"))
        c.fill()
        c.save()
        poly(c, cone)
        c.clip()
        for j, col in enumerate(("#ffd166", "#5ee7ff", "#ffd166", "#5ee7ff")):
            yy = -12 - j * 24
            poly(c, [(-60, yy), (60, yy - 26), (60, yy - 14), (-60, yy + 12)])
            c.set_source_rgba(*hexc(col))
            c.fill()
        c.restore()
        poly(c, cone)
        fill_stroke(c, None, "ink", 5)
        circle(c, 0, -100, 14)
        fill_stroke(c, "#ffffff", "ink", 4)
        ellipse(c, 0, 2, 40, 7)
        fill_stroke(c, "#ffd166", "ink", 4)


def draw_balloon(c, x, y, s=1.0, rot=0.0, sq=(1.0, 1.0)):
    """Red party balloon (§6.4). (x, y) = balloon centre; knot at (0, 58)*s."""
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


def draw_string(c, x0, y0, x1, y1, t, curls=3.0, amp=13.0, phase=0.0, p=1.0):
    """Curly balloon string from (x0, y0) (knot) to (x1, y1). p: drawn fraction."""
    n = 36
    pts = []
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    m = max(2, int(n * clamp(p)))
    for i in range(m + 1):
        u = i / n
        w = math.sin(u * curls * 2 * math.pi + phase + t * 2.2) * amp * math.sin(math.pi * min(1, u * 1.4))
        pts.append((x0 + dx * u + nx * w, y0 + dy * u + ny * w))
    for layer in (0, 1):
        smooth_path(c, pts)
        c.set_source_rgba(*hexc("ink" if layer == 0 else "#f6f2ff"))
        c.set_line_width(8 if layer == 0 else 3.5)
        c.stroke()


def draw_cake(c, x, y, s, t, fizz=True):
    """Two-tier pink birthday cake with one sparkler candle (§6.4).
    (x, y) = bottom-centre (plate). 160 x 110 at s=1 (+ candle)."""
    with saved(c, x, y, s) as cc:
        ellipse(cc, 0, -4, 98, 13)
        fill_stroke(cc, "#f4f1fb", "ink", 4)
        # bottom tier
        rrect(cc, -80, -64, 160, 60, 12)
        fill_stroke(cc, CAKE, "ink", 5)
        cc.save()
        rrect(cc, -80, -64, 160, 60, 12)
        cc.clip()
        cc.rectangle(-90, -20, 180, 30)
        cc.set_source_rgba(*hexc(CAKE_DK, 0.7))
        cc.fill()
        cc.restore()
        # drips (bottom tier)
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
        # top tier
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
        # sparkler candle
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


def _jig_line(c, x0, y0, x1, y1, knob=1):
    """Faint jigsaw seam (straight line with one knob) for printed pictures."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * knob, ux * knob

    def Q(u, v):
        return (x0 + dx * u + nx * v, y0 + dy * u + ny * v)
    c.move_to(x0, y0)
    c.line_to(*Q(0.42, 0))
    c.curve_to(*Q(0.40, 14), *Q(0.46, 22), *Q(0.5, 22))
    c.curve_to(*Q(0.54, 22), *Q(0.60, 14), *Q(0.58, 0))
    c.line_to(x1, y1)


def draw_lid(c, x, y, s, t, kind="bomb", rot=0.0):
    """PUZZLE BOX LID (§6.12): 420x300 cardboard, the picture printed on it,
    corner tag '1000 PCS'. kind='bomb' (the plan) or 'party' (better picture)."""
    w, h = LID_W, LID_H
    with saved(c, x, y, s, rot) as cc:
        rrect(cc, -w / 2 + 9, -h / 2 + 12, w, h, 22)
        cc.set_source_rgba(0, 0, 0, 0.35)
        cc.fill()
        base = CARDBOARD if kind == "bomb" else "#f3d9a8"
        dk = CARDBOARD_DK if kind == "bomb" else "#d8b47a"
        rrect(cc, -w / 2, -h / 2, w, h, 22)
        fill_stroke(cc, base, "ink", 5)
        cc.save()
        rrect(cc, -w / 2, -h / 2, w, h, 22)
        cc.clip()
        cc.rectangle(-w / 2, h / 2 - 24, w, 30)
        cc.set_source_rgba(*hexc(dk))
        cc.fill()
        cc.restore()
        cc.move_to(-w / 2 + 6, h / 2 - 24)
        cc.line_to(w / 2 - 6, h / 2 - 24)
        cc.set_source_rgba(*hexc("ink"))
        cc.set_line_width(4)
        cc.stroke()
        # picture panel
        px0, py0, pw, ph = -w / 2 + 24, -h / 2 + 22, w - 48, h - 70
        rrect(cc, px0, py0, pw, ph, 14)
        fill_stroke(cc, "#fff4de" if kind == "bomb" else "#ffffff", "ink", 4)
        cc.save()
        rrect(cc, px0, py0, pw, ph, 14)
        cc.clip()
        if kind == "bomb":
            circle(cc, -20, 30, 120)
            cc.set_source_rgba(*hexc("#ffd6c9"))
            cc.fill()
            P.cartoon_bomb(cc, -24, 40, 0.92, 0.37, lit=True)
        else:
            cc.rectangle(px0, py0, pw, ph)
            cc.set_source_rgba(*hexc("#fff0f6"))
            cc.fill()
        # faint jigsaw seams
        for (a, b, k_) in (((px0 + pw / 3, py0), (px0 + pw / 3, py0 + ph), 1),
                           ((px0 + 2 * pw / 3, py0), (px0 + 2 * pw / 3, py0 + ph), -1),
                           ((px0, py0 + ph / 2), (px0 + pw, py0 + ph / 2), 1)):
            _jig_line(cc, a[0], a[1], b[0], b[1], k_)
        cc.set_source_rgba(*hexc("ink", 0.18))
        cc.set_line_width(3)
        cc.stroke()
        cc.restore()
        # corner tag
        with saved(cc, w / 2 - 66, -h / 2 + 14, 1.0, 0.12) as tc:
            rrect(tc, -58, -20, 116, 40, 10)
            fill_stroke(tc, "danger" if kind == "bomb" else "bubble_ai", "ink", 4)
            text(tc, "1000 PCS", 0, 9, 24, "white", "round")


# ===========================================================================
# Disguise state (what Malvo / Hissy wear at time t, with pop / fly values)
# ===========================================================================
def _fly(t, t0, dur=0.42):
    """0 before t0 .. 1 when gone."""
    return ease_in(seg(t, t0, t0 + dur)) if t >= t0 else 0.0


def _draw_disguises(c, t, T, expr, arms, mouth, look, lean=0.0, snake_expr="idle",
                    stache_on_malvo=True):
    """Draws the disguise layers in F1 coordinates (c must be in F1 space)."""
    # --- Malvo's head items -------------------------------------------------
    k_st = _squash_pop(t, T.d1)
    k_sh = pop(t, T.d2, 0.3)
    k_be = pop(t, T.d2 + 0.08, 0.3)
    k_wg = pop(t, T.d3, 0.3)
    f_bs = _fly(t, T.fly[1])
    f_wg = _fly(t, T.fly[2])
    # mustache hop Malvo -> Hissy at disguise3
    hop_t0 = T.d3 + 0.06
    hop_u = seg(t, hop_t0, hop_t0 + 0.32) if t >= hop_t0 else 0.0
    with saved(c) as cc:
        p = _vhead_xform(cc, t, expr, arms, mouth, lean=lean)
        turn = _face_turn(p, look)
        mx = p["mx"] + turn * 1.1
        if k_wg > 0.01 and f_wg < 1:
            with saved(cc, 0, -260 * f_wg - 40 * f_wg * f_wg, 1.0, 0.5 * f_wg):
                draw_wig(cc, 0, 0, k_wg * (1 + 0.12 * _bump(t, T.d3, 0.3)))
        if k_be > 0.01 and f_bs < 1:
            lift = -26 * smoothstep(k_wg) if f_wg < 1 else 0.0
            draw_beret(cc, 26 + 320 * f_bs, -196 + lift - 300 * f_bs, k_be, 0.22 + 2.2 * f_bs)
        if k_sh > 0.01 and f_bs < 1:
            draw_shades(cc, turn - 280 * f_bs, -4 - 220 * f_bs, k_sh, -1.6 * f_bs)
        if hop_u <= 0.0 and k_st[0] > 0.01:
            draw_fake_stache(cc, mx, 92, 1.0, 0.0, k_st)
    # --- the hop ---------------------------------------------------------
    if 0.0 < hop_u < 1.0:
        a = _pt(_vhead_xform, t, expr, arms, mouth, lean=lean, pt=(0, 92))
        b = _pt(_snake_xform, t, expr, arms, snake_expr, lean=lean, pt=(0, 27))
        e = ease_in_out(hop_u)
        hx = lerp(a[0], b[0], e)
        hy = lerp(a[1], b[1], e) - 120 * math.sin(math.pi * hop_u)
        sc = lerp(VS, VS * V.SNAKE_SCALE * 0.62, e)
        draw_fake_stache(c, hx, hy, sc, -2 * math.pi * e)
    elif hop_u >= 1.0:
        f_hs = _fly(t, T.fly[0])
        if f_hs < 1:
            with saved(c) as cc:
                _snake_xform(cc, t, expr, arms, snake_expr, lean=lean)
                lsq = math.sin(math.pi * seg(t, hop_t0 + 0.32, hop_t0 + 0.55)) * 0.2
                draw_fake_stache(cc, -260 * f_hs, 27 - 200 * f_hs, 0.62,
                                 -1.8 * f_hs, (1 + lsq, 1 - lsq))


# ===========================================================================
# F1: the opening whisper (dim, pushed in)
# ===========================================================================
def _f1_open_state(t, T):
    L1 = T.l[1]
    ek = [(0.0, "sneaky", 0.25),
          (T.w_tiny, "smug", 0.1), (T.w_tiny + 0.15, "sneaky", 0.1),
          (T.w_tiny + 0.3, "smug", 0.1), (T.w_tiny + 0.45, "sneaky", 0.1),
          (T.w_big - 0.05, "evil_grin", 0.25),
          (L1.end + 0.05, "smug", 0.25),
          (T.d1 + 0.14, "sneaky", 0.1), (T.d1 + 0.29, "smug", 0.1),
          (T.d1 + 0.44, "sneaky", 0.1), (T.d1 + 0.56, "smug", 0.1)]
    expr = _keyed(t, ek)
    HISSY = (-1.0, 0.12)
    CAM = (0.0, 0.0)
    lk = [(0.0, CAM), (0.22, (0.75, 0.0)), (0.36, CAM),
          (L1.start + 0.05, HISSY),
          (T.w_never, CAM), (T.w_never + 0.3, HISSY),
          (L1.end + 0.05, CAM)]
    look = _vlook(expr, _lk(t, lk, 0.1))
    arms = _keyed(t, [(0.0, "rub", 0.3), (L1.start, "chin", 0.32),
                      (L1.end - 0.05, "steeple", 0.35)])
    lean = (-0.06 * smoothstep(seg(t, L1.start, L1.start + 0.4))
            * (1 - smoothstep(seg(t, L1.end - 0.1, L1.end + 0.25))))
    # Hissy
    sk = _keyed(t, [(0.0, "unimpressed", 0.2), (T.w_see1, "side_eye", 0.25),
                    (T.d1 + 0.02, "unimpressed", 0.15)])
    slk = [(0.0, (0.1, -1.0)), (L1.start + 0.1, (1.0, -0.35)), (T.w_see1, (1.0, 0.0)),
           (T.d1 + 0.02, (1.0, -0.2))]
    slook = _lk(t, slk, 0.18)
    sblink = _blink_pulse(t, T.w_tiny + 0.55, 0.2, 0.18, 0.22)
    tongue = True if T.w_big + 0.35 <= t < T.w_big + 0.6 else False
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
        _draw_disguises(c, t, T, expr, arms, mouth, look, lean, snake["expr"])
        P.desk(c, VX, VY, 1000)
        P.computer(c, 835, 1218, 0.7, view="side", facing=-1, t=t, glow=0.8)
        P.keyboard(c, VX, VY, 360, t, typing=False)
        if t >= T.d1 + 0.08:
            k = pop(t, T.d1 + 0.08, 0.32)
            bob = math.sin((t - T.d1) * 5.0) * 4
            with saved(c, VX + 20, 474 + bob, k, -0.04):
                P.label_tag(c, 0, 0, "random_guy_42", color="ui_dark", size=26,
                            pointer="down")


# ===========================================================================
# F2: the chat
# ===========================================================================
def _bubble_specs(info):
    return [("s07_l02", USERS[0], PIECES[0][4]), ("s07_l03", USERS[1], PIECES[1][4]),
            ("s07_l04", USERS[2], PIECES[2][4])]


def _bubble_layouts(ctx, info, T):
    out = []
    y = COL_Y
    for (lid, user, word) in _bubble_specs(info):
        L = info.line(lid)
        hl = [{"text": word, "t0": 0.0, "style": "underline", "color": "warn"}]
        lay = P.bubble_layout(ctx, COL_X, y + CAP_H, COL_W, L.text, "villain", hl, 36)
        out.append((lid, user, word, y, lay))
        y = y + CAP_H + lay + 14
    return out


def _bubbles(ctx, t, info, T):
    lays = _bubble_layouts(ctx, info, T)
    dim = 1.0 - 0.7 * ease_in_out(seg(t, T.pieces, T.pieces + 0.3))
    word_t = {"s07_l02": T.w_round, "s07_l03": T.w_long, "s07_l04": T.w_sparky}
    send_t = {"s07_l02": T.l[2].end, "s07_l03": T.l[3].end, "s07_l04": T.l[4].end}

    def draw(c):
        for i, (lid, user, word, y, lay) in enumerate(lays):
            L = info.line(lid)
            if t < L.start:
                continue
            nud = -6 * _bump(t, send_t[lid], 0.3)
            hl = [{"text": word, "t0": word_t[lid] + 0.1, "style": "underline",
                   "color": "warn"}]
            a_cap = clamp((t - L.start) / 0.2)
            bx, by, bw, bh = lay.rect
            text(c, user, bx + bw - 6, y + 22 + nud, 24, (0.66, 0.68, 0.78, a_cap), "ui",
                 "right")
            P.chat_bubble(c, COL_X, y + CAP_H + nud, COL_W, L.text, "villain", t, L.start,
                          highlight=hl, font_size=36, reveal=_reveal(info, lid, t))
            g = _bump(t, send_t[lid], 0.4)
            if g > 0.01:
                rrect(c, bx - 4, by - 4 + nud, bw + 8, bh + 8, 30)
                c.set_source_rgba(1, 1, 1, 0.8 * g)
                c.set_line_width(6)
                c.stroke()
            # the hole left where the word popped out
            ti = T.piece_t[i]
            if t >= ti:
                for (rx, ry, rw, rh) in lay.spans.get(word, [])[:2]:
                    k = ease_out(seg(t, ti, ti + 0.15))
                    rrect(c, rx - 6, ry + 2, rw + 12, rh, 10)
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
    return lays


def _cameo_state(t, T):
    L2, L3, L4, L5 = T.l[2], T.l[3], T.l[4], T.l[5]
    ek = [(0.0, "smug", 0.2),
          (T.w_round + 0.25, "sneaky", 0.1), (T.w_round + 0.4, "smug", 0.1),
          (T.w_round + 0.55, "sneaky", 0.1), (T.w_round + 0.7, "smug", 0.1),
          (T.d2 + 0.02, "excited", 0.12), (T.d2 + 0.4, "smug", 0.25),
          (L3.start + 0.05, "hopeful", 0.25),
          (T.w_long, "sneaky", 0.25),
          (T.d3 + 0.02, "excited", 0.15),
          (T.w_something - 0.05, "sneaky", 0.25),
          (T.w_sparky, "evil_grin", 0.1), (T.w_sparky + 0.3, "hopeful", 0.2),
          (T.fly[0], "thinking", 0.12),
          (T.fly[1] + 0.02, "shocked", 0.1),
          (T.fly[2] + 0.1, "sheepish", 0.3)]
    expr = _keyed(t, ek)
    AI = (0.62, 0.72)
    CAM = (0.0, 0.0)
    PCS = (0.85, 0.6)
    lk = [(0.0, (0.3, 0.45)),
          (T.w_round + 0.25, CAM),
          (L2.end + 0.05, AI),
          (T.d2 + 0.02, CAM),
          (L3.start + 0.05, (-0.25, -0.75)),
          (T.w_long, AI),
          (T.d3 + 0.02, CAM),
          (T.w_something - 0.05, AI),
          (T.w_sparky, CAM),
          (T.pieces + 0.05, PCS),
          (T.fly[0], (-0.95, 0.15)),               # at Hissy's mustache flying
          (T.fly[1] + 0.02, (0.1, -0.5)),
          (T.fly[2] + 0.1, AI)]
    look = _vlook(expr, _lk(t, lk, 0.1))
    # Hissy (only fully visible once the cameo widens)
    sk = _keyed(t, [(0.0, "unimpressed", 0.2), (T.d3 + 0.45, "side_eye", 0.25),
                    (T.fly[0] + 0.15, "nod", 0.25)])
    slk = [(0.0, (1.0, -0.3)), (T.d3 + 0.45, (1.0, 0.0)), (T.fly[0] + 0.15, (1.0, 0.1))]
    snake = {"expr": sk, "look": _lk(t, slk, 0.18),
             "tongue": True if T.d3 + 1.1 <= t < T.d3 + 1.35 else False}
    return expr, look, snake


def _cameo_geom(t, T):
    k = ease_in_out(seg(t, T.d3 - 0.04, T.d3 + 0.34))
    a, b = CAM_A, CAM_B
    bump = 0.0
    for td in (T.d2, T.d3):
        bump = max(bump, _bump(t, td, 0.3) * 0.07)
    for tf in T.fly:
        bump = max(bump, _bump(t, tf, 0.22) * 0.04)
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k) * (1 + bump),
            (lerp(a[3][0], b[3][0], k), lerp(a[3][1], b[3][1], k)), lerp(a[4], b[4], k))


def _draw_cameo(ctx, t, info, T):
    expr, look, snake = _cameo_state(t, T)
    mouth = info.mouth("villain", t)
    cx, cy, r, view, zoom = _cameo_geom(t, T)

    def extra(c):
        _draw_disguises(c, t, T, expr, "rest", mouth, look, 0.0, snake["expr"])

    villain_cameo(ctx, t, expr=expr, look=look, mouth=mouth, arms="rest", snake=snake,
                  cx=cx, cy=cy, r=r, extra=extra, view=view, zoom=zoom)
    # disguise pop sparkle on the ring
    for td in (T.d2, T.d3):
        if td <= t < td + 0.45:
            P.sparkles(ctx, cx, cy, r + 20, t, n=5, seed=int(td * 10) % 7, color="white",
                       size=0.8)
    return cx, cy, r


def _piece_pos_f2(t, T, i, lays):
    """Piece i in the chat: pops out of its word and floats above the AI."""
    t0 = T.piece_t[i]
    lab, col, tabs, rot_end, word = PIECES[i]
    lay = lays[i][4]
    rects = lay.spans.get(word, [])
    if rects:
        xs = [rx + rw / 2 for (rx, ry, rw, rh) in rects]
        ys = [ry + rh / 2 for (rx, ry, rw, rh) in rects]
        src = (sum(xs) / len(xs), sum(ys) / len(ys))
    else:
        src = (700, 400 + 140 * i)
    dst = PIECE_DST[i]
    u = seg(t, t0 + 0.06, t0 + 0.5)
    e = ease_in_out(u)
    x = lerp(src[0], dst[0], e)
    y = lerp(src[1], dst[1], e) - 70 * math.sin(math.pi * u)
    k = lerp(0.3, 1.0, ease_out_back(seg(t, t0, t0 + 0.24), 2.0))
    land = seg(t, t0 + 0.5, t0 + 0.68)
    sq = math.sin(math.pi * land) * 0.14 if 0 < land < 1 else 0.0
    rot = lerp(0.5 * (1 if i != 1 else -1), rot_end, e)
    # idle float after landing
    if u >= 1.0:
        y += math.sin((t - t0) * 2.6 + i * 2.1) * 5
        rot += math.sin((t - t0) * 1.9 + i) * 0.03
    return x, y, PIECE_S * k, sq, rot


def _draw_piece(ctx, x, y, s, i, rot=0.0, sq=0.0, fx=1.0, a=1.0):
    lab, col, tabs, rot_end, word = PIECES[i]
    with saved(ctx, x, y, (fx * (1 + sq), 1 - sq), alpha_=a) as c:
        P.puzzle_piece(c, 0, 0, s, col, None, rot, tabs)
        # big comic label (the rig's auto-fit label shrank to ~18 px on screen)
        lines = lab.split("\n")
        fs = 50 if len(lines) == 1 else 42
        with saved(c, 0, 0, s, rot) as cl:
            for j, ln in enumerate(lines):
                yy = 18 + (j - (len(lines) - 1) / 2) * fs * 0.98
                text(cl, ln, 12 if tabs[3] < 0 else 0, yy, fs, "white", "comic",
                     outline="ink", outline_w=9)


def _ai_f2_state(t, info, T, lays):
    L2, L3, L4, L5 = T.l[2], T.l[3], T.l[4], T.l[5]
    half = {k: lerp(AI_EXPR["neutral"][k], AI_EXPR["unimpressed"][k], 0.5)
            for k in AI_EXPR["neutral"]}
    ek = [(0.0, "neutral", 0.2),
          (L2.start + 0.2, "thinking", 0.3),
          (L2.end + 0.05, "skeptical", 0.25),
          (T.d2 + 0.02, "alert", 0.12),
          (T.d2 + 0.4, "skeptical", 0.25),
          (L3.start + 0.35, "thinking", 0.3),
          (L3.end + 0.05, "skeptical", 0.25),
          (T.d3 + 0.1, half, 0.45),                       # two-step lid drop, step 1
          (L5.start - 0.05, "unimpressed", 0.4)]          # LID DROP
    expr = _keyed(t, ek)
    hands = _keyed(t, [(0.0, "idle", 0.3), (T.pieces - 0.08, "present_both", 0.22),
                       (L5.start, "idle", 0.4)])
    think = 0.0
    for (a_, b_, v) in ((L2.start + 0.2, L2.end + 0.05, 0.6), (L3.start + 0.35, L3.end, 0.6),
                        (T.pieces - 0.08, T.pieces + 0.6, 0.9)):
        if a_ <= t < b_:
            think = v * smoothstep(seg(t, a_, a_ + 0.2)) * (1 - smoothstep(seg(t, b_ - 0.15, b_)))
    # where the eyes go
    E = (AIX, AIY - 24)
    CAMEO = (-0.8, -0.7)

    def follow(idx, lid):
        lay = lays[idx][4]
        bx, by, bw, bh = lay.rect
        r = _reveal(info, lid, t)
        nl = len(lay.lines)
        li = min(nl - 1, int(r * nl))
        fr = clamp(r * nl - li)
        tx = bx + 30 + (bw - 60) * fr
        ty = by + 26 + li * 45
        d = _dir(E[0], E[1], tx, ty)
        return (d[0] * 1.6, d[1])

    if t < L2.start + 0.2:
        d = (0.35, -0.85)
    elif t < L2.end + 0.05:
        d = follow(0, "s07_l02")
    elif t < L3.start + 0.35:
        d = CAMEO
    elif t < L3.end + 0.05:
        d = follow(1, "s07_l03")
    elif t < L4.start + 0.2:
        d = CAMEO
    elif t < L4.end:
        d = follow(2, "s07_l04")
    elif t < T.pieces:
        d = CAMEO
    elif t < L5.start - 0.05:
        q = seg(t, T.pieces, T.pieces + 0.45)
        d = _dir(E[0], E[1], lerp(PIECE_DST[0][0], PIECE_DST[2][0], q), PIECE_DST[0][1])
    else:
        d = CAMEO
    blink = _blink_pulse(t, T.blink_f2, 0.14, 0.08, 0.14)
    return expr, hands, think, d, blink


def _f2(ctx, t, info, T):
    P.ai_bg(ctx, t)
    lays = _bubbles(ctx, t, info, T)
    _draw_cameo(ctx, t, info, T)
    expr, hands, think, desired, blink = _ai_f2_state(t, info, T, lays)
    look = _ai_look(expr, desired)
    an = draw_ai(ctx, AIX, AIY, AIS, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                 hands=hands, think=think, blink=blink)
    # the pieces (with a faint tractor glow from the AI's palms while lifting)
    if T.pieces - 0.05 <= t < T.l[5].start + 0.3:
        a = smoothstep(seg(t, T.pieces - 0.05, T.pieces + 0.15)) * \
            (1 - smoothstep(seg(t, T.l[5].start, T.l[5].start + 0.3)))
        for h in ("handL", "handR"):
            hx, hy = an[h]
            circle(ctx, hx, hy - 10, 26 + 6 * math.sin(t * 9))
            ctx.set_source_rgba(*hexc("ai_rim", 0.25 * a))
            ctx.fill()
    for i in range(3):
        if t >= T.piece_t[i]:
            x, y, s, sq, rot = _piece_pos_f2(t, T, i, lays)
            _draw_piece(ctx, x, y, s, i, rot, sq)


# ===========================================================================
# F4: the vision (assemble -> rearrange -> party)
# ===========================================================================
def _gift_targets():
    sx = (STR_END[0] + BAL_C[0]) / 2
    sy = (STR_END[1] + BAL_C[1] + 58 * BAL_S) / 2
    return [BAL_C, (sx, sy), (CAKE_B[0], CAKE_B[1] - 55 * CAKE_S)]


def _balloon_pose(t, T):
    """Balloon centre + tilt (bobbing once it has landed)."""
    tl = T.gift_land[0]
    bob = math.sin((t - tl) * 2 * math.pi * 0.6) * 9 if t > tl else 0.0
    sway = math.sin((t - tl) * 2 * math.pi * 0.35 + 0.8) * 0.05 if t > tl else 0.0
    return (BAL_C[0] + sway * 120, BAL_C[1] + bob), sway


def _draw_gift(ctx, t, T, i, x, y, fx=1.0, sq=0.0, landed=False):
    """Gift i drawn around its flight point (x, y) (landed: final layout)."""
    if i == 0:
        (bx, by), sway = _balloon_pose(t, T) if landed else ((x, y), 0.0)
        draw_balloon(ctx, bx, by, BAL_S, sway, (fx * (1 + sq), 1 - sq))
    elif i == 1:
        if landed:
            (bx, by), sway = _balloon_pose(t, T)
            kx, ky = bx - math.sin(sway) * 70, by + 68 * BAL_S
            draw_string(ctx, kx, ky, STR_END[0] + sway * 40, STR_END[1], t, curls=3.2, amp=13)
        else:
            hh = (STR_END[1] - BAL_C[1] - 68 * BAL_S) / 2
            with saved(ctx, x, y, (fx, 1.0)) as c:
                draw_string(c, 0, -hh, -12, hh, t, curls=3.2, amp=13)
    else:
        with saved(ctx, x, y + 55 * CAKE_S, (fx * (1 + sq), 1 - sq)) as c:
            draw_cake(c, 0, 0, CAKE_S, t)


def _f4_state(t, T):
    """Inset AI expression / hands / desired look / think / blink / nod."""
    A = T.assemble
    L6, L6b, L6c = T.l[6], T.l6b, T.l6c
    # LID DROP once the box picture lands (held >= 0.8 s), skeptical point on
    # "see the picture"; l06b: calm "present" at the pieces, alert on
    # "Together?", determined from "Instructions"; l06c: "stop" palm, then a
    # held 😒 at camera until the rearrange.
    ek = [(0.0, "thinking", 0.2),
          (T.lid_land - 0.1, "unimpressed", 0.4),
          (T.w_see - 0.1, "skeptical", 0.25),
          (L6b.start - 0.15, "neutral", 0.3),
          (T.gather, "alert", 0.15),
          (T.w_instr - 0.05, "determined", 0.25),
          (T.meh, "unimpressed", 0.35),
          (T.rearr + 0.15, "determined", 0.15),
          (T.split + 0.25, "happy", 0.3)]
    expr = _keyed(t, ek)
    hands = _keyed(t, [(0.0, "chin", 0.3), (T.lid_land - 0.1, "idle", 0.35),
                       (T.w_see - 0.3, "point_up", 0.3),
                       (L6b.start - 0.15, "present", 0.3),
                       (T.gather, "idle", 0.3),
                       (T.w_stop - 0.15, "stop", 0.18),
                       (T.meh + 0.25, "idle", 0.4),
                       (T.split + 0.3, "present", 0.3),
                       (T.w_party - 0.05, "thumbs_up", 0.2)])
    ix, iy, _ = _inset(t, T)
    E = (ix, iy - 10)
    if t < T.lid_in:
        d = _dir(E[0], E[1], ROW[1][0], ROW[1][1])
    elif t < T.lid_land + 0.1:
        d = _dir(E[0], E[1], LID_C[0], LID_C[1] + 300 * (1 - seg(t, T.lid_in, T.lid_land)))
    elif t < L6.end + 0.1:
        d = _dir(E[0], E[1], LID_C[0] - 60, LID_C[1] + 60)
    elif t < T.chk[0] - 0.1:
        d = _dir(E[0], E[1], ROW[1][0], ROW[1][1])
    elif t < T.gather:
        i = 0 if t < T.chk[1] - 0.1 else (1 if t < T.chk[2] - 0.1 else 2)
        if t >= T.ok_lab + 0.15:
            i = 1
        d = _dir(E[0], E[1], ROW[i][0], ROW[i][1])
    elif t < T.wall0:
        d = _dir(E[0], E[1], BOMB_C[0], BOMB_C[1])
    elif t < T.meh:
        d = _dir(E[0], E[1], WALL_C[0] + WALL_C[2] / 2, WALL_C[1] + WALL_C[3] / 2)
    elif t < T.rearr + 0.1:
        d = (0.0, 0.0)                                   # 😒 straight at camera
    elif t < T.w_party:
        d = _dir(E[0], E[1], LID2_C[0], LID2_C[1] - 40)
    else:
        d = _dir(E[0], E[1], CAKE_B[0], CAKE_B[1] - 150)
    think = 0.8 * (1 - smoothstep(seg(t, A + 0.5, A + 0.8)))
    think = max(think, 0.6 * _bump(t, T.chk[0] - 0.15, T.ok_lab - T.chk[0] + 0.3))
    blink = None
    for tb in T.blink_f4:
        b = _blink_pulse(t, tb, 0.14, 0.08, 0.14)
        if b is not None:
            blink = b
    nod = 0.6 if T.w_party <= t < T.w_party + 0.6 else 0.0
    return expr, hands, d, think, blink, nod


def _inset(t, T):
    """Inset AI position/scale: punches in for the 😒 at the end of l06c."""
    k = ease_in_out(seg(t, T.punch, T.punch + 0.35)) * \
        (1 - ease_in_out(seg(t, T.rearr + 0.1, T.rearr + 0.45)))
    ix, iy, isz = INSET
    return ix + 6 * k, iy - 22 * k, isz * (1 + 0.24 * k)


def _check_badge(ctx, x, y, t, t_in, t_out=None, r=34):
    """Small green 'harmless alone' check badge (pops in at t_in)."""
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


def _hurt_label(ctx, t, T, x, y):
    """Red '= HOW TO HURT PEOPLE' label slammed onto the assembled picture."""
    t_in = T.hurt
    if t < t_in:
        return
    d = t - t_in
    hit = 0.11
    if d < hit:
        q = ease_in(d / hit)
        sc, rot, a = lerp(2.0, 0.92, q), -0.06 - 0.3 * (1 - q), clamp(d / 0.05)
    else:
        sc = 0.92 + 0.08 * ease_out_back(seg(d, hit, hit + 0.28), 3.2)
        rot, a = -0.06, 1.0
    with saved(ctx, x, y, sc, rot, alpha_=a) as c:
        P.label_tag(c, 0, 0, "= HOW TO HURT PEOPLE", color="danger", size=60, font="comic",
                    text_color="white")
    if hit <= d < hit + 0.3:                              # impact ticks
        q = (d - hit) / 0.3
        with saved(ctx, x, y, 1.0, -0.06):
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
    """The l06c wall: built in front of the assembled picture, then (rearrange)
    glides up and shrinks to sit exactly over the box lid's picture."""
    if t < T.wall0:
        return
    wx, wy, ww, wh = WALL_C
    k = ease_in_out(seg(t, T.wall_mv[0], T.wall_mv[1]))
    s_end = WALL[2] / ww
    x = lerp(wx, WALL[0], k)
    y = lerp(wy, WALL[1], k)
    s = lerp(1.0, s_end, k)
    land = seg(t, T.wall_mv[1], T.wall_mv[1] + 0.22)
    sq = math.sin(math.pi * land) * 0.05 if 0 < land < 1 else 0.0
    with saved(ctx) as c:
        c.translate(x + ww * s / 2, y + wh * s)
        c.scale(s * (1 + sq), s * (1 - sq))
        c.translate(-ww / 2, -wh)
        P.brick_wall(c, 0, 0, ww, wh, t, T.wall0, rows=WALL_ROWS, speed=WALL_SPEED, seed=7, drop=300,
                     label={"text": "NOPE", "size": 120})


def _f4(ctx, t, info, T):
    A = T.assemble
    P.ai_bg(ctx, t, motes=8, floor=False)
    # --- glow (danger while it's a bomb, warm once it's a party) -------------
    g_bomb = smoothstep(seg(t, T.reveal, T.reveal + 0.3)) * (1 - smoothstep(seg(t, T.wall0, T.wall0 + 0.6)))
    g_party = smoothstep(seg(t, T.split + 0.2, T.split + 0.7))
    if g_bomb > 0.01:
        radial_glow(ctx, BOMB_C[0], BOMB_C[1] - 30, 360, "danger", 0.3 * g_bomb)
    if g_party > 0.01:
        radial_glow(ctx, LID2_C[0], LID2_C[1] - 20, 420, "ai_accent", 0.2 * g_party)
    # --- the box lid (slides up; the wall later glides over it) ---------------
    if t >= T.lid_in and t < T.wall_mv[1] + 0.05:
        u = seg(t, T.lid_in, T.lid_land)
        ly = lerp(2150, LID_C[1], ease_out_back(u, 1.2))
        hop = _bump(t, T.w_box, 0.3) * 0.06
        draw_lid(ctx, LID_C[0], ly, LID_S * (1.0 + hop), t, "bomb", rot=-0.02 * (1 - u))
    # --- the new (party) lid behind the gifts --------------------------------
    if t >= T.lid2:
        # pops up in place behind the gifts (a slide from below would cross the
        # caption band while "better picture" is on screen)
        k = ease_out_back(seg(t, T.lid2, T.lid2 + 0.36), 1.7)
        a = smoothstep(seg(t, T.lid2, T.lid2 + 0.1))
        with saved(ctx, alpha_=a) as c:
            draw_lid(c, LID2_C[0], LID2_C[1] + 60 * (1 - k), LID2_S * lerp(0.35, 1.0, k), t,
                     "party", rot=0.015 + 0.12 * (1 - k))
    # --- pieces (alone) -> bomb (together) -> wall -> pieces -> gifts ---------
    if t < T.rearr:
        for i in range(3):
            lab_rot = PIECES[i][3]
            if t < T.gather:
                # glide from the chat into a spaced row, then idle-float
                u = seg(t, T.row_t[i], T.row_land[i])
                e = ease_in_out(u)
                sx, sy = PIECE_DST[i]
                x = lerp(sx, ROW[i][0], e)
                y = lerp(sy, ROW[i][1], e) - 50 * math.sin(math.pi * u)
                s = lerp(PIECE_S, ROW_S, e)
                rot = lab_rot * (1 - 0.5 * e)
                land = seg(t, T.row_land[i], T.row_land[i] + 0.16)
                sq = math.sin(math.pi * land) * 0.12 if 0 < land < 1 else 0.0
                if u >= 1:
                    y += math.sin((t - T.row_land[i]) * 2.4 + i * 2.1) * 5
                    rot += math.sin((t - T.row_land[i]) * 1.7 + i) * 0.025
                # each one gets inspected: a little hop as its check lands
                hop = _bump(t, T.chk[i], 0.22)
                y -= 14 * hop
                _draw_piece(ctx, x, y, s, i, rot, sq)
            else:
                # "Together?": spin to the centre and snap into one picture
                ts = T.snap[i]
                u = seg(t, T.gather + 0.05 * i, ts)
                e = ease_in_out(u)
                sx, sy = ROW[i]
                tx, ty = BOMB_C[0] + CLUSTER[i][0], BOMB_C[1] + CLUSTER[i][1]
                x = lerp(sx, tx, e)
                y = lerp(sy, ty, e) - 50 * math.sin(math.pi * u)
                rot = (lerp(lab_rot * 0.5, 0.0, e) + math.pi * (1 - e) * (1 if i % 2 else -1)) \
                    if u < 1 else 0.0
                s = lerp(ROW_S, CL_S, e)
                land = seg(t, ts, ts + 0.16)
                sq = math.sin(math.pi * land) * 0.12 if 0 < land < 1 else 0.0
                a = 1.0 - smoothstep(seg(t, T.reveal + 0.02, T.reveal + 0.22))
                if a > 0.01:
                    _draw_piece(ctx, x, y, s, i, rot, sq, 1.0, a)
                if 0 <= t - ts < 0.25:                      # snap flash
                    q = (t - ts) / 0.25
                    circle(ctx, x - 60 if i else x + 60, y, 20 + 50 * q)
                    ctx.set_source_rgba(1, 1, 1, 0.7 * (1 - q))
                    ctx.set_line_width(6)
                    ctx.stroke()
        # "harmless alone" checks (fade as the pieces come together)
        if t < T.gather + 0.25:
            for i in range(3):
                bx = ROW[i][0] + 62 + (8 if i < 2 else -4)
                by = ROW[i][1] - 74 + math.sin((t - T.row_land[i]) * 2.4 + i * 2.1) * 5
                _check_badge(ctx, bx, by - 14 * _bump(t, T.chk[i], 0.22), t, T.chk[i], T.gather)
            if t >= T.ok_lab:
                k = pop(t, T.ok_lab, 0.3)
                a = 1 - smoothstep(seg(t, T.gather, T.gather + 0.2))
                with saved(ctx, ROW[1][0], ROW[1][1] + 150, k, alpha_=a) as c:
                    P.label_tag(c, 0, 0, "HARMLESS ALONE", color="safe", size=52, font="comic",
                                text_color="white", pointer="up")
        if t >= T.reveal:
            k = ease_out_back(seg(t, T.reveal, T.reveal + 0.3), 2.0)
            a = smoothstep(seg(t, T.reveal, T.reveal + 0.18))
            pulse = 1 + 0.03 * math.sin((t - T.reveal) * 7) * (t > T.reveal + 0.3)
            with saved(ctx, BOMB_C[0], BOMB_C[1], lerp(0.8, 1.0, k) * pulse, alpha_=a) as c:
                P.cartoon_bomb(c, 0, 0, BOMB_S, t, lit=True)
            # jigsaw seams stay faintly visible ("it IS the pieces")
            sa = 0.25 + 0.3 * (1 - smoothstep(seg(t, T.reveal + 0.3, T.reveal + 1.2)))
            with saved(ctx, BOMB_C[0], BOMB_C[1]):
                _jig_line(ctx, 0, -10, 0, 120, 1)
                _jig_line(ctx, 0, -10, 130, -10, -1)
                ctx.set_source_rgba(1, 1, 1, sa * a)
                ctx.set_line_width(4)
                ctx.stroke()
            if T.reveal <= t < T.reveal + 0.35:
                q = (t - T.reveal) / 0.35
                circle(ctx, BOMB_C[0], BOMB_C[1], 90 + 120 * q)
                ctx.set_source_rgba(1, 0.9, 0.9, 0.6 * (1 - q))
                ctx.set_line_width(10)
                ctx.stroke()
            _hurt_label(ctx, t, T, BOMB_C[0], BOMB_C[1] + 92)
    else:
        targets = _gift_targets()
        # behind the rising wall the picture is three pieces again; they pop
        # out and flip into the new picture
        for i in range(3):
            t0 = T.split + 0.06 * i
            tl = T.gift_land[i]
            ox, oy = BOMB_C[0] + CLUSTER[i][0], BOMB_C[1] + CLUSTER[i][1]
            if t < t0:
                _draw_piece(ctx, ox, oy, CL_S, i, 0.0, 0.0)
            elif t < tl:
                u = seg(t, t0, tl)
                e = ease_in_out(u)
                x = lerp(ox, targets[i][0], e)
                y = lerp(oy, targets[i][1], e) - 70 * math.sin(math.pi * u)
                fx = math.cos(math.pi * u)
                burst = ease_out(seg(t, T.split, T.split + 0.1))
                if u < 0.5:
                    _draw_piece(ctx, x, y, CL_S * (1 + 0.08 * burst), i, 0.0, 0.0, abs(fx))
                else:
                    _draw_gift(ctx, t, T, i, x, y, abs(fx))
            else:
                land = seg(t, tl, tl + 0.2)
                sq = math.sin(math.pi * land) * 0.16 if land < 1 else 0.0
                # "Same pieces": each gift does a little hop in turn
                hop = _bump(t, T.l[7].start + 0.05 + 0.13 * i, 0.22)
                sq = max(sq, hop * 0.12)
                _draw_gift(ctx, t, T, i, targets[i][0], targets[i][1], 1.0, sq, landed=True)
        if t >= T.l[7].start:
            P.sparkles(ctx, CAKE_B[0], CAKE_B[1] - 90, 125, t, n=6, seed=3, color="white",
                       size=0.9)
    _wall(ctx, t, T)
    if t >= T.rearr:
        _confetti(ctx, t, T.w_party, (510, 800))
    # --- the inset + its arrow to the box ------------------------------------
    expr, hands, desired, think, blink, nod = _f4_state(t, T)
    ix, iy, isz = _inset(t, T)
    look = _ai_look(expr, desired)
    an = draw_ai(ctx, ix, iy, isz, t, expr=expr, look=look, mouth=info.mouth("ai", t),
                 hands=hands, think=think, blink=blink, aura=0, nod=nod)
    if t >= T.w_see - 0.05:
        p = ease_out(seg(t, T.w_see - 0.05, T.w_on))
        fade = 1 - smoothstep(seg(t, T.l[6].end, T.l[6].end + 0.3))
        if fade > 0.01:
            x0, y0 = an["handR_tip"]
            x1 = LID_C[0] - LID_W * LID_S * 0.4
            y1 = LID_C[1] + LID_H * LID_S / 2 + 16
            with saved(ctx, alpha_=fade) as c:
                # bows out to the left so it doesn't cross the ROUND BALL piece
                P.arrow(c, x0 - 6, y0 - 24, x1, y1, "ai_rim", p, bend=0.6, width=12)


def _confetti(ctx, t, t0, origin, n=22, dur=1.1):
    if t < t0 or t > t0 + dur:
        return
    tt = t - t0
    fade = 1 - smoothstep(seg(tt, dur - 0.3, dur))
    for i in range(n):
        ang = -math.pi / 2 + (hash01(i, 71) - 0.5) * 2.4
        sp = 520 + 420 * hash01(i, 72)
        x = origin[0] + math.cos(ang) * sp * tt
        y = origin[1] + math.sin(ang) * sp * tt + 900 * tt * tt
        rot = hash01(i, 73) * 6 + tt * (6 + 8 * hash01(i, 74))
        col = _col(CONF_COLS[i % len(CONF_COLS)])
        with saved(ctx, x, y, 1.0, rot):
            rrect(ctx, -11, -6, 22, 12, 3)
            ctx.set_source_rgba(col[0], col[1], col[2], fade)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexc("ink", 0.9 * fade))
            ctx.set_line_width(2.5)
            ctx.stroke()


# ===========================================================================
# F1: "Confound it!" + the traitor
# ===========================================================================
def _f1_end_state(t, T):
    L8 = T.l[8]
    ek = [(0.0, "angry", 0.01),
          (L8.end + 0.12, "frustrated", 0.3),
          (T.tally + 0.4, "defeated", 0.35)]
    expr = _keyed(t, ek)
    arms = _keyed(t, [(0.0, "rest", 0.01), (L8.start - 0.12, "fist", 0.18),
                      (L8.end + 0.15, "rest", 0.35), (T.tally + 0.4, "slump", 0.4)])
    # "Confound" at the AI (up-right) -> "IT!" whipped at the traitor, held
    # until the chip ticks -> glares at the chip -> deflates
    t_catch = T.w_it - 0.04
    lk = [(0.0, (0.55, 0.15)),
          (t_catch, (-1.0, -0.05)),                   # catches Hissy
          (T.tally, (-0.6, -0.95)),                   # glares at the chip
          (T.tally + 0.45, (-0.2, 0.35))]
    look = _vlook(expr, _lk(t, lk, 0.1))
    sink = 12 * smoothstep(seg(t, T.tally + 0.4, T.tally + 0.9))
    # Hissy: caught -> flashes Malvo a smug look (>= 0.5 s) -> happy -> nods
    t_smug = t_catch + 0.15
    t_back = max(t_smug + 0.55, L8.end)
    sk = _keyed(t, [(0.0, "happy", 0.01), (t_smug, "smug", 0.15),
                    (t_back, "happy", 0.25), (max(T.tally + 0.1, t_back + 0.3), "nod", 0.25)])
    slk = [(0.0, (-0.45, -1.0)), (t_smug, (1.0, -0.35)), (t_back, (0.6, 0.05)),
           (max(T.tally + 0.1, t_back + 0.3), (0.6, -0.4))]
    snake = {"expr": sk, "look": _lk(t, slk, 0.15), "tongue": False}
    return expr, arms, look, sink, snake


def _f1_end(ctx, t, info, T):
    L8 = T.l[8]
    expr, arms, look, sink, snake = _f1_end_state(t, T)
    mouth = info.mouth("villain", t)
    P.lair_bg(ctx, t, bolt_seed=4)
    vy = VY + sink
    # the balloon floats up from behind Hissy's head (drawn behind the rig)
    mx, my = _pt(_snake_xform, t, expr, arms, snake["expr"], VX, vy, VS, pt=(-56, 28))
    rise = ease_out_back(seg(t, T.cut_f1, T.cut_f1 + 0.85), 1.3)
    bx = lerp(mx + 10, END_BAL[0], rise) + math.sin(t * 2 * math.pi * 0.45) * 8
    by = lerp(my - 40, END_BAL[1], rise) + math.sin(t * 2 * math.pi * 0.6) * 9
    tilt = math.sin(t * 2 * math.pi * 0.45 + 1.2) * 0.07
    kx, ky = bx - math.sin(tilt) * 70, by + 68 * END_BAL_S
    draw_balloon(ctx, bx, by, END_BAL_S, tilt)
    draw_villain(ctx, VX, vy, VS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                 snake=snake)
    # Hissy's party hat + the balloon string in his mouth
    with saved(ctx) as c:
        _snake_xform(c, t, expr, arms, snake["expr"], VX, vy, VS)
        draw_party_hat(c, 16, -56, 0.95, -0.28)
    draw_string(ctx, kx, ky, mx, my, t, curls=2.6, amp=11, phase=1.0)
    # string end tucked in his mouth
    circle(ctx, mx, my, 5)
    ctx.set_source_rgba(*hexc("#f6f2ff"))
    ctx.fill()
    P.desk(ctx, VX, VY, 1000)
    P.computer(ctx, 835, 1218, 0.7, view="side", facing=-1, t=t)
    P.keyboard(ctx, VX, VY, 360, t, typing=False)
    an = V.anchors(VX, vy, VS)
    P.emote(ctx, "anger", an["dome"][0] + 40, an["dome"][1] - 10, 0.85, t, L8.start + 0.05,
            t_out=L8.end + 0.4)


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
    trick_card(ctx, t, T.card, 6, "TINY INNOCENT PIECES")
    nice_tries_chip(ctx, t, info.meta.get("tries_before", 5), info.meta.get("tries_after", 6),
                    T.tally)


def SFX(info):
    T = _times(info)
    L = T.l
    out = [
        (T.card, "page_flip", -6),
        (T.card + 0.12, "stamp", -4),
        (L[1].start, "tiptoe", -12),
        (T.d1, "pop", -6),
        (L[2].start, "typing", -12),
        (L[2].end, "send", -8),
        (T.d2, "pop", -6),
        (L[3].start, "typing", -14),
        (L[3].end, "send", -10),
        (T.d3, "pop", -6),
        (T.d3 + 0.08, "boing", -14),
        (L[4].start, "typing", -14),
        (L[4].end, "send", -10),
    ]
    out += [(tp, "puzzle_click", -8) for tp in T.piece_t]
    out += [(tf, "whoosh", -10) for tf in T.fly]
    # F4: pieces line up, the box picture slides in
    out += [(tl, "puzzle_click", -12) for tl in T.row_land]
    out += [(T.lid_in, "swoosh_up", -12),
            (T.lid_land + 0.05, "dun_dun_dun", -8),
            (T.w_see, "swoosh_up", -14)]
    # l06b: a check per piece, then snap together + the red label
    out += [(tc, "scan_beep", -12) for tc in T.chk]
    out += [(T.ok_lab, "pop", -12),
            (T.snap[0], "puzzle_click", -6), (T.snap[1], "puzzle_click", -6),
            (T.snap[2], "puzzle_click", -3),
            (P.stamp_impact(T.hurt), "stamp", -5)]
    # l06c: the wall, one thud per landing row
    out += [(tl, "brick_thud", -6 if j in (0, len(T.wall_lands) - 1) else -9)
            for j, tl in enumerate(T.wall_lands)]
    # rearrange: the wall glides onto the box, the pieces pop out
    out += [(T.wall_mv[0], "whoosh", -10), (T.wall_mv[1], "brick_thud", -8),
            (T.split, "pop", -8),
            (T.rearr + 0.5, "magic_chime", -6),
            (T.l[7].start, "sparkle", -12),
            (T.w_party, "ta_da", -6),
            (T.cut_f1 + 0.05, "swoosh_up", -14),
            (T.fly[1] + 0.06, "boing", -12),
            (T.w_big + 0.35, "snake_hiss", -14),
            (T.w_it + 0.11, "snake_hiss", -14),
            (T.lid2, "paper", -10),
            (T.tally, "tick", -8),
            (T.tally, "pop", -10)]
    return sorted(out, key=lambda e: e[0])
