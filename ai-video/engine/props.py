"""Shared backgrounds and props for "Nice Try, My Guy".

Everything draws in the LOGICAL 1080x1920 space (origin top-left, y down) on
whatever cairo context the renderer hands us (already scaled). Flat colours,
dark `ink` outlines (~5 px), motion only where it matters (bitrate budget).

Coordinate conventions used below
---------------------------------
* "(x, y) = centre"      -> the prop is centred on the point.
* "(x, y) = top-left"    -> rect-like props (bubbles, walls, documents).
* "(x, y) = bottom-centre" -> things that sit on a surface (computer, lamp, mug).
* `t` is scene-local seconds. `t_in` = when the prop pops in; nothing is drawn
  before it (functions still return their layout/height so scenes can plan).
* `s` is a uniform scale (1.0 = the "typical size" given in each docstring).

Static backgrounds (`lair_bg`, `ai_bg`) are rendered once per device scale
into an image surface and blitted (≈1-3 ms at 720x1280); only small elements
(rain in the window, a candle flame, bubbles in a flask, motes) are animated.

Content rule: props never contain real harmful specifics. Bombs are only the
classic round cartoon kind.

API index (see each docstring):
  backgrounds : lair_bg, ai_bg
  lair props  : desk, computer, keyboard, mug, skull_lamp
  chat        : chat_bubble (-> BubbleLayout), bubble_layout, typing_dots
  motif       : brick_wall (+ brick_wall_land_times), stamp (+ stamp_impact)
  vision      : future_tree (+ future_tree_layout), scroll_doc
  reactions   : emote, sparkles, x_mark, check_mark, label_tag, arrow
  screen      : split_divider, split_screen, panel, iris, flash, title_card
  extras      : cartoon_bomb, magnifier, puzzle_piece, folder
  misc        : C (colour lookup incl. COL), clear_cache
"""
import math

import cairocffi as cairo

from .core import (W, H, PAL, hexc, clamp, lerp, seg, smoothstep, ease_in, ease_out,
                   ease_in_out, ease_out_back, pop, hash01, noise1, rrect, ellipse, circle,
                   poly, smooth_path, radial_glow, set_font, text, text_width, wrap_lines,
                   saved)

INK = "ink"
LW = 5.0                      # standard prop outline width (logical px)

# extra prop colours (derived from PAL so the look stays coherent)
COL = {
    "wood": "#5a2c34", "wood_top": "#7a4048", "wood_dk": "#3c1a22", "wood_in": "#4a222b",
    "gold": PAL["monocle"], "gold_dk": "#b08a2e",
    "cork": "#c4925c", "cork_dk": "#a5743f", "frame": "#6b3f22",
    "paper": "#f6ecd6", "paper_dk": "#e2cfa6", "parch": "#f4e4c1", "parch_dk": "#dcc293",
    "sky_top": "#14254f", "sky_bot": "#2c5288", "cloud": "#1b2d58", "moon": "#eef3ff",
    "rain": "#a9c8ff", "night_hill": "#101b3c",
    "plastic": "#6a6080", "plastic_hi": "#887ea3", "plastic_dk": "#4b4462",
    "crt": "#062221", "crt_glow": PAL["lair_glow"],
    "bone": "#efe6d2", "bone_dk": "#cdbf9f", "lamp_light": "#ffd98a",
    "villain_dk": "#4e2380", "ai_dk": "#0b6f6a",
    "steel": "#8a93a8", "steel_dk": "#5d6478",
}


def C(name, a=1.0):
    """Colour lookup: COL name, PAL name or '#hex' -> rgba tuple."""
    if isinstance(name, str) and name in COL:
        return hexc(COL[name], a)
    return hexc(name, a)


def _src(ctx, c, a=1.0):
    col = C(c)
    ctx.set_source_rgba(col[0], col[1], col[2], col[3] * a)


def _fs(ctx, fc, sc=INK, w=LW, a=1.0):
    """Fill + stroke current path, then clear it."""
    if fc is not None:
        _src(ctx, fc, a)
        ctx.fill_preserve()
    if sc is not None and w > 0:
        _src(ctx, sc, a)
        ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke_preserve()
    ctx.new_path()


def _f(ctx, fc, a=1.0):
    _src(ctx, fc, a)
    ctx.fill()


def _s(ctx, sc, w, a=1.0, cap=cairo.LINE_CAP_ROUND):
    _src(ctx, sc, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def _glow(ctx, cx, cy, r, c, a=0.5):
    """radial_glow that understands COL names too."""
    col = C(c)
    radial_glow(ctx, cx, cy, r, (col[0], col[1], col[2], 1.0), a)


def _mix(c1, c2, k):
    a, b = C(c1), C(c2)
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(4))


def _text(ctx, s, x, y, size=40, color="white", font="ui", align="center", outline=None,
          outline_w=8, shadow=None):
    """core.text with COL-aware colours."""
    if shadow is not None:
        shadow = (shadow[0], shadow[1], C(shadow[2]))
    return text(ctx, s, x, y, size, C(color), font, align,
                C(outline) if outline is not None else None, outline_w, shadow=shadow)


def _lum(c):
    r, g, b, _ = C(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _txt_on(c):
    return "ink" if _lum(c) > 0.62 else "white"


# ---------------------------------------------------------------------------
# static-layer cache (per device scale)
# ---------------------------------------------------------------------------
_CACHE = {}


def _dev_scale(ctx):
    xx, yx, xy, yy, _, _ = ctx.get_matrix().as_tuple()
    return math.sqrt(abs(xx * yy - xy * yx)) or 1.0


def _cached_layer(ctx, key, draw_fn, rect=(0, 0, W, H), opaque=False):
    """Draw `draw_fn(c)` (logical coords) once into an image and blit it.

    Cache entries are keyed by `key` + device scale (from ctx.get_matrix()),
    so previews at different sizes and camera push-ins work: when the scale
    grows past a cached one a new entry with 25% headroom is rendered and
    then reused (downsampled, bilinear) until the next 25%.
    `rect` = logical area covered (x, y, w, h); outside it nothing is drawn.
    """
    s = _dev_scale(ctx)
    entries = _CACHE.setdefault(key, [])
    hit = None
    for e in entries:
        if abs(e[0] - s) < 1e-4:
            hit = e
            break
    if hit is None:
        for e in entries:
            if s <= e[0] <= s * 1.3:
                hit = e
                break
    if hit is None:
        cs = s if not entries else s * 1.25
        rx, ry, rw, rh = rect
        px0, py0 = math.floor(rx * cs + 1e-6), math.floor(ry * cs + 1e-6)
        px1, py1 = math.ceil((rx + rw) * cs - 1e-6), math.ceil((ry + rh) * cs - 1e-6)
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24 if opaque else cairo.FORMAT_ARGB32,
                                  max(1, px1 - px0), max(1, py1 - py0))
        c = cairo.Context(surf)
        c.translate(-px0, -py0)
        c.scale(cs, cs)
        draw_fn(c)
        surf.flush()
        hit = (cs, surf, px0 / cs, py0 / cs)
        entries.append(hit)
        if len(entries) > 3:
            entries.pop(0)
    cs, surf, ox, oy = hit
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(1.0 / cs, 1.0 / cs)
    pat = cairo.SurfacePattern(surf)
    pat.set_extend(cairo.EXTEND_PAD)
    pat.set_filter(cairo.FILTER_BILINEAR)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, surf.get_width(), surf.get_height())
    ctx.fill()
    ctx.restore()


def clear_cache():
    """Drop cached background layers (e.g. after editing art in a live session)."""
    _CACHE.clear()


# ---------------------------------------------------------------------------
# small shape helpers
# ---------------------------------------------------------------------------
def _star4(ctx, x, y, r, rot=0.0, pinch=0.28):
    """Four-point sparkle star path (concave sides)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.move_to(0, -r)
    for k in range(4):
        a0 = -math.pi / 2 + k * math.pi / 2
        a1 = a0 + math.pi / 2
        am = (a0 + a1) / 2
        ctx.curve_to(math.cos(am) * r * pinch, math.sin(am) * r * pinch,
                     math.cos(am) * r * pinch, math.sin(am) * r * pinch,
                     math.cos(a1) * r, math.sin(a1) * r)
    ctx.close_path()
    ctx.restore()


def _heart_path(ctx, x, y, r):
    """Heart centred near (x, y); r ~ half width."""
    ctx.move_to(x, y + r * 0.95)
    ctx.curve_to(x - r * 1.35, y + r * 0.05, x - r * 0.95, y - r * 1.05, x, y - r * 0.38)
    ctx.curve_to(x + r * 0.95, y - r * 1.05, x + r * 1.35, y + r * 0.05, x, y + r * 0.95)
    ctx.close_path()


def _partial_polyline(ctx, pts, p):
    """Path along the first fraction p (0..1) of a polyline; returns tip & dir."""
    if p <= 0 or len(pts) < 2:
        return pts[0], (1.0, 0.0)
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(lens) or 1.0
    want = total * clamp(p)
    ctx.move_to(*pts[0])
    acc = 0.0
    tip, d = pts[0], (1.0, 0.0)
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        if L <= 1e-9:
            continue
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        if acc + L >= want:
            f = (want - acc) / L
            tip = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            ctx.line_to(*tip)
            return tip, d
        ctx.line_to(*b)
        acc += L
        tip = b
    return tip, d


def _qbez(p0, p1, p2, n=24):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])
            for u in (i / n for i in range(n + 1))]


def _cbez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        u = i / n
        a, b, c_, d = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u ** 3
        out.append((a * p0[0] + b * p1[0] + c_ * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c_ * p2[1] + d * p3[1]))
    return out


def _gothic_arch(ctx, x0, x1, ys, yb, k=0.9):
    """Pointed-arch window path: straight sides from yb up to the spring line ys."""
    wd = x1 - x0
    r = k * wd
    c = (wd / 2 - r) / r
    pa = 2 * math.pi - math.acos(c)
    pb = 2 * math.pi - math.acos(-c)
    ctx.move_to(x0, yb)
    ctx.line_to(x0, ys)
    ctx.arc(x0 + r, ys, r, math.pi, pa)
    ctx.arc(x1 - r, ys, r, pb, 2 * math.pi)
    ctx.line_to(x1, yb)
    ctx.close_path()
    return ys - r * math.sin(math.acos(abs(c)))   # apex y


def _check_path(ctx, x, y, s):
    ctx.move_to(x - 0.42 * s, y + 0.02 * s)
    ctx.line_to(x - 0.12 * s, y + 0.32 * s)
    ctx.line_to(x + 0.46 * s, y - 0.34 * s)


def _x_path(ctx, x, y, s):
    ctx.move_to(x - 0.36 * s, y - 0.36 * s)
    ctx.line_to(x + 0.36 * s, y + 0.36 * s)
    ctx.move_to(x + 0.36 * s, y - 0.36 * s)
    ctx.line_to(x - 0.36 * s, y + 0.36 * s)


def _snake_emblem(ctx, x, y, s, col="gold", dk="gold_dk"):
    """Little S-shaped snake emblem (Sneakworth monogram)."""
    pts = [(x + 34 * s, y - 62 * s), (x - 6 * s, y - 70 * s), (x - 36 * s, y - 40 * s),
           (x - 14 * s, y - 6 * s), (x + 22 * s, y + 18 * s), (x + 26 * s, y + 52 * s),
           (x - 8 * s, y + 70 * s), (x - 40 * s, y + 56 * s)]
    smooth_path(ctx, pts)
    path = ctx.copy_path()
    _s(ctx, INK, 38 * s)
    ctx.append_path(path)
    _s(ctx, col, 26 * s)
    ctx.append_path(path)
    ctx.set_dash([2 * s, 16 * s])
    _s(ctx, dk, 7 * s)
    ctx.set_dash([])
    ctx.new_path()
    # head
    ellipse(ctx, x + 42 * s, y - 62 * s, 23 * s, 17 * s, 0.25)
    _fs(ctx, col, INK, 4 * s)
    circle(ctx, x + 49 * s, y - 67 * s, 4 * s)
    _f(ctx, INK)
    # tongue
    ctx.move_to(x + 63 * s, y - 56 * s)
    ctx.line_to(x + 75 * s, y - 52 * s)
    ctx.move_to(x + 75 * s, y - 52 * s)
    ctx.line_to(x + 81 * s, y - 56 * s)
    ctx.move_to(x + 75 * s, y - 52 * s)
    ctx.line_to(x + 80 * s, y - 46 * s)
    _s(ctx, "danger", 3 * s)


# ===========================================================================
# LAIR BACKGROUND
# ===========================================================================
# window geometry (logical px)
_WX0, _WX1, _WYS, _WYB = 78.0, 372.0, 430.0, 900.0
_WIN_RECT = (24, 140, 400, 820)          # cache rect for the window frame overlay
_BG_RECT = (-320, -240, W + 640, H + 480)  # static bg cache covers a margin for zoom-outs
_FLOOR_Y = 1400.0
_CANDLE = (128.0, 900.0)                 # candle base on the sill
_FLASK = (936.0, 760.0)                  # flask base on the shelf


def _lair_glass_path(ctx):
    return _gothic_arch(ctx, _WX0, _WX1, _WYS, _WYB)


def _lair_stones(c):
    rh = 112.0
    row = 0
    y0 = -264.0
    while y0 < _FLOOR_Y:
        x = -380.0 - hash01(row, 11) * 140
        i = 0
        while x < W + 340:
            bw = 170 + hash01(row * 31 + i, 12) * 130
            bx, by = x + 5, y0 + 5
            h_ = min(rh - 10, _FLOOR_Y - by - 4)
            if h_ > 12:
                rrect(c, bx, by, bw - 10, h_, 12)
                _f(c, "lair_stone")
                rrect(c, bx + 5, by + 6, bw - 15, h_ - 8, 10)
                _f(c, "lair_bg2")
                k = hash01(row * 57 + i, 13)
                if k < 0.16 and h_ > 60:
                    # little crack
                    cx_, cy_ = bx + bw * (0.3 + 0.4 * hash01(i, row)), by + 14
                    c.move_to(cx_, cy_)
                    c.line_to(cx_ + 10, cy_ + 22)
                    c.line_to(cx_ + 2, cy_ + 38)
                    c.line_to(cx_ + 14, cy_ + 56)
                    _s(c, "lair_bg", 4)
                elif k > 0.86 and h_ > 60:
                    # chipped corner
                    poly(c, [(bx + bw - 10, by + h_ - 26), (bx + bw - 10, by + h_),
                             (bx + bw - 40, by + h_)])
                    _f(c, "lair_bg")
            x += bw
            i += 1
        y0 += rh
        row += 1


def _lair_floor(c):
    X0, X1 = -340, W + 340
    c.rectangle(X0, _FLOOR_Y, X1 - X0, H + 260 - _FLOOR_Y)
    _f(c, "lair_stone_dk")
    c.rectangle(X0, _FLOOR_Y - 4, X1 - X0, 26)
    _f(c, "#1a0d2b")
    c.move_to(X0, _FLOOR_Y - 4)
    c.line_to(X1, _FLOOR_Y - 4)
    _s(c, INK, 5)
    # perspective planks
    for yy in (1470, 1560, 1680, 1840, 2040):
        c.move_to(X0, yy)
        c.line_to(X1, yy)
        _s(c, "#2f1a4a", 4)
    vx, vy = 540, 980
    for i in range(-7, 8):
        bx = 540 + i * 260
        c.move_to(vx + (bx - vx) * (_FLOOR_Y + 22 - vy) / (H - vy), _FLOOR_Y + 22)
        c.line_to(vx + (bx - vx) * (H + 240 - vy) / (H - vy), H + 240)
        _s(c, "#2f1a4a", 4)


def _lair_banner(c):
    x0, x1, y0, y1 = 438.0, 642.0, 104.0, 470.0
    cx = (x0 + x1) / 2
    # wall shadow
    poly(c, [(x0 + 12, y0 + 10), (x1 + 12, y0 + 10), (x1 + 12, y1 + 12), (cx + 12, y1 - 44),
             (x0 + 12, y1 + 12)])
    _f(c, INK, 0.35)
    # cloth
    poly(c, [(x0, y0), (x1, y0), (x1, y1), (cx, y1 - 56), (x0, y1)])
    _fs(c, "cape_in", INK, LW)
    # side shade fold
    poly(c, [(x1 - 28, y0 + 4), (x1 - 3, y0 + 4), (x1 - 3, y1 - 6), (x1 - 28, y1 - 18)])
    _f(c, "#8c0d2e")
    # gold trim
    m = 16
    poly(c, [(x0 + m, y0 + 26), (x1 - m, y0 + 26), (x1 - m, y1 - 26), (cx, y1 - 74),
             (x0 + m, y1 - 26)])
    _s(c, "gold", 5)
    _snake_emblem(c, cx, 278, 1.08)
    # rod + finials
    rrect(c, x0 - 34, y0 - 16, (x1 - x0) + 68, 18, 9)
    _fs(c, "#2b2236", INK, 4)
    for fx in (x0 - 40, x1 + 40):
        circle(c, fx, y0 - 7, 14)
        _fs(c, "gold", INK, 4)
    # hanging chains to the ceiling
    for fx in (x0 + 10, x1 - 10):
        for k in range(5):
            ellipse(c, fx, y0 - 30 - k * 22, 6, 11)
            _s(c, "#5a4a6e", 4)


def _lair_window_sky(c):
    """Glass contents: night sky, moon, stars, clouds, hills (clipped to arch)."""
    c.save()
    _lair_glass_path(c)
    c.clip()
    g = cairo.LinearGradient(0, 190, 0, _WYB)
    g.add_color_stop_rgba(0, *C("sky_top"))
    g.add_color_stop_rgba(1, *C("sky_bot"))
    c.rectangle(_WX0 - 5, 150, _WX1 - _WX0 + 10, _WYB - 140)
    c.set_source(g)
    c.fill()
    # stars
    for i in range(9):
        sx = _WX0 + 20 + hash01(i, 41) * (_WX1 - _WX0 - 40)
        sy = 250 + hash01(i, 42) * 300
        _star4(c, sx, sy, 5 + 5 * hash01(i, 43))
        _f(c, "#dfe9ff", 0.75)
    # moon (crescent via even-odd) + halo
    _glow(c, 304, 506, 110, "moon", 0.22)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    circle(c, 304, 506, 40)
    circle(c, 286, 494, 35)
    _f(c, "moon")
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    # clouds
    for (cx, cy, s) in ((150, 560, 0.9), (340, 600, 0.75), (200, 700, 1.15)):
        for (dx, dy, r) in ((-60, 10, 34), (-20, -10, 46), (30, -2, 40), (70, 14, 28),
                            (0, 20, 36)):
            circle(c, cx + dx * s, cy + dy * s, r * s)
        _f(c, "cloud")
    # distant hills + spooky tower silhouette
    c.move_to(_WX0 - 5, 820)
    c.curve_to(150, 760, 200, 770, 250, 800)
    c.curve_to(300, 770, 340, 760, _WX1 + 5, 790)
    c.line_to(_WX1 + 5, _WYB + 5)
    c.line_to(_WX0 - 5, _WYB + 5)
    c.close_path()
    _f(c, "night_hill")
    c.rectangle(300, 700, 24, 100)
    poly(c, [(294, 702), (312, 666), (330, 702)])
    _f(c, "night_hill")
    c.rectangle(308, 724, 7, 10)
    _f(c, "warn", 0.9)
    c.restore()


def _lair_window_frame(c):
    """Mullions + inner frame (drawn ABOVE the glass)."""
    cx = (_WX0 + _WX1) / 2
    c.save()
    _lair_glass_path(c)
    c.clip()
    # mullion + transoms
    c.rectangle(cx - 8, _WYS - 4, 16, _WYB - _WYS + 8)
    for yy in (_WYS - 8, _WYS + 150, _WYS + 300):
        c.rectangle(_WX0, yy, _WX1 - _WX0, 14 if yy == _WYS - 8 else 9)
    _fs(c, "#20122f", INK, 3)
    # rose window ring in the arch
    circle(c, cx, 326, 54)
    _s(c, INK, 20)
    circle(c, cx, 326, 54)
    _s(c, "#20122f", 12)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        c.move_to(cx + math.cos(a) * 54, 326 + math.sin(a) * 54)
        c.line_to(cx + math.cos(a) * 140, 326 + math.sin(a) * 140)
    _s(c, "#20122f", 7)
    circle(c, cx, 326, 14)
    _fs(c, "#20122f", INK, 3)
    # glass glints
    c.move_to(_WX0 + 22, _WYS + 40)
    c.line_to(_WX0 + 22, _WYS + 120)
    c.move_to(cx + 22, _WYS + 190)
    c.line_to(cx + 22, _WYS + 240)
    _s(c, "white", 6, 0.18)
    c.restore()
    # inner frame edge
    _lair_glass_path(c)
    _s(c, INK, 14)
    _lair_glass_path(c)
    _s(c, "#20122f", 7)


def _lair_window_surround(c):
    """Stone surround + sill (drawn BELOW the glass)."""
    # outer stone surround
    _gothic_arch(c, _WX0 - 34, _WX1 + 34, _WYS, _WYB + 4, k=0.9)
    _fs(c, "lair_stone", INK, LW)
    # inner bevel line + block joints on the jambs
    cx = (_WX0 + _WX1) / 2
    _gothic_arch(c, _WX0 - 16, _WX1 + 16, _WYS, _WYB + 4, k=0.9)
    _s(c, "lair_bg2", 4)
    for yy in (540, 680, 820):
        c.move_to(_WX0 - 34, yy)
        c.line_to(_WX0 - 16, yy)
        c.move_to(_WX1 + 16, yy)
        c.line_to(_WX1 + 34, yy)
    _s(c, INK, 4)
    # keystone
    apex = _gothic_arch(c, _WX0 - 34, _WX1 + 34, _WYS, _WYB + 4, k=0.9)
    c.new_path()
    poly(c, [(cx - 25, apex + 2), (cx + 25, apex + 2), (cx + 15, apex + 52),
             (cx - 15, apex + 52)])
    _fs(c, "lair_stone", INK, 4)
    c.move_to(cx - 18, apex + 10)
    c.line_to(cx + 18, apex + 10)
    _s(c, "#6a4a92", 4)
    # sill
    rrect(c, _WX0 - 56, _WYB - 6, _WX1 - _WX0 + 112, 36, 8)
    _fs(c, "lair_stone", INK, LW)
    c.rectangle(_WX0 - 50, _WYB + 18, _WX1 - _WX0 + 100, 8)
    _f(c, "lair_stone_dk", 0.8)
    c.move_to(_WX0 - 48, _WYB + 2)
    c.line_to(_WX1 + 48, _WYB + 2)
    _s(c, "#6a4a92", 4)


def _lair_candle_static(c):
    x, y = _CANDLE
    # dish
    ellipse(c, x, y - 6, 40, 10)
    _fs(c, "gold", INK, 4)
    # wax body w/ drips
    c.move_to(x - 14, y - 8)
    c.line_to(x - 14, y - 78)
    c.curve_to(x - 8, y - 84, x + 8, y - 84, x + 14, y - 78)
    c.line_to(x + 14, y - 8)
    c.close_path()
    _fs(c, "#f3ead2", INK, 4)
    c.move_to(x + 4, y - 80)
    c.curve_to(x + 6, y - 64, x + 10, y - 60, x + 8, y - 52)
    _s(c, "#d8cbab", 5)
    c.move_to(x, y - 82)
    c.line_to(x + 1, y - 92)
    _s(c, INK, 3)


def _lair_corkboard(c):
    x0, y0, x1, y1 = 694.0, 160.0, 1040.0, 590.0
    # shadow
    rrect(c, x0 + 12, y0 + 12, x1 - x0, y1 - y0, 10)
    _f(c, INK, 0.35)
    rrect(c, x0, y0, x1 - x0, y1 - y0, 10)
    _fs(c, "frame", INK, LW)
    rrect(c, x0 + 20, y0 + 20, x1 - x0 - 40, y1 - y0 - 40, 4)
    _fs(c, "cork", INK, 4)
    # frame highlight
    c.move_to(x0 + 8, y0 + 8)
    c.line_to(x1 - 8, y0 + 8)
    _s(c, "#8c5a33", 4)
    # cork speckles
    for i in range(70):
        sx = x0 + 28 + hash01(i, 51) * (x1 - x0 - 56)
        sy = y0 + 28 + hash01(i, 52) * (y1 - y0 - 56)
        circle(c, sx, sy, 1.6 + 2.2 * hash01(i, 53))
        _f(c, "cork_dk", 0.8)

    pins = {}

    def paper(px, py, pw, ph, rot, col, draw=None, pin=(0.5, 0.08), pin_col="danger",
              name=None):
        with saved(c, px, py, 1.0, rot):
            rrect(c, -pw / 2 + 6, -ph / 2 + 8, pw, ph, 3)
            _f(c, INK, 0.3)
            rrect(c, -pw / 2, -ph / 2, pw, ph, 3)
            _fs(c, col, INK, 3.5)
            if draw:
                draw(c, pw, ph)
        # pin position in world coords
        lx, ly = (pin[0] - 0.5) * pw, (pin[1] - 0.5) * ph
        wx = px + lx * math.cos(rot) - ly * math.sin(rot)
        wy = py + lx * math.sin(rot) + ly * math.cos(rot)
        if name:
            pins[name] = (wx, wy, pin_col)
        return wx, wy

    def polaroid(cc, pw, ph):
        rrect(cc, -pw / 2 + 10, -ph / 2 + 10, pw - 20, pw - 26, 2)
        _fs(cc, "ai_bg", INK, 2.5)
        # tiny AI face doing 😒
        rrect(cc, -34, -ph / 2 + 24, 68, 54, 14)
        _fs(cc, "ai_body", "ai_rim", 3)
        for ex in (-14, 14):
            ellipse(cc, ex, -ph / 2 + 50, 8, 9)
            _f(cc, "ai_eye")
            cc.rectangle(ex - 9, -ph / 2 + 39, 18, 9)
            _f(cc, "ai_body")
            cc.move_to(ex - 9, -ph / 2 + 48)
            cc.line_to(ex + 9, -ph / 2 + 48)
            _s(cc, "ai_rim", 2.5)
        cc.move_to(-8, -ph / 2 + 66)
        cc.line_to(8, -ph / 2 + 66)
        _s(cc, "ai_eye", 3)
        text(cc, "???", 0, ph / 2 - 12, 24, "danger", "comic")

    def blueprint(cc, pw, ph):
        # Trojan-horse doodle (the sneaky plan, cartoon)
        cc.save()
        cc.translate(-6, 4)
        rrect(cc, -38, -14, 64, 30, 6)              # body
        cc.move_to(20, -12)
        cc.line_to(34, -38)
        cc.line_to(48, -34)
        cc.line_to(42, -14)                         # neck/head
        for lx in (-28, -8, 6, 18):
            cc.move_to(lx, 16)
            cc.line_to(lx, 28)
        circle(cc, -26, 34, 6)
        circle(cc, 16, 34, 6)
        cc.move_to(-46, 40)
        cc.line_to(40, 40)
        _s(cc, "white", 2.5)
        cc.restore()
        for gy in range(-ph // 2 + 12, ph // 2, 18):
            cc.move_to(-pw / 2 + 4, gy)
            cc.line_to(pw / 2 - 4, gy)
        _s(cc, "white", 1, 0.18)
        text(cc, "PLAN A", -pw / 2 + 10, -ph / 2 + 22, 16, "white", "mono", "left")

    def sticky(cc, pw, ph):
        cc.rectangle(-pw / 2, -ph / 2, pw, 16)
        _f(cc, "#f2cf3a")
        text(cc, "PLAN B", 0, 4, 28, "ink", "comic")
        cc.move_to(-34, 22)
        cc.curve_to(-14, 16, 10, 28, 34, 20)
        _s(cc, "ink", 3)

    def lined(cc, pw, ph):
        for k in range(7):
            yy = -ph / 2 + 30 + k * 17
            cc.move_to(-pw / 2 + 8, yy)
            cc.line_to(pw / 2 - 8, yy)
        _s(cc, "#7aa7e0", 1.5, 0.8)
        for k in range(4):
            yy = -ph / 2 + 27 + k * 17
            ww = 50 + 30 * hash01(k, 61)
            cc.move_to(-pw / 2 + 14, yy)
            for j in range(6):
                cc.line_to(-pw / 2 + 14 + ww * (j + 1) / 6, yy + (3 if j % 2 else -3))
        _s(cc, "ink", 2)
        text(cc, "STEP 3:", -pw / 2 + 12, ph / 2 - 44, 18, "ink", "round", "left")
        text(cc, "???", 0, ph / 2 - 14, 30, "danger", "comic")
        ellipse(cc, 0, ph / 2 - 24, 36, 20, -0.1)
        _s(cc, "danger", 2.5)

    paper(764, 330, 112, 138, -0.09, "#fbfbf6", polaroid, name="pol")
    paper(920, 318, 148, 112, 0.06, "#2d6cb5", blueprint, name="blue")
    paper(792, 500, 112, 100, 0.07, "#ffe066", sticky, pin=(0.5, 0.12), name="sticky",
          pin_col="ai_rim")
    paper(944, 484, 124, 156, -0.05, "#f4f1e8", lined, name="lined", pin_col="safe")

    # header strip
    with saved(c, 866, 210, 1.0, -0.035):
        rrect(c, -126 + 5, -30 + 7, 252, 60, 4)
        _f(c, INK, 0.3)
        rrect(c, -126, -30, 252, 60, 4)
        _fs(c, "paper", INK, 3.5)
        text(c, "EVIL PLANS", 0, 16, 40, "danger", "title")
    for px in (752, 980):
        circle(c, px, 208 + (px - 866) * -0.035, 8)
        _fs(c, "#3a3a4a", INK, 2.5)

    # red string between pins
    order = ["pol", "blue", "lined", "sticky", "pol"]
    for a, b in zip(order, order[1:]):
        (ax, ay, _), (bx, by, _) = pins[a], pins[b]
        mx, my = (ax + bx) / 2, (ay + by) / 2 + 22
        c.move_to(ax, ay)
        c.curve_to(mx, my, mx, my, bx, by)
        _s(c, "#7d0c2a", 5)
        c.move_to(ax, ay)
        c.curve_to(mx, my, mx, my, bx, by)
        _s(c, "danger", 3)
    for (px, py, pc) in pins.values():
        circle(c, px + 2, py + 3, 9)
        _f(c, INK, 0.4)
        circle(c, px, py, 9)
        _fs(c, pc, INK, 2.5)
        circle(c, px - 3, py - 3, 2.8)
        _f(c, "white", 0.9)


def _lair_shelf(c):
    sy = _FLASK[1]
    # brackets
    for bx in (900, 1046):
        poly(c, [(bx, sy + 16), (bx + 14, sy + 16), (bx + 14, sy + 70)])
        _fs(c, "#2b2236", INK, 4)
    rrect(c, 862, sy, 240, 20, 4)
    _fs(c, "frame", INK, LW)
    c.move_to(866, sy + 4)
    c.line_to(1080, sy + 4)
    _s(c, "#8c5a33", 3)
    # books lying
    rrect(c, 1010, sy - 30, 90, 30, 4)
    _fs(c, "#3e6fa8", INK, 4)
    rrect(c, 1018, sy - 56, 80, 26, 4)
    _fs(c, "cape_in", INK, 4)
    c.move_to(1030, sy - 43)
    c.line_to(1080, sy - 43)
    _s(c, "gold", 3)
    # vial
    vx = 990
    rrect(c, vx - 11, sy - 110, 22, 110, 11)
    _fs(c, "white", INK, 4, 0.15)
    rrect(c, vx - 7, sy - 64, 14, 60, 7)
    _f(c, "#c06bff")
    rrect(c, vx - 11, sy - 110, 22, 110, 11)
    _s(c, INK, 4)
    rrect(c, vx - 13, sy - 124, 26, 18, 4)
    _fs(c, "frame", INK, 3.5)
    # round flask
    fx, fy = _FLASK
    _glow(c, fx, fy - 50, 150, "lair_glow", 0.22)
    c.rectangle(fx - 13, fy - 150, 26, 70)
    circle(c, fx, fy - 46, 46)
    _fs(c, "white", INK, 4, 0.12)
    c.save()
    circle(c, fx, fy - 46, 46)
    c.clip()
    c.rectangle(fx - 50, fy - 58, 100, 70)
    _f(c, "lair_glow")
    c.move_to(fx - 50, fy - 58)
    c.line_to(fx + 50, fy - 58)
    _s(c, "#c7ffee", 5)
    c.restore()
    c.rectangle(fx - 13, fy - 150, 26, 70)
    circle(c, fx, fy - 46, 46)
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    _s(c, INK, 4.5)
    # cover the seam between neck and bulb
    c.rectangle(fx - 10.5, fy - 100, 21, 14)
    _f(c, "#e9e3ee", 0.0)
    rrect(c, fx - 17, fy - 162, 34, 16, 4)
    _fs(c, "frame", INK, 3.5)
    c.move_to(fx - 26, fy - 70)
    c.curve_to(fx - 30, fy - 52, fx - 26, fy - 36, fx - 18, fy - 26)
    _s(c, "white", 5, 0.5)


def _lair_cobweb(c):
    ox, oy = 0, 0
    for k in range(6):
        a = k * (math.pi / 2) / 5
        c.move_to(ox, oy)
        c.line_to(ox + math.cos(a) * 190, oy + math.sin(a) * 190)
    for r in (50, 95, 140, 180):
        pts = [(ox + math.cos(k * (math.pi / 2) / 5) * r,
                oy + math.sin(k * (math.pi / 2) / 5) * r) for k in range(6)]
        c.move_to(*pts[0])
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            c.curve_to(mx - (mx - ox) * 0.08, my - (my - oy) * 0.08,
                       mx - (mx - ox) * 0.08, my - (my - oy) * 0.08, b[0], b[1])
    _s(c, "#cdbbe8", 2, 0.28)


def _lair_static(c):
    _src(c, "lair_bg")
    c.paint()
    _lair_stones(c)
    # top darkening + soft central light pool (static, cached)
    g = cairo.LinearGradient(0, 0, 0, 560)
    g.add_color_stop_rgba(0, *hexc("ink", 0.55))
    g.add_color_stop_rgba(1, *hexc("ink", 0.0))
    c.rectangle(-340, 0, W + 680, 560)
    c.set_source(g)
    c.fill()
    c.rectangle(-340, -260, W + 680, 260)
    _f(c, INK, 0.55)
    _glow(c, 540, 820, 640, "#6a3f9a", 0.28)
    _lair_cobweb(c)
    _lair_floor(c)
    _lair_banner(c)
    _lair_window_surround(c)
    _lair_window_sky(c)
    _lair_window_frame(c)
    _lair_candle_static(c)
    _lair_corkboard(c)
    _lair_shelf(c)


def _lair_window_overlay(c):
    _lair_window_frame(c)


def _bolt_pts(seed=0):
    x = _WX0 + 70 + hash01(seed, 71) * 110
    y = 214.0
    pts = [(x, y)]
    while y < 760:
        y += 44 + hash01(len(pts), 72 + seed) * 40
        x += (hash01(len(pts), 73 + seed) - 0.5) * 70
        x = clamp(x, _WX0 + 20, _WX1 - 20)
        pts.append((x, y))
    return pts


def lair_bg(ctx, t, flash=0, rain=True, candle=True, bubbles=True, bolt_seed=0):
    """Villain lair backdrop, full frame (1080x1920 logical).

    Layout (logical px): gothic arched night window LEFT (x 44..406, y 194..930,
    sill at y≈900 with a candle), crimson snake-crest banner TOP-CENTRE
    (x 438..642, y 104..470), corkboard "EVIL PLANS" RIGHT (x 694..1040,
    y 168..580), potion shelf right edge (y≈760), stone floor from y=1400.
    A villain at desk (x=540, desk y≈1250, s=1) covers the middle: the props
    peek out around his head and cape.

    t      : seconds (drives rain, candle flicker, flask bubbles).
    flash  : 0..1 lightning. >0 brightens the window sky, shows a bolt
             (>0.35) and washes the room pale. For a full hit also call
             `flash(ctx, 0.2*f)` AFTER drawing characters.
    rain   : animated rain streaks in the window (small area).
    candle : flickering candle flame on the sill.
    bubbles: rising bubbles in the green flask on the shelf.
    bolt_seed: pick a different bolt shape per strike.
    Static parts are cached per device scale (≈2 ms per frame at 720p).
    """
    ctx.new_path()
    _cached_layer(ctx, "lair_static", _lair_static, rect=_BG_RECT, opaque=True)
    f = clamp(flash)
    if rain or f > 0:
        ctx.save()
        _lair_glass_path(ctx)
        ctx.clip()
        if f > 0:
            ctx.rectangle(_WX0, 150, _WX1 - _WX0, _WYB - 140)
            _f(ctx, "#dcecff", 0.85 * f)
        if rain:
            for i in range(9):
                sp = 1000 + 250 * hash01(i, 81)
                L = 50 + 26 * hash01(i, 82)
                span = _WYB - 150 + L
                yy = 170 + ((t * sp + hash01(i, 83) * span) % span) - L
                xx = _WX0 + hash01(i, 84) * (_WX1 - _WX0 + 80) - 20 - (yy - 170) * 0.12
                ctx.move_to(xx, yy)
                ctx.line_to(xx - L * 0.14, yy + L)
            _s(ctx, "rain", 3, 0.32 + 0.5 * f)
        if f > 0.35:
            pts = _bolt_pts(bolt_seed)
            k = (f - 0.35) / 0.65
            poly(ctx, pts, closed=False)
            _s(ctx, "#bfe0ff", 16, 0.5 * k)
            poly(ctx, pts, closed=False)
            _s(ctx, "white", 6, k)
        ctx.restore()
        _cached_layer(ctx, "lair_winframe", _lair_window_overlay, rect=_WIN_RECT)
    if candle:
        x, y = _CANDLE
        fl = 1 + 0.12 * noise1(t * 9, 5) + 0.06 * math.sin(t * 23)
        sw = noise1(t * 4, 6) * 0.12
        fy = y - 96
        ctx.save()
        ctx.translate(x, fy)
        ctx.rotate(sw)
        ctx.scale(fl * 0.9, fl)
        circle(ctx, 0, -6, 34)
        _f(ctx, "warn", 0.12)
        ctx.move_to(0, -34)
        ctx.curve_to(10, -18, 13, -4, 0, 6)
        ctx.curve_to(-13, -4, -10, -18, 0, -34)
        _fs(ctx, "warn", INK, 3)
        ctx.move_to(0, -18)
        ctx.curve_to(5, -10, 6, -2, 0, 3)
        ctx.curve_to(-6, -2, -5, -10, 0, -18)
        _f(ctx, "#fff3c4")
        ctx.restore()
    if bubbles:
        fx, fy = _FLASK
        ctx.save()
        circle(ctx, fx, fy - 46, 44)
        ctx.clip()
        for i in range(5):
            ph = (t * (0.6 + 0.3 * hash01(i, 91)) + hash01(i, 92)) % 1.0
            bx = fx - 24 + 48 * hash01(i, 93) + math.sin(t * 3 + i) * 3
            by = fy - 8 - ph * 50
            circle(ctx, bx, by, 3 + 3 * hash01(i, 94))
            _f(ctx, "#e6fff7", 0.85 * (1 - ph))
        ctx.restore()
    if f > 0:
        ctx.rectangle(0, 0, W, H)
        _f(ctx, "#c9d6ff", 0.22 * f)


# ===========================================================================
# AI MIND-SPACE BACKGROUND
# ===========================================================================
_AI_C = (540.0, 820.0)
_AI_HORIZON = 1330.0


def _ai_static(c, floor=True):
    _src(c, "ai_bg")
    c.paint()
    _glow(c, _AI_C[0], _AI_C[1], 1100, "ai_bg2", 1.0)
    _glow(c, _AI_C[0], _AI_C[1], 520, "#1a3366", 0.55)
    # faint dot grid
    sp = 54
    ylim = _AI_HORIZON - 30 if floor else H
    for gy in range(27 - 5 * sp, int(ylim), sp):
        for gx in range(27 - 6 * sp, W + 6 * sp, sp):
            d = math.hypot(gx - _AI_C[0], gy - _AI_C[1])
            a = 0.10 + 0.08 * clamp(d / 900)
            circle(c, gx, gy, 2.4)
            _f(c, "ai_rim", a)
    # mind rings
    for r, a in ((400, 0.07), (488, 0.045)):
        circle(c, _AI_C[0], _AI_C[1], r)
        _s(c, "ai_rim", 3, a)
    if floor:
        hy = _AI_HORIZON
        X0, X1, YB = -340, W + 340, H + 250
        c.rectangle(X0, hy, X1 - X0, YB - hy)
        _f(c, "#081127", 0.75)
        c.move_to(X0, hy)
        c.line_to(X1, hy)
        _s(c, "ai_rim", 4, 0.30)
        vx, vy = 540.0, hy - 260
        for i in range(-16, 17):
            bx = 540 + i * 150
            x_h = vx + (bx - vx) * (hy - vy) / (H - vy)
            c.move_to(x_h, hy)
            c.line_to(vx + (bx - vx) * (YB - vy) / (H - vy), YB)
        _s(c, "ai_rim", 2.5, 0.13)
        for k in range(1, 12):
            yy = hy + (H - hy) * 0.95 / (k * 0.85)
            if yy > YB:
                continue
            c.move_to(X0, yy)
            c.line_to(X1, yy)
            _s(c, "ai_rim", 2.5, 0.05 + 0.10 / k)
        _glow(c, 540, hy, 420, "ai_rim", 0.10)


def ai_bg(ctx, t, motes=10, floor=True):
    """The AI's mind-space, full frame.

    Deep navy (`ai_bg`) with a large soft centre glow at (540, 820) (where the
    AI head usually floats), a faint cyan dot grid, two faint "mind rings"
    (r 400 / 488 around (540, 820)) and, if `floor`, a perspective light-grid
    floor below y=1330. `motes` (≤12) slow drifting light specks are the
    only motion. Static part cached per device scale.
    """
    ctx.new_path()
    key = "ai_static_f" if floor else "ai_static_nf"
    _cached_layer(ctx, key, lambda c: _ai_static(c, floor), rect=_BG_RECT, opaque=True)
    n = min(12, max(0, int(motes)))
    for i in range(n):
        sp = 14 + 16 * hash01(i, 101)
        yr = 1500.0
        yy = 1450 - ((t * sp + hash01(i, 102) * yr) % yr)
        xx = 60 + hash01(i, 103) * 960 + math.sin(t * 0.4 + i * 1.7) * 24
        tw = 0.55 + 0.45 * math.sin(t * (0.9 + 0.5 * hash01(i, 104)) + i)
        edge = smoothstep(seg(yy, -40, 120)) * smoothstep(seg(1450 - yy, 0, 160))
        a = tw * edge
        if a < 0.02:
            continue
        r = 3 + 2.5 * hash01(i, 105)
        circle(ctx, xx, yy, r * 3.2)
        _f(ctx, "ai_rim", 0.10 * a)
        circle(ctx, xx, yy, r)
        _f(ctx, "ai_eye", 0.75 * a)


# ===========================================================================
# DESK, LAMP, KEYBOARD, MUG, COMPUTER
# ===========================================================================
def skull_lamp(ctx, x, y, s=1.0, on=1.0):
    """Skull-shaped desk lamp. (x, y) = bottom-centre (sits on a surface).

    s=1 -> ~150 px wide, ~190 px tall. `on` 0..1 = glow from the eye sockets
    and the open crown (warm yellow) + a soft light pool.
    """
    ctx.new_path()
    with saved(ctx, x, y, s):
        if on > 0.01:
            _glow(ctx, 0, -120, 190, "lamp_light", 0.30 * on)
        # brass base
        ellipse(ctx, 0, -10, 70, 16)
        _fs(ctx, "gold", INK, LW)
        rrect(ctx, -18, -44, 36, 36, 6)
        _fs(ctx, "gold_dk", INK, 4)
        # skull
        ctx.move_to(-60, -112)
        ctx.curve_to(-64, -170, -34, -196, 0, -196)
        ctx.curve_to(34, -196, 64, -170, 60, -112)
        ctx.curve_to(58, -88, 44, -80, 36, -72)
        ctx.line_to(34, -44)
        ctx.line_to(-34, -44)
        ctx.line_to(-36, -72)
        ctx.curve_to(-44, -80, -58, -88, -60, -112)
        ctx.close_path()
        _fs(ctx, "bone", INK, LW)
        # side shading
        ctx.move_to(40, -182)
        ctx.curve_to(62, -160, 62, -120, 52, -96)
        ctx.curve_to(48, -110, 46, -150, 40, -182)
        _f(ctx, "bone_dk")
        glow = _mix("#3a2030", "lamp_light", clamp(on))
        for ex in (-25, 25):
            ellipse(ctx, ex, -118, 19, 21, -0.2 if ex < 0 else 0.2)
            ctx.set_source_rgba(*glow)
            ctx.fill_preserve()
            _s(ctx, INK, 4)
        poly(ctx, [(0, -98), (-9, -82), (9, -82)])
        ctx.set_source_rgba(*glow)
        ctx.fill_preserve()
        _s(ctx, INK, 3.5)
        # teeth
        for tx in (-22, -7, 8, 23):
            ctx.move_to(tx, -64)
            ctx.line_to(tx, -48)
        _s(ctx, INK, 3.5)
        ctx.move_to(-30, -64)
        ctx.line_to(30, -64)
        _s(ctx, INK, 3.5)
        # open crown with light
        ellipse(ctx, 0, -190, 34, 9)
        ctx.set_source_rgba(*glow)
        ctx.fill_preserve()
        _s(ctx, INK, 4)
        # little crack for charm
        ctx.move_to(-30, -184)
        ctx.line_to(-24, -168)
        ctx.line_to(-32, -156)
        _s(ctx, INK, 3)


def desk(ctx, x, y, w, lamp=True, emblem=True, h=None):
    """Villain's mahogany desk, seen from the front.

    (x, y) = centre of the desk's FRONT TOP EDGE (= the villain's waistline y
    from draw_villain). w = desk width (typ. 860..1100). The top surface is
    drawn ~32 px above y (it occludes his waist); the front panel runs down
    to y+h (default: bottom of the frame).
    lamp  : True draws the skull lamp on the left end of the desk (or pass a
            float = lamp x offset from desk centre, e.g. 330 for the right).
    emblem: gold snake medallion on the front panel.
    """
    ctx.new_path()
    h = (H + 20 - y) if h is None else h
    xl, xr = x - w / 2, x + w / 2
    # top surface (receding)
    poly(ctx, [(xl + 24, y - 34), (xr - 24, y - 34), (xr, y), (xl, y)])
    _fs(ctx, "wood_top", INK, LW)
    ctx.move_to(xl + 40, y - 24)
    ctx.line_to(xr - 40, y - 24)
    _s(ctx, "#93525b", 4, 0.8)
    # front lip
    rrect(ctx, xl - 6, y, w + 12, 30, 6)
    _fs(ctx, "wood", INK, LW)
    ctx.move_to(xl + 4, y + 22)
    ctx.line_to(xr - 4, y + 22)
    _s(ctx, "gold", 4)
    # body
    ctx.rectangle(xl + 14, y + 30, w - 28, h - 30)
    _fs(ctx, "wood_in", INK, LW)
    # panels
    pw = (w - 28 - 4 * 22) / 3
    for i in range(3):
        px = xl + 14 + 22 + i * (pw + 22)
        rrect(ctx, px, y + 62, pw, max(40, min(h - 90, 420)), 14)
        _fs(ctx, "wood_dk", INK, 4)
        rrect(ctx, px + 10, y + 72, pw - 20, max(20, min(h - 110, 400)), 10)
        _s(ctx, "#5e2c38", 4)
    if emblem:
        ex, ey = x, y + 150
        ellipse(ctx, ex, ey, 62, 74)
        _fs(ctx, "gold", INK, LW)
        ellipse(ctx, ex, ey, 48, 60)
        _fs(ctx, "cape_in", INK, 3)
        _snake_emblem(ctx, ex - 5, ey + 2, 0.5)
    if lamp:
        lx = x - w / 2 + 120 if lamp is True else x + float(lamp)
        skull_lamp(ctx, lx, y - 12, 0.95)


def keyboard(ctx, x, y, w=380, t=0.0, typing=False, seed=0):
    """Chunky retro keyboard lying on the desk top.

    (x, y) = centre of its FRONT edge (put y at the desk's front-top edge).
    w = width (default 380; depth is ~0.2 w). `typing`=True makes random keys
    dip/light up from `t` (pair with villain arms="type").
    """
    ctx.new_path()
    d = w * 0.2
    xl, xr = x - w / 2, x + w / 2
    poly(ctx, [(xl + 18, y - d), (xr - 18, y - d), (xr, y), (xl, y)])
    _fs(ctx, "plastic_dk", INK, LW)
    rrect(ctx, xl - 2, y - 4, w + 4, 14, 5)
    _fs(ctx, "plastic", INK, 4)
    rows, cols = 3, 11
    step = int(t * 12) if typing else -1
    for r in range(rows):
        yy = y - d + 6 + r * (d - 12) / rows
        inset = 18 * (1 - (r + 1) / rows) + 6
        kw = (w - 2 * inset - 8) / cols
        for k in range(cols):
            kx = xl + inset + 4 + k * kw
            hit = typing and hash01(step * 37 + r * 11 + k, seed) < 0.09
            dy = 3 if hit else 0
            rrect(ctx, kx + 2, yy + dy, kw - 4, (d - 12) / rows - 3, 3)
            _fs(ctx, "lair_glow" if hit else "plastic_hi", INK, 2.5)


def mug(ctx, x, y, s=1.0, txt="#1 EVIL", t=None):
    """Coffee mug. (x, y) = bottom-centre. s=1 -> ~110 px tall. t -> steam."""
    ctx.new_path()
    with saved(ctx, x, y, s):
        circle(ctx, 52, -58, 24)
        _s(ctx, INK, 18)
        circle(ctx, 52, -58, 24)
        _s(ctx, "white", 9)
        rrect(ctx, -46, -110, 92, 110, 14)
        _fs(ctx, "white", INK, LW)
        ellipse(ctx, 0, -108, 44, 8)
        _fs(ctx, "#4a2a1a", INK, 3)
        text(ctx, txt, 0, -46, 24, "cape_in", "comic")
        ctx.move_to(-36, -18)
        ctx.line_to(36, -18)
        _s(ctx, "#e7e2ef", 6)
        if t is not None:
            for i in range(2):
                ph = (t * 0.5 + i * 0.5) % 1.0
                yy = -120 - ph * 70
                ctx.move_to(-10 + i * 20, yy + 20)
                ctx.curve_to(-22 + i * 20, yy + 6, 2 + i * 20, yy - 6, -10 + i * 20, yy - 20)
                _s(ctx, "white", 5, 0.4 * math.sin(ph * math.pi))


def _default_screen(t):
    def fn(c, sw, sh):
        _text(c, "> HELLO, AI", 26, 58, 34, "lair_glow", "mono", "left")
        if int(t * 2) % 2 == 0:
            c.rectangle(26, 78, 22, 32)
            _f(c, "lair_glow")
    return fn


def computer(ctx, x, y, s=1.0, screen_fn=None, view="front", facing=1, glow=1.0, t=0.0,
             label="EVILTRON"):
    """Chunky retro CRT computer whose screen glows cool teal.

    (x, y) = bottom-centre of the monitor stand (sits on the desk top).
    s=1 -> front view ~440 px wide x ~420 px tall (screen 368x292).
    view:
      "front" : screen faces the camera; `screen_fn(ctx, sw, sh)` draws the
                screen content with ctx translated to the screen's top-left
                and clipped to it, in screen-local px (sw=368, sh=292 at s=1;
                already scaled by s). Use a closure to capture t. Default
                content: blinking "> HELLO, AI" prompt (uses `t`).
      "side"  : profile, screen facing `facing` (+1 right / -1 left) with a
                teal light wedge spilling that way (put it beside the villain
                facing him: the light reads as lighting his face).
      "back"  : rear of the CRT (vents, cable) with a teal halo spilling
                around its edges (monitor between camera and villain/AI).
    glow : 0..1.5 screen/halo brightness.
    Returns {"screen": (x, y, w, h) world rect (front view), "glow": (gx, gy)}.
    """
    ctx.new_path()
    out = {}
    with saved(ctx, x, y, s) as c:
        if view == "front":
            _glow(c, 0, -220, 360, "lair_glow", 0.16 * glow)
            # depth (top of the tube housing)
            poly(c, [(-220, -404), (220, -404), (176, -442), (-176, -442)])
            _fs(c, "plastic_hi", INK, LW)
            # stand
            rrect(c, -52, -60, 104, 48, 8)
            _fs(c, "plastic_dk", INK, LW)
            rrect(c, -136, -24, 272, 26, 12)
            _fs(c, "plastic", INK, LW)
            # bezel
            rrect(c, -222, -406, 444, 356, 30)
            _fs(c, "plastic", INK, LW)
            c.move_to(-200, -398)
            c.line_to(200, -398)
            _s(c, "plastic_hi", 5)
            rrect(c, -222, -88, 444, 38, 18)
            _f(c, "plastic_dk")
            rrect(c, -222, -406, 444, 356, 30)
            _s(c, INK, LW)
            # screen
            sx, sy, sw, sh = -184, -370, 368, 266
            rrect(c, sx - 10, sy - 10, sw + 20, sh + 20, 34)
            _fs(c, "#2c2638", INK, 4)
            rrect(c, sx, sy, sw, sh, 28)
            _src(c, "crt")
            c.fill()
            c.save()
            rrect(c, sx, sy, sw, sh, 28)
            c.clip()
            _glow(c, 0, sy + sh / 2, 230, "lair_glow", 0.22 * glow)
            c.save()
            c.translate(sx, sy)
            (screen_fn or _default_screen(t))(c, sw, sh)
            c.restore()
            for yy in range(int(sy) + 4, int(sy + sh), 7):
                c.rectangle(sx, yy, sw, 2)
            _f(c, "black", 0.10)
            c.move_to(sx + sw - 46, sy + 13)
            c.curve_to(sx + sw - 26, sy + 15, sx + sw - 16, sy + 26, sx + sw - 14, sy + 44)
            _s(c, "white", 7, 0.25)
            c.restore()
            rrect(c, sx, sy, sw, sh, 28)
            _s(c, INK, 4)
            # label, LED, knobs
            if label:
                text(c, label, -150, -60, 22, "#d8d0ee", "round", "left")
            circle(c, 150, -69, 8)
            _fs(c, "safe", INK, 3)
            circle(c, 182, -69, 9)
            _fs(c, "plastic_dk", INK, 3)
            out["screen"] = (x + sx * s, y + sy * s, sw * s, sh * s)
            out["glow"] = (x, y - 238 * s)
        elif view == "side":
            f = 1 if facing >= 0 else -1
            c.scale(f, 1)
            # light wedge toward the facing side
            g = cairo.LinearGradient(180, 0, 520, 0)
            g.add_color_stop_rgba(0, *C("lair_glow", 0.16 * glow))
            g.add_color_stop_rgba(1, *C("lair_glow", 0.0))
            poly(c, [(184, -390), (520, -470), (520, 10), (184, -70)])
            c.set_source(g)
            c.fill()
            _glow(c, 200, -230, 260, "lair_glow", 0.30 * glow)
            # stand
            rrect(c, -10, -60, 90, 48, 8)
            _fs(c, "plastic_dk", INK, LW)
            rrect(c, -100, -24, 260, 26, 12)
            _fs(c, "plastic", INK, LW)
            # tube body (tapers to the back)
            poly(c, [(40, -380), (-150, -320), (-176, -290), (-176, -150), (-150, -120),
                     (40, -66)])
            _fs(c, "plastic_dk", INK, LW)
            for k in range(5):
                c.move_to(-150, -266 + k * 26)
                c.line_to(-40, -276 + k * 26)
            _s(c, INK, 5, 0.55)
            # front housing box
            rrect(c, 20, -412, 164, 364, 22)
            _fs(c, "plastic", INK, LW)
            c.move_to(36, -398)
            c.line_to(168, -398)
            _s(c, "plastic_hi", 5)
            rrect(c, 20, -96, 164, 48, 18)
            _f(c, "plastic_dk")
            rrect(c, 20, -412, 164, 364, 22)
            _s(c, INK, LW)
            circle(c, 160, -72, 6)
            _fs(c, "safe", INK, 2.5)
            # bezel lip on the screen side
            rrect(c, 172, -404, 24, 348, 10)
            _fs(c, "plastic_hi", INK, 4)
            # glowing screen edge
            c.move_to(198, -380)
            c.line_to(198, -84)
            _s(c, "lair_glow", 18, 0.35 * glow)
            c.move_to(198, -376)
            c.line_to(198, -88)
            _s(c, "lair_glow", 6, min(1.0, glow))
            out["glow"] = (x + 198 * s * f, y - 230 * s)
        else:  # back
            _glow(c, 0, -230, 420, "lair_glow", 0.34 * glow)
            # soft light spill around the bezel (stacked strokes, no blur)
            for (wd, a) in ((60, 0.08), (36, 0.12), (16, 0.22)):
                rrect(c, -224, -408, 448, 360, 32)
                _s(c, "lair_glow", wd, a * glow)
            rrect(c, -222, -406, 444, 356, 30)
            _fs(c, "plastic_dk", INK, LW)
            c.move_to(-200, -398)
            c.line_to(200, -398)
            _s(c, "plastic", 5)
            # stand + base
            rrect(c, -52, -60, 104, 48, 8)
            _fs(c, "plastic_dk", INK, LW)
            rrect(c, -136, -24, 272, 26, 12)
            _fs(c, "plastic", INK, LW)
            # rear tube housing (closer to camera, so smaller + lighter)
            rrect(c, -160, -360, 320, 262, 40)
            _fs(c, "plastic", INK, LW)
            c.move_to(-128, -346)
            c.line_to(128, -346)
            _s(c, "plastic_hi", 5)
            for col_ in range(3):
                for row_ in range(4):
                    rrect(c, -96 + col_ * 70, -318 + row_ * 34, 52, 13, 6.5)
                    _fs(c, "plastic_dk", INK, 2.5)
            rrect(c, -46, -164, 92, 40, 6)
            _fs(c, "paper", INK, 3)
            c.move_to(-34, -150)
            c.line_to(30, -150)
            c.move_to(-34, -138)
            c.line_to(12, -138)
            _s(c, "#9a90a8", 3)
            # cable
            c.move_to(60, -112)
            c.curve_to(80, -60, 150, -40, 190, 0)
            _s(c, INK, 14)
            c.move_to(60, -112)
            c.curve_to(80, -60, 150, -40, 190, 0)
            _s(c, "#2b2236", 7)
            out["glow"] = (x, y - 230 * s)
    return out


# ===========================================================================
# SMALL UI BITS: label_tag, x_mark, check_mark, arrow
# ===========================================================================
def label_tag(ctx, x, y, txt, color="warn", size=30, text_color=None, t=None, t_in=None,
              font="ui", pointer=None, rot=0.0):
    """Small pill/chip label. (x, y) = CENTRE. size = font px (chip ≈ 1.7*size tall).

    color      : chip fill; text auto white/ink for contrast unless text_color.
    t, t_in    : optional pop-in (ease_out_back) at t_in.
    pointer    : None | "down" | "up" -> little triangle pointing at something
                 below/above the chip (e.g. a highlighted word).
    rot        : tilt in radians.
    Returns (w, h) of the chip.
    """
    ctx.new_path()
    set_font(ctx, font, size)
    tw = ctx.text_extents(txt)[4]
    w_, h_ = tw + size * 1.1, size * 1.62
    k = 1.0
    if t is not None and t_in is not None:
        if t < t_in:
            return (w_, h_)
        k = pop(t, t_in, 0.3)
    if k < 0.01:
        return (w_, h_)
    tc = text_color or _txt_on(color)
    with saved(ctx, x, y, k, rot) as c:
        if pointer in ("down", "up"):
            sg = 1 if pointer == "down" else -1
            poly(c, [(-size * 0.32, sg * h_ * 0.42), (size * 0.32, sg * h_ * 0.42),
                     (0, sg * (h_ / 2 + size * 0.42))])
            _fs(c, color, INK, 4)
        rrect(c, -w_ / 2, -h_ / 2 + 4, w_, h_, h_ / 2)
        _f(c, INK, 0.45)
        rrect(c, -w_ / 2, -h_ / 2, w_, h_, h_ / 2)
        _fs(c, color, INK, 4)
        if pointer in ("down", "up"):
            sg = 1 if pointer == "down" else -1
            poly(c, [(-size * 0.26, sg * h_ * 0.36), (size * 0.26, sg * h_ * 0.36),
                     (0, sg * (h_ / 2 + size * 0.28))])
            _f(c, color)
        _text(c, txt, 0, size * 0.36, size, tc, font)
    return (w_, h_)


def _mark(ctx, x, y, s, t, t_in, kind):
    if t < t_in:
        return
    ctx.new_path()
    d = t - t_in
    k = 0.85 + 0.15 * ease_out_back(seg(d, 0.0, 0.3), 3.0)
    S = 140.0
    col = "danger" if kind == "x" else "safe"
    with saved(ctx, x, y, s * k, -0.06 if kind == "x" else 0.0) as c:
        if kind == "x":
            strokes = [((-0.36, -0.36), (0.36, 0.36)), ((0.36, -0.36), (-0.36, 0.36))]
            ps = [ease_out(seg(d, 0.0, 0.12)), ease_out(seg(d, 0.10, 0.22))]
        else:
            strokes = [((-0.42, 0.02), (-0.12, 0.32)), ((-0.12, 0.32), (0.46, -0.34))]
            ps = [ease_out(seg(d, 0.0, 0.10)), ease_out(seg(d, 0.08, 0.24))]
        # shadow + ink + colour, per stroke
        for layer in ("shadow", "ink", "col"):
            for (a, b), p in zip(strokes, ps):
                if p <= 0:
                    continue
                ax, ay = a[0] * S, a[1] * S
                bx, by = ax + (b[0] * S - ax) * p, ay + (b[1] * S - ay) * p
                if layer == "shadow":
                    c.move_to(ax + 6, ay + 8)
                    c.line_to(bx + 6, by + 8)
                    _s(c, INK, 40, 0.35)
                elif layer == "ink":
                    c.move_to(ax, ay)
                    c.line_to(bx, by)
                    _s(c, INK, 40)
                else:
                    c.move_to(ax, ay)
                    c.line_to(bx, by)
                    _s(c, col, 26)
                    c.move_to(ax + (bx - ax) * 0.1 - 3, ay + (by - ay) * 0.1 - 4)
                    c.line_to(ax + (bx - ax) * 0.45 - 3, ay + (by - ay) * 0.45 - 4)
                    _s(c, "white", 6, 0.35)


def x_mark(ctx, x, y, s, t, t_in):
    """Big red X that swipes in (two strokes, 0.22 s) at t_in. (x, y) = centre;
    s=1 -> ~140 px. Stays until the scene stops drawing it."""
    _mark(ctx, x, y, s, t, t_in, "x")


def check_mark(ctx, x, y, s, t, t_in):
    """Big green check that draws in (0.24 s) at t_in. (x, y) = centre; s=1 -> ~140 px."""
    _mark(ctx, x, y, s, t, t_in, "check")


def arrow(ctx, x0, y0, x1, y1, color="warn", t_progress=1.0, bend=0.18, width=14, head=1.0):
    """Hand-drawn curved arrow from (x0, y0) to (x1, y1) growing with t_progress 0..1.

    bend : sideways bow as a fraction of the length (+ bows to the left of the
           travel direction, - to the right, 0 = straight).
    width: shaft width (ink outline added). head: arrowhead scale.
    Drive t_progress with e.g. ease_out(seg(t, a, a + 0.4)).
    """
    p = clamp(t_progress)
    if p <= 0.001:
        return
    ctx.new_path()
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = dy / L, -dx / L
    cpt = ((x0 + x1) / 2 + nx * bend * L, (y0 + y1) / 2 + ny * bend * L)
    hs = width * 2.2 * head
    # shorten the shaft so the head covers its end
    pts = _qbez((x0, y0), cpt, (x1, y1), 32)
    for layer in ("ink", "col"):
        tip, d = _partial_polyline(ctx, pts, p)
        _s(ctx, INK if layer == "ink" else color, width + (2 * LW if layer == "ink" else 0))
        if p > 0.04:
            kk = ease_out_back(clamp((p - 0.04) / 0.25)) * hs
            ux, uy = d
            px_, py_ = -uy, ux
            hp = [(tip[0] + ux * kk * 0.9, tip[1] + uy * kk * 0.9),
                  (tip[0] - ux * kk * 0.6 + px_ * kk * 0.8, tip[1] - uy * kk * 0.6 + py_ * kk * 0.8),
                  (tip[0] - ux * kk * 0.6 - px_ * kk * 0.8, tip[1] - uy * kk * 0.6 - py_ * kk * 0.8)]
            poly(ctx, hp)
            if layer == "ink":
                _src(ctx, INK)
                ctx.fill_preserve()
                _s(ctx, INK, 2 * LW)
            else:
                _f(ctx, color)


# ===========================================================================
# CHAT BUBBLES
# ===========================================================================
BUBBLE_COL = {"villain": ("bubble_villain", "villain_dk"), "ai": ("bubble_ai", "ai_dk"),
              "narrator": ("ui_panel", "ui_dark")}


class BubbleLayout(float):
    """Returned by chat_bubble: a float (total height incl. tail) + layout info.

    .rect  = (x, y, w, h) bubble body (world)    .tail = (x, y) tail tip
    .spans = {substring: [(x, y, w, h), ...]}   highlight rects (world, at rest)
    .lines = wrapped lines                       .font_size
    """


def _bubble_path(ctx, bx, by, bw, bh, r, side, fs):
    """Rounded bubble with an iMessage-style tail at the bottom corner.
    side=-1 tail bottom-LEFT (ai), +1 bottom-RIGHT (villain), 0 none."""
    if side == 0:
        rrect(ctx, bx, by, bw, bh, r)
        return
    ctx.save()
    if side > 0:
        ctx.translate(bx + bw, by)
        ctx.scale(-1, 1)
    else:
        ctx.translate(bx, by)
    th = fs * 0.36
    ctx.move_to(r, 0)
    ctx.line_to(bw - r, 0)
    ctx.arc(bw - r, r, r, -math.pi / 2, 0)
    ctx.line_to(bw, bh - r)
    ctx.arc(bw - r, bh - r, r, 0, math.pi / 2)
    ctx.line_to(r * 1.05, bh)
    ctx.curve_to(r * 0.55, bh, r * 0.25, bh + th * 0.55, -fs * 0.34, bh + th)
    ctx.curve_to(-fs * 0.02, bh + th * 0.25, 0, bh - r * 0.2, 0, bh - r * 0.75)
    ctx.line_to(0, r)
    ctx.arc(r, r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
    ctx.restore()


def _norm_highlights(highlight, t_in):
    out = []
    for k, h in enumerate(highlight or []):
        if isinstance(h, str):
            h = {"text": h}
        elif isinstance(h, (tuple, list)):
            h = {"text": h[0], "t0": h[1]}
        un = h.get("unmask_t", h.get("tag_t"))
        out.append({"text": h["text"], "t0": h.get("t0", t_in + 0.45 + 0.22 * k),
                    "style": h.get("style", "underline"), "color": h.get("color", "warn"),
                    "tag": h.get("tag"), "unmask_t": un,
                    "unmask_color": h.get("unmask_color", "danger"),
                    "tag_pos": h.get("tag_pos", "auto"),
                    "all": h.get("all", True)})
    return out


def bubble_layout(ctx, x, y, w, txt, who, highlight=None, font_size=40, fit=True):
    """Pure layout for chat_bubble (no drawing). Same args; returns BubbleLayout."""
    fs = font_size
    pad_x, pad_y = fs * 0.68, fs * 0.5
    lh = fs * 1.24
    norm = " ".join(str(txt).split())
    lines = wrap_lines(ctx, norm, w - 2 * pad_x, "ui", fs) if norm else [""]
    set_font(ctx, "ui", fs)
    widths = [ctx.text_extents(l)[4] for l in lines]
    bw = min(w, max(widths) + 2 * pad_x) if fit else w
    bw = max(bw, fs * 2.4)
    bh = 2 * pad_y + (len(lines) - 1) * lh + fs * 1.0
    side = 1 if who == "villain" else (0 if who == "narrator" else -1)
    bx = x + w - bw if side > 0 else (x + (w - bw) / 2 if side == 0 else x)
    offs, o = [], 0
    for l in lines:
        offs.append(o)
        o += len(l) + 1
    base0 = y + pad_y + fs * 0.80
    tx = bx + pad_x
    spans = {}
    low = norm.lower()
    for hl in _norm_highlights(highlight, 0.0):
        key = hl["text"].lower()
        rects, start = [], 0
        while key:
            i = low.find(key, start)
            if i < 0:
                break
            j = i + len(key)
            for li, (l, lo) in enumerate(zip(lines, offs)):
                a, b = max(i, lo), min(j, lo + len(l))
                if a < b:
                    xa = ctx.text_extents(l[:a - lo])[4]
                    xb = ctx.text_extents(l[:b - lo])[4]
                    rects.append((tx + xa, base0 + li * lh - fs * 0.80, xb - xa, fs * 1.02))
            start = j
            if not hl["all"]:
                break
        spans[hl["text"]] = rects
    th = fs * 0.36 if side else 0
    res = BubbleLayout(bh + th + fs * 0.06)
    res.rect = (bx, y, bw, bh)
    res.tail = ((bx - fs * 0.34) if side < 0 else (bx + bw + fs * 0.34) if side > 0
                else (bx + bw / 2), y + bh + th)
    res.spans = spans
    res.lines = lines
    res.font_size = fs
    res.tag_space = fs * 1.9
    res._base0, res._lh, res._tx, res._side = base0, lh, tx, side
    return res


def _wavy(ctx, x0, x1, y, amp, wl):
    n = max(2, int((x1 - x0) / (wl / 4)))
    ctx.move_to(x0, y)
    for i in range(1, n + 1):
        xx = x0 + (x1 - x0) * i / n
        ctx.line_to(xx, y + amp * math.sin((xx - x0) / wl * 2 * math.pi))


def chat_bubble(ctx, x, y, w, txt, who, t, t_in, highlight=None, font_size=40, fit=True,
                reveal=None, t_out=None):
    """Messaging-style chat bubble (Nunito, white text, ink outline, flat shadow).

    (x, y) = TOP-LEFT of the bubble COLUMN; w = column width (max bubble width,
    typ. 640..820). With fit=True the bubble hugs its text: "villain" bubbles
    are RIGHT-aligned in the column (purple, tail bottom-right, like 'sent'
    messages), "ai" bubbles LEFT-aligned (teal, tail bottom-left), "narrator"
    centred, no tail (dark panel).
    Pops in from its tail at t_in (0.32 s ease_out_back); nothing drawn before.
    t_out  : optional pop-out (0.2 s). reveal : optional 0..1 typewriter.
    font_size: 40 logical px default (readable on phones at 1080 wide).

    highlight: list of entries marking substrings (case-insensitive, every
    occurrence) — for euphemisms. Each entry is a str, (str, t0) or dict:
        {"text": "party favors",       # substring to mark
         "t0": 3.2,                     # marker draws in (default t_in+0.45, +0.22 per entry)
         "style": "underline",          # underline (wavy) | box | fill (highlighter) | strike
         "color": "warn",               # marker colour
         "unmask_t": 5.0,               # optional: UNMASK at this time ->
         "tag": "= hurts people",       #   marker turns unmask_color, red box + tint
         "unmask_color": "danger",      #   behind the words, and the tag chip pops
         "tag_pos": "auto"}             #   OUTSIDE the bubble ("above"/"below"/auto =
                                        #   nearest edge) with a leader line to the word
    So a scene first underlines ("hmm, suspicious") then later unmasks. The
    tag needs ≈ 1.9*font_size of free space above/below the bubble
    (BubbleLayout.tag_space).

    Returns BubbleLayout: a float = total height incl. tail (stack the next
    bubble at y + h + gap) with .rect, .tail, .spans (world rects of each
    highlighted substring), .lines.
    """
    ctx.new_path()
    L = bubble_layout(ctx, x, y, w, txt, who, highlight, font_size, fit)
    if t < t_in:
        return L
    k = pop(t, t_in, 0.32)
    if t_out is not None and t >= t_out:
        k *= 1 - ease_in(seg(t, t_out, t_out + 0.2))
    if k < 0.01:
        return L
    fs = font_size
    bx, by, bw, bh = L.rect
    side = L._side
    fc, dk = BUBBLE_COL.get(who, BUBBLE_COL["ai"])
    r = min(fs * 0.8, bh / 2)
    hls = _norm_highlights(highlight, t_in)
    ax, ay = L.tail
    rot = (1 - clamp(seg(t, t_in, t_in + 0.32))) * 0.10 * (side or 1)
    ctx.save()
    ctx.translate(ax, ay)
    ctx.scale(k, k)
    ctx.rotate(-rot)
    ctx.translate(-ax, -ay)
    # flat shadow + body
    ctx.save()
    ctx.translate(0, 8)
    _bubble_path(ctx, bx, by, bw, bh, r, side, fs)
    _f(ctx, INK, 0.45)
    ctx.restore()
    _bubble_path(ctx, bx, by, bw, bh, r, side, fs)
    _fs(ctx, fc, INK, LW)
    # lower shade band + gloss
    ctx.save()
    _bubble_path(ctx, bx, by, bw, bh, r, side, fs)
    ctx.clip()
    ctx.rectangle(bx - 40, by + bh - 9, bw + 80, 40)
    _f(ctx, dk, 0.55)
    ctx.restore()

    # highlight state per entry
    st = []
    for hl in hls:
        rects = L.spans.get(hl["text"], [])
        p = ease_in_out(seg(t, hl["t0"], hl["t0"] + 0.35))
        u = 0.0
        if hl["unmask_t"] is not None:
            u = smoothstep(seg(t, hl["unmask_t"], hl["unmask_t"] + 0.25))
        col = _mix(hl["color"], hl["unmask_color"], u)
        st.append((hl, rects, p, u, col))
    # fills behind text
    for hl, rects, p, u, col in st:
        for (rx, ry, rw, rh) in rects:
            if hl["style"] == "fill" and p > 0:
                rrect(ctx, rx - 6, ry + 2, (rw + 12) * p, rh + 2, 8)
                ctx.set_source_rgba(col[0], col[1], col[2], 0.55)
                ctx.fill()
            if u > 0:
                rrect(ctx, rx - 7, ry - 1, rw + 14, rh + 6, 10)
                ctx.set_source_rgba(*_mix(INK, hl["unmask_color"], 0.55)[:3], 0.75 * u)
                ctx.fill()
    # text
    nchar = sum(len(l) for l in L.lines)
    budget = nchar if reveal is None else int(round(nchar * clamp(reveal)))
    for i, l in enumerate(L.lines):
        shown = l[:max(0, budget)]
        budget -= len(l)
        if shown:
            _text(ctx, shown, L._tx, L._base0 + i * L._lh, fs, "bubble_text", "ui", "left")
    # markers over text
    for hl, rects, p, u, col in st:
        if p <= 0 and u <= 0:
            continue
        sh = 0.0
        if u > 0 and hl["unmask_t"] is not None:
            dt = t - hl["unmask_t"]
            sh = math.sin(dt * 60) * 5 * clamp(1 - dt / 0.35) if dt < 0.35 else 0.0
        total = sum(rr[2] for rr in rects) or 1.0
        acc = 0.0
        for (rx, ry, rw, rh) in rects:
            pp = clamp((p * total - acc) / rw) if rw > 0 else 0
            acc += rw
            rx += sh
            sty = "box" if u > 0.5 else hl["style"]
            if sty == "underline" and pp > 0:
                _wavy(ctx, rx - 2, rx - 2 + (rw + 4) * pp, ry + rh * 0.98, fs * 0.075, fs * 0.5)
                path = ctx.copy_path()
                _s(ctx, INK, fs * 0.27)
                ctx.append_path(path)
                ctx.set_source_rgba(*col)
                ctx.set_line_width(fs * 0.15)
                ctx.stroke()
            elif sty == "strike" and pp > 0:
                ctx.move_to(rx - 4, ry + rh * 0.52)
                ctx.line_to(rx - 4 + (rw + 8) * pp, ry + rh * 0.48)
                path = ctx.copy_path()
                _s(ctx, INK, fs * 0.24)
                ctx.append_path(path)
                ctx.set_source_rgba(*col)
                ctx.set_line_width(fs * 0.13)
                ctx.stroke()
            elif sty == "box":
                pb = 1.0 if u > 0.5 else pp
                if pb > 0:
                    pts = _rrect_pts(rx - 7, ry - 1, rw + 14, rh + 7, fs * 0.25)
                    _partial_polyline(ctx, pts, pb)
                    path = ctx.copy_path()
                    _s(ctx, INK, fs * 0.24)
                    ctx.append_path(path)
                    ctx.set_source_rgba(*col)
                    ctx.set_line_width(fs * 0.13)
                    ctx.stroke()
    ctx.restore()
    # unmask tags: OUTSIDE the bubble (above it if the word sits in the upper
    # half of the text, else below), with a leader line down/up to the word
    for hl, rects, p, u, col in st:
        if hl["tag"] and hl["unmask_t"] is not None and t >= hl["unmask_t"] and rects:
            _bubble_tag(ctx, L, rects[0], hl, t, fs, k)
    return L


def _rrect_pts(x, y, w, h, r, n=6):
    """Points around a rounded rect, clockwise from the top-left corner's end."""
    pts = []
    for (cx, cy, a0) in ((x + w - r, y + r, -math.pi / 2), (x + w - r, y + h - r, 0.0),
                         (x + r, y + h - r, math.pi / 2), (x + r, y + r, math.pi)):
        for j in range(n + 1):
            a = a0 + (math.pi / 2) * j / n
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pts.append(pts[0])
    return pts


def _bubble_tag(ctx, L, rect, hl, t, fs, k):
    bx, by, bw, bh = L.rect
    rx, ry, rw, rh = rect
    if hl["tag_pos"] in ("above", "below"):
        above = hl["tag_pos"] == "above"
    else:
        above = (ry + rh / 2) < (by + bh / 2)
    tsz = fs * 0.78
    th = tsz * 1.62
    cx = rx + rw / 2
    cy = (by - th * 0.5 - fs * 0.35) if above else (by + bh + th * 0.5 + fs * 0.55)
    set_font(ctx, "ui", tsz)
    tw = ctx.text_extents(hl["tag"])[4] + tsz * 1.1
    cx = clamp(cx, bx + tw / 2 - fs * 0.5, bx + bw - tw / 2 + fs * 0.5)
    t_in = hl["unmask_t"] + 0.08
    q = ease_out(seg(t, t_in, t_in + 0.2))
    if q > 0 and k > 0.5:
        x0 = rx + rw / 2
        y0 = ry - 2 if above else ry + rh + 4
        y1 = cy + (th / 2 if above else -th / 2)
        ctx.move_to(x0, y0)
        ctx.line_to(lerp(x0, cx, q), lerp(y0, y1, q))
        _s(ctx, INK, 9)
        ctx.move_to(x0, y0)
        ctx.line_to(lerp(x0, cx, q), lerp(y0, y1, q))
        _s(ctx, hl["unmask_color"], 4)
        circle(ctx, x0, y0, 6)
        _fs(ctx, hl["unmask_color"], INK, 3)
    label_tag(ctx, cx, cy, hl["tag"], hl["unmask_color"], size=tsz, t=t, t_in=t_in,
              rot=-0.03 if above else 0.03)


def typing_dots(ctx, x, y, t, who, t_in=None, s=1.0):
    """'…is typing' bubble with three bouncing dots.

    (x, y) = TOP-LEFT of the small bubble (≈150 x 80 px at s=1); tail at
    bottom-left for "ai", bottom-right for "villain" (match chat_bubble).
    t_in: optional pop-in time. Returns (w, h).
    """
    ctx.new_path()
    bw, bh = 150 * s, 80 * s
    if t_in is not None and t < t_in:
        return (bw, bh)
    k = pop(t, t_in, 0.25) if t_in is not None else 1.0
    if k < 0.01:
        return (bw, bh)
    fc, dk = BUBBLE_COL.get(who, BUBBLE_COL["ai"])
    side = 1 if who == "villain" else -1
    fs = 40 * s
    ax = x - fs * 0.34 if side < 0 else x + bw + fs * 0.34
    ay = y + bh + fs * 0.36
    with saved(ctx, ax, ay, k):
        ctx.translate(-ax, -ay)
        ctx.save()
        ctx.translate(0, 7 * s)
        _bubble_path(ctx, x, y, bw, bh, bh / 2, side, fs)
        _f(ctx, INK, 0.45)
        ctx.restore()
        _bubble_path(ctx, x, y, bw, bh, bh / 2, side, fs)
        _fs(ctx, fc, INK, LW)
        for i in range(3):
            b = max(0.0, math.sin(t * 2 * math.pi * 1.5 - i * 0.9))
            circle(ctx, x + bw / 2 + (i - 1) * 34 * s, y + bh / 2 - b * 11 * s, 10 * s)
            _f(ctx, "white", 0.55 + 0.45 * b)
    return (bw, bh)


# ===========================================================================
# BRICK WALL
# ===========================================================================
_ROW_GAP, _BRICK_GAP, _FALL = 0.16, 0.035, 0.42


def _wall_grid(x, y, w, h, rows):
    bh = h / rows
    cols = max(2, int(round(w / (bh * 2.05))))
    bw = w / cols
    bricks = []
    for r in range(rows):                    # r = 0 bottom row
        yy = y + h - (r + 1) * bh
        if r % 2 == 0:
            xs = [(x + i * bw, bw) for i in range(cols)]
        else:
            xs = [(x, bw / 2)] + [(x + bw / 2 + i * bw, bw) for i in range(cols - 1)] + \
                 [(x + w - bw / 2, bw / 2)]
        for i, (bx, ww) in enumerate(xs):
            bricks.append((r, i, bx, yy, ww, bh))
    return bricks, bh, cols


def brick_wall_land_times(t0, rows=6, speed=1.0):
    """Time each row's first brick lands (for thud SFX). Pure, no ctx."""
    return [t0 + (r * _ROW_GAP + _FALL * 0.62) / speed for r in range(rows)]


def _drop(u, drop):
    """Fall + two small bounces. Returns (dy, squash)."""
    uc = 0.62
    if u < uc:
        p = u / uc
        return -drop * (1 - p * p), -0.05 * p      # slight stretch while falling
    v = (u - uc) / (1 - uc)
    sq = 0.2 * max(0.0, 1 - v / 0.22) + 0.06 * max(0.0, 1 - abs(v - 0.6) / 0.12)
    if v < 0.6:
        q = v / 0.6
        return -drop * 0.06 * 4 * q * (1 - q), sq
    q = (v - 0.6) / 0.4
    return -drop * 0.015 * 4 * q * (1 - q), sq


def _brick_shape(ctx, bx, by, bw, bh, tint, g=4.0):
    rrect(ctx, bx + g, by + g, bw - 2 * g, bh - 2 * g, 7)
    _src(ctx, tint)
    ctx.fill()
    ctx.save()
    rrect(ctx, bx + g, by + g, bw - 2 * g, bh - 2 * g, 7)
    ctx.clip()
    ctx.rectangle(bx, by + bh - g - bh * 0.24, bw, bh * 0.3)
    _f(ctx, "brick_dk", 0.75)
    ctx.move_to(bx + g + 10, by + g + 7)
    ctx.line_to(bx + bw - g - 14, by + g + 7)
    _s(ctx, "#e28a6c", 4, 0.8)
    ctx.restore()
    rrect(ctx, bx + g, by + g, bw - 2 * g, bh - 2 * g, 7)
    _s(ctx, INK, LW)


def brick_wall(ctx, x, y, w, h, t, t0, rows=6, window=None, label=None, speed=1.0,
               drop=380, seed=0):
    """THE recurring motif: a brick wall that builds itself row by row.

    (x, y) = TOP-LEFT of the finished wall, w x h its size (typ. 760 x 560).
    Bricks (running bond, ≈2:1) drop from `drop` px above starting at t0,
    bottom row first (row every 0.16 s, bricks 0.035 s apart, left→right),
    land with a squash + two small bounces and a dust puff; mortar fills in
    behind each finished row. 6 rows x ~5 bricks finish ≈ 1.45 s after t0
    (divide by `speed`). Nothing is drawn before t0.

    window: the SERVICE WINDOW (helpful stuff passes through), given RELATIVE
      to the wall's top-left, in px:  (wx, wy, ww, wh)  or a dict
      {"rect": (wx, wy, ww, wh), "t_open": None|time (shutter rolls up then),
       "fill": None|"#ffe9b0" (interior colour; None = see-through),
       "awning": True, "sign": None|"OPEN"}.
      Bricks are cut around it; the frame + counter + striped awning pop in
      once the rows around it are laid.
    label: painted text (str, or dict {"text", "color", "size", "y": 0..1 rel})
      that wipes on after the wall is complete (e.g. "NOPE", "HARM-FREE ZONE").

    Returns {"t_done", "land_times" (per row), "window": world rect | None,
             "rect": (x, y, w, h)}.
    """
    ctx.new_path()
    bricks, bh, cols = _wall_grid(x, y, w, h, rows)
    sp = max(0.05, speed)
    win = None
    if window is not None:
        win = dict(window) if isinstance(window, dict) else {"rect": tuple(window)}
        win.setdefault("t_open", None)
        win.setdefault("fill", None)
        win.setdefault("awning", True)
        win.setdefault("sign", None)
        wx, wy, ww, wh = win["rect"]
        win["world"] = (x + wx, y + wy, ww, wh)

    def start_of(r, i):
        return t0 + (r * _ROW_GAP + i * _BRICK_GAP + hash01(r * 17 + i, seed) * 0.02) / sp

    fall = _FALL / sp
    row_done = {}
    for (r, i, bx, by, bw_, bh_) in bricks:
        row_done[r] = max(row_done.get(r, 0), start_of(r, i) + fall)
    t_done = max(row_done.values())
    land = brick_wall_land_times(t0, rows, speed)
    res = {"t_done": t_done, "land_times": land,
           "window": win["world"] if win else None, "rect": (x, y, w, h)}
    if t < t0:
        return res

    def win_cut(c):
        if win:
            X, Y, WW, WH = win["world"]
            c.rectangle(x - 50, y - drop - 400, w + 100, h + drop + 500)
            c.rectangle(X, Y, WW, WH)
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            c.clip()
            c.set_fill_rule(cairo.FILL_RULE_WINDING)

    ctx.save()
    win_cut(ctx)
    # mortar behind finished rows
    for r in range(rows):
        a = seg(t, row_done[r], row_done[r] + 0.15)
        if a > 0:
            yy = y + h - (r + 1) * bh
            ctx.rectangle(x, yy, w, bh)
            _f(ctx, "mortar", a)
    if t >= t_done:
        a = seg(t, t_done, t_done + 0.2)
        ctx.rectangle(x, y, w, h)
        _s(ctx, INK, LW, a)
    # bricks
    tints = [PAL["brick"], "#c05d44", "#a94a35"]
    puffs = []
    for (r, i, bx, by, bw_, bh_) in bricks:
        st = start_of(r, i)
        if t < st:
            continue
        if win:
            X, Y, WW, WH = win["world"]
            if bx >= X and bx + bw_ <= X + WW and by >= Y and by + bh_ <= Y + WH:
                continue
        u = seg(t, st, st + fall)
        dy, sq = _drop(u, drop)
        a = clamp((t - st) / 0.05)
        tint = tints[int(hash01(r * 31 + i, seed + 5) * 3) % 3]
        ctx.save()
        cx_, base = bx + bw_ / 2, by + bh_
        ctx.translate(cx_, base + dy)
        ctx.scale(1 + sq * 0.7, 1 - sq)
        ctx.translate(-cx_, -base)
        if a < 1:
            ctx.push_group()
            _brick_shape(ctx, bx, by, bw_, bh_, tint)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
        else:
            _brick_shape(ctx, bx, by, bw_, bh_, tint)
        ctx.restore()
        tl = st + fall * 0.62
        if (r == 0 or r == rows - 1) and tl <= t < tl + 0.3:
            puffs.append((bx, bw_, base, (t - tl) / 0.3))
    ctx.restore()
    for (bx, bw_, base, q) in puffs:
        e = ease_out(q)
        for sgn in (-1, 1):
            px_ = bx + bw_ / 2 + sgn * (bw_ * 0.42 + e * 34)
            for (ox, oy, rr) in ((0, 0, 15), (sgn * 15, -9, 11), (-sgn * 10, -14, 9)):
                circle(ctx, px_ + ox * (1 + e), base - 10 - e * 14 + oy, rr * (0.7 + 0.8 * e))
            ctx.set_source_rgba(*C("#f3e6d6", 0.85 * (1 - q) ** 1.5))
            ctx.fill()

    # service window
    if win:
        X, Y, WW, WH = win["world"]
        rb = int((y + h - (Y + WH)) // bh)        # full rows below the window
        tw = row_done[rb - 1] if rb >= 1 else t0 + 0.1 / sp
        k = pop(t, tw - 0.02, 0.35)
        if k > 0.01:
            with saved(ctx, X + WW / 2, Y + WH / 2, k) as c:
                c.translate(-(X + WW / 2), -(Y + WH / 2))
                if win["fill"]:
                    c.rectangle(X, Y, WW, WH)
                    _f(c, win["fill"])
                # shutter
                op = 1.0
                if win["t_open"] is not None:
                    op = ease_in_out(seg(t, win["t_open"], win["t_open"] + 0.5))
                if op < 1:
                    sh = WH * (1 - op)
                    c.rectangle(X, Y, WW, sh)
                    _f(c, "steel")
                    for yy in range(int(Y + 14), int(Y + sh), 18):
                        c.move_to(X, yy)
                        c.line_to(X + WW, yy)
                    _s(c, "steel_dk", 4)
                    c.rectangle(X, Y + sh - 12, WW, 12)
                    _fs(c, "steel_dk", INK, 3)
                    if sh > 40:
                        rrect(c, X + WW / 2 - 22, Y + sh - 20, 44, 10, 5)
                        _fs(c, "#c9cfdc", INK, 3)
                # frame
                fw = 16
                c.rectangle(X - fw, Y - fw, WW + 2 * fw, fw)
                c.rectangle(X - fw, Y, fw, WH)
                c.rectangle(X + WW, Y, fw, WH)
                _fs(c, "#3a6f8f", INK, 4)
                c.rectangle(X - fw, Y - fw, WW + 2 * fw, WH + fw)
                _s(c, INK, LW)
                c.rectangle(X, Y, WW, WH)
                _s(c, INK, 4)
                # counter
                rrect(c, X - fw - 18, Y + WH - 4, WW + 2 * fw + 36, 26, 6)
                _fs(c, "#c9915a", INK, LW)
                c.move_to(X - fw - 10, Y + WH + 3)
                c.line_to(X + WW + fw + 10, Y + WH + 3)
                _s(c, "#e8b47e", 4)
                if win["awning"]:
                    aw, ah = WW + 2 * fw + 40, 58
                    ax0, ay0 = X - fw - 20, Y - fw - ah + 10
                    n = max(4, int(aw / 46))
                    sw_ = aw / n
                    for j in range(n):
                        poly(c, [(ax0 + j * sw_ + 10, ay0), (ax0 + (j + 1) * sw_ + 10, ay0),
                                 (ax0 + (j + 1) * sw_, ay0 + ah), (ax0 + j * sw_, ay0 + ah)])
                        _f(c, "bubble_ai" if j % 2 == 0 else "white")
                        c.arc(ax0 + (j + 0.5) * sw_, ay0 + ah, sw_ / 2, 0, math.pi)
                        _fs(c, "bubble_ai" if j % 2 == 0 else "white", INK, 4)
                    poly(c, [(ax0 + 10, ay0), (ax0 + aw + 10, ay0), (ax0 + aw, ay0 + ah),
                             (ax0, ay0 + ah)])
                    _s(c, INK, LW)
                if win["sign"]:
                    label_tag(c, X + WW / 2, Y - fw - (70 if win["awning"] else 30),
                              win["sign"], "ai_accent", 28)
    # painted label
    if label and t >= t_done:
        lab = label if isinstance(label, dict) else {"text": str(label)}
        size = lab.get("size", min(130, w * 0.16))
        col = lab.get("color", "white")
        if "y" in lab:
            ly = y + h * lab["y"]
        elif win:
            X, Y, WW, WH = win["world"]
            top_edge = Y - 16 - (48 if win["awning"] else 0) - (56 if win["sign"] else 0)
            top_free = top_edge - y
            bot_free = (y + h) - (Y + WH + 26)
            if top_free >= bot_free:
                ly = y + top_free / 2
                size = min(size, top_free * 0.95)
            else:
                ly = Y + WH + 26 + bot_free / 2
                size = min(size, bot_free * 0.95)
        else:
            ly = y + h / 2
        p = ease_out(seg(t, t_done + 0.1, t_done + 0.5))
        if p > 0:
            ctx.save()
            ctx.rectangle(x, y - 40, w * p, h + 80)
            ctx.clip()
            with saved(ctx, x + w / 2, ly - size * 0.04, 1.0, -0.04) as c:
                _text(c, lab["text"], 4, size * 0.36 + 6, size, INK, "comic", "center")
                _text(c, lab["text"], 0, size * 0.36, size, col, "comic", "center")
            ctx.restore()
    return res


# ===========================================================================
# STAMP
# ===========================================================================
def _glyph_runs(txt):
    out, cur = [], ""
    for ch in txt:
        if ch in "✓✔":
            if cur:
                out.append(("t", cur))
                cur = ""
            out.append(("check", ch))
        elif ch in "✗✘✕❌":
            if cur:
                out.append(("t", cur))
                cur = ""
            out.append(("x", ch))
        else:
            cur += ch
    if cur:
        out.append(("t", cur))
    return out


def stamp_impact(t_in):
    """Time the stamp hits the page (for a 'thunk' SFX)."""
    return t_in + 0.11


def stamp(ctx, x, y, txt, t, t_in, color="danger", size=1.0, rot=-0.12, t_out=None,
          font="black"):
    """Rubber-stamp SLAM. (x, y) = centre; size=1 -> text 110 px (box ≈ text + margins).

    Drops from 2.3x scale (with a twist), hits at t_in+0.11 (see
    stamp_impact), squashes to 0.9 and springs back with overshoot; impact
    tick-lines burst out. Double-border box, slightly distressed ink.
    "✓" / "✗" characters in txt are drawn as vector marks ("HELPFUL ✓").
    color: e.g. "danger" (NOPE), "safe" (HELPFUL ✓), "warn".
    t_out: optional fade-out start.
    """
    if t < t_in:
        return
    ctx.new_path()
    d = t - t_in
    hit = 0.11
    if d < hit:
        q = ease_in(d / hit)
        sc = lerp(2.3, 0.9, q)
        r_ = rot - 0.35 * (1 - q)
        a = clamp(d / 0.05)
    else:
        q = seg(d, hit, hit + 0.28)
        sc = 0.9 + 0.1 * ease_out_back(q, 3.2)
        r_ = rot
        a = 1.0
    if t_out is not None and t > t_out:
        a *= 1 - seg(t, t_out, t_out + 0.25)
    if a <= 0.01:
        return
    fs = 110 * size
    runs = _glyph_runs(txt)
    set_font(ctx, font, fs)
    widths = []
    for kind, s_ in runs:
        widths.append(ctx.text_extents(s_)[4] if kind == "t" else fs * 0.82)
    tw = sum(widths)
    bw, bh = tw + fs * 0.7, fs * 1.32
    with saved(ctx, x, y, sc, r_, alpha_=a) as c:
        c.push_group()
        rrect(c, -bw / 2, -bh / 2, bw, bh, fs * 0.16)
        _s(c, color, fs * 0.11)
        rrect(c, -bw / 2 + fs * 0.13, -bh / 2 + fs * 0.13, bw - fs * 0.26, bh - fs * 0.26,
              fs * 0.08)
        _s(c, color, fs * 0.04)
        xx = -tw / 2
        for (kind, s_), ww in zip(runs, widths):
            if kind == "t":
                _text(c, s_, xx, fs * 0.36, fs, color, font, "left")
            elif kind == "check":
                _check_path(c, xx + ww / 2, -fs * 0.0, fs * 0.8)
                _s(c, color, fs * 0.17)
            else:
                _x_path(c, xx + ww / 2, 0, fs * 0.7)
                _s(c, color, fs * 0.17)
            xx += ww
        # distress: knock out tiny specks (static per text)
        c.set_operator(cairo.OPERATOR_DEST_OUT)
        hs = sum(ord(ch) for ch in txt)
        for i in range(46):
            sx = (hash01(i, hs) - 0.5) * bw
            sy = (hash01(i, hs + 1) - 0.5) * bh
            circle(c, sx, sy, fs * (0.008 + 0.016 * hash01(i, hs + 2)))
            c.set_source_rgba(0, 0, 0, 0.85)
            c.fill()
        c.set_operator(cairo.OPERATOR_OVER)
        c.pop_group_to_source()
        c.paint_with_alpha(0.95)
    # impact ticks
    if hit <= d < hit + 0.3:
        q = (d - hit) / 0.3
        with saved(ctx, x, y, 1.0, rot):
            for j in range(10):
                ang = j / 10 * 2 * math.pi + 0.3
                rx_, ry_ = bw * 0.5 + 20, bh * 0.5 + 20
                r0 = 1.0 + q * 0.25
                cx_ = math.cos(ang)
                cy_ = math.sin(ang)
                p0 = (cx_ * rx_ * r0, cy_ * ry_ * r0)
                p1 = (cx_ * (rx_ * r0 + 40 * (1 - q) + 10), cy_ * (ry_ * r0 + 40 * (1 - q) + 10))
                ctx.move_to(*p0)
                ctx.line_to(*p1)
            _s(ctx, color, 8 * (1 - q) + 1, 1 - q)


# ===========================================================================
# EMOTES
# ===========================================================================
def _em_sweat(c, lt):
    dy = min(lt, 1.2) * 16
    for (ox, oy, sc) in ((0, 0, 1.0), (30, 26, 0.5)):
        with saved(c, ox, oy + dy * sc, sc):
            c.move_to(0, -50)
            c.curve_to(16, -22, 30, -2, 30, 16)
            c.arc(0, 16, 30, 0, math.pi)
            c.curve_to(-30, -2, -16, -22, 0, -50)
            c.close_path()
            _fs(c, "#8fd8ff", INK, LW)
            c.move_to(-14, 8)
            c.curve_to(-16, 20, -10, 30, -2, 32)
            _s(c, "white", 6, 0.85)


def _em_anger(c, lt):
    pulse = 1 + 0.14 * max(0.0, math.sin(lt * 2 * math.pi * 2.2))
    c.scale(pulse, pulse)
    for q in range(4):
        c.save()
        c.rotate(q * math.pi / 2)
        c.move_to(-19, -54)
        c.line_to(-19, -33)
        c.curve_to(-19, -23, -23, -19, -33, -19)
        c.line_to(-54, -19)
        c.restore()
    path = c.copy_path()
    _s(c, INK, 25)
    c.append_path(path)
    _s(c, "danger", 14)


def _em_char(c, lt, ch, col, wob):
    r_ = math.sin(lt * 2 * math.pi * 0.9) * 0.12 * wob
    dy = math.sin(lt * 2 * math.pi * 1.1) * 6 * wob
    with saved(c, 0, dy, 1.0, r_):
        _text(c, ch, 0, 42, 124, col, "title", "center", outline=INK, outline_w=16,
              shadow=(5, 7, (0, 0, 0, 0.35)))


def _em_sparkle(c, lt):
    for j, (ox, oy, r, col) in enumerate(((0, 0, 44, "white"), (44, -38, 22, "ai_accent"),
                                          (-40, 30, 18, "ai_accent"))):
        tw = 0.6 + 0.4 * math.sin(lt * 2 * math.pi * 1.3 + j * 2.1)
        _star4(c, ox, oy, r * tw, lt * 0.8 * (1 if j % 2 else -1))
        _fs(c, col, INK, 4)


def _em_heart(c, lt):
    ph = (lt * 1.3) % 1.0
    beat = 1 + 0.16 * (math.exp(-((ph - 0.1) / 0.06) ** 2) + 0.7 * math.exp(-((ph - 0.3) / 0.06) ** 2))
    c.scale(beat, beat)
    _heart_path(c, 0, 0, 44)
    _fs(c, "#ff5c8a", INK, LW)
    ellipse(c, -18, -18, 9, 6, -0.6)
    _f(c, "white", 0.8)


def _em_bulb(c, lt):
    on = smoothstep(seg(lt, 0.1, 0.25))
    if on > 0:
        _glow(c, 0, -14, 110, "ai_accent", 0.35 * on)
        for j in range(7):
            a = -math.pi + j * math.pi / 6
            fl = 1 + 0.12 * math.sin(lt * 9 + j)
            c.move_to(math.cos(a) * 60, -14 + math.sin(a) * 60)
            c.line_to(math.cos(a) * (60 + 22 * on * fl), -14 + math.sin(a) * (60 + 22 * on * fl))
        _s(c, "ai_accent", 7)
    c.move_to(-20, 24)
    c.curve_to(-22, 10, -44, -2, -44, -22)
    c.arc(0, -22, 44, math.pi, 2 * math.pi)
    c.curve_to(44, -2, 22, 10, 20, 24)
    c.close_path()
    _fs(c, _mix("#fff1b0", "ai_accent", 0.5 * (1 - on)) if on > 0 else "#b8b0a0", INK, LW)
    for yy in (28, 40):
        rrect(c, -20, yy - 4, 40, 10, 5)
        _fs(c, "#a9adbb", INK, 3.5)
    c.move_to(-8, 2)
    c.line_to(-8, -18)
    c.line_to(0, -10)
    c.line_to(8, -18)
    c.line_to(8, 2)
    _s(c, "warn", 4)


def _em_zzz(c, lt):
    for j in range(3):
        ph = (lt * 0.55 + j / 3) % 1.0
        a = clamp(math.sin(ph * math.pi) * 1.6)
        _text(c, "Z", -24 + ph * 56, 34 - ph * 96, 36 + ph * 36, C("ai_eye", a), "round",
              "center", outline=C(INK, a), outline_w=8)


def emote(ctx, kind, x, y, s, t, t_in, t_out=None):
    """Anime-style reaction emote. (x, y) = centre; s=1 -> ~110 px icon.

    kind: "sweat" (drops slide down), "anger" (💢 pulsing vein), "question"
    (bobbing ?), "exclaim" (! with jolt), "sparkle" (twinkling stars),
    "heart" (double heartbeat), "lightbulb" (switches on, rays), "zzz"
    (Z's float up). Pops in at t_in (ease_out_back); t_out pops it out.
    Typical placement: just above/beside a character's head.
    """
    if t < t_in:
        return
    k = pop(t, t_in, 0.3)
    if t_out is not None and t >= t_out:
        k *= 1 - ease_in(seg(t, t_out, t_out + 0.18))
    if k < 0.01:
        return
    ctx.new_path()
    lt = t - t_in
    jolt = 0.0
    if kind == "exclaim":
        jolt = math.sin(lt * 70) * 6 * clamp(1 - lt / 0.3)
    with saved(ctx, x + jolt, y, s * k) as c:
        if kind == "sweat":
            _em_sweat(c, lt)
        elif kind == "anger":
            _em_anger(c, lt)
        elif kind == "question":
            _em_char(c, lt, "?", "ai_accent", 1.0)
        elif kind == "exclaim":
            _em_char(c, lt, "!", "danger", 0.3)
        elif kind == "sparkle":
            _em_sparkle(c, lt)
        elif kind == "heart":
            _em_heart(c, lt)
        elif kind == "lightbulb":
            _em_bulb(c, lt)
        elif kind == "zzz":
            _em_zzz(c, lt)


# ===========================================================================
# SPARKLES
# ===========================================================================
def sparkles(ctx, x, y, r, t, n=6, seed=0, color="white", size=1.0):
    """n twinkling four-point stars scattered within radius r of (x, y).

    Each star blinks on/off on its own phase (≈1.4 s period) and slowly
    turns. Alternates `color` and gold. size scales the stars (base ≈ 18 px).
    """
    ctx.new_path()
    for i in range(n):
        ang = hash01(i, seed + 201) * 2 * math.pi
        rr = r * (0.35 + 0.65 * math.sqrt(hash01(i, seed + 202)))
        sx, sy = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        ph = hash01(i, seed + 203)
        per = 1.1 + 0.6 * hash01(i, seed + 204)
        v = math.sin(((t / per) + ph) * 2 * math.pi)
        k = smoothstep((v + 0.45) / 1.45)
        if k < 0.03:
            continue
        rad = (18 + 20 * hash01(i, seed + 205)) * size * k
        col = color if i % 2 == 0 else "ai_accent"
        _star4(ctx, sx, sy, rad, t * 0.6 + ph * 3)
        _f(ctx, col, 0.95)


# ===========================================================================
# FUTURE TREE ("10 steps ahead")
# ===========================================================================
_KIND_COL = {"harm": "danger", "safe": "safe", "neutral": "ai_glow"}


def future_tree_layout(x, y, s, t0, branches, direction="down", step=0.55, judge=None,
                       spread=None, level=None):
    """Pure layout/timing of future_tree (no ctx). Returns list of node dicts:
    {"label", "kind", "icon", "x", "y", "depth", "parent" (index|None),
     "t_show", "t_judge" (None for neutral), "r"} — index 0 is the root."""
    level = level or 250 * s

    def leaves(n):
        ch = n.get("children") or []
        return sum(leaves(c) for c in ch) if ch else 1

    total = sum(leaves(b) for b in branches) or 1
    span = spread if spread is not None else min(880.0, total * 220 * s)
    slot = span / total
    nodes = [{"label": None, "kind": "neutral", "icon": None, "x": x, "y": y, "depth": 0,
              "parent": None, "t_show": t0, "t_judge": None, "r": 42 * s}]

    def place(n, depth, lo, parent, pkind, sib):
        nl = leaves(n)
        cross = -span / 2 + (lo + nl / 2) * slot
        along = depth * level
        px, py = (x + cross, y + along) if direction == "down" else (x + along, y + cross)
        kind = n.get("kind", pkind)
        par = nodes[parent]
        ts = n.get("t", par["t_show"] + step + sib * 0.12)
        tj = None
        if kind in ("harm", "safe"):
            if "judge" in n:
                tj = n["judge"]
            elif judge is not None:
                tj = max(judge + 0.12 * (depth - 1), ts + 0.15)
            else:
                tj = ts + 0.5
        nodes.append({"label": n.get("label"), "kind": kind, "icon": n.get("icon"),
                      "x": px, "y": py, "depth": depth, "parent": parent, "t_show": ts,
                      "t_judge": tj, "r": 33 * s})
        me = len(nodes) - 1
        acc = lo
        for j, c in enumerate(n.get("children") or []):
            place(c, depth + 1, acc, me, kind, j)
            acc += leaves(c)

    acc = 0
    for j, b in enumerate(branches):
        place(b, 1, acc, 0, b.get("kind", "neutral"), j)
        acc += leaves(b)
    return nodes


def _icon(ctx, name, x, y, r, col):
    """Tiny glyph inside a tree node / chip. r ~ node radius."""
    k = r / 30.0
    with saved(ctx, x, y, k) as c:
        if name == "bomb":
            circle(c, 0, 3, 14)
            _f(c, col)
            c.rectangle(-4, -15, 8, 7)
            _f(c, col)
            c.move_to(2, -15)
            c.curve_to(6, -24, 12, -20, 14, -26)
            _s(c, col, 3)
        elif name == "heart":
            _heart_path(c, 0, 1, 15)
            _f(c, col)
        elif name == "book":
            poly(c, [(-17, -11), (0, -7), (17, -11), (17, 12), (0, 16), (-17, 12)])
            _f(c, col)
            c.move_to(0, -7)
            c.line_to(0, 16)
            _s(c, "ai_screen", 3)
        elif name == "gift":
            c.rectangle(-15, -6, 30, 22)
            c.rectangle(-17, -12, 34, 8)
            _f(c, col)
            c.move_to(0, -12)
            c.line_to(0, 16)
            _s(c, "ai_screen", 3)
            ellipse(c, -6, -16, 6, 4, 0.5)
            ellipse(c, 6, -16, 6, 4, -0.5)
            _s(c, col, 3)
        elif name == "star":
            pts = []
            for j in range(10):
                a = -math.pi / 2 + j * math.pi / 5
                rr = 17 if j % 2 == 0 else 7.5
                pts.append((math.cos(a) * rr, math.sin(a) * rr + 1))
            poly(c, pts)
            _f(c, col)
        elif name == "skull":
            circle(c, 0, -3, 13)
            c.rectangle(-8, 4, 16, 9)
            _f(c, col)
            for ex in (-5, 5):
                circle(c, ex, -3, 3.5)
            _f(c, "ai_screen")
        elif name == "people":
            for ox in (-8, 8):
                circle(c, ox, -7, 6)
                c.move_to(ox - 10, 15)
                c.curve_to(ox - 10, 0, ox + 10, 0, ox + 10, 15)
                c.close_path()
            _f(c, col)
        elif name == "bulb":
            circle(c, 0, -5, 11)
            c.rectangle(-5, 5, 10, 8)
            _f(c, col)
        else:  # question
            _text(c, "?", 0, 11, 32, col, "round")


def future_tree(ctx, x, y, s, t, t0, branches, direction="down", step=0.55, judge=None,
                root_label=None, spread=None, level=None, label_size=32):
    """The AI's "10 steps ahead" vision: a glowing branching flowchart.

    (x, y) = ROOT node centre (the request). Children grow DOWN from it
    (direction="down", levels 250*s apart) or RIGHT ("right"). Leaves are
    spread evenly over `spread` px (default min(880, leaves*220*s)) centred
    on x (or y). s=1: nodes r=33 (root 42), label chips 32 px font below each
    node; `root_label` sits ABOVE the root. Edges leave from under a label chip.

    branches: list of node dicts (the root's children), recursively:
        {"label": "write the story",     # short chip text (≤ ~16 chars) or None
         "kind": "safe",                 # "harm" | "safe" | "neutral"; inherits
                                         #   from the parent when omitted
         "icon": "book",                 # optional glyph: bomb heart book gift star
                                         #   skull people bulb question
         "children": [ ... ],            # optional
         "t": 4.0, "judge": 5.1}         # optional absolute show / verdict times
    Reveal: root pops at t0; each level's paths grow and nodes pop `step`
    seconds after their parent (siblings +0.12 s). Everything starts cyan
    ("simulating"); at each node's verdict time (default show+0.5 s, or the
    global `judge` time, staggered 0.12 s per depth) HARM nodes turn red,
    shake, get an X and a dashed red path; SAFE nodes turn green with a
    ring pulse and a check badge. Neutral nodes stay cyan.
    Returns the node list from future_tree_layout (world x/y + times).
    """
    nodes = future_tree_layout(x, y, s, t0, branches, direction, step, judge, spread, level)
    nodes[0]["label"] = root_label
    if t < t0:
        return nodes
    ctx.new_path()

    def state(n):
        if n["t_judge"] is None or t < n["t_judge"]:
            return C("ai_glow"), 0.0
        u = smoothstep(seg(t, n["t_judge"], n["t_judge"] + 0.25))
        return _mix("ai_glow", _KIND_COL[n["kind"]], u), u

    def shake_dx(n):
        if n["kind"] != "harm" or n["t_judge"] is None or t < n["t_judge"]:
            return 0.0
        d = t - n["t_judge"]
        return math.sin(d * 55) * 9 * s * clamp(1 - d / 0.45)

    # edges
    for n in nodes[1:]:
        par = nodes[n["parent"]]
        e0 = par["t_show"] + 0.08
        e1 = max(n["t_show"], e0 + 0.15)
        p = ease_in_out(seg(t, e0, e1))
        if p <= 0:
            continue
        col, u = state(n)
        dxs = shake_dx(n)
        if direction == "down":
            off = par["r"]
            if par["label"] and n["parent"] != 0:
                off = par["r"] + label_size * s * 1.9
            p0 = (par["x"], par["y"] + off)
            p3 = (n["x"] + dxs, n["y"] - n["r"])
            mid = (p0[1] + p3[1]) / 2
            pts = _cbez(p0, (p0[0], mid), (p3[0], mid), p3, 22)
        else:
            p0 = (par["x"] + par["r"], par["y"])
            p3 = (n["x"] - n["r"] + dxs, n["y"])
            mid = (p0[0] + p3[0]) / 2
            pts = _cbez(p0, (mid, p0[1]), (mid, p3[1]), p3, 22)
        _partial_polyline(ctx, pts, p)
        path = ctx.copy_path()
        ctx.set_source_rgba(col[0], col[1], col[2], 0.20)
        ctx.set_line_width(20 * s)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.append_path(path)
        if n["kind"] == "harm" and u > 0.5:
            ctx.set_dash([16 * s, 13 * s])
        ctx.set_source_rgba(*col)
        ctx.set_line_width(6.5 * s)
        ctx.stroke()
        ctx.set_dash([])
        # travelling spark while growing
        if p < 1:
            tip = pts[min(len(pts) - 1, int(p * (len(pts) - 1)))]
            circle(ctx, tip[0], tip[1], 9 * s)
            _f(ctx, "white", 0.9)
    # nodes
    for i, n in enumerate(nodes):
        if t < n["t_show"]:
            continue
        k = pop(t, n["t_show"], 0.3)
        if k < 0.01:
            continue
        col, u = state(n)
        dxs = shake_dx(n)
        nx, ny, r = n["x"] + dxs, n["y"], n["r"] * k
        circle(ctx, nx, ny, r * 1.45)
        ctx.set_source_rgba(col[0], col[1], col[2], 0.16)
        ctx.fill()
        circle(ctx, nx, ny, r)
        fillc = "ai_screen"
        if n["kind"] == "harm" and u > 0:
            fillc = _mix("ai_screen", "#3a0d1c", u)
        elif n["kind"] == "safe" and u > 0:
            fillc = _mix("ai_screen", "#0c3324", u)
        ctx.set_source_rgba(*C(fillc))
        ctx.fill_preserve()
        ctx.set_source_rgba(*col)
        ctx.set_line_width(6 * s)
        ctx.stroke()
        if n["icon"]:
            _icon(ctx, n["icon"], nx, ny, r * 0.95, col)
        elif i == 0:
            circle(ctx, nx, ny, r * 0.32)
            ctx.set_source_rgba(*col)
            ctx.fill()
        # safe ring pulse
        if n["kind"] == "safe" and n["t_judge"] is not None and t >= n["t_judge"]:
            q = seg(t, n["t_judge"], n["t_judge"] + 0.6)
            if q < 1:
                circle(ctx, nx, ny, r * (1 + 1.3 * ease_out(q)))
                _s(ctx, "safe", 5 * s, 0.8 * (1 - q))
        # label chip
        if n["label"]:
            fsz = label_size * s
            if i == 0:
                lx, ly = nx, ny - n["r"] - fsz * 1.05
            else:
                lx, ly = nx, ny + n["r"] + fsz * 1.15
            a = clamp(seg(t, n["t_show"] + 0.1, n["t_show"] + 0.3))
            if a > 0:
                set_font(ctx, "ui", fsz)
                tw = ctx.text_extents(n["label"])[4]
                cw, ch = tw + fsz * 0.9, fsz * 1.45
                rrect(ctx, lx - cw / 2, ly - ch / 2, cw, ch, ch / 2)
                ctx.set_source_rgba(*C("ui_dark", 0.85 * a))
                ctx.fill_preserve()
                ctx.set_source_rgba(col[0], col[1], col[2], a)
                ctx.set_line_width(3 * s)
                ctx.stroke()
                _text(ctx, n["label"], lx, ly + fsz * 0.35, fsz,
                      (1, 1, 1, a), "ui", "center")
        # verdict marks
        if n["t_judge"] is not None and t >= n["t_judge"]:
            if n["kind"] == "harm":
                x_mark(ctx, nx, ny, 0.42 * s, t, n["t_judge"])
            elif n["kind"] == "safe":
                bxx, byy = nx + n["r"] * 0.85, ny - n["r"] * 0.85
                kk = pop(t, n["t_judge"], 0.3)
                if kk > 0.01:
                    circle(ctx, bxx, byy, 15 * s * kk)
                    _fs(ctx, "safe", INK, 3.5 * s)
                    _check_path(ctx, bxx, byy, 20 * s * kk)
                    _s(ctx, "white", 4.5 * s)
    return nodes


# ===========================================================================
# SCROLL DOCUMENT
# ===========================================================================
def scroll_doc(ctx, x, y, w, h, title, lines, t, t_in, font_size=34, unroll=0.6,
               line_gap=0.22, title_font="title"):
    """Parchment scroll (the AI's story / plan) that unrolls downward.

    (x, y) = TOP-LEFT of the unrolled paper area; w x h its full size
    (typ. 700 x 900). Top roller pops at t_in, paper unrolls over `unroll`
    s, then title and lines fade/slide in one by one every `line_gap` s.
    lines: list of items:
      "plain text"                         -> wrapped paragraph (Nunito, dark ink)
      {"text": "...", "color": "...", "size": 30}
      {"redact": "the recipe stays off the page"}  -> a strip of tiny BRICKS
          walling off that part of the page, with a small caption chip.
      {"gap": 20}                          -> vertical space
    Text is clipped to the visible paper. Returns content height used.
    """
    ctx.new_path()
    if t < t_in:
        return 0
    k = pop(t, t_in, 0.3)
    if k < 0.01:
        return 0
    u = ease_out(seg(t, t_in + 0.15, t_in + 0.15 + unroll))
    ph = (h - 30) * u
    rx0, rx1 = x - 22, x + w + 22
    with saved(ctx, x + w / 2, y, (k, 1.0)) as c:
        c.translate(-(x + w / 2), -y)
        # paper
        if ph > 1:
            rrect(c, x + 6, y + 14 + 10, w, ph, 6)
            _f(c, INK, 0.35)
            c.rectangle(x, y + 14, w, ph)
            _fs(c, "parch", INK, LW)
            c.rectangle(x + LW / 2, y + 14, 18, ph)
            c.rectangle(x + w - 18 - LW / 2, y + 14, 18, ph)
            _f(c, "parch_dk", 0.6)
        # content
        c.save()
        c.rectangle(x, y + 14, w, max(0, ph))
        c.clip()
        pad = 44
        yy = y + 40
        t_txt = t_in + 0.15 + unroll * 0.55
        if title:
            a = clamp(seg(t, t_txt, t_txt + 0.25))
            if a > 0:
                tsz = font_size * 1.85
                _text(c, title, x + w / 2, yy + tsz * 0.9, tsz, (*C("suit")[:3], a),
                      title_font)
            yy += font_size * 1.85 * 1.2 + 10
            if a > 0:
                _wavy(c, x + w / 2 - 120, x + w / 2 + 120, yy, 5, 40)
                _s(c, "cape_in", 4, a)
            yy += 26
        for i, item in enumerate(lines):
            ti = t_txt + 0.3 + i * line_gap
            a = clamp(seg(t, ti, ti + 0.25))
            dx = (1 - ease_out(seg(t, ti, ti + 0.3))) * 16
            if isinstance(item, str):
                item = {"text": item}
            if "gap" in item:
                yy += item["gap"]
                continue
            if "redact" in item:
                bw_ = w - 2 * pad
                bh_ = font_size * 2.2
                if a > 0:
                    c.save()
                    rrect(c, x + pad + dx, yy, bw_, bh_, 8)
                    c.clip()
                    _src(c, "mortar", a)
                    c.paint()
                    rows_, bhh = 2, bh_ / 2
                    for r in range(rows_):
                        ww = bhh * 2.1
                        off = (r % 2) * ww / 2
                        xx = x + pad + dx - off
                        while xx < x + pad + dx + bw_:
                            rrect(c, xx + 3, yy + r * bhh + 3, ww - 6, bhh - 6, 4)
                            _fs(c, "brick", INK, 3, a)
                            xx += ww
                    c.restore()
                    rrect(c, x + pad + dx, yy, bw_, bh_, 8)
                    _s(c, INK, 4, a)
                    if item["redact"]:
                        label_tag(c, x + w / 2 + dx, yy + bh_ / 2, item["redact"], "ui_dark",
                                  font_size * 0.8)
                yy += bh_ + font_size * 0.6
                continue
            fsz = item.get("size", font_size)
            col = item.get("color", "#3b2a20")
            ls = wrap_lines(c, item["text"], w - 2 * pad, "ui", fsz)
            for l in ls:
                if a > 0:
                    cc = C(col)
                    _text(c, l, x + pad + dx, yy + fsz * 0.9, fsz, (cc[0], cc[1], cc[2], a),
                          "ui", "left")
                yy += fsz * 1.28
            yy += fsz * 0.35
        c.restore()
        # rollers
        for ry in ((y,) if ph <= 1 else (y, y + 14 + ph - 2)):
            rrect(c, rx0, ry - 8, rx1 - rx0, 42, 20)
            _fs(c, "frame", INK, LW)
            c.move_to(rx0 + 20, ry + 2)
            c.line_to(rx1 - 20, ry + 2)
            _s(c, "#9a6a43", 5)
            for kx in (rx0 - 14, rx1 + 14):
                circle(c, kx, ry + 13, 21)
                _fs(c, "gold", INK, LW)
                circle(c, kx - 6, ry + 7, 5)
                _f(c, "white", 0.55)
    return yy - y


# ===========================================================================
# SCREEN-LEVEL HELPERS: split_divider, iris, flash, title_card
# ===========================================================================
def split_divider(ctx, y, t, top="bubble_villain", bottom="ai_rim", badge=None):
    """Glowing horizontal divider for split screen (villain top / AI bottom).

    y = centre line of the divider (e.g. 900). A 16 px ink band with a
    purple glow above and a cyan glow below, plus a small light pulse that
    glides along it every ~3 s. badge: optional short text ("VS", "?") in a
    round chip at the centre.
    """
    ctx.new_path()
    for (yy, col) in ((y - 16, top), (y + 16, bottom)):
        for (wd, a) in ((40, 0.10), (22, 0.18)):
            ctx.move_to(-10, yy)
            ctx.line_to(W + 10, yy)
            _s(ctx, col, wd, a, cap=cairo.LINE_CAP_BUTT)
    ctx.rectangle(-10, y - 12, W + 20, 24)
    _f(ctx, INK)
    ctx.move_to(-10, y - 6)
    ctx.line_to(W + 10, y - 6)
    _s(ctx, _mix(top, "white", 0.25), 6, 1.0, cap=cairo.LINE_CAP_BUTT)
    ctx.move_to(-10, y + 6)
    ctx.line_to(W + 10, y + 6)
    _s(ctx, _mix(bottom, "white", 0.15), 6, 1.0, cap=cairo.LINE_CAP_BUTT)
    ph = (t / 3.2) % 1.0
    px = -100 + ph * (W + 200)
    ellipse(ctx, px, y, 80, 5)
    _f(ctx, "white", 0.7)
    if badge:
        circle(ctx, W / 2, y + 5, 52)
        _f(ctx, INK, 0.5)
        circle(ctx, W / 2, y, 52)
        _fs(ctx, "ui_dark", INK, LW)
        circle(ctx, W / 2, y, 42)
        _s(ctx, "ai_accent", 5)
        _text(ctx, badge, W / 2, y + 16, 44, "ai_accent", "title")


def iris(ctx, t, t0, t1, cx=540, cy=820, closing=True, color="black", ring="ai_accent"):
    """Classic cartoon iris wipe around (cx, cy).

    closing=True : full picture before t0, circle shrinks to black by t1
                   (black stays after t1).
    closing=False: black before t0, circle opens from (cx, cy) by t1.
    ring: thin coloured rim on the iris edge (None to disable).
    """
    p = ease_in_out(seg(t, t0, t1))
    if closing:
        if t < t0:
            return
        k = 1 - p
    else:
        if t >= t1:
            return
        k = p if t >= t0 else 0.0
    ctx.new_path()
    R = math.hypot(max(cx, W - cx), max(cy, H - cy)) + 20
    r = R * k
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(-50, -50, W + 100, H + 100)
    if r > 0.5:
        circle(ctx, cx, cy, r)
    _f(ctx, color)
    ctx.restore()
    if ring and 1 < r < R - 5:
        circle(ctx, cx, cy, r)
        _s(ctx, ring, 8)


def flash(ctx, a, color="white"):
    """Full-frame flash overlay at opacity a (0..1). Keep it short (3-5 frames)."""
    if a <= 0.001:
        return
    ctx.new_path()
    ctx.rectangle(-50, -50, W + 100, H + 100)
    _f(ctx, color, clamp(a))


def title_card(ctx, t, t_in, line1, line2=None, y=800, color="ai_accent", color2="white",
               size=None, burst=False, t_out=None, burst_color="ai_rim"):
    """Big bouncy title. Letters of line1 drop in one by one (0.045 s apart,
    ease_out_back, little twist) in "Luckiest Guy" with thick ink outline and
    drop shadow; line2 (smaller, Fredoka) slides up after. Centred at x=540,
    y = baseline of line1 (default 800). size: line1 font px (auto-fits 900 px,
    default ≤150). burst=True adds a static sunburst behind (scales in,
    `burst_color` at 10% opacity).
    t_out: optional quick shrink-out. Text settles fully (no idle motion).
    """
    if t < t_in:
        return
    ctx.new_path()
    out_k = 1.0
    if t_out is not None and t >= t_out:
        out_k = 1 - ease_in(seg(t, t_out, t_out + 0.25))
        if out_k <= 0.01:
            return
    fs = size or 150
    set_font(ctx, "title", fs)
    tw = ctx.text_extents(line1)[4]
    if tw > 900:
        fs *= 900 / tw
        set_font(ctx, "title", fs)
        tw = ctx.text_extents(line1)[4]
    if burst:
        kb = ease_out_back(seg(t, t_in, t_in + 0.4)) * out_k
        if kb > 0.01:
            with saved(ctx, W / 2, y - fs * 0.35, kb) as c:
                for j in range(16):
                    a0 = j * 2 * math.pi / 16
                    poly(c, [(0, 0), (math.cos(a0) * 700, math.sin(a0) * 700),
                             (math.cos(a0 + 0.2) * 700, math.sin(a0 + 0.2) * 700)])
                _f(c, burst_color, 0.10)
    with saved(ctx, W / 2, y, out_k) as c:
        xx = -tw / 2
        n = len(line1)
        for i, ch in enumerate(line1):
            set_font(c, "title", fs)
            adv = c.text_extents(ch)[4]
            ti = t_in + i * 0.045
            if ch.strip() and t >= ti:
                q = seg(t, ti, ti + 0.35)
                kk = ease_out_back(q, 2.4)
                if kk > 0.01:
                    rot = (1 - q) * (0.5 if i % 2 else -0.5) + (hash01(i, 7) - 0.5) * 0.08
                    dy = -(1 - ease_out(q)) * 60
                    with saved(c, xx + adv / 2, dy - fs * 0.35, kk, rot) as cc:
                        _text(cc, ch, 0, fs * 0.35 + fs * 0.07, fs, INK, "title", "center",
                              outline=INK, outline_w=fs * 0.16)
                        _text(cc, ch, 0, fs * 0.35, fs, color, "title", "center",
                              outline=INK, outline_w=fs * 0.12)
            xx += adv
        if line2:
            t2 = t_in + n * 0.045 + 0.15
            if t >= t2:
                q = ease_out(seg(t, t2, t2 + 0.35))
                f2 = fs * 0.42
                set_font(c, "round", f2)
                w2 = c.text_extents(line2)[4]
                if w2 > 900:
                    f2 *= 900 / w2
                cc2 = C(color2)
                _text(c, line2, 0, fs * 0.2 + f2 * 1.25 + (1 - q) * 30, f2,
                      (cc2[0], cc2[1], cc2[2], q), "round", "center",
                      outline=(*C(INK)[:3], q), outline_w=f2 * 0.2)


def panel(ctx, x, y, w, h, draw_fn, view=None, radius=0, border=True, border_col=INK):
    """Draw a whole 'shot' into a rectangle (no vignette): picture-in-picture,
    split screens, comic panels.

    draw_fn(ctx) draws in normal LOGICAL frame coords (e.g. lair_bg + villain).
    view = (vx, vy, vw): the region of the logical frame shown in the panel,
    width vw starting at (vx, vy) (height follows the panel aspect). Default
    (x, y, w) = no scaling, just clipping. radius: rounded corners.
    border: ink outline (LW) around the panel.
    """
    vx, vy, vw = view if view is not None else (x, y, w)
    ctx.save()
    if radius > 0:
        rrect(ctx, x, y, w, h, radius)
    else:
        ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.new_path()
    ctx.translate(x, y)
    ctx.scale(w / vw, w / vw)
    ctx.translate(-vx, -vy)
    draw_fn(ctx)
    ctx.restore()
    ctx.new_path()
    if border:
        if radius > 0:
            rrect(ctx, x, y, w, h, radius)
        else:
            ctx.rectangle(x, y, w, h)
        _s(ctx, border_col, LW + 2)


def split_screen(ctx, t, top_fn, bottom_fn, y=900, top_view=None, bottom_view=None,
                 badge=None):
    """Villain-top / AI-bottom split screen with the glowing divider at y.

    top_fn(ctx) / bottom_fn(ctx) draw full logical frames (backgrounds +
    characters) as usual. top_view / bottom_view = (vx, vy, vw) source
    regions (see panel); defaults show the frame unscaled and clipped:
    the top panel shows logical y 0..y, the bottom panel logical y..1920.
    Tip: to fit a whole character, e.g. top_view=(-90, 120, 1260) shrinks
    the top shot to 86%.
    """
    panel(ctx, 0, 0, W, y, top_fn, top_view, border=False)
    panel(ctx, 0, y, W, H - y, bottom_fn, bottom_view, border=False)
    split_divider(ctx, y, t, badge=badge)


# ===========================================================================
# EXTRA PROPS: cartoon_bomb, magnifier, puzzle_piece, folder
# ===========================================================================
def cartoon_bomb(ctx, x, y, s=1.0, t=0.0, lit=True):
    """Classic round black CARTOON bomb (the only kind allowed). (x, y) = centre
    of the ball; s=1 -> ball r=60. lit: animated fuse spark."""
    ctx.new_path()
    with saved(ctx, x, y, s) as c:
        c.move_to(30, -50)
        c.curve_to(44, -84, 70, -64, 76, -96)
        _s(c, INK, 12)
        c.move_to(30, -50)
        c.curve_to(44, -84, 70, -64, 76, -96)
        _s(c, "#c9a46a", 6)
        circle(c, 0, 0, 60)
        _fs(c, "#23202b", INK, LW)
        with saved(c, 22, -46, 1.0, 0.55):
            rrect(c, -16, -12, 32, 24, 4)
            _fs(c, "#5a5866", INK, 4)
        ellipse(c, -24, -22, 16, 10, -0.7)
        _f(c, "white", 0.5)
        if lit:
            f = 1 + 0.25 * math.sin(t * 40) + 0.15 * noise1(t * 20, 3)
            _star4(c, 78, -100, 22 * f, t * 6)
            _fs(c, "warn", INK, 3)
            _star4(c, 78, -100, 10 * f, -t * 6)
            _f(c, "#fff3c4")
            for j in range(3):
                ph = (t * 3 + j / 3) % 1.0
                a = j * 2.1 + 0.5
                circle(c, 78 + math.cos(a) * ph * 34, -100 + math.sin(a) * ph * 34, 4 * (1 - ph))
                _f(c, "warn")


def magnifier(ctx, x, y, s=1.0, rot=0.6, glass=0.25):
    """Magnifying glass for 'unmasking'. (x, y) = lens centre; s=1 -> lens r=70,
    handle ~120 px toward angle `rot` (radians, 0 = right, +0.6 = down-right).
    glass: tint opacity of the lens."""
    ctx.new_path()
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, 74, -14, 130, 28, 14)
        _fs(c, "frame", INK, LW)
        c.rectangle(64, -10, 22, 20)
        _fs(c, "steel", INK, 4)
        circle(c, 0, 0, 70)
        _fs(c, None, INK, 22)
        circle(c, 0, 0, 70)
        _src(c, "ai_eye", glass)
        c.fill()
        circle(c, 0, 0, 70)
        _s(c, "gold", 12)
        c.arc(0, 0, 50, math.pi * 1.1, math.pi * 1.45)
        _s(c, "white", 8, 0.7)


def _jig_edge(ctx, p, q, k, S):
    """Jigsaw edge from p to q; k=+1 knob outward (to the left of travel), -1 slot."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = uy, -ux

    def P(u, v):
        return (p[0] + ux * u * L + nx * v * S * k, p[1] + uy * u * L + ny * v * S * k)
    if k == 0:
        ctx.line_to(*q)
        return
    ctx.line_to(*P(0.39, 0))
    ctx.curve_to(*P(0.42, 0.08), *P(0.32, 0.11), *P(0.34, 0.19))
    ctx.curve_to(*P(0.37, 0.29), *P(0.63, 0.29), *P(0.66, 0.19))
    ctx.curve_to(*P(0.68, 0.11), *P(0.58, 0.08), *P(0.61, 0))
    ctx.line_to(*q)


def puzzle_piece(ctx, x, y, s=1.0, color="ai_accent", label=None, rot=0.0,
                 tabs=(1, 1, -1, -1), label_size=28):
    """Jigsaw piece (the AI 'assembling the pieces' of a sneaky plan).
    (x, y) = centre of the square body; s=1 -> 160 px body. tabs = (top,
    right, bottom, left): +1 knob out, -1 slot in, 0 flat. label: short text."""
    ctx.new_path()
    S = 160.0
    hs = S / 2
    with saved(ctx, x, y, s, rot) as c:
        for layer in ("shadow", "body"):
            c.save()
            if layer == "shadow":
                c.translate(6, 9)
            corners = [(-hs, -hs), (hs, -hs), (hs, hs), (-hs, hs)]
            c.move_to(*corners[0])
            for j in range(4):
                _jig_edge(c, corners[j], corners[(j + 1) % 4], tabs[j], S)
            c.close_path()
            c.restore()
            if layer == "shadow":
                _f(c, INK, 0.35)
            else:
                _fs(c, color, INK, LW)
        c.move_to(-hs + 16, -hs + 14)
        c.line_to(hs * 0.2, -hs + 14)
        _s(c, "white", 6, 0.35)
        if label:
            xl = -hs + (0.29 * S + 6 if tabs[3] < 0 else 10)
            xr = hs - (0.29 * S + 6 if tabs[1] < 0 else 10)
            fsz = label_size
            ls = wrap_lines(c, label, xr - xl, "ui", fsz)
            while fsz > 16 and max(text_width(c, l, "ui", fsz) for l in ls) > xr - xl:
                fsz -= 2
                ls = wrap_lines(c, label, xr - xl, "ui", fsz)
            for i, l in enumerate(ls):
                _text(c, l, (xl + xr) / 2,
                      (i - (len(ls) - 1) / 2) * fsz * 1.15 + fsz * 0.35, fsz,
                      _txt_on(color), "ui")


def folder(ctx, x, y, s=1.0, label="", color="#e8c76a", stamp_txt=None, stamp_color="danger",
           rot=0.0):
    """Manila case-file folder (the AI's archive of past tricks).
    (x, y) = centre; s=1 -> 300 x 220 px. label = tab text (short).
    stamp_txt: a small static stamp on the cover (e.g. "TRIED", "NOPE")."""
    ctx.new_path()
    fw, fh = 300.0, 220.0
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -fw / 2 + 7, -fh / 2 + 9, fw, fh, 10)
        _f(c, INK, 0.35)
        # back + tab
        poly(c, [(-fw / 2, -fh / 2 + 10), (-fw / 2 + 10, -fh / 2 - 34), (-fw / 2 + 150, -fh / 2 - 34),
                 (-fw / 2 + 168, -fh / 2 + 4), (fw / 2, -fh / 2 + 4), (fw / 2, fh / 2),
                 (-fw / 2, fh / 2)])
        _fs(c, _mix(color, "#000000", 0.18), INK, LW)
        if label:
            fsz = 26
            while fsz > 14 and text_width(c, label, "ui", fsz) > 128:
                fsz -= 1
            _text(c, label, -fw / 2 + 82, -fh / 2 - 12 + fsz * 0.36, fsz, "ink", "ui")
        # paper peeking
        c.rectangle(-fw / 2 + 16, -fh / 2 + 10, fw - 40, 40)
        _fs(c, "paper", INK, 3)
        # front
        rrect(c, -fw / 2, -fh / 2 + 26, fw, fh - 26, 8)
        _fs(c, color, INK, LW)
        c.move_to(-fw / 2 + 18, -fh / 2 + 42)
        c.line_to(fw / 2 - 18, -fh / 2 + 42)
        _s(c, "white", 4, 0.4)
        if stamp_txt:
            with saved(c, 10, 30, 1.0, -0.14):
                fs = 44
                set_font(c, "black", fs)
                tw = c.text_extents(stamp_txt)[4]
                rrect(c, -tw / 2 - 16, -fs * 0.7, tw + 32, fs * 1.4, 8)
                _s(c, stamp_color, 6, 0.9)
                _text(c, stamp_txt, 0, fs * 0.36, fs, C(stamp_color, 0.9), "black")
