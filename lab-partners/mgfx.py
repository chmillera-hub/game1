"""Characters, props and sets for Lab Partners."""
import math
import random

import cairo

import engine as E
from engine import W, H, PI, clamp, lerp, ease, ellipse, rrect, src, mix, rgb, fill_stroke, sparkle, text
import rgfx  # noqa: F401  (librarian Doubt, the book item)

GROUND = 612


# ---------------------------------------------------------------- Boredom, mad scientist
def _boredom_hook(stage, ctx, c, k, t, top):
    if not c.get("lab"):
        return
    fx = c["face"] * k["w"] * 0.1
    if stage == "pre":
        # wild hair
        for i in range(7):
            a = -PI / 2 + (i - 3) * 0.32 + math.sin(t * 3 + i) * 0.06
            ctx.move_to(fx + math.cos(a) * 30, top + 30 + math.sin(a) * 10)
            ctx.line_to(fx + math.cos(a) * 66, top + 26 + math.sin(a) * 46)
            src(ctx, "#E8E8F0")
            ctx.set_line_width(10)
            ctx.stroke()
    elif stage == "body":
        # lab coat over the lower body
        ctx.move_to(-66, -72)
        ctx.curve_to(-40, -86, 40, -86, 66, -72)
        ctx.line_to(70, -22)
        ctx.line_to(-70, -22)
        ctx.close_path()
        fill_stroke(ctx, "#F4F6F8", "#8A98A4", 3)
        for side in (-1, 1):
            ctx.move_to(side * 8, -80)
            ctx.line_to(side * 26, -50)
            ctx.line_to(side * 10, -24)
        src(ctx, "#8A98A4")
        ctx.set_line_width(3)
        ctx.stroke()
        rrect(ctx, 30, -54, 20, 16, 3)
        src(ctx, "#8A98A4")
        ctx.set_line_width(2)
        ctx.stroke()
        for i, col in enumerate(("#D9483A", "#3E6AA0")):
            ctx.rectangle(34 + i * 6, -64, 3, 12)
            src(ctx, col)
            ctx.fill()
    elif stage == "post":
        gy = k["eye_y"] - 34
        ctx.rectangle(fx - 62, gy - 5, 124, 10)
        src(ctx, "#3A3A44")
        ctx.fill()
        for side in (-1, 1):
            ellipse(ctx, fx + side * 22, gy, 17, 14)
            fill_stroke(ctx, "#8FD8FF", "#3A3A44", 4)
            ellipse(ctx, fx + side * 22 - 5, gy - 4, 4, 3)
            src(ctx, "#FFFFFF", 0.8)
            ctx.fill()


E.HOOKS["boredom"] = _boredom_hook


def new_boredom(x, **kw):
    c = E.new_char("boredom", x, mouth="flat", lab=True, lid=0.3)
    c.update(kw)
    return c


def new_doubt(x, **kw):
    return rgfx.new_doubt(x, **kw)


# ---------------------------------------------------------------- Lord Vex and friends
def make_kind(name, col, dark, w=118, h=200, extra=None):
    E.KIND[name] = dict(w=w, h=h, legh=30, n=2.6, taper=0.12, col=col, dark=dark,
                        eye_y=-h * 0.85 - 10, eye_dx=w * 0.15, erx=11, ery=12, mouth_y=-h * 0.85 + 24,
                        mw=26, sh=(w * 0.46, -h * 0.6), hip=w * 0.18, L=w * 0.46, brow=(28, 28),
                        brow_raise=(0, 0), lid=0.15, legw=(14, 9), legcol=mix(dark, "#000000", 0.2),
                        legdark="#0A0610", footr=(18, 9), foot="#111111", browlen=22, browlw=5)
    if extra:
        E.KIND[name].update(extra)


make_kind("vex", "#4A4A5C", "#141420")
make_kind("heir", "#2A6A6A", "#0E2E2E", w=96, h=160)
make_kind("minion", "#7ABA4A", "#2E5A1E", w=80, h=110, extra=dict(brow=(0, 0), lid=0.0))
make_kind("goon1", "#C8483A", "#4A120E", w=120, h=170)
make_kind("goon2", "#3A6AC8", "#0E1E4A", w=110, h=180)
make_kind("goon3", "#C8A83A", "#4A3A0E", w=130, h=160)
make_kind("council", "#5A5A66", "#22222A", w=110, h=170, extra=dict(brow=(10, 10), lid=0.5))


def _vex_hook(stage, ctx, c, k, t, top):
    fx = c["face"] * k["w"] * 0.1
    if stage == "pre" and c.get("cape", True):
        sway = math.sin(t * 2) * 6
        ctx.move_to(-k["w"] * 0.42, -k["h"] * 0.78)
        ctx.line_to(k["w"] * 0.42, -k["h"] * 0.78)
        ctx.curve_to(k["w"] * 0.7, -k["h"] * 0.4, k["w"] * 0.75 + sway, -20, k["w"] * 0.7 + sway, -6)
        ctx.line_to(-k["w"] * 0.7 + sway, -6)
        ctx.curve_to(-k["w"] * 0.75 + sway, -20, -k["w"] * 0.7, -k["h"] * 0.4, -k["w"] * 0.42, -k["h"] * 0.78)
        ctx.close_path()
        fill_stroke(ctx, "#8A1A2A", "#3A0610", 4)
    elif stage == "body":
        # spiky high collar
        cy = -k["h"] * 0.62
        ctx.move_to(-k["w"] * 0.42, cy)
        ctx.line_to(-k["w"] * 0.5, cy - 46)
        ctx.line_to(-k["w"] * 0.22, cy - 8)
        ctx.close_path()
        ctx.move_to(k["w"] * 0.42, cy)
        ctx.line_to(k["w"] * 0.5, cy - 46)
        ctx.line_to(k["w"] * 0.22, cy - 8)
        ctx.close_path()
        fill_stroke(ctx, "#8A1A2A", "#3A0610", 3)
        # emblem
        E.star_path(ctx, 0, -k["h"] * 0.4, 14, 6)
        src(ctx, "#C8F24A")
        ctx.fill()
    elif stage == "post":
        my = k["mouth_y"] - 8
        for side in (-1, 1):
            ctx.move_to(fx, my)
            ctx.curve_to(fx + side * 16, my - 8, fx + side * 26, my + 6, fx + side * 36, my - 10)
            ctx.curve_to(fx + side * 38, my - 18, fx + side * 30, my - 18, fx + side * 32, my - 12)
            src(ctx, "#1A0A1A")
            ctx.set_line_width(5)
            ctx.stroke()
        if c.get("blush", 0) > 0:
            for side in (-1, 1):
                ellipse(ctx, fx + side * (k["eye_dx"] + 10), k["eye_y"] + 22, 12, 7)
                src(ctx, "#FF6FAE", 0.75 * c["blush"])
                ctx.fill()
        if c.get("tears", 0) > 0:
            for side in (-1, 1):
                u = (t * 0.8 + (side + 1) * 0.3) % 1
                ellipse(ctx, fx + side * (k["eye_dx"] + 4), k["eye_y"] + 12 + u * 30, 3.5, 5)
                src(ctx, "#8FD8FF", c["tears"] * (1 - u))
                ctx.fill()
            for side in (-1, 1):
                ellipse(ctx, fx + side * k["eye_dx"], k["eye_y"] + 10, 11, 3.5)
                src(ctx, "#8FD8FF", 0.8 * c["tears"])
                ctx.fill()
        if c.get("crown"):
            ctx.move_to(fx - 30, top + 2)
            for i in range(5):
                ctx.line_to(fx - 30 + i * 15, top - 26 if i % 2 == 0 else top - 8)
            ctx.line_to(fx + 30, top + 2)
            ctx.close_path()
            fill_stroke(ctx, "#E8C84A", "#7A5E14", 3)


def _minion_hook(stage, ctx, c, k, t, top):
    if stage == "post":
        ctx.move_to(-k["w"] * 0.48, top + 26)
        ctx.curve_to(-k["w"] * 0.48, top - 14, k["w"] * 0.48, top - 14, k["w"] * 0.48, top + 26)
        ctx.close_path()
        fill_stroke(ctx, "#8A8A94", "#3A3A44", 3)


def _goon_hook(stage, ctx, c, k, t, top):
    if stage == "body":
        fx = c["face"] * k["w"] * 0.1
        rrect(ctx, fx - k["eye_dx"] - 20, k["eye_y"] - 14, (k["eye_dx"] + 20) * 2, 28, 12)
        src(ctx, "#111111")
        ctx.fill()


def _council_hook(stage, ctx, c, k, t, top):
    if stage == "body":
        fx = c["face"] * k["w"] * 0.1
        ctx.move_to(-k["w"] * 0.52, -40)
        ctx.curve_to(-k["w"] * 0.55, top - 30, k["w"] * 0.55, top - 30, k["w"] * 0.52, -40)
        ctx.curve_to(k["w"] * 0.3, top + 30, -k["w"] * 0.3, top + 30, -k["w"] * 0.52, -40)
        ctx.close_path()
        src(ctx, "#2A2A33")
        ctx.fill()


E.HOOKS["vex"] = _vex_hook
E.HOOKS["heir"] = _vex_hook
E.HOOKS["minion"] = _minion_hook
for _g in ("goon1", "goon2", "goon3"):
    E.HOOKS[_g] = _goon_hook
E.HOOKS["council"] = _council_hook


def new_char(kind, x, **kw):
    c = E.new_char(kind, x, mouth="smirk", mamt=0.6, brow=-0.6)
    c.update(kw)
    return c


# ---------------------------------------------------------------- props
def _vial(ctx, hx, hy, wang, c, t):
    draw_vial(ctx, hx, hy - 30, 0.0, t)


E.ITEMS["vial"] = _vial


def draw_vial(ctx, x, y, ang, t, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.scale(s, s)
    g = cairo.RadialGradient(0, 6, 2, 0, 6, 50)
    g.add_color_stop_rgba(0, 0.5, 1, 0.4, 0.5)
    g.add_color_stop_rgba(1, 0.5, 1, 0.4, 0)
    ctx.set_source(g)
    ctx.arc(0, 6, 50, 0, 2 * PI)
    ctx.fill()
    ctx.move_to(-8, -30)
    ctx.line_to(-8, -10)
    ctx.line_to(-22, 22)
    ctx.curve_to(-24, 30, 24, 30, 22, 22)
    ctx.line_to(8, -10)
    ctx.line_to(8, -30)
    ctx.close_path()
    src(ctx, "#DFF4FF", 0.6)
    ctx.fill_preserve()
    src(ctx, "#3A5A6A")
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.move_to(-17, 10)
    ctx.line_to(17, 10)
    ctx.line_to(22, 22)
    ctx.curve_to(24, 30, -24, 30, -22, 22)
    ctx.close_path()
    src(ctx, "#7CFF5A", 0.9)
    ctx.fill()
    for i in range(3):
        u = (t * 0.8 + i / 3) % 1
        ellipse(ctx, -8 + i * 8, 22 - u * 14, 2.5, 2.5)
        src(ctx, "#E8FFE0", 1 - u)
        ctx.fill()
    rrect(ctx, -10, -36, 20, 8, 2)
    src(ctx, "#8A5A3A")
    ctx.fill()
    ctx.restore()


def pedestal(ctx, x, y=GROUND):
    rrect(ctx, x - 40, y - 140, 80, 140, 6)
    fill_stroke(ctx, "#5A6670", "#22282E", 3)
    rrect(ctx, x - 52, y - 150, 104, 16, 4)
    fill_stroke(ctx, "#8A96A0", "#22282E", 3)


def banana_peel(ctx, x, y, t=0):
    ctx.save()
    ctx.translate(x, y)
    for a in (-0.9, 0, 0.9):
        ctx.save()
        ctx.rotate(a)
        ellipse(ctx, 0, -12, 7, 16)
        fill_stroke(ctx, "#F2D84A", "#8A6A14", 2)
        ctx.restore()
    ctx.restore()


# ---------------------------------------------------------------- sets
def lab(ctx, t, dial=0.5, sparks=1.0, wreck=0.0):
    g = cairo.LinearGradient(0, 0, 0, 600)
    g.add_color_stop_rgb(0, *rgb("#1E3A40"))
    g.add_color_stop_rgb(1, *rgb("#2E5058"))
    ctx.set_source(g)
    ctx.paint()
    for i in range(0, W, 64):
        ctx.rectangle(i, 0, 2, 600)
        src(ctx, "#163036")
        ctx.fill()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#2A2E36")
    ctx.fill()
    for i in range(0, W, 80):
        ctx.rectangle(i, 600, 40, 120)
        src(ctx, "#33373F")
        ctx.fill()
    rrect(ctx, 520, 40, 240, 60, 8)
    fill_stroke(ctx, "#E8D2A0", "#7A5A20", 3)
    text(ctx, "LABORATORY", 640, 82, 30, "#3A2410")
    # big machine
    rrect(ctx, 40, 200, 380, 400, 10)
    fill_stroke(ctx, "#6A7A84", "#22282E", 4)
    for i in range(3):
        cx, cy = 110 + i * 120, 290
        ellipse(ctx, cx, cy, 42, 42)
        fill_stroke(ctx, "#F2EEE4", "#22282E", 3)
        for k in range(12):
            a = PI * 0.75 + k * PI * 1.5 / 11
            ctx.move_to(cx + math.cos(a) * 34, cy + math.sin(a) * 34)
            ctx.line_to(cx + math.cos(a) * 40, cy + math.sin(a) * 40)
        src(ctx, "#22282E")
        ctx.set_line_width(2)
        ctx.stroke()
        v = clamp(dial + 0.15 * math.sin(t * (3 + i) + i))
        a = PI * 0.75 + v * PI * 1.5
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.cos(a) * 32, cy + math.sin(a) * 32)
        src(ctx, "#D9483A")
        ctx.set_line_width(3)
        ctx.stroke()
        text(ctx, "11", cx + 26, cy + 34, 12, "#D9483A")
    for i in range(5):
        lx = 80 + i * 70
        up = math.sin(t * 2 + i * 1.7) > 0
        ctx.rectangle(lx - 6, 380, 12, 80)
        src(ctx, "#22282E")
        ctx.fill()
        ellipse(ctx, lx, 390 if up else 450, 14, 14)
        src(ctx, ["#D9483A", "#E8B64A", "#4AB86A", "#3E6AA0", "#B98CFF"][i])
        ctx.fill()
    for i in range(8):
        on = math.sin(t * 6 + i * 2) > 0
        ellipse(ctx, 80 + i * 45, 520, 8, 8)
        src(ctx, "#7CFF5A" if on else "#1E3A1E")
        ctx.fill()
    # tesla coil
    ctx.rectangle(470, 340, 30, 260)
    src(ctx, "#8A6A4A")
    ctx.fill()
    ellipse(ctx, 485, 330, 40, 26)
    fill_stroke(ctx, "#C9CED6", "#5A6270", 3)
    if sparks > 0:
        rnd = random.Random(int(t * 15))
        for j in range(3):
            ctx.move_to(485, 310)
            x, y = 485, 310
            for s in range(6):
                x += rnd.uniform(-30, 30)
                y -= rnd.uniform(10, 30)
                ctx.line_to(x, y)
            src(ctx, "#B8F0FF", 0.8 * sparks)
            ctx.set_line_width(2)
            ctx.stroke()
    # bubbling flasks on a shelf
    ctx.rectangle(560, 300, 220, 10)
    src(ctx, "#5A3A22")
    ctx.fill()
    for i, col in enumerate(("#FF6FAE", "#7CFF5A", "#5EC8E8", "#E8B64A")):
        fx = 590 + i * 54
        ctx.move_to(fx - 6, 300)
        ctx.line_to(fx - 6, 270)
        ctx.line_to(fx - 18, 250)
        ctx.line_to(fx + 18, 250)
        ctx.line_to(fx + 6, 270)
        ctx.line_to(fx + 6, 300)
        ctx.close_path()
        ellipse(ctx, fx, 282, 20, 18)
        src(ctx, col, 0.85)
        ctx.fill()
        for b in range(2):
            u = (t * 0.9 + b * 0.5 + i * 0.2) % 1
            ellipse(ctx, fx + math.sin(u * 9) * 4, 250 - u * 40, 4, 4)
            src(ctx, col, 0.6 * (1 - u))
            ctx.fill()
    # Doubt's bookshelf corner
    rrect(ctx, 1000, 180, 240, 420, 6)
    fill_stroke(ctx, "#5A3A22", "#2A1A0E", 4)
    rnd = random.Random(5)
    for r in range(5):
        ctx.rectangle(1010, 250 + r * 80, 220, 8)
        src(ctx, "#2A1A0E")
        ctx.fill()
        x = 1014
        while x < 1220:
            w = rnd.uniform(12, 24)
            h = rnd.uniform(44, 64)
            ctx.rectangle(x, 250 + r * 80 - h, w, h)
            src(ctx, rnd.choice(["#8E1F2F", "#2E5A9E", "#3E7A3E", "#C9A040", "#6B4E8E"]))
            ctx.fill()
            x += w + 2
    if wreck > 0:
        ctx.set_source_rgba(0.1, 0.08, 0.06, 0.6 * wreck)
        ctx.paint()


def city(ctx, t, smash=None):
    g = cairo.LinearGradient(0, 0, 0, 500)
    g.add_color_stop_rgb(0, *rgb("#8EC5E8"))
    g.add_color_stop_rgb(1, *rgb("#E8F4FF"))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(8)
    for i in range(12):
        bx = i * 115
        h = rnd.uniform(160, 330)
        if smash and smash[0] - 70 < bx + 50 < smash[0] + 70 and t > smash[1]:
            dt = t - smash[1]
            h *= max(0.15, 1 - dt * 1.2)
        ctx.rectangle(bx, 560 - h, 100, h)
        src(ctx, mix("#8A96A8", "#5A6678", rnd.random()))
        ctx.fill()
        for wy in range(int(560 - h) + 14, 550, 26):
            for wx in range(bx + 10, bx + 90, 22):
                ctx.rectangle(wx, wy, 12, 14)
                src(ctx, "#C8E0F0")
                ctx.fill()
        if i % 3 == 1:
            rrect(ctx, bx + 4, 560 - h - 30, 92, 26, 4)
            fill_stroke(ctx, "#FFE36A", "#7A5E14", 2)
            text(ctx, "APPROVED", bx + 50, 560 - h - 12, 13, "#5A3A10")
    ctx.rectangle(0, 560, W, 160)
    src(ctx, "#6A6E74")
    ctx.fill()


def draw_robot(ctx, x, y, t, s=1.0, step=0.0, arm=0.0, pilot=None):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for side in (-1, 1):
        lift = max(0, math.sin(step + (0 if side < 0 else PI))) * 30
        rrect(ctx, side * 60 - 30, -200 - lift, 60, 200, 10)
        fill_stroke(ctx, "#5A4A7A", "#1A0E2A", 5)
        rrect(ctx, side * 60 - 46, -30 - lift, 92, 34, 8)
        fill_stroke(ctx, "#3A2A5A", "#1A0E2A", 5)
    rrect(ctx, -140, -470, 280, 280, 30)
    fill_stroke(ctx, "#6A5A9A", "#1A0E2A", 6)
    E.star_path(ctx, 0, -250, 30, 13)
    src(ctx, "#C8F24A")
    ctx.fill()
    # cockpit
    rrect(ctx, -90, -450, 180, 130, 20)
    src(ctx, "#B8E8FF", 0.9)
    ctx.fill()
    if pilot:
        ctx.save()
        rrect(ctx, -90, -450, 180, 130, 20)
        ctx.clip()
        E.draw_char(ctx, pilot, t)
        ctx.restore()
    rrect(ctx, -90, -450, 180, 130, 20)
    src(ctx, "#1A0E2A")
    ctx.set_line_width(6)
    ctx.stroke()
    for side in (-1, 1):
        a = (0.4 + arm * 1.4) if side > 0 else 0.4
        ctx.save()
        ctx.translate(side * 150, -420)
        ctx.rotate(-side * a)
        rrect(ctx, -22, 0, 44, 200, 16)
        fill_stroke(ctx, "#5A4A7A", "#1A0E2A", 5)
        ellipse(ctx, 0, 210, 40, 40)
        fill_stroke(ctx, "#3A2A5A", "#1A0E2A", 5)
        ctx.restore()
    ctx.restore()


def beach(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, 380)
    g.add_color_stop_rgb(0, *rgb("#5EC8F2"))
    g.add_color_stop_rgb(1, *rgb("#C8F0FF"))
    ctx.set_source(g)
    ctx.paint()
    ellipse(ctx, 1080, 110, 54, 54)
    src(ctx, "#FFF2A8")
    ctx.fill()
    ctx.rectangle(0, 360, W, 140)
    src(ctx, "#2EA8C8")
    ctx.fill()
    for k in range(6):
        y = 380 + k * 20
        ctx.move_to(0, y)
        for x in range(0, W + 40, 40):
            ctx.line_to(x, y + math.sin(t * 1.5 + x * 0.02 + k) * 4)
        src(ctx, "#FFFFFF", 0.25)
        ctx.set_line_width(2)
        ctx.stroke()
    ctx.move_to(0, 500)
    ctx.curve_to(400, 470, 900, 520, W, 480)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, "#F2DCA8")
    ctx.fill()
    for px in (120, 1180):
        ctx.move_to(px, 620)
        ctx.curve_to(px + 10, 450, px - 20, 330, px + 20, 230)
        src(ctx, "#8A5A3A")
        ctx.set_line_width(18)
        ctx.stroke()
        for i in range(6):
            a = i * PI / 3 + math.sin(t + i) * 0.05
            ctx.move_to(px + 20, 230)
            ctx.curve_to(px + 20 + math.cos(a) * 60, 230 + math.sin(a) * 30 - 30, px + 20 + math.cos(a) * 110,
                         230 + math.sin(a) * 60, px + 20 + math.cos(a) * 130, 240 + math.sin(a) * 80)
            src(ctx, "#3E9A3E")
            ctx.set_line_width(12)
            ctx.stroke()
    # umbrella
    ctx.move_to(640, 620)
    ctx.line_to(640, 360)
    src(ctx, "#5A3A22")
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.move_to(480, 380)
    ctx.curve_to(520, 300, 760, 300, 800, 380)
    ctx.close_path()
    fill_stroke(ctx, "#E85E5E", "#8A2A2A", 3)


def lounger(ctx, x):
    ctx.move_to(x - 90, 600)
    ctx.line_to(x + 60, 600)
    ctx.line_to(x + 100, 530)
    src(ctx, "#E8E4DA")
    ctx.set_line_width(16)
    ctx.stroke()


def cocktail(ctx, x, y):
    ctx.move_to(x - 16, y - 30)
    ctx.line_to(x + 16, y - 30)
    ctx.line_to(x, y - 8)
    ctx.close_path()
    src(ctx, "#FF8A5A", 0.9)
    ctx.fill()
    ctx.move_to(x, y - 8)
    ctx.line_to(x, y + 6)
    src(ctx, "#DDEEFF")
    ctx.set_line_width(3)
    ctx.stroke()
    ellipse(ctx, x + 12, y - 32, 6, 6)
    src(ctx, "#7CC84A")
    ctx.fill()


def news_screen(ctx, t, headline, sub, a=1.0, img=None):
    ctx.push_group()
    src(ctx, "#0E1A3A")
    ctx.paint()
    rrect(ctx, 80, 80, 1120, 470, 10)
    src(ctx, "#1E2E5A")
    ctx.fill()
    if img:
        img(ctx)
    ctx.rectangle(0, 560, W, 70)
    src(ctx, "#D9283A")
    ctx.fill()
    text(ctx, "BREAKING", 120, 606, 30, "#FFFFFF", align="left")
    ctx.rectangle(320, 560, W - 320, 70)
    src(ctx, "#F2F2F2")
    ctx.fill()
    text(ctx, headline, 340, 606, 28, "#1A1A1A", align="left")
    ctx.rectangle(0, 630, W, 40)
    src(ctx, "#1A1A1A")
    ctx.fill()
    off = (t * 120) % 1400
    text(ctx, sub, W - off, 658, 20, "#FFE36A", align="left")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def office(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, 600)
    g.add_color_stop_rgb(0, *rgb("#2A1A3A"))
    g.add_color_stop_rgb(1, *rgb("#3A2450"))
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#1A0E22")
    ctx.fill()
    # portrait of Vex
    rrect(ctx, 420, 70, 220, 260, 6)
    fill_stroke(ctx, "#3A2A4A", "#E8C84A", 8)
    p = new_char("vex", 530, y=300, s=0.8, mouth="smirk", brow=-0.9, crown=True)
    E.draw_char(ctx, p, 0.0)
    # door on the right
    rrect(ctx, 1060, 260, 150, 340, 6)
    fill_stroke(ctx, "#4A2E1A", "#1A0E06", 4)
    ellipse(ctx, 1080, 440, 7, 7)
    src(ctx, "#E8C84A")
    ctx.fill()


def office_desk(ctx, x=420):
    rrect(ctx, x - 300, 470, 600, 30, 6)
    fill_stroke(ctx, "#4A2E1A", "#1A0E06", 4)
    ctx.rectangle(x - 290, 500, 580, 110)
    src(ctx, "#3A2214")
    ctx.fill()


def laptop_call(ctx, x, y, t, scale=1.0, look=0.0, worry=0.0):
    """A laptop showing Boredom and Doubt on a video call. look: eyes toward screen-right; worry: 0..1."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)
    rrect(ctx, -130, -170, 260, 170, 10)
    fill_stroke(ctx, "#1A1A22", "#000", 4)
    ctx.save()
    rrect(ctx, -120, -160, 240, 150, 6)
    ctx.clip()
    src(ctx, "#2E5058")
    ctx.paint()
    kw = dict(px=look, py=-0.1 * look)
    if worry > 0:
        kw.update(brow=0.9 * worry, mouth="frown", mamt=0.5 * worry, wide=0.5 * worry, sweat=worry)
    b = new_boredom(-50, y=-12, s=0.6, **kw)
    d = new_doubt(55, y=-12, s=0.55, **kw)
    E.draw_char(ctx, b, t)
    E.draw_char(ctx, d, t)
    ctx.restore()
    ctx.move_to(-150, 4)
    ctx.line_to(150, 4)
    src(ctx, "#3A3A44")
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.restore()


def thought_bubble(ctx, x, y, t, a=1.0):
    """A cloud above someone's head showing Boredom and Doubt relaxing in the Bahamas."""
    if a <= 0:
        return
    ctx.push_group()
    for i, (dx, dy, r) in enumerate(((-150, 150, 9), (-120, 118, 14))):
        ellipse(ctx, x + dx, y + dy, r, r)
        fill_stroke(ctx, "#FFFFFF", "#8A8A9A", 3)
    w, h = 170, 105
    ctx.new_path()
    for i in range(12):
        ang = i / 12 * 2 * PI
        ctx.arc(x + math.cos(ang) * w, y + math.sin(ang) * h, 42, 0, 2 * PI)
        ctx.new_sub_path()
    src(ctx, "#8A8A9A")
    ctx.fill()
    for i in range(12):
        ang = i / 12 * 2 * PI
        ellipse(ctx, x + math.cos(ang) * w, y + math.sin(ang) * h, 38, 38)
        src(ctx, "#FFFFFF")
        ctx.fill()
    ellipse(ctx, x, y, w + 4, h + 4)
    src(ctx, "#FFFFFF")
    ctx.fill()
    ctx.save()
    ellipse(ctx, x, y, w - 8, h - 6)
    ctx.clip()
    ctx.translate(x - 640 * 0.28, y - 400 * 0.28)
    ctx.scale(0.28, 0.28)
    beach(ctx, t)
    for cx, flip in ((470, 1), (810, -1)):
        c = (new_boredom if flip > 0 else new_doubt)(cx, s=1.1, shades=True, mouth="smile", mamt=0.8,
                                                    face=0.3 * flip, itemR=None,
                                                    tilt=-0.12 * flip + math.sin(t * 2) * 0.03)
        c["itemR" if flip > 0 else "itemL"] = "cocktail"
        c["hr" if flip > 0 else "hl"] = (60 * flip, -150 + math.sin(t * 3) * 8)
        E.draw_char(ctx, c, t)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def comedy_stage(ctx, t, spot=1.0):
    src(ctx, "#140A0E")
    ctx.paint()
    # stage on the right
    rrect(ctx, 420, 120, 860, 480, 0)
    src(ctx, "#2A1218")
    ctx.fill()
    for i in range(14):
        x = 420 + i * 62
        g = cairo.LinearGradient(x, 0, x + 62, 0)
        g.add_color_stop_rgb(0, *rgb("#7A0C19"))
        g.add_color_stop_rgb(0.5, *rgb("#C41E3A"))
        g.add_color_stop_rgb(1, *rgb("#6E0A16"))
        ctx.rectangle(x, 60, 63, 540)
        ctx.set_source(g)
        ctx.fill()
    ctx.rectangle(420, 560, 860, 60)
    src(ctx, "#5A3A22")
    ctx.fill()
    if spot > 0:
        g = cairo.RadialGradient(850, 560, 20, 850, 560, 330)
        g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.45 * spot)
        g.add_color_stop_rgba(1, 1, 0.95, 0.8, 0)
        ctx.set_source(g)
        ctx.paint()
    # mic stand
    ctx.move_to(900, 600)
    ctx.line_to(900, 440)
    src(ctx, "#2A2A2A")
    ctx.set_line_width(5)
    ctx.stroke()
    ellipse(ctx, 900, 432, 9, 12)
    src(ctx, "#4A4A4A")
    ctx.fill()
    rrect(ctx, 520, 20, 660, 50, 8)
    fill_stroke(ctx, "#1A0A0E", "#E8C84A", 3)
    text(ctx, "VILLAIN COMEDY NIGHT", 850, 56, 30, "#E8C84A")
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#0E0608")
    ctx.fill()


def council_table(ctx):
    rrect(ctx, 0, 520, 400, 30, 4)
    fill_stroke(ctx, "#2A2A33", "#0E0E14", 3)
    ctx.rectangle(10, 550, 380, 70)
    src(ctx, "#1A1A22")
    ctx.fill()


def curtain_drop(ctx, u):
    if u <= 0:
        return
    h = H * ease(u)
    for i in range(22):
        x = i * 60
        g = cairo.LinearGradient(x, 0, x + 60, 0)
        g.add_color_stop_rgb(0, *rgb("#7A0C19"))
        g.add_color_stop_rgb(0.5, *rgb("#E0283F"))
        g.add_color_stop_rgb(1, *rgb("#6E0A16"))
        ctx.rectangle(x, 0, 61, h)
        ctx.set_source(g)
        ctx.fill()
    ctx.rectangle(0, h - 18, W, 18)
    src(ctx, "#E8B64A")
    ctx.fill()


# ---------------------------------------------------------------- montage props
def evil_car(ctx, x, y, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.move_to(-200, 0)
    ctx.line_to(-190, -70)
    ctx.line_to(-80, -90)
    ctx.line_to(-30, -150)
    ctx.line_to(90, -150)
    ctx.line_to(150, -90)
    ctx.line_to(210, -70)
    ctx.line_to(220, 0)
    ctx.close_path()
    fill_stroke(ctx, "#1A1A22", "#000", 4)
    for sx in (-150, -90, 60, 120):
        ctx.move_to(sx, -80)
        ctx.line_to(sx + 10, -110)
        ctx.line_to(sx + 20, -80)
        ctx.close_path()
        src(ctx, "#C8F24A")
        ctx.fill()
    rrect(ctx, -20, -140, 100, 48, 6)
    src(ctx, "#5A3A8A", 0.8)
    ctx.fill()
    for wx in (-120, 140):
        ellipse(ctx, wx, 0, 40, 40)
        fill_stroke(ctx, "#2A2A2A", "#000", 4)
        ellipse(ctx, wx, 0, 14, 14)
        src(ctx, "#C8F24A")
        ctx.fill()
    ctx.restore()


def money_pile(ctx, x, y, t):
    rnd = random.Random(4)
    for i in range(60):
        px = x + rnd.uniform(-220, 220) * (1 - i / 80)
        py = y - i * 2.6 + rnd.uniform(-6, 6)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(rnd.uniform(-0.6, 0.6))
        rrect(ctx, -26, -12, 52, 24, 3)
        fill_stroke(ctx, "#8AC87A", "#3E6A2E", 2)
        ctx.restore()
    for i in range(10):
        u = (t * 0.6 + i / 10) % 1
        ctx.save()
        ctx.translate(x + math.sin(i * 3) * 200, 100 + u * 500)
        ctx.rotate(u * 6 + i)
        rrect(ctx, -20, -9, 40, 18, 3)
        fill_stroke(ctx, "#8AC87A", "#3E6A2E", 2)
        ctx.restore()


def sitcom_set(ctx, t):
    src(ctx, "#E8C8A8")
    ctx.paint()
    for i in range(0, W, 90):
        ctx.rectangle(i, 0, 45, 560)
        src(ctx, "#DDB898")
        ctx.fill()
    rrect(ctx, 280, 400, 520, 140, 30)
    fill_stroke(ctx, "#8A3A5A", "#4A1A2A", 4)
    ctx.rectangle(0, 560, W, 160)
    src(ctx, "#6A4A3A")
    ctx.fill()
    rrect(ctx, 900, 60, 320, 80, 10)
    fill_stroke(ctx, "#1A0A1A", "#E8C84A", 4)
    text(ctx, "EVIL & FRIENDS", 1060, 112, 32, "#E8C84A")
    ellipse(ctx, 70, 70, 26, 26)
    src(ctx, "#D9283A")
    ctx.fill()
    text(ctx, "ON AIR", 150, 80, 24, "#D9283A")


def medal_wall(ctx, t):
    src(ctx, "#2A1A3A")
    ctx.paint()
    rnd = random.Random(6)
    for i in range(12):
        x = 140 + (i % 6) * 200
        y = 140 + (i // 6) * 220
        ctx.move_to(x - 14, y - 70)
        ctx.line_to(x, y - 20)
        ctx.line_to(x + 14, y - 70)
        src(ctx, rnd.choice(["#D9283A", "#3E6AA0", "#3E8A3E"]))
        ctx.set_line_width(10)
        ctx.stroke()
        ellipse(ctx, x, y, 34, 34)
        fill_stroke(ctx, "#E8C84A", "#7A5E14", 4)
        E.star_path(ctx, x, y, 18, 8)
        src(ctx, "#FFF2A8")
        ctx.fill()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#140A1E")
    ctx.fill()


def dark_room(ctx, t):
    src(ctx, "#0A0A12")
    ctx.paint()
    g = cairo.RadialGradient(640, 520, 20, 640, 520, 420)
    g.add_color_stop_rgba(0, 0.4, 0.5, 0.8, 0.35)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#06060A")
    ctx.fill()


def hallway(ctx, t):
    src(ctx, "#1E1428")
    ctx.paint()
    for i in range(6):
        x = 100 + i * 220
        rrect(ctx, x, 140, 120, 200, 60)
        src(ctx, "#2E2040")
        ctx.fill()
        ellipse(ctx, x + 60, 120, 16, 16)
        src(ctx, "#C8F24A", 0.6 + 0.4 * math.sin(t * 3 + i))
        ctx.fill()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#140A1E")
    ctx.fill()
    ctx.rectangle(0, 610, W, 40)
    src(ctx, "#6A0A1A")
    ctx.fill()


def heart(ctx, x, y, s, a=1.0, col="#FF5A7A"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(0, 12)
    ctx.curve_to(-30, -8, -16, -34, 0, -16)
    ctx.curve_to(16, -34, 30, -8, 0, 12)
    src(ctx, col, a)
    ctx.fill()
    ctx.restore()


def whiteboard(ctx, x, y, t, prog=1.0):
    rrect(ctx, x - 200, y - 130, 400, 260, 8)
    fill_stroke(ctx, "#F8F8F4", "#8A8A84", 5)
    text(ctx, "MASTER PLAN", x, y - 90, 28, "#2E5A9E")
    lines = ["1. Protect Vex's reputation", "2. Keep the lab open", "3. Nobody gets hurt", "4. Snacks"]
    for i, ln in enumerate(lines):
        if prog > i / len(lines):
            text(ctx, ln, x - 170, y - 40 + i * 42, 22, "#2A2A2A", align="left")
    if prog > 0.9:
        ctx.move_to(x + 120, y + 70)
        ctx.curve_to(x + 140, y + 100, x + 180, y + 60, x + 170, y + 40)
        src(ctx, "#D9483A")
        ctx.set_line_width(4)
        ctx.stroke()


def title_card(ctx, t, title, sub, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    lab(ctx, t, 0.9)
    ctx.set_source_rgba(0.02, 0.04, 0.06, 0.6)
    ctx.paint()
    text(ctx, title, 640, 300, 84, "#C8F24A", outline="#1A0E2A", olw=12)
    text(ctx, sub, 640, 380, 36, "#FFFFFF", outline="#1A0E2A", olw=7)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------------------------------------------------------------- episode 3/4 extras
def _cocktail_item(ctx, hx, hy, wang, c, t):
    cocktail(ctx, hx, hy + 2)


def _phone_item(ctx, hx, hy, wang, c, t):
    rrect(ctx, hx - 9, hy - 34, 18, 34, 4)
    fill_stroke(ctx, "#1A1A22", "#000", 2)
    rrect(ctx, hx - 6, hy - 30, 12, 24, 2)
    src(ctx, "#7AD0FF", 0.9)
    ctx.fill()


def _mic_item(ctx, hx, hy, wang, c, t):
    ctx.move_to(hx, hy + 6)
    ctx.line_to(hx, hy - 22)
    src(ctx, "#2A2A2A")
    ctx.set_line_width(6)
    ctx.stroke()
    ellipse(ctx, hx, hy - 30, 9, 12)
    src(ctx, "#5A5A5A")
    ctx.fill()


E.ITEMS["cocktail"] = _cocktail_item
E.ITEMS["phone"] = _phone_item
E.ITEMS["mic"] = _mic_item


def _shades_hook(stage, ctx, c, k, t, top):
    if stage == "post" and c.get("shades"):
        fx = c["face"] * k["w"] * 0.1
        for side in (-1, 1):
            rrect(ctx, fx + side * k["eye_dx"] - 22, k["eye_y"] - 14, 44, 26, 9)
            src(ctx, "#111118")
            ctx.fill()
        ctx.move_to(fx - k["eye_dx"] + 22, k["eye_y"] - 6)
        ctx.line_to(fx + k["eye_dx"] - 22, k["eye_y"] - 6)
        src(ctx, "#111118")
        ctx.set_line_width(4)
        ctx.stroke()
    if stage == "post" and c.get("disguise"):
        # fake nose + mustache glasses
        fx = c["face"] * k["w"] * 0.1
        for side in (-1, 1):
            ellipse(ctx, fx + side * k["eye_dx"], k["eye_y"], 18, 18)
            src(ctx, "#111111")
            ctx.set_line_width(4)
            ctx.stroke()
        ellipse(ctx, fx, k["eye_y"] + 20, 12, 15)
        fill_stroke(ctx, "#F2B8A0", "#8A4A3A", 2)
        ctx.move_to(fx - 30, k["eye_y"] + 40)
        ctx.curve_to(fx - 10, k["eye_y"] + 28, fx + 10, k["eye_y"] + 28, fx + 30, k["eye_y"] + 40)
        src(ctx, "#2A1A0A")
        ctx.set_line_width(9)
        ctx.stroke()


def _wrap(prev):
    def hook(stage, ctx, c, k, t, top):
        if prev:
            prev(stage, ctx, c, k, t, top)
        _shades_hook(stage, ctx, c, k, t, top)
    return hook


for _k in ("boredom", "doubt", "vex", "heir"):
    E.HOOKS[_k] = _wrap(E.HOOKS.get(_k))


def lab_wrecked_sign(ctx, t, a=1.0):
    ctx.save()
    ctx.translate(960, 250)
    ctx.rotate(-0.12)
    rrect(ctx, -170, -40, 340, 80, 6)
    fill_stroke(ctx, "#F8F8F4", "#8A8A84", 4)
    text(ctx, "GONE FISHIN'", 0, 12, 34, "#2E5A9E")
    ctx.restore()


def _bottle_item(ctx, hx, hy, wang, c, t):
    rrect(ctx, hx - 9, hy - 40, 18, 44, 5)
    fill_stroke(ctx, "#8FD8FF", "#2E6A8A", 2)
    ctx.rectangle(hx - 5, hy - 48, 10, 9)
    src(ctx, "#2E6AA0")
    ctx.fill()


E.ITEMS["bottle"] = _bottle_item


# ---------------------------------------------------------------- episode 1: Doubt's broom and Boredom's flasks
def _broom_item(ctx, hx, hy, wang, c, t):
    dirn = c.get("broomdir") or (-1 if c["face"] < 0 else 1)
    bx, by = hx + dirn * 46, -6
    ctx.move_to(hx - dirn * 14, hy - 46)
    ctx.line_to(bx, by - 26)
    src(ctx, "#8A5A3A")
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.move_to(bx - 10, by - 30)
    ctx.line_to(bx + 10, by - 30)
    ctx.line_to(bx + 22, by + 4)
    ctx.line_to(bx - 22, by + 4)
    ctx.close_path()
    fill_stroke(ctx, "#E8C86A", "#8A6A2A", 3)


def _flask_item(ctx, hx, hy, wang, c, t):
    flask(ctx, hx, hy - 6, 0.0, "#7CFF5A")


E.ITEMS["broom"] = _broom_item
E.ITEMS["flask"] = _flask_item


def flask(ctx, x, y, ang, col, a=1.0):
    """Small round-bottom flask, centered on its bulb."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.rectangle(-5, -26, 10, 16)
    src(ctx, "#DDEEFF", 0.9 * a)
    ctx.fill()
    ellipse(ctx, 0, 0, 14, 14)
    src(ctx, col, 0.85 * a)
    ctx.fill()
    ellipse(ctx, 0, 0, 14, 14)
    src(ctx, "#2A3A44", a)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ellipse(ctx, -5, -4, 3, 4)
    src(ctx, "#FFFFFF", 0.7 * a)
    ctx.fill()
    ctx.restore()


def flask_stand(ctx, x):
    rrect(ctx, x - 50, GROUND - 106, 100, 12, 3)
    fill_stroke(ctx, "#6A6A74", "#2A2A33", 3)
    for sx in (-38, 38):
        ctx.move_to(x + sx, GROUND - 94)
        ctx.line_to(x + sx, GROUND - 2)
        src(ctx, "#4A4A54")
        ctx.set_line_width(6)
        ctx.stroke()


def shards(ctx, x, a, seed=0):
    if a <= 0:
        return
    rnd = random.Random(seed)
    for i in range(14):
        sx = x + rnd.uniform(-46, 46)
        sy = GROUND - 2 + rnd.uniform(-6, 4)
        r = rnd.uniform(3, 7)
        ctx.move_to(sx, sy - r)
        ctx.line_to(sx + r, sy + r * 0.4)
        ctx.line_to(sx - r * 0.6, sy + r * 0.6)
        ctx.close_path()
        src(ctx, "#DDEEFF", 0.9 * a)
        ctx.fill()
    ellipse(ctx, x, GROUND, 40, 6)
    src(ctx, "#7CFF5A", 0.35 * a)
    ctx.fill()
