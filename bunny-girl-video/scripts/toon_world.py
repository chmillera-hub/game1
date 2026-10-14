"""Cartoon scenery and effects for the Bunny Girl story (skia vector drawing).

Backgrounds take the canvas and a time (for drifting clouds, turning sun
rays, rippling river). Static pieces are cheap enough to redraw each frame.
"""
import math

import numpy as np
import skia

from toon import (OUT, WHITE, Fade, Xf, arc_path, circle, color, fill_paint, font, heart_path,
                  outlined_union, oval, poly, rrect, shape, smooth, sparkle_path, star_path,
                  stroke_paint, text)

W, H = 1080, 1920
SOFT = (88, 104, 128)        # softer outline for scenery so characters pop


def rect(c, x0, y0, x1, y1, rgb=None, shader=None):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill_paint(rgb or WHITE, 1.0, shader))


def vgrad(y0, y1, c0, c1, c2=None):
    cols = [color(c0), color(c1)] + ([color(c2)] if c2 else [])
    pos = None if c2 is None else [0.0, 0.6, 1.0]
    return skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], cols, pos)


# ------------------------------------------------------------------ sky
SKIES = {
    "day": ((126, 205, 246), (196, 233, 252), (255, 236, 244)),
    "soft": ((150, 214, 246), (210, 238, 252), (255, 240, 246)),
    "rain": ((126, 140, 166), (168, 180, 200), (196, 206, 220)),
    "snow": ((176, 196, 222), (214, 226, 242), (238, 244, 252)),
    "sunset": ((255, 176, 206), (255, 214, 214), (255, 236, 200)),
    "magic": ((150, 120, 200), (210, 170, 230), (255, 220, 240)),
}


def sky(c, kind="day", horizon=1200):
    a, b, cc = SKIES[kind]
    rect(c, 0, 0, W, horizon + 40, shader=vgrad(0, horizon, a, b, cc))


def sun(c, t, x=70, y=96, r=128, a=1.0):
    with Fade(c, a), Xf(c, x, y, t * 6):
        for i in range(14):
            with Xf(c, 0, 0, i * 360 / 14):
                ray = poly([(-16, -r - 8), (0, -r - 62 - 10 * (i % 2)), (16, -r - 8)])
                shape(c, ray, (255, 170, 60), 4, out=(232, 96, 40))
        g = skia.GradientShader.MakeRadial(skia.Point(-20, -20), r * 1.3, [color((255, 246, 160)), color((255, 196, 56))])
        shape(c, circle(0, 0, r), (255, 214, 80), 6, out=(232, 96, 40), shader=g)


def cloud(c, x, y, s=1.0, rgb=WHITE, a=1.0, out=(150, 170, 205)):
    with Fade(c, a), Xf(c, x, y, 0, s):
        parts = [circle(-70, 10, 42), circle(-20, -20, 58), circle(40, -10, 50), circle(85, 14, 36), oval(10, 22, 100, 34)]
        outlined_union(c, parts, rgb, 3.5, out=out)
        c.drawPath(oval(-12, -30, 26, 12), fill_paint(WHITE, 0.6))


def drifting_clouds(c, t, kind="day", ys=(640, 760, 600), speed=10.0):
    col = WHITE if kind not in ("rain",) else (196, 202, 214)
    out = (150, 170, 205) if kind != "rain" else (110, 118, 136)
    for i, (x0, y, s) in enumerate(((180, ys[0], 0.9), (720, ys[1], 0.75), (1180, ys[2], 1.05))):
        x = (x0 + speed * t * (1 + 0.3 * i)) % 1500 - 210
        cloud(c, x, y, s, col, 1.0, out)


# --------------------------------------------------------------- ground
def hills(c, base=1150, far=(184, 230, 164), near=(150, 216, 128), seed=0):
    p = skia.Path()
    p.moveTo(0, H)
    for x in range(0, W + 41, 40):
        p.lineTo(x, base - 40 * math.sin(x / 210 + seed) - 22 * math.sin(x / 90 + 2 * seed))
    p.lineTo(W, H)
    p.close()
    shape(c, p, far, 4, out=SOFT)
    q = skia.Path()
    q.moveTo(0, H)
    for x in range(0, W + 41, 40):
        q.lineTo(x, base + 70 - 26 * math.sin(x / 260 + 1.3 + seed) - 12 * math.sin(x / 70 + seed))
    q.lineTo(W, H)
    q.close()
    shape(c, q, near, 4, out=SOFT)


def ground(c, top=1260, c0=(146, 212, 120), c1=(116, 192, 98)):
    p = skia.Path()
    p.moveTo(0, H)
    for x in range(0, W + 41, 40):
        p.lineTo(x, top - 14 * math.sin(x / 160 + 0.7))
    p.lineTo(W, H)
    p.close()
    shape(c, p, c0, 4, out=SOFT, shader=vgrad(top, H, c0, c1))


def grass_tufts(c, seed=1, n=40, y0=1300, y1=1900, col=(92, 168, 84)):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.uniform(20, W - 20), rng.uniform(y0, y1)
        k = 0.6 + (y - y0) / (y1 - y0) * 0.8
        for dx, h, lean in ((-8, 22, -6), (0, 30, 0), (8, 22, 6)):
            p = skia.Path()
            p.moveTo(x + dx * k, y)
            p.quadTo(x + (dx + lean * 0.3) * k, y - h * 0.6 * k, x + (dx + lean) * k, y - h * k)
            c.drawPath(p, stroke_paint(col, 4 * k))


def tulip(c, x, y, s=1.0, col=(255, 140, 180), sway=0.0):
    with Xf(c, x, y, sway, s):
        p = skia.Path()
        p.moveTo(0, 0)
        p.quadTo(4, -40, 0, -78)
        c.drawPath(p, stroke_paint((70, 150, 80), 6))
        leaf = smooth([(0, -20), (-26, -44), (-6, -40)], k=1)
        shape(c, leaf, (110, 190, 100), 3, out=(60, 120, 70))
        head = smooth([(-18, -82), (-20, -104), (-9, -96), (0, -110), (9, -96), (20, -104), (18, -82), (0, -72)], k=0.6)
        shape(c, head, col, 3.5)


def daisy(c, x, y, s=1.0, col=WHITE, center=(255, 205, 60), sway=0.0):
    with Xf(c, x, y, sway, s):
        p = skia.Path()
        p.moveTo(0, 0)
        p.lineTo(0, -46)
        c.drawPath(p, stroke_paint((70, 150, 80), 5))
        for k in range(6):
            a = math.radians(k * 60)
            shape(c, oval(15 * math.cos(a), -52 + 15 * math.sin(a), 10, 10), col, 3)
        shape(c, circle(0, -52, 9), center, 3)


def round_flower(c, x, y, s=1.0, col=(176, 120, 220), stem=90, sway=0.0):
    with Xf(c, x, y, sway, s):
        p = skia.Path()
        p.moveTo(0, 0)
        p.quadTo(-6, -stem / 2, 0, -stem)
        c.drawPath(p, stroke_paint((60, 160, 120), 5))
        shape(c, oval(0, -stem - 8, 13, 16), col, 3.5)


def big_red_flower(c, x, y, s=1.0, sway=0.0):
    """Inspired by the big red flower in the hug drawing."""
    with Xf(c, x, y, sway, s):
        p = skia.Path()
        p.moveTo(0, 0)
        p.quadTo(-10, -70, 6, -150)
        c.drawPath(p, stroke_paint((50, 140, 110), 9))
        for sgn in (-1, 1):
            shape(c, smooth([(0, -60), (sgn * 70, -100), (sgn * 30, -70)], k=1), (90, 200, 170), 4, out=(40, 120, 100))
        bloom = smooth([(-70, -190), (-40, -235), (0, -205), (40, -235), (70, -190), (40, -150), (0, -140), (-40, -150)], k=0.9)
        shape(c, bloom, (238, 52, 60), 5)
        shape(c, smooth([(-22, -190), (0, -214), (22, -190), (0, -160)], k=0.8), (255, 210, 60), 4)


def round_tree(c, x, y, s=1.0, sway=0.0, col=(96, 196, 96), trunk=(150, 96, 62)):
    """Lollipop tree like the park drawing."""
    with Xf(c, x, y, 0, s):
        p = smooth([(-18, 0), (-12, -120), (-26, -190), (0, -170), (24, -200), (12, -120), (18, 0)], k=0.6)
        shape(c, p, trunk, 5)
        with Xf(c, 0, -230, sway):
            shape(c, oval(0, -60, 110, 128), col, 5)
            c.drawPath(oval(-34, -112, 34, 46), fill_paint(WHITE, 0.25))


def leafy_tree(c, x, y, s=1.0, t=0.0, seed=0):
    """Tall tree with separate leaves, like the hug drawing."""
    rng = np.random.default_rng(seed)
    with Xf(c, x, y, 0, s):
        trunk = smooth([(-22, 0), (-14, -300), (-50, -520), (-30, -530), (0, -380), (30, -560), (48, -548), (14, -300), (22, 0)], k=0.5)
        shape(c, trunk, (150, 100, 70), 5)
        for i in range(34):
            lx, ly = rng.uniform(-170, 170), rng.uniform(-760, -330)
            ang = rng.uniform(-60, 60) + 8 * math.sin(t * 1.6 + i)
            with Xf(c, lx, ly, ang):
                shape(c, oval(0, 0, 16, 30), (70 + rng.integers(0, 40), 170 + rng.integers(0, 50), 80), 3.5, out=(40, 110, 60))


def bush(c, x, y, s=1.0, col=(110, 196, 104)):
    with Xf(c, x, y, 0, s):
        outlined_union(c, [circle(-50, -30, 40), circle(0, -50, 52), circle(52, -30, 40), oval(0, -18, 90, 28)], col, 2.5, out=SOFT)


def house(c, x, y, s=1.0):
    with Xf(c, x, y, 0, s):
        shape(c, rrect(-70, -110, 70, 0, 6), (255, 248, 236), 5)
        shape(c, poly([(-92, -104), (0, -182), (92, -104)]), (236, 96, 110), 5)
        shape(c, rrect(-22, -64, 18, 0, 6), (176, 120, 90), 4)
        shape(c, rrect(28, -82, 58, -52, 4), (160, 220, 250), 4)
        shape(c, rrect(-60, -82, -30, -52, 4), (160, 220, 250), 4)
        shape(c, rrect(36, -176, 58, -138, 3), (200, 120, 110), 4)


def fence(c, y=1188, x0=0, x1=W, gate=None):
    rail = (226, 190, 140)
    for yy in (y - 52, y - 18):
        shape(c, rrect(x0, yy - 8, x1, yy + 8, 4), rail, 3.5, out=(120, 84, 60))
    x = x0 + 10
    while x < x1:
        if gate is None or not (gate[0] < x < gate[1]):
            shape(c, poly([(x - 16, y + 8), (x - 16, y - 78), (x, y - 96), (x + 16, y - 78), (x + 16, y + 8)]), (244, 214, 168), 3.5, out=(120, 84, 60))
        x += 52


def dog_park_sign(c, x, y, s=1.0):
    with Xf(c, x, y, 0, s):
        shape(c, rrect(-10, -170, 10, 0, 4), (176, 120, 80), 4)
        shape(c, rrect(-120, -250, 120, -150, 18), (255, 236, 196), 5, out=(120, 84, 60))
        text(c, "DOG PARK", 0, -186, 52, (110, 70, 160), WHITE, 0, name="LilitaOne-Regular.ttf")
        paw(c, -86, -222, 0.5, (236, 96, 130))
        paw(c, 86, -222, 0.5, (236, 96, 130))


def paw(c, x, y, s=1.0, col=(255, 255, 255)):
    with Xf(c, x, y, 0, s):
        c.drawPath(oval(0, 8, 22, 18), fill_paint(col))
        for ox, oy in ((-22, -16), (-8, -28), (8, -28), (22, -16)):
            c.drawPath(oval(ox, oy, 8, 10), fill_paint(col))


def river(c, t, y=1300, width=74):
    top, bot = [], []
    for x in range(-40, W + 81, 40):
        cy = y + 30 * math.sin(x / 190) + 10 * math.sin(x / 70 + 1)
        top.append((x, cy - width / 2))
        bot.append((x, cy + width / 2))
    p = smooth(top + bot[::-1], k=0.8)
    shape(c, p, (92, 206, 226), 4, out=(60, 140, 170))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    for i in range(9):
        x = (i * 140 + t * 60) % (W + 200) - 100
        cy = y + 30 * math.sin(x / 190) + 10 * math.sin(x / 70 + 1)
        q = skia.Path()
        q.moveTo(x - 40, cy - 8 + (i % 3) * 10)
        q.quadTo(x, cy - 16 + (i % 3) * 10, x + 40, cy - 8 + (i % 3) * 10)
        c.drawPath(q, stroke_paint((200, 244, 250), 5))
    c.restore()


def rainbow(c, cx=540, cy=1240, r=620, band=46, a=1.0):
    cols = [(255, 110, 120), (255, 170, 90), (255, 226, 110), (130, 220, 120), (110, 190, 255), (180, 140, 240)]
    with Fade(c, a):
        for i, col in enumerate(cols):
            rr = r - i * band
            p = arc_path(cx, cy, rr, rr, 180, 360, n=40)
            c.drawPath(p, stroke_paint(col, band + 1, cap=skia.Paint.kButt_Cap))
        c.drawPath(arc_path(cx, cy, r + band / 2, r + band / 2, 180, 360, 40), stroke_paint(WHITE, 4, 0.7))


def sunbeam(c, x, top, bottom, w0=120, w1=420, a=0.35):
    g = vgrad(top, bottom, (255, 246, 180), (255, 236, 150))
    p = poly([(x - w0 / 2, top), (x + w0 / 2, top), (x + w1 / 2, bottom), (x - w1 / 2, bottom)])
    c.drawPath(p, fill_paint(WHITE, a, shader=g, blur=18))


# -------------------------------------------------------------- weather
def rain(c, t, amount=1.0, seed=3):
    rng = np.random.default_rng(seed)
    n = int(150 * amount)
    xs, ys, sp = rng.uniform(-100, W + 100, n), rng.uniform(0, H, n), rng.uniform(1300, 1700, n)
    for x, y0, v in zip(xs, ys, sp):
        y = (y0 + v * t) % (H + 100) - 50
        xx = x - 0.25 * (y - y0)
        p = skia.Path()
        p.moveTo(xx, y)
        p.lineTo(xx - 10, y + 44)
        c.drawPath(p, stroke_paint((210, 230, 255), 4, 0.85))


def puddle_splash(c, x, y, t, period=0.6, s=1.0):
    k = (t % period) / period
    with Fade(c, 1 - k):
        c.drawPath(oval(x, y, 40 * s * (0.4 + k), 10 * s * (0.4 + k)), stroke_paint((200, 230, 255), 4))


def snow(c, t, amount=1.0, seed=4):
    rng = np.random.default_rng(seed)
    n = int(120 * amount)
    xs, ys, sp, rs = rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(90, 180, n), rng.uniform(5, 11, n)
    for i, (x0, y0, v, r) in enumerate(zip(xs, ys, sp, rs)):
        y = (y0 + v * t) % (H + 40) - 20
        x = x0 + 30 * math.sin(t * 1.3 + i)
        c.drawPath(circle(x, y, r), fill_paint(WHITE, 0.95))


def snow_ground(c, top=1260):
    p = skia.Path()
    p.moveTo(0, H)
    for x in range(0, W + 41, 40):
        p.lineTo(x, top - 18 - 10 * math.sin(x / 120))
    p.lineTo(W, H)
    p.close()
    shape(c, p, (246, 250, 255), 4, out=(170, 190, 220))


def umbrella(c, x, y, s=1.0, col=(255, 120, 170), tilt=0.0):
    """y is the handle grip; canopy above."""
    with Xf(c, x, y, tilt, s):
        p = skia.Path()
        p.moveTo(0, 0)
        p.lineTo(0, -230)
        c.drawPath(p, stroke_paint(OUT, 10))
        c.drawPath(p, stroke_paint((240, 240, 250), 5))
        hook = skia.Path()
        hook.moveTo(0, 0)
        hook.quadTo(0, 22, -18, 18)
        c.drawPath(hook, stroke_paint(OUT, 9))
        canopy = skia.Path()
        canopy.moveTo(-210, -200)
        canopy.cubicTo(-200, -330, 200, -330, 210, -200)
        for i in range(5):
            x0 = 210 - i * 84
            canopy.quadTo(x0 - 42, -230, x0 - 84, -200)
        canopy.close()
        shape(c, canopy, col, 6)
        for k in (-126, -42, 42, 126):
            q = skia.Path()
            q.moveTo(0, -300)
            q.quadTo(k * 0.6, -280, k, -205)
            c.drawPath(q, stroke_paint(OUT, 3.5, 0.6))
        shape(c, circle(0, -306, 9), (255, 220, 90), 3)


# -------------------------------------------------------------- effects
def heart(c, x, y, s=1.0, col=(255, 92, 141), a=1.0, rot=0.0):
    with Fade(c, a), Xf(c, x, y, rot, s):
        shape(c, heart_path(0, 0, 30), col, 5)
        c.drawPath(oval(-12, -10, 7, 5), fill_paint(WHITE, 0.7))


def sparkle(c, x, y, r=18, col=(255, 236, 120), a=1.0, rot=0.0):
    with Fade(c, a), Xf(c, x, y, rot):
        c.drawPath(sparkle_path(0, 0, r * 1.25), fill_paint(WHITE, 0.5, blur=4))
        shape(c, sparkle_path(0, 0, r), col, 3, out=(230, 160, 60))


def puff(c, x, y, r=60, a=1.0):
    with Fade(c, a):
        parts = [circle(x + r * 0.6 * math.cos(k), y + r * 0.45 * math.sin(k), r * 0.55) for k in np.linspace(0, 2 * math.pi, 7)[:-1]]
        parts.append(circle(x, y, r * 0.7))
        outlined_union(c, parts, WHITE, 3, out=(170, 180, 205))


def confetti(c, x, y, k, col, rot, s=1.0, a=1.0):
    with Fade(c, a), Xf(c, x, y, rot, s):
        if k % 2:
            shape(c, star_path(0, 0, 14, 6), col, 2.5)
        else:
            shape(c, rrect(-6, -11, 6, 11, 3), col, 2.5)


def lightbulb(c, x, y, s=1.0, glow=1.0, a=1.0):
    with Fade(c, a), Xf(c, x, y, 0, s):
        if glow > 0:
            g = skia.GradientShader.MakeRadial(skia.Point(0, -20), 150, [color((255, 246, 150), 0.9 * glow), color((255, 240, 150), 0)])
            c.drawPath(circle(0, -20, 150), fill_paint(WHITE, 1, shader=g))
            for i in range(8):
                with Xf(c, 0, -20, i * 45):
                    q = skia.Path()
                    q.moveTo(0, -78)
                    q.lineTo(0, -108)
                    c.drawPath(q, stroke_paint((255, 190, 60), 7 * glow))
        shape(c, smooth([(-38, -40), (-30, -78), (0, -92), (30, -78), (38, -40), (20, -8), (20, 12), (-20, 12), (-20, -8)], k=0.8),
              (255, 238, 120), 5)
        shape(c, rrect(-20, 12, 20, 40, 7), (180, 186, 200), 4)
        q = skia.Path()
        q.moveTo(-10, -30)
        q.quadTo(0, -50, 10, -30)
        c.drawPath(q, stroke_paint((255, 170, 60), 4))


def thought_bubble(c, x, y, w, h, tail, a=1.0):
    """Cloud bubble centred at (x, y); little puffs lead to `tail` (a head)."""
    with Fade(c, a):
        parts = []
        n = 10
        for i in range(n):
            ang = 2 * math.pi * i / n
            parts.append(circle(x + (w / 2 - 34) * math.cos(ang), y + (h / 2 - 30) * math.sin(ang), 46))
        parts.append(oval(x, y, w / 2 - 10, h / 2 - 8))
        outlined_union(c, parts, WHITE, 4)
        tx, ty = tail
        for k, r in ((0.55, 18), (0.78, 12), (0.93, 8)):
            px, py = x + (tx - x) * k, (y + h / 2) + (ty - (y + h / 2)) * k
            shape(c, circle(px, py, r), WHITE, 4)


def question_mark(c, x, y, s=1.0, a=1.0, rot=0.0):
    with Fade(c, a), Xf(c, x, y, rot, s):
        text(c, "?", 0, 0, 92, (255, 214, 80), OUT, 9)


def music_note(c, x, y, s=1.0, a=1.0, col=(150, 110, 230)):
    with Fade(c, a), Xf(c, x, y, 0, s):
        shape(c, oval(-10, 0, 14, 10), col, 3.5)
        p = skia.Path()
        p.moveTo(2, 0)
        p.lineTo(2, -50)
        p.quadTo(22, -40, 26, -24)
        c.drawPath(p, stroke_paint(OUT, 5))


def speed_lines(c, x, y, direction=-1, n=4, length=120, a=1.0):
    for i in range(n):
        yy = y - 30 + i * 20
        q = skia.Path()
        q.moveTo(x, yy)
        q.lineTo(x + direction * (length - 20 * (i % 2)), yy)
        c.drawPath(q, stroke_paint(WHITE, 6, a))


def burst(c, x, y, r, label, s=1.0, a=1.0, rot=0.0):
    with Fade(c, a), Xf(c, x, y, rot, s):
        for rad, col in ((r * 1.08, (255, 120, 40)), (r * 0.96, (255, 216, 64))):
            pts = []
            for i in range(28):
                rr = rad * (1.0 if i % 2 == 0 else 0.72)
                ang = i * math.pi / 14
                pts.append((rr * math.cos(ang), rr * math.sin(ang)))
            shape(c, poly(pts), col, 5)
        text(c, label, 0, r * 0.2, int(r * 0.6), WHITE, OUT, 12)


def name_tag(c, x, y, label, col, s=1.0, a=1.0, rot=0.0):
    f = font("LilitaOne-Regular.ttf", 46)
    tw = f.measureText(label)
    with Fade(c, a), Xf(c, x, y, rot, s):
        w2 = tw / 2 + 30
        shape(c, rrect(-w2, -34, w2, 34, 34), col, 5)
        c.drawPath(rrect(-w2 + 6, -28, w2 - 6, 28, 28), stroke_paint(WHITE, 4, 0.9))
        text(c, label, 0, 16, 46, WHITE, OUT, 6, name="LilitaOne-Regular.ttf")


def photo_frame(c, x0, y0, x1, y1, a=1.0):
    """Polaroid-style border around a rectangle (drawn on top of the scene)."""
    with Fade(c, a):
        outer = rrect(x0 - 26, y0 - 26, x1 + 26, y1 + 110, 10)
        inner = rrect(x0, y0, x1, y1, 4)
        frame = skia.Op(outer, inner, skia.PathOp.kDifference_PathOp)
        c.drawPath(outer, stroke_paint(OUT, 6))
        c.drawPath(frame, fill_paint((255, 252, 246)))
        c.drawPath(inner, stroke_paint((200, 190, 200), 3))


def vignette(c, amount, col=(30, 20, 50)):
    if amount <= 0:
        return
    g = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.55), H * 0.62,
                                       [color(col, 0), color(col, 0), color(col, 0.75 * amount)], [0.0, 0.55, 1.0])
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill_paint(WHITE, 1, shader=g))


def flash(c, amount, col=WHITE):
    if amount > 0:
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill_paint(col, min(1, amount)))


def ball(c, x, y, r=34, rot=0.0):
    with Xf(c, x, y, rot):
        shape(c, circle(0, 0, r), (240, 80, 90), 5)
        c.save()
        c.clipPath(circle(0, 0, r), doAntiAlias=True)
        c.drawPath(arc_path(0, 0, r * 1.6, r * 0.5, 0, 360), stroke_paint(WHITE, 7))
        c.restore()
        c.drawPath(circle(-r * 0.35, -r * 0.4, r * 0.18), fill_paint(WHITE, 0.7))
