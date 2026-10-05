"""Backgrounds ("sets"). World space is 1080 x 1920 at camera zoom 1.
Each set draws its background, calls `actors(layer)` at the right depth, then its foreground."""
import math
import random
import cairo
from .draw import (OUT, LW, TAU, hexc, shade, src, ell, rrect, fs, fill, poly, line, text, lin, radial,
                   star, heart, cloud)
from .keys import State
from .characters import kid, C_HAT, C_BRIM

W, H = 1080, 1920

COATS = ["#e05a47", "#4a7fd0", "#3f9e5a", "#f0a52a", "#8b4fd0", "#2bb3a8", "#d94f8a", "#6a6f7d", "#b8642e",
         "#5ab0e0", "#c9c24a", "#9a3d3d"]
HAIRS = ["#2a1a12", "#4a3020", "#7a4a2a", "#d9a440", "#b03a1a", "#151515", "#e8d080"]
SKINS = ["#f6d2ae", "#f3cfa8", "#e0b088", "#c68a62", "#9a6440", "#7a4a2e", "#f8dcc0"]
STYLES = ["short", "short", "spiky", "bob", "pigtails", "cap", "beanie", "afro"]


def _rand_look(rng):
    return dict(coat=hexc(rng.choice(COATS)), hairc=hexc(rng.choice(HAIRS)), skin=hexc(rng.choice(SKINS)),
                hair=rng.choice(STYLES), capc=hexc(rng.choice(COATS)), glasses=rng.random() < 0.15,
                pants=hexc("#3a3a55"))


# ---------------------------------------------------------------------------------------------
# Crowd behaviour
# ---------------------------------------------------------------------------------------------
def crowd_state(mood, t, seed, target_x=None, my_x=0.0):
    """Expression state for one crowd member."""
    r = random.Random(seed)
    phase = r.random() * 10
    s = State(_t=t, seated=1, autoblink=0)
    blink_p = (t + phase) % (3.0 + r.random() * 2)
    s["blink"] = 1.0 if blink_p < 0.12 else 0.0
    s["look"] = math.sin(t * 0.4 + phase) * 0.4
    s["arms"] = None
    dy = 0.0
    quirk = r.random()
    if mood == "laugh" or mood == "roar":
        amp = 1.0 if mood == "roar" else 0.7
        s.update(eyes="happy", mouth="grin", talk=0.4 + 0.4 * abs(math.sin(t * 14 + phase)))
        dy = -abs(math.sin(t * 9 + phase)) * 10 * amp
        if quirk < 0.2 and mood == "laugh":
            s.update(eyes="open", mouth="smile", talk=0)
            dy = 0
    elif mood == "stare":
        s.update(eyes="stare", mouth="flat", blink=0)
        if target_x is not None:
            s["look"] = max(-1, min(1, (target_x - my_x) / 250))
        s["looky"] = 0.2
    elif mood == "wtf":
        s.update(eyes="wide", mouth="o" if quirk < 0.5 else "frown", brow=1.0, talk=0.2 * abs(math.sin(t * 8 + phase)))
        if target_x is not None:
            s["look"] = max(-1, min(1, (target_x - my_x) / 250))
        dy = math.sin(t * 3 + phase) * 3
    elif mood == "shock":
        s.update(eyes="wide", mouth="o", brow=1.0)
    elif mood == "cringe":
        s.update(eyes="squint" if quirk < 0.6 else "half", mouth="grimace" if quirk < 0.5 else "frown", brow=0.6)
    elif mood == "bored":
        s.update(eyes="half", mouth="flat", looky=0.3)
    elif mood == "smile":
        s.update(eyes="open", mouth="smile")
    elif mood == "cheer":
        s.update(eyes="happy", mouth="grin", talk=0.5, arms="up")
        dy = -abs(math.sin(t * 7 + phase)) * 14
    elif mood == "uneasy":
        s.update(eyes="open", mouth="wobbly" if quirk < 0.5 else "flat", brow=0.7, look=(quirk - 0.5) * 2)
        if quirk < 0.3:
            s.update(eyes="happy", mouth="grin", talk=0.3)
    else:  # idle
        s.update(eyes="open" if quirk > 0.2 else "half", mouth="smile" if quirk > 0.4 else "flat")
    return s, dy


def apply_arms(s):
    from .characters import ARMS
    a = s.pop("arms", None)
    if a:
        aLx, aLy, aRx, aRy = ARMS[a]
        s.update(aLx=aLx, aLy=aLy, aRx=aRx, aRy=aRy)
    return s


# ---------------------------------------------------------------------------------------------
# Shared pieces
# ---------------------------------------------------------------------------------------------
def cinderblock(c, x0, y0, x1, y1, col):
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    fill(c, col)
    dark = shade(col, 0.88)
    bh, bw = 64, 150
    row = 0
    y = y0
    while y < y1:
        line(c, x0, y, x1, y, dark, 3)
        off = (bw / 2) if row % 2 else 0
        x = x0 - off
        while x < x1:
            line(c, x, y, x, min(y + bh, y1), dark, 3)
            x += bw
        y += bh
        row += 1


def wall_clock(c, x, y, r, t, tick_time=True):
    ell(c, x, y, r, r); fs(c, (1, 1, 1), lw=LW * 1.4)
    ell(c, x, y, r * 0.88, r * 0.88); src(c, OUT); c.set_line_width(2); c.stroke()
    for i in range(12):
        a = TAU * i / 12
        line(c, x + math.cos(a) * r * 0.72, y + math.sin(a) * r * 0.72, x + math.cos(a) * r * 0.82,
             y + math.sin(a) * r * 0.82, OUT, 4 if i % 3 == 0 else 2)
    sec = math.floor(t) if tick_time else t
    for ang, ln, w in ((TAU * (10.2 / 12) - math.pi / 2, 0.45, 7), (TAU * (sec % 60) / 60 + 1.2 - math.pi / 2, 0.68, 4)):
        line(c, x, y, x + math.cos(ang) * r * ln, y + math.sin(ang) * r * ln, OUT, w)
    a = TAU * ((sec + 12) % 60) / 60 - math.pi / 2
    line(c, x, y, x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, hexc("#d83030"), 2.5)
    ell(c, x, y, 6, 6); fill(c, OUT)


def bunting(c, x0, x1, y, n=14, sag=40):
    cols = [hexc(h) for h in ("#ff6fa8", "#36c9bd", "#f4c430", "#6fb7e9", "#9b6ff0")]
    line_pts = []
    for i in range(n + 1):
        u = i / n
        line_pts.append((x0 + (x1 - x0) * u, y + sag * 4 * u * (1 - u)))
    c.move_to(*line_pts[0])
    for p in line_pts[1:]:
        c.line_to(*p)
    src(c, OUT); c.set_line_width(3); c.stroke()
    for i in range(n):
        (ax, ay), (bx, by) = line_pts[i], line_pts[i + 1]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        poly(c, [(ax + 4, ay), (bx - 4, by), (mx, my + 50)])
        fs(c, cols[i % len(cols)], lw=3)


# ---------------------------------------------------------------------------------------------
# OFFICE
# ---------------------------------------------------------------------------------------------
def set_office(c, t, P, actors):
    c.rectangle(-400, -400, W + 800, 1730); fill(c, hexc("#f1dfc0"))
    for x in range(-400, W + 400, 70):
        c.rectangle(x, -400, 32, 1730); src(c, hexc("#e9d3ad"), 0.6); c.fill()
    c.rectangle(-400, 1080, W + 800, 250); fs(c, hexc("#c99d6a"), lw=4)
    for x in range(-380, W + 400, 180):
        rrect(c, x, 1105, 150, 200, 8); src(c, shade(hexc("#c99d6a"), 0.85)); c.set_line_width(4); c.stroke()
    # floor
    c.rectangle(-400, 1330, W + 800, 900); fill(c, hexc("#a8723f"))
    for i, y in enumerate(range(1330, 2300, 70)):
        line(c, -400, y, W + 400, y, shade(hexc("#a8723f"), 0.8), 3)
        off = (i % 2) * 160
        for x in range(-400 + off, W + 400, 320):
            line(c, x, y, x, y + 70, shade(hexc("#a8723f"), 0.8), 3)
    line(c, -400, 1330, W + 400, 1330, OUT, 5)
    # window
    rrect(c, 70, 300, 380, 440, 10); fs(c, (1, 1, 1), lw=LW)
    c.rectangle(92, 322, 336, 396)
    c.set_source(lin(0, 322, 0, 718, [(0, hexc("#7cc6ff")), (1, hexc("#d6f0ff"))])); c.fill()
    for (cx, cy, s) in ((180, 420, 1.0), (340, 520, 0.8)):
        cx += (t * 6) % 60
        for dx, dy, r in ((0, 0, 34), (34, -12, 40), (70, 0, 30)):
            ell(c, cx + dx * s, cy + dy * s, r * s, r * s * 0.8); fill(c, (1, 1, 1))
    line(c, 260, 322, 260, 718, (1, 1, 1), 14)
    line(c, 92, 520, 428, 520, (1, 1, 1), 14)
    # poster
    rrect(c, 560, 260, 400, 360, 16); fs(c, hexc("#ffb8cc"))
    heart(c, 760, 400, 70); fs(c, hexc("#ff4f7e"))
    text(c, "FEELINGS", 760, 520, 54, "Luckiest Guy", (1, 1, 1), OUT, 8)
    text(c, "ARE VALID", 760, 585, 46, "Luckiest Guy", (1, 1, 1), OUT, 8)
    # framed diploma
    rrect(c, 600, 680, 160, 120, 6); fs(c, hexc("#c69b4a"))
    c.rectangle(615, 695, 130, 90); fill(c, (1, 1, 0.95))
    text(c, "PC", 680, 755, 40, "Luckiest Guy", hexc("#2a5fb0"))
    # door (right)
    dopen = P.get("door", 0.0)
    rrect(c, 830, 700, 230, 640, 6)
    fs(c, shade(hexc("#8a5a32"), 0.9))
    if dopen > 0:
        c.rectangle(840, 710, 210 * dopen, 620); fill(c, hexc("#2a2a35"))
    c.save()
    c.translate(840 + 210 * dopen, 0)
    c.scale(max(0.05, 1 - dopen), 1)
    rrect(c, 0, 710, 210, 620, 4); fs(c, hexc("#a8703f"))
    rrect(c, 30, 750, 150, 220, 6); src(c, shade(hexc("#a8703f"), 0.8)); c.set_line_width(5); c.stroke()
    rrect(c, 30, 1010, 150, 260, 6); src(c, shade(hexc("#a8703f"), 0.8)); c.set_line_width(5); c.stroke()
    ell(c, 30, 1030, 14, 14); fs(c, hexc("#e2c060"))
    c.restore()
    # desk (back, left)
    c.rectangle(40, 1130, 520, 34); fs(c, hexc("#6b4426"))
    c.rectangle(60, 1164, 480, 190); fs(c, hexc("#7c4e2c"))
    for y in (1190, 1260):
        rrect(c, 340, y, 170, 56, 6); fs(c, hexc("#8d5c34"), lw=4)
        line(c, 400, y + 28, 450, y + 28, hexc("#e2c060"), 6)
    # monitor + mug
    rrect(c, 110, 960, 220, 150, 10); fs(c, hexc("#2a2a33"))
    c.rectangle(124, 974, 192, 122); fill(c, hexc("#4fb4ff"))
    heart(c, 220, 1040, 26); fill(c, (1, 1, 1))
    c.rectangle(205, 1110, 30, 22); fs(c, hexc("#2a2a33"), lw=3)
    rrect(c, 410, 1060, 70, 72, 10); fs(c, (1, 1, 1))
    text(c, "#1", 445, 1108, 30, "Luckiest Guy", hexc("#e04050"))
    ell(c, 490, 1095, 18, 22, -math.pi / 2, math.pi / 2); src(c, OUT); c.set_line_width(6); c.stroke()
    # plant
    rrect(c, 625, 1240, 110, 100, 12); fs(c, hexc("#d9673a"))
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.32
        x1, y1 = 680 + math.cos(a) * 190, 1240 + math.sin(a) * 210
        c.move_to(680, 1240); c.curve_to(680 + math.cos(a) * 60, 1180, x1 - 20, y1 + 30, x1, y1)
        src(c, OUT); c.set_line_width(26); c.stroke()
        c.move_to(680, 1240); c.curve_to(680 + math.cos(a) * 60, 1180, x1 - 20, y1 + 30, x1, y1)
        src(c, hexc("#3fae5a")); c.set_line_width(17); c.stroke()
    if P.get("night"):
        c.rectangle(-400, -400, W + 800, H + 800); src(c, (0.05, 0.05, 0.2), 0.3); c.fill()
    actors(0)


# ---------------------------------------------------------------------------------------------
# HALLWAY
# ---------------------------------------------------------------------------------------------
def set_hallway(c, t, P, actors):
    night = P.get("night", 0)
    c.rectangle(-600, -400, W + 1200, 1720); fill(c, hexc("#cfe3d8"))
    c.rectangle(-600, 1180, W + 1200, 140); fill(c, hexc("#9cc4b0"))
    # bulletin board + flyer
    if P.get("board", 1):
        rrect(c, 250, 210, 580, 400, 10); fs(c, hexc("#b88a58"))
        c.rectangle(270, 230, 540, 360); fill(c, hexc("#d9b07a"))
        c.save(); c.translate(540, 410); c.rotate(-0.03)
        rrect(c, -210, -160, 420, 320, 6); fs(c, (1, 1, 1), lw=4)
        c.rectangle(-210, -160, 420, 90); fill(c, hexc("#ff6fa8"))
        text(c, "EMOTIONAL", 0, -122, 44, "Luckiest Guy", (1, 1, 1), OUT, 6)
        text(c, "EDUCATION ASSEMBLY", 0, -80, 30, "Luckiest Guy", (1, 1, 1), OUT, 5)
        text(c, "FRIDAY! WHOLE SCHOOL!", 0, -18, 30, "Luckiest Guy", hexc("#2a5fb0"))
        heart(c, -120, 80, 46); fs(c, hexc("#ff4f7e"), lw=4)
        text(c, "FEELINGS", 60, 60, 34, "Luckiest Guy", OUT)
        text(c, "ARE REPS", 60, 105, 34, "Luckiest Guy", OUT)
        ell(c, 0, -150, 10, 10); fs(c, hexc("#e04050"), lw=3)
        c.restore()
    # lockers
    door_x = P.get("door_x", None)
    x = -600
    while x < W + 600:
        if door_x is not None and door_x - 120 < x < door_x + 260:
            x += 120
            continue
        rrect(c, x + 4, 640, 112, 640, 4); fs(c, hexc("#3e6fc4"), lw=4)
        for k in range(4):
            line(c, x + 30, 680 + k * 14, x + 90, 680 + k * 14, shade(hexc("#3e6fc4"), 0.6), 4)
        rrect(c, x + 84, 940, 14, 60, 5); fs(c, hexc("#c9ced6"), lw=3)
        x += 120
    if door_x is not None:
        dopen = P.get("door", 0.0)
        dx = door_x
        rrect(c, dx - 10, 560, 260, 740, 6); fs(c, hexc("#6b4426"))
        # light behind the door
        c.rectangle(dx + 10, 580, 220, 700)
        fill(c, hexc("#fff3c4") if night else hexc("#3a3a45"))
        c.save(); c.translate(dx + 10, 0); c.scale(max(0.06, 1 - dopen * 0.85), 1)
        c.rectangle(0, 580, 220, 700); fs(c, hexc("#a8703f"), lw=4)
        rrect(c, 40, 640, 140, 200, 8); fs(c, hexc("#d8ecf8"), lw=4)
        rrect(c, 30, 880, 160, 46, 6); fs(c, hexc("#f2d36b"), lw=3)
        text(c, "PRINCIPAL", 110, 914, 28, "Luckiest Guy", OUT)
        ell(c, 190, 1000, 13, 13); fs(c, hexc("#e2c060"), lw=3)
        c.restore()
    # floor
    c.rectangle(-600, 1320, W + 1200, 900); fill(c, hexc("#d8d4cc"))
    for i, y in enumerate(range(1320, 2300, 110)):
        for j, xx in enumerate(range(-600, W + 600, 110)):
            if (i + j) % 2 == 0:
                c.rectangle(xx, y, 110, 110); src(c, hexc("#c4bfb4")); c.fill()
    line(c, -600, 1320, W + 600, 1320, OUT, 5)
    if door_x is not None and night and P.get("door", 0) > 0:
        dopen = P.get("door", 0.0)
        # light wedge on the floor
        poly(c, [(door_x + 10 + 220 * (1 - dopen * 0.85), 1320), (door_x + 230, 1320),
                 (door_x + 330, 1920), (door_x + 10 + 230 * (1 - dopen * 0.85) - 100 * dopen, 1920)])
        src(c, hexc("#fff3c4"), 0.45); c.fill()
    if night:
        c.rectangle(-600, -400, W + 1200, H + 800); src(c, (0.04, 0.04, 0.16), 0.42); c.fill()
        if door_x is not None and P.get("door", 0) > 0:
            c.rectangle(door_x + 10, 580, 220, 700)
            c.set_source(radial(door_x + 120, 900, 520, (1, 0.95, 0.75, 0.35), (1, 0.95, 0.75, 0)))
            c.fill()
    actors(0)


# ---------------------------------------------------------------------------------------------
# GYM: STAGE (looking at the stage, audience heads in the foreground)
# ---------------------------------------------------------------------------------------------
_HEADS = None


def _heads():
    global _HEADS
    if _HEADS is None:
        rng = random.Random(11)
        rows = []
        for r, (y, n, rad) in enumerate(((1520, 8, 58), (1665, 7, 70), (1830, 6, 84))):
            row = []
            for i in range(n):
                x = (i + 0.5) * W / n + rng.uniform(-25, 25) + (40 if r % 2 else 0) - 20
                row.append(dict(x=x, y=y + rng.uniform(-10, 10), r=rad * rng.uniform(0.92, 1.08),
                                hair=hexc(rng.choice(HAIRS)), coat=hexc(rng.choice(COATS)),
                                style=rng.choice(["round", "round", "spiky", "pig", "cap", "beanie"]),
                                capc=hexc(rng.choice(COATS)), seed=rng.random() * 100))
            rows.append(row)
        _HEADS = rows
    return _HEADS


def audience_backs(c, t, mood):
    for row in _heads():
        for h in row:
            x, y, r = h["x"], h["y"], h["r"]
            dy, dx, rot = 0, 0, 0
            ph = h["seed"]
            if mood in ("laugh", "roar", "cheer"):
                dy = -abs(math.sin(t * 9 + ph)) * r * (0.22 if mood != "laugh" else 0.14)
                rot = math.sin(t * 7 + ph) * 0.08
            elif mood == "wtf":
                rot = math.sin(ph) * 0.25
                dx = math.sin(t * 2 + ph) * 4
            elif mood == "idle":
                rot = math.sin(t * 0.7 + ph) * 0.03
            c.save(); c.translate(x + dx, y + dy); c.rotate(rot)
            ell(c, 0, r * 1.45, r * 1.35, r * 0.95); fs(c, h["coat"])
            if h["style"] == "pig":
                for s in (-1, 1):
                    ell(c, s * r * 0.95, r * 0.2, r * 0.32, r * 0.42); fs(c, h["hair"])
            ell(c, 0, 0, r, r * 1.02); fs(c, h["hair"])
            if h["style"] == "spiky":
                pts = []
                for i in range(9):
                    a = math.pi + math.pi * i / 8
                    rr = r * (1.18 if i % 2 else 0.95)
                    pts.append((math.cos(a) * rr, math.sin(a) * rr))
                poly(c, pts); fs(c, h["hair"])
            elif h["style"] == "cap":
                ell(c, 0, -r * 0.1, r * 1.02, r * 0.9, math.pi, TAU); c.close_path(); fs(c, h["capc"])
            elif h["style"] == "beanie":
                ell(c, 0, -r * 0.05, r * 1.02, r * 1.0, math.pi, TAU); c.close_path(); fs(c, h["capc"])
                ell(c, 0, -r * 1.02, r * 0.2, r * 0.18); fs(c, (1, 1, 1))
            for s in (-1, 1):
                ell(c, s * r * 0.98, r * 0.15, r * 0.14, r * 0.22); fs(c, hexc("#f0c8a0"), lw=3)
            c.restore()


def set_stage(c, t, P, actors):
    cinderblock(c, -400, -400, W + 400, 1150, hexc("#e8dcc2"))
    bunting(c, -100, W + 100, 120, 16, 60)
    banner = P.get("banner", "EMOTIONAL EDUCATION")
    sub = P.get("banner2", "ASSEMBLY")
    rrect(c, 110, 230, 860, 190, 18); fs(c, hexc("#3b6fd8"), lw=6)
    rrect(c, 126, 246, 828, 158, 12); src(c, (1, 1, 1)); c.set_line_width(3); c.stroke()
    text(c, banner, 540, 322, 58 if len(banner) < 22 else 50, "Luckiest Guy", (1, 1, 1), OUT, 9)
    text(c, sub, 540, 392, 46, "Luckiest Guy", hexc("#f4c430"), OUT, 7)
    heart(c, 175, 330, 30); fs(c, hexc("#ff6fa8"), lw=4)
    heart(c, 905, 330, 30); fs(c, hexc("#ff6fa8"), lw=4)
    wall_clock(c, 865, 540, 52, P.get("clock_t", t))
    # curtains
    for side in (-1, 1):
        def X(x):
            return x if side < 0 else W - x
        c.move_to(X(-60), 60)
        c.line_to(X(150), 60)
        c.curve_to(X(110), 600, X(190), 900, X(120), 1170)
        c.line_to(X(-60), 1170)
        c.close_path()
        fs(c, hexc("#b0243a"))
        for k in range(1, 4):
            line(c, X(k * 34), 70, X(k * 34), 1160, shade(hexc("#b0243a"), 0.7), 5)
    rrect(c, -40, 40, W + 80, 70, 10); fs(c, hexc("#b0243a"))
    for i in range(12):
        ell(c, i * 100 + 40, 112, 50, 26, 0, math.pi); fs(c, hexc("#b0243a"))
    line(c, -40, 110, W + 40, 110, hexc("#f4c430"), 8)
    # stage floor
    poly(c, [(-200, 1120), (W + 200, 1120), (W + 260, 1300), (-260, 1300)])
    fill(c, hexc("#cf9f62"))
    for k in range(-6, 8):
        line(c, 540 + k * 110, 1120, 540 + k * 150, 1300, shade(hexc("#cf9f62"), 0.85), 3)
    line(c, -260, 1120, W + 260, 1120, OUT, 4)
    # spotlights
    if P.get("spot", 1):
        for sx in (P.get("spot_x", 540),):
            c.set_source(radial(sx, 1220, 330, (1, 1, 0.85, 0.35), (1, 1, 0.85, 0.0)))
            ell(c, sx, 1220, 330, 90); c.fill()
    # speakers
    for sx in (175, 905):
        rrect(c, sx - 60, 900, 120, 220, 10); fs(c, hexc("#23232b"))
        for yy, rr in ((960, 30), (1050, 44)):
            ell(c, sx, yy, rr, rr); fs(c, hexc("#3a3a45"), lw=4)
            ell(c, sx, yy, rr * 0.35, rr * 0.35); fill(c, hexc("#16161c"))
    if P.get("stool", 0):
        sx = P.get("stool_x", 540)
        for dx in (-38, 38):
            line(c, sx + dx * 0.6, 1085, sx + dx * 1.3, 1235, OUT, 16)
            line(c, sx + dx * 0.6, 1085, sx + dx * 1.3, 1235, hexc("#c0c6cf"), 9)
        line(c, sx - 50, 1180, sx + 50, 1180, OUT, 12)
        line(c, sx - 50, 1180, sx + 50, 1180, hexc("#c0c6cf"), 6)
        ell(c, sx, 1080, 62, 18); fs(c, hexc("#d8382b"))
    if P.get("table", 0):
        tx = P.get("table_x", 330)
        rrect(c, tx - 110, 1040, 220, 28, 6); fs(c, (1, 1, 1))
        poly(c, [(tx - 110, 1068), (tx + 110, 1068), (tx + 96, 1140), (tx - 96, 1140)])
        fs(c, hexc("#e45064"), lw=4)
        for k in range(-3, 4):
            line(c, tx + k * 30, 1070, tx + k * 27, 1138, (1, 1, 1), 5)
        line(c, tx, 1140, tx, 1235, OUT, 12)
        ell(c, tx, 1238, 60, 12); fs(c, hexc("#555555"))
        # candle
        rrect(c, tx - 8, 990, 16, 50, 4); fs(c, (1, 1, 0.95), lw=3)
        ell(c, tx, 980 + math.sin(t * 20) * 2, 7, 12); fill(c, hexc("#ffb020"))
    if P.get("toilet", 0):
        tx = P.get("toilet_x", 760)
        rrect(c, tx - 30, 980, 90, 140, 12); fs(c, (1, 1, 1))
        ell(c, tx - 40, 1130, 80, 30); fs(c, (1, 1, 1))
        poly(c, [(tx - 90, 1135), (tx + 10, 1135), (tx - 5, 1230), (tx - 75, 1230)]); fs(c, (1, 1, 1))
        ell(c, tx - 40, 1128, 58, 18); fill(c, hexc("#9fd8ff"))
    actors(0)
    # stage front
    c.rectangle(-300, 1300, W + 600, 130); fs(c, hexc("#7a4a28"))
    for k in range(-2, 10):
        rrect(c, k * 140 + 10, 1318, 120, 94, 6); src(c, shade(hexc("#7a4a28"), 0.8)); c.set_line_width(4); c.stroke()
    # gym floor
    c.rectangle(-300, 1430, W + 600, 900); fill(c, hexc("#d9a35f"))
    for y in range(1430, 2300, 60):
        line(c, -300, y, W + 300, y, shade(hexc("#d9a35f"), 0.9), 2)
    actors(1)
    if P.get("audience", 1):
        audience_backs(c, t, P.get("mood", "idle"))
    actors(2)


# ---------------------------------------------------------------------------------------------
# GYM: STANDS (bleachers facing the camera)
# ---------------------------------------------------------------------------------------------
ROW_Y = [1700 - r * 175 for r in range(6)]
SEAT_OFF = 32
_STANDS = None
RESERVED = {2: [330, 540, 750]}


def _stands():
    global _STANDS
    if _STANDS is None:
        rng = random.Random(5)
        rows = []
        for r in range(6):
            row = []
            n = 7
            for i in range(n):
                x = (i + 0.5) * (W + 120) / n - 60 + rng.uniform(-18, 18)
                if any(abs(x - rx) < 110 for rx in RESERVED.get(r, [])):
                    continue
                row.append(dict(x=x, look=_rand_look(rng), seed=rng.randint(0, 10 ** 6), sc=0.7 + rng.uniform(-0.03, 0.03)))
            rows.append(row)
        _STANDS = rows
    return _STANDS


def set_stands(c, t, P, actors):
    cinderblock(c, -400, -400, W + 400, 900, hexc("#e8dcc2"))
    # high windows
    for x in (80, 420, 760):
        rrect(c, x, 90, 240, 150, 6); fs(c, (1, 1, 1))
        c.rectangle(x + 12, 102, 216, 126); c.set_source(lin(0, 102, 0, 228, [(0, hexc("#9fd8ff")), (1, hexc("#e2f4ff"))])); c.fill()
        line(c, x + 120, 102, x + 120, 228, (1, 1, 1), 8)
    # pennant + clock
    poly(c, [(80, 330), (380, 370), (80, 410)]); fs(c, hexc("#2a5fb0"))
    text(c, "GO HAWKS", 190, 382, 30, "Luckiest Guy", (1, 1, 1))
    wall_clock(c, 900, 360, 60, P.get("clock_t", t))
    mood = P.get("mood", "idle")
    target = P.get("target_x", 540)
    stands = _stands()
    for r in range(5, -1, -1):
        y = ROW_Y[r]
        # bench
        c.rectangle(-400, y - 4, W + 800, 26); fs(c, hexc("#c99a5e"), lw=4)
        c.rectangle(-400, y + 22, W + 800, 150); fs(c, hexc("#8a8f99"), lw=4)
        for xx in range(-400, W + 400, 180):
            line(c, xx, y + 22, xx, y + 172, shade(hexc("#8a8f99"), 0.75), 3)
        for k in stands[r]:
            delay = (k["seed"] % 1000) / 1000 * 0.45
            m = P.get("mood_at", lambda tt: mood)(t - delay)
            s, dy = crowd_state(m, t, k["seed"], target, k["x"])
            apply_arms(s)
            c.save(); c.translate(k["x"], y + SEAT_OFF + dy); c.scale(k["sc"], k["sc"])
            kid(c, s, k["look"])
            c.restore()
        actors(r)
    # gym floor
    c.rectangle(-400, ROW_Y[0] + 172, W + 800, 600); fill(c, hexc("#d9a35f"))
    line(c, -400, ROW_Y[0] + 172, W + 400, ROW_Y[0] + 172, OUT, 4)
    actors(-1)


# ---------------------------------------------------------------------------------------------
# Inserts and cards
# ---------------------------------------------------------------------------------------------
def set_hat(c, t, P, actors):
    c.set_source(radial(540, 900, 900, (0.16, 0.16, 0.2, 1), (0.03, 0.03, 0.05, 1)))
    c.paint()
    ell(c, 540, 960, 600, 820); src(c, hexc("#c4283a")); c.set_line_width(60); c.stroke()
    rng = random.Random(2)
    names = ["ERIC CARTMAN", "CARTMAN", "CARTMAN :)", "E. CARTMAN", "CARTMAN!!", "ERIC C.", "CARTMAN",
             "CARTMAN", "THE CARTMAN KID", "CARTMAN", "ERIC CARTMAN", "CARTMAN (DEFINITELY)"]
    for i in range(22):
        x = rng.uniform(170, 910)
        y = rng.uniform(420, 1500)
        a = rng.uniform(-0.6, 0.6)
        c.save(); c.translate(x, y + math.sin(t * 2 + i) * 3); c.rotate(a)
        rrect(c, -150, -55, 300, 110, 8); fs(c, (1, 1, 0.93))
        text(c, names[i % len(names)], 0, 14, 36 if len(names[i % len(names)]) < 12 else 26, "Luckiest Guy", OUT)
        c.restore()
    actors(0)


def set_clock(c, t, P, actors):
    cinderblock(c, -200, -200, W + 200, H + 200, hexc("#e8dcc2"))
    wall_clock(c, 540, 820, 380, P.get("clock_t", t))
    actors(0)


def set_void(c, t, P, actors):
    c.set_source(radial(540, 900, 1200, (0.25, 0.1, 0.4, 1), (0.02, 0.0, 0.06, 1)))
    c.paint()
    rng = random.Random(9)
    for i in range(140):
        x, y = rng.uniform(-200, W + 200), rng.uniform(-200, H + 200)
        tw = 0.5 + 0.5 * math.sin(t * 3 + i)
        ell(c, x, y, 2 + 3 * tw * rng.random(), 2 + 3 * tw * rng.random()); src(c, (1, 1, 1), 0.4 + 0.5 * tw); c.fill()
    c.save(); c.translate(540, 900); c.rotate(t * 0.6)
    for k in range(4):
        c.save(); c.rotate(k * math.pi / 2)
        for i in range(80):
            a = i / 80 * TAU * 1.3
            r = 20 + i * 9
            (c.move_to if i == 0 else c.line_to)(math.cos(a) * r, math.sin(a) * r)
        src(c, (0.7, 0.5, 1.0), 0.35); c.set_line_width(14); c.stroke()
        c.restore()
    c.restore()
    words = P.get("void_words", [])
    for i, w in enumerate(words):
        a = t * 0.5 + i * TAU / max(1, len(words))
        x = 540 + math.cos(a) * 360
        y = 900 + math.sin(a) * 520
        text(c, w, x, y, 46, "Patrick Hand", (1, 1, 1), (0.1, 0, 0.2), 6, alpha=0.85)
    actors(0)


def set_imagine(c, t, P, actors):
    c.set_source(radial(540, 900, 1100, (0.45, 0.06, 0.08, 1), (0.08, 0.0, 0.02, 1)))
    c.paint()
    for i in range(18):
        a = TAU * i / 18 + t * 0.2
        poly(c, [(540, 900), (540 + math.cos(a) * 1600, 900 + math.sin(a) * 1600),
                 (540 + math.cos(a + 0.12) * 1600, 900 + math.sin(a + 0.12) * 1600)])
        src(c, (0, 0, 0), 0.18); c.fill()
    c.rectangle(-200, 1300, W + 400, 800); src(c, (0.1, 0.02, 0.04), 0.9); c.fill()
    actors(0)
    # dreamy border
    c.save()
    c.new_path()
    c.rectangle(-500, -500, W + 1000, H + 1000)
    cloud(c, 540, 930, 1000, 1480, 14, new=False)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    src(c, (1, 1, 1), 0.95); c.fill()
    c.restore()
    cloud(c, 540, 930, 1000, 1480, 14)
    src(c, OUT); c.set_line_width(8); c.stroke()


def set_card(c, t, P, actors):
    """Title / 'to be continued' / time-skip cards."""
    kind = P.get("card", "title")
    c.set_source(lin(0, 0, 0, H, [(0, hexc("#2a1b5c")), (1, hexc("#b0306a"))]))
    c.paint()
    c.save(); c.translate(540, 820); c.rotate(t * 0.25)
    for i in range(16):
        a = TAU * i / 16
        poly(c, [(0, 0), (math.cos(a) * 1800, math.sin(a) * 1800), (math.cos(a + 0.2) * 1800, math.sin(a + 0.2) * 1800)])
        src(c, (1, 1, 1), 0.06); c.fill()
    c.restore()
    if kind == "title":
        pop = min(1.0, t / 0.35)
        s = 0.6 + 0.4 * (1 - (1 - pop) ** 3) + 0.03 * math.sin(t * 5)
        c.save(); c.translate(540, 700); c.scale(s, s); c.rotate(-0.05)
        text(c, "EMOTIONAL", 0, -40, 130, "Luckiest Guy", hexc("#ff6fa8"), OUT, 18)
        text(c, "EDUCATION", 0, 100, 130, "Luckiest Guy", hexc("#36c9bd"), OUT, 18)
        c.restore()
        heart(c, 540, 470, 60); fs(c, hexc("#ff4f7e"), lw=6)
        a = min(1.0, max(0.0, (t - 0.5) / 0.4))
        rrect(c, 290, 960, 500, 90, 45); src(c, (0, 0, 0), 0.5 * a); c.fill()
        text(c, P.get("part", "PART 1"), 540, 1025, 58, "Luckiest Guy", hexc("#f4c430"), OUT, 6, alpha=a)
        text(c, P.get("subtitle", ""), 540, 1180, 92, "Bangers", (1, 1, 1), OUT, 12, alpha=a)
    elif kind == "tbc":
        a = min(1.0, t / 0.4)
        text(c, "TO BE", 540, 640, 120, "Luckiest Guy", (1, 1, 1), OUT, 16, alpha=a)
        text(c, "CONTINUED...", 540, 790, 120, "Luckiest Guy", (1, 1, 1), OUT, 16, alpha=a)
        b = min(1.0, max(0.0, (t - 0.8) / 0.4))
        text(c, "NEXT:", 540, 1000, 60, "Luckiest Guy", hexc("#f4c430"), OUT, 7, alpha=b)
        text(c, P.get("next", ""), 540, 1110, 90, "Bangers", (1, 1, 1), OUT, 12, alpha=b)
    elif kind == "end":
        a = min(1.0, t / 0.5)
        text(c, "THE END", 540, 760, 150, "Luckiest Guy", (1, 1, 1), OUT, 18, alpha=a)
        heart(c, 540, 960, 70); fs(c, hexc("#ff4f7e"), lw=6)
        b = min(1.0, max(0.0, (t - 0.8) / 0.4))
        text(c, P.get("tag", ""), 540, 1130, 64, "Bangers", hexc("#f4c430"), OUT, 9, alpha=b)
    elif kind == "text":
        a = min(1.0, t / 0.3)
        lines_ = P.get("lines", [])
        y = 860 - (len(lines_) - 1) * 70
        for ln in lines_:
            text(c, ln, 540, y, 96, "Luckiest Guy", (1, 1, 1), OUT, 14, alpha=a)
            y += 140
    actors(0)


SETS = {
    "office": set_office,
    "hallway": set_hallway,
    "stage": set_stage,
    "stands": set_stands,
    "hat": set_hat,
    "clock": set_clock,
    "void": set_void,
    "imagine": set_imagine,
    "card": set_card,
}
