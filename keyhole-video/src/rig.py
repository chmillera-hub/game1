"""Character rigs: expressive cartoon faces, humans and emotion-creatures."""
import math
import numpy as np
import skia
import gfx
from gfx import (fill, stroke, shade, alpha, mixc, hexc, ellipse, path_poly, smooth_closed, smooth_open,
                 clamp, lerp, smooth, wobble, rad_grad, lin_grad)

FACE = dict(
    lookx=0.0, looky=0.0, lid=1.0, lidL=0.0, lidR=0.0, lower=0.0, lid_tilt=0.0, squeeze=0.0, happy=0.0,
    brow=0.0, browL=0.0, browR=0.0, brow_ang=0.0, brow_angL=0.0, brow_angR=0.0,
    smile=0.1, open=0.0, wide=1.0, round=0.0, smirk=0.0, press=0.0, teeth=1.0, puff=0.0,
    blush=0.0, tears=0.0, stream=0.0, sweat=0.0, pupil=1.0,
    turn=0.0, tilt=0.0, nod=0.0,
)
gfx.DEFAULTS_FACE.update(FACE)

# Expression presets (only the keys that differ from neutral)
EXPR = {
    "neutral": {},
    "attentive": dict(lid=1.05, brow=0.15, smile=0.05),
    "smile": dict(smile=0.6, lower=0.25, brow=0.1),
    "grin": dict(smile=0.9, open=0.25, lower=0.4, brow=0.2, teeth=1.0),
    "warm": dict(smile=0.45, lower=0.3, brow=0.05, brow_ang=0.25, lid=0.92),
    "sad": dict(smile=-0.35, brow_ang=0.8, brow=0.05, lid=0.78, lid_tilt=-0.5),
    "hurt": dict(smile=-0.2, brow_ang=0.65, brow=0.1, lid=0.85, lid_tilt=-0.35, press=0.3),
    "worried": dict(smile=-0.25, brow_ang=0.75, brow=0.25, lid=1.05),
    "angry": dict(smile=-0.4, brow_ang=-0.85, brow=-0.3, lid=0.85, lid_tilt=0.6, press=0.4),
    "stern": dict(smile=-0.15, brow_ang=-0.45, brow=-0.25, lid=0.82, lid_tilt=0.3, press=0.5),
    "surprised": dict(lid=1.2, brow=0.85, open=0.35, round=0.6, smile=0.0, pupil=0.85),
    "shocked": dict(lid=1.22, brow=1.0, open=0.55, round=0.5, smile=-0.2, pupil=0.7),
    "deadpan": dict(lid=0.62, smile=0.0, press=0.25, brow=-0.05),
    "tired": dict(lid=0.55, smile=-0.05, brow_ang=0.3, brow=-0.1, lid_tilt=-0.25),
    "smug": dict(lid=0.7, smile=0.35, smirk=0.7, brow=0.1, browR=0.25, brow_angL=-0.2),
    "suspicious": dict(lid=0.6, lower=0.35, smile=-0.1, smirk=-0.3, brow_angL=-0.5, browR=0.4),
    "hold_laugh": dict(press=1.0, puff=0.85, smile=0.25, brow=0.55, brow_ang=0.45, lid=0.85, lower=0.45, tears=0.6, blush=0.6),
    "wary": dict(lid=0.85, brow=-0.1, brow_ang=-0.2, smile=-0.1, press=0.35),
    "tender": dict(smile=0.3, lower=0.25, brow_ang=0.45, brow=0.1, lid=0.88),
    "ashamed": dict(smile=-0.25, brow_ang=0.7, lid=0.7, lid_tilt=-0.3, press=0.4),
    "panic": dict(lid=1.22, brow=1.0, brow_ang=0.8, open=0.6, smile=-0.4, pupil=0.6, sweat=1.0),
    "relief": dict(smile=0.4, lid=0.75, brow_ang=0.4, lower=0.2),
    "laughing": dict(happy=1.0, smile=1.0, open=0.6, brow=0.45, brow_ang=0.3, blush=0.4),
    "unimpressed": dict(lid=0.68, smile=-0.12, brow=-0.05, browR=0.45, brow_angR=-0.2, press=0.3, smirk=-0.2),
    "glassy": dict(tears=0.8, lid=0.82, brow_ang=0.55, lid_tilt=-0.25),
}


def expr(name, **over):
    d = dict(EXPR[name])
    d.update(over)
    return d


def ex_mix(a, b, t):
    return gfx.blend(a, b, t)


# ======================================================================= FACE
OUT_ALPHA = 1.0


class Look:
    """Visual design of a character's face."""

    def __init__(self, skin, iris="#4a3426", brow="#3a2a20", eye_sp=0.37, eye_y=0.05, eye_rx=0.2, eye_ry=0.24,
                 mouth_y=0.56, nose=1.0, lash=False, stubble=None, glasses=None, freckles=False, mustache=None,
                 outline=None, cheek="#f08a8a", brow_th=1.0, mouth_w=0.40):
        self.skin = skin
        self.iris = iris
        self.brow = brow
        self.eye_sp, self.eye_y, self.eye_rx, self.eye_ry = eye_sp, eye_y, eye_rx, eye_ry
        self.mouth_y = mouth_y
        self.nose = nose
        self.lash = lash
        self.stubble = stubble
        self.glasses = glasses
        self.freckles = freckles
        self.mustache = mustache
        self.outline = outline or shade(skin, 0.62)
        self.cheek = cheek
        self.brow_th = brow_th
        self.mouth_w = mouth_w


def yaw_of(P):
    return P["turn"] * 0.62


def eye_geom(L, R, P, side):
    yaw = yaw_of(P)
    th = side * 0.39 * (L.eye_sp / 0.36)
    ws = max(0.25, math.cos(th + yaw) / math.cos(th))
    x = R * 0.93 * math.sin(th + yaw)
    fy = P["nod"] * 0.13 * R
    y = (L.eye_y * R) + fy
    return x, y, L.eye_rx * R * ws, L.eye_ry * R * (1 - 0.08 * abs(P["nod"])), ws


def draw_eye(cv, L, R, P, side):
    cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
    u = P["lid"] + (P["lidL"] if side < 0 else P["lidR"])
    lower = P["lower"]
    tilt = P["lid_tilt"]
    lash_c = shade(L.brow, 0.6)
    lw = 0.13 * L.eye_ry * R
    sq = P["squeeze"]
    hp = P["happy"]
    if sq > 0.5:
        # >  < squeezed eyes
        inner = -side
        p = skia.Path()
        p.moveTo(cx + side * rx * 0.9, cy - ry * 0.55)
        p.lineTo(cx + inner * rx * 0.75, cy + ry * 0.05)
        p.lineTo(cx + side * rx * 0.9, cy + ry * 0.6)
        cv.drawPath(p, stroke(lash_c, lw * 1.1))
        return
    if hp > 0.5 or u < 0.12:
        p = skia.Path()
        if hp > 0.5:
            p.moveTo(cx - rx * 1.0, cy + ry * 0.25)
            p.quadTo(cx, cy - ry * 0.85, cx + rx * 1.0, cy + ry * 0.25)
        else:
            p.moveTo(cx - rx * 1.02, cy + ry * 0.12 + tilt * side * 0.1 * ry)
            p.quadTo(cx, cy + ry * 0.45, cx + rx * 1.02, cy + ry * 0.12 - tilt * side * 0.1 * ry)
        cv.drawPath(p, stroke(lash_c, lw))
        if P["tears"] > 0.3 and hp <= 0.5:
            cv.drawPath(p, stroke(alpha("#bfe6ff", 0.6 * P["tears"]), lw * 0.5))
        return
    eye = ellipse(cx, cy, rx, ry)
    skin = L.skin
    ue = clamp(u, 0.0, 1.25)
    ye = cy + ry * (0.15 - 0.78 * ue)
    y_in = ye + tilt * 0.38 * ry
    y_out = ye - tilt * 0.38 * ry
    inner_x = cx - side * rx * 1.15
    outer_x = cx + side * rx * 1.15
    ctrl_y = ye - 0.42 * ry * clamp(ue, 0, 1) - 0.06 * ry
    lid = skia.Path()
    lid.moveTo(inner_x, y_in)
    lid.quadTo(cx, ctrl_y, outer_x, y_out)
    lid.lineTo(outer_x, cy - ry * 2)
    lid.lineTo(inner_x, cy - ry * 2)
    lid.close()
    edge = skia.Path()
    edge.moveTo(inner_x, y_in)
    edge.quadTo(cx, ctrl_y, outer_x, y_out)
    low_eff = max(lower, (0.3 - ue) / 0.3 * 0.7 if ue < 0.3 else 0.0)
    lc_y = cy + ry * (1.45 - 2.3 * low_eff)
    ll = skia.Path()
    ll.moveTo(cx - rx * 1.2, cy + ry * 0.35)
    ll.quadTo(cx, lc_y, cx + rx * 1.2, cy + ry * 0.35)
    ll.lineTo(cx + rx * 1.2, cy + ry * 2)
    ll.lineTo(cx - rx * 1.2, cy + ry * 2)
    ll.close()
    vis = skia.Op(eye, lid, skia.PathOp.kDifference_PathOp)
    if vis is not None:
        vis = skia.Op(vis, ll, skia.PathOp.kDifference_PathOp)
    if vis is None or vis.isEmpty():
        vis = None
    if vis is not None:
        cv.save()
        cv.clipPath(vis, doAntiAlias=True)
        cv.drawPath(eye, fill("#fbfaf7"))
        cv.drawPath(eye, rad_grad((cx, cy + ry * 0.4), ry * 1.6, [(1, 1, 1, 0), alpha("#c9c0d0", 0.55)], [0.55, 1.0]))
        ri = 0.62 * L.eye_rx * R
        ix = cx + P["lookx"] * 0.45 * rx
        iy = cy + P["looky"] * 0.38 * ry
        cv.save()
        cv.translate(ix, iy)
        cv.scale(ws * 0.9 + 0.1, 1.0)
        cv.drawCircle(0, 0, ri, fill(L.iris))
        cv.drawCircle(0, 0, ri, rad_grad((0, -ri * 0.3), ri * 1.1, [shade(L.iris, 1.35), shade(L.iris, 0.75)], [0.0, 1.0]))
        pr = ri * 0.52 * P["pupil"]
        cv.drawCircle(0, 0, pr, fill("#140c0a"))
        g = 1.0 + 0.5 * P["tears"]
        cv.drawCircle(-ri * 0.36, -ri * 0.4, ri * 0.3 * g, fill((1, 1, 1, 0.95)))
        cv.drawCircle(ri * 0.38, ri * 0.32, ri * 0.13 * g, fill((1, 1, 1, 0.85)))
        if P["tears"] > 0.2:
            cv.drawCircle(-ri * 0.05, ri * 0.55, ri * 0.09, fill((1, 1, 1, 0.7 * P["tears"])))
        cv.restore()
        # upper lid shadow on the eyeball
        sh = skia.Path(lid)
        sh.offset(0, ry * 0.12)
        cv.drawPath(sh, fill(alpha("#6a5060", 0.18)))
        if P["tears"] > 0.05:
            wl = skia.Path()
            wl.moveTo(cx - rx, cy + ry * 0.55)
            wl.quadTo(cx, cy + ry * 1.05, cx + rx, cy + ry * 0.55)
            cv.drawPath(wl, stroke(alpha("#d6f1ff", 0.85 * P["tears"]), ry * 0.22))
        cv.restore()
        cv.drawPath(vis, stroke(alpha(L.outline, 0.45), lw * 0.35))
    cv.save()
    cv.clipPath(ellipse(cx, cy, rx * 1.08, ry * 1.12), doAntiAlias=True)
    if low_eff > 0.12:
        le = skia.Path()
        le.moveTo(cx - rx * 1.2, cy + ry * 0.35)
        le.quadTo(cx, lc_y, cx + rx * 1.2, cy + ry * 0.35)
        cv.drawPath(le, stroke(alpha(L.outline, 0.6), lw * 0.4))
    cv.drawPath(edge, stroke(lash_c, lw))
    cv.restore()
    # lash flick at outer corner
    if L.lash:
        fl = skia.Path()
        ox = cx + side * rx * 0.92
        oy = cy - ry * 0.45 + (y_out - (cy - ry * 0.75)) * 0.6
        fl.moveTo(ox, oy)
        fl.quadTo(ox + side * rx * 0.28, oy - ry * 0.1, ox + side * rx * 0.38, oy - ry * 0.32)
        cv.drawPath(fl, stroke(lash_c, lw * 0.75))


def draw_brow(cv, L, R, P, side):
    cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
    rise = P["brow"] + (P["browL"] if side < 0 else P["browR"])
    ang = P["brow_ang"] + (P["brow_angL"] if side < 0 else P["brow_angR"])
    ry0 = L.eye_ry * R
    base = cy - ry0 * 1.38 - rise * 0.42 * ry0
    ix = cx - side * rx * 0.85
    ox = cx + side * rx * 1.1
    iy = base - ang * 0.45 * ry0
    oy = base + ang * 0.12 * ry0 + 0.08 * ry0
    mx = (ix + ox) / 2
    my = min(iy, oy) - 0.24 * ry0 * (1 - 0.6 * abs(ang)) + (0.1 * ry0 if ang < -0.3 else 0)
    th_i = 0.30 * ry0 * L.brow_th
    th_o = 0.12 * ry0 * L.brow_th
    p = skia.Path()
    p.moveTo(ix, iy - th_i / 2)
    p.quadTo(mx, my - (th_i + th_o) / 4, ox, oy - th_o / 2)
    p.quadTo(ox + side * th_o * 0.6, oy, ox, oy + th_o / 2)
    p.quadTo(mx, my + (th_i + th_o) / 4, ix, iy + th_i / 2)
    p.quadTo(ix - side * th_i * 0.55, iy, ix, iy - th_i / 2)
    p.close()
    cv.drawPath(p, fill(L.brow))


def draw_mouth(cv, L, R, P):
    yaw = yaw_of(P)
    ws = math.cos(yaw)
    mx = R * 0.86 * math.sin(yaw)
    my = L.mouth_y * R + P["nod"] * 0.1 * R
    op = clamp(P["open"], 0, 1.2)
    sm = P["smile"]
    rnd = clamp(P["round"], 0, 1)
    press = clamp(P["press"], 0, 1)
    W = L.mouth_w * R * P["wide"] * ws * (1 - 0.45 * rnd) * (1 + 0.15 * max(sm, 0)) * (1 - 0.3 * press)
    hw = W / 2
    lift = sm * 0.11 * R
    sk = P["smirk"] * 0.07 * R
    Lc = (mx - hw, my - lift + sk * 0.5)
    Rc = (mx + hw, my - lift - sk)
    dark = "#4a1d24"
    lc = shade(L.skin, 0.45)
    lw = 0.045 * R
    if op < 0.05:
        p = skia.Path()
        p.moveTo(*Lc)
        cyy = my + sm * 0.12 * R * (1 - 0.6 * press) + (0.0 if sm >= 0 else 0.0)
        p.quadTo(mx + sk * 0.3, cyy, *Rc)
        cv.drawPath(p, stroke(lc, lw * (1 + 0.3 * press)))
        if press > 0.4:
            for s, c in ((-1, Lc), (1, Rc)):
                q = skia.Path()
                q.moveTo(c[0] + s * 0.01 * R, c[1] - 0.035 * R)
                q.quadTo(c[0] + s * 0.035 * R, c[1], c[0] + s * 0.01 * R, c[1] + 0.035 * R)
                cv.drawPath(q, stroke(alpha(lc, 0.7 * press), lw * 0.6))
        return
    o = op * 0.34 * R * (1 + 0.35 * rnd)
    top_c = (mx, my - 0.015 * R - rnd * o * 0.9 + max(sm, 0) * 0.02 * R)
    bot_c = (mx, my + o * 1.55 + max(sm, 0) * 0.13 * R + min(sm, 0) * 0.05 * R)
    p = skia.Path()
    p.moveTo(*Lc)
    p.quadTo(*top_c, *Rc)
    p.quadTo(*bot_c, *Lc)
    p.close()
    cv.drawPath(p, fill(dark))
    cv.save()
    cv.clipPath(p, doAntiAlias=True)
    top_y = min(Lc[1], Rc[1], (Lc[1] + Rc[1]) / 4 + top_c[1] / 2)
    if P["teeth"] > 0.1 and rnd < 0.6:
        th = 0.075 * R * P["teeth"]
        tp = skia.Path()
        tp.moveTo(Lc[0], Lc[1] - 0.05 * R)
        tp.quadTo(top_c[0], top_c[1] - 0.05 * R, Rc[0], Rc[1] - 0.05 * R)
        tp.lineTo(Rc[0], Rc[1] + th)
        tp.quadTo(top_c[0], top_c[1] + th, Lc[0], Lc[1] + th)
        tp.close()
        cv.drawPath(tp, fill("#fffaf2"))
    if op > 0.25:
        by = (Lc[1] + Rc[1]) / 4 + bot_c[1] / 2
        cv.drawOval(skia.Rect.MakeLTRB(mx - hw * 0.6, by - o * 0.55, mx + hw * 0.6, by + o * 0.5), fill("#d9646b"))
    cv.restore()
    cv.drawPath(p, stroke(lc, lw * 0.8))


def head_path(R, jaw=0.55, chin=1.02, puff=0.0, crown=1.32, cheek=1.0, yaw=0.0):
    p = _head_base(R, jaw, chin, puff, crown, cheek)
    if puff > 0.05:
        for side in (-1, 1):
            c = skia.Path()
            cx = side * 0.62 * R + 0.25 * R * math.sin(yaw)
            c.addCircle(cx + side * 0.12 * R * puff, 0.5 * R, 0.33 * R * puff)
            p = skia.Op(p, c, skia.PathOp.kUnion_PathOp) or p
    return p


def _head_base(R, jaw, chin, puff, crown, cheek):
    p = skia.Path()
    w = R * cheek
    p.moveTo(-R, -0.05 * R)
    p.cubicTo(-R * 1.0, -crown * R, R * 1.0, -crown * R, R, -0.05 * R)
    p.cubicTo(w, 0.55 * R, jaw * R, chin * R, 0, chin * R)
    p.cubicTo(-jaw * R, chin * R, -w, 0.55 * R, -R, -0.05 * R)
    p.close()
    return p


def draw_face(cv, L, R, P, t=0.0):
    """Draw features in head-local coords (head center at 0,0)."""
    yaw = yaw_of(P)
    # blush
    if P["blush"] > 0.01:
        for side in (-1, 1):
            cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
            bx, by = cx + side * 0.05 * R, cy + 0.36 * R
            cv.drawOval(skia.Rect.MakeLTRB(bx - 0.2 * R * ws, by - 0.1 * R, bx + 0.2 * R * ws, by + 0.1 * R),
                        rad_grad((bx, by), 0.2 * R, [alpha(L.cheek, 0.55 * P["blush"]), alpha(L.cheek, 0.0)]))
    if L.freckles:
        for side in (-1, 1):
            cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
            for k, (dx, dy) in enumerate([(-0.08, 0.3), (0.02, 0.33), (0.1, 0.29), (-0.02, 0.4), (0.07, 0.38)]):
                cv.drawCircle(cx + dx * R * ws, cy + dy * R, 0.014 * R, fill(alpha(shade(L.skin, 0.7), 0.8)))
    # nose
    nx = R * 1.0 * math.sin(yaw)
    ny = 0.30 * R + P["nod"] * 0.12 * R
    s = 1 if P["turn"] >= 0 else -1
    nsz = L.nose
    np_ = skia.Path()
    if nsz > 0:
        cv.drawOval(skia.Rect.MakeLTRB(nx - 0.09 * R * nsz, ny - 0.02 * R, nx + 0.09 * R * nsz, ny + 0.08 * R * nsz),
                    rad_grad((nx, ny + 0.03 * R), 0.1 * R * nsz, [alpha(shade(L.skin, 0.7), 0.35), alpha(shade(L.skin, 0.7), 0.0)]))
        np_.moveTo(nx + s * 0.035 * R, ny - 0.07 * R * nsz)
        np_.quadTo(nx + s * 0.1 * R * nsz, ny + 0.04 * R * nsz, nx - s * 0.0 * R, ny + 0.055 * R * nsz)
        np_.quadTo(nx - s * 0.04 * R, ny + 0.06 * R * nsz, nx - s * 0.06 * R * nsz, ny + 0.035 * R * nsz)
        cv.drawPath(np_, stroke(shade(L.skin, 0.68), 0.035 * R))
    for side in (-1, 1):
        draw_eye(cv, L, R, P, side)
    for side in (-1, 1):
        draw_brow(cv, L, R, P, side)
    if L.glasses:
        for side in (-1, 1):
            cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
            g = skia.Rect.MakeLTRB(cx - L.eye_rx * R * 1.45 * ws, cy - L.eye_ry * R * 1.25, cx + L.eye_rx * R * 1.45 * ws, cy + L.eye_ry * R * 1.25)
            cv.drawRoundRect(g, L.eye_rx * R * 0.9, L.eye_rx * R * 0.9, fill((1, 1, 1, 0.12)))
            cv.drawRoundRect(g, L.eye_rx * R * 0.9, L.eye_rx * R * 0.9, stroke(L.glasses, 0.05 * R))
        lx = eye_geom(L, R, P, -1)
        rx_ = eye_geom(L, R, P, 1)
        br = skia.Path()
        br.moveTo(lx[0] + L.eye_rx * R * 1.45 * lx[4], lx[1] - 0.05 * R)
        br.quadTo((lx[0] + rx_[0]) / 2, lx[1] - 0.12 * R, rx_[0] - L.eye_rx * R * 1.45 * rx_[4], rx_[1] - 0.05 * R)
        cv.drawPath(br, stroke(L.glasses, 0.045 * R))
    if L.mustache:
        mx = R * 0.86 * math.sin(yaw)
        my = L.mouth_y * R + P["nod"] * 0.1 * R - 0.11 * R
        m = skia.Path()
        m.moveTo(mx - 0.36 * R, my + 0.1 * R)
        m.quadTo(mx - 0.22 * R, my - 0.12 * R, mx, my - 0.04 * R)
        m.quadTo(mx + 0.22 * R, my - 0.12 * R, mx + 0.36 * R, my + 0.1 * R)
        m.quadTo(mx + 0.18 * R, my + 0.04 * R, mx, my + 0.05 * R)
        m.quadTo(mx - 0.18 * R, my + 0.04 * R, mx - 0.36 * R, my + 0.1 * R)
        m.close()
    draw_mouth(cv, L, R, P)
    if L.mustache:
        cv.drawPath(m, fill(L.mustache))
    # tear streams
    if P["stream"] > 0.02:
        for side in (-1, 1):
            cx, cy, rx, ry, ws = eye_geom(L, R, P, side)
            sx, sy = cx + side * rx * 0.55, cy + ry * 0.8
            ln = 0.55 * R * clamp(P["stream"], 0, 1)
            tp = skia.Path()
            tp.moveTo(sx, sy)
            tp.cubicTo(sx + side * 0.04 * R, sy + ln * 0.3, sx - side * 0.02 * R, sy + ln * 0.7, sx + side * 0.03 * R, sy + ln)
            cv.drawPath(tp, stroke(alpha("#aee0ff", 0.75), 0.05 * R))
            cv.drawCircle(sx + side * 0.03 * R, sy + ln, 0.04 * R, fill(alpha("#aee0ff", 0.85)))
    if P["sweat"] > 0.02:
        sx = 0.78 * R + R * 0.2 * math.sin(yaw)
        sy = -0.38 * R + 0.12 * R * (math.sin(t * 2.0) * 0.5 + 0.5)
        dp = skia.Path()
        sz = 0.11 * R * P["sweat"]
        dp.moveTo(sx, sy - sz * 1.6)
        dp.cubicTo(sx + sz * 1.1, sy - sz * 0.2, sx + sz, sy + sz, sx, sy + sz)
        dp.cubicTo(sx - sz, sy + sz, sx - sz * 1.1, sy - sz * 0.2, sx, sy - sz * 1.6)
        cv.drawPath(dp, fill("#bfe9ff"))
        cv.drawPath(dp, stroke("#6fb3d9", 0.02 * R))
        cv.drawCircle(sx - sz * 0.3, sy + sz * 0.1, sz * 0.25, fill((1, 1, 1, 0.9)))


# ======================================================================= IK / limbs
def ik2(sx, sy, tx, ty, L1, L2, bend):
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = clamp(d, abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3)
    a = math.atan2(dy, dx)
    cA = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1)
    A_ = math.acos(cA)
    a1 = a + bend * A_
    ex, ey = sx + L1 * math.cos(a1), sy + L1 * math.sin(a1)
    hx, hy = sx + d * math.cos(a), sy + d * math.sin(a)
    return (ex, ey), (hx, hy)


def draw_limb(cv, pts, width, col, outline, ow):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    cv.drawPath(p, stroke(outline, width + ow * 2))
    cv.drawPath(p, stroke(col, width))


def draw_hand(cv, x, y, r, ang, skin, outline, ow, kind="mitt"):
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang) - 90)
    if kind == "fist":
        cv.drawCircle(0, 0, r, fill(skin))
        cv.drawCircle(0, 0, r, stroke(outline, ow))
        q = skia.Path()
        q.moveTo(-r * 0.5, r * 0.1)
        q.quadTo(0, r * 0.45, r * 0.5, r * 0.1)
        cv.drawPath(q, stroke(alpha(outline, 0.7), ow * 0.8))
    elif kind == "point":
        f = skia.Rect.MakeLTRB(-r * 0.22, r * 0.2, r * 0.22, r * 1.75)
        cv.drawRoundRect(f, r * 0.22, r * 0.22, fill(skin))
        cv.drawRoundRect(f, r * 0.22, r * 0.22, stroke(outline, ow))
        cv.drawCircle(0, 0, r, fill(skin))
        cv.drawCircle(0, 0, r, stroke(outline, ow))
    elif kind == "thumb":
        f = skia.Rect.MakeLTRB(-r * 0.24, -r * 1.6, r * 0.24, -r * 0.2)
        cv.drawCircle(0, 0, r, fill(skin))
        cv.drawCircle(0, 0, r, stroke(outline, ow))
        cv.drawRoundRect(f, r * 0.24, r * 0.24, fill(skin))
        cv.drawRoundRect(f, r * 0.24, r * 0.24, stroke(outline, ow))
    else:  # open mitten
        m = ellipse(0, r * 0.25, r * 0.9, r * 1.2)
        cv.drawPath(m, fill(skin))
        cv.drawPath(m, stroke(outline, ow))
        th = ellipse(-r * 0.8, -r * 0.1, r * 0.32, r * 0.55)
        cv.drawPath(th, fill(skin))
        cv.drawPath(th, stroke(outline, ow))
        cv.drawPath(ellipse(-r * 0.62, 0.0, r * 0.25, r * 0.42), fill(skin))
    cv.restore()


# ======================================================================= PROPS
def draw_prop(cv, kind, x, y, ang, s, t=0.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang))
    cv.scale(s, s)
    ol = "#3a2a2a"
    if kind == "cup":
        p = path_poly([(-22, -38), (22, -38), (17, 30), (-17, 30)])
        cv.drawPath(p, fill("#e8473d"))
        cv.drawPath(p, stroke(ol, 3.5))
        cv.drawRect(skia.Rect.MakeLTRB(-21, -30, 21, -22), fill("#f5f0e8"))
    elif kind == "spatula":
        cv.drawRect(skia.Rect.MakeLTRB(-5, -10, 5, 60), fill("#5a3b2a"))
        cv.drawRect(skia.Rect.MakeLTRB(-5, -10, 5, 60), stroke(ol, 3))
        b = path_poly([(-24, -70), (24, -70), (20, -12), (-20, -12)])
        cv.drawPath(b, fill("#b9c2c9"))
        cv.drawPath(b, stroke(ol, 3))
        for k in (-8, 0, 8):
            cv.drawLine(k, -62, k, -22, stroke("#8a949c", 2.5))
    elif kind == "corn":
        e = ellipse(0, -10, 16, 44)
        cv.drawPath(e, fill("#f2c94c"))
        cv.drawPath(e, stroke(ol, 3))
        for k in range(-3, 4):
            cv.drawLine(-12, -10 + k * 11, 12, -10 + k * 11, stroke("#d9a92c", 2))
    elif kind == "can":
        r = skia.Rect.MakeLTRB(-16, -30, 16, 30)
        cv.drawRoundRect(r, 6, 6, fill("#3fa7d6"))
        cv.drawRoundRect(r, 6, 6, stroke(ol, 3))
        cv.drawRect(skia.Rect.MakeLTRB(-16, -8, 16, 4), fill("#f5f0e8"))
    elif kind == "pencil":
        cv.drawRect(skia.Rect.MakeLTRB(-5, -45, 5, 35), fill("#f4b63f"))
        cv.drawPath(path_poly([(-5, 35), (5, 35), (0, 50)]), fill("#f3d6b0"))
        cv.drawRect(skia.Rect.MakeLTRB(-5, -52, 5, -45), fill("#e88a9a"))
    cv.restore()


# ======================================================================= HAIR
def hair_back(cv, style, R, P, col):
    yaw = yaw_of(P)
    hx = R * 0.18 * math.sin(yaw)
    p = None
    if style in ("bob", "kidbob"):
        L = 1.0 if style == "bob" else 0.8
        p = smooth_closed([(-1.14 * R + hx, 0.0), (-1.12 * R + hx * 0.5, 0.55 * R * L), (-1.0 * R, 0.98 * R * L),
                           (-0.55 * R, 1.08 * R * L), (0.55 * R, 1.08 * R * L), (1.0 * R, 0.98 * R * L),
                           (1.12 * R + hx * 0.5, 0.55 * R * L), (1.14 * R + hx, 0.0), (0.9 * R, -0.95 * R),
                           (0, -1.2 * R), (-0.9 * R, -0.95 * R)], 0.6)
    elif style == "curly":
        pts = []
        for k in range(22):
            a = k / 22 * 2 * math.pi
            rr = R * (1.38 + 0.07 * math.sin(a * 7))
            pts.append((rr * math.cos(a) + hx * 0.5, rr * math.sin(a) * 0.95 - 0.25 * R))
        p = smooth_closed(pts, 0.7)
    if p is not None:
        cv.drawPath(p, fill(col))
        cv.drawPath(p, stroke(shade(col, 0.6), 0.035 * R))


def hair_front(cv, style, R, P, col, t=0.0):
    yaw = yaw_of(P)
    hx = R * 0.22 * math.sin(yaw)
    nd = P["nod"] * 0.06 * R
    ol = shade(col, 0.6)
    ow = 0.035 * R
    if style in ("bob", "kidbob"):
        p = skia.Path()
        p.moveTo(-1.08 * R, 0.1 * R)
        p.cubicTo(-1.16 * R, -1.42 * R, 1.16 * R, -1.42 * R, 1.08 * R, 0.1 * R)
        # fringe right->left (side swept)
        p.cubicTo(0.98 * R, -0.35 * R + nd, 0.75 * R + hx, -0.5 * R + nd, 0.45 * R + hx, -0.46 * R + nd)
        p.cubicTo(0.2 * R + hx, -0.42 * R + nd, 0.05 * R + hx, -0.6 * R + nd, -0.2 * R + hx, -0.56 * R + nd)
        p.cubicTo(-0.55 * R + hx, -0.5 * R + nd, -0.85 * R + hx * 0.5, -0.3 * R + nd, -0.95 * R, 0.25 * R)
        p.close()
        cv.drawPath(p, fill(col))
        fr = skia.Path()
        fr.moveTo(1.08 * R, 0.1 * R)
        fr.cubicTo(0.98 * R, -0.35 * R + nd, 0.75 * R + hx, -0.5 * R + nd, 0.45 * R + hx, -0.46 * R + nd)
        fr.cubicTo(0.2 * R + hx, -0.42 * R + nd, 0.05 * R + hx, -0.6 * R + nd, -0.2 * R + hx, -0.56 * R + nd)
        fr.cubicTo(-0.55 * R + hx, -0.5 * R + nd, -0.85 * R + hx * 0.5, -0.3 * R + nd, -0.95 * R, 0.25 * R)
        cv.drawPath(fr, stroke(ol, ow))
        for k in range(3):
            st = skia.Path()
            bx = (-0.5 + 0.4 * k) * R + hx
            st.moveTo(bx, -1.0 * R + 0.05 * R * k)
            st.quadTo(bx + 0.15 * R, -0.75 * R, bx + 0.1 * R, -0.5 * R + nd)
            cv.drawPath(st, stroke(alpha(ol, 0.35), ow * 0.8))
        # shine
        sh = skia.Path()
        sh.moveTo(-0.55 * R + hx * 0.6, -0.88 * R)
        sh.quadTo(-0.1 * R + hx * 0.6, -1.06 * R, 0.35 * R + hx * 0.6, -0.92 * R)
        cv.drawPath(sh, stroke(alpha(shade(col, 1.35), 0.7), 0.07 * R))
        # clip
        cx, cy = 0.72 * R + hx * 0.6, -0.55 * R + nd
        r = skia.Rect.MakeLTRB(cx - 0.17 * R, cy - 0.07 * R, cx + 0.17 * R, cy + 0.07 * R)
        cv.save()
        cv.rotate(-25, cx, cy) if False else None
        cv.drawRoundRect(r, 0.06 * R, 0.06 * R, fill("#ffcf3f"))
        cv.drawRoundRect(r, 0.06 * R, 0.06 * R, stroke("#b8860b", 0.025 * R))
        cv.restore()
    elif style in ("crew", "kidspiky"):
        p = skia.Path()
        hl = -0.58 * R + nd
        p.moveTo(-1.02 * R, 0.0)
        if style == "crew":
            p.cubicTo(-1.08 * R, -1.38 * R, 1.08 * R, -1.38 * R, 1.02 * R, 0.0)
            p.lineTo(0.92 * R, -0.25 * R)
            p.cubicTo(0.8 * R + hx, hl - 0.05 * R, 0.4 * R + hx, hl, 0.0 + hx, hl + 0.02 * R)
            p.cubicTo(-0.4 * R + hx, hl, -0.8 * R + hx, hl - 0.05 * R, -0.92 * R, -0.25 * R)
            p.close()
        else:
            # spiky top (soft tufts)
            pts = [(-1.02 * R, 0.0), (-1.06 * R, -0.62 * R)]
            spikes = [(-0.86, -1.12), (-0.66, -1.06), (-0.5, -1.32), (-0.26, -1.12), (-0.04, -1.38), (0.2, -1.13),
                      (0.42, -1.33), (0.64, -1.06), (0.84, -1.14), (1.06, -0.62)]
            for sx, sy in spikes:
                pts.append((sx * R + hx * 0.4, sy * R))
            pts += [(1.02 * R, 0.0), (0.9 * R, -0.3 * R), (0.5 * R + hx, hl - 0.06 * R), (0.1 * R + hx, hl + 0.06 * R),
                    (-0.3 * R + hx, hl - 0.04 * R), (-0.7 * R + hx, hl + 0.02 * R), (-0.92 * R, -0.3 * R)]
            p = smooth_closed(pts, 0.25)
        cv.drawPath(p, fill(col))
        cv.drawPath(p, stroke(ol, ow))
    elif style == "teacher":
        for s in (-1, 1):
            q = smooth_closed([(s * 1.02 * R, -0.45 * R), (s * 1.12 * R, -0.2 * R), (s * 1.08 * R, 0.12 * R),
                               (s * 0.94 * R, 0.1 * R), (s * 0.92 * R, -0.3 * R)], 0.6)
            cv.drawPath(q, fill(col))
            cv.drawPath(q, stroke(ol, ow))
        sh = skia.Path()
        sh.moveTo(-0.45 * R + hx, -0.9 * R)
        sh.quadTo(hx, -1.05 * R, 0.4 * R + hx, -0.92 * R)
        cv.drawPath(sh, stroke((1, 1, 1, 0.35), 0.06 * R))
    elif style == "curly":
        p = skia.Path()
        hl = -0.55 * R + nd
        p.moveTo(-1.05 * R, 0.0)
        p.cubicTo(-1.1 * R, -1.4 * R, 1.1 * R, -1.4 * R, 1.05 * R, 0.0)
        p.cubicTo(0.9 * R, hl, 0.3 * R + hx, hl - 0.1 * R, 0.0 + hx, hl)
        p.cubicTo(-0.3 * R + hx, hl - 0.1 * R, -0.9 * R, hl, -1.05 * R, 0.0)
        p.close()
        cv.drawPath(p, fill(col))
        for k in range(9):
            a = math.pi + k / 8 * math.pi
            cv.drawCircle(0.95 * R * math.cos(a) + hx * 0.4, -0.25 * R + 0.95 * R * math.sin(a), 0.16 * R, fill(col))
    elif style == "swoop":
        p = skia.Path()
        p.moveTo(-1.03 * R, 0.0)
        p.cubicTo(-1.1 * R, -1.45 * R, 1.1 * R, -1.45 * R, 1.03 * R, 0.0)
        p.cubicTo(0.95 * R, -0.4 * R, 0.6 * R + hx, -0.75 * R + nd, 0.1 * R + hx, -0.62 * R + nd)
        p.cubicTo(-0.35 * R + hx, -0.5 * R + nd, -0.8 * R, -0.55 * R, -0.95 * R, -0.25 * R)
        p.close()
        cv.drawPath(p, fill(col))
        cv.drawPath(p, stroke(ol, ow))


# ======================================================================= HUMAN
class Human:
    def __init__(self, name, R, look, hair_style, hair_col, shirt, pants="#3b4a6b", sw=0.95, ww=0.82,
                 torso=2.0, jaw=0.55, arm_w=0.34, sleeve="long", collar="crew", dogtags=False, vest=None,
                 hood=False, cheek_w=1.0):
        self.name = name
        self.R = R
        self.L = look
        self.hair_style = hair_style
        self.hair_col = hair_col
        self.shirt = shirt
        self.pants = pants
        self.sw, self.ww, self.torso = sw, ww, torso
        self.jaw = jaw
        self.arm_w = arm_w
        self.sleeve = sleeve
        self.collar = collar
        self.dogtags = dogtags
        self.vest = vest
        self.cheek_w = cheek_w

    # local geometry (hip at 0,0)
    def shoulder_y(self):
        return -self.torso * self.R

    def neck_top(self):
        return -(self.torso + 0.28) * self.R

    def head_center(self):
        return -(self.torso + 0.28 + 0.92) * self.R

    def draw(self, cv, P, t=0.0):
        R = self.R
        L = self.L
        ol = L.outline
        ow = 0.035 * R
        cv.save()
        cv.translate(P.get("x", 0), P.get("y", 0))
        s = P.get("scale", 1.0)
        cv.scale(s * P.get("flip", 1), s)
        # body lean / shake
        shake = P.get("shake", 0.0)
        bob = P.get("bob", 0.0) * R
        cv.translate(0, bob)
        cv.rotate(P.get("lean", 0.0))
        breath = P.get("breath", 0.0)
        sh_y = self.shoulder_y() - breath * 0.03 * R + shake * 0.06 * R
        hc_y = self.head_center() - breath * 0.025 * R + shake * 0.07 * R
        nt_y = self.neck_top() - breath * 0.025 * R + shake * 0.06 * R
        sw = self.sw * R * (1 + P.get("shrug", 0) * 0.04)
        sh_y -= P.get("shrug", 0) * 0.18 * R
        ww = self.ww * R
        # ---- head transform helper
        def head_xform():
            cv.translate(0, nt_y)
            cv.rotate(P["tilt"])
            cv.translate(P.get("head_dx", 0) * R, hc_y - nt_y)

        part = P.get("part", "all")
        if part != "arms":
            # ---- back hair
            cv.save()
            head_xform()
            hair_back(cv, self.hair_style, R, P, self.hair_col)
            cv.restore()
            # ---- seated legs (porch steps)
            if P.get("legs") == "steps":
                pc = self.pants
                for side in (-1, 1):
                    kx = side * (0.46 + P.get("knee_dx", 0.0)) * R
                    ky = 0.42 * R
                    fx = side * (0.5 + P.get("knee_dx", 0.0) * 0.6) * R
                    fy = 1.62 * R
                    draw_limb(cv, [(kx, ky), (fx, fy)], 0.4 * R, shade(pc, 0.85), shade(pc, 0.55), ow)
                    sh = ellipse(fx + side * 0.04 * R, fy + 0.12 * R, 0.3 * R, 0.15 * R)
                    cv.drawPath(sh, fill("#2c2a33"))
                    cv.drawPath(sh, stroke("#141318", ow))
                for side in (-1, 1):
                    hx0 = side * 0.34 * R
                    kx = side * (0.46 + P.get("knee_dx", 0.0)) * R
                    ky = 0.42 * R
                    draw_limb(cv, [(hx0, -0.05 * R), (kx, ky)], 0.52 * R, pc, shade(pc, 0.6), ow)
                    cv.drawCircle(kx, ky, 0.27 * R, fill(pc))
                    cv.drawCircle(kx - side * 0.05 * R, ky - 0.06 * R, 0.12 * R, fill(alpha(shade(pc, 1.25), 0.6)))
            # ---- arms behind (if requested)
            if P.get("arms_behind", False):
                self.draw_arms(cv, P, sh_y, sw, t)
            # ---- torso
            tp = skia.Path()
            nw = 0.3 * R
            tp.moveTo(-nw, nt_y + 0.12 * R)
            tp.cubicTo(-nw - 0.1 * R, sh_y - 0.05 * R, -sw + 0.15 * R, sh_y - 0.08 * R, -sw, sh_y + 0.22 * R)
            tp.cubicTo(-sw - 0.05 * R, sh_y + 0.9 * R, -ww - 0.04 * R, -0.6 * R, -ww, 0.15 * R)
            tp.lineTo(ww, 0.15 * R)
            tp.cubicTo(ww + 0.04 * R, -0.6 * R, sw + 0.05 * R, sh_y + 0.9 * R, sw, sh_y + 0.22 * R)
            tp.cubicTo(sw - 0.15 * R, sh_y - 0.08 * R, nw + 0.1 * R, sh_y - 0.05 * R, nw, nt_y + 0.12 * R)
            tp.close()
            # neck
            neck = skia.Rect.MakeLTRB(-0.24 * R, nt_y - 0.3 * R, 0.24 * R, sh_y + 0.1 * R)
            cv.drawRect(neck, fill(L.skin))
            cv.drawRect(skia.Rect.MakeLTRB(-0.24 * R, nt_y - 0.05 * R, 0.24 * R, sh_y + 0.1 * R), fill(shade(L.skin, 0.85)))
            cv.drawPath(tp, fill(self.shirt))
            # soft side shading
            cv.save()
            cv.clipPath(tp, doAntiAlias=True)
            cv.drawPath(tp, lin_grad((-sw, 0), (sw, 0), [alpha("#000000", 0.0), alpha("#000000", 0.12)], [0.55, 1.0]))
            if self.vest:
                vp = skia.Path()
                vp.moveTo(-sw * 0.62, sh_y + 0.05 * R)
                vp.lineTo(0, sh_y + 0.85 * R)
                vp.lineTo(sw * 0.62, sh_y + 0.05 * R)
                vp.lineTo(sw * 1.2, 0.3 * R)
                vp.lineTo(-sw * 1.2, 0.3 * R)
                vp.close()
                cv.drawPath(vp, fill(self.vest))
                for k in range(5):
                    yk = sh_y + (0.6 + 0.35 * k) * R
                    cv.drawLine(-sw, yk, sw, yk, stroke(alpha(shade(self.vest, 0.8), 0.5), 0.05 * R))
            cv.restore()
            cv.drawPath(tp, stroke(shade(self.shirt, 0.6), ow))
            # collar
            cl = skia.Path()
            if self.collar == "v":
                cl.moveTo(-nw - 0.02 * R, nt_y + 0.2 * R)
                cl.lineTo(0, sh_y + 0.45 * R)
                cl.lineTo(nw + 0.02 * R, nt_y + 0.2 * R)
                cv.drawPath(cl, fill(L.skin))
                cv.drawPath(cl, stroke(shade(self.shirt, 0.6), ow))
            else:
                cl.moveTo(-nw - 0.03 * R, sh_y + 0.0 * R)
                cl.quadTo(0, sh_y + 0.32 * R, nw + 0.03 * R, sh_y + 0.0 * R)
                cv.drawPath(cl, stroke(shade(self.shirt, 0.7), 0.07 * R))
            if self.dogtags:
                ch = skia.Path()
                ch.moveTo(-nw * 0.9, sh_y - 0.02 * R)
                ch.quadTo(0, sh_y + 0.75 * R, nw * 0.9, sh_y - 0.02 * R)
                cv.drawPath(ch, stroke("#9aa3ab", 0.02 * R))
                tg = skia.Rect.MakeLTRB(-0.07 * R, sh_y + 0.34 * R, 0.07 * R, sh_y + 0.55 * R)
                cv.drawRoundRect(tg, 0.03 * R, 0.03 * R, fill("#c3cbd2"))
                cv.drawRoundRect(tg, 0.03 * R, 0.03 * R, stroke("#6d757c", 0.018 * R))
            # ---- head
            cv.save()
            head_xform()
            yaw = yaw_of(P)
            for side in (-1, 1):
                ex = side * 0.97 * R + R * 0.14 * math.sin(yaw)
                e = ellipse(ex, 0.12 * R + P["nod"] * 0.08 * R, 0.17 * R, 0.24 * R)
                cv.drawPath(e, fill(L.skin))
                cv.drawPath(e, stroke(ol, ow))
                cv.drawPath(ellipse(ex - side * 0.02 * R, 0.13 * R, 0.07 * R, 0.13 * R), fill(shade(L.skin, 0.85)))
            hp = head_path(R, self.jaw, 1.02, P["puff"], cheek=self.cheek_w, yaw=yaw_of(P))
            cv.drawPath(hp, fill(L.skin))
            cv.save()
            cv.clipPath(hp, doAntiAlias=True)
            # soft jaw shading + stubble
            cv.drawPath(hp, rad_grad((R * 0.3 * math.sin(yaw), -0.2 * R), 1.35 * R, [alpha("#ffffff", 0.0), alpha("#7a3b20", 0.13)], [0.6, 1.0]))
            if L.stubble:
                sp = skia.Path()
                mxx = R * 0.8 * math.sin(yaw)
                sp.addOval(skia.Rect.MakeLTRB(mxx - 0.95 * R, 0.36 * R + P["nod"] * 0.1 * R, mxx + 0.95 * R, 1.55 * R))
                cv.drawPath(sp, rad_grad((mxx, 1.05 * R), 0.95 * R, [alpha(L.stubble, 0.2), alpha(L.stubble, 0.16), alpha(L.stubble, 0.0)], [0.0, 0.7, 1.0]))
            cv.restore()
            cv.drawPath(hp, stroke(ol, ow))
            draw_face(cv, L, R, P, t)
            hair_front(cv, self.hair_style, R, P, self.hair_col, t)
            cv.restore()
        # ---- arms
        if not P.get("arms_behind", False) and part != "body":
            self.draw_arms(cv, P, sh_y, sw, t)
        cv.restore()

    def draw_arms(self, cv, P, sh_y, sw, t):
        R = self.R
        L = self.L
        ow = 0.035 * R
        for side, key in ((-1, "armL"), (1, "armR")):
            arm = P.get(key)
            if arm is None:
                continue
            hx, hy = arm[0] * R, arm[1] * R
            bend = arm[2] if len(arm) > 2 else 1.0
            hand = arm[3] if len(arm) > 3 else "mitt"
            prop = arm[4] if len(arm) > 4 else None
            sx, sy = side * (sw - 0.12 * R), sh_y + 0.28 * R
            L1, L2 = 0.53 * self.torso * R, 0.51 * self.torso * R
            (ex, ey), (hx2, hy2) = ik2(sx, sy, hx, hy, L1, L2, bend * -side)
            col = self.shirt
            aw = self.arm_w * R
            if self.sleeve == "short":
                mx_, my_ = sx + (ex - sx) * 0.55, sy + (ey - sy) * 0.55
                draw_limb(cv, [(mx_, my_), (ex, ey), (hx2, hy2)], aw * 0.82, L.skin, L.outline, ow)
                draw_limb(cv, [(sx, sy), (mx_, my_)], aw * 1.05, col, shade(col, 0.6), ow)
            else:
                draw_limb(cv, [(sx, sy), (ex, ey), (hx2, hy2)], aw, col, shade(col, 0.6), ow)
            ang = math.atan2(hy2 - ey, hx2 - ex)
            if prop:
                pk, ps, pa = prop
                draw_prop(cv, pk, hx2, hy2, pa, ps * R / 100, t)
            draw_hand(cv, hx2, hy2, 0.19 * R, ang, L.skin, L.outline, ow, hand)


# ======================================================================= EMOTION CREATURES
class Emo:
    def __init__(self, name, R, look, body, bw=1.55, bh=2.7, shape="bean", acc=None):
        self.name = name
        self.R = R
        self.L = look
        self.body = body
        self.bw, self.bh = bw, bh
        self.shape = shape
        self.acc = acc or []

    def body_path(self, P):
        R = self.R
        w = self.bw * R * (1 + P.get("squash", 0) * 0.15)
        h = self.bh * R * (1 - P.get("squash", 0) * 0.12)
        if self.shape == "box":
            p = skia.Path()
            p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -h, w / 2, 0), w * 0.28, w * 0.28))
            return p, w, h
        p = skia.Path()
        p.moveTo(0, -h)
        p.cubicTo(w * 0.62, -h, w * 0.55, -h * 0.35, w * 0.5, -h * 0.12)
        p.cubicTo(w * 0.47, 0.02 * R, -w * 0.47, 0.02 * R, -w * 0.5, -h * 0.12)
        p.cubicTo(-w * 0.55, -h * 0.35, -w * 0.62, -h, 0, -h)
        p.close()
        return p, w, h

    def draw(self, cv, P, t=0.0):
        R = self.R
        L = self.L
        ol = L.outline
        ow = 0.04 * R
        cv.save()
        cv.translate(P.get("x", 0), P.get("y", 0))
        s = P.get("scale", 1.0)
        cv.scale(s * P.get("flip", 1), s)
        cv.translate(0, P.get("bob", 0) * R)
        cv.rotate(P.get("lean", 0.0))
        shake = P.get("shake", 0)
        cv.translate(0, shake * 0.05 * R)
        bp, w, h = self.body_path(P)
        # legs
        pose = P.get("pose", "stand")
        if pose == "stand":
            for side in (-1, 1):
                lx = side * 0.32 * R + P.get("step", 0) * side * 0.1 * R
                lift = max(0, P.get("run", 0) * math.sin(t * 14 + (0 if side < 0 else math.pi))) * 0.25 * R
                draw_limb(cv, [(lx, -0.3 * R), (lx, -0.02 * R - lift)], 0.3 * R, shade(self.body, 0.85), ol, ow)
                cv.drawPath(ellipse(lx + side * 0.08 * R, 0.0 - lift, 0.24 * R, 0.13 * R), fill(shade(self.body, 0.6)))
        for a in self.acc:
            if a[0] == "hood_back":
                cv.drawPath(ellipse(0, -h + 1.05 * R + 0.0, w * 0.52, w * 0.52 * 0.92), fill(a[1]))
        # body
        cv.drawPath(bp, fill(self.body))
        cv.save()
        cv.clipPath(bp, doAntiAlias=True)
        cv.drawPath(bp, rad_grad((-w * 0.2, -h * 0.75), h * 1.0, [alpha("#ffffff", 0.18), alpha("#ffffff", 0.0), alpha("#000000", 0.14)], [0.0, 0.5, 1.0]))
        for a in self.acc:
            if a[0] == "hoodie":
                hp = skia.Path()
                hp.addRect(skia.Rect.MakeLTRB(-w, -h * 0.4, w, 1))
                cv.drawPath(hp, fill(a[1]))
                pk = skia.Rect.MakeLTRB(-w * 0.28, -h * 0.22, w * 0.28, -h * 0.07)
                cv.drawRoundRect(pk, 0.1 * R, 0.1 * R, stroke(shade(a[1], 0.7), ow))
            if a[0] == "uniform":
                cv.drawRect(skia.Rect.MakeLTRB(-w, -h * 0.5, w, 1), fill(a[1]))
                cv.drawRect(skia.Rect.MakeLTRB(-w, -h * 0.5, w, -h * 0.47), fill(a[2]))
            if a[0] == "cardigan":
                cp = skia.Path()
                cp.moveTo(-w, -h * 0.55)
                cp.lineTo(-w * 0.1, -h * 0.55)
                cp.lineTo(-w * 0.05, 1)
                cp.lineTo(-w, 1)
                cp.close()
                cv.drawPath(cp, fill(a[1]))
                cp2 = skia.Path()
                cp2.moveTo(w, -h * 0.55)
                cp2.lineTo(w * 0.1, -h * 0.55)
                cp2.lineTo(w * 0.05, 1)
                cp2.lineTo(w, 1)
                cp2.close()
                cv.drawPath(cp2, fill(a[1]))
        cv.restore()
        cv.drawPath(bp, stroke(ol, ow))
        for a in self.acc:
            if a[0] == "hood_rim":
                rim = ellipse(0, -h + 1.05 * R, w * 0.46, w * 0.46 * 0.95)
                cv.drawPath(rim, stroke(a[1], 0.12 * R))
            if a[0] == "strings":
                for side in (-1, 1):
                    sx = side * 0.22 * R
                    sy = -h * 0.4
                    swing = math.sin(t * 9 + side) * P.get("run", 0) * 0.15 * R
                    sp = skia.Path()
                    sp.moveTo(sx, sy)
                    sp.quadTo(sx + swing, sy + 0.2 * R, sx + swing * 1.5, sy + 0.38 * R)
                    cv.drawPath(sp, stroke("#ffffff", 0.05 * R))
                    cv.drawCircle(sx + swing * 1.5, sy + 0.4 * R, 0.05 * R, fill("#ffffff"))
        # face
        cv.save()
        fcx, fcy = 0, -h + 1.05 * R
        cv.translate(fcx, fcy)
        cv.rotate(P["tilt"])
        draw_face(cv, L, R, P, t)
        for a in self.acc:
            if a[0] == "beanie":
                bn = skia.Path()
                bn.moveTo(-0.85 * R, -0.62 * R)
                bn.cubicTo(-0.9 * R, -1.65 * R, 0.9 * R, -1.65 * R, 0.85 * R, -0.62 * R)
                bn.close()
                cv.drawPath(bn, fill(a[1]))
                cv.drawPath(bn, stroke(shade(a[1], 0.6), ow))
                band = skia.Rect.MakeLTRB(-0.92 * R, -0.78 * R, 0.92 * R, -0.52 * R)
                cv.drawRoundRect(band, 0.1 * R, 0.1 * R, fill(shade(a[1], 0.85)))
                cv.drawRoundRect(band, 0.1 * R, 0.1 * R, stroke(shade(a[1], 0.6), ow))
                cv.drawCircle(0, -1.42 * R, 0.16 * R, fill(shade(a[1], 1.15)))
            if a[0] == "bun":
                cv.drawCircle(0.1 * R, -1.25 * R, 0.32 * R, fill(a[1]))
                cv.drawCircle(0.1 * R, -1.25 * R, 0.32 * R, stroke(shade(a[1], 0.6), ow))
            if a[0] == "flame":
                fp = skia.Path()
                fp.moveTo(-0.35 * R, -0.85 * R)
                fl = math.sin(t * 9) * 0.06 * R
                fp.quadTo(-0.4 * R, -1.25 * R, -0.12 * R + fl, -1.5 * R)
                fp.quadTo(-0.08 * R, -1.2 * R, 0.08 * R, -1.3 * R)
                fp.quadTo(0.12 * R, -1.55 * R + fl, 0.32 * R, -1.62 * R)
                fp.quadTo(0.45 * R, -1.1 * R, 0.35 * R, -0.85 * R)
                fp.close()
                cv.drawPath(fp, fill("#ffb23e"))
                cv.drawPath(fp, stroke("#c4561c", ow))
            if a[0] == "helmet":
                hm = skia.Path()
                hm.moveTo(-1.05 * R, -0.72 * R)
                hm.cubicTo(-1.15 * R, -1.95 * R, 1.15 * R, -1.95 * R, 1.05 * R, -0.72 * R)
                hm.lineTo(1.18 * R, -0.63 * R)
                hm.lineTo(-1.18 * R, -0.63 * R)
                hm.close()
                cv.drawPath(hm, fill(a[1]))
                cv.drawPath(hm, stroke(shade(a[1], 0.55), ow))
                cv.drawLine(-1.1 * R, -0.69 * R, 1.1 * R, -0.69 * R, stroke(shade(a[1], 0.7), 0.08 * R))
                for k in range(6):
                    cv.drawCircle(-0.5 * R + k * 0.2 * R, -1.25 * R + (k % 2) * 0.15 * R, 0.035 * R, fill(shade(a[1], 0.75)))
        cv.restore()
        # arms
        cross = P.get("cross", 0.0)
        if cross > 0.5:
            for side in (-1, 1):
                sx, sy = side * w * 0.44, -h * 0.55
                ex, ey = side * w * 0.47, -h * 0.33
                hx2, hy2 = -side * w * 0.22, -h * 0.4 + side * 0.04 * R
                draw_limb(cv, [(sx, sy), (ex, ey)], 0.26 * R, self.body, ol, ow)
            for side in (1, -1):
                ex, ey = side * w * 0.47, -h * 0.33
                hx2, hy2 = -side * w * 0.24, -h * 0.4 + side * 0.05 * R
                draw_limb(cv, [(ex, ey), (hx2, hy2)], 0.26 * R, self.body, ol, ow)
                cv.drawCircle(hx2, hy2, 0.15 * R, fill(self.body))
                cv.drawCircle(hx2, hy2, 0.15 * R, stroke(ol, ow))
        for side, key in ((-1, "armL"), (1, "armR")):
            arm = P.get(key)
            if arm is None or cross > 0.5:
                continue
            hx, hy = arm[0] * R, arm[1] * R - h
            bend = arm[2] if len(arm) > 2 else 1.0
            hand = arm[3] if len(arm) > 3 else "fist"
            sx, sy = side * w * 0.42, -h * 0.5
            (ex, ey), (hx2, hy2) = ik2(sx, sy, hx, hy, 0.62 * R, 0.6 * R, bend * -side)
            draw_limb(cv, [(sx, sy), (ex, ey), (hx2, hy2)], 0.24 * R, self.body, ol, ow)
            ang = math.atan2(hy2 - ey, hx2 - ex)
            draw_hand(cv, hx2, hy2, 0.15 * R, ang, self.body, ol, ow, hand)
        if pose == "hug_knees":
            # knees in front + arms wrapped
            for side in (-1, 1):
                kp = ellipse(side * 0.3 * R, -0.28 * R, 0.32 * R, 0.34 * R)
                cv.drawPath(kp, fill(shade(self.body, 0.92)))
                cv.drawPath(kp, stroke(ol, ow))
            ap = skia.Path()
            ap.moveTo(-w * 0.45, -h * 0.4)
            ap.quadTo(-0.25 * R, -0.12 * R, 0.0, -0.3 * R)
            ap.quadTo(0.25 * R, -0.12 * R, w * 0.45, -h * 0.4)
            cv.drawPath(ap, stroke(ol, 0.24 * R + ow * 2))
            cv.drawPath(ap, stroke(self.body, 0.24 * R))
        cv.restore()


# ======================================================================= CAST
def make_cast():
    cast = {}
    cast["kidme"] = Human("kidme", 118, Look("#f6cfae", iris="#5a3a24", brow="#5e3420", eye_rx=0.22, eye_ry=0.27, eye_y=0.1,
                                             mouth_y=0.6, nose=0.8, lash=True, mouth_w=0.36),
                          "kidbob", "#7a3f26", "#f0b030", torso=1.45, sw=0.78, ww=0.7, jaw=0.6, arm_w=0.3)
    cast["kiddanny"] = Human("kiddanny", 118, Look("#d49a6f", iris="#3b2618", brow="#2f2219", eye_rx=0.22, eye_ry=0.27, eye_y=0.1,
                                                   mouth_y=0.6, nose=0.85, freckles=True, mouth_w=0.38),
                             "kidspiky", "#33241b", "#6f8a3e", torso=1.45, sw=0.8, ww=0.72, jaw=0.62, arm_w=0.3)
    cast["teacher"] = Human("teacher", 100, Look("#f0c6a6", iris="#3e5566", brow="#8c8c8c", glasses="#3a3a44", mustache="#6e6e6e",
                                                 eye_rx=0.17, eye_ry=0.2, nose=1.3, mouth_y=0.62),
                            "teacher", "#a7a7a7", "#e8e0d0", vest="#7a4b5c", torso=2.3, sw=1.05, ww=0.95, jaw=0.62, collar="v")
    cast["me"] = Human("me", 100, Look("#f3c9a8", iris="#5a3a24", brow="#5a311d", lash=True, eye_y=0.06),
                       "bob", "#7a3f26", "#e9a82c", torso=2.05, sw=0.9, ww=0.8, jaw=0.52, collar="v")
    cast["danny"] = Human("danny", 104, Look("#c98d64", iris="#33221a", brow="#2a1e17", stubble="#3a2a20", nose=1.15, brow_th=1.25,
                                             eye_rx=0.185, eye_ry=0.215),
                          "crew", "#2e221a", "#6b7a3a", torso=2.25, sw=1.15, ww=0.95, jaw=0.72, sleeve="short", dogtags=True, cheek_w=1.03)
    cast["f1"] = Human("f1", 96, Look("#8d5a3b", iris="#2b1a10", brow="#1e140e", lash=True, cheek="#c96a5a"),
                       "curly", "#1f1611", "#f2d15c", torso=2.0, sw=0.88, ww=0.8, collar="crew")
    cast["f2"] = Human("f2", 98, Look("#f6d3b9", iris="#3c6e8f", brow="#c9953f"),
                       "swoop", "#d9a441", "#4f7fc4", torso=2.1, sw=0.98, ww=0.85, collar="crew")
    # emotions
    cast["emb"] = Emo("emb", 70, Look("#f497b6", iris="#6b2340", brow="#b04a72", eye_rx=0.21, eye_ry=0.25, mouth_y=0.55,
                                      nose=0.0, outline="#a9476d", cheek="#ff5f8a", lash=True), "#f497b6", bw=2.0, bh=3.0,
                      acc=[("hood_back", "#e0679a"), ("hoodie", "#e0679a"), ("hood_rim", "#e0679a"), ("strings",)])
    cast["doubt"] = Emo("doubt", 66, Look("#a99ae0", iris="#3a2a6e", brow="#5b4a9a", eye_rx=0.19, eye_ry=0.23, nose=0.0,
                                         outline="#6a5aa8", glasses="#2e2550", lash=True), "#a99ae0", bw=1.75, bh=3.3,
                        acc=[("bun", "#5b4a9a"), ("cardigan", "#e8d7a5")])
    cast["anger"] = Emo("anger", 74, Look("#e85a45", iris="#4a120a", brow="#7a1c10", eye_rx=0.18, eye_ry=0.21, nose=0.0,
                                         outline="#9a2a1a", brow_th=1.5), "#e85a45", bw=2.5, bh=2.7, shape="box",
                        acc=[("uniform", "#b23a2a", "#f2c14e"), ("flame",)])
    cast["bored"] = Emo("bored", 68, Look("#5cc0b5", iris="#174f4a", brow="#2a7a72", eye_rx=0.19, eye_ry=0.23, nose=0.0,
                                         outline="#2f8279"), "#5cc0b5", bw=1.9, bh=2.8,
                        acc=[("beanie", "#e9a82c")])
    cast["anger_d"] = Emo("anger_d", 92, Look("#d9503c", iris="#3c0e08", brow="#6a170d", eye_rx=0.16, eye_ry=0.19, nose=0.0,
                                             outline="#8a2414", brow_th=1.6), "#d9503c", bw=2.6, bh=3.1, shape="box",
                          acc=[("uniform", "#6b7a3a", "#3e4a20"), ("helmet", "#5d6b33")])
    cast["guilt"] = Emo("guilt", 60, Look("#7d8fb3", iris="#25304a", brow="#4a5878", eye_rx=0.2, eye_ry=0.24, nose=0.0,
                                         outline="#4f5f82"), "#7d8fb3", bw=1.8, bh=2.3)
    return cast
