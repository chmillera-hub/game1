"""Backgrounds, icons and props."""
import math

import cairo

from draw import (INK, WHITE, W, H, clamp, ellipse, fill_stroke, glow, lerp, rgba, rrect,
                  shade, star, text, text_block, vgrad, font, text_w, smooth)


# ------------------------------------------------------------------ outdoor
def sky(ctx, top=(0.62, 0.84, 1.0), bottom=(1.0, 0.92, 0.8), y1=H):
    ctx.set_source(vgrad(ctx, 0, y1, [(0, top), (1, bottom)]))
    ctx.paint()


def sun(ctx, x, y, r, t):
    glow(ctx, x, y, r * 3, (1, 0.9, 0.55), 0.55)
    for i in range(12):
        a = i * math.pi / 6 + t * 0.15
        ctx.move_to(x + math.cos(a) * r * 1.25, y + math.sin(a) * r * 1.25)
        ctx.line_to(x + math.cos(a) * r * 1.55, y + math.sin(a) * r * 1.55)
    rgba(ctx, (1, 0.8, 0.3), 0.8)
    ctx.set_line_width(10)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    fill_stroke(ctx, (1, 0.85, 0.35), INK, 5)


def cloud(ctx, x, y, s, a=1.0, c=WHITE, outline=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.new_path()
    for cx, cy, r in ((-60, 10, 42), (-15, -18, 55), (40, -5, 48), (78, 16, 34), (10, 20, 45)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    rgba(ctx, c, a)
    ctx.fill()
    ctx.restore()


def clouds(ctx, t, ys=(330, 480, 260), speed=12):
    for i, y in enumerate(ys):
        x = (i * 420 + t * speed * (1 + 0.3 * i)) % (W + 400) - 200
        cloud(ctx, x, y, 0.9 - 0.15 * i, 0.9)


def ground(ctx, y, c=(0.55, 0.8, 0.45), edge=True):
    ctx.rectangle(0, y, W, H - y)
    rgba(ctx, c)
    ctx.fill()
    if edge:
        ctx.move_to(0, y)
        ctx.line_to(W, y)
        rgba(ctx, shade(c, -0.25))
        ctx.set_line_width(5)
        ctx.stroke()


def bush(ctx, x, y, s, c=(0.36, 0.68, 0.36)):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.new_path()
    for cx, cy, r in ((-55, -40, 50), (0, -70, 62), (55, -42, 50), (0, -30, 55)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    fill_stroke(ctx, c, INK, 5)
    for cx, cy, r in ((-55, -40, 44), (0, -70, 56), (55, -42, 44), (0, -30, 49)):
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        rgba(ctx, c)
        ctx.fill()
    for cx, cy in ((-20, -90), (30, -60), (-50, -45)):
        ellipse(ctx, cx, cy, 14, 9)
        rgba(ctx, WHITE, 0.25)
        ctx.fill()
    ctx.restore()


def tree(ctx, x, y, s, t=0.0, c=(0.38, 0.72, 0.4)):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -22, -200, 44, 200, 12)
    fill_stroke(ctx, (0.55, 0.38, 0.25), INK, 5)
    sway = math.sin(t * 1.2 + x) * 4
    ctx.translate(sway, 0)
    ctx.new_path()
    for cx, cy, r in ((-70, -230, 75), (0, -300, 95), (70, -230, 75), (0, -200, 70)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    fill_stroke(ctx, c, INK, 5)
    for cx, cy, r in ((-70, -230, 69), (0, -300, 89), (70, -230, 69), (0, -200, 64)):
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        rgba(ctx, c)
        ctx.fill()
    ctx.restore()


def bench(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    wood = (0.75, 0.52, 0.32)
    for yy in (-120, -85):
        rrect(ctx, -150, yy, 300, 22, 8)
        fill_stroke(ctx, wood, INK, 4.5)
    rrect(ctx, -160, -60, 320, 24, 8)
    fill_stroke(ctx, wood, INK, 4.5)
    for xx in (-130, 120):
        ctx.rectangle(xx, -40, 12, 40)
        fill_stroke(ctx, (0.35, 0.35, 0.4), INK, 4)
    ctx.restore()


# ------------------------------------------------------------------ house
def house(ctx, door_open=0.0, t=0.0, bell_glow=0.0):
    wall = (0.99, 0.9, 0.76)
    ctx.rectangle(-10, 380, W + 20, 900)
    fill_stroke(ctx, wall, INK, 6)
    # siding lines
    for y in range(440, 1260, 60):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    rgba(ctx, shade(wall, -0.07))
    ctx.set_line_width(3)
    ctx.stroke()
    # roof edge
    ctx.move_to(-20, 400)
    ctx.line_to(W + 20, 400)
    ctx.line_to(W + 20, 330)
    ctx.line_to(-20, 330)
    ctx.close_path()
    fill_stroke(ctx, (0.75, 0.32, 0.3), INK, 6)
    for x in range(-20, W + 40, 60):
        ctx.arc(x + 30, 400, 30, 0, math.pi)
        fill_stroke(ctx, (0.68, 0.28, 0.27), INK, 4)
    # windows
    for wx in (150, 930):
        rrect(ctx, wx - 105, 560, 210, 250, 14)
        fill_stroke(ctx, (0.9, 0.92, 0.95), INK, 6)
        rrect(ctx, wx - 88, 577, 176, 216, 8)
        ctx.set_source(vgrad(ctx, 577, 793, [(0, (0.62, 0.82, 0.98)), (1, (0.85, 0.93, 1))]))
        ctx.fill()
        ctx.move_to(wx, 577)
        ctx.line_to(wx, 793)
        ctx.move_to(wx - 88, 685)
        ctx.line_to(wx + 88, 685)
        rgba(ctx, (0.9, 0.92, 0.95))
        ctx.set_line_width(10)
        ctx.stroke()
        for s in (-1, 1):  # curtains
            ctx.move_to(wx + s * 88, 577)
            ctx.curve_to(wx + s * 40, 620, wx + s * 75, 720, wx + s * 50, 793)
            ctx.line_to(wx + s * 88, 793)
            ctx.close_path()
            rgba(ctx, (0.95, 0.55, 0.5), 0.85)
            ctx.fill()
        rrect(ctx, wx - 120, 805, 240, 26, 8)
        fill_stroke(ctx, (0.9, 0.92, 0.95), INK, 5)
    # door frame
    fx, fy, fw, fh = 540 - 170, 690, 340, 545
    rrect(ctx, fx - 18, fy - 18, fw + 36, fh + 18, 20)
    fill_stroke(ctx, (0.95, 0.95, 0.97), INK, 6)
    # interior
    ctx.rectangle(fx, fy, fw, fh)
    ctx.set_source(vgrad(ctx, fy, fy + fh, [(0, (0.98, 0.8, 0.5)), (1, (0.85, 0.6, 0.4))]))
    ctx.fill()
    # bell
    ctx.arc(fx - 60, 930, 18, 0, 2 * math.pi)
    fill_stroke(ctx, (0.95, 0.95, 0.97), INK, 4)
    if bell_glow > 0:
        glow(ctx, fx - 60, 930, 60, (1, 0.9, 0.4), 0.8 * bell_glow)
    ctx.arc(fx - 60, 930, 8, 0, 2 * math.pi)
    rgba(ctx, (1, 0.8, 0.3))
    ctx.fill()
    return (fx, fy, fw, fh)


def door_panel(ctx, frame, open_k, color=(0.33, 0.55, 0.85)):
    fx, fy, fw, fh = frame
    k = clamp(open_k)
    if k > 0.98:
        return
    # door swings inward: visible width shrinks toward the hinge (left side)
    w = fw * (1 - k * 0.85)
    skew = k * 40
    ctx.move_to(fx, fy)
    ctx.line_to(fx + w, fy + skew * 0.5)
    ctx.line_to(fx + w, fy + fh - skew * 0.3)
    ctx.line_to(fx, fy + fh)
    ctx.close_path()
    fill_stroke(ctx, shade(color, -0.1 * k), INK, 6)
    # panels
    sx = w / fw
    for py, ph in ((fy + 60, 170), (fy + 290, 200)):
        rrect(ctx, fx + 45 * sx, py + skew * 0.2, (fw - 90) * sx, ph, 10)
        rgba(ctx, shade(color, -0.18))
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.arc(fx + w - 40 * sx, fy + fh * 0.55, 15, 0, 2 * math.pi)
    fill_stroke(ctx, (1, 0.82, 0.3), INK, 4)


def doorstep(ctx):
    rrect(ctx, 320, 1228, 440, 42, 10)
    fill_stroke(ctx, (0.75, 0.73, 0.75), INK, 5)
    rrect(ctx, 400, 1214, 280, 20, 8)
    fill_stroke(ctx, (0.85, 0.55, 0.4), INK, 4)


def pot_plant(ctx, x, y, s=1.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for i, a in enumerate((-0.6, -0.2, 0.25, 0.65)):
        ctx.save()
        ctx.rotate(a + math.sin(t * 1.5 + i) * 0.04)
        ctx.move_to(0, -90)
        ctx.curve_to(-30, -150, -20, -210, 0, -240)
        ctx.curve_to(20, -210, 30, -150, 0, -90)
        fill_stroke(ctx, (0.35, 0.7, 0.4), INK, 4.5)
        ctx.restore()
    ctx.move_to(-60, -100)
    ctx.line_to(60, -100)
    ctx.line_to(45, 0)
    ctx.line_to(-45, 0)
    ctx.close_path()
    fill_stroke(ctx, (0.88, 0.5, 0.35), INK, 5)
    ctx.restore()


def trash_bag(ctx, x, y, s=1.0, tilt=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.scale(s, s)
    c = (0.3, 0.33, 0.36)
    ctx.move_to(-20, -120)
    ctx.curve_to(-90, -110, -105, -20, -80, 0)
    ctx.curve_to(-40, 12, 40, 12, 80, 0)
    ctx.curve_to(105, -20, 90, -110, 20, -120)
    ctx.close_path()
    fill_stroke(ctx, c, INK, 5)
    ctx.move_to(-20, -120)
    ctx.curve_to(-40, -150, -10, -150, 0, -128)
    ctx.curve_to(10, -150, 40, -150, 20, -120)
    fill_stroke(ctx, c, INK, 5)
    ctx.move_to(-50, -80)
    ctx.curve_to(-60, -50, -55, -30, -45, -15)
    rgba(ctx, WHITE, 0.25)
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.restore()


def banana_peel(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    yl = (1, 0.85, 0.3)
    for a in (-0.9, 0, 0.9):
        ctx.save()
        ctx.rotate(a)
        ctx.move_to(-10, 0)
        ctx.curve_to(-18, -30, -8, -55, 0, -60)
        ctx.curve_to(8, -55, 18, -30, 10, 0)
        fill_stroke(ctx, yl, INK, 4)
        ctx.restore()
    ctx.restore()


def crumpled(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    pts = [(-25, -5), (-15, -28), (8, -30), (26, -14), (22, 8), (2, 14), (-20, 10)]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    fill_stroke(ctx, (0.95, 0.95, 0.92), INK, 4)
    ctx.move_to(-10, -18)
    ctx.line_to(5, -5)
    ctx.line_to(15, -20)
    rgba(ctx, INK, 0.5)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.restore()


# ------------------------------------------------------------------ icons
def heart(ctx, x, y, s, c=(0.95, 0.35, 0.45), crack=0.0, lw=5):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s / 100, s / 100)
    ctx.move_to(0, 35)
    ctx.curve_to(-60, -5, -55, -60, -25, -60)
    ctx.curve_to(-10, -60, 0, -48, 0, -38)
    ctx.curve_to(0, -48, 10, -60, 25, -60)
    ctx.curve_to(55, -60, 60, -5, 0, 35)
    ctx.close_path()
    fill_stroke(ctx, c, INK, lw * 100 / s)
    if crack > 0:
        ctx.move_to(0, -38)
        ctx.line_to(-8, -18)
        ctx.line_to(6, -6)
        ctx.line_to(-4, 12)
        ctx.line_to(2, 30)
        rgba(ctx, INK, crack)
        ctx.set_line_width(4 * 100 / s)
        ctx.stroke()
    ellipse(ctx, -25, -38, 10, 7)
    rgba(ctx, WHITE, 0.5)
    ctx.fill()
    ctx.restore()


def lock(ctx, x, y, s, c=(1.0, 0.78, 0.25), open_k=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s / 100, s / 100)
    lift = open_k * 18
    ctx.arc(0, -25 - lift, 30, math.pi, 0)
    ctx.line_to(30, -5 - lift)
    rgba(ctx, INK)
    ctx.set_line_width(22)
    ctx.stroke()
    ctx.arc(0, -25 - lift, 30, math.pi, 0)
    ctx.line_to(30, -5 - lift)
    rgba(ctx, (0.75, 0.77, 0.82))
    ctx.set_line_width(12)
    ctx.stroke()
    ctx.move_to(-30, -25 - lift)
    ctx.line_to(-30, -5 - lift)
    rgba(ctx, INK)
    ctx.set_line_width(22)
    ctx.stroke()
    ctx.move_to(-30, -25 - lift)
    ctx.line_to(-30, -5 - lift)
    rgba(ctx, (0.75, 0.77, 0.82))
    ctx.set_line_width(12)
    ctx.stroke()
    rrect(ctx, -48, -12, 96, 78, 14)
    fill_stroke(ctx, c, INK, 6)
    ctx.arc(0, 18, 10, 0, 2 * math.pi)
    rgba(ctx, INK)
    ctx.fill()
    ctx.rectangle(-4, 22, 8, 22)
    ctx.fill()
    ctx.restore()


def bubble(ctx, x, y, w, h, tail=(0, 1), c=WHITE, lw=5, a=1.0, tail_x=0.3):
    """Speech bubble centred at (x, y); tail points toward tail direction."""
    ctx.save()
    if a < 1:
        ctx.push_group()
    rrect(ctx, x - w / 2, y - h / 2, w, h, min(40, h / 2))
    if tail:
        tx = x - w / 2 + w * tail_x
        if tail[1] > 0:
            ctx.move_to(tx - 22, y + h / 2 - 2)
            ctx.line_to(tx + tail[0] * 40 - 10, y + h / 2 + 50)
            ctx.line_to(tx + 26, y + h / 2 - 2)
        else:
            ctx.move_to(tx - 22, y - h / 2 + 2)
            ctx.line_to(tx + tail[0] * 40 - 10, y - h / 2 - 50)
            ctx.line_to(tx + 26, y - h / 2 + 2)
    fill_stroke(ctx, c, INK, lw)
    rrect(ctx, x - w / 2 + 3, y - h / 2 + 3, w - 6, h - 6, min(37, h / 2 - 3))
    rgba(ctx, c)
    ctx.fill()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


def thought(ctx, x, y, w, h, toward=(0, 1), c=WHITE, a=1.0):
    ctx.save()
    ctx.push_group()
    ctx.new_path()
    n = 9
    for i in range(n):
        ang = 2 * math.pi * i / n
        ctx.new_sub_path()
        ctx.arc(x + math.cos(ang) * w * 0.4, y + math.sin(ang) * h * 0.36, min(w, h) * 0.24, 0,
                2 * math.pi)
    ctx.new_sub_path()
    ellipse(ctx, x, y, w * 0.42, h * 0.38)
    fill_stroke(ctx, c, INK, 5)
    for i in range(n):
        ang = 2 * math.pi * i / n
        ctx.arc(x + math.cos(ang) * w * 0.4, y + math.sin(ang) * h * 0.36, min(w, h) * 0.24 - 4,
                0, 2 * math.pi)
        rgba(ctx, c)
        ctx.fill()
    ellipse(ctx, x, y, w * 0.42, h * 0.38)
    rgba(ctx, c)
    ctx.fill()
    for k, r in ((1, 20), (2, 12)):
        bx = x + toward[0] * (w * 0.35 + k * 30)
        by = y + toward[1] * (h * 0.5 + k * 28)
        ctx.arc(bx, by, r, 0, 2 * math.pi)
        fill_stroke(ctx, c, INK, 4)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def bulb(ctx, x, y, s, on=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if on > 0:
        glow(ctx, 0, -10, 120, (1, 0.95, 0.5), 0.7 * on)
        for i in range(8):
            a = i * math.pi / 4
            ctx.move_to(math.cos(a) * 70, -10 + math.sin(a) * 70)
            ctx.line_to(math.cos(a) * 92, -10 + math.sin(a) * 92)
        rgba(ctx, (1, 0.8, 0.2), on)
        ctx.set_line_width(7)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    c = (1, 0.92, 0.45) if on > 0.5 else (0.8, 0.8, 0.82)
    ctx.arc(0, -15, 45, math.pi * 0.8, math.pi * 2.2)
    ctx.line_to(18, 40)
    ctx.line_to(-18, 40)
    ctx.close_path()
    fill_stroke(ctx, c, INK, 5)
    rrect(ctx, -20, 40, 40, 26, 6)
    fill_stroke(ctx, (0.7, 0.72, 0.78), INK, 4.5)
    ctx.move_to(-12, 5)
    ctx.line_to(-5, -10)
    ctx.line_to(5, 5)
    ctx.line_to(12, -10)
    rgba(ctx, INK, 0.6)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def qmark(ctx, x, y, s, c=(0.55, 0.45, 0.95), a=1.0):
    text(ctx, "?", x, y, s, c, outline=INK, olw=8, a=a)


def card(ctx, x, y, w, h, c=WHITE, r=28, lw=5, shadow=True, a=1.0):
    if shadow:
        rrect(ctx, x + 8, y + 10, w, h, r)
        rgba(ctx, (0, 0, 0), 0.14 * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, r)
    fill_stroke(ctx, c, INK, lw, a)


def pill(ctx, s, x, y, size, bg, fg=INK, pad=22, a=1.0, outline=True):
    font(ctx, size)
    w = text_w(ctx, s) + pad * 2
    h = size * 1.45
    rrect(ctx, x - w / 2, y - h / 2, w, h, h / 2)
    fill_stroke(ctx, bg, INK if outline else None, 4.5, a)
    text(ctx, s, x, y + size * 0.36, size, fg, a=a)
    return w


def road_sign(ctx, x, y, s, label, arrows="one", c=(0.2, 0.55, 0.35), a=1.0, flip=0.0):
    """flip in [0,1] squashes the sign horizontally (for a flip animation)."""
    ctx.save()
    ctx.translate(x, y)
    sx = abs(math.cos(flip * math.pi)) if flip else 1
    ctx.scale(s * max(sx, 0.02), s)
    ctx.push_group()
    rrect(ctx, -10, 0, 20, 300, 6)
    fill_stroke(ctx, (0.6, 0.62, 0.68), INK, 4)
    rrect(ctx, -190, -130, 380, 150, 18)
    fill_stroke(ctx, c, INK, 6)
    rrect(ctx, -178, -118, 356, 126, 12)
    rgba(ctx, WHITE)
    ctx.set_line_width(4)
    ctx.stroke()
    text(ctx, label, 0, -70, 42, WHITE)
    if arrows == "one":
        arrow(ctx, -110, -25, 110, -25, WHITE, 10)
    elif arrows == "two":
        arrow(ctx, -110, -38, 110, -38, WHITE, 8, head=18)
        arrow(ctx, 110, -12, -110, -12, WHITE, 8, head=18)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def arrow(ctx, x0, y0, x1, y1, c=INK, lw=8, head=24):
    ang = math.atan2(y1 - y0, x1 - x0)
    ctx.move_to(x0, y0)
    ctx.line_to(x1 - math.cos(ang) * head * 0.6, y1 - math.sin(ang) * head * 0.6)
    rgba(ctx, c)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.move_to(x1, y1)
    ctx.line_to(x1 - math.cos(ang - 0.5) * head, y1 - math.sin(ang - 0.5) * head)
    ctx.line_to(x1 - math.cos(ang + 0.5) * head, y1 - math.sin(ang + 0.5) * head)
    ctx.close_path()
    ctx.fill()


def shield(ctx, x, y, s, c=(0.4, 0.7, 1.0), a=1.0, glow_k=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s / 100, s / 100)
    if glow_k:
        glow(ctx, 0, 0, 180, (0.6, 0.85, 1), 0.6 * glow_k * a)
    ctx.move_to(0, -80)
    ctx.curve_to(30, -60, 60, -62, 70, -60)
    ctx.curve_to(72, 10, 50, 55, 0, 85)
    ctx.curve_to(-50, 55, -72, 10, -70, -60)
    ctx.curve_to(-60, -62, -30, -60, 0, -80)
    ctx.close_path()
    fill_stroke(ctx, c, INK, 6, a)
    ctx.move_to(0, -55)
    ctx.curve_to(20, -42, 40, -42, 48, -42)
    ctx.curve_to(48, 5, 34, 36, 0, 58)
    ctx.close_path()
    rgba(ctx, WHITE, 0.3 * a)
    ctx.fill()
    ctx.restore()


def notebook(ctx, x, y, w, h, lines=(), reveal=1.0, a=1.0, title=None):
    card(ctx, x, y, w, h, (1, 0.99, 0.93), 22, a=a)
    for i in range(12):
        ly = y + 110 + i * 62
        if ly > y + h - 30:
            break
        ctx.move_to(x + 30, ly)
        ctx.line_to(x + w - 30, ly)
    rgba(ctx, (0.6, 0.75, 0.95), 0.5 * a)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.move_to(x + 90, y + 20)
    ctx.line_to(x + 90, y + h - 20)
    rgba(ctx, (0.95, 0.5, 0.5), 0.6 * a)
    ctx.set_line_width(3)
    ctx.stroke()
    for i in range(6):  # spiral rings
        ctx.arc(x + 45 + i * ((w - 90) / 5), y + 4, 12, math.pi, 2 * math.pi)
        rgba(ctx, INK, a)
        ctx.set_line_width(5)
        ctx.stroke()
    if title:
        text(ctx, title, x + w / 2, y + 80, 44, INK, a=a)
    total = sum(len(s) for s in lines) or 1
    shown = reveal * total
    acc = 0
    for i, ln in enumerate(lines):
        n = int(clamp(shown - acc, 0, len(ln)))
        acc += len(ln)
        if n <= 0:
            break
        text(ctx, ln[:n], x + 105, y + 100 + i * 62 - 8 + 62 * (1 if title else 0) - 62 + 62,
             36, (0.15, 0.2, 0.45), align="left", a=a)


def checkbox(ctx, x, y, s, checked=0.0, c=(0.3, 0.75, 0.45)):
    rrect(ctx, x - s / 2, y - s / 2, s, s, s * 0.2)
    fill_stroke(ctx, WHITE, INK, 5)
    if checked > 0:
        k = clamp(checked)
        ctx.move_to(x - s * 0.3, y)
        pts = [(x - s * 0.3, y), (x - s * 0.08, y + s * 0.25), (x + s * 0.35, y - s * 0.3)]
        if k < 0.5:
            e = lerp(pts[0][0], pts[1][0], k * 2), lerp(pts[0][1], pts[1][1], k * 2)
            ctx.line_to(*e)
        else:
            ctx.line_to(*pts[1])
            ctx.line_to(lerp(pts[1][0], pts[2][0], (k - 0.5) * 2),
                        lerp(pts[1][1], pts[2][1], (k - 0.5) * 2))
        rgba(ctx, c)
        ctx.set_line_width(s * 0.16)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def target(ctx, x, y, r, a=1.0):
    for i, c in enumerate(((0.95, 0.35, 0.35), WHITE, (0.95, 0.35, 0.35), WHITE, (0.95, 0.35, 0.35))):
        ctx.arc(x, y, r * (1 - i * 0.2), 0, 2 * math.pi)
        rgba(ctx, c, a)
        ctx.fill()


def gauge(ctx, x, y, r, val, label="", a=1.0):
    ctx.arc(x, y, r, math.pi, 2 * math.pi)
    ctx.close_path()
    fill_stroke(ctx, WHITE, INK, 5, a)
    for i, c in enumerate(((0.45, 0.8, 0.5), (1, 0.8, 0.3), (0.95, 0.4, 0.35))):
        ctx.arc(x, y, r * 0.8, math.pi + i * math.pi / 3, math.pi + (i + 1) * math.pi / 3)
        rgba(ctx, c, a)
        ctx.set_line_width(r * 0.18)
        ctx.stroke()
    ang = math.pi + clamp(val) * math.pi
    ctx.move_to(x, y)
    ctx.line_to(x + math.cos(ang) * r * 0.72, y + math.sin(ang) * r * 0.72)
    rgba(ctx, INK, a)
    ctx.set_line_width(8)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.arc(x, y, 12, 0, 2 * math.pi)
    ctx.fill()
    if label:
        text(ctx, label, x, y + 50, 34, INK, a=a)


def flame(ctx, x, y, s, t, a=1.0):
    if s <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k, c in ((1.0, (1, 0.5, 0.2)), (0.65, (1, 0.8, 0.3)), (0.35, (1, 0.97, 0.75))):
        w = 50 * k
        h = 130 * k * (1 + 0.08 * math.sin(t * 13 + k))
        ctx.move_to(0, 0)
        ctx.curve_to(-w * 1.2, -h * 0.2, -w * 0.4, -h * 0.6, math.sin(t * 9) * 8, -h)
        ctx.curve_to(w * 0.5, -h * 0.6, w * 1.2, -h * 0.2, 0, 0)
        fill_stroke(ctx, c, INK if k == 1.0 else None, 4, a)
    ctx.restore()


def phone(ctx, x, y, w, h, screen=(1, 1, 1)):
    rrect(ctx, x, y, w, h, 60)
    fill_stroke(ctx, (0.18, 0.18, 0.25), INK, 6)
    rrect(ctx, x + 22, y + 22, w - 44, h - 44, 42)
    rgba(ctx, screen)
    ctx.fill()
    rrect(ctx, x + w / 2 - 70, y + 34, 140, 26, 13)
    rgba(ctx, (0.18, 0.18, 0.25))
    ctx.fill()


def avatar(ctx, x, y, r, c, emo_smile=0.4, ring=True):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    fill_stroke(ctx, c, INK, 4)
    for s in (-1, 1):
        ellipse(ctx, x + s * r * 0.32, y - r * 0.1, r * 0.17, r * 0.22)
        rgba(ctx, WHITE)
        ctx.fill()
        ellipse(ctx, x + s * r * 0.32, y - r * 0.06, r * 0.09, r * 0.11)
        rgba(ctx, INK)
        ctx.fill()
    ctx.move_to(x - r * 0.3, y + r * 0.35 - emo_smile * r * 0.1)
    ctx.curve_to(x - r * 0.1, y + r * 0.35 + emo_smile * r * 0.2, x + r * 0.1,
                 y + r * 0.35 + emo_smile * r * 0.2, x + r * 0.3, y + r * 0.35 - emo_smile * r * 0.1)
    rgba(ctx, INK)
    ctx.set_line_width(max(2.5, r * 0.09))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def painting(ctx, x, y, w, h):
    rrect(ctx, x, y, w, h, 18)
    ctx.set_source(vgrad(ctx, y, y + h, [(0, (0.55, 0.8, 1)), (1, (1, 0.85, 0.7))]))
    ctx.fill()
    ctx.save()
    rrect(ctx, x, y, w, h, 18)
    ctx.clip()
    ctx.arc(x + w * 0.72, y + h * 0.35, h * 0.14, 0, 2 * math.pi)
    rgba(ctx, (1, 0.85, 0.3))
    ctx.fill()
    ctx.move_to(x, y + h)
    ctx.line_to(x + w * 0.3, y + h * 0.45)
    ctx.line_to(x + w * 0.55, y + h * 0.8)
    ctx.line_to(x + w * 0.75, y + h * 0.55)
    ctx.line_to(x + w, y + h * 0.9)
    ctx.line_to(x + w, y + h)
    ctx.close_path()
    rgba(ctx, (0.4, 0.68, 0.45))
    ctx.fill()
    ctx.restore()
    rrect(ctx, x, y, w, h, 18)
    rgba(ctx, INK)
    ctx.set_line_width(4)
    ctx.stroke()


# ------------------------------------------------------------------ indoor
def office_wall(ctx, c=(0.86, 0.9, 0.95)):
    ctx.set_source(vgrad(ctx, 0, H, [(0, c), (1, shade(c, -0.08))]))
    ctx.paint()


def city_window(ctx, x, y, w, h, t, night=False):
    rrect(ctx, x - 14, y - 14, w + 28, h + 28, 16)
    fill_stroke(ctx, (0.95, 0.96, 0.98), INK, 5)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    top, bot = ((0.15, 0.18, 0.38), (0.32, 0.3, 0.55)) if night else ((0.6, 0.82, 1), (0.9, 0.95, 1))
    ctx.set_source(vgrad(ctx, y, y + h, [(0, top), (1, bot)]))
    ctx.paint()
    bx = x
    i = 0
    while bx < x + w:
        bw = 60 + (i * 37) % 50
        bh = 120 + (i * 71) % 160
        ctx.rectangle(bx, y + h - bh, bw - 8, bh)
        rgba(ctx, (0.45, 0.55, 0.72) if not night else (0.12, 0.13, 0.25))
        ctx.fill()
        for wy in range(int(y + h - bh + 15), int(y + h - 10), 30):
            for wx in range(int(bx + 10), int(bx + bw - 18), 20):
                lit = ((wx * 7 + wy * 13) % 5 == 0)
                ctx.rectangle(wx, wy, 9, 14)
                rgba(ctx, (1, 0.9, 0.6) if (night and lit) else (0.75, 0.85, 0.95), 0.9 if night and lit else 0.5)
                ctx.fill()
        bx += bw
        i += 1
    ctx.restore()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    rgba(ctx, (0.95, 0.96, 0.98))
    ctx.set_line_width(12)
    ctx.stroke()


def table(ctx, y, h=300, c=(0.72, 0.5, 0.33)):
    rrect(ctx, -20, y, W + 40, 60, 16)
    fill_stroke(ctx, shade(c, 0.1), INK, 6)
    ctx.rectangle(-20, y + 56, W + 40, h)
    ctx.set_source(vgrad(ctx, y, y + h, [(0, c), (1, shade(c, -0.3))]))
    ctx.fill()


def mug(ctx, x, y, c=(0.95, 0.5, 0.45)):
    rrect(ctx, x - 28, y - 60, 56, 60, 10)
    fill_stroke(ctx, c, INK, 4.5)
    ctx.arc(x + 32, y - 32, 15, -math.pi / 2, math.pi / 2)
    rgba(ctx, INK)
    ctx.set_line_width(7)
    ctx.stroke()


def laptop(ctx, x, y, s=1.0, glow_c=(0.7, 0.85, 1)):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-110, 0)
    ctx.line_to(-90, -150)
    ctx.line_to(90, -150)
    ctx.line_to(110, 0)
    ctx.close_path()
    fill_stroke(ctx, (0.75, 0.77, 0.82), INK, 5)
    ctx.arc(0, -78, 14, 0, 2 * math.pi)
    rgba(ctx, WHITE, 0.7)
    ctx.fill()
    rrect(ctx, -130, -6, 260, 16, 6)
    fill_stroke(ctx, (0.65, 0.67, 0.72), INK, 5)
    ctx.restore()


def monitor(ctx, x, y, s=1.0, screen=(0.6, 0.8, 1.0), back=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -20, -60, 40, 60, 6)
    fill_stroke(ctx, (0.4, 0.42, 0.5), INK, 4)
    rrect(ctx, -150, -250, 300, 195, 14)
    fill_stroke(ctx, (0.3, 0.32, 0.4), INK, 5)
    if not back:
        rrect(ctx, -136, -236, 272, 167, 8)
        rgba(ctx, screen)
        ctx.fill()
    ctx.restore()


def whiteboard(ctx, x, y, w, h, t=0.0):
    card(ctx, x, y, w, h, (0.98, 0.98, 1), 10, shadow=False)
    bars = (0.4, 0.65, 0.5, 0.85)
    for i, b in enumerate(bars):
        bh = (h - 80) * b
        ctx.rectangle(x + 40 + i * (w - 80) / 4, y + h - 30 - bh, (w - 80) / 4 - 20, bh)
        rgba(ctx, ((0.4, 0.7, 1), (1, 0.6, 0.5), (0.5, 0.8, 0.5), (1, 0.8, 0.35))[i])
        ctx.fill()


def framed_picture(ctx, x, y, w, h, kind=0):
    rrect(ctx, x, y, w, h, 8)
    fill_stroke(ctx, (0.85, 0.65, 0.45), INK, 5)
    rrect(ctx, x + 14, y + 14, w - 28, h - 28, 4)
    rgba(ctx, ((0.7, 0.85, 1), (1, 0.9, 0.7), (0.8, 0.95, 0.8))[kind % 3])
    ctx.fill()
    if kind % 3 == 0:
        ctx.move_to(x + 14, y + h - 14)
        ctx.line_to(x + w * 0.45, y + h * 0.45)
        ctx.line_to(x + w - 14, y + h - 14)
        rgba(ctx, (0.45, 0.7, 0.5))
        ctx.fill()
    else:
        ctx.arc(x + w / 2, y + h / 2, min(w, h) * 0.2, 0, 2 * math.pi)
        rgba(ctx, (1, 0.6, 0.5) if kind % 3 == 1 else (0.5, 0.6, 1))
        ctx.fill()


def office_door(ctx, x, y, w, h, open_k, inside=None, label="M. MARSH", sub="MANAGER", sign=True):
    """Door whose hinge is on the right; inside(ctx) draws the room behind it."""
    rrect(ctx, x - 16, y - 16, w + 32, h + 16, 12)
    fill_stroke(ctx, (0.95, 0.95, 0.97), INK, 6)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.set_source(vgrad(ctx, y, y + h, [(0, (0.98, 0.92, 0.8)), (1, (0.85, 0.78, 0.68))]))
    ctx.paint()
    if inside:
        inside(ctx)
    ctx.restore()
    k = clamp(open_k)
    dw = w * (1 - 0.88 * k)
    dx = x + w - dw
    ctx.move_to(dx, y + k * 20)
    ctx.line_to(x + w, y)
    ctx.line_to(x + w, y + h)
    ctx.line_to(dx, y + h - k * 12)
    ctx.close_path()
    col = (0.62, 0.45, 0.32)
    fill_stroke(ctx, shade(col, -0.15 * k), INK, 6)
    if k < 0.5:
        a = 1 - k * 2
        sx = dw / w
        rrect(ctx, dx + 50 * sx, y + 70, (w - 100) * sx, 70, 8)
        fill_stroke(ctx, (0.92, 0.8, 0.45), INK, 4, a)
        if sx > 0.6:
            text(ctx, label, dx + dw / 2, y + 102, 30, INK, a=a)
            text(ctx, sub, dx + dw / 2, y + 130, 20, INK, a=a)
        if sign and sx > 0.6:
            ctx.save()
            ctx.translate(dx + dw / 2, y + 260)
            ctx.rotate(0.04)
            rrect(ctx, -110, -40, 220, 120, 10)
            fill_stroke(ctx, WHITE, INK, 4, a)
            text(ctx, "My door is", 0, 4, 28, INK, a=a)
            text(ctx, "ALWAYS OPEN!", 0, 42, 30, (0.85, 0.3, 0.35), a=a)
            ctx.restore()
        ctx.arc(dx + 40 * sx, y + h * 0.55, 14, 0, 2 * math.pi)
        fill_stroke(ctx, (1, 0.82, 0.3), INK, 4, a)


def corridor(ctx, t, c=(0.82, 0.84, 0.92)):
    ctx.set_source(vgrad(ctx, 0, H, [(0, shade(c, -0.15)), (1, shade(c, 0.05))]))
    ctx.paint()
    vx, vy = 540, 640
    # floor
    ctx.move_to(0, 1330)
    ctx.line_to(vx - 120, vy + 120)
    ctx.line_to(vx + 120, vy + 120)
    ctx.line_to(W, 1330)
    ctx.line_to(W, H)
    ctx.line_to(0, H)
    ctx.close_path()
    rgba(ctx, (0.66, 0.62, 0.72))
    ctx.fill()
    # ceiling
    ctx.move_to(0, 180)
    ctx.line_to(vx - 120, vy - 120)
    ctx.line_to(vx + 120, vy - 120)
    ctx.line_to(W, 180)
    ctx.line_to(W, 0)
    ctx.line_to(0, 0)
    ctx.close_path()
    rgba(ctx, shade(c, -0.25))
    ctx.fill()
    ctx.rectangle(vx - 120, vy - 120, 240, 240)
    rgba(ctx, (0.25, 0.25, 0.35))
    ctx.fill()
    for p in ((0, 180), (0, 1330), (W, 180), (W, 1330)):
        ctx.move_to(*p)
        ctx.line_to(vx + (-120 if p[0] == 0 else 120), vy + (-120 if p[1] < 600 else 120))
    rgba(ctx, INK, 0.5)
    ctx.set_line_width(4)
    ctx.stroke()


def corridor_doors(ctx, labels):
    """Doors in perspective along both walls; returns (x, y, scale) for each lock."""
    spots = []
    vx, vy = 540, 640

    def wall(side, d):
        # d: 0 = near (screen edge) .. 1 = far (back wall)
        e = 1 - 1 / (1 + 3.0 * d)
        e /= 1 - 1 / 4.0
        x = lerp(0 if side < 0 else W, vx + side * 120, e)
        top = lerp(180, vy - 120, e)
        bot = lerp(1330, vy + 120, e)
        return x, top, bot

    slots = [(0.12, 0.30), (0.45, 0.6), (0.72, 0.8)]
    for i, lab in enumerate(labels):
        side = -1 if i % 2 == 0 else 1
        d1, d2 = slots[i // 2]
        x1, t1, b1 = wall(side, d1)
        x2, t2, b2 = wall(side, d2)
        y1t, y2t = lerp(t1, b1, 0.24), lerp(t2, b2, 0.24)
        ctx.move_to(x1, y1t)
        ctx.line_to(x2, y2t)
        ctx.line_to(x2, b2 - 4)
        ctx.line_to(x1, b1 - 4)
        ctx.close_path()
        fill_stroke(ctx, (0.55, 0.42, 0.35), INK, 4 * (b1 - t1) / 1150 + 1.5)
        k = (b1 - y1t + b2 - y2t) / 2 / 870
        cx, cy = (x1 + x2) / 2, (y1t + y2t) / 2
        ctx.save()
        ctx.translate(cx, cy + 40 * k)
        ctx.scale(1, 1)
        text(ctx, lab, 0, 0, max(14, 46 * k), WHITE, outline=INK, olw=max(3, 8 * k))
        ctx.restore()
        spots.append((cx, (y1t + b1 + y2t + b2) / 4 + 30 * k, k))
    return spots


def toolbox(ctx, x, y, s, open_k=0.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if open_k > 0:
        glow(ctx, 0, -120, 320, (1, 0.95, 0.6), 0.8 * open_k)
    # lid
    ctx.save()
    ctx.translate(-170, -150)
    ctx.rotate(-open_k * 1.9)
    rrect(ctx, 0, -50, 340, 60, 16)
    fill_stroke(ctx, (0.25, 0.65, 0.65), INK, 6)
    ctx.restore()
    rrect(ctx, -180, -150, 360, 200, 22)
    fill_stroke(ctx, (0.92, 0.35, 0.35), INK, 6)
    rrect(ctx, -40, -190, 80, 40, 12)
    rgba(ctx, INK)
    ctx.set_line_width(10)
    ctx.stroke()
    rrect(ctx, -30, -60, 60, 36, 8)
    fill_stroke(ctx, (1, 0.8, 0.3), INK, 4)
    ctx.restore()


def lens_icon(ctx, x, y, r, num, c, a=1.0):
    ctx.save()
    ctx.push_group()
    ctx.move_to(x + r * 0.65, y + r * 0.65)
    ctx.line_to(x + r * 1.25, y + r * 1.25)
    rgba(ctx, INK)
    ctx.set_line_width(r * 0.35)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.move_to(x + r * 0.65, y + r * 0.65)
    ctx.line_to(x + r * 1.25, y + r * 1.25)
    rgba(ctx, (0.6, 0.45, 0.35))
    ctx.set_line_width(r * 0.2)
    ctx.stroke()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    fill_stroke(ctx, c, INK, 5)
    ctx.arc(x, y, r * 0.78, 0, 2 * math.pi)
    rgba(ctx, WHITE, 0.55)
    ctx.fill()
    text(ctx, str(num), x, y + r * 0.32, r * 0.9, INK)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def scribble_ball(ctx, x, y, r, t, c=(0.55, 0.35, 0.65)):
    ctx.save()
    ctx.translate(x, y)
    ctx.move_to(r, 0)
    for i in range(1, 120):
        a = i * 0.55 + t * 2
        rr = r * (0.55 + 0.45 * math.sin(i * 1.7 + t))
        ctx.line_to(math.cos(a) * rr, math.sin(a) * rr)
    rgba(ctx, c)
    ctx.set_line_width(5)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.restore()


def envelope_card(ctx, x, y, w, h, a=1.0):
    card(ctx, x, y, w, h, WHITE, 26, a=a)


def pin(ctx, x, y, s, c=(0.95, 0.35, 0.35), a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(0, 0)
    ctx.curve_to(-30, -40, -30, -75, 0, -75)
    ctx.curve_to(30, -75, 30, -40, 0, 0)
    fill_stroke(ctx, c, INK, 4.5, a)
    ctx.arc(0, -50, 11, 0, 2 * math.pi)
    rgba(ctx, WHITE, a)
    ctx.fill()
    ctx.restore()


def weather_cloud(ctx, x, y, s, t, rain=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for i in range(7):
        rx = -70 + i * 23
        ry = 40 + ((t * 300 + i * 37) % 120)
        ctx.move_to(rx, ry)
        ctx.line_to(rx - 6, ry + 22)
        rgba(ctx, (0.45, 0.65, 0.95), rain * (1 - ((t * 300 + i * 37) % 120) / 120))
        ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    ctx.new_path()
    for cx, cy, r in ((-60, 10, 42), (-15, -18, 55), (40, -5, 48), (78, 16, 34), (10, 20, 45)):
        ctx.new_sub_path()
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    fill_stroke(ctx, (0.6, 0.63, 0.72), INK, 5)
    for cx, cy, r in ((-60, 10, 37), (-15, -18, 50), (40, -5, 43), (78, 16, 29), (10, 20, 40)):
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        rgba(ctx, (0.6, 0.63, 0.72))
        ctx.fill()
    ctx.restore()


def ramp_road(ctx, t, sign_label="OPTIONS", sign_k=1.0):
    ground(ctx, 900, (0.55, 0.8, 0.5))
    # main road
    ctx.move_to(-50, 1250)
    ctx.line_to(W + 50, 1000)
    ctx.line_to(W + 50, 1110)
    ctx.line_to(-50, 1360)
    ctx.close_path()
    fill_stroke(ctx, (0.45, 0.46, 0.52), INK, 5)
    # exit ramp
    ctx.move_to(380, 1170)
    ctx.curve_to(600, 1060, 760, 930, 1100, 820)
    ctx.line_to(1100, 900)
    ctx.curve_to(780, 1010, 640, 1130, 480, 1220)
    ctx.close_path()
    fill_stroke(ctx, (0.5, 0.51, 0.57), INK, 5)
    for i in range(8):
        x0 = -50 + i * 160
        ctx.move_to(x0, 1305 - i * 160 * 250 / 1180)
        ctx.line_to(x0 + 70, 1305 - (i * 160 + 70) * 250 / 1180)
    rgba(ctx, (1, 0.9, 0.4))
    ctx.set_line_width(8)
    ctx.stroke()


def piggy(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ellipse(ctx, 0, 0, 80, 60)
    fill_stroke(ctx, (1, 0.7, 0.75), INK, 5)
    ellipse(ctx, 75, 5, 20, 22)
    fill_stroke(ctx, (1, 0.6, 0.68), INK, 4)
    for dx in (-40, 30):
        rrect(ctx, dx, 45, 20, 30, 6)
        fill_stroke(ctx, (1, 0.7, 0.75), INK, 4)
    ctx.move_to(-20, -55)
    ctx.line_to(-5, -85)
    ctx.line_to(10, -55)
    fill_stroke(ctx, (1, 0.6, 0.68), INK, 4)
    ctx.arc(35, -15, 6, 0, 2 * math.pi)
    rgba(ctx, INK)
    ctx.fill()
    rrect(ctx, -25, -62, 40, 8, 4)
    ctx.fill()
    ctx.restore()


def doc_icon(ctx, x, y, s, title="RESUME"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    card(ctx, -60, -80, 120, 160, WHITE, 12, shadow=False)
    ctx.arc(0, -40, 18, 0, 2 * math.pi)
    rgba(ctx, (0.4, 0.7, 0.9))
    ctx.fill()
    for i in range(4):
        ctx.rectangle(-40, -5 + i * 20, 80 - (i % 2) * 20, 8)
        rgba(ctx, (0.7, 0.72, 0.8))
        ctx.fill()
    ctx.restore()


def network_icon(ctx, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    pts = [(0, -60), (-60, 30), (60, 30), (0, 0)]
    for a, b in ((0, 3), (1, 3), (2, 3), (0, 1), (0, 2), (1, 2)):
        ctx.move_to(*pts[a])
        ctx.line_to(*pts[b])
    rgba(ctx, INK)
    ctx.set_line_width(5)
    ctx.stroke()
    for i, (px, py) in enumerate(pts):
        ctx.arc(px, py, 24, 0, 2 * math.pi)
        fill_stroke(ctx, ((0.95, 0.6, 0.45), (0.3, 0.75, 0.68), (0.55, 0.5, 0.75), (1, 0.8, 0.3))[i], INK, 4)
    ctx.restore()


def flag_icon(ctx, x, y, s, c=(0.95, 0.4, 0.35)):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-30, 60)
    ctx.line_to(-30, -60)
    rgba(ctx, INK)
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.move_to(-30, -60)
    ctx.curve_to(0, -75, 20, -40, 50, -55)
    ctx.line_to(50, -5)
    ctx.curve_to(20, 10, 0, -25, -30, -10)
    ctx.close_path()
    fill_stroke(ctx, c, INK, 5)
    ctx.restore()


def camera_icon(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -60, -40, 120, 85, 16)
    fill_stroke(ctx, (0.35, 0.37, 0.45), INK, 5)
    rrect(ctx, -25, -55, 50, 20, 6)
    fill_stroke(ctx, (0.35, 0.37, 0.45), INK, 4)
    ctx.arc(0, 2, 26, 0, 2 * math.pi)
    fill_stroke(ctx, (0.6, 0.8, 1), INK, 5)
    ctx.restore()


def mute_icon(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-50, -20)
    ctx.line_to(-25, -20)
    ctx.line_to(5, -50)
    ctx.line_to(5, 50)
    ctx.line_to(-25, 20)
    ctx.line_to(-50, 20)
    ctx.close_path()
    fill_stroke(ctx, (0.55, 0.6, 0.75), INK, 5)
    ctx.move_to(25, -25)
    ctx.line_to(60, 25)
    ctx.move_to(60, -25)
    ctx.line_to(25, 25)
    rgba(ctx, (0.9, 0.3, 0.35))
    ctx.set_line_width(10)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.restore()


def scales_icon(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(0, -70)
    ctx.line_to(0, 60)
    ctx.move_to(-70, -45)
    ctx.line_to(70, -45)
    ctx.move_to(-40, 60)
    ctx.line_to(40, 60)
    rgba(ctx, INK)
    ctx.set_line_width(8)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    for sx in (-70, 70):
        ctx.move_to(sx, -45)
        ctx.line_to(sx - 25, 5)
        ctx.move_to(sx, -45)
        ctx.line_to(sx + 25, 5)
        rgba(ctx, INK)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.arc(sx, 5, 28, 0, math.pi)
        ctx.close_path()
        fill_stroke(ctx, (1, 0.8, 0.3), INK, 4)
    ctx.restore()


def open_door_light(ctx, x, y, w, h, k, t):
    """A doorway with warm light pouring out (k = how open)."""
    glow(ctx, x + w / 2, y + h * 0.6, 520 * k + 1, (1, 0.9, 0.55), 0.6 * k)
    rrect(ctx, x - 18, y - 18, w + 36, h + 18, 18)
    fill_stroke(ctx, (0.95, 0.95, 0.97), INK, 6)
    ctx.rectangle(x, y, w, h)
    ctx.set_source(vgrad(ctx, y, y + h, [(0, (1, 0.97, 0.8)), (1, (1, 0.85, 0.55))]))
    ctx.fill()
    # light spill on the floor
    ctx.move_to(x, y + h)
    ctx.line_to(x + w, y + h)
    ctx.line_to(x + w + 200 * k, y + h + 160)
    ctx.line_to(x - 200 * k, y + h + 160)
    ctx.close_path()
    rgba(ctx, (1, 0.92, 0.6), 0.45 * k)
    ctx.fill()
    dw = w * (1 - 0.85 * k)
    ctx.move_to(x, y)
    ctx.line_to(x + dw, y + 30 * k)
    ctx.line_to(x + dw, y + h - 20 * k)
    ctx.line_to(x, y + h)
    ctx.close_path()
    fill_stroke(ctx, (0.9, 0.55, 0.35), INK, 6)
