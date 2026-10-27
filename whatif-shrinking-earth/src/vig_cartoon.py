"""Cartoon vignettes: stacked Pips, bicycle pump, seesaws (elephants, mountain)."""
import math

import numpy as np
import skia

import rig
from chalk import COOL, WARM, appear, cue, glow_path, label, p_arrow, p_circle, pop, ramp, spotlight_bg
from gfx import (clamp, ease_back, ease_in, ease_io, ease_out, fill, font, hexc, lerp, linear_shader, mixhex,
                 radial_shader, smooth_path, smoothstep, stroke, tapered_stroke)

W, H = 1080, 1920
OL = rig.OUTLINE


def _ol(c, path, color, width=6.0, alpha=1.0):
    c.drawPath(path, stroke(hexc(OL, alpha), width))
    c.drawPath(path, fill(hexc(color, alpha)))


def _rr(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def _floor_glow(c, y, rx=470, ry=60, alpha=0.25, cx=540):
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, y - ry, cx + rx, y + ry), fill(hexc("#7d9ae0", alpha), blur=36))


def _blinks(t, times, d=0.17):
    b = 0.0
    for tb in times:
        x = (t - tb) / d
        if 0 <= x <= 1:
            b = max(b, 1 - abs(2 * x - 1))
    return min(1.0, b * 1.7)


def _sweat(c, x, y, s, a=1.0):
    p = skia.Path()
    p.moveTo(x, y - 14 * s)
    p.cubicTo(x + 9 * s, y - 2 * s, x + 9 * s, y + 9 * s, x, y + 9 * s)
    p.cubicTo(x - 9 * s, y + 9 * s, x - 9 * s, y - 2 * s, x, y - 14 * s)
    c.drawPath(p, stroke(hexc(OL, a), 4))
    c.drawPath(p, fill(hexc("#bfe6ff", a)))


# ============================================================================
# vignette_stack: "carrying three extra copies of yourself"
# ============================================================================

def _pip_standing(hands="side"):
    p = rig.default_pose()
    p.update(standing=True, near_foot=(-24.0, 158.0), far_foot=(22.0, 158.0), far_hand_front=False)
    if hands == "side":
        p.update(near_hand_pos=(-64.0, -22.0), far_hand_pos=(70.0, -26.0))
    elif hands == "up":
        p.update(near_hand_pos=(-165.0, -190.0), far_hand_pos=(168.0, -196.0), near_hand="open", far_hand="open")
    elif hands == "proud":
        p.update(near_hand_pos=(-40.0, -40.0), far_hand_pos=(46.0, -44.0))
    return p


def scene_stack(c, t, dur, cues, params):
    t_std = cue(cues, "standing", 0.5)
    t_three = cue(cues, "three", 2.2)
    t_cop = cue(cues, "copies", 2.9)
    SX = 440
    spotlight_bg(c, center=(SX, 900), inner="#2c417f", outer="#0a1230", r=1150)
    _floor_glow(c, 1395, 430, 60, 0.30, cx=SX)
    S = 0.84
    feet_y = 1390
    hip0 = feet_y - 160 * S
    lands = [t_three - 0.08, t_three + 0.32, t_cop + 0.05]
    n = sum(1 for x in lands if t >= x)
    after = t - lands[0]
    strain = clamp(after / 0.25) if after > 0 else 0.0
    wob_amp = ramp(t, lands[2], 0.8)
    # bottom Pip
    jitter = math.sin(t * 47) * 2.0 * strain
    bounce = 0.0
    for lt in lands:
        if t > lt:
            bounce += 14 * math.exp(-(t - lt) * 7) * math.cos((t - lt) * 20)
    f0 = rig.default_face()
    if strain < 0.5:
        f0.update(yaw=0.12, gx=0.0, gy=0.1, msmile=0.65, lower=0.35, braise=0.35, blush=0.35,
                  blink=_blinks(t, [0.25, 1.7]))
        pose0 = _pip_standing("proud" if t > t_std else "side")
    else:
        f0.update(yaw=0.05, pitch=-0.08, blink=1.0, tilt=-0.6, lower=0.0, bfurrow=1.0, binner=-1.0,
                  mopen=0.42, mteeth=1.0, mtongue=0.0, mwide=1.45, msmile=-0.55, blush=1.0, squish=1.0)
        pose0 = _pip_standing("up")
        pose0["near_foot"] = (-30.0, 150.0)
        pose0["far_foot"] = (28.0, 150.0)
    rig.draw_character(c, rig.PIP, f0, pose0, t, SX + jitter, hip0 + bounce * 0.3, S, rim_moon=0.6, rim_warm=0.2)
    if strain > 0.5:
        hcx, hcy = SX + jitter, hip0 - 228 * S
        for k, ang in enumerate((-2.6, -2.3, -0.8, -0.5)):
            r0, r1 = 118 * S, 150 * S
            wig = 1 + 0.06 * math.sin(t * 30 + k)
            c.drawLine(hcx + math.cos(ang) * r0 * wig, hcy + math.sin(ang) * r0 * wig,
                       hcx + math.cos(ang) * r1 * wig, hcy + math.sin(ang) * r1 * wig, stroke(hexc(WARM, 0.8), 5))
    if strain > 0.5 and n >= 2:
        for k, (dx, dy) in enumerate(((-120, -260), (115, -300))):
            ph = ((t - lands[1]) * 0.8 + k * 0.5) % 1.0
            _sweat(c, SX + dx * S, hip0 + (dy + ph * 60) * S, 1.6, 1 - ph)
    # riders
    lvl_dy = -303 * S
    y_prev = hip0
    for k in range(3):
        lt = lands[k]
        y_k = y_prev + lvl_dy
        y_prev = y_k
        if t < lt - 0.45:
            continue
        drop = clamp((t - (lt - 0.45)) / 0.45)
        off = -950 * (1 - ease_in(drop))
        wob = math.sin(t * 2.7 + k * 0.8) * (k + 1) * 9 * wob_amp
        rot = math.sin(t * 2.7 + k * 0.8 - 0.4) * 0.025 * (k + 1) * wob_amp
        f = rig.default_face()
        pose = rig.default_pose()
        pose.update(rig.default_pose())
        from poses import PIP_POSES
        pose.update(PIP_POSES["hug"])
        pose["slump"] = 0.0
        if k == 0:
            f.update(yaw=0.2, blink=1.0, lower=0.85, msmile=0.95, mopen=0.15, mteeth=0.8, blush=0.5)
        elif k == 1:
            f.update(yaw=-0.15, gx=-0.3, gy=0.7, pitch=-0.12, msmile=0.8, mopen=0.3, mteeth=1.0, lower=0.4,
                     braise=0.4, blink=_blinks(t, [3.6]))
        else:
            f.update(yaw=0.25, gx=0.2, gy=-0.1, msmile=0.95, mopen=0.45, mteeth=1.0, lower=0.45, braise=0.6,
                     blush=0.5)
            wave = math.sin(t * 9) * 26
            pose.update(near_hand_pos=(-120.0 + wave * 0.3, -270.0 + wave), near_hand="open", far_front=False)
        c.save()
        c.translate(SX + wob, y_k + off)
        c.rotate(math.degrees(rot))
        rig.draw_character(c, rig.PIP, f, pose, t + k * 0.7, 0, 0, S, rim_moon=0.6, rim_warm=0.2)
        c.restore()
    # labels
    if t_std <= t < lands[0] + 0.3:
        a = appear(t, t_std, 0.3) * (1 - ramp(t, lands[0], 0.3))
        label(c, "you", SX + 220, hip0 - 120, 44, WARM, a, "bold")
        glow_path(c, p_arrow(SX + 190, hip0 - 140, SX + 100, hip0 - 190, 16), WARM, 4.0, a)
    if t > t_cop + 0.35:
        a = appear(t, t_cop + 0.35, 0.35)
        label(c, "4 × the weight", 800, 640, 52, WARM, a, "extrabold")


# ============================================================================
# vignette_pump: squeezed air heats up
# ============================================================================

def scene_pump(c, t, dur, cues, params):
    t_heat = cue(cues, "heats", 1.2)
    t_pump = cue(cues, "pump", 2.9)
    t_warm = cue(cues, "warming", 3.2)
    spotlight_bg(c, center=(560, 820), inner="#2b4a6e", outer="#0a1424", r=1150)
    _floor_glow(c, 1330, 480, 50, 0.25)
    heat = smoothstep(t_heat - 0.2, t_warm + 1.3, t)
    # pumping cycle: quick push down, slower return
    cyc = (t * 1.15) % 1.0
    press = ease_io(cyc / 0.4) if cyc < 0.4 else 1 - ease_io((cyc - 0.4) / 0.6)
    hy = lerp(330, 590, press)
    bx0, bx1, by0, by1 = 470, 610, 620, 1290
    # bicycle wheel at the right edge
    wx, wy, wr = 1150, 980, 320
    c.drawCircle(wx, wy, wr, stroke(hexc("#14161c"), 46))
    c.drawCircle(wx, wy, wr, stroke(hexc("#2b2f38"), 30))
    for k in range(18):
        a = k * math.tau / 18 + 0.1
        c.drawLine(wx, wy, wx + math.cos(a) * (wr - 22), wy + math.sin(a) * (wr - 22), stroke(hexc("#9aa3ad", 0.8), 3))
    c.drawCircle(wx, wy, 30, fill(hexc("#9aa3ad")))
    # hose from the base to the valve
    hose = skia.Path()
    hose.moveTo(600, 1300)
    hose.cubicTo(760, 1330, 760, 1120, 860, 1080)
    c.drawPath(hose, stroke(hexc(OL), 22))
    c.drawPath(hose, stroke(hexc("#2a2d35"), 14))
    c.drawPath(_rr(845, 1050, 905, 1105, 10), fill(hexc("#c9ced8")))
    c.drawPath(_rr(845, 1050, 905, 1105, 10), stroke(hexc(OL), 5))
    # base plate
    _ol(c, _rr(330, 1290, 750, 1340, 18), "#2a2d35", 6)
    _ol(c, _rr(300, 1310, 400, 1345, 12), "#3a3e48", 5)
    _ol(c, _rr(680, 1310, 780, 1345, 12), "#3a3e48", 5)
    # barrel
    barrel = _rr(bx0, by0, bx1, by1, 26)
    c.drawPath(barrel, stroke(hexc(OL), 7))
    bp = skia.Paint(AntiAlias=True)
    bp.setShader(linear_shader((bx0, 0), (bx1, 0), [hexc("#8f99a8"), hexc("#e3e8ef"), hexc("#b4bdc9"), hexc("#7b8594")],
                               [0.0, 0.35, 0.6, 1.0]))
    c.drawPath(barrel, bp)
    if heat > 0.01:
        hp = skia.Paint(AntiAlias=True)
        hp.setShader(linear_shader((0, by1), (0, by0 + 120), [hexc("#ff4a2a", 0.75 * heat), hexc("#ff8a3a", 0.35 * heat),
                                                             hexc("#ff8a3a", 0.0)], [0.0, 0.5, 1.0]))
        c.save()
        c.clipPath(barrel, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeLTRB(bx0, by0, bx1, by1), hp)
        c.restore()
        c.drawPath(barrel, stroke(hexc("#ff7a45", 0.35 * heat), 26, blur=16))
    # cutaway window with air molecules
    wx0, wx1, wy0, wy1 = 492, 588, 700, 1255
    win = _rr(wx0, wy0, wx1, wy1, 14)
    c.drawPath(win, fill(hexc("#162238")))
    c.save()
    c.clipPath(win, skia.ClipOp.kIntersect, True)
    piston = lerp(720, 1010, press)
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0 - 10, wx1, piston), fill(hexc("#0e1626")))
    c.drawRect(skia.Rect.MakeLTRB(536, wy0 - 10, 544, piston), fill(hexc("#c9ced8")))
    c.drawPath(_rr(wx0 + 2, piston - 4, wx1 - 2, piston + 18, 6), fill(hexc("#3a3e48")))
    rng = np.random.default_rng(11)
    bxs, bys, phs = rng.uniform(0.08, 0.92, 26), rng.uniform(0.05, 0.95, 26), rng.uniform(0, 6.28, 26)
    jig = 2.5 + 7.0 * heat + 3.0 * press
    col = mixhex("#7fd3ff", "#ffb04a", heat)
    for i in range(26):
        x = lerp(wx0, wx1, bxs[i]) + math.sin(t * (9 + 6 * heat) + phs[i]) * jig
        y = lerp(piston + 26, wy1 - 8, bys[i]) + math.cos(t * (11 + 7 * heat) + phs[i] * 1.3) * jig
        c.drawCircle(x, y, 7, fill(hexc(col)))
        c.drawCircle(x - 2, y - 2, 2.4, fill(hexc("#ffffff", 0.7)))
    c.restore()
    c.drawPath(win, stroke(hexc(OL), 5))
    # top cap, rod and T-handle
    _ol(c, _rr(bx0 - 14, by0 - 34, bx1 + 14, by0 + 6, 12), "#3a3e48", 6)
    c.drawLine(540, hy, 540, by0 - 30, stroke(hexc(OL), 20))
    c.drawLine(540, hy, 540, by0 - 30, stroke(hexc("#d7dce4"), 12))
    _ol(c, _rr(300, hy - 22, 780, hy + 22, 20), "#c9ced8", 6)
    for gx in (300, 640):
        _ol(c, _rr(gx, hy - 30, gx + 140, hy + 30, 26), "#22252c", 6)
    # hands with yellow sleeves from above
    for (gx, sx, side) in ((370, 240, -1), (710, 860, 1)):
        sl = skia.Path()
        sl.moveTo(sx, -60)
        sl.lineTo(gx - side * 4, hy - 46)
        c.drawPath(sl, stroke(hexc(OL), 92))
        c.drawPath(sl, stroke(hexc("#f1b53e"), 80))
        c.drawPath(sl, stroke(hexc("#c8862a", 0.6), 22))
        c.drawCircle(gx, hy - 40, 34, fill(hexc(OL)))
        c.drawCircle(gx - side * 2, hy - 24, 50, fill(hexc(OL)))
        c.drawCircle(gx - side * 2, hy - 24, 44, fill(hexc(rig.PIP["skin"])))
        for k in range(3):
            c.drawLine(gx - 30 + k * 22, hy - 4, gx - 30 + k * 22, hy + 16, stroke(hexc(rig.PIP["skin_sh"]), 4))
    # heat shimmer rising beside the barrel
    if heat > 0.02:
        for k, x0 in enumerate((440, 470, 610, 640)):
            ph = (t * 0.7 + k * 0.27) % 1.0
            pts = [(x0 + math.sin(j * 0.9 + t * 4 + k) * 9, 1180 - j * 34 - ph * 60) for j in range(9)]
            c.drawPath(smooth_path(pts, False, 0.6), stroke(hexc("#ffb27a", 0.55 * heat * math.sin(ph * math.pi)), 5))
    # thermometer
    tx, ty = 230, 820
    _ol(c, _rr(tx - 26, ty - 260, tx + 26, ty + 40, 26), "#f3f6fb", 6)
    c.drawCircle(tx, ty + 60, 46, fill(hexc(OL)))
    c.drawCircle(tx, ty + 60, 40, fill(hexc("#e04848")))
    lvl = lerp(ty + 10, ty - 220, 0.15 + 0.85 * heat)
    c.drawPath(_rr(tx - 12, lvl, tx + 12, ty + 50, 12), fill(hexc("#e04848")))
    for k in range(6):
        c.drawLine(tx + 14, ty - 220 + k * 44, tx + 26, ty - 220 + k * 44, stroke(hexc(OL), 3))
    if t > t_warm:
        label(c, "squeezed air heats up", 540, 1418, 50, "#ffcf9a", appear(t, t_warm, 0.4), "extrabold")


# ============================================================================
# seesaw helpers
# ============================================================================

def _plank_angle(t, events):
    """Superpose damped step responses: events = [(t0, delta, freq, damp)]."""
    a = 0.0
    for (t0, d, fq, dp) in events:
        if t > t0:
            x = t - t0
            a += d * (1 - math.exp(-dp * x) * math.cos(fq * math.tau * x))
    return a


def _seesaw_base(c, px, py, ground_y):
    tri = skia.Path()
    tri.moveTo(px, py + 8)
    tri.lineTo(px - 95, ground_y)
    tri.lineTo(px + 95, ground_y)
    tri.close()
    _ol(c, tri, "#c0503f", 7)
    c.drawCircle(px, py + 8, 16, fill(hexc(OL)))
    c.drawCircle(px, py + 8, 10, fill(hexc("#f0c95c")))


def _plank(c, half):
    p = _rr(-half, -16, half, 16, 12)
    _ol(c, p, "#c8925c", 7)
    for k in range(-5, 6):
        c.drawLine(k * half / 5.5, -10, k * half / 5.5 + 40, -10, stroke(hexc("#a87547", 0.6), 3))
    c.drawLine(-half + 12, 4, half - 12, 4, stroke(hexc("#a87547", 0.5), 3))


def _spoon(c, x, y, speck_col="#ffffff", glow_col="#fff3c4", t=0.0, scale=1.0):
    """Teaspoon lying on the plank, bowl at (x, y) (local coords, y = plank top)."""
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    hd = skia.Path()
    hd.moveTo(60, -10)
    hd.cubicTo(140, -14, 220, -18, 300, -26)
    c.drawPath(hd, stroke(hexc(OL), 26))
    c.drawPath(hd, stroke(hexc("#cfd6df"), 17))
    c.drawPath(hd, stroke(hexc("#ffffff", 0.7), 5))
    bowl = skia.Path()
    bowl.addOval(skia.Rect.MakeLTRB(-70, -64, 74, -4))
    _ol(c, bowl, "#d9dfe7", 6)
    inner = skia.Path()
    inner.addOval(skia.Rect.MakeLTRB(-54, -56, 58, -18))
    c.drawPath(inner, fill(hexc("#aab3bf")))
    c.restore()
    # the speck of ultra-dense matter
    sx, sy = x, y - 40 * scale
    pulse = 1 + 0.08 * math.sin(t * 5)
    c.drawCircle(sx, sy, 60 * scale * pulse, fill(hexc(glow_col, 0.25), blur=26))
    c.drawCircle(sx, sy, 22 * scale * pulse, fill(hexc(glow_col, 0.6), blur=10))
    c.drawCircle(sx, sy, 7 * scale, fill(hexc(speck_col)))


def draw_elephant(c, x, y, s, t, look=0.0, surprise=0.0, seed=0, blink=0.0):
    """Cute elephant facing left; (x, y) = bottom centre of the feet."""
    body_c, sh_c, ear_in = "#a3adba", "#828d9b", "#e7aab6"
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    # tail
    tl = skia.Path()
    tl.moveTo(68, -78)
    tl.quadTo(96, -70, 92, -44)
    c.drawPath(tl, stroke(hexc(OL), 7))
    c.drawCircle(92, -42, 7, fill(hexc(OL)))
    # far legs
    for lx in (-24, 50):
        _ol(c, _rr(lx - 15, -48, lx + 15, 0, 11), sh_c, 6)
    body = skia.Path()
    body.addOval(skia.Rect.MakeLTRB(-70, -128, 84, -30))
    _ol(c, body, body_c, 7)
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawOval(skia.Rect.MakeLTRB(-40, -60, 110, 10), fill(hexc(sh_c, 0.6), blur=14))
    c.restore()
    for lx in (-44, 30):
        lg = _rr(lx - 17, -52, lx + 17, 0, 12)
        _ol(c, lg, body_c, 6)
        for k in range(3):
            c.drawCircle(lx - 9 + k * 9, -4, 3.5, fill(hexc("#f3efe6")))
    # head
    hx, hy = -74, -102
    trunk_curl = surprise
    tr = skia.Path()
    tr.moveTo(hx - 30, hy + 4)
    tr.cubicTo(hx - 62, hy + 20, hx - 70 + 20 * trunk_curl, hy + 60 - 70 * trunk_curl,
               hx - 52 + 18 * trunk_curl, hy + 82 - 100 * trunk_curl)
    c.drawPath(tr, stroke(hexc(OL), 32))
    c.drawPath(tr, stroke(hexc(body_c), 24))
    for k in range(3):
        c.drawLine(hx - 46 - k * 4, hy + 14 + k * 14 - 30 * trunk_curl * (k / 2),
                   hx - 36 - k * 4, hy + 16 + k * 14 - 30 * trunk_curl * (k / 2), stroke(hexc(sh_c), 3))
    head = skia.Path()
    head.addCircle(hx, hy, 46)
    _ol(c, head, body_c, 7)
    # ear
    ear = smooth_path([(hx + 10, hy - 42), (hx + 56, hy - 58), (hx + 74, hy - 8), (hx + 56, hy + 40),
                       (hx + 18, hy + 34)], True, 0.5)
    _ol(c, ear, body_c, 6)
    ei = smooth_path([(hx + 22, hy - 30), (hx + 52, hy - 40), (hx + 62, hy - 6), (hx + 48, hy + 26),
                      (hx + 24, hy + 20)], True, 0.5)
    c.drawPath(ei, fill(hexc(ear_in)))
    # eye
    ex, ey = hx - 16, hy - 12
    er = 10 + 5 * surprise
    if blink > 0.6:
        c.drawLine(ex - er, ey, ex + er, ey, stroke(hexc(OL), 4))
    else:
        c.drawCircle(ex, ey, er, fill(hexc("#ffffff")))
        c.drawCircle(ex, ey, er, stroke(hexc(OL), 3.5))
        c.drawCircle(ex - 3 - 4 * look, ey - 1, 5.5 - 1.5 * surprise, fill(hexc("#1c1416")))
        c.drawCircle(ex - 5 - 4 * look, ey - 3.5, 1.8, fill(hexc("#ffffff")))
    # brow
    c.drawLine(ex - 12, ey - 16 - 9 * surprise, ex + 9, ey - 14 - 12 * surprise, stroke(hexc(OL), 4))
    c.drawCircle(hx - 4, hy + 16, 9, fill(hexc("#e88a9a", 0.45), blur=4))
    c.restore()


# ============================================================================
# vignette_elephants: a teaspoon of white-dwarf stuff vs four elephants
# ============================================================================

def scene_elephants(c, t, dur, cues, params):
    t_sp = cue(cues, "spoon", 1.0)
    t_w = cue(cues, "weigh", 2.0)
    t_4 = cue(cues, "four", 2.7)
    t_el = cue(cues, "elephants", 3.0)
    spotlight_bg(c, center=(540, 900), inner="#2c417f", outer="#0a1230", r=1150)
    ground = 1145
    c.drawRect(skia.Rect.MakeLTRB(0, ground, W, H), fill(hexc("#0f1a3d")))
    _floor_glow(c, ground, 520, 50, 0.35)
    lands = [t_w - 0.05, t_4 - 0.32, t_4 - 0.02, t_el + 0.02]
    ev = [(t_sp - 0.05, -0.20, 0.9, 3.0)]
    for lt in lands:
        ev.append((lt, 0.05, 1.2, 3.4))
    ang = _plank_angle(t, ev)
    px, py = 540, 940
    _seesaw_base(c, px, py, ground)
    spots = [(300, 0.0), (420, 0.0), (316, -112), (408, -112)]
    c.save()
    c.translate(px, py)
    c.rotate(math.degrees(ang))
    _plank(c, 470)
    sp = appear(t, t_sp - 0.15, 0.35)
    if sp > 0:
        c.save()
        c.translate(0, -60 * (1 - sp))
        _spoon(c, -380, -16, "#ffffff", "#fff3c4", t)
        c.restore()
    surprised = ramp(t, t_el + 0.45, 0.35)
    for k in range(4):
        lt = lands[k]
        if t < lt - 0.42:
            continue
        drop = clamp((t - (lt - 0.42)) / 0.42)
        off = -900 * (1 - ease_in(drop))
        sq = 0.0
        if t > lt:
            sq = 0.12 * math.exp(-(t - lt) * 8) * math.cos((t - lt) * 25)
        ex, ey = spots[k]
        c.save()
        c.translate(ex, -16 + ey + off)
        c.scale(1 + sq, 1 - sq)
        bl = 1.0 if (k == 1 and 3.9 < t < 4.05) else 0.0
        draw_elephant(c, 0, 0, 0.82, t, look=surprised, surprise=surprised * (1 if k % 2 == 0 else 0.7), seed=k,
                      blink=bl)
        c.restore()
    c.restore()
    if surprised > 0.05:
        for k, (x, y) in enumerate(((790, 580), (850, 540), (910, 585))):
            a = pop(t, t_el + 0.5 + k * 0.08, 0.3)
            if a > 0:
                f = font(64 * a, "black")
                c.drawString("!", x - 8, y, f, fill(hexc(WARM, min(1, a))))
    if sp > 0:
        label(c, "1 teaspoon", 175, 780, 40, "#fff3c4", appear(t, t_sp + 0.2), "bold")
    if t > t_el + 0.3:
        label(c, "= 4 elephants", 540, 1330, 58, WARM, appear(t, t_el + 0.3, 0.35), "extrabold")


# ============================================================================
# vignette_mountain: a teaspoon of neutron-star stuff vs a mountain
# ============================================================================

def _mountain(c, s=1.0, t=0.0):
    """Mountain sitting on y=0, centred on x=0."""
    c.save()
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-270, 0)
    body.lineTo(-120, -250)
    body.lineTo(-60, -210)
    body.lineTo(10, -420)
    body.lineTo(120, -240)
    body.lineTo(170, -280)
    body.lineTo(280, 0)
    body.close()
    _ol(c, body, "#6f7d96", 7)
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    shade = skia.Path()
    shade.moveTo(10, -420)
    shade.lineTo(60, -150)
    shade.lineTo(30, 0)
    shade.lineTo(300, 0)
    shade.lineTo(170, -280)
    shade.lineTo(120, -240)
    shade.close()
    c.drawPath(shade, fill(hexc("#55617a")))
    snow = skia.Path()
    snow.moveTo(10, -420)
    snow.lineTo(-55, -312)
    snow.lineTo(-25, -325)
    snow.lineTo(0, -300)
    snow.lineTo(30, -330)
    snow.lineTo(62, -310)
    snow.close()
    c.drawPath(snow, fill(hexc("#f4f8ff")))
    sn2 = skia.Path()
    sn2.moveTo(170, -280)
    sn2.lineTo(140, -232)
    sn2.lineTo(165, -244)
    sn2.lineTo(195, -232)
    sn2.close()
    c.drawPath(sn2, fill(hexc("#f4f8ff")))
    c.restore()
    for k, (x, h) in enumerate(((-200, 70), (-160, 90), (190, 80), (230, 60), (-110, 60))):
        tr = skia.Path()
        tr.moveTo(x, -h)
        tr.lineTo(x - 24, 0)
        tr.lineTo(x + 24, 0)
        tr.close()
        _ol(c, tr, "#2f6b4f", 4)
    c.restore()


def scene_mountain(c, t, dur, cues, params):
    t_n = cue(cues, "neutron", 1.9)
    t_tsp = cue(cues, "teaspoon", 3.8)
    t_b = cue(cues, "billion", 5.1)
    spotlight_bg(c, center=(540, 860), inner="#283d78", outer="#090f26", r=1150)
    ground = 1160
    c.drawRect(skia.Rect.MakeLTRB(0, ground, W, H), fill(hexc("#0f1a3d")))
    _floor_glow(c, ground, 540, 50, 0.35)
    t_land = t_tsp - 0.15
    ang = _plank_angle(t, [(-1.0, -0.22, 0.6, 3.0), (t_land, 0.22, 0.55, 2.2)])
    px, py = 540, 960
    _seesaw_base(c, px, py, ground)
    c.save()
    c.translate(px, py)
    c.rotate(math.degrees(ang))
    _plank(c, 480)
    _spoon(c, -390, -16, "#e9f4ff", "#8cc8ff", t)
    if t > t_land - 0.5:
        drop = clamp((t - (t_land - 0.5)) / 0.5)
        off = -1300 * (1 - ease_in(drop))
        sq = 0.0
        if t > t_land:
            sq = 0.06 * math.exp(-(t - t_land) * 6) * math.cos((t - t_land) * 20)
        c.save()
        c.translate(290, -16 + off)
        c.scale(1 + sq, 1 - sq)
        _mountain(c, 0.78, t)
        c.restore()
    c.restore()
    # dust puff at landing
    if t_land < t < t_land + 0.9:
        k = (t - t_land) / 0.9
        for j in range(7):
            a = j / 6 * math.pi
            x = 830 + math.cos(a) * 240 * k
            y = 940 - math.sin(a) * 50 * k
            c.drawCircle(x, y, 26 + 30 * k, fill(hexc("#c9d3e6", 0.35 * (1 - k)), blur=8))
    # the four elephants watch from the ground (callback)
    for k in range(4):
        x = 600 + k * 110
        look = ramp(t, t_land + 0.3, 0.4)
        draw_elephant(c, x, 1300, 0.48, t + k, look=look, surprise=look * 0.8)
    if t > t_n - 0.1:
        label(c, "neutron-star stuff", 230, 710, 40, "#bfe3ff", appear(t, t_n - 0.1), "bold")
    if t > t_b - 0.1:
        a = pop(t, t_b - 0.1, 0.4)
        c.save()
        c.translate(270, 580)
        c.scale(max(0.01, a), max(0.01, a))
        label(c, "≈ 1 billion tons", 0, 0, 56, WARM, min(1.0, a), "extrabold")
        c.restore()
