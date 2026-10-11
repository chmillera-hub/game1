"""Backgrounds: the audience rows (seen from the stage) and the stage itself.

Static parts are pre-rendered once into large images in world coordinates;
dynamic parts (spotlight, silhouettes) are drawn per frame.
"""
import math
import skia
from gfx import (rgb, hx, mix, shade, fill, stroke, oval, rrect, poly, font,
                 lin_grad, rad_grad, hash01)
from rig import DESIGNS

# x positions of the front row (audience world, seen from the stage)
ROW_X = {'doubt': -600, 'boredom': -300, 'me': 0, 'anger': 300, 'stranger': 600}
# same people seen from behind in the stage world (mirrored)
BACK_X = {'stranger': -660, 'anger': -330, 'me': 0, 'boredom': 330, 'doubt': 660}
BACK_Y = 700

AUD_BOUNDS = (-1400, -1800, 1400, 1500)
STAGE_BOUNDS = (-1000, -1800, 1000, 1500)


def _surface(bounds):
    l, t, r, b = bounds
    s = skia.Surface(int(r - l), int(b - t))
    c = s.getCanvas()
    c.translate(-l, -t)
    return s, c


def _seat(cv, x, floor_y, sc, col=(128, 22, 34), dark=0.0):
    cv.save()
    cv.translate(x, floor_y)
    cv.scale(sc, sc)
    c = mix(col, (10, 5, 8), dark)
    back = rrect(-112, -372, 112, -150, 46)
    cv.drawPath(back, fill(c))
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad((0, -372), (0, -150), [((255, 200, 170), 0.18 * (1 - dark)), ((0, 0, 0), 0.35)]))
    cv.drawPath(back, g)
    for k in (-1, 1):
        cv.drawLine(k * 40, -350, k * 40, -170, stroke(shade(c, 0.75), 3))
    cv.drawPath(back, stroke(mix((50, 8, 14), (5, 2, 4), dark), 4))
    # cushion
    cush = rrect(-108, -165, 108, -112, 22)
    cv.drawPath(cush, fill(shade(c, 0.85)))
    cv.drawPath(cush, stroke(mix((50, 8, 14), (5, 2, 4), dark), 3))
    cv.restore()


def _armrest(cv, x, floor_y, sc, dark=0.0):
    cv.save()
    cv.translate(x, floor_y)
    cv.scale(sc, sc)
    c = mix((60, 36, 30), (8, 5, 6), dark)
    cv.drawPath(rrect(-17, -215, 17, -40, 8), fill(c))
    cv.drawPath(rrect(-22, -222, 22, -196, 9), fill(shade(c, 1.15)))
    cv.drawPath(oval(0, -214, 11, 5), fill((15, 10, 10)))
    cv.restore()


def _silhouette_head(cv, x, y, sc, kind, col):
    cv.save()
    cv.translate(x, y)
    cv.scale(sc, sc)
    cv.drawPath(rrect(-70, -150, 70, 30, 40), fill(col))
    cv.drawPath(oval(0, -225, 58, 66), fill(col))
    if kind == 1:
        cv.drawPath(oval(0, -300, 26, 22), fill(col))        # bun
    elif kind == 2:
        cv.drawPath(oval(0, -262, 64, 34), fill(col))        # cap
        cv.drawPath(rrect(-10, -268, 95, -250, 9), fill(col))
    elif kind == 3:
        cv.drawPath(oval(0, -205, 78, 82), fill(col))        # big hair
    cv.restore()


def build_audience_bg():
    s, cv = _surface(AUD_BOUNDS)
    l, t, r, b = AUD_BOUNDS
    # wall
    wall = skia.Paint(AntiAlias=True)
    wall.setShader(lin_grad((0, t), (0, -300), [((12, 6, 12), 1), ((34, 14, 24), 1)]))
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, b), wall)
    for i in range(int(l), int(r), 140):
        cv.drawLine(i, t, i, -700, stroke((15, 6, 12), 4, 0.6))
    # sconces
    for sx in (-900, -300, 300, 900):
        cv.drawPath(oval(sx, -1250, 120, 120), fill((255, 170, 90), 0.18, blur=40))
        cv.drawPath(poly([(sx - 24, -1270), (sx + 24, -1270), (sx + 14, -1225), (sx - 14, -1225)]), fill((240, 170, 90)))
        cv.drawPath(oval(sx, -1248, 46, 30), fill((255, 200, 120), 0.35, blur=12))
    # exit sign
    cv.drawPath(rrect(-1250, -1520, -1080, -1440, 8), fill((20, 120, 60)))
    cv.drawPath(rrect(-1250, -1520, -1080, -1440, 8), fill((60, 255, 140), 0.25, blur=14))
    f = font('InterDisplay-Black', 52)
    cv.drawString('EXIT', -1232, -1460, f, fill((220, 255, 230)))
    # back rows of silhouettes (raked seating)
    rows = [(-520, 0.58, 0.93), (-270, 0.78, 0.82)]
    for ri, (fy, sc, dark) in enumerate(rows):
        step = 250 * sc
        x = l + (step / 2 if ri % 2 else 0)
        i = 0
        while x < r + step:
            _seat(cv, x, fy, sc, dark=dark)
            if hash01(i, ri, 4) > 0.22:
                col = mix((40, 22, 32), (6, 3, 6), dark)
                _silhouette_head(cv, x, fy - 150 * sc, sc * 0.95, int(hash01(i, ri) * 4), col)
            x += step
            i += 1
        # light falloff band
        g = skia.Paint(AntiAlias=True)
        g.setShader(lin_grad((0, fy - 420 * sc), (0, fy), [((0, 0, 0), 0.0), ((0, 0, 0), 0.25)]))
        cv.drawRect(skia.Rect.MakeLTRB(l, fy - 420 * sc, r, fy), g)
    # floor / carpet
    cv.drawRect(skia.Rect.MakeLTRB(l, -60, r, b), fill((58, 18, 28)))
    for i in range(-30, 30):
        for j in range(0, 12):
            xx, yy = i * 90 + (45 if j % 2 else 0), j * 80
            cv.drawPath(poly([(xx, yy - 26), (xx + 26, yy), (xx, yy + 26), (xx - 26, yy)]),
                        fill((90, 30, 40), 0.35))
    # front-row seats & armrests
    for name, x in ROW_X.items():
        _seat(cv, x, 0, 1.0)
    for x in list(ROW_X.values()) + [900, -900]:
        _armrest(cv, x - 150, 0, 1.0)
    for x in (-900, 900):
        _seat(cv, x, 0, 1.0)
    for x in (1200, -1200):
        _seat(cv, x, 0, 1.0)
    # warm stage light on the front row
    g = skia.Paint(AntiAlias=True)
    g.setShader(rad_grad((0, -200), 1100, [((255, 190, 140), 0.10), ((255, 190, 140), 0.0)]))
    g.setBlendMode(skia.BlendMode.kPlus)
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, b), g)
    # aisle step lights
    for x in range(int(l) + 60, int(r), 300):
        cv.drawPath(oval(x, 60, 26, 9), fill((255, 190, 90), 0.35, blur=10))
        cv.drawPath(oval(x, 60, 7, 4), fill((255, 220, 150)))
    img = s.makeImageSnapshot()
    return img


def _brick_wall(cv, l, t, r, b):
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, b), fill((40, 20, 18)))
    bh, bw = 46, 120
    j = 0
    y = t
    while y < b:
        off = (bw / 2) if j % 2 else 0
        x = l - off
        i = 0
        while x < r:
            v = hash01(i, j, 7)
            c = mix((104, 48, 38), (140, 68, 52), v)
            c = mix(c, (70, 34, 30), hash01(i, j, 3) * 0.5)
            cv.drawPath(rrect(x + 3, y + 3, x + bw - 3, y + bh - 3, 4), fill(c))
            x += bw
            i += 1
        y += bh
        j += 1


def build_stage_bg():
    s, cv = _surface(STAGE_BOUNDS)
    l, t, r, b = STAGE_BOUNDS
    _brick_wall(cv, l, t, r, 0)
    # darken the top and edges of the wall
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad((0, t), (0, 0), [((0, 0, 0), 0.75), ((0, 0, 0), 0.15)]))
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, 0), g)
    # spotlight pool on the wall
    g = skia.Paint(AntiAlias=True)
    g.setShader(rad_grad((0, -330), 520, [((255, 230, 190), 0.55), ((255, 230, 190), 0.0)]))
    g.setBlendMode(skia.BlendMode.kPlus)
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, 0), g)
    # neon sign
    cx, cy = 0, -980
    f = font('InterDisplay-Black', 104)
    txt = 'COMEDY NIGHT'
    w = f.measureText(txt)
    cv.drawPath(rrect(-w / 2 - 40, cy - 120, w / 2 + 40, cy + 40, 20), fill((15, 8, 14), 0.8))
    for blur, a in ((26, 0.8), (10, 0.9)):
        p = fill((255, 70, 170), a, blur=blur)
        p.setBlendMode(skia.BlendMode.kPlus)
        cv.drawString(txt, -w / 2, cy, f, p)
    cv.drawString(txt, -w / 2, cy, f, fill((255, 200, 235)))
    f2 = font('InterDisplay-Bold', 46)
    t2 = '~ live stand-up ~'
    w2 = f2.measureText(t2)
    for blur, a in ((16, 0.9), (6, 0.9)):
        p = fill((80, 230, 255), a, blur=blur)
        p.setBlendMode(skia.BlendMode.kPlus)
        cv.drawString(t2, -w2 / 2, cy + 90, f2, p)
    cv.drawString(t2, -w2 / 2, cy + 90, f2, fill((210, 250, 255)))
    # stool with a glass of water
    sx = 230
    cv.drawLine(sx - 40, -140, sx - 55, 0, stroke((40, 25, 20), 12))
    cv.drawLine(sx + 40, -140, sx + 55, 0, stroke((40, 25, 20), 12))
    cv.drawLine(sx - 48, -70, sx + 48, -70, stroke((40, 25, 20), 9))
    cv.drawPath(rrect(sx - 62, -160, sx + 62, -138, 10), fill((70, 40, 30)))
    cv.drawPath(rrect(sx - 16, -205, sx + 16, -160, 4), fill((200, 230, 255), 0.55))
    cv.drawPath(rrect(sx - 16, -205, sx + 16, -160, 4), stroke((230, 240, 255), 2.5))
    # stage floor (planks)
    cv.drawRect(skia.Rect.MakeLTRB(l, 0, r, 170), fill((112, 70, 40)))
    for k in range(0, 170, 26):
        cv.drawLine(l, k, r, k, stroke((80, 48, 28), 3))
    for i in range(-20, 20):
        x0 = i * 160 + (k % 2) * 40
        for j in range(0, 7):
            xx = i * 210 + (j % 3) * 70
            cv.drawLine(xx, j * 26, xx, j * 26 + 26, stroke((80, 48, 28), 2.5))
    g = skia.Paint(AntiAlias=True)
    g.setShader(rad_grad((0, 40), 520, [((255, 220, 170), 0.35), ((255, 220, 170), 0.0)]))
    g.setBlendMode(skia.BlendMode.kPlus)
    cv.drawRect(skia.Rect.MakeLTRB(l, 0, r, 170), g)
    # stage front face + footlights
    cv.drawRect(skia.Rect.MakeLTRB(l, 170, r, 260), fill((36, 20, 16)))
    cv.drawLine(l, 170, r, 170, stroke((150, 100, 60), 5))
    for x in range(int(l) + 50, int(r), 140):
        cv.drawPath(oval(x, 175, 40, 18), fill((255, 200, 120), 0.4, blur=14))
        cv.drawPath(rrect(x - 16, 168, x + 16, 182, 5), fill((255, 230, 170)))
    # pit
    cv.drawRect(skia.Rect.MakeLTRB(l, 260, r, b), fill((14, 8, 12)))
    # curtains
    for sd in (-1, 1):
        x0 = sd * 440
        x1 = sd * 1000
        lo, hi = min(x0, x1), max(x0, x1)
        cv.drawRect(skia.Rect.MakeLTRB(lo, t, hi, 175), fill((120, 14, 24)))
        n = 9
        for i in range(n):
            xa = lo + (hi - lo) * i / n
            xb = lo + (hi - lo) * (i + 1) / n
            gp = skia.Paint(AntiAlias=True)
            gp.setShader(lin_grad((xa, 0), (xb, 0), [((40, 0, 6), 0.55), ((255, 120, 120), 0.12), ((40, 0, 6), 0.55)]))
            cv.drawRect(skia.Rect.MakeLTRB(xa, t, xb, 175), gp)
        edge = x0
        cv.drawLine(edge, t, edge, 175, stroke((60, 5, 12), 8))
    # valance
    cv.drawRect(skia.Rect.MakeLTRB(l, t, r, -1420), fill((120, 14, 24)))
    for i in range(-10, 11):
        xx = i * 110
        cv.drawPath(oval(xx, -1420, 58, 40), fill((120, 14, 24)))
        cv.drawPath(oval(xx, -1420, 58, 40), stroke((70, 6, 14), 3))
    cv.drawLine(l, -1460, r, -1460, stroke((230, 180, 70), 10))
    img = s.makeImageSnapshot()
    return img


def draw_spot_cone(cv, x, top_y, floor_y, width, alpha, t):
    flick = 1 + 0.03 * math.sin(t * 13) + 0.02 * math.sin(t * 7.3)
    p = poly([(x - 60, top_y), (x + 60, top_y), (x + width, floor_y), (x - width, floor_y)])
    g = skia.Paint(AntiAlias=True)
    g.setShader(lin_grad((0, top_y), (0, floor_y), [((255, 245, 220), 0.0), ((255, 245, 220), 0.22 * alpha * flick)]))
    g.setBlendMode(skia.BlendMode.kPlus)
    cv.drawPath(p, g)
    g2 = skia.Paint(AntiAlias=True)
    g2.setShader(rad_grad((x, floor_y), width * 1.1, [((255, 240, 200), 0.35 * alpha), ((255, 240, 200), 0.0)]))
    g2.setBlendMode(skia.BlendMode.kPlus)
    cv.drawPath(oval(x, floor_y, width * 1.1, 46), g2)


def draw_back_silhouette(cv, name, x, y, sc, st, t):
    """A character seen from behind (stage world foreground)."""
    d = DESIGNS[name]
    col = (16, 10, 16)
    rim = (255, 200, 150)
    stand = st.get('stand', 0.0)
    rise = stand * 120 - st.get('sink', 0)
    cv.save()
    cv.translate(x + st.get('back_dx', 0.0), y - rise)
    cv.scale(sc, sc)
    cv.rotate(-st.get('lean', 0.0))
    a, b = d['head_w'], d['head_h']
    sw = d['sh_w'] / 2
    body = rrect(-sw, -200, sw, 200, 50)
    cv.drawPath(body, fill(col))
    hy = -200 - 10 - b * 0.9
    cv.save()
    cv.translate(0, hy)
    cv.rotate(-st.get('head_tilt', 0.0))
    if name == 'me':
        cv.drawPath(oval(0, 10, a * 1.15, b * 1.05), fill(col))
    elif name == 'anger':
        cv.drawPath(rrect(-a, -b * 1.2, a, b, 40), fill(col))
    elif name == 'doubt':
        cv.drawPath(oval(0, 0, a, b), fill(col))
        cv.drawPath(oval(0, -b * 1.12, a * 0.42, b * 0.32), fill(col))
    elif name == 'boredom':
        cv.drawPath(oval(0, 0, a, b), fill(col))
        cv.drawPath(oval(0, -b * 1.17, 16, 14), fill(col))
        cv.drawPath(oval(0, -b * 0.6, a * 1.06, b * 0.7), fill(col))
    else:
        cv.drawPath(oval(0, 0, a, b), fill(col))
        cv.drawPath(oval(0, -b * 0.55, a * 1.05, b * 0.62), fill(col))
    # rim light on top of head
    rp = skia.Path()
    rp.addArc(skia.Rect.MakeLTRB(-a * 0.95, -b * 1.15, a * 0.95, b * 0.9), 200, 140)
    cv.drawPath(rp, stroke(rim, 7, 0.55))
    cv.restore()
    # arms up?
    for side in (-1, 1):
        up = st.get('arms_up', 0.0)
        if up > 0.05:
            ex = side * (sw + 30)
            cv.drawLine(side * (sw - 20), -170, ex + side * 30 * up, -170 - 240 * up, stroke(col, 50))
            cv.drawPath(oval(ex + side * 30 * up, -170 - 260 * up, 30, 30), fill(col))
    if st.get('popcorn_up', 0.0) > 0.05:
        u = st['popcorn_up']
        cv.drawPath(poly([(sw - 10, -230 - 60 * u), (sw + 70, -230 - 60 * u), (sw + 55, -140 - 60 * u), (sw + 5, -140 - 60 * u)]),
                    fill((28, 18, 22)))
    cv.restore()
