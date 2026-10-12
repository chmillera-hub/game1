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


def house(cv, x, y, w, h, wall="#5c5650", light="#857c72", roof="#4a3a2c", sunlit_side=1):
    """Simple basalt house: front face + side face + flat roof with beams."""
    d = w * 0.35
    front = skia.Rect.MakeXYWH(x, y - h, w, h)
    cv.drawRect(front, fill(light if sunlit_side > 0 else wall))
    side = poly([(x + w, y - h), (x + w + d, y - h - d * 0.35), (x + w + d, y - d * 0.35), (x + w, y)])
    cv.drawPath(side, fill(wall if sunlit_side > 0 else light))
    roofp = poly([(x - w * 0.03, y - h), (x + w * 1.03, y - h), (x + w + d + w * 0.03, y - h - d * 0.35), (x + d * 0.98, y - h - d * 0.35)])
    cv.drawPath(roofp, fill(roof))
    # door
    cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.4, y - h * 0.55, w * 0.18, h * 0.55), fill("#2c2420"))
    # stone texture dots
    rng = np.random.default_rng(int(x + y))
    for k in range(int(w * h / 900)):
        px = x + rng.uniform(0.03, 0.97) * w
        py = y - rng.uniform(0.05, 0.95) * h
        cv.drawRect(skia.Rect.MakeXYWH(px, py, rng.uniform(4, 10), rng.uniform(2, 4)), fill("#3e3a36", alpha=0.25))


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
    for k in range(9):
        x = W * (-0.05 + k * 0.12) + rng.uniform(-10, 10)
        w = rng.uniform(70, 110)
        h = rng.uniform(45, 70)
        house(cv, x, base + rng.uniform(-8, 8), w, h, wall=stone_w, light=stone_l, sunlit_side=1)
    # synagogue (white limestone) in the town
    sx, sy = W * 0.58, base - 6
    cv.drawRect(skia.Rect.MakeXYWH(sx, sy - 120, 180, 120), fill("#e8dcc4" if tod == "morning" else "#a88a8c"))
    cv.drawPath(poly([(sx - 8, sy - 120), (sx + 188, sy - 120), (sx + 90, sy - 160)]), fill("#d7c9ad" if tod == "morning" else "#8e7078"))
    for c in range(5):
        cv.drawRect(skia.Rect.MakeXYWH(sx + 14 + c * 36, sy - 112, 10, 112), fill("#cdbf9f" if tod == "morning" else "#8a6c74"))
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


def synagogue(cv, W, H, view="front"):
    """Interior: limestone walls, columns, high windows with light beams."""
    rng = np.random.default_rng(31 if view == "front" else 37)
    # back wall
    cv.drawRect(skia.Rect.MakeWH(W, H), fill("#ffffff", shader=lin_grad((0, 0), (0, H), ["#6b5440", "#a8875f", "#8a6a4a", "#5a4430"], [0.0, 0.35, 0.7, 1.0])))
    # stone block courses
    for row in range(26):
        y = row * H / 26
        cv.drawLine(0, y, W, y, stroke("#4e3c2c", 1.6, alpha=0.35))
        off = (row % 2) * 45
        for col in range(12):
            x = off + col * 90
            cv.drawLine(x, y, x, y + H / 26, stroke("#4e3c2c", 1.2, alpha=0.3))
    # high windows with glow
    for wx in (0.22, 0.62) if view == "front" else (0.35, 0.8):
        x = W * wx
        r = skia.Rect.MakeXYWH(x, H * 0.08, W * 0.09, H * 0.13)
        cv.drawRoundRect(r, 30, 30, fill("#fff1cf"))
        glow(cv, x + W * 0.045, H * 0.145, W * 0.25, "#ffe2a6", 0.55)
    if view == "front":
        # niche (Torah ark) with curtain behind the speaker
        nx, ny, nw, nh = W * 0.38, H * 0.38, W * 0.24, H * 0.26
        cv.drawRoundRect(skia.Rect.MakeXYWH(nx, ny, nw, nh), 80, 80, fill("#3a2a1e"))
        cv.drawRect(skia.Rect.MakeXYWH(nx + nw * 0.12, ny + nh * 0.3, nw * 0.76, nh * 0.7), fill("#6b2a2a"))
        for k in range(6):
            cv.drawLine(nx + nw * (0.18 + k * 0.12), ny + nh * 0.3, nx + nw * (0.18 + k * 0.12), ny + nh, stroke("#4a1a1a", 3, alpha=0.6))
        cv.drawRect(skia.Rect.MakeXYWH(nx - 10, ny + nh, nw + 20, 18), fill("#c9b18a"))
    # columns
    cols = (0.06, 0.94) if view == "front" else (0.1, 0.5, 0.9)
    for cx in cols:
        x = W * cx
        cw = W * 0.11
        cv.drawRect(skia.Rect.MakeXYWH(x - cw / 2, 0, cw, H), fill("#ffffff", shader=lin_grad((x - cw / 2, 0), (x + cw / 2, 0), ["#7a6248", "#d8c09a", "#b89a72", "#5e4a36"], [0.0, 0.35, 0.65, 1.0])))
        cv.drawRect(skia.Rect.MakeXYWH(x - cw * 0.65, H * 0.06, cw * 1.3, H * 0.03), fill("#c9ae86"))
    # stone benches / floor
    floor_y = H * 0.70
    cv.drawRect(skia.Rect.MakeLTRB(0, floor_y, W, H), fill("#ffffff", shader=lin_grad((0, floor_y), (0, H), ["#7a5e44", "#4a3828"])))
    cv.drawRect(skia.Rect.MakeLTRB(0, floor_y - H * 0.05, W, floor_y), fill("#9a7e5c"))
    cv.drawRect(skia.Rect.MakeLTRB(0, floor_y - H * 0.05, W, floor_y - H * 0.045), fill("#c9ae86"))
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
