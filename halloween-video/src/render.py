"""Cairo renderer v2: gothic stop-motion look (sculpted light, rim light, hatching, curls)."""
import math, os
import numpy as np
import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
TAU = math.tau
INK = (0.04, 0.04, 0.07)
from story import POS

MOON = (560, 330)
SUBCOL = {'N': (0.98, 0.9, 0.7), 'IRIS': (0.74, 0.95, 0.5), 'BEE': (1.0, 0.82, 0.32),
          'CLAWD': (0.7, 0.8, 1.0), 'CLAWDIA': (0.96, 0.75, 0.95), 'GOSTE': (0.8, 0.97, 1.0)}
NAMES = {'IRIS': 'IRIS', 'BEE': 'BEE-EYE', 'CLAWD': 'CLAWD', 'CLAWDIA': 'CLAWDIA', 'GOSTE': 'GOSTE'}


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def unit(x, y):
    n = math.hypot(x, y) + 1e-9
    return x / n, y / n


def light_at(x, y):
    """moonlight direction for an object at world (x, y)."""
    return unit(MOON[0] - x, MOON[1] - y - 200)


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


# ------------------------------------------------------------------ paths
def wob(pts, seed, t, amp=1.0):
    b = int(t * 6)  # puppet "boil" at 6 fps
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


def poly(ctx, pts, closed=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if closed:
        ctx.close_path()


def ink(ctx, lw, alpha=1.0, col=INK):
    ctx.set_source_rgba(*col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def set_src(ctx, src, alpha=1.0):
    if isinstance(src, cairo.Pattern):
        ctx.set_source(src)
    else:
        ctx.set_source_rgba(*src, alpha)


def circle_pts(r, n=18, rx=1.0):
    a = np.linspace(0, TAU, n, endpoint=False)
    return np.stack([np.cos(a) * r * rx, np.sin(a) * r], 1)


def spiral(cx, cy, r0, turns=1.6, a0=0.0, sign=1, n=26):
    pts = []
    for i in range(n):
        u = i / (n - 1)
        a = a0 + sign * u * turns * TAU
        r = r0 * (1 - u * 0.92)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return np.array(pts)


def taper(ctx, pts, w0, w1, col=INK, alpha=1.0):
    """filled tapered ribbon along a polyline."""
    pts = np.asarray(pts, float)
    tan = np.gradient(pts, axis=0)
    nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    w = np.linspace(w0, w1, len(pts))[:, None] / 2
    out = np.concatenate([pts + nrm * w, (pts - nrm * w)[::-1]])
    poly(ctx, out)
    ctx.set_source_rgba(*col, alpha)
    ctx.fill()


def hatch(ctx, sp, lw, alpha, ang=0.8, col=INK):
    x0, y0, x1, y1 = ctx.clip_extents()
    dx, dy = math.cos(ang), math.sin(ang)
    L = (x1 - x0) + (y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    n = int(L / sp) + 2
    for k in range(-n // 2, n // 2 + 1):
        ox, oy = cx - dy * k * sp, cy + dx * k * sp
        ctx.move_to(ox - dx * L, oy - dy * L)
        ctx.line_to(ox + dx * L, oy + dy * L)
    ctx.set_source_rgba(*col, alpha)
    ctx.set_line_width(lw)
    ctx.stroke()


def lit_shape(ctx, pathfn, base, shade, rim, L, size, cx=0.0, cy=0.0, lw=5, soff=0.16, roff=0.05,
              hatch_a=0.0, hatch_sp=9.0, rim_a=0.85, outline=True, heavy=1.8, ink_a=1.0):
    """sculpted fill: shadow crescent away from light, rim light toward it, heavier outline on the dark side."""
    Lx, Ly = L
    ctx.save()
    pathfn(ctx)
    ctx.clip()
    set_src(ctx, shade)
    ctx.paint()
    ctx.save()
    ctx.translate(Lx * soff * size, Ly * soff * size)
    pathfn(ctx)
    ctx.restore()
    set_src(ctx, base)
    ctx.fill()
    if hatch_a > 0:
        ctx.push_group()
        hatch(ctx, hatch_sp, max(1.0, lw * 0.28), hatch_a, ang=math.atan2(Ly, Lx) + 1.2)
        ctx.set_operator(cairo.OPERATOR_DEST_OUT)
        ctx.save()
        ctx.translate(Lx * soff * size * 0.55, Ly * soff * size * 0.55)
        pathfn(ctx)
        ctx.restore()
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint()
    if rim_a > 0:
        ctx.push_group()
        pathfn(ctx)
        ctx.set_source_rgba(*rim, rim_a)
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_DEST_OUT)
        ctx.save()
        ctx.translate(-Lx * roff * size, -Ly * roff * size)
        pathfn(ctx)
        ctx.restore()
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint()
    ctx.restore()
    if outline:
        pathfn(ctx)
        ink(ctx, lw, ink_a)
        if heavy:
            heavy_side(ctx, pathfn, L, size, cx, cy, lw * heavy, ink_a)


def heavy_side(ctx, pathfn, L, size, cx, cy, lw, alpha=1.0):
    Lx, Ly = L
    px, py = -Ly, Lx
    B = size * 4 + 200
    ctx.save()
    ctx.move_to(cx + px * B, cy + py * B)
    ctx.line_to(cx - px * B, cy - py * B)
    ctx.line_to(cx - px * B - Lx * B, cy - py * B - Ly * B)
    ctx.line_to(cx + px * B - Lx * B, cy + py * B - Ly * B)
    ctx.close_path()
    ctx.clip()
    pathfn(ctx)
    ink(ctx, lw, alpha)
    ctx.restore()


def radial_glow(ctx, x, y, r0, r1, col, a):
    g = cairo.RadialGradient(x, y, r0, x, y, r1)
    g.add_color_stop_rgba(0, *col, a)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r1, 0, TAU)
    ctx.fill()


# ------------------------------------------------------------------ face parts
def brow(ctx, R, S, lw, seed, t, col=INK, width=0.15, rise=1.32, spiky=0.0):
    yb = -R * rise - S['brow'] * R * 0.32 + S['lid'] * R * 0.14 - S.get('emph', 0) * R * 0.12
    ar, tb = S['arch'], S['tiltb']
    p = np.array([[-R * 0.84, yb + ar * R * 0.28 - tb * R * 0.2],
                  [0, yb - ar * R * 0.25],
                  [R * 0.84, yb + ar * R * 0.28 + tb * R * 0.2]])
    p = wob(p, seed, t, R * 0.01)
    c = 2 * p[1] - 0.5 * (p[0] + p[2])
    us = np.linspace(0, 1, 17)
    pts = np.array([(1 - u) ** 2 * p[0] + 2 * (1 - u) * u * c + u ** 2 * p[2] for u in us])
    tan = np.gradient(pts, axis=0)
    nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    wv = R * width * (0.12 + 0.88 * np.sin(np.pi * us) ** 0.8) / 2
    top = pts + nrm * wv[:, None]
    if spiky:
        top = top + nrm * (np.abs(np.sin(us * 9 * np.pi)) * R * spiky * 0.06)[:, None]
    outline = np.concatenate([top, (pts - nrm * wv[:, None])[::-1]])
    poly(ctx, outline)
    ctx.set_source_rgb(*col)
    ctx.fill_preserve()
    ink(ctx, max(1.0, R * 0.015), 1, col)


def socket(ctx, R, rx=1.0, a=0.5, col=(0.02, 0.02, 0.06)):
    ctx.save()
    ctx.scale(rx, 1)
    g = cairo.RadialGradient(0, R * 0.05, R * 0.9, 0, R * 0.05, R * 1.45)
    g.add_color_stop_rgba(0, *col, a)
    g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g)
    ctx.arc(0, R * 0.05, R * 1.45, 0, TAU)
    ctx.fill()
    ctx.restore()


def lid_y(R, lid):
    """upper-lid edge height; past half-closed it slows so a shut eye is a seam just below centre."""
    if lid <= 0.55:
        return -R + 2.05 * R * lid
    return 0.1275 * R + (lid - 0.55) / 0.45 * 0.12 * R


def eyeball(ctx, R, S, lw, seed, t, iris=(0.5, 0.8, 0.3), sclera=(0.93, 0.92, 0.86),
            lidc=(0.6, 0.55, 0.6), veins=0.0, rx=1.0, pupil_oval=1.0, lashes=False, L=(-0.5, -0.8),
            fibers=True, sock=0.5):
    lid = max(S['lid'], S.get('blink', 0))
    blid = S['blid'] * (1 - S.get('blink', 0))
    lx, ly = S['lookv']
    if sock:
        socket(ctx, R, rx, sock)
    outline = wob(circle_pts(R, 22, rx), seed, t, R * 0.008)
    spline(ctx, outline)
    g = cairo.RadialGradient(L[0] * R * 0.35, L[1] * R * 0.35, R * 0.1, 0, 0, R * 1.05)
    g.add_color_stop_rgb(0, *mix(sclera, (1, 1, 1), 0.4))
    g.add_color_stop_rgb(0.7, *sclera)
    g.add_color_stop_rgb(1, *mix(sclera, (0.35, 0.38, 0.55), 0.55))
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if veins:
        rr = np.random.default_rng(seed)
        for i in range(11):
            a = i / 11 * TAU + rr.uniform(-.2, .2)
            pts = []
            for k in range(6):
                r = R * (1.02 - k * 0.09)
                aa = a + math.sin(k * 2.1 + i) * 0.13
                pts.append((math.cos(aa) * r * rx, math.sin(aa) * r))
            spline(ctx, np.array(pts), closed=False)
            ink(ctx, lw * 0.45, 0.6 * veins, (0.5, 0.06, 0.1))
            k2 = 2
            bx, by = pts[k2]
            ang = a + (0.5 if i % 2 else -0.5)
            ctx.move_to(bx, by)
            ctx.line_to(bx + math.cos(ang) * R * 0.12, by + math.sin(ang) * R * 0.12)
            ink(ctx, lw * 0.3, 0.45 * veins, (0.5, 0.06, 0.1))
    ox, oy = lx * R * 0.42 * rx, ly * R * 0.38
    ir = R * 0.5
    g = cairo.RadialGradient(ox, oy, ir * 0.15, ox, oy, ir)
    g.add_color_stop_rgb(0, *mix(iris, (1, 0.95, 0.7), 0.35))
    g.add_color_stop_rgb(0.6, *iris)
    g.add_color_stop_rgb(1, *mix(iris, (0, 0, 0), 0.6))
    ctx.arc(ox, oy, ir, 0, TAU)
    ctx.set_source(g)
    ctx.fill()
    if fibers:
        for k in range(28):
            a = k / 28 * TAU
            r0, r1 = ir * 0.3, ir * (0.9 if k % 2 else 0.75)
            ctx.move_to(ox + math.cos(a) * r0, oy + math.sin(a) * r0)
            ctx.line_to(ox + math.cos(a + 0.05) * r1, oy + math.sin(a + 0.05) * r1)
        ctx.set_source_rgba(*mix(iris, (0, 0, 0), 0.5), 0.45)
        ctx.set_line_width(max(0.8, lw * 0.3))
        ctx.stroke()
    ctx.arc(ox, oy, ir * 0.98, 0, TAU)
    ink(ctx, lw * 1.0)
    pr = R * 0.2 * S['pupil']
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(1, pupil_oval)
    ctx.arc(0, 0, pr, 0, TAU)
    ctx.restore()
    ctx.set_source_rgb(0.01, 0.01, 0.02)
    ctx.fill()
    # occlusion under the upper lid
    yl = lid_y(R, lid)
    g = cairo.LinearGradient(0, yl - R * 0.05, 0, yl + R * 0.45)
    g.add_color_stop_rgba(0, 0.05, 0.03, 0.12, 0.55)
    g.add_color_stop_rgba(1, 0.05, 0.03, 0.12, 0)
    ctx.set_source(g)
    ctx.rectangle(-R * 1.2, -R * 1.2, R * 2.4, R * 2.4)
    ctx.fill()
    # specular: window highlight + dot + bounce
    tear = S.get('tear', 0)
    hx, hy = ox - R * 0.2 + L[0] * R * 0.05, oy - R * 0.2 + L[1] * R * 0.05
    hs = R * (0.11 + 0.04 * tear)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(-0.5)
    ctx.scale(1.25, 0.85)
    ctx.arc(0, 0, hs, 0, TAU)
    ctx.restore()
    ctx.set_source_rgba(1, 1, 0.97, 0.95)
    ctx.fill()
    ctx.arc(ox + R * 0.13, oy + R * 0.1, hs * 0.38, 0, TAU)
    ctx.fill()
    ctx.save()
    ctx.scale(rx, 1)
    ctx.arc(0, 0, R * 0.82, math.radians(30), math.radians(120))
    ctx.restore()
    ink(ctx, R * 0.05, 0.18 + 0.4 * tear, (0.75, 0.9, 1.0))
    lash_edge = None
    if lid > 0.01:
        ye = lid_y(R, lid)
        bow = R * 0.22 * (1 - abs(min(lid, 0.75) - 0.5))
        xs = np.linspace(-R * 1.1, R * 1.1, 11)
        edge = [(x, ye + bow * (1 - (x / (R * 1.1)) ** 2)) for x in xs]
        poly(ctx, [(-R * 1.2, -R * 1.25)] + edge + [(R * 1.2, -R * 1.25)])
        g = cairo.LinearGradient(0, -R, 0, ye)
        g.add_color_stop_rgb(0, *mix(lidc, (1, 1, 1), 0.18))
        g.add_color_stop_rgb(1, *mix(lidc, (0, 0, 0), 0.35))
        ctx.set_source(g)
        ctx.fill()
        if lid > 0.22:
            spline(ctx, np.array([(x, y - R * 0.17) for x, y in edge[2:-2]]), closed=False)
            ink(ctx, lw * 0.6, 0.55)
        if lid > 0.55:
            spline(ctx, np.array([(x * 0.8, y - R * 0.42) for x, y in edge[3:-3]]), closed=False)
            ink(ctx, lw * 0.45, 0.35)
            spline(ctx, np.array([(x * 0.9, y - R * 0.3) for x, y in edge[1:-1]]), closed=False)
            ink(ctx, R * 0.05, 0.12, (1, 1, 1))
        if lid > 0.55:
            k = clamp((lid - 0.55) / 0.45)
            low = [(x, R * 1.08 * (1 - k) + (y + 1.5) * k) for x, y in edge]
            poly(ctx, [(-R * 1.2, R * 1.25)] + low + [(R * 1.2, R * 1.25)])
            ctx.set_source_rgb(*mix(lidc, (0, 0, 0), 0.25))
            ctx.fill()
            if k < 0.97:
                spline(ctx, np.array(low), closed=False)
                ink(ctx, lw * 0.8)
        spline(ctx, np.array(edge), closed=False)
        ink(ctx, lw * 1.5)
        if lashes and lid > 0.06:
            lash_edge = edge
    if blid > 0.01:
        yb = R - 1.15 * R * blid
        xs = np.linspace(-R * 1.1, R * 1.1, 9)
        edge = [(x, yb - R * 0.25 * blid * (1 - (x / (R * 1.1)) ** 2)) for x in xs]
        poly(ctx, [(-R * 1.2, R * 1.25)] + edge + [(R * 1.2, R * 1.25)])
        ctx.set_source_rgb(*mix(lidc, (0, 0, 0), 0.15))
        ctx.fill()
        spline(ctx, np.array(edge), closed=False)
        ink(ctx, lw * 0.9)
    ctx.restore()
    spline(ctx, outline)
    ink(ctx, lw)
    if lash_edge is not None:
        for k in range(1, 10):
            x_, y_ = lash_edge[k]
            rr_ = math.hypot(x_ / max(rx, .1), y_)
            if rr_ > R * 0.985:
                if abs(x_) > R * 0.8 * rx:
                    continue
                x_, y_ = x_ * R * 0.985 / rr_, y_ * R * 0.985 / rr_
            side = x_ / R
            pts = np.array([(x_, y_), (x_ + side * R * 0.14, y_ + R * 0.13),
                            (x_ + side * R * 0.3, y_ + R * 0.14 - R * 0.06)])
            taper(ctx, pts, lw * 1.1, lw * 0.25)


def mouth(ctx, w, S, lw, seed, t, oness=0.0, inner=(0.22, 0.02, 0.06), teeth=False):
    talk = S.get('talk', 0)
    sib = S.get('sib', 0)
    op = clamp(S.get('mopen', 0) + talk * (0.95 - 0.45 * clamp(sib * 3 - 0.3)))
    wide = 1 + 0.18 * clamp(sib * 3 - 0.3) - 0.12 * op * (1 - oness)
    we = w * wide * (1 - oness) + w * 0.42 * oness
    h = (we * 0.62 * op) * (1 - oness) + (we * (1.2 + 0.5 * op)) * oness
    sm = S['smile'] * (1 - oness)
    k = sm * w * 0.2
    xs = np.linspace(-we / 2, we / 2, 13)
    base = np.array([k * (1 - (2 * x / we) ** 2) - k * 0.5 for x in xs])
    prof = np.sqrt(np.clip(1 - (2 * xs / we) ** 2, 0, 1)) ** (0.7 + 0.3 * oness)
    up = 0.35 + 0.15 * oness
    top = np.stack([xs, base - h * prof * up], 1)
    bot = np.stack([xs, base + h * prof * (1 - up)], 1)
    if h < 2.0:
        pts = wob(np.stack([xs, base], 1)[::2], seed, t, w * 0.01)
        n = len(pts)
        tan = np.gradient(pts, axis=0)
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
        wv = lw * (0.35 + 0.65 * np.sin(np.linspace(0, np.pi, n)))
        poly(ctx, np.concatenate([pts + nrm * wv[:, None] / 2, (pts - nrm * wv[:, None] / 2)[::-1]]))
        ctx.set_source_rgb(*INK)
        ctx.fill()
        for e in (0, -1):
            ctx.arc(*pts[e], lw * 0.45, 0, TAU)
            ctx.fill()
        return
    shape = np.concatenate([top, bot[::-1][1:-1]])
    shape = wob(shape, seed, t, w * 0.006)
    spline(ctx, shape)
    g = cairo.LinearGradient(0, base[6] - h * up, 0, base[6] + h * (1 - up))
    g.add_color_stop_rgb(0, 0.01, 0.0, 0.02)
    g.add_color_stop_rgb(1, *inner)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if h > w * 0.12 and oness < 0.5:
        ctx.save()
        ctx.translate(0, base[6] + h * (1 - up) * 0.95)
        ctx.scale(1, 0.5)
        ctx.arc(0, 0, we * 0.28, 0, TAU)
        ctx.restore()
        ctx.set_source_rgb(0.62, 0.22, 0.3)
        ctx.fill()
    if teeth and h > 3:
        for i in range(-2, 3):
            ctx.rectangle(i * we * 0.13 - we * 0.05, base[6] - h * up - 2, we * 0.1, h * 0.28)
        ctx.set_source_rgb(0.92, 0.9, 0.8)
        ctx.fill()
    ctx.restore()
    spline(ctx, shape)
    ink(ctx, lw)


# ------------------------------------------------------------------ characters
def draw_iris(ctx, S, t):
    x, y = S['x'], S['y']
    lean, droop, spread = S['lean'], S['droop'], S['spread']
    hx = x + lean * 80 + math.sin(t * 0.7) * 6
    hy = y + abs(lean) * 22 + droop * 22 + math.sin(t * 1.1) * 4 - S.get('talk', 0) * 4
    R = 165
    lw = 5.5
    L = light_at(hx, hy)
    # stem
    bx, by = x - 10, 1990
    c1 = (bx + 10, by - 300)
    c2 = (hx - lean * 120, hy + 380)

    def bez(u):
        p0, p1, p2, p3 = np.array((bx, by)), np.array(c1), np.array(c2), np.array((hx, hy + R))
        return (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3 * p3

    stem = np.array([bez(u) for u in np.linspace(0, 1, 24)])
    taper(ctx, stem, 30, 18, INK)
    taper(ctx, stem, 20, 10, (0.13, 0.2, 0.15))
    taper(ctx, stem + np.array(L) * 4, 5, 2, (0.42, 0.55, 0.42), 0.7)
    for k, u in enumerate((0.12, 0.27, 0.41, 0.56, 0.71, 0.84)):
        p = bez(u); q = bez(u + 0.01)
        tx, ty = unit(*(q - p))
        sd = 1 if k % 2 else -1
        nx, ny = -ty * sd, tx * sd
        poly(ctx, [(p[0] + tx * 7, p[1] + ty * 7), (p[0] + nx * 26 - tx * 10, p[1] + ny * 26 - ty * 10),
                   (p[0] - tx * 7, p[1] - ty * 7)])
        ctx.set_source_rgb(*INK)
        ctx.fill()
    # tendril curl
    p = bez(0.52)
    tend = np.concatenate([[p], [p + (40, -20), p + (80, -30)], spiral(p[0] + 100, p[1] - 30, 28, 1.4, math.pi, 1)])
    spline(ctx, tend, closed=False)
    ink(ctx, 5.5)

    def leaf(u, ang, Ln, seed):
        px, py = bez(u)
        ctx.save()
        ctx.translate(px, py)
        a = ang + math.sin(t * 1.3 + seed) * 0.05
        ctx.rotate(a)
        Ll = rot(L, -a)
        up, dn = [], []
        n = 15
        for i in range(n + 1):
            v = i / n
            wd = Ln * 0.17 * math.sin(math.pi * v) ** 0.75 * (1 - 0.25 * v)
            serr = (5 if i % 2 else 0) * math.sin(math.pi * v)
            cy_ = -Ln * 0.06 * math.sin(math.pi * v) - (Ln * 0.12 * (v - 0.8) / 0.2 if v > 0.8 else 0)
            up.append((v * Ln, cy_ - wd - serr))
            dn.append((v * Ln, cy_ + wd + serr))
        pts = wob(np.array(up + dn[::-1][1:-1]), seed, t, 0.8)
        pf = lambda c: poly(c, pts)
        g = cairo.LinearGradient(0, -Ln * 0.2, 0, Ln * 0.2)
        g.add_color_stop_rgb(0, 0.3, 0.42, 0.3)
        g.add_color_stop_rgb(1, 0.16, 0.26, 0.19)
        lit_shape(ctx, pf, g, (0.07, 0.12, 0.1), (0.7, 0.85, 0.65), Ll, Ln * 0.3, Ln / 2, 0, lw,
                  hatch_a=0.35, hatch_sp=8)
        mid = np.array([(v * Ln, -Ln * 0.06 * math.sin(math.pi * v) - (Ln * 0.12 * (v - 0.8) / 0.2 if v > 0.8 else 0))
                        for v in np.linspace(0.03, 0.95, 10)])
        spline(ctx, mid, closed=False)
        ink(ctx, lw * 0.6, 0.85)
        for k in range(2, 9):
            mx_, my_ = mid[k]
            for sd in (-1, 1):
                ctx.move_to(mx_, my_)
                ctx.line_to(mx_ + Ln * 0.07, my_ + sd * Ln * 0.11 * math.sin(math.pi * k / 10))
        ink(ctx, lw * 0.35, 0.6)
        ctx.restore()

    leaf(0.42, math.radians(-150 + 55 * S['leafL']), 250, 11)
    leaf(0.64, math.radians(-40 - 25 * S['leafR']), 230, 12)

    ctx.save()
    ctx.translate(hx, hy)
    hr = lean * 0.12 + math.sin(t * 0.7) * 0.02
    ctx.rotate(hr)

    def petal(a, Lp, wdt, seed, curl, cols, back=False):
        ctx.save()
        ctx.rotate(a)
        Ll = rot(L, -a - hr)
        up, dn = [], []
        n = 12
        for i in range(n + 1):
            v = i / n
            wd = wdt * math.sin(math.pi * min(1, v * 1.08)) ** 0.7 * (1 - 0.35 * v) / 2
            cl = curl * (math.sin(math.pi * v * 0.9) * 0.08 + (max(0, v - 0.75) / 0.25) ** 2 * 0.22) * Lp
            xx = R * 0.72 + v * (Lp - R * 0.72)
            up.append((xx, cl - wd))
            dn.append((xx, cl + wd))
        pts = wob(np.array(up + dn[::-1]), seed, t, 1.1)
        pf = lambda c: spline(c, pts)
        g = cairo.LinearGradient(R * 0.7, 0, Lp, 0)
        b0, b1, sh = cols
        g.add_color_stop_rgb(0, *b0)
        g.add_color_stop_rgb(1, *b1)
        lit_shape(ctx, pf, g, sh, (1, 1, 0.9), Ll, wdt * 0.9, (R + Lp) / 2, 0, lw,
                  hatch_a=0.0 if back else 0.28, hatch_sp=7, rim_a=0.0 if back else 0.75)
        if not back:
            crease = np.array([(R * 0.8 + v * (Lp - R * 0.8) * 0.85,
                                curl * (math.sin(math.pi * v * 0.9 * 0.85) * 0.08) * Lp) for v in np.linspace(0.1, 0.9, 6)])
            spline(ctx, crease, closed=False)
            ink(ctx, lw * 0.45, 0.4)
        ctx.restore()

    # back ring (darker, between front petals)
    n = 13
    for i in range(n - 1):
        a0 = math.radians(158 + (i + 0.5) * (226 / (n - 1)))
        a = a0 - droop * 0.4 * math.cos(a0 - math.pi / 2) * 0 + droop * 0.38 * math.sin(math.pi / 2 - a0) * 0
        a = a0 + droop * 0.4 * math.cos(a0) * -0.0 + droop * 0.35 * (math.pi / 2 - a0) / math.pi
        Lp = R * (1.62 + 0.1 * math.sin(i * 1.7)) * (1 - 0.1 * droop + 0.08 * spread)
        petal(a + math.sin(t * 0.8 + i) * 0.02, Lp, R * 0.3, 300 + i, 0.6,
              ((0.42, 0.36, 0.46), (0.62, 0.6, 0.62), (0.16, 0.14, 0.22)), back=True)
    for i in range(n):
        a0 = math.radians(158 + i * (226 / (n - 1)))
        a = a0 + droop * 0.35 * (math.pi / 2 - a0) / math.pi * 1.6
        a += math.sin(t * 0.9 + i * 0.7) * 0.025 + spread * 0.04 * math.cos(a0)
        Lp = R * (1.9 + 0.12 * math.sin(i * 2.3)) * (1 - 0.12 * droop + 0.1 * spread)
        petal(a, Lp, R * 0.34, 30 + i, 0.8 if i % 2 else -0.6,
              ((0.6, 0.52, 0.62), (0.95, 0.93, 0.85), (0.32, 0.3, 0.42)))
    for i, a0 in enumerate((100, 122, 146)):
        petal(math.radians(a0 + droop * 6), R * 1.4, R * 0.42, 60 + i, 0.3,
              ((0.55, 0.48, 0.58), (0.82, 0.78, 0.72), (0.28, 0.25, 0.36)))
    # mouth interior below disk
    talk = S.get('talk', 0)
    op = clamp(S.get('mopen', 0) + talk * 0.9)
    sm = S['smile']
    ctx.save()
    ctx.translate(0, R * 0.78)
    ctx.scale(1, 0.3 + op * 0.55)
    ctx.arc(0, 0, R * 0.62, 0, math.pi)
    ctx.restore()
    g = cairo.LinearGradient(0, R * 0.78, 0, R * 1.3)
    g.add_color_stop_rgb(0, 0.02, 0, 0.02)
    g.add_color_stop_rgb(1, 0.3, 0.03, 0.08)
    ctx.set_source(g)
    ctx.fill()
    Ll = rot(L, -hr)
    eyeball(ctx, R, S, lw, 5, t, iris=(0.48, 0.78, 0.2), lidc=(0.5, 0.42, 0.52), veins=1.0,
            lashes=True, L=Ll, sock=0.6)
    for sx in (-1, 1):
        poly(ctx, [(sx * R * 0.24, R * 0.955), (sx * R * 0.15, R * (1.16 + op * 0.06)), (sx * R * 0.07, R * 0.99)])
        ctx.set_source_rgb(0.93, 0.92, 0.84)
        ctx.fill_preserve()
        ink(ctx, lw * 0.6)
    # crooked tombstone teeth (the drawing's little rectangles)
    drop = op * R * 0.42
    for i in range(6):
        u = (i - 2.5) / 2.5
        tx = u * R * 0.55
        ty = R * 0.9 + drop * (1 - 0.3 * abs(u)) - sm * R * 0.14 * (1 - u * u) + sm * R * 0.05
        ctx.save()
        ctx.translate(tx, ty)
        ctx.rotate(u * 0.25 + math.sin(i * 2.7) * 0.08)
        tw, th = R * 0.085, R * (0.3 + 0.04 * math.sin(i * 1.9))
        pts = wob(np.array([[-tw, 0], [tw, 0], [tw * 0.95, th * 0.8], [tw * 0.4, th], [-tw * 0.4, th], [-tw * 0.95, th * 0.8]]),
                  80 + i, t, 0.8)
        pf = lambda c, pts=pts: poly(c, pts)
        lit_shape(ctx, pf, (0.6, 0.7, 0.5), (0.25, 0.33, 0.24), (0.95, 1, 0.85), rot(Ll, -u * 0.25), tw * 2, 0, th / 2,
                  lw * 0.85, heavy=1.4)
        ctx.restore()
    brow(ctx, R, S, lw, 9, t, col=(0.06, 0.08, 0.06), width=0.1, rise=1.18, spiky=0.4)
    ctx.restore()


CLOUDS = {
    'CLAWD': dict(blobs=[(-150, 15, 68), (-100, -38, 80), (-25, -72, 88), (62, -58, 84), (135, -12, 72),
                         (158, 38, 52), (-165, 48, 48)], box=(-168, -10, 336, 92), R=60, rx=1.0,
                  base=(0.44, 0.49, 0.58), shade=(0.15, 0.17, 0.25), iris=(0.45, 0.6, 0.85)),
    'CLAWDIA': dict(blobs=[(-122, 12, 60), (-72, -42, 70), (2, -68, 78), (78, -44, 68), (124, 12, 58),
                           (0, 22, 92)], box=(-130, 0, 260, 78), R=52, rx=0.84,
                    base=(0.64, 0.58, 0.72), shade=(0.27, 0.23, 0.36), iris=(0.82, 0.48, 0.78)),
}


def draw_cloud(ctx, S, t, kind):
    C = CLOUDS[kind]
    x, y = S['x'], S['y']
    ph = 0 if kind == 'CLAWD' else 2
    br = math.sin(t * 1.2 + ph)
    talk = S.get('talk', 0)
    ctx.save()
    ctx.translate(x, y + math.sin(t * 0.6 + ph) * 6)
    ctx.scale(1 + 0.015 * br + 0.02 * talk, 1 - 0.012 * br + 0.02 * talk)
    L = light_at(x, y)
    base = mix(C['base'], C['shade'], S['dark'] * 0.7)
    rr = np.random.default_rng(3 if kind == 'CLAWD' else 4)
    blobs = [(bx, by, r * (1 + 0.03 * math.sin(t * 1.3 + i * 1.7))) for i, (bx, by, r) in enumerate(C['blobs'])]
    bx0, by0, bw, bh = C['box']

    def pf(c):
        for (bx, by, r) in blobs:
            c.new_sub_path()
            c.arc(bx, by, r, 0, TAU)
        c.new_sub_path()
        c.rectangle(bx0, by0, bw, bh)

    # wisps curling off the sides (behind)
    for sd in (-1, 1):
        sx = sd * (bw / 2 + 10)
        pts = np.concatenate([[(sx, 50), (sx + sd * 40, 66)],
                              spiral(sx + sd * 70, 50, 26, 1.3, math.pi / 2, -sd)])
        pts = wob(pts, 150 + sd, t, 0.8)
        spline(ctx, pts, closed=False)
        ink(ctx, 14)
        spline(ctx, pts, closed=False)
        ink(ctx, 7, 1, mix(base, C['shade'], 0.4))
    pf(ctx)
    ink(ctx, 11)
    heavy_side(ctx, pf, L, 180, 0, 0, 17)
    lit_shape(ctx, pf, base, C['shade'], (0.98, 0.97, 0.86), L, 170, 0, 0, 5, soff=0.13, roff=0.04,
              hatch_a=0.3, hatch_sp=10, outline=False)
    # billow definition
    for (bx, by, r) in blobs[:5]:
        ctx.arc(bx, by + 4, r * 0.92, math.radians(40), math.radians(140))
        ink(ctx, 3.5, 0.35)
    # underside darkening
    g = cairo.LinearGradient(0, 20, 0, 100)
    g.add_color_stop_rgba(0, 0.02, 0.02, 0.08, 0)
    g.add_color_stop_rgba(1, 0.02, 0.02, 0.08, 0.35)
    ctx.save()
    pf(ctx)
    ctx.clip()
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    ctx.save()
    ctx.translate(0, -10)
    R = C['R']
    eyeball(ctx, R, S, 4.5, 110 if kind == 'CLAWD' else 111, t, iris=C['iris'],
            lidc=mix(base, (0, 0, 0), 0.1), rx=C['rx'], pupil_oval=1.5, lashes=(kind == 'CLAWDIA'), L=L,
            veins=0.35, sock=0.55)
    brow(ctx, R, S, 4, 112, t, width=0.2 if kind == 'CLAWD' else 0.13, spiky=0.5 if kind == 'CLAWD' else 0)
    ctx.restore()
    ctx.save()
    ctx.translate(0, R * 1.05 + 12)
    mouth(ctx, 62, S, 4.5, 113, t, teeth=(kind == 'CLAWD'))
    ctx.restore()
    ctx.restore()


def draw_rain(ctx, S, t):
    amt = S['rain']
    if amt < 0.02:
        return
    x, y = S['x'], S['y']
    rr = np.random.default_rng(55)
    n = int(46 * amt)
    for i in range(n):
        ox = rr.uniform(-140, 140)
        ph = rr.uniform(0, 1)
        sp = rr.uniform(0.7, 1.1)
        u = (t * sp * 1.4 + ph) % 1.0
        yy = y + 70 + u * 900
        ctx.move_to(x + ox - u * 20, yy)
        ctx.line_to(x + ox - u * 20 - 3, yy + 30)
        ink(ctx, 3, 0.55 * amt * (1 - u), (0.75, 0.88, 1.0))


def draw_bee(ctx, S, t, f):
    x, y = S['x'], S['y']
    face = S['face']
    ctx.save()
    ctx.translate(x + math.sin(t * 7) * 3, y + math.sin(t * 9.3) * 5)
    ctx.scale(-face, 1)
    ctx.scale(0.92, 0.92)
    L = light_at(x, y)
    L = (L[0] * -face, L[1])
    # wings: two poses alternate (stop-motion flutter) + faint smear
    pose = (f // 2) % 2
    for smear, al in ((1 - pose, 0.12), (pose, 0.4)):
        wa = -0.6 if smear else 0.1
        for i, (wx, wy) in enumerate(((18, -56), (44, -50))):
            ctx.save()
            ctx.translate(wx, wy)
            ctx.rotate(wa + i * 0.3)
            pts = np.array([[0, 0], [-14, -40], [-4, -82], [22, -94], [36, -64], [18, -22]])
            spline(ctx, pts)
            ctx.set_source_rgba(0.78, 0.92, 0.95, al)
            ctx.fill_preserve()
            ink(ctx, 2.5, al * 1.8)
            for v in ((2, -30, 4, -80), (8, -20, 26, -78), (12, -14, 30, -50)):
                ctx.move_to(v[0], v[1]); ctx.line_to(v[2], v[3])
            ink(ctx, 1.4, al * 1.4)
            ctx.restore()
    # antennae with spiral tips
    an = S['antenna']
    for i, bx in enumerate((-34, -8)):
        ctx.save()
        ctx.translate(bx, -54)
        ctx.rotate(-0.15 + i * 0.22 + (1 - an) * (0.9 + i * 0.2) + math.sin(t * 16 + i) * 0.05 * an)
        pts = np.concatenate([[(0, 0), (-4, -40), (2, -72)], spiral(14, -82, 14, 1.3, math.pi, 1, 16)])
        spline(ctx, pts, closed=False)
        ink(ctx, 4.5)
        ctx.restore()
    # stinger
    poly(ctx, [(70, -14), (132, -38), (72, 12)])
    ctx.set_source_rgb(0.1, 0.08, 0.06)
    ctx.fill()
    # legs
    for k, lx in enumerate((-30, -5, 22)):
        sw = math.sin(t * 4 + k) * 4
        pts = np.array([(lx, 55), (lx - 6, 78), (lx + 4 + sw, 98), (lx + 12 + sw, 96)])
        spline(ctx, pts, closed=False)
        ink(ctx, 3.5)
    body = wob(circle_pts(1, 24) * np.array([82, 66]), 125, t, 1.0)
    pf = lambda c: spline(c, body)
    g = cairo.RadialGradient(-25, -28, 8, 0, 0, 95)
    g.add_color_stop_rgb(0, 0.98, 0.84, 0.38)
    g.add_color_stop_rgb(1, 0.78, 0.55, 0.12)
    lit_shape(ctx, pf, g, (0.32, 0.2, 0.06), (1, 0.97, 0.8), L, 120, 0, 0, 5, hatch_a=0.0, outline=False)
    ctx.save()
    pf(ctx)
    ctx.clip()
    for sx in (18, 46, 74):
        ctx.move_to(sx, -80)
        ctx.curve_to(sx - 16, -25, sx - 16, 25, sx, 80)
        ink(ctx, 15, 0.92, (0.06, 0.05, 0.05))
    ctx.restore()
    # fuzz
    for k in range(0, len(body), 1):
        px, py = body[k]
        nx, ny = unit(px / 82, py / 66)
        ln = 7 + 3 * math.sin(k * 3.1 + int(t * 6))
        ctx.move_to(px - nx * 2, py - ny * 2)
        ctx.line_to(px + nx * ln + ny * 2, py + ny * ln - nx * 2)
    ink(ctx, 2.6)
    pf(ctx)
    ink(ctx, 4.5)
    heavy_side(ctx, pf, L, 90, 0, 0, 8)
    ctx.save()
    ctx.translate(-18, -8)
    eyeball(ctx, 34, S, 3.5, 126, t, iris=(0.55, 0.32, 0.12), lidc=(0.7, 0.52, 0.16), pupil_oval=1.4, L=L, sock=0.45)
    brow(ctx, 34, S, 3.5, 127, t, width=0.22, rise=1.38)
    ctx.restore()
    ctx.save()
    ctx.translate(-18, 42)
    mouth(ctx, 30, S, 3.2, 128, t)
    ctx.restore()
    ctx.restore()


def draw_goste(ctx, S, t, f):
    x, y = S['x'], S['y']
    al = S['alpha']
    trem = S['tremble']
    talk = S.get('talk', 0)
    jx = (math.sin(f * 2.7) * 2.2 + math.sin(f * 1.3) * 1.2) * trem
    bob = math.sin(t * 2.0) * 7
    L = light_at(x, y)
    ctx.save()
    ctx.translate(x + jx, y + bob)
    sq = 1 + 0.03 * talk
    ctx.scale(1 / sq ** 0.5, sq)
    radial_glow(ctx, 0, 10, 30, 240, (0.55, 0.85, 1.0), 0.3 * al)
    ctx.push_group()
    # wispy arms
    for side, key in ((-1, 'armL'), (1, 'armR')):
        a = S[key]
        wv = math.sin(t * 9) * 0.45 * S['wave'] if side == 1 else 0
        ctx.save()
        ctx.translate(side * 70, 28 - a * 32)
        ctx.rotate(side * (0.55 - a * 1.9) + wv * side)
        pts = np.array([(0, -14), (side * 22, -12), (side * 40, -2), (side * 46, 6), (side * 30, 12), (0, 14)])
        pf = lambda c, pts=pts: spline(c, pts)
        lit_shape(ctx, pf, (0.93, 0.96, 1.0), (0.6, 0.66, 0.82), (1, 1, 1), L, 30, side * 20, 0, 4.5, heavy=1.5)
        ctx.restore()
    # body: dome, flaring sides, tattered hem that flutters
    pts = []
    for i in range(11):
        a = math.pi + i / 10 * math.pi
        pts.append((math.cos(a) * 80, -28 + math.sin(a) * 84))
    pts.append((86, 40))
    pts.append((96, 100))
    hem = 6
    for i in range(hem * 2 + 1):
        u = i / (hem * 2)
        xx = 98 - u * 196
        if i % 2 == 0:
            yy = 142 + 10 * math.sin(t * 3 + u * 9)
            xx += 6 * math.sin(t * 2.4 + u * 7)
        else:
            yy = 112 + 6 * math.sin(t * 2 + u * 5)
        pts.append((xx, yy))
    pts.append((-96, 100))
    pts.append((-86, 40))
    body = wob(np.array(pts), 140, t, 1.0)
    pf = lambda c: poly(c, body) if False else spline(c, body)
    g = cairo.LinearGradient(0, -110, 0, 150)
    g.add_color_stop_rgba(0, 0.97, 0.98, 1.0, 1)
    g.add_color_stop_rgba(0.6, 0.86, 0.92, 1.0, 1)
    g.add_color_stop_rgba(1, 0.62, 0.76, 0.95, 0.75)
    lit_shape(ctx, pf, g, (0.55, 0.62, 0.8), (1, 1, 1), L, 130, 0, 0, 5, soff=0.12, hatch_a=0.18, hatch_sp=9)
    # warm uplight from the jack-o'-lantern
    ctx.save()
    pf(ctx)
    ctx.clip()
    g = cairo.RadialGradient(-30, 220, 20, -30, 220, 260)
    g.add_color_stop_rgba(0, 1, 0.55, 0.15, 0.3)
    g.add_color_stop_rgba(1, 1, 0.55, 0.15, 0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    # trailing wisps
    for k, hxp in enumerate((-60, 10, 70)):
        pts = np.concatenate([[(hxp, 135), (hxp + 8, 165)], spiral(hxp + 22 * (1 if k % 2 else -1), 180, 16, 1.2,
                                                                     math.pi, 1 if k % 2 else -1, 12)])
        spline(ctx, wob(pts, 160 + k, t, 1.0), closed=False)
        ink(ctx, 3.5, 0.45, (0.75, 0.88, 1.0))
    if S['blush'] > 0.01:
        for sx in (-1, 1):
            ctx.save()
            ctx.translate(sx * 50, 2)
            ctx.scale(1, 0.55)
            ctx.arc(0, 0, 17, 0, TAU)
            ctx.restore()
            ctx.set_source_rgba(1, 0.5, 0.58, 0.5 * S['blush'])
            ctx.fill()
    lid = max(S['lid'], S.get('blink', 0))
    blid = S['blid'] * (1 - S.get('blink', 0))
    lx, ly = S['lookv']
    tear = S['tear']
    for sx in (-1, 1):
        ex, ey = sx * 27 + lx * 7, -36 + ly * 6
        ry = 23 * (0.85 + 0.12 * S['pupil'] + 0.1 * S['brow'])
        ctx.save()
        ctx.translate(ex, ey)
        # soft socket shadow
        ctx.save()
        ctx.scale(1, ry / 12)
        g = cairo.RadialGradient(0, 0, 10, 0, 0, 20)
        g.add_color_stop_rgba(0, 0.2, 0.25, 0.45, 0.35)
        g.add_color_stop_rgba(1, 0.2, 0.25, 0.45, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, 20, 0, TAU)
        ctx.fill()
        ctx.arc(0, 0, 12, 0, TAU)
        ctx.restore()
        g = cairo.LinearGradient(0, -ry, 0, ry)
        g.add_color_stop_rgb(0, 0.0, 0.0, 0.02)
        g.add_color_stop_rgb(1, 0.08, 0.1, 0.22)
        ctx.set_source(g)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        hr = 4 + 3 * tear
        ctx.arc(-3, -ry * 0.45, hr, 0, TAU)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill()
        ctx.arc(3, ry * 0.32, hr * 0.5, 0, TAU)
        ctx.fill()
        if lid > 0.01:
            yy = -ry + 2.1 * ry * lid
            ctx.rectangle(-20, -ry - 5, 40, yy + ry + 5)
            ctx.set_source_rgb(0.9, 0.93, 1)
            ctx.fill()
        if blid > 0.01:
            yy = ry - 1.2 * ry * blid
            ctx.move_to(-20, ry + 5)
            ctx.line_to(-20, yy + 4)
            ctx.curve_to(-6, yy - 6, 6, yy - 6, 20, yy + 4)
            ctx.line_to(20, ry + 5)
            ctx.close_path()
            ctx.set_source_rgb(0.9, 0.93, 1)
            ctx.fill()
        ctx.restore()
        if lid > 0.01:
            yy = -ry + 2.1 * ry * lid
            ctx.move_to(-13, yy)
            ctx.curve_to(-5, yy + 3, 5, yy + 3, 13, yy)
            ink(ctx, 4)
        if tear > 0.45:
            u = (t * 0.5 + (0.3 if sx > 0 else 0)) % 1.0
            ty = ry + 4 + u * 50
            ctx.move_to(sx * 4, ty - 8)
            ctx.curve_to(sx * 4 + 6, ty, sx * 4 + 6, ty + 6, sx * 4, ty + 6)
            ctx.curve_to(sx * 4 - 6, ty + 6, sx * 4 - 6, ty, sx * 4, ty - 8)
            ctx.set_source_rgba(0.55, 0.85, 1.0, (tear - 0.45) * 1.8 * (1 - u))
            ctx.fill()
        ctx.restore()
        ar = S['arch']
        yb = -74 - S['brow'] * 10 + S['lid'] * 5
        outer, inner = sx * 44, sx * 13
        pts = np.array([(outer, yb + ar * 7), (sx * 30, yb - 4), (inner, yb - ar * 8)])
        taper(ctx, pts, 2, 6, INK, 0.8)
    ctx.save()
    ctx.translate(0, 26)
    mouth(ctx, 56, S, 4.5, 141, t, oness=S['oness'], inner=(0.06, 0.08, 0.2))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(al)
    ctx.restore()


# ------------------------------------------------------------------ world
_rng = np.random.default_rng(3)
STARS = [(_rng.uniform(0, W), _rng.uniform(0, 1250), _rng.uniform(1.5, 4.5), _rng.uniform(0, TAU)) for _ in range(70)]


def tree_branches(x0, y0, L0, w0, seed, depth=5):
    out = []
    rr = np.random.default_rng(seed)

    def br(x, y, a, L, w, d):
        pts = [(x, y)]
        bend = rr.uniform(-0.5, 0.5)
        for k in range(1, 7):
            u = k / 6
            aa = a + bend * u + math.sin(u * 5 + d) * 0.12
            x, y = x + math.cos(aa) * L / 6, y + math.sin(aa) * L / 6
            pts.append((x, y))
        end_a = a + bend
        if d >= depth or L < 30:
            sg = 1 if rr.random() < 0.5 else -1
            curl = spiral(x + math.cos(end_a + sg * 1.57) * 14, y + math.sin(end_a + sg * 1.57) * 14, 14, 1.2,
                          end_a - sg * 1.57, sg, 10)
            pts += [tuple(p) for p in curl]
            out.append((np.array(pts), w, w * 0.15))
            return
        out.append((np.array(pts), w, w * 0.62))
        for k in (-1, 1):
            br(x, y, end_a + k * rr.uniform(0.3, 0.75), L * rr.uniform(0.62, 0.8), w * 0.62, d + 1)
        if rr.random() < 0.35:
            br(x, y, end_a + rr.uniform(-0.2, 0.2), L * 0.5, w * 0.5, d + 1)
    br(x0, y0, -math.pi / 2 + 0.08, L0, w0, 0)
    return out


TREE = tree_branches(95, 1480, 260, 46, 9)
TREE2 = tree_branches(1010, 1330, 120, 16, 21, 4)


def sky_colors(dawn):
    top = mix((0.02, 0.04, 0.07), (0.28, 0.33, 0.42), dawn)
    mid = mix((0.07, 0.13, 0.17), (0.6, 0.55, 0.58), dawn)
    hor = mix((0.2, 0.3, 0.3), (0.95, 0.72, 0.55), dawn)
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


def draw_tree(ctx, branches, L, sil, rim):
    for pts, w0, w1 in branches:
        taper(ctx, pts, w0, w1, sil)
    for pts, w0, w1 in branches:
        if w0 > 6:
            taper(ctx, pts + np.array(L) * w0 * 0.3, w0 * 0.22, w1 * 0.1, rim, 0.4)


def draw_pumpkin(ctx, x, y, rx, ry, t, seed, one_eye):
    fl = 0.8 + 0.2 * math.sin(int(t * 12) * 1.3 + seed) * math.sin(int(t * 12) * 0.7 + seed * 2)
    # light pool on ground
    ctx.save()
    ctx.translate(x, y + ry * 0.9)
    ctx.scale(1, 0.3)
    radial_glow(ctx, 0, 0, 10, rx * 3.2, (1, 0.55, 0.15), 0.4 * fl)
    ctx.restore()
    radial_glow(ctx, x, y, 10, rx * 2.4, (1, 0.5, 0.1), 0.25 * fl)
    L = light_at(x, y)
    for k, (ox, sc) in enumerate(((-0.58, 0.6), (0.58, 0.6), (-0.27, 0.74), (0.27, 0.74), (0, 0.62))):
        pts = wob(circle_pts(1, 18) * np.array([rx * sc, ry]) + np.array([x + ox * rx, y]), seed + k, t, 0.9)
        pf = lambda c, pts=pts: spline(c, pts)
        g = cairo.LinearGradient(x, y - ry, x, y + ry)
        g.add_color_stop_rgb(0, 0.92, 0.5, 0.12)
        g.add_color_stop_rgb(1, 0.6, 0.22, 0.04)
        lit_shape(ctx, pf, g, (0.28, 0.08, 0.02), (1, 0.85, 0.55), L, rx * sc * 1.6, x + ox * rx, y, 4.5,
                  hatch_a=0.3, hatch_sp=8, rim_a=0.6, heavy=1.5)
    # curly stem + vine
    stem = np.array([(x - 6, y - ry + 8), (x - 3, y - ry - 18), (x + 6, y - ry - 32), (x + 16, y - ry - 36)])
    taper(ctx, stem, 16, 9, (0.2, 0.26, 0.14))
    spline(ctx, stem, closed=False)
    ink(ctx, 3, 0.8)
    vine = np.concatenate([[(x + 2, y - ry - 6), (x + 30, y - ry - 2)], spiral(x + 46, y - ry - 12, 14, 1.4, math.pi * 0.8, 1, 12)])
    spline(ctx, vine, closed=False)
    ink(ctx, 3.5)
    glow = mix((1, 0.5, 0.08), (1, 0.92, 0.5), fl)
    rim_in = mix((0.6, 0.25, 0.05), (0.9, 0.55, 0.15), fl)

    def carve(pathfn):
        ctx.save()
        ctx.translate(2, 3)
        pathfn()
        ctx.set_source_rgb(*rim_in)
        ctx.fill()
        ctx.restore()
        pathfn()
        g = cairo.RadialGradient(x, y, 5, x, y, rx)
        g.add_color_stop_rgb(0, 1, 0.98, 0.75)
        g.add_color_stop_rgb(1, *glow)
        ctx.set_source(g)
        ctx.fill_preserve()
        ink(ctx, 2.5, 0.8)

    if one_eye:
        carve(lambda: (ctx.new_sub_path(), ctx.arc(x, y - ry * 0.25, rx * 0.27, 0, TAU)))
        ctx.arc(x + rx * 0.05, y - ry * 0.22, rx * 0.1, 0, TAU)
        ctx.set_source_rgb(0.3, 0.1, 0.02)
        ctx.fill()
    else:
        for sx in (-1, 1):
            carve(lambda sx=sx: poly(ctx, [(x + sx * rx * 0.46, y - ry * 0.05), (x + sx * rx * 0.28, y - ry * 0.5),
                                           (x + sx * rx * 0.08, y - ry * 0.08)]))
    # jagged grin
    top, bot = [], []
    for i in range(9):
        u = i / 8
        xx = x - rx * 0.56 + u * rx * 1.12
        cv = math.sin(u * math.pi)
        top.append((xx, y + ry * (0.18 + 0.14 * cv - (0.12 if i % 2 else 0) * cv)))
        bot.append((xx, y + ry * (0.3 + 0.32 * cv + (0.1 if i % 2 == 0 and 0 < i < 8 else 0) * cv)))
    carve(lambda: poly(ctx, top + bot[::-1]))


def draw_house(ctx, Wd, t, dawn, L):
    sil = mix((0.08, 0.1, 0.14), (0.3, 0.3, 0.36), dawn)
    wall = mix((0.12, 0.15, 0.2), (0.38, 0.38, 0.44), dawn)
    # turret behind (left)
    tur = np.array([(762, 1500), (770, 1010), (742, 1000), (790, 830), (812, 790), (820, 760), (838, 785),
                    (868, 1000), (842, 1010), (848, 1500)])
    pf = lambda c: poly(c, tur)
    lit_shape(ctx, pf, wall, sil, (0.65, 0.75, 0.75), L, 80, 805, 1150, 5, hatch_a=0.25, hatch_sp=10, rim_a=0.5)
    curl = spiral(828, 752, 16, 1.3, 0, 1, 12)
    spline(ctx, np.concatenate([[(820, 762)], curl]), closed=False)
    ink(ctx, 6)
    # main body (crooked)
    body = np.array([(800, 1500), (812, 1200), (806, 1000), (818, 805), (1062, 795), (1072, 1000), (1066, 1250),
                     (1078, 1500)])
    pf = lambda c: poly(c, body)
    lit_shape(ctx, pf, wall, sil, (0.65, 0.75, 0.75), L, 260, 940, 1150, 5, rim_a=0.5)
    ctx.save()
    pf(ctx)
    ctx.clip()
    for k in range(30):
        yy = 815 + k * 24
        ctx.move_to(780, yy + 6 * math.sin(k))
        ctx.curve_to(880, yy + 8, 980, yy - 6, 1090, yy + 4 * math.cos(k))
    ink(ctx, 2, 0.3)
    ctx.restore()
    # roof with a curling spire
    roof = np.array([(772, 812), (850, 700), (915, 600), (948, 520), (970, 540), (1010, 640), (1100, 820)])
    pf = lambda c: poly(c, roof)
    lit_shape(ctx, pf, mix(sil, (0.2, 0.2, 0.3), 0.3), (0.03, 0.03, 0.06), (0.7, 0.8, 0.8), L, 160, 940, 700, 5,
              hatch_a=0.45, hatch_sp=8, rim_a=0.55)
    sp = np.concatenate([[(948, 522), (930, 480)], spiral(950, 462, 26, 1.5, math.pi, 1, 18)])
    taper(ctx, sp, 12, 3, INK)
    # crooked chimney with a curl of smoke
    ch = np.array([(1010, 650), (1006, 600), (1045, 596), (1052, 700)])
    poly(ctx, ch)
    ctx.set_source_rgb(*sil)
    ctx.fill_preserve()
    ink(ctx, 4.5)
    for k in range(3):
        u = (t * 0.08 + k / 3) % 1
        sx, sy = 1025 + math.sin(u * 7) * 14 * u, 590 - u * 220
        ctx.arc(sx, sy, 10 + u * 26, 0, TAU)
        ctx.set_source_rgba(0.6, 0.65, 0.7, 0.18 * (1 - u))
        ctx.fill()
    # dark crooked windows + door
    for (wx_, wy_, ww, wh, a) in ((862, 1215, 56, 80, 0.06), (1012, 1180, 46, 66, -0.08), (948, 700, 40, 40, 0)):
        ctx.save()
        ctx.translate(wx_, wy_)
        ctx.rotate(a)
        if wh == 40:
            ctx.arc(0, 0, 20, 0, TAU)
        else:
            ctx.rectangle(-ww / 2, -wh / 2, ww, wh)
        ctx.set_source_rgb(0.02, 0.02, 0.04)
        ctx.fill_preserve()
        ink(ctx, 5)
        ctx.restore()
    ctx.move_to(950, 1500)
    ctx.line_to(952, 1390)
    ctx.curve_to(955, 1330, 1025, 1330, 1028, 1390)
    ctx.line_to(1030, 1500)
    ctx.set_source_rgb(0.03, 0.02, 0.04)
    ctx.fill_preserve()
    ink(ctx, 5)
    ctx.rectangle(952, 1494, 78, 6)
    ctx.set_source_rgba(1, 0.7, 0.3, 0.7)
    ctx.fill()
    # the child's window
    wx, wy = POS['WINDOW']
    wl = Wd['window']
    radial_glow(ctx, wx, wy, 20, 300, (1, 0.72, 0.35), 0.38 * clamp(wl))
    frame = np.array([(wx - 64, wy - 70), (wx + 60, wy - 76), (wx + 64, wy + 72), (wx - 60, wy + 74)])
    poly(ctx, frame)
    g = cairo.LinearGradient(0, wy - 72, 0, wy + 72)
    g.add_color_stop_rgb(0, *mix((0.15, 0.1, 0.1), (1.0, 0.86, 0.5), clamp(wl)))
    g.add_color_stop_rgb(1, *mix((0.1, 0.06, 0.06), (0.95, 0.55, 0.22), clamp(wl)))
    ctx.set_source(g)
    ctx.fill()
    ch_a = Wd['child']
    if ch_a > 0.01:
        ctx.save()
        poly(ctx, frame)
        ctx.clip()
        sc = (0.14, 0.06, 0.08)
        ctx.set_source_rgba(*sc, ch_a)
        hx_, hy_ = wx - 8, wy + 5 - 6 * ch_a
        ctx.arc(hx_, hy_, 22, 0, TAU)
        ctx.fill()
        for k in range(5):
            ctx.arc(hx_ - 18 + k * 9, hy_ - 18 + abs(k - 2) * 2, 7, 0, TAU)
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
            ink(ctx, 13, ch_a, sc)
            ctx.arc(ex, ey, 10, 0, TAU)
            ctx.set_source_rgba(*sc, ch_a)
            ctx.fill()
        ctx.restore()
    for sx in (-1, 1):
        ctx.move_to(wx + sx * 62, wy - 72)
        ctx.line_to(wx + sx * 20, wy - 74)
        ctx.curve_to(wx + sx * 40, wy - 10, wx + sx * 55, wy + 30, wx + sx * 62, wy + 72)
        ctx.close_path()
        ctx.set_source_rgba(0.38, 0.08, 0.12, 0.92)
        ctx.fill()
    poly(ctx, frame)
    ink(ctx, 8)
    ctx.move_to(wx - 2, wy - 74); ctx.line_to(wx + 2, wy + 73)
    ctx.move_to(wx - 62, wy + 2); ctx.line_to(wx + 62, wy - 2)
    ink(ctx, 5)
    poly(ctx, [(wx - 78, wy + 74), (wx + 78, wy + 70), (wx + 74, wy + 86), (wx - 74, wy + 88)])
    ctx.set_source_rgb(*sil)
    ctx.fill_preserve()
    ink(ctx, 4)


def draw_fence(ctx, t, L, dawn):
    iron = mix((0.03, 0.04, 0.06), (0.2, 0.2, 0.24), dawn)
    rr = np.random.default_rng(12)
    ctx.move_to(-150, 1392)
    for k in range(14):
        ctx.line_to(-150 + k * 110, 1392 + 8 * math.sin(k * 1.9))
    ink(ctx, 7, 1, iron)
    ctx.move_to(-150, 1440)
    for k in range(14):
        ctx.line_to(-150 + k * 110, 1440 + 6 * math.sin(k * 1.3 + 1))
    ink(ctx, 7, 1, iron)
    for k in range(26):
        x = -140 + k * 52 + rr.uniform(-6, 6)
        a = rr.uniform(-0.09, 0.09)
        h = rr.uniform(110, 150)
        tx, ty = x + math.sin(a) * h, 1470 - math.cos(a) * h
        ctx.move_to(x, 1470)
        ctx.line_to(tx, ty)
        ink(ctx, 6, 1, iron)
        if k % 3 == 0:
            curl = spiral(tx + 8, ty - 8, 9, 1.2, math.pi, 1, 9)
            spline(ctx, np.concatenate([[(tx, ty)], curl]), closed=False)
            ink(ctx, 4, 1, iron)
        else:
            poly(ctx, [(tx - 7, ty + 4), (tx, ty - 20), (tx + 7, ty + 4), (tx, ty + 10)])
            ctx.set_source_rgb(*iron)
            ctx.fill()
        ctx.move_to(x + 2, 1470)
        ctx.line_to(tx + 2 + L[0] * 2, ty + 6)
        ink(ctx, 1.5, 0.35, (0.6, 0.75, 0.75))


def draw_grave(ctx, x, y, w, h, a, t, L, seed):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(a)
    pts = [(-w / 2, 0)]
    for i in range(9):
        aa = math.pi + i / 8 * math.pi
        pts.append((math.cos(aa) * w / 2, -h + w / 2 + math.sin(aa) * w / 2))
    pts.append((w / 2, 0))
    pts = wob(np.array(pts), seed, t, 0.6)
    pf = lambda c: poly(c, pts)
    lit_shape(ctx, pf, (0.4, 0.43, 0.46), (0.12, 0.13, 0.17), (0.85, 0.92, 0.9), rot(L, -a), w, 0, -h / 2, 4.5,
              hatch_a=0.35, hatch_sp=7)
    ctx.move_to(-w * 0.1, -h * 0.75)
    ctx.line_to(w * 0.05, -h * 0.55)
    ctx.line_to(-w * 0.05, -h * 0.4)
    ctx.line_to(w * 0.1, -h * 0.25)
    ink(ctx, 2.5, 0.8)
    ctx.restore()


def draw_world(ctx, st):
    t, f = st['t'], st['f']
    P = st['P']
    Wd = P['WORLD']
    dawn = Wd['dawn']
    cam = st['cam']
    top, mid, hor = sky_colors(dawn)
    ctx.identity_matrix()
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(0.45, *mid)
    g.add_color_stop_rgb(0.78, *hor)
    ctx.set_source(g)
    ctx.paint()
    # stars as small 4-point glints
    layer(ctx, cam, 0.12)
    for (sx, sy, r, ph) in STARS:
        a = (0.35 + 0.65 * math.sin(int(t * 12) / 12 * 2 + ph) ** 2) * (1 - dawn)
        poly(ctx, [(sx, sy - r * 2), (sx + r * 0.4, sy - r * 0.4), (sx + r * 2, sy), (sx + r * 0.4, sy + r * 0.4),
                   (sx, sy + r * 2), (sx - r * 0.4, sy + r * 0.4), (sx - r * 2, sy), (sx - r * 0.4, sy - r * 0.4)])
        ctx.set_source_rgba(0.95, 0.97, 0.85, a)
        ctx.fill()
    # the enormous pale moon
    layer(ctx, cam, 0.3)
    mx, my = MOON
    MR = 255
    radial_glow(ctx, mx, my, MR * 0.8, MR * 2.6, (0.75, 0.85, 0.8), 0.4 * (1 - dawn * 0.6))
    ctx.arc(mx, my, MR, 0, TAU)
    g = cairo.RadialGradient(mx - 60, my - 70, 20, mx, my, MR)
    g.add_color_stop_rgb(0, *mix((1.0, 0.99, 0.9), (1, 1, 0.97), dawn))
    g.add_color_stop_rgb(0.8, *mix((0.9, 0.9, 0.78), (0.97, 0.95, 0.9), dawn))
    g.add_color_stop_rgb(1, *mix((0.72, 0.76, 0.66), (0.92, 0.9, 0.86), dawn))
    ctx.set_source(g)
    ctx.fill()
    rr = np.random.default_rng(77)
    for k in range(9):
        a = rr.uniform(0, TAU); d = rr.uniform(0, MR * 0.75); r = rr.uniform(18, 60)
        radial_glow(ctx, mx + math.cos(a) * d, my + math.sin(a) * d, r * 0.2, r, (0.55, 0.6, 0.55), 0.2)
    me = Wd['mooneye']
    ctx.save()
    ctx.translate(mx, my + 30)
    if me < 0.05:
        ctx.move_to(-46, 0)
        ctx.curve_to(-20, 26, 20, 26, 46, 0)
        ink(ctx, 6, 0.75, (0.3, 0.32, 0.3))
        for k in range(5):
            u = (k + 1) / 6
            xx = -46 + u * 92
            yy = 19.5 * math.sin(math.pi * u)
            ctx.move_to(xx, yy)
            ctx.line_to(xx + (u - 0.5) * 14, yy + 14)
        ink(ctx, 3.5, 0.7, (0.3, 0.32, 0.3))
    else:
        S = dict(lid=1 - me * 0.75, blid=0.15, lookv=(0.2, 0.8), pupil=1.1, tear=0, blink=0)
        eyeball(ctx, 46 * (0.6 + 0.4 * me), S, 4, 7, t, iris=(0.85, 0.65, 0.25), lidc=(0.85, 0.85, 0.72),
                fibers=False, sock=0.2)
    ctx.restore()
    # thin wispy streaks drifting across the moon
    for k, (yy, x0, ln, th) in enumerate(((205, 160, 560, 10), (488, 430, 640, 12), (540, 80, 420, 7))):
        dx = (t * (5 + k * 3)) % 900 - 300
        pts = []
        for i in range(13):
            u = i / 12
            pts.append((x0 + dx - ln / 2 + u * ln, yy + math.sin(u * 5 + k) * 6))
        pts = np.array(pts)
        tan_w = np.sin(np.linspace(0, np.pi, 13)) * th
        nr = np.array([0, 1.0])
        poly(ctx, np.concatenate([pts - nr * tan_w[:, None] / 2, (pts + nr * tan_w[:, None] / 2)[::-1]]))
        ctx.set_source_rgba(*mix((0.04, 0.07, 0.1), (0.5, 0.5, 0.55), dawn), 0.5)
        ctx.fill()
    # bats with jagged wings
    for (t0, y0, dirn) in ((10.5, 560, 1), (52, 640, -1), (98, 470, 1), (146, 560, -1)):
        u = (t - t0) / 7.0
        if 0 <= u <= 1:
            bx = -100 + u * (W + 200) if dirn > 0 else W + 100 - u * (W + 200)
            by = y0 + math.sin(u * 9) * 40
            fl = 1 if (int(t * 12) % 2) else -0.6
            ctx.save()
            ctx.translate(bx, by)
            ctx.scale(dirn, 1)
            pts = [(0, 6), (-12, -2), (-24, -16 * fl), (-30, -6 * fl), (-40, -14 * fl), (-44, 0 * fl), (-50, -6 * fl),
                   (-38, 10), (-28, 4), (-18, 12), (-8, 8)]
            poly(ctx, pts + [(-p[0], p[1]) for p in pts[::-1]])
            ctx.set_source_rgba(0.02, 0.02, 0.04, 0.95 * (1 - dawn))
            ctx.fill()
            ctx.restore()
    # clouds (characters) with rain
    layer(ctx, cam, 1.0)
    for ch in ('CLAWD', 'CLAWDIA'):
        draw_rain(ctx, P[ch], t)
        draw_cloud(ctx, P[ch], t, ch)
    # far hills + crooked distant tower
    layer(ctx, cam, 0.45)
    for k, (base_y, amp, col, seed) in enumerate(((1300, 70, (0.09, 0.14, 0.17), 1), (1360, 50, (0.06, 0.1, 0.12), 2))):
        ctx.move_to(-500, base_y + 100)
        xs = np.linspace(-500, 1600, 15)
        pts = [(xx, base_y - amp * abs(math.sin(i * 0.9 + seed))) for i, xx in enumerate(xs)]
        spline(ctx, np.array(pts), closed=False)
        ctx.line_to(1600, 2700)
        ctx.line_to(-500, 2700)
        ctx.close_path()
        ctx.set_source_rgb(*mix(col, (0.5, 0.48, 0.55), dawn * 0.8))
        ctx.fill()
        if k == 0:
            tw = [(250, 1260), (262, 1100), (250, 1085), (268, 1000), (276, 990), (286, 1004), (300, 1085),
                  (290, 1100), (298, 1260)]
            poly(ctx, tw)
            ctx.set_source_rgb(*mix(col, (0.5, 0.48, 0.55), dawn * 0.8))
            ctx.fill()
            ctx.rectangle(270, 1120, 10, 16)
            ctx.set_source_rgba(1, 0.7, 0.3, 0.8 * (1 - dawn))
            ctx.fill()
        for j in range(3):
            cx_, cy_ = pts[3 + j * 4]
            spline(ctx, spiral(cx_, cy_ - 6, 16, 1.2, 0, 1, 12), closed=False)
            ink(ctx, 3, 0.5, mix(col, (0.5, 0.6, 0.6), 0.5))
    # twisted trees
    layer(ctx, cam, 0.8)
    sil = mix((0.04, 0.05, 0.08), (0.25, 0.25, 0.3), dawn)
    draw_tree(ctx, TREE, light_at(95, 1100), sil, (0.65, 0.78, 0.8))
    draw_tree(ctx, TREE2, light_at(1010, 1200), sil, (0.65, 0.78, 0.8))
    layer(ctx, cam, 1.0)
    draw_house(ctx, Wd, t, dawn, light_at(940, 1000))
    # ground
    pts = np.array([(-300 + i * 130, 1462 + 26 * math.sin(i * 1.3 + 0.5)) for i in range(14)])
    ctx.move_to(-300, 2700)
    ctx.line_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.line_to(1500, 2700)
    ctx.close_path()
    g = cairo.LinearGradient(0, 1440, 0, 2000)
    g.add_color_stop_rgb(0, *mix((0.12, 0.17, 0.17), (0.35, 0.42, 0.32), dawn))
    g.add_color_stop_rgb(1, *mix((0.02, 0.03, 0.05), (0.18, 0.22, 0.17), dawn))
    ctx.set_source(g)
    ctx.fill()
    spline(ctx, pts, closed=False)
    ink(ctx, 3, 0.5, (0.6, 0.75, 0.72))
    # moonlight pool
    ctx.save()
    ctx.translate(520, 1640)
    ctx.scale(1, 0.25)
    radial_glow(ctx, 0, 0, 30, 600, (0.6, 0.75, 0.75), 0.18 * (1 - dawn))
    ctx.restore()
    draw_fence(ctx, t, light_at(500, 1400), dawn)
    draw_grave(ctx, 425, 1478, 74, 104, -0.12, t, light_at(425, 1430), 170)
    draw_grave(ctx, 708, 1492, 62, 84, 0.14, t, light_at(708, 1450), 171)
    # stepping stones + curling grass
    for (sx, sy, sr) in ((700, 1560, 40), (760, 1650, 46), (800, 1760, 54), (840, 1890, 60)):
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1, 0.38)
        ctx.arc(0, 0, sr, 0, TAU)
        ctx.restore()
        ctx.set_source_rgb(*mix((0.2, 0.24, 0.26), (0.5, 0.5, 0.48), dawn))
        ctx.fill_preserve()
        ink(ctx, 3.5)
    rr = np.random.default_rng(4)
    for i in range(46):
        gx = rr.uniform(-100, 1180)
        gy = rr.uniform(1490, 1960)
        sw = math.sin(int(t * 12) / 12 * 1.5 + gx * 0.01) * 4
        s = 0.7 + 0.6 * (gy - 1490) / 470
        for k in (-1, 0, 1):
            bl = np.array([(gx + k * 7 * s, gy), (gx + k * 10 * s + sw, gy - 18 * s),
                           (gx + k * 16 * s + sw * 1.5, gy - 30 * s - abs(k) * -4)])
            if k == 0 and i % 4 == 0:
                bl = np.concatenate([bl, spiral(bl[-1][0] + 5 * s, bl[-1][1] + 2, 6 * s, 1.1, math.pi, 1, 7)])
            spline(ctx, bl, closed=False)
        ink(ctx, 3 * s, 0.75, (0.03, 0.05, 0.05))
    draw_iris(ctx, P['IRIS'], t)
    # ground shadow under the ghost
    gS = P['GOSTE']
    ctx.save()
    ctx.translate(gS['x'], 1500)
    ctx.scale(1, 0.22)
    radial_glow(ctx, 0, 0, 10, 110, (0.0, 0.0, 0.05), 0.4 * gS['alpha'])
    ctx.restore()
    draw_goste(ctx, P['GOSTE'], t, f)
    draw_pumpkin(ctx, 215, 1560, 105, 82, t, 200, False)
    draw_pumpkin(ctx, 905, 1640, 88, 70, t, 210, True)
    draw_bee(ctx, P['BEE'], t, f)
    # low fog with curls
    layer(ctx, cam, 1.12)
    for i in range(4):
        fx = ((t * (12 + i * 5) + i * 400) % 1800) - 400
        fy = 1530 + i * 95
        ctx.save()
        ctx.translate(fx, fy)
        ctx.scale(1, 0.3)
        radial_glow(ctx, 0, 0, 20, 440, (0.6, 0.75, 0.75), 0.13 * (1 - dawn * 0.6))
        ctx.restore()
        spline(ctx, spiral(fx + 120, fy - 18, 22, 1.2, 0, 1, 12), closed=False)
        ink(ctx, 3, 0.12, (0.85, 0.95, 0.95))
    # foreground brambles framing the bottom corners
    layer(ctx, cam, 1.3)
    for (bx, by, sg) in ((-30, 2000, 1), (1110, 2010, -1)):
        for k in range(5):
            a = -math.pi / 2 + sg * (0.3 + k * 0.22)
            pts = [(bx, by)]
            x_, y_ = bx, by
            for j in range(6):
                x_ += math.cos(a + j * 0.12 * sg) * 32
                y_ += math.sin(a + j * 0.12 * sg) * 32
                pts.append((x_, y_))
            pts = np.concatenate([np.array(pts), spiral(x_ + sg * 14, y_, 14, 1.2, math.pi, sg, 10)])
            taper(ctx, pts, 16, 3, (0.01, 0.01, 0.02))
            for j in range(1, 6):
                px, py = pts[j]
                poly(ctx, [(px - 4, py), (px + sg * 14, py - 10), (px + 4, py + 2)])
                ctx.set_source_rgb(0.01, 0.01, 0.02)
                ctx.fill()


def grade(ctx, st, strength=1.0):
    """teal-night grade, vignette and a whisper of stop-motion exposure flicker."""
    ctx.identity_matrix()
    dawn = st['P']['WORLD']['dawn']
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    ctx.set_source_rgba(0.15, 0.32, 0.38, 0.35 * strength * (1 - dawn * 0.5))
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)
    g = cairo.RadialGradient(W / 2, H * 0.42, H * 0.28, W / 2, H * 0.45, H * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.0, 0.01, 0.03, 0.7 * strength * (1 - dawn * 0.5))
    ctx.set_source(g)
    ctx.paint()
    fl = math.sin(st['f'] // 2 * 12.9898) * 0.5 + 0.5
    ctx.set_source_rgba(0, 0, 0, 0.018 * fl)
    ctx.paint()


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
        bg = Image.blend(bg, Image.new('RGB', bg.size, (14, 40, 52)), 0.45)
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
    ctx.set_source_rgba(0.01, 0.03, 0.05, 0.76 * a)
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
    for key, lines, y0, size in (('title', ['The Ones', 'Who Watch'], 250, 124),
                                 ('endtitle', ['Happy', 'Halloween'], 125, 112)):
        a = Wd[key]
        if a < 0.01:
            continue
        if key == 'endtitle' and st['scene'] != 'photo':
            continue
        for i, l in enumerate(lines):
            y = y0 + i * size * 1.0 + (1 - a) * 30
            text_path(ctx, l, 'Griffy', size, W / 2, y)
            ctx.set_source_rgba(1, 0.45, 0.08, 0.25 * a)
            ctx.set_line_width(34)
            ctx.stroke_preserve()
            ctx.set_source_rgba(0.01, 0.02, 0.04, 0.95 * a)
            ctx.set_line_width(13)
            ctx.stroke_preserve()
            g = cairo.LinearGradient(0, y - size, 0, y)
            if key == 'title':
                g.add_color_stop_rgba(0, 0.97, 0.96, 0.86, a)
                g.add_color_stop_rgba(1, 0.7, 0.82, 0.74, a)
            else:
                g.add_color_stop_rgba(0, 1, 0.78, 0.25, a)
                g.add_color_stop_rgba(1, 1, 0.42, 0.06, a)
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
        grade(ctx, st)
    if pa > 0.001:
        ctx.identity_matrix()
        ctx.push_group()
        draw_photo(ctx, st)
        ctx.identity_matrix()
        grade(ctx, st, 0.45)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(pa)
    draw_titles(ctx, st)
    draw_subs(ctx, st)
    return surf
