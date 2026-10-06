"""Graphics for 'Anger in the Dungeon': the warrior, the creature, the beast,
cave scenes, lighting and particles."""
import math
import random

import cairo

import engine as E
from engine import (W, H, GROUND, PI, clamp, lerp, ease, ease_out, ellipse, rrect, src, mix, rgb,
                    fill_stroke, sparkle)

TITLE_FONT = "Cinzel"

# ---------------------------------------------------------------- the warrior
E.KIND["warrior"] = dict(
    w=160, h=205, legh=42, n=3.0, taper=-0.2, col="#D64A3A", dark="#5E160F",
    eye_y=-182, eye_dx=26, erx=12, ery=13, mouth_y=-146, mw=34, sh=(84, -150), hip=36, L=64,
    brow=(30, 30), brow_raise=(0, 0), lid=0.0, legw=(28, 20), legcol="#7C8794",
    legdark="#22262C", armw=(26, 18), handcol="#8E99A6", handdark="#22262C", handr=15,
    footr=(24, 12), foot="#3A3F47")

STEEL = "#9AA5B1"
STEEL_D = "#3B434D"


def _warrior_hook(stage, ctx, c, k, t, top):
    if stage == "pre":
        if c.get("cape", True):
            sway = math.sin(t * 2.1) * 6 + c.get("cape_lift", 0) * -40
            ctx.move_to(-76, -220)
            ctx.line_to(76, -220)
            ctx.curve_to(98, -140, 100 + sway, -70, 88 + sway, -16)
            ctx.line_to(-90 + sway, -16)
            ctx.curve_to(-100 + sway, -70, -98, -140, -76, -220)
            ctx.close_path()
            fill_stroke(ctx, "#5A1020", "#2A0710", 4)
        if c.get("shield_back", True):
            sx, sy = -44 * (1 if c["face"] >= 0 else -1), -140
            ellipse(ctx, sx, sy, 66, 66)
            fill_stroke(ctx, "#6B4426", STEEL_D, 6)
            ellipse(ctx, sx, sy, 56, 56)
            src(ctx, STEEL_D)
            ctx.set_line_width(3)
            ctx.stroke()
            for a in range(8):
                ang = a * PI / 4
                ctx.move_to(sx + math.cos(ang) * 14, sy + math.sin(ang) * 14)
                ctx.line_to(sx + math.cos(ang) * 56, sy + math.sin(ang) * 56)
            src(ctx, "#4E3019")
            ctx.set_line_width(2)
            ctx.stroke()
            ellipse(ctx, sx, sy, 14, 14)
            fill_stroke(ctx, STEEL, STEEL_D, 3)
    elif stage == "body":
        fx = c["face"] * k["w"] * 0.1
        # breastplate
        ctx.save()
        ctx.move_to(-88, -122)
        ctx.curve_to(-40, -134, 40, -134, 88, -122)
        ctx.line_to(80, -58)
        ctx.curve_to(40, -46, -40, -46, -80, -58)
        ctx.close_path()
        g = cairo.LinearGradient(-80, 0, 80, 0)
        g.add_color_stop_rgb(0, *rgb("#6E7884"))
        g.add_color_stop_rgb(0.45, *rgb("#C9D2DB"))
        g.add_color_stop_rgb(1, *rgb("#5C6570"))
        ctx.set_source(g)
        ctx.fill_preserve()
        src(ctx, STEEL_D)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.move_to(0, -128)
        ctx.line_to(0, -50)
        src(ctx, STEEL_D, 0.6)
        ctx.set_line_width(3)
        ctx.stroke()
        # pecs / abs lines
        for sx_ in (-1, 1):
            ctx.move_to(sx_ * 8, -116)
            ctx.curve_to(sx_ * 40, -118, sx_ * 66, -108, sx_ * 70, -94)
        src(ctx, STEEL_D, 0.5)
        ctx.set_line_width(3)
        ctx.stroke()
        for rx in (-68, 68):
            ellipse(ctx, rx, -110, 3, 3)
            src(ctx, STEEL_D)
            ctx.fill()
        # belt
        ctx.rectangle(-84, -62, 168, 15)
        fill_stroke(ctx, "#5A3A22", "#2E1D10", 3)
        rrect(ctx, -12, -65, 24, 21, 3)
        fill_stroke(ctx, "#D9B44A", "#7A5E14", 3)
        ctx.restore()
        # beard
        rnd_ = random.Random(4)
        for i in range(46):
            sx_ = fx + rnd_.uniform(-44, 44)
            sy_ = -150 + rnd_.uniform(-4, 16) + abs(sx_ - fx) * -0.15
            ellipse(ctx, sx_, sy_, 1.4, 1.4)
            src(ctx, "#5A1A12", 0.7)
            ctx.fill()
        # scar
        ctx.move_to(fx + 44, -192)
        ctx.line_to(fx + 34, -164)
        src(ctx, "#8E2A20")
        ctx.set_line_width(3)
        ctx.stroke()
        # helmet
        hy = -203
        ctx.save()
        ctx.move_to(-84, hy)
        ctx.curve_to(-84, top - 40, 84, top - 40, 84, hy)
        ctx.close_path()
        g = cairo.LinearGradient(-84, 0, 84, 0)
        g.add_color_stop_rgb(0, *rgb("#5E6873"))
        g.add_color_stop_rgb(0.4, *rgb("#D2DAE2"))
        g.add_color_stop_rgb(1, *rgb("#4E5762"))
        ctx.set_source(g)
        ctx.fill_preserve()
        src(ctx, STEEL_D)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.move_to(0, top - 26)
        ctx.line_to(0, hy)
        src(ctx, STEEL_D, 0.7)
        ctx.set_line_width(5)
        ctx.stroke()
        rrect(ctx, -88, hy - 6, 176, 14, 5)
        fill_stroke(ctx, "#8A949F", STEEL_D, 3)
        for i in range(7):
            ellipse(ctx, -72 + i * 24, hy + 1, 2.5, 2.5)
            src(ctx, STEEL_D)
            ctx.fill()
        # horns
        for side in (-1, 1):
            ctx.move_to(side * 70, hy - 26)
            ctx.curve_to(side * 110, hy - 34, side * 122, hy - 70, side * 104, hy - 100)
            ctx.curve_to(side * 104, hy - 70, side * 96, hy - 48, side * 66, hy - 44)
            ctx.close_path()
            fill_stroke(ctx, "#EADFC6", "#6E6250", 3)
        ctx.restore()
        # dirt / bruises
        if c.get("hurt", 0) > 0:
            for (bx, by, r) in ((fx - 44, -160, 9), (fx + 38, -140, 7), (-30, -90, 10)):
                ellipse(ctx, bx, by, r, r * 0.8)
                src(ctx, "#5A2A5E", 0.55 * c["hurt"])
                ctx.fill()
    elif stage == "post":
        for side in (-1, 1):
            px, py = side * 84, -152
            ctx.move_to(px - 34, py + 12)
            ctx.curve_to(px - 34, py - 34, px + 34, py - 34, px + 34, py + 12)
            ctx.close_path()
            g = cairo.LinearGradient(px - 34, 0, px + 34, 0)
            g.add_color_stop_rgb(0, *rgb("#68727D"))
            g.add_color_stop_rgb(0.5, *rgb("#C9D2DB"))
            g.add_color_stop_rgb(1, *rgb("#55606B"))
            ctx.set_source(g)
            ctx.fill_preserve()
            src(ctx, STEEL_D)
            ctx.set_line_width(4)
            ctx.stroke()
            ctx.move_to(px - 30, py)
            ctx.curve_to(px - 20, py - 12, px + 20, py - 12, px + 30, py)
            src(ctx, STEEL_D, 0.6)
            ctx.set_line_width(2.5)
            ctx.stroke()


E.HOOKS["warrior"] = _warrior_hook


def flame(ctx, x, y, t, s=1.0, seed=0.0):
    g = cairo.RadialGradient(x, y - 10 * s, 0, x, y - 10 * s, 70 * s)
    g.add_color_stop_rgba(0, 1, 0.75, 0.3, 0.55)
    g.add_color_stop_rgba(1, 1, 0.5, 0.1, 0)
    ctx.set_source(g)
    ctx.arc(x, y - 10 * s, 70 * s, 0, 2 * PI)
    ctx.fill()
    for i, (col, sc) in enumerate((("#FF5A1F", 1.0), ("#FFA62B", 0.72), ("#FFF1A8", 0.42))):
        fl = 1 + 0.12 * math.sin(t * 17 + i * 2 + seed) + 0.08 * math.sin(t * 29 + seed)
        hh = 46 * s * sc * fl
        ww = 16 * s * sc
        sw = math.sin(t * 9 + i + seed) * 5 * s * sc
        ctx.move_to(x - ww, y)
        ctx.curve_to(x - ww * 1.2, y - hh * 0.5, x + sw - ww * 0.2, y - hh * 0.8, x + sw, y - hh)
        ctx.curve_to(x + sw + ww * 0.2, y - hh * 0.8, x + ww * 1.2, y - hh * 0.5, x + ww, y)
        ctx.curve_to(x + ww * 0.6, y + ww * 0.7, x - ww * 0.6, y + ww * 0.7, x - ww, y)
        src(ctx, col, 0.95)
        ctx.fill()


def _torch(ctx, hx, hy, wang, c, t):
    a = math.radians(wang)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(a)
    ctx.move_to(-14, 0)
    ctx.line_to(58, 0)
    src(ctx, "#5A3A22")
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.move_to(44, 0)
    ctx.line_to(62, 0)
    src(ctx, "#2E1D10")
    ctx.set_line_width(14)
    ctx.stroke()
    ctx.restore()


def _torch_front(ctx, hx, hy, wang, c, t):
    a = math.radians(wang)
    fx, fy = hx + math.cos(a) * 64, hy + math.sin(a) * 64
    ctx.save()
    ctx.translate(fx, fy)
    ctx.rotate(-c["tilt"])
    flame(ctx, 0, 0, t, 1.0)
    ctx.restore()


def _sword(ctx, hx, hy, wang, c, t):
    a = math.radians(wang)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(a)
    # pommel and grip
    ellipse(ctx, -22, 0, 7, 7)
    fill_stroke(ctx, "#D9B44A", "#7A5E14", 2)
    ctx.rectangle(-20, -5, 26, 10)
    fill_stroke(ctx, "#3A2414", "#1A0F06", 2)
    # blade
    L = c.get("blade", 128)
    ctx.move_to(14, -8)
    ctx.line_to(14 + L, -5)
    ctx.line_to(26 + L, 0)
    ctx.line_to(14 + L, 5)
    ctx.line_to(14, 8)
    ctx.close_path()
    g = cairo.LinearGradient(0, -8, 0, 8)
    g.add_color_stop_rgb(0, *rgb("#F2F6FA"))
    g.add_color_stop_rgb(0.5, *rgb("#A8B4C0"))
    g.add_color_stop_rgb(1, *rgb("#6E7A86"))
    ctx.set_source(g)
    ctx.fill_preserve()
    src(ctx, "#2B323A")
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.move_to(18, 0)
    ctx.line_to(8 + L, 0)
    src(ctx, "#6E7A86")
    ctx.set_line_width(2)
    ctx.stroke()
    # crossguard
    rrect(ctx, 8, -22, 9, 44, 3)
    fill_stroke(ctx, "#D9B44A", "#7A5E14", 2)
    if c.get("glint", 0) > 0:
        sparkle(ctx, 14 + L * 0.7, -3, 16 * c["glint"], "#FFFFFF")
    ctx.restore()


E.ITEMS["torch"] = _torch
E.FRONT_ITEMS["torch"] = _torch_front
E.ITEMS["sword"] = _sword


def new_warrior(x, **kw):
    c = E.new_char("warrior", x, mouth="frown", mamt=0.25, brow=-0.2, itemL="torch", wandL=-80,
                   itemR="sword", wandR=-55)
    c["hl"] = (-64, -250)
    c["hr"] = (112, -110)
    c.update(kw)
    return c


def hand_world(c, side):
    h = c["hl"] if side < 0 else c["hr"]
    return c["x"] + c["s"] * h[0], c["y"] + c["yoff"] + c["s"] * h[1]


def torch_world(c):
    hx, hy = hand_world(c, -1)
    a = math.radians(c["wandL"])
    return hx + math.cos(a) * 64 * c["s"], hy + math.sin(a) * 64 * c["s"] - 20


# ---------------------------------------------------------------- the creature
def draw_creature(ctx, x, y, s, face, t, m=None):
    m = m or {}
    mouth = m.get("mouth", 0.0)
    ko = m.get("ko", 0.0)
    walk = m.get("walk", 0.0)
    glow = m.get("glow", 1.0)
    alpha = m.get("alpha", 1.0)
    shadow_only = m.get("shadow", False)
    ctx.save()
    if alpha < 1:
        ctx.push_group()
    ctx.translate(x, y)
    ctx.scale(s * (1 if face >= 0 else -1), s)
    if ko > 0:
        ctx.translate(0, -10 * ko)
        ctx.rotate(-0.35 * ko)
    body = "#151821" if not shadow_only else "#07080C"
    edge = "#3A2E55"
    # tail
    tail_sway = math.sin(t * 4) * 12 * (1 - ko)
    ctx.move_to(-60, -40)
    ctx.curve_to(-120, -30 + tail_sway, -160, -70 - tail_sway, -205, -50 + tail_sway * 0.5)
    src(ctx, body)
    ctx.set_line_width(14)
    ctx.stroke()
    ctx.move_to(-195, -52 + tail_sway * 0.5)
    ctx.line_to(-225, -44 + tail_sway * 0.5)
    ctx.line_to(-200, -36 + tail_sway * 0.5)
    ctx.close_path()
    src(ctx, body)
    ctx.fill()
    # legs
    for i, lx in enumerate((-50, -25, 25, 50)):
        ph = t * 22 * walk + i * PI / 2
        lift = max(0, math.sin(ph)) * 14 * walk
        kx = lx + math.cos(ph) * 10 * walk
        ctx.move_to(lx * 0.8, -36)
        ctx.line_to(kx + 6, -24 - lift)
        ctx.line_to(kx + 12, -lift)
        src(ctx, body)
        ctx.set_line_width(9)
        ctx.stroke()
    # body with spines
    ellipse(ctx, 0, -50, 78, 30)
    src(ctx, body)
    ctx.fill_preserve()
    src(ctx, edge, 0.8)
    ctx.set_line_width(2.5)
    ctx.stroke()
    for i in range(6):
        sx = -50 + i * 18
        ctx.move_to(sx - 7, -74 + abs(sx) * 0.12)
        ctx.line_to(sx, -96 + abs(sx) * 0.15)
        ctx.line_to(sx + 7, -74 + abs(sx) * 0.12)
        src(ctx, body)
        ctx.fill()
    # head
    hx, hy = 92, -62
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(-0.2 * mouth)
    ellipse(ctx, 0, 0, 44, 30)
    src(ctx, body)
    ctx.fill_preserve()
    src(ctx, edge, 0.8)
    ctx.set_line_width(2.5)
    ctx.stroke()
    # ears
    for ex in (-14, 6):
        ctx.move_to(ex - 8, -22)
        ctx.line_to(ex - 18, -50)
        ctx.line_to(ex + 6, -26)
        ctx.close_path()
        src(ctx, body)
        ctx.fill()
    # eyes
    for ex, ey in ((14, -10), (-6, -12)):
        if ko > 0.5:
            for d in (-1, 1):
                ctx.move_to(ex - 6, ey - 6 * d)
                ctx.line_to(ex + 6, ey + 6 * d)
            src(ctx, "#FFE36A")
            ctx.set_line_width(3)
            ctx.stroke()
        elif glow > 0:
            g = cairo.RadialGradient(ex, ey, 0, ex, ey, 22)
            g.add_color_stop_rgba(0, 1, 0.9, 0.2, 0.7 * glow)
            g.add_color_stop_rgba(1, 1, 0.8, 0.1, 0)
            ctx.set_source(g)
            ctx.arc(ex, ey, 22, 0, 2 * PI)
            ctx.fill()
            ellipse(ctx, ex, ey, 7, 5.5)
            src(ctx, "#FFE36A", glow)
            ctx.fill()
            ellipse(ctx, ex + 1, ey, 1.6, 4.5)
            src(ctx, "#1A1200", glow)
            ctx.fill()
    ctx.restore()
    # jaw / mouth
    if mouth > 0.02 or ko > 0:
        mo = max(mouth, 0.5 * ko)
        ctx.save()
        ctx.translate(hx + 10, hy + 10)
        ctx.move_to(-20, 0)
        ctx.curve_to(10, 6 + 40 * mo, 40, 6 + 30 * mo, 46, 4 + 24 * mo)
        ctx.line_to(46, 0)
        ctx.close_path()
        src(ctx, "#3A0712")
        ctx.fill()
        # teeth
        for i in range(6):
            tx = -10 + i * 9
            ctx.move_to(tx, 0)
            ctx.line_to(tx + 4, 10 + mo * 4)
            ctx.line_to(tx + 8, 0)
            ctx.close_path()
            ctx.move_to(tx + 2, 6 + 34 * mo * (0.4 + i * 0.12))
            ctx.line_to(tx + 6, -4 + 34 * mo * (0.4 + i * 0.12))
            ctx.line_to(tx + 10, 6 + 34 * mo * (0.4 + i * 0.12))
            ctx.close_path()
        src(ctx, "#F2EEDC")
        ctx.fill()
        # tongue
        if m.get("tongue", 0) > 0 or ko > 0:
            tg = max(m.get("tongue", 0), ko)
            ctx.move_to(10, 10 + 20 * mo)
            ctx.curve_to(26, 30 + 30 * tg, 30, 60 * tg + 20, 22 + math.sin(t * 6) * 4, 70 * tg + 18)
            src(ctx, "#C2305A")
            ctx.set_line_width(9)
            ctx.stroke()
        ctx.restore()
        # drool
        if m.get("drool", 0) > 0:
            for i in range(3):
                u = (t * 0.9 + i * 0.33) % 1.0
                dx = hx + 18 + i * 12
                dy = hy + 16 + 30 * mo + u * 70
                ctx.move_to(dx, hy + 16 + 30 * mo)
                ctx.line_to(dx, dy)
                src(ctx, "#B9E8FF", 0.6 * (1 - u) * m["drool"])
                ctx.set_line_width(2.5)
                ctx.stroke()
                ellipse(ctx, dx, dy + 3, 3.5, 5)
                ctx.fill()
    if ko > 0.5:
        for i in range(4):
            a = t * 4 + i * PI / 2
            sparkle(ctx, hx + math.cos(a) * 40, hy - 50 + math.sin(a) * 12, 9, "#FFE36A")
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def glowing_eyes(ctx, x, y, a, t, s=1.0, look=0.0):
    if a <= 0:
        return
    for dx in (-11, 11):
        ex = x + dx * s + look * 4
        g = cairo.RadialGradient(ex, y, 0, ex, y, 20 * s)
        g.add_color_stop_rgba(0, 1, 0.9, 0.2, 0.7 * a)
        g.add_color_stop_rgba(1, 1, 0.8, 0.1, 0)
        ctx.set_source(g)
        ctx.arc(ex, y, 20 * s, 0, 2 * PI)
        ctx.fill()
        ellipse(ctx, ex, y, 6 * s, 4.5 * s)
        src(ctx, "#FFE36A", a)
        ctx.fill()


# ---------------------------------------------------------------- the beast
BEAST = "#4E6479"
BEAST_D = "#1E2A36"
CREAM = "#EFE3C4"


def draw_beast(ctx, x, y, s, t, b=None):
    b = b or {}
    ctx.save()
    ctx.translate(x + b.get("shake", 0) * math.sin(t * 50), y)
    ctx.scale(s, s * b.get("sq", 1.0))
    ctx.rotate(b.get("tilt", 0.0))
    breathe = 1 + 0.015 * math.sin(t * 1.6)
    tap = b.get("tap", 0.0)
    # feet
    for side in (-1, 1):
        lift = 0
        rot = 0
        if side > 0 and tap > 0:
            lift = max(0, math.sin(t * 9)) * 16 * tap
            rot = -max(0, math.sin(t * 9)) * 0.25 * tap
        ctx.save()
        ctx.translate(side * 90, -26 - lift)
        ctx.rotate(rot)
        ellipse(ctx, 0, 0, 66, 30)
        fill_stroke(ctx, CREAM, BEAST_D, 5)
        ellipse(ctx, 0, 2, 24, 13)
        src(ctx, "#C9B58C")
        ctx.fill()
        for k in (-36, 0, 36):
            ellipse(ctx, k, -18, 10, 8)
            src(ctx, "#F7EED6")
            ctx.fill()
        ctx.restore()
    # body
    ctx.save()
    ctx.scale(breathe, 1 / breathe)
    ellipse(ctx, 0, -215, 172, 200)
    g = cairo.RadialGradient(-50, -300, 30, 0, -215, 230)
    g.add_color_stop_rgb(0, *rgb("#6D86A0"))
    g.add_color_stop_rgb(1, *rgb(BEAST))
    ctx.set_source(g)
    ctx.fill_preserve()
    src(ctx, BEAST_D)
    ctx.set_line_width(6)
    ctx.stroke()
    # ears
    for side in (-1, 1):
        ctx.move_to(side * 70, -385)
        ctx.line_to(side * 112, -452)
        ctx.line_to(side * 126, -362)
        ctx.close_path()
        fill_stroke(ctx, BEAST, BEAST_D, 5)
        ctx.move_to(side * 86, -385)
        ctx.line_to(side * 110, -430)
        ctx.line_to(side * 116, -375)
        ctx.close_path()
        src(ctx, "#2E3C4B")
        ctx.fill()
    # belly
    ellipse(ctx, 0, -168, 128, 140)
    fill_stroke(ctx, CREAM, "#B9A77E", 3)
    # face (cream mask)
    ctx.move_to(-96, -318)
    ctx.curve_to(-96, -380, -40, -372, 0, -348)
    ctx.curve_to(40, -372, 96, -380, 96, -318)
    ctx.curve_to(96, -262, -96, -262, -96, -318)
    ctx.close_path()
    fill_stroke(ctx, CREAM, "#B9A77E", 3)
    ctx.restore()
    # eyes
    eyes = b.get("eyes", "beady")
    px = b.get("px", 0.0)
    for side in (-1, 1):
        ex, ey = side * 44 + px * 6, -330
        if eyes == "happy":
            ctx.move_to(ex - 12, ey + 3)
            ctx.curve_to(ex - 6, ey - 9, ex + 6, ey - 9, ex + 12, ey + 3)
            src(ctx, "#111")
            ctx.set_line_width(4.5)
            ctx.stroke()
        elif eyes == "squint":
            ctx.move_to(ex - 14, ey - 2 * side)
            ctx.line_to(ex + 14, ey + 2 * side)
            src(ctx, "#111")
            ctx.set_line_width(5)
            ctx.stroke()
            ctx.move_to(ex - 16, ey - 14 - 4 * side)
            ctx.line_to(ex + 16, ey - 10 + 4 * side)
            src(ctx, BEAST_D)
            ctx.set_line_width(5)
            ctx.stroke()
        elif eyes == "side":
            ellipse(ctx, ex + 6 * (1 if px >= 0 else -1), ey + 1, 5, 6)
            src(ctx, "#111")
            ctx.fill()
            ctx.move_to(ex - 15, ey - 4)
            ctx.line_to(ex + 15, ey - 4)
            src(ctx, BEAST_D)
            ctx.set_line_width(5)
            ctx.stroke()
        elif eyes == "wide":
            ellipse(ctx, ex, ey, 11, 12)
            fill_stroke(ctx, "#FFFFFF", "#111", 3)
            ellipse(ctx, ex + px * 4, ey + 1, 4.5, 5)
            src(ctx, "#111")
            ctx.fill()
        else:  # beady
            blink = ((t + 0.7) % 4.3) < 0.14
            if blink:
                ctx.move_to(ex - 7, ey)
                ctx.line_to(ex + 7, ey)
                src(ctx, "#111")
                ctx.set_line_width(4)
                ctx.stroke()
            else:
                ellipse(ctx, ex + px * 4, ey, 5.5, 7)
                src(ctx, "#111")
                ctx.fill()
                ellipse(ctx, ex + px * 4 - 1.5, ey - 2.5, 1.6, 1.6)
                src(ctx, "#FFF")
                ctx.fill()
    # cheeks
    if b.get("blush", 0) > 0:
        for side in (-1, 1):
            ellipse(ctx, side * 70, -300, 14, 8)
            src(ctx, "#F28BA8", 0.7 * b["blush"])
            ctx.fill()
    # mouth
    mouth = b.get("mouth", "grin")
    my = -296
    if mouth in ("grin", "tongue"):
        ctx.move_to(-58, my - 6)
        ctx.curve_to(-30, my + 24, 30, my + 24, 58, my - 6)
        ctx.curve_to(30, my + 8, -30, my + 8, -58, my - 6)
        ctx.close_path()
        src(ctx, "#5B1C26")
        ctx.fill_preserve()
        src(ctx, BEAST_D)
        ctx.set_line_width(4)
        ctx.stroke()
        for side in (-1, 1):
            ctx.move_to(side * 30 - 6, my + 5)
            ctx.line_to(side * 30, my - 6)
            ctx.line_to(side * 30 + 6, my + 6)
            ctx.close_path()
            src(ctx, "#FFFFFF")
            ctx.fill()
        if mouth == "tongue" and "tdx" in b:
            tdx, tdy = b["tdx"], b["tdy"]
            for wdt, col in ((30, "#8E2546"), (24, "#E2577E")):
                ctx.move_to(0, my + 8)
                ctx.curve_to(tdx * 0.2, my + tdy + 70, tdx * 0.7, my + tdy + 30, tdx, my + tdy)
                src(ctx, col)
                ctx.set_line_width(wdt)
                ctx.stroke()
            ellipse(ctx, tdx, my + tdy, 13, 11)
            src(ctx, "#E2577E")
            ctx.fill()
        elif mouth == "tongue":
            tl = b.get("tongue_len", 1.0)
            sw = math.sin(t * 2) * 4
            ctx.move_to(-20, my + 10)
            ctx.curve_to(-24, my + 60 * tl, 24 + sw, my + 60 * tl, 20, my + 10)
            ctx.close_path()
            fill_stroke(ctx, "#E2577E", "#8E2546", 3)
            ctx.move_to(0, my + 16)
            ctx.line_to(sw * 0.5, my + 40 * tl)
            src(ctx, "#8E2546")
            ctx.set_line_width(2)
            ctx.stroke()
    elif mouth == "pout":
        ellipse(ctx, 0, my + 4, 12, 7)
        fill_stroke(ctx, "#5B1C26", BEAST_D, 3)
    elif mouth == "frown":
        ctx.move_to(-34, my + 10)
        ctx.curve_to(-14, my - 6, 14, my - 6, 34, my + 10)
        src(ctx, BEAST_D)
        ctx.set_line_width(5)
        ctx.stroke()
    elif mouth == "snort":
        ellipse(ctx, 0, my + 4, 26, 16)
        fill_stroke(ctx, "#5B1C26", BEAST_D, 3)
    else:
        ctx.move_to(-30, my + 4)
        ctx.line_to(30, my + 4)
        src(ctx, BEAST_D)
        ctx.set_line_width(5)
        ctx.stroke()
    # arms
    arms = b.get("arms", "down")
    for side in (-1, 1):
        sx, sy = side * 150, -250
        if arms == "crossed":
            tx, ty = -side * 70, -205 + (12 if side > 0 else 0)
        elif arms == "mouth":
            tx, ty = (side * 26, -282) if side > 0 else (side * 150, -150)
        elif arms == "both_mouth":
            tx, ty = side * 22, -280
        elif arms == "wave" and side > 0:
            tx, ty = 230, -400 + math.sin(t * 10) * 18
        elif arms == "wipe" and side > 0:
            tx, ty = 40, -300
        else:
            tx, ty = side * 186, -130
        ctx.move_to(sx, sy)
        ctx.line_to(tx, ty)
        src(ctx, BEAST_D)
        ctx.set_line_width(56)
        ctx.stroke()
        ctx.move_to(sx, sy)
        ctx.line_to(tx, ty)
        src(ctx, BEAST)
        ctx.set_line_width(46)
        ctx.stroke()
        ellipse(ctx, tx, ty, 30, 28)
        fill_stroke(ctx, BEAST, BEAST_D, 5)
        for k in (-1, 0, 1):
            ellipse(ctx, tx + k * 12, ty + 14, 6, 7)
            src(ctx, CREAM)
            ctx.fill()
    ctx.restore()


def beast_local_to_world(x, y, s, b, px, py):
    tl = b.get("tilt", 0.0)
    sq = b.get("sq", 1.0)
    rx = px * math.cos(tl) - py * math.sin(tl)
    ry = px * math.sin(tl) + py * math.cos(tl)
    return x + s * rx, y + s * sq * ry


def beast_tongue_tip(x, y, s, b):
    return beast_local_to_world(x, y, s, b, b.get("tdx", 0), -296 + b.get("tdy", 60) + 8)


# ---------------------------------------------------------------- glove
def draw_glove_arm(ctx, x, y, t, reach=1.0, from_x=-200, grip=True):
    ctx.save()
    sx = from_x
    ctx.move_to(sx, y + 30)
    ctx.curve_to(lerp(sx, x, 0.5), y + 40, x - 60, y + 6, x - 20, y)
    src(ctx, "#2A2018")
    ctx.set_line_width(40)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    # cuff
    ctx.save()
    ctx.translate(x - 26, y)
    rrect(ctx, -16, -20, 26, 40, 6)
    fill_stroke(ctx, "#7A4E2A", "#3A2412", 3)
    ctx.restore()
    # glove
    ellipse(ctx, x, y, 24, 20)
    fill_stroke(ctx, "#8B5A2B", "#3A2412", 3)
    for i in range(4):
        fy = y - 12 + i * 8
        if grip:
            ellipse(ctx, x + 16, fy, 10, 5)
        else:
            ellipse(ctx, x + 26, fy, 14, 4.5)
        fill_stroke(ctx, "#8B5A2B", "#3A2412", 2)
    ctx.move_to(x - 14, y - 6)
    ctx.line_to(x + 6, y - 6)
    src(ctx, "#C9A06A", 0.8)
    ctx.set_line_width(1.5)
    ctx.set_dash([3, 3])
    ctx.stroke()
    ctx.set_dash([])
    ctx.restore()


# ---------------------------------------------------------------- rocks & scenes
def rock_fill(ctx, x0, y0, w, h, seed, base, n=260, lo=10, hi=60, light=0.25, dark=0.35):
    rnd = random.Random(seed)
    src(ctx, base)
    ctx.rectangle(x0, y0, w, h)
    ctx.fill()
    for i in range(n):
        cx = rnd.uniform(x0, x0 + w)
        cy = rnd.uniform(y0, y0 + h)
        r = rnd.uniform(lo, hi)
        k = rnd.randint(5, 8)
        for j in range(k):
            a = j * 2 * PI / k + rnd.uniform(-0.3, 0.3)
            rr = r * rnd.uniform(0.6, 1.0)
            px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.7
            (ctx.move_to if j == 0 else ctx.line_to)(px, py)
        ctx.close_path()
        u = rnd.random()
        col = mix(base, "#FFFFFF", light * rnd.random()) if u < 0.5 else mix(base, "#000000", dark * rnd.random())
        ctx.set_source_rgba(*col, 0.85)
        ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.25)
        ctx.set_line_width(2)
        ctx.stroke()


def stalactites(ctx, x0, x1, ytop, seed, col, down=True, scale=1.0):
    rnd = random.Random(seed)
    x = x0
    while x < x1:
        w = rnd.uniform(20, 70) * scale
        h = rnd.uniform(30, 150) * scale
        ctx.move_to(x, ytop)
        ctx.line_to(x + w / 2 + rnd.uniform(-8, 8), ytop + (h if down else -h))
        ctx.line_to(x + w, ytop)
        ctx.close_path()
        src(ctx, mix(col, "#000000", rnd.uniform(0, 0.3)))
        ctx.fill()
        x += w * rnd.uniform(0.5, 1.2)


_CACHE = {}


def tunnel_bg():
    if "tunnel" in _CACHE:
        return _CACHE["tunnel"]
    WW = 3400
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WW, H)
    ctx = cairo.Context(surf)
    rock_fill(ctx, 0, 0, WW, H, 1, "#3B332E", n=900, lo=14, hi=70)
    # floor
    g = cairo.LinearGradient(0, 600, 0, H)
    g.add_color_stop_rgb(0, *rgb("#2E2622"))
    g.add_color_stop_rgb(1, *rgb("#1A1512"))
    ctx.rectangle(0, 604, WW, H - 604)
    ctx.set_source(g)
    ctx.fill()
    rnd = random.Random(5)
    for i in range(220):
        x = rnd.uniform(0, WW)
        y = rnd.uniform(610, 712)
        ellipse(ctx, x, y, rnd.uniform(6, 26), rnd.uniform(3, 8))
        src(ctx, mix("#4A3F37", "#000000", rnd.random() * 0.5))
        ctx.fill()
    ctx.move_to(0, 606)
    for i in range(0, WW + 40, 40):
        ctx.line_to(i, 604 + rnd.uniform(-5, 5))
    src(ctx, "#57493F")
    ctx.set_line_width(4)
    ctx.stroke()
    # ceiling
    ctx.rectangle(0, 0, WW, 60)
    src(ctx, "#1E1916")
    ctx.fill()
    stalactites(ctx, 0, WW, 58, 7, "#2A231F")
    # roots
    for i in range(30):
        x = rnd.uniform(0, WW)
        ctx.move_to(x, 40)
        ctx.curve_to(x + rnd.uniform(-30, 30), 100, x + rnd.uniform(-40, 40), 160, x + rnd.uniform(-20, 20),
                     rnd.uniform(140, 260))
        src(ctx, "#4A3424", 0.8)
        ctx.set_line_width(rnd.uniform(2, 5))
        ctx.stroke()
    # bones & skull
    for bx in (520, 1720, 2480):
        ctx.move_to(bx, 640)
        ctx.line_to(bx + 50, 632)
        src(ctx, "#D9D2BE")
        ctx.set_line_width(7)
        ctx.stroke()
        ellipse(ctx, bx + 80, 628, 16, 13)
        src(ctx, "#D9D2BE")
        ctx.fill()
        for ex in (74, 86):
            ellipse(ctx, bx + ex, 626, 3.5, 4)
            src(ctx, "#1A1512")
            ctx.fill()
    # door arch
    ax = 3000
    ctx.move_to(ax - 150, 606)
    ctx.line_to(ax - 150, 300)
    ctx.curve_to(ax - 150, 160, ax + 150, 160, ax + 150, 300)
    ctx.line_to(ax + 150, 606)
    ctx.close_path()
    src(ctx, "#2A231F")
    ctx.fill()
    for i in range(11):
        a = PI + i * PI / 10
        r0, r1 = 150, 196
        cx, cy = ax, 300
        ctx.move_to(cx + math.cos(a - 0.12) * r0, cy + math.sin(a - 0.12) * r0)
        ctx.line_to(cx + math.cos(a - 0.12) * r1, cy + math.sin(a - 0.12) * r1)
        ctx.line_to(cx + math.cos(a + 0.12) * r1, cy + math.sin(a + 0.12) * r1)
        ctx.line_to(cx + math.cos(a + 0.12) * r0, cy + math.sin(a + 0.12) * r0)
        ctx.close_path()
        fill_stroke(ctx, "#5E544B", "#1A1512", 3)
    for side in (-1, 1):
        for j in range(6):
            rrect(ctx, ax + side * 173 - 23, 300 + j * 52, 46, 50, 4)
            fill_stroke(ctx, "#5E544B", "#1A1512", 3)
    _CACHE["tunnel"] = surf
    return surf


def draw_door(ctx, x, t, state):
    """Wooden door in the arch at world x (arch center). state: dict(burst=t0 or None, rattle)."""
    burst = state.get("burst")
    if burst is None or t < burst:
        rat = state.get("rattle", 0.0)
        dx = math.sin(t * 60) * 3 * rat
        ctx.save()
        ctx.translate(dx, 0)
        ctx.move_to(x - 140, 606)
        ctx.line_to(x - 140, 300)
        ctx.curve_to(x - 140, 172, x + 140, 172, x + 140, 300)
        ctx.line_to(x + 140, 606)
        ctx.close_path()
        ctx.save()
        ctx.clip_preserve()
        src(ctx, "#5A3A22")
        ctx.fill()
        for i in range(7):
            ctx.rectangle(x - 140 + i * 40, 160, 3, 450)
            src(ctx, "#2E1D10")
            ctx.fill()
        for by in (290, 470):
            ctx.rectangle(x - 140, by, 280, 20)
            src(ctx, "#3B434D")
            ctx.fill()
            for i in range(7):
                ellipse(ctx, x - 120 + i * 40, by + 10, 4, 4)
                src(ctx, "#9AA5B1")
                ctx.fill()
        ctx.restore()
        # ring handle + lock
        ellipse(ctx, x + 80, 420, 18, 18)
        src(ctx, "#9AA5B1")
        ctx.set_line_width(5)
        ctx.stroke()
        rrect(ctx, x + 60, 380, 40, 22, 4)
        fill_stroke(ctx, "#3B434D", "#111", 2)
        ellipse(ctx, x + 80, 391, 4, 6)
        src(ctx, "#111")
        ctx.fill()
        ctx.restore()
        return
    # splinters fly outward
    dt = t - burst
    rnd = random.Random(42)
    for i in range(18):
        px0 = x + rnd.uniform(-120, 120)
        py0 = rnd.uniform(220, 590)
        vx = rnd.uniform(300, 1100)
        vy = rnd.uniform(-600, -100)
        px = px0 + vx * dt
        py = py0 + vy * dt + 900 * dt * dt
        if py > 640:
            py = 640 + rnd.uniform(-20, 20)
            px = px0 + vx * max(0, (math.sqrt(max(0, (640 - py0) / 900 + (vy / 1800) ** 2)) - vy / 1800))
        ang = rnd.uniform(0, 6) + dt * rnd.uniform(-10, 10) * clamp(1 - dt)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(ang)
        ctx.rectangle(-rnd.uniform(20, 50), -9, rnd.uniform(40, 100), 18)
        fill_stroke(ctx, "#5A3A22", "#2E1D10", 3)
        ctx.restore()


def cavern_bg():
    if "cavern" in _CACHE:
        return _CACHE["cavern"]
    WW, HH = 2600, 1080
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WW, HH)
    ctx = cairo.Context(surf)
    ctx.translate(0, 360)  # world y=-360 maps to 0
    g = cairo.LinearGradient(0, -360, 0, 720)
    g.add_color_stop_rgb(0, *rgb("#0E0D14"))
    g.add_color_stop_rgb(1, *rgb("#2E2A33"))
    ctx.rectangle(0, -360, WW, HH)
    ctx.set_source(g)
    ctx.fill()
    # far wall layers
    rnd = random.Random(9)
    for layer, (col, base_y, amp) in enumerate((("#1C1A22", 150, 120), ("#26222B", 300, 90), ("#302A30", 430, 70))):
        ctx.move_to(0, 720)
        x = 0
        while x <= WW + 60:
            ctx.line_to(x, base_y + math.sin(x * 0.004 + layer) * amp + rnd.uniform(-30, 30))
            x += 60
        ctx.line_to(WW, 720)
        ctx.close_path()
        src(ctx, col)
        ctx.fill()
    # pillars / stalagmites in the distance
    for i in range(14):
        x = rnd.uniform(0, WW)
        h = rnd.uniform(120, 360)
        ctx.move_to(x - 40, 610)
        ctx.line_to(x, 610 - h)
        ctx.line_to(x + 40, 610)
        ctx.close_path()
        src(ctx, mix("#3A333A", "#000000", rnd.uniform(0.2, 0.5)))
        ctx.fill()
    # ceiling
    ctx.rectangle(0, -360, WW, 80)
    src(ctx, "#0A090D")
    ctx.fill()
    stalactites(ctx, 0, WW, -282, 13, "#15131A", scale=2.2)
    # crevices
    for (cx, cy, hh) in ((1180, 360, 150), (1760, 300, 170), (560, 380, 120), (2200, 340, 140)):
        ctx.move_to(cx, cy - hh / 2)
        ctx.curve_to(cx - 18, cy - 10, cx + 14, cy + 10, cx - 4, cy + hh / 2)
        ctx.curve_to(cx + 30, cy + 10, cx + 22, cy - 20, cx, cy - hh / 2)
        src(ctx, "#050407")
        ctx.fill()
    # crystals (faint)
    for i in range(40):
        x = rnd.uniform(0, WW)
        y = rnd.uniform(-200, 560)
        ctx.move_to(x, y)
        ctx.line_to(x + 5, y - 16)
        ctx.line_to(x + 10, y)
        ctx.close_path()
        src(ctx, "#4FD1C5", 0.35)
        ctx.fill()
    # floor
    g = cairo.LinearGradient(0, 600, 0, 720)
    g.add_color_stop_rgb(0, *rgb("#3A3434"))
    g.add_color_stop_rgb(1, *rgb("#1C1818"))
    ctx.rectangle(0, 604, WW, 116)
    ctx.set_source(g)
    ctx.fill()
    for i in range(0, WW, 70):
        rrect(ctx, i + rnd.uniform(-6, 6), 606 + rnd.uniform(-2, 4), rnd.uniform(56, 70), 18, 5)
        src(ctx, mix("#4A4242", "#000000", rnd.uniform(0, 0.4)))
        ctx.fill()
    # pool
    ellipse(ctx, 1560, 640, 170, 30)
    src(ctx, "#0E2A33")
    ctx.fill()
    # broken entrance at left, door frame at right
    ctx.rectangle(0, 300, 70, 306)
    src(ctx, "#1A1716")
    ctx.fill()
    ax = 2460
    ctx.move_to(ax - 80, 606)
    ctx.line_to(ax - 80, 420)
    ctx.curve_to(ax - 80, 340, ax + 80, 340, ax + 80, 420)
    ctx.line_to(ax + 80, 606)
    ctx.close_path()
    fill_stroke(ctx, "#3A2A1E", "#5E544B", 10)
    _CACHE["cavern"] = surf
    return surf


def draw_pool(ctx, t, lit=1.0):
    ellipse(ctx, 1560, 640, 170, 30)
    g = cairo.LinearGradient(1390, 0, 1730, 0)
    g.add_color_stop_rgba(0, 0.1, 0.3, 0.38, 0.9)
    g.add_color_stop_rgba(1, 0.05, 0.18, 0.25, 0.9)
    ctx.set_source(g)
    ctx.fill()
    for i in range(5):
        u = (t * 0.3 + i / 5) % 1
        ellipse(ctx, 1560 + math.sin(i * 3) * 60, 640, 20 + u * 80, 4 + u * 12)
        src(ctx, "#9FE4FF", 0.25 * (1 - u) * lit)
        ctx.set_line_width(1.5)
        ctx.stroke()


def shaft_strip():
    if "shaft" in _CACHE:
        return _CACHE["shaft"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 420, 1440)
    ctx = cairo.Context(surf)
    rock_fill(ctx, 0, 0, 420, 1440, 17, "#2C2622", n=300, lo=12, hi=60)
    # make it tile vertically by mirroring the seam
    _CACHE["shaft"] = surf
    return surf


def pit_bg():
    if "pit" in _CACHE:
        return _CACHE["pit"]
    WW = 1600
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WW, H)
    ctx = cairo.Context(surf)
    rock_fill(ctx, 0, 0, WW, H, 21, "#2B2726", n=500, lo=14, hi=70)
    # dark tunnel mouth on the left, where the stranger lives
    ctx.move_to(0, 120)
    ctx.curve_to(180, 90, 330, 200, 360, 400)
    ctx.curve_to(370, 520, 330, 610, 300, 640)
    ctx.line_to(0, 640)
    ctx.close_path()
    g = cairo.LinearGradient(0, 0, 360, 0)
    g.add_color_stop_rgb(0, 0, 0, 0)
    g.add_color_stop_rgb(1, *rgb("#0C0A0A"))
    ctx.set_source(g)
    ctx.fill()
    # right wall (where he leans) closer and darker
    ctx.move_to(WW, 0)
    ctx.line_to(1110, 0)
    ctx.curve_to(1140, 200, 1080, 420, 1120, 640)
    ctx.line_to(WW, 640)
    ctx.close_path()
    src(ctx, "#211D1C")
    ctx.fill_preserve()
    src(ctx, "#0E0C0B")
    ctx.set_line_width(6)
    ctx.stroke()
    rnd = random.Random(23)
    for i in range(40):
        x = rnd.uniform(1130, WW)
        y = rnd.uniform(0, 620)
        r = rnd.uniform(12, 40)
        ellipse(ctx, x, y, r, r * 0.7)
        src(ctx, mix("#2E2826", "#000000", rnd.random() * 0.5))
        ctx.fill()
    # floor
    g = cairo.LinearGradient(0, 600, 0, H)
    g.add_color_stop_rgb(0, *rgb("#35302C"))
    g.add_color_stop_rgb(1, *rgb("#181513"))
    ctx.rectangle(0, 606, WW, H - 606)
    ctx.set_source(g)
    ctx.fill()
    for i in range(160):
        x = rnd.uniform(0, WW)
        y = rnd.uniform(612, 712)
        ellipse(ctx, x, y, rnd.uniform(5, 22), rnd.uniform(3, 7))
        src(ctx, mix("#4A433E", "#000000", rnd.random() * 0.5))
        ctx.fill()
    # rubble from the fall
    for i in range(26):
        x = rnd.uniform(460, 840)
        y = rnd.uniform(600, 650)
        r = rnd.uniform(8, 26)
        ellipse(ctx, x, y, r, r * 0.7)
        src(ctx, mix("#5A514A", "#000000", rnd.random() * 0.5))
        ctx.fill()
    # old bones
    for bx in (420, 1250):
        ctx.move_to(bx, 652)
        ctx.line_to(bx + 46, 646)
        src(ctx, "#CFC7B0")
        ctx.set_line_width(6)
        ctx.stroke()
    _CACHE["pit"] = surf
    return surf


MUSHROOMS = [(1180, 640, 1.1), (1290, 610, 0.8), (860, 662, 0.7), (1060, 676, 0.9), (520, 668, 0.6),
             (1450, 630, 1.2), (1380, 470, 0.7)]


def draw_mushrooms(ctx, t, glow=1.0):
    for i, (x, y, s) in enumerate(MUSHROOMS):
        pul = 0.85 + 0.15 * math.sin(t * 1.7 + i)
        g = cairo.RadialGradient(x, y - 20 * s, 0, x, y - 20 * s, 90 * s)
        g.add_color_stop_rgba(0, 0.3, 1, 0.9, 0.35 * glow * pul)
        g.add_color_stop_rgba(1, 0.3, 1, 0.9, 0)
        ctx.set_source(g)
        ctx.arc(x, y - 20 * s, 90 * s, 0, 2 * PI)
        ctx.fill()
        for k, (dx, hh, r) in enumerate(((-14, 26, 12), (6, 38, 16), (22, 20, 9))):
            ctx.move_to(x + dx * s, y)
            ctx.line_to(x + dx * s, y - hh * s)
            src(ctx, "#BFF7F0")
            ctx.set_line_width(4 * s)
            ctx.stroke()
            ctx.move_to(x + (dx - r) * s, y - hh * s)
            ctx.curve_to(x + (dx - r) * s, y - (hh + r) * s, x + (dx + r) * s, y - (hh + r) * s, x + (dx + r) * s,
                         y - hh * s)
            ctx.close_path()
            src(ctx, mix("#3EF2D8", "#FFFFFF", 0.2 * pul))
            ctx.fill()


# ---------------------------------------------------------------- lighting
def darkness(ctx, amb, lights, tint=(0.01, 0.01, 0.03)):
    """Darken everything except around lights. lights: [(x, y, r, strength)] in current coords."""
    if amb <= 0:
        return
    ctx.push_group()
    ctx.set_source_rgba(*tint, amb)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_DEST_OUT)
    for (x, y, r, k) in lights:
        if k <= 0 or r <= 0:
            continue
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, 0, 0, 0, k)
        g.add_color_stop_rgba(0.45, 0, 0, 0, k * 0.75)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(x, y, r, 0, 2 * PI)
        ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint()


def warm_glow(ctx, x, y, r, a, col=(1, 0.55, 0.15)):
    if a <= 0:
        return
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col, 0.28 * a)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * PI)
    ctx.fill()
    ctx.restore()


def vignette(ctx, a=0.6):
    g = cairo.RadialGradient(W / 2, H / 2, 260, W / 2, H / 2, 820)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    ctx.set_source(g)
    ctx.paint()


# ---------------------------------------------------------------- particles
def dust(ctx, x, y, t0, t, n=10, spread=120, col="#9C8F82", dur=1.6, seed=1, rise=60):
    dt = t - t0
    if dt < 0 or dt > dur:
        return
    rnd = random.Random(seed)
    for i in range(n):
        ang = rnd.uniform(PI, 2 * PI)
        sp = rnd.uniform(0.3, 1.0) * spread
        px = x + math.cos(ang) * sp * ease_out(dt / dur) * 1.4
        py = y + math.sin(ang) * sp * ease_out(dt / dur) * 0.4 - rise * dt / dur
        r = rnd.uniform(18, 40) * (0.6 + dt / dur)
        ellipse(ctx, px, py, r, r * 0.75)
        src(ctx, col, 0.45 * (1 - dt / dur))
        ctx.fill()


def debris(ctx, x, y, t0, t, n=14, seed=2, vx=(-300, 300), vy=(-500, -100), floor=640, col="#5A514A",
           size=(6, 18), g=1100):
    dt = t - t0
    if dt < 0:
        return
    rnd = random.Random(seed)
    for i in range(n):
        vxx = rnd.uniform(*vx)
        vyy = rnd.uniform(*vy)
        px = x + vxx * dt
        py = y + vyy * dt + g * dt * dt
        if floor is not None and py > floor:
            continue
        r = rnd.uniform(*size)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(dt * rnd.uniform(-8, 8))
        ctx.move_to(-r, -r * 0.5)
        ctx.line_to(r * 0.3, -r)
        ctx.line_to(r, r * 0.2)
        ctx.line_to(-r * 0.2, r * 0.8)
        ctx.close_path()
        fill_stroke(ctx, mix(col, "#000000", rnd.random() * 0.4), "#1A1512", 2)
        ctx.restore()


def sparks(ctx, x, y, t, n=12, seed=0, a=1.0):
    rnd = random.Random(seed + int(t * 30))
    for i in range(n):
        ang = rnd.uniform(-PI * 0.9, -PI * 0.1) + PI * (rnd.random() < 0.5)
        ln = rnd.uniform(10, 40)
        d = rnd.uniform(0, 40)
        sx, sy = x + math.cos(ang) * d, y + math.sin(ang) * d
        ctx.move_to(sx, sy)
        ctx.line_to(sx + math.cos(ang) * ln, sy + math.sin(ang) * ln)
        src(ctx, rnd.choice(["#FFE36A", "#FFB23F", "#FFFFFF"]), a)
        ctx.set_line_width(2.5)
        ctx.stroke()


def zzz(ctx, x, y, t, a=1.0):
    for i in range(3):
        u = (t * 0.45 + i / 3) % 1
        E.text(ctx, "Z", x + u * 60 + math.sin(u * 6) * 10, y - u * 120, 22 + u * 26, "#CFE8FF",
               outline="#0A0A12", olw=5, alpha=a * math.sin(u * PI))


# ---------------------------------------------------------------- cards
def title_card(ctx, t, title, sub, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    src(ctx, "#050405")
    ctx.paint()
    rnd = random.Random(3)
    for i in range(70):
        x0 = rnd.uniform(0, W)
        sp = rnd.uniform(20, 70)
        y = (rnd.uniform(0, H) - t * sp) % H
        x = x0 + math.sin(t + i) * 20
        r = rnd.uniform(1.5, 3.5)
        ellipse(ctx, x, y, r, r)
        src(ctx, "#FF8A3D", 0.4 + 0.4 * math.sin(t * 3 + i))
        ctx.fill()
    g = cairo.RadialGradient(640, 330, 30, 640, 330, 500)
    g.add_color_stop_rgba(0, 0.6, 0.12, 0.05, 0.35)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.paint()
    ctx.select_font_face(TITLE_FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    for txt, y, size, col in ((title, 330, 120, "#E8D9B8"), (sub, 420, 38, "#C9A06A")):
        ctx.set_font_size(size)
        ext = ctx.text_extents(txt)
        ctx.move_to(640 - ext.width / 2 - ext.x_bearing, y)
        ctx.text_path(txt)
        src(ctx, "#000000")
        ctx.set_line_width(8)
        ctx.stroke_preserve()
        src(ctx, col)
        ctx.fill()
    ctx.move_to(420, 360)
    ctx.line_to(860, 360)
    src(ctx, "#8A2A1A")
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def end_card(ctx, t, title, sub, a=1.0):
    title_card(ctx, t, title, sub, a)
