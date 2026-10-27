"""24-hour diner at 2 AM: booth, rainy window, wall TV, table props.

World coordinates match the 1080x1920 wide shot. `light` controls the
night -> dawn change, `rain` the storm intensity.
"""
import math

import numpy as np
import skia

from gfx import (Rng, clamp, draw_text, fill, font, hexc, linear_shader, mixhex, radial_shader, smooth_path,
                 stroke)

W, H = 1080, 1920
WIN = (100.0, 300.0, 980.0, 1005.0)
TV_RECT = (772.0, 78.0, 1012.0, 236.0)
TABLE_FAR, TABLE_NEAR = 1270.0, 1430.0
TABLE_X = (150.0, 930.0, 110.0, 970.0)  # far left, far right, near left, near right
OUTLINE = "#1a1216"


class Cam:
    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0):
        self.cx, self.cy, self.zoom = cx, cy, zoom

    def apply(self, c, par=1.0):
        z = 1 + (self.zoom - 1) * par
        cx = W / 2 + (self.cx - W / 2) * par
        cy = H / 2 + (self.cy - H / 2) * par
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-cx, -cy)

    def to_screen(self, x, y, par=1.0):
        z = 1 + (self.zoom - 1) * par
        cx = W / 2 + (self.cx - W / 2) * par
        cy = H / 2 + (self.cy - H / 2) * par
        return (x - cx) * z + W / 2, (y - cy) * z + H / 2


def lerp_cam(a, b, t):
    return Cam(a.cx + (b.cx - a.cx) * t, a.cy + (b.cy - a.cy) * t,
               math.exp(math.log(a.zoom) + (math.log(b.zoom) - math.log(a.zoom)) * t))


# --------------------------------------------------------------------------- outside
_r = Rng(21)
BUILDINGS = []
x = WIN[0] - 120
while x < WIN[2] + 120:
    w_ = _r.u(90, 170)
    h_ = _r.u(170, 330)
    BUILDINGS.append((x, w_, h_, _r.u(0, 1)))
    x += w_ + _r.u(4, 18)
_r2 = Rng(5)
LIT = [(_r2.u(), _r2.u(), _r2.u()) for _ in range(160)]
_r3 = Rng(9)
BOKEH = [(_r3.u(WIN[0], WIN[2]), _r3.u(700, 940), _r3.u(10, 28), _r3.u()) for _ in range(26)]
_r4 = Rng(13)
DROPS = [(_r4.u(WIN[0] + 10, WIN[2] - 10), _r4.u(WIN[1] + 10, WIN[3] - 10), _r4.u(2.0, 6.5), _r4.u(0, 9)) for _ in range(120)]
_r5 = Rng(17)
STREAKS = [(_r5.u(WIN[0] - 60, WIN[2]), _r5.u(0, 1), _r5.u(0.6, 1.0)) for _ in range(70)]


def draw_outside(c, t, light, rain):
    x0, y0, x1, y1 = WIN
    night_top, night_bot = "#0b1430", "#1d2c4e"
    dawn_top, dawn_bot = "#f2b48d", "#ffd9b0"
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((0, y0), (0, y1), [hexc(mixhex(night_top, dawn_top, light)),
                                                 hexc(mixhex(night_bot, dawn_bot, light))]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)
    # buildings across the street
    for (bx, bw, bh, sh) in BUILDINGS:
        top = 860 - bh
        col = mixhex(mixhex("#0c1530", "#162244", sh), mixhex("#7a5a6e", "#8e6a78", sh), light)
        c.drawRect(skia.Rect.MakeLTRB(bx, top, bx + bw, 900), fill(hexc(col)))
        cols = max(2, int(bw // 34))
        for i, (u, v, on) in enumerate(LIT[: cols * 5]):
            cx_ = bx + 12 + (i % cols) * 32
            cy_ = top + 18 + (i // cols) * 38
            if cy_ > 840 or cx_ > bx + bw - 18:
                continue
            if on < 0.42 * (1 - light):
                c.drawRect(skia.Rect.MakeLTRB(cx_, cy_, cx_ + 14, cy_ + 18), fill(hexc("#ffcf7a", 0.85)))
    # street + curb
    c.drawRect(skia.Rect.MakeLTRB(x0, 900, x1, y1), fill(hexc(mixhex("#141b2e", "#8b7882", light))))
    c.drawRect(skia.Rect.MakeLTRB(x0, 892, x1, 902), fill(hexc(mixhex("#2a3350", "#b39aa0", light))))
    # streetlamp glow
    lamp_a = 1 - light
    if lamp_a > 0.02:
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((250, 560), 260, [hexc("#ffcf8a", 0.45 * lamp_a), hexc("#ffcf8a", 0.0)]))
        c.drawCircle(250, 560, 260, g)
    c.drawLine(250, 560, 250, 900, stroke(hexc(mixhex("#0e1426", "#6a5560", light)), 8))
    c.drawCircle(250, 556, 12, fill(hexc(mixhex("#ffe2a8", "#c8a99a", light))))
    # parked cruiser (her car) across the window
    car = smooth_path([(560, 935), (565, 890), (610, 880), (650, 846), (790, 842), (840, 876), (900, 884), (912, 935)],
                      True, 0.25)
    c.drawPath(car, fill(hexc(mixhex("#0d1222", "#4e4652", light))))
    c.drawRect(skia.Rect.MakeLTRB(655, 878, 835, 904), fill(hexc(mixhex("#cfd4de", "#e6dcd8", light), 0.25 + 0.2 * light)))
    c.drawRoundRect(skia.Rect.MakeLTRB(700, 834, 760, 844), 3, 3, fill(hexc(mixhex("#3a1a2a", "#5a4a5a", light))))
    for wx in (600, 870):
        c.drawCircle(wx, 935, 22, fill(hexc(mixhex("#06080f", "#3a3038", light))))
    # wet street reflections
    for (bx, by, r, ph) in BOKEH:
        a = (0.28 if ph > 0.5 else 0.18) * (1 - light)
        if a <= 0.01:
            continue
        col = "#ffcf7a" if ph > 0.35 else ("#ff6f91" if ph > 0.15 else "#8fb8ff")
        c.drawOval(skia.Rect.MakeLTRB(bx - r * 0.5, by + 40, bx + r * 0.5, by + 40 + r * 2.4), fill(hexc(col, a), blur=6))
        c.drawCircle(bx, by, r * 0.5, fill(hexc(col, a * 0.9), blur=4))
    # rain streaks outside (slow, faint)
    if rain > 0.01:
        sp = stroke(hexc("#b9cdf0", 0.22 * rain), 1.6)
        for (sx, ph, sp_) in STREAKS:
            fr = (ph + t * 1.25 * sp_) % 1.0
            yy = y0 + fr * (y1 - y0 + 80) - 40
            c.drawLine(sx, yy, sx + 18, yy + 70, sp)


def draw_window(c, t, light, rain):
    x0, y0, x1, y1 = WIN
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.ClipOp.kIntersect, True)
    draw_outside(c, t, light, rain)
    # neon coffee cup sign hanging in the window (seen from inside)
    nx, ny = 300, 420
    neon = "#ff6f91"
    na = 1.0 - 0.8 * light
    g = skia.Paint(AntiAlias=True)
    g.setShader(radial_shader((nx, ny), 150, [hexc(neon, 0.35 * na), hexc(neon, 0.0)]))
    c.drawCircle(nx, ny, 150, g)
    cup = smooth_path([(nx - 46, ny - 30), (nx + 46, ny - 30), (nx + 36, ny + 34), (nx - 36, ny + 34)], True, 0.1)
    for wdt, a in ((14, 0.25), (6, 0.95)):
        c.drawPath(cup, stroke(hexc(neon, a * na), wdt))
        hp = skia.Path()
        hp.addArc(skia.Rect.MakeLTRB(nx + 30, ny - 18, nx + 70, ny + 18), -90, 180)
        c.drawPath(hp, stroke(hexc(neon, a * na), wdt))
    for k in (-1, 0, 1):
        sx = nx + k * 18
        c.drawPath(smooth_path([(sx, ny - 44), (sx + 8, ny - 60), (sx - 4, ny - 78)], False),
                   stroke(hexc("#ffd0dc", 0.8 * na), 4))
    # droplets on the glass
    if rain > 0.01:
        for (dx, dy, r, ph) in DROPS:
            yy = dy + (t * 6 * (0.3 + 0.1 * (ph % 1))) % 40 if ph > 7.5 else dy
            a = rain * 0.7
            c.drawCircle(dx, yy, r, fill(hexc("#d7e6ff", 0.16 * a)))
            c.drawCircle(dx - r * 0.3, yy - r * 0.3, r * 0.35, fill(hexc("#ffffff", 0.5 * a)))
    # cool window light spill
    c.restore()
    # frame + mullions
    fr = hexc(mixhex("#9aa3b2", "#d9d2c8", light))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), stroke(fr, 14))
    for mx in (393, 687):
        c.drawLine(mx, y0, mx, y1, stroke(fr, 10))
    c.drawLine(x0, y1 + 6, x1, y1 + 6, stroke(hexc(mixhex("#c9ccd2", "#efe6da", light)), 12))


def draw_tv(c, t, light, cues=None, lt=0.0):
    x0, y0, x1, y1 = TV_RECT
    # bracket
    c.drawLine((x0 + x1) / 2, 0, (x0 + x1) / 2, y0, stroke(hexc("#20242c"), 10))
    c.drawRoundRect(skia.Rect.MakeLTRB(x0 - 10, y0 - 10, x1 + 10, y1 + 10), 8, 8, fill(hexc("#121418")))
    draw_tv_screen(c, x0, y0, x1, y1, t, cues or {}, lt)
    # glow on the wall
    g = skia.Paint(AntiAlias=True)
    g.setShader(radial_shader(((x0 + x1) / 2, (y0 + y1) / 2), 240, [hexc("#6fa8ff", 0.10 * (1 - light)), hexc("#6fa8ff", 0.0)]))
    c.drawCircle((x0 + x1) / 2, (y0 + y1) / 2, 240, g)


def draw_tv_screen(c, x0, y0, x1, y1, t, cues, lt):
    w, h = x1 - x0, y1 - y0
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.ClipOp.kIntersect, True)
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((x0, y0), (x1, y1), [hexc("#0e2a52"), hexc("#14386b")]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)
    # headline card
    c.drawRect(skia.Rect.MakeLTRB(x0, y0 + h * 0.06, x0 + w * 0.36, y0 + h * 0.2), fill(hexc("#d7263d")))
    draw_text(c, "BREAKING", x0 + w * 0.18, y0 + h * 0.17, font(13, "black"), hexc("#ffffff"))
    draw_text(c, "NO-FORCE LAW", x0 + w * 0.5, y0 + h * 0.43, font(27, "black"), hexc("#ffffff"))
    draw_text(c, "BEGINS AT SUNRISE", x0 + w * 0.5, y0 + h * 0.58, font(17, "bold"), hexc("#ffd36b"))
    # icons: no grabbing hand, no cage, consent handshake
    iy = y0 + h * 0.72
    icons = [("hand", cues.get("touch", 99)), ("cage", 0.0), ("ok", cues.get("consent", 99))]
    for k, (kind, tc) in enumerate(icons):
        cx = x0 + w * (0.26 + 0.24 * k)
        pop = clamp((lt - tc) / 0.25) if tc < 90 else 1.0
        s = 0.6 + 0.4 * pop + 0.18 * math.sin(math.pi * clamp((lt - tc) / 0.35)) if tc < 90 else 1.0
        c.save()
        c.translate(cx, iy)
        c.scale(s, s)
        col = hexc("#ffffff", 0.95)
        if kind == "hand":
            c.drawRoundRect(skia.Rect.MakeLTRB(-9, -8, 9, 12), 5, 5, stroke(col, 2.5))
            for fx in (-6, -2, 2, 6):
                c.drawLine(fx, -8, fx, -15, stroke(col, 2.5))
        elif kind == "cage":
            c.drawRect(skia.Rect.MakeLTRB(-12, -13, 12, 13), stroke(col, 2.5))
            for fx in (-6, 0, 6):
                c.drawLine(fx, -13, fx, 13, stroke(col, 2))
        else:
            c.drawCircle(0, 0, 13, stroke(hexc("#7fe3a0"), 2.5))
            c.drawPath(smooth_path([(-7, 0), (-2, 6), (8, -6)], False), stroke(hexc("#7fe3a0"), 3))
        if kind != "ok":
            c.drawCircle(0, 0, 17, stroke(hexc("#ff5a6e"), 3))
            c.drawLine(-12, 12, 12, -12, stroke(hexc("#ff5a6e"), 3))
        c.restore()
    # ticker
    c.drawRect(skia.Rect.MakeLTRB(x0, y1 - h * 0.13, x1, y1), fill(hexc("#081a33")))
    tick = "NO CAGES  •  NO TOUCH WITHOUT CONSENT  •  POLICE, SOLDIERS AND CITIZENS ALIKE  •  "
    f = font(11, "bold")
    tw = f.measureText(tick)
    off = (t * 28) % tw
    for k in range(3):
        c.drawString(tick, x0 + 6 - off + k * tw, y1 - h * 0.035, f, fill(hexc("#d8e6ff")))
    c.restore()
    # glass sheen
    c.drawLine(x0 + w * 0.65, y0 + 4, x0 + w * 0.95, y0 + 4, stroke(hexc("#ffffff", 0.08), 6))


def draw_room(c, cam, t, light=0.0, rain=1.0, tv_cues=None, tv_lt=0.0):
    """Everything behind the characters."""
    c.save()
    cam.apply(c, 1.0)
    # wall
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((0, -300), (0, 2200), [hexc(mixhex("#18303a", "#5a6466", light)),
                                                    hexc(mixhex("#10222b", "#3c4446", light))]))
    c.drawRect(skia.Rect.MakeLTRB(-600, -600, 1700, 2600), p)
    # wainscot under the window
    c.drawRect(skia.Rect.MakeLTRB(-600, 1012, 1700, 2600), fill(hexc(mixhex("#0e1c24", "#3a3c3e", light))))
    for xx in range(-600, 1700, 70):
        c.drawLine(xx, 1012, xx, 2600, stroke(hexc("#000000", 0.18), 3))
    draw_window(c, t, light, rain)
    # cool spill from the window onto the wall below it
    g = skia.Paint(AntiAlias=True)
    g.setShader(linear_shader((0, 1005), (0, 1300), [hexc(mixhex("#6f8fd0", "#ffd7a8", light), 0.16), hexc("#000000", 0.0)]))
    c.drawRect(skia.Rect.MakeLTRB(WIN[0], 1005, WIN[2], 1300), g)
    draw_tv(c, t, light, tv_cues, tv_lt)
    # pendant lamp
    lx, ly = 540, 236
    c.drawLine(lx, -600, lx, ly - 40, stroke(hexc("#0c0c10"), 4))
    shade = smooth_path([(lx - 26, ly - 44), (lx + 26, ly - 44), (lx + 76, ly + 6), (lx - 76, ly + 6)], True, 0.15)
    c.drawPath(shade, stroke(hexc(OUTLINE), 5))
    c.drawPath(shade, fill(hexc("#24503f")))
    c.drawOval(skia.Rect.MakeLTRB(lx - 76, ly - 2, lx + 76, ly + 14), fill(hexc("#ffe2a6", 0.95 - 0.5 * light)))
    c.restore()


def draw_lamp_light(c, cam, light):
    """Warm cone from the lamp over the booth (drawn over the room, under the characters)."""
    c.save()
    cam.apply(c, 1.0)
    g = skia.Paint(AntiAlias=True)
    a = 0.22 * (1 - 0.6 * light)
    g.setShader(radial_shader((540, 1150), 620, [hexc("#ffcf8a", a), hexc("#ffb060", a * 0.4), hexc("#ffb060", 0.0)],
                              [0.0, 0.5, 1.0]))
    c.drawRect(skia.Rect.MakeLTRB(-100, 300, 1180, 1800), g)
    c.restore()


def draw_seats(c, cam, light):
    c.save()
    cam.apply(c, 1.0)
    for (x0, x1) in ((40, 452), (628, 1040)):
        r = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, 860, x1, 1420), 40, 40)
        c.drawRRect(r, stroke(hexc(OUTLINE), 7))
        c.drawRRect(r, fill(hexc(mixhex("#6a2230", "#8a3a42", light))))
        for k in range(1, 6):
            xx = x0 + (x1 - x0) * k / 6
            c.drawLine(xx, 900, xx, 1400, stroke(hexc("#4a1520", 0.8), 4))
        c.drawRoundRect(skia.Rect.MakeLTRB(x0 + 6, 866, x1 - 6, 900), 18, 18, fill(hexc("#ffffff", 0.10)))
    c.restore()


def table_path():
    fl, fr, nl, nr = TABLE_X
    p = skia.Path()
    p.moveTo(fl, TABLE_FAR)
    p.lineTo(fr, TABLE_FAR)
    p.lineTo(nr, TABLE_NEAR)
    p.lineTo(nl, TABLE_NEAR)
    p.close()
    return p


def draw_floor(c, light):
    """Checkered diner floor in perspective, booth bench fronts, the table pedestal."""
    y0, vx, vy = TABLE_NEAR + 18, 540.0, 640.0
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-600, y0, 1700, 2600), skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(-600, y0, 1700, 2600), fill(hexc(mixhex("#0d0c12", "#2b2729", light))))
    dark, lite = hexc(mixhex("#121118", "#2e2a2c", light)), hexc(mixhex("#5d5952", "#c9bfb2", light))
    ys = [y0]
    h = 34.0
    while ys[-1] < 2600:
        ys.append(ys[-1] + h)
        h *= 1.2
    xs = [-1200 + 120 * k for k in range(30)]

    def px(x, y):
        return vx + (x - vx) * (y - vy) / (y0 - vy)
    for r in range(len(ys) - 1):
        for k in range(len(xs) - 1):
            ya, yb = ys[r], ys[r + 1]
            p = skia.Path()
            p.moveTo(px(xs[k], ya), ya)
            p.lineTo(px(xs[k + 1], ya), ya)
            p.lineTo(px(xs[k + 1], yb), yb)
            p.lineTo(px(xs[k], yb), yb)
            p.close()
            c.drawPath(p, fill(lite if (r + k) % 2 else dark))
    # light pooling on the floor from the window / dawn
    g = skia.Paint(AntiAlias=True)
    g.setShader(linear_shader((0, y0), (0, y0 + 420), [hexc("#000000", 0.0), hexc("#05040a", 0.55)]))
    c.drawRect(skia.Rect.MakeLTRB(-600, y0, 1700, 2600), g)
    c.restore()
    # bench fronts below the table edge
    for (x0, x1) in ((40, 452), (628, 1040)):
        c.drawRect(skia.Rect.MakeLTRB(x0, y0 - 10, x1, y0 + 120), fill(hexc(mixhex("#3c111b", "#5e2730", light))))
        c.drawRect(skia.Rect.MakeLTRB(x0, y0 + 108, x1, y0 + 124), fill(hexc(mixhex("#6f7580", "#b9bec6", light))))
        for k in range(1, 6):
            xx = x0 + (x1 - x0) * k / 6
            c.drawLine(xx, y0 - 10, xx, y0 + 106, stroke(hexc("#000000", 0.25), 3))
    # pedestal + its shadow
    c.drawOval(skia.Rect.MakeLTRB(400, y0 + 150, 680, y0 + 200), fill(hexc("#000000", 0.45), blur=10))
    c.drawRect(skia.Rect.MakeLTRB(512, y0 - 6, 568, y0 + 175), fill(hexc(mixhex("#2a2e36", "#6a6e76", light))))
    c.drawRect(skia.Rect.MakeLTRB(520, y0 - 6, 530, y0 + 175), fill(hexc("#ffffff", 0.12)))
    c.drawOval(skia.Rect.MakeLTRB(450, y0 + 160, 630, y0 + 190), fill(hexc(mixhex("#2a2e36", "#6a6e76", light))))


def draw_table(c, cam, t, light, props):
    c.save()
    cam.apply(c, 1.0)
    fl, fr, nl, nr = TABLE_X
    draw_floor(c, light)
    tp = table_path()
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((0, TABLE_FAR), (0, TABLE_NEAR), [hexc(mixhex("#b9d3c4", "#e7efe6", light)),
                                                                 hexc(mixhex("#d7e8dc", "#f4f6ee", light))]))
    c.drawPath(tp, p)
    # boomerang speckles
    rng = Rng(3)
    for _ in range(28):
        x = rng.u(fl + 20, fr - 20)
        y = rng.u(TABLE_FAR + 10, TABLE_NEAR - 10)
        c.drawLine(x, y, x + 12, y - 4, stroke(hexc("#7aa596", 0.35), 3))
    # chrome edge
    c.drawRect(skia.Rect.MakeLTRB(nl, TABLE_NEAR, nr, TABLE_NEAR + 22), fill(hexc("#aab0ba")))
    c.drawRect(skia.Rect.MakeLTRB(nl, TABLE_NEAR + 3, nr, TABLE_NEAR + 8), fill(hexc("#eef2f8")))
    c.drawPath(tp, stroke(hexc(OUTLINE, 0.6), 3))
    for pr in props:
        pr(c)
    c.restore()


# --------------------------------------------------------------------------- table props

def prop_mug(x, y, steam, t, s=1.0):
    from rig import draw_mug

    def f(c):
        draw_mug(c, x, y, 1.25 * s, "#f2efe8", 0.0, steam, t, dots=False)
    return f


def prop_belt(x, y, cuffs_only=False):
    def f(c):
        c.save()
        c.translate(x, y)
        if not cuffs_only:
            belt = smooth_path([(-120, 10), (-60, -22), (40, -26), (120, -6), (110, 18), (20, 26), (-80, 30)], True, 0.5)
            c.drawPath(belt, stroke(hexc(OUTLINE), 5))
            c.drawPath(belt, stroke(hexc("#16161b"), 16))
            c.drawRoundRect(skia.Rect.MakeLTRB(52, -40, 92, 8), 6, 6, fill(hexc("#24242a")))  # radio
            c.drawLine(62, -40, 62, -60, stroke(hexc("#24242a"), 5))
        for k, cx in enumerate((-30, 6)):
            c.drawOval(skia.Rect.MakeLTRB(cx - 18, -12, cx + 18, 16), stroke(hexc(OUTLINE), 9))
            c.drawOval(skia.Rect.MakeLTRB(cx - 18, -12, cx + 18, 16), stroke(hexc("#c7cdd6"), 5))
        c.drawLine(-12, 2, -12, 2, stroke(hexc("#c7cdd6"), 4))
        c.drawLine(-14, 2, -10, 2, stroke(hexc("#c7cdd6"), 6))
        c.restore()
    return f


def prop_sketchbook(x, y, page_doodle=0.0):
    def f(c):
        c.save()
        c.translate(x, y)
        book = smooth_path([(-90, -32), (90, -36), (100, 34), (-100, 38)], True, 0.1)
        c.drawPath(book, stroke(hexc(OUTLINE), 5))
        c.drawPath(book, fill(hexc("#f3ead8")))
        c.drawLine(0, -35, 0, 36, stroke(hexc("#c9bda4"), 3))
        k = int(page_doodle * 6)
        for j in range(k):
            yy = -22 + j * 9
            c.drawLine(-80 + (j % 2) * 8, yy, -20 - (j % 3) * 10, yy + 2, stroke(hexc("#2b2a33", 0.7), 2))
        c.drawCircle(46, -6, 14, stroke(hexc("#2b2a33", 0.6), 2))
        c.restore()
    return f


def prop_condiments(x, y, light):
    def f(c):
        c.save()
        c.translate(x, y)
        # napkin dispenser
        c.drawRoundRect(skia.Rect.MakeLTRB(-34, -46, 34, 6), 6, 6, stroke(hexc(OUTLINE), 5))
        c.drawRoundRect(skia.Rect.MakeLTRB(-34, -46, 34, 6), 6, 6, fill(hexc("#b8bec8")))
        c.drawRect(skia.Rect.MakeLTRB(-22, -40, 22, -30), fill(hexc("#f5f5f0")))
        # sugar jar
        c.drawRoundRect(skia.Rect.MakeLTRB(44, -40, 74, 6), 8, 8, fill(hexc("#e9edf2", 0.8)))
        c.drawRect(skia.Rect.MakeLTRB(44, -50, 74, -38), fill(hexc("#c9ced6")))
        # ketchup
        c.drawRoundRect(skia.Rect.MakeLTRB(-74, -60, -46, 6), 9, 9, stroke(hexc(OUTLINE), 4))
        c.drawRoundRect(skia.Rect.MakeLTRB(-74, -60, -46, 6), 9, 9, fill(hexc("#c8263a")))
        c.drawRect(skia.Rect.MakeLTRB(-66, -72, -54, -58), fill(hexc("#c8263a")))
        c.restore()
    return f
