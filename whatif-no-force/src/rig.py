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


HALE = dict(
    name="hale", R=92.0, hair_style="curls", outfit="uniform", bags=0.8, folds=0.55, scar=True,
    skin="#a8714f", skin_sh="#7d4f37", skin_lid="#98653f", blush="#c45f55", lip="#6a3a33",
    hair="#2b201d", hair_hi="#a29f9b", hair_sh="#1a1311",
    iris="#6a4528", iris_dk="#3a2414",
    hoodie="#2c3a5c", hoodie_sh="#1f2944", hoodie_hi="#4a5c8a",
    pants="#26314f", pants_sh="#1b2440", sock="#1d1d24", sock_sh="#121216",
    eye_lon=28.0, eye_lat=-7.0, eye_w=35.0, eye_h=33.0, iris_r=0.43,
    brow_lat=19.0, brow_w=33.0, brow_th=8.2,
    nose_lat=-26.0, mouth_lat=-48.0, mouth_w=41.0,
    chin_y=1.07, cheek_out=1.0,
    neck_len=22.0, neck_w=33.0, torso_h=178.0, sh_half=76.0, waist_half=64.0,
    up_arm=98.0, fore_arm=90.0, arm_th=35.0, hand_r=15.5,
    thigh=122.0, shin=116.0, leg_th=40.0,
)

KAI = dict(
    name="kai", R=90.0, hair_style="twists", outfit="apron", sleeves_up=True, earring=True,
    skin="#7a4a32", skin_sh="#583322", skin_lid="#6c412c", blush="#a3493f", lip="#5a2e26",
    hair="#1b1412", hair_hi="#4a3a32", hair_sh="#0f0b0a",
    iris="#4a2c18", iris_dk="#24140b",
    hoodie="#8e939b", hoodie_sh="#6c717a", hoodie_hi="#b3b8c0",
    apron="#2e5a4c", apron_sh="#22443a",
    pants="#2a2a30", pants_sh="#1e1e24", sock="#e9e6e0", sock_sh="#b9b5ad",
    eye_lon=28.0, eye_lat=-6.0, eye_w=34.0, eye_h=34.0, iris_r=0.44,
    brow_lat=20.0, brow_w=32.0, brow_th=8.0,
    nose_lat=-26.0, mouth_lat=-48.0, mouth_w=40.0,
    chin_y=1.08, cheek_out=0.98,
    neck_len=27.0, neck_w=30.0, torso_h=190.0, sh_half=72.0, waist_half=58.0,
    up_arm=102.0, fore_arm=94.0, arm_th=31.0, hand_r=15.0,
    thigh=126.0, shin=120.0, leg_th=38.0,
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

def _hair_cap(R, yaw, pitch, bottom, rk=1.03, top_r=1.07, top_dy=-0.02, bump=0.0, freq=0.0):
    """Hair mass: projected bottom edge points + arc over the crown (optionally scalloped)."""
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
        rr = R * top_r * (1 + bump * abs(math.sin(freq * a)))
        arc.append((math.cos(a) * rr, top_dy * R + math.sin(a) * rr))
    return pts + arc


def _bumpy_dome(R, cx, cy, rr, a0, a1, n, bump, freq, phase=0.0):
    pts = []
    for k in range(n):
        a = a0 + (a1 - a0) * k / (n - 1)
        r = rr * (1 + bump * math.sin(freq * a + phase))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_hair_back(c, ch, f, t):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    hc = hexc(ch["hair"])
    style = ch.get("hair_style")
    if style == "curls":
        # short natural curls with volume: a scalloped mass wider than the head
        dome = []
        for k in range(56):
            a = math.radians(150) + math.radians(240) * k / 55
            r = R * 1.22 * (1 + 0.045 * abs(math.sin(9.5 * a)))
            dome.append((-yaw * R * 0.08 + math.cos(a) * r * 1.02, -R * 0.14 + math.sin(a) * r * 0.97))
        pts = [(-R * 1.0, R * 0.36)] + dome + [(R * 1.0, R * 0.36), (0, R * 0.5)]
        p = smooth_path(pts, True, 0.35)
        c.drawPath(p, stroke(hexc(OUTLINE), 7))
        c.drawPath(p, fill(hexc(ch["hair_sh"])))
        return
    if style == "twists":
        # faded sides: a close dark layer just outside the head silhouette
        dome = _bumpy_dome(R, 0, -R * 0.02, R * 1.035, math.radians(165), math.radians(375), 30, 0.0, 1)
        pts = [(-R * 0.97, R * 0.30)] + dome + [(R * 0.97, R * 0.30), (0, R * 0.42)]
        p = smooth_path(pts, True, 0.35)
        c.drawPath(p, stroke(hexc(OUTLINE), 6))
        c.drawPath(p, fill(hexc(ch["hair_sh"])))
        return
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
    style = ch.get("hair_style")
    if style == "curls":
        # hairline at the temples, curls piled with volume on top
        bottom = [(-102, -4), (-92, 16), (-80, 28), (-64, 36), (-46, 41), (-28, 44), (-10, 46), (8, 46), (26, 44),
                  (44, 41), (62, 36), (78, 28), (92, 16), (102, -4)]
        cap = _hair_cap(R, yaw, pitch, bottom, rk=1.05, top_r=1.22, top_dy=-0.13, bump=0.045, freq=9.5)
        cap_shadow = _hair_cap(R, yaw, pitch, [(lo, la - 5) for lo, la in bottom], rk=1.05, top_r=1.22, top_dy=-0.13,
                               bump=0.045, freq=9.5)
        return cap, cap_shadow
    if style == "twists":
        # crisp line-up hairline, short faded hair under the twists
        bottom = [(-100, -8), (-92, 10), (-82, 26), (-70, 36), (-50, 44), (-26, 48), (0, 49), (26, 48), (50, 44),
                  (70, 36), (82, 26), (92, 10), (100, -8)]
        cap = _hair_cap(R, yaw, pitch, bottom, rk=1.025, top_r=1.04, top_dy=-0.02)
        cap_shadow = _hair_cap(R, yaw, pitch, [(lo, la - 4) for lo, la in bottom], rk=1.025, top_r=1.04, top_dy=-0.02)
        return cap, cap_shadow
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


def _paint_curls(c, ch, f, cap, t):
    R = ch["R"]
    yaw = f["yaw"]
    p = smooth_path(cap, True, 0.45)
    c.drawPath(p, stroke(hexc(OUTLINE), 6.5))
    c.drawPath(p, fill(hexc(ch["hair"])))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    # soft top light on the curl mass
    hl = skia.Path()
    hl.addOval(skia.Rect.MakeLTRB(-R * 0.75 + yaw * R * 0.5, -R * 1.42, R * 0.6 + yaw * R * 0.5, -R * 0.78))
    c.drawPath(hl, fill(hexc("#6a5650", 0.35), blur=R * 0.1))
    rng = np.random.default_rng(5)
    for k in range(120):
        lon = rng.uniform(-100, 100)
        lat = rng.uniform(44, 96)
        x, y, z = proj(R, lon, lat, yaw, f["pitch"], 1.12)
        y -= R * 0.1 * (lat - 44) / 52
        if z < -0.25:
            continue
        rr = R * rng.uniform(0.045, 0.075)
        grey = (abs(lon) > 62 and lat < 66 and rng.uniform() < 0.8) or rng.uniform() < 0.07
        col = "#8a8481" if grey else "#45362f"
        a0 = rng.uniform(0, 360)
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeLTRB(x - rr, y - rr, x + rr, y + rr), a0, 230)
        c.drawPath(arc, stroke(hexc(col, 0.5 if grey else 0.55), R * 0.02))
    c.restore()


def _paint_twists(c, ch, f, cap, t):
    R = ch["R"]
    yaw, pitch = f["yaw"], f["pitch"]
    p = smooth_path(cap, True, 0.45)
    c.drawPath(p, stroke(hexc(OUTLINE), 6))
    c.drawPath(p, fill(hexc(ch["hair_sh"])))
    # twists rising from the crown, back row first
    rng = np.random.default_rng(9)
    twists = []
    for row, (lat, n) in enumerate(((84, 5), (74, 7), (64, 8), (55, 7))):
        for k in range(n):
            lon = -78 + 156 * (k + 0.5) / n + rng.uniform(-5, 5)
            twists.append((row, lon, lat + rng.uniform(-3, 3), rng.uniform(0.30, 0.42)))
    for row, lon, lat, ln in twists:
        x0, y0, z0 = proj(R, lon, lat, yaw, pitch, 1.02)
        if z0 < -0.35:
            continue
        nx, ny = x0 / R, (y0 + R * 0.05) / R
        nrm = math.hypot(nx, ny) + 1e-6
        dx, dy = nx / nrm, ny / nrm
        sway = math.sin(t * 1.1 + lon * 0.1) * 0.03
        x1 = x0 + (dx * 0.55 + sway) * R * ln
        y1 = y0 + (dy * 0.9 - 0.35) * R * ln
        w = R * 0.085
        c.drawLine(x0, y0, x1, y1, stroke(hexc(OUTLINE), w + 5))
        c.drawLine(x0, y0, x1, y1, stroke(hexc(ch["hair"]), w))
        # twist ridges
        for j in range(1, 4):
            u = j / 4.0
            mx, my = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            px, py = -(y1 - y0), (x1 - x0)
            pl = math.hypot(px, py) + 1e-6
            px, py = px / pl * w * 0.38, py / pl * w * 0.38
            c.drawLine(mx - px, my - py + 2, mx + px, my + py - 2, stroke(hexc(ch["hair_hi"], 0.7), R * 0.016))


def paint_hair_front(c, ch, f, cap, t):
    style = ch.get("hair_style")
    if style == "curls":
        return _paint_curls(c, ch, f, cap, t)
    if style == "twists":
        return _paint_twists(c, ch, f, cap, t)
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
            if ch.get("earring"):
                circle(c, exo, ey + er * 0.82, R * 0.035, hexc("#2a2a2e"))
                circle(c, exo, ey + er * 0.82, R * 0.025, hexc("#dfe3ea"))
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
    # age lines and details
    if ch.get("bags", 0) > 0:
        for side in (-1, 1):
            lon = side * ch["eye_lon"]
            x, y, z = proj(R, lon, ch["eye_lat"], yaw, pitch, 0.98)
            fx = clamp(math.cos(math.radians(lon) + yaw), 0.35, 1.0)
            w = ch["eye_w"] * fx
            yb = y + ch["eye_h"] * 0.66
            pts = quad_pts((x - w * 0.42, yb - 2), (x + w * 0.42, yb - 2), (x, yb + ch["eye_h"] * 0.16), 10)
            c.drawPath(smooth_path([tuple(q) for q in pts], False), stroke(hexc(ch["skin_sh"], 0.55 * ch["bags"]), R * 0.02))
    if ch.get("folds", 0) > 0:
        nx_, ny_, _ = proj(R, 0, ch["nose_lat"], yaw, pitch, 1.1)
        mx_, my_, _ = proj(R, 0, ch["mouth_lat"], yaw, pitch, 1.02)
        for side in (-1, 1):
            a = (nx_ + side * R * 0.13 * max(0.5, math.cos(yaw + side * 0.4)), ny_ + R * 0.02)
            b = (mx_ + side * R * 0.22 * max(0.5, math.cos(yaw + side * 0.4)), my_ + R * 0.05)
            cc = (0.5 * (a[0] + b[0]) + side * R * 0.05, 0.5 * (a[1] + b[1]))
            pts = quad_pts(a, b, cc, 10)
            c.drawPath(smooth_path([tuple(q) for q in pts], False),
                       stroke(hexc(ch["skin_sh"], 0.38 * ch["folds"] * (1 + 0.6 * max(0, f.get("msmile", 0)))), R * 0.02))
    if ch.get("scar"):
        bx, by, bz = proj(R, -(ch["eye_lon"] + 1), ch["brow_lat"], yaw, pitch, 1.0)
        if bz > 0.2:
            c.drawLine(bx - R * 0.02, by - R * 0.09, bx + R * 0.05, by + R * 0.05, stroke(hexc(ch["skin"]), R * 0.035))
            c.drawLine(bx - R * 0.02, by - R * 0.09, bx + R * 0.05, by + R * 0.05, stroke(hexc("#d9a585", 0.7), R * 0.012))
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


def _forearm(c, ch, E, W, w0, w1, color, start=0.0):
    """Bare forearm: tapers toward the wrist, with a soft muscle highlight (reads less like a tube)."""
    ex, ey = E[0] + (W[0] - E[0]) * start, E[1] + (W[1] - E[1]) * start
    w0 = w0 + (w1 - w0) * start
    dx, dy = W[0] - ex, W[1] - ey
    ln = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    p = skia.Path()
    p.moveTo(ex + nx * w0 / 2, ey + ny * w0 / 2)
    p.cubicTo(ex + ux * ln * 0.35 + nx * w0 * 0.56, ey + uy * ln * 0.35 + ny * w0 * 0.56,
              W[0] - ux * ln * 0.3 + nx * w1 * 0.5, W[1] - uy * ln * 0.3 + ny * w1 * 0.5,
              W[0] + nx * w1 / 2, W[1] + ny * w1 / 2)
    p.lineTo(W[0] - nx * w1 / 2, W[1] - ny * w1 / 2)
    p.cubicTo(W[0] - ux * ln * 0.3 - nx * w1 * 0.5, W[1] - uy * ln * 0.3 - ny * w1 * 0.5,
              ex + ux * ln * 0.35 - nx * w0 * 0.52, ey + uy * ln * 0.35 - ny * w0 * 0.52,
              ex - nx * w0 / 2, ey - ny * w0 / 2)
    p.close()
    c.drawPath(p, stroke(hexc(OUTLINE), 7))
    if start <= 0.0:
        c.drawCircle(ex, ey, w0 / 2 + 3.5, fill(hexc(OUTLINE)))
        c.drawCircle(ex, ey, w0 / 2, fill(hexc(color)))
    c.drawPath(p, fill(hexc(color)))
    # shadow along one side, highlight along the other
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    c.drawLine(ex - nx * w0 * 0.42, ey - ny * w0 * 0.42, W[0] - nx * w1 * 0.42, W[1] - ny * w1 * 0.42,
               stroke(hexc(ch["skin_sh"], 0.55), w0 * 0.32))
    c.drawLine(ex + ux * ln * 0.15 + nx * w0 * 0.2, ey + uy * ln * 0.15 + ny * w0 * 0.2,
               ex + ux * ln * 0.55 + nx * w0 * 0.18, ey + uy * ln * 0.55 + ny * w0 * 0.18,
               stroke(hexc("#ffffff", 0.10), w0 * 0.16))
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
    px, py = -dy * mirror, dx * mirror
    if kind == "point":
        tipx, tipy = hx + dx * r * 1.9, hy + dy * r * 1.9
        c.drawLine(hx, hy, tipx, tipy, stroke(ol, r * 0.62 + 6))
        c.drawLine(hx, hy, tipx, tipy, stroke(sk, r * 0.62))
    if kind == "pinch":
        for k, (ln, sp) in enumerate(((1.7, 0.55), (1.5, -0.55))):
            tx = hx + dx * r * ln + px * r * sp * 0.6
            ty = hy + dy * r * ln + py * r * sp * 0.6
            c.drawLine(hx + px * r * sp * 0.4, hy + py * r * sp * 0.4, tx, ty, stroke(ol, r * 0.5 + 6))
            c.drawLine(hx + px * r * sp * 0.4, hy + py * r * sp * 0.4, tx, ty, stroke(sk, r * 0.5))
    if kind == "pencil":
        # pencil held like a writer: points down/forward to the page
        a2 = ang + 0.9 * mirror
        ex, ey = hx + math.sin(a2) * r * 2.6, hy + math.cos(a2) * r * 2.6
        bx_, by_ = hx - math.sin(a2) * r * 0.9, hy - math.cos(a2) * r * 0.9
        c.drawLine(bx_, by_, ex, ey, stroke(ol, r * 0.42 + 4))
        c.drawLine(bx_, by_, ex, ey, stroke(hexc("#f2c94c"), r * 0.42))
        c.drawLine(ex - math.sin(a2) * r * 0.45, ey - math.cos(a2) * r * 0.45, ex, ey, stroke(hexc("#e8c9a0"), r * 0.3))
        c.drawCircle(ex, ey, r * 0.08, fill(hexc("#333333")))
    if kind == "fist":
        # chunky fist: knuckles forward
        c.drawCircle(hx + dx * r * 0.15, hy + dy * r * 0.15, r * 1.12 + 3.5, fill(ol))
        c.drawCircle(hx + dx * r * 0.15, hy + dy * r * 0.15, r * 1.12, fill(sk))
        for k in (-0.55, -0.18, 0.18, 0.55):
            kx = hx + dx * r * 0.85 + px * r * k
            ky = hy + dy * r * 0.85 + py * r * k
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeLTRB(kx - r * 0.22, ky - r * 0.22, kx + r * 0.22, ky + r * 0.22),
                       math.degrees(math.atan2(dy, dx)) - 70, 140)
            c.drawPath(arc, stroke(hexc(ch["skin_sh"], 0.9), r * 0.1))
        # thumb wrapped across
        c.drawLine(hx + px * r * 0.55 - dx * r * 0.1, hy + py * r * 0.55 - dy * r * 0.1,
                   hx + dx * r * 0.45 + px * r * 0.1, hy + dy * r * 0.45 + py * r * 0.1, stroke(hexc(ch["skin_sh"]), r * 0.16))
        return
    c.drawCircle(hx, hy, r + 3.5, fill(ol))
    c.drawCircle(hx, hy, r, fill(sk))
    if kind in ("mitten", "open", "pencil"):
        tx, ty = hx + px * r * 0.75 + dx * r * 0.2, hy + py * r * 0.75 + dy * r * 0.2
        c.drawCircle(tx, ty, r * 0.42 + 3, fill(ol))
        c.drawCircle(tx, ty, r * 0.42, fill(sk))
        c.drawCircle(hx, hy, r * 0.92, fill(sk))
        for k in (-0.38, 0.0, 0.38):
            bx = hx + dx * r * 0.35 - px * r * k
            by = hy + dy * r * 0.35 - py * r * k
            ex = bx + dx * r * 0.42
            ey = by + dy * r * 0.42
            c.drawLine(bx, by, ex, ey, stroke(hexc(ch["skin_sh"], 0.8), r * 0.12))
    if kind == "open":
        # spread fingers a little for an open, offering hand
        for k in (-0.6, -0.2, 0.2, 0.6):
            bx = hx + dx * r * 0.6 - px * r * k
            by = hy + dy * r * 0.6 - py * r * k
            ex = bx + dx * r * 0.55 - px * r * k * 0.35
            ey = by + dy * r * 0.55 - py * r * k * 0.35
            c.drawLine(bx, by, ex, ey, stroke(ol, r * 0.36 + 4))
            c.drawLine(bx, by, ex, ey, stroke(sk, r * 0.36))
    if kind == "point":
        c.drawCircle(hx, hy, r * 0.92, fill(sk))


def draw_pot(c, x, y, s, tilt=0.0, fill_level=0.45):
    """Diner coffee carafe held at its handle (x, y = handle grip)."""
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(tilt))
    ol = hexc(OUTLINE)
    # bulb
    body = skia.Path()
    body.addOval(skia.Rect.MakeLTRB(14 * s, -10 * s, 74 * s, 50 * s))
    neck = skia.Path()
    neck.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(26 * s, -30 * s, 62 * s, -2 * s), 6 * s, 6 * s))
    for p in (body, neck):
        c.drawPath(p, stroke(ol, 6))
    c.drawPath(body, fill(hexc("#cfe3ea", 0.55)))
    c.drawPath(neck, fill(hexc("#cfe3ea", 0.45)))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(0, 50 * s - 60 * s * fill_level, 90 * s, 60 * s), fill(hexc("#4a2a1a", 0.95)))
    c.restore()
    c.drawOval(skia.Rect.MakeLTRB(22 * s, 0, 40 * s, 22 * s), fill(hexc("#ffffff", 0.45)))
    # black lid + handle
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(22 * s, -40 * s, 66 * s, -26 * s), 5 * s, 5 * s), fill(hexc("#1f1f24")))
    hp = skia.Path()
    hp.moveTo(24 * s, -30 * s)
    hp.cubicTo(-12 * s, -30 * s, -14 * s, 22 * s, 18 * s, 24 * s)
    c.drawPath(hp, stroke(ol, 14 * s))
    c.drawPath(hp, stroke(hexc("#2a2a30"), 9 * s))
    c.restore()


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


def _name_tag(c, x, y, text, mirrored, w=46, h=14, bg="#e9e4d8", fg="#24161c"):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - w / 2, y - h / 2, x + w / 2, y + h / 2), 3, 3), fill(hexc(bg)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - w / 2, y - h / 2, x + w / 2, y + h / 2), 3, 3),
                stroke(hexc(OUTLINE, 0.8), 2))
    from gfx import font as _font
    f_ = _font(11, "bold")
    tw = f_.measureText(text)
    c.save()
    if mirrored:
        c.translate(x, 0)
        c.scale(-1, 1)
        c.translate(-x, 0)
    c.drawString(text, x - tw / 2, y + 4, f_, fill(hexc(fg)))
    c.restore()


def _torso_path(shh, wh, th):
    return smooth_path([(-shh, -th + 22), (-shh * 0.8, -th + 2), (0, -th - 6), (shh * 0.8, -th + 2), (shh, -th + 22),
                        (wh * 1.04, -th * 0.45), (wh, -8), (wh * 0.7, 6), (0, 9), (-wh * 0.7, 6), (-wh, -8),
                        (-wh * 1.04, -th * 0.45)], True, 0.42)


def _draw_torso(c, ch, shh, wh, th, t, rim_moon, mirrored):
    outfit = ch.get("outfit", "hoodie")
    if outfit in ("hoodie", "apron"):
        hood = smooth_path([(-shh * 0.62, -th + 4), (-shh * 0.55, -th - 24), (0, -th - 34), (shh * 0.55, -th - 24),
                            (shh * 0.62, -th + 4)], True, 0.5)
        c.drawPath(hood, stroke(hexc(OUTLINE), 7))
        c.drawPath(hood, fill(hexc(ch["hoodie_sh"])))
    tp = _torso_path(shh, wh, th)
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
    if outfit == "hoodie":
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
    elif outfit == "uniform":
        # button placket, pocket flaps, badge, name tag, epaulettes
        c.drawLine(4, -th + 8, 2, 0, stroke(hexc(ch["hoodie_sh"]), 3))
        for k in range(4):
            c.drawCircle(10, -th + 40 + k * 38, 3.4, fill(hexc("#c9ccd6")))
        for side in (-1, 1):
            fx0 = side * wh * 0.55
            flap = smooth_path([(fx0 - 26, -th * 0.70), (fx0 + 26, -th * 0.70), (fx0 + 24, -th * 0.62), (fx0, -th * 0.58),
                                (fx0 - 24, -th * 0.62)], True, 0.2)
            c.drawPath(flap, fill(hexc(ch["hoodie_sh"])))
            c.drawPath(flap, stroke(hexc(OUTLINE, 0.6), 2))
        # badge on the far (screen-right) chest
        bx, by = wh * 0.56, -th * 0.80
        badge = smooth_path([(bx - 16, by - 16), (bx, by - 22), (bx + 16, by - 16), (bx + 14, by + 6), (bx, by + 20),
                             (bx - 14, by + 6)], True, 0.25)
        c.drawPath(badge, stroke(hexc(OUTLINE), 4))
        c.drawPath(badge, fill(hexc("#d6b04c")))
        c.drawCircle(bx, by - 1, 7, fill(hexc("#f1d67e")))
        c.drawCircle(bx, by - 1, 7, stroke(hexc("#9c7a26"), 2))
        _name_tag(c, -wh * 0.55, -th * 0.80, ch["name"].upper(), mirrored, w=50, h=15, bg="#d8dbe2")
        # epaulettes
        for side in (-1, 1):
            c.drawLine(side * shh * 0.45, -th + 4, side * shh * 0.92, -th + 20, stroke(hexc(ch["hoodie_sh"]), 9))
    elif outfit == "apron":
        # hoodie body with a bib apron on top
        bib = smooth_path([(-wh * 0.62, -th * 0.80), (wh * 0.62, -th * 0.80), (wh * 0.70, -th * 0.40), (wh * 0.86, -th * 0.30),
                           (wh * 0.90, 30), (-wh * 0.90, 30), (-wh * 0.86, -th * 0.30), (-wh * 0.70, -th * 0.40)], True, 0.15)
        c.drawPath(bib, stroke(hexc(OUTLINE), 5))
        c.drawPath(bib, fill(hexc(ch["apron"])))
        c.save()
        c.clipPath(bib, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeLTRB(-400, -600, -wh * 0.2, 200), fill(hexc(ch["apron_sh"], 0.6)))
        c.restore()
        # neck straps
        for side in (-1, 1):
            c.drawLine(side * wh * 0.55, -th * 0.80, side * 16, -th - 2, stroke(hexc(OUTLINE), 7))
            c.drawLine(side * wh * 0.55, -th * 0.80, side * 16, -th - 2, stroke(hexc(ch["apron"]), 4))
        # front pocket with a pencil
        c.drawLine(-wh * 0.55, -th * 0.36, wh * 0.55, -th * 0.36, stroke(hexc(ch["apron_sh"]), 3))
        c.drawLine(wh * 0.30, -th * 0.36 + 2, wh * 0.40, -th * 0.50, stroke(hexc(OUTLINE), 7))
        c.drawLine(wh * 0.30, -th * 0.36 + 2, wh * 0.40, -th * 0.50, stroke(hexc("#f2c94c"), 4))
        _name_tag(c, -wh * 0.32, -th * 0.68, ch["name"].upper(), mirrored, w=40, h=14, bg="#f3efe6")
    c.restore()
    if outfit == "uniform":
        # collar points over the neckline
        for side in (-1, 1):
            col = smooth_path([(side * 4, -th - 2), (side * shh * 0.42, -th + 2), (side * shh * 0.20, -th + 30)], True, 0.0)
            c.drawPath(col, stroke(hexc(OUTLINE), 4))
            c.drawPath(col, fill(hexc(ch["hoodie_hi"])))
    else:
        sw = math.sin(t * 2.0) * 2
        for k in (-1, 1):
            x0 = k * 12
            ln = 46 if outfit == "hoodie" else 26
            c.drawLine(x0, -th + 4, x0 + sw, -th + ln, stroke(hexc("#f7f1e3"), 3.2))
            c.drawCircle(x0 + sw, -th + ln + 2, 3.2, fill(hexc("#f7f1e3")))


def _arm(c, ch, S, E, W, sleeve):
    if ch.get("sleeves_up"):
        # sleeve pushed past the elbow: cloth on the upper arm, skin on the forearm
        _forearm(c, ch, E, W, ch["arm_th"] * 0.9, ch["arm_th"] * 0.66, ch["skin"])
        _limb(c, [S, E], ch["arm_th"], sleeve)
        # rolled cuff: a short band across the arm just above the elbow
        ux, uy = E[0] - S[0], E[1] - S[1]
        ul = math.hypot(ux, uy) + 1e-6
        ux, uy = ux / ul, uy / ul
        cx_, cy_ = E[0] - ux * ch["arm_th"] * 0.35, E[1] - uy * ch["arm_th"] * 0.35
        a_ = (cx_ - ux * ch["arm_th"] * 0.22, cy_ - uy * ch["arm_th"] * 0.22)
        b_ = (cx_ + ux * ch["arm_th"] * 0.22, cy_ + uy * ch["arm_th"] * 0.22)
        c.drawLine(*a_, *b_, stroke(hexc(OUTLINE), ch["arm_th"] * 1.18 + 5, cap="butt"))
        c.drawLine(*a_, *b_, stroke(hexc(ch["hoodie_hi"]), ch["arm_th"] * 1.18, cap="butt"))
    else:
        _limb(c, [S, E, W], ch["arm_th"], sleeve)


def draw_character(c, ch, f, pose, t, x, y, scale, rim_moon=0.8, rim_warm=0.35, mug_color=None,
                   overlay=None, front_overlay=None, parts=("body", "arms"), mirror=False):
    """Draw a seated (or standing) character. (x, y) is the hip point on the seat.

    Limb targets in `pose` are in the character frame (hip origin, y down).
    parts: "body" draws everything except arms/hands/held props; "arms" draws only those
    (used to put forearms on top of a table). mirror=True faces the character left.
    """
    R = ch["R"]
    c.save()
    c.translate(x, y)
    if mirror:
        c.scale(-scale, scale)
    else:
        c.scale(scale, scale)
    do_body = "body" in parts
    do_arms = "arms" in parts
    lean = pose["lean"]
    slump = pose["slump"]
    breath = pose["breath"]
    shrug = pose["shrug"]
    th = ch["torso_h"] * (1 - 0.06 * slump) * (1 + 0.012 * breath)
    shh = ch["sh_half"] * (1 - 0.05 * slump)
    wh = ch["waist_half"]
    standing = pose.get("standing", False)
    hide_legs = pose.get("hide_legs", False)
    hip_y = -10

    def to_char(px, py):
        cs, sn = math.cos(lean), math.sin(lean)
        return px * cs - py * sn, px * sn + py * cs

    if do_body and not standing and not hide_legs:
        c.drawOval(skia.Rect.MakeLTRB(-wh * 1.5, -8, wh * 2.6, 22), fill(hexc("#0a0f24", 0.45), blur=10))

    legs = []
    for name, side in (("far_foot", 1), ("near_foot", -1)):
        hx_ = side * wh * 0.45
        fx_, fy_ = pose[name]
        K, A = ik2(hx_, hip_y, fx_, fy_, ch["thigh"], ch["shin"], pose.get("knee_bend", 1.0))
        legs.append(((hx_, hip_y), K, A, side))

    def draw_leg(lg):
        (hx_, hy_), (kx, ky), (ax, ay), side = lg
        _limb(c, [(hx_, hy_), (kx, ky), (ax, ay)], ch["leg_th"], ch["pants"] if side < 0 else ch["pants_sh"])
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

    if do_body:
        if standing and not hide_legs:
            for lg in legs:
                draw_leg(lg)
        c.save()
        c.rotate(math.degrees(lean))
        c.save()
        head_xf()
        draw_hair_back(c, ch, f, t)
        c.restore()
        c.restore()
        if not do_arms or not pose.get("arms_on_table", True):
            pass
        # far arm behind the torso (its hand may come forward again in the arms pass)
        if not pose.get("far_front", False):
            _arm(c, ch, S_far, Ef, Wf, ch["hoodie_sh"])
            if not pose.get("far_hand_front", False):
                draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)
        c.save()
        c.rotate(math.degrees(lean))
        _draw_torso(c, ch, shh, wh, th, t, rim_moon, mirror)
        nk = skia.Path()
        nk.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-ch["neck_w"] / 2, neck_top - 20, ch["neck_w"] / 2, -th + 6), 10, 10))
        c.drawPath(nk, stroke(hexc(OUTLINE), 6))
        c.drawPath(nk, fill(hexc(ch["skin_sh"])))
        if ch.get("outfit") == "uniform":
            for side in (-1, 1):
                col = smooth_path([(side * 4, -th - 2), (side * shh * 0.42, -th + 2), (side * shh * 0.20, -th + 30)], True, 0.0)
                c.drawPath(col, stroke(hexc(OUTLINE), 4))
                c.drawPath(col, fill(hexc(ch["hoodie_hi"])))
        c.save()
        head_xf()
        draw_head(c, ch, f, t, rim_moon, rim_warm, back=False)
        c.restore()
        c.restore()  # lean
        if not standing and not hide_legs:
            for lg in legs:
                draw_leg(lg)

    if do_arms:
        if pose.get("far_front", False):
            _arm(c, ch, S_far, Ef, Wf, ch["hoodie_sh"])
            if pose.get("far_mug"):
                draw_mug(c, Wf[0] + 14, Wf[1] - 8, 1.15, pose["far_mug"], pose.get("mug_tilt", 0.0),
                         pose.get("steam", 1.0), t + 0.37, dots=False)
            draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)
        elif pose.get("far_hand_front", False):
            mx_, my_ = (Ef[0] * 0.35 + Wf[0] * 0.65), (Ef[1] * 0.35 + Wf[1] * 0.65)
            if ch.get("sleeves_up"):
                _forearm(c, ch, Ef, Wf, ch["arm_th"] * 0.9, ch["arm_th"] * 0.66, ch["skin"], start=0.35)
            else:
                _limb(c, [(mx_, my_), Wf], ch["arm_th"], ch["hoodie_sh"])
            draw_hand(c, ch, Wf[0], Wf[1], fdir, pose["far_hand"], ch["hand_r"], mirror=-1)
        if overlay:
            overlay(c)
        mug = pose.get("mug")
        if mug and mug_color:
            mx, my = pose.get("mug_pos", (Wn[0] + 18, Wn[1] - 6))
            draw_mug(c, mx, my, 1.15, mug_color, pose.get("mug_tilt", 0.0), pose.get("steam", 1.0), t, dots=False)
        _arm(c, ch, S_near, En, Wn, ch["hoodie"])
        if not ch.get("sleeves_up"):
            cdx, cdy = math.sin(ndir), math.cos(ndir)
            c.drawLine(Wn[0] - cdx * 6, Wn[1] - cdy * 6, Wn[0] - cdx * 1, Wn[1] - cdy * 1,
                       stroke(hexc(ch["hoodie_sh"]), ch["arm_th"] - 2, cap="butt"))
        if pose.get("pot"):
            draw_pot(c, Wn[0] + math.sin(ndir) * 8, Wn[1] + math.cos(ndir) * 8, 1.0, pose.get("pot_tilt", 0.0))
        draw_hand(c, ch, Wn[0], Wn[1], ndir, pose["near_hand"], ch["hand_r"], mirror=1)
        if front_overlay:
            front_overlay(c)
    c.restore()


def arm_local(ch, pose, which="near"):
    """Shoulder, elbow, wrist and forearm direction in the character frame."""
    lean = pose["lean"]
    th = ch["torso_h"] * (1 - 0.06 * pose["slump"]) * (1 + 0.012 * pose["breath"])
    shh = ch["sh_half"] * (1 - 0.05 * pose["slump"])
    sh_y = -th + 12 - pose["shrug"] * 10
    cs, sn = math.cos(lean), math.sin(lean)
    sx = (shh * 0.78 if which == "far" else -shh * 0.78)
    S = (sx * cs - sh_y * sn, sx * sn + sh_y * cs)
    tgt = pose["far_hand_pos" if which == "far" else "near_hand_pos"]
    E, W = ik2(S[0], S[1], tgt[0], tgt[1], ch["up_arm"], ch["fore_arm"],
               pose.get("far_elbow" if which == "far" else "near_elbow", -1.0))
    return S, E, W, math.atan2(W[0] - E[0], W[1] - E[1])


def hand_world(ch, pose, x, y, scale, which="near", mirror=False):
    """World position of a wrist (for props/contacts drawn by the scene)."""
    lean = pose["lean"]
    th = ch["torso_h"] * (1 - 0.06 * pose["slump"]) * (1 + 0.012 * pose["breath"])
    shh = ch["sh_half"] * (1 - 0.05 * pose["slump"])
    sh_y = -th + 12 - pose["shrug"] * 10
    cs, sn = math.cos(lean), math.sin(lean)
    sx = (shh * 0.78 if which == "far" else -shh * 0.78)
    S = (sx * cs - sh_y * sn, sx * sn + sh_y * cs)
    tgt = pose["far_hand_pos" if which == "far" else "near_hand_pos"]
    E, W = ik2(S[0], S[1], tgt[0], tgt[1], ch["up_arm"], ch["fore_arm"],
               pose.get("far_elbow" if which == "far" else "near_elbow", -1.0))
    sgn = -1 if mirror else 1
    return x + sgn * W[0] * scale, y + W[1] * scale


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
