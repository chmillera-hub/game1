"""A cartoon skeleton: rounded bones, a big friendly skull with expressive
eye sockets, brow ridges and a flapping jaw, plus a small dance vocabulary.

Angles: 0 points straight down, positive swings toward screen-right.
"""
import math

import cairo

from drawkit import INK, clamp, draw_eye, ellipse, hash01, hexc, lerp, radial, smooth

BONE = hexc('#efe8da')
BONE_SHADE = hexc('#c9c0b0')
SOCKET = INK

# limb lengths (local units, scale 1)
UPPER, FORE, THIGH, SHIN = 70, 64, 84, 80
NECK_Y = -178

POSE_DEF = dict(dy=0.0, lean=0.0, head=0.0, crouch=0.0, armL=-14.0, elbL=6.0, armR=14.0, elbR=-6.0,
                legL=-5.0, kneeL=0.0, legR=5.0, kneeR=0.0, spread=0.0, flip=1.0, shake=0.0, rise=1.0)

FACE_DEF = dict(brow_y=0, brow_tilt=0, brow_asym=0, lid_top=0.02, lid_bot=0.05, lid_tilt=0, eye_scale=1.0,
                happy=0, glint=1.0, smile=0.5, jaw=0.0)
FACE_EMO = {
    'neutral': {},
    'jolly': dict(brow_y=6, lid_bot=.25, smile=.9, glint=1.2),
    'gleeful': dict(brow_y=10, happy=.9, smile=1.0, jaw=.25),
    'sly': dict(lid_top=.35, lid_bot=.2, brow_asym=12, brow_tilt=-5, smile=.8),
    'gentle': dict(brow_y=4, brow_tilt=7, lid_top=.25, lid_bot=.3, smile=.55),
    'warm': dict(brow_y=6, brow_tilt=4, lid_top=.18, lid_bot=.32, smile=.75, glint=1.3),
    'curious': dict(brow_y=8, brow_asym=12, lid_top=.05, smile=.35, eye_scale=1.06),
    'surprised': dict(brow_y=16, eye_scale=1.18, jaw=.5, smile=.1),
    'singing': dict(brow_y=8, lid_bot=.15, smile=.8, glint=1.2),
    'belting': dict(brow_y=14, happy=.6, smile=.9, glint=1.3),
    'proud': dict(brow_y=6, lid_top=.3, lid_bot=.3, smile=.9),
    'listening': dict(brow_y=5, brow_tilt=6, lid_top=.12, smile=.4, glint=1.2),
    'concerned': dict(brow_y=4, brow_tilt=12, lid_top=.2, smile=.15),
}


def face_params(name):
    return dict(FACE_DEF, **FACE_EMO.get(name, {}))


def bone(ctx, a, b, w=9, knob=8.5):
    """A single bone from point a to point b: shaft with knobbly ends, inked."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy) + 1e-6
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    for col, grow in ((INK, 4.5), (BONE, 0.0)):
        ctx.set_source_rgb(*col)
        ctx.new_path()
        ctx.move_to(ax + nx * (w / 2 + grow / 2), ay + ny * (w / 2 + grow / 2))
        ctx.line_to(bx + nx * (w / 2 + grow / 2), by + ny * (w / 2 + grow / 2))
        ctx.line_to(bx - nx * (w / 2 + grow / 2), by - ny * (w / 2 + grow / 2))
        ctx.line_to(ax - nx * (w / 2 + grow / 2), ay - ny * (w / 2 + grow / 2))
        ctx.close_path()
        ctx.fill()
        for (px, py) in ((ax, ay), (bx, by)):
            for side in (-1, 1):
                ctx.new_path()
                ctx.arc(px + nx * side * knob * 0.55, py + ny * side * knob * 0.55, knob * 0.62 + grow / 2, 0, 2 * math.pi)
                ctx.fill()


def limb(origin, a1, rel, l1, l2):
    a1r = math.radians(a1)
    a2r = math.radians(a1 + rel)
    j = (origin[0] + l1 * math.sin(a1r), origin[1] + l1 * math.cos(a1r))
    e = (j[0] + l2 * math.sin(a2r), j[1] + l2 * math.cos(a2r))
    return j, e, a1 + rel


def leg_points(p):
    hipL, hipR = (-28, 6), (28, 6)
    kL, fL, aL = limb(hipL, p['legL'] - p['crouch'] * 28, p['kneeL'] + p['crouch'] * 50, THIGH, SHIN)
    kR, fR, aR = limb(hipR, p['legR'] + p['crouch'] * 28, p['kneeR'] - p['crouch'] * 50, THIGH, SHIN)
    return hipL, kL, fL, aL, hipR, kR, fR, aR


def foot_drop(p):
    """How far below the pelvis the lowest foot sits (to keep feet on the ground)."""
    _, _, fL, _, _, _, fR, _ = leg_points(p)
    return max(fL[1], fR[1]) + 10


def draw_hand(ctx, at, ang, spread, side):
    a = math.radians(ang)
    ux, uy = math.sin(a), math.cos(a)
    palm = (at[0] + ux * 10, at[1] + uy * 10)
    ellipse(ctx, palm[0], palm[1], 11, 9, -a)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    ellipse(ctx, palm[0], palm[1], 8, 6.5, -a)
    ctx.set_source_rgb(*BONE)
    ctx.fill()
    for k in range(4):
        fa = a + math.radians((k - 1.5) * (14 + 26 * spread))
        f0 = (palm[0] + math.sin(fa) * 6, palm[1] + math.cos(fa) * 6)
        f1 = (palm[0] + math.sin(fa) * (19 + 3 * (k in (1, 2))), palm[1] + math.cos(fa) * (19 + 3 * (k in (1, 2))))
        bone(ctx, f0, f1, w=3.5, knob=4.5)


def draw_skull(ctx, f, gaze, blink, t, look=None, hat=None, accent=None, boil=0):
    """Skull centred at its eye line; f = face params."""
    jaw = clamp(f['jaw'])
    # jaw (behind), then the open mouth, then the cranium on top
    jy = 44 + jaw * 46
    ctx.new_path()
    ctx.move_to(-40, jy - 18)
    ctx.curve_to(-42, jy + 22, -22, jy + 36, 0, jy + 36)
    ctx.curve_to(22, jy + 36, 42, jy + 22, 40, jy - 18)
    ctx.close_path()
    ctx.set_source_rgb(*BONE)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4.5)
    ctx.stroke()
    low = jy - 8                                     # lower teeth line
    if low > 44:
        ctx.new_path()
        ctx.move_to(-34, 40)
        ctx.line_to(34, 40)
        ctx.curve_to(36, low, 20, low + 4, 0, low + 4)
        ctx.curve_to(-20, low + 4, -36, low, -34, 40)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#1b0c12'))
        ctx.fill()
        ellipse(ctx, 2, low - 2, 16, min(9, (low - 44) * 0.5 + 2))
        ctx.set_source_rgb(*hexc('#8a3048'))
        ctx.fill()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(2.5)
    for k in range(-3, 4):
        ctx.move_to(k * 8, low)
        ctx.line_to(k * 8, low + 7)
    ctx.stroke()
    ctx.new_path()
    ctx.move_to(-30, low)
    ctx.curve_to(-15, low + f['smile'] * 6, 15, low + f['smile'] * 6, 30, low)
    ctx.stroke()
    # cranium with cheekbones
    j = lambda i: 1.2 * (hash01(i, boil) - 0.5)
    ctx.new_path()
    ctx.move_to(-46 + j(1), 44)
    ctx.curve_to(-58, 30, -74 + j(2), 10, -74, -24)
    ctx.curve_to(-74 + j(3), -84, -36, -108, 0, -108 + j(4))
    ctx.curve_to(36, -108, 74 + j(5), -84, 74, -24)
    ctx.curve_to(74 + j(6), 10, 58, 30, 46, 44)
    ctx.curve_to(30, 50, -30, 50, -46 + j(1), 44)
    ctx.close_path()
    ctx.set_source(radial(ctx, -22, -50, 140, [(0, (1, 1, 0.98, 1)), (0.6, BONE + (1,)), (1, BONE_SHADE + (1,))]))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    # upper teeth row, curved into a smile
    sm = f['smile']
    ctx.set_line_width(2.5)
    ctx.new_path()
    ctx.move_to(-32, 40 - sm * 6)
    ctx.curve_to(-14, 46 + sm * 6, 14, 46 + sm * 6, 32, 40 - sm * 6)
    ctx.stroke()
    for k in range(-3, 4):
        x = k * 8.5
        y = 44 + sm * 6 * (1 - (k / 4) ** 2) - sm * 4
        ctx.move_to(x, y - 9)
        ctx.line_to(x, y)
    ctx.stroke()
    # nose
    ctx.new_path()
    ctx.move_to(0, 28)
    ctx.curve_to(-9, 18, -8, 10, -3, 12)
    ctx.line_to(0, 16)
    ctx.line_to(3, 12)
    ctx.curve_to(8, 10, 9, 18, 0, 28)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    # eye sockets — same expressive eyes as the ghost, carved into bone
    es = f['eye_scale']
    for side, ex in ((-1, -30), (1, 30)):
        draw_eye(ctx, ex + gaze[0] * 3, -18 + gaze[1] * 2, 21 * es, 25 * es, side * -0.12, f, gaze, side, blink,
                 body_col=BONE)
        by = -18 - 25 * es - 12 - f['brow_y'] + (-f['brow_asym'] if side > 0 else f['brow_asym'] * 0.3)
        tilt = f['brow_tilt'] * 1.2
        inner = (ex - side * 16, by - tilt * 0.5)
        outer = (ex + side * 22, by + tilt * 0.5)
        ctx.new_path()
        ctx.move_to(*outer)
        ctx.curve_to(lerp(outer[0], inner[0], 0.35), outer[1] - 6, lerp(outer[0], inner[0], 0.7), inner[1] - 5, *inner)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # a hairline crack, for character
    ctx.new_path()
    ctx.move_to(40, -96)
    ctx.line_to(34, -80)
    ctx.line_to(42, -70)
    ctx.line_to(37, -60)
    ctx.set_line_width(2)
    ctx.stroke()
    if hat:
        draw_hat(ctx, hat, accent, t)


def draw_hat(ctx, kind, accent, t):
    if kind == 'bowler':
        ctx.save()
        ctx.translate(6, -100)
        ctx.rotate(0.16)
        ellipse(ctx, 0, 0, 78, 13)
        ctx.set_source_rgb(*hexc('#3b2350'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.new_path()
        ctx.move_to(-48, -2)
        ctx.curve_to(-50, -70, 50, -70, 48, -2)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#4a2c63'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.rectangle(-48, -16, 96, 12)
        ctx.set_source_rgb(*hexc('#ff8a2a'))
        ctx.fill()
        ctx.restore()
    elif kind == 'cap':
        ctx.save()
        ctx.translate(0, -98)
        ctx.rotate(-0.1)
        ctx.new_path()
        ctx.move_to(-60, 0)
        ctx.curve_to(-60, -46, 60, -46, 60, 0)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#3f6b4a'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ellipse(ctx, 40, 0, 42, 9, 0.05)
        ctx.set_source_rgb(*hexc('#2f5239'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.restore()
    elif kind == 'flower':
        ctx.save()
        ctx.translate(-46, -86)
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            ellipse(ctx, math.cos(a) * 15, math.sin(a) * 15, 13, 9, a)
            ctx.set_source_rgb(*hexc('#e2456a'))
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(2.5)
            ctx.stroke()
        ctx.arc(0, 0, 8, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#ffd36b'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.restore()
    elif kind == 'beanie':
        ctx.save()
        ctx.translate(0, -88)
        ctx.new_path()
        ctx.move_to(-66, 8)
        ctx.curve_to(-66, -62, 66, -62, 66, 8)
        ctx.close_path()
        ctx.set_source_rgb(*hexc('#e8792a'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        for k in range(-4, 5):
            ctx.move_to(k * 13, 6)
            ctx.line_to(k * 11, -38 + abs(k) * 3)
        ctx.set_source_rgba(0.5, 0.2, 0.05, 0.6)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.arc(0, -50, 12, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc('#f3e7c4'))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.restore()


def draw_skeleton(ctx, x, ground, s, p, f, gaze, blink, t, frame, hat=None, accent=None, scarf=None,
                  baton=False, hat_off=None, clip_ground=None):
    """Draw a skeleton standing on `ground` (world y) at x. p = pose, f = face."""
    drop = foot_drop(p)
    py = ground - drop * s + p['dy'] * s
    ctx.save()
    if clip_ground is not None:                         # climbing out of a grave
        ctx.rectangle(-5000, -5000, 10000, clip_ground + 5000)
        ctx.clip()
    ctx.translate(x, py)
    ctx.scale(s * p['flip'], s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    boil = frame // 3
    lean = math.radians(p['lean'])
    shake = p['shake'] * 5 * math.sin(t * 2 * math.pi * 9)

    hipL, kL, fL, aL, hipR, kR, fR, aR = leg_points(p)
    # legs
    for hip, knee, foot, ang in ((hipL, kL, fL, aL), (hipR, kR, fR, aR)):
        bone(ctx, hip, knee, w=10)
        bone(ctx, knee, foot, w=9)
        a = math.radians(ang)
        toe = (foot[0] + (16 if foot[0] > 0 else -16) * math.cos(a), foot[1] + 4)
        bone(ctx, (foot[0], foot[1] + 2), toe, w=8, knob=9)
    # pelvis
    ctx.new_path()
    ctx.move_to(-42, -10)
    ctx.curve_to(-46, 18, -18, 26, 0, 14)
    ctx.curve_to(18, 26, 46, 18, 42, -10)
    ctx.curve_to(20, -2, -20, -2, -42, -10)
    ctx.close_path()
    ctx.set_source_rgb(*BONE)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4.5)
    ctx.stroke()
    # spine (leans, and wiggles when shaking)
    neck = (math.sin(lean) * -NECK_Y + shake * 0.3, NECK_Y * math.cos(lean))
    for k in range(9):
        u = k / 8
        cx = lerp(0, neck[0], u) + shake * math.sin(u * math.pi) * 0.8
        cy = lerp(-6, neck[1], u)
        ellipse(ctx, cx, cy, 9, 7)
        ctx.set_source_rgb(*BONE)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
    # ribcage
    ctx.save()
    rc = (lerp(0, neck[0], 0.62) + shake, lerp(-6, neck[1], 0.62))
    ctx.translate(*rc)
    ctx.rotate(lean * 0.8)
    for k in range(4):
        y = -42 + k * 20
        w = 56 - k * 5 + (6 if k == 1 else 0)
        for col, lw in ((INK, 12), (BONE, 6.5)):
            ctx.set_source_rgb(*col)
            ctx.set_line_width(lw)
            for side in (-1, 1):
                ctx.new_path()
                ctx.move_to(0, y)
                ctx.curve_to(side * w * 0.8, y - 10, side * w, y + 2, side * w * 0.85, y + 14)
                ctx.stroke()
    ctx.rectangle(-5, -50, 10, 70)
    ctx.set_source_rgb(*BONE)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()
    # arms
    shL = (neck[0] - 50, neck[1] + 22)
    shR = (neck[0] + 50, neck[1] + 22)
    hands = {}
    for key, sh in (('L', shL), ('R', shR)):
        el, wr, ang = limb(sh, p['arm' + key], p['elb' + key], UPPER, FORE)
        bone(ctx, sh, el, w=9)
        bone(ctx, el, wr, w=8)
        hands[key] = (wr, ang)
    for key, (wr, ang) in hands.items():
        draw_hand(ctx, wr, ang, p['spread'], -1 if key == 'L' else 1)
    if baton:
        wr, ang = hands['R']
        a = math.radians(ang)
        tip = (wr[0] + math.sin(a + 0.9) * 70, wr[1] + math.cos(a + 0.9) * 70)
        ctx.move_to(wr[0], wr[1])
        ctx.line_to(*tip)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6)
        ctx.stroke()
        ctx.arc(tip[0], tip[1], 5, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
    # scarf at the neck
    if scarf:
        ctx.save()
        ctx.translate(neck[0], neck[1] + 8)
        ctx.new_path()
        ctx.move_to(-30, -6)
        ctx.curve_to(-10, 8, 10, 8, 30, -6)
        ctx.line_to(26, 8)
        ctx.curve_to(10, 18, -10, 18, -26, 8)
        ctx.close_path()
        ctx.set_source_rgb(*scarf)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3.5)
        ctx.stroke()
        wave = 6 * math.sin(t * 3)
        ctx.new_path()
        ctx.move_to(12, 10)
        ctx.curve_to(22, 30, 16 + wave, 46, 26 + wave, 62)
        ctx.line_to(10 + wave, 58)
        ctx.curve_to(6, 40, 8, 28, 2, 12)
        ctx.close_path()
        ctx.set_source_rgb(*scarf)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.stroke()
        ctx.restore()
    # skull
    ctx.save()
    ctx.translate(neck[0], neck[1] - 62)
    ctx.rotate(math.radians(p['head']) + lean * 0.5)
    draw_skull(ctx, f, gaze, blink, t, hat=None if hat_off else hat, accent=accent, boil=boil)
    ctx.restore()
    ctx.restore()
    # a hat blown off its head flies on its own
    if hat and hat_off:
        hx, hy, rot = hat_off
        ctx.save()
        ctx.translate(hx, hy)
        ctx.rotate(rot)
        ctx.scale(s, s)
        ctx.translate(0, 100)
        draw_hat(ctx, hat, accent, t)
        ctx.restore()
    return py


def skull_world(x, ground, s, p):
    """World position of the skull's eye line (for gaze targets and cameras)."""
    drop = foot_drop(p)
    py = ground - drop * s + p['dy'] * s
    lean = math.radians(p['lean'])
    nx, ny = math.sin(lean) * -NECK_Y, NECK_Y * math.cos(lean)
    return x + nx * s * p['flip'], py + (ny - 62) * s


# ── dance vocabulary: each returns a pose for beat position b (in beats) ─────
def pose(**kw):
    return dict(POSE_DEF, **kw)


def hop(b, amt=14):
    return -amt * abs(math.sin(math.pi * b))


def dance(style, b, seed=0, u=0.0):
    """b: beats since the start of the section; u: 0..1 progress for one-shot moves."""
    ph = b % 1.0
    two = b % 2.0
    sway = math.sin(math.pi * b)
    if style == 'idle':
        return pose(dy=1.5 * math.sin(b * 1.3 + seed), head=3 * math.sin(b * 0.7 + seed),
                    armL=-12 + 3 * math.sin(b * 0.9 + seed), armR=12 - 3 * math.sin(b * 0.8 + seed))
    if style == 'groove':
        s = 1 if two < 1 else -1
        return pose(dy=hop(b, 10), crouch=0.25 * abs(math.cos(math.pi * b)), lean=5 * s * smooth(ph * 2),
                    head=-6 * s, armL=-40 + 25 * sway, elbL=-60, armR=40 + 25 * sway, elbR=60,
                    legL=-8 - 6 * (s > 0), legR=8 + 6 * (s < 0))
    if style == 'conduct':
        p = dance('groove', b, seed)
        p.update(armR=120 + 35 * math.sin(2 * math.pi * b), elbR=-50 + 30 * math.cos(2 * math.pi * b))
        return p
    if style == 'clap':
        c = smooth(1 - abs(ph - 0.5) * 2) if True else 0
        return pose(dy=hop(b, 8), crouch=0.2, armL=-70 + 55 * c, elbL=-60 - 40 * c, armR=70 - 55 * c,
                    elbR=60 + 40 * c, head=4 * math.sin(math.pi * b), kneeL=-10 * c, kneeR=10 * c)
    if style == 'point_up':
        return pose(dy=hop(b, 6), armR=170, elbR=-5, armL=-30, elbL=-40, head=-14, lean=-4)
    if style == 'shimmy':
        return pose(crouch=0.45 + 0.1 * math.sin(2 * math.pi * b), shake=1.0, armL=-60, elbL=-70, armR=60,
                    elbR=70, spread=0.6, head=6 * math.sin(4 * math.pi * b))
    if style == 'kick':
        k = math.sin(math.pi * ph)
        left = int(b) % 2 == 0
        return pose(dy=hop(b, 6), legL=-5 - (70 * k if left else 0), kneeL=(20 * k if left else 0),
                    legR=5 + (70 * k if not left else 0), kneeR=(-20 * k if not left else 0),
                    armL=-120, elbL=-30, armR=120, elbR=30, lean=(6 if left else -6) * k)
    if style == 'spin':
        # one quick twirl per bar (beats 1-2), facing front the rest of the time
        u = clamp(((b % 4) - 0.9) / 1.1)
        fl = math.cos(2 * math.pi * smooth(u))
        if abs(fl) < 0.12:
            fl = 0.12 if fl >= 0 else -0.12
        return pose(dy=hop(b, 18), flip=fl, armL=-100, armR=100, elbL=-20, elbR=20)
    if style == 'jazz':
        return pose(dy=-6, crouch=0.3, armL=-130, elbL=10, armR=130, elbR=-10, spread=1.0,
                    head=5 * math.sin(2 * math.pi * b * 2), shake=0.25, legL=-18, legR=18)
    if style == 'dust':
        d = math.sin(2 * math.pi * b * 2)
        return pose(head=8, armR=-40 + 25 * d, elbR=-120, armL=-15, elbL=10, lean=-3)
    if style == 'polish':
        d = math.sin(2 * math.pi * b * 2)
        return pose(lean=-38, crouch=0.35, armL=-5 + 12 * d, elbL=-10, armR=8 - 12 * d, elbR=10, head=10)
    if style == 'tap':
        k = max(0.0, math.sin(2 * math.pi * b))
        return pose(legR=5 + 40 * k, kneeR=-30 * k, armL=-35, elbL=-90, armR=35, elbR=90, dy=hop(b, 4),
                    head=6 * math.sin(math.pi * b))
    if style == 'sway':
        return pose(lean=10 * math.sin(math.pi * b / 2), armL=-150 + 20 * math.sin(math.pi * b / 2),
                    armR=150 + 20 * math.sin(math.pi * b / 2), elbL=10, elbR=-10, head=-8 * math.sin(math.pi * b / 2))
    if style == 'beckon':
        c = math.sin(2 * math.pi * b * 1.5)
        return pose(armR=60, elbR=70 + 50 * c, armL=-14, head=-8, lean=-4, dy=hop(b, 4))
    if style == 'climb':
        rise = smooth(u)
        reach = math.sin(2 * math.pi * b)
        return pose(rise=rise, armL=-160 + 20 * reach, armR=160 - 20 * reach, elbL=-10, elbR=10, head=-10 * (1 - rise))
    if style == 'listen':
        return pose(lean=-6, head=-10, armL=-20, armR=40, elbR=110, dy=1.5 * math.sin(b * 0.6 + seed))
    if style == 'cheer':
        return pose(dy=hop(b, 22), armL=-150 + 20 * math.sin(2 * math.pi * b), armR=150 - 20 * math.sin(2 * math.pi * b),
                    spread=0.8, elbL=-10, elbR=10)
    if style == 'hat_hold':
        return pose(armL=-150, elbL=-60, armR=150, elbR=60, crouch=0.2, lean=-8, head=-12)
    if style == 'shrug':
        return pose(armL=-60, elbL=-120, armR=60, elbR=120, head=10, dy=-4)
    return pose()


def blend_pose(a, b, w):
    return {k: lerp(a[k], b[k], w) for k in POSE_DEF}
