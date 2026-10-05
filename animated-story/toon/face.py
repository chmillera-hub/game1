"""Eyes, brows and mouths shared by every character."""
import math
import cairo
from .draw import OUT, LW, TAU, ell, fs, fill, src, line, poly, shade, hexc

WHITE = (1, 1, 1)
PUPIL = (0.08, 0.07, 0.1)
MOUTH_IN = hexc("#5b1a24")
TONGUE = hexc("#e8707e")


def _lid(c, x, y, rx, ry, skin, top_cut, slant):
    """Fill a skin-coloured lid over the eye. top_cut 0..1 = how far down; slant tilts it."""
    if top_cut <= 0:
        return
    yy = y - ry + 2 * ry * top_cut
    c.move_to(x - rx * 1.4, y - ry * 1.6)
    c.line_to(x + rx * 1.4, y - ry * 1.6)
    c.line_to(x + rx * 1.4, yy - slant * ry)
    c.line_to(x - rx * 1.4, yy + slant * ry)
    c.close_path()
    fill(c, skin)
    # lid line
    line(c, x - rx * 1.05, yy + slant * ry * 0.75, x + rx * 1.05, yy - slant * ry * 0.75, OUT, LW * 0.9)


def eye(c, x, y, rx, ry, S, side, skin, iris=None):
    """side: -1 for screen-left eye, +1 for screen-right eye."""
    kind = S.eyes
    look, looky = S.look, S.looky
    blink = S.blink
    if kind in ("happy",):
        c.move_to(x - rx, y + ry * 0.25)
        c.curve_to(x - rx * 0.6, y - ry * 0.9, x + rx * 0.6, y - ry * 0.9, x + rx, y + ry * 0.25)
        src(c, OUT); c.set_line_width(LW * 1.3); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        return
    if kind in ("closed",) or blink > 0.85:
        line(c, x - rx, y + ry * 0.1, x + rx, y + ry * 0.1, OUT, LW * 1.2)
        return
    if kind == "squeeze":  # >_<
        d = 1 if side < 0 else -1
        c.move_to(x - rx * d, y - ry * 0.7)
        c.line_to(x + rx * d * 0.9, y)
        c.line_to(x - rx * d, y + ry * 0.7)
        src(c, OUT); c.set_line_width(LW * 1.3); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
        return
    if kind == "spiral":
        ell(c, x, y, rx, ry)
        fs(c, WHITE)
        c.save(); c.translate(x, y)
        n = 60
        rot = S.get("_t", 0) * 6 * side
        for i in range(n):
            a = i / n * TAU * 2.6 + rot
            r = (i / n) * min(rx, ry) * 0.9
            px, py = math.cos(a) * r, math.sin(a) * r
            (c.move_to if i == 0 else c.line_to)(px, py)
        src(c, OUT); c.set_line_width(3); c.stroke(); c.restore()
        return
    if kind == "dots":
        ell(c, x + look * rx * 0.3, y + looky * ry * 0.3, rx * 0.22, rx * 0.22)
        fill(c, PUPIL)
        return

    sx = {"wide": 1.22, "stare": 1.0, "warm": 1.08}.get(kind, 1.0)
    erx, ery = rx * sx, ry * sx
    pup = {"wide": 0.24, "stare": 0.22, "warm": 0.62, "open": 0.45, "teary": 0.6}.get(kind, 0.45)
    ell(c, x, y, erx, ery)
    src(c, WHITE); c.fill_preserve()
    c.save(); c.clip()
    px = x + look * erx * 0.45
    py = y + looky * ery * 0.45
    if kind in ("warm", "teary") and iris:
        ell(c, px, py, erx * pup, erx * pup * 1.05)
        fill(c, iris)
        ell(c, px, py, erx * pup * 0.55, erx * pup * 0.58)
        fill(c, PUPIL)
        ell(c, px - erx * 0.22, py - ery * 0.25, erx * 0.2, erx * 0.2)
        fill(c, WHITE)
        ell(c, px + erx * 0.18, py + ery * 0.15, erx * 0.09, erx * 0.09)
        fill(c, WHITE)
        if kind == "teary":
            c.rectangle(x - erx, y + ery * 0.35, erx * 2, ery)
            src(c, (0.55, 0.8, 1.0), 0.45); c.fill()
    else:
        ell(c, px, py, erx * pup, erx * pup)
        fill(c, PUPIL)
        ell(c, px - erx * pup * 0.35, py - erx * pup * 0.35, erx * pup * 0.3, erx * pup * 0.3)
        fill(c, WHITE)
    # lids
    cut, slant = 0.0, 0.0
    if kind == "half":
        cut = 0.5
    elif kind == "stare":
        cut = 0.32
    elif kind == "angry":
        cut, slant = 0.3, 0.45 * side
    elif kind == "sad":
        cut, slant = 0.25, -0.45 * side
    elif kind == "squint":
        cut = 0.62
    elif kind == "roll":
        cut = 0.35
    cut = max(cut, blink)
    _lid(c, x, y, erx, ery, skin, cut, slant)
    c.restore()
    ell(c, x, y, erx, ery)
    src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()
    if kind == "squint":
        # lower lid squeeze
        c.move_to(x - erx, y + ery * 0.55)
        c.curve_to(x - erx * 0.3, y + ery * 0.2, x + erx * 0.3, y + ery * 0.2, x + erx, y + ery * 0.55)
        src(c, OUT); c.set_line_width(LW * 0.8); c.stroke()


def brows(c, cx, y, sep, w, S, col=OUT, thick=LW * 1.4):
    b = S.brow
    raise_ = S.browy
    if S.eyes in ("wide",):
        raise_ -= 6
    for side in (-1, 1):
        x = cx + side * sep
        inner = x - side * w / 2
        outer = x + side * w / 2
        # brow>0 worried (inner up), brow<0 angry (inner down)
        yi = y + raise_ - b * 10
        yo = y + raise_ + b * 4
        c.move_to(outer, yo)
        c.curve_to(x, min(yi, yo) - 6, x, min(yi, yo) - 6, inner, yi)
        src(c, col); c.set_line_width(thick); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()


def mouth(c, x, y, w, S, lip=None):
    kind = S.mouth
    talk = max(0.0, min(1.0, S.talk))
    h_open = w * 0.75 * talk
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)

    def open_shape(top_curve, depth, width, smile=1.0):
        # D-shaped open mouth: flat-ish top, round bottom
        c.move_to(x - width / 2, y - top_curve)
        c.curve_to(x - width / 4, y + top_curve * 0.3 * smile, x + width / 4, y + top_curve * 0.3 * smile,
                   x + width / 2, y - top_curve)
        c.curve_to(x + width / 2, y + depth, x - width / 2, y + depth, x - width / 2, y - top_curve)
        c.close_path()
        src(c, MOUTH_IN); c.fill_preserve()
        c.save(); c.clip()
        ell(c, x, y + depth * 0.95, width * 0.32, depth * 0.45)
        fill(c, TONGUE)
        c.rectangle(x - width / 2, y - top_curve - 4, width, max(6, depth * 0.22) + 4)
        fill(c, (1, 1, 1))
        c.restore()
        src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()

    if kind == "scream":
        hh = w * (1.1 + 0.35 * talk)
        ell(c, x, y + hh * 0.35, w * 0.55, hh * 0.6)
        src(c, MOUTH_IN); c.fill_preserve()
        c.save(); c.clip()
        ell(c, x, y + hh * 0.75, w * 0.35, hh * 0.25); fill(c, TONGUE)
        ell(c, x, y - hh * 0.12, w * 0.07, hh * 0.12); fill(c, TONGUE)
        c.restore()
        src(c, OUT); c.set_line_width(LW); c.stroke()
        return
    if kind == "o":
        r = w * (0.22 + 0.25 * talk)
        ell(c, x, y + r * 0.4, r, r * 1.2)
        src(c, MOUTH_IN); c.fill_preserve(); src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()
        return
    if kind == "grimace":
        hh = w * 0.28 + h_open * 0.4
        c.rectangle(x - w / 2, y - hh / 2, w, hh)
        src(c, (1, 1, 1)); c.fill_preserve(); src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()
        for i in range(1, 5):
            line(c, x - w / 2 + w * i / 5, y - hh / 2, x - w / 2 + w * i / 5, y + hh / 2, OUT, 2.5)
        line(c, x - w / 2, y, x + w / 2, y, OUT, 2.5)
        return
    if kind == "wobbly":
        c.move_to(x - w / 2, y)
        n = 6
        for i in range(1, n + 1):
            c.line_to(x - w / 2 + w * i / n, y + (5 if i % 2 else -5))
        src(c, OUT); c.set_line_width(LW); c.stroke()
        if talk > 0.15:
            ell(c, x, y + 6, w * 0.22, h_open * 0.5 + 3)
            src(c, MOUTH_IN); c.fill_preserve(); src(c, OUT); c.set_line_width(3); c.stroke()
        return
    if kind == "grin":
        open_shape(w * 0.08, w * 0.45 + h_open * 0.5, w * 1.1)
        return
    if kind == "frown":
        if talk > 0.12:
            c.move_to(x - w * 0.4, y + w * 0.2)
            c.curve_to(x - w * 0.3, y - w * 0.15 - h_open * 0.2, x + w * 0.3, y - w * 0.15 - h_open * 0.2,
                       x + w * 0.4, y + w * 0.2)
            c.curve_to(x + w * 0.2, y + w * 0.2 + h_open * 0.35, x - w * 0.2, y + w * 0.2 + h_open * 0.35,
                       x - w * 0.4, y + w * 0.2)
            c.close_path()
            src(c, MOUTH_IN); c.fill_preserve(); src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()
        else:
            c.move_to(x - w / 2, y + w * 0.18)
            c.curve_to(x - w / 4, y - w * 0.12, x + w / 4, y - w * 0.12, x + w / 2, y + w * 0.18)
            src(c, OUT); c.set_line_width(LW); c.stroke()
        return
    if kind == "smirk":
        if talk > 0.12:
            open_shape(w * 0.02, h_open * 0.7 + 4, w * 0.75)
        else:
            c.move_to(x - w * 0.45, y + 2)
            c.curve_to(x - w * 0.1, y + 8, x + w * 0.25, y + 2, x + w * 0.5, y - w * 0.2)
            src(c, OUT); c.set_line_width(LW); c.stroke()
        return
    if kind == "flat":
        if talk > 0.12:
            ell(c, x, y + h_open * 0.25, w * 0.32, h_open * 0.45 + 3)
            src(c, MOUTH_IN); c.fill_preserve(); src(c, OUT); c.set_line_width(LW * 0.9); c.stroke()
        else:
            line(c, x - w * 0.4, y, x + w * 0.4, y, OUT, LW)
        return
    if kind == "pout":
        ell(c, x, y, w * 0.18, w * 0.12)
        src(c, shade(TONGUE, 0.8)); c.fill_preserve(); src(c, OUT); c.set_line_width(3); c.stroke()
        return
    # smile (default)
    if talk > 0.12:
        open_shape(w * 0.05, h_open * 0.85 + w * 0.12, w * 0.9)
    else:
        c.move_to(x - w / 2, y - w * 0.08)
        c.curve_to(x - w / 4, y + w * 0.28, x + w / 4, y + w * 0.28, x + w / 2, y - w * 0.08)
        src(c, OUT); c.set_line_width(LW); c.stroke()


def sweat(c, x, y, n, t, size=14):
    for i in range(int(math.ceil(n))):
        a = min(1.0, n - i)
        drop_t = (t * 0.6 + i * 0.37) % 1.0
        dx = x + (i % 2) * size * 2.2 - size
        dy = y + drop_t * size * 3 + i * size
        c.move_to(dx, dy - size * 1.3)
        c.curve_to(dx + size * 0.9, dy - size * 0.1, dx + size * 0.6, dy + size * 0.8, dx, dy + size * 0.8)
        c.curve_to(dx - size * 0.6, dy + size * 0.8, dx - size * 0.9, dy - size * 0.1, dx, dy - size * 1.3)
        c.close_path()
        src(c, (0.6, 0.85, 1.0), a); c.fill_preserve()
        src(c, (0.2, 0.4, 0.6), a); c.set_line_width(2.5); c.stroke()


def tears(c, x, y, amt, t, length=90):
    """A single wobbly tear stream starting under an eye at x,y."""
    if amt <= 0:
        return
    wob = math.sin(t * 9 + x) * 3
    c.move_to(x, y)
    c.curve_to(x + 4 + wob, y + length * 0.4 * amt, x - 4 - wob, y + length * 0.7 * amt, x + wob, y + length * amt)
    src(c, (0.45, 0.75, 1.0), 0.85)
    c.set_line_width(9)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.stroke()
