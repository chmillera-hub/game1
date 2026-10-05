"""Low-level cairo drawing helpers shared by characters, sets and overlays."""
import math
import cairo

OUT = (0.12, 0.10, 0.15)  # outline ink
LW = 5.0
TAU = math.pi * 2


def hexc(h, a=None):
    h = h.lstrip("#")
    rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return rgb if a is None else rgb + (a,)


def shade(col, f):
    """Darken (f<1) or lighten (f>1) an rgb tuple."""
    if f < 1:
        return tuple(max(0.0, c * f) for c in col[:3])
    return tuple(min(1.0, c + (1 - c) * (f - 1)) for c in col[:3])


def src(c, col, a=1.0):
    if len(col) == 4:
        c.set_source_rgba(*col)
    elif a < 1:
        c.set_source_rgba(col[0], col[1], col[2], a)
    else:
        c.set_source_rgb(*col)


def ell(c, x, y, rx, ry, a0=0, a1=TAU):
    c.save()
    c.translate(x, y)
    c.scale(max(rx, 0.01), max(ry, 0.01))
    c.arc(0, 0, 1, a0, a1)
    c.restore()


def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def fs(c, col, lw=LW, out=OUT, a=1.0):
    """Fill current path with col then outline it."""
    src(c, col, a)
    c.fill_preserve()
    if lw > 0:
        src(c, out, a)
        c.set_line_width(lw)
        c.stroke()
    else:
        c.new_path()


def fill(c, col, a=1.0):
    src(c, col, a)
    c.fill()


def poly(c, pts, close=True):
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    if close:
        c.close_path()


def line(c, x0, y0, x1, y1, col=OUT, w=LW, cap=cairo.LINE_CAP_ROUND):
    c.move_to(x0, y0)
    c.line_to(x1, y1)
    src(c, col)
    c.set_line_width(w)
    c.set_line_cap(cap)
    c.stroke()


def bend_point(x0, y0, x1, y1, bend, cx_body=0.0):
    """Midpoint pushed perpendicular by `bend`, on the side away from the body centre."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    a = (mx + nx * bend, my + ny * bend)
    b = (mx - nx * bend, my - ny * bend)
    # prefer outward (away from body centre); tie-break downward
    sa = abs(a[0] - cx_body) + 0.15 * a[1]
    sb = abs(b[0] - cx_body) + 0.15 * b[1]
    return a if sa >= sb else b


def hose(c, pts_list, width, col, out=OUT, lw=LW):
    """Draw rubber-hose limbs. pts_list: list of polylines (each a list of points).
    Outline pass for all first, then fill pass, so joints don't show seams."""
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    for pass_ in (0, 1):
        for item in pts_list:
            pts, w, colr = item if isinstance(item, tuple) else (item, width, col)
            c.move_to(*pts[0])
            if len(pts) == 3:
                c.curve_to(pts[1][0], pts[1][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1])
            else:
                for p in pts[1:]:
                    c.line_to(*p)
            if pass_ == 0:
                src(c, out)
                c.set_line_width(w + 2 * lw)
            else:
                src(c, colr)
                c.set_line_width(w)
            c.stroke()


def text(c, s, x, y, size, family="Fredoka", col=(1, 1, 1), outline=OUT, ow=0.0,
         align="center", bold=True, valign="baseline", alpha=1.0):
    c.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)
    ext = c.text_extents(s)
    if align == "center":
        tx = x - (ext.width / 2 + ext.x_bearing)
    elif align == "right":
        tx = x - (ext.width + ext.x_bearing)
    else:
        tx = x
    ty = y
    if valign == "middle":
        ty = y - (ext.height / 2 + ext.y_bearing)
    c.move_to(tx, ty)
    c.text_path(s)
    if ow > 0:
        src(c, outline, alpha)
        c.set_line_width(ow)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke_preserve()
    src(c, col, alpha)
    c.fill()
    return ext


def text_width(c, s, size, family="Fredoka", bold=True):
    c.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)
    return c.text_extents(s).x_advance


def wrap(c, s, size, maxw, family="Fredoka", bold=True):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(c, trial, size, family, bold) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def radial(x, y, r, col_in, col_out):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *col_in)
    g.add_color_stop_rgba(1, *col_out)
    return g


def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col in stops:
        if len(col) == 3:
            g.add_color_stop_rgb(off, *col)
        else:
            g.add_color_stop_rgba(off, *col)
    return g


def cloud(c, x, y, w, h, bumps=9, new=True):
    """Thought-bubble cloud path centred on x,y."""
    if new:
        c.new_path()
    pts = []
    for i in range(bumps):
        a = TAU * i / bumps
        pts.append((x + math.cos(a) * w / 2, y + math.sin(a) * h / 2))
    c.new_sub_path()
    for i in range(bumps):
        a0 = TAU * i / bumps
        a1 = TAU * (i + 1) / bumps
        mx = x + math.cos((a0 + a1) / 2) * w / 2 * 1.12
        my = y + math.sin((a0 + a1) / 2) * h / 2 * 1.16
        p0 = pts[i]
        p1 = pts[(i + 1) % bumps]
        if i == 0:
            c.move_to(*p0)
        c.curve_to(mx + (p0[0] - x) * 0.18, my + (p0[1] - y) * 0.18,
                   mx + (p1[0] - x) * 0.18, my + (p1[1] - y) * 0.18, *p1)
    c.close_path()


def star(c, x, y, r_out, r_in, n=5, rot=-math.pi / 2):
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / n
        px, py = x + math.cos(a) * r, y + math.sin(a) * r
        if i == 0:
            c.move_to(px, py)
        else:
            c.line_to(px, py)
    c.close_path()


def heart(c, x, y, s):
    c.move_to(x, y + s * 0.35)
    c.curve_to(x - s * 1.1, y - s * 0.4, x - s * 0.45, y - s * 1.05, x, y - s * 0.45)
    c.curve_to(x + s * 0.45, y - s * 1.05, x + s * 1.1, y - s * 0.4, x, y + s * 0.35)
    c.close_path()
