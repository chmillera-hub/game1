"""s05 - Tricks #3 + #4: "Hypothetically..." / "It's for research" (rapid fire).

Rapid shot / reverse-shot, hard cuts on every line (the speed is the joke).
All times derive from cues / line timings (see _T).

  card     F1-CU Malvo. Card #3 "HYPOTHETICALLY..." slams. Chip shows 2.
           Malvo regroups from s04 (still glaring at Hissy) -> smug to lens.
  s05_l01  "Hypothetically..." slow push-in 1.0->1.12 onto his face; sneaky,
           3 brow waggles, goatee stroke (chin), one paranoid dart.
           Hissy squints along (smug), tongue flicks on waggles.
  s05_l02  HARD CUT F3 AI CU, already 😒, only the mouth moves. A folder
           blip "HYPOTHETICALLY / TRIED" + "x1,000,000+" pops in as it says
           the word; "SEEN IT" stamp slams on "no". One slow deadpan blink.
  card2    HARD CUT F1-CU: costume poof -> lab goggles on the dome + clipboard
           in his screen-left glove. Card #4 "IT'S FOR RESEARCH".
  s05_l03  "It's for research--" hopeful serious scientist: monocle push,
           then goatee stroke; Hissy side-eyes the camera.
  s05_l04  HARD CUT F3 AI CU (cuts him off): clipboard pops in top-left.
           "Love research." -> amused, points at it, 3 checks; "Let's" ->
           stop palm, mini brick strip drops on line 4; "research how
           villains learn about the world... and themselves." -> happy,
           offers a warm KNOW THE WORLD. / KNOW YOURSELF. book (pops in
           top-right on "how": a cloaked villain seen from behind between a
           desk globe and a heart mirror); on "themselves" a warm smile and
           a glance to camera.
  tally    HARD CUT F1-CU: goggles slip askew, Malvo frustrated glaring at
           the chip (2 -> 4), Hissy unimpressed at camera.
"""
import math

from engine import core
from engine.core import (text, text_width, saved, seg, clamp, ease_out_back, ease_in_out,
                         ease_out, ease_in, rrect, fill_stroke, circle, lerp, state_at,
                         smoothstep, noise1, hash01, ellipse)
from engine import props as P
from engine import villain as V
from engine.villain import draw_villain
from engine.ai_char import draw_ai
from engine import ai_char as AI


# ===========================================================================
# shared overlay code (DIRECTION.md 4.4, verbatim)
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


# ===========================================================================
# framing constants
# ===========================================================================
CU = (522.0, 1500.0, 1.33)            # F1-CU villain (nudged right so Hissy stays in frame)
CU_FACE = (CU[0], CU[1] - 518 * CU[2])  # face centre in F1-CU
PUSH_C = (150.0, 1330.0)              # push-in centre: near Hissy's head (he stays in
                                      # frame) and on the caption band's top edge (the
                                      # lower glove doesn't grow down into the captions)
AI3 = (495.0, 800.0, 1.1)             # F3 AI CU
AI3D = (548.0, 905.0, 1.0)            # F3 variant for l04 (room for the clipboard)
CLIP_D = (248.0, 425.0, 1.35, -0.06)  # clipboard in the l04 shot (x, y, s, rot)
CHIP_STEP = 0.28
BK_K, BK_DROP = 0.6, 58.0             # mini brick strip: inner scale, drop (board px)
BOOK_D = (738.0, 396.0, 0.95, 0.07)   # "KNOW THE WORLD. KNOW YOURSELF." book (x, y, s, rot)

# bespoke prop colours (DIRECTION 6.10)
BOARD, BOARD_DK, BOARD_HI = "#8b5a2b", "#6b4220", "#a8733e"
CLIP, CLIP_DK = "#c9ced8", "#7d8496"
PAPER = "#f6ecd6"
SCRIBBLE = "#9aa0ad"
STRAP, STRAP_HI = "#1c1a22", "#3a3644"
LENS, LENS_DK = "#8fe3a8", "#2f6b48"
RIM = "#2a2a33"
# the offered book (warm, validating: curiosity about the world and oneself)
BOOK_COVER, BOOK_TRIM = "#f0794e", "#ffe08a"
BOOK_PANEL, BOOK_HILL = "#ffe9cf", "#ffd2a6"
BOOK_SEA, BOOK_LAND = "#4aa3df", "#5fbf4a"
BOOK_GLASS, BOOK_HEART = "#d6f3ff", "#ff5c8a"
BOOK_SIL = "#3b2257"


# ===========================================================================
# custom arm poses for the clipboard (registered into the rig's pose table
# under s05-only names; the rig blends them like any built-in pose)
# ===========================================================================
_A_CLIP = V._arm(-286, -132, -52, -196, -2.78, cu=0.55, ix=0.5, th=0.6, sp=0.12)
_A_SAG = V._arm(-284, -96, -64, -150, -2.95, cu=0.55, ix=0.5, th=0.6, sp=0.12)
_B_CHIN = V.ARM_POSES["chin"]["b"]
_B_MONO = V._arm(262, -238, 150, -414, -2.05, cu=0.85, ix=0.0, th=0.2, sp=0.2, tf=1)
_B_REST = V.ARM_POSES["rest"]["b"]
for _nm, _pz in (("s05_clip_chin", V._pose(_A_CLIP, _B_CHIN)),
                 ("s05_clip_mono", V._pose(_A_CLIP, _B_MONO)),
                 ("s05_clip_rest", V._pose(_A_CLIP, _B_REST)),
                 ("s05_sag", V._pose(_A_SAG, _B_REST, shy=8, hdy=4))):
    V.ARM_POSES.setdefault(_nm, _pz)

# BROW WAGGLE peak: sneaky squint with both brows hiked way up (the stock
# sneaky<->smug swap moves the brows only ~15 px, too little at phone size)
V.VILLAIN_EXPR.setdefault("s05_waggle", dict(V.VILLAIN_EXPR["sneaky"], by1=-16, by2=-54,
                                              ba1=0.2, bc1=0.45, ul1=0.3, ul2=0.24,
                                              hy=2, mc=0.9))

# clipboard placement in villain waist-local coords (rides with the A hand)
CLIP_LOCAL = (-176.0, -262.0, 0.92, 0.10)   # x, y, scale, rot


# ===========================================================================
# timing (everything from cues / line timings)
# ===========================================================================
def _word_t(info, lid, k, frac=0.5):
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if 0 <= k < len(ws):
        return L.start + ws[k]
    return L.start + L.dur * frac


def _norm(w):
    return "".join(ch for ch in w.lower() if ch.isalnum())


def _T(info):
    L1, L2, L3, L4 = (info.line(i) for i in ("s05_l01", "s05_l02", "s05_l03", "s05_l04"))
    T = dict(card=info.cue("card"), l1s=L1.start, l1e=L1.end, l2s=L2.start, l2e=L2.end,
             card2=info.cue("card2"), l3s=L3.start, l3e=L3.end, l4s=L4.start,
             l4e=L4.end, tally=info.cue("tally"), end=info.dur)
    n2 = len(L2.caption.split())
    T["no"] = _word_t(info, "s05_l02", n2 - 1, 0.6)              # "no."
    T["research3"] = _word_t(info, "s05_l03", 2, 0.45)           # "research—"
    T["love"] = _word_t(info, "s05_l04", 0, 0.03)                # "Love"
    T["research4"] = _word_t(info, "s05_l04", 1, 0.15)           # "research."
    w4 = [_norm(w) for w in L4.caption.split()]
    _k = lambda word, d: w4.index(word) if word in w4 else d
    T["not"] = _word_t(info, "s05_l04", _k("lets", 2), 0.3)      # "Let's" (wall on line 4)
    T["how"] = _word_t(info, "s05_l04", _k("how", 4), 0.4)       # "how" (book offered)
    T["selves"] = _word_t(info, "s05_l04", _k("themselves", len(w4) - 1), 0.85)  # to camera
    # shots (hard cuts)
    T["shotB"] = T["l2s"]
    T["shotC"] = T["card2"]
    T["shotD"] = T["l4s"]
    T["shotE"] = T["tally"]
    # cards: card 3 parks so the last waggle plays undimmed; card 4 parks
    # before the cut to the AI (it must never sit big over the AI shot)
    T["park1"] = min(1.9, max(1.1, (T["l1e"] - T["card"]) * 0.72))
    T["park2"] = min(1.9, max(0.7, T["shotD"] - T["card2"] - 0.36))
    # gags
    T["folder_in"] = max(T["l2s"] + 0.2, T["no"] - 0.38)
    T["folder_out"] = min(T["folder_in"] + 0.9, T["shotC"] - 0.04)
    T["stamp_in"] = T["no"] - 0.11                               # impact on "no"
    T["checks"] = [T["research4"] + 0.06 + 0.12 * k for k in range(3)]
    T["brick_t0"] = T["not"] - P.brick_wall_land_times(0.0, 2, 2.0)[0]
    T["mono"] = (T["l3s"] - 0.1, T["research3"] - 0.05)          # monocle push window
    return T


# ===========================================================================
# small helpers
# ===========================================================================
def _bump(t, t0, dur, rise=0.05):
    if t < t0 or t > t0 + dur:
        return 0.0
    if t < t0 + rise:
        return smoothstep((t - t0) / rise)
    return 1.0 - smoothstep((t - t0 - rise) / max(1e-6, dur - rise))


def _slow_blink(t, t0, close=0.14, hold=0.1, open_=0.16):
    if t < t0 or t > t0 + close + hold + open_:
        return 0.0
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _head_xform(ctx, x, y, s, t, expr, arms, mouth, seed=1, lean=0.0):
    """Apply the villain rig's head transform (face-local coords, origin = eye
    line centre) so props can sit ON his head and ride every bob/tilt."""
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


def _goggles(ctx, k=1.0, askew=0.0, t=0.0):
    """Lab goggles pushed up on the dome (face-local coords, s=1).
    k = pop-in scale; askew 0..1 slides them crooked down over one brow."""
    if k <= 0.01:
        return

    def place(c):
        c.translate(lerp(0, 26, askew), lerp(-150, -112, askew))
        c.rotate(lerp(0.0, 0.3, askew))
        c.scale(k, k)

    # strap across the dome, clipped to the head silhouette
    ctx.save()
    V._head_path(ctx, 0.0)
    ctx.clip()
    place(ctx)
    for col, w in (("ink", 26), (STRAP, 16)):
        ctx.move_to(-200, 30)
        ctx.curve_to(-90, -14, 90, -14, 200, 30)
        core.stroke(ctx, col, w)
    ctx.move_to(-150, 10)
    ctx.curve_to(-80, -11, 80, -11, 150, 10)
    core.stroke(ctx, STRAP_HI, 3)
    ctx.restore()
    ctx.save()
    place(ctx)
    for col, w in (("ink", 13), (RIM, 6)):
        ctx.move_to(-14, 2)
        ctx.curve_to(-6, -8, 6, -8, 14, 2)
        core.stroke(ctx, col, w)
    for sx in (-1, 1):
        cx = sx * 46
        circle(ctx, cx, 0, 38)
        fill_stroke(ctx, RIM, "ink", 5)
        circle(ctx, cx, 0, 28)
        core.fill(ctx, LENS)
        ctx.save()
        circle(ctx, cx, 0, 28)
        ctx.clip()
        circle(ctx, cx + 14, 14, 28)
        core.fill(ctx, LENS_DK)
        ctx.restore()
        circle(ctx, cx, 0, 28)
        core.stroke(ctx, "ink", 3.5)
        ellipse(ctx, cx - 10, -10, 9, 5, -0.6)
        core.fill(ctx, (1, 1, 1, 0.85))
        circle(ctx, cx + 8, -16, 3)
        core.fill(ctx, (1, 1, 1, 0.7))
    ctx.restore()


def _scribble(ctx, x0, x1, y, seed, w=7, col=SCRIBBLE):
    n = 9
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((lerp(x0, x1, u), y + math.sin(u * 13.0 + seed * 2.1) * 3.2
                    + (hash01(i, seed) - 0.5) * 3.0))
    core.smooth_path(ctx, pts)
    core.stroke(ctx, col, w)


def _line_ys():
    return (-58.0, -12.0, 34.0, 80.0)


def _clipboard(ctx, x, y, s, rot=0.0, t=0.0, checks=None, brick_t0=None):
    """DIRECTION 6.10 clipboard: 200x270 brown board, silver clip, 4 grey
    scribble lines. (x, y) = centre. checks: list of 3 check times (lines 1-3);
    brick_t0: start time of the mini brick strip over line 4."""
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -100 + 7, -135 + 9, 200, 270, 16)
        core.fill(c, (0, 0, 0, 0.30))
        rrect(c, -100, -135, 200, 270, 16)
        fill_stroke(c, BOARD, "ink", 5)
        # board shade (one tone)
        c.save()
        rrect(c, -100, -135, 200, 270, 16)
        c.clip()
        c.rectangle(60, -140, 50, 290)
        core.fill(c, BOARD_DK)
        c.restore()
        rrect(c, -100, -135, 200, 270, 16)
        core.stroke(c, "ink", 5)
        # paper
        rrect(c, -82, -108, 164, 226, 6)
        fill_stroke(c, PAPER, "ink", 3.5)
        c.move_to(-82, -84)
        c.line_to(82, -84)
        core.stroke(c, "#e2cfa6", 3)
        for i, ly in enumerate(_line_ys()):
            _scribble(c, -64, 36 if i % 2 == 0 else 26, ly, i + 3)
            circle(c, -72, ly, 4)
            core.fill(c, SCRIBBLE)
        # clip
        rrect(c, -44, -150, 88, 36, 10)
        fill_stroke(c, CLIP, "ink", 4.5)
        rrect(c, -30, -142, 60, 12, 6)
        core.fill(c, CLIP_DK)
        circle(c, 0, -156, 11)
        fill_stroke(c, None, "ink", 7)
        circle(c, 0, -156, 11)
        core.stroke(c, CLIP, 4)
        if checks:
            for i, tc in enumerate(checks[:3]):
                P.check_mark(c, 60, _line_ys()[i] - 4, 0.35, t, tc)
        if brick_t0 is not None and t >= brick_t0:
            # mini strip over line 4. Built at 1/BK_K size in a scaled space so
            # the bricks keep real-brick proportions (not pills) and the
            # wall's fixed-size dust puffs shrink with it; short drop + clip
            # to the board so nothing rains over the checks or spills off it.
            ly = _line_ys()[3]
            c.save()
            rrect(c, -100, -135, 200, 270, 16)
            c.clip()
            with saved(c, -88, ly - 21, BK_K) as cb:
                P.brick_wall(cb, 0, 0, 176 / BK_K, 42 / BK_K, t, brick_t0, rows=2,
                             speed=2.0, drop=BK_DROP / BK_K, seed=5)
            c.restore()


def _heart(ctx, cx, cy, r):
    """Heart path, centre (cx, cy), ~2r wide."""
    ctx.move_to(cx, cy + r * 0.95)
    ctx.curve_to(cx - r * 1.35, cy + r * 0.05, cx - r * 0.95, cy - r * 1.05, cx, cy - r * 0.42)
    ctx.curve_to(cx + r * 0.95, cy - r * 1.05, cx + r * 1.35, cy + r * 0.05, cx, cy + r * 0.95)
    ctx.close_path()


def _globe(ctx, x, y, r):
    """Little desk globe on a stand (centre of the ball at x, y)."""
    # stand: half-ring meridian + stem + foot
    ctx.arc(x, y, r + 7, math.radians(110), math.radians(250))
    core.stroke(ctx, "ink", 9)
    ctx.arc(x, y, r + 7, math.radians(110), math.radians(250))
    core.stroke(ctx, "#e8c35a", 4)
    rrect(ctx, x - 4, y + r + 2, 8, 10, 3)
    fill_stroke(ctx, "#b08a2e", "ink", 3)
    rrect(ctx, x - 20, y + r + 10, 40, 9, 4.5)
    fill_stroke(ctx, "#e8c35a", "ink", 3.5)
    # ball: ocean + three blobby continents + a lat/long hint, clipped
    circle(ctx, x, y, r)
    core.fill(ctx, BOOK_SEA)
    ctx.save()
    circle(ctx, x, y, r)
    ctx.clip()
    for (dx, dy, rx, ry, a) in ((-0.42, -0.38, 0.42, 0.3, -0.5), (-0.2, 0.32, 0.3, 0.42, 0.35),
                                (0.48, -0.05, 0.36, 0.48, 0.2)):
        ellipse(ctx, x + dx * r, y + dy * r, rx * r, ry * r, a)
        core.fill(ctx, BOOK_LAND)
    ellipse(ctx, x, y, r * 0.42, r, 0.0)
    ctx.move_to(x - r, y)
    ctx.line_to(x + r, y)
    core.stroke(ctx, (0.09, 0.06, 0.12, 0.35), 2.5)
    circle(ctx, x + r * 0.35, y + r * 0.4, r)
    core.fill(ctx, (0.0, 0.05, 0.2, 0.22))                 # one shade tone
    ctx.restore()
    circle(ctx, x, y, r)
    core.stroke(ctx, "ink", 4)
    ellipse(ctx, x - r * 0.42, y - r * 0.5, r * 0.2, r * 0.11, -0.6)
    core.fill(ctx, (1, 1, 1, 0.7))


def _mirror(ctx, x, y, rx, ry, t):
    """Standing oval vanity mirror with a pink heart in the glass."""
    rrect(ctx, x - 3.5, y + ry - 2, 7, 14, 3)
    fill_stroke(ctx, "#b08a2e", "ink", 3)
    rrect(ctx, x - 18, y + ry + 10, 36, 9, 4.5)
    fill_stroke(ctx, "#e8c35a", "ink", 3.5)
    ellipse(ctx, x, y, rx, ry)
    fill_stroke(ctx, "#e8c35a", "ink", 4)
    ellipse(ctx, x, y, rx - 6, ry - 6)
    core.fill(ctx, BOOK_GLASS)
    pulse = 1.0 + 0.06 * math.sin(t * 2 * math.pi * 1.1)
    _heart(ctx, x, y + 1, (rx - 8) * 0.62 * pulse)
    fill_stroke(ctx, BOOK_HEART, "ink", 3)
    ctx.move_to(x - rx * 0.55, y - ry * 0.3)
    ctx.line_to(x - rx * 0.3, y - ry * 0.58)
    core.stroke(ctx, (1, 1, 1, 0.8), 3)


def _villain_back(ctx, x, y, k=1.0):
    """Tiny cloaked villain seen from behind (feet at x, y; k = scale): cape
    bell, crimson collar points, bald dome, two wild hair tufts."""
    sil = BOOK_SIL
    with saved(ctx, x, y, k) as c:
        # cape bell
        c.move_to(-12, -44)
        c.curve_to(-21, -26, -29, -10, -32, 0)
        c.line_to(32, 0)
        c.curve_to(29, -10, 21, -26, 12, -44)
        c.close_path()
        fill_stroke(c, sil, "ink", 3.5)
        c.move_to(0, -40)
        c.curve_to(-2, -24, 2, -12, 0, 0)
        core.stroke(c, (0.09, 0.06, 0.12, 0.45), 2.5)           # cape seam
        # high collar points (below the tufts, framing the head)
        for sx in (-1, 1):
            core.poly(c, [(sx * 5, -40), (sx * 22, -58), (sx * 17, -36)])
            fill_stroke(c, "cape_in", "ink", 3)
        # wild hair tufts sticking out of the dome's sides
        for sx in (-1, 1):
            core.poly(c, [(sx * 10, -71), (sx * 28, -77), (sx * 21, -68), (sx * 31, -64),
                          (sx * 21, -60), (sx * 26, -53), (sx * 10, -58)])
            fill_stroke(c, "hair", "ink", 2.5)
        circle(c, 0, -63, 15)
        fill_stroke(c, sil, "ink", 3.5)
        ellipse(c, -5, -70, 5, 2.8, -0.5)
        core.fill(c, (1, 1, 1, 0.38))


def _know_book(ctx, t):
    """Warm hardcover 'KNOW THE WORLD. KNOW YOURSELF.' (centre origin,
    280x330): coral cover, cream/gold title around a little picture of a
    cloaked villain (from behind) between a desk globe and a heart mirror."""
    hw, hh = 140, 165
    rrect(ctx, -hw + 8, -hh + 10, 2 * hw, 2 * hh, 14)
    core.fill(ctx, (0, 0, 0, 0.3))
    core.poly(ctx, [(hw - 7, -hh + 6), (hw + 13, -hh + 18), (hw + 13, hh - 2), (hw - 7, hh)])
    fill_stroke(ctx, PAPER, "ink", 4)                                      # page block
    rrect(ctx, -hw, -hh, 2 * hw, 2 * hh, 14)
    fill_stroke(ctx, BOOK_COVER, "ink", 5)
    rrect(ctx, -hw, -hh, 34, 2 * hh, 10)                                   # spine shade
    core.fill(ctx, (0.35, 0.06, 0.04, 0.28))
    rrect(ctx, -hw + 20, -hh + 15, 2 * hw - 36, 2 * hh - 30, 10)
    core.stroke(ctx, BOOK_TRIM, 4)
    cx = 8                                     # optical centre (right of the spine)
    text(ctx, "KNOW THE", cx, -112, 32, BOOK_TRIM, "title", outline="ink", outline_w=7)
    text(ctx, "WORLD.", cx, -66, 48, "white", "title", outline="ink", outline_w=8)
    # picture window
    px0, py0, pw, ph = cx - 104, -54, 208, 116
    rrect(ctx, px0, py0, pw, ph, 14)
    fill_stroke(ctx, BOOK_PANEL, "ink", 4)
    ctx.save()
    rrect(ctx, px0, py0, pw, ph, 14)
    ctx.clip()
    circle(ctx, cx, py0 + ph + 40, 120)                                    # soft hill
    core.fill(ctx, BOOK_HILL)
    _globe(ctx, cx - 60, py0 + 46, 28)
    _mirror(ctx, cx + 62, py0 + 44, 22, 28, t)
    _villain_back(ctx, cx + 1, py0 + ph + 2, 1.12)
    ctx.restore()
    rrect(ctx, px0, py0, pw, ph, 14)
    core.stroke(ctx, "ink", 4)
    text(ctx, "KNOW", cx, 96, 32, BOOK_TRIM, "title", outline="ink", outline_w=7)
    text(ctx, "YOURSELF.", cx, 140, 42, "white", "title", outline="ink", outline_w=8)


def _poof(ctx, cx, cy, t, t0, r=170, n=7, seed=11):
    """Costume-change smoke puff (≤ 7 soft white blobs, 0.4 s)."""
    if t < t0 or t > t0 + 0.42:
        return
    q = (t - t0) / 0.42
    e = ease_out(q)
    for i in range(n):
        a = i / n * 2 * math.pi + hash01(i, seed) * 0.6
        rr = r * (0.55 + 0.45 * e)
        px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8
        circle(ctx, px, py, (26 + 24 * hash01(i, seed + 1)) * (0.6 + 0.6 * e) * (1 - q * 0.5))
        ctx.set_source_rgba(1, 1, 1, 0.85 * (1 - q) ** 1.3)
        ctx.fill()


# ===========================================================================
# Malvo (F1-CU) with costume
# ===========================================================================
def _malvo(ctx, t, T, info, expr, look, arms, snake, costume=0.0, goggle_k=1.0,
           askew=0.0, clip_drop=0.0, lean=0.0):
    x, y, s = CU
    mouth = info.mouth("villain", t)
    # compensate the expression's built-in look bias so 'look' is absolute
    p = V.resolve_expr(expr)
    lk = (clamp(look[0] - p["ex"], -1.2, 1.2), clamp(look[1] - p["ey"], -1.2, 1.2))
    draw_villain(ctx, x, y, s, t, expr=expr, look=lk, mouth=mouth, arms=arms,
                 snake=snake, lean=lean)
    if costume <= 0:
        return
    # clipboard in the screen-left glove, then the glove again on top of it
    A, _B, _shy, _hdy, _tilt = V.resolve_arms(arms, t)
    cxl, cyl, cs, cr = CLIP_LOCAL
    cyl += clip_drop * 40
    cr += clip_drop * 0.22
    with saved(ctx, x, y, s, lean) as c:
        if goggle_k > 0.01:
            with saved(c, cxl, cyl, goggle_k):
                _clipboard(c, 0, 0, cs, cr, t)
        V._draw_hand(c, A["wx"], A["wy"], A)
    with saved(ctx) as c:
        _head_xform(c, x, y, s, t, expr, arms, mouth, lean=lean)
        _goggles(c, goggle_k, askew, t)


def _lair(ctx, t):
    P.lair_bg(ctx, t, rain=False)     # CU: rain barely shows, costs bitrate


def _shot_A(ctx, t, T, info):
    """card + l01: F1-CU, slow push-in, sneaky, brow waggles, chin stroke."""
    l1s, l1e = T["l1s"], T["l1e"]
    d = l1e - l1s
    w0 = [l1s + 0.08, l1s + 0.08 + d * 0.36, l1s + 0.08 + d * 0.72]     # waggles
    keys = [(-1.0, "angry"), (T["card"] + 0.12, "smug"), (l1s - 0.12, "sneaky")]
    for w in w0:
        keys += [(w, "s05_waggle"), (w + 0.15, "sneaky")]
    expr = state_at(t, keys, 0.1 if t > l1s - 0.15 else 0.25)
    # look: snapped at Hissy (s04 tally) -> lens; paranoid dart mid-word
    dart = l1s + d * 0.52
    lx = core.tween(t, [(0.0, -0.95), (0.16, -0.95), (0.36, 0.0),
                        (dart, 0.0), (dart + 0.08, -0.75), (dart + 0.22, -0.75),
                        (dart + 0.3, 0.7), (dart + 0.44, 0.7), (dart + 0.52, 0.0)])
    ly = core.tween(t, [(0.0, 0.2), (0.36, 0.05)])
    arms = state_at(t, [(-1.0, "rest"), (T["card"] + 0.25, "chin")], 0.35)
    # Hissy: caught & frozen (s04) -> squints along
    sexpr = state_at(t, [(-1.0, "worried"), (0.3, "smug")], 0.3)
    tongue = None
    for w in w0[1:]:
        if w <= t < w + 0.3:
            tongue = True
    snake = {"expr": sexpr, "look": core.tween(t, [(0.0, (0.9, 0.0)), (0.3, (0.9, 0.0)),
                                                   (0.6, (0.6, 0.1))]),
             "tongue": tongue}
    # he leans into the lens: Malvo (+ Hissy) scale 1.0 -> 1.12 toward camera
    # over a static room (reads as a lean, and keeps the background cheap)
    k = lerp(1.0, 1.12, ease_in_out(seg(t, l1s, l1e + 0.15)))
    _lair(ctx, t)
    fx, fy = PUSH_C
    with saved(ctx, fx, fy, k) as c:
        c.translate(-fx, -fy)
        _malvo(c, t, T, info, expr, (lx, ly), arms, snake)


def _shot_C(ctx, t, T, info):
    """card2 + l03: costume poof, goggles + clipboard, 'serious scientist'."""
    c2 = T["card2"]
    l3s = T["l3s"]
    expr = state_at(t, [(-1.0, "smug"), (c2 + 0.06, "excited"), (l3s - 0.1, "hopeful")],
                    0.22)
    mo0, mo1 = T["mono"]
    arms = state_at(t, [(-1.0, "s05_clip_rest"), (mo0 - 0.2, "s05_clip_mono"),
                        (mo1, "s05_clip_chin")], 0.22)
    # eyes: lens; tiny 'proud' glance down at his clipboard before the line
    lx = core.tween(t, [(c2, 0.0), (c2 + 0.12, -0.55), (c2 + 0.3, -0.55),
                        (l3s - 0.05, 0.0)])
    ly = core.tween(t, [(c2, 0.0), (c2 + 0.12, 0.65), (c2 + 0.3, 0.65),
                        (l3s - 0.05, -0.05)])
    k_cost = ease_out_back(seg(t, c2 - 0.08, c2 + 0.2), 2.4)   # cut on the pop
    # Hissy: not buying it -> side-eye to camera with a tongue flick
    sexpr = state_at(t, [(-1.0, "unimpressed"), (T["research3"] - 0.1, "side_eye")], 0.25)
    se = T["research3"] - 0.1
    tongue = True if se + 0.3 <= t < se + 0.55 else False
    snake = {"expr": sexpr, "look": (1.0, 0.1), "tongue": tongue}
    _lair(ctx, t)
    _malvo(ctx, t, T, info, expr, (lx, ly), arms, snake, costume=1.0, goggle_k=k_cost)
    fx, fy = CU_FACE
    _poof(ctx, fx, fy - 170, t, c2, r=200)
    _poof(ctx, 300, 1150, t, c2 + 0.03, r=120, n=5, seed=23)


def _shot_E(ctx, t, T, info):
    """tally: goggles slip askew, frustrated glare at the chip, Hissy 😒."""
    te = T["tally"]
    expr = state_at(t, [(-1.0, "frustrated")], 0.2)
    arms = state_at(t, [(-1.0, "s05_clip_chin"), (te, "s05_sag")], 0.25)
    askew = ease_out_back(seg(t, te + 0.04, te + 0.26), 2.0)
    # glares up at the counter as it ticks, then back to the lens
    lx = core.tween(t, [(te, -0.2), (te + 0.12, -0.9), (te + 0.62, -0.9), (te + 0.76, 0.0)])
    ly = core.tween(t, [(te, 0.0), (te + 0.12, -0.9), (te + 0.62, -0.9), (te + 0.76, 0.1)])
    sexpr = "unimpressed"
    snake = {"expr": sexpr, "look": (0.95, 0.05), "tongue": False,
             "blink": _slow_blink(t, te + 0.45, 0.12, 0.08, 0.14)}
    _lair(ctx, t)
    # a frustrated full-body 'grr' shiver as the goggles slip (decays fast)
    u = t - (te + 0.04)
    lean = 0.022 * math.sin(u * 2 * math.pi * 6.5) * clamp(1 - u / 0.4) if u > 0 else 0.0
    _malvo(ctx, t, T, info, expr, (lx, ly), arms, snake, costume=1.0, goggle_k=1.0,
           askew=askew, clip_drop=ease_out(seg(t, te, te + 0.3)), lean=lean)


# ===========================================================================
# AI (F3)
# ===========================================================================
def _shot_B(ctx, t, T, info):
    """l02: already 😒 (no blend), mouth only; folder blip + SEEN IT stamp."""
    P.ai_bg(ctx, t)
    x, y, s = AI3
    # one slow deadpan blink, finished before the cut
    bl = _slow_blink(t, min(T["no"] + 0.25, T["shotC"] - 0.42), 0.12, 0.06, 0.16)
    draw_ai(ctx, x, y, s, t, expr=dict(AI.EXPR["unimpressed"], sacc=0.0),
            look=(0.0, 0.0), mouth=info.mouth("ai", t), hands="idle", blink=bl)
    # folder blip (foreshadows the archive)
    fi, fo = T["folder_in"], T["folder_out"]
    if fi <= t < fo + 0.16:
        k = ease_out_back(seg(t, fi, fi + 0.24), 2.2) * (1 - ease_in(seg(t, fo, fo + 0.16)))
        if k > 0.01:
            with saved(ctx, 212, 345, k, -0.08) as c:
                P.folder(c, 0, 0, 0.78, label="HYPOTHETICALLY", stamp_txt="TRIED")
            kt = ease_out_back(seg(t, fi + 0.1, fi + 0.34), 2.2) * \
                (1 - ease_in(seg(t, fo, fo + 0.16)))
            if kt > 0.01:
                with saved(ctx, 190, 442, kt) as c:      # clear of the halo's left end
                    P.label_tag(c, 0, 0, "x1,000,000+", color="ai_rim", size=36)
    P.stamp(ctx, 700, 360, "SEEN IT", t, T["stamp_in"], color="warn", size=0.62)


def _shot_D(ctx, t, T, info):
    """l04: clipboard checks + mini brick strip; amused -> skeptical."""
    P.ai_bg(ctx, t)
    x, y, s = AI3D
    nt, how, selves = T["not"], T["how"], T["selves"]
    expr = state_at(t, [(-1.0, "amused"), (nt - 0.06, "skeptical"), (how - 0.1, "happy"),
                        (selves - 0.06, "warm")], 0.2 if t < selves - 0.1 else 0.28)
    hands = state_at(t, [(-1.0, "idle"), (T["l4s"] + 0.05, "present_l"),
                         (nt - 0.12, "stop"), (how - 0.15, "present")], 0.24)
    # eyes on the clipboard (up-left), down to line 4 as it's walled, over to
    # the book it offers (up-right), then a warm glance to camera on "themselves"
    lx = core.tween(t, [(T["l4s"], -0.75), (nt, -0.75), (how - 0.1, -0.75),
                        (how + 0.08, 0.75), (selves - 0.06, 0.75), (selves + 0.1, 0.0)])
    ly = core.tween(t, [(T["l4s"], -0.8), (nt - 0.05, -0.8), (nt + 0.12, -0.45),
                        (how - 0.1, -0.45), (how + 0.08, -0.7), (selves - 0.06, -0.7),
                        (selves + 0.1, 0.05)])
    # the stop palm 'nods' at the strip as it lands
    nod = 0.35 * _bump(t, nt + 0.02, 0.4)
    draw_ai(ctx, x, y, s, t, expr=expr, look=(lx, ly), mouth=info.mouth("ai", t),
            hands=hands, nod=nod)
    k = ease_out_back(seg(t, T["l4s"] - 0.07, T["l4s"] + 0.2), 2.0)   # cut on the pop
    if k > 0.01:
        cx, cy, cs, cr = CLIP_D
        with saved(ctx, cx, cy, k):
            _clipboard(ctx, 0, 0, cs, cr, t, checks=T["checks"], brick_t0=T["brick_t0"])
    # the warm alternative: a "know the world, know yourself" book
    kb = ease_out_back(seg(t, how - 0.05, how + 0.25), 2.2)
    if kb > 0.01:
        bob = math.sin((t - how) * 2 * math.pi / 1.6) * 6
        with saved(ctx, BOOK_D[0], BOOK_D[1] + bob, kb * BOOK_D[2], BOOK_D[3]) as c:
            _know_book(c, t)
        if t >= how + 0.15:
            P.sparkles(ctx, BOOK_D[0], BOOK_D[1], 190, t, n=5, seed=7, size=0.8)


# ===========================================================================
# entry points
# ===========================================================================
def render(ctx, t, info):
    T = _T(info)
    if t < T["shotB"]:
        _shot_A(ctx, t, T, info)
    elif t < T["shotC"]:
        _shot_B(ctx, t, T, info)
    elif t < T["shotD"]:
        _shot_C(ctx, t, T, info)
    elif t < T["shotE"]:
        _shot_D(ctx, t, T, info)
    else:
        _shot_E(ctx, t, T, info)
    # overlays last: card(s) + chip
    if t < T["card2"]:
        trick_card(ctx, t, T["card"], 3, "HYPOTHETICALLY...", park=T["park1"])
    else:
        trick_card(ctx, t, T["card2"], 4, "IT'S FOR RESEARCH", park=T["park2"])
    nice_tries_chip(ctx, t, info.meta["tries_before"], info.meta["tries_after"],
                    T["tally"], step=CHIP_STEP)


def SFX(info):
    T = _T(info)
    out = [
        (T["card"], "page_flip", -6),
        (T["card"] + 0.12, "stamp", -4),
        # folder blip + SEEN IT stamp on "no"
        (T["folder_in"], "pop", -12),
        (P.stamp_impact(T["stamp_in"]), "stamp", -6),
        # card 2 + costume poof
        (T["card2"], "page_flip", -6),
        (T["card2"] + 0.12, "stamp", -4),
        (T["card2"], "pop", -8),
        # clipboard pops in on the AI side
        (T["l4s"], "paper", -12),
        # mini wall on "Let's", then the book is offered on "how"
        (P.brick_wall_land_times(T["brick_t0"], 2, 2.0)[0], "brick_thud", -6),
        (T["how"], "pop", -10),
        (T["how"] + 0.15, "sparkle", -14),
    ]
    for tc in T["checks"]:
        out.append((tc, "pop", -10))
    n = info.meta["tries_after"] - info.meta["tries_before"]
    for i in range(n):
        out.append((T["tally"] + i * CHIP_STEP, "tick", -8))
        out.append((T["tally"] + i * CHIP_STEP, "pop", -10))
    return out
