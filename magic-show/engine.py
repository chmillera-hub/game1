"""Drawing engine for 'The Magic Show Inside My Head'.

Everything is drawn procedurally with Cairo: characters, props, scenes,
effects, subtitles and title cards.
"""
import math
import random
import cairo

W, H, FPS = 1280, 720, 24
GROUND = 612
FONT = "Fredoka"
PI = math.pi


# ---------------------------------------------------------------- helpers
def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_in(u):
    u = clamp(u)
    return u ** 3


def back_out(u):
    u = clamp(u)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def linear(u):
    return clamp(u)


def lerp(a, b, u):
    return a + (b - a) * u


def tw(lt, t0, t1, a, b, fn=ease):
    """Tween from a to b while local time lt runs from t0 to t1."""
    if t1 <= t0:
        return b if lt >= t0 else a
    return lerp(a, b, fn((lt - t0) / (t1 - t0)))


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def src(ctx, h, a=1.0):
    r, g, b = rgb(h) if isinstance(h, str) else h
    ctx.set_source_rgba(r, g, b, a)


def mix(c1, c2, u):
    a, b = rgb(c1), rgb(c2)
    return tuple(lerp(a[i], b[i], u) for i in range(3))


def ellipse(ctx, x, y, rx, ry):
    if rx <= 0 or ry <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * PI)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI)
    ctx.arc(x + r, y + r, r, PI, 1.5 * PI)
    ctx.close_path()


def fill_stroke(ctx, fill, stroke=None, lw=4, alpha=1.0):
    src(ctx, fill, alpha)
    if stroke:
        ctx.fill_preserve()
        src(ctx, stroke, alpha)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def star_path(ctx, x, y, r1, r2, n=5, rot=-PI / 2):
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * PI / n
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        if i == 0:
            ctx.move_to(px, py)
        else:
            ctx.line_to(px, py)
    ctx.close_path()


def sparkle(ctx, x, y, r, col="#FFFFFF", a=1.0):
    """Four-point twinkle."""
    if r <= 0.3 or a <= 0:
        return
    src(ctx, col, a)
    ctx.move_to(x, y - r)
    ctx.curve_to(x + r * 0.12, y - r * 0.12, x + r * 0.12, y - r * 0.12, x + r, y)
    ctx.curve_to(x + r * 0.12, y + r * 0.12, x + r * 0.12, y + r * 0.12, x, y + r)
    ctx.curve_to(x - r * 0.12, y + r * 0.12, x - r * 0.12, y + r * 0.12, x - r, y)
    ctx.curve_to(x - r * 0.12, y - r * 0.12, x - r * 0.12, y - r * 0.12, x, y - r)
    ctx.fill()


def text(ctx, s, x, y, size, col="#FFFFFF", align="center", weight=True,
         outline=None, olw=6, alpha=1.0):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if weight else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if align == "center":
        px = x - ext.width / 2 - ext.x_bearing
    elif align == "right":
        px = x - ext.width - ext.x_bearing
    else:
        px = x
    ctx.move_to(px, y)
    ctx.text_path(s)
    if outline:
        src(ctx, outline, alpha)
        ctx.set_line_width(olw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    src(ctx, col, alpha)
    ctx.fill()
    return ext


def text_width(ctx, s, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance


def hash01(*k):
    return random.Random(hash(k) & 0xFFFFFFFF).random()


# ---------------------------------------------------------------- characters
KIND = {
    "anger": dict(w=140, h=140, legh=22, n=3.4, taper=0.08, col="#E8473A", dark="#7E1A12",
                  eye_y=-112, eye_dx=26, erx=15, ery=18, mouth_y=-70, mw=34,
                  sh=(64, -84), hip=30, L=50, brow=(24, 24), brow_raise=(0, 0), lid=0.0),
    "doubt": dict(w=104, h=190, legh=22, n=2.6, taper=0.32, col="#9B7BE0", dark="#43307F",
                  eye_y=-170, eye_dx=19, erx=13, ery=17, mouth_y=-138, mw=26,
                  sh=(46, -112), hip=24, L=46, brow=(-4, 14), brow_raise=(0, 7), lid=0.0),
    "boredom": dict(w=136, h=150, legh=18, n=2.4, taper=-0.06, col="#8FA6B5", dark="#3E5260",
                    eye_y=-106, eye_dx=25, erx=15, ery=16, mouth_y=-70, mw=30,
                    sh=(60, -80), hip=30, L=48, brow=(-6, -6), brow_raise=(-2, -2), lid=0.48),
}

POSES = {
    # hand targets in local (unscaled) coordinates, relative to ground point
    "rest": lambda k, s: (s * (k["sh"][0] + 12), k["sh"][1] + 70),
    "hip": lambda k, s: (s * (k["sh"][0] - 2), k["sh"][1] + 42),
    "up": lambda k, s: (s * (k["sh"][0] + 26), k["sh"][1] - 82),
    "out": lambda k, s: (s * (k["sh"][0] + 88), k["sh"][1] - 6),
    "mouth": lambda k, s: (s * 12, k["mouth_y"] + 4),
    "cheek": lambda k, s: (s * (k["eye_dx"] + 22), k["mouth_y"] - 6),
    "belly": lambda k, s: (s * 26, k["sh"][1] + 50),
    "cross": lambda k, s: (-s * 22, k["sh"][1] + 26),
    "wave": lambda k, s: (s * (k["sh"][0] + 40), k["sh"][1] - 70),
    "face": lambda k, s: (s * 10, k["eye_y"] + 14),
}


def pose(kind, side, name):
    """side: -1 left hand, +1 right hand."""
    return POSES[name](KIND[kind], side)


def new_char(kind, x, **kw):
    k = KIND[kind]
    c = dict(kind=kind, x=x, y=GROUND, s=1.0, face=0.0, tilt=0.0, yoff=0.0, sq=1.0,
             eyes="open", lid=k["lid"], px=0.0, py=0.0, brow=0.0, mouth="smile", mamt=0.5,
             talk=0.0, hl=pose(kind, -1, "rest"), hr=pose(kind, 1, "rest"), itemR=None,
             itemL=None, wandR=-30.0, wandL=210.0, glow=0.0, makeup=0.0, glitter=0.0,
             mode=None, walking=0.0, visible=True, cheeks=0.0, steam=0.0, blink=True,
             wide=0.0, footL=(0.0, 0.0), footR=(0.0, 0.0), sweat=0.0, layer=0, alpha=1.0,
             shake=0.0)
    c.update(kw)
    return c


def ik(sx, sy, tx, ty, L, side):
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return sx + side * L, sy
    dd = min(d, 2 * L * 0.999)
    ux, uy = dx / d, dy / d
    mx, my = sx + ux * dd / 2, sy + uy * dd / 2
    h = math.sqrt(max(0.0, L * L - (dd / 2) ** 2))
    n1 = (-uy, ux)
    n2 = (uy, -ux)
    n = n1
    score1 = n1[0] * side + 0.35 * n1[1]
    score2 = n2[0] * side + 0.35 * n2[1]
    if score2 > score1:
        n = n2
    return mx + n[0] * h, my + n[1] * h


def resolve(c, t):
    """Apply continuous 'mode' animation on top of the stored state."""
    d = dict(c)
    k = KIND[c["kind"]]
    m = c["mode"]
    ph = {"anger": 0.0, "doubt": 1.3, "boredom": 2.1}[c["kind"]]
    if c["walking"] > 0:
        sp = 9.0 * c["walking"]
        lift = 9 * c["walking"]
        d["footL"] = (0, -max(0, math.sin(t * sp)) * lift)
        d["footR"] = (0, -max(0, -math.sin(t * sp)) * lift)
        d["yoff"] = c["yoff"] - abs(math.sin(t * sp)) * 4 * c["walking"]
    if m == "laugh":
        d["yoff"] = c["yoff"] - abs(math.sin(t * 15)) * 7
        d["eyes"] = "happy"
        d["mouth"], d["mamt"] = "laugh", 0.85 + 0.15 * math.sin(t * 30)
        d["hl"], d["hr"] = pose(c["kind"], -1, "belly"), pose(c["kind"], 1, "belly")
        d["tilt"] = c["tilt"] + math.sin(t * 7) * 0.05
        d["brow"] = 0.6
    elif m == "giggle":
        d["yoff"] = c["yoff"] - abs(math.sin(t * 13)) * 4
        d["eyes"] = "happy"
        d["mouth"], d["mamt"] = "smile", 0.8
        d["hl"] = (-6, k["mouth_y"] + 2)
        d["hr"] = (10, k["mouth_y"] + 10)
        d["covered"] = True
        d["footL"] = (0, -max(0, math.sin(t * 14)) * 12)
        d["footR"] = (0, -max(0, -math.sin(t * 14)) * 12)
        d["tilt"] = c["tilt"] + math.sin(t * 9) * 0.04
        d["brow"] = 0.7
    elif m == "floorlaugh":
        d["tilt"] = -PI / 2
        d["eyes"] = "happy"
        d["mouth"], d["mamt"] = "laugh", 0.9 + 0.1 * math.sin(t * 28)
        # legs kick in the air (local y towards feet maps to screen right)
        d["footL"] = (math.sin(t * 13) * 16 - 6, -abs(math.sin(t * 13)) * 10)
        d["footR"] = (math.sin(t * 13 + 2.2) * 16 + 6, -abs(math.sin(t * 13 + 2.2)) * 10)
        # left fist pounds the floor (local -x is the floor side)
        pound = abs(math.sin(t * 9))
        d["hl"] = (-k["sh"][0] - 40 - pound * 30, k["sh"][1] + 10)
        d["hr"] = pose(c["kind"], 1, "belly")
        d["shake"] = 2.0
        d["brow"] = 0.8
    elif m == "stomp":
        d["footL"] = (0, -max(0, math.sin(t * 10)) * 20)
        d["footR"] = (0, -max(0, -math.sin(t * 10)) * 20)
        d["yoff"] = c["yoff"] - abs(math.sin(t * 10)) * 6
        d["hl"], d["hr"] = pose(c["kind"], -1, "hip"), pose(c["kind"], 1, "hip")
        d["steam"] = 1.0
        d["brow"] = -1.0
        d["mouth"] = "frown" if c["talk"] < 0.05 else c["mouth"]
    elif m == "run":
        sp = 22
        d["footL"] = (math.sin(t * sp) * 14, -max(0, math.sin(t * sp)) * 18)
        d["footR"] = (-math.sin(t * sp) * 14, -max(0, -math.sin(t * sp)) * 18)
        d["yoff"] = c["yoff"] - abs(math.sin(t * sp)) * 10
        d["tilt"] = c["tilt"] + 0.22 * (1 if c["face"] >= 0 else -1)
        d["hl"] = (-k["sh"][0] - 20 + math.sin(t * sp) * 18, k["sh"][1] - 60)
        d["hr"] = (k["sh"][0] + 20 - math.sin(t * sp) * 18, k["sh"][1] - 60)
    elif m == "holdin":
        d["cheeks"] = 1.0
        d["eyes"] = "squeeze"
        d["mouth"], d["mamt"] = "tight", 1.0
        d["shake"] = 1.8
    if d.get("shake", 0) > 0:
        d["x"] = d["x"] + math.sin(t * 61 + ph) * d["shake"]
        d["yoff"] = d["yoff"] + math.cos(t * 53 + ph) * d["shake"] * 0.6
    # automatic blinking
    if c["blink"] and d["eyes"] in ("open", "side", "wide"):
        cyc = (t + ph * 1.7) % 3.7
        if cyc < 0.13:
            d["lid"] = 1.0
    return d


def body_points(k, t, sq, kind):
    w, h = k["w"], k["h"]
    cy = -(k["legh"] + h / 2)
    br = 1 + 0.018 * math.sin(t * 2.3 + w)
    pts = []
    n = k["n"]
    N = 72
    for i in range(N):
        a = 2 * PI * i / N
        ca, sa = math.cos(a), math.sin(a)
        x = (w / 2) * math.copysign(abs(ca) ** (2 / n), ca)
        y = (h / 2) * math.copysign(abs(sa) ** (2 / n), sa)
        f = 1 - k["taper"] * (0.5 - 0.5 * y / (h / 2))
        x *= f
        if kind == "boredom":
            # droopy: top sags towards one side
            x += -10 * max(0, -y / (h / 2)) ** 2
            y += 6 * max(0, -y / (h / 2)) ** 3
        x *= br / math.sqrt(sq)
        y = y / br * sq
        pts.append((x, cy * sq + y - (cy * sq - cy) * 0 + (cy * (sq - 1)) * 0))
    # anchor the bottom to the legs
    bottom = max(p[1] for p in pts)
    off = -k["legh"] - bottom
    return [(x, y + off) for x, y in pts], cy * sq


def draw_char(ctx, c0, t, mirror_world=False):
    if not c0["visible"]:
        return
    c = resolve(c0, t)
    k = KIND[c["kind"]]
    s = c["s"]
    col, dark = k["col"], k["dark"]
    ctx.save()
    if c["alpha"] < 1:
        ctx.push_group()
    pts, cy = body_points(k, t, c["sq"], c["kind"])
    # lift so a tilted body rests on the floor
    hc = lerp(-cy, k["w"] / 2 + 4, abs(math.sin(c["tilt"])))
    ctx.translate(c["x"], c["y"] + c["yoff"])
    ctx.scale(s, s)
    ctx.translate(0, -hc)
    ctx.rotate(c["tilt"])
    ctx.translate(0, -cy)  # back to ground-origin coordinates
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # legs
    for side, foot in ((-1, c["footL"]), (1, c["footR"])):
        hx = side * k["hip"]
        fx, fy = hx + foot[0] + side * 4, foot[1]
        ctx.move_to(hx, -k["legh"] - 6)
        ctx.line_to(fx, fy - 6)
        src(ctx, dark)
        ctx.set_line_width(15)
        ctx.stroke()
        ctx.move_to(hx, -k["legh"] - 6)
        ctx.line_to(fx, fy - 6)
        src(ctx, col)
        ctx.set_line_width(8)
        ctx.stroke()
        ellipse(ctx, fx + side * 6 + c["face"] * 5, fy - 4, 17, 9)
        fill_stroke(ctx, "#2B2233", "#140f18", 3)

    # body
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.save()
    pat = cairo.LinearGradient(-k["w"] / 2, cy - k["h"] / 2, k["w"] / 2, cy + k["h"] / 2)
    pat.add_color_stop_rgb(0, *mix(col, "#FFFFFF", 0.18))
    pat.add_color_stop_rgb(1, *mix(col, "#000000", 0.12))
    ctx.set_source(pat)
    ctx.fill_preserve()
    src(ctx, dark)
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.restore()

    top = min(p[1] for p in pts)
    fx = c["face"] * k["w"] * 0.1

    # kind specific accessories
    if c["kind"] == "anger":
        flick = math.sin(t * 9) * 3
        ctx.move_to(-26, top + 10)
        ctx.line_to(-18 + flick, top - 26)
        ctx.line_to(-6, top + 4)
        ctx.line_to(2 - flick, top - 38)
        ctx.line_to(12, top + 4)
        ctx.line_to(24 + flick, top - 22)
        ctx.line_to(30, top + 12)
        ctx.close_path()
        fill_stroke(ctx, "#FF8A3D", dark, 4)
    elif c["kind"] == "doubt":
        ctx.move_to(-8 + fx, top + 6)
        ctx.curve_to(-30 + fx, top - 30, 20 + fx, top - 42, 14 + fx, top - 14)
        ctx.curve_to(10 + fx, top - 4, 0 + fx, top - 20, 6 + fx, top - 24)
        src(ctx, dark)
        ctx.set_line_width(6)
        ctx.stroke()
        # bow
        bx, by = 22 + fx, top + 12
        ctx.move_to(bx, by)
        ctx.line_to(bx - 14, by - 10)
        ctx.line_to(bx - 14, by + 10)
        ctx.close_path()
        ctx.move_to(bx, by)
        ctx.line_to(bx + 14, by - 10)
        ctx.line_to(bx + 14, by + 10)
        ctx.close_path()
        fill_stroke(ctx, "#FF6FAE", "#9C2A61", 3)
        ellipse(ctx, bx, by, 4, 4)
        fill_stroke(ctx, "#FF6FAE", "#9C2A61", 2)
    elif c["kind"] == "boredom":
        sway = math.sin(t * 1.3) * 4
        ctx.move_to(-2 + fx, top + 4)
        ctx.curve_to(4 + fx, top - 24, 26 + fx + sway, top - 22, 24 + fx + sway, top + 2)
        src(ctx, dark)
        ctx.set_line_width(5)
        ctx.stroke()

    # glitter specks on the body
    if c["glitter"] > 0:
        rnd = random.Random(7)
        for i in range(int(60 * c["glitter"])):
            gx = rnd.uniform(-k["w"] * 0.42, k["w"] * 0.42)
            gy = rnd.uniform(top + 10, -k["legh"] - 10)
            tw_ = 0.5 + 0.5 * math.sin(t * 6 + i)
            colg = rnd.choice(["#FFE45C", "#FF7AD9", "#7AE7FF", "#FFFFFF", "#B98CFF"])
            sparkle(ctx, gx, gy, 2 + 3 * tw_, colg, c["glitter"])

    draw_face(ctx, c, k, fx, t)

    # cheeks puffed (holding in a laugh)
    if c["cheeks"] > 0:
        for side in (-1, 1):
            ellipse(ctx, fx + side * (k["mw"] * 0.8), k["mouth_y"] - 2, 13 * c["cheeks"], 10 * c["cheeks"])
            src(ctx, mix(col, "#FFFFFF", 0.25), 0.9)
            ctx.fill()

    # arms
    sx, sy = k["sh"]
    for side, hand, item, wang in ((-1, c["hl"], c["itemL"], c["wandL"]),
                                   (1, c["hr"], c["itemR"], c["wandR"])):
        shx = side * sx
        ex, ey = ik(shx, sy, hand[0], hand[1], k["L"], side)
        dd = math.hypot(hand[0] - shx, hand[1] - sy)
        hx, hy = hand
        if dd > 2 * k["L"]:
            u = 2 * k["L"] / dd
            hx, hy = shx + (hand[0] - shx) * u, sy + (hand[1] - sy) * u
        ctx.move_to(shx, sy)
        ctx.curve_to(ex, ey, ex, ey, hx, hy)
        src(ctx, dark)
        ctx.set_line_width(14)
        ctx.stroke()
        ctx.move_to(shx, sy)
        ctx.curve_to(ex, ey, ex, ey, hx, hy)
        src(ctx, col)
        ctx.set_line_width(8)
        ctx.stroke()
        if item == "wand":
            a = math.radians(wang)
            ctx.save()
            ctx.translate(hx, hy)
            ctx.rotate(a)
            ctx.move_to(-8, 0)
            ctx.line_to(46, 0)
            src(ctx, "#111111")
            ctx.set_line_width(6)
            ctx.stroke()
            ctx.move_to(36, 0)
            ctx.line_to(48, 0)
            src(ctx, "#FFFFFF")
            ctx.set_line_width(6)
            ctx.stroke()
            if c["glow"] > 0:
                g = cairo.RadialGradient(50, 0, 0, 50, 0, 30)
                g.add_color_stop_rgba(0, 1, 1, 0.8, 0.9 * c["glow"])
                g.add_color_stop_rgba(1, 1, 0.9, 0.4, 0)
                ctx.set_source(g)
                ctx.arc(50, 0, 30, 0, 2 * PI)
                ctx.fill()
                for i in range(4):
                    aa = t * 5 + i * PI / 2
                    sparkle(ctx, 50 + math.cos(aa) * 18, math.sin(aa) * 18, 6 * c["glow"], "#FFF6B0")
            ctx.restore()
        elif item == "turtle":
            draw_turtle(ctx, hx, hy - 4, 0.75, 1, t, held=True)
        ellipse(ctx, hx, hy, 11, 11)
        fill_stroke(ctx, col, dark, 3.5)

    # steam puffs
    if c["steam"] > 0:
        for i in range(3):
            u = ((t * 0.9 + i / 3) % 1.0)
            for side in (-1, 1):
                px = side * (30 + u * 30)
                py = top - 10 - u * 60
                ellipse(ctx, px, py, 8 + u * 14, 8 + u * 12)
                src(ctx, "#FFFFFF", 0.7 * (1 - u) * c["steam"])
                ctx.fill()
    if c["sweat"] > 0:
        u = (t * 1.2) % 1.0
        ctx.move_to(k["w"] * 0.42, top + 30 + u * 30)
        ctx.curve_to(k["w"] * 0.42 + 8, top + 44 + u * 30, k["w"] * 0.42 - 8, top + 44 + u * 30,
                     k["w"] * 0.42, top + 30 + u * 30)
        src(ctx, "#8FD8FF", c["sweat"])
        ctx.fill()

    if c["alpha"] < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(c["alpha"])
    ctx.restore()


def draw_face(ctx, c, k, fx, t):
    ey = k["eye_y"]
    mk = c["makeup"]
    wide = c["wide"]
    # blush / powder
    if mk > 0:
        for side in (-1, 1):
            bx, by = fx + side * (k["eye_dx"] + 14), ey + 34
            g = cairo.RadialGradient(bx, by, 0, bx, by, 18)
            g.add_color_stop_rgba(0, 1, 0.42, 0.62, 0.85 * mk)
            g.add_color_stop_rgba(1, 1, 0.42, 0.62, 0)
            ctx.set_source(g)
            ctx.arc(bx, by, 18, 0, 2 * PI)
            ctx.fill()
    for side in (-1, 1):
        ex = fx + side * k["eye_dx"]
        rx, ry = k["erx"] * (1 + 0.25 * wide), k["ery"] * (1 + 0.25 * wide)
        eyes = c["eyes"]
        if mk > 0 and eyes not in ("happy",):
            # eyeshadow
            ctx.save()
            ellipse(ctx, ex, ey - 3, rx + 6, ry + 6)
            src(ctx, "#4FC3F7", 0.75 * mk)
            ctx.fill()
            ctx.restore()
        if eyes == "happy":
            ctx.move_to(ex - rx, ey + 3)
            ctx.curve_to(ex - rx * 0.5, ey - ry, ex + rx * 0.5, ey - ry, ex + rx, ey + 3)
            src(ctx, "#1d1420")
            ctx.set_line_width(4.5)
            ctx.stroke()
        elif eyes == "squeeze":
            ctx.move_to(ex - side * rx, ey - 6)
            ctx.line_to(ex + side * rx * 0.6, ey)
            ctx.line_to(ex - side * rx, ey + 6)
            src(ctx, "#1d1420")
            ctx.set_line_width(4.5)
            ctx.stroke()
        else:
            ellipse(ctx, ex, ey, rx, ry)
            fill_stroke(ctx, "#FFFFFF", "#1d1420", 3)
            pr = (6.5 if not wide else 4.5)
            ppx = ex + clamp(c["px"] + c["face"] * 0.3, -1, 1) * rx * 0.5
            ppy = ey + clamp(c["py"], -1, 1) * ry * 0.5
            ctx.save()
            ellipse(ctx, ex, ey, rx, ry)
            ctx.clip()
            ellipse(ctx, ppx, ppy, pr, pr * 1.05)
            src(ctx, "#1d1420")
            ctx.fill()
            ellipse(ctx, ppx - 2, ppy - 2.5, 2, 2)
            src(ctx, "#FFFFFF")
            ctx.fill()
            lid = clamp(c["lid"])
            if lid > 0:
                ctx.rectangle(ex - rx - 2, ey - ry - 2, rx * 2 + 4, (ry * 2 + 4) * lid)
                src(ctx, mix(k["col"], "#000000", 0.08))
                ctx.fill()
                ctx.move_to(ex - rx, ey - ry + (ry * 2) * lid)
                ctx.line_to(ex + rx, ey - ry + (ry * 2) * lid)
                src(ctx, "#1d1420")
                ctx.set_line_width(3)
                ctx.stroke()
            ctx.restore()
            ellipse(ctx, ex, ey, rx, ry)
            src(ctx, "#1d1420")
            ctx.set_line_width(3)
            ctx.stroke()
        # lashes
        lash = mk * 1.0 + (0.45 if c["kind"] == "doubt" else 0)
        if lash > 0 and eyes != "squeeze":
            ln = 7 + 9 * mk
            for i in range(3):
                a = -PI / 2 + side * (0.35 + i * 0.32)
                bx = ex + math.cos(a) * rx * 0.95
                by = ey + math.sin(a) * ry * 0.95 - (0 if eyes != "happy" else -ry * 0.5)
                ctx.move_to(bx, by)
                ctx.line_to(bx + math.cos(a) * ln * lash, by + math.sin(a) * ln * lash - 2)
                src(ctx, "#1d1420")
                ctx.set_line_width(3)
                ctx.stroke()
        # brows
        base = k["brow"][0 if side < 0 else 1]
        raise_ = k["brow_raise"][0 if side < 0 else 1]
        ang = math.radians(base - c["brow"] * 18)
        bcx = ex
        bcy = ey - ry - 9 - raise_ - c["brow"] * 6 - wide * 6
        L = 30 if c["kind"] != "doubt" else 22
        ctx.move_to(bcx - side * L / 2 * math.cos(ang), bcy + L / 2 * math.sin(ang))
        ctx.line_to(bcx + side * L / 2 * math.cos(ang), bcy - L / 2 * math.sin(ang))
        src(ctx, "#1d1420")
        ctx.set_line_width(7 if c["kind"] != "doubt" else 4.5)
        ctx.stroke()

    if c.get("covered"):
        return
    draw_mouth(ctx, c, k, fx, t)


def draw_mouth(ctx, c, k, fx, t):
    mx, my = fx, k["mouth_y"]
    mw = k["mw"]
    mk = c["makeup"]
    lip = "#D6112F"
    m, a = c["mouth"], c["mamt"]
    talk = c["talk"]
    ink = "#1d1420"
    if m in ("laugh", "jaw", "o") or talk > 0.06:
        if m == "jaw":
            ry = 14 + a * 110
            ctx.move_to(mx - mw * 0.6, my - 6)
            ctx.curve_to(mx - mw * 0.9, my + ry, mx + mw * 0.9, my + ry, mx + mw * 0.6, my - 6)
            ctx.close_path()
        elif m == "laugh":
            ry = 10 + 18 * a
            ctx.move_to(mx - mw * 0.75, my - 4)
            ctx.line_to(mx + mw * 0.75, my - 4)
            ctx.curve_to(mx + mw * 0.7, my + ry, mx - mw * 0.7, my + ry, mx - mw * 0.75, my - 4)
            ctx.close_path()
        elif m == "o" and talk <= 0.06:
            ellipse(ctx, mx, my + 2, 7 + 5 * a, 9 + 7 * a)
        else:
            op = clamp(talk)
            ry = 3 + 15 * op
            rx = mw * (0.45 + 0.15 * (1 - op))
            ellipse(ctx, mx, my + ry * 0.4, rx, ry)
        mpath = ctx.copy_path()
        ctx.save()
        ctx.clip_preserve()
        src(ctx, "#5B1324")
        ctx.fill()
        if m == "jaw":
            ty, tr = my + (14 + a * 110) * 0.62, 12 + a * 14
        elif m == "laugh":
            ty, tr = my + 10 + 18 * a, 9
        else:
            ty, tr = my + 4 + 15 * clamp(talk) * 1.1, 7
        ellipse(ctx, mx, ty, mw * 0.42, tr)
        src(ctx, "#FF7A93")
        ctx.fill()
        ctx.restore()
        ctx.new_path()
        ctx.append_path(mpath)
        if mk > 0:
            src(ctx, lip, mk)
            ctx.set_line_width(7)
        else:
            src(ctx, ink)
            ctx.set_line_width(4)
        ctx.stroke()
        if mk > 0 and m == "jaw":
            pass
        return
    if m == "kiss":
        ctx.save()
        ctx.translate(mx + 4, my)
        ellipse(ctx, 0, 0, 7, 8)
        src(ctx, lip if mk > 0 else "#5B1324")
        ctx.fill()
        ellipse(ctx, 0, 0, 3, 3.5)
        src(ctx, "#5B1324")
        ctx.fill()
        ctx.restore()
        return
    # line mouths
    if m == "smile":
        ctx.move_to(mx - mw / 2, my - 2)
        ctx.curve_to(mx - mw / 4, my + 10 * a + 2, mx + mw / 4, my + 10 * a + 2, mx + mw / 2, my - 2)
    elif m == "frown":
        ctx.move_to(mx - mw / 2, my + 6)
        ctx.curve_to(mx - mw / 4, my - 8 * a, mx + mw / 4, my - 8 * a, mx + mw / 2, my + 6)
    elif m == "smirk":
        ctx.move_to(mx - mw / 2, my + 2)
        ctx.curve_to(mx - mw / 6, my + 4, mx + mw / 4, my + 2, mx + mw / 2, my - 8 * a)
    elif m == "tight":
        ctx.move_to(mx - mw / 2, my)
        for i in range(1, 9):
            ctx.line_to(mx - mw / 2 + mw * i / 8, my + (3 if i % 2 else -3) + math.sin(t * 40) * 1.5)
    elif m == "wavy":
        ctx.move_to(mx - mw / 2, my)
        for i in range(1, 13):
            ctx.line_to(mx - mw / 2 + mw * i / 12, my + math.sin(i * 1.4 + t * 12) * 3)
    else:  # flat
        ctx.move_to(mx - mw / 2, my + 2)
        ctx.line_to(mx + mw / 2, my + 2)
    if mk > 0:
        ctx.save()
        src(ctx, lip, mk)
        ctx.set_line_width(4 + 7 * mk)
        ctx.stroke_preserve()
        ctx.restore()
        src(ctx, "#7A0A1C", mk)
        ctx.set_line_width(2)
        ctx.stroke()
        # cupid's bow highlight
        ellipse(ctx, mx - 3, my - 2, 3, 1.5)
        src(ctx, "#FFFFFF", 0.6 * mk)
        ctx.fill()
    else:
        src(ctx, ink)
        ctx.set_line_width(4.5)
        ctx.stroke()


# ---------------------------------------------------------------- critters
def draw_rabbit(ctx, x, y, s, face, t, phase=0.0, giggle=0.0, look=0.0):
    ctx.save()
    hop = max(0.0, math.sin(t * 2.6 + phase * 7)) ** 10 * 10
    sh = math.sin(t * 40 + phase) * 2 * giggle
    ctx.translate(x + sh, y - hop - abs(math.sin(t * 16 + phase)) * 3 * giggle)
    ctx.scale(s * (1 if face >= 0 else -1), s)
    ink = "#3A3340"
    ellipse(ctx, -24, -22, 9, 8)  # tail
    fill_stroke(ctx, "#FFFFFF", ink, 3)
    ellipse(ctx, 0, -24, 26, 22)  # body
    fill_stroke(ctx, "#FFFFFF", ink, 3.5)
    tw_ = math.sin(t * 3 + phase * 5) * 0.12
    for dx, a in ((8, -0.18 + tw_), (20, 0.22 - tw_)):
        ctx.save()
        ctx.translate(dx + 4, -62)
        ctx.rotate(a)
        ellipse(ctx, 0, -22, 7, 22)
        fill_stroke(ctx, "#FFFFFF", ink, 3)
        ellipse(ctx, 0, -20, 3.2, 15)
        src(ctx, "#FFB3C7")
        ctx.fill()
        ctx.restore()
    ellipse(ctx, 16, -50, 19, 17)  # head
    fill_stroke(ctx, "#FFFFFF", ink, 3.5)
    if giggle > 0.5:
        ctx.move_to(17 + look * 2, -55)
        ctx.curve_to(20, -60, 25, -60, 28, -55)
        src(ctx, ink)
        ctx.set_line_width(2.5)
        ctx.stroke()
    else:
        blink = ((t + phase * 3) % 4.1) < 0.12
        if blink:
            ctx.move_to(19, -54)
            ctx.line_to(28, -54)
            src(ctx, ink)
            ctx.set_line_width(2.5)
            ctx.stroke()
        else:
            ellipse(ctx, 23 + look * 3, -54, 3.5, 4.5)
            src(ctx, ink)
            ctx.fill()
    nose = math.sin(t * 14 + phase) * 0.8
    ellipse(ctx, 33, -46 + nose, 3.5, 2.8)
    src(ctx, "#FF7FA3")
    ctx.fill()
    ellipse(ctx, 22, -40, 5, 3)
    src(ctx, "#FFC2D4", 0.8)
    ctx.fill()
    for fx in (-8, 12):
        ellipse(ctx, fx, -3, 9, 5)
        fill_stroke(ctx, "#FFFFFF", ink, 3)
    ctx.restore()


def draw_turtle(ctx, x, y, s, face, t, held=False, blink_slow=0.0, smile=0.0, blush=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * (1 if face >= 0 else -1), s)
    ink = "#1E3A1E"
    wig = math.sin(t * 8) * 3 if held else 0
    for lx in (-22, 20):
        ellipse(ctx, lx, -6 + (wig if lx < 0 else -wig), 9, 7)
        fill_stroke(ctx, "#8BCB6A", ink, 3)
    ellipse(ctx, -36, -14, 7, 4)
    fill_stroke(ctx, "#8BCB6A", ink, 3)
    # head
    ellipse(ctx, 40, -24 + wig * 0.5, 15, 13)
    fill_stroke(ctx, "#8BCB6A", ink, 3.5)
    blink = ((t * 0.9) % 3.3) < 0.14
    lid = max(blink_slow, 1.0 if blink else 0.0)
    ex, ey = 45, -28 + wig * 0.5
    ellipse(ctx, ex, ey, 5.5, 6.5)
    fill_stroke(ctx, "#FFFFFF", ink, 2)
    ellipse(ctx, ex + 1.5, ey + 1, 3, 3.5)
    src(ctx, ink)
    ctx.fill()
    if lid > 0:
        ctx.save()
        ellipse(ctx, ex, ey, 6.5, 7.5)
        ctx.clip()
        ctx.rectangle(ex - 8, ey - 8, 16, 16 * lid)
        src(ctx, "#8BCB6A")
        ctx.fill()
        ctx.restore()
        ctx.move_to(ex - 6, ey - 6.5 + 13 * lid)
        ctx.line_to(ex + 6, ey - 6.5 + 13 * lid)
        src(ctx, ink)
        ctx.set_line_width(2)
        ctx.stroke()
    ctx.move_to(44, -18 + wig * 0.5)
    ctx.curve_to(48, -15 + 4 * smile, 52, -15 + 4 * smile, 54, -19)
    src(ctx, ink)
    ctx.set_line_width(2.2)
    ctx.stroke()
    if blush > 0:
        ellipse(ctx, 40, -20, 4, 2.5)
        src(ctx, "#FF8FB0", blush)
        ctx.fill()
    # shell
    ctx.move_to(-38, -8)
    ctx.curve_to(-36, -58, 34, -58, 36, -8)
    ctx.close_path()
    g = cairo.LinearGradient(0, -50, 0, -8)
    g.add_color_stop_rgb(0, *rgb("#5FAE48"))
    g.add_color_stop_rgb(1, *rgb("#3C7D31"))
    ctx.set_source(g)
    ctx.fill_preserve()
    src(ctx, ink)
    ctx.set_line_width(3.5)
    ctx.stroke()
    for hx, hy in ((0, -32), (-20, -22), (20, -22)):
        for i in range(6):
            a = i * PI / 3
            px, py = hx + 9 * math.cos(a), hy + 8 * math.sin(a)
            (ctx.move_to if i == 0 else ctx.line_to)(px, py)
        ctx.close_path()
        src(ctx, "#A6D98C", 0.55)
        ctx.fill_preserve()
        src(ctx, ink, 0.6)
        ctx.set_line_width(2)
        ctx.stroke()
    ctx.move_to(-40, -8)
    ctx.line_to(38, -8)
    src(ctx, "#D9C27A")
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------- stage
_STAGE_CACHE = {}


def stage_bg():
    if "stage" in _STAGE_CACHE:
        return _STAGE_CACHE["stage"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, 0, 560)
    g.add_color_stop_rgb(0, *rgb("#1B1036"))
    g.add_color_stop_rgb(1, *rgb("#3B2366"))
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(3)
    # backdrop stars
    for i in range(70):
        x, y = rnd.uniform(90, 1190), rnd.uniform(110, 520)
        r = rnd.uniform(3, 9)
        star_path(ctx, x, y, r, r * 0.45, rot=rnd.uniform(0, PI))
        src(ctx, "#F7D774", rnd.uniform(0.15, 0.45))
        ctx.fill()
    # moon
    ellipse(ctx, 1010, 200, 44, 44)
    src(ctx, "#F6E7B0", 0.35)
    ctx.fill()
    ellipse(ctx, 1028, 188, 40, 40)
    g = cairo.LinearGradient(0, 160, 0, 240)
    ctx.set_source_rgb(*rgb("#2C1950"))
    ctx.fill()
    # floor
    g = cairo.LinearGradient(0, 540, 0, H)
    g.add_color_stop_rgb(0, *rgb("#7A4A2A"))
    g.add_color_stop_rgb(1, *rgb("#4A2A16"))
    ctx.rectangle(0, 540, W, H - 540)
    ctx.set_source(g)
    ctx.fill()
    for i in range(-12, 13):
        ctx.move_to(640 + i * 30, 540)
        ctx.line_to(640 + i * 120, H)
        src(ctx, "#3A2010", 0.5)
        ctx.set_line_width(2)
        ctx.stroke()
    for yy in (565, 598, 640, 690):
        ctx.move_to(0, yy)
        ctx.line_to(W, yy)
        src(ctx, "#3A2010", 0.35)
        ctx.set_line_width(1.5)
        ctx.stroke()
    ctx.rectangle(0, 536, W, 8)
    src(ctx, "#C8963E")
    ctx.fill()
    # side drapes
    for side in (0, 1):
        x0 = 0 if side == 0 else W - 100
        for i in range(5):
            xs = x0 + i * 20
            g = cairo.LinearGradient(xs, 0, xs + 20, 0)
            g.add_color_stop_rgb(0, *rgb("#8E0F1E"))
            g.add_color_stop_rgb(0.5, *rgb("#D7263D"))
            g.add_color_stop_rgb(1, *rgb("#7A0C19"))
            ctx.rectangle(xs, 0, 21, 600)
            ctx.set_source(g)
            ctx.fill()
        # tie back
        ty = 380
        ellipse(ctx, x0 + 50, ty, 56, 12)
        src(ctx, "#E8B64A")
        ctx.fill()
    # valance
    ctx.rectangle(0, 0, W, 70)
    g = cairo.LinearGradient(0, 0, 0, 70)
    g.add_color_stop_rgb(0, *rgb("#7A0C19"))
    g.add_color_stop_rgb(1, *rgb("#C41E3A"))
    ctx.set_source(g)
    ctx.fill()
    for i in range(17):
        cx = i * 80 + 40
        ctx.arc(cx, 70, 40, 0, PI)
        ctx.close_path()
        src(ctx, "#C41E3A")
        ctx.fill()
        ctx.arc(cx, 70, 40, 0, PI)
        src(ctx, "#E8B64A")
        ctx.set_line_width(5)
        ctx.stroke()
    # marquee sign
    rrect(ctx, 330, 14, 620, 74, 18)
    fill_stroke(ctx, "#2A1446", "#E8B64A", 6)
    for i in range(26):
        bx = 345 + i * 23.6
        for by in (22, 80):
            ellipse(ctx, bx, by, 3.5, 3.5)
            src(ctx, "#FFF2B3")
            ctx.fill()
    text(ctx, "THE GREAT EMOTION MAGIC SHOW", 640, 62, 34, "#FFD54F", outline="#6A1B9A", olw=6)
    _STAGE_CACHE["stage"] = surf
    return surf


def draw_bulbs_twinkle(ctx, t):
    for i in range(26):
        bx = 345 + i * 23.6
        for j, by in enumerate((22, 80)):
            on = (int(t * 6) + i + j) % 3 == 0
            if on:
                g = cairo.RadialGradient(bx, by, 0, bx, by, 9)
                g.add_color_stop_rgba(0, 1, 1, 0.8, 0.95)
                g.add_color_stop_rgba(1, 1, 0.8, 0.3, 0)
                ctx.set_source(g)
                ctx.arc(bx, by, 9, 0, 2 * PI)
                ctx.fill()


def draw_main_curtains(ctx, openness):
    """Two red panels; openness 0 closed, 1 fully open (bunched at sides)."""
    if openness >= 0.999:
        return
    pw = lerp(660, 60, ease(openness))
    for side in (0, 1):
        x0 = 0 if side == 0 else W - pw
        n = 12
        for i in range(n):
            xs = x0 + i * pw / n
            g = cairo.LinearGradient(xs, 0, xs + pw / n, 0)
            g.add_color_stop_rgb(0, *rgb("#7A0C19"))
            g.add_color_stop_rgb(0.5, *rgb("#E0283F"))
            g.add_color_stop_rgb(1, *rgb("#6E0A16"))
            ctx.rectangle(xs, 60, pw / n + 1, H - 60)
            ctx.set_source(g)
            ctx.fill()
        ctx.rectangle(x0, H - 18, pw, 18)
        src(ctx, "#E8B64A")
        ctx.fill()


def draw_table(ctx, x, t):
    top = 505
    # legs
    for dx in (-44, 44):
        ctx.rectangle(x + dx - 5, top, 10, GROUND - top)
        src(ctx, "#3B2A1A")
        ctx.fill()
    # cloth
    ctx.move_to(x - 66, top)
    ctx.line_to(x + 66, top)
    ctx.line_to(x + 70, top + 60)
    for i in range(7):
        xx = x + 70 - (i + 1) * 20
        ctx.curve_to(xx + 14, top + 70, xx + 6, top + 70, xx, top + 60)
    ctx.close_path()
    fill_stroke(ctx, "#5E2B97", "#2A1046", 4)
    ctx.move_to(x - 66, top + 54)
    ctx.line_to(x + 70, top + 54)
    src(ctx, "#E8B64A")
    ctx.set_line_width(4)
    ctx.stroke()
    for sx in (-35, 0, 35):
        star_path(ctx, x + sx, top + 28, 9, 4)
        src(ctx, "#FFD54F")
        ctx.fill()
    ellipse(ctx, x, top, 66, 8)
    fill_stroke(ctx, "#7A3DBA", "#2A1046", 3)


HAT_X, HAT_TOP = 660, 448


def draw_hat(ctx, t, wobble=0.0, front=True):
    x = HAT_X + math.sin(t * 30) * wobble
    y0 = HAT_TOP
    # crown resting on the table (hat is upside down, opening on top)
    ctx.move_to(x - 28, y0 + 4)
    ctx.line_to(x - 25, 503)
    ctx.curve_to(x - 10, 510, x + 10, 510, x + 25, 503)
    ctx.line_to(x + 28, y0 + 4)
    ctx.close_path()
    g = cairo.LinearGradient(x - 28, 0, x + 28, 0)
    g.add_color_stop_rgb(0, *rgb("#1A1A22"))
    g.add_color_stop_rgb(0.4, *rgb("#3B3B4A"))
    g.add_color_stop_rgb(1, *rgb("#111117"))
    ctx.set_source(g)
    ctx.fill_preserve()
    src(ctx, "#000000")
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.rectangle(x - 27, y0 + 10, 54, 13)
    src(ctx, "#C62828")
    ctx.fill()
    # brim
    ellipse(ctx, x, y0, 46, 10)
    fill_stroke(ctx, "#22222C", "#000000", 3)
    ellipse(ctx, x, y0 - 1, 27, 6)
    src(ctx, "#050507")
    ctx.fill()


def hat_clip_above(ctx):
    """Clip region above the hat opening (things emerging from the hat)."""
    ctx.rectangle(0, 0, W, HAT_TOP - 1)
    ctx.new_sub_path()
    ellipse(ctx, HAT_X, HAT_TOP - 1, 27, 6)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.clip()


def draw_spot_overlay(ctx, dim, sx, sy=470, rad=230):
    if dim <= 0.01:
        return
    g = cairo.RadialGradient(sx, sy, rad * 0.55, sx, sy, rad * 1.25)
    g.add_color_stop_rgba(0, 0, 0, 0.04, 0)
    g.add_color_stop_rgba(1, 0, 0, 0.04, 0.78 * dim)
    ctx.rectangle(-200, -200, W + 400, H + 400)
    ctx.set_source(g)
    ctx.fill()
    # cone
    ctx.move_to(sx - 30, -10)
    ctx.line_to(sx + 30, -10)
    ctx.line_to(sx + rad * 0.75, GROUND + 20)
    ctx.line_to(sx - rad * 0.75, GROUND + 20)
    ctx.close_path()
    g = cairo.LinearGradient(0, 0, 0, GROUND)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.16 * dim)
    g.add_color_stop_rgba(1, 1, 1, 0.85, 0.04 * dim)
    ctx.set_source(g)
    ctx.fill()


def draw_ambient_cones(ctx, t, a=1.0):
    for i, (bx, sw) in enumerate(((200, 0.7), (1080, 0.9))):
        tx = 640 + math.sin(t * 0.35 * sw + i * 2) * 330
        ctx.move_to(bx - 20, -10)
        ctx.line_to(bx + 20, -10)
        ctx.line_to(tx + 150, GROUND + 20)
        ctx.line_to(tx - 150, GROUND + 20)
        ctx.close_path()
        g = cairo.LinearGradient(0, 0, 0, GROUND)
        g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.10 * a)
        g.add_color_stop_rgba(1, 1, 0.95, 0.8, 0.02 * a)
        ctx.set_source(g)
        ctx.fill()


# ---------------------------------------------------------------- effects
def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def missile_pos(m, tt):
    u = clamp((tt - m["t0"]) / (m["t1"] - m["t0"]))
    u = m.get("ease", linear)(u)
    p0, p2 = (m["x0"], m["y0"]), (m["x1"], m["y1"])
    p1 = ((p0[0] + p2[0]) / 2, min(p0[1], p2[1]) - m.get("arc", 60))
    x, y = bez(p0, p1, p2, u)
    wob = m.get("wobble", 0)
    if wob:
        y += math.sin(u * 18) * wob * math.sin(u * PI)
        x += math.cos(u * 11) * wob * 0.3 * math.sin(u * PI)
    return x, y


def draw_missile(ctx, m, t):
    if not (m["t0"] <= t <= m["t1"]):
        return
    col = m["col"]
    for k in range(16, 0, -1):
        tt = t - k * 0.035 * m.get("trail", 1.0)
        if tt < m["t0"]:
            continue
        x, y = missile_pos(m, tt)
        r = 9 * (1 - k / 17)
        sparkle(ctx, x + math.sin(k * 3.1) * 6, y + math.cos(k * 2.3) * 6, r,
                ["#FFFFFF", col, "#FFE45C"][k % 3], 0.8 * (1 - k / 17))
    x, y = missile_pos(m, t)
    g = cairo.RadialGradient(x, y, 0, x, y, 34)
    r_, g_, b_ = rgb(col)
    g.add_color_stop_rgba(0, 1, 1, 1, 1)
    g.add_color_stop_rgba(0.3, r_, g_, b_, 0.95)
    g.add_color_stop_rgba(1, r_, g_, b_, 0)
    ctx.set_source(g)
    ctx.arc(x, y, 34, 0, 2 * PI)
    ctx.fill()
    sparkle(ctx, x, y, 22 + 4 * math.sin(t * 30), "#FFFFFF", 0.9)


def draw_burst(ctx, e, t):
    dt = t - e["t"]
    if dt < 0:
        return
    x, y = e["x"], e["y"]
    kind = e["kind"]
    rnd = random.Random(e.get("seed", 1))
    if kind == "fire":
        if dt > 1.4:
            return
        r = 20 + 160 * ease_out(dt / 0.6)
        a = clamp(1 - dt / 0.7)
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, 1, 1, 0.8, a)
        g.add_color_stop_rgba(0.5, 1, 0.55, 0.1, a * 0.8)
        g.add_color_stop_rgba(1, 1, 0.2, 0.05, 0)
        ctx.set_source(g)
        ctx.arc(x, y, r, 0, 2 * PI)
        ctx.fill()
        for i in range(36):
            ang = rnd.uniform(0, 2 * PI)
            sp = rnd.uniform(150, 420)
            px = x + math.cos(ang) * sp * dt
            py = y + math.sin(ang) * sp * dt + 260 * dt * dt
            sparkle(ctx, px, py, rnd.uniform(5, 11) * clamp(1 - dt / 1.4),
                    rnd.choice(["#FFE45C", "#FF8A3D", "#FFFFFF"]), clamp(1.3 - dt))
    elif kind == "glitter":
        dur = e.get("dur", 4.0)
        if dt > dur:
            return
        if dt < 0.5:
            r = 20 + 140 * ease_out(dt / 0.35)
            a = clamp(1 - dt / 0.5)
            g = cairo.RadialGradient(x, y, 0, x, y, r)
            g.add_color_stop_rgba(0, 1, 1, 1, a)
            g.add_color_stop_rgba(0.6, 1, 0.5, 0.9, a * 0.6)
            g.add_color_stop_rgba(1, 1, 0.5, 0.9, 0)
            ctx.set_source(g)
            ctx.arc(x, y, r, 0, 2 * PI)
            ctx.fill()
        for i in range(160):
            ang = rnd.uniform(0, 2 * PI)
            sp = rnd.uniform(120, 560)
            drag = 2.4
            dist = sp * (1 - math.exp(-drag * dt)) / drag
            px = x + math.cos(ang) * dist + math.sin(dt * 3 + i) * 8
            py = y + math.sin(ang) * dist + 40 * dt * dt * rnd.uniform(0.5, 1.2)
            py = min(py, GROUND + rnd.uniform(0, 70))
            col = rnd.choice(["#FFE45C", "#FF7AD9", "#7AE7FF", "#FFFFFF", "#B98CFF", "#7CFF9B"])
            fade = clamp((dur - dt) / 1.2)
            tw_ = 0.5 + 0.5 * math.sin(t * 9 + i * 1.7)
            sparkle(ctx, px, py, rnd.uniform(3, 8) * (0.5 + tw_), col, fade)
    elif kind == "pop":
        if dt > 0.5:
            return
        for i in range(8):
            ang = i * PI / 4 + 0.3
            r0 = 10 + 50 * ease_out(dt / 0.4)
            sparkle(ctx, x + math.cos(ang) * r0, y + math.sin(ang) * r0, 7 * (1 - dt / 0.5), "#FFF6B0")
    elif kind == "ding":
        if dt > 0.9:
            return
        u = dt / 0.9
        sparkle(ctx, x, y, 26 * math.sin(u * PI), "#FFFFFF", 1.0)
        sparkle(ctx, x + 14, y - 12, 12 * math.sin(u * PI), "#FFF6B0", 1.0)
    elif kind == "dust":
        if dt > 1.0:
            return
        for i in range(6):
            r = 12 + 30 * dt + i * 3
            ellipse(ctx, x + (i - 2.5) * 16 * (1 + dt), y - 10 - dt * 20 - i % 2 * 8, r, r * 0.7)
            src(ctx, "#E9DCC8", 0.7 * (1 - dt))
            ctx.fill()


def draw_cloud(ctx, x, y, alpha, t, size=1.0, seed=5):
    if alpha <= 0.01:
        return
    rnd = random.Random(seed)
    ctx.push_group()
    for i in range(16):
        ang = rnd.uniform(0, 2 * PI)
        d = rnd.uniform(0, 70) * size
        px = x + math.cos(ang) * d * 1.3 + math.sin(t * 1.5 + i) * 6
        py = y + math.sin(ang) * d * 0.8 + math.cos(t * 1.2 + i) * 5
        r = rnd.uniform(40, 66) * size
        ellipse(ctx, px, py, r, r * 0.9)
        src(ctx, mix("#FFFFFF", "#FFC6EC", rnd.uniform(0, 0.6)))
        ctx.fill()
    for i in range(40):
        px = x + rnd.uniform(-110, 110) * size
        py = y + rnd.uniform(-70, 70) * size
        sparkle(ctx, px, py, 3 + 3 * (0.5 + 0.5 * math.sin(t * 8 + i)),
                rnd.choice(["#FFD54F", "#FF7AD9", "#7AE7FF", "#B98CFF"]))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


def draw_scorch(ctx, x, y, a):
    if a <= 0:
        return
    g = cairo.RadialGradient(x, y, 0, x, y, 60)
    g.add_color_stop_rgba(0, 0.1, 0.05, 0.05, 0.85 * a)
    g.add_color_stop_rgba(0.6, 0.2, 0.08, 0.05, 0.5 * a)
    g.add_color_stop_rgba(1, 0.2, 0.05, 0.05, 0)
    ctx.set_source(g)
    ctx.arc(x, y, 60, 0, 2 * PI)
    ctx.fill()


def draw_hand_mirror_arm(ctx, x, y, t, reflect_fn=None, ang=0.0):
    """A human arm reaching in from the right holding a hand mirror.
    (x, y) is the mirror glass center."""
    ctx.save()
    # sleeve + forearm from the right edge
    hx, hy = x + 30, y + 92
    ctx.move_to(W + 40, hy + 70)
    ctx.curve_to(W - 60, hy + 60, hx + 90, hy + 20, hx + 20, hy + 6)
    src(ctx, "#2E7D74")
    ctx.set_line_width(48)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.move_to(hx + 70, hy + 14)
    ctx.line_to(hx + 10, hy + 4)
    src(ctx, "#E2B38F")
    ctx.set_line_width(30)
    ctx.stroke()
    ctx.translate(x, y)
    ctx.rotate(ang)
    # handle
    rrect(ctx, -9, 40, 18, 70, 8)
    fill_stroke(ctx, "#C9CED6", "#5A6270", 3)
    # frame and glass
    ellipse(ctx, 0, 0, 52, 60)
    fill_stroke(ctx, "#D9DEE6", "#5A6270", 4)
    ellipse(ctx, 0, 0, 43, 51)
    g = cairo.LinearGradient(-40, -50, 40, 50)
    g.add_color_stop_rgb(0, *rgb("#E8F6FF"))
    g.add_color_stop_rgb(1, *rgb("#9CC9E8"))
    ctx.set_source(g)
    ctx.fill()
    if reflect_fn:
        ctx.save()
        ellipse(ctx, 0, 0, 43, 51)
        ctx.clip()
        reflect_fn(ctx)
        ctx.restore()
    ctx.move_to(-30, -20)
    ctx.line_to(-8, -42)
    src(ctx, "#FFFFFF", 0.7)
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.restore()
    # fingers wrapped around handle
    for i in range(4):
        ellipse(ctx, x + 2 + 0 * i, y + 62 + i * 11, 11, 6)
        fill_stroke(ctx, "#E2B38F", "#A9775A", 2)


# ---------------------------------------------------------------- subconscious
def draw_subconscious(ctx, t, door_open=0.0, door_glow=1.0):
    g = cairo.RadialGradient(640, 360, 50, 640, 360, 800)
    g.add_color_stop_rgb(0, *rgb("#4A2B8C"))
    g.add_color_stop_rgb(1, *rgb("#0E0626"))
    ctx.set_source(g)
    ctx.paint()
    # spiral arms
    for arm in range(5):
        a0 = arm * 2 * PI / 5 + t * 0.25
        ctx.move_to(640, 360)
        for i in range(1, 80):
            r = 8 * math.exp(i * 0.055)
            a = a0 + i * 0.13
            ctx.line_to(640 + math.cos(a) * r, 360 + math.sin(a) * r * 0.7)
        src(ctx, "#B39DFF", 0.13)
        ctx.set_line_width(14)
        ctx.stroke()
    rnd = random.Random(11)
    syms = ["?", "!", "zZ", "?", "!", "...", "~"]
    for i in range(26):
        bx = rnd.uniform(0, W)
        sp = rnd.uniform(12, 40)
        by = (rnd.uniform(0, H) - t * sp) % (H + 100) - 50
        r = rnd.uniform(14, 36)
        ellipse(ctx, bx + math.sin(t + i) * 10, by, r, r)
        src(ctx, "#D7C8FF", 0.10)
        ctx.fill_preserve()
        src(ctx, "#EDE5FF", 0.35)
        ctx.set_line_width(2)
        ctx.stroke()
        if i % 2 == 0:
            text(ctx, syms[i % len(syms)], bx + math.sin(t + i) * 10, by + r * 0.35, r * 0.9,
                 "#FFFFFF", alpha=0.35)
    # floating path
    for i in range(8):
        px = 80 + i * 130
        py = 600 + math.sin(t * 1.4 + i) * 6
        ellipse(ctx, px, py, 60, 14)
        src(ctx, "#7E62C9", 0.9)
        ctx.fill()
        ellipse(ctx, px, py - 4, 56, 10)
        src(ctx, "#A48BEA", 0.9)
        ctx.fill()
    # door on a cloud
    dx, dy = 1110, 600
    for i, (ox, r) in enumerate(((-70, 40), (-30, 52), (20, 48), (66, 38))):
        ellipse(ctx, dx + ox, dy + math.sin(t * 2 + i) * 2, r, r * 0.55)
        src(ctx, "#F1EAFF", 0.95)
        ctx.fill()
    if door_glow > 0:
        g = cairo.RadialGradient(dx, dy - 110, 10, dx, dy - 110, 190)
        g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.45 * door_glow)
        g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
        ctx.set_source(g)
        ctx.arc(dx, dy - 110, 190, 0, 2 * PI)
        ctx.fill()
    rrect(ctx, dx - 58, dy - 210, 116, 200, 14)
    fill_stroke(ctx, "#2A1446", "#E8B64A", 6)
    # door panel swings open
    ow = 112 * (1 - 0.85 * ease(door_open))
    rrect(ctx, dx - 56, dy - 208, ow, 196, 12)
    fill_stroke(ctx, "#E36BAE", "#7A1E52", 4)
    if door_open < 0.5:
        star_path(ctx, dx, dy - 140, 22, 10)
        fill_stroke(ctx, "#FFD54F", "#A0761A", 3)
        ellipse(ctx, dx + 36, dy - 100, 6, 6)
        src(ctx, "#FFD54F")
        ctx.fill()
    rrect(ctx, dx - 92, dy - 268, 184, 46, 10)
    fill_stroke(ctx, "#FFF3D6", "#A0761A", 4)
    text(ctx, "EMOTIONAL", dx, dy - 249, 17, "#7A1E52")
    text(ctx, "DRESSING ROOM", dx, dy - 229, 17, "#7A1E52")


# ---------------------------------------------------------------- dressing room
MIRROR = (735, 150, 330, 330)  # x, y, w, h of the glass
SINK_X = 690
_DR_CACHE = {}


def dressing_bg():
    if "bg" in _DR_CACHE:
        return _DR_CACHE["bg"]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    src(ctx, "#C98BB9")
    ctx.paint()
    for i in range(0, W, 64):
        ctx.rectangle(i, 0, 32, 540)
        src(ctx, "#B677A6")
        ctx.fill()
    ctx.rectangle(0, 520, W, 20)
    src(ctx, "#7D3F6E")
    ctx.fill()
    g = cairo.LinearGradient(0, 540, 0, H)
    g.add_color_stop_rgb(0, *rgb("#6B4127"))
    g.add_color_stop_rgb(1, *rgb("#3E2414"))
    ctx.rectangle(0, 540, W, H - 540)
    ctx.set_source(g)
    ctx.fill()
    for i in range(0, W, 90):
        ctx.move_to(i, 540)
        ctx.line_to(i - 40, H)
        src(ctx, "#2E190C", 0.5)
        ctx.set_line_width(2)
        ctx.stroke()
    # sign on wall
    star_path(ctx, 200, 150, 90, 42)
    fill_stroke(ctx, "#FFD54F", "#A0761A", 6)
    text(ctx, "EMOTIONAL", 200, 146, 19, "#7A1E52")
    text(ctx, "DRESSING", 200, 168, 19, "#7A1E52")
    text(ctx, "ROOM", 200, 190, 19, "#7A1E52")
    # coat rack with costumes
    ctx.rectangle(48, 250, 8, 300)
    src(ctx, "#4A2A16")
    ctx.fill()
    ellipse(ctx, 52, 548, 40, 8)
    src(ctx, "#4A2A16")
    ctx.fill()
    ctx.move_to(52, 270)
    ctx.line_to(20, 300)
    ctx.move_to(52, 270)
    ctx.line_to(84, 300)
    src(ctx, "#4A2A16")
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.move_to(84, 300)
    ctx.line_to(70, 400)
    ctx.line_to(110, 400)
    ctx.close_path()
    fill_stroke(ctx, "#4FC3F7", "#1A6A8C", 3)
    # counter
    rrect(ctx, 640, 490, 620, 30, 6)
    fill_stroke(ctx, "#F2E6D8", "#8D6E63", 4)
    ctx.rectangle(655, 520, 590, 95)
    src(ctx, "#8D5A3B")
    ctx.fill()
    for cx in (720, 870, 1020, 1170):
        rrect(ctx, cx - 60, 530, 120, 76, 6)
        fill_stroke(ctx, "#A06C4A", "#5D3A22", 3)
        ellipse(ctx, cx, 568, 6, 6)
        src(ctx, "#E8B64A")
        ctx.fill()
    # mirror frame
    mx, my, mw, mh = MIRROR
    rrect(ctx, mx - 22, my - 22, mw + 44, mh + 34, 26)
    fill_stroke(ctx, "#E8B64A", "#8C6418", 5)
    # towel ring
    ellipse(ctx, 1190, 330, 22, 22)
    src(ctx, "#C9CED6")
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.move_to(1170, 340)
    ctx.line_to(1165, 440)
    ctx.line_to(1215, 440)
    ctx.line_to(1210, 340)
    ctx.close_path()
    fill_stroke(ctx, "#FFFFFF", "#9E9E9E", 3)
    ctx.rectangle(1167, 410, 46, 8)
    src(ctx, "#F48FB1")
    ctx.fill()
    _DR_CACHE["bg"] = surf
    return surf


def draw_mirror_glass(ctx, t, reflect_fn=None, kiss=0.0):
    mx, my, mw, mh = MIRROR
    rrect(ctx, mx, my, mw, mh - 10, 16)
    g = cairo.LinearGradient(mx, my, mx + mw, my + mh)
    g.add_color_stop_rgb(0, *rgb("#D8EEF9"))
    g.add_color_stop_rgb(1, *rgb("#9CC2DA"))
    ctx.set_source(g)
    ctx.fill()
    ctx.save()
    rrect(ctx, mx, my, mw, mh - 10, 16)
    ctx.clip()
    # reflected wall
    for i in range(int(mx), int(mx + mw), 48):
        ctx.rectangle(i, my, 24, mh)
        src(ctx, "#B9A2C9", 0.35)
        ctx.fill()
    if reflect_fn:
        reflect_fn(ctx)
    # shine
    ctx.move_to(mx + 40, my + mh)
    ctx.line_to(mx + 130, my)
    ctx.line_to(mx + 170, my)
    ctx.line_to(mx + 80, my + mh)
    ctx.close_path()
    src(ctx, "#FFFFFF", 0.22)
    ctx.fill()
    if kiss > 0:
        draw_kiss_print(ctx, mx + mw * 0.36, my + 120, kiss)
    ctx.restore()


def draw_kiss_print(ctx, x, y, a):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.25)
    src(ctx, "#D6112F", 0.85 * a)
    ctx.move_to(-18, 0)
    ctx.curve_to(-12, -10, -4, -10, 0, -4)
    ctx.curve_to(4, -10, 12, -10, 18, 0)
    ctx.curve_to(10, 4, -10, 4, -18, 0)
    ctx.fill()
    ctx.move_to(-18, 2)
    ctx.curve_to(-10, 14, 10, 14, 18, 2)
    ctx.curve_to(10, 6, -10, 6, -18, 2)
    ctx.fill()
    ctx.restore()


def draw_bulbs(ctx, t, on=1.0):
    mx, my, mw, mh = MIRROR
    pts = []
    for i in range(6):
        pts.append((mx - 4 + i * (mw + 8) / 5, my - 30))
    for i in range(1, 5):
        pts.append((mx - 32, my - 30 + i * (mh + 10) / 5))
        pts.append((mx + mw + 32, my - 30 + i * (mh + 10) / 5))
    for (bx, by) in pts:
        if on > 0:
            g = cairo.RadialGradient(bx, by, 0, bx, by, 26)
            g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.6 * on)
            g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
            ctx.set_source(g)
            ctx.arc(bx, by, 26, 0, 2 * PI)
            ctx.fill()
        ellipse(ctx, bx, by, 11, 11)
        fill_stroke(ctx, mix("#9E9E9E", "#FFF8E1", on), "#8C6418", 2)


def draw_sink(ctx, t, water=0.0):
    x = SINK_X
    ellipse(ctx, x, 494, 52, 12)
    fill_stroke(ctx, "#E3EEF5", "#7C93A3", 3)
    ellipse(ctx, x, 494, 40, 7)
    src(ctx, "#B7CCD9")
    ctx.fill()
    # faucet
    ctx.move_to(x + 36, 488)
    ctx.line_to(x + 36, 440)
    ctx.curve_to(x + 36, 424, x + 10, 424, x + 10, 440)
    src(ctx, "#AEB8C2")
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.move_to(x + 36, 488)
    ctx.line_to(x + 36, 440)
    ctx.curve_to(x + 36, 424, x + 10, 424, x + 10, 440)
    src(ctx, "#E6ECF2")
    ctx.set_line_width(5)
    ctx.stroke()
    ellipse(ctx, x + 50, 470, 8, 5)
    fill_stroke(ctx, "#E6ECF2", "#7C93A3", 2)
    if water > 0:
        for i in range(4):
            ox = (i - 1.5) * 2.5
            ctx.move_to(x + 10 + ox, 444)
            yy = 444
            while yy < 490:
                yy += 6
                ctx.line_to(x + 10 + ox + math.sin(t * 40 + yy * 0.3 + i) * 1.2, yy)
            src(ctx, "#7FD3FF", 0.7 * water)
            ctx.set_line_width(2.2)
            ctx.stroke()


# ---------------------------------------------------------------- overlays
SPEAKER_COL = {"narr": "#FFFFFF", "me": "#FFFFFF", "anger": "#FF9C8F", "doubt": "#D7C2FF",
               "boredom": "#C3D7E3"}


def wrap(ctx, s, size, maxw):
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_width(ctx, trial, size) > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_subtitle(ctx, s, who, alpha=1.0):
    if not s or alpha <= 0:
        return
    size = 30
    lines = wrap(ctx, s, size, 1040)
    lh = 38
    y0 = H - 26 - lh * (len(lines) - 1)
    col = SPEAKER_COL.get(who, "#FFFFFF")
    bw = max(text_width(ctx, ln, size) for ln in lines) + 44
    rrect(ctx, W / 2 - bw / 2, y0 - 34, bw, lh * len(lines) + 16, 14)
    ctx.set_source_rgba(0.05, 0.02, 0.1, 0.55 * alpha)
    ctx.fill()
    for i, ln in enumerate(lines):
        text(ctx, ln, W / 2, y0 + i * lh, size, col, outline="#120A1C", olw=7, alpha=alpha)


def draw_title_card(ctx, t, title, subtitle, part, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    g = cairo.RadialGradient(640, 360, 40, 640, 360, 760)
    g.add_color_stop_rgb(0, *rgb("#5B2C9E"))
    g.add_color_stop_rgb(1, *rgb("#12062A"))
    ctx.set_source(g)
    ctx.paint()
    for i in range(16):
        ang = t * 0.15 + i * PI / 8
        ctx.move_to(640, 330)
        ctx.line_to(640 + math.cos(ang - 0.08) * 1000, 330 + math.sin(ang - 0.08) * 1000)
        ctx.line_to(640 + math.cos(ang + 0.08) * 1000, 330 + math.sin(ang + 0.08) * 1000)
        ctx.close_path()
        src(ctx, "#FFFFFF", 0.04)
        ctx.fill()
    rnd = random.Random(21)
    for i in range(50):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        sparkle(ctx, x, y, rnd.uniform(3, 9) * (0.5 + 0.5 * math.sin(t * 3 + i)), "#FFF6B0", 0.8)
    if part:
        text(ctx, part, 640, 190, 34, "#FFD54F", outline="#3A1466", olw=6)
    sc = 1 + 0.02 * math.sin(t * 2)
    ctx.save()
    ctx.translate(640, 300)
    ctx.scale(sc, sc)
    text(ctx, title, 0, 0, 76, "#FFFFFF", outline="#E0283F", olw=12)
    ctx.restore()
    if subtitle:
        text(ctx, subtitle, 640, 400, 46, "#FFD54F", outline="#3A1466", olw=8)
    # tiny cast parade along the bottom
    for i, kind in enumerate(("doubt", "anger", "boredom")):
        c = new_char(kind, 420 + i * 220, s=0.62, mouth="smile", y=640)
        c["y"] = 650 + math.sin(t * 3 + i) * 4 - 40
        draw_char(ctx, c, t + i)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_end_card(ctx, t, title, sub, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    src(ctx, "#12062A")
    ctx.paint()
    rnd = random.Random(31)
    for i in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        sparkle(ctx, x, y, rnd.uniform(3, 8) * (0.5 + 0.5 * math.sin(t * 3 + i)), "#FFF6B0", 0.8)
    text(ctx, title, 640, 350, 84, "#FFFFFF", outline="#E0283F", olw=12)
    if sub:
        text(ctx, sub, 640, 430, 36, "#FFD54F", outline="#3A1466", olw=6)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_swirl(ctx, t, amt):
    if amt <= 0:
        return
    ctx.save()
    ctx.push_group()
    src(ctx, "#1A0B3D")
    ctx.paint()
    for arm in range(8):
        a0 = arm * 2 * PI / 8 + t * 3
        ctx.move_to(640, 360)
        for i in range(1, 70):
            r = 6 * math.exp(i * 0.07)
            a = a0 + i * 0.16
            ctx.line_to(640 + math.cos(a) * r, 360 + math.sin(a) * r)
        src(ctx, "#C9B3FF", 0.5)
        ctx.set_line_width(18)
        ctx.stroke()
    ctx.pop_group_to_source()
    # iris reveal
    r = 900 * ease(amt)
    ctx.arc(640, 360, r, 0, 2 * PI)
    ctx.clip()
    ctx.paint()
    ctx.restore()
