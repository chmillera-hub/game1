"""Pages of Kai's sketchbook: the illustrated beats of the No-Force what-if.

Each scene paints a full 1080x1920 frame. Strokes draw on in time with the
spoken cue words so every sentence's action appears as it is said.
"""
import math

import numpy as np
import skia

import sketchbook as sb
from gfx import clamp, hexc
from sketchbook import (BLUE, COLD, CORAL, GREEN, GREY, HOODIE, INK, LGREY, MUSTARD, NAVY, OLIVE, SKIN, TEAL, WARM,
                        arrow, cross_out, cue, eprog, hand_pos, ink, marker, pop, prog, solid, spark, underline,
                        wcircle, wellipse, wpath, write)

CX = 572  # optical centre of the page (spiral binding on the left)


def _start(c, t, tint=sb.PAGE):
    sb.page(c, tint)


def _turn(c, t):
    sb.page_turn(c, t, 0.42)


def _popped(c, x, y, sc, fn):
    """Draw fn() scaled about (x, y) by sc (for pop-in icons)."""
    if sc <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(sc, sc)
    c.translate(-x, -y)
    fn()
    c.restore()


# ============================================================ 1. the rule
def _rule_table(c, t, t_table, t_every):
    write(c, "THE RULE", CX, 272, 150, "caveat_b", prog(t, 0.3, 1.0))
    underline(c, CX - 250, CX + 250, 306, prog(t, 1.1, 0.4), 6.5)
    # "force is off the table": cuffs + a cage sit on a table, then slide off it
    tp = prog(t, 0.7, 0.9)
    ink(c, wpath([(CX - 300, 640), (CX + 300, 636)], 3, 1.6), tp, 7.5)
    ink(c, wpath([(CX - 286, 664), (CX + 286, 661)], 6, 1.2), tp, 4.5)
    ink(c, wpath([(CX - 236, 664), (CX - 248, 812)], 4, 1.0), prog(t, 1.2, 0.5), 6.5)
    ink(c, wpath([(CX + 236, 664), (CX + 248, 812)], 5, 1.0), prog(t, 1.3, 0.5), 6.5)
    slide = eprog(t, t_table - 0.05, 1.0)
    fade = 1.0 - prog(t, t_table + 0.55, 0.45)
    if fade > 0:
        for i, (x0, y0, fn, sc, dirn) in enumerate(((CX - 130, 596, sb.icon_cuffs, 1.25, -1),
                                                     (CX + 140, 568, sb.icon_cage, 1.0, 1))):
            dx = dirn * slide * 380
            dy = max(0.0, slide - 0.45) ** 2 * 1500
            ang = dirn * max(0.0, slide - 0.4) * 110
            c.save()
            c.translate(x0 + dx, y0 + dy)
            c.rotate(ang)
            sb.alpha_layer(c, fade, (-150, -150, 150, 150))
            fn(c, 0, 0, sc, prog(t, 1.0 + i * 0.35, 0.9))
            c.restore()
            c.restore()
    write(c, "force: off the table", CX, 906, 72, "caveat_b", prog(t, t_table + 0.3, 0.8), CORAL)
    # for everyone: a cop, a soldier, a citizen
    write(c, "for everyone", CX, 1022, 88, "caveat_b", prog(t, t_every - 0.1, 0.7))
    arms = ((-0.42, 0.86), (0.42, 0.86))
    sb.figure(c, CX - 285, 1345, 0.86, prog(t, t_every + 0.1, 1.2), seed=711, outfit=NAVY, hat="cap", badge=True,
              face="neutral", arms=arms, hands="open", skin=SKIN[2])
    sb.figure(c, CX, 1345, 0.86, prog(t, t_every + 0.35, 1.2), seed=722, outfit=OLIVE, hat="helmet",
              face="neutral", arms=arms, hands="open", skin=SKIN[0])
    sb.figure(c, CX + 285, 1345, 0.86, prog(t, t_every + 0.6, 1.2), seed=733, outfit=TEAL, hair="short",
              face="happy", arms=arms, hands="open", skin=SKIN[4])


def _rule_answer(c, t, t_break, t_force, t_words, t_dist, t_people):
    write(c, "if someone breaks it…", CX, 250, 88, "caveat_b", prog(t, t_break - 0.1, 0.9))
    # a shove: the rule-breaker and the person pushed
    sp = eprog(t, t_break + 0.25, 0.35)
    sb.figure(c, CX - 320, 730, 1.1, prog(t, t_break - 0.05, 0.8), seed=750, outfit=CORAL, hair="short",
              face="angry", arms=((0.62 + 0.3 * sp, -0.2), (0.75 + 0.3 * sp, -0.05)), lean=0.12 * sp, skin=SKIN[2])
    sb.figure(c, CX - 80 + 30 * sp, 730, 1.1, prog(t, t_break + 0.05, 0.8), seed=751, outfit=MUSTARD, hair="long",
              hair_col="#5a3a28", face="scared", arms=((-0.62, -0.3), (-0.25, -0.62)), lean=0.22 * sp,
              skin=SKIN[4])
    for k in range(3):
        ink(c, wpath([(CX - 186 + k * 6, 452 + k * 40), (CX - 156 + k * 6, 457 + k * 40)], 760 + k, 0.4),
            prog(t, t_break + 0.35 + k * 0.06, 0.15), 4.5, INK)
    # the answer still can't be force
    sb.icon_cuffs(c, CX + 190, 470, 1.1, prog(t, t_force - 0.45, 0.6), seed=12)
    cross_out(c, CX + 190, 470, 82, prog(t, t_force + 0.05, 0.35), 12)
    sb.icon_cage(c, CX + 372, 470, 0.95, prog(t, t_force - 0.3, 0.6), seed=22)
    cross_out(c, CX + 372, 470, 82, prog(t, t_force + 0.25, 0.35), 12)
    write(c, "still no force", CX + 282, 660, 76, "caveat_b", prog(t, t_force + 0.2, 0.7), CORAL)
    # only words, distance and the people around you
    write(c, "only:", CX, 880, 80, "caveat_b", prog(t, t_words - 0.55, 0.35))
    y = 1060
    x1, x2, x3 = CX - 315, CX, CX + 315

    def words():
        sb.icon_bubble(c, x1 - 30, y - 42, 1.35, 1.0, seed=34, color=TEAL, text="…", size=56)
        sb.icon_bubble(c, x1 + 72, y + 46, 0.95, 1.0, seed=35, color=MUSTARD, tail=1)
    _popped(c, x1, y, pop(t, t_words), words)
    write(c, "words", x1, 1268, 80, "caveat_b", prog(t, t_words + 0.15, 0.4), TEAL)

    def distance():
        sb.figure(c, x2 - 110, y + 105, 0.62, 1.0, seed=770, outfit=CORAL, hair="short", face="neutral",
                  skin=SKIN[2], arms=((-0.4, 0.9), (0.4, 0.9)))
        sb.figure(c, x2 + 110, y + 105, 0.62, 1.0, seed=771, outfit=BLUE, hair="bun", face="neutral",
                  skin=SKIN[5], hair_col="#3b2b22", arms=((-0.4, 0.9), (0.4, 0.9)))
        arrow(c, [(x2 - 46, y - 4), (x2 + 60, y - 4)], 1.0, 5.5, CORAL, 772, 18)
        arrow(c, [(x2 + 46, y + 4), (x2 - 60, y + 4)], 1.0, 5.5, CORAL, 773, 18)
    _popped(c, x2, y, pop(t, t_dist), distance)
    write(c, "distance", x2, 1268, 80, "caveat_b", prog(t, t_dist + 0.15, 0.4), CORAL)

    rp = prog(t, t_people - 0.05, 0.8)
    if rp > 0:
        cols = [TEAL, CORAL, MUSTARD, BLUE, GREEN]
        hairs = ["short", "long", "twists", "bun", "curls"]
        hcol = ["#2e2826", "#5a3a28", "#2b211e", "#3b2b22", "#2e2826"]
        for k, dx in enumerate((-96, 96, -50, 50, 0)):
            back = k < 2
            sb.figure(c, x3 + dx, y + (88 if back else 112) + (k == 4) * 8, 0.52 if back else 0.58,
                      clamp(rp * 1.8 - k * 0.18), seed=780 + k, outfit=cols[k], hair=hairs[k], face="happy",
                      skin=SKIN[(k * 2 + 1) % 6], hair_col=hcol[k])
    write(c, "people", x3, 1268, 80, "caveat_b", prog(t, t_people + 0.15, 0.4), BLUE)


def sketch_rule(c, t, dur, cues, params):
    t_table = cue(cues, "table", 2.6)
    t_every = cue(cues, "everyone", 4.56)
    t_break = cue(cues, "breaks", 6.94)
    t_force = cue(cues, "force", 9.2)
    t_words = cue(cues, "words", 11.24)
    t_dist = cue(cues, "distance", 11.8)
    t_people = cue(cues, "people", 12.73)
    sb.turn_to(c, t, t_break - 0.55,
               lambda c_: _rule_table(c_, t, t_table, t_every),
               lambda c_: _rule_answer(c_, t, t_break, t_force, t_words, t_dist, t_people))
    _turn(c, t)


# ============================================================ 2. the toolkit
def _grab_arm(c, p, alpha, seed=51):
    """A uniformed arm reaching in from the right edge to grab (to be crossed out)."""
    if p <= 0 or alpha <= 0:
        return
    sb.alpha_layer(c, alpha, (200, 260, 1080, 1000))
    ext = p
    hx, hy = 1140 - 715 * ext, 340 + 505 * ext
    ang = math.degrees(math.atan2(-505, 715))
    c.save()
    c.translate(hx, hy)
    c.rotate(ang)
    sleeve = wpath([(-18, -34), (980, -40), (980, 40), (-18, 34), (-18, -32)], seed, 1.2)
    marker(c, sleeve, 1.0, NAVY, 0.92, (4, 3), sweep=False)
    ink(c, sleeve, 1.0, 5.5)
    ink(c, wpath([(10, -36), (10, 36)], seed + 1, 0.8), 1.0, 4.0)
    palm = wpath([(-14, -30), (-70, -40), (-96, -18), (-100, 14), (-70, 34), (-14, 30), (-14, -28)], seed + 2, 1.0)
    marker(c, palm, 1.0, SKIN[3], 0.95, (3, 2), sweep=False)
    ink(c, palm, 1.0, 5.0)
    for k, (fx, fy) in enumerate(((-96, -16), (-100, 0), (-98, 14), (-88, 28))):
        ink(c, wpath([(fx, fy), (fx - 34, fy + 4), (fx - 40, fy + 22)], seed + 3 + k, 0.6), 1.0, 5.0)
    ink(c, wpath([(-40, -38), (-72, -62), (-92, -54)], seed + 9, 0.6), 1.0, 5.0)
    c.restore()
    c.restore()


def sketch_toolkit(c, t, dur, cues, params):
    _start(c, t)
    t_grab = cue(cues, "grab", 0.73)
    t_reach = cue(cues, "reach", 4.0)
    t_back = cue(cues, "back", 6.38)
    t_vio = cue(cues, "violence", 8.38)
    t_seen = cue(cues, "seen", 9.98)
    ground = 1185
    S = 1.1
    ink(c, wpath([(120, ground + 4), (1020, ground)], 31, 2.0), prog(t, 0.15, 0.6), 4, GREY)

    # witnesses: a back row of people, phones up, "STOP!"
    wp = prog(t, t_vio - 0.2, 1.3)
    if wp > 0:
        wy = 764
        ink(c, wpath([(130, wy + 3), (1010, wy)], 32, 1.5), wp, 3, LGREY)
        xs = [165, 318, 470, 690, 840, 985]
        for k, sx in enumerate(xs):
            q = clamp(wp * 1.8 - k * 0.13)
            side = 1 if sx < 560 else -1
            hand = (0.35 * side, -0.62)
            sb.figure(c, sx, wy, 0.56, q, seed=830 + k, outfit=[MUSTARD, TEAL, GREEN, CORAL, BLUE, GREY][k],
                      hair=["short", "long", "bun", "short", "curls", "twists"][k], face="shout" if k % 2 else "angry",
                      arms=((-0.45 * side, 0.8), hand), skin=SKIN[(k + 2) % 6], flip=side < 0,
                      hair_col=["#2e2826", "#5a3a28", "#3b2b22", "#2e2826", "#2e2826", "#2b211e"][k])
            if q > 0.75:
                phx, phy = hand_pos(sx, wy, 0.56, 1, hand, flip=side < 0)
                sb.icon_phone(c, phx, phy - 10, 0.62, (q - 0.75) / 0.25, seed=850 + k)
        for k, (bx, i) in enumerate(((235, 0), (545, 2), (905, 4))):
            _popped(c, bx, 548, pop(t, t_vio + 0.35 + k * 0.32),
                    lambda bx=bx, k=k: sb.icon_bubble(c, bx, 548, 0.82, 1.0, seed=860 + k, color=MUSTARD,
                                                      text="STOP!", size=46, tail=1 if bx > 560 else -1))

    # the one causing harm, bottle raised; lowers it once he is seen
    lower = eprog(t, t_seen + 0.1, 0.9)
    arm_up = (0.25 + 0.2 * lower, -0.95 + 1.8 * lower)
    ax = 255
    sb.figure(c, ax, ground, S, prog(t, 0.1, 0.9), seed=801, outfit=CORAL, hair="short",
              face="angry" if lower < 0.5 else "scared", arms=((-0.55, 0.75), arm_up), skin=SKIN[2],
              look=(0.4, 0.0) if lower < 0.5 else (-0.3, -0.8))
    hx, hy = hand_pos(ax, ground, S, 1, arm_up)
    sb.icon_bottle(c, hx, hy - 12, 0.95, prog(t, 0.45, 0.6), ang=20 - 60 * (1 - lower))

    # the person being hurt reaches back to a helper; they step away together
    away = eprog(t, t_back + 0.7, 1.3)
    reach_back = eprog(t, t_back, 0.45)
    tx = 560 + away * 100
    arm_r = (0.25 + 0.6 * reach_back, -0.62 + 0.47 * reach_back)
    sb.figure(c, tx, ground, S, prog(t, 0.25, 0.9), seed=802, outfit=BLUE, hair="long", hair_col="#4a3326",
              face="scared" if reach_back < 0.5 else ("sad" if away < 0.8 else "peace"),
              arms=((-0.62, -0.3), arm_r), lean=0.16 * (1 - away), skin=SKIN[4], step=0.4 * away)
    # the helper (Hale) comes in and offers an open hand
    enter = eprog(t, t_reach - 0.5, 0.9)
    hx2 = 1000 - 180 * enter + away * 100
    offer = eprog(t, t_reach + 0.1, 0.6)
    sb.hale(c, hx2, ground, S, prog(t, t_reach - 0.5, 0.7), face="neutral" if offer < 1 else "happy",
            arms=((-0.3 - 0.55 * offer, 0.75 - 0.85 * offer), (0.4, 0.85)), hands="open", look=(-0.6, 0.1))
    if reach_back > 0.6:
        mx, my = hand_pos(hx2, ground, S, -1, (-0.85, -0.1))
        spark(c, mx - 22, my - 8, 24, prog(t, t_back + 0.3, 0.4))

    # no grabbing
    gfade = 1.0 - prog(t, t_reach - 0.7, 0.5)
    _grab_arm(c, eprog(t, t_grab - 0.35, 0.7), gfade)
    if gfade > 0:
        sb.alpha_layer(c, gfade, (180, 180, 1080, 1060))
        cross_out(c, 395, 862, 115, prog(t, t_grab + 0.45, 0.45), 13)
        write(c, "no grabbing", CX, 330, 96, "caveat_b", prog(t, t_grab + 0.55, 0.7), CORAL)
        c.restore()

    # captions
    cfade = 1.0 - prog(t, t_seen - 0.3, 0.35)
    if cfade > 0:
        write(c, "reach for the one being hurt", CX, 300, 70, "caveat_b", prog(t, t_reach + 0.1, 1.1), alpha=cfade)
        write(c, "…if they reach back", CX + 40, 388, 66, "caveat_b", prog(t, t_back + 0.2, 0.8), TEAL,
              alpha=cfade)
    write(c, "being seen changes things", CX, 330, 76, "caveat_b", prog(t, t_seen + 0.1, 1.0))
    _turn(c, t)


# ============================================================ 3. the honest cost
def _bandage(c, x, y, s, p, seed):
    """A sticking plaster across a sketch head centred at (x, y)."""
    if p <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(-34)
    c.scale(s, s)
    strip = wpath([(-30, -9), (30, -9), (30, 9), (-30, 9), (-30, -8)], seed, 0.6)
    solid(c, strip, "#f7f1e6", p)
    ink(c, strip, p, 3.0)
    ink(c, wpath([(-6, 0), (6, 0)], seed + 1, 0.3), p, 2.5, CORAL)
    ink(c, wpath([(0, -6), (0, 6)], seed + 2, 0.3), p, 2.5, CORAL)
    c.restore()


def sketch_cost(c, t, dur, cues, params):
    _start(c, t)
    t_cost = cue(cues, "cost", 1.18)
    t_stop = cue(cues, "stopped", 4.23)
    t_vic = cue(cues, "victims", 8.12)
    t_trade = cue(cues, "trade", 11.58)
    write(c, "the honest cost", CX, 268, 116, "caveat_b", prog(t, t_cost - 0.5, 1.0))
    underline(c, CX - 285, CX + 285, 302, prog(t, t_cost + 0.4, 0.4), 6)

    # beam angle: harm force could have stopped tips it left; force's own victims level it;
    # then the bet: a slow wobble that settles a little to the right
    a = 0.0
    a -= 0.17 * eprog(t, t_stop + 0.35, 0.8)
    a += 0.17 * eprog(t, t_vic + 0.35, 0.8)
    if t > t_trade:
        u = t - t_trade
        a += 0.075 * math.sin(u * 3.3) * math.exp(-u * 0.6) + 0.045 * eprog(t, t_trade + 0.8, 1.6)
    py0 = 545
    half = 302
    SX = 556
    sp = prog(t, 0.3, 1.5)
    ink(c, wpath([(SX, py0 + 10), (SX, 1215)], 61, 1.0), sp, 9)
    ink(c, wpath([(SX - 170, 1222), (SX + 170, 1222)], 62, 1.2), sp, 9)
    solid(c, wcircle(SX, py0, 16, 63), INK, sp)
    ends = [(SX + side * half * math.cos(a), py0 + side * half * math.sin(a)) for side in (-1, 1)]
    ink(c, wpath([ends[0], ends[1]], 64, 1.4), sp, 10)
    for k, (ex, ey) in enumerate(ends):
        py = ey + 300
        sq = clamp(sp * 1.5 - 0.5)
        ink(c, wpath([(ex, ey), (ex - 104, py)], 65 + k, 0.6), sq, 4.0)
        ink(c, wpath([(ex, ey), (ex + 104, py)], 67 + k, 0.6), sq, 4.0)
        if k == 0:
            q = prog(t, t_stop - 0.1, 0.9)
            if q > 0:
                # someone hurt that force might have protected
                sb.figure(c, ex - 4, py - 2, 0.66, q, seed=880, outfit=BLUE, hair="long", hair_col="#4a3326",
                          face="pained", skin=SKIN[4], legs="floor", arms=((-0.45, 0.55), (0.5, 0.2)))
                hxp, hyp = sb.head_pos(ex - 4, py - 2, 0.66, "floor")
                _bandage(c, hxp + 9, hyp - 16, 0.6, prog(t, t_stop + 0.6, 0.3), 882)
            sb.icon_scale_pan(c, ex, py, 1.5, sq, 70 + k)
            write(c, "harm force", ex, py + 112, 62, "caveat_b", prog(t, t_stop + 0.3, 0.6))
            write(c, "could have stopped", ex, py + 168, 50, "caveat", prog(t, t_stop + 0.6, 0.7))
        else:
            q = prog(t, t_vic - 0.1, 0.9)
            if q > 0:
                # force's own victims: someone behind bars
                sb.figure(c, ex + 2, py - 2, 0.66, q, seed=890, outfit=MUSTARD, hair="twists", face="sad",
                          skin=SKIN[1], legs="floor", arms=((-0.3, 0.55), (0.3, 0.55)))
                c.save()
                c.translate(ex + 2, py - 64)
                c.scale(1.0, 0.62)
                sb.icon_cage(c, 0, 0, 0.82, prog(t, t_vic + 0.35, 0.6), seed=891)
                c.restore()
            sb.icon_scale_pan(c, ex, py, 1.5, sq, 70 + k)
            write(c, "harm force", ex, py + 112, 62, "caveat_b", prog(t, t_vic + 0.3, 0.6))
            write(c, "causes", ex, py + 168, 50, "caveat", prog(t, t_vic + 0.6, 0.6))
    write(c, "is the trade worth it?", CX, 1345, 84, "caveat_b", prog(t, t_trade + 0.2, 1.0), CORAL)
    _turn(c, t)


# ============================================================ 4. the cells open
CELL_W, CELL_H, CELL_GX, CELL_GY = 205, 215, 20, 36
BLOCK_W = 4 * CELL_W + 3 * CELL_GX
BLOCK_H = 3 * CELL_H + 2 * CELL_GY
BLOCK_X0, BLOCK_Y0 = 545 - BLOCK_W // 2, 345
_OUTFITS = [TEAL, CORAL, MUSTARD, BLUE, GREEN, HOODIE, CORAL, BLUE, MUSTARD, TEAL, GREY, GREEN]
_HAIRS = ["short", "long", "twists", "bun", "curls", "short", "long", "short", "bun", "twists", "short", "long"]
_JOY = ["happy", "peace", "happy", "neutral", "peace", "happy", "peace", "happy", "sad", "peace", "happy", "peace"]
_BLOCK_IMG = []


def _cell_block(c, t, t_open, ox, oy, p=1.0, final=False):
    """Three tiers of four cells; the bars slide open in a wave and the people inside step forward."""
    for r in range(3):
        wy = oy + r * (CELL_H + CELL_GY) + CELL_H
        for col in range(4):
            k = r * 4 + col
            x0 = ox + col * (CELL_W + CELL_GX)
            y0 = wy - CELL_H
            op = 1.0 if final else eprog(t, t_open + 0.13 * col + 0.24 * r, 0.75)
            q = clamp(p * 1.6 - k * 0.05)
            if q <= 0:
                continue
            rect = sb.wrect(x0, y0, x0 + CELL_W, wy, 1410 + k)
            solid(c, rect, "#d8d0bf", q)
            if op > 0:
                solid(c, rect, WARM, 0.8 * op)
            win = sb.wrect(x0 + 16, y0 + 16, x0 + 60, y0 + 54, 1430 + k)
            solid(c, win, WARM if op > 0.2 else "#bfb7a6", q)
            ink(c, win, q, 3.0)
            ink(c, wpath([(x0 + 31, y0 + 17), (x0 + 31, y0 + 53)], 1460 + k, 0.3), q, 2.5)
            ink(c, wpath([(x0 + 45, y0 + 17), (x0 + 45, y0 + 53)], 1480 + k, 0.3), q, 2.5)
            step = op
            happy = op > 0.55
            arms = ((-0.55, -0.7), (0.55, -0.7)) if (happy and k % 3 == 0) else ((-0.35, 0.85), (0.35, 0.85))

            def person():
                sb.figure(c, x0 + CELL_W / 2 + (k % 3 - 1) * 12, wy - 10 + 14 * step, 0.5 + 0.07 * step, q,
                          seed=1000 + k, outfit=_OUTFITS[k], hair=_HAIRS[k], face=_JOY[k] if happy else "sad",
                          skin=SKIN[(k * 5) % 6], arms=arms,
                          hair_col=["#2e2826", "#5a3a28", "#2b211e"][k % 3])
            if op < 0.5:
                person()
            # bars slide away to the right (clipped to the cell)
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(x0 + 2, y0 - 6, x0 + CELL_W - 2, wy + 6))
            dx = op * (CELL_W - 6)
            bars = skia.Path()
            for b in range(6):
                bx = x0 + 16 + b * 35 + dx
                bars.addPath(wpath([(bx, y0 + 4), (bx, wy - 4)], 1440 + k * 7 + b, 0.7))
            bars.addPath(wpath([(x0 + 8 + dx, y0 + 70), (x0 + CELL_W - 4 + dx, y0 + 70)], 1500 + k, 0.7))
            ink(c, bars, q, 6.0, "#3a3a44")
            c.restore()
            if op >= 0.5:
                person()
            ink(c, rect, q, 5.5)
        ink(c, wpath([(ox - 18, wy + 8), (ox + BLOCK_W + 18, wy + 6)], 1400 + r, 1.2), clamp(p * 1.4 - r * 0.1), 6)


def _block_image():
    if not _BLOCK_IMG:
        pad = 40
        surf = skia.Surface(BLOCK_W + 2 * pad, BLOCK_H + 2 * pad)
        cc = surf.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        _cell_block(cc, 99.0, 0.0, pad, pad, 1.0, final=True)
        _BLOCK_IMG.append((surf.makeImageSnapshot().withDefaultMipmaps(), pad))
    return _BLOCK_IMG[0]


def _sun(c, x, y, r, p, t, seed=1600):
    solid(c, wcircle(x, y, r, seed), MUSTARD, 0.95 * p)
    ink(c, wcircle(x, y, r, seed + 1), p, 4.5)
    for k in range(8):
        a = k * math.pi / 4 + t * 0.15
        ink(c, wpath([(x + math.cos(a) * (r + 14), y + math.sin(a) * (r + 14)),
                      (x + math.cos(a) * (r + 34), y + math.sin(a) * (r + 34))], seed + 2 + k, 0.4),
            clamp(p * 2 - 1), 4.5, MUSTARD)


def _cells_block_page(c, t, t_open, t_11):
    write(c, "sunrise", CX - 40, 262, 100, "caveat_b", prog(t, 0.3, 0.8))
    rise = eprog(t, 0.6, 3.0)
    _sun(c, CX + 190, 262 - 24 * rise, 40, prog(t, 0.6, 0.8), t)
    z = 1.0 - 0.8 * eprog(t, t_11 - 0.2, 1.9)
    if z > 0.999:
        _cell_block(c, t, t_open, BLOCK_X0, BLOCK_Y0, prog(t, 0.35, 1.6))
    else:
        img, pad = _block_image()
        cx, cy = BLOCK_X0 + BLOCK_W / 2, BLOCK_Y0 + BLOCK_H / 2
        px, py = (BLOCK_W + 46) * z, (BLOCK_H + 40) * z
        iw, ih = (BLOCK_W + 2 * pad) * z, (BLOCK_H + 2 * pad) * z
        view = skia.Rect.MakeLTRB(84, 318, 1012, 1092)
        c.save()
        c.clipRect(view)
        nx, ny = int(500 / px) + 1, int(420 / py) + 1
        samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        for j in range(-ny, ny + 1):
            for i in range(-nx, nx + 1):
                x = cx + i * px
                y = cy + j * py
                if x + iw / 2 < view.left() or x - iw / 2 > view.right() or y + ih / 2 < view.top() or \
                        y - ih / 2 > view.bottom():
                    continue
                c.drawImageRect(img, skia.Rect.MakeXYWH(x - iw / 2, y - ih / 2, iw, ih), samp)
        c.restore()
        ink(c, sb.wrect(84, 318, 1012, 1092, 1610), prog(t, t_11, 0.6), 4.0, GREY)
    if t > t_11:
        _popped(c, CX - 25, 1215, pop(t, t_11, 0.5),
                lambda: write(c, "11,000,000+", CX - 25, 1250, 140, "caveat_b", 1.0, CORAL))
        write(c, "people behind bars, worldwide", CX - 25, 1335, 60, "caveat_b", prog(t, t_11 + 0.5, 0.9))


def _fit(s, max_w, size, kind="caveat_b"):
    w = sb.hfont(size, kind).measureText(s)
    return size if w <= max_w else size * max_w / w


def _cells_groups(c, t, t_conv, t_sick, t_terr):
    write(c, "who walks out?", CX - 20, 250, 96, "caveat_b", prog(t, t_conv - 0.45, 0.7))
    tx = 478
    # never convicted: still waiting on a bench
    q1 = prog(t, t_conv - 0.15, 0.9)
    if q1 > 0:
        sb.icon_clock(c, 285, 372, 0.95, q1, t=t)
        ink(c, wpath([(110, 566), (450, 562)], 1620, 1.0), q1, 8, "#8a6d4a")
        ink(c, wpath([(140, 568), (134, 632)], 1621, 0.6), q1, 6)
        ink(c, wpath([(420, 566), (426, 632)], 1622, 0.6), q1, 6)
        for k in range(2):
            sb.figure(c, 168 + k * 160, 634, 0.76, q1, seed=1100 + k, outfit=[BLUE, MUSTARD][k], legs="sit",
                      hair=["short", "bun"][k], face="neutral", skin=SKIN[k * 2 + 1],
                      arms=((-0.15, 0.7), (0.35, 0.7)), hair_col="#2e2826")
    write(c, "never convicted", tx, 548, _fit("never convicted", 530, 80), "caveat_b", prog(t, t_conv, 0.7),
          align="left")
    # sick, addicted, poor
    q2 = prog(t, t_sick - 0.15, 0.9)
    if q2 > 0:
        sb.figure(c, 190, 1000, 0.8, q2, seed=1120, outfit=GREY, hair="long", hair_col="#5a3a28", face="sad",
                  skin=SKIN[2], arms=((-0.3, 0.85), (0.45, 0.6)), tilt=-0.12)
        sb.icon_pills(c, 330, 905, 1.15, prog(t, t_sick + 0.25, 0.5))
        sb.icon_coin(c, 410, 960, 1.6, prog(t, t_sick + 0.55, 0.4))
        cross_out(c, 410, 960, 36, prog(t, t_sick + 0.8, 0.3), 7)
    write(c, "sick · addicted · poor", tx, 900, _fit("sick · addicted · poor", 530, 76), "caveat_b",
          prog(t, t_sick, 1.1), align="left")
    # some did terrible things
    q3 = prog(t, t_terr - 0.2, 1.1)
    if q3 > 0:
        sb.figure(c, 270, 1345, 0.86, q3, seed=1130, outfit="#6b6e76", hair="short", face="closed", scribble=1.0,
                  skin=SKIN[5], tilt=0.2, arms=((-0.2, 0.86), (0.2, 0.86)))
    write(c, "some did", tx, 1205, 80, "caveat_b", prog(t, t_terr, 0.5), align="left")
    write(c, "terrible things", tx, 1290, 80, "caveat_b", prog(t, t_terr + 0.3, 0.8), CORAL, align="left")


def sketch_cells(c, t, dur, cues, params):
    t_open = cue(cues, "opens", 2.27)
    t_11 = cue(cues, "eleven", 4.44)
    t_conv = cue(cues, "convicted", 8.11)
    t_sick = cue(cues, "sick", 10.3)
    t_terr = cue(cues, "terrible", 14.19)
    sb.turn_to(c, t, t_conv - 0.75,
               lambda c_: _cells_block_page(c_, t, t_open, t_11),
               lambda c_: _cells_groups(c_, t, t_conv, t_sick, t_terr))
    _turn(c, t)


# ============================================================ 5. they still exist
def sketch_still(c, t, dur, cues, params):
    _start(c, t)
    t_ex = cue(cues, "exist", 0.83)
    t_ch = cue(cues, "changes", 4.04)
    t_al = cue(cues, "allowed", 5.78)
    fx, fy = CX - 20, 1190
    look = eprog(t, t_al + 0.3, 0.5)
    sb.figure(c, fx, fy, 1.45, prog(t, 0.1, 0.8), seed=1130, outfit="#6b6e76", hair="short", face="sad",
              scribble=1.0, skin=SKIN[5], tilt=0.2 * (1 - look), arms=((-0.2, 0.85), (0.2, 0.85)),
              look=(0.0, -0.9 * look))
    # the old answer: bars around him... scribbled out
    bp = prog(t, 0.2, 0.8)
    gone = prog(t, t_ch + 0.7, 0.7)
    if bp > 0 and gone < 1:
        sb.alpha_layer(c, 1 - gone, (200, 560, 900, 1240))
        for k in range(7):
            bx = fx - 270 + k * 90
            ink(c, wpath([(bx, 600), (bx, 1215)], 1200 + k, 1.2), bp, 7, GREY)
        ink(c, wpath([(fx - 300, 610), (fx + 300, 606)], 1208, 1.2), bp, 7, GREY)
        for k in range(7):
            bx = fx - 270 + k * 90
            sc = prog(t, t_ch + k * 0.07, 0.3)
            if sc > 0:
                ink(c, wpath([(bx - 34, 860), (bx + 34, 892), (bx - 32, 930), (bx + 34, 966)],
                             1210 + k, 1.0), sc, 9, CORAL)
        c.restore()
    write(c, "they still exist.", CX, 282, 108, "caveat_b", prog(t, t_ex, 1.0))
    write(c, "what changes: what everyone else can do", CX, 382, _fit("what changes: what everyone else can do",
          900, 58), "caveat_b", prog(t, t_ch, 1.4), BLUE)
    # the options, instead of bars
    _popped(c, 225, 830, pop(t, t_al), lambda: sb.icon_feet(c, 225, 830, 1.4, 1.0))
    write(c, "step back", 225, 985, 66, "caveat_b", prog(t, t_al + 0.15, 0.5), CORAL)
    _popped(c, CX - 20, 540, pop(t, t_al + 0.45),
            lambda: sb.icon_bubble(c, CX - 20, 535, 1.55, 1.0, seed=1220, text="let's talk", size=33))
    _popped(c, 885, 830, pop(t, t_al + 0.9), lambda: sb.icon_door(c, 885, 830, 1.2, 1.0, ajar=0.9))
    write(c, "a way back", 885, 1088, 66, "caveat_b", prog(t, t_al + 1.05, 0.5), "#c98a1c")
    _turn(c, t)


# ============================================================ 6. distance, not a cage
def sketch_distance(c, t, dur, cues, params):
    _start(c, t)
    t_step = cue(cues, "step", 2.95)
    t_cage = cue(cues, "cage", 5.83)
    t_bound = cue(cues, "boundary", 7.75)
    t_door = cue(cues, "door", 9.55)
    cx, fy = CX - 20, 860
    write(c, "if someone keeps hurting people…", CX, 250, _fit("if someone keeps hurting people…", 880, 64),
          "caveat_b", prog(t, 0.2, 1.4))
    write(c, "the community steps back", CX, 340, 80, "caveat_b", prog(t, t_step - 0.1, 1.0), TEAL)
    back = eprog(t, t_step, 1.4)
    rx, ry = 205 + back * 215, 112 + back * 128
    people = []
    for k in range(8):
        a = (k + 0.5) / 8 * 2 * math.pi
        people.append((fy + math.sin(a) * ry, k, cx + math.cos(a) * rx))
    bp = prog(t, t_bound - 0.1, 1.2)

    def boundary():
        if bp > 0:
            ring = wellipse(cx, fy, 282, 152, 1340, amp=1.6)
            dash = skia.Paint(AntiAlias=True, Color=hexc(BLUE), Style=skia.Paint.kStroke_Style, StrokeWidth=7)
            dash.setStrokeCap(skia.Paint.kRound_Cap)
            dash.setPathEffect(skia.DashPathEffect.Make([24.0, 18.0], 0.0))
            c.drawPath(sb.lens(ring).partial(bp), dash)
    boundary()
    dp = pop(t, t_door, 0.45)
    if dp > 0:
        _popped(c, cx + 282, fy, dp, lambda: sb.icon_door(c, cx + 282, fy - 86, 0.9, 1.0, ajar=0.85))
    centre_drawn = False
    for (py, k, px) in sorted(people):
        if not centre_drawn and py > fy:
            sb.figure(c, cx, fy, 1.0, prog(t, 0.1, 0.7), seed=1300, outfit="#6b6e76", hair="short", face="sad",
                      scribble=0.6, skin=SKIN[5], tilt=0.12)
            centre_drawn = True
        flip = px > cx
        sb.figure(c, px, py, 0.62, prog(t, 0.3 + k * 0.08, 0.8), seed=1310 + k,
                  outfit=[TEAL, CORAL, MUSTARD, BLUE, GREEN, HOODIE, TEAL, CORAL][k],
                  hair=["short", "long", "bun", "twists", "curls", "short", "long", "short"][k],
                  hair_col=["#2e2826", "#5a3a28", "#3b2b22", "#2b211e"][k % 4],
                  face="sad" if back < 0.5 else "neutral", skin=SKIN[(k * 5 + 1) % 6], flip=flip,
                  legs="walk" if 0.05 < back < 0.95 else "stand", look=(-1.0 if flip else 1.0, 0.0))
    if not centre_drawn:
        sb.figure(c, cx, fy, 1.0, prog(t, 0.1, 0.7), seed=1300, outfit="#6b6e76", hair="short", face="sad",
                  scribble=0.6, skin=SKIN[5], tilt=0.12)
    # captions
    w = write(c, "distance ≠ cage", CX - 60, 1205, 76, "caveat_b", prog(t, t_cage - 0.05, 0.8), CORAL)
    if t > t_cage:
        sb.icon_cage(c, CX - 60 + w / 2 + 70, 1180, 0.55, prog(t, t_cage + 0.35, 0.5), seed=1330)
        cross_out(c, CX - 60 + w / 2 + 70, 1180, 46, prog(t, t_cage + 0.7, 0.4), 8)
    write(c, "it's a boundary", CX, 1288, 76, "caveat_b", prog(t, t_bound, 0.8), BLUE)
    write(c, "the door stays open", CX, 1370, 76, "caveat_b", prog(t, t_door + 0.15, 1.0), "#c98a1c")
    _turn(c, t)


# ============================================================ 7. the circle
def sketch_circle(c, t, dur, cues, params):
    _start(c, t)
    t_circ = cue(cues, "circles", 0.53)
    t_sat = cue(cues, "satisfied", 4.23)
    t_rev = cue(cues, "revenge", 6.05)
    t_court = cue(cues, "court", 7.07)
    write(c, "a circle", CX - 20, 262, 104, "caveat_b", prog(t, t_circ - 0.25, 0.8))
    cx, cy, rx, ry = CX - 20, 640, 345, 172
    n = 7
    seats = []
    for k in range(n):
        a = k / n * 2 * math.pi + math.pi / 2
        seats.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    # the talking piece travels hand to hand among the people who were hurt; the one who did it listens
    order = [6, 0, 1, 2]
    pos = clamp((t - 1.3) / 6.0) * 3.0
    holder = order[min(3, int(pos + 0.5))]
    rug = wellipse(cx, cy + 40, rx - 70, ry - 50, 1405, amp=1.4)
    marker(c, rug, prog(t, 0.2, 0.9), "#e9d6b0", 0.7, (0, 0), sweep=False)
    for k in sorted(range(n), key=lambda k: seats[k][1]):
        x, y = seats[k]
        q = prog(t, 0.25 + k * 0.08, 0.8)
        flip = x > cx + 1
        bowed = k == 3
        sb.icon_chair(c, x, y, 1.05, q, seed=1400 + k, color=[MUSTARD, TEAL, CORAL, LGREY, BLUE, GREEN, MUSTARD][k])
        talking = k == holder and t > 1.2
        sb.figure(c, x + (-8 if flip else 8), y + 48, 0.62, q, seed=1410 + k, legs="sit", flip=flip,
                  outfit=[TEAL, CORAL, BLUE, "#6b6e76", MUSTARD, GREEN, HOODIE][k],
                  hair=["long", "short", "curls", "short", "bun", "twists", "long"][k],
                  hair_col=["#5a3a28", "#2e2826", "#2e2826", "#2e2826", "#3b2b22", "#2b211e", "#4a3326"][k],
                  face="sad" if bowed else ("talk" if talking else "neutral"), tilt=0.5 if bowed else 0.0,
                  scribble=0.5 if bowed else 0.0, skin=SKIN[(k * 5 + 2) % 6],
                  arms=((0.25, 0.45), (0.45, 0.4)) if talking else ((-0.2, 0.7), (0.3, 0.7)))
    if t > 1.0:
        i0 = int(min(3, math.floor(pos)))
        f = pos - i0 if i0 < 3 else 0.0
        xa, ya = seats[order[i0]]
        xb, yb = seats[order[min(3, i0 + 1)]]
        px = xa + (xb - xa) * f
        py = ya + (yb - ya) * f - 20 - math.sin(f * math.pi) * 60
        solid(c, wcircle(px, py, 15, 1430), MUSTARD, prog(t, 1.0, 0.3))
        ink(c, wcircle(px, py, 15, 1431), prog(t, 1.0, 0.3), 4)
        hx, hy = seats[holder]
        _popped(c, hx, hy - 150, pop(t, 1.3 + order.index(holder) * 2.0 - (0.0 if holder == 6 else 1.0)),
                lambda: sb.icon_bubble(c, hx + (60 if hx < cx else -60), hy - 175, 0.62, 1.0, seed=1440 + holder,
                                       text="…", size=44, tail=-1 if hx < cx else 1))
    # what the research found
    write(c, "victims report:", 150, 1002, 62, "caveat_b", prog(t, t_sat - 0.6, 0.6), align="left")
    sb.check(c, 175, 1068, 1.1, prog(t, t_sat, 0.3))
    write(c, "more satisfied", 228, 1095, 80, "caveat_b", prog(t, t_sat + 0.15, 0.8), TEAL, align="left")
    sb.check(c, 175, 1160, 1.1, prog(t, t_rev, 0.3))
    write(c, "less hungry for revenge", 228, 1187, _fit("less hungry for revenge", 770, 80), "caveat_b",
          prog(t, t_rev + 0.15, 0.9), TEAL, align="left")
    w = write(c, "…than after court", 228, 1290, 66, "caveat_b", prog(t, t_court, 0.8), align="left")
    if t > t_court:
        sb.icon_gavel(c, 228 + w + 80, 1238, 0.85, prog(t, t_court + 0.3, 0.6))
    _turn(c, t)


# ============================================================ 8. calls, care, and money
def _note(c, x, y, s=1.0, p=1.0, color=CORAL, seed=1590):
    """A hand-drawn musical note."""
    if p <= 0:
        return
    solid(c, wellipse(x, y, 13 * s, 10 * s, seed, amp=0.5), color, p)
    ink(c, wpath([(x + 11 * s, y - 2 * s), (x + 12 * s, y - 52 * s), (x + 30 * s, y - 38 * s)], seed + 1, 0.4),
        p, 5 * s, color)


def _icon_noise(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    box = sb.wrect(-50, -50, 0, 50, 1580)
    marker(c, box, 1.0, LGREY, 0.85)
    ink(c, box, 1.0, 5)
    ink(c, wcircle(-25, 15, 17, 1581), 1.0, 4)
    ink(c, wcircle(-25, -26, 8, 1582), 1.0, 3.5)
    for k in range(3):
        r = 26 + k * 20
        a = skia.Path()
        a.addArc(skia.Rect.MakeLTRB(4 - r, -r, 4 + r, r), -40, 80)
        ink(c, a, 1.0, 4.5)
    bob = math.sin(t * 6.0) * 5
    _note(c, 92, -16 + bob, 1.0, 1.0, CORAL, 1583)
    _note(c, 62, 34 - bob, 0.75, 1.0, MUSTARD, 1585)
    c.restore()


def _calls_page(c, t, t_noise, t_crash, t_bridge, t_talk, t_treat, t_stay):
    write(c, "most police calls…", CX - 20, 236, 92, "caveat_b", prog(t, 0.2, 0.9))
    # pie: only a small slice is violent
    pp = prog(t, 0.6, 1.3)
    pcx, pcy, pr = CX - 70, 470, 158
    if pp > 0:
        slice_ang = 22.0
        rest = skia.Path()
        rest.moveTo(pcx, pcy)
        rest.arcTo(skia.Rect.MakeLTRB(pcx - pr, pcy - pr, pcx + pr, pcy + pr), -90 + slice_ang,
                   (360 - slice_ang) * pp, False)
        rest.close()
        marker(c, rest, 1.0, TEAL, 0.85, (5, 4), sweep=False)
        if pp > 0.8:
            sl = skia.Path()
            sl.moveTo(pcx, pcy)
            sl.arcTo(skia.Rect.MakeLTRB(pcx - pr, pcy - pr, pcx + pr, pcy + pr), -90, slice_ang, False)
            sl.close()
            marker(c, sl, (pp - 0.8) / 0.2, CORAL, 0.9, (5, 4), sweep=False)
        ink(c, wcircle(pcx, pcy, pr, 1500), pp, 5.5)
        write(c, "not violent", pcx, pcy + 22, 56, "caveat_b", prog(t, 2.0, 0.8), "#ffffff")
        arrow(c, [(pcx + 215, pcy - 120), (pcx + 120, pcy - 150), (pcx + 52, pcy - 132)], prog(t, 1.7, 0.4), 4.5,
              CORAL, 1501, 15)
        write(c, "violent", pcx + 300, pcy - 104, 60, "caveat_b", prog(t, 1.8, 0.5), CORAL)
    cols = (245, 560, 875)
    # the calls
    _popped(c, cols[0], 760, pop(t, t_noise), lambda: _icon_noise(c, cols[0] + 4, 760, 1.25, t))
    write(c, "noise", cols[0], 905, 62, "caveat_b", prog(t, t_noise + 0.15, 0.4))
    if t > t_crash - 0.2:
        bump = eprog(t, t_crash, 0.45)
        q = prog(t, t_crash - 0.2, 0.5)
        sb.icon_car(c, cols[1] - 95 + 22 * bump, 800, 0.58, q, seed=1520, color=MUSTARD)
        sb.icon_car(c, cols[1] + 95 - 22 * bump, 800, 0.58, q, seed=1530, color=BLUE, flip=True)
        if bump > 0.95:
            spark(c, cols[1], 750, 30, prog(t, t_crash + 0.45, 0.3), CORAL)
        write(c, "car crash", cols[1], 905, 62, "caveat_b", prog(t, t_crash + 0.15, 0.5))
    bq = prog(t, t_bridge - 0.1, 0.9)
    if bq > 0:
        bx = cols[2]
        ink(c, wpath([(bx - 140, 830), (bx - 80, 762), (bx, 748), (bx + 80, 762), (bx + 140, 830)], 1540, 1.2),
            bq, 6.5)
        ink(c, wpath([(bx - 140, 752), (bx + 140, 752)], 1541, 1.0), bq, 5)
        for k in range(3):
            ink(c, wpath([(bx - 120 + k * 50, 850 + k * 6), (bx - 90 + k * 50, 850 + k * 6)], 1543 + k, 0.5), bq,
                3.5, BLUE)
        sb.figure(c, bx + 30, 760, 0.5, bq, seed=1542, outfit=BLUE, hair="long", hair_col="#4a3326", face="sad",
                  legs="sit", skin=SKIN[2], tilt=0.35, arms=((-0.1, 0.6), (0.3, 0.6)))
        write(c, "a crisis", bx, 905, 62, "caveat_b", prog(t, t_bridge + 0.15, 0.5))
    # ...go to people trained to talk, to treat, and to stay
    write(c, "here, they go to people trained to…", CX - 20, 995,
          _fit("here, they go to people trained to…", 900, 56), "caveat_b", prog(t, t_talk - 1.6, 1.2), BLUE)
    gy = 1225
    q = prog(t, t_talk - 0.1, 0.8)
    if q > 0:
        sb.figure(c, cols[0] - 30, gy, 0.66, q, seed=1550, outfit=TEAL, hair="bun", hair_col="#3b2b22", face="talk",
                  skin=SKIN[3], arms=((-0.3, 0.8), (0.75, -0.1)), hands="open")
        _popped(c, cols[0] + 70, 1060, pop(t, t_talk + 0.25),
                lambda: sb.icon_bubble(c, cols[0] + 72, 1062, 0.6, 1.0, seed=1551, text="…", size=44))
    write(c, "talk", cols[0], 1318, 72, "caveat_b", prog(t, t_talk + 0.1, 0.4), TEAL)
    q = prog(t, t_treat - 0.1, 0.8)
    if q > 0:
        sb.figure(c, cols[1] - 30, gy, 0.66, q, seed=1560, outfit="#f6f2ea", hair="short", face="neutral",
                  skin=SKIN[1], arms=((-0.3, 0.8), (0.55, 0.6)))
        hx, hy = hand_pos(cols[1] - 30, gy, 0.66, 1, (0.55, 0.6))
        sb.icon_clinic(c, hx + 34, hy + 14, 0.5, q)
    write(c, "treat", cols[1], 1318, 72, "caveat_b", prog(t, t_treat + 0.1, 0.4), CORAL)
    q = prog(t, t_stay - 0.1, 0.8)
    if q > 0:
        sb.figure(c, cols[2] - 50, gy, 0.6, q, seed=1570, outfit=MUSTARD, hair="curls", face="peace", legs="sit",
                  skin=SKIN[4], arms=((-0.2, 0.6), (0.3, 0.6)))
        sb.figure(c, cols[2] + 50, gy, 0.6, q, seed=1571, outfit=BLUE, hair="long", hair_col="#4a3326",
                  face="sad", legs="sit", skin=SKIN[2], flip=True, arms=((-0.2, 0.6), (0.2, 0.6)))
        sb.icon_heart(c, cols[2], 1035, 0.42, prog(t, t_stay + 0.4, 0.4))
    write(c, "stay", cols[2], 1318, 72, "caveat_b", prog(t, t_stay + 0.1, 0.4), "#c98a1c")


def _calls_money(c, t, t_money, t_starts):
    write(c, "the money once spent on cages…", CX - 20, 262, _fit("the money once spent on cages…", 900, 72),
          "caveat_b", prog(t, t_money - 0.1, 1.2))
    dis = eprog(t, t_money + 0.5, 1.2)
    sb.alpha_layer(c, 1.0 - 0.72 * dis, (CX - 140, 340, CX + 100, 600))
    sb.icon_cage(c, CX - 20, 470, 1.6, prog(t, t_money - 0.2, 0.5), seed=1600)
    c.restore()
    src = (CX - 20, 590)
    targets = [(225, 920, "a home"), (CX - 20, 980, "healing"), (870, 920, "second chances")]
    for k, (tx, ty, label) in enumerate(targets):
        mid = ((src[0] + tx) / 2, 720)
        arrow(c, [(src[0] + (k - 1) * 70, src[1]), mid, (tx, ty - 150)], prog(t, t_money + 0.7 + k * 0.2, 0.8),
              5, INK, 1610 + k, 20)
        for j in range(3):
            u = (t - t_money - 0.9 - j * 0.35 - k * 0.15) / 1.6
            if 0 < u < 1:
                x0 = src[0] + (k - 1) * 70
                bx = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mid[0] + u * u * tx
                by = (1 - u) ** 2 * src[1] + 2 * (1 - u) * u * mid[1] + u * u * (ty - 160)
                sb.icon_coin(c, bx, by, 1.0, 1.0, seed=1620 + j)
    sb.icon_house(c, targets[0][0], targets[0][1], 1.45, prog(t, t_money + 1.6, 0.8))
    sb.icon_clinic(c, targets[1][0], targets[1][1], 1.3, prog(t, t_money + 1.9, 0.8))
    _popped(c, targets[2][0], targets[2][1], pop(t, t_money + 2.2),
            lambda: sb.icon_heart(c, targets[2][0], targets[2][1], 1.6, 1.0))
    for k, (tx, ty, label) in enumerate(targets):
        write(c, label, tx, ty + 135, _fit(label, 300, 64), "caveat_b", prog(t, t_money + 1.8 + k * 0.3, 0.6),
              [CORAL, BLUE, TEAL][k])
    write(c, "…what stops harm", CX - 20, 1262, 84, "caveat_b", prog(t, t_starts - 0.6, 0.9), CORAL)
    write(c, "before it starts", CX - 20, 1350, 84, "caveat_b", prog(t, t_starts, 0.8), CORAL)


def sketch_calls(c, t, dur, cues, params):
    t_noise = cue(cues, "noise", 4.03)
    t_crash = cue(cues, "crashes", 5.51)
    t_bridge = cue(cues, "bridge", 8.14)
    t_talk = cue(cues, "talk", 11.78)
    t_treat = cue(cues, "treat", 12.47)
    t_stay = cue(cues, "stay", 13.3)
    t_money = cue(cues, "money", 15.19)
    t_starts = cue(cues, "starts", 18.49)
    sb.turn_to(c, t, t_money - 0.75,
               lambda c_: _calls_page(c_, t, t_noise, t_crash, t_bridge, t_talk, t_treat, t_stay),
               lambda c_: _calls_money(c_, t, t_money, t_starts))
    _turn(c, t)


# ============================================================ 9. refusal
def _refusal_street(c, t, t_ref, t_str, t_emp, t_obey):
    write(c, "refusal", CX - 20, 252, 124, "caveat_b", prog(t, t_ref - 0.15, 0.8))
    ground = 1000
    # four shops; shutters come down on "strikes"
    for k in range(4):
        x0 = 110 + k * 225
        q = prog(t, 0.2 + k * 0.12, 0.7)
        if q <= 0:
            continue
        bld = sb.wrect(x0, 470, x0 + 205, 905, 1710 + k)
        marker(c, bld, q, ["#d9c7a7", LGREY, "#e3b9a5", "#c9d3c0"][k], 0.85, (4, 3))
        ink(c, bld, q, 5)
        win = sb.wrect(x0 + 52, 505, x0 + 153, 600, 1715 + k)
        solid(c, win, "#cfe0ee", q)
        ink(c, win, q, 4)
        ink(c, wpath([(x0 + 102, 505), (x0 + 102, 600)], 1719 + k, 0.5), q, 3)
        awn = wpath([(x0 - 6, 640), (x0 + 211, 640), (x0 + 196, 690), (x0 + 9, 690), (x0 - 6, 641)], 1725 + k, 0.8)
        marker(c, awn, q, [CORAL, TEAL, MUSTARD, BLUE][k], 0.9, (3, 2))
        ink(c, awn, q, 4.5)
        door = sb.wrect(x0 + 22, 708, x0 + 183, 905, 1730 + k)
        solid(c, door, "#5b5148", 0.85 * q)
        ink(c, door, q, 4)
        down = eprog(t, t_str + k * 0.16, 0.7)
        if down > 0:
            sh_y = 708 + (905 - 708) * down
            shutter = sb.wrect(x0 + 22, 708, x0 + 183, sh_y, 1735 + k)
            solid(c, shutter, "#9c9fa6", 1.0)
            ink(c, shutter, 1.0, 4)
            stripes = skia.Path()
            for ly in np.arange(728, sh_y - 6, 24):
                stripes.addPath(wpath([(x0 + 26, ly), (x0 + 179, ly)], 1740 + k * 40 + int(ly), 0.5))
            ink(c, stripes, 1.0, 2.4, INK, 0.55)
            if down > 0.95:
                sign = sb.wrect(x0 + 28, 770, x0 + 177, 830, 1745 + k)
                q2 = prog(t, t_str + k * 0.16 + 0.6, 0.35)
                solid(c, sign, "#f7f1e6", q2)
                ink(c, sign, q2, 3.5)
                write(c, "CLOSED", x0 + 102, 812, 37, "caveat_b", q2, CORAL)
    ink(c, wpath([(80, 920), (1010, 916)], 1700, 1.6), prog(t, 0.1, 0.6), 5)
    ink(c, wpath([(80, ground + 150), (1010, ground + 146)], 1701, 1.6), prog(t, 0.2, 0.6), 4, GREY)
    for k in range(5):
        ink(c, wpath([(130 + k * 190, ground + 70), (210 + k * 190, ground + 70)], 1702 + k, 0.6),
            prog(t, 0.3, 0.6), 6, MUSTARD)
    # passers-by leave: the streets empty
    gone = eprog(t, t_emp - 0.2, 0.8)
    if gone < 1:
        for k in range(3):
            px = 260 + k * 250 + t * 22 + gone * (300 + k * 60)
            sb.figure(c, px, 915, 0.5, prog(t, 0.6 + k * 0.2, 0.7), seed=1750 + k,
                      outfit=[BLUE, MUSTARD, GREEN][k], hair=["bun", "short", "long"][k], face="neutral",
                      legs="walk", skin=SKIN[(k * 3 + 1) % 6], alpha=1 - gone,
                      hair_col=["#3b2b22", "#2e2826", "#5a3a28"][k])
    lp = prog(t, t_emp + 0.1, 2.2)
    if 0 < lp < 1:
        lx, ly = 230 + lp * 700, ground + 40 - math.sin(lp * 9) * 22 - lp * 40
        c.save()
        c.translate(lx, ly)
        c.rotate(lp * 520)
        leaf = sb.wrect(-16, -11, 16, 11, 1758)
        solid(c, leaf, "#f7f1e6", 1.0)
        ink(c, leaf, 1.0, 3)
        c.restore()
    # people sit down in the road with linked arms
    q = prog(t, t_obey - 0.5, 1.1)
    if q > 0:
        for k in range(4):
            px = 655 + k * 105
            sb.figure(c, px, ground + 112, 0.56, clamp(q * 2 - k * 0.2), seed=1760 + k, legs="floor",
                      outfit=[TEAL, CORAL, MUSTARD, BLUE][k], hair=["short", "long", "curls", "twists"][k],
                      hair_col=["#2e2826", "#5a3a28", "#2e2826", "#2b211e"][k], face="peace",
                      skin=SKIN[(k * 5 + 2) % 6], arms=((-0.6, 0.15), (0.6, 0.15)))
    # the tank rolls in... and stops: no one obeys
    move_end = min(t, t_obey)
    tank_x = -150 + min(1.0, move_end / max(1.0, t_obey)) * 480
    sb.icon_tank(c, tank_x, ground + 62, 1.15, prog(t, 0.1, 1.0), t=move_end, moving=t < t_obey)
    if t > t_obey - 0.9:
        _popped(c, tank_x + 40, ground - 90, pop(t, t_obey - 0.9),
                lambda: sb.icon_bubble(c, tank_x + 60, ground - 92, 0.82, 1.0, seed=1770, color=LGREY,
                                       text="MOVE!", size=44, tail=-1))
    if t > t_obey + 1.0:
        write(c, "?", tank_x + 150, ground - 30, 72, "caveat_b", prog(t, t_obey + 1.0, 0.3), CORAL)
    write(c, "strikes", 270, 1250, 70, "caveat_b", prog(t, t_str, 0.5), CORAL)
    write(c, "empty streets", CX - 20, 1325, 70, "caveat_b", prog(t, t_emp, 0.6), BLUE)
    write(c, "no one obeying", 800, 1250, 70, "caveat_b", prog(t, t_obey, 0.6), TEAL)


def _refusal_chart(c, t, t_study, t_twice):
    write(c, "a century of uprisings", CX - 20, 250, _fit("a century of uprisings", 880, 92), "caveat_b",
          prog(t, t_study - 0.4, 0.9))
    write(c, "1900–2006: how often they succeeded", CX - 20, 330,
          _fit("1900–2006: how often they succeeded", 860, 54), "caveat", prog(t, t_study + 0.4, 1.0), GREY)
    base = 1150
    ink(c, wpath([(150, base), (960, base)], 1780, 1.0), prog(t, t_study, 0.6), 6)
    for k, (label, val, col) in enumerate((("violent", 26, GREY), ("nonviolent", 53, TEAL))):
        bx = 340 + k * 410
        g = eprog(t, t_study + 0.6 + k * 0.7, 1.3)
        top = base - val * 12.5 * g
        if g > 0:
            bar = sb.wrect(bx - 105, top, bx + 105, base, 1790 + k)
            marker(c, bar, 1.0, col, 0.9, (6, 5), sweep=False)
            ink(c, bar, 1.0, 5)
            write(c, f"{int(round(val * g))}%", bx, top - 26, 84, "caveat_b", 1.0)
        write(c, label, bx, base + 78, 70, "caveat_b", prog(t, t_study + 0.5 + k * 0.7, 0.6),
              [INK, TEAL][k])
    tq = prog(t, t_twice - 0.15, 0.7)
    if tq > 0:
        arrow(c, [(380, 760), (470, 620), (600, 548)], tq, 6, CORAL, 1800, 22)
        write(c, "≈ 2×", 290, 680, 104, "caveat_b", prog(t, t_twice + 0.2, 0.5), CORAL)
        write(c, "(not a guarantee)", CX - 20, 1325, 60, "caveat_b", prog(t, t_twice + 1.0, 0.8), GREY)


def sketch_refusal(c, t, dur, cues, params):
    t_ref = cue(cues, "refusal", 2.1)
    t_str = cue(cues, "strikes", 4.02)
    t_emp = cue(cues, "empty", 5.17)
    t_obey = cue(cues, "obeying", 7.33)
    t_study = cue(cues, "study", 8.99)
    t_twice = cue(cues, "twice", 13.44)
    sb.turn_to(c, t, t_study - 0.55,
               lambda c_: _refusal_street(c_, t, t_ref, t_str, t_emp, t_obey),
               lambda c_: _refusal_chart(c_, t, t_study, t_twice))
    _turn(c, t)


# ============================================================ 10. the memory (Kai's own drawing)
MEM_BOX = (100, 330, 1010, 1180)
MEM_TINT = "#eef0f3"


def _hand(c, x, y, ang, s, p, seed):
    """A gripping hand: palm + four short fingers pointing along ang (degrees)."""
    if p <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    palm = wellipse(0, 0, 22, 17, seed, amp=1.2)
    solid(c, palm, SKIN[3], p)
    ink(c, palm, p, 4)
    for k in range(4):
        ink(c, wpath([(14, -12 + k * 8), (32, -14 + k * 9), (36, -4 + k * 9)], seed + 1 + k, 0.8), p, 4)
    c.restore()


def _memory_drawing(c, t, cues, shaky=2.6, full=False):
    """Kai's rough drawing of that night. With full=True everything is drawn (for the copies)."""
    t_didnt = cue(cues, "didnt", 0.56)
    t_held = cue(cues, "held", 1.86)
    t_hood = cue(cues, "hood", 3.24)
    t_metal = cue(cues, "metal", 4.74)
    P = (lambda a, d: 1.0) if full else (lambda a, d: prog(t, a, d))
    x0, y0, x1, y1 = MEM_BOX
    box = sb.wrect(x0, y0, x1, y1, 1990, amp=2.4)
    solid(c, box, "#dfe5ee", P(0.0, 0.4))
    # rain
    rp = P(0.05, 0.7)
    rain = skia.Path()
    for k in range(34):
        x = x0 + 40 + (k * 157) % (x1 - x0 - 80)
        y = y0 + 30 + (k * 263) % 360
        rain.addPath(wpath([(x, y), (x - 16, y + 44)], 2000 + k, 0.6))
    ink(c, rain, rp, 3, COLD, 0.85)
    ink(c, wpath([(x0 + 10, 1112), (x1 - 10, 1108)], 2040, shaky), P(0.1, 0.5), 5)
    # the car (front on the left): no words, no markings
    car = wpath([(130, 1050), (124, 962), (150, 905), (560, 862), (650, 722), (880, 716), (962, 852),
                 (1000, 872), (1004, 1050), (130, 1050)], 2050, shaky)
    marker(c, car, P(t_metal, 0.8), COLD, 0.92, (6, 5))
    ink(c, car, P(0.1, 0.9), 5.5)
    win = wpath([(664, 738), (868, 734), (928, 850), (646, 858), (664, 740)], 2051, shaky)
    solid(c, win, "#5d6f8f", P(0.5, 0.4))
    ink(c, win, P(0.5, 0.4), 4.5)
    ink(c, wpath([(780, 862), (782, 1040)], 2052, shaky), P(0.6, 0.3), 4)
    bar = sb.wrect(724, 694, 826, 718, 2074, amp=2.0)
    solid(c, sb.wrect(728, 698, 775, 714, 2075), "#d9534f", P(0.6, 0.4))
    solid(c, sb.wrect(775, 698, 822, 714, 2076), BLUE, P(0.6, 0.4))
    ink(c, bar, P(0.6, 0.4), 4)
    for wx in (300, 850):
        solid(c, wcircle(wx, 1052, 58, 2070 + wx, amp=2.5), "#3a3a40", P(0.3, 0.6))
        ink(c, wcircle(wx, 1052, 58, 2071 + wx, amp=2.5), P(0.3, 0.6), 5)
    # the officer: navy, faceless (scribbled out), standing over him
    op = P(t_held - 0.9, 1.0)
    if op > 0:
        legs = skia.Path()
        legs.addPath(wpath([(668, 858), (660, 1000), (652, 1110)], 2120, shaky))
        legs.addPath(wpath([(718, 858), (728, 1000), (740, 1110)], 2121, shaky))
        ink(c, legs, op, 30, "#2d3b57")
        ink(c, wpath([(632, 1114), (676, 1116)], 2128, 0.8), op, 11)
        ink(c, wpath([(724, 1114), (768, 1116)], 2129, 0.8), op, 11)
        torso = wpath([(624, 632), (760, 628), (754, 760), (740, 866), (646, 868), (632, 760), (624, 634)], 2122,
                      shaky)
        marker(c, torso, op, NAVY, 0.95, (4, 3))
        ink(c, torso, op, 5)
        solid(c, wcircle(668, 676, 7, 2123), MUSTARD, op)
        head = wcircle(692, 572, 44, 2124, amp=2.2)
        solid(c, head, SKIN[3], op)
        ink(c, head, op, 5)
        sb.hatch(c, head, op, 7, -30, 3.0, INK, 0.85, 2125)
        sb.hatch(c, head, op, 9, 40, 3.0, INK, 0.7, 2126)
        capp = wpath([(646, 556), (650, 516), (736, 514), (740, 556), (764, 562), (646, 560)], 2127, 1.6)
        solid(c, capp, NAVY, op)
        ink(c, capp, op, 4.5)
    # the boy bent over the hood, cheek on the metal, eyes shut
    bp = P(t_didnt - 0.4, 1.0)
    if bp > 0:
        legs = skia.Path()
        legs.addPath(wpath([(540, 892), (552, 1000), (560, 1114)], 2099, shaky))
        legs.addPath(wpath([(566, 888), (594, 1000), (612, 1114)], 2100, shaky))
        ink(c, legs, bp, 16, "#40506b")
        ink(c, wpath([(546, 1116), (584, 1118)], 2101, 0.8), bp, 9)
        ink(c, wpath([(600, 1116), (640, 1118)], 2102, 0.8), bp, 9)
        body = wpath([(340, 838), (452, 828), (568, 846), (582, 880), (566, 904), (452, 900), (346, 890),
                      (338, 840)], 2080, shaky)
        marker(c, body, bp, HOODIE, 0.95, (4, 3))
        ink(c, body, bp, 5)
        # arm twisted behind his back
        ink(c, wpath([(392, 850), (440, 806), (512, 842)], 2084, shaky), bp, 14, "#8a8e96")
        ink(c, wpath([(392, 850), (440, 806), (512, 842)], 2085, shaky), bp, 4)
        hx, hy, R = 296, 846, 44
        head = wcircle(hx, hy, R, 2081, amp=2.0)
        solid(c, head, SKIN[1], bp)
        ink(c, head, bp, 5)
        # twists on the top of his head (pointing left: his head lies sideways)
        tw = skia.Path()
        for k in range(7):
            a = math.radians(105 + k * 25)
            tw.addPath(wpath([(hx + math.cos(a) * (R - 3), hy + math.sin(a) * (R - 3)),
                              (hx + math.cos(a) * (R + 17), hy + math.sin(a) * (R + 17))], 2090 + k, 0.8))
        ink(c, tw, bp, 8, "#2b211e")
        if bp > 0.8:
            # squeezed-shut eyes, tight mouth
            ink(c, wpath([(278, 828), (288, 834), (298, 828)], 2097, 0.5), 1.0, 4)
            ink(c, wpath([(282, 858), (292, 864), (302, 858)], 2096, 0.5), 1.0, 4)
            ink(c, wpath([(318, 836), (322, 852)], 2095, 0.5), 1.0, 4)
    # her hands: one on the back of his head and neck, one gripping his wrists
    hp = P(t_held, 0.8)
    if hp > 0:
        arm1 = wpath([(640, 656), (548, 740), (372, 812)], 2110, shaky)
        arm2 = wpath([(728, 664), (626, 780), (526, 836)], 2111, shaky)
        for arm in (arm2, arm1):
            ink(c, arm, hp, 30, NAVY)
            ink(c, arm, hp, 4.5)
        _hand(c, 356, 818, 165, 1.0, clamp(hp * 3 - 2), 2112)
        _hand(c, 512, 842, 160, 0.95, clamp(hp * 3 - 2), 2117)
    # "against the hood": the hood line pressed over and over
    for k in range(3):
        ink(c, wpath([(152, 908 + k * 3), (558, 866 + k * 3)], 2060 + k, shaky * 1.3), P(t_hood + k * 0.18, 0.45),
            7.5 - k * 2)
    if not full and t > t_hood + 0.2:
        q = prog(t, t_hood + 0.2, 0.3)
        for k in range(3):
            a = math.radians(200 + k * 35)
            ink(c, wpath([(296 + math.cos(a) * 66, 846 + math.sin(a) * 66),
                          (296 + math.cos(a) * 88, 846 + math.sin(a) * 88)], 2130 + k, 0.4), q, 4)
    ink(c, box, P(0.0, 0.6), 5)


def sketch_memory(c, t, dur, cues, params):
    t_cold = cue(cues, "cold", 5.48)
    shiver = prog(t, t_cold, 0.2) * (1.0 - 0.6 * prog(t, t_cold + 0.6, 0.8))
    _start(c, t, MEM_TINT)
    c.save()
    if shiver > 0:
        c.translate(math.sin(t * 47.0) * 2.4 * shiver, math.cos(t * 39.0) * 1.6 * shiver)
    write(c, "4th st. — 3 yrs ago", 340, 262, 62, "caveat_b", prog(t, 0.15, 0.9), "#7d8696", rot=-3)
    _memory_drawing(c, t, cues)
    write(c, "so cold.", 560, 1300, 84, "caveat_b", prog(t, cue(cues, "metal", 4.74) + 0.35, 0.8), "#5b7fb3",
          rot=-2)
    fq = prog(t, t_cold, 0.6)
    if fq > 0:
        ink(c, wpath([(262, 872), (258, 900)], 2199, 0.4), fq, 4, BLUE)
        frost = skia.Path()
        for k, (fx, fy) in enumerate(((236, 800), (226, 900), (360, 920), (300, 770), (430, 925))):
            for j in range(3):
                a = j * math.pi / 3
                frost.addPath(wpath([(fx - math.cos(a) * 13, fy - math.sin(a) * 13),
                                     (fx + math.cos(a) * 13, fy + math.sin(a) * 13)], 2200 + k * 3 + j, 0.3))
        ink(c, frost, fq, 3.5, BLUE)
    c.restore()
    _turn(c, t)


# ============================================================ 11. old world / this world
def _panel(c, x0, y0, x1, y1, p, seed, fill=None):
    if fill and p > 0:
        solid(c, sb.wrect(x0, y0, x1, y1, seed, amp=1.8), fill, 0.6 * p)
    ink(c, sb.wrect(x0, y0, x1, y1, seed, amp=1.8), p, 5)


def _wide_bubble(c, x, y, w, h, p, color, text, size, tail=-1, seed=2350):
    if p <= 0:
        return
    body = wellipse(x, y, w / 2, h / 2, seed, amp=1.6)
    marker(c, body, clamp(p * 1.5 - 0.3), color, 0.85, (5, 4))
    ink(c, body, clamp(p * 1.5), 5)
    ink(c, wpath([(x + tail * w * 0.22, y + h * 0.42), (x + tail * w * 0.34, y + h * 0.85),
                  (x + tail * w * 0.06, y + h * 0.48)], seed + 1, 1.0), clamp(p * 2 - 0.8), 5)
    write(c, text, x, y + size * 0.33, size, "caveat_b", clamp(p * 2 - 1))


def _rock(c, x, y, s, p, seed=2360):
    rock = wpath([(-70, 20), (-62, -30), (-20, -58), (36, -52), (72, -14), (66, 30), (20, 50), (-40, 48), (-70, 22)],
                 seed, 2.0)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    marker(c, rock, p, "#5b5d66", 0.95, (4, 3))
    sb.hatch(c, rock, p, 9, -35, 3, INK, 0.7, seed + 1)
    ink(c, rock, p, 5.5)
    c.restore()


def sketch_oldworld(c, t, dur, cues, params):
    _start(c, t)
    t_ends = cue(cues, "ends", 1.98)
    t_drive = cue(cues, "drives", 3.87)
    t_carry = cue(cues, "carries", 5.9)
    t_call = cue(cues, "call", 8.74)
    t_listen = cue(cues, "listen", 11.21)
    dim = 1.0 - 0.35 * prog(t, t_call - 0.8, 0.8)
    sb.alpha_layer(c, dim, (80, 150, 1040, 810))
    write(c, "the old world", CX - 20, 240, 86, "caveat_b", prog(t, 0.2, 0.8), GREY)
    _panel(c, 110, 280, 545, 700, prog(t, 0.4, 0.7), 2300, "#e6e1d6")
    _panel(c, 575, 280, 1010, 700, prog(t, 0.6, 0.7), 2301, "#e6e1d6")
    # she drives home
    dq = prog(t, t_drive - 0.25, 0.6)
    if dq > 0:
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(114, 284, 541, 696))
        u = eprog(t, t_drive - 0.2, 3.2)
        cx_ = 420 - u * 175
        sb.icon_house(c, 185, 595, 0.95, dq, color=LGREY)
        ink(c, wpath([(114, 660), (541, 656)], 2319, 1.0), dq, 4, GREY)
        sb.icon_car(c, cx_, 640, 0.82, dq, seed=2310, color=GREY, lightbar=True, flip=True)
        for k in range(3):
            ink(c, wpath([(cx_ + 110 + k * 8, 565 + k * 26), (cx_ + 170 + k * 8, 565 + k * 26)], 2320 + k, 0.5),
                dq, 3.5, GREY)
        c.restore()
    write(c, "she drives home", 327, 350, 56, "caveat_b", prog(t, t_drive, 0.6))
    # he carries it
    cq = prog(t, t_carry - 0.25, 0.8)
    if cq > 0:
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(579, 284, 1006, 696))
        walk = eprog(t, t_carry - 0.2, 5.0)
        bx = 760 + walk * 80
        ink(c, wpath([(579, 662), (1006, 658)], 2329, 1.0), cq, 4, GREY)
        sb.figure(c, bx, 662, 0.92, cq, seed=2330, outfit="#8d9097", hair="twists", hair_col="#2b211e", face="sad",
                  skin=SKIN[1], legs="walk", lean=0.38, tilt=0.3, arms=((-0.8, -0.55), (-0.5, -0.8)))
        _rock(c, bx - 58, 428, 1.05, prog(t, t_carry + 0.1, 0.6))
        c.restore()
    write(c, "he carries it", 792, 350, 56, "caveat_b", prog(t, t_carry, 0.6))
    write(c, "…and that's where it ends.", CX - 20, 772, _fit("…and that's where it ends.", 880, 64), "caveat_b",
          prog(t, t_ends - 0.2, 1.1), GREY)
    c.restore()
    # this world: he can call it out, and she can listen
    write(c, "this world", CX - 20, 880, 94, "caveat_b", prog(t, t_call - 1.1, 0.6), TEAL)
    _panel(c, 110, 920, 1010, 1350, prog(t, t_call - 0.9, 0.7), 2340, "#f6efe0")
    kq = prog(t, t_call - 0.7, 0.8)
    if kq > 0:
        talk = (t > t_call) and (int((t - t_call) * 7) % 2 == 0) and t < t_call + 1.6
        sb.kai(c, 300, 1325, 0.98, kq, face="talk" if talk else "neutral", arms=((-0.45, 0.75), (0.75, -0.15)),
               hands="open", look=(1.0, 0.0))
        _wide_bubble(c, 455, 985, 330, 102, pop(t, t_call), CORAL, "that was wrong.", 50, tail=-1)
    lq = prog(t, t_call - 0.4, 0.8)
    if lq > 0:
        lis = eprog(t, t_listen, 0.7)
        sb.hale(c, 790, 1325, 0.98, lq, face="sad" if lis < 0.5 else "closed", tilt=-0.22 * lis,
                arms=((-0.2, 0.8), (-0.5 * lis + 0.2 * (1 - lis), -0.45 * lis + 0.8 * (1 - lis))),
                look=(-1.0, 0.0), flip=True)
        if lis > 0:
            for k in range(3):
                a0 = skia.Path()
                r = 34 + k * 20
                a0.addArc(skia.Rect.MakeLTRB(700 - r, 1080 - r, 700 + r, 1080 + r), 150, 60)
                ink(c, a0, clamp(lis * 3 - k), 4.5, TEAL)
        write(c, "listening", 830, 1000, 66, "caveat_b", prog(t, t_listen + 0.2, 0.7), TEAL)
    _turn(c, t)


# ============================================================ 12. a hundred times, smaller
_MEM_PIC = []


def _memory_picture():
    if not _MEM_PIC:
        rec = skia.PictureRecorder()
        cc = rec.beginRecording(skia.Rect.MakeWH(1080, 1920))
        _memory_drawing(cc, 10.0, {}, full=True)
        _MEM_PIC.append(rec.finishRecordingAsPicture())
    return _MEM_PIC[0]


def _small_copy(c, k):
    """Page k of the hundred: the same night, drawn smaller each time."""
    s = 0.8 ** k
    mx, my = (MEM_BOX[0] + MEM_BOX[2]) / 2, (MEM_BOX[1] + MEM_BOX[3]) / 2
    c.save()
    c.translate(mx, my + (1 - s) * 60)
    c.scale(s, s)
    c.translate(-mx, -my)
    c.drawPicture(_memory_picture())
    c.restore()


def _tally(c, t, t_hund, t_small):
    tq = prog(t, t_hund - 0.1, 1.7)
    if tq <= 0:
        return
    n = int(tq * 100)
    marks = skia.Path()
    slashes = skia.Path()
    for i in range(n):
        g, j = divmod(i, 5)
        gx = 140 + (g % 10) * 86
        gy = 1238 + (g // 10) * 84
        if j < 4:
            marks.addPath(wpath([(gx + j * 13, gy), (gx + j * 13 + 3, gy + 50)], 2400 + i, 0.5))
        else:
            slashes.addPath(wpath([(gx - 8, gy + 42), (gx + 52, gy + 8)], 2400 + i, 0.5))
    ink(c, marks, 1.0, 3.5, INK, 0.8)
    ink(c, slashes, 1.0, 3.5, CORAL, 0.9)


def sketch_smaller(c, t, dur, cues, params):
    t_hund = cue(cues, "hundred", 1.27)
    t_small = cue(cues, "smaller", 3.09)
    flips = 9
    period = max(0.2, (t_small - 0.1) / flips)
    k = int(clamp((t - 0.05) / period, 0, flips))
    tk = 0.05 + k * period
    if k >= 1:
        sb.turn_to(c, t, tk, lambda c_: _small_copy(c_, k - 1), lambda c_: _small_copy(c_, k), 0.2, MEM_TINT,
                   MEM_TINT)
    else:
        sb.page(c, MEM_TINT)
        _small_copy(c, 0)
    _tally(c, t, t_hund, t_small)
    write(c, "a hundred times", 560, 262, 80, "caveat_b", prog(t, t_hund - 0.1, 0.9), "#7d8696", rot=-2)
    write(c, "smaller…", CX - 20, 1120, 92, "caveat_b", prog(t, t_small, 0.9), "#5b7fb3")
    if k == 0:
        _turn(c, t)


# ============================================================ 13. the final page
def _booth_sunrise(c, t, t_tried):
    """Hale and Kai in the booth at sunrise -- steadier lines this time."""
    wq = prog(t, 0.3, 1.1)
    x0, y0, x1, y1 = 130, 380, 950, 800
    win = sb.wrect(x0, y0, x1, y1, 2500, amp=0.7)
    sun_q = prog(t, 0.9, 1.4)
    if sun_q > 0:
        c.save()
        c.clipPath(win, skia.ClipOp.kIntersect, True)
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                                   [hexc("#ffe7b3", sun_q), hexc("#f4ad86", sun_q)]))
        c.drawRect(skia.Rect.MakeLTRB(x0 - 10, y0 - 10, x1 + 10, y1 + 10), g)
        rise = eprog(t, 0.9, 14.0)
        sx, sy = (x0 + x1) / 2, y1 - 30 - 170 * rise
        solid(c, wcircle(sx, sy, 105, 2501, amp=0.6), MUSTARD, sun_q)
        for k in range(10):
            a = k * math.pi / 5 + t * 0.12
            ink(c, wpath([(sx + math.cos(a) * 125, sy + math.sin(a) * 125),
                          (sx + math.cos(a) * 160, sy + math.sin(a) * 160)], 2503 + k, 0.4), sun_q, 5, "#f6c35a")
        ink(c, wpath([(x0, y1 - 40), (x0 + 180, y1 - 70), (x0 + 330, y1 - 52), (x0 + 520, y1 - 84),
                      (x0 + 700, y1 - 60), (x1, y1 - 76)], 2515, 1.0), sun_q, 4, "#c98a6a")
        c.restore()
    ink(c, win, wq, 6)
    ink(c, wpath([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], 2502, 0.4), wq, 5)
    # booth backs
    bq = prog(t, 1.4, 1.2)
    for k, (bx0, bx1) in enumerate(((95, 380), (700, 985))):
        back = sb.wrect(bx0, 690, bx1, 1010, 2510 + k, amp=0.7)
        marker(c, back, bq, CORAL, 0.88)
        ink(c, back, bq, 5.5)
    # Hale (left) and Kai (right) facing each other
    sb.hale(c, 330, 1040, 1.12, prog(t, 2.2, 1.5), face="happy", legs="sit", arms=((-0.2, 0.6), (0.78, 0.42)),
            look=(1.0, 0.0), seed=2520)
    sb.kai(c, 750, 1040, 1.12, prog(t, 2.9, 1.5), face="happy", legs="sit", flip=True,
           arms=((-0.2, 0.6), (0.78, 0.42)), look=(1.0, 0.0), seed=2530)
    tq = prog(t, 3.8, 0.9)
    table = sb.wrect(215, 905, 865, 948, 2540, amp=0.7)
    marker(c, table, tq, "#e9e1cf", 1.0, (0, 0), sweep=False)
    ink(c, table, tq, 5.5)
    ink(c, wpath([(540, 948), (540, 1080)], 2541, 0.5), tq, 7)
    st = 1.0 if t > 5.0 else 0.0
    sb.icon_mug(c, 455, 866, 0.95, prog(t, 4.4, 0.6), seed=2550, steam=st, t=t)
    sb.icon_mug(c, 640, 866, 0.95, prog(t, 4.7, 0.6), seed=2560, color="#f6f2ea", steam=st, t=t + 0.4)


def _final_question(c, t, t_work, t_tried, t_forced, t_earn):
    write(c, "would it work?", CX - 20, 252, 112, "caveat_b", prog(t, t_work - 0.25, 0.9))
    write(c, "(no society this big has ever tried)", CX - 20, 332,
          _fit("(no society this big has ever tried)", 860, 54), "caveat_b", prog(t, t_tried - 0.3, 1.2), GREY)
    _booth_sunrise(c, t, t_tried)
    write(c, "if no one can be forced,", CX - 20, 1135, 66, "caveat_b", prog(t, t_forced - 0.4, 1.0))
    write(c, "the only power left is", CX - 20, 1215, 66, "caveat_b", prog(t, t_forced + 0.9, 1.0))
    write(c, "the kind you earn.", CX - 20, 1330, 100, "caveat_b", prog(t, t_earn - 0.5, 0.9), CORAL)
    if t > t_earn + 0.4:
        underline(c, CX - 330, CX + 290, 1356, prog(t, t_earn + 0.4, 0.4), 6, CORAL)


def _final_powers(c, t, t_prot, t_pers, t_care, t_end):
    write(c, "the power to…", CX - 20, 250, 96, "caveat_b", prog(t, t_prot - 0.5, 0.6))
    # protect: standing in the way, arms open, someone small behind
    q = prog(t, t_prot - 0.15, 0.9)
    if q > 0:
        sb.figure(c, 400, 640, 0.6, q, seed=2575, outfit=MUSTARD, hair="bun", hair_col="#3b2b22", face="neutral",
                  skin=SKIN[4], arms=((-0.4, 0.6), (0.3, 0.75)))
        sb.hale(c, 290, 645, 1.02, q, face="neutral", arms=((-0.95, -0.15), (0.95, -0.15)), hands="open",
                look=(-1.0, 0.0), seed=2570)
        for k in range(3):
            ink(c, wpath([(150 - k * 6, 440 + k * 40), (110 - k * 6, 452 + k * 40)], 2577 + k, 0.4),
                prog(t, t_prot + 0.4 + k * 0.06, 0.2), 5, CORAL)
    write(c, "protect", 770, 520, 108, "caveat_b", prog(t, t_prot, 0.6), NAVY)
    # persuade: an idea passed across
    q = prog(t, t_pers - 0.15, 0.9)
    if q > 0:
        sb.figure(c, 640, 965, 0.82, q, seed=2580, outfit=TEAL, hair="short", face="talk", skin=SKIN[0],
                  arms=((-0.4, 0.8), (0.75, -0.1)), hands="open", look=(1.0, 0.0))
        sb.figure(c, 900, 965, 0.82, q, seed=2581, outfit=CORAL, hair="long", hair_col="#5a3a28",
                  face="happy" if t > t_pers + 0.9 else "neutral", skin=SKIN[5], flip=True,
                  arms=((-0.3, 0.8), (0.4, 0.8)), look=(1.0, 0.0))
        _popped(c, 720, 700, pop(t, t_pers + 0.15),
                lambda: sb.icon_bubble(c, 720, 700, 0.95, 1.0, seed=2582, color=TEAL, text="what if…", size=34))
        _popped(c, 985, 668, pop(t, t_pers + 0.85),
                lambda: sb.icon_bubble(c, 985, 668, 0.62, 1.0, seed=2583, color=MUSTARD, text="oh!", size=48,
                                       tail=-1))
    write(c, "persuade", 290, 860, 108, "caveat_b", prog(t, t_pers, 0.6), TEAL)
    # care: the fist bump
    q = prog(t, t_care - 0.15, 0.7)
    if q > 0:
        bump = eprog(t, t_care + 0.05, 0.5)
        for side, col, sleeve in ((-1, SKIN[3], NAVY), (1, SKIN[1], HOODIE)):
            fx = 330 + side * (115 - 70 * bump)
            fy = 1195
            arm = wpath([(fx + side * 30, fy), (fx + side * 150, fy + 40), (fx + side * 250, fy + 90)], 2595 + side,
                        0.8)
            ink(c, arm, q, 46, sleeve)
            ink(c, arm, q, 5)
            fist = wellipse(fx, fy, 44, 38, 2590 + side, amp=1.0)
            solid(c, fist, col, q)
            ink(c, fist, q, 5)
            for j in range(3):
                ink(c, wpath([(fx - side * 30, fy - 18 + j * 15), (fx - side * 12, fy - 18 + j * 15)],
                             2600 + j + side * 5, 0.4), q, 3.5)
        if bump > 0.9:
            spark(c, 330, 1135, 34, prog(t, t_care + 0.5, 0.3))
    write(c, "care", 770, 1215, 120, "caveat_b", prog(t, t_care, 0.6), CORAL)
    if t > t_care + 0.6:
        sb.icon_heart(c, 905, 1150, 0.55, prog(t, t_care + 0.6, 0.5))
    write(c, "— Kai", 860, 1372, 64, "caveat_b", prog(t, t_end + 0.5, 0.8), GREY, rot=-4)


def sketch_final(c, t, dur, cues, params):
    t_work = cue(cues, "work", 1.04)
    t_tried = cue(cues, "tried", 4.43)
    t_forced = cue(cues, "forced", 7.2)
    t_earn = cue(cues, "earn", 10.2)
    t_prot = cue(cues, "protect", 12.59)
    t_pers = cue(cues, "persuade", 14.56)
    t_care = cue(cues, "care", 16.7)
    t_end = cue(cues, "end", 17.61)
    sb.turn_to(c, t, t_prot - 0.7,
               lambda c_: _final_question(c_, t, t_work, t_tried, t_forced, t_earn),
               lambda c_: _final_powers(c_, t, t_prot, t_pers, t_care, t_end))
    _turn(c, t)


SCENES = {

    "sketch_rule": sketch_rule,
    "sketch_toolkit": sketch_toolkit,
    "sketch_cost": sketch_cost,
    "sketch_cells": sketch_cells,
    "sketch_still": sketch_still,
    "sketch_distance": sketch_distance,
    "sketch_circle": sketch_circle,
    "sketch_calls": sketch_calls,
    "sketch_refusal": sketch_refusal,
    "sketch_memory": sketch_memory,
    "sketch_oldworld": sketch_oldworld,
    "sketch_smaller": sketch_smaller,
    "sketch_final": sketch_final,
}
