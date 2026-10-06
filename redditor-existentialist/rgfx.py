"""Graphics for 'Redditor Existentialist': the redditor, librarian Doubt, Anger the wall,
the bedroom, the chat screen, the void, the box and the stage."""
import math
import random

import cairo

import engine as E
from engine import (W, H, GROUND, PI, clamp, lerp, ease, ease_out, ellipse, rrect, src, mix, rgb,
                    fill_stroke, sparkle, text)

SKIN = "#D9A882"
SKIN_D = "#8A5A3A"

# ---------------------------------------------------------------- the redditor
E.KIND["redditor"] = dict(
    w=124, h=176, legh=34, n=2.6, taper=0.06, col="#5A6372", dark="#22262E",
    eye_y=-150, eye_dx=17, erx=10, ery=10, mouth_y=-121, mw=20, sh=(56, -110), hip=24, L=48,
    brow=(-4, -4), brow_raise=(-4, -4), lid=0.42, legw=(18, 12), legcol="#3B4A66", legdark="#1C2333",
    armw=(16, 10), handcol=SKIN, handdark=SKIN_D, handr=10, footr=(18, 9), foot="#E8E8E8")


def _redditor_hook(stage, ctx, c, k, t, top):
    fx = c["face"] * k["w"] * 0.1
    if stage == "body":
        # kangaroo pocket and drawstrings
        rrect(ctx, -34, -78, 68, 30, 10)
        src(ctx, mix(k["col"], "#000000", 0.18))
        ctx.fill()
        if c.get("hood", 1.0) > 0:
            # hood ring around the face
            ellipse(ctx, fx, -138, 58, 60)
            src(ctx, mix(k["col"], "#000000", 0.08))
            ctx.fill()
            ellipse(ctx, fx, -138, 58, 60)
            src(ctx, k["dark"])
            ctx.set_line_width(4)
            ctx.stroke()
        for sx in (-12, 12):
            ctx.move_to(fx + sx, -96)
            ctx.line_to(fx + sx * 1.1, -66)
            src(ctx, "#DADDE3")
            ctx.set_line_width(3)
            ctx.stroke()
        # face
        ellipse(ctx, fx, -136, 40, 44)
        src(ctx, SKIN)
        ctx.fill()
        ellipse(ctx, fx, -136, 40, 44)
        src(ctx, SKIN_D)
        ctx.set_line_width(2.5)
        ctx.stroke()
        # messy fringe
        ctx.move_to(fx - 38, -150)
        for i in range(8):
            xx = fx - 38 + i * 11
            ctx.line_to(xx + 5, -168 + (i % 2) * 8)
        ctx.line_to(fx + 40, -152)
        ctx.curve_to(fx + 34, -186, fx - 34, -186, fx - 38, -150)
        ctx.close_path()
        src(ctx, "#3A2A22")
        ctx.fill()
        # under-eye bags
        for side in (-1, 1):
            ctx.move_to(fx + side * k["eye_dx"] - 9, -138)
            ctx.curve_to(fx + side * k["eye_dx"] - 4, -134, fx + side * k["eye_dx"] + 4, -134,
                         fx + side * k["eye_dx"] + 9, -138)
            src(ctx, "#8E6A8A", 0.7)
            ctx.set_line_width(2.5)
            ctx.stroke()
        if c.get("glow", 0) > 0:
            g = cairo.RadialGradient(0, -80, 0, 0, -80, 40)
            g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.95 * c["glow"])
            g.add_color_stop_rgba(1, 1, 0.85, 0.4, 0)
            ctx.set_source(g)
            ctx.arc(0, -80, 40, 0, 2 * PI)
            ctx.fill()
            sparkle(ctx, 0, -80, 10 * c["glow"], "#FFFFFF")


E.HOOKS["redditor"] = _redditor_hook


def new_redditor(x, **kw):
    c = E.new_char("redditor", x, mouth="flat", mamt=0, brow=0.0)
    c.update(kw)
    return c


# ---------------------------------------------------------------- librarian Doubt
def _doubt_hook(stage, ctx, c, k, t, top):
    if stage == "post" and c.get("glasses"):
        fx = c["face"] * k["w"] * 0.1
        for side in (-1, 1):
            ellipse(ctx, fx + side * k["eye_dx"], k["eye_y"], 16, 15)
            src(ctx, "#2B1B4A")
            ctx.set_line_width(3)
            ctx.stroke()
        ctx.move_to(fx - k["eye_dx"] + 15, k["eye_y"] - 2)
        ctx.line_to(fx + k["eye_dx"] - 15, k["eye_y"] - 2)
        src(ctx, "#2B1B4A")
        ctx.set_line_width(3)
        ctx.stroke()
        if c.get("bun", True):
            ellipse(ctx, fx - 2, top - 8, 18, 14)
            fill_stroke(ctx, "#5B3A8F", "#2B1B4A", 3)
            ctx.move_to(fx - 22, top - 18)
            ctx.line_to(fx + 18, top + 2)
            src(ctx, "#E8B64A")
            ctx.set_line_width(3)
            ctx.stroke()
        if c.get("lip", 0) > 0:
            # trembling bottom lip
            ctx.save()
            my = k["mouth_y"] + 4
            ctx.translate(fx + math.sin(t * 40) * 1.2, my)
            ellipse(ctx, 0, 0, 12 * c["lip"], 6 * c["lip"])
            fill_stroke(ctx, "#E87AA4", "#7A1E52", 2)
            ctx.restore()
        if c.get("tears", 0) > 0:
            for side in (-1, 1):
                u = (t * 0.8 + (side + 1) * 0.3) % 1
                ellipse(ctx, fx + side * (k["eye_dx"] + 4), k["eye_y"] + 12 + u * 24, 3, 4.5)
                src(ctx, "#8FD8FF", c["tears"] * (1 - u))
                ctx.fill()
            for side in (-1, 1):
                ellipse(ctx, fx + side * k["eye_dx"], k["eye_y"] + 9, 10, 3)
                src(ctx, "#8FD8FF", 0.8 * c["tears"])
                ctx.fill()


E.HOOKS["doubt"] = _doubt_hook


def _book(ctx, hx, hy, wang, c, t):
    ctx.save()
    ctx.translate(hx, hy - 6)
    ctx.rotate(math.radians(wang))
    rrect(ctx, -22, -30, 44, 58, 4)
    fill_stroke(ctx, "#8E1F2F", "#3E0A14", 3)
    ctx.rectangle(-22, -30, 8, 58)
    src(ctx, "#5E1220")
    ctx.fill()
    ctx.rectangle(-8, -18, 26, 4)
    ctx.rectangle(-8, 12, 26, 4)
    src(ctx, "#E8B64A")
    ctx.fill()
    ctx.restore()


E.ITEMS["book"] = _book


def new_doubt(x, **kw):
    c = E.new_char("doubt", x, mouth="smile", mamt=0.4, glasses=True, itemR="book", wandR=-10)
    c["hr"] = (48, -96)
    c.update(kw)
    return c


# ---------------------------------------------------------------- Anger the wall
def draw_anger_wall(ctx, x, y, s, t, a=None):
    a = a or {}
    ctx.save()
    ctx.translate(x + math.sin(t * 50) * a.get("shake", 0), y)
    ctx.scale(s, s)
    alpha = a.get("alpha", 1.0)
    if alpha < 1:
        ctx.push_group()
    w, h = 300, 430
    flick = math.sin(t * 9) * 4
    # flame crest
    ctx.move_to(-90, -h + 6)
    for i, (dx, hh) in enumerate(((-60, 60), (-25, 90), (10, 70), (45, 100), (80, 55))):
        ctx.line_to(dx + flick * (1 if i % 2 else -1), -h - hh)
        ctx.line_to(dx + 18, -h + 4)
    ctx.line_to(100, -h + 6)
    ctx.close_path()
    fill_stroke(ctx, "#FF8A3D", "#7E1A12", 4)
    # bricks
    rrect(ctx, -w / 2, -h, w, h, 14)
    src(ctx, "#B8382E")
    ctx.fill()
    ctx.save()
    rrect(ctx, -w / 2, -h, w, h, 14)
    ctx.clip()
    bh, bw = 36, 74
    for r in range(int(h / bh) + 1):
        off = (bw / 2) if r % 2 else 0
        for col in range(-1, int(w / bw) + 2):
            bx = -w / 2 + col * bw - off
            by = -h + r * bh
            rrect(ctx, bx + 3, by + 3, bw - 6, bh - 6, 5)
            src(ctx, mix("#D9483A", "#7E1A12", ((r * 7 + col * 3) % 5) / 12))
            ctx.fill()
    ctx.restore()
    rrect(ctx, -w / 2, -h, w, h, 14)
    src(ctx, "#5E140E")
    ctx.set_line_width(7)
    ctx.stroke()
    # face plate
    fy = -h + 150
    look = a.get("px", 0.0)
    facepalm = a.get("facepalm", 0.0)
    # eyes
    for side in (-1, 1):
        ex = side * 50
        ellipse(ctx, ex, fy, 26, 28 * (1 - 0.5 * a.get("squint", 0)))
        fill_stroke(ctx, "#FFFFFF", "#2A0A06", 4)
        ellipse(ctx, ex + look * 9, fy + 2, 10, 11)
        src(ctx, "#2A0A06")
        ctx.fill()
        ang = math.radians(26 - a.get("brow", 0) * 16)
        bx, by = ex, fy - 40 - a.get("brow", 0) * 6
        ctx.move_to(bx - side * 30 * math.cos(ang), by + 30 * math.sin(ang))
        ctx.line_to(bx + side * 30 * math.cos(ang), by - 30 * math.sin(ang))
        src(ctx, "#2A0A06")
        ctx.set_line_width(12)
        ctx.stroke()
    # mouth
    my = fy + 90
    talk = a.get("talk", 0.0)
    if talk > 0.06 or a.get("shout", 0) > 0:
        op = max(talk, a.get("shout", 0))
        ellipse(ctx, 0, my, 54, 10 + 36 * op)
        fill_stroke(ctx, "#4A0A10", "#2A0A06", 4)
        ctx.rectangle(-40, my - 10 - 34 * op, 80, 10)
        src(ctx, "#FFFFFF")
        ctx.fill()
    else:
        ctx.move_to(-56, my + 10)
        ctx.curve_to(-20, my - 16, 20, my - 16, 56, my + 10)
        src(ctx, "#2A0A06")
        ctx.set_line_width(9)
        ctx.stroke()
    # arms
    for side in (-1, 1):
        sx, sy = side * w / 2, -h + 210
        if facepalm > 0 and side > 0:
            tx, ty = lerp(sx + 70, 40, facepalm), lerp(sy + 90, fy, facepalm)
        elif a.get("point", 0) > 0 and side > 0:
            tx, ty = sx + 150, sy - 60
        elif a.get("hips", 0) > 0:
            tx, ty = sx + side * 10, sy + 110
        else:
            tx, ty = sx + side * 60, sy + 120
        ctx.move_to(sx, sy)
        ctx.line_to(tx, ty)
        src(ctx, "#5E140E")
        ctx.set_line_width(46)
        ctx.stroke()
        ctx.move_to(sx, sy)
        ctx.line_to(tx, ty)
        src(ctx, "#B8382E")
        ctx.set_line_width(34)
        ctx.stroke()
        rrect(ctx, tx - 34, ty - 30, 68, 60, 14)
        fill_stroke(ctx, "#9E9E9E", "#3A3A3A", 5)
        for k in range(3):
            ctx.move_to(tx - 20 + k * 20, ty - 26)
            ctx.line_to(tx - 20 + k * 20, ty + 26)
        src(ctx, "#3A3A3A")
        ctx.set_line_width(3)
        ctx.stroke()
    # legs / base
    for side in (-1, 1):
        rrect(ctx, side * 80 - 40, -16, 80, 26, 8)
        fill_stroke(ctx, "#7A7A7A", "#3A3A3A", 4)
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


# ---------------------------------------------------------------- the bedroom
_CACHE = {}


def bedroom_bg():
    if "bed" in _CACHE:
        return _CACHE["bed"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *rgb("#1A1D2B"))
    g.add_color_stop_rgb(1, *rgb("#0E1018"))
    ctx.set_source(g)
    ctx.paint()
    # window with night city
    rrect(ctx, 820, 90, 340, 240, 6)
    src(ctx, "#0B1430")
    ctx.fill()
    rnd = random.Random(2)
    for i in range(18):
        bx = 830 + i * 18
        bh = rnd.uniform(40, 150)
        ctx.rectangle(bx, 330 - bh, 16, bh)
        src(ctx, "#121A3A")
        ctx.fill()
        for j in range(int(bh / 16)):
            if rnd.random() < 0.25:
                ctx.rectangle(bx + 4, 330 - bh + 6 + j * 16, 5, 6)
                src(ctx, "#F2D27A", 0.7)
                ctx.fill()
    ellipse(ctx, 1110, 130, 18, 18)
    src(ctx, "#E8E4D0", 0.8)
    ctx.fill()
    rrect(ctx, 820, 90, 340, 240, 6)
    src(ctx, "#2A2E40")
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.move_to(990, 90)
    ctx.line_to(990, 330)
    ctx.stroke()
    # poster
    rrect(ctx, 120, 110, 150, 200, 4)
    fill_stroke(ctx, "#232838", "#14171F", 4)
    text(ctx, "NOTHING", 195, 190, 26, "#5A6372")
    text(ctx, "MATTERS", 195, 222, 26, "#5A6372")
    text(ctx, "(probably)", 195, 254, 16, "#3E4555")
    # floor
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#15171F")
    ctx.fill()
    # bed (unmade) on the right
    rrect(ctx, 880, 470, 380, 140, 14)
    fill_stroke(ctx, "#2E3448", "#151824", 4)
    ctx.move_to(880, 500)
    ctx.curve_to(960, 450, 1060, 540, 1260, 480)
    ctx.line_to(1260, 560)
    ctx.line_to(880, 560)
    ctx.close_path()
    src(ctx, "#4A5270")
    ctx.fill()
    # desk
    rrect(ctx, 260, 430, 440, 22, 4)
    fill_stroke(ctx, "#3A3326", "#1A160F", 3)
    ctx.rectangle(280, 452, 16, 150)
    ctx.rectangle(664, 452, 16, 150)
    src(ctx, "#2A251B")
    ctx.fill()
    # cans and pizza box
    for cx in (600, 628, 645):
        rrect(ctx, cx, 396, 16, 34, 4)
        fill_stroke(ctx, "#3FBF7F", "#1E5E3E", 2)
    ctx.move_to(70, 610)
    ctx.line_to(230, 610)
    ctx.line_to(220, 590)
    ctx.line_to(80, 590)
    ctx.close_path()
    fill_stroke(ctx, "#8A6A44", "#4A3418", 3)
    # laundry pile
    for i, col in enumerate(("#6B4E8E", "#3E6E8E", "#8E5A3E", "#5A6372")):
        ellipse(ctx, 760 + i * 22, 600 - (i % 2) * 10, 40, 16)
        src(ctx, col)
        ctx.fill()
    _CACHE["bed"] = surf
    return surf


def draw_monitor(ctx, t, glow=1.0, x=480, y=300):
    # stand
    ctx.rectangle(x - 10, y + 80, 20, 50)
    src(ctx, "#1A1A1F")
    ctx.fill()
    rrect(ctx, x - 50, y + 124, 100, 10, 4)
    ctx.fill()
    rrect(ctx, x - 130, y - 80, 260, 170, 8)
    fill_stroke(ctx, "#101015", "#000000", 4)
    rrect(ctx, x - 120, y - 70, 240, 150, 4)
    g = cairo.LinearGradient(0, y - 70, 0, y + 80)
    g.add_color_stop_rgb(0, *rgb("#1E2433"))
    g.add_color_stop_rgb(1, *rgb("#141822"))
    ctx.set_source(g)
    ctx.fill()
    # mini chat bubbles
    for i in range(4):
        bw = 120 + (i * 37) % 60
        bx = x - 108 if i % 2 else x + 108 - bw
        rrect(ctx, bx, y - 58 + i * 34, bw, 22, 8)
        src(ctx, "#3A4A6A" if i % 2 else "#2E7D74", 0.9)
        ctx.fill()
    if glow > 0:
        g = cairo.RadialGradient(x, y, 30, x, y, 420)
        g.add_color_stop_rgba(0, 0.5, 0.7, 1, 0.22 * glow)
        g.add_color_stop_rgba(1, 0.5, 0.7, 1, 0)
        ctx.set_source(g)
        ctx.arc(x, y, 420, 0, 2 * PI)
        ctx.fill()


def draw_keyboard(ctx, x, y):
    """Keyboard and mouse sitting on the desk top (y = desk surface)."""
    ctx.move_to(x - 62, y)
    ctx.line_to(x + 62, y)
    ctx.line_to(x + 54, y - 12)
    ctx.line_to(x - 54, y - 12)
    ctx.close_path()
    fill_stroke(ctx, "#2A2E3A", "#0E1016", 2)
    for row in range(2):
        for k in range(9):
            kx = x - 48 + k * 11 + row * 4
            ctx.rectangle(kx, y - 10 + row * 5, 8, 3)
    src(ctx, "#6E7A94")
    ctx.fill()
    ellipse(ctx, x - 82, y - 5, 9, 5)
    fill_stroke(ctx, "#2A2E3A", "#0E1016", 2)


def draw_chair(ctx, x):
    rrect(ctx, x - 50, 380, 30, 150, 10)
    fill_stroke(ctx, "#2A2A33", "#111", 3)
    rrect(ctx, x - 60, 500, 120, 22, 8)
    fill_stroke(ctx, "#2A2A33", "#111", 3)
    ctx.rectangle(x - 6, 522, 12, 60)
    src(ctx, "#111")
    ctx.fill()
    ctx.move_to(x - 50, 600)
    ctx.line_to(x + 50, 600)
    ctx.set_line_width(8)
    ctx.stroke()


def desaturate(ctx, amt):
    if amt <= 0:
        return
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_HSL_SATURATION)
    ctx.set_source_rgba(0.5, 0.5, 0.5, amt)
    ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------- chat screen
def draw_chat(ctx, t, msgs, title="Journey Into Your Emotional World"):
    """msgs: list of (who, text, alpha, typed_fraction) newest last."""
    src(ctx, "#0F1219")
    ctx.paint()
    rrect(ctx, 140, 30, 1000, 660, 18)
    fill_stroke(ctx, "#171B26", "#262C3C", 3)
    rrect(ctx, 140, 30, 1000, 62, 18)
    src(ctx, "#1E2433")
    ctx.fill()
    ctx.rectangle(140, 70, 1000, 22)
    ctx.fill()
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        ellipse(ctx, 176 + i * 24, 61, 7, 7)
        src(ctx, col)
        ctx.fill()
    text(ctx, title, 640, 70, 24, "#AEB8CC")
    # bubbles bottom-up
    y = 600
    for who, s, a, frac in reversed(msgs):
        if a <= 0:
            continue
        shown = s[:max(1, int(len(s) * frac))] if frac < 1 else s
        lines = E.wrap(ctx, shown, 24, 560)
        bh = 36 * len(lines) + 20
        bw = max(E.text_width(ctx, ln, 24) for ln in lines) + 40
        y -= bh
        if y < 100:
            break
        if who == "user":
            bx = 1100 - bw
            col, tcol = "#2E5A9E", "#FFFFFF"
        else:
            bx = 180
            col, tcol = "#2A3142", "#D8E0F0"
        rrect(ctx, bx, y, bw, bh, 16)
        src(ctx, col, a)
        ctx.fill()
        for i, ln in enumerate(lines):
            text(ctx, ln, bx + 20, y + 38 + i * 36, 24, tcol, align="left", alpha=a)
        if who == "ai":
            text(ctx, "AI", 160, y + 28, 16, "#6E7A94", align="center", alpha=a)
        y -= 18
    # input bar
    rrect(ctx, 180, 618, 920, 50, 25)
    fill_stroke(ctx, "#1E2433", "#2E3548", 2)
    if int(t * 2) % 2 == 0:
        ctx.rectangle(206, 630, 2, 26)
        src(ctx, "#AEB8CC")
        ctx.fill()


# ---------------------------------------------------------------- the void
def draw_void_space(ctx, t, vx=900, vy=330, vr=170, pull=1.0, barrier=0.0, bx=620):
    g = cairo.RadialGradient(640, 360, 50, 640, 360, 900)
    g.add_color_stop_rgb(0, *rgb("#1A1426"))
    g.add_color_stop_rgb(1, *rgb("#05040A"))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(4)
    # dust being pulled in
    for i in range(90):
        a0 = rnd.uniform(0, 2 * PI)
        r0 = rnd.uniform(220, 700)
        sp = rnd.uniform(0.05, 0.16) * pull
        u = (t * sp + rnd.random()) % 1
        r = r0 * (1 - u) + vr * 0.6
        a = a0 + u * 3
        px, py = vx + math.cos(a) * r, vy + math.sin(a) * r * 0.6
        ellipse(ctx, px, py, 1.6, 1.6)
        src(ctx, "#9C8FB8", 0.6 * (1 - u))
        ctx.fill()
    # ground ledge where the redditor stands
    ctx.move_to(0, 612)
    ctx.curve_to(300, 600, 500, 620, 760, 612)
    ctx.line_to(760, 720)
    ctx.line_to(0, 720)
    ctx.close_path()
    src(ctx, "#15111E")
    ctx.fill()
    ctx.move_to(0, 612)
    ctx.curve_to(300, 600, 500, 620, 760, 612)
    src(ctx, "#3A2E52")
    ctx.set_line_width(3)
    ctx.stroke()
    # the void itself
    for k in range(7):
        a0 = t * 0.35 + k * 2 * PI / 7
        ctx.move_to(vx, vy)
        for i in range(1, 40):
            r = vr * 0.2 + i * vr * 0.05
            a = a0 + i * 0.12
            ctx.line_to(vx + math.cos(a) * r, vy + math.sin(a) * r * 0.7)
        src(ctx, "#4B3A78", 0.35)
        ctx.set_line_width(10)
        ctx.stroke()
    g = cairo.RadialGradient(vx, vy, vr * 0.2, vx, vy, vr * 1.3)
    g.add_color_stop_rgba(0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0.55, 0, 0, 0, 0.95)
    g.add_color_stop_rgba(0.75, 0.3, 0.2, 0.55, 0.5)
    g.add_color_stop_rgba(1, 0.1, 0.05, 0.2, 0)
    ctx.set_source(g)
    ctx.arc(vx, vy, vr * 1.3, 0, 2 * PI)
    ctx.fill()
    if barrier > 0:
        draw_barrier(ctx, bx, 612, barrier, t)


def draw_barrier(ctx, x, y, rise=1.0, t=0.0, w=170, h=420, col="#5E6066", shake=0.0):
    hh = h * ease_out(rise)
    if hh <= 1:
        return
    ctx.save()
    ctx.translate(x + math.sin(t * 60) * shake, y)
    rrect(ctx, -w / 2, -hh, w, hh + 8, 8)
    g = cairo.LinearGradient(-w / 2, 0, w / 2, 0)
    g.add_color_stop_rgb(0, *rgb("#45474D"))
    g.add_color_stop_rgb(0.5, *rgb(col))
    g.add_color_stop_rgb(1, *rgb("#3A3C42"))
    ctx.set_source(g)
    ctx.fill_preserve()
    src(ctx, "#202126")
    ctx.set_line_width(5)
    ctx.stroke()
    rnd = random.Random(int(x))
    for i in range(6):
        cy = -rnd.uniform(20, hh - 20)
        ctx.move_to(-w / 2 + rnd.uniform(10, 40), cy)
        ctx.line_to(-w / 2 + rnd.uniform(60, 120), cy + rnd.uniform(-20, 20))
        src(ctx, "#2E3036", 0.7)
        ctx.set_line_width(2)
        ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------- the box
def draw_box_interior(ctx, t, light=1.0, squeeze=0.0, pulse=0.0):
    src(ctx, "#050506")
    ctx.paint()
    m = 160 + squeeze * 60
    bx0, by0, bx1, by1 = 420 + squeeze * 40, 150 + squeeze * 20, 860 - squeeze * 40, 520 - squeeze * 6
    pts = dict(tl=(m - 160 + 40, 0), tr=(W - (m - 160) - 40, 0), bl=(m - 160 + 40, H), br=(W - (m - 160) - 40, H))
    # walls as trapezoids
    def quad(a, b, c_, d, col):
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.line_to(*c_)
        ctx.line_to(*d)
        ctx.close_path()
        src(ctx, col)
        ctx.fill_preserve()
        src(ctx, "#000000", 0.6)
        ctx.set_line_width(3)
        ctx.stroke()
    L, R = pts["tl"][0], pts["tr"][0]
    quad((L, 0), (bx0, by0), (bx0, by1), (L, H), "#1E1F24")       # left wall
    quad((R, 0), (bx1, by0), (bx1, by1), (R, H), "#1B1C21")       # right wall
    quad((L, 0), (R, 0), (bx1, by0), (bx0, by0), "#141519")       # ceiling
    quad((L, H), (R, H), (bx1, by1), (bx0, by1), "#26272D")       # floor
    ctx.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
    src(ctx, "#222329")
    ctx.fill()
    # outside the box edges: pure black
    ctx.rectangle(0, 0, L, H)
    ctx.rectangle(R, 0, W - R, H)
    src(ctx, "#000000")
    ctx.fill()
    # dim light from above
    g = cairo.RadialGradient(640, 200, 20, 640, 420, 520)
    g.add_color_stop_rgba(0, 0.8, 0.8, 0.95, 0.22 * light)
    g.add_color_stop_rgba(1, 0.8, 0.8, 0.95, 0)
    ctx.set_source(g)
    ctx.paint()
    if pulse > 0:
        g = cairo.RadialGradient(640, 430, 10, 640, 430, 300)
        g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.25 * pulse)
        g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
        ctx.set_source(g)
        ctx.paint()


def draw_box_back(ctx, t, rx, close):
    u = ease(clamp((close - 0.3) / 0.5))
    if u > 0:
        ctx.rectangle(rx - 150, 640 - 480 * u, 300, 480 * u)
        src(ctx, "#3E4046")
        ctx.fill()
        ctx.rectangle(rx - 150, 640 - 480 * u, 300, 480 * u)
        src(ctx, "#202126")
        ctx.set_line_width(4)
        ctx.stroke()


def draw_box_exterior(ctx, t, rx, close):
    """Side slabs and lid closing around the redditor at world x=rx. close: 0..1"""
    for i, (dx, delay) in enumerate(((-1, 0.0), (1, 0.15))):
        u = ease(clamp((close - delay) / 0.6))
        x = rx + dx * lerp(700, 150, u)
        draw_barrier(ctx, x, 640, 1.0, t, w=90, h=480, col="#55575D")
    # lid comes down
    u = ease(clamp((close - 0.6) / 0.4))
    if u > 0:
        y = lerp(-200, 150, u)
        rrect(ctx, rx - 200, y, 400, 26, 6)
        fill_stroke(ctx, "#5E6066", "#202126", 4)


# ---------------------------------------------------------------- warm stage (part 3)
def stage_room(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *rgb("#F2C77E"))
    g.add_color_stop_rgb(1, *rgb("#E59A5A"))
    ctx.set_source(g)
    ctx.paint()
    for i in range(0, W, 80):
        ctx.rectangle(i, 0, 40, 540)
        src(ctx, "#FFFFFF", 0.06)
        ctx.fill()
    ctx.rectangle(0, 540, W, 180)
    src(ctx, "#9C6440")
    ctx.fill()
    for i in range(0, W, 90):
        ctx.move_to(i, 540)
        ctx.line_to(i - 50, H)
        src(ctx, "#6E4228", 0.5)
        ctx.set_line_width(2)
        ctx.stroke()
    # string lights
    for i in range(18):
        x = 40 + i * 70
        y = 60 + math.sin(i * 0.9) * 12
        on = 0.6 + 0.4 * math.sin(t * 3 + i)
        g = cairo.RadialGradient(x, y, 0, x, y, 20)
        g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.8 * on)
        g.add_color_stop_rgba(1, 1, 0.9, 0.5, 0)
        ctx.set_source(g)
        ctx.arc(x, y, 20, 0, 2 * PI)
        ctx.fill()
        ellipse(ctx, x, y, 5, 6)
        src(ctx, "#FFF3C4")
        ctx.fill()
    text(ctx, "THE EMOTIONAL FAMILY THEATER", 640, 140, 34, "#7A2E1A", outline="#FFE7B8", olw=6)


def draw_cardboard_wall(ctx, x, y, t, fallen=0.0, label="WALL"):
    """Prop wall that tips over backwards, showing it was cardboard."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(1, max(0.05, math.cos(fallen * PI / 2)))
    rrect(ctx, -90, -300, 180, 300, 6)
    src(ctx, "#5E6066")
    ctx.fill()
    if fallen > 0.3:
        rrect(ctx, -90, -300, 180, 300, 6)
        src(ctx, "#C49A64", clamp((fallen - 0.3) / 0.3))
        ctx.fill()
        text(ctx, label, 0, -150, 30, "#7A5A30", alpha=clamp((fallen - 0.3) / 0.3))
    ctx.restore()


def pov_hand(ctx, x, y, ang=0.0, open_=True, sleeve="#2E7D74"):
    """'My' arm entering from the bottom of the frame."""
    ctx.save()
    ctx.move_to(x + 80, H + 80)
    ctx.line_to(x + 10, y + 50)
    src(ctx, sleeve)
    ctx.set_line_width(80)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ellipse(ctx, 0, 0, 44, 50)
    fill_stroke(ctx, "#E2B38F", "#A9775A", 3)
    if open_:
        for i, (fx, fl) in enumerate(((-30, 46), (-12, 62), (8, 64), (26, 56))):
            rrect(ctx, fx - 8, -40 - fl, 16, fl + 10, 8)
            fill_stroke(ctx, "#E2B38F", "#A9775A", 3)
        ctx.save()
        ctx.translate(40, 0)
        ctx.rotate(-0.7)
        rrect(ctx, -8, -44, 16, 44, 8)
        fill_stroke(ctx, "#E2B38F", "#A9775A", 3)
        ctx.restore()
    ctx.restore()


# ---------------------------------------------------------------- clock
def draw_crisis_clock(ctx, x, y, t, secs, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    rrect(ctx, -250, -90, 500, 180, 18)
    fill_stroke(ctx, "#15151C", "#E0283F", 6)
    text(ctx, "NEXT EXISTENTIAL CRISIS IN", 0, -44, 26, "#FFB3B3")
    d = int(secs // 86400)
    hh = int(secs % 86400 // 3600)
    mm = int(secs % 3600 // 60)
    ss = int(secs % 60)
    text(ctx, f"{d}d {hh:02d}:{mm:02d}:{ss:02d}", 0, 40, 64, "#FF3B4F")
    ctx.restore()


# ---------------------------------------------------------------- cards
def title_card(ctx, t, title, sub, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    src(ctx, "#0B0D14")
    ctx.paint()
    rnd = random.Random(8)
    for i in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ellipse(ctx, x, y, 1.5, 1.5)
        src(ctx, "#8C96B8", 0.3 + 0.3 * math.sin(t * 2 + i))
        ctx.fill()
    # a lonely box in the middle
    rrect(ctx, 590, 470, 100, 100, 6)
    fill_stroke(ctx, "#2A2E3A", "#5A6372", 3)
    text(ctx, title, 640, 300, 70, "#E8ECF4", outline="#000000", olw=8)
    text(ctx, sub, 640, 380, 34, "#8FA6C8", outline="#000000", olw=6)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def end_card(ctx, t, title, sub, note=None, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    src(ctx, "#0B0D14")
    ctx.paint()
    text(ctx, title, 640, 320, 74, "#E8ECF4", outline="#000000", olw=8)
    if sub:
        text(ctx, sub, 640, 390, 32, "#8FA6C8")
    if note:
        for i, ln in enumerate(note):
            text(ctx, ln, 640, 560 + i * 34, 22, "#9AA3B8")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
