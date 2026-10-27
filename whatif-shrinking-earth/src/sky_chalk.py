"""Starlight 'chalk' drawings that appear in the night sky above the sisters.

Each overlay: fn(c, t, dur, cues, params, rect) draws in SCREEN space inside
rect=(x0, y0, x1, y1). The Moon sits small at the top-right corner of the
frame during these shots, so content near the top stays left of x~840.
"""
import math

import numpy as np
import skia

from chalk import (BLUE, COOL, PINK, WARM, appear, cue, dotted, glow_fill, glow_path, hand_creases_point, label,
                   p_arrow, p_burst, p_circle, p_cloud, p_eye, p_hill, p_house, p_lines, p_moon_icon, p_open_hand,
                   p_point_hand, p_ruler, p_school, p_smooth, p_wave, pop, ramp, trim_path)
from gfx import clamp, ease_io, ease_out, fill, hexc, lerp, smooth_path, stroke


def _geom(rect):
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    u = min(w / 940.0, h / 690.0)
    cx = (x0 + x1) / 2 - 40 * u
    cy = (y0 + y1) / 2 + 30 * u
    return cx, cy, u


def xf(path, x, y, s=1.0, rot=0.0, sx=None):
    m = skia.Matrix()
    m.setScale(s if sx is None else sx, s)
    if rot:
        m.postRotate(math.degrees(rot))
    m.postTranslate(x, y)
    out = skia.Path(path)
    out.transform(m)
    return out


def _icon(c, path, x, y, s, color=COOL, width=5.0, alpha=1.0, draw=1.0, rot=0.0):
    if s <= 0.01 or alpha <= 0.01:
        return
    glow_path(c, xf(path, x, y, s, rot), color, width, alpha, draw)


# ----------------------------------------------------------------------------
def sky_list(c, t, dur, cues, params, rect):
    """Ground, oceans, air, Moon pop in; all shrink; a level balance: just as heavy."""
    cx, cy, u = _geom(rect)
    names = ["ground", "oceans", "air", "moon"]
    paths = [p_hill(), p_wave(), p_cloud(), p_moon_icon(46)]
    colors = [COOL, BLUE, COOL, WARM]
    labels = ["ground", "oceans", "air", "Moon"]
    t_sm = cue(cues, "smaller", dur * 0.6)
    t_hv = cue(cues, "heavy", dur * 0.85)
    k = ramp(t, t_sm - 0.1, 1.5)
    gy = cy - 70 * u
    for i, nm in enumerate(names):
        t0 = cue(cues, nm, 0.4 + i * 0.6)
        s_pop = pop(t, t0 - 0.05)
        if s_pop <= 0:
            continue
        x_full = cx + (-300 + i * 200) * u
        x = lerp(x_full, cx + (-300 + i * 200) * u * 0.28, k)
        y = lerp(gy, gy + 10 * u, k)
        s = s_pop * u * lerp(1.0, 0.42, k)
        _icon(c, paths[i], x, y, s, colors[i], 5.0)
        label(c, labels[i], x_full, gy + 118 * u, 30 * u, colors[i], (1 - k) * appear(t, t0, 0.3))
    # shrink arrows
    if 0.02 < k < 0.98:
        a = math.sin(k * math.pi)
        for sgn in (-1, 1):
            glow_path(c, p_arrow(cx + sgn * 420 * u, gy, cx + sgn * 250 * u, gy, 16 * u), WARM, 4.0, a)
    # balance: big dashed "before" vs small solid "now", beam level
    b = pop(t, t_hv - 0.35, 0.4)
    if b > 0:
        by = cy + 150 * u
        bw = 270 * u
        al = min(1.0, b)
        glow_path(c, p_lines([(cx, by + 80 * u), (cx, by)], [(cx - 40 * u, by + 80 * u), (cx + 40 * u, by + 80 * u)]),
                  COOL, 4.5, al)
        glow_path(c, p_lines([(cx - bw, by), (cx + bw, by)]), COOL, 5.0, al)
        for sgn in (-1, 1):
            px = cx + sgn * bw
            glow_path(c, p_lines([(px, by), (px - 40 * u, by + 50 * u)], [(px, by), (px + 40 * u, by + 50 * u)],
                                 [(px - 55 * u, by + 50 * u), (px + 55 * u, by + 50 * u)]), COOL, 3.5, al)
        # left: ghost of the original size (dashed)
        gp = p_circle(46 * u, cx - bw, by + 2 * u)
        ghost = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                           Color=hexc(COOL, 0.75 * al))
        ghost.setPathEffect(skia.DashPathEffect.Make([10.0, 8.0], 0.0))
        c.save()
        c.translate(0, -48 * u)
        c.drawPath(gp, ghost)
        c.restore()
        label(c, "before", cx - bw, by + 95 * u, 26 * u, COOL, al)
        glow_fill(c, p_circle(17 * u, cx + bw, by + 31 * u), WARM, al)
        label(c, "now", cx + bw, by + 95 * u, 26 * u, WARM, al)
        label(c, "same weight", cx, by - 30 * u, 32 * u, WARM, appear(t, t_hv, 0.3))


def sky_map(c, t, dur, cues, params, rect):
    """Home and school joined by a dotted road that stretches far away."""
    cx, cy, u = _geom(rect)
    t_far = cue(cues, "far", dur * 0.55)
    k = ramp(t, t_far - 0.15, 0.9)
    hx, hy = cx - 300 * u, cy + 90 * u
    sx = lerp(cx + 230 * u, cx + 330 * u, k)
    sy = lerp(cy - 20 * u, cy - 120 * u, k)
    ss = lerp(1.0, 0.62, k)
    a0 = pop(t, 0.05)
    _icon(c, p_house(), hx, hy, u * a0, WARM, 5.0)
    label(c, "home", hx, hy + 85 * u, 28 * u, WARM, appear(t, 0.2))
    a1 = pop(t, 0.35)
    _icon(c, p_school(), sx, sy, u * ss * a1, COOL, 5.0)
    label(c, "school", sx, sy + (70 * ss + 25) * u, 28 * u, COOL, appear(t, 0.5))
    # winding road; extra wiggles appear as it stretches
    n = 60
    pts = []
    for i in range(n + 1):
        f = i / n
        x = lerp(hx + 60 * u, sx - 70 * u * ss, f)
        y = lerp(hy, sy + 40 * u * ss, f)
        y += math.sin(f * math.pi) * -120 * u
        y += math.sin(f * math.pi * (3 + 4 * k)) * 26 * u * k
        pts.append((x, y))
    draw = ramp(t, 0.3, 1.0)
    dotted(c, pts, COOL, 3.8 * u + 0.6, 21 * u * (1 - 0.3 * k), draw)
    # little bus trundling along
    if draw > 0.3:
        f = clamp(0.12 + 0.18 * max(0.0, t - 0.6) / 2.5, 0, 0.9)
        i = int(f * n)
        bx, by = pts[i]
        bus = skia.Path()
        bus.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-26, -16, 26, 10), 6, 6))
        bus.addCircle(-14, 12, 6)
        bus.addCircle(14, 12, 6)
        bus.addRect(skia.Rect.MakeLTRB(-18, -10, -4, -1))
        bus.addRect(skia.Rect.MakeLTRB(2, -10, 16, -1))
        _icon(c, bus, bx, by - 20 * u, u, WARM, 3.5, appear(t, 0.8))


def _cup_hand(mirror=1):
    pts = [(-62, 105), (-80, 30), (-66, -55), (-26, -96), (18, -86), (30, -66), (6, -46), (-6, 0),
           (8, 44), (34, 64), (28, 90), (-4, 110)]
    pts = [(x * mirror, y) for x, y in pts]
    return smooth_path(pts, True, 0.5)


def _earth_path(r):
    p = p_circle(r)
    # continents as soft blobs
    for (x, y, sc, seed) in ((-0.35, -0.25, 0.38, 1), (0.25, 0.1, 0.45, 2), (-0.1, 0.5, 0.25, 3)):
        pts = []
        for k in range(9):
            a = k / 9 * math.tau
            rr = sc * (0.75 + 0.25 * math.sin(a * 3 + seed * 1.7) + 0.12 * math.cos(a * 5 + seed))
            pts.append(((x + math.cos(a) * rr * 0.9) * r, (y + math.sin(a) * rr * 0.7) * r))
        p.addPath(smooth_path(pts, True, 0.5))
    return p


def sky_squeeze_earth(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_sq = cue(cues, "squeeze", dur * 0.6)
    k = ramp(t, t_sq - 0.15, 0.45)
    r0 = 120 * u
    ex, ey = cx + 20 * u, cy - 10 * u
    sq = math.sin(clamp((t - t_sq + 0.15) / 0.6) * math.pi) * 0.12 if t > t_sq - 0.15 else 0.0
    s = lerp(1.0, 0.7, k)
    a = pop(t, 0.05)
    c.save()
    c.translate(ex, ey)
    c.scale(s * (1 - sq) * a, s * (1 + sq * 0.6) * a)
    glow_fill(c, p_circle(r0), "#3d7fd6", 0.35, 20, 0.35)
    glow_path(c, _earth_path(r0), COOL, 4.0 / max(0.3, s), 1.0)
    c.restore()
    gap = lerp(r0 + 105 * u, r0 * 0.7 + 78 * u, k)
    ha = appear(t, 0.25, 0.4)
    hand = p_open_hand()
    for sgn in (-1, 1):
        m = skia.Matrix()
        m.setScale(-sgn * 1.15 * u, 1.15 * u)
        m.postRotate(sgn * -28)
        m.postTranslate(ex + sgn * gap, ey + 28 * u)
        hp = skia.Path(hand)
        hp.transform(m)
        glow_fill(c, hp, "#ffcf9a", 0.16 * ha, 10, 0.2)
        glow_path(c, hp, WARM, 5.0, ha)
    # motion ticks when squeezing
    if 0.0 < k < 1.0 or (t_sq < t < t_sq + 0.6):
        al = math.sin(clamp((t - t_sq + 0.15) / 0.8) * math.pi)
        for sgn in (-1, 1):
            for j in (-1, 0, 1):
                x0 = ex + sgn * (gap + 120 * u)
                glow_path(c, p_lines([(x0, ey + j * 45 * u), (x0 + sgn * 50 * u, ey + j * 55 * u)]), WARM, 4.0, al)
    if t > t_sq:
        label(c, "squeeze!", ex, ey + r0 + 105 * u, 34 * u, WARM, appear(t, t_sq + 0.1) * (1 - ramp(t, t_sq + 1.2, 0.4)))


def sky_ruler_house_eye(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    items = [("ruler", p_ruler(), -290, WARM), ("house", p_house(110, 100), 0, COOL), ("eyes", p_eye(), 270, BLUE)]
    t_tog = cue(cues, "together", dur * 0.85)
    k = ramp(t, t_tog - 0.25, 0.5)
    y = cy - 30 * u
    for i, (nm, p, dx, col) in enumerate(items):
        t0 = cue(cues, nm, 0.3 + 0.5 * i)
        s = pop(t, t0 - 0.05)
        if s <= 0:
            continue
        x_full = cx + dx * u
        x = cx + dx * u * lerp(1.0, 0.5, k)
        # ghost of the original size during/after shrink
        if k > 0.02:
            ghost = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                               Color=hexc(col, 0.45 * (1 - 0.5 * k)))
            ghost.setPathEffect(skia.DashPathEffect.Make([9.0, 9.0], 0.0))
            c.drawPath(xf(p, x_full, y, u * 1.25), ghost)
        _icon(c, p, x, y, s * u * 1.25 * lerp(1.0, 0.5, k), col, 5.0)
        label(c, nm, x_full, y + 110 * u, 30 * u, col, appear(t, t0, 0.3) * (1 - k))
    if k > 0.02:
        label(c, "all together", cx, y + 150 * u, 36 * u, WARM, k)


def sky_pool(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_pop = cue(cues, "pop", dur * 0.5)
    t_pool = cue(cues, "pool", dur * 0.77)
    pool_k = appear(t, t_pool - 0.25, 0.5)
    # thickening air: dots get more numerous and closer
    dens = ramp(t, 0.0, 3.0)
    n = int(14 + 40 * dens)
    rng = np.random.default_rng(5)
    xs = rng.uniform(-1, 1, 60)
    ys = rng.uniform(-1, 1, 60)
    ph = rng.uniform(0, 6.28, 60)
    air_a = 1 - pool_k * 0.85
    spread = lerp(1.0, 0.72, dens)
    for i in range(n):
        x = cx + xs[i] * 360 * u * spread + math.sin(t * 0.9 + ph[i]) * 10 * u
        y = cy - 20 * u + ys[i] * 230 * u * spread + math.cos(t * 0.7 + ph[i]) * 8 * u
        if y < 380 and x > 820:
            continue
        a = min(1.0, (n - i) / 6.0) * air_a
        c.drawCircle(x, y, 7 * u, stroke(hexc(COOL, 0.8 * a), 2.5))
        c.drawCircle(x, y, 11 * u, fill(hexc(COOL, 0.10 * a), blur=6))
    if t < t_pool:
        label(c, "air", cx - 300 * u, cy - 220 * u, 30 * u, COOL, appear(t, 0.3) * (1 - pool_k))
    # POP!
    bp = pop(t, t_pop - 0.05, 0.3, 2.2)
    fade = 1 - ramp(t, t_pop + 1.1, 0.4)
    if bp > 0 and fade > 0:
        bx, by = cx - 140 * u, cy - 150 * u
        glow_fill(c, xf(p_burst(52, 92, 11, 0.2), bx, by, u * bp), WARM, 0.25 * fade, 18, 0.3)
        glow_path(c, xf(p_burst(52, 92, 11, 0.2), bx, by, u * bp), WARM, 4.5, fade)
        label(c, "POP!", bx, by + 16 * u * bp, 46 * u * bp, "#fff6dc", fade, "extrabold")
    # swimming pool cross-section
    if pool_k > 0:
        px0, px1 = cx - 290 * u, cx + 290 * u
        py0, py1 = cy - 40 * u, cy + 230 * u
        tank = p_lines([(px0, py0 - 40 * u), (px0, py1), (px1, py1), (px1, py0 - 40 * u)])
        glow_path(c, tank, COOL, 5.0, pool_k, draw=pool_k)
        wpts = [(px0 + i * (px1 - px0) / 24, py0 + math.sin(i * 0.9 + t * 3) * 7 * u) for i in range(25)]
        glow_path(c, smooth_path(wpts, False, 0.5), BLUE, 4.0, pool_k, draw=pool_k)
        # ladder
        lad = p_lines([(px1 - 40 * u, py0 - 60 * u), (px1 - 40 * u, py0 + 60 * u)],
                      [(px1 - 70 * u, py0 - 60 * u), (px1 - 70 * u, py0 + 60 * u)])
        for j in range(4):
            yy = py0 - 50 * u + j * 32 * u
            lad.moveTo(px1 - 70 * u, yy)
            lad.lineTo(px1 - 40 * u, yy)
        glow_path(c, lad, COOL, 3.5, pool_k)
        # swimmer at the bottom: head, body, arms; pinching nose
        sx, sy = cx - 60 * u, py1 - 45 * u
        sw = skia.Path()
        sw.addCircle(sx, sy - 40 * u, 20 * u)
        sw.moveTo(sx, sy - 20 * u)
        sw.lineTo(sx + 10 * u, sy + 25 * u)
        sw.moveTo(sx + 10 * u, sy + 25 * u)
        sw.lineTo(sx - 25 * u, sy + 40 * u)
        sw.moveTo(sx + 10 * u, sy + 25 * u)
        sw.lineTo(sx + 40 * u, sy + 38 * u)
        sw.moveTo(sx + 3 * u, sy - 5 * u)
        sw.lineTo(sx - 18 * u, sy - 30 * u)
        sw.moveTo(sx + 3 * u, sy - 5 * u)
        sw.lineTo(sx + 32 * u, sy - 10 * u)
        glow_path(c, sw, WARM, 4.5, pool_k)
        for j in range(6):
            ph = (t * 0.55 + j * 0.17) % 1.0
            bx = sx + 12 * u + math.sin(j * 2.1 + t * 3) * 8 * u
            by = sy - 70 * u - ph * (sy - 70 * u - py0) * 0.95
            c.drawCircle(bx, by, (4 + 3 * ph) * u, stroke(hexc(COOL, 0.8 * pool_k * (1 - ph * 0.6)), 2.2))
        label(c, "bottom of the pool", cx, py1 + 55 * u, 30 * u, COOL, appear(t, t_pool + 0.2))


def sky_sun_arcs(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_sh = cue(cues, "shorter", dur * 0.5)
    hy = cy + 170 * u
    R = 300 * u
    a = appear(t, 0.0, 0.4)
    glow_path(c, p_lines([(cx - 400 * u, hy), (cx + 400 * u, hy)]), COOL, 4.0, a)
    # phase integral of day speed
    steps = 160
    phase = 0.0
    dt = t / steps if t > 0 else 0
    for i in range(steps):
        tt = (i + 0.5) * dt
        P = 2.6 if tt < t_sh else max(0.5, 2.6 * math.exp(-(tt - t_sh) * 1.6))
        phase += dt / P
    frac = phase % 1.0
    days = int(phase) + 1
    # dotted trail of the sun's arc
    arc = [(cx - R * math.cos(f * math.pi), hy - R * math.sin(f * math.pi) * 0.8) for f in np.linspace(0, 1, 40)]
    dotted(c, arc, COOL, 2.5, 22 * u, 1.0, 0.5 * a)
    if frac < 0.5:
        f = frac / 0.5
        x, y = cx - R * math.cos(f * math.pi), hy - R * math.sin(f * math.pi) * 0.8
        sun = p_circle(26 * u, x, y)
        for k in range(8):
            ang = k * math.pi / 4 + t
            sun.moveTo(x + math.cos(ang) * 38 * u, y + math.sin(ang) * 38 * u)
            sun.lineTo(x + math.cos(ang) * 52 * u, y + math.sin(ang) * 52 * u)
        glow_fill(c, p_circle(26 * u, x, y), WARM, 0.35 * a)
        glow_path(c, sun, WARM, 4.5, a)
    else:
        f = (frac - 0.5) / 0.5
        x, y = cx - R * math.cos(f * math.pi), hy - R * math.sin(f * math.pi) * 0.8
        m = skia.Path()
        m.addCircle(x, y, 22 * u)
        glow_path(c, m, COOL, 4.0, a)
        glow_fill(c, p_circle(18 * u, x + 9 * u, y - 5 * u), "#0b1636", a, 2, 0.0)
    label(c, f"day {days}", cx, hy + 60 * u, 34 * u, WARM, a)
    if t > t_sh:
        label(c, "faster and faster", cx, hy + 105 * u, 28 * u, COOL, appear(t, t_sh + 0.3))


def _skater(arm_in, leg_k=1.0):
    """Skater figure centred at hips (0,0), facing +x."""
    p = skia.Path()
    p.addCircle(0, -150, 24)                 # head
    p.moveTo(-14, -175)
    p.quadTo(-30, -195, -6, -196)            # bun
    p.moveTo(0, -126)
    p.lineTo(0, -40)                          # torso
    p.moveTo(-40, 10)
    p.lineTo(0, -40)
    p.lineTo(40, 10)                          # skirt
    p.lineTo(-40, 10)
    p.moveTo(-8, 10)
    p.lineTo(-10, 110)                        # standing leg
    p.moveTo(-34, 112)
    p.lineTo(18, 112)                         # blade
    p.moveTo(10, 10)
    p.lineTo(lerp(40, 22, leg_k), lerp(70, 60, leg_k))
    p.lineTo(lerp(60, 18, leg_k), lerp(60, 100, leg_k))
    # arms
    if arm_in < 0.5:
        k = arm_in * 2
        for s in (-1, 1):
            p.moveTo(0, -112)
            p.lineTo(s * lerp(120, 60, k), lerp(-118, -105, k))
    else:
        k = (arm_in - 0.5) * 2
        for s in (-1, 1):
            p.moveTo(0, -112)
            p.lineTo(s * lerp(60, 26, k), lerp(-105, -80, k))
            p.lineTo(s * lerp(40, -6, k), lerp(-90, -96, k))
    return p


def sky_skater(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_out = cue(cues, "out", dur * 0.37)
    t_pull = cue(cues, "pull", dur * 0.83)
    arm_in = ramp(t, t_pull - 0.05, 0.3)
    # rotation phase: slow -> fast
    steps = 120
    ph = 0.0
    dt = t / steps if t > 0 else 0
    for i in range(steps):
        tt = (i + 0.5) * dt
        w = 0.15 if tt < t_out else (0.55 if tt < t_pull else 0.55 + 2.4 * ease_out((tt - t_pull) / 0.4))
        ph += w * dt
    sx = math.cos(ph * math.tau)
    sxa = max(0.08, abs(sx)) * (1 if sx >= 0 else -1)
    a = appear(t, 0.0, 0.4)
    x, y = cx - 30 * u, cy + 40 * u
    m = skia.Matrix()
    m.setScale(sxa * 1.05 * u, 1.05 * u)
    m.postTranslate(x, y)
    p = skia.Path(_skater(arm_in))
    p.transform(m)
    glow_path(c, p, COOL, 5.0, a)
    # ice + spin swooshes
    ice = skia.Path()
    ice.addOval(skia.Rect.MakeLTRB(x - 220 * u, y + 105 * u, x + 220 * u, y + 145 * u))
    glow_path(c, ice, BLUE, 3.0, 0.7 * a)
    speed = 0.15 if t < t_out else (0.55 if t < t_pull else 3.0)
    n_sw = 1 if speed < 0.3 else (2 if speed < 1 else 4)
    for k in range(n_sw):
        rr = (150 + 30 * k) * u
        a0 = (ph * 360 * 0.7 + k * 90) % 360
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeLTRB(x - rr, y - 60 * u - rr * 0.45, x + rr, y - 60 * u + rr * 0.45), a0, 70)
        glow_path(c, arc, WARM, 3.5, a * min(1.0, speed))
    lab = "arms out: slow" if t < t_pull else "arms in: FAST"
    label(c, lab, x, y + 205 * u, 32 * u, WARM, appear(t, t_out) if t < t_pull else appear(t, t_pull))


def sky_clock(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_half = cue(cues, "half", dur * 0.5)
    t_six = cue(cues, "six", dur * 0.82)
    ccx, ccy = cx - 90 * u, cy - 20 * u
    R = 160 * u
    a = appear(t, 0.0, 0.4)
    face = p_circle(R, ccx, ccy)
    for k in range(24):
        ang = k / 24 * math.tau - math.pi / 2
        L = 26 if k % 6 == 0 else 12
        face.moveTo(ccx + math.cos(ang) * (R - 8 * u), ccy + math.sin(ang) * (R - 8 * u))
        face.lineTo(ccx + math.cos(ang) * (R - (8 + L) * u), ccy + math.sin(ang) * (R - (8 + L) * u))
    glow_path(c, face, COOL, 5.0, a)
    # sun at top, moon at bottom of the 24 h dial
    glow_path(c, p_circle(12 * u, ccx, ccy - R + 58 * u), WARM, 3.5, a)
    glow_path(c, xf(p_moon_icon(11), ccx, ccy + R - 58 * u, u), COOL, 3.0, a)
    # hand: integrate speed (1 turn / 4.5 s, then 4x faster)
    steps = 140
    ang = 0.0
    dt = t / steps if t > 0 else 0
    for i in range(steps):
        tt = (i + 0.5) * dt
        w = 1 / 4.5 if tt < t_half else (1 / 4.5) * (1 + 3 * ease_out((tt - t_half) / 0.8))
        ang += w * dt * math.tau
    hx = ccx + math.cos(ang - math.pi / 2) * R * 0.78
    hy = ccy + math.sin(ang - math.pi / 2) * R * 0.78
    glow_path(c, p_lines([(ccx, ccy), (hx, hy)]), WARM, 6.0, a)
    glow_fill(c, p_circle(9 * u, ccx, ccy), WARM, a)
    # Earth shrinks to half at `half`
    k = ramp(t, t_half - 0.1, 0.7)
    ex, ey = cx + 250 * u, cy - 10 * u
    er = lerp(70, 35, k) * u
    glow_fill(c, p_circle(er, ex, ey), "#3d7fd6", 0.35 * a, 12, 0.3)
    glow_path(c, xf(_earth_path(70), ex, ey, er / 70), COOL, 4.0, a)
    if k > 0.05:
        label(c, "half size", ex, ey + 110 * u, 30 * u, COOL, k)
    # label: 1 day = 24 h -> 6 h
    six = pop(t, t_six - 0.05, 0.35)
    if six <= 0:
        label(c, "1 day = 24 h", ccx, ccy + R + 70 * u, 40 * u, WARM, a)
    else:
        label(c, "1 day = 6 h", ccx, ccy + R + 70 * u, 40 * u * max(0.6, six), "#fff6dc", min(1.0, six))


def sky_pizza(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_pz = cue(cues, "pizza", 0.4)
    k = ramp(t, t_pz, 1.4)
    a = appear(t, 0.0, 0.3)
    fx, fy = cx - 20 * u, cy + 60 * u
    # fist with the index finger raised; the fingertip sits at (fx, fy)
    hx, hy = fx - 27 * 1.1 * u, fy + 112 * 1.1 * u
    hp = xf(p_point_hand(), hx, hy, 1.1 * u)
    glow_fill(c, hp, "#ffcf9a", 0.16 * a, 10, 0.2)
    glow_path(c, hp, WARM, 4.5, a)
    glow_path(c, xf(hand_creases_point(), hx, hy, 1.1 * u), WARM, 3.0, 0.7 * a, shadow=False)
    rx = lerp(110, 200, k) * u
    ry = lerp(34, 20, k) * u
    dy = fy - 12 * u
    dough = skia.Path()
    dough.addOval(skia.Rect.MakeLTRB(fx - rx, dy - ry, fx + rx, dy + ry))
    glow_fill(c, dough, "#f3d9a4", 0.30 * a, 10, 0.3)
    glow_path(c, dough, WARM, 5.0, a)
    # spinning flour dots on the rim
    spin = t * (2.0 + 5.0 * k)
    for j in range(10):
        ang = spin + j * math.tau / 10
        x = fx + math.cos(ang) * rx * 0.75
        y = dy + math.sin(ang) * ry * 0.75
        if math.sin(ang) > -0.2:
            c.drawCircle(x, y, 3.5 * u, fill(hexc(WARM, 0.9 * a)))
    # bits flung off the rim
    if k > 0.05:
        for j in range(12):
            ph = (t * 0.9 + j / 12) % 1.0
            ang = j * 2.3 + 1.0
            d = rx + ph * 160 * u
            x = fx + math.cos(ang) * d
            y = dy + math.sin(ang) * d * 0.3 - ph * 20 * u
            c.drawCircle(x, y, 4 * u * (1 - ph * 0.5), fill(hexc(WARM, k * (1 - ph))))
    for s in (-1, 1):
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeLTRB(fx - rx - 40 * u, dy - ry - 30 * u, fx + rx + 40 * u, dy + ry + 30 * u),
                   (0 if s > 0 else 180) + (t * 200) % 40, 50)
        glow_path(c, arc, COOL, 3.0, a * (0.4 + 0.6 * k))


def sky_marble(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_b = cue(cues, "blue", dur * 0.35)
    t_one = cue(cues, "one", dur * 0.62)
    t_b2 = cue(cues, "blue2", dur * 0.87)
    a = pop(t, 0.2, 0.5)
    if a <= 0:
        return
    shr = ramp(t, t_one - 0.1, 0.8)
    dark = ramp(t, t_b2 - 0.1, 1.0)
    mx, my = cx - 10 * u, cy - 10 * u
    r = lerp(125, 80, shr) * u * a
    pulse = math.exp(-((t - t_b) / 0.6) ** 2) if t > t_b - 1 else 0.0
    # glow
    c.drawCircle(mx, my, r * 1.6, fill(hexc("#5aa8ff", (0.28 + 0.25 * pulse) * (1 - dark)), blur=r * 0.5))
    pnt = skia.Paint(AntiAlias=True)
    c1 = hexc(_mix("#7cc4ff", "#05060c", dark))
    c2 = hexc(_mix("#1d5fbf", "#020308", dark))
    c3 = hexc(_mix("#0d2a66", "#000000", dark))
    pnt.setShader(skia.GradientShader.MakeRadial(skia.Point(mx - r * 0.35, my - r * 0.35), r * 1.5,
                                                 [c1, c2, c3], [0.0, 0.55, 1.0]))
    c.drawCircle(mx, my, r, pnt)
    c.save()
    c.clipPath(p_circle(r, mx, my), skia.ClipOp.kIntersect, True)
    # swirls / land inside the glass
    sw = 1 - dark
    if sw > 0.02:
        for k in range(3):
            pts = [(mx + math.cos(t * 0.3 + k * 2.1 + j * 0.5) * r * (0.25 + 0.2 * j / 6),
                    my + math.sin(t * 0.3 + k * 2.1 + j * 0.5) * r * (0.25 + 0.2 * j / 6) * 0.8) for j in range(7)]
            c.drawPath(smooth_path(pts, False, 0.6), stroke(hexc("#ffffff", 0.55 * sw), r * 0.07))
        for (lx, ly, lr) in ((-0.3, 0.1, 0.22), (0.25, -0.2, 0.18), (0.2, 0.35, 0.12)):
            c.drawCircle(mx + lx * r, my + ly * r, lr * r, fill(hexc("#4fae6a", 0.55 * sw)))
    c.restore()
    # glass highlight
    hl = skia.Path()
    hl.addOval(skia.Rect.MakeLTRB(mx - r * 0.62, my - r * 0.72, mx - r * 0.05, my - r * 0.32))
    c.drawPath(hl, fill(hexc("#ffffff", 0.55 * (1 - dark * 0.7)), blur=r * 0.05))
    # photon ring once it is black
    if dark > 0.02:
        ring = p_circle(r * 1.06, mx, my)
        glow_path(c, ring, "#ffd9a8", 3.0, dark, glow_w=14, glow_a=0.6, shadow=False)
    glow_path(c, p_circle(r, mx, my), COOL, 3.0, 0.6 * (1 - dark), shadow=False)
    if t > t_b - 0.2 and dark < 0.5:
        label(c, "the blue marble", mx, my + r + 70 * u, 36 * u, "#bfe3ff", appear(t, t_b - 0.1) * (1 - dark * 2))
    if shr > 0.05:
        # little ruler under it: about 2 cm
        ry0 = my + r + 120 * u
        rl = p_ruler(220, 34)
        _icon(c, rl, mx, ry0, u * shr, WARM, 3.5, shr)
        label(c, "about 2 cm", mx, ry0 + 60 * u, 30 * u, WARM, shr * (1 - dark * 0.4))


def _mix(h1, h2, k):
    from gfx import mixhex
    return mixhex(h1, h2, clamp(k))


def sky_star_sizes(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_l = cue(cues, "light", 1.2)
    t_s = cue(cues, "sun", 3.3)
    t_h = cue(cues, "heavier", 6.8)
    t_g = cue(cues, "giant", 8.3)
    t_p = cue(cues, "pushes", 11.7)
    base = cy + 10 * u
    ex, sx = cx - 340 * u, cx - 110 * u
    # giant star first (behind), arc entering from the right, faded out at the rect bottom
    ga = appear(t, t_g - 0.2, 0.7)
    if ga > 0:
        gx, gy, gr = cx + 650 * u, base + 150 * u, 400 * u
        c.saveLayer(skia.Rect.MakeLTRB(rect[0] - 40, rect[1], 1080, rect[3] + 40), None)
        c.drawCircle(gx, gy, gr * 1.1, fill(hexc("#ff7a5a", 0.22 * ga), blur=gr * 0.1))
        pnt = skia.Paint(AntiAlias=True)
        pnt.setShader(skia.GradientShader.MakeRadial(skia.Point(gx - gr * 0.3, gy - gr * 0.2), gr * 1.2,
                                                     [hexc("#ffd2a8", ga), hexc("#ff8a5c", ga), hexc("#d9483b", ga)],
                                                     [0, 0.55, 1]))
        c.drawCircle(gx, gy, gr * (0.9 + 0.1 * ga), pnt)
        mask = skia.Paint()
        mask.setShader(skia.GradientShader.MakeLinear([skia.Point(0, rect[3] - 150 * u), skia.Point(0, rect[3])],
                                                      [hexc("#ffffff", 1.0), hexc("#ffffff", 0.0)]))
        mask.setBlendMode(skia.BlendMode.kDstIn)
        c.drawRect(skia.Rect.MakeLTRB(rect[0] - 40, rect[1], 1080, rect[3] + 40), mask)
        c.restore()
        lx = cx + 250 * u
        label(c, "giant star", lx, base - 150 * u, 32 * u, "#ffd2a8", ga)
        label(c, "20+ Suns: can collapse", lx, base - 112 * u, 24 * u, "#ffd2a8", appear(t, t_g + 0.6))
    # Earth
    ea = pop(t, t_l - 0.2)
    if ea > 0:
        glow_fill(c, p_circle(11 * u * ea, ex, base), "#5aa8ff", 1.0, 10, 0.6)
        label(c, "Earth", ex, base + 62 * u, 30 * u, COOL, min(1, ea))
        label(c, "too light", ex, base + 100 * u, 25 * u, PINK, appear(t, t_l + 0.4))
    # Sun
    sa = pop(t, t_s - 0.15, 0.5)
    if sa > 0:
        r = 112 * u * sa
        c.drawCircle(sx, base, r * 1.45, fill(hexc("#ffcf6b", 0.25), blur=r * 0.35))
        pnt = skia.Paint(AntiAlias=True)
        pnt.setShader(skia.GradientShader.MakeRadial(skia.Point(sx - r * 0.2, base - r * 0.2), r * 1.2,
                                                     [hexc("#fff4cf"), hexc("#ffc44d"), hexc("#ff9a2e")], [0, 0.6, 1]))
        c.drawCircle(sx, base, r, pnt)
        label(c, "Sun", sx, base + 160 * u, 32 * u, WARM, min(1, sa))
        label(c, "also too light", sx, base + 198 * u, 25 * u, PINK, appear(t, t_s + 1.2))
    if t > t_h - 0.2:
        label(c, "333,000 × Earth", sx, base - 150 * u, 32 * u, WARM, appear(t, t_h - 0.1))
    # push-back arrows around Earth and Sun
    pa = appear(t, t_p - 0.15, 0.4)
    if pa > 0:
        for (x, rr) in ((ex, 22 * u), (sx, 124 * u)):
            for k in range(8):
                ang = k * math.tau / 8 + 0.2
                wob = 1 + 0.08 * math.sin(t * 6 + k)
                x0 = x + math.cos(ang) * rr * wob
                y0 = base + math.sin(ang) * rr * wob
                x1 = x + math.cos(ang) * (rr + 34 * u) * wob
                y1 = base + math.sin(ang) * (rr + 34 * u) * wob
                glow_path(c, p_arrow(x0, y0, x1, y1, 11 * u), "#9dffc4", 3.5, pa)
        label(c, "everything pushes back", (ex + sx) / 2 + 20 * u, base + 262 * u, 32 * u, "#c8ffdd", pa)


def _atom_face(c, x, y, r, mood, alpha, t, arms=True, seed=0):
    """Round glowing atom with a grumpy-stubborn face and crossed arms."""
    glow_fill(c, p_circle(r, x, y), "#7fb8ff", 0.25 * alpha, r * 0.3, 0.3)
    glow_path(c, p_circle(r, x, y), COOL, 4.0, alpha)
    orb = skia.Path()
    orb.addOval(skia.Rect.MakeLTRB(x - r * 1.55, y - r * 0.45, x + r * 1.55, y + r * 0.45))
    rot_a = math.radians(-20 + seed * 35)
    m = skia.Matrix()
    m.setRotate(math.degrees(rot_a), x, y)
    orb.transform(m)
    glow_path(c, orb, BLUE, 2.5, 0.7 * alpha)
    ang = t * 2.2 + seed
    ox, oy = math.cos(ang) * r * 1.55, math.sin(ang) * r * 0.45
    ex2 = x + ox * math.cos(rot_a) - oy * math.sin(rot_a)
    ey2 = y + ox * math.sin(rot_a) + oy * math.cos(rot_a)
    c.drawCircle(ex2, ey2, r * 0.13, fill(hexc(BLUE, alpha)))
    # face: furrowed brows, eyes, small pout
    face = skia.Path()
    for s in (-1, 1):
        face.moveTo(x + s * r * 0.55, y - r * 0.42)
        face.lineTo(x + s * r * 0.12, y - r * 0.27)
    glow_path(c, face, WARM, 4.0, alpha)
    for s in (-1, 1):
        c.drawCircle(x + s * r * 0.32, y - r * 0.10, r * 0.10, fill(hexc(WARM, alpha)))
    mouth = skia.Path()
    mouth.moveTo(x - r * 0.16, y + r * 0.22)
    mouth.quadTo(x, y + r * 0.12, x + r * 0.16, y + r * 0.22)
    glow_path(c, mouth, WARM, 3.5, alpha)
    if arms:
        # crossed arms: two chunky bars over the lower body, with little fists
        aw = r * 0.24
        for s in (-1, 1):
            x0, y0 = x + s * r * 0.92, y + r * 0.38
            x1, y1 = x - s * r * 0.42, y + r * 0.66
            bar = skia.Path()
            bar.moveTo(x0, y0)
            bar.lineTo(x1, y1)
            c.drawPath(bar, stroke(hexc("#0a1430", 0.9 * alpha), aw + 7))
            c.drawPath(bar, stroke(hexc("#ffdcae", alpha), aw))
            c.drawCircle(x1 - s * r * 0.04, y1 - r * 0.02, aw * 0.62, fill(hexc("#fff0d8", alpha)))


def sky_stubborn(c, t, dur, cues, params, rect):
    cx, cy, u = _geom(rect)
    t_st = cue(cues, "stubborn", dur * 0.5)
    spots = [(-240, 30, 78, 0.15), (0, -20, 92, 0.45), (240, 30, 78, 0.75)]
    for i, (dx, dy, r, d0) in enumerate(spots):
        s = pop(t, d0, 0.4)
        if s <= 0:
            continue
        hmph = math.exp(-((t - t_st - 0.1 * i) / 0.18) ** 2) if t > t_st - 0.5 else 0.0
        _atom_face(c, cx + dx * u, cy + dy * u - hmph * 14 * u, r * u * s, 1.0, min(1.0, s), t, True, seed=i)
    if t > t_st:
        label(c, "hmph!", cx, cy - 170 * u, 40 * u, WARM, appear(t, t_st), "extrabold")


SKY = {
    "list": sky_list,
    "map": sky_map,
    "squeeze_earth": sky_squeeze_earth,
    "ruler_house_eye": sky_ruler_house_eye,
    "pool": sky_pool,
    "sun_arcs": sky_sun_arcs,
    "skater": sky_skater,
    "clock": sky_clock,
    "pizza": sky_pizza,
    "marble": sky_marble,
    "star_sizes": sky_star_sizes,
    "stubborn": sky_stubborn,
}
