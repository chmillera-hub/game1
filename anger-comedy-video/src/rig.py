"""Parametric cartoon character rig drawn with skia.

Every character is drawn from a *design* (static look) and a *state* (dict of
animated parameters: pose, arms, eyes, lids, brows, mouth, extras).  The origin of
a character is the floor point under the hips; y grows downward like the screen.
"""
import math
import skia
from gfx import (rgb, hx, mix, shade, fill, stroke, oval, rrect, poly,
                 superellipse, lin_grad, rad_grad, hash01, noise1, font)

# --------------------------------------------------------------------------
# default animated state
# --------------------------------------------------------------------------
DEFAULTS = dict(
    x=0.0, y=0.0, s=1.0, alpha=1.0,
    stand=0.0, kneel=0.0, lying=0.0, head_lift=0.0, walk=0.0, walk_phase=0.0,
    lean=0.0, hunch=0.0, sink=0.0, bob=0.0, dx=0.0,
    head_tilt=0.0, head_turn=0.0, head_nod=0.0, head_dx=0.0,
    look_x=0.0, look_y=0.0,
    brow_y=0.0, brow_tilt=0.0, brow_l=0.0, brow_r=0.0,
    lid_t=0.18, lid_b=0.05, lid_tilt=0.0, lid_l=0.0, lid_r=0.0,
    pupil=1.0, iris_dim=0.0,
    smile=0.15, open=0.0, mw=1.0, teeth=0.0, skew=0.0, round=0.0, chew=0.0,
    sweat=0.0, blush=0.0, tears=0.0, gloom=0.0, vein=0.0, pale=0.0, heat=0.0,
    steam=0.0, bags=0.0, popcorn_stuck=0.0, shake=0.0, laugh=0.0, twitch=0.0,
    la1=8.0, la2=20.0, ra1=8.0, ra2=20.0,
    eat=0.0, breath=1.0, tub_crush=0.0, tub_tilt=0.0,
    talk=0.0, talk_round=0.0, blink=0.0,
    # discrete (non-interpolated) keys
    lh='open', rh='open', prop_l='', prop_r='', mark='', view='front',
)
DISCRETE = {'lh', 'rh', 'prop_l', 'prop_r', 'mark', 'view'}

OUT_W = 4.0  # outline width at scale 1


# --------------------------------------------------------------------------
# designs
# --------------------------------------------------------------------------
def _d(**kw):
    base = dict(
        skin=hx('#e8b48a'), outline=hx('#3b2418'), head_w=86, head_h=92, head_n=2.0,
        jaw=0.12, eye_rx=19, eye_ry=23, eye_dx=34, eye_y=4, iris=hx('#5b3a1e'),
        iris_r=11, brow_c=hx('#3b2418'), brow_th=9, brow_len=34, brow_gap=14,
        mouth_y=50, mouth_w=46, nose_y=28, nose='small', ears=True,
        sh_w=150, hip_w=128, torso_h=165, neck=16, top=hx('#2a9d8f'),
        arm1=74, arm2=68, arm_th=30, sleeve=hx('#2a9d8f'), sleeve2=None,
        hand_r=17, legs=hx('#3a3f58'), shoes=hx('#262626'), leg_th=34,
        seat_hip=140, stand_hip=225, defaults={},
    )
    base.update(kw)
    if base['sleeve2'] is None:
        base['sleeve2'] = base['sleeve']
    return base


DESIGNS = {
    'me': _d(name='me', skin=hx('#e0a77f'), outline=hx('#3a2216'),
             hair=hx('#3b261c'), top=hx('#2b9c8e'), sleeve=hx('#2b9c8e'),
             iris=hx('#6a4024'), legs=hx('#34395a'), head_w=84, head_h=90),
    'anger': _d(name='anger', skin=hx('#d4442e'), outline=hx('#4a0d0a'), hair=hx('#2a0c0a'),
                head_w=98, head_h=88, head_n=2.45, jaw=0.02, eye_rx=20, eye_ry=21,
                eye_dx=40, eye_y=6, iris=hx('#2a0a08'), iris_r=10, brow_c=hx('#2e0605'),
                brow_th=17, brow_len=44, brow_gap=11, mouth_y=50, mouth_w=62,
                nose='bulb', nose_y=26, ears=True, sh_w=204, hip_w=164, torso_h=160,
                top=hx('#26272e'), sleeve=hx('#26272e'), sleeve2=hx('#d4442e'),
                arm_th=36, hand_r=20, legs=hx('#3b3440'), neck=8,
                defaults=dict(smile=0.25, lid_t=0.22)),
    'doubt': _d(name='doubt', skin=hx('#a796dc'), outline=hx('#2f2350'),
                hair=hx('#3c2a6b'), iris=hx('#3a2a6a'), head_w=80, head_h=92,
                jaw=0.18, top=hx('#d9a441'), sleeve=hx('#d9a441'), legs=hx('#2f2f3f'),
                sh_w=136, hip_w=120, eye_rx=18, eye_ry=21, brow_c=hx('#2c1f55'),
                defaults=dict(lid_t=0.3, lid_b=0.12, smile=0.05, brow_l=0.0)),
    'boredom': _d(name='boredom', skin=hx('#9fb2c4'), outline=hx('#28384a'),
                  hair=hx('#4b5a6b'), iris=hx('#56677a'), head_w=84, head_h=94,
                  top=hx('#7d8796'), sleeve=hx('#7d8796'), legs=hx('#3a4250'),
                  hat=hx('#3b4350'), brow_c=hx('#3a4a5c'),
                  defaults=dict(lid_t=0.52, lid_b=0.08, smile=-0.08, sink=14,
                                brow_y=-0.2, la1=4, ra1=4, la2=40, ra2=40)),
    'stranger': _d(name='stranger', skin=hx('#9a6440'), outline=hx('#2e1a0e'),
                   hair=hx('#1f1510'), iris=hx('#2e1a0e'), head_w=88, head_h=92,
                   top=hx('#3d6fb0'), sleeve=hx('#3d6fb0'), legs=hx('#4a4038'),
                   cap=hx('#2f8f4e'), brow_c=hx('#1f1510'), sh_w=158, hip_w=134,
                   defaults=dict(smile=0.0)),
}


def state_for(name, **over):
    st = dict(DEFAULTS)
    st.update(DESIGNS[name]['defaults'])
    st.update(over)
    return st


# --------------------------------------------------------------------------
# small parts
# --------------------------------------------------------------------------
def _outlined(cv, path, color, oc, ow=OUT_W):
    cv.drawPath(path, fill(color))
    cv.drawPath(path, stroke(oc, ow))


def draw_hand(cv, d, x, y, ang, kind, flip=1, color=None):
    """ang = direction of forearm (radians, screen space)."""
    c = color or d['skin']
    oc = d['outline']
    r = d['hand_r']
    cv.save()
    cv.translate(x, y)
    if kind == 'thumb':
        # fist with thumb pointing up (screen)
        _outlined(cv, rrect(-r, -r * 0.8, r, r * 0.9, r * 0.6), c, oc)
        th = rrect(-r * 0.35 * flip - r * 0.28, -r * 2.0, -r * 0.35 * flip + r * 0.28, -r * 0.4, r * 0.3)
        _outlined(cv, th, c, oc)
        for k in range(3):
            yy = -r * 0.35 + k * r * 0.4
            cv.drawLine(-r * 0.2 * flip, yy, r * 0.95 * flip, yy, stroke(oc, 2.2))
        cv.restore()
        return
    cv.rotate(math.degrees(ang) - 90)
    # local frame: +y along forearm direction
    if kind == 'fist':
        _outlined(cv, oval(0, r * 0.3, r * 0.95, r * 0.9), c, oc)
        for k in (-1, 0, 1):
            cv.drawLine(k * r * 0.35, r * 0.75, k * r * 0.35, r * 1.05, stroke(oc, 2))
    elif kind == 'point':
        fp = rrect(-r * 0.24, r * 0.4, r * 0.24, r * 2.1, r * 0.24)
        _outlined(cv, fp, c, oc)
        _outlined(cv, oval(0, r * 0.3, r * 0.9, r * 0.85), c, oc)
    elif kind == 'splay':
        for k in range(4):
            a = math.radians(-50 + k * 33)
            ex, ey = math.sin(a) * r * 2.0, math.cos(a) * r * 2.0
            cv.drawLine(0, r * 0.4, ex, ey, stroke(oc, r * 0.55 + OUT_W))
            cv.drawLine(0, r * 0.4, ex, ey, stroke(c, r * 0.55))
        tx, ty = -flip * r * 1.3, r * 0.2
        cv.drawLine(0, r * 0.4, tx, ty, stroke(oc, r * 0.55 + OUT_W))
        cv.drawLine(0, r * 0.4, tx, ty, stroke(c, r * 0.55))
        cv.drawPath(oval(0, r * 0.45, r * 0.85, r * 0.8), fill(c))
    elif kind == 'grip':
        _outlined(cv, oval(0, r * 0.35, r * 0.85, r * 1.0), c, oc)
        cv.drawLine(-r * 0.5, r * 0.6, r * 0.5, r * 0.6, stroke(oc, 2))
    else:  # open mitten
        _outlined(cv, oval(-flip * r * 0.75, r * 0.15, r * 0.38, r * 0.55), c, oc)
        _outlined(cv, rrect(-r * 0.8, -r * 0.2, r * 0.8, r * 1.55, r * 0.75), c, oc)
        for k in (-1, 0, 1):
            cv.drawLine(k * r * 0.33, r * 1.05, k * r * 0.33, r * 1.45, stroke(oc, 1.8))
    cv.restore()


def draw_popcorn_tub(cv, x, y, sc=1.0, crush=0.0, tilt=0.0, fullness=1.0, t=0.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(tilt)
    cv.scale(sc * (1 - 0.25 * crush), sc * (1 + 0.08 * crush))
    w1, w2, h = 40, 30, 74
    body = poly([(-w1, -h * 0.55), (w1, -h * 0.55), (w2, h * 0.45), (-w2, h * 0.45)])
    # popcorn top
    if fullness > 0:
        rng = 0
        for i in range(13):
            px = -w1 + 6 + (i % 7) * (2 * w1 - 12) / 6 + (hash01(i, 3) - 0.5) * 6
            py = -h * 0.55 - 6 - (i // 7) * 10 - hash01(i, 5) * 8 * fullness
            rr = 9 + hash01(i, 9) * 4
            cv.drawPath(oval(px, py, rr, rr * 0.85), fill((255, 244, 214)))
            cv.drawPath(oval(px, py, rr, rr * 0.85), stroke((150, 110, 50), 1.6))
            cv.drawPath(oval(px - 2, py - 2, rr * 0.35, rr * 0.3), fill((255, 215, 120), 0.8))
    cv.drawPath(body, fill((240, 240, 240)))
    cv.save()
    cv.clipPath(body, doAntiAlias=True)
    for k in range(-3, 4, 2):
        sx = k * 13
        cv.drawPath(poly([(sx - 6.5, -h), (sx + 6.5, -h), (sx * 0.72 + 5, h), (sx * 0.72 - 5, h)]),
                    fill((210, 40, 40)))
    cv.restore()
    cv.drawPath(body, stroke((70, 20, 20), 3))
    cv.restore()


def draw_soda(cv, x, y, sc=1.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(sc, sc)
    body = poly([(-20, -42), (20, -42), (15, 40), (-15, 40)])
    cv.drawLine(6, -42, 14, -78, stroke((40, 40, 40), 7))
    cv.drawLine(6, -42, 14, -78, stroke((240, 240, 240), 4))
    cv.drawPath(body, fill((235, 235, 240)))
    cv.save()
    cv.clipPath(body, doAntiAlias=True)
    cv.drawRect(skia.Rect.MakeLTRB(-25, -12, 25, 14), fill((30, 110, 200)))
    cv.restore()
    cv.drawPath(rrect(-23, -48, 23, -40, 3), fill((250, 250, 250)))
    cv.drawPath(rrect(-23, -48, 23, -40, 3), stroke((40, 40, 60), 2.5))
    cv.drawPath(body, stroke((40, 40, 60), 3))
    cv.restore()


# --------------------------------------------------------------------------
# face
# --------------------------------------------------------------------------
def _eye(cv, d, st, cx, cy, side, t):
    """side=-1 for screen-left eye, +1 for screen-right eye."""
    rx, ry = d['eye_rx'], d['eye_ry']
    turn = st['head_turn']
    rx *= 1 - 0.18 * max(0, -turn * side)   # far eye narrows
    skin = d['skin']
    oc = d['outline']
    lt = st['lid_t'] + (st['lid_l'] if side < 0 else st['lid_r'])
    lt = max(lt, st['blink'])
    lb = st['lid_b']
    # twitching lower lid
    if st['twitch'] > 0 and side > 0:
        lt += st['twitch'] * 0.25 * max(0, math.sin(t * 47) * math.sin(t * 13))
    lt = max(-0.15, min(1.0, lt))
    lb = max(0.0, min(1.0, lb))
    eye = oval(cx, cy, rx, ry)
    openness = 1 - max(0, lt) - lb
    tilt = st['lid_tilt']
    inner = -side  # inner corner direction in x
    if openness <= 0.06:
        # closed eye: single curve
        tot = max(1e-3, max(0, lt) + lb)
        yc = cy - ry + 2 * ry * (max(0, lt) / tot) * (1 - 0.0)
        yc = cy + ry * 0.15 * (max(0, lt) - lb) / tot
        bow = -ry * 0.75 * (lb / tot) + ry * 0.45 * (max(0, lt) / tot)
        p = skia.Path()
        p.moveTo(cx - rx * 1.05, yc + (tilt * ry * 0.4 if inner < 0 else 0))
        p.quadTo(cx, yc + bow * 2, cx + rx * 1.05, yc + (tilt * ry * 0.4 if inner > 0 else 0))
        cv.drawPath(p, stroke(oc, 5.0))
        return
    # sclera
    cv.drawPath(eye, fill((255, 255, 255)))
    cv.save()
    cv.clipPath(eye, doAntiAlias=True)
    # iris & pupil
    lx = st['look_x'] + turn * 0.35
    ly = st['look_y']
    ir = d['iris_r'] * (0.85 + 0.15 * st['pupil'])
    px = cx + lx * (rx - ir * 0.75)
    py = cy + ly * (ry - ir * 0.8) + ry * 0.05
    icol = mix(d['iris'], (120, 120, 120), st['iris_dim'])
    cv.drawPath(oval(px, py, ir, ir * 1.08), fill(icol))
    pr = ir * 0.58 * st['pupil']
    cv.drawPath(oval(px, py, pr, pr * 1.08), fill((12, 8, 8)))
    if st['iris_dim'] < 0.6:
        cv.drawPath(oval(px + ir * 0.35, py - ir * 0.4, ir * 0.3, ir * 0.3),
                    fill((255, 255, 255), 0.95 * (1 - st['iris_dim'])))
        cv.drawPath(oval(px - ir * 0.35, py + ir * 0.35, ir * 0.13, ir * 0.13),
                    fill((255, 255, 255), 0.7 * (1 - st['iris_dim'])))
    # upper lid
    lid_c = shade(skin, 0.93)
    yb = cy - ry + 2 * ry * max(0.0, lt)
    arch = ry * 0.55 * (1 - max(0.0, lt))
    y_in = yb + tilt * ry * 0.55
    y_out = yb - tilt * ry * 0.15
    yl = y_in if inner < 0 else y_out
    yr = y_in if inner > 0 else y_out
    lid = skia.Path()
    lid.moveTo(cx - rx - 4, cy - ry - 30)
    lid.lineTo(cx - rx - 4, yl)
    lid.quadTo(cx, yb - arch, cx + rx + 4, yr)
    lid.lineTo(cx + rx + 4, cy - ry - 30)
    lid.close()
    if lt > -0.1:
        cv.drawPath(lid, fill(lid_c))
    # lower lid
    if lb > 0.01:
        ybb = cy + ry - 2 * ry * lb
        bowb = ry * 0.9 * lb
        lw = skia.Path()
        lw.moveTo(cx - rx - 4, cy + ry + 30)
        lw.lineTo(cx - rx - 4, ybb + 2)
        lw.quadTo(cx, ybb - bowb, cx + rx + 4, ybb + 2)
        lw.lineTo(cx + rx + 4, cy + ry + 30)
        lw.close()
        cv.drawPath(lw, fill(lid_c))
    cv.restore()
    # outline + lash line
    cv.drawPath(eye, stroke(oc, 2.6))
    if lt > -0.1:
        cv.save()
        cv.clipPath(oval(cx, cy, rx + 3, ry + 3), doAntiAlias=True)
        lash = skia.Path()
        lash.moveTo(cx - rx - 4, yl)
        lash.quadTo(cx, yb - arch, cx + rx + 4, yr)
        cv.drawPath(lash, stroke(oc, 4.6))
        cv.restore()


def _brow(cv, d, st, cx, cy, side):
    L = d['brow_len']
    inner = -side
    raise_ = st['brow_y'] + (st['brow_l'] if side < 0 else st['brow_r'])
    tilt = st['brow_tilt']
    base_y = cy - d['eye_ry'] - d['brow_gap'] - raise_ * 13
    y_in = base_y - tilt * 11 + (6 if tilt < 0 else 0) * (-tilt)
    y_out = base_y + tilt * 5
    x_in = cx + inner * L * 0.5 - inner * 2 * max(0, -tilt)
    x_out = cx - inner * L * 0.5
    arch = 6 - 4 * abs(tilt)
    p = skia.Path()
    p.moveTo(x_out, y_out)
    p.quadTo((x_in + x_out) / 2, min(y_in, y_out) - arch, x_in, y_in)
    cv.drawPath(p, stroke(d['brow_c'], d['brow_th']))


def _mouth(cv, d, st, cx, cy, t):
    W = d['mouth_w'] * st['mw'] * (1 - 0.3 * st['talk_round'])
    talk = st['talk']
    op = st['open'] + talk * 0.62
    if st['chew'] > 0:
        op += st['chew'] * 0.12 * (0.5 + 0.5 * math.sin(t * 11))
    sm = st['smile']
    sk = st['skew']
    oc = d['outline']
    Hs = W * 0.22
    lx, rx_ = cx - W / 2, cx + W / 2
    ly = cy - sm * Hs - sk * Hs
    ry_ = cy - sm * Hs + sk * Hs * 0.4
    if op < 0.05 and st['teeth'] < 0.3:
        p = skia.Path()
        p.moveTo(lx, ly)
        p.cubicTo(lx + W * 0.3, cy + sm * Hs * 1.3, rx_ - W * 0.3, cy + sm * Hs * 1.3, rx_, ry_)
        cv.drawPath(p, stroke(oc, 4.2))
        return
    oph = max(op, 0.12 if st['teeth'] > 0.3 else 0)
    up_c = cy - sm * Hs * 0.2 - oph * W * 0.10
    lo_c = cy + sm * Hs * 1.1 + oph * W * 0.72
    k = 0.12 + 0.25 * min(1, oph)   # corner roundness
    p = skia.Path()
    p.moveTo(lx, ly)
    p.cubicTo(lx + W * k, up_c, rx_ - W * k, up_c, rx_, ry_)
    p.cubicTo(rx_ - W * k * 0.6, lo_c, lx + W * k * 0.6, lo_c, lx, ly)
    p.close()
    if st['teeth'] > 0.3:
        cv.drawPath(p, fill((250, 250, 245)))
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        mid = (up_c + lo_c) / 2 + (ly + ry_) / 4 - cy / 2
        mid = (min(ly, ry_) + lo_c) / 2
        cv.drawLine(lx, mid, rx_, mid, stroke(oc, 2))
        for i in range(1, 6):
            xx = lx + W * i / 6
            cv.drawLine(xx, up_c - 10, xx, lo_c + 10, stroke((150, 140, 140), 1.6))
        cv.restore()
    else:
        cv.drawPath(p, fill((90, 22, 30)))
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        if oph > 0.12:
            cv.drawPath(rrect(lx - 5, min(ly, ry_, up_c) - 20, rx_ + 5, up_c + W * 0.08 + 2, 4),
                        fill((250, 250, 245)))
        if oph > 0.3:
            cv.drawPath(oval(cx, lo_c - W * 0.02, W * 0.3, W * 0.16 * min(1.5, oph + 0.4)),
                        fill((222, 92, 110)))
        cv.restore()
    cv.drawPath(p, stroke(oc, 4.0))


def _sweat_drop(cv, x, y, s, a=1.0):
    p = skia.Path()
    p.moveTo(x, y - 14 * s)
    p.cubicTo(x + 9 * s, y - 2 * s, x + 9 * s, y + 9 * s, x, y + 9 * s)
    p.cubicTo(x - 9 * s, y + 9 * s, x - 9 * s, y - 2 * s, x, y - 14 * s)
    cv.drawPath(p, fill((170, 220, 255), 0.9 * a))
    cv.drawPath(p, stroke((60, 120, 190), 2, a))
    cv.drawPath(oval(x - 2.5 * s, y + 2 * s, 2.2 * s, 3 * s), fill((255, 255, 255), 0.9 * a))


def draw_head(cv, d, st, t, back=False):
    """Draw head centered at origin (already transformed)."""
    a, b = d['head_w'], d['head_h']
    skin = d['skin']
    if st['heat'] > 0:
        skin = mix(skin, (150, 15, 10), st['heat'] * 0.5)
    if st['pale'] > 0:
        skin = mix(skin, (190, 200, 225), st['pale'] * 0.45)
    oc = d['outline']
    name = d['name']
    turn = st['head_turn']
    fx = turn * a * 0.16
    head = superellipse(0, 0, a, b, d['head_n'], d['jaw'])

    # ---- back hair / hats behind
    if name == 'me':
        bh = skia.Path()
        bh.moveTo(-a * 1.08, -b * 0.2)
        bh.cubicTo(-a * 1.25, b * 0.6, -a * 1.05, b * 0.95, -a * 0.7, b * 0.98)
        bh.lineTo(a * 0.7, b * 0.98)
        bh.cubicTo(a * 1.05, b * 0.95, a * 1.25, b * 0.6, a * 1.08, -b * 0.2)
        bh.cubicTo(a * 1.1, -b * 1.25, -a * 1.1, -b * 1.25, -a * 1.08, -b * 0.2)
        _outlined(cv, bh, d['hair'], oc)
    if name == 'doubt':
        _outlined(cv, oval(0, -b * 1.12, a * 0.42, b * 0.32), d['hair'], oc)   # bun
    if name == 'stranger':
        pass

    # ---- ears
    if d['ears']:
        for sd in (-1, 1):
            ex = sd * a * 0.98 + fx * 0.3
            if turn * sd < -0.5:
                continue
            _outlined(cv, oval(ex, b * 0.12, a * 0.16, b * 0.22), shade(skin, 0.95), oc)
    # ---- head
    _outlined(cv, head, skin, oc)
    # soft shading
    cv.save()
    cv.clipPath(head, doAntiAlias=True)
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(lin_grad((0, -b), (0, b), [(shade(skin, 1.12), 0.0), (shade(skin, 0.80), 0.35)]))
    cv.drawRect(skia.Rect.MakeLTRB(-a * 1.2, -b * 1.2, a * 1.2, b * 1.2), sh)
    cv.restore()

    if back:
        _hair_front(cv, d, st, a, b, oc, back=True)
        return

    # ---- cheeks / blush
    if st['blush'] > 0.01:
        for sd in (-1, 1):
            cv.drawPath(oval(fx + sd * a * 0.58, b * 0.32, a * 0.2, b * 0.1),
                        fill((255, 90, 110), 0.45 * st['blush'], blur=4))
    # ---- eye bags
    if st['bags'] > 0.01:
        for sd in (-1, 1):
            ex = fx + sd * d['eye_dx']
            p = skia.Path()
            p.moveTo(ex - d['eye_rx'], d['eye_y'] + d['eye_ry'] * 0.9)
            p.quadTo(ex, d['eye_y'] + d['eye_ry'] * 1.8, ex + d['eye_rx'], d['eye_y'] + d['eye_ry'] * 0.9)
            cv.drawPath(p, stroke(shade(skin, 0.6), 4, st['bags']))
    # ---- gloom lines
    if st['gloom'] > 0.01:
        cv.save()
        cv.clipPath(head, doAntiAlias=True)
        for i in range(9):
            xx = -a * 0.8 + i * a * 0.2
            yy = -b * 1.0
            cv.drawLine(xx, yy, xx, yy + b * (0.45 + 0.15 * hash01(i, 2)),
                        stroke((60, 50, 140), 3.2, st['gloom'] * 0.8))
        cv.restore()
    # ---- eyes
    for sd in (-1, 1):
        _eye(cv, d, st, fx + sd * d['eye_dx'], d['eye_y'], sd, t)
    # ---- nose
    nx, ny = fx * 1.3, d['nose_y']
    if d['nose'] == 'bulb':
        _outlined(cv, oval(nx, ny, 17, 13), shade(skin, 0.9), oc, 3)
        cv.drawPath(oval(nx - 5, ny - 4, 5, 3.5), fill((255, 255, 255), 0.35))
    else:
        p = skia.Path()
        p.moveTo(nx - 6, ny - 4)
        p.quadTo(nx - 9, ny + 8, nx + 2, ny + 7)
        cv.drawPath(p, stroke(oc, 3.2))
    # ---- facial hair (stranger goatee)
    if name == 'stranger':
        my = d['mouth_y']
        g = skia.Path()
        g.moveTo(fx - 13, my + 14)
        g.quadTo(fx, my + 40, fx + 13, my + 14)
        g.quadTo(fx, my + 20, fx - 13, my + 14)
        cv.drawPath(g, fill(d['hair'], 0.92))
        for sd in (-1, 1):
            mus = skia.Path()
            mus.moveTo(fx + sd * 2, my - 9)
            mus.quadTo(fx + sd * 18, my - 13, fx + sd * 27, my - 1)
            cv.drawPath(mus, stroke(d['hair'], 5))
    # ---- mouth
    _mouth(cv, d, st, fx * 1.2, d['mouth_y'], t)
    # ---- hair front, brows, glasses, hats
    _hair_front(cv, d, st, a, b, oc)
    for sd in (-1, 1):
        _brow(cv, d, st, fx + sd * d['eye_dx'], d['eye_y'], sd)
    if name == 'doubt':
        for sd in (-1, 1):
            ex = fx + sd * d['eye_dx']
            cv.drawPath(oval(ex, d['eye_y'], 27, 27), fill((220, 235, 255), 0.18))
            cv.drawPath(oval(ex, d['eye_y'], 27, 27), stroke((30, 25, 50), 4))
            cv.drawLine(ex - 12, d['eye_y'] - 14, ex - 2, d['eye_y'] - 20, stroke((255, 255, 255), 3, 0.7))
        cv.drawLine(fx - d['eye_dx'] + 27, d['eye_y'] - 3, fx + d['eye_dx'] - 27, d['eye_y'] - 3, stroke((30, 25, 50), 4))
    # ---- extras
    if st['vein'] > 0.01:
        vx, vy = a * 0.5, -b * 0.6
        sc = 0.8 + 0.2 * math.sin(t * 9)
        for k in range(4):
            ang = k * math.pi / 2 + math.pi / 4
            px, py = vx + math.cos(ang) * 6 * sc, vy + math.sin(ang) * 6 * sc
            p = skia.Path()
            p.moveTo(px + math.cos(ang) * 10 * sc, py + math.sin(ang) * 10 * sc)
            p.quadTo(px, py, px + math.cos(ang + 1.2) * 12 * sc, py + math.sin(ang + 1.2) * 12 * sc)
            cv.drawPath(p, stroke((120, 0, 0), 4.5, st['vein']))
    if st['sweat'] > 0.01:
        n = 1 + int(st['sweat'] * 2.99)
        for i in range(n):
            ph = (t * (0.35 + 0.1 * i) + hash01(i, 11)) % 1.0
            sdx = 1 if i % 2 == 0 else -1
            x0 = sdx * a * (0.72 + 0.08 * i) + fx * 0.5
            y0 = -b * 0.45 + ph * b * 0.6 + i * 10
            _sweat_drop(cv, x0, y0, 0.9 + 0.2 * st['sweat'], min(1, st['sweat'] * 2) * (1 - ph ** 3))
    if st['tears'] > 0.01:
        for sd in (-1, 1):
            ex = fx + sd * (d['eye_dx'] + d['eye_rx'] * 0.7)
            p = skia.Path()
            p.moveTo(ex, d['eye_y'] + 6)
            p.quadTo(ex + sd * 6, d['eye_y'] + 30, ex + sd * 2, d['eye_y'] + 30 + 40 * st['tears'])
            cv.drawPath(p, stroke((120, 190, 255), 6, 0.75 * st['tears']))
            for k in range(2):
                ph = (t * 1.6 + k * 0.5 + (0.25 if sd > 0 else 0)) % 1.0
                tx_ = ex + sd * (10 + ph * 40)
                ty_ = d['eye_y'] - 4 - 30 * ph + 60 * ph * ph
                cv.drawPath(oval(tx_, ty_, 5, 6), fill((140, 200, 255), st['tears'] * (1 - ph)))
    if st['popcorn_stuck'] > 0.01:
        spots = [(-0.5, -0.7), (0.3, -0.85), (0.62, -0.2), (-0.7, 0.3), (0.1, 0.62), (-0.25, -0.35)]
        n = int(len(spots) * st['popcorn_stuck'] + 0.5)
        for i in range(n):
            px, py = spots[i]
            px, py = px * a + fx * 0.5, py * b
            cv.drawPath(oval(px, py, 8, 7), fill((255, 244, 214)))
            cv.drawPath(oval(px, py, 8, 7), stroke((150, 110, 50), 1.5))
            cv.drawPath(oval(px + 3, py - 2, 4, 3.5), fill((255, 244, 214)))


def _hair_front(cv, d, st, a, b, oc, back=False):
    name = d['name']
    if name == 'me':
        p = skia.Path()
        p.moveTo(-a * 1.04, b * 0.05)
        p.cubicTo(-a * 1.12, -b * 0.9, -a * 0.4, -b * 1.2, a * 0.2, -b * 1.08)
        p.cubicTo(a * 0.9, -b * 1.0, a * 1.15, -b * 0.55, a * 1.05, b * 0.1)
        if back:
            p.cubicTo(a * 0.6, b * 0.3, -a * 0.6, b * 0.3, -a * 1.04, b * 0.05)
        else:
            p.cubicTo(a * 0.95, -b * 0.35, a * 0.8, -b * 0.55, a * 0.55, -b * 0.6)
            p.cubicTo(a * 0.2, -b * 0.35, -a * 0.1, -b * 0.45, -a * 0.25, -b * 0.62)
            p.cubicTo(-a * 0.5, -b * 0.4, -a * 0.75, -b * 0.35, -a * 0.82, -b * 0.15)
            p.cubicTo(-a * 0.9, -b * 0.0, -a * 0.95, b * 0.0, -a * 1.04, b * 0.05)
        p.close()
        _outlined(cv, p, d['hair'], oc)
        cv.drawPath(oval(-a * 0.2, -b * 0.88, a * 0.3, b * 0.07), fill((255, 255, 255), 0.12))
    elif name == 'anger':
        p = skia.Path()
        p.moveTo(-a * 0.98, -b * 0.42)
        p.lineTo(-a * 0.99, -b * 1.12)
        p.quadTo(-a * 0.99, -b * 1.2, -a * 0.88, -b * 1.2)
        p.lineTo(a * 0.88, -b * 1.2)
        p.quadTo(a * 0.99, -b * 1.2, a * 0.99, -b * 1.12)
        p.lineTo(a * 0.98, -b * 0.42)
        if back:
            p.lineTo(a * 0.98, b * 0.2)
            p.quadTo(0, b * 0.35, -a * 0.98, b * 0.2)
        else:
            p.lineTo(a * 0.86, -b * 0.42)
            p.lineTo(a * 0.82, -b * 0.62)
            p.quadTo(0, -b * 0.72, -a * 0.82, -b * 0.62)
            p.lineTo(-a * 0.86, -b * 0.42)
        p.close()
        _outlined(cv, p, d['hair'], oc)
        for i in range(-6, 7):
            cv.drawLine(i * a * 0.13, -b * 1.17, i * a * 0.13, -b * 0.95, stroke(shade(d['hair'], 1.6), 1.6, 0.5))
    elif name == 'doubt':
        p = skia.Path()
        p.moveTo(-a * 1.0, -b * 0.05)
        p.cubicTo(-a * 1.08, -b * 1.12, a * 1.08, -b * 1.12, a * 1.0, -b * 0.05)
        if back:
            p.cubicTo(a * 0.5, b * 0.3, -a * 0.5, b * 0.3, -a * 1.0, -b * 0.05)
        else:
            p.cubicTo(a * 0.85, -b * 0.55, a * 0.3, -b * 0.62, 0, -b * 0.7)
            p.cubicTo(-a * 0.3, -b * 0.62, -a * 0.85, -b * 0.55, -a * 1.0, -b * 0.05)
        p.close()
        _outlined(cv, p, d['hair'], oc)
        cv.drawLine(0, -b * 0.98, 0, -b * 0.72, stroke(shade(d['hair'], 0.7), 3))
    elif name == 'boredom':
        # tufts + beanie
        for sd in (-1, 1):
            tp = skia.Path()
            tp.moveTo(sd * a * 0.98, -b * 0.4)
            tp.quadTo(sd * a * 1.18, -b * 0.1, sd * a * 0.95, b * 0.05)
            tp.quadTo(sd * a * 0.9, -b * 0.2, sd * a * 0.8, -b * 0.35)
            _outlined(cv, tp, d['hair'], oc, 3)
        hat = skia.Path()
        hat.moveTo(-a * 1.06, -b * 0.42)
        hat.cubicTo(-a * 1.1, -b * 1.45, a * 1.1, -b * 1.45, a * 1.06, -b * 0.42)
        hat.close()
        _outlined(cv, hat, d['hat'], oc)
        _outlined(cv, rrect(-a * 1.1, -b * 0.62, a * 1.1, -b * 0.36, 12), shade(d['hat'], 0.85), oc)
        for i in range(-4, 5):
            cv.drawLine(i * a * 0.22, -b * 0.6, i * a * 0.22, -b * 0.39, stroke(shade(d['hat'], 0.65), 2))
        _outlined(cv, oval(0, -b * 1.17, 16, 14), shade(d['hat'], 1.3), oc, 3)
    elif name == 'stranger':
        cap = skia.Path()
        cap.moveTo(-a * 1.04, -b * 0.35)
        cap.cubicTo(-a * 1.05, -b * 1.35, a * 1.05, -b * 1.35, a * 1.04, -b * 0.35)
        cap.close()
        _outlined(cv, cap, d['cap'], oc)
        cv.drawLine(0, -b * 1.03, 0, -b * 0.4, stroke(shade(d['cap'], 0.7), 2.5))
        cv.drawPath(oval(0, -b * 1.04, 7, 5), fill(shade(d['cap'], 0.7)))
        if not back:
            bill = skia.Path()
            bill.moveTo(-a * 1.08, -b * 0.38)
            bill.cubicTo(-a * 0.8, -b * 0.18, a * 0.8, -b * 0.18, a * 1.08, -b * 0.38)
            bill.cubicTo(a * 0.8, -b * 0.5, -a * 0.8, -b * 0.5, -a * 1.08, -b * 0.38)
            _outlined(cv, bill, shade(d['cap'], 0.8), oc)
        # sideburns
        for sd in (-1, 1):
            cv.drawPath(rrect(sd * a * 0.95 - 7, -b * 0.4, sd * a * 0.95 + 7, b * 0.05, 6), fill(d['hair']))


# --------------------------------------------------------------------------
# body
# --------------------------------------------------------------------------
def _torso_path(d, sc_y=1.0, hunch=0.0):
    sw, hw, th = d['sh_w'] / 2, d['hip_w'] / 2, d['torso_h'] * sc_y * (1 - 0.18 * hunch)
    p = skia.Path()
    p.moveTo(-hw, 0)
    p.lineTo(-sw * 0.98, -th * 0.72)
    p.quadTo(-sw, -th, -sw * 0.68, -th)
    p.lineTo(sw * 0.68, -th)
    p.quadTo(sw, -th, sw * 0.98, -th * 0.72)
    p.lineTo(hw, 0)
    p.quadTo(0, 14, -hw, 0)
    p.close()
    return p, th


def _clothes(cv, d, st, th, t):
    name = d['name']
    oc = d['outline']
    sw = d['sh_w'] / 2
    if name == 'me':
        # hood collar + strings + pocket
        hood = skia.Path()
        hood.moveTo(-sw * 0.62, -th - 4)
        hood.quadTo(0, -th + 34, sw * 0.62, -th - 4)
        hood.quadTo(0, -th + 12, -sw * 0.62, -th - 4)
        cv.drawPath(hood, fill(shade(d['top'], 0.75)))
        for sd in (-1, 1):
            cv.drawLine(sd * 16, -th + 22, sd * 18 + math.sin(t * 2 + sd) * 2, -th + 75, stroke((240, 240, 240), 3.5))
            cv.drawPath(oval(sd * 18, -th + 79, 3.5, 5), fill((200, 200, 200)))
        pk = poly([(-48, -th * 0.42), (48, -th * 0.42), (60, -12), (-60, -12)])
        cv.drawPath(pk, stroke(shade(d['top'], 0.7), 3))
    elif name == 'anger':
        # black tee: crew neck + yellow shield emblem (the protector)
        neck = skia.Path()
        neck.moveTo(-40, -th - 2)
        neck.quadTo(0, -th + 30, 40, -th - 2)
        cv.drawPath(neck, stroke((70, 72, 82), 6))
        sx, sy = -42, -th + 62
        sp = skia.Path()
        sp.moveTo(sx - 17, sy - 18)
        sp.lineTo(sx + 17, sy - 18)
        sp.lineTo(sx + 17, sy + 2)
        sp.quadTo(sx + 14, sy + 16, sx, sy + 24)
        sp.quadTo(sx - 14, sy + 16, sx - 17, sy + 2)
        sp.close()
        cv.drawPath(sp, fill((240, 190, 60)))
        cv.drawPath(sp, stroke((120, 80, 10), 2.5))
        cv.drawLine(sx, sy - 12, sx, sy + 16, stroke((200, 60, 40), 4))
        cv.drawRect(skia.Rect.MakeLTRB(-d['hip_w'] / 2, -18, d['hip_w'] / 2, -4), fill((50, 40, 45)))
    elif name == 'doubt':
        cv.drawPath(poly([(-30, -th + 2), (30, -th + 2), (0, -th + 50)]), fill((245, 245, 250)))
        cv.drawLine(0, -th + 50, 0, -6, stroke(shade(d['top'], 0.7), 3))
        for k in range(4):
            cv.drawPath(oval(-9, -th + 62 + k * 26, 4, 4), fill((120, 80, 30)))
    elif name == 'boredom':
        cv.drawPath(rrect(-46, -th - 6, 46, -th + 14, 9), fill(shade(d['top'], 0.85)))
        for i in range(-4, 5):
            cv.drawLine(i * 10, -th - 4, i * 10, -th + 12, stroke(shade(d['top'], 0.65), 2))
    elif name == 'stranger':
        cv.save()
        p, _ = _torso_path(d, 1.0)
        cv.clipPath(p, doAntiAlias=True)
        for i in range(-6, 7):
            cv.drawLine(i * 26, -th - 10, i * 26, 10, stroke((25, 50, 100), 6, 0.55))
        for j in range(0, 8):
            cv.drawLine(-120, -th + j * 26, 120, -th + j * 26, stroke((25, 50, 100), 5, 0.45))
        cv.restore()
        cv.drawPath(poly([(-26, -th + 2), (26, -th + 2), (0, -th + 30)]), fill(d['skin']))
        cv.drawLine(0, -th + 30, 0, -6, stroke(oc, 2.5))


def _legs(cv, d, st, hip_h):
    oc = d['outline']
    lt = d['leg_th']
    hw = d['hip_w'] / 2
    stand = st['stand']
    kneel = st['kneel']
    walk = st['walk']
    ph = st['walk_phase']
    for sd in (-1, 1):
        hx_ = sd * hw * 0.48
        lift = walk * 18 * max(0.0, math.sin(ph + (0 if sd < 0 else math.pi)))
        if kneel > 0.5:
            # thighs down to knees on the floor
            kx, ky = sd * hw * 0.55, -6
            cv.drawLine(hx_, -hip_h, kx, ky - 18, stroke(oc, lt + OUT_W * 2))
            cv.drawLine(hx_, -hip_h, kx, ky - 18, stroke(d['legs'], lt))
            _outlined(cv, oval(kx, ky - 10, lt * 0.62, lt * 0.42), shade(d['legs'], 0.9), oc)
            continue
        if stand < 0.5:
            # seated: thighs foreshortened, knees forward
            kx, ky = sd * hw * 0.62, -hip_h + 32
            fx_, fy = sd * hw * 0.62, -8 - lift
            cv.drawLine(kx, ky, fx_, fy - 6, stroke(oc, lt + OUT_W * 2))
            cv.drawLine(kx, ky, fx_, fy - 6, stroke(d['legs'], lt))
            _outlined(cv, oval(kx, ky, lt * 0.78, lt * 0.68), shade(d['legs'], 1.08), oc)
        else:
            fx_, fy = sd * hw * 0.55, -8 - lift
            cv.drawLine(hx_, -hip_h + 10, fx_, fy - 6, stroke(oc, lt + OUT_W * 2))
            cv.drawLine(hx_, -hip_h + 10, fx_, fy - 6, stroke(d['legs'], lt))
        _outlined(cv, oval(fx_ + sd * 6, fy, lt * 0.85, lt * 0.42), d['shoes'], oc)


def _arm_points(d, st, side, th):
    """Returns shoulder, elbow, hand points and forearm angle, in torso space."""
    sw = d['sh_w'] / 2
    a1 = st['la1'] if side < 0 else st['ra1']
    a2 = st['la2'] if side < 0 else st['ra2']
    sx, sy = side * (sw - d['arm_th'] * 0.45), -th + d['arm_th'] * 0.5
    r1 = math.radians(a1)
    ex = sx + side * math.sin(r1) * d['arm1']
    ey = sy + math.cos(r1) * d['arm1']
    r2 = math.radians(a1 - a2)
    hx_ = ex + side * math.sin(r2) * d['arm2']
    hy = ey + math.cos(r2) * d['arm2']
    ang = math.atan2(hy - ey, hx_ - ex)
    return (sx, sy), (ex, ey), (hx_, hy), ang


def _draw_arm(cv, d, st, side, th, t):
    (sx, sy), (ex, ey), (hx_, hy), ang = _arm_points(d, st, side, th)
    oc = d['outline']
    at = d['arm_th']
    cv.drawLine(sx, sy, ex, ey, stroke(oc, at + OUT_W * 2))
    cv.drawLine(ex, ey, hx_, hy, stroke(oc, at * 0.9 + OUT_W * 2))
    cv.drawLine(sx, sy, ex, ey, stroke(d['sleeve'], at))
    cv.drawLine(ex, ey, hx_, hy, stroke(d['sleeve2'], at * 0.9))
    if d['name'] == 'anger':   # tee sleeve ends above the elbow; muscular forearm
        r1 = math.atan2(ey - sy, ex - sx)
        mx, my = sx + (ex - sx) * 0.62, sy + (ey - sy) * 0.62
        cv.drawLine(mx, my, ex, ey, stroke(oc, at + OUT_W * 2))
        cv.drawLine(mx, my, ex, ey, stroke(d['skin'], at))
        cv.drawLine(ex, ey, hx_, hy, stroke(d['skin'], at * 0.9))
        cv.drawLine(mx - math.cos(r1) * 2, my - math.sin(r1) * 2, mx + math.cos(r1) * 2, my + math.sin(r1) * 2,
                    stroke((60, 62, 72), at + 2, cap='butt'))
    elif d['name'] in ('me', 'boredom', 'doubt', 'stranger'):
        cx = hx_ - math.cos(ang) * d['hand_r'] * 0.6
        cy = hy - math.sin(ang) * d['hand_r'] * 0.6
        cv.drawLine(cx - math.cos(ang) * 6, cy - math.sin(ang) * 6, cx, cy,
                    stroke(shade(d['sleeve'], 0.85), at * 0.95))
    prop = st['prop_l'] if side < 0 else st['prop_r']
    kind = st['lh'] if side < 0 else st['rh']
    if prop == 'popcorn':
        draw_popcorn_tub(cv, hx_ + side * 4, hy - 30, 1.0, st['tub_crush'], st['tub_tilt'],
                         fullness=1.0 - 0.6 * st['tub_crush'], t=t)
        draw_hand(cv, d, hx_, hy - 10, ang, 'grip', side)
        return
    if prop == 'soda':
        draw_soda(cv, hx_, hy - 34, 0.9)
        draw_hand(cv, d, hx_, hy - 18, ang, 'grip', side)
        return
    draw_hand(cv, d, hx_, hy, ang, kind, side, color=d['skin'])
    if prop == 'kernel':
        cv.drawPath(oval(hx_ + math.cos(ang) * 14, hy + math.sin(ang) * 14, 8, 7), fill((255, 244, 214)))


def draw_character(cv, name, st, t):
    d = DESIGNS[name]
    if st['alpha'] <= 0.001:
        return
    cv.save()
    jx = jy = 0.0
    if st['shake'] > 0:
        jx = noise1(t * 30, 1.7) * 5 * st['shake']
        jy = noise1(t * 30, 4.1) * 4 * st['shake']
    cv.translate(st['x'] + jx, st['y'] + jy)
    cv.scale(st['s'], st['s'])
    if st['alpha'] < 0.999:
        cv.saveLayerAlpha(None, int(st['alpha'] * 255))
    if st['lying'] > 0.5:
        _draw_lying(cv, d, st, t)
    else:
        _draw_upright(cv, d, st, t)
    if st['alpha'] < 0.999:
        cv.restore()
    cv.restore()


def _draw_upright(cv, d, st, t):
    stand = st['stand']
    hip_h = d['seat_hip'] + (d['stand_hip'] - d['seat_hip']) * min(1, stand)
    if st['kneel'] > 0:
        hip_h = hip_h + (95 - hip_h) * st['kneel']
    hip_h -= st['sink']
    walk_bob = st['walk'] * 6 * abs(math.sin(st['walk_phase']))
    hip_y = -hip_h - walk_bob + st['bob']
    # ground shadow
    cv.drawPath(oval(0, 2, d['hip_w'] * 0.75, 12), fill((0, 0, 0), 0.25, blur=6))
    _legs(cv, d, st, hip_h - st['bob'])
    # torso (with lean around hips)
    breath = math.sin(t * 2 * math.pi / 3.6 * st['breath']) * (0.012 + 0.02 * max(0, st['breath'] - 1))
    lf = st['laugh']
    if lf > 0:
        breath += lf * 0.03 * math.sin(t * 2 * math.pi * 4.5)
    cv.save()
    cv.translate(st['dx'], hip_y)
    cv.rotate(st['lean'])
    tp, th = _torso_path(d, 1 + breath, st['hunch'])
    _outlined(cv, tp, d['top'], d['outline'])
    cv.save()
    cv.clipPath(tp, doAntiAlias=True)
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(lin_grad((0, -th), (0, 0), [((255, 255, 255), 0.10), ((0, 0, 0), 0.18)]))
    cv.drawRect(skia.Rect.MakeLTRB(-200, -th - 10, 200, 20), sh)
    _clothes(cv, d, st, th, t)
    cv.restore()
    # neck + head
    neck_top = -th - d['neck']
    cv.drawRect(skia.Rect.MakeLTRB(-d['head_w'] * 0.28, neck_top - 10, d['head_w'] * 0.28, -th + 6),
                fill(shade(d['skin'], 0.8)))
    head_y = neck_top - d['head_h'] * 0.88 + st['head_nod'] + st['hunch'] * 30
    cv.save()
    cv.translate(st['head_dx'], -th - d['neck'] * 0.5)
    tilt = st['head_tilt'] + (noise1(t * 0.35, hash01(len(d['name']))) * 1.6)
    if st['laugh'] > 0:
        tilt += st['laugh'] * 3 * math.sin(t * 2 * math.pi * 2.2)
    cv.rotate(tilt)
    cv.translate(0, head_y + th + d['neck'] * 0.5)
    draw_head(cv, d, st, t)
    # comic marks / steam
    if st['mark']:
        f = font('InterDisplay-Black', 64)
        cv.drawString(st['mark'], d['head_w'] * 0.75, -d['head_h'] * 0.95, f, stroke((20, 20, 20), 8))
        cv.drawString(st['mark'], d['head_w'] * 0.75, -d['head_h'] * 0.95, f, fill((255, 230, 80)))
    if st['steam'] > 0.01:
        for i in range(4):
            ph = (t * 0.7 + i * 0.25) % 1.0
            sx = (i - 1.5) * 30 + math.sin(t * 3 + i) * 8
            sy = -d['head_h'] - 10 - ph * 90
            cv.drawPath(oval(sx, sy, 12 + 18 * ph, 10 + 14 * ph), fill((255, 255, 255), st['steam'] * 0.55 * (1 - ph)))
    cv.restore()
    # arms (in torso space)
    for side in (-1, 1):
        _draw_arm(cv, d, st, side, th, t)
    cv.restore()


def name_has_ear(d):
    return d['name'] in ('anger', 'me', 'stranger')


def _draw_lying(cv, d, st, t):
    """Face-down on the floor, head at screen-left; head_lift raises the face."""
    oc = d['outline']
    L = d['torso_h']
    # legs
    for k, yy in enumerate((-22, -8)):
        cv.drawLine(L * 0.55, yy, L * 0.55 + 190, yy + 4, stroke(oc, d['leg_th'] + OUT_W * 2))
        cv.drawLine(L * 0.55, yy, L * 0.55 + 190, yy + 4, stroke(d['legs'], d['leg_th']))
        _outlined(cv, oval(L * 0.55 + 205, yy, 16, 22), d['shoes'], oc)
    # back arm splayed above head
    cv.drawLine(-L * 0.45, -40, -L * 0.45 - 70, -70, stroke(oc, d['arm_th'] + OUT_W * 2))
    cv.drawLine(-L * 0.45 - 70, -70, -L * 0.45 - 150, -40, stroke(oc, d['arm_th'] + OUT_W * 2))
    cv.drawLine(-L * 0.45, -40, -L * 0.45 - 70, -70, stroke(d['sleeve'], d['arm_th']))
    cv.drawLine(-L * 0.45 - 70, -70, -L * 0.45 - 150, -40, stroke(d['sleeve2'], d['arm_th'] * 0.9))
    draw_hand(cv, d, -L * 0.45 - 155, -36, math.radians(160), 'open', 1)
    # torso horizontal
    tp = rrect(-L * 0.55, -d['sh_w'] * 0.32, L * 0.6, 0, 30)
    _outlined(cv, tp, d['top'], oc)
    # front arm along body
    cv.drawLine(-L * 0.3, -18, L * 0.1, -2, stroke(oc, d['arm_th'] + OUT_W * 2))
    cv.drawLine(L * 0.1, -2, L * 0.45, -6, stroke(oc, d['arm_th'] + OUT_W * 2))
    cv.drawLine(-L * 0.3, -18, L * 0.1, -2, stroke(d['sleeve'], d['arm_th']))
    cv.drawLine(L * 0.1, -2, L * 0.45, -6, stroke(d['sleeve2'], d['arm_th'] * 0.9))
    draw_hand(cv, d, L * 0.5, -6, 0.0, 'open', -1)
    # head
    lift = st['head_lift']
    hx_ = -L * 0.55 - d['head_w'] * 0.75
    if lift < 0.5:
        # face pressed into the floor: we see the side/back of the head, crown pointing away
        cv.save()
        cv.translate(hx_ + 6, -d['head_h'] * 0.55)
        cv.rotate(-80 + 10 * lift)
        cv.scale(0.92, 0.92)
        draw_head(cv, d, st, t, back=True)
        if d['ears'] or name_has_ear(d):
            _outlined(cv, oval(0, d['head_h'] * 0.05, d['head_w'] * 0.17, d['head_h'] * 0.24), shade(d['skin'], 0.92), d['outline'])
        cv.restore()
    else:
        u = (lift - 0.5) * 2
        cv.save()
        cv.translate(hx_ - 10 * u, -d['head_h'] * (0.75 + 0.35 * u))
        cv.rotate(-6 * (1 - u))
        draw_head(cv, d, st, t)
        cv.restore()


def head_world(name, st):
    """Approximate world position of a character's head center (for camera follow)."""
    d = DESIGNS[name]
    s = st['s']
    if st['lying'] > 0.5:
        L = d['torso_h']
        lift = st['head_lift']
        hx_ = st['x'] - (L * 0.55 + d['head_w'] * 0.75 + 10 * max(0, lift - 0.5) * 2) * s
        hy = st['y'] - d['head_h'] * (0.62 + 0.48 * lift) * s
        return hx_, hy
    stand = st['stand']
    hip_h = d['seat_hip'] + (d['stand_hip'] - d['seat_hip']) * min(1, stand)
    if st['kneel'] > 0:
        hip_h = hip_h + (95 - hip_h) * st['kneel']
    hip_h -= st['sink']
    hip_y = -hip_h + st['bob']
    th = d['torso_h'] * (1 - 0.18 * st['hunch'])
    up = th + d['neck'] * 0.5 + (d['neck'] * 0.5 + d['head_h'] * 0.88 - st['head_nod'] - st['hunch'] * 30)
    a = math.radians(st['lean'])
    ox, oy = math.sin(a) * up, -math.cos(a) * up
    return st['x'] + (st['dx'] + ox) * s, st['y'] + (hip_y + oy) * s
