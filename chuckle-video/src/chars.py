"""Characters: generic expressive face + per-character bodies."""
import math
import skia
from gfx import *

SKIN_LORD = "#f1c9a5"
SKIN_CREATOR = "#c98d63"

# ---------------------------------------------------------------------- face parts

FACE_DEFAULT = dict(lid=1.0, lidL=None, lidR=None, lower=0.0, lid_tilt=0.0, px=0.0, py=0.0, pr=1.0,
                    squeeze=0.0, happy=0.0, brow_y=0.0, brow_ang=0.0, browL=0.0, browR=0.0,
                    mouth_open=0.0, smile=0.2, mouth_w=1.0, asym=0.0, wobble=0.0, teeth=False,
                    clench=0.0, puff=0.0, red=0.0, pale=0.0, sweat=0.0, tears=0.0, blush=0.0,
                    light=None, light_a=0.0, t=0.0, jaw=0.0)


def P_(**kw):
    p = dict(FACE_DEFAULT)
    p.update(kw)
    return p


def head_path(hw, hh, jowl=0.1, puff=0.0, top_flat=0.95, chin=0.0):
    pts = []
    n = 32
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * hw, math.sin(a) * hh
        b = math.exp(-((a - math.pi / 4) / 0.5) ** 2) + math.exp(-((a - 3 * math.pi / 4) / 0.5) ** 2)
        k = 1 + jowl * b
        # puffed cheeks bulge out sideways, just below eye level (held breath), not down past the jaw
        def g(a0):
            d = math.atan2(math.sin(a - a0), math.cos(a - a0))
            return math.exp(-(d / 0.42) ** 2)
        side = g(0.3) + g(math.pi - 0.3)
        kx = k + 0.27 * puff * side
        ch = chin * math.exp(-((a - math.pi / 2) / 0.35) ** 2)
        yy = y * (k if y > 0 else top_flat) + ch * hh - 0.05 * puff * hh * side
        pts.append((x * kx, yy))
    return smooth_path(pts)


def draw_eye(c, x, y, rx, ry, P, side, skin, iris="#4a3426", lash=OUT):
    """side: -1 = viewer's left eye, +1 = viewer's right eye"""
    t = P["t"]
    lid = P["lidL"] if (side < 0 and P["lidL"] is not None) else P["lidR"] if (side > 0 and P["lidR"] is not None) else P["lid"]
    if P["squeeze"] > 0.5:
        # >  < squeezed shut
        d = 1 if side < 0 else -1
        p = skia.Path()
        p.moveTo(x - rx * 0.8 * d, y - ry * 0.55)
        p.lineTo(x + rx * 0.7 * d, y)
        p.lineTo(x - rx * 0.8 * d, y + ry * 0.55)
        c.drawPath(p, stroke(lash, 6))
        return
    if lid < 0.08:
        p = skia.Path()
        if P["happy"] > 0.5:
            p.moveTo(x - rx, y + ry * 0.15)
            p.quadTo(x, y - ry * 0.75, x + rx, y + ry * 0.15)
        else:
            p.moveTo(x - rx, y + ry * 0.05)
            p.quadTo(x, y + ry * 0.45, x + rx, y + ry * 0.05)
        c.drawPath(p, stroke(lash, 5.5))
        return
    sc = oval(x, y, rx, ry)
    c.drawPath(sc, fill("#ffffff"))
    c.save()
    c.clipPath(sc, skia.ClipOp.kIntersect, True)
    ir = rx * 0.58
    ix = x + P["px"] * rx * 0.5
    iy = y + P["py"] * ry * 0.45
    c.drawCircle(ix, iy, ir, fill(iris))
    c.drawCircle(ix, iy, ir * 0.52 * P["pr"], fill("#120c10"))
    c.drawCircle(ix - ir * 0.35, iy - ir * 0.38, ir * 0.24, fill("#ffffff", 0.9))
    # upper lid
    tilt = P["lid_tilt"] * ry * 0.6 * (1 if side < 0 else -1)  # + : inner corner lower (angry)
    yl = y - ry + (1 - clamp(lid, 0, 1.2)) * 2 * ry
    sag = ry * 0.25 * (1 if lid < 0.98 else 0)
    lp = skia.Path()
    lp.moveTo(x - rx - 3, y - ry - 6)
    lp.lineTo(x + rx + 3, y - ry - 6)
    lp.lineTo(x + rx + 3, yl + tilt)
    lp.quadTo(x, yl + sag, x - rx - 3, yl - tilt)
    lp.close()
    if lid < 0.99 or abs(tilt) > 0.01:
        c.drawPath(lp, fill(skin))
        ln = skia.Path()
        ln.moveTo(x - rx - 3, yl - tilt)
        ln.quadTo(x, yl + sag, x + rx + 3, yl + tilt)
        c.drawPath(ln, stroke(lash, 5))
    if P["lower"] > 0.01:
        yb = y + ry - P["lower"] * ry * 1.1
        bp_ = skia.Path()
        bp_.moveTo(x - rx - 3, y + ry + 6)
        bp_.lineTo(x + rx + 3, y + ry + 6)
        bp_.lineTo(x + rx + 3, yb + ry * 0.2)
        bp_.quadTo(x, yb - ry * 0.25, x - rx - 3, yb + ry * 0.2)
        bp_.close()
        c.drawPath(bp_, fill(skin))
        bl = skia.Path()
        bl.moveTo(x - rx, yb + ry * 0.15)
        bl.quadTo(x, yb - ry * 0.25, x + rx, yb + ry * 0.15)
        c.drawPath(bl, stroke(lash, 3, 0.7))
    c.restore()
    c.drawPath(sc, stroke(lash, 4.5))
    # tears welling
    if P["tears"] > 0.05:
        tx = x + rx * 0.8 * (-1 if side < 0 else 1)
        c.drawPath(oval(tx, y + ry * 0.7, 7 * P["tears"], 9 * P["tears"]), fill("#8fd3ff", 0.9))
        if P["tears"] > 0.55:
            k = (t * 0.9 + (0.3 if side > 0 else 0)) % 1.0
            ty = y + ry + 10 + k * 90
            d = skia.Path()
            d.moveTo(tx, y + ry * 0.7)
            d.lineTo(tx + 2 * side, ty)
            c.drawPath(d, stroke("#8fd3ff", 6 * (P["tears"] - 0.4), 0.8))
            c.drawPath(oval(tx + 2 * side, ty, 6, 8), fill("#8fd3ff", 0.9))


def draw_brow(c, x, y, w, ang, side, color="#3b2a20", thick=10):
    """ang>0 worried (inner up), ang<0 angry (inner down)."""
    inner = 1 if side < 0 else -1  # inner end direction in x
    p = skia.Path()
    xi, xo = x + inner * w, x - inner * w
    yi, yo = y - ang * 14, y + ang * 4
    p.moveTo(xo, yo)
    p.quadTo(x, min(yi, yo) - 8, xi, yi)
    c.drawPath(p, stroke(color, thick))


def draw_mouth(c, x, y, w, P, inside="#5a1626"):
    t = P["t"]
    s = P["smile"]
    o = clamp(P["mouth_open"], 0, 1.3)
    asym = P["asym"]
    w = w * P["mouth_w"] * (1 - 0.25 * o)
    Lx, Ly = x - w, y - s * 14 + asym * 10
    Rx, Ry = x + w, y - s * 14 - asym * 10
    if P["clench"] > 0.05:
        h = 10 + 16 * P["clench"]
        r = rrect(x - w, y - h / 2, 2 * w, h, 6)
        c.drawPath(r, fill("#fffdf5"))
        c.drawPath(skia.Path().moveTo(x - w, y).lineTo(x + w, y) if False else poly([(x - w, y), (x + w, y)], False), stroke(OUT, 2.5))
        for i in range(1, 6):
            xx = x - w + 2 * w * i / 6
            c.drawPath(poly([(xx, y - h / 2), (xx, y + h / 2)], False), stroke(OUT, 2))
        c.drawPath(r, stroke(OUT, 4.5))
        return
    if o < 0.06:
        if P["wobble"] > 0.01:
            pts = []
            for i in range(13):
                u = i / 12
                xx = lerp(Lx, Rx, u)
                yy = lerp(Ly, Ry, u) + s * 16 * math.sin(math.pi * u) + P["wobble"] * 5 * math.sin(u * 18 + t * 30)
                pts.append((xx, yy))
            c.drawPath(smooth_path(pts, False), stroke(OUT, 5))
        else:
            p = skia.Path()
            p.moveTo(Lx, Ly)
            p.quadTo(x, y + s * 18, Rx, Ry)
            c.drawPath(p, stroke(OUT, 5))
        return
    up = skia.Path()
    up.moveTo(Lx, Ly)
    up.quadTo(x, y + s * 8 - o * 8, Rx, Ry)
    up.quadTo(x, y + s * 20 + o * 52, Lx, Ly)
    up.close()
    c.drawPath(up, fill(inside))
    c.save()
    c.clipPath(up, skia.ClipOp.kIntersect, True)
    c.drawPath(oval(x, y + s * 14 + o * 46, w * 0.62, 18 + o * 8), fill("#e2677a"))
    if P["teeth"]:
        c.drawRect(skia.Rect.MakeLTRB(x - w, y - 30, x + w, y + s * 4 - o * 4 + 8), fill("#fffdf5"))
    c.restore()
    c.drawPath(up, stroke(OUT, 4.5))


def sweat_drops(c, hw, hh, amount, t, seed=0):
    n = int(1 + amount * 4)
    for i in range(n):
        side = -1 if i % 2 == 0 else 1
        ph = (t * (0.35 + 0.1 * i) + hash1(i + seed) * 0.5) % 1.0
        x = side * hw * (0.55 + 0.25 * hash1(i * 3 + seed))
        y = -hh * 0.5 + ph * hh * 0.9
        a = clamp(amount * 1.5) * (1 - ph ** 3)
        r = 7 + 4 * hash1(i * 7)
        p = skia.Path()
        p.moveTo(x, y - r * 2.0)
        p.cubicTo(x + r * 1.1, y - r * 0.3, x + r, y + r, x, y + r)
        p.cubicTo(x - r, y + r, x - r * 1.1, y - r * 0.3, x, y - r * 2.0)
        c.drawPath(p, fill("#9fe0ff", a))
        c.drawPath(p, stroke("#3f8fb8", 2.5, a))


# ---------------------------------------------------------------------- the Logical Lord

def lord_head(c, P, fedora=True, fedora_tilt=0.0, fedora_dy=0.0, glasses=True, glass_glow=None, glow_a=0.0,
              deflate=0.0, clown_nose=0.0, dart=0.0, dart_wob=0.0, sunglasses=0.0):
    t = P["t"]
    skin = hexs(mix(mix(SKIN_LORD, "#e3322a", P["red"] * 0.85), "#b8cf95", P["pale"]))
    hw, hh = 108 * (1 - 0.08 * deflate), 112 * (1 - 0.2 * deflate)
    # ears
    for s in (-1, 1):
        fs(c, oval(s * hw * 0.98, 5, 18, 26), skin, 4)
    # hair under the hat
    for s in (-1, 1):
        pts = [(s * hw * 0.55, -hh * 0.75), (s * hw * 1.05, -hh * 0.55), (s * hw * 1.08, -hh * 0.1), (s * hw * 0.9, -hh * 0.3)]
        fs(c, smooth_path(pts), "#5a3d2b", 3)
    hp_ = head_path(hw, hh, 0.13 + 0.1 * deflate, P["puff"])
    fs(c, hp_, skin, 5)
    c.save()
    c.clipPath(hp_, skia.ClipOp.kIntersect, True)
    # neckbeard / stubble
    nb = skia.Path()
    nb.moveTo(-hw * 0.95, hh * 0.15)
    nb.quadTo(-hw * 0.9, hh * 1.25, 0, hh * 1.2)
    nb.quadTo(hw * 0.9, hh * 1.25, hw * 0.95, hh * 0.15)
    nb.quadTo(hw * 0.7, hh * 0.85, 0, hh * 0.92)
    nb.quadTo(-hw * 0.7, hh * 0.85, -hw * 0.95, hh * 0.15)
    c.drawPath(nb, fill("#5a3d2b", 0.75))
    for i in range(22):
        a = math.pi * (0.12 + 0.76 * i / 21)
        x0, y0 = math.cos(a) * hw * 0.92, math.sin(a) * hh * 0.98
        c.drawPath(poly([(x0, y0), (x0 * 0.97, y0 + 10)], False), stroke("#3b2618", 2.5))
    # puffed cheeks: round, high, inflated from held breath
    if P["puff"] > 0.12:
        pf = clamp(P["puff"])
        for s_ in (-1, 1):
            cx_, cy_ = s_ * hw * 0.74, 26
            r_ = 22 + 16 * pf
            c.drawPath(oval(cx_, cy_, r_, r_ * 0.9), fill(hexs(mix(skin, "#ffffff", 0.12)), 0.9 * pf))
            arc = skia.Path()
            arc.arcTo(skia.Rect.MakeLTRB(cx_ - r_, cy_ - r_ * 0.9, cx_ + r_, cy_ + r_ * 0.9), 20 if s_ > 0 else 100, 60, True)
            c.drawPath(arc, stroke(OUT, 3, 0.55 * pf))
            c.drawPath(oval(cx_ - s_ * r_ * 0.3, cy_ - r_ * 0.35, r_ * 0.28, r_ * 0.18), fill("#ffffff", 0.45 * pf))
    # cheeks blush / red
    if P["blush"] > 0 or P["red"] > 0.3:
        a = max(P["blush"], (P["red"] - 0.3))
        for s in (-1, 1):
            c.drawPath(oval(s * 62, 38, 26, 16), fill("#ff5d5d", 0.45 * clamp(a), blur=6))
    # screen light
    if P["light"]:
        c.drawRect(skia.Rect.MakeLTRB(-200, -200, 200, 200), lin_grad(0, 160, 0, -120, [P["light"], P["light"]], None, 0.0))
        c.drawRect(skia.Rect.MakeLTRB(-200, -200, 200, 200), rad_grad(0, 120, 220, [P["light"], P["light"]], [0, 1], [P["light_a"], 0.0]))
    c.restore()
    if deflate > 0.2:
        for i in range(4):
            yy = -40 + i * 28
            c.drawPath(poly([(-hw * 0.7, yy + 5), (-hw * 0.5, yy), (-hw * 0.35, yy + 6)], False), stroke(OUT, 2.5, deflate * 0.6))
            c.drawPath(poly([(hw * 0.7, yy + 2), (hw * 0.5, yy + 8), (hw * 0.3, yy + 3)], False), stroke(OUT, 2.5, deflate * 0.6))
    # eyes
    ey = -2
    for s in (-1, 1):
        draw_eye(c, s * 42, ey, 25, 29, P, s, skin, iris="#5b7a3a")
    # brows
    for s in (-1, 1):
        extra = P["browL"] if s < 0 else P["browR"]
        draw_brow(c, s * 42, ey - 44 - P["brow_y"] * 14 - extra * 14, 26, P["brow_ang"], s, "#4a3020", 11)
    # glasses
    if glasses:
        for s in (-1, 1):
            g = rrect(s * 42 - 37, ey - 32, 74, 62, 14)
            if glass_glow and glow_a > 0:
                c.drawPath(g, fill(glass_glow, 0.55 * glow_a))
            c.drawPath(g, stroke("#1d1a22", 7))
            c.save()
            c.clipPath(g, skia.ClipOp.kIntersect, True)
            gl = 0.22 + 0.4 * glow_a
            c.drawPath(poly([(s * 42 - 30, ey + 30), (s * 42 + 10, ey - 34)], False), stroke("#ffffff", 9, gl))
            c.drawPath(poly([(s * 42 - 12, ey + 34), (s * 42 + 26, ey - 30)], False), stroke("#ffffff", 4, gl))
            c.restore()
        c.drawPath(poly([(-5, ey - 6), (5, ey - 6)], False), stroke("#1d1a22", 6))
    if sunglasses > 0:
        dy = -260 * (1 - ease_out_back(sunglasses, 1.2))
        c.save()
        c.translate(0, dy)
        for s in (-1, 1):
            fs(c, poly([(s * 6, ey - 28), (s * 82, ey - 28), (s * 82, ey - 4), (s * 70, ey - 4), (s * 70, ey + 8), (s * 18, ey + 8), (s * 18, ey - 4), (s * 6, ey - 4)]), "#111111", 3, "#000000")
        c.drawRect(skia.Rect.MakeLTRB(-90, ey - 38, 90, ey - 26), fill("#111111"))
        for i in range(6):
            c.drawRect(skia.Rect.MakeXYWH(-70 + i * 10, ey - 24 + (i % 2) * 6, 6, 6), fill("#ffffff", 0.8))
        c.restore()
    # nose
    if clown_nose > 0:
        r = 22 * ease_out_back(clown_nose, 3)
        c.drawCircle(0, 34, r, fill("#e8202a"))
        c.drawCircle(0, 34, r, stroke(OUT, 4))
        c.drawCircle(-r * 0.35, 34 - r * 0.35, r * 0.25, fill("#ffffff", 0.8))
    else:
        nose = skia.Path()
        nose.moveTo(-8, 18)
        nose.cubicTo(-26, 30, -18, 48, 0, 46)
        nose.cubicTo(18, 48, 26, 30, 8, 18)
        fs(c, nose, hexs(mix(skin, "#d98b78", 0.35 + 0.3 * P["red"])), 4)
    draw_mouth(c, 0, 72 + P["jaw"] * 6, 34, P)
    if P["sweat"] > 0.02:
        sweat_drops(c, hw, hh, P["sweat"], t, 3)
    # fedora
    if fedora:
        c.save()
        c.translate(0, -hh * 0.78 + fedora_dy)
        c.rotate(fedora_tilt)
        crown = skia.Path()
        crown.moveTo(-82, 0)
        crown.cubicTo(-90, -60, -70, -102, -30, -98)
        crown.quadTo(0, -82, 30, -98)
        crown.cubicTo(70, -102, 90, -60, 82, 0)
        crown.close()
        fs(c, crown, "#3a3842", 5)
        c.drawRect(skia.Rect.MakeLTRB(-84, -30, 84, -6), fill("#1b1a20"))
        c.drawPath(poly([(-30, -96), (0, -70), (30, -96)], False), stroke("#2a2830", 4))
        brim = oval(0, 2, 150, 26)
        fs(c, brim, "#2f2d36", 5)
        c.drawPath(oval(0, -4, 84, 10), fill("#1b1a20"))
        c.restore()
    # dart (stuck between the brows, drawn last so it sits on top)
    if dart > 0:
        c.save()
        c.translate(0, ey - 50)
        c.rotate(28 + dart_wob * 14 * math.sin(t * 22))
        c.scale(dart, dart)
        fs(c, rrect(-11, -100, 22, 92, 9), "#ff8c2a", 4)
        for i in range(3):
            c.drawPath(poly([(-9, -82 + i * 22), (9, -82 + i * 22)], False), stroke("#d86a10", 3))
        fs(c, oval(0, -4, 22, 13), "#2a7de1", 4)
        c.restore()


SHIRT_LORD = "#3f6a6a"


def arm(c, sx, sy, ex, ey, hx, hy, sleeve, skin, hand="fist", side=1, t=0.0, curl=0.0, cheeto=True, w=44):
    # upper arm (sleeve) and forearm (skin)
    p1 = poly([(sx, sy), (ex, ey)], False)
    p2 = poly([(ex, ey), (hx, hy)], False)
    c.drawPath(p2, stroke(OUT, w + 9))
    c.drawPath(p2, stroke(skin, w))
    c.drawPath(p1, stroke(OUT, w + 13))
    c.drawPath(p1, stroke(sleeve, w + 4))
    draw_hand(c, hx, hy, hand, side, skin, t, curl, cheeto)


def draw_hand(c, x, y, kind, side, skin, t=0.0, curl=0.0, cheeto=True):
    tip = "#ff8a1e" if cheeto else skin
    if kind == "quote":
        fs(c, oval(x, y, 24, 22), skin, 4)
        for i, dx in enumerate((-9, 9)):
            ang = curl * 70
            c.save()
            c.translate(x + dx, y - 16)
            c.rotate(-ang * side)
            fs(c, rrect(-6, -34, 12, 36, 6), skin, 3.5)
            c.drawCircle(0, -30, 5, fill(tip))
            c.restore()
        return
    if kind == "point":
        fs(c, oval(x, y, 24, 22), skin, 4)
        c.save()
        c.translate(x, y)
        c.rotate(200 * side)
        fs(c, rrect(-6, -52, 12, 40, 6), skin, 3.5)
        c.drawCircle(0, -48, 5, fill(tip))
        c.restore()
        return
    if kind == "open":
        for i in range(4):
            a = -math.pi / 2 + (i - 1.5) * 0.35
            fx, fy = x + math.cos(a) * 30, y + math.sin(a) * 30
            c.drawPath(poly([(x, y), (fx, fy)], False), stroke(OUT, 15))
            c.drawPath(poly([(x, y), (fx, fy)], False), stroke(skin, 9))
            c.drawCircle(fx, fy, 4.5, fill(tip))
        fs(c, oval(x, y, 24, 22), skin, 4)
        return
    # fist / default
    fs(c, oval(x, y, 25, 23), skin, 4)
    for i in range(3):
        c.drawPath(poly([(x - 14 + i * 12, y - 12), (x - 14 + i * 12, y - 2)], False), stroke(OUT, 2.5))
    c.drawCircle(x - 12, y - 16, 4, fill(tip))
    c.drawCircle(x + 10, y - 16, 4, fill(tip))


ARM_POSES = {
    #          elbow(x,y)     hand(x,y)    hand kind
    "type": ((175, 300), (118, 360), "fist"),
    "rest": ((180, 310), (130, 380), "fist"),
    "quote": ((215, 180), (170, -20), "quote"),
    "point": ((185, 250), (95, 205), "point"),
    "knuck": ((160, 250), (28, 215), "fist"),
    "temple": ((205, 170), (118, -5), "open"),
    "flag": ((220, 180), (190, -60), "fist"),
    "clutch": ((175, 260), (60, 270), "open"),
    "mouth": ((190, 230), (30, 88), "open"),
    "up": ((230, 80), (250, -120), "open"),
}


def lord_body(c, P, poseL="type", poseR="type", blendL=None, blendR=None, t=0.0, lean=0.0, head_rot=0.0,
              head_dx=0.0, head_dy=0.0, shake=0.0, typing=0.0, quote_curl=0.0, flag=0.0, **headkw):
    """Upper body (front view) with head center at (0,0)."""
    skin = hexs(mix(SKIN_LORD, "#b8cf95", P["pale"] * 0.5))
    sh = SHIRT_LORD
    # torso
    torso = skia.Path()
    torso.moveTo(-150, 150)
    torso.cubicTo(-190, 170, -200, 260, -190, 420)
    torso.lineTo(190, 420)
    torso.cubicTo(200, 260, 190, 170, 150, 150)
    torso.quadTo(0, 120, -150, 150)
    fs(c, torso, sh, 5)
    # belly roll + print
    c.drawPath(poly([(-120, 330), (0, 345), (120, 330)], False), stroke("#2d4f4f", 4))
    text(c, "r/LOGIC", 0, 270, "inter_black", 30, "#f2e6c9", a=0.9)
    c.drawPath(oval(0, 214, 22, 20), stroke("#f2e6c9", 4, 0.9))
    c.drawPath(poly([(-12, 214), (12, 214)], False), stroke("#f2e6c9", 3, 0.9))
    # neck
    fs(c, rrect(-55, 80, 110, 80, 30), skin, 5)

    def arm_for(side, pose, blend):
        e, h, kind = ARM_POSES[pose]
        if blend:
            p2, u = blend
            e2, h2, kind2 = ARM_POSES[p2]
            e = (lerp(e[0], e2[0], u), lerp(e[1], e2[1], u))
            h = (lerp(h[0], h2[0], u), lerp(h[1], h2[1], u))
            kind = kind if u < 0.5 else kind2
        hx, hy = h
        if pose == "type" or (blend and blend[0] == "type" and blend[1] > 0.5):
            hy += typing * 8 * math.sin(t * 22 + (0 if side < 0 else 1.7))
        arm(c, side * 160, 180, side * e[0], e[1], side * hx, hy, sh, skin, kind, side, t, quote_curl)
        return side * hx, hy, kind

    hl = arm_for(-1, poseL, blendL)
    hr = arm_for(1, poseR, blendR)
    if flag > 0:
        x, y = hr[0], hr[1]
        c.drawPath(poly([(x, y + 20), (x, y - 120 * flag)], False), stroke("#7b5a3a", 6))
        wv = math.sin(t * 9)
        fl = smooth_path([(x, y - 120 * flag), (x + 40, y - 125 * flag + wv * 6), (x + 80, y - 118 * flag - wv * 4),
                          (x + 80, y - 75 * flag - wv * 4), (x + 40, y - 80 * flag + wv * 6), (x, y - 72 * flag)])
        fs(c, fl, "#ffffff", 4)
    c.save()
    c.translate(head_dx + shake * 6 * math.sin(t * 61), head_dy + lean * 20 + shake * 4 * math.sin(t * 53))
    c.rotate(head_rot)
    lord_head(c, P, **headkw)
    c.restore()
    return hl, hr


# ---------------------------------------------------------------------- creator

def creator_head(c, P):
    skin = SKIN_CREATOR
    hw, hh = 100, 108
    for s in (-1, 1):
        fs(c, oval(s * hw * 0.98, 8, 16, 24), skin, 4)
    hp_ = head_path(hw, hh, 0.04, P["puff"], 0.95)
    fs(c, hp_, skin, 5)
    # hair
    hair = []
    for i in range(15):
        a = math.pi + math.pi * i / 14
        r = hh * (1.12 + 0.14 * (i % 2))
        hair.append((math.cos(a) * hw * 1.08, math.sin(a) * r * 0.9 - 18))
    hair += [(hw * 0.95, -20), (hw * 0.5, -58), (0, -48), (-hw * 0.5, -60), (-hw * 0.98, -16)]
    fs(c, smooth_path(hair), "#2b1d1a", 4)
    ey = 4
    for s in (-1, 1):
        draw_eye(c, s * 40, ey, 24, 28, P, s, skin, iris="#3a2414")
        extra = P["browL"] if s < 0 else P["browR"]
        draw_brow(c, s * 40, ey - 42 - P["brow_y"] * 14 - extra * 14, 24, P["brow_ang"], s, "#2b1d1a", 10)
    if P["blush"] > 0:
        for s in (-1, 1):
            c.drawPath(oval(s * 60, 44, 22, 13), fill("#ff6a6a", 0.4 * P["blush"], blur=5))
    nose = skia.Path()
    nose.moveTo(-4, 24)
    nose.quadTo(-16, 44, 0, 44)
    c.drawPath(nose, stroke("#8a5638", 4))
    draw_mouth(c, 0, 68, 32, P)


def creator_body(c, P, t=0.0, typing=0.0, poseR=None, mug=0.0, head_dy=0.0, head_rot=0.0, enter=0.0):
    skin = SKIN_CREATOR
    hood = "#5a4bd6"
    torso = skia.Path()
    torso.moveTo(-145, 150)
    torso.cubicTo(-185, 170, -195, 260, -185, 420)
    torso.lineTo(185, 420)
    torso.cubicTo(195, 260, 185, 170, 145, 150)
    torso.quadTo(0, 125, -145, 150)
    fs(c, torso, hood, 5)
    c.drawPath(poly([(-30, 160), (-24, 260)], False), stroke("#e7e2ff", 4))
    c.drawPath(poly([(30, 160), (24, 260)], False), stroke("#e7e2ff", 4))
    fs(c, rrect(-48, 85, 96, 75, 28), skin, 5)
    # headphones around neck
    hpp = skia.Path()
    hpp.moveTo(-95, 150)
    hpp.quadTo(0, 215, 95, 150)
    c.drawPath(hpp, stroke(OUT, 18))
    c.drawPath(hpp, stroke("#3a3a46", 12))
    for s in (-1, 1):
        fs(c, rrect(s * 98 - 22, 125, 44, 52, 16), "#3a3a46", 4)
        c.drawPath(oval(s * 98, 151, 12, 16), fill("#7ef0ff", 0.8))
    def draw_arm(side):
        hx, hy = side * 118, 360 + typing * 8 * math.sin(t * 20 + (0 if side < 0 else 1.9))
        kind = "fist"
        ex, ey = side * 175, 300
        if side > 0 and enter > 0:
            hy = 360 - 120 * math.sin(math.pi * clamp(enter)) if enter < 1 else 360
        if side > 0 and mug > 0:
            hx, hy = lerp(118, 150, mug), lerp(360, 95, mug)
            ex, ey = lerp(175, 215, mug), lerp(300, 250, mug)
        arm(c, side * 155, 180, ex, ey, hx, hy, hood, skin, kind, side, t, 0, cheeto=False)
        if side > 0 and mug > 0:
            fs(c, rrect(hx - 30, hy - 62, 54, 62, 8), "#f2f2f2", 4)
            c.drawPath(oval(hx + 28, hy - 32, 14, 16), stroke(OUT, 6))
            c.drawPath(oval(hx + 28, hy - 32, 14, 16), stroke("#f2f2f2", 3))
            text(c, "MEME", hx - 3, hy - 22, "inter_black", 14, "#5a4bd6")
            for k in range(3):
                yy = hy - 75 - k * 16 - (t * 20 % 16)
                c.drawPath(smooth_path([(hx - 8 + k * 8, yy + 14), (hx - 2 + k * 8, yy + 7), (hx - 8 + k * 8, yy)], False), stroke("#ffffff", 3, 0.5))

    draw_arm(-1)
    if mug <= 0:
        draw_arm(1)
    c.save()
    c.translate(0, head_dy)
    c.rotate(head_rot)
    creator_head(c, P)
    c.restore()
    if mug > 0:
        draw_arm(1)


# ---------------------------------------------------------------------- imagined folks

def generic_head(c, P, skin, hair_fn=None, hair_back_fn=None, glasses=None, iris="#3a2a20", brow="#4a3020", hw=92, hh=100):
    if hair_back_fn:
        hair_back_fn(c)
    for s in (-1, 1):
        fs(c, oval(s * hw * 0.98, 8, 15, 22), skin, 4)
    fs(c, head_path(hw, hh, 0.03, P["puff"]), skin, 5)
    if hair_fn:
        hair_fn(c)
    ey = 2
    for s in (-1, 1):
        draw_eye(c, s * 37, ey, 22, 25, P, s, skin, iris=iris)
        draw_brow(c, s * 37, ey - 38 - P["brow_y"] * 12, 22, P["brow_ang"], s, brow, 8)
    if glasses:
        for s in (-1, 1):
            c.drawPath(oval(s * 37, ey, 32, 30), stroke(glasses, 5))
        c.drawPath(poly([(-6, ey), (6, ey)], False), stroke(glasses, 4))
    if P["blush"] > 0:
        for s in (-1, 1):
            c.drawPath(oval(s * 56, 42, 20, 12), fill("#ff6a6a", 0.4 * P["blush"], blur=5))
    c.drawPath(smooth_path([(-3, 22), (-12, 40), (2, 42)], False), stroke(hexs(mix(skin, "#000000", 0.35)), 3.5))
    draw_mouth(c, 0, 64, 30, P)


def therapist(c, P, t, nod=0.0):
    skin = "#e8bfa0"

    def bun(c_):
        fs(c_, oval(0, -112, 34, 26), "#b9b9c2", 4)

    def hair(c_):
        h = smooth_path([(-95, 10), (-100, -60), (-60, -105), (0, -112), (60, -105), (100, -60), (95, 10), (70, -50), (0, -70), (-70, -50)])
        fs(c_, h, "#c8c8d0", 4)

    # cardigan torso
    fs(c, smooth_path([(-140, 140), (-170, 260), (-170, 420), (170, 420), (170, 260), (140, 140), (0, 120)]), "#d9a441", 5)
    fs(c, poly([(-40, 125), (0, 230), (40, 125)]), "#f3efe6", 4)
    # clipboard
    fs(c, rrect(-120, 230, 150, 190, 10), "#9a6b3e", 5)
    fs(c, rrect(-108, 250, 126, 160, 4), "#ffffff", 3)
    for i in range(5):
        c.drawPath(poly([(-96, 275 + i * 24), (6, 275 + i * 24)], False), stroke("#9aa0b0", 3))
    fs(c, rrect(-70, 222, 50, 18, 5), "#c0c0c8", 3)
    fs(c, oval(40, 330, 26, 22), skin, 4)
    c.save()
    c.translate(0, nod * 14)
    c.rotate(nod * 4)
    generic_head(c, P, skin, hair, bun, glasses="#7a3b2e", iris="#4b6a8a", brow="#9a9aa8")
    c.restore()


def sjw(c, P, t, chart_shake=0.0, x_stamp=0.0):
    skin = "#f0c8a8"

    def hair(c_):
        h = smooth_path([(-98, 20), (-104, -70), (-50, -118), (30, -122), (100, -80), (104, 0), (80, -60), (20, -82), (-40, -70), (-80, -30)])
        fs(c_, h, "#2ec4b6", 4)
        c_.drawPath(smooth_path([(30, -122), (100, -80), (104, 0), (80, -60)]), fill("#ff5fa2"))

    fs(c, smooth_path([(-140, 140), (-170, 260), (-170, 420), (170, 420), (170, 260), (140, 140), (0, 125)]), "#7d5ba6", 5)
    generic_head(c, P, skin, hair, glasses="#222222", iris="#5a3b8a", brow="#2ec4b6")
    # pie chart sign held up
    c.save()
    c.translate(0 + chart_shake * 4 * math.sin(t * 30), 330)
    fs(c, rrect(-170, -10, 340, 230, 14), "#fffaf0", 5)
    cx, cy, r = -95, 105, 66
    segs = [(0.0, 0.45, "#e63946"), (0.45, 0.8, "#f4a261"), (0.8, 1.0, "#6d597a")]
    for a0, a1, cc in segs:
        p = skia.Path()
        p.moveTo(cx, cy)
        p.arcTo(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), -90 + a0 * 360, (a1 - a0) * 360, False)
        p.close()
        fs(c, p, cc, 3)
    labels = [("#e63946", "problematic"), ("#f4a261", "VERY problematic"), ("#6d597a", "this pie chart")]
    for i, (cc, s) in enumerate(labels):
        c.drawRect(skia.Rect.MakeXYWH(-18, 52 + i * 46, 18, 18), fill(cc))
        text(c, s, 6, 67 + i * 46, "fredoka", 17, "#222222", align="left")
    if x_stamp > 0:
        sc = 1 + 1.5 * (1 - ease_out_back(x_stamp, 2))
        c.save()
        c.translate(cx, cy)
        c.scale(sc, sc)
        c.rotate(-12)
        c.drawPath(poly([(-70, -70), (70, 70)], False), stroke("#d62828", 18, clamp(x_stamp * 3)))
        c.drawPath(poly([(70, -70), (-70, 70)], False), stroke("#d62828", 18, clamp(x_stamp * 3)))
        c.restore()
    for s in (-1, 1):
        fs(c, oval(s * 170, 60, 24, 22), skin, 4)
    c.restore()


def suburb_person(c, P, t, kind="greg", turn=0.0, sip=0.0, wave=0.0):
    """Full body, feet at y=0, ~ 300 tall (scaled by caller)."""
    skin = "#f2cdb0" if kind == "greg" else "#f5d0b8"
    # legs
    if kind == "greg":
        for s in (-1, 1):
            fs(c, rrect(s * 22 - 14, -130, 28, 95, 10), "#d8c49a", 4)
            fs(c, rrect(s * 22 - 12, -40, 24, 36, 8), skin, 4)
            fs(c, rrect(s * 22 - 18, -10, 36, 14, 6), "#ffffff", 3)
        fs(c, smooth_path([(-60, -250), (-70, -150), (-58, -125), (58, -125), (70, -150), (60, -250), (0, -262)]), "#f28b82", 4)
        fs(c, poly([(-20, -260), (0, -232), (20, -260)]), "#ffffff", 3)
    else:
        for s in (-1, 1):
            fs(c, rrect(s * 18 - 10, -70, 20, 66, 8), skin, 4)
            fs(c, rrect(s * 18 - 14, -10, 30, 12, 6), "#f6c1d0", 3)
        fs(c, smooth_path([(-45, -255), (-58, -170), (-92, -60), (92, -60), (58, -170), (45, -255), (0, -265)]), "#8ecae6", 4)
        for i in range(5):
            c.drawCircle(-60 + i * 30, -100 + (i % 2) * 30, 7, fill("#ffffff", 0.8))
    # arms
    for s in (-1, 1):
        if kind == "linda" and s > 0:
            hx, hy = lerp(55, 18, sip), lerp(-150, -300, sip)
        elif kind == "greg":
            hx, hy = s * 65 + 40, -150
        else:
            hx, hy = -70, lerp(-150, -340, wave)
        sx = s * 52 if kind == "greg" else s * 42
        hx = hx if kind != "linda" or s > 0 else hx
        hxx = hx if (kind == "linda") else hx
        c.drawPath(poly([(sx, -240), (hxx, hy)], False), stroke(OUT, 25))
        c.drawPath(poly([(sx, -240), (hxx, hy)], False), stroke(skin, 18))
        c.drawCircle(hxx, hy, 13, fill(skin))
        c.drawCircle(hxx, hy, 13, stroke(OUT, 3.5))
        if kind == "linda" and s > 0:
            fs(c, poly([(hxx - 18, hy - 40), (hxx + 18, hy - 40), (hxx + 14, hy + 10), (hxx - 14, hy + 10)]), "#ffffff", 3.5)
            c.drawRect(skia.Rect.MakeLTRB(hxx - 16, hy - 22, hxx + 16, hy - 6), fill("#a0522d"))
            fs(c, rrect(hxx - 20, hy - 48, 40, 10, 4), "#ffffff", 3)
    # head
    c.save()
    c.translate(0, -330)
    c.scale(0.62, 0.62)
    c.rotate(turn * 0.0)
    if kind == "greg":
        def hair(c_):
            fs(c_, smooth_path([(-96, -10), (-98, -72), (-40, -110), (40, -112), (98, -70), (96, -10), (60, -60), (-30, -78)]), "#e8c35a", 4)
            c_.drawPath(poly([(-30, -78), (-10, -105)], False), stroke(OUT, 3))
        generic_head(c, P, skin, hair, iris="#3b6ea5", brow="#c9a040")
    else:
        def hair(c_):
            fs(c_, smooth_path([(-100, 40), (-104, -70), (-50, -112), (40, -114), (102, -70), (100, 40), (78, -40), (0, -72), (-78, -40)]), "#8b4a2b", 4)

        def hat(c_):
            pass
        generic_head(c, P, skin, hair, iris="#5a7a3a", brow="#6b3a20")
        fs(c, oval(0, -88, 170, 28), "#f3dfa2", 4)
        fs(c, smooth_path([(-80, -90), (-70, -150), (0, -165), (70, -150), (80, -90)]), "#f3dfa2", 4)
        c.drawRect(skia.Rect.MakeLTRB(-78, -112, 78, -96), fill("#e76f51"))
    c.restore()


def lawnmower(c, x, y, t, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    fs(c, rrect(-70, -60, 140, 50, 14), "#d62828", 4)
    fs(c, rrect(-40, -80, 70, 24, 8), "#333333", 3)
    for wx in (-50, 50):
        fs(c, oval(wx, -8, 18, 18), "#222222", 3)
    c.drawPath(poly([(30, -60), (110, -170)], False), stroke(OUT, 10))
    c.drawPath(poly([(30, -60), (110, -170)], False), stroke("#9a9aa4", 6))
    for i in range(6):
        gx = -70 + i * 26 + 5 * math.sin(t * 30 + i)
        c.drawPath(poly([(gx, -10), (gx - 8, -30 - 10 * hash1(i))], False), stroke("#3a9a3a", 4))
    c.restore()


def dog(c, x, y, t, s=1.0, bark=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    gold = "#e0a040"
    wag = math.sin(t * 16) * 18
    c.save()
    c.translate(-70, -70)
    c.rotate(-40 + wag)
    fs(c, rrect(-8, -60, 16, 60, 8), gold, 4)
    c.restore()
    for lx in (-50, -25, 25, 50):
        fs(c, rrect(lx - 9, -45, 18, 45, 7), gold, 3.5)
    fs(c, oval(0, -70, 80, 40), gold, 4)
    c.save()
    c.translate(70, -110)
    fs(c, oval(0, 0, 40, 36), gold, 4)
    fs(c, oval(30, 12, 26, 16), "#f0c070", 4)
    c.drawCircle(50, 6, 7, fill(OUT))
    c.drawCircle(4, -8, 6, fill(OUT))
    c.drawCircle(2, -10, 2, fill("#ffffff"))
    if bark > 0:
        fs(c, oval(36, 30 + 6 * bark, 16, 10 * bark), "#5a1626", 3)
    fs(c, oval(-24, 6, 14, 26), "#b87828", 3.5)
    c.restore()
    c.restore()


def gremlin(c, x, y, r, t, awake=1.0, glow=0.0):
    if glow > 0:
        c.drawCircle(x, y, r * (1.8 + 0.2 * math.sin(t * 8)), rad_grad(x, y, r * 2.2, ["#ffe14d", "#ff7a00"], [0, 1], [0.8 * glow, 0.0]))
    b = blob(x, y, r, 9, 0.08 + 0.05 * awake, t * (1 + 2 * awake), 4)
    fs(c, b, "#ffd93b", 4)
    for s in (-1, 1):
        ax = x + s * r * 0.95
        c.drawPath(poly([(ax, y + r * 0.1), (ax + s * r * 0.45, y - r * 0.3 + 6 * math.sin(t * 14 + s))], False), stroke(OUT, 6))
    for s in (-1, 1):
        ex, ey = x + s * r * 0.35, y - r * 0.15
        if awake < 0.5:
            c.drawPath(smooth_path([(ex - 10, ey), (ex, ey + 6), (ex + 10, ey)], False), stroke(OUT, 4))
        else:
            c.drawPath(oval(ex, ey, r * 0.22, r * 0.28 * awake), fill("#ffffff"))
            c.drawPath(oval(ex, ey, r * 0.22, r * 0.28 * awake), stroke(OUT, 3))
            c.drawCircle(ex + 2, ey + 2, r * 0.1, fill(OUT))
    if awake < 0.5:
        text(c, "z", x + r, y - r - 10 - 10 * (t % 1), "fredoka", 30, "#ffffff", a=0.8)
    else:
        m = skia.Path()
        m.moveTo(x - r * 0.4, y + r * 0.25)
        m.quadTo(x, y + r * (0.7 + 0.15 * math.sin(t * 20)), x + r * 0.4, y + r * 0.25)
        m.close()
        fs(c, m, "#5a1626", 3.5)


def ghost(c, x, y, t, s=1.0, a=0.85):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    pts = [(-60, 20), (-62, -40), (-40, -90), (0, -104), (40, -90), (62, -40), (60, 20)]
    for i in range(7):
        xx = 60 - i * 20
        pts.append((xx, 60 + 14 * math.sin(t * 6 + i * 1.3) + (10 if i % 2 else -4)))
    g = smooth_path(pts)
    c.drawPath(g, fill("#d9dde6", a))
    c.drawPath(g, stroke("#6c7385", 4, a))
    for sx in (-22, 22):
        c.drawPath(oval(sx, -40, 10, 14), fill("#2a2f3a", a))
    c.drawCircle(22, -40, 18, stroke("#c9a227", 3, a))
    c.drawPath(poly([(40, -40), (46, 10)], False), stroke("#c9a227", 2, a))
    c.drawPath(poly([(-38, -66), (-10, -58)], False), stroke("#2a2f3a", 5, a))
    c.drawPath(poly([(38, -66), (10, -58)], False), stroke("#2a2f3a", 5, a))
    c.drawPath(smooth_path([(-14, -6), (0, -12), (14, -6)], False), stroke("#2a2f3a", 4, a))
    # tiny fedora
    fs(c, oval(0, -100, 52, 9), "#3a3842", 3, a=a)
    fs(c, smooth_path([(-30, -100), (-30, -130), (0, -124), (30, -130), (30, -100)]), "#3a3842", 3, a=a)
    # sign
    c.drawPath(poly([(70, 40), (70, -60)], False), stroke("#7b5a3a", 6, a))
    fs(c, rrect(60, -150, 170, 90, 8), "#fffaf0", 4, a=a)
    text(c, "WELL,", 145, -114, "bangers", 34, "#333333", a=a)
    text(c, "ACTUALLY", 145, -76, "bangers", 34, "#333333", a=a)
    c.restore()


# ---------------------------------------------------------------------- v2 additions

def lord_lying(c, t, flag=1.0):
    """Imagined: the Lord flat on the floor, a white flag planted on top of him. Floor at y=0."""
    kh = "#d2bd8f"
    fs(c, rrect(90, -62, 210, 30, 14), kh, 4)
    fs(c, rrect(90, -32, 210, 30, 14), kh, 4)
    for yy in (-62, -32):
        fs(c, rrect(292, yy - 8, 46, 40, 14), "#f2f2f2", 4)
    torso = rrect(-110, -78, 220, 78, 34)
    fs(c, torso, SHIRT_LORD, 5)
    for s in (-1, 1):
        c.drawPath(poly([(-60, -6), (-20, 4 + 2 * s)], False), stroke(OUT, 26))
        c.drawPath(poly([(-60, -6), (-20, 4 + 2 * s)], False), stroke(SKIN_LORD, 19))
    P = P_(t=t, lid=0.0, smile=-0.6, tears=0.9, brow_ang=1.0, brow_y=0.3)
    c.save()
    c.translate(-175, -48)
    c.rotate(-80)
    c.scale(0.55, 0.55)
    lord_head(c, P, fedora=False)
    c.restore()
    fs(c, oval(-260, -6, 70, 12), "#2f2d36", 3)
    if flag > 0:
        h = 230 * flag
        c.drawPath(poly([(10, -60), (10, -60 - h)], False), stroke("#7b5a3a", 7))
        wv = math.sin(t * 7)
        fl = smooth_path([(10, -60 - h), (70, -66 - h + wv * 8), (130, -58 - h - wv * 6), (130, -2 - h - wv * 6), (70, -8 - h + wv * 8), (10, -60 - h + 58)])
        fs(c, fl, "#ffffff", 4)


def astronaut(c, t, P, wave=0.0, jet=0.0):
    """The Lord in a spacesuit, full body, centre of torso at (0,0)."""
    suit, trim = "#f2f2f7", "#c9cbd6"
    # jetpack
    fs(c, rrect(-95, -60, 190, 170, 30), "#9aa0b0", 5)
    # legs
    for s in (-1, 1):
        fs(c, rrect(s * 48 - 34, 90, 68, 150, 28), suit, 5)
        fs(c, rrect(s * 48 - 40, 222, 80, 46, 18), "#6b7280", 5)
        c.drawPath(poly([(s * 48 - 32, 170), (s * 48 + 32, 170)], False), stroke(trim, 6))
    # torso
    fs(c, rrect(-110, -70, 220, 190, 60), suit, 6)
    fs(c, rrect(-55, -10, 110, 70, 12), "#e5e7ef", 4)
    for i, cc in enumerate(("#ff4d4d", "#3dff6e", "#4cc9ff")):
        c.drawCircle(-30 + i * 30, 25, 9, fill(cc))
    # arms
    for s in (-1, 1):
        if s > 0 and wave > 0:
            ang = -2.2 + 0.35 * math.sin(t * 10) * wave
            ex, ey = 150, -40
            hx, hy = ex + math.cos(ang) * 95, ey + math.sin(ang) * 95
        else:
            ex, ey = s * 150, 30
            hx, hy = s * 175, 110
        for (a_, b_) in (((s * 100, -40), (ex, ey)), ((ex, ey), (hx, hy))):
            c.drawPath(poly([a_, b_], False), stroke(OUT, 62))
            c.drawPath(poly([a_, b_], False), stroke(suit, 52))
        c.drawCircle(hx, hy, 30, fill("#6b7280"))
        c.drawCircle(hx, hy, 30, stroke(OUT, 5))
    # helmet + head
    c.save()
    c.translate(0, -175)
    c.drawCircle(0, 0, 150, fill("#bfe6ff", 0.25))
    c.save()
    c.scale(0.95, 0.95)
    lord_head(c, P, fedora=False)
    c.restore()
    c.drawCircle(0, 0, 150, stroke("#ffffff", 10))
    c.drawCircle(0, 0, 150, stroke(OUT, 4))
    c.drawPath(smooth_path([(-95, -80), (-60, -115), (-10, -128)], False), stroke("#ffffff", 12, 0.7))
    fs(c, rrect(-80, 120, 160, 40, 18), trim, 5)
    c.restore()
    # fart jet
    if jet > 0:
        for i in range(7):
            ph = (t * 2.2 + i / 7) % 1.0
            x = -120 - 260 * ph
            y = 120 + 40 * math.sin(i * 1.7 + t * 4) * ph
            r = 22 + 55 * ph
            p = blob(x, y, r, 8, 0.15, t, i)
            c.drawPath(p, fill("#9ccf55", 0.75 * jet * (1 - ph)))
            c.drawPath(p, stroke("#4e6d2a", 3.5, 0.8 * jet * (1 - ph)))
