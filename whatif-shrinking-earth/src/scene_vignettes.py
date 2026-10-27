"""Full-frame vignette scenes: fn(c, t, dur, cues, params) paints 1080x1920.

suitcase, pinch, vignette_scale, vignette_stack, vignette_pump,
vignette_elephants, vignette_atom, vignette_mountain, vignette_atoms, split_moon
"""
import math

import numpy as np
import skia

import rig
import scene_roof as sr
from chalk import (BLUE, COOL, PINK, WARM, appear, cue, glow_fill, glow_path, label, p_arrow, p_burst,
                   p_circle, pop, ramp, spotlight_bg, _capsule, _union)
from gfx import (clamp, ease_back, ease_in, ease_io, ease_out, fill, font, hexc, lerp, linear_shader, mixhex,
                 radial_shader, smooth_path, stroke, tapered_stroke)

W, H = 1080, 1920
OL = rig.OUTLINE


# ----------------------------------------------------------------------------
# shared helpers
# ----------------------------------------------------------------------------

def _ol_path(c, path, color, width=6.0, alpha=1.0):
    c.drawPath(path, stroke(hexc(OL, alpha), width))
    c.drawPath(path, fill(hexc(color, alpha)))


def _rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def _blink(t, times, dur=0.17):
    b = 0.0
    for tb in times:
        x = (t - tb) / dur
        if 0 <= x <= 1:
            b = max(b, 1 - abs(2 * x - 1))
    return min(1.0, b * 1.6)


def _spring(t, t0, a0, a1, freq=2.2, damp=3.2):
    """Value going from a0 to a1 at t0 with a damped overshoot."""
    if t <= t0:
        return a0
    x = t - t0
    return a1 + (a0 - a1) * math.exp(-damp * x) * math.cos(freq * math.tau * x)


def _soft_floor(c, y, color="#6f8fd8", alpha=0.18, rx=520, ry=70, cx=540):
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, y - ry, cx + rx, y + ry), fill(hexc(color, alpha), blur=40))


def _vignette_edges(c, strength=0.55):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(540, 860), 1250,
                                               [hexc("#000000", 0.0), hexc("#000000", 0.0), hexc("#000000", strength)],
                                               [0.0, 0.55, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def _sweat(c, x, y, s, alpha=1.0):
    p = skia.Path()
    p.moveTo(x, y - 14 * s)
    p.cubicTo(x + 9 * s, y - 2 * s, x + 9 * s, y + 9 * s, x, y + 9 * s)
    p.cubicTo(x - 9 * s, y + 9 * s, x - 9 * s, y - 2 * s, x, y - 14 * s)
    c.drawPath(p, stroke(hexc(OL, alpha), 4))
    c.drawPath(p, fill(hexc("#bfe6ff", alpha)))
    c.drawCircle(x - 2.5 * s, y + 1 * s, 2.2 * s, fill(hexc("#ffffff", alpha)))


# ============================================================================
# suitcase: warm hallway, packed suitcase by the front door, tag "7:00 BUS"
# ============================================================================

def scene_suitcase(c, t, dur, cues, params):
    t_tag = cue(cues, "tag", 1.0)
    push = 1.0 + 0.055 * ease_io(t / max(dur, 0.1))
    c.save()
    c.translate(470, 1000)
    c.scale(push, push)
    c.translate(-470, -1000)
    floor_y = 1260
    # wall
    c.drawRect(skia.Rect.MakeLTRB(-60, -60, W + 60, floor_y), fill(hexc("#3b2731")))
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((130, 430), 820, [hexc("#d39a66", 0.85), hexc("#8a5a4a", 0.35), hexc("#3b2731", 0.0)],
                              [0.0, 0.45, 1.0]))
    c.drawRect(skia.Rect.MakeLTRB(-60, -60, W + 60, floor_y), p)
    # wainscot
    c.drawRect(skia.Rect.MakeLTRB(-60, 905, W + 60, floor_y), fill(hexc("#2f1f27", 0.55)))
    c.drawRect(skia.Rect.MakeLTRB(-60, 892, W + 60, 912), fill(hexc("#7a5048")))
    for x in range(-40, W + 60, 150):
        c.drawRect(skia.Rect.MakeLTRB(x + 18, 950, x + 132, floor_y - 40), stroke(hexc("#24171e", 0.45), 3))
    # floor (planks in perspective)
    c.drawRect(skia.Rect.MakeLTRB(-60, floor_y, W + 60, H + 60), fill(hexc("#3a2620")))
    vx, vy = 540, -900
    for k in range(-8, 16):
        xb = 540 + k * 150
        c.drawLine(vx + (xb - vx) * (floor_y - vy) / (H + 60 - vy), floor_y, xb, H + 60, stroke(hexc("#2a1a16"), 3))
    c.drawRect(skia.Rect.MakeLTRB(-60, floor_y - 18, W + 60, floor_y + 4), fill(hexc("#5a3a32")))
    # warm pool of light + cool moonlight patch from the door's fanlight
    c.drawOval(skia.Rect.MakeLTRB(-120, floor_y + 40, 760, floor_y + 380), fill(hexc("#ffb36b", 0.20), blur=60))
    mp = skia.Path()
    mp.moveTo(640, floor_y + 60)
    mp.lineTo(860, floor_y + 60)
    mp.lineTo(980, floor_y + 330)
    mp.lineTo(700, floor_y + 330)
    mp.close()
    c.drawPath(mp, fill(hexc("#8fb0ff", 0.12), blur=18))
    # rug
    c.drawOval(skia.Rect.MakeLTRB(80, floor_y + 150, 880, floor_y + 420), fill(hexc("#6e2f36")))
    c.drawOval(skia.Rect.MakeLTRB(110, floor_y + 168, 850, floor_y + 402), stroke(hexc("#c98a5a", 0.7), 6))
    c.drawOval(skia.Rect.MakeLTRB(150, floor_y + 192, 810, floor_y + 378), stroke(hexc("#c98a5a", 0.35), 3))
    # door (right)
    dx0, dx1, dy0 = 640, 1000, 300
    c.drawRect(skia.Rect.MakeLTRB(dx0 - 26, dy0 - 110, dx1 + 26, floor_y), fill(hexc("#6b4538")))
    # fanlight window with the night
    fl = skia.Path()
    fl.addArc(skia.Rect.MakeLTRB(dx0, dy0 - 100, dx1, dy0 + 100), 180, 180)
    fl.close()
    c.drawPath(fl, fill(hexc("#16245a")))
    c.drawCircle(dx0 + 110, dy0 - 40, 3, fill(hexc("#ffffff", 0.9)))
    c.drawCircle(dx0 + 250, dy0 - 62, 2, fill(hexc("#ffffff", 0.7)))
    for k in range(1, 5):
        a = math.radians(180 + k * 36)
        c.drawLine((dx0 + dx1) / 2, dy0, (dx0 + dx1) / 2 + math.cos(a) * 180, dy0 + math.sin(a) * 100,
                   stroke(hexc("#6b4538"), 6))
    c.drawPath(fl, stroke(hexc("#6b4538"), 10))
    door = skia.Rect.MakeLTRB(dx0, dy0, dx1, floor_y)
    dp = skia.Paint(AntiAlias=True)
    dp.setShader(linear_shader((dx0, 0), (dx1, 0), [hexc("#6a3d27"), hexc("#4a2a1c")]))
    c.drawRect(door, dp)
    for (px0, py0, px1, py1) in ((dx0 + 40, dy0 + 50, dx0 + 160, dy0 + 420), (dx0 + 200, dy0 + 50, dx1 - 40, dy0 + 420),
                                 (dx0 + 40, dy0 + 480, dx0 + 160, floor_y - 60), (dx0 + 200, dy0 + 480, dx1 - 40, floor_y - 60)):
        c.drawRect(skia.Rect.MakeLTRB(px0, py0, px1, py1), fill(hexc("#3f2317")))
        c.drawRect(skia.Rect.MakeLTRB(px0, py0, px1, py1), stroke(hexc("#7a4a32", 0.6), 3))
    c.drawCircle(dx0 + 45, 820, 17, fill(hexc("#e7b75c")))
    c.drawCircle(dx0 + 40, 814, 6, fill(hexc("#fff2c8", 0.9)))
    c.drawRect(skia.Rect.MakeLTRB(dx0 + 36, 700, dx0 + 54, 730), fill(hexc("#c99a4a")))
    # sconce + lamp glow
    c.drawCircle(130, 430, 160, fill(hexc("#ffcf88", 0.25), blur=70))
    c.drawRect(skia.Rect.MakeLTRB(120, 430, 140, 500), fill(hexc("#5a3a30")))
    sh = skia.Path()
    sh.moveTo(80, 430)
    sh.lineTo(180, 430)
    sh.lineTo(155, 360)
    sh.lineTo(105, 360)
    sh.close()
    c.drawPath(sh, fill(hexc("#ffe2b0")))
    c.drawPath(sh, stroke(hexc("#c48a50"), 3))
    # kid drawing in a frame: two figures under a moon
    fx0, fy0 = 60, 600
    c.drawRect(skia.Rect.MakeLTRB(fx0, fy0, fx0 + 190, fy0 + 150), fill(hexc("#8a5a3a")))
    c.drawRect(skia.Rect.MakeLTRB(fx0 + 12, fy0 + 12, fx0 + 178, fy0 + 138), fill(hexc("#f4ead2")))
    c.drawCircle(fx0 + 140, fy0 + 45, 18, fill(hexc("#f2c94c")))
    for (sx_, hh, col) in ((fx0 + 60, 66, "#2e8c88"), (fx0 + 100, 48, "#f1b53e")):
        c.drawCircle(sx_, fy0 + 132 - hh, 9, stroke(hexc("#3a3a3a"), 3))
        c.drawLine(sx_, fy0 + 132 - hh + 9, sx_, fy0 + 118, stroke(hexc(col), 6))
        c.drawLine(sx_ - 9, fy0 + 132, sx_, fy0 + 118, stroke(hexc("#3a3a3a"), 3))
        c.drawLine(sx_ + 9, fy0 + 132, sx_, fy0 + 118, stroke(hexc("#3a3a3a"), 3))
    c.drawLine(fx0 + 68, fy0 + 92, fx0 + 92, fy0 + 98, stroke(hexc("#3a3a3a"), 3))
    # coat hook with Pip's yellow scarf
    c.drawRect(skia.Rect.MakeLTRB(230, 420, 380, 438), fill(hexc("#6b4538")))
    for hx in (255, 305, 355):
        c.drawCircle(hx, 450, 7, fill(hexc("#d9b26a")))
    sc = smooth_path([(307, 450), (285, 510), (295, 610), (275, 710), (315, 720), (327, 610), (321, 510)], True, 0.4)
    _ol_path(c, sc, "#f1b53e", 5)
    for yy in (650, 678, 702):
        c.drawLine(282, yy, 319, yy + 4, stroke(hexc("#c8862a"), 4))
    cap = smooth_path([(338, 452), (372, 448), (392, 480), (380, 520), (350, 528), (328, 500)], True, 0.5)
    _ol_path(c, cap, "#2d3c6c", 5)
    # sneakers
    for k, sx_ in enumerate((110, 215)):
        sn = smooth_path([(sx_ - 55, floor_y + 40), (sx_ - 50, floor_y - 12), (sx_ + 10, floor_y - 18),
                          (sx_ + 55, floor_y + 6), (sx_ + 60, floor_y + 40)], True, 0.35)
        _ol_path(c, sn, "#eef1f4", 5)
        c.drawLine(sx_ - 40, floor_y + 32, sx_ + 55, floor_y + 32, stroke(hexc("#2e8c88"), 7))
        c.drawLine(sx_ - 20, floor_y - 6, sx_ + 20, floor_y + 2, stroke(hexc("#9aa3ad"), 3))
    # suitcase
    _suitcase(c, 500, floor_y + 22, t, t_tag)
    c.restore()
    _vignette_edges(c, 0.6)


def _suitcase(c, cx, base_y, t, t_tag):
    w, h = 320, 470
    x0, x1 = cx - w / 2, cx + w / 2
    y1 = base_y - 28
    y0 = y1 - h
    # shadow
    c.drawOval(skia.Rect.MakeLTRB(x0 - 30, base_y - 22, x1 + 50, base_y + 20), fill(hexc("#000000", 0.45), blur=12))
    # telescoping handle
    for hx in (cx - 60, cx + 60):
        c.drawRect(skia.Rect.MakeLTRB(hx - 9, y0 - 180, hx + 9, y0 + 4), fill(hexc("#9aa3ad")))
        c.drawRect(skia.Rect.MakeLTRB(hx - 9, y0 - 180, hx + 9, y0 + 4), stroke(hexc(OL), 4))
    hb = _rrect(cx - 82, y0 - 210, cx + 82, y0 - 172, 16)
    _ol_path(c, hb, "#3a3f4a", 5)
    body = _rrect(x0, y0, x1, y1, 34)
    c.drawPath(body, stroke(hexc(OL), 7))
    bp = skia.Paint(AntiAlias=True)
    bp.setShader(linear_shader((x0, 0), (x1, 0), [hexc("#3aa39e"), hexc("#2e8c88"), hexc("#1f6663")], [0, 0.55, 1]))
    c.drawPath(body, bp)
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    for k in range(1, 6):
        xx = x0 + k * w / 6
        c.drawLine(xx, y0 + 18, xx, y1 - 18, stroke(hexc("#1f6663", 0.75), 7))
        c.drawLine(xx + 5, y0 + 18, xx + 5, y1 - 18, stroke(hexc("#5cc0b8", 0.45), 3))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0 + h * 0.48, x1, y0 + h * 0.52), fill(hexc("#1b5654")))
    # warm lamp rim on the left side
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + 16, y1), fill(hexc("#ffb36b", 0.35)))
    c.restore()
    # corner guards + wheels
    for (gx, gy) in ((x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x0 + 6, y1 - 6), (x1 - 6, y1 - 6)):
        c.drawCircle(gx, gy, 20, fill(hexc("#2b2f38")))
    for wx in (x0 + 45, x1 - 45):
        c.drawCircle(wx, base_y - 14, 17, fill(hexc("#1c1f26")))
        c.drawCircle(wx, base_y - 14, 6, fill(hexc("#6b7280")))
    # top carry handle
    th = skia.Path()
    th.moveTo(cx - 50, y0 + 2)
    th.cubicTo(cx - 50, y0 - 40, cx + 50, y0 - 40, cx + 50, y0 + 2)
    c.drawPath(th, stroke(hexc(OL), 16))
    c.drawPath(th, stroke(hexc("#2b2f38"), 10))
    # stickers: star + atom
    from rig import draw_star
    c.drawCircle(x0 + 75, y0 + 330, 30, fill(hexc("#f2c94c")))
    draw_star(c, x0 + 75, y0 + 330, 20, hexc("#fff6dc"))
    c.save()
    c.translate(x1 - 80, y0 + 120)
    c.drawCircle(0, 0, 34, fill(hexc("#f4efe6")))
    for k in range(3):
        c.save()
        c.rotate(k * 60 + 15)
        c.drawOval(skia.Rect.MakeLTRB(-25, -9, 25, 9), stroke(hexc("#2e8c88"), 3))
        c.restore()
    c.drawCircle(0, 0, 4.5, fill(hexc("#2e8c88")))
    c.restore()
    # luggage tag on a loop from the carry handle; flips into view at t_tag
    lx, ly = cx + 46, y0 - 18
    sway = math.sin(t * 2.3) * 0.06
    flip = ease_back(clamp((t - t_tag + 0.05) / 0.45), 1.3) if t > t_tag - 0.05 else 0.0
    sx = lerp(0.12, 1.0, flip)
    c.save()
    c.translate(lx, ly)
    c.rotate(math.degrees(0.22 + sway - 0.18 * flip))
    c.drawLine(0, 0, 0, 70, stroke(hexc("#e9e2cf"), 4))
    c.translate(0, 70)
    c.scale(sx, 1.0)
    tag = skia.Path()
    tag.moveTo(-58, 18)
    tag.lineTo(-40, 0)
    tag.lineTo(40, 0)
    tag.lineTo(58, 18)
    tag.lineTo(58, 120)
    tag.lineTo(-58, 120)
    tag.close()
    _ol_path(c, tag, "#f3e6c8", 5)
    c.drawCircle(0, 14, 7, fill(hexc("#7a5a3a")))
    if flip > 0.35:
        a = clamp((flip - 0.35) / 0.4)
        f1 = font(38, "black")
        f2 = font(30, "extrabold")
        s1, s2 = "7:00", "BUS"
        c.drawString(s1, -f1.measureText(s1) / 2, 66, f1, fill(hexc("#c0392b", a)))
        c.drawString(s2, -f2.measureText(s2) / 2, 104, f2, fill(hexc("#3a2a20", a)))
    c.restore()


# ============================================================================
# pinch: over Pip's shoulder, her hand pinches the Moon
# ============================================================================

MOON_P = (560.0, 560.0, 100.0)


def _pinch_hand_path(gap_open):
    """Back of a right hand pinching; fingertips frame MOON_P vertically.

    gap_open: 0 = fingertips touching the Moon's top/bottom, 1 = wide apart.
    """
    mx, my, mr = MOON_P
    ix, iy = mx + 22, my - mr - 12 - 70 * gap_open      # index tip
    tx, ty = mx + 22, my + mr + 12 + 70 * gap_open      # thumb tip
    kx, ky = mx + 230, my - 30                            # index knuckle
    parts = []
    # index finger: two segments
    mid = (lerp(ix, kx, 0.48) + 22, lerp(iy, ky, 0.48) - 28 - 10 * gap_open)
    parts.append(_capsule(kx, ky, mid[0], mid[1], 58))
    parts.append(_capsule(mid[0], mid[1], ix + 18, iy + 4, 50))
    # thumb
    tb = (mx + 255, my + 120)
    tm = (lerp(tx, tb[0], 0.5) + 10, lerp(ty, tb[1], 0.5) + 30 + 10 * gap_open)
    parts.append(_capsule(tb[0], tb[1], tm[0], tm[1], 66))
    parts.append(_capsule(tm[0], tm[1], tx + 20, ty - 2, 56))
    # hand back
    hb = smooth_path([(kx - 30, ky - 40), (kx + 110, ky - 70), (kx + 210, ky + 10), (kx + 230, ky + 170),
                      (kx + 120, ky + 240), (kx + 10, ky + 200), (kx - 40, ky + 90)], True, 0.5)
    parts.append(hb)
    # curled fingers (knuckles) under the index
    for k, (ox, oy) in enumerate(((-30, 60), (-22, 118), (-6, 168))):
        q = skia.Path()
        q.addCircle(kx + ox, ky + oy, 40 - k * 3)
        parts.append(q)
    # wrist + forearm
    parts.append(_capsule(kx + 150, ky + 150, kx + 420, ky + 640, 190))
    return _union(parts), (ix, iy), (tx, ty), (kx, ky)


def scene_pinch(c, t, dur, cues, params):
    t_raise = cue(cues, "raise_", 0.2)
    t_pinch = cue(cues, "pinch", 0.8)
    again = bool(params.get("again", False))
    mx, my, mr = MOON_P
    sr.draw_sky(c, sr.Cam(), t, moon_alpha=0.0)
    sr.draw_moon(c, mx, my, mr)
    sr.draw_town(c, sr.Cam(540, -200, 1.0), t)
    # Pip from behind, 3/4: hair, one bun with a pink scrunchie, ear, yellow hoodie shoulders
    hair = hexc("#4a241c")
    sh_p = smooth_path([(-120, 1920), (-100, 1820), (60, 1760), (330, 1770), (560, 1850), (640, 1920)], True, 0.5)
    _ol_path(c, sh_p, "#e2a536", 8)
    hood = smooth_path([(-40, 1920), (-10, 1840), (150, 1805), (330, 1830), (420, 1920)], True, 0.5)
    _ol_path(c, hood, "#c8862a", 6)
    hx, hy, hr = 120, 1600, 285
    head = smooth_path([(hx - hr, hy + 40), (hx - hr * 0.92, hy - hr * 0.55), (hx - hr * 0.35, hy - hr * 0.98),
                        (hx + hr * 0.35, hy - hr * 0.97), (hx + hr * 0.88, hy - hr * 0.55), (hx + hr * 1.0, hy + 10),
                        (hx + hr * 0.82, hy + hr * 0.62), (hx + hr * 0.3, hy + hr * 0.92), (hx - hr * 0.5, hy + hr * 0.85)],
                       True, 0.55)
    ear = skia.Path()
    ear.addOval(skia.Rect.MakeLTRB(hx + hr * 0.86, hy - 40, hx + hr * 1.08, hy + 60))
    _ol_path(c, ear, "#9c6249", 6)
    bx, by, br = hx + 175, hy - 300, 98
    bun = p_circle(br, bx, by)
    _ol_path(c, bun, "#4a241c", 7)
    c.save()
    c.clipPath(bun, skia.ClipOp.kIntersect, True)
    c.drawCircle(bx + 30, by - 50, 70, fill(hexc(rig.MOON_RIM, 0.30), blur=18))
    for k in range(3):
        arc = skia.Path()
        rr = br * (0.8 - k * 0.22)
        arc.addArc(skia.Rect.MakeLTRB(bx - rr, by - rr, bx + rr, by + rr), 200 + k * 40, 150)
        c.drawPath(arc, stroke(hexc("#6b3a2c", 0.75), 5))
    c.restore()
    c.drawPath(head, stroke(hexc(OL), 8))
    c.drawPath(head, fill(hair))
    c.save()
    c.clipPath(head, skia.ClipOp.kIntersect, True)
    rim = skia.Path(head)
    rim.offset(-12, 24)
    c.save()
    c.clipPath(rim, skia.ClipOp.kDifference, True)
    c.drawRect(skia.Rect.MakeLTRB(-300, 1200, 700, 2100), fill(hexc(rig.MOON_RIM, 0.55)))
    c.restore()
    for k in range(7):
        sx0 = hx - 220 + k * 62
        strand = smooth_path([(sx0, hy + 240), (sx0 + 40, hy + 40), (lerp(sx0, bx, 0.6), hy - 160), (bx - 30 + k * 8, by + 80)],
                             False, 0.5)
        c.drawPath(strand, stroke(hexc("#6b3a2c", 0.55), 5))
    c.restore()
    scr = skia.Path()
    scr.addOval(skia.Rect.MakeLTRB(bx - 78, by + 52, bx + 70, by + 104))
    _ol_path(c, scr, "#f07aa0", 6)
    for k in range(5):
        c.drawCircle(bx - 55 + k * 28, by + 78, 6, fill(hexc("#ffb3c7", 0.9)))
    for (wx, wy, d) in ((hx - 60, hy - 270, -1), (hx + 250, hy - 120, 1)):
        wp = smooth_path([(wx, wy), (wx + d * 25, wy - 40), (wx + d * 10, wy - 75)], False, 0.6)
        c.drawPath(wp, stroke(hexc(OL), 7))
        c.drawPath(wp, stroke(hexc("#5b2c22"), 4))
    # the hand
    rise = ease_out(clamp((t - t_raise) / 0.55))
    if rise > 0:
        if t < t_pinch - 0.1:
            g = 1.0
        else:
            g = max(-0.06, 1 - ease_back(clamp((t - t_pinch + 0.1) / 0.4), 1.6))
            g = max(g, 0.0) if g > 0 else g * 0.5
        hp, (ix, iy), (tx, ty), (kx, ky) = _pinch_hand_path(max(0.0, g))
        c.save()
        c.translate((1 - rise) * 140, (1 - rise) * 1100)
        c.rotate((1 - rise) * 12)
        # sleeve
        sl = _capsule(kx + 300, ky + 470, kx + 760, ky + 1300, 300)
        _ol_path(c, sl, "#c8862a", 8)
        c.save()
        c.clipPath(sl, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, 1080, 1920), fill(hexc("#f1b53e", 0.0)))
        rim2 = skia.Path(sl)
        rim2.offset(18, 10)
        c.save()
        c.clipPath(rim2, skia.ClipOp.kDifference, True)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, 1400, 2400), fill(hexc("#ffd77a", 0.85)))
        c.restore()
        c.restore()
        cuff = _capsule(kx + 285, ky + 450, kx + 345, ky + 560, 250)
        _ol_path(c, cuff, "#b67a24", 6)
        # hand: dark against the moonlight with a bright rim on the moon-facing edges
        c.drawPath(hp, stroke(hexc(OL), 9))
        c.drawPath(hp, fill(hexc("#6e4130")))
        c.save()
        c.clipPath(hp, skia.ClipOp.kIntersect, True)
        rp = skia.Path(hp)
        rp.offset(16, 9)
        c.save()
        c.clipPath(rp, skia.ClipOp.kDifference, True)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, 1400, 2400), fill(hexc("#ffe2c8", 0.9)))
        c.restore()
        c.drawCircle(kx + 120, ky + 130, 120, fill(hexc("#8c5640", 0.6), blur=40))
        # knuckle creases
        for (ox, oy) in ((-30, 60), (-22, 118)):
            c.drawLine(kx + ox + 20, ky + oy + 30, kx + ox + 52, ky + oy + 22, stroke(hexc("#4a281c", 0.7), 4))
        c.drawPath(smooth_path([(ix + 40, iy + 30), (ix + 60, iy + 50)], False), stroke(hexc("#4a281c", 0.6), 4))
        c.restore()
        c.restore()
        # glints at the fingertips when the pinch lands
        gl = math.exp(-((t - t_pinch - 0.25) / 0.25) ** 2) if t > t_pinch else 0.0
        if gl > 0.02:
            for (gx, gy) in ((mx + 22, my - mr - 8), (mx + 22, my + mr + 8)):
                _glint(c, gx, gy, 26 * gl, gl)
        if again and t > t_pinch:
            a = appear(t, t_pinch + 0.15, 0.4)
            ring = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                              Color=hexc(WARM, 0.85 * a))
            ring.setPathEffect(skia.DashPathEffect.Make([14.0, 10.0], t * 30))
            c.drawCircle(mx, my, mr + 26, ring)
            label(c, "exactly the same size", mx - 20, my - mr - 70, 40, WARM, a)


def _glint(c, x, y, r, a):
    p = skia.Path()
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.18
        ang = k * math.pi / 4
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        if k == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    c.drawPath(p, fill(hexc("#ffffff", 0.35 * a), blur=6))
    c.drawPath(p, fill(hexc("#ffffff", a)))


# ============================================================================
# vignette_scale: bathroom scale blamed unfairly
# ============================================================================

def scene_scale(c, t, dur, cues, params):
    t_step = cue(cues, "step", 1.5)
    t_blame = cue(cues, "blamed", 2.9)
    t_fault = cue(cues, "fault", 4.5)
    horizon = 700
    wp = skia.Paint(AntiAlias=True)
    wp.setShader(linear_shader((0, 0), (0, horizon), [hexc("#d9eee8"), hexc("#bcd9d1")]))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, horizon), wp)
    for x in range(-60, W + 1, 140):
        c.drawLine(x, 0, x, horizon, stroke(hexc("#9fc2b9"), 3))
    for y in range(0, horizon + 1, 140):
        c.drawLine(0, y, W, y, stroke(hexc("#9fc2b9"), 3))
    c.drawRect(skia.Rect.MakeLTRB(0, horizon - 22, W, horizon + 14), fill(hexc("#efe9dc")))
    c.drawLine(0, horizon + 14, W, horizon + 14, stroke(hexc("#c9c0ad"), 3))
    vx, vy = 540, -1500
    fy0 = horizon + 14
    c.drawRect(skia.Rect.MakeLTRB(0, fy0, W, H), fill(hexc("#efe7da")))
    ys = [fy0]
    hgt = 80
    while ys[-1] < H + 200:
        ys.append(ys[-1] + hgt)
        hgt *= 1.16

    def X(xx, yy):
        return vx + (540 + xx - vx) * (yy - vy) / (H - vy)

    for r_ in range(len(ys) - 1):
        ya, yb = ys[r_], ys[r_ + 1]
        for k in range(-14, 16):
            if (k + r_) % 2:
                continue
            q = skia.Path()
            q.moveTo(X(k * 180, ya), ya)
            q.lineTo(X((k + 1) * 180, ya), ya)
            q.lineTo(X((k + 1) * 180, yb), yb)
            q.lineTo(X(k * 180, yb), yb)
            q.close()
            c.drawPath(q, fill(hexc("#d6cbb8")))
    lp = skia.Path()
    lp.moveTo(0, 200)
    lp.lineTo(260, 200)
    lp.lineTo(560, 1600)
    lp.lineTo(0, 1600)
    lp.close()
    c.drawPath(lp, fill(hexc("#fff8e6", 0.16), blur=30))
    land = clamp((t - (t_step - 0.42)) / 0.42)
    foot_dy = -900 * (1 - ease_in(land)) if land < 1 else 0.0
    squash = 0.0
    if t > t_step:
        squash = 0.03 * math.exp(-(t - t_step) * 6) * math.cos((t - t_step) * 22)
    shiver = 0.0
    if t > t_fault:
        shiver = math.sin(t * 55) * 2.4 * min(1.0, (t - t_fault) * 3)
    v = 0.0
    if t > t_step:
        v = _spring(t, t_step, 0.0, 40.0, 1.6, 3.0)
    if t > t_blame:
        v = _spring(t, t_blame, 40.0, 49.0, 1.4, 2.6)
    cx, cy = 540 + shiver, 1040
    c.save()
    c.translate(cx, cy + 220)
    c.scale(1.0, 1.0 - squash)
    c.translate(-cx, -(cy + 220))
    _bath_scale(c, cx, cy, v, t, t_fault)
    c.restore()
    if land > 0:
        for (fx, side) in ((295, -1), (785, 1)):
            _sock_foot(c, fx + shiver * 0.5, 905 + foot_dy - squash * 400, side, t)
    q = pop(t, t_blame + 0.25, 0.35)
    if q > 0:
        bx, by = 830, 330
        bub = smooth_path([(bx - 130, by - 70), (bx + 130, by - 80), (bx + 140, by + 60), (bx + 20, by + 72),
                           (bx - 30, by + 130), (bx - 34, by + 68), (bx - 135, by + 56)], True, 0.35)
        c.save()
        c.translate(bx, by)
        c.scale(q, q)
        c.translate(-bx, -by)
        _ol_path(c, bub, "#ffffff", 6)
        f = font(100, "black")
        c.drawString("?!", bx - f.measureText("?!") / 2, by + 36, f, fill(hexc("#e04848")))
        c.restore()
    if t > t_blame + 0.2:
        a = appear(t, t_blame + 0.2, 0.3) * (1 - ramp(t, t_blame + 2.0, 0.5))
        _pill(c, 850, 1390, "+23%", "#e04848", a, 56)


def _pill(c, x, y, txt, col, a, size=46):
    if a <= 0.01:
        return
    f = font(size, "black")
    w = f.measureText(txt)
    r = _rrect(x - w / 2 - 22, y - size * 0.95, x + w / 2 + 22, y + size * 0.35, size * 0.6)
    c.drawPath(r, stroke(hexc(OL, a), 6))
    c.drawPath(r, fill(hexc("#ffffff", a)))
    c.drawString(txt, x - w / 2, y, f, fill(hexc(col, a)))


def _bath_scale(c, cx, cy, v, t, t_fault):
    c.drawOval(skia.Rect.MakeLTRB(cx - 470, cy + 200, cx + 480, cy + 300), fill(hexc("#5a5145", 0.35), blur=20))
    top = smooth_path([(cx - 360, cy - 200), (cx + 360, cy - 200), (cx + 450, cy + 120), (cx + 450, cy + 150),
                       (cx - 450, cy + 150), (cx - 450, cy + 120)], True, 0.18)
    front = _rrect(cx - 455, cy + 90, cx + 455, cy + 255, 60)
    _ol_path(c, front, "#d4cdbf", 8)
    _ol_path(c, top, "#f6f2ea", 8)
    c.save()
    c.clipPath(top, skia.ClipOp.kIntersect, True)
    for k in range(-9, 10):
        x0 = cx + k * 52
        c.drawLine(x0 * 0.98 + cx * 0.02, cy - 200, x0 * 1.22 - cx * 0.22, cy + 150, stroke(hexc("#e6dfd2"), 6))
    c.restore()
    dcx, dcy = cx, cy + 60
    win = _rrect(dcx - 215, dcy - 82, dcx + 215, dcy + 72, 50)
    _ol_path(c, win, "#c5bcac", 7)
    face = _rrect(dcx - 198, dcy - 68, dcx + 198, dcy + 58, 38)
    c.drawPath(face, fill(hexc("#fffdf6")))
    c.save()
    c.clipPath(face, skia.ClipOp.kIntersect, True)
    piv = (dcx, dcy + 420)
    R = 460
    f = font(34, "bold")
    for val in range(0, 121, 2):
        ang = math.radians(-90 + (val - v) * 0.85)
        x0 = piv[0] + math.cos(ang) * R
        y0 = piv[1] + math.sin(ang) * R
        L = 32 if val % 10 == 0 else 16
        x1 = piv[0] + math.cos(ang) * (R - L)
        y1 = piv[1] + math.sin(ang) * (R - L)
        col = "#2e9e5b" if val == 40 else "#3a3a3a"
        c.drawLine(x0, y0, x1, y1, stroke(hexc(col), 5 if val % 10 == 0 else 3))
        if val % 10 == 0:
            st = str(val)
            xt = piv[0] + math.cos(ang) * (R - 62)
            yt = piv[1] + math.sin(ang) * (R - 62)
            c.drawString(st, xt - f.measureText(st) / 2, yt + 12, f, fill(hexc(col)))
    c.restore()
    c.drawLine(dcx, dcy - 68, dcx, dcy + 14, stroke(hexc("#e04848"), 7))
    c.drawCircle(dcx, dcy - 68, 8, fill(hexc("#e04848")))
    c.drawPath(win, stroke(hexc(OL), 7))
    lab = font(24, "bold")
    c.drawString("kg", dcx + 150, dcy + 48, lab, fill(hexc("#8a8275")))
    fa = appear(t, t_fault - 0.1, 0.35)
    if fa > 0:
        ey = cy + 175
        for s_ in (-1, 1):
            ex = cx + s_ * 95
            c.drawCircle(ex, ey, 26 * fa, fill(hexc("#ffffff")))
            c.drawCircle(ex, ey, 26 * fa, stroke(hexc(OL), 5))
            c.drawCircle(ex + 3, ey - 9 * fa, 11 * fa, fill(hexc(OL)))
            c.drawCircle(ex + 6, ey - 13 * fa, 3.5 * fa, fill(hexc("#ffffff")))
            c.drawLine(ex - s_ * 38, ey - 48, ex + s_ * 10, ey - 36 - 12 * fa, stroke(hexc(OL), 6))
        mo = smooth_path([(cx - 44, ey + 50), (cx - 22, ey + 40), (cx, ey + 50), (cx + 22, ey + 40), (cx + 44, ey + 50)],
                         False, 0.5)
        c.drawPath(mo, stroke(hexc(OL, fa), 6))
        sd = clamp((t - t_fault - 0.2) / 1.0)
        _sweat(c, cx + 330, cy + 120 + sd * 70, 2.4 * fa, fa)


def _sock_foot(c, x, y, side, t):
    leg = _rrect(x - 78, y - 1300, x + 78, y - 20, 44)
    _ol_path(c, leg, "#2d3c6c", 7)
    c.drawRect(skia.Rect.MakeLTRB(x - 78, y - 70, x + 78, y - 26), fill(hexc("#24315a")))
    for k in range(4):
        rig.draw_star(c, x - 30 + k * 22, y - 260 - k * 150, 9, hexc("#f2c94c", 0.8))
    pts = [(x - 62, y - 40), (x - 84, y + 30), (x - 80, y + 92), (x - 52, y + 128), (x, y + 140),
           (x + 52, y + 128), (x + 80, y + 92), (x + 84, y + 30), (x + 62, y - 40)]
    base = smooth_path(pts, True, 0.5)
    c.drawPath(base, stroke(hexc("#f8a8bf", 0.9), 16))
    _ol_path(c, base, "#f08aa6", 6)
    c.save()
    c.clipPath(base, skia.ClipOp.kIntersect, True)
    c.drawOval(skia.Rect.MakeLTRB(x - 120, y - 100, x + 30, y + 90), fill(hexc("#ffb3c7", 0.65), blur=22))
    c.drawLine(x - 90, y + 8, x + 90, y + 8, stroke(hexc("#d76d8c", 0.6), 4))
    c.restore()
    for k in range(5):
        tx = x - 52 + k * 26
        ty = y + 128 - abs(k - 2) * 9
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeLTRB(tx - 14, ty - 18, tx + 14, ty + 10), 20, 140)
        c.drawPath(arc, stroke(hexc("#c76683", 0.8), 4))


import vig_atoms  # noqa: E402
import vig_cartoon  # noqa: E402
import vig_split  # noqa: E402

SCENES = {
    "suitcase": scene_suitcase,
    "pinch": scene_pinch,
    "vignette_scale": scene_scale,
    "vignette_stack": vig_cartoon.scene_stack,
    "vignette_pump": vig_cartoon.scene_pump,
    "vignette_elephants": vig_cartoon.scene_elephants,
    "vignette_mountain": vig_cartoon.scene_mountain,
    "vignette_atom": vig_atoms.scene_atom,
    "vignette_atoms": vig_atoms.scene_atoms,
    "split_moon": vig_split.scene_split,
}
