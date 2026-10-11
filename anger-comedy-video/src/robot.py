"""The stand-up comedian robot ('Gemini bot' from the story).

A generic boxy robot with an LED screen face, bow tie and microphone.  It
intentionally uses no real product logo or branding.
"""
import math
import skia
from gfx import rgb, fill, stroke, oval, rrect, poly, font, shade, lin_grad, noise1

BOT_DEFAULTS = dict(
    x=0.0, y=0.0, s=1.0, lean=0.0, bob=0.0, hop=0.0,
    la1=10.0, la2=30.0, ra1=20.0, ra2=100.0,     # right arm holds the mic near the face
    look_x=0.0, look_y=0.0, eye_open=1.0, smile=0.6, talk=0.0, blink=0.0,
    glow=1.0, screen_flash=0.0,
    face='normal', lh='open', text='', mic='hand',
)
BOT_DISCRETE = {'face', 'lh', 'text', 'mic'}

CASE = (226, 232, 238)
CASE_D = (150, 160, 175)
OUT = (40, 48, 64)
LED = (110, 240, 255)
LED2 = (255, 140, 220)


def _glow_paint(c, a=1.0, w=None, blur=6):
    if w is None:
        p = fill(c, a, blur=blur)
    else:
        p = stroke(c, w, a, blur=blur)
    p.setBlendMode(skia.BlendMode.kPlus)
    return p


def _led_eye(cv, kind, cx, cy, st, side, t):
    op = max(0.08, st['eye_open'] * (1 - st['blink']))
    lx, ly = st['look_x'] * 8, st['look_y'] * 6
    c = LED
    paths = []
    if kind in ('normal', 'smug', 'expect') or (kind == 'wink' and side < 0):
        if kind == 'expect':
            r = 20
            paths.append(('f', oval(cx + lx, cy + ly, r, r * op)))
        else:
            hh = 26 * op * (0.55 if kind == 'smug' else 1)
            paths.append(('f', rrect(cx - 11 + lx, cy - hh + ly + (8 if kind == 'smug' else 0),
                                     cx + 11 + lx, cy + hh + ly, 10)))
    elif kind in ('happy', 'wink'):
        p = skia.Path()
        p.moveTo(cx - 16, cy + 8)
        p.quadTo(cx, cy - 22, cx + 16, cy + 8)
        paths.append(('s', p))
    elif kind == 'star':
        pts = []
        sc = 1 + 0.12 * math.sin(t * 10)
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = (24 if i % 2 == 0 else 10) * sc
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        paths.append(('f', poly(pts)))
    elif kind == 'x':
        p = skia.Path()
        p.moveTo(cx - 13, cy - 13); p.lineTo(cx + 13, cy + 13)
        p.moveTo(cx + 13, cy - 13); p.lineTo(cx - 13, cy + 13)
        paths.append(('s', p))
    elif kind == 'heart':
        p = skia.Path()
        p.moveTo(cx, cy + 16)
        p.cubicTo(cx - 30, cy - 4, cx - 14, cy - 26, cx, cy - 10)
        p.cubicTo(cx + 14, cy - 26, cx + 30, cy - 4, cx, cy + 16)
        paths.append(('f', p))
        c = LED2
    for kind_, p in paths:
        if kind_ == 'f':
            cv.drawPath(p, _glow_paint(c, 0.8 * st['glow'], blur=8))
            cv.drawPath(p, fill(c))
        else:
            cv.drawPath(p, _glow_paint(c, 0.8 * st['glow'], 9, blur=8))
            cv.drawPath(p, stroke(c, 7))


def draw_mic(cv, x, y, ang=0.0, sc=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang)
    cv.scale(sc, sc)
    cv.drawPath(rrect(-7, 0, 7, 46, 6), fill((30, 30, 36)))
    cv.drawPath(rrect(-7, 0, 7, 46, 6), stroke((10, 10, 14), 2))
    cv.drawPath(oval(0, -6, 14, 15), fill((150, 155, 165)))
    for k in range(-2, 3):
        cv.drawLine(-12, -6 + k * 5, 12, -6 + k * 5, stroke((90, 95, 105), 1.4))
    cv.drawPath(oval(0, -6, 14, 15), stroke((40, 40, 50), 2))
    cv.restore()


def draw_robot(cv, st, t):
    cv.save()
    cv.translate(st['x'], st['y'] - st['hop'])
    cv.scale(st['s'], st['s'])
    bob = st['bob'] + 3 * math.sin(t * 2 * math.pi / 1.6)
    # shadow
    cv.drawPath(oval(0, 4, 95, 14), fill((0, 0, 0), 0.35, blur=8))
    # legs
    for sd in (-1, 1):
        cv.drawLine(sd * 30, -110 + bob * 0.5, sd * 34, -14, stroke(OUT, 26))
        cv.drawLine(sd * 30, -110 + bob * 0.5, sd * 34, -14, stroke(CASE_D, 18))
        cv.drawPath(oval(sd * 32, -62 + bob * 0.25, 13, 13), fill((90, 98, 112)))
        cv.drawPath(rrect(sd * 34 - 30, -20, sd * 34 + 30, 2, 10), fill((70, 76, 90)))
        cv.drawPath(rrect(sd * 34 - 30, -20, sd * 34 + 30, 2, 10), stroke(OUT, 3))
    cv.save()
    cv.translate(0, -110 + bob)
    cv.rotate(st['lean'])
    # torso
    body = rrect(-78, -170, 78, 0, 34)
    cv.drawPath(body, fill(CASE))
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(lin_grad((-78, 0), (78, 0), [((255, 255, 255), 0.25), ((0, 0, 0), 0.18)]))
    cv.save(); cv.clipPath(body, doAntiAlias=True); cv.drawRect(skia.Rect.MakeLTRB(-90, -180, 90, 10), sh); cv.restore()
    cv.drawPath(body, stroke(OUT, 4))
    # chest panel
    cv.drawPath(rrect(-50, -128, 50, -40, 14), fill((32, 40, 56)))
    for i in range(4):
        on = (math.sin(t * 5 + i * 1.7) > 0)
        cv.drawPath(oval(-30 + i * 20, -110, 5.5, 5.5), fill((90, 255, 160) if on else (40, 90, 70)))
    cv.drawPath(oval(0, -72, 17, 17), fill((230, 50, 60)))      # the rimshot button
    cv.drawPath(oval(-5, -77, 6, 4), fill((255, 255, 255), 0.5))
    cv.drawPath(oval(0, -72, 17, 17), stroke((90, 10, 20), 3))
    # bow tie
    bt = poly([(-36, -186), (0, -172), (36, -186), (36, -150), (0, -164), (-36, -150)])
    cv.drawPath(bt, fill((150, 40, 200)))
    cv.drawPath(bt, stroke((50, 10, 70), 3))
    cv.drawPath(rrect(-10, -178, 10, -158, 5), fill((120, 25, 170)))
    # neck
    cv.drawPath(rrect(-20, -200, 20, -168, 6), fill((120, 128, 140)))
    # head
    cv.save()
    cv.translate(0, -290)
    head = rrect(-104, -82, 104, 82, 36)
    cv.drawPath(head, fill(CASE))
    cv.save(); cv.clipPath(head, doAntiAlias=True)
    sh2 = skia.Paint(AntiAlias=True)
    sh2.setShader(lin_grad((0, -82), (0, 82), [((255, 255, 255), 0.3), ((0, 0, 0), 0.15)]))
    cv.drawRect(skia.Rect.MakeLTRB(-110, -90, 110, 90), sh2)
    cv.restore()
    cv.drawPath(head, stroke(OUT, 4))
    # ear bolts
    for sd in (-1, 1):
        cv.drawPath(rrect(sd * 104 - 10, -26, sd * 104 + 10, 26, 7), fill(CASE_D))
        cv.drawPath(rrect(sd * 104 - 10, -26, sd * 104 + 10, 26, 7), stroke(OUT, 3))
    # antennae (twins)
    for sd, col in ((-1, LED), (1, LED2)):
        cv.drawLine(sd * 40, -82, sd * 58, -132, stroke(OUT, 5))
        pulse = 0.6 + 0.4 * math.sin(t * 6 + sd)
        cv.drawPath(oval(sd * 58, -136, 11, 11), fill(col))
        cv.drawPath(oval(sd * 58, -136, 16, 16), _glow_paint(col, 0.6 * pulse, blur=10))
    # screen
    scr = rrect(-84, -62, 84, 62, 24)
    cv.drawPath(scr, fill((10, 22, 36)))
    cv.save()
    cv.clipPath(scr, doAntiAlias=True)
    for yy in range(-60, 62, 6):
        cv.drawLine(-84, yy, 84, yy, stroke((255, 255, 255), 1, 0.03))
    if st['screen_flash'] > 0:
        cv.drawRect(skia.Rect.MakeLTRB(-90, -70, 90, 70), fill(LED, 0.35 * st['screen_flash']))
    if st['text']:
        f = font('InterDisplay-Black', 34)
        w = f.measureText(st['text'])
        jitter = math.sin(t * 20) * 2
        cv.drawString(st['text'], -w / 2, 12 + jitter, f, _glow_paint(LED, 0.9, blur=6))
        cv.drawString(st['text'], -w / 2, 12 + jitter, f, fill(LED))
    else:
        face = st['face']
        for sd in (-1, 1):
            _led_eye(cv, face if not (face == 'wink' and sd > 0) else 'happy', sd * 38, -14, st, sd, t)
        # mouth
        talk = st['talk']
        sm = st['smile']
        mw = 46
        if talk > 0.06 or face == 'expect':
            hh = 6 + talk * 26 if face != 'expect' else 9
            if face == 'expect':
                p = oval(0, 30, 9, hh)
            else:
                p = skia.Path()
                p.moveTo(-mw / 2, 26 - sm * 6)
                p.quadTo(0, 26 + sm * 8 + hh * 1.6, mw / 2, 26 - sm * 6)
                p.quadTo(0, 26 - hh * 0.3, -mw / 2, 26 - sm * 6)
            cv.drawPath(p, _glow_paint(LED, 0.7, blur=8))
            cv.drawPath(p, fill(LED))
        else:
            p = skia.Path()
            p.moveTo(-mw / 2, 26 - sm * 8)
            p.quadTo(0, 26 + sm * 18, mw / 2, 26 - sm * 8)
            cv.drawPath(p, _glow_paint(LED, 0.7, 8, blur=8))
            cv.drawPath(p, stroke(LED, 6))
    cv.restore()
    cv.drawPath(scr, stroke((60, 70, 90), 4))
    cv.drawPath(oval(-60, -46, 20, 7), fill((255, 255, 255), 0.10))
    cv.restore()   # head
    # arms
    for side in (-1, 1):
        a1 = st['la1'] if side < 0 else st['ra1']
        a2 = st['la2'] if side < 0 else st['ra2']
        sx, sy = side * 84, -150
        r1 = math.radians(a1)
        ex, ey = sx + side * math.sin(r1) * 70, sy + math.cos(r1) * 70
        r2 = math.radians(a1 - a2)
        hx, hy = ex + side * math.sin(r2) * 66, ey + math.cos(r2) * 66
        for (x0, y0, x1, y1) in ((sx, sy, ex, ey), (ex, ey, hx, hy)):
            cv.drawLine(x0, y0, x1, y1, stroke(OUT, 22))
            cv.drawLine(x0, y0, x1, y1, stroke(CASE_D, 15))
        cv.drawPath(oval(sx, sy, 15, 15), fill((110, 118, 132)))
        cv.drawPath(oval(ex, ey, 12, 12), fill((110, 118, 132)))
        ang = math.degrees(math.atan2(hy - ey, hx - ex))
        if side > 0 and st['mic'] == 'hand':
            draw_mic(cv, hx - 4, hy - 30, -10, 1.1)
            cv.drawPath(oval(hx, hy - 4, 17, 15), fill(CASE))
            cv.drawPath(oval(hx, hy - 4, 17, 15), stroke(OUT, 3))
            continue
        kind = st['lh'] if side < 0 else 'open'
        cv.save()
        cv.translate(hx, hy)
        if kind == 'point':      # finger gun
            cv.drawPath(rrect(-6, -40, 6, 0, 6), fill(CASE))
            cv.drawPath(rrect(-6, -40, 6, 0, 6), stroke(OUT, 3))
            cv.drawPath(rrect(0, -14, 34 * side, -2, 6) if side > 0 else rrect(34 * side, -14, 0, -2, 6), fill(CASE))
        elif kind == 'press':
            pass
        cv.drawPath(oval(0, 0, 17, 15), fill(CASE))
        cv.drawPath(oval(0, 0, 17, 15), stroke(OUT, 3))
        for k in (-1, 0, 1):
            cv.drawLine(k * 8, 8, k * 10, 22, stroke(OUT, 8))
            cv.drawLine(k * 8, 8, k * 10, 22, stroke(CASE, 4))
        cv.restore()
    cv.restore()   # torso
    cv.restore()


def robot_state(**kw):
    s = dict(BOT_DEFAULTS)
    s.update(kw)
    return s
