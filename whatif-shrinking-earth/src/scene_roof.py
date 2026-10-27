"""Rooftop at night: sky, Moon, distant town, house roof, dormer window.

World coordinates match the 1080x1920 wide shot. A camera (cx, cy, zoom)
frames part of the world; background layers use parallax factors.
"""
import math

import numpy as np
import skia

from gfx import (Rng, clamp, ellipse_path, fill, hexc, linear_shader, mixhex, radial_shader,
                 smooth_path, stroke)

W, H = 1080, 1920
MOON = (760.0, 470.0, 165.0)

_rng = Rng(7)
STARS = []
for i in range(150):
    x, y = _rng.u(0, W * 1.6) - W * 0.3, _rng.u(-500, 1150)
    STARS.append((x, y, _rng.u(0.6, 2.1), _rng.u(0, 6.28), _rng.u(0.35, 1.0)))
BIG_STARS = [(130, 210), (330, 120), (980, 860), (60, 640), (520, 300), (900, 90), (250, 820), (1010, 330)]


class Cam:
    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, roll=0.0):
        self.cx, self.cy, self.zoom, self.roll = cx, cy, zoom, roll

    def apply(self, c, par=1.0):
        z = 1 + (self.zoom - 1) * par
        cx = W / 2 + (self.cx - W / 2) * par
        cy = H / 2 + (self.cy - H / 2) * par
        c.translate(W / 2, H / 2)
        if self.roll:
            c.rotate(math.degrees(self.roll) * par)
        c.scale(z, z)
        c.translate(-cx, -cy)

    def to_screen(self, x, y, par=1.0):
        z = 1 + (self.zoom - 1) * par
        cx = W / 2 + (self.cx - W / 2) * par
        cy = H / 2 + (self.cy - H / 2) * par
        return (x - cx) * z + W / 2, (y - cy) * z + H / 2


def lerp_cam(a, b, t):
    return Cam(a.cx + (b.cx - a.cx) * t, a.cy + (b.cy - a.cy) * t,
               math.exp(math.log(a.zoom) + (math.log(b.zoom) - math.log(a.zoom)) * t),
               a.roll + (b.roll - a.roll) * t)


def draw_sky(c, cam, t, night=1.0, moon_scale=1.0, moon_alpha=1.0, star_alpha=1.0, moon_screen=None):
    c.save()
    # sky gradient fixed to the screen (very far away)
    p = skia.Paint()
    p.setShader(linear_shader((0, 0), (0, H), [hexc("#070e27"), hexc("#0f1c47"), hexc("#1b2f66"), hexc("#2b4580")],
                              [0.0, 0.35, 0.68, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    c.restore()
    c.save()
    cam.apply(c, 0.12)
    # stars
    for (x, y, r, ph, b) in STARS:
        tw = 0.75 + 0.25 * math.sin(t * 1.3 + ph * 3) if r > 1.6 else 1.0
        c.drawCircle(x, y, r, fill(hexc("#eaf1ff", b * tw * star_alpha)))
    for (x, y) in BIG_STARS:
        tw = 0.7 + 0.3 * math.sin(t * 0.9 + x)
        a = 0.85 * tw * star_alpha
        c.drawCircle(x, y, 2.6, fill(hexc("#ffffff", a)))
        sp = stroke(hexc("#dfe9ff", 0.5 * a), 1.4)
        c.drawLine(x - 9, y, x + 9, y, sp)
        c.drawLine(x, y - 9, x, y + 9, sp)
    c.restore()
    if moon_screen is not None:
        draw_moon(c, moon_screen[0], moon_screen[1], moon_screen[2], moon_alpha)
        return
    c.save()
    cam.apply(c, 0.18)
    draw_moon(c, MOON[0], MOON[1], MOON[2] * moon_scale, moon_alpha)
    c.restore()


def draw_moon(c, x, y, r, alpha=1.0, glow=True, phase_rot=0.0):
    if alpha <= 0.01:
        return
    if glow:
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((x, y), r * 3.2, [hexc("#cfe0ff", 0.30 * alpha), hexc("#9fb8f0", 0.10 * alpha),
                                                    hexc("#7f9ce0", 0.0)], [0.25, 0.5, 1.0]))
        c.drawCircle(x, y, r * 3.2, g)
    p = skia.Paint(AntiAlias=True)
    p.setShader(radial_shader((x - r * 0.25, y - r * 0.25), r * 1.35,
                              [hexc("#fbf8ec", alpha), hexc("#ede6d2", alpha), hexc("#c9c2b0", alpha)], [0.0, 0.6, 1.0]))
    c.drawCircle(x, y, r, p)
    c.save()
    c.clipPath(ellipse_path(x, y, r, r), skia.ClipOp.kIntersect, True)
    c.translate(x, y)
    c.rotate(math.degrees(phase_rot))
    maria = [(-0.30, -0.25, 0.30, 0.22), (0.10, -0.38, 0.22, 0.16), (0.25, 0.05, 0.26, 0.20),
             (-0.15, 0.20, 0.20, 0.14), (0.42, -0.15, 0.12, 0.10), (-0.05, -0.05, 0.12, 0.09)]
    for (mx, my, rx, ry) in maria:
        c.drawOval(skia.Rect.MakeLTRB((mx - rx) * r, (my - ry) * r, (mx + rx) * r, (my + ry) * r),
                   fill(hexc("#bdb6a6", 0.55 * alpha), blur=r * 0.05))
    craters = [(0.15, 0.55, 0.07), (-0.55, 0.35, 0.05), (0.6, 0.35, 0.05), (-0.35, -0.65, 0.045),
               (0.35, -0.62, 0.04), (-0.68, -0.1, 0.035), (0.05, 0.75, 0.035), (0.7, -0.45, 0.03)]
    for (cx_, cy_, cr) in craters:
        c.drawCircle(cx_ * r, cy_ * r, cr * r, fill(hexc("#b3ab9a", 0.7 * alpha)))
        c.drawCircle(cx_ * r + cr * r * 0.25, cy_ * r + cr * r * 0.25, cr * r * 0.75, fill(hexc("#d9d2c0", 0.8 * alpha)))
    # ray crater
    c.drawCircle(0.15 * r, 0.55 * r, 0.025 * r, fill(hexc("#ffffff", 0.7 * alpha)))
    c.restore()


def hill_path(y0, amp, seed, x0=-400, x1=1480, n=14):
    r = Rng(seed)
    pts = [(x0, 2400)]
    xs = np.linspace(x0, x1, n)
    ys = y0 + r.u(-amp, amp, n)
    for x, y in zip(xs, ys):
        pts.append((x, y))
    pts.append((x1, 2400))
    return smooth_path(pts, True, 0.5)


_HILLS = [hill_path(1010, 35, 3), hill_path(1075, 40, 5), hill_path(1150, 30, 9)]
_lr = Rng(11)
TOWN = [(_lr.u(-300, 1400), _lr.u(1060, 1170), _lr.u(1.2, 2.6), _lr.u(0, 6)) for _ in range(90)]


def draw_town(c, cam, t):
    c.save()
    cam.apply(c, 0.3)
    c.drawPath(_HILLS[0], fill(hexc("#1c2c5a")))
    c.drawPath(_HILLS[1], fill(hexc("#16244b")))
    for (x, y, r, ph) in TOWN:
        a = 0.55 + 0.25 * math.sin(t * 0.7 + ph * 5) if ph > 5.4 else 0.7
        c.drawCircle(x, y, r, fill(hexc("#ffd28a", a)))
        c.drawCircle(x, y, r * 3, fill(hexc("#ffb85c", 0.07)))
    c.drawPath(_HILLS[2], fill(hexc("#101a3a")))
    c.restore()
    # near trees
    c.save()
    cam.apply(c, 0.55)
    for (tx, ty, s) in ((-20, 1180, 1.25), (110, 1215, 0.9), (1010, 1170, 1.15), (1120, 1205, 1.3)):
        draw_tree(c, tx, ty, s)
    c.restore()


def draw_tree(c, x, y, s):
    col = hexc("#0b1430")
    c.drawRect(skia.Rect.MakeLTRB(x - 6 * s, y - 40 * s, x + 6 * s, y + 200 * s), fill(col))
    for k, (dy, rr) in enumerate(((-140, 70), (-90, 85), (-40, 95), (10, 80))):
        c.drawCircle(x + (k % 2 * 2 - 1) * 14 * s, y + dy * s, rr * s, fill(col))
    c.drawCircle(x + 30 * s, y - 120 * s, 55 * s, fill(hexc("#1a2a55", 0.35)))


# --- house -------------------------------------------------------------------

RIDGE_Y0, RIDGE_Y1 = 1215.0, 1185.0  # ridge line y at x=-200 and x=1280


def roof_y(x):
    return RIDGE_Y0 + (RIDGE_Y1 - RIDGE_Y0) * (x + 200) / 1480.0


_ROOF_PIC = None


def _record_roof():
    rec = skia.PictureRecorder()
    c = rec.beginRecording(skia.Rect.MakeLTRB(-400, 900, 1500, 2700))
    # roof surface base
    roof = skia.Path()
    roof.moveTo(-300, roof_y(-300))
    roof.lineTo(1400, roof_y(1400))
    roof.lineTo(1400, 2600)
    roof.lineTo(-300, 2600)
    roof.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((0, 1190), (0, 2000), [hexc("#2f3d6b"), hexc("#222d55"), hexc("#18213f")], [0, 0.4, 1]))
    c.drawPath(roof, p)
    # shingle courses: horizontal rows with short staggered slots and a dark drip edge
    rows = []
    yy, k = 0.0, 0
    while yy < 1000:
        gap = 30 + k * 8.5
        rows.append((yy, gap, k))
        yy += gap
        k += 1
    rng = Rng(5)
    for (y_off, gap, k) in rows:
        shade = k / max(1, len(rows) - 1)
        y0a, y0b = roof_y(-340) + y_off, roof_y(1420) + y_off
        band = skia.Path()
        band.moveTo(-340, y0a)
        band.lineTo(1420, y0b)
        band.lineTo(1420, y0b + gap)
        band.lineTo(-340, y0a + gap)
        band.close()
        top = mixhex("#33436e", "#202a50", shade)
        bot = mixhex("#2a3862", "#1a2344", shade)
        bp = skia.Paint(AntiAlias=True)
        bp.setShader(linear_shader((0, y0a), (0, y0a + gap), [hexc(top), hexc(bot)]))
        c.drawPath(band, bp)
        # drip edge shadow at the bottom of each course + moonlit lip above it
        c.drawLine(-340, y0a + gap, 1420, y0b + gap, stroke(hexc("#121a36", 0.9), 2.5 + k * 0.45))
        c.drawLine(-340, y0a + gap - 3 - k * 0.3, 1420, y0b + gap - 3 - k * 0.3, stroke(hexc("#4a5b8f", 0.25), 1.5 + k * 0.2))
        tw = 62 + k * 15.0
        off = (k % 2) * tw * 0.5
        for x0 in np.arange(-340 + off, 1420, tw):
            yb = roof_y(x0) + y_off + gap
            ln = gap * (0.38 + 0.12 * rng.u())
            c.drawLine(x0, yb - ln, x0, yb, stroke(hexc("#141c3a", 0.75), 1.6 + k * 0.25))
    # moonlit ridge cap
    c.drawLine(-300, roof_y(-300) - 4, 1400, roof_y(1400) - 4, stroke(hexc("#6f80b8"), 9))
    c.drawLine(-300, roof_y(-300) + 3, 1400, roof_y(1400) + 3, stroke(hexc("#1a2346"), 5))
    # chimney (right)
    cx0, cx1 = 905, 1015
    ctop = 1010
    cb = roof_y(cx1) + 30
    ch = skia.Rect.MakeLTRB(cx0, ctop, cx1, cb)
    c.drawRect(ch, fill(hexc("#5b3b3f")))
    for row_i, y in enumerate(np.arange(ctop + 14, cb, 22)):
        c.drawLine(cx0, y, cx1, y, stroke(hexc("#3f272b"), 2))
        o2 = (row_i % 2) * 22
        for x in np.arange(cx0 + o2, cx1, 44):
            c.drawLine(x, y - 22, x, y, stroke(hexc("#3f272b"), 2))
    c.drawRect(skia.Rect.MakeLTRB(cx1 - 26, ctop, cx1, cb), fill(hexc("#000000", 0.25)))
    c.drawRect(skia.Rect.MakeLTRB(cx0 - 10, ctop - 18, cx1 + 10, ctop + 4), fill(hexc("#4a3034")))
    c.drawRect(skia.Rect.MakeLTRB(cx0 - 10, ctop - 18, cx1 + 10, ctop - 12), fill(hexc("#8f7f9e", 0.8)))
    return rec.finishRecordingAsPicture()


def draw_house(c, cam, t, window_glow=1.0, window_open=1.0):
    global _ROOF_PIC
    if _ROOF_PIC is None:
        _ROOF_PIC = _record_roof()
    c.save()
    cam.apply(c, 1.0)
    c.drawPicture(_ROOF_PIC)
    draw_dormer(c, t, window_glow, window_open)
    c.restore()


def draw_dormer(c, t, glow=1.0, open_=1.0):
    x0, x1 = 40, 330
    ytop = 1010
    yb = roof_y(x1) + 210
    # warm light spill on the roof
    if glow > 0:
        g = skia.Paint(AntiAlias=True)
        g.setShader(radial_shader((300, yb + 30), 520, [hexc("#ffb25e", 0.30 * glow), hexc("#ff9b45", 0.10 * glow),
                                                        hexc("#ff9b45", 0.0)], [0.0, 0.45, 1.0]))
        c.drawCircle(300, yb + 30, 520, g)
    wall = smooth_path([(x0, yb), (x0, ytop + 120), (x0 + (x1 - x0) / 2, ytop - 20), (x1, ytop + 120), (x1, yb)], True, 0.0)
    c.drawPath(wall, fill(hexc("#3d3a5c")))
    for y in np.arange(ytop + 140, yb, 18):
        c.drawLine(x0, y, x1, y, stroke(hexc("#34314f"), 2))
    # dormer roof
    rp = smooth_path([(x0 - 40, ytop + 140), (x0 + (x1 - x0) / 2, ytop - 50), (x1 + 40, ytop + 140),
                      (x1 + 40, ytop + 120), (x0 + (x1 - x0) / 2, ytop - 72), (x0 - 40, ytop + 120)], True, 0.0)
    c.drawPath(rp, fill(hexc("#1b2445")))
    c.drawLine(x0 + (x1 - x0) / 2, ytop - 70, x1 + 40, ytop + 122, stroke(hexc("#6f80b8"), 5))
    # window
    wx0, wx1, wy0, wy1 = x0 + 50, x1 - 50, ytop + 120, yb - 40
    lp = skia.Paint(AntiAlias=True)
    lp.setShader(linear_shader((0, wy0), (0, wy1), [hexc(mixhex("#3a2a3a", "#ffd08a", glow)),
                                                    hexc(mixhex("#2a1f30", "#ffab5c", glow))]))
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1), lp)
    # curtains
    for side in (-1, 1):
        xx = wx0 if side < 0 else wx1
        cp = smooth_path([(xx, wy0), (xx - side * 38, wy0), (xx - side * 30, (wy0 + wy1) / 2), (xx - side * 48, wy1),
                          (xx, wy1)], True, 0.3)
        c.drawPath(cp, fill(hexc(mixhex("#3b2e4a", "#e98f6f", glow * 0.8))))
    # open pane swung outward (left)
    po = open_
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1), stroke(hexc("#e8dcc0"), 9))
    c.drawLine((wx0 + wx1) / 2, wy0, (wx0 + wx1) / 2, wy1, stroke(hexc("#e8dcc0"), 6))
    if po > 0:
        pw = (wx1 - wx0) / 2 * (1 - 0.65 * po)
        pane = skia.Path()
        pane.moveTo(wx0, wy0)
        pane.lineTo(wx0 - pw * 0.3 * po, wy0 + 12 * po)
        pane.lineTo(wx0 - pw * 0.3 * po, wy1 + 12 * po)
        pane.lineTo(wx0, wy1)
        c.drawPath(pane, fill(hexc("#9fb0d8", 0.35)))
        c.drawPath(pane, stroke(hexc("#e8dcc0"), 6))
    # sill
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 16, wy1, wx1 + 16, wy1 + 14), fill(hexc("#e8dcc0")))
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 16, wy1 + 10, wx1 + 16, wy1 + 14), fill(hexc("#b9ab90")))
