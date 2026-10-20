"""Backgrounds and props: a crooked gothic kitchen at midnight."""
import math

import skia

from gfx import (CANDLE, GRAPHITE, H, INK, MOON, NIGHT_BLUE, NIGHT_DEEP, PAPER, PUMPKIN, W, Xf, circle, clamp,
                 ellipse, fill, glow, lerp, lin_grad, noise1, open_path, pencil, poly, rad_grad, rng,
                 rounded_poly, smooth_path, spiral_pts, stroke, wobble)
from letters import draw_text
from mice import draw_mouse, pose as mpose

WALL_A = (30, 22, 50)
WALL_B = (21, 15, 37)
WOOD = (52, 32, 42)
WOOD_HI = (84, 56, 66)
FRAME = (22, 15, 26)


# ------------------------------------------------------------------ sky & outside
def draw_sky(c, rect, moon, t, stars=True, seed=1):
    x0, y0, x1, y1 = rect
    mx, my, mr = moon
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1),
               fill((0, 0, 0), 1.0, rad_grad((mx, my), max(x1 - x0, y1 - y0) * 1.1,
                                             [(44, 86, 110), (24, 44, 78), (12, 16, 40)], [0.0, 0.35, 1.0])))
    if stars:
        r = rng("stars", seed)
        for _ in range(int((x1 - x0) * (y1 - y0) / 9000)):
            sx, sy = r.uniform(x0, x1), r.uniform(y0, y1)
            if math.hypot(sx - mx, sy - my) < mr * 1.6:
                continue
            ts = math.floor(t * 2.0) / 2.0
            tw = 0.55 + 0.45 * math.sin(ts * r.uniform(0.6, 1.6) + r.uniform(0, 6))
            c.drawCircle(sx, sy, r.uniform(1.0, 2.6), fill((230, 230, 255), 0.35 + 0.4 * tw))


def draw_moon(c, x, y, r, a=1.0):
    glow(c, x, y, r * 2.6, (150, 190, 215), 0.35 * a)
    c.drawCircle(x, y, r, fill(MOON, a, rad_grad((x - r * 0.25, y - r * 0.25), r * 1.3,
                                                 [(250, 250, 228), (232, 234, 204), (196, 204, 182)])))
    rr = rng("moon")
    for _ in range(9):  # soft craters
        cx, cy = x + rr.uniform(-0.6, 0.6) * r, y + rr.uniform(-0.6, 0.6) * r
        cr = rr.uniform(0.06, 0.18) * r
        c.drawCircle(cx, cy, cr, fill((170, 178, 160), 0.22 * a))


def draw_clouds(c, t, rect, moon, seed=3):
    x0, y0, x1, y1 = rect
    rr = rng("clouds", seed)
    for i in range(4):
        cy = lerp(y0, y1, rr.uniform(0.25, 0.85))
        cx = lerp(x0, x1, rr.uniform(0, 1)) + math.floor(t * 2.0) / 2.0 * rr.uniform(4, 9)
        cx = x0 + (cx - x0) % ((x1 - x0) + 500) - 250
        wdt = rr.uniform(260, 420)
        p = smooth_path([(cx - wdt / 2, cy), (cx - wdt * 0.2, cy - 24), (cx + wdt * 0.1, cy - 34), (cx + wdt / 2, cy - 6),
                         (cx + wdt * 0.2, cy + 10), (cx - wdt * 0.25, cy + 8)])
        c.drawPath(p, fill((60, 54, 96), 0.55))
        c.drawPath(open_path([(cx - wdt * 0.35, cy + 2), (cx, cy - 14), (cx + wdt * 0.4, cy - 4)]),
                   stroke((160, 170, 200), 2.0, 0.25))


def draw_tree(c, x, y, s, seed=0, col=(10, 8, 18)):
    """Twisted bare tree whose branches end in spirals."""
    with Xf(c, x, y, sx=s):
        trunk = smooth_path([(-40, 0), (-30, -200), (-60, -380), (-20, -520), (10, -520), (-10, -380), (30, -200),
                             (40, 0)])
        c.drawPath(trunk, fill(col))
        branches = [((-40, -380), (-180, -470), (-230, -600), 1), ((-20, -500), (40, -640), (150, -700), -1),
                    ((-30, -240), (-140, -280), (-230, -250), -1), ((0, -330), (120, -380), (190, -470), 1),
                    ((-10, -520), (-60, -650), (-20, -760), 1)]
        for (sx, sy), (mx, my), (ex, ey), d in branches:
            p = skia.Path()
            p.moveTo(sx, sy)
            p.quadTo(mx, my, ex, ey)
            c.drawPath(p, stroke(col, 16, cap="round"))
            sp = spiral_pts(ex + d * 26, ey, 26, 2, 1.5, a0=math.pi if d > 0 else 0, n=24, direction=d)
            c.drawPath(open_path([(ex, ey)] + sp), stroke(col, 8))


def draw_bat(c, x, y, s, phase, col=(8, 6, 14)):
    flap = math.sin(phase)
    with Xf(c, x, y, sx=s):
        for side in (-1, 1):
            wy = -14 * flap
            wing = smooth_path([(0, -4), (side * 22, -12 + wy * 0.5), (side * 46, -6 + wy), (side * 40, 4 + wy * 0.6),
                                (side * 30, 0 + wy * 0.4), (side * 22, 8 + wy * 0.2), (side * 10, 4)], tension=0.7)
            c.drawPath(wing, fill(col))
        c.drawOval(skia.Rect.MakeLTRB(-8, -9, 8, 10), fill(col))
        c.drawPath(poly([(-7, -6), (-5, -15), (-1, -7)]), fill(col))
        c.drawPath(poly([(7, -6), (5, -15), (1, -7)]), fill(col))


def draw_bats(c, t, rect, n=3, seed=5, speed=1.0):
    x0, y0, x1, y1 = rect
    rr = rng("bats", seed)
    for i in range(n):
        period = rr.uniform(14, 22) / speed
        off = rr.uniform(0, period)
        u = ((t + off) % period) / period
        x = lerp(x0 - 80, x1 + 80, u)
        y = lerp(y0, y1, rr.uniform(0.2, 0.8)) + math.sin(u * 9 + i) * 30
        draw_bat(c, x, y, rr.uniform(0.6, 1.1), t * rr.uniform(9, 13) + i)


def draw_cobweb(c, x, y, s, flip=1, t=0.0):
    with Xf(c, x, y, sx=s * flip, sy=s):
        col = (190, 196, 220)
        for i in range(6):
            a = math.radians(i * 18)
            c.drawLine(0, 0, math.cos(a) * 200, math.sin(a) * 200, stroke(col, 1.4, 0.35))
        for k in range(1, 6):
            r = k * 36
            p = skia.Path()
            for i in range(6):
                a = math.radians(i * 18)
                pt = (math.cos(a) * r, math.sin(a) * r)
                if i == 0:
                    p.moveTo(*pt)
                else:
                    a0 = math.radians((i - 0.5) * 18)
                    p.quadTo(math.cos(a0) * r * 0.86, math.sin(a0) * r * 0.86, *pt)
            c.drawPath(p, stroke(col, 1.2, 0.3))
        # dangling spider
        sy = 230 + 18 * math.sin(t * 1.3)
        c.drawLine(110, 100, 110, sy, stroke(col, 1.0, 0.45))
        c.drawCircle(110, sy + 8, 9, fill((12, 10, 18)))
        for j in range(4):
            for side in (-1, 1):
                c.drawLine(110, sy + 8, 110 + side * (16 + j % 2 * 4), sy + 2 + j * 5, stroke((12, 10, 18), 2.0))


def draw_window(c, rect, t, moon_rel=(0.58, 0.42), moon_r=0.38, frame_col=FRAME, bats=True, lean=-1.8,
                tree=True, cobweb=True, sill=True, clouds=True):
    """Tall crooked gothic window. rect = (x0, y0, x1, y1) of the outer frame."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    with Xf(c, cx, y1, rot=lean):
        c.translate(-cx, -y1)
        arch = skia.Path()
        arch.moveTo(x0, y1)
        arch.lineTo(x0, y0 + w * 0.5)
        arch.quadTo(x0 + w * 0.06, y0 + w * 0.08, cx, y0)
        arch.quadTo(x1 - w * 0.06, y0 + w * 0.08, x1, y0 + w * 0.5)
        arch.lineTo(x1, y1)
        arch.close()
        c.drawPath(arch, stroke((0, 0, 0), 30, 0.5, blur=10))
        c.save()
        c.clipPath(arch, skia.ClipOp.kIntersect, True)
        mx, my, mr = x0 + w * moon_rel[0], y0 + h * moon_rel[1], w * moon_r
        draw_sky(c, (x0, y0, x1, y1), (mx, my, mr), t)
        draw_moon(c, mx, my, mr)
        if clouds:
            draw_clouds(c, t, (x0, y0, x1, y1), (mx, my, mr))
        # distant crooked hill line and fence
        hill = smooth_path([(x0 - 40, y1), (x0 - 40, y1 - h * 0.14), (x0 + w * 0.3, y1 - h * 0.19),
                            (x0 + w * 0.7, y1 - h * 0.13), (x1 + 40, y1 - h * 0.17), (x1 + 40, y1)], closed=True)
        c.drawPath(hill, fill((14, 12, 26)))
        rr = rng("fence")
        for i in range(12):
            fx = x0 + i * w / 11
            fy = y1 - h * 0.15 + rr.uniform(-8, 8)
            with Xf(c, fx, fy, rot=rr.uniform(-12, 12)):
                c.drawPath(poly([(-6, 0), (-6, -54), (0, -66), (6, -54), (6, 0)]), fill((14, 12, 26)))
        if tree:
            draw_tree(c, x0 + w * 0.16, y1 - h * 0.1, h / 1100.0)
        if bats:
            draw_bats(c, t, (x0, y0 + h * 0.15, x1, y0 + h * 0.6))
        c.restore()
        # frame and crooked mullions
        c.drawPath(arch, stroke(frame_col, 28))
        c.drawPath(arch, stroke((60, 44, 70), 3, 0.6))
        mull = skia.Path()
        mull.moveTo(cx, y0 + 10)
        mull.quadTo(cx + 14, y0 + h * 0.5, cx - 6, y1)
        mull.moveTo(x0, y0 + h * 0.58)
        mull.quadTo(cx, y0 + h * 0.6 + 16, x1, y0 + h * 0.56)
        c.drawPath(mull, stroke(frame_col, 16))
        if cobweb:
            draw_cobweb(c, x0 + 14, y0 + w * 0.48, 0.9, 1, t)
        if sill:
            c.drawPath(poly([(x0 - 50, y1 - 4), (x1 + 50, y1 - 4), (x1 + 70, y1 + 34), (x0 - 70, y1 + 34)]), fill(WOOD))
            c.drawLine(x0 - 50, y1 - 2, x1 + 50, y1 - 2, stroke(WOOD_HI, 3, 0.6))
    return (x0 + w * moon_rel[0], y0 + h * moon_rel[1])


def draw_wall(c, rect, lean=1.2, a=WALL_A, b=WALL_B, stripe=58):
    x0, y0, x1, y1 = rect
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(a))
    with Xf(c, (x0 + x1) / 2, y1, rot=lean):
        c.translate(-(x0 + x1) / 2, -y1)
        n = int((x1 - x0) / stripe) + 6
        for i in range(-3, n):
            if i % 2 == 0:
                xx = x0 + i * stripe
                c.drawRect(skia.Rect.MakeLTRB(xx, y0 - 200, xx + stripe * 0.5, y1 + 200), fill(b))
            else:
                xx = x0 + i * stripe + stripe * 0.25
                c.drawLine(xx, y0 - 200, xx, y1 + 200, stroke((70, 56, 100), 1.5, 0.35))


# ------------------------------------------------------------------ props
def draw_lantern(c, x, y, r, t, lit=1.0, glow_amt=1.0, face=True):
    """Ribbed jack-o'-lantern sitting at (x, y) (base point)."""
    tf = math.floor(t * 4.0) / 4.0
    fl = 0.92 + 0.08 * noise1(tf * 3.0, 7)
    cy = y - r * 0.82
    if lit > 0 and glow_amt > 0:
        glow(c, x, cy, r * 4.2, (255, 140, 40), 0.36 * lit * fl * glow_amt)
    body = smooth_path([(x - r * 1.18, cy), (x - r * 0.9, cy - r * 0.78), (x, cy - r * 0.86), (x + r * 0.9, cy - r * 0.78),
                        (x + r * 1.18, cy), (x + r * 0.95, cy + r * 0.72), (x, cy + r * 0.84), (x - r * 0.95, cy + r * 0.72)])
    c.drawOval(skia.Rect.MakeLTRB(x - r * 1.2, y - r * 0.12, x + r * 1.2, y + r * 0.12),
               fill((0, 0, 0), 1.0, rad_grad((x, y), r * 1.2, [(0, 0, 0, 0.5), (0, 0, 0, 0)])))
    c.drawPath(body, fill(PUMPKIN, 1.0, rad_grad((x - r * 0.35, cy - r * 0.4), r * 1.9,
                                                 [(255, 170, 70), (238, 112, 20), (130, 44, 10)], [0, 0.5, 1])))
    for k in (-0.62, -0.25, 0.25, 0.62):  # ribs (stripes)
        p = skia.Path()
        p.moveTo(x + k * r * 0.5, cy - r * 0.82)
        p.quadTo(x + k * r * 1.7, cy, x + k * r * 0.55, cy + r * 0.82)
        c.drawPath(p, stroke((150, 54, 8), r * 0.035, 0.75))
    c.drawPath(body, stroke((90, 30, 6), r * 0.03))
    # spiral stem
    stem = poly([(x - r * 0.1, cy - r * 0.8), (x - r * 0.06, cy - r * 1.08), (x + r * 0.12, cy - r * 1.14),
                 (x + r * 0.1, cy - r * 0.8)])
    c.drawPath(stem, fill((70, 84, 46)))
    c.drawPath(open_path(spiral_pts(x + r * 0.32, cy - r * 1.06, 2, r * 0.22, 1.6, a0=math.pi, n=26)),
               stroke((70, 84, 46), r * 0.03))
    if face:
        inner = (255, int(200 + 40 * fl), int(90 + 60 * fl)) if lit > 0 else (40, 14, 6)
        ia = 1.0 if lit > 0 else 0.9
        eyes = [poly([(x - r * 0.62, cy - r * 0.05), (x - r * 0.38, cy - r * 0.46), (x - r * 0.14, cy - r * 0.05)]),
                poly([(x + r * 0.14, cy - r * 0.05), (x + r * 0.38, cy - r * 0.46), (x + r * 0.62, cy - r * 0.05)])]
        nose = poly([(x - r * 0.1, cy + r * 0.12), (x, cy - r * 0.04), (x + r * 0.1, cy + r * 0.12)])
        mouth = poly([(x - r * 0.72, cy + r * 0.22), (x - r * 0.5, cy + r * 0.3), (x - r * 0.42, cy + r * 0.22),
                      (x - r * 0.28, cy + r * 0.34), (x - r * 0.12, cy + r * 0.25), (x, cy + r * 0.36),
                      (x + r * 0.12, cy + r * 0.25), (x + r * 0.28, cy + r * 0.34), (x + r * 0.42, cy + r * 0.22),
                      (x + r * 0.5, cy + r * 0.3), (x + r * 0.72, cy + r * 0.22), (x + r * 0.5, cy + r * 0.62),
                      (x + r * 0.3, cy + r * 0.5), (x + r * 0.16, cy + r * 0.66), (x, cy + r * 0.52),
                      (x - r * 0.16, cy + r * 0.66), (x - r * 0.3, cy + r * 0.5), (x - r * 0.5, cy + r * 0.62)])
        for shape in eyes + [nose, mouth]:
            c.drawPath(shape, fill(inner, ia))
            if lit > 0:
                c.drawPath(shape, fill((255, 120, 30), 1.0, blur=r * 0.06, blend=skia.BlendMode.kScreen))
            c.drawPath(shape, stroke((100, 34, 6), r * 0.02))


def draw_table(c, rect, wood=WOOD, top_lean=0.0):
    x0, y0, x1, y1 = rect
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(wood, 1.0, lin_grad((0, y0), (0, y1), [(70, 44, 54), wood, (34, 20, 30)])))
    rr = rng("grain")
    for i in range(14):
        yy = lerp(y0, y1, (i + 0.5) / 14) + rr.uniform(-6, 6)
        p = skia.Path()
        p.moveTo(x0, yy)
        p.cubicTo(lerp(x0, x1, 0.3), yy + rr.uniform(-10, 10), lerp(x0, x1, 0.6), yy + rr.uniform(-10, 10), x1, yy)
        c.drawPath(p, stroke(WOOD_HI if i % 3 else (30, 18, 26), 2.2, 0.35))
    c.drawLine(x0, y0, x1, y0, stroke((96, 66, 76), 4, 0.8))


# ------------------------------------------------------------------ the drawing itself
PAPER_W, PAPER_H = 1000, 1330

# where each mouse lives on the page (paper coords) and its flat-pose base
PAGE_MICE = {
    "tilt": dict(x=290, y=230, scale=0.95, tilt=-22.0, facing=1),
    "biscuit": dict(x=470, y=215, scale=1.05, tilt=2.0, facing=1),
    "crumb": dict(x=670, y=330, scale=1.25, tilt=0.0, facing=1),
    "wedge": dict(x=470, y=640, scale=1.85, tilt=0.0, facing=1),
    "pip": dict(x=395, y=1110, scale=2.2, tilt=0.0, facing=1),
}


def draw_flower(c, x, y, s, seed=0, col=GRAPHITE, bloom=0.0):
    with Xf(c, x, y, sx=s):
        stem = open_path([(0, 10), (4, 60), (-2, 110)])
        pencil(c, stem, 3.0, col, 1.0, seed=seed)
        pencil(c, smooth_path([(2, 70), (24, 56), (34, 66), (14, 78)]), 2.5, col, 1.0, seed=seed + 1)
        for i in range(7):
            a = i / 7 * 2 * math.pi + bloom * 0.3
            px, py = math.cos(a) * (24 + bloom * 6), math.sin(a) * (24 + bloom * 6)
            pencil(c, ellipse(px, py, 14 + bloom * 3, 9 + bloom * 2), 2.2, col, 1.0, seed=seed + 3 + i, rough=0.8)
        pencil(c, circle(0, 0, 11), 2.4, col, 1.0, seed=seed + 20)


def draw_stick_girl(c, x, y, s, seed=0, col=GRAPHITE, wave=0.0):
    with Xf(c, x, y, sx=s):
        pencil(c, circle(0, -70, 22), 2.6, col, 1.0, seed=seed)
        c.drawCircle(-7, -74, 2.5, fill(col))
        c.drawCircle(7, -74, 2.5, fill(col))
        pencil(c, open_path([(-9, -62), (0, -56), (9, -62)]), 2.0, col, 1.0, seed=seed + 1)
        dress = poly([(0, -48), (-34, 34), (34, 34)])
        pencil(c, dress, 2.6, col, 1.0, seed=seed + 2)
        c.save()
        c.clipPath(dress, skia.ClipOp.kIntersect, True)
        hp = skia.Path()
        for i in range(-6, 8):
            hp.moveTo(i * 10, -50)
            hp.lineTo(i * 10 + 60, 40)
            hp.moveTo(i * 10, -50)
            hp.lineTo(i * 10 - 60, 40)
        pencil(c, hp, 1.5, col, 0.8, seed=seed + 3, rough=0.6, double=False)
        c.restore()
        wa = math.sin(wave * 8) * 20 * min(1, wave * 3)
        pencil(c, open_path([(-12, -30), (-40, -10 - (wa if wave else 0)), (-52, -24 - (wa if wave else 0))]), 2.2, col, 1.0,
               seed=seed + 4)
        pencil(c, open_path([(12, -30), (40, -6), (50, 4)]), 2.2, col, 1.0, seed=seed + 5)
        pencil(c, open_path([(-12, 34), (-14, 74)]), 2.2, col, 1.0, seed=seed + 6)
        pencil(c, open_path([(12, 34), (14, 74)]), 2.2, col, 1.0, seed=seed + 7)


def draw_page_pumpkin(c, x, y, r, seed=0, col=GRAPHITE, tint=0.0):
    body = ellipse(x, y, r, r * 0.95)
    if tint > 0:
        c.drawPath(body, fill((246, 150, 60), 0.35 * tint))
    pencil(c, body, 2.6, col, 1.0, seed=seed)
    for k in (-0.55, -0.15, 0.25, 0.6):
        p = skia.Path()
        p.moveTo(x + k * r * 0.6, y - r * 0.9)
        p.quadTo(x + k * r * 1.2, y, x + k * r * 0.6, y + r * 0.92)
        pencil(c, p, 2.0, col, 0.85, seed=seed + 1 + int(k * 10), double=False)
    pencil(c, poly([(x - 6, y - r * 0.92), (x - 5, y - r * 1.15), (x + 7, y - r * 1.15), (x + 6, y - r * 0.92)]),
           2.2, col, 1.0, seed=seed + 7)
    sp = spiral_pts(x + r * 0.45, y - r * 1.1, 2, r * 0.26, 1.8, a0=math.pi, n=30)
    pencil(c, open_path(sp), 1.8, col, 0.9, seed=seed + 8, double=False)


def draw_page(c, t, D=None, seed=0):
    """The child's drawing in paper coordinates (PAPER_W x PAPER_H).
    D: dict of per-element state: {'reveal': 0..1 write-on, '<mouse>': pose overrides, 'cat': bool}."""
    D = D or {}
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 0, PAPER_W, PAPER_H), skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(0, 0, PAPER_W, PAPER_H), fill(PAPER))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, PAPER_W, PAPER_H),
               fill((0, 0, 0), 1.0, rad_grad((PAPER_W * 0.45, PAPER_H * 0.4), PAPER_H * 0.9,
                                             [(0, 0, 0, 0.0), (60, 50, 40, 0.18)])))
    bs = D.get("boil", 0)
    v = D.get("r_flower", 1.0)
    if v > 0:
        with Xf(c, 0, 0, alpha=v):
            draw_flower(c, 105, 70, 0.95, seed=11 + bs, bloom=D.get("bloom", 0.0))
    v = D.get("r_girl", 1.0)
    if v > 0:
        with Xf(c, 0, 0, alpha=v):
            draw_stick_girl(c, 150, 330, 1.05, seed=21 + bs, wave=D.get("girl_wave", 0.0))
    mice_order = ["wedge", "biscuit", "tilt", "crumb", "pip"]
    rm = D.get("r_mice", 1.0)
    for i, name in enumerate(mice_order):
        v = clamp(rm * 5 - i)
        if v <= 0 or D.get("hide_" + name):
            continue
        base = dict(PAGE_MICE[name])
        over = D.get(name, {})
        base.update(over)
        p = mpose(flat=True, seed=31 + i * 13 + bs, ink=D.get("ink", 0.0), lid=D.get("lid", 0.0))
        p.update(base)
        with Xf(c, 0, 0, alpha=v):
            draw_mouse(c, name, p)
    rp = D.get("r_pumpkins", 1.0)
    for i, (px, py, pr) in enumerate(((160, 660, 115), (470, 470, 52), (330, 880, 56))):
        v = clamp(rp * 3 - i)
        if v > 0:
            with Xf(c, 0, 0, alpha=v):
                draw_page_pumpkin(c, px, py, pr, seed=61 + i * 10 + bs, tint=D.get("tint", 0.0))
    if D.get("cat"):
        draw_page_cat(c, 120, 230, 0.9, seed=91 + bs)
    # the words, last, pressed hard
    wv = D.get("r_words", 1.0)
    if wv > 0 and not D.get("hide_words"):
        draw_text(c, "TOO MOM I LOVE YOU", 165, 26, 54, style="pencil", seed=100 + bs, reveal=wv, weight=1.25)
        if wv >= 1:
            u = open_path([(318, 96), (370, 100), (432, 94)])
            pencil(c, u, 4.0, GRAPHITE, 1.0, seed=140 + bs)
    c.restore()


def draw_page_cat(c, x, y, s, seed=0):
    """The little black cat the mice add next to the flower."""
    with Xf(c, x, y, sx=s):
        body = smooth_path([(-20, 40), (-26, 0), (-14, -30), (14, -30), (26, 0), (24, 40)])
        c.drawPath(body, fill((30, 28, 36)))
        head = smooth_path([(-22, -30), (-26, -52), (-20, -76), (-10, -60), (10, -60), (20, -76), (26, -52), (22, -30)])
        c.drawPath(head, fill((30, 28, 36)))
        c.drawCircle(-9, -45, 4, fill((236, 220, 80)))
        c.drawCircle(9, -45, 4, fill((236, 220, 80)))
        sp = spiral_pts(48, -10, 2, 14, 1.4, a0=0, n=20)
        c.drawPath(open_path([(22, 34), (46, 20), (52, 0)] + sp[::-1]), stroke((30, 28, 36), 5))
        pencil(c, smooth_path([(-8, -88), (0, -96), (8, -88), (0, -80)]), 2.0, (200, 60, 90), 0.9, seed=seed)


def paper_matrix(quad):
    """Perspective matrix mapping paper rect -> quad [(x,y)*4] (tl, tr, br, bl)."""
    m = skia.Matrix()
    src = [skia.Point(0, 0), skia.Point(PAPER_W, 0), skia.Point(PAPER_W, PAPER_H), skia.Point(0, PAPER_H)]
    dst = [skia.Point(*q) for q in quad]
    m.setPolyToPoly(src, dst)
    return m


def draw_page_in_quad(c, quad, t, D=None, shade=0.0):
    c.drawPath(poly([(q[0] + 10, q[1] + 14) for q in quad]), fill((0, 0, 0), 0.4, blur=10))
    c.save()
    c.concat(paper_matrix(quad))
    draw_page(c, t, D)
    if shade > 0:
        c.drawRect(skia.Rect.MakeLTRB(0, 0, PAPER_W, PAPER_H), fill((20, 24, 60), shade))
    c.restore()


def vignette(c, a=0.55):
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H),
               fill((0, 0, 0), 1.0, rad_grad((W / 2, H * 0.46), H * 0.68,
                                             [(0, 0, 0, 0.0), (0, 0, 0, 0.0), (0, 0, 0, a)], [0.0, 0.55, 1.0])))


# ------------------------------------------------------------------ tabletop stage (mouse-eye view)
STAGE_GROUND = 1340          # paper's far edge (letters stand here)
STAGE_PAGE_QUAD = [(-520, 1335), (1640, 1335), (2900, 2500), (-1780, 2500)]
DOOR_X = 930


def draw_doorway(c, x, y_floor, w, h, light=0.0, t=0.0):
    """Arched doorway in the far wall; light=1 means the hallway lamp is on."""
    x0, x1 = x - w / 2, x + w / 2
    top = y_floor - h
    arch = skia.Path()
    arch.moveTo(x0, y_floor)
    arch.lineTo(x0, top + w * 0.45)
    arch.quadTo(x0, top, x, top - w * 0.12)
    arch.quadTo(x1, top, x1, top + w * 0.45)
    arch.lineTo(x1, y_floor)
    arch.close()
    c.drawPath(arch, fill((6, 5, 12)))
    if light > 0:
        c.drawPath(arch, fill((255, 196, 110), light, lin_grad((x, top), (x, y_floor),
                                                              [(255, 214, 140), (232, 160, 84)])))
        # crooked stair edges inside
        for i in range(6):
            yy = y_floor - i * h * 0.12
            c.drawLine(x0 + i * w * 0.06, yy, x1, yy - w * 0.08, stroke((150, 90, 50), 4, 0.6 * light))
    c.drawPath(arch, stroke(FRAME, 22))
    c.drawPath(open_path(spiral_pts(x, top - w * 0.2, 4, 26, 1.4, a0=0, n=24)), stroke(FRAME, 7))


def stage_far(c, t, S):
    """Far wall: drawn in frame coords, used with parallax ~0.3."""
    draw_wall(c, (-900, -800, W + 1400, STAGE_GROUND + 60))
    draw_window(c, (-60, 120, 640, 1180), t, moon_rel=(0.58, 0.5), moon_r=0.27, cobweb=True, sill=True,
                bats=S.get("bats", True))
    draw_doorway(c, DOOR_X, STAGE_GROUND + 40, 300, 760, S.get("door_light", 0.0), t)
    sh = S.get("wall_shadow")
    if sh is not None:
        sh(c)
    if S.get("door_light", 0.0) > 0:
        dl = S["door_light"]
        c.drawPath(poly([(DOOR_X - 150, STAGE_GROUND + 40), (DOOR_X + 150, STAGE_GROUND + 40), (DOOR_X - 280, STAGE_GROUND + 300),
                         (-200, STAGE_GROUND + 300)]), fill((255, 200, 120), 0.18 * dl, blend=skia.BlendMode.kScreen))
        glow(c, DOOR_X, STAGE_GROUND - 300, 900, (255, 190, 110), 0.22 * dl)


def stage_table(c, t, S):
    """Table top surface + far edge, parallax 1."""
    c.drawRect(skia.Rect.MakeLTRB(-3000, STAGE_GROUND - 6, 4000, 4000),
               fill(WOOD, 1.0, lin_grad((0, STAGE_GROUND), (0, 2600), [(46, 28, 40), (70, 44, 54), (40, 24, 32)])))
    rr = rng("stage_grain")
    for i in range(10):
        yy = STAGE_GROUND + 20 + (i ** 1.6) * 30
        c.drawLine(-3000, yy, 4000, yy + rr.uniform(-8, 8), stroke(WOOD_HI, 2.0, 0.25))
    c.drawLine(-3000, STAGE_GROUND - 4, 4000, STAGE_GROUND - 4, stroke((96, 66, 76), 5, 0.7))


def stage_page(c, t, S):
    D = dict(S.get("page", {}))
    q = STAGE_PAGE_QUAD
    c.save()
    c.concat(paper_matrix(q))
    draw_page(c, t, D)
    c.drawRect(skia.Rect.MakeLTRB(0, 0, PAPER_W, PAPER_H), fill((22, 26, 64), 0.52))
    c.restore()
    # moonlight pool and the lantern's warm pool on the page
    c.drawOval(skia.Rect.MakeLTRB(-100, 1360, 1300, 2300), fill((0, 0, 0), 1.0,
                                                               rad_grad((560, 1700), 760, [(150, 180, 220, 0.20), (150, 180, 220, 0.0)]),
                                                               blend=skia.BlendMode.kScreen))
    lit = S.get("lantern", 1.0)
    if lit > 0:
        c.drawOval(skia.Rect.MakeLTRB(-900, 1300, 900, 2400), fill((0, 0, 0), 1.0,
                                                                  rad_grad((-300, 1480), 1000, [(255, 140, 50, 0.34 * lit), (255, 120, 40, 0.0)]),
                                                                  blend=skia.BlendMode.kScreen))


def draw_popup_letters(c, t, up, x0=60, base=STAGE_GROUND + 16, h=170, seed=0, glow_amt=0.0, only=None):
    """'TOO MOM I LOVE YOU' standing up from the page's top edge. up: 0..1 per-letter stagger."""
    from letters import layout, glyph_path
    items, width = layout("TOO MOM I LOVE YOU")
    k = h / 140.0
    n = len(items)
    for i, (ch, lx, dy, rot, sc) in enumerate(items):
        u = clamp((up * 1.4) - i * 0.4 / n)
        if u <= 0:
            continue
        sy = 1.0 if u >= 1 else math.sin(u * math.pi * 0.5) * (1 + 0.15 * math.sin(u * math.pi * 3) * (1 - u))
        cx = x0 + (lx + 50 * sc) * k
        if only is not None and i not in only:
            continue
        # shadow on paper
        c.drawOval(skia.Rect.MakeLTRB(cx - 60 * k * sc, base - 10, cx + 60 * k * sc, base + 18),
                   fill((0, 0, 0), 0.35 * u, blur=6))
        with Xf(c, cx, base, sx=k * sc, sy=k * sc * sy):
            with Xf(c, 0, -70, rot=rot * 0.5):
                c.translate(-50, -70)
                gp = glyph_path(ch)
                if glow_amt > 0:
                    c.drawPath(gp, stroke((255, 210, 130), 90, 0.55 * glow_amt, blur=26, blend=skia.BlendMode.kScreen))
                    c.drawPath(gp, stroke((255, 236, 180), 44, 0.6 * glow_amt, blur=8, blend=skia.BlendMode.kScreen))
                c.drawPath(gp, stroke((10, 8, 16), 36, 0.55, blur=6))
                c.translate(4, 3)
                c.drawPath(gp, stroke((150, 146, 140), 30))  # paper thickness
                c.translate(-4, -3)
                c.drawPath(gp, stroke(GRAPHITE, 30, effect=wobble(10, 1.5, seed + i)))
                c.drawPath(gp, stroke(PAPER, 21, effect=wobble(10, 1.2, seed + i + 50)))
    return x0, x0 + width * k


def letter_x(i, x0=60, h=170):
    from letters import layout
    items, _ = layout("TOO MOM I LOVE YOU")
    k = h / 140.0
    ch, lx, dy, rot, sc = items[i]
    return x0 + (lx + 50 * sc) * k


# ------------------------------------------------------------------ grandfather clock
def draw_clock(c, x, y, s, t, hour_ang, min_ang, pend=0.0, shake=0.0):
    with Xf(c, x + shake * 6 * math.sin(t * 60), y, sx=s, rot=-3):
        case = poly([(-150, 0), (-170, -900), (-130, -1180), (-190, -1250), (0, -1420), (190, -1250), (130, -1180),
                     (170, -900), (150, 0)])
        c.drawPath(case, fill((44, 26, 36)))
        c.drawPath(case, stroke((90, 60, 72), 5))
        # pendulum window
        win = rounded_poly([(-90, -820), (90, -820), (80, -160), (-80, -160)], 30)
        c.drawPath(win, fill((14, 12, 26)))
        c.save()
        c.clipPath(win, skia.ClipOp.kIntersect, True)
        a = math.radians(18 * math.sin(pend))
        px, py = math.sin(a) * 520, -820 + math.cos(a) * 520
        c.drawLine(0, -820, px, py, stroke((200, 170, 90), 6))
        c.drawCircle(px, py, 46, fill((220, 186, 96), 1.0, rad_grad((px - 12, py - 12), 60,
                                                                    [(255, 236, 160), (200, 160, 70), (120, 90, 30)])))
        c.drawPath(win, fill((150, 190, 230), 0.08))
        c.restore()
        c.drawPath(win, stroke((90, 60, 72), 5))
        # face
        c.drawCircle(0, -1060, 150, fill((236, 226, 196), 1.0, rad_grad((-30, -1090), 190,
                                                                          [(250, 244, 222), (220, 206, 170)])))
        c.drawCircle(0, -1060, 150, stroke((30, 20, 26), 10))
        for i in range(12):
            r = math.radians(i * 30)
            c.drawLine(math.sin(r) * 118, -1060 - math.cos(r) * 118, math.sin(r) * 136, -1060 - math.cos(r) * 136,
                       stroke((30, 20, 26), 7 if i % 3 == 0 else 3))
        for ang, L, wdt in ((hour_ang, 78, 9), (min_ang, 112, 6)):
            r = math.radians(ang)
            ex, ey = math.sin(r) * L, -1060 - math.cos(r) * L
            c.drawLine(0, -1060, ex, ey, stroke((22, 14, 20), wdt))
            sp = spiral_pts(ex, ey, 1, 12, 1.2, a0=r, n=14)
            c.drawPath(open_path(sp), stroke((22, 14, 20), 3))
        c.drawCircle(0, -1060, 12, fill((22, 14, 20)))
        # crescent moon on the crown
        c.drawCircle(0, -1330, 46, fill((236, 230, 190)))
        c.drawCircle(18, -1342, 42, fill((44, 26, 36)))


# ------------------------------------------------------------------ staircase
def draw_stairs(c, t, lamp=1.0):
    draw_wall(c, (-200, -200, W + 200, H + 200), lean=-1.5)
    if lamp > 0:
        glow(c, 860, 260, 900, (255, 190, 110), 0.30 * lamp)
    # crooked steps rising to the upper right
    for i in range(12):
        x = -100 + i * 100
        y = 1900 - i * 120
        step = poly([(x, y), (x + 130, y - 8), (x + 130, y + 140), (x, y + 150)])
        c.drawPath(step, fill((48, 30, 40)))
        c.drawLine(x, y, x + 130, y - 8, stroke((96, 66, 76), 4, 0.8))
    # banister with spiral finials
    c.drawLine(-60, 1640, 1180, 160, stroke((30, 18, 26), 18))
    for i in range(12):
        x = -40 + i * 100
        y = 1620 - i * 120
        c.drawLine(x, y, x, y + 170, stroke((30, 18, 26), 8))
    c.drawPath(open_path(spiral_pts(-60, 1600, 2, 40, 1.6, a0=0, n=30)), stroke((30, 18, 26), 10))
    # wall lamp
    c.drawLine(860, 180, 860, 240, stroke((30, 20, 30), 6))
    c.drawPath(poly([(810, 240), (910, 240), (880, 320), (840, 320)]),
               fill((255, 210, 140) if lamp > 0 else (60, 50, 60)))


# ------------------------------------------------------------------ fridge
CRAYON_PURPLE = (150, 90, 210)


def draw_crayon_sun(c, x, y, s, t, face=None, seed=0):
    """Old drawing: a purple crayon sun with one big eye and one small."""
    face = face or {}
    with Xf(c, x, y, sx=s):
        c.drawRect(skia.Rect.MakeLTRB(-150, -150, 150, 150), fill((246, 240, 226)))
        c.drawRect(skia.Rect.MakeLTRB(-150, -150, 150, 150), fill((0, 0, 0), 1.0, lin_grad((-150, -150), (150, 150),
                                                                                              [(0, 0, 0, 0), (60, 40, 20, 0.12)])))
        col = CRAYON_PURPLE
        for i in range(12):
            a = i / 12 * 2 * math.pi + 0.15
            r0, r1 = 70, 118 + (i % 2) * 14
            p = open_path([(math.cos(a) * r0, math.sin(a) * r0), (math.cos(a + 0.08) * (r0 + r1) / 2, math.sin(a + 0.08) * (r0 + r1) / 2),
                           (math.cos(a) * r1, math.sin(a) * r1)])
            for j in range(2):
                c.drawPath(p, stroke(col, 9 - j * 3, 0.6, effect=wobble(5, 2.2, seed + i * 3 + j)))
        disk = circle(0, 0, 66)
        c.drawPath(disk, fill((200, 160, 240), 0.55))
        for j in range(3):
            c.drawPath(disk, stroke(col, 10 - j * 3, 0.65, effect=wobble(5, 2.5, seed + 40 + j)))
        # scribble fill
        sp = skia.Path()
        rr = rng("sun_scrib", seed)
        sp.moveTo(-50, -30)
        for k in range(14):
            sp.lineTo(rr.uniform(-55, 55), rr.uniform(-45, 50))
        c.save()
        c.clipPath(disk, skia.ClipOp.kIntersect, True)
        c.drawPath(sp, stroke(col, 5, 0.35, effect=wobble(4, 2, seed)))
        c.restore()
        lid = face.get("lid", 0.0)
        for ex, er in ((-24, 17), (26, 9)):
            c.drawCircle(ex, -12, er, fill((255, 255, 255)))
            c.drawCircle(ex + face.get("look", 0) * er * 0.4, -10, er * 0.5, fill((40, 20, 60)))
            if lid > 0:
                c.drawRect(skia.Rect.MakeLTRB(ex - er - 2, -12 - er - 2, ex + er + 2, -12 - er + lid * er * 2.1),
                           fill((200, 160, 240)))
            c.drawCircle(ex, -12, er, stroke(col, 3.5, 0.9))
        op = face.get("mouth", 0.0)
        sm = face.get("smile", 0.6)
        if op > 0.05:
            c.drawOval(skia.Rect.MakeLTRB(-22, 18, 22, 22 + 26 * op), fill((90, 30, 70)))
            c.drawOval(skia.Rect.MakeLTRB(-22, 18, 22, 22 + 26 * op), stroke(col, 4))
        else:
            p = skia.Path()
            p.moveTo(-28, 20)
            p.quadTo(0, 20 + 22 * sm, 28, 20)
            c.drawPath(p, stroke(col, 5))


def draw_ghost_drawing(c, x, y, s, t, face=None, seed=0):
    """Last Halloween's scribble ghost on grey paper, with BOO."""
    face = face or {}
    with Xf(c, x, y, sx=s):
        c.drawRect(skia.Rect.MakeLTRB(-130, -160, 130, 160), fill((52, 58, 72)))
        wob = face.get("wobble", 0.0)
        g = smooth_path([(-60, 90 + wob * 6), (-70, -20), (-40, -100), (0, -118), (40, -100), (70, -20), (62, 90),
                         (40, 70 - wob * 8), (20, 96), (0, 72 + wob * 8), (-20, 96), (-40, 70)])
        c.drawPath(g, fill((236, 238, 246), 0.92))
        for j in range(2):
            c.drawPath(g, stroke((255, 255, 255), 6 - j * 2, 0.6, effect=wobble(6, 2.4, seed + j)))
        op = face.get("mouth", 0.0)
        c.drawOval(skia.Rect.MakeLTRB(-34, -56, -10, -24), fill((30, 30, 44)))
        c.drawOval(skia.Rect.MakeLTRB(12, -56, 36, -24), fill((30, 30, 44)))
        c.drawOval(skia.Rect.MakeLTRB(-12, -4, 14, 10 + 30 * op), fill((30, 30, 44)))
        draw_text(c, "BOO", -70, 112, 34, style="crayon", seed=seed + 7, color=(240, 240, 250))


def draw_family_drawing(c, x, y, s, t, wave=0.0, seed=0):
    with Xf(c, x, y, sx=s):
        c.drawRect(skia.Rect.MakeLTRB(-170, -130, 170, 130), fill((250, 246, 230)))
        col_m, col_k = (220, 90, 120), (90, 150, 230)
        for (fx, h, col) in ((-60, 150, col_m), (40, 100, col_k)):
            with Xf(c, fx, 100):
                c.drawCircle(0, -h, 24, stroke(col, 5, effect=wobble(5, 1.6, seed)))
                c.drawLine(0, -h + 24, 0, -h * 0.35, stroke(col, 5))
                c.drawLine(0, -h * 0.35, -18, 0, stroke(col, 5))
                c.drawLine(0, -h * 0.35, 18, 0, stroke(col, 5))
        c.drawLine(-60, -70, 40, -40, stroke(col_m, 5, effect=wobble(5, 1.6, seed + 3)))  # holding hands
        wa = math.sin(wave * 9) * 0.5 if wave > 0 else 0.0
        c.drawLine(-60, -70, -110, -110 + wa * 40, stroke(col_m, 5))
        heart = smooth_path([(110, -40), (150, -86), (130, -110), (110, -90), (90, -110), (70, -86)])
        c.drawPath(heart, fill((240, 80, 100), 0.85))


def draw_magnet(c, x, y, kind="pumpkin"):
    if kind == "pumpkin":
        c.drawCircle(x, y, 26, fill((250, 130, 30)))
        c.drawCircle(x, y, 26, stroke((150, 60, 10), 3))
        c.drawLine(x, y - 26, x + 4, y - 36, stroke((70, 90, 40), 5))
    elif kind == "star":
        pts = []
        for i in range(10):
            r = 24 if i % 2 == 0 else 11
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
        c.drawPath(poly(pts), fill((240, 210, 90)))
    else:
        c.drawCircle(x, y, 20, fill((120, 200, 190)))


FRIDGE_RECT = (120, 140, 960, 1720)


def draw_fridge(c, t, moon=1.0, morning=0.0):
    x0, y0, x1, y1 = FRIDGE_RECT
    body = rounded_poly([(x0, y0 + 30), (x1, y0), (x1 + 10, y1), (x0 - 12, y1 + 6)], 90)
    base = (160, 196, 190) if morning <= 0 else (196, 222, 214)
    c.drawPath(body, fill(base, 1.0, lin_grad((x0, 0), (x1, 0), [(186, 216, 210), base, (92, 120, 126)])))
    c.drawLine(x0 + 10, 640, x1 - 6, 628, stroke((60, 80, 86), 6))
    c.drawPath(rounded_poly([(x1 - 90, 260), (x1 - 60, 258), (x1 - 56, 560), (x1 - 86, 562)], 14),
               fill((210, 214, 220)))
    c.drawPath(body, stroke((40, 50, 60), 8))
    if moon > 0:  # window-pane moonlight across the door
        c.save()
        c.clipPath(body, skia.ClipOp.kIntersect, True)
        for (px, py) in ((0, 0), (330, 20), (0, 440), (330, 460)):
            c.drawPath(poly([(x0 - 180 + px, y0 + 180 + py), (x0 + 110 + px, y0 + 150 + py), (x0 + 170 + px, y0 + 560 + py),
                             (x0 - 120 + px, y0 + 590 + py)]), fill((200, 230, 255), 0.13 * moon, blend=skia.BlendMode.kScreen))
        c.restore()
    c.drawRect(skia.Rect.MakeLTRB(-400, y1, W + 400, H + 400), fill((0, 0, 0)))
    for i in range(-4, 14):  # checkered floor in perspective
        for j in range(0, 6):
            xa = -200 + i * 140 + (j * 40)
            ya = y1 + j * 60
            if (i + j) % 2 == 0:
                c.drawPath(poly([(xa, ya), (xa + 140, ya), (xa + 180, ya + 60), (xa + 40, ya + 60)]),
                           fill((214, 206, 196) if morning else (46, 42, 64)))
            else:
                c.drawPath(poly([(xa, ya), (xa + 140, ya), (xa + 180, ya + 60), (xa + 40, ya + 60)]),
                           fill((40, 30, 40) if morning else (16, 14, 26)))


FRIDGE_SPOT = (540, 980)       # where our drawing hangs (centre)
FRIDGE_PAGE_W = 420            # display width of our drawing


def fridge_page_quad(cx=FRIDGE_SPOT[0], cy=FRIDGE_SPOT[1], w=FRIDGE_PAGE_W, rot=-2.0):
    h = w * PAPER_H / PAPER_W
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for (px, py) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    return pts


def draw_old_drawings(c, t, S):
    face_sun = S.get("sun", {})
    face_ghost = S.get("ghost", {})
    draw_crayon_sun(c, 280, 420, 0.95, t, face_sun, seed=3)
    draw_ghost_drawing(c, 790, 420, 0.95, t, face_ghost, seed=9)
    draw_family_drawing(c, 270, 1480, 0.85, t, wave=S.get("family_wave", 0.0), seed=13)
    with Xf(c, 820, 1470, rot=4):  # a rainbow
        c.drawRect(skia.Rect.MakeLTRB(-130, -110, 130, 110), fill((250, 246, 232)))
        for k, col in enumerate(((230, 70, 80), (240, 160, 60), (240, 220, 80), (90, 190, 110), (90, 140, 230))):
            p = skia.Path()
            p.addArc(skia.Rect.MakeLTRB(-100 + k * 14, -60 + k * 14, 100 - k * 14, 140 - k * 14), 180, 180)
            c.drawPath(p, stroke(col, 12, 0.85, effect=wobble(6, 1.8, k)))
    draw_magnet(c, 280, 280, "star")
    draw_magnet(c, 790, 268, "dot")
    draw_magnet(c, 270, 1360, "dot")
    draw_magnet(c, 820, 1370, "star")


# ------------------------------------------------------------------ exterior
def draw_house(c, x, y, s, t, window_light=1.0, sil=None):
    """Tall crooked house; sil(c, wx, wy) draws silhouettes in the lit window."""
    col = (14, 12, 24)
    with Xf(c, x, y, sx=s):
        body = poly([(-260, 0), (-280, -700), (-300, -760), (-20, -1180), (40, -1200), (290, -770), (262, -700),
                     (250, 0)])
        c.drawPath(body, fill(col))
        tower = poly([(60, -700), (50, -1180), (40, -1260), (140, -1560), (240, -1250), (210, -1180), (200, -700)])
        c.drawPath(tower, fill(col))
        c.drawPath(open_path(spiral_pts(140, -1600, 2, 30, 1.6, a0=0, n=24)), stroke(col, 9))
        for (wx, wy, ww, wh, lit) in ((-150, -520, 90, 150, 0.15), (120, -1000, 70, 120, 0.0), (-120, -200, 90, 150, 0.1)):
            r = rounded_poly([(wx - ww / 2, wy - wh / 2), (wx + ww / 2, wy - wh / 2 - 6), (wx + ww / 2, wy + wh / 2),
                              (wx - ww / 2, wy + wh / 2 + 4)], 10)
            c.drawPath(r, fill((255, 200, 110), 0.4 + lit) if lit > 0 else fill((30, 34, 60)))
        # the lit bedroom window
        wx, wy, ww, wh = 110, -500, 170, 230
        r = rounded_poly([(wx - ww / 2, wy - wh / 2), (wx + ww / 2, wy - wh / 2 - 10), (wx + ww / 2 + 6, wy + wh / 2),
                          (wx - ww / 2, wy + wh / 2 + 6)], 18)
        glow(c, wx, wy, 380, (255, 180, 90), 0.35 * window_light)
        c.drawPath(r, fill((255, 206, 120), window_light, lin_grad((0, wy - wh / 2), (0, wy + wh / 2),
                                                                   [(255, 222, 150), (240, 160, 80)])))
        if sil is not None:
            c.save()
            c.clipPath(r, skia.ClipOp.kIntersect, True)
            sil(c, wx, wy)
            c.restore()
        c.drawPath(r, stroke(col, 12))
        c.drawLine(wx, wy - wh / 2, wx + 3, wy + wh / 2, stroke(col, 8))
        # door, steps and lanterns
        c.drawPath(rounded_poly([(-40, 0), (-40, -170), (40, -176), (40, 0)], 30), fill((40, 26, 34)))
        for i, lx in enumerate((-150, 150)):
            draw_lantern(c, lx, 10, 36, t + i, lit=1.0, glow_amt=0.8)
