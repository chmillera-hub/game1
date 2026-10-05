"""Locations for DO NOT DISTURB (world space 1080 x 1920 at zoom 1)."""
import math
import random
import cairo
from toon.draw import (OUT, LW, TAU, hexc, shade, src, ell, rrect, fs, fill, poly, line, text, star, heart,
                       cloud, lin, radial)
from .style import (PAPER, INK, LAV, LAV_D, HOOD, PINK, RED, COAT, MUST, MUST_D, TEAL, TEAL_L, INDIGO, NIGHT,
                    CORAL, MINT, SLATE, ALARM, CREAM2, shade_fill, mix)
from .cast import thing_body, cage

W, H = 1080, 1920


def rect_fs(c, x, y, w, h, col, lw=LW):
    c.rectangle(x, y, w, h)
    fs(c, col, lw=lw)


def sky(c, x0, x1, y0, y1, night=0):
    top = mix(hexc("#f6a77d"), NIGHT, night)
    bot = mix(hexc("#b9a6d9"), INDIGO, night)
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.set_source(lin(0, y0, 0, y1, [(0, bot), (1, top)]))
    c.fill()


def door_hanger(c, x, y, s=1.0, rot=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.move_to(-40, -60); c.line_to(40, -60); c.line_to(40, 90); c.line_to(-40, 90); c.close_path()
    c.new_sub_path(); c.arc(0, -36, 16, 0, TAU)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fs(c, MUST, lw=4)
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    text(c, "DO NOT", 0, 18, 15, "Bungee", INK)
    text(c, "DISTURB", 0, 42, 12.5, "Bungee", INK)
    c.restore()


def logo(c, x, y, s=1.0, tag=True):
    c.save(); c.translate(x, y); c.scale(s, s)
    ell(c, 0, 0, 46, 46); fs(c, TEAL, lw=5)
    c.move_to(-26, 6); c.curve_to(-12, -10, 12, 18, 26, 2)
    src(c, PAPER); c.set_line_width(7); c.stroke()
    text(c, "CALM CORP", 70, 14, 40, "Bungee", INK, align="left")
    if tag:
        text(c, "FEEL LESS.", 72, 50, 22, "Bungee", TEAL, align="left")
    c.restore()


# ------------------------------------------------------------------------------------- bedroom
def set_room(c, t, P, actors):
    wall = hexc("#48606f")
    # ceiling
    c.rectangle(-300, -400, W + 600, 700); fill(c, shade(wall, 0.75))
    line(c, -300, 300, W + 300, 300, INK, 5)
    ell(c, 540, 300, 70, 18, 0, math.pi); fs(c, PAPER)
    if P.get("crack", 0):
        cx = P.get("crack_x", 540)
        for a in (-2.4, -1.9, -1.2, -0.6, 0.0):
            line(c, cx, 300, cx + math.cos(a + math.pi / 2) * 70, 300 - math.sin(a) * 40 - 4, INK, 4)
        ell(c, cx, 292, 46, 10); fill(c, INK)
    # wall
    c.rectangle(-300, 300, W + 600, 1000); fill(c, wall)
    for x in range(-300, W + 300, 90):
        line(c, x, 300, x, 1300, shade(wall, 0.92), 3)
    # window
    rect_fs(c, 60, 420, 380, 420, PAPER)
    sky(c, 78, 422, 438, 822, P.get("night", 0))
    c.save(); c.rectangle(78, 438, 344, 384); c.clip()
    for (hx, hw, hh) in ((90, 140, 160), (250, 170, 210)):
        poly(c, [(hx, 822), (hx, 822 - hh), (hx + hw / 2, 822 - hh - 60), (hx + hw, 822 - hh), (hx + hw, 822)])
        fill(c, shade(INDIGO, 1.3))
        for k in range(2):
            c.rectangle(hx + 20 + k * (hw - 70), 822 - hh + 40, 30, 36); fill(c, MUST)
    bx = P.get("blur_x", -999)
    if bx > -900:
        for k in range(5):
            ell(c, bx - k * 30, 760, 34 - k * 3, 60); src(c, PINK, 0.8 - k * 0.15); c.fill()
    if P.get("rain", 0):
        for k in range(30):
            rx = 78 + (k * 37) % 344
            ry = 438 + ((t * 900 + k * 73) % 384)
            line(c, rx, ry, rx - 8, ry + 30, MINT, 3)
    c.restore()
    line(c, 250, 438, 250, 822, PAPER, 12)
    line(c, 78, 630, 422, 630, PAPER, 12)
    # posters
    rect_fs(c, 600, 390, 220, 300, CORAL)
    star(c, 710, 500, 60, 26, 5); fs(c, MUST, lw=4)
    text(c, "LEVEL 99", 710, 640, 30, "Bungee", PAPER, INK, 5)
    rect_fs(c, 860, 360, 160, 120, MUST)
    text(c, "GG", 940, 440, 54, "Bungee", INK)
    # closet
    rect_fs(c, 640, 760, 230, 540, shade(wall, 1.25))
    op = P.get("closet", 0)
    if op > 0:
        c.rectangle(650, 770, 210, 520); fill(c, NIGHT)
        for k, col in enumerate((CORAL, MUST, TEAL, PINK, SLATE)):
            rrect(c, 664 + k * 38, 800 + (k % 2) * 20, 34, 220, 8); fs(c, col, lw=3)
        line(c, 650, 800, 860, 800, PAPER, 5)
        clothes = P.get("clothes", 0)
        if clothes:
            rnd = random.Random(int(t * 6))
            for k in range(6):
                x = 700 + rnd.uniform(-160, 160)
                y = 700 - ((t * 400 + k * 90) % 500)
                c.save(); c.translate(x, y); c.rotate(rnd.uniform(-1, 1))
                rrect(c, -30, -16, 60, 32, 8); fs(c, rnd.choice((CORAL, MUST, TEAL, PINK)), lw=3)
                c.restore()
    else:
        line(c, 755, 760, 755, 1300, INK, 4)
        ell(c, 740, 1030, 6, 6); fill(c, INK); ell(c, 770, 1030, 6, 6); fill(c, INK)
    # door (far right)
    dop = P.get("door", 0)
    rect_fs(c, 890, 660, 190, 640, shade(wall, 0.6))
    if dop > 0:
        c.rectangle(900, 670, 170, 620); fill(c, NIGHT)
    c.save(); c.translate(900, 0); c.scale(max(0.08, 1 - dop), 1)
    rect_fs(c, 0, 670, 170, 620, hexc("#c99a6a"))
    rrect(c, 24, 710, 122, 220, 6); src(c, INK); c.set_line_width(4); c.stroke()
    rrect(c, 24, 960, 122, 280, 6); src(c, INK); c.set_line_width(4); c.stroke()
    ell(c, 30, 980, 12, 12); fs(c, MUST, lw=3)
    if dop < 0.6:
        door_hanger(c, 50, 1080, 0.9, math.sin(t * 2) * 0.05)
    c.restore()
    # desk + PC
    rect_fs(c, 30, 1060, 520, 30, hexc("#2b2b3a"))
    for x in (50, 500):
        rect_fs(c, x, 1090, 24, 210, hexc("#2b2b3a"))
    rrect(c, 120, 820, 280, 200, 12); fs(c, NIGHT)
    rrect(c, 136, 836, 248, 168, 6)
    hue = (math.sin(t * 7) + 1) / 2
    c.set_source(lin(0, 836, 0, 1004, [(0, mix(TEAL, CORAL, hue)), (1, mix(INDIGO, TEAL, hue))]))
    c.fill()
    rect_fs(c, 245, 1020, 30, 40, NIGHT)
    rrect(c, 180, 1040, 170, 20, 6); fs(c, SLATE, lw=3)
    if P.get("sweater", 0):
        wig = P.get("wiggle", 0)
        k = 1 + 0.06 * math.sin(t * 25) * wig
        c.save(); c.translate(440 + math.sin(t * 31) * 6 * wig, 1030); c.scale(k, 2 - k)
        ell(c, 0, 0, 80, 48); fs(c, CORAL)
        for j in range(-2, 3):
            line(c, -68, j * 14, 68, j * 14, shade(CORAL, 0.75), 4)
        c.restore()
    if P.get("thing_desk", 0):
        thing_body(c, 440, 1020, 0.7, t)
    # floor
    c.rectangle(-300, 1300, W + 600, 900); fill(c, hexc("#8a6f8f"))
    c.rectangle(-300, 1300, W + 600, 900); shade_fill(c, 0.18)
    line(c, -300, 1300, W + 300, 1300, INK, 5)
    # gaming chair behind the player
    if P.get("chair", 0):
        cx = P.get("chair_x", 540)
        rrect(c, cx - 120, 840, 240, 420, 60); fs(c, NIGHT)
        rrect(c, cx - 80, 880, 160, 300, 40); fs(c, CORAL)
        line(c, cx, 1300, cx, 1420, INK, 14)
        line(c, cx - 90, 1430, cx + 90, 1430, INK, 12)
    actors(0)
    # TV glow from the camera side
    if P.get("tv", 0):
        hue = (math.sin(t * 5) + 1) / 2
        col = mix(TEAL_L, CORAL, hue)
        g = cairo.RadialGradient(540, 2300, 200, 540, 2300, 1500)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.35 * P.get("tv", 0))
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        c.set_source(g); c.paint()
    dust = P.get("dust", 0)
    if dust:
        rnd = random.Random(4)
        for k in range(40):
            x = rnd.uniform(200, 900)
            y = 300 + ((t * 200 * rnd.uniform(0.5, 1.2)) + rnd.uniform(0, 600)) % 1000
            ell(c, x, y, 4, 4); src(c, PAPER, 0.6 * dust); c.fill()


# ------------------------------------------------------------------------------------- house, outside
def trash_can(c, x, y, down=0, t=0):
    c.save(); c.translate(x, y)
    if down:
        c.rotate(-1.4)
    rrect(c, -50, -150, 100, 150, 10); fs(c, SLATE)
    for k in range(3):
        line(c, -34 + k * 34, -140, -34 + k * 34, -10, shade(SLATE, 0.8), 4)
    rrect(c, -58, -168, 116, 22, 8); fs(c, shade(SLATE, 0.9))
    c.restore()
    if down:
        rnd = random.Random(int(x))
        for k in range(6):
            px = x + 60 + k * 30 + rnd.uniform(-10, 10)
            rrect(c, px, y - 20 + rnd.uniform(-10, 10), 30, 18, 4); fs(c, rnd.choice((PAPER, MUST, CORAL)), lw=3)


def street_lamp(c, x, y, broken=0, t=0, night=0):
    line(c, x, y, x, y - 560, INK, 16)
    line(c, x, y - 560, x + 90, y - 560, INK, 12)
    if broken:
        poly(c, [(x + 60, y - 554), (x + 120, y - 554), (x + 112, y - 520), (x + 96, y - 534), (x + 82, y - 516),
                 (x + 68, y - 532)])
        fs(c, SLATE, lw=3)
        for k in range(5):
            ell(c, x + 50 + k * 22, y - 6, 6, 3); fill(c, MINT)
    else:
        rrect(c, x + 60, y - 554, 60, 40, 10); fs(c, MUST if night else PAPER, lw=4)
        if night:
            c.set_source(radial(x + 90, y - 500, 300, (1, 0.85, 0.5, 0.35), (1, 0.85, 0.5, 0)))
            c.arc(x + 90, y - 500, 300, 0, TAU); c.fill()


def van(c, x, y):
    c.save(); c.translate(x, y)
    rrect(c, -190, -200, 380, 170, 20); fs(c, NIGHT)
    poly(c, [(110, -200), (170, -200), (200, -120), (200, -60), (110, -60)]); fs(c, NIGHT)
    poly(c, [(120, -190), (165, -190), (190, -125), (120, -125)]); fs(c, SLATE, lw=3)
    logo_ = True
    ell(c, -60, -120, 26, 26); fs(c, TEAL, lw=3)
    for wx in (-120, 120):
        ell(c, wx, -26, 34, 34); fs(c, INK); ell(c, wx, -26, 14, 14); fill(c, SLATE)
    c.restore()


def set_house(c, t, P, actors):
    night = P.get("night", 0)
    sky(c, -500, W + 500, -500, 1400, night)
    ell(c, 820, 360, 70, 70); src(c, MUST if not night else PAPER, 0.85); c.fill()
    # house
    poly(c, [(110, 600), (540, 300), (970, 600)]); fs(c, INDIGO)
    rect_fs(c, 140, 600, 800, 800, hexc("#d9cfb8"))
    for y in range(630, 1400, 34):
        line(c, 145, y, 935, y, shade(hexc("#d9cfb8"), 0.88), 3)
    c.rectangle(140, 600, 800, 800); c.set_source(lin(140, 0, 940, 0, [(0, (0, 0, 0, 0)), (1, (0, 0, 0, 0))])); c.fill()
    c.rectangle(700, 600, 240, 800); shade_fill(c, 0.25)
    # upstairs window = Tiredness's room
    rect_fs(c, 600, 700, 220, 200, PAPER)
    c.rectangle(614, 714, 192, 172); fill(c, mix(TEAL, NIGHT, 0.3))
    hue = (math.sin(t * 7) + 1) / 2
    c.rectangle(614, 714, 192, 172); src(c, mix(TEAL_L, CORAL, hue), 0.35); c.fill()
    ell(c, 700, 860, 46, 40); fill(c, shade(LAV, 0.7))  # silhouette
    line(c, 710, 714, 710, 886, PAPER, 8)
    rect_fs(c, 230, 700, 220, 200, PAPER)
    c.rectangle(244, 714, 192, 172); fill(c, shade(INDIGO, 1.6))
    # downstairs window
    rect_fs(c, 200, 1050, 200, 200, PAPER)
    c.rectangle(214, 1064, 172, 172); fill(c, shade(INDIGO, 1.6))
    # front door with gap
    rect_fs(c, 470, 1080, 160, 320, CORAL)
    rrect(c, 494, 1110, 112, 110, 6); src(c, INK); c.set_line_width(4); c.stroke()
    ell(c, 604, 1260, 10, 10); fs(c, MUST, lw=3)
    c.rectangle(476, 1384, 148, 14); fill(c, NIGHT)
    rect_fs(c, 440, 1396, 220, 18, SLATE)
    # bushes
    for bx in (170, 900):
        for k in range(3):
            ell(c, bx + (k - 1) * 50, 1360 - (k % 2) * 30, 70, 55); fs(c, hexc("#3f8c6a"))
    # sidewalk + street
    c.rectangle(-500, 1410, W + 1000, 120); fs(c, CREAM2)
    for x in range(-500, W + 500, 160):
        line(c, x, 1410, x, 1530, shade(CREAM2, 0.8), 3)
    c.rectangle(-500, 1530, W + 1000, 600); fill(c, hexc("#3b3a52"))
    for x in range(-500, W + 500, 220):
        rrect(c, x, 1730, 110, 16, 6); fill(c, MUST)
    trash_can(c, 1000 if not P.get("cans_down", 0) else 980, 1500, P.get("cans_down", 0), t)
    trash_can(c, 1080, 1510, P.get("cans_down", 0), t)
    street_lamp(c, 60, 1500, P.get("lamp_broken", 0), t, night)
    if P.get("debris", 0):
        rnd = random.Random(8)
        for k in range(26):
            x, y = rnd.uniform(-200, 1200), rnd.uniform(1430, 1900)
            c.save(); c.translate(x, y); c.rotate(rnd.uniform(0, 3))
            rrect(c, -14, -8, 28, 16, 3); fs(c, rnd.choice((PAPER, MUST, CORAL, MINT)), lw=2)
            c.restore()
    if P.get("vans", 0):
        for vx in (-120, 380, 900):
            van(c, vx, 1760)
    if night:
        c.rectangle(-500, -500, W + 1000, 2600); src(c, NIGHT, 0.35 * night); c.fill()
    actors(0)


# ------------------------------------------------------------------------------------- house, side wall
def set_side(c, t, P, actors):
    sky(c, -800, 2600, -400, 1400, 0)
    c.rectangle(-800, 380, 3400, 1040); fill(c, hexc("#d9cfb8"))
    for y in range(400, 1420, 34):
        line(c, -800, y, 2600, y, shade(hexc("#d9cfb8"), 0.88), 3)
    poly(c, [(-800, 380), (2600, 380), (2600, 300), (-800, 300)]); fs(c, INDIGO)
    for i, wx in enumerate((-300, 450, 1200, 1950)):
        rect_fs(c, wx, 820, 260, 280, PAPER)
        c.rectangle(wx + 14, 834, 232, 252); fill(c, shade(INDIGO, 1.6))
        line(c, wx + 14, 960, wx + 246, 960, PAPER, 10)
        if i == P.get("broken_i", 99):
            c.rectangle(wx + 14, 960, 232, 126); fill(c, NIGHT)
            rnd = random.Random(3)
            pts = [(wx + 14, 960)]
            for k in range(10):
                pts.append((wx + 30 + k * 22, 990 + rnd.uniform(-20, 40)))
            pts += [(wx + 246, 960)]
            poly(c, pts + [(wx + 246, 1086), (wx + 14, 1086)]); fill(c, NIGHT)
        if i == P.get("label_i", 99):
            text(c, P.get("label", ""), wx + 130, 800, 26, "Bungee", INK)
    for bx in range(-700, 2600, 260):
        ell(c, bx, 1380, 90, 60); fs(c, hexc("#3f8c6a"))
    c.rectangle(-800, 1410, 3400, 800); fill(c, hexc("#6e9a5e"))
    c.rectangle(-800, 1410, 3400, 800); shade_fill(c, 0.18)
    line(c, -800, 1410, 2600, 1410, INK, 5)
    if P.get("shards", 0):
        rnd = random.Random(5)
        bx = P.get("shards_x", 1330)
        for k in range(14):
            x = bx + rnd.uniform(-160, 160)
            y = 1420 + rnd.uniform(0, 60)
            poly(c, [(x, y), (x + 10, y - 14), (x + 18, y + 4)]); fs(c, MINT, lw=2)
    actors(0)


# ------------------------------------------------------------------------------------- downstairs (kitchen + stairs)
STAIR_BOTTOM = (760, 1400)
STAIR_TOP = (1500, 600)


def set_kitchen(c, t, P, actors):
    wall = hexc("#e2c99c")
    c.rectangle(-700, -300, 2500, 1700); fill(c, wall)
    for x in range(-700, 1800, 60):
        line(c, x, -300, x, 1400, shade(wall, 0.95), 2)
    # broken window (left)
    rect_fs(c, -420, 520, 320, 340, PAPER)
    sky(c, -406, -114, 534, 846, 0)
    if P.get("broken", 1):
        rnd = random.Random(11)
        pts = []
        for k in range(14):
            a = TAU * k / 14
            r = rnd.uniform(70, 130)
            pts.append((-260 + math.cos(a) * r, 690 + math.sin(a) * r))
        poly(c, pts); fill(c, hexc("#f6a77d"))
        for k in range(8):
            a = TAU * k / 8
            line(c, -260 + math.cos(a) * 120, 690 + math.sin(a) * 120, -260 + math.cos(a) * 160,
                 690 + math.sin(a) * 160, PAPER, 3)
    line(c, -260, 534, -260, 846, PAPER, 10)
    # upper cabinets
    for k in range(3):
        rect_fs(c, -60 + k * 150, 380, 140, 220, hexc("#8fb6a6"))
        ell(c, -60 + k * 150 + 120, 580, 6, 6); fill(c, INK)
    # counter + drawers
    rect_fs(c, -700, 1060, 1100, 40, CREAM2)
    for k in range(5):
        x = -680 + k * 216
        rect_fs(c, x, 1100, 200, 300, hexc("#8fb6a6"))
        dop = P.get("drawer", 0) if k == P.get("drawer_i", 3) else 0
        rect_fs(c, x + 14 - dop * 0, 1120 + dop * 30, 172, 80 + dop * 20, shade(hexc("#8fb6a6"), 1.15), lw=4)
        line(c, x + 80, 1160 + dop * 40, x + 120, 1160 + dop * 40, INK, 6)
    # plates on the counter
    for k in range(3):
        if k == P.get("plate_up_i", -1):
            yy = 1050 - P.get("plate_up", 0) * 120
        else:
            yy = 1050
        ell(c, 150 + k * 70, yy, 46, 14); fs(c, PAPER, lw=4)
    # fridge
    rect_fs(c, -680, 560, 220, 500, PAPER)
    line(c, -680, 760, -460, 760, INK, 4)
    line(c, -490, 620, -490, 720, INK, 6)
    # dining table
    rect_fs(c, 260, 1200, 440, 30, hexc("#a8703f"))
    for x in (280, 660):
        rect_fs(c, x, 1230, 22, 170, hexc("#a8703f"))
    # stairs
    bx, by = STAIR_BOTTOM
    tx, ty = STAIR_TOP
    n = 12
    poly(c, [(bx, by), (tx, ty), (1800, ty), (1800, by)]); fill(c, shade(wall, 0.85))
    for k in range(n):
        u0 = k / n
        x0 = bx + (tx - bx) * u0
        y0 = by + (ty - by) * u0
        x1 = bx + (tx - bx) * (k + 1) / n
        y1 = by + (ty - by) * (k + 1) / n
        poly(c, [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]); fs(c, hexc("#a8703f"), lw=3)
    line(c, bx - 20, by - 240, tx - 20, ty - 240, INK, 10)
    for k in range(0, n + 1, 2):
        x = bx + (tx - bx) * k / n
        y = by + (ty - by) * k / n
        line(c, x - 20, y, x - 20, y - 240, INK, 5)
    # landing + Tiredness's door at the top
    c.rectangle(tx, ty - 520, 400, 520); fill(c, shade(wall, 0.9))
    rect_fs(c, tx + 60, ty - 470, 200, 470, hexc("#c99a6a"))
    door_hanger(c, tx + 100, ty - 220, 0.8)
    c.rectangle(tx + 66, ty - 14, 188, 12); fill(c, TEAL_L)
    # creeping shadow on the stair wall
    sh = P.get("shadow", -1)
    if sh >= 0:
        sx = bx + (tx - bx) * sh + 60
        sy = by + (ty - by) * sh - 330
        c.save(); c.translate(sx, sy); c.rotate(-0.8)
        n2 = 24
        rnd = random.Random(int(t * 15))
        for i in range(n2 + 1):
            a = TAU * i / n2
            r = 1 + 0.25 * math.sin(a * 6 + t * 10) + rnd.uniform(0, 0.15)
            (c.move_to if i == 0 else c.line_to)(math.cos(a) * 150 * r, math.sin(a) * 60 * r)
        c.close_path(); src(c, NIGHT, 0.55); c.fill()
        for k in range(6):
            a = t * 20 + k
            line(c, -100 + k * 40, 40, -120 + k * 40 + math.sin(a) * 20, 110, (0.11, 0.11, 0.24, 0.55), 8)
        c.restore()
    # floor
    c.rectangle(-700, 1400, 2500, 800); fill(c, hexc("#b5835a"))
    for x in range(-700, 1800, 120):
        line(c, x, 1400, x - 80, 2200, shade(hexc("#b5835a"), 0.85), 3)
    line(c, -700, 1400, 1800, 1400, INK, 5)
    if P.get("glass", 1):
        rnd = random.Random(6)
        for k in range(12):
            x = -300 + rnd.uniform(-120, 200)
            y = 1420 + rnd.uniform(0, 80)
            poly(c, [(x, y), (x + 12, y - 16), (x + 22, y + 4)]); fs(c, MINT, lw=2)
    actors(0)


# ------------------------------------------------------------------------------------- Calm Corp
def corp_wall(c, x0, x1, y0, y1, col=hexc("#e3ece6")):
    c.rectangle(x0, y0, x1 - x0, y1 - y0); fill(c, col)
    for x in range(int(x0), int(x1), 180):
        line(c, x, y0, x, y1, shade(col, 0.94), 3)


def set_office(c, t, P, actors):
    corp_wall(c, -400, W + 400, -400, 1350)
    # window: night city
    rect_fs(c, 140, 260, 800, 560, INK)
    c.rectangle(156, 276, 768, 528); c.set_source(lin(0, 276, 0, 804, [(0, NIGHT), (1, INDIGO)])); c.fill()
    rnd = random.Random(2)
    c.save(); c.rectangle(156, 276, 768, 528); c.clip()
    ell(c, 820, 360, 40, 40); fill(c, PAPER)
    x = 156
    while x < 924:
        w_ = rnd.uniform(60, 120); h_ = rnd.uniform(160, 420)
        c.rectangle(x, 804 - h_, w_, h_); fill(c, shade(NIGHT, 1.4))
        for wy in range(int(804 - h_ + 20), 800, 34):
            for wx in range(int(x + 10), int(x + w_ - 14), 24):
                if rnd.random() < 0.4:
                    c.rectangle(wx, wy, 10, 14); fill(c, MUST)
        x += w_ + 6
    c.restore()
    logo(c, 330, 940, 1.0)
    c.rectangle(-400, 1350, W + 800, 800); fill(c, hexc("#c5d3cc"))
    line(c, -400, 1350, W + 400, 1350, INK, 5)
    actors(0)
    # desk (in front of whoever stands behind it)
    rect_fs(c, 140, 1150, 800, 60, hexc("#2b2b3a"))
    rect_fs(c, 180, 1210, 720, 190, shade(hexc("#2b2b3a"), 1.3))
    rect_fs(c, 600, 1090, 120, 60, PAPER)
    if P.get("tinychair", 0):
        cx = P.get("chair_x", 540)
        rect_fs(c, cx - 50, 1560, 100, 16, CORAL, lw=4)
        for dx in (-40, 36):
            line(c, cx + dx, 1576, cx + dx, 1640, INK, 6)
        rect_fs(c, cx - 50, 1500, 14, 60, CORAL, lw=4)
    actors(1)


def set_lobby(c, t, P, actors):
    corp_wall(c, -600, 1700, -400, 1350, hexc("#eef2ee"))
    logo(c, 250, 470, 1.6)
    # elevator
    rect_fs(c, 820, 700, 260, 650, SLATE)
    line(c, 950, 700, 950, 1350, INK, 5)
    # plants
    for px in (-200, 1400):
        rect_fs(c, px - 50, 1240, 100, 110, CORAL)
        for k in range(5):
            ell(c, px + (k - 2) * 26, 1170 - (k % 2) * 40, 26, 70); fs(c, hexc("#3f8c6a"))
    c.rectangle(-600, 1350, 2300, 800); fill(c, hexc("#d5ddd8"))
    for x in range(-600, 1700, 200):
        line(c, x, 1350, x - 100, 2150, shade(hexc("#d5ddd8"), 0.9), 3)
    line(c, -600, 1350, 1700, 1350, INK, 5)
    actors(0)
    # reception desk in front of the receptionist
    rect_fs(c, 20, 1180, 460, 280, TEAL)
    rect_fs(c, 0, 1160, 500, 30, PAPER)
    text(c, "RECEPTION", 250, 1300, 36, "Bungee", PAPER)
    # security gate
    gx = P.get("gate_x", 700)
    for k in range(2):
        rect_fs(c, gx + k * 200, 1260, 40, 200, SLATE)
    op = P.get("gate", 0)
    c.save(); c.translate(gx + 40, 1330); c.rotate(-op * 1.4)
    rect_fs(c, 0, -8, 160, 16, ALARM if op < 0.5 else MINT, lw=3)
    c.restore()
    actors(1)


def set_lab(c, t, P, actors):
    corp_wall(c, -400, W + 400, -400, 1350, hexc("#dfe8e4"))
    # monitors
    lines_ = P.get("screen", [])
    rect_fs(c, 560, 360, 470, 420, NIGHT)
    c.rectangle(578, 378, 434, 384); fill(c, hexc("#13324a"))
    y = 420
    for ln in lines_:
        text(c, ln, 596, y, 26, "Special Elite", TEAL_L, align="left")
        y += 40
    if P.get("sketch", 0):
        thing_body(c, 900, 690, 0.9, t)
        ell(c, 900, 690, 90, 60); src(c, TEAL_L); c.set_line_width(2); c.set_dash([8, 6]); c.stroke(); c.set_dash([])
    # containment tank
    tx = P.get("tank_x", 250)
    rect_fs(c, tx - 150, 1220, 300, 80, SLATE)
    rect_fs(c, tx - 150, 380, 300, 50, SLATE)
    c.rectangle(tx - 130, 430, 260, 790); src(c, MINT, 0.45); c.fill()
    c.rectangle(tx - 130, 430, 260, 790); src(c, INK); c.set_line_width(5); c.stroke()
    for k in range(3):
        line(c, tx - 100 + k * 30, 470, tx - 120 + k * 30, 650, PAPER, 6)
    if P.get("cracked", 1):
        for a in (0.3, 1.1, 2.0, 2.9, 4.0, 5.2):
            line(c, tx + 20, 820, tx + 20 + math.cos(a) * 110, 820 + math.sin(a) * 150, INK, 3)
        c.rectangle(tx - 40, 760, 120, 140); fill(c, hexc("#dfe8e4"))
    rect_fs(c, tx - 120, 1250, 240, 40, MUST, lw=3)
    text(c, P.get("tank_label", "SUBJECT 7: ESCAPED"), tx, 1280, 22, "Bungee", INK)
    # console with the big red button
    rect_fs(c, 560, 1120, 470, 230, SLATE)
    for k in range(6):
        ell(c, 600 + k * 40, 1170, 10, 10); fill(c, (TEAL_L, MUST, CORAL)[k % 3])
    bx = P.get("button_x", 900)
    ell(c, bx, 1160, 46, 22); fs(c, shade(ALARM, 0.6))
    ell(c, bx, 1150 + P.get("pressed", 0) * 8, 40, 20); fs(c, ALARM)
    c.rectangle(-400, 1350, W + 800, 800); fill(c, hexc("#c9d4cf"))
    for k in range(-6, 12):
        poly(c, [(k * 120, 1350), (k * 120 + 60, 1350), (k * 120 + 20, 1390), (k * 120 - 40, 1390)])
        fill(c, MUST if k % 2 else INK)
    line(c, -400, 1350, W + 400, 1350, INK, 5)
    actors(0)
    alarm_overlay(c, t, P)


def alarm_overlay(c, t, P):
    if P.get("alarm", 0):
        k = (math.sin(t * 12) + 1) / 2
        c.rectangle(-2000, -2000, 6000, 6000); src(c, ALARM, 0.12 + 0.22 * k); c.fill()
        for bx in P.get("beacons", [120, 960]):
            ang = t * 7
            c.save(); c.translate(bx, 300)
            poly(c, [(0, 0), (math.cos(ang) * 800, math.sin(ang) * 400 + 200),
                     (math.cos(ang + 0.4) * 800, math.sin(ang + 0.4) * 400 + 200)])
            src(c, ALARM, 0.25); c.fill()
            ell(c, 0, 0, 30, 24); fs(c, ALARM)
            c.restore()


def set_hall(c, t, P, actors):
    corp_wall(c, -1200, 3000, -400, 1350, hexc("#e3ece6"))
    for k in range(-2, 10):
        dx = k * 380
        rect_fs(c, dx, 760, 200, 590, SLATE)
        rect_fs(c, dx + 30, 690, 140, 44, PAPER, lw=3)
        text(c, f"LAB {k + 11}", dx + 100, 724, 22, "Bungee", INK)
    # window at the far end
    wx = P.get("window_x", 2600)
    rect_fs(c, wx, 420, 360, 760, INK)
    c.rectangle(wx + 16, 436, 328, 728); c.set_source(lin(0, 436, 0, 1164, [(0, NIGHT), (1, INDIGO)])); c.fill()
    if P.get("smashed", 0):
        c.rectangle(wx + 16, 436, 328, 728); fill(c, NIGHT)
        rnd = random.Random(9)
        for k in range(16):
            a = rnd.uniform(0, TAU)
            r = rnd.uniform(30, 240) + (t - P.get("smash_t", 0)) * 300
            x, y = wx + 180 + math.cos(a) * r, 800 + math.sin(a) * r * 0.7
            poly(c, [(x, y), (x + 18, y - 22), (x + 30, y + 8)]); fs(c, MINT, lw=2)
    c.rectangle(-1200, 1350, 4200, 800); fill(c, hexc("#c5d3cc"))
    line(c, -1200, 1350, 3000, 1350, INK, 5)
    actors(0)
    alarm_overlay(c, t, dict(P, beacons=[P.get("cam_x", 540) - 400, P.get("cam_x", 540) + 400]))


def set_fall(c, t, P, actors):
    c.rectangle(-600, -6000, 2300, 8500); c.set_source(lin(0, -6000, 0, 1700, [(0, NIGHT), (1, INDIGO)])); c.fill()
    rnd = random.Random(1)
    for k in range(120):
        ell(c, rnd.uniform(-500, 1600), rnd.uniform(-6000, 1200), 2, 2); src(c, PAPER, 0.6); c.fill()
    # building facade
    c.rectangle(160, -6000, 760, 7700); fill(c, hexc("#3c4a6a"))
    for y in range(-5900, 1500, 200):
        for x in (210, 420, 630, 820):
            rect_fs(c, x, y, 70, 120, MUST if rnd.random() < 0.35 else shade(NIGHT, 1.3), lw=3)
    c.rectangle(640, -6000, 280, 7700); shade_fill(c, 0.2)
    sx, sy = P.get("shatter_x", 540), P.get("shatter_y", -5600)
    if P.get("shatter", 0):
        age = t - P.get("shatter_t", 0)
        rnd2 = random.Random(3)
        for k in range(24):
            a = rnd2.uniform(-math.pi, 0.3)
            v = rnd2.uniform(200, 500)
            x = sx + math.cos(a) * v * age
            y = sy + math.sin(a) * v * age + 400 * age * age
            poly(c, [(x, y), (x + 16, y - 20), (x + 26, y + 6)]); fs(c, MINT, lw=2)
    # ground
    c.rectangle(-600, 1600, 2300, 600); fill(c, hexc("#2e2e40"))
    line(c, -600, 1600, 1700, 1600, INK, 5)
    ell(c, 540, 1660, 120, 26); fs(c, SLATE)
    for k in range(-3, 4):
        line(c, 540 + k * 30, 1640, 540 + k * 30, 1680, INK, 3)
    actors(0)


# ------------------------------------------------------------------------------------- sewers
def set_sewer(c, t, P, actors):
    brick = hexc("#3e4a5c")
    c.rectangle(-1500, -500, 4500, 3000); fill(c, NIGHT)
    for (cx_, w_) in P.get("arches", [(540, 900)]):
        ell(c, cx_, 1100, w_ / 2, 760, math.pi, TAU); c.line_to(cx_ + w_ / 2, 1900); c.line_to(cx_ - w_ / 2, 1900)
        c.close_path(); fs(c, brick)
        c.save(); ell(c, cx_, 1100, w_ / 2, 760, math.pi, TAU); c.line_to(cx_ + w_ / 2, 1900)
        c.line_to(cx_ - w_ / 2, 1900); c.close_path(); c.clip()
        for y in range(300, 1900, 50):
            off = 0 if (y // 50) % 2 else 50
            line(c, cx_ - w_, y, cx_ + w_, y, shade(brick, 0.8), 3)
            for x in range(int(cx_ - w_) + off, int(cx_ + w_), 100):
                line(c, x, y, x, y + 50, shade(brick, 0.8), 3)
        ell(c, cx_, 1150, w_ * 0.32, 520, math.pi, TAU); c.line_to(cx_ + w_ * 0.32, 1900)
        c.line_to(cx_ - w_ * 0.32, 1900); c.close_path(); fill(c, NIGHT)
        c.restore()
    # pipes
    for (px, py) in ((-200, 700), (1300, 640)):
        line(c, px, py, px + 400, py + 60, INK, 46); line(c, px, py, px + 400, py + 60, SLATE, 34)
    # ledges + water
    c.rectangle(-1500, 1450, 4500, 120); fs(c, hexc("#5a6577"))
    c.rectangle(-1500, 1570, 4500, 400); fill(c, hexc("#2c4a4a"))
    for k in range(14):
        y = 1610 + k * 22
        x = (t * 80 + k * 140) % 400
        for xx in range(-1500 + int(x), 3000, 400):
            line(c, xx, y, xx + 60, y, TEAL, 3)
    # sign at a junction
    if P.get("sign", 0):
        rect_fs(c, P.get("sign_x", 760) - 90, 980, 180, 90, MUST)
        text(c, "EXIT?", P.get("sign_x", 760), 1040, 34, "Bungee", INK)
    # drips
    for k, dx in enumerate((200, 640, 980)):
        ph = (t * 0.8 + k * 0.37) % 1
        ell(c, dx, 500 + ph * 1000, 5, 9); src(c, TEAL_L, 0.7); c.fill()
    actors(0)
    # eyes in the dark
    ea = P.get("eyes", 0)
    if ea:
        for k, (ex, ey) in enumerate(((140, 1180), (900, 1040), (420, 860))):
            on = (math.sin(t * 1.5 + k * 2.1) > 0.2)
            if on:
                for sd in (-1, 1):
                    ell(c, ex + sd * 16, ey, 8, 5); src(c, TEAL_L, ea); c.fill()
    # darkness + flashlight-ish vignette
    g = cairo.RadialGradient(P.get("light_x", 540), P.get("light_y", 1150), 200, P.get("light_x", 540),
                             P.get("light_y", 1150), 900)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, NIGHT[0] * 0.5, NIGHT[1] * 0.5, NIGHT[2] * 0.5, 0.85)
    c.set_source(g); c.rectangle(-1500, -500, 4500, 3000); c.fill()
    sense = P.get("sense", 0)
    if sense:
        sx, sy = P.get("sense_x", 540), P.get("sense_y", 1150)
        for k in range(4):
            r = ((t * 400 + k * 220) % 900)
            ell(c, sx, sy, r, r * 0.8)
            src(c, TEAL_L, sense * (1 - r / 900) * 0.7); c.set_line_width(5); c.stroke()


def set_shaft(c, t, P, actors):
    c.rectangle(-1500, -3000, 4000, 7000); fill(c, NIGHT)
    # light from above
    poly(c, [(380, -3000), (700, -3000), (1000, 2600), (80, 2600)])
    c.set_source(lin(0, -3000, 0, 2600, [(0, (1, 1, 0.9, 0.25)), (1, (1, 1, 0.9, 0.0))])); c.fill()
    # walls with pods, receding rings
    for ring in range(9):
        y = -900 + ring * 330
        sc = 1.0 - ring * 0.06
        span = 1700 * sc
        ell(c, 540, y + 230, span / 2, 70 * sc, 0, math.pi); src(c, SLATE, 0.9); c.set_line_width(10 * sc); c.stroke()
        n = 9
        for k in range(n):
            u = (k + 0.5) / n
            px = 540 - span / 2 + span * u
            py = y + 120 + math.sin(u * math.pi) * 70 * sc
            pw, ph = 70 * sc, 170 * sc
            glow = 0.5 + 0.5 * math.sin(t * 1.5 + k + ring)
            g = cairo.RadialGradient(px, py, 0, px, py, ph)
            g.add_color_stop_rgba(0, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0.25 + 0.15 * glow)
            g.add_color_stop_rgba(1, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0)
            c.set_source(g); c.arc(px, py, ph, 0, TAU); c.fill()
            rrect(c, px - pw / 2, py - ph / 2, pw, ph, pw / 2); src(c, MINT, 0.35); c.fill_preserve()
            src(c, INK); c.set_line_width(3 * sc); c.stroke()
            ell(c, px, py + ph * 0.08, pw * 0.3, pw * 0.26); fill(c, NIGHT)
            for sd in (-1, 1):
                ell(c, px + sd * pw * 0.11, py + ph * 0.04, pw * 0.05, pw * 0.02); src(c, TEAL_L, 0.6); c.fill()
            line(c, px, py - ph / 2, px, py - ph / 2 - 40 * sc, INK, 4 * sc)
    # banner
    rect_fs(c, 220, -1200, 640, 120, PAPER)
    text(c, P.get("banner", "HARVEST ARRAY"), 540, -1125, 52, "Bungee", INK)
    logo(c, 330, -1300, 1.2)
    # foreground ledge
    c.rectangle(-500, 1500, 2100, 800); fill(c, hexc("#2e2e40"))
    c.rectangle(-500, 1500, 2100, 30); fill(c, MUST)
    for k in range(-8, 16):
        poly(c, [(k * 90, 1500), (k * 90 + 45, 1500), (k * 90 + 25, 1530), (k * 90 - 20, 1530)]); fill(c, INK)
    actors(0)


# ------------------------------------------------------------------------------------- inserts and cards
def set_screen(c, t, P, actors):
    c.rectangle(-300, -300, W + 600, H + 600); fill(c, NIGHT)
    rect_fs(c, 40, 400, 1000, 1000, hexc("#f4f1ea"))
    c.rectangle(40, 400, 1000, 70); fill(c, SLATE)
    for k, col in enumerate((ALARM, MUST, MINT)):
        ell(c, 80 + k * 36, 435, 11, 11); fill(c, col)
    rrect(c, 80, 500, 920, 70, 35); fs(c, PAPER, lw=3)
    q = P.get("query", "")
    n = int(min(len(q), max(0, (t - 0.2) * 18)))
    text(c, q[:n] + ("|" if (t * 2) % 1 < 0.5 else ""), 120, 548, 34, "Fredoka", INK, align="left")
    y = 640
    for k, (title, body) in enumerate(P.get("results", [])):
        if t > 1.0 + k * 0.5:
            text(c, title, 90, y, 34, "Fredoka", hexc("#2a5fb0"), align="left")
            text(c, body, 90, y + 44, 26, "Fredoka", SLATE, align="left", bold=False)
            y += 150
    actors(0)


def set_black(c, t, P, actors):
    c.rectangle(-500, -500, W + 1000, H + 1000); fill(c, (0, 0, 0))
    actors(0)


def set_card2(c, t, P, actors):
    kind = P.get("card", "title")
    c.rectangle(-100, -100, W + 200, H + 200); fill(c, PAPER)
    c.rectangle(-100, -100, W + 200, H + 200); shade_fill(c, 0.12)
    if kind == "title":
        sw = math.sin(t * 2.2) * 0.08 * math.exp(-t * 0.6)
        door = hexc("#c99a6a")
        rect_fs(c, 290, 260, 500, 1400, door)
        rrect(c, 330, 320, 420, 500, 10); src(c, INK); c.set_line_width(5); c.stroke()
        rrect(c, 330, 880, 420, 700, 10); src(c, INK); c.set_line_width(5); c.stroke()
        ell(c, 330, 900, 22, 22); fs(c, MUST, lw=4)
        c.save(); c.translate(330, 900); c.rotate(sw)
        c.move_to(-120, 40); c.line_to(120, 40); c.line_to(120, 560); c.line_to(-120, 560); c.close_path()
        c.new_sub_path(); c.arc(0, 0, 0, 0, TAU)
        fs(c, MUST, lw=6)
        ell(c, 0, 0, 34, 34); src(c, INK); c.set_line_width(6); c.stroke()
        text(c, "DO NOT", 0, 180, 46, "Bungee", INK)
        text(c, "DISTURB", 0, 245, 38, "Bungee", INK)
        line(c, -80, 300, 80, 300, INK, 4)
        text(c, "zzz", 0, 380, 44, "Bungee", CORAL)
        c.restore()
        a = min(1.0, max(0.0, (t - 0.4) / 0.4))
        rrect(c, 340, 1690, 400, 80, 40); src(c, INK, a); c.fill()
        text(c, P.get("part", "PART 1"), 540, 1748, 46, "Bungee", MUST, alpha=a)
        text(c, P.get("subtitle", ""), 540, 1860, 54, "Bungee", INK, alpha=a)
    elif kind == "tbc":
        a = min(1.0, t / 0.4)
        door_hanger(c, 540, 600, 3.2, math.sin(t * 2) * 0.06)
        text(c, "TO BE CONTINUED", 540, 1180, 64, "Bungee", INK, alpha=a)
        b = min(1.0, max(0.0, (t - 0.7) / 0.4))
        text(c, "NEXT:", 540, 1320, 44, "Bungee", CORAL, alpha=b)
        text(c, P.get("next", ""), 540, 1400, 54, "Bungee", INK, alpha=b)
    elif kind == "end":
        a = min(1.0, t / 0.5)
        text(c, P.get("big", "TO BE"), 540, 820, 100, "Bungee", INK, alpha=a)
        text(c, P.get("big2", "CONTINUED?"), 540, 950, 90, "Bungee", CORAL, alpha=a)
        b = min(1.0, max(0.0, (t - 0.8) / 0.4))
        text(c, P.get("tag", ""), 540, 1120, 40, "Bungee", INK, alpha=b)
    elif kind == "text":
        a = min(1.0, t / 0.3)
        lines_ = P.get("lines", [])
        y = 900 - (len(lines_) - 1) * 60
        for ln in lines_:
            text(c, ln, 540, y, 84, "Bungee", INK, alpha=a)
            y += 120
    actors(0)


SETS = {
    "d_room": set_room, "d_house": set_house, "d_side": set_side, "d_kitchen": set_kitchen,
    "d_office": set_office, "d_lobby": set_lobby, "d_lab": set_lab, "d_hall": set_hall, "d_fall": set_fall,
    "d_sewer": set_sewer, "d_shaft": set_shaft, "d_screen": set_screen, "d_black": set_black, "d_card": set_card2,
}
