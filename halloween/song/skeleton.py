"""Dancing skeleton puppet in the pencil-on-paper gothic style.

Local units: pelvis at (0, 0), feet on the ground at y = 0 when standing
(the rig lifts the pelvis to leg height). ~560 units tall at scale 1.
"""
import math
import random

import skia

from gfx import GRAPHITE, INK, Xf, circle, clamp, ellipse, fill, lerp, open_path, pencil, rad_grad, smooth_path, stroke

BONE = (238, 232, 212)
BONE_SH = (190, 184, 170)
SOCKET = (16, 12, 22)
GLOW = (236, 248, 170)

DEFAULT = dict(
    x=0.0, y=0.0, scale=1.0, facing=1, alpha=1.0,
    bounce=0.0,          # pelvis down (units)
    sway=0.0,            # pelvis sideways
    lean=0.0,            # torso lean degrees
    twist=0.0,           # ribcage shift sideways
    tilt=0.0, head_dx=0.0, head_dy=0.0, head_off=0.0,   # head_off lifts the skull off the neck
    jaw=0.0,             # 0 closed .. 1 wide open
    look=(0.0, 0.0), pupil=1.0, glow=1.0,
    brow=0.0,            # socket tops: +1 surprised (round), -1 angry (inner corners down)
    sad=0.0,             # outer corners down
    blink=0.0,
    grin=0.6,            # teeth smile curve
    sh_l=(25.0, 15.0), sh_r=(25.0, 15.0),   # (shoulder deg from down, elbow deg)
    hand_l=0.0, hand_r=0.0,                 # finger spread / wiggle phase
    foot_l=(-42.0, 0.0), foot_r=(42.0, 0.0),  # foot targets relative to (x, y), y<0 lifts
    knee_out=1.0,
    hat=None,            # 'bowler'
    hat_lift=0.0,
    hat_hand=False,      # holding the hat up in the right hand (tipped off the bald skull)
    flower=False, bucket=False, big=False, tiny=False,
    collapse=0.0,        # 0 standing .. 1 a pile of bones
    seed=0,
    rib_glow=-1,         # index of a rib lit up (xylophone)
    scarf=False,         # Big Clatter's knitted scarf
    mallet=False,        # a little bone mallet in the right hand
    scarf_swing=None,    # override for where the scarf tails hang
)


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


def bone(c, x0, y0, x1, y1, w, seed, col=BONE):
    """Cartoon bone with knobby ends between two points."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) + 1e-6
    ang = math.degrees(math.atan2(dy, dx))
    with Xf(c, x0, y0, rot=ang):
        shaft = skia.Path()
        shaft.addRoundRect(skia.Rect.MakeLTRB(0, -w * 0.42, L, w * 0.42), w * 0.3, w * 0.3)
        knobs = skia.Path()
        for (kx, ky) in ((0, -w * 0.38), (0, w * 0.38), (L, -w * 0.38), (L, w * 0.38)):
            knobs.addCircle(kx, ky, w * 0.42)
        shape = skia.Op(shaft, knobs, skia.PathOp.kUnion_PathOp) or shaft
        c.drawPath(shape, fill(col))
        c.drawPath(shape, fill((0, 0, 0), 1.0, rad_grad((L * 0.5, w * 0.8), L * 0.7, [(60, 50, 70, 0.22), (0, 0, 0, 0)])))
        pencil(c, shape, 2.4, GRAPHITE, 0.95, seed=seed, rough=0.7, double=False)


def two_bone_ik(hx, hy, fx, fy, l1, l2, bend):
    """Knee position for hip (hx,hy) -> foot (fx,fy). bend: +1 knee to the right / forward."""
    dx, dy = fx - hx, fy - hy
    d = min(math.hypot(dx, dy), l1 + l2 - 1e-3)
    d = max(d, abs(l1 - l2) + 1e-3)
    a = math.atan2(dy, dx)
    cos_k = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    k = math.acos(clamp(cos_k, -1, 1))
    ang = a - bend * k
    return hx + math.cos(ang) * l1, hy + math.sin(ang) * l1


def draw_skull(c, P, seed):
    big = 1.15 if P["big"] else 1.0
    with Xf(c, 0, 0, sx=big):
        jaw = clamp(P["jaw"])
        # mandible (behind cranium so it hinges out of the cheeks)
        jy = 52 + jaw * 34
        mand = smooth_path([(-52, 30), (-46, jy - 4), (-20, jy + 10), (20, jy + 10), (46, jy - 4), (52, 30), (30, 38),
                            (-30, 38)])
        c.drawPath(mand, fill(BONE))
        pencil(c, mand, 2.6, GRAPHITE, 1.0, seed=seed + 1, rough=0.7)
        # mouth cavity when open
        if jaw > 0.05:
            cav = smooth_path([(-40, 38), (40, 38), (34, jy - 6), (0, jy + 2), (-34, jy - 6)])
            c.drawPath(cav, fill(SOCKET))
        # lower teeth
        for i in range(-3, 4):
            tx = i * 10
            c.drawRoundRect(skia.Rect.MakeLTRB(tx - 4.5, jy - 14, tx + 4.5, jy - 3), 2, 2, fill(BONE))
            c.drawRoundRect(skia.Rect.MakeLTRB(tx - 4.5, jy - 14, tx + 4.5, jy - 3), 2, 2, stroke(GRAPHITE, 1.4, 0.8))
        # cranium
        cran = smooth_path([(-74, -10), (-70, -62), (-40, -96), (0, -104), (40, -96), (70, -62), (74, -10), (60, 22),
                            (40, 40), (-40, 40), (-60, 22)])
        c.drawPath(cran, fill(BONE))
        c.drawPath(cran, fill((0, 0, 0), 1.0, rad_grad((-24, -50), 120, [(255, 255, 255, 0.0), (70, 60, 90, 0.28)])))
        # little crack for character
        c.drawPath(open_path([(30, -96), (36, -78), (28, -66), (34, -54)]), stroke(GRAPHITE, 1.6, 0.7))
        pencil(c, cran, 3.0, GRAPHITE, 1.0, seed=seed, rough=0.8)
        # upper teeth row
        cur = P["grin"]
        for i in range(-3, 4):
            tx = i * 10
            ty = 30 - cur * (6 - abs(i) * 1.8)
            c.drawRoundRect(skia.Rect.MakeLTRB(tx - 4.5, ty, tx + 4.5, ty + 12), 2, 2, fill(BONE))
            c.drawRoundRect(skia.Rect.MakeLTRB(tx - 4.5, ty, tx + 4.5, ty + 12), 2, 2, stroke(GRAPHITE, 1.4, 0.8))
        # eye sockets with expression (brow / sad) and glowing pupils
        lx, ly = P["look"]
        for side in (-1, 1):
            ex, ey = side * 32, -22
            sock = ellipse(ex, ey, 25, 28)
            c.drawPath(sock, fill(SOCKET))
            c.save()
            c.clipPath(sock, skia.ClipOp.kIntersect, True)
            if P["glow"] > 0 and P["blink"] < 0.9:
                px, py = ex + lx * 9, ey + ly * 9
                r = 6.5 * P["pupil"]
                c.drawCircle(px, py, r * 3.2, fill(GLOW, 1.0, rad_grad((px, py), r * 3.2,
                                                                    [(*GLOW, 0.5 * P["glow"]), (*GLOW, 0.0)])))
                c.drawCircle(px, py, r, fill(GLOW, P["glow"]))
                c.drawCircle(px - r * 0.3, py - r * 0.3, r * 0.35, fill((255, 255, 255), P["glow"]))
            # brow / sadness / blink: bone-coloured lids eat into the socket
            b, s = P["brow"], P["sad"]
            lid = skia.Path()
            inner_drop = max(0.0, -b) * 22 - max(0.0, b) * 6
            outer_drop = s * 20 - max(0.0, b) * 6
            ix, ox = ex - side * 28, ex + side * 28
            lid.moveTo(ix, ey - 40)
            lid.lineTo(ox, ey - 40)
            lid.lineTo(ox, ey - 30 + outer_drop)
            lid.quadTo(ex, ey - 34 + (inner_drop + outer_drop) * 0.4, ix, ey - 30 + inner_drop)
            lid.close()
            c.drawPath(lid, fill(BONE))
            if P["blink"] > 0:
                bl = clamp(P["blink"])
                c.drawRect(skia.Rect.MakeLTRB(ex - 30, ey - 32, ex + 30, ey - 32 + 62 * bl), fill(BONE))
            c.restore()
            pencil(c, sock, 2.4, GRAPHITE, 0.9, seed=seed + 3 + side, rough=0.6)
            if P["blink"] > 0.85:
                c.drawPath(open_path([(ex - 22, ey + 2), (ex, ey + 8), (ex + 22, ey + 2)]), stroke(GRAPHITE, 2.6))
        # nose hole
        nose = smooth_path([(0, 2), (-9, 16), (-4, 22), (0, 18), (4, 22), (9, 16)], tension=0.7)
        c.drawPath(nose, fill(SOCKET))
        if P["flower"]:
            draw_flower(c, -62, -70, 1.0)


def draw_flower(c, x, y, s):
    with Xf(c, x, y, sx=s):
        for i in range(6):
            a = i / 6 * 2 * math.pi
            c.drawOval(skia.Rect.MakeLTRB(math.cos(a) * 16 - 11, math.sin(a) * 16 - 8, math.cos(a) * 16 + 11,
                                          math.sin(a) * 16 + 8), fill((236, 120, 170)))
        c.drawCircle(0, 0, 9, fill((250, 214, 90)))
        c.drawCircle(0, 0, 9, stroke(GRAPHITE, 1.6))


def draw_hat(c, lift, x=4.0, y=None, rot=-8.0):
    with Xf(c, x, -96 - lift if y is None else y, rot=rot):
        c.drawOval(skia.Rect.MakeLTRB(-78, -12, 78, 12), fill((22, 18, 28)))
        c.drawPath(smooth_path([(-50, 0), (-48, -54), (-20, -74), (20, -74), (48, -54), (50, 0)], tension=0.8),
                   fill((22, 18, 28)))
        c.drawRect(skia.Rect.MakeLTRB(-50, -16, 50, -2), fill((120, 40, 60)))
        c.drawOval(skia.Rect.MakeLTRB(-78, -12, 78, 12), stroke((70, 60, 90), 2.0, 0.8))


def draw_bucket(c, x, y):
    with Xf(c, x, y):
        c.drawPath(smooth_path([(-30, -10), (30, -10), (26, 34), (-26, 34)], tension=0.5), fill((250, 130, 30)))
        c.drawPath(smooth_path([(-14, 6), (-6, 0), (2, 6)], tension=0.5), stroke((90, 30, 6), 3))
        c.drawPath(smooth_path([(6, 6), (14, 0), (20, 6)], tension=0.5), stroke((90, 30, 6), 3))
        p = skia.Path()
        p.moveTo(-30, -10)
        p.quadTo(0, -60, 30, -10)
        c.drawPath(p, stroke(GRAPHITE, 3))


SCARF_A = (120, 56, 128)
SCARF_B = (226, 170, 64)


def ribbon(c, pts, w, seed):
    """Striped knitted ribbon along a polyline."""
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        quad = skia.Path()
        quad.moveTo(x0 + nx, y0 + ny)
        quad.lineTo(x1 + nx * 1.04, y1 + ny * 1.04)
        quad.lineTo(x1 - nx * 1.04, y1 - ny * 1.04)
        quad.lineTo(x0 - nx, y0 - ny)
        quad.close()
        c.drawPath(quad, fill(SCARF_A if (i // 2) % 2 == 0 else SCARF_B))
    outline = skia.Path()
    for side in (1, -1):
        p2 = []
        for i, (x, y) in enumerate(pts):
            j = min(i, len(pts) - 2)
            dx, dy = pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]
            L = math.hypot(dx, dy) + 1e-6
            p2.append((x - dy / L * w / 2 * side, y + dx / L * w / 2 * side))
        outline.addPath(open_path(p2))
    c.drawPath(outline, stroke(GRAPHITE, 2.4, 0.9))
    # fringe
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    dx, dy = xb - xa, yb - ya
    L = math.hypot(dx, dy) + 1e-6
    for k in range(-2, 3):
        fx = xb - dy / L * k * w * 0.2
        fy = yb + dx / L * k * w * 0.2
        c.drawLine(fx, fy, fx + dx / L * 14, fy + dy / L * 14, stroke(SCARF_B, 3.0))


def draw_scarf(c, x, y, swing, seed):
    """Wrapped around the neck, two tails hanging down the chest and swinging."""
    for k, (ox, n, ln) in enumerate(((-16, 6, 150), (18, 5, 118))):
        pts = []
        for i in range(n + 1):
            u = i / n
            pts.append((x + ox + swing * (u ** 1.6) * (1.0 + 0.3 * k) + 6 * math.sin(u * 3 + k),
                        y + 12 + u * ln))
        ribbon(c, pts, 30, seed + k)
    wrap = smooth_path([(-50, -12), (-20, -22), (20, -22), (50, -12), (52, 12), (20, 22), (-20, 22), (-52, 12)],
                       tension=0.7)
    with Xf(c, x, y):
        c.drawPath(wrap, fill(SCARF_A))
        c.save()
        c.clipPath(wrap, skia.ClipOp.kIntersect, True)
        for k in range(-3, 4):
            c.drawRect(skia.Rect.MakeLTRB(k * 18 - 5, -30, k * 18 + 5, 30), fill(SCARF_B))
        c.restore()
        pencil(c, wrap, 2.4, GRAPHITE, 0.95, seed=seed + 5, rough=0.6)


def draw_mallet(c, hx, hy, ang, side, big, seed):
    """A short bone with a round knob, held along the forearm direction."""
    L = 64 * big
    ex, ey = hx + side * math.sin(ang) * L, hy + math.cos(ang) * L
    bone(c, hx, hy, ex, ey, 12 * big, seed, col=(214, 196, 160))
    c.drawCircle(ex, ey, 17 * big, fill((214, 196, 160)))
    c.drawCircle(ex, ey, 17 * big, stroke(GRAPHITE, 2.6))


def _dims(P):
    big = 1.2 if P["big"] else 1.0
    s = P["scale"] * (0.62 if P["tiny"] else 1.0)
    f = 1 if P["facing"] >= 0 else -1
    hip_y = -(105.0 * big + 100.0 * big) * 0.94 + P["bounce"]
    return big, s, f, hip_y


def torso_to_world(P, lx, ly):
    """Point in the torso frame (pelvis origin, before lean) -> world."""
    big, s, f, hip_y = _dims(P)
    a = math.radians(P["lean"])
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    return P["x"] + s * f * (P["sway"] + rx), P["y"] + s * (hip_y + ry)


def rib_point(P, i, side=-1):
    """World position of the middle of rib i on the given side."""
    big = 1.2 if P["big"] else 1.0
    rcx, rcy = P["twist"] * 0.9, -165 * big
    wdt = (70 - abs(i - 1.5) * 9) * big
    ry = rcy - 50 * big + i * 23 * big
    return torso_to_world(P, rcx + side * wdt * 0.75, ry + 6)


def reach(P, side, tx, ty, extra=0.0):
    """(shoulder, elbow) angles so the hand (+extra length along the forearm) lands on world (tx, ty)."""
    big, s, f, hip_y = _dims(P)
    lx = (tx - P["x"]) / (s * f) - P["sway"]
    ly = (ty - P["y"]) / s - hip_y
    a = -math.radians(P["lean"])
    rx = lx * math.cos(a) - ly * math.sin(a)
    ry = lx * math.sin(a) + ly * math.cos(a)
    rcx, shy = P["twist"] * 0.9, -165 * big - 58 * big
    u, v = (rx - (rcx + side * 66 * big)) * side, ry - shy
    l1, l2 = 92 * big, 86 * big + extra
    d = clamp(math.hypot(u, v), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    phi = math.atan2(u, v)
    al = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    r1 = phi - al
    eu, ev = l1 * math.sin(r1), l1 * math.cos(r1)
    r2 = math.atan2(u - eu, v - ev)
    return math.degrees(r1), math.degrees(r2 - r1)


def draw_skeleton(c, P):
    f = 1 if P["facing"] >= 0 else -1
    seed = P["seed"]
    tiny = 0.62 if P["tiny"] else 1.0
    big = 1.2 if P["big"] else 1.0
    s = P["scale"] * tiny
    with Xf(c, P["x"], P["y"], sx=s * f, sy=s, alpha=P["alpha"]):
        if P["collapse"] > 0:
            draw_pile(c, P, seed)
            return
        # ground shadow
        c.drawOval(skia.Rect.MakeLTRB(-120 * big, -14, 120 * big, 14),
                   fill((0, 0, 0), 1.0, rad_grad((0, 0), 120 * big, [(0, 0, 0, 0.45), (0, 0, 0, 0.0)])))
        thigh, shin = 105.0 * big, 100.0 * big
        hip_y = -(thigh + shin) * 0.94 + P["bounce"]
        px = P["sway"]
        # legs (IK), back to front
        legs = []
        for side, key in ((-1, "foot_l"), (1, "foot_r")):
            fx, fy = P[key]
            hx, hy = px + side * 34 * big, hip_y + 8
            kx, ky = two_bone_ik(hx, hy, fx, fy, thigh, shin, side * P["knee_out"])
            legs.append((side, hx, hy, kx, ky, fx, fy))
        for side, hx, hy, kx, ky, fx, fy in legs:
            bone(c, hx, hy, kx, ky, 16 * big, seed + 10 + side)
            bone(c, kx, ky, fx, fy - 6, 14 * big, seed + 12 + side)
            with Xf(c, fx, fy - 6):
                ft = smooth_path([(-8, -8), (side * 40 * big, -6), (side * 46 * big, 4), (-10, 6)], tension=0.6)
                c.drawPath(ft, fill(BONE))
                pencil(c, ft, 2.2, GRAPHITE, 0.9, seed=seed + 14 + side, double=False)
            c.drawCircle(kx, ky, 9 * big, fill(BONE))
            c.drawCircle(kx, ky, 9 * big, stroke(GRAPHITE, 2.0))
        with Xf(c, px, hip_y, rot=P["lean"]):
            # pelvis
            pel = smooth_path([(-56, -14), (-30, -26), (0, -18), (30, -26), (56, -14), (40, 14), (14, 22), (-14, 22),
                               (-40, 14)])
            with Xf(c, 0, 0, sx=big):
                c.drawPath(pel, fill(BONE))
                c.drawCircle(-22, 2, 9, fill(SOCKET))
                c.drawCircle(22, 2, 9, fill(SOCKET))
                pencil(c, pel, 2.6, GRAPHITE, 1.0, seed=seed + 20, rough=0.7)
            # spine
            tw = P["twist"]
            top_y = -240 * big
            sp = []
            for i in range(9):
                u = i / 8
                sp.append((tw * math.sin(u * math.pi * 0.9), -24 - u * (-top_y - 24)))
            for i, (vx, vy) in enumerate(sp):
                c.drawRoundRect(skia.Rect.MakeLTRB(vx - 9, vy - 7, vx + 9, vy + 7), 4, 4, fill(BONE))
                c.drawRoundRect(skia.Rect.MakeLTRB(vx - 9, vy - 7, vx + 9, vy + 7), 4, 4, stroke(GRAPHITE, 1.8, 0.9))
            # ribcage
            rcx, rcy = tw * 0.9, -165 * big
            for i in range(5):
                ry = rcy - 50 * big + i * 23 * big
                wdt = (70 - abs(i - 1.5) * 9) * big
                rib = skia.Path()
                rib.moveTo(rcx, ry)
                rib.cubicTo(rcx - wdt * 0.6, ry - 14, rcx - wdt, ry + 4, rcx - wdt * 0.8, ry + 18)
                rib2 = skia.Path()
                rib2.moveTo(rcx, ry)
                rib2.cubicTo(rcx + wdt * 0.6, ry - 14, rcx + wdt, ry + 4, rcx + wdt * 0.8, ry + 18)
                lit = P["rib_glow"] == i
                col = (255, 236, 150) if lit else BONE
                for r in (rib, rib2):
                    c.drawPath(r, stroke(GRAPHITE, 13 * big))
                    c.drawPath(r, stroke(col, 8 * big))
                if lit:
                    c.drawCircle(rcx, ry + 6, 90 * big, fill(GLOW, 1.0, rad_grad((rcx, ry + 6), 90 * big,
                                                                                  [(*GLOW, 0.85), (*GLOW, 0.0)]),
                                                              blend=skia.BlendMode.kScreen))
            c.drawLine(rcx, rcy - 56 * big, rcx, rcy + 46 * big, stroke(GRAPHITE, 10 * big))
            c.drawLine(rcx, rcy - 56 * big, rcx, rcy + 46 * big, stroke(BONE, 6 * big))
            # arms
            shy = rcy - 58 * big
            for side, key, hkey in ((-1, "sh_l", "hand_l"), (1, "sh_r", "hand_r")):
                a1, a2 = P[key]
                sx0 = rcx + side * 66 * big
                r1 = math.radians(a1)
                ex_, ey_ = sx0 + side * math.sin(r1) * 92 * big, shy + math.cos(r1) * 92 * big
                r2 = math.radians(a1 + a2)
                hx_, hy_ = ex_ + side * math.sin(r2) * 86 * big, ey_ + math.cos(r2) * 86 * big
                bone(c, sx0, shy, ex_, ey_, 14 * big, seed + 30 + side)
                bone(c, ex_, ey_, hx_, hy_, 12 * big, seed + 32 + side)
                c.drawCircle(sx0, shy, 12 * big, fill(BONE))
                c.drawCircle(sx0, shy, 12 * big, stroke(GRAPHITE, 2.2))
                # hand: palm + four wiggly finger bones
                ang = r2
                wig = P[hkey]
                for k in range(4):
                    fa = ang + (k - 1.5) * 0.32 + 0.25 * math.sin(wig * 2 * math.pi + k)
                    fx_ = hx_ + side * math.sin(fa) * 30 * big
                    fy_ = hy_ + math.cos(fa) * 30 * big
                    c.drawLine(hx_, hy_, fx_, fy_, stroke(GRAPHITE, 7 * big))
                    c.drawLine(hx_, hy_, fx_, fy_, stroke(BONE, 4 * big))
                c.drawCircle(hx_, hy_, 11 * big, fill(BONE))
                c.drawCircle(hx_, hy_, 11 * big, stroke(GRAPHITE, 2.0))
                if P["bucket"] and side == 1:
                    draw_bucket(c, hx_ + 10, hy_ + 30)
                if P["mallet"] and side == 1:
                    draw_mallet(c, hx_, hy_, r2, side, big, seed + 50)
                if side == 1:
                    hand_r = (hx_, hy_)
            # neck + skull
            neck_top = top_y - 40 * big
            for k in range(3):
                c.drawCircle(tw * 0.5, top_y - 8 - k * 12, 7, fill(BONE))
                c.drawCircle(tw * 0.5, top_y - 8 - k * 12, 7, stroke(GRAPHITE, 1.6))
            if P["scarf"]:
                swing = P["scarf_swing"]
                if swing is None:
                    swing = -P["sway"] * 1.4 - P["twist"] * 0.8 + P["lean"] * 2
                draw_scarf(c, tw * 0.5, top_y - 14, swing, seed + 60)
            hx2 = tw * 0.5 + P["head_dx"]
            hy2 = neck_top - 70 - P["head_off"] + P["head_dy"]
            with Xf(c, hx2, hy2, rot=P["tilt"]):
                draw_skull(c, P, seed + 40)
                if P["hat"] == "bowler" and not P["hat_hand"]:
                    draw_hat(c, P["hat_lift"])
            if P["hat"] == "bowler" and P["hat_hand"]:
                draw_hat(c, 0.0, x=hand_r[0] + 6, y=hand_r[1] - 14, rot=-18)


def draw_pile(c, P, seed):
    """Collapsed into a heap of bones; the skull sits on top."""
    u = clamp(P["collapse"])
    rr = random.Random(seed * 13 + 7)
    c.drawOval(skia.Rect.MakeLTRB(-150, -16, 150, 16), fill((0, 0, 0), 1.0, rad_grad((0, 0), 150,
                                                                                     [(0, 0, 0, 0.45), (0, 0, 0, 0)])))
    for i in range(14):
        L = rr.uniform(60, 110)
        ang = rr.uniform(-40, 40)
        x0 = rr.uniform(-110, 110)
        y_end = -8 - rr.uniform(0, 34)
        y0 = lerp(-380 + i * 22, y_end, min(1.0, u * 1.4 - i * 0.02))
        with Xf(c, x0, y0, rot=ang * u):
            bone(c, -L / 2, 0, L / 2, 0, 14, seed + i)
    hy = lerp(-380, -66, u)
    with Xf(c, 10, hy, rot=-14 * u):
        draw_skull(c, P, seed + 40)
        if P["hat"] == "bowler":
            draw_hat(c, P["hat_lift"])
