"""Drawing kit shared with the "Alice" short: helpers, Alice the ghost, Granny Simmer,
and pieces of the moonlit graveyard. (Extracted from alice_ghost_video/render.py.)"""
import math

import cairo
import numpy as np

W, H = 1080, 1920

SUB_FONT = 'Patrick Hand'

TITLE_FONT = 'Mountains of Christmas'

HAND_FONT = 'Schoolbell'

INK = (0.07, 0.06, 0.09)

GHOST = (0.95, 0.94, 0.91)

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.9):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def hexc(h, a=None):
    h = h.lstrip('#')
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else c + (a,)


def hash01(i, seed=0):
    x = math.sin(i * 127.1 + seed * 311.7) * 43758.5453
    return x - math.floor(x)


def vnoise(x, seed=0):
    i = math.floor(x)
    f = x - i
    a, b = hash01(i, seed), hash01(i + 1, seed)
    return lerp(a, b, f * f * (3 - 2 * f)) * 2 - 1


def spline(ctx, pts, closed=True, corners=None, tension=1.0):
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (0, 0) if corners and corners[i] else ((p2[0] - p0[0]) / 6 * tension, (p2[1] - p0[1]) / 6 * tension)
        c2 = (0, 0) if corners and corners[(i + 1) % n] else ((p3[0] - p1[0]) / 6 * tension, (p3[1] - p1[1]) / 6 * tension)
        ctx.curve_to(p1[0] + c1[0], p1[1] + c1[1], p2[0] - c2[0], p2[1] - c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def ellipse(ctx, x, y, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def radial(ctx, x, y, r, stops):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    return g


def linear(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        g.add_color_stop_rgba(off, *col)
    return g


def heart_path(ctx, x, y, s):
    ctx.move_to(x, y + 0.35 * s)
    ctx.curve_to(x - 0.05 * s, y + 0.25 * s, x - 0.55 * s, y + 0.05 * s, x - 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x - 0.45 * s, y - 0.5 * s, x - 0.05 * s, y - 0.5 * s, x, y - 0.22 * s)
    ctx.curve_to(x + 0.05 * s, y - 0.5 * s, x + 0.45 * s, y - 0.5 * s, x + 0.5 * s, y - 0.2 * s)
    ctx.curve_to(x + 0.55 * s, y + 0.05 * s, x + 0.05 * s, y + 0.25 * s, x, y + 0.35 * s)
    ctx.close_path()


def text_center(ctx, txt, x, y, font, size, fill, outline=None, ow=8, bold=False):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(txt)
    ctx.move_to(x - ext.x_advance / 2, y)
    ctx.text_path(txt)
    if outline:
        ctx.set_source_rgba(*outline)
        ctx.set_line_width(ow)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*fill)
    ctx.fill()


A_DEF = dict(brow_y=0, brow_tilt=0, brow_asym=0, lid_top=0.03, lid_tilt=0, lid_bot=0.05, eye_scale=1.0,
             happy=0, smile=0.3, open=0, mouth_w=1.0, squash=0, tilt=0, armL=65, armR=65,
             chestL=0, chestR=0, mouthL=0, mouthR=0, bob=1.0, blush=0.1, glint=1.0)

A_EMO = {
    'content': dict(smile=.45, lid_top=.06, lid_bot=.1, blush=.15),
    'dreamy': dict(brow_y=10, brow_tilt=5, lid_top=.14, lid_bot=.26, smile=.55, tilt=5, blush=.35, bob=1.25, armL=55, armR=55),
    'shy': dict(brow_y=5, brow_tilt=5, lid_top=.22, lid_bot=.22, smile=.5, blush=.75, tilt=-5, chestL=.6),
    'happy': dict(brow_y=6, lid_top=.02, lid_bot=.25, smile=.72, blush=.3, armL=45, armR=45),
    'curious': dict(brow_y=4, brow_asym=10, lid_top=.08, smile=.12, mouth_w=.8, tilt=9),
    'eager': dict(brow_y=9, lid_top=0, eye_scale=1.07, smile=.8, open=.12, armL=25, armR=25, squash=.03, blush=.25, bob=1.2),
    'surprised': dict(brow_y=16, lid_top=0, eye_scale=1.16, open=.5, smile=-.1, mouth_w=.65, squash=.06, armL=-20, armR=-20),
    'deflated': dict(brow_y=-2, brow_tilt=10, lid_top=.45, lid_tilt=6, smile=-.5, squash=-.07, armL=85, armR=85, tilt=-3, bob=.45),
    'determined': dict(brow_y=-6, brow_tilt=-11, lid_top=.32, lid_tilt=-5, smile=-.05, mouth_w=.7, armL=15, armR=15, squash=.03),
    'startled': dict(brow_y=20, brow_tilt=3, lid_top=0, eye_scale=1.2, open=.6, smile=-.15, mouth_w=.65, squash=.09, armL=-35, armR=-35, bob=.6),
    'embarrassed': dict(brow_y=6, brow_tilt=11, lid_top=.25, lid_bot=.15, smile=.12, blush=.85, tilt=-6, mouthL=.8, mouthR=.8),
    'hurt': dict(brow_y=3, brow_tilt=14, lid_top=.38, lid_tilt=8, smile=-.4, squash=-.03, armL=80, chestR=.95, bob=.7, glint=1.15),
    'sad': dict(brow_y=2, brow_tilt=13, lid_top=.42, lid_tilt=8, smile=-.45, squash=-.035, armL=80, armR=80, bob=.7, glint=1.15),
    'wistful': dict(brow_y=4, brow_tilt=9, lid_top=.3, lid_tilt=4, smile=.08, armL=72, armR=72, chestR=.5),
    'wistful_smile': dict(brow_y=5, brow_tilt=8, lid_top=.3, lid_bot=.15, lid_tilt=3, smile=.38, armL=70, armR=70, chestR=.5),
    'hopeful': dict(brow_y=11, brow_tilt=8, lid_top=.04, eye_scale=1.08, smile=.22, glint=1.45, chestL=.5, chestR=.5),
    'realizing': dict(brow_y=15, brow_tilt=4, lid_top=0, eye_scale=1.15, open=.35, smile=.05, mouth_w=.6, glint=1.5, squash=.04),
    'amazed': dict(brow_y=14, lid_top=.04, eye_scale=1.12, open=.3, smile=.32, glint=1.5, armL=-5, armR=-5, blush=.4),
    'inhale': dict(lid_top=1.0, brow_y=7, brow_tilt=2, smile=.15, open=.28, mouth_w=.5, squash=.07, armL=40, armR=40, bob=.4),
    'joyful': dict(brow_y=13, happy=.95, smile=1.0, open=.45, squash=.05, armL=-50, armR=-50, blush=.75, bob=1.5),
    'giggly': dict(brow_y=8, happy=.85, smile=.9, open=.2, blush=.85, tilt=6, mouthL=.9, mouthR=.3),
    'blissful': dict(brow_y=8, happy=1.0, smile=.85, blush=.55, tilt=8, bob=1.2, chestL=.5, chestR=.5),
    'touched': dict(brow_y=9, brow_tilt=9, lid_top=.3, lid_bot=.3, smile=.5, blush=.6, chestL=.8, chestR=.8, glint=1.4),
    'beaming': dict(brow_y=10, happy=.65, smile=1.0, open=.3, armL=-25, armR=-25, blush=.55, bob=1.3),
}

S_DEF = dict(lid_top=.3, lid_bot=.15, lid_tilt=0, brow_y=0, brow_tilt=0, brow_asym=0, happy=0, smile=.4,
             open=0, mouth_w=1.0, squash=0, tilt=0, glow=.6, glint=1.0)

S_EMO = {
    'asleep': dict(lid_top=1, smile=.25, glow=.35, brow_y=-3),
    'sleepy': dict(lid_top=.62, lid_bot=.1, smile=.3, glow=.45),
    'amused': dict(lid_top=.38, lid_bot=.2, brow_asym=9, smile=.6),
    'curious': dict(lid_top=.15, brow_y=7, brow_asym=11, smile=.2),
    'gentle': dict(lid_top=.32, lid_bot=.25, brow_tilt=5, smile=.5),
    'concerned': dict(lid_top=.3, brow_y=4, brow_tilt=13, smile=.02),
    'sad': dict(lid_top=.45, brow_tilt=13, lid_tilt=6, smile=-.3, glow=.45),
    'thoughtful': dict(lid_top=.3, brow_y=6, brow_asym=7, smile=.15),
    'warm': dict(lid_top=.28, lid_bot=.32, brow_y=4, brow_tilt=3, smile=.65, glow=.7),
    'mischievous': dict(lid_top=.36, lid_bot=.22, brow_asym=15, brow_tilt=-6, smile=.85, glow=.75),
    'gleeful': dict(happy=.6, brow_y=9, smile=.95, open=.2, glow=.9, squash=.03),
    'tender': dict(lid_top=.36, lid_bot=.36, brow_tilt=7, smile=.55, glow=.75),
    'laughing': dict(happy=1, brow_y=10, smile=1, open=.65, glow=1.0),
}

def draw_candy(ctx, kind, x, y, r, rot=0.0, alpha=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.push_group()
    if kind == 'E':                                            # eyeball gobstopper
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, -r * .35, -r * .4, r * 1.4, [(0, hexc('#ffffff', 1)), (1, hexc('#d9d2c4', 1))]))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, r * 0.09))
        ctx.stroke()
        ctx.set_source_rgba(*hexc('#b3263a', 0.85))
        ctx.set_line_width(max(1, r * 0.05))
        for k in range(9):                                     # squiggly veins, like the drawing
            a = k * 2 * math.pi / 9 + 0.3
            ctx.move_to(math.cos(a) * r * .38, math.sin(a) * r * .38)
            for j in range(1, 5):
                rr = r * (.38 + .14 * j)
                aa = a + 0.12 * math.sin(j * 2.1 + k)
                ctx.line_to(math.cos(aa) * rr, math.sin(aa) * rr)
            ctx.stroke()
        ctx.arc(0, 0, r * .4, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#3f9b6e'))
        ctx.fill()
        ctx.arc(0, 0, r * .2, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.arc(-r * .12, -r * .12, r * .07, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
    else:                                                      # stripey moon-mint
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#f3eadb'))
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        ctx.set_source_rgb(*hexc('#6b3a8f'))
        for k in range(-3, 4):
            x0 = k * r * 0.32
            ctx.move_to(x0, -r)
            for j in range(9):
                yy = -r + j * r / 4
                ctx.line_to(x0 + math.sin(j * 1.6) * r * 0.09, yy)
            ctx.set_line_width(r * 0.15)
            ctx.stroke()
        ctx.restore()
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, r * 0.09))
        ctx.stroke()
        ctx.arc(-r * .35, -r * .4, r * .18, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.6)
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


GHOST_PTS = [(0, -268), (128, -212), (180, -60), (196, 110), (214, 196), (182, 250), (122, 182),
             (96, 262), (34, 300), (-22, 262), (-48, 178), (-92, 272), (-160, 292), (-226, 238),
             (-198, 150), (-182, -50), (-132, -208)]

GHOST_CORNERS = [False] * len(GHOST_PTS)

GHOST_CORNERS[6] = GHOST_CORNERS[10] = True

FEET = [(178, 222, 0.5), (36, 270, 0.0), (-160, 262, -0.3)]

def ghost_outline(g, t, frame):
    sq = g['squash']
    boil = (frame // 3)
    pts = []
    for i, (x, y) in enumerate(GHOST_PTS):
        if y > 120:                                       # the hem ripples
            x += 7 * math.sin(t * 2.3 + y * 0.03 + i)
            y += 5 * math.sin(t * 3.1 + x * 0.025 + i * 0.7)
        x += 1.2 * (hash01(i, boil) - 0.5)
        y += 1.2 * (hash01(i + 40, boil) - 0.5)
        pts.append((x * (1 - sq * 0.55), y * (1 + sq) - sq * 30))
    return pts


def fpos(g, x, y):
    sq = g['squash']
    return x * (1 - sq * 0.55), y * (1 + sq) - sq * 30


def draw_arm(ctx, root, tip, side, width=27):
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    d = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / d, dx / d
    r = 23
    a = (root[0] + nx * width, root[1] + ny * width)
    b = (root[0] - nx * width, root[1] - ny * width)
    ang = math.atan2(dy, dx)
    ctx.new_path()
    ctx.move_to(*b)
    ctx.curve_to(b[0] + dx * 0.5, b[1] + dy * 0.5, tip[0] - nx * r - dx / d * 10, tip[1] - ny * r - dy / d * 10,
                 tip[0] - nx * r, tip[1] - ny * r)
    ctx.arc(tip[0], tip[1], r, ang - math.pi / 2, ang + math.pi / 2)
    ctx.curve_to(tip[0] + nx * r - dx / d * 10, tip[1] + ny * r - dy / d * 10, a[0] + dx * 0.5, a[1] + dy * 0.5, *a)
    path = ctx.copy_path()
    ctx.close_path()
    ctx.set_source_rgb(*GHOST)
    ctx.fill()
    ctx.new_path()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()


def draw_ghost(ctx, g, t, frame, inside=()):
    ctx.save()
    ctx.translate(g['x'], g['y'])
    ctx.rotate(math.radians(g['tilt']))
    ctx.scale(g['s'] * g.get('flip', 1.0), g['s'])

    # spectral glow
    ctx.arc(0, 0, 420, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, 0, 420, [(0, (0.75, 0.88, 1.0, 0.22 * g.get('glow', 1))),
                                           (1, (0.75, 0.88, 1.0, 0))]))
    ctx.fill()

    pts = ghost_outline(g, t, frame)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    def body_path():
        ctx.new_path()
        spline(ctx, pts, corners=GHOST_CORNERS)

    body_path()
    ctx.set_source(radial(ctx, -50, -140, 430, [(0, hexc('#ffffff', 1)), (0.55, GHOST + (1,)),
                                                (1, hexc('#b9c4d6', 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()

    # inner warmth after the steam soup
    if g.get('inner', 0) > 0.01:
        body_path()
        ctx.save()
        ctx.clip()
        ctx.arc(0, 80, 260, 0, 2 * math.pi)
        ctx.set_source(radial(ctx, 0, 80, 260, [(0, (1.0, 0.82, 0.55, 0.38 * g['inner'])),
                                                (1, (1.0, 0.82, 0.55, 0))]))
        ctx.fill()
        ctx.restore()

    # things seen through the sheet (a swallowed candy falling straight through)
    for kind, x, y, r, rot in inside:
        body_path()
        ctx.save()
        ctx.clip()
        draw_candy(ctx, kind, x, y, r, rot, alpha=0.55)
        ctx.restore()

    # little foot dots
    ctx.set_source_rgb(*INK)
    for fx, fy, rot in FEET:
        x, y = fpos(g, fx, fy)
        x += 7 * math.sin(t * 2.3 + fy * 0.03)
        ellipse(ctx, x, y, 9, 14, rot)
        ctx.fill()

    draw_ghost_face(ctx, g, t)

    # chest heart: hollow outline, later filled with warm light
    if g.get('heart', 0) > 0.01:
        hx, hy = fpos(g, 4, 132)
        a = g['heart']
        fill = g.get('heart_fill', 0)
        pulse = 1 + 0.06 * math.sin(t * 6) * fill
        if fill > 0.01:
            ctx.arc(hx, hy, 90, 0, 2 * math.pi)
            ctx.set_source(radial(ctx, hx, hy, 90, [(0, (1, 0.45, 0.4, 0.45 * fill * a)), (1, (1, 0.45, 0.4, 0))]))
            ctx.fill()
            heart_path(ctx, hx, hy, 62 * pulse)
            ctx.set_source_rgba(*hexc('#e5485e'), a * fill)
            ctx.fill()
        heart_path(ctx, hx, hy, 62 * pulse)
        ctx.set_source_rgba(*hexc('#5a1622'), a)
        ctx.set_line_width(4.5)
        ctx.stroke()

    # arms (drawn over the body edge so they read as part of the sheet)
    for side in (-1, 1):
        key = 'L' if side < 0 else 'R'
        root = fpos(g, side * 176, 12)
        ang = math.radians(g['arm' + key])
        tip = (root[0] + side * 78 * math.cos(ang), root[1] + 78 * math.sin(ang))
        chest = fpos(g, side * 42, 112)
        mouth = fpos(g, side * 36, 40)
        tip = (lerp(tip[0], chest[0], g['chest' + key]), lerp(tip[1], chest[1], g['chest' + key]))
        tip = (lerp(tip[0], mouth[0], g['mouth' + key]), lerp(tip[1], mouth[1], g['mouth' + key]))
        if g.get('tip' + key):
            tip = g['tip' + key]
        draw_arm(ctx, root, tip, side)
        held = g.get('hold' + key)
        if held:
            cx_, cy_ = tip[0] + side * 4, tip[1] + 18
            if key == 'R' and g.get('feed'):
                mx, my = fpos(g, 2, 32)
                cx_, cy_ = lerp(cx_, mx + 6, g['feed']), lerp(cy_, my + 4, g['feed'])
            draw_candy(ctx, held, cx_, cy_, 26)
    ctx.restore()


def draw_eye(ctx, cx, cy, rx, ry, rot, p, gaze, side, blink, body_col=GHOST):
    happy = p['happy']
    lid_top = clamp(max(p['lid_top'], blink, happy * 1.4 - 0.4))
    if happy > 0.5:
        # ^ ^ smiling eyes
        ctx.new_path()
        ctx.move_to(cx - rx * 1.25, cy + ry * 0.15)
        ctx.curve_to(cx - rx * 0.7, cy - ry * 0.75, cx + rx * 0.7, cy - ry * 0.75, cx + rx * 1.25, cy + ry * 0.15)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(9)
        ctx.stroke()
        return
    if lid_top > 0.93:
        ctx.new_path()
        ctx.move_to(cx - rx * 1.2, cy + ry * 0.05)
        ctx.curve_to(cx - rx * 0.6, cy + ry * 0.45, cx + rx * 0.6, cy + ry * 0.45, cx + rx * 1.2, cy + ry * 0.05)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(7)
        ctx.stroke()
        return
    ex, ey = cx + gaze[0] * 6, cy + gaze[1] * 5
    ctx.save()
    ellipse(ctx, ex, ey, rx, ry, rot)
    ctx.clip()
    ctx.set_source_rgb(*INK)
    ctx.paint()
    # glint shows where she is looking
    gr = p['glint']
    ellipse(ctx, ex - rx * 0.32 + gaze[0] * rx * 0.55, ey - ry * 0.42 + gaze[1] * ry * 0.4, 6.5 * gr, 11 * gr, rot)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    ellipse(ctx, ex + rx * 0.28 + gaze[0] * rx * 0.4, ey + ry * 0.3 + gaze[1] * ry * 0.3, 3 * gr, 4 * gr, 0)
    ctx.fill()
    # eyelids, in body colour; lid_tilt > 0 droops the outer corner (sad)
    top = ey - ry
    ly = top + 2 * ry * lid_top
    slope = side * p['lid_tilt'] * 2.4 / rx

    def lid_y(x):
        return ly + slope * (x - ex)
    ctx.set_source_rgb(*body_col)
    ctx.new_path()
    ctx.move_to(ex - rx * 2, lid_y(ex - rx * 2))
    ctx.line_to(ex - rx * 2, top - 60)
    ctx.line_to(ex + rx * 2, top - 60)
    ctx.line_to(ex + rx * 2, lid_y(ex + rx * 2))
    ctx.close_path()
    ctx.fill()
    bot = p['lid_bot']
    if bot > 0.02:
        by = ey + ry - 2 * ry * bot * 0.8
        ctx.new_path()
        ctx.move_to(ex - rx * 2, ey + ry + 40)
        ctx.line_to(ex - rx * 2, by + ry * 0.25)
        ctx.curve_to(ex - rx * 0.6, by - ry * 0.25 * bot, ex + rx * 0.6, by - ry * 0.25 * bot, ex + rx * 2, by + ry * 0.25)
        ctx.line_to(ex + rx * 2, ey + ry + 40)
        ctx.close_path()
        ctx.fill()
    ctx.restore()
    if lid_top > 0.08:
        ctx.new_path()
        ctx.move_to(ex - rx * 1.15, lid_y(ex - rx * 1.15))
        ctx.line_to(ex + rx * 1.15, lid_y(ex + rx * 1.15))
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()


def draw_mouth(ctx, cx, cy, open_, w, smile, depth=118, tongue=True, inner=None):
    hw = w / 2
    lift = smile * 16
    if open_ < 0.06:
        ctx.new_path()
        ctx.move_to(cx - hw * 0.8, cy - lift)
        ctx.curve_to(cx - hw * 0.3, cy + smile * 10, cx + hw * 0.3, cy + smile * 10, cx + hw * 0.8, cy - lift)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6.5)
        ctx.stroke()
        return
    h = depth * open_
    top_c = cy - h * 0.38 + smile * 5
    bot_c = cy + h * 0.62 + smile * 10
    ctx.new_path()
    ctx.move_to(cx - hw, cy - lift)
    ctx.curve_to(cx - hw * 0.85, top_c - h * 0.22, cx + hw * 0.85, top_c - h * 0.22, cx + hw, cy - lift)
    ctx.curve_to(cx + hw * 1.0, bot_c + h * 0.3, cx - hw * 1.0, bot_c + h * 0.3, cx - hw, cy - lift)
    ctx.close_path()
    path = ctx.copy_path()
    ctx.set_source_rgb(*(inner or hexc('#1b0c12')))
    ctx.fill()
    if tongue and open_ > 0.3:
        ctx.save()
        ctx.append_path(path)
        ctx.clip()
        ellipse(ctx, cx + hw * 0.1, bot_c + h * 0.12, hw * 0.75, h * 0.32)
        ctx.set_source_rgb(*hexc('#a43a55'))
        ctx.fill()
        ctx.restore()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()


def draw_ghost_face(ctx, g, t):
    p = g
    es = p['eye_scale']
    gaze = g['gaze']
    ctx.save()
    ctx.translate(gaze[0] * 16, gaze[1] * 9)        # a little head-turn toward what she looks at
    for side, (ex, ey, rot) in ((-1, (-62, -104, 0.10)), (1, (62, -109, -0.10))):
        x, y = fpos(g, ex + gaze[0] * 3, ey + gaze[1] * 2)
        draw_eye(ctx, x, y, 26.5 * es, 50 * es, rot, p, gaze, side, g['blink'])
        # eyebrows
        by = y - 50 * es - 24 - p['brow_y'] + (-p['brow_asym'] if side > 0 else p['brow_asym'] * 0.3)
        tilt = p['brow_tilt'] * 1.3
        inner = (x - side * 22, by - tilt * 0.5)
        outer = (x + side * 24, by + tilt * 0.5)
        ctx.new_path()
        ctx.move_to(*outer)
        ctx.curve_to(lerp(outer[0], inner[0], 0.35), outer[1] - 7, lerp(outer[0], inner[0], 0.7), inner[1] - 6, *inner)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(7.5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # blush
    if p['blush'] > 0.02:
        for side in (-1, 1):
            x, y = fpos(g, side * 98, -28)
            ellipse(ctx, x, y, 30, 15)
            ctx.set_source(radial(ctx, x, y, 30, [(0, hexc('#ff8fa8', 0.55 * p['blush'])), (1, hexc('#ff8fa8', 0))]))
            ctx.fill()
    # tear
    tear = g.get('tear', 0)
    if tear > 0:
        x, y = fpos(g, -88, -70)
        prog = clamp((tear - 0.2) / 0.8)
        ty = y + prog * 110
        a = 1 - clamp((tear - 0.85) / 0.15)
        sz = 7 + 5 * clamp(tear / 0.2)
        ctx.new_path()
        ctx.move_to(x, ty - sz * 1.8)
        ctx.curve_to(x + sz, ty - sz * 0.2, x + sz, ty + sz, x, ty + sz)
        ctx.curve_to(x - sz, ty + sz, x - sz, ty - sz * 0.2, x, ty - sz * 1.8)
        ctx.set_source_rgba(*hexc('#a9dcff'), 0.9 * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexc('#2a4f73'), 0.8 * a)
        ctx.set_line_width(2)
        ctx.stroke()
        ellipse(ctx, x - sz * 0.3, ty, sz * 0.25, sz * 0.4)
        ctx.set_source_rgba(1, 1, 1, 0.9 * a)
        ctx.fill()
    mx, my = fpos(g, 2 + gaze[0] * 3, 32)
    draw_mouth(ctx, mx, my, p['open'], 58 * p['mouth_w'], p['smile'])
    ctx.restore()


POT = hexc('#2d2b3a')

def draw_cauldron(ctx, c, t, frame):
    ctx.save()
    ctx.translate(c['x'], c['y'])
    ctx.rotate(math.radians(c['tilt']))
    sq = c['squash']
    ctx.scale(c['s'] * (1 - sq * 0.5), c['s'] * (1 + sq))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    glow = c['glow']
    gcol = c.get('gcol', (0.55, 1.0, 0.78))
    boil = frame // 3

    def jit(i, a=1.3):
        return a * (hash01(i, boil) - 0.5)

    # glow from the brew
    ctx.arc(0, -150, 300, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, -150, 300, [(0, gcol + (0.28 * glow,)), (1, gcol + (0,))]))
    ctx.fill()
    # stubby feet
    for fx in (-100, 0, 100):
        ellipse(ctx, fx, 122 + (8 if fx == 0 else 0), 30, 22)
        ctx.set_source_rgb(*hexc('#1d1b26'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        ctx.stroke()
    # side handles
    for side in (-1, 1):
        ctx.new_path()
        ctx.arc(side * 160, -78, 26, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(9)
        ctx.stroke()
    # belly
    pts = [(-150 + jit(1), -100), (-176 + jit(2), -20), (-160 + jit(3), 70), (-95, 125 + jit(4)), (0, 140 + jit(5)),
           (95, 125 + jit(6)), (160 + jit(7), 70), (176 + jit(8), -20), (150 + jit(9), -100)]
    ctx.new_path()
    spline(ctx, pts, closed=True)
    ctx.set_source(radial(ctx, -70, -50, 260, [(0, hexc('#5c5a72', 1)), (0.45, POT + (1,)), (1, hexc('#121019', 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()
    # warm firelight from below
    ctx.new_path()
    spline(ctx, pts, closed=True)
    ctx.save()
    ctx.clip()
    ctx.arc(0, 190, 200, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, 0, 190, 200, [(0, (1, 0.55, 0.2, 0.35 * c.get('fire', 1))), (1, (1, 0.55, 0.2, 0))]))
    ctx.fill()
    ctx.restore()
    # shine
    ctx.new_path()
    ctx.arc(-40, 0, 125, math.radians(195), math.radians(245))
    ctx.set_source_rgba(1, 1, 1, 0.22)
    ctx.set_line_width(10)
    ctx.stroke()
    # rim + brew
    ellipse(ctx, 0, -108, 162, 40)
    ctx.set_source_rgb(*hexc('#3a384b'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.stroke()
    ellipse(ctx, 0, -112, 134, 26)
    bright = clamp(0.45 + 0.55 * glow)
    ctx.set_source(radial(ctx, 0, -112, 140, [(0, (lerp(0.2, 0.85, bright), 1.0, lerp(0.6, 0.9, bright), 1)),
                                              (1, (gcol[0] * 0.45, gcol[1] * 0.6, gcol[2] * 0.5, 1))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    # surface bubbles
    for k in range(6):
        ph = (t * (0.6 + 0.25 * glow) + hash01(k, 1)) % 1.0
        bx = -95 + 190 * hash01(k + int(t * (0.6 + 0.25 * glow) + hash01(k, 1)), 2)
        r = 5 + 9 * ph
        ellipse(ctx, bx, -112 + 10 * hash01(k, 4), r, r * 0.6)
        ctx.set_source_rgba(0.9, 1, 0.95, 0.75 * (1 - ph))
        ctx.set_line_width(2.5)
        ctx.stroke()
    # big "blorp" bubbles when she wakes / when sweets go in
    for bt in c.get('blorps', ()):
        u = t - bt
        if 0 <= u <= 0.7:
            r = 16 + 40 * u
            ellipse(ctx, 20, -122 - 30 * u, r, r * 0.8)
            ctx.set_source_rgba(0.85, 1, 0.92, 0.85 * (1 - u / 0.7))
            ctx.set_line_width(4)
            ctx.stroke()
    # the three rings on the rim, as in the drawing
    for k, rx in enumerate((-92, 0, 92)):
        ry = -82 if rx else -70
        ctx.new_path()
        ctx.arc(rx, ry, 12, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#4a4860'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4.5)
        ctx.stroke()

    # face
    p = c
    gaze = c['gaze']
    ctx.save()
    ctx.translate(gaze[0] * 12, gaze[1] * 6)
    for side in (-1, 1):
        ex, ey = side * 52 + gaze[0] * 5, -12 + gaze[1] * 4
        draw_eye(ctx, ex, ey, 14, 19, 0, p, gaze, side, c['blink'], body_col=hexc('#3a3848'))
        # spectacles
        ctx.new_path()
        ctx.arc(ex, ey + 2, 27, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexc('#d9be7a'), 0.95)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.new_path()
        ctx.arc(ex - 8, ey - 6, 18, math.radians(200), math.radians(250))
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ctx.set_line_width(3)
        ctx.stroke()
        # bushy grey brows
        by = ey - 40 - p['brow_y'] + (-p['brow_asym'] if side > 0 else p['brow_asym'] * 0.3)
        tilt = p['brow_tilt'] * 1.2
        inner = (ex - side * 20, by - tilt * 0.5)
        outer = (ex + side * 26, by + tilt * 0.5 + 3)
        ctx.new_path()
        ctx.move_to(*outer)
        ctx.curve_to(lerp(outer[0], inner[0], 0.35), outer[1] - 9, lerp(outer[0], inner[0], 0.7), inner[1] - 7, *inner)
        ctx.set_source_rgb(*hexc('#b9b6c6'))
        ctx.set_line_width(10)
        ctx.stroke()
    ctx.new_path()
    ctx.move_to(-27, -10)
    ctx.curve_to(-15, -18, 15, -18, 27, -10)
    ctx.set_source_rgba(*hexc('#d9be7a'), 0.95)
    ctx.set_line_width(3.5)
    ctx.stroke()
    # rosy cheeks
    for side in (-1, 1):
        ellipse(ctx, side * 92, 30, 24, 13)
        ctx.set_source(radial(ctx, side * 92, 30, 24, [(0, hexc('#ff8f8f', 0.35)), (1, hexc('#ff8f8f', 0))]))
        ctx.fill()
    # the U-shaped smile from the drawing
    open_ = p['open']
    w = 104 * p['mouth_w']
    smile = p['smile']
    hw = w / 2
    lift = smile * 14
    cy = 52
    depth = 16 + 46 * open_ + 10 * max(0, smile)
    ctx.new_path()
    ctx.move_to(-hw, cy - lift)
    ctx.curve_to(-hw * 0.6, cy - lift + 6 - open_ * 10, hw * 0.6, cy - lift + 6 - open_ * 10, hw, cy - lift)
    ctx.curve_to(hw * 0.95, cy + depth * 1.3, -hw * 0.95, cy + depth * 1.3, -hw, cy - lift)
    ctx.close_path()
    path = ctx.copy_path()
    ctx.set_source(radial(ctx, 0, cy + depth, hw * 1.2, [(0, (0.95, 0.45, 0.15, 1)), (1, (0.22, 0.06, 0.05, 1))]))
    ctx.fill()
    ctx.save()
    ctx.append_path(path)
    ctx.clip()
    ellipse(ctx, 6, cy + depth * 0.95, hw * 0.55, depth * 0.35)
    ctx.set_source_rgb(*hexc('#b8435a'))
    ctx.fill()
    ctx.restore()
    ctx.append_path(path)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5.5)
    ctx.stroke()
    ctx.restore()
    ctx.restore()


def draw_steam_squiggles(ctx, x, y, s, t, alpha=0.6):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k, dx in enumerate((-55, 0, 55)):
        ctx.new_path()
        for j in range(18):
            yy = -j * 9
            xx = dx + 11 * math.sin(j * 0.55 - t * 3.2 + k * 1.7) * (0.4 + j / 18)
            (ctx.line_to if j else ctx.move_to)(xx, yy - 130)
        ctx.set_source(linear(0, -130, 0, -290, [(0, (0.92, 0.95, 1, alpha)), (1, (0.92, 0.95, 1, 0))]))
        ctx.set_line_width(6)
        ctx.stroke()
    ctx.restore()


def stars(ctx, n, y1, seed):
    for i in range(n):
        x = hash01(i, seed) * W
        y = hash01(i, seed + 1) * y1
        r = 0.8 + 1.8 * hash01(i, seed + 2) ** 3
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.97, 0.88, 0.35 + 0.5 * hash01(i, seed + 3))
        ctx.fill()


def moon(ctx, x, y, r):
    ctx.arc(x, y, r * 2.2, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x, y, r * 2.2, [(0, hexc('#f6ecc9', 0.35)), (0.45, hexc('#f6ecc9', 0.12)), (1, hexc('#f6ecc9', 0))]))
    ctx.fill()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x - r * .3, y - r * .3, r * 1.4, [(0, hexc('#fbf3da', 1)), (1, hexc('#e3cf9f', 1))]))
    ctx.fill()
    for i in range(7):
        cx = x + (hash01(i, 77) - 0.5) * r * 1.3
        cy = y + (hash01(i, 78) - 0.5) * r * 1.3
        if math.hypot(cx - x, cy - y) > r * 0.8:
            continue
        ellipse(ctx, cx, cy, r * (0.06 + 0.1 * hash01(i, 79)), r * (0.05 + 0.08 * hash01(i, 79)))
        ctx.set_source_rgba(0.72, 0.62, 0.42, 0.22)
        ctx.fill()


def curly_tree(ctx, x, y, h, flip=1, col=hexc('#07070c')):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(flip, 1)
    ctx.set_source_rgb(*col)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # trunk
    ctx.new_path()
    ctx.move_to(-38, 0)
    ctx.curve_to(-30, -h * 0.4, 10, -h * 0.6, -5, -h)
    ctx.curve_to(20, -h * 0.6, 22, -h * 0.35, 40, 0)
    ctx.close_path()
    ctx.fill()

    def branch(x0, y0, ang, length, width, depth):
        x1 = x0 + math.cos(ang) * length
        y1 = y0 + math.sin(ang) * length
        ctx.new_path()
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 + math.cos(ang - 0.3) * length * 0.5, y0 + math.sin(ang - 0.3) * length * 0.5,
                     x1 - math.cos(ang + 0.4) * length * 0.3, y1 - math.sin(ang + 0.4) * length * 0.3, x1, y1)
        ctx.set_line_width(width)
        ctx.stroke()
        if depth == 0:
            # curl the tip into a little spiral
            r = length * 0.22
            a0 = ang + math.pi / 2
            ctx.new_path()
            for k in range(40):
                f = k / 39
                a = a0 + f * 4.2
                rr = r * (1 - f * 0.85)
                (ctx.line_to if k else ctx.move_to)(x1 + math.cos(a) * rr - math.cos(a0) * r,
                                                     y1 + math.sin(a) * rr - math.sin(a0) * r)
            ctx.set_line_width(max(2, width * 0.8))
            ctx.stroke()
            return
        branch(x1, y1, ang - 0.55, length * 0.68, width * 0.6, depth - 1)
        branch(x1, y1, ang + 0.5, length * 0.6, width * 0.55, depth - 1)

    branch(-5, -h, -math.pi / 2 - 0.35, h * 0.32, 16, 2)
    branch(-8, -h * 0.75, -math.pi / 2 - 1.1, h * 0.3, 12, 2)
    branch(5, -h * 0.65, -math.pi / 2 + 1.0, h * 0.28, 11, 2)
    ctx.restore()


def crooked_house(ctx, x, y, w, h, lean, roof, col, win_col, seed):
    ctx.save()
    ctx.translate(x, y)
    ctx.new_path()
    ctx.move_to(0, 0)
    ctx.line_to(lean * h * 0.1, -h)
    ctx.line_to(w * 0.5 + lean * h * 0.25, -h - roof)
    ctx.line_to(w + lean * h * 0.1, -h)
    ctx.line_to(w, 0)
    ctx.close_path()
    ctx.set_source_rgb(*col)
    ctx.fill()
    for i in range(3):
        if hash01(i, seed) < 0.55:
            wx = w * (0.2 + 0.25 * i) + lean * h * 0.05
            wy = -h * (0.35 + 0.3 * hash01(i, seed + 1))
            ctx.rectangle(wx, wy, w * 0.13, h * 0.13)
            ctx.set_source_rgb(*win_col)
            ctx.fill()
    ctx.restore()


def tombstone(ctx, x, y, w, h, rot, cross=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.new_path()
    if cross:
        ctx.rectangle(-w * 0.12, -h, w * 0.24, h)
        ctx.rectangle(-w * 0.45, -h * 0.75, w * 0.9, w * 0.22)
    else:
        ctx.move_to(-w / 2, 0)
        ctx.line_to(-w / 2, -h + w / 2)
        ctx.arc(0, -h + w / 2, w / 2, math.pi, 0)
        ctx.line_to(w / 2, 0)
        ctx.close_path()
    ctx.set_source_rgb(*hexc('#2a3140'))
    ctx.fill_preserve()
    ctx.set_source_rgb(*hexc('#0c0e14'))
    ctx.set_line_width(4)
    ctx.stroke()
    if not cross:
        ctx.move_to(-w * 0.25, -h * 0.55)
        ctx.line_to(w * 0.25, -h * 0.55)
        ctx.move_to(-w * 0.2, -h * 0.42)
        ctx.line_to(w * 0.2, -h * 0.42)
        ctx.set_source_rgba(0.05, 0.06, 0.08, 0.6)
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.restore()


def fence(ctx, x0, x1, y, h):
    ctx.set_source_rgb(*hexc('#090a10'))
    ctx.set_line_width(5)
    ctx.move_to(x0, y - h * 0.25)
    ctx.line_to(x1, y - h * 0.25 + 6)
    ctx.move_to(x0, y - h * 0.75)
    ctx.line_to(x1, y - h * 0.75 + 4)
    ctx.stroke()
    x = x0
    i = 0
    while x < x1:
        lean = (hash01(i, 5) - 0.5) * 0.08
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(lean)
        ctx.move_to(0, 0)
        ctx.line_to(0, -h)
        ctx.set_line_width(5)
        ctx.stroke()
        # curly finial
        ctx.new_path()
        for k in range(20):
            f = k / 19
            a = -math.pi / 2 + f * 5.5
            r = 11 * (1 - f * 0.7)
            (ctx.line_to if k else ctx.move_to)(math.cos(a) * r, -h - 11 + math.sin(a) * r + 11)
        ctx.set_line_width(3.5)
        ctx.stroke()
        ctx.restore()
        x += 46
        i += 1


def pumpkin(ctx, x, y, r, t=0.0, lit=1.0):
    ctx.save()
    ctx.translate(x, y)
    for k, dx in enumerate((-0.45, 0.45, 0.0)):
        ellipse(ctx, dx * r, 0, r * 0.62, r * 0.78)
        ctx.set_source_rgb(*(hexc('#d4661c') if k < 2 else hexc('#e8792a')))
        ctx.fill_preserve()
        ctx.set_source_rgb(*hexc('#3a1606'))
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.rectangle(-r * 0.08, -r * 0.95, r * 0.16, r * 0.25)
    ctx.set_source_rgb(*hexc('#2f3d1c'))
    ctx.fill()
    # carved face
    flick = 0.8 + 0.2 * lit
    face = hexc('#ffd36b')
    ctx.set_source_rgba(*face, flick)
    for side in (-1, 1):
        ctx.move_to(side * r * 0.35, -r * 0.3)
        ctx.line_to(side * r * 0.15, -r * 0.05)
        ctx.line_to(side * r * 0.5, -r * 0.05)
        ctx.close_path()
        ctx.fill()
    ctx.move_to(-r * 0.5, r * 0.2)
    ctx.curve_to(-r * 0.2, r * 0.55, r * 0.2, r * 0.55, r * 0.5, r * 0.2)
    ctx.line_to(r * 0.25, r * 0.3)
    ctx.line_to(r * 0.1, r * 0.2)
    ctx.line_to(-r * 0.1, r * 0.32)
    ctx.line_to(-r * 0.3, r * 0.22)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


def vignette(ctx, strength=0.55):
    ctx.rectangle(0, 0, W, H)
    g = cairo.RadialGradient(W / 2, H * 0.45, H * 0.32, W / 2, H * 0.45, H * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0.02, 0)
    g.add_color_stop_rgba(1, 0, 0, 0.02, strength)
    ctx.set_source(g)
    ctx.fill()


def flame(ctx, x, y, s, t, seed):
    f = 1 + 0.12 * vnoise(t * 9, seed) + 0.06 * vnoise(t * 17, seed + 1)
    sway = 6 * vnoise(t * 5, seed + 2) * s
    ctx.arc(x, y - 20 * s, 60 * s, 0, 2 * math.pi)
    ctx.set_source(radial(ctx, x, y - 20 * s, 60 * s, [(0, (1, 0.75, 0.3, 0.35)), (1, (1, 0.75, 0.3, 0))]))
    ctx.fill()
    for k, (col, sc) in enumerate((('#ff7a1a', 1.0), ('#ffd166', 0.6))):
        h = 46 * s * f * sc
        w = 15 * s * sc
        ctx.new_path()
        ctx.move_to(x, y)
        ctx.curve_to(x - w * 1.3, y - h * 0.2, x - w * 0.5 + sway, y - h * 0.7, x + sway * 1.4, y - h)
        ctx.curve_to(x + w * 0.5 + sway, y - h * 0.7, x + w * 1.3, y - h * 0.2, x, y)
        ctx.set_source_rgb(*hexc(col))
        ctx.fill()


def silhouette(ctx, x, y, s, kind, side):
    col = hexc('#0b0e16')
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.push_group()
    ctx.set_source_rgb(*col)
    ctx.new_path()
    ctx.move_to(-70, 0)
    ctx.curve_to(-70, -120, 70, -120, 70, 0)
    ctx.close_path()
    ctx.fill()
    hy = -150
    if kind == 'pumpkin':
        ellipse(ctx, 0, hy, 62, 50)
        ctx.fill()
        ctx.rectangle(-6, hy - 66, 12, 20)
        ctx.fill()
    elif kind == 'cat':
        ellipse(ctx, 0, hy + 20, 42, 38)
        ctx.fill()
        for e in (-1, 1):
            ctx.move_to(e * 38, hy)
            ctx.line_to(e * 26, hy - 50)
            ctx.line_to(e * 8, hy - 12)
            ctx.fill()
    elif kind == 'hood':
        ctx.move_to(-50, hy + 40)
        ctx.curve_to(-55, hy - 40, -10, hy - 80, 10, hy - 90)
        ctx.curve_to(40, hy - 50, 55, hy, 50, hy + 40)
        ctx.close_path()
        ctx.fill()
    else:
        ellipse(ctx, 0, hy, 40, 46)
        ctx.fill()
        if kind == 'hat':
            ellipse(ctx, 0, hy - 36, 80, 12)
            ctx.fill()
            ctx.move_to(-38, hy - 40)
            ctx.line_to(14, hy - 170)
            ctx.line_to(36, hy - 40)
            ctx.fill()
        else:
            ctx.rectangle(-30, hy - 110, 60, 75)
            ctx.fill()
            ellipse(ctx, 0, hy - 36, 62, 10)
            ctx.fill()
    shape = ctx.pop_group()
    # moonlit rim so each neighbour reads against the night
    ctx.save()
    ctx.translate(-4, -4)
    ctx.set_source_rgba(0.55, 0.65, 0.85, 0.55)
    ctx.mask(shape)
    ctx.restore()
    ctx.set_source(shape)
    ctx.paint()
    for e in (-1, 1):
        ellipse(ctx, e * 15 - side * 8, hy + 2 + (20 if kind == 'cat' else 0), 7, 9)
        ctx.set_source_rgb(*hexc('#ffd36b'))
        ctx.fill()
    ctx.new_path()
    ctx.move_to(-14 - side * 8, hy + 22 + (20 if kind == 'cat' else 0))
    ctx.curve_to(-6 - side * 8, hy + 30, 6 - side * 8, hy + 30, 14 - side * 8, hy + 22 + (20 if kind == 'cat' else 0))
    ctx.set_source_rgba(*hexc('#ffd36b'), 0.8)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def draw_bubble_cloud(ctx, cx, cy, rx, ry, seed):
    pts = []
    n = 9
    for i in range(n):
        a = i / n * 2 * math.pi
        bump = 1 + 0.12 * math.sin(a * 3 + seed)
        pts.append((cx + math.cos(a) * rx * bump, cy + math.sin(a) * ry * bump))
    ctx.new_path()
    ctx.move_to(*pts[0])
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ox, oy = mx - cx, my - cy
        ctx.curve_to(p0[0] + ox * 0.45, p0[1] + oy * 0.45, p1[0] + ox * 0.45, p1[1] + oy * 0.45, *p1)
    ctx.close_path()
    ctx.set_source_rgba(0.97, 0.96, 0.93, 0.95)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()


def draw_hearts(ctx, x, y, s, t, alpha=1.0):
    """The two hearts from the drawing: one hollow, one filled in."""
    for k, (dx, filled) in enumerate(((-42, False), (42, True))):
        hx = x + dx * s
        hy = y + 8 * math.sin(t * 2 + k) * s
        heart_path(ctx, hx, hy, 60 * s)
        if filled:
            ctx.set_source_rgba(*hexc('#e5485e'), alpha)
            ctx.fill_preserve()
            ctx.set_source_rgba(*INK, alpha)
        else:
            ctx.set_source_rgba(*hexc('#f4e6c4'), alpha)
        ctx.set_line_width(5 * s)
        ctx.stroke()


