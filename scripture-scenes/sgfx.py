"""Characters and scenes for the scripture video."""
import math
import random

import cairo

import engine as E
from engine import (W, H, GROUND, PI, clamp, lerp, ease, ellipse, rrect, src, mix, rgb, fill_stroke,
                    sparkle, text)

TITLE_FONT = "Cinzel"


# ---------------------------------------------------------------- people
def person_kind(name, robe, skin, hair="#3A2A1E", style="short", beard=False, sash=None, scarf=None):
    dark = "#" + "".join(f"{int(v * 255 * 0.45):02x}" for v in rgb(robe))
    skin_d = "#" + "".join(f"{int(v * 255 * 0.6):02x}" for v in rgb(skin))
    E.KIND[name] = dict(
        w=120, h=190, legh=20, n=2.4, taper=-0.1, col=robe, dark=dark,
        eye_y=-168, eye_dx=16, erx=9, ery=10, mouth_y=-138, mw=20, sh=(52, -120), hip=20, L=50,
        brow=(0, 0), brow_raise=(0, 0), lid=0.08, legw=(12, 8), legcol=skin, legdark=skin_d,
        armw=(18, 12), handcol=skin, handdark=skin_d, handr=10, footr=(15, 7), foot="#6E4A2A",
        browlen=15, browlw=3.5)

    def hook(stage, ctx, c, k, t, top):
        if stage != "body":
            return
        fx = c["face"] * k["w"] * 0.1
        # sash / belt
        if sash:
            ctx.rectangle(-60, -86, 120, 12)
            src(ctx, sash)
            ctx.fill()
            ctx.move_to(-30, -150)
            ctx.line_to(30, -86)
            src(ctx, sash)
            ctx.set_line_width(9)
            ctx.stroke()
        # long hair behind the face
        if style == "long":
            ellipse(ctx, fx, -160, 44, 48)
            src(ctx, hair)
            ctx.fill()
            ctx.rectangle(fx - 44, -160, 88, 46)
            ctx.fill()
        if scarf:
            ellipse(ctx, fx, -158, 48, 50)
            src(ctx, scarf)
            ctx.fill()
            ctx.move_to(fx - 46, -150)
            ctx.line_to(fx - 56, -100)
            ctx.line_to(fx + 56, -100)
            ctx.line_to(fx + 46, -150)
            ctx.close_path()
            ctx.fill()
        # face
        ellipse(ctx, fx, -156, 36, 40)
        src(ctx, skin)
        ctx.fill()
        ellipse(ctx, fx, -156, 36, 40)
        src(ctx, skin_d)
        ctx.set_line_width(2.5)
        ctx.stroke()
        if beard:
            ctx.move_to(fx - 34, -152)
            ctx.curve_to(fx - 34, -110, fx + 34, -110, fx + 34, -152)
            ctx.curve_to(fx + 22, -130, fx - 22, -130, fx - 34, -152)
            ctx.close_path()
            src(ctx, beard if isinstance(beard, str) else hair)
            ctx.fill()
        # hair on top
        if style in ("short", "long", "messy") and not scarf:
            ctx.move_to(fx - 37, -158)
            if style == "messy":
                for i in range(8):
                    ctx.line_to(fx - 37 + i * 10 + 5, -186 - (i % 2) * 8)
            ctx.curve_to(fx - 34, -206, fx + 34, -206, fx + 37, -158)
            ctx.curve_to(fx + 20, -178, fx - 20, -178, fx - 37, -158)
            ctx.close_path()
            src(ctx, hair)
            ctx.fill()
        elif style == "bald":
            ellipse(ctx, fx - 14, -184, 9, 5)
            src(ctx, "#FFFFFF", 0.35)
            ctx.fill()
            for side in (-1, 1):
                ellipse(ctx, fx + side * 34, -160, 6, 12)
                src(ctx, hair)
                ctx.fill()
        if c.get("tears", 0) > 0:
            for side in (-1, 1):
                u = (t * 0.7 + (side + 1) * 0.3) % 1
                ellipse(ctx, fx + side * 20, -158 + u * 26, 2.5, 4)
                src(ctx, "#8FD8FF", c["tears"] * (1 - u))
                ctx.fill()
        if c.get("halo", 0) > 0:
            g = cairo.RadialGradient(fx, -160, 20, fx, -160, 110)
            g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.0)
            g.add_color_stop_rgba(0.5, 1, 0.95, 0.75, 0.35 * c["halo"])
            g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0)
            ctx.set_source(g)
            ctx.arc(fx, -160, 110, 0, 2 * PI)
            ctx.fill()

    E.HOOKS[name] = hook
    return name


def new_person(kind, x, **kw):
    c = E.new_char(kind, x, mouth="smile", mamt=0.2, brow=0.0)
    c.update(kw)
    return c


# ---------------------------------------------------------------- items
def _bread(ctx, hx, hy, wang, c, t):
    ellipse(ctx, hx + 14, hy - 10, 24, 15)
    fill_stroke(ctx, "#D9A35A", "#8A5A24", 2.5)
    for i in range(3):
        ctx.move_to(hx + 2 + i * 10, hy - 20)
        ctx.line_to(hx + 8 + i * 10, hy - 4)
    src(ctx, "#8A5A24")
    ctx.set_line_width(2)
    ctx.stroke()


def _cup(ctx, hx, hy, wang, c, t):
    ctx.move_to(hx - 12, hy - 34)
    ctx.line_to(hx + 12, hy - 34)
    ctx.line_to(hx + 8, hy - 8)
    ctx.line_to(hx - 8, hy - 8)
    ctx.close_path()
    fill_stroke(ctx, "#B97A4A", "#5E3A1E", 2.5)
    ellipse(ctx, hx, hy - 34, 12, 4)
    src(ctx, "#7FB8E0")
    ctx.fill()


def _stone(ctx, hx, hy, wang, c, t):
    ellipse(ctx, hx, hy - 8, 15, 12)
    fill_stroke(ctx, "#8A8178", "#3A3530", 2.5)


def _quill(ctx, hx, hy, wang, c, t):
    ctx.move_to(hx, hy)
    ctx.curve_to(hx + 10, hy - 30, hx + 30, hy - 50, hx + 40, hy - 70)
    ctx.curve_to(hx + 20, hy - 50, hx + 6, hy - 30, hx, hy)
    fill_stroke(ctx, "#F2EEE4", "#8A8070", 1.5)


def _scroll(ctx, hx, hy, wang, c, t):
    rrect(ctx, hx - 6, hy - 30, 12, 50, 4)
    fill_stroke(ctx, "#E8D9B0", "#8A7444", 2)


for _n, _f in (("bread", _bread), ("cup", _cup), ("stone", _stone), ("quill", _quill), ("scroll", _scroll)):
    E.ITEMS[_n] = _f


def draw_pot(ctx, x, y, broken_t=None, t=0.0):
    if broken_t is None or t < broken_t:
        ctx.move_to(x - 22, y)
        ctx.curve_to(x - 40, y - 30, x - 30, y - 60, x - 14, y - 66)
        ctx.line_to(x + 14, y - 66)
        ctx.curve_to(x + 30, y - 60, x + 40, y - 30, x + 22, y)
        ctx.close_path()
        fill_stroke(ctx, "#B9643A", "#5E2A14", 3)
        ctx.move_to(x - 30, y - 38)
        ctx.line_to(x + 30, y - 38)
        src(ctx, "#E8B07A")
        ctx.set_line_width(3)
        ctx.stroke()
        return
    dt = t - broken_t
    rnd = random.Random(5)
    for i in range(8):
        vx = rnd.uniform(-160, 160)
        vy = rnd.uniform(-260, -80)
        dd = min(dt, 0.45)
        px = x + vx * dd
        py = min(y, y - 30 + vy * dd + 900 * dd * dd)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(rnd.uniform(0, 6) + dd * 6)
        ctx.move_to(-10, -6)
        ctx.line_to(12, -8)
        ctx.line_to(6, 8)
        ctx.close_path()
        fill_stroke(ctx, "#B9643A", "#5E2A14", 2)
        ctx.restore()


def draw_coals(ctx, x, y, a, t):
    """Glowing embers above a head (the 'burning coals')."""
    if a <= 0:
        return
    g = cairo.RadialGradient(x, y, 0, x, y, 90)
    g.add_color_stop_rgba(0, 1, 0.6, 0.2, 0.45 * a)
    g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
    ctx.set_source(g)
    ctx.arc(x, y, 90, 0, 2 * PI)
    ctx.fill()
    rnd = random.Random(3)
    for i in range(14):
        ang = rnd.uniform(0, 2 * PI)
        r = rnd.uniform(6, 34)
        px = x + math.cos(ang) * r
        py = y + math.sin(ang) * r * 0.4
        flick = 0.6 + 0.4 * math.sin(t * 9 + i)
        ellipse(ctx, px, py, 7, 5)
        src(ctx, mix("#FF5A1F", "#FFE36A", flick), a)
        ctx.fill()
    for i in range(6):
        u = (t * 0.6 + i / 6) % 1
        sparkle(ctx, x + math.sin(i * 2 + t) * 20, y - u * 70, 5 * (1 - u), "#FFD27A", a * (1 - u))


def draw_sheep(ctx, x, y, s, t, ph=0.0):
    ctx.save()
    ctx.translate(x, y + math.sin(t * 2 + ph) * 1.5)
    ctx.scale(s, s)
    for lx in (-16, -6, 8, 18):
        ctx.rectangle(lx - 2, -14, 4, 14)
    src(ctx, "#2A2420")
    ctx.fill()
    for i in range(7):
        ellipse(ctx, -18 + i * 6, -26 + (i % 2) * 4, 12, 11)
        src(ctx, "#F2EEE4")
        ctx.fill()
    ellipse(ctx, 26, -30, 9, 8)
    src(ctx, "#2A2420")
    ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- backgrounds
def sky(ctx, top, bottom, y1=H):
    g = cairo.LinearGradient(0, 0, 0, y1)
    g.add_color_stop_rgb(0, *rgb(top))
    g.add_color_stop_rgb(1, *rgb(bottom))
    ctx.set_source(g)
    ctx.paint()


def village(ctx, t, dusk=0.0, rain=0.0, door=0.0, watchers=0.0, sunrise=0.0):
    sky(ctx, mix("#8EC5E8", "#2A3550", dusk) if sunrise == 0 else mix("#F2B26A", "#8EC5E8", 1 - sunrise),
        mix("#F2E2B8", "#4A4A60", dusk))
    if sunrise > 0:
        g = cairo.RadialGradient(1050, 420, 20, 1050, 420, 500)
        g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.8 * sunrise)
        g.add_color_stop_rgba(1, 1, 0.7, 0.4, 0)
        ctx.set_source(g)
        ctx.paint()
    # distant hills and houses
    ctx.move_to(0, 470)
    for x in range(0, W + 80, 80):
        ctx.line_to(x, 450 + math.sin(x * 0.01) * 20)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, mix("#8EA86A", "#3A4A3A", dusk))
    ctx.fill()
    for hx in (140, 980, 1160):
        rrect(ctx, hx - 60, 360, 120, 120, 4)
        src(ctx, mix("#E2C9A0", "#5A5048", dusk))
        ctx.fill()
        ctx.rectangle(hx - 66, 352, 132, 14)
        src(ctx, mix("#9C7A54", "#3A3028", dusk))
        ctx.fill()
        rrect(ctx, hx - 16, 400, 32, 32, 3)
        win = mix("#3A3028", "#FFD27A", watchers if hx != 140 else watchers)
        src(ctx, win)
        ctx.fill()
        if watchers > 0.3:
            ellipse(ctx, hx, 422, 9, 10)
            src(ctx, "#2A2018", watchers)
            ctx.fill()
    # the main house
    rrect(ctx, 420, 250, 380, 360, 6)
    src(ctx, mix("#E8D2A8", "#6A5E50", dusk))
    ctx.fill()
    ctx.rectangle(408, 236, 404, 22)
    src(ctx, mix("#9C7A54", "#3A3028", dusk))
    ctx.fill()
    # door with warm light
    rrect(ctx, 560, 420, 100, 190, 6)
    src(ctx, "#2A1E14")
    ctx.fill()
    if door > 0:
        g = cairo.LinearGradient(560, 0, 660, 0)
        g.add_color_stop_rgba(0, 1, 0.8, 0.45, 0.9 * door)
        g.add_color_stop_rgba(1, 1, 0.7, 0.35, 0.7 * door)
        rrect(ctx, 560, 420, 100, 190, 6)
        ctx.set_source(g)
        ctx.fill()
        g = cairo.RadialGradient(610, 600, 10, 610, 600, 260)
        g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.35 * door)
        g.add_color_stop_rgba(1, 1, 0.8, 0.4, 0)
        ctx.set_source(g)
        ctx.paint()
    rrect(ctx, 560 + 100 * (1 - (1 - door) ** 0) * 0, 420, 100 * (1 - door * 0.85), 190, 6)
    fill_stroke(ctx, "#7A5230", "#3A2414", 3)
    for wx in (470, 700):
        rrect(ctx, wx, 320, 60, 60, 4)
        src(ctx, mix("#6E8EA8", "#FFD27A", dusk * 0.8))
        ctx.fill()
    # ground
    ctx.rectangle(0, 600, W, 120)
    src(ctx, mix("#C9A878", "#4A4038", dusk))
    ctx.fill()
    # fence
    for fx in range(840, W, 46):
        ctx.rectangle(fx, 540, 10, 70)
    ctx.rectangle(840, 556, W - 840, 8)
    src(ctx, mix("#9C7A54", "#3A3028", dusk))
    ctx.fill()
    if rain > 0:
        rnd = random.Random(1)
        for i in range(220):
            x = rnd.uniform(-100, W)
            sp = rnd.uniform(700, 1000)
            y = (rnd.uniform(0, H) + t * sp) % (H + 40) - 40
            ctx.move_to(x, y)
            ctx.line_to(x - 6, y + 22)
        src(ctx, "#B8C8E0", 0.45 * rain)
        ctx.set_line_width(1.6)
        ctx.stroke()


def upper_room(ctx, t):
    src(ctx, "#3A2A20")
    ctx.paint()
    rnd = random.Random(2)
    for row in range(14):
        for col in range(18):
            off = 40 if row % 2 else 0
            rrect(ctx, col * 80 - off + 3, row * 44 + 3, 74, 38, 4)
            src(ctx, mix("#6A4E3A", "#4A3428", rnd.random()))
            ctx.fill()
    # arched window with night sky
    ctx.move_to(560, 330)
    ctx.line_to(560, 200)
    ctx.curve_to(560, 120, 720, 120, 720, 200)
    ctx.line_to(720, 330)
    ctx.close_path()
    src(ctx, "#1A2240")
    ctx.fill()
    for i in range(12):
        sparkle(ctx, 570 + rnd.uniform(0, 140), 150 + rnd.uniform(0, 170), 3, "#F2E8C8", 0.8)
    # warm lamp light
    g = cairo.RadialGradient(640, 470, 40, 640, 470, 700)
    g.add_color_stop_rgba(0, 1, 0.8, 0.45, 0.35)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(g)
    ctx.paint()


def supper_table(ctx, t):
    rrect(ctx, 150, 520, 980, 40, 6)
    fill_stroke(ctx, "#E8DCC0", "#8A7A5A", 3)
    ctx.rectangle(160, 556, 960, 170)
    src(ctx, "#5A3A24")
    ctx.fill()
    for bx in (330, 640, 950):
        ellipse(ctx, bx, 514, 30, 14)
        fill_stroke(ctx, "#D9A35A", "#8A5A24", 2)
    for cx in (480, 800):
        ctx.move_to(cx - 12, 520)
        ctx.line_to(cx + 12, 520)
        ctx.line_to(cx + 8, 494)
        ctx.line_to(cx - 8, 494)
        ctx.close_path()
        fill_stroke(ctx, "#B97A4A", "#5E3A1E", 2)
    for lx in (220, 1060):
        ctx.rectangle(lx - 5, 480, 10, 40)
        src(ctx, "#F2EEE4")
        ctx.fill()
        g = cairo.RadialGradient(lx, 470, 0, lx, 470, 60)
        g.add_color_stop_rgba(0, 1, 0.85, 0.4, 0.8)
        g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
        ctx.set_source(g)
        ctx.arc(lx, 470, 60, 0, 2 * PI)
        ctx.fill()
        ellipse(ctx, lx, 468, 5, 10 + math.sin(t * 12) * 1.5)
        src(ctx, "#FFE36A")
        ctx.fill()


def prison(ctx, t, dawn=0.0):
    src(ctx, "#2A2622")
    ctx.paint()
    rnd = random.Random(7)
    for row in range(12):
        for col in range(16):
            off = 45 if row % 2 else 0
            rrect(ctx, col * 90 - off + 3, row * 60 + 3, 84, 54, 6)
            src(ctx, mix("#4A443C", "#36312B", rnd.random()))
            ctx.fill()
    # barred window
    rrect(ctx, 820, 120, 200, 150, 6)
    src(ctx, mix("#1A2240", "#F2C27A", dawn))
    ctx.fill()
    for bx in range(840, 1020, 36):
        ctx.rectangle(bx, 120, 8, 150)
    src(ctx, "#1A1714")
    ctx.fill()
    # light beam
    a = 0.12 + 0.3 * dawn
    ctx.move_to(820, 270)
    ctx.line_to(1020, 270)
    ctx.line_to(760, 640)
    ctx.line_to(420, 640)
    ctx.close_path()
    src(ctx, mix("#9FB4E0", "#FFE7A8", dawn), a)
    ctx.fill()
    ctx.rectangle(0, 620, W, 100)
    src(ctx, "#1E1B18")
    ctx.fill()
    # chains on the wall
    for i in range(8):
        ellipse(ctx, 180, 260 + i * 18, 6, 9)
        src(ctx, "#6E6A64")
        ctx.set_line_width(3)
        ctx.stroke()


def writing_desk(ctx, t, x=640):
    rrect(ctx, x - 160, 520, 320, 22, 4)
    fill_stroke(ctx, "#6A4A30", "#2E1E10", 3)
    ctx.rectangle(x - 150, 542, 14, 90)
    ctx.rectangle(x + 136, 542, 14, 90)
    src(ctx, "#4A3420")
    ctx.fill()
    rrect(ctx, x - 90, 506, 150, 16, 4)
    fill_stroke(ctx, "#E8D9B0", "#8A7444", 2)
    for i in range(3):
        ctx.move_to(x - 80, 512 + i * 3)
        ctx.line_to(x + 40, 512 + i * 3)
    src(ctx, "#6A5A3A", 0.6)
    ctx.set_line_width(1)
    ctx.stroke()
    cx = x + 110
    ctx.rectangle(cx - 6, 480, 12, 40)
    src(ctx, "#F2EEE4")
    ctx.fill()
    g = cairo.RadialGradient(cx, 470, 0, cx, 470, 260)
    g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.45)
    g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
    ctx.set_source(g)
    ctx.arc(cx, 470, 260, 0, 2 * PI)
    ctx.fill()
    ellipse(ctx, cx, 470, 5, 11 + math.sin(t * 11) * 1.5)
    src(ctx, "#FFE36A")
    ctx.fill()


def city_street(ctx, t):
    sky(ctx, "#6A3A2A", "#C98A5A")
    for i, bx in enumerate((60, 280, 520, 760, 1000, 1200)):
        h = 220 + (i * 53) % 120
        ctx.rectangle(bx - 90, 600 - h, 190, h)
        src(ctx, mix("#8A6A4A", "#5A3A2A", (i % 3) / 3))
        ctx.fill()
        rrect(ctx, bx - 20, 600 - h + 40, 40, 50, 20)
        src(ctx, "#2A1A10")
        ctx.fill()
    ctx.rectangle(0, 600, W, 120)
    src(ctx, "#7A5A3A")
    ctx.fill()


def damascus_road(ctx, t, light=0.0):
    sky(ctx, "#E8C890", "#F2E2B8")
    ctx.move_to(0, 480)
    for x in range(0, W + 60, 60):
        ctx.line_to(x, 470 + math.sin(x * 0.006) * 30)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, "#D9B07A")
    ctx.fill()
    ctx.move_to(560, 480)
    ctx.line_to(720, 480)
    ctx.line_to(1000, H)
    ctx.line_to(280, H)
    ctx.close_path()
    src(ctx, "#C49A64")
    ctx.fill()
    if light > 0:
        ctx.move_to(560, -20)
        ctx.line_to(720, -20)
        ctx.line_to(980, 660)
        ctx.line_to(300, 660)
        ctx.close_path()
        g = cairo.LinearGradient(0, 0, 0, 660)
        g.add_color_stop_rgba(0, 1, 1, 0.95, 0.95 * light)
        g.add_color_stop_rgba(1, 1, 1, 0.9, 0.5 * light)
        ctx.set_source(g)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 0.95, 0.5 * light)
        ctx.paint()


def journey(ctx, t, phase):
    """phase: 'storm', 'desert', 'danger', 'dusk', 'dawn', 'cosmos', 'glory'."""
    if phase == "storm":
        sky(ctx, "#2A3040", "#4A5060")
        flash = max(0.0, math.sin(t * 1.3) ** 40)
        if flash > 0.1:
            ctx.set_source_rgba(1, 1, 1, 0.35 * flash)
            ctx.paint()
            ctx.move_to(900, 0)
            ctx.line_to(860, 120)
            ctx.line_to(900, 130)
            ctx.line_to(840, 280)
            src(ctx, "#FFFFFF", flash)
            ctx.set_line_width(4)
            ctx.stroke()
        ground, gcol = 600, "#3A4038"
    elif phase == "desert":
        sky(ctx, "#E8A85A", "#F2DCA8")
        ellipse(ctx, 1000, 150, 70, 70)
        src(ctx, "#FFF2C8")
        ctx.fill()
        ground, gcol = 600, "#D9A86A"
    elif phase == "danger":
        sky(ctx, "#4A1A1A", "#9A3A2A")
        ground, gcol = 600, "#3A2420"
    elif phase == "dusk":
        sky(ctx, "#4A3A6A", "#E89A6A")
        ground, gcol = 600, "#4A5A3A"
    elif phase == "dawn":
        sky(ctx, "#F2C27A", "#FFF2D8")
        g = cairo.RadialGradient(640, 520, 20, 640, 520, 700)
        g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.9)
        g.add_color_stop_rgba(1, 1, 0.8, 0.5, 0)
        ctx.set_source(g)
        ctx.paint()
        ground, gcol = 600, "#7A9A5A"
    elif phase == "cosmos":
        sky(ctx, "#05061A", "#1A1A3A")
        rnd = random.Random(9)
        for i in range(160):
            sparkle(ctx, rnd.uniform(0, W), rnd.uniform(0, 600), rnd.uniform(1, 4) * (0.6 + 0.4 * math.sin(t * 2 + i)),
                    "#F2E8C8", 0.9)
        ground, gcol = 610, "#14142A"
    else:  # glory
        sky(ctx, "#FFE7A8", "#FFF8E8")
        ground, gcol = 600, "#9AB86A"
    # hills
    ctx.move_to(0, ground)
    for x in range(0, W + 80, 80):
        ctx.line_to(x, ground - 30 + math.sin(x * 0.008 + 1) * 24)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    src(ctx, gcol)
    ctx.fill()
    if phase == "storm":
        rnd = random.Random(4)
        for i in range(260):
            x = rnd.uniform(-100, W + 100)
            y = (rnd.uniform(0, H) + t * 1000) % (H + 40) - 40
            ctx.move_to(x, y)
            ctx.line_to(x - 12, y + 26)
        src(ctx, "#B8C8E0", 0.5)
        ctx.set_line_width(1.6)
        ctx.stroke()
    if phase == "desert":
        for i in range(12):
            x = 60 + i * 110
            ctx.move_to(x, 640)
            ctx.line_to(x + 40, 660)
            ctx.line_to(x + 20, 690)
            src(ctx, "#A8783A", 0.6)
            ctx.set_line_width(2)
            ctx.stroke()
    if phase == "danger":
        for i, sx in enumerate((150, 260, 1000, 1120)):
            ctx.move_to(sx, 600)
            ctx.line_to(sx + (i % 2) * 20, 300)
            src(ctx, "#1A0A0A")
            ctx.set_line_width(6)
            ctx.stroke()
            ctx.move_to(sx - 12, 300)
            ctx.line_to(sx + (i % 2) * 20, 260)
            ctx.line_to(sx + 12 + (i % 2) * 20, 300)
            ctx.close_path()
            src(ctx, "#1A0A0A")
            ctx.fill()
    if phase in ("dawn", "glory"):
        # a cross on the far hill
        cx, cy = 640, ground - 40
        ctx.rectangle(cx - 6, cy - 150, 12, 150)
        ctx.rectangle(cx - 46, cy - 120, 92, 12)
        src(ctx, "#4A3420" if phase == "dawn" else "#7A5A3A")
        ctx.fill()
        rays = 1.0 if phase == "glory" else 0.5
        for i in range(16):
            a = i * PI / 8 + t * 0.05
            ctx.move_to(cx, cy - 114)
            ctx.line_to(cx + math.cos(a - 0.05) * 900, cy - 114 + math.sin(a - 0.05) * 900)
            ctx.line_to(cx + math.cos(a + 0.05) * 900, cy - 114 + math.sin(a + 0.05) * 900)
            ctx.close_path()
            src(ctx, "#FFFFFF", 0.08 * rays)
            ctx.fill()


# ---------------------------------------------------------------- cards
def chapter_card(ctx, t, ref, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    g = cairo.RadialGradient(640, 360, 40, 640, 360, 760)
    g.add_color_stop_rgb(0, *rgb("#3A2A1A"))
    g.add_color_stop_rgb(1, *rgb("#0E0A06"))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(11)
    for i in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        sparkle(ctx, x, y, rnd.uniform(1, 3) * (0.6 + 0.4 * math.sin(t * 2 + i)), "#F2DCA8", 0.6)
    ctx.select_font_face(TITLE_FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(68)
    ext = ctx.text_extents(ref)
    ctx.move_to(640 - ext.width / 2 - ext.x_bearing, 380)
    ctx.text_path(ref)
    src(ctx, "#000000")
    ctx.set_line_width(6)
    ctx.stroke_preserve()
    src(ctx, "#F2DCA8")
    ctx.fill()
    ctx.move_to(460, 420)
    ctx.line_to(820, 420)
    src(ctx, "#C9A060")
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
