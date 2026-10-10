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


class Cam3:
    """Minimal perspective camera: position, downward pitch (deg), focal length."""

    def __init__(self, pos, pitch, f=900.0, cx=360.0, cy=640.0):
        self.C = pos
        p = math.radians(pitch)
        self.up = (math.cos(p), math.sin(p))     # (y, z) components
        self.fw = (-math.sin(p), math.cos(p))
        self.f, self.cx, self.cy = f, cx, cy

    @staticmethod
    def look_at(pos, target, f=900.0, cy=640.0):
        dy, dz = pos[1] - target[1], target[2] - pos[2]
        return Cam3(pos, math.degrees(math.atan2(dy, dz)), f, cy=cy)

    def depth(self, X, Y, Z):
        vy, vz = Y - self.C[1], Z - self.C[2]
        return vy * self.fw[0] + vz * self.fw[1]

    def p(self, X, Y, Z):
        vx, vy, vz = X - self.C[0], Y - self.C[1], Z - self.C[2]
        yc = vy * self.up[0] + vz * self.up[1]
        zc = max(0.5, vy * self.fw[0] + vz * self.fw[1])
        return (self.cx + self.f * vx / zc, self.cy - self.f * yc / zc)


def _quad(cam, pts):
    return path([cam.p(*q) for q in pts])


# drab, warm, lived-in adobe palette
ADOBE = [(214, 198, 170), (204, 186, 156), (220, 208, 186), (196, 180, 152), (210, 192, 160)]


def _village_layout():
    rnd = lambda *k: hashf(77, *k)
    houses = []
    for zi, gz in enumerate((14, 34, 56, 78, 100)):
        for xi, gx in enumerate((-45, -24, 24, 45)):
            w = 11 + 5 * rnd(zi, xi, 1)
            d = 9 + 4 * rnd(zi, xi, 2)
            h = 4.5 + 2.5 * rnd(zi, xi, 3) + (3.2 if rnd(zi, xi, 4) > 0.78 else 0)
            x = gx + (rnd(zi, xi, 5) - 0.5) * 4
            z = gz + (rnd(zi, xi, 6) - 0.5) * 3
            houses.append(dict(x0=x - w / 2, x1=x + w / 2, z0=z - d / 2, z1=z + d / 2, h=h, i=zi * 4 + xi,
                               col=ADOBE[int(rnd(zi, xi, 7) * 5)]))
    for k, gx in enumerate((-8, 9)):  # two houses behind the plaza
        houses.append(dict(x0=gx - 6, x1=gx + 6, z0=96, z1=106, h=5.5 + k, i=40 + k, col=ADOBE[k + 2]))
    return houses


HOUSES = _village_layout()


def _box(cv, cam, b, night=0.0, lights=0.0, details=True):
    x0, x1, z0, z1, h = b["x0"], b["x1"], b["z0"], b["z1"], b["h"]
    base = mixc(b["col"], (26, 30, 58), night * 0.8)
    top_c, front_c, lit_side, dark_side = shade(base, 1.07), shade(base, 0.86), shade(base, 0.95), shade(base, 0.68)
    cx = cam.C[0]
    # side walls (light comes from the left)
    if cx < x0:
        cv.drawPath(_quad(cam, [(x0, 0, z0), (x0, h, z0), (x0, h, z1), (x0, 0, z1)]), paint(lit_side))
    if cx > x1:
        cv.drawPath(_quad(cam, [(x1, 0, z0), (x1, h, z0), (x1, h, z1), (x1, 0, z1)]), paint(dark_side))
    # front wall, facing the camera
    cv.drawPath(_quad(cam, [(x0, 0, z0), (x1, 0, z0), (x1, h, z0), (x0, h, z0)]), paint(front_c))
    # roof with a low parapet lip
    cv.drawPath(_quad(cam, [(x0, h, z0), (x1, h, z0), (x1, h, z1), (x0, h, z1)]), paint(top_c))
    i = 0.6
    cv.drawPath(_quad(cam, [(x0 + i, h, z0 + i), (x1 - i, h, z0 + i), (x1 - i, h, z1 - i), (x0 + i, h, z1 - i)]),
                paint(shade(top_c, 0.94)))
    cv.drawPath(path([cam.p(x0, h, z0), cam.p(x1, h, z0)], closed=False), paint(shade(top_c, 1.08), stroke=1.6))
    # a little grime at the foot of the wall
    cv.drawPath(_quad(cam, [(x0, 0, z0), (x1, 0, z0), (x1, 0.5, z0), (x0, 0.5, z0)]), paint(shade(front_c, 0.82)))
    if not details:
        return
    r = lambda k: hashf(b["i"], k, 13)
    w = x1 - x0
    # one door, off-centre; at most one small window, never a symmetric "face"
    dl = x0 + w * (0.14 if r(1) < 0.5 else 0.62)
    door_c = mixc((74, 58, 46), (12, 12, 24), night * 0.6)
    cv.drawPath(_quad(cam, [(dl, 0, z0), (dl + 2.0, 0, z0), (dl + 2.0, 2.9, z0), (dl, 2.9, z0)]), paint(door_c))
    if r(2) > 0.35:
        wl = x0 + w * (0.62 if dl < x0 + w / 2 else 0.18)
        lit = lights * (r(9) > 0.4)
        wc = mixc(mixc((86, 72, 62), (16, 16, 30), night * 0.6), (255, 196, 120), lit)
        cv.drawPath(_quad(cam, [(wl, h * 0.55, z0), (wl + 1.4, h * 0.55, z0), (wl + 1.4, h * 0.55 + 1.2, z0),
                                (wl, h * 0.55 + 1.2, z0)]), paint(wc))
    if r(3) > 0.55:   # cloth awning over the door
        aw = mixc([(150, 92, 70), (116, 120, 104), (170, 140, 96)][int(r(4) * 3)], (30, 30, 50), night * 0.7)
        cv.drawPath(_quad(cam, [(dl - 0.6, 3.4, z0), (dl + 2.6, 3.4, z0), (dl + 2.6, 2.9, z0 - 1.6),
                                (dl - 0.6, 2.9, z0 - 1.6)]), paint(aw))
    if r(5) > 0.6:    # a cluster of clay jars in a back corner of the roof
        for k, (ux, uz, sz) in enumerate(((0.78, 0.8, 1.0), (0.86, 0.66, 0.75), (0.7, 0.62, 0.6))):
            jx, jz = x0 + w * ux, z0 + (z1 - z0) * uz
            p0 = cam.p(jx, h, jz)
            p1 = cam.p(jx, h + 1.2 * sz, jz)
            rr = abs(cam.p(jx + 0.55 * sz, h, jz)[0] - p0[0])
            jc = mixc((150, 98, 70), (40, 30, 46), night * 0.7)
            cv.drawOval(oval(p0[0], (p0[1] + p1[1]) / 2, rr, abs(p0[1] - p1[1]) / 2 + rr * 0.3), paint(jc))
            cv.drawOval(oval(p0[0] - rr * 0.3, (p0[1] + p1[1]) / 2 - rr * 0.2, rr * 0.35, rr * 0.5),
                        paint(shade(jc, 1.2), 0.6))
    if r(6) > 0.7:    # a ladder up the side
        for k in range(2):
            xx = x1 - 1.0 - k * 0.9
            cv.drawPath(path([cam.p(xx, 0, z0 - 0.4), cam.p(xx, h + 0.8, z0 - 0.1)], closed=False),
                        paint(mixc((110, 80, 52), (30, 26, 40), night * 0.7), stroke=1.4))


def _shadow(cv, cam, b, night=0.0):
    x0, x1, z0, z1, h = b["x0"], b["x1"], b["z0"], b["z1"], b["h"]
    sx, sz = 0.75 * h, 0.35 * h
    pts = [(x0, 0, z1), (x0, 0, z0), (x0 + sx, 0, z0 + sz), (x1 + sx, 0, z0 + sz), (x1 + sx, 0, z1 + sz), (x1, 0, z1)]
    cv.drawPath(_quad(cam, pts), paint((40, 30, 30), 0.22 * (1 - 0.6 * night)))


def _palm(cv, cam, x, z, h, t, night=0.0):
    base, top = cam.p(x, 0, z), cam.p(x + 0.8, h, z)
    s = cam.f / max(1, cam.depth(x, h, z))
    trunk = mixc((122, 92, 64), (34, 30, 44), night * 0.7)
    cv.drawPath(spline([base, ((base[0] + top[0]) / 2 + 2 * s, (base[1] + top[1]) / 2), top], closed=False),
                paint(trunk, stroke=max(1.5, 0.5 * s)))
    leaf = mixc((86, 112, 60), (24, 34, 40), night * 0.7)
    for k in range(7):
        ang = k / 7 * 2 * math.pi + 0.1 * math.sin(t + k)
        ex, ey = top[0] + math.cos(ang) * 3.8 * s, top[1] + math.sin(ang) * 1.6 * s + 1.2 * s
        cv.drawPath(spline([top, ((top[0] + ex) / 2, top[1] - 0.6 * s + (ey - top[1]) * 0.2), (ex, ey)], closed=False),
                    paint(leaf, stroke=max(1.2, 0.35 * s)))


def village3d(cv, cam, t, night=0.0, lights=0.0, crowd=True, glow_seed=0.0):
    dim = lambda c: mixc(c, (24, 28, 56), night * 0.82)
    # sand to the horizon, then the paved village floor with its straight lines
    cv.drawPath(_quad(cam, [(-3000, 0, cam.C[2] + 2), (3000, 0, cam.C[2] + 2), (3000, 0, 6000), (-3000, 0, 6000)]),
                paint(dim(SAND)))
    for k in range(18):
        zz = 140 + k * 26
        cv.drawPath(path([cam.p(-900, 0, zz), cam.p(0, 0, zz + 6), cam.p(900, 0, zz)], closed=False),
                    paint(dim(shade(SAND, 0.92)), 0.6, stroke=1.2))
    cv.drawPath(_quad(cam, [(-60, 0, 0), (60, 0, 0), (60, 0, 120), (-60, 0, 120)]), paint(dim(GROUND_IN)))
    for g in range(-60, 61, 8):
        cv.drawPath(path([cam.p(g, 0, 0), cam.p(g, 0, 120)], closed=False), paint(dim(shade(GROUND_IN, 0.9)), 0.5,
                                                                               stroke=0.8))
    for g in range(0, 121, 8):
        cv.drawPath(path([cam.p(-60, 0, g), cam.p(60, 0, g)], closed=False), paint(dim(shade(GROUND_IN, 0.9)), 0.5,
                                                                             stroke=0.8))
    walls = [dict(x0=-62, x1=62, z0=118, z1=121, h=7, i=90, col=(190, 176, 150)),
             dict(x0=-62, x1=-59, z0=0, z1=121, h=7, i=91, col=(190, 176, 150)),
             dict(x0=59, x1=62, z0=0, z1=121, h=7, i=92, col=(190, 176, 150)),
             dict(x0=-62, x1=-6, z0=-1, z1=2, h=7, i=93, col=(184, 170, 144)),
             dict(x0=6, x1=62, z0=-1, z1=2, h=7, i=94, col=(184, 170, 144))]
    towers = [dict(x0=x - 4, x1=x + 4, z0=z - 4, z1=z + 4, h=10.5, i=95 + k, col=(196, 182, 156))
              for k, (x, z) in enumerate(((-60, 0), (60, 0), (-60, 120), (60, 120), (-9, 0), (9, 0)))]
    dais_b = dict(x0=-5, x1=5, z0=60, z1=67, h=1.3, i=99, col=(176, 166, 150))
    blocks = HOUSES + walls + towers + [dais_b]
    for b in HOUSES + [dais_b]:
        _shadow(cv, cam, b, night)
    if glow_seed > 0:
        q = cam.p(0, 0, 64)
        glow(cv, q[0], q[1], 60 + 160 * glow_seed, (255, 214, 140), 0.85 * glow_seed)
    order = sorted(blocks, key=lambda b: -cam.depth((b["x0"] + b["x1"]) / 2, 0, (b["z0"] + b["z1"]) / 2))
    palms = [(-14, 44), (15, 86), (-52, 66)]
    drawn_palms = set()
    for b in order:
        dz = cam.depth(0, 0, (b["z0"] + b["z1"]) / 2)
        for k, (px, pz) in enumerate(palms):
            if k not in drawn_palms and cam.depth(px, 0, pz) > dz:
                _palm(cv, cam, px, pz, 9, t, night)
                drawn_palms.add(k)
        _box(cv, cam, b, night, lights, details=b["i"] < 90)
        if b is dais_b and crowd and night < 0.5:
            for k in range(22):
                a = math.pi * (0.1 + 0.8 * hashf(k, 31))
                rr = 9 + 5 * hashf(k, 32)
                fx, fz = math.cos(a) * rr, 63 - math.sin(a) * rr * 0.9
                pb, ph = cam.p(fx, 0, fz), cam.p(fx, 1.7, fz)
                sz = abs(pb[1] - ph[1])
                cv.drawOval(oval(pb[0], (pb[1] + ph[1]) / 2 + sz * 0.1, sz * 0.22, sz * 0.42),
                            paint(dim(HEAD_COLS[k % 4])))
                cv.drawCircle(ph[0], ph[1], sz * 0.14, paint(dim((176, 140, 110))))
            pe, he = cam.p(0, 1.3, 63.5), cam.p(0, 3.3, 63.5)
            sz = abs(pe[1] - he[1])
            cv.drawOval(oval(pe[0], (pe[1] + he[1]) / 2, sz * 0.2, sz * 0.45), paint((64, 62, 90)))
    for k, (px, pz) in enumerate(palms):
        if k not in drawn_palms:
            _palm(cv, cam, px, pz, 9, t, night)
    # the gate
    g = [(-3.2, 0, -1.05), (3.2, 0, -1.05), (3.2, 5.2, -1.05), (-3.2, 5.2, -1.05)]
    cv.drawPath(_quad(cam, g), paint(dim((96, 68, 44))))
    cv.drawPath(path([cam.p(0, 0, -1.05), cam.p(0, 5.2, -1.05)], closed=False), paint(dim((60, 42, 28)), stroke=1.2))


HEAD_COLS = [(160, 150, 130), (140, 132, 118), (120, 116, 108), (96, 100, 120)]


def aerial_view(cv, t, cam, night=0.0, lights=0.0, glow_seed=0.0, crowd=True):
    """The walled village from a hill, in true 3D, with sky and horizon."""
    hz = cam.p(0, 0, 1e6)[1]
    top = mixc((120, 150, 190), (8, 10, 30), night)
    hor = mixc((238, 214, 180), (50, 46, 80), night)
    sky(cv, [top, hor], None, 0, hz + 10)
    if night:
        stars(cv, t, night, n=160, y1=hz)
    mountains(cv, hz + 4, mixc((176, 150, 140), (40, 40, 66), night), seed=11, h=36)
    village3d(cv, cam, t, night, lights, crowd, glow_seed)
    cv.drawRect(skia.Rect.MakeLTRB(-400, hz, W + 400, hz + 200), paint(
        shader=lin((0, hz), (0, hz + 200), [(hor, 0.7), (hor, 0.0)])))


def house_row(cv, y_base, height, n=6, x0=-80, x1=W + 80, dim=0.0, seed=1, col=HOUSE_FRONT, lights=0.0):
    """A street of plain adobe houses: varied heights, one door each, never a symmetric 'face'."""
    w = (x1 - x0) / n
    vx = (x0 + x1) / 2
    for i in range(n):
        r = lambda k: hashf(seed, i, k)
        x = x0 + i * w
        hh = height * (0.82 + 0.3 * r(1))
        c = mixc(mixc(col, ADOBE[int(r(2) * 5)], 0.4), (36, 40, 66), dim)
        l, rr_ = x + 3, x + w - 3
        # a sliver of side wall, turned away from the street's centre, gives each house depth
        side = 14 if (l + rr_) / 2 < vx else -14
        sx = rr_ if side > 0 else l
        cv.drawPath(path([(sx, y_base - hh), (sx + side, y_base - hh - 8), (sx + side, y_base - 6), (sx, y_base)]),
                    paint(shade(c, 0.72)))
        cv.drawRect(skia.Rect.MakeLTRB(l, y_base - hh, rr_, y_base), paint(c))
        cv.drawRect(skia.Rect.MakeLTRB(l - 3, y_base - hh - 9, rr_ + 3, y_base - hh + 3), paint(shade(c, 1.1)))
        cv.drawRect(skia.Rect.MakeLTRB(l, y_base - hh + 3, rr_, y_base - hh + 9), paint(shade(c, 0.8), 0.5))
        cv.drawRect(skia.Rect.MakeLTRB(l, y_base - 10, rr_, y_base), paint(shade(c, 0.85), 0.6))
        # one door, off-centre
        dw = w * 0.2
        dx = l + (w - 6) * (0.18 if r(3) < 0.5 else 0.6)
        door = mixc((78, 62, 50), (20, 20, 36), dim)
        cv.drawRect(skia.Rect.MakeLTRB(dx, y_base - min(hh * 0.5, 120), dx + dw, y_base), paint(door))
        cv.drawRect(skia.Rect.MakeLTRB(dx - 3, y_base - min(hh * 0.5, 120) - 5, dx + dw + 3,
                                       y_base - min(hh * 0.5, 120)), paint(shade(c, 0.75)))
        # at most one small window, on the other side and at its own height
        if r(4) > 0.3:
            wx = l + (w - 6) * (0.62 if dx < x + w / 2 else 0.16) + w * 0.04
            wy = y_base - hh * (0.62 + 0.15 * r(5))
            lit = lights * (r(6) > 0.35)
            cv.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + w * 0.13, wy + w * 0.11),
                        paint(mixc(mixc((86, 74, 66), (20, 20, 36), dim), (255, 196, 120), lit)))
            if lit:
                glow(cv, wx + w * 0.06, wy + w * 0.05, w * 0.3, (255, 180, 100), 0.35 * lit)
        if r(7) > 0.6:   # cloth awning
            aw = mixc([(150, 96, 74), (118, 122, 104), (168, 140, 98)][int(r(8) * 3)], (30, 30, 50), dim * 0.9)
            cv.drawPath(path([(dx - 10, y_base - min(hh * 0.5, 120) - 14), (dx + dw + 10, y_base - min(hh * 0.5, 120) - 14),
                              (dx + dw + 16, y_base - min(hh * 0.5, 120) + 10), (dx - 16, y_base - min(hh * 0.5, 120) + 10)]),
                         paint(aw))
        if r(9) > 0.75:  # outside stair to the roof
            sx0 = rr_ - 6 if dx < x + w / 2 else l + 6
            sgn = -1 if dx < x + w / 2 else 1
            cv.drawPath(path([(sx0, y_base), (sx0 + sgn * w * 0.3, y_base - hh * 0.95), (sx0 + sgn * w * 0.3, y_base)]),
                        paint(shade(c, 0.9)))


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
def _branches(x, y, ang, length, width, depth, seed, out):
    """Recursive branching: appends (x0, y0, x1, y1, width, depth) segments."""
    x1 = x + math.cos(ang) * length
    y1 = y + math.sin(ang) * length
    out.append((x, y, x1, y1, width, depth))
    if depth == 0:
        return
    n = 2 if hashf(seed, depth, 1) < 0.6 else 3
    for k in range(n):
        spread = (k - (n - 1) / 2) * 0.55 + (hashf(seed, k, depth) - 0.5) * 0.35
        _branches(x1, y1, ang + spread, length * (0.68 + 0.12 * hashf(seed, k, 9)), width * 0.66, depth - 1,
                  seed * 3 + k + 1, out)


def burning_bush(cv, x, y, s, t, a=1.0):
    """The bush that burned and was not consumed: woody branches, green leaves, flames among them."""
    if a <= 0:
        return
    cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cv.translate(x, y)
    cv.scale(s, s)
    glow(cv, 0, -110, 330, (255, 150, 50), 0.4)
    # rocky mound it grows from
    mound = skia.Path()
    mound.moveTo(-150, 18)
    mound.cubicTo(-120, -22, 120, -22, 150, 18)
    mound.close()
    cv.drawPath(mound, paint((120, 86, 60)))
    for k in range(5):
        cv.drawOval(oval(-110 + k * 55, 6 + 4 * (k % 2), 24, 13), paint((140, 104, 74)))
    segs = []
    for k, ang in enumerate((-2.45, -2.05, -1.7, -1.4, -1.05, -0.7)):
        _branches(k * 12 - 30, 4, ang, 56 + 8 * hashf(k, 5), 10, 3, 11 + k, segs)
    # flames behind the bush
    def flames(front):
        for i in range(34):
            if (i % 3 == 0) != front:
                continue
            sx, sy, ex, ey, w, d = segs[(i * 7) % len(segs)]
            fx, fy = ex, ey + 6
            h = 30 + 46 * hashf(i, 3)
            fl = 1 + 0.35 * math.sin(t * (6 + 6 * hashf(i, 4)) + i * 1.7)
            sway = 6 * math.sin(t * 4 + i)
            fw = 8 + 6 * hashf(i, 6)
            f = skia.Path()
            f.moveTo(fx - fw, fy)
            f.cubicTo(fx - fw * 1.2, fy - h * 0.5 * fl, fx + sway - 3, fy - h * 0.7 * fl, fx + sway, fy - h * fl)
            f.cubicTo(fx + sway + 3, fy - h * 0.7 * fl, fx + fw * 1.2, fy - h * 0.5 * fl, fx + fw, fy)
            f.quadTo(fx, fy + fw * 0.8, fx - fw, fy)
            f.close()
            sh = lin((fx, fy), (fx, fy - h * fl), [((235, 70, 20), 0.88), ((255, 140, 30), 0.82),
                                                    ((255, 225, 110), 0.72), ((255, 245, 200), 0.0)],
                     [0, 0.35, 0.75, 1])
            cv.drawPath(f, paint(shader=sh) if front else paint(shader=sh, blend="screen"))
    flames(False)
    # woody branches
    for (sx, sy, ex, ey, w, d) in segs:
        cv.drawLine(sx, sy, ex, ey, paint((74, 46, 28), stroke=w))
        cv.drawLine(sx - w * 0.2, sy, ex - w * 0.2, ey, paint((110, 74, 46), 0.6, stroke=w * 0.35))
    # leaves: clusters along the outer branches, clearly green
    greens = [(46, 104, 38), (66, 132, 46), (92, 158, 58), (120, 176, 70)]
    for j, (sx, sy, ex, ey, w, d) in enumerate(segs):
        if d > 1:
            continue
        for k in range(7 if d == 0 else 4):
            u = 0.35 + 0.65 * hashf(j, k, 1)
            lx, ly = lerp(sx, ex, u), lerp(sy, ey, u)
            ang = math.atan2(ey - sy, ex - sx) + (1 if k % 2 else -1) * (0.7 + 0.5 * hashf(j, k, 2))
            ang += 0.08 * math.sin(t * 2 + j + k)
            L = 15 + 8 * hashf(j, k, 3)
            cx, cy = lx + math.cos(ang) * L * 0.55, ly + math.sin(ang) * L * 0.55
            cv.save()
            cv.translate(cx, cy)
            cv.rotate(math.degrees(ang))
            leaf = skia.Path()
            leaf.moveTo(-L / 2, 0)
            leaf.quadTo(0, -L * 0.36, L / 2, 0)
            leaf.quadTo(0, L * 0.36, -L / 2, 0)
            leaf.close()
            g = greens[int(hashf(j, k, 4) * 4)]
            cv.drawPath(leaf, paint(g))
            cv.drawLine(-L / 2, 0, L / 2, 0, paint(shade(g, 1.35), 0.7, stroke=1.2))
            cv.restore()
    # firelight catching the leaves, and flames in front
    glow(cv, 0, -90, 150, (255, 170, 70), 0.35, blend="screen")
    flames(True)
    glow(cv, 0, -100, 60, (255, 235, 180), 0.35)
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


def _divine_parts():
    """Parts of the colossal figure, back to front. Local coords: base centre (0, 0), head ~ -745."""
    parts = []
    hair = skia.Path()   # long hair falling behind the shoulders
    hair.moveTo(-62, -812)
    hair.cubicTo(-104, -770, -112, -680, -108, -585)
    hair.lineTo(106, -585)
    hair.cubicTo(110, -680, 100, -770, 58, -812)
    hair.cubicTo(40, -860, -44, -860, -62, -812)
    hair.close()
    parts.append(("hair", hair))
    body = skia.Path()   # shoulders and robe rising from behind the horizon
    body.moveTo(-60, -615)
    body.cubicTo(-170, -615, -262, -592, -286, -515)
    body.cubicTo(-306, -420, -318, -200, -350, 40)
    body.lineTo(350, 40)
    body.cubicTo(318, -200, 306, -420, 286, -515)
    body.cubicTo(262, -592, 170, -615, 60, -615)
    body.close()
    parts.append(("body", body))
    face = skia.Path()
    face.addOval(oval(-4, -748, 60, 76))
    parts.append(("face", face))
    beard = skia.Path()
    beard.moveTo(-60, -736)
    beard.cubicTo(-66, -650, -38, -580, -10, -555)
    beard.lineTo(6, -555)
    beard.cubicTo(32, -580, 58, -650, 54, -736)
    beard.cubicTo(30, -706, 10, -712, -4, -722)
    beard.cubicTo(-18, -712, -38, -706, -60, -736)
    beard.close()
    parts.append(("beard", beard))
    arm = skia.Path()   # reaching down and forward, toward Moses
    arm.moveTo(-286, -540)
    arm.cubicTo(-330, -470, -360, -400, -352, -340)
    arm.cubicTo(-344, -280, -300, -230, -250, -196)
    arm.lineTo(-196, -236)
    arm.cubicTo(-240, -262, -280, -300, -284, -350)
    arm.cubicTo(-288, -410, -268, -470, -222, -536)
    arm.close()
    parts.append(("arm", arm))
    hand = skia.Path()   # broad open hand, palm down, fingers curving toward his shoulders
    hand.moveTo(-262, -214)
    hand.cubicTo(-282, -186, -280, -160, -266, -140)
    for k in range(4):
        x = -262 + k * 27
        hand.cubicTo(x - 4, -110, x + 2, -88, x + 9, -86)
        hand.cubicTo(x + 18, -86, x + 20, -110, x + 22, -136)
    hand.cubicTo(-140, -150, -160, -200, -190, -238)
    hand.close()
    parts.append(("hand", hand))
    return parts


DIVINE = _divine_parts()


def _divine_union(cv):
    for name, pth in DIVINE:
        cv.save()
        if name in ("face", "beard", "hair"):
            cv.translate(-6, -560)
            cv.rotate(-12)       # head bowed toward him
            cv.translate(6, 560)
        cv.drawPath(pth, paint((255, 255, 255)))
        cv.restore()


def divine_figure(cv, x, y, s, t, a=1.0, sigh=0.0):
    """The presence: a towering masculine figure made of night and starlight, bending over him."""
    if a <= 0:
        return
    br = 1 + 0.25 * sigh

    def begin(alpha, blur=0.0, blend=None):
        lp = skia.Paint()
        if blur:
            lp.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        if blend:
            lp.setBlendMode(blend)
        lp.setAlphaf(clamp(alpha))
        cv.saveLayer(None, lp)
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)

    def end():
        cv.restore()
        cv.restore()

    # outer aura
    begin(0.4 * a * br, blur=36)
    _divine_union(cv)
    cv.drawPaint(paint((120, 145, 255), blend="srcin_fix"))
    end()
    # each part: a deep night-blue body with its own luminous rim, so beard, face, arm and hand all read
    begin(a)
    fill_sh = lin((0, -840), (0, 40), [(34, 42, 104), (22, 28, 74), ((16, 18, 50), 0.75)], [0, 0.6, 1])
    for name, pth in DIVINE:
        cv.save()
        if name in ("face", "beard", "hair"):
            cv.translate(-6, -560)
            cv.rotate(-12)
            cv.translate(6, 560)
        f = paint(shader=fill_sh)
        if name == "face":
            f = paint((44, 54, 124))
        cv.drawPath(pth, f)
        cv.drawPath(pth, paint((150, 175, 255), 0.55, stroke=7, blur=5))
        cv.drawPath(pth, paint((215, 228, 255), 0.95, stroke=2.2))
        if name == "face":
            for sx in (-28, 20):   # closed eyes, looking down at him
                cv.drawPath(spline([(sx - 15, -764), (sx, -755), (sx + 15, -764)], closed=False),
                            paint((225, 232, 255), 0.85, stroke=2.4))
                cv.drawPath(spline([(sx - 16, -786), (sx, -792), (sx + 16, -786)], closed=False),
                            paint((200, 215, 255), 0.5, stroke=2.2))
            cv.drawPath(spline([(-2, -752), (-9, -728), (0, -722)], closed=False), paint((200, 215, 255), 0.6, stroke=2))
        if name == "body":   # neckline and a few robe folds
            for (x0, y0, x1, y1) in ((-120, -560, -170, 30), (120, -560, 190, 30), (0, -540, 10, 30)):
                cv.drawLine(x0, y0, x1, y1, paint((150, 175, 255), 0.25, stroke=2))
        if name == "beard":
            for k in range(5):
                xx = -40 + k * 20
                cv.drawLine(xx, -690, xx * 0.6, -575, paint((170, 190, 255), 0.35, stroke=1.6))
        cv.restore()
    end()
    # stars living inside the figure
    begin(a)
    for i in range(240):
        px, py = (hashf(i, 81) - 0.5) * 820, -860 + hashf(i, 82) * 900
        tw = 0.55 + 0.45 * math.sin(t * (1.5 + 3 * hashf(i, 83)) + i)
        r = 0.9 + 2.4 * hashf(i, 84) ** 3
        cv.drawCircle(px, py, r * br, paint((255, 250, 235), tw))
        if r > 2:
            glow(cv, px, py, r * 8, (200, 215, 255), 0.5 * tw)
    mp = skia.Paint()
    mp.setBlendMode(skia.BlendMode.kDstIn)
    cv.saveLayer(None, mp)
    _divine_union(cv)
    cv.restore()
    end()


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
        if st.head == "keffiyeh":
            cv.save()
            cv.clipPath(k, skia.ClipOp.kIntersect, True)
            for i in range(-3, 4):
                cv.drawLine(hx + i * 22, -540, hx + i * 30, -330, paint(_dim(st.head_c2, p), 0.35, stroke=4))
            cv.restore()
            cv.drawPath(spline([(hx - 52, -470), (hx, -478), (hx + 52, -470)], closed=False),
                        paint(_dim((40, 28, 24), p), stroke=13))
    else:
        cv.drawOval(oval(hx, -450, 44, 54), paint(_dim(st.hair, p)))
        cv.drawPath(spline([(hx - 46, -470), (hx, -520), (hx + 46, -470)], closed=False),
                    paint(_dim(st.head_c1, p), stroke=26))
    cv.restore()
