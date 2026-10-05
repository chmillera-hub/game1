"""Character drawings. Every character is drawn front-facing in local coordinates with the
feet at (0, 0) and +y pointing down. State `S` is an attribute-style dict (see engine.State)."""
import math
import cairo
from .draw import (OUT, LW, TAU, hexc, shade, src, ell, rrect, fs, fill, poly, line, hose,
                   bend_point, heart, text, star)
from . import face

# Arm presets: (aLx, aLy, aRx, aRy), normalised to arm length. +x = outward from the body,
# +y = down. L = screen-left arm, R = screen-right arm.
ARMS = {
    "down": (0.22, 0.97, 0.22, 0.97),
    "out": (0.95, 0.15, 0.95, 0.15),
    "up": (0.35, -0.95, 0.35, -0.95),
    "wave": (0.22, 0.97, 0.6, -0.85),
    "shield": (-0.85, -0.95, -0.85, -0.95),
    "shield1": (0.22, 0.97, -0.85, -0.95),
    "point": (0.22, 0.97, 1.05, -0.15),
    "pointL": (1.05, -0.15, 0.22, 0.97),
    "cup": (-0.62, -0.62, -0.62, -0.62),
    "rub": (-0.72, 0.55, -0.72, 0.55),
    "shrug": (0.75, -0.35, 0.75, -0.35),
    "cross": (-0.95, 0.3, -0.95, 0.3),
    "hold": (0.22, 0.97, 0.45, 0.35),
    "holdup": (0.22, 0.97, 0.4, -0.95),
    "flex": (0.95, -0.55, 0.95, -0.55),
    "fists": (0.3, 0.45, 0.3, 0.45),
    "carry": (0.12, -1.08, 0.12, -1.08),
    "grab": (-0.15, 0.35, -0.15, 0.35),
    "chin": (0.22, 0.97, -0.55, -0.6),
    "heart": (-0.62, 0.12, -0.62, 0.12),
    "face": (-0.48, -0.8, -0.48, -0.8),
    "clap": (-0.7, 0.2, -0.7, 0.2),
    "mic": (0.22, 0.97, -0.42, -0.58),
    "table": (0.2, 0.55, 0.2, 0.55),
    "tray": (0.22, 0.97, 0.78, -0.4),
    "hips": (0.12, 0.42, 0.12, 0.42),
    "hug": (-0.5, 0.0, -0.5, 0.0),
    "reach": (0.22, 0.97, 0.9, -0.55),
    "shades": (0.22, 0.97, -0.25, -1.05),
    "sad": (0.1, 1.0, 0.1, 1.0),
    "fistup": (0.22, 0.97, 0.3, -1.0),
    "presentL": (0.95, -0.25, 0.22, 0.97),
    "present": (0.22, 0.97, 0.95, -0.25),
    "shrug1": (0.75, -0.35, 0.22, 0.97),
    "phone": (0.22, 0.97, -0.55, -0.15),
    "dance": (0.9, -0.6, 0.6, 0.6),
}


def arm_vec(S):
    t = S.get("_t", 0.0)
    aLx, aLy, aRx, aRy = S.aLx, S.aLy, S.aRx, S.aRy
    fl = S.flail
    if fl:
        aLx += fl * 0.55 * math.sin(t * 23.0)
        aLy += fl * 0.9 * math.cos(t * 19.0)
        aRx += fl * 0.55 * math.sin(t * 21.0 + 1)
        aRy += fl * 0.9 * math.cos(t * 17.0 + 2)
    if S.waveR:
        aRx += S.waveR * 0.35 * math.sin(t * 14)
    if S.waveL:
        aLx += S.waveL * 0.35 * math.sin(t * 14 + 1)
    if S.rub:
        aLy += S.rub * 0.12 * math.sin(t * 22)
        aRy -= S.rub * 0.12 * math.sin(t * 22)
    if S.clap:
        k = (math.sin(t * 18) + 1) / 2
        aLx += S.clap * 0.45 * k
        aRx += S.clap * 0.45 * k
    if S.gest:
        g = S.gest * S.talk
        aRx += g * 0.25 * math.sin(t * 7)
        aRy -= g * 0.3 * (0.5 + 0.5 * math.sin(t * 5))
    return aLx, aLy, aRx, aRy


def arms_paths(S, sh_x, sh_y, L, bend=0.22, cx=0.0):
    aLx, aLy, aRx, aRy = arm_vec(S)
    hl = (-sh_x - aLx * L, sh_y + aLy * L)
    hr = (sh_x + aRx * L, sh_y + aRy * L)
    el = bend_point(-sh_x, sh_y, hl[0], hl[1], bend * L, cx)
    er = bend_point(sh_x, sh_y, hr[0], hr[1], bend * L, cx)
    return ((-sh_x, sh_y), el, hl), ((sh_x, sh_y), er, hr)


def legs_paths(S, hip_x, hip_y, length, spread=6):
    t = S.get("_t", 0.0)
    out = []
    for side in (-1, 1):
        swing = 0.0
        lift = 0.0
        if S.walk:
            ph = t * 9.0 + (0 if side < 0 else math.pi)
            swing = math.sin(ph) * 0.35 * S.walk
            lift = max(0, math.cos(ph)) * 0.12 * S.walk
        if S.kick:
            ph = t * 26 + (0 if side < 0 else 2.0)
            swing += math.sin(ph) * 0.45 * S.kick
            lift += abs(math.cos(ph)) * 0.2 * S.kick
        fx = side * (hip_x + spread) + swing * length
        fy = hip_y + length * (1 - lift)
        out.append(((side * hip_x, hip_y), (fx, fy)))
    return out


def mitten(c, x, y, r, col, hold=None, flip=1):
    ell(c, x, y, r, r * 0.92)
    fs(c, col)
    # thumb
    ell(c, x - flip * r * 0.75, y - r * 0.35, r * 0.38, r * 0.32)
    fs(c, col, lw=LW * 0.8)


def draw_prop(c, kind, x, y, S, scale=1.0):
    """Hand-held props drawn at the hand position."""
    t = S.get("_t", 0.0)
    if kind == "mic":
        c.save(); c.translate(x, y); c.rotate(-0.5)
        rrect(c, -9, -10, 18, 70, 8); fs(c, hexc("#333344"))
        ell(c, 0, -22, 20, 22); fs(c, hexc("#9aa0ad"))
        for i in range(-2, 3):
            line(c, -14, -22 + i * 6, 14, -22 + i * 6, shade(hexc("#9aa0ad"), 0.6), 2)
        c.restore()
    elif kind == "hat":
        c.save(); c.translate(x, y - 30)
        ell(c, 0, 40, 95, 22); fs(c, hexc("#1d1d26"))
        rrect(c, -60, -70, 120, 112, 14); fs(c, hexc("#262632"))
        c.rectangle(-60, 10, 120, 22); fs(c, hexc("#c4283a"))
        ell(c, 0, -70, 60, 14); fs(c, hexc("#33333f"))
        c.restore()
    elif kind == "slip":
        c.save(); c.translate(x, y - 25); c.rotate(-0.15)
        rrect(c, -55, -30, 110, 60, 6); fs(c, (1, 1, 0.94), lw=4)
        text(c, S.get("slip_text", "?"), 0, 8, 22, "Luckiest Guy", OUT)
        c.restore()
    elif kind == "shades":
        c.save(); c.translate(x, y - 16)
        rrect(c, -50, -12, 100, 26, 10); fs(c, hexc("#111116"))
        c.restore()
    elif kind == "phone":
        c.save(); c.translate(x, y - 20); c.rotate(0.15)
        rrect(c, -18, -34, 36, 66, 7); fs(c, hexc("#22222a"))
        rrect(c, -13, -27, 26, 50, 3); fill(c, hexc("#6fd0ff"))
        c.restore()
    elif kind == "tray":
        c.save(); c.translate(x, y - 12)
        ell(c, 0, 0, 80, 15); fs(c, hexc("#c9ced6"))
        ell(c, 0, -32, 34, 30, math.pi, TAU); c.close_path(); fs(c, hexc("#dfe3ea"))
        ell(c, 0, -64, 7, 7); fs(c, hexc("#dfe3ea"))
        c.restore()
    elif kind == "menu":
        c.save(); c.translate(x, y - 30); c.rotate(-0.1)
        rrect(c, -40, -55, 80, 110, 6); fs(c, hexc("#7a2230"))
        text(c, "MENU", 0, -20, 20, "Luckiest Guy", hexc("#f5d76e"))
        c.restore()
    elif kind == "paper":
        c.save(); c.translate(x, y - 30); c.rotate(0.1)
        rrect(c, -45, -60, 90, 120, 4); fs(c, (1, 1, 1), lw=4)
        for i in range(5):
            line(c, -30, -35 + i * 18, 30, -35 + i * 18, (0.6, 0.6, 0.7), 3)
        c.restore()
    elif kind == "towel":
        pass


def costume_front(c, S, neck_x, neck_y, w):
    cos = S.costume
    if cos == "waiter":
        # bow tie
        c.move_to(neck_x, neck_y)
        c.line_to(neck_x - w * 0.22, neck_y - w * 0.12)
        c.line_to(neck_x - w * 0.22, neck_y + w * 0.12)
        c.close_path()
        c.move_to(neck_x, neck_y)
        c.line_to(neck_x + w * 0.22, neck_y - w * 0.12)
        c.line_to(neck_x + w * 0.22, neck_y + w * 0.12)
        c.close_path()
        fs(c, hexc("#111116"), lw=3)
        ell(c, neck_x, neck_y, w * 0.06, w * 0.06); fs(c, hexc("#111116"), lw=3)
    elif cos == "bib":
        c.move_to(neck_x - w * 0.35, neck_y - 6)
        c.line_to(neck_x + w * 0.35, neck_y - 6)
        c.line_to(neck_x + w * 0.25, neck_y + w * 0.6)
        c.line_to(neck_x - w * 0.25, neck_y + w * 0.6)
        c.close_path()
        fs(c, (1, 1, 1), lw=4)
        for i in range(3):
            line(c, neck_x - w * 0.2, neck_y + 12 + i * w * 0.15, neck_x + w * 0.2, neck_y + 12 + i * w * 0.15,
                 hexc("#e04050"), 3)


def costume_face(c, S, cx, eye_y, mouth_y, sep):
    cos = S.costume
    if cos == "posh":
        # monocle on screen-right eye + curly mustache
        ell(c, cx + sep, eye_y, sep * 0.7, sep * 0.75)
        src(c, hexc("#d4af37")); c.set_line_width(4); c.stroke()
        line(c, cx + sep * 1.6, eye_y + sep * 0.3, cx + sep * 1.9, eye_y + sep * 2.4, hexc("#d4af37"), 2)
    if cos in ("posh", "mustache"):
        y = (eye_y + mouth_y) / 2 + sep * 0.25
        for s in (-1, 1):
            c.move_to(cx, y)
            c.curve_to(cx + s * sep * 0.6, y - sep * 0.35, cx + s * sep * 1.1, y + sep * 0.2,
                       cx + s * sep * 1.3, y - sep * 0.25)
            c.curve_to(cx + s * sep * 1.0, y + sep * 0.45, cx + s * sep * 0.5, y + sep * 0.15, cx, y + sep * 0.15)
            c.close_path()
            fs(c, hexc("#3a2a1a"), lw=3)


# --------------------------------------------------------------------------------------
# CARTMAN (original take: rubber-hose limbs, outlined, shaded — not the show's paper style)
# --------------------------------------------------------------------------------------
C_JACKET = hexc("#d8382b")
C_MITTEN = hexc("#f4c430")
C_PANTS = hexc("#7a5434")
C_HAT = hexc("#25b3ad")
C_BRIM = hexc("#f4c430")
C_SKIN = hexc("#f6d2ae")
C_SHOE = hexc("#2a2a33")


def cartman(c, S):
    t = S.get("_t", 0.0)
    puff = S.puff  # 0..1 "fluffed up"
    bw = 102 * (1 + 0.12 * puff)
    # legs
    if S.sit:
        for side in (-1, 1):
            ell(c, side * 42, -18, 30, 26)
            fs(c, C_PANTS)
            ell(c, side * 48, 6, 26, 15)
            fs(c, C_SHOE)
    else:
        legs = legs_paths(S, 40, -44, 26)
        hose(c, [[(hx, hy), (fx, fy)] for (hx, hy), (fx, fy) in legs], 40, C_PANTS)
        for (hx, hy), (fx, fy) in legs:
            ell(c, fx + (6 if fx > 0 else -6), fy + 9, 32, 15)
            fs(c, C_SHOE)
    # body
    ell(c, 0, -112, bw, 94 * (1 + 0.05 * puff))
    fs(c, C_JACKET)
    # shading
    c.save(); ell(c, 0, -112, bw, 94); c.clip()
    ell(c, bw * 0.45, -80, bw * 0.7, 80); src(c, (0, 0, 0), 0.10); c.fill()
    c.restore()
    line(c, 0, -190, 0, -30, shade(C_JACKET, 0.55), 4)
    for yy in (-150, -110, -70):
        ell(c, -12, yy, 5, 5); fill(c, shade(C_JACKET, 0.5))
    costume_front(c, S, 0, -172, 120)
    # head
    hy = -238 - 3 * S.talk
    ell(c, -90, hy + 8, 14, 18); fs(c, C_SKIN)  # ears
    ell(c, 90, hy + 8, 14, 18); fs(c, C_SKIN)
    ell(c, 0, hy, 92, 80)
    fs(c, C_SKIN)
    # chin fold
    c.move_to(-34, hy + 66); c.curve_to(-14, hy + 76, 14, hy + 76, 34, hy + 66)
    src(c, shade(C_SKIN, 0.75)); c.set_line_width(3); c.stroke()
    # hair tufts
    for side in (-1, 1):
        c.move_to(side * 82, hy - 30)
        c.line_to(side * 92, hy - 8)
        c.line_to(side * 70, hy - 22)
        c.close_path()
        fs(c, hexc("#6b4428"), lw=3)
    # hat
    ell(c, 0, hy - 24, 90, 64, math.pi, TAU)
    c.close_path()
    fs(c, C_HAT)
    c.save(); ell(c, 0, hy - 24, 90, 64, math.pi, TAU); c.close_path(); c.clip()
    ell(c, 40, hy - 50, 55, 40); src(c, (0, 0, 0), 0.10); c.fill()
    c.restore()
    rrect(c, -96, hy - 38, 192, 26, 12)
    fs(c, C_BRIM)
    ell(c, 0, hy - 92, 19, 17)
    fs(c, C_BRIM)
    # face
    ey = hy + 10
    for side in (-1, 1):
        face.eye(c, side * 30, ey, 25, 28, S, side, C_SKIN, iris=hexc("#5a8fd8"))
    face.brows(c, 0, ey - 40, 32, 34, S)
    ell(c, 0, ey + 30, 10, 8); fs(c, hexc("#f0a49a"), lw=3)
    if S.blush or True:
        a = 0.35 + 0.5 * S.blush
        ell(c, -58, ey + 34, 17, 10); src(c, hexc("#ff8a8a"), a); c.fill()
        ell(c, 58, ey + 34, 17, 10); src(c, hexc("#ff8a8a"), a); c.fill()
    face.mouth(c, 0, ey + 52, 54, S)
    costume_face(c, S, 0, ey, ey + 52, 30)
    if S.sweat:
        face.sweat(c, 78, hy - 30, S.sweat, t)
    if S.tears:
        face.tears(c, -30, ey + 22, S.tears, t)
        face.tears(c, 30, ey + 22, S.tears, t + 0.5)
    # arms (after head so shielding covers the face)
    l, r = arms_paths(S, 86, -150, 92, cx=0)
    hose(c, [list(l), list(r)], 32, C_JACKET)
    mitten(c, l[2][0], l[2][1], 21, C_MITTEN, flip=-1)
    mitten(c, r[2][0], r[2][1], 21, C_MITTEN, flip=1)
    if S.hold:
        draw_prop(c, S.hold, r[2][0], r[2][1], S)


# --------------------------------------------------------------------------------------
# Generic big adult builder used for PC Principal, Emotional Chad, gym bros
# --------------------------------------------------------------------------------------
def adult(c, S, cfg):
    t = S.get("_t", 0.0)
    skin = cfg["skin"]
    shirt = cfg["shirt"]
    pants = cfg["pants"]
    shoe = cfg["shoe"]
    sw = cfg["shoulder"]  # half shoulder width
    ww = cfg["waist"]
    hip_y = -cfg["leg"]
    sh_y = hip_y - cfg["torso"]
    head_cy = sh_y - cfg["neck"] - cfg["head_ry"]
    puff = S.puff
    # legs
    if S.sit:
        for side in (-1, 1):
            hose(c, [[(side * ww * 0.55, hip_y), (side * ww * 0.7, hip_y + 30), (side * ww * 0.75, hip_y + 110)]],
                 cfg["legw"], pants)
            ell(c, side * ww * 0.8, hip_y + 118, 34, 15); fs(c, shoe)
    else:
        legs = legs_paths(S, ww * 0.55, hip_y, cfg["leg"] - 34, spread=4)
        hose(c, [[(hx, hy), (fx, fy)] for (hx, hy), (fx, fy) in legs], cfg["legw"], pants)
        if cfg.get("shorts"):
            for (hx, hy), (fx, fy) in legs:
                mx, my = hx + (fx - hx) * 0.45, hy + (fy - hy) * 0.45
                hose(c, [[(mx, my), (fx, fy)]], cfg["legw"] * 0.78, skin)
        for (hx, hy), (fx, fy) in legs:
            ell(c, fx + (10 if fx > 0 else -10), fy + 18, 38, 17); fs(c, shoe)
    # torso (V)
    sw2 = sw * (1 + 0.08 * puff)
    c.move_to(-ww, hip_y + 6)
    c.line_to(ww, hip_y + 6)
    c.curve_to(ww + 10, hip_y - cfg["torso"] * 0.5, sw2 + 10, sh_y + 40, sw2, sh_y + 10)
    c.curve_to(sw2 - 10, sh_y - 18, sw2 * 0.4, sh_y - 22, 0, sh_y - 22)
    c.curve_to(-sw2 * 0.4, sh_y - 22, -sw2 + 10, sh_y - 18, -sw2, sh_y + 10)
    c.curve_to(-sw2 - 10, sh_y + 40, -ww - 10, hip_y - cfg["torso"] * 0.5, -ww, hip_y + 6)
    c.close_path()
    torso_path = c.copy_path()
    if cfg.get("tank"):
        fs(c, skin)
        c.save(); c.append_path(torso_path); c.clip()
        strap = cfg.get("strap", 0.42)
        c.move_to(-ww - 20, hip_y + 10)
        c.line_to(ww + 20, hip_y + 10)
        c.line_to(sw2 * 0.95, sh_y + 70)
        c.line_to(sw2 * strap, sh_y - 30)
        c.line_to(sw2 * (strap - 0.18), sh_y - 30)
        c.curve_to(sw2 * 0.15, sh_y + 60, -sw2 * 0.15, sh_y + 60, -sw2 * (strap - 0.18), sh_y - 30)
        c.line_to(-sw2 * strap, sh_y - 30)
        c.line_to(-sw2 * 0.95, sh_y + 70)
        c.close_path()
        fs(c, shirt, lw=LW * 0.8)
        # chest definition
        c.move_to(-sw2 * 0.45, sh_y + 75); c.curve_to(-sw2 * 0.2, sh_y + 95, -5, sh_y + 90, 0, sh_y + 70)
        c.move_to(sw2 * 0.45, sh_y + 75); c.curve_to(sw2 * 0.2, sh_y + 95, 5, sh_y + 90, 0, sh_y + 70)
        src(c, shade(shirt, 0.6)); c.set_line_width(3); c.stroke()
        c.restore()
        c.append_path(torso_path); src(c, OUT); c.set_line_width(LW); c.stroke()
    else:
        fs(c, shirt)
        c.save(); c.append_path(torso_path); c.clip()
        c.rectangle(sw * 0.3, sh_y - 30, sw * 1.2, cfg["torso"] + 60); src(c, (0, 0, 0), 0.08); c.fill()
        c.restore()
    # waistband / belt
    if cfg.get("belt"):
        c.rectangle(-ww - 2, hip_y - 14, ww * 2 + 4, 22); fs(c, cfg["belt"], lw=4)
        rrect(c, -14, hip_y - 16, 28, 26, 4); fs(c, hexc("#d9b44a"), lw=3)
    # emblem
    if cfg.get("emblem") == "heart":
        heart(c, 0, sh_y + 120, 34); fs(c, (1, 1, 1), lw=4)
    elif cfg.get("emblem") == "pc":
        ell(c, -sw * 0.45, sh_y + 70, 26, 26); fs(c, (1, 1, 1), lw=4)
        text(c, "PC", -sw * 0.45, sh_y + 79, 24, "Luckiest Guy", hexc("#2a5fb0"))
    if cfg.get("collar"):
        for s in (-1, 1):
            poly(c, [(0, sh_y - 16), (s * 46, sh_y - 26), (s * 40, sh_y + 22)])
            fs(c, cfg["collar"], lw=4)
        line(c, 0, sh_y - 10, 0, sh_y + 60, shade(shirt, 0.6), 3)
    # neck
    nw = cfg["neckw"]
    c.rectangle(-nw, sh_y - cfg["neck"] - 22, nw * 2, cfg["neck"] + 24)
    fs(c, skin)
    c.rectangle(-nw + 3, sh_y - 20, nw * 2 - 6, 14); fill(c, skin)
    if cfg.get("collar"):
        for s in (-1, 1):
            poly(c, [(0, sh_y - 8), (s * 46, sh_y - 24), (s * 38, sh_y + 20)])
            fs(c, cfg["collar"], lw=4)
    costume_front(c, S, 0, sh_y - 4, 110)
    # head
    hry, hrx = cfg["head_ry"], cfg["head_rx"]
    hy = head_cy - 3 * S.talk
    ex = hrx * 0.42
    ey = hy - hry * 0.02
    for s in (-1, 1):
        ell(c, s * hrx, hy + 6, 13, 19); fs(c, skin)
    if cfg.get("square"):
        rrect(c, -hrx, hy - hry, hrx * 2, hry * 2, hrx * 0.55)
    else:
        ell(c, 0, hy, hrx, hry)
    fs(c, skin)
    hair = cfg.get("hair")
    if hair:
        hair(c, hy, hrx, hry, S)
    # beard / mustache
    if cfg.get("beard"):
        c.move_to(-hrx * 0.98, hy + hry * 0.0)
        c.curve_to(-hrx * 0.9, hy + hry * 1.25, hrx * 0.9, hy + hry * 1.25, hrx * 0.98, hy + hry * 0.0)
        c.curve_to(hrx * 0.6, hy + hry * 0.5, -hrx * 0.6, hy + hry * 0.5, -hrx * 0.98, hy)
        c.close_path()
        fs(c, cfg["beard"], lw=4)
    # eyes
    if cfg.get("crowsfeet"):
        for s in (-1, 1):
            for k in (-1, 0, 1):
                line(c, s * (ex + hrx * 0.28), ey + k * 7, s * (ex + hrx * 0.42), ey + k * 11, shade(skin, 0.7), 2.5)
    for s in (-1, 1):
        face.eye(c, s * ex, ey, hrx * 0.25, hry * 0.22, S, s, skin, iris=cfg.get("iris"))
    face.brows(c, 0, ey - hry * 0.3, ex, hrx * 0.42, S, col=cfg.get("brow", OUT))
    # nose
    c.move_to(0, ey + 8); c.curve_to(-12, ey + 36, -6, ey + 40, 8, ey + 38)
    src(c, shade(skin, 0.65)); c.set_line_width(4); c.stroke()
    my = hy + hry * 0.55
    if cfg.get("mustache"):
        for s in (-1, 1):
            c.move_to(0, my - 16)
            c.curve_to(s * 30, my - 30, s * 50, my - 10, s * 56, my + 18)
            c.curve_to(s * 40, my - 4, s * 20, my - 6, 0, my - 6)
            c.close_path()
            fs(c, cfg["mustache"], lw=3)
    face.mouth(c, 0, my, hrx * 0.62, S)
    costume_face(c, S, 0, ey, my, ex)
    if cfg.get("cleft"):
        line(c, 0, hy + hry * 0.85, 0, hy + hry * 0.95, shade(skin, 0.6), 3)
    if S.blush:
        for s in (-1, 1):
            ell(c, s * hrx * 0.62, ey + hry * 0.38, 16, 9); src(c, hexc("#ff8a8a"), 0.6 * S.blush); c.fill()
    # sunglasses
    if cfg.get("shades_ok"):
        sh = S.shades
        if sh > 0:
            lift = (1 - sh)
            gy = ey - lift * 150
            gx = lift * hrx * 1.2
            c.save(); c.translate(gx, gy); c.rotate(-lift * 0.5)
            c.move_to(-hrx * 1.02, -hry * 0.16)
            c.line_to(hrx * 1.02, -hry * 0.16)
            c.curve_to(hrx * 1.0, hry * 0.2, hrx * 0.3, hry * 0.28, hrx * 0.08, hry * 0.08)
            c.curve_to(0, hry * 0.04, 0, hry * 0.04, -hrx * 0.08, hry * 0.08)
            c.curve_to(-hrx * 0.3, hry * 0.28, -hrx * 1.0, hry * 0.2, -hrx * 1.02, -hry * 0.16)
            c.close_path()
            fs(c, hexc("#101015"))
            glint = S.glint
            if glint:
                c.save()
                c.move_to(-hrx * 0.7 + glint * hrx * 1.2, -hry * 0.12)
                c.line_to(-hrx * 0.55 + glint * hrx * 1.2, -hry * 0.12)
                c.line_to(-hrx * 0.75 + glint * hrx * 1.2, hry * 0.18)
                c.line_to(-hrx * 0.9 + glint * hrx * 1.2, hry * 0.18)
                c.close_path()
                src(c, (1, 1, 1), 0.85); c.fill()
                c.restore()
            else:
                poly(c, [(-hrx * 0.75, -hry * 0.1), (-hrx * 0.6, -hry * 0.1), (-hrx * 0.75, hry * 0.12), (-hrx * 0.88, hry * 0.12)])
                src(c, (1, 1, 1), 0.35); c.fill()
            c.restore()
    if S.sweat:
        face.sweat(c, hrx * 0.9, hy - hry * 0.6, S.sweat, t)
    if S.tears:
        face.tears(c, -ex, ey + hry * 0.2, S.tears, t)
        face.tears(c, ex, ey + hry * 0.2, S.tears, t + 0.4)
    if S.sparkle:
        for i, (dx, dy) in enumerate([(-hrx * 1.4, -hry * 0.8), (hrx * 1.5, -hry * 0.4), (hrx * 1.2, hry * 0.9)]):
            k = 0.6 + 0.4 * math.sin(t * 6 + i * 2)
            star(c, dx, dy, 18 * k * S.sparkle, 6 * k * S.sparkle, 4)
            fs(c, hexc("#fff3a0"), lw=3)
    # arms
    L = cfg["arm"]
    l, r = arms_paths(S, sw2 - cfg["armw"] * 0.25, sh_y + 22, L, bend=0.18)
    sleeve = cfg.get("sleeve")
    segs = []
    for (p0, el, h) in (l, r):
        segs.append(([p0, el], cfg["armw"] * 1.08, skin))
        segs.append(([el, h], cfg["armw"] * 0.88, skin))
    hose(c, segs, cfg["armw"], skin)
    # biceps bulge
    for (p0, el, h) in (l, r):
        bx, by = (p0[0] * 0.55 + el[0] * 0.45), (p0[1] * 0.55 + el[1] * 0.45)
        ell(c, bx, by, cfg["armw"] * 0.62, cfg["armw"] * 0.58)
        fill(c, skin)
    if sleeve:
        for (p0, el, h) in (l, r):
            ell(c, p0[0], p0[1] + 4, cfg["armw"] * 0.78, cfg["armw"] * 0.7)
            fs(c, sleeve)
    if cfg.get("wristband"):
        for (p0, el, h) in (l, r):
            wx, wy = el[0] + (h[0] - el[0]) * 0.72, el[1] + (h[1] - el[1]) * 0.72
            ell(c, wx, wy, cfg["armw"] * 0.55, cfg["armw"] * 0.5)
            fs(c, cfg["wristband"], lw=4)
    for (p0, el, h) in (l, r):
        ell(c, h[0], h[1], cfg["armw"] * 0.58, cfg["armw"] * 0.55)
        fs(c, skin)
    if S.hold:
        draw_prop(c, S.hold, r[2][0], r[2][1], S)
    if cfg.get("shades_ok") and S.shades <= 0 and S.holdshades:
        draw_prop(c, "shades", r[2][0], r[2][1] - 10, S)


def _pc_hair(c, hy, hrx, hry, S):
    rrect(c, -hrx * 0.98, hy - hry - 26, hrx * 1.96, 48, 10)
    fs(c, hexc("#efd36a"))
    for i in range(-5, 6):
        line(c, i * hrx * 0.16, hy - hry - 18, i * hrx * 0.16 + 3, hy - hry + 8, hexc("#c9a843"), 2.5)


def _chad_hair(c, hy, hrx, hry, S):
    col = hexc("#7a4a2a")
    # man bun
    ell(c, hrx * 0.25, hy - hry - 18, 26, 22); fs(c, col)
    c.move_to(-hrx * 1.02, hy - hry * 0.15)
    c.curve_to(-hrx * 1.25, hy - hry * 1.3, hrx * 0.6, hy - hry * 1.55, hrx * 1.05, hy - hry * 0.45)
    c.curve_to(hrx * 0.95, hy - hry * 0.25, hrx * 0.6, hy - hry * 0.55, hrx * 0.1, hy - hry * 0.55)
    c.curve_to(-hrx * 0.4, hy - hry * 0.55, -hrx * 0.75, hy - hry * 0.4, -hrx * 1.02, hy - hry * 0.15)
    c.close_path()
    fs(c, col)
    # swoop strand
    c.move_to(-hrx * 0.2, hy - hry * 0.6)
    c.curve_to(-hrx * 0.6, hy - hry * 0.3, -hrx * 0.7, hy - hry * 0.1, -hrx * 0.55, hy + hry * 0.05)
    src(c, col); c.set_line_width(10); c.stroke()
    # headband
    c.move_to(-hrx * 1.0, hy - hry * 0.42)
    c.curve_to(-hrx * 0.4, hy - hry * 0.62, hrx * 0.4, hy - hry * 0.62, hrx * 1.0, hy - hry * 0.42)
    src(c, OUT); c.set_line_width(22); c.stroke()
    c.move_to(-hrx * 1.0, hy - hry * 0.42)
    c.curve_to(-hrx * 0.4, hy - hry * 0.62, hrx * 0.4, hy - hry * 0.62, hrx * 1.0, hy - hry * 0.42)
    src(c, hexc("#36c9bd")); c.set_line_width(14); c.stroke()


def _broA_hair(c, hy, hrx, hry, S):
    # backwards cap
    ell(c, 0, hy - hry * 0.35, hrx * 1.04, hry * 0.82, math.pi, TAU); c.close_path()
    fs(c, hexc("#c62f2f"))
    rrect(c, -hrx * 0.35, hy - hry * 0.42, hrx * 0.7, 20, 8); fs(c, hexc("#a52626"), lw=3)
    rrect(c, -hrx * 1.05, hy - hry * 0.45, hrx * 2.1, 18, 8); fs(c, hexc("#a52626"), lw=4)


def _broB_hair(c, hy, hrx, hry, S):
    ell(c, -hrx * 0.35, hy - hry * 0.65, hrx * 0.3, hry * 0.15)
    src(c, (1, 1, 1), 0.45); c.fill()
    for s in (-1, 1):
        ell(c, s * hrx * 0.92, hy - hry * 0.15, hrx * 0.16, hry * 0.3)
        fs(c, hexc("#3a2a20"), lw=3)


PC_CFG = dict(skin=hexc("#f1b98d"), shirt=hexc("#6fb7e9"), pants=hexc("#cfb281"), shoe=hexc("#f4f4f4"),
              shoulder=128, waist=74, leg=210, torso=215, neck=26, neckw=38, head_rx=64, head_ry=68,
              legw=54, armw=48, arm=168, square=True, hair=_pc_hair, collar=(1, 1, 1),
              belt=hexc("#6b4a2b"), emblem="pc", sleeve=hexc("#6fb7e9"), shades_ok=True, cleft=True,
              iris=hexc("#5aa8e6"))

CHAD_CFG = dict(skin=hexc("#d89a72"), shirt=hexc("#ff6fa8"), pants=hexc("#8d93a3"), shoe=hexc("#36c9bd"),
                shoulder=112, waist=64, leg=222, torso=205, neck=24, neckw=30, head_rx=58, head_ry=70,
                legw=48, armw=40, arm=164, hair=_chad_hair, tank=True, emblem="heart",
                wristband=hexc("#36c9bd"), iris=hexc("#7b5a3a"))

BRO_A_CFG = dict(skin=hexc("#f0bf98"), shirt=hexc("#9aa0aa"), pants=hexc("#24242c"), shoe=hexc("#e8e8e8"),
                 shoulder=150, waist=80, leg=220, torso=225, neck=30, neckw=46, head_rx=62, head_ry=70,
                 legw=62, armw=60, arm=176, hair=_broA_hair, tank=True, strap=0.38, beard=hexc("#5a3a22"),
                 crowsfeet=True, shorts=True, iris=hexc("#6b8a5a"))

BRO_B_CFG = dict(skin=hexc("#b97a52"), shirt=hexc("#22222a"), pants=hexc("#c63a3a"), shoe=hexc("#22222a"),
                 shoulder=152, waist=82, leg=218, torso=228, neck=32, neckw=48, head_rx=60, head_ry=72,
                 legw=62, armw=60, arm=178, hair=_broB_hair, tank=True, strap=0.38,
                 mustache=hexc("#3a2a20"), crowsfeet=True, shorts=True, iris=hexc("#4a3020"))


def pc(c, S):
    adult(c, S, PC_CFG)


def chad(c, S):
    adult(c, S, CHAD_CFG)


def broA(c, S):
    adult(c, S, BRO_A_CFG)


def broB(c, S):
    adult(c, S, BRO_B_CFG)


# --------------------------------------------------------------------------------------
# Generic kids (friends, heckler, crowd)
# --------------------------------------------------------------------------------------
def kid(c, S, look):
    t = S.get("_t", 0.0)
    skin = look.get("skin", hexc("#f3cfa8"))
    coat = look.get("coat", hexc("#4a7fd0"))
    pants = look.get("pants", hexc("#3a3a55"))
    hairc = look.get("hairc", hexc("#4a3020"))
    style = look.get("hair", "short")
    if not S.seated:
        if S.sit:
            for side in (-1, 1):
                ell(c, side * 32, -14, 24, 20); fs(c, pants)
        else:
            legs = legs_paths(S, 30, -36, 22)
            hose(c, [[(hx, hy), (fx, fy)] for (hx, hy), (fx, fy) in legs], 32, pants)
            for (hx, hy), (fx, fy) in legs:
                ell(c, fx + (5 if fx > 0 else -5), fy + 8, 25, 12); fs(c, C_SHOE)
    ell(c, 0, -96, 74, 70)
    fs(c, coat)
    c.save(); ell(c, 0, -96, 74, 70); c.clip()
    ell(c, 40, -70, 50, 60); src(c, (0, 0, 0), 0.10); c.fill(); c.restore()
    if look.get("stripe"):
        line(c, -60, -110, 60, -110, look["stripe"], 10)
    hy = -205 - 2 * S.talk
    if style == "pigtails":
        for s in (-1, 1):
            ell(c, s * 80, hy + 10, 22, 30); fs(c, hairc)
    if style == "afro":
        ell(c, 0, hy - 20, 86, 72); fs(c, hairc)
    ell(c, 0, hy, 70, 64)
    fs(c, skin)
    if style == "short":
        ell(c, 0, hy - 30, 70, 38, math.pi, TAU); c.close_path(); fs(c, hairc)
    elif style == "spiky":
        pts = []
        for i in range(9):
            a = math.pi + math.pi * i / 8
            r = 76 if i % 2 else 60
            pts.append((math.cos(a) * r, hy - 20 + math.sin(a) * r * 0.8))
        poly(c, pts); fs(c, hairc)
    elif style in ("pigtails", "bob"):
        ell(c, 0, hy - 18, 72, 50, math.pi, TAU); c.close_path(); fs(c, hairc)
        if style == "bob":
            for s in (-1, 1):
                rrect(c, s * 70 - 14, hy - 24, 28, 60, 12); fs(c, hairc)
    elif style == "cap":
        ell(c, 0, hy - 26, 72, 44, math.pi, TAU); c.close_path(); fs(c, look.get("capc", hexc("#2f7d3a")))
        # backwards brim
        rrect(c, -40, hy - 34, 80, 16, 6); fs(c, shade(look.get("capc", hexc("#2f7d3a")), 0.7), lw=3)
    elif style == "beanie":
        ell(c, 0, hy - 22, 72, 52, math.pi, TAU); c.close_path(); fs(c, look.get("capc", hexc("#8a3fc0")))
        rrect(c, -74, hy - 30, 148, 18, 8); fs(c, shade(look.get("capc", hexc("#8a3fc0")), 0.75), lw=3)
    ey = hy + 6
    for s in (-1, 1):
        face.eye(c, s * 24, ey, 18, 21, S, s, skin, iris=hexc("#6a4a2a"))
    face.brows(c, 0, ey - 30, 25, 26, S)
    if look.get("glasses"):
        for s in (-1, 1):
            ell(c, s * 24, ey, 24, 24)
            src(c, OUT); c.set_line_width(4); c.stroke()
        line(c, -2, ey, 2, ey, OUT, 4)
    face.mouth(c, 0, ey + 36, 40, S)
    if S.sweat:
        face.sweat(c, 60, hy - 30, S.sweat, t, 11)
    l, r = arms_paths(S, 62, -130, 70)
    hose(c, [list(l), list(r)], 24, coat)
    for p in (l[2], r[2]):
        ell(c, p[0], p[1], 15, 14); fs(c, skin)
    if S.hold:
        draw_prop(c, S.hold, r[2][0], r[2][1], S)


KID_LOOKS = {
    "friend1": dict(coat=hexc("#8b4fd0"), hair="pigtails", hairc=hexc("#2a1a12"), skin=hexc("#c68a62")),
    "friend2": dict(coat=hexc("#3f9e5a"), hair="short", hairc=hexc("#d9a440"), glasses=True),
    "heckler": dict(coat=hexc("#f08a24"), hair="cap", capc=hexc("#3050b0"), hairc=hexc("#3a2a1a"),
                    skin=hexc("#f0c8a0"), stripe=hexc("#ffffff")),
    "hecklerpal": dict(coat=hexc("#606a7a"), hair="spiky", hairc=hexc("#202020")),
}


def slug_cartman(c, S):
    """Imagined 'little slug' Cartman (green, slimy, still wearing the beanie)."""
    t = S.get("_t", 0.0)
    wob = math.sin(t * 4) * 6
    c.move_to(-170, 0)
    c.curve_to(-170, -70, -60, -60 + wob, 20, -80)
    c.curve_to(70, -200, 170, -190, 170, -110)
    c.curve_to(175, -40, 120, 0, 60, 0)
    c.close_path()
    fs(c, hexc("#9ccc52"))
    ell(c, -60, 4, 120, 10); src(c, (0.7, 1, 0.6), 0.5); c.fill()
    # eye stalks
    for s in (-1, 1):
        x0 = 110 + s * 26
        line(c, x0, -170, x0 + s * 20, -250, OUT, 14)
        line(c, x0, -170, x0 + s * 20, -250, hexc("#9ccc52"), 8)
        ell(c, x0 + s * 20, -258, 18, 18); fs(c, (1, 1, 1))
        ell(c, x0 + s * 20 + 3, -256, 8, 8); fill(c, OUT)
    # tiny beanie
    ell(c, 110, -190, 44, 30, math.pi, TAU); c.close_path(); fs(c, C_HAT)
    rrect(c, 64, -198, 92, 14, 6); fs(c, C_BRIM, lw=3)
    ell(c, 110, -224, 9, 8); fs(c, C_BRIM, lw=3)
    S2 = dict(S)
    face.mouth(c, 130, -120, 40, S)


DRAWERS = {
    "cartman": cartman,
    "pc": pc,
    "chad": chad,
    "broA": broA,
    "broB": broB,
    "slug": slug_cartman,
}


def draw_actor(c, kind, S):
    if kind in DRAWERS:
        DRAWERS[kind](c, S)
    elif kind in KID_LOOKS:
        kid(c, S, KID_LOOKS[kind])
    elif kind.startswith("kid:"):
        kid(c, S, S.get("look") or {})
    else:
        raise KeyError(kind)
