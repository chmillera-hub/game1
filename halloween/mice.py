"""The five pencil mice from the drawing, as posable paper puppets.

Local units: head centre at (0, 0), roughly 130 units tall head.
A pose is a plain dict; see DEFAULT for every knob.
"""
import math

import skia

from gfx import (GRAPHITE, INK, PAPER, Xf, circle, clamp, ellipse, fill, lerp,
                 open_path, pencil, rad_grad, lin_grad, rounded_poly, smooth_path,
                 spiral_pts, stroke)

PAPER_HI = (250, 247, 238)
PAPER_SHADE = (200, 198, 196)
WHISKER_HALO = (226, 224, 216)
SOCKET = (60, 58, 78)
MOUTH_IN = (52, 22, 34)
TONGUE = (196, 96, 112)
TEAR = (190, 225, 255)

DEFAULT = dict(
    x=0.0, y=0.0, scale=1.0, facing=1, alpha=1.0,
    lift=0.0,            # hop height (world units, before scale)
    squash=1.0,          # vertical squash & stretch
    lean=0.0,            # body lean degrees
    tilt=0.0,            # head roll degrees
    yaw=0.0,             # -1..1 head turn (features slide)
    nod=0.0,             # head dip (units)
    look=(0.0, 0.0),     # pupil direction -1..1
    pupil=1.0,           # pupil size
    lid=0.0,             # upper lids 0 open .. 1 closed
    lid_low=0.0,         # lower lids raise 0..1 (happy squint)
    lid_tilt=0.0,        # +: sad (outer corners droop), -: cross
    closed_curve=0.0,    # when lids closed: +1 happy arc, -1 sleepy
    brow=0.0,            # brow height -1..1
    brow_tilt=0.0,       # +1 worried/sad (inner up), -1 angry
    mouth=0.0,           # open 0..1
    mround=0.0,          # rounded mouth (O/U)
    mwide=0.0,           # wide mouth (EE)
    smile=0.0,           # -1 frown .. 1 smile
    teeth=1.0,
    ear_droop=0.0, ear_perk=0.0, ear_twitch=0.0,
    whisk=0.0,           # whisker twitch -1..1
    tail_t=0.0,          # tail wave phase (seconds)
    tail_amp=1.0,
    walk=0.0,            # walk cycle phase (cycles); legs animate if walking>0
    walking=0.0,
    arm_l=(30.0, 20.0),  # (shoulder, elbow) degrees, 0 = straight down
    arm_r=(30.0, 20.0),
    hand_l=None, hand_r=None,  # optional override target points
    tear=0.0,            # 0 none, 0..1 tear drop progress
    glisten=0.0,         # wet eyes
    blush=0.0,
    flat=False,          # drawn flat on the page (no legs/arms)
    sleep=False,
    prop=None,           # 'pumpkin'
    seed=0,
    ink=1.0,             # 0 = plain pencil drawing, 1 = alive (shading, sockets, colour)
    light=(0.0, 0.0),    # direction to warm light in local space (-1..1)
    warm=0.0,            # warm light strength on this character
    upside=False,
)

KINDS = {
    # head outline kind, half width, top, chin; ears [(x, y, r)]; eyes; nose/mouth; body (cx, cy, rx, ry)
    "wedge": dict(head="tri", hw=72, top=-60, chin=88, ears=[(-68, -62, 31), (68, -66, 32)],
                  eye_y=-20, eye_dx=27, eye_r=16, eye_style="ring", nose_y=40, mouth_y=52, mw=11, jaw=20,
                  body=(118, 34, 112, 62), legs=62, whisk_y=44, whisk_len=96, arms_y=40, arm_x=20, arm_len=34,
                  size=1.0),
    "biscuit": dict(head="square", hw=56, top=-52, chin=52, ears=[(-56, -52, 27), (56, -54, 28)],
                    eye_y=-12, eye_dx=22, eye_r=13, eye_style="dot", nose_y=12, mouth_y=24, mw=14, jaw=12,
                    body=(98, 22, 98, 50), legs=56, whisk_y=18, whisk_len=80, arms_y=46, arm_x=30, arm_len=30,
                    size=1.0),
    "pip": dict(head="round", hw=58, top=-56, chin=58, ears=[(-50, -44, 25), (44, -50, 24)],
                eye_y=-8, eye_dx=22, eye_r=14, eye_style="dot", nose_y=20, mouth_y=31, mw=12, jaw=12,
                body=(96, 18, 100, 46), legs=54, whisk_y=26, whisk_len=76, arms_y=46, arm_x=26, arm_len=30,
                size=0.95),
    "crumb": dict(head="tri_round", hw=52, top=-46, chin=52, ears=[(-46, -48, 21), (46, -50, 22)],
                  eye_y=-14, eye_dx=20, eye_r=14, eye_style="big", nose_y=18, mouth_y=27, mw=9, jaw=14,
                  body=(66, 14, 62, 32), legs=40, whisk_y=22, whisk_len=56, arms_y=30, arm_x=18, arm_len=24,
                  size=0.62),
    "tilt": dict(head="tri", hw=60, top=-52, chin=74, ears=[(-57, -54, 26), (57, -57, 26)],
                 eye_y=-16, eye_dx=22, eye_r=13, eye_style="dot", nose_y=32, mouth_y=42, mw=10, jaw=16,
                 body=(96, 26, 92, 50), legs=50, whisk_y=36, whisk_len=74, arms_y=32, arm_x=17, arm_len=28,
                 size=0.85),
}


def pose(**kw):
    p = dict(DEFAULT)
    p.update(kw)
    return p


def head_path(K, jaw=0.0):
    hw, top, chin = K["hw"], K["top"], K["chin"] + jaw
    h = K["head"]
    if h == "tri":
        return rounded_poly([(-hw, top), (hw, top), (0, chin)], 16)
    if h == "tri_round":
        return smooth_path([(-hw, top + 4), (-hw * 0.2, top - 2), (hw * 0.2, top - 2), (hw, top + 4),
                            (hw * 0.55, chin * 0.35), (0, chin), (-hw * 0.55, chin * 0.35)])
    if h == "square":
        return rounded_poly([(-hw, top), (hw, top + 2), (hw * 0.92, chin), (-hw * 0.94, chin - 2)], 14)
    # round / heart-ish
    return smooth_path([(-hw, -10), (-hw * 0.8, top * 0.85), (0, top), (hw * 0.8, top * 0.85), (hw, -6),
                        (hw * 0.62, chin * 0.7), (0, chin), (-hw * 0.62, chin * 0.7)])


def body_path(K, kind, f):
    bx, by, rx, ry = K["body"]
    bx *= f
    if kind == "pip":  # leaf-shaped body tapering to the tail end
        pts = [(bx - rx * f * 0.95, by - ry * 0.2), (bx - rx * 0.3 * f, by - ry), (bx + rx * 0.45 * f, by - ry * 0.75),
               (bx + rx * 1.0 * f, by + ry * 0.05), (bx + rx * 0.4 * f, by + ry * 0.92), (bx - rx * 0.5 * f, by + ry * 0.85)]
        return smooth_path(pts)
    return ellipse(bx, by, rx, ry)


def hatch(c, clip_path, x0, y0, x1, y1, gap=9.0, a=0.35, seed=0, width=1.6, angle=1.0):
    """Diagonal pencil hatching inside clip_path, within the box."""
    c.save()
    c.clipPath(clip_path, skia.ClipOp.kIntersect, True)
    p = skia.Path()
    span = (x1 - x0) + (y1 - y0)
    n = int(span / gap) + 2
    for i in range(n):
        sx = x0 + i * gap
        p.moveTo(sx, y0)
        p.lineTo(sx - (y1 - y0) * angle, y1)
    pencil(c, p, width, GRAPHITE, a, seed=seed, rough=0.8, double=False)
    c.restore()


def limb(c, x0, y0, a1, a2, l1, l2, width, seed, color=PAPER, hand=True, foot=False, flip=1):
    """Two-segment spindly limb. Angles in degrees, 0 = straight down."""
    r1 = math.radians(a1)
    x1, y1 = x0 + math.sin(r1) * l1 * flip, y0 + math.cos(r1) * l1
    r2 = math.radians(a1 + a2)
    x2, y2 = x1 + math.sin(r2) * l2 * flip, y1 + math.cos(r2) * l2
    p = skia.Path()
    p.moveTo(x0, y0)
    p.quadTo(x1, y1, (x1 + x2) / 2, (y1 + y2) / 2)
    p.lineTo(x2, y2)
    c.drawPath(p, stroke(GRAPHITE, width * 2.3, 1.0))
    c.drawPath(p, stroke(color, width * 1.15, 1.0))
    if hand:
        # three thin fingers fanning from a little round paw
        ang = r2
        for k in (-0.6, 0.0, 0.6):
            fx = x2 + math.sin(ang + k) * width * 3.0 * flip
            fy = y2 + math.cos(ang + k) * width * 3.0
            c.drawLine(x2, y2, fx, fy, stroke(GRAPHITE, width * 1.5))
            c.drawLine(x2, y2, fx, fy, stroke(color, width * 0.6))
        c.drawCircle(x2, y2, width * 1.5, fill(color))
        c.drawCircle(x2, y2, width * 1.5, stroke(GRAPHITE, 1.4))
    if foot:
        r = skia.Rect.MakeLTRB(x2 - width * 2.4, y2 - width * 1.2, x2 + width * 2.8 * flip, y2 + width * 0.8)
        r.sort()
        c.drawOval(r, fill(color))
        c.drawOval(r, stroke(GRAPHITE, 1.6))
    return x2, y2


def draw_eye(c, K, P, side, ex, ey, er, seed):
    style = K["eye_style"]
    lid = clamp(P["lid"])
    ink = P["ink"]
    if lid >= 0.85:
        # shut: lids meet a little below the middle -> a soft curved line, like a blink or sleep
        if ink > 0:
            c.drawCircle(ex, ey, er * 1.9, fill(SOCKET, 1.0, rad_grad((ex, ey), er * 1.9,
                                                                        [(*SOCKET, 0.5 * ink), (*SOCKET, 0.22 * ink),
                                                                         (*SOCKET, 0.0)], [0.45, 0.72, 1.0])))
        eye = circle(ex, ey, er)
        c.drawPath(eye, fill(PAPER))
        cc = P["closed_curve"]
        p = skia.Path()
        p.moveTo(ex - er * 0.95, ey + er * 0.1)
        p.quadTo(ex, ey + er * 0.1 + er * (0.45 - cc * 0.9), ex + er * 0.95, ey + er * 0.1)
        c.drawPath(p, stroke(GRAPHITE, 2.6))
        for k in (-0.5, 0.0, 0.5):  # tiny lashes so a blink reads as a blink
            lx = ex + k * er * 0.8
            ly = ey + er * 0.1 + er * (0.45 - cc * 0.9) * (1 - k * k) * 0.95
            c.drawLine(lx, ly, lx + k * er * 0.25, ly + er * 0.28, stroke(GRAPHITE, 1.4, 0.8))
        pencil(c, eye, 2.2, GRAPHITE, 0.6, seed=seed + side * 7, rough=0.6)
        return
    # dark gothic socket
    if ink > 0:
        c.drawCircle(ex, ey, er * 1.9, fill(SOCKET, 1.0, rad_grad((ex, ey), er * 1.9,
                                                                    [(*SOCKET, 0.62 * ink), (*SOCKET, 0.30 * ink), (*SOCKET, 0.0)],
                                                                    [0.45, 0.72, 1.0])))
    eye = circle(ex, ey, er)
    c.drawPath(eye, fill(PAPER_HI))
    lx, ly = P["look"]
    pr = er * (0.36 if style != "big" else 0.46) * P["pupil"]
    px = ex + lx * (er - pr) * 0.72
    py = ey + ly * (er - pr) * 0.62
    c.save()
    c.clipPath(eye, skia.ClipOp.kIntersect, True)
    if style == "ring":
        ir = er * 0.62
        ix, iy = ex + lx * (er - ir) * 0.8, ey + ly * (er - ir) * 0.7
        c.drawCircle(ix, iy, ir, stroke(GRAPHITE, 1.6, 0.9))
        sp = spiral_pts(ix, iy, ir * 0.15, ir * 0.85, 1.6, a0=seed * 0.0, n=26)
        c.drawPath(open_path(sp), stroke(GRAPHITE, 1.1, 0.45))
    c.drawCircle(px, py, pr, fill(INK))
    c.drawCircle(px - pr * 0.35, py - pr * 0.4, max(1.2, pr * 0.32), fill((255, 255, 255), 0.95))
    if style == "big":
        c.drawCircle(px + pr * 0.4, py + pr * 0.35, max(0.8, pr * 0.15), fill((255, 255, 255), 0.8))
    if P["glisten"] > 0:
        g = P["glisten"]
        c.drawPath(open_path([(ex - er * 0.8, ey + er * 0.55), (ex, ey + er * 0.85), (ex + er * 0.8, ey + er * 0.55)]),
                   stroke(TEAR, er * 0.22, 0.8 * g))
        c.drawCircle(px + pr * 0.5, py - pr * 0.1, pr * 0.22, fill((255, 255, 255), 0.9 * g))
    # upper lid: paper coloured cover, angled edge
    tilt = P["lid_tilt"] * (1 if side > 0 else -1)
    if lid > 0.001:
        edge = ey - er * 1.05 + lid * er * 2.1
        dy = tilt * er * 0.35
        lidp = skia.Path()
        lidp.moveTo(ex - er * 1.3, ey - er * 1.3)
        lidp.lineTo(ex + er * 1.3, ey - er * 1.3)
        lidp.lineTo(ex + er * 1.3, edge + dy)
        lidp.quadTo(ex, edge + er * 0.25 * (1 - lid) - dy * 0.2, ex - er * 1.3, edge - dy)
        lidp.close()
        c.drawPath(lidp, fill(PAPER))
        c.drawPath(lidp, stroke(GRAPHITE, 2.0, 0.9))
    lo = clamp(P["lid_low"])
    if lo > 0.001:
        edge = ey + er * 1.05 - lo * er * 1.1
        lp = skia.Path()
        lp.moveTo(ex - er * 1.3, ey + er * 1.3)
        lp.lineTo(ex + er * 1.3, ey + er * 1.3)
        lp.lineTo(ex + er * 1.3, edge)
        lp.quadTo(ex, edge - er * 0.35 * lo, ex - er * 1.3, edge)
        lp.close()
        c.drawPath(lp, fill(PAPER))
        c.drawPath(lp, stroke(GRAPHITE, 1.8, 0.85))
    c.restore()
    if lid > 0.96:  # fully shut: draw the closed-eye curve over everything
        cc = P["closed_curve"]
        c.drawPath(open_path([(ex - er, ey), (ex, ey - cc * er * 0.55), (ex + er, ey)]), stroke(GRAPHITE, 2.4))
    pencil(c, eye, 2.2, GRAPHITE, 0.95, seed=seed + side * 7, rough=0.6)


def draw_brow(c, P, side, ex, ey, er, seed):
    by = ey - er * 1.55 - P["brow"] * er * 0.55
    tilt = P["brow_tilt"]
    inner = (ex - side * er * 0.75, by - tilt * er * 0.45)
    outer = (ex + side * er * 0.85, by + tilt * er * 0.30)
    mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 - er * 0.12)
    c.drawPath(open_path([inner, mid, outer]), stroke(GRAPHITE, 3.0, 0.95))


def draw_mouth(c, K, P, ox, seed, jaw=0.0):
    ny, my, mw = K["nose_y"], K["mouth_y"], K["mw"]
    smile = P["smile"]
    op = clamp(P["mouth"])
    rnd, wide = clamp(P["mround"]), clamp(P["mwide"])
    # nose
    nose = smooth_path([(ox - 5, ny - 3), (ox + 5, ny - 3), (ox + 1.5, ny + 3.5), (ox - 1.5, ny + 3.5)])
    c.drawPath(nose, fill(INK))
    c.drawLine(ox, ny + 3, ox, my - 1, stroke(GRAPHITE, 2.0))
    w = mw * (1 + 0.45 * wide - 0.35 * rnd)
    if op > 0.04:
        h = (4 + 0.85 * jaw + 8 * op) * (1 + 0.25 * rnd - 0.2 * wide)
        ww = w * (0.85 + 0.3 * wide - 0.35 * rnd)
        top = my - 1
        mp = skia.Path()
        mp.moveTo(ox - ww, top - smile * 4)
        mp.quadTo(ox, top + 2, ox + ww, top - smile * 4)
        mp.quadTo(ox + ww * (1.0 - 0.25 * rnd), top + h * 0.9, ox, top + h)
        mp.quadTo(ox - ww * (1.0 - 0.25 * rnd), top + h * 0.9, ox - ww, top - smile * 4)
        mp.close()
        c.drawPath(mp, fill(MOUTH_IN))
        c.save()
        c.clipPath(mp, skia.ClipOp.kIntersect, True)
        c.drawOval(skia.Rect.MakeLTRB(ox - ww * 0.7, top + h * 0.55, ox + ww * 0.7, top + h * 1.3), fill(TONGUE))
        if P["teeth"] > 0:
            tw = max(2.5, ww * 0.28)
            c.drawRect(skia.Rect.MakeLTRB(ox - tw, top, ox - 0.6, top + tw * 1.3), fill(PAPER_HI))
            c.drawRect(skia.Rect.MakeLTRB(ox + 0.6, top, ox + tw, top + tw * 1.3), fill(PAPER_HI))
        c.restore()
        c.drawPath(mp, stroke(GRAPHITE, 2.0))
    else:
        # the drawing's little 'w' mouth
        lc = (ox - w, my - smile * 6 - 1)
        rc = (ox + w, my - smile * 6 - 1)
        dip = 4 + 3 * max(0, smile)
        p = skia.Path()
        p.moveTo(*lc)
        p.quadTo(ox - w * 0.5, my + dip, ox, my)
        p.quadTo(ox + w * 0.5, my + dip, rc[0], rc[1])
        c.drawPath(p, stroke(GRAPHITE, 2.2))
        if smile < -0.2:  # frown: corners pulled down
            c.drawLine(lc[0], lc[1], lc[0] - 3, lc[1] - smile * 7, stroke(GRAPHITE, 2.0))
            c.drawLine(rc[0], rc[1], rc[0] + 3, rc[1] - smile * 7, stroke(GRAPHITE, 2.0))


def draw_whiskers(c, K, P, ox, seed):
    wy, L = K["whisk_y"], K["whisk_len"]
    tw = P["whisk"]
    for side in (-1, 1):
        for i, ang in enumerate((-14, 0, 14)):
            a = math.radians(ang + tw * 7 * (1 if i != 1 else -1))
            sx = ox + side * 7
            sy = wy + (i - 1) * 3
            ex = sx + side * math.cos(a) * L
            ey = sy + math.sin(a) * L
            mx = (sx + ex) / 2
            my = (sy + ey) / 2 - 5
            p = skia.Path()
            p.moveTo(sx, sy)
            p.quadTo(mx, my, ex, ey)
            # tiny curl at the tip
            p.quadTo(ex + side * 6, ey + 4, ex + side * 2, ey + 8)
            c.drawPath(p, stroke(WHISKER_HALO, 3.4, 0.55))
            c.drawPath(p, stroke(GRAPHITE, 1.4, 0.9))


def draw_ear(c, ex, ey, r, droop, perk, twitch, side, seed, ink=1.0):
    ang = side * (droop * 38 - perk * 10 + twitch * 12)
    dy = droop * r * 0.35 - perk * r * 0.25
    with Xf(c, ex, ey + dy, rot=ang):
        e = circle(0, 0, r)
        c.drawPath(e, fill(PAPER))
        if ink > 0:
            c.drawCircle(0, r * 0.08, r * 0.55, fill((196, 168, 178), ink))
            c.drawCircle(0, r * 0.08, r * 0.55, fill((0, 0, 0), 1.0,
                                                      rad_grad((0, r * 0.08), r * 0.55, [(0, 0, 0, 0.0), (0, 0, 0, 0.25 * ink)])))
        pencil(c, circle(0, r * 0.08, r * 0.55), 1.6, GRAPHITE, 0.7, seed=seed + 3)
        pencil(c, e, 2.6, GRAPHITE, 1.0, seed=seed)


def draw_tail(c, K, P, f, seed):
    bx, by, rx, ry = K["body"]
    sx, sy = f * (bx + rx * 0.95), by + ry * 0.15
    t = P["tail_t"]
    amp = P["tail_amp"]
    pts = []
    n = 9
    for i in range(n):
        u = i / (n - 1)
        x = sx + f * u * rx * 1.15
        y = sy + u * ry * 1.4 + math.sin(t * 2.2 - u * 3.0) * 14 * u * amp
        pts.append((x, y))
    ex, ey = pts[-1]
    sp = spiral_pts(ex + f * 14, ey + 2, 15, 1.5, 1.4, a0=math.pi, n=24, direction=-f)
    tail = open_path(pts + sp[1:])
    c.drawPath(tail, stroke(GRAPHITE, 6.4))
    c.drawPath(tail, stroke(PAPER_SHADE, 3.0))


def draw_pumpkin_prop(c, x, y, r, seed, alpha=1.0):
    """Little striped pumpkin with a curly vine, as in the drawing."""
    body = ellipse(x, y, r, r * 0.86)
    c.drawPath(body, fill((246, 150, 60), alpha, rad_grad((x - r * 0.3, y - r * 0.3), r * 1.4,
                                                            [(255, 182, 90), (232, 118, 34), (150, 60, 18)])))
    for k in (-0.55, 0.0, 0.55):
        p = skia.Path()
        p.moveTo(x + k * r * 0.5, y - r * 0.8)
        p.quadTo(x + k * r * 1.25, y, x + k * r * 0.5, y + r * 0.84)
        c.drawPath(p, stroke(GRAPHITE, 1.8, 0.75 * alpha))
    pencil(c, body, 2.2, GRAPHITE, alpha, seed=seed)
    c.drawLine(x, y - r * 0.8, x + 2, y - r * 1.15, stroke((70, 90, 50), 4, alpha))
    c.drawPath(open_path(spiral_pts(x + r * 0.35, y - r * 1.1, 1, r * 0.32, 1.5, a0=0, n=20)),
               stroke((70, 90, 50), 1.8, alpha))


def draw_mouse(c, kind, P):
    K = KINDS[kind]
    f = 1 if P["facing"] >= 0 else -1
    seed = P["seed"]
    s = P["scale"] * K["size"]
    flat = P["flat"]
    head_y = -(K["chin"] + K["legs"] + 18) if not flat else 0.0
    with Xf(c, P["x"], P["y"], sx=s, alpha=P["alpha"]):
        if P["upside"]:
            c.rotate(180)
        if not flat:
            # soft contact shadow
            bx = K["body"][0] * f * 0.6
            c.drawOval(skia.Rect.MakeLTRB(bx - 150, -14, bx + 150, 14),
                       fill((0, 0, 0), 0.0, rad_grad((bx, 0), 150, [(0, 0, 0, 0.45), (0, 0, 0, 0.0)])))
        c.translate(0, -P["lift"])
        c.scale(1.0 / math.sqrt(P["squash"]), P["squash"])
        c.translate(0, head_y)
        if P["lean"]:
            c.rotate(P["lean"])
        bx, by, rx, ry = K["body"]
        # tail + back legs (behind body)
        draw_tail(c, K, P, f, seed)
        ground = -head_y if not flat else None
        legs = []
        if not flat:
            wk = P["walking"]
            for i, lx in enumerate((0.15, 0.42, 0.72, 0.95)):
                xx = f * (bx - rx * 0.9 + lx * rx * 1.6)
                yy = by + ry * 0.62 - abs(lx - 0.55) * ry * 0.35
                ph = P["walk"] * 2 * math.pi + (i % 2) * math.pi + (i // 2) * 0.6
                swing = math.sin(ph) * 28 * wk
                lift = max(0, math.cos(ph)) * 10 * wk
                L = ground - yy - lift
                legs.append((i, xx, yy, swing, L))
            for i, xx, yy, swing, L in legs:
                if i in (1, 3):
                    limb(c, xx, yy, swing * f, -swing * 0.5 * f, L * 0.5, L * 0.52, 2.6, seed + i,
                         color=PAPER_SHADE, hand=False, foot=True, flip=f)
        body = body_path(K, kind, f)
        c.drawPath(body, fill(PAPER))
        hatch(c, body, f * bx - rx, by + ry * 0.15, f * bx + rx, by + ry, gap=8, a=0.30 * (0.35 + 0.65 * P["ink"]), seed=seed + 5)
        pencil(c, body, 3.0, GRAPHITE, 1.0, seed=seed + 1)
        if not flat:
            for i, xx, yy, swing, L in legs:
                if i in (0, 2):
                    limb(c, xx, yy, swing * f, -swing * 0.5 * f, L * 0.5, L * 0.52, 2.8, seed + i,
                         hand=False, foot=True, flip=f)
        # head group
        neck = (0, K["chin"] * 0.7)
        with Xf(c, 0, P["nod"]):
            c.translate(*neck)
            c.rotate(P["tilt"])
            c.translate(-neck[0], -neck[1])
            for i, (ex, ey, er) in enumerate(K["ears"]):
                draw_ear(c, ex, ey, er, P["ear_droop"], P["ear_perk"], P["ear_twitch"] * (1 if i else -1),
                         -1 if i == 0 else 1, seed + 20 + i, P["ink"])
            jaw = clamp(P["mouth"]) * K["jaw"] * (1 + 0.3 * clamp(P["mround"]))
            hp = head_path(K, jaw)
            c.drawPath(hp, fill(PAPER))
            # shading: warm light side vs cool shade side
            lx = P["light"][0]
            sh = lin_grad((-K["hw"] * lx, 0), (K["hw"] * lx, 0), [(0, 0, 0, 0.0), (20, 24, 50, 0.20)])
            if abs(lx) > 0.01:
                c.drawPath(hp, fill((0, 0, 0), 1.0, sh))
            hatch(c, hp, -K["hw"] if lx >= 0 else 0, K["top"], 0 if lx >= 0 else K["hw"], K["chin"],
                  gap=10, a=0.16 * P["ink"], seed=seed + 9)
            pencil(c, hp, 3.2, GRAPHITE, 1.0, seed=seed + 2)
            ox = P["yaw"] * K["hw"] * 0.22
            if P["blush"] > 0:
                for side in (-1, 1):
                    cx = ox + side * K["eye_dx"] * 1.25
                    cy = K["eye_y"] + K["eye_r"] * 1.9
                    c.drawCircle(cx, cy, K["eye_r"] * 0.9,
                                 fill((255, 120, 140), 1.0, rad_grad((cx, cy), K["eye_r"] * 0.9,
                                                                    [(255, 120, 140, 0.45 * P["blush"]), (255, 120, 140, 0)])))
            for side in (-1, 1):
                ex = ox + side * K["eye_dx"]
                ey = K["eye_y"]
                if P["sleep"]:
                    c.drawPath(open_path([(ex - K["eye_r"], ey), (ex, ey + K["eye_r"] * 0.45), (ex + K["eye_r"], ey)]),
                               stroke(GRAPHITE, 2.6))
                else:
                    draw_eye(c, K, P, side, ex, ey, K["eye_r"], seed + 30)
                    draw_brow(c, P, side, ex, ey, K["eye_r"], seed + 40)
            if P["tear"] > 0:
                tp = P["tear"]
                tx = ox + K["eye_dx"] * 0.9
                ty = K["eye_y"] + K["eye_r"] * (1.1 + tp * 3.2)
                a = clamp(1.5 - tp * 1.3)
                drop = smooth_path([(tx, ty - 7), (tx + 4.5, ty + 2), (tx, ty + 6), (tx - 4.5, ty + 2)])
                c.drawPath(drop, fill(TEAR, 0.85 * a))
                c.drawPath(drop, stroke((90, 130, 170), 1.2, a))
            draw_mouth(c, K, P, ox, seed + 50, jaw)
            draw_whiskers(c, K, P, ox, seed + 60)
        # arms in front
        if not flat:
            ay = K["arms_y"]
            for side, key in ((-1, "arm_l"), (1, "arm_r")):
                a1, a2 = P[key]
                limb(c, side * K["arm_x"], ay, a1 * side, a2 * side, K["arm_len"], K["arm_len"] * 0.95, 2.7,
                     seed + 70 + side, hand=True, flip=1)
            if P["prop"] == "pumpkin":
                draw_pumpkin_prop(c, 0, ay + 44, 24, seed + 90)
