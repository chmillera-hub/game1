"""Space scenes: the Earth (and Moon) seen from outside the shrinking bubble.

Every scene function has the signature fn(c, t, dur, cues, params) and paints
the full 1080x1920 frame. `cues` holds times (s, relative to shot start) of
the spoken words the visuals react to.
"""
import functools
import math

import numpy as np
import skia

import sphere
from gfx import (clamp, draw_text, ease_back, ease_in, ease_io, ease_out, fill, font, hexc, lerp,
                 linear_shader, radial_shader, smooth_path, smoothstep, stroke)

W, H = 1080, 1920
CX = 540.0
CY = 820.0

HUD_LABEL = "#93aee6"
LABEL = "#e6eeff"
CHALK = "#d8ecff"


# ----------------------------------------------------------------------------
# background
# ----------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _bg():
    arr = np.zeros((H, W, 4), np.uint8)
    s = skia.Surface(arr)
    c = s.getCanvas()
    p = skia.Paint()
    p.setShader(linear_shader((0, 0), (0, H), [hexc("#03050e"), hexc("#070b1f"), hexc("#0b1430"), hexc("#0d1838")],
                              [0.0, 0.35, 0.75, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # faint nebulae (static)
    for (x, y, r, col, a) in ((180, 420, 520, "#3a2a6e", 0.16), (930, 1250, 600, "#16466a", 0.15),
                              (760, 300, 380, "#2a3a7a", 0.10), (300, 1500, 500, "#3b1f55", 0.10)):
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((x, y), r, [hexc(col, a), hexc(col, a * 0.4), hexc(col, 0)], [0, 0.5, 1]))
        c.drawCircle(x, y, r, g)
    rng = np.random.default_rng(1234)
    n = 320
    xs = rng.uniform(0, W, n)
    ys = rng.uniform(0, H, n)
    br = rng.uniform(0.25, 1.0, n) ** 1.8
    sz = 0.5 + 1.5 * rng.uniform(0, 1, n) ** 3
    tint = rng.integers(0, 4, n)
    cols = ["#ffffff", "#cfe0ff", "#fff1d6", "#dfe8ff"]
    for x, y, b, r, k in zip(xs, ys, br, sz, tint):
        c.drawCircle(float(x), float(y), float(r), skia.Paint(AntiAlias=True, Color=hexc(cols[k], 0.25 + 0.75 * b)))
    for (x, y) in ((120, 260), (960, 520), (210, 1180), (870, 1500), (640, 140), (420, 1660), (1010, 980)):
        c.drawCircle(x, y, 2.4, skia.Paint(AntiAlias=True, Color=hexc("#ffffff", 0.95)))
        sp = stroke(hexc("#dfe9ff", 0.45), 1.3)
        c.drawLine(x - 9, y, x + 9, y, sp)
        c.drawLine(x, y - 9, x, y + 9, sp)
    rgb = arr.copy()
    img = skia.Image.fromarray(rgb, colorType=skia.kRGBA_8888_ColorType)
    return rgb, img


def draw_bg(c, alpha=1.0):
    rgb, img = _bg()
    if alpha >= 0.999:
        c.drawImage(img, 0, 0)
    else:
        c.clear(hexc("#03050e"))
        p = skia.Paint()
        p.setAlphaf(alpha)
        c.drawImage(img, 0, 0, skia.SamplingOptions(), p)


def warp_bg(c, cx, cy, half, r_sh=0.0, theta_e=0.0, ripples=None, alpha=1.0):
    """Gravitational lensing (+ optional radial ripples) of the starfield around (cx, cy)."""
    rgb, _ = _bg()
    x0, x1 = int(max(0, cx - half)), int(min(W, cx + half))
    y0, y1 = int(max(0, cy - half)), int(min(H, cy + half))
    if x1 <= x0 or y1 <= y0:
        return
    xs = np.arange(x0, x1, dtype=np.float32) + 0.5 - cx
    ys = np.arange(y0, y1, dtype=np.float32) + 0.5 - cy
    dx, dy = np.meshgrid(xs, ys)
    b = np.sqrt(dx * dx + dy * dy) + 1e-3
    k = np.ones_like(b)
    if theta_e > 0:
        k = k - (theta_e * theta_e) / (b * b)
    if ripples:
        # ripple field is smooth: evaluate at half resolution and upsample
        bs = b[::2, ::2]
        kr = np.zeros_like(bs)
        for (rc, lam, amp) in ripples:
            band = np.abs(bs - rc) < lam * 4.0
            if not band.any():
                continue
            bb = bs[band]
            kr[band] += amp * np.exp(-((bb - rc) / (lam * 1.6)) ** 2) * np.sin((bb - rc) / lam * 2 * np.pi) / bb
        kr = np.repeat(np.repeat(kr, 2, 0), 2, 1)[:b.shape[0], :b.shape[1]]
        k = k + kr
    sx = np.clip((cx + dx * k).astype(np.int32), 0, W - 1)
    sy = np.clip((cy + dy * k).astype(np.int32), 0, H - 1)
    out = rgb[sy, sx].copy()
    # blend toward the unwarped image at the edges of the region
    edge = np.clip((half - np.maximum(np.abs(dx), np.abs(dy))) / (half * 0.25), 0, 1)
    if r_sh > 0:
        inside = b < r_sh
        out[inside, :3] = 0
    a = (edge * alpha * 255).astype(np.uint8)
    out[..., 3] = a
    img = skia.Image.fromarray(np.ascontiguousarray(out), colorType=skia.kRGBA_8888_ColorType,
                               alphaType=skia.kUnpremul_AlphaType)
    c.drawImage(img, x0, y0)


# ----------------------------------------------------------------------------
# HUD + labels
# ----------------------------------------------------------------------------

def hud(c, chips, y=150):
    """chips: list of dicts(label, value, a, emph, values). Visible chips stay centred; a chip that is
    fading in slides its neighbours over smoothly. `values` lists strings whose width the chip reserves."""
    fl = font(23, "semibold")
    fv = font(40, "bold")
    pad, gap, hgt = 24, 16, 106
    widths, weights = [], []
    for ch in chips:
        wv = max(fv.measureText(v) for v in ch.get("values", [ch["value"]]) + [ch["value"]])
        widths.append(max(fl.measureText(ch["label"]), wv) + 2 * pad)
        weights.append(ease_io(clamp(ch.get("a", 1.0) * 1.25)))
    total = sum((w + gap) * k for w, k in zip(widths, weights)) - gap * (max(weights) if weights else 0)
    x = CX - total / 2
    for ch, w, k in zip(chips, widths, weights):
        a = clamp(ch.get("a", 1.0))
        e = clamp(ch.get("emph", 0.0))
        if a > 0.01:
            sc = (1 + 0.06 * e) * (0.85 + 0.15 * k)
            c.save()
            c.translate(x + w / 2, y + hgt / 2)
            c.scale(sc, sc)
            c.translate(-(x + w / 2), -(y + hgt / 2))
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, hgt), 20, 20)
            c.drawRRect(rr, fill(hexc("#0a1330", 0.78 * a)))
            if e > 0.01:
                c.drawRRect(rr, stroke(hexc("#9ec5ff", 0.55 * e * a), 12, blur=9))
            c.drawRRect(rr, stroke(hexc("#7895db", (0.5 + 0.5 * e) * a), 2.5))
            draw_text(c, ch["label"], x + w / 2, y + 36, fl, hexc(HUD_LABEL, a))
            draw_text(c, ch["value"], x + w / 2, y + 85, fv, hexc(ch.get("color", "#ffffff"), a))
            c.restore()
        x += (w + gap) * k


def label(c, s, x, y, size=32, color=LABEL, a=1.0, align="center", weight="semibold"):
    if a <= 0.01:
        return
    f = font(size, weight)
    draw_text(c, s, x, y, f, hexc(color, a), align, outline=hexc("#040714", 0.85 * a), outline_w=6)


def small_note(c, s, x, y, a=0.65, align="right"):
    label(c, s, x, y, 24, "#9fb0d8", a, align, "medium")


def fade_in(t, t0, d=0.5):
    return smoothstep(t0, t0 + d, t)


def pulse(t, t0, d=1.2):
    if t < t0:
        return 0.0
    x = (t - t0) / d
    return max(0.0, math.sin(min(1.0, x) * math.pi)) if x < 1 else 0.0


def glow(c, x, y, r, col, a):
    if a <= 0.005 or r <= 1:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((x, y), r, [hexc(col, a), hexc(col, a * 0.45), hexc(col, a * 0.12), hexc(col, 0)],
                              [0.0, 0.25, 0.55, 1.0]))
    c.drawCircle(x, y, r, p)


def dashed_circle(c, x, y, r, col, a, w=3.0, on=14, off=10, phase=0.0):
    if a <= 0.01:
        return
    p = stroke(hexc(col, a), w)
    p.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    c.drawCircle(x, y, r, p)


def path_segment(path, p):
    pm = skia.PathMeasure(path, False)
    L = pm.getLength()
    dst = skia.Path()
    if p <= 0:
        return dst
    pm.getSegment(0, L * min(1.0, p), dst, True)
    return dst


def chalk(c, path, col=CHALK, a=1.0, w=4.0, progress=1.0, glow_w=12.0):
    if a <= 0.01 or progress <= 0:
        return
    pth = path if progress >= 1 else path_segment(path, progress)
    c.drawPath(pth, stroke(hexc(col, 0.35 * a), glow_w, blur=glow_w * 0.6))
    c.drawPath(pth, stroke(hexc(col, a), w))


def fmt_km(d):
    if d >= 100:
        return f"{int(round(d / 10.0) * 10):,} km" if d < 1000 else f"{int(round(d)):,} km"
    if d >= 1:
        return f"{d:.0f} km"
    if d >= 0.001:
        return f"{d * 1000:.0f} m"
    return f"{d * 1e5:.1f} cm"


def log_interp(t, keys):
    """keys: [(t, value>0)] -> log-linear interpolation with smooth easing."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease_io((t - t0) / max(1e-6, t1 - t0))
            return math.exp(math.log(v0) + (math.log(v1) - math.log(v0)) * u)
    return keys[-1][1]


# ----------------------------------------------------------------------------
# planets
# ----------------------------------------------------------------------------

def earth(c, x, y, r, spin, sx=1.0, sy=1.0, glow_col=None, glow_a=0.0, glow_r=2.2, **state):
    if r < 0.6:
        return
    if glow_col and glow_a > 0:
        glow(c, x, y, r * glow_r, glow_col, glow_a)
    spr = sphere.render_earth(r, spin=spin, **state)
    sphere.draw_sprite(c, spr, x, y, sx, sy)


def moon(c, x, y, r, spin=0.0, a=1.0):
    if r < 0.6 or a <= 0.01:
        return
    spr = sphere.render_textured(r, sphere.moon_texture(), spin=spin, tilt=0.15, night=0.06)
    sphere.draw_sprite(c, spr, x, y, alpha=a)


def mars(c, x, y, r, spin=0.0, a=1.0):
    spr = sphere.render_textured(r, sphere.mars_texture(), spin=spin, tilt=0.25, night=0.05,
                                 rim_col=(1.0, 0.65, 0.45), rim_k=0.35)
    sphere.draw_sprite(c, spr, x, y, alpha=a)


def atmosphere_halo(c, x, y, r, a=1.0):
    glow(c, x, y, r * 1.18, "#6fb0ff", 0.28 * a)


def hot_glow(c, x, y, r, heat, white=0.0):
    """Outer glow for a hot/compressed planet. heat 0..1, white 0..1 (bluer)."""
    col = "#ff8a3d" if white < 0.5 else "#bfe0ff"
    if white > 0 and white < 1:
        col = "#ffd2a0" if white < 0.5 else "#d6e9ff"
    glow(c, x, y, r * (2.4 + 1.2 * heat), col, 0.45 * heat)
    glow(c, x, y, r * 1.35, "#fff2dc" if white < 0.5 else "#eef6ff", 0.55 * heat)


def neutron(c, x, y, r, t, intensity=1.0):
    """Tiny, intensely bright blue-white ball."""
    glow(c, x, y, r * 7.0, "#6ea8ff", 0.35 * intensity)
    glow(c, x, y, r * 3.2, "#cfe4ff", 0.55 * intensity)
    spr = sphere.render_earth(max(r, 1.0), spin=t * 3.0, white=1.0)
    sphere.draw_sprite(c, spr, x, y)
    glow(c, x, y, r * 1.25, "#ffffff", 0.5 * intensity)


# ----------------------------------------------------------------------------
# little illustrations
# ----------------------------------------------------------------------------

def kid(c, x, y, s, t, wave=True):
    """Tiny waving kid in a yellow hoodie (Pip), feet at (x, y)."""
    ol = hexc("#24161c")
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    # legs
    c.drawLine(-7, -26, -8, 0, stroke(ol, 9))
    c.drawLine(7, -26, 8, 0, stroke(ol, 9))
    c.drawLine(-7, -26, -8, 0, stroke(hexc("#2d3c6c"), 6))
    c.drawLine(7, -26, 8, 0, stroke(hexc("#2d3c6c"), 6))
    # body
    body = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-16, -62, 16, -22), 10, 10)
    c.drawRRect(body, stroke(ol, 3))
    c.drawRRect(body, fill(hexc("#f1b53e")))
    # waving arm
    ang = -2.4 + (0.45 * math.sin(t * 9.0) if wave else 0)
    ax, ay = 14 + math.sin(ang) * 0, -56
    hx, hy = ax + math.cos(ang) * 26, ay + math.sin(ang) * 26
    c.drawLine(ax, ay, hx, hy, stroke(ol, 9))
    c.drawLine(ax, ay, hx, hy, stroke(hexc("#f1b53e"), 6))
    c.drawCircle(hx, hy, 4.5, fill(hexc("#c98c66")))
    c.drawLine(-14, -56, -22, -32, stroke(ol, 9))
    c.drawLine(-14, -56, -22, -32, stroke(hexc("#e0a636"), 6))
    # head + buns
    for bx in (-13, 13):
        c.drawCircle(bx, -95, 8, fill(hexc("#5b2c22")))
    c.drawCircle(0, -80, 18, stroke(ol, 3))
    c.drawCircle(0, -80, 18, fill(hexc("#c98c66")))
    hair = skia.Path()
    hair.addArc(skia.Rect.MakeLTRB(-19, -99, 19, -61), 180, 180)
    hair.close()
    c.drawPath(hair, fill(hexc("#5b2c22")))
    c.drawCircle(-6, -78, 2.4, fill(ol))
    c.drawCircle(6, -78, 2.4, fill(ol))
    sm = skia.Path()
    sm.moveTo(-6, -71)
    sm.quadTo(0, -66, 6, -71)
    c.drawPath(sm, stroke(ol, 2))
    c.restore()


def inset(c, x, y, r, a, kind, t, k=1.0, title=""):
    """Circular 'magnifier' inset popping in. k = content scale (shrinks with the world)."""
    if a <= 0.01:
        return
    sc = ease_back(clamp(a), 1.8)
    c.save()
    c.translate(x, y)
    c.scale(sc, sc)
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    glow(c, 0, 0, r * 1.3, "#9ec5ff", 0.25)
    c.save()
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    p = skia.Paint()
    p.setShader(linear_shader((0, -r), (0, r), [hexc("#7cc4ff"), hexc("#bfe6ff")]))
    c.drawRect(skia.Rect.MakeLTRB(-r, -r, r, r), p)
    c.save()
    c.scale(k, k)
    if kind == "ocean":
        c.drawRect(skia.Rect.MakeLTRB(-r * 1.5, 0, r * 1.5, r * 1.5), fill(hexc("#2c78c8")))
        for j in range(4):
            yy = 6 + j * 16
            pth = skia.Path()
            pth.moveTo(-r * 1.3, yy)
            for q in range(10):
                x0 = -r * 1.3 + q * 26 + (t * 22) % 26
                pth.quadTo(x0 + 6.5, yy - 7, x0 + 13, yy)
                pth.quadTo(x0 + 19.5, yy + 7, x0 + 26, yy)
            c.drawPath(pth, stroke(hexc("#e9f6ff", 0.85 - j * 0.15), 3.2))
        # tiny boat
        bob = math.sin(t * 2.4) * 2.5
        hull = smooth_path([(-22, -6 + bob), (22, -6 + bob), (14, 6 + bob), (-14, 6 + bob)], True, 0.0)
        c.drawPath(hull, fill(hexc("#a84b3a")))
        c.drawLine(0, -6 + bob, 0, -38 + bob, stroke(hexc("#3b2a22"), 2.5))
        sail = smooth_path([(2, -36 + bob), (20, -10 + bob), (2, -10 + bob)], True, 0.0)
        c.drawPath(sail, fill(hexc("#fdf7ea")))
    elif kind == "cloud":
        dx = math.sin(t * 0.8) * 6
        for (cx_, cy_, rr) in ((-26, 8, 22), (0, -6, 30), (26, 6, 24), (8, 14, 22), (-10, 16, 20)):
            c.drawCircle(cx_ + dx, cy_, rr + 3, fill(hexc("#c7d9ee")))
        for (cx_, cy_, rr) in ((-26, 8, 22), (0, -6, 30), (26, 6, 24), (8, 14, 22), (-10, 16, 20)):
            c.drawCircle(cx_ + dx, cy_ - 2, rr, fill(hexc("#ffffff")))
    elif kind == "person":
        c.drawRect(skia.Rect.MakeLTRB(-r * 1.5, 30, r * 1.5, r * 1.5), fill(hexc("#58a85a")))
        c.drawOval(skia.Rect.MakeLTRB(-60, 18, 70, 46), fill(hexc("#6dbd66")))
        kid(c, 0, 44, 0.78, t)
    c.restore()
    c.restore()
    c.drawCircle(0, 0, r, stroke(hexc("#ffffff", 0.95), 5))
    c.restore()
    if title:
        label(c, title, x, y + r * sc + 36, 27, "#dbe7ff", clamp(a * 1.5))


def city_skyline(c, x, y, w, a=1.0, col="#2a3a6a", windows=True, seed=4):
    """Skyline silhouette with base centred at (x, y) and given width."""
    if a <= 0.01:
        return
    rng = np.random.default_rng(seed)
    n = 14
    xs = np.linspace(-0.5, 0.5, n + 1)
    hs = rng.uniform(0.18, 0.55, n)
    hs[n // 2] = 0.78
    hs[n // 2 - 3] = 0.62
    pth = skia.Path()
    pth.moveTo(x - w / 2, y)
    for i in range(n):
        x0 = x + xs[i] * w
        x1 = x + xs[i + 1] * w
        hh = hs[i] * w * 0.42
        pth.lineTo(x0, y - hh)
        if i == n // 2:
            pth.lineTo((x0 + x1) / 2, y - hh - w * 0.08)
        pth.lineTo(x1, y - hh)
    pth.lineTo(x + w / 2, y)
    pth.close()
    c.drawPath(pth, fill(hexc(col, a)))
    c.drawPath(pth, stroke(hexc("#9fc0ff", 0.55 * a), 2.0))
    if windows and w > 120:
        r2 = np.random.default_rng(seed + 1)
        for i in range(n):
            x0 = x + xs[i] * w
            x1 = x + xs[i + 1] * w
            hh = hs[i] * w * 0.42
            for yy in np.arange(y - hh + 10, y - 6, 12):
                for xx in np.arange(x0 + 5, x1 - 5, 9):
                    if r2.uniform() < 0.35:
                        c.drawRect(skia.Rect.MakeXYWH(float(xx), float(yy), 3.2, 4.2), fill(hexc("#ffd88a", 0.75 * a)))


def stadium(c, x, y, w, a=1.0):
    """Oblique view of a stadium bowl centred at (x, y), width w."""
    if a <= 0.01:
        return
    h = w * 0.46
    c.save()
    # outer wall
    c.drawOval(skia.Rect.MakeLTRB(x - w / 2, y - h / 2 + h * 0.10, x + w / 2, y + h / 2 + h * 0.10), fill(hexc("#1c2850", a)))
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2, y, x + w / 2, y + h * 0.10), fill(hexc("#1c2850", a)))
    # stands (top surface)
    c.drawOval(skia.Rect.MakeLTRB(x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill(hexc("#3a4f86", a)))
    for k in range(1, 4):
        f = 1 - k * 0.09
        c.drawOval(skia.Rect.MakeLTRB(x - w / 2 * f, y - h / 2 * f, x + w / 2 * f, y + h / 2 * f),
                   stroke(hexc("#5b72b0", 0.7 * a), 1.6))
    # pitch
    fw, fh = w * 0.56, h * 0.56
    c.drawOval(skia.Rect.MakeLTRB(x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2), fill(hexc("#3f9a52", a)))
    c.drawLine(x, y - fh / 2 + 3, x, y + fh / 2 - 3, stroke(hexc("#e8fff0", 0.8 * a), 1.6))
    c.drawOval(skia.Rect.MakeLTRB(x - fw * 0.12, y - fh * 0.12, x + fw * 0.12, y + fh * 0.12), stroke(hexc("#e8fff0", 0.8 * a), 1.6))
    c.drawOval(skia.Rect.MakeLTRB(x - w / 2, y - h / 2, x + w / 2, y + h / 2), stroke(hexc("#9fc0ff", 0.6 * a), 2.0))
    # floodlights
    for (sx, sy) in ((-0.42, -0.30), (0.42, -0.30), (-0.46, 0.28), (0.46, 0.28)):
        tx, ty = x + sx * w, y + sy * h
        c.drawLine(tx, ty, tx, ty - h * 0.55, stroke(hexc("#2a3a6a", a), 3))
        c.drawRect(skia.Rect.MakeLTRB(tx - 8, ty - h * 0.62, tx + 8, ty - h * 0.53), fill(hexc("#fff6d8", a)))
        glow(c, tx, ty - h * 0.57, w * 0.10, "#fff2c0", 0.45 * a)
    c.restore()


def country_outline(c, x, y, r, a=1.0, seed=8, progress=1.0):
    if a <= 0.01:
        return
    rng = np.random.default_rng(seed)
    n = 22
    pts = []
    for i in range(n):
        ang = i / n * 2 * math.pi
        rr = r * (0.78 + 0.32 * rng.uniform()) * (1 + 0.12 * math.sin(3 * ang + 1))
        pts.append((x + math.cos(ang) * rr * 1.1, y + math.sin(ang) * rr * 0.9))
    pth = smooth_path(pts, True, 0.5)
    c.drawPath(pth, fill(hexc("#3b6b4a", 0.10 * a)))
    p = stroke(hexc("#9ff0b8", 0.9 * a), 3.2)
    p.setPathEffect(skia.DashPathEffect.Make([16, 10], 0))
    seg = path_segment(pth, progress) if progress < 1 else pth
    c.drawPath(seg, p)


def ruler(c, x0, y, cm_px, cms=3, a=1.0):
    if a <= 0.01:
        return
    w = cm_px * cms + 72
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - 20, y, x0 - 20 + w, y + 70), 8, 8)
    c.drawRRect(rr, fill(hexc("#e9d29a", 0.92 * a)))
    c.drawRRect(rr, stroke(hexc("#7a5a2a", a), 2.5))
    f = font(24, "bold")
    for mm in range(cms * 10 + 1):
        xx = x0 + mm * cm_px / 10
        ln = 30 if mm % 10 == 0 else (20 if mm % 5 == 0 else 12)
        c.drawLine(xx, y, xx, y + ln, stroke(hexc("#4a3518", a), 2.0 if mm % 10 == 0 else 1.4))
        if mm % 10 == 0:
            s = f"{mm // 10}"
            draw_text(c, s, xx, y + 58, f, hexc("#4a3518", a))
    draw_text(c, "cm", x0 + cm_px * cms + 2, y + 58, font(20, "bold"), hexc("#4a3518", a), "left")


def marble(c, x, y, r, a=1.0, t=0.0):
    if a <= 0.01:
        return
    c.save()
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((x - r * 0.3, y - r * 0.35), r * 1.5,
                              [hexc("#bfe8ff", a), hexc("#3f8fd8", a), hexc("#123a7a", a)], [0.0, 0.5, 1.0]))
    c.drawCircle(x, y, r, p)
    clip = skia.Path()
    clip.addCircle(x, y, r)
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    sw = smooth_path([(x - r * 0.9, y + r * 0.2), (x - r * 0.3, y - r * 0.25), (x + r * 0.2, y + r * 0.15),
                      (x + r * 0.8, y - r * 0.35)], False)
    c.drawPath(sw, stroke(hexc("#e8fbff", 0.85 * a), r * 0.16))
    sw2 = smooth_path([(x - r * 0.7, y + r * 0.6), (x - r * 0.1, y + r * 0.35), (x + r * 0.5, y + r * 0.55)], False)
    c.drawPath(sw2, stroke(hexc("#7ff0d8", 0.75 * a), r * 0.12))
    c.restore()
    c.drawCircle(x, y, r, stroke(hexc("#0d2350", a), 3))
    c.drawOval(skia.Rect.MakeLTRB(x - r * 0.55, y - r * 0.7, x - r * 0.05, y - r * 0.4), fill(hexc("#ffffff", 0.7 * a), blur=r * 0.05))
    c.drawCircle(x + r * 0.45, y + r * 0.45, r * 0.08, fill(hexc("#ffffff", 0.5 * a)))


def peppercorn(c, x, y, r, a=1.0):
    if a <= 0.01:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((x - r * 0.3, y - r * 0.3), r * 1.4, [hexc("#6b4a3a", a), hexc("#2a1a14", a)], [0, 1]))
    c.drawCircle(x, y, r, p)
    for k in range(6):
        ang = k * 1.1
        pth = skia.Path()
        pth.moveTo(x + math.cos(ang) * r * 0.2, y + math.sin(ang) * r * 0.2)
        pth.quadTo(x + math.cos(ang + 0.6) * r * 0.7, y + math.sin(ang + 0.6) * r * 0.7,
                   x + math.cos(ang + 0.2) * r * 0.95, y + math.sin(ang + 0.2) * r * 0.95)
        c.drawPath(pth, stroke(hexc("#140c08", 0.8 * a), max(1.2, r * 0.1)))
    c.drawCircle(x - r * 0.35, y - r * 0.35, r * 0.18, fill(hexc("#c9a58a", 0.6 * a)))


def stick_walker(c, x, y, s, phase, ang, col=CHALK, a=1.0):
    """Chalk stick figure with feet at (x, y), standing along direction ang (radians, 0 = up)."""
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    c.scale(s, s)
    sw = math.sin(phase) * 0.5
    pc = stroke(hexc(col, a), 3.2)
    c.drawLine(0, -18, math.sin(sw) * 12, 0, pc)
    c.drawLine(0, -18, -math.sin(sw) * 12, 0, pc)
    c.drawLine(0, -18, 0, -38, pc)
    c.drawLine(0, -33, 10 * math.cos(sw), -24, pc)
    c.drawLine(0, -33, -10 * math.cos(sw), -24, pc)
    c.drawCircle(0, -45, 7, stroke(hexc(col, a), 3.2))
    c.restore()


def icon_mountain(c, x, y, s, a, progress=1.0):
    pth = skia.Path()
    pth.moveTo(x - 60 * s, y + 30 * s)
    pth.lineTo(x - 15 * s, y - 40 * s)
    pth.lineTo(x + 5 * s, y - 10 * s)
    pth.lineTo(x + 25 * s, y - 30 * s)
    pth.lineTo(x + 60 * s, y + 30 * s)
    pth.close()
    snow = skia.Path()
    snow.moveTo(x - 27 * s, y - 22 * s)
    snow.lineTo(x - 15 * s, y - 40 * s)
    snow.lineTo(x - 3 * s, y - 22 * s)
    chalk(c, pth, a=a, w=4 * max(s, 0.5), progress=progress)
    chalk(c, snow, a=a * 0.8, w=3 * max(s, 0.5), progress=progress)


def icon_wave(c, x, y, s, a, progress=1.0):
    pth = skia.Path()
    pth.moveTo(x - 60 * s, y)
    for q in range(4):
        x0 = x - 60 * s + q * 30 * s
        pth.quadTo(x0 + 7.5 * s, y - 16 * s, x0 + 15 * s, y)
        pth.quadTo(x0 + 22.5 * s, y + 16 * s, x0 + 30 * s, y)
    chalk(c, pth, col="#9fdcff", a=a, w=4 * max(s, 0.5), progress=progress)
    pth2 = skia.Path()
    pth2.moveTo(x - 45 * s, y + 24 * s)
    for q in range(3):
        x0 = x - 45 * s + q * 30 * s
        pth2.quadTo(x0 + 7.5 * s, y + 10 * s, x0 + 15 * s, y + 24 * s)
        pth2.quadTo(x0 + 22.5 * s, y + 38 * s, x0 + 30 * s, y + 24 * s)
    chalk(c, pth2, col="#9fdcff", a=a * 0.8, w=3.5 * max(s, 0.5), progress=progress)


def icon_city(c, x, y, s, a, progress=1.0):
    pth = skia.Path()
    xs = [-60, -60, -38, -38, -20, -20, 2, 2, 22, 22, 40, 40, 60, 60]
    ys = [30, -10, -10, -35, -35, -55, -55, -20, -20, -42, -42, -5, -5, 30]
    pth.moveTo(x + xs[0] * s, y + ys[0] * s)
    for xx, yy in zip(xs[1:], ys[1:]):
        pth.lineTo(x + xx * s, y + yy * s)
    pth.close()
    chalk(c, pth, col="#ffe3a0", a=a, w=4 * max(s, 0.5), progress=progress)


def _annulus(r_in, r_out):
    p = skia.Path()
    p.setFillType(skia.PathFillType.kEvenOdd)
    p.addCircle(0, 0, r_out)
    p.addCircle(0, 0, r_in)
    return p


def accretion_ring(c, x, y, r_in, r_out, tilt=0.22, a=1.0, front=True, t=0.0, white=0.0):
    """Half of a glowing tilted disk (front = lower half, drawn over the shadow)."""
    if a <= 0.01:
        return
    c.save()
    clip = skia.Path()
    if front:
        clip.addRect(skia.Rect.MakeLTRB(x - r_out * 2, y, x + r_out * 2, y + r_out * 2))
    else:
        clip.addRect(skia.Rect.MakeLTRB(x - r_out * 2, y - r_out * 2, x + r_out * 2, y))
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    c.translate(x, y)
    c.scale(1.0, tilt)
    if white > 0.5:
        cols = ["#ffffff", "#e6f0ff", "#b8d0ff", "#7fa0e8", "#4a6ac0"]
    else:
        cols = ["#fffaf0", "#ffe2a8", "#ffb35c", "#f07a30", "#a83a1a"]
    u0 = r_in / r_out
    pos = [u0, u0 + (1 - u0) * 0.12, u0 + (1 - u0) * 0.35, u0 + (1 - u0) * 0.65, 1.0]
    halo = skia.Paint(AntiAlias=True)
    halo.setShader(radial_shader((0, 0), r_out * 1.25, [hexc(cols[2], 0.0), hexc(cols[2], 0.35 * a), hexc(cols[3], 0.0)],
                                 [u0 * 0.8, (u0 + 1) / 2, 1.0]))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
    c.drawPath(_annulus(r_in * 0.9, r_out * 1.2), halo)
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((0, 0), r_out, [hexc(cols[0], a), hexc(cols[1], a), hexc(cols[2], 0.92 * a),
                                              hexc(cols[3], 0.6 * a), hexc(cols[4], 0.0)], pos))
    c.drawPath(_annulus(r_in, r_out), p)
    # Doppler beaming: the approaching (left) side is brighter
    d = skia.Paint(AntiAlias=True)
    d.setShader(linear_shader((-r_out, 0), (r_out, 0), [hexc("#ffffff", 0.35 * a), hexc("#ffffff", 0.0)], [0.0, 0.6]))
    d.setBlendMode(skia.BlendMode.kPlus)
    c.drawPath(_annulus(r_in, r_out * 0.85), d)
    # thin bright inner edge
    c.drawCircle(0, 0, r_in * 1.02, stroke(hexc(cols[0], 0.8 * a), max(1.5, (r_out - r_in) * 0.05)))
    c.restore()


def black_hole(c, x, y, r_sh, a_ring=1.0, a_photon=1.0, t=0.0, ring_in=1.55, ring_out=2.7, tilt=0.20, lens=1.0,
               white=0.0):
    """Shadow + photon ring + lensed far side of the disk + front of the disk."""
    accretion_ring(c, x, y, r_sh * ring_in, r_sh * ring_out, tilt, a_ring, front=False, t=t, white=white)
    if a_ring > 0.01:
        # far side of the disk, bent over the top (and faintly under the bottom) of the shadow
        warm = white < 0.5
        for (a0, sweep, rr, wv, aa) in ((185, 170, 1.30, 0.42, 0.95), (15, 150, 1.20, 0.18, 0.45)):
            pth = skia.Path()
            pth.addArc(skia.Rect.MakeLTRB(x - r_sh * rr, y - r_sh * rr, x + r_sh * rr, y + r_sh * rr), a0, sweep)
            g = stroke(hexc("#ffffff"), r_sh * wv)
            g.setShader(radial_shader((x, y), r_sh * (rr + wv / 2),
                                      [hexc("#fff4dc" if warm else "#eef4ff", aa * a_ring * lens),
                                       hexc("#ffb35c" if warm else "#9fbcff", 0.75 * aa * a_ring * lens),
                                       hexc("#c0501f" if warm else "#4a6ac0", 0.0)],
                                      [(rr - wv / 2) / (rr + wv / 2), rr / (rr + wv / 2), 1.0]))
            g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r_sh * 0.03))
            c.drawPath(pth, g)
    c.drawCircle(x, y, r_sh, fill(hexc("#000000")))
    if a_photon > 0.01:
        c.drawCircle(x, y, r_sh * 1.03, stroke(hexc("#fff4e0" if white == 0 else "#eef5ff", 0.9 * a_photon), max(1.5, r_sh * 0.03)))
        c.drawCircle(x, y, r_sh * 1.05, stroke(hexc("#ffd29a" if white == 0 else "#cfe2ff", 0.30 * a_photon), r_sh * 0.10, blur=r_sh * 0.05))
    accretion_ring(c, x, y, r_sh * ring_in, r_sh * ring_out, tilt, a_ring, front=True, t=t, white=white)


# ----------------------------------------------------------------------------
# scenes
# ----------------------------------------------------------------------------

def space_bubble(c, t, dur, cues, params):
    draw_bg(c)
    tb = cues.get("bubble", 1.2)
    ts = cues.get("shrink", 5.6)
    u = ease_io((t - ts) / 3.4)
    s = 1.0 - 0.38 * u - 0.10 * clamp((t - ts - 3.4) / max(1.0, dur - ts - 3.4))
    BC = (560.0, 800.0)
    RB = 495.0
    pb = ease_out((t - tb) / 1.4)
    if s < 0.999 and pb > 0:
        dashed_circle(c, BC[0], BC[1], RB, "#7fb2ff", 0.35 * pb, 2.5, 10, 12)
        small_note(c, "original size", BC[0] - RB * 0.62, BC[1] - RB * 0.80, 0.6 * clamp((1 - s) * 8), "center")
    rb = RB * s
    if pb > 0:
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((BC[0] - rb * 0.25, BC[1] - rb * 0.3), rb * 1.3,
                                  [hexc("#9fd0ff", 0.0), hexc("#9fd0ff", 0.04 * pb), hexc("#9fd0ff", 0.13 * pb)],
                                  [0.0, 0.7, 1.0]))
        c.drawCircle(BC[0], BC[1], rb, g)
    ex, ey, er = BC[0] - 60 * s, BC[1] + 265 * s, 200 * s
    mx, my, mr = BC[0] + 225 * s, BC[1] - 300 * s, 54 * s
    atmosphere_halo(c, ex, ey, er)
    earth(c, ex, ey, er, spin=0.9 + 0.06 * t, cloud_spin=0.012 * t)
    moon(c, mx, my, mr, spin=0.4)
    label(c, "Moon", mx, my - mr - 18, 28, "#cfd9f0", fade_in(t, 0.3) * 0.85)
    if pb > 0:
        circ = skia.Path()
        circ.addArc(skia.Rect.MakeLTRB(BC[0] - rb, BC[1] - rb, BC[0] + rb, BC[1] + rb), -90, 359.9)
        chalk(c, circ, "#bfe0ff", 0.95, 4.0, pb, 18)
        hl = skia.Path()
        hl.addArc(skia.Rect.MakeLTRB(BC[0] - rb * 0.88, BC[1] - rb * 0.88, BC[0] + rb * 0.88, BC[1] + rb * 0.88), 205, 38)
        c.drawPath(hl, stroke(hexc("#ffffff", 0.28 * pb), 9, blur=5))
        hl2 = skia.Path()
        hl2.addArc(skia.Rect.MakeLTRB(BC[0] - rb * 0.80, BC[1] - rb * 0.80, BC[0] + rb * 0.80, BC[1] + rb * 0.80), 212, 14)
        c.drawPath(hl2, stroke(hexc("#ffffff", 0.22 * pb), 6, blur=3))
    # insets: ocean / cloud / person
    k = 0.55 + 0.45 * (s - 0.52) / 0.48
    for key, (ix, iy), title in (("ocean", (175, 1262), "every ocean"), ("cloud", (540, 1290), "every cloud"),
                                 ("person", (905, 1262), "every person")):
        tc = cues.get(key)
        if tc is None:
            continue
        a = clamp((t - tc + 0.05) / 0.45)
        if a > 0:
            # leader line to the Earth
            lx, ly = ex + (ix - ex) * er / max(1, math.hypot(ix - ex, iy - ey)), ey + (iy - ey) * er / max(1, math.hypot(ix - ex, iy - ey))
            lp = stroke(hexc("#cfe3ff", 0.5 * a), 2.0)
            lp.setPathEffect(skia.DashPathEffect.Make([6, 8], 0))
            c.drawLine(lx, ly, ix, iy - 86, lp)
            inset(c, ix, iy, 86, a, key, t, k, title)
    tg = cues.get("gram", 14.4)
    hud(c, [dict(label="SIZE", value=f"{round(s * 100)}%", values=["100%"], a=fade_in(t, 0.4),
                 emph=0.6 * pulse(t, ts, 1.4)),
            dict(label="MASS", value="100%", a=fade_in(t, 0.6), emph=pulse(t, tg - 0.1, 1.6),
                 color="#ffe7a8" if t > tg - 0.1 else "#ffffff")])
    small_note(c, "Earth & Moon not to scale", 1030, 296, 0.6 * fade_in(t, 0.8))


def space_gravity(c, t, dur, cues, params):
    draw_bg(c)
    ts = cues.get("squeeze", 3.0)
    tg = cues.get("gravity", 5.6)
    tq = cues.get("quarter", 7.8)
    tf = cues.get("feel", 1.4)
    s = 1.0 - 0.10 * ease_io((t - ts) / 1.6)
    x, y, R0 = CX, 890.0, 330.0
    r = R0 * s
    if t > ts - 0.2:
        dashed_circle(c, x, y, R0, "#8fb6ff", 0.45 * fade_in(t, ts - 0.2, 0.4), 2.5)
    atmosphere_halo(c, x, y, r)
    earth(c, x, y, r, spin=2.2 + 0.05 * t, cloud_spin=0.01 * t)
    # squeeze chevrons
    sq = clamp(1 - abs((t - (ts + 0.7)) / 1.3))
    if sq > 0:
        for k in range(8):
            ang = k * math.pi / 4 + math.pi / 8
            d = R0 + 70 - 30 * ease_io((t - ts + 0.2) / 1.6)
            px, py = x + math.cos(ang) * d, y + math.sin(ang) * d
            ix, iy = -math.cos(ang), -math.sin(ang)
            jx, jy = -iy, ix
            pth = skia.Path()
            pth.moveTo(px - ix * 18 + jx * 20, py - iy * 18 + jy * 20)
            pth.lineTo(px, py)
            pth.lineTo(px - ix * 18 - jx * 20, py - iy * 18 - jy * 20)
            c.drawPath(pth, stroke(hexc("#ffd36a", 0.9 * sq), 6))
    # gravity arrows around the surface
    ga = fade_in(t, tg - 0.3, 0.5)
    grow = 1 + 0.23 * ease_io((t - tg) / 1.4)
    if ga > 0:
        for k in range(12):
            ang = k * math.pi / 6 + 0.26
            if -2.2 < ang - (-math.pi / 2) < -1.2:
                continue
            L = 52 * grow
            ox, oy = x + math.cos(ang) * (r + 18 + L), y + math.sin(ang) * (r + 18 + L)
            tx, ty = x + math.cos(ang) * (r + 14), y + math.sin(ang) * (r + 14)
            arrow(c, ox, oy, tx, ty, "#ffb4a0", ga * 0.85, 6)
    # a person on top whose weight grows
    pa = fade_in(t, tf - 0.2, 0.5)
    if pa > 0:
        px, py = x, y - r
        kid(c, px, py, 1.0, t, wave=t < tg)
        L = 70 * (1 + 0.23 * ease_io((t - tg) / 1.4))
        arrow(c, px + 46, py - 60, px + 46, py - 60 + L, "#ffd36a", pa, 7)
        label(c, "your weight", px + 62, py - 70, 26, "#ffe7a8", pa, "left")
    gv = 1.0 + 0.23 * ease_io((t - tg) / 1.4)
    hud(c, [dict(label="SIZE", value=f"{round(s * 100)}%", values=["100%"], a=fade_in(t, 0.2),
                 emph=0.6 * pulse(t, ts, 1.5)),
            dict(label="GRAVITY", value=f"×{gv:.2f}", values=["×1.23"], a=fade_in(t, tg - 0.4),
                 emph=pulse(t, tq - 0.2, 1.6), color="#ffd0c0" if t > tq - 0.2 else "#ffffff")])


def arrow(c, x0, y0, x1, y1, col, a, w=6):
    if a <= 0.01:
        return
    c.drawLine(x0, y0, x1, y1, stroke(hexc(col, a), w))
    ang = math.atan2(y1 - y0, x1 - x0)
    hl = w * 3.2
    pth = skia.Path()
    pth.moveTo(x1, y1)
    pth.lineTo(x1 - math.cos(ang - 0.45) * hl, y1 - math.sin(ang - 0.45) * hl)
    pth.lineTo(x1 - math.cos(ang + 0.45) * hl, y1 - math.sin(ang + 0.45) * hl)
    pth.close()
    c.drawPath(pth, fill(hexc(col, a)))


def space_mars(c, t, dur, cues, params):
    draw_bg(c)
    tm = cues.get("mars", 2.75)
    tf = cues.get("four", 4.1)
    ex, ey, er = 330.0, 830.0, 165.0
    ga = 1 - fade_in(t, tm - 0.4, 0.8)
    dashed_circle(c, ex, ey, er * 2, "#8fb6ff", 0.45 * ga, 2.5)
    label(c, "original size", ex, ey - er * 2 - 16, 24, "#9fb0d8", 0.6 * ga)
    atmosphere_halo(c, ex, ey, er)
    earth(c, ex, ey, er, spin=1.5 + 0.12 * t, cloud_spin=0.02 * t)
    label(c, "Earth, half size", ex, ey + er + 52, 30, LABEL, fade_in(t, 0.5))
    ma = ease_out((t - tm + 0.2) / 0.9)
    if ma > 0:
        mx = lerp(1250.0, 770.0, ma)
        mr = er * 1.06
        glow(c, mx, ey, mr * 1.25, "#ff9a6a", 0.18 * ma)
        mars(c, mx, ey, mr, spin=0.6 + 0.05 * t)
        label(c, "Mars", mx, ey + mr + 52, 30, "#ffc2a6", ma)
        la = fade_in(t, tm + 0.6, 0.5)
        if la > 0:
            p = stroke(hexc("#cfe0ff", 0.55 * la), 2.0)
            p.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
            c.drawLine(ex - er - 30, ey - er, mx + mr + 30, ey - er, p)
            c.drawLine(ex - er - 30, ey + er, mx + mr + 30, ey + er, p)
            label(c, "≈ same size", (ex + mx) / 2, ey - er - 22, 30, "#ffffff", la)
    hud(c, [dict(label="SIZE", value="50%", a=fade_in(t, 0.2)),
            dict(label="GRAVITY", value="×4", a=fade_in(t, tf - 0.3, 0.4), emph=pulse(t, tf - 0.2, 1.4),
                 color="#ffd0c0"),
            dict(label="DAY", value="6 h", a=fade_in(t, tf + 0.6, 0.4), emph=pulse(t, tf + 0.5, 1.4))])


def steam_curls(c, x, y, r, t, a):
    """Wavy steam lines rising off the limb, like a hot mug."""
    for k in range(11):
        ang = -math.pi / 2 + (k - 5) * 0.27
        ph = (t * 0.55 + k * 0.37) % 1.0
        base = r * (1.02 + 0.05 * ph)
        pts = []
        for j in range(8):
            d = base + j * r * 0.035 + ph * r * 0.10
            wob = math.sin(j * 1.1 + t * 2.4 + k) * r * 0.018
            px = x + math.cos(ang) * d - math.sin(ang) * wob
            py = y + math.sin(ang) * d + math.cos(ang) * wob
            pts.append((px, py))
        aa = a * 0.75 * math.sin(ph * math.pi)
        pth = smooth_path(pts, False)
        c.drawPath(pth, stroke(hexc("#ffffff", aa * 0.35), 10, blur=5))
        c.drawPath(pth, stroke(hexc("#ffffff", aa), 3.6))
    for side in (-1, 1):
        for k in range(3):
            ang = (math.pi if side < 0 else 0.0) + (k - 1) * 0.35
            ph = (t * 0.55 + k * 0.29 + (0.5 if side > 0 else 0)) % 1.0
            pts = []
            for j in range(7):
                d = r * (1.02 + 0.05 * ph) + j * r * 0.03 + ph * r * 0.08
                wob = math.sin(j * 1.2 + t * 2.0 + k) * r * 0.016
                pts.append((x + math.cos(ang) * d - math.sin(ang) * wob, y + math.sin(ang) * d + math.cos(ang) * wob))
            aa = a * 0.6 * math.sin(ph * math.pi)
            c.drawPath(smooth_path(pts, False), stroke(hexc("#ffffff", aa), 3.2))


def space_heat(c, t, dur, cues, params):
    draw_bg(c)
    tst = cues.get("steam", 2.4)
    tml = cues.get("melt", 4.4)
    tgl = cues.get("glow", 6.5)
    steam = ease_io((t - tst + 0.3) / 1.6)
    molten = ease_io((t - tml + 0.25) / 1.2)
    gl = ease_io((t - tgl + 0.2) / 1.4)
    steam_v = steam * (1 - smoothstep(tml - 0.5, tml + 0.3, t))
    x, y = CX, 860.0
    r = 290.0 + 22 * clamp(t / dur)
    heat = 0.35 * molten + 0.65 * gl
    if heat > 0:
        hot_glow(c, x, y, r, heat)
    if steam_v > 0:
        glow(c, x, y, r * 1.28, "#eef4ff", 0.42 * steam_v)
    atmosphere_halo(c, x, y, r, 1 - steam_v)
    earth(c, x, y, r, spin=3.0 + 0.16 * t, cloud_spin=0.03 * t, steam=steam_v, molten=molten, glow=gl)
    # steam wisps rising off the limb
    if steam_v > 0.02:
        steam_curls(c, x, y, r, t, steam_v)
    state = "steaming" if t < tml - 0.1 else ("melting" if t < tgl - 0.1 else "glowing")
    col = "#ffffff" if t < tst - 0.1 else ("#d8ecff" if state == "steaming" else ("#ffb27a" if state == "melting" else "#ffd9a0"))
    hud(c, [dict(label="SIZE", value="45%", a=fade_in(t, 0.2)),
            dict(label="SURFACE", value=state if t >= tst - 0.1 else "calm", values=["steaming", "melting", "glowing"],
                 a=fade_in(t, 0.4), emph=max(pulse(t, tst - 0.1), pulse(t, tml - 0.1), pulse(t, tgl - 0.1)),
                 color=col)])


def space_shrink(c, t, dur, cues, params):
    draw_bg(c)
    tmn = cues.get("moon", 5.8)
    tco = cues.get("country", 7.6)
    tci = cues.get("city", 9.4)
    keys = [(0.0, 5734.0), (tmn, 3474.0), (tco, 1000.0), (tci, 128.0), (max(dur, tci + 0.5), 118.0)]
    D = log_interp(t, keys)
    Rd = 300.0 * (D / 5734.0) ** 0.2
    kpx = Rd / (D / 2)
    x, y = CX, 800.0
    # comparison outlines (true sizes at this zoom)
    ma = fade_in(t, tmn - 1.3, 0.6) * (1 - fade_in(t, tco + 0.2, 0.8))
    mR = kpx * 1737.0
    if ma > 0 and mR < 1600:
        if mR < 560:
            moon(c, x, y, mR, spin=0.3, a=0.35 * ma)
        dashed_circle(c, x, y, mR, "#d0d8ea", 0.8 * ma, 3.0, 16, 10)
        label(c, "Moon", x, y - mR - 18, 34, "#e6ecf8", ma)
    ca = fade_in(t, tco - 1.0, 0.6) * (1 - fade_in(t, tci - 0.4, 0.6))
    if ca > 0:
        cR = kpx * 520.0
        country_outline(c, x, y + 10, cR, ca, progress=ease_out((t - tco + 1.0) / 1.1))
        label(c, "a country", x, y - cR * 0.9 - 26, 34, "#bdf5cc", ca)
    sa = fade_in(t, tci - 0.9, 0.6)
    heat = 1.0
    hot_glow(c, x, y, Rd, heat * 0.9)
    earth(c, x, y, Rd, spin=0.8 * t + 0.09 * t * t, glow=1.0, molten=1.0)
    if sa > 0:
        sw = kpx * 128.0
        city_skyline(c, x, y + Rd + 210, sw, sa)
        bp = stroke(hexc("#cfe0ff", 0.6 * sa), 2.0)
        bp.setPathEffect(skia.DashPathEffect.Make([8, 8], 0))
        c.drawLine(x - Rd, y, x - sw / 2, y + Rd + 210, bp)
        c.drawLine(x + Rd, y, x + sw / 2, y + Rd + 210, bp)
        label(c, "a city", x, y + Rd + 262, 34, "#ffe3a0", sa)
    hud(c, [dict(label="ACROSS", value=fmt_km(D), values=["12,742 km"], a=1.0,
                 emph=max(pulse(t, tmn - 0.1), pulse(t, tco - 0.1), pulse(t, tci - 0.1)) * 0.8),
            dict(label="SIZE", value=f"{D / 12742 * 100:.0f}%" if D > 127 else "1%", values=["100%"], a=1.0)])


def nebula(c, x, y, s, a=1.0, t=0.0):
    if a <= 0.01:
        return
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    g = skia.Paint(AntiAlias=True)
    g.setShader(radial_shader((0, 0), 260, [hexc("#7fe0ff", 0.30 * a), hexc("#4fb8e8", 0.25 * a), hexc("#ff7a59", 0.32 * a),
                                           hexc("#c23a6a", 0.18 * a), hexc("#5a1f55", 0.0)], [0.0, 0.35, 0.62, 0.8, 1.0]))
    c.drawOval(skia.Rect.MakeLTRB(-260, -205, 260, 205), g)
    for (rx, ry, col, aa, w) in ((175, 140, "#ff8a6a", 0.55, 40), (165, 128, "#ffd0a0", 0.35, 14), (120, 95, "#7ff0ff", 0.35, 30)):
        c.drawOval(skia.Rect.MakeLTRB(-rx, -ry, rx, ry), stroke(hexc(col, aa * a), w, blur=w * 0.5))
    rng = np.random.default_rng(77)
    for k in range(26):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.85, 1.12)
        c.drawCircle(math.cos(ang) * 172 * rr, math.sin(ang) * 136 * rr, rng.uniform(5, 13),
                     fill(hexc("#ffb08a", 0.35 * a), blur=4))
    c.restore()
    glow(c, x, y, 70 * s, "#cfe6ff", 0.6 * a)
    c.drawCircle(x, y, 7.5 * s, fill(hexc("#ffffff", a)))


def space_whitedwarf(c, t, dur, cues, params):
    draw_bg(c)
    tde = cues.get("dense", 2.9)
    tdw = cues.get("dwarf", 3.75)
    tgl = cues.get("glowing", 5.2)
    tdd = cues.get("dead", 6.9)
    mv = ease_io((t - tdw + 0.3) / 1.1)
    x = CX
    y = lerp(820.0, 560.0, mv)
    r = lerp(150.0, 110.0, mv)
    hot_glow(c, x, y, r, 1.0, white=0.7)
    earth(c, x, y, r, spin=1.2 * t, glow=1.0, molten=1.0, white=0.65)
    label(c, "Earth, ~130 km across", x, y + r + 54, 30, LABEL, fade_in(t, 0.3) * (1 - 0.0 * mv))
    na = ease_out((t - tdw) / 1.0)
    if na > 0:
        ny = 1140.0
        nebula(c, x, ny, 0.78 + 0.22 * na + 0.02 * clamp((t - tdd) / 2), na, t)
        label(c, "a white dwarf", x, ny + 180, 34, "#ffffff", fade_in(t, tgl - 0.2))
        label(c, "the leftover core of a dead star", x, ny + 224, 28, "#ffd2c0", fade_in(t, tdd - 0.3))
        label(c, "≈ as dense as", x, (y + r + ny - 160) / 2 + 34, 30, "#ffe7a8", na)
    hud(c, [dict(label="ACROSS", value="≈ 130 km", a=fade_in(t, 0.1)),
            dict(label="1 cm³ WEIGHS", value="≈ 5 tonnes", a=fade_in(t, tde - 0.3, 0.4), emph=pulse(t, tde - 0.2, 1.5),
                 color="#ffe7a8")])


def space_spin(c, t, dur, cues, params):
    draw_bg(c)
    tn = cues.get("nine", 1.85)
    x, y, r = CX, 830.0, 175.0
    hot_glow(c, x, y, r, 0.9, white=0.6)
    spin = 2 * math.pi * t / 9.0
    earth(c, x, y, r, spin=spin + 1.0, glow=1.0, molten=1.0, white=0.55)
    # motion arcs
    for k in range(3):
        ang0 = (t * 40 + k * 120) % 360
        pth = skia.Path()
        rr = r * (1.22 + 0.06 * k)
        pth.addArc(skia.Rect.MakeLTRB(x - rr, y - rr * 0.32, x + rr, y + rr * 0.32), ang0, 70)
        c.drawPath(pth, stroke(hexc("#ffffff", 0.5), 3.5, blur=1.5))
    # stopwatch
    sx, sy, sr = CX, 1260.0, 82.0
    c.drawCircle(sx, sy, sr + 10, fill(hexc("#0a1330", 0.8)))
    c.drawCircle(sx, sy, sr, stroke(hexc("#cfe0ff", 0.9), 5))
    c.drawRect(skia.Rect.MakeLTRB(sx - 12, sy - sr - 26, sx + 12, sy - sr - 8), fill(hexc("#cfe0ff", 0.9)))
    for k in range(9):
        ang = -math.pi / 2 + k * 2 * math.pi / 9
        c.drawLine(sx + math.cos(ang) * sr * 0.8, sy + math.sin(ang) * sr * 0.8, sx + math.cos(ang) * sr * 0.93,
                   sy + math.sin(ang) * sr * 0.93, stroke(hexc("#cfe0ff"), 3))
    hang = -math.pi / 2 + 2 * math.pi * (t % 9.0) / 9.0
    sweep = skia.Path()
    sweep.moveTo(sx, sy)
    sweep.arcTo(skia.Rect.MakeLTRB(sx - sr * 0.78, sy - sr * 0.78, sx + sr * 0.78, sy + sr * 0.78), -90,
                math.degrees(hang + math.pi / 2), False)
    sweep.close()
    c.drawPath(sweep, fill(hexc("#ffd36a", 0.25)))
    c.drawLine(sx, sy, sx + math.cos(hang) * sr * 0.78, sy + math.sin(hang) * sr * 0.78, stroke(hexc("#ffd36a"), 5))
    c.drawCircle(sx, sy, 6, fill(hexc("#ffd36a")))
    label(c, f"{t % 9.0:.1f} s", sx + sr + 30, sy + 12, 34, "#ffffff", 1.0, "left", "bold")
    hud(c, [dict(label="ONE DAY", value="24 h" if t < tn - 0.15 else "≈ 9 s", values=["≈ 9 s"], a=fade_in(t, 0.1),
                 emph=pulse(t, tn - 0.15, 1.6), color="#ffffff" if t < tn - 0.15 else "#ffe7a8")])


def space_ring(c, t, dur, cues, params):
    draw_bg(c)
    tf = cues.get("flattens", 2.2)
    tfl = cues.get("flinging", 3.1)
    tr = cues.get("ring", 4.55)
    x, y, r = CX, 840.0, 170.0
    ob = 0.28 * ease_io((t - tf + 0.2) / 1.2)
    ring_a = ease_io((t - tr + 0.4) / 1.2)
    tilt = 0.24
    hot_glow(c, x, y, r, 0.9, white=0.55)
    # particles flung from the equator (spiralling outward)
    rng = np.random.default_rng(9)
    parts = []
    if t > tfl - 0.2:
        for k in range(70):
            t0 = tfl - 0.2 + rng.uniform(0, 1.6)
            if t < t0:
                continue
            age = t - t0
            ang0 = rng.uniform(0, 2 * math.pi)
            rr = r * (1.0 + ob * 0.5) + (r * rng.uniform(0.75, 1.15)) * ease_out(age / 1.4)
            ang = ang0 + age * 2.5
            px = x + math.cos(ang) * rr
            py = y + math.sin(ang) * rr * tilt
            parts.append((math.sin(ang) > 0, px, py, rng.uniform(2.5, 5.5), clamp(age * 3) * (1 - 0.5 * ring_a)))
    # back half of ring + back particles
    ring_in, ring_out = r * 1.55, r * 2.15
    accretion_ring(c, x, y, ring_in, ring_out, tilt, ring_a * 0.9, front=False, t=t)
    for front, px, py, ps, pa in parts:
        if not front:
            c.drawCircle(px, py, ps * 2.2, fill(hexc("#ffb36a", 0.25 * pa), blur=3))
            c.drawCircle(px, py, ps, fill(hexc("#fff2d0", pa)))
    spin = t * (1.4 + 0.9 * t)
    earth(c, x, y, r, spin=spin, glow=1.0, molten=1.0, white=0.55, blur_spin=0.25, sx=1 + ob * 0.55, sy=1 - ob)
    accretion_ring(c, x, y, ring_in, ring_out, tilt, ring_a * 0.9, front=True, t=t)
    for front, px, py, ps, pa in parts:
        if front:
            c.drawCircle(px, py, ps * 2.2, fill(hexc("#ffb36a", 0.25 * pa), blur=3))
            c.drawCircle(px, py, ps, fill(hexc("#fff2d0", pa)))
    hud(c, [dict(label="ACROSS", value="≈ 44 km", a=fade_in(t, 0.1)),
            dict(label="SPIN", value="breaking apart" if t > tfl - 0.1 else "faster…", values=["breaking apart"],
                 a=fade_in(t, tf - 0.4), emph=pulse(t, tfl - 0.1, 1.4), color="#ffd0a0")])


def space_stadium(c, t, dur, cues, params):
    draw_bg(c)
    tsd = cues.get("stadium", 3.8)
    D = log_interp(t, [(0.0, 44.0), (tsd - 0.2, 0.30), (dur + 2, 0.29)])
    mv = ease_io((t - tsd + 0.9) / 1.0)
    x = lerp(CX, 330.0, mv)
    y = 820.0
    r = 210.0 * (D / 44.0) ** 0.12
    white = clamp(0.55 + 0.45 * (1 - (D / 44.0) ** 0.2))
    hot_glow(c, x, y, r, 1.0, white=white)
    accretion_ring(c, x, y, r * 1.6, r * 2.1, 0.24, 0.55, front=False, t=t, white=white * 0.6)
    earth(c, x, y, r, spin=t * 9.0, glow=1.0, molten=1.0, white=white, blur_spin=0.6)
    accretion_ring(c, x, y, r * 1.6, r * 2.1, 0.24, 0.55, front=True, t=t, white=white * 0.6)
    sa = ease_out((t - tsd + 0.2) / 0.8)
    if sa > 0:
        sx = lerp(1150.0, 790.0, sa)
        stadium(c, sx, y + r * 0.2, 2 * r, sa)
        bp = stroke(hexc("#cfe0ff", 0.65 * sa), 2.4)
        yb = y + r + 70
        c.drawLine(x - r, yb, x + r, yb, bp)
        c.drawLine(sx - r, yb, sx + r, yb, bp)
        for xx in (x - r, x + r, sx - r, sx + r):
            c.drawLine(xx, yb - 12, xx, yb + 12, bp)
        label(c, "≈ 300 m", x, yb + 50, 32, "#ffffff", sa)
        label(c, "a stadium", sx, yb + 50, 32, "#cfe0ff", sa)
    hud(c, [dict(label="ACROSS", value=fmt_km(D), values=["≈ 300 m"], a=1.0, emph=pulse(t, tsd - 0.1, 1.5))])


def space_walk(c, t, dur, cues, params):
    draw_bg(c)
    x, y, r = CX, 900.0, 130.0
    neutron_glow = 1.0
    glow(c, x, y, r * 4.5, "#6ea8ff", 0.30)
    glow(c, x, y, r * 2.0, "#cfe4ff", 0.45)
    pul = pulse(t, cues.get("ball", 4.1) - 0.1, 0.9)
    earth(c, x, y, r * (1 + 0.04 * pul), spin=t * 9.0, glow=1.0, molten=1.0, white=0.95, blur_spin=0.6)
    for key, fn, (ix, iy) in (("mountain", icon_mountain, (250, 430)), ("ocean", icon_wave, (540, 400)),
                              ("city", icon_city, (830, 430))):
        tc = cues.get(key)
        if tc is None:
            continue
        a_in = clamp((t - tc + 0.1) / 0.35)
        fall = ease_in((t - tc - 0.7) / 0.8)
        if a_in <= 0:
            continue
        px = lerp(ix, x, fall)
        py = lerp(iy, y, fall)
        sc = lerp(1.0, 0.08, fall)
        aa = a_in * (1 - smoothstep(0.85, 1.0, fall))
        fn(c, px, py, sc, aa, progress=clamp((t - tc + 0.1) / 0.5))
        if 0.9 < fall < 1.0 or (fall >= 1.0 and t - tc - 1.5 < 0.3):
            glow(c, x, y - r * 0.2, r * 0.9, "#ffffff", 0.4)
    tw = cues.get("walk", 4.8)
    wa = fade_in(t, tw - 0.5, 0.4)
    if wa > 0:
        ang = -math.pi / 2 + 0.9 * (t - tw + 0.5)
        fx, fy = x + math.cos(ang) * (r + 4), y + math.sin(ang) * (r + 4)
        trail = skia.Path()
        trail.addArc(skia.Rect.MakeLTRB(x - r - 4, y - r - 4, x + r + 4, y + r + 4), -90, math.degrees(ang + math.pi / 2))
        tp = stroke(hexc("#ffe3a0", 0.8 * wa), 3)
        tp.setPathEffect(skia.DashPathEffect.Make([6, 7], 0))
        c.drawPath(trail, tp)
        stick_walker(c, fx, fy, 1.5, t * 9, ang + math.pi / 2, "#ffffff", wa)
    hud(c, [dict(label="ACROSS", value="≈ 300 m", a=1.0)])
    label(c, "walk all the way around: ≈ 12 minutes", x, y + r + 110, 32, "#ffe7a8", wa)


def space_marble(c, t, dur, cues, params):
    draw_bg(c)
    tsq = cues.get("squeezed", 2.6)
    tt = cues.get("two", 4.0)
    tmb = cues.get("marble", 7.2)
    D_cm = log_interp(t, [(0.0, 30000.0), (tsq, 3000.0), (tt + 0.8, 1.8), (dur + 1, 1.78)])
    mv = ease_io((t - tmb + 0.5) / 0.9)
    x = lerp(CX, 380.0, mv)
    y = 780.0
    r = 100.0 * (D_cm / 1.8) ** 0.10
    tremble = 1.5 * math.sin(t * 37) * clamp((t - tt) / 2)
    glow(c, x, y, r * 6.0, "#6ea8ff", 0.35)
    glow(c, x, y, r * 2.6, "#d6e8ff", 0.55)
    earth(c, x + tremble, y, r, spin=t * 9.0, glow=1.0, molten=1.0, white=1.0, blur_spin=0.6)
    glow(c, x, y, r * 1.2, "#ffffff", 0.35)
    ra = ease_out((t - tt + 0.2) / 0.8)
    if ra > 0:
        cm = 2 * r / 1.8
        x0 = x - r
        ry = y + r + 120 + 40 * (1 - ra)
        ruler(c, x0, ry, cm, 3, ra)
        bp = stroke(hexc("#ffffff", 0.6 * ra), 2.0)
        bp.setPathEffect(skia.DashPathEffect.Make([7, 7], 0))
        c.drawLine(x - r, y, x - r, ry, bp)
        c.drawLine(x + r, y, x + r, ry, bp)
    ma = ease_out((t - tmb + 0.2) / 0.7)
    if ma > 0:
        marble(c, 740.0, y, r * (0.6 + 0.4 * ma), ma, t)
        label(c, "a marble", 740.0, y + r + 60, 32, "#cfe8ff", ma)
    hud(c, [dict(label="ACROSS", value=f"{D_cm / 1e5:.0f} km" if D_cm >= 1e5 else (f"{D_cm / 100:.0f} m" if D_cm >= 100 else f"{D_cm:.1f} cm"),
                 values=["300 m"], a=1.0, emph=pulse(t, tt - 0.2, 1.4)),
            dict(label="MASS", value="all of Earth", a=fade_in(t, tsq - 0.3, 0.5), color="#ffe7a8")])


def space_blackhole(c, t, dur, cues, params):
    tw = cues.get("wins", 0.9)
    tl = cues.get("light", 3.07)
    tb = cues.get("black", 6.5)
    push = 1.0 + 0.10 * ease_io((t - (tb - 1.0)) / 3.0)
    x, y = CX, 820.0
    R_sh = 112.0 * push
    form = ease_out((t - tw - 0.15) / 0.7)
    draw_bg(c)
    if form > 0:
        warp_bg(c, x, y, 540, r_sh=R_sh * form, theta_e=R_sh * 1.5 * form, alpha=1.0)
    if t < tw + 0.25:
        k = clamp((tw + 0.25 - t) / 0.25) if t > tw else 1.0
        rr = 62.0 * k * (1 + 0.03 * math.sin(t * 40))
        glow(c, x, y, rr * 6.0 + 1, "#6ea8ff", 0.35 * k)
        glow(c, x, y, rr * 2.6 + 1, "#d6e8ff", 0.55 * k)
        if rr > 1:
            earth(c, x, y, rr, spin=t * 9.0, glow=1.0, molten=1.0, white=1.0, blur_spin=0.6)
    fl = clamp(1 - abs(t - (tw + 0.2)) / 0.45)
    if fl > 0:
        glow(c, x, y, 520 * fl + 60, "#ffffff", 0.85 * fl)
    if form > 0:
        # light pulses spiralling in from every side
        for k in range(9):
            t0 = tl - 0.7 + (k % 3) * 0.35 + (k // 3) * 0.12
            age = t - t0
            T = 1.7
            if age < 0 or age > T + 0.3:
                continue
            ang0 = k * 2 * math.pi / 9 + 0.3
            r0 = 700.0
            def pos(u):
                rr = lerp(r0, R_sh * 1.0, ease_in(u) ** 0.7)
                return (x + math.cos(ang0 + 1.9 * ease_in(u)) * rr, y + math.sin(ang0 + 1.9 * ease_in(u)) * rr)
            uh = clamp(age / T)
            pts = [pos(max(0.0, uh - 0.30 * (1 - j / 14.0))) for j in range(15)]
            aa = clamp(1 - (age - T) / 0.3)
            pth = smooth_path(pts, False)
            c.drawPath(pth, stroke(hexc("#fff3c4", 0.22 * aa), 12, blur=6))
            c.drawPath(pth, stroke(hexc("#fff8e0", 0.75 * aa), 3.0))
            hx, hy = pts[-1]
            if uh < 1:
                c.drawCircle(hx, hy, 6, fill(hexc("#ffffff", aa)))
                glow(c, hx, hy, 26, "#fff2c0", 0.5 * aa)
        # a ray that tries to escape from just outside the horizon, turns, and falls back
        te = cues.get("escape", 3.59) - 0.2
        for j, side in enumerate((-1, 1)):
            age = t - te - j * 0.25
            T = 1.9
            if 0 < age < T + 0.4:
                ang0 = -math.pi / 2 + side * 0.5
                def epos(u):
                    out = math.sin(min(1.0, u) * math.pi) * R_sh * 1.6
                    rr = R_sh * 1.06 + out
                    a2 = ang0 + side * 2.2 * u
                    return (x + math.cos(a2) * rr, y + math.sin(a2) * rr)
                uh = clamp(age / T)
                pts = [epos(max(0.0, uh - 0.35 * (1 - q / 14.0))) for q in range(15)]
                aa = clamp(1 - (age - T) / 0.4)
                pth = smooth_path(pts, False)
                c.drawPath(pth, stroke(hexc("#bfe0ff", 0.25 * aa), 12, blur=6))
                c.drawPath(pth, stroke(hexc("#eaf6ff", 0.85 * aa), 3.0))
                if uh < 1:
                    hx, hy = pts[-1]
                    c.drawCircle(hx, hy, 6, fill(hexc("#ffffff", aa)))
        ring_a = ease_io((t - tb + 0.6) / 1.6)
        black_hole(c, x, y, R_sh * form, a_ring=ring_a, a_photon=form, t=t)
    if t > tb + 0.6:
        label(c, "a black hole, less than 2 cm across", CX, 1330, 32, "#ffe7c8", fade_in(t, tb + 0.6, 0.6))


def space_peppercorn(c, t, dur, cues, params):
    tp = cues.get("peppercorn", 1.7)
    twh = cues.get("whips", 2.6)
    tarm = cues.get("arm", 4.3)
    t8 = cues.get("eight", 6.4)
    t10 = cues.get("tenth", 9.2)
    tsp = cues.get("spirals", 12.0)
    tch = cues.get("chirp", 13.9)
    twv = cues.get("waves", 15.1)
    tsi = cues.get("silence", 19.9)
    tm = twv + 1.6  # merger
    x, y = CX, 760.0
    R_sh = 66.0
    Ro0 = 340.0
    # orbit radius
    if t < tsp:
        Ro = Ro0
    else:
        u = clamp((t - tsp) / (tm - tsp))
        Ro = lerp(Ro0, R_sh * 1.15, u ** 2.2)
    merged = t >= tm
    draw_bg(c)
    ripples = []
    if tch - 0.3 < t < tm + 3.0:
        for k in range(10):
            te = tch - 0.3 + k * (tm - tch + 0.3) / 10.0 * (1 - 0.35 * k / 10)
            if t < te:
                continue
            rc = (t - te) * 420.0
            lam = 42.0 * (1 - 0.55 * k / 10)
            amp = 55.0 * (0.4 + 0.6 * k / 10) * clamp(1 - (t - tm) / 3.0) * clamp(1 - rc / 1400)
            ripples.append((rc, lam, amp))
    warp_bg(c, x, y, 960 if ripples else 360, r_sh=R_sh, theta_e=R_sh * 1.45, ripples=ripples or None)
    for (rc, lam, amp) in ripples:
        if rc > 20:
            c.drawCircle(x, y, rc, stroke(hexc("#bcd6ff", 0.10 * clamp(amp / 120)), 3.0))
    blur_back = 0.0 if merged else clamp((t - twh - 0.4) / 0.8)

    def orbit_half(front):
        if blur_back <= 0:
            return
        c.save()
        clip = skia.Path()
        if front:
            clip.addRect(skia.Rect.MakeLTRB(0, y, W, H))
        else:
            clip.addRect(skia.Rect.MakeLTRB(0, 0, W, y))
        c.clipPath(clip, skia.ClipOp.kIntersect, True)
        ring = skia.Path()
        ring.addOval(skia.Rect.MakeLTRB(x - Ro, y - Ro * 0.38, x + Ro, y + Ro * 0.38))
        c.drawPath(ring, stroke(hexc("#d9dee8", 0.55 * blur_back), 15, blur=4))
        c.drawPath(ring, stroke(hexc("#ffffff", 0.75 * blur_back), 4))
        c.restore()

    orbit_half(False)
    black_hole(c, x, y, R_sh, a_ring=0.75, a_photon=1.0, t=t, ring_in=1.6, ring_out=2.4)
    orbit_half(True)
    # the Moon
    if not merged:
        spin_rate = 0.0 if t < twh else min(30.0, (t - twh) ** 2 * 9.0 + (t - twh) * 3.0)
        if t > tsp:
            spin_rate = 30.0 + (t - tsp) * 25.0
        ang_v = -0.15 + (twh and 0.0)
        if t >= twh:
            dt = t - twh
            ang_v = -0.15 + 3.0 * dt * dt + 1.0 * dt
        blur = clamp((t - twh - 0.4) / 0.8)
        mx, my = x + math.cos(ang_v) * Ro, y + math.sin(ang_v) * Ro * 0.38
        if blur < 1:
            moon(c, mx, my, 22, spin=0.2, a=1 - blur)
        if blur > 0:
            ph = (t * 3.3) % 1.0
            a0 = ph * 360
            hd = skia.Path()
            hd.addArc(skia.Rect.MakeLTRB(x - Ro, y - Ro * 0.38, x + Ro, y + Ro * 0.38), a0, 40)
            c.drawPath(hd, stroke(hexc("#ffffff", 0.9 * blur), 9, blur=2))
        # labels
        la = fade_in(t, tp - 0.3) * (1 - fade_in(t, twh + 1.6))
        if la > 0:
            gx, gy = x + Ro0 - 40, y - 250
            peppercorn(c, gx - 60, gy, 22, la)
            label(c, "≈", gx - 14, gy + 12, 34, "#ffffff", la)
            moon(c, gx + 34, gy, 22, spin=0.2, a=la)
            label(c, "the Moon ≈ a peppercorn", gx - 10, gy + 70, 30, "#e6ecf8", la)
            lp = stroke(hexc("#cfe0ff", 0.45 * la), 2.0)
            lp.setPathEffect(skia.DashPathEffect.Make([6, 7], 0))
            c.drawLine(gx + 34, gy + 26, mx, my - 26, lp)
    # arm's-length dimension
    aa = fade_in(t, tarm - 0.3) * (1 - fade_in(t, tsp - 0.3))
    if aa > 0:
        yb = y + 270
        c.drawLine(x, yb, x + Ro0, yb, stroke(hexc(CHALK, aa), 3.5))
        for xx in (x, x + Ro0):
            c.drawLine(xx, yb - 16, xx, yb + 16, stroke(hexc(CHALK, aa), 3.5))
        # chalk outline of an outstretched arm spanning the distance
        L = Ro0
        ay = yb - 70
        top = [(0, -30), (L * 0.24, -27), (L * 0.48, -22), (L * 0.68, -19), (L * 0.80, -15), (L * 0.88, -20),
               (L * 0.97, -17), (L * 1.0, -7)]
        bot = [(L * 0.99, 5), (L * 0.92, 11), (L * 0.85, 13), (L * 0.80, 14), (L * 0.66, 18), (L * 0.48, 21),
               (L * 0.24, 26), (0, 30)]
        arm = smooth_path([(x + px, ay + py) for px, py in top + bot], False, 0.35)
        pr = ease_out((t - tarm + 0.3) / 0.9)
        chalk(c, arm, CHALK, aa, 3.6, pr)
        thumb = smooth_path([(x + L * 0.84, ay - 17), (x + L * 0.88, ay - 36), (x + L * 0.93, ay - 33), (x + L * 0.92, ay - 20)], False, 0.4)
        chalk(c, thumb, CHALK, aa * clamp((pr - 0.8) * 5), 3.4, 1.0)
        fa = aa * 0.7 * clamp((pr - 0.85) * 6)
        if fa > 0:
            for (fy0, fy1, fx1) in ((-8, -6, 0.985), (-1, 0, 0.99), (6, 6, 0.965)):
                fp = skia.Path()
                fp.moveTo(x + L * 0.90, ay + fy0)
                fp.lineTo(x + L * fx1, ay + fy1)
                chalk(c, fp, CHALK, fa, 2.4, 1.0, 6.0)
        label(c, "≈ an arm's length", x + Ro0 / 2, yb + 52, 30, "#ffffff", aa)
    # chirp waveform HUD
    if t > tch - 0.4:
        ca = fade_in(t, tch - 0.4) * (1 - fade_in(t, tsi - 0.8, 1.0))
        bx0, by0, bw, bh = 110.0, 1230.0, 860.0, 160.0
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx0, by0, bw, bh), 18, 18)
        c.drawRRect(rr, fill(hexc("#0a1330", 0.75 * ca)))
        c.drawRRect(rr, stroke(hexc("#7895db", 0.6 * ca), 2.5))
        label(c, "gravitational-wave chirp", bx0 + 24, by0 + 36, 24, HUD_LABEL, ca, "left")
        prog = clamp((t - (tch - 0.4)) / (tm - tch + 0.4 + 0.6))
        n = 400
        pts = []
        for j in range(n):
            u = j / (n - 1)
            if u > prog:
                break
            tt = u * (tm - tch + 1.0)
            tau = max(0.02, (tm - tch + 0.3) - tt)
            if tt < tm - tch + 0.3:
                amp = 0.12 + 0.88 * (1 / (1 + tau * 1.3)) ** 1.2
                phs = 6.0 * (1 - tau / (tm - tch + 0.3)) ** 0.2 * 60 - 40 * tau ** 0.6
                v = amp * math.sin(phs)
            else:
                dd = tt - (tm - tch + 0.3)
                v = math.exp(-dd * 9) * math.sin(dd * 60)
            pts.append((bx0 + 24 + u * (bw - 48), by0 + 100 + v * 48))
        if len(pts) > 1:
            pth = skia.Path()
            pth.moveTo(*pts[0])
            for q in pts[1:]:
                pth.lineTo(*q)
            c.drawPath(pth, stroke(hexc("#9fd8ff", 0.35 * ca), 8, blur=4))
            c.drawPath(pth, stroke(hexc("#e8f6ff", ca), 2.6))
    # merger flash
    fl = clamp(1 - abs(t - tm) / 0.5)
    if fl > 0:
        glow(c, x, y, 380 * fl + 40, "#ffffff", 0.75 * fl)
    hud(c, [dict(label="ORBITS", value="8,000,000 / s", a=fade_in(t, t8 - 0.3) * (1 - fade_in(t, tsi - 1.0, 1.0)),
                 emph=pulse(t, t8 - 0.2, 1.4)),
            dict(label="SPEED", value="≈ 0.09 × light", a=fade_in(t, t10 - 0.3) * (1 - fade_in(t, tsi - 1.0, 1.0)),
                 emph=pulse(t, t10 - 0.2, 1.4), color="#ffe7a8")])
    small_note(c, "not to scale", 1030, 300, 0.55 * (1 - fade_in(t, tsi - 1.0, 1.0)))


def space_solar(c, t, dur, cues, params):
    draw_bg(c)
    tn = cues.get("notice", 5.2)
    tms = cues.get("mass", 9.2)
    tsun = cues.get("sun", 11.6)
    tmr = cues.get("mars", 14.4)
    tyr = cues.get("year", 20.1)
    tev = cues.get("every", 21.0)
    x, y = CX, 820.0
    ty = 0.5
    P_e = tyr / 3.0
    orbits = [("Mercury", 138.0, 0.24, "#b9b2a8", 6.5), ("Venus", 212.0, 0.62, "#f1d9a0", 11.0),
              ("Earth", 305.0, 1.0, None, 9.0), ("Mars", 440.0, 1.88, "#e0663a", 10.0)]
    # orbit lines
    ha = pulse(t, tn - 0.1, 1.8)
    for name, a_, per, col, rad in orbits:
        o = skia.Path()
        o.addOval(skia.Rect.MakeLTRB(x - a_, y - a_ * ty, x + a_, y + a_ * ty))
        c.drawPath(o, stroke(hexc("#4a6aa8", 0.55 + 0.35 * ha), 2.0))
    bodies = []
    for name, a_, per, col, rad in orbits:
        ang = math.pi / 2 + 2 * math.pi * t / (P_e * per)
        px, py = x + math.cos(ang) * a_, y + math.sin(ang) * a_ * ty
        bodies.append((py, name, px, py, col, rad, ang))
    sun_pulse = pulse(t, tsun - 0.1, 2.0)

    def draw_body(name, px, py, col, rad):
        if name == "Earth":
            glow(c, px, py, 40, "#ffb36a", 0.25)
            c.drawCircle(px, py, 13, stroke(hexc("#ffd9a0", 0.9), 3))
            c.drawCircle(px, py, rad, fill(hexc("#000000")))
            c.drawCircle(px, py, rad + 1.5, stroke(hexc("#ffffff", 0.9), 1.6))
        else:
            hl = pulse(t, tmr - 0.1, 2.4) if name == "Mars" else 0
            glow(c, px, py, rad * 3.5, col, 0.25 + 0.4 * hl)
            c.drawCircle(px, py, rad, fill(hexc(col)))
            if hl > 0:
                c.drawCircle(px, py, rad + 12 + 6 * hl, stroke(hexc("#ffd0b0", 0.9 * hl), 3))
    for b in sorted(bodies):
        if b[0] < y:
            draw_body(*b[1:6])
    # Sun
    glow(c, x, y, 230 * (1 + 0.15 * sun_pulse), "#ffb347", 0.35 + 0.15 * sun_pulse)
    glow(c, x, y, 110, "#fff2b0", 0.7)
    sp = skia.Paint(AntiAlias=True)
    sp.setShader(radial_shader((x - 12, y - 12), 70, [hexc("#ffffff"), hexc("#fff1a8"), hexc("#ffc24a")], [0, 0.5, 1]))
    c.drawCircle(x, y, 58, sp)
    for b in sorted(bodies):
        if b[0] >= y:
            draw_body(*b[1:6])
    # labels that follow the bodies
    for _, name, px, py, col, rad, ang in bodies:
        if name == "Earth":
            label(c, "Earth (a black hole)", px, py - 30, 28, "#ffe7c8", fade_in(t, 0.5))
            # gravity tether to the Sun
            ta = pulse(t, tsun - 0.1, 3.0)
            if ta > 0:
                tp = stroke(hexc("#ffe7a8", 0.6 * ta), 2.5)
                tp.setPathEffect(skia.DashPathEffect.Make([8, 8], -t * 30))
                c.drawLine(x, y, px, py, tp)
            ma = fade_in(t, tms - 0.2, 0.5) * (1 - fade_in(t, tyr - 2.5))
            if ma > 0:
                label(c, "same mass → same pull → same orbit", CX, 1300, 32, "#ffffff", ma)
        elif name == "Mars":
            label(c, "Mars", px, py + 40, 26, "#ffc2a6", 0.8 + 0.2 * pulse(t, tmr - 0.1, 2.4))
        elif name == "Venus":
            label(c, "Venus", px, py + 36, 22, "#cfd6ea", 0.55)
    label(c, "Sun", x, y + 100, 30, "#fff1c0", 0.9)
    laps = int(t / P_e)
    yrs = f"{laps} year" + ("" if laps == 1 else "s")
    ye = max(pulse(t, tyr - 0.1, 1.2), pulse(t, tev - 0.05, 1.2))
    for k in range(1, 4):
        ye = max(ye, 0.6 * pulse(t, k * P_e - 0.05, 0.9))
    hud(c, [dict(label="EARTH'S ORBIT", value="unchanged", a=fade_in(t, tn - 0.3, 0.5), emph=pulse(t, tn - 0.2, 1.6),
                 color="#bdf5cc"),
            dict(label="TIME", value=yrs, values=["0 years", "3 years"], a=fade_in(t, 0.3), emph=ye, color="#ffe7a8")])


SCENES = {
    "space_bubble": space_bubble,
    "space_gravity": space_gravity,
    "space_mars": space_mars,
    "space_heat": space_heat,
    "space_shrink": space_shrink,
    "space_whitedwarf": space_whitedwarf,
    "space_spin": space_spin,
    "space_ring": space_ring,
    "space_stadium": space_stadium,
    "space_walk": space_walk,
    "space_marble": space_marble,
    "space_blackhole": space_blackhole,
    "space_peppercorn": space_peppercorn,
    "space_solar": space_solar,
}
