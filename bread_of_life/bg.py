"""Procedural painted backgrounds ("plates") + per-frame live elements.

Plates are drawn once into an image (optionally blurred for depth of field)
and cached; shots then frame them with a camera (center, zoom).
Detail is kept soft on purpose: smooth gradients and shapes compress well.
"""
import math

import numpy as np
import skia

from gfx import c4, ellipse, fill, hexc, lin_grad, mix, poly, rad_grad, sample_spline, spline, stroke, tapered

PW, PH = 1000, 1600  # plate size (wider/taller than the 720x1280 frame for camera moves)


def ridge(rng, x0, x1, y, amp, n=40, rough=0.55, seed_shift=0.0):
    xs = np.linspace(x0, x1, n)
    ys = np.zeros(n)
    a = amp
    for o in range(5):
        ph = rng.uniform(0, 6.28)
        f = (o + 1) * 1.7 / (x1 - x0)
        ys += a * np.sin(xs * f * 2 * math.pi + ph)
        a *= rough
    return [(float(x), float(y + yy)) for x, yy in zip(xs, ys)]


def cloud(cv, x, y, w, h, top="#ffffff", bottom="#f3c9b0", alpha=0.9, blur=6, rng=None):
    rng = rng or np.random.default_rng(int(x * 7 + y * 13))
    path = skia.Path()
    for k in range(9):
        cx = x + rng.uniform(-0.5, 0.5) * w
        cy = y + rng.uniform(-0.25, 0.15) * h
        rx = rng.uniform(0.18, 0.32) * w
        ry = rng.uniform(0.35, 0.6) * h
        path.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    p = fill(top, alpha=alpha, blur=blur, shader=lin_grad((0, y - h * 0.6), (0, y + h * 0.6), [top, bottom]))
    cv.drawPath(path, p)


def sky(cv, W, H, stops, pos):
    cv.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", shader=lin_grad((0, 0), (0, H), stops, pos)))


def glow(cv, x, y, r, col, alpha=1.0):
    c = hexc(col) if isinstance(col, str) else col
    cv.drawCircle(x, y, r, fill(col, shader=rad_grad((x, y), r, [(c[0], c[1], c[2], alpha), (c[0], c[1], c[2], alpha * 0.35), (c[0], c[1], c[2], 0.0)], [0.0, 0.35, 1.0])))


# ----------------------------------------------------------------------------
# Plates
# ----------------------------------------------------------------------------

def shore_lake(cv, W, H, tod="morning"):
    """Looking across the Sea of Galilee. Horizon around 0.47H."""
    rng = np.random.default_rng(5)
    hz = H * 0.47
    if tod == "morning":
        sky(cv, W, hz + 5, ["#5f93cf", "#8db6e0", "#cfe0ee", "#fbe3c8"], [0.0, 0.45, 0.8, 1.0])
        sun = (W * 0.18, hz - H * 0.13)
        glow(cv, *sun, W * 0.55, "#fff1d6", 0.85)
        glow(cv, *sun, W * 0.12, "#ffffff", 1.0)
        for (x, y, w, h) in [(0.75, 0.12, 0.5, 0.05), (0.35, 0.2, 0.6, 0.045), (0.9, 0.28, 0.4, 0.03), (0.15, 0.33, 0.45, 0.03), (0.6, 0.36, 0.5, 0.025)]:
            cloud(cv, W * x, H * y, W * w, H * h, top="#ffffff", bottom="#f2cdb6", alpha=0.85, blur=7, rng=rng)
        hill_far, hill_near = "#aeb1cf", "#9095b8"
        water = ["#d9e3ec", "#9fbfd6", "#5f95b8", "#3f7598"]
        refl = "#fff4dc"
    else:  # dusk
        sky(cv, W, hz + 5, ["#2f2c5e", "#7b4f86", "#e07a6a", "#ffb067", "#ffd59a"], [0.0, 0.3, 0.62, 0.86, 1.0])
        sun = (W * 0.80, hz - H * 0.035)
        glow(cv, *sun, W * 0.7, "#ffb36b", 0.8)
        glow(cv, *sun, W * 0.09, "#fff1c9", 1.0)
        for (x, y, w, h) in [(0.3, 0.1, 0.6, 0.04), (0.65, 0.18, 0.5, 0.035), (0.2, 0.26, 0.5, 0.03), (0.75, 0.31, 0.45, 0.025)]:
            cloud(cv, W * x, H * y, W * w, H * h, top="#f6a07d", bottom="#7a4a7a", alpha=0.8, blur=6, rng=rng)
        hill_far, hill_near = "#6f557f", "#4f3d63"
        water = ["#f2b07a", "#c27a72", "#6b5378", "#3c3556"]
        refl = "#ffd7a0"
    # far hills (other side of the lake)
    far = ridge(rng, -20, W + 20, hz - H * 0.018, H * 0.012, n=50)
    cv.drawPath(poly(far + [(W + 20, hz + 4), (-20, hz + 4)]), fill(hill_far))
    near = ridge(rng, -20, W + 20, hz - H * 0.004, H * 0.007, n=50)
    cv.drawPath(poly(near + [(W + 20, hz + 4), (-20, hz + 4)]), fill(hill_near))
    # water
    cv.drawRect(skia.Rect.MakeLTRB(0, hz, W, H), fill("#ffffff", shader=lin_grad((0, hz), (0, H), water, [0.0, 0.18, 0.55, 1.0])))
    # sun reflection column
    sx = sun[0]
    for k in range(70):
        y = hz + (H - hz) * (k / 70) ** 1.6
        wv = W * (0.02 + 0.10 * (y - hz) / (H - hz)) * rng.uniform(0.4, 1.0)
        x = sx + rng.normal(0, W * 0.03 * (1 + (y - hz) / (H - hz)))
        th = 1.0 + 3.0 * (y - hz) / (H - hz)
        cv.drawRect(skia.Rect.MakeXYWH(x - wv / 2, y, wv, th), fill(refl, alpha=rng.uniform(0.25, 0.6)))
    # gentle wave lines
    for k in range(60):
        y = hz + (H - hz) * rng.uniform(0.02, 1.0) ** 1.8
        x = rng.uniform(-0.1, 1.0) * W
        wv = W * rng.uniform(0.05, 0.22) * (0.3 + (y - hz) / (H - hz))
        th = 1.0 + 2.5 * (y - hz) / (H - hz)
        col = "#ffffff" if rng.uniform() < 0.5 else "#2f5f80"
        if tod != "morning":
            col = "#ffd1a0" if rng.uniform() < 0.5 else "#3a2f50"
        cv.drawRect(skia.Rect.MakeXYWH(x, y, wv, th), fill(col, alpha=0.18))
    # distant boats
    for (bx, by, sc) in [(0.62, 0.005, 1.0), (0.83, 0.012, 0.8), (0.33, 0.02, 1.3)]:
        boat(cv, W * bx, hz + H * by, 18 * sc, dark=(tod != "morning"))
    return dict(sun=sun, horizon=hz)


def boat(cv, x, y, s, dark=False, sail=True):
    hull = "#4a3426" if not dark else "#2a1d24"
    cv.drawPath(spline([(x - s, y - 0.1 * s), (x + s, y - 0.1 * s), (x + 0.7 * s, y + 0.25 * s), (x - 0.75 * s, y + 0.25 * s)], closed=True, corners=[0, 1, 2, 3]), fill(hull))
    if sail:
        cv.drawPath(poly([(x - 0.05 * s, y - 0.12 * s), (x - 0.05 * s, y - 1.7 * s), (x + 0.75 * s, y - 0.25 * s)]), fill("#efe6d6" if not dark else "#5a4060", alpha=0.95))
        cv.drawRect(skia.Rect.MakeXYWH(x - 0.08 * s, y - 1.8 * s, 0.06 * s, 1.7 * s), fill(hull))


def olive_tree(cv, x, y, s, col="#6a7a4a", dark="#4d5a36", trunk="#5a4a3a"):
    cv.drawPath(tapered([(x, y), (x + 0.1 * s, y - 0.5 * s), (x - 0.05 * s, y - 0.9 * s)], 0.22 * s, 0.1 * s), fill(trunk))
    rng = np.random.default_rng(int(x * 3 + y))
    path = skia.Path()
    for k in range(7):
        cx = x + rng.uniform(-0.6, 0.6) * s
        cy = y - s * (1.0 + rng.uniform(-0.25, 0.3))
        r = s * rng.uniform(0.3, 0.5)
        path.addOval(skia.Rect.MakeLTRB(cx - r, cy - r * 0.8, cx + r, cy + r * 0.8))
    cv.drawPath(path, fill(col))
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    cv.drawPath(path.makeOffset(0.15 * s, 0.18 * s) if hasattr(path, "makeOffset") else path, fill(dark, alpha=0.6))
    cv.restore()


def _fieldstone(cv, rng, path, x0, y0, x1, y1, base_col, sh=6.0):
    """Rough-laid basalt: rows of rounded, irregular stones with dark gaps, clipped to `path`."""
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    cv.drawPath(path, fill("#16120f", alpha=0.45))
    y = y0
    while y < y1:
        rh = sh * rng.uniform(0.75, 1.25)
        x = x0 - rng.uniform(0, sh * 1.5)
        while x < x1:
            sw = sh * rng.uniform(1.1, 2.4)
            g = rng.uniform(0.35, 0.9)
            pts = [(x + g + rng.uniform(-0.4, 0.4) * sh * 0.2, y + g), (x + sw - g, y + g + rng.uniform(-0.3, 0.3)),
                   (x + sw - g + rng.uniform(-0.5, 0.5), y + rh - g), (x + g, y + rh - g + rng.uniform(-0.3, 0.3))]
            col = mix(base_col, "#000000" if rng.random() < 0.5 else "#ffffff", rng.uniform(0.0, 0.14))
            cv.drawPath(spline(pts, closed=True), fill(col))
            cv.drawLine(x + g + 1, y + g + 0.6, x + sw - g - 1, y + g + 0.6, stroke("#ffffff", 0.8, alpha=0.12))
            x += sw
        y += rh
    cv.restore()


def house(cv, x, y, w, h, wall="#5c5650", light="#857c72", roof="#4a3a2c", sunlit_side=1):
    """Basalt house of rough fieldstone: front face + side face + flat roof with beams,
    weathered with roof drip stains and grime at the foot."""
    rng = np.random.default_rng(int(x + y))
    d = w * 0.35
    front_col, side_col = (light, wall) if sunlit_side > 0 else (wall, light)
    front = skia.Rect.MakeXYWH(x, y - h, w, h)
    front_p = skia.Path()
    front_p.addRect(front)
    side = poly([(x + w, y - h), (x + w + d, y - h - d * 0.35), (x + w + d, y - d * 0.35), (x + w, y)])
    sh = max(2.2, h / 7.5)
    cv.drawRect(front, fill(front_col))
    cv.drawPath(side, fill(side_col))
    _fieldstone(cv, rng, front_p, x, y - h, x + w, y, hexc(front_col), sh)
    _fieldstone(cv, rng, side, x + w, y - h - d * 0.35, x + w + d, y, hexc(side_col), sh * 0.8)
    for p_, x0, x1 in ((front_p, x, x + w), (side, x + w, x + w + d)):
        cv.save()
        cv.clipPath(p_, skia.ClipOp.kIntersect, True)
        # drip stains under the roof edge, grime splashed up from the ground
        _streaks(cv, rng, max(2, int(w / 25)), x0 + 2, x1 - 2, y - h - d * 0.35, (h * 0.3, h * 0.9), (sh * 0.8, sh * 1.8),
                 col="#141010", alpha=(0.12, 0.22), blur=1.2)
        cv.drawRect(skia.Rect.MakeLTRB(x0, y - h - d * 0.4, x1, y - h + sh * 1.5),
                    fill("#000000", shader=lin_grad((0, y - h), (0, y - h + sh * 1.5), [(0, 0, 0, 0.4), (0, 0, 0, 0.0)])))
        cv.drawRect(skia.Rect.MakeLTRB(x0, y - h * 0.3, x1, y),
                    fill("#000000", shader=lin_grad((0, y - h * 0.3), (0, y), [(0.08, 0.06, 0.04, 0.0), (0.08, 0.06, 0.04, 0.38)])))
        cv.restore()
    roofp = poly([(x - w * 0.03, y - h), (x + w * 1.03, y - h), (x + w + d + w * 0.03, y - h - d * 0.35), (x + d * 0.98, y - h - d * 0.35)])
    cv.drawPath(roofp, fill(roof))
    cv.drawLine(x - w * 0.03, y - h, x + w * 1.03, y - h, stroke("#000000", 1.4, alpha=0.35))
    for k in range(int(w / 9)):   # beam ends poking out under the roof
        bx = x + w * 0.05 + k * 9
        if bx < x + w - 3:
            cv.drawCircle(bx, y - h + 1.6, 1.3, fill("#2a2018", alpha=0.8))
    # door: worn wooden boards in a stone frame with a lintel
    dx, dw, dh = x + w * 0.4, w * 0.18, h * 0.55
    cv.drawRect(skia.Rect.MakeXYWH(dx - 2, y - dh - 3, dw + 4, 3), fill(mix(front_col, "#ffffff", 0.18)))
    cv.drawRect(skia.Rect.MakeXYWH(dx, y - dh, dw, dh), fill("#2c2420"))
    cv.drawLine(dx + dw / 2, y - dh, dx + dw / 2, y, stroke("#1a1410", 0.8, alpha=0.6))
    walls = skia.Path(front_p)
    walls.addPath(side)
    return walls


def shore_land(cv, W, H, tod="morning"):
    """Looking inland toward Capernaum: hills, houses, shore."""
    rng = np.random.default_rng(9)
    hz = H * 0.40
    if tod == "morning":
        sky(cv, W, H * 0.6, ["#6c9fd6", "#a5c6e6", "#e9eef0"], [0.0, 0.55, 1.0])
        glow(cv, W * 0.95, H * 0.12, W * 0.6, "#fff0d0", 0.55)
        for (x, y, w, h) in [(0.3, 0.1, 0.5, 0.04), (0.75, 0.2, 0.55, 0.035), (0.2, 0.27, 0.4, 0.03)]:
            cloud(cv, W * x, H * y, W * w, H * h, top="#ffffff", bottom="#dde6f0", alpha=0.85, blur=7, rng=rng)
        hill1, hill2, grass = "#9aa77a", "#7f8d5e", "#b9a77c"
        stone_w, stone_l = "#5a544e", "#8a8178"
    else:
        sky(cv, W, H * 0.6, ["#3a3466", "#8a5a84", "#e9917a"], [0.0, 0.55, 1.0])
        glow(cv, W * 0.0, H * 0.35, W * 0.7, "#ffab6b", 0.6)
        hill1, hill2, grass = "#6d5a6e", "#544660", "#8a6a62"
        stone_w, stone_l = "#3d3440", "#6a5560"
    h1 = ridge(rng, -20, W + 20, hz - H * 0.06, H * 0.03, n=40)
    cv.drawPath(poly(h1 + [(W + 20, H), (-20, H)]), fill(hill1))
    # olive groves on the hill
    for k in range(26):
        x = rng.uniform(0, W)
        y = hz - H * 0.03 + rng.uniform(0, H * 0.07)
        olive_tree(cv, x, y, rng.uniform(9, 16), col="#6f8150" if tod == "morning" else "#4a4256", dark="#4f5e38" if tod == "morning" else "#2f2a3c")
    h2 = ridge(rng, -20, W + 20, hz + H * 0.03, H * 0.012, n=30)
    cv.drawPath(poly(h2 + [(W + 20, H), (-20, H)]), fill(hill2))
    # town of basalt houses
    base = hz + H * 0.09
    town = skia.Path()
    for k in range(9):
        x = W * (-0.05 + k * 0.12) + rng.uniform(-10, 10)
        w = rng.uniform(70, 110)
        h = rng.uniform(45, 70)
        town.addPath(house(cv, x, base + rng.uniform(-8, 8), w, h, wall=stone_w, light=stone_l, sunlit_side=1))
    # synagogue (white limestone) in the town: coursed blocks, rain streaks, worn columns
    sx, sy = W * 0.58, base - 6
    trng = np.random.default_rng(19)   # own stream: the beach below keeps its layout
    face = skia.Rect.MakeXYWH(sx, sy - 120, 180, 120)
    cv.drawRect(face, fill("#e8dcc4" if tod == "morning" else "#a88a8c"))
    cv.save()
    cv.clipRect(face, True)
    for r in range(10):
        yy = sy - 120 + r * 12
        cv.drawLine(sx, yy, sx + 180, yy, stroke("#6a5a44", 1.0, alpha=0.3))
        for c in range(8):
            xx = sx + (r % 2) * 11 + c * 23 + trng.uniform(-3, 3)
            cv.drawLine(xx, yy, xx, yy + 12, stroke("#6a5a44", 0.9, alpha=0.25))
    _streaks(cv, trng, 9, sx + 2, sx + 178, sy - 120, (25, 90), (3, 7), col="#5a4a38", alpha=(0.12, 0.22), blur=1.5)
    cv.drawRect(skia.Rect.MakeLTRB(sx, sy - 30, sx + 180, sy),
                fill("#000000", shader=lin_grad((0, sy - 30), (0, sy), [(0.15, 0.1, 0.05, 0.0), (0.15, 0.1, 0.05, 0.35)])))
    cv.restore()
    cv.drawPath(poly([(sx - 8, sy - 120), (sx + 188, sy - 120), (sx + 90, sy - 160)]), fill("#d7c9ad" if tod == "morning" else "#8e7078"))
    cv.drawLine(sx - 8, sy - 120, sx + 188, sy - 120, stroke("#5a4a38", 1.5, alpha=0.4))
    for c in range(5):
        cr = skia.Rect.MakeXYWH(sx + 14 + c * 36, sy - 112, 10, 112)
        cv.drawRect(cr, fill("#cdbf9f" if tod == "morning" else "#8a6c74"))
        cv.drawRect(skia.Rect.MakeXYWH(cr.right() - 3.5, cr.top(), 3.5, cr.height()), fill("#000000", alpha=0.18))
        cv.drawRect(skia.Rect.MakeXYWH(cr.left() - 2, cr.top() - 4, 14, 4), fill("#ddd0b2" if tod == "morning" else "#9a7c82"))
        for k in range(4):
            jy = cr.top() + 18 + k * 24 + trng.uniform(-3, 3)
            cv.drawLine(cr.left(), jy, cr.right(), jy, stroke("#6a5a44", 0.9, alpha=0.3))
    town.addRect(face)
    town.addPath(poly([(sx - 8, sy - 120), (sx + 188, sy - 120), (sx + 90, sy - 160)]))
    grit(cv, trng, W, H, amp=0.16, octaves=((40, 0.4), (12, 0.35), (4, 0.25)), inside=town)
    # shore / beach
    beach = ridge(rng, -20, W + 20, base + H * 0.05, H * 0.008, n=20)
    cv.drawPath(poly(beach + [(W + 20, H), (-20, H)]), fill(grass))
    cv.drawRect(skia.Rect.MakeLTRB(0, base + H * 0.06, W, H), fill("#000000", shader=lin_grad((0, base + H * 0.06), (0, H), [(0, 0, 0, 0.0), (0.1, 0.05, 0.0, 0.35)])))
    # basalt pebbles
    for k in range(140):
        y = base + H * 0.07 + (H - base) * rng.uniform(0, 1) ** 1.5
        x = rng.uniform(0, W)
        r = 2 + 10 * (y - base) / (H - base)
        cv.drawPath(ellipse(x, y, r * 1.4, r * 0.8), fill("#4a4440" if tod == "morning" else "#2e2630", alpha=0.75))
    # nets on poles + beached boat
    for px in (0.12, 0.3):
        cv.drawRect(skia.Rect.MakeXYWH(W * px, base - 20, 5, 90), fill("#4a3a2a"))
    cv.drawPath(spline([(W * 0.12, base - 15), (W * 0.21, base + 15), (W * 0.3, base - 15)], closed=False), stroke("#6a5a48", 3, alpha=0.8))
    for k in range(9):
        x = W * (0.13 + k * 0.019)
        cv.drawLine(x, base - 12 + abs(k - 4) * 2, x, base + 40, stroke("#6a5a48", 1.2, alpha=0.6))
    boat(cv, W * 0.82, base + H * 0.085, 70, dark=(tod != "morning"), sail=False)
    return dict(horizon=hz, base=base)


def shore_wide(cv, W, H, tod="morning"):
    """Establishing view: lake to the left, a low beach and the town of Capernaum to the right."""
    rng = np.random.default_rng(21)
    info = shore_lake(cv, W, H, tod)
    hz = info["horizon"]
    morning = tod == "morning"
    # at dusk the land must read as land, not as more lake: warm olive-brown against the violet water
    grass = "#a4a874" if morning else "#5a4f37"
    sand = "#dccb9f" if morning else "#a88470"
    # distant hills behind the town on the right
    hills = ridge(rng, W * 0.45, W + 20, hz - H * 0.035, H * 0.012, n=24)
    cv.drawPath(poly(hills + [(W + 20, hz + 2), (W * 0.45, hz + 2)]), fill("#8f9a78" if morning else "#4f3d5e"))
    # low land: coastline curving from the far right edge of the horizon toward the bottom right
    coast = [(W * 0.52, hz + 1), (W * 0.60, hz + H * 0.03), (W * 0.66, hz + H * 0.09), (W * 0.71, hz + H * 0.2),
             (W * 0.75, hz + H * 0.36), (W * 0.78, H + 10)]
    land = spline(coast + [(W + 10, H + 10), (W + 10, hz - 2), (W * 0.7, hz - 2)], closed=True, corners=[5, 6, 7])
    cv.drawPath(land, fill(grass, shader=lin_grad((0, hz), (0, H), [mix(grass, "#ffffff", 0.15), grass, mix(grass, "#000000", 0.18)], [0.0, 0.4, 1.0])))
    # scrub and rocks on the land
    cv.save()
    cv.clipPath(land, skia.ClipOp.kIntersect, True)
    for k in range(70):
        u = rng.uniform() ** 0.7
        y = hz + (H - hz) * u
        x = W * (0.6 + 0.4 * rng.uniform()) + W * 0.2 * u
        r = 2.0 + 16.0 * u * rng.uniform(0.5, 1.0)
        col = mix(grass, "#1c2410" if morning else "#2a2418", rng.uniform(0.35, 0.6))
        cv.drawPath(ellipse(x, y, r * 1.6, r * 0.8), fill(col, alpha=0.8))
        cv.drawPath(ellipse(x - r * 0.3, y - r * 0.3, r * 0.9, r * 0.4), fill(mix(grass, "#ffffff" if morning else "#e0a070", 0.25), alpha=0.5))
    cv.restore()
    # wet sand + dry sand bands along the water
    beach = spline(coast + [(W * 0.94, H + 10), (W * 0.88, hz + H * 0.36), (W * 0.8, hz + H * 0.19), (W * 0.72, hz + H * 0.08), (W * 0.62, hz + H * 0.02)], closed=True, corners=[5, 6])
    cv.drawPath(beach, fill(sand))
    wet = spline(coast + [(W * 0.82, H + 10), (W * 0.79, hz + H * 0.36), (W * 0.74, hz + H * 0.2), (W * 0.68, hz + H * 0.09), (W * 0.6, hz + H * 0.03)], closed=True, corners=[5, 6])
    cv.drawPath(wet, fill("#b9a682" if morning else "#7c5e5a", alpha=0.8))
    cv.drawPath(spline(coast, closed=False), stroke("#ffffff", 2.0, alpha=0.5))
    # town: houses at increasing size toward the viewer
    for k in range(12):
        u = k / 11
        x = W * (0.70 + 0.27 * u) + rng.uniform(-8, 8)
        y = hz + H * (0.006 + 0.05 * u * u)
        sc = 0.35 + 0.9 * u
        house(cv, x, y, 34 * sc, 22 * sc, wall="#5a544e" if morning else "#3d3440", light="#8a8178" if morning else "#6a5560")
    for k in range(8):
        olive_tree(cv, W * rng.uniform(0.74, 1.0), hz + H * rng.uniform(0.0, 0.06), rng.uniform(5, 10),
                   col="#6f8150" if morning else "#4a4256", dark="#4f5e38" if morning else "#2f2a3c")
    # boats are drawn live (they move)
    return info


def _value_noise(rng, w, h, scale):
    """Smooth value noise in [-1, 1] with features about `scale` px across."""
    gw, gh = int(w / scale) + 3, int(h / scale) + 3
    g = rng.uniform(-1.0, 1.0, (gh, gw)).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) / scale
    xs = np.arange(w, dtype=np.float32) / scale
    y0 = ys.astype(int)
    x0 = xs.astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = (fy * fy * (3 - 2 * fy))[:, None]
    fx = (fx * fx * (3 - 2 * fx))[None, :]
    top = g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx
    bot = g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx
    return top * (1 - fy) + bot * fy


def grit(cv, rng, W, H, amp=0.2, octaves=((140, 0.42), (40, 0.3), (12, 0.18), (4, 0.1)), rect=None, holes=None, inside=None):
    """Weathering: soft-light a multi-scale mottle over whatever stone is already drawn
    (inside `rect` / the `inside` path, skipping the `holes` path)."""
    n = sum(a * _value_noise(rng, W, H, s) for s, a in octaves)
    v = (np.clip(0.5 + amp * n / (np.std(n) * 2.5 + 1e-6), 0.0, 1.0) * 255).astype(np.uint8)
    img = skia.Image.fromarray(np.ascontiguousarray(np.dstack([v, v, v, np.full_like(v, 255)])),
                               colorType=skia.kRGBA_8888_ColorType)
    p = skia.Paint()
    p.setBlendMode(skia.BlendMode.kSoftLight)
    cv.save()
    if rect is not None:
        cv.clipRect(rect, True)
    if inside is not None:
        cv.clipPath(inside, skia.ClipOp.kIntersect, True)
    if holes is not None:
        cv.clipPath(holes, skia.ClipOp.kDifference, True)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(), p)
    cv.restore()


def _pits(cv, rng, n, x0, x1, y0, y1, rmax=2.0):
    """Small weathered pits: dark hollow with a lit lower lip (light comes from above)."""
    for _ in range(n):
        px, py = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(0.6, rmax)
        cv.drawCircle(px, py + 0.8, r, fill("#f4dfb8", alpha=0.12))
        cv.drawCircle(px, py, r, fill("#271b12", alpha=rng.uniform(0.22, 0.42)))


def _crack(cv, rng, x, y, dx, dy, length, steps=6):
    pts = [(x, y)]
    for _ in range(steps):
        x += dx * length / steps + rng.uniform(-4, 4) * abs(dy)
        y += dy * length / steps + rng.uniform(-4, 4) * abs(dx)
        pts.append((x, y))
    cv.drawPath(poly([(px, py + 0.9) for px, py in pts], closed=False), stroke("#f0dab2", 1.1, alpha=0.13))
    cv.drawPath(poly(pts, closed=False), stroke("#1e140c", 1.0, alpha=0.45))


def _stone_block(cv, rng, x0, y0, x1, y1, shader):
    """One dressed limestone block inside its mortar bed: worn arrises, chipped corners,
    its own tone, a lit top edge, a shadowed lower edge, pits and the odd hairline crack."""
    mt, mr, mb, ml = rng.uniform(1.2, 2.6, 4)
    L, T, R, B = x0 + ml, y0 + mt, x1 - mr, y1 - mb
    if R - L < 8 or B - T < 8:
        return

    def corner(cx, cy, sx, sy, first):
        chip = rng.random() < 0.2
        a = rng.uniform(4, 11) if chip else rng.uniform(1.0, 2.4)
        b = rng.uniform(3, 9) if chip else rng.uniform(1.0, 2.4)
        p_edge_y = (cx, cy + sy * b)
        p_mid = (cx + sx * a * rng.uniform(0.3, 0.6), cy + sy * b * rng.uniform(0.3, 0.6))
        p_edge_x = (cx + sx * a, cy)
        return [p_edge_y, p_mid, p_edge_x] if first else [p_edge_x, p_mid, p_edge_y]

    def edge(p0, p1, nrm):
        out = []
        for u in sorted(rng.uniform(0.15, 0.85, 2)):
            j = rng.uniform(-0.8, 0.8)
            out.append((p0[0] + (p1[0] - p0[0]) * u + nrm[0] * j, p0[1] + (p1[1] - p0[1]) * u + nrm[1] * j))
        return out

    pts = corner(L, T, 1, 1, True) + edge((L, T), (R, T), (0, 1))
    pts += corner(R, T, -1, 1, False) + edge((R, T), (R, B), (1, 0))
    pts += corner(R, B, -1, -1, True) + edge((R, B), (L, B), (0, 1))
    pts += corner(L, B, 1, -1, False) + edge((L, B), (L, T), (1, 0))
    path = poly(pts)
    cv.drawPath(path, fill("#ffffff", shader=shader))
    tone = rng.normal(0.0, 1.0)
    if tone < 0:
        cv.drawPath(path, fill("#2a1d13", alpha=min(0.17, -tone * 0.065)))
    else:
        cv.drawPath(path, fill("#fff0d2", alpha=min(0.13, tone * 0.05)))
    if rng.random() < 0.35:   # grey-buff or ochre beds in the limestone
        cv.drawPath(path, fill("#8d887e" if rng.random() < 0.55 else "#b4864c", alpha=rng.uniform(0.07, 0.15)))
    cv.save()
    cv.clipPath(path, skia.ClipOp.kIntersect, True)
    cv.drawLine(L, T + 1.1, R, T + 1.1, stroke("#f7e4bf", 2.2, alpha=0.2, blur=0.6))
    cv.drawLine(L, B - 1.3, R, B - 1.3, stroke("#21160e", 2.6, alpha=0.3, blur=0.6))
    cv.drawLine(R - 1.1, T, R - 1.1, B, stroke("#21160e", 2.0, alpha=0.14, blur=0.6))
    if rng.random() < 0.3:   # eroded, darker patch on the face
        cv.drawPath(ellipse(rng.uniform(L, R), rng.uniform(T, B), rng.uniform(8, 26), rng.uniform(5, 14)),
                    fill("#33251a", alpha=rng.uniform(0.07, 0.14), blur=5))
    _pits(cv, rng, rng.poisson(3.5), L + 3, R - 3, T + 3, B - 3)
    if rng.random() < 0.08:
        if rng.random() < 0.5:
            _crack(cv, rng, rng.uniform(L + 8, R - 8), T, rng.uniform(-0.25, 0.25), 1.0, (B - T) * rng.uniform(0.5, 1.0))
        else:
            _crack(cv, rng, L, rng.uniform(T + 6, B - 6), 1.0, rng.uniform(-0.15, 0.15), (R - L) * rng.uniform(0.3, 0.6))
    cv.restore()


def ashlar(cv, rng, W, y_top, y_bot, shader, course=(54, 70), length=(72, 135)):
    """Coursed limestone wall: darken everything to mortar, then lay each block back on top."""
    cv.drawRect(skia.Rect.MakeLTRB(0, y_top, W, y_bot), fill("#2d2118", alpha=0.55))
    y = y_top
    while y < y_bot - 4:
        y1 = min(y + rng.uniform(*course), y_bot)
        x = -rng.uniform(10, 100)
        while x < W:
            bw = rng.uniform(*length)
            _stone_block(cv, rng, x, y, x + bw, y1, shader)
            x += bw
        y = y1


def _streaks(cv, rng, n, x0, x1, y0, length, width, col="#36281b", alpha=(0.08, 0.16), blur=3.5):
    """Water / soot run-off streaks running down the stone."""
    for _ in range(n):
        x = rng.uniform(x0, x1)
        ln = rng.uniform(*length)
        ph = rng.uniform(0, 6.28)
        pts = [(x + 2.5 * math.sin(k * 0.8 + ph), y0 + ln * k / 8) for k in range(9)]
        cv.drawPath(tapered(pts, rng.uniform(*width), 1.0), fill(col, alpha=rng.uniform(*alpha), blur=blur))


def _column(cv, rng, x, cw, top, bot, eye_y, H):
    """Weathered stone column: shaded shaft built of drums, run-off streaks, chips, grime at the
    foot, and a worn capital that throws a shadow onto the shaft."""
    rect = skia.Rect.MakeLTRB(x - cw / 2, top, x + cw / 2, bot)
    cv.drawRect(rect, fill("#ffffff", shader=lin_grad((x - cw / 2, 0), (x + cw / 2, 0),
                                                      ["#7a6248", "#d8c09a", "#b89a72", "#5e4a36"], [0.0, 0.35, 0.65, 1.0])))
    cap_y = H * 0.06
    cv.save()
    cv.clipRect(rect, True)
    # drum joints: circles seen from the eye line bow up above it and sag below it
    y = cap_y + H * 0.03 + rng.uniform(50, 150)
    while y < bot - 30:
        sag = (y - eye_y) * 0.014
        j = skia.Path()
        j.moveTo(x - cw / 2, y)
        j.quadTo(x, y + 2 * sag, x + cw / 2, y)
        lit = skia.Path(j)
        lit.offset(0, 1.6)
        cv.drawPath(lit, stroke("#f2ddb5", 1.3, alpha=0.18))
        cv.drawPath(j, stroke("#271a10", 1.8, alpha=0.42))
        if rng.random() < 0.6:   # chipped drum edge
            side = 1 if rng.random() < 0.5 else -1
            u = rng.uniform(0.2, 0.42) * side
            cx = x + u * cw
            cy = y + sag * (1 - (2 * u) ** 2)
            a, b = rng.uniform(4, 9), rng.uniform(3, 7)
            chip = poly([(cx - a, cy), (cx - a * 0.3, cy + b * rng.uniform(0.6, 1.0)), (cx + a * 0.6, cy + b * 0.5), (cx + a, cy)])
            cv.drawPath(chip, fill("#2a1c12", alpha=0.32))
            cv.drawLine(cx - a * 0.3, cy + b * 0.9, cx + a * 0.6, cy + b * 0.5 + 0.6, stroke("#f0dab2", 1.0, alpha=0.18))
        y += rng.uniform(140, 210)
    _streaks(cv, rng, int(rng.integers(3, 7)), x - cw * 0.38, x + cw * 0.38, top + H * 0.09, (80, 420), (3, 7),
             col="#2e2016", alpha=(0.07, 0.14), blur=1.8)
    for _ in range(int(rng.integers(1, 3))):   # long vertical weather lines on the shaft
        sx = x + rng.uniform(-0.3, 0.3) * cw
        sy = rng.uniform(top + H * 0.12, bot - 300)
        _crack(cv, rng, sx, sy, rng.uniform(-0.05, 0.05), 1.0, rng.uniform(60, 160), steps=8)
    _pits(cv, rng, int(rng.poisson(45)), x - cw * 0.46, x + cw * 0.46, top + H * 0.09, bot, rmax=1.8)
    # grime rising from the foot and the shadow under the capital
    cv.drawRect(skia.Rect.MakeLTRB(x - cw / 2, bot - 170, x + cw / 2, bot),
                fill("#000000", shader=lin_grad((0, bot - 170), (0, bot), [(0.12, 0.08, 0.05, 0.0), (0.12, 0.08, 0.05, 0.42)])))
    cv.drawRect(skia.Rect.MakeLTRB(x - cw / 2, cap_y, x + cw / 2, cap_y + H * 0.03 + 60),
                fill("#000000", shader=lin_grad((0, cap_y + H * 0.03), (0, cap_y + H * 0.03 + 60), [(0.1, 0.06, 0.03, 0.4), (0.1, 0.06, 0.03, 0.0)])))
    cv.restore()
    # capital: rounded echinus under a square abacus, both worn and chipped
    ech = skia.Rect.MakeLTRB(x - cw * 0.58, cap_y + H * 0.03 - 4, x + cw * 0.58, cap_y + H * 0.03 + 16)
    cv.drawRoundRect(ech, 10, 10, fill("#ffffff", shader=lin_grad((ech.left(), 0), (ech.right(), 0),
                                                                   ["#8a7052", "#d2b88e", "#a88a64", "#6a543c"], [0.0, 0.35, 0.65, 1.0])))
    aba = skia.Rect.MakeXYWH(x - cw * 0.65, cap_y, cw * 1.3, H * 0.03)
    cv.drawRect(aba, fill("#ffffff", shader=lin_grad((0, aba.top()), (0, aba.bottom()), ["#d9c098", "#c3a77e", "#9c8160"])))
    cv.drawLine(aba.left(), aba.top() + 1, aba.right(), aba.top() + 1, stroke("#f4e2be", 2.0, alpha=0.4))
    cv.drawLine(aba.left(), aba.bottom() - 1, aba.right(), aba.bottom() - 1, stroke("#3a2a1c", 2.0, alpha=0.4))
    for _ in range(int(rng.integers(2, 5))):
        ex = rng.uniform(aba.left() + 4, aba.right() - 4)
        ey = aba.bottom() if rng.random() < 0.6 else aba.top()
        s = 1 if ey == aba.top() else -1
        a, b = rng.uniform(3, 8), rng.uniform(2, 6)
        cv.drawPath(poly([(ex - a, ey), (ex, ey + s * b), (ex + a, ey)]), fill("#3b2b1d", alpha=0.45))
    cv.save()
    cv.clipRect(aba, True)
    _pits(cv, rng, 25, aba.left(), aba.right(), aba.top(), aba.bottom(), rmax=1.6)
    cv.restore()


def _flagstones(cv, rng, W, H, y0, vy):
    """Worn floor flags in perspective: staggered slabs with their own tones, dark joints with a
    lit far arris, chipped corners, cracks, a polished walking path and dust."""
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, H), fill("#ffffff", shader=lin_grad((0, y0), (0, H), ["#7a5e44", "#4a3828"])))
    d_far = 6.0
    K = (y0 - vy) * d_far
    vx, f = W * 0.5, 900.0

    def P(xw, d):
        return (vx + xw * f / d, vy + K / d)

    ds = [d_far]
    while ds[-1] > 2.9:
        ds.append(ds[-1] - rng.uniform(0.42, 0.6))
    for i in range(len(ds) - 1):
        d0, d1 = ds[i], ds[i + 1]
        xw = -4.6 + rng.uniform(0.0, 1.0)
        jw = 5.5 / d1
        while xw < 4.6:
            sw = rng.uniform(0.75, 1.35)
            q = [P(xw, d0), P(xw + sw, d0), P(xw + sw, d1), P(xw, d1)]
            xw += sw
            if q[1][0] < -60 or q[0][0] > W + 60:
                continue
            slab = poly(q)
            tone = rng.normal(0.0, 1.0)
            cv.drawPath(slab, fill("#1e140c" if tone < 0 else "#f3dcb4", alpha=min(0.16, abs(tone) * 0.06)))
            if rng.random() < 0.3:
                cv.drawPath(slab, fill("#857f74" if rng.random() < 0.5 else "#a87c48", alpha=rng.uniform(0.06, 0.12)))
            cv.save()
            cv.clipPath(slab, skia.ClipOp.kIntersect, True)
            cx, cy = (q[0][0] + q[2][0]) / 2, (q[0][1] + q[2][1]) / 2
            sx = (q[2][0] - q[3][0]) / 2
            sy = (q[2][1] - q[0][1]) / 2
            if rng.random() < 0.35:   # worn hollow / stain on the slab
                cv.drawPath(ellipse(cx + rng.uniform(-0.4, 0.4) * sx, cy + rng.uniform(-0.3, 0.3) * sy,
                                    sx * rng.uniform(0.25, 0.6), sy * rng.uniform(0.25, 0.6)),
                            fill("#2a1d12", alpha=rng.uniform(0.06, 0.13), blur=6))
            _pits(cv, rng, int(rng.poisson(5)), q[3][0], q[2][0], q[0][1] + 2, q[2][1] - 2, rmax=1.2 + 6 / d1 * 0.2)
            if rng.random() < 0.1:
                _crack(cv, rng, q[3][0] + (q[2][0] - q[3][0]) * rng.uniform(0.2, 0.8), q[2][1], rng.uniform(-0.6, 0.6), -1.0,
                       2 * sy * rng.uniform(0.5, 1.0))
            for k in range(4):   # chipped corners
                if rng.random() < 0.18:
                    px, py = q[k]
                    a = rng.uniform(4, 10) / d1 * 3
                    sxn = 1 if k in (0, 3) else -1
                    syn = 1 if k in (0, 1) else -1
                    cv.drawPath(poly([(px, py), (px + sxn * a, py), (px + sxn * a * 0.3, py + syn * a * 0.45), (px, py + syn * a * 0.5)]),
                                fill("#1c120a", alpha=0.4))
            cv.restore()
            # joints: dark gap along the far and left edges, lit far arris just in front of it
            cv.drawLine(q[0][0], q[0][1] + jw * 0.6, q[1][0], q[1][1] + jw * 0.6, stroke("#f0d6ac", max(0.8, jw * 0.45), alpha=0.12))
            cv.drawLine(q[0][0], q[0][1], q[1][0], q[1][1], stroke("#1b120b", jw * 0.8, alpha=0.6))
            cv.drawLine(q[0][0], q[0][1], q[3][0], q[3][1], stroke("#1b120b", jw * 0.75, alpha=0.55))
    # polished path worn by feet, contact shadow under the bench, dust and grit
    cv.drawPath(ellipse(W * 0.5, H * 0.88, W * 0.42, (H - y0) * 0.35), fill("#e2c79a", alpha=0.09, blur=45))
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y0 + 46),
                fill("#000000", shader=lin_grad((0, y0), (0, y0 + 46), [(0.08, 0.05, 0.02, 0.5), (0.08, 0.05, 0.02, 0.0)])))
    for _ in range(140):
        y = y0 + 8 + (H - y0 - 8) * rng.uniform(0, 1) ** 1.2
        x = rng.uniform(0, W)
        s = 0.6 + 2.6 * (y - y0) / (H - y0)
        cv.drawPath(ellipse(x, y + s * 0.35, s * 1.3, s * 0.6), fill("#f0d8ae", alpha=0.12))
        cv.drawPath(ellipse(x, y, s * 1.2, s * 0.55), fill("#21170e", alpha=rng.uniform(0.25, 0.5)))


def _bench(cv, rng, W, y0, y1):
    """Long stone bench along the wall: blocky front, worn rounded seat edge, chips, grime."""
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), fill("#ffffff", shader=lin_grad((0, y0), (0, y1), ["#a58763", "#8e7253", "#6c553e"])))
    x = -rng.uniform(0, 160)
    while x < W:
        bw = rng.uniform(150, 280)
        tone = rng.normal(0.0, 1.0)
        r = skia.Rect.MakeLTRB(x + 1.5, y0 + 8, x + bw - 1.5, y1)
        cv.drawRect(r, fill("#1e140c" if tone < 0 else "#f3dcb4", alpha=min(0.14, abs(tone) * 0.05)))
        cv.drawLine(x, y0 + 8, x, y1, stroke("#22170e", 2.2, alpha=0.5))
        cv.drawLine(x + 2, y0 + 8, x + 2, y1, stroke("#e8d0a6", 1.0, alpha=0.15))
        cv.save()
        cv.clipRect(r, True)
        _pits(cv, rng, int(rng.poisson(10)), r.left(), r.right(), r.top(), r.bottom(), rmax=1.6)
        if rng.random() < 0.3:
            cv.drawPath(ellipse(rng.uniform(r.left(), r.right()), rng.uniform(r.top(), r.bottom()), rng.uniform(15, 40), rng.uniform(6, 14)),
                        fill("#2a1d12", alpha=0.1, blur=6))
        cv.restore()
        x += bw
    # seat: lit worn top with a rounded front arris
    cv.drawRect(skia.Rect.MakeLTRB(0, y0, W, y0 + 9), fill("#ffffff", shader=lin_grad((0, y0), (0, y0 + 9), ["#dcc49c", "#c3a67c"])))
    cv.drawLine(0, y0 + 9.5, W, y0 + 9.5, stroke("#3a2a1b", 2.0, alpha=0.35, blur=0.8))
    for _ in range(14):   # chips out of the seat edge
        ex = rng.uniform(0, W)
        a, b = rng.uniform(4, 12), rng.uniform(3, 7)
        cv.drawPath(poly([(ex - a, y0 + 9), (ex - a * 0.2, y0 + 9 - b), (ex + a * 0.5, y0 + 9 - b * 0.6), (ex + a, y0 + 9)]), fill("#5a4430", alpha=0.6))
    # grime and damp creeping up from the floor
    cv.drawRect(skia.Rect.MakeLTRB(0, y1 - 40, W, y1),
                fill("#000000", shader=lin_grad((0, y1 - 40), (0, y1), [(0.1, 0.07, 0.04, 0.0), (0.1, 0.07, 0.04, 0.45)])))


def synagogue(cv, W, H, view="front"):
    """Interior: weathered limestone walls, columns, high windows with light beams."""
    rng = np.random.default_rng(31 if view == "front" else 37)
    eye_y = H * 0.45
    floor_y = H * 0.70
    bench_y = floor_y - H * 0.05
    wall_grad = lin_grad((0, 0), (0, H), ["#6b5440", "#a8875f", "#8a6a4a", "#5a4430"], [0.0, 0.35, 0.7, 1.0])
    # back wall: dressed blocks in mortar beds
    cv.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", shader=wall_grad))
    ashlar(cv, rng, W, 0, bench_y + 6, wall_grad)
    # rising damp at the foot of the wall with a pale salt tide line, soot and grime up high
    tide = ridge(rng, -20, W + 20, bench_y - 80, 16, n=40)
    cv.drawPath(spline(tide + [(W + 20, bench_y + 10), (-20, bench_y + 10)], closed=True, corners=[len(tide) - 1, len(tide), len(tide) + 1]),
                fill("#000000", blur=6, shader=lin_grad((0, bench_y - 110), (0, bench_y),
                                                         [(0.14, 0.1, 0.06, 0.12), (0.14, 0.1, 0.06, 0.42)])))
    cv.drawPath(spline(tide, closed=False), stroke("#ead9b6", 3.0, alpha=0.12, blur=2.0))
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, W, H * 0.12),
                fill("#000000", shader=lin_grad((0, 0), (0, H * 0.12), [(0.08, 0.05, 0.03, 0.35), (0.08, 0.05, 0.03, 0.0)])))
    windows = (0.22, 0.62) if view == "front" else (0.35, 0.8)
    for wx in windows:   # rain run-off below each sill
        _streaks(cv, rng, 6, W * wx - 4, W * (wx + 0.09) + 4, H * 0.21 + 8, (90, 380), (7, 16))
    # high windows: deep reveal in the thick wall, a worn sill, then the glow
    for wx in windows:
        x = W * wx
        r = skia.Rect.MakeXYWH(x, H * 0.08, W * 0.09, H * 0.13)
        jamb = r.makeOutset(8, 8)
        cv.drawRoundRect(jamb, 36, 36, fill("#5a4532"))
        cv.drawRoundRect(skia.Rect.MakeLTRB(jamb.left() + 2, jamb.top() + 2, jamb.right() - 2, jamb.bottom() - 2), 34, 34,
                         fill("#ffffff", shader=lin_grad((jamb.left(), 0), (jamb.right(), 0), ["#c9a97c", "#7d6249", "#6a523c", "#b8976c"], [0.0, 0.2, 0.8, 1.0])))
        cv.drawRoundRect(r, 30, 30, fill("#fff1cf"))
        sill = skia.Rect.MakeLTRB(jamb.left() - 8, r.bottom() + 2, jamb.right() + 8, r.bottom() + 13)
        cv.drawRect(sill, fill("#ffffff", shader=lin_grad((0, sill.top()), (0, sill.bottom()), ["#dcc39a", "#a88a64"])))
        cv.drawLine(sill.left(), sill.bottom() + 1.5, sill.right(), sill.bottom() + 1.5, stroke("#2a1d13", 3.0, alpha=0.35, blur=1.5))
        glow(cv, x + W * 0.045, H * 0.145, W * 0.25, "#ffe2a6", 0.55)
    if view == "front":
        # niche (Torah ark) with curtain behind the speaker, framed by a worn stone surround
        nx, ny, nw, nh = W * 0.38, H * 0.38, W * 0.24, H * 0.26
        frame = skia.Rect.MakeXYWH(nx - 14, ny - 14, nw + 28, nh + 14)
        cv.drawRoundRect(frame, 94, 94, fill("#ffffff", shader=lin_grad((frame.left(), 0), (frame.right(), 0),
                                                                         ["#7d6448", "#cdb38b", "#b39570", "#6a543c"], [0.0, 0.3, 0.7, 1.0])))
        cv.save()
        cv.clipRRect(skia.RRect.MakeRectXY(frame, 94, 94), skia.ClipOp.kIntersect, True)
        for k in range(9):   # voussoir joints radiating from the arch centre
            a = math.pi * (k + 0.5) / 9
            cx, cy = nx + nw / 2, ny + 80
            cv.drawLine(cx - math.cos(a) * (nw / 2 - 30), cy - math.sin(a) * 60, cx - math.cos(a) * (nw / 2 + 30), cy - math.sin(a) * 120,
                        stroke("#2a1d13", 1.6, alpha=0.4))
        for y in (ny + nh * 0.45, ny + nh * 0.75):
            cv.drawLine(frame.left(), y, frame.right(), y, stroke("#2a1d13", 1.6, alpha=0.4))
        _pits(cv, rng, 60, frame.left(), frame.right(), frame.top(), frame.bottom(), rmax=1.6)
        cv.restore()
        cv.drawRoundRect(skia.Rect.MakeXYWH(nx, ny, nw, nh), 80, 80, fill("#3a2a1e"))
        cur = skia.Rect.MakeXYWH(nx + nw * 0.12, ny + nh * 0.3, nw * 0.76, nh * 0.7)
        folds = ["#5c2222", "#76302e", "#62262a", "#7a3432", "#5a2222", "#72302e", "#5e2426"]
        cv.drawRect(cur, fill("#ffffff", shader=lin_grad((cur.left(), 0), (cur.right(), 0), folds)))
        for k in range(6):
            cv.drawLine(nx + nw * (0.18 + k * 0.12), ny + nh * 0.3, nx + nw * (0.18 + k * 0.12), ny + nh, stroke("#4a1a1a", 3, alpha=0.5, blur=1.2))
        cv.drawRect(skia.Rect.MakeLTRB(cur.left(), cur.top(), cur.right(), cur.top() + 26),
                    fill("#000000", shader=lin_grad((0, cur.top()), (0, cur.top() + 26), [(0.05, 0.02, 0.02, 0.45), (0.05, 0.02, 0.02, 0.0)])))
        cv.drawRect(skia.Rect.MakeXYWH(nx - 10, ny + nh, nw + 20, 18), fill("#ffffff", shader=lin_grad((0, ny + nh), (0, ny + nh + 18), ["#d6be96", "#a88c66"])))
        cv.drawLine(nx - 10, ny + nh + 19, nx + nw + 10, ny + nh + 19, stroke("#2a1d13", 2.5, alpha=0.4, blur=1.2))
    # columns
    for cx in (0.06, 0.94) if view == "front" else (0.1, 0.5, 0.9):
        _column(cv, rng, W * cx, W * 0.11, 0, bench_y + 6, eye_y, H)
    # stone bench and floor
    _bench(cv, rng, W, bench_y, floor_y)
    _flagstones(cv, rng, W, H, floor_y, H * 0.40)
    # one pass of grit over every stone surface (not the window glass)
    panes = skia.Path()
    for wx in windows:
        panes.addRoundRect(skia.Rect.MakeXYWH(W * wx, H * 0.08, W * 0.09, H * 0.13), 30, 30)
    grit(cv, rng, W, H, rect=skia.Rect.MakeLTRB(0, 0, W, floor_y), holes=panes)
    grit(cv, rng, W, H, amp=0.12, octaves=((90, 0.35), (30, 0.3), (10, 0.22), (4, 0.13)), rect=skia.Rect.MakeLTRB(0, floor_y, W, H))
    # hanging oil lamps
    for lx in (0.3, 0.72):
        x = W * lx
        cv.drawLine(x, 0, x, H * 0.28, stroke("#2a1e14", 2))
        cv.drawPath(ellipse(x, H * 0.29, 16, 7), fill("#7a5a2a"))
        glow(cv, x, H * 0.275, 70, "#ffcf7a", 0.75)
    # warm vignette
    cv.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", shader=rad_grad((W * 0.5, H * 0.45), H * 0.75, [(0, 0, 0, 0.0), (0.1, 0.05, 0.0, 0.45)])))
    return dict(windows=[(0.22, 0.08), (0.62, 0.08)] if view == "front" else [(0.35, 0.08), (0.8, 0.08)])


def beach_fore(cv, W, H, tod="morning", y0=0.70):
    """Foreground beach (sand, wet edge, pebbles, a beached boat) over a lake view."""
    rng = np.random.default_rng(41 if tod == "morning" else 43)
    morning = tod == "morning"
    sand = "#d7c29a" if morning else "#8c6a68"
    wet = "#b19d78" if morning else "#6a5060"
    top = H * y0
    edge = [(-20, top + 18)]
    for k in range(1, 12):
        edge.append((W * k / 11, top + 14 * math.sin(k * 1.3) + 10 * math.sin(k * 0.6 + 1)))
    edge.append((W + 20, top + 6))
    land = edge + [(W + 20, H + 20), (-20, H + 20)]
    # foam line + wet sand
    cv.drawPath(spline([(x, y - 6) for x, y in edge], closed=False), stroke("#ffffff" if morning else "#ffd8b0", 5, alpha=0.6, blur=1.5))
    cv.drawPath(spline(land, closed=True, corners=[len(edge) - 1, len(edge), len(edge) + 1]), fill(wet))
    dry = [(x, y + 26 + 8 * math.sin(x * 0.01)) for x, y in edge]
    cv.drawPath(spline(dry + [(W + 20, H + 20), (-20, H + 20)], closed=True), fill(sand, shader=lin_grad((0, top), (0, H), [mix(sand, "#ffffff", 0.08), sand, mix(sand, "#000000", 0.12)], [0.0, 0.5, 1.0])))
    for k in range(120):
        y = top + 40 + (H - top - 40) * rng.uniform(0, 1) ** 1.3
        x = rng.uniform(0, W)
        r = 2 + 9 * (y - top) / (H - top)
        cv.drawPath(ellipse(x, y, r * 1.4, r * 0.7), fill("#4a4440" if morning else "#2e2630", alpha=0.6))
    boat(cv, W * 0.86, top + H * 0.06, 85, dark=not morning, sail=False)
    return dict()


def beach_view(cv, W, H, tod="morning"):
    info = shore_lake(cv, W, H, tod)
    beach_fore(cv, W, H, tod)
    return info


PLATES = {
    "lake_morning": lambda cv, W, H: shore_lake(cv, W, H, "morning"),
    "land_morning": lambda cv, W, H: shore_land(cv, W, H, "morning"),
    "wide_morning": lambda cv, W, H: shore_wide(cv, W, H, "morning"),
    "syn_front": lambda cv, W, H: synagogue(cv, W, H, "front"),
    "syn_side": lambda cv, W, H: synagogue(cv, W, H, "side"),
    "lake_dusk": lambda cv, W, H: shore_lake(cv, W, H, "dusk"),
    "land_dusk": lambda cv, W, H: shore_land(cv, W, H, "dusk"),
    "wide_dusk": lambda cv, W, H: shore_wide(cv, W, H, "dusk"),
    "beach_morning": lambda cv, W, H: beach_view(cv, W, H, "morning"),
    "beach_dusk": lambda cv, W, H: beach_view(cv, W, H, "dusk"),
}

_cache = {}


def plate(name, blur=0.0):
    key = (name, round(blur, 1))
    if key in _cache:
        return _cache[key]
    surf = skia.Surface(PW, PH)
    cv = surf.getCanvas()
    cv.clear(skia.ColorBLACK)
    info = PLATES[name](cv, PW, PH)
    img = surf.makeImageSnapshot()
    if blur > 0:
        s2 = skia.Surface(PW, PH)
        c2 = s2.getCanvas()
        p = skia.Paint()
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur, skia.TileMode.kClamp))
        c2.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        img = s2.makeImageSnapshot()
    _cache[key] = (img, info)
    return _cache[key]


def draw_plate(cv, name, cam, W, H, blur=0.0):
    """cam = (cx, cy, zoom) in plate fractions; zoom 1 => frame shows W x H plate pixels."""
    img, info = plate(name, blur)
    cx, cy, z = cam
    # keep the frame inside the plate
    hx = W / (2 * z * PW)
    hy = H / (2 * z * PH)
    cx = min(max(cx, hx), 1 - hx)
    cy = min(max(cy, hy), 1 - hy)
    cv.save()
    cv.translate(W / 2, H / 2)
    cv.scale(z, z)
    cv.translate(-cx * PW, -cy * PH)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    cv.restore()
    return info
