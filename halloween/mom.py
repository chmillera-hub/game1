"""Mom: tall, tired, tender. A gothic-storybook puppet with a striped robe,
hair curlers (horns, in silhouette) and bat slippers.

Local units: face centre at (0, 0); face ~300 units tall.
"""
import math

import skia

from gfx import (Xf, circle, clamp, ellipse, fill, lerp, lin_grad, open_path, rad_grad, smooth_path,
                 spiral_pts, stroke)

SKIN = (240, 214, 196)
SKIN_SH = (196, 150, 150)
HAIR = (48, 28, 42)
HAIR_HI = (96, 62, 84)
LIP = (186, 86, 98)
IRIS = (92, 70, 48)
LASH = (24, 14, 20)
ROBE_A = (150, 128, 176)
ROBE_B = (58, 38, 82)
COLLAR = (206, 192, 220)
CURLERS = [(196, 166, 226), (236, 150, 182), (150, 212, 192)]
SIL = (6, 5, 10)

DEFAULT = dict(
    x=0.0, y=0.0, scale=1.0, alpha=1.0, full=False,
    tilt=0.0, turn=0.0, nod=0.0, lean=0.0,
    look=(0.0, 0.0), lid=0.0, lid_low=0.0, lid_tilt=0.0, closed_curve=0.0,
    brow=0.0, brow_tilt=0.0,
    mouth=0.0, mround=0.0, mwide=0.0, mclosed=0.0, smile=0.0,
    glisten=0.0, tear=0.0, blush=0.0,
    arms="down",       # down / candle / hold / hug / pin / hold_low
    paper=None,        # callable(c) drawing the held paper, in hand space
    candle=0.0,        # candle flame flicker phase; <0 no candle
    sil=False,         # silhouette only (for shadows)
    walk=0.0, walking=0.0,
    breathe=0.0,
    warm=0.6,          # warm underlight amount
    seed=0,
)


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


def face_path():
    return smooth_path([(0, -158), (78, -142), (110, -86), (112, -10), (96, 64), (62, 122), (22, 156), (0, 160),
                        (-22, 156), (-62, 122), (-96, 64), (-112, -10), (-110, -86), (-78, -142)])


def draw_eye(c, P, side, ex, ey):
    w, h = 47, 26
    lid = clamp(P["lid"])
    low = clamp(P["lid_low"])
    lx, ly = P["look"]
    # tired shadow under the eye
    c.drawOval(skia.Rect.MakeLTRB(ex - 46, ey + 4, ex + 46, ey + 40),
               fill((120, 80, 120), 1.0, rad_grad((ex, ey + 20), 46, [(120, 80, 120, 0.30), (120, 80, 120, 0)])))
    eye = skia.Path()
    outer = side * w
    eye.moveTo(ex - w * side, ey + 2)
    eye.cubicTo(ex - w * 0.45 * side, ey - h * 1.25, ex + w * 0.55 * side, ey - h * 1.2, ex + outer, ey - 6)
    eye.cubicTo(ex + w * 0.5 * side, ey + h * 0.95, ex - w * 0.5 * side, ey + h * 0.95, ex - w * side, ey + 2)
    eye.close()
    c.drawPath(eye, fill((248, 242, 236)))
    c.save()
    c.clipPath(eye, skia.ClipOp.kIntersect, True)
    ix, iy = ex + lx * 15, ey + ly * 9 - 2
    c.drawCircle(ix, iy, 20.5, fill(IRIS, 1.0, rad_grad((ix, iy), 20.5, [(140, 112, 70), IRIS, (40, 28, 22)], [0, 0.6, 1])))
    c.drawCircle(ix, iy, 9.5, fill((10, 6, 8)))
    c.drawCircle(ix - 7, iy - 8, 5.2, fill((255, 255, 255), 0.95))
    c.drawCircle(ix + 5, iy + 6, 2.0, fill((255, 255, 255), 0.7))
    if P["glisten"] > 0:
        g = P["glisten"]
        c.drawPath(open_path([(ex - w * 0.8, ey + 12), (ex, ey + 18), (ex + w * 0.8, ey + 12)]),
                   stroke((210, 235, 255), 4, 0.75 * g))
        c.drawCircle(ix + 7, iy - 2, 3.4, fill((255, 255, 255), 0.85 * g))
    tilt = P["lid_tilt"] * side
    # upper lid (skin) closing
    edge = ey - h * 1.25 + (lid + max(0.0, ly) * 0.25) * (h * 2.3)
    lp = skia.Path()
    lp.moveTo(ex - w - 10, ey - 60)
    lp.lineTo(ex + w + 10, ey - 60)
    lp.lineTo(ex + w + 10, edge + tilt * 10)
    lp.quadTo(ex, edge + 10 * (1 - lid), ex - w - 10, edge - tilt * 10)
    lp.close()
    c.drawPath(lp, fill(SKIN))
    c.drawPath(lp, fill(SKIN_SH, 0.25))
    if low > 0.001:
        e2 = ey + h + 2 - low * h * 1.1
        bp = skia.Path()
        bp.moveTo(ex - w - 10, ey + 50)
        bp.lineTo(ex + w + 10, ey + 50)
        bp.lineTo(ex + w + 10, e2)
        bp.quadTo(ex, e2 - 10 * low, ex - w - 10, e2)
        bp.close()
        c.drawPath(bp, fill(SKIN))
    c.restore()
    # lash line follows the upper lid edge
    k = clamp(lid + max(0.0, ly) * 0.25)
    if k < 0.95:
        top_y = lerp(ey - h * 1.22, ey + 4, k)
        lash = skia.Path()
        lash.moveTo(ex - w * side, ey + 2 - k * 2)
        lash.quadTo(ex, top_y - 4 + tilt * 0, ex + outer + side * 4, ey - 8 + k * 6)
        c.drawPath(lash, stroke(LASH, 5.5))
        for j in range(3):  # gothic lash flicks at the outer corner
            bx = ex + outer * (0.55 + j * 0.2)
            by = lerp(ey - h * 1.05, ey - 4, k) + j * 4
            c.drawLine(bx, by, bx + side * (10 + j * 3), by - 12 + j * 2, stroke(LASH, 2.6))
        crease = skia.Path()
        crease.moveTo(ex - w * 0.8 * side, ey - h * 1.4)
        crease.quadTo(ex, ey - h * 2.1, ex + w * 0.9 * side, ey - h * 1.2)
        c.drawPath(crease, stroke(SKIN_SH, 2.2, 0.6))
    else:
        cc = P["closed_curve"]
        p = skia.Path()
        p.moveTo(ex - w * side, ey + 2)
        p.quadTo(ex, ey + 10 - cc * 14, ex + outer + side * 4, ey - 4)
        c.drawPath(p, stroke(LASH, 4.5))
        for j in range(3):
            bx = ex + outer * (0.45 + j * 0.22)
            c.drawLine(bx, ey + 4, bx + side * 8, ey + 14, stroke(LASH, 2.2))
    c.drawPath(open_path([(ex - w * 0.6 * side, ey + h * 0.9), (ex + w * 0.2 * side, ey + h * 1.05),
                          (ex + w * 0.85 * side, ey + 4)]), stroke(SKIN_SH, 1.8, 0.7))
    if P["tear"] > 0:
        tp = P["tear"]
        tx = ex + outer * 0.75
        ty = ey + 18 + tp * 120
        a = clamp(1.4 - tp * 1.2)
        drop = smooth_path([(tx, ty - 10), (tx + 6, ty + 3), (tx, ty + 9), (tx - 6, ty + 3)])
        c.drawPath(drop, fill((215, 236, 255), 0.85 * a))
        c.drawPath(open_path([(tx, ey + 22), (tx + 1, ty - 8)]), stroke((220, 236, 255), 2.4, 0.45 * a))


def draw_brow(c, P, side, ex, ey):
    by = ey - 52 - P["brow"] * 16
    t = P["brow_tilt"]
    p = skia.Path()
    inner = (ex - side * 30, by + 8 - t * 14)
    peak = (ex + side * 8, by - 8 - t * 2)
    outer = (ex + side * 46, by + 10 + t * 6)
    p.moveTo(*inner)
    p.quadTo(peak[0], peak[1], outer[0], outer[1])
    c.drawPath(p, stroke(HAIR, 6.5))
    c.drawPath(p, stroke(HAIR_HI, 2.0, 0.6))


def draw_mouth(c, P):
    mx, my = P["turn"] * 10, 92
    op = clamp(P["mouth"]) * (1 - clamp(P["mclosed"]))
    wide, rnd, sm = clamp(P["mwide"]), clamp(P["mround"]), P["smile"]
    w = 29 * (1 + 0.25 * wide - 0.3 * rnd) + 4 * max(0, sm)
    cy = -sm * 7
    if op > 0.04:
        h = 6 + 30 * op
        mp = skia.Path()
        mp.moveTo(mx - w, my + cy)
        mp.cubicTo(mx - w * 0.5, my - 6, mx + w * 0.5, my - 6, mx + w, my + cy)
        mp.cubicTo(mx + w * 0.6, my + h, mx - w * 0.6, my + h, mx - w, my + cy)
        mp.close()
        c.drawPath(mp, fill((70, 24, 34)))
        c.save()
        c.clipPath(mp, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeLTRB(mx - w, my - 10, mx + w, my + 2 + 3 * (1 - op)), fill((244, 240, 232)))
        c.drawOval(skia.Rect.MakeLTRB(mx - w * 0.6, my + h * 0.55, mx + w * 0.6, my + h * 1.2), fill((190, 90, 100)))
        c.restore()
        # lips
        c.drawPath(mp, stroke(LIP, 7))
        up = skia.Path()
        up.moveTo(mx - w - 2, my + cy)
        up.cubicTo(mx - w * 0.4, my - 12, mx - 6, my - 10, mx, my - 6)
        up.cubicTo(mx + 6, my - 10, mx + w * 0.4, my - 12, mx + w + 2, my + cy)
        c.drawPath(up, stroke(LIP, 5))
    else:
        # closed: soft upper lip + lower lip with a gentle line
        lip = skia.Path()
        lip.moveTo(mx - w, my + cy)
        lip.cubicTo(mx - w * 0.45, my - 11, mx - 7, my - 9, mx, my - 5)
        lip.cubicTo(mx + 7, my - 9, mx + w * 0.45, my - 11, mx + w, my + cy)
        lip.cubicTo(mx + w * 0.5, my + 16 - sm * 3, mx - w * 0.5, my + 16 - sm * 3, mx - w, my + cy)
        lip.close()
        c.drawPath(lip, fill(LIP))
        line = skia.Path()
        line.moveTo(mx - w, my + cy)
        line.quadTo(mx, my + 3 + sm * 5, mx + w, my + cy)
        c.drawPath(line, stroke((110, 40, 54), 2.6))
        c.drawPath(open_path([(mx - w * 0.3, my + 9), (mx + w * 0.3, my + 9)]), stroke((236, 170, 170), 2.4, 0.5))
    if sm > 0.3:  # smile creases
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(mx + side * (w + 4), my + cy - 10)
            p.quadTo(mx + side * (w + 12), my + cy, mx + side * (w + 6), my + cy + 12)
            c.drawPath(p, stroke(SKIN_SH, 2.2, 0.55 * (sm - 0.3) / 0.7))


def draw_hair_back(c, P):
    c.drawPath(smooth_path([(-120, -40), (-150, -170), (-60, -250), (60, -252), (150, -170), (124, -40),
                            (132, 60), (100, 140), (60, 40), (-60, 40), (-100, 140), (-134, 60)]), fill(HAIR))


def draw_hair_front(c, P):
    # parted fringe sweeping to the sides
    for side in (-1, 1):
        p = smooth_path([(0, -162), (side * 60, -170), (side * 112, -130), (side * 126, -60), (side * 118, 10),
                         (side * 104, -40), (side * 92, -96), (side * 50, -128), (side * 8, -140)])
        c.drawPath(p, fill(HAIR))
        for k in range(3):
            q = skia.Path()
            q.moveTo(side * (14 + k * 16), -150 + k * 4)
            q.quadTo(side * (80 + k * 10), -140 + k * 10, side * (104 + k * 6), -40 + k * 14)
            c.drawPath(q, stroke(HAIR_HI, 2.4, 0.55))
    # wild midnight flyaways (they make the scary silhouette)
    for k, (bx, by, tx, ty) in enumerate(((-60, -250, -110, -330), (30, -270, 60, -350), (70, -240, 140, -300),
                                          (-100, -200, -170, -250), (110, -170, 175, -205), (-10, -280, -20, -360))):
        q = skia.Path()
        q.moveTo(bx, by)
        q.quadTo((bx + tx) / 2 + 20, (by + ty) / 2, tx, ty)
        c.drawPath(q, stroke(HAIR, 7))
    # messy bun with spiral loops
    c.drawCircle(0, -222, 82, fill(HAIR))
    for k, (dx, dy, r) in enumerate(((-30, -236, 34), (24, -248, 28), (40, -202, 24), (-36, -196, 22))):
        sp = spiral_pts(dx, dy, r, 4, 1.6, a0=k, n=30)
        c.drawPath(open_path(sp), stroke(HAIR_HI, 3.0, 0.7))
    # stray curls
    for side in (-1, 1):
        sp = spiral_pts(side * 132, 52, 4, 20, 1.4, a0=0, n=24, direction=side)
        c.drawPath(open_path([(side * 118, -10), (side * 132, 30)] + sp[::-1]), stroke(HAIR, 4.5))
    # curlers (the "horns")
    for (cx, cy, ang), col in zip(((-126, -196, -52), (124, -202, 52), (0, -296, 0)), CURLERS):
        with Xf(c, cx, cy, rot=ang):
            r = skia.Rect.MakeLTRB(-24, -46, 24, 46)
            c.drawRoundRect(r, 18, 18, fill(col))
            for yy in range(-36, 40, 12):
                c.drawLine(-22, yy, 22, yy, stroke((255, 255, 255), 2.4, 0.35))
            c.drawRoundRect(r, 18, 18, stroke((40, 30, 50), 3.0, 0.8))


def draw_hand(c, x, y, ang, side, fingers=4, curl=0.3):
    with Xf(c, x, y, rot=ang):
        c.drawOval(skia.Rect.MakeLTRB(-22, -16, 22, 26), fill(SKIN))
        for i in range(fingers):
            fx = -15 + i * 10
            L = 58 - abs(i - 1.5) * 8
            p = skia.Path()
            p.moveTo(fx, 16)
            p.quadTo(fx + side * curl * 10, 16 + L * 0.6, fx + side * curl * 22, 16 + L)
            c.drawPath(p, stroke(SKIN_SH, 13))
            c.drawPath(p, stroke(SKIN, 10))
        th = skia.Path()
        th.moveTo(side * 18, 0)
        th.quadTo(side * 40, 18, side * 34, 42)
        c.drawPath(th, stroke(SKIN_SH, 13))
        c.drawPath(th, stroke(SKIN, 10))


def robe_path(full):
    if full:
        return smooth_path([(-60, 300), (-150, 360), (-176, 600), (-196, 1100), (-230, 1640), (-120, 1700),
                            (0, 1690), (120, 1700), (230, 1640), (196, 1100), (176, 600), (150, 360), (60, 300)])
    return smooth_path([(-60, 300), (-160, 360), (-196, 640), (-220, 1000), (0, 1040), (220, 1000), (196, 640),
                        (160, 360), (60, 300)])


def draw_robe(c, P):
    full = P["full"]
    rp = robe_path(full)
    c.drawPath(rp, fill(ROBE_B))
    c.save()
    c.clipPath(rp, skia.ClipOp.kIntersect, True)
    bottom = 1720 if full else 1060
    for i in range(-9, 10):
        x0 = i * 34
        p = skia.Path()
        p.moveTo(x0 * 0.55, 300)
        p.cubicTo(x0 * 1.0, 600, x0 * 1.15, 1000, x0 * 1.3, bottom)
        if i % 2 == 0:
            c.drawPath(p, stroke(ROBE_A, 15, 0.9))
    c.drawPath(rp, fill((0, 0, 0), 1.0, lin_grad((-220, 0), (220, 0), [(0, 0, 0, 0.35), (0, 0, 0, 0.0), (0, 0, 0, 0.45)])))
    c.restore()
    # fuzzy shawl collar
    for side in (-1, 1):
        col = smooth_path([(side * 30, 290), (side * 120, 330), (side * 150, 400), (side * 60, 760), (side * 6, 800),
                           (side * 34, 600), (side * 60, 420)])
        c.drawPath(col, fill(COLLAR))
        c.drawPath(col, stroke((150, 130, 170), 3, 0.7))
    if full:
        c.drawRect(skia.Rect.MakeLTRB(-170, 860, 170, 900), fill(COLLAR))  # belt
        for side in (-1, 1):  # bat slippers
            with Xf(c, side * 70, 1712):
                c.drawOval(skia.Rect.MakeLTRB(-60, -26, 60, 22), fill((30, 24, 36)))
                for w in (-1, 1):
                    wing = smooth_path([(w * 30, -10), (w * 80, -40), (w * 72, -16), (w * 92, -12), (w * 60, 6)])
                    c.drawPath(wing, fill((30, 24, 36)))
                c.drawCircle(-14, -8, 5, fill((250, 230, 120)))
                c.drawCircle(14, -8, 5, fill((250, 230, 120)))


def arm_layout(arms):
    """Returns ((lx, ly, l_ang), (rx, ry, r_ang)) hand positions in body space."""
    return {
        "down": ((-170, 860, 10), (170, 860, -10)),
        "candle": ((-178, 780, 4), (70, 560, -24)),
        "hold": ((-118, 640, 28), (118, 640, -28)),
        "hold_low": ((-130, 760, 15), (130, 760, -15)),
        "hug": ((-46, 560, 70), (58, 590, -76)),
        "pin": ((-170, 800, 8), (140, -60, -165)),
    }[arms]


def draw_arms(c, P, sleeves=True, hands=True):
    (lx, ly, la), (rx, ry, ra) = arm_layout(P["arms"])
    for side, (hx, hy, ang) in ((-1, (lx, ly, la)), (1, (rx, ry, ra))):
        if sleeves:
            sx, sy = side * 150, 360
            ex, ey = (sx + hx) / 2 + side * 60, (sy + hy) / 2 + 40
            sleeve = skia.Path()
            sleeve.moveTo(sx, sy)
            sleeve.quadTo(ex, ey, hx, hy - 20)
            c.drawPath(sleeve, stroke(ROBE_B, 58))
            c.drawPath(sleeve, stroke(ROBE_A, 14, 0.6))
        if hands:
            draw_hand(c, hx, hy, ang, side)


def draw_candle(c, P, x, y):
    ph = P["candle"]
    c.drawOval(skia.Rect.MakeLTRB(x - 60, y + 26, x + 60, y + 46), fill((150, 120, 70)))
    c.drawRect(skia.Rect.MakeLTRB(x - 22, y - 70, x + 22, y + 34), fill((236, 226, 200)))
    c.drawPath(smooth_path([(x - 22, y - 70), (x - 10, y - 60), (x - 4, y - 74), (x + 22, y - 70), (x + 22, y - 50),
                            (x - 22, y - 50)]), fill((246, 238, 214)))
    fl = 1 + 0.12 * math.sin(ph * 13) + 0.08 * math.sin(ph * 29)
    flame = smooth_path([(x, y - 134 * fl), (x + 14, y - 92), (x, y - 76), (x - 14, y - 92)])
    c.drawCircle(x, y - 98, 160, fill((255, 190, 90), 1.0, rad_grad((x, y - 98), 160,
                                                                     [(255, 200, 100, 0.45), (255, 160, 60, 0.12), (255, 140, 40, 0)]),
                                      blend=skia.BlendMode.kScreen))
    c.drawPath(flame, fill((255, 224, 140)))
    c.drawPath(smooth_path([(x, y - 112 * fl), (x + 6, y - 90), (x, y - 80), (x - 6, y - 90)]), fill((255, 252, 230)))


def draw_mom(c, P):
    with Xf(c, P["x"], P["y"], sx=P["scale"], alpha=P["alpha"]):
        if P["lean"]:
            c.rotate(P["lean"])
        if P["sil"]:
            c.saveLayer(None, None)
        draw_hair_back(c, P)
        # neck
        c.drawPath(smooth_path([(-36, 100), (36, 100), (42, 250), (-42, 250)], tension=0.4), fill(SKIN))
        c.drawPath(smooth_path([(-36, 100), (36, 100), (42, 250), (-42, 250)], tension=0.4),
                   fill((0, 0, 0), 1.0, lin_grad((0, 120), (0, 200), [(80, 40, 60, 0.45), (80, 40, 60, 0.0)])))
        c.save()
        c.translate(0, -70)
        draw_robe(c, P)
        if P["paper"] is not None and P["arms"] == "hug":
            P["paper"](c)
            draw_arms(c, P)
        elif P["paper"] is not None:
            draw_arms(c, P, sleeves=True, hands=False)
            P["paper"](c)
            draw_arms(c, P, sleeves=False, hands=True)
        else:
            draw_arms(c, P)
        if P["candle"] >= 0 and P["arms"] == "candle":
            draw_candle(c, P, 74, 512)
        c.restore()
        with Xf(c, P["turn"] * 8, P["nod"], rot=P["tilt"]):
            fp = face_path()
            c.drawPath(fp, fill(SKIN))
            # warm underlight + cool shade
            c.drawPath(fp, fill((0, 0, 0), 1.0, lin_grad((0, 170), (0, -160), [(255, 170, 90, 0.30 * P["warm"]), (255, 170, 90, 0.0)])))
            c.drawPath(fp, fill((0, 0, 0), 1.0, lin_grad((-120, 0), (120, 0), [(60, 40, 90, 0.0), (60, 40, 90, 0.22)])))
            for side in (-1, 1):
                cx = side * 66 + P["turn"] * 8
                c.drawCircle(cx, 52, 34, fill((230, 120, 130), 1.0, rad_grad((cx, 52), 34,
                                                                             [(230, 120, 130, 0.18 + 0.25 * P["blush"]), (230, 120, 130, 0)])))
            draw_hair_front(c, P)
            ox = P["turn"] * 16
            for side in (-1, 1):
                draw_eye(c, P, side, ox + side * 52, -8)
                draw_brow(c, P, side, ox + side * 52, -8)
            # nose
            n = skia.Path()
            n.moveTo(ox + 4, -6)
            n.quadTo(ox + 14, 30, ox + 6, 50)
            n.quadTo(ox - 2, 58, ox - 10, 50)
            c.drawPath(n, stroke(SKIN_SH, 3.0, 0.8))
            draw_mouth(c, P)
        if P["sil"]:
            c.drawPaint(fill(SIL, 1.0, blend=skia.BlendMode.kSrcIn))
            c.restore()
