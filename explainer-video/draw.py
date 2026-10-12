"""Cairo drawing helpers and the cartoon character rig."""
import math

import cairo

W, H = 1080, 1920
INK = (0.13, 0.12, 0.20)
WHITE = (1, 1, 1)
FONT = "Fredoka"


# ------------------------------------------------------------------ math helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_out_back(t, s=1.7):
    t = clamp(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ramp(x, a, b):
    """0 before a, 1 after b, smooth in between."""
    if b == a:
        return 1.0 if x >= b else 0.0
    return smooth((x - a) / (b - a))


def keyed(t, keys, ease=smooth):
    """Interpolate numbers or tuples over [(time, value), ...]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]


def mix(c1, c2, k):
    return tuple(lerp(a, b, k) for a, b in zip(c1, c2))


def shade(c, k):
    """k<0 darker, k>0 lighter."""
    return mix(c, (0, 0, 0), -k) if k < 0 else mix(c, (1, 1, 1), k)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ------------------------------------------------------------------ primitives
def rgba(ctx, c, a=1.0):
    if len(c) == 4:
        ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)
    else:
        ctx.set_source_rgba(c[0], c[1], c[2], a)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def fill_stroke(ctx, fill, stroke=INK, lw=5, a=1.0):
    if fill is not None:
        rgba(ctx, fill, a)
        if stroke is not None:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke is not None:
        rgba(ctx, stroke, a)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def vgrad(ctx, y0, y1, stops):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(c if len(c) == 4 else (*c, 1)))
    return g


def paint_bg(ctx, top, bottom):
    ctx.set_source(vgrad(ctx, 0, H, [(0, top), (1, bottom)]))
    ctx.paint()


def glow(ctx, x, y, r, c, a=0.5):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *c[:3], a)
    g.add_color_stop_rgba(1, *c[:3], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


# ------------------------------------------------------------------ text
def font(ctx, size, bold=True, family=FONT):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_w(ctx, s):
    return ctx.text_extents(s).x_advance


def wrap(ctx, text, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(ctx, trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text(ctx, s, x, y, size, color=INK, align="center", bold=True, outline=None,
         olw=10, a=1.0, family=FONT, shadow=None):
    font(ctx, size, bold, family)
    w = text_w(ctx, s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow:
        ctx.move_to(x + shadow[0], y + shadow[1])
        ctx.text_path(s)
        rgba(ctx, shadow[2], a * shadow[3])
        ctx.fill()
    if outline:
        ctx.move_to(x, y)
        ctx.text_path(s)
        rgba(ctx, outline, a)
        ctx.set_line_width(olw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    ctx.move_to(x, y)
    ctx.text_path(s)
    rgba(ctx, color, a)
    ctx.fill()
    return w


def text_block(ctx, s, x, y, size, maxw, color=INK, lh=1.18, align="center", **kw):
    font(ctx, size, kw.get("bold", True))
    lines = wrap(ctx, s, maxw)
    for i, ln in enumerate(lines):
        text(ctx, ln, x, y + i * size * lh, size, color, align, **kw)
    return len(lines)


# ------------------------------------------------------------------ emotions
BASE = dict(brow_y=0.0, brow_tilt=0.0, brow_asym=0.0, lid_top=0.14, lid_tilt=0.0,
            lid_bot=0.0, pupil=1.0, eye_scale=1.0, smile=0.2, mouth_w=1.0, mouth_skew=0.0,
            blush=0.0, sweat=0.0, tear=0.0, shake=0.0, open_bias=0.0, open_round=0.0,
            sparkle=0.0)

EMO = {
    "neutral": {},
    "happy": dict(brow_y=0.18, lid_bot=0.28, smile=0.85, pupil=1.08, blush=0.3, sparkle=0.6),
    "excited": dict(brow_y=0.35, lid_bot=0.22, smile=1.0, pupil=1.12, eye_scale=1.08,
                    open_bias=0.25, blush=0.4, sparkle=1.0),
    "laugh": dict(brow_y=0.3, lid_top=0.25, lid_bot=0.55, smile=1.0, mouth_w=1.25,
                  open_bias=0.45, blush=0.4),
    "smug": dict(brow_y=0.05, brow_tilt=-0.25, brow_asym=0.5, lid_top=0.45, lid_bot=0.22,
                 smile=0.6, mouth_skew=0.7),
    "fake_nice": dict(brow_y=0.4, lid_top=0.05, lid_bot=0.45, smile=1.0, mouth_w=1.2,
                      blush=0.2),
    "sad": dict(brow_tilt=0.75, brow_y=0.05, lid_top=0.32, lid_tilt=0.45, smile=-0.65,
                pupil=1.18, sparkle=0.4),
    "hurt": dict(brow_tilt=0.85, brow_y=0.15, lid_top=0.2, lid_tilt=0.35, smile=-0.5,
                 pupil=1.25, tear=0.6, sparkle=0.8, mouth_w=0.85),
    "sympathetic": dict(brow_tilt=0.5, brow_y=0.12, lid_top=0.22, lid_bot=0.12, smile=0.15,
                        pupil=1.12),
    "angry": dict(brow_tilt=-0.8, brow_y=-0.2, lid_top=0.3, lid_tilt=-0.45, smile=-0.6),
    "annoyed": dict(brow_tilt=-0.45, brow_y=-0.08, lid_top=0.48, lid_tilt=-0.15, smile=-0.35,
                    mouth_skew=-0.4),
    "dismissive": dict(brow_y=0.12, brow_asym=0.6, lid_top=0.55, smile=-0.2, mouth_skew=0.5,
                       pupil=0.9),
    "bored": dict(lid_top=0.5, brow_y=-0.05, smile=-0.1, mouth_w=0.8, pupil=0.9),
    "surprised": dict(brow_y=0.5, eye_scale=1.16, pupil=0.72, lid_top=0.0, smile=0.0,
                      open_bias=0.35, open_round=1.0),
    "confused": dict(brow_asym=0.75, brow_tilt=0.2, smile=-0.15, mouth_skew=-0.5, pupil=0.95,
                     mouth_w=0.8),
    "worried": dict(brow_tilt=0.7, brow_y=0.18, smile=-0.35, pupil=0.95, sweat=0.7,
                    mouth_w=0.85),
    "scared": dict(brow_tilt=0.8, brow_y=0.38, eye_scale=1.12, pupil=0.66, smile=-0.55,
                   shake=0.6, sweat=1.0, lid_top=0.0),
    "nervous": dict(brow_tilt=0.55, brow_y=0.15, smile=0.35, mouth_w=0.9, sweat=0.7,
                    lid_bot=0.1, pupil=0.95),
    "determined": dict(brow_tilt=-0.35, brow_y=-0.06, lid_top=0.2, lid_bot=0.12, smile=0.3),
    "calm": dict(lid_top=0.36, lid_bot=0.12, smile=0.35, brow_y=0.05),
    "relieved": dict(lid_top=0.3, lid_bot=0.15, smile=0.6, brow_tilt=0.3, brow_y=0.1,
                     blush=0.25),
    "proud": dict(brow_y=0.12, lid_top=0.12, lid_bot=0.26, smile=0.85, blush=0.25),
    "confident": dict(brow_y=0.1, brow_tilt=-0.15, lid_top=0.12, lid_bot=0.25, smile=0.75),
    "caring": dict(brow_tilt=0.35, brow_y=0.12, lid_bot=0.3, smile=0.65, blush=0.35,
                   sparkle=0.6),
    "thinking": dict(brow_asym=0.5, lid_top=0.22, smile=0.0, mouth_skew=0.5, mouth_w=0.75),
    "curious": dict(brow_y=0.3, brow_asym=0.3, eye_scale=1.05, smile=0.35, pupil=1.08),
    "hopeful": dict(brow_y=0.3, brow_tilt=0.2, smile=0.6, pupil=1.12, sparkle=1.0,
                    eye_scale=1.04),
    "realize": dict(brow_y=0.42, eye_scale=1.1, pupil=0.9, smile=0.35, open_bias=0.12,
                    open_round=0.6),
    "serious": dict(brow_tilt=-0.1, brow_y=-0.02, lid_top=0.2, smile=0.0),
}


def emo_params(name):
    p = dict(BASE)
    p.update(EMO.get(name or "neutral", {}))
    return p


def blend_params(a, b, k):
    return {key: lerp(a[key], b[key], k) for key in a}


# ------------------------------------------------------------------ arm poses
# (upper angle, elbow bend) per arm in degrees; 0 = hanging straight down,
# positive = swinging outward / upward.
POSES = {
    "down": ((14, 4), (14, 4)),
    "relax": ((22, -12), (22, -12)),
    "wave": ((20, 4), (150, 25)),
    "wave2": ((150, 25), (150, 25)),
    "point": ((14, 4), (82, 8)),
    "point_l": ((82, 8), (14, 4)),
    "shrug": ((55, 95), (55, 95)),
    "cheer": ((155, 12), (155, 12)),
    "hips": ((48, -95), (48, -95)),
    "think": ((14, 4), (22, 172)),
    "hold": ((22, -118), (22, -118)),
    "type": ((30, -100), (30, -100)),
    "cover": ((28, 168), (28, 168)),
    "open": ((48, 45), (48, 45)),
    "present": ((14, 4), (60, 50)),
    "cross": ((26, -112), (30, -118)),
    "heart": ((24, -128), (24, -128)),
    "fist": ((14, 4), (40, 120)),
    "run": ((60, 40), (-30, 60)),
    "carry": ((30, -95), (30, -95)),
    "phone": ((14, 4), (26, -150)),
    "headphones": ((80, 120), (80, 120)),
}


def pose_lerp(p1, p2, k):
    a, b = POSES[p1] if isinstance(p1, str) else p1, POSES[p2] if isinstance(p2, str) else p2
    return tuple(tuple(lerp(x, y, k) for x, y in zip(sa, sb)) for sa, sb in zip(a, b))


# ------------------------------------------------------------------ characters
CHARS = {
    "sam": dict(color=(0.27, 0.76, 0.69), w=230, h=330, eye=34, gap=0.21, acc=("sprout",),
                iris=(0.32, 0.22, 0.14)),
    "marsh": dict(color=(0.56, 0.53, 0.72), w=250, h=430, eye=30, gap=0.2,
                  acc=("hair", "tie", "glasses"), iris=(0.25, 0.25, 0.32)),
    "ned": dict(color=(0.64, 0.84, 0.32), w=205, h=290, eye=33, gap=0.22, acc=("hood",),
                iris=(0.45, 0.28, 0.12)),
    "priya": dict(color=(0.98, 0.6, 0.46), w=220, h=320, eye=33, gap=0.21, acc=("bun",),
                  iris=(0.30, 0.18, 0.10)),
    "lumi": dict(color=(1.0, 0.83, 0.30), r=78, eye=24, gap=0.36, acc=(), iris=(0.45, 0.27, 0.08)),
    "extra1": dict(color=(0.55, 0.70, 0.92), w=200, h=280, eye=28, gap=0.21, acc=(),
                   iris=(0.2, 0.2, 0.3)),
    "extra2": dict(color=(0.93, 0.75, 0.45), w=210, h=300, eye=28, gap=0.21, acc=("bun",),
                   iris=(0.2, 0.2, 0.3)),
    "extra3": dict(color=(0.80, 0.62, 0.85), w=200, h=290, eye=28, gap=0.21, acc=(),
                   iris=(0.2, 0.2, 0.3)),
}


class Pose:
    """Everything that varies per frame for one character."""

    def __init__(self, emo=None, mouth=0.0, rnd=0.0, look=(0.0, 0.0), blink=0.0,
                 arms="down", walk=0.0, walk_amt=0.0, t=0.0, props=(), squash=0.0, alpha=1.0,
                 flip=False, tilt=0.0, hold_item=None):
        self.emo = emo or emo_params("neutral")
        self.mouth, self.rnd, self.look, self.blink = mouth, rnd, look, blink
        self.arms = arms
        self.walk, self.walk_amt, self.t = walk, walk_amt, t
        self.props, self.squash, self.alpha, self.flip, self.tilt = props, squash, alpha, flip, tilt
        self.hold_item = hold_item


def bean_path(ctx, w, h):
    ctx.move_to(0, 0)
    ctx.curve_to(w * 0.42, 0, w * 0.5, -h * 0.1, w * 0.5, -h * 0.38)
    ctx.curve_to(w * 0.5, -h * 0.76, w * 0.36, -h, 0, -h)
    ctx.curve_to(-w * 0.36, -h, -w * 0.5, -h * 0.76, -w * 0.5, -h * 0.38)
    ctx.curve_to(-w * 0.5, -h * 0.1, -w * 0.42, 0, 0, 0)
    ctx.close_path()


def draw_eye(ctx, cx, cy, rx, ry, side, p, body, look, blink, iris_c, lw):
    """side = -1 for the character's right eye (screen left), +1 for the other."""
    ctx.save()
    ctx.translate(cx, cy)
    ellipse(ctx, 0, 0, rx, ry)
    rgba(ctx, WHITE)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    # iris + pupil
    lx = clamp(look[0], -1, 1) * rx * 0.38
    ly = clamp(look[1], -1, 1) * ry * 0.32
    ir = min(rx, ry) * 0.66 * (0.85 + 0.15 * p["pupil"])
    ellipse(ctx, lx, ly, ir, ir * 1.05)
    rgba(ctx, iris_c)
    ctx.fill()
    pr = ir * 0.62 * p["pupil"]
    ellipse(ctx, lx, ly, pr, pr * 1.05)
    rgba(ctx, (0.06, 0.05, 0.1))
    ctx.fill()
    # highlights (bigger when "sparkle" is high: the cute glossy-eye look)
    hs = 1 + 0.5 * p["sparkle"]
    ellipse(ctx, lx + ir * 0.35, ly - ir * 0.4, ir * 0.3 * hs, ir * 0.3 * hs)
    rgba(ctx, WHITE, 0.95)
    ctx.fill()
    ellipse(ctx, lx - ir * 0.35, ly + ir * 0.38, ir * 0.13 * hs, ir * 0.13 * hs)
    rgba(ctx, WHITE, 0.85)
    ctx.fill()
    # upper lid
    top = clamp(max(p["lid_top"], blink), 0, 1)
    ylid = -ry + 2.05 * ry * top
    tilt = p["lid_tilt"] * ry * 0.6
    y_out = ylid + tilt
    y_in = ylid - tilt
    x_out, x_in = side * rx * 1.1, -side * rx * 1.1
    lidc = shade(body, -0.12)
    ctx.move_to(x_out, -ry * 1.6)
    ctx.line_to(x_out, y_out)
    ctx.curve_to(x_out * 0.4, y_out + ry * 0.18 * (1 - top), x_in * 0.4,
                 y_in + ry * 0.18 * (1 - top), x_in, y_in)
    ctx.line_to(x_in, -ry * 1.6)
    ctx.close_path()
    rgba(ctx, lidc)
    ctx.fill()
    if top > 0.02:
        ctx.move_to(x_out, y_out)
        ctx.curve_to(x_out * 0.4, y_out + ry * 0.18 * (1 - top), x_in * 0.4,
                     y_in + ry * 0.18 * (1 - top), x_in, y_in)
        rgba(ctx, INK)
        ctx.set_line_width(lw * 1.1)
        ctx.stroke()
    # lower lid (happy squint pushes it up into a curve)
    bot = clamp(p["lid_bot"], 0, 0.9) * (1 - top * 0.5)
    if bot > 0.01:
        yb = ry - 2 * ry * bot
        ctx.move_to(-rx * 1.2, ry * 1.6)
        ctx.line_to(-rx * 1.2, yb + ry * 0.35 * bot)
        ctx.curve_to(-rx * 0.4, yb - ry * 0.25 * bot, rx * 0.4, yb - ry * 0.25 * bot,
                     rx * 1.2, yb + ry * 0.35 * bot)
        ctx.line_to(rx * 1.2, ry * 1.6)
        ctx.close_path()
        rgba(ctx, lidc)
        ctx.fill()
    ctx.restore()
    ellipse(ctx, 0, 0, rx, ry)
    rgba(ctx, INK)
    ctx.set_line_width(lw)
    ctx.stroke()
    ctx.restore()


def draw_brow(ctx, cx, cy, rx, ry, side, p, lw, color=INK):
    base = cy - ry * 1.38 - p["brow_y"] * ry * 0.85 - p["brow_asym"] * side * ry * 0.32
    xi, xo = cx - side * rx * 0.85, cx + side * rx * 0.95
    yi = base - p["brow_tilt"] * ry * 0.42
    yo = base + p["brow_tilt"] * ry * 0.12
    ctx.move_to(xi, yi)
    ctx.curve_to(lerp(xi, xo, 0.3), min(yi, yo) - ry * 0.18, lerp(xi, xo, 0.7),
                 min(yi, yo) - ry * 0.18, xo, yo + ry * 0.05)
    rgba(ctx, color)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def draw_mouth(ctx, mx, my, size, p, mouth, rnd, lw):
    k = p["smile"]
    o = clamp(max(mouth, p["open_bias"]), 0, 1)
    r = clamp(max(rnd * clamp(mouth * 3), p["open_round"] if mouth < 0.15 else rnd), 0, 1)
    Wm = size * 1.7 * p["mouth_w"]
    skew = p["mouth_skew"]
    if o < 0.07:
        yl = -k * Wm * 0.2 + skew * Wm * 0.06
        yr = -k * Wm * 0.2 - skew * Wm * 0.16
        ctx.move_to(mx - Wm / 2, my + yl)
        ctx.curve_to(mx - Wm / 4, my + k * Wm * 0.22, mx + Wm / 4, my + k * Wm * 0.22,
                     mx + Wm / 2, my + yr)
        rgba(ctx, INK)
        ctx.set_line_width(lw * 1.25)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        return
    w = Wm * (1 - 0.42 * r) * (1 + 0.12 * max(k, 0))
    h = Wm * (0.12 + 0.7 * o) * (0.8 + 0.35 * r)
    yc = -k * Wm * 0.14
    yl, yr = yc + skew * Wm * 0.05, yc - skew * Wm * 0.14
    top_c = -h * (0.22 + 0.25 * r) - max(-k, 0) * h * 0.4
    bot_c = h * (0.95 + 0.2 * max(k, 0))
    ctx.save()
    ctx.translate(mx, my)
    ctx.move_to(-w / 2, yl)
    ctx.curve_to(-w * 0.3, top_c, w * 0.3, top_c, w / 2, yr)
    ctx.curve_to(w * 0.38, bot_c, -w * 0.38, bot_c, -w / 2, yl)
    ctx.close_path()
    path = ctx.copy_path()
    rgba(ctx, (0.33, 0.08, 0.13))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    # tongue
    ellipse(ctx, 0, bot_c * 0.78, w * 0.32, h * 0.38)
    rgba(ctx, (0.95, 0.45, 0.52))
    ctx.fill()
    # teeth
    if h > size * 0.35:
        ctx.rectangle(-w, top_c - h, 2 * w, h * 1.1 + h * 0.12)
        rgba(ctx, WHITE)
        ctx.fill()
    ctx.restore()
    ctx.new_path()
    ctx.append_path(path)
    rgba(ctx, INK)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.restore()


def draw_arm(ctx, sx, sy, side, a1, a2, seg, thick, color, flip_hand=False):
    d1 = math.radians(a1)
    d2 = math.radians(a1 + a2)
    ex, ey = sx + side * math.sin(d1) * seg, sy + math.cos(d1) * seg
    hx, hy = ex + side * math.sin(d2) * seg, ey + math.cos(d2) * seg
    for wdt, col in ((thick + 9, INK), (thick, color)):
        ctx.move_to(sx, sy)
        ctx.curve_to(lerp(sx, ex, 0.6), lerp(sy, ey, 0.6), ex, ey, lerp(ex, hx, 0.5),
                     lerp(ey, hy, 0.5))
        ctx.line_to(hx, hy)
        rgba(ctx, col)
        ctx.set_line_width(wdt)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    ellipse(ctx, hx, hy, thick * 0.78, thick * 0.78)
    fill_stroke(ctx, color, INK, 4.5)
    return hx, hy


def draw_feet(ctx, w, walk, amt, color):
    for side in (-1, 1):
        ph = walk + (0 if side < 0 else math.pi)
        dx = math.sin(ph) * w * 0.16 * amt
        lift = max(0.0, math.cos(ph)) * w * 0.1 * amt
        ellipse(ctx, side * w * 0.2 + dx, -lift - 2, w * 0.17, w * 0.085)
        fill_stroke(ctx, shade(color, -0.35), INK, 4.5)


def draw_headphones(ctx, w, h, eye_y):
    ctx.arc(0, eye_y + h * 0.02, w * 0.56, math.pi * 1.08, math.pi * 1.92)
    rgba(ctx, INK)
    ctx.set_line_width(26)
    ctx.stroke()
    ctx.arc(0, eye_y + h * 0.02, w * 0.56, math.pi * 1.08, math.pi * 1.92)
    rgba(ctx, (0.25, 0.27, 0.35))
    ctx.set_line_width(16)
    ctx.stroke()
    for s in (-1, 1):
        rrect(ctx, s * w * 0.53 - 26, eye_y - 10, 52, 92, 22)
        fill_stroke(ctx, (0.92, 0.32, 0.38), INK, 5)
        rrect(ctx, s * w * 0.53 - 14 + s * 6, eye_y + 6, 22, 60, 10)
        rgba(ctx, (1, 1, 1), 0.35)
        ctx.fill()


def draw_char(ctx, name, x, y, scale, pose):
    spec = CHARS[name]
    if name == "lumi":
        return draw_lumi(ctx, x, y, scale, pose)
    c = spec["color"]
    p = pose.emo
    w, h = spec["w"], spec["h"]
    t = pose.t
    sq = 0.012 * math.sin(t * 2.3 + sum(map(ord, name)) % 7) + pose.squash - pose.mouth * 0.012
    bob = -abs(math.sin(pose.walk)) * w * 0.05 * pose.walk_amt
    shake = math.sin(t * 57) * p["shake"] * 4
    ctx.save()
    ctx.translate(x + shake, y + bob)
    ctx.scale(scale, scale)
    if pose.flip:
        ctx.scale(-1, 1)
    ctx.rotate(pose.tilt)
    if pose.alpha < 1:
        ctx.push_group()
    # shadow
    ellipse(ctx, 0, 4, w * 0.52, w * 0.09)
    rgba(ctx, (0, 0, 0), 0.16)
    ctx.fill()
    draw_feet(ctx, w, pose.walk, pose.walk_amt, c)
    bw, bh = w * (1 + sq), h * (1 - sq)
    ctx.translate(0, -w * 0.05)
    # hood goes behind the body
    if "hood" in spec["acc"]:
        hood = shade(c, -0.42)
        ctx.save()
        ctx.scale(1.12, 1.05)
        bean_path(ctx, bw, bh)
        ctx.restore()
        fill_stroke(ctx, hood, INK, 5.5)
    if "bun" in spec["acc"]:
        hair = (0.30, 0.17, 0.12)
        ellipse(ctx, 0, -bh - 18, 46, 40)
        fill_stroke(ctx, hair, INK, 5)
    # body
    bean_path(ctx, bw, bh)
    g = cairo.LinearGradient(-bw * 0.4, -bh, bw * 0.4, 0)
    g.add_color_stop_rgb(0, *shade(c, 0.18))
    g.add_color_stop_rgb(1, *shade(c, -0.08))
    ctx.set_source(g)
    ctx.fill_preserve()
    rgba(ctx, INK)
    ctx.set_line_width(5.5)
    ctx.stroke()
    # belly highlight
    ellipse(ctx, 0, -bh * 0.28, bw * 0.3, bh * 0.2)
    rgba(ctx, WHITE, 0.16)
    ctx.fill()
    if "hood" in spec["acc"]:
        # face opening
        ellipse(ctx, 0, -bh * 0.62, bw * 0.43, bh * 0.33)
        fill_stroke(ctx, shade(c, 0.1), shade(c, -0.55), 5)
        for s in (-1, 1):  # drawstrings
            ctx.move_to(s * bw * 0.16, -bh * 0.3)
            ctx.line_to(s * bw * 0.18, -bh * 0.13)
            rgba(ctx, WHITE)
            ctx.set_line_width(6)
            ctx.stroke()
            ellipse(ctx, s * bw * 0.18, -bh * 0.12, 6, 7)
            fill_stroke(ctx, WHITE, INK, 2.5)
    if "hair" in spec["acc"]:
        ctx.save()
        bean_path(ctx, bw, bh)
        ctx.clip()
        ctx.move_to(-bw, -bh * 0.83)
        ctx.curve_to(-bw * 0.2, -bh * 0.92, bw * 0.15, -bh * 0.8, bw, -bh * 0.9)
        ctx.line_to(bw, -bh * 1.2)
        ctx.line_to(-bw, -bh * 1.2)
        ctx.close_path()
        rgba(ctx, (0.22, 0.2, 0.28))
        ctx.fill()
        ctx.restore()
        bean_path(ctx, bw, bh)
        rgba(ctx, INK)
        ctx.set_line_width(5.5)
        ctx.stroke()
    if "bun" in spec["acc"]:
        ctx.save()
        bean_path(ctx, bw, bh)
        ctx.clip()
        ctx.move_to(-bw, -bh * 0.84)
        ctx.curve_to(-bw * 0.3, -bh * 0.78, -bw * 0.1, -bh * 0.95, bw * 0.05, -bh * 0.84)
        ctx.curve_to(bw * 0.25, -bh * 0.92, bw * 0.4, -bh * 0.8, bw, -bh * 0.82)
        ctx.line_to(bw, -bh * 1.2)
        ctx.line_to(-bw, -bh * 1.2)
        ctx.close_path()
        rgba(ctx, (0.30, 0.17, 0.12))
        ctx.fill()
        ctx.restore()
        bean_path(ctx, bw, bh)
        rgba(ctx, INK)
        ctx.set_line_width(5.5)
        ctx.stroke()
    if "sprout" in spec["acc"]:
        ctx.move_to(0, -bh + 2)
        ctx.curve_to(2, -bh - 18, -4, -bh - 30, 4, -bh - 40)
        rgba(ctx, INK)
        ctx.set_line_width(6)
        ctx.stroke()
        for s, ang in ((-1, -0.5), (1, 0.4)):
            ctx.save()
            ctx.translate(4, -bh - 38)
            ctx.rotate(ang)
            ctx.move_to(0, 0)
            ctx.curve_to(s * 14, -18, s * 34, -14, s * 40, 0)
            ctx.curve_to(s * 30, 10, s * 12, 10, 0, 0)
            fill_stroke(ctx, (0.45, 0.82, 0.38), INK, 4.5)
            ctx.restore()
    if "badge" in pose.props:
        ctx.move_to(-bw * 0.14, -bh * 0.38)
        ctx.line_to(0, -bh * 0.22)
        ctx.line_to(bw * 0.14, -bh * 0.38)
        rgba(ctx, (0.25, 0.4, 0.85))
        ctx.set_line_width(6)
        ctx.stroke()
        rrect(ctx, -26, -bh * 0.23, 52, 62, 8)
        fill_stroke(ctx, WHITE, INK, 4)
        ellipse(ctx, 0, -bh * 0.23 + 22, 10, 10)
        rgba(ctx, c)
        ctx.fill()
        ctx.rectangle(-15, -bh * 0.23 + 40, 30, 5)
        rgba(ctx, (0.6, 0.6, 0.7))
        ctx.fill()
    if "tie" in spec["acc"]:
        ty = -bh * 0.4
        ctx.move_to(-30, ty - 14)
        ctx.line_to(0, ty + 2)
        ctx.line_to(30, ty - 14)
        ctx.line_to(30, ty + 4)
        ctx.line_to(0, ty + 12)
        ctx.line_to(-30, ty + 4)
        ctx.close_path()
        fill_stroke(ctx, WHITE, INK, 4)
        ctx.move_to(-11, ty + 4)
        ctx.line_to(11, ty + 4)
        ctx.line_to(17, ty + 90)
        ctx.line_to(0, ty + 112)
        ctx.line_to(-17, ty + 90)
        ctx.close_path()
        fill_stroke(ctx, (0.85, 0.25, 0.3), INK, 4.5)
    # face
    er = spec["eye"] * p["eye_scale"]
    ey = -bh * (0.69 if "hood" not in spec["acc"] else 0.66)
    gap = bw * spec["gap"]
    lw = 4.5
    look = pose.look
    face_dx = look[0] * bw * 0.035
    face_dy = look[1] * bh * 0.012
    for side in (-1, 1):
        ex = side * gap + face_dx
        draw_eye(ctx, ex, ey + face_dy, er * 0.84, er * 1.04, side, p, c, look, pose.blink,
                 spec["iris"], lw)
    if "glasses" in spec["acc"]:
        for side in (-1, 1):
            ex = side * gap + face_dx
            rrect(ctx, ex - er * 1.15, ey + face_dy - er * 1.1, er * 2.3, er * 2.15, 14)
            rgba(ctx, (0.15, 0.15, 0.22))
            ctx.set_line_width(6)
            ctx.stroke()
        ctx.move_to(-gap + face_dx + er * 1.15, ey + face_dy - er * 0.2)
        ctx.line_to(gap + face_dx - er * 1.15, ey + face_dy - er * 0.2)
        ctx.set_line_width(6)
        ctx.stroke()
    brow_col = INK if "hair" not in spec["acc"] else (0.22, 0.2, 0.28)
    for side in (-1, 1):
        draw_brow(ctx, side * gap + face_dx, ey + face_dy - (er * 0.25 if "glasses" in spec["acc"] else 0),
                  er * 0.84, er * 1.04, side, p, er * 0.3, brow_col)
    # blush, tears, sweat
    if p["blush"] > 0.02:
        for side in (-1, 1):
            ellipse(ctx, side * (gap + er * 0.55) + face_dx, ey + er * 1.45, er * 0.55, er * 0.28)
            rgba(ctx, (1.0, 0.45, 0.5), 0.45 * p["blush"])
            ctx.fill()
    mx, my = face_dx, ey + er * 1.85 + face_dy
    draw_mouth(ctx, mx, my, er, p, pose.mouth, pose.rnd, lw)
    if p["tear"] > 0.05:
        for side in (-1, 1):
            tx = side * gap + face_dx + side * er * 0.3
            ty = ey + er * 1.0 + (t * 30 % 40) * p["tear"]
            ctx.move_to(tx, ty - 14)
            ctx.curve_to(tx + 9, ty, tx + 9, ty + 12, tx, ty + 12)
            ctx.curve_to(tx - 9, ty + 12, tx - 9, ty, tx, ty - 14)
            fill_stroke(ctx, (0.55, 0.8, 1.0), INK, 3, a=p["tear"])
    if p["sweat"] > 0.05:
        sx, sy = bw * 0.36, -bh * 0.84 + math.sin(t * 3) * 3
        ctx.move_to(sx, sy - 22)
        ctx.curve_to(sx + 14, sy, sx + 14, sy + 16, sx, sy + 16)
        ctx.curve_to(sx - 14, sy + 16, sx - 14, sy, sx, sy - 22)
        fill_stroke(ctx, (0.6, 0.85, 1.0), INK, 3.5, a=p["sweat"])
    # arms
    arms = POSES[pose.arms] if isinstance(pose.arms, str) else pose.arms
    seg = bh * 0.2
    thick = bw * 0.085
    hands = []
    for i, side in enumerate((-1, 1)):
        a1, a2 = arms[i]
        if arms is not None and pose.walk_amt > 0:
            a1 += math.sin(pose.walk + (0 if side < 0 else math.pi)) * 25 * pose.walk_amt
        hands.append(draw_arm(ctx, side * bw * 0.43, -bh * 0.42, side, a1, a2, seg, thick, c))
    if "headphones" in pose.props:
        draw_headphones(ctx, bw, bh, ey - er * 0.6)
    if pose.hold_item:
        pose.hold_item(ctx, hands, bw, bh)
    if pose.alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(pose.alpha)
    ctx.restore()
    return hands


def draw_lumi(ctx, x, y, scale, pose):
    spec = CHARS["lumi"]
    c = spec["color"]
    p = pose.emo
    t = pose.t
    r = spec["r"]
    y = y + math.sin(t * 2.0) * 8
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)
    if pose.alpha < 1:
        ctx.push_group()
    glow(ctx, 0, 0, r * 2.3, (1, 0.9, 0.5), 0.45 + 0.1 * math.sin(t * 3))
    # little orbiting sparkles
    for i in range(3):
        a = t * 1.3 + i * 2.1
        sx, sy = math.cos(a) * r * 1.45, math.sin(a) * r * 0.55 - r * 0.2
        star(ctx, sx, sy, 9 + 3 * math.sin(t * 4 + i), (1, 0.97, 0.7))
    sq = 0.02 * math.sin(t * 2.4) - pose.mouth * 0.03
    ctx.save()
    ctx.scale(1 + sq, 1 - sq)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    g = cairo.RadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r)
    g.add_color_stop_rgb(0, 1, 0.97, 0.75)
    g.add_color_stop_rgb(1, *c)
    ctx.set_source(g)
    ctx.fill_preserve()
    rgba(ctx, INK)
    ctx.set_line_width(5)
    ctx.stroke()
    # little flame-like tuft
    ctx.move_to(-14, -r + 4)
    ctx.curve_to(-14, -r - 22, 6, -r - 26, 4, -r - 44)
    ctx.curve_to(20, -r - 26, 18, -r - 10, 14, -r + 4)
    fill_stroke(ctx, (1, 0.68, 0.25), INK, 4.5)
    ctx.restore()
    er = spec["eye"] * p["eye_scale"]
    gap = r * spec["gap"]
    look = pose.look
    fx = look[0] * r * 0.08
    for side in (-1, 1):
        draw_eye(ctx, side * gap + fx, -r * 0.12, er * 0.84, er * 1.05, side, p, c, look,
                 pose.blink, spec["iris"], 4)
        draw_brow(ctx, side * gap + fx, -r * 0.12, er * 0.84, er * 1.05, side, p, er * 0.28)
    if p["blush"] > 0.02:
        for side in (-1, 1):
            ellipse(ctx, side * (gap + er * 0.6) + fx, r * 0.22, er * 0.5, er * 0.26)
            rgba(ctx, (1.0, 0.5, 0.45), 0.5 * p["blush"])
            ctx.fill()
    draw_mouth(ctx, fx, r * 0.4, er * 0.95, p, pose.mouth, pose.rnd, 4)
    if p["sweat"] > 0.05:
        sx, sy = r * 0.7, -r * 0.6
        ctx.move_to(sx, sy - 18)
        ctx.curve_to(sx + 11, sy, sx + 11, sy + 13, sx, sy + 13)
        ctx.curve_to(sx - 11, sy + 13, sx - 11, sy, sx, sy - 18)
        fill_stroke(ctx, (0.6, 0.85, 1.0), INK, 3, a=p["sweat"])
    if pose.alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(pose.alpha)
    ctx.restore()


def star(ctx, x, y, r, c=(1, 0.95, 0.6), a=1.0, points=4):
    ctx.save()
    ctx.translate(x, y)
    for i in range(points * 2):
        ang = math.pi * i / points - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        (ctx.move_to if i == 0 else ctx.line_to)(math.cos(ang) * rr, math.sin(ang) * rr)
    ctx.close_path()
    rgba(ctx, c, a)
    ctx.fill()
    ctx.restore()
