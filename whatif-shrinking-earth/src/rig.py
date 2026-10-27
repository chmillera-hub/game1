"""2D character rig for Pip and Tess, drawn with skia.

Faces use a pseudo-3D projection: each feature sits at a longitude/latitude on
the head sphere and is projected with the current yaw/pitch, so head turns and
nods move the features with parallax. Eyes have separate upper/lower lids,
irises with catchlights, lash lines; brows are tapered strokes; the mouth is a
parametric shape driven by visemes plus smile/round/teeth controls.
"""
import math

import numpy as np
import skia

from gfx import (circle, clamp, cubic_pts, ellipse_path, fill, hexc, lerp, mixhex,
                 quad_pts, smooth_path, stroke, tapered_stroke)

OUTLINE = "#24161c"
MOON_RIM = "#cfe0ff"
WARM_RIM = "#ffb36b"

PIP = dict(
    name="pip", R=100.0,
    skin="#c98c66", skin_sh="#9c6249", skin_lid="#b97d5b", blush="#e66e6e", lip="#6b2f2c",
    hair="#5b2c22", hair_hi="#8a4a37", hair_sh="#3d1c17",
    iris="#a4682e", iris_dk="#5a3214",
    hoodie="#f1b53e", hoodie_sh="#c8862a", hoodie_hi="#ffd77a",
    pants="#2d3c6c", pants_sh="#1f2a50", sock="#f08aa6", sock_sh="#c76683",
    eye_lon=29.0, eye_lat=-12.0, eye_w=43.0, eye_h=49.0, iris_r=0.46,
    brow_lat=21.0, brow_w=31.0, brow_th=8.0,
    nose_lat=-29.0, mouth_lat=-47.0, mouth_w=40.0,
    chin_y=0.93, cheek_out=1.03,
    neck_len=14.0, neck_w=32.0, torso_h=128.0, sh_half=62.0, waist_half=58.0,
    up_arm=70.0, fore_arm=64.0, arm_th=32.0, hand_r=14.5,
    thigh=86.0, shin=80.0, leg_th=36.0,
)

TESS = dict(
    name="tess", R=92.0,
    skin="#c98c66", skin_sh="#9c6249", skin_lid="#b97d5b", blush="#e46a6a", lip="#7a3534",
    hair="#2b1b18", hair_hi="#4e3329", hair_sh="#170e0c",
    iris="#6e4424", iris_dk="#3a220f",
    hoodie="#2e8c88", hoodie_sh="#1e6461", hoodie_hi="#5cc0b8",
    pants="#8d93a3", pants_sh="#676d7e", sock="#e9e6e0", sock_sh="#b9b5ad",
    eye_lon=28.0, eye_lat=-8.0, eye_w=37.0, eye_h=37.0, iris_r=0.43,
    brow_lat=20.0, brow_w=32.0, brow_th=7.5,
    nose_lat=-26.0, mouth_lat=-48.0, mouth_w=42.0,
    chin_y=1.06, cheek_out=0.99,
    neck_len=24.0, neck_w=30.0, torso_h=182.0, sh_half=72.0, waist_half=60.0,
    up_arm=98.0, fore_arm=90.0, arm_th=33.0, hand_r=15.0,
    thigh=122.0, shin=116.0, leg_th=40.0,
)


def default_face():
    return dict(
        yaw=0.25, pitch=0.0, roll=0.0,
        eopen=0.92, blink=0.0, tilt=0.0, lower=0.12, gx=0.3, gy=0.0, pupil=1.0, wet=0.0,
        eopen_l=None, eopen_r=None,
        braise=0.0, binner=0.0, bouter=0.0, bfurrow=0.0, basym=0.0,
        mopen=0.0, mwide=1.0, msmile=0.15, mround=0.0, mteeth=0.6, mtongue=0.3, masym=0.0,
        blush=0.25, tear=0.0, squish=0.0,
    )


def default_pose():
    return dict(
        lean=0.0, slump=0.0, shrug=0.0, breath=0.0,
        head_dx=0.0, head_dy=0.0,
        near_hand_pos=(30.0, -60.0), far_hand_pos=(60.0, -60.0), near_elbow=-1.0, far_elbow=-1.0,
        near_hand="mitten", far_hand="mitten", far_front=False, far_hand_front=False,
        near_foot=(60.0, 4.0), far_foot=(85.0, 0.0), knee_bend=1.0,
        mug=None, mug_pos=None, mug_tilt=0.0, steam=1.0,
        standing=False,
    )


# ----------------------------------------------------------------------------
# projection
# ----------------------------------------------------------------------------

def proj(R, lon, lat, yaw, pitch, rk=1.0):
    l = math.radians(lon) + yaw
    la = math.radians(lat) + pitch
    lc = max(-math.pi / 2, min(math.pi / 2, l))
    x = R * rk * math.sin(lc) * math.cos(la)
    y = -R * rk * math.sin(la)
    z = math.cos(l) * math.cos(la)
    return x, y, z


def head_outline(ch, f):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    sy = math.sin(yaw)
    cx = 0.52 * R * sy
    cy = R * ch["chin_y"] * (1 + 0.06 * math.sin(pitch)) + f.get("squish", 0) * 6
    co = ch["cheek_out"]
    p = skia.Path()
    p.moveTo(-R, 0)
    p.arcTo(skia.Rect.MakeLTRB(-R, -R, R, R), 180, 180, False)
    # far cheek (screen right when yaw>0) bulges a little
    rb = 1 + 0.035 * max(0, sy) - 0.02 * max(0, -sy)
    lb = 1 + 0.035 * max(0, -sy) - 0.02 * max(0, sy)
    p.cubicTo(R * rb * co, R * 0.52, cx + R * 0.48, cy, cx, cy)
    p.cubicTo(cx - R * 0.48, cy, -R * lb * co, R * 0.52, -R, 0)
    p.close()
    return p


# ----------------------------------------------------------------------------
# eyes
# ----------------------------------------------------------------------------

def _lid_curve(x0, y0, x1, y1, ym):
    ctrl = (0.5 * (x0 + x1), 2 * ym - 0.5 * (y0 + y1))
    return quad_pts((x0, y0), (x1, y1), ctrl, 18)


def draw_eye(c, ch, x, y, fx, side, f, open_override=None, light=(1.0, -1.0)):
    w0, h0 = ch["eye_w"], ch["eye_h"]
    op = f["eopen"] if open_override is None else open_override
    op = op * (1 - f["blink"])
    wide = max(0.0, op - 1.0)
    w = w0 * fx
    h = h0 * (1 + wide * 0.35)
    left, right = x - w / 2, x + w / 2
    top, bot = y - h / 2, y + h / 2
    tilt = f["tilt"]
    # which end is outer: side=-1 (screen-left eye) -> outer is left
    outer_is_left = side < 0
    cy_corner = y + h * 0.06
    yl = cy_corner
    yr = cy_corner
    sad = max(0.0, tilt)
    ang = max(0.0, -tilt)
    d_outer = sad * h * 0.22 - ang * h * 0.02
    d_inner = -sad * h * 0.06 + ang * h * 0.30
    if outer_is_left:
        yl += d_outer
        yr += d_inner
    else:
        yr += d_outer
        yl += d_inner
    o = clamp(op, 0.0, 1.0)
    lid_mid = top + (1 - o) * h * 0.98 + sad * h * 0.06 + ang * h * 0.10
    lower = clamp(f["lower"], 0, 1)
    low_mid = bot - lower * h * 0.62
    eye = ellipse_path(x, y, w / 2, h / 2)

    closed = (lid_mid >= low_mid - h * 0.06) or o < 0.06
    if not closed:
        # eye opening = ellipse ∩ below the upper lid ∩ above the lower lid (no painted lids,
        # so the face shading continues naturally over the eyelids)
        up = _lid_curve(left - 2, yl, right + 2, yr, lid_mid)
        lo = _lid_curve(right + 2, cy_corner + h * 0.04, left - 2, cy_corner + h * 0.04, low_mid)
        opening = smooth_path([tuple(q) for q in up] + [tuple(q) for q in lo[1:-1]], True, 0.08)
        # soft crease shadow above the lid
        crease = [tuple(q) for q in _lid_curve(left + w * 0.08, yl - h * 0.20, right - w * 0.08, yr - h * 0.20,
                                               lid_mid - h * 0.24)]
        c.drawPath(smooth_path(crease, False), stroke(hexc(ch["skin_sh"], 0.45), h0 * 0.05, blur=h0 * 0.02))
        c.save()
        c.clipPath(eye, skia.ClipOp.kIntersect, True)
        c.clipPath(opening, skia.ClipOp.kIntersect, True)
        c.drawPath(eye, fill(hexc("#f6f2ec")))
        # iris
        ir = h0 * ch["iris_r"]
        gx, gy = clamp(f["gx"], -1, 1), clamp(f["gy"], -1, 1)
        ix = x + gx * (w / 2 - ir * fx * 0.75) * 0.85
        iy = y + h * 0.04 + gy * (h / 2 - ir * 0.8) * 0.7
        irx = ir * max(0.55, fx)
        ip = skia.Paint(AntiAlias=True)
        ip.setShader(skia.GradientShader.MakeRadial(
            skia.Point(ix, iy + ir * 0.25), ir * 1.05,
            [hexc(mixhex(ch["iris"], "#ffd9a0", 0.35)), hexc(ch["iris"]), hexc(ch["iris_dk"])],
            [0.0, 0.55, 1.0]))
        c.drawOval(skia.Rect.MakeLTRB(ix - irx, iy - ir, ix + irx, iy + ir), ip)
        c.drawOval(skia.Rect.MakeLTRB(ix - irx, iy - ir, ix + irx, iy + ir),
                   stroke(hexc(ch["iris_dk"], 0.9), ir * 0.12))
        pr = ir * 0.47 * f["pupil"]
        c.drawOval(skia.Rect.MakeLTRB(ix - pr * irx / ir, iy - pr, ix + pr * irx / ir, iy + pr),
                   fill(hexc("#120a0a")))
        # shadow cast by the upper lid
        shp = smooth_path([tuple(q) for q in up] + [(right + 4, top - h), (left - 4, top - h)], True, 0.1)
        c.save()
        c.translate(0, h * 0.10)
        c.drawPath(shp, fill(hexc("#6f5a66", 0.42), blur=h * 0.07))
        c.restore()
        # catchlights (light from upper right)
        wet = f["wet"]
        hr = ir * (0.30 + 0.10 * wet)
        circle(c, ix + irx * 0.38, iy - ir * 0.40, hr, hexc("#ffffff", 0.95))
        circle(c, ix - irx * 0.36, iy + ir * 0.38, hr * 0.42, hexc("#ffffff", 0.8))
        if wet > 0.05:
            circle(c, ix + irx * 0.05, iy + ir * 0.62, hr * 0.35 * wet, hexc("#ffffff", 0.7 * wet))
        mref = f.get("moonref", 0.0)
        if mref > 0.01:
            mx_, my_ = ix - irx * 0.18, iy - ir * 0.05
            circle(c, mx_, my_, ir * 0.22, hexc("#f6f1df", 0.95 * mref))
            circle(c, mx_ - ir * 0.07, my_ - ir * 0.05, ir * 0.07, hexc("#c9c0aa", 0.8 * mref))
            circle(c, mx_ + ir * 0.09, my_ + ir * 0.08, ir * 0.05, hexc("#c9c0aa", 0.8 * mref))
        if wet > 0.05:
            wl = _lid_curve(left + w * 0.12, cy_corner + h * 0.04, right - w * 0.12, cy_corner + h * 0.04,
                            low_mid - h * 0.04)
            c.drawPath(smooth_path([tuple(q) for q in wl], False), stroke(hexc("#d6ecff", 0.8 * wet), h * 0.07))
        c.restore()
        # lash line along the upper lid
        lash = [tuple(q) for q in _lid_curve(left, yl, right, yr, lid_mid)]
        lw = h0 * (0.10 if ch["name"] == "pip" else 0.11)
        c.drawPath(tapered_stroke(lash, lw * 0.55, lw * 1.05, lw * 1.0) if not outer_is_left
                   else tapered_stroke(lash, lw * 1.05, lw * 0.55, lw * 1.0), fill(hexc(OUTLINE)))
        # outer wing
        if outer_is_left:
            ox, oy, dirx = left, yl, -1
        else:
            ox, oy, dirx = right, yr, 1
        wing = [(ox - dirx * w * 0.05, oy + h * 0.02), (ox + dirx * w * 0.10, oy - h * 0.07),
                (ox + dirx * w * 0.17, oy - h * 0.15)]
        c.drawPath(tapered_stroke(wing, lw * 0.9, lw * 0.2), fill(hexc(OUTLINE)))
        # lower lid line (stronger when the cheeks push up in a smile)
        lowl = [tuple(q) for q in _lid_curve(left + w * 0.16, cy_corner + h * 0.06,
                                             right - w * 0.16, cy_corner + h * 0.06, low_mid + h * 0.01)]
        c.drawPath(smooth_path(lowl, False), stroke(hexc(ch["skin_sh"], 0.6 + 0.3 * lower), h0 * 0.038))
    else:
        happy = lower > 0.45
        if happy:
            pts = quad_pts((left, y + h * 0.12), (right, y + h * 0.12), (x, y - h * 0.22), 16)
        else:
            ym = y + h * 0.10 + sad * h * 0.05
            pts = quad_pts((left, ym - h * 0.04 + (sad * h * 0.12 if outer_is_left else 0)),
                           (right, ym - h * 0.04 + (0 if outer_is_left else sad * h * 0.12)),
                           (x, ym + h * 0.16), 16)
        lw = h0 * 0.10
        c.drawPath(tapered_stroke([tuple(q) for q in pts], lw * 0.7, lw * 0.7, lw * 1.05), fill(hexc(OUTLINE)))
        # lashes on closed eyes
        if outer_is_left:
            q = pts[0]
            wing = [(q[0] + w * 0.04, q[1]), (q[0] - w * 0.08, q[1] + h * 0.04), (q[0] - w * 0.14, q[1] + h * 0.10)]
        else:
            q = pts[-1]
            wing = [(q[0] - w * 0.04, q[1]), (q[0] + w * 0.08, q[1] + h * 0.04), (q[0] + w * 0.14, q[1] + h * 0.10)]
        c.drawPath(tapered_stroke(wing, lw * 0.7, lw * 0.2), fill(hexc(OUTLINE)))


def draw_brow(c, ch, x, y, fx, side, f):
    w = ch["brow_w"] * max(0.6, fx)
    th = ch["brow_th"]
    R = ch["R"]
    inner_dir = -side  # inner end points toward the nose
    raise_ = f["braise"] * R * 0.12
    asym = f["basym"] * R * 0.15 * (1 if side > 0 else -1)
    inner_up = f["binner"] * R * 0.13
    outer_up = f["bouter"] * R * 0.09
    furrow = f["bfurrow"]
    xi = x + inner_dir * w * 0.5 - inner_dir * furrow * w * 0.12 * -1
    xi = x + inner_dir * (w * 0.5 - furrow * w * 0.10)
    xo = x - inner_dir * w * 0.5
    yi = y - raise_ - inner_up + furrow * R * 0.05 - asym
    yo = y - raise_ * 0.8 - outer_up + R * 0.02 - asym
    ym = y - raise_ * 0.95 - R * 0.035 - 0.5 * (inner_up + outer_up) - asym + furrow * R * 0.02
    pts = quad_pts((xi, yi), (xo, yo), (x, 2 * ym - 0.5 * (yi + yo)), 14)
    c.drawPath(tapered_stroke([tuple(q) for q in pts], th * 1.25, th * 0.55, th * 1.15), fill(hexc(ch["hair_sh"])))


def draw_mouth(c, ch, x, y, fx, f):
    R = ch["R"]
    op = clamp(f["mopen"], 0, 1.2)
    rnd = clamp(f["mround"], 0, 1)
    smile = f["msmile"]
    hw = ch["mouth_w"] * 0.5 * f["mwide"] * max(0.62, fx) * (1 - 0.42 * rnd)
    asym = f["masym"] * R * 0.04
    lift = smile * R * 0.055
    xl, xr = x - hw, x + hw
    yl = y - lift + asym
    yr = y - lift - asym
    line = hexc(ch["lip"])
    if op < 0.06:
        sag = smile * R * 0.06
        pts = quad_pts((xl, yl), (xr, yr), (x, y + sag), 16)
        lw = R * 0.032
        c.drawPath(tapered_stroke([tuple(q) for q in pts], lw * 0.55, lw * 0.55, lw), fill(line))
        if smile > 0.45:
            for (px, py, d) in ((xl, yl, -1), (xr, yr, 1)):
                dp = quad_pts((px + d * R * 0.01, py + R * 0.025), (px + d * R * 0.03, py - R * 0.03),
                              (px + d * R * 0.045, py), 8)
                c.drawPath(smooth_path([tuple(q) for q in dp], False),
                           stroke(hexc(ch["skin_sh"], 0.8 * (smile - 0.45) * 2), R * 0.018))
        if smile < -0.3:
            # pout / tension under the lip
            dp = quad_pts((x - hw * 0.4, y + R * 0.07), (x + hw * 0.4, y + R * 0.07), (x, y + R * 0.05), 8)
            c.drawPath(smooth_path([tuple(q) for q in dp], False), stroke(hexc(ch["skin_sh"], 0.45), R * 0.016))
        return
    oh = op * R * 0.37
    up_ctrl = (x, y - oh * 0.18 - lift * 0.2)
    lo_ctrl = (x, y + oh * 1.25 - lift * 0.3)
    up = quad_pts((xl, yl), (xr, yr), up_ctrl, 18)
    lo = quad_pts((xr, yr), (xl, yl), lo_ctrl, 18)
    pts = np.concatenate([up, lo[1:-1]], 0)
    if rnd > 0:
        t = np.linspace(0, 2 * np.pi, len(pts), endpoint=False)
        ex = x + np.cos(np.pi - t) * hw
        ey = y + oh * 0.5 - np.sin(np.pi - t) * oh * 0.62 * -1
        ell = np.stack([ex, ey], 1)
        # reorder ellipse to start at left corner going along the top
        pts = pts * (1 - rnd * 0.8) + ell * (rnd * 0.8)
    mp = smooth_path([tuple(q) for q in pts], True, 0.35)
    c.drawPath(mp, fill(hexc("#4a1c24")))
    c.save()
    c.clipPath(mp, skia.ClipOp.kIntersect, True)
    teeth = clamp(f["mteeth"], 0, 1)
    if teeth > 0.02:
        ty = y - oh * 0.35
        tb = y + oh * (0.10 + 0.22 * teeth)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - hw * 1.1, ty - oh, x + hw * 1.1, tb), oh * 0.2, oh * 0.2),
                    fill(hexc("#fbf6ee")))
    tg = clamp(f["mtongue"], 0, 1)
    if tg > 0.02:
        c.drawOval(skia.Rect.MakeLTRB(x - hw * 0.75, y + oh * (1.05 - 0.45 * tg), x + hw * 0.75, y + oh * 1.6),
                   fill(hexc("#d1626b")))
    c.restore()
    c.drawPath(mp, stroke(line, R * 0.026))


def draw_nose(c, ch, x, y, fx, f):
    R = ch["R"]
    yaw = f["yaw"]
    sd = 1 if yaw >= 0 else -1  # nose shadow on the side away from the face direction
    if ch["name"] == "pip":
        pts = quad_pts((x - sd * R * 0.035, y - R * 0.035), (x + sd * R * 0.03, y + R * 0.03),
                       (x - sd * R * 0.065, y + R * 0.035), 10)
        c.drawPath(smooth_path([tuple(q) for q in pts], False), stroke(hexc(ch["skin_sh"]), R * 0.03))
        circle(c, x + sd * R * 0.015, y - R * 0.01, R * 0.018, hexc("#ffe1c8", 0.55))
    else:
        bridge = quad_pts((x - sd * R * 0.06, y - R * 0.22), (x - sd * R * 0.03, y + R * 0.02),
                          (x - sd * R * 0.075, y - R * 0.10), 10)
        c.drawPath(smooth_path([tuple(q) for q in bridge], False), stroke(hexc(ch["skin_sh"], 0.55), R * 0.022))
        pts = quad_pts((x - sd * R * 0.05, y + R * 0.01), (x + sd * R * 0.04, y + R * 0.03),
                       (x - sd * R * 0.01, y + R * 0.07), 10)
        c.drawPath(smooth_path([tuple(q) for q in pts], False), stroke(hexc(ch["skin_sh"]), R * 0.03))
        circle(c, x + sd * R * 0.02, y - R * 0.03, R * 0.02, hexc("#ffe1c8", 0.5))


# ----------------------------------------------------------------------------
# hair
# ----------------------------------------------------------------------------

def _hair_cap(R, yaw, pitch, bottom, rk=1.03, top_r=1.07, top_dy=-0.02):
    """Hair mass: projected bottom edge points + arc over the crown."""
    pts = []
    for lon, lat in bottom:
        x, y, z = proj(R, lon, lat, yaw, pitch, rk)
        pts.append((x, y))
    # arc over the top from last point back to first
    x0, y0 = pts[-1]
    x1, y1 = pts[0]
    a0 = math.atan2(y0 - top_dy * R, x0)
    a1 = math.atan2(y1 - top_dy * R, x1)
    if a1 > a0:
        a1 -= 2 * math.pi
    arc = []
    for t in np.linspace(0, 1, 24)[1:-1]:
        a = a0 + (a1 - a0) * t
        arc.append((math.cos(a) * R * top_r, top_dy * R + math.sin(a) * R * top_r))
    return pts + arc


def draw_hair_back(c, ch, f, t):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    hc = hexc(ch["hair"])
    if ch["name"] == "pip":
        # two puffy buns
        for lon in (-52, 52):
            x, y, z = proj(R, lon, 58, yaw * 0.8, pitch, 1.0)
            r = R * 0.36
            c.drawCircle(x, y - R * 0.06, r + 4, fill(hexc(OUTLINE)))
            c.drawCircle(x, y - R * 0.06, r, fill(hc))
            c.drawCircle(x + r * 0.25, y - R * 0.06 - r * 0.3, r * 0.45, fill(hexc(ch["hair_hi"], 0.55), blur=r * 0.2))
            # little curl strokes
            c.drawPath(smooth_path([(x - r * 0.5, y - R * 0.02), (x - r * 0.1, y + r * 0.1 - R * 0.06), (x + r * 0.4, y - R * 0.05)], False),
                       stroke(hexc(ch["hair_sh"], 0.6), R * 0.03))
        # short hair at the back of the neck
        back = smooth_path([(-R * 0.98, R * 0.05), (-R * 1.02, R * 0.55), (-R * 0.55, R * 0.80),
                            (R * 0.55, R * 0.80), (R * 1.02, R * 0.55), (R * 0.98, R * 0.05),
                            (0, -R * 0.3)], True, 0.5)
        c.drawPath(back, fill(hexc(OUTLINE)))
        c.save(); c.scale(0.97, 0.97)
        c.drawPath(back, fill(hexc(ch["hair_sh"])))
        c.restore()
    else:
        # long hair falling behind the shoulders
        sway = math.sin(t * 1.3) * R * 0.02
        back = smooth_path([(-R * 1.02, -R * 0.1), (-R * 1.12, R * 0.6), (-R * 1.05 + sway, R * 1.35),
                            (-R * 0.5 + sway, R * 1.55), (R * 0.5 + sway, R * 1.5), (R * 1.08 + sway, R * 1.25),
                            (R * 1.12, R * 0.55), (R * 1.0, -R * 0.1), (0, -R * 0.4)], True, 0.5)
        c.drawPath(back, fill(hexc(OUTLINE)))
        c.save(); c.translate(0, -2); c.scale(0.975, 0.98)
        c.drawPath(back, fill(hexc(ch["hair_sh"])))
        c.restore()
        # messy bun on top/back + pencil
        x, y, z = proj(R, -18, 72, yaw * 0.6, pitch, 1.0)
        bx, by = x - R * 0.05, y - R * 0.22
        # pencil (behind bun)
        ang = -0.55
        L = R * 0.95
        px0, py0 = bx - math.cos(ang) * L * 0.45, by - math.sin(ang) * L * 0.45
        px1, py1 = bx + math.cos(ang) * L * 0.55, by + math.sin(ang) * L * 0.55
        c.drawLine(px0, py0, px1, py1, stroke(hexc(OUTLINE), R * 0.11))
        c.drawLine(px0, py0, px1, py1, stroke(hexc("#f2c94c"), R * 0.075))
        c.drawLine(px0, py0, px0 + math.cos(ang) * R * 0.12, py0 + math.sin(ang) * R * 0.12, stroke(hexc("#f08a9a"), R * 0.075))
        tip = (px1 + math.cos(ang) * R * 0.08, py1 + math.sin(ang) * R * 0.08)
        c.drawLine(px1, py1, tip[0], tip[1], stroke(hexc("#e8c9a0"), R * 0.06))
        bun = smooth_path([(bx - R * 0.42, by + R * 0.08), (bx - R * 0.36, by - R * 0.25), (bx - R * 0.05, by - R * 0.40),
                           (bx + R * 0.30, by - R * 0.30), (bx + R * 0.42, by - R * 0.02), (bx + R * 0.25, by + R * 0.18),
                           (bx - R * 0.15, by + R * 0.22)], True, 0.6)
        c.drawPath(bun, stroke(hexc(OUTLINE), 7))
        c.drawPath(bun, fill(hc))
        c.drawPath(smooth_path([(bx - R * 0.25, by - R * 0.05), (bx, by - R * 0.22), (bx + R * 0.25, by - R * 0.1)], False),
                   stroke(hexc(ch["hair_hi"], 0.8), R * 0.035))
        c.drawPath(smooth_path([(bx - R * 0.1, by + R * 0.12), (bx + R * 0.15, by + R * 0.05)], False),
                   stroke(hexc(ch["hair_sh"]), R * 0.03))


def draw_hair_front(c, ch, f, t):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    hc = hexc(ch["hair"])
    if ch["name"] == "pip":
        bottom = [(-96, 2), (-84, 22), (-64, 30), (-46, 26), (-30, 36), (-12, 31), (6, 38), (24, 31),
                  (42, 35), (60, 27), (80, 20), (96, 2)]
        cap = _hair_cap(R, yaw, pitch, bottom, rk=1.03, top_r=1.06)
        cap_shadow = _hair_cap(R, yaw, pitch, [(lo, la - 7) for lo, la in bottom], rk=1.03, top_r=1.06)
    else:
        # side-swept fringe: longer on the screen-left side
        bottom = [(-98, -12), (-86, 6), (-70, 18), (-52, 24), (-34, 34), (-14, 42), (6, 48), (26, 46),
                  (46, 38), (64, 28), (82, 16), (98, -6)]
        cap = _hair_cap(R, yaw, pitch, bottom, rk=1.03, top_r=1.07)
        cap_shadow = _hair_cap(R, yaw, pitch, [(lo, la - 7) for lo, la in bottom], rk=1.03, top_r=1.07)
    return cap, cap_shadow


def paint_hair_front(c, ch, f, cap, t):
    R = ch["R"]
    p = smooth_path(cap, True, 0.45)
    c.drawPath(p, stroke(hexc(OUTLINE), 6.5))
    c.drawPath(p, fill(hexc(ch["hair"])))
    # sheen band
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    yaw = f["yaw"]
    sh = skia.Path()
    sh.addOval(skia.Rect.MakeLTRB(-R * 0.55 + yaw * R * 0.6, -R * 1.02, R * 0.85 + yaw * R * 0.6, -R * 0.55))
    c.drawPath(sh, fill(hexc(ch["hair_hi"], 0.55), blur=R * 0.08))
    # strand lines
    for k, lon in enumerate((-50, -15, 22, 55)):
        x0, y0, _ = proj(R, lon, 74, yaw, f["pitch"], 1.0)
        x1, y1, _ = proj(R, lon + 8, 40, yaw, f["pitch"], 1.03)
        c.drawPath(smooth_path([(x0, y0), ((x0 + x1) / 2 + 4, (y0 + y1) / 2), (x1, y1)], False),
                   stroke(hexc(ch["hair_sh"], 0.5), R * 0.022))
    c.restore()
    if ch["name"] == "tess":
        # curls framing the face
        for side in (-1, 1):
            x, y, z = proj(R, side * 88, -10, yaw, f["pitch"], 1.02)
            sway = math.sin(t * 1.7 + side) * R * 0.02
            pts = [(x, y - R * 0.2), (x + side * R * 0.05 + sway, y + R * 0.05), (x - side * R * 0.02 + sway, y + R * 0.3),
                   (x + side * R * 0.06 + sway, y + R * 0.5)]
            c.drawPath(smooth_path(pts, False), stroke(hexc(OUTLINE), R * 0.11))
            c.drawPath(smooth_path(pts, False), stroke(hexc(ch["hair"]), R * 0.075))


# ----------------------------------------------------------------------------
# head
# ----------------------------------------------------------------------------

def draw_head(c, ch, f, t, rim_moon=0.8, rim_warm=0.35, back=True):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    if back:
        draw_hair_back(c, ch, f, t)
    # ear on the near (screen-left) side when facing right
    for side in (-1, 1):
        ex, ey, ez = proj(R, side * 92, -8, yaw, pitch, 1.0)
        if ez > -0.15 and ((side < 0 and yaw > -0.05) or (side > 0 and yaw < 0.05)):
            er = R * 0.17
            exo = ex + side * R * 0.06
            c.drawOval(skia.Rect.MakeLTRB(exo - er * 0.8, ey - er, exo + er * 0.8, ey + er), stroke(hexc(OUTLINE), 6))
            c.drawOval(skia.Rect.MakeLTRB(exo - er * 0.8, ey - er, exo + er * 0.8, ey + er), fill(hexc(ch["skin"])))
            c.drawPath(smooth_path([(exo + side * er * 0.2, ey - er * 0.5), (exo - side * er * 0.25, ey),
                                    (exo + side * er * 0.15, ey + er * 0.5)], False),
                       stroke(hexc(ch["skin_sh"]), R * 0.035))
    head = head_outline(ch, f)
    c.drawPath(head, stroke(hexc(OUTLINE), 7))
    c.drawPath(head, fill(hexc(ch["skin"])))
    cap, cap_sh = draw_hair_front(c, ch, f, t)
    c.save()
    c.clipPath(head, skia.ClipOp.kIntersect, True)
    # broad form shadow (light from upper right)
    sh = skia.Path()
    sh.addOval(skia.Rect.MakeLTRB(-R * 2.15 - yaw * R * 0.3, -R * 0.7, R * 0.05 - yaw * R * 0.5, R * 1.6))
    c.drawPath(sh, fill(hexc(ch["skin_sh"], 0.55), blur=R * 0.18))
    # shadow from the fringe
    c.save(); c.translate(R * 0.02, R * 0.07)
    c.drawPath(smooth_path(cap_sh, True, 0.45), fill(hexc(ch["skin_sh"], 0.6), blur=R * 0.04))
    c.restore()
    # blush
    for side in (-1, 1):
        bx, by, bz = proj(R, side * 42, -30, yaw, pitch, 1.0)
        if bz > 0.1:
            b = f["blush"]
            c.drawOval(skia.Rect.MakeLTRB(bx - R * 0.17 * bz, by - R * 0.09, bx + R * 0.17 * bz, by + R * 0.09),
                       fill(hexc(ch["blush"], 0.42 * b + 0.10), blur=R * 0.07))
    # moon rim light (right edge) and warm window rim (left edge)
    if rim_moon > 0:
        c.save()
        sp = skia.Path(head)
        sp.offset(-R * 0.09, R * 0.03)
        c.clipPath(sp, skia.ClipOp.kDifference, True)
        c.drawRect(skia.Rect.MakeLTRB(-2 * R, -2 * R, 2 * R, 2 * R), fill(hexc(MOON_RIM, 0.55 * rim_moon)))
        c.restore()
    if rim_warm > 0:
        c.save()
        sp = skia.Path(head)
        sp.offset(R * 0.06, 0)
        c.clipPath(sp, skia.ClipOp.kDifference, True)
        c.drawRect(skia.Rect.MakeLTRB(-2 * R, -2 * R, 2 * R, 2 * R), fill(hexc(WARM_RIM, 0.35 * rim_warm)))
        c.restore()
    c.restore()

    # features
    for side in (-1, 1):
        lon = side * ch["eye_lon"]
        x, y, z = proj(R, lon, ch["eye_lat"], yaw, pitch, 0.98)
        fx = clamp(math.cos(math.radians(lon) + yaw), 0.35, 1.0)
        ov = f.get("eopen_l") if side < 0 else f.get("eopen_r")
        draw_eye(c, ch, x, y, fx, side, f, open_override=ov)
        bx, by, bz = proj(R, side * (ch["eye_lon"] + 1), ch["brow_lat"], yaw, pitch, 1.0)
        draw_brow(c, ch, bx, by, fx, side, f)
    nx, ny, nz = proj(R, 0, ch["nose_lat"], yaw, pitch, 1.10)
    draw_nose(c, ch, nx, ny, 1.0, f)
    mx, my, mz = proj(R, 0, ch["mouth_lat"], yaw, pitch, 1.02)
    fx = clamp(math.cos(yaw), 0.6, 1.0)
    draw_mouth(c, ch, mx, my, fx, f)
    # tear running down
    if f["tear"] > 0.01:
        side = 1
        x, y, z = proj(R, side * ch["eye_lon"], ch["eye_lat"], yaw, pitch, 0.98)
        tt = f["tear"]
        ty = y + ch["eye_h"] * 0.5 + tt * R * 0.45
        c.drawPath(smooth_path([(x + 4, y + ch["eye_h"] * 0.45), (x + 6, ty - 4)], False),
                   stroke(hexc("#d6ecff", 0.5), R * 0.035))
        circle(c, x + 6, ty, R * 0.045, hexc("#e6f4ff", 0.85))
    # fringe on top
    paint_hair_front(c, ch, f, cap, t)


# ----------------------------------------------------------------------------
# body
# ----------------------------------------------------------------------------

def _limb(c, pts, width, color, outline=True, sh_color=None):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if outline:
        c.drawPath(p, stroke(hexc(OUTLINE), width + 7))
    c.drawPath(p, stroke(hexc(color), width))
    if sh_color is not None:
        c.save()
        c.translate(-width * 0.18, width * 0.06)
        c.drawPath(p, stroke(hexc(sh_color, 0.0), width * 0.4))
        c.restore()


def arm_points(sx, sy, a1, a2, L1, L2):
    ex = sx + L1 * math.sin(a1)
    ey = sy + L1 * math.cos(a1)
    wx = ex + L2 * math.sin(a1 + a2)
    wy = ey + L2 * math.cos(a1 + a2)
    return (sx, sy), (ex, ey), (wx, wy)


def draw_hand(c, ch, wx, wy, ang, kind, r, mirror=1):
    """ang: direction of the forearm (radians, screen space)."""
    dx, dy = math.sin(ang), math.cos(ang)
    hx, hy = wx + dx * r * 0.75, wy + dy * r * 0.75
    sk = hexc(ch["skin"])
    ol = hexc(OUTLINE)
    if kind == "point":
        tipx, tipy = hx + dx * r * 1.9, hy + dy * r * 1.9
        c.drawLine(hx, hy, tipx, tipy, stroke(ol, r * 0.62 + 6))
        c.drawLine(hx, hy, tipx, tipy, stroke(sk, r * 0.62))
    if kind == "pinch":
        # thumb and index nearly touching
        px, py = -dy * mirror, dx * mirror
        for k, (ln, sp) in enumerate(((1.7, 0.55), (1.5, -0.55))):
            tx = hx + dx * r * ln + px * r * sp * 0.6
            ty = hy + dy * r * ln + py * r * sp * 0.6
            c.drawLine(hx + px * r * sp * 0.4, hy + py * r * sp * 0.4, tx, ty, stroke(ol, r * 0.5 + 6))
            c.drawLine(hx + px * r * sp * 0.4, hy + py * r * sp * 0.4, tx, ty, stroke(sk, r * 0.5))
    c.drawCircle(hx, hy, r + 3.5, fill(ol))
    c.drawCircle(hx, hy, r, fill(sk))
    if kind in ("mitten", "open"):
        # thumb bump
        px, py = -dy * mirror, dx * mirror
        tx, ty = hx + px * r * 0.75 + dx * r * 0.2, hy + py * r * 0.75 + dy * r * 0.2
        c.drawCircle(tx, ty, r * 0.42 + 3, fill(ol))
        c.drawCircle(tx, ty, r * 0.42, fill(sk))
        c.drawCircle(hx, hy, r * 0.92, fill(sk))
        # finger creases
        for k in (-0.38, 0.0, 0.38):
            bx = hx + dx * r * 0.35 - px * r * k
            by = hy + dy * r * 0.35 - py * r * k
            ex = bx + dx * r * 0.42
            ey = by + dy * r * 0.42
            c.drawLine(bx, by, ex, ey, stroke(hexc(ch["skin_sh"], 0.8), r * 0.12))
    if kind == "point":
        c.drawCircle(hx, hy, r * 0.92, fill(sk))


def draw_mug(c, x, y, s, color, tilt=0.0, steam=1.0, t=0.0, dots=True):
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(tilt))
    w, h = 34 * s, 40 * s
    body = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w / 2, -h / 2, w / 2, h / 2), 7 * s, 7 * s)
    # handle
    hp = skia.Path()
    hp.addOval(skia.Rect.MakeLTRB(w / 2 - 6 * s, -h * 0.28, w / 2 + 14 * s, h * 0.22))
    c.drawPath(hp, stroke(hexc(OUTLINE), 11 * s))
    c.drawPath(hp, stroke(hexc(color), 6 * s))
    c.drawRRect(body, stroke(hexc(OUTLINE), 6))
    c.drawRRect(body, fill(hexc(color)))
    c.save()
    c.clipRRect(body, True)
    c.drawRect(skia.Rect.MakeLTRB(-w / 2, -h / 2, -w * 0.15, h / 2), fill(hexc("#000000", 0.18)))
    if dots:
        for (dx, dy) in ((-0.2, -0.15), (0.2, 0.05), (-0.05, 0.28), (0.25, -0.3)):
            c.drawCircle(dx * w, dy * h, 3.2 * s, fill(hexc("#fff3e0", 0.9)))
    c.restore()
    # rim + cocoa
    c.drawOval(skia.Rect.MakeLTRB(-w / 2, -h / 2 - 4 * s, w / 2, -h / 2 + 4 * s), fill(hexc("#5a3020")))
    c.drawOval(skia.Rect.MakeLTRB(-w / 2, -h / 2 - 4 * s, w / 2, -h / 2 + 4 * s), stroke(hexc(OUTLINE), 3))
    c.restore()
    if steam > 0.02:
        for k in range(2):
            ph = t * 0.6 + k * 0.5
            fr = ph - math.floor(ph)
            pts = []
            for j in range(7):
                yy = y - h / 2 - 8 * s - j * 9 * s - fr * 18 * s
                xx = x + (k - 0.5) * 12 * s + math.sin(j * 0.9 + t * 2.2 + k * 2) * 5 * s
                pts.append((xx, yy))
            a = steam * 0.55 * math.sin(fr * math.pi)
            c.drawPath(smooth_path(pts, False), stroke(hexc("#ffffff", a), 3.2 * s, blur=1.5))


def ik2(sx, sy, tx, ty, L1, L2, bend=1.0):
    """Two-bone IK. Returns elbow and (possibly clamped) end point."""
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    dmin, dmax = abs(L1 - L2) + 1e-3, (L1 + L2) * 0.999
    if d > dmax:
        k = dmax / d
        tx, ty = sx + dx * k, sy + dy * k
        d = dmax
    d = max(d, dmin)
    th = math.atan2(ty - sy, tx - sx)
    a = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    ang = th - a * bend
    ex, ey = sx + L1 * math.cos(ang), sy + L1 * math.sin(ang)
    return (ex, ey), (tx, ty)


def draw_character(c, ch, f, pose, t, x, y, scale, rim_moon=0.8, rim_warm=0.35, mug_color=None,
                   overlay=None, front_overlay=None):
    """Draw a seated (or standing) character. (x, y) is the hip point on the seat.

    Limb targets in `pose` are in the character frame (hip origin, y down).
    """
    R = ch["R"]
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    lean = pose["lean"]
    slump = pose["slump"]
    breath = pose["breath"]
    shrug = pose["shrug"]
    th = ch["torso_h"] * (1 - 0.06 * slump) * (1 + 0.012 * breath)
    shh = ch["sh_half"] * (1 - 0.05 * slump)
    wh = ch["waist_half"]
    standing = pose.get("standing", False)
    hip_y = -10

    def to_char(px, py):
        cs, sn = math.cos(lean), math.sin(lean)
        return px * cs - py * sn, px * sn + py * cs

    # contact shadow
    if not standing:
        c.drawOval(skia.Rect.MakeLTRB(-wh * 1.5, -8, wh * 2.6, 22), fill(hexc("#0a0f24", 0.45), blur=10))

    legs = []
    for name, side in (("far_foot", 1), ("near_foot", -1)):
        hx = side * wh * 0.45
        fx_, fy_ = pose[name]
        K, A = ik2(hx, hip_y, fx_, fy_, ch["thigh"], ch["shin"], pose.get("knee_bend", 1.0))
        legs.append(((hx, hip_y), K, A, side))

    def draw_leg(lg):
        (hx, hy), (kx, ky), (ax, ay), side = lg
        _limb(c, [(hx, hy), (kx, ky), (ax, ay)], ch["leg_th"], ch["pants"] if side < 0 else ch["pants_sh"])
        fw, fh = ch["leg_th"] * 0.78, ch["leg_th"] * 0.5
        c.save()
        c.translate(ax + 6, ay + 2)
        c.drawOval(skia.Rect.MakeLTRB(-fw * 0.6, -fh, fw * 1.0, fh * 0.6), stroke(hexc(OUTLINE), 6))
        c.drawOval(skia.Rect.MakeLTRB(-fw * 0.6, -fh, fw * 1.0, fh * 0.6),
                   fill(hexc(ch["sock"] if side < 0 else ch["sock_sh"])))
        c.restore()

    sh_y = -th + 12 - shrug * 10
    S_far = to_char(shh * 0.78, sh_y)
    S_near = to_char(-shh * 0.78, sh_y)
    Ef, Wf = ik2(*S_far, *pose["far_hand_pos"], ch["up_arm"], ch["fore_arm"], pose.get("far_elbow", -1.0))
    En, Wn = ik2(*S_near, *pose["near_hand_pos"], ch["up_arm"], ch["fore_arm"], pose.get("near_elbow", 1.0))
    fdir = math.atan2(Wf[0] - Ef[0], Wf[1] - Ef[1])
    ndir = math.atan2(Wn[0] - En[0], Wn[1] - En[1])

    neck_top = -th - ch["neck_len"]
    hx = pose["head_dx"]
    hy = neck_top - R * 0.86 + pose["head_dy"] + shrug * 6

    def head_xf():
        c.translate(hx, hy + R * 0.86)
        c.rotate(math.degrees(f["roll"]))
        c.translate(0, -R * 0.86)

    if standing:
        for lg in legs:
            draw_leg(lg)

    c.save()
    c.rotate(math.degrees(lean))
    c.save()
    head_xf()
    draw_hair_back(c, ch, f, t)
    c.restore()
    c.restore()

    # far arm behind the torso
    if not pose.get("far_front", False):
        _limb(c, [S_far, Ef, Wf], ch["arm_th"], ch["hoodie_sh"])
        if not pose.get("far_hand_front", False):
            draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)

    c.save()
    c.rotate(math.degrees(lean))
    hood = smooth_path([(-shh * 0.62, -th + 4), (-shh * 0.55, -th - 24), (0, -th - 34), (shh * 0.55, -th - 24),
                        (shh * 0.62, -th + 4)], True, 0.5)
    c.drawPath(hood, stroke(hexc(OUTLINE), 7))
    c.drawPath(hood, fill(hexc(ch["hoodie_sh"])))
    tp = smooth_path([(-shh, -th + 22), (-shh * 0.8, -th + 2), (0, -th - 6), (shh * 0.8, -th + 2), (shh, -th + 22),
                      (wh * 1.04, -th * 0.45), (wh, -8), (wh * 0.7, 6), (0, 9), (-wh * 0.7, 6), (-wh, -8),
                      (-wh * 1.04, -th * 0.45)], True, 0.42)
    c.drawPath(tp, stroke(hexc(OUTLINE), 7))
    c.drawPath(tp, fill(hexc(ch["hoodie"])))
    c.save()
    c.clipPath(tp, skia.ClipOp.kIntersect, True)
    shp = skia.Path()
    shp.addOval(skia.Rect.MakeLTRB(-shh * 2.4, -th * 1.4, -shh * 0.15, th * 0.6))
    c.drawPath(shp, fill(hexc(ch["hoodie_sh"], 0.75), blur=18))
    if rim_moon > 0:
        sp = skia.Path(tp)
        sp.offset(-9, 2)
        c.save()
        c.clipPath(sp, skia.ClipOp.kDifference, True)
        c.drawRect(skia.Rect.MakeLTRB(-400, -600, 400, 200), fill(hexc(MOON_RIM, 0.45 * rim_moon)))
        c.restore()
    pk = smooth_path([(-wh * 0.62, -th * 0.30), (wh * 0.62, -th * 0.30), (wh * 0.72, -th * 0.06),
                      (-wh * 0.72, -th * 0.06)], True, 0.2)
    c.drawPath(pk, stroke(hexc(ch["hoodie_sh"]), 3.5))
    if ch["name"] == "tess":
        cx0, cy0 = wh * 0.1, -th * 0.62
        for k in range(3):
            c.save()
            c.translate(cx0, cy0)
            c.rotate(k * 60 + 15)
            c.drawOval(skia.Rect.MakeLTRB(-20, -7, 20, 7), stroke(hexc("#e9f6f2", 0.9), 2.6))
            c.restore()
        c.drawCircle(cx0, cy0, 4, fill(hexc("#e9f6f2")))
    else:
        for (sx_, sy_) in ((-0.5, -0.75), (0.35, -0.55), (-0.15, -0.45), (0.55, -0.85)):
            draw_star(c, sx_ * wh, sy_ * th, 5.5, hexc("#fff4c8", 0.9))
    c.restore()
    sw = math.sin(t * 2.0) * 2
    for k in (-1, 1):
        x0 = k * 12
        c.drawLine(x0, -th + 4, x0 + sw, -th + 46, stroke(hexc("#f7f1e3"), 3.2))
        c.drawCircle(x0 + sw, -th + 48, 3.2, fill(hexc("#f7f1e3")))
    nk = skia.Path()
    nk.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-ch["neck_w"] / 2, neck_top - 20, ch["neck_w"] / 2, -th + 6), 10, 10))
    c.drawPath(nk, stroke(hexc(OUTLINE), 6))
    c.drawPath(nk, fill(hexc(ch["skin_sh"])))
    c.save()
    head_xf()
    draw_head(c, ch, f, t, rim_moon, rim_warm, back=False)
    c.restore()
    c.restore()  # lean

    if not standing:
        for lg in legs:
            draw_leg(lg)

    far_mug = pose.get("far_mug")
    if far_mug:
        draw_mug(c, Wf[0] + 14, Wf[1] - 8, 1.0 if ch["name"] == "pip" else 1.15, far_mug, pose.get("mug_tilt", 0.0),
                 pose.get("steam", 1.0), t + 0.37, dots=(ch["name"] != "pip"))
    if pose.get("far_front", False):
        _limb(c, [S_far, Ef, Wf], ch["arm_th"], ch["hoodie_sh"])
        draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)
    elif pose.get("far_hand_front", False):
        # forearm peeks out in front, then the hand
        mx_, my_ = (Ef[0] * 0.35 + Wf[0] * 0.65), (Ef[1] * 0.35 + Wf[1] * 0.65)
        _limb(c, [(mx_, my_), Wf], ch["arm_th"], ch["hoodie_sh"])
        draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)

    if overlay:
        overlay(c)
    mug = pose.get("mug")
    if mug and mug_color:
        mx, my = pose.get("mug_pos", (Wn[0] + 18, Wn[1] - 6))
        draw_mug(c, mx, my, 1.0 if ch["name"] == "pip" else 1.15, mug_color, pose.get("mug_tilt", 0.0),
                 pose.get("steam", 1.0), t, dots=(ch["name"] == "pip"))
    _limb(c, [S_near, En, Wn], ch["arm_th"], ch["hoodie"])
    cdx, cdy = math.sin(ndir), math.cos(ndir)
    c.drawLine(Wn[0] - cdx * 6, Wn[1] - cdy * 6, Wn[0] - cdx * 1, Wn[1] - cdy * 1,
               stroke(hexc(ch["hoodie_sh"]), ch["arm_th"] - 2, cap="butt"))
    draw_hand(c, ch, Wn[0], Wn[1], ndir, pose["near_hand"], ch["hand_r"], mirror=1)
    if front_overlay:
        front_overlay(c)
    c.restore()


def draw_star(c, x, y, r, color, points=5, inner=0.45, rot_deg=-90):
    p = skia.Path()
    for k in range(points * 2):
        rr = r if k % 2 == 0 else r * inner
        a = math.radians(rot_deg + k * 180 / points)
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if k == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    c.drawPath(p, fill(color))
