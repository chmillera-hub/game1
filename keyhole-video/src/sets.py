"""Backgrounds / sets. World space is 1080 x 1920 (porch extends upward into the sky)."""
import math
import numpy as np
import skia
from gfx import (fill, stroke, shade, alpha, mixc, hexc, ellipse, path_poly, smooth_closed, smooth_open, rrect,
                 lin_grad, rad_grad, font, text_width, clamp, smooth, wobble)

_PICS = {}


def picture(key, fn, w=1080, h=1920, y0=0):
    if key not in _PICS:
        rec = skia.PictureRecorder()
        c = rec.beginRecording(skia.Rect.MakeLTRB(-400, y0 - 400, w + 400, h + 400))
        fn(c)
        _PICS[key] = rec.finishRecordingAsPicture()
    return _PICS[key]


def glow(cv, x, y, r, col, a=0.6):
    cv.drawCircle(x, y, r, rad_grad((x, y), r, [alpha(col, a), alpha(col, a * 0.35), alpha(col, 0.0)], [0.0, 0.4, 1.0]))


# =================================================================== CLASSROOM (students view)
def _class_back(c):
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, 1480, 1360), lin_grad((0, 0), (0, 1360), ["#f6e9cf", "#efdcb8"]))
    for k in range(-6, 30):
        c.drawRect(skia.Rect.MakeLTRB(k * 60, -400, k * 60 + 28, 1060), fill(alpha("#e3c995", 0.18)))
    # wainscot
    c.drawRect(skia.Rect.MakeLTRB(-400, 1040, 1480, 1360), fill("#d6b083"))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1030, 1480, 1052), fill("#b98a5a"))
    for k in range(-3, 14):
        c.drawRect(skia.Rect.MakeLTRB(k * 120 + 15, 1085, k * 120 + 105, 1320), stroke(alpha("#a87a4c", 0.6), 4))
    # window
    wx0, wy0, wx1, wy1 = 60, 230, 470, 760
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 22, wy0 - 22, wx1 + 22, wy1 + 22), fill("#fbf5ea"))
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 22, wy0 - 22, wx1 + 22, wy1 + 22), stroke("#b89a78", 4))
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1), lin_grad((0, wy0), (0, wy1), ["#7cc3ee", "#c6ebff"]))
    for (x, y, r) in [(120, 640, 120), (230, 600, 110), (330, 660, 120), (420, 610, 90)]:
        c.drawCircle(x, y, r, fill("#6fb36a"))
        c.drawCircle(x - 20, y - 30, r * 0.6, fill(alpha("#8fd18a", 0.6)))
    c.drawRect(skia.Rect.MakeLTRB(wx0, 700, wx1, wy1), fill("#78b866"))
    for (x, y) in [(140, 330), (330, 290)]:
        for k in range(4):
            c.drawCircle(x + k * 28, y + (k % 2) * 6, 26, fill((1, 1, 1, 0.9)))
    c.drawRect(skia.Rect.MakeLTRB((wx0 + wx1) / 2 - 8, wy0, (wx0 + wx1) / 2 + 8, wy1), fill("#fbf5ea"))
    c.drawRect(skia.Rect.MakeLTRB(wx0, (wy0 + wy1) / 2 - 8, wx1, (wy0 + wy1) / 2 + 8), fill("#fbf5ea"))
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 40, wy1 + 18, wx1 + 40, wy1 + 44), fill("#e9dcc6"))
    # bulletin board
    bx0, by0, bx1, by1 = 600, 300, 1010, 700
    c.drawRect(skia.Rect.MakeLTRB(bx0 - 16, by0 - 16, bx1 + 16, by1 + 16), fill("#9b6a3c"))
    c.drawRect(skia.Rect.MakeLTRB(bx0, by0, bx1, by1), fill("#d4a574"))
    rng = np.random.default_rng(3)
    for k in range(10):
        c.drawCircle(rng.uniform(bx0 + 10, bx1 - 10), rng.uniform(by0 + 10, by1 - 10), 3, fill(alpha("#8a5a2c", 0.6)))
    papers = [(640, 330, 150, 120, "#fffbe8", -4), (810, 320, 170, 140, "#e8f4ff", 3), (650, 480, 160, 180, "#ffe8ef", 2),
              (835, 490, 150, 170, "#fffbe8", -3)]
    for (x, y, w, h, col, ang) in papers:
        c.save()
        c.rotate(ang, x + w / 2, y + h / 2)
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fill(col))
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), stroke(alpha("#000000", 0.12), 2))
        c.drawCircle(x + w / 2, y + 8, 6, fill("#e2463b"))
        c.restore()
    # kid drawings
    c.drawCircle(700, 400, 26, fill("#ffcf3f"))
    for k in range(8):
        a = k * math.pi / 4
        c.drawLine(700 + 34 * math.cos(a), 400 + 34 * math.sin(a), 700 + 48 * math.cos(a), 400 + 48 * math.sin(a), stroke("#ffb52e", 5))
    hp = skia.Path()
    hp.moveTo(870, 400)
    hp.lineTo(900, 360)
    hp.lineTo(930, 400)
    hp.close()
    c.drawPath(hp, fill("#e2463b"))
    c.drawRect(skia.Rect.MakeLTRB(876, 400, 924, 440), fill("#5aa0d8"))
    f = font("PatrickHand.ttf", 34)
    c.drawString("A+", 690, 600, f, fill("#e2463b"))
    c.drawString("2+2=4", 850, 590, f, fill("#3a5aa8"))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(-400, 1360, 1480, 2400), lin_grad((0, 1360), (0, 1920), ["#b98656", "#9c6b40"]))
    for k in range(-4, 16):
        c.drawLine(k * 110, 1360, k * 160 - 300, 2400, stroke(alpha("#7d522e", 0.35), 3))


def _clock(cv, x, y, r, t):
    cv.drawCircle(x, y + 6, r + 10, fill(alpha("#000000", 0.12)))
    cv.drawCircle(x, y, r + 10, fill("#3f4a5a"))
    cv.drawCircle(x, y, r, fill("#fffdf6"))
    for k in range(12):
        a = k * math.pi / 6
        cv.drawLine(x + r * 0.78 * math.cos(a), y + r * 0.78 * math.sin(a), x + r * 0.92 * math.cos(a), y + r * 0.92 * math.sin(a),
                    stroke("#3f4a5a", 5 if k % 3 == 0 else 3))
    sec = math.floor(t - 0.3) + 12
    hm = 2.5 * math.pi / 6 - math.pi / 2 + sec / 3600 * 2 * math.pi
    mm = 42 / 60 * 2 * math.pi - math.pi / 2 + sec / 60 / 60 * 2 * math.pi
    ss = sec / 60 * 2 * math.pi - math.pi / 2
    cv.drawLine(x, y, x + r * 0.5 * math.cos(hm), y + r * 0.5 * math.sin(hm), stroke("#2a2f38", 8))
    cv.drawLine(x, y, x + r * 0.75 * math.cos(mm), y + r * 0.75 * math.sin(mm), stroke("#2a2f38", 6))
    cv.drawLine(x, y, x + r * 0.85 * math.cos(ss), y + r * 0.85 * math.sin(ss), stroke("#e2463b", 3))
    cv.drawCircle(x, y, 7, fill("#e2463b"))


def class_back_bg(cv, t):
    cv.drawPicture(picture("class_back", _class_back))
    _clock(cv, 805, 150, 70, t)


def desk(cv, x, y, w=330):
    # desk top seen slightly from above, then front panel
    top = path_poly([(x - w / 2 + 14, y), (x + w / 2 - 14, y), (x + w / 2, y + 56), (x - w / 2, y + 56)])
    cv.drawPath(top, fill("#e7bd84"))
    cv.drawPath(top, stroke("#8f6338", 4))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y + 56, x + w / 2, y + 80), fill("#c9935a"))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2, y + 56, x + w / 2, y + 80), stroke("#8f6338", 4))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2 + 25, y + 80, x + w / 2 - 25, y + 260), fill("#a8b3bd"))
    cv.drawRect(skia.Rect.MakeLTRB(x - w / 2 + 25, y + 80, x + w / 2 - 25, y + 260), stroke("#5f6b75", 4))
    for lx in (x - w / 2 + 40, x + w / 2 - 40):
        cv.drawRect(skia.Rect.MakeLTRB(lx - 8, y + 260, lx + 8, y + 560), fill("#7d8892"))


def class_back_fg(cv, t):
    desk(cv, 300, 1236)
    desk(cv, 780, 1236)
    # notebooks & pencils
    for (x, ang, col) in [(270, -6, "#5aa0d8"), (800, 5, "#e88a3c")]:
        cv.save()
        cv.rotate(ang, x, 1262)
        cv.drawRect(skia.Rect.MakeLTRB(x - 60, 1246, x + 60, 1280), fill(col))
        cv.drawRect(skia.Rect.MakeLTRB(x - 60, 1246, x + 60, 1280), stroke(shade(col, 0.6), 3))
        cv.drawRect(skia.Rect.MakeLTRB(x - 54, 1250, x + 54, 1274), fill("#fffaf0"))
        cv.restore()


# =================================================================== CLASSROOM (teacher view)
def _class_front(c):
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, 1480, 1500), lin_grad((0, 0), (0, 1500), ["#f6e9cf", "#ecd6ae"]))
    for k in range(-6, 30):
        c.drawRect(skia.Rect.MakeLTRB(k * 60, -400, k * 60 + 28, 1500), fill(alpha("#e3c995", 0.18)))
    # chalkboard
    x0, y0, x1, y1 = 70, 380, 1010, 1080
    c.drawRect(skia.Rect.MakeLTRB(x0 - 26, y0 - 26, x1 + 26, y1 + 26), fill("#8a5a32"))
    c.drawRect(skia.Rect.MakeLTRB(x0 - 26, y0 - 26, x1 + 26, y1 + 26), stroke("#5c3a1e", 5))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), lin_grad((0, y0), (0, y1), ["#2f5e4b", "#284f40"]))
    rng = np.random.default_rng(5)
    for k in range(14):
        xx, yy = rng.uniform(x0 + 30, x1 - 80), rng.uniform(y0 + 30, y1 - 30)
        c.drawLine(xx, yy, xx + rng.uniform(40, 160), yy + rng.uniform(-10, 10), stroke(alpha("#ffffff", 0.05), rng.uniform(10, 30)))
    chalk = alpha("#f4f1e6", 0.9)
    f1 = font("PatrickHand.ttf", 92)
    f2 = font("PatrickHand.ttf", 120)
    c.drawString("Rule #1:", 150, 520, f1, fill(chalk))
    c.drawString("NO LAUGHING.", 150, 650, f2, fill(chalk))
    c.drawLine(150, 672, 760, 668, stroke(chalk, 5))
    f3 = font("PatrickHand.ttf", 54)
    c.drawString("Quiet reading", 650, 460, f3, fill(alpha("#ffd9e6", 0.85)))
    c.drawString("until 3:00", 690, 520, f3, fill(alpha("#ffd9e6", 0.85)))
    c.drawString("7 x 8 = 56", 120, 1010, f3, fill(alpha("#cfe9ff", 0.8)))
    # tray
    c.drawRect(skia.Rect.MakeLTRB(x0 - 30, y1 + 22, x1 + 30, y1 + 46), fill("#7a4c28"))
    c.drawRect(skia.Rect.MakeLTRB(300, y1 + 12, 350, y1 + 24), fill("#ffffff"))
    c.drawRect(skia.Rect.MakeLTRB(380, y1 + 14, 470, y1 + 32), fill("#3d3d46"))
    # flag-ish pennant string
    for k in range(8):
        xx = 120 + k * 120
        p = path_poly([(xx, 250), (xx + 90, 250), (xx + 45, 320)])
        c.drawPath(p, fill(["#f2c14e", "#e2463b", "#5aa0d8", "#6fb36a"][k % 4]))
    c.drawLine(80, 248, 1010, 248, stroke("#7a5a3a", 3))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1500, 1480, 2400), fill("#a8774a"))


def class_front_bg(cv, t):
    cv.drawPicture(picture("class_front", _class_front))


def class_front_fg(cv, t):
    x0, x1, y = 120, 960, 1500
    top = path_poly([(x0 + 30, y), (x1 - 30, y), (x1, y + 70), (x0, y + 70)])
    cv.drawPath(top, fill("#b07a48"))
    cv.drawPath(top, stroke("#5c3a1e", 5))
    cv.drawRect(skia.Rect.MakeLTRB(x0, y + 70, x1, y + 520), fill("#8f5d33"))
    cv.drawRect(skia.Rect.MakeLTRB(x0, y + 70, x1, y + 520), stroke("#5c3a1e", 5))
    cv.drawRect(skia.Rect.MakeLTRB(x0 + 40, y + 110, x1 - 40, y + 380), stroke(alpha("#5c3a1e", 0.6), 4))
    # apple
    cv.drawCircle(780, y + 12, 40, fill("#e2463b"))
    cv.drawCircle(766, y, 12, fill((1, 1, 1, 0.4)))
    cv.drawLine(782, y - 28, 790, y - 48, stroke("#5c3a1e", 6))
    lf = ellipse(806, y - 44, 18, 9)
    cv.drawPath(lf, fill("#6fb36a"))
    # books
    for k, col in enumerate(["#5aa0d8", "#f2c14e", "#6fb36a"]):
        cv.drawRect(skia.Rect.MakeLTRB(230 + k * 6, y - 30 - k * 28, 400 + k * 4, y - 2 - k * 28), fill(col))
        cv.drawRect(skia.Rect.MakeLTRB(230 + k * 6, y - 30 - k * 28, 400 + k * 4, y - 2 - k * 28), stroke(shade(col, 0.6), 3))


# =================================================================== BACKYARD (dusk)
def _yard_sky(c):
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, 1480, 1300),
               lin_grad((0, -200), (0, 1150), ["#262a5a", "#5a3f86", "#c4628a", "#f58b72", "#ffc27a"], [0.0, 0.35, 0.65, 0.85, 1.0]))
    c.drawCircle(300, 1110, 420, rad_grad((300, 1110), 420, [alpha("#fff0b0", 0.55), alpha("#ffb070", 0.0)]))
    rng = np.random.default_rng(1)
    for k in range(30):
        x, y = rng.uniform(-300, 1400), rng.uniform(-300, 380)
        c.drawCircle(x, y, rng.uniform(1.5, 3.2), fill(alpha("#fff6e0", rng.uniform(0.4, 0.9))))
    # clouds
    for (x, y, s) in [(780, 520, 1.0), (180, 640, 0.8)]:
        for k, (dx, dy, r) in enumerate([(0, 0, 60), (60, -20, 70), (130, 0, 55), (70, 20, 60)]):
            c.drawCircle(x + dx * s, y + dy * s, r * s, fill(alpha("#f7a8a0", 0.55)))
    # distant trees
    p = skia.Path()
    p.moveTo(-400, 1300)
    xs = np.arange(-400, 1500, 40)
    rng = np.random.default_rng(2)
    for x in xs:
        p.lineTo(x, 1010 + 40 * math.sin(x / 90) + rng.uniform(-25, 15))
    p.lineTo(1500, 1300)
    p.close()
    c.drawPath(p, fill("#3a2f58"))
    # house corner (right)
    c.drawRect(skia.Rect.MakeLTRB(940, 760, 1480, 1300), fill("#6b5a7a"))
    for k in range(14):
        c.drawLine(940, 780 + k * 36, 1480, 780 + k * 36, stroke(alpha("#4d3f5c", 0.6), 3))
    c.drawPath(path_poly([(900, 770), (1480, 600), (1480, 640), (940, 800)]), fill("#3d3250"))
    c.drawRect(skia.Rect.MakeLTRB(1000, 900, 1150, 1080), fill("#ffcf7a"))
    c.drawRect(skia.Rect.MakeLTRB(1000, 900, 1150, 1080), stroke("#4d3f5c", 8))
    # fence
    for k in range(-6, 22):
        x = k * 70
        c.drawPath(path_poly([(x, 1010), (x + 30, 985), (x + 60, 1010), (x + 60, 1290), (x, 1290)]), fill("#a8705a"))
        c.drawPath(path_poly([(x, 1010), (x + 30, 985), (x + 60, 1010), (x + 60, 1290), (x, 1290)]), stroke("#6e4434", 3))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1060, 1480, 1080), fill("#8a5644"))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1210, 1480, 1230), fill("#8a5644"))
    # lawn
    c.drawRect(skia.Rect.MakeLTRB(-400, 1270, 1480, 2400), lin_grad((0, 1270), (0, 1920), ["#5c7d48", "#3e5c34"]))
    rng = np.random.default_rng(4)
    for k in range(160):
        x, y = rng.uniform(-300, 1400), rng.uniform(1290, 1920)
        c.drawLine(x, y, x + rng.uniform(-6, 6), y - rng.uniform(10, 22), stroke(alpha("#7fa060", 0.5), 3))


def string_lights(cv, t, pts_list, seed=0, night=False):
    for si, (p0, p1, sag) in enumerate(pts_list):
        path = skia.Path()
        path.moveTo(*p0)
        mx = (p0[0] + p1[0]) / 2
        my = (p0[1] + p1[1]) / 2 + sag
        path.quadTo(mx, my + sag * 0.0, *p1)
        cv.drawPath(path, stroke("#2b2530", 3))
        n = 9
        for k in range(1, n):
            u = k / n
            x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * mx + u ** 2 * p1[0]
            y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * (my) + u ** 2 * p1[1]
            fl = 0.85 + 0.15 * math.sin(t * 2.3 + k * 1.7 + si)
            glow(cv, x, y + 14, 46 if night else 34, "#ffd27a", (0.55 if night else 0.4) * fl)
            cv.drawCircle(x, y + 14, 9, fill(mixc("#fff3c4", "#ffd27a", 0.3)))
            cv.drawRect(skia.Rect.MakeLTRB(x - 4, y, x + 4, y + 7), fill("#2b2530"))


def smoke(cv, x, y, t):
    for k in range(6):
        ph = (t * 0.35 + k / 6) % 1.0
        yy = y - ph * 260
        xx = x + 25 * math.sin(ph * 6 + k) + ph * 30
        r = 18 + ph * 40
        cv.drawCircle(xx, yy, r, fill(alpha("#d9d2dc", 0.16 * (1 - ph) * min(1, ph * 5))))


def grill(cv, x, y, t, with_smoke=True):
    # legs
    for dx in (-50, 0, 50):
        cv.drawLine(x, y + 30, x + dx * 1.6, y + 190, stroke("#2a2a30", 8))
    cv.drawCircle(x, y + 190, 6, fill("#2a2a30"))
    bowl = skia.Path()
    bowl.moveTo(x - 115, y - 10)
    bowl.cubicTo(x - 110, y + 70, x + 110, y + 70, x + 115, y - 10)
    bowl.close()
    cv.drawPath(bowl, fill("#2f2f38"))
    cv.drawPath(bowl, stroke("#151519", 4))
    cv.drawPath(bowl, lin_grad((x - 115, 0), (x + 115, 0), [alpha("#ffffff", 0.0), alpha("#ffffff", 0.15), alpha("#ffffff", 0.0)], [0.2, 0.4, 0.6]))
    # grate & patties
    cv.drawRect(skia.Rect.MakeLTRB(x - 118, y - 16, x + 118, y - 6), fill("#8a8f99"))
    for k, dx in enumerate((-60, 5, 65)):
        pt = ellipse(x + dx, y - 22, 34, 12)
        cv.drawPath(pt, fill("#6b3a24"))
        cv.drawPath(pt, stroke("#3d1e10", 3))
        if k == 1:
            cv.drawRect(skia.Rect.MakeLTRB(x + dx - 30, y - 30, x + dx + 30, y - 25), fill("#f2c14e"))
    if with_smoke:
        smoke(cv, x - 20, y - 40, t)
    glow(cv, x, y - 20, 140, "#ff8a3a", 0.18 + 0.05 * math.sin(t * 7))


def yard_bg(cv, t):
    cv.drawPicture(picture("yard_sky", _yard_sky))
    string_lights(cv, t, [((-60, 300), (1140, 420), 120), ((-60, 560), (1140, 470), 100)])


def picnic_table(cv, t):
    y = 1420
    top = path_poly([(40, y), (1040, y), (1080, y + 70), (0, y + 70)])
    cv.drawPath(top, fill("#c58b5a"))
    for k in range(1, 4):
        cv.drawLine(40 + k * 0 - 20, y + k * 17, 1060, y + k * 17, stroke(alpha("#8a5a34", 0.5), 3))
    cv.drawPath(top, stroke("#6e4426", 5))
    cv.drawRect(skia.Rect.MakeLTRB(0, y + 70, 1080, y + 100), fill("#a8703f"))
    cv.drawRect(skia.Rect.MakeLTRB(0, y + 70, 1080, y + 100), stroke("#6e4426", 5))
    for lx in (160, 920):
        cv.drawPath(path_poly([(lx - 12, y + 100), (lx + 12, y + 100), (lx + 90, y + 520), (lx + 62, y + 520)]), fill("#8a5a34"))
        cv.drawPath(path_poly([(lx - 12, y + 100), (lx + 12, y + 100), (lx - 62, y + 520), (lx - 90, y + 520)]), fill("#8a5a34"))
    # bench (front)
    cv.drawRect(skia.Rect.MakeLTRB(-40, y + 290, 1120, y + 330), fill("#b57e4e"))
    cv.drawRect(skia.Rect.MakeLTRB(-40, y + 290, 1120, y + 330), stroke("#6e4426", 5))
    # plates/items on table
    for (px, col) in [(225, "#ffffff"), (478, "#ffffff"), (718, "#ffffff")]:
        pl = ellipse(px, y + 32, 70, 18)
        cv.drawPath(pl, fill(col))
        cv.drawPath(pl, stroke("#b9b0a6", 3))
    bun = ellipse(225, y + 22, 40, 14)
    cv.drawPath(bun, fill("#3a2416"))  # burned bun!
    cv.drawPath(bun, stroke("#1d120b", 3))
    cv.drawPath(ellipse(478, y + 22, 40, 14), fill("#e0a35a"))
    cv.drawPath(ellipse(478, y + 22, 40, 14), stroke("#8a5a2a", 3))
    # ketchup bottle
    cv.drawRoundRect(skia.Rect.MakeLTRB(580, y - 70, 620, y + 20), 14, 14, fill("#d8392c"))
    cv.drawRect(skia.Rect.MakeLTRB(590, y - 92, 610, y - 70), fill("#f2f2f2"))


# =================================================================== MIND BRIDGE
def _bridge(c):
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, 1480, 2400), lin_grad((0, 0), (0, 1920), ["#141a33", "#232b52", "#1a2142"]))
    # wall panels
    for k in range(-2, 10):
        x = k * 150
        c.drawRect(skia.Rect.MakeLTRB(x + 8, 60, x + 142, 1020), fill(alpha("#2c3563", 0.6)))
        c.drawLine(x + 75, 60, x + 75, 1020, stroke(alpha("#3d4a85", 0.35), 2))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(-400, 1100, 1480, 2400), lin_grad((0, 1100), (0, 1920), ["#2b3463", "#1b2145"]))
    c.drawOval(skia.Rect.MakeLTRB(120, 1300, 960, 1700), fill(alpha("#3f4d8f", 0.45)))
    c.drawOval(skia.Rect.MakeLTRB(120, 1300, 960, 1700), stroke(alpha("#7fd1ff", 0.35), 4))
    # screen frame
    c.drawRoundRect(skia.Rect.MakeLTRB(70, 150, 1010, 760), 40, 40, fill("#0b0f20"))
    c.drawRoundRect(skia.Rect.MakeLTRB(70, 150, 1010, 760), 40, 40, stroke("#7fd1ff", 8))


def bridge_bg(cv, t, screen_img=None, alarm=0.0):
    cv.drawPicture(picture("bridge", _bridge))
    if screen_img is not None:
        cv.save()
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(84, 164, 996, 746), 30, 30)
        cv.clipRRect(rr, True)
        src = skia.Rect.MakeXYWH(0, 0, screen_img.width(), screen_img.height())
        # show the middle band of the yard frame
        sw, sh = screen_img.width(), screen_img.height()
        crop_h = sw * (582 / 912)
        src = skia.Rect.MakeXYWH(0, sh * 0.42 - crop_h / 2, sw, crop_h)
        cv.drawImageRect(screen_img, src, skia.Rect.MakeLTRB(84, 164, 996, 746), skia.SamplingOptions(skia.FilterMode.kLinear))
        for y in range(164, 746, 6):
            cv.drawLine(84, y, 996, y, stroke(alpha("#000000", 0.12), 2))
        cv.drawRect(skia.Rect.MakeLTRB(84, 164, 996, 746), fill(alpha("#7fd1ff", 0.08)))
        # PAUSED label
        f = font("Fredoka-SemiBold.ttf", 40)
        if int(t * 2) % 2 == 0:
            cv.drawString("❚❚ FROZEN", 120, 220, f, fill(alpha("#ffffff", 0.85)))
        cv.restore()
    if alarm > 0:
        pulse = 0.5 + 0.5 * math.sin(t * 9)
        cv.drawRect(skia.Rect.MakeLTRB(-400, -400, 1480, 2400), fill(alpha("#ff5f8a", 0.10 * alarm * pulse)))
        glow(cv, 540, 60, 300, "#ff5f8a", 0.6 * alarm * pulse)


def bridge_consoles(cv, t):
    for (x0, x1) in [(20, 380), (700, 1060)]:
        top = path_poly([(x0 + 30, 1080), (x1 - 30, 1080), (x1, 1150), (x0, 1150)])
        cv.drawPath(top, fill("#3a4a8a"))
        cv.drawPath(top, stroke("#7fd1ff", 3))
        cv.drawRect(skia.Rect.MakeLTRB(x0, 1150, x1, 1330), fill("#2a3566"))
        cv.drawRect(skia.Rect.MakeLTRB(x0, 1150, x1, 1330), stroke("#1a2142", 4))
    rng = np.random.default_rng(int(t * 3))
    for (x0, x1) in [(20, 380), (700, 1060)]:
        for k in range(6):
            on = rng.random() > 0.4
            col = ["#7fd1ff", "#ffcf3f", "#ff6f91", "#7cf0a0"][k % 4]
            cx, cy = x0 + 60 + k * 50, 1112
            cv.drawCircle(cx, cy, 10, fill(col if on else shade(col, 0.4)))
            if on:
                glow(cv, cx, cy, 26, col, 0.4)
    f = font("Fredoka-SemiBold.ttf", 38)
    for (txt, x, y) in [("DOUBT", 200, 1270), ("ANGER", 880, 1270)]:
        w = text_width(txt, f)
        cv.drawRoundRect(skia.Rect.MakeLTRB(x - w / 2 - 18, y - 38, x + w / 2 + 18, y + 14), 12, 12, fill("#0b0f20"))
        cv.drawRoundRect(skia.Rect.MakeLTRB(x - w / 2 - 18, y - 38, x + w / 2 + 18, y + 14), 12, 12, stroke("#7fd1ff", 3))
        cv.drawString(txt, x - w / 2, y, f, fill("#bfe9ff"))


def captain_chair(cv, t):
    x, y = 540, 1640
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 210, y - 60, x + 210, y + 400), 60, 60, fill("#c2453a"))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 210, y - 60, x + 210, y + 400), 60, 60, stroke("#7a221a", 6))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 170, y - 20, x + 170, y + 360), 40, 40, fill("#d65a4c"))
    # mini-me back of head
    hc = "#7a3f26"
    p = smooth_closed([(x - 120, y - 40), (x - 125, y - 150), (x - 60, y - 230), (x + 60, y - 230), (x + 125, y - 150),
                       (x + 120, y - 40), (x, y - 20)], 0.6)
    cv.drawPath(p, fill(hc))
    cv.drawPath(p, stroke(shade(hc, 0.6), 5))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x + 50, y - 175, x + 105, y - 150), 10, 10, fill("#ffcf3f"))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x + 50, y - 175, x + 105, y - 150), 10, 10, stroke("#b8860b", 3))


def stool(cv, x, y):
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 120, y - 20, x + 120, y + 30), 20, 20, fill("#e9a82c"))
    cv.drawRoundRect(skia.Rect.MakeLTRB(x - 120, y - 20, x + 120, y + 30), 20, 20, stroke("#8a5a10", 5))
    cv.drawRect(skia.Rect.MakeLTRB(x - 12, y + 30, x + 12, y + 160), fill("#9aa3b8"))
    cv.drawRect(skia.Rect.MakeLTRB(x - 90, y + 160, x + 90, y + 180), fill("#6f7891"))


# =================================================================== PORCH (night) + sky above
STAR_RNG = np.random.default_rng(42)
STARS = [(STAR_RNG.uniform(-200, 1280), STAR_RNG.uniform(-1900, 420), STAR_RNG.uniform(1.2, 3.6), STAR_RNG.uniform(0, 6.28))
         for _ in range(260)]
KEYHOLE_STARS = []
for k in range(18):
    a = k / 18 * 2 * math.pi - math.pi / 2
    KEYHOLE_STARS.append((540 + 125 * math.cos(a), -1120 + 125 * math.sin(a)))
for k in range(7):
    u = k / 6
    KEYHOLE_STARS.append((540 - 55 - 60 * u, -995 + 260 * u))
    KEYHOLE_STARS.append((540 + 55 + 60 * u, -995 + 260 * u))
KEYHOLE_STARS += [(540 - 70, -735), (540 - 23, -735), (540 + 23, -735), (540 + 70, -735)]


def _porch(c):
    c.drawRect(skia.Rect.MakeLTRB(-400, -2400, 1480, 500), lin_grad((0, -2000), (0, 450), ["#070b1f", "#111a3d", "#24305e"], [0.0, 0.6, 1.0]))
    # moon
    c.drawCircle(820, -220, 70, fill("#f4f0dc"))
    c.drawCircle(845, -235, 62, fill(alpha("#24305e", 0.0)))
    c.drawCircle(820, -220, 200, rad_grad((820, -220), 200, [alpha("#f4f0dc", 0.25), alpha("#f4f0dc", 0.0)]))
    for (x, y, r) in [(800, -240, 10), (840, -200, 7), (810, -190, 6)]:
        c.drawCircle(x, y, r, fill(alpha("#d8d2bb", 0.8)))
    # tree silhouettes left
    for (x, y, r) in [(-60, 330, 210), (110, 280, 160), (230, 360, 150)]:
        c.drawCircle(x, y, r, fill("#0f1631"))
    # roof
    c.drawPath(path_poly([(-400, 470), (1480, 470), (1480, 380), (-400, 380)]), fill("#2a2738"))
    c.drawRect(skia.Rect.MakeLTRB(-400, 460, 1480, 500), fill("#3a3550"))
    # wall
    c.drawRect(skia.Rect.MakeLTRB(-400, 500, 1480, 1460), fill("#3c4a6e"))
    for k in range(30):
        y = 520 + k * 34
        c.drawLine(-400, y, 1480, y, stroke(alpha("#2c3756", 0.8), 3))
    # window left
    c.drawRect(skia.Rect.MakeLTRB(90, 640, 430, 1010), fill("#ffcf7e"))
    c.drawRect(skia.Rect.MakeLTRB(90, 640, 430, 1010), rad_grad((260, 820), 260, ["#fff0c0", "#ffb860"]))
    c.drawRect(skia.Rect.MakeLTRB(90, 640, 430, 1010), stroke("#2a2738", 14))
    c.drawLine(260, 640, 260, 1010, stroke("#2a2738", 10))
    c.drawLine(90, 825, 430, 825, stroke("#2a2738", 10))
    c.drawPath(path_poly([(97, 647), (180, 647), (130, 1003), (97, 1003)]), fill(alpha("#c0583a", 0.7)))
    c.drawPath(path_poly([(423, 647), (340, 647), (390, 1003), (423, 1003)]), fill(alpha("#c0583a", 0.7)))
    # door
    c.drawRect(skia.Rect.MakeLTRB(620, 700, 900, 1460), fill("#4a2e22"))
    c.drawRect(skia.Rect.MakeLTRB(620, 700, 900, 1460), stroke("#24160f", 10))
    c.drawRect(skia.Rect.MakeLTRB(670, 760, 850, 940), fill("#ffcf7e"))
    c.drawRect(skia.Rect.MakeLTRB(670, 760, 850, 940), stroke("#24160f", 8))
    for (y0, y1) in [(990, 1180), (1220, 1410)]:
        c.drawRect(skia.Rect.MakeLTRB(670, y0, 850, y1), stroke(alpha("#24160f", 0.8), 6))
    c.drawCircle(870, 1100, 12, fill("#d9b24a"))
    # porch floor & steps
    c.drawRect(skia.Rect.MakeLTRB(-400, 1450, 1480, 1530), fill("#6e4c37"))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1450, 1480, 1462), fill("#8a6248"))
    for k, (y0, y1) in enumerate([(1530, 1660), (1660, 1790), (1790, 1920), (1920, 2100)]):
        c.drawRect(skia.Rect.MakeLTRB(-400, y0, 1480, y1), fill(shade("#6e4c37", 1.0 - 0.08 * k)))
        c.drawRect(skia.Rect.MakeLTRB(-400, y0, 1480, y0 + 14), fill(shade("#8a6248", 1.0 - 0.08 * k)))
        c.drawLine(-400, y0, 1480, y0, stroke("#3a2618", 4))
    # railing posts
    for x in (-20, 1060):
        c.drawRect(skia.Rect.MakeLTRB(x - 26, 900, x + 26, 1530), fill("#e8e0d0"))
        c.drawRect(skia.Rect.MakeLTRB(x - 26, 900, x + 26, 1530), stroke("#8a8070", 4))


def porch_bg(cv, t, star_reveal=0.0):
    cv.drawPicture(picture("porch", _porch, y0=-2000))
    for (x, y, r, ph) in STARS:
        tw = 0.6 + 0.4 * math.sin(t * 1.7 + ph)
        cv.drawCircle(x, y, r, fill(alpha("#fffbe8", 0.85 * tw)))
    if star_reveal > 0:
        for k, (x, y) in enumerate(KEYHOLE_STARS):
            a = clamp(star_reveal * 1.6 - k / len(KEYHOLE_STARS) * 0.6)
            if a > 0:
                glow(cv, x, y, 34, "#fff3c4", 0.75 * a)
                cv.drawCircle(x, y, 6, fill(alpha("#fffbe8", a)))
        if star_reveal > 0.6:
            g = clamp((star_reveal - 0.6) / 0.4)
            glow(cv, 540, -1050, 320, "#ffd98a", 0.25 * g)
    # porch lamp
    glow(cv, 960, 700, 380, "#ffcc77", 0.32 + 0.02 * math.sin(t * 3))
    cv.drawRoundRect(skia.Rect.MakeLTRB(935, 650, 985, 740), 12, 12, fill("#fff1c8"))
    cv.drawRoundRect(skia.Rect.MakeLTRB(935, 650, 985, 740), 12, 12, stroke("#2a2738", 6))
    string_lights(cv, t, [((-60, 505), (1140, 520), 70)], night=True)
    # fireflies
    for k in range(7):
        fx = 540 + 520 * wobble(t * 0.15, k * 3.3, 0.6)
        fy = 1150 + 420 * wobble(t * 0.12, k * 7.1 + 2, 0.5)
        a = 0.5 + 0.5 * math.sin(t * 2 + k * 2.1)
        glow(cv, fx, fy, 22, "#d8ff7a", 0.55 * a)
        cv.drawCircle(fx, fy, 3, fill(alpha("#f4ffc0", a)))


# =================================================================== FORTRESS (Danny's mind)
def _stone_wall(c, x0, y0, x1, y1, base="#3b4058", seed=1):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(shade(base, 0.7)))
    rng = np.random.default_rng(seed)
    bh = 70
    row = 0
    y = y0
    while y < y1:
        off = (row % 2) * 60
        x = x0 - 120 + off
        while x < x1:
            w = rng.uniform(100, 160)
            col = shade(base, rng.uniform(0.85, 1.15))
            c.drawRoundRect(skia.Rect.MakeLTRB(x + 5, y + 5, x + w - 5, y + bh - 5), 12, 12, fill(col))
            c.drawRoundRect(skia.Rect.MakeLTRB(x + 5, y + 5, x + w - 5, y + bh * 0.4), 10, 10, fill(alpha("#ffffff", 0.05)))
            x += w
        y += bh
        row += 1


def _fortress(c):
    _stone_wall(c, -400, -400, 1480, 1500, "#3e4560", 3)
    # arch
    arch = skia.Path()
    arch.moveTo(330, 1500)
    arch.lineTo(330, 900)
    arch.cubicTo(330, 700, 750, 700, 750, 900)
    arch.lineTo(750, 1500)
    c.drawPath(arch, stroke("#2a2f45", 60))
    c.drawPath(arch, stroke("#555d7e", 40))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(-400, 1500, 1480, 2400), lin_grad((0, 1500), (0, 1920), ["#3a3f55", "#22263a"]))
    for k in range(-6, 16):
        c.drawLine(540 + (k - 5) * 60, 1500, 540 + (k - 5) * 220, 2400, stroke(alpha("#1a1d2c", 0.6), 4))
    for y in (1580, 1700, 1860):
        c.drawLine(-400, y, 1480, y, stroke(alpha("#1a1d2c", 0.6), 4))
    # dark doorway interior
    inner = skia.Path()
    inner.moveTo(360, 1500)
    inner.lineTo(360, 910)
    inner.cubicTo(360, 740, 720, 740, 720, 910)
    inner.lineTo(720, 1500)
    inner.close()
    c.drawPath(inner, fill("#0b0c14"))


def torch(cv, x, y, t, seed=0):
    cv.drawRect(skia.Rect.MakeLTRB(x - 10, y, x + 10, y + 110), fill("#4a3020"))
    cv.drawPath(path_poly([(x - 30, y), (x + 30, y), (x + 18, y + 30), (x - 18, y + 30)]), fill("#5a5f70"))
    fl = 0.85 + 0.15 * math.sin(t * 11 + seed) * math.sin(t * 7.3 + seed * 2)
    glow(cv, x, y - 30, 330 * fl, "#ff9a3c", 0.35)
    for k, (col, sc) in enumerate([("#ff6a1c", 1.0), ("#ffb23e", 0.7), ("#fff0a0", 0.4)]):
        p = skia.Path()
        h = 90 * sc * fl
        w = 34 * sc
        sway = 8 * math.sin(t * 6 + seed + k)
        p.moveTo(x - w, y)
        p.cubicTo(x - w, y - h * 0.5, x + sway - 4, y - h * 0.8, x + sway, y - h)
        p.cubicTo(x + sway + 4, y - h * 0.8, x + w, y - h * 0.5, x + w, y)
        p.close()
        cv.drawPath(p, fill(col))


def fortress_bg(cv, t):
    cv.drawPicture(picture("fortress", _fortress))
    torch(cv, 160, 820, t, 1)
    torch(cv, 920, 820, t, 2)


def cell_interior(cv, t, light=0.0, x0=360, x1=720):
    """Contents seen through the open doorway (drawn in fortress coords, clipped by caller)."""
    cv.drawRect(skia.Rect.MakeLTRB(x0 - 50, 700, x1 + 50, 1500), fill("#0b0c14"))
    if light > 0:
        beam = path_poly([(x0, 1500), (x0 + 60, 900), (x0 + 200, 900), (x1 + 120, 1500)])
        cv.drawPath(beam, lin_grad((0, 900), (0, 1500), [alpha("#ffc070", 0.0), alpha("#ffc070", 0.35 * light)]))


def door(cv, t, open_amt=0.0, keyhole_glow=0.6):
    """Wooden door hinged at left edge (x=360). open_amt 0..1."""
    x0, x1, y0, y1 = 360, 720, 740, 1500
    w = (x1 - x0) * (1 - 0.82 * open_amt)
    skew = 60 * open_amt
    p = skia.Path()
    p.moveTo(x0, y1)
    p.lineTo(x0, 910)
    p.cubicTo(x0, y0, x0 + w, y0 - skew * 0.3, x0 + w, 910 - skew * 0.4)
    p.lineTo(x0 + w, y1 + skew * 0.4)
    p.close()
    cv.drawPath(p, fill(shade("#6b4428", 1.0 - 0.35 * open_amt)))
    cv.save()
    cv.clipPath(p, doAntiAlias=True)
    for k in range(6):
        xx = x0 + (k + 1) * w / 6
        cv.drawLine(xx, y0 - 100, xx, y1 + 100, stroke(alpha("#3a2414", 0.7), 5))
    for yy in (960, 1300):
        cv.drawRect(skia.Rect.MakeLTRB(x0 - 10, yy, x0 + w + 10, yy + 36), fill("#3a3d48"))
        for k in range(4):
            cv.drawCircle(x0 + 20 + k * (w - 40) / 3, yy + 18, 6, fill("#6a6e7c"))
    # keyhole plate
    kx, ky = x0 + w * 0.8, 1180
    cv.drawRoundRect(skia.Rect.MakeLTRB(kx - 26 * (1 - 0.6 * open_amt), ky - 50, kx + 26 * (1 - 0.6 * open_amt), ky + 60), 10, 10, fill("#b8923a"))
    kh = skia.Path()
    kh.addCircle(kx, ky - 10, 11 * (1 - 0.5 * open_amt))
    kh.addRect(skia.Rect.MakeLTRB(kx - 6 * (1 - 0.5 * open_amt), ky - 6, kx + 6 * (1 - 0.5 * open_amt), ky + 34))
    cv.drawPath(kh, fill("#ffd98a" if keyhole_glow > 0.3 else "#151515"))
    cv.restore()
    cv.drawPath(p, stroke("#2a1a0e", 6))
    if keyhole_glow > 0.05:
        glow(cv, kx, ky, 90, "#ffcc66", 0.45 * keyhole_glow)


def _cell(c):
    _stone_wall(c, -400, -400, 1480, 1550, "#272b3e", 9)
    c.drawRect(skia.Rect.MakeLTRB(-400, 1550, 1480, 2400), lin_grad((0, 1550), (0, 1920), ["#22263a", "#141624"]))
    # high window slit with moonbeam
    c.drawRoundRect(skia.Rect.MakeLTRB(760, 420, 840, 600), 30, 30, fill("#9fb3e0"))
    beam = path_poly([(760, 600), (840, 600), (620, 1600), (330, 1600)])
    c.drawPath(beam, lin_grad((0, 600), (0, 1600), [alpha("#9fb3e0", 0.35), alpha("#9fb3e0", 0.05)]))
    c.drawOval(skia.Rect.MakeLTRB(300, 1540, 680, 1660), fill(alpha("#9fb3e0", 0.18)))


def cell_bg(cv, t):
    cv.drawPicture(picture("cell", _cell))


# =================================================================== shared overlays
def vignette(cv, strength=0.35, col="#000000"):
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, 1080, 1920),
                rad_grad((540, 900), 1250, [alpha(col, 0.0), alpha(col, 0.0), alpha(col, strength)], [0.0, 0.55, 1.0]))


def keyhole_path(cx, cy, s):
    p = skia.Path()
    p.addCircle(cx, cy - 0.35 * s, 0.42 * s)
    tr = path_poly([(cx - 0.2 * s, cy - 0.2 * s), (cx + 0.2 * s, cy - 0.2 * s), (cx + 0.36 * s, cy + 0.85 * s), (cx - 0.36 * s, cy + 0.85 * s)])
    return skia.Op(p, tr, skia.PathOp.kUnion_PathOp)
