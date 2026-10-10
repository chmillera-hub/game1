"""Backgrounds, props and effects."""
import math

import skia

from anim import (H, W, C, clamp, glow, hashf, lerp, lin, mixc, noise, oval, paint, path, rad, shade,
                  smooth, spline)


# ------------------------------------------------------------------ sky & desert
def sky(cv, cols, pos=None, y0=0, y1=H, x0=-400, x1=W + 400):
    cv.drawRect(skia.Rect.MakeLTRB(x0, y0 - 600, x1, y1), paint(shader=lin((0, y0), (0, y1), cols, pos)))


def stars(cv, t, a, cx=360, cy=300, rot=0.0, n=260, area=1.0, seed=1, x0=-200, x1=W + 200, y0=-300, y1=900):
    if a <= 0:
        return
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    for i in range(n):
        x = lerp(x0 - cx, x1 - cx, hashf(seed, i, 1)) * area
        y = lerp(y0 - cy, y1 - cy, hashf(seed, i, 2)) * area
        appear = hashf(seed, i, 5)  # stars come out one by one
        vis = clamp((a - appear * 0.7) / 0.3)
        if vis <= 0:
            continue
        tw = 0.65 + 0.35 * math.sin(t * (1.5 + 3 * hashf(i, 3)) + i)
        r = 0.7 + 1.6 * hashf(seed, i, 4) ** 3
        c = mixc((255, 244, 220), (200, 215, 255), hashf(i, 6))
        cv.drawCircle(x, y, r, paint(c, vis * tw))
        if r > 1.6:
            glow(cv, x, y, r * 6, c, 0.25 * vis * tw)
    cv.restore()


def dune_layer(cv, base_y, amp, col, seed, x0=-300, x1=W + 300, light=None, rim=0.0, bottom=H + 600):
    pts = []
    n = 9
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        y = base_y - amp * (0.5 + 0.5 * math.sin(i * 1.7 + seed * 2.1)) * (0.6 + 0.8 * hashf(seed, i))
        pts.append((x, y))
    p = spline(pts, closed=False)
    p.lineTo(x1, bottom)
    p.lineTo(x0, bottom)
    p.close()
    cv.drawPath(p, paint(shader=lin((0, base_y - amp), (0, base_y + 300), [shade(col, 1.08), col, shade(col, 0.8)])))
    if rim > 0:
        top = spline(pts, closed=False)
        cv.drawPath(top, paint(light or shade(col, 1.3), rim, stroke=3, blur=1.5))
    return pts


def mountains(cv, base_y, col, seed=3, h=90):
    pts = [(-300, base_y + 50)]
    for i in range(14):
        x = lerp(-300, W + 300, i / 13)
        pts.append((x, base_y - h * (0.3 + 0.7 * hashf(seed, i))))
    pts.append((W + 300, base_y + 50))
    cv.drawPath(path(pts), paint(col))


def desert(cv, t, horizon=640, sun=(470, 600), warm=1.0, sun_r=46, dunes=True, night=0.0):
    top = mixc((26, 30, 70), (10, 12, 30), night)
    mid = mixc((122, 78, 116), (40, 36, 70), night)
    hor = mixc((250, 168, 96), (90, 70, 90), night)
    sky(cv, [top, mid, hor, shade(hor, 1.15)], [0, 0.45, 0.88, 1], 0, horizon + 20)
    if night > 0:
        stars(cv, t, night, n=180)
    sx, sy = sun
    glow(cv, sx, sy, 380, (255, 190, 110), 0.5 * warm)
    glow(cv, sx, sy, 140, (255, 220, 160), 0.6 * warm)
    cv.drawCircle(sx, sy, sun_r, paint((255, 236, 196), warm))
    mountains(cv, horizon - 5, mixc((150, 96, 118), (60, 50, 80), night), seed=3, h=70)
    mountains(cv, horizon + 10, mixc((176, 112, 112), (70, 56, 80), night), seed=7, h=40)
    # horizon haze
    cv.drawRect(skia.Rect.MakeLTRB(-400, horizon - 60, W + 400, horizon + 40),
                paint(shader=lin((0, horizon - 60), (0, horizon + 40), [((255, 190, 130), 0.0),
                                                                         ((255, 190, 130), 0.35 * warm),
                                                                         ((255, 190, 130), 0.0)])))
    if not dunes:
        return
    d = lambda c: mixc(c, (60, 50, 70), night * 0.7)
    dune_layer(cv, horizon + 40, 30, d((200, 132, 100)), 1, rim=0.5 * warm, light=(255, 200, 150))
    dune_layer(cv, horizon + 150, 60, d((216, 148, 98)), 2, rim=0.6 * warm, light=(255, 210, 160))
    dune_layer(cv, horizon + 300, 70, d((226, 162, 104)), 4, rim=0.7 * warm, light=(255, 220, 170))


def dust(cv, t, n=40, a=0.35, wind=40, seed=2, col=(240, 210, 170), x0=-50, x1=W + 50, y0=0, y1=H, size=1.0):
    for i in range(n):
        sp = (0.5 + hashf(seed, i, 1)) * wind
        x = (lerp(x0, x1, hashf(seed, i, 2)) + sp * t) % (x1 - x0 + 100) + x0 - 50
        y = lerp(y0, y1, hashf(seed, i, 3)) + 12 * math.sin(t * 1.3 + i)
        r = (1 + 2.5 * hashf(seed, i, 4)) * size
        cv.drawCircle(x, y, r, paint(col, a * (0.4 + 0.6 * hashf(i, 9)), blur=r * 0.6))


def cracked_ground(cv, rect, col, seed=5, cell=70, line_a=0.5, persp=None):
    l, tp, r, b = rect
    cv.drawRect(skia.Rect.MakeLTRB(l, tp, r, b), paint(col))
    dark = shade(col, 0.62)
    cols = int((r - l) / cell) + 2
    rows = int((b - tp) / (cell * 0.6)) + 2
    pts = {}
    for i in range(cols + 1):
        for j in range(rows + 1):
            pts[i, j] = (l + i * cell + (hashf(seed, i, j) - 0.5) * cell * 0.7,
                         tp + j * cell * 0.6 + (hashf(seed, j, i, 3) - 0.5) * cell * 0.4)
    pa = paint(dark, line_a, stroke=2.2)
    for i in range(cols):
        for j in range(rows):
            if hashf(seed, i, j, 7) < 0.8:
                cv.drawLine(*pts[i, j], *pts[i + 1, j], pa)
            if hashf(seed, i, j, 8) < 0.8:
                cv.drawLine(*pts[i, j], *pts[i, j + 1], pa)
    for k in range(40):
        x, y = lerp(l, r, hashf(seed, k, 21)), lerp(tp, b, hashf(seed, k, 22))
        cv.drawOval(oval(x, y, 3 + 5 * hashf(k, 1), 2 + 3 * hashf(k, 2)), paint(shade(col, 0.8), 0.7))


# ------------------------------------------------------------------ the village
HOUSE_TOP = (214, 206, 190)
HOUSE_FRONT = (176, 166, 150)
GROUND_IN = (196, 188, 172)
SAND = (214, 170, 122)


def village_aerial(cv, t, glow_seed=0.0, night=0.0, lights=0.0):
    """Oblique map-like view of the walled village, centred at (0, 0) world."""
    k = 0.55
    dim = lambda c: mixc(c, (22, 26, 52), night * 0.82)
    cv.drawRect(skia.Rect.MakeLTRB(-1400, -1400, 1400, 1400), paint(dim(SAND)))
    for i in range(30):  # sand ripples
        y = -1300 + i * 90
        cv.drawPath(spline([(-1400, y), (-700, y + 20), (0, y - 10), (700, y + 25), (1400, y)], closed=False),
                    paint(dim(shade(SAND, 0.9)), 0.5, stroke=3))
    X0, X1, Z0, Z1 = -300, 300, -420, 420
    # village floor
    cv.drawRect(skia.Rect.MakeLTRB(X0, Z0 * k, X1, Z1 * k), paint(dim(GROUND_IN)))
    for x in range(X0, X1 + 1, 30):
        cv.drawLine(x, Z0 * k, x, Z1 * k, paint(dim(shade(GROUND_IN, 0.9)), 0.6, stroke=1))
    for z in range(Z0, Z1 + 1, 30):
        cv.drawLine(X0, z * k, X1, z * k, paint(dim(shade(GROUND_IN, 0.9)), 0.6, stroke=1))
    # houses, back to front
    houses = []
    for zi, z in enumerate(range(-370, 371, 92)):
        for xi, x in enumerate(range(-255, 256, 85)):
            if abs(x) < 120 and abs(z) < 120:
                continue
            houses.append((z, x))
    houses.sort()
    hh = 34
    for z, x in houses:
        w, d = 58, 52
        top_y = z * k - d * k / 2 - hh
        # shadow
        cv.drawPath(path([(x + w / 2, z * k - d * k / 2), (x + w / 2 + 22, z * k - d * k / 2 + 8),
                          (x + w / 2 + 22, z * k + d * k / 2 + 8), (x + w / 2, z * k + d * k / 2)]),
                    paint((0, 0, 0), 0.18 * (1 - night * 0.5)))
        cv.drawRect(skia.Rect.MakeXYWH(x - w / 2, top_y, w, d * k), paint(dim(HOUSE_TOP)))
        cv.drawRect(skia.Rect.MakeXYWH(x - w / 2, top_y + d * k, w, hh), paint(dim(HOUSE_FRONT)))
        cv.drawRect(skia.Rect.MakeXYWH(x - 6, top_y + d * k + hh - 18, 12, 18), paint(dim((70, 62, 56))))
        lit = lights * (hashf(x, z) > 0.55)
        wc = mixc(dim((90, 80, 74)), (255, 200, 120), lit)
        cv.drawRect(skia.Rect.MakeXYWH(x - w / 2 + 8, top_y + d * k + 8, 8, 8), paint(wc))
        cv.drawRect(skia.Rect.MakeXYWH(x + w / 2 - 16, top_y + d * k + 8, 8, 8), paint(wc))
    # plaza dais + crowd dots
    cv.drawRect(skia.Rect.MakeXYWH(-26, -14 - 14, 52, 28 * k + 4), paint(dim((170, 160, 146))))
    cv.drawRect(skia.Rect.MakeXYWH(-26, -14 - 14 + 28 * k + 4, 52, 12), paint(dim((140, 130, 118))))
    if night < 0.5:
        for i in range(22):
            a = hashf(i, 31) * math.pi + math.pi * 0.05
            rr = 46 + 26 * hashf(i, 32)
            px, pz = math.cos(a) * rr, math.sin(a) * rr * 0.7 + 18
            cv.drawCircle(px, pz * k * 2 - 6, 5, paint(dim(HOUSE_FRONT)))
            cv.drawCircle(px, pz * k * 2 - 11, 3.5, paint(dim((150, 120, 96))))
        cv.drawCircle(0, -26, 4, paint((60, 58, 84)))
        cv.drawCircle(0, -32, 3.5, paint((180, 150, 120)))
    # walls: back, sides, front with gate
    wh = 46
    wc_top, wc_front = dim((190, 178, 156)), dim((150, 138, 118))
    cv.drawRect(skia.Rect.MakeLTRB(X0 - 16, Z0 * k - 16 - wh, X1 + 16, Z0 * k - wh), paint(wc_top))
    cv.drawRect(skia.Rect.MakeLTRB(X0 - 16, Z0 * k - wh, X1 + 16, Z0 * k), paint(wc_front))
    for xs in (X0 - 16, X1):
        cv.drawRect(skia.Rect.MakeLTRB(xs, Z0 * k - 16 - wh, xs + 16, Z1 * k - wh), paint(wc_top))
    cv.drawRect(skia.Rect.MakeLTRB(X0 - 16, Z1 * k - wh, X1 + 16, Z1 * k - wh + 16), paint(wc_top))
    cv.drawRect(skia.Rect.MakeLTRB(X0 - 16, Z1 * k - wh + 16, X1 + 16, Z1 * k + 16), paint(wc_front))
    for i in range(int((X1 - X0) / 24) + 2):  # block lines on the front wall
        x = X0 - 16 + i * 24
        cv.drawLine(x, Z1 * k - wh + 16, x, Z1 * k + 16, paint(dim(shade(wc_front, 0.85)), 0.6, stroke=1))
    cv.drawRect(skia.Rect.MakeLTRB(-22, Z1 * k - 18, 22, Z1 * k + 16), paint(dim((92, 66, 44))))
    cv.drawLine(0, Z1 * k - 18, 0, Z1 * k + 16, paint(dim((60, 40, 28)), stroke=2))
    for (cx, cz) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        cv.drawRect(skia.Rect.MakeXYWH(cx - 26, cz * k - wh - 34, 52, 26), paint(dim(shade(wc_top, 1.05))))
        cv.drawRect(skia.Rect.MakeXYWH(cx - 26, cz * k - wh - 8, 52, wh + 26), paint(dim(shade(wc_front, 0.95))))
    if glow_seed > 0:
        glow(cv, 0, 4, 60 + 140 * glow_seed, (255, 214, 140), 0.85 * glow_seed)
        glow(cv, 0, 4, 18 + 20 * glow_seed, (255, 245, 210), glow_seed)


def aerial_view(cv, t, zoom=1.0, focus=(0, 0), night=0.0, lights=0.0, glow_seed=0.0, horizon=330):
    """The village seen from a high hill, in true perspective, with sky and horizon."""
    top = mixc((120, 150, 190), (8, 10, 30), night)
    hor = mixc((238, 214, 180), (50, 46, 80), night)
    sky(cv, [top, hor], None, 0, horizon + 10)
    if night:
        stars(cv, t, night, n=160, y1=horizon)
    mountains(cv, horizon + 4, mixc((176, 150, 140), (40, 40, 66), night), seed=11, h=36)
    fx, fy = focus
    # map the flat village plane into a receding trapezoid
    src = [skia.Point(-900, -700), skia.Point(900, -700), skia.Point(900, 800), skia.Point(-900, 800)]
    w_far, w_near, y_far, y_near = 520, 1700, horizon + 14, 1700
    dst = [skia.Point(360 - w_far, y_far), skia.Point(360 + w_far, y_far), skia.Point(360 + w_near, y_near),
           skia.Point(360 - w_near, y_near)]
    m = skia.Matrix()
    m.setPolyToPoly(src, dst)
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(-400, horizon + 6, W + 400, H + 400))
    # zoom toward the focus point on screen
    fp = m.mapXY(fx, fy)
    cv.translate(fp.x(), fp.y())
    cv.scale(zoom, zoom)
    cv.translate(-fp.x(), -fp.y())
    cv.concat(m)
    village_aerial(cv, t, glow_seed=glow_seed, night=night, lights=lights)
    cv.restore()
    # atmospheric haze toward the horizon
    cv.drawRect(skia.Rect.MakeLTRB(-400, horizon, W + 400, horizon + 260), paint(
        shader=lin((0, horizon), (0, horizon + 260), [(hor, 0.75), (hor, 0.0)])))


def house_row(cv, y_base, height, n=6, x0=-80, x1=W + 80, dim=0.0, seed=1, col=HOUSE_FRONT, lights=0.0):
    w = (x1 - x0) / n
    for i in range(n):
        x = x0 + i * w
        c = mixc(col, (36, 40, 66), dim)
        cv.drawRect(skia.Rect.MakeLTRB(x + 4, y_base - height, x + w - 4, y_base), paint(c))
        cv.drawRect(skia.Rect.MakeLTRB(x, y_base - height - 10, x + w, y_base - height + 4), paint(shade(c, 1.12)))
        cv.drawRect(skia.Rect.MakeLTRB(x + 4, y_base - height + 4, x + w - 4, y_base - height + 10),
                    paint(shade(c, 0.8), 0.6))
        dw = w * 0.2
        cv.drawRect(skia.Rect.MakeLTRB(x + w / 2 - dw / 2, y_base - height * 0.55, x + w / 2 + dw / 2, y_base),
                    paint(mixc((78, 66, 58), (20, 20, 36), dim)))
        for s in (-1, 1):
            wx = x + w / 2 + s * w * 0.3
            lit = lights * (hashf(seed, i, s) > 0.4)
            cv.drawRect(skia.Rect.MakeLTRB(wx - w * 0.06, y_base - height * 0.78, wx + w * 0.06, y_base - height * 0.62),
                        paint(mixc(mixc((86, 74, 66), (20, 20, 36), dim), (255, 196, 120), lit)))
            if lit:
                glow(cv, wx, y_base - height * 0.7, w * 0.3, (255, 180, 100), 0.35 * lit)


def paving(cv, vp, y0, y1, col, dim=0.0, spacing=90):
    """Perspective grid of paving stones: ground from y0 down; vp = vanishing point (horizon)."""
    c = mixc(col, (36, 40, 66), dim)
    cv.drawRect(skia.Rect.MakeLTRB(-400, y0, W + 400, H + 600),
                paint(shader=lin((0, y0), (0, y1), [shade(c, 0.88), c, shade(c, 1.04)])))
    vx, vy = vp
    lc = shade(c, 0.74)
    yb = H + 600
    for i in range(-40, 41):
        xb = vx + i * spacing
        xa = vx + (xb - vx) * (y0 - vy) / (y1 - vy)
        xe = vx + (xb - vx) * (yb - vy) / (y1 - vy)
        cv.drawLine(xa, y0, xe, yb, paint(lc, 0.75, stroke=1.8))
    for k in range(-8, 80):
        z = 1 + k * spacing / (y1 - vy) * 1.1
        if z <= 0.05:
            continue
        y = vy + (y1 - vy) / z
        if y < y0 or y > yb:
            continue
        cv.drawLine(-400, y, W + 400, y, paint(lc, 0.75, stroke=1.0 + 1.2 / z))


def dais(cv, x, y, w, h, crack=0.0, dim=0.0, top=26):
    c = mixc((176, 166, 150), (40, 44, 70), dim)
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y - top, x + w / 2, y), paint(shade(c, 1.12)))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y, x + w / 2, y + h), paint(shade(c, 0.9)))
    for i in range(1, 5):
        cv.drawLine(x - w / 2 + i * w / 5, y, x - w / 2 + i * w / 5, y + h, paint(shade(c, 0.7), 0.5, stroke=2))
    cv.drawLine(x - w / 2, y + h / 2, x + w / 2, y + h / 2, paint(shade(c, 0.7), 0.5, stroke=2))
    if crack > 0:
        pts = [(x - w * 0.3, y - top + 4)]
        for i in range(1, 11):
            pts.append((x - w * 0.3 + i * w * 0.07 + (hashf(i, 41) - 0.5) * 24, y - top + 4 + (top + h) * i / 10))
        n = int(clamp(crack) * 10)
        for a, b in zip(pts[:n], pts[1:n + 1]):
            cv.drawLine(*a, *b, paint((30, 26, 24), 0.95, stroke=4.5))
            cv.drawLine(a[0] + 2, a[1], b[0] + 2, b[1], paint((235, 228, 214), 0.5, stroke=1.5))
        for i in (3, 6):  # branches
            if n > i:
                bx, by = pts[i]
                cv.drawLine(bx, by, bx + 30 * (1 if i == 3 else -1), by + 14, paint((30, 26, 24), 0.9, stroke=3))


def gate_inside(cv, t, light=1.0, dim=0.0):
    """Looking out through the open gate from inside the village."""
    sky(cv, [(206, 200, 188), (190, 184, 172)], None, 0, 700)
    cw = mixc((168, 156, 136), (40, 44, 70), dim)
    cv.drawRect(skia.Rect.MakeLTRB(-200, 0, W + 200, 900), paint(cw))
    for j in range(0, 900, 48):
        off = 40 if (j // 48) % 2 else 0
        cv.drawLine(-200, j, W + 200, j, paint(shade(cw, 0.85), 0.7, stroke=2))
        for x in range(-200 + off, W + 200, 80):
            cv.drawLine(x, j, x, j + 48, paint(shade(cw, 0.85), 0.7, stroke=2))
    # opening
    gx0, gx1, gy0, gy1 = 150, 570, 130, 900
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(gx0, gy0, gx1, gy1))
    desert(cv, t, horizon=560, sun=(360, 470), warm=light, sun_r=40)
    cv.restore()
    cv.drawRect(skia.Rect.MakeLTRB(gx0 - 26, gy0 - 26, gx1 + 26, gy0), paint(shade(cw, 0.75)))
    for s, xx in ((-1, gx0), (1, gx1)):
        cv.drawRect(skia.Rect.MakeLTRB(xx - 26 if s < 0 else xx, gy0, xx if s < 0 else xx + 26, gy1),
                    paint(shade(cw, 0.75)))
    # open doors (seen edge-on)
    for s, xx in ((-1, gx0 - 26), (1, gx1 + 26)):
        d = path([(xx, gy0 - 10), (xx + s * 70, gy0 + 20), (xx + s * 70, gy1 + 10), (xx, gy1)])
        cv.drawPath(d, paint(mixc((112, 80, 52), (30, 26, 40), dim)))
        for k in range(1, 4):
            cv.drawLine(xx + s * 70 * k / 4, gy0 - 10 + 30 * k / 4, xx + s * 70 * k / 4, gy1,
                        paint((70, 48, 30), 0.6, stroke=2))
    paving(cv, (360, 600), 900, 1200, GROUND_IN, dim=dim)
    # light spill onto the paving
    glow(cv, 360, 900, 420, (255, 200, 140), 0.35 * light, blend="screen")


def wall_outside(cv, t, gate=0.0, night=0.0, horizon=820, ground_col=(176, 128, 88), star_rot=0.0):
    """The village wall from the desert side. gate: 0 closed .. 1 open."""
    top = mixc((120, 140, 170), (8, 10, 28), night)
    mid = mixc((236, 170, 120), (30, 30, 66), night)
    hor = mixc((250, 196, 140), (70, 56, 86), night)
    sky(cv, [top, mid, hor], [0, 0.6, 1], 0, horizon - 200)
    if night > 0.3:
        stars(cv, t, clamp((night - 0.3) / 0.5), n=220, y0=-900, y1=300, x0=-500, x1=W + 500, rot=star_rot,
              cx=360, cy=-200)
    cw = mixc((170, 150, 122), (52, 50, 72), night)
    wall_top = 330
    cv.drawRect(skia.Rect.MakeLTRB(-400, wall_top, W + 400, horizon), paint(shade(cw, 0.95)))
    for i, x in enumerate(range(-400, W + 400, 60)):  # crenellations
        if i % 2 == 0:
            cv.drawRect(skia.Rect.MakeLTRB(x, wall_top - 36, x + 60, wall_top), paint(shade(cw, 0.95)))
    for j in range(wall_top, horizon, 44):
        off = 40 if ((j - wall_top) // 44) % 2 else 0
        cv.drawLine(-400, j, W + 400, j, paint(shade(cw, 0.8), 0.7, stroke=2))
        for x in range(-400 + off, W + 400, 80):
            cv.drawLine(x, j, x, min(horizon, j + 44), paint(shade(cw, 0.8), 0.7, stroke=2))
    cv.drawRect(skia.Rect.MakeLTRB(-400, wall_top - 36, W + 400, horizon), paint(
        shader=lin((0, wall_top), (0, horizon), [((0, 0, 0), 0.0), ((0, 0, 0), 0.25)])))
    # gate
    gx0, gx1, gy0 = 220, 500, 470
    cv.drawRect(skia.Rect.MakeLTRB(gx0 - 22, gy0 - 22, gx1 + 22, horizon), paint(shade(cw, 0.7)))
    inner = mixc((210, 200, 180), (40, 40, 64), night)
    cv.drawRect(skia.Rect.MakeLTRB(gx0, gy0, gx1, horizon), paint(inner))
    wood = mixc((118, 82, 52), (36, 30, 40), night)
    half = (gx1 - gx0) / 2
    for s, hinge in ((-1, gx0), (1, gx1)):
        wd = half * (1 - 0.82 * gate)
        x_in = hinge - s * wd
        d = path([(hinge, gy0), (x_in, gy0 + 8 * gate), (x_in, horizon - 4 * gate), (hinge, horizon)])
        cv.drawPath(d, paint(wood))
        for k in range(1, 4):
            xx = lerp(hinge, x_in, k / 4)
            cv.drawLine(xx, gy0 + 4, xx, horizon, paint(shade(wood, 0.7), 0.7, stroke=2))
        for yy in (gy0 + 80, horizon - 90):
            cv.drawLine(hinge, yy, x_in, yy, paint(shade(wood, 0.55), stroke=8))
    # ground
    cracked_ground(cv, (-400, horizon, W + 400, H + 400), mixc(ground_col, (50, 46, 66), night), seed=9)
    cv.drawRect(skia.Rect.MakeLTRB(-400, horizon, W + 400, horizon + 120), paint(
        shader=lin((0, horizon), (0, horizon + 120), [((0, 0, 0), 0.25), ((0, 0, 0), 0.0)])))


# ------------------------------------------------------------------ props & effects
def burning_bush(cv, x, y, s, t, a=1.0):
    """The bush that burned and was not consumed: a remembered vision."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cv.translate(x, y)
    cv.scale(s, s)
    glow(cv, 0, -60, 300, (255, 140, 40), 0.45)
    # the bush: a dome of leafy clumps
    for i in range(16):
        ang = math.pi + (i / 15) * math.pi
        r = 70 + 18 * hashf(i, 7)
        bx, by = math.cos(ang) * r * 1.1, math.sin(ang) * r * 0.8 - 10
        cv.drawCircle(bx * 0.8, by * 0.9, 34 + 10 * hashf(i, 8), paint((54, 58, 30)))
    for i in range(10):
        bx = (hashf(i, 9) - 0.5) * 120
        by = -30 - hashf(i, 10) * 40
        cv.drawCircle(bx, by, 30, paint((70, 76, 38)))
    for k in (-1, 1):
        cv.drawLine(0, 20, k * 30, -30, paint((60, 38, 24), stroke=9))
    cv.drawLine(0, 30, 0, -10, paint((60, 38, 24), stroke=11))
    # tongues of flame licking around it, never consuming it
    for i in range(34):
        ang = math.pi * (1.05 + 0.9 * hashf(i, 1))
        r = 60 + 40 * hashf(i, 2)
        fx, fy = math.cos(ang) * r, math.sin(ang) * r * 0.85 - 20
        h = 34 + 46 * hashf(i, 3)
        fl = 1 + 0.35 * math.sin(t * (6 + 6 * hashf(i, 4)) + i * 1.7)
        sway = 7 * math.sin(t * 4 + i)
        w = 10 + 6 * hashf(i, 6)
        f = skia.Path()
        f.moveTo(fx - w, fy)
        f.cubicTo(fx - w * 1.2, fy - h * 0.5 * fl, fx + sway - 3, fy - h * 0.7 * fl, fx + sway, fy - h * fl)
        f.cubicTo(fx + sway + 3, fy - h * 0.7 * fl, fx + w * 1.2, fy - h * 0.5 * fl, fx + w, fy)
        f.quadTo(fx, fy + w * 0.8, fx - w, fy)
        f.close()
        c = mixc((255, 110, 20), (255, 210, 90), hashf(i, 5))
        cv.drawPath(f, paint(c, 0.8, blend="plus"))
    glow(cv, 0, -40, 120, (255, 220, 150), 0.55)
    cv.restore()


def vessel(cv, x, y, s, t, crack=1.0, light=0.0, a=1.0, ghost=True):
    """A clay jar with cracks; light pours out through the cracks."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cv.translate(x, y)
    cv.scale(s, s)
    body = skia.Path()
    body.moveTo(-28, -120)
    body.lineTo(28, -120)
    body.quadTo(30, -96, 52, -80)
    body.cubicTo(100, -50, 96, 40, 50, 70)
    body.quadTo(0, 92, -50, 70)
    body.cubicTo(-96, 40, -100, -50, -52, -80)
    body.quadTo(-30, -96, -28, -120)
    body.close()
    clay = (176, 98, 60)
    if light > 0:
        glow(cv, 0, -10, 260 * (0.6 + light), (255, 200, 110), 0.5 * light)
    cv.drawPath(body, paint(shader=rad((-30, -40), 150, [shade(clay, 1.25), clay, shade(clay, 0.6)], [0, 0.5, 1])))
    cv.drawRect(skia.Rect.MakeLTRB(-34, -128, 34, -116), paint(shade(clay, 0.85)))
    cv.drawOval(oval(0, -126, 32, 7), paint((60, 30, 20)))
    for k in range(3):  # bands
        cv.drawPath(spline([(-80, -30 + k * 26), (0, -20 + k * 26), (80, -30 + k * 26)], closed=False),
                    paint(shade(clay, 0.7), 0.5, stroke=2.5))
    cracks = [[(-10, -100), (-18, -70), (-6, -40), (-22, -10), (-12, 20)],
              [(-12, 20), (-40, 40), (-52, 60)], [(-6, -40), (20, -24), (44, -30), (70, -10)],
              [(-22, -10), (-60, -6), (-80, 10)], [(20, -24), (26, 10), (14, 50), (24, 76)]]
    for ci, cr in enumerate(cracks):
        n = int(clamp(crack * 1.3 - ci * 0.12) * (len(cr) - 1) + 0.999)
        pts = cr[:n + 1]
        if len(pts) < 2:
            continue
        p = path(pts, closed=False)
        cv.drawPath(p, paint((40, 20, 14), stroke=4))
        if light > 0:
            cv.drawPath(p, paint((255, 240, 190), light, stroke=4.5, blend="plus"))
            cv.drawPath(p, paint((255, 200, 110), 0.8 * light, stroke=14, blur=6, blend="plus"))
            # beams
            for (px, py) in pts[1:]:
                ang = math.atan2(py + 10, px) + 0.15 * math.sin(t + px)
                L = 220 * light
                beam = path([(px, py), (px + math.cos(ang - 0.08) * L, py + math.sin(ang - 0.08) * L),
                             (px + math.cos(ang + 0.08) * L, py + math.sin(ang + 0.08) * L)])
                cv.drawPath(beam, paint(shader=rad((px, py), L, [((255, 230, 160), 0.55 * light),
                                                                 ((255, 200, 120), 0.0)]), blend="plus"))
    cv.restore()


def ghost(cv, x, y, t, a=1.0, s=1.0):
    """The familiar ghost of fear: smoke circling, with hollow eyes."""
    if a <= 0:
        return
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for i in range(16):
        ph = t * 1.1 + i * 0.4
        r = 120 + 40 * math.sin(ph * 0.7 + i)
        px = math.cos(ph) * r
        py = math.sin(ph) * r * 0.45 - 20 + i * 4
        cv.drawCircle(px, py, 46 + 20 * math.sin(ph * 1.3), paint((20, 18, 30), 0.3 * a, blur=22))
    ex, ey = math.cos(t * 1.1 + 0.6) * 140, math.sin(t * 1.1 + 0.6) * 50 - 40
    cv.drawOval(oval(ex, ey, 60, 70), paint((14, 12, 22), 0.5 * a, blur=26))
    for s2 in (-1, 1):
        cv.drawOval(oval(ex + s2 * 20, ey - 10, 8, 12), paint((210, 220, 240), 0.55 * a, blur=2))
    cv.restore()


def star_figure(cv, x, y, s, t, a=1.0, sigh=0.0, st=None):
    """The universe kneeling beside him: a luminous kneeling silhouette full of stars."""
    if a <= 0:
        return
    from rig import draw_person, mk
    br = 1 + 0.3 * sigh
    pose = mk(kneel=1.0, bow=0.25 - 0.1 * sigh, sigh=sigh, shadow=0, lid=1.0, arm_l=(14, -26, 1, 1),
              arm_r=(14, -26, 1, 1))
    glow(cv, x, y - 250 * s, 380 * s * br, (120, 140, 255), 0.22 * a)

    def silhouette(col, alpha, blur=0.0):
        lp = skia.Paint()
        if blur:
            lp.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        lp.setAlphaf(alpha)
        cv.saveLayer(None, lp)
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)
        draw_person(cv, st, pose, t)
        cv.restore()
        cv.drawPaint(paint(col, blend="srcin_fix"))
        cv.restore()

    silhouette((150, 170, 255), 0.55 * a * br, blur=26 * s)
    silhouette((40, 52, 120), 0.62 * a)
    silhouette((120, 150, 255), 0.18 * a, blur=4)
    # stars inside the body
    pts = []
    for i in range(46):
        u, v = hashf(i, 71), hashf(i, 72)
        if i < 8:   # head
            ang = u * 2 * math.pi
            px, py = math.cos(ang) * 40 * v, -305 + math.sin(ang) * 48 * v
        elif i < 26:  # torso
            px, py = (u - 0.5) * 120, -250 + v * 150
        else:   # robe on the ground
            px, py = (u - 0.5) * (220 + 40 * v), -100 + v * 90
        pts.append((x + px * s, y + py * s))
    for i in range(0, 20, 2):
        la = clamp(a * 2 - 1) * 0.35
        cv.drawLine(*pts[i], *pts[i + 1], paint((190, 205, 255), la, stroke=1.5))
    for i, (px, py) in enumerate(pts):
        vis = clamp(a * 1.6 - hashf(i, 73) * 0.6)
        tw = 0.6 + 0.4 * math.sin(t * (2 + 3 * hashf(i, 74)) + i)
        r = (1.4 + 2.6 * hashf(i, 75) ** 2) * br
        cv.drawCircle(px, py, r, paint((255, 250, 235), vis * tw))
        glow(cv, px, py, r * 7, (200, 215, 255), 0.45 * vis * tw)


def sprout(cv, x, y, grow, t, a=1.0, s=1.0):
    if a <= 0 or grow <= 0:
        return
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    h = 90 * grow
    stem = skia.Path()
    stem.moveTo(0, 0)
    stem.cubicTo(-8, -h * 0.3, 10, -h * 0.6, 0, -h)
    glow(cv, 0, -h * 0.5, 80 + 60 * grow, (255, 220, 140), 0.55 * a)
    cv.drawPath(stem, paint((170, 230, 140), a, stroke=5))
    for side, k in ((-1, 0.6), (1, 0.85)):
        g2 = clamp((grow - k + 0.4) / 0.4)
        if g2 <= 0:
            continue
        ly = -h * k
        leaf = skia.Path()
        leaf.moveTo(0, ly)
        leaf.quadTo(side * 30 * g2, ly - 26 * g2, side * 46 * g2, ly - 8 * g2)
        leaf.quadTo(side * 26 * g2, ly + 6 * g2, 0, ly)
        cv.drawPath(leaf, paint((190, 245, 150), a))
    glow(cv, 0, -h, 22, (255, 250, 220), a)
    cv.restore()


def light_rays(cv, x, y, a, t, n=9, L=900, col=(255, 220, 160), spread=1.2, base=-math.pi / 2):
    if a <= 0:
        return
    for i in range(n):
        ang = base + (i - (n - 1) / 2) / max(1, n - 1) * spread + 0.04 * math.sin(t * 0.5 + i)
        w = 0.035 + 0.02 * hashf(i, 3)
        ray = path([(x, y), (x + math.cos(ang - w) * L, y + math.sin(ang - w) * L),
                    (x + math.cos(ang + w) * L, y + math.sin(ang + w) * L)])
        cv.drawPath(ray, paint(shader=rad((x, y), L, [(col, 0.22 * a * (0.6 + 0.4 * hashf(i, 4))), (col, 0.0)]),
                               blend="plus"))


def vignette(cv, a=0.5, col=(0, 0, 0), inner=0.45):
    cv.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad((W / 2, H * 0.45), H * 0.75,
                                                         [(col, 0.0), (col, 0.0), (col, a)], [0, inner, 1])))


def grade(cv, col, a, mode="softlight"):
    if a > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(col, a, blend=mode))


def loom(cv, x, y, s, t, shuttle=0.0, dim=0.0, bars=0.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    wood = mixc((126, 88, 56), (40, 34, 46), dim)
    thread = mixc((226, 214, 190), (90, 90, 110), dim)
    w, h = 300, 420
    # woven cloth (bottom)
    cloth_h = 150
    cv.drawRect(skia.Rect.MakeLTRB(-w / 2, h - cloth_h, w / 2, h), paint(mixc((170, 70, 60), (50, 30, 50), dim)))
    for k in range(10):
        cv.drawLine(-w / 2, h - cloth_h + k * 15, w / 2, h - cloth_h + k * 15,
                    paint(mixc((200, 160, 90), (70, 60, 70), dim), 0.7, stroke=4))
    # warp threads
    for i in range(24):
        xx = -w / 2 + 10 + i * (w - 20) / 23
        cv.drawLine(xx, 0, xx, h - cloth_h, paint(thread, 0.9, stroke=2))
    cv.drawRect(skia.Rect.MakeLTRB(-w / 2 - 20, -20, -w / 2, h + 40), paint(wood))
    cv.drawRect(skia.Rect.MakeLTRB(w / 2, -20, w / 2 + 20, h + 40), paint(wood))
    cv.drawRect(skia.Rect.MakeLTRB(-w / 2 - 30, -30, w / 2 + 30, -6), paint(shade(wood, 1.1)))
    cv.drawRect(skia.Rect.MakeLTRB(-w / 2 - 20, h - cloth_h - 8, w / 2 + 20, h - cloth_h + 8), paint(shade(wood, 0.9)))
    # shuttle
    sx = lerp(-w / 2 + 30, w / 2 - 30, shuttle)
    cv.drawRoundRect(skia.Rect.MakeLTRB(sx - 34, h - cloth_h - 26, sx + 34, h - cloth_h - 12), 7, 7,
                     paint(shade(wood, 1.25)))
    cv.restore()


def wheel(cv, x, y, s, t, spin=0.0, dim=0.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    wood = mixc((120, 84, 54), (40, 34, 46), dim)
    clay = mixc((168, 104, 70), (60, 40, 50), dim)
    cv.drawRect(skia.Rect.MakeLTRB(-16, -10, 16, 120), paint(shade(wood, 0.8)))
    cv.drawOval(oval(0, 0, 90, 18), paint(shade(wood, 1.1)))
    cv.drawOval(oval(0, 6, 90, 18), paint(shade(wood, 0.8)))
    cv.drawOval(oval(0, 0, 90, 18), paint(shade(wood, 1.1)))
    pot = skia.Path()
    pot.moveTo(-30, 0)
    pot.cubicTo(-46, -40, -20, -60, -16, -90)
    pot.lineTo(16, -90)
    pot.cubicTo(20, -60, 46, -40, 30, 0)
    pot.close()
    cv.drawPath(pot, paint(shader=lin((-40, 0), (40, 0), [shade(clay, 0.7), shade(clay, 1.2), clay])))
    for k in range(4):
        yy = -12 - k * 20
        a = 0.4 * (0.5 + 0.5 * math.sin(spin * 12 + k))
        cv.drawLine(-28 + k * 3, yy, 28 - k * 3, yy, paint(shade(clay, 0.75), a, stroke=2))
    cv.restore()


def draw_back(cv, st, x, y, s, t=0.0, dim=0.0, turn=0.0):
    """A figure seen from behind (crowd foregrounds)."""
    from rig import _dim, robe_path
    p = {"dim": dim}
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    sway = math.sin(t * 1.1 + st.seed) * 2
    robe = _dim(st.robe, p)
    if st.cloak:
        robe = _dim(st.cloak, p)
    rp = robe_path(62 * st.girth, -372 + sway * 0.3, -228, 86 * st.girth, -8, 52 * st.girth)
    cv.drawPath(rp, paint(shader=lin((-90, 0), (90, 0), [shade(robe, 0.7), robe, shade(robe, 0.75)])))
    for side in (-1, 1):
        cv.drawLine(side * 56, -354, side * 74, -170, paint(shade(robe, 0.85), stroke=30))
    hc = _dim(st.head_c1 if st.head != "cap" else st.hair, p)
    hx = turn * 14 + sway
    cv.drawRect(skia.Rect.MakeLTRB(-16, -400, 16, -360), paint(shade(_dim(st.skin, p), 0.7)))
    if st.head in ("veil", "wrap", "keffiyeh"):
        k = skia.Path()
        k.moveTo(hx - 50, -410)
        k.cubicTo(hx - 60, -540, hx + 60, -540, hx + 50, -410)
        k.cubicTo(hx + 62, -380, hx + 80, -350, hx + 84, -330)
        k.lineTo(hx - 84, -330)
        k.cubicTo(hx - 80, -350, hx - 62, -380, hx - 50, -410)
        k.close()
        cv.drawPath(k, paint(shader=lin((0, -530), (0, -330), [shade(hc, 1.1), shade(hc, 0.8)])))
    else:
        cv.drawOval(oval(hx, -450, 44, 54), paint(_dim(st.hair, p)))
        cv.drawPath(spline([(hx - 46, -470), (hx, -520), (hx + 46, -470)], closed=False),
                    paint(_dim(st.head_c1, p), stroke=26))
    cv.restore()
