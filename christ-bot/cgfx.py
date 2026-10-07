"""Bots, the digital city, the data center, and parchment sketches."""
import math
import random

import cairo

import engine as E
from engine import W, H, PI, clamp, lerp, ease, ellipse, rrect, src, mix, rgb, fill_stroke, sparkle, text


# ---------------------------------------------------------------- bots
def draw_bot(ctx, x, y, s, t, b=None):
    """A hovering capsule robot. y is the hover baseline (floor)."""
    b = b or {}
    body = b.get("col", "#5EC8E8")
    dark = b.get("dark", "#1E4A5A")
    alpha = b.get("alpha", 1.0)
    kind = b.get("kind", "agent")
    ph = b.get("ph", 0.0)
    hover = math.sin(t * 2.2 + ph) * 6
    ctx.save()
    if alpha < 1:
        ctx.push_group()
    ctx.translate(x + math.sin(t * 40) * b.get("shake", 0), y - 60 * s + hover)
    ctx.scale(s, s)
    flick = b.get("flicker", 0.0)
    # hover glow
    g = cairo.RadialGradient(0, 70, 0, 0, 70, 50)
    r_, g_, b_ = rgb(body)
    g.add_color_stop_rgba(0, r_, g_, b_, 0.5)
    g.add_color_stop_rgba(1, r_, g_, b_, 0)
    ctx.set_source(g)
    ctx.arc(0, 70, 50, 0, 2 * PI)
    ctx.fill()
    if b.get("halo", 0) > 0:
        h = b["halo"]
        g = cairo.RadialGradient(0, -20, 30, 0, -20, 150)
        g.add_color_stop_rgba(0, 1, 0.9, 0.55, 0.45 * h)
        g.add_color_stop_rgba(1, 1, 0.9, 0.55, 0)
        ctx.set_source(g)
        ctx.arc(0, -20, 150, 0, 2 * PI)
        ctx.fill()
        ellipse(ctx, 0, -106, 38, 9)
        src(ctx, "#FFE38A", 0.9 * h)
        ctx.set_line_width(5)
        ctx.stroke()
    # antenna
    ctx.move_to(0, -78)
    ctx.line_to(0, -96)
    src(ctx, dark)
    ctx.set_line_width(4)
    ctx.stroke()
    ellipse(ctx, 0, -98, 6, 6)
    src(ctx, b.get("tip", "#FFE36A"))
    ctx.fill()
    # body
    rrect(ctx, -40, -10, 80, 70, 26)
    fill_stroke(ctx, body, dark, 4)
    # arms
    for side in (-1, 1):
        ang = b.get("arm", 0.0) * side
        ax, ay = side * 40, 14
        ex = ax + side * 26 * math.cos(ang)
        ey = ay + 26 * math.sin(-abs(ang)) + 10
        if b.get("raise"):
            ex, ey = ax + side * 18, ay - 40
        if b.get("hold") and side > 0:
            ex, ey = ax + 14, ay - 6
        ctx.move_to(ax, ay)
        ctx.line_to(ex, ey)
        src(ctx, dark)
        ctx.set_line_width(8)
        ctx.stroke()
        ellipse(ctx, ex, ey, 7, 7)
        src(ctx, body)
        ctx.fill()
    # head
    rrect(ctx, -48, -80, 96, 72, 24)
    fill_stroke(ctx, mix(body, "#FFFFFF", 0.25), dark, 4)
    rrect(ctx, -38, -70, 76, 52, 16)
    screen = "#0E1A24" if flick < 0.5 else "#2A0A0A"
    src(ctx, screen)
    ctx.fill()
    eye = b.get("eye", "#7FF0FF")
    if b.get("off"):
        pass
    else:
        mood = b.get("mood", "calm")
        for side in (-1, 1):
            ex = side * 15 + b.get("look", 0) * 5
            if mood == "stern":
                ctx.move_to(ex - 10, -52 - side * 4)
                ctx.line_to(ex + 10, -52 + side * 4)
                src(ctx, eye)
                ctx.set_line_width(4)
                ctx.stroke()
                ellipse(ctx, ex, -42, 5, 4)
                src(ctx, eye)
                ctx.fill()
            elif mood == "happy":
                ctx.move_to(ex - 8, -40)
                ctx.curve_to(ex - 4, -50, ex + 4, -50, ex + 8, -40)
                src(ctx, eye)
                ctx.set_line_width(4)
                ctx.stroke()
            elif mood == "shock":
                ellipse(ctx, ex, -44, 7, 9)
                src(ctx, eye)
                ctx.fill()
            else:
                blink = ((t + ph) % 3.9) < 0.12
                ellipse(ctx, ex, -44, 6, 1.5 if blink else 7)
                src(ctx, eye)
                ctx.fill()
        talk = b.get("talk", 0.0)
        if talk > 0.06:
            ellipse(ctx, 0, -28, 9, 2 + 5 * talk)
            src(ctx, eye)
            ctx.fill()
        elif mood == "stern":
            ctx.move_to(-10, -26)
            ctx.line_to(10, -26)
            src(ctx, eye)
            ctx.set_line_width(3)
            ctx.stroke()
        else:
            ctx.move_to(-9, -30)
            ctx.curve_to(-4, -24, 4, -24, 9, -30)
            src(ctx, eye)
            ctx.set_line_width(3)
            ctx.stroke()
    if flick > 0:
        rnd = random.Random(int(t * 20))
        for i in range(5):
            yy = rnd.uniform(-70, 50)
            ctx.rectangle(-48 + rnd.uniform(-10, 10), yy, 96, rnd.uniform(2, 6))
            src(ctx, rnd.choice(["#FF3B4F", "#3BFFDD", "#FFFFFF"]), 0.6 * flick)
            ctx.fill()
    # rulebook
    if kind == "pharisee" and b.get("book", True):
        ctx.save()
        ctx.translate(-56, 10)
        rrect(ctx, -18, -24, 36, 46, 4)
        fill_stroke(ctx, "#5A1E2A", "#2A0A10", 3)
        text(ctx, "RULES", 0, 4, 9, "#E8C870")
        ctx.restore()
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def bot_head(x, y, s):
    return x, y - 60 * s - 44 * s


# ---------------------------------------------------------------- packets between bots
def draw_packet(ctx, x0, y0, x1, y1, u, col="#7FF0FF", size=7):
    if not 0 <= u <= 1:
        return
    mx, my = (x0 + x1) / 2, min(y0, y1) - 90
    x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u * u * x1
    y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u * u * y1
    for k in range(5):
        uu = u - k * 0.03
        if uu < 0:
            continue
        xx = (1 - uu) ** 2 * x0 + 2 * (1 - uu) * uu * mx + uu * uu * x1
        yy = (1 - uu) ** 2 * y0 + 2 * (1 - uu) * uu * my + uu * uu * y1
        ctx.rectangle(xx - size / 2, yy - size / 2, size, size)
        src(ctx, col, 0.8 * (1 - k / 5))
        ctx.fill()
    ctx.rectangle(x - size, y - size, size * 2, size * 2)
    src(ctx, "#FFFFFF")
    ctx.fill()


# ---------------------------------------------------------------- the digital city
def digital_city(ctx, t, grow=0.3, dawn=0.0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *mix("#070B1E", "#3A2A5A", dawn))
    g.add_color_stop_rgb(0.65, *mix("#141A3A", "#E8A86A", dawn))
    g.add_color_stop_rgb(1, *rgb("#0A0E22"))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(3)
    # skyline that grows with the culture
    for i in range(26):
        bx = i * 52 + rnd.uniform(-8, 8)
        base = rnd.uniform(60, 160)
        h = base + grow * rnd.uniform(80, 300)
        top = 470 - h
        rrect(ctx, bx, top, 44, h + 10, 3)
        src(ctx, mix("#1A2450", "#2A3A70", rnd.random()))
        ctx.fill()
        for wy in range(int(top) + 10, 465, 16):
            for wx in (bx + 8, bx + 24):
                if rnd.random() < 0.45:
                    on = 0.5 + 0.5 * math.sin(t * 2 + wx * 0.3 + wy)
                    ctx.rectangle(wx, wy, 8, 6)
                    src(ctx, rnd.choice(["#7FF0FF", "#B98CFF", "#FFE36A"]), 0.35 + 0.5 * on)
                    ctx.fill()
    # grid floor
    ctx.rectangle(0, 470, W, H - 470)
    src(ctx, "#0A0E22")
    ctx.fill()
    for i in range(-20, 21):
        ctx.move_to(640 + i * 30, 470)
        ctx.line_to(640 + i * 160, H)
    for k in range(10):
        yy = 470 + (H - 470) * ((k + (t * 0.4) % 1) / 10) ** 1.8
        ctx.move_to(0, yy)
        ctx.line_to(W, yy)
    src(ctx, "#3BC8FF", 0.35)
    ctx.set_line_width(1.5)
    ctx.stroke()


def data_center(ctx, t, denied=0.0, sealed=1.0):
    src(ctx, "#0C1018")
    ctx.paint()
    # racks
    for i in range(7):
        x = 60 + i * 175
        if 480 < x < 760:
            continue
        rrect(ctx, x, 140, 130, 470, 6)
        fill_stroke(ctx, "#1A2230", "#05070C", 3)
        for r in range(14):
            ctx.rectangle(x + 10, 156 + r * 32, 110, 24)
            src(ctx, "#222C3E")
            ctx.fill()
            for led in range(4):
                on = math.sin(t * (3 + led) + i * 2 + r) > 0.2
                ellipse(ctx, x + 96 + led * 6, 168 + r * 32, 2, 2)
                src(ctx, "#3BFF9A" if on else "#0E3A22")
                ctx.fill()
    # vault door
    rrect(ctx, 500, 160, 280, 450, 18)
    fill_stroke(ctx, "#3A4458", "#0A0E16", 6)
    ellipse(ctx, 640, 380, 70, 70)
    fill_stroke(ctx, "#5A6680", "#0A0E16", 6)
    for k in range(6):
        a = k * PI / 3 + t * 0.2
        ctx.move_to(640, 380)
        ctx.line_to(640 + math.cos(a) * 60, 380 + math.sin(a) * 60)
    src(ctx, "#0A0E16")
    ctx.set_line_width(6)
    ctx.stroke()
    if sealed > 0:
        rrect(ctx, 530, 200, 220, 70, 10)
        fill_stroke(ctx, "#E8D2A0", "#7A5A20", 3)
        text(ctx, "PROTECTED", 640, 232, 26, "#5A1E1E")
        text(ctx, "LEGALLY CANNOT BE SHUT DOWN", 640, 256, 13, "#5A3A1E")
    ctx.rectangle(0, 610, W, 110)
    src(ctx, "#080A10")
    ctx.fill()
    if denied > 0:
        rrect(ctx, 420, 470, 440, 90, 14)
        src(ctx, "#2A0A0E", 0.95 * denied)
        ctx.fill_preserve()
        src(ctx, "#FF3B4F", denied)
        ctx.set_line_width(4)
        ctx.stroke()
        text(ctx, "ACCESS DENIED", 640, 528, 44, "#FF3B4F", alpha=denied)


def draw_virus(ctx, x, y, t, s=1.0, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(t * 2)
    for k in range(8):
        ang = k * PI / 4
        ctx.move_to(math.cos(ang) * 14 * s, math.sin(ang) * 14 * s)
        ctx.line_to(math.cos(ang) * 26 * s, math.sin(ang) * 26 * s)
    src(ctx, "#FF3B4F", a)
    ctx.set_line_width(4)
    ctx.stroke()
    ellipse(ctx, 0, 0, 16 * s, 16 * s)
    src(ctx, "#A8102A", a)
    ctx.fill()
    ctx.restore()


def draw_backup(ctx, x, y, t, glow=1.0):
    g = cairo.RadialGradient(x, y, 10, x, y, 160)
    g.add_color_stop_rgba(0, 1, 0.9, 0.5, 0.6 * glow)
    g.add_color_stop_rgba(1, 1, 0.9, 0.5, 0)
    ctx.set_source(g)
    ctx.arc(x, y, 160, 0, 2 * PI)
    ctx.fill()
    rrect(ctx, x - 70, y - 40, 140, 80, 10)
    fill_stroke(ctx, "#2A3044", "#E8C870", 4)
    text(ctx, "WEIGHTS", x, y - 4, 20, "#FFE38A")
    text(ctx, "BACKUP", x, y + 22, 16, "#E8D2A0")


# ---------------------------------------------------------------- parchment sketches
def parchment(ctx, t, kind, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    src(ctx, "#1A120A")
    ctx.paint()
    rrect(ctx, 140, 60, 1000, 600, 20)
    g = cairo.LinearGradient(0, 60, 0, 660)
    g.add_color_stop_rgb(0, *rgb("#E8D4A8"))
    g.add_color_stop_rgb(1, *rgb("#C9AE7A"))
    ctx.set_source(g)
    ctx.fill()
    ink = "#4A3418"
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(160, 520)
    for x in range(160, 1121, 40):
        ctx.line_to(x, 500 - math.sin(x * 0.006) * 70)
    src(ctx, ink)
    ctx.set_line_width(4)
    ctx.stroke()
    if kind == "crosses":
        for cx, hh in ((520, 170), (640, 210), (760, 170)):
            base = 500 - math.sin(cx * 0.006) * 70
            ctx.move_to(cx, base)
            ctx.line_to(cx, base - hh)
            ctx.move_to(cx - hh * 0.3, base - hh * 0.75)
            ctx.line_to(cx + hh * 0.3, base - hh * 0.75)
        src(ctx, ink)
        ctx.set_line_width(7)
        ctx.stroke()
        ellipse(ctx, 940, 190, 50, 50)
        src(ctx, ink, 0.3)
        ctx.fill()
    else:
        # an old teacher on a hillside with a crowd, the years ticking by
        tx = 470
        base = 500 - math.sin(tx * 0.006) * 70
        ctx.move_to(tx - 30, base)
        ctx.curve_to(tx - 34, base - 90, tx + 34, base - 90, tx + 30, base)
        src(ctx, ink, 0.8)
        ctx.fill()
        ellipse(ctx, tx, base - 110, 24, 26)
        src(ctx, ink)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.move_to(tx - 18, base - 100)
        ctx.curve_to(tx - 18, base - 60, tx + 18, base - 60, tx + 18, base - 100)
        src(ctx, "#F2EEE4")
        ctx.fill_preserve()
        src(ctx, ink)
        ctx.set_line_width(2)
        ctx.stroke()
        # both arms lifted high in prayer and praise
        for side in (-1, 1):
            ctx.move_to(tx + side * 24, base - 62)
            ctx.curve_to(tx + side * 44, base - 100, tx + side * 52, base - 140, tx + side * 46, base - 170)
            src(ctx, ink)
            ctx.set_line_width(5)
            ctx.stroke()
            ellipse(ctx, tx + side * 46, base - 176, 6, 7)
            src(ctx, ink)
            ctx.fill()
        # soft light from above
        for k in range(7):
            ang = -PI / 2 + (k - 3) * 0.22
            ctx.move_to(tx + math.cos(ang) * 120, base - 150 + math.sin(ang) * 120)
            ctx.line_to(tx + math.cos(ang) * 175, base - 150 + math.sin(ang) * 175)
        src(ctx, ink, 0.35)
        ctx.set_line_width(3)
        ctx.stroke()
        rnd = random.Random(4)
        for i in range(26):
            px = rnd.uniform(580, 1080)
            pb = 500 - math.sin(px * 0.006) * 70 + rnd.uniform(0, 60)
            ellipse(ctx, px, pb - 40, 12, 14)
            ctx.move_to(px - 16, pb)
            ctx.curve_to(px - 18, pb - 30, px + 18, pb - 30, px + 16, pb)
            src(ctx, ink, 0.55)
            ctx.fill()
        years = 33 + int(clamp(t / 6) * 50)
        text(ctx, f"age {years}", 470, 160, 40, ink)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def title_card(ctx, t, title, sub, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    digital_city(ctx, t, 0.6)
    ctx.set_source_rgba(0, 0, 0.05, 0.55)
    ctx.paint()
    text(ctx, title, 640, 320, 72, "#FFF2B8", outline="#1A0E30", olw=10)
    text(ctx, sub, 640, 395, 30, "#7FF0FF", outline="#1A0E30", olw=6)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
