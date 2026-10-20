"""The skinny black cat: a spindly gothic silhouette with lantern eyes."""
import math

import skia

from gfx import (Xf, circle, clamp, fill, lerp, open_path, rad_grad, smooth_path, spiral_pts, stroke)

FUR = (13, 11, 20)
FUR_HI = (44, 38, 70)
RIM = (130, 140, 210)
EYE_A = (250, 244, 150)
EYE_B = (214, 200, 40)
INNER_EAR = (70, 40, 74)

DEFAULT = dict(
    x=0.0, y=0.0, scale=1.0, facing=1, alpha=1.0,
    rise=1.0,          # 0 crouched/hidden .. 1 sitting tall
    tilt=0.0,          # head roll
    turn=0.0,          # -1..1 head turn
    look=(0.0, 0.0),
    lid=0.15,          # upper lids (0 wide .. 1 closed)
    lid_low=0.1,
    lid_tilt=0.3,      # + menacing (inner corners down), - soft/sad
    pupil=0.25,        # 0 thin slit .. 1 round
    mouth=0.0,
    smile=0.0,
    ear_back=0.0,      # flattened ears
    tail_t=0.0,
    tail_amp=1.0,
    breathe=0.0,
    eyes_only=0.0,     # 1 = only the glowing eyes visible (in the dark)
    glow=1.0,
    rim=1.0,
    light_dir=1.0,     # -1 light from left, 1 from right
    curl=0.0,          # 1 = curled up asleep pose
    seed=0,
)


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


def with_rim(c, path, P, dx):
    """Fill a silhouette with a moonlit rim on one side."""
    c.drawPath(path, fill(FUR))
    if P["rim"] <= 0:
        return
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    c.drawPath(path, fill(RIM, 0.75 * P["rim"]))
    c.translate(-dx, dx * 0.35)
    c.drawPath(path, fill(FUR, 1.0, blur=1.2))
    c.restore()


def head_path(turn):
    k = turn * 10
    return smooth_path([(-78 + k, -6), (-70 + k, -58), (-30 + k, -84), (30 + k, -84), (70 + k, -58), (78 + k, -6),
                        (54 + k, 34), (24 + k * 1.3, 58), (0 + k * 1.4, 64), (-24 + k * 1.3, 58), (-54 + k, 34)])


def ear_path(side, back, turn):
    b = back
    bx = side * 34 + turn * 8
    tip = (side * (64 + 34 * b) + turn * 10, -170 + 70 * b)
    return smooth_path([(bx - side * 26, -66), (tip[0] - side * 12, tip[1] + 22), tip, (tip[0] + side * 6, tip[1] + 30),
                        (bx + side * 36, -50)], tension=0.8)


def draw_eye(c, P, side, ex, ey):
    rx, ry = 27, 23
    lid, low = clamp(P["lid"]), clamp(P["lid_low"])
    if lid > 0.95:
        p = skia.Path()
        p.moveTo(ex - rx, ey)
        p.quadTo(ex, ey + 12, ex + rx, ey)
        c.drawPath(p, stroke(RIM, 3.0, 0.8))
        return
    g = P["glow"]
    c.drawCircle(ex, ey, 70, fill(EYE_B, 1.0, rad_grad((ex, ey), 70, [(*EYE_A, 0.30 * g), (*EYE_B, 0.10 * g), (*EYE_B, 0)]),
                                  blend=skia.BlendMode.kScreen))
    eye = skia.Path()
    eye.addOval(skia.Rect.MakeLTRB(ex - rx, ey - ry, ex + rx, ey + ry))
    c.save()
    c.clipPath(eye, skia.ClipOp.kIntersect, True)
    c.drawPath(eye, fill(EYE_A, 1.0, rad_grad((ex, ey + 4), rx * 1.2, [EYE_A, EYE_B, (150, 120, 20)])))
    lx, ly = P["look"]
    px, py = ex + lx * 10, ey + ly * 7
    pw = lerp(3.5, 13.0, clamp(P["pupil"]))
    c.drawOval(skia.Rect.MakeLTRB(px - pw, py - 19, px + pw, py + 19), fill((8, 6, 10)))
    c.drawCircle(px - 7, py - 9, 4.2, fill((255, 255, 255), 0.9))
    # lids (fur coloured)
    t = P["lid_tilt"] * side
    if lid > 0.001:
        edge = ey - ry - 2 + lid * (2 * ry + 4)
        lp = skia.Path()
        lp.moveTo(ex - rx - 6, ey - ry - 30)
        lp.lineTo(ex + rx + 6, ey - ry - 30)
        lp.lineTo(ex + rx + 6, edge - t * 12)
        lp.quadTo(ex, edge + 6 * (1 - lid), ex - rx - 6, edge + t * 12)
        lp.close()
        c.drawPath(lp, fill(FUR))
        c.drawPath(lp, stroke((0, 0, 0), 3))
    if low > 0.001:
        edge = ey + ry + 2 - low * (ry + 2)
        lp = skia.Path()
        lp.moveTo(ex - rx - 6, ey + ry + 30)
        lp.lineTo(ex + rx + 6, ey + ry + 30)
        lp.lineTo(ex + rx + 6, edge)
        lp.quadTo(ex, edge - 8 * low, ex - rx - 6, edge)
        lp.close()
        c.drawPath(lp, fill(FUR))
    c.restore()
    c.drawPath(eye, stroke((0, 0, 0), 3.0, 0.9))


def draw_face(c, P):
    turn = P["turn"]
    ox = turn * 16
    for side in (-1, 1):
        draw_eye(c, P, side, ox + side * 36, -22)
    # nose + mouth
    nx, ny = ox * 1.3, 22
    c.drawPath(smooth_path([(nx - 7, ny - 4), (nx + 7, ny - 4), (nx, ny + 5)]), fill((60, 40, 66)))
    op = clamp(P["mouth"])
    sm = P["smile"]
    if op > 0.05:
        h = 6 + 22 * op
        mp = skia.Path()
        mp.moveTo(nx - 15, ny + 12 - sm * 4)
        mp.quadTo(nx, ny + 8, nx + 15, ny + 12 - sm * 4)
        mp.quadTo(nx + 12, ny + 12 + h, nx, ny + 14 + h)
        mp.quadTo(nx - 12, ny + 12 + h, nx - 15, ny + 12 - sm * 4)
        mp.close()
        c.drawPath(mp, fill((40, 10, 24)))
        c.save()
        c.clipPath(mp, skia.ClipOp.kIntersect, True)
        c.drawOval(skia.Rect.MakeLTRB(nx - 10, ny + 8 + h * 0.6, nx + 10, ny + 22 + h), fill((150, 60, 90)))
        for fx in (-9, 9):  # tiny fangs
            c.drawPath(smooth_path([(nx + fx - 3, ny + 10), (nx + fx + 3, ny + 10), (nx + fx, ny + 18)]),
                       fill((240, 236, 226)))
        c.restore()
    else:
        p = skia.Path()
        p.moveTo(nx - 16, ny + 12 - sm * 6)
        p.quadTo(nx - 8, ny + 18, nx, ny + 9)
        p.quadTo(nx + 8, ny + 18, nx + 16, ny + 12 - sm * 6)
        c.drawPath(p, stroke((90, 76, 120), 2.4))
    c.drawLine(nx, ny + 4, nx, ny + 10, stroke((90, 76, 120), 2.0))
    # whiskers
    for side in (-1, 1):
        for i, a in enumerate((-12, 2, 16)):
            r = math.radians(a)
            sx, sy = nx + side * 18, ny + 8 + i * 4
            ex, ey = sx + side * math.cos(r) * 120, sy + math.sin(r) * 120
            p = skia.Path()
            p.moveTo(sx, sy)
            p.quadTo((sx + ex) / 2, (sy + ey) / 2 - 10, ex, ey)
            c.drawPath(p, stroke((200, 200, 225), 1.6, 0.7))


def draw_tail(c, P, base):
    t, amp = P["tail_t"], P["tail_amp"]
    bx, by = base
    pts = []
    n = 12
    for i in range(n):
        u = i / (n - 1)
        x = bx + 60 + u * 170 + math.sin(t * 1.3 + u * 2.4) * 30 * u * amp
        y = by - 10 - u * 300 + math.sin(t * 1.7 - u * 3.1) * 18 * u * amp
        pts.append((x, y))
    ex, ey = pts[-1]
    sp = spiral_pts(ex - 30, ey - 2, 30, 3, 1.5, a0=0.0, n=30, direction=-1)
    path = open_path(pts + sp[1:])
    c.drawPath(path, stroke(FUR, 17))
    c.drawPath(path, stroke(RIM, 2.4, 0.35 * P["rim"]))


def draw_cat(c, P):
    f = 1 if P["facing"] >= 0 else -1
    with Xf(c, P["x"], P["y"], sx=P["scale"] * f, sy=P["scale"], alpha=P["alpha"]):
        if P["eyes_only"] >= 0.999:
            with Xf(c, 0, -470 * P["rise"] - 60 * (1 - P["rise"])):
                for side in (-1, 1):
                    draw_eye(c, P, side, side * 36, -22)
            return
        if P["curl"] > 0.5:
            draw_curled(c, P)
            return
        rise = P["rise"]
        br = 1 + 0.015 * math.sin(P["breathe"])
        dx = 7 * P["light_dir"] * f
        # contact shadow
        c.drawOval(skia.Rect.MakeLTRB(-170, -16, 190, 16), fill((0, 0, 0), 1.0,
                                                               rad_grad((10, 0), 190, [(0, 0, 0, 0.5), (0, 0, 0, 0)])))
        draw_tail(c, P, (40, -20))
        top = -330 * rise - 80
        haunch = smooth_path([(-46, -8), (-66, -110), (-46, top + 80), (-6, top), (40, top + 30),
                              (58, top + 120), (120, -170 * rise - 10), (150, -60), (118, -4)])
        with_rim(c, haunch, P, dx)
        # front legs
        for lx in (-32, 12):
            leg = smooth_path([(lx - 10, top + 120), (lx + 10, top + 120), (lx + 9, -14), (lx + 16, -2),
                               (lx - 14, -2), (lx - 9, -14)], tension=0.6)
            with_rim(c, leg, P, dx)
        # chest tuft
        tuft = skia.Path()
        for i in range(5):
            tuft.moveTo(-14 + i * 7, top + 70)
            tuft.lineTo(-16 + i * 8 + (i % 2) * 6, top + 104)
        c.drawPath(tuft, stroke(FUR_HI, 2.0, 0.6))
        # head
        hy = top - 70
        with Xf(c, 6 * P["turn"], hy, rot=P["tilt"]):
            for side in (-1, 1):
                ep = ear_path(side, P["ear_back"], P["turn"])
                with_rim(c, ep, P, dx)
                inner = skia.Path()
                tipx = side * (60 + 34 * P["ear_back"]) + P["turn"] * 10
                tipy = -152 + 70 * P["ear_back"]
                inner.moveTo(side * 30 + P["turn"] * 8, -62)
                inner.lineTo(tipx, tipy)
                inner.lineTo(side * 56 + P["turn"] * 8, -56)
                inner.close()
                c.drawPath(inner, fill(INNER_EAR, 0.8))
            hp = head_path(P["turn"])
            with_rim(c, hp, P, dx)
            # scraggly cheek tufts
            for side in (-1, 1):
                p = skia.Path()
                p.moveTo(side * 74, -4)
                p.lineTo(side * 92, 8)
                p.lineTo(side * 70, 16)
                p.lineTo(side * 84, 30)
                p.lineTo(side * 56, 34)
                c.drawPath(p, fill(FUR))
            c.scale(1.0, br)
            draw_face(c, P)


def draw_curled(c, P):
    dx = 5 * P["light_dir"]
    c.drawOval(skia.Rect.MakeLTRB(-200, -18, 200, 18), fill((0, 0, 0), 1.0,
                                                           rad_grad((0, 0), 200, [(0, 0, 0, 0.5), (0, 0, 0, 0)])))
    br = 1 + 0.02 * math.sin(P["breathe"])
    with Xf(c, 0, 0, sy=br):
        body = smooth_path([(-170, -6), (-150, -90), (-40, -140), (90, -128), (170, -60), (176, -6)])
        with_rim(c, body, P, dx)
        tail = open_path([(170, -14), (120, 4), (0, 8), (-120, 4), (-176, -20)] +
                         spiral_pts(-190, -40, 22, 3, 1.3, a0=math.pi * 0.5, n=20, direction=1)[1:])
        c.drawPath(tail, stroke(FUR, 16))
        c.drawPath(tail, stroke(RIM, 2.0, 0.3))
    with Xf(c, -112, -86, rot=-8):
        for side in (-1, 1):
            ep = ear_path(side, 0.25, 0.0)
            with Xf(c, 0, 0, sx=0.7):
                with_rim(c, ep, P, dx)
        with Xf(c, 0, 0, sx=0.7, sy=0.7):
            with_rim(c, head_path(0.0), P, dx)
            draw_face(c, P)
