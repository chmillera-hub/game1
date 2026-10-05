"""The cast of DO NOT DISTURB, drawn in the riso-noir style. Feet at (0, 0), +y down."""
import math
import random
import cairo
from toon.draw import (OUT, LW, TAU, hexc, shade, src, ell, rrect, fs, fill, poly, line, hose, text, star, heart)
from toon import face
from toon.characters import ARMS, arms_paths, legs_paths
from .style import (PAPER, INK, LAV, LAV_D, HOOD, PINK, RED, COAT, MUST, MUST_D, TEAL, TEAL_L, INDIGO, NIGHT,
                    CORAL, MINT, SLATE, ALARM, CREAM2, shade_fill, mix, halftone)

ARMS.update({
    "behind": (-0.05, 0.6, -0.05, 0.6),
    "wring": (-0.75, 0.25, -0.75, 0.25),
    "peek": (-0.2, -0.66, -0.2, -0.66),
    "crawl": (0.25, 1.15, 0.25, 1.15),
    "tug": (-0.55, 1.0, 0.65, 1.15),
    "facepalm": (0.15, 0.97, -0.55, -0.95),
    "salute": (0.15, 0.97, -0.2, -1.05),
    "typing": (-0.35, 0.45, -0.35, 0.45),
    "catch": (-0.55, -0.15, -0.55, -0.15),
    "hold2": (-0.45, 0.3, -0.45, 0.3),
    "guns": (0.8, 0.1, 0.8, 0.1),
    "lean": (0.15, 0.97, 0.9, 0.45),
    "phone_ear": (0.15, 0.97, -0.25, -0.95),
    "reachup": (0.15, 0.97, 0.5, -1.15),
    "coffee": (0.15, 0.97, -0.3, 0.2),
})


def sh_body(c, path, alpha=0.32):
    """Halftone shadow on the right third of a shape (path is reused via copy_path)."""
    c.save()
    c.append_path(path)
    c.clip()
    ext = c.clip_extents()
    x0, y0, x1, y1 = ext
    c.rectangle(x0 + (x1 - x0) * 0.62, y0, (x1 - x0), y1 - y0)
    shade_fill(c, alpha)
    c.restore()


# ------------------------------------------------------------------------------------------- props
def cage(c, x, y, S, scale=1.0, inside=True):
    t = S.get("_t", 0)
    c.save(); c.translate(x, y); c.scale(scale, scale)
    w, h = 130, 120
    # floor
    rrect(c, -w / 2 - 8, h / 2 - 10, w + 16, 22, 6); fs(c, SLATE)
    if inside and S.get("cage_full", 1):
        jit = math.sin(t * 30) * 3 * S.get("rattle", 0)
        thing_body(c, jit, 25, 0.75, t, S.get("rattle", 0))
    # bars
    c.move_to(-w / 2, h / 2)
    c.line_to(-w / 2, -h / 4)
    c.curve_to(-w / 2, -h * 0.85, w / 2, -h * 0.85, w / 2, -h / 4)
    c.line_to(w / 2, h / 2)
    src(c, INK); c.set_line_width(7); c.stroke()
    for i in range(1, 6):
        bx = -w / 2 + w * i / 6
        top = -h / 4 - math.sin(math.pi * i / 6) * h * 0.42
        line(c, bx, h / 2, bx, top, INK, 4)
    # handle
    ell(c, 0, -h * 0.7, 18, 12, math.pi, TAU); src(c, INK); c.set_line_width(6); c.stroke()
    # door (front, swings open)
    op = S.get("cage_open", 0)
    c.save(); c.translate(w / 2 - 6, 0)
    c.scale(max(0.08, 1 - op * 0.92), 1)
    rrect(c, -w * 0.62, -h * 0.25, w * 0.55, h * 0.7, 6)
    src(c, INK); c.set_line_width(5); c.stroke()
    for i in range(1, 4):
        line(c, -w * 0.62 + w * 0.55 * i / 4, -h * 0.25, -w * 0.62 + w * 0.55 * i / 4, h * 0.45, INK, 3)
    c.restore()
    c.restore()


def thing_body(c, x, y, k, t, writhe=0.0, eyes=True, bite=0.0):
    """The little escaped critter: a fuzzy ink blot with skittering legs and glowing eyes."""
    c.save(); c.translate(x, y); c.scale(k, k)
    # legs
    for i in range(6):
        side = -1 if i < 3 else 1
        j = i % 3
        ph = t * 22 + i * 1.7
        lx = side * (28 + j * 10)
        ly = 10
        fx = side * (55 + j * 12) + math.sin(ph) * 8
        fy = 34 + math.cos(ph) * 6
        c.move_to(lx, ly); c.curve_to(lx + side * 18, ly - 18, fx, fy - 20, fx, fy)
        src(c, INK); c.set_line_width(5); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    # fuzzy body
    n = 28
    rnd = random.Random(int(t * 15))
    for i in range(n + 1):
        a = TAU * i / n
        r = 1 + 0.16 * math.sin(a * 5 + t * 8) + rnd.uniform(0, 0.12 + 0.2 * writhe)
        px, py = math.cos(a) * 48 * r, math.sin(a) * 34 * r
        (c.move_to if i == 0 else c.line_to)(px, py)
    c.close_path()
    src(c, NIGHT); c.fill_preserve(); src(c, INK); c.set_line_width(3); c.stroke()
    if eyes:
        for s in (-1, 1):
            g = cairo.RadialGradient(s * 16, -6, 0, s * 16, -6, 26)
            g.add_color_stop_rgba(0, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0.7)
            g.add_color_stop_rgba(1, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0)
            c.set_source(g); c.arc(s * 16, -6, 26, 0, TAU); c.fill()
            ell(c, s * 16, -6, 9, 11); fill(c, TEAL_L)
            ell(c, s * 16, -6, 3, 6); fill(c, NIGHT)
    if bite > 0:
        c.move_to(-22, 14)
        for i in range(7):
            c.line_to(-22 + i * 7.3, 14 + (10 if i % 2 else 0) * bite)
        src(c, PAPER); c.set_line_width(3); c.stroke()
    c.restore()


def prop(c, kind, x, y, S):
    t = S.get("_t", 0)
    if kind == "controller":
        c.save(); c.translate(x, y - 6)
        rrect(c, -48, -20, 96, 40, 18); fs(c, SLATE)
        ell(c, -42, 10, 18, 20); fs(c, SLATE)
        ell(c, 42, 10, 18, 20); fs(c, SLATE)
        line(c, -28, -4, -16, -4, PAPER, 5); line(c, -22, -10, -22, 2, PAPER, 5)
        for dx, dy, col in ((22, -8, CORAL), (32, 0, TEAL), (12, 0, MUST)):
            ell(c, dx, dy, 5, 5); fill(c, col)
        c.restore()
    elif kind == "cage":
        cage(c, x, y - 60, S, 0.9)
    elif kind == "rock":
        c.save(); c.translate(x, y - 10)
        poly(c, [(-30, 10), (-24, -18), (4, -26), (28, -10), (26, 16), (-6, 22)]); fs(c, SLATE)
        poly(c, [(4, -26), (28, -10), (26, 16)]); shade_fill(c, 0.4)
        c.restore()
    elif kind == "sweater":
        c.save(); c.translate(x, y - 20)
        ell(c, 0, 0, 70, 46); fs(c, CORAL)
        for k in range(-2, 3):
            line(c, -60, k * 14, 60, k * 14, shade(CORAL, 0.75), 4)
        c.restore()
    elif kind == "recorder":
        c.save(); c.translate(x, y - 10); c.rotate(0.2)
        rrect(c, -16, -30, 32, 60, 6); fs(c, NIGHT)
        blink = 1 if (t * 2) % 1 < 0.6 else 0.3
        ell(c, 0, -18, 6, 6); fill(c, ALARM if blink > 0.5 else shade(ALARM, 0.5))
        for k in range(3):
            line(c, -8, 0 + k * 8, 8, 0 + k * 8, SLATE, 2)
        c.restore()
    elif kind == "clipboard":
        c.save(); c.translate(x, y - 30); c.rotate(-0.1)
        rrect(c, -40, -55, 80, 110, 6); fs(c, hexc("#b58a5a"))
        c.rectangle(-32, -42, 64, 90); fill(c, PAPER)
        for k in range(5):
            line(c, -24, -30 + k * 16, 24, -30 + k * 16, SLATE, 2)
        rrect(c, -16, -62, 32, 14, 4); fs(c, SLATE, lw=3)
        c.restore()
    elif kind == "plate":
        c.save(); c.translate(x, y - 12)
        ell(c, 0, 0, 46, 14); fs(c, PAPER)
        ell(c, 0, -2, 28, 8); src(c, SLATE); c.set_line_width(2); c.stroke()
        c.restore()
    elif kind == "coffee":
        c.save(); c.translate(x, y - 20)
        rrect(c, -18, -24, 36, 44, 6); fs(c, PAPER)
        rrect(c, -18, -10, 36, 12, 0); fill(c, TEAL)
        c.restore()
    elif kind == "snacks":
        c.save(); c.translate(x, y - 30); c.rotate(0.15)
        poly(c, [(-34, -46), (34, -46), (30, 46), (-30, 46)]); fs(c, MUST)
        text(c, "CHIPS", 0, 6, 20, "Bungee", INK)
        c.restore()
    elif kind == "laptop":
        c.save(); c.translate(x, y - 10)
        poly(c, [(-60, 0), (60, 0), (70, 14), (-70, 14)]); fs(c, SLATE)
        c.restore()
    elif kind == "badge":
        c.save(); c.translate(x, y - 20)
        rrect(c, -26, -34, 52, 68, 6); fs(c, PAPER)
        c.rectangle(-16, -24, 32, 24); fill(c, TEAL)
        c.restore()


# ------------------------------------------------------------------------------------------- people
def person(c, S, cfg):
    t = S.get("_t", 0.0)
    skin = cfg["skin"]
    if cfg.get("mort") is not None:
        skin = mix(skin, cfg["mort"], max(0.0, min(1.0, S.mortified or 0)))
    leg = cfg["leg"]
    hip_y = -leg
    bw, bh = cfg["bw"], cfg["bh"]
    top = hip_y - bh + 24
    hrx, hry = cfg["hrx"], cfg["hry"]
    hy = top - hry * 0.72 - 2 * S.talk
    # legs
    pants, shoe = cfg["pants"], cfg["shoe"]
    if S.sit:
        for sd in (-1, 1):
            hose(c, [[(sd * bw * 0.25, hip_y), (sd * bw * 0.32, hip_y + 20), (sd * bw * 0.36, hip_y + 75)]],
                 cfg["legw"], pants)
            ell(c, sd * bw * 0.4, hip_y + 86, 30, 14); fs(c, shoe)
    elif S.tiptoe:
        for sd in (-1, 1):
            ph = t * 7 + (0 if sd < 0 else math.pi)
            lift = max(0, math.sin(ph))
            hx = sd * bw * 0.22
            kx, ky = hx + sd * 10 + lift * 26 * sd, hip_y + leg * 0.5 - lift * 40
            fx, fy = hx + sd * 6, -4 - lift * 36
            hose(c, [[(hx, hip_y), (kx, ky), (fx, fy)]], cfg["legw"], pants)
            c.save(); c.translate(fx + sd * 6, fy + 6); c.rotate(sd * -0.5)
            ell(c, 0, 0, 22, 11); fs(c, shoe); c.restore()
    else:
        legs = legs_paths(S, bw * 0.22, hip_y, leg - 22, spread=2)
        hose(c, [[(hx, hy_), (fx, fy)] for (hx, hy_), (fx, fy) in legs], cfg["legw"], pants)
        for i, ((hx, hy_), (fx, fy)) in enumerate(legs):
            tap = 0.0
            if S.tap and i == 1:
                tap = abs(math.sin(t * 9)) * 14
            c.save(); c.translate(fx + (8 if fx > 0 else -8), fy + 12)
            if tap:
                c.rotate(-0.3 * tap / 14)
            ell(c, 0, 0, cfg.get("shoe_rx", 30), 14); fs(c, shoe)
            c.restore()
    # arms behind the body (hands clasped behind)
    sh_x, sh_y = bw * 0.42, top + 44
    L = cfg["arm"]
    l, r = arms_paths(S, sh_x, sh_y, L, bend=0.2)
    behind = S.behind
    if behind:
        hose(c, [list(l), list(r)], cfg["armw"], cfg["sleeve"])
    if cfg.get("back"):
        cfg["back"](c, S, dict(top=top, hy=hy, hrx=hrx, hry=hry, bw=bw, bh=bh, hip_y=hip_y))
    # body
    rrect(c, -bw / 2, top, bw, bh, bw * 0.42)
    body = c.copy_path()
    fs(c, cfg["outfit"])
    sh_body(c, body)
    if cfg.get("front"):
        cfg["front"](c, S, dict(top=top, hy=hy, hrx=hrx, hry=hry, bw=bw, bh=bh, hip_y=hip_y, skin=skin))
    # head
    if cfg.get("square"):
        rrect(c, -hrx, hy - hry, hrx * 2, hry * 2, hrx * 0.45)
    else:
        ell(c, 0, hy, hrx, hry)
    head = c.copy_path()
    fs(c, skin)
    sh_body(c, head, 0.25)
    if cfg.get("hair"):
        cfg["hair"](c, S, hy, hrx, hry)
    ex, ey = hrx * 0.38, hy + hry * cfg.get("eye_dy", 0.0)
    erx, ery = cfg.get("erx", 16), cfg.get("ery", 19)
    if S.glow:
        for sd in (-1, 1):
            g = cairo.RadialGradient(sd * ex, ey, 0, sd * ex, ey, 60)
            g.add_color_stop_rgba(0, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0.8 * S.glow)
            g.add_color_stop_rgba(1, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0)
            c.set_source(g); c.arc(sd * ex, ey, 60, 0, TAU); c.fill()
    if not cfg.get("hide_eyes"):
        for sd in (-1, 1):
            face.eye(c, sd * ex, ey, erx, ery, S, sd, skin, iris=cfg.get("iris", TEAL))
        if cfg.get("bags"):
            for sd in (-1, 1):
                for k, a in ((0, 0.9), (1, 0.5)):
                    c.move_to(sd * ex - erx * 0.9, ey + ery * (1.15 + k * 0.35))
                    c.curve_to(sd * ex - erx * 0.3, ey + ery * (1.55 + k * 0.35), sd * ex + erx * 0.3,
                               ey + ery * (1.55 + k * 0.35), sd * ex + erx * 0.9, ey + ery * (1.15 + k * 0.35))
                    src(c, LAV_D, a); c.set_line_width(3.5); c.stroke()
        face.brows(c, 0, ey - ery * 1.55, ex, erx * 1.9, S, col=INK, thick=5)
    if S.blush or cfg.get("blushy"):
        a = max(S.blush or 0, cfg.get("blushy", 0))
        for sd in (-1, 1):
            ell(c, sd * hrx * 0.6, ey + ery * 1.5, 18, 10); src(c, RED, 0.5 * a); c.fill()
    face.mouth(c, 0, hy + hry * cfg.get("mouth_dy", 0.5), hrx * 0.5, S)
    if cfg.get("acc"):
        cfg["acc"](c, S, dict(hy=hy, hrx=hrx, hry=hry, ex=ex, ey=ey, erx=erx, ery=ery, top=top, bw=bw))
    if S.sweat:
        face.sweat(c, hrx * 0.95, hy - hry * 0.5, S.sweat, t, 12)
    if S.tears:
        face.tears(c, -ex, ey + ery, S.tears, t)
        face.tears(c, ex, ey + ery, S.tears, t + 0.4)
    if S.dazed:
        for k in range(3):
            a = t * 5 + k * TAU / 3
            star(c, math.cos(a) * hrx * 1.1, hy - hry * 1.05 + math.sin(a) * 14, 16, 6, 5)
            fs(c, MUST, lw=3)
    if S.bruise:
        c.save(); c.translate(-hrx * 0.55, hy + hry * 0.25); c.rotate(-0.5)
        rrect(c, -18, -7, 36, 14, 5); fs(c, CREAM2, lw=3); c.restore()
    # arms
    if not behind:
        hose(c, [list(l), list(r)], cfg["armw"], cfg["sleeve"])
    if cfg.get("cuffs"):
        for (p0, el, h) in (l, r):
            wx, wy = el[0] + (h[0] - el[0]) * 0.8, el[1] + (h[1] - el[1]) * 0.8
            ell(c, wx, wy, cfg["armw"] * 0.55, cfg["armw"] * 0.5); fs(c, cfg["cuffs"], lw=3)
    if S.bandage and not behind:
        p0, el, h = r
        wx, wy = el[0] + (h[0] - el[0]) * 0.55, el[1] + (h[1] - el[1]) * 0.55
        ell(c, wx, wy, cfg["armw"] * 0.6, cfg["armw"] * 0.55); fs(c, PAPER, lw=3)
        line(c, wx - 8, wy - 6, wx + 8, wy + 6, CREAM2, 2)
    if not behind:
        rh = r[2]
        lh = l[2]
        if S.roll:
            a = t * 12
            rh = (rh[0] + math.cos(a) * 16, rh[1] + math.sin(a) * 16)
        for hpt in (lh, rh):
            ell(c, hpt[0], hpt[1], cfg["armw"] * 0.62, cfg["armw"] * 0.58); fs(c, skin)
        if S.hold:
            prop(c, S.hold, rh[0], rh[1], S)
    if cfg.get("over"):
        cfg["over"](c, S, dict(hy=hy, hrx=hrx, hry=hry, ex=ex, ey=ey))


# -- Tiredness ---------------------------------------------------------------------------------
def _tired_hair(c, S, hy, hrx, hry):
    pts = []
    for i in range(13):
        a = math.pi * 1.08 + math.pi * 0.84 * i / 12
        r = 1.12 if i % 2 else 0.86
        pts.append((math.cos(a) * hrx * r * 0.95, hy - hry * 0.5 + math.sin(a) * hry * r * 0.62))
    poly(c, pts)
    fs(c, INDIGO)
    c.move_to(-hrx * 0.1, hy - hry * 1.05)
    c.curve_to(hrx * 0.2, hy - hry * 1.5, hrx * 0.5, hy - hry * 1.3, hrx * 0.45, hy - hry * 1.05)
    src(c, INK); c.set_line_width(6); c.stroke()


def _tired_back(c, S, g):
    # hood behind the head
    ell(c, 0, g["top"] + 6, g["bw"] * 0.42, 46)
    fs(c, shade(HOOD, 0.85))


def _tired_front(c, S, g):
    top, bw, bh = g["top"], g["bw"], g["bh"]
    # pocket
    rrect(c, -bw * 0.3, top + bh * 0.55, bw * 0.6, bh * 0.28, 16)
    src(c, INK); c.set_line_width(3.5); c.stroke()
    # drawstrings
    for sd in (-1, 1):
        line(c, sd * 16, top + 14, sd * 20, top + 80, PAPER, 5)
        ell(c, sd * 20, top + 84, 5, 7); fs(c, PAPER, lw=2)
    phones = S.phones if S.phones is not None else 0
    if phones < 0.5:
        # headphones around the neck
        c.move_to(-g["hrx"] * 0.9, top + 10)
        c.curve_to(-g["hrx"] * 0.6, top + 52, g["hrx"] * 0.6, top + 52, g["hrx"] * 0.9, top + 10)
        src(c, INK); c.set_line_width(12); c.stroke()
        for sd in (-1, 1):
            rrect(c, sd * g["hrx"] * 0.9 - 20, top + 4, 40, 50, 14); fs(c, TEAL)


def _tired_acc(c, S, g):
    phones = S.phones if S.phones is not None else 0
    hy, hrx, hry = g["hy"], g["hrx"], g["hry"]
    if phones >= 0.5:
        lift = 1.0 if phones < 0.99 and phones > 0.51 else 0.0
        c.move_to(-hrx * 1.02, hy)
        c.curve_to(-hrx * 1.1, hy - hry * 1.5, hrx * 1.1, hy - hry * 1.5, hrx * 1.02, hy)
        src(c, INK); c.set_line_width(12); c.stroke()
        rrect(c, hrx * 0.88, hy - 30, 36, 64, 14); fs(c, TEAL)
        if lift:
            rrect(c, -hrx * 0.88 - 36 - 22, hy - 72, 36, 64, 14); fs(c, TEAL)
        else:
            rrect(c, -hrx * 0.88 - 36, hy - 30, 36, 64, 14); fs(c, TEAL)
        if S.music:
            for k in range(2):
                a = (t := S.get("_t", 0)) * 2 + k
                yy = hy - hry - 20 - ((t * 40 + k * 50) % 90)
                text(c, "♪", hrx * 1.2 + k * 20, yy, 40, "DejaVu Sans", INK, alpha=0.8)


TIRED = dict(skin=LAV, outfit=HOOD, pants=hexc("#4d4f6e"), shoe=hexc("#e8d9c0"), shoe_rx=36, leg=120, legw=40,
             bw=200, bh=230, hrx=96, hry=88, arm=150, armw=38, sleeve=HOOD, hair=_tired_hair, bags=True,
             back=_tired_back, front=_tired_front, acc=_tired_acc, erx=17, ery=19, eye_dy=0.02, mouth_dy=0.55,
             iris=hexc("#6a5aa8"), cuffs=shade(HOOD, 0.8))


# -- Embarrassment -----------------------------------------------------------------------------
def _emb_hair(c, S, hy, hrx, hry):
    c.move_to(-hrx * 0.5, hy - hry * 0.88)
    c.curve_to(-hrx * 0.2, hy - hry * 1.5, hrx * 0.6, hy - hry * 1.45, hrx * 0.35, hy - hry * 0.95)
    c.curve_to(hrx * 0.2, hy - hry * 1.2, -hrx * 0.1, hy - hry * 1.2, -hrx * 0.5, hy - hry * 0.88)
    c.close_path()
    fs(c, hexc("#8c1838"))


def _emb_front(c, S, g):
    top, bw, bh = g["top"], g["bw"], g["bh"]
    # teal shirt strip between coat panels
    c.rectangle(-bw * 0.16, top + 6, bw * 0.32, bh - 30); fill(c, TEAL)
    # lab coat panels (longer than the body)
    for sd in (-1, 1):
        poly(c, [(sd * bw * 0.14, top + 8), (sd * bw * 0.52, top + 30), (sd * bw * 0.58, top + bh + 50),
                 (sd * bw * 0.1, top + bh + 50)])
        fs(c, COAT)
        poly(c, [(sd * bw * 0.14, top + 8), (sd * bw * 0.34, top + 26), (sd * bw * 0.18, top + 96)])
        fs(c, shade(COAT, 0.9), lw=3)
    # pocket with pens
    rrect(c, bw * 0.2, top + 70, bw * 0.24, 40, 4); src(c, INK); c.set_line_width(3); c.stroke()
    for k, col in enumerate((CORAL, TEAL)):
        line(c, bw * 0.26 + k * 12, top + 58, bw * 0.26 + k * 12, top + 76, col, 5)
    # lanyard + badge
    line(c, -bw * 0.12, top + 4, -bw * 0.2, top + 96, CORAL, 4)
    line(c, bw * 0.02, top + 4, -bw * 0.12, top + 96, CORAL, 4)
    rrect(c, -bw * 0.3, top + 94, 50, 62, 5); fs(c, PAPER, lw=3)
    c.rectangle(-bw * 0.3 + 8, top + 102, 34, 22); fill(c, TEAL)
    text(c, "CALM", -bw * 0.3 + 25, top + 146, 12, "Bungee", INK)


def _emb_acc(c, S, g):
    ex, ey, erx, ery = g["ex"], g["ey"], g["erx"], g["ery"]
    for sd in (-1, 1):
        ell(c, sd * ex, ey, erx * 1.45, ery * 1.3)
        src(c, INK); c.set_line_width(4.5); c.stroke()
    line(c, -ex + erx * 1.45, ey, ex - erx * 1.45, ey, INK, 4)


def _emb_over(c, S, g):
    if S.peek:
        ex, ey = g["ex"], g["ey"]
        col = mix(PINK, RED, S.mortified or 0)
        for sd in (-1, 1):
            rrect(c, sd * ex - 34, ey - 36, 68, 72, 26); fs(c, col)
            for k in range(1, 3):
                line(c, sd * ex - 34 + k * 22, ey - 30, sd * ex - 34 + k * 22, ey + 30, shade(col, 0.7), 2)
        if S.peek > 0.5:
            # fingers parted over one eye
            rrect(c, -ex - 14, ey - 9, 28, 18, 8); fill(c, PAPER)
            ell(c, -ex + (S.look or 0) * 6, ey, 6, 7); fill(c, INK)


EMB = dict(skin=PINK, mort=RED, outfit=TEAL, pants=hexc("#34345e"), shoe=PAPER, leg=190, legw=26, bw=150, bh=220,
           hrx=74, hry=86, arm=170, armw=26, sleeve=COAT, hair=_emb_hair, front=_emb_front, acc=_emb_acc,
           erx=17, ery=20, eye_dy=-0.05, mouth_dy=0.52, blushy=0.5, over=_emb_over)


# -- Boss, aide, guards, receptionist, scientists, agents ---------------------------------------
def _boss_hair(c, S, hy, hrx, hry):
    rrect(c, -hrx * 1.02, hy - hry * 1.08, hrx * 2.04, hry * 0.55, 18); fs(c, INK)
    c.move_to(-hrx * 0.6, hy - hry * 0.95); c.curve_to(-hrx * 0.1, hy - hry * 1.05, hrx * 0.3, hy - hry * 1.0,
                                                        hrx * 0.8, hy - hry * 0.75)
    src(c, SLATE); c.set_line_width(3); c.stroke()


def _suit_front(c, S, g, tie=TEAL, shirt=PAPER):
    top, bw, bh = g["top"], g["bw"], g["bh"]
    poly(c, [(-bw * 0.2, top + 4), (bw * 0.2, top + 4), (0, top + 110)]); fill(c, shirt)
    poly(c, [(-8, top + 14), (8, top + 14), (12, top + 100), (0, top + 116), (-12, top + 100)]); fs(c, tie, lw=3)
    for sd in (-1, 1):
        poly(c, [(sd * bw * 0.2, top + 4), (sd * bw * 0.36, top + 30), (sd * 6, top + 120)])
        fs(c, shade(hexc("#2b2b3a"), 1.25), lw=3)
    ell(c, bw * 0.28, top + 60, 9, 9); fs(c, TEAL, lw=2)


def _boss_acc(c, S, g):
    ex, ey, erx, ery = g["ex"], g["ey"], g["erx"], g["ery"]
    if not S.noglasses:
        for sd in (-1, 1):
            rrect(c, sd * ex - erx * 1.5, ey - ery * 1.0, erx * 3.0, ery * 1.9, 5)
            fs(c, PAPER, lw=4.5)
            k = (S.get("_t", 0) * 0.7) % 3
            poly(c, [(sd * ex - erx * 0.8 + k * 6, ey - ery * 0.8), (sd * ex - erx * 0.3 + k * 6, ey - ery * 0.8),
                     (sd * ex - erx * 0.9 + k * 6, ey + ery * 0.7), (sd * ex - erx * 1.3 + k * 6, ey + ery * 0.7)])
            src(c, MINT, 0.7); c.fill()
        line(c, -ex + erx * 1.5, ey - 4, ex - erx * 1.5, ey - 4, INK, 4)


BOSS = dict(skin=hexc("#a3abbf"), outfit=hexc("#2b2b3a"), pants=hexc("#2b2b3a"), shoe=INK, leg=230, legw=34, bw=190,
            bh=270, hrx=70, hry=88, arm=190, armw=32, sleeve=hexc("#2b2b3a"), hair=_boss_hair, square=True,
            front=_suit_front, acc=_boss_acc, hide_eyes=True, mouth_dy=0.55)


def _aide_hair(c, S, hy, hrx, hry):
    ell(c, 0, hy - hry * 0.5, hrx * 1.02, hry * 0.6, math.pi, TAU); c.close_path(); fs(c, hexc("#5a3a2a"))
    ell(c, 0, hy - hry * 1.1, 24, 20); fs(c, hexc("#5a3a2a"))


AIDE = dict(skin=hexc("#e8c4a0"), outfit=CREAM2, pants=SLATE, shoe=INK, leg=200, legw=28, bw=160, bh=230, hrx=66,
            hry=76, arm=160, armw=28, sleeve=CREAM2, hair=_aide_hair, iris=SLATE)


def _guard_hair(c, S, hy, hrx, hry):
    ell(c, 0, hy - hry * 0.55, hrx * 1.05, hry * 0.6, math.pi, TAU); c.close_path(); fs(c, hexc("#2e3a66"))
    rrect(c, -hrx * 1.1, hy - hry * 0.62, hrx * 2.5, 18, 8); fs(c, hexc("#1f2849"))
    ell(c, 0, hy - hry * 0.9, 12, 12); fs(c, MUST, lw=3)


def _guard_front(c, S, g):
    top, bw, bh = g["top"], g["bw"], g["bh"]
    c.rectangle(-bw * 0.5, top + bh - 60, bw, 20); fs(c, INK, lw=0)
    star(c, -bw * 0.25, top + 60, 16, 7, 5); fs(c, MUST, lw=3)
    for sd in (-1, 1):
        rrect(c, sd * bw * 0.2 - 18, top + 40, 36, 30, 4); src(c, INK); c.set_line_width(3); c.stroke()


def _guard_acc(c, S, g):
    hy, hrx, hry = g["hy"], g["hrx"], g["hry"]
    my = hy + hry * 0.32
    for sd in (-1, 1):
        c.move_to(0, my); c.curve_to(sd * 20, my - 10, sd * 40, my, sd * 46, my + 14)
        c.curve_to(sd * 30, my + 6, sd * 14, my + 8, 0, my + 6); c.close_path(); fs(c, hexc("#3a2a20"), lw=2)


GUARD = dict(skin=hexc("#d8a07a"), outfit=hexc("#2e3a66"), pants=hexc("#1f2849"), shoe=INK, leg=210, legw=36,
             bw=210, bh=250, hrx=72, hry=78, arm=170, armw=36, sleeve=hexc("#2e3a66"), hair=_guard_hair,
             front=_guard_front, acc=_guard_acc, iris=SLATE)
GUARD2 = dict(GUARD, skin=hexc("#8a5a3e"))


def _rec_hair(c, S, hy, hrx, hry):
    ell(c, 0, hy - hry * 0.2, hrx * 1.15, hry * 1.05, math.pi * 0.95, TAU * 1.025); c.close_path(); fs(c, hexc("#2a1a3a"))
    for sd in (-1, 1):
        rrect(c, sd * hrx * 1.0 - 16, hy - hry * 0.3, 32, hry * 1.1, 14); fs(c, hexc("#2a1a3a"))


RECEPT = dict(skin=hexc("#c48a68"), outfit=TEAL, pants=SLATE, shoe=INK, leg=190, legw=28, bw=170, bh=220, hrx=66,
              hry=74, arm=150, armw=28, sleeve=TEAL, hair=_rec_hair, iris=hexc("#4a3020"))


def _sci_acc(c, S, g):
    hy, hrx, hry = g["hy"], g["hrx"], g["hry"]
    line(c, -hrx, hy - hry * 0.55, hrx, hry * 0 + hy - hry * 0.55, INK, 6)
    for sd in (-1, 1):
        ell(c, sd * hrx * 0.38, hy - hry * 0.6, 20, 16); fs(c, MINT, lw=4)


def _sci_hair(c, S, hy, hrx, hry):
    ell(c, 0, hy - hry * 0.45, hrx * 1.02, hry * 0.62, math.pi, TAU); c.close_path(); fs(c, hexc("#c9c2b0"))


SCI = dict(skin=hexc("#f0c8a8"), outfit=COAT, pants=SLATE, shoe=INK, leg=200, legw=28, bw=170, bh=240, hrx=66,
           hry=76, arm=160, armw=28, sleeve=COAT, hair=_sci_hair, acc=_sci_acc, iris=SLATE)


def _agent_acc(c, S, g):
    ex, ey, erx, ery = g["ex"], g["ey"], g["erx"], g["ery"]
    poly(c, [(-ex - erx * 1.5, ey - ery), (ex + erx * 1.5, ey - ery), (ex + erx * 1.3, ey + ery * 0.9),
             (erx * 0.3, ey + ery * 0.5), (-erx * 0.3, ey + ery * 0.5), (-ex - erx * 1.3, ey + ery * 0.9)])
    fs(c, NIGHT, lw=3)


AGENT = dict(BOSS, skin=hexc("#c6b49a"), hair=_aide_hair, acc=_agent_acc, square=False, hrx=64, hry=72,
             hide_eyes=False, front=lambda c, S, g: _suit_front(c, S, g, tie=NIGHT))


# ------------------------------------------------------------------------------------------- impulsivity
def impulsivity(c, S):
    t = S.get("_t", 0.0)
    pant = S.pant if S.pant is not None else 1.0
    pulse = 1 + 0.025 * math.sin(t * 16) * pant
    run = S.run or 0
    if run:
        ph = t * 18
        # running: stretched body, legs whirling
        for k in range(4):
            lx = -70 + k * 46
            a = ph + k * 1.6
            fx, fy = lx + math.sin(a) * 34, -6 + min(0, math.cos(a)) * 22
            hose(c, [[(lx, -80), (fx, fy)]], 26, MUST)
        ell(c, 0, -120, 140, 80); body = c.copy_path(); fs(c, MUST); sh_body(c, body, 0.3)
        hx, hy = 110, -200
    else:
        # sitting
        for sd in (-1, 1):
            ell(c, sd * 104, -16, 44, 22); fs(c, MUST)
        ell(c, 0, -120, 120 * pulse, 110 * pulse)
        body = c.copy_path()
        fs(c, MUST)
        sh_body(c, body, 0.3)
        ell(c, 0, -100, 70, 75); fill(c, shade(MUST, 1.25))
        for (sx, sy, r) in ((-70, -150, 18), (64, -80, 14), (-40, -60, 10)):
            ell(c, sx, sy, r, r * 0.85); fill(c, MUST_D)
        for sd in (-1, 1):
            hose(c, [[(sd * 42, -110), (sd * 46, -12)]], 30, MUST)
            ell(c, sd * 48, -6, 30, 15); fs(c, MUST)
        hx, hy = 0, -268
    # tail
    wag = math.sin(t * 20) * 0.6 * (S.wag or 0)
    c.save(); c.translate(-110 if not run else -140, -110); c.rotate(-0.6 + wag)
    c.move_to(0, 0); c.curve_to(-40, -20, -50, -70, -30, -100)
    src(c, INK); c.set_line_width(26); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    c.move_to(0, 0); c.curve_to(-40, -20, -50, -70, -30, -100)
    src(c, MUST); c.set_line_width(16); c.stroke()
    c.restore()
    # head
    flap = math.sin(t * 20) * 0.4 * run
    for sd in (-1, 1):
        c.save(); c.translate(hx + sd * 78, hy - 30); c.rotate(sd * (0.25 + flap))
        ell(c, 0, 60, 34, 74); fs(c, hexc("#c4732a")); c.restore()
    ell(c, hx, hy, 98, 92)
    head = c.copy_path()
    fs(c, MUST)
    sh_body(c, head, 0.25)
    # muzzle + nose
    ell(c, hx, hy + 38, 58, 40); fs(c, shade(MUST, 1.3), lw=3)
    ell(c, hx, hy + 16, 18, 12); fill(c, INK)
    # mouth: the dumbest grin
    bark = S.bark or 0
    c.move_to(hx - 52, hy + 44)
    c.curve_to(hx - 30, hy + 74 + bark * 40, hx + 30, hy + 74 + bark * 40, hx + 52, hy + 44)
    c.curve_to(hx + 20, hy + 54, hx - 20, hy + 54, hx - 52, hy + 44)
    c.close_path()
    fs(c, hexc("#5b1a24"), lw=3)
    if not S.mouthful:
        tb = math.sin(t * 16) * 6 * pant
        c.move_to(hx + 4, hy + 58)
        c.curve_to(hx + 40, hy + 70, hx + 46, hy + 120 + tb, hx + 26, hy + 132 + tb)
        c.curve_to(hx + 6, hy + 138 + tb, hx - 6, hy + 100, hx + 4, hy + 58)
        c.close_path()
        fs(c, hexc("#ff7d9c"), lw=3)
        line(c, hx + 18, hy + 74, hx + 22, hy + 112 + tb * 0.5, hexc("#d9506e"), 3)
    # googly eyes, each looking its own way
    wall = S.wall if S.wall is not None else 1.0
    for sd, (lx, ly) in ((-1, (-0.75, -0.55)), (1, (0.8, 0.6))):
        ex, ey = hx + sd * 40, hy - 32
        ell(c, ex, ey, 30, 32); fs(c, PAPER, lw=4)
        px = ex + (lx * wall + (S.look or 0) * (1 - wall)) * 14
        py = ey + (ly * wall + (S.looky or 0) * (1 - wall)) * 14
        ell(c, px, py, 10, 10); fill(c, INK)
        ell(c, px - 3, py - 3, 3, 3); fill(c, PAPER)
    if S.hold == "cage":
        cage(c, hx + 70, hy + 110, S, 0.8)


# ------------------------------------------------------------------------------------------- critters
def thing(c, S):
    t = S.get("_t", 0.0)
    thing_body(c, 0, -40, S.k or 1.0, t, S.writhe or 0, bite=S.bitey or 0)


def creature(c, S):
    """Subject 7. form=0: jagged, many-eyed nightmare. form=1: a soft round blob with two big eyes."""
    t = S.get("_t", 0.0)
    f = max(0.0, min(1.0, S.form or 0))
    w = S.writhe or 0
    cy = -150
    # aura
    g = cairo.RadialGradient(0, cy, 40, 0, cy, 300)
    g.add_color_stop_rgba(0, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0.25 + 0.15 * f)
    g.add_color_stop_rgba(1, TEAL_L[0], TEAL_L[1], TEAL_L[2], 0)
    c.set_source(g); c.arc(0, cy, 300, 0, TAU); c.fill()
    # tendrils
    n_t = 6
    for i in range(n_t):
        base = TAU * i / n_t + 0.4
        length = 170 * (1 - f) + 60 * f
        wav = math.sin(t * (4 + 6 * w) + i * 1.3)
        a = base + wav * 0.3
        x0, y0 = math.cos(base) * 120, cy + math.sin(base) * 100
        x1, y1 = x0 + math.cos(a) * length, y0 + math.sin(a) * length
        mx, my = (x0 + x1) / 2 + math.sin(t * 5 + i) * 30, (y0 + y1) / 2 + math.cos(t * 4 + i) * 30
        c.move_to(x0, y0); c.curve_to(mx, my, mx, my, x1, y1)
        src(c, INK); c.set_line_width(22 - 8 * f); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        c.move_to(x0, y0); c.curve_to(mx, my, mx, my, x1, y1)
        src(c, NIGHT); c.set_line_width(14 - 6 * f); c.stroke()
    # pointing tendril
    if S.point:
        ang = S.point_dir or 0.0
        k = S.point
        x0, y0 = math.cos(ang) * 120, cy + math.sin(ang) * 90
        x1, y1 = x0 + math.cos(ang) * 200 * k, y0 + math.sin(ang) * 200 * k
        c.move_to(x0, y0); c.line_to(x1, y1)
        src(c, INK); c.set_line_width(20); c.stroke()
        src(c, NIGHT); c.move_to(x0, y0); c.line_to(x1, y1); c.set_line_width(12); c.stroke()
        ell(c, x1, y1, 14, 14); fs(c, NIGHT, lw=3)
    # body
    n = 40
    rnd = random.Random(int(t * 15))
    spikes = 70 * (1 - f) + 6 * f
    sq = 1 + 0.05 * math.sin(t * 3) * f
    for i in range(n + 1):
        a = TAU * i / n
        spike = spikes * (1 if i % 2 == 0 else 0.15) * (0.7 + 0.3 * math.sin(t * 6 + i))
        r = 150 + spike + rnd.uniform(-1, 1) * 10 * w
        px, py = math.cos(a) * r * 1.05, cy + math.sin(a) * r * 0.9 * sq
        (c.move_to if i == 0 else c.line_to)(px, py)
    c.close_path()
    src(c, NIGHT); c.fill_preserve(); src(c, INK); c.set_line_width(5); c.stroke()
    # inner sheen
    ell(c, -40, cy - 50, 70, 40); src(c, INDIGO, 0.5); c.fill()
    # scary eyes (fade out as it calms)
    a_scary = 1 - min(1.0, f * 1.6)
    if a_scary > 0.01:
        for (ex, ey, r) in ((-70, -40, 16), (-20, -70, 22), (40, -55, 18), (80, -10, 12), (-90, 20, 10)):
            g = cairo.RadialGradient(ex, cy + ey, 0, ex, cy + ey, r * 2.2)
            g.add_color_stop_rgba(0, 1, 0.3, 0.45, 0.7 * a_scary)
            g.add_color_stop_rgba(1, 1, 0.3, 0.45, 0)
            c.set_source(g); c.arc(ex, cy + ey, r * 2.2, 0, TAU); c.fill()
            ell(c, ex, cy + ey, r, r * 0.8); src(c, hexc("#ff5f87"), a_scary); c.fill()
            ell(c, ex, cy + ey, r * 0.2, r * 0.7); src(c, NIGHT, a_scary); c.fill()
        # jagged mouth
        c.move_to(-90, cy + 50)
        for i in range(13):
            c.line_to(-90 + i * 15, cy + 50 + (22 if i % 2 else -4))
        src(c, PAPER, a_scary); c.set_line_width(4); c.stroke()
    # calm eyes
    a_calm = max(0.0, min(1.0, (f - 0.35) * 1.6))
    if a_calm > 0.01:
        for sd in (-1, 1):
            ex, ey = sd * 55, cy - 30
            ell(c, ex, ey, 40, 46); src(c, PAPER, a_calm); c.fill_preserve(); src(c, INK, a_calm)
            c.set_line_width(4); c.stroke()
            lx = (S.look or 0) * 14
            ly = (S.looky or 0) * 16
            if S.eyes == "roll":
                ly = -22
            if S.eyes == "happy":
                ell(c, ex, ey, 40, 46); src(c, NIGHT, a_calm); c.fill()
                c.move_to(ex - 28, ey + 6); c.curve_to(ex - 10, ey - 24, ex + 10, ey - 24, ex + 28, ey + 6)
                src(c, TEAL_L, a_calm); c.set_line_width(7); c.stroke()
                continue
            r_i = 24 if S.eyes != "wide" else 14
            ell(c, ex + lx, ey + ly, r_i, r_i * 1.1); src(c, TEAL, a_calm); c.fill()
            ell(c, ex + lx, ey + ly, r_i * 0.5, r_i * 0.55); src(c, NIGHT, a_calm); c.fill()
            ell(c, ex + lx - 8, ey + ly - 10, 7, 7); src(c, PAPER, a_calm); c.fill()
            if S.eyes == "half" or S.eyes == "roll":
                c.save(); ell(c, ex, ey, 40, 46); c.clip()
                c.rectangle(ex - 44, ey - 50, 88, 50); src(c, NIGHT, a_calm); c.fill()
                c.restore()
        # little smile
        c.move_to(-22, cy + 40); c.curve_to(-10, cy + 54, 10, cy + 54, 22, cy + 40)
        src(c, TEAL_L, a_calm); c.set_line_width(5); c.stroke()
        if S.blush:
            for sd in (-1, 1):
                ell(c, sd * 95, cy + 20, 18, 10); src(c, hexc("#ff6b8f"), 0.6 * S.blush * a_calm); c.fill()


DRAW = {
    "tired": lambda c, S: person(c, S, TIRED),
    "emb": lambda c, S: person(c, S, EMB),
    "boss": lambda c, S: person(c, S, BOSS),
    "aide": lambda c, S: person(c, S, AIDE),
    "guard": lambda c, S: person(c, S, GUARD),
    "guard2": lambda c, S: person(c, S, GUARD2),
    "recept": lambda c, S: person(c, S, RECEPT),
    "sci": lambda c, S: person(c, S, SCI),
    "agent": lambda c, S: person(c, S, AGENT),
    "imp": impulsivity,
    "thing": thing,
    "creature": creature,
    "rec": lambda c, S: prop(c, "recorder", 0, 0, S),
}

HEADS = {"tired": 520, "emb": 560, "boss": 690, "aide": 560, "guard": 600, "guard2": 600, "recept": 540,
         "sci": 580, "agent": 640, "imp": 360, "thing": 90, "creature": 330, "rec": 60}
