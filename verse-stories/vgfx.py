"""Backgrounds and props for Verse Stories (modern everyday scenes)."""
import math
import random

import cairo

import engine as E
from engine import W, H, PI, clamp, lerp, ellipse, rrect, src, mix, rgb, fill_stroke, sparkle, text
import sgfx as S


def grad(ctx, top, bottom, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgb(0, *rgb(top))
    g.add_color_stop_rgb(1, *rgb(bottom))
    ctx.set_source(g)


def room(ctx, wall, floor, wall2=None, floor_y=600):
    grad(ctx, wall, wall2 or mix(wall, "#000000", 0.15), 0, floor_y)
    ctx.paint()
    ctx.rectangle(0, floor_y, W, H - floor_y)
    src(ctx, floor)
    ctx.fill()
    ctx.rectangle(0, floor_y - 6, W, 8)
    src(ctx, mix(floor, "#000000", 0.3))
    ctx.fill()


def window(ctx, x, y, w, h, sky="#8EC5E8", night=False, rain=0.0, t=0.0):
    rrect(ctx, x, y, w, h, 4)
    src(ctx, "#1A2240" if night else sky)
    ctx.fill()
    if rain > 0:
        ctx.save()
        rrect(ctx, x, y, w, h, 4)
        ctx.clip()
        rnd = random.Random(2)
        for i in range(40):
            rx = x + rnd.uniform(0, w)
            ry = y + (rnd.uniform(0, h) + t * 500) % h
            ctx.move_to(rx, ry)
            ctx.line_to(rx - 3, ry + 12)
        src(ctx, "#B8C8E0", 0.6 * rain)
        ctx.set_line_width(1.4)
        ctx.stroke()
        ctx.restore()
    rrect(ctx, x, y, w, h, 4)
    src(ctx, "#F2EEE4")
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.stroke()


# ---------------------------------------------------------------- scenes
def hallway(ctx, t):
    room(ctx, "#E8E0C8", "#B9B4A8")
    for i in range(16):
        x = i * 82
        rrect(ctx, x + 4, 240, 74, 360, 4)
        fill_stroke(ctx, ["#4A7AB8", "#3E6AA0"][i % 2], "#1E3A60", 3)
        for k in range(3):
            ctx.rectangle(x + 24, 260 + k * 8, 34, 3)
        src(ctx, "#1E3A60")
        ctx.fill()
        rrect(ctx, x + 60, 400, 6, 26, 3)
        src(ctx, "#C9CED6")
        ctx.fill()
    rrect(ctx, 520, 90, 240, 110, 6)
    fill_stroke(ctx, "#FFFFFF", "#8A8A8A", 3)
    text(ctx, "ART SHOW", 640, 140, 30, "#D9483A")
    text(ctx, "FRIDAY", 640, 178, 24, "#3E6AA0")


def breakroom(ctx, t):
    room(ctx, "#D8E2E8", "#8A8478")
    window(ctx, 860, 110, 300, 200, "#A8D0EE")
    rrect(ctx, 60, 420, 520, 30, 4)
    fill_stroke(ctx, "#E8E4DA", "#8A8478", 3)
    ctx.rectangle(70, 450, 500, 150)
    src(ctx, "#6E7E8A")
    ctx.fill()
    rrect(ctx, 100, 330, 90, 90, 8)
    fill_stroke(ctx, "#2A2E36", "#111", 3)
    ellipse(ctx, 145, 360, 14, 14)
    src(ctx, "#D9483A")
    ctx.fill()
    rrect(ctx, 600, 230, 150, 370, 8)
    fill_stroke(ctx, "#E8ECF0", "#8A9AA8", 3)
    ctx.move_to(600, 360)
    ctx.line_to(750, 360)
    src(ctx, "#8A9AA8")
    ctx.stroke()
    # round table
    ellipse(ctx, 980, 520, 160, 26)
    fill_stroke(ctx, "#C9A87A", "#6A5030", 3)
    ctx.rectangle(970, 520, 20, 80)
    src(ctx, "#6A5030")
    ctx.fill()


def soccer(ctx, t):
    grad(ctx, "#7EC0EE", "#D8F0FF", 0, 420)
    ctx.paint()
    ctx.rectangle(0, 400, W, 320)
    src(ctx, "#4E9A3E")
    ctx.fill()
    for i in range(0, W, 160):
        ctx.rectangle(i, 400, 80, 320)
        src(ctx, "#56A646")
        ctx.fill()
    ctx.move_to(0, 520)
    ctx.line_to(W, 520)
    src(ctx, "#FFFFFF", 0.7)
    ctx.set_line_width(4)
    ctx.stroke()
    # goal
    ctx.rectangle(1050, 300, 200, 120)
    src(ctx, "#FFFFFF")
    ctx.set_line_width(8)
    ctx.stroke()
    for i in range(10):
        ctx.move_to(1050 + i * 20, 300)
        ctx.line_to(1050 + i * 20, 420)
    src(ctx, "#FFFFFF", 0.4)
    ctx.set_line_width(1.5)
    ctx.stroke()
    # bleachers
    for r in range(3):
        ctx.rectangle(0, 320 + r * 26, 600, 10)
        src(ctx, "#A8A8B0")
        ctx.fill()


def grocery(ctx, t):
    room(ctx, "#F2EEE4", "#C9C2B4")
    for sx in (40, 900):
        for r in range(4):
            ctx.rectangle(sx, 160 + r * 90, 340, 10)
            src(ctx, "#8A8A8A")
            ctx.fill()
            rnd = random.Random(sx + r)
            for k in range(12):
                rrect(ctx, sx + 6 + k * 28, 160 + r * 90 - 50, 22, 50, 3)
                src(ctx, rnd.choice(["#D9483A", "#E8B64A", "#4A9A5A", "#3E6AA0", "#E87AA4"]))
                ctx.fill()
    # checkout counter
    rrect(ctx, 430, 440, 420, 160, 8)
    fill_stroke(ctx, "#3A4A5A", "#1A2430", 3)
    rrect(ctx, 430, 430, 420, 20, 4)
    src(ctx, "#1A1A1A")
    ctx.fill()
    rrect(ctx, 720, 360, 90, 70, 6)
    fill_stroke(ctx, "#2A2E36", "#111", 3)
    rrect(ctx, 730, 370, 70, 30, 3)
    src(ctx, "#5EE8A8")
    ctx.fill()
    text(ctx, "$20.00", 765, 392, 18, "#0E3A22")


def neighbors(ctx, t, music_on=1.0):
    grad(ctx, "#8EC5E8", "#E8F4FF", 0, 480)
    ctx.paint()
    ctx.rectangle(0, 470, W, 250)
    src(ctx, "#6EAA4E")
    ctx.fill()
    for hx, col, roof in ((240, "#E8D2A8", "#9C4A3A"), (1040, "#B8D0E8", "#3A4A6A")):
        rrect(ctx, hx - 190, 260, 380, 280, 4)
        src(ctx, col)
        ctx.fill()
        ctx.move_to(hx - 215, 270)
        ctx.line_to(hx, 150)
        ctx.line_to(hx + 215, 270)
        ctx.close_path()
        src(ctx, roof)
        ctx.fill()
        rrect(ctx, hx - 30, 400, 60, 140, 4)
        src(ctx, "#5A3A22")
        ctx.fill()
        for wx in (-130, 80):
            rrect(ctx, hx + wx, 320, 60, 60, 3)
            src(ctx, "#F2EEE4")
            ctx.fill()
    # fence between them
    for fx in range(560, 720, 20):
        ctx.move_to(fx, 600)
        ctx.line_to(fx, 500)
        ctx.line_to(fx + 8, 490)
        ctx.line_to(fx + 16, 500)
        ctx.line_to(fx + 16, 600)
        ctx.close_path()
        src(ctx, "#FFFFFF")
        ctx.fill()
    # speaker and music notes
    rrect(ctx, 1180, 480, 60, 90, 6)
    fill_stroke(ctx, "#2A2A2A", "#000", 3)
    ellipse(ctx, 1210, 530, 18, 18)
    src(ctx, "#555")
    ctx.fill()
    if music_on > 0:
        for i in range(4):
            u = (t * 0.7 + i / 4) % 1
            nx, ny = 1180 - u * 260 + math.sin(u * 8) * 14, 470 - u * 160
            ellipse(ctx, nx, ny, 9, 7)
            src(ctx, "#2A2A2A", music_on * (1 - u))
            ctx.fill()
            ctx.move_to(nx + 8, ny)
            ctx.line_to(nx + 8, ny - 30)
            ctx.line_to(nx + 18, ny - 22)
            ctx.set_line_width(3)
            ctx.stroke()


def kitchen(ctx, t):
    room(ctx, "#F2D8A8", "#9C7A54")
    window(ctx, 520, 100, 240, 170, "#F2B26A")
    for cx in range(40, 400, 90):
        rrect(ctx, cx, 120, 80, 120, 4)
        fill_stroke(ctx, "#C9A07A", "#7A5A3A", 3)
    # dinner table
    rrect(ctx, 260, 500, 760, 26, 6)
    fill_stroke(ctx, "#8A5A3A", "#4A2E1A", 3)
    ctx.rectangle(290, 526, 20, 80)
    ctx.rectangle(970, 526, 20, 80)
    src(ctx, "#4A2E1A")
    ctx.fill()
    ellipse(ctx, 640, 494, 60, 12)
    fill_stroke(ctx, "#F2EEE4", "#8A8A8A", 2)
    ellipse(ctx, 400, 494, 34, 9)
    fill_stroke(ctx, "#F2EEE4", "#8A8A8A", 2)
    ellipse(ctx, 880, 494, 34, 9)
    fill_stroke(ctx, "#F2EEE4", "#8A8A8A", 2)


def basement(ctx, t):
    room(ctx, "#C9C2B4", "#7A7468", "#A8A094")
    for i in range(0, W, 90):
        ctx.move_to(i, 0)
        ctx.line_to(i, 594)
        src(ctx, "#B0A898", 0.6)
        ctx.set_line_width(2)
        ctx.stroke()
    rrect(ctx, 480, 70, 320, 90, 6)
    fill_stroke(ctx, "#F2EEE4", "#8A7A5A", 3)
    text(ctx, "Thursday Night Group", 640, 110, 24, "#5A3A22")
    text(ctx, "all are welcome", 640, 142, 18, "#8A6A4A")
    # coffee table
    rrect(ctx, 1040, 430, 200, 18, 4)
    fill_stroke(ctx, "#8A6A4A", "#4A3420", 3)
    for k in range(3):
        rrect(ctx, 1060 + k * 40, 400, 24, 30, 4)
        src(ctx, "#F2EEE4")
        ctx.fill()


def folding_chair(ctx, x, y=600):
    ctx.move_to(x - 26, y)
    ctx.line_to(x - 20, y - 70)
    ctx.move_to(x + 26, y)
    ctx.line_to(x + 20, y - 70)
    src(ctx, "#4A4A52")
    ctx.set_line_width(5)
    ctx.stroke()
    rrect(ctx, x - 28, y - 76, 56, 10, 3)
    src(ctx, "#6A6A74")
    ctx.fill()
    rrect(ctx, x - 24, y - 150, 48, 50, 6)
    src(ctx, "#6A6A74")
    ctx.fill()


def podium(ctx, x):
    ctx.move_to(x - 50, 612)
    ctx.line_to(x - 40, 530)
    ctx.line_to(x + 40, 530)
    ctx.line_to(x + 50, 612)
    ctx.close_path()
    fill_stroke(ctx, "#7A5A3A", "#3A2414", 3)
    rrect(ctx, x - 52, 520, 104, 14, 3)
    src(ctx, "#5A3A22")
    ctx.fill()


def night_street(ctx, t):
    grad(ctx, "#0E1222", "#2A2E40", 0, 600)
    ctx.paint()
    for i, bx in enumerate((80, 330, 900, 1150)):
        h = 300 + (i * 77) % 140
        ctx.rectangle(bx - 120, 600 - h, 240, h)
        src(ctx, "#1A1E2E")
        ctx.fill()
    ctx.rectangle(640, 260, 8, 340)
    src(ctx, "#2A2A2A")
    ctx.fill()
    g = cairo.RadialGradient(644, 270, 0, 644, 400, 300)
    g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.5)
    g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#15161E")
    ctx.fill()
    rnd = random.Random(1)
    for i in range(140):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) + t * 800) % (H + 20) - 20
        ctx.move_to(x, y)
        ctx.line_to(x - 4, y + 16)
    src(ctx, "#8A9AB8", 0.4)
    ctx.set_line_width(1.2)
    ctx.stroke()


def visiting_room(ctx, t):
    room(ctx, "#B8C0B0", "#6E7468", "#9AA090")
    for i in range(0, W, 120):
        ctx.rectangle(i, 0, 4, 594)
        src(ctx, "#8A9080")
        ctx.fill()
    window(ctx, 540, 80, 200, 120, "#A8C8E0")
    for bx in range(550, 740, 24):
        ctx.rectangle(bx, 80, 5, 120)
    src(ctx, "#3A3A3A")
    ctx.fill()
    rrect(ctx, 380, 480, 520, 24, 4)
    fill_stroke(ctx, "#8A8A84", "#3A3A36", 3)
    ctx.rectangle(400, 504, 16, 100)
    ctx.rectangle(864, 504, 16, 100)
    src(ctx, "#3A3A36")
    ctx.fill()


def river(ctx, t):
    grad(ctx, "#8EC5E8", "#F2F2D8", 0, 380)
    ctx.paint()
    g = cairo.RadialGradient(900, 140, 10, 900, 140, 400)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.9)
    g.add_color_stop_rgba(1, 1, 1, 0.85, 0)
    ctx.set_source(g)
    ctx.paint()
    for i in range(9):
        x = i * 160 + 30
        ellipse(ctx, x, 360, 90, 70)
        src(ctx, "#4E8A3E")
        ctx.fill()
    ctx.rectangle(0, 380, W, 340)
    src(ctx, "#6A9A4E")
    ctx.fill()
    ctx.move_to(0, 520)
    ctx.curve_to(400, 480, 900, 560, W, 500)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, "#4A8AC0")
    ctx.fill()
    for k in range(8):
        y = 560 + k * 20
        ctx.move_to(0, y + math.sin(t + k) * 4)
        for x in range(0, W + 40, 40):
            ctx.line_to(x, y + math.sin(t * 1.5 + x * 0.02 + k) * 4)
        src(ctx, "#8EC5E8", 0.3)
        ctx.set_line_width(2)
        ctx.stroke()


def water_front(ctx, t, level=600):
    ctx.rectangle(0, level, W, H - level)
    src(ctx, "#4A8AC0", 0.85)
    ctx.fill()
    ctx.move_to(0, level)
    for x in range(0, W + 40, 40):
        ctx.line_to(x, level + math.sin(t * 2 + x * 0.03) * 4)
    src(ctx, "#B8E0FF")
    ctx.set_line_width(3)
    ctx.stroke()


def hospital(ctx, t, night=True, rain=1.0):
    room(ctx, "#D8E8E4", "#9AB0AC")
    window(ctx, 860, 110, 300, 220, night=night, rain=rain, t=t)
    # bed
    rrect(ctx, 300, 470, 520, 40, 8)
    fill_stroke(ctx, "#F2F6F8", "#8AA0A8", 3)
    ctx.rectangle(310, 510, 20, 90)
    ctx.rectangle(790, 510, 20, 90)
    src(ctx, "#8AA0A8")
    ctx.fill()
    rrect(ctx, 300, 390, 30, 120, 6)
    src(ctx, "#C9D6DA")
    ctx.fill()
    # monitor
    rrect(ctx, 150, 260, 120, 90, 6)
    fill_stroke(ctx, "#1A2228", "#000", 3)
    ctx.move_to(160, 310)
    for i in range(20):
        x = 160 + i * 5
        y = 310 - (18 if (i + int(t * 4)) % 10 == 0 else 0)
        ctx.line_to(x, y)
    src(ctx, "#3BFF9A")
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.rectangle(206, 350, 8, 250)
    src(ctx, "#8AA0A8")
    ctx.fill()


def patient_in_bed(ctx, x, t, c):
    """Draw a lying patient under a blanket at the bed."""
    E.draw_char(ctx, c, t)
    rrect(ctx, x - 40, 440, 400, 50, 16)
    src(ctx, "#8EB8E8")
    ctx.fill()


def hospital_exit(ctx, t):
    grad(ctx, "#8EC5E8", "#F2F8FF", 0, 500)
    ctx.paint()
    rrect(ctx, 220, 120, 840, 480, 6)
    src(ctx, "#E8ECF0")
    ctx.fill()
    text(ctx, "ST. LUKE'S HOSPITAL", 640, 200, 40, "#3E6AA0")
    rrect(ctx, 520, 330, 240, 270, 6)
    src(ctx, "#A8D0EE")
    ctx.fill()
    ctx.move_to(640, 330)
    ctx.line_to(640, 600)
    src(ctx, "#F2EEE4")
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#B9B4A8")
    ctx.fill()
    for i, (bx, col) in enumerate(((330, "#E85E5E"), (360, "#E8C85E"), (300, "#5E9AE8"))):
        ellipse(ctx, bx, 300 + math.sin(t * 2 + i) * 6 - i * 20, 22, 28)
        src(ctx, col)
        ctx.fill()
        ctx.move_to(bx, 328 - i * 20)
        ctx.line_to(330, 470)
        src(ctx, "#5A5A5A")
        ctx.set_line_width(1.5)
        ctx.stroke()


def hidden_room(ctx, t, knock=0.0):
    src(ctx, "#1A120C")
    ctx.paint()
    rnd = random.Random(3)
    for row in range(10):
        for col in range(14):
            rrect(ctx, col * 96 + (48 if row % 2 else 0) + 3, row * 64 + 3, 90, 58, 4)
            src(ctx, mix("#3A2A1E", "#2A1E14", rnd.random()))
            ctx.fill()
    rrect(ctx, 1080, 260, 140, 340, 6)
    fill_stroke(ctx, "#4A3420", "#1A0E06", 4)
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#140E08")
    ctx.fill()
    rrect(ctx, 420, 500, 440, 20, 4)
    fill_stroke(ctx, "#5A3A22", "#2A1A0E", 3)
    for cx in (480, 640, 800):
        ctx.rectangle(cx - 5, 466, 10, 34)
        src(ctx, "#F2EEE4")
        ctx.fill()
        g = cairo.RadialGradient(cx, 456, 0, cx, 456, 220)
        g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.5)
        g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
        ctx.set_source(g)
        ctx.arc(cx, 456, 220, 0, 2 * PI)
        ctx.fill()
        ellipse(ctx, cx, 456, 5, 10 + math.sin(t * 11 + cx) * 1.5)
        src(ctx, "#FFE36A")
        ctx.fill()


def montage_panel(ctx, kind, t):
    if kind == "storm":
        grad(ctx, "#3A4250", "#6A7280", 0, 600)
        ctx.paint()
        ctx.move_to(420, 600)
        ctx.line_to(420, 330)
        ctx.line_to(640, 220)
        ctx.line_to(860, 330)
        ctx.line_to(860, 600)
        ctx.close_path()
        src(ctx, "#8A7A6A")
        ctx.fill()
        ctx.move_to(640, 220)
        ctx.line_to(700, 260)
        ctx.line_to(660, 320)
        ctx.line_to(720, 380)
        src(ctx, "#2A2A2A")
        ctx.set_line_width(4)
        ctx.stroke()
        rrect(ctx, 560, 380, 160, 100, 2)
        src(ctx, "#2A2A2A")
        ctx.fill()
        ctx.rectangle(0, 600, W, 120)
        src(ctx, "#4A5A6A")
        ctx.fill()
        water_front(ctx, t, 640)
    elif kind == "foodbank":
        room(ctx, "#E8DCC0", "#9C8A6A")
        rrect(ctx, 820, 340, 360, 260, 6)
        fill_stroke(ctx, "#C9A87A", "#6A5030", 3)
        text(ctx, "FOOD BANK", 1000, 400, 36, "#5A3A22")
        for k in range(5):
            rrect(ctx, 850 + k * 64, 440, 50, 50, 4)
            src(ctx, "#B9643A")
            ctx.fill()
    else:  # schoolyard
        grad(ctx, "#8EC5E8", "#E8F4FF", 0, 480)
        ctx.paint()
        ctx.rectangle(0, 470, W, 250)
        src(ctx, "#B9A888")
        ctx.fill()
        rrect(ctx, 60, 200, 520, 270, 4)
        src(ctx, "#C96A4A")
        ctx.fill()
        for k in range(4):
            rrect(ctx, 100 + k * 120, 260, 70, 70, 3)
            src(ctx, "#A8D0EE")
            ctx.fill()


def cemetery(ctx, t, dawn=1.0):
    grad(ctx, mix("#2A2E50", "#F2B26A", dawn), mix("#4A4A60", "#FFF2D8", dawn), 0, 520)
    ctx.paint()
    g = cairo.RadialGradient(1000, 470, 10, 1000, 470, 500)
    g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.8 * dawn)
    g.add_color_stop_rgba(1, 1, 0.8, 0.4, 0)
    ctx.set_source(g)
    ctx.paint()
    ctx.move_to(0, 520)
    for x in range(0, W + 80, 80):
        ctx.line_to(x, 510 + math.sin(x * 0.01) * 14)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, mix("#2A3A2A", "#6A9A4E", dawn))
    ctx.fill()
    for i, gx in enumerate((160, 300, 960, 1120)):
        ctx.move_to(gx - 30, 560)
        ctx.line_to(gx - 30, 500)
        ctx.curve_to(gx - 30, 470, gx + 30, 470, gx + 30, 500)
        ctx.line_to(gx + 30, 560)
        ctx.close_path()
        src(ctx, "#8A8A90")
        ctx.fill()
    # the main stone
    ctx.move_to(600, 610)
    ctx.line_to(600, 470)
    ctx.curve_to(600, 420, 720, 420, 720, 470)
    ctx.line_to(720, 610)
    ctx.close_path()
    fill_stroke(ctx, "#B0B0B6", "#5A5A60", 3)
    text(ctx, "RUTH", 660, 500, 22, "#4A4A50")
    text(ctx, "beloved", 660, 530, 16, "#4A4A50")


def flowers(ctx, x, y):
    for k, col in enumerate(("#E85E8C", "#FFE36A", "#E8A85E", "#FFFFFF")):
        ctx.move_to(x, y)
        ctx.line_to(x - 16 + k * 10, y - 30)
        src(ctx, "#3E7A2E")
        ctx.set_line_width(2)
        ctx.stroke()
        ellipse(ctx, x - 16 + k * 10, y - 32, 6, 6)
        src(ctx, col)
        ctx.fill()


def park(ctx, t):
    grad(ctx, "#F2A86A", "#FFE8B8", 0, 480)
    ctx.paint()
    g = cairo.RadialGradient(640, 470, 20, 640, 470, 600)
    g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.8)
    g.add_color_stop_rgba(1, 1, 0.8, 0.5, 0)
    ctx.set_source(g)
    ctx.paint()
    ellipse(ctx, 640, 470, 70, 70)
    src(ctx, "#FFF2C8")
    ctx.fill()
    ctx.rectangle(0, 470, W, 250)
    src(ctx, "#7A9A4E")
    ctx.fill()
    for tx in (80, 1200):
        ctx.rectangle(tx - 10, 300, 20, 180)
        src(ctx, "#5A3A22")
        ctx.fill()
        ellipse(ctx, tx, 290, 90, 80)
        src(ctx, "#4E7A3E")
        ctx.fill()
    # picnic blanket
    ctx.move_to(360, 640)
    ctx.line_to(920, 640)
    ctx.line_to(860, 690)
    ctx.line_to(420, 690)
    ctx.close_path()
    src(ctx, "#D9483A")
    ctx.fill()
    for i in range(6):
        ctx.move_to(420 + i * 90, 640)
        ctx.line_to(440 + i * 80, 690)
    src(ctx, "#FFFFFF", 0.6)
    ctx.set_line_width(6)
    ctx.stroke()


# ---------------------------------------------------------------- props
def paper(ctx, x, y, torn=0.0, a=1.0):
    for side in ((-1, 1) if torn > 0 else (0,)):
        ctx.save()
        ctx.translate(x + side * 20 * torn, y + abs(side) * 20 * torn)
        ctx.rotate(side * 0.4 * torn)
        w = 60 if side == 0 else 30
        ox = -30 if side <= 0 else 0
        rrect(ctx, ox, -40, w, 80, 2)
        src(ctx, "#FFFFFF", a)
        ctx.fill()
        ellipse(ctx, ox + w / 2, -10, 12, 12)
        src(ctx, "#E8B64A", a)
        ctx.fill()
        ctx.move_to(ox + 6, 20)
        ctx.line_to(ox + w - 6, 14)
        src(ctx, "#4A9A5A", a)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.restore()


def ball(ctx, x, y, t, r=16):
    ellipse(ctx, x, y, r, r)
    fill_stroke(ctx, "#FFFFFF", "#1A1A1A", 2)
    star = S  # noqa
    ellipse(ctx, x, y, r * 0.35, r * 0.35)
    src(ctx, "#1A1A1A")
    ctx.fill()


def plate_of_cookies(ctx, x, y):
    ellipse(ctx, x, y, 30, 8)
    fill_stroke(ctx, "#F2EEE4", "#8A8A8A", 2)
    for k in range(4):
        ellipse(ctx, x - 15 + k * 10, y - 6 - (k % 2) * 4, 9, 6)
        src(ctx, "#C9904A")
        ctx.fill()


def money(ctx, x, y):
    rrect(ctx, x - 20, y - 10, 40, 20, 3)
    fill_stroke(ctx, "#8AC87A", "#3E6A2E", 2)
    text(ctx, "20", x, y + 6, 13, "#2E5A22")


def chapter_card(ctx, t, ref, a=1.0):
    S.chapter_card(ctx, t, ref, a)


def blush_glow(ctx, x, y, a, t):
    S.draw_coals(ctx, x, y, a, t)
