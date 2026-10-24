"""Illustrated cutaways: what each sentence describes, shown on screen."""
import math
import random
import cairo
from chars import rgb, src
from scenes import lin, rad, rrect, W, H

TAU = math.tau


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def sky(ctx, top, bot, y1=H):
    ctx.set_source(lin(ctx, 0, 0, 0, y1, [(0, rgb(top)), (1, rgb(bot))])); ctx.paint()


def glow(ctx, x, y, r, col, a):
    c = rgb(col)
    ctx.set_source(rad(ctx, x, y, 0, r, [(0, c[:3] + (a,)), (1, c[:3] + (0,))]))
    ctx.arc(x, y, r, 0, TAU); ctx.fill()


# ---------------------------------------------------------------- figures
def figure(ctx, x, y, s, kind="robe", bow=0.0, look=0.0, arms=None, alpha=1.0):
    """Simple standing figure, head centre (x, y), head radius s."""
    pal = {
        "robe": ("#efe7d6", "#d8ccb4", "#c49a72", "#5a3a26"),
        "reader": ("#e3a738", "#b98226", "#c68a5e", "#24160f"),
        "rich": ("#6d3f8c", "#4f2b68", "#d2a07a", "#3a2416"),
        "plain": ("#7d8a96", "#5c6873", "#b98a68", "#2f2620"),
        "dark": ("#2c3440", "#1f252e", "#7a6150", "#15110e"),
        "old": ("#5c7a55", "#45603f", "#b98060", "#e9e4dc"),
        "stone": ("#9a9ea6", "#7d828a", "#a9adb3", "#868a92"),
    }[kind]
    body, body_sh, skin, hair = [rgb(c, alpha) for c in pal]
    ctx.save()
    ctx.translate(x, y)
    # body
    src(ctx, body)
    ctx.move_to(-0.6 * s, 1.1 * s)
    ctx.curve_to(-1.4 * s, 1.5 * s, -1.5 * s, 3.2 * s, -1.6 * s, 5.2 * s)
    ctx.line_to(1.6 * s, 5.2 * s)
    ctx.curve_to(1.5 * s, 3.2 * s, 1.4 * s, 1.5 * s, 0.6 * s, 1.1 * s)
    ctx.close_path(); ctx.fill()
    src(ctx, body_sh)
    ctx.move_to(0.1 * s, 1.4 * s); ctx.curve_to(0.5 * s, 3 * s, 0.6 * s, 4 * s, 0.7 * s, 5.2 * s)
    ctx.line_to(1.6 * s, 5.2 * s); ctx.curve_to(1.5 * s, 3.2 * s, 1.4 * s, 1.5 * s, 0.6 * s, 1.1 * s); ctx.close_path(); ctx.fill()
    if arms:
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(0.55 * s)
        for (sx, sy, hx, hy) in arms:
            src(ctx, body_sh); ctx.move_to(sx * s, sy * s); ctx.line_to(hx * s, hy * s); ctx.stroke()
            src(ctx, skin); ctx.arc(hx * s, hy * s, 0.26 * s, 0, TAU); ctx.fill()
    # head
    ctx.translate(0, bow * s * 0.4)
    ctx.rotate(bow * 0.5)
    if kind == "reader":
        src(ctx, hair); ctx.arc(0.1 * s, -1.25 * s, 0.5 * s, 0, TAU); ctx.fill()
        ctx.arc(0, -0.2 * s, 1.08 * s, 0, TAU); ctx.fill()
    src(ctx, skin); ctx.arc(look * 0.15 * s, 0, s, 0, TAU); ctx.fill()
    src(ctx, hair)
    if kind == "robe":
        ctx.arc(0, -0.15 * s, 1.02 * s, math.pi * 1.05, math.pi * 1.95); ctx.fill()
        ctx.move_to(-0.95 * s, -0.2 * s); ctx.curve_to(-1.1 * s, 0.6 * s, -0.9 * s, 1.1 * s, -0.7 * s, 1.2 * s)
        ctx.line_to(-0.6 * s, 0.1 * s); ctx.fill()
        ctx.move_to(0.95 * s, -0.2 * s); ctx.curve_to(1.1 * s, 0.6 * s, 0.9 * s, 1.1 * s, 0.7 * s, 1.2 * s)
        ctx.line_to(0.6 * s, 0.1 * s); ctx.fill()
        ctx.move_to(-0.55 * s, 0.45 * s); ctx.curve_to(-0.4 * s, 1.15 * s, 0.4 * s, 1.15 * s, 0.55 * s, 0.45 * s)
        ctx.curve_to(0.2 * s, 0.7 * s, -0.2 * s, 0.7 * s, -0.55 * s, 0.45 * s); ctx.fill()
    elif kind == "reader":
        ctx.move_to(-0.95 * s, -0.1 * s); ctx.curve_to(-0.9 * s, -1.05 * s, 0.9 * s, -1.05 * s, 0.95 * s, -0.1 * s)
        ctx.curve_to(0.5 * s, -0.55 * s, -0.5 * s, -0.55 * s, -0.95 * s, -0.1 * s); ctx.fill()
    elif kind == "old":
        ctx.arc(-0.85 * s, -0.2 * s, 0.25 * s, 0, TAU); ctx.fill(); ctx.arc(0.85 * s, -0.2 * s, 0.25 * s, 0, TAU); ctx.fill()
        ctx.move_to(-0.8 * s, 0.2 * s); ctx.curve_to(-0.6 * s, 1.2 * s, 0.6 * s, 1.2 * s, 0.8 * s, 0.2 * s)
        ctx.curve_to(0.4 * s, 0.6 * s, -0.4 * s, 0.6 * s, -0.8 * s, 0.2 * s); ctx.fill()
    else:
        ctx.arc(0, -0.2 * s, 1.0 * s, math.pi * 1.05, math.pi * 1.95); ctx.fill()
    ctx.restore()


def rain_streaks(ctx, t, n=50, a=0.3, seed=5):
    r = random.Random(seed)
    ctx.set_line_width(1.6)
    for i in range(n):
        x = r.uniform(0, W); ph = r.uniform(0, 1); sp = r.uniform(0.7, 1)
        y = ((ph + t * 1.1 * sp) % 1) * (H + 80) - 40
        ctx.set_source_rgba(0.7, 0.8, 0.95, a)
        ctx.move_to(x, y); ctx.line_to(x - 5, y + 30); ctx.stroke()


# ---------------------------------------------------------------- visions
def v_car(ctx, S, t, ph):
    sky(ctx, "#0b1322", "#1c2a40")
    for x, y in ((120, 380), (600, 420)):
        src(ctx, rgb("#141a24")); ctx.rectangle(x - 4, y, 8, 560); ctx.fill()
        glow(ctx, x, y, 140, "#f2a14a", 0.5)
        src(ctx, rgb("#ffd79a")); ctx.arc(x, y, 9, 0, TAU); ctx.fill()
    # wet asphalt
    src(ctx, rgb("#151c28")); ctx.rectangle(0, 860, W, H); ctx.fill()
    for x in (120, 600):
        ctx.set_source_rgba(0.95, 0.6, 0.3, 0.12); ctx.save(); ctx.translate(x, 1010); ctx.scale(110, 14); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    ctx.save(); ctx.translate(360, 780); ctx.scale(1.25, 1.25); ctx.translate(-360, -780)
    # car
    src(ctx, rgb("#1e4552"))
    ctx.move_to(60, 860); ctx.curve_to(60, 790, 90, 770, 160, 760); ctx.curve_to(220, 690, 270, 660, 360, 660)
    ctx.curve_to(450, 660, 500, 690, 560, 760); ctx.curve_to(640, 770, 670, 800, 670, 860); ctx.close_path(); ctx.fill()
    src(ctx, rgb("#2d5e6c"))
    ctx.move_to(190, 760); ctx.curve_to(240, 700, 280, 680, 355, 680); ctx.line_to(355, 760); ctx.close_path(); ctx.fill()
    ctx.move_to(370, 680); ctx.curve_to(440, 680, 480, 700, 530, 760); ctx.line_to(370, 760); ctx.close_path(); ctx.fill()
    # Maya inside, forehead on the wheel, shoulders shaking
    sh = math.sin(t * 8.5) * 2.2 if S["beat_start"] <= S["t"] <= S["beat_end"] else 0
    ctx.save(); ctx.rectangle(190, 680, 340, 80); ctx.clip()
    src(ctx, rgb("#e3a738")); ctx.save(); ctx.translate(300, 770 + sh); ctx.scale(70, 40); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#24160f")); ctx.arc(352, 742 + sh, 30, 0, TAU); ctx.fill(); ctx.arc(338, 716 + sh, 15, 0, TAU); ctx.fill()
    src(ctx, rgb("#141414")); ctx.set_line_width(7); ctx.arc(400, 752, 26, 3.4, 5.6); ctx.stroke()
    ctx.restore()
    for x in (180, 540):
        src(ctx, rgb("#0d0f12")); ctx.arc(x, 860, 46, 0, TAU); ctx.fill()
        src(ctx, rgb("#59606a")); ctx.arc(x, 860, 18, 0, TAU); ctx.fill()
    src(ctx, rgb("#f7d58a")); ctx.arc(80, 815, 10, 0, TAU); ctx.fill()
    ctx.restore()
    rain_streaks(ctx, t, 60, 0.32)


def v_statue(ctx, S, t, ph):
    sky(ctx, "#3a2a22", "#20160f")
    glow(ctx, 360, 520, 420, "#ffc87a", 0.22)
    # shelf
    src(ctx, rgb("#5a3a24")); ctx.rectangle(150, 600, 420, 22); ctx.fill()
    dur = S["shot_dur"]
    u = ease((t - 2.6) / 2.4)
    # statue (stone robe figure) dissolving into light
    r = random.Random(4)
    if u < 1:
        ctx.push_group()
        figure(ctx, 360, 330, 42, "stone")
        src(ctx, rgb("#7d828a")); ctx.rectangle(280, 540, 160, 60); ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - u)
    for i in range(70):
        sx, sy = r.uniform(300, 420), r.uniform(290, 590)
        tx, ty = r.uniform(180, 540), r.uniform(900, 1060)
        k = ease((u - i / 140) * 1.4)
        x = sx + (tx - sx) * k + 10 * math.sin(t * 2 + i)
        y = sy + (ty - sy) * k
        a = 0.85 * min(1, u * 3) * (1 - 0.4 * k)
        if a > 0.01:
            ctx.set_source_rgba(1, 0.82, 0.45, a); ctx.arc(x, y, 3 + (i % 3), 0, TAU); ctx.fill()
    # the table it lands on
    src(ctx, rgb("#7a4b2e")); ctx.rectangle(120, 1040, 480, 26); ctx.fill()
    glow(ctx, 360, 1030, 260, "#ffcf7a", 0.35 * u)


def v_walkaway(ctx, S, t, ph):
    sky(ctx, "#f2a65a", "#5b3a6b", 900)
    glow(ctx, 470, 560, 260, "#ffe2a0", 0.65)
    src(ctx, rgb("#fff1c9")); ctx.arc(470, 560, 46, 0, TAU); ctx.fill()
    src(ctx, rgb("#6a4a6a")); ctx.move_to(0, 640); ctx.curve_to(200, 560, 380, 610, 720, 570); ctx.line_to(720, H); ctx.line_to(0, H); ctx.fill()
    src(ctx, rgb("#4a3352")); ctx.move_to(0, 760); ctx.curve_to(240, 700, 480, 740, 720, 700); ctx.line_to(720, H); ctx.line_to(0, H); ctx.fill()
    src(ctx, rgb("#b48a6a")); ctx.move_to(250, H); ctx.line_to(455, 615); ctx.line_to(485, 615); ctx.line_to(700, H); ctx.fill()
    tt = S["t"] - (S["beat_start"] if ph == 1 else S["t"] - t)
    u = ease(t / 9.0) if ph == 1 else ease(0.55 + t / 14)
    # rich young man walking away up the road
    x = 420 + 45 * u; y = 860 - 230 * u; s = 34 * (1 - 0.62 * u)
    bob = abs(math.sin(t * 4.2)) * 4 * (1 - u)
    look = -1.0 if 0.45 < (t % 6) / 6 < 0.6 else 0.0
    figure(ctx, x, y - bob, s, "rich", look=look)
    # the watcher (becomes the reader on the second line)
    kind = "robe" if ph == 1 else "reader"
    if ph == 2 and t < 1.0:
        figure(ctx, 170, 760, 54, "robe")
        ctx.push_group(); figure(ctx, 170, 760, 54, "reader"); ctx.pop_group_to_source(); ctx.paint_with_alpha(ease(t))
    else:
        figure(ctx, 170, 760, 54, kind)
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    lv = 1.0 if ph == 2 else ease((S["t"] - S["beat_start"]) / max(1, S["beat_end"] - S["beat_start"]) * 1.6 - 0.6)
    glow(ctx, 185, 880, 70 + 20 * pulse, "#ff9c8a", 0.6 * lv)


SHEEP = [(random.Random(i).uniform(70, 650), random.Random(i * 7).uniform(640, 1180), random.Random(i * 3).uniform(0.7, 1.1)) for i in range(15)]


def v_sheep(ctx, S, t, ph):
    sky(ctx, "#4a5a8a", "#e8a88a", 700)
    src(ctx, rgb("#556f5a")); ctx.move_to(0, 640); ctx.curve_to(240, 560, 480, 620, 720, 580); ctx.line_to(720, H); ctx.line_to(0, H); ctx.fill()
    src(ctx, rgb("#46604c")); ctx.move_to(0, 820); ctx.curve_to(200, 760, 520, 800, 720, 760); ctx.line_to(720, H); ctx.line_to(0, H); ctx.fill()
    g = ease(t / 4.0) if ph == 2 else 0.0
    cx, cy = 360, 760
    if ph == 2:
        glow(ctx, cx, cy - 60, 300, "#ffd98a", 0.55 * g)
        ctx.push_group(); figure(ctx, cx, cy - 150, 34, "reader", arms=[(1.0, 1.6, 2.2, 3.0)]); ctx.pop_group_to_source(); ctx.paint_with_alpha(g)
        glow(ctx, cx + 75, cy - 50, 50, "#ffe9a8", 0.9 * g)
    for i, (x, y, s) in enumerate(SHEEP):
        wx = x + 14 * math.sin(t * 0.7 + i * 1.9)
        wy = y + 6 * math.sin(t * 0.5 + i)
        if ph == 2:
            ang = i / len(SHEEP) * TAU
            tx = cx + math.cos(ang) * (110 + 40 * (i % 3)); ty = cy + 130 + math.sin(ang) * 70
            wx += (tx - wx) * g * 0.9; wy += (ty - wy) * g * 0.9
        sc = 0.55 + (wy - 600) / 800
        sheep(ctx, wx, wy, 26 * sc * s, facing=1 if i % 2 else -1, t=t + i)


def sheep(ctx, x, y, s, facing=1, t=0.0):
    src(ctx, rgb("#2b2522"))
    for lx in (-0.6, -0.2, 0.3, 0.7):
        ctx.rectangle(x + lx * s, y + 0.3 * s, 0.16 * s, 0.8 * s); ctx.fill()
    src(ctx, rgb("#f4efe6"))
    for (dx, dy, r) in ((-0.6, 0, 0.55), (0, -0.2, 0.62), (0.6, 0, 0.55), (-0.25, 0.25, 0.5), (0.3, 0.25, 0.5)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, TAU); ctx.fill()
    src(ctx, rgb("#2b2522"))
    ctx.save(); ctx.translate(x + facing * 1.05 * s, y - 0.15 * s + math.sin(t * 2) * 0.05 * s); ctx.scale(0.32 * s, 0.4 * s); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()


def hand_stone(ctx, S, t, curl, light):
    sky(ctx, "#121a2c", "#0a0e18")
    glow(ctx, 380, 700, 420, "#ffcf8a", 0.12 + 0.35 * light)
    trem = (1 - min(1, (1 - curl) * 3)) * 1.6
    ox = math.sin(t * 31) * trem; oy = math.cos(t * 27) * trem
    ctx.save(); ctx.translate(ox, oy)
    ctx.translate(360, 640); ctx.scale(1.35, 1.35); ctx.translate(-390, -720)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # forearm with sleeve
    src(ctx, rgb("#b98226")); ctx.set_line_width(150); ctx.move_to(-40, 1010); ctx.line_to(200, 815); ctx.stroke()
    src(ctx, rgb("#e3a738")); ctx.set_line_width(130); ctx.move_to(-40, 1010); ctx.line_to(185, 825); ctx.stroke()
    skin = rgb("#c68a5e"); sh = rgb("#a86f48")
    # palm
    src(ctx, skin); ctx.save(); ctx.translate(345, 772); ctx.scale(150, 58); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    # stone
    src(ctx, rgb("#7f848c")); ctx.save(); ctx.translate(390, 690); ctx.scale(88, 62); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#9aa0a8")); ctx.save(); ctx.translate(372, 668); ctx.scale(46, 24); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#5f646b"))
    for (x, y, r) in ((420, 700, 6), (360, 712, 4), (440, 670, 3)):
        ctx.arc(x, y, r, 0, TAU); ctx.fill()
    # fingers: base at the far end of the palm, curling up and over the stone
    for i in range(4):
        bx = 472 - i * 12; by = 764 - i * 13
        segs = (72 - i * 5, 54 - i * 4, 40 - i * 3)
        a0 = -0.05 + i * 0.02
        angs = [a0 - curl * 1.35, a0 - curl * 2.55, a0 - curl * 3.45]
        pts = [(bx, by)]
        for L, a in zip(segs, angs):
            px, py = pts[-1]; pts.append((px + L * math.cos(a), py + L * math.sin(a)))
        for wdt, col in ((40 - i * 2, sh), (34 - i * 2, skin)):
            src(ctx, col); ctx.set_line_width(wdt)
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.stroke()
        src(ctx, rgb("#e8b896")); ctx.arc(pts[-1][0], pts[-1][1], 8, 0, TAU); ctx.fill()
    # thumb
    tip = (300 + 110 * curl, 735 - 60 * curl - 30 * (1 - curl))
    src(ctx, sh); ctx.set_line_width(44); ctx.move_to(250, 770); ctx.line_to(*tip); ctx.stroke()
    src(ctx, skin); ctx.set_line_width(38); ctx.move_to(250, 770); ctx.line_to(*tip); ctx.stroke()
    ctx.restore()


def v_stone(ctx, S, t, ph):
    if ph == 1:
        hand_stone(ctx, S, t, 1.0, 0.0)
    elif ph == 2:
        hand_stone(ctx, S, t, 1.0 - 0.25 * ease(t / 2.5), 0.2 * ease(t / 2.5))
    else:
        u = ease((t - 2.0) / 3.5)
        hand_stone(ctx, S, t, 0.75 - 0.6 * u, 0.2 + 0.8 * u)


def v_lightpass(ctx, S, t, ph):
    sky(ctx, "#140f12", "#22160f")
    src(ctx, rgb("#5a3622")); ctx.rectangle(0, 860, W, H); ctx.fill()
    u = ease((t - 0.8) / 2.6)
    lx = 220 + 280 * u; ly = 780 - 40 * math.sin(u * math.pi)
    glow(ctx, lx, ly - 60, 360, "#ffc86a", 0.55)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # giver (green sleeve) from left, receiver (yellow) from right
    for (sx, sy, hx, hy, c1, c2, sk) in ((-60, 1000, min(lx - 40, 300) if u < 0.98 else 260 - 30 * ease(t - 3.6), ly + 30, "#45603f", "#5c7a55", "#b98060"),
                                          (780, 1000, max(lx + 40, 420) if u > 0.02 else 560, ly + 30, "#b98226", "#e3a738", "#c68a5e")):
        src(ctx, rgb(c1)); ctx.set_line_width(110); ctx.move_to(sx, sy); ctx.line_to(hx, hy + 40); ctx.stroke()
        src(ctx, rgb(c2)); ctx.set_line_width(94); ctx.move_to(sx, sy); ctx.line_to(hx, hy + 40); ctx.stroke()
        src(ctx, rgb(sk)); ctx.save(); ctx.translate(hx, hy + 18); ctx.scale(54, 30); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    # little clay lamp
    src(ctx, rgb("#a8643a")); ctx.save(); ctx.translate(lx, ly); ctx.scale(60, 24); ctx.arc(0, 0, 1, 0, math.pi); ctx.restore(); ctx.fill()
    src(ctx, rgb("#8a4f2c")); ctx.save(); ctx.translate(lx, ly); ctx.scale(60, 10); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    fl = 1 + 0.1 * math.sin(t * 14) + 0.06 * math.sin(t * 31)
    src(ctx, rgb("#ffcf6a")); ctx.save(); ctx.translate(lx + 40, ly - 26); ctx.scale(12, 28 * fl); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#fff6d6")); ctx.save(); ctx.translate(lx + 40, ly - 20); ctx.scale(5, 12 * fl); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()


def v_basket(ctx, S, t, ph):
    u = ease((t - 0.5) / 2.2)
    sky(ctx, "#0e0b0a", "#1a120c")
    src(ctx, rgb("#2a1c12")); ctx.rectangle(0, 900, W, H); ctx.fill()
    # light pouring out
    glow(ctx, 360, 860, 120 + 720 * u, "#ffd27a", 0.35 + 0.5 * u)
    if u > 0.05:
        ctx.save(); ctx.translate(360, 860); ctx.rotate(t * 0.08)
        for i in range(12):
            ctx.rotate(TAU / 12)
            ctx.set_source_rgba(1, 0.9, 0.6, 0.08 * u)
            ctx.move_to(0, 0); ctx.line_to(900, -60); ctx.line_to(900, 60); ctx.close_path(); ctx.fill()
        ctx.restore()
    src(ctx, rgb("#fff3c8")); ctx.save(); ctx.translate(360, 880); ctx.scale(40, 14); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    # woven basket lifting away
    by = 900 - 760 * u; bx = 360 + 140 * u
    ctx.save(); ctx.translate(bx, by); ctx.rotate(0.35 * u)
    src(ctx, rgb("#a8753f"))
    ctx.move_to(-160, 0); ctx.curve_to(-150, -170, 150, -170, 160, 0); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.45, 0.28, 0.12, 0.8); ctx.set_line_width(5)
    for k in range(1, 6):
        yy = -k * 28
        ww = 160 * math.sqrt(max(0, 1 - (yy / -130) ** 2)) if yy > -130 else 0
        ctx.move_to(-ww, yy); ctx.line_to(ww, yy); ctx.stroke()
    for k in range(-5, 6):
        ctx.move_to(k * 28, 0); ctx.line_to(k * 22, -120); ctx.stroke()
    src(ctx, rgb("#7a5228")); ctx.rectangle(-165, -10, 330, 16); ctx.fill()
    ctx.restore()


def v_pour(ctx, S, t, ph):
    sky(ctx, "#b88a62", "#6e4a34")
    ctx.set_source_rgba(0, 0, 0, 0.06)
    for y in range(0, H, 90):
        for x in range((y // 90) % 2 * 60, W, 120):
            rrect(ctx, x + 4, y + 4, 112, 82, 8); ctx.fill()
    glow(ctx, 360, 600, 500, "#ffe0a8", 0.3)
    level = ease(t / 8.0)
    # basin
    src(ctx, rgb("#8a8f8a")); ctx.move_to(150, 900); ctx.curve_to(170, 1080, 550, 1080, 570, 900); ctx.close_path(); ctx.fill()
    src(ctx, rgb("#6e746f")); ctx.save(); ctx.translate(360, 900); ctx.scale(210, 40); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#5b8fb5")); ctx.save(); ctx.translate(360, 906); ctx.scale(190 * (0.6 + 0.4 * level), 30 * (0.6 + 0.4 * level)); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    for k in range(3):
        r = ((t * 0.7 + k / 3) % 1)
        ctx.set_source_rgba(0.85, 0.95, 1, 0.5 * (1 - r)); ctx.set_line_width(2.5)
        ctx.save(); ctx.translate(385, 906); ctx.scale(30 + 140 * r, 6 + 22 * r); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.stroke()
    # pitcher, tilted
    ctx.save(); ctx.translate(250, 470); ctx.rotate(0.85)
    src(ctx, rgb("#b5643f"))
    ctx.move_to(-70, -120); ctx.curve_to(-120, -40, -120, 80, -60, 120); ctx.line_to(60, 120)
    ctx.curve_to(120, 80, 120, -40, 70, -120); ctx.close_path(); ctx.fill()
    src(ctx, rgb("#8f4a2c")); ctx.rectangle(-75, -140, 150, 26); ctx.fill()
    ctx.set_line_width(16); ctx.arc(-110, -10, 46, 1.6, 4.7); ctx.stroke()
    ctx.restore()
    # stream
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for wdt, a in ((26, 0.5), (14, 0.85), (4, 0.9)):
        ctx.set_source_rgba(0.55 + 0.4 * (wdt < 10), 0.78 + 0.2 * (wdt < 10), 1, a); ctx.set_line_width(wdt)
        ctx.move_to(352, 432)
        for i in range(1, 13):
            y = 432 + i * 40
            ctx.line_to(372 + i * 1.2 + 4 * math.sin(t * 9 + i) * (wdt / 26), y)
        ctx.stroke()


def v_feet(ctx, S, t, ph):
    sky(ctx, "#3a2a24", "#1e1612")
    glow(ctx, 400, 700, 460, "#ffc27a", 0.3)
    src(ctx, rgb("#2a1d16")); ctx.rectangle(0, 1000, W, H); ctx.fill()
    frac = (S["t"] - S["beat_start"]) / max(1, S["beat_end"] - S["beat_start"])
    dark = ease((frac - 0.62) / 0.15)
    # bench + seated friend
    src(ctx, rgb("#5a3a24")); ctx.rectangle(430, 760, 260, 30); ctx.fill()
    ctx.push_group()
    figure(ctx, 560, 560, 44, "plain")
    src(ctx, rgb("#5c6873")); ctx.set_line_width(48); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(540, 790); ctx.line_to(430, 800); ctx.line_to(420, 940); ctx.stroke()
    ctx.pop_group_to_source(); ctx.paint()
    if dark > 0:
        ctx.set_source_rgba(0.05, 0.05, 0.1, 0.55 * dark); ctx.rectangle(470, 480, 220, 340); ctx.fill()
    # feet in the basin
    src(ctx, rgb("#b98a68")); ctx.save(); ctx.translate(400, 958); ctx.scale(52, 20); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    src(ctx, rgb("#8a8f8a")); ctx.move_to(270, 950); ctx.curve_to(280, 1040, 520, 1040, 530, 950); ctx.close_path(); ctx.fill()
    src(ctx, rgb("#5b8fb5")); ctx.save(); ctx.translate(400, 952); ctx.scale(126, 18); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    # kneeling figure with towel
    kx, ky = 190, 720
    figure(ctx, kx, ky, 44, "robe", bow=0.5)
    sw = math.sin(t * 3.2) * 22
    src(ctx, rgb("#d8ccb4")); ctx.set_line_width(36); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(kx + 20, ky + 90); ctx.line_to(330 + sw, 930); ctx.stroke()
    src(ctx, rgb("#f4efe6")); rrect(ctx, 320 + sw, 905, 90, 40, 10); ctx.fill()
    for k in range(4):
        dy = ((t * 1.3 + k / 4) % 1)
        ctx.set_source_rgba(0.7, 0.85, 1, 0.8 * (1 - dy)); ctx.arc(360 + k * 22 + sw * 0.3, 950 + dy * 50, 4, 0, TAU); ctx.fill()


CRACKS = [[(random.Random(k).uniform(0, W), random.Random(k + 50).uniform(900, H))] for k in range(14)]


def v_spill(ctx, S, t, ph):
    sky(ctx, "#e6b77a", "#c48a52", 800)
    src(ctx, rgb("#a8743f")); ctx.rectangle(0, 800, W, H); ctx.fill()
    ctx.set_source_rgba(0.4, 0.24, 0.1, 0.55); ctx.set_line_width(3)
    r = random.Random(9)
    for k in range(18):
        x, y = r.uniform(0, W), r.uniform(850, H)
        ctx.move_to(x, y)
        for j in range(4):
            x += r.uniform(-50, 50); y += r.uniform(-25, 25); ctx.line_to(x, y)
        ctx.stroke()
    if ph == 1:
        u = ease(t / 3.0)
        wet = u
        flow = 1 - ease((t - 2.2) / 1.5)
    else:
        wet = 1.0; flow = 0.0
    # wet patch
    ctx.set_source_rgba(0.35, 0.22, 0.12, 0.75 * wet)
    ctx.save(); ctx.translate(380, 1000); ctx.scale(60 + 190 * wet, 22 + 60 * wet); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    ctx.set_source_rgba(0.55, 0.75, 0.95, 0.45 * wet * (1 if ph == 1 else max(0.2, 1 - t / 6)))
    ctx.save(); ctx.translate(380, 1000); ctx.scale(30 + 120 * wet, 10 + 34 * wet); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
    if ph == 1:
        ctx.save(); ctx.translate(300, 380); ctx.rotate(1.2 + 0.9 * ease(t / 3))
        src(ctx, rgb("#b5643f"))
        ctx.move_to(-60, -100); ctx.curve_to(-100, -30, -100, 70, -50, 100); ctx.line_to(50, 100)
        ctx.curve_to(100, 70, 100, -30, 60, -100); ctx.close_path(); ctx.fill()
        src(ctx, rgb("#8f4a2c")); ctx.rectangle(-65, -118, 130, 22); ctx.fill()
        ctx.restore()
        if flow > 0.02:
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for wdt, a in ((30 * flow, 0.5), (14 * flow, 0.85)):
                ctx.set_source_rgba(0.6, 0.82, 1, a); ctx.set_line_width(max(1, wdt))
                ctx.move_to(372, 400)
                for i in range(1, 15):
                    ctx.line_to(378 + 3 * math.sin(t * 10 + i), 400 + i * 43)
                ctx.stroke()
    else:
        # the sprout
        g = ease(t / 4.5)
        bloom = ease((t - 5.0) / 2.0)
        h = 260 * g
        src(ctx, rgb("#4f8a4c")); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(380, 1000); ctx.curve_to(370, 1000 - h * 0.4, 395, 1000 - h * 0.7, 382, 1000 - h); ctx.stroke()
        for side, yy in ((-1, 0.45), (1, 0.65)):
            lg = ease((g - yy * 0.6) * 2.5)
            if lg > 0:
                ctx.save(); ctx.translate(380, 1000 - h * yy); ctx.rotate(side * (0.9 - 0.3 * lg))
                ctx.scale(70 * lg, 26 * lg); ctx.arc(side * 1, 0, 1, 0, TAU); ctx.restore()
                src(ctx, rgb("#5fa35a")); ctx.fill()
        if bloom > 0:
            fx, fy = 382, 1000 - h
            glow(ctx, fx, fy, 160 * bloom, "#fff0a0", 0.5 * bloom)
            for k in range(6):
                a = k / 6 * TAU + 0.3
                ctx.save(); ctx.translate(fx + math.cos(a) * 22 * bloom, fy + math.sin(a) * 22 * bloom); ctx.rotate(a)
                ctx.scale(24 * bloom, 13 * bloom); ctx.arc(0, 0, 1, 0, TAU); ctx.restore()
                src(ctx, rgb("#f6c94f")); ctx.fill()
            src(ctx, rgb("#c97a2a")); ctx.arc(fx, fy, 11 * bloom, 0, TAU); ctx.fill()


def v_rest(ctx, S, t, ph):
    sky(ctx, "#f0a868", "#6b4a7a", 820)
    src(ctx, rgb("#5a4a5a")); ctx.rectangle(0, 820, W, H); ctx.fill()
    src(ctx, rgb("#8a6a5a")); ctx.move_to(0, H); ctx.line_to(330, 820); ctx.line_to(390, 820); ctx.line_to(W, H); ctx.fill()
    # tree + lamp-lit table
    src(ctx, rgb("#3a2a2a")); ctx.rectangle(520, 520, 26, 320); ctx.fill()
    ctx.arc(530, 500, 120, 0, TAU); ctx.fill(); ctx.arc(450, 540, 80, 0, TAU); ctx.fill()
    glow(ctx, 470, 800, 280, "#ffd27a", 0.55)
    src(ctx, rgb("#7a4b2e")); ctx.rectangle(380, 860, 200, 18); ctx.fill()
    ctx.rectangle(395, 878, 12, 90); ctx.fill(); ctx.rectangle(553, 878, 12, 90); ctx.fill()
    src(ctx, rgb("#ffe7a8")); ctx.arc(470, 840, 12, 0, TAU); ctx.fill()
    for i, (x0, delay, kind) in enumerate(((60, 0.0, "plain"), (170, 0.7, "old"), (280, 1.4, "reader"))):
        u = ease((t - delay) / 2.2)
        x = x0 + 60 * u; y = 820 + i * 40
        down = ease((t - delay - 2.0) / 0.8)
        bow = 0.55 * (1 - down)
        figure(ctx, x, y - 20 * (1 - bow), 30, kind, bow=bow)
        # sack: on the back, then on the ground
        sx = x - 40 + 10 * down; sy = (y + 40) + (130 * down)
        src(ctx, rgb("#a88a5a")); ctx.save(); ctx.translate(sx, sy); ctx.scale(42, 48); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
        src(ctx, rgb("#7a6440")); ctx.set_line_width(4); ctx.move_to(sx - 10, sy - 44); ctx.line_to(sx + 10, sy - 44); ctx.stroke()


def v_montage(ctx, S, t, ph):
    sky(ctx, "#141a2e", "#0c0f1a")
    segs = S["beat_segs"]
    starts = [s[1] for s in segs[1:5]] + [1e9] * 4
    rects = ((40, 120), (370, 120), (40, 520), (370, 520))
    for k, (x, y) in enumerate(rects):
        on = ease((S["t"] - starts[k] + 0.15) / 0.4)
        w, h = 310, 370
        ctx.set_source_rgba(0.2, 0.25, 0.4, 0.5 + 0.3 * on); rrect(ctx, x, y, w, h, 22); ctx.fill()
        if on > 0:
            ctx.push_group()
            ctx.translate(x + w / 2, y + h / 2)
            glow(ctx, 0, 0, 200, "#ffcf7a", 0.35)
            if k == 0:  # weep
                src(ctx, rgb("#f7f2ea")); ctx.save(); ctx.scale(80, 46); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
                src(ctx, rgb("#3b2214")); ctx.arc(0, 4, 32, 0, TAU); ctx.fill()
                src(ctx, rgb("#c68a5e")); ctx.rectangle(-90, -60, 180, 34); ctx.fill()
                ctx.set_source_rgba(0.8, 0.9, 1, 0.95)
                ty = 60 + 50 * ((t * 0.6) % 1)
                ctx.move_to(40, ty - 18); ctx.curve_to(54, ty, 50, ty + 14, 40, ty + 14); ctx.curve_to(30, ty + 14, 26, ty, 40, ty - 18); ctx.fill()
            elif k == 1:  # look longer
                for s in (-1, 1):
                    src(ctx, rgb("#f7f2ea")); ctx.save(); ctx.translate(s * 66, -10); ctx.scale(52, 34); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
                    src(ctx, rgb("#3b2214")); ctx.arc(s * 66 + 10, -6, 22, 0, TAU); ctx.fill()
                    src(ctx, (1, 1, 1, 1)); ctx.arc(s * 66 + 16, -14, 6, 0, TAU); ctx.fill()
                glow(ctx, 0, 90, 60, "#ff9c8a", 0.8)
            elif k == 2:  # open hand
                src(ctx, rgb("#c68a5e")); ctx.save(); ctx.translate(0, 40); ctx.scale(100, 40); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
                ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(26)
                for i in range(4):
                    ctx.move_to(60, 30 - i * 6); ctx.line_to(140, 10 - i * 12); ctx.stroke()
                src(ctx, rgb("#7f848c")); ctx.save(); ctx.translate(-10, 0); ctx.scale(50, 36); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
            else:  # towel + basin
                src(ctx, rgb("#8a8f8a")); ctx.move_to(-110, 30); ctx.curve_to(-100, 120, 100, 120, 110, 30); ctx.close_path(); ctx.fill()
                src(ctx, rgb("#5b8fb5")); ctx.save(); ctx.translate(0, 34); ctx.scale(100, 16); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()
                src(ctx, rgb("#f4efe6")); rrect(ctx, -60 + 20 * math.sin(t * 3), -70, 120, 60, 12); ctx.fill()
            ctx.pop_group_to_source(); ctx.paint_with_alpha(on)


def v_crown(ctx, S, t, ph):
    sky(ctx, "#3a2a1e", "#1b130d")
    segs = S["beat_segs"]
    t2 = segs[1][1] if len(segs) > 1 else S["beat_start"] + 1.2
    u = ease((S["t"] - t2 + 0.2) / 0.9)
    glow(ctx, 360, 640, 380, "#ffd27a", 0.35)
    # crown sinks and fades
    ctx.save(); ctx.translate(360, 560 + 260 * u); ctx.rotate(0.4 * u)
    a = 1 - u
    ctx.set_source_rgba(0.95, 0.75, 0.25, a)
    ctx.move_to(-130, 60); ctx.line_to(-130, -60); ctx.line_to(-65, 0); ctx.line_to(0, -90); ctx.line_to(65, 0); ctx.line_to(130, -60); ctx.line_to(130, 60); ctx.close_path(); ctx.fill()
    for x, c in ((-70, "#c0392b"), (0, "#2e86c1"), (70, "#27ae60")):
        ctx.set_source_rgba(*rgb(c)[:3], a); ctx.arc(x, 30, 12, 0, TAU); ctx.fill()
    ctx.restore()
    # apron descends
    if u > 0:
        ctx.push_group()
        ctx.translate(360, 420 + 200 * u)
        src(ctx, rgb("#efe6d2"))
        ctx.move_to(-70, -40); ctx.line_to(70, -40); ctx.line_to(80, 60); ctx.curve_to(130, 80, 140, 160, 130, 330)
        ctx.line_to(-130, 330); ctx.curve_to(-140, 160, -130, 80, -80, 60); ctx.close_path(); ctx.fill()
        src(ctx, rgb("#d8ccb2")); rrect(ctx, -60, 180, 120, 80, 10); ctx.fill()
        src(ctx, rgb("#c9b48a")); ctx.set_line_width(6)
        ctx.move_to(-70, -40); ctx.curve_to(-60, -150, 60, -150, 70, -40); ctx.stroke()
        ctx.move_to(-82, 62); ctx.curve_to(-150, 70, -170, 110, -180, 150); ctx.stroke()
        ctx.move_to(82, 62); ctx.curve_to(150, 70, 170, 110, 180, 150); ctx.stroke()
        ctx.pop_group_to_source(); ctx.paint_with_alpha(u)


STARS = [(random.Random(k).uniform(0, W), random.Random(k + 999).uniform(0, 1500), random.Random(k + 5).uniform(0.8, 2.6)) for k in range(170)]


def v_stars(ctx, S, t, ph):
    dur = S["shot_dur"]
    u = ease(t / (dur * 0.92))
    off = 1500 * (1 - u)   # world is 2780 tall: stars on top, sea at the bottom
    ctx.save(); ctx.translate(0, -off)
    ctx.set_source(lin(ctx, 0, 0, 0, 2780, [(0, rgb("#070a1a")), (0.42, rgb("#1a2350")), (0.52, rgb("#3a4f80")),
                                            (0.535, rgb("#2a6f8a")), (0.75, rgb("#0d3550")), (1, rgb("#03101c"))]))
    ctx.rectangle(0, 0, W, 2780); ctx.fill()
    ctx.set_source(rad(ctx, 360, 500, 0, 520, [(0, (0.7, 0.6, 1, 0.22)), (1, (0.5, 0.4, 0.9, 0))])); ctx.rectangle(0, 0, W, 1200); ctx.fill()
    for (x, y, r) in STARS:
        tw = 0.6 + 0.4 * math.sin(t * 2 + x)
        ctx.set_source_rgba(1, 0.97, 0.88, 0.8 * tw); ctx.arc(x, y, r, 0, TAU); ctx.fill()
    # surface line
    ctx.set_source_rgba(0.8, 0.9, 1, 0.4); ctx.set_line_width(3)
    ctx.move_to(0, 1480)
    for x in range(0, W + 40, 40):
        ctx.line_to(x, 1480 + 6 * math.sin(x / 50 + t * 2))
    ctx.stroke()
    # bubbles in the deep
    for k in range(24):
        bx = (k * 97) % W; by = 2700 - ((t * 60 + k * 113) % 1200)
        ctx.set_source_rgba(0.7, 0.9, 1, 0.35); ctx.set_line_width(2); ctx.arc(bx, by, 4 + k % 5, 0, TAU); ctx.stroke()
    ctx.restore()
    # the light that rises with us and is never left behind
    y = 700 + 30 * math.sin(t * 1.3)
    glow(ctx, 360, y, 240, "#ffd98a", 0.45)
    glow(ctx, 360, y, 60, "#fff6d6", 0.9)


def v_least(ctx, S, t, ph):
    sky(ctx, "#121826", "#1c2232")
    src(ctx, rgb("#2a2f3a")); ctx.rectangle(0, 300, W, 700); ctx.fill()
    src(ctx, rgb("#3a3f4a"))
    for y in range(320, 1000, 46):
        for x in range((y // 46) % 2 * 50, W, 100):
            ctx.rectangle(x + 3, y + 3, 94, 40); ctx.fill()
    src(ctx, rgb("#20242c")); ctx.rectangle(0, 1000, W, H); ctx.fill()
    src(ctx, rgb("#11141a")); ctx.rectangle(600, 200, 10, 820); ctx.fill()
    glow(ctx, 605, 210, 260, "#f2b45a", 0.45)
    u = ease(t / 2.4)
    give = ease((t - 2.4) / 1.4)
    warm = ease((t - 3.4) / 1.6)
    glow(ctx, 380, 880, 380 * warm + 1, "#ffcf7a", 0.45 * warm)
    # seated person, wrapped, shivering then lifting their head
    shiver = math.sin(t * 22) * 1.5 * (1 - warm)
    src(ctx, rgb("#55606e")); ctx.save(); ctx.translate(430 + shiver, 930); ctx.scale(95, 90); ctx.arc(0, 0, 1, math.pi, TAU); ctx.restore(); ctx.fill()
    ctx.rectangle(335 + shiver, 930, 190, 70); ctx.fill()
    figure(ctx, 430 + shiver, 815 - 25 * warm, 34, "plain", bow=0.6 * (1 - warm))
    # the coat lands on their shoulders
    if give > 0:
        ctx.push_group()
        src(ctx, rgb("#a4462e")); ctx.save(); ctx.translate(430, 900 - 120 * (1 - give)); ctx.scale(115, 80); ctx.arc(0, 0, 1, math.pi, TAU); ctx.restore(); ctx.fill()
        ctx.rectangle(315, 900 - 120 * (1 - give), 230, 60); ctx.fill()
        ctx.pop_group_to_source(); ctx.paint_with_alpha(give)
    # the reader walks in and kneels
    rx = -60 + 260 * u
    kneel = ease((t - 2.0) / 0.6)
    figure(ctx, rx, 760 + 70 * kneel, 38, "reader", bow=0.25 * kneel, arms=[(1.0, 1.6, 2.6 + 0.6 * kneel, 2.4 - 0.6 * kneel)])
    if warm > 0:
        src(ctx, rgb("#d9a85a")); ctx.save(); ctx.translate(rx + 120, 880 - 20 * warm); ctx.scale(30, 18); ctx.arc(0, 0, 1, 0, TAU); ctx.restore(); ctx.fill()


VISIONS = dict(car=v_car, statue=v_statue, walkaway=v_walkaway, sheep=v_sheep, stone=v_stone, lightpass=v_lightpass,
               basket=v_basket, pour=v_pour, feet=v_feet, spill=v_spill, rest=v_rest, montage=v_montage,
               crown=v_crown, stars=v_stars, least=v_least)


def draw_vision(ctx, S, name):
    base = name.rstrip("0123456789")
    ph = int(name[len(base):] or 1)
    VISIONS[base](ctx, S, S["shot_t"], ph)
