"""Cairo renderer: draws one frame from a sim state."""
import math, os
import numpy as np
import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
TAU = math.tau
INK = (0.08, 0.06, 0.11)
from story import POS

SUBCOL = {'N': (1.0, 0.86, 0.62), 'IRIS': (0.72, 0.95, 0.45), 'BEE': (1.0, 0.86, 0.3),
          'CLAWD': (0.72, 0.76, 1.0), 'CLAWDIA': (1.0, 0.72, 0.9), 'GOSTE': (0.78, 0.96, 1.0)}
NAMES = {'IRIS': 'IRIS', 'BEE': 'BEE-EYE', 'CLAWD': 'CLAWD', 'CLAWDIA': 'CLAWDIA', 'GOSTE': 'GOSTE'}


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


# ------------------------------------------------------------------ paths
def wob(pts, seed, t, amp=1.3):
    b = int(t * 8)  # line boil on "threes"
    r = np.random.default_rng((seed * 7919 + b * 104729) & 0xFFFFFFFF)
    return pts + r.normal(0, amp, pts.shape)


def spline(ctx, pts, closed=True):
    n = len(pts)
    if closed:
        ctx.move_to(*pts[0])
        for i in range(n):
            p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
            ctx.curve_to(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                         p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1])
        ctx.close_path()
    else:
        ctx.move_to(*pts[0])
        for i in range(n - 1):
            p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, n - 1)]
            ctx.curve_to(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
                         p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1])


def ink(ctx, lw, alpha=1.0, col=INK):
    ctx.set_source_rgba(*col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def fill_ink(ctx, col, lw, alpha=1.0, ink_alpha=None):
    ctx.set_source_rgba(*col, alpha)
    ctx.fill_preserve()
    ink(ctx, lw, alpha if ink_alpha is None else ink_alpha)


def circle_pts(r, n=18, rx=1.0):
    a = np.linspace(0, TAU, n, endpoint=False)
    return np.stack([np.cos(a) * r * rx, np.sin(a) * r], 1)


# ------------------------------------------------------------------ face parts
def brow(ctx, R, S, lw, seed, t, col=INK, width=0.15, rise=1.32):
    yb = -R * rise - S['brow'] * R * 0.32 + S['lid'] * R * 0.14 - S.get('emph', 0) * R * 0.12
    ar, tb = S['arch'], S['tiltb']
    p = np.array([[-R * 0.8, yb + ar * R * 0.26 - tb * R * 0.2],
                  [0, yb - ar * R * 0.24],
                  [R * 0.8, yb + ar * R * 0.26 + tb * R * 0.2]])
    p = wob(p, seed, t, R * 0.012)
    # quadratic through the 3 points, then a tapered ribbon
    c = 2 * p[1] - 0.5 * (p[0] + p[2])
    us = np.linspace(0, 1, 15)
    pts = np.array([(1 - u) ** 2 * p[0] + 2 * (1 - u) * u * c + u ** 2 * p[2] for u in us])
    tan = np.gradient(pts, axis=0)
    nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    wv = R * width * (0.18 + 0.82 * np.sin(np.pi * us) ** 0.7) / 2
    outline = np.concatenate([pts + nrm * wv[:, None], (pts - nrm * wv[:, None])[::-1]])
    ctx.move_to(*outline[0])
    for q in outline[1:]:
        ctx.line_to(*q)
    ctx.close_path()
    ctx.set_source_rgb(*col)
    ctx.fill_preserve()
    ink(ctx, R * 0.02, 1, col)


def eyeball(ctx, R, S, lw, seed, t, iris=(0.5, 0.8, 0.3), sclera=(0.97, 0.95, 0.9),
            lidc=(0.8, 0.75, 0.65), veins=0, ring=True, rx=1.0, pupil_oval=1.0, lashes=False):
    lid = max(S['lid'], S.get('blink', 0))
    blid = S['blid'] * (1 - S.get('blink', 0))
    lx, ly = S['lookv']
    outline = wob(circle_pts(R, 20, rx), seed, t, R * 0.012)
    spline(ctx, outline)
    ctx.set_source_rgb(*sclera)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if veins:
        rr = np.random.default_rng(seed)
        for i in range(9):
            a = i / 9 * TAU + rr.uniform(-.2, .2)
            pts = []
            for k in range(5):
                r = R * (1.0 - k * 0.11)
                aa = a + math.sin(k * 2.1 + i) * 0.12
                pts.append((math.cos(aa) * r * rx, math.sin(aa) * r))
            spline(ctx, np.array(pts), closed=False)
            ink(ctx, lw * 0.55, 0.75 * veins, (0.62, 0.08, 0.12))
    ox, oy = lx * R * 0.42 * rx, ly * R * 0.38
    ir = R * 0.5
    g = cairo.RadialGradient(ox, oy, ir * 0.2, ox, oy, ir)
    g.add_color_stop_rgb(0, *mix(iris, (1, 1, 1), 0.25))
    g.add_color_stop_rgb(1, *mix(iris, (0, 0, 0), 0.35))
    ctx.arc(ox, oy, ir, 0, TAU)
    ctx.set_source(g)
    ctx.fill_preserve()
    ink(ctx, lw * 0.9)
    if ring:
        ctx.arc(ox, oy, ir * 0.72, 0, TAU)
        ink(ctx, lw * 0.6, 0.55)
    pr = R * 0.21 * S['pupil']
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(1, pupil_oval)
    ctx.arc(0, 0, pr, 0, TAU)
    ctx.restore()
    ctx.set_source_rgb(*INK)
    ctx.fill()
    lash_edge = None
    tear = S.get('tear', 0)
    hr = R * (0.1 + 0.05 * tear)
    ctx.arc(ox - R * 0.17, oy - R * 0.18, hr, 0, TAU)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill()
    ctx.arc(ox + R * 0.14, oy + R * 0.12, hr * 0.45, 0, TAU)
    ctx.fill()
    if tear > 0.05:
        ctx.save()
        ctx.scale(rx, 1)
        ctx.arc(0, R * 0.25, R * 0.85, math.radians(35), math.radians(145))
        ctx.restore()
        ink(ctx, R * 0.09, 0.55 * tear, (0.7, 0.9, 1.0))
    # top lid
    if lid > 0.01:
        ye = -R + 2.05 * R * lid
        bow = R * 0.22 * (1 - abs(lid - 0.5))
        xs = np.linspace(-R * 1.1, R * 1.1, 9)
        edge = [(x, ye + bow * (1 - (x / (R * 1.1)) ** 2)) for x in xs]
        ctx.move_to(-R * 1.2, -R * 1.2)
        for p in edge:
            ctx.line_to(*p)
        ctx.line_to(R * 1.2, -R * 1.2)
        ctx.close_path()
        ctx.set_source_rgb(*lidc)
        ctx.fill()
        spline(ctx, np.array(edge), closed=False)
        ink(ctx, lw * 1.25)
        # crease
        ce = [(x_, y_ - R * 0.16) for x_, y_ in edge[1:-1]]
        if lid > 0.25:
            spline(ctx, np.array(ce), closed=False)
            ink(ctx, lw * 0.5, 0.35)
        if lashes and lid > 0.08:
            lash_edge = edge
    if blid > 0.01:
        yb = R - 1.15 * R * blid
        xs = np.linspace(-R * 1.1, R * 1.1, 9)
        edge = [(x, yb - R * 0.25 * blid * (1 - (x / (R * 1.1)) ** 2)) for x in xs]
        ctx.move_to(-R * 1.2, R * 1.2)
        for p in edge:
            ctx.line_to(*p)
        ctx.line_to(R * 1.2, R * 1.2)
        ctx.close_path()
        ctx.set_source_rgb(*lidc)
        ctx.fill()
        spline(ctx, np.array(edge), closed=False)
        ink(ctx, lw * 0.9)
    ctx.restore()
    spline(ctx, outline)
    ink(ctx, lw)
    if lash_edge is not None:
        for k in range(2, 7):
            x_, y_ = lash_edge[k]
            if x_ * x_ + y_ * y_ > (R * 1.02) ** 2:
                continue
            ang = math.atan2(1.0, x_ / R * 1.4)
            ctx.move_to(x_, y_)
            ctx.line_to(x_ + math.cos(ang) * R * 0.14 + x_ * 0.08, y_ + math.sin(ang) * R * 0.14)
            ink(ctx, lw * 0.6)


def mouth(ctx, w, S, lw, seed, t, oness=0.0, inner=(0.3, 0.05, 0.1), skin=None):
    talk = S.get('talk', 0)
    sib = S.get('sib', 0)
    op = clamp(S.get('mopen', 0) + talk * (0.95 - 0.45 * clamp(sib * 3 - 0.3)))
    wide = 1 + 0.18 * clamp(sib * 3 - 0.3) - 0.12 * op * (1 - oness)
    we = w * wide * (1 - oness) + w * 0.42 * oness
    h_norm = we * 0.62 * op
    h_o = we * (1.2 + 0.5 * op)
    h = h_norm * (1 - oness) + h_o * oness
    sm = S['smile'] * (1 - oness)
    k = sm * w * 0.2
    xs = np.linspace(-we / 2, we / 2, 11)
    base = np.array([k * (1 - (2 * x / we) ** 2) - k * 0.5 for x in xs])
    prof = np.sqrt(np.clip(1 - (2 * xs / we) ** 2, 0, 1)) ** (0.7 + 0.3 * oness)
    up = 0.35 + 0.15 * oness
    top = np.stack([xs, base - h * prof * up], 1)
    bot = np.stack([xs, base + h * prof * (1 - up)], 1)
    if h < 2.0:
        pts = wob(np.stack([xs, base], 1)[::2], seed, t, w * 0.012)
        spline(ctx, pts, closed=False)
        ink(ctx, lw)
        return
    shape = np.concatenate([top, bot[::-1][1:-1]])
    shape = wob(shape, seed, t, w * 0.008)
    spline(ctx, shape)
    ctx.set_source_rgb(*inner)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if h > w * 0.12:
        ctx.save()
        ctx.translate(0, base[5] + h * (1 - up) * 0.9)
        ctx.scale(1, 0.5)
        ctx.arc(0, 0, we * 0.28, 0, TAU)
        ctx.restore()
        ctx.set_source_rgb(0.85, 0.35, 0.4)
        ctx.fill()
    ctx.restore()
    spline(ctx, shape)
    ink(ctx, lw)


# ------------------------------------------------------------------ characters
def draw_iris(ctx, S, t, night):
    x, y = S['x'], S['y']
    lean, droop, spread = S['lean'], S['droop'], S['spread']
    hx = x + lean * 80 + math.sin(t * 0.7) * 6
    hy = y + abs(lean) * 22 + droop * 22 + math.sin(t * 1.1) * 4 - S.get('talk', 0) * 4
    R = 165
    lw = 6
    # stem
    bx, by = x - 10, 1990
    c1 = (bx + 10, by - 300)
    c2 = (hx - lean * 120, hy + 380)
    ctx.move_to(bx, by)
    ctx.curve_to(*c1, *c2, hx, hy + R)
    ctx.set_source_rgb(*INK); ctx.set_line_width(20); ctx.stroke()
    ctx.move_to(bx, by)
    ctx.curve_to(*c1, *c2, hx, hy + R)
    ctx.set_source_rgb(0.33, 0.5, 0.25); ctx.set_line_width(10); ctx.stroke()

    def bez(u):
        p0, p1, p2, p3 = np.array((bx, by)), np.array(c1), np.array(c2), np.array((hx, hy + R))
        return (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * p3

    def leaf(u, ang, L, seed):
        px, py = bez(u)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(ang + math.sin(t * 1.3 + seed) * 0.05)
        pts = np.array([[0, 0], [L * 0.3, -L * 0.17], [L * 0.7, -L * 0.15], [L, 0],
                        [L * 0.7, L * 0.13], [L * 0.3, L * 0.15]])
        pts = wob(pts, seed, t, 1.5)
        spline(ctx, pts)
        g = cairo.LinearGradient(0, -L * 0.2, 0, L * 0.2)
        g.add_color_stop_rgb(0, 0.5, 0.72, 0.33)
        g.add_color_stop_rgb(1, 0.26, 0.45, 0.22)
        ctx.set_source(g)
        ctx.fill_preserve()
        ink(ctx, lw)
        ctx.move_to(8, 0)
        ctx.line_to(L * 0.92, 0)
        ink(ctx, lw * 0.6)
        for k in range(1, 6):
            xx = L * k / 6.3
            hw = L * 0.15 * math.sin(math.pi * (k / 6.3)) * 0.95
            ctx.move_to(xx - 6, -hw)
            ctx.curve_to(xx + 6, -hw * 0.4, xx - 6, hw * 0.4, xx + 6, hw)
            ink(ctx, lw * 0.5, 0.8)
        ctx.restore()

    leaf(0.42, math.radians(-150 + 55 * S['leafL']), 240, 11)
    leaf(0.64, math.radians(-40 - 25 * S['leafR']), 220, 12)

    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(lean * 0.12 + math.sin(t * 0.7) * 0.02)
    # petals
    n = 13
    for i in range(n):
        a0 = math.radians(158 + i * (226 / (n - 1)))
        # droop pulls toward down (90deg)
        a = a0 + droop * 0.45 * math.sin(a0 - math.pi / 2) * -1 * 0.9
        a += math.sin(t * 0.9 + i * 0.7) * 0.025 + spread * 0.04 * math.cos(a0)
        L = R * (1.82 + 0.12 * math.sin(i * 2.3)) * (1 - 0.12 * droop + 0.1 * spread)
        wdt = R * 0.36
        ctx.save()
        ctx.rotate(a)
        pts = np.array([[R * 0.7, -wdt * 0.32], [R * 1.25, -wdt * 0.5], [L * 0.93, -wdt * 0.42], [L, 0],
                        [L * 0.93, wdt * 0.42], [R * 1.25, wdt * 0.5], [R * 0.7, wdt * 0.32]])
        pts = wob(pts, 30 + i, t, 1.6)
        spline(ctx, pts)
        g = cairo.LinearGradient(R * 0.7, 0, L, 0)
        g.add_color_stop_rgb(0, *mix((0.93, 0.88, 0.76), night, 0.15))
        g.add_color_stop_rgb(1, *mix((0.98, 0.66, 0.36), night, 0.15))
        ctx.set_source(g)
        ctx.fill_preserve()
        ink(ctx, lw)
        ctx.restore()
    # lower rounded petals
    for i, a0 in enumerate((100, 122, 145)):
        ctx.save()
        ctx.rotate(math.radians(a0 + droop * 6))
        L = R * 1.38
        pts = np.array([[R * 0.75, -R * 0.2], [R * 1.1, -R * 0.24], [L, -R * 0.1], [L, R * 0.1],
                        [R * 1.1, R * 0.24], [R * 0.75, R * 0.2]])
        spline(ctx, wob(pts, 60 + i, t, 1.5))
        ctx.set_source_rgb(*mix((0.92, 0.84, 0.7), night, 0.15))
        ctx.fill_preserve()
        ink(ctx, lw)
        ctx.restore()
    # mouth interior below disk
    talk = S.get('talk', 0)
    op = clamp(S.get('mopen', 0) + talk * 0.9)
    sm = S['smile']
    ctx.save()
    ctx.translate(0, R * 0.78)
    ctx.scale(1, 0.3 + op * 0.55)
    ctx.arc(0, 0, R * 0.62, 0, math.pi)
    ctx.restore()
    ctx.set_source_rgb(0.25, 0.04, 0.08)
    ctx.fill()
    # eyeball
    eyeball(ctx, R, S, lw, 5, t, iris=(0.55, 0.82, 0.22), lidc=(0.78, 0.6, 0.55), veins=1, ring=True, lashes=True)
    # fangs
    for sx in (-1, 1):
        ctx.move_to(sx * R * 0.22, R * 0.96)
        ctx.line_to(sx * R * 0.15, R * (1.13 + op * 0.06))
        ctx.line_to(sx * R * 0.08, R * 0.985)
        ctx.close_path()
        fill_ink(ctx, (0.98, 0.97, 0.92), lw * 0.6)
    # sepal teeth (lower jaw) - the drawing's little rectangles
    drop = op * R * 0.42
    for i in range(6):
        u = (i - 2.5) / 2.5
        tx = u * R * 0.55
        ty = R * 0.9 + drop * (1 - 0.3 * abs(u)) - sm * R * 0.14 * (1 - u * u) + sm * R * 0.05
        ctx.save()
        ctx.translate(tx, ty)
        ctx.rotate(u * 0.25)
        pts = np.array([[-R * 0.08, 0], [R * 0.08, 0], [R * 0.075, R * 0.3], [-R * 0.075, R * 0.3]])
        spline(ctx, wob(pts, 80 + i, t, 1.2))
        fill_ink(ctx, (0.62, 0.74, 0.45), lw * 0.85)
        ctx.restore()
    brow(ctx, R, S, lw, 9, t, col=(0.13, 0.2, 0.1), width=0.11, rise=1.18)
    ctx.restore()


def cloud_shape(a, b, boxy, bumps, phase, t):
    pts = []
    n = 40
    for i in range(n):
        th = i / n * TAU
        c, s = math.cos(th), math.sin(th)
        e = 2 / boxy
        x = a * math.copysign(abs(c) ** e, c)
        y = b * math.copysign(abs(s) ** e, s)
        if s < 0.25:
            k = 1 + 0.16 * abs(math.sin(bumps * th / 2 + phase)) ** 0.7
        else:
            k = 0.98
        pts.append((x * k, y * (k if s < 0.25 else 0.88)))
    return np.array(pts)


def draw_cloud(ctx, S, t, kind, night):
    x, y = S['x'], S['y']
    br = math.sin(t * 1.2 + (0 if kind == 'CLAWD' else 2))
    talk = S.get('talk', 0)
    ctx.save()
    ctx.translate(x, y + math.sin(t * 0.6 + (1 if kind == 'CLAWD' else 0)) * 6)
    ctx.scale(1 + 0.015 * br + 0.02 * talk, 1 - 0.012 * br + 0.02 * talk)
    if kind == 'CLAWD':
        a, b, boxy, bumps, R, rx, col = 185, 118, 3.2, 7, 60, 1.0, (0.6, 0.58, 0.72)
    else:
        a, b, boxy, bumps, R, rx, col = 160, 108, 2.0, 9, 52, 0.84, (0.78, 0.72, 0.9)
    col = mix(col, (0.34, 0.33, 0.45), S['dark'])
    pts = wob(cloud_shape(a, b, boxy, bumps, 0.6, t), 100 if kind == 'CLAWD' else 101, t, 1.6)
    spline(ctx, pts)
    g = cairo.LinearGradient(0, -b * 1.2, 0, b)
    g.add_color_stop_rgb(0, *mix(col, (1, 0.95, 0.85), 0.25))
    g.add_color_stop_rgb(1, *mix(col, (0.1, 0.08, 0.2), 0.3))
    ctx.set_source(g)
    ctx.fill_preserve()
    ink(ctx, 6)
    # inner fluff line
    ctx.move_to(-a * 0.55, b * 0.55)
    ctx.curve_to(-a * 0.3, b * 0.75, a * 0.1, b * 0.5, a * 0.3, b * 0.68)
    ink(ctx, 4, 0.35)
    ctx.save()
    ctx.translate(0, -10)
    eyeball(ctx, R, S, 5, 110 if kind == 'CLAWD' else 111, t,
            iris=(0.45, 0.55, 0.85) if kind == 'CLAWD' else (0.8, 0.45, 0.75),
            lidc=mix(col, (1, 1, 1), 0.15), ring=True, rx=rx, pupil_oval=1.5, lashes=(kind == 'CLAWDIA'))
    brow(ctx, R, S, 5, 112, t, width=0.17)
    ctx.restore()
    ctx.save()
    ctx.translate(0, R * 1.05 + 10)
    mouth(ctx, 62, S, 5, 113, t)
    ctx.restore()
    ctx.restore()


def draw_rain(ctx, S, t, kind):
    amt = S['rain']
    if amt < 0.02:
        return
    x, y = S['x'], S['y']
    rr = np.random.default_rng(55)
    n = int(40 * amt)
    for i in range(n):
        ox = rr.uniform(-130, 130)
        ph = rr.uniform(0, 1)
        sp = rr.uniform(0.7, 1.1)
        u = (t * sp * 1.4 + ph) % 1.0
        yy = y + 70 + u * 900
        ctx.move_to(x + ox - u * 20, yy)
        ctx.line_to(x + ox - u * 20 - 3, yy + 26)
        ink(ctx, 3.5, 0.6 * amt * (1 - u), (0.7, 0.85, 1.0))


def draw_bee(ctx, S, t, f):
    x, y = S['x'], S['y']
    face = S['face']
    talk = S.get('talk', 0)
    ctx.save()
    ctx.translate(x + math.sin(t * 7) * 3, y + math.sin(t * 9.3) * 5)
    ctx.scale(-face, 1)
    ctx.scale(0.9, 0.9)
    # wings (flap on alternate frames)
    wa = [-0.55, 0.15, -0.2][f % 3]
    for i, (wx, wy) in enumerate(((20, -58), (44, -52))):
        ctx.save()
        ctx.translate(wx, wy)
        ctx.rotate(wa + i * 0.25)
        ctx.scale(1, 0.48)
        ctx.arc(10, -40, 42, 0, TAU)
        ctx.restore()
        ctx.set_source_rgba(0.85, 0.95, 1.0, 0.45)
        ctx.fill_preserve()
        ink(ctx, 3.5, 0.8)
    # antennae (the drawing's two tall loops)
    an = S['antenna']
    for i, bx in enumerate((-32, -6)):
        ctx.save()
        ctx.translate(bx, -52)
        jig = math.sin(t * 16 + i) * 0.06 * an
        ctx.rotate(-0.15 + i * 0.2 + (1 - an) * (0.9 + i * 0.2) + jig)
        pts = np.array([[-8, 0], [-11, -45], [-6, -78], [4, -80], [9, -45], [8, 0]])
        spline(ctx, wob(pts, 120 + i, t, 1.0), closed=False)
        ink(ctx, 5)
        ctx.restore()
    # stinger
    ctx.move_to(70, -14)
    ctx.line_to(128, -36)
    ctx.line_to(72, 10)
    ctx.close_path()
    fill_ink(ctx, (0.95, 0.8, 0.45), 5)
    # body
    body = wob(circle_pts(1, 22) * np.array([80, 64]), 125, t, 1.3)
    spline(ctx, body)
    g = cairo.RadialGradient(-20, -25, 10, 0, 0, 90)
    g.add_color_stop_rgb(0, 1.0, 0.92, 0.45)
    g.add_color_stop_rgb(1, 0.92, 0.66, 0.1)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    for sx in (38, 62):
        ctx.move_to(sx, -70)
        ctx.curve_to(sx - 12, -20, sx - 12, 20, sx, 70)
        ink(ctx, 13, 0.85, (0.35, 0.2, 0.08))
    ctx.restore()
    ink(ctx, 5.5)
    # legs
    for lx in (-20, 10):
        ctx.move_to(lx, 60)
        ctx.line_to(lx + math.sin(t * 5 + lx) * 5, 82)
        ink(ctx, 4)
    ctx.save()
    ctx.translate(-16, -8)
    eyeball(ctx, 34, S, 4, 126, t, iris=(0.45, 0.3, 0.15), lidc=(0.98, 0.82, 0.3), ring=True, pupil_oval=1.4)
    brow(ctx, 34, S, 4, 127, t, width=0.2, rise=1.38)
    ctx.restore()
    ctx.save()
    ctx.translate(-16, 40)
    mouth(ctx, 30, S, 3.5, 128, t)
    ctx.restore()
    ctx.restore()


def draw_goste(ctx, S, t, f):
    x, y = S['x'], S['y']
    al = S['alpha']
    trem = S['tremble']
    talk = S.get('talk', 0)
    jx = (math.sin(f * 2.7) * 2.2 + math.sin(f * 1.3) * 1.2) * trem
    bob = math.sin(t * 2.0) * 7
    ctx.save()
    ctx.translate(x + jx, y + bob)
    sq = 1 + 0.03 * talk
    ctx.scale(1 / sq ** 0.5, sq)
    # glow
    g = cairo.RadialGradient(0, 0, 30, 0, 0, 210)
    g.add_color_stop_rgba(0, 0.6, 0.9, 1.0, 0.32 * al)
    g.add_color_stop_rgba(1, 0.6, 0.9, 1.0, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 210, 0, TAU)
    ctx.fill()
    ctx.push_group()
    # arms (behind body edge)
    for side, key in ((-1, 'armL'), (1, 'armR')):
        a = S[key]
        wv = math.sin(t * 9) * 0.45 * S['wave'] if side == 1 else 0
        ctx.save()
        ctx.translate(side * 72, 25 - a * 30)
        ctx.rotate(side * (0.5 - a * 1.9) + wv * side)
        ctx.scale(1, 0.62)
        ctx.arc(side * 16, 0, 20, 0, TAU)
        ctx.restore()
        fill_ink(ctx, (0.95, 0.97, 1.0), 5)
    # body
    pts = []
    for i in range(10):
        a = math.pi + i / 9 * math.pi
        pts.append((math.cos(a) * 80, -28 + math.sin(a) * 82))
    pts.append((82, 40))
    for i in range(9):
        u = i / 8
        xx = 80 - u * 160
        yy = 100 + 14 * abs(math.sin(u * math.pi * 2.0 + t * 2.4)) - 8 * math.sin(u * math.pi * 4 + t * 3)
        pts.append((xx, yy))
    pts.append((-82, 40))
    body = wob(np.array(pts), 140, t, 1.3)
    spline(ctx, body)
    g = cairo.LinearGradient(0, -110, 0, 110)
    g.add_color_stop_rgb(0, 1.0, 1.0, 1.0)
    g.add_color_stop_rgb(1, 0.82, 0.88, 0.98)
    ctx.set_source(g)
    ctx.fill_preserve()
    ink(ctx, 5.5)
    # blush
    if S['blush'] > 0.01:
        for sx in (-1, 1):
            ctx.save()
            ctx.translate(sx * 50, 2)
            ctx.scale(1, 0.55)
            ctx.arc(0, 0, 16, 0, TAU)
            ctx.restore()
            ctx.set_source_rgba(1, 0.55, 0.6, 0.5 * S['blush'])
            ctx.fill()
    # eyes: black ovals like the drawing
    lid = max(S['lid'], S.get('blink', 0))
    blid = S['blid'] * (1 - S.get('blink', 0))
    lx, ly = S['lookv']
    tear = S['tear']
    for sx in (-1, 1):
        ex, ey = sx * 27 + lx * 7, -36 + ly * 6
        ry = 22 * (0.85 + 0.25 * S['pupil'] * 0.5 + 0.1 * S['brow'])
        ctx.save()
        ctx.translate(ex, ey)
        ctx.save()
        ctx.scale(1, ry / 11.5)
        ctx.arc(0, 0, 11.5, 0, TAU)
        ctx.restore()
        ctx.set_source_rgb(*INK)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        hr = 4 + 3 * tear
        ctx.arc(-3, -ry * 0.45, hr, 0, TAU)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill()
        ctx.arc(3, ry * 0.3, hr * 0.5, 0, TAU)
        ctx.fill()
        if lid > 0.01:
            yy = -ry + 2.1 * ry * lid
            ctx.rectangle(-20, -ry - 5, 40, yy + ry + 5)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        if blid > 0.01:
            yy = ry - 1.2 * ry * blid
            ctx.move_to(-20, ry + 5)
            ctx.line_to(-20, yy + 4)
            ctx.curve_to(-6, yy - 6, 6, yy - 6, 20, yy + 4)
            ctx.line_to(20, ry + 5)
            ctx.close_path()
            ctx.set_source_rgb(0.97, 0.98, 1)
            ctx.fill()
        ctx.restore()
        if lid > 0.01:
            yy = -ry + 2.1 * ry * lid
            ctx.move_to(-13, yy)
            ctx.line_to(13, yy)
            ink(ctx, 4)
        if tear > 0.45:
            u = (t * 0.5 + (0.3 if sx > 0 else 0)) % 1.0
            ty = ry + 4 + u * 50
            ctx.move_to(sx * 4, ty - 8)
            ctx.curve_to(sx * 4 + 6, ty, sx * 4 + 6, ty + 6, sx * 4, ty + 6)
            ctx.curve_to(sx * 4 - 6, ty + 6, sx * 4 - 6, ty, sx * 4, ty - 8)
            ctx.set_source_rgba(0.55, 0.8, 1.0, (tear - 0.45) * 1.8 * (1 - u))
            ctx.fill()
        ctx.restore()
        # thin brows for two-eyed face
        ar = S['arch']
        yb = -72 - S['brow'] * 10 + S['lid'] * 5
        outer, inner = sx * 42, sx * 14
        ctx.move_to(outer, yb + ar * 7)
        ctx.curve_to(sx * 32, yb - 3, sx * 22, yb - 3, inner, yb - ar * 8)
        ink(ctx, 4.5, 0.75)
    ctx.save()
    ctx.translate(0, 26)
    mouth(ctx, 56, S, 5, 141, t, oness=S['oness'], inner=INK)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(al)
    ctx.restore()


# ------------------------------------------------------------------ world
_rng = np.random.default_rng(3)
STARS = [(_rng.uniform(0, W), _rng.uniform(0, 1300), _rng.uniform(1, 3.2), _rng.uniform(0, TAU)) for _ in range(110)]


def tree_branches():
    out = []
    rr = np.random.default_rng(9)

    def br(x, y, a, L, w, d):
        x2, y2 = x + math.cos(a) * L, y + math.sin(a) * L
        out.append((x, y, x2, y2, w))
        if d < 5:
            for k in (-1, 1):
                br(x2, y2, a + k * rr.uniform(0.3, 0.7), L * rr.uniform(0.6, 0.78), w * 0.65, d + 1)
    br(110, 1420, -math.pi / 2 - 0.05, 250, 30, 0)
    return out


TREE = tree_branches()


def sky_colors(dawn):
    top = mix((0.05, 0.03, 0.13), (0.35, 0.45, 0.72), dawn)
    mid = mix((0.16, 0.08, 0.27), (0.95, 0.62, 0.55), dawn)
    hor = mix((0.32, 0.15, 0.32), (1.0, 0.82, 0.55), dawn)
    return top, mid, hor


def layer(ctx, cam, d):
    cx, cy, z = cam
    zd = 1 + (z - 1) * d
    ccx = W / 2 + (cx - W / 2) * d
    ccy = H / 2 + (cy - H / 2) * d
    ctx.identity_matrix()
    ctx.translate(W / 2, H / 2)
    ctx.scale(zd, zd)
    ctx.translate(-ccx, -ccy)


def draw_pumpkin(ctx, x, y, rx, ry, t, seed, one_eye):
    fl = 0.8 + 0.2 * math.sin(t * 13 + seed) * math.sin(t * 7.3 + seed * 2)
    g = cairo.RadialGradient(x, y, 10, x, y, rx * 2.6)
    g.add_color_stop_rgba(0, 1, 0.6, 0.15, 0.35 * fl)
    g.add_color_stop_rgba(1, 1, 0.5, 0.1, 0)
    ctx.set_source(g)
    ctx.arc(x, y, rx * 2.6, 0, TAU)
    ctx.fill()
    for k, (ox, sc) in enumerate(((-0.55, 0.62), (0.55, 0.62), (-0.25, 0.75), (0.25, 0.75), (0, 0.6))):
        pts = wob(circle_pts(1, 16) * np.array([rx * sc, ry]) + np.array([x + ox * rx, y]), seed + k, t, 1.2)
        spline(ctx, pts)
        g = cairo.LinearGradient(x, y - ry, x, y + ry)
        g.add_color_stop_rgb(0, 1.0, 0.6, 0.18)
        g.add_color_stop_rgb(1, 0.72, 0.3, 0.05)
        ctx.set_source(g)
        ctx.fill_preserve()
        ink(ctx, 5)
    ctx.move_to(x - 6, y - ry + 6)
    ctx.curve_to(x - 4, y - ry - 20, x + 6, y - ry - 30, x + 16, y - ry - 34)
    ink(ctx, 12, 1, (0.25, 0.35, 0.15))
    glow = mix((1, 0.55, 0.1), (1, 0.95, 0.55), fl)
    ctx.set_source_rgb(*glow)
    if one_eye:
        ctx.arc(x, y - ry * 0.25, rx * 0.26, 0, TAU)
        ctx.fill()
        ctx.arc(x + rx * 0.05, y - ry * 0.22, rx * 0.1, 0, TAU)
        ctx.set_source_rgb(0.35, 0.12, 0.02)
        ctx.fill()
        ctx.set_source_rgb(*glow)
    else:
        for sx in (-1, 1):
            ctx.move_to(x + sx * rx * 0.42, y - ry * 0.1)
            ctx.line_to(x + sx * rx * 0.22, y - ry * 0.45)
            ctx.line_to(x + sx * rx * 0.08, y - ry * 0.1)
            ctx.close_path()
            ctx.fill()
    ctx.move_to(x - rx * 0.5, y + ry * 0.2)
    for i in range(7):
        u = i / 6
        ctx.line_to(x - rx * 0.5 + u * rx, y + ry * (0.32 + (0.16 if i % 2 else 0)))
    ctx.curve_to(x + rx * 0.3, y + ry * 0.7, x - rx * 0.3, y + ry * 0.7, x - rx * 0.5, y + ry * 0.2)
    ctx.fill()


def draw_world(ctx, st):
    t, f = st['t'], st['f']
    P = st['P']
    Wd = P['WORLD']
    dawn = Wd['dawn']
    cam = st['cam']
    night = mix((0.2, 0.15, 0.35), (1, 0.85, 0.75), dawn)
    top, mid, hor = sky_colors(dawn)
    ctx.identity_matrix()
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(0.5, *mid)
    g.add_color_stop_rgb(0.8, *hor)
    ctx.set_source(g)
    ctx.paint()
    # stars
    layer(ctx, cam, 0.12)
    for (sx, sy, r, ph) in STARS:
        a = (0.45 + 0.55 * math.sin(t * 2 + ph) ** 2) * (1 - dawn)
        ctx.arc(sx, sy, r, 0, TAU)
        ctx.set_source_rgba(1, 0.97, 0.85, a)
        ctx.fill()
    # moon with a sleepy eye
    layer(ctx, cam, 0.3)
    mx, my = POS['MOON']
    g = cairo.RadialGradient(mx, my, 60, mx, my, 330)
    g.add_color_stop_rgba(0, 1, 0.85, 0.55, 0.45 * (1 - dawn * 0.7))
    g.add_color_stop_rgba(1, 1, 0.8, 0.5, 0)
    ctx.set_source(g)
    ctx.arc(mx, my, 330, 0, TAU)
    ctx.fill()
    ctx.arc(mx, my, 118, 0, TAU)
    ctx.set_source_rgb(*mix((1.0, 0.86, 0.55), (1, 0.97, 0.9), dawn))
    ctx.fill_preserve()
    ink(ctx, 5, 0.6)
    for (cx_, cy_, r_) in ((-40, -35, 20), (35, 40, 14), (50, -50, 10), (-30, 55, 9)):
        ctx.arc(mx + cx_, my + cy_, r_, 0, TAU)
        ctx.set_source_rgba(0.85, 0.65, 0.35, 0.35)
        ctx.fill()
    me = Wd['mooneye']
    if me < 0.05:
        ctx.move_to(mx - 34, my + 5)
        ctx.curve_to(mx - 15, my + 22, mx + 15, my + 22, mx + 34, my + 5)
        ink(ctx, 5, 0.75)
    else:
        ctx.save()
        ctx.translate(mx, my + 5)
        S = dict(lid=1 - me * 0.75, blid=0.15, lookv=(0.2, 0.8), pupil=1.1, tear=0, blink=0)
        eyeball(ctx, 32 * (0.6 + 0.4 * me), S, 4, 7, t, iris=(0.95, 0.6, 0.2), lidc=(1.0, 0.86, 0.55))
        ctx.restore()
    # bats
    for (t0, y0, dirn) in ((10.5, 520, 1), (52, 640, -1), (98, 470, 1), (146, 560, -1)):
        u = (t - t0) / 7.0
        if 0 <= u <= 1:
            bx = -100 + u * (W + 200) if dirn > 0 else W + 100 - u * (W + 200)
            by = y0 + math.sin(u * 9) * 40
            fl = math.sin(t * 22)
            ctx.save()
            ctx.translate(bx, by)
            ctx.scale(dirn, 1)
            ctx.move_to(-40, -10 * fl)
            ctx.curve_to(-25, -20 * fl - 5, -12, 0, 0, 2)
            ctx.curve_to(12, 0, 25, -20 * fl - 5, 40, -10 * fl)
            ctx.curve_to(25, 8, 10, 6, 0, 12)
            ctx.curve_to(-10, 6, -25, 8, -40, -10 * fl)
            ctx.set_source_rgba(0.06, 0.04, 0.1, 0.9 * (1 - dawn))
            ctx.fill()
            ctx.restore()
    # clouds (with rain)
    layer(ctx, cam, 1.0)
    for ch in ('CLAWD', 'CLAWDIA'):
        draw_rain(ctx, P[ch], t, ch)
        draw_cloud(ctx, P[ch], t, ch, night)
    # distant hills
    layer(ctx, cam, 0.55)
    ctx.move_to(-400, 1350)
    for i in range(12):
        xx = -400 + i * 170
        ctx.line_to(xx, 1290 + 60 * math.sin(i * 1.7))
    ctx.line_to(1600, 1350)
    ctx.line_to(1600, 2600)
    ctx.line_to(-400, 2600)
    ctx.close_path()
    ctx.set_source_rgb(*mix((0.11, 0.07, 0.2), (0.45, 0.42, 0.55), dawn))
    ctx.fill()
    # tree + house
    layer(ctx, cam, 0.85)
    sil = mix((0.07, 0.04, 0.12), (0.3, 0.25, 0.35), dawn)
    for (x1, y1, x2, y2, w) in TREE:
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ink(ctx, w, 1, sil)
    layer(ctx, cam, 1.0)
    hx0, hx1, hy0 = 790, 1090, 820
    ctx.move_to(hx0 - 30, hy0)
    ctx.line_to(940, 650)
    ctx.line_to(hx1 + 40, hy0)
    ctx.line_to(hx1, hy0)
    ctx.line_to(hx1, 1500)
    ctx.line_to(hx0, 1500)
    ctx.line_to(hx0, hy0)
    ctx.close_path()
    ctx.set_source_rgb(*sil)
    ctx.fill_preserve()
    ink(ctx, 5, 0.8)
    ctx.rectangle(1010, 680, 40, 90)
    ctx.set_source_rgb(*sil)
    ctx.fill()
    wx, wy = POS['WINDOW']
    wl = Wd['window']
    g = cairo.RadialGradient(wx, wy, 20, wx, wy, 260)
    g.add_color_stop_rgba(0, 1, 0.8, 0.4, 0.35 * wl)
    g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
    ctx.set_source(g)
    ctx.arc(wx, wy, 260, 0, TAU)
    ctx.fill()
    ctx.rectangle(wx - 62, wy - 72, 124, 144)
    g = cairo.LinearGradient(0, wy - 72, 0, wy + 72)
    g.add_color_stop_rgb(0, *mix((0.2, 0.12, 0.1), (1.0, 0.86, 0.5), clamp(wl)))
    g.add_color_stop_rgb(1, *mix((0.15, 0.08, 0.08), (1.0, 0.65, 0.3), clamp(wl)))
    ctx.set_source(g)
    ctx.fill()
    # child silhouette
    ch_a = Wd['child']
    if ch_a > 0.01:
        ctx.save()
        ctx.rectangle(wx - 62, wy - 72, 124, 144)
        ctx.clip()
        sc = (0.18, 0.1, 0.12, ch_a)
        ctx.set_source_rgba(*sc)
        ctx.arc(wx - 8, wy + 5 - 6 * ch_a, 22, 0, TAU)
        ctx.fill()
        ctx.save()
        ctx.translate(wx - 8, wy + 75)
        ctx.scale(1, 0.7)
        ctx.arc(0, 0, 50, 0, TAU)
        ctx.restore()
        ctx.fill()
        cw = Wd['childwave']
        if cw > 0.01:
            ang = -1.9 + math.sin(t * 7) * 0.35 * cw
            ctx.move_to(wx + 22, wy + 50)
            ex = wx + 22 + math.cos(ang) * 60 * cw
            ey = wy + 50 + math.sin(ang) * 60 * cw
            ctx.line_to(ex, ey)
            ink(ctx, 13, ch_a, sc[:3])
            ctx.arc(ex, ey, 10, 0, TAU)
            ctx.fill()
        ctx.restore()
    # curtains + frame
    for sx in (-1, 1):
        ctx.move_to(wx + sx * 62, wy - 72)
        ctx.line_to(wx + sx * 22, wy - 72)
        ctx.curve_to(wx + sx * 40, wy - 10, wx + sx * 55, wy + 30, wx + sx * 62, wy + 72)
        ctx.close_path()
        ctx.set_source_rgba(0.45, 0.12, 0.15, 0.9)
        ctx.fill()
    ctx.rectangle(wx - 62, wy - 72, 124, 144)
    ink(ctx, 7)
    ctx.move_to(wx, wy - 72); ctx.line_to(wx, wy + 72)
    ctx.move_to(wx - 62, wy); ctx.line_to(wx + 62, wy)
    ink(ctx, 5, 0.6)
    # ground
    ctx.move_to(-300, 1480)
    for i in range(14):
        xx = -300 + i * 130
        ctx.line_to(xx, 1470 + 28 * math.sin(i * 1.3 + 0.5))
    ctx.line_to(1500, 1480)
    ctx.line_to(1500, 2700)
    ctx.line_to(-300, 2700)
    ctx.close_path()
    g = cairo.LinearGradient(0, 1450, 0, 2000)
    g.add_color_stop_rgb(0, *mix((0.13, 0.17, 0.16), (0.35, 0.45, 0.3), dawn))
    g.add_color_stop_rgb(1, *mix((0.05, 0.06, 0.08), (0.2, 0.25, 0.18), dawn))
    ctx.set_source(g)
    ctx.fill_preserve()
    ink(ctx, 5, 0.7)
    rr = np.random.default_rng(4)
    for i in range(40):
        gx = rr.uniform(-100, 1180)
        gy = rr.uniform(1490, 1950)
        sw = math.sin(t * 1.5 + gx * 0.01) * 4
        for k in (-1, 0, 1):
            ctx.move_to(gx + k * 7, gy)
            ctx.line_to(gx + k * 12 + sw, gy - 26 - abs(k) * -6)
        ink(ctx, 3.5, 0.55, (0.05, 0.08, 0.06))
    # Iris
    draw_iris(ctx, P['IRIS'], t, night)
    # Goste then the pumpkin he hides behind
    draw_goste(ctx, P['GOSTE'], t, f)
    draw_pumpkin(ctx, 215, 1560, 105, 82, t, 200, False)
    draw_pumpkin(ctx, 905, 1640, 88, 70, t, 210, True)
    draw_bee(ctx, P['BEE'], t, f)
    # front fog
    layer(ctx, cam, 1.15)
    for i in range(4):
        fx = ((t * (14 + i * 5) + i * 400) % 1800) - 400
        fy = 1520 + i * 90
        g = cairo.RadialGradient(fx, fy, 20, fx, fy, 420)
        g.add_color_stop_rgba(0, 0.8, 0.75, 0.95, 0.11 * (1 - dawn * 0.6))
        g.add_color_stop_rgba(1, 0.8, 0.75, 0.95, 0)
        ctx.set_source(g)
        ctx.save()
        ctx.translate(fx, fy)
        ctx.scale(1, 0.35)
        ctx.translate(-fx, -fy)
        ctx.arc(fx, fy, 420, 0, TAU)
        ctx.fill()
        ctx.restore()


# ------------------------------------------------------------------ photo
PHOTO = None
PHOTO_BG = None
PAPER = {}
PEYES = {  # (x, y, ring_r, pupil_rx, pupil_ry, inner_r)
    'flower': (741, 1028, 74, 22, 22, 42),
    'lcloud': (260, 242, 64, 10, 18, 50),
    'rcloud': (918, 150, 46, 8, 14, 34),
    'bee': (603, 409, 32, 7, 12, 22),
}
GHOST_EYES = [(268, 551), (320, 550)]
GHOST_MOUTH = (293, 655)
PBASE = W / 1502


def load_photo():
    global PHOTO, PHOTO_BG
    if PHOTO is None:
        from PIL import Image, ImageFilter, ImageEnhance
        PHOTO = cairo.ImageSurface.create_from_png(os.path.join(HERE, '..', 'photo.png'))
        im = Image.open(os.path.join(HERE, '..', 'photo.png')).convert('RGB')
        bg = im.resize((int(1502 * 1920 / 2000), 1920)).crop((0, 0, W, 1920))
        bg = bg.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.38)
        bg = Image.blend(bg, Image.new('RGB', bg.size, (60, 25, 70)), 0.35)
        p = os.path.join(HERE, 'photo_bg.png')
        bg.save(p)
        PHOTO_BG = cairo.ImageSurface.create_from_png(p)
        arr = np.asarray(im).astype(float) / 255
        for k, (x, y, r, *_rest) in list(PEYES.items()) + [('ghost', (293, 600, 60))]:
            patch = arr[y - r - 25:y + r + 25, x - r - 25:x + r + 25].reshape(-1, 3)
            lum = patch.mean(1)
            PAPER[k] = tuple(np.median(patch[lum > np.percentile(lum, 60)], 0))


def draw_photo(ctx, st):
    load_photo()
    P = st['P']['PHOTO']
    t = st['t']
    ctx.identity_matrix()
    ctx.set_source_surface(PHOTO_BG, 0, 0)
    ctx.paint()
    z = P['zoom']
    ctx.translate(W / 2, H / 2)
    ctx.scale(PBASE * z, PBASE * z)
    ctx.translate(-P['cx'], -P['cy'])
    # soft shadow
    ctx.rectangle(10, 14, 1502, 2000)
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.fill()
    ctx.set_source_surface(PHOTO, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    blink = P['blink']
    fl = P['flook']
    for k, (x, y, r, prx, pry, rin) in PEYES.items():
        paper = PAPER[k]
        lid = max(blink if k in ('flower', 'bee') or int(t / 3.7) % 2 == 0 else 0, P['wink'] if k == 'flower' else 0)
        look = fl if k == 'flower' else (fl[0] * 0.8, fl[1] * 0.8)
        if abs(look[0]) + abs(look[1]) > 0.01:
            ctx.save()
            ctx.translate(x, y)
            ctx.save(); ctx.scale(1, pry / prx); ctx.arc(0, 0, prx + 4, 0, TAU); ctx.restore()
            ctx.set_source_rgb(*paper)
            ctx.fill()
            ctx.save()
            ctx.arc(0, 0, rin * 0.92, 0, TAU)
            ctx.clip()
            ctx.translate(look[0] * rin * 0.45, look[1] * rin * 0.35)
            ctx.scale(1, pry / prx)
            ctx.arc(0, 0, prx, 0, TAU)
            ctx.set_source_rgb(0.12, 0.12, 0.13)
            ctx.fill()
            ctx.restore()
            ctx.restore()
        if lid > 0.02:
            ctx.save()
            ctx.translate(x, y)
            rr_ = r + 3
            ctx.arc(0, 0, rr_, 0, TAU)
            ctx.clip()
            ye = -rr_ + 2 * rr_ * lid
            ctx.move_to(-rr_, -rr_)
            ctx.line_to(-rr_, ye)
            ctx.curve_to(-rr_ * 0.4, ye + rr_ * 0.25, rr_ * 0.4, ye + rr_ * 0.25, rr_, ye)
            ctx.line_to(rr_, -rr_)
            ctx.close_path()
            ctx.set_source_rgb(*paper)
            ctx.fill()
            ctx.move_to(-rr_, ye)
            ctx.curve_to(-rr_ * 0.4, ye + rr_ * 0.25, rr_ * 0.4, ye + rr_ * 0.25, rr_, ye)
            ink(ctx, 6, 0.95, (0.15, 0.15, 0.17))
            ctx.restore()
    # ghost: glance + finally smiles
    gl = P['ghostlook']
    gp = PAPER['ghost']
    if abs(gl[0]) + abs(gl[1]) > 0.01 or blink > 0.3:
        for (x, y) in GHOST_EYES:
            ctx.save(); ctx.translate(x, y); ctx.scale(1, 2.0); ctx.arc(0, 0, 13, 0, TAU); ctx.restore()
            ctx.set_source_rgb(*gp)
            ctx.fill()
            ctx.save(); ctx.translate(x + gl[0] * 6, y + gl[1] * 6)
            sy = 1.8 * (1 - 0.9 * (blink if blink > 0.3 else 0))
            ctx.scale(1, max(sy, 0.12)); ctx.arc(0, 0, 9.5, 0, TAU); ctx.restore()
            ctx.set_source_rgb(0.12, 0.12, 0.13)
            ctx.fill()
    gs = P['ghostsmile']
    if gs > 0.01:
        x, y = GHOST_MOUTH
        ctx.save(); ctx.translate(x, y); ctx.scale(1, 1.75); ctx.arc(0, 0, 19, 0, TAU); ctx.restore()
        ctx.set_source_rgba(*gp, clamp(gs * 1.6))
        ctx.fill()
        k = clamp(gs * 1.3 - 0.3)
        hh = 24 * (1 - k)
        ctx.save()
        ctx.translate(x, y - 6)
        ctx.move_to(-22, 0)
        ctx.curve_to(-12, 14 + hh * 0.2, 12, 14 + hh * 0.2, 22, 0)
        if hh > 2:
            ctx.curve_to(12, -hh, -12, -hh, -22, 0)
            ctx.set_source_rgba(0.12, 0.12, 0.13, gs)
            ctx.fill()
        else:
            ink(ctx, 7, gs, (0.12, 0.12, 0.13))
        ctx.restore()
        for sx in (-1, 1):
            ctx.arc(x + sx * 44, y - 30, 11, 0, TAU)
            ctx.set_source_rgba(1, 0.5, 0.55, 0.35 * k)
            ctx.fill()


# ------------------------------------------------------------------ overlays
def text_path(ctx, txt, font, size, x, y, align=0.5):
    ctx.select_font_face(font)
    ctx.set_font_size(size)
    xb, yb, tw, th, xa, ya = ctx.text_extents(txt)
    ctx.move_to(x - tw * align - xb, y)
    ctx.text_path(txt)
    return tw


def wrap(ctx, txt, font, size, maxw):
    ctx.select_font_face(font)
    ctx.set_font_size(size)
    words = txt.split()
    lines, cur = [], ''
    for w in words:
        tst = (cur + ' ' + w).strip()
        if ctx.text_extents(tst)[4] > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = tst
    if cur:
        lines.append(cur)
    return lines


def draw_subs(ctx, st):
    sub = st['sub']
    if not sub:
        return
    sp, txt, a = sub
    if a <= 0:
        return
    ctx.identity_matrix()
    font, size = 'Patrick Hand', 62
    lines = wrap(ctx, txt, font, size, 900)
    lh = 70
    y0 = 1560 - (len(lines) - 1) * lh / 2
    bw = max(ctx.text_extents(l)[4] for l in lines) + 70
    bh = len(lines) * lh + 34
    bx, by = W / 2 - bw / 2, y0 - lh * 0.78 - 8
    r = 26
    ctx.new_path()
    ctx.arc(bx + bw - r, by + r, r, -math.pi / 2, 0)
    ctx.arc(bx + bw - r, by + bh - r, r, 0, math.pi / 2)
    ctx.arc(bx + r, by + bh - r, r, math.pi / 2, math.pi)
    ctx.arc(bx + r, by + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
    ctx.set_source_rgba(0.04, 0.02, 0.08, 0.74 * a)
    ctx.fill()
    col = SUBCOL.get(sp, (1, 1, 1))
    if sp in NAMES:
        text_path(ctx, NAMES[sp], 'Patrick Hand', 42, bx + 30, by - 10, 0)
        ctx.set_source_rgba(0.04, 0.02, 0.08, 0.8 * a)
        ctx.set_line_width(6)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*col, a)
        ctx.fill()
    for i, l in enumerate(lines):
        text_path(ctx, l, font, size, W / 2, y0 + i * lh)
        ctx.set_source_rgba(0.03, 0.01, 0.06, 0.9 * a)
        ctx.set_line_width(7)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*col, a)
        ctx.fill()


def draw_titles(ctx, st):
    Wd = st['P']['WORLD']
    ctx.identity_matrix()
    for key, lines, y0, size in (('title', ['THE ONES', 'WHO WATCH'], 250, 120),
                                 ('endtitle', ['Happy', 'Halloween'], 120, 108)):
        a = Wd[key]
        if a < 0.01:
            continue
        if key == 'endtitle' and st['scene'] != 'photo':
            continue
        for i, l in enumerate(lines):
            y = y0 + i * size * 0.95 + (1 - a) * 30
            text_path(ctx, l, 'Creepster', size, W / 2, y)
            ctx.set_source_rgba(0.05, 0.0, 0.08, 0.9 * a)
            ctx.set_line_width(14)
            ctx.stroke_preserve()
            g = cairo.LinearGradient(0, y - size, 0, y)
            g.add_color_stop_rgba(0, 1, 0.78, 0.2, a)
            g.add_color_stop_rgba(1, 1, 0.42, 0.05, a)
            ctx.set_source(g)
            ctx.fill()


def vignette(ctx, strength=0.55):
    ctx.identity_matrix()
    g = cairo.RadialGradient(W / 2, H * 0.45, H * 0.3, W / 2, H * 0.45, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.02, 0, 0.05, strength)
    ctx.set_source(g)
    ctx.paint()


def render(st, surf=None):
    if surf is None:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    pa = st['P']['PHOTO']['alpha']
    if st['scene'] == 'garden' or pa < 0.999:
        draw_world(ctx, st)
        vignette(ctx, 0.55 * (1 - st['P']['WORLD']['dawn'] * 0.6))
    if pa > 0.001:
        ctx.identity_matrix()
        ctx.push_group()
        draw_photo(ctx, st)
        ctx.identity_matrix()
        vignette(ctx, 0.35)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(pa)
    draw_titles(ctx, st)
    draw_subs(ctx, st)
    return surf
