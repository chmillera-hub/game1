"""The moonlit graveyard dance floor, and the little band:
a pumpkin drummer, a black cat on the fiddle, and a bat on a horn."""
import math

import cairo

from drawkit import (INK, crooked_house, curly_tree, ellipse, fence, hash01, hexc, lerp, linear, moon, pumpkin,
                     radial, stars, tombstone, vnoise)

W, H = 1080, 1920
MOON_XY, MOON_R = (540, 600), 250
GROUND = 1395                # front row of dancers stands here
GRAVES = {'M': (560, 1395), 'K1': (385, 1385), 'K2': (765, 1388), 'K3': (470, 1300), 'K4': (665, 1306)}
SIMMER_AT = (118, 1300)
CAT_AT = (968, 1068)
PUMPKIN_AT = (978, 1300)
HIDE_STONE = (262, 1245)     # the tombstone Alice hides behind


def clock_tower(ctx, x, y):
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgb(*hexc('#0f1826'))
    ctx.move_to(-38, 0)
    ctx.line_to(-30, -230)
    ctx.line_to(30, -236)
    ctx.line_to(40, 0)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(-44, -228)
    ctx.line_to(8, -330)
    ctx.line_to(44, -234)
    ctx.close_path()
    ctx.fill()
    ctx.arc(0, -190, 27, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc('#f3e2a8'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*hexc('#0f1826'))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.move_to(0, -190)
    ctx.line_to(0, -212)                     # both hands straight up: midnight
    ctx.move_to(0, -190)
    ctx.line_to(2, -205)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


def gate(ctx, x, y):
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgb(*hexc('#090a10'))
    for px in (-70, 70):
        ctx.rectangle(px - 12, -300, 24, 300)
        ctx.fill()
        ctx.arc(px, -306, 16, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_line_width(5)
    ctx.new_path()
    ctx.arc(0, -250, 70, math.pi, 2 * math.pi)
    ctx.stroke()
    for k in range(-2, 3):
        ctx.move_to(k * 24, 0)
        ctx.line_to(k * 24, -240 + abs(k) * 8)
    ctx.stroke()
    for k in range(-1, 2):
        ctx.new_path()
        for j in range(18):
            f = j / 17
            a = f * 5.2
            r = 13 * (1 - f * 0.7)
            (ctx.line_to if j else ctx.move_to)(k * 40 + math.cos(a) * r, -150 + math.sin(a) * r)
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.restore()


def grave_mound(ctx, x, y, s=1.0):
    ellipse(ctx, x, y + 6 * s, 92 * s, 20 * s)
    ctx.set_source_rgb(*hexc('#2a2118'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ellipse(ctx, x, y + 4 * s, 64 * s, 11 * s)
    ctx.set_source_rgb(*hexc('#0b0806'))
    ctx.fill()


def bg_dance(ctx):
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(linear(0, 0, 0, 1300, [(0, hexc('#0a0b1d', 1)), (0.62, hexc('#1f3150', 1)), (1, hexc('#3f6172', 1))]))
    ctx.fill()
    stars(ctx, 150, 1000, 33)
    moon(ctx, MOON_XY[0], MOON_XY[1], MOON_R)
    for i, (cx, cy, rx) in enumerate(((330, 700, 240), (820, 480, 190), (650, 820, 210))):
        ellipse(ctx, cx, cy, rx, 15 + 5 * i)
        ctx.set_source_rgba(0.12, 0.16, 0.26, 0.5)
        ctx.fill()
    # far hills and the crooked town, with its clock tower
    ctx.new_path()
    ctx.move_to(0, 1120)
    for x in range(0, W + 60, 60):
        ctx.line_to(x, 1060 + 30 * math.sin(x * 0.007 + 2) + 14 * math.sin(x * 0.019))
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    ctx.set_source_rgb(*hexc('#17263a'))
    ctx.fill()
    for i, (x, y, w, h, lean, roof) in enumerate([(250, 1065, 60, 110, 0.4, 60), (320, 1060, 50, 140, -0.6, 70),
                                                   (640, 1055, 70, 120, 0.5, 60), (880, 1066, 60, 100, -0.3, 50),
                                                   (960, 1070, 70, 140, 0.6, 80)]):
        crooked_house(ctx, x, y, w, h, lean, roof, hexc('#0f1826'), hexc('#ffb54d'), i + 3)
    clock_tower(ctx, 790, 1070)
    # nearer hill with the graveyard
    ctx.new_path()
    ctx.move_to(0, 1210)
    ctx.curve_to(300, 1150, 700, 1180, W, 1150)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    ctx.set_source_rgb(*hexc('#131c29'))
    ctx.fill()
    fence(ctx, 250, 1080, 1220, 90)
    curly_tree(ctx, 70, 1300, 640, 1)
    gate(ctx, 105, 1290)
    # the dance floor: a moonlit clearing
    ctx.new_path()
    ctx.move_to(0, 1290)
    ctx.curve_to(300, 1250, 750, 1270, W, 1250)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    ctx.set_source(linear(0, 1250, 0, H, [(0, hexc('#182230', 1)), (0.5, hexc('#0d131c', 1)), (1, hexc('#05070b', 1))]))
    ctx.fill()
    ellipse(ctx, 540, 1390, 520, 95)
    ctx.set_source(radial(ctx, 540, 1390, 520, [(0, (0.55, 0.65, 0.85, 0.16)), (1, (0.55, 0.65, 0.85, 0))]))
    ctx.fill()
    # each dancer's grave: a headstone behind, a mound at their feet
    for k, (x, y) in GRAVES.items():
        s = 0.82 if k in ('K3', 'K4') else 1.0
        tombstone(ctx, x + (70 if k != 'M' else 95) * s, y - 8, 64 * s, 120 * s, 0.06 * (1 if x > 540 else -1),
                  cross=k in ('K2', 'K3'))
    for k, (x, y) in GRAVES.items():
        grave_mound(ctx, x, y, 0.82 if k in ('K3', 'K4') else 1.0)
    # the band's perch
    tombstone(ctx, CAT_AT[0], CAT_AT[1] + 220, 110, 140, 0.04)
    for i in range(30):
        gx = hash01(i, 61) * W
        gy = 1440 + hash01(i, 62) * 460
        ctx.move_to(gx - 10, gy)
        ctx.line_to(gx - 4, gy - 22)
        ctx.line_to(gx, gy)
        ctx.line_to(gx + 6, gy - 28)
        ctx.line_to(gx + 10, gy)
        ctx.set_source_rgb(*hexc('#1a2430'))
        ctx.fill()


def fg_dance(ctx, t):
    # Alice's hiding stone, drawn in front of her
    tombstone(ctx, HIDE_STONE[0], HIDE_STONE[1] + 85, 150, 205, -0.05)
    for x, y, r, seed in ((80, 1690, 60, 1), (1000, 1660, 52, 2)):
        pumpkin(ctx, x, y, r, t, 0.5 + 0.5 * vnoise(t * 6, seed))


# ── the band ─────────────────────────────────────────────────────────────────
def draw_pumpkin_drummer(ctx, x, y, s, t, beat_phase, hit, look=0.0, grin=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    bounce = -6 * hit
    # little drum
    ellipse(ctx, -10, 92, 76, 20)
    ctx.set_source_rgb(*hexc('#d9d0c0'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.rectangle(-86, 92, 152, 62)
    ctx.set_source_rgb(*hexc('#7a2430'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.stroke()
    for k in range(5):
        ctx.move_to(-86 + k * 38, 94)
        ctx.line_to(-67 + k * 38, 152)
    ctx.set_source_rgb(*hexc('#e8c46a'))
    ctx.set_line_width(3)
    ctx.stroke()
    # body (a big pumpkin) with a carved face that grins harder on the hits
    pumpkin(ctx, 0, bounce, 82, t, 0.7 + 0.3 * hit)
    for side in (-1, 1):
        ellipse(ctx, side * 30 + look * 6, -22 + bounce, 15, 13 - 7 * hit)
        ctx.set_source_rgb(*hexc('#ffe9a0'))
        ctx.fill()
    # vine arms with drumsticks
    for side in (-1, 1):
        lift = 30 * (1 - hit) if (side < 0) == (beat_phase < 0.5) else 6
        sx, sy = side * 70, 20 + bounce
        hx, hy = side * 58, 70 - lift
        ctx.new_path()
        ctx.move_to(sx, sy)
        ctx.curve_to(side * 95, 40, side * 80, 60, hx, hy)
        ctx.set_source_rgb(*hexc('#2f5a24'))
        ctx.set_line_width(7)
        ctx.stroke()
        ctx.move_to(hx, hy)
        ctx.line_to(hx - side * 50, hy + 24 - lift * 0.4)
        ctx.set_source_rgb(*hexc('#c9a46a'))
        ctx.set_line_width(6)
        ctx.stroke()
    ctx.restore()


def draw_cat(ctx, x, y, s, t, playing, bow_phase, lids=0.55, mouth=0.0, ear=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    black = hexc('#0c0b10')
    rim = (0.45, 0.55, 0.8, 0.7)
    # tail
    ctx.new_path()
    ctx.move_to(40, 70)
    tw = 12 * math.sin(t * 2.1)
    ctx.curve_to(110, 70, 120 + tw, -10, 80 + tw, -40)
    ctx.set_source_rgb(*black)
    ctx.set_line_width(14)
    ctx.stroke()
    # body
    ellipse(ctx, 0, 40, 60, 66)
    ctx.set_source_rgb(*black)
    ctx.fill_preserve()
    ctx.set_source_rgba(*rim)
    ctx.set_line_width(3)
    ctx.stroke()
    # head with ears
    hy = -50
    for side in (-1, 1):
        ctx.new_path()
        ctx.move_to(side * 40, hy - 10)
        ctx.line_to(side * (34 + ear * 6), hy - 70)
        ctx.line_to(side * 8, hy - 32)
        ctx.close_path()
        ctx.set_source_rgb(*black)
        ctx.fill_preserve()
        ctx.set_source_rgba(*rim)
        ctx.stroke()
    ellipse(ctx, 0, hy, 52, 44)
    ctx.set_source_rgb(*black)
    ctx.fill_preserve()
    ctx.set_source_rgba(*rim)
    ctx.stroke()
    # smug half-lidded yellow eyes
    for side in (-1, 1):
        ex, ey = side * 22, hy - 6
        ctx.save()
        ellipse(ctx, ex, ey, 13, 11)
        ctx.clip()
        ctx.set_source_rgb(*hexc('#ffd84d'))
        ctx.paint()
        ellipse(ctx, ex + 2, ey, 3, 9)
        ctx.set_source_rgb(*black)
        ctx.fill()
        ctx.rectangle(ex - 20, ey - 20, 40, 20 * lids * 1.6)
        ctx.set_source_rgb(*black)
        ctx.fill()
        ctx.restore()
    # mouth / whiskers
    ctx.new_path()
    if mouth > 0.05:
        ellipse(ctx, 0, hy + 20, 10, 8 * mouth + 2)
        ctx.set_source_rgb(*hexc('#c45a6e'))
        ctx.fill()
    ctx.move_to(-10, hy + 14)
    ctx.curve_to(-4, hy + 20, 0, hy + 16, 0, hy + 14)
    ctx.curve_to(0, hy + 16, 4, hy + 20, 10, hy + 14)
    ctx.set_source_rgba(*rim)
    ctx.set_line_width(2.5)
    ctx.stroke()
    for side in (-1, 1):
        for k in (-1, 0, 1):
            ctx.move_to(side * 18, hy + 12 + k * 4)
            ctx.line_to(side * 54, hy + 6 + k * 9)
    ctx.set_source_rgba(0.8, 0.85, 0.95, 0.6)
    ctx.set_line_width(1.5)
    ctx.stroke()
    # fiddle tucked under the chin, bow sawing on the beat
    ctx.save()
    ctx.translate(-34, 10)
    ctx.rotate(-0.6)
    ellipse(ctx, 0, 30, 22, 34)
    ctx.set_source_rgb(*hexc('#a0522d'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.rectangle(-4, -46, 8, 50)
    ctx.set_source_rgb(*hexc('#3a2010'))
    ctx.fill()
    ctx.restore()
    bow = 26 * math.sin(2 * math.pi * bow_phase) if playing else 0
    ctx.move_to(-80 + bow, 30 - bow * 0.3)
    ctx.line_to(10 + bow, 0 - bow * 0.3)
    ctx.set_source_rgb(*hexc('#e8dcc0'))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def draw_bat(ctx, x, y, s, t, toot=0.0, flap_rate=7.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    flap = math.sin(t * 2 * math.pi * flap_rate)
    ctx.set_source_rgb(*hexc('#100c18'))
    for side in (-1, 1):
        ctx.new_path()
        ctx.move_to(0, -4)
        ctx.curve_to(side * 30, -36 - 30 * flap, side * 60, -18 - 36 * flap, side * 86, -10 - 32 * flap)
        ctx.curve_to(side * 68, 8, side * 52, -2, side * 38, 14)
        ctx.curve_to(side * 24, 6, side * 12, 12, 0, 8)
        ctx.close_path()
        ctx.fill()
    ellipse(ctx, 0, 0, 22, 26)
    ctx.fill()
    for side in (-1, 1):
        ctx.move_to(side * 8, -20)
        ctx.line_to(side * 16, -44)
        ctx.line_to(side * 20, -16)
        ctx.fill()
    for side in (-1, 1):
        ellipse(ctx, side * 8, -6, 5, 6)
        ctx.set_source_rgb(*hexc('#ff9a3c'))
        ctx.fill()
    # tiny brass horn
    ctx.set_source_rgb(*hexc('#e0b040'))
    ctx.move_to(4, 8)
    ctx.line_to(40, 14)
    ctx.line_to(52, 2 - 6 * toot)
    ctx.line_to(54, 30 + 6 * toot)
    ctx.line_to(40, 20)
    ctx.line_to(4, 16)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(2.5)
    ctx.stroke()
    if toot > 0.1:
        for k in range(3):
            ctx.arc(64 + k * 14, 16 - k * 10, 3 + 2 * toot, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 0.9, 0.5, 0.8 * toot)
            ctx.fill()
    ctx.restore()


def draw_owl(ctx, x, y, s, t, awake=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ellipse(ctx, 0, 0, 26, 32)
    ctx.set_source_rgb(*hexc('#3b2c22'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    for side in (-1, 1):
        ctx.arc(side * 11, -10, 10, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#ffd36b'))
        ctx.fill()
        ctx.rectangle(side * 11 - 11, -21, 22, 22 * (1 - awake) * 0.9)
        ctx.set_source_rgb(*hexc('#3b2c22'))
        ctx.fill()
        ctx.arc(side * 11, -10, 3.5 * awake, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
    ctx.move_to(-4, 2)
    ctx.line_to(4, 2)
    ctx.line_to(0, 10)
    ctx.set_source_rgb(*hexc('#e8a030'))
    ctx.fill()
    ctx.restore()
