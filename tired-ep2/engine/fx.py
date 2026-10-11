"""engine/fx.py -- effects, comedy marks, story overlays, UI screens, titles.

Rules every function here follows (see API_fx.md for the full reference):

* Pure functions of time. Anything with a start time (t0 / t_in / t_on) draws
  NOTHING before it and NOTHING after it ends. Continuous effects
  (motion_lines, dizzy_stars, heat_squiggles, music_notes, power_aura,
  alarm_wash, time_slow, vignette) are driven by an amount/intensity and draw
  nothing at 0.
* Logical 1080x1920 user space. Local effects (marks, emotes, auras...) also
  work inside a core.camera() block (pass world coordinates). Full-frame
  effects (flash, whip_pan, alarm_wash, vignette, eyelid_wipe, time_slow,
  end_card, black) and name tags belong in SCREEN space (after the camera).
* `s` is a size factor: the documented sizes are at s=1.
* Bitrate: flat shapes, <= ~20 small moving pieces per effect, no noise, no
  strobing (pulses >= 0.6 s period), full-frame flashes <= 3 frames.
* Static parts are rasterised once into fx's own layer cache (same 1/8-octave
  scale quantisation as core.cached, but a separate LRU so fx never evicts
  set/background layers, and blits can carry an alpha).
"""
import math
from collections import OrderedDict

import cairocffi as cairo

from .core import (W, H, FPS, PAL, hexc, mixc, clamp, lerp, seg, smoothstep,
                   ease_in, ease_out, ease_in_out, ease_out_back, ease_out_bounce, hash01,
                   fill, stroke, rrect, ellipse, circle, poly, smooth_path,
                   text, set_font, saved, radial_glow)

INK = PAL["ink"]
TAU = 2 * math.pi

# Character / tag colours (slab fills). Keys or aliases are accepted wherever
# a `color` for a name tag is asked for; any '#rrggbb' or PAL key works too.
TAG_COLORS = {
    "tired": "#8fa3f2",   # sleepy periwinkle
    "embar": "#ff8ab4",   # blush pink
    "imp": "#f7b33a",     # impulsivity gold
    "boss": "#5fdcc2",    # cold mint / teal (NOT the special power teal)
}
_TAG_ALIAS = {"tiredness": "tired", "periwinkle": "tired",
              "embarrassment": "embar", "pink": "embar",
              "impulsivity": "imp", "gold": "imp",
              "the boss": "boss", "mint": "boss", "teal": "boss"}

# misc effect colours
STAR_YELLOW = "#ffe066"
SWEAT_BLUE = "#9fdcff"
HEAT_RED = "#ff5f7e"
DUST = "#efe6d8"
HOLO = "#9feeff"        # hologram cyan (bluer than the power teal)
LINK_BLUE = "#2a5bd7"


# ----------------------------------------------------------------------------
# small utils
# ----------------------------------------------------------------------------
def _frac(x):
    return x - math.floor(x)


def _rgba(ctx, c, a=1.0):
    r, g, b, aa = hexc(c)
    ctx.set_source_rgba(r, g, b, aa * a)


def _fill(ctx, c, a=1.0, preserve=False):
    _rgba(ctx, c, a)
    ctx.fill_preserve() if preserve else ctx.fill()


def _stroke(ctx, c, w, a=1.0, preserve=False, cap=cairo.LINE_CAP_ROUND,
            join=cairo.LINE_JOIN_ROUND):
    _rgba(ctx, c, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(join)
    ctx.stroke_preserve() if preserve else ctx.stroke()


def _lighten(c, k):
    return mixc(c, "#ffffff", k)


def _darken(c, k):
    return mixc(c, INK, k)


_EXT = {}


def _ext(ctx, s, font, size):
    """Cached text_extents (x_bearing, y_bearing, w, h, x_adv, y_adv)."""
    k = (s, font, round(size, 2))
    e = _EXT.get(k)
    if e is None:
        set_font(ctx, font, size)
        e = ctx.text_extents(s)
        _EXT[k] = e
    return e


def _tw(ctx, s, font, size):
    return _ext(ctx, s, font, size)[4]


def _tracked(ctx, s, x, y, size, color, font="ui", tracking=0.0, align="left",
             outline=None, outline_w=6):
    """Text with letter spacing (tracking in px). y is the baseline."""
    advs = [_tw(ctx, ch, font, size) for ch in s]
    total = sum(advs) + tracking * (len(s) - 1)
    xx = x - {"left": 0, "center": total / 2, "right": total}[align]
    set_font(ctx, font, size)
    for ch, a in zip(s, advs):
        ctx.move_to(xx, y)
        ctx.text_path(ch)
        xx += a + tracking
    if outline:
        _stroke(ctx, outline, outline_w, preserve=True)
    _fill(ctx, color)
    return total


def _fit_size(ctx, s, font, size, max_w, min_size=10):
    w = _tw(ctx, s, font, size)
    if w <= max_w:
        return size
    return max(min_size, size * max_w / w * 0.99)


# ----------------------------------------------------------------------------
# fx layer cache (static parts rasterised once, blitted with optional alpha)
# ----------------------------------------------------------------------------
_FXL = OrderedDict()
_FXL_MAX = 96


def _qscale(ctx, mul=1.0):
    m = ctx.get_matrix()
    sc = math.hypot(m.xx, m.yx) * mul
    if sc <= 1e-6:
        return 0.0
    return 2 ** (math.ceil(math.log2(sc) * 8 - 1e-6) / 8)


def _layer(ctx, key, x0, y0, w, h, draw_fn, a=1.0, pad=4, q=None, exact=False):
    """Blit draw_fn(c) (drawn in current user coords inside x0,y0,w,h) from a
    cached bitmap. `q` overrides the raster scale (use it when the CTM is
    animating, e.g. a pop-in, so the bitmap is not re-rendered per frame).
    exact=True rasterises at the exact device scale (for screen-space
    layers with a fixed CTM) so the blit is a plain pixel copy."""
    if a <= 0.003:
        return
    m = ctx.get_matrix()
    if q is None:
        if exact and abs(m.yx) < 1e-9 and abs(m.xy) < 1e-9 and abs(m.xx - m.yy) < 1e-9:
            q = m.xx
        else:
            q = _qscale(ctx)
    if q <= 0:
        return
    k = (key, round(q, 4), round(x0, 2), round(y0, 2), round(w, 2), round(h, 2))
    surf = _FXL.get(k)
    if surf is None:
        sw = int(math.ceil((w + 2 * pad) * q))
        sh = int(math.ceil((h + 2 * pad) * q))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, sw), max(1, sh))
        c = cairo.Context(surf)
        c.scale(q, q)
        c.translate(-(x0 - pad), -(y0 - pad))
        draw_fn(c)
        surf.flush()
        _FXL[k] = surf
        while len(_FXL) > _FXL_MAX:
            _FXL.popitem(last=False)
    else:
        _FXL.move_to_end(k)
    ctx.save()
    ctx.translate(x0 - pad, y0 - pad)
    ctx.scale(1 / q, 1 / q)
    ctx.set_source_surface(surf, 0, 0)
    dm = ctx.get_matrix()
    if abs(dm.xx - 1) < 1e-6 and abs(dm.yy - 1) < 1e-6 and abs(dm.xy) < 1e-9 \
            and abs(dm.yx) < 1e-9:
        # pixel-aligned copy when possible (fast path)
        ox, oy = round(dm.x0), round(dm.y0)
        if abs(dm.x0 - ox) < 1e-3 and abs(dm.y0 - oy) < 1e-3:
            ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        else:
            ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    else:
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.rectangle(0, 0, surf.get_width(), surf.get_height())
    if a >= 0.997:
        ctx.fill()
    else:
        ctx.clip()
        ctx.paint_with_alpha(a)
    ctx.restore()


def clear_cache():
    """Drop fx's cached layers (e.g. between scenes in one process)."""
    _FXL.clear()


# ----------------------------------------------------------------------------
# shape helpers
# ----------------------------------------------------------------------------
def _star_path(ctx, cx, cy, r_out, r_in, n=5, rot=-math.pi / 2, radii=None):
    pts = []
    for i in range(2 * n):
        a = rot + math.pi * i / n
        r = (radii[i // 2] if radii else r_out) if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly(ctx, pts)


def _twinkle_path(ctx, cx, cy, r, inner=0.2, rot=0.0):
    """4-point twinkle (concave diamond)."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ri = r * inner
    ctx.move_to(0, -r)
    ctx.curve_to(ri * 0.4, -ri, ri, -ri * 0.4, r, 0)
    ctx.curve_to(ri, ri * 0.4, ri * 0.4, ri, 0, r)
    ctx.curve_to(-ri * 0.4, ri, -ri, ri * 0.4, -r, 0)
    ctx.curve_to(-ri, -ri * 0.4, -ri * 0.4, -ri, 0, -r)
    ctx.close_path()
    ctx.restore()


def _heart_path(ctx, cx, cy, r):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(r, r)
    ctx.move_to(0, 0.95)
    ctx.curve_to(-0.35, 0.68, -1.05, 0.25, -1.0, -0.3)
    ctx.curve_to(-0.95, -0.88, -0.25, -1.02, 0, -0.52)
    ctx.curve_to(0.25, -1.02, 0.95, -0.88, 1.0, -0.3)
    ctx.curve_to(1.05, 0.25, 0.35, 0.68, 0, 0.95)
    ctx.close_path()
    ctx.restore()


def _drop_path(ctx, cx, cy, r, ang=-math.pi / 2, tail=2.0):
    """Teardrop: round part centred at (cx,cy), tip pointing along `ang`."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang + math.pi / 2)        # local -y == tip direction
    ctx.move_to(0, -tail * r)
    ctx.curve_to(0.5 * r, -1.15 * r, r, -0.6 * r, r, 0)
    ctx.arc(0, 0, r, 0, math.pi)
    ctx.curve_to(-r, -0.6 * r, -0.5 * r, -1.15 * r, 0, -tail * r)
    ctx.close_path()
    ctx.restore()


def _drop(ctx, cx, cy, r, ang=-math.pi / 2, color=SWEAT_BLUE, a=1.0, ow=None):
    _drop_path(ctx, cx, cy, r, ang)
    _fill(ctx, color, a, preserve=True)
    _stroke(ctx, INK, ow if ow is not None else max(1.5, r * 0.22), a)
    # highlight
    hx = cx + r * 0.38 * math.cos(ang + 2.4)
    hy = cy + r * 0.38 * math.sin(ang + 2.4)
    ellipse(ctx, hx, hy, r * 0.22, r * 0.32, ang)
    _fill(ctx, "#ffffff", 0.9 * a)


def _z_path(ctx, x, y, sz, rot=0.0):
    """Thick 'Z' letter shape centred at (x, y), sz = height."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(sz, sz)
    pts = [(-0.45, -0.5), (0.45, -0.5), (0.45, -0.3), (-0.08, 0.28), (0.47, 0.28),
           (0.47, 0.5), (-0.47, 0.5), (-0.47, 0.3), (0.06, -0.28), (-0.45, -0.28)]
    poly(ctx, pts)
    ctx.restore()


def _check_path(ctx, x, y, sz, prog=1.0):
    """Check mark polyline in a sz x sz box at (x,y); prog draws it on."""
    pts = [(x + 0.08 * sz, y + 0.52 * sz), (x + 0.38 * sz, y + 0.82 * sz),
           (x + 0.94 * sz, y + 0.12 * sz)]
    l1 = math.dist(pts[0], pts[1])
    l2 = math.dist(pts[1], pts[2])
    d = (l1 + l2) * clamp(prog)
    if d <= 0.01:
        return False
    ctx.move_to(*pts[0])
    if d <= l1:
        k = d / l1
        ctx.line_to(lerp(pts[0][0], pts[1][0], k), lerp(pts[0][1], pts[1][1], k))
    else:
        ctx.line_to(*pts[1])
        k = (d - l1) / l2
        ctx.line_to(lerp(pts[1][0], pts[2][0], k), lerp(pts[1][1], pts[2][1], k))
    return True


def _taper(ctx, x0, y0, x1, y1, w0, w1):
    """Tapered band from (x0,y0) width w0 to (x1,y1) width w1 (round ends)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-3:
        circle(ctx, x0, y0, max(w0, w1) / 2)
        return
    nx, ny = -dy / L, dx / L
    a = math.atan2(dy, dx)
    ctx.new_sub_path()
    ctx.arc(x1, y1, w1 / 2, a - math.pi / 2, a + math.pi / 2)
    ctx.arc(x0, y0, w0 / 2, a + math.pi / 2, a + 3 * math.pi / 2)
    ctx.close_path()


def _note_shape(ctx, kind, fc, a, sz):
    """Music note drawn at the origin (unit = sz px). kind 0 = eighth, 1 = pair.
    Outline is made by a fat ink pass underneath the colour pass."""
    ctx.save()
    ctx.scale(sz, sz)
    if kind == 0:
        heads = [(0.0, 0.0)]
        stems = [((0.86, -0.22), (0.86, -3.1))]
        beam = None
        flag = ((0.86, -3.1), (1.95, -2.4), (1.85, -1.5))
    else:
        heads = [(0.0, 0.0), (2.5, -0.45)]
        stems = [((0.86, -0.22), (0.86, -3.1)), ((3.36, -0.67), (3.36, -3.55))]
        beam = ((0.86, -3.1), (3.36, -3.55))
        flag = None
    for p, col, grow in ((0, INK, 0.38), (1, fc, 0.0)):
        _rgba(ctx, col, a)
        for hx, hy in heads:
            ellipse(ctx, hx, hy, 1.0 + grow, 0.74 + grow, -0.38)
            ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for (sx0, sy0), (sx1, sy1) in stems:
            ctx.move_to(sx0, sy0)
            ctx.line_to(sx1, sy1)
        ctx.set_line_width(0.36 + 2 * grow)
        ctx.stroke()
        if beam:
            ctx.move_to(*beam[0])
            ctx.line_to(*beam[1])
            ctx.set_line_width(0.75 + 2 * grow)
            ctx.stroke()
        if flag:
            ctx.move_to(*flag[0])
            ctx.curve_to(flag[0][0] + 0.2, flag[0][1] + 0.5, flag[1][0], flag[1][1],
                         flag[2][0], flag[2][1])
            ctx.set_line_width(0.42 + 2 * grow)
            ctx.stroke()
    ctx.restore()


# ----------------------------------------------------------------------------
# 1. Name tags
# ----------------------------------------------------------------------------
TAG_IN = 0.5    # seconds the pop-in takes
TAG_OUT = 0.32  # seconds the slide-out takes (starts at t_out)
_GEOM = {}


def _tag_color(color):
    k = str(color).lower()
    k = _TAG_ALIAS.get(k, k)
    return TAG_COLORS.get(k, color)


def _tag_geom(ctx, title, subtitle, s, max_w):
    key = (title, subtitle, round(s, 3), round(max_w, 1))
    g = _GEOM.get(key)
    if g is not None:
        return g
    k = 0.2                        # skew (forward lean)
    ts = 104 * s
    for _ in range(4):
        e = _ext(ctx, title, "title", ts)
        tw, cap = e[2], -e[1]
        pad_x, pad_y = 34 * s, 22 * s
        sh = cap + 2 * pad_y
        sw = tw + 2 * pad_x
        tot = k * sh + sw + 10 * s
        if tot <= max_w or ts < 30:
            break
        ts *= max_w / tot * 0.99
    ss = 46 * s
    if subtitle:
        while _tw(ctx, subtitle, "ui", ss) + 44 * s + 60 * s > max_w and ss > 16:
            ss *= 0.94
        sub_w = _tw(ctx, subtitle, "ui", ss)
    else:
        sub_w = 0
    st_h = ss * 1.55
    st_w = sub_w + 44 * s
    g = dict(k=k, ts=ts, e=e, tw=tw, cap=cap, pad_x=pad_x, pad_y=pad_y, sh=sh, sw=sw,
             ss=ss, st_h=st_h, st_w=st_w, sub_w=sub_w, s=s)
    # title placement (sheared text centred on the slab)
    g["bx"] = k * sh / 2 + sw / 2 - e[0] - tw / 2 - k * cap / 2
    g["by"] = pad_y + cap
    _GEOM[key] = g
    return g


def _slab_pts(x, y, w, h, k):
    return [(x + k * h, y), (x + k * h + w, y), (x + w, y + h), (x, y + h)]


def name_tag(ctx, title, subtitle, t, t_in, t_out, x=90, y=170, color="tired",
             align="left", s=1.0, max_w=None):
    """Character intro tag. (x, y) = top-left (align left), top-right (right)
    or top-centre (center) of the tag. Visible t_in .. t_out + TAG_OUT."""
    if t < t_in or t > t_out + TAG_OUT:
        return
    if max_w is None:
        max_w = {"left": 930 - x, "right": x - 60,
                 "center": 2 * min(x - 60, 930 - x)}[align]
    max_w = max(200.0, max_w)
    g = _tag_geom(ctx, title, subtitle, s, max_w)
    col = _tag_color(color)
    k, sh, sw, st_h, st_w = g["k"], g["sh"], g["sw"], g["st_h"], g["st_w"]
    slab_w = k * sh + sw
    # subtitle strip position (tag-local, slab top-left = 0,0)
    sy = sh - 9 * s
    if align == "left":
        sx = 46 * s
    elif align == "right":
        sx = max(0.0, slab_w - 46 * s - (k * st_h + st_w))
    else:
        sx = slab_w / 2 - (k * st_h + st_w) / 2 + 24 * s
    tot_w = max(slab_w, sx + k * st_h + st_w)
    ox = {"left": 0.0, "right": -tot_w, "center": -tot_w / 2}[align]
    dt = t - t_in
    q = _qscale(ctx, 1.15)
    # idle wobble + out motion
    rot = -0.035 + 0.007 * math.sin(TAU * dt / 2.3)
    bob = 2.5 * s * math.sin(TAU * dt / 1.9)
    po = seg(t, t_out, t_out + TAG_OUT)
    ps = seg(t, t_out - 0.06, t_out + TAG_OUT - 0.08)
    if align == "left":
        dist = -(x + tot_w + 80)
    elif align == "right":
        dist = (W - x) + tot_w + 80
    else:
        dist = 0.0
    slide = dist * ease_in(po)
    sub_slide = dist * ease_in(ps)
    shrink = 1.0 - ease_in(po) if align == "center" else 1.0

    ctx.save()
    ctx.translate(x + slide, y + bob)
    ctx.rotate(rot)
    if shrink < 1.0:
        if shrink <= 0.01:
            ctx.restore()
            return
        ctx.translate(0, sh / 2)
        ctx.scale(shrink, shrink)
        ctx.translate(0, -sh / 2)
    ctx.translate(ox, 0)

    # --- subtitle strip (behind the slab) ---
    if g["sub_w"] > 0:
        rv = ease_out(seg(dt, 0.26, 0.52))
        if rv > 0.01:
            def draw_sub(c):
                poly(c, [(p[0] + 6 * s, p[1] + 7 * s) for p in _slab_pts(sx, sy, st_w, st_h, k)])
                _fill(c, INK, 0.35)
                poly(c, _slab_pts(sx, sy, st_w, st_h, k))
                _fill(c, INK)
                c.save()
                c.translate(sx + 22 * s + k * st_h * 0.5, sy + st_h / 2 + g["ss"] * 0.36)
                c.transform(cairo.Matrix(1, 0, -k * 0.6, 1, 0, 0))
                text(c, subtitle, 0, 0, g["ss"], _lighten(col, 0.6), "ui", "left")
                c.restore()
            ctx.save()
            ctx.translate(sub_slide - slide, 0)
            # reveal from the anchor side
            full = k * st_h + st_w + 12 * s
            if align == "right":
                ctx.rectangle(sx + full * (1 - rv) - 2, sy - 4, full * rv + 16 * s, st_h + 20 * s)
            else:
                ctx.rectangle(sx - 4, sy - 4, full * rv + 4, st_h + 20 * s)
            ctx.clip()
            _layer(ctx, ("tag_sub", subtitle, round(s, 3), col, round(st_w, 1)),
                   sx - 2, sy - 2, k * st_h + st_w + 12 * s, st_h + 12 * s, draw_sub, q=q)
            ctx.restore()

    # --- slab ---
    kx = ease_out_back(seg(dt, 0.0, 0.30), 2.2)
    if kx > 0.01:
        ky = 0.7 + 0.3 * ease_out(seg(dt, 0.0, 0.2))

        def draw_slab(c):
            pts = _slab_pts(0, 0, sw, sh, k)
            poly(c, [(p[0] + 9 * s, p[1] + 10 * s) for p in pts])
            _fill(c, INK)
            poly(c, pts)
            c.save()
            _fill(c, col, preserve=True)
            c.clip()
            c.rectangle(-10, sh * 0.70, slab_w + 20, sh)
            _fill(c, _darken(col, 0.2))
            c.rectangle(-10, sh * 0.08, slab_w + 20, 5 * s)
            _fill(c, _lighten(col, 0.45), 0.8)
            c.restore()
            poly(c, pts)
            _stroke(c, INK, 6.5 * s)
        ax = 0.0 if align == "left" else slab_w if align == "right" else slab_w / 2
        ctx.save()
        ctx.translate(ax, sh)
        ctx.scale(kx, ky)
        ctx.translate(-ax, -sh)
        _layer(ctx, ("tag_slab", round(sw, 1), round(sh, 1), col, round(s, 3)),
               -4, -4, slab_w + 20 * s, sh + 20 * s, draw_slab, q=q)
        ctx.restore()

    # --- title ---
    kt = ease_out_back(seg(dt, 0.10, 0.40), 2.0)
    if kt > 0.01:
        e, bx, by, ts = g["e"], g["bx"], g["by"], g["ts"]

        def draw_title(c):
            c.save()
            c.translate(bx, by)
            c.transform(cairo.Matrix(1, 0, -k, 1, 0, 0))
            set_font(c, "title", ts)
            c.move_to(4 * s, 6 * s)
            c.text_path(title)
            _stroke(c, INK, 11 * s, preserve=True)
            _fill(c, INK)
            c.move_to(0, 0)
            c.text_path(title)
            _stroke(c, INK, 11 * s, preserve=True)
            _fill(c, "#ffffff")
            c.restore()
        cx, cy = bx + e[0] + g["tw"] / 2 + k * g["cap"] / 2, by - g["cap"] / 2
        rt = (1 - kt) * 0.25
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(rt)
        ctx.scale(kt, kt)
        ctx.translate(-cx, -cy)
        x0 = bx + e[0] - 12 * s
        _layer(ctx, ("tag_title", title, round(ts, 2)), x0, by + e[1] - 12 * s,
               g["tw"] + k * g["cap"] + 30 * s, g["cap"] + 32 * s, draw_title, q=q)
        ctx.restore()
    ctx.restore()


# ----------------------------------------------------------------------------
# 2. Motion, impact and comedy marks
# ----------------------------------------------------------------------------
def motion_lines(ctx, x, y, angle, length, t, intensity=1.0, color="ink", n=None,
                 spread=None, width=12, seed=0):
    """Speed lines BEHIND a mover at (x, y) moving in direction `angle`
    (radians, 0 = moving right). Lines stream back over `length` px from
    the mover's back edge; `spread` = band height (default 0.6*length)."""
    if intensity <= 0.01 or length <= 1:
        return
    intensity = clamp(intensity)
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    n = n if n is not None else int(round(3 + 3 * intensity))
    n = max(1, min(n, 9))
    spread = spread if spread is not None else length * 0.6
    for i in range(n):
        h1, h2, h3 = hash01(i, seed + 11), hash01(i, seed + 23), hash01(i, seed + 37)
        off = ((i + 0.5) / n - 0.5) * spread + (h1 - 0.5) * spread / n * 0.5
        ph = _frac(t * (2.2 + h2 * 1.0) + h3)
        # each line shoots out from the mover, stretches, then detaches & fades
        st = length * (0.04 + 0.1 * h1) + length * 0.45 * ease_in(ph)
        L = length * (0.5 + 0.45 * h2) * (0.55 + 0.45 * math.sin(math.pi * min(1.0, ph * 1.4)))
        a = intensity * (1 - smoothstep(seg(ph, 0.55, 1.0)))
        if a < 0.03:
            continue
        x0 = x - dx * st + nx * off
        y0 = y - dy * st + ny * off
        x1 = x0 - dx * L
        y1 = y0 - dy * L
        w0 = width * (0.75 + 0.5 * h3) * (0.6 + 0.4 * intensity)
        _taper(ctx, x0, y0, x1, y1, w0, w0 * 0.2)
        _fill(ctx, color, a * 0.92)


def smear(ctx, x0, y0, x1, y1, t, t0, dur=0.38, color="#f4f6f8", width=120, seed=0):
    """Teleport zip: a tapered three-strand smear from (x0,y0) (where the
    character was) to (x1,y1) (where it is now). Head arrives in the first
    15%, the tail retracts to the head by t0+dur."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    hk = ease_out(seg(p, 0.0, 0.15))
    tk = ease_in_out(seg(p, 0.12, 1.0))
    a = 1.0 - smoothstep(seg(p, 0.7, 1.0))
    hx, hy = lerp(x0, x1, hk), lerp(y0, y1, hk)
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    # three strands (outline pass then colour pass for a clean union)
    strands = [(-0.32, 1.0, 0.42), (0.0, 0.8, 0.55), (0.32, 0.62, 0.40)]
    for pas in (0, 1):
        for off, reach, wk in strands:
            tail_k = lerp(tk, 1.0, 1 - reach) if reach < 1 else tk
            tx, ty = lerp(x0, x1, min(tail_k, hk)), lerp(y0, y1, min(tail_k, hk))
            o = off * width
            w0 = width * wk
            ww = w0 + (11 if pas == 0 else 0)
            _taper(ctx, hx + nx * o * 0.6, hy + ny * o * 0.6, tx + nx * o, ty + ny * o,
                   ww, max(2.0, ww * 0.18))
            _fill(ctx, INK if pas == 0 else color, a)
    # speed ticks along the trail
    for i in range(4):
        h = hash01(i, seed + 5)
        o = (h - 0.5) * width * 1.6
        u = lerp(tk, 1.0, 0.2 + 0.6 * hash01(i, seed + 9))
        cx, cy = lerp(x0, x1, u), lerp(y0, y1, u)
        ll = width * (0.5 + 0.6 * h)
        _taper(ctx, cx + nx * o, cy + ny * o, cx + nx * o - ux * ll, cy + ny * o - uy * ll, 7, 2)
        _fill(ctx, INK, a * 0.8)
    # poof at the origin (solid cloud, union outline)
    pk = seg(p, 0.0, 0.5)
    if 0 < pk < 1:
        r = width * (0.24 + 0.1 * ease_out(pk)) * (1 - pk ** 1.5)
        if r > 1:
            d = width * 0.28 * ease_out(pk)
            pts = [(x0 + math.cos(TAU * i / 5 + 0.6) * d, y0 + math.sin(TAU * i / 5 + 0.6) * d * 0.8)
                   for i in range(5)]
            _cloud(ctx, pts, r, color, 4.5)


def _cloud(ctx, centres, r, color, ow, a=1.0, rs=None):
    """Puffy cloud made of circles with ONE outer ink outline (outline pass,
    then fill pass)."""
    rs = rs or [r] * len(centres)
    for (cx, cy), rr in zip(centres, rs):
        circle(ctx, cx, cy, rr + ow / 2)
    _fill(ctx, INK, a)
    for (cx, cy), rr in zip(centres, rs):
        circle(ctx, cx, cy, max(0.5, rr - ow / 2))
    _fill(ctx, color, a)


WHIP_COLORS = ("#f3efe8", "#cfd7e6", "#a3afc8", "#ffffff", "#e6dccb")


def whip_pan(ctx, t, t0, dur=0.32, direction=1, colors=WHIP_COLORS, seed=0):
    """Bold horizontal streak bands for a whip-pan cut. Covers the frame most
    at t0 + dur/2 (cut there). direction +1 = streaks travel right->left
    (camera pans right), -1 the other way. Pass `colors` sampled from the
    two scenes to blend it in."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    env = math.sin(math.pi * p) ** 0.7
    # soften the image underneath (cheap stand-in for blur)
    _rgba(ctx, colors[0], 0.6 * env)
    ctx.paint()
    n = 12
    for j in range(n):
        h1, h2, h3 = hash01(j, seed + 1), hash01(j, seed + 2), hash01(j, seed + 3)
        yc = (j + 0.5) / n * H + (h1 - 0.5) * H / n * 0.8
        th = (0.6 + 0.8 * h2) * H / n * (0.35 + 0.95 * env)
        ln = (1.1 + 0.8 * h3) * W
        travel = 2.2 * W
        xc = W / 2 + (0.5 - p) * travel * (0.8 + 0.4 * h1) + (h2 - 0.5) * W * 0.3
        if direction < 0:
            xc = W - xc
        _taper(ctx, xc - ln / 2, yc, xc + ln / 2, yc, th * 0.3, th)
        _fill(ctx, colors[j % len(colors)], (0.7 + 0.3 * h3) * env)


def whip_pan_offset(t, t0, dur=0.32, dist=1500, direction=1):
    """Camera helper for whip_pan: returns (dx, incoming). Before t0+dur/2
    draw the OUTGOING scene shifted by dx; after, the INCOMING scene shifted
    by dx (incoming=True). dx eases in, then eases out to 0."""
    mid = t0 + dur / 2
    if t < mid:
        return (-direction * dist * ease_in(seg(t, t0, mid)), False)
    return (direction * dist * (1 - ease_out(seg(t, mid, t0 + dur))), True)


def impact_star(ctx, x, y, s, t, t0, dur=0.45, color=STAR_YELLOW, inner="#ffffff",
                word=None, word_color="danger", seed=0, spikes=11):
    """Comic burst (r ~110 px at s=1) popping at t0, gone by t0+dur.
    Optional `word` ("BONK!") in comic lettering."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    k = ease_out_back(seg(p, 0.0, 0.22), 2.0) * (1 - ease_in(seg(p, 0.65, 1.0)))
    if k < 0.02:
        return
    rot = 0.15 * p + hash01(seed, 77) * 0.6
    radii = [110 * s * (0.72 + 0.5 * hash01(i, seed + 3)) * k for i in range(spikes)]
    _star_path(ctx, x, y, 0, 52 * s * k, spikes, rot, radii)
    _fill(ctx, color, preserve=True)
    _stroke(ctx, INK, 7 * s)
    _star_path(ctx, x, y, 0, 30 * s * k, spikes, rot + 0.12, [r * 0.55 for r in radii])
    _fill(ctx, inner)
    # flying impact lines
    lk = seg(p, 0.08, 0.6)
    if 0 < lk < 1:
        for i in range(6):
            a = rot + TAU * (i + 0.5) / 6
            r0 = 120 * s + 70 * s * ease_out(lk)
            r1 = r0 + 40 * s * (1 - lk)
            _taper(ctx, x + math.cos(a) * r0, y + math.sin(a) * r0,
                   x + math.cos(a) * r1, y + math.sin(a) * r1, 10 * s, 4 * s)
            _fill(ctx, INK, 1 - lk)
    if word:
        sz = 62 * s * k
        with saved(ctx, x, y + sz * 0.35, 1.0, -0.12):
            text(ctx, word, 0, 0, sz, word_color, "comic", "center", outline=INK,
                 outline_w=8 * s, shadow=(3 * s, 4 * s, INK))


def dust_puff(ctx, x, y, s, t, t0, seed=0, dur=0.8, color=DUST, spread=1.0):
    """Cartoon dust clouds kicked out sideways along the ground from (x, y)
    (ground contact point): two puffy clouds (one outline each) rolling
    out ~120 px each way at s=1, plus 4 flecks."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    tau = p * dur
    for i in range(4):
        h = hash01(i, seed + 9)
        side = -1 if i % 2 else 1
        vx = side * (160 + 140 * h) * s
        vy = -(300 + 200 * hash01(i, seed + 4)) * s
        fx = x + vx * tau
        fy = y + vy * tau + 0.5 * 2200 * s * tau * tau
        if fy > y:
            continue
        circle(ctx, fx, fy, (6 + 3 * h) * s)
        _fill(ctx, _darken(color, 0.08), preserve=True)
        _stroke(ctx, INK, 2.5 * s)
    grow = ease_out(seg(p, 0, 0.45))
    shrink = 1 - ease_in(seg(p, 0.45, 1.0))
    for side in (-1, 1):
        d = (40 + 90 * ease_out(p)) * s * spread
        cx0 = x + side * d
        cs, rs = [], []
        for i in range(4):
            h = hash01(i + (side > 0) * 10, seed + 1)
            u = i / 3.0
            cs.append((cx0 - side * u * 70 * s * (0.6 + 0.4 * grow),
                       y - (12 + 26 * math.sin(math.pi * (0.2 + 0.6 * u))) * s * (0.5 + 0.5 * grow)
                       - 14 * s * p))
            rs.append((16 + 16 * h + 10 * (1 - u)) * s * (0.45 + 0.55 * grow) * shrink)
        if max(rs) < 1.5:
            continue
        _cloud(ctx, cs, 0, color, 4.5 * s, rs=rs)


def plaster_dust(ctx, x, y, s, t, t0, seed=0, dur=1.4, width=220, n=10, fall=520,
                 color="#f2ede3"):
    """Ceiling hit at (x, y) (the ceiling line): a flat dust cloud bulging
    down and spreading `width` px, plus <=12 plaster flecks tumbling down
    `fall` px. Flecks 12-28 px at s=1."""
    if t < t0 or t > t0 + dur:
        return
    n = min(n, 12)
    tau = t - t0
    # cloud
    ck = seg(tau, 0, 0.8)
    if ck < 1:
        grow = ease_out(seg(ck, 0, 0.5))
        shrink = 1 - ease_in(seg(ck, 0.35, 1.0))
        cs, rs = [], []
        for i in range(5):
            side = (i - 2) / 2.0
            cs.append((x + side * width * 0.42 * s * (0.45 + 0.55 * grow),
                       y + (10 + 22 * (1 - abs(side))) * s * (0.5 + 0.5 * grow)))
            rs.append((34 + 12 * hash01(i, seed + 3)) * s * (1.15 - 0.4 * abs(side))
                      * (0.4 + 0.6 * grow) * shrink)
        if max(rs) > 1.5:
            _cloud(ctx, cs, 0, color, 4 * s, rs=rs)
    # flecks
    g = 2 * fall * s / (dur * 0.85) ** 2
    for i in range(n):
        h1, h2, h3 = hash01(i, seed + 11), hash01(i, seed + 12), hash01(i, seed + 13)
        d0 = h1 * 0.3
        tt = tau - d0
        if tt < 0:
            continue
        fx = x + (h2 - 0.5) * width * s + math.sin(tt * (3 + 3 * h3) + i) * 12 * s
        fy = y + 14 * s + 0.5 * g * tt * tt * (0.75 + 0.35 * h3)
        sz = (6 + 8 * h3) * s
        a = 1 - smoothstep(seg(tt, dur * 0.7 - d0, dur - d0))
        if a <= 0.02:
            continue
        rot = tt * (4 + 6 * h1) * (1 if i % 2 else -1)
        ctx.save()
        ctx.translate(fx, fy)
        ctx.rotate(rot)
        poly(ctx, [(-sz, -sz * 0.6), (sz * 0.8, -sz * 0.8), (sz, sz * 0.5), (-sz * 0.5, sz * 0.8)])
        ctx.restore()
        _fill(ctx, color if i % 3 else "#d9cfbd", a, preserve=True)
        _stroke(ctx, INK, 3 * s, a)


def dizzy_stars(ctx, x, y, s, t, t0=None, dur=None, n=3, rx=95, ry=26, speed=1.0,
                layer="both", color=STAR_YELLOW, ring=True):
    """3-4 stars (r ~25 px) orbiting a head at (x, y) on an ellipse rx x ry
    px at s=1 (0.85 turns/s). Continuous; with t0 it pops in over 0.3 s,
    with dur it pops out by t0+dur. layer: 'back' draws only the far half
    (call before the character), 'front' only the near half (after)."""
    if t0 is not None and t < t0:
        return
    k = 1.0
    if t0 is not None:
        k = ease_out_back(seg(t, t0, t0 + 0.3))
    if dur is not None:
        if t > t0 + dur:
            return
        k *= 1 - ease_in(seg(t, t0 + dur - 0.25, t0 + dur))
    if k < 0.02:
        return
    n = max(1, min(n, 5))
    if ring and layer in ("both", "back"):
        ellipse(ctx, x, y, rx * s * k, ry * s * k)
        ctx.set_dash([10 * s, 12 * s], -t * 60 * s)
        _stroke(ctx, INK, 3 * s, 0.35)
        ctx.set_dash([])
    for i in range(n):
        a = TAU * (t * 0.85 * speed + i / n)
        depth = math.sin(a)
        if layer == "back" and depth >= 0:
            continue
        if layer == "front" and depth < 0:
            continue
        sx = x + rx * s * k * math.cos(a)
        sy = y + ry * s * k * depth
        r = (25 + 7 * depth) * s * k
        _star_path(ctx, sx, sy, r, r * 0.46, 5, -math.pi / 2 + t * 3.0 + i)
        c = color if depth >= 0 else mixc(color, "#c9a640", 0.5)
        _fill(ctx, c, preserve=True)
        _stroke(ctx, INK, 4.5 * s)


def flash(ctx, t, t0, frames=2, color="white", peak=1.0):
    """Full-frame flash for `frames` (<=3) frames starting at t0."""
    frames = max(1, min(3, int(frames)))
    f = int(math.floor((t - t0) * FPS + 1e-4))
    if f < 0 or f >= frames:
        return
    a = (1.0, 0.7, 0.4)[f] * peak
    _rgba(ctx, color, a)
    ctx.paint()


def _bolt(ctx, x0, y0, ang, length, width, seed):
    """Filled lightning bolt polygon starting at (x0,y0) pointing along ang:
    a 3-step zigzag tapering to a point (classic comic bolt)."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    z = width * 0.55
    c = [(0.0, 0.0), (0.36, z), (0.44, -z * 0.45), (0.74, z * 0.6), (1.0, -z * 0.15)]
    left, right = [], []
    for i, (u, o) in enumerate(c):
        w = width * (1 - i / (len(c) - 1)) * 0.5
        j = (hash01(i, seed) - 0.5) * width * 0.5
        px = x0 + ux * u * length + nx * (o + j)
        py = y0 + uy * u * length + ny * (o + j)
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    poly(ctx, left + right[::-1])


def shock_lines(ctx, x, y, s, t, t0, dur=1.0, rx=200, ry=420, color="#fff36b",
                bolts=8, seed=0):
    """'Struck by lightning' freeze around a figure centred at (x, y)
    (ellipse rx x ry px at s=1): a bold crackling jagged outline plus
    filled zigzag bolts radiating out. Pattern re-rolls 8x per second.
    Pair with flash(ctx, t, t0) on the same t0."""
    if t < t0 or t > t0 + dur:
        return
    tau = t - t0
    k = ease_out_back(seg(tau, 0.0, 0.12), 2.5)
    a = 1 - smoothstep(seg(tau, dur - 0.22, dur))
    if k < 0.02 or a < 0.02:
        return
    v = int(tau * 8)
    RX, RY = rx * s * k, ry * s * k
    # jagged outline ring
    N = 22
    pts = []
    for i in range(N):
        ang = TAU * (i + 0.3 * (hash01(i + v * 31, seed + 5) - 0.5)) / N
        rr = (1.1 if i % 2 else 0.95) + (hash01(i + v * 101, seed + 3) - 0.5) * 0.08
        pts.append((x + RX * rr * math.cos(ang), y + RY * rr * math.sin(ang)))
    poly(ctx, pts)
    _stroke(ctx, INK, 22 * s, a, preserve=True, join=cairo.LINE_JOIN_MITER)
    _stroke(ctx, color, 11 * s, a, preserve=True, join=cairo.LINE_JOIN_MITER)
    _stroke(ctx, "#ffffff", 3.5 * s, a, join=cairo.LINE_JOIN_MITER)
    # bolts
    for b in range(bolts):
        ang = TAU * (b + 0.35 * (hash01(b + v * 7, seed + 9) - 0.5)) / bolts + 0.2
        cx, cy = math.cos(ang), math.sin(ang)
        r0 = 1.12
        ln = (110 + 60 * hash01(b + v * 13, seed)) * s
        bx0, by0 = x + RX * r0 * cx, y + RY * r0 * cy
        _bolt(ctx, bx0, by0, math.atan2(cy * RY, cx * RX) if RX > 0 else ang, ln, 40 * s,
              seed + b + v * 17)
        _fill(ctx, color, a, preserve=True)
        _stroke(ctx, INK, 5.5 * s, a, join=cairo.LINE_JOIN_MITER)


def sweat_fly(ctx, x, y, s, t, t0, seed=0, n=4, dur=0.65, side=0, color=SWEAT_BLUE):
    """Sweat drops flicking off a head at (x, y). side +1 = fly right,
    -1 = left, 0 = both. Drops r ~14-19 px at s=1, gone by t0+dur."""
    if t < t0 or t > t0 + dur:
        return
    n = min(n, 8)
    g = 1900 * s
    for i in range(n):
        h1, h2, h3 = hash01(i, seed + 1), hash01(i, seed + 2), hash01(i, seed + 3)
        tt = t - t0 - h1 * 0.12
        if tt <= 0:
            continue
        sd = side if side else (1 if i % 2 == 0 else -1)
        ang = -math.pi / 2 + sd * (0.35 + 0.85 * h2)
        v = (430 + 230 * h3) * s
        vx, vy = v * math.cos(ang), v * math.sin(ang)
        px = x + vx * tt
        py = y + vy * tt + 0.5 * g * tt * tt
        cvx, cvy = vx, vy + g * tt
        life = tt / (dur - h1 * 0.12)
        r = (14 + 5 * h2) * s * (1 - 0.45 * smoothstep(seg(life, 0.55, 1.0)))
        a = 1 - smoothstep(seg(life, 0.75, 1.0))
        # tip points back along the velocity
        _drop(ctx, px, py, r, math.atan2(-cvy, -cvx), color, a)


def heat_squiggles(ctx, x, y, s, t, amount=1.0, width=170, color=HEAT_RED, n=None):
    """Embarrassment heat lines rising above a head top at (x, y): 2-5
    wavy hot-pink strokes (with a pale core) across `width` px, ~50-80 px
    tall at s=1, looping (1.8 s); count/height/opacity follow amount 0..1."""
    amount = clamp(amount)
    if amount <= 0.02:
        return
    n = n if n is not None else int(round(2 + 3 * amount))
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        hx = x + u * width * s
        hlen = (48 + 34 * hash01(i, 5)) * s * (0.55 + 0.45 * amount)
        y0 = y - 12 * s - abs(u) * 26 * s
        ph = t * 1.6 + i * 0.37
        # rise and fade on a loop
        cyc = _frac(t * 0.55 + hash01(i, 9))
        lift = cyc * 22 * s
        a = amount * math.sin(math.pi * cyc) * 0.95
        if a < 0.03:
            continue
        pts = []
        for j in range(7):
            v = j / 6
            pts.append((hx + 9 * s * math.sin(TAU * (v * 1.3 - ph)),
                        y0 - lift - v * hlen))
        smooth_path(ctx, pts)
        _stroke(ctx, color, 9 * s, a, preserve=True)
        _stroke(ctx, "#ffe3e8", 3 * s, a)


def tap_marks(ctx, x, y, s, t, t0, taps=2, gap=0.32, angle=-math.pi / 2, label="tap",
              color="ink"):
    """'tap tap': little fan of impact ticks at the contact point (x, y) for
    each tap (t0, t0+gap, ...), plus an optional small comic word.
    `angle` = direction the ticks fan toward."""
    end = t0 + (taps - 1) * gap + 0.6
    if t < t0 or t > end:
        return
    for kk in range(taps):
        tk = t0 + kk * gap
        p = (t - tk) / 0.22
        if 0 <= p <= 1:
            for j in (-1, 0, 1):
                a = angle + j * 0.62
                r0 = (18 + 18 * p) * s
                r1 = r0 + 28 * s * (1 - 0.5 * p)
                _taper(ctx, x + math.cos(a) * r0, y + math.sin(a) * r0,
                       x + math.cos(a) * r1, y + math.sin(a) * r1, 10 * s, 5 * s)
                _fill(ctx, color, 1 - p * p)
        if label:
            q = (t - tk) / 0.55
            if 0 <= q <= 1:
                side = 1 if kk % 2 == 0 else -1
                lx = x + math.cos(angle) * 62 * s + side * 30 * s
                ly = y + math.sin(angle) * 62 * s - 18 * s * ease_out(q)
                sz = 46 * s * ease_out_back(seg(q, 0, 0.3))
                if sz > 2:
                    a = 1 - smoothstep(seg(q, 0.6, 1.0))
                    with saved(ctx, lx, ly, 1.0, side * 0.12):
                        set_font(ctx, "comic", sz)
                        e = ctx.text_extents(label)
                        ctx.move_to(-e[4] / 2, sz * 0.35)
                        ctx.text_path(label)
                        _stroke(ctx, INK, 6 * s, a, preserve=True)
                        _fill(ctx, "#ffffff", a)


EMOTES = ("question", "exclaim", "sweatdrop", "anger_vein", "sparkle", "heart", "zzz", "gulp")


def emote(ctx, kind, x, y, s, t, t0, dur=None, color=None):
    """Comic emote mark popping in at t0 (0.25 s overshoot) with a gentle idle;
    if `dur` is given it pops out at t0+dur. Kinds: question, exclaim,
    sweatdrop, anger_vein, sparkle, heart, zzz, gulp. ~90-120 px at s=1;
    (x, y) is the mark's centre."""
    if t < t0:
        return
    if dur is not None and t > t0 + dur:
        return
    tau = t - t0
    k = ease_out_back(seg(tau, 0, 0.25), 2.2)
    if dur is not None:
        k *= 1 - ease_in(seg(t, t0 + dur - 0.16, t0 + dur))
    if k < 0.02:
        return
    ctx.save()
    ctx.translate(x, y)
    if kind == "question":
        ctx.rotate(0.12 + 0.08 * math.sin(TAU * tau / 1.4))
        ctx.scale(k * s, k * s)
        set_font(ctx, "title", 120)
        e = ctx.text_extents("?")
        ctx.move_to(-e[0] - e[2] / 2, -e[1] - e[3] / 2)
        ctx.text_path("?")
        _stroke(ctx, INK, 12, preserve=True)
        _fill(ctx, color or "#ffffff")
    elif kind == "exclaim":
        ctx.scale(k * s, k * s)
        ctx.rotate(-0.1)
        bob = 4 * math.sin(TAU * tau / 0.9)
        ctx.translate(0, bob)
        poly(ctx, [(-21, -66), (21, -66), (9, 18), (-9, 18)])
        _stroke(ctx, INK, 22, preserve=True)
        _fill(ctx, color or STAR_YELLOW, preserve=True)
        _stroke(ctx, color or STAR_YELLOW, 8)
        circle(ctx, 0, 46, 17)
        _fill(ctx, color or STAR_YELLOW, preserve=True)
        _stroke(ctx, INK, 7)
        for j in (-1, 0, 1):
            a = -math.pi / 2 + j * 0.75
            _taper(ctx, math.cos(a) * 82, -14 + math.sin(a) * 82, math.cos(a) * 112,
                   -14 + math.sin(a) * 112, 11, 6)
            _fill(ctx, INK)
    elif kind == "sweatdrop":
        ctx.scale(k * s, k * s)
        slide = 18 * ease_in_out(seg(tau, 0.2, 1.2))
        _drop(ctx, 0, slide, 28, -math.pi / 2 - 0.15, color or SWEAT_BLUE, 1.0, ow=5)
    elif kind == "anger_vein":
        pulse = 1 + 0.12 * math.sin(TAU * tau / 0.7) ** 2
        ctx.scale(k * s * pulse, k * s * pulse)
        for p in (0, 1):
            for qd in range(4):
                ctx.save()
                ctx.rotate(qd * math.pi / 2)
                ctx.move_to(12, -40)
                ctx.curve_to(12, -14, 14, -12, 40, -12)
                ctx.restore()
                if p == 0:
                    _stroke(ctx, INK, 21)
                else:
                    _stroke(ctx, color or "#ff3b5c", 10)
    elif kind == "sparkle":
        ctx.scale(k * s, k * s)
        for i, (sx, sy, r) in enumerate(((0, 0, 52), (52, -44, 26), (-46, 36, 21))):
            tw = 0.65 + 0.35 * math.sin(TAU * (tau / 0.9 + i * 0.33)) ** 2
            _twinkle_path(ctx, sx, sy, r * tw, 0.24)
            _fill(ctx, color or "#fffbe0", preserve=True)
            _stroke(ctx, INK, 5)
    elif kind == "heart":
        rise = -24 * ease_out(seg(tau, 0, 1.2))
        beat = 1 + 0.1 * max(0.0, math.sin(TAU * tau / 0.8)) ** 4
        ctx.translate(0, rise)
        ctx.scale(k * s * beat, k * s * beat)
        _heart_path(ctx, 0, 0, 40)
        _fill(ctx, color or "#ff6f91", preserve=True)
        _stroke(ctx, INK, 6)
        ellipse(ctx, -16, -14, 7, 10, 0.6)
        _fill(ctx, "#ffffff", 0.85)
    elif kind == "zzz":
        ctx.scale(k * s, k * s)
        for i in range(3):
            ph = _frac(tau / 1.8 + i / 3)
            zx = -30 + 90 * ph + 10 * math.sin(TAU * ph)
            zy = 40 - 120 * ph
            sz = 24 + 34 * ph
            a = smoothstep(seg(ph, 0, 0.12)) * (1 - smoothstep(seg(ph, 0.65, 1.0)))
            if a < 0.03:
                continue
            _z_path(ctx, zx, zy, sz, -0.15)
            _fill(ctx, color or "#ffffff", a, preserve=True)
            _stroke(ctx, INK, 4.5, a)
    elif kind == "gulp":
        ctx.scale(k * s, k * s)
        dy = 10 * ease_in_out(seg(tau, 0.05, 0.45))
        sq = 1 - 0.12 * math.sin(math.pi * seg(tau, 0.05, 0.45))
        ctx.save()
        ctx.translate(0, dy)
        ctx.scale(1 / sq, sq)
        set_font(ctx, "comic", 52)
        e = ctx.text_extents("gulp")
        ctx.move_to(-e[4] / 2, 16)
        ctx.text_path("gulp")
        _stroke(ctx, INK, 8, preserve=True)
        _fill(ctx, color or "#ffffff")
        ctx.restore()
        for sd in (-1, 1):
            ctx.move_to(sd * 64, -14 + dy)
            ctx.curve_to(sd * 76, -2 + dy, sd * 76, 14 + dy, sd * 64, 26 + dy)
            _stroke(ctx, INK, 5)
    else:
        ctx.restore()
        raise ValueError(f"unknown emote kind {kind!r}; use one of {EMOTES}")
    ctx.restore()


# ----------------------------------------------------------------------------
# 3. Story effects
# ----------------------------------------------------------------------------
def music_notes(ctx, x, y, s, t, intensity=1.0, direction=1, color="#fff3c4", n=4,
                rise=190, period=2.4, seed=0):
    """Little notes (single and beamed pairs, drawn as shapes) leaking up
    from a headphone cup at (x, y), drifting up and sideways by `direction`.
    Notes are ~45 px tall at s=1; <= n (4) on screen."""
    intensity = clamp(intensity)
    if intensity <= 0.01:
        return
    n = min(n, 8)
    active = max(1, int(math.ceil(n * intensity)))
    for i in range(active):
        u = t / period + i / n + hash01(i, seed) * 0.15
        cyc = math.floor(u)
        ph = u - cyc
        kind = 1 if hash01(int(cyc) * 7 + i, seed + 3) < 0.4 else 0
        a = smoothstep(seg(ph, 0, 0.15)) * (1 - smoothstep(seg(ph, 0.6, 1.0)))
        a *= min(1.0, 0.4 + intensity)
        if a < 0.03:
            continue
        hx = hash01(int(cyc) * 3 + i, seed + 5) - 0.5
        px = x + direction * (14 + 110 * ph) * s + hx * 40 * s \
            + 16 * s * math.sin(TAU * (ph * 1.2) + i)
        py = y - rise * s * ph
        sz = 12 * s * (0.5 + 0.5 * ease_out_back(seg(ph, 0, 0.25)))
        with saved(ctx, px, py, 1.0, 0.28 * math.sin(TAU * ph + i) - 0.1 * direction):
            _note_shape(ctx, kind, color, a, sz)


def ripple_rings(ctx, x, y, s, t, t0, color="power", n=3, interval=0.4, ring_dur=1.5,
                 max_r=760, width=9, outline_fn=None, outline_fill=0.12):
    """The SENSE: sonar rings expanding from (x, y) starting at t0 (one every
    `interval` s, each lasting ring_dur), fading as they grow to max_r*s.
    outline_fn(ctx) may append a silhouette PATH (no fill/stroke); it lights
    up with a teal outline as a ring passes over it, then fades."""
    end = t0 + (n - 1) * interval + ring_dur
    if t < t0 or t > end + (0.6 if outline_fn else 0):
        return
    R0 = 26 * s
    RM = max_r * s
    rings = []
    for kk in range(n):
        tau = t - (t0 + kk * interval)
        p = tau / ring_dur
        rings.append((p, R0 + (RM - R0) * ease_out(clamp(p))))
        if not (0 <= p <= 1):
            continue
        r = rings[-1][1]
        a = (1 - p) ** 1.3
        circle(ctx, x, y, r)
        if p < 0.55:  # soft halo while the ring is young
            _stroke(ctx, color, width * s * (3.0 - 1.6 * p), a * 0.18 * (1 - p / 0.55),
                    preserve=True)
        _stroke(ctx, _lighten(color, 0.35 * (1 - p)), width * s * (1 - 0.5 * p), a * 0.92)
    # ping core
    pc = seg(t, t0, t0 + 0.3)
    if 0 < pc < 1:
        circle(ctx, x, y, (10 + 24 * ease_out(pc)) * s)
        _fill(ctx, color, 1 - pc)
    if outline_fn is None:
        return
    ctx.save()
    ctx.new_path()
    outline_fn(ctx)
    path = ctx.copy_path()
    x1, y1, x2, y2 = ctx.path_extents()
    ctx.new_path()
    if x2 <= x1:
        ctx.restore()
        return
    # nearest / farthest distance of the silhouette box from the ring centre
    dxn = max(x1 - x, 0, x - x2)
    dyn = max(y1 - y, 0, y - y2)
    dn = math.hypot(dxn, dyn)
    df = math.hypot(max(abs(x - x1), abs(x - x2)), max(abs(y - y1), abs(y - y2)))
    glow = 0.0
    for (p, r) in rings:
        if p < 0:
            continue
        if r < dn:
            gk = math.exp(-((dn - r) / (70 * s)) ** 2)
        elif r <= df:
            gk = 1.0
        else:
            gk = math.exp(-((r - df) / (160 * s)) ** 2)
        if p > 1:  # ring finished: let the last glow fade out
            gk *= max(0.0, 1 - (p - 1) * ring_dur / 0.6)
        glow = max(glow, gk * (1 - 0.35 * clamp(p)))
    if glow > 0.02:
        ctx.append_path(path)
        if outline_fill > 0:
            _fill(ctx, color, outline_fill * glow, preserve=True)
        _stroke(ctx, color, 22 * s, 0.25 * glow, preserve=True)
        _stroke(ctx, _lighten(color, 0.5), 5 * s, 0.95 * glow)
    ctx.restore()


def power_aura(ctx, x, y, w, h, t, amount, color="power", outline_fn=None, pulse=0.0):
    """Soft teal aura around a figure: concentric soft strokes around a
    capsule (centre x, y, size w x h) or around outline_fn's PATH. Static
    for a given amount (pulse>0 adds a gentle 1.2 s breathing)."""
    amount = clamp(amount)
    if amount <= 0.01:
        return
    if pulse > 0:
        amount *= 1 - pulse * 0.25 * (0.5 + 0.5 * math.sin(TAU * t / 1.2))
    bands = ((58, 0.07), (40, 0.10), (24, 0.16), (11, 0.32), (4, 0.85))
    if outline_fn is not None:
        ctx.save()
        ctx.new_path()
        outline_fn(ctx)
        for wd, al in bands:
            _stroke(ctx, color if wd > 4 else _lighten(color, 0.4), wd * (0.5 + 0.5 * amount),
                    al * amount, preserve=True)
        ctx.new_path()
        ctx.restore()
        return
    aq = round(amount * 20) / 20.0

    def draw(c):
        for wd, al in bands[:-1]:
            off = wd * 0.3
            rrect(c, -w / 2 - off, -h / 2 - off, w + 2 * off, h + 2 * off, w / 2 + off)
            _stroke(c, color, wd * (0.6 + 0.4 * aq), al * 1.25 * aq)
        rrect(c, -w / 2, -h / 2, w, h, w / 2)
        _fill(c, color, 0.06 * aq)
    m = 70
    with saved(ctx, x, y):
        _layer(ctx, ("aura", round(w, 1), round(h, 1), aq, str(color)), -w / 2 - m, -h / 2 - m,
               w + 2 * m, h + 2 * m, draw)


def eye_glint(ctx, x, y, s, t, t0, dur=0.4, color="white", halo="power"):
    """Tiny glint flash on an eye at (x, y): a 4-point twinkle (r ~26 px at
    s=1) that blooms, turns 45 deg and vanishes by t0+dur."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    k = math.sin(math.pi * p) ** 0.8
    if k < 0.02:
        return
    r = 26 * s * k
    if halo:
        radial_glow(ctx, x, y, r * 2.4, halo, 0.55 * k)
    _taper(ctx, x - r * 1.9, y, x + r * 1.9, y, 3 * s * k, 3 * s * k)
    _fill(ctx, color, 0.7 * k)
    _twinkle_path(ctx, x, y, r, 0.2, p * math.pi / 4)
    _fill(ctx, color)


def _eyelid_open(p, blinks):
    keys = [(0.0, 0.0), (0.07, 0.0)]
    peaks = [(0.46, 0.12), (0.66, 0.36), (0.8, 0.5)]
    blinks = max(0, min(3, int(blinks)))
    span = 0.93 / (blinks + 1)
    tt = 0.07
    for b in range(blinks):
        o, c = peaks[b]
        keys.append((tt + span * 0.62, o))
        keys.append((tt + span, c))
        tt += span
    keys.append((1.0, 1.0))
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if p < t1:
            return lerp(v0, v1, ease_in_out((p - t0) / (t1 - t0)) if t1 > t0 else 1)
    return 1.0


def _lid_path(ctx, top, edge_c, curve):
    """Lid region: top lid if top else bottom; edge_c = edge y at frame centre."""
    pts = []
    for i in range(9):
        u = i / 8
        xx = -40 + (W + 80) * u
        d = (xx - W / 2) / (W * 0.62)
        yy = edge_c + (curve * d * d if top else -curve * d * d)
        pts.append((xx, yy))
    if top:
        ctx.move_to(-40, -40)
        ctx.line_to(*pts[0])
        _smooth_path_cont(ctx, pts)
        ctx.line_to(W + 40, -40)
    else:
        ctx.move_to(-40, H + 40)
        ctx.line_to(*pts[0])
        _smooth_path_cont(ctx, pts)
        ctx.line_to(W + 40, H + 40)
    ctx.close_path()


def _smooth_path_cont(ctx, pts, tension=0.5):
    """Catmull-Rom through pts continuing the current path (no move_to)."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(pts)):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])


def eyelid_wipe(ctx, t, t0, dur=1.3, blinks=2, color="#07040b", cy=H * 0.47):
    """Waking-up POV. Full black at t0; two dark curved lids (soft edges)
    part slowly, half-close `blinks` times, then open fully by t0+dur.
    A soft dark vignette recedes over the same time. Screen space."""
    if t < t0 or t > t0 + dur:
        return
    p = (t - t0) / dur
    o = _eyelid_open(p, blinks)
    if o <= 0.002:
        _rgba(ctx, color)
        ctx.paint()
        return
    # recede vignette (blur suggestion)
    vk = 1 - ease_out(seg(p, 0.0, 1.0))
    if vk > 0.02:
        vignette(ctx, 0.95 * vk, color, inner=0.35)
    half = o * (H * 0.72)
    curve = min(half * 0.85, 340)
    warm = _darken("#5a1a24", 0.55)
    bands = ((78, 0.12, warm), (46, 0.22, warm), (22, 0.42, color), (8, 0.7, color))
    for top in (True, False):
        ec = cy - half if top else cy + half
        sgn = 1 if top else -1
        for d, a, c in bands:
            _lid_path(ctx, top, ec + sgn * d, curve)
            _fill(ctx, c, a)
        _lid_path(ctx, top, ec, curve)
        _fill(ctx, color)


def _vig_draw(c, color, inner, x, y, w, h):
    col = hexc(color)
    g = cairo.RadialGradient(0, 0, inner, 0, 0, 1.0)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0)
    g.add_color_stop_rgba(0.55, col[0], col[1], col[2], 0.45 * col[3])
    g.add_color_stop_rgba(1, col[0], col[1], col[2], col[3])
    # pattern space: unit circle == the vignette ellipse
    mm = cairo.Matrix(1.0 / (w * 0.62), 0, 0, 1.0 / (h * 0.6),
                      -(x + w / 2) / (w * 0.62), -(y + h / 2) / (h * 0.6))
    g.set_matrix(mm)
    c.rectangle(x, y, w, h)
    c.set_source(g)
    c.fill()


def vignette(ctx, amount=0.5, color="ink", inner=0.55, x=0, y=0, w=W, h=H):
    """Static darkening frame over (x, y, w, h) (default full frame), blitted
    from a cached bitmap with opacity `amount`. Screen space."""
    if amount <= 0.01:
        return
    inner = round(clamp(inner, 0.0, 0.95) * 20) / 20

    def draw(c):
        _vig_draw(c, color, inner, x, y, w, h)
    ctx.save()
    # skip the fully transparent centre (speed)
    hw, hh = inner * 0.62 * w * 0.7, inner * 0.6 * h * 0.7
    if hw > 20 and hh > 20:
        ctx.rectangle(x, y, w, h)
        ctx.rectangle(x + w / 2 + hw, y + h / 2 - hh, -2 * hw, 2 * hh)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.clip()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    _layer(ctx, ("vignette", str(color), inner, x, y, w, h), x, y, w, h, draw,
           a=clamp(amount), pad=0, exact=True)
    ctx.restore()


def alarm_wash(ctx, t, amount=1.0, beacon=(540, 120), period=1.6, tint_period=1.2,
               color="danger", lamp=False):
    """Rotating red beacon light: two flat, banded light cones sweeping from
    `beacon` (one turn per `period` s) over a gentle dark-red tint that
    pulses with `tint_period` (>= 0.7 s). Screen space; nothing at 0."""
    amount = clamp(amount)
    if amount <= 0.01:
        return
    tint_period = max(0.7, tint_period)
    pulse = 0.5 + 0.5 * math.sin(TAU * t / tint_period)
    # tint: deep red OVER (reddens and dims the room without a wash-out)
    _rgba(ctx, "#9a0c1c", amount * (0.34 + 0.14 * pulse))
    ctx.paint()
    bx, by = beacon
    L = 2400
    for b in range(2):
        a = TAU * t / period + b * math.pi
        face = 0.5 + 0.5 * math.cos(a)          # 1 = beam toward the camera
        if face < 0.06:
            continue
        ang = math.pi / 2 - 1.25 * math.sin(a)  # screen direction (down = pi/2)
        half = 0.2 + 0.16 * face
        for kk, (wk, lk, al) in enumerate(((1.0, 1.0, 0.16), (0.55, 0.8, 0.16))):
            hh = half * wk
            ll = L * lk
            ctx.move_to(bx, by)
            ctx.line_to(bx + ll * math.cos(ang - hh), by + ll * math.sin(ang - hh))
            ctx.line_to(bx + ll * math.cos(ang + hh), by + ll * math.sin(ang + hh))
            ctx.close_path()
            _fill(ctx, "#ff4a5e", al * amount * face)
    if lamp:
        radial_glow(ctx, bx, by, 120, color, 0.8 * amount)
        circle(ctx, bx, by, 26)
        _fill(ctx, _lighten(color, 0.35), preserve=True)
        _stroke(ctx, INK, 5)


def heartbeat_sync(ctx, x1, y1, x2, y2, t, t0, sync, s=1.0, period=0.9, c1="#ff6f91",
                   c2="#ff6f91", glow="power", t1=None, link=True):
    """Two small glowing hearts (r ~30 px at s=1) beating 'lub-dub'. At
    sync 0 the second beats off-phase with a drifting lag; as sync -> 1 the
    beats lock together and a dotted link between them lights on each beat.
    Fades in over 0.3 s from t0; optional fade-out ending at t1."""
    if t < t0 or (t1 is not None and t > t1):
        return
    fa = smoothstep(seg(t, t0, t0 + 0.3))
    if t1 is not None:
        fa *= 1 - smoothstep(seg(t, t1 - 0.3, t1))
    if fa < 0.02:
        return
    sync = clamp(sync)
    tau = t - t0
    lag = (1 - sync) * (0.5 + 0.22 * math.sin(TAU * tau / 3.1))

    def beat(ph):
        ph = _frac(ph)
        return math.exp(-(ph / 0.07) ** 2) + math.exp(-((ph - 1) / 0.07) ** 2) \
            + 0.6 * math.exp(-((ph - 0.24) / 0.07) ** 2)
    b1 = beat(tau / period)
    b2 = beat(tau / period + lag)
    for (hx, hy, b, c) in ((x1, y1, b1, c1), (x2, y2, b2, c2)):
        if glow:
            radial_glow(ctx, hx, hy, 70 * s * (1 + 0.25 * b), glow, (0.25 + 0.35 * b) * fa)
        r = 30 * s * (1 + 0.2 * b)
        _heart_path(ctx, hx, hy, r)
        _fill(ctx, c, fa, preserve=True)
        _stroke(ctx, INK, 4.5 * s, fa)
        ellipse(ctx, hx - r * 0.4, hy - r * 0.35, r * 0.17, r * 0.25, 0.6)
        _fill(ctx, "#ffffff", 0.85 * fa)
    if link and sync > 0.6:
        lk = smoothstep(seg(sync, 0.6, 0.95))
        bb = min(b1, b2)
        L = math.hypot(x2 - x1, y2 - y1)
        nd = max(3, int(L / (34 * s)))
        for i in range(1, nd):
            u = i / nd
            px = lerp(x1, x2, u)
            py = lerp(y1, y2, u) - math.sin(math.pi * u) * L * 0.18
            circle(ctx, px, py, 6 * s * (1 + 0.45 * bb))
            _fill(ctx, glow or c1, fa * lk * (0.45 + 0.55 * bb), preserve=True)
            _stroke(ctx, INK, 2 * s, fa * lk * 0.6)


def _time_slow_draw(c, cx, cy):
    c.rectangle(0, 0, W, H)
    _fill(c, "#1f7480", 0.2)
    for i in range(18):
        a = TAU * (i + 0.4 * hash01(i, 3)) / 18
        wd = 0.012 + 0.016 * hash01(i, 5)
        r0 = 330 + 200 * hash01(i, 7)
        c.move_to(cx + r0 * math.cos(a), cy + r0 * math.sin(a))
        c.line_to(cx + 1700 * math.cos(a - wd), cy + 1700 * math.sin(a - wd))
        c.line_to(cx + 1700 * math.cos(a + wd), cy + 1700 * math.sin(a + wd))
        c.close_path()
    _fill(c, "#c9fbff", 0.22)
    _vig_draw(c, _rgba_of("#05302f", 0.55), 0.45, 0, 0, W, H)


def _rgba_of(c, a):
    r, g, b, aa = hexc(c)
    return (r, g, b, aa * a)


def time_slow(ctx, t, amount, cx=W / 2, cy=H * 0.45):
    """Slowed time: a cool teal tint, faint tapered radial streaks from
    (cx, cy) and a dark-teal vignette -- one static cached layer blitted at
    opacity `amount` (bitrate-friendly; t is accepted for API symmetry).
    Screen space."""
    amount = clamp(amount)
    if amount <= 0.01:
        return
    _layer(ctx, ("time_slow", round(cx), round(cy)), 0, 0, W, H,
           lambda c: _time_slow_draw(c, cx, cy), a=amount, pad=0, exact=True)


def black(ctx, a=1.0):
    """Full black fill (s11 end only)."""
    ctx.set_source_rgba(0, 0, 0, a)
    ctx.paint()


# ----------------------------------------------------------------------------
# HushCorp logo + portrait stand-in (used by the screens)
# ----------------------------------------------------------------------------
def hush_logo(ctx, x, y, s=1.0, wordmark=True, color="hush", hole="#ffffff",
              text_color="ink", text_size=None):
    """HushCorp logo: teal circle (r 40*s) with a keyhole, centred at (x, y),
    plus the wide-tracked 'HUSHCORP' wordmark to its right."""
    R = 40 * s
    circle(ctx, x, y, R)
    _fill(ctx, color)
    circle(ctx, x, y - R * 0.16, R * 0.28)
    poly(ctx, [(x - R * 0.13, y - R * 0.05), (x + R * 0.13, y - R * 0.05),
               (x + R * 0.22, y + R * 0.52), (x - R * 0.22, y + R * 0.52)])
    _fill(ctx, hole)
    if wordmark:
        ts = text_size or R * 0.95
        _tracked(ctx, "HUSHCORP", x + R * 1.45, y + ts * 0.36, ts, text_color, "ui",
                 tracking=ts * 0.28)


def standin_portrait(ctx, cx, cy, s=1.0):
    """Simple Tiredness bust (frame = 300*s square centred at cx, cy): navy
    hoodie, headphones round the neck, messy mop with a cowlick, heavy lids."""
    ow = 5 * s
    with saved(ctx, cx, cy, s):
        # hoodie shoulders
        ctx.move_to(-150, 160)
        ctx.curve_to(-140, 70, -90, 52, -40, 48)
        ctx.line_to(40, 48)
        ctx.curve_to(90, 52, 140, 70, 150, 160)
        ctx.close_path()
        fill(ctx, PAL["t_hoodie"], preserve=True)
        stroke(ctx, INK, 5)
        # neck
        rrect(ctx, -22, 20, 44, 40, 10)
        fill(ctx, PAL["t_skin_sh"], preserve=True)
        stroke(ctx, INK, 4)
        # headphones around the neck
        ctx.move_to(-62, 50)
        ctx.curve_to(-60, 86, 60, 86, 62, 50)
        stroke(ctx, INK, 16)
        ctx.move_to(-62, 50)
        ctx.curve_to(-60, 86, 60, 86, 62, 50)
        stroke(ctx, PAL["headphones"], 9)
        for sd in (-1, 1):
            ellipse(ctx, sd * 64, 54, 18, 24)
            fill(ctx, PAL["headphones"], preserve=True)
            stroke(ctx, INK, 4)
        # head
        ellipse(ctx, 0, -40, 64, 74)
        fill(ctx, PAL["t_skin"], preserve=True)
        stroke(ctx, INK, 5)
        # eyes: heavy lids + bags
        for sd in (-1, 1):
            ex, ey = sd * 26, -36
            ellipse(ctx, ex, ey + 9, 15, 6)
            _fill(ctx, PAL["t_bags"], 0.7)
            ellipse(ctx, ex, ey, 13, 11)
            fill(ctx, "#ffffff", preserve=True)
            stroke(ctx, INK, 3)
            circle(ctx, ex + 1, ey + 3, 5.5)
            fill(ctx, INK)
            # lid covering ~45%
            ctx.save()
            ellipse(ctx, ex, ey, 13.5, 11.5)
            ctx.clip()
            ctx.rectangle(ex - 16, ey - 14, 32, 13)
            fill(ctx, PAL["t_skin_sh"])
            ctx.restore()
            ctx.move_to(ex - 14, ey - 1)
            ctx.line_to(ex + 14, ey - 1)
            stroke(ctx, INK, 3.5)
            # brow
            ctx.move_to(ex - 13, ey - 20)
            ctx.line_to(ex + 13, ey - 18 - sd * 1)
            stroke(ctx, PAL["t_hair"], 5)
        # mouth: flat
        ctx.move_to(-12, 4)
        ctx.line_to(12, 3)
        stroke(ctx, INK, 3.5)
        # hair mop
        pts = [(-70, -30), (-74, -70), (-56, -108), (-20, -122), (20, -124), (56, -110),
               (74, -74), (70, -36), (58, -62), (40, -56), (22, -70), (0, -58), (-22, -70),
               (-42, -56), (-58, -64)]
        smooth_path(ctx, pts, closed=True)
        fill(ctx, PAL["t_hair"], preserve=True)
        stroke(ctx, INK, 4)
        # cowlick
        ctx.move_to(4, -122)
        ctx.curve_to(10, -150, 34, -150, 30, -136)
        stroke(ctx, INK, 9)
        ctx.move_to(4, -122)
        ctx.curve_to(10, -150, 34, -150, 30, -136)
        stroke(ctx, PAL["t_hair"], 4.5)


# ----------------------------------------------------------------------------
# 4. UI screens
# ----------------------------------------------------------------------------
UI_BG = "#f4f6fa"
UI_TXT = "#2b3142"
UI_GREY = "#6b7486"


def type_times(t_type, query="HUSHCORP", char_dt=0.11):
    """Per-character keypress times for search_screen (for typing SFX)."""
    return [t_type + i * char_dt for i in range(len(query))]


def _magnifier(ctx, x, y, r, col, w=None):
    circle(ctx, x - r * 0.15, y - r * 0.15, r * 0.62)
    _stroke(ctx, col, w or r * 0.28)
    ctx.move_to(x + r * 0.3, y + r * 0.3)
    ctx.line_to(x + r * 0.85, y + r * 0.85)
    _stroke(ctx, col, (w or r * 0.28) * 1.3)


def _cursor(ctx, x, y, s=1.0):
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    poly(ctx, [(x + px * s, y + py * s) for px, py in pts])
    _fill(ctx, "#ffffff", preserve=True)
    _stroke(ctx, INK, 3 * s)


def _browser_chrome(c, RW, RH, tab, url, fav):
    rrect(c, 0, 0, RW, RH, 22)
    _fill(c, UI_BG)
    c.rectangle(0, 0, RW, 62)
    _fill(c, "#dde3ee")
    for i, col in enumerate(("#ff6b6b", "#ffc94d", "#5fd38a")):
        circle(c, 32 + 26 * i, 31, 8.5)
        _fill(c, col)
    # tab
    c.move_to(118, 62)
    c.line_to(118, 24)
    c.arc(132, 24, 14, math.pi, 1.5 * math.pi)
    c.line_to(430, 10)
    c.arc(430, 24, 14, 1.5 * math.pi, 0)
    c.line_to(444, 62)
    c.close_path()
    _fill(c, UI_BG)
    if fav == "hush":
        hush_logo(c, 146, 38, 0.27, wordmark=False)
    else:
        _magnifier(c, 146, 38, 13, "#3d4f86", 3.5)
    text(c, tab, 168, 47, 24, UI_TXT, "ui", "left")
    # address bar
    rrect(c, 24, 74, RW - 48, 52, 26)
    _fill(c, "#ffffff", preserve=True)
    _stroke(c, "#c5cdda", 2.5)
    # lock
    rrect(c, 44, 98, 18, 15, 3)
    _fill(c, UI_GREY)
    c.arc(53, 98, 6, math.pi, 0)
    _stroke(c, UI_GREY, 3)
    text(c, url, 76, 109, 25, "#4a5468", "ui", "left")


def _search_home(c, RW, RH):
    _browser_chrome(c, RW, RH, "Seekly", "seekly.com", "seek")
    cy0 = 140 + (RH - 140) * 0.26
    lw = _tw(c, "seekly", "round", 84)
    _magnifier(c, RW / 2 - lw / 2 - 20, cy0 - 26, 34, "#3d4f86", 9)
    text(c, "seekly", RW / 2 + 26, cy0, 84, "#3d4f86", "round", "center")
    by = cy0 + 46
    rrect(c, 80, by, RW - 160, 92, 46)
    _fill(c, "#ffffff", preserve=True)
    _stroke(c, "#9aa6bf", 4)
    _magnifier(c, 128, by + 44, 18, "#9aa6bf", 4.5)
    rrect(c, RW / 2 - 90, by + 122, 180, 58, 29)
    _fill(c, "#e6ebf3")
    text(c, "Search", RW / 2, by + 161, 28, UI_TXT, "ui", "center")


_RESULTS = (
    ("HushCorp — Official Site", "hushcorp.com", "We keep secrets so you don't have to."),
    ("Research Campus — Visitor Entrance", "hushcorp.com/campus",
     "Directions, parking & visitor badges."),
    ("Is HushCorp hiding something?", "forum.example › threads",
     "This thread has been removed."),
)


def _result_rows(RH):
    top = 286
    sp = min(126.0, (RH - top - 6) / 3.0)
    n = 3 if top + 2 * sp + 96 <= RH else 2
    return top, sp, n


def _search_results(c, RW, RH, query):
    _browser_chrome(c, RW, RH, query.lower() + " - Seekly", "seekly.com/search?q=" + query.lower(),
                    "seek")
    rrect(c, 24, 146, RW - 48, 70, 35)
    _fill(c, "#ffffff", preserve=True)
    _stroke(c, "#9aa6bf", 3)
    _magnifier(c, 64, 181, 15, "#9aa6bf", 4)
    text(c, query, 96, 196, 38, INK, "ui", "left")
    text(c, "About 3 results (0.0001 seconds)", 40, 254, 22, "#8a92a3", "ui", "left")
    top, sp, n = _result_rows(RH)
    for i in range(n):
        ti, url, snip = _RESULTS[i]
        ry = top + i * sp
        ts = _fit_size(c, ti, "ui", 36, RW - 80)
        text(c, ti, 40, ry + 34, ts, LINK_BLUE, "ui", "left")
        text(c, url, 40, ry + 64, 23, "#2e8b57", "ui", "left")
        text(c, snip, 40, ry + 96, _fit_size(c, snip, "ui", 26, RW - 80), "#4a5468", "ui", "left")


def _site_layout(RH):
    hero_y = 220
    hero_h = clamp(0.42 * (RH - 220 - 20), 190, 340)
    card_y = hero_y + hero_h + 18
    card_h = RH - card_y - 20
    return hero_y, hero_h, card_y, card_h


def _site_page(c, RW, RH):
    _browser_chrome(c, RW, RH, "HushCorp", "hushcorp.com", "hush")
    c.rectangle(0, 136, RW, 84)
    _fill(c, "#ffffff")
    hush_logo(c, 62, 178, 0.62, wordmark=True, text_size=30)
    for i, lab in enumerate(("CONTACT", "CAREERS", "ABOUT")):
        text(c, lab, RW - 36 - i * 128, 186, 19, UI_GREY, "ui", "right")
    c.rectangle(0, 219, RW, 2)
    _fill(c, "#d5dde6")
    hy, hh, _, _ = _site_layout(RH)
    c.rectangle(0, hy, RW, hh)
    _fill(c, "#123a44")
    # big faint keyhole motif
    hush_logo(c, RW - 130, hy + hh / 2, hh / 95.0, wordmark=False, color="#1b5560",
              hole="#123a44")
    sz = min(92, hh * 0.36)
    _tracked(c, "HUSHCORP", 46, hy + 30 + sz * 0.78, sz, "#ffffff", "ui", tracking=sz * 0.12)
    ts = min(46, hh * 0.17)
    text(c, "We keep secrets so", 48, hy + 30 + sz * 0.78 + ts * 1.55, ts, "#bff4ee", "ui", "left")
    text(c, "you don't have to.", 48, hy + 30 + sz * 0.78 + ts * 2.75, ts, "#bff4ee", "ui", "left")


def _map_thumb(c, x, y, w, h):
    rrect(c, x, y, w, h, 14)
    c.save()
    _fill(c, "#e3ecdf", preserve=True)
    c.clip()
    # river
    c.move_to(x - 10, y + h * 0.78)
    c.curve_to(x + w * 0.3, y + h * 0.62, x + w * 0.6, y + h * 1.0, x + w + 10, y + h * 0.82)
    _stroke(c, "#a9d4e6", h * 0.14)
    # blocks
    for (bx, by, bw, bh) in ((0.08, 0.1, 0.22, 0.22), (0.62, 0.08, 0.3, 0.2),
                             (0.1, 0.44, 0.2, 0.18), (0.66, 0.42, 0.24, 0.2)):
        rrect(c, x + bx * w, y + by * h, bw * w, bh * h, 5)
        _fill(c, "#cfd6d0")
    # campus
    rrect(c, x + 0.4 * w, y + 0.26 * h, 0.2 * w, 0.24 * h, 5)
    _fill(c, "#9fd8d2", preserve=True)
    _stroke(c, "#0f6f6a", 2.5)
    # roads
    for (x0, y0, x1, y1) in ((0, 0.38, 1, 0.34), (0.36, 0, 0.34, 1), (0.64, 0, 0.66, 1)):
        c.move_to(x + x0 * w, y + y0 * h)
        c.line_to(x + x1 * w, y + y1 * h)
        _stroke(c, "#b8beb6", 9)
        c.move_to(x + x0 * w, y + y0 * h)
        c.line_to(x + x1 * w, y + y1 * h)
        _stroke(c, "#ffffff", 6)
    c.restore()
    rrect(c, x, y, w, h, 14)
    _stroke(c, "#b9c3cf", 2.5)


def _pin(c, x, y, s=1.0, color="danger"):
    """Map pin with its tip at (x, y)."""
    _drop_path(c, x, y - 30 * s, 17 * s, math.pi / 2, tail=1.75)
    _fill(c, color, preserve=True)
    _stroke(c, INK, 3.5 * s)
    circle(c, x, y - 30 * s, 6.5 * s)
    _fill(c, "#ffffff")


def _site_card(c, RW, RH):
    _, _, cy, ch = _site_layout(RH)
    x, w = 30, RW - 60
    rrect(c, x + 5, cy + 7, w, ch, 20)
    _fill(c, "#0b1d22", 0.15)
    rrect(c, x, cy, w, ch, 20)
    _fill(c, "#ffffff", preserve=True)
    _stroke(c, "#c5cdda", 3)
    mh = ch - 28
    mw = min(w * 0.4, mh * 1.6)
    _map_thumb(c, x + 14, cy + 14, mw, mh)
    tx = x + 14 + mw + 24
    avail = x + w - tx - 18
    s1 = _fit_size(c, "Research Campus", "ui", 40, avail)
    s2 = _fit_size(c, "— Visitor Entrance", "ui", 32, avail)
    text(c, "Research Campus", tx, cy + 18 + s1 * 0.95, s1, INK, "ui", "left")
    text(c, "— Visitor Entrance", tx, cy + 18 + s1 * 0.95 + s2 * 1.25, s2, "#0f8f86",
         "ui", "left")
    by = cy + 18 + s1 * 0.95 + s2 * 1.25 + 16
    bh = min(44, cy + ch - by - 12)
    if bh > 26:
        fs = bh * 0.55
        bw = _tw(c, "Get directions", "ui", fs) + 36 + fs * 0.9
        rrect(c, tx, by, bw, bh, bh / 2)
        _fill(c, "#18a99f")
        adv = text(c, "Get directions", tx + 18, by + bh * 0.7, fs, "#ffffff", "ui", "left")
        ax = tx + 18 + adv + fs * 0.35
        c.move_to(ax, by + bh * 0.3)
        c.line_to(ax + fs * 0.32, by + bh * 0.5)
        c.line_to(ax, by + bh * 0.7)
        _stroke(c, "#ffffff", fs * 0.16)


def search_screen(ctx, x, y, w, h, t, t_type, query="HUSHCORP", t_results=None,
                  t_site=None, char_dt=0.11):
    """Browser in rect (x, y, w, h) (designed at 900 px wide; scales). Query
    types one letter every char_dt from t_type, results at t_results
    (default typing end + 0.35 s), HushCorp site at t_site (default
    t_results + 1.3 s) with the campus card sliding up and a map pin drop."""
    RW = 900.0
    sc = w / RW
    RH = h / sc
    n = len(query)
    t_done = t_type + n * char_dt
    if t_results is None:
        t_results = t_done + 0.35
    if t_site is None:
        t_site = t_results + 1.3
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    rrect(ctx, 0, 0, RW, RH, 22)
    ctx.clip()
    if t < t_results:
        _layer(ctx, ("srch_home", RH), 0, 0, RW, RH, lambda c: _search_home(c, RW, RH), pad=0)
        cy0 = 140 + (RH - 140) * 0.26
        by = cy0 + 46
        nch = int(clamp((t - t_type) / char_dt + 1e-6, 0, n)) if t >= t_type else 0
        shown = query[:nch]
        adv = text(ctx, shown, 160, by + 64, 50, INK, "ui", "left") if shown else 0
        typing = t_type <= t < t_done + 0.1
        if typing or _frac(t / 1.0) < 0.6:
            ctx.rectangle(164 + adv, by + 22, 4, 52)
            _fill(ctx, INK)
        # the Enter press: box glows
        ek = seg(t, t_done + 0.08, t_done + 0.3)
        if 0 < ek < 1:
            rrect(ctx, 80, by, RW - 160, 92, 46)
            _stroke(ctx, "#18a99f", 6, 1 - ek)
    elif t < t_site:
        rv = ease_out(seg(t, t_results, t_results + 0.4))
        ctx.save()
        ctx.rectangle(0, 0, RW, 140 + (RH - 140) * rv)
        ctx.clip()
        _layer(ctx, ("srch_res", RH, query), 0, 0, RW, RH,
               lambda c: _search_results(c, RW, RH, query), pad=0)
        ctx.restore()
        if rv < 1:
            ctx.rectangle(0, 140 + (RH - 140) * rv, RW, RH)
            _fill(ctx, UI_BG)
        # mouse to the first result and click
        top, sp, _ = _result_rows(RH)
        tx, ty = 250, top + 24
        mk = ease_in_out(seg(t, t_results + 0.35, t_results + 0.85))
        mx, my = lerp(RW * 0.78, tx, mk), lerp(RH * 0.9, ty, mk)
        ck = seg(t, t_results + 0.95, t_results + 1.25)
        if t >= t_results + 0.95:
            ctx.rectangle(40, top + 40, _tw(ctx, _RESULTS[0][0], "ui", 36), 3)
            _fill(ctx, LINK_BLUE)
        if 0 < ck < 1:
            circle(ctx, mx, my, 10 + 26 * ease_out(ck))
            _stroke(ctx, "#18a99f", 5, 1 - ck)
        _cursor(ctx, mx, my, 1.1)
    else:
        fk = seg(t, t_site, t_site + 0.2)
        if fk < 1:
            _layer(ctx, ("srch_res", RH, query), 0, 0, RW, RH,
                   lambda c: _search_results(c, RW, RH, query), pad=0)
        _layer(ctx, ("site", RH), 0, 0, RW, RH, lambda c: _site_page(c, RW, RH), a=fk, pad=0)
        # campus card slides up
        ck = ease_out_back(seg(t, t_site + 0.45, t_site + 0.85), 1.3)
        if ck > 0:
            _, _, cy, chh = _site_layout(RH)
            ctx.save()
            ctx.translate(0, (1 - ck) * (RH - cy + 30))
            _layer(ctx, ("site_card", RH), 0, cy - 4, RW, chh + 20,
                   lambda c: _site_card(c, RW, RH), pad=6)
            # pin drop
            pk = seg(t, t_site + 0.9, t_site + 1.35)
            if pk > 0:
                mh = chh - 28
                mw = min((RW - 60) * 0.4, mh * 1.6)
                px = 30 + 14 + mw * 0.5
                py = cy + 14 + mh * 0.42
                from_y = -90
                yy = py + from_y * (1 - _bounce(pk))
                ellipse(ctx, px, py, 12 * min(1, pk * 2), 4.5 * min(1, pk * 2))
                _fill(ctx, INK, 0.3)
                _pin(ctx, px, yy, 1.6)
            ctx.restore()
        # loading bar
        lk = seg(t, t_site, t_site + 0.45)
        if lk < 1:
            ctx.rectangle(0, 132, RW * ease_out(lk), 6)
            _fill(ctx, "#18a99f")
    ctx.restore()
    with saved(ctx, x, y, sc):
        rrect(ctx, 0, 0, RW, RH, 22)
        _stroke(ctx, INK, 5)


def _bounce(p):
    return ease_out_bounce(p)


# --- lab screen --------------------------------------------------------------
LAB_BG = "#0a1724"
LAB_LINE = "#2fd1c5"


def _catmull(pts, steps=6):
    """Sample a Catmull-Rom curve through pts."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts)):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(steps):
            u = k / steps
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * u
                                    + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u2
                                    + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * u3)
                             for d in (0, 1)))
    out.append(pts[-1])
    return out


def _tapered_curve(ctx, pts, w0, w1):
    """Closed outline of a curve through pts whose width tapers w0 -> w1."""
    sp = _catmull(pts)
    n = len(sp)
    left, right = [], []
    for i, (px, py) in enumerate(sp):
        qx, qy = sp[min(i + 1, n - 1)]
        rx, ry = sp[max(i - 1, 0)]
        dx, dy = qx - rx, qy - ry
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = lerp(w0, w1, i / (n - 1)) / 2
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    poly(ctx, left + right[::-1])


def _creature_silhouette(c, x, y, w, h, fill_c="#163a52", line_c="#7ff6ff", ow=4.0):
    """Sleek dog-sized creature in profile facing left (long fin ears swept
    back, slim legs, long S-curved tail), fitted in (x, y, w, h)."""
    s = min(w / 430.0, h / 270.0)
    ox = x + (w - 430 * s) / 2
    oy = y + (h - 270 * s) / 2
    c.save()
    c.translate(ox, oy)
    c.scale(s, s)

    def parts(cc):
        # body: deep chest, tucked waist, rounded rump
        smooth_path(cc, [(96, 132), (130, 112), (190, 110), (250, 118), (300, 112),
                         (338, 124), (350, 150), (334, 174), (296, 172), (250, 160),
                         (196, 168), (144, 182), (108, 170)], closed=True)
        # head with a slim snout
        smooth_path(cc, [(10, 128), (34, 108), (70, 92), (104, 96), (124, 118),
                         (116, 142), (86, 152), (48, 146), (22, 138)], closed=True)
        # long fin ears swept back along the neck
        smooth_path(cc, [(74, 96), (122, 64), (196, 38), (252, 34), (206, 58),
                         (146, 90), (104, 108)], closed=True)
        smooth_path(cc, [(92, 100), (150, 82), (222, 70), (178, 94), (118, 112)],
                    closed=True)
        # slim legs with small paws
        for pts in (((116, 160), (124, 204), (118, 246)), ((150, 166), (154, 206), (160, 246)),
                    ((292, 160), (314, 200), (300, 246)), ((322, 158), (342, 200), (330, 246))):
            _tapered_curve(cc, pts, 30, 15)
            ellipse(cc, pts[-1][0] - 5, pts[-1][1] + 2, 15, 7)
        # long S-curved tail with a fin tip
        _tapered_curve(cc, [(336, 134), (372, 130), (398, 104), (400, 70), (388, 46),
                            (402, 26)], 26, 9)
        smooth_path(cc, [(394, 34), (414, 8), (428, 20), (412, 44)], closed=True)

    c.new_path()
    parts(c)
    _stroke(c, line_c, ow * 2 / s + 10 / s, 0.14, preserve=True)
    _stroke(c, line_c, ow * 2 / s, 1.0)
    parts(c)
    _fill(c, fill_c)
    # glowing eye slit
    ellipse(c, 62, 116, 10, 4, -0.2)
    _fill(c, PAL["power"])
    c.restore()


def _lab_layout(RW, RH):
    if RH <= RW * 0.85:
        return dict(port=False, sil=(24, 112, 420, RH - 136), col=468,
                    status_y=150, last_y=300, map=(468, 380, RW - 24 - 468, RH - 404))
    sil_h = (RH - 112) * 0.40
    y2 = 112 + sil_h + 24
    return dict(port=True, sil=(24, 112, RW - 48, sil_h), col=36, status_y=y2 + 30,
                last_y=y2 + 180, map=(36, y2 + 260, RW - 72, RH - (y2 + 260) - 24))


_MAP_PIPES = (((0.0, 0.3), (0.45, 0.3), (0.45, 0.75), (1.0, 0.75)),
              ((0.2, 0.0), (0.2, 1.0)),
              ((0.65, 0.0), (0.65, 0.5), (1.0, 0.5)),
              ((0.0, 0.88), (0.3, 0.88)))
_MAP_LINE7 = ((0.08, 0.55), (0.45, 0.55), (0.82, 0.55), (0.82, 0.18))


def _map_pts(pts, mx, my, mw, mh):
    return [(mx + 16 + u * (mw - 32), my + 16 + v * (mh - 32)) for u, v in pts]


def _lab_static(c, RW, RH):
    L = _lab_layout(RW, RH)
    rrect(c, 0, 0, RW, RH, 20)
    _fill(c, LAB_BG)
    # grid
    for gx in range(0, int(RW) + 1, 45):
        c.rectangle(gx, 0, 1.5, RH)
    for gy in range(0, int(RH) + 1, 45):
        c.rectangle(0, gy, RW, 1.5)
    _fill(c, LAB_LINE, 0.08)
    # header
    hs = _fit_size(c, "SPECIMEN ZERO", "ui", 66, RW - 72)
    text(c, "SPECIMEN ZERO", 36, 76, hs, "#ffffff", "ui", "left")
    text(c, "HUSHCORP · CONTAINMENT", RW - 30, 34, 19, "#6fb7c0", "mono", "right")
    c.rectangle(36, 92, RW - 72, 3)
    _fill(c, LAB_LINE, 0.6)
    # silhouette panel
    sx, sy, sw, sh = L["sil"]
    rrect(c, sx, sy, sw, sh, 14)
    _fill(c, "#0f2233", preserve=True)
    _stroke(c, LAB_LINE, 2, 0.5)
    for (cx, cy, dx, dy) in ((sx + 10, sy + 10, 1, 1), (sx + sw - 10, sy + 10, -1, 1),
                             (sx + 10, sy + sh - 10, 1, -1), (sx + sw - 10, sy + sh - 10, -1, -1)):
        c.move_to(cx, cy + dy * 26)
        c.line_to(cx, cy)
        c.line_to(cx + dx * 26, cy)
        _stroke(c, "#7ff6ff", 4)
    _creature_silhouette(c, sx + 20, sy + 18, sw - 40, sh - 50)
    text(c, "UNKNOWN · CLASS ?", sx + sw / 2, sy + sh - 14, 20, "#6fb7c0", "mono", "center")
    # text column
    col = L["col"]
    cw = RW - 24 - col
    text(c, "STATUS:", col, L["status_y"], 28, "#8fc3cc", "mono", "left")
    text(c, "LAST SEEN:", col, L["last_y"], 28, "#8fc3cc", "mono", "left")
    ls = _fit_size(c, "SEWER LINE 7", "ui", 50, cw)
    text(c, "SEWER LINE 7", col, L["last_y"] + 54, ls, "#ffffff", "ui", "left")
    # map
    mx, my, mw, mh = L["map"]
    if mh > 60:
        rrect(c, mx, my, mw, mh, 12)
        _fill(c, "#0f2233", preserve=True)
        _stroke(c, LAB_LINE, 2, 0.5)
        for pipe in _MAP_PIPES:
            pts = _map_pts(pipe, mx, my, mw, mh)
            poly(c, pts, closed=False)
            _stroke(c, "#2c5b6c", 7)
        pts = _map_pts(_MAP_LINE7, mx, my, mw, mh)
        poly(c, pts, closed=False)
        _stroke(c, PAL["warn"], 7)
        circle(c, pts[0][0], pts[0][1], 15)
        _fill(c, PAL["warn"])
        text(c, "7", pts[0][0], pts[0][1] + 7, 20, LAB_BG, "ui", "center")


def lab_screen(ctx, x, y, w, h, t, t_on, off=False):
    """HushCorp wall screen in rect (x, y, w, h) (designed at 900 px wide,
    landscape; a tall rect stacks vertically). Powers on at t_on (CRT open
    0.25 s). 'SPECIMEN ZERO', blinking red 'STATUS: ESCAPED' (1 s period),
    'LAST SEEN: SEWER LINE 7', creature silhouette with a scan bar, sewer map
    with a pulsing last-seen dot. off=True draws a dark glass before t_on."""
    RW = 900.0
    sc = w / RW
    RH = h / sc
    if t < t_on:
        if off:
            with saved(ctx, x, y, sc):
                rrect(ctx, 0, 0, RW, RH, 20)
                _fill(ctx, "#0b1118", preserve=True)
                _stroke(ctx, INK, 6)
        return
    tau = t - t_on
    L = _lab_layout(RW, RH)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    rrect(ctx, 0, 0, RW, RH, 20)
    _fill(ctx, "#05090d")
    ok = ease_out(seg(tau, 0.06, 0.28))
    if tau < 0.12:
        lw = RW * ease_out(seg(tau, 0, 0.1))
        ctx.rectangle(RW / 2 - lw / 2, RH / 2 - 3, lw, 6)
        _fill(ctx, "#dffcff")
    if ok > 0:
        ctx.save()
        hh = RH * ok
        ctx.rectangle(0, RH / 2 - hh / 2, RW, hh)
        ctx.clip()
        _layer(ctx, ("lab", RH), 0, 0, RW, RH, lambda c: _lab_static(c, RW, RH), pad=0)
        # status box (blinks: 0.6 s bright, 0.4 s dim, soft edges)
        col = L["col"]
        cw = RW - 24 - col
        bx, by, bw, bh = col, L["status_y"] + 16, min(cw, 420), 88
        ph = _frac(tau / 1.0)
        on = smoothstep(seg(ph, 0.0, 0.06)) * (1 - smoothstep(seg(ph, 0.6, 0.68)))
        rrect(ctx, bx, by, bw, bh, 12)
        _fill(ctx, mixc("#3a0b14", PAL["danger"], on), preserve=True)
        _stroke(ctx, PAL["danger"], 4)
        es = _fit_size(ctx, "ESCAPED", "ui", 62, bw - 30)
        text(ctx, "ESCAPED", bx + bw / 2, by + bh / 2 + es * 0.36, es,
             mixc(PAL["danger"], "#ffffff", on), "ui", "center")
        # scan bar over the silhouette
        sx, sy, sw, sh = L["sil"]
        u = _frac(tau / 2.4)
        yy = sy + 16 + (sh - 32) * u
        ctx.rectangle(sx + 6, yy - 3, sw - 12, 6)
        _fill(ctx, "#7ff6ff", 0.55 * math.sin(math.pi * u))
        # last-seen pulse on the map
        mx, my, mw, mh = L["map"]
        if mh > 60:
            end = _map_pts(_MAP_LINE7, mx, my, mw, mh)[-1]
            pk = _frac(tau / 1.2)
            circle(ctx, end[0], end[1], 10 + 26 * ease_out(pk))
            _stroke(ctx, PAL["danger"], 4, 1 - pk)
            circle(ctx, end[0], end[1], 10)
            _fill(ctx, PAL["danger"])
        ctx.restore()
    if tau < 0.4:
        rrect(ctx, 0, 0, RW, RH, 20)
        _fill(ctx, "#dffcff", 0.35 * (1 - seg(tau, 0.1, 0.4)))
    rrect(ctx, 0, 0, RW, RH, 20)
    _stroke(ctx, INK, 6)
    ctx.restore()


# --- tablet ------------------------------------------------------------------
def _fn_key(fn):
    """Stable cache key for a portrait callback (None -> the stand-in)."""
    if fn is None:
        return "standin"
    return (getattr(fn, "__module__", ""), getattr(fn, "__qualname__", repr(fn)), id(fn))


def _portrait(ctx, x, y, w, h, portrait_fn, bg="#cfe3ea"):
    """Clip to the frame and draw portrait_fn (or the stand-in)."""
    ctx.save()
    rrect(ctx, x, y, w, h, 10)
    _fill(ctx, bg, preserve=True)
    ctx.clip()
    side = min(w, h)
    fn = portrait_fn or standin_portrait
    fn(ctx, x + w / 2, y + h / 2 + side * 0.05, side / 300.0)
    ctx.restore()


def _tablet_layout(RW, RH):
    content_h = 420
    off = max(0.0, (RH - 64 - content_h) / 2)
    return 64 + off


def _tablet_static(c, RW, RH, portrait_fn):
    rrect(c, 0, 0, RW, RH, 18)
    _fill(c, "#eef5f7")
    c.save()
    rrect(c, 0, 0, RW, RH, 18)
    c.clip()
    c.rectangle(0, 0, RW, 64)
    _fill(c, "#123a44")
    c.restore()
    hush_logo(c, 34, 32, 0.42, wordmark=True, color=PAL["hush"], hole="#123a44",
              text_color="#ffffff", text_size=22)
    text(c, "DOSSIER", RW - 24, 41, 20, "#9fd6d0", "mono", "right")
    y0 = _tablet_layout(RW, RH)
    _portrait(c, 28, y0 + 22, 196, 210, portrait_fn)
    rrect(c, 28, y0 + 22, 196, 210, 10)
    _stroke(c, "#123a44", 4)
    fx = 250
    text(c, "SUBJECT:", fx, y0 + 62, 24, "#58707a", "mono", "left")
    ns = _fit_size(c, "TIREDNESS", "ui", 54, RW - fx - 22)
    text(c, "TIREDNESS", fx, y0 + 62 + ns * 1.02, ns, INK, "ui", "left")
    # redacted lines (we keep secrets...)
    for i, ww in enumerate((0.9, 0.62, 0.78)):
        rrect(c, fx, y0 + 150 + i * 28, (RW - fx - 24) * ww, 16, 3)
        _fill(c, "#1d2a33")
    c.rectangle(28, y0 + 256, RW - 56, 2.5)
    _fill(c, "#b7c9cf")
    text(c, "KNOWN ASSOCIATE:", 28, y0 + 298, 24, "#58707a", "mono", "left")


def _tablet_assoc(c, RW, RH):
    y0 = _tablet_layout(RW, RH)
    s2 = _fit_size(c, "EMBARRASSMENT", "ui", 46, RW - 28 - 100)
    text(c, "EMBARRASSMENT", 28, y0 + 298 + s2 * 1.15, s2, INK, "ui", "left")
    return 28 + _tw(c, "EMBARRASSMENT", "ui", s2), y0 + 298 + s2 * 1.15


def tablet_screen(ctx, x, y, w, h, t, portrait_fn=None, t_on=None, t_check=None,
                  glow=True, bezel=True, portrait_key=None):
    """The Boss's dossier tablet in rect (x, y, w, h) (designed at 600 px
    wide): 'SUBJECT: TIREDNESS' with a portrait frame, redacted lines,
    'KNOWN ASSOCIATE: EMBARRASSMENT' and a drawn check mark. t_on None =
    already on; else wakes at t_on, check draws at t_check (t_on + 0.75).
    The screen (incl. the portrait) is cached: pass a module-level
    portrait_fn (or a stable portrait_key) so the cache key stays fixed."""
    RW = 600.0
    sc = w / RW
    RH = h / sc
    if t_on is not None and t < t_on:
        return
    tau = 99.0 if t_on is None else t - t_on
    if t_check is None:
        t_check = (t_on if t_on is not None else -99.0) + 0.75
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    if bezel:
        rrect(ctx, -22, -22, RW + 44, RH + 44, 34)
        _fill(ctx, "#20232c", preserve=True)
        _stroke(ctx, INK, 6)
    wake = ease_out(seg(tau, 0, 0.25))
    if glow:
        for i, (o, a) in enumerate(((34, 0.06), (20, 0.1), (8, 0.16))):
            rrect(ctx, -o, -o, RW + 2 * o, RH + 2 * o, 18 + o)
            _stroke(ctx, "#bdf4ff", 14, a * wake)
    key = ("tablet", RH, _fn_key(portrait_fn) if portrait_key is None else portrait_key)
    rrect(ctx, 0, 0, RW, RH, 18)
    _fill(ctx, "#0b1418")
    _layer(ctx, key, 0, 0, RW, RH, lambda c: _tablet_static(c, RW, RH, portrait_fn),
           a=wake, pad=0)
    ak = ease_out(seg(tau, 0.4, 0.6))
    if ak > 0:
        y0 = _tablet_layout(RW, RH)
        ex = [0.0, 0.0]

        def draw_assoc(c):
            ex[0], ex[1] = _tablet_assoc(c, RW, RH)
        _layer(ctx, ("tablet_assoc", RH), 0, y0 + 300, RW, 90, draw_assoc, a=ak, pad=4)
        s2 = _fit_size(ctx, "EMBARRASSMENT", "ui", 46, RW - 28 - 100)
        bx = 28 + _tw(ctx, "EMBARRASSMENT", "ui", s2) + 20
        by = y0 + 298 + s2 * 1.15 - 46
        bs = 54
        rrect(ctx, bx, by, bs, bs, 10)
        _fill(ctx, "#ffffff", ak, preserve=True)
        _stroke(ctx, "#0f8f86", 4, ak)
        ck = seg(t, t_check, t_check + 0.25)
        if ck > 0:
            pk = 1 + 0.25 * math.sin(math.pi * seg(t, t_check + 0.2, t_check + 0.45))
            with saved(ctx, bx + bs / 2, by + bs / 2, pk):
                if _check_path(ctx, -bs * 0.5 + 4, -bs * 0.62, bs * 1.1, ck):
                    _stroke(ctx, INK, 15)
                if _check_path(ctx, -bs * 0.5 + 4, -bs * 0.62, bs * 1.1, ck):
                    _stroke(ctx, "#13b5a8", 8)
    ctx.restore()


# --- hologram photo -------------------------------------------------------------
_FLICK = (0.0, 0.75, 0.1, 0.95, 0.35, 0.85, 0.55, 1.0)


def hologram_photo(ctx, x, y, w, h, t, t_on, portrait_fn=None, label="SUBJECT: TIREDNESS",
                   color=HOLO, cache_key="auto"):
    """Photo of Tiredness flickering on (8 frames) onto a glass wall in rect
    (x, y, w, h) (designed at 500 px wide): cool cyan-white tint, static
    scanlines, corner brackets, a soft glow and a mono label. The tinted
    photo is cached under cache_key ('auto' = derived from portrait_fn);
    pass cache_key=None if portrait_fn animates (redrawn each frame)."""
    if t < t_on:
        return
    RW = 500.0
    sc = w / RW
    RH = h / sc
    f = int(math.floor((t - t_on) * FPS + 1e-4))
    a = _FLICK[f] if f < len(_FLICK) else 1.0
    if a <= 0.01:
        return
    glitch = f in (1, 3, 5)
    lab_h = 50 if label else 0
    px, py, pw, ph = 22, 22, RW - 44, RH - 44 - lab_h

    def draw_photo(c):
        rrect(c, px, py, pw, ph, 8)
        c.save()
        c.clip()
        _portrait(c, px, py, pw, ph, portrait_fn, bg="#c4f3ff")
        # tint
        c.set_operator(cairo.OPERATOR_HSL_COLOR)
        c.rectangle(px, py, pw, ph)
        _fill(c, "#7fe9ff", 0.9)
        c.set_operator(cairo.OPERATOR_OVER)
        c.rectangle(px, py, pw, ph)
        _fill(c, "#effeff", 0.4)
        # scanlines (static)
        for yy in range(int(py), int(py + ph), 7):
            c.rectangle(px, yy, pw, 2.5)
        _fill(c, "#0b3a4a", 0.22)
        c.restore()
        rrect(c, px, py, pw, ph, 8)
        _stroke(c, color, 2.5, 0.7)

    def draw_frame(c):
        rrect(c, 0, 0, RW, RH, 14)
        _fill(c, "#0b2a36", 0.62)
        for o, al in ((16, 0.06), (8, 0.1)):
            rrect(c, -o, -o, RW + 2 * o, RH + 2 * o, 14 + o)
            _stroke(c, color, 10, al)
        L = 40
        for (cx, cy, dx, dy) in ((4, 4, 1, 1), (RW - 4, 4, -1, 1), (4, RH - 4, 1, -1),
                                 (RW - 4, RH - 4, -1, -1)):
            c.move_to(cx, cy + dy * L)
            c.line_to(cx, cy)
            c.line_to(cx + dx * L, cy)
            _stroke(c, color, 5)
        if label:
            ls = _fit_size(c, label, "mono", 30, RW - 60)
            text(c, label, RW / 2, RH - 20, ls, color, "mono", "center")

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    _layer(ctx, ("holo_frame", RH, label, str(color)), -30, -30, RW + 60, RH + 60, draw_frame,
           a=a)
    if cache_key is not None:
        pkey = ("holo_photo", RH, _fn_key(portrait_fn) if cache_key == "auto" else cache_key,
                str(color))
        if glitch:
            band = (py + ph * 0.3, ph * 0.22)
            ctx.save()
            ctx.rectangle(0, 0, RW, band[0])
            ctx.rectangle(0, band[0] + band[1], RW, RH)
            ctx.clip()
            _layer(ctx, pkey, px, py, pw, ph, draw_photo, a=a * 0.9)
            ctx.restore()
            ctx.save()
            ctx.rectangle(0, band[0], RW, band[1])
            ctx.clip()
            ctx.translate(16, 0)
            _layer(ctx, pkey, px, py, pw, ph, draw_photo, a=a * 0.9)
            ctx.restore()
        else:
            _layer(ctx, pkey, px, py, pw, ph, draw_photo, a=a * 0.9)
    else:
        ctx.push_group()
        draw_photo(ctx)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a * 0.82)
    ctx.restore()


# --- label card -------------------------------------------------------------
def label_card(ctx, x, y, text_, t, t_in, color="hush", t_out=None, sub=None, size=52,
               style="plate", max_w=820, rot=-0.025):
    """Readable sign/label centred at (x, y) popping in at t_in (0.3 s
    overshoot), popping out over 0.2 s at t_out (if given). style 'plate'
    (cream plate, coloured stripe) or 'hazard' (yellow/ink stripes header)."""
    if t < t_in or (t_out is not None and t > t_out + 0.2):
        return
    k = ease_out_back(seg(t, t_in, t_in + 0.3), 2.0)
    if t_out is not None:
        k *= 1 - ease_in(seg(t, t_out, t_out + 0.2))
    if k < 0.02:
        return
    lines = text_.split("\n")
    fs = size
    for _ in range(3):
        mw = max(_tw(ctx, l, "black", fs) for l in lines)
        if mw <= max_w - 70:
            break
        fs *= (max_w - 70) / mw
    ss = size * 0.64
    if sub:
        ss = min(ss, (max_w - 70) / max(1.0, _tw(ctx, sub, "ui", ss)) * ss)
        sw = _tw(ctx, sub, "ui", ss)
    else:
        sw = 0
    mw = max(max(_tw(ctx, l, "black", fs) for l in lines), sw)
    stripe = 30 if style == "hazard" else 0
    pw = mw + 64 + (14 if style == "plate" else 0)
    lh = fs * 1.12
    ph = 30 + len(lines) * lh + (ss * 1.4 if sub else 0) + stripe + 16
    x0, y0 = -pw / 2, -ph / 2

    def draw(c):
        rrect(c, x0 + 7, y0 + 9, pw, ph, 16)
        _fill(c, INK, 0.45)
        rrect(c, x0, y0, pw, ph, 16)
        _fill(c, "#fbf8f1", preserve=True)
        c.save()
        c.clip()
        if style == "hazard":
            c.rectangle(x0, y0, pw, stripe)
            _fill(c, PAL["warn"])
            for i in range(int(pw / 30) + 2):
                xx = x0 + i * 30
                poly(c, [(xx, y0 + stripe), (xx + 14, y0 + stripe), (xx + 28, y0),
                         (xx + 14, y0)])
            _fill(c, INK)
            c.rectangle(x0, y0 + stripe, pw, 3.5)
            _fill(c, INK)
        else:
            c.rectangle(x0, y0, 16, ph)
            _fill(c, color)
        c.restore()
        rrect(c, x0, y0, pw, ph, 16)
        _stroke(c, INK, 6)
        cx = (x0 + 14 + x0 + pw) / 2 if style == "plate" else 0
        yy = y0 + stripe + 18 + fs * 0.9
        for l in lines:
            text(c, l, cx, yy, fs, INK, "black", "center")
            yy += lh
        if sub:
            text(c, sub, cx, yy - lh + fs * 0.25 + ss * 1.25, ss, "#4a4458", "ui", "center")
    q = _qscale(ctx, 1.15)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot + (1 - k) * 0.12)
    ctx.scale(k, k)
    _layer(ctx, ("label", text_, sub, round(size, 1), str(color), style, round(max_w)),
           x0 - 4, y0 - 4, pw + 18, ph + 20, draw, q=q)
    ctx.restore()


# ----------------------------------------------------------------------------
# 5. Titles
# ----------------------------------------------------------------------------
END_FILL = "#aebcff"
END_SHADE = "#7d8fe6"


def _end_letter(c, ch, size):
    set_font(c, "title", size)
    # dark halo for busy backgrounds
    c.move_to(0, 0)
    c.text_path(ch)
    _stroke(c, INK, size * 0.24, 0.24, preserve=True)
    c.new_path()
    # hard drop shadow
    c.move_to(0, size * 0.08)
    c.text_path(ch)
    _stroke(c, INK, size * 0.11, preserve=True)
    _fill(c, INK)
    c.move_to(0, 0)
    c.text_path(ch)
    _stroke(c, INK, size * 0.11, preserve=True)
    c.save()
    _fill(c, END_FILL, preserve=True)
    c.clip()
    c.rectangle(-size, -size * 0.30, size * 3, size)
    _fill(c, END_SHADE)
    c.rectangle(-size, -size * 0.66, size * 3, size * 0.05)
    _fill(c, "#ffffff", 0.55)
    c.restore()
    c.new_path()


def _end_layout(ctx, title, size, max_w=840):
    adv = [_tw(ctx, ch, "title", size) for ch in title]
    track = -size * 0.015
    total = sum(adv) + track * (len(title) - 1)
    if total > max_w:
        f = max_w / total
        size *= f
        adv = [a * f for a in adv]
        track *= f
        total = max_w
    return size, adv, track, total


def _end_pose(i, n, sag, size):
    """(dy, rot, squash) of letter i for a given sag 0..1: the word nods
    off -- later letters sink and tip forward, the last one most."""
    u = i / max(1, n - 1)
    depth = 34.0 * size / 150
    dy = sag * depth * (0.25 * math.sin(math.pi * u) + 1.1 * u * u)
    rot = sag * (0.17 * u ** 2.2 + 0.035 * (hash01(i, 4) - 0.5))
    if i == n - 1:
        rot += 0.09 * sag
        dy += 4 * sag * size / 150
    return dy, rot, 1 - 0.07 * sag * u


def _end_letters(ctx, title, cx, baseline, size, adv, track, total, tau, sag, q, a=1.0):
    """Draw the title letters; returns the top of the last letter."""
    n = len(title)
    xx = cx - total / 2
    last_top = None
    for i, ch in enumerate(title):
        k = ease_out_back(seg(tau, i * 0.045, i * 0.045 + 0.32), 2.2)
        if k >= 0.02:
            dy, rot, sq = _end_pose(i, n, sag, size)
            lx = xx + adv[i] / 2
            ctx.save()
            ctx.translate(lx, baseline + dy - (1 - k) * 30)
            if rot:
                ctx.rotate(rot)
            ctx.scale(k, k * sq)
            e = _ext(ctx, ch, "title", size)
            m = size * 0.17
            _layer(ctx, ("endL", ch, round(size, 1)), -adv[i] / 2 + e[0] - m, e[1] - m,
                   e[2] + 2 * m, e[3] + 2 * m + size * 0.1,
                   lambda c, ch=ch, a_=adv[i]: (c.translate(-a_ / 2, 0), _end_letter(c, ch, size)),
                   a=a, q=q)
            ctx.restore()
            if i == n - 1:
                hgt = size * 0.72 * sq
                last_top = (lx + adv[i] * 0.3 + math.sin(rot) * hgt,
                            baseline + dy - math.cos(rot) * hgt)
        xx += adv[i] + track
    return last_top


END_SAG_STEPS = 14


def end_card(ctx, t, t0, title="TIREDNESS", cx=468, baseline=730, size=168, t_tbc=None,
             tbc="to be continued\u2026", t_out=None):
    """End title (screen space). Letters pop in staggered (0-0.7 s), then the
    word nods off -- later letters sink and tip forward (0.75-1.75 s); a
    little 'z' drifts up off the last S (from +1.1 s, 1.6 s loop), and
    'to be continued...' fades in under it at t_tbc (default t0 + 1.5).
    Title ~840 px wide, letters ~130 px tall; occupies x ~50-930,
    y ~480-890 (z's included). Holds
    until the caller stops; optional 0.4 s fade-out from t_out."""
    if t < t0:
        return
    if t_out is not None and t > t_out + 0.4:
        return
    fade = 1.0 if t_out is None else 1 - smoothstep(seg(t, t_out, t_out + 0.4))
    tau = t - t0
    n = len(title)
    size, adv, track, total = _end_layout(ctx, title, size)
    pop_end = (n - 1) * 0.045 + 0.32
    sag = ease_in_out(seg(tau, 0.75, 1.75))
    if tau < pop_end:
        last_top = _end_letters(ctx, title, cx, baseline, size, adv, track, total, tau, 0.0,
                                _qscale(ctx, 1.2), fade)
    else:
        # settled/sagging: compose the whole word once per sag step and blit
        sq_ = round(sag * END_SAG_STEPS) / END_SAG_STEPS
        m = size * 0.6
        x0, y0 = cx - total / 2 - m, baseline - size - m
        lw, lh = total + 2 * m, size * 1.5 + 2 * m
        holder = [None]

        def draw(c):
            holder[0] = _end_letters(c, title, cx, baseline, size, adv, track, total, 99.0,
                                     sq_, None)
        _layer(ctx, ("endT", title, round(size, 1), cx, baseline, sq_), x0, y0, lw, lh, draw,
               a=fade, pad=0, exact=True)
        dy, rot, sq = _end_pose(n - 1, n, sq_, size)
        hgt = size * 0.72 * sq
        lx = cx + total / 2 - adv[-1] / 2
        last_top = (lx + adv[-1] * 0.3 + math.sin(rot) * hgt, baseline + dy - math.cos(rot) * hgt)
    # little z's drifting up off the last letter (kept inside x < 930)
    if last_top and tau > 1.1:
        for j in range(3):
            ph = (tau - 1.1) / 1.6 - j / 3
            if ph < 0:
                continue
            ph = _frac(ph)
            zx = last_top[0] + (2 + 22 * ph) * size / 150 + 7 * math.sin(TAU * ph)
            zy = last_top[1] - (14 + 140 * ph) * size / 150
            zs = (22 + 26 * ph) * size / 150
            a = smoothstep(seg(ph, 0, 0.15)) * (1 - smoothstep(seg(ph, 0.6, 1.0))) * fade
            if a < 0.03:
                continue
            _z_path(ctx, zx, zy, zs, -0.2)
            _stroke(ctx, INK, zs * 0.22, a, preserve=True)
            _fill(ctx, "#ffffff", a)
    # to be continued...
    t_tbc = t0 + 1.5 if t_tbc is None else t_tbc
    tk = smoothstep(seg(t, t_tbc, t_tbc + 0.6))
    if tk > 0.01:
        ts = 54 * size / 150

        def draw_tbc(c):
            text(c, tbc, cx, baseline + size * 0.82, ts, "#ffffff", "round", "center",
                 outline=INK, outline_w=ts * 0.2, shadow=(0, ts * 0.08, INK))
        tw_ = _tw(ctx, tbc, "round", ts)
        ctx.save()
        ctx.translate(0, round((1 - tk) * 12))
        _layer(ctx, ("tbc", tbc, round(ts, 1), cx, baseline), cx - tw_ / 2 - 20,
               baseline + size * 0.82 - ts * 1.1, tw_ + 40, ts * 1.6, draw_tbc, a=tk * fade,
               exact=True)
        ctx.restore()
