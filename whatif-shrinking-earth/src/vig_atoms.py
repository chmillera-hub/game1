"""Atom vignettes: an atom crushed into neutrons; cute atoms that push back."""
import math

import numpy as np
import skia

import rig
from chalk import (BLUE, COOL, WARM, _capsule, _union, appear, cue, glow_fill, glow_path, label, p_arrow,
                   p_circle, pop, ramp, spotlight_bg)
from gfx import (clamp, ease_back, ease_in, ease_io, ease_out, fill, font, hexc, lerp, mixhex, smooth_path,
                 smoothstep, stroke)

W, H = 1080, 1920
OL = rig.OUTLINE
PROTON = ("#ff8a7a", "#d8433b")
NEUTRON = ("#d7dde6", "#8b95a5")


def _ball(c, x, y, r, cols, alpha=1.0, flash=0.0):
    lt, dk = cols
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x - r * 0.35, y - r * 0.4), r * 1.45,
                                               [hexc(lt, alpha), hexc(dk, alpha)], [0.0, 1.0]))
    c.drawCircle(x, y, r + 3, fill(hexc(OL, alpha)))
    c.drawCircle(x, y, r, p)
    c.drawCircle(x - r * 0.35, y - r * 0.38, r * 0.22, fill(hexc("#ffffff", 0.55 * alpha)))
    if flash > 0.01:
        c.drawCircle(x, y, r * (1.6 + flash), fill(hexc("#fff6d8", 0.55 * flash), blur=r * 0.6))


def _rr(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


# ============================================================================
# vignette_atom: electrons crushed into protons -> neutrons
# ============================================================================

_NUC = [(0, 0, "p"), (54, 2, "n"), (-54, -2, "p"), (27, 47, "n"), (-27, 47, "p"), (27, -47, "p"), (-27, -46, "n"),
        (0, 18, "n")]
_ORB = [(330, 108, -25, 0.42, 0.0), (300, 96, 35, 0.37, 1.7), (350, 88, 95, 0.33, 3.4), (276, 116, -70, 0.47, 5.0)]
_PROTONS = [i for i, (_, _, k) in enumerate(_NUC) if k == "p"]


def scene_atom(c, t, dur, cues, params):
    t_stop = cue(cues, "stop", 1.1)
    t_cr = cue(cues, "crushed", 3.9)
    t_pr = cue(cues, "protons", 4.5)
    t_ne = cue(cues, "neutrons", 6.9)
    spotlight_bg(c, center=(540, 760), inner="#26336a", outer="#070b1a", r=1100)
    cx, cy = 540, 760
    so = lerp(1.0, 0.2, ease_io((t - t_cr) / 1.3)) if t > t_cr else 1.0
    merge = [t_pr + i * 0.42 for i in range(4)]
    # surrounding neutrons packing in at the end
    pack = t - (t_ne + 0.25)
    if pack > 0:
        sp = 60
        for row in range(-12, 13):
            for col in range(-11, 12):
                x = cx + col * sp + (row % 2) * sp / 2
                y = cy + row * sp * 0.866
                d = math.hypot(x - cx, y - cy)
                if d < 96 or d > 600 or y < 150 or y > 1240:
                    continue
                k = clamp((pack - d / 900) / 0.6)
                if k <= 0:
                    continue
                ux, uy = (x - cx) / d, (y - cy) / d
                off = (1 - ease_out(k)) * 380
                _ball(c, x + ux * off, y + uy * off, 27, NEUTRON, min(1.0, k * 2))
    # orbit paths
    for (rx, ry, rot, sp_, ph) in _ORB:
        orb = skia.Path()
        orb.addOval(skia.Rect.MakeLTRB(cx - rx * so, cy - ry * so, cx + rx * so, cy + ry * so))
        m = skia.Matrix()
        m.setRotate(rot, cx, cy)
        orb.transform(m)
        a = 0.55 * (1 - ramp(t, t_pr + 1.4, 0.8))
        if a > 0.01:
            glow_path(c, orb, BLUE, 2.5, a, shadow=False)
    # nucleus (back to front by y)
    conv = {}
    for k, pi in enumerate(_PROTONS):
        conv[pi] = merge[k]
    order = sorted(range(len(_NUC)), key=lambda i: _NUC[i][1])
    for i in order:
        dx, dy, kind = _NUC[i]
        cols = PROTON if kind == "p" else NEUTRON
        fl = 0.0
        if kind == "p" and t > conv[i]:
            cols = NEUTRON
            fl = math.exp(-(t - conv[i]) * 5)
        squeeze = 1 - 0.08 * ramp(t, t_cr, 1.0)
        _ball(c, cx + dx * squeeze, cy + dy * squeeze, 30, cols, 1.0, fl)
    # electrons
    epos = []
    for i, (rx, ry, rot, sp_, ph) in enumerate(_ORB):
        mt = merge[i]
        if t > mt:
            epos.append(None)
            continue
        fall = ease_in(clamp((t - (mt - 0.6)) / 0.6))
        w = sp_ * (1 + 2.5 * (1 - so))
        a = ph + t * w * math.tau
        x0 = math.cos(a) * rx * so
        y0 = math.sin(a) * ry * so
        r_ = math.radians(rot)
        ex = cx + x0 * math.cos(r_) - y0 * math.sin(r_)
        ey = cy + x0 * math.sin(r_) + y0 * math.cos(r_)
        tx, ty = cx + _NUC[_PROTONS[i]][0], cy + _NUC[_PROTONS[i]][1]
        ex, ey = lerp(ex, tx, fall), lerp(ey, ty, fall)
        c.drawCircle(ex, ey, 26, fill(hexc("#6fd6ff", 0.35), blur=12))
        c.drawCircle(ex, ey, 14, fill(hexc(OL)))
        c.drawCircle(ex, ey, 11, fill(hexc("#7fe0ff")))
        c.drawCircle(ex - 3, ey - 4, 3.5, fill(hexc("#ffffff", 0.9)))
        epos.append((ex, ey))
    # neutrino streaks
    for i, mt in enumerate(merge):
        x = t - mt
        if 0 < x < 0.5:
            ang = 0.7 + i * 1.9
            d0, d1 = 60 + x * 1500, 60 + x * 1500 + 140
            a = 1 - x / 0.5
            c.drawLine(cx + math.cos(ang) * d0, cy + math.sin(ang) * d0, cx + math.cos(ang) * d1,
                       cy + math.sin(ang) * d1, stroke(hexc("#e9fbff", 0.8 * a), 4))
    # pressure arrows
    pa = appear(t, t_cr - 0.25, 0.35) * (1 - ramp(t, t_ne - 0.4, 0.5))
    if pa > 0.01:
        d = lerp(560, 360, ease_io((t - t_cr) / 1.3)) if t > t_cr else 560
        d += math.sin(t * 9) * 8
        for k in range(4):
            ang = k * math.pi / 2 + math.pi / 4
            x0, y0 = cx + math.cos(ang) * (d + 150), cy + math.sin(ang) * (d + 150)
            x1, y1 = cx + math.cos(ang) * d, cy + math.sin(ang) * d
            glow_path(c, p_arrow(x0, y0, x1, y1, 38), WARM, 13.0, pa)
        label(c, "SQUEEZE", cx, 205, 52, WARM, pa, "black")
    # labels
    la = appear(t, t_stop - 0.1, 0.35) * (1 - ramp(t, t_cr - 0.2, 0.4))
    if la > 0.01 and epos and epos[0] is not None:
        ex, ey = epos[0]
        c.drawLine(ex, ey - 18, ex + 30, ey - 70, stroke(hexc(COOL, 0.8 * la), 3))
        label(c, "electron", ex + 40, ey - 80, 40, COOL, la, "bold")
        px_, py_ = cx + _NUC[2][0], cy + _NUC[2][1]
        c.drawLine(px_ - 20, py_ + 20, px_ - 120, py_ + 150, stroke(hexc("#ffb3a8", 0.8 * la), 3))
        label(c, "proton", px_ - 150, py_ + 190, 40, "#ffb3a8", la, "bold")
    if t > t_pr:
        a = appear(t, t_pr + 0.2, 0.3) * (1 - ramp(t, t_ne - 0.2, 0.4))
        label(c, "electron + proton → neutron", cx, 1330, 44, "#e9eef6", a, "bold")
    if t > t_ne - 0.1:
        a = appear(t, t_ne - 0.1, 0.35)
        label(c, "neutrons", cx, cy + 6, 44, "#ffffff", a * (1 - ramp(t, t_ne + 1.0, 0.3)), "extrabold")
        label(c, "neutron-star matter", cx, 1345, 54, "#e9eef6", ramp(t, t_ne + 0.8, 0.4), "extrabold")


# ============================================================================
# vignette_atoms: atoms push back
# ============================================================================

def cute_atom(c, x, y, r, t, mood="determined", arms=1.0, squish=0.0, seed=0, look=(0.0, 0.0), cross=0.0,
              alpha=1.0):
    """Round atom character standing on (x, y) = bottom centre."""
    cy_ = y - r * (1 - squish * 0.5)
    sx, sy = 1 + squish * 0.45, 1 - squish * 0.5
    # orbit + electron behind
    orb_rot = math.radians(-25 + seed * 40)
    ang = t * 2.4 + seed * 1.3
    ox, oy = math.cos(ang) * r * 1.45, math.sin(ang) * r * 0.42
    ex = x + ox * math.cos(orb_rot) - oy * math.sin(orb_rot)
    ey = cy_ + ox * math.sin(orb_rot) + oy * math.cos(orb_rot)
    behind = math.sin(ang) < 0
    orb = skia.Path()
    orb.addOval(skia.Rect.MakeLTRB(x - r * 1.45, cy_ - r * 0.42, x + r * 1.45, cy_ + r * 0.42))
    m = skia.Matrix()
    m.setRotate(math.degrees(orb_rot), x, cy_)
    orb.transform(m)
    c.drawPath(orb, stroke(hexc("#7fd3ff", 0.55 * alpha), 3))
    if behind:
        c.drawCircle(ex, ey, r * 0.13, fill(hexc("#9fe6ff", alpha)))
    # arms (behind body when pushing up)
    def arm(side, up):
        sxp = x + side * r * 0.85 * sx
        syp = cy_ + r * 0.1
        if cross > 0.5:
            return
        hx = sxp + side * r * lerp(0.55, 0.25, up)
        hy = syp + lerp(r * 0.55, -r * 1.25, up)
        p = skia.Path()
        p.moveTo(sxp, syp)
        p.quadTo(sxp + side * r * 0.5, lerp(syp + r * 0.3, syp - r * 0.4, up), hx, hy)
        c.drawPath(p, stroke(hexc(OL, alpha), r * 0.24 + 6))
        c.drawPath(p, stroke(hexc("#a9c3ff", alpha), r * 0.24))
        c.drawCircle(hx, hy, r * 0.17 + 3, fill(hexc(OL, alpha)))
        c.drawCircle(hx, hy, r * 0.17, fill(hexc("#d9e6ff", alpha)))
    arm(-1, arms)
    arm(1, arms)
    body = skia.Path()
    body.addOval(skia.Rect.MakeLTRB(x - r * sx, cy_ - r * sy, x + r * sx, cy_ + r * sy))
    c.drawPath(body, fill(hexc("#8fb5ff", 0.3 * alpha), blur=r * 0.3))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x - r * 0.3, cy_ - r * 0.4), r * 1.5,
                                               [hexc("#cfe0ff", alpha), hexc("#7f9ef0", alpha), hexc("#5a73c8", alpha)],
                                               [0.0, 0.6, 1.0]))
    c.drawPath(body, stroke(hexc(OL, alpha), 6))
    c.drawPath(body, p)
    # face
    lx, ly = look
    for s in (-1, 1):
        fx, fy = x + s * r * 0.32 * sx, cy_ - r * 0.12
        if mood == "happy":
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeLTRB(fx - r * 0.13, fy - r * 0.1, fx + r * 0.13, fy + r * 0.12), 200, 140)
            c.drawPath(arc, stroke(hexc(OL, alpha), r * 0.06))
        else:
            c.drawOval(skia.Rect.MakeLTRB(fx - r * 0.14, fy - r * 0.17, fx + r * 0.14, fy + r * 0.17),
                       fill(hexc("#ffffff", alpha)))
            c.drawCircle(fx + lx * r * 0.05, fy + ly * r * 0.06, r * 0.085, fill(hexc(OL, alpha)))
        if mood in ("determined", "grumpy"):
            bi = 0.10 if mood == "determined" else 0.16
            c.drawLine(fx - s * r * 0.18, fy - r * 0.3, fx + s * r * 0.15, fy - r * (0.22 - bi + 0.12) - r * 0.06,
                       stroke(hexc(OL, alpha), r * 0.07))
    mx, my = x, cy_ + r * 0.36
    if mood == "determined":
        mp = skia.Path()
        mp.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(mx - r * 0.24, my - r * 0.08, mx + r * 0.24, my + r * 0.1),
                                          r * 0.06, r * 0.06))
        c.drawPath(mp, fill(hexc("#ffffff", alpha)))
        c.drawPath(mp, stroke(hexc(OL, alpha), r * 0.05))
        c.drawLine(mx, my - r * 0.08, mx, my + r * 0.1, stroke(hexc(OL, alpha), r * 0.03))
    elif mood == "grumpy":
        mp = skia.Path()
        mp.moveTo(mx - r * 0.16, my + r * 0.06)
        mp.quadTo(mx, my - r * 0.06, mx + r * 0.16, my + r * 0.06)
        c.drawPath(mp, stroke(hexc(OL, alpha), r * 0.06))
    else:
        mp = skia.Path()
        mp.moveTo(mx - r * 0.18, my - r * 0.04)
        mp.quadTo(mx, my + r * 0.16, mx + r * 0.18, my - r * 0.04)
        c.drawPath(mp, stroke(hexc(OL, alpha), r * 0.06))
    c.drawCircle(x - r * 0.55 * sx, cy_ + r * 0.18, r * 0.12, fill(hexc("#ff9fb3", 0.45 * alpha), blur=r * 0.05))
    c.drawCircle(x + r * 0.55 * sx, cy_ + r * 0.18, r * 0.12, fill(hexc("#ff9fb3", 0.45 * alpha), blur=r * 0.05))
    if cross > 0.5:
        for s in (-1, 1):
            x0, y0 = x + s * r * 0.85, cy_ + r * 0.25
            x1, y1 = x - s * r * 0.35, cy_ + r * 0.55
            p = skia.Path()
            p.moveTo(x0, y0)
            p.lineTo(x1, y1)
            c.drawPath(p, stroke(hexc(OL, alpha), r * 0.24 + 6))
            c.drawPath(p, stroke(hexc("#a9c3ff", alpha), r * 0.24))
    if not behind:
        c.drawCircle(ex, ey, r * 0.14 + 2, fill(hexc(OL, alpha)))
        c.drawCircle(ex, ey, r * 0.13, fill(hexc("#9fe6ff", alpha)))


def _big_hand(c, x_tip, y_bottom, tremble):
    """Giant flat hand pressing down; fingers point left, wrist up at right."""
    yb = y_bottom + tremble
    parts = []
    for k in range(4):
        y0 = yb - 34 - k * 40
        parts.append(_capsule(x_tip + k * 26, y0, 900, y0, 62))
    palm = skia.Path()
    palm.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(560, yb - 190, 1000, yb), 60, 60))
    parts.append(palm)
    parts.append(_capsule(700, yb - 175, 520, yb - 235, 70))
    parts.append(_capsule(860, yb - 120, 980, yb - 900, 260))
    hand = _union(parts)
    c.drawPath(hand, stroke(hexc(OL), 8))
    c.drawPath(hand, fill(hexc("#d9a57c")))
    c.save()
    c.clipPath(hand, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(0, yb - 40, 1080, yb + 10), fill(hexc("#b07a55", 0.55)))
    for k in range(1, 4):
        y0 = yb - 34 - k * 40 + 20
        c.drawLine(x_tip + k * 26 + 40, y0, 560, y0, stroke(hexc("#9a6a48", 0.6), 4))
    c.restore()
    sl = _capsule(900, yb - 330, 1060, yb - 1100, 300)
    c.drawPath(sl, stroke(hexc(OL), 8))
    c.drawPath(sl, fill(hexc("#7d6bb0")))


def _layer(c, a, fn):
    if a <= 0.01:
        return
    if a >= 0.99:
        fn()
        return
    p = skia.Paint()
    p.setAlphaf(a)
    c.saveLayer(None, p)
    fn()
    c.restore()


def scene_atoms(c, t, dur, cues, params):
    t_res = cue(cues, "resists", 1.1)
    t_el = cue(cues, "electrons", 3.7)
    t_ref = cue(cues, "refuse", 5.0)
    t_gr = cue(cues, "ground", 8.6)
    t_ch = cue(cues, "chair", 12.3)
    spotlight_bg(c, center=(540, 820), inner="#2a3f7a", outer="#0a1230", r=1150)
    b = [0.0, t_el - 0.45, t_gr - 0.75, t_ch - 0.65, dur + 1]
    xf = 0.35

    def wgt(i):
        a = ramp(t, b[i] - xf / 2, xf) if i > 0 else 1.0
        e = 1 - ramp(t, b[i + 1] - xf / 2, xf)
        return a * e

    _layer(c, wgt(0), lambda: _beat_press(c, t, t_res))
    _layer(c, wgt(1), lambda: _beat_seats(c, t, t_el, t_ref))
    _layer(c, wgt(2), lambda: _beat_ground(c, t, t_gr))
    _layer(c, wgt(3), lambda: _beat_chair(c, t, t_ch))


def _beat_press(c, t, t_res):
    floor = 1180
    c.drawRect(skia.Rect.MakeLTRB(0, floor, W, H), fill(hexc("#121d42")))
    c.drawLine(0, floor, W, floor, stroke(hexc("#6f8fd8", 0.6), 4))
    contact = clamp((t - (t_res - 0.5)) / 0.5)
    push = ease_in(contact)
    r = 74
    y_hands = floor - 2 * r - 1.25 * r + 6
    tremble = math.sin(t * 38) * 4 * (1 if t > t_res else 0)
    yb = lerp(-120, y_hands - 6, push)
    sq = 0.10 * (1 if t > t_res else 0) + 0.03 * math.sin(t * 38)
    for i in range(5):
        x = 150 + i * 195
        arms = 1.0
        mood = "determined" if t > t_res - 0.2 else "happy"
        cute_atom(c, x, floor, r, t, mood, arms=arms, squish=max(0.0, sq), seed=i, look=(0.0, -1.0))
    _big_hand(c, 70, yb, tremble)
    if t > t_res + 0.2:
        label(c, "push back!", 540, 1300, 56, WARM, appear(t, t_res + 0.2, 0.3), "extrabold")


def _seat_box(c, x, y, s=210, glow=1.0):
    p = _rr(x - s / 2, y - s / 2, x + s / 2, y + s / 2, 30)
    glow_path(c, p, COOL, 6.0, glow)


def _beat_seats(c, t, t_el, t_ref):
    y = 860
    lx, rx_ = 330, 750
    _seat_box(c, lx, y)
    _seat_box(c, rx_, y)
    # sign
    c.drawLine(540, 560, 540, 700, stroke(hexc("#8a6a4a"), 10))
    sg = _rr(330, 470, 750, 580, 20)
    c.drawPath(sg, stroke(hexc(OL), 6))
    c.drawPath(sg, fill(hexc("#f3e6c8")))
    f = font(44, "extrabold")
    s = "ONE PER SEAT"
    c.drawString(s, 540 - f.measureText(s) / 2, 542, f, fill(hexc("#3a2a20")))
    r = 70
    refuse = t > t_ref
    a_mood = "grumpy" if refuse else "happy"
    cute_atom(c, lx, y + r, r, t, a_mood, arms=0.0, seed=1, look=(1.0, 0.0), cross=1.0 if refuse else 0.0)
    # electron B: comes in, tries the full seat, bounces into the free one
    if t < t_ref:
        k = ease_out(clamp((t - t_el) / (t_ref - t_el)))
        bx = lerp(1250, lx + 120, k)
        by = y + r
        b_mood = "happy"
    else:
        x = t - t_ref
        bx = lerp(lx + 120, rx_, ease_out(clamp(x / 0.8)))
        by = y + r - math.sin(clamp(x / 0.8) * math.pi) * 160
        b_mood = "grumpy" if x > 0.5 else "determined"
    cute_atom(c, bx, by, r, t, b_mood, arms=0.0, seed=4, look=(-1.0, 0.0), cross=1.0 if t > t_ref + 0.6 else 0.0)
    if refuse:
        a = pop(t, t_ref + 0.02, 0.3) * (1 - ramp(t, t_ref + 1.6, 0.4))
        if a > 0:
            label(c, "NOPE!", lx, y - 150, 60, "#ff9a8a", min(1, a), "black")
    label(c, "electrons", 540, 1120, 46, COOL, appear(t, t_el, 0.3), "bold")


def _ground_atoms(c, x0, x1, ytop, rows, r, t, squish_x=None):
    for row in range(rows):
        n = int((x1 - x0) / (2.1 * r))
        for i in range(n):
            x = x0 + r * 1.05 + i * 2.1 * r + (row % 2) * r * 1.05
            if x > x1 - r:
                continue
            yb = ytop + (row + 1) * 2.05 * r
            sq = 0.0
            mood = "happy"
            if squish_x is not None and abs(x - squish_x) < r * 2.2 and row == 0:
                sq, mood = 0.12, "determined"
            cute_atom(c, x, yb, r, t, mood, arms=1.0 if row == 0 else 0.0, squish=sq, seed=i + row * 3,
                      look=(0.0, -1.0))


def _beat_ground(c, t, t_gr):
    gy = 1000
    # cutaway soil
    soil = _rr(60, gy, 1020, 1420, 40)
    c.drawPath(soil, fill(hexc("#3a2a28")))
    c.save()
    c.clipPath(soil, skia.ClipOp.kIntersect, True)
    _ground_atoms(c, 70, 1010, gy - 8, 2, 52, t, squish_x=540)
    c.restore()
    c.drawPath(soil, stroke(hexc(OL), 6))
    c.drawRect(skia.Rect.MakeLTRB(0, gy - 26, W, gy + 6), fill(hexc("#4f9a5e")))
    c.drawLine(0, gy - 26, W, gy - 26, stroke(hexc("#7fcf86"), 5))
    p = rig.default_pose()
    p.update(standing=True, near_foot=(-24.0, 158.0), far_foot=(22.0, 158.0), near_hand_pos=(-60.0, -24.0),
             far_hand_pos=(66.0, -28.0))
    f = rig.default_face()
    f.update(yaw=0.2, pitch=-0.25, gx=0.1, gy=0.9, msmile=0.6, lower=0.3, braise=0.4,
             blink=1.0 if 10.2 < t < 10.36 else 0.0)
    rig.draw_character(c, rig.PIP, f, p, t, 540, gy - 30 - 158 * 0.9, 0.9, rim_moon=0.5, rim_warm=0.2)
    label(c, "atoms holding you up", 540, 430, 46, WARM, appear(t, t_gr, 0.35), "bold")


def _chair(c, x, seat_y):
    col, dk = "#b9824f", "#8a5c34"
    for lx in (x - 120, x + 110):
        c.drawPath(_rr(lx - 14, seat_y, lx + 14, seat_y + 300, 8), stroke(hexc(OL), 6))
        c.drawPath(_rr(lx - 14, seat_y, lx + 14, seat_y + 300, 8), fill(hexc(dk)))
    c.drawPath(_rr(x - 130, seat_y - 330, x - 100, seat_y + 10, 10), stroke(hexc(OL), 6))
    c.drawPath(_rr(x - 130, seat_y - 330, x - 100, seat_y + 10, 10), fill(hexc(col)))
    for yy in (seat_y - 300, seat_y - 210):
        c.drawPath(_rr(x - 140, yy, x - 80, yy + 40, 10), stroke(hexc(OL), 5))
        c.drawPath(_rr(x - 140, yy, x - 80, yy + 40, 10), fill(hexc(col)))
    seat = _rr(x - 150, seat_y - 20, x + 150, seat_y + 22, 12)
    c.drawPath(seat, stroke(hexc(OL), 6))
    c.drawPath(seat, fill(hexc(col)))


def _beat_chair(c, t, t_ch):
    floor = 1330
    c.drawRect(skia.Rect.MakeLTRB(0, floor, W, H), fill(hexc("#121d42")))
    c.drawLine(0, floor, W, floor, stroke(hexc("#6f8fd8", 0.6), 4))
    sx, seat_y = 380, 1030
    _chair(c, sx, seat_y)
    p = rig.default_pose()
    p.update(near_foot=(60.0, 120.0), far_foot=(86.0, 116.0), near_hand_pos=(56.0, -40.0),
             far_hand_pos=(86.0, -44.0), far_hand_front=True)
    f = rig.default_face()
    f.update(yaw=0.3, gx=0.6, gy=0.2, msmile=0.55, lower=0.3, blink=1.0 if 12.9 < t < 13.06 else 0.0)
    rig.draw_character(c, rig.PIP, f, p, t, sx, seat_y - 20, 0.95, rim_moon=0.5, rim_warm=0.2)
    # magnifier bubble showing atoms inside the seat
    mx, my, mr = 790, 760, 200
    a = appear(t, t_ch - 0.4, 0.4)
    if a > 0.01:
        c.drawLine(sx + 150, seat_y - 4, mx - mr * 0.7, my + mr * 0.7, stroke(hexc(COOL, 0.8 * a), 5))
        circ = p_circle(mr, mx, my)
        c.save()
        c.clipPath(circ, skia.ClipOp.kIntersect, True)
        c.drawCircle(mx, my, mr, fill(hexc("#b9824f", a)))
        c.drawRect(skia.Rect.MakeLTRB(mx - mr, my - mr, mx + mr, my - 60), fill(hexc("#1b2a5a", a)))
        for i in range(4):
            cute_atom(c, mx - 150 + i * 100, my + 20, 44, t, "determined" if i in (1, 2) else "happy", arms=1.0,
                      seed=i, look=(0.0, -1.0), alpha=a)
        c.restore()
        glow_path(c, circ, COOL, 7.0, a)
        label(c, "atoms in the seat", mx, my + mr + 60, 40, COOL, a, "bold")
