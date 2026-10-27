"""split_moon: Tess at her dorm window and Pip on the roof under the same Moon."""
import math

import skia

import rig
import scene_roof as sr
from chalk import COOL, WARM, appear, cue, dotted, label
from gfx import clamp, ease_io, fill, hexc, lerp, linear_shader, smooth_path, stroke

W, H = 1080, 1920
OL = rig.OUTLINE
SPLIT = 880
MOON_R = 95


def _blinks(t, times, d=0.17):
    b = 0.0
    for tb in times:
        x = (t - tb) / d
        if 0 <= x <= 1:
            b = max(b, 1 - abs(2 * x - 1))
    return min(1.0, b * 1.7)


def _night_sky(c, y0, y1, top="#070e27", bottom="#24407a"):
    p = skia.Paint(AntiAlias=True)
    p.setShader(linear_shader((0, y0), (0, y1), [hexc(top), hexc(bottom)]))
    c.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), p)


def _stars(c, y0, y1, seed, n=70):
    import numpy as np
    r = np.random.default_rng(seed)
    xs, ys, rs = r.uniform(0, W, n), r.uniform(y0, y1, n), r.uniform(0.8, 2.2, n)
    for x, y, rr in zip(xs, ys, rs):
        c.drawCircle(x, y, rr, fill(hexc("#eaf1ff", 0.8)))


def _dorm(c, t, k):
    """Top panel: brick building with Tess at a warm window."""
    off = -W * (1 - k)
    c.save()
    c.translate(off, 0)
    top = 330
    c.drawRect(skia.Rect.MakeLTRB(-20, top, W + 20, SPLIT), fill(hexc("#5a2f2d")))
    for row, y in enumerate(range(top + 34, SPLIT, 30)):
        c.drawLine(-20, y, W + 20, y, stroke(hexc("#3f1f1f"), 3))
        for x in range(-20 + (row % 2) * 45, W + 20, 90):
            c.drawLine(x, y - 30, x, y, stroke(hexc("#3f1f1f"), 3))
    c.drawRect(skia.Rect.MakeLTRB(-20, top - 6, W + 20, top + 30), fill(hexc("#3b2224")))
    c.drawRect(skia.Rect.MakeLTRB(-20, top - 6, W + 20, top), fill(hexc("#8f7f9e", 0.8)))
    # neighbouring windows
    for (x0, lit) in ((700, True), (900, False)):
        c.drawRect(skia.Rect.MakeLTRB(x0, 470, x0 + 150, 720), fill(hexc("#f0c27a" if lit else "#1a2348")))
        c.drawRect(skia.Rect.MakeLTRB(x0, 470, x0 + 150, 720), stroke(hexc("#e8dcc0"), 8))
        c.drawLine(x0 + 75, 470, x0 + 75, 720, stroke(hexc("#e8dcc0"), 5))
        if lit:
            c.drawRect(skia.Rect.MakeLTRB(x0 + 8, 478, x0 + 142, 712), fill(hexc("#ffb36b", 0.25), blur=10))
    # Tess's window
    wx0, wx1, wy0, sill = 120, 610, 400, 830
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 40, wy0 - 40, wx1 + 40, sill + 50), fill(hexc("#ffb36b", 0.22), blur=40))
    ip = skia.Paint(AntiAlias=True)
    ip.setShader(linear_shader((0, wy0), (0, sill), [hexc("#ffd79a"), hexc("#f2a65e")]))
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, sill), ip)
    # pennant + shelf inside
    pn = skia.Path()
    pn.moveTo(160, 560)
    pn.lineTo(300, 585)
    pn.lineTo(160, 615)
    pn.close()
    c.drawPath(pn, fill(hexc("#2e8c88")))
    c.drawRect(skia.Rect.MakeLTRB(430, 600, 590, 610), fill(hexc("#a8744d")))
    for k, (bh, col) in enumerate(((56, "#c0392b"), (48, "#2d3c6c"), (62, "#f2c94c"), (44, "#2e8c88"))):
        c.drawRect(skia.Rect.MakeLTRB(445 + k * 26, 600 - bh, 465 + k * 26, 600), fill(hexc(col)))
    # string lights
    pts = [(wx0 + 10, wy0 + 30), ((wx0 + wx1) / 2, wy0 + 70), (wx1 - 10, wy0 + 30)]
    cord = skia.Path()
    cord.moveTo(*pts[0])
    cord.quadTo(pts[1][0], pts[1][1] + 30, *pts[2])
    c.drawPath(cord, stroke(hexc("#3a2a20"), 3))
    for i in range(11):
        u = i / 10
        x = (1 - u) ** 2 * pts[0][0] + 2 * (1 - u) * u * pts[1][0] + u * u * pts[2][0]
        y = (1 - u) ** 2 * pts[0][1] + 2 * (1 - u) * u * (pts[1][1] + 30) + u * u * pts[2][1]
        tw = 0.75 + 0.25 * math.sin(t * 2.0 + i * 1.7)
        col = ("#fff1b8", "#ffc98a", "#ffd6f0")[i % 3]
        c.drawCircle(x, y + 10, 16, fill(hexc(col, 0.35 * tw), blur=8))
        c.drawCircle(x, y + 10, 6, fill(hexc(col)))
    # sill (drawn before Tess so her forearms rest on it)
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 30, sill - 8, wx1 + 30, sill + 22), fill(hexc("#efe6d4")))
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 30, sill + 14, wx1 + 30, sill + 22), fill(hexc("#b9ab90")))
    # Tess (clipped to the window above the sill)
    S = 1.15
    hx, hy = 360, 935
    f = rig.default_face()
    f.update(yaw=0.36, pitch=0.2, roll=-0.1, gx=0.75, gy=-0.75, eopen=0.84, lower=0.3, msmile=0.45, binner=0.35,
             braise=0.1, blush=0.45, wet=0.45, blink=_blinks(t, [2.95, 4.45]))
    p = rig.default_pose()
    p.update(near_hand_pos=(2.0, -172.0), near_elbow=-1.0, far_hand_pos=(118.0, -100.0), far_front=True,
             near_foot=(60.0, 60.0), far_foot=(80.0, 60.0), breath=math.sin(t * 1.75), lean=0.05)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, sill + 4), skia.ClipOp.kIntersect, True)
    rig.draw_character(c, rig.TESS, f, p, t, hx, hy, S, rim_moon=0.8, rim_warm=0.6)
    c.restore()
    # window frame on top
    c.drawRect(skia.Rect.MakeLTRB(wx0, wy0, wx1, sill), stroke(hexc("#e8dcc0"), 14))
    c.drawRect(skia.Rect.MakeLTRB(wx0 - 7, wy0 - 7, wx1 + 7, sill + 7), stroke(hexc(OL), 3))
    c.restore()


def _roof_panel(c, t, k):
    off = (1 - k) * 1150
    c.save()
    c.translate(0, off)
    y0 = SPLIT + 8
    _night_sky(c, y0, 1400, "#0a1433", "#2a4580")
    _stars(c, y0 + 10, 1200, 21, 45)
    sr.draw_moon(c, 800, 1050, MOON_R)
    hills = smooth_path([(-50, 1500), (-50, 1270), (200, 1240), (420, 1275), (680, 1235), (900, 1265), (1130, 1245),
                         (1130, 1500)], True, 0.4)
    c.drawPath(hills, fill(hexc("#16244b")))
    for i in range(26):
        x = (i * 97) % 1080
        y = 1268 + (i * 37) % 40
        c.drawCircle(x, y, 2.2, fill(hexc("#ffd28a", 0.75)))
    roof = skia.Path()
    roof.moveTo(-50, 1330)
    roof.lineTo(1130, 1300)
    roof.lineTo(1130, 1950)
    roof.lineTo(-50, 1950)
    roof.close()
    rp = skia.Paint(AntiAlias=True)
    rp.setShader(linear_shader((0, 1300), (0, 1920), [hexc("#2f3d6b"), hexc("#18213f")]))
    c.drawPath(roof, rp)
    c.drawLine(-50, 1326, 1130, 1296, stroke(hexc("#6f80b8"), 8))
    for k_ in range(1, 9):
        y = 1330 + k_ * (30 + k_ * 6)
        c.drawLine(-50, y, 1130, y - 30, stroke(hexc("#1a2448", 0.9), 2.5))
    f = rig.default_face()
    f.update(yaw=0.34, pitch=0.22, gx=0.75, gy=-0.75, eopen=0.9, lower=0.22, msmile=0.3, binner=0.45,
             blush=0.4, wet=0.35, blink=_blinks(t, [4.25]))
    from poses import PIP_POSES
    p = rig.default_pose()
    p.update(PIP_POSES["hug"])
    p.update(breath=math.sin(t * 1.9), slump=0.2)
    rig.draw_character(c, rig.PIP, f, p, t, 360, 1480, 1.0, rim_moon=0.9, rim_warm=0.0)
    c.restore()


def scene_split(c, t, dur, cues, params):
    t_d = cue(cues, "dorm", 2.3)
    t_r = cue(cues, "roof", 3.9)
    k_top = ease_io(clamp((t - (t_d - 0.35)) / 0.6))
    k_bot = ease_io(clamp((t - (t_r - 0.35)) / 0.6))
    _night_sky(c, 0, H, "#070e27", "#1f3670")
    _stars(c, 0, H, 7, 120)
    mx = lerp(540, 800, k_top)
    my = lerp(760, 250, k_top)
    mr = lerp(150, MOON_R, k_top)
    push = 1 + 0.03 * clamp(t / max(t_d, 0.1))
    sr.draw_moon(c, mx, my, mr * (push if k_top < 0.01 else 1.0))
    if k_top > 0.001:
        _dorm(c, t, k_top)
    if k_bot > 0.001:
        _roof_panel(c, t, k_bot)
        a = k_bot
        c.drawRect(skia.Rect.MakeLTRB(0, SPLIT - 3, W, SPLIT + 8), fill(hexc("#0a0f22", a)))
        c.drawLine(0, SPLIT + 2, W, SPLIT + 2, stroke(hexc("#dfe9ff", 0.7 * a), 3, blur=2))
        la = appear(t, t_r + 0.35, 0.4)
        if la > 0:
            pts = [(800, 250 + MOON_R + 16), (800, 1050 - MOON_R - 16)]
            dotted(c, pts, WARM, 4.5, 26, la, la)
            label(c, "same Moon", 935, 600, 36, WARM, la, "extrabold")
