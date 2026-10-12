"""Per-frame effects: glows, god rays, bokeh, sparkles, beams, dust, boats,
crowds, departing figures, bread prop, color grades, vignette."""
import math

import numpy as np
import skia

import bg
from gfx import ellipse, fill, hexc, lin_grad, poly, rad_grad, sample_spline, spline, stroke, tapered


def screen_pt(px, py, pcam, W, H):
    cx, cy, z = pcam
    hx = W / (2 * z * bg.PW)
    hy = H / (2 * z * bg.PH)
    cx = min(max(cx, hx), 1 - hx)
    cy = min(max(cy, hy), 1 - hy)
    return (W / 2 + (px - cx * bg.PW) * z, H / 2 + (py - cy * bg.PH) * z)


def _additive():
    return skia.BlendMode.kScreen


def sun_glow(cv, W, H, t, info, pcam, strength=1.0, col="#fff3d8"):
    if "sun" not in info:
        return
    x, y = screen_pt(*info["sun"], pcam, W, H)
    pulse = 1.0 + 0.04 * math.sin(t * 0.9)
    c = hexc(col)
    r = W * 0.75 * pulse
    p = fill(col, shader=rad_grad((x, y), r, [(c[0], c[1], c[2], 0.55 * strength), (c[0], c[1], c[2], 0.18 * strength), (c[0], c[1], c[2], 0.0)], [0.0, 0.35, 1.0]))
    p.setBlendMode(_additive())
    cv.drawRect(skia.Rect.MakeWH(W, H), p)


def god_rays(cv, W, H, t, info, pcam, strength=1.0, origin=None, col="#fff0cf", n=7, spread=0.9, length=1.6):
    if origin is None:
        if "sun" not in info:
            return
        origin = screen_pt(*info["sun"], pcam, W, H)
    ox, oy = origin
    rng = np.random.default_rng(3)
    c = hexc(col)
    for k in range(n):
        base = rng.uniform(-spread, spread) + 0.6
        ang = base + 0.025 * math.sin(t * 0.25 + k)
        wdt = rng.uniform(0.03, 0.08)
        L = H * length
        a1, a2 = ang - wdt, ang + wdt
        pts = [(ox, oy), (ox + math.cos(a1) * L, oy + math.sin(a1) * L), (ox + math.cos(a2) * L, oy + math.sin(a2) * L)]
        al = (0.06 + 0.05 * math.sin(t * 0.5 + k * 1.7)) * strength
        p = fill(col, shader=rad_grad((ox, oy), L, [(c[0], c[1], c[2], al), (c[0], c[1], c[2], 0.0)]), blur=6)
        p.setBlendMode(_additive())
        cv.drawPath(poly(pts), p)


def bokeh(cv, W, H, t, seed, cols, n=14, region=(0.0, 0.45, 1.0, 1.0), rmin=10, rmax=30, alpha=0.22):
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = region
    for k in range(n):
        x = (rng.uniform(x0, x1) + 0.01 * math.sin(t * 0.2 + k)) * W
        y = (rng.uniform(y0, y1) + 0.006 * math.cos(t * 0.17 + k * 2)) * H
        r = rng.uniform(rmin, rmax)
        col = cols[k % len(cols)]
        c = hexc(col)
        a = alpha * (0.55 + 0.45 * math.sin(t * rng.uniform(0.6, 1.6) + k))
        p = fill(col, shader=rad_grad((x, y), r, [(c[0], c[1], c[2], a), (c[0], c[1], c[2], a * 0.8), (c[0], c[1], c[2], 0.0)], [0.0, 0.75, 1.0]))
        p.setBlendMode(_additive())
        cv.drawCircle(x, y, r, p)


def water_sparkle(cv, W, H, t, info, pcam, col="#ffffff"):
    if "sun" not in info:
        return
    sx, _ = screen_pt(*info["sun"], pcam, W, H)
    _, hz = screen_pt(0, info["horizon"], pcam, W, H)
    rng = np.random.default_rng(11)
    for k in range(40):
        y = hz + (H - hz) * rng.uniform(0.01, 1.0) ** 1.7
        x = sx + rng.normal(0, 30 + 120 * (y - hz) / max(H - hz, 1))
        ph = rng.uniform(0, 6.28)
        a = max(0.0, math.sin(t * rng.uniform(2, 4) + ph)) ** 3
        if a < 0.05:
            continue
        w = 2 + 10 * (y - hz) / max(H - hz, 1)
        p = fill(col, alpha=0.85 * a)
        p.setBlendMode(_additive())
        cv.drawRect(skia.Rect.MakeXYWH(x - w / 2, y, w, 1.5), p)


def boats_moving(cv, W, H, t, t0, info, pcam):
    _, hz = screen_pt(0, info["horizon"], pcam, W, H)
    u = t - t0
    for k, (x0, y0, s, vx, vy) in enumerate([(0.10, 0.10, 2.4, 9, 3.0), (0.32, 0.18, 3.4, 11, 4.0), (0.05, 0.27, 4.4, 13, 5.0)]):
        x = W * x0 + vx * u
        y = hz + H * y0 + vy * u
        bob = 1.5 * math.sin(u * 1.4 + k)
        bg.boat(cv, x, y + bob, 15 * s)
        # oars / people silhouettes
        for j in range(3):
            px = x - 10 * s + j * 9 * s
            cv.drawPath(ellipse(px, y - 3.2 * s + bob, 1.6 * s, 2.0 * s), fill("#3a2a22"))
        # wake
        cv.drawPath(spline([(x - 18 * s, y + 4 * s), (x - 40 * s, y + 7 * s)], closed=False), stroke("#ffffff", 1.5, alpha=0.4))


def beams(cv, W, H, t, strength=1.0, windows=((0.18, -0.05), (0.62, -0.05))):
    c = hexc("#ffe2a8")
    for k, (wx, wy) in enumerate(windows):
        ox, oy = W * wx, H * wy
        ang = 1.12 + 0.02 * math.sin(t * 0.2 + k)
        L = H * 1.5
        w0, w1 = 50, 240
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        pts = [(ox - nx * w0, oy - ny * w0), (ox + nx * w0, oy + ny * w0),
               (ox + dx * L + nx * w1, oy + dy * L + ny * w1), (ox + dx * L - nx * w1, oy + dy * L - ny * w1)]
        a = (0.16 + 0.03 * math.sin(t * 0.6 + k * 2)) * strength
        p = fill("#ffe2a8", shader=lin_grad((ox, oy), (ox + dx * L, oy + dy * L), [(c[0], c[1], c[2], a), (c[0], c[1], c[2], a * 0.5), (c[0], c[1], c[2], 0.0)], [0.0, 0.5, 1.0]), blur=18)
        p.setBlendMode(_additive())
        cv.drawPath(poly(pts), p)


def dust(cv, W, H, t, n=36, seed=5):
    rng = np.random.default_rng(seed)
    for k in range(n):
        x0 = rng.uniform(0.0, 1.0)
        y0 = rng.uniform(0.0, 1.0)
        vx = rng.uniform(-0.004, 0.006)
        vy = rng.uniform(-0.003, 0.008)
        x = ((x0 + vx * t + 0.01 * math.sin(t * 0.7 + k)) % 1.0) * W
        y = ((y0 + vy * t) % 1.0) * H
        r = rng.uniform(1.0, 2.6)
        a = 0.35 + 0.35 * math.sin(t * 1.3 + k)
        p = fill("#fff2cc", alpha=max(0.0, a), blur=0.8)
        p.setBlendMode(_additive())
        cv.drawCircle(x, y, r, p)


def silhouette(cv, x, y, s, col="#2a1f2e", head_cloth=True, walk=0.0, rim="#ff9a5a", rim_side=1, facing=1, walking=True):
    """Backlit robed figure with arms and legs (feet at x,y; height ~ 7.4s).
    `walk` is the stride phase; facing -1 = seen from behind (walking away), +1 = turned toward us."""
    ph = walk * math.pi
    stride = math.sin(ph) if walking else 0.0
    bob = abs(math.sin(ph)) * 0.10 * s if walking else 0.0
    top = y - 6.2 * s - bob
    sh_y = y - 5.75 * s - bob
    parts = []
    # legs (lower legs below a calf-length robe), alternating steps
    for side in (-1, 1):
        lift = max(0.0, side * stride) * 0.45 * s
        fx_ = x + side * 0.22 * s + side * stride * 0.10 * s
        knee = (x + side * 0.24 * s, y - 2.2 * s - bob)
        foot = (fx_, y - lift)
        leg = tapered([knee, ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2), foot], 0.30 * s, 0.17 * s)
        parts.append(leg)
        parts.append(ellipse(foot[0] + side * 0.05 * s, foot[1], 0.24 * s, 0.09 * s))
    # robe
    robe = spline([(x - 0.72 * s, sh_y + 0.05 * s), (x - 0.62 * s, y - 4.0 * s - bob), (x - 0.78 * s + 0.08 * s * stride, y - 1.45 * s),
                   (x, y - 1.35 * s), (x + 0.78 * s + 0.08 * s * stride, y - 1.45 * s), (x + 0.62 * s, y - 4.0 * s - bob),
                   (x + 0.72 * s, sh_y + 0.05 * s), (x, sh_y - 0.25 * s)], closed=True, corners=[2, 4])
    parts.append(robe)
    # arms swinging opposite to the legs
    for side in (-1, 1):
        swing = -side * stride * 0.45 * s if walking else 0.0
        sh = (x + side * 0.66 * s, sh_y + 0.2 * s)
        el = (x + side * 0.82 * s, y - 4.35 * s - bob + abs(swing) * 0.1)
        wr = (x + side * 0.86 * s + swing * 0.25, y - 3.45 * s - bob - abs(swing) * 0.35)
        parts.append(tapered(sample_spline([sh, el, wr], n=10), 0.36 * s, 0.30 * s, wmid=0.32 * s))
        parts.append(ellipse(wr[0], wr[1] + 0.22 * s, 0.13 * s, 0.24 * s))
    # head + cloth
    hx = x + facing * 0.05 * s
    parts.append(ellipse(hx, top - 0.55 * s, 0.42 * s, 0.5 * s))
    if head_cloth:
        parts.append(spline([(hx - 0.62 * s, top - 0.2 * s), (hx - 0.5 * s, top - 1.0 * s), (hx, top - 1.25 * s), (hx + 0.5 * s, top - 1.0 * s),
                             (hx + 0.62 * s, top - 0.2 * s), (hx + 0.7 * s, sh_y + 0.3 * s), (hx - 0.7 * s, sh_y + 0.3 * s)], closed=True))
    shape = skia.Path()
    for p in parts:
        shape.addPath(p)
    shape.setFillType(skia.PathFillType.kWinding)
    cv.drawPath(shape, fill(col))
    cv.save()
    cv.clipPath(shape, skia.ClipOp.kIntersect, True)
    m = skia.Matrix()
    m.setTranslate(-rim_side * 0.18 * s, 0)
    inner = skia.Path(shape)
    inner.transform(m)
    inner.setFillType(skia.PathFillType.kInverseWinding)
    cv.drawPath(inner, fill(rim, alpha=0.55))
    cv.restore()
    cv.drawPath(ellipse(x, y + 0.05 * s, 0.9 * s, 0.14 * s), fill("#000000", alpha=0.25, blur=0.2 * s))


def dusk_figures(cv, W, H, t, pcam=(0.5, 0.47, 0.82)):
    """Groups of disciples standing and talking on the beach, backlit by the sunset."""
    _, hz = screen_pt(0, bg.PH * 0.47, pcam, W, H)
    rng = np.random.default_rng(29)
    items = []
    for g, (u0, n) in enumerate([(0.22, 3), (0.40, 4), (0.58, 3), (0.74, 2)]):
        for i in range(n):
            u = u0 + rng.uniform(-0.03, 0.03)
            px, py = _beach_path(u)
            lane = (i - n / 2) * 0.012 + rng.uniform(-0.006, 0.006)
            sx, sy = screen_pt(px + lane * bg.PW * (1.3 - u), py, pcam, W, H)
            depth = max(sy - hz, 2.0)
            items.append((sy, sx, depth * 0.032, g * 3 + i))
    for sy, sx, s_, k in sorted(items):
        sway = 0.08 * math.sin(t * 0.6 + k)
        silhouette(cv, sx + sway * s_, sy, max(s_, 1.6), col="#2a1f2e", walking=False, facing=(1 if k % 2 else -1))


def _beach_path(u):
    """Point along the middle of the beach in plate coordinates (u=0 near camera, 1 far)."""
    hz = bg.PH * 0.47
    pts = [(0.885 * bg.PW, bg.PH * 1.0), (0.84 * bg.PW, hz + bg.PH * 0.36), (0.775 * bg.PW, hz + bg.PH * 0.2),
           (0.70 * bg.PW, hz + bg.PH * 0.085), (0.62 * bg.PW, hz + bg.PH * 0.025), (0.56 * bg.PW, hz + bg.PH * 0.004)]
    u = min(max(u, 0.0), 1.0) * (len(pts) - 1)
    i = min(int(u), len(pts) - 2)
    f_ = u - i
    return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f_, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f_)


def leaving(cv, W, H, t, t0, pcam=(0.5, 0.47, 0.82)):
    """Disciples walking away along the beach toward the town, in perspective."""
    u = t - t0
    _, hz = screen_pt(0, bg.PH * 0.47, pcam, W, H)
    walkers = []
    rng = np.random.default_rng(13)
    for k in range(12):
        s0 = 0.18 + 0.065 * k + rng.uniform(-0.02, 0.02)
        lane = rng.uniform(-0.035, 0.035)
        walkers.append((s0, lane, k))
    items = []
    for s0, lane, k in walkers:
        s = s0 + 0.018 * u
        px, py = _beach_path(s)
        x, y = screen_pt(px + lane * bg.PW * (1.2 - s), py, pcam, W, H)
        depth = max(y - hz, 2.0)
        items.append((y, x, depth * 0.032, u * 1.4 + k * 0.37))
    # Eli: near the camera, walks away, stops and looks back, then goes on
    if u < 2.4:
        s = 0.02 + 0.03 * u
    elif u < 4.4:
        s = 0.02 + 0.03 * 2.4
    else:
        s = 0.02 + 0.03 * 2.4 + 0.03 * (u - 4.4)
    px, py = _beach_path(s)
    ex, ey = screen_pt(px - 0.05 * bg.PW, py, pcam, W, H)
    ey = min(ey, H * 0.96)
    walk = (min(u, 2.4) + max(0.0, u - 4.4)) * 1.4
    look_back = 1 if 2.6 < u < 4.3 else -1
    items.append((ey, ex, (ey - hz) * 0.034, walk, look_back))
    for it in sorted(items, key=lambda i: i[0]):
        if len(it) == 4:
            y, x, s_, w = it
            silhouette(cv, x, y, max(s_, 1.6), col="#2a1f2e", walk=w)
        else:
            y, x, s_, w, fb = it
            silhouette(cv, x, y, s_, col="#221a24", walk=w, facing=fb)


def bread(cv, x, y, s, broken=0.0, side_only=None):
    """Round flat loaf; broken=1 draws a half (side_only -1 = left half, +1 = right half)."""
    path = ellipse(x, y, s * 1.2, s * 0.62)
    cv.save()
    if side_only is not None:
        clip = skia.Path()
        if side_only < 0:
            clip.addRect(skia.Rect.MakeLTRB(x - 3 * s, y - 2 * s, x + 0.08 * s, y + 2 * s))
        else:
            clip.addRect(skia.Rect.MakeLTRB(x - 0.08 * s, y - 2 * s, x + 3 * s, y + 2 * s))
        cv.clipPath(clip, skia.ClipOp.kIntersect, True)
    cv.drawPath(path, fill("#c98a45", shader=rad_grad((x - 0.3 * s, y - 0.3 * s), 1.5 * s, ["#e8b56c", "#b8743a", "#8a5428"])))
    for k in range(3):
        cv.drawPath(spline([(x - 0.6 * s + k * 0.5 * s, y - 0.35 * s), (x - 0.45 * s + k * 0.5 * s, y + 0.1 * s)], closed=False), stroke("#7a4a22", 0.08 * s, alpha=0.7))
    cv.drawPath(path, stroke("#5a3418", 0.06 * s))
    cv.restore()
    if side_only is not None:
        ex = x + 0.08 * s * (1 if side_only < 0 else -1)
        cv.drawPath(spline([(ex, y - 0.58 * s), (ex + side_only * 0.08 * s, y - 0.2 * s), (ex - side_only * 0.05 * s, y + 0.2 * s), (ex, y + 0.58 * s)], closed=False), stroke("#f2dcb0", 0.2 * s))


GRADES = {
    "morning": dict(tint=(1.0, 0.93, 0.82, 0.10), mode=skia.BlendMode.kSoftLight, vignette=0.28, lift=(0.04, 0.05, 0.09, 0.05)),
    "synagogue": dict(tint=(1.0, 0.78, 0.48, 0.22), mode=skia.BlendMode.kSoftLight, vignette=0.45, lift=(0.06, 0.03, 0.0, 0.05)),
    "synagogue_dark": dict(tint=(1.0, 0.72, 0.42, 0.26), mode=skia.BlendMode.kSoftLight, vignette=0.62, lift=(0.05, 0.02, 0.0, 0.04)),
    "dusk": dict(tint=(1.0, 0.62, 0.45, 0.24), mode=skia.BlendMode.kSoftLight, vignette=0.42, lift=(0.08, 0.03, 0.10, 0.06)),
}


def grade(cv, W, H, name):
    g = GRADES.get(name, GRADES["morning"])
    p = skia.Paint(Color4f=skia.Color4f(*g["tint"]))
    p.setBlendMode(g["mode"])
    cv.drawRect(skia.Rect.MakeWH(W, H), p)
    if g.get("lift"):
        p2 = skia.Paint(Color4f=skia.Color4f(*g["lift"]))
        p2.setBlendMode(skia.BlendMode.kScreen)
        cv.drawRect(skia.Rect.MakeWH(W, H), p2)
    v = g["vignette"]
    cv.drawRect(skia.Rect.MakeWH(W, H), fill("#000000", shader=rad_grad((W / 2, H * 0.42), H * 0.78, [(0, 0, 0, 0.0), (0, 0, 0, 0.0), (0, 0, 0, v)], [0.0, 0.55, 1.0])))
