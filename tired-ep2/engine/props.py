"""Props for TIREDNESS (see API_sets.md).

Every prop is `name(ctx, x, y, s=1.0, ...)`, drawn around a documented ANCHOR
point (x, y) at scale s (s=1 matches a ~1000 px tall adult). All props are
deterministic (no unseeded randomness) and cheap enough to draw live; the
heavier ones (van body) cache their static parts through core.cached.

The module also holds the small shared drawing helpers used by sets.py
(fs, rect, ell, polyf, blob, line, spaced_text) and the HushCorp logo.
"""
import math
import cairocffi as cairo
from engine import core
from engine.core import PAL, hexc, mixc, clamp, lerp, hash01, noise1

INK = PAL["ink"]
TAU = math.pi * 2


# ----------------------------------------------------------------------------
# shared drawing helpers
# ----------------------------------------------------------------------------
def fs(ctx, fc, lw=4.0, sc=INK):
    """Fill (fc) and stroke (sc, lw) the current path, then clear it."""
    if fc is not None:
        core.fill(ctx, fc, preserve=True)
    if lw and sc is not None:
        core.stroke(ctx, sc, lw, preserve=True)
    ctx.new_path()


def rect(ctx, x, y, w, h, fc, lw=4.0, r=0, sc=INK):
    if r:
        core.rrect(ctx, x, y, w, h, r)
    else:
        ctx.rectangle(x, y, w, h)
    fs(ctx, fc, lw, sc)


def ell(ctx, cx, cy, rx, ry, fc, lw=4.0, sc=INK, rot=0.0):
    core.ellipse(ctx, cx, cy, rx, ry, rot)
    fs(ctx, fc, lw, sc)


def polyf(ctx, pts, fc, lw=4.0, sc=INK):
    core.poly(ctx, pts)
    fs(ctx, fc, lw, sc)


def blob(ctx, pts, fc, lw=4.0, sc=INK, tension=0.5):
    core.smooth_path(ctx, pts, closed=True, tension=tension)
    fs(ctx, fc, lw, sc)


def line(ctx, pts, c=INK, lw=4.0, cap="round"):
    core.poly(ctx, pts, closed=False)
    core.stroke(ctx, c, lw, cap=cap)


def curve(ctx, pts, c=INK, lw=4.0, tension=0.5):
    core.smooth_path(ctx, pts, closed=False, tension=tension)
    core.stroke(ctx, c, lw)


def spaced_text(ctx, s, x, y, size, color, font="ui", spacing=0.45, align="center"):
    """Text with wide letter spacing (spacing = extra advance in em). y = baseline."""
    core.set_font(ctx, font, size)
    advs = [ctx.text_extents(ch)[4] for ch in s]
    gap = spacing * size
    total = sum(advs) + gap * (len(s) - 1)
    xx = x - {"left": 0, "center": total / 2, "right": total}[align]
    core.set_color(ctx, color)
    for ch, a in zip(s, advs):
        ctx.move_to(xx, y)
        ctx.show_text(ch)
        xx += a + gap
    return total


def keyhole_path(ctx, x, y, r):
    """Stylised keyhole centred at (x, y), fitting a circle of radius r."""
    hr = r * 0.36
    cy = y - r * 0.28
    ctx.new_sub_path()
    ctx.arc(x, cy, hr, math.radians(120), math.radians(60) + TAU)
    ctx.line_to(x + r * 0.30, y + r * 0.62)
    ctx.curve_to(x + r * 0.30, y + r * 0.70, x - r * 0.30, y + r * 0.70, x - r * 0.30, y + r * 0.62)
    ctx.close_path()


def hush_logo(ctx, x, y, r, color=None, hole="#ffffff", lw=None, wordmark=False,
              word_color=None, word_size=None, ring=True, word_dy=None):
    """HushCorp logo: teal circle with a stylised keyhole. (x, y) = circle centre.

    wordmark=True adds the wide-spaced "HUSHCORP" wordmark below (font "ui").
    Returns the bottom y of what was drawn.
    """
    color = color or PAL["hush"]
    lw = r * 0.06 if lw is None else lw
    core.circle(ctx, x, y, r)
    fs(ctx, color, lw if lw > 0 else 0, INK)
    if ring:
        core.circle(ctx, x, y, r * 0.84)
        core.stroke(ctx, hole, max(1.0, r * 0.045))
    keyhole_path(ctx, x, y, r * 0.78)
    core.fill(ctx, hole)
    bottom = y + r
    if wordmark:
        ws = word_size or r * 0.55
        wy = y + r + (word_dy if word_dy is not None else ws * 1.35)
        spaced_text(ctx, "HUSHCORP", x, wy, ws, word_color or PAL["hush_dk"], "ui", 0.55)
        bottom = wy
    return bottom


def _star(ctx, x, y, r, n=5, inner=0.45, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        a = rot + i * math.pi / n
        rr = r if i % 2 == 0 else r * inner
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    core.poly(ctx, pts)


# ----------------------------------------------------------------------------
# monitor game screen
# ----------------------------------------------------------------------------
_G_COLS, _G_ROWS = 48, 30
_HERO = [  # 7 x 8 pixel hero (0 = clear)
    "..HHH..",
    ".HHHHH.",
    "..FFE..",
    "..FFF..",
    ".BBBBB.",
    "F.BBB.F",
    "..L.L..",
    ".SS.SS.",
]
_HERO_RUN2 = [
    "..HHH..",
    ".HHHHH.",
    "..FFE..",
    "..FFF..",
    ".BBBBB.",
    ".FBBBF.",
    "..LL...",
    "..SSS..",
]
_HERO_COL = {"H": "#3d4f86", "F": "#f2c29a", "E": "#1d1626", "B": "#ff6f61",
             "L": "#5a5f7a", "S": "#1d1626"}
_BLOB = [
    "..GGG..",
    ".GGGGG.",
    "GWEGWEG",
    "GGGGGGG",
    ".G.G.G.",
]


def _pix_sprite(ctx, rows, cols_map, x, y, pw, ph, flip=False):
    by = {}
    for j, row in enumerate(rows):
        n = len(row)
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            ii = (n - 1 - i) if flip else i
            by.setdefault(ch, []).append((x + ii * pw, y + j * ph))
    for ch, cells in by.items():
        for (cx, cy) in cells:
            ctx.rectangle(cx, cy, pw + 0.3, ph + 0.3)
        core.fill(ctx, cols_map[ch])


def monitor_game_screen(ctx, x, y, w, h, t, speed=1.0, seed=0, hud=True, scanlines=True):
    """Cute 8-bit platformer, drawn into the rect (x, y, w, h). Animated by t.

    Flat chunky pixels (48 x 30 grid), parallax clouds and hills, scrolling
    ground, spinning coins, a hopping hero and a little blob enemy. ~1 ms.
    """
    pw, ph = w / _G_COLS, h / _G_ROWS
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    # sky (two flat bands)
    ctx.rectangle(x, y, w, h)
    core.fill(ctx, "#7fd0ff")
    ctx.rectangle(x, y + ph * 14, w, ph * 8)
    core.fill(ctx, "#a6e0ff")
    scroll = t * 9.0 * speed  # pixels per second (grid px)

    def px(i, j, wi=1, hj=1):
        ctx.rectangle(x + i * pw, y + j * ph, wi * pw + 0.3, hj * ph + 0.3)

    # clouds (parallax 0.25), snapped to whole pixels
    off = int(scroll * 0.25)
    for k in range(4):
        cx = (k * 17 + 5 - off) % 64 - 8
        cy = 3 + (k * 5) % 6
        px(cx, cy, 6, 2); px(cx + 1, cy - 1, 3, 1); px(cx + 2, cy + 2, 3, 1)
    core.fill(ctx, "#ffffff")
    # far hills (parallax 0.5)
    off = int(scroll * 0.5)
    for k in range(5):
        hx = (k * 14 - off) % 70 - 12
        hgt = 5 + (k * 3) % 4
        for r_ in range(hgt):
            px(hx + r_, 22 - r_, (hgt - r_) * 2, 1)
    core.fill(ctx, "#5cc46a")
    for k in range(5):
        hx = (k * 14 - off) % 70 - 12
        px(hx + 3, 19, 1, 1); px(hx + 6, 20, 1, 1)
    core.fill(ctx, "#3f9a52")
    # ground: grass row + dirt, scrolling at full speed
    off = int(scroll)
    gy = 23
    px(0, gy, _G_COLS, 1)
    core.fill(ctx, "#4ed15a")
    px(0, gy + 1, _G_COLS, _G_ROWS - gy - 1)
    core.fill(ctx, "#c47a3a")
    for i in range(-2, _G_COLS + 2, 4):
        ii = i - (off % 4)
        px(ii, gy + 2, 2, 1); px(ii + 2, gy + 4, 2, 1); px(ii + 1, gy + 6, 1, 1)
    core.fill(ctx, "#9a5a28")
    # floating ? blocks and coins (world positions in grid px)
    for k in range(3):
        bx = (k * 23 + 12 - off) % 69 - 10
        px(bx, 15, 3, 3)
        core.fill(ctx, "#ffb020")
        px(bx + 1, 16, 1, 1)
        core.fill(ctx, "#8a4a10")
    spin = [3, 2, 1, 2][int(t * 8) % 4]
    for k in range(6):
        cx = (k * 11 + 4 - off) % 66 - 6
        cy = 18 if k % 2 == 0 else 12
        px(cx + (3 - spin) / 2, cy, spin, 3)
    core.fill(ctx, "#ffe45c")
    # blob enemy
    ex = (40 - off * 1.2) % 70 - 10
    _pix_sprite(ctx, _BLOB, {"G": "#8a5cd6", "W": "#ffffff", "E": "#1d1626"},
                x + int(ex) * pw, y + (gy - 5) * ph, pw, ph)
    # hero: runs in place at x=12, hops every 1.3 s
    period = 1.3
    ph_ = (t % period) / period
    jump = 0.0
    if ph_ < 0.55:
        k = ph_ / 0.55
        jump = 4 * k * (1 - k) * 8
    frame = _HERO if (int(t * 8) % 2 == 0 or jump > 0) else _HERO_RUN2
    hy = gy - 8 - int(round(jump))
    _pix_sprite(ctx, frame, _HERO_COL, x + 12 * pw, y + hy * ph, pw, ph)
    if hud:
        sz = max(6.0, ph * 1.6)
        sc = 1250 + int(t * 50) * 10
        core.text(ctx, f"SCORE {sc:06d}", x + pw * 1.5, y + ph * 2.4, sz, "#ffffff", "mono", "left")
        for k in range(3):
            px(_G_COLS - 3 - k * 3, 1, 2, 2)
        core.fill(ctx, "#ff4f6d")
    if scanlines:
        for j in range(0, _G_ROWS, 2):
            ctx.rectangle(x, y + j * ph, w, max(0.6, ph * 0.18))
        core.fill(ctx, (0, 0, 0, 0.06))
    ctx.restore()


# ----------------------------------------------------------------------------
# cage
# ----------------------------------------------------------------------------
CAGE_W, CAGE_H = 300, 270  # body size at s=1 (handle top is the anchor)


def cage(ctx, x, y, s=1.0, t=0.0, door=0.0, latch="closed", rattle=0.0, inside_fn=None,
         rot=0.0, empty=None, label=True):
    """Lab pet-carrier cage. ANCHOR = top of the handle (where hands/teeth grip).

    door 0..1 swings the barred front door open (hinge on the left, creaks
    toward the viewer); latch "open"|"half"|"closed" ("half" wiggles);
    rattle 0..1 shakes the cage about the handle; inside_fn(ctx) is called
    behind the bars in a local frame whose origin is the interior FLOOR
    centre (units = cage units, interior ~200 x 150, y up is negative).
    empty=True (or no inside_fn) shows only bedding straw.
    """
    rj = 0.0
    if rattle > 0:
        rj = rattle * (0.07 * math.sin(t * 47) + 0.04 * math.sin(t * 31 + 1.3))
    with core.saved(ctx, x, y, s, rot + rj):
        _cage_body(ctx, t, door, latch, rattle, inside_fn if not empty else None, label)
    if rattle > 0.05:
        # little rattle marks either side
        a = clamp(rattle)
        for side in (-1, 1):
            for k in range(2):
                ox = x + side * (CAGE_W / 2 + 24 + k * 18) * s
                oy = y + (120 + k * 40) * s
                line(ctx, [(ox, oy - 18 * s), (ox + side * 8 * s, oy), (ox, oy + 18 * s)],
                     core.alpha(INK, a), 4 * s)


def _cage_body(ctx, t, door, latch, rattle, inside_fn, label):
    shell, shell_dk = "#d6e1ea", "#a8b8c8"
    # handle
    ctx.move_to(-62, 48)
    ctx.curve_to(-62, -6, 62, -6, 62, 48)
    core.stroke(ctx, INK, 30)
    ctx.move_to(-62, 48)
    ctx.curve_to(-62, -6, 62, -6, 62, 48)
    core.stroke(ctx, "#7c8aa0", 18)
    # body
    rect(ctx, -150, 40, 300, 230, shell, 6, r=26)
    rect(ctx, -150, 236, 300, 34, shell_dk, 0, r=14)
    core.rrect(ctx, -150, 40, 300, 230, 26)
    core.stroke(ctx, INK, 6)
    # top ridge
    line(ctx, [(-120, 58), (120, 58)], shell_dk, 6)
    # feet
    for fx in (-118, 118):
        rect(ctx, fx - 20, 262, 40, 16, "#5a6378", 4, r=6)
    # interior
    ix, iy, iw, ih = -112, 74, 224, 168
    rect(ctx, ix, iy, iw, ih, "#3b3150", 4, r=10)
    ctx.rectangle(ix + 4, iy + ih - 34, iw - 8, 30)
    core.fill(ctx, "#5a4a3a")
    for k in range(9):
        sx = ix + 14 + k * 24
        line(ctx, [(sx, iy + ih - 18), (sx + 14, iy + ih - 30)], "#d9b45a", 4)
    if inside_fn is not None:
        ctx.save()
        ctx.rectangle(ix, iy, iw, ih)
        ctx.clip()
        ctx.translate(0, iy + ih - 8)
        inside_fn(ctx)
        ctx.restore()
    # door (hinged on the left edge of the opening)
    ang = clamp(door) * math.radians(105)
    hx = ix
    wdoor = iw
    fx = hx + wdoor * math.cos(ang)
    grow = 1 + 0.18 * math.sin(ang)  # free edge closer -> taller
    top_f = iy + ih / 2 - ih / 2 * grow
    bot_f = iy + ih / 2 + ih / 2 * grow
    q = [(hx, iy), (fx, top_f), (fx, bot_f), (hx, iy + ih)]
    if abs(fx - hx) > 3:
        # bars
        nb = 8
        for k in range(nb + 1):
            u = k / nb
            xa = lerp(hx, fx, u)
            ya, yb = lerp(iy, top_f, u), lerp(iy + ih, bot_f, u)
            line(ctx, [(xa, ya), (xa, yb)], INK, 9)
            line(ctx, [(xa, ya), (xa, yb)], "#c7ced8", 4)
        for v in (0.0, 0.5, 1.0):
            line(ctx, [(hx, lerp(iy, iy + ih, v)), (fx, lerp(top_f, bot_f, v))], INK, 12)
            line(ctx, [(hx, lerp(iy, iy + ih, v)), (fx, lerp(top_f, bot_f, v))], "#9aa6b6", 6)
    else:
        line(ctx, [(hx, iy), (hx, iy + ih)], INK, 12)
    # hinges
    for hy in (iy + 24, iy + ih - 24):
        rect(ctx, hx - 12, hy - 10, 18, 20, "#7c8aa0", 3, r=4)
    # latch on the right edge of the opening
    lx, ly = ix + iw + 10, iy + ih / 2
    rect(ctx, lx - 8, ly - 26, 26, 52, shell_dk, 4, r=6)  # catch housing
    if latch == "closed":
        boff, btilt = 0.0, 0.0
    elif latch == "half":
        boff = 14 + 4 * math.sin(t * 21)
        btilt = 0.18 * math.sin(t * 17 + 0.5)
    else:
        boff, btilt = 34.0, 0.0
    # the bolt rides on the door's free edge when the door is shut
    if door < 0.05:
        with core.saved(ctx, lx - 6 - boff, ly, 1.0, btilt):
            rect(ctx, -30, -9, 52, 18, "#ffb020", 4, r=6)
            core.circle(ctx, -24, -14, 7)
            fs(ctx, "#ffb020", 3)
    if label:
        rect(ctx, 70, 246, 64, 18, "#ffffff", 2, r=4)
        hush_logo(ctx, 82, 255, 6.5, lw=0, ring=False)
        line(ctx, [(94, 252), (126, 252)], "#9aa6b6", 2.5)
        line(ctx, [(94, 258), (118, 258)], "#9aa6b6", 2.5)


# ----------------------------------------------------------------------------
# small items
# ----------------------------------------------------------------------------
def rock(ctx, x, y, s=1.0, rot=0.0, seed=3):
    """Hand-sized lawn rock (~90 x 65 at s=1). ANCHOR = centre."""
    with core.saved(ctx, x, y, s, rot):
        pts = []
        for i in range(9):
            a = i / 9 * TAU
            r = 1 + 0.16 * (hash01(i, seed) - 0.5)
            pts.append((math.cos(a) * 46 * r, math.sin(a) * 32 * r + (6 if math.sin(a) > 0 else 0)))
        blob(ctx, pts, "#9a96a6", 5)
        blob(ctx, [(p[0] * 0.8 + 6, p[1] * 0.45 + 14) for p in pts], "#7f7b8e", 0)
        curve(ctx, [(-24, -14), (-8, -22), (10, -20)], "#c9c6d4", 5)
        core.circle(ctx, 14, 2, 3.5)
        core.fill(ctx, "#6b677a")


RECORDER_BUTTON = (-22, -29)   # top button (local, s=1): where a thumb presses


def recorder(ctx, x, y, s=1.0, t=0.0, led=None, glow=0.0, rot=0.0, only_led=False, button=0.0):
    """Tiny black recording device (~96 x 58 at s=1). ANCHOR = centre.

    led: LED brightness 0..1 (None -> blinks with t, 1 Hz; False/0 = off,
    True/1 = steady on). glow 0..1 adds a red halo. only_led=True draws just
    the LED + halo (for "blinking through his coat pocket"). button 0..1
    pushes the small top button down (the off "click"; RECORDER_BUTTON is
    its local position).
    """
    if led is None:
        led = 1.0 if (t % 1.0) < 0.45 else 0.15
    led = float(led)
    with core.saved(ctx, x, y, s, rot):
        lx, ly = 30, -12
        if not only_led:
            bx, by = RECORDER_BUTTON
            bh = 12 - 8 * clamp(button)
            rect(ctx, bx - 13, by - bh, 26, bh + 6, "#3a3746", 3.5, r=4)
            rect(ctx, -48, -29, 96, 58, "#26242f", 4.5, r=14)
            rect(ctx, -40, -22, 80, 10, "#3a3746", 0, r=4)
            for k in range(4):
                line(ctx, [(-34 + k * 9, 6), (-34 + k * 9, 18)], "#4a4658", 3)
            hush_logo(ctx, 18, 10, 9, lw=0, ring=False, hole="#26242f")
            core.circle(ctx, lx, ly, 6)
            fs(ctx, "#4a1620", 2)
        if glow > 0 or only_led:
            core.radial_glow(ctx, lx, ly, 26 + 22 * glow, PAL["danger"], 0.55 * led * max(glow, 0.6))
        core.circle(ctx, lx, ly, 4.5)
        core.fill(ctx, mixc("#5a1a26", "#ff3b5c", led))
        if led > 0.5:
            core.circle(ctx, lx - 1.5, ly - 1.5, 1.6)
            core.fill(ctx, "#ffd0d8")


def pink_slip(ctx, x, y, s=1.0, rot=0.0, curl=0.0):
    """Pink 'TERMINATION NOTICE' slip (~190 x 220 at s=1). ANCHOR = centre.

    The title is bold and large so it reads at s >= 1.2 on a phone.
    """
    with core.saved(ctx, x, y, s, rot):
        pts = [(-95, -110), (95, -110), (95, 110 - 20 * curl), (-95, 110)]
        polyf(ctx, pts, "#ffb3c7", 4)
        line(ctx, [(-78, -94), (78, -94)], "#ff7aa0", 3)
        core.text(ctx, "TERMINATION", 0, -62, 23, "#c2184b", "ui")
        core.text(ctx, "NOTICE", 0, -32, 30, "#c2184b", "ui")
        for k in range(5):
            w = 120 if k % 3 else 90
            line(ctx, [(-66, -6 + k * 18), (-66 + w, -6 + k * 18)], "#e889a6", 5)
        line(ctx, [(10, 88), (70, 88)], "#c2184b", 3)
        curve(ctx, [(14, 84), (26, 72), (36, 86), (50, 74), (62, 82)], "#5a2236", 3)
        hush_logo(ctx, -56, 78, 14, lw=0, ring=False, color="#c2184b", hole="#ffb3c7")


def tablet(ctx, x, y, s=1.0, rot=0.0, t=0.0, screen_fn=None, glow=0.0, portrait=False,
           on=True):
    """Slim tablet. ANCHOR = centre. Landscape 300 x 200 at s=1 (portrait swaps).

    screen_fn(ctx, sx, sy, sw, sh, t) draws into the screen rect (local
    units). glow 0..1 adds a cool screen halo.
    """
    w, h = (200, 300) if portrait else (300, 200)
    with core.saved(ctx, x, y, s, rot):
        if glow > 0:
            core.radial_glow(ctx, 0, 0, max(w, h) * 0.9, "#cfefff", 0.35 * glow)
        rect(ctx, -w / 2, -h / 2, w, h, "#2a2d3a", 5, r=22)
        sx, sy, sw, sh = -w / 2 + 16, -h / 2 + 16, w - 32, h - 32
        rect(ctx, sx, sy, sw, sh, "#dff4ff" if on else "#1b1d27", 0, r=8)
        if on:
            if screen_fn is not None:
                ctx.save()
                core.rrect(ctx, sx, sy, sw, sh, 8)
                ctx.clip()
                screen_fn(ctx, sx, sy, sw, sh, t)
                ctx.restore()
            else:
                hush_logo(ctx, 0, -10, min(sw, sh) * 0.22, lw=0)
                spaced_text(ctx, "HUSHCORP", 0, sh * 0.32, min(sw, sh) * 0.1, PAL["hush_dk"])
        # glass glint
        ctx.move_to(sx + sw * 0.55, sy)
        ctx.line_to(sx + sw * 0.75, sy)
        ctx.line_to(sx + sw * 0.45, sy + sh)
        ctx.line_to(sx + sw * 0.25, sy + sh)
        ctx.close_path()
        core.fill(ctx, (1, 1, 1, 0.12))


def clipboard(ctx, x, y, s=1.0, rot=0.0):
    """Clipboard with a work order (~190 x 260 at s=1). ANCHOR = centre."""
    with core.saved(ctx, x, y, s, rot):
        rect(ctx, -95, -130, 190, 260, "#b9874f", 5, r=12)
        rect(ctx, -80, -104, 160, 222, "#fbfaf4", 3.5, r=4)
        core.text(ctx, "WORK ORDER", 0, -72, 19, "#3d4f86", "ui")
        for k in range(6):
            yy = -48 + k * 24
            rect(ctx, -64, yy - 9, 12, 12, None, 2.5, sc="#6b7088")
            line(ctx, [(-44, yy - 3), (50 - (k % 3) * 18, yy - 3)], "#a7abc0", 4)
        line(ctx, [(-62, -50), (-56, -42), (-48, -58)], "#3ddc84", 3.5)
        rect(ctx, -46, -146, 92, 40, "#c9ced8", 4.5, r=10)
        core.circle(ctx, 0, -128, 8)
        fs(ctx, "#8d93a3", 3)


def picture_frame(ctx, x, y, s=1.0, rot=0.0, face_down=False, cracked=False, wire=True):
    """Small framed photo of two kids (young Tiredness + Embarrassment).

    ANCHOR = the nail (top centre; the frame hangs ~30 px below it).
    Frame 120 x 140 at s=1. face_down=True shows the cardboard back.
    """
    with core.saved(ctx, x, y, s, rot):
        if wire and not face_down:
            line(ctx, [(-34, 34), (0, 0), (34, 34)], "#5a5368", 2.5)
        fx, fy, fw, fh = -60, 28, 120, 140
        if face_down:
            rect(ctx, fx, fy, fw, fh, "#a77b4f", 5, r=6)
            rect(ctx, fx + 12, fy + 12, fw - 24, fh - 24, "#c9a87a", 3)
            rect(ctx, -10, fy + 56, 20, 34, "#8a6a44", 2.5, r=3)
            return
        rect(ctx, fx, fy, fw, fh, "#c98d4a", 5, r=6)
        rect(ctx, fx + 14, fy + 14, fw - 28, fh - 28, "#ffe9b8", 3)
        # the photo: two kid heads
        ctx.save()
        ctx.rectangle(fx + 14, fy + 14, fw - 28, fh - 28)
        ctx.clip()
        ctx.rectangle(fx + 14, fy + 92, fw - 28, 40)
        core.fill(ctx, "#9ed27a")
        ell(ctx, -18, 96, 15, 17, PAL["t_skin"], 2.5)
        blob(ctx, [(-34, 90), (-30, 74), (-12, 72), (-2, 86), (-14, 80), (-26, 84)], PAL["t_hair"], 2)
        ell(ctx, 18, 92, 13, 17, PAL["e_skin"], 2.5)
        blob(ctx, [(6, 84), (12, 72), (28, 74), (32, 86), (22, 80)], PAL["e_hair"], 2)
        core.circle(ctx, 14, 92, 4.5); core.circle(ctx, 24, 92, 4.5)
        core.stroke(ctx, INK, 1.8)
        rect(ctx, -32, 112, 30, 26, PAL["t_hoodie"], 2)
        rect(ctx, 6, 110, 26, 28, PAL["e_vest"], 2)
        ctx.restore()
        ctx.move_to(fx + 30, fy + 14); ctx.line_to(fx + 50, fy + 14); ctx.line_to(fx + 14, fy + 70)
        ctx.line_to(fx + 14, fy + 42); ctx.close_path()
        core.fill(ctx, (1, 1, 1, 0.35))
        if cracked:
            line(ctx, [(-10, 60), (6, 84), (-4, 104), (14, 128)], "#ffffff", 2.5)
            line(ctx, [(6, 84), (30, 90)], "#ffffff", 2)


def plates_stack(ctx, x, y, s=1.0, lift=0.0, n=4, t=0.0):
    """Stack of dinner plates (side view, 190 wide at s=1). ANCHOR = bottom centre.

    lift 0..1 raises the top plate ~70 px with a tiny tilt (careful lift).
    """
    with core.saved(ctx, x, y, s):
        for k in range(n):
            top = (k == n - 1)
            yy = -10 - k * 13
            rot = 0.0
            if top and lift > 0:
                yy -= 70 * lift
                rot = -0.06 * math.sin(lift * math.pi) + 0.01 * math.sin(t * 9) * lift
            with core.saved(ctx, 0, yy, 1.0, rot):
                ell(ctx, 0, 0, 95, 15, "#f7f4ec", 4)
                ell(ctx, 0, -3, 58, 7, "#e3ddcf", 0)
                curve(ctx, [(-80, 4), (0, 10), (80, 4)], "#5b7fd1", 3)


_SHARD_SHAPES = [
    [(0, -18), (9, 10), (-7, 14)],
    [(-12, -10), (14, -6), (2, 16)],
    [(0, -22), (6, -2), (2, 18), (-6, 4)],
    [(-10, -6), (12, -12), (8, 10)],
]


def shards(ctx, t, t0, x, y, seed=0, n=12, s=1.0, floor_y=None, dir=1.0, spread=1.0,
           power=1.0, out_z=False):
    """Band of flying glass shards from (x, y) starting at t0 that settle on
    floor_y (default y + 320*s). n <= 15. dir = +1 throws right, -1 left, 0 both.

    Each shard has its own hashed velocity, spin and size; once it hits the
    floor it lies still (a tiny bounce). Nothing is drawn before t0.
    """
    if t < t0:
        return
    n = min(int(n), 15)
    fy = y + 320 * s if floor_y is None else floor_y
    tau = t - t0
    g = 2600 * s
    for i in range(n):
        h1, h2, h3, h4 = (hash01(i, seed + k) for k in (11, 23, 37, 51))
        d = dir if dir != 0 else (1 if h1 > 0.5 else -1)
        vx = d * (120 + 900 * h2) * spread * s * power
        vy = (-900 * h3 - 150) * s * power
        spin = (h4 - 0.5) * 16
        sz = (0.7 + 0.7 * h1) * s
        # landing time (y(t) = y + vy t + g t^2/2 = fy)
        a, b, c = g / 2, vy, (y - fy)
        disc = max(0.0, b * b - 4 * a * c)
        tl = (-b + math.sqrt(disc)) / (2 * a)
        tt = min(tau, tl)
        px = x + vx * tt
        py = y + vy * tt + g * tt * tt / 2
        rot = spin * tt
        if tau > tl:
            # small settle hop then rest, lying flat-ish
            k = tau - tl
            hop = max(0.0, math.sin(min(k / 0.18, 1.0) * math.pi)) * 18 * s * (1 - min(k / 0.18, 1))
            py -= hop
            px += vx * 0.04 * min(k / 0.18, 1)
            rot = round(rot / math.pi) * math.pi + (h2 - 0.5) * 0.6
        shape = _SHARD_SHAPES[i % len(_SHARD_SHAPES)]
        with core.saved(ctx, px, py, sz, rot):
            polyf(ctx, shape, "#dff3ff", 2.5)
            line(ctx, [shape[0], shape[1]], "#ffffff", 2)


# ----------------------------------------------------------------------------
# vehicles and street
# ----------------------------------------------------------------------------
VAN_L, VAN_H = 2700, 1180  # at s=1


def _van_body_static(ctx, tint):
    body, body_hi, body_dk = "#2a2b36", "#41435a", "#1b1c24"
    L, H = VAN_L, VAN_H
    x0 = -L / 2
    # body silhouette (facing right): rear at x0, nose at x0+L
    pts = [(x0 + 30, -150), (x0 + 30, -H + 60), (x0 + 90, -H), (x0 + L - 700, -H),
           (x0 + L - 420, -H + 380), (x0 + L - 40, -H + 470), (x0 + L, -H + 540),
           (x0 + L, -170), (x0 + L - 40, -150)]
    core.smooth_path(ctx, pts, closed=True, tension=0.18)
    fs(ctx, body, 9)
    # lower shade band
    ctx.rectangle(x0 + 34, -360, L - 70, 200)
    core.fill(ctx, body_dk)
    # highlight line along the shoulder
    line(ctx, [(x0 + 100, -H + 70), (x0 + L - 720, -H + 70)], body_hi, 14)
    line(ctx, [(x0 + 60, -560), (x0 + L - 30, -560)], body_hi, 8)
    # windscreen
    wpts = [(x0 + L - 690, -H + 50), (x0 + L - 450, -H + 360), (x0 + L - 450, -H + 420),
            (x0 + L - 690, -H + 420)]
    polyf(ctx, wpts, mixc("#6b8db0", "#1b2230", tint), 7)
    # side windows (tinted)
    for wx, ww in ((x0 + 120, 520),):
        rect(ctx, wx, -H + 120, ww, 300, mixc("#6b8db0", "#1b2230", tint), 7, r=18)
    # reflections
    ctx.move_to(x0 + 200, -H + 120); ctx.line_to(x0 + 290, -H + 120)
    ctx.line_to(x0 + 190, -H + 420); ctx.line_to(x0 + 100 + 20, -H + 420); ctx.close_path()
    core.fill(ctx, (1, 1, 1, 0.12))
    ctx.move_to(x0 + L - 600, -H + 90); ctx.line_to(x0 + L - 560, -H + 140)
    ctx.line_to(x0 + L - 640, -H + 420); ctx.line_to(x0 + L - 680, -H + 420); ctx.close_path()
    core.fill(ctx, (1, 1, 1, 0.14))
    # headlight + tail light + bumpers
    rect(ctx, x0 + L - 80, -470, 60, 80, "#fff3c4", 5, r=14)
    rect(ctx, x0 + 18, -720, 34, 120, "#c23a4a", 5, r=8)
    rect(ctx, x0 + L - 160, -230, 170, 70, "#3a3c4c", 6, r=20)
    rect(ctx, x0, -230, 150, 70, "#3a3c4c", 6, r=20)
    # front door seam + mirror
    line(ctx, [(x0 + L - 700, -H + 60), (x0 + L - 700, -200)], INK, 6)
    rect(ctx, x0 + L - 470, -700, 70, 16, "#5a5c70", 4, r=6)
    rect(ctx, x0 + L - 690, -H + 340, 70, 60, "#3a3c4c", 5, r=10)
    # logo on the side (rear panel)
    hush_logo(ctx, x0 + 380, -620, 95, lw=6)
    spaced_text(ctx, "HUSHCORP", x0 + 380, -470, 58, "#cfeeea", "ui", 0.5)
    # wheel arches
    for wx in (x0 + 470, x0 + L - 560):
        ctx.new_sub_path()
        ctx.arc(wx, -150, 220, math.pi, 0)
        ctx.close_path()
        fs(ctx, "#121218", 6)


def black_van(ctx, x, y, s=1.0, door=0.0, facing=1, tint=0.75, t=0.0, layer="all",
              bounce=0.0):
    """Black HushCorp van, side view, ~2700 x 1180 at s=1 (use s~0.4-0.5 by the
    house). ANCHOR = ground point under the middle of the van.

    door 0..1 slides the side door toward the rear, opening a dark interior.
    tint 0..1 darkens the windows. facing=+1 nose right, -1 nose left.
    layer: "all" | "interior" (just the dark opening, draw before a
    character climbing in) | "body" (everything else).
    bounce: suspension squash offset 0..1 (e.g. when someone jumps in).
    """
    L, H = VAN_L, VAN_H
    x0 = -L / 2
    dx0, dw, dtop, dbot = x0 + 760, 620, -H + 90, -200
    open_w = dw * clamp(door) * 0.92
    with core.saved(ctx, x, y, (s * facing, s)):
        by = -12 * bounce
        if layer in ("all", "interior"):
            if open_w > 2:
                ctx.save()
                ctx.translate(0, by)
                rect(ctx, dx0 + dw - open_w, dtop, open_w, dbot - dtop, "#0d0d14", 0)
                ctx.rectangle(dx0 + dw - open_w, dbot - 70, open_w, 70)
                core.fill(ctx, "#25252f")
                ctx.restore()
        if layer == "interior":
            return
        # wheels (live: cheap)
        for wx in (x0 + 470, x0 + L - 560):
            core.circle(ctx, wx, -150, 165)
            fs(ctx, "#1a1a20", 8)
            core.circle(ctx, wx, -150, 80)
            fs(ctx, "#9aa0b0", 6)
            core.circle(ctx, wx, -150, 22)
            fs(ctx, "#5a5f70", 4)
        ctx.save()
        ctx.translate(0, by)
        if open_w > 2:
            ctx.rectangle(-L, -H - 50, 2 * L, H + 100)
            ctx.rectangle(dx0 + dw - open_w + open_w, dtop, -open_w, dbot - dtop)
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            ctx.clip()
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        core.cached(ctx, ("van_body", round(tint, 2)), x0 - 20, -H - 20, L + 40, H + 40,
                    lambda c: _van_body_static(c, tint))
        ctx.restore()
        # sliding door panel (slides rearward over the body)
        ctx.save()
        ctx.translate(-open_w * 0.96, by)
        rect(ctx, dx0, dtop, dw, dbot - dtop, "#30313e", 6, r=10)
        rect(ctx, dx0 + 40, dtop + 30, dw - 80, 300, mixc("#6b8db0", "#1b2230", tint), 6, r=14)
        rect(ctx, dx0 + 30, -600, 90, 26, "#5a5c70", 4, r=8)
        line(ctx, [(dx0 + 10, -560), (dx0 + dw - 10, -560)], "#41435a", 8)
        ctx.restore()


def trash_can(ctx, x, y, s=1.0, knocked=0.0, spill=True, dir=1, seed=0, lid_on=True,
              dent=0.0):
    """Metal trash can (260 x 420 at s=1). ANCHOR = bottom centre (ground).

    knocked 0..1 tips it over sideways (dir=+1 to the right), the lid rolls
    off and trash spills out (spill=True) in proportion to knocked.
    """
    k = clamp(knocked)
    ang = dir * k * math.radians(92)
    piv_x = x + dir * 130 * s
    with core.saved(ctx, x, y, s):
        if spill and k > 0.4:
            a = (k - 0.4) / 0.6
            items = [("#f2d04b", "banana"), ("#ffffff", "paper"), ("#c94f4f", "can"),
                     ("#8fd16a", "paper"), ("#ffffff", "paper"), ("#b98a5a", "box")]
            for i, (col, kind) in enumerate(items):
                d = (180 + 360 * hash01(i, seed + 3)) * a
                px = dir * (210 + d)
                py = -14 - 30 * hash01(i, seed + 5)
                rr = (hash01(i, seed + 7) - 0.5) * 2.4
                with core.saved(ctx, px, py, 1.0, rr):
                    if kind == "banana":
                        curve(ctx, [(-34, 0), (0, 14), (34, 0)], INK, 22)
                        curve(ctx, [(-34, 0), (0, 14), (34, 0)], col, 14)
                    elif kind == "can":
                        rect(ctx, -26, -16, 52, 32, col, 4, r=6)
                        line(ctx, [(-10, -16), (-10, 16)], "#ffffff", 4)
                    elif kind == "box":
                        rect(ctx, -34, -24, 68, 48, col, 4, r=4)
                    else:
                        polyf(ctx, [(-30, -16), (26, -22), (34, 14), (-22, 20)], col, 4)
                        line(ctx, [(-16, -6), (16, -9)], "#aaaabb", 3)
    with core.saved(ctx, piv_x, y, s, ang):
        ctx.translate(-dir * 130, 0)
        body, sh = "#a7b0bb", "#7d8794"
        pts = [(-118, -400), (118, -400), (130, 0), (-130, 0)]
        polyf(ctx, pts, body, 6)
        polyf(ctx, [(40, -400), (118, -400), (130, 0), (52, 0)], sh, 0)
        polyf(ctx, pts, None, 6)
        for yy in (-300, -160):
            line(ctx, [(-122, yy), (122, yy)], sh, 7)
            line(ctx, [(-122, yy + 10), (122, yy + 10)], "#cfd5dc", 4)
        if dent:
            ell(ctx, -30, -210, 40 * dent, 30 * dent, sh, 3)
        rect(ctx, -70, -320, 22, 50, "#7d8794", 4, r=8)
        if k > 0.3:
            ell(ctx, 0, -400, 118, 26, "#2e2a36", 5)
    if lid_on:
        lid_x = x + (dir * k * 300 * s if k > 0 else 0)
        lid_y = y - (420 * s if k < 0.05 else 30 * s)
        lid_rot = k * dir * 1.4
        with core.saved(ctx, lid_x, lid_y, s, lid_rot if k > 0.05 else 0):
            if k <= 0.05:
                ell(ctx, 0, 14, 136, 26, "#bcc4ce", 6)
                rect(ctx, -30, -14, 60, 22, "#7d8794", 5, r=8)
            else:
                ell(ctx, 0, 0, 28, 136, "#bcc4ce", 6, rot=0.0)
                ell(ctx, 0, 0, 10, 100, "#9aa3ad", 0)


def streetlight(ctx, x, y, s=1.0, t=0.0, broken=0.0, on=False, lean=None, seed=1):
    """Street light (~2700 px tall at s=1). ANCHOR = base centre.

    broken 0..1: the lamp head shatters (jagged glass, bits on the ground),
    the pole leans (lean defaults to 9 deg * broken) and, if broken > 0.5, a
    small deterministic spark flicker. on=True lights the lamp (dusk).
    """
    b = clamp(broken)
    ang = math.radians(9) * b if lean is None else lean
    # glass bits on the ground
    if b > 0.3:
        for i in range(9):
            gx = x + (hash01(i, seed) - 0.3) * 520 * s
            gy = y - 6 * s - hash01(i, seed + 4) * 16 * s
            with core.saved(ctx, gx, gy, s * (0.8 + 0.6 * hash01(i, seed + 2)), hash01(i, seed + 9) * 6):
                polyf(ctx, [(-10, -6), (12, -3), (2, 8)], "#e8f6ff", 2.5)
    with core.saved(ctx, x, y, s, ang):
        rect(ctx, -60, -60, 120, 60, "#4b5067", 6, r=12)
        polyf(ctx, [(-22, -60), (22, -60), (14, -2500), (-14, -2500)], "#5d6380", 6)
        line(ctx, [(-8, -120), (-4, -2450)], "#7e86a6", 6)
        # arm
        ctx.move_to(0, -2480)
        ctx.curve_to(0, -2640, 200, -2700, 380, -2640)
        core.stroke(ctx, INK, 30)
        ctx.move_to(0, -2480)
        ctx.curve_to(0, -2640, 200, -2700, 380, -2640)
        core.stroke(ctx, "#5d6380", 18)
        hx, hy = 400, -2630
        polyf(ctx, [(hx - 130, hy - 30), (hx + 130, hy - 30), (hx + 100, hy + 20), (hx - 100, hy + 20)],
              "#4b5067", 6)
        if b < 0.5:
            glow = "#fff2b0" if on else "#e8eef5"
            ell(ctx, hx, hy + 32, 92, 30, glow, 5)
            if on:
                core.radial_glow(ctx, hx, hy + 60, 420, "#ffe7a0", 0.45)
        else:
            polyf(ctx, [(hx - 92, hy + 22), (hx - 60, hy + 64), (hx - 30, hy + 30), (hx + 4, hy + 76),
                        (hx + 34, hy + 34), (hx + 70, hy + 58), (hx + 92, hy + 22)], "#e8eef5", 4)
            ell(ctx, hx, hy + 24, 20, 10, "#3a3c4c", 3)
            # flicker: rare short sparks
            fl = hash01(int(t * 12), seed + 17)
            if fl > 0.78:
                core.radial_glow(ctx, hx, hy + 30, 120, "#fff2b0", 0.6)
                for k in range(3):
                    a = k * 2.1 + t * 3
                    line(ctx, [(hx, hy + 30), (hx + math.cos(a) * 46, hy + 30 + abs(math.sin(a)) * 46)],
                         "#ffe45c", 4)


def debris(ctx, x, y, s=1.0, kind="plank", rot=0.0, seed=0):
    """Debris piece. kind: plank | brick | paper | can | chunk | shard | bolt.
    ANCHOR = centre (~80-200 px at s=1)."""
    with core.saved(ctx, x, y, s, rot):
        if kind == "plank":
            polyf(ctx, [(-100, -14), (96, -18), (104, 12), (-92, 16), (-104, 2)], "#c98d5a", 4)
            line(ctx, [(-70, -2), (60, -6)], "#a8703f", 3)
            core.circle(ctx, 70, 0, 4); core.fill(ctx, "#5a4a3a")
        elif kind == "brick":
            rect(ctx, -46, -22, 92, 44, "#b5544a", 4, r=5)
            line(ctx, [(-30, -8), (-10, -12)], "#d77b6e", 3)
        elif kind == "paper":
            polyf(ctx, [(-40, -28), (36, -34), (44, 26), (-34, 30)], "#ffffff", 3.5)
            line(ctx, [(-24, -12), (24, -16)], "#c9cfe0", 3)
            line(ctx, [(-24, 2), (16, -1)], "#c9cfe0", 3)
        elif kind == "can":
            rect(ctx, -30, -18, 60, 36, "#5b9bd5", 4, r=8)
            line(ctx, [(-10, -18), (-10, 18)], "#ffffff", 4)
        elif kind == "chunk":
            polyf(ctx, [(-40, -20), (-6, -36), (38, -16), (30, 22), (-28, 26)], "#a9a3b5", 4)
            line(ctx, [(-10, -20), (8, 4)], "#8a8498", 3)
        elif kind == "shard":
            polyf(ctx, [(0, -24), (12, 12), (-10, 16)], "#dff3ff", 3)
        else:  # bolt
            rect(ctx, -22, -8, 44, 16, "#8d93a3", 3, r=4)
            rect(ctx, 16, -14, 14, 28, "#6b7088", 3, r=3)


# ----------------------------------------------------------------------------
# room clutter
# ----------------------------------------------------------------------------
def sock(ctx, x, y, s=1.0, rot=0.0, color="#f4f1e8", stripe="#ff6f61"):
    """A sock (~120 x 70 at s=1). ANCHOR = centre."""
    with core.saved(ctx, x, y, s, rot):
        blob(ctx, [(-50, -30), (-14, -32), (-10, 6), (36, 4), (58, 18), (44, 36), (-6, 34), (-40, 20)],
             color, 4.5)
        line(ctx, [(-48, -16), (-12, -18)], stripe, 7)
        ell(ctx, 46, 22, 12, 10, mixc(color, "#000000", 0.12), 0)


def shirt(ctx, x, y, s=1.0, rot=0.0, color="#ff8f5a", flap=0.0, t=0.0, print_=True):
    """A flying T-shirt (~240 x 220 at s=1). ANCHOR = centre. flap 0..1 waves it."""
    w = flap * math.sin(t * 14)
    with core.saved(ctx, x, y, s, rot):
        pts = [(-50, -96), (-20, -84), (20, -84), (50, -96), (114, -56 + 10 * w),
               (90, -10 + 14 * w), (60, -30), (64, 96 - 10 * w), (0, 104 + 8 * w), (-64, 96 + 10 * w),
               (-60, -30), (-90, -10 - 14 * w), (-114, -56 - 10 * w)]
        core.smooth_path(ctx, pts, closed=True, tension=0.25)
        fs(ctx, color, 5)
        curve(ctx, [(-20, -84), (0, -66), (20, -84)], INK, 4)
        if print_:
            _star(ctx, 0, 10, 26)
            fs(ctx, "#fff3c4", 3)
        line(ctx, [(-56, 60), (-50, 80)], mixc(color, "#000000", 0.2), 4)


def sweater(ctx, x, y, s=1.0, state="folded", lump=0.0, wiggle=0.0, t=0.0, rot=0.0,
            color="#d9604c"):
    """Knit sweater. ANCHOR = bottom centre.

    state "folded" (neat 200 x 90 stack), "flat" (spread out, 380 x 300) or
    "draped" (a mound over something; lump 0..1 = mound height, wiggle 0..1
    makes the lump shift with t). Knit texture = little chevron rows.
    """
    dk = mixc(color, "#2a1020", 0.28)
    lt = mixc(color, "#ffffff", 0.25)
    with core.saved(ctx, x, y, s, rot):
        if state == "folded":
            rect(ctx, -100, -90, 200, 90, color, 5, r=16)
            line(ctx, [(-100, -48), (100, -48)], dk, 4)
            for row in range(3):
                for k in range(8):
                    cx = -84 + k * 24
                    cy = -76 + row * 26
                    line(ctx, [(cx - 7, cy), (cx, cy + 6), (cx + 7, cy)], dk, 2.5)
            rect(ctx, -100, -16, 200, 16, dk, 0, r=6)
            for k in range(12):
                line(ctx, [(-92 + k * 16, -14), (-92 + k * 16, -2)], lt, 2.5)
        elif state == "flat":
            pts = [(-70, -300), (-26, -286), (26, -286), (70, -300), (190, -220), (176, -150),
                   (100, -190), (104, 0), (-104, 0), (-100, -190), (-176, -150), (-190, -220)]
            polyf(ctx, pts, color, 5)
            for row in range(7):
                for k in range(7):
                    cx = -78 + k * 26
                    cy = -250 + row * 34
                    line(ctx, [(cx - 8, cy), (cx, cy + 7), (cx + 8, cy)], dk, 2.5)
            rect(ctx, -104, -22, 208, 22, dk, 3, r=4)
            curve(ctx, [(-26, -286), (0, -262), (26, -286)], INK, 4)
        else:  # draped
            h = 40 + 90 * clamp(lump)
            sh = wiggle * 18 * math.sin(t * 9)
            sq = wiggle * 10 * math.sin(t * 13 + 1)
            pts = [(-170, 0), (-150, -h * 0.25), (-80 + sh * 0.5, -h * 0.85 - sq),
                   (sh, -h - sq), (80 + sh * 0.5, -h * 0.8), (150, -h * 0.2), (175, 0),
                   (120, 8), (40, 2), (-40, 8), (-120, 4)]
            blob(ctx, pts, color, 5, tension=0.45)
            for row in range(3):
                for k in range(6):
                    cx = -90 + k * 36 + sh * 0.6
                    cy = -h * (0.75 - row * 0.25)
                    line(ctx, [(cx - 8, cy), (cx, cy + 6), (cx + 8, cy)], dk, 2.5)
            # a dangling sleeve
            blob(ctx, [(120, -10), (150, -34), (196, -20), (210, 6), (170, 10)], color, 4.5)
            line(ctx, [(196, -18), (204, 6)], dk, 3)


def fly(ctx, x, y, s=1.0, t=0.0, rot=0.0):
    """Tiny house fly (~26 px at s=1). ANCHOR = centre. Wings blur with t."""
    with core.saved(ctx, x, y, s, rot):
        fl = math.sin(t * 90)
        for side in (-1, 1):
            ell(ctx, side * 7, -8 - 2 * fl, 9, 5, (0.85, 0.92, 1.0, 0.75), 1.6, rot=side * (0.5 + 0.3 * fl))
        ell(ctx, 0, 0, 7, 9, "#2b2b38", 2)
        core.circle(ctx, -3, -7, 2.6); core.circle(ctx, 3, -7, 2.6)
        core.fill(ctx, "#b5544a")


def leaf(ctx, x, y, s=1.0, rot=0.0, color="#e9a23b"):
    """Single autumn-ish leaf (~70 x 40 at s=1). ANCHOR = centre."""
    with core.saved(ctx, x, y, s, rot):
        blob(ctx, [(-34, 0), (-10, -18), (24, -14), (36, 0), (22, 14), (-10, 18)], color, 3.5)
        line(ctx, [(-40, 2), (30, 0)], mixc(color, "#4a2a10", 0.45), 2.5)
        line(ctx, [(-6, 0), (6, -10)], mixc(color, "#4a2a10", 0.45), 2)
        line(ctx, [(4, 0), (14, 10)], mixc(color, "#4a2a10", 0.45), 2)


# ----------------------------------------------------------------------------
# lab + shaft
# ----------------------------------------------------------------------------
def red_button_console(ctx, x, y, s=1.0, pressed=0.0, t=0.0, alarm=0.0, label=True):
    """Lab console with a big red button. ANCHOR = bottom centre (floor).

    ~620 wide x 560 tall at s=1. The button dome sits at (x + 150 s,
    y - 470 s) (see BUTTON_OFFSET). pressed 0..1 squashes the dome.
    alarm 0..1 lights the status lamps red.
    """
    with core.saved(ctx, x, y, s):
        # cabinet
        polyf(ctx, [(-300, 0), (300, 0), (300, -400), (-300, -400)], "#c9d3dc", 6)
        polyf(ctx, [(160, 0), (300, 0), (300, -400), (160, -400)], "#aab7c3", 0)
        polyf(ctx, [(-300, 0), (300, 0), (300, -400), (-300, -400)], None, 6)
        rect(ctx, -270, -340, 180, 230, "#b7c3ce", 4, r=10)
        for k in range(4):
            line(ctx, [(-250, -300 + k * 50), (-110, -300 + k * 50)], "#93a2b0", 5)
        # slanted top panel
        polyf(ctx, [(-320, -400), (320, -400), (290, -520), (-290, -520)], "#e7edf2", 6)
        # small buttons + screen
        rect(ctx, -250, -506, 190, 92, "#24323b", 5, r=8)
        for k in range(4):
            line(ctx, [(-236, -488 + k * 20), (-236 + 60 + 40 * hash01(k, 3), -488 + k * 20)],
                 PAL["hush"], 4)
        for k in range(5):
            cx = -30 + k * 34
            col = [PAL["safe"], PAL["warn"], "#7fb2e8", PAL["safe"], "#ffffff"][k]
            if alarm > 0:
                col = mixc(col, PAL["danger"], alarm)
            core.circle(ctx, cx, -462, 10)
            fs(ctx, col, 3)
        # big red button
        bx, by = 150, -470
        p = clamp(pressed)
        ell(ctx, bx, by + 6, 92, 30, "#5a6378", 5)
        ell(ctx, bx, by, 80, 24, "#ffd34d", 5)
        dome_h = 52 * (1 - 0.75 * p)
        ctx.move_to(bx - 62, by)
        ctx.curve_to(bx - 62, by - dome_h * 1.3, bx + 62, by - dome_h * 1.3, bx + 62, by)
        ctx.curve_to(bx + 40, by + 12, bx - 40, by + 12, bx - 62, by)
        fs(ctx, "#ff3b5c", 5)
        ell(ctx, bx - 18, by - dome_h * 0.62, 20, 8, "#ff9aac", 0, rot=-0.2)
        if label:
            rect(ctx, 40, -380, 220, 46, "#fff3c4", 3.5, r=6)
            core.text(ctx, "DO NOT LEAN", 150, -362, 18, "#c2184b", "ui")
            core.text(ctx, "ON CONSOLE", 150, -342, 15, "#5a5368", "ui")


BUTTON_OFFSET = (150, -470)


def containment_pod(ctx, x, y, s=1.0, t=0.0, sleeper_fn=None, seed=0, glow=1.0, pulse=None,
                    lit=True):
    """Standalone containment pod for close-ups. ANCHOR = centre of the glass.

    ~420 x 760 at s=1 (glass 300 x 560). Teal liquid glow (power colour),
    metal caps, tubes, a few bubbles. sleeper_fn(ctx, x, y, s, t, seed) is
    called inside the glass at the sleeper's centre (s = this pod's s * 0.9);
    without it a dim curled silhouette is drawn. pulse: glow multiplier
    (None -> slow 0.25 Hz breathing pulse from t).
    """
    if pulse is None:
        pulse = 0.85 + 0.15 * math.sin(t * TAU * 0.25 + seed)
    g = glow * pulse
    pw = PAL["power"]
    with core.saved(ctx, x, y, s):
        if lit:
            core.radial_glow(ctx, 0, 0, 420, pw, 0.30 * g)
        # tubes
        for side in (-1, 1):
            curve(ctx, [(side * 150, -330), (side * 210, -380), (side * 230, -440)], INK, 22)
            curve(ctx, [(side * 150, -330), (side * 210, -380), (side * 230, -440)], "#3b4757", 12)
        # glass capsule
        core.rrect(ctx, -150, -280, 300, 560, 150)
        fs(ctx, mixc("#0b3a40", pw, 0.35 + 0.35 * g if lit else 0.1), 0)
        ctx.save()
        core.rrect(ctx, -150, -280, 300, 560, 150)
        ctx.clip()
        if lit:
            core.radial_glow(ctx, 0, 40, 260, pw, 0.55 * g)
        if sleeper_fn is not None:
            sleeper_fn(ctx, 0, 40, 0.9, t, seed)
        else:
            sleeper_silhouette(ctx, 0, 40, 1.0, t, seed)
        # bubbles
        for k in range(5):
            ph = (t * 0.25 + hash01(k, seed + 3)) % 1.0
            bx = -90 + 180 * hash01(k, seed + 5) + 8 * math.sin(t * 2 + k)
            byy = 250 - ph * 520
            core.circle(ctx, bx, byy, 6 + 5 * hash01(k, seed + 7))
            core.stroke(ctx, (0.85, 1.0, 0.98, 0.7), 2.5)
        # glass sheen
        ctx.move_to(-110, -240); ctx.line_to(-60, -260); ctx.line_to(-60, 240); ctx.line_to(-110, 220)
        ctx.close_path()
        core.fill(ctx, (1, 1, 1, 0.16))
        ctx.restore()
        core.rrect(ctx, -150, -280, 300, 560, 150)
        core.stroke(ctx, INK, 7)
        # caps
        for cy, hh in ((-330, 90), (240, 100)):
            rect(ctx, -190, cy, 380, hh, "#4a5868", 7, r=26)
            line(ctx, [(-160, cy + hh * 0.5), (160, cy + hh * 0.5)], "#6b7a8c", 6)
        for k in range(3):
            core.circle(ctx, -60 + k * 60, 300, 9)
            fs(ctx, pw if lit else "#3b4757", 3)


def sleeper_silhouette(ctx, x, y, s=1.0, t=0.0, seed=0, color="#123a44"):
    """Dim curled creature silhouette (default pod content). ANCHOR = centre."""
    br = 1 + 0.025 * math.sin(t * 1.3 + seed)
    with core.saved(ctx, x, y, (s * br, s)):
        blob(ctx, [(-110, 40), (-120, -20), (-70, -80), (10, -90), (90, -60), (120, 0),
                   (100, 60), (20, 90), (-60, 84)], color, 0)
        # long fin ears swept back over the body
        blob(ctx, [(70, -70), (20, -120), (-60, -140), (-20, -104), (40, -66)], color, 0)
        blob(ctx, [(90, -60), (50, -104), (-10, -112), (30, -82), (70, -50)], color, 0)
        # tail curl
        curve(ctx, [(-100, 50), (-150, 90), (-120, 130), (-60, 110)], color, 22)
        # closed eye line
        curve(ctx, [(52, -30), (66, -22), (80, -30)], mixc(color, PAL["power"], 0.45), 4)


def doormat(ctx, x, y, s=1.0, rot=0.0, bunch=0.0, text="GO AWAY", t=0.0):
    """Coir doormat seen at a low angle (~520 x 150 at s=1). ANCHOR = centre.

    bunch 0..1 rumples it (after the trip: a fold ridge and a flipped corner).
    """
    b = clamp(bunch)
    with core.saved(ctx, x, y, s, rot):
        ridge = 46 * b
        pts = [(-250, -60), (250, -60), (270, 70), (-270 + 90 * b, 70 + 10 * b)]
        top = [(-250, -60), (-90, -60 - ridge * 0.4), (40, -60 - ridge), (250, -60)]
        ctx.move_to(*top[0])
        core.smooth_path(ctx, top, closed=False)
        ctx.line_to(270, 70)
        ctx.line_to(60, 70 - ridge * 0.5)
        ctx.line_to(-270 + 90 * b, 70 + 10 * b)
        ctx.close_path()
        fs(ctx, "#b8864a", 5)
        rect(ctx, -230, -46, 460, 98, None, 3, sc="#8a5e2e")
        core.text(ctx, text, 0, 28, 64, "#5a3a1a", "title")
        if b > 0.05:
            polyf(ctx, [(-270, 70), (-270 + 90 * b, 70 + 10 * b), (-250 + 70 * b, 30 - 40 * b)],
                  "#a07038", 4)


# ============================================================================
# Episode 2 props: shaft / tunnel / control room / bedroom-at-dawn
# ============================================================================
STEEL, STEEL_SH, STEEL_DK, STEEL_HI = "#aab6c0", "#7f8d99", "#4a5868", "#d3dbe1"
HAZ_Y = "#ffc93c"


def _spaced_w(ctx, s, size, font="ui", spacing=0.45):
    core.set_font(ctx, font, size)
    advs = [ctx.text_extents(ch)[4] for ch in s]
    return sum(advs) + spacing * size * (len(s) - 1)


def hazard_band(ctx, x, y, w, h, step=None, col1=HAZ_Y, col2=INK, lw=3.0, slant=1.0):
    """Yellow/ink diagonal hazard stripes filling the rect (x, y, w, h)."""
    step = step or max(12.0, h * 1.1)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.rectangle(x, y, w, h)
    core.fill(ctx, col1)
    xx = x - h * slant - step
    while xx < x + w + step:
        core.poly(ctx, [(xx, y + h), (xx + step * 0.5, y + h), (xx + step * 0.5 + h * slant, y),
                        (xx + h * slant, y)])
        xx += step
    core.fill(ctx, col2)
    ctx.restore()
    if lw:
        ctx.rectangle(x, y, w, h)
        core.stroke(ctx, INK, lw)


# ----------------------------------------------------------------------------
# pod nameplate (dusty, thumb-wipe reveal)
# ----------------------------------------------------------------------------
def nameplate_size(text="CURIOSITY", sub="SPECIMEN 00", size=44):
    """(w, h) of a nameplate at s=1 (needs a font context; cheap)."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    c = cairo.Context(surf)
    tw = _spaced_w(c, text, size, "ui", 0.12)
    sw = _spaced_w(c, sub, size * 0.45, "mono", 0.25) if sub else 0
    w = max(220.0, tw + 64, sw + 64)
    h = size * 2.25 if sub else size * 1.6
    return w, h


def nameplate(ctx, x, y, s=1.0, text="CURIOSITY", sub="SPECIMEN 00", dust=0.0, wipe=0.0,
              rot=0.0, seed=0, size=44, light=1.0):
    """Brushed-steel pod nameplate with engraved text. ANCHOR = centre.

    ~300 x 100 at s=1 (the width follows the text; nameplate_size()).
    sub = small top line (None = one line). dust 0..1 lays a grey-brown film
    over it (0.85+ hides the text). wipe 0..1 clears the dust from left to
    right behind a ragged front (the thumb-wipe insert: animate wipe with
    the thumb's x), leaving a faint smear. light < 1 darkens it (dark sets).
    """
    w, h = nameplate_size(text, sub, size)
    with core.saved(ctx, x, y, s, rot):
        x0, y0 = -w / 2, -h / 2
        rect(ctx, x0, y0, w, h, "#c4ccd3", 4.5, r=10)
        rect(ctx, x0 + 6, y0 + 5, w - 12, 5, "#e4eaee", 0, r=2)
        rect(ctx, x0 + 6, y0 + h - 10, w - 12, 5, "#9aa6b0", 0, r=2)
        for k in range(3):
            yy = y0 + h * (0.3 + 0.22 * k)
            line(ctx, [(x0 + 18, yy), (x0 + w * (0.5 + 0.3 * hash01(k, seed + 3)), yy)],
                 (1, 1, 1, 0.22), 2)
        for (rx, ry) in ((x0 + 14, y0 + 14), (x0 + w - 14, y0 + 14),
                         (x0 + 14, y0 + h - 14), (x0 + w - 14, y0 + h - 14)):
            core.circle(ctx, rx, ry, 5.5)
            fs(ctx, "#8d99a3", 2)
        if sub:
            spaced_text(ctx, sub, 0, y0 + size * 0.78, size * 0.45, "#4a5868", "mono", 0.25)
            spaced_text(ctx, text, 0, y0 + h - size * 0.42, size, "#1f2a33", "ui", 0.12)
        else:
            spaced_text(ctx, text, 0, size * 0.36, size, "#1f2a33", "ui", 0.12)
        d = clamp(dust)
        if d > 0.01:
            ctx.save()
            core.rrect(ctx, x0, y0, w, h, 10)
            ctx.clip()
            wf = clamp(wipe)
            xw = x0 - 30 + (w + 60) * wf
            if wf > 0:
                # ragged wipe front; dust remains to the right of it
                pts = [(x0 + w + 40, y0 - 10)]
                n = 9
                for i in range(n + 1):
                    yy = y0 - 10 + (h + 20) * i / n
                    pts.append((xw + (hash01(i, seed + 11) - 0.5) * 22, yy))
                pts.append((x0 + w + 40, y0 + h + 10))
                core.poly(ctx, [pts[0]] + pts[1:-1][::1] + [pts[-1]])
                ctx.clip()
            ctx.rectangle(x0 - 4, y0 - 4, w + 8, h + 8)
            core.fill(ctx, core.alpha("#8f8676", 0.9 * d))
            for i in range(6):
                bx = x0 + w * hash01(i, seed + 20)
                by = y0 + h * hash01(i, seed + 21)
                ell(ctx, bx, by, 30 + 40 * hash01(i, seed + 22), 10 + 14 * hash01(i, seed + 23),
                    core.alpha("#776f61", 0.55 * d), 0, rot=hash01(i, seed + 24) - 0.5)
            for i in range(14):
                core.circle(ctx, x0 + w * hash01(i, seed + 30), y0 + h * hash01(i, seed + 31),
                            1.5 + 2.5 * hash01(i, seed + 32))
            core.fill(ctx, core.alpha("#5e574b", 0.8 * d))
            for i in range(4):
                yy = y0 + h * (0.2 + 0.2 * i)
                line(ctx, [(x0 + w * hash01(i, seed + 40), yy),
                           (x0 + w * hash01(i, seed + 40) + 60, yy + 3)], core.alpha("#b8b0a0", 0.5 * d), 3)
            if wf > 0:
                # dust heaped at the wipe front
                curve(ctx, [(xw + 4, y0 - 4), (xw + 10, y0 + h * 0.5), (xw + 2, y0 + h + 4)],
                      core.alpha("#6e6657", 0.8 * d), 7)
            ctx.restore()
            if wf > 0:
                # faint thumb smear left behind
                ctx.save()
                core.rrect(ctx, x0, y0, w, h, 10)
                ctx.clip()
                for i in range(3):
                    yy = y0 + h * (0.3 + 0.2 * i)
                    line(ctx, [(x0 + 10, yy), (min(xw, x0 + w) - 10, yy + 2 * (i - 1))],
                         core.alpha("#8f8676", 0.16 * d), 10)
                ctx.restore()
        if light < 1:
            core.rrect(ctx, x0, y0, w, h, 10)
            core.fill(ctx, core.alpha("#03070b", 0.85 * (1 - clamp(light))))
    return (x - w * s / 2, y - h * s / 2, w * s, h * s)


# ----------------------------------------------------------------------------
# security camera (wall mount, red LED)
# ----------------------------------------------------------------------------
def security_camera(ctx, x, y, s=1.0, t=0.0, cam_angle=0.35, led=None, face=0.0, flip=False,
                    glow=1.0, only_led=False):
    """Wall security camera. ANCHOR = the wall mount plate.

    The arm reaches ~110 px out (to the right; flip=True mirrors it) to a
    pivot; the body (~200 x 80) hangs from the pivot and rotates by
    cam_angle (radians, 0 = lens pointing out level, + = tilting down,
    ~1.2 = looking down steeply). face 0..1 swivels the lens toward the
    viewer (the body foreshortens, the round lens shows). led 0..1 (None =
    1 Hz blink); glow scales the LED halo. only_led=True draws just the LED
    + halo (on top of a darkened camera). Returns the lens centre (caller
    coordinates) so a glint / whir can be placed.
    """
    if led is None:
        led = 1.0 if (t % 1.0) < 0.5 else 0.12
    led = clamp(float(led))
    sx = -1 if flip else 1
    fc = clamp(face)
    L = 210 * (1 - 0.55 * fc)
    with core.saved(ctx, x, y, (s * sx, s)):
        if not only_led:
            rect(ctx, -26, -46, 52, 92, STEEL_DK, 4, r=8)
            for by in (-30, 30):
                core.circle(ctx, 0, by, 5)
                fs(ctx, STEEL_SH, 2)
            line(ctx, [(0, 0), (90, 6), (110, 40)], INK, 20)
            line(ctx, [(0, 0), (90, 6), (110, 40)], "#8693a0", 11)
        with core.saved(ctx, 110, 44, 1.0, cam_angle):
            bx0, bx1 = -64, -64 + L
            if not only_led:
                polyf(ctx, [(bx0 - 12, -12), (bx1 + 22, -12), (bx1 + 30, -2), (bx0 - 12, -2)], "#c9d1d8", 4)
                rect(ctx, bx0, -4, L, 70, "#e6ebef", 4.5, r=14)
                rect(ctx, bx0 + 8, 42, L - 16, 16, "#b9c3cc", 0, r=6)
                rect(ctx, bx0 + 12, 8, 46, 8, "#c9d1d8", 0, r=3)
                lx = bx1 + 2
                rx = 9 + 31 * fc
                ell(ctx, lx, 31, rx + 6, 34, "#3b4757", 4.5)
                ell(ctx, lx + 2 * (1 - fc), 31, rx, 26, "#121a24", 3)
                ell(ctx, lx + 2 * (1 - fc), 31, rx * 0.5, 13, "#24425a", 0)
                ell(ctx, lx - rx * 0.3, 22, max(2.0, rx * 0.25), 6, (1, 1, 1, 0.55), 0)
            lex, ley = bx1 - 26, 12
            if led > 0.2 and glow > 0:
                core.radial_glow(ctx, lex, ley, 46 * glow, PAL["danger"], 0.6 * led)
            core.circle(ctx, lex, ley, 7)
            fs(ctx, mixc("#4a1620", "#ff3b5c", led), 2.5)
            if led > 0.5:
                core.circle(ctx, lex - 2, ley - 2, 2.2)
                core.fill(ctx, "#ffd0d8")
    ca, sa = math.cos(cam_angle), math.sin(cam_angle)
    lx_l, ly_l = -64 + L + 2, 31
    px = 110 + lx_l * ca - ly_l * sa
    py = 44 + lx_l * sa + ly_l * ca
    return (x + px * s * sx, y + py * s)


# ----------------------------------------------------------------------------
# low pipe (the bonk)
# ----------------------------------------------------------------------------
def low_pipe(ctx, x, y, s=1.0, r=46, rise=300, span=300, reach=(700, 500), part="all", t=0.0,
             wobble=0.0, wobble_t0=0.0, hazard=True, sign=True, color="#6f8792", side=1):
    """A ceiling pipe that DIPS to face height (low clearance): it runs
    level `rise` above the face, bends down, runs low for `span`, and bends
    back up. ANCHOR = the contact point: the outer side of the descending
    bend at face height, i.e. where the face of someone walking LEFT hits it
    (side=-1 mirrors: walking right). reach = (right, left) lengths of the
    high runs. hazard: yellow/black bands on the dip; sign: a hanging MIND
    YOUR HEAD sign over the high run. wobble 0..1 after a bonk at
    wobble_t0: the dip shivers (~1 s decay) and the sign swings (~2 s).
    part is accepted for symmetry ("all"/"bg" draw it, "fg" draws nothing).
    Returns the contact point.
    """
    if part == "fg":
        return (x, y)
    k = t - wobble_t0
    jx = jy = sw = 0.0
    if wobble > 0 and 0 <= k < 2.4:
        a_ = wobble * math.exp(-3.2 * k)
        jx = a_ * 8 * math.sin(k * 38)
        jy = a_ * 4 * math.sin(k * 29 + 1)
        sw = wobble * 0.30 * math.sin(k * 7.5) * math.exp(-1.6 * k)
    R = 90
    with core.saved(ctx, x, y, (s * side, s)):
        xd = -r                                  # descending section centre line
        yt = -rise                               # high run
        yb = r * 0.4                             # low run (just below the face)
        dk = mixc(color, INK, 0.35)
        hi = mixc(color, "#ffffff", 0.32)

        def path(dx=0.0, dy=0.0):
            ctx.move_to(xd + reach[0], yt)
            ctx.line_to(xd + R, yt)
            ctx.curve_to(xd + R * 0.45, yt, xd, yt + R * 0.45, xd, yt + R)
            ctx.line_to(xd + dx, yb - R + dy)
            ctx.curve_to(xd + dx, yb - R * 0.45 + dy, xd - R * 0.45 + dx, yb + dy, xd - R + dx, yb + dy)
            ctx.line_to(xd - span + R + dx, yb + dy)
            ctx.curve_to(xd - span + R * 0.45 + dx, yb + dy, xd - span + dx, yb - R * 0.45 + dy,
                         xd - span + dx, yb - R + dy)
            ctx.line_to(xd - span, yt + R)
            ctx.curve_to(xd - span, yt + R * 0.45, xd - span - R * 0.45, yt, xd - span - R, yt)
            ctx.line_to(xd - span - reach[1], yt)
        path(jx, jy)
        core.stroke(ctx, INK, 2 * r + 10, cap="butt")
        path(jx, jy)
        core.stroke(ctx, color, 2 * r, cap="butt")
        ctx.save()
        ctx.translate(-r * 0.35, -r * 0.35)
        path(jx, jy)
        core.stroke(ctx, hi, r * 0.35, cap="butt")
        ctx.restore()
        # flanges + hangers on the high runs
        for fx in (xd + reach[0] * 0.55, xd - span - reach[1] * 0.5):
            rect(ctx, fx - 11, yt - r - 7, 22, 2 * r + 14, "#4a5868", 4, r=4)
            line(ctx, [(fx + 60, yt - r), (fx + 60, yt - r - 260)], "#4a5868", 7)
        rect(ctx, xd - r - 8 + jx, yb - R - 16 + jy, 2 * r + 16, 20, "#4a5868", 4, r=4)
        if hazard:
            hazard_band(ctx, xd - r + jx, yt + R + 30, 2 * r, max(20, yb - R - 46 - (yt + R + 30)), step=34,
                        lw=3.5)
            hazard_band(ctx, xd - span + R + 10 + jx, yb - r + jy, span - 2 * R - 20, 2 * r, step=40, lw=3.5)
        if sign:
            sx_, sy_ = xd - span - R - 40, yt + r
            line(ctx, [(sx_, sy_), (sx_, sy_ + 26)], "#5a6470", 3)
            with core.saved(ctx, sx_, sy_ + 26, (side, 1.0), sw):
                rect(ctx, -86, 0, 172, 78, HAZ_Y, 4.5, r=8)
                core.text(ctx, "MIND", 0, 32, 26, INK, "ui")
                core.text(ctx, "YOUR HEAD", 0, 62, 24, INK, "ui")
    return (x, y)


# ----------------------------------------------------------------------------
# HushCorp keycard
# ----------------------------------------------------------------------------
def _emb_photo(ctx, x, y, w, h):
    """Tiny ID photo of Embarrassment (light-blue backdrop) in rect x, y, w, h."""
    ctx.save()
    core.rrect(ctx, x, y, w, h, 6)
    ctx.clip()
    ctx.rectangle(x, y, w, h)
    core.fill(ctx, "#cfe6f5")
    cx = x + w / 2
    # shoulders: lab coat + teal vest
    blob(ctx, [(cx - w * 0.55, y + h + 10), (cx - w * 0.42, y + h * 0.80), (cx, y + h * 0.74),
               (cx + w * 0.42, y + h * 0.80), (cx + w * 0.55, y + h + 10)], PAL["e_coat"], 2.5)
    polyf(ctx, [(cx - w * 0.14, y + h * 0.76), (cx + w * 0.14, y + h * 0.76), (cx + w * 0.1, y + h + 4),
                (cx - w * 0.1, y + h + 4)], PAL["e_vest"], 2)
    rect(ctx, cx - w * 0.07, y + h * 0.62, w * 0.14, h * 0.16, PAL["e_skin_sh"], 0)
    # head
    ell(ctx, cx, y + h * 0.46, w * 0.27, h * 0.24, PAL["e_skin"], 2.5)
    # hair with a tuft
    blob(ctx, [(cx - w * 0.29, y + h * 0.42), (cx - w * 0.26, y + h * 0.22), (cx - w * 0.06, y + h * 0.14),
               (cx + w * 0.08, y + h * 0.04), (cx + w * 0.12, y + h * 0.15), (cx + w * 0.28, y + h * 0.24),
               (cx + w * 0.29, y + h * 0.40), (cx + w * 0.10, y + h * 0.30), (cx - w * 0.12, y + h * 0.31)],
         PAL["e_hair"], 2.5)
    # glasses + eyes + a nervous little mouth
    for sx in (-1, 1):
        core.circle(ctx, cx + sx * w * 0.12, y + h * 0.48, w * 0.095)
        core.stroke(ctx, PAL["glasses"], 2.2)
        core.circle(ctx, cx + sx * w * 0.12, y + h * 0.485, w * 0.03)
        core.fill(ctx, INK)
    line(ctx, [(cx - w * 0.025, y + h * 0.48), (cx + w * 0.025, y + h * 0.48)], PAL["glasses"], 2)
    curve(ctx, [(cx - w * 0.07, y + h * 0.60), (cx, y + h * 0.585), (cx + w * 0.07, y + h * 0.60)], INK, 2)
    ell(ctx, cx - w * 0.2, y + h * 0.57, w * 0.05, h * 0.02, core.alpha(PAL["blush"], 0.5), 0)
    ell(ctx, cx + w * 0.2, y + h * 0.57, w * 0.05, h * 0.02, core.alpha(PAL["blush"], 0.5), 0)
    ctx.restore()
    core.rrect(ctx, x, y, w, h, 6)
    core.stroke(ctx, INK, 3)


KEYCARD_W, KEYCARD_H = 340, 216


def keycard(ctx, x, y, s=1.0, rot=0.0, photo=True, glint=0.0, back=False):
    """HushCorp keycard "HUSHCORP / LVL 9" with Embarrassment's tiny photo.
    ANCHOR = centre. 340 x 216 at s=1 (credit-card shape). Readable in an
    insert at on-screen s >= ~1.4. glint 0..1 sweeps a light streak across
    it; back=True draws the plain back (magnetic stripe)."""
    W_, H_ = KEYCARD_W, KEYCARD_H
    with core.saved(ctx, x, y, s, rot):
        x0, y0 = -W_ / 2, -H_ / 2
        rect(ctx, x0, y0, W_, H_, "#f7fafc", 5, r=18)
        if back:
            rect(ctx, x0 + 3, y0 + 30, W_ - 6, 44, "#2a2d3a", 0)
            rect(ctx, x0 + 24, y0 + 100, 170, 30, "#e6ebf0", 2.5, sc="#c9d1d8", r=4)
            core.text(ctx, "IF FOUND, RETURN TO HUSHCORP", 0, y0 + H_ - 26, 15, "#7f8b98", "mono")
        else:
            ctx.save()
            core.rrect(ctx, x0, y0, W_, H_, 18)
            ctx.clip()
            ctx.rectangle(x0, y0, W_, 58)
            core.fill(ctx, PAL["hush"])
            ctx.rectangle(x0, y0 + 58, W_, 6)
            core.fill(ctx, PAL["hush_dk"])
            ctx.restore()
            hush_logo(ctx, x0 + 34, y0 + 29, 19, color="#ffffff", hole=PAL["hush"], lw=0)
            spaced_text(ctx, "HUSHCORP", x0 + 62, y0 + 39, 25, "#ffffff", "ui", 0.42, align="left")
            rect(ctx, -26, y0 + 8, 52, 9, "#1f8f88", 0, r=4)
            if photo:
                _emb_photo(ctx, x0 + 18, y0 + 76, 102, 124)
            core.text(ctx, "ACCESS LEVEL", x0 + 236, y0 + 94, 17, "#6b7a8c", "mono")
            core.text(ctx, "LVL 9", x0 + 236, y0 + 150, 58, "#1f2a44", "ui")
            core.text(ctx, "RESEARCH", x0 + 236, y0 + 176, 18, PAL["hush_dk"], "mono")
            for i in range(26):
                bw = 2 + 3 * hash01(i, 77)
                rect(ctx, x0 + 140 + i * 7.2, y0 + 186, bw, 18, "#2a2d3a", 0)
        if glint > 0:
            ctx.save()
            core.rrect(ctx, x0, y0, W_, H_, 18)
            ctx.clip()
            gx = x0 - 80 + (W_ + 160) * clamp(glint)
            core.poly(ctx, [(gx, y0), (gx + 46, y0), (gx - 30, y0 + H_), (gx - 76, y0 + H_)])
            core.fill(ctx, (1, 1, 1, 0.45 * math.sin(clamp(glint) * math.pi)))
            ctx.restore()
        core.rrect(ctx, x0, y0, W_, H_, 18)
        core.stroke(ctx, INK, 5)


# ----------------------------------------------------------------------------
# flashlight
# ----------------------------------------------------------------------------
FLASHLIGHT_LENS = (116, 0)   # local lens centre (s=1); the beam leaves along +x


def flashlight(ctx, x, y, s=1.0, rot=0.0, on=True, glow=1.0, t=0.0, flip=False):
    """Handheld flashlight, side view. ANCHOR = middle of the grip (where the
    fist goes); the lens points along +x rotated by rot (flip=True points
    -x). ~250 x 72 at s=1. on: the lens face glows (bright disc + small
    halo); the beam itself is an fx job. Returns {"lens": (x, y), "angle":
    beam direction in radians} in caller coordinates."""
    on = float(on)
    sx = -1 if flip else 1
    with core.saved(ctx, x, y, (s * sx, s), rot * sx):
        rect(ctx, -122, -18, 26, 36, "#262a35", 4, r=8)
        rect(ctx, -100, -20, 140, 40, "#353b4a", 4.5, r=8)
        for k in range(6):
            line(ctx, [(-86 + k * 14, -16), (-86 + k * 14, 16)], "#252a36", 4)
        rect(ctx, 6, -27, 26, 10, "#ff6f61", 3, r=4)
        polyf(ctx, [(38, -22), (78, -34), (102, -34), (102, 34), (78, 34), (38, 22)], "#3f4656", 4.5)
        line(ctx, [(46, -18), (96, -28)], "#5b6375", 4)
        rect(ctx, 100, -37, 12, 74, STEEL_HI, 4, r=4)
        lc = mixc("#5a6070", "#fff6d6", on)
        ell(ctx, 115, 0, 9, 32, lc, 3.5)
        if on > 0.05 and glow > 0:
            core.radial_glow(ctx, 118, 0, 80 * glow, "#fff3c4", 0.55 * on)
            ell(ctx, 116, 0, 5, 22, (1, 1, 1, 0.9 * on), 0)
    lx, ly = FLASHLIGHT_LENS
    ang = rot if not flip else math.pi - rot
    ca, sa = math.cos(rot * sx), math.sin(rot * sx)
    px = (lx * ca - ly * sa) * sx
    py = lx * sa + ly * ca
    return {"lens": (x + px * s, y + py * s), "angle": ang}


# ----------------------------------------------------------------------------
# phone (+ a chat screen helper)
# ----------------------------------------------------------------------------
PHONE_W, PHONE_H = 128, 250
PHONE_SCREEN = (-56, -110, 112, 220)   # local screen rect at s=1


def _phone_lock(ctx, x, y, w, h, t):
    core.vgradient(ctx, "#3a3f78", "#e58aa0", x, y, w, h)
    core.text(ctx, "6:02", x + w / 2, y + h * 0.3, w * 0.34, "#ffffff", "ui")
    core.text(ctx, "SAT", x + w / 2, y + h * 0.39, w * 0.11, (1, 1, 1, 0.8), "ui")


def phone_chat_screen(msgs=(("them", "you ok?", 0.0),), avatar=True, typing=None):
    """Build a screen_fn for props.phone(): a tiny chat. msgs = [(side,
    text, t_show)], side "them" (grey, left) or "me" (blue, right); each
    bubble pops in at t_show. typing = (t0, t1) shows a "..." bubble on
    "me"'s side. avatar: a little orange-haired face in the header (no
    name)."""
    def fn(ctx, x, y, w, h, t):
        ctx.rectangle(x, y, w, h)
        core.fill(ctx, "#f4f6fb")
        ctx.rectangle(x, y, w, h * 0.16)
        core.fill(ctx, "#dfe4ee")
        if avatar:
            ax, ay, ar = x + w * 0.5, y + h * 0.08, h * 0.055
            core.circle(ctx, ax, ay, ar)
            fs(ctx, PAL["e_skin"], 1.5)
            blob(ctx, [(ax - ar, ay - ar * 0.1), (ax - ar * 0.6, ay - ar * 1.0), (ax + ar * 0.2, ay - ar * 1.25),
                       (ax + ar, ay - ar * 0.3), (ax, ay - ar * 0.55)], PAL["e_hair"], 1.2)
            for sx_ in (-1, 1):
                core.circle(ctx, ax + sx_ * ar * 0.42, ay + ar * 0.1, ar * 0.3)
                core.stroke(ctx, PAL["glasses"], 1.2)
        yy = y + h * 0.22
        fsz = w * 0.14
        for side, txt, ts in msgs:
            if t < ts:
                continue
            k = core.ease_out_back(core.seg(t, ts, ts + 0.25))
            tw = text_w = _spaced_w(ctx, txt, fsz, "ui", 0.0)
            bw, bh = text_w + fsz * 1.2, fsz * 1.7
            bx = x + w * 0.06 if side == "them" else x + w * 0.94 - bw
            with core.saved(ctx, bx + (0 if side == "them" else bw), yy + bh / 2, k):
                ox = 0 if side == "them" else -bw
                rect(ctx, ox, -bh / 2, bw, bh, "#d9dde6" if side == "them" else "#4f8ef7", 0, r=bh / 2)
                core.text(ctx, txt, ox + bw / 2, fsz * 0.36, fsz, INK if side == "them" else "#ffffff", "ui")
            yy += bh + h * 0.04
            del tw
        if typing and typing[0] <= t < typing[1]:
            bw, bh = w * 0.34, fsz * 1.7
            bx = x + w * 0.94 - bw
            rect(ctx, bx, yy, bw, bh, "#4f8ef7", 0, r=bh / 2)
            for i in range(3):
                ph = 0.5 + 0.5 * math.sin(t * 7 - i * 0.9)
                core.circle(ctx, bx + bw * (0.3 + 0.2 * i), yy + bh / 2, fsz * (0.16 + 0.06 * ph))
            core.fill(ctx, "#ffffff")
    return fn


def phone(ctx, x, y, s=1.0, rot=0.0, t=0.0, screen_fn=None, on=True, buzz=0.0, glow=0.0):
    """Smartphone, front (screen) view, portrait. ANCHOR = centre.
    128 x 250 at s=1; PHONE_SCREEN is the local screen rect.
    screen_fn(ctx, sx, sy, sw, sh, t) draws the clipped screen (default: a
    lock screen "6:02"; see phone_chat_screen()). on=False = black glass.
    buzz 0..1: a vibration shiver (20 Hz, a few px) + small buzz arcs.
    glow 0..1: soft screen halo (dark rooms)."""
    jit = 0.0
    if buzz > 0:
        jit = buzz * 0.035 * math.sin(t * TAU * 20)
    with core.saved(ctx, x, y, s, rot + jit):
        if glow > 0 and on:
            core.radial_glow(ctx, 0, 0, 230, "#cfe4ff", 0.35 * glow)
        rect(ctx, -PHONE_W / 2, -PHONE_H / 2, PHONE_W, PHONE_H, "#22252f", 5, r=22)
        sx, sy, sw, sh = PHONE_SCREEN
        if on:
            ctx.save()
            core.rrect(ctx, sx, sy, sw, sh, 12)
            ctx.clip()
            (screen_fn or _phone_lock)(ctx, sx, sy, sw, sh, t)
            ctx.restore()
        else:
            rect(ctx, sx, sy, sw, sh, "#0e1016", 0, r=12)
        rect(ctx, -16, -PHONE_H / 2 + 6, 32, 8, "#0e1016", 0, r=4)
        core.poly(ctx, [(sx + sw * 0.55, sy), (sx + sw * 0.8, sy), (sx + sw * 0.3, sy + sh),
                        (sx + sw * 0.05, sy + sh)])
        core.fill(ctx, (1, 1, 1, 0.07))
    if buzz > 0.05:
        a = clamp(buzz)
        for side in (-1, 1):
            for k in range(2):
                ox = x + side * (PHONE_W / 2 + 18 + k * 16) * s
                line(ctx, [(ox, y - (30 - k * 4) * s), (ox + side * 7 * s, y), (ox, y + (30 - k * 4) * s)],
                     core.alpha(INK, a), 3.5 * s)


# ----------------------------------------------------------------------------
# MASTER RELEASE lever in a glass case (+ its pedestal console)
# ----------------------------------------------------------------------------
_RC_PIVOT = (0, -196)
_RC_ARM = 116
_RC_IMPACT = (-14, -236)


def release_handle(x, y, s=1.0, lever=0.0):
    """Centre of the MASTER RELEASE T-handle (caller coords) for a case
    anchored at (x, y) with scale s, at lever 0..1 (for hand IK)."""
    a = math.pi * core.ease_in_out(clamp(lever))
    return (x + _RC_PIVOT[0] * s, y + (_RC_PIVOT[1] - _RC_ARM * math.cos(a)) * s)


def release_impact(x, y, s=1.0):
    """Where the fist hits the glass (the shard burst origin)."""
    return (x + _RC_IMPACT[0] * s, y + _RC_IMPACT[1] * s)


def _rc_glass_rect():
    return (-112, -372, 224, 330)


def release_case(ctx, x, y, s=1.0, t=0.0, case_broken=0.0, lever=0.0, label=True, glow=1.0,
                 part="all", seed=0, light=1.0):
    """MASTER RELEASE lever in a glass case. ANCHOR = bottom centre of the
    base plate (it sits on a console). ~260 x 470 at s=1 (incl. the label).

    case_broken: 0 intact; (0, 1) cracks spread from the impact point
    (release_impact()); 1 smashed: only jagged teeth stay in the frame and a
    few bits lie on the base (throw props.shards from release_impact at the
    smash). lever 0 = UP (locked) .. 1 = DOWN (released): the arm swings
    toward the viewer through the open front (the T-handle grows a little
    mid-swing); release_handle() gives the grip point.
    part: "back" (panel + lever) and "front" (glass/teeth + frame) so hands
    can go between; "all".
    """
    b = clamp(case_broken)
    lv = clamp(lever)
    a = math.pi * core.ease_in_out(lv)
    gx, gy, gw, gh = _rc_glass_rect()
    with core.saved(ctx, x, y, s):
        def lever_draw():
            pvx, pvy = _RC_PIVOT
            hx, hy = pvx, pvy - _RC_ARM * math.cos(a)
            k = 1 + 0.4 * math.sin(a)
            line(ctx, [(pvx, pvy), (hx, hy)], INK, 26 * k)
            line(ctx, [(pvx, pvy), (hx, hy)], "#c9d1d8", 15 * k)
            core.circle(ctx, pvx, pvy, 24)
            fs(ctx, STEEL, 4.5)
            core.circle(ctx, pvx, pvy, 9)
            fs(ctx, STEEL_DK, 2.5)
            hw, hh = 150 * k, 36 * k
            rect(ctx, hx - hw / 2, hy - hh / 2, hw, hh, "#e8323f", 5, r=hh / 2)
            rect(ctx, hx - hw * 0.4, hy - hh * 0.32, hw * 0.5, hh * 0.22, "#ff8a94", 0, r=4)
        if part in ("back", "all"):
            rect(ctx, -132, -40, 264, 40, STEEL_DK, 4.5, r=6)
            for bx in (-112, 112):
                core.circle(ctx, bx, -20, 6)
                fs(ctx, STEEL_SH, 2)
            rect(ctx, -104, -364, 208, 324, "#1c2430", 4.5, r=8)
            rect(ctx, -14, -330, 28, 268, "#0b0f15", 3, r=12)
            core.text(ctx, "LOCK", 62, -300, 20, "#ff6f7a", "mono")
            core.text(ctx, "RELEASE", 58, -84, 18, "#7cf2b0", "mono")
            line(ctx, [(28, -306), (40, -306)], "#ff6f7a", 4)
            line(ctx, [(28, -90), (40, -90)], "#7cf2b0", 4)
            if b < 1:
                lever_draw()
        if part in ("front", "all"):
            # case frame
            rect(ctx, gx - 10, gy - 10, gw + 20, gh + 20, None, 0)
            if b < 1:
                rect(ctx, gx, gy, gw, gh, (0.80, 0.92, 0.98, 0.26), 0)
                core.poly(ctx, [(gx + 26, gy + 8), (gx + 66, gy + 8), (gx + 20, gy + gh - 8), (gx - 4, gy + gh - 8)])
                core.fill(ctx, (1, 1, 1, 0.28))
                core.poly(ctx, [(gx + 86, gy + 8), (gx + 100, gy + 8), (gx + 54, gy + gh - 8), (gx + 40, gy + gh - 8)])
                core.fill(ctx, (1, 1, 1, 0.18))
                if b > 0:
                    ix, iy = _RC_IMPACT
                    for i in range(9):
                        an = i / 9 * TAU + hash01(i, seed + 3)
                        L = (50 + 110 * hash01(i, seed + 4)) * min(1.0, b * 1.6)
                        mx = ix + math.cos(an) * L * 0.5 + (hash01(i, seed + 5) - 0.5) * 14
                        my = iy + math.sin(an) * L * 0.5
                        line(ctx, [(ix, iy), (mx, my), (ix + math.cos(an + 0.15) * L, iy + math.sin(an + 0.15) * L)],
                             (1, 1, 1, 0.95), 3)
                    if b > 0.35:
                        for rr in (26, 58):
                            ctx.new_sub_path()
                            ctx.arc(ix, iy, rr * min(1.0, b * 1.4), 0.3, 2.4)
                            core.stroke(ctx, (1, 1, 1, 0.85), 2.5)
                    core.circle(ctx, ix, iy, 8)
                    core.fill(ctx, (1, 1, 1, 0.9))
            else:
                # smashed: jagged teeth along the frame + bits on the base
                teeth = []
                for i in range(7):
                    u = (i + 0.5) / 7
                    L = 24 + 40 * hash01(i, seed + 7)
                    teeth.append([(gx + gw * (u - 0.07), gy), (gx + gw * (u + 0.07), gy),
                                  (gx + gw * (u + 0.02 * (hash01(i, seed + 8) - 0.5)), gy + L)])
                    L2 = 16 + 30 * hash01(i, seed + 9)
                    teeth.append([(gx + gw * (u - 0.06), gy + gh), (gx + gw * (u + 0.06), gy + gh),
                                  (gx + gw * u, gy + gh - L2)])
                for i in range(6):
                    v = (i + 0.5) / 6
                    for (ex, sgn) in ((gx, 1), (gx + gw, -1)):
                        L = 18 + 36 * hash01(i * 2 + (sgn > 0), seed + 10)
                        teeth.append([(ex, gy + gh * (v - 0.07)), (ex, gy + gh * (v + 0.07)),
                                      (ex + sgn * L, gy + gh * v)])
                for tp in teeth:
                    core.poly(ctx, tp)
                core.fill(ctx, (0.82, 0.93, 0.99, 0.55))
                for tp in teeth:
                    core.poly(ctx, tp)
                core.stroke(ctx, (1, 1, 1, 0.9), 2)
                for i in range(5):
                    with core.saved(ctx, -90 + 45 * i + 10 * hash01(i, seed + 12), -46, 0.8, hash01(i, seed + 13) * 3):
                        polyf(ctx, [(0, -10), (10, 6), (-8, 7)], "#dff3ff", 2)
                lever_draw()
            # steel frame
            ctx.rectangle(gx - 12, gy - 12, gw + 24, gh + 24)
            ctx.rectangle(gx + gw, gy, -gw, gh)
            core.fill(ctx, STEEL)
            rect(ctx, gx - 12, gy - 12, gw + 24, gh + 24, None, 4.5)
            rect(ctx, gx, gy, gw, gh, None, 3)
            for (cx_, cy_) in ((gx - 4, gy - 4), (gx + gw + 4, gy - 4), (gx - 4, gy + gh + 4), (gx + gw + 4, gy + gh + 4)):
                core.circle(ctx, cx_, cy_, 4)
                core.fill(ctx, STEEL_DK)
            if label:
                rect(ctx, -134, gy - 74, 268, 54, "#c2253c", 4.5, r=8)
                core.text(ctx, "MASTER RELEASE", 0, gy - 37, 27, "#ffffff", "ui")
        if light < 1:
            ctx.rectangle(-140, -460, 280, 460)
            core.fill(ctx, core.alpha("#03070b", 0.85 * (1 - clamp(light))))


def release_console(ctx, x, y, s=1.0, t=0.0, case_broken=0.0, lever=0.0, alarm=0.0, part="all",
                    seed=0):
    """Pedestal console carrying the MASTER RELEASE case. ANCHOR = floor
    point under its middle. ~380 x 1010 at s=1: pedestal top (= case
    anchor) at y - 540 s, so the T-handle is at shoulder height of an adult
    when UP and at the waist when DOWN. part "back" / "front" / "all" as in
    release_case (the pedestal is drawn with "back"). alarm 0..1 turns the
    status lamps red."""
    with core.saved(ctx, x, y, s):
        if part in ("back", "all"):
            polyf(ctx, [(-176, 0), (176, 0), (150, -520), (-150, -520)], "#2f3846", 6)
            polyf(ctx, [(60, 0), (176, 0), (150, -520), (50, -520)], "#262e3a", 0)
            polyf(ctx, [(-176, 0), (176, 0), (150, -520), (-150, -520)], None, 6)
            hazard_band(ctx, -146, -506, 292, 30, step=36, lw=3.5)
            rect(ctx, -164, -546, 328, 30, STEEL, 5, r=6)
            rect(ctx, -110, -440, 220, 120, "#1b222c", 4, r=10)
            for k in range(4):
                col = PAL["safe"] if (k < 2 and lever < 0.9) else PAL["warn"]
                if lever >= 0.9:
                    col = PAL["safe"]
                if alarm > 0:
                    col = mixc(col, PAL["danger"], clamp(alarm))
                core.circle(ctx, -66 + k * 44, -400, 12)
                fs(ctx, col, 3)
            for k in range(3):
                line(ctx, [(-90, -360 + k * 14), (-90 + 90 + 60 * hash01(k, 5), -360 + k * 14)], PAL["hush"], 4)
            rect(ctx, -120, -110, 240, 60, "#232b36", 4, r=8)
            core.text(ctx, "SHAFT A — ALL PODS", 0, -72, 19, "#9fb3c4", "mono")
            ell(ctx, 0, 0, 190, 16, core.alpha(INK, 0.35), 0)
    release_case(ctx, x, y - 540 * s, s, t, case_broken, lever, part=part, seed=seed)


def release_console_handle(x, y, s=1.0, lever=0.0):
    """T-handle centre for a release_console anchored at floor (x, y)."""
    return release_handle(x, y - 540 * s, s, lever)


def release_console_impact(x, y, s=1.0):
    return release_impact(x, y - 540 * s, s)


# ----------------------------------------------------------------------------
# LOCKDOWN button, SHAFT POWER switch
# ----------------------------------------------------------------------------
def lockdown_button(ctx, x, y, s=1.0, pressed=0.0, t=0.0, glow=0.0, label=True):
    """Big red LOCKDOWN mushroom button in a hazard-striped collar.
    ANCHOR = base centre on its surface. ~200 x 150 at s=1 (+ the label
    plate below the base). pressed 0..1 sinks the cap; glow 0..1 red halo
    (lit after the press)."""
    p = clamp(pressed)
    with core.saved(ctx, x, y, s):
        if glow > 0:
            core.radial_glow(ctx, 0, -50, 170, PAL["danger"], 0.45 * glow)
        ell(ctx, 0, 0, 100, 28, "#2a3240", 5)
        ctx.save()
        core.ellipse(ctx, 0, -10, 92, 26)
        ctx.clip()
        hazard_band(ctx, -100, -40, 200, 60, step=30, lw=0)
        ctx.restore()
        core.ellipse(ctx, 0, -10, 92, 26)
        core.stroke(ctx, INK, 4.5)
        rect(ctx, -54, -40 + 14 * p, 108, 34, "#3a4250", 4.5, r=8)
        top = -40 - 66 * (1 - 0.8 * p) + 14 * p
        ctx.move_to(-74, -34 + 14 * p)
        ctx.curve_to(-80, top - 10, 80, top - 10, 74, -34 + 14 * p)
        ctx.curve_to(40, -22 + 14 * p, -40, -22 + 14 * p, -74, -34 + 14 * p)
        fs(ctx, "#e8263c", 5)
        ell(ctx, -22, top + 18, 24, 9, "#ff8a94", 0, rot=-0.2)
        if label:
            rect(ctx, -96, 22, 192, 44, "#1b1d27", 4, r=6)
            spaced_text(ctx, "LOCKDOWN", 0, 54, 26, HAZ_Y, "ui", 0.12)


def power_switch(ctx, x, y, s=1.0, on=1.0, label="SHAFT POWER", t=0.0):
    """Wall/console panel with a big toggle switch. ANCHOR = panel centre.
    ~200 x 280 at s=1. on 1 = lever UP (ON, green lamp) .. 0 = DOWN (OFF,
    red lamp); animate on for the flip. Returns the lever tip (where a
    fingertip rests) in caller coordinates."""
    o = clamp(on)
    a = math.pi * (1 - core.ease_in_out(o))
    with core.saved(ctx, x, y, s):
        rect(ctx, -100, -140, 200, 280, "#2a3240", 5, r=12)
        rect(ctx, -86, -128, 172, 48, "#d9dee3", 3.5, r=6)
        tsz = min(25.0, 25.0 * 150 / max(1.0, _spaced_w(ctx, label, 25, "ui", 0.0)))
        core.text(ctx, label, 0, -95, tsz, "#1b1d27", "ui")
        core.text(ctx, "ON", 52, -46, 18, "#7cf2b0", "mono")
        core.text(ctx, "OFF", 52, 74, 18, "#ff6f7a", "mono")
        rect(ctx, -34, -40, 68, 120, "#1b222c", 4, r=10)
        bx, by = 0, 20
        tx, ty = bx, by - 64 * math.cos(a)
        k = 1 + 0.3 * math.sin(a)
        line(ctx, [(bx, by), (tx, ty)], INK, 22 * k)
        line(ctx, [(bx, by), (tx, ty)], STEEL_HI, 12 * k)
        core.circle(ctx, tx, ty, 13 * k)
        fs(ctx, "#f4f6f8", 4)
        core.circle(ctx, bx, by, 16)
        fs(ctx, STEEL, 4)
        lamp = mixc(PAL["danger"], PAL["safe"], o)
        core.radial_glow(ctx, -60, 104, 34, lamp, 0.6)
        core.circle(ctx, -60, 104, 11)
        fs(ctx, lamp, 3)
    return (x + tx * s, y + ty * s)


# ----------------------------------------------------------------------------
# the Boss's tall high-backed swivel chair
# ----------------------------------------------------------------------------
BOSS_CHAIR_SEAT = 240     # seat top above the floor at s=1 (Boss SEAT_H 233)
BOSS_CHAIR_TOP = 1010     # back top above the floor at s=1


def boss_chair(ctx, x, y, s=1.0, turn=0.0, part="all", t=0.0, rim=None, dir=1, rim_a=0.85):
    """The Boss's very tall high-backed swivel chair. ANCHOR = floor point
    under the seat centre.

    turn 0 = facing AWAY (we see the tall back: it hides a sitter
    completely), 0.5 = profile (facing screen-right for dir=+1, left for
    -1), 1 = facing the camera. Seat top at BOSS_CHAIR_SEAT*s, back top at
    BOSS_CHAIR_TOP*s. part "behind" (draw before the sitter) / "front"
    (after the sitter) / "all": whichever pieces are nearer the camera at
    this turn go in "front". rim = rim-light colour along the edges (the
    monitor glow behind it; None = cool teal, False = none).
    """
    psi = math.pi * (1 - clamp(turn))       # 0 = facing camera
    sp, cp = math.sin(psi) * dir, math.cos(psi)
    rimc = "#7fe8ff" if rim is None else rim
    leather, leather_sh, leather_hi = "#2a2e3c", "#20232e", "#3b4154"
    d = 120.0
    bw = 380.0
    th = 84.0
    back_x = -d * sp
    back_depth = -d * cp                   # > 0: back is nearer the camera than the sitter
    vis_w = max(th, bw * abs(cp) + th * abs(sp))
    seat_y = -BOSS_CHAIR_SEAT
    top = -BOSS_CHAIR_TOP
    show_front_face = cp > 0.0             # cushion side toward us

    def rim_stroke(path_fn, w=10):
        if rimc:
            path_fn()
            core.stroke(ctx, core.alpha(rimc, rim_a), w)

    def draw_base():
        rect(ctx, -16, seat_y + 30, 32, BOSS_CHAIR_SEAT - 60, "#4a5060", 4)
        ell(ctx, 0, -14, 160, 26, "#1b1d27", 5)
        ell(ctx, 0, -20, 120, 16, "#2f3442", 0)
        rim_stroke(lambda: core.ellipse(ctx, 0, -14, 160, 26), 6)
        ell(ctx, 0, -14, 160, 26, None, 4)

    def draw_seat():
        sw = 160 + 30 * abs(cp)
        ell(ctx, 0, seat_y + 18, sw, 40, leather_sh, 5)
        ell(ctx, 0, seat_y, sw - 6, 34, leather, 4.5)
        ell(ctx, 0, seat_y - 6, sw - 50, 14, leather_hi, 0)

    def back_path():
        bx0 = back_x - vis_w / 2
        h = BOSS_CHAIR_TOP - BOSS_CHAIR_SEAT + 30
        r = min(70, vis_w / 2)
        core.rrect(ctx, bx0, top, vis_w, h, r)

    def draw_back():
        back_path()
        fs(ctx, leather if show_front_face or abs(cp) < 0.2 else leather_sh, 6)
        bx0 = back_x - vis_w / 2
        if abs(cp) > 0.2:
            if show_front_face:
                # tufted cushion
                rect(ctx, bx0 + vis_w * 0.12, top + 60, vis_w * 0.76, BOSS_CHAIR_TOP - BOSS_CHAIR_SEAT - 110,
                     leather_hi, 4, r=40 * abs(cp))
                for i in range(3):
                    for j in range(5):
                        core.circle(ctx, back_x + (i - 1) * vis_w * 0.24, top + 150 + j * 150, 6)
                core.fill(ctx, leather_sh)
            else:
                for i in (-1, 0, 1):
                    line(ctx, [(back_x + i * vis_w * 0.26, top + 70), (back_x + i * vis_w * 0.26,
                                                                       seat_y - 40)], "#30343f", 6)
                hush_logo(ctx, back_x, top + 170, 34 * abs(cp), color="#30343f", hole=leather_sh, lw=0,
                          ring=False)
        else:
            line(ctx, [(back_x, top + 50), (back_x, seat_y - 30)], leather_hi, 5)
        rim_stroke(back_path, 10)
        back_path()
        core.stroke(ctx, INK, 5)
        # headrest wings
        rect(ctx, back_x - vis_w * 0.42, top + 6, vis_w * 0.84, 46, leather_sh, 4, r=20)

    def draw_arms(near):
        for side in (-1, 1):
            depth = side * sp                # > 0: this armrest is nearer the camera
            is_near = depth > 0.3
            if near != is_near:
                continue
            axx = side * 175 * abs(cp) - sp * 20
            w = 70 + 150 * abs(sp)
            rect(ctx, axx - w / 2, seat_y - 120, w, 30, leather_sh, 4.5, r=14)
            rect(ctx, axx - 9, seat_y - 92, 18, 76, "#4a5060", 4)

    with core.saved(ctx, x, y, s):
        back_in_front = back_depth > 1.0
        if part in ("behind", "all"):
            draw_base()
            if not back_in_front:
                draw_back()
            draw_seat()
            draw_arms(near=False)
        if part in ("front", "all"):
            if back_in_front:
                draw_back()
            draw_arms(near=True)


# ----------------------------------------------------------------------------
# crate, caged emergency lamp
# ----------------------------------------------------------------------------
def crate(ctx, x, y, s=1.0, w=420, h=360, kind="wood", stencil="HUSHCORP", seed=0, top=True,
          light=1.0):
    """Shipping crate, front view with a sliver of lid. ANCHOR = bottom
    centre. Top surface (sit / perch) at y - h*s. kind "wood" | "steel".
    stencil text (None = none)."""
    with core.saved(ctx, x, y, s):
        x0, y0 = -w / 2, -h
        if kind == "steel":
            base, sh, hi = "#4f6274", "#3d4e5e", "#6a7f92"
        else:
            base, sh, hi = "#9a7650", "#7d5d3c", "#b8946a"
        if top:
            polyf(ctx, [(x0, y0), (x0 + 26, y0 - 30), (x0 + w + 26, y0 - 30), (x0 + w, y0)], hi, 4.5)
            polyf(ctx, [(x0 + w, y0), (x0 + w + 26, y0 - 30), (x0 + w + 26, -30), (x0 + w, 0)], sh, 4.5)
        rect(ctx, x0, y0, w, h, base, 5)
        if kind == "steel":
            for k in range(1, 4):
                line(ctx, [(x0 + w * k / 4, y0 + 10), (x0 + w * k / 4, -10)], sh, 8)
            rect(ctx, x0, y0, w, 28, sh, 4)
            rect(ctx, x0, -28, w, 28, sh, 4)
        else:
            for k in range(1, 4):
                line(ctx, [(x0 + 8, y0 + h * k / 4), (x0 + w - 8, y0 + h * k / 4)], sh, 3.5)
            for (ax, ay, bx_, by_) in ((x0, y0, x0 + w, 0), (x0 + w, y0, x0, 0)):
                line(ctx, [(ax + (24 if ax < bx_ else -24), ay + 24), (bx_ + (-24 if ax < bx_ else 24), by_ - 24)],
                     INK, 30)
                line(ctx, [(ax + (24 if ax < bx_ else -24), ay + 24), (bx_ + (-24 if ax < bx_ else 24), by_ - 24)],
                     hi, 20)
            for (rx_, ry_, rw_, rh_) in ((x0, y0, w, 30), (x0, -30, w, 30), (x0, y0, 30, h), (x0 + w - 30, y0, 30, h)):
                rect(ctx, rx_, ry_, rw_, rh_, hi, 4)
        if stencil:
            sz = min(46, w * 0.11)
            ctx.save()
            core.text(ctx, stencil, 0, y0 + h * 0.56, sz, core.alpha("#1d1626", 0.55), "black")
            ctx.restore()
        if light < 1:
            ctx.rectangle(x0 - 2, y0 - 34, w + 32, h + 36)
            core.fill(ctx, core.alpha("#03070b", 0.85 * (1 - clamp(light))))
    return y - h * s


def cage_lamp(ctx, x, y, s=1.0, on=1.0, color="#ffb35a", down=True, halo=True):
    """Caged emergency/work lamp on a wall bracket. ANCHOR = the bracket on
    the wall; the lamp hangs below it (down=True) or sits above it. on 0..1
    lights the bulb (+ a small halo if halo=True; sets bake the big light
    pools)."""
    on = clamp(float(on))
    sg = 1 if down else -1
    with core.saved(ctx, x, y, s):
        rect(ctx, -22, -14, 44, 28, STEEL_DK, 4, r=6)
        line(ctx, [(0, 0), (0, sg * 40)], INK, 12)
        line(ctx, [(0, 0), (0, sg * 40)], STEEL_SH, 6)
        cy = sg * 92
        if halo and on > 0.02:
            core.radial_glow(ctx, 0, cy, 120, color, 0.55 * on)
        rect(ctx, -34, sg * 40 - (0 if down else 16), 68, 16, STEEL_DK, 4, r=4)
        bulb = mixc("#5b5048", "#fff1c9", on)
        ell(ctx, 0, cy, 30, 40, bulb, 3.5)
        if on > 0.3:
            ell(ctx, 0, cy, 16, 24, core.alpha("#ffffff", 0.85 * on), 0)
        for k in (-1, 0, 1):
            curve(ctx, [(k * 14 - 22 * (k != 0) * k, sg * 50), (k * 40, cy), (k * 12, cy + sg * 46)], "#3a3f4a", 4.5)
        ell(ctx, 0, cy, 38, 46, None, 4.5, sc="#3a3f4a")
        core.circle(ctx, 0, cy + sg * 48, 7)
        fs(ctx, STEEL_DK, 3)
