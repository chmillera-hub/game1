"""Backgrounds / locations for TIREDNESS (documented in API_sets.md).

Every set is drawn in WORLD coordinates. Frame it with
    with core.camera(ctx, cx, cy, zoom):
        sets.bedroom(ctx, t, layer="bg", **state)
        ...characters...
        sets.bedroom(ctx, t, layer="fg", **state)

Static parts are rendered once into core.cached() bitmaps (tiled when the
bitmap would get huge at high zoom, and only visible tiles are blitted).
Only small sparse details are drawn live per frame (doors, chair, game
screen, a few drips / motes / shimmer lines, alarm wash).

Each set has a <NAME>_MARKS dict of stage marks (floor line, door, stand
points, screen rects, suggested camera framings...).
"""
import math
import cairocffi as cairo
from engine import core
from engine import props
from engine.core import PAL, hexc, mixc, clamp, lerp, hash01, noise1
from engine.props import fs, rect, ell, polyf, blob, line, curve, spaced_text, hush_logo

INK = PAL["ink"]
TAU = math.pi * 2

# ----------------------------------------------------------------------------
# set palette
# ----------------------------------------------------------------------------
C = {
    # bedroom (warm, cosy, afternoon)
    "bd_wall": "#b9c99a", "bd_wall_sh": "#97aa7c", "bd_stripe": "#c5d4a8",
    "bd_ceil": "#e8e2c8", "bd_ceil_sh": "#d3cba9",
    "wood": "#d29a63", "wood_sh": "#b07a46", "wood_dk": "#8f5c33", "wood_hi": "#e3b27f",
    "trim": "#f3ead6", "trim_sh": "#d8cbb0",
    "sun": "#ffe9a6",
    "blanket": "#8a6aa8", "blanket_sh": "#6b4f8a", "blanket_hi": "#a98bc6",
    "sheet": "#eef0fa", "sheet_sh": "#c9cde3",
    "curtain": "#e8846a", "curtain_sh": "#c8644e",
    "desk": "#4a4560", "desk_sh": "#353147", "desk_top": "#5d5878",
    "chair": "#8a5cd6", "chair_sh": "#6a41b0", "chair_shell": "#2f2b3d",
    "rug": "#8a9bd0", "rug_sh": "#7183bd", "rug_rim": "#f3ead6",
    "sky": "#9fd8f7", "sky_hi": "#c9ecff", "cloud": "#ffffff",
    "grass": "#7cc96a", "grass_sh": "#5eaa52", "leaf": "#4f9a4e", "leaf_sh": "#3d7d40",
    "bark": "#8a6a4a", "road": "#8a8796", "road_sh": "#76738a",
    # living room / hallway (warm, slightly dim)
    "lv_wall": "#a4a7cf", "lv_wall_sh": "#8a8db8", "lv_paper": "#b2b5d9",
    "lv_wain": "#efe2c8", "lv_wain_sh": "#d6c6a6",
    "couch": "#a8505f", "couch_sh": "#87384a", "couch_hi": "#c26e7b",
    "petbed": "#5f86c4", "petbed_sh": "#4a6aa3", "petbed_rim": "#f3e6cf",
    "counter": "#f1ead8", "counter_top": "#7a6a8a", "cab": "#7fa58f", "cab_sh": "#638a74",
    # house exterior
    "siding": "#f3d892", "siding_sh": "#d9b56e", "siding_line": "#dcbb74",
    "house_trim": "#fbf7ee", "roof": "#5d6390", "roof_sh": "#474c78",
    "door_red": "#c0453f", "door_red_sh": "#9a3330",
    "fence": "#fbf7ee", "fence_sh": "#d7d3cc",
    "walk": "#d9d2c3", "walk_sh": "#bfb6a4",
    # hushcorp
    "hc_wall": "#e9eff4", "hc_wall_sh": "#cdd7e0", "hc_floor": "#d5dee6", "hc_floor_sh": "#b9c6d2",
    "hc_steel": "#9aa8b6", "hc_steel_dk": "#6f7f90", "hc_slate": "#3b4757", "hc_glass": "#bcd6e4",
    "hc_glass_dk": "#8fb2c6", "hc_white": "#f7fafc",
    # sewer (deep teal-green, readable)
    "sw_brick": "#3f6e66", "sw_brick_sh": "#2f5850", "sw_mortar": "#2a4c46", "sw_dark": "#173430",
    "sw_walk": "#5b7f73", "sw_walk_sh": "#466a5f", "sw_water": "#24585a", "sw_water_hi": "#7fbfae",
    "sw_pipe": "#6f8a7e", "sw_pipe_sh": "#56705f", "sw_moss": "#6e9a4a",
    # dusk
    "dusk_top": "#3a2a6e", "dusk_mid": "#a2508a", "dusk_low": "#f2a65a",
    "city": "#3a3466", "city_sh": "#2a2650", "city_win": "#ffd27a",
}


# ----------------------------------------------------------------------------
# infrastructure
# ----------------------------------------------------------------------------
def _qscale(ctx):
    m = ctx.get_matrix()
    sc = math.hypot(m.xx, m.yx)
    if sc <= 0:
        return 0.0
    return 2 ** (math.ceil(math.log2(sc) * 8 - 1e-6) / 8)


def view_rect(ctx):
    """Visible region (x0, y0, x1, y1) in current user coordinates."""
    return ctx.clip_extents()


def _visible(ctx, x0, y0, w, h):
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    return not (vx1 <= x0 or vx0 >= x0 + w or vy1 <= y0 or vy0 >= y0 + h)


MAX_LAYER_MP = 12.0  # above this many megapixels a static layer is tiled


def static_layer(ctx, key, x0, y0, w, h, draw_fn, max_mp=None, tile_px=2040):
    """core.cached() wrapper: one bitmap when small, visible tiles when big.

    Tiles are ~tile_px bitmaps; they overlap by core's pad, so use this
    for OPAQUE layers (small translucent layers go through cached_or_live).
    """
    if not _visible(ctx, x0, y0, w, h):
        return
    q = _qscale(ctx)
    if q <= 0:
        return
    if w * h * q * q <= (MAX_LAYER_MP if max_mp is None else max_mp) * 1e6:
        core.cached(ctx, key, x0, y0, w, h, draw_fn)
        return
    T = max(160, int(tile_px / q) // 32 * 32)
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    nx, ny = int(math.ceil(w / T)), int(math.ceil(h / T))
    for j in range(ny):
        ty = y0 + j * T
        th = min(T, y0 + h - ty)
        if ty + th <= vy0 or ty >= vy1:
            continue
        for i in range(nx):
            tx = x0 + i * T
            tw = min(T, x0 + w - tx)
            if tx + tw <= vx0 or tx >= vx1:
                continue
            core.cached(ctx, (key, "tile", i, j, T), tx, ty, tw, th, draw_fn)


def cached_or_live(ctx, key, x0, y0, w, h, draw_fn):
    """core.cached() for translucent overlays; draws live instead when the
    bitmap would exceed MAX_LAYER_MP (extreme close-ups), so memory stays bounded."""
    if not _visible(ctx, x0, y0, w, h):
        return
    q = _qscale(ctx)
    if w * h * q * q > MAX_LAYER_MP * 1e6:
        draw_fn(ctx)
    else:
        core.cached(ctx, key, x0, y0, w, h, draw_fn)


def _overscan(ctx, x0, y0, x1, y1, top, bottom, left=None, right=None):
    """Flat fills outside the drawn rect (x0, y0)-(x1, y1) so extreme framings
    never show void. Colours may be None to skip a side."""
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    if vy0 < y0 and top:
        ctx.rectangle(vx0 - 2, vy0 - 2, vx1 - vx0 + 4, y0 - vy0 + 3)
        core.fill(ctx, top)
    if vy1 > y1 and bottom:
        ctx.rectangle(vx0 - 2, y1 - 1, vx1 - vx0 + 4, vy1 - y1 + 3)
        core.fill(ctx, bottom)
    if vx0 < x0 and left:
        ctx.rectangle(vx0 - 2, y0, x0 - vx0 + 3, y1 - y0)
        core.fill(ctx, left)
    if vx1 > x1 and right:
        ctx.rectangle(x1 - 1, y0, vx1 - x1 + 3, y1 - y0)
        core.fill(ctx, right)


def _jit(i, seed, amt):
    return (hash01(i, seed) - 0.5) * 2 * amt


def wonky_rect(ctx, x, y, w, h, fc, lw=4, seed=0, amt=4, sc=INK):
    """Slightly hand-made quad (corners nudged by +-amt)."""
    pts = [(x + _jit(1, seed, amt), y + _jit(2, seed, amt)),
           (x + w + _jit(3, seed, amt), y + _jit(4, seed, amt)),
           (x + w + _jit(5, seed, amt), y + h + _jit(6, seed, amt)),
           (x + _jit(7, seed, amt), y + h + _jit(8, seed, amt))]
    polyf(ctx, pts, fc, lw, sc)
    return pts


def _persp(px, py, vp, D, d):
    """Project wall-plane point (px, py) pulled toward the camera by d (d<0 = away)."""
    f = D / (D - d)
    return (vp[0] + (px - vp[0]) * f, vp[1] + (py - vp[1]) * f)


def door_quad(hinge_x, top, bottom, width, opening, vp, D=2600.0, toward=True, hinge_left=True):
    """4 points of a swinging door panel. opening 0..1 (0 = shut, 1 = 95 deg).

    toward=True swings toward the viewer (door opens into the room we see),
    False swings away (we look at it from the other side).
    Returns [hinge_top, free_top, free_bottom, hinge_bottom].
    """
    a = clamp(opening) * math.radians(95)
    sgn = 1 if hinge_left else -1
    fx = hinge_x + sgn * width * math.cos(a)
    d = width * math.sin(a) * (1 if toward else -1)
    ft = _persp(fx, top, vp, D, d)
    fb = _persp(fx, bottom, vp, D, d)
    return [(hinge_x, top), ft, fb, (hinge_x, bottom)]


def _glow(ctx, x, y, r, c, a):
    core.radial_glow(ctx, x, y, r, c, a)


def _sun_patch(ctx, pts, a=0.42, col=None):
    core.poly(ctx, pts)
    core.fill(ctx, core.alpha(col or C["sun"], a))


def _plant(ctx, x, y, s=1.0, pot="#d9734f", leafc=None, seed=0):
    """Little potted plant, ANCHOR = pot bottom centre."""
    leafc = leafc or C["leaf"]
    with core.saved(ctx, x, y, s):
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.45 + _jit(k, seed, 0.1)
            L = 70 + 25 * hash01(k, seed + 2)
            tip = (math.cos(a) * L, -60 + math.sin(a) * L)
            blob(ctx, [(0, -60), (tip[0] * 0.5 - 12, tip[1] * 0.5 - 30), tip,
                       (tip[0] * 0.5 + 12, tip[1] * 0.5 - 24)], leafc, 3.5)
        polyf(ctx, [(-38, -64), (38, -64), (30, 0), (-30, 0)], pot, 4)
        rect(ctx, -44, -76, 88, 18, mixc(pot, "#ffffff", 0.15), 4, r=5)


def _book_row(ctx, x, y, n, seed=0, h=70):
    cols = ["#e8846a", "#5f86c4", "#f2c14e", "#8a6aa8", "#7cc96a", "#f3ead6", "#c0453f"]
    xx = x
    for i in range(n):
        w = 18 + 10 * hash01(i, seed)
        hh = h * (0.75 + 0.25 * hash01(i, seed + 1))
        tilt = 0.0 if hash01(i, seed + 3) > 0.15 else 0.18
        with core.saved(ctx, xx, y, 1.0, tilt):
            rect(ctx, 0, -hh, w, hh, cols[int(hash01(i, seed + 2) * len(cols))], 3, r=2)
            line(ctx, [(4, -hh + 12), (w - 4, -hh + 12)], (1, 1, 1, 0.5), 2.5)
        xx += w + 2
    return xx


def _cloud(ctx, x, y, s=1.0, c="#ffffff", lw=0, sc=INK):
    with core.saved(ctx, x, y, s):
        core.circle(ctx, -60, 10, 42); core.circle(ctx, 0, -10, 58); core.circle(ctx, 62, 8, 44)
        core.rrect(ctx, -100, 0, 200, 52, 26)
        core.fill(ctx, c)


def _tree(ctx, x, y, s=1.0, seed=0, leafc=None, leaf_sh=None, lw=4):
    """Round cartoon tree. ANCHOR = trunk base."""
    leafc, leaf_sh = leafc or C["leaf"], leaf_sh or C["leaf_sh"]
    with core.saved(ctx, x, y, s):
        polyf(ctx, [(-26, 0), (26, 0), (16, -260), (-16, -260)], C["bark"], lw)
        line(ctx, [(0, -150), (50, -230)], INK, 22)
        line(ctx, [(0, -150), (50, -230)], C["bark"], 12)
        pts = []
        n = 11
        for i in range(n):
            a = i / n * TAU
            r = 190 * (1 + 0.12 * (hash01(i, seed) - 0.5))
            pts.append((math.cos(a) * r * 1.05, -380 + math.sin(a) * r * 0.9))
        blob(ctx, pts, leafc, lw)
        blob(ctx, [(p[0] * 0.75 + 30, p[1] * 0.0 - 330 + (p[1] + 380) * 0.55) for p in pts],
             leaf_sh, 0)
        for i in range(5):
            a = i * 1.3 + seed
            core.circle(ctx, math.cos(a) * 110, -400 + math.sin(a) * 90, 20)
        core.fill(ctx, mixc(leafc, "#ffffff", 0.15))


def _house_far(ctx, x, y, w, h, wall, roof, seed=0, lw=4, door=True):
    """Simple distant house. ANCHOR = bottom-left (x, y)."""
    rect(ctx, x, y - h, w, h, wall, lw)
    polyf(ctx, [(x - 20, y - h), (x + w / 2, y - h - h * 0.55), (x + w + 20, y - h)], roof, lw)
    ww = w * 0.2
    for k in range(2):
        wx = x + w * (0.18 + k * 0.45)
        rect(ctx, wx, y - h * 0.75, ww, h * 0.28, "#cfe8f5", lw * 0.8)
        line(ctx, [(wx + ww / 2, y - h * 0.75), (wx + ww / 2, y - h * 0.47)], INK, lw * 0.6)
    if door:
        rect(ctx, x + w * 0.42, y - h * 0.42, w * 0.16, h * 0.42, mixc(roof, "#000000", 0.1), lw * 0.8)


def _alarm(ctx, t, alarm, beacons=(), W=1080, H=1920, wash=0.32):
    """Red alarm wash (moderate, ~1.2 Hz pulse, never strobing) + rotating beacons.

    beacons: list of (x, y) lamp positions in world coords.
    """
    if alarm <= 0.001:
        return
    p = 0.5 + 0.5 * math.sin(t * TAU * 0.8)
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
    core.fill(ctx, core.alpha("#ff2a3c", alarm * (wash * 0.55 + wash * 0.45 * p)))
    for i, (bx, by) in enumerate(beacons):
        a = t * 3.2 + i * 1.7
        for k in (0, math.pi):
            aa = a + k
            ctx.move_to(bx, by)
            ctx.arc(bx, by, 900, aa - 0.16, aa + 0.16)
            ctx.close_path()
            core.fill(ctx, core.alpha("#ff6070", 0.16 * alarm))
        ell(ctx, bx, by, 26, 20, mixc("#7a1020", "#ff3b5c", 0.5 + 0.5 * p), 4)
        core.radial_glow(ctx, bx, by, 90, "#ff3b5c", 0.5 * alarm * (0.6 + 0.4 * p))


# ============================================================================
# 1. BEDROOM
# ============================================================================
BEDROOM_W, BEDROOM_H = 2400, 1920
_BD_CEIL, _BD_FLOOR = 300, 1330
_BD_VP = (1200, 860)
_BD_DOOR = (110, 505, 400, 825)        # x, top, w, h (bottom = floor)
_BD_CLOSET = (590, 560, 410, 770)
_BD_WIN = (1100, 470, 400, 410)
_BD_MON = (1832, 800, 248, 218, -10)   # screen origin x, y, width, height, top-edge rise
_BD_CHAIR = (1625, 1590)               # chair floor point (centre of base)

BEDROOM_MARKS = {
    "size": (BEDROOM_W, BEDROOM_H),
    "char_scale": 0.75,
    "ceiling_y": _BD_CEIL,
    "floor_y": _BD_FLOOR,           # where back wall meets floor
    "stand_y": 1520,                # feet line for people in the room (front of furniture)
    "door": _BD_DOOR,               # x, y_top, w, h of the doorway opening
    "door_hinge_x": 110,
    "door_knob": (468, 960),
    "doorway_feet": (312, 1334),    # feet of someone standing in the doorway
    "hall_feet": (312, 1300),       # feet of someone in the hallway, seen through door
    "closet": _BD_CLOSET,
    "closet_open_rect": (590, 560, 205, 770),   # half revealed by closet_open
    "closet_rummage_feet": (700, 1530),
    "bed": (1030, 1120, 560, 340),
    "under_bed_head": (1300, 1415),  # head point for a character crouched under the bed
    "under_bed_feet": (1300, 1560),
    "laundry": (1000, 1585),        # pile base centre
    "laundry_hands": (1000, 1450),  # where hands grab to lift it
    "window": _BD_WIN,
    "picture_nail": (1668, 752),
    "picture_floor": (1560, 1560),  # where the fallen frame lies
    "shelf_figurine": (2020, 642),
    "ceiling_light": (1440, 268),
    "desk": (1700, 1100, 640, 350),
    "desk_top_y": 1104,             # surface objects rest on (front half)
    "keyboard": (1878, 1104),
    "desk_critter": (1985, 1100),   # where the thing sits grooming
    "sweater_spot": (1985, 1104),
    "monitor_quad": None,           # filled below (4 corners of the screen)
    "monitor_rect": None,           # bounding rect of the screen
    "monitor_space": (640, 400),    # logical size used by bedroom_monitor_space()
    "chair_floor": _BD_CHAIR,
    "chair_seat": (1625, 1392),     # hip point of a seated character
    "seated_faces": "right",
    "behind_chair_feet": (1460, 1560),
    "desk_lean_feet": (1880, 1520),  # Emb leaning on the desk (s06)
    "tug_left_feet": (560, 1540),   # s07 tug-of-war spots
    "tug_right_feet": (1080, 1540),
    "cam": {  # suggested framings: (cx, cy, zoom)
        "s01_open": (1735, 980, 1.12),
        "desk_medium": (1760, 1010, 1.7),
        "s05_wide": (1180, 1010, 0.56),
        "door_wide": (520, 1000, 1.0),
        "closet_bed": (980, 1050, 1.0),
        "tug": (760, 1030, 0.85),
    },
}


def _bd_monitor_geo():
    x, y, w, h, rise = _BD_MON
    quad = [(x, y), (x + w, y + rise), (x + w, y + rise + h), (x, y + h)]
    return quad


BEDROOM_MARKS["monitor_quad"] = _bd_monitor_geo()
_q = BEDROOM_MARKS["monitor_quad"]
BEDROOM_MARKS["monitor_rect"] = (min(p[0] for p in _q), min(p[1] for p in _q),
                                 max(p[0] for p in _q) - min(p[0] for p in _q),
                                 max(p[1] for p in _q) - min(p[1] for p in _q))


class bedroom_monitor_space:
    """with sets.bedroom_monitor_space(ctx): draw into (0, 0, 640, 400).

    Maps a flat 640 x 400 screen onto the bedroom monitor's 3/4-turned
    screen (affine, clipped). Use it inside the same camera as the set.
    """
    def __init__(self, ctx, W=640, H=400):
        self.ctx, self.W, self.H = ctx, W, H

    def __enter__(self):
        x, y, w, h, rise = _BD_MON
        c = self.ctx
        c.save()
        core.poly(c, BEDROOM_MARKS["monitor_quad"])
        c.clip()
        m = cairo.Matrix(w / self.W, rise / self.W, 0, h / self.H, x, y)
        c.transform(m)
        return c

    def __exit__(self, *a):
        self.ctx.restore()


def _room_shell(c, W, H, CEIL, FLOOR, vp, wall, wall_sh, ceil, ceil_sh, floor, floor_sh,
                ext=(500, 800, 500, 800), planks=True, trim=None, side=True):
    """Box-set shell: ceiling band, back wall (0..W), perspective side walls
    beyond the world edges, plank floor; drawn over the extended rect so zoomed
    out framings stay furnished."""
    x0, y0, x1, y1 = -ext[0], -ext[1], W + ext[2], H + ext[3]
    c.rectangle(x0, y0, x1 - x0, CEIL - y0 + 2)
    core.fill(c, ceil)
    c.rectangle(x0, FLOOR, x1 - x0, y1 - FLOOR)
    core.fill(c, floor)
    if planks:
        yy, gap, row = FLOOR, 34, 0
        while yy < y1:
            line(c, [(x0, yy), (x1, yy)], floor_sh, 3.5)
            off = (row * 233) % 420
            for xx in range(int(x0) - 420 + off, int(x1), 420):
                line(c, [(xx, yy), (xx, yy + gap)], floor_sh, 3)
            yy += gap
            gap = min(gap * 1.2, 260)
            row += 1
    if side:
        c.rectangle(0, CEIL, W, FLOOR - CEIL)
    else:
        c.rectangle(x0, CEIL, x1 - x0, FLOOR - CEIL)
    core.fill(c, wall)

    def along(px, py, xt):
        k = (xt - vp[0]) / (px - vp[0])
        return (xt, vp[1] + (py - vp[1]) * k)
    if side:
        for (bx, xt) in ((0, x0), (W, x1)):
            pc, pf = along(bx, CEIL, xt), along(bx, FLOOR, xt)
            polyf(c, [(bx, CEIL), pc, pf, (bx, FLOOR)], wall_sh, 0)
            line(c, [(bx, CEIL), pc], INK, 5)
            line(c, [(bx, FLOOR), pf], INK, 5)
            line(c, [(bx, CEIL), (bx, FLOOR)], INK, 4)
            # baseboard on the side wall
            pf2 = along(bx, FLOOR - 40, xt)
            polyf(c, [(bx, FLOOR - 40), pf2, pf, (bx, FLOOR)], trim or C["trim"], 4)
    # contact shadow + baseboard + crown on the back wall
    bx0, bx1 = (0, W) if side else (x0, x1)
    c.rectangle(bx0, FLOOR, bx1 - bx0, 26)
    core.fill(c, core.alpha(C["wood_dk"], 0.30))
    c.rectangle(bx0, FLOOR - 40, bx1 - bx0, 40)
    fs(c, trim or C["trim"], 4)
    line(c, [(bx0, FLOOR - 28), (bx1, FLOOR - 28)], C["trim_sh"], 3)
    c.rectangle(bx0, CEIL - 6, bx1 - bx0, 22)
    fs(c, trim or C["trim"], 4)
    # faint ceiling shading toward the camera
    c.rectangle(x0, y0, x1 - x0, min(0, CEIL) - y0)
    core.fill(c, core.alpha(ceil_sh, 0.5))


_BD_EXT = (500, 800, 500, 800)


def _bd_static(c, light_on=True):
    W, H = BEDROOM_W, BEDROOM_H
    CEIL, FLOOR = _BD_CEIL, _BD_FLOOR
    _room_shell(c, W, H, CEIL, FLOOR, _BD_VP, C["bd_wall"], C["bd_wall_sh"], C["bd_ceil"],
                C["bd_ceil_sh"], C["wood"], C["wood_sh"], _BD_EXT)
    # wallpaper stripes + dots
    for i in range(0, W, 96):
        c.rectangle(i + 30, CEIL + 16, 34, FLOOR - CEIL - 56)
    core.fill(c, C["bd_stripe"])
    for i in range(0, W, 96):
        for k in range(6):
            yy = CEIL + 80 + k * 170 + (40 if (i // 96) % 2 else 0)
            core.circle(c, i + 47, yy, 5)
    core.fill(c, C["bd_wall_sh"])
    # glow-in-the-dark star stickers on the ceiling
    for i in range(16):
        sx = -300 + hash01(i, 41) * 3000
        sy = -700 + hash01(i, 42) * 940
        props._star(c, sx, sy, 14 + 10 * hash01(i, 43), rot=hash01(i, 44))
        fs(c, "#f4f7c8", 3, sc=C["bd_ceil_sh"])
    # stuff on the near floor (only seen in wide framings)
    props.sock(c, 1750, 2050, 1.2, 0.5, "#ffffff")
    rect(c, 300, 2080, 300, 60, "#e8b25a", 5, r=8)          # pizza box
    core.text(c, "PIZZA", 450, 2124, 40, "#c0453f", "comic")
    # spare game controller (clearly a gamepad: grips, d-pad, coloured buttons)
    blob(c, [(1222, 2190), (1236, 2128), (1290, 2112), (1350, 2112), (1404, 2128),
             (1418, 2190), (1392, 2206), (1360, 2176), (1280, 2176), (1248, 2206)],
         "#8a8fa8", 5)
    rect(c, 1262, 2142, 30, 10, "#3a3a4a", 0); rect(c, 1272, 2132, 10, 30, "#3a3a4a", 0)
    for (bx_, by_, bc_) in ((1372, 2134, "#ff6f61"), (1388, 2148, "#5ec2ff"),
                            (1356, 2148, "#ffd166"), (1372, 2162, "#7bd88f")):
        core.circle(c, bx_, by_, 6.5); core.fill(c, bc_)

    # ---- string lights along the top of the wall (cosy)
    pts = []
    for k in range(15):
        x = 980 + k * 95
        pts.append((x, CEIL + 34 + 30 * math.sin(k * 0.5 * math.pi) ** 2))
    curve(c, pts, "#4a4458", 3)
    for k, (x, y) in enumerate(pts):
        col = ["#ffd27a", "#ff9aac", "#9fd8f7", "#c9f29b"][k % 4]
        _glow(c, x, y + 14, 34, col, 0.45)
        ell(c, x, y + 12, 8, 11, col, 2.5)

    # ---- door frame recess (the doorway opening is cleared at the end)
    dx, dt, dw, dh = _BD_DOOR
    rect(c, dx - 4, dt - 4, dw + 8, dh + 4, C["bd_wall_sh"], 0)
    # outlet near the desk
    rect(c, 1690, 1210, 30, 42, C["trim"], 3, r=5)

    # ---- closet frame + interior
    cx, ct, cw, ch = _BD_CLOSET
    rect(c, cx - 26, ct - 26, cw + 52, ch + 26, C["trim"], 5, r=4)
    rect(c, cx, ct, cw, ch, "#6a5a7e", 4)
    rect(c, cx, ct, cw, 160, "#594a6d", 0)
    # shelf + boxes
    rect(c, cx + 6, ct + 150, cw - 12, 16, C["wood_sh"], 3.5)
    rect(c, cx + 30, ct + 70, 110, 80, "#d9a46a", 3.5, r=4)
    rect(c, cx + 150, ct + 96, 90, 54, "#e8846a", 3.5, r=4)
    rect(c, cx + 260, ct + 40, 70, 110, "#7fb2e8", 3.5, r=4)
    # rod + hangers + clothes
    line(c, [(cx + 10, ct + 220), (cx + cw - 10, ct + 220)], "#c9c6d4", 7)
    cols = ["#3d4f86", "#8d8f9a", "#e8846a", "#3d4f86", "#f2c14e", "#7cc96a", "#8d8f9a"]
    for k in range(7):
        hx = cx + 40 + k * 54
        line(c, [(hx, ct + 222), (hx, ct + 238)], "#c9c6d4", 3)
        col = cols[k]
        L = 300 + 80 * hash01(k, 5)
        blob(c, [(hx - 34, ct + 244), (hx + 34, ct + 244), (hx + 40, ct + 244 + L * 0.5),
                 (hx + 30, ct + 244 + L), (hx - 30, ct + 244 + L), (hx - 40, ct + 244 + L * 0.5)],
             col, 3.5, tension=0.3)
        line(c, [(hx - 20, ct + 260), (hx, ct + 280), (hx + 20, ct + 260)], INK, 3)
    # shoes on the closet floor
    for k in range(3):
        sx = cx + 50 + k * 120
        blob(c, [(sx, ct + ch - 6), (sx + 4, ct + ch - 40), (sx + 50, ct + ch - 36),
                 (sx + 80, ct + ch - 8)], ["#ff6f61", "#ffffff", "#3d4f86"][k], 3.5)
    rect(c, cx, ct + ch - 12, cw, 12, C["wood_sh"], 0)

    # ---- window with the sunny street
    wx, wy, ww, wh = _BD_WIN
    rect(c, wx - 34, wy - 34, ww + 68, wh + 68, C["trim"], 5, r=6)
    c.save()
    c.rectangle(wx, wy, ww, wh)
    c.clip()
    core.vgradient(c, "#8fd0f5", "#d2f0ff", wx, wy, ww, wh)
    _cloud(c, wx + 110, wy + 80, 0.55)
    _cloud(c, wx + 330, wy + 50, 0.4)
    # houses across the street
    _house_far(c, wx - 40, wy + 330, 200, 120, "#f2b6a0", "#7a6a9a", 1, 3)
    _house_far(c, wx + 200, wy + 336, 230, 140, "#bfe0c0", "#c0453f", 2, 3)
    _tree(c, wx + 170, wy + 340, 0.42, seed=4)
    c.rectangle(wx, wy + 330, ww, 30)
    core.fill(c, C["grass"])
    c.rectangle(wx, wy + 356, ww, 60)
    core.fill(c, C["road"])
    line(c, [(wx, wy + 384), (wx + ww, wy + 384)], "#f3ead6", 4)
    c.restore()
    # window light spill on the wall
    _glow(c, wx + ww / 2, wy + wh / 2, 420, "#fff6d0", 0.28)
    # sash + glass glints
    rect(c, wx, wy, ww, wh, None, 5)
    rect(c, wx - 6, wy + wh * 0.5 - 8, ww + 12, 16, C["trim"], 4)
    line(c, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], INK, 14)
    line(c, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], C["trim"], 8)
    for gx in (wx + 30, wx + ww / 2 + 30):
        polyf(c, [(gx, wy + 20), (gx + 40, wy + 20), (gx + 10, wy + 150), (gx - 30, wy + 150)],
              (1, 1, 1, 0.28), 0)
    # sill + cactus + soda can
    rect(c, wx - 50, wy + wh + 30, ww + 100, 26, C["trim"], 4, r=4)
    rect(c, wx + 40, wy + wh - 20, 50, 50, "#d9734f", 3.5, r=6)
    blob(c, [(wx + 50, wy + wh - 20), (wx + 52, wy + wh - 80), (wx + 66, wy + wh - 100),
             (wx + 80, wy + wh - 80), (wx + 80, wy + wh - 20)], "#6fbf6a", 3.5)
    rect(c, wx + ww - 90, wy + wh - 22, 36, 52, "#ff6f61", 3.5, r=6)
    line(c, [(wx + ww - 72, wy + wh - 14), (wx + ww - 72, wy + wh + 24)], "#ffffff", 4)
    # curtains
    for side in (-1, 1):
        bx = wx - 40 if side < 0 else wx + ww + 40
        pts = [(bx - side * 0, wy - 60), (bx + side * 90, wy - 60), (bx + side * 60, wy + 240),
               (bx + side * 110, wy + wh + 120), (bx - side * 10, wy + wh + 120), (bx + side * 10, wy + 240)]
        blob(c, pts, C["curtain"], 5, tension=0.3)
        curve(c, [(bx + side * 40, wy - 40), (bx + side * 30, wy + 200), (bx + side * 60, wy + wh + 100)],
              C["curtain_sh"], 5)
        rect(c, bx + side * 10 - 22, wy + 228, 70 if side > 0 else 70, 20, "#f2c14e", 3.5, r=8)
    rect(c, wx - 150, wy - 74, ww + 300, 18, "#8f5c33", 4, r=9)
    for kx in (wx - 160, wx + ww + 160):
        core.circle(c, kx, wy - 65, 16)
        fs(c, "#f2c14e", 4)

    # ---- bed (headboard left)
    bx, by, bw, bh = BEDROOM_MARKS["bed"]
    rect(c, bx, 1000, 50, 440, C["wood_sh"], 5, r=16)       # headboard post
    rect(c, bx + 4, 1010, 42, 30, C["wood_hi"], 0, r=10)
    rect(c, bx + bw - 30, 1150, 36, 290, C["wood_sh"], 5, r=12)  # footboard post
    # under-bed darkness
    rect(c, bx + 40, 1370, bw - 60, 90, "#3b2f2a", 0)
    rect(c, bx + 120, 1396, 140, 64, "#c9a87a", 3.5, r=4)     # storage box
    props.sock(c, bx + 380, 1442, 0.6, 0.2, "#f4f1e8")
    # mattress top + pillow
    rect(c, bx + 40, 1170, bw - 60, 70, C["sheet"], 4, r=14)
    blob(c, [(bx + 60, 1176), (bx + 70, 1120), (bx + 190, 1110), (bx + 230, 1150), (bx + 220, 1186),
             (bx + 80, 1192)], C["sheet"], 4.5)
    curve(c, [(bx + 110, 1150), (bx + 150, 1160), (bx + 190, 1146)], C["sheet_sh"], 4)
    # rumpled blanket on top, draping over the front side
    blob(c, [(bx + 210, 1180), (bx + 300, 1140), (bx + 420, 1160), (bx + 540, 1150), (bx + 560, 1200),
             (bx + 570, 1350), (bx + 470, 1372), (bx + 360, 1345), (bx + 250, 1372), (bx + 160, 1350),
             (bx + 170, 1250)], C["blanket"], 5, tension=0.4)
    for k in range(4):
        sx = bx + 200 + k * 92
        curve(c, [(sx, 1210), (sx + 10, 1280), (sx - 4, 1350)], C["blanket_hi"], 9)
    curve(c, [(bx + 260, 1180), (bx + 330, 1200), (bx + 410, 1185)], C["blanket_sh"], 5)
    curve(c, [(bx + 470, 1300), (bx + 520, 1330)], C["blanket_sh"], 5)
    # bed frame rail
    rect(c, bx + 40, 1352, bw - 60, 34, C["wood"], 4.5, r=8)
    # a dangling blanket corner
    blob(c, [(bx + 470, 1340), (bx + 560, 1350), (bx + 580, 1440), (bx + 520, 1430)], C["blanket"], 4.5)

    # ---- wall shelf above the desk (figurine is live)
    rect(c, 1790, 646, 290, 20, C["wood"], 4, r=4)
    for kx in (1820, 2050):
        polyf(c, [(kx, 666), (kx + 12, 666), (kx + 12, 700)], C["wood_sh"], 3)
    _book_row(c, 1810, 646, 6, seed=3, h=80)
    _plant(c, 1950, 646, 0.5, pot="#7fb2e8", seed=2)

    # ---- desk (right). Front-left leg also in fg (part 'desk').
    _bd_desk_back(c)

    # posters/frames that never move are in the live layer (they tilt on shake)
    # ---- rug
    ell(c, 920, 1700, 520, 120, C["rug_rim"], 5)
    ell(c, 920, 1700, 480, 100, C["rug"], 0)
    ell(c, 920, 1700, 380, 72, None, 4, sc=C["rug_rim"])
    ell(c, 920, 1700, 250, 44, C["rug_sh"], 0)

    # hanging lamp glow (static; the lamp itself is live so it can swing)
    if light_on:
        core.radial_glow(c, 1440, 300, 230, "#ffe7a0", 0.30)

    # clear the doorway so the hallway (layer 'back') shows through
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(dx, dt, dw, dh)
    c.fill()
    c.restore()


def _bd_rest(c, frame_state, with_laundry, light_on):
    """Cached overlay of the props that only move on shake: right sun patch,
    posters, picture frame, figurine, hanging lamp, laundry heap at rest."""
    _sun_patch(c, [(1560, 520), (1810, 492), (1850, 1060), (1590, 1100)], 0.5)
    _sun_patch(c, [(1580, 560), (1676, 549), (1692, 770), (1596, 784)], 0.22, "#ffffff")
    _bd_posters(c, 0.0, 0.0)
    _bd_frame(c, 0.0, frame_state)
    _bd_figurine(c, 0.0, 0.0)
    _bd_light(c, 0.0, 0.0, light_on)
    if with_laundry:
        _bd_laundry(c, 0.0, 0.0, with_laundry == "scattered")


_BD_REST_RECT = (600, -10, 1740, 1780)


def _bd_desk_back(c):
    # desk: top surface, apron, legs, PC tower, stuff on it
    x0, x1 = 1700, 2340
    top_back, top_front = 1076, 1110
    # monitor glow on the wall (static) + desk lamp pool
    _glow(c, 1960, 900, 380, "#bfe6ff", 0.35)
    _glow(c, 2290, 980, 300, "#ffd27a", 0.40)
    # right leg + PC tower
    rect(c, x1 - 50, top_front + 30, 34, 1450 - top_front - 30, C["desk_sh"], 4.5)
    rect(c, 2090, 1180, 170, 270, "#2f2b3d", 5, r=10)
    core.circle(c, 2175, 1290, 50)
    fs(c, "#3a3550", 4)
    core.circle(c, 2175, 1290, 50)
    core.stroke(c, "#d77bff", 6)
    core.circle(c, 2175, 1380, 30)
    core.stroke(c, "#ff9aac", 5)
    _glow(c, 2175, 1290, 120, "#d77bff", 0.25)
    rect(c, 2110, 1196, 60, 10, "#4a4560", 0, r=3)
    # back legs
    rect(c, 1760, top_front + 20, 26, 280, C["desk_sh"], 4)
    # top + apron
    polyf(c, [(x0 + 30, top_back), (x1 - 20, top_back), (x1, top_front), (x0, top_front)], C["desk_top"], 5)
    rect(c, x0, top_front, x1 - x0, 40, C["desk"], 5, r=4)
    line(c, [(x0 + 12, top_front + 36), (x1 - 12, top_front + 36)], "#ff7ad9", 5)
    _glow(c, (x0 + x1) / 2, top_front + 60, 260, "#ff7ad9", 0.12)
    # monitor stand + bezel
    q = BEDROOM_MARKS["monitor_quad"]
    polyf(c, [(1946, 1018), (1976, 1016), (1990, 1080), (1934, 1082)], "#2f2b3d", 4)
    ell(c, 1962, 1086, 70, 12, "#2f2b3d", 4)
    bez = 14
    side = 22
    # side thickness (screen is turned to face the chair: we see its right side)
    polyf(c, [q[1], (q[1][0] + side, q[1][1] + 10), (q[2][0] + side, q[2][1] - 4), q[2]], "#24212f", 5)
    polyf(c, [(q[0][0] - bez, q[0][1] - bez), (q[1][0] + bez * 0.6, q[1][1] - bez),
              (q[2][0] + bez * 0.6, q[2][1] + bez), (q[3][0] - bez, q[3][1] + bez)], "#2f2b3d", 5)
    rect(c, q[3][0] + 100, q[3][1] + 4, 14, 6, "#3ddc84", 0)  # tiny power LED
    # speaker
    rect(c, 1745, 960, 56, 120, "#2f2b3d", 4, r=12)
    core.circle(c, 1773, 1000, 16); fs(c, "#4a4560", 3)
    core.circle(c, 1773, 1048, 10); fs(c, "#4a4560", 3)
    # keyboard (RGB) + mouse
    polyf(c, [(1806, 1090), (1952, 1090), (1966, 1106), (1796, 1106)], "#2f2b3d", 4)
    for k in range(8):
        col = ["#ff7ad9", "#d77bff", "#7fb2e8", "#7cf2b0", "#ffd27a", "#ff9aac", "#7fb2e8", "#d77bff"][k]
        rect(c, 1812 + k * 18, 1094, 12, 6, col, 0, r=2)
    polyf(c, [(2026, 1094), (2102, 1094), (2108, 1108), (2020, 1108)], "#3a3550", 0)
    ell(c, 2072, 1096, 16, 9, "#2f2b3d", 3.5)
    # snacks: chips bag, soda cans, mug
    blob(c, [(2196, 1104), (2186, 1030), (2212, 1010), (2262, 1014), (2276, 1040), (2268, 1104)],
         "#ffb020", 4)
    rect(c, 2206, 1046, 50, 30, "#ff3b5c", 3, r=6)
    core.text(c, "CHIPZ", 2231, 1068, 17, "#ffffff", "comic")
    rect(c, 2140, 1052, 30, 52, "#7cc96a", 3.5, r=6)
    rect(c, 2290, 1056, 28, 48, "#5b9bd5", 3.5, r=6)
    line(c, [(2304, 1062), (2304, 1096)], "#ffffff", 3)
    for k in range(4):
        core.circle(c, 2120 + k * 22, 1100 + (k % 2) * 3, 3.5)
    core.fill(c, "#e8a33b")
    # desk lamp
    rect(c, 2300, 1088, 60, 14, "#2f2b3d", 4, r=5)
    line(c, [(2330, 1090), (2300, 970), (2250, 930)], INK, 14)
    line(c, [(2330, 1090), (2300, 970), (2250, 930)], "#5d5878", 8)
    polyf(c, [(2210, 900), (2280, 920), (2262, 968), (2196, 950)], "#ff9aac", 4.5)
    ell(c, 2228, 958, 26, 10, "#fff3c4", 3)


def _bd_desk_front(c):
    """fg part 'desk': the front-left leg that a seated character's knees go behind."""
    rect(c, 1712, 1146, 38, 306, C["desk"], 5)
    line(c, [(1724, 1160), (1724, 1440)], C["desk_top"], 4)


def _bd_hall(c):
    """What you see through the bedroom door: the upstairs hallway (dim, warm)."""
    dx, dt, dw, dh = _BD_DOOR
    x0, y0 = dx - 10, dt - 10
    c.rectangle(x0, y0, dw + 20, dh + 20)
    core.fill(c, C["lv_wall_sh"])
    c.rectangle(x0, y0, dw + 20, 380)
    core.fill(c, mixc(C["lv_wall_sh"], C["lv_wall"], 0.6))
    rect(c, x0, dt + 520, dw + 20, 300, C["lv_wain_sh"], 0)
    line(c, [(x0, dt + 520), (x0 + dw + 20, dt + 520)], INK, 4)
    c.rectangle(x0, dt + dh - 40, dw + 20, 60)
    core.fill(c, C["wood_sh"])
    # sconce + framed picture across the hall
    _glow(c, dx + 120, dt + 280, 200, "#ffd27a", 0.35)
    rect(c, dx + 104, dt + 260, 32, 50, "#f2c14e", 3.5, r=10)
    rect(c, dx + 220, dt + 180, 120, 150, "#c98d4a", 4, r=4)
    rect(c, dx + 236, dt + 196, 88, 118, "#9fd8f7", 3)
    polyf(c, [(dx + 236, dt + 314), (dx + 280, dt + 250), (dx + 324, dt + 314)], C["grass"], 3)
    # banister top running across
    rect(c, x0, dt + 560, dw + 20, 22, C["wood_dk"], 4)
    for k in range(5):
        rect(c, x0 + 30 + k * 90, dt + 582, 16, dh - 600, C["wood_sh"], 3)


def _bd_poster(c, kind):
    if kind == 0:   # game poster (left of the shelf)
        rect(c, -85, 0, 170, 230, "#2b2e5a", 4.5, r=3)
        _star_field(c, -70, 14, 140, 120, 7)
        for (px, py, w, h, col) in ((-30, 120, 20, 20, "#3d4f86"), (-36, 100, 32, 22, "#3d4f86"),
                                    (-26, 86, 14, 14, "#f2c29a")):
            rect(c, px, py, w, h, col, 0)
        rect(c, -70, 150, 140, 18, "#4ed15a", 0)
        core.text(c, "PIXEL", 0, 196, 30, "#ffe45c", "title")
        core.text(c, "QUEST", 0, 222, 26, "#ff9aac", "title")
    elif kind == 1:  # chill planet poster (above closet)
        rect(c, -150, 0, 300, 170, "#ffb3a0", 4.5, r=3)
        core.circle(c, -40, 80, 50); fs(c, "#8a6aa8", 3.5)
        ell(c, -40, 80, 86, 18, None, 4, sc="#ffe9a6", rot=-0.2)
        core.text(c, "NAP", 80, 82, 40, "#5a3a7a", "title")
        core.text(c, "MODE", 80, 120, 32, "#5a3a7a", "title")
    else:            # band/headphones poster (right of the shelf)
        rect(c, -90, 0, 180, 250, "#ffe9a6", 4.5, r=3)
        core.circle(c, 0, 110, 56); core.stroke(c, INK, 10)
        rect(c, -70, 100, 34, 60, "#7fb2e8", 4, r=10)
        rect(c, 36, 100, 34, 60, "#7fb2e8", 4, r=10)
        core.text(c, "LO-FI", 0, 214, 34, "#3d4f86", "title")
        core.text(c, "BEATS", 0, 240, 22, "#c0453f", "title")


def _star_field(c, x, y, w, h, n, seed=5):
    for i in range(n):
        core.circle(c, x + hash01(i, seed) * w, y + hash01(i, seed + 1) * h, 2.5 + 2 * hash01(i, seed + 2))
    core.fill(c, "#ffffff")


def _bd_posters(ctx, t, shake):
    for i, (kind, px, py) in enumerate(((1, 795, 334), (0, 2205, 360), (2, 1760, 360))):
        rot = 0.0
        if shake > 0:
            rot = shake * (0.10 * math.sin(t * 21 + i * 2.1) + 0.05 * math.sin(t * 34 + i))
        rot += (-0.02, 0.025, -0.015)[i]
        with core.saved(ctx, px, py, 0.92 if kind == 2 else 1.0, rot):
            _bd_poster(ctx, kind)
        core.circle(ctx, px, py + 6, 6)
        fs(ctx, "#ff6f61", 2.5)


def _bd_chair(ctx, spin, empty, dx=0.0, part="bg"):
    """Gaming chair. spin 0 = facing right (toward the desk)."""
    x, fy = _BD_CHAIR
    x += dx
    a = spin
    sa, ca = math.sin(a), math.cos(a)
    seat_y = fy - 205
    if part == "bg":
        # base: gas lift + star legs + casters
        rect(ctx, x - 12, seat_y + 40, 24, 120, "#5a5670", 4)
        for k in range(5):
            ang = a + k * TAU / 5
            lx = math.cos(ang) * 110
            ly = math.sin(ang) * 22
            line(ctx, [(x, fy - 34), (x + lx, fy - 30 + ly)], INK, 16)
            line(ctx, [(x, fy - 34), (x + lx, fy - 30 + ly)], C["chair_shell"], 9)
        for k in range(5):
            ang = a + k * TAU / 5
            core.circle(ctx, x + math.cos(ang) * 110, fy - 16 + math.sin(ang) * 22, 13)
            fs(ctx, "#2b2b38", 3)
    back_off = -ca * 70
    back_w = 64 + 136 * abs(sa)
    face = sa > 0.15
    def draw_back():
        bx = x + back_off - back_w / 2
        top = seat_y - 410
        if not face and abs(sa) <= 0.15:
            # profile: cushion face toward the seat, black shell on the back side
            sgn = 1 if ca > 0 else -1
            core.rrect(ctx, bx, top, back_w, 410, 30)
            fs(ctx, C["chair_shell"], 5)
            cx0 = bx + (back_w * 0.35 if sgn > 0 else 0)
            rect(ctx, cx0, top + 10, back_w * 0.65, 390, C["chair"], 4, r=24)
            rect(ctx, cx0 + 8, top + 120, back_w * 0.65 - 16, 150, C["chair_sh"], 0, r=14)
            return
        rect(ctx, bx, top, back_w, 410, C["chair"] if face else C["chair_shell"], 5, r=min(40, back_w / 2))
        if face:
            rect(ctx, bx + back_w * 0.32, top + 30, back_w * 0.36, 330, C["chair_sh"], 0, r=back_w * 0.12)
            rect(ctx, bx + back_w * 0.18, top + 60, back_w * 0.64, 50, C["chair_shell"], 3.5, r=12)
        else:
            line(ctx, [(bx + back_w * 0.5, top + 40), (bx + back_w * 0.5, top + 360)], C["chair"], 6)
        # headrest pillow
        rect(ctx, bx + back_w * 0.15, top + 8, back_w * 0.7, 40, C["chair_shell"] if face else C["chair"],
             3.5, r=14)
    def draw_seat():
        sw = 170 + 30 * abs(ca)
        ell(ctx, x, seat_y, sw / 2 + 6, 34, C["chair_shell"], 5)
        ell(ctx, x, seat_y - 10, sw / 2, 28, C["chair"], 4)
        ell(ctx, x, seat_y - 14, sw / 2 - 30, 12, C["chair_sh"], 0)
    if part == "bg":
        back_behind = sa > -0.05
        if back_behind:
            draw_back()
        draw_seat()
        if not back_behind:
            draw_back()
        if empty:
            # near armrest
            ax = x + ca * 10
            rect(ctx, ax - 60, seat_y - 90, 120, 22, C["chair_shell"], 4, r=10)
            rect(ctx, ax - 8, seat_y - 70, 16, 60, C["chair_shell"], 3.5)
    elif part == "fg" and not empty:
        ax = x + ca * 10
        rect(ctx, ax - 8, seat_y - 70, 16, 60, C["chair_shell"], 3.5)


def _stripes_in(ctx, path_fn, x0, y0, w, h, step, col, lw, ang=0.0):
    ctx.save()
    path_fn()
    ctx.clip()
    for k in range(-2, int((w + h) / step) + 3):
        xx = x0 + k * step
        line(ctx, [(xx, y0 - 10), (xx + h * ang, y0 + h + 10)], col, lw)
    ctx.restore()


def _garment(ctx, kind, col, t=0.0, dang=0.0):
    """Clothes for the laundry heap, local coords (~120-200 px)."""
    dk = mixc(col, "#2a1020", 0.25)
    if kind == "jeans":
        for side, rr in ((-1, -0.25), (1, 0.18)):
            with core.saved(ctx, side * 40, 0, 1.0, rr):
                rect(ctx, -32, -20, 64, 150 + dang, col, 4.5, r=14)
                line(ctx, [(0, -10), (0, 130 + dang)], dk, 3)
                rect(ctx, -32, 118 + dang, 64, 18, dk, 3.5, r=6)
        rect(ctx, -76, -46, 152, 46, col, 4.5, r=12)
        line(ctx, [(-70, -30), (70, -30)], "#f2c14e", 3)
    elif kind == "tee":
        pts = [(-80, -50), (-36, -60), (36, -60), (80, -50), (100, -10), (64, 0), (60, 60 + dang),
               (-60, 60 + dang), (-64, 0), (-100, -10)]
        def path():
            core.smooth_path(ctx, pts, closed=True, tension=0.25)
        path()
        fs(ctx, "#ffffff", 0)
        _stripes_in(ctx, path, -110, -70, 220, 140 + dang, 30, col, 12, ang=0.0)
        path()
        core.stroke(ctx, INK, 4.5)
        curve(ctx, [(-30, -60), (0, -46), (30, -60)], INK, 3.5)
    elif kind == "hoodie":
        pts = [(-90, -40), (-50, -70), (50, -70), (92, -40), (96, 50), (-96, 50)]
        blob(ctx, pts, col, 5, tension=0.3)
        blob(ctx, [(-40, -66), (-30, -104), (30, -106), (44, -66), (0, -54)], dk, 4)
        line(ctx, [(-12, -54), (-14, -16)], "#ffffff", 3.5)
        line(ctx, [(12, -54), (16, -20)], "#ffffff", 3.5)
        # dangling sleeve
        blob(ctx, [(70, 0), (104, -6), (112, 70 + dang), (80, 76 + dang)], col, 4.5)
        rect(ctx, 80, 64 + dang, 34, 16, dk, 3, r=6)
        rect(ctx, -50, 10, 100, 34, dk, 3, r=10)   # pocket
    elif kind == "towel":
        polyf(ctx, [(-70, -30), (70, -40), (80, 30 + dang), (-64, 40 + dang)], col, 4.5)
        for k in range(3):
            line(ctx, [(-60, -16 + k * 20), (68, -24 + k * 20)], "#ffffff", 4)


def _bd_laundry(ctx, t, lift, scattered):
    x, y = BEDROOM_MARKS["laundry"]
    if scattered:
        spots = [(-320, 30, 0.4), (-170, 70, -0.6), (210, 40, 0.8), (330, 80, -0.2), (60, 100, 1.4)]
        cols = ["#8d8f9a", "#ff6f61", "#ffffff", "#f2c14e", "#ffffff"]
        for i, (ox, oy, r) in enumerate(spots):
            if i in (1, 4):
                props.sock(ctx, x + ox, y + oy, 0.9, r, cols[i])
            else:
                props.shirt(ctx, x + ox, y + oy - 10, 0.55, r, cols[i], print_=(i == 0))
        return
    l = clamp(lift)
    # bottom: jeans stay on the floor
    with core.saved(ctx, x - 20, y - 40, 1.0, -1.35):
        _garment(ctx, "jeans", "#4f6fae")
    # top bundle lifts as one with dangling bits
    up = -270 * l
    sway = 6 * math.sin(t * 5) * l
    dang = 60 * l
    with core.saved(ctx, x + sway, y - 70 + up):
        with core.saved(ctx, 60, -10, 0.9, 0.15):
            _garment(ctx, "towel", "#f2c14e", t, dang * 0.5)
        with core.saved(ctx, -40, -20, 0.95, -0.12):
            _garment(ctx, "hoodie", "#8d8f9a", t, dang)
        with core.saved(ctx, 40, -60, 0.8, 0.22):
            _garment(ctx, "tee", "#ff6f61", t, dang * 0.4)
        props.sock(ctx, -90, -84, 0.75, -0.5, "#ffffff")
        props.sock(ctx, 96, -96, 0.7, 0.9 + 0.5 * l, "#7cc96a", "#ffffff")


def _bd_closet_panel(ctx, opening):
    cx, ct, cw, ch = _BD_CLOSET
    half = cw / 2
    # back track panel (right half) fixed
    def panel(x, stickers):
        rect(ctx, x, ct, half, ch, "#f6efe0", 5, r=4)
        rect(ctx, x + 22, ct + 30, half - 44, ch * 0.42, None, 4, sc=C["trim_sh"], r=6)
        rect(ctx, x + 22, ct + 60 + ch * 0.42, half - 44, ch * 0.42, None, 4, sc=C["trim_sh"], r=6)
        if stickers:
            props._star(ctx, x + 60, ct + 120, 26)
            fs(ctx, "#ffd27a", 3)
            rect(ctx, x + 110, ct + 240, 64, 40, "#7fb2e8", 3, r=12)
            core.circle(ctx, x + 126, ct + 260, 5); core.circle(ctx, x + 156, ct + 260, 5)
            core.fill(ctx, INK)
            core.circle(ctx, x + 70, ct + 420, 22); fs(ctx, "#ff9aac", 3)
            core.text(ctx, "zz", x + 70, ct + 428, 22, "#ffffff", "comic")
        return x
    panel(cx + half, False)
    ell(ctx, cx + half + 30, ct + ch * 0.5, 9, 22, C["trim_sh"], 3)
    off = clamp(opening) * (half - 12)
    panel(cx + off, True)
    ell(ctx, cx + off + half - 30, ct + ch * 0.5, 9, 22, C["trim_sh"], 3)


def _bd_door_panel(ctx, opening):
    dx, dt, dw, dh = _BD_DOOR
    q = door_quad(dx, dt, dt + dh, dw, opening, _BD_VP, toward=True)
    polyf(ctx, q, "#f4ecdd", 6)
    if opening < 0.97:
        # panels drawn in door-local coords via bilinear mapping of the quad
        def P(u, v):
            top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
            bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
            return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
        for (u0, v0, u1, v1) in ((0.16, 0.07, 0.84, 0.44), (0.16, 0.53, 0.84, 0.92)):
            polyf(ctx, [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], None, 4, sc=C["trim_sh"])
        kx, ky = P(0.89, 0.55)
        core.circle(ctx, kx, ky, 15 * (1 - 0.6 * opening))
        fs(ctx, "#f2c14e", 4)
        # little zZz sticker
        sx, sy = P(0.5, 0.25)
        if opening < 0.6:
            core.text(ctx, "zZz", sx, sy + 14, 40 * (1 - 0.7 * opening), "#8a6aa8", "comic")


def _bd_door_casing(ctx):
    dx, dt, dw, dh = _BD_DOOR
    trim = 30
    polyf(ctx, [(dx - trim, dt - trim), (dx + dw + trim, dt - trim), (dx + dw + trim, dt + dh),
                (dx + dw, dt + dh), (dx + dw, dt), (dx, dt), (dx, dt + dh), (dx - trim, dt + dh)], C["trim"], 5)
    line(ctx, [(dx - trim + 10, dt - trim + 10), (dx + dw + trim - 10, dt - trim + 10)], C["trim_sh"], 3)


def _bd_light(ctx, t, shake, on=True):
    x, y = 1440, 0
    ang = shake * 0.22 * math.sin(t * 8.5)
    with core.saved(ctx, x, y, 1.0, ang):
        line(ctx, [(0, 0), (0, 190)], "#4a4458", 5)
        polyf(ctx, [(-34, 190), (34, 190), (90, 268), (-90, 268)], "#f2c14e", 5)
        ell(ctx, 0, 270, 90, 14, "#fff3c4" if on else "#e8e2c8", 4)
        line(ctx, [(-50, 230), (50, 230)], "#d9973b", 4)


def _bd_figurine(ctx, t, shake):
    x, y = BEDROOM_MARKS["shelf_figurine"]
    rot = shake * 0.28 * math.sin(t * 26)
    with core.saved(ctx, x, y + 4, 1.0, rot):
        ell(ctx, 0, -4, 26, 8, "#5d5878", 3)
        # little pixel-hero vinyl figure
        rect(ctx, -16, -60, 32, 54, "#ff6f61", 3.5, r=8)
        core.circle(ctx, 0, -78, 22); fs(ctx, "#f2c29a", 3.5)
        blob(ctx, [(-24, -82), (-18, -104), (18, -104), (26, -84), (0, -92)], "#3d4f86", 3.5)
        core.circle(ctx, -7, -78, 3); core.circle(ctx, 7, -78, 3)
        core.fill(ctx, INK)


def _bd_frame(ctx, t, fallen):
    nx, ny = BEDROOM_MARKS["picture_nail"]
    f = 1.0 if fallen is True else (0.0 if fallen is False or fallen is None else clamp(float(fallen)))
    if f > 0:
        # paler unfaded patch where it hung + nail
        rect(ctx, nx - 60, ny + 28, 120, 140, mixc(C["bd_wall"], "#ffffff", 0.18), 0, r=4)
    core.circle(ctx, nx, ny, 4)
    core.fill(ctx, "#5a5368")
    if f <= 0:
        props.picture_frame(ctx, nx, ny, 1.0, 0.03)
        return
    fx, fy = BEDROOM_MARKS["picture_floor"]
    if f < 1:
        k = core.ease_in(f)
        x = lerp(nx, fx, k)
        y = lerp(ny, fy - 170, k)
        rot = 2.6 * k
        props.picture_frame(ctx, x, y, 1.0, rot, wire=False)
    else:
        # lying flat on the floor, face down
        with core.saved(ctx, fx, fy, (1.0, 0.32)):
            props.picture_frame(ctx, 0, -100, 1.0, 0.0, face_down=True)


def _bd_dust(ctx, t, shake):
    if shake <= 0.05:
        return
    x0, y0 = 1440, 280
    for i in range(10):
        ph = (t * 0.7 + hash01(i, 77)) % 1.0
        x = x0 + (hash01(i, 78) - 0.5) * 160 + 14 * math.sin(t * 3 + i)
        y = y0 + ph * 520
        core.circle(ctx, x, y, 3 + 2.5 * hash01(i, 79))
        core.fill(ctx, core.alpha("#fff7dc", shake * (1 - ph) * 0.9))


def bedroom(ctx, t=0.0, layer="bg", door_open=0.0, closet_open=0.0, laundry=0.0,
            laundry_scattered=False, chair_spin=0.0, chair_empty=False, chair_dx=0.0,
            shake=0.0, frame_fallen=True, screen_fn=None, screen_on=True, game_speed=1.0,
            light_on=True, parts=None):
    """Tiredness's bedroom. World 2400 x 1920, people at s=0.75. See BEDROOM_MARKS.

    layer: "bg" (everything behind characters), "back" (only the hallway
    seen through the doorway), "room" (bg without the hallway: use
    back -> character in the hallway -> room), "fg" (door casing, desk
    front-left leg, near armrest when someone sits; pick with parts=).
    States: door_open 0..1, closet_open 0..1, laundry 0..1 (heap lifted),
    laundry_scattered, chair_spin (radians, 0 = facing the desk),
    chair_empty, chair_dx, shake 0..1, frame_fallen (bool or 0..1 fall
    progress), screen_fn(ctx, t) draws into bedroom_monitor_space (default:
    props.monitor_game_screen), screen_on, game_speed, light_on.
    """
    W, H = BEDROOM_W, BEDROOM_H
    if layer in ("bg", "back"):
        dx, dt, dw, dh = _BD_DOOR
        cached_or_live(ctx, "bedroom_hall", dx - 12, dt - 12, dw + 24, dh + 24, _bd_hall)
        if layer == "back":
            return
    if layer in ("bg", "room"):
        e = _BD_EXT
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], C["bd_ceil"], C["wood"], C["bd_wall_sh"],
                  C["bd_wall_sh"])
        static_layer(ctx, ("bedroom_room", bool(light_on)), -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3],
                     lambda c: _bd_static(c, light_on))
        _bd_door_casing(ctx)
        _bd_door_panel(ctx, door_open)
        _bd_closet_panel(ctx, closet_open)
        # sun patch from the (off-screen) side window over the closet (live: panel moves)
        _sun_patch(ctx, [(600, 640), (860, 610), (930, 1060), (660, 1110)], 0.22)
        fs_ = frame_fallen
        frame_rest = fs_ in (True, False, None) or float(fs_) in (0.0, 1.0)
        frame_state = bool(fs_) if frame_rest else None
        laundry_rest = laundry_scattered or laundry <= 0.0
        if shake <= 0.0 and frame_rest:
            lk = ("scattered" if laundry_scattered else "heap") if laundry_rest else None
            cached_or_live(ctx, ("bedroom_rest", frame_state, lk, bool(light_on)), *_BD_REST_RECT,
                           lambda c: _bd_rest(c, frame_state, lk, light_on))
            if not laundry_rest:
                _bd_laundry(ctx, t, laundry, laundry_scattered)
        else:
            _sun_patch(ctx, [(1560, 520), (1810, 492), (1850, 1060), (1590, 1100)], 0.5)
            _sun_patch(ctx, [(1580, 560), (1676, 549), (1692, 770), (1596, 784)], 0.22, "#ffffff")
            _bd_posters(ctx, t, shake)
            _bd_frame(ctx, t, frame_fallen)
            _bd_figurine(ctx, t, shake)
            _bd_light(ctx, t, shake, light_on)
            _bd_laundry(ctx, t, laundry, laundry_scattered)
        if screen_on:
            with bedroom_monitor_space(ctx) as c:
                if screen_fn is not None:
                    screen_fn(c, t)
                else:
                    props.monitor_game_screen(c, 0, 0, 640, 400, t, speed=game_speed)
        else:
            core.poly(ctx, BEDROOM_MARKS["monitor_quad"])
            core.fill(ctx, "#1b1d27")
        core.poly(ctx, BEDROOM_MARKS["monitor_quad"])
        core.stroke(ctx, INK, 4)
        _bd_chair(ctx, chair_spin, chair_empty, chair_dx, "bg")
        _bd_dust(ctx, t, shake)
        return
    if layer == "fg":
        parts = parts or ("door", "desk", "chair")
        if "door" in parts:
            _bd_door_casing(ctx)
            if door_open > 0.02:
                _bd_door_panel(ctx, door_open)
        if "desk" in parts:
            _bd_desk_front(ctx)
        if "chair" in parts:
            _bd_chair(ctx, chair_spin, chair_empty, chair_dx, "fg")


# ============================================================================
# 2. BEDROOM WINDOW, SEEN FROM OUTSIDE  +  STREET VIEW (his POV)
# ============================================================================
WINDOW_EXT_W, WINDOW_EXT_H = 1080, 1920
_WX = (190, 430, 700, 730)   # glass x, y, w, h
WINDOW_EXT_MARKS = {
    "size": (WINDOW_EXT_W, WINDOW_EXT_H),
    "char_scale": 1.45,          # medium shot: head + shoulders fill the glass
    "glass": _WX,
    "lean_face": (540, 800),     # face position of someone leaning to the glass
    "lean_feet": (540, 2100),    # feet (off-screen, hidden by the wall) for s=1.45 -> face at ~800
    "sill_y": 1180,
    "meeting_rail_y": 1020,
    "cam": {"default": (540, 960, 1.0), "close": (540, 800, 1.35)},
}


def _siding(c, x, y, w, h, base, sh, line_c, step=62, lw=3.5):
    c.rectangle(x, y, w, h)
    core.fill(c, base)
    yy = y + step
    while yy < y + h:
        c.rectangle(x, yy - 12, w, 12)
        core.fill(c, sh)
        line(c, [(x, yy), (x + w, yy)], line_c, lw)
        yy += step


def _wext_interior(c):
    gx, gy, gw, gh = _WX
    dim = lambda col: mixc(col, "#2a2238", 0.42)
    c.rectangle(gx, gy, gw, gh)
    core.fill(c, dim(C["bd_wall"]))
    for i in range(0, gw + 96, 96):
        c.rectangle(gx + i + 30, gy, 34, gh)
    core.fill(c, dim(C["bd_stripe"]))
    c.rectangle(gx, gy, gw, 70)
    core.fill(c, dim(C["bd_ceil"]))
    _glow(c, gx + 470, gy + 70, 260, "#ffe7a0", 0.25)
    with core.saved(c, gx + 470, gy - 120):
        line(c, [(0, 0), (0, 150)], "#4a4458", 5)
        polyf(c, [(-26, 150), (26, 150), (70, 210), (-70, 210)], dim("#f2c14e"), 4)
    with core.saved(c, gx + 150, gy + 160, 0.9, 0.03):
        _bd_poster(c, 2)
    rect(c, gx + 430, gy + 230, 220, 520, dim("#f4ecdd"), 5)      # far door
    core.circle(c, gx + 460, gy + 520, 12); fs(c, dim("#f2c14e"), 3)
    c.rectangle(gx, gy + gh - 120, gw, 120)
    core.fill(c, dim(C["wood"]))
    c.rectangle(gx, gy, gw, gh)
    core.fill(c, (0.1, 0.08, 0.16, 0.12))


def _wext_wall(c, streaks):
    """Siding wall with the glass cut out, frame, shutters, sill, flower box."""
    W, H = WINDOW_EXT_W, WINDOW_EXT_H
    gx, gy, gw, gh = _WX
    _siding(c, -200, 0, W + 400, H, C["siding"], C["siding_sh"], C["siding_line"])
    rect(c, -200, -40, W + 400, 150, C["house_trim"], 6)
    rect(c, -200, 110, W + 400, 40, "#e6e0d2", 5, r=8)
    for sx in (40, 940):
        rect(c, sx, 400, 100, 790, "#6f86b8", 5, r=6)
        for k in range(12):
            line(c, [(sx + 12, 440 + k * 60), (sx + 88, 440 + k * 60)], "#566ea3", 6)
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(gx, gy, gw, gh)
    c.fill()
    c.restore()
    _wext_fg(c, streaks)


def _wext_fg(c, streaks=True):
    gx, gy, gw, gh = _WX
    t = 44
    trim = C["house_trim"]
    # outer trim (frame with a hole)
    c.rectangle(gx - t, gy - t, gw + 2 * t, gh + 2 * t)
    c.rectangle(gx + gw, gy, -gw, gh)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fs(c, trim, 6)
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    rect(c, gx - t - 20, gy - t - 30, gw + 2 * t + 40, 36, trim, 5, r=6)
    rect(c, gx, gy, gw, gh, None, 5)
    # meeting rail (low, below the face)
    rail = WINDOW_EXT_MARKS["meeting_rail_y"]
    rect(c, gx - 4, rail - 12, gw + 8, 26, trim, 5)
    if streaks:
        for (x0, w0) in ((gx + 60, 70), (gx + 160, 26), (gx + 520, 46)):
            polyf(c, [(x0, gy), (x0 + w0, gy), (x0 + w0 - 140, gy + gh), (x0 - 140, gy + gh)],
                  (1, 1, 1, 0.13), 0)
        c.save()
        c.rectangle(gx, gy, gw, gh)
        c.clip()
        polyf(c, [(gx + gw - 120, gy), (gx + gw, gy), (gx + gw, gy + 120)], (1, 1, 1, 0.18), 0)
        c.restore()
    # sill + flower box
    sy = WINDOW_EXT_MARKS["sill_y"]
    rect(c, gx - 80, sy, gw + 160, 40, trim, 6, r=6)
    rect(c, gx + 40, sy + 40, gw - 80, 120, "#b5544a", 6, r=10)
    for k in range(7):
        line(c, [(gx + 60 + k * 90, sy + 60), (gx + 60 + k * 90, sy + 150)], "#99433b", 4)
    for k in range(9):
        fx = gx + 70 + k * 72
        blob(c, [(fx - 34, sy + 44), (fx - 20, sy + 10), (fx + 6, sy + 4), (fx + 30, sy + 20),
                 (fx + 34, sy + 44)], C["leaf"], 4)
    for k in range(8):
        fx = gx + 100 + k * 72
        fy = sy + 4 - 18 * hash01(k, 3)
        for p in range(5):
            a = p * TAU / 5
            core.circle(c, fx + math.cos(a) * 12, fy + math.sin(a) * 12, 10)
        fs(c, ["#ff6f8a", "#ffffff", "#ffd27a"][k % 3], 3)
        core.circle(c, fx, fy, 6)
        fs(c, "#f2a93b", 2)


def bedroom_window_exterior(ctx, t=0.0, layer="bg", light=1.0):
    """His bedroom window seen from OUTSIDE (world 1080 x 1920).

    layer "bg" = dim room behind the glass + the siding wall (complete
    picture); layer "fg" = the same wall with the glass cut out, frame,
    meeting rail, sill, flower box AND the glass reflection streaks: draw it
    over the character so only what is behind the glass shows.
    light 0..1 dims the interior further when < 1."""
    W, H = WINDOW_EXT_W, WINDOW_EXT_H
    gx, gy, gw, gh = _WX
    if layer == "bg":
        _overscan(ctx, -200, -40, W + 200, H, C["house_trim"], C["siding"], C["siding"], C["siding"])
        cached_or_live(ctx, "window_ext_in", gx - 4, gy - 4, gw + 8, gh + 8, _wext_interior)
        if light < 1:
            ctx.rectangle(gx, gy, gw, gh)
            core.fill(ctx, (0.08, 0.06, 0.14, 0.5 * (1 - light)))
        static_layer(ctx, "window_ext_wall", -200, -40, W + 400, H + 40, lambda c: _wext_wall(c, False))
    elif layer == "fg":
        _overscan(ctx, -200, -40, W + 200, H, C["house_trim"], C["siding"], C["siding"], C["siding"])
        static_layer(ctx, "window_ext_wall_fg", -200, -40, W + 400, H + 40, lambda c: _wext_wall(c, True))


STREET_W, STREET_H = 1080, 1920
STREET_MARKS = {
    "size": (STREET_W, STREET_H),
    "char_scale": 0.3,           # someone running across the lawn below
    "lawn_feet_y": 1450,         # feet line for the lawn run (x 120..960)
    "lawn_x": (120, 960),
    "sidewalk_y": 1272,
    "street_y": 1205,            # road surface (car wheels)
    "far_sidewalk_y": 1030,
    "bird": (660, 1420),
    "sill_y": 1530,              # interior window sill when frame=True
    "cam": {"default": (540, 960, 1.0)},
}


def _car(c, x, y, s=1.0, col="#7fb2e8"):
    """Cute parked car, side view. ANCHOR = ground under the middle."""
    with core.saved(c, x, y, s):
        blob(c, [(-190, -40), (-180, -110), (-110, -120), (-70, -190), (70, -192), (120, -120),
                 (190, -104), (196, -40)], col, 5, tension=0.3)
        polyf(c, [(-60, -178), (-8, -178), (-8, -122), (-96, -122)], "#d7f0ff", 4)
        polyf(c, [(8, -178), (60, -178), (100, -122), (8, -122)], "#d7f0ff", 4)
        line(c, [(-190, -64), (196, -64)], mixc(col, "#000000", 0.2), 5)
        ell(c, 186, -84, 10, 12, "#fff3c4", 3)
        for wx in (-110, 120):
            core.circle(c, wx, -36, 40); fs(c, "#2b2b38", 5)
            core.circle(c, wx, -36, 16); fs(c, "#c9ced8", 3)


def _street_static(c, frame):
    W, H = STREET_W, STREET_H
    core.vgradient(c, "#79c4f2", "#cfefff", -100, -100, W + 200, 1100)
    _glow(c, 900, 120, 380, "#fff6c8", 0.55)
    core.circle(c, 900, 120, 70); core.fill(c, "#fff6c8")
    _cloud(c, 220, 240, 1.1)
    _cloud(c, 640, 150, 0.7)
    _cloud(c, 1000, 380, 0.8)
    # distant rooftops
    for k in range(7):
        x = -60 + k * 180
        polyf(c, [(x, 760), (x + 90, 690 - 30 * hash01(k, 3)), (x + 180, 760)], "#b6c6e6", 0)
    c.rectangle(-100, 740, W + 200, 60)
    core.fill(c, "#b6c6e6")
    c.rectangle(-100, 790, W + 200, 230)
    core.fill(c, C["grass_sh"])
    # houses across the street
    _house_far(c, -40, 1010, 420, 300, "#f2b6a0", "#7a6a9a", 1, 5)
    _house_far(c, 440, 1010, 330, 260, "#bfe0c0", "#c0453f", 2, 5)
    _house_far(c, 820, 1010, 360, 290, "#d6c3ea", "#5d6390", 3, 5)
    for bx in (60, 300, 520, 900):
        blob(c, [(bx - 70, 1012), (bx - 60, 960), (bx, 940), (bx + 60, 960), (bx + 70, 1012)],
             C["leaf"], 4)
    _tree(c, 410, 1010, 1.15, seed=7)
    # mailbox
    rect(c, 790, 950, 16, 70, "#8a6a4a", 3)
    rect(c, 766, 920, 64, 40, "#5f86c4", 4, r=12)
    # far sidewalk, curb, road
    c.rectangle(-100, 1010, W + 200, 40)
    fs(c, C["walk"], 4)
    c.rectangle(-100, 1050, W + 200, 190)
    core.fill(c, C["road"])
    for k in range(6):
        rect(c, -40 + k * 220, 1140, 120, 14, "#f6efe0", 0, r=6)
    c.rectangle(-100, 1050, W + 200, 10)
    core.fill(c, C["road_sh"])
    _car(c, 760, 1205, 1.0, "#ff8f6a")
    # telephone pole + wires
    rect(c, 140, 520, 26, 540, C["bark"], 4)
    rect(c, 90, 560, 126, 18, C["bark"], 4)
    for (y0, y1) in ((566, 620), (566, 650)):
        curve(c, [(150, y0), (600, y0 + 60), (1180, y1)], "#4a4458", 3)
        curve(c, [(150, y0), (-100, y0 + 40)], "#4a4458", 3)
    # near curb + sidewalk + his fence + lawn
    c.rectangle(-100, 1238, W + 200, 64)
    fs(c, C["walk"], 4)
    for k in range(7):
        line(c, [(-40 + k * 190, 1238), (-60 + k * 190, 1300)], C["walk_sh"], 3)
    c.rectangle(-100, 1300, W + 200, 700)
    core.fill(c, C["grass"])
    for k in range(40):
        gx = hash01(k, 9) * W
        gy = 1360 + hash01(k, 10) * 380
        line(c, [(gx, gy), (gx + 6, gy - 16)], C["grass_sh"], 4)
    # picket fence between the sidewalk and his lawn (we look down over it)
    for k in range(-1, 18):
        px = k * 64
        polyf(c, [(px, 1336), (px, 1290), (px + 18, 1272), (px + 36, 1290), (px + 36, 1336)],
              C["fence"], 4)
    rect(c, -100, 1302, W + 200, 14, C["fence"], 3.5)
    if frame:
        _street_frame(c)


def _street_frame(c):
    W, H = STREET_W, STREET_H
    trim = C["trim"]
    # interior window trim around the view + curtains + sill
    c.rectangle(-200, -200, W + 400, H + 400)
    c.rectangle(W - 70, 70, -(W - 140), 1440)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fs(c, trim, 6)
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    rect(c, 70, 70, W - 140, 1440, None, 6)
    rect(c, -40, 1500, W + 80, 60, trim, 6, r=8)
    c.rectangle(-200, 1560, W + 400, H)
    core.fill(c, C["bd_wall"])
    for side in (-1, 1):
        bx = 0 if side < 0 else W
        blob(c, [(bx, -40), (bx - side * 150, -40), (bx - side * 110, 700), (bx - side * 170, 1620),
                 (bx, 1620)], C["curtain"], 6, tension=0.3)
        curve(c, [(bx - side * 70, 0), (bx - side * 60, 700), (bx - side * 100, 1580)], C["curtain_sh"], 6)


def street_view(ctx, t=0.0, layer="bg", frame=True, leaf=True, bird=True):
    """The empty sunny street from his window (world 1080 x 1920).

    frame=True wraps it in his interior window frame + curtains. Animated: a
    drifting leaf and a hopping bird (leaf / bird toggles). layer "fg" is
    empty (people on the lawn are in front of everything)."""
    if layer != "bg":
        return
    W, H = STREET_W, STREET_H
    _overscan(ctx, -200, -200, W + 200, H + 200, "#79c4f2", C["bd_wall"], C["trim"], C["trim"])
    static_layer(ctx, ("street_view", bool(frame)), -200, -200, W + 400, H + 400,
                 lambda c: _street_static(c, frame))
    if bird:
        bx, by = STREET_MARKS["bird"]
        p = t % 3.2
        face, hop, dx, peck = 1, 0.0, 0.0, 0.0
        if p < 0.5:
            k = (p % 0.25) / 0.25
            hop = 4 * k * (1 - k) * 22
            dx = (int(p / 0.25) + k) * 20
        elif p < 1.6:
            dx = 40
            peck = 0.45 if (p - 0.5) % 0.55 < 0.18 else 0.0
        elif p < 2.1:
            face = -1
            q = p - 1.6
            k = (q % 0.25) / 0.25
            hop = 4 * k * (1 - k) * 22
            dx = 40 - (int(q / 0.25) + k) * 20
        else:
            face = -1
            peck = 0.45 if (p - 2.1) % 0.55 < 0.18 else 0.0
        _bird(ctx, bx + dx, by - hop, (face, 1.0), peck)
    if leaf:
        p = (t / 7.0) % 1.0
        lx = 380 + p * 520 + 60 * math.sin(p * 9)
        ly = 640 + p * 640 + 30 * math.sin(p * 13)
        props.leaf(ctx, lx, ly, 0.9, math.sin(t * 2.2) * 0.9, "#e9a23b")
    if frame:
        # draw the frame over the animated bits again only where they could overlap it
        pass


def _bird(ctx, x, y, s=1.0, peck=0.0):
    with core.saved(ctx, x, y, s):
        ell(ctx, 0, -18, 22, 15, "#7a5a4a", 3.5)
        with core.saved(ctx, 16, -28, 1.0, peck):
            core.circle(ctx, 0, 0, 11); fs(ctx, "#7a5a4a", 3.5)
            polyf(ctx, [(9, -2), (20, 2), (9, 5)], "#f2a93b", 2)
            core.circle(ctx, 3, -3, 2.4); core.fill(ctx, INK)
        polyf(ctx, [(-18, -22), (-36, -30), (-30, -14)], "#5a3e30", 3)
        ell(ctx, -2, -12, 12, 7, "#e3c2a6", 0)
        line(ctx, [(-4, -4), (-6, 4)], INK, 2.5)
        line(ctx, [(4, -4), (6, 4)], INK, 2.5)


# ============================================================================
# 3. HOUSE EXTERIOR (front view, side wall at the left end)
# ============================================================================
HOUSE_W, HOUSE_H = 2600, 2300
_HG = 1500                     # ground line at the facade
_H_FACADE = (640, 440, 1560, 1060)   # x, y_top(eave), w, h
_H_WIN = [(760, 1020, 230, 250), (1100, 1020, 230, 250), (1870, 1020, 230, 250)]
_H_DOOR = (1480, 990, 220, 440)      # x, top, w, h (bottom = porch deck 1430)
_H_BEDWIN = (1085, 560, 260, 300)
HOUSE_MARKS = {
    "size": (HOUSE_W, HOUSE_H),
    "char_scale": 0.45,
    "ground_y": _HG,               # facade base
    "lawn_feet_y": 1600,           # feet line for people standing on the lawn at the house
    "lawn_rect": (640, 1520, 1580, 270),
    "windows": [(x, y, w, h) for (x, y, w, h) in _H_WIN],
    "window_push": [(x + w / 2, 1580) for (x, y, w, h) in _H_WIN],   # feet spots to push each window
    "window_sill_y": 1270,
    "door": _H_DOOR,
    "door_gap": (1486, 1424, 208, 6),
    "porch_feet_y": 1452,
    "porch_x": (1400, 1780),
    "doormat": (1590, 1458),
    "doorway_feet": (1590, 1432),
    "steps": [(1590, 1508), (1590, 1538)],
    "path_feet": (1590, 1660),
    "gate": (1590, 1800),
    "fence_y": 1800,
    "sidewalk_y": 1840,
    "street_y": 2150,              # where van wheels touch the road
    "van_spots": [(860, 2150), (1980, 2150)],
    "van_scale": 0.45,
    "boss_feet": (1420, 2210),
    "bedroom_window": _H_BEDWIN,
    "side_wall": (0, 440, 640, 1060),
    "dent": (330, 1200),           # centre of the body-shaped dent (s~0.45 body)
    "side_feet": (330, 1560),      # feet of someone flattened against the side wall
    "rock": (1880, 1690),
    "trash_cans": [(2300, 1790), (2440, 1796)],
    "streetlight": (2520, 1850),
    "hedge_trip": (1210, 1520),
    "cam": {
        "wide": (1300, 1150, 0.62),
        "s02_side": (380, 1150, 1.25),
        "s03_windows": (1430, 1240, 1.15),
        "win1": (875, 1250, 1.6), "win2": (1215, 1250, 1.6), "win3": (1985, 1250, 1.6),
        "porch": (1590, 1240, 2.3),
        "s08_vans": (1420, 1640, 0.9),
    },
}


def _h_window(c, x, y, w, h, broken=False, curtain="#ffd27a", seed=0, lw=4):
    trim = C["house_trim"]
    rect(c, x - 22, y - 24, w + 44, h + 48, trim, lw + 1, r=4)
    rect(c, x - 34, y + h + 10, w + 68, 22, trim, lw, r=4)
    # glass (interior: warm curtains)
    c.save()
    c.rectangle(x, y, w, h)
    c.clip()
    c.rectangle(x, y, w, h)
    core.fill(c, "#4a5a7a")
    blob(c, [(x - 10, y), (x + w * 0.32, y), (x + w * 0.22, y + h * 0.6), (x + w * 0.3, y + h),
             (x - 10, y + h)], curtain, 3)
    blob(c, [(x + w + 10, y), (x + w * 0.68, y), (x + w * 0.78, y + h * 0.6), (x + w * 0.7, y + h),
             (x + w + 10, y + h)], curtain, 3)
    if broken:
        # jagged hole with dark interior + glass teeth around the edge
        pts = []
        n = 16
        for i in range(n):
            a = i / n * TAU
            r = 0.62 + 0.3 * hash01(i, seed + 5)
            pts.append((x + w / 2 + math.cos(a) * w * 0.5 * r, y + h / 2 + math.sin(a) * h * 0.5 * r))
        polyf(c, pts, "#2a2238", 3)
        for i in range(0, n, 3):
            line(c, [pts[i], (x + w / 2 + (pts[i][0] - x - w / 2) * 1.7,
                              y + h / 2 + (pts[i][1] - y - h / 2) * 1.7)], "#ffffff", 3)
    else:
        polyf(c, [(x + 20, y), (x + 70, y), (x + 20, y + 90), (x - 30, y + 90)], (1, 1, 1, 0.3), 0)
        polyf(c, [(x + 120, y), (x + 140, y), (x + 60, y + 150), (x + 40, y + 150)], (1, 1, 1, 0.22), 0)
    c.restore()
    rect(c, x, y, w, h, None, lw)
    line(c, [(x + w / 2, y), (x + w / 2, y + h)], INK, lw + 8)
    line(c, [(x + w / 2, y), (x + w / 2, y + h)], trim, lw + 2)
    line(c, [(x, y + h / 2), (x + w, y + h / 2)], INK, lw + 8)
    line(c, [(x, y + h / 2), (x + w, y + h / 2)], trim, lw + 2)


def _h_bush(c, x, y, w, h, seed=0, col=None, sh=None, lw=4):
    col, sh = col or C["leaf"], sh or C["leaf_sh"]
    n = max(3, int(w / 70))
    pts = [(x, y)]
    for i in range(n + 1):
        u = i / n
        bump = h * (0.75 + 0.25 * hash01(i, seed))
        pts.append((x + w * u, y - bump * math.sin(math.pi * (0.15 + 0.7 * u)) - h * 0.15))
    pts.append((x + w, y))
    blob(c, pts, col, lw, tension=0.6)
    for i in range(n):
        core.circle(c, x + w * (i + 0.5) / n, y - h * 0.55 + 10 * hash01(i, seed + 2), 9)
    core.fill(c, mixc(col, "#ffffff", 0.18))
    c.rectangle(x + 6, y - 14, w - 12, 12)
    core.fill(c, core.alpha(sh, 0.7))


def _h_static(c, broken):
    W, H = HOUSE_W, HOUSE_H
    G = _HG
    # sky
    core.vgradient(c, "#6fbdf0", "#c8ecff", -400, -500, W + 800, 2000)
    core.circle(c, 2380, 120, 90)
    core.fill(c, "#fff6c8")
    _glow(c, 2380, 120, 360, "#fff6c8", 0.5)
    _cloud(c, 330, 140, 1.2)
    _cloud(c, 1500, 70, 0.9)
    _cloud(c, 2150, 330, 0.8)
    # far hedge line + trees behind the house
    _tree(c, 2440, 1480, 2.4, seed=3)
    _h_bush(c, 2180, G + 6, 520, 200, seed=5, col=C["leaf_sh"], sh="#2f6232")
    _h_bush(c, -420, G + 6, 600, 200, seed=6, col=C["leaf_sh"], sh="#2f6232")
    _tree(c, 140, 1480, 1.9, seed=9)
    # ---- lawn, path, sidewalk, street
    c.rectangle(-400, G, W + 800, 1800 - G)
    core.fill(c, C["grass"])
    for k in range(-2, 16):
        x0 = k * 220
        polyf(c, [(x0, G), (x0 + 110, G), (x0 + 30, 1800), (x0 - 80, 1800)],
              mixc(C["grass"], "#ffffff", 0.08), 0)
    for k in range(70):
        gx = -300 + hash01(k, 21) * (W + 600)
        gy = G + 30 + hash01(k, 22) * 250
        line(c, [(gx, gy), (gx + 5, gy - 14)], C["grass_sh"], 3.5)
    # flowers dotted on the lawn
    for k in range(18):
        fx = 700 + hash01(k, 31) * 1500
        fy = G + 60 + hash01(k, 32) * 210
        core.circle(c, fx, fy, 6)
        core.fill(c, ["#ffffff", "#ffd27a", "#ff9aac"][k % 3])
    # driveway
    polyf(c, [(2240, G - 10), (2600 + 400, G - 10), (2600 + 400, 1900), (2200, 1900)], "#c9c3b6", 4)
    for k in range(4):
        line(c, [(2240 - k * 12, G + 70 + k * 100), (3000, G + 70 + k * 100)], "#b3ac9d", 3)
    # stone path from steps to gate
    for k in range(6):
        yy = 1575 + k * 40
        ell(c, 1590 + (12 if k % 2 else -12), yy, 70 + k * 6, 14 + k * 1.5, C["walk"], 3.5)
    # sidewalk + curb + street
    c.rectangle(-400, 1800, W + 800, 80)
    fs(c, C["walk"], 4)
    for k in range(-1, 15):
        line(c, [(k * 210, 1800), (k * 210 - 20, 1880)], C["walk_sh"], 3)
    c.rectangle(-400, 1880, W + 800, 24)
    fs(c, "#e9e3d6", 4)
    c.rectangle(-400, 1904, W + 800, 800)
    core.fill(c, C["road"])
    c.rectangle(-400, 1904, W + 800, 18)
    core.fill(c, C["road_sh"])
    for k in range(-1, 9):
        rect(c, k * 360 + 60, 2215, 200, 18, "#f6efe0", 0, r=8)

    # ---- side wall (left end, in shade)
    sx0, sx1 = -40, 640
    _siding(c, sx0, 440, sx1 - sx0, G - 440, mixc(C["siding"], C["siding_sh"], 0.55), C["siding_sh"],
            mixc(C["siding_line"], "#000000", 0.08), step=52)
    # gable end triangle (ridge height matches the front roof ridge)
    polyf(c, [(sx0 - 30, 452), (320, 150), (sx1 + 30, 452)], C["roof_sh"], 6)
    polyf(c, [(sx0 + 40, 440), (320, 196), (sx1 - 40, 440)], mixc(C["siding"], C["siding_sh"], 0.55), 4)
    for k in range(4):
        yy = 290 + k * 40
        hw = (yy - 196) / (440 - 196) * 270
        line(c, [(320 - hw, yy), (320 + hw, yy)], C["siding_sh"], 4)
    core.circle(c, 320, 330, 34); fs(c, C["house_trim"], 4)
    core.circle(c, 320, 330, 22); fs(c, "#4a5a7a", 3)
    rect(c, sx0, G - 40, sx1 - sx0, 40, "#a59a8a", 4)     # foundation
    rect(c, 120, G - 34, 90, 30, "#4a5a7a", 3.5, r=4)     # basement window
    rect(c, 470, 1230, 70, 90, "#c9ced8", 4, r=8)         # gas meter
    core.circle(c, 505, 1265, 18); fs(c, "#ffffff", 3)
    rect(c, 618, 450, 24, G - 450, "#e6e0d2", 4, r=6)     # downspout
    ell(c, 600, G + 4, 40, 10, "#e6e0d2", 3.5)
    # hose reel
    core.circle(c, 70, 1400, 50); fs(c, "#3ddc84", 5)
    core.circle(c, 70, 1400, 20); fs(c, "#2f9a60", 4)
    _h_bush(c, 360, G + 6, 260, 90, seed=12)

    # ---- front facade
    fx, fy, fw, fh = _H_FACADE
    _siding(c, fx, fy, fw, fh, C["siding"], C["siding_sh"], C["siding_line"], step=52)
    line(c, [(fx, fy), (fx, G)], INK, 6)
    rect(c, fx - 6, fy, 26, fh, C["house_trim"], 4)          # corner boards
    rect(c, fx + fw - 20, fy, 26, fh, C["house_trim"], 4)
    rect(c, fx, G - 40, fw, 40, "#a59a8a", 5)                # foundation
    rect(c, fx - 10, 930, fw + 20, 18, C["house_trim"], 4)   # floor band
    # roof (side-gabled) + front gable over the bedroom window
    polyf(c, [(fx - 50, fy + 12), (fx + 120, 170), (fx + fw - 120, 170), (fx + fw + 50, fy + 12)],
          C["roof"], 6)
    for k in range(1, 7):
        yy = 170 + k * 40
        u = (yy - 170) / (fy + 12 - 170)
        xa = lerp(fx + 120, fx - 50, u)
        xb = lerp(fx + fw - 120, fx + fw + 50, u)
        line(c, [(xa, yy), (xb, yy)], C["roof_sh"], 5)
        for kk in range(int((xb - xa) / 90)):
            xx = xa + 40 + kk * 90 + (45 if k % 2 else 0)
            if xx < xb - 10:
                line(c, [(xx, yy - 40), (xx, yy)], C["roof_sh"], 3.5)
    rect(c, fx - 60, fy, fw + 120, 26, C["house_trim"], 5, r=6)   # fascia/gutter
    # chimney
    rect(c, 1880, 70, 120, 200, "#b5544a", 5)
    rect(c, 1866, 56, 148, 30, "#99433b", 5, r=4)
    for k in range(4):
        line(c, [(1880, 110 + k * 40), (2000, 110 + k * 40)], "#99433b", 3)
    # front gable
    gx0, gx1, gpk = 990, 1440, 150
    polyf(c, [(gx0 - 40, fy + 30), ((gx0 + gx1) / 2, gpk - 20), (gx1 + 40, fy + 30)], C["roof_sh"], 6)
    polyf(c, [(gx0, fy + 30), ((gx0 + gx1) / 2, gpk + 30), (gx1, fy + 30)], C["siding"], 5)
    for k in range(5):
        yy = gpk + 70 + k * 52
        hw = (yy - gpk - 30) / (fy + 30 - gpk - 30) * (gx1 - gx0) / 2
        line(c, [((gx0 + gx1) / 2 - hw, yy), ((gx0 + gx1) / 2 + hw, yy)], C["siding_line"], 3.5)
    core.circle(c, (gx0 + gx1) / 2, 300, 40); fs(c, C["house_trim"], 4)
    core.circle(c, (gx0 + gx1) / 2, 300, 26); fs(c, "#4a5a7a", 3.5)
    line(c, [((gx0 + gx1) / 2 - 26, 300), ((gx0 + gx1) / 2 + 26, 300)], C["house_trim"], 5)
    # upstairs: bedroom window (shutters + flower box) and the second window
    bx, by, bw, bh = _H_BEDWIN
    for sxx in (bx - 70, bx + bw + 30):
        rect(c, sxx, by - 10, 40, bh + 20, "#6f86b8", 4, r=4)
        for k in range(7):
            line(c, [(sxx + 6, by + 14 + k * 44), (sxx + 34, by + 14 + k * 44)], "#566ea3", 4)
    _h_window(c, bx, by, bw, bh, curtain=C["curtain"])
    # tiny poster + monitor glow seen through his window
    rect(c, bx + 92, by + 30, 50, 66, "#ffe9a6", 3)
    _glow(c, bx + bw * 0.5, by + bh * 0.7, 120, "#bfe6ff", 0.35)
    rect(c, bx - 10, by + bh + 34, bw + 20, 50, "#b5544a", 4, r=6)
    for k in range(6):
        core.circle(c, bx + 18 + k * 45, by + bh + 30, 12)
        fs(c, ["#ff6f8a", "#ffffff", "#ffd27a"][k % 3], 2.5)
    _h_window(c, 1880, 580, 220, 280, curtain="#bfe0c0")
    # ground floor windows (broken one is a jagged hole)
    for i, (x, y, w, h) in enumerate(_H_WIN):
        _h_window(c, x, y, w, h, broken=(broken == i), curtain="#ffd27a", seed=i)
    # house number + porch light
    rect(c, 1730, 1080, 60, 40, C["house_trim"], 3.5, r=6)
    core.text(c, "42", 1760, 1110, 30, INK, "ui")
    # ---- porch
    px0, px1 = 1400, 1780
    rect(c, px0 - 20, 1430, px1 - px0 + 40, 70, "#d9cdb8", 5)            # deck front
    polyf(c, [(px0 - 20, 1430), (px1 + 20, 1430), (px1 + 30, 1440), (px0 - 30, 1440)], "#efe6d2", 4)
    rect(c, 1500, 1500, 180, 30, "#efe6d2", 4)                             # step 1
    rect(c, 1488, 1530, 204, 30, "#e2d7c2", 4)                             # step 2
    # porch roof + posts
    rect(c, px0 - 50, 930, px1 - px0 + 100, 40, C["house_trim"], 5, r=4)
    polyf(c, [(px0 - 60, 930), (px1 + 60, 930), (px1 + 20, 880), (px0 - 20, 880)], C["roof"], 5)
    for pxx in (px0 - 10, px1 - 10):
        rect(c, pxx, 970, 20, 460, C["house_trim"], 4)
    # porch railings (low)
    for (ra, rb) in ((px0 - 10, 1470), (1710, px1 + 10)):
        rect(c, ra, 1300, rb - ra, 16, C["house_trim"], 3.5)
        for k in range(int((rb - ra) / 26)):
            rect(c, ra + 8 + k * 26, 1316, 8, 114, C["house_trim"], 2.5)
    # door frame (the doorway opening is cleared; layer "back" shows inside)
    dx, dt, dw, dh = _H_DOOR
    rect(c, dx - 30, dt - 34, dw + 60, dh + 34, C["house_trim"], 5)
    # porch lamp
    rect(c, dx + dw + 44, dt + 60, 30, 50, "#2f2b3d", 3.5, r=6)
    ell(c, dx + dw + 59, dt + 92, 10, 14, "#fff3c4", 2.5)
    # foundation hedges under the ground floor windows
    for (x, y, w, h) in _H_WIN:
        _h_bush(c, x - 50, G + 4, w + 100, 120, seed=int(x))
    _h_bush(c, 2110, G + 4, 120, 90, seed=77)
    # mailbox by the gate
    rect(c, 1700, 1690, 16, 110, "#8a6a4a", 3.5)
    rect(c, 1670, 1650, 76, 46, "#c0453f", 4, r=14)
    # clear the doorway
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(dx, dt, dw, dh)
    c.fill()
    c.restore()


def _h_back(c):
    dx, dt, dw, dh = _H_DOOR
    c.rectangle(dx - 10, dt - 10, dw + 20, dh + 20)
    core.fill(c, C["lv_wall_sh"])
    _glow(c, dx + dw / 2, dt + 120, 200, "#ffd27a", 0.45)
    rect(c, dx - 10, dt + 300, dw + 20, dh, C["lv_wain_sh"], 0)
    line(c, [(dx - 10, dt + 300), (dx + dw + 10, dt + 300)], INK, 3)
    rect(c, dx + 120, dt + 120, 60, 80, "#c98d4a", 3)
    c.rectangle(dx - 10, dt + dh - 30, dw + 20, 40)
    core.fill(c, C["wood_sh"])


def _h_door_panel(ctx, opening):
    dx, dt, dw, dh = _H_DOOR
    q = door_quad(dx, dt, dt + dh, dw, opening, (1300, 900), D=2600, toward=False)
    polyf(ctx, q, C["door_red"], 5)
    if opening < 0.97:
        def P(u, v):
            top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
            bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
            return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
        polyf(ctx, [P(0.18, 0.08), P(0.82, 0.08), P(0.82, 0.30), P(0.18, 0.30)], "#ffe9a6", 3.5)
        for (v0, v1) in ((0.40, 0.62), (0.70, 0.92)):
            polyf(ctx, [P(0.18, v0), P(0.82, v0), P(0.82, v1), P(0.18, v1)], None, 3.5,
                  sc=C["door_red_sh"])
        kx, ky = P(0.86, 0.55)
        core.circle(ctx, kx, ky, 10 * (1 - 0.5 * opening))
        fs(ctx, "#f2c14e", 3)
        # the gap under the door
        if opening < 0.05:
            ctx.rectangle(dx + 6, dt + dh - 6, dw - 12, 6)
            core.fill(ctx, "#2a2238")


def _h_door_casing(ctx):
    dx, dt, dw, dh = _H_DOOR
    t = 30
    polyf(ctx, [(dx - t, dt - 34), (dx + dw + t, dt - 34), (dx + dw + t, dt + dh), (dx + dw, dt + dh),
                (dx + dw, dt), (dx, dt), (dx, dt + dh), (dx - t, dt + dh)], C["house_trim"], 5)


def _h_fence(c):
    gate0, gate1 = 1530, 1650
    y = 1800
    for k in range(-14, 61):
        px = k * 38
        if px > 2210:
            break
        if gate0 - 30 < px < gate1:
            continue
        polyf(c, [(px, y), (px, y - 160), (px + 12, y - 184), (px + 24, y - 160), (px + 24, y)],
              C["fence"], 3.5)
    for yy in (y - 140, y - 60):
        for (a, b) in ((-560, gate0 - 30), (gate1 + 8, 2234)):
            rect(c, a, yy, b - a, 16, C["fence"], 3.5)
    # gate (slightly ajar) + posts
    for (px, ph) in ((gate0 - 40, 210), (gate1 + 4, 210), (2216, 210)):
        rect(c, px, y - ph, 28, ph, C["fence"], 4)
        rect(c, px - 6, y - ph - 14, 40, 18, C["fence"], 3.5, r=4)
    for k in range(4):
        polyf(c, [(gate0 + k * 30, y - 6), (gate0 + k * 30, y - 150), (gate0 + 12 + k * 30, y - 170),
                  (gate0 + 24 + k * 30, y - 150), (gate0 + 24 + k * 30, y - 6)], C["fence_sh"], 3)
    rect(c, gate0, y - 120, 120, 14, C["fence_sh"], 3)


def _h_damage(ctx, t, damage):
    if damage <= 0:
        return
    d = clamp(damage)
    for i, kind in enumerate(["paper", "plank", "paper", "can", "chunk", "paper", "plank", "paper",
                              "brick", "paper", "shard", "paper"]):
        if hash01(i, 61) > d + 0.15:
            continue
        x = 700 + hash01(i, 62) * 1900
        y = 1560 + hash01(i, 63) * 330
        if 1790 < y < 1810:
            y += 30
        props.debris(ctx, x, y, 0.5 + 0.2 * hash01(i, 64), kind, hash01(i, 65) * 6, seed=i)
    # torn lawn divots
    for i in range(3):
        x = 900 + i * 520
        ell(ctx, x, 1700 + 30 * i, 60 * d, 14 * d, "#8a6a4a", 3)


def _h_dent(ctx, dent):
    if dent <= 0:
        return
    x, y = HOUSE_MARKS["dent"]
    d = clamp(dent)
    with core.saved(ctx, x, y, 1.0):
        sh = mixc(C["siding_sh"], "#3a2a20", 0.35)
        # splat silhouette (head, spread arms, legs) ~ 0.45-scale body
        pts = [(0, -250), (40, -230), (46, -180), (120, -210), (200, -170), (190, -140), (60, -120),
               (60, 40), (120, 200), (90, 220), (10, 80), (-20, 80), (-90, 220), (-120, 200),
               (-60, 40), (-60, -120), (-190, -140), (-200, -170), (-120, -210), (-46, -180),
               (-40, -230)]
        core.smooth_path(ctx, pts, closed=True, tension=0.35)
        fs(ctx, core.alpha(sh, 0.85 * d), 4 * d)
        core.circle(ctx, 0, -200, 48)
        fs(ctx, core.alpha(sh, 0.85 * d), 0)
        # highlight rim + cracks + popped boards
        curve(ctx, [(-40, -238), (0, -258), (40, -238)], core.alpha("#fff3c4", d), 5)
        for (a, L) in ((0.3, 120), (2.6, 140), (4.0, 100), (5.4, 110)):
            px0, py0 = math.cos(a) * 150, math.sin(a) * 180 - 40
            line(ctx, [(px0, py0), (px0 + math.cos(a) * L * 0.5, py0 + math.sin(a) * L * 0.4 + 10),
                       (px0 + math.cos(a) * L, py0 + math.sin(a) * L * 0.6)], core.alpha(INK, d), 4)
        with core.saved(ctx, 170, 80, 1.0, 0.18 * d):
            rect(ctx, -60, -10, 120, 22, core.alpha(C["siding"], d), 4 * d)


def house_exterior(ctx, t=0.0, layer="bg", broken=None, door_open=0.0, damage=0.0, dent=0.0,
                   parts=None, porch_light=False, rock=True):
    """Two-storey house, front view (world 2600 x 2300, people at s=0.45).

    layer "bg" | "back" (only the hall behind the front door) | "house" (bg
    without "back") | "fg" (parts: "fence", "door" casing, "hedge").
    broken: index 0..2 of the smashed ground-floor window, or None.
    door_open 0..1 (opens inward, away from us), damage 0..1 (knocked cans,
    shattered leaning streetlight, debris), dent 0..1 (body dent in the side
    wall, left end), porch_light, rock (draw the lawn rock; False once
    picked up - props.rock at s=0.6 matches it).
    """
    W, H = HOUSE_W, HOUSE_H
    if layer in ("bg", "back"):
        dx, dt, dw, dh = _H_DOOR
        cached_or_live(ctx, "house_back", dx - 12, dt - 12, dw + 24, dh + 24, _h_back)
        if layer == "back":
            return
    if layer in ("bg", "house"):
        _overscan(ctx, -400, -500, W + 400, H + 400, "#6fbdf0", C["road"], C["grass"], C["grass"])
        static_layer(ctx, ("house", broken), -400, -500, W + 800, H + 900, lambda c: _h_static(c, broken))
        _h_door_panel(ctx, door_open)
        _h_dent(ctx, dent)
        # trash cans + streetlight (live, they change with damage)
        (c1x, c1y), (c2x, c2y) = HOUSE_MARKS["trash_cans"]
        props.trash_can(ctx, c1x, c1y, 0.55, knocked=damage, dir=-1, seed=1)
        props.trash_can(ctx, c2x, c2y, 0.55, knocked=damage * 0.9, dir=1, seed=2)
        if rock:
            rx, ry = HOUSE_MARKS["rock"]
            props.rock(ctx, rx, ry, 0.6)
        _h_damage(ctx, t, damage)
        lx, ly = HOUSE_MARKS["streetlight"]
        props.streetlight(ctx, lx, ly, 0.45, t, broken=damage, on=False)
        if porch_light:
            dx, dt, dw, dh = _H_DOOR
            _glow(ctx, dx + dw + 59, dt + 92, 120, "#ffe7a0", 0.5)
        static_layer(ctx, "house_fence", -560, 1580, 2800, 240, _h_fence)
        return
    if layer == "fg":
        parts = parts or ("fence", "door")
        if "door" in parts:
            _h_door_casing(ctx)
            if door_open > 0.02:
                _h_door_panel(ctx, door_open)
        if "hedge" in parts:
            cached_or_live(ctx, "house_hedges", 660, 1360, 1580, 150,
                        lambda c: [_h_bush(c, x - 50, _HG + 4, w + 100, 120, seed=int(x)) for (x, y, w, h) in _H_WIN])
        if "fence" in parts:
            cached_or_live(ctx, "house_fence_fg", -560, 1580, 2800, 240, _h_fence)


# ============================================================================
# 4. LIVING ROOM / KITCHEN (s04)
# ============================================================================
LIVING_W, LIVING_H = 2800, 1920
_LV_CEIL, _LV_FLOOR = 300, 1330
_LV_VP = (1400, 860)
_LV_EXT = (500, 800, 600, 800)
_LV_WIN = (90, 470, 360, 470)
_LV_COUNTER = (1560, 1050, 420, 390)   # x, top y, w, h
_LV_DRAWERS = [(1574, 1086, 128, 66), (1712, 1086, 128, 66), (1850, 1086, 118, 66)]
_LV_STAIRS = dict(x0=2250, y0=1330, n=9, rise=81, run=56)
_LV_LANDING_Y = _LV_STAIRS["y0"] - _LV_STAIRS["n"] * _LV_STAIRS["rise"]
LIVING_MARKS = {
    "size": (LIVING_W, LIVING_H),
    "char_scale": 0.75,
    "ceiling_y": _LV_CEIL,
    "floor_y": _LV_FLOOR,
    "stand_y": 1520,
    "window": _LV_WIN,
    "heap_feet": (300, 1500),        # Emb in a heap under the broken window
    "imp_sit": (640, 1560),          # Impulsivity sitting, facing the window heap
    "pet_bed": (700, 1560),
    "couch": (960, 990, 520, 460),
    "coffee_table_top": (1220, 1408),
    "plates": (1220, 1404),          # plates_stack anchor (bottom centre) on the table
    "counter": _LV_COUNTER,
    "drawer": _LV_DRAWERS[1],        # the top drawer that opens
    "drawer_hands": (1776, 1130),
    "counter_feet": (1776, 1520),
    "table": (2000, 1265, 360, 335), # dining table x, top y, w, h(to floor)
    "under_table": (2180, 1450),     # where you peek under
    "table_crouch_feet": (2080, 1600),
    "stairs_bottom": (2250, 1330),
    "stairs_top": (2250 + 9 * 56, _LV_LANDING_Y),
    "landing_wall": (2560, 160, 700, _LV_LANDING_Y - 160),   # rect for the moving shadow
    "landing_floor_y": _LV_LANDING_Y,
    "cam": {
        "low_heap": (420, 1250, 1.5),
        "reveal_up": (560, 1000, 1.15),
        "tiptoe_wide": (1250, 1060, 0.62),
        "plates": (1220, 1180, 1.5),
        "drawer": (1776, 1100, 1.5),
        "table": (2150, 1250, 1.3),
        "stairs": (2470, 820, 1.1),
    },
}


def _lv_static(c, broken):
    W, H = LIVING_W, LIVING_H
    CEIL, FLOOR = _LV_CEIL, _LV_FLOOR
    _room_shell(c, W, H, CEIL, FLOOR, _LV_VP, C["lv_wall"], C["lv_wall_sh"], "#e2ddd0", "#cfc8b6",
                "#c4895a", "#a36d42", _LV_EXT, side=False)
    # wallpaper diamonds + wainscot (lower third)
    for i in range(0, W + 80, 80):
        for k in range(8):
            yy = CEIL + 60 + k * 90
            if yy > 900:
                break
            ox = 40 if k % 2 else 0
            polyf(c, [(i + ox, yy - 12), (i + ox + 9, yy), (i + ox, yy + 12), (i + ox - 9, yy)],
                  C["lv_paper"], 0)
    rect(c, 0, 900, W, FLOOR - 900, C["lv_wain"], 0)
    for i in range(0, W, 140):
        rect(c, i + 18, 940, 104, 330, None, 3.5, sc=C["lv_wain_sh"], r=6)
    rect(c, -10, 890, W + 20, 22, C["lv_wain_sh"], 4)
    # right side beyond the world: the wall continues (stairwell)
    c.rectangle(W, CEIL, _LV_EXT[2], FLOOR - CEIL)
    core.fill(c, C["lv_wall_sh"])

    # ---- broken front window with the yard outside
    wx, wy, ww, wh = _LV_WIN
    rect(c, wx - 30, wy - 30, ww + 60, wh + 60, C["trim"], 5, r=4)
    c.save()
    c.rectangle(wx, wy, ww, wh)
    c.clip()
    core.vgradient(c, "#7cc6f2", "#d2f0ff", wx, wy, ww, wh * 0.6)
    _cloud(c, wx + 120, wy + 90, 0.5)
    c.rectangle(wx, wy + wh * 0.55, ww, wh)
    core.fill(c, C["grass"])
    _house_far(c, wx - 20, wy + wh * 0.58, 220, 120, "#d6c3ea", "#5d6390", 4, 3)
    for k in range(9):
        px = wx + k * 42
        polyf(c, [(px, wy + wh * 0.82), (px, wy + wh * 0.68), (px + 10, wy + wh * 0.64),
                  (px + 20, wy + wh * 0.68), (px + 20, wy + wh * 0.82)], C["fence"], 3)
    if broken:
        # glass remains only as jagged teeth around the frame
        pts = [(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)]
        teeth = [(wx, wy), (wx + 90, wy), (wx + 40, wy + 70), (wx + 150, wy), (wx + ww, wy),
                 (wx + ww, wy + 120), (wx + ww - 60, wy + 60), (wx + ww, wy + 230), (wx + ww, wy + wh),
                 (wx + ww - 120, wy + wh), (wx + ww - 160, wy + wh - 70), (wx + ww - 210, wy + wh),
                 (wx + 60, wy + wh), (wx + 20, wy + wh - 110), (wx, wy + wh - 60), (wx, wy + 200),
                 (wx + 50, wy + 150), (wx, wy + 110)]
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.close_path()
        c.move_to(*teeth[0])
        for p in reversed(teeth[1:]):
            c.line_to(*p)
        c.close_path()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        fs(c, (0.85, 0.95, 1.0, 0.55), 3)
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
    else:
        polyf(c, [(wx + 30, wy), (wx + 80, wy), (wx + 30, wy + 100), (wx - 20, wy + 100)], (1, 1, 1, 0.3), 0)
    c.restore()
    rect(c, wx, wy, ww, wh, None, 5)
    line(c, [(wx, wy + wh * 0.5), (wx + 30, wy + wh * 0.5)], C["trim"], 10)
    line(c, [(wx + ww - 30, wy + wh * 0.5), (wx + ww, wy + wh * 0.5)], C["trim"], 10)
    rect(c, wx - 50, wy + wh + 26, ww + 100, 26, C["trim"], 4, r=4)
    # curtains (one knocked askew)
    blob(c, [(wx - 60, wy - 50), (wx + 30, wy - 50), (wx + 10, wy + 300), (wx + 40, wy + wh + 90),
             (wx - 60, wy + wh + 90)], "#d9734f", 5, tension=0.3)
    blob(c, [(wx + ww + 60, wy - 50), (wx + ww - 20, wy - 50), (wx + ww - 70, wy + 240),
             (wx + ww - 10, wy + wh + 30), (wx + ww + 70, wy + wh + 90)], "#d9734f", 5, tension=0.3)
    rect(c, wx - 90, wy - 70, ww + 180, 18, "#8f5c33", 4, r=9)
    # sunlight from the window onto the floor + glass bits
    _sun_patch(c, [(wx + 20, FLOOR), (wx + ww + 20, FLOOR), (wx + ww + 260, 1700), (wx + 160, 1700)], 0.30)
    if broken:
        for i in range(14):
            gx = wx + 20 + hash01(i, 71) * (ww + 160)
            gy = FLOOR + 30 + hash01(i, 72) * 200
            with core.saved(c, gx, gy, 0.8 + 0.5 * hash01(i, 73), hash01(i, 74) * 6):
                polyf(c, [(-14, -6), (14, -10), (4, 10)], "#e6f6ff", 3)
                line(c, [(-8, -5), (8, -8)], "#ffffff", 2)

    # ---- framed painting + floor lamp by the couch
    rect(c, 1040, 470, 380, 260, "#c98d4a", 6, r=4)
    rect(c, 1062, 492, 336, 216, "#f6d6a8", 3)
    c.save()
    c.rectangle(1062, 492, 336, 216)
    c.clip()
    core.circle(c, 1300, 560, 40); core.fill(c, "#ff9a6a")
    polyf(c, [(1062, 708), (1160, 600), (1240, 660), (1320, 590), (1398, 680), (1398, 708)], "#7a8ac8", 3)
    polyf(c, [(1062, 708), (1130, 660), (1250, 700), (1398, 650), (1398, 708)], "#5a6aa8", 3)
    c.restore()
    _glow(c, 920, 760, 360, "#ffd27a", 0.42)
    line(c, [(920, 1440), (920, 800)], INK, 12)
    line(c, [(920, 1440), (920, 800)], "#8f5c33", 6)
    ell(c, 920, 1446, 60, 12, "#8f5c33", 4)
    polyf(c, [(860, 700), (980, 700), (1010, 800), (830, 800)], "#f2c14e", 5)

    # ---- couch
    cx, cy, cw, ch = LIVING_MARKS["couch"]
    rect(c, cx + 20, 1060, cw - 40, 230, C["couch_sh"], 5, r=40)            # backrest
    for k in range(3):
        rect(c, cx + 50 + k * 145, 1080, 140, 170, C["couch"], 4.5, r=30)
    rect(c, cx, 1180, 80, 230, C["couch"], 5, r=34)                          # arms
    rect(c, cx + cw - 80, 1180, 80, 230, C["couch"], 5, r=34)
    rect(c, cx + 60, 1250, cw - 120, 110, C["couch_hi"], 5, r=24)          # seat cushion
    line(c, [(cx + cw / 2, 1256), (cx + cw / 2, 1356)], C["couch_sh"], 4)
    rect(c, cx + 40, 1350, cw - 80, 80, C["couch"], 5, r=16)               # front
    for fx in (cx + 50, cx + cw - 70):
        rect(c, fx, 1428, 22, 24, "#5a3a2a", 3)
    rect(c, cx + 80, 1160, 110, 100, "#f2c14e", 4, r=26)                    # throw pillow
    blob(c, [(cx + cw - 220, 1250), (cx + cw - 90, 1240), (cx + cw - 70, 1400), (cx + cw - 150, 1440),
             (cx + cw - 210, 1380)], "#bfe0c0", 4)                          # draped throw
    for k in range(3):
        line(c, [(cx + cw - 200 + k * 40, 1260), (cx + cw - 180 + k * 40, 1420)], "#9cc79e", 4)

    # ---- rug + coffee table
    ell(c, 1220, 1620, 470, 110, "#e8d2a8", 5)
    ell(c, 1220, 1620, 420, 90, "#c0453f", 0)
    ell(c, 1220, 1620, 330, 66, None, 5, sc="#e8d2a8")
    ell(c, 1220, 1620, 200, 36, "#9a3330", 0)
    rect(c, 1060, 1420, 24, 150, C["wood_dk"], 4)
    rect(c, 1356, 1420, 24, 150, C["wood_dk"], 4)
    polyf(c, [(1040, 1392), (1400, 1392), (1416, 1408), (1024, 1408)], C["wood_hi"], 4)
    rect(c, 1024, 1408, 392, 26, C["wood_sh"], 4, r=4)
    rect(c, 1290, 1372, 70, 22, "#5f86c4", 3, r=4)        # TV remote / book
    line(c, [(1060, 1520), (1380, 1520)], C["wood_dk"], 8)

    # ---- pet bed (giant, round) + bowl
    px, py = LIVING_MARKS["pet_bed"]
    ell(c, px, py, 270, 82, C["petbed_rim"], 6)
    ell(c, px, py - 6, 200, 52, C["petbed"], 4)
    ell(c, px, py - 10, 150, 30, C["petbed_sh"], 0)
    for k in range(8):
        a = k / 8 * TAU
        core.circle(c, px + math.cos(a) * 236, py + math.sin(a) * 70, 10)
    core.fill(c, mixc(C["petbed_rim"], "#c9a87a", 0.4))
    # chewed toy bone + ball
    with core.saved(c, px + 120, py - 30, 1.0, 0.3):
        rect(c, -40, -9, 80, 18, "#ffffff", 3.5, r=8)
        for ex in (-40, 40):
            core.circle(c, ex, -10, 13); core.circle(c, ex, 10, 13)
            fs(c, "#ffffff", 3.5)
    core.circle(c, px - 300, py + 60, 30); fs(c, "#ff6f61", 4)
    curve(c, [(px - 324, py + 50), (px - 300, py + 66), (px - 276, py + 50)], "#ffffff", 4)
    # food bowl
    ell(c, 990, 1572, 64, 20, "#5f86c4", 4)
    polyf(c, [(926, 1572), (1054, 1572), (1040, 1606), (940, 1606)], "#5f86c4", 4)
    ell(c, 990, 1570, 50, 12, "#c98d4a", 0)
    core.text(c, "IMP", 990, 1600, 24, "#ffffff", "ui")

    # ---- kitchen: upper cabinets, backsplash, counter + drawers
    kx, ky, kw, kh = _LV_COUNTER
    rect(c, kx - 10, 480, kw + 20, 290, C["cab"], 5, r=6)
    for k in range(3):
        rect(c, kx + 6 + k * 138, 496, 130, 258, C["cab"], 4, r=6)
        rect(c, kx + 26 + k * 138, 520, 90, 210, None, 3.5, sc=C["cab_sh"], r=6)
        core.circle(c, kx + 120 + k * 138 - 4, 730, 7); fs(c, "#f2c14e", 2.5)
    for j in range(5):
        for i in range(9):
            rect(c, kx + i * 47, 800 + j * 48, 47, 48, "#f6efe0" if (i + j) % 2 else "#e9e0cc", 2.5,
                 sc="#d6c6a6")
    # sink tap + kettle + fruit bowl + jar
    line(c, [(1690, 1050), (1690, 990), (1740, 980), (1750, 1000)], INK, 12)
    line(c, [(1690, 1050), (1690, 990), (1740, 980), (1750, 1000)], "#c9ced8", 6)
    blob(c, [(1830, 1050), (1820, 990), (1880, 960), (1930, 990), (1920, 1050)], "#ff6f61", 4.5)
    line(c, [(1844, 976), (1880, 940), (1910, 976)], INK, 6)
    ell(c, 1620, 1040, 44, 14, "#f6efe0", 4)
    for k, col in enumerate(["#ffd27a", "#ff6f61", "#7cc96a"]):
        core.circle(c, 1600 + k * 20, 1020 - (k % 2) * 8, 16); fs(c, col, 3)
    # counter body
    rect(c, kx, ky, kw, 30, C["counter_top"], 5, r=6)
    rect(c, kx + 6, ky + 30, kw - 12, kh - 30, C["counter"], 5)
    for (dx, dy, dw, dh) in _LV_DRAWERS:
        if (dx, dy, dw, dh) == _LV_DRAWERS[1]:
            rect(c, dx, dy, dw, dh, "#3b2f2a", 3)        # cavity (front is live)
            continue
        rect(c, dx, dy, dw, dh, C["counter"], 4, r=6)
        rect(c, dx + dw / 2 - 22, dy + dh / 2 - 5, 44, 10, "#c9ced8", 3, r=5)
    for k in range(2):
        rect(c, kx + 16 + k * 196, ky + 120, 190, 250, C["counter"], 4, r=6)
        rect(c, kx + 160 + k * 196 - 130 * k, ky + 230, 10, 40, "#c9ced8", 3, r=5)
    rect(c, kx, ky + kh - 6, kw, 16, "#5a3a2a", 0)
    # wall clock
    core.circle(c, 2140, 600, 70); fs(c, "#ffffff", 6)
    line(c, [(2140, 600), (2140, 556)], INK, 6)
    line(c, [(2140, 600), (2174, 616)], INK, 5)

    # ---- staircase on the right, up to the landing
    st = _LV_STAIRS
    x0, y0, n, rise, run = st["x0"], st["y0"], st["n"], st["rise"], st["run"]
    top = y0 - n * rise
    # stairwell: upper hall wall + landing (beyond the ceiling line)
    lw_x, lw_y, lw_w, lw_h = LIVING_MARKS["landing_wall"]
    rect(c, lw_x - 260, -820, lw_w + 400, top + 820, mixc(C["lv_wall"], "#2a2238", 0.18), 0)
    _glow(c, 2700, 300, 300, "#ffd27a", 0.30)
    rect(c, 2700, 280, 34, 52, "#f2c14e", 3.5, r=10)
    rect(c, lw_x - 260, top - 30, lw_w + 400, 30, C["wood_sh"], 4)       # landing floor edge
    rect(c, lw_x - 260, top, lw_w + 400, 22, C["trim"], 4)
    # under-stair wall (closet door)
    pts = [(x0, y0)]
    for i in range(n):
        pts += [(x0 + i * run, y0 - (i + 1) * rise), (x0 + (i + 1) * run, y0 - (i + 1) * rise)]
    pts += [(W + 600, top), (W + 600, y0)]
    polyf(c, pts, C["lv_wain"], 0)
    rect(c, x0 + 230, y0 - 330, 170, 330, C["lv_wain_sh"], 4, r=6)
    core.circle(c, x0 + 380, y0 - 160, 9); fs(c, "#f2c14e", 3)
    # treads + risers
    for i in range(n):
        tx = x0 + i * run
        ty = y0 - (i + 1) * rise
        rect(c, tx - 8, ty, run + 16, 18, C["wood_hi"], 4, r=4)
        rect(c, tx, ty + 18, run, rise - 18, C["wood"], 3.5)
    line(c, [(x0 - 10, y0), (x0 + n * run, top)], INK, 6)
    # stair runner carpet
    for i in range(n):
        tx = x0 + i * run
        ty = y0 - (i + 1) * rise
        rect(c, tx + 6, ty + 2, run - 12, 12, "#8a4a63", 0, r=3)
    # slightly dim afternoon: static warm-plum falloff toward the edges
    g = cairo.RadialGradient(900, 1100, 500, 1100, 1000, 2300)
    g.add_color_stop_rgba(0, 0.17, 0.10, 0.20, 0.0)
    g.add_color_stop_rgba(1, 0.17, 0.10, 0.20, 0.30)
    c.rectangle(-_LV_EXT[0], -_LV_EXT[1], W + _LV_EXT[0] + _LV_EXT[2], H + _LV_EXT[1] + _LV_EXT[3])
    c.set_source(g)
    c.fill()


def _lv_railing(c):
    st = _LV_STAIRS
    x0, y0, n, rise, run = st["x0"], st["y0"], st["n"], st["rise"], st["run"]
    top = y0 - n * rise
    hr = 300
    a = (x0 - 10, y0 - hr)
    b = (x0 + n * run + 10, top - hr)
    for i in range(n):
        bx = x0 + i * run + run / 2
        by = y0 - (i + 1) * rise
        yrail = lerp(a[1], b[1], (bx - a[0]) / (b[0] - a[0]))
        rect(c, bx - 6, yrail, 12, by - yrail, C["trim"], 3)
    line(c, [a, b], INK, 22)
    line(c, [a, b], C["wood_dk"], 14)
    rect(c, x0 - 34, y0 - hr - 30, 44, hr + 30, C["wood_dk"], 5, r=6)    # newel post
    core.circle(c, x0 - 12, y0 - hr - 40, 24); fs(c, C["wood_dk"], 5)
    # landing balusters along the top edge
    for k in range(12):
        bx = b[0] + 30 + k * 50
        rect(c, bx - 6, top - hr, 12, hr, C["trim"], 3)
    line(c, [(b[0], top - hr), (b[0] + 700, top - hr)], INK, 22)
    line(c, [(b[0], top - hr), (b[0] + 700, top - hr)], C["wood_dk"], 14)


def _lv_table(c, part):
    x, ty, w, h = LIVING_MARKS["table"]
    floor = ty + h
    if part in ("bg", "all"):
        # far chair, table top, under-table shadow, legs
        ell(c, x + w / 2, floor, w * 0.6, 22, core.alpha(C["wood_dk"], 0.35), 0)
        rect(c, x + w - 30, ty - 150, 26, 300, C["wood_sh"], 4, r=6)      # far chair back (right)
        rect(c, x + w - 120, ty + 70, 130, 22, C["wood_sh"], 4, r=6)
        rect(c, x + w - 20, ty + 92, 18, h - 92, C["wood_sh"], 3.5)
        rect(c, x + 30, ty + 30, 22, h - 30, C["wood_sh"], 4)               # back legs
        rect(c, x + w - 60, ty + 30, 22, h - 30, C["wood_sh"], 4)
    if part in ("fg", "all", "bg"):
        polyf(c, [(x + 20, ty - 12), (x + w - 20, ty - 12), (x + w, ty + 12), (x, ty + 12)], C["wood_hi"], 4)
        rect(c, x, ty + 12, w, 34, C["wood"], 4, r=4)
        rect(c, x + 6, ty + 46, 26, h - 46, C["wood"], 4)                  # front legs
        rect(c, x + w - 32, ty + 46, 26, h - 46, C["wood"], 4)
        # vase with flowers
        polyf(c, [(x + w / 2 - 22, ty - 12), (x + w / 2 + 22, ty - 12), (x + w / 2 + 14, ty - 80),
                  (x + w / 2 - 14, ty - 80)], "#7fb2e8", 3.5)
        for k in range(3):
            core.circle(c, x + w / 2 - 20 + k * 20, ty - 104 + (k % 2) * 10, 14)
            fs(c, ["#ff9aac", "#ffffff", "#ffd27a"][k], 3)
        # near chair (left end), side view
        rect(c, x - 40, ty - 160, 26, 320, C["wood"], 4, r=6)
        rect(c, x - 40, ty + 70, 130, 22, C["wood"], 4, r=6)
        rect(c, x - 36, ty + 92, 18, h - 92, C["wood"], 3.5)
        rect(c, x + 66, ty + 92, 18, h - 92, C["wood"], 3.5)


def _lv_drawer(ctx, opening):
    dx, dy, dw, dh = _LV_DRAWERS[1]
    o = clamp(opening)
    out = o * 64
    if o > 0.02:
        # drawer box: sides + interior seen from above as it slides toward us
        polyf(ctx, [(dx - 2, dy), (dx + dw + 2, dy), (dx + dw + 12 * o, dy + out * 0.55),
                    (dx - 12 * o, dy + out * 0.55)], "#d9c6a6", 3.5)
        for k in range(3):
            ang = 0.15 * (k - 1)
            with core.saved(ctx, dx + 30 + k * 34, dy + out * 0.3, 1.0, ang):
                rect(ctx, -4, -12, 8, 24, "#c9ced8", 2.5, r=3)
                ell(ctx, 0, -14, 7, 9, "#c9ced8", 2.5)
    sc = 1 + 0.08 * o
    with core.saved(ctx, dx + dw / 2, dy + dh / 2 + out * 0.55, sc):
        if o > 0.02:
            rect(ctx, -dw / 2 + 4, dh / 2, dw - 8, 10 * o, "#a68a64", 0)
        rect(ctx, -dw / 2, -dh / 2, dw, dh, C["counter"], 4, r=6)
        rect(ctx, -22, -5, 44, 10, "#c9ced8", 3, r=5)


def living_room(ctx, t=0.0, layer="bg", drawer_open=0.0, broken=True, plates=True, plates_lift=0.0,
                parts=None):
    """Living room + kitchen (world 2800 x 1920, people at s=0.75).

    Left to right: broken window (glass bits below), Impulsivity's giant pet
    bed, couch + coffee table (plates), kitchen counter (drawer_open 0..1 =
    top-middle drawer), dining table (you can see under it), staircase up to
    a landing wall (LIVING_MARKS["landing_wall"] is free for a shadow).
    layer "bg" | "fg" (parts: "table" = table top/front legs/near chair,
    "stairs" = banister + balusters). plates=False lets a scene draw its own
    props.plates_stack at LIVING_MARKS["plates"].
    """
    W, H = LIVING_W, LIVING_H
    e = _LV_EXT
    if layer == "bg":
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#e2ddd0", "#c4895a", C["lv_wall_sh"], C["lv_wall_sh"])
        static_layer(ctx, ("living", bool(broken)), -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3],
                     lambda c: _lv_static(c, broken))
        _lv_drawer(ctx, drawer_open)
        if plates:
            px, py = LIVING_MARKS["plates"]
            props.plates_stack(ctx, px, py, 0.62, lift=plates_lift, t=t)
        cached_or_live(ctx, "living_table", 1900, 1050, 520, 560, lambda c: _lv_table(c, "all"))
        cached_or_live(ctx, "living_rail", 2180, _LV_LANDING_Y - 340, 1300, 1340 - _LV_LANDING_Y + 340,
                    _lv_railing)
        # dim afternoon: soft darkening toward the far right/left ends (static)
        return
    if layer == "fg":
        parts = parts or ("table", "stairs")
        if "table" in parts:
            cached_or_live(ctx, "living_table_fg", 1900, 1050, 520, 560, lambda c: _lv_table(c, "fg"))
        if "stairs" in parts:
            cached_or_live(ctx, "living_rail", 2180, _LV_LANDING_Y - 340, 1300, 1340 - _LV_LANDING_Y + 340,
                        _lv_railing)


# ============================================================================
# 5. UPSTAIRS HALLWAY (s05): top of the stairs + the bedroom door
# ============================================================================
HALL_W, HALL_H = 1500, 1920
_HL_CEIL, _HL_FLOOR = 300, 1330
_HL_VP = (760, 860)
_HL_EXT = (600, 700, 500, 900)
_HL_TOP_X = 700                     # stairwell edge (top step nosing)
_HL_RISE, _HL_RUN, _HL_N = 70, 110, 9
_HL_DOOR = (860, 505, 400, 825)     # bedroom door from the hallway side (hinge on the RIGHT)
_HL_DIM = (0.30, 0.13, 0.22, 0.20)  # warm dim over the (lights-off) hallway


def _dim(col, d=_HL_DIM):
    a = hexc(col)
    k = d[3]
    return (a[0] * (1 - k) + d[0] * k, a[1] * (1 - k) + d[1] * k, a[2] * (1 - k) + d[2] * k, a[3])
HALL_MARKS = {
    "size": (HALL_W, HALL_H),
    "char_scale": 0.75,
    "ceiling_y": _HL_CEIL,
    "floor_y": _HL_FLOOR,           # landing floor / wall base
    "stand_y": 1480,
    "door": _HL_DOOR,
    "door_hinge_x": _HL_DOOR[0] + _HL_DOOR[2],
    "light_gap": (_HL_DOOR[0] + 8, _HL_FLOOR - 16, _HL_DOOR[2] - 16, 16),
    "tail_slip": (_HL_DOOR[0] + 200, _HL_FLOOR - 6),   # where a tail vanishes under the door
    "doorway_feet": (1060, 1334),
    "stair_top": (_HL_TOP_X, _HL_FLOOR),
    # tread centres from the top (k=0 is the landing edge, k=1 the first step down ...)
    "steps": [(_HL_TOP_X - (k - 0.5) * _HL_RUN if k else _HL_TOP_X + 60, _HL_FLOOR + k * _HL_RISE)
              for k in range(_HL_N + 1)],
    "stair_slope": math.atan2(_HL_RISE, _HL_RUN),   # radians (stairs descend to the left)
    "landing_feet": (790, 1480),
    "cam": {
        "crawl": (640, 1320, 1.0),
        "door": (1060, 1050, 1.15),
        "door_close": (1060, 1150, 1.7),
    },
}


def _hl_static(c):
    W, H = HALL_W, HALL_H
    CEIL, FLOOR = _HL_CEIL, _HL_FLOOR
    e = _HL_EXT
    _room_shell(c, W, H, CEIL, FLOOR, _HL_VP, C["lv_wall"], C["lv_wall_sh"], "#e2ddd0", "#cfc8b6",
                "#c4895a", "#a36d42", e, side=False)
    # wallpaper + wainscot like downstairs
    for i in range(-560, W + 480, 80):
        for k in range(8):
            yy = CEIL + 60 + k * 90
            if yy > 900:
                break
            ox = 40 if k % 2 else 0
            polyf(c, [(i + ox, yy - 12), (i + ox + 9, yy), (i + ox, yy + 12), (i + ox - 9, yy)],
                  C["lv_paper"], 0)
    rect(c, -e[0], 900, W + e[0] + e[2], FLOOR - 900, C["lv_wain"], 0)
    for i in range(-560, W + 480, 140):
        rect(c, i + 18, 940, 104, 330, None, 3.5, sc=C["lv_wain_sh"], r=6)
    rect(c, -e[0], 890, W + e[0] + e[2], 22, C["lv_wain_sh"], 4)
    # stairwell: the wall continues down below the landing on the left
    tx = _HL_TOP_X
    c.rectangle(-e[0], FLOOR, tx + e[0], H + e[3] - FLOOR)
    core.fill(c, mixc(C["lv_wain"], C["lv_wain_sh"], 0.5))
    for k in range(6):
        rect(c, -e[0] + 30 + k * 140, FLOOR + 80, 100, 300, None, 3.5, sc=C["lv_wain_sh"], r=6)
    # stair stringer (white side board) with wood treads + runner on top
    pts = [(tx + 30, FLOOR + 18)]
    for k in range(1, _HL_N + 2):
        x1 = tx - (k - 1) * _HL_RUN
        y = FLOOR + k * _HL_RISE - _HL_RISE
        pts += [(x1, y + 18), (x1 - _HL_RUN, y + 18)]
    pts += [(-e[0], H + e[3]), (tx + 30, H + e[3])]
    polyf(c, pts, mixc(C["lv_wain"], C["lv_wain_sh"], 0.25), 5)
    for k in range(4):
        px0 = tx - 150 - k * 260
        py0 = FLOOR + 150 + k * 165
        polyf(c, [(px0, py0), (px0 + 190, py0 - 120), (px0 + 190, py0 + 160), (px0, py0 + 280)], None, 3.5,
              sc=C["lv_wain_sh"])
    line(c, pts[:-2], C["trim"], 9)
    for k in range(1, _HL_N + 2):
        x1 = tx - (k - 1) * _HL_RUN
        y = FLOOR + k * _HL_RISE - _HL_RISE
        rect(c, x1 - _HL_RUN - 8, y, _HL_RUN + 14, 20, C["wood_hi"], 4, r=5)
        rect(c, x1 - _HL_RUN + 10, y - 6, _HL_RUN - 18, 9, "#8a4a63", 3, r=3)
    # landing floor edge + nosing
    rect(c, tx - 8, FLOOR - 4, 40, 22, C["wood_hi"], 4, r=4)
    dx, dt, dw, dh = _HL_DOOR
    # runner rug on the landing
    polyf(c, [(tx + 60, 1360), (W + 400, 1360), (W + 460, 1470), (tx + 20, 1470)], "#8a4a63", 4)
    line(c, [(tx + 70, 1380), (W + 410, 1380)], "#c26e7b", 4)
    # decor: framed picture + sconce on the hall wall
    rect(c, 360, 540, 170, 210, "#c98d4a", 5, r=4)
    rect(c, 380, 560, 130, 170, "#ffe9a6", 3)
    core.circle(c, 445, 630, 30); fs(c, PAL["t_skin"], 3)
    blob(c, [(410, 620), (420, 590), (470, 588), (482, 616), (445, 606)], PAL["t_hair"], 3)
    rect(c, 405, 668, 80, 62, PAL["t_hoodie"], 3)
    _glow(c, 640, 600, 220, "#ffd27a", 0.4)
    rect(c, 624, 580, 32, 52, "#f2c14e", 3.5, r=10)
    # a small hall table + plant at the right
    rect(c, 1330, 1060, 150, 18, C["wood"], 4, r=4)
    rect(c, 1342, 1078, 14, 250, C["wood_sh"], 3)
    rect(c, 1452, 1078, 14, 250, C["wood_sh"], 3)
    _plant(c, 1405, 1062, 0.7, seed=4)
    # the hallway is dim (lights off upstairs) so the bedroom light gap pops
    c.rectangle(-e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3])
    core.fill(c, _HL_DIM)
    # warm glow spilling from under the bedroom door onto the floor + door foot
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 1.0, 0.93, 0.70, 0.75)
    g.add_color_stop_rgba(0.5, 1.0, 0.90, 0.60, 0.30)
    g.add_color_stop_rgba(1, 1.0, 0.90, 0.60, 0.0)
    c.save()
    c.translate(dx + dw / 2, FLOOR + 4)
    c.scale(dw * 0.95, 150)
    c.rectangle(-1.2, -0.25, 2.4, 1.3)
    c.set_source(g)
    c.fill()
    c.restore()
    # the doorway opening is cleared (layer "back" = bedroom beyond)
    rect(c, dx - 4, dt - 4, dw + 8, dh + 4, C["lv_wall_sh"], 0)
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(dx, dt, dw, dh)
    c.fill()
    c.restore()


def _hl_back(c):
    """The bright bedroom seen through its door from the hallway."""
    dx, dt, dw, dh = _HL_DOOR
    c.rectangle(dx - 10, dt - 10, dw + 20, dh + 20)
    core.fill(c, mixc(C["bd_wall"], "#fff6d0", 0.25))
    for i in range(0, dw + 96, 96):
        c.rectangle(dx + i + 10, dt - 10, 34, dh)
    core.fill(c, mixc(C["bd_stripe"], "#fff6d0", 0.25))
    c.rectangle(dx - 10, dt + dh - 120, dw + 20, 140)
    core.fill(c, C["wood"])
    # the bed's foot + the desk corner with monitor glow beyond
    rect(c, dx + 30, dt + 520, 180, 150, C["blanket"], 4, r=16)
    _glow(c, dx + dw - 90, dt + 380, 220, "#bfe6ff", 0.6)
    rect(c, dx + dw - 160, dt + 300, 150, 110, "#2f2b3d", 4, r=8)
    rect(c, dx + dw - 148, dt + 312, 126, 86, "#a6e0ff", 0, r=4)
    rect(c, dx + dw - 200, dt + 430, 200, 26, C["desk_top"], 4)
    with core.saved(c, dx + 120, dt + 120, 0.8, -0.03):
        _bd_poster(c, 0)
    _glow(c, dx + dw / 2, dt + dh - 60, 300, "#fff6d0", 0.4)


def _hl_door_panel(ctx, opening, burst, t):
    dx, dt, dw, dh = _HL_DOOR
    wob = 0.0
    if 0 < burst < 1:
        wob = 0.10 * math.sin(burst * 26) * (1 - burst)
    op = clamp(opening + wob)
    q = door_quad(dx + dw, dt, dt + dh, dw, op, _HL_VP, D=2600, toward=False, hinge_left=False)
    polyf(ctx, q, _dim("#efe6d6"), 6)
    if op < 0.97:
        def P(u, v):
            top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
            bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
            return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
        for (u0, v0, u1, v1) in ((0.16, 0.07, 0.84, 0.44), (0.16, 0.53, 0.84, 0.92)):
            polyf(ctx, [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], None, 4, sc=_dim(C["trim_sh"]))
        kx, ky = P(0.11, 0.55)
        core.circle(ctx, kx, ky, 15 * (1 - 0.6 * op))
        fs(ctx, _dim("#f2c14e"), 4)
        # hanging sign on the knob
        if op < 0.3:
            sx, sy = P(0.11, 0.62)
            with core.saved(ctx, sx, sy, 1.0, 0.05 * math.sin(t * 2)):
                line(ctx, [(0, -60), (-30, 0)], "#5a5368", 2.5)
                line(ctx, [(0, -60), (30, 0)], "#5a5368", 2.5)
                rect(ctx, -60, 0, 120, 70, "#ffe9a6", 3.5, r=8)
                core.text(ctx, "GAMING", 0, 30, 22, "#3d4f86", "ui")
                core.text(ctx, "zZz", 0, 58, 22, "#8a6aa8", "comic")


def _hl_light_gap(ctx, t, opening):
    if opening > 0.04:
        return
    x, y, w, h = HALL_MARKS["light_gap"]
    ctx.rectangle(x - 4, y - 6, w + 8, h + 6)
    core.fill(ctx, (1.0, 0.95, 0.75, 0.45))
    ctx.rectangle(x, y, w, h)
    core.fill(ctx, "#fff3c4")
    ctx.rectangle(x + 10, y + 3, w - 20, 5)
    core.fill(ctx, "#ffffff")


def _hl_casing(ctx):
    dx, dt, dw, dh = _HL_DOOR
    trim = 30
    polyf(ctx, [(dx - trim, dt - trim), (dx + dw + trim, dt - trim), (dx + dw + trim, dt + dh),
                (dx + dw, dt + dh), (dx + dw, dt), (dx, dt), (dx, dt + dh), (dx - trim, dt + dh)], _dim(C["trim"]), 5)


def _hl_railing(c):
    tx = _HL_TOP_X
    hr = 300
    a = (tx + 30, _HL_FLOOR - hr)
    b = (tx - (_HL_N + 1) * _HL_RUN, _HL_FLOOR + _HL_N * _HL_RISE - hr)
    for k in range(1, _HL_N + 2):
        bx = tx - (k - 0.5) * _HL_RUN
        by = _HL_FLOOR + (k - 1) * _HL_RISE
        yr = lerp(a[1], b[1], (bx - a[0]) / (b[0] - a[0]))
        rect(c, bx - 7, yr, 14, by - yr, _dim(C["trim"]), 3)
    line(c, [a, b], INK, 24)
    line(c, [a, b], _dim(C["wood_dk"]), 15)
    rect(c, tx + 8, _HL_FLOOR - hr - 30, 46, hr + 40, _dim(C["wood_dk"]), 5, r=6)   # newel
    core.circle(c, tx + 31, _HL_FLOOR - hr - 42, 26); fs(c, _dim(C["wood_dk"]), 5)


def hallway_upstairs(ctx, t=0.0, layer="bg", door_open=0.0, burst=0.0, parts=None):
    """Upstairs landing (world 1500 x 1920, people at s=0.75): stairs coming up
    from the lower left (HALL_MARKS["steps"] tread centres, slope in
    "stair_slope"), the bedroom door on the right with a glowing light gap.

    door_open 0..1 (swings away from us into the bright bedroom),
    burst 0..1 = progress of a slam-open (door rattle, impact lines, dust).
    layer "bg" | "back" (bedroom beyond the door) | "hall" (bg without back)
    | "fg" (parts: "railing" = banister in front of the stairs, "door" =
    casing + panel for someone in the doorway).
    """
    W, H = HALL_W, HALL_H
    e = _HL_EXT
    if layer in ("bg", "back"):
        dx, dt, dw, dh = _HL_DOOR
        cached_or_live(ctx, "hall_back", dx - 12, dt - 12, dw + 24, dh + 24, _hl_back)
        if layer == "back":
            return
    if layer in ("bg", "hall"):
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#e2ddd0", mixc(C["lv_wain"], C["lv_wain_sh"], 0.5),
                  C["lv_wall_sh"], C["lv_wall_sh"])
        static_layer(ctx, "hall", -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3], _hl_static)
        _hl_casing(ctx)
        _hl_door_panel(ctx, door_open, burst, t)
        _hl_light_gap(ctx, t, door_open)
        if 0 < burst < 1:
            dx, dt, dw, dh = _HL_DOOR
            a = 1 - burst
            for k in range(7):
                ang = math.pi + (k - 3) * 0.32
                r0, r1 = 470 + 120 * burst, 600 + 160 * burst
                cx, cy = dx + dw / 2, dt + dh / 2
                line(ctx, [(cx + math.cos(ang) * r0 * 0.9, cy + math.sin(ang) * r0),
                           (cx + math.cos(ang) * r1 * 0.9, cy + math.sin(ang) * r1)],
                     core.alpha(INK, a), 7)
            for k in range(6):
                pr = 20 + 70 * burst + 10 * hash01(k, 3)
                core.circle(ctx, dx + dw - 20 + (k - 3) * 40 * burst, dt + dh - 30 - 50 * burst * hash01(k, 4), pr)
                core.fill(ctx, core.alpha("#f3ead6", 0.6 * a))
        if layer == "bg":
            cached_or_live(ctx, "hall_rail", -560, 600, 1400, 1330, _hl_railing)
        return
    if layer == "fg":
        parts = parts or ("railing",)
        if "door" in parts:
            _hl_casing(ctx)
            if door_open > 0.02:
                _hl_door_panel(ctx, door_open, burst, t)
        if "railing" in parts:
            cached_or_live(ctx, "hall_rail", -560, 600, 1400, 1330, _hl_railing)


# ============================================================================
# HushCorp shared bits
# ============================================================================
def _city_skyline(c, x0, y0, w, h, seed=0, lw=3.5, sky=("#bfdcf0", "#eef7ff"), dusk=False):
    """Cool daytime (or dusk) skyline filling (x0, y0, w, h). Static."""
    core.vgradient(c, sky[0], sky[1], x0, y0, w, h)
    far = "#b4c6d8" if not dusk else "#5a4a8a"
    mid = "#93a9c0" if not dusk else "#433a74"
    near = "#7088a3" if not dusk else "#2f2a5a"
    base = y0 + h
    for layer, (col, hmin, hmax, wmin) in enumerate(((far, 0.25, 0.55, 60), (mid, 0.18, 0.45, 80),
                                                     (near, 0.10, 0.32, 110))):
        xx = x0 - 40
        i = 0
        while xx < x0 + w + 40:
            bw = wmin + 80 * hash01(i, seed + layer * 7)
            bh = h * (hmin + (hmax - hmin) * hash01(i, seed + layer * 7 + 1))
            rect(c, xx, base - bh, bw, bh + 4, col, lw if layer == 2 else 0)
            if hash01(i, seed + layer * 7 + 2) > 0.6:
                rect(c, xx + bw * 0.4, base - bh - 40, bw * 0.2, 44, col, lw if layer == 2 else 0)
            # window grid
            wc = mixc(col, "#ffffff", 0.25) if not dusk else "#ffd27a"
            for yy in range(int(base - bh + 20), int(base), 34):
                for xw in range(int(xx + 10), int(xx + bw - 10), 22):
                    if hash01(xw * 7 + yy, seed + layer) > (0.35 if not dusk else 0.72):
                        c.rectangle(xw, yy, 10, 14)
            core.fill(c, core.alpha(wc, 0.55 if not dusk else 0.9))
            xx += bw + 6
            i += 1


def _corp_panels(c, x0, y0, w, h, step=180, base=None, seam=None):
    base, seam = base or C["hc_wall"], seam or C["hc_wall_sh"]
    c.rectangle(x0, y0 - 2, w, h + 6)
    core.fill(c, base)
    xx = x0 + step
    while xx < x0 + w:
        line(c, [(xx, y0), (xx, y0 + h)], seam, 3)
        xx += step


# ============================================================================
# 6. HUSHCORP OFFICE (s09)
# ============================================================================
OFFICE_W, OFFICE_H = 1400, 1920
_OF_CEIL, _OF_FLOOR = 250, 1300
_OF_EXT = (500, 700, 500, 700)
OFFICE_MARKS = {
    "size": (OFFICE_W, OFFICE_H),
    "char_scale": 0.75,
    "floor_y": _OF_FLOOR,          # base of the glass wall
    "stand_y": 1500,
    "desk": (500, 1140, 760, 360),  # x, top y, w, h (to the floor)
    "desk_top_y": 1140,            # slide devices along this line
    "desk_slide": ((1110, 1140), (600, 1140)),   # Boss -> Emb
    "boss_seat": (1175, 1225),     # hips, she faces LEFT
    "boss_chair": (1190, 1500),
    "guest_seat": (330, 1452),     # hips of Emb in the low chair, faces RIGHT
    "guest_chair": (330, 1500),
    "sweat_floor": (372, 1508),    # where the drop lands ("plip")
    "glass_rect": (110, 420, 560, 470),   # free glass area for the photo / hologram
    "logo": (1200, 455),
    "cam": {
        "wide": (700, 1060, 0.95),
        "two_shot": (740, 1120, 1.0),
        "emb_low": (420, 1230, 1.9),
        "boss": (1130, 1000, 1.9),
        "desk_slide": (850, 1150, 1.6),
    },
}


def _of_static(c):
    W, H = OFFICE_W, OFFICE_H
    CEIL, FLOOR = _OF_CEIL, _OF_FLOOR
    e = _OF_EXT
    x0, y0, x1, y1 = -e[0], -e[1], W + e[2], H + e[3]
    # ceiling
    c.rectangle(x0, y0, x1 - x0, CEIL - y0 + 4)
    core.fill(c, "#f2f5f8")
    for k in range(-2, 6):
        rect(c, k * 380 + 80, CEIL - 70, 220, 18, "#ffffff", 3, sc=C["hc_wall_sh"], r=6)
    # floor-to-ceiling glass with the skyline (we are high up)
    _city_skyline(c, x0, CEIL, x1 - x0, FLOOR - CEIL, seed=4)
    c.rectangle(x0, CEIL, x1 - x0, FLOOR - CEIL)
    core.fill(c, (0.75, 0.86, 0.93, 0.25))
    for k in range(-2, 6):
        mx = k * 350
        rect(c, mx - 8, CEIL, 16, FLOOR - CEIL, C["hc_slate"], 3)
        polyf(c, [(mx + 40, CEIL), (mx + 110, CEIL), (mx + 30, FLOOR), (mx - 40, FLOOR)], (1, 1, 1, 0.10), 0)
    rect(c, x0, 410, x1 - x0, 12, C["hc_slate"], 3)
    # solid wall with the logo behind the Boss
    rect(c, 1000, CEIL, 400 + e[2], FLOOR - CEIL, C["hc_white"], 5)
    line(c, [(1000, CEIL), (1000, FLOOR)], C["hc_wall_sh"], 10)
    lx, ly = OFFICE_MARKS["logo"]
    _glow(c, lx, ly, 260, "#ffffff", 0.6)
    hush_logo(c, lx, ly, 112, lw=7)
    spaced_text(c, "HUSHCORP", lx, ly + 172, 40, PAL["hush_dk"], "ui", 0.55)
    line(c, [(lx - 110, ly + 196), (lx + 110, ly + 196)], PAL["hush"], 4)
    # floor: grey carpet + glass-wall base
    c.rectangle(x0, FLOOR, x1 - x0, y1 - FLOOR)
    core.fill(c, "#b9c3cd")
    for k in range(-6, 14):
        line(c, [(k * 160, FLOOR), (700 + (k * 160 - 700) * 2.6, y1)], "#aeb8c3", 3)
    rect(c, x0, FLOOR - 14, x1 - x0, 20, C["hc_slate"], 4)
    c.rectangle(x0, FLOOR + 6, x1 - x0, 40)
    core.fill(c, core.alpha("#7f8b98", 0.35))
    # big cold rug under the desk area
    polyf(c, [(150, 1420), (1400, 1420), (1500, 1640), (60, 1640)], "#d6dde4", 4)


def _of_boss_chair(c):
    x, fy = OFFICE_MARKS["boss_chair"]
    # very tall white leather back (she faces left: back on the right)
    rect(c, x - 10, 700, 120, 560, "#f7f9fb", 6, r=50)
    rect(c, x + 6, 736, 88, 490, "#e6ebf0", 0, r=40)
    for k in range(4):
        line(c, [(x + 20, 790 + k * 110), (x + 80, 790 + k * 110)], "#d3dae2", 4)
    rect(c, x - 130, 1230, 230, 40, "#f7f9fb", 5, r=18)
    rect(c, x - 16, 1270, 32, 170, C["hc_steel"], 4)
    line(c, [(x - 140, fy - 20), (x + 140, fy - 20)], INK, 16)
    line(c, [(x - 140, fy - 20), (x + 140, fy - 20)], C["hc_steel"], 8)
    for wx in (x - 140, x + 140):
        core.circle(c, wx, fy - 10, 11); fs(c, C["hc_slate"], 3)


def _of_guest_chair(c):
    x, fy = OFFICE_MARKS["guest_chair"]
    # comically low: seat 50 px off the floor, a stubby back
    rect(c, x - 110, fy - 64, 220, 26, "#9aa8b6", 5, r=12)
    rect(c, x - 130, fy - 150, 26, 110, "#9aa8b6", 4.5, r=10)
    for lx in (x - 100, x + 90):
        rect(c, lx, fy - 40, 12, 40, C["hc_slate"], 3)


def _of_desk(c):
    x, ty, w, h = OFFICE_MARKS["desk"]
    floor = ty + h
    # slab top
    rect(c, x, ty, w, 30, "#fbfdff", 6, r=6)
    line(c, [(x + 8, ty + 26), (x + w - 8, ty + 26)], C["hc_wall_sh"], 4)
    # pedestal (right) + thin steel leg (left)
    rect(c, x + w - 220, ty + 30, 210, h - 30, "#f1f5f8", 6, r=4)
    line(c, [(x + w - 200, ty + 60), (x + w - 200, floor - 20)], "#dfe6ec", 6)
    rect(c, x + w - 120, ty + 90, 80, 8, PAL["hush"], 0, r=4)
    rect(c, x + 26, ty + 30, 18, h - 30, C["hc_steel"], 4)
    ell(c, x + 35, floor, 50, 10, C["hc_steel"], 4)


def office(ctx, t=0.0, layer="bg", parts=None):
    """Cold glass HushCorp office (world 1400 x 1920, people at s=0.75).

    Side-on staging: Emb in the comically low chair on the LEFT (faces
    right), the Boss in her tall chair on the RIGHT behind the huge desk
    (faces left). layer "bg" | "fg" (parts: "desk" = the whole desk, in
    front of the Boss's legs; draw devices sliding on the desk AFTER it).
    OFFICE_MARKS["glass_rect"] is free glass for the photo/hologram.
    """
    W, H = OFFICE_W, OFFICE_H
    e = _OF_EXT
    if layer == "bg":
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#f2f5f8", "#b9c3cd", "#bfdcf0", C["hc_white"])
        static_layer(ctx, "office", -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3], _of_static)
        cached_or_live(ctx, "office_chairs", 150, 540, 1300, 980,
                    lambda c: (_of_boss_chair(c), _of_guest_chair(c)))
        cached_or_live(ctx, "office_desk", 440, 1110, 860, 410, _of_desk)
    elif layer == "fg":
        parts = parts or ("desk",)
        if "desk" in parts:
            cached_or_live(ctx, "office_desk", 440, 1110, 860, 410, _of_desk)


# ============================================================================
# 7. HUSHCORP LOBBY (s11)
# ============================================================================
LOBBY_W, LOBBY_H = 1800, 1920
_LB_CEIL, _LB_FLOOR = 250, 1300
_LB_EXT = (500, 700, 500, 700)
_LB_COUNTER = (330, 1070, 650, 430)   # x, top, w, h (to floor 1500)
_LB_GATES = [1090, 1270, 1450]       # turnstile post x centres
LOBBY_MARKS = {
    "size": (LOBBY_W, LOBBY_H),
    "char_scale": 0.75,
    "floor_y": _LB_FLOOR,
    "stand_y": 1500,
    "counter": _LB_COUNTER,
    "counter_top_y": 1070,
    "recep_seat": (760, 1260),       # hips of the receptionist (hidden behind the counter), faces LEFT
    "visitor_feet": (250, 1500),     # Tiredness at the counter's left end, faces RIGHT
    "turnstiles": [(x, 1500) for x in _LB_GATES],
    "lanes": [((_LB_GATES[i] + _LB_GATES[i + 1]) / 2, 1500) for i in range(2)],
    "guard_feet": (1640, 1500),
    "plant": (1010, 1500),
    "logo": (650, 470),
    "cam": {
        "wide": (900, 1060, 0.85),
        "counter_two": (520, 1080, 1.35),
        "recep_close": (720, 1000, 2.0),
        "turnstiles": (1330, 1150, 1.2),
    },
}


def _lb_static(c):
    W, H = LOBBY_W, LOBBY_H
    CEIL, FLOOR = _LB_CEIL, _LB_FLOOR
    e = _LB_EXT
    x0, y0, x1, y1 = -e[0], -e[1], W + e[2], H + e[3]
    c.rectangle(x0, y0, x1 - x0, CEIL - y0 + 4)
    core.fill(c, "#f2f5f8")
    for k in range(-1, 7):
        rect(c, k * 300 + 40, CEIL - 60, 200, 16, "#ffffff", 3, sc=C["hc_wall_sh"], r=6)
    _corp_panels(c, x0, CEIL, x1 - x0, FLOOR - CEIL, 200)
    rect(c, x0, 300, x1 - x0, 10, C["hc_wall_sh"], 0)
    rect(c, x0, 1000, x1 - x0, 14, PAL["hush"], 0)          # teal accent line
    # entrance glass doors at the left with daylight
    rect(c, -e[0], CEIL, 260 + e[0], FLOOR - CEIL, "#d8ecf7", 5)
    core.vgradient(c, "#cfe8f7", "#f4fbff", -e[0], CEIL, 260 + e[0], FLOOR - CEIL)
    for mx in (-120, 120, 250):
        rect(c, mx - 7, CEIL, 14, FLOOR - CEIL, C["hc_slate"], 3)
    _house_far(c, -200, FLOOR, 260, 200, "#dfe6ee", "#b9c6d2", 3, 3, door=False)
    polyf(c, [(0, CEIL), (60, CEIL), (-60, FLOOR), (-120, FLOOR)], (1, 1, 1, 0.3), 0)
    # logo wall behind the counter (backlit, cool white halo - NOT the power teal)
    lx, ly = LOBBY_MARKS["logo"]
    rect(c, 330, 300, 640, 670, "#f7fafc", 6, r=10)
    _glow(c, lx, ly, 340, "#ffffff", 0.9)
    _glow(c, lx, ly, 220, "#dff6f4", 0.6)
    hush_logo(c, lx, ly, 140, lw=8)
    spaced_text(c, "HUSHCORP", lx, ly + 205, 50, PAL["hush_dk"], "ui", 0.55)
    core.text(c, "We keep secrets so you don't have to.", lx, ly + 246, 22, "#7f8b98", "ui")
    # guard post backdrop: a door + security monitors
    rect(c, 1500, 540, 260, 760, "#dfe6ee", 5, r=6)
    rect(c, 1530, 600, 200, 120, C["hc_slate"], 4, r=6)
    core.text(c, "SECURITY", 1630, 676, 30, "#ffffff", "ui")
    # floor: polished, with reflections (static)
    c.rectangle(x0, FLOOR, x1 - x0, y1 - FLOOR)
    core.fill(c, "#dfe6ed")
    for k in range(-8, 18):
        line(c, [(k * 150, FLOOR), (900 + (k * 150 - 900) * 2.4, y1)], "#cfd8e1", 3)
    for yy in (1370, 1470, 1610, 1790):
        line(c, [(x0, yy), (x1, yy)], "#cfd8e1", 3)
    rect(c, x0, FLOOR - 12, x1 - x0, 16, C["hc_wall_sh"], 3)
    # reflections: faint mirrored ghosts of the counter, logo wall and posts
    c.save()
    c.rectangle(x0, FLOOR + 4, x1 - x0, y1 - FLOOR)
    c.clip()
    rect(c, 330, 1500, 650, 300, (0.75, 0.82, 0.88, 0.45), 0)
    rect(c, 330, 1500, 650, 24, (0.18, 0.82, 0.77, 0.25), 0)
    for gx in _LB_GATES:
        rect(c, gx - 40, 1500, 80, 260, (0.62, 0.7, 0.78, 0.40), 0)
    for k in range(5):
        polyf(c, [(k * 380 + 50, FLOOR), (k * 380 + 120, FLOOR), (k * 380 + 40, y1), (k * 380 - 30, y1)],
              (1, 1, 1, 0.22), 0)
    c.restore()


def _lb_counter(c):
    x, ty, w, h = _LB_COUNTER
    floor = ty + h
    # counter top + curved white front with a teal stripe and logo
    rect(c, x - 20, ty - 10, w + 40, 30, "#c9d3dc", 5, r=10)
    core.rrect(c, x, ty + 20, w, h - 20, 30)
    fs(c, "#f7fafc", 6)
    rect(c, x + 6, ty + 120, w - 12, 18, PAL["hush"], 0)
    rect(c, x + 6, floor - 30, w - 12, 24, "#d8e0e8", 0)
    hush_logo(c, x + w / 2, ty + 250, 54, lw=4)
    spaced_text(c, "RECEPTION", x + w / 2, ty + 350, 28, "#8a96a4", "ui", 0.5)
    # sign-in tablet + bell on top
    with core.saved(c, x + 120, ty - 14, 1.0, -0.05):
        rect(c, -50, -12, 100, 16, C["hc_slate"], 3.5, r=4)
    ell(c, x + w - 120, ty - 16, 26, 8, "#c9a227", 3)
    ctx = c
    ctx.move_to(x + w - 140, ty - 16)
    ctx.curve_to(x + w - 140, ty - 50, x + w - 100, ty - 50, x + w - 100, ty - 16)
    fs(ctx, "#f2c14e", 3.5)


def _lb_turnstile(ctx, x, open_, light):
    floor = 1500
    rect(ctx, x - 40, floor - 410, 80, 410, "#c9d3dc", 5, r=14)
    rect(ctx, x - 40, floor - 410, 80, 40, C["hc_slate"], 4, r=12)
    rect(ctx, x - 26, floor - 300, 52, 60, "#24323b", 3.5, r=8)     # card reader
    col = {"green": PAL["safe"], "red": PAL["danger"]}.get(light, "#7f8b98")
    ell(ctx, x, floor - 392, 22, 9, col, 3)
    if light in ("green", "red"):
        _glow(ctx, x, floor - 392, 70, col, 0.55)


def _lb_flaps(ctx, open_):
    # glass flaps between posts; they fold back into the posts as open_ -> 1
    o = clamp(open_)
    for i in range(2):
        xa, xb = _LB_GATES[i] + 40, _LB_GATES[i + 1] - 40
        half = (xb - xa) / 2 - 4
        w = half * (1 - 0.88 * o)
        for (xx, sgn) in ((xa, 1), (xb, -1)):
            x0 = xx if sgn > 0 else xx - w
            rect(ctx, x0, 1222, w, 120, (0.80, 0.92, 0.98, 0.6), 4, r=12)
            line(ctx, [(x0 + 10, 1236), (x0 + min(w - 10, 30), 1236)], (1, 1, 1, 0.8), 3)


def _lb_guard_post(c):
    rect(c, 1520, 1130, 230, 370, "#c9d3dc", 5, r=8)
    rect(c, 1520, 1130, 230, 30, C["hc_slate"], 4, r=8)
    with core.saved(c, 1600, 1110, 1.0, -0.1):
        rect(c, -50, -70, 100, 70, "#24323b", 4, r=6)
        rect(c, -42, -62, 84, 54, "#3b5a6a", 0, r=4)
    ell(c, 1700, 1124, 22, 8, "#7f8b98", 3)      # coffee cup
    rect(c, 1688, 1090, 24, 34, "#ffffff", 3, r=4)


def lobby(ctx, t=0.0, layer="bg", turnstile_open=0.0, turnstile_light="red", parts=None):
    """HushCorp lobby (world 1800 x 1920, people at s=0.75).

    Reception counter (receptionist sits behind it: draw her between bg and
    fg), backlit logo wall, two turnstile lanes (turnstile_open 0..1,
    turnstile_light "red"|"green"|None), guard post, potted plant and a
    polished floor with static reflections. layer "fg" parts: "counter",
    "turnstiles", "guard".
    """
    W, H = LOBBY_W, LOBBY_H
    e = _LB_EXT
    if layer == "bg":
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#f2f5f8", "#dfe6ed", "#d8ecf7", C["hc_wall"])
        static_layer(ctx, "lobby", -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3], _lb_static)
        cached_or_live(ctx, "lobby_counter", 290, 1030, 730, 480, _lb_counter)
        _plant(ctx, LOBBY_MARKS["plant"][0], 1500, 2.6, pot="#e9eff4", leafc="#5aa86a", seed=8)
        for gx in _LB_GATES:
            _lb_turnstile(ctx, gx, turnstile_open, turnstile_light)
        _lb_flaps(ctx, turnstile_open)
        cached_or_live(ctx, "lobby_guard", 1500, 1030, 280, 480, _lb_guard_post)
    elif layer == "fg":
        parts = parts or ("counter",)
        if "counter" in parts:
            cached_or_live(ctx, "lobby_counter", 290, 1030, 730, 480, _lb_counter)
        if "turnstiles" in parts:
            for gx in _LB_GATES:
                _lb_turnstile(ctx, gx, turnstile_open, turnstile_light)
            _lb_flaps(ctx, turnstile_open)
        if "guard" in parts:
            cached_or_live(ctx, "lobby_guard", 1500, 1030, 280, 480, _lb_guard_post)


# ============================================================================
# 8. HUSHCORP LAB (s11)
# ============================================================================
LAB_W, LAB_H = 2400, 1920
_LA_CEIL, _LA_FLOOR = 250, 1300
_LA_EXT = (500, 700, 500, 700)
_LA_TANKS = [(220, 560), (480, 560), (740, 560)]   # centre x, top y
_LA_TERR = (930, 840, 380, 250)                    # terrarium glass x, y, w, h
_LA_SCREEN = (1380, 360, 640, 440)
_LA_CONSOLE = (1700, 1500)
_LA_DOOR = (2090, 520, 280, 780)
LAB_MARKS = {
    "size": (LAB_W, LAB_H),
    "char_scale": 0.75,
    "floor_y": _LA_FLOOR,
    "stand_y": 1500,
    "tanks": [(x, y, 200, 700) for (x, y) in _LA_TANKS],
    "terrarium": _LA_TERR,          # critters_fn(ctx, x, y, w, h, t) draws inside this rect
    "label": (1120, 1146),          # centre of the CARRIER placard
    "terrarium_feet": (1000, 1500),
    "screen": _LA_SCREEN,           # fx draws the wall-screen UI into this rect
    "console": _LA_CONSOLE,         # props.red_button_console anchor (s=0.75)
    "button": (_LA_CONSOLE[0] + props.BUTTON_OFFSET[0] * 0.75, _LA_CONSOLE[1] + props.BUTTON_OFFSET[1] * 0.75),
    "console_lean_feet": (1560, 1500),
    "door": _LA_DOOR,
    "door_feet": (2230, 1500),
    "beacons": [(560, 300), (1300, 300), (2230, 470)],
    "cam": {
        "wide": (1200, 1060, 0.62),
        "tanks": (480, 1000, 1.1),
        "terrarium": (1110, 1000, 1.6),
        "label_close": (1120, 1080, 2.6),
        "screen": (1700, 800, 1.0),
        "console": (1700, 1180, 1.5),
        "door": (2100, 1050, 1.1),
    },
}


def _la_static(c):
    W, H = LAB_W, LAB_H
    CEIL, FLOOR = _LA_CEIL, _LA_FLOOR
    e = _LA_EXT
    x0, y0, x1, y1 = -e[0], -e[1], W + e[2], H + e[3]
    c.rectangle(x0, y0, x1 - x0, CEIL - y0 + 4)
    core.fill(c, "#e9eef3")
    for k in range(-1, 9):
        rect(c, k * 320 + 60, CEIL - 60, 210, 16, "#ffffff", 3, sc=C["hc_wall_sh"], r=6)
    _corp_panels(c, x0, CEIL, x1 - x0, FLOOR - CEIL, 240, "#e3eaf0", "#cbd5de")
    rect(c, x0, 980, x1 - x0, 12, PAL["hush_dk"], 0)
    # cable trays / pipes along the top
    rect(c, x0, 300, x1 - x0, 26, C["hc_steel"], 4)
    for k in range(12):
        line(c, [(k * 220, 326), (k * 220, 360)], C["hc_steel_dk"], 5)
    # floor
    c.rectangle(x0, FLOOR, x1 - x0, y1 - FLOOR)
    core.fill(c, "#cfd8e0")
    for k in range(-8, 24):
        line(c, [(k * 160, FLOOR), (1200 + (k * 160 - 1200) * 2.4, y1)], "#c0cad4", 3)
    for yy in (1380, 1490, 1640, 1840):
        line(c, [(x0, yy), (x1, yy)], "#c0cad4", 3)
    rect(c, x0, FLOOR - 12, x1 - x0, 16, C["hc_wall_sh"], 3)
    # specimen tanks
    for i, (tx, ty) in enumerate(_LA_TANKS):
        _la_tank(c, tx, ty, i)
    # lab bench under the terrarium
    gx, gy, gw, gh = _LA_TERR
    rect(c, gx - 60, gy + gh, gw + 120, 30, "#c9d3dc", 5, r=6)
    rect(c, gx - 40, gy + gh + 30, 30, 1500 - gy - gh - 30, C["hc_steel"], 4)
    rect(c, gx + gw + 10, gy + gh + 30, 30, 1500 - gy - gh - 30, C["hc_steel"], 4)
    rect(c, gx - 20, gy + gh + 220, gw + 40, 18, C["hc_steel"], 4)
    # terrarium box (glass drawn live over the critters)
    rect(c, gx, gy, gw, gh, "#e8f2e0", 5, r=6)
    c.rectangle(gx + 4, gy + gh - 60, gw - 8, 56)
    core.fill(c, "#c9a87a")
    for k in range(10):
        line(c, [(gx + 20 + k * 36, gy + gh - 30), (gx + 34 + k * 36, gy + gh - 44)], "#e2c58e", 4)
    core.circle(c, gx + gw - 70, gy + gh - 110, 50)
    core.stroke(c, C["hc_steel"], 6)
    line(c, [(gx + gw - 70, gy + gh - 110), (gx + gw - 70, gy + gh - 56)], C["hc_steel"], 6)
    ell(c, gx + 70, gy + gh - 52, 34, 9, "#7fb2e8", 3)
    # the CARRIER placard
    lx, ly = LAB_MARKS["label"]
    rect(c, lx - 190, ly - 30, 380, 70, "#fff3c4", 4, r=8)
    core.text(c, "CARRIER", lx, ly + 4, 30, "#c2184b", "ui")
    core.text(c, "BITE TRANSFERS TRAITS", lx, ly + 32, 22, INK, "ui")
    # beakers shelf
    rect(c, 880, 600, 420, 16, C["hc_steel"], 4)
    for k in range(5):
        bx = 910 + k * 80
        col = ["#9fe0a0", "#ff9aac", "#7fb2e8", "#ffd27a", "#d0a8ff"][k]
        polyf(c, [(bx, 540), (bx + 30, 540), (bx + 44, 598), (bx - 14, 598)], "#ffffff", 3)
        polyf(c, [(bx - 6, 575), (bx + 36, 575), (bx + 44, 598), (bx - 14, 598)], col, 0)
        polyf(c, [(bx, 540), (bx + 30, 540), (bx + 44, 598), (bx - 14, 598)], None, 3)
    # wall screen frame (content: screen_fn or default)
    sx, sy, sw, sh = _LA_SCREEN
    rect(c, sx - 24, sy - 24, sw + 48, sh + 48, C["hc_slate"], 6, r=14)
    rect(c, sx + sw / 2 - 40, sy + sh + 24, 80, 30, C["hc_slate"], 4)
    # door frame (panels live)
    dx, dt, dw, dh = _LA_DOOR
    rect(c, dx - 30, dt - 30, dw + 60, dh + 30, C["hc_steel"], 5)
    rect(c, dx, dt, dw, dh, "#2a3640", 4)
    rect(c, dx + dw / 2 - 70, dt - 90, 140, 44, PAL["hush_dk"], 4, r=8)
    core.text(c, "LAB 7", dx + dw / 2, dt - 58, 28, "#ffffff", "ui")
    # biohazard-free warning sign: "AUTHORIZED STAFF ONLY"
    rect(c, 1080, 700, 200, 70, "#ffb020", 4, r=6)
    core.text(c, "AUTHORIZED", 1180, 730, 22, INK, "ui")
    core.text(c, "STAFF ONLY", 1180, 758, 22, INK, "ui")


def _la_tank(c, x, ty, i):
    w, h = 200, 700
    # base + cap
    rect(c, x - w / 2 - 20, ty + h, w + 40, 100, C["hc_steel"], 5, r=12)
    rect(c, x - w / 2 - 20, ty - 60, w + 40, 70, C["hc_steel"], 5, r=12)
    line(c, [(x, ty - 60), (x, 330)], C["hc_steel_dk"], 14)
    # liquid
    core.rrect(c, x - w / 2, ty, w, h, 30)
    fs(c, "#8fd3a0", 0)
    _glow(c, x, ty + h * 0.5, 260, "#d8ffd0", 0.35)
    # vague contents (a dim floating shape)
    with core.saved(c, x, ty + h * 0.45, 1.0, 0.2 * (i - 1)):
        blob(c, [(-50, -80), (20, -110), (60, -40), (40, 60), (-10, 110), (-60, 40)],
             (0.18, 0.36, 0.30, 0.45), 0)
        curve(c, [(10, 100), (30, 180), (0, 240)], (0.18, 0.36, 0.30, 0.4), 12)
    # glass sheen + outline
    polyf(c, [(x - 70, ty + 20), (x - 40, ty + 20), (x - 40, ty + h - 20), (x - 70, ty + h - 20)], (1, 1, 1, 0.22), 0)
    core.rrect(c, x - w / 2, ty, w, h, 30)
    core.stroke(c, INK, 6)
    for yy in (ty + 120, ty + h - 120):
        line(c, [(x - w / 2, yy), (x + w / 2, yy)], (1, 1, 1, 0.35), 4)
    rect(c, x - 60, ty + h + 30, 120, 40, "#ffffff", 3, r=6)
    core.text(c, f"SPEC-{i + 3:02d}", x, ty + h + 58, 22, INK, "mono")


def _la_default_screen(c, x, y, w, h, t):
    c.rectangle(x, y, w, h)
    core.fill(c, "#10242c")
    for k in range(1, 8):
        line(c, [(x, y + k * h / 8), (x + w, y + k * h / 8)], (0.2, 0.5, 0.55, 0.25), 2)
    for k in range(1, 12):
        line(c, [(x + k * w / 12, y), (x + k * w / 12, y + h)], (0.2, 0.5, 0.55, 0.25), 2)
    hush_logo(c, x + w / 2, y + h / 2 - 20, 70, lw=0, color=PAL["hush_dk"], hole="#10242c")
    spaced_text(c, "HUSHCORP", x + w / 2, y + h / 2 + 100, 32, PAL["hush_dk"], "ui", 0.55)


def _la_bubbles(ctx, t):
    n = 0
    for i, (tx, ty) in enumerate(_LA_TANKS):
        for k in range(3 if i == 1 else 2):
            if n >= 8:
                return
            n += 1
            ph = (t * 0.18 + hash01(n, 5)) % 1.0
            bx = tx - 60 + 120 * hash01(n, 6) + 10 * math.sin(t * 1.5 + n)
            by = ty + 660 - ph * 620
            core.circle(ctx, bx, by, 7 + 6 * hash01(n, 7))
            core.stroke(ctx, (1, 1, 1, 0.7), 3)


def _la_default_critters(ctx, x, y, w, h, t):
    for k in range(3):
        cx = x + 70 + k * 110
        cy = y + h - 64
        bob = 3 * math.sin(t * 3 + k * 2)
        ell(ctx, cx, cy + bob, 34, 22, PAL["thing_fur"], 3.5)
        core.circle(ctx, cx + 22, cy - 12 + bob, 16); fs(ctx, PAL["thing_fur"], 3.5)
        core.circle(ctx, cx + 28, cy - 14 + bob, 6); core.fill(ctx, INK)
        core.circle(ctx, cx + 30, cy - 16 + bob, 2); core.fill(ctx, "#ffffff")
        curve(ctx, [(cx - 32, cy + bob), (cx - 60, cy - 10), (cx - 70, cy + 10)], PAL["thing_dk"], 4)


def _la_door(ctx, opening):
    dx, dt, dw, dh = _LA_DOOR
    o = clamp(opening) * (dw / 2 - 6)
    for side in (-1, 1):
        px = dx + (0 if side < 0 else dw / 2) + side * o
        ctx.save()
        ctx.rectangle(dx, dt, dw, dh)
        ctx.clip()
        rect(ctx, px, dt, dw / 2, dh, "#dfe6ee", 5)
        rect(ctx, px + 30, dt + 120, dw / 2 - 60, 160, "#a9c7d8", 4, r=8)
        rect(ctx, px + (dw / 2 - 30 if side < 0 else 14), dt + 380, 16, 120, C["hc_steel"], 3, r=6)
        ctx.restore()


def lab(ctx, t=0.0, layer="bg", alarm=0.0, button_pressed=0.0, critters_fn=None, screen_fn=None,
        door_open=0.0, parts=None):
    """HushCorp lab (world 2400 x 1920, people at s=0.75).

    Specimen tanks (<= 8 slow bubbles), the critter terrarium + "CARRIER -
    BITE TRANSFERS TRAITS" placard (critters_fn(ctx, x, y, w, h, t) draws
    the critters inside LAB_MARKS["terrarium"]), a big wall screen
    (screen_fn(ctx, x, y, w, h, t) for fx UI in LAB_MARKS["screen"]), the
    big red button console (button_pressed 0..1), sliding lab door
    (door_open 0..1) and alarm 0..1 (red wash + rotating beacons).
    layer "fg" parts: "console", "bench".
    """
    W, H = LAB_W, LAB_H
    e = _LA_EXT
    if layer == "bg":
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#e9eef3", "#cfd8e0", "#e3eaf0", "#e3eaf0")
        static_layer(ctx, "lab", -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3], _la_static)
        _la_bubbles(ctx, t)
        gx, gy, gw, gh = _LA_TERR
        ctx.save()
        ctx.rectangle(gx, gy, gw, gh)
        ctx.clip()
        (critters_fn or _la_default_critters)(ctx, gx, gy, gw, gh, t)
        ctx.restore()
        # terrarium glass: tint + glints + lid
        rect(ctx, gx, gy, gw, gh, (0.85, 0.95, 1.0, 0.18), 5)
        polyf(ctx, [(gx + 30, gy), (gx + 80, gy), (gx + 20, gy + gh), (gx - 20, gy + gh)], (1, 1, 1, 0.18), 0)
        rect(ctx, gx - 14, gy - 22, gw + 28, 26, C["hc_steel"], 4, r=6)
        sx, sy, sw, sh = _LA_SCREEN
        ctx.save()
        ctx.rectangle(sx, sy, sw, sh)
        ctx.clip()
        (screen_fn or _la_default_screen)(ctx, sx, sy, sw, sh, t)
        ctx.restore()
        _la_door(ctx, door_open)
        cx, cy = _LA_CONSOLE
        props.red_button_console(ctx, cx, cy, 0.75, pressed=button_pressed, t=t, alarm=alarm)
        _alarm(ctx, t, alarm, LAB_MARKS["beacons"])
    elif layer == "fg":
        parts = parts or ()
        if "console" in parts:
            cx, cy = _LA_CONSOLE
            props.red_button_console(ctx, cx, cy, 0.75, pressed=button_pressed, t=t, alarm=alarm)
        if alarm > 0:
            # keep characters inside the red wash too (subtle, no beacons)
            p = 0.5 + 0.5 * math.sin(t * TAU * 0.8)
            vx0, vy0, vx1, vy1 = ctx.clip_extents()
            ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
            core.fill(ctx, core.alpha("#ff2a3c", alarm * (0.06 + 0.06 * p)))


# ============================================================================
# 9. HUSHCORP CORRIDOR (s11 chase): one-point perspective
# ============================================================================
CORRIDOR_W, CORRIDOR_H = 1080, 1920
_CR_VP = (540, 820)
_CR_FAR = (380, 560, 320, 520)      # end-wall rect at the window
_CR_WIN = (420, 590, 240, 470)
_CR_K0, _CR_KF = 940.0, 260.0       # floor offset below VP at z=0 and at the end wall
_CR_D = _CR_K0 / _CR_KF
_CR_HALF = 0.615                    # corridor half-width / eye height


def corridor_scale(z, lane=0.0):
    """Perspective placement in the corridor. z = 0 near camera .. 1 at the
    end window; lane -1 (left wall) .. +1 (right wall), runners use ~+-0.4.
    Returns (x, y_feet, s): screen-world point for the feet and character scale."""
    k = 1 + clamp(z, -0.2, 1.0) * (_CR_D - 1)
    y = _CR_VP[1] + _CR_K0 / k
    x = _CR_VP[0] + lane * _CR_K0 * _CR_HALF / k
    s = 1.028 / k
    return (x, y, s)


CORRIDOR_MARKS = {
    "size": (CORRIDOR_W, CORRIDOR_H),
    "vp": _CR_VP,
    "window": _CR_WIN,
    "window_sill_y": 1060,
    "end_wall": _CR_FAR,
    "beacons": [(540, 380), (300, 230)],
    "note": "use corridor_scale(z, lane) for characters: z=0 feet y=1760 s=1.03, z=1 feet y=1080 s=0.28",
    "cam": {"default": (540, 960, 1.0)},
}


def _cr_pt(u, v, z):
    """Point on the corridor box at depth z: u -1..1 across, v 0 (floor) .. 1 (ceiling)."""
    k = 1 + z * (_CR_D - 1)
    x = _CR_VP[0] + u * _CR_K0 * _CR_HALF / k
    y = _CR_VP[1] + (_CR_K0 - v * 2 * _CR_K0) / k
    return (x, y)


def _cr_static(c, broken_level):
    zn = -0.25
    # walls / floor / ceiling quads
    def quad(a, b, col, lw=0):
        polyf(c, [_cr_pt(*a, zn), _cr_pt(*b, zn), _cr_pt(*b, 1.0), _cr_pt(*a, 1.0)], col, lw)
    quad((-1, 0), (1, 0), "#cdd6de")         # floor
    quad((-1, 1), (1, 1), "#eef2f6")         # ceiling
    quad((-1, 0), (-1, 1), "#dfe6ec")        # left wall
    quad((1, 0), (1, 1), "#d6dee6")          # right wall
    # floor tiles: lines to the VP + depth lines
    for u in (-0.6, -0.2, 0.2, 0.6):
        line(c, [_cr_pt(u, 0, zn), _cr_pt(u, 0, 1.0)], "#bfc9d2", 4)
    for k in range(12):
        z = (k / 12) ** 1.6
        line(c, [_cr_pt(-1, 0, z), _cr_pt(1, 0, z)], "#bfc9d2", 3)
    # ceiling light panels
    for k in range(7):
        za, zb = (k / 7) ** 1.5, (k / 7) ** 1.5 + 0.03 + 0.02 * (1 - k / 7)
        polyf(c, [_cr_pt(-0.35, 1, za), _cr_pt(0.35, 1, za), _cr_pt(0.35, 1, zb), _cr_pt(-0.35, 1, zb)],
              "#ffffff", 3)
    # teal accent stripe + doors along the walls
    for side in (-1, 1):
        for vv in (0.42, 0.44):
            line(c, [_cr_pt(side, vv, zn), _cr_pt(side, vv, 1.0)], PAL["hush_dk"] if vv < 0.43 else PAL["hush"], 5)
        for k, z0 in enumerate((0.05, 0.32, 0.58)):
            z1 = z0 + 0.12
            polyf(c, [_cr_pt(side, 0, z0), _cr_pt(side, 0.62, z0), _cr_pt(side, 0.62, z1), _cr_pt(side, 0, z1)],
                  "#c3ced8", 4)
            polyf(c, [_cr_pt(side, 0.40, z0 + 0.02), _cr_pt(side, 0.55, z0 + 0.02), _cr_pt(side, 0.55, z1 - 0.03),
                      _cr_pt(side, 0.40, z1 - 0.03)], "#a9c7d8", 3)
    # corner lines
    for (u, v) in ((-1, 0), (1, 0), (-1, 1), (1, 1)):
        line(c, [_cr_pt(u, v, zn), _cr_pt(u, v, 1.0)], INK, 5)
    # warm dusk light spilling from the window along the floor
    polyf(c, [_cr_pt(-0.25, 0, 1.0), _cr_pt(0.25, 0, 1.0), _cr_pt(0.5, 0, 0.55), _cr_pt(-0.5, 0, 0.55)],
          (1.0, 0.72, 0.50, 0.22), 0)
    polyf(c, [_cr_pt(-0.25, 0, 1.0), _cr_pt(0.25, 0, 1.0), _cr_pt(0.36, 0, 0.8), _cr_pt(-0.36, 0, 0.8)],
          (1.0, 0.72, 0.50, 0.20), 0)
    # wall seams receding
    for side in (-1, 1):
        for z in (0.12, 0.25, 0.45, 0.72, 0.88):
            line(c, [_cr_pt(side, 0, z), _cr_pt(side, 1, z)], "#c9d3dc", 3)
    # end wall + tall window
    fx, fy, fw, fh = _CR_FAR
    rect(c, fx, fy, fw, fh, "#e3eaf0", 4)
    wx, wy, ww, wh = _CR_WIN
    c.save()
    c.rectangle(wx, wy, ww, wh)
    c.clip()
    core.vgradient(c, C["dusk_top"], C["dusk_low"], wx, wy, ww, wh)
    core.vgradient(c, C["dusk_top"], C["dusk_mid"], wx, wy, ww, wh * 0.6)
    for k in range(5):
        core.circle(c, wx + 30 + hash01(k, 3) * (ww - 60), wy + 30 + hash01(k, 4) * 150, 2.5)
    core.fill(c, "#ffffff")
    for k in range(6):
        bx = wx + k * 44 - 10
        bh = 60 + 70 * hash01(k, 8)
        rect(c, bx, wy + wh - bh, 40, bh, C["city"], 0)
    c.restore()
    rect(c, wx, wy, ww, wh, None, 6)
    line(c, [(wx + ww / 2, wy), (wx + ww / 2, wy + wh)], C["hc_slate"], 6)
    if broken_level < 0.5:
        polyf(c, [(wx + 20, wy), (wx + 60, wy), (wx + 10, wy + 120), (wx - 10, wy + 120)], (1, 1, 1, 0.25), 0)
    rect(c, wx - 12, wy + wh, ww + 24, 14, C["hc_steel"], 3)


def _cr_window_damage(ctx, b):
    wx, wy, ww, wh = _CR_WIN
    if b <= 0:
        return
    cx, cy = wx + ww * 0.5, wy + wh * 0.55
    if b < 1:
        for k in range(9):
            a = k / 9 * TAU + 0.3
            L = (60 + 140 * hash01(k, 2)) * clamp(b * 1.6)
            pts = [(cx, cy)]
            for j in range(1, 4):
                pts.append((cx + math.cos(a + 0.1 * (j % 2)) * L * j / 3, cy + math.sin(a) * L * j / 3))
            line(ctx, pts, "#ffffff", 3)
        for r in (30, 70):
            core.circle(ctx, cx, cy, r * clamp(b * 1.6))
            core.stroke(ctx, (1, 1, 1, 0.6), 2.5)
    else:
        # shattered: only jagged teeth remain on the frame edges (sky shows through)
        teeth = [[(wx, wy), (wx + 70, wy), (wx + 20, wy + 80)],
                 [(wx + ww, wy), (wx + ww, wy + 110), (wx + ww - 50, wy + 40)],
                 [(wx, wy + wh), (wx, wy + wh - 90), (wx + 60, wy + wh)],
                 [(wx + ww, wy + wh), (wx + ww - 80, wy + wh), (wx + ww, wy + wh - 60)],
                 [(wx + ww / 2 - 6, wy + wh), (wx + ww / 2 + 30, wy + wh), (wx + ww / 2, wy + wh - 70)]]
        for tpts in teeth:
            polyf(ctx, tpts, (0.88, 0.96, 1.0, 0.75), 3)


def corridor(ctx, t=0.0, layer="bg", alarm=0.0, window_broken=0.0):
    """Long HushCorp corridor in one-point perspective (world 1080 x 1920,
    fixed camera). Tall dusk window at the end (window_broken 0..1:
    cracks -> shattered). alarm 0..1 as in the lab. Place runners with
    corridor_scale(z, lane); sort them far-to-near."""
    if layer != "bg":
        return
    W, H = CORRIDOR_W, CORRIDOR_H
    b = clamp(window_broken)
    _overscan(ctx, -300, -400, W + 300, H + 400, "#eef2f6", "#cdd6de", "#dfe6ec", "#d6dee6")
    static_layer(ctx, ("corridor", b >= 1), -300, -400, W + 600, H + 800, lambda c: _cr_static(c, b))
    if b >= 1:
        wx, wy, ww, wh = _CR_WIN
        ctx.save()
        ctx.rectangle(wx, wy, ww, wh)
        ctx.clip()
        # mullion gone: redraw the clean sky over it
        core.vgradient(ctx, C["dusk_top"], C["dusk_mid"], wx + ww / 2 - 8, wy, 16, wh * 0.6)
        core.vgradient(ctx, C["dusk_mid"], C["dusk_low"], wx + ww / 2 - 8, wy + wh * 0.6, 16, wh * 0.4)
        ctx.restore()
    _cr_window_damage(ctx, b)
    _alarm(ctx, t, alarm, CORRIDOR_MARKS["beacons"], wash=0.28)


# ============================================================================
# 10. TOWER EXTERIOR (dusk) + CITY FALL
# ============================================================================
TOWER_W, TOWER_H = 1080, 1920
_TW_HOLE = (600, 560, 260, 360)          # the broken window panel
TOWER_MARKS = {
    "size": (TOWER_W, TOWER_H),
    "char_scale": 0.45,
    "hole": _TW_HOLE,
    "hole_center": (730, 740),
    "facade_x": 560,                    # tower face starts here; open sky to the left
    "fall_from": (700, 760),            # where a body leaves the hole
    "fall_path": [(700, 760), (480, 900), (360, 1150)],
    "shard_origin": (720, 760),
    "cam": {"default": (540, 960, 1.0), "hole": (700, 780, 1.6)},
}


def _dusk_sky(c, x, y, w, h, stars=True):
    g = cairo.LinearGradient(0, y, 0, y + h)
    for (u, col) in ((0.0, "#241a52"), (0.30, "#4b2f7e"), (0.55, "#a2508a"), (0.75, "#e47a6a"),
                     (0.88, "#f2a65a"), (1.0, "#ffd08a")):
        g.add_color_stop_rgba(u, *hexc(col))
    c.rectangle(x, y, w, h)
    c.set_source(g)
    c.fill()
    if stars:
        for i in range(11):
            sx = x + hash01(i, 13) * w
            sy = y + hash01(i, 14) * h * 0.32
            r = 2.0 + 2.5 * hash01(i, 15)
            core.circle(c, sx, sy, r)
        core.fill(c, "#ffffff")
        props._star(c, x + w * 0.22, y + h * 0.12, 9)
        core.fill(c, "#fff6d0")


def _tw_static(c):
    W, H = TOWER_W, TOWER_H
    _dusk_sky(c, -300, -300, W + 600, H + 600)
    # pink-orange cloud streaks
    for (cx, cy, s) in ((220, 1160, 1.4), (640, 1290, 1.0), (120, 1380, 0.9)):
        with core.saved(c, cx, cy, (s * 1.6, s * 0.45)):
            _cloud(c, 0, 0, 1.0, (1.0, 0.72, 0.62, 0.55))
    # city far below with lit windows
    base = H + 200
    for layer, (col, top) in enumerate((("#5a3f86", 1540), ("#3f2d6e", 1610), ("#2a2052", 1700))):
        xx = -300
        i = 0
        while xx < W + 300:
            bw = 40 + 50 * hash01(i, 30 + layer)
            bt = top + 140 * hash01(i, 33 + layer)
            rect(c, xx, bt, bw, base - bt, col, 0)
            for yy in range(int(bt + 10), int(base), 26):
                for xw in range(int(xx + 6), int(xx + bw - 6), 14):
                    if hash01(xw * 13 + yy, 40 + layer) > 0.7:
                        c.rectangle(xw, yy, 6, 9)
            core.fill(c, "#ffd27a")
            xx += bw + 4
            i += 1
    c.rectangle(-300, 1500, W + 600, 90)
    core.fill(c, (1.0, 0.75, 0.55, 0.25))
    # the tower facade (glass curtain wall, mullions converge downward)
    fx = TOWER_MARKS["facade_x"]
    vpx, vpy = 860, 7000
    polyf(c, [(fx, -300), (W + 400, -300), (W + 400, H + 300), (fx + 120, H + 300)], "#3a3f7a", 6)
    # sky reflection gradient on the glass
    g = cairo.LinearGradient(0, -300, 0, H + 300)
    g.add_color_stop_rgba(0, *hexc("#2e2a66"))
    g.add_color_stop_rgba(0.6, *hexc("#7a4a8e"))
    g.add_color_stop_rgba(1, *hexc("#c46a7a"))
    c.move_to(fx + 6, -300); c.line_to(W + 400, -300); c.line_to(W + 400, H + 300); c.line_to(fx + 126, H + 300)
    c.close_path()
    c.set_source(g)
    c.fill()
    c.save()
    c.move_to(fx, -300); c.line_to(W + 400, -300); c.line_to(W + 400, H + 300); c.line_to(fx + 120, H + 300)
    c.close_path()
    c.clip()
    for k in range(0, 8):
        x_top = fx + k * 140
        x_bot = vpx + (x_top - vpx) * (vpy - (H + 300)) / (vpy + 300)
        line(c, [(x_top, -300), (x_bot, H + 300)], "#1d1a40", 9)
    for yy in range(-200, H + 300, 220):
        line(c, [(fx - 10, yy), (W + 400, yy)], "#1d1a40", 11)
    for k in range(4):
        x0 = fx + 60 + k * 230
        polyf(c, [(x0, -300), (x0 + 60, -300), (x0 + 260, H + 300), (x0 + 200, H + 300)], (1, 1, 1, 0.08), 0)
    # cloud reflections on the glass
    for (cx, cy) in ((780, 1180), (960, 1320)):
        with core.saved(c, cx, cy, (1.2, 0.35)):
            _cloud(c, 0, 0, 1.0, (1.0, 0.75, 0.7, 0.25))
    c.restore()
    line(c, [(fx, -300), (fx + 120, H + 300)], "#e8b0c8", 6)    # lit corner edge
    # the broken window: red-lit corridor inside
    hx, hy, hw, hh = _TW_HOLE
    c.save()
    c.rectangle(hx, hy, hw, hh)
    c.clip()
    c.rectangle(hx, hy, hw, hh)
    core.fill(c, "#5a1a2e")
    _glow(c, hx + hw / 2, hy + hh / 2, 220, "#ff3b5c", 0.6)
    # the corridor inside, in one-point perspective toward the camera
    polyf(c, [(hx + 80, hy + 120), (hx + hw - 80, hy + 120), (hx + hw, hy + hh), (hx, hy + hh)], "#7a2a3e", 0)
    polyf(c, [(hx, hy), (hx + hw, hy), (hx + hw - 80, hy + 90), (hx + 80, hy + 90)], "#6a2236", 0)
    rect(c, hx + 80, hy + 90, hw - 160, 30, "#4a1426", 0)
    for k in range(3):
        rect(c, hx + 110 + k * 4, hy + 18 + k * 26, hw - 220 - k * 8, 10, (1.0, 0.8, 0.8, 0.5), 0)
    c.restore()
    _glow(c, hx + hw / 2, hy + hh / 2, 300, "#ff3b5c", 0.22)


def _tw_teeth(c):
    hx, hy, hw, hh = _TW_HOLE
    teeth = [[(hx, hy), (hx + 90, hy), (hx + 30, hy + 70), (hx, hy + 40)],
             [(hx + 140, hy), (hx + hw, hy), (hx + hw, hy + 130), (hx + hw - 40, hy + 50)],
             [(hx, hy + hh), (hx, hy + hh - 140), (hx + 50, hy + hh - 60), (hx + 110, hy + hh)],
             [(hx + hw, hy + hh), (hx + hw - 90, hy + hh), (hx + hw - 30, hy + hh - 90), (hx + hw, hy + hh - 160)],
             [(hx, hy + 150), (hx + 40, hy + 190), (hx, hy + 230)]]
    for tp in teeth:
        polyf(c, tp, (0.72, 0.74, 0.95, 0.75), 4)
        line(c, [tp[0], tp[1]], (1, 1, 1, 0.8), 3)
    rect(c, hx - 8, hy - 8, hw + 16, hh + 16, None, 10, sc="#1d1a40")


def tower_exterior(ctx, t=0.0, layer="bg"):
    """Outside the glass tower at dusk, by the broken window (world 1080 x
    1920). Static warm-to-violet sky with a few stars, city far below.
    layer "fg" = the jagged glass teeth + frame of the hole (a body leaving
    the hole is drawn between bg and fg)."""
    W, H = TOWER_W, TOWER_H
    if layer == "bg":
        _overscan(ctx, -300, -300, W + 400, H + 300, "#241a52", "#2a2052", "#4b2f7e", "#3a3f7a")
        static_layer(ctx, "tower", -300, -300, W + 700, H + 600, _tw_static)
    elif layer == "fg":
        hx, hy, hw, hh = _TW_HOLE
        cached_or_live(ctx, "tower_teeth", hx - 20, hy - 20, hw + 40, hh + 40, _tw_teeth)


CITY_FALL_MARKS = {
    "size": (1080, 1920),
    "centre": (540, 1000),        # the landing street point (screen-world)
    "note": "approach 0..1: ground scale 0.35 -> ~4.2 (exponential), rooftops grow faster (pseudo-3D)",
    "cam": {"default": (540, 960, 1.0)},
}
_CF_BLOCK, _CF_STREET = 360, 90


def _cf_blocks():
    """Static city plan (list of buildings) around the landing point (0, 0)."""
    out = []
    step = _CF_BLOCK + _CF_STREET
    for bi in range(-5, 6):
        for bj in range(-6, 7):
            bx0 = bi * step + _CF_STREET / 2
            by0 = bj * step + _CF_STREET / 2
            k = bi * 31 + bj * 17
            if (bi, bj) in ((1, -2), (-2, 1)):
                out.append(("park", bx0, by0, _CF_BLOCK, _CF_BLOCK, 0.0, k))
                continue
            n = 2 if hash01(k, 3) > 0.5 else 3
            for m in range(n):
                if n == 2:
                    rx, ry, rw, rh = (bx0 + 14, by0 + 14 + m * 176, _CF_BLOCK - 28, 160)
                else:
                    rx, ry, rw, rh = (bx0 + 14 + (m % 2) * 172, by0 + 14 + (m // 2) * 176,
                                      158 if m < 2 else _CF_BLOCK - 28, 160)
                h = 0.08 + 0.42 * hash01(k * 5 + m, 9)
                out.append(("bld", rx, ry, rw, rh, h, k * 5 + m))
    return out


_CF_PLAN = None
_CF_COLS = ["#5a4a8a", "#6b5aa0", "#4a5a8a", "#8a5a7a", "#a46a6a", "#5a6a9a"]


def city_fall(ctx, t=0.0, layer="bg", approach=0.0):
    """Looking DOWN at the city (world 1080 x 1920). approach 0..1 = the
    ground rushing up: a fixed (static) city plan scaled about the landing
    street at CITY_FALL_MARKS["centre"]; taller rooftops grow faster for a
    pseudo-3D rush. Drawn live with culling (~3-6 ms), no per-frame noise."""
    global _CF_PLAN
    if layer != "bg":
        return
    if _CF_PLAN is None:
        _CF_PLAN = _cf_blocks()
    a = clamp(approach)
    S = 0.35 * (12.0 ** a)
    cx, cy = CITY_FALL_MARKS["centre"]
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    # streets (ground)
    ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
    core.fill(ctx, "#2c2650")
    lw = max(1.5, 3.0 * S)
    step = _CF_BLOCK + _CF_STREET

    def P(x, y, k=1.0):
        return (cx + x * S * k, cy + y * S * k)

    # block bases (one path)
    for bi in range(-5, 6):
        for bj in range(-6, 7):
            bx0 = bi * step + _CF_STREET / 2
            by0 = bj * step + _CF_STREET / 2
            p0 = P(bx0, by0)
            p1 = P(bx0 + _CF_BLOCK, by0 + _CF_BLOCK)
            if p1[0] < vx0 or p0[0] > vx1 or p1[1] < vy0 or p0[1] > vy1:
                continue
            ctx.rectangle(p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1])
    core.fill(ctx, "#4a4270")
    # street lights + car lights (static dots, one path per colour)
    rad = max(1.5, 5 * S)
    for (ox, oy, col) in ((0, 80, "#ffd27a"), (80, 0, "#ffd27a"), (22, 190, "#ff6070"), (190, -20, "#fff3c4")):
        for i in range(-5, 6):
            for j in range(-6, 7):
                px, py = P(i * step + ox, j * step + oy)
                if vx0 - 10 < px < vx1 + 10 and vy0 - 10 < py < vy1 + 10:
                    ctx.new_sub_path()
                    ctx.arc(px, py, rad, 0, TAU)
        core.fill(ctx, col)
    # buildings: side faces first (two shades), then roofs grouped by colour
    sides = ([], [])
    roofs = {}
    parks = []
    details = []
    for (kind, x, y, w, h, hh, seed) in _CF_PLAN:
        k = 1.0 + hh * (0.25 + 1.6 * a)
        b0, b1 = P(x, y), P(x + w, y + h)
        r0, r1 = P(x, y, k), P(x + w, y + h, k)
        if max(b1[0], r1[0]) < vx0 or min(b0[0], r0[0]) > vx1 or max(b1[1], r1[1]) < vy0 or min(b0[1], r0[1]) > vy1:
            continue
        if kind == "park":
            parks.append((b0, b1, x, y, seed))
            continue
        if cx < b0[0]:
            sides[0].append([b0, (b0[0], b1[1]), (r0[0], r1[1]), r0])
        elif cx > b1[0]:
            sides[0].append([(b1[0], b0[1]), b1, r1, (r1[0], r0[1])])
        if cy < b0[1]:
            sides[1].append([b0, (b1[0], b0[1]), (r1[0], r0[1]), r0])
        elif cy > b1[1]:
            sides[1].append([(b0[0], b1[1]), b1, r1, (r0[0], r1[1])])
        roofs.setdefault(seed % len(_CF_COLS), []).append((r0, r1))
        details.append((r0, r1, seed))
    for (b0, b1, x, y, seed) in parks:
        ctx.rectangle(b0[0], b0[1], b1[0] - b0[0], b1[1] - b0[1])
        fs(ctx, "#3f7a5a", lw)
        for m in range(6):
            tx, ty = P(x + 50 + 260 * hash01(m, seed), y + 50 + 260 * hash01(m, seed + 1), 1.04)
            ctx.new_sub_path()
            ctx.arc(tx, ty, 34 * S, 0, TAU)
        fs(ctx, "#4f9a6a", lw)
    for shade, quads in zip(("#2a2450", "#231e44"), sides):
        for q in quads:
            core.poly(ctx, q)
        fs(ctx, shade, lw if S > 0.55 else 0)
    for ci, rs in roofs.items():
        for (r0, r1) in rs:
            ctx.rectangle(r0[0], r0[1], r1[0] - r0[0], r1[1] - r0[1])
        fs(ctx, _CF_COLS[ci], lw if S > 0.55 else 1.2)
    # rooftop details only once they are big enough to read
    if S > 0.6:
        for (r0, r1, seed) in details:
            rw, rh = r1[0] - r0[0], r1[1] - r0[1]
            ctx.rectangle(r0[0], r0[1], rw, max(1.0, rh * 0.08))
        core.fill(ctx, (1.0, 0.7, 0.5, 0.5))
        for (r0, r1, seed) in details:
            rw, rh = r1[0] - r0[0], r1[1] - r0[1]
            if hash01(seed, 4) > 0.5:
                ctx.new_sub_path()
                ctx.arc(r0[0] + rw * 0.3, r0[1] + rh * 0.55, min(rw, rh) * 0.16, 0, TAU)
        fs(ctx, "#8a6a5a", lw * 0.8)
        for (r0, r1, seed) in details:
            rw, rh = r1[0] - r0[0], r1[1] - r0[1]
            if hash01(seed, 4) <= 0.5:
                ctx.rectangle(r0[0] + rw * 0.55, r0[1] + rh * 0.3, rw * 0.25, rh * 0.3)
        fs(ctx, "#9aa0b8", lw * 0.8)
    # the landing manhole at the centre of the street
    mx, my = P(0, 0)
    core.circle(ctx, mx, my, 30 * S)
    fs(ctx, "#5a5468", lw)
    core.circle(ctx, mx, my, 18 * S)
    core.stroke(ctx, "#3a3450", lw)


# ============================================================================
# 11. SEWER (s12, s13 tunnels)
# ============================================================================
SEWER_W, SEWER_H = 2600, 1920
_SW_VAULT, _SW_WALK, _SW_EDGE = 210, 1250, 1300   # vault bottom, walkway top, walkway front edge
_SW_WATER = 1385
_SW_EXT = (500, 600, 500, 700)
_SW_HOLE_X = 1300
_SW_SIDE = {0: (2150, 690, 300), 1: (1700, 690, 300), 2: (900, 690, 300), 3: (2050, 690, 300)}
SEWER_MARKS = {
    "size": (SEWER_W, SEWER_H),
    "char_scale": 0.75,
    "walk_feet_y": 1282,           # feet line on the walkway
    "walk_x": (80, 2520),
    "wall_lean_x": 640,            # good spot to slump against the wall (s13)
    "hole": (_SW_HOLE_X, 90),      # centre of the broken hole in the vault (variant 0, hole=True)
    "crater": (_SW_HOLE_X, 1276),  # centre of the shallow crater on the walkway
    "lie_hips": (_SW_HOLE_X, 1262),  # someone lying in the crater
    "water_y": _SW_WATER,
    "side_tunnel": {v: (x, top, w, _SW_WALK - top) for v, (x, top, w) in _SW_SIDE.items()},
    "dark_ends": (600, 2000),      # darkness ramps in left of / right of these x
    "eyes_in_dark": (300, 980),    # good spot for teal slits watching from the dark
    "cam": {
        "wide": (1300, 1000, 0.75),
        "crater": (1300, 1050, 1.5),
        "walk": (900, 1000, 1.0),
        "side_tunnel": (2250, 1000, 1.0),
    },
}


def _sw_bricks(c, x0, y0, w, h, seed, bh=46, bw=110):
    c.rectangle(x0, y0, w, h)
    core.fill(c, C["sw_mortar"])
    row = 0
    yy = y0
    while yy < y0 + h:
        off = (bw / 2) if row % 2 else 0
        xx = x0 - off
        i = 0
        while xx < x0 + w:
            v = hash01(i * 7 + row * 131, seed)
            col = C["sw_brick"] if v > 0.22 else (C["sw_brick_sh"] if v > 0.08 else "#4d7d73")
            c.rectangle(xx + 4, yy + 4, bw - 8, bh - 8)
            core.fill(c, col)
            xx += bw
            i += 1
        yy += bh
        row += 1


def _sw_static(c, variant, hole):
    W, H = SEWER_W, SEWER_H
    e = _SW_EXT
    x0, y0, x1, y1 = -e[0], -e[1], W + e[2], H + e[3]
    seed = 11 + variant * 7
    # vault + back wall bricks
    _sw_bricks(c, x0, y0, x1 - x0, _SW_WALK - y0 + 10, seed)
    c.rectangle(x0, y0, x1 - x0, _SW_VAULT - y0)
    core.fill(c, (0.05, 0.14, 0.13, 0.45))
    line(c, [(x0, _SW_VAULT), (x1, _SW_VAULT)], INK, 6)
    # arch ribs (pilasters curving into the vault)
    for k in range(-1, 6):
        px = 300 + k * 650 + (variant * 120) % 300
        rect(c, px - 50, _SW_VAULT, 100, _SW_WALK - _SW_VAULT, C["sw_brick_sh"], 5)
        for yy in range(_SW_VAULT + 40, _SW_WALK, 92):
            line(c, [(px - 50, yy), (px + 50, yy)], C["sw_mortar"], 4)
        c.move_to(px - 50, _SW_VAULT)
        c.curve_to(px - 50, 120, px - 20, 40, px + 10, y0)
        c.line_to(px + 110, y0)
        c.curve_to(px + 80, 40, px + 50, 120, px + 50, _SW_VAULT)
        c.close_path()
        fs(c, C["sw_brick_sh"], 5)
    # moss + water stains
    for k in range(9):
        mx = hash01(k, seed + 1) * W
        polyf(c, [(mx - 20, 500 + 300 * hash01(k, seed + 2)), (mx + 20, 500 + 300 * hash01(k, seed + 2)),
                  (mx + 30, _SW_WALK), (mx - 30, _SW_WALK)], (0.10, 0.25, 0.22, 0.35), 0)
    for k in range(7):
        mx = hash01(k, seed + 3) * W
        blob(c, [(mx - 90, _SW_WALK), (mx - 60, _SW_WALK - 70), (mx, _SW_WALK - 100), (mx + 70, _SW_WALK - 60),
                 (mx + 100, _SW_WALK)], C["sw_moss"], 0)
    # pipes
    py = 360 + 60 * (variant % 2)
    rect(c, x0, py, x1 - x0, 64, C["sw_pipe"], 5)
    line(c, [(x0, py + 16), (x1, py + 16)], "#8aa89b", 5)
    for k in range(-1, 10):
        fx = 150 + k * 320 + variant * 60
        rect(c, fx - 14, py - 10, 28, 84, C["sw_pipe_sh"], 4, r=4)
    rect(c, x0, py + 110, x1 - x0, 34, C["sw_pipe_sh"], 4)
    vx = 1850 - variant * 330
    rect(c, vx - 30, py + 60, 60, _SW_WATER - py - 40, C["sw_pipe"], 5)
    core.circle(c, vx, py + 300, 46)
    core.stroke(c, INK, 14)
    core.circle(c, vx, py + 300, 46)
    core.stroke(c, "#b5544a", 8)
    line(c, [(vx - 46, py + 300), (vx + 46, py + 300)], "#b5544a", 6)
    line(c, [(vx, py + 254), (vx, py + 346)], "#b5544a", 6)
    # outflow pipes (drips come from these)
    for ox in SEWER_DRIPS[variant]:
        rect(c, ox - 40, 1040, 80, 70, C["sw_pipe_sh"], 5, r=10)
        ell(c, ox, 1110, 32, 12, "#122a26", 3)
        polyf(c, [(ox - 30, 1110), (ox + 30, 1110), (ox + 40, _SW_WALK), (ox - 40, _SW_WALK)], (0.12, 0.3, 0.26, 0.4), 0)
    # chalk mark (every junction looks the same...)
    mxk = 1000 + variant * 410
    line(c, [(mxk - 30, 820), (mxk + 30, 880)], (0.9, 0.95, 0.9, 0.55), 6)
    line(c, [(mxk + 30, 820), (mxk - 30, 880)], (0.9, 0.95, 0.9, 0.55), 6)
    # side tunnel mouth (dark arch)
    sx, stop, sw = _SW_SIDE[variant]
    c.move_to(sx, _SW_WALK)
    c.line_to(sx, stop + sw / 2)
    c.arc(sx + sw / 2, stop + sw / 2, sw / 2, math.pi, 0)
    c.line_to(sx + sw, _SW_WALK)
    c.close_path()
    fs(c, "#0f2624", 7)
    c.move_to(sx + 30, _SW_WALK)
    c.line_to(sx + 30, stop + sw / 2)
    c.arc(sx + sw / 2, stop + sw / 2, sw / 2 - 30, math.pi, 0)
    c.line_to(sx + sw - 30, _SW_WALK)
    c.close_path()
    fs(c, "#0a1c1a", 0)
    for k in range(9):
        a = math.pi + k * math.pi / 8
        line(c, [(sx + sw / 2 + math.cos(a) * sw / 2, stop + sw / 2 + math.sin(a) * sw / 2),
                 (sx + sw / 2 + math.cos(a) * (sw / 2 + 40), stop + sw / 2 + math.sin(a) * (sw / 2 + 40))],
             C["sw_mortar"], 5)
    # walkway
    c.rectangle(x0, _SW_WALK, x1 - x0, _SW_EDGE - _SW_WALK)
    fs(c, C["sw_walk"], 5)
    c.rectangle(x0, _SW_EDGE, x1 - x0, _SW_WATER - _SW_EDGE)
    fs(c, C["sw_walk_sh"], 5)
    line(c, [(x0, _SW_EDGE + 8), (x1, _SW_EDGE + 8)], "#7f9f93", 4)
    for k in range(14):
        cx = hash01(k, seed + 5) * W
        line(c, [(cx, _SW_WALK + 6), (cx + 30, _SW_WALK + 26), (cx + 20, _SW_EDGE)], "#466a5f", 3)
    for k in range(4):
        px = 200 + hash01(k, seed + 6) * 2200
        ell(c, px, _SW_WALK + 24, 70, 10, "#3f6f68", 0)
    # water channel
    c.rectangle(x0, _SW_WATER, x1 - x0, y1 - _SW_WATER)
    core.fill(c, C["sw_water"])
    c.rectangle(x0, _SW_WATER, x1 - x0, 40)
    core.fill(c, "#1b4648")
    for k in range(8):
        wx = hash01(k, seed + 8) * W
        wy = _SW_WATER + 80 + hash01(k, seed + 9) * 380
        line(c, [(wx, wy), (wx + 120, wy)], (0.45, 0.75, 0.68, 0.35), 4)
    # the hole + daylight shaft + crater + rubble (variant 0)
    if hole:
        hx = _SW_HOLE_X
        pts = []
        for i in range(14):
            a = i / 14 * TAU
            r = 1 + 0.25 * (hash01(i, 5) - 0.5)
            pts.append((hx + math.cos(a) * 120 * r, 80 + math.sin(a) * 70 * r))
        polyf(c, pts, "#cfeeff", 6)
        c.save()
        core.poly(c, pts)
        c.clip()
        core.vgradient(c, "#9fd8f7", "#f4fbff", hx - 130, 0, 260, 160)
        _cloud(c, hx - 30, 60, 0.35)
        rect(c, hx + 40, 20, 14, 140, "#5d6380", 0)        # a streetlight pole up there
        c.restore()
        polyf(c, pts, None, 7)
        for i in range(0, 14, 2):
            with core.saved(c, pts[i][0], pts[i][1], 1.0, hash01(i, 6)):
                rect(c, -26, -14, 52, 28, C["sw_brick"], 4, r=4)
        # light beam (static, soft)
        g = cairo.LinearGradient(0, 100, 0, _SW_EDGE)
        g.add_color_stop_rgba(0, 1.0, 0.97, 0.85, 0.55)
        g.add_color_stop_rgba(1, 1.0, 0.97, 0.85, 0.18)
        c.move_to(hx - 105, 110); c.line_to(hx + 105, 110)
        c.line_to(hx + 260, _SW_EDGE); c.line_to(hx - 260, _SW_EDGE); c.close_path()
        c.set_source(g)
        c.fill()
        ell(c, hx, _SW_WALK + 20, 300, 40, (1.0, 0.97, 0.85, 0.35), 0)
        # crater
        ell(c, hx, _SW_WALK + 26, 210, 30, "#2f544b", 5)
        ell(c, hx, _SW_WALK + 30, 160, 18, "#3a6f74", 0)
        for k in range(6):
            a = math.pi + k * math.pi / 5
            line(c, [(hx + math.cos(a) * 210, _SW_WALK + 26 + math.sin(a) * 30),
                     (hx + math.cos(a) * 270, _SW_WALK + 20 + math.sin(a) * 40)], INK, 4)
        for k in range(9):
            rx = hx - 330 + 660 * hash01(k, 21)
            if abs(rx - hx) < 200:
                rx += 260 if rx > hx else -260
            with core.saved(c, rx, _SW_WALK + 12 + 16 * hash01(k, 22), 0.8 + 0.4 * hash01(k, 23),
                            hash01(k, 24) * 3):
                rect(c, -30, -16, 60, 32, C["sw_brick"] if k % 2 else "#7a9a8a", 4, r=5)
        # light on the water below
        polyf(c, [(hx - 200, _SW_WATER + 20), (hx + 200, _SW_WATER + 20), (hx + 260, _SW_WATER + 220),
                  (hx - 260, _SW_WATER + 220)], (1.0, 0.97, 0.85, 0.12), 0)
    # darkness at the far ends (static vignette, never pitch black)
    for (xa, xb) in ((x0, 600), (x1, 2000)):
        g = cairo.LinearGradient(xa, 0, xb, 0)
        g.add_color_stop_rgba(0, 0.03, 0.10, 0.09, 0.80)
        g.add_color_stop_rgba(1, 0.03, 0.10, 0.09, 0.0)
        c.rectangle(min(xa, xb), y0, abs(xb - xa), y1 - y0)
        c.set_source(g)
        c.fill()
    # top/bottom falloff
    g = cairo.LinearGradient(0, y0, 0, 500)
    g.add_color_stop_rgba(0, 0.03, 0.10, 0.09, 0.6)
    g.add_color_stop_rgba(1, 0.03, 0.10, 0.09, 0.0)
    c.rectangle(x0, y0, x1 - x0, 500 - y0)
    c.set_source(g)
    c.fill()


SEWER_DRIPS = {0: (520, 2300), 1: (420, 1500), 2: (1500, 2350), 3: (700, 1400)}


def _sw_teal(c, variant):
    sx, stop, sw = _SW_SIDE[variant]
    c.save()
    c.move_to(sx + 30, _SW_WALK)
    c.line_to(sx + 30, stop + sw / 2)
    c.arc(sx + sw / 2, stop + sw / 2, sw / 2 - 30, math.pi, 0)
    c.line_to(sx + sw - 30, _SW_WALK)
    c.close_path()
    c.clip()
    _glow(c, sx + sw / 2, _SW_WALK - 120, 360, PAL["power"], 0.85)
    c.restore()
    _glow(c, sx + sw / 2, _SW_WALK + 10, 420, PAL["power"], 0.30)
    ell(c, sx + sw / 2, _SW_WALK + 22, 200, 18, core.alpha(PAL["power"], 0.25), 0)


def sewer(ctx, t=0.0, layer="bg", hole=None, light=1.0, teal_glow_end=0.0, variant=0, drips=True,
          motes=True):
    """Brick sewer tunnel, side view (world 2600 x 1920, people at s=0.75).

    Walkway (feet at SEWER_MARKS["walk_feet_y"]) over a water channel with a
    slow shimmer (<= 10 lines), pipes, a few animated drips, static dark ends.
    hole (default True for variant 0, else False): broken hole in the vault,
    daylight shaft with dust motes, rubble and the shallow crater.
    light 0..1 overall light level; teal_glow_end 0..1 lights the side
    tunnel mouth (SEWER_MARKS["side_tunnel"][variant]) teal.
    variant 0..3: montage junctions (pipes, chalk mark, tunnel mouth move).
    layer "fg" (optional) applies the same light level over the characters.
    """
    if layer == "fg":
        # optional: darken the characters too (same overall light level)
        if light < 1:
            vx0, vy0, vx1, vy1 = ctx.clip_extents()
            ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
            core.fill(ctx, (0.02, 0.08, 0.07, 0.6 * (1 - clamp(light))))
        return
    if layer != "bg":
        return
    W, H = SEWER_W, SEWER_H
    e = _SW_EXT
    variant = int(variant) % 4
    if hole is None:
        hole = (variant == 0)
    _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], "#0b1f1d", C["sw_water"], "#0b1f1d", "#0b1f1d")
    static_layer(ctx, ("sewer", variant, bool(hole)), -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3],
                 lambda c: _sw_static(c, variant, hole))
    # water shimmer (<= 10 short lines drifting)
    for k in range(9):
        ph = (t * 0.12 + hash01(k, 40)) % 1.0
        wx = 100 + hash01(k, 41) * 2400 + ph * 160
        wy = _SW_WATER + 60 + hash01(k, 42) * 420
        a = math.sin(ph * math.pi)
        line(ctx, [(wx, wy), (wx + 70 + 40 * hash01(k, 43), wy)], core.alpha("#9fd8c8", 0.55 * a), 4)
    if drips:
        for i, ox in enumerate(SEWER_DRIPS[variant]):
            ph = ((t + i * 0.77) % 1.9) / 1.9
            if ph < 0.75:
                yy = 1112 + (_SW_WATER - 1112) * (ph / 0.75) ** 2
                ell(ctx, ox, yy, 6, 9, "#bfe8dc", 2.5)
            else:
                k = (ph - 0.75) / 0.25
                ell(ctx, ox, _SW_WATER + 30, 20 + 50 * k, 5 + 6 * k, None, 3, sc=core.alpha("#bfe8dc", 1 - k))
    if hole and motes:
        hx = _SW_HOLE_X
        for k in range(10):
            ph = (t * 0.05 + hash01(k, 50)) % 1.0
            mx = hx - 150 + 300 * hash01(k, 51) + 30 * math.sin(t * 0.6 + k)
            my = 180 + ph * 1000
            spread = (my - 110) / (_SW_EDGE - 110)
            mx = hx + (mx - hx) * (0.6 + spread)
            core.circle(ctx, mx, my, 3 + 2 * hash01(k, 52))
            core.fill(ctx, core.alpha("#fff6d8", 0.7 * math.sin(ph * math.pi)))
    if teal_glow_end > 0:
        sx, stop, sw = _SW_SIDE[variant]
        g = clamp(teal_glow_end)
        rx, ry, rw, rh = sx + sw / 2 - 430, _SW_WALK - 420, 860, 860
        ctx.save()
        ctx.rectangle(rx, ry, rw, rh)
        ctx.clip()
        ctx.push_group()
        cached_or_live(ctx, ("sewer_teal", variant), rx, ry, rw, rh, lambda c: _sw_teal(c, variant))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(g)
        ctx.restore()
    if light < 1:
        vx0, vy0, vx1, vy1 = ctx.clip_extents()
        ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
        core.fill(ctx, (0.02, 0.08, 0.07, 0.6 * (1 - clamp(light))))


SEWER_POV_MARKS = {"size": (1080, 1920), "hole": (540, 760), "cam": {"default": (540, 960, 1.0)}}


def _swpov_static(c):
    W, H = 1080, 1920
    hx, hy = SEWER_POV_MARKS["hole"]
    c.rectangle(-300, -300, W + 600, H + 600)
    core.fill(c, C["sw_mortar"])
    # bricks in rings around the hole (looking straight up the vault)
    for ring in range(1, 16):
        r = 180 + ring * 90
        n = int(r * TAU / 120)
        for i in range(n):
            a0 = (i + (ring % 2) * 0.5) / n * TAU
            a1 = a0 + TAU / n * 0.86
            c.new_sub_path()
            c.arc(hx, hy, r + 40, a0, a1)
            c.arc_negative(hx, hy, r - 40, a1, a0)
            c.close_path()
            v = hash01(i * 13 + ring, 7)
            core.fill(c, C["sw_brick"] if v > 0.25 else C["sw_brick_sh"])
    pts = []
    for i in range(16):
        a = i / 16 * TAU
        rr = 1 + 0.28 * (hash01(i, 9) - 0.5)
        pts.append((hx + math.cos(a) * 200 * rr, hy + math.sin(a) * 230 * rr))
    core.poly(c, pts)
    c.save()
    c.clip()
    core.vgradient(c, "#9fd8f7", "#f4fbff", hx - 260, hy - 260, 520, 520)
    _cloud(c, hx - 60, hy - 90, 0.6)
    c.restore()
    _glow(c, hx, hy, 520, "#fff6d8", 0.55)
    polyf(c, pts, None, 8)
    for i in range(0, 16, 2):
        with core.saved(c, pts[i][0], pts[i][1], 1.2, hash01(i, 10) * 3):
            rect(c, -30, -16, 60, 32, C["sw_brick"], 4, r=4)
    g = cairo.RadialGradient(hx, hy, 300, hx, hy, 1200)
    g.add_color_stop_rgba(0, 0.03, 0.10, 0.09, 0.0)
    g.add_color_stop_rgba(1, 0.03, 0.10, 0.09, 0.7)
    c.rectangle(-300, -300, W + 600, H + 600)
    c.set_source(g)
    c.fill()


def sewer_hole_pov(ctx, t=0.0, layer="bg", drip_t0=0.4):
    """His POV lying in the crater: looking straight UP at the broken hole
    (world 1080 x 1920). A drip falls toward the camera from drip_t0
    (repeats every 2.2 s). fx does the eyelid wipe on top."""
    if layer != "bg":
        return
    static_layer(ctx, "sewer_pov", -300, -300, 1680, 2520, _swpov_static)
    if t >= drip_t0:
        ph = ((t - drip_t0) % 2.2) / 2.2
        hx, hy = SEWER_POV_MARKS["hole"]
        if ph < 0.6:
            k = ph / 0.6
            r = 8 + 140 * k ** 3
            ell(ctx, hx + 150 + 40 * k, hy - 160 + 500 * k ** 2, r * 0.8, r, (0.75, 0.92, 0.88, 0.8), 3 + 3 * k)


# ============================================================================
# 12. THE SHAFT (s13): vertical cylindrical containment chamber
# ============================================================================
SHAFT_W, SHAFT_H = 1080, 3600
_SH_X0, _SH_X1 = -700, 1780        # drawable width (zoom-outs to ~0.5)
_SH_HZ = 2350                      # eye level (horizon)
_SH_F = 520.0
_SH_CAM = 0.85                     # camera distance from the axis (in radii)
_SH_TIER = 0.32                    # tier spacing (radii)
_SH_POD = 0.12                     # pod width (radii)
_SH_CAT_Y = 2400                   # catwalk deck (feet)
SHAFT_MARKS = {
    "size": (SHAFT_W, SHAFT_H),
    "drawable_x": (_SH_X0, _SH_X1),
    "char_scale": 0.22,            # tiny figures on the catwalk for the epic wide
    "horizon_y": _SH_HZ,
    "catwalk_feet_y": _SH_CAT_Y,
    "catwalk_x": (-520, 640),      # walkable span of the near catwalk
    "tunnel_mouth": (-380, 2400),  # where they come out (left)
    "tired_feet": (300, _SH_CAT_Y),
    "creature_feet": (390, _SH_CAT_Y),
    "logo": (540, 1560),
    "cam": {
        "arrive": (60, 2250, 2.2),
        "two_close": (340, 2300, 3.2),
        "reveal_wide": (540, 1900, 0.56),
        "title_wide": (420, 2150, 0.75),
        "look_up": (540, 1300, 0.9),
    },
    "note": "pull-outs: zoom 3.2 -> 0.56; close-ups: frame the shaft at 1.2-2 and draw people in screen space",
}


def _sh_proj(phi, yw):
    z = math.cos(phi) + _SH_CAM
    return (540 + _SH_F * math.sin(phi) / z, _SH_HZ + _SH_F * yw / z, _SH_F / z, z)


def _sleeper_path(c, x, y, s):
    """Curled sleeper silhouette as sub-paths (no fill), for batching."""
    pts = [(-110, 40), (-120, -20), (-70, -80), (10, -90), (90, -60), (120, 0), (100, 60), (20, 90), (-60, 84)]
    core.smooth_path(c, [(x + px * s, y + py * s) for px, py in pts], closed=True)
    for ear in ([(70, -70), (20, -120), (-60, -140), (-20, -104), (40, -66)],
                [(90, -60), (50, -104), (-10, -112), (30, -82), (70, -50)]):
        core.smooth_path(c, [(x + px * s, y + py * s) for px, py in ear], closed=True)


def _sh_pods():
    """Static list of pods: (x, y, w, h, foreshortening, seed, group)."""
    out = []
    n_phi = 26
    for k in range(-30, 8):
        yw = k * _SH_TIER + _SH_TIER * 0.5
        for i in range(n_phi):
            phi = (i + (0.5 if k % 2 else 0)) / n_phi * TAU - math.pi
            if abs(phi) > math.radians(128):
                continue
            x, y, sc, z = _sh_proj(phi, yw)
            # leave room for the giant logo on the far wall
            if abs(phi) < math.radians(54) and -3.95 < yw < -1.2:
                continue
            if y < -200 or y > SHAFT_H + 200 or x < _SH_X0 - 100 or x > _SH_X1 + 100:
                continue
            fore = (1 + _SH_CAM * math.cos(phi)) / math.hypot(math.sin(phi), math.cos(phi) + _SH_CAM)
            w = _SH_POD * sc * fore
            h = _SH_POD * 1.7 * sc
            seed = (k * 37 + i * 11) & 1023
            out.append((x, y, w, h, z, seed, seed % 3))
    out.sort(key=lambda p: -p[4])   # far first
    return out


_SH_PODS = _sh_pods()
_SH_INDEX = {(round(p[0], 1), round(p[1], 1)): i for i, p in enumerate(_SH_PODS)}
_SH_BANDS = [(-1e9, 600), (600, 1200), (1200, 1800), (1800, 2300), (2300, 2900), (2900, 1e9)]


def _sh_nearest(x, y, wmin=0):
    best, bi = 1e18, None
    for i, p in enumerate(_SH_PODS):
        if p[2] < wmin:
            continue
        d = (p[0] - x) ** 2 + (p[1] - y) ** 2
        if d < best:
            best, bi = d, i
    return bi


_SH_JOY = _sh_nearest(540, 2960, wmin=8)
_SH_DEFAULT_LABELS = {_SH_JOY: "JOY"}
SHAFT_MARKS["pods"] = [(p[0], p[1], p[2], p[3]) for p in _SH_PODS]   # (x, y, w, h) per index
_SH_PULSE = [[[(p[0], p[1], p[2], p[3]) for p in _SH_PODS
               if p[6] == g and p[2] >= 3 and b0 <= p[1] < b1] for g in range(3)] for (b0, b1) in _SH_BANDS]
SHAFT_MARKS["pods_near"] = [i for i, p in enumerate(_SH_PODS) if p[2] > 90]
SHAFT_MARKS["joy_pod"] = _SH_JOY
SHAFT_MARKS["n_sections"] = len(_SH_BANDS)
SHAFT_MARKS["sections"] = [(max(a, -200), min(b, SHAFT_H + 200)) for a, b in _SH_BANDS]


def _sh_static(c, sleeper_fn, labels=None):
    W, H = SHAFT_W, SHAFT_H
    x0, x1 = _SH_X0, _SH_X1
    g = cairo.LinearGradient(0, -200, 0, H + 200)
    g.add_color_stop_rgba(0, *hexc("#06121a"))
    g.add_color_stop_rgba(0.45, *hexc("#0f2d38"))
    g.add_color_stop_rgba(0.8, *hexc("#123844"))
    g.add_color_stop_rgba(1, *hexc("#0f3a40"))
    c.rectangle(x0, -200, x1 - x0, H + 400)
    c.set_source(g)
    c.fill()
    # meridian ribs (vertical in this projection)
    for i in range(-14, 15):
        phi = i / 26 * TAU
        if abs(phi) > math.radians(128):
            continue
        x, _, sc, z = _sh_proj(phi, 0)
        wpx = max(3, 0.02 * sc)
        c.rectangle(x - wpx / 2, -200, wpx, H + 400)
        core.fill(c, (0.20, 0.42, 0.50, 0.5))
    # tier ledges (projected circles)
    for k in range(-30, 9):
        yw = k * _SH_TIER + _SH_TIER * 0.05
        pts = []
        for j in range(0, 61):
            phi = (j / 60 - 0.5) * math.radians(256)
            x, y, sc, z = _sh_proj(phi, yw)
            pts.append((x, y))
        line(c, pts, (0.30, 0.55, 0.60, 0.55), 5)
    # giant HushCorp logo on the far wall
    lx, ly = SHAFT_MARKS["logo"]
    _glow(c, lx, ly, 420, PAL["hush"], 0.18)
    hush_logo(c, lx, ly, 200, color="#1d6f6c", hole="#0b2026", lw=8, ring=True)
    spaced_text(c, "HUSHCORP", lx, ly + 280, 56, "#2a8a86", "ui", 0.6)
    # pods (culled to this cache tile), batched per depth bin: one path per material
    pods = _SH_PODS
    pw = PAL["power"]
    cx0, cy0, cx1, cy1 = c.clip_extents()
    vis = [p for p in pods if p[2] >= 2 and not (p[0] + p[2] * 2 < cx0 or p[0] - p[2] * 2 > cx1 or
                                                 p[1] + p[3] * 1.4 < cy0 or p[1] - p[3] * 1.4 > cy1)]
    bins = [[], [], [], []]
    for p in vis:
        w = p[2]
        bins[0 if w < 14 else 1 if w < 32 else 2 if w < 70 else 3].append(p)
    body_col = mixc("#0b3a40", pw, 0.55)
    sil_col = "#123a44"
    for bi, grp in enumerate(bins):
        if not grp:
            continue
        lw = (1.2, 2.2, 3.5, 5.0)[bi]
        for (x, y, w, h, z, seed, g) in grp:
            core.rrect(c, x - w * 1.05, y - h * 0.78, w * 2.1, h * 1.56, w)
        core.fill(c, core.alpha(pw, 0.07))
        for (x, y, w, h, z, seed, g) in grp:
            core.rrect(c, x - w * 0.78, y - h * 0.64, w * 1.56, h * 1.28, w * 0.75)
        core.fill(c, core.alpha(pw, 0.10))
        for (x, y, w, h, z, seed, g) in grp:
            core.rrect(c, x - w / 2, y - h / 2, w, h, w / 2)
        fs(c, body_col, lw)
        big = [p for p in grp if p[2] > 10]
        if sleeper_fn is not None:
            for (x, y, w, h, z, seed, g) in big:
                c.save()
                core.rrect(c, x - w / 2, y - h / 2, w, h, w / 2)
                c.clip()
                sleeper_fn(c, x, y + h * 0.08, w / 300.0, 0.0, seed)
                c.restore()
        elif big:
            for (x, y, w, h, z, seed, g) in big:
                _sleeper_path(c, x, y + h * 0.08, w / 300.0)
            core.fill(c, sil_col)
            for (x, y, w, h, z, seed, g) in big:
                sc_ = w / 300.0
                c.move_to(x - 100 * sc_, y + h * 0.08 + 50 * sc_)
                c.curve_to(x - 160 * sc_, y + h * 0.08 + 100 * sc_, x - 120 * sc_, y + h * 0.08 + 140 * sc_,
                           x - 60 * sc_, y + h * 0.08 + 110 * sc_)
            core.stroke(c, sil_col, max(1.5, 22 * big[0][2] / 300.0))
        for (x, y, w, h, z, seed, g) in big:
            core.rrect(c, x - w * 0.32, y - h * 0.42, w * 0.18, h * 0.8, w * 0.09)
        core.fill(c, (1, 1, 1, 0.16))
        for (x, y, w, h, z, seed, g) in grp:
            core.rrect(c, x - w * 0.62, y - h / 2 - h * 0.1, w * 1.24, h * 0.14, w * 0.1)
            core.rrect(c, x - w * 0.62, y + h / 2 - h * 0.04, w * 1.24, h * 0.14, w * 0.1)
        fs(c, "#2a4654", lw)
        # nameplates on the bottom caps (readable text on the near pods)
        plated = [p for p in grp if p[2] > 26]
        for (x, y, w, h, z, seed, g) in plated:
            core.rrect(c, x - w * 0.44, y + h / 2 - h * 0.005, w * 0.88, h * 0.075, w * 0.04)
        if plated:
            fs(c, "#b9c3cc", max(1.0, lw * 0.6))
        for (x, y, w, h, z, seed, g) in plated:
            idx = _SH_INDEX.get((round(x, 1), round(y, 1)))
            txt = (labels or {}).get(idx) or _SH_DEFAULT_LABELS.get(idx)
            if txt is None:
                txt = f"SPECIMEN {(idx or 0) % 100:02d}" if w > 90 else None
            if txt and (w > 44 or (idx in (labels or {}) or idx in _SH_DEFAULT_LABELS) and w > 18):
                fsz = min(h * 0.055, w * 1.5 / max(4, len(txt)))
                core.text(c, txt, x, y + h / 2 + h * 0.055, fsz, "#1f2a33", "ui")
            elif w > 26:
                line(c, [(x - w * 0.25, y + h / 2 + h * 0.035), (x + w * 0.25, y + h / 2 + h * 0.035)],
                     "#6b7a8c", max(1.0, h * 0.02))
    # light beams from far above + haze bands
    for (bx, bw, ang) in ((300, 160, 0.10), (720, 220, -0.06), (520, 90, 0.02)):
        gb = cairo.LinearGradient(0, -200, 0, 2600)
        gb.add_color_stop_rgba(0, 0.85, 1.0, 0.98, 0.22)
        gb.add_color_stop_rgba(1, 0.85, 1.0, 0.98, 0.0)
        c.move_to(bx, -200); c.line_to(bx + bw, -200)
        c.line_to(bx + bw * 2.2 + ang * 2600, 2600); c.line_to(bx - bw * 0.6 + ang * 2600, 2600)
        c.close_path()
        c.set_source(gb)
        c.fill()
    for (hy, hh, a) in ((900, 260, 0.10), (1700, 300, 0.10), (2650, 420, 0.16), (3300, 500, 0.22)):
        gh = cairo.LinearGradient(0, hy - hh / 2, 0, hy + hh / 2)
        gh.add_color_stop_rgba(0, 0.25, 0.95, 0.88, 0)
        gh.add_color_stop_rgba(0.5, 0.25, 0.95, 0.88, a)
        gh.add_color_stop_rgba(1, 0.25, 0.95, 0.88, 0)
        c.rectangle(x0, hy - hh / 2, x1 - x0, hh)
        c.set_source(gh)
        c.fill()
    # darkness far above
    gt = cairo.LinearGradient(0, -200, 0, 700)
    gt.add_color_stop_rgba(0, 0.02, 0.05, 0.08, 0.85)
    gt.add_color_stop_rgba(1, 0.02, 0.05, 0.08, 0.0)
    c.rectangle(x0, -200, x1 - x0, 900)
    c.set_source(gt)
    c.fill()
    # a bridge across the shaft below the catwalk
    by = _SH_HZ + _SH_F * 1.25 / _SH_CAM
    rect(c, x0, by, x1 - x0, 40, "#24404c", 5)
    for k in range(int((x1 - x0) / 60)):
        line(c, [(x0 + k * 60, by), (x0 + k * 60 + 30, by - 70)], "#3b6070", 4)
    line(c, [(x0, by - 70), (x1, by - 70)], "#3b6070", 6)
    # the near catwalk + the side tunnel mouth they come out of (left)
    _sh_catwalk(c, deck=True)


def _sh_catwalk(c, deck=True):
    y = _SH_CAT_Y
    x0, x1 = _SH_X0, 660
    if deck:
        tx, ty = SHAFT_MARKS["tunnel_mouth"]
        c.move_to(tx - 120, ty); c.line_to(tx - 120, ty - 170)
        c.arc(tx, ty - 170, 120, math.pi, 0)
        c.line_to(tx + 120, ty); c.close_path()
        fs(c, "#081a1e", 5)
        _glow(c, tx, ty - 120, 220, PAL["power"], 0.25)
        rect(c, x0, y, x1 - x0, 26, "#3b5a66", 5)
        rect(c, x0, y + 26, x1 - x0, 30, "#24404c", 4)
        for k in range(int((x1 - x0) / 40)):
            line(c, [(x0 + k * 40, y + 30), (x0 + k * 40 + 20, y + 52)], "#33505c", 3)
        # support struts
        for sx in (-300, 200, 600):
            line(c, [(sx, y + 56), (sx - 120, y + 260)], "#24404c", 10)
    # railing (front)
    rail_h = 120
    for k in range(int((x1 - x0) / 46) + 1):
        px = x0 + k * 46
        line(c, [(px, y + 4), (px, y - rail_h)], "#5d7f8c", 4)
    line(c, [(x0, y - rail_h), (x1, y - rail_h)], INK, 12)
    line(c, [(x0, y - rail_h), (x1, y - rail_h)], "#7fa0ac", 7)
    line(c, [(x0, y - rail_h * 0.5), (x1, y - rail_h * 0.5)], "#5d7f8c", 4)
    line(c, [(x1, y + 4), (x1, y - rail_h)], INK, 10)


def shaft(ctx, t=0.0, layer="bg", sleeper_fn=None, sleeper_key=None, pulse=True, glow=1.0,
          power=1.0, power_sections=None, pod_glow=None, lit=None, labels=None, shutters=None,
          shutters_except=None):
    """The containment shaft (world 1080 x 3600; drawable x -700..1780 so
    the camera can pull out to zoom ~0.56). Tiers of teal pods ring the
    curved wall (near pods big, far pods small), tier ledges, a bridge,
    the near catwalk (feet at SHAFT_MARKS["catwalk_feet_y"], s~0.22),
    a giant logo, static beams and haze.

    sleeper_fn(ctx, x, y, s, t, seed) draws each sleeper; pods are CACHED
    with the sleepers drawn once at t=0 (pass sleeper_key, e.g. "spec", so
    the cache knows the drawing). Per frame only a cheap shared glow pulse
    (3 phase groups, ~0.25 Hz) is drawn over visible pods.
    layer "fg" = the catwalk front railing (draw over the characters).

    Episode 2 (all optional, defaults = Episode 1 look):
    * power 0..1 / power_sections (6 bands, top first: SHAFT_MARKS
      ["sections"], use shaft_power_sections(t, t0, n=6)): lights out by
      section = darkness wash (DARK_A) per band; the pulse fades with it.
    * pod_glow 0..1 (None = follows power, EMBER when dark): what the pods
      keep glowing in dark sections (batched live fill).
    * lit True / False forces the lit / dark look (fx sense reveal).
    * labels {pod index: "TEXT"}: nameplates on the bottom caps (near pods
      show "SPECIMEN nn" by default; the tiny JOY pod at the bottom centre
      is SHAFT_MARKS["joy_pod"]). Baked: changing labels re-renders.
    * shutters 0..1 (or a list per section): steel shutters slide down over
      every pod (s07 lockdown); shutters_except = pod indices left open
      (e.g. [SHAFT_MARKS["joy_pod"]]).
    layer "shade": darkness for characters (use with sets.shaded()).
    """
    n = len(_SH_BANDS)
    ps = _section_powers(power, power_sections, n, lit)
    bands = SHAFT_MARKS["sections"]
    if layer == "bg":
        lk = tuple(sorted((labels or {}).items()))
        key = ("shaft", sleeper_key or (getattr(sleeper_fn, "__qualname__", None) if sleeper_fn else None), lk)
        _overscan(ctx, _SH_X0, -200, _SH_X1, SHAFT_H + 200, "#06121a", "#0f3a40", "#0f2d38", "#0f2d38")
        static_layer(ctx, key, _SH_X0, -200, _SH_X1 - _SH_X0, SHAFT_H + 400,
                     lambda c: _sh_static(c, sleeper_fn, labels), max_mp=2.5, tile_px=1100)
        vx0, vy0, vx1, vy1 = ctx.clip_extents()
        if pulse and glow > 0:
            amps = [0.5 + 0.5 * math.sin(t * TAU * 0.25 + g * 2.1) for g in range(3)]
            pw = hexc(PAL["power"])
            for bi, (by0, by1) in enumerate(bands):
                pk = ps[bi]
                if pk <= 0.02 or by1 < vy0 or by0 > vy1:
                    continue
                for gi in range(3):
                    a = 0.16 * glow * amps[gi] * pk
                    if a < 0.01:
                        continue
                    m = 0
                    for (x, y, w, h) in _SH_PULSE[bi][gi]:
                        if x + w < vx0 or x - w > vx1 or y + h < vy0 or y - h > vy1:
                            continue
                        # capsule-ish octagon (no arcs: ~5x cheaper to rasterise)
                        hw, hh, cw_ = w * 0.55, h * 0.55, w * 0.24
                        ctx.move_to(x - hw + cw_, y - hh)
                        ctx.line_to(x + hw - cw_, y - hh)
                        ctx.line_to(x + hw, y - hh + cw_ * 1.6)
                        ctx.line_to(x + hw, y + hh - cw_ * 1.6)
                        ctx.line_to(x + hw - cw_, y + hh)
                        ctx.line_to(x - hw + cw_, y + hh)
                        ctx.line_to(x - hw, y + hh - cw_ * 1.6)
                        ctx.line_to(x - hw, y - hh + cw_ * 1.6)
                        ctx.close_path()
                        m += 1
                    if m:
                        ctx.set_source_rgba(pw[0], pw[1], pw[2], a)
                        ctx.fill()
        if lit is not True and min(ps) < 0.999:
            _wash_bands(ctx, bands, ps)
            # what the pods keep glowing in the dark sections
            for bi, (by0, by1) in enumerate(bands):
                pk = ps[bi]
                if pk >= 0.999 or by1 < vy0 or by0 > vy1:
                    continue
                res = 1 - DARK_A * (1 - pk)                 # glow left in the washed bake
                want = lerp(EMBER, 1.0, pk) if pod_glow is None else clamp(float(pod_glow))
                diff = want - res
                if abs(diff) < 0.01:
                    continue
                col = PAL["power"] if diff > 0 else DARK
                al = min(0.9, abs(diff) * (0.75 if diff > 0 else 1.0 / max(0.05, res) * 0.6))
                m = 0
                for (x, y, w, h, z, seed, grp) in _SH_PODS:
                    if w < 2 or y < by0 or y >= by1:
                        continue
                    if x + w < vx0 or x - w > vx1 or y + h < vy0 or y - h > vy1:
                        continue
                    core.rrect(ctx, x - w / 2, y - h / 2, w, h, w / 2)
                    m += 1
                if m:
                    core.fill(ctx, core.alpha(col, al))
        if shutters is not None:
            shs = shutters if isinstance(shutters, (list, tuple)) else [shutters] * n
            skip = set(shutters_except or ())
            for bi, (by0, by1) in enumerate(bands):
                f = clamp(float(shs[min(bi, len(shs) - 1)]))
                if f <= 0.01 or by1 < vy0 or by0 > vy1:
                    continue
                dk = 0.0 if lit is True else DARK_A * (1 - ps[bi])
                m = 0
                for i, (x, y, w, h, z, seed, grp) in enumerate(_SH_PODS):
                    if w < 2 or y < by0 or y >= by1 or i in skip:
                        continue
                    if x + w < vx0 or x - w > vx1 or y + h < vy0 or y - h > vy1:
                        continue
                    ctx.rectangle(x - w * 0.62, y - h * 0.62, w * 1.24, h * 1.24 * f)
                    m += 1
                if m:
                    core.fill(ctx, mixc("#56646f", DARK, dk), preserve=True)
                    core.stroke(ctx, INK, 2.5)
                    for i, (x, y, w, h, z, seed, grp) in enumerate(_SH_PODS):
                        if w < 14 or y < by0 or y >= by1 or i in skip:
                            continue
                        if x + w < vx0 or x - w > vx1 or y + h < vy0 or y - h > vy1:
                            continue
                        yy = y - h * 0.62 + h * 1.24 * f
                        ctx.move_to(x - w * 0.62, yy - h * 0.06)
                        ctx.line_to(x + w * 0.62, yy - h * 0.06)
                    core.stroke(ctx, mixc(PAL["warn"], DARK, dk), 3)
    elif layer == "fg":
        d4 = 0.0 if lit is True else DARK_A * (1 - ps[4])
        dimmed(ctx, (_SH_X0, _SH_CAT_Y - 140, 660 - _SH_X0 + 20, 160), d4,
               lambda c: cached_or_live(c, "shaft_rail", _SH_X0, _SH_CAT_Y - 140, 660 - _SH_X0 + 20, 160,
                                        lambda cc: _sh_catwalk(cc, deck=False)))
    elif layer == "shade":
        _wash_bands(ctx, bands, ps, a=DARK_A * 0.94)


# ============================================================================
# EPISODE 2 INFRASTRUCTURE: alpha blits, translucent tiles, light sections,
# darkness and character shading
# ============================================================================
DARK = "#03070b"      # the darkness wash colour (near-black blue)
DARK_A = 0.86         # wash strength at power 0: "almost black but readable"
EMBER = 0.14          # pod glow left once the lights are out (pod_glow=None)


def _q_of(ctx):
    m = ctx.get_matrix()
    sc = math.hypot(m.xx, m.yx)
    if sc <= 0:
        return 0.0
    n = core._Q_STEPS[-1]
    return 2 ** (math.ceil(math.log2(sc) * n - 1e-6) / n)


def blit(ctx, key, x0, y0, w, h, draw_fn, alpha=1.0, pad=4, clip=None):
    """core.cached() with an opacity and an optional exact clip rect.

    Shares core's LRU and scale quantisation (same cache entry as
    core.cached for the same key). The cache key ignores x0/y0, so a
    position-independent drawing (drawn around a translated origin) is a
    reusable sprite.
    """
    if alpha <= 0.003:
        return
    q = _q_of(ctx)
    if q <= 0:
        return
    k = (key, round(q, 5), w, h)
    surf = core._LAYERS.get(k)
    if surf is None:
        sw, sh = int(math.ceil((w + 2 * pad) * q)), int(math.ceil((h + 2 * pad) * q))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, sw), max(1, sh))
        c = cairo.Context(surf)
        c.scale(q, q)
        c.translate(-(x0 - pad), -(y0 - pad))
        draw_fn(c)
        surf.flush()
        core._LAYERS[k] = surf
        while len(core._LAYERS) > core._LAYERS_MAX:
            core._LAYERS.popitem(last=False)
    else:
        core._LAYERS.move_to_end(k)
    ctx.save()
    if clip is not None:
        ctx.rectangle(*clip)
        ctx.clip()
    ctx.translate(x0 - pad, y0 - pad)
    ctx.scale(1 / q, 1 / q)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.rectangle(0, 0, surf.get_width(), surf.get_height())
    if alpha >= 0.997:
        ctx.fill()
    else:
        ctx.clip()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def layer_blit(ctx, key, x0, y0, w, h, draw_fn, alpha=1.0, clip=None, max_mp=None, tile_px=2040):
    """Big cached layer with opacity, for OPAQUE or TRANSLUCENT drawings.

    One bitmap when small; above max_mp (default MAX_LAYER_MP) it is split
    into ~tile_px tiles, and each tile is blitted clipped exactly to its own
    rect, so translucent layers have no seams. clip = optional (x, y, w, h)
    to restrict the blit (e.g. a light section band). Only visible tiles
    are rendered / blitted.
    """
    if alpha <= 0.003:
        return
    if clip is not None:
        cx0, cy0 = max(x0, clip[0]), max(y0, clip[1])
        cx1, cy1 = min(x0 + w, clip[0] + clip[2]), min(y0 + h, clip[1] + clip[3])
        if cx1 <= cx0 or cy1 <= cy0:
            return
        clip = (cx0, cy0, cx1 - cx0, cy1 - cy0)
    if not _visible(ctx, *(clip or (x0, y0, w, h))):
        return
    q = _q_of(ctx)
    if q <= 0:
        return
    if w * h * q * q <= (MAX_LAYER_MP if max_mp is None else max_mp) * 1e6:
        blit(ctx, key, x0, y0, w, h, draw_fn, alpha, clip=clip)
        return
    T = max(160, int(tile_px / q) // 32 * 32)
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    if clip is not None:
        vx0, vy0 = max(vx0, clip[0]), max(vy0, clip[1])
        vx1, vy1 = min(vx1, clip[0] + clip[2]), min(vy1, clip[1] + clip[3])
    nx, ny = int(math.ceil(w / T)), int(math.ceil(h / T))
    for j in range(ny):
        ty = y0 + j * T
        th = min(T, y0 + h - ty)
        if ty + th <= vy0 or ty >= vy1:
            continue
        for i in range(nx):
            tx = x0 + i * T
            tw = min(T, x0 + w - tx)
            if tx + tw <= vx0 or tx >= vx1:
                continue
            ex0, ey0 = max(tx, vx0), max(ty, vy0)
            ex1, ey1 = min(tx + tw, vx1), min(ty + th, vy1)
            blit(ctx, (key, "tile", i, j, T), tx, ty, tw, th, draw_fn, alpha,
                 clip=(ex0, ey0, ex1 - ex0, ey1 - ey0))


def dimmed(ctx, bbox, dim, draw_fn, col=DARK):
    """Draw draw_fn(ctx) darkened by `dim` (0..1, the darkness-wash
    strength), like the cached dark sets. The wash is applied ATOP the
    drawing inside a small group clipped to bbox (x, y, w, h), so only the
    drawing darkens."""
    if dim <= 0.003:
        draw_fn(ctx)
        return
    if not _visible(ctx, *bbox):
        return
    ctx.save()
    ctx.rectangle(*bbox)
    ctx.clip()
    ctx.push_group()
    draw_fn(ctx)
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.rectangle(*bbox)
    core.fill(ctx, core.alpha(col, dim))
    ctx.pop_group_to_source()
    ctx.paint()
    ctx.restore()


from collections import OrderedDict as _OD2
_SPR = _OD2()
_SPR_MAX = 64


def sprite(ctx, key, x0, y0, w, h, draw_fn, alpha=1.0, max_mp=4.0, pad=4):
    """Small cached drawing in its OWN LRU (64 entries), separate from
    core's set-layer cache, so animated live pieces (doors, plates, the
    security camera...) can cache per state without evicting big tiles.
    Draws live when the bitmap would exceed max_mp."""
    if alpha <= 0.003 or not _visible(ctx, x0, y0, w, h):
        return
    q = _q_of(ctx)
    if q <= 0:
        return
    if w * h * q * q > max_mp * 1e6:
        if alpha >= 0.997:
            draw_fn(ctx)
        else:
            ctx.push_group()
            draw_fn(ctx)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha)
        return
    k = (key, round(q, 5), w, h)
    surf = _SPR.get(k)
    if surf is None:
        sw, sh = int(math.ceil((w + 2 * pad) * q)), int(math.ceil((h + 2 * pad) * q))
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, sw), max(1, sh))
        c = cairo.Context(surf)
        c.scale(q, q)
        c.translate(-(x0 - pad), -(y0 - pad))
        draw_fn(c)
        surf.flush()
        _SPR[k] = surf
        while len(_SPR) > _SPR_MAX:
            _SPR.popitem(last=False)
    else:
        _SPR.move_to_end(k)
    ctx.save()
    ctx.translate(x0 - pad, y0 - pad)
    ctx.scale(1 / q, 1 / q)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.rectangle(0, 0, surf.get_width(), surf.get_height())
    if alpha >= 0.997:
        ctx.fill()
    else:
        ctx.clip()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def _dim_into(c, bbox, dim, draw_fn, col=DARK):
    """(for bakes) draw_fn darkened by dim inside bbox, ATOP."""
    if dim <= 0.003:
        draw_fn(c)
        return
    c.save()
    c.rectangle(*bbox)
    c.clip()
    c.push_group()
    draw_fn(c)
    c.set_operator(cairo.OPERATOR_ATOP)
    c.rectangle(*bbox)
    core.fill(c, core.alpha(col, dim))
    c.pop_group_to_source()
    c.paint()
    c.restore()


def dim_sprite(ctx, key, bbox, dim, draw_fn):
    """A live piece darkened by dim, cached in the sprite LRU per
    (key, dim): pass a key that changes with the piece's state."""
    sprite(ctx, (key, round(dim, 3)), *bbox, lambda c: _dim_into(c, bbox, dim, draw_fn))


def _steady(vals):
    return all(v == 0.0 or v == 1.0 for v in vals)


def shaft_power_at(section, t, t0, step=0.55, dur=0.16):
    """Lights-out cascade: the power 0..1 of light `section` (0 = the top)
    at scene time t, when the cascade starts at t0. Section k cuts out at
    t0 + k*step with one heavy "chunk" (dip to 0.25, a brief catch at 0.5,
    then off, all within `dur`; no strobing)."""
    ts = t0 + section * step
    if t < ts:
        return 1.0
    k = (t - ts) / max(1e-6, dur)
    if k >= 1:
        return 0.0
    if k < 0.3:
        return lerp(1.0, 0.25, k / 0.3)
    if k < 0.55:
        return lerp(0.25, 0.5, (k - 0.3) / 0.25)
    return lerp(0.5, 0.0, (k - 0.55) / 0.45)


def shaft_power_sections(t, t0, n=4, step=0.55, dur=0.16):
    """[shaft_power_at(k, t, t0, step, dur) for k in range(n)]: pass it as
    power_sections= to catwalk / shaft (n = <SET>_MARKS["n_sections"])."""
    return [shaft_power_at(k, t, t0, step, dur) for k in range(n)]


def shaft_power_times(t0, n=4, step=0.55):
    """The cut-out ("chunk" SFX) time of each section, top first."""
    return [t0 + k * step for k in range(n)]


def _section_powers(power, power_sections, n, lit=None):
    if lit is True:
        return [1.0] * n
    if lit is False:
        return [0.0] * n
    p = clamp(float(power))
    if power_sections is None:
        return [p] * n
    ps = list(power_sections) + [power_sections[-1]] * max(0, n - len(power_sections))
    return [p * clamp(float(v)) for v in ps[:n]]


def _wash_bands(ctx, bands, powers, a=DARK_A, col=DARK, x0=None, x1=None):
    """Darkness wash over each horizontal band (y0, y1) at a*(1-power)."""
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    if x0 is not None:
        vx0, vx1 = max(vx0, x0), min(vx1, x1)
    for (by0, by1), p in zip(bands, powers):
        al = a * (1 - p)
        if al <= 0.002:
            continue
        y0, y1 = max(vy0, by0), min(vy1, by1)
        if y1 <= y0:
            continue
        ctx.rectangle(vx0 - 2, y0, vx1 - vx0 + 4, y1 - y0)
        core.fill(ctx, core.alpha(col, al))


def _band_of(bands, y):
    for i, (y0, y1) in enumerate(bands):
        if y0 <= y < y1:
            return i
    return len(bands) - 1


class shaded:
    """Light the characters like the set they stand in.

        with sets.shaded(ctx, sets.catwalk, t, layer="shade", power=p):
            human.draw_tired(ctx, ...)
            creatures.draw_specimen(ctx, ...)

    Everything drawn inside the block goes into a group; the set's "shade"
    layer (darkness wash per light section + coloured light from pods /
    monitors / lamps) is then composited ATOP it (only where the
    characters are), and the group is painted. So characters darken with
    the lights without darkening the background twice. Cost: one
    frame-sized group (~1-2 ms at 720p).
    """
    def __init__(self, ctx, set_fn, *args, **kw):
        self.ctx, self.fn, self.args, self.kw = ctx, set_fn, args, kw

    def __enter__(self):
        self.ctx.push_group()
        return self.ctx

    def __exit__(self, *exc):
        c = self.ctx
        c.save()
        c.set_operator(cairo.OPERATOR_ATOP)
        self.fn(c, *self.args, **self.kw)
        c.restore()
        c.pop_group_to_source()
        c.paint()


# ============================================================================
# 13. SHAFT CATWALK (Episode 2 s01-s02): side-on, human scale
# ============================================================================
CATWALK_W, CATWALK_H = 3600, 1920
_CW_X0, _CW_X1, _CW_Y0, _CW_Y1 = -800, 4400, -1400, 2720
_CW_WALL, _CW_FEET, _CW_FRONT = 1380, 1500, 1720
_CW_LEDGE, _CW_LEDGE2 = 560, -320
_CW_ST_TOP, _CW_ST_N, _CW_ST_RISE, _CW_ST_RUN = 640, 6, 45, 86
_CW_ST_BOT = _CW_ST_TOP - _CW_ST_N * _CW_ST_RUN               # 124
_CW_LAND_FEET = _CW_FEET + _CW_ST_N * _CW_ST_RISE               # 1770
_CW_LAND_WALL, _CW_LAND_FRONT = _CW_LAND_FEET - 120, _CW_LAND_FEET + 220
_CW_VP = (1800, 900)
_CW_PIPE = (-90, 1150)         # low pipe contact point (the bonk), s = 0.75
_CW_CAM = (1250, 650)          # security camera wall mount
_CW_BANDS = [(-1e9, _CW_LEDGE2 + 40), (_CW_LEDGE2 + 40, _CW_LEDGE + 40), (_CW_LEDGE + 40, _CW_WALL),
             (_CW_WALL, 1e9)]
_CW_MAIN = [(1000, "CURIOSITY", "SPECIMEN 00", "empty"), (1500, "JOY", "SPECIMEN 01", "tiny"),
            (1990, "COURAGE", "SPECIMEN 02", "pod"), (2480, "CALM", "SPECIMEN 03", "pod"),
            (2970, "WONDER", "SPECIMEN 04", "pod"), (3460, "HOPE", "SPECIMEN 05", "pod"),
            (3950, "TRUST", "SPECIMEN 06", "pod")]
_CW_UP = [760 + 490 * k for k in range(8)]
_CW_TOP = [1000 + 490 * k for k in range(-1, 8)]
_CW_LAMPS = [760, 1745, 2725, 3705]
_CW_LAMPS2 = [1005, 1985, 2965, 3945]
_CW_PLATE_S = 0.74


def _cw_pod_geo(x, kind, base_y=_CW_WALL, sc=1.0):
    """Glass rect, cap rects, ground point for a pod standing on base_y."""
    if kind == "tiny":
        gw, gh, bh, cw_, th = 200, 320, 100, 300, 64
    else:
        gw, gh, bh, cw_, th = 330, 560, 100, 410, 80
    gw, gh, bh, cw_, th = gw * sc, gh * sc, bh * sc, cw_ * sc, th * sc
    gb = base_y - bh
    gt = gb - gh
    return {"glass": (x - gw / 2, gt, gw, gh), "base": (x - cw_ / 2, gb, cw_, bh),
            "top": (x - cw_ / 2 * 0.98, gt - th, cw_ * 0.98, th), "ground": (x, gb - 26 * sc),
            "plate_c": (x, gb + bh / 2), "s": sc * (0.45 if kind == "tiny" else 0.75)}


def _cw_labels(labels):
    out = []
    for i, (x, text, sub, kind) in enumerate(_CW_MAIN):
        v = None
        if callable(labels):
            v = labels(i, (text, sub))
        elif labels:
            v = labels.get(i, labels.get(text))
        if v is not None:
            if isinstance(v, (tuple, list)):
                text, sub = v[0], (v[1] if len(v) > 1 else sub)
            else:
                text = v
        out.append((x, text, sub, kind))
    return out


CATWALK_MARKS = {
    "size": (CATWALK_W, CATWALK_H),
    "drawable": (_CW_X0, _CW_Y0, _CW_X1, _CW_Y1),
    "char_scale": 0.75,
    "feet_y": _CW_FEET,              # walk line on the main deck (x 640 .. 4400)
    "wall_y": _CW_WALL,              # where the deck meets the pod wall
    "front_y": _CW_FRONT,            # deck front edge (railing, fg)
    "deck_x": (_CW_ST_TOP, _CW_X1),
    "stair_top": (_CW_ST_TOP, _CW_FEET),
    "stair_steps": [(_CW_ST_TOP - (i + 0.5) * _CW_ST_RUN, _CW_FEET + (i + 1) * _CW_ST_RISE)
                    for i in range(_CW_ST_N)],
    "stair_bottom": (_CW_ST_BOT, _CW_LAND_FEET),
    "landing_feet_y": _CW_LAND_FEET,  # lower walkway (x -800 .. 124)
    "landing_x": (_CW_X0, _CW_ST_BOT),
    "bonk_pipe": _CW_PIPE,           # props.low_pipe anchor = contact point (s 0.75)
    "bonk_face": _CW_PIPE,           # the face touches here walking LEFT
    "bonk_feet": (_CW_PIPE[0] + 46, _CW_LAND_FEET),
    "sec_cam": _CW_CAM,
    "lamps": [(x, _CW_LEDGE + 40) for x in _CW_LAMPS],
    "n_sections": len(_CW_BANDS),
    "sections": [(max(a, _CW_Y0), min(b, _CW_Y1)) for a, b in _CW_BANDS],   # top -> bottom
    "pods": [],                      # filled below
    "cam": {
        "pod_close": (1170, 1290, 3.0),     # Curiosity's face at its empty pod (feet 1235, 1500)
        "pod_two": (1290, 1140, 1.75),      # Curiosity at the pod + Tiredness walking up
        "plate": (1000, 1330, 4.2),         # the empty pod's nameplate (or use props.nameplate)
        "plates_pan_a": (1500, 1180, 1.6),  # pan right along JOY .. HOPE (cy keeps plates < y 1300)
        "plates_pan_b": (3460, 1180, 1.6),
        "cam_up": (1250, 760, 2.4),         # the security camera swivelling
        "wide": (1700, 900, 0.62),
        "cascade": (1500, 640, 0.56),       # whole wall, lights die top -> down
        "eyes_dark": (1180, 1180, 1.8),
        "stair": (400, 1360, 1.25),
        "bonk": (-20, 1300, 1.7),
    },
}
for _i, (_x, _t, _sb, _k) in enumerate(_CW_MAIN):
    _g = _cw_pod_geo(_x, _k)
    _pw, _ph = 0, 0
    CATWALK_MARKS["pods"].append({
        "x": _x, "label": _t, "sub": _sb, "kind": _k, "glass": _g["glass"], "ground": _g["ground"],
        "plate_c": _g["plate_c"], "sleeper_s": _g["s"]})
_E = CATWALK_MARKS["pods"][0]
CATWALK_MARKS["empty_pod"] = 0
CATWALK_MARKS["empty_glass"] = _E["glass"]
CATWALK_MARKS["paw_spot"] = (_E["x"] + 120, 1236)          # on the glass at creature paw height
CATWALK_MARKS["creature_at_pod"] = (_E["x"] + 235, _CW_FEET)  # feet; faces LEFT to the glass
CATWALK_MARKS["tired_at_pod"] = (_E["x"] + 560, _CW_FEET)
CATWALK_MARKS["fog_spot"] = (_E["x"] + 70, 1170)


def _cw_plate_rect(text, sub, cx, cy):
    w, h = props.nameplate_size(text, sub)
    s = _CW_PLATE_S
    return (cx - w * s / 2, cy - h * s / 2, w * s, h * s)


for _p in CATWALK_MARKS["pods"]:
    _p["plate"] = _cw_plate_rect(_p["label"], _p["sub"], *_p["plate_c"])
CATWALK_MARKS["empty_plate"] = CATWALK_MARKS["pods"][0]["plate"]


def _capsule(c, x, y, w, h):
    core.rrect(c, x, y, w, h, w / 2)


def _cw_ledge(c, y, x0, x1, base_col="#2c4a56"):
    rect(c, x0, y, x1 - x0, 40, base_col, 5)
    rect(c, x0, y - 12, x1 - x0, 14, "#45656f", 4)
    rect(c, x0, y + 40, x1 - x0, 12, "#33505a", 4)       # strip light housing (lit in the lamps layer)
    for k in range(int((x1 - x0) / 150) + 1):
        px = x0 + k * 150
        line(c, [(px, y - 12), (px, y - 110)], "#46666f", 5)
    line(c, [(x0, y - 110), (x1, y - 110)], INK, 10)
    line(c, [(x0, y - 110), (x1, y - 110)], "#5d7f8c", 6)
    line(c, [(x0, y - 60), (x1, y - 60)], "#46666f", 4)


def _cw_pod_shell(c, x, kind, sc=1.0, base_y=_CW_WALL, plate=None, tubes_to=None):
    """Unlit pod: caps, tubes, dark glass, plate (base layer)."""
    g = _cw_pod_geo(x, kind, base_y, sc)
    gx, gy, gw, gh = g["glass"]
    bx, by, bw, bh = g["base"]
    tx, ty, tw, th = g["top"]
    if tubes_to is not None:
        for side in (-1, 1):
            px = x + side * tw * 0.28
            line(c, [(px, ty + 6), (px, tubes_to)], INK, 20 * sc)
            line(c, [(px, ty + 6), (px, tubes_to)], "#3b4757", 11 * sc)
    _capsule(c, gx - 10 * sc, gy - 10 * sc, gw + 20 * sc, gh + 20 * sc)
    fs(c, "#2a3a46", 5)
    _capsule(c, gx, gy, gw, gh)
    fs(c, "#0a1d23", 4)
    rect(c, tx, ty, tw, th, "#4a5868", 5, r=22 * sc)
    line(c, [(tx + 20 * sc, ty + th * 0.5), (tx + tw - 20 * sc, ty + th * 0.5)], "#6b7a8c", 5 * sc)
    rect(c, bx, by, bw, bh, "#4a5868", 5, r=16 * sc)
    rect(c, bx + 8 * sc, by + 6 * sc, bw - 16 * sc, 8 * sc, "#6b7a8c", 0, r=4)
    if plate:
        text, sub = plate
        props.nameplate(c, x, by + bh / 2, _CW_PLATE_S * sc, text=text, sub=sub, seed=int(x) % 97)
    return g


def _cw_empty_interior(c, g, lit):
    """Inside of Curiosity's empty pod (behind its glass door)."""
    gx, gy, gw, gh = g["glass"]
    c.save()
    _capsule(c, gx, gy, gw, gh)
    c.clip()
    if lit:
        core.vgradient(c, mixc("#0b3a40", PAL["power"], 0.70), mixc("#0b3a40", PAL["power"], 0.40), gx, gy, gw, gh)
        core.radial_glow(c, gx + gw / 2, gy + 70, gw * 0.9, "#e9fffd", 0.55)
        sc_col = mixc("#0b3a40", PAL["power"], 0.22)
        drip = mixc("#0b3a40", PAL["power"], 0.85)
    else:
        c.rectangle(gx, gy, gw, gh)
        core.fill(c, "#0c2228")
        sc_col = "#081619"
        drip = "#12303a"
    # back-wall ribs of the capsule
    for k in (0.3, 0.7):
        line(c, [(gx + gw * k, gy), (gx + gw * k, gy + gh)], core.alpha(sc_col, 0.5), 5)
    # claw scratches (it got out on its own)
    for k in range(3):
        curve(c, [(gx + gw * 0.52 + k * 16, gy + gh * 0.48), (gx + gw * 0.58 + k * 16, gy + gh * 0.58),
                  (gx + gw * 0.56 + k * 16, gy + gh * 0.70)], sc_col, 5)
    # drained: drip lines + a puddle on the floor grate
    for k in range(4):
        xx = gx + gw * (0.18 + 0.2 * k)
        line(c, [(xx, gy + gh * (0.25 + 0.1 * hash01(k, 4))), (xx, gy + gh * (0.45 + 0.2 * hash01(k, 5)))],
             drip, 4)
    ell(c, gx + gw / 2, gy + gh - 26, gw * 0.42, 16, drip, 0)
    for k in range(5):
        line(c, [(gx + gw * (0.22 + k * 0.14), gy + gh - 40), (gx + gw * (0.22 + k * 0.14), gy + gh - 12)],
             sc_col, 4)
    c.restore()


def _cw_glass_lit(c, g, seed, sleeper_fn, t=0.0):
    """Lit glass content of an occupied pod (pods layer)."""
    gx, gy, gw, gh = g["glass"]
    pw = PAL["power"]
    c.save()
    _capsule(c, gx, gy, gw, gh)
    c.clip()
    core.vgradient(c, mixc("#0b3a40", pw, 0.52), mixc("#0b3a40", pw, 0.70), gx, gy, gw, gh)
    core.radial_glow(c, gx + gw / 2, gy + gh * 0.6, gw * 0.85, "#e9fffd", 0.30)
    gxx, gyy = g["ground"]
    if sleeper_fn is not None:
        sleeper_fn(c, gxx, gyy, g["s"], t, seed)
    else:
        props.sleeper_silhouette(c, gxx, gyy - 110 * g["s"], g["s"], 0.0, seed, color="#0f3640")
    for k in range(4):
        bx = gx + gw * (0.2 + 0.6 * hash01(k, seed + 3))
        byy = gy + gh * (0.15 + 0.5 * hash01(k, seed + 4))
        core.circle(c, bx, byy, (5 + 5 * hash01(k, seed + 5)) * gw / 330)
        core.stroke(c, (0.85, 1.0, 0.98, 0.6), 2.5)
    line(c, [(gx, gy + 44 * gh / 560), (gx + gw, gy + 44 * gh / 560)], (0.9, 1.0, 1.0, 0.5), 4)
    core.poly(c, [(gx + gw * 0.16, gy + 30), (gx + gw * 0.30, gy + 20), (gx + gw * 0.30, gy + gh - 30),
                  (gx + gw * 0.16, gy + gh - 40)])
    core.fill(c, (1, 1, 1, 0.16))
    c.restore()
    _capsule(c, gx, gy, gw, gh)
    core.stroke(c, INK, 4)


def _cw_pod_glow(c, g, kind):
    gx, gy, gw, gh = g["glass"]
    cx, cy = gx + gw / 2, gy + gh / 2
    core.radial_glow(c, cx, cy, gw * 1.7, PAL["power"], 0.34)
    bx, by, bw, bh = g["base"]
    core.radial_glow(c, cx, by + bh + 60, gw * 1.1, PAL["power"], 0.22)
    tx, ty, tw, th = g["top"]
    for k in range(3):
        core.circle(c, cx - tw * 0.18 + k * tw * 0.18, ty + th * 0.5, 7 * gw / 330)
    core.fill(c, PAL["power"])


def _cw_base(c, lab=None):
    lab = lab or _CW_MAIN
    x0, x1, y0, y1 = _CW_X0, _CW_X1, _CW_Y0, _CW_Y1
    g = cairo.LinearGradient(0, y0, 0, _CW_WALL)
    g.add_color_stop_rgba(0, *hexc("#0b222a"))
    g.add_color_stop_rgba(1, *hexc("#16363f"))
    c.rectangle(x0, y0, x1 - x0, _CW_LAND_WALL - y0 + 4)
    c.set_source(g)
    c.fill()
    # wall panels + seams + ribs
    for yy in range(int(y0) + 120, _CW_LAND_WALL, 230):
        line(c, [(x0, yy), (x1, yy)], "#123038", 4)
    ribs = sorted(set(_CW_UP + [_CW_ST_TOP - 60]))
    for rx in ribs:
        rect(c, rx - 34, y0, 68, _CW_LAND_WALL - y0, "#1b414c", 4)
        line(c, [(rx - 18, y0), (rx - 18, _CW_LAND_WALL)], "#24525e", 5)
        for yy in range(int(y0) + 60, _CW_LAND_WALL, 230):
            core.circle(c, rx, yy, 6)
        core.fill(c, "#0f2a32")
    # conduits behind the pods
    for (yy, col, w) in ((664, "#24505c", 26), (706, "#1f4652", 18), (1200, "#1f4652", 22)):
        rect(c, x0, yy, x1 - x0, w, col, 4)
    for k in range(14):
        cx = _CW_ST_TOP + 60 + k * 270
        line(c, [(cx, 664), (cx, 706 + 18)], "#173a44", 6)
    # hazard stripe along the wall base
    ctx = c
    for (wy, xa, xb) in ((_CW_WALL, _CW_ST_TOP, x1), (_CW_LAND_WALL, x0, _CW_ST_TOP)):
        props.hazard_band(ctx, xa, wy - 34, xb - xa, 22, step=40, col1="#9c8530", col2="#1a2a30", lw=3)
    # signage by the stair
    rect(c, 300, 1050, 250, 120, "#24404c", 4.5, r=10)
    core.text(c, "LEVEL B2", 425, 1102, 34, "#cfe9ee", "ui")
    core.text(c, "SHAFT A  ▼", 425, 1146, 28, PAL["hush"], "ui")
    # top darkness
    gt = cairo.LinearGradient(0, y0, 0, -200)
    gt.add_color_stop_rgba(0, 0.01, 0.04, 0.06, 0.92)
    gt.add_color_stop_rgba(1, 0.01, 0.04, 0.06, 0.0)
    # third tier (top) + its ledge
    for i, x in enumerate(_CW_TOP):
        _cw_pod_shell(c, x, "pod", 0.86, base_y=_CW_LEDGE2, tubes_to=_CW_LEDGE2 - 900)
    _cw_ledge(c, _CW_LEDGE2, x0, x1)
    # upper tier + ledge
    for i, x in enumerate(_CW_UP):
        _cw_pod_shell(c, x, "pod", 0.86, base_y=_CW_LEDGE, plate=(f"SPECIMEN {i + 12:02d}", None),
                      tubes_to=_CW_LEDGE2 + 52)
    _cw_ledge(c, _CW_LEDGE, _CW_ST_TOP - 120, x1)
    c.rectangle(x0, y0, x1 - x0, -200 - y0)
    c.set_source(gt)
    c.fill()
    # main tier pods (plates; the empty pod's plate + door are live)
    for i, (x, text, sub, kind) in enumerate(lab):
        g_ = _cw_pod_shell(c, x, kind, 1.0, plate=None if kind == "empty" else (text, sub),
                           tubes_to=_CW_LEDGE + 52)
        if kind == "empty":
            _cw_empty_interior(c, g_, False)
    # lamps (off) + camera mount area
    for x in _CW_LAMPS:
        props.cage_lamp(c, x, _CW_LEDGE + 64, 0.8, on=0.0, halo=False)
    for x in _CW_LAMPS2:
        props.cage_lamp(c, x, _CW_LEDGE2 + 64, 0.7, on=0.0, halo=False)
    # main deck
    dx0 = _CW_ST_TOP
    c.rectangle(dx0, _CW_WALL, x1 - dx0, _CW_FRONT - _CW_WALL)
    fs(c, "#36545f", 5)
    for k in range(int((x1 - dx0) / 44) + 1):
        xx = dx0 + k * 44
        line(c, [(xx, _CW_WALL + 6), (xx - 30, _CW_FRONT - 6)], "#2c4853", 4)
    for yy in (_CW_WALL + 70, _CW_WALL + 170, _CW_WALL + 270):
        line(c, [(dx0, yy), (x1, yy)], "#2c4853", 3)
    c.rectangle(dx0, _CW_WALL, x1 - dx0, 22)
    core.fill(c, core.alpha(INK, 0.35))
    rect(c, dx0, _CW_FRONT, x1 - dx0, 50, "#24404c", 5)
    for k in range(int((x1 - dx0) / 120) + 1):
        core.circle(c, dx0 + 30 + k * 120, _CW_FRONT + 25, 5)
    core.fill(c, "#3b5a66")
    # landing (lower walkway, left)
    lx1 = _CW_ST_BOT + 40
    c.rectangle(x0, _CW_LAND_WALL, lx1 - x0, _CW_LAND_FRONT - _CW_LAND_WALL)
    fs(c, "#36545f", 5)
    for k in range(int((lx1 - x0) / 44) + 1):
        xx = x0 + k * 44
        line(c, [(xx, _CW_LAND_WALL + 6), (xx - 30, _CW_LAND_FRONT - 6)], "#2c4853", 4)
    c.rectangle(x0, _CW_LAND_WALL, lx1 - x0, 22)
    core.fill(c, core.alpha(INK, 0.35))
    rect(c, x0, _CW_LAND_FRONT, lx1 - x0, 50, "#24404c", 5)
    # the void below (dark teal haze; distant pods glow in the pods layer)
    gv = cairo.LinearGradient(0, _CW_FRONT + 50, 0, y1)
    gv.add_color_stop_rgba(0, *hexc("#0d2a33"))
    gv.add_color_stop_rgba(1, *hexc("#04121a"))
    core.poly(c, [(dx0, _CW_FRONT + 50), (x1, _CW_FRONT + 50), (x1, y1), (x0, y1), (x0, _CW_LAND_FRONT + 50),
                  (lx1, _CW_LAND_FRONT + 50), (lx1, _CW_LAND_WALL), (dx0, _CW_WALL)])
    c.set_source(gv)
    c.fill()
    for k in range(40):
        vx = x0 + 120 * k + 60 * (k % 3)
        vy = 2050 + 160 * (k % 4) + 30 * hash01(k, 3)
        if vy < _CW_LAND_FRONT + 120 and vx < lx1 + 60:
            continue
        core.rrect(c, vx, vy, 20, 34, 10)
    core.fill(c, "#0f3138")
    # deck supports
    for sx in range(int(dx0) + 200, int(x1), 600):
        line(c, [(sx, _CW_FRONT + 50), (sx - 140, _CW_FRONT + 320)], "#1b3540", 14)
    # stair: open steel treads between two stringers
    _cw_stair(c, "back")
    _cw_stair(c, "treads")


def _cw_stair(c, part):
    top, n, rise, run = _CW_ST_TOP, _CW_ST_N, _CW_ST_RISE, _CW_ST_RUN
    bx, by = _CW_ST_BOT, _CW_LAND_FEET
    if part == "back":
        # back stringer + handrail along the wall
        polyf(c, [(top + 20, _CW_FEET - 40), (top + 20, _CW_FEET + 10), (bx - 40, by + 10), (bx - 40, by - 40)],
              "#24404c", 4.5)
        line(c, [(top + 20, _CW_FEET - 330), (bx - 40, by - 330)], INK, 10)
        line(c, [(top + 20, _CW_FEET - 330), (bx - 40, by - 330)], "#5d7f8c", 6)
        for k in range(4):
            px = lerp(top, bx, k / 3)
            py = lerp(_CW_FEET, by, k / 3)
            line(c, [(px, py - 330), (px, py - 30)], "#46666f", 5)
    elif part == "treads":
        for i in range(n):
            xr = top - i * run
            yt = _CW_FEET + (i + 1) * rise
            rect(c, xr - run - 6, yt - 4, run + 12, 20, "#4f6f7b", 4, r=3)
            line(c, [(xr - run, yt + 1), (xr, yt + 1)], "#7fa0ac", 3)
        # top / bottom plates
        rect(c, top - 8, _CW_FEET - 6, 30, 26, "#4f6f7b", 4)
    elif part == "front":
        polyf(c, [(top + 30, _CW_FEET + 20), (top + 30, _CW_FEET + 80), (bx - 30, by + 80), (bx - 30, by + 20)],
              "#2c4a56", 5)
        line(c, [(top + 30, _CW_FEET - 260), (bx - 30, by - 260)], INK, 12)
        line(c, [(top + 30, _CW_FEET - 260), (bx - 30, by - 260)], "#7fa0ac", 7)
        for k in range(3):
            px = lerp(top + 30, bx - 30, k / 2)
            py = lerp(_CW_FEET, by, k / 2)
            line(c, [(px, py - 260), (px, py + 30)], "#5d7f8c", 6)


def _cw_lamps(c):
    """Room lights (lamps layer, faded by section power)."""
    x0, x1 = _CW_X0, _CW_X1
    col = "#d8fbff"
    for (ly, xs, sc) in ((_CW_LEDGE + 64, _CW_LAMPS, 0.8), (_CW_LEDGE2 + 64, _CW_LAMPS2, 0.7)):
        for x in xs:
            by = ly + 92 * sc
            props.cage_lamp(c, x, ly, sc, on=1.0, color="#cff8ff", halo=False)
            core.radial_glow(c, x, by, 260, col, 0.45)
            fl = (_CW_WALL if ly > 0 else _CW_LEDGE) - 10
            gb = cairo.LinearGradient(0, by, 0, fl + 100)
            gb.add_color_stop_rgba(0, 0.85, 0.98, 1.0, 0.20)
            gb.add_color_stop_rgba(1, 0.85, 0.98, 1.0, 0.03)
            core.poly(c, [(x - 30, by), (x + 30, by), (x + 300, fl + 100), (x - 300, fl + 100)])
            c.set_source(gb)
            c.fill()
            ell(c, x, fl + 110, 320, 60, core.alpha(col, 0.18), 0)
    for (yy, xa) in ((_CW_LEDGE + 40, _CW_ST_TOP - 120), (_CW_LEDGE2 + 40, x0)):
        rect(c, xa + 10, yy + 2, x1 - xa - 20, 9, "#e9fdff", 0, r=4)
        gs = cairo.LinearGradient(0, yy + 10, 0, yy + 200)
        gs.add_color_stop_rgba(0, 0.85, 0.98, 1.0, 0.30)
        gs.add_color_stop_rgba(1, 0.85, 0.98, 1.0, 0.0)
        c.rectangle(xa, yy + 10, x1 - xa, 190)
        c.set_source(gs)
        c.fill()
    # a soft light beam from far above + bright deck edge
    for (bx, bw) in ((1500, 260), (2900, 200)):
        gb = cairo.LinearGradient(0, _CW_Y0, 0, _CW_LEDGE2)
        gb.add_color_stop_rgba(0, 0.85, 1.0, 0.98, 0.16)
        gb.add_color_stop_rgba(1, 0.85, 1.0, 0.98, 0.0)
        core.poly(c, [(bx, _CW_Y0), (bx + bw, _CW_Y0), (bx + bw * 1.6, _CW_LEDGE2), (bx - bw * 0.5, _CW_LEDGE2)])
        c.set_source(gb)
        c.fill()
    line(c, [(_CW_ST_TOP, _CW_FRONT + 3), (x1, _CW_FRONT + 3)], (0.8, 0.96, 1.0, 0.5), 4)


def _cw_pods_lit(c, sleeper_fn, sleeper_fns, lab=None):
    """Pod glow + lit glass content (pods layer, faded by pod_glow)."""
    lab = lab or _CW_MAIN
    for i, x in enumerate(_CW_TOP):
        g = _cw_pod_geo(x, "pod", _CW_LEDGE2, 0.86)
        _cw_pod_glow(c, g, "pod")
        _cw_glass_lit(c, g, 300 + i, sleeper_fn)
    for i, x in enumerate(_CW_UP):
        g = _cw_pod_geo(x, "pod", _CW_LEDGE, 0.86)
        _cw_pod_glow(c, g, "pod")
        _cw_glass_lit(c, g, 200 + i, sleeper_fn)
    for i, (x, text, sub, kind) in enumerate(lab):
        g = _cw_pod_geo(x, kind)
        _cw_pod_glow(c, g, kind)
        if kind == "empty":
            _cw_empty_interior(c, g, True)
            gx, gy, gw, gh = g["glass"]
            _capsule(c, gx, gy, gw, gh)
            core.stroke(c, INK, 4)
        else:
            fn = (sleeper_fns or {}).get(i, (sleeper_fns or {}).get(text, sleeper_fn))
            _cw_glass_lit(c, g, 100 + i, fn)
    # distant pods across the shaft, far below
    lx1 = _CW_ST_BOT + 40
    for k in range(40):
        vx = _CW_X0 + 120 * k + 60 * (k % 3)
        vy = 2050 + 160 * (k % 4) + 30 * hash01(k, 3)
        if vy < _CW_LAND_FRONT + 120 and vx < lx1 + 60:
            continue
        core.rrect(c, vx, vy, 20, 34, 10)
    core.fill(c, core.alpha(PAL["power"], 0.55))
    gh_ = cairo.LinearGradient(0, _CW_FRONT + 60, 0, _CW_Y1)
    gh_.add_color_stop_rgba(0, 0.25, 0.95, 0.88, 0.0)
    gh_.add_color_stop_rgba(0.5, 0.25, 0.95, 0.88, 0.10)
    gh_.add_color_stop_rgba(1, 0.25, 0.95, 0.88, 0.02)
    c.rectangle(_CW_X0, _CW_FRONT + 60, _CW_X1 - _CW_X0, _CW_Y1 - _CW_FRONT - 60)
    c.set_source(gh_)
    c.fill()


def _cw_empty_door(ctx, opening, lit_g):
    """Curiosity's pod door (glass pane, hinge on the RIGHT), live."""
    g = _cw_pod_geo(_CW_MAIN[0][0], "empty")
    gx, gy, gw, gh = g["glass"]
    q = door_quad(gx + gw, gy, gy + gh, gw, opening, _CW_VP, D=2600.0, toward=True, hinge_left=False)
    # q: hinge_top, free_top, free_bottom, hinge_bottom
    def P(u, v):  # u: 0 = free edge, 1 = hinge
        top = (lerp(q[1][0], q[0][0], u), lerp(q[1][1], q[0][1], u))
        bot = (lerp(q[2][0], q[3][0], u), lerp(q[2][1], q[3][1], u))
        return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
    rv = (gw / 2) / gh
    pts = []
    for k in range(13):
        th = math.pi - k * math.pi / 12
        pts.append(P(0.5 + 0.5 * math.cos(th), rv - rv * math.sin(th)))
    for k in range(13):
        th = k * math.pi / 12
        pts.append(P(0.5 + 0.5 * math.cos(th), 1 - rv + rv * math.sin(th)))
    core.poly(ctx, pts)
    core.fill(ctx, (0.75, 0.96, 1.0, 0.10 + 0.08 * lit_g))
    for (u0, u1) in ((0.18, 0.30), (0.38, 0.44)):
        core.poly(ctx, [P(u0, 0.08), P(u1, 0.06), P(u1 - 0.04, 0.9), P(u0 - 0.04, 0.92)])
        core.fill(ctx, (1, 1, 1, 0.20))
    core.poly(ctx, pts)
    core.stroke(ctx, "#5d7f8c", 10)
    core.poly(ctx, pts)
    core.stroke(ctx, INK, 4)
    for v in (0.22, 0.78):
        hx, hy = P(1.0, v)
        rect(ctx, hx - 8, hy - 18, 22, 36, "#4a5868", 3.5, r=4)
    # the unlatched latch, hanging down on the free edge
    lx, ly = P(0.0, 0.5)
    with core.saved(ctx, lx, ly, 1.0, 0.9):
        rect(ctx, -10, -8, 50, 16, "#8a96a2", 3.5, r=5)
    core.circle(ctx, lx, ly, 8)
    fs(ctx, "#4a5868", 3)
    return pts


def _band_blits(ctx, key, rect, fn, bands, alphas):
    x0, y0, w, h = rect
    if len(set(alphas)) == 1:
        layer_blit(ctx, key, x0, y0, w, h, fn, alpha=alphas[0])
        return
    for (by0, by1), a in zip(bands, alphas):
        if a > 0.003:
            layer_blit(ctx, key, x0, y0, w, h, fn, alpha=a,
                       clip=(x0, max(y0, by0), w, min(y0 + h, by1) - max(y0, by0)))


def _band_paint(c, bands, alphas, fn):
    """(for bakes) fn drawn per band at each band's opacity."""
    vx0, vy0, vx1, vy1 = c.clip_extents()
    for (by0, by1), a in zip(bands, alphas):
        if a <= 0.003 or by1 <= vy0 or by0 >= vy1:
            continue
        c.save()
        c.rectangle(vx0, max(vy0, by0), vx1 - vx0, min(vy1, by1) - max(vy0, by0))
        c.clip()
        if a >= 0.997:
            fn(c)
        else:
            c.push_group()
            fn(c)
            c.pop_group_to_source()
            c.paint_with_alpha(a)
        c.restore()


def _cw_compose(c, lab, pods_fn, ps, gs, lamps_on, wash_on, bands):
    _cw_base(c, lab)
    if lamps_on:
        _band_paint(c, bands, ps, _cw_lamps)
    if wash_on:
        _wash_bands(c, bands, ps)
    _band_paint(c, bands, gs, pods_fn)


def catwalk(ctx, t=0.0, layer="bg", power=1.0, power_sections=None, pod_glow=None, lit=None,
            labels=None, sleeper_fn=None, sleeper_fns=None, sleeper_key=None, door_open=0.12,
            plate_dust=0.85, plate_wipe=0.0, cam_angle=0.25, cam_face=0.0, cam_led=0.0,
            pipe_wobble=0.0, pipe_wobble_t0=0.0, pulse=True, bubbles=True, parts=None):
    """The shaft catwalk, side-on at human scale (world 3600 x 1920, people
    at s=0.75; drawable x -800..4400, y -1400..2720). See CATWALK_MARKS.

    The pod wall: a main tier of pods standing on the deck, each with a
    readable nameplate (CURIOSITY = Curiosity's EMPTY pod, door ajar and a
    dusty plate; then JOY (a tiny pod), COURAGE, CALM, WONDER, HOPE, TRUST),
    two more tiers above on ledges, caged lamps and strip lights, a wall
    security camera (red LED), the grated deck with the void below, and a
    short stair down to a lower walkway on the left where a LOW PIPE
    crosses at head height (the bonk).

    Light: power 0..1 (room lights) and power_sections (per section, top
    first; CATWALK_MARKS["n_sections"], see shaft_power_sections()), pod_glow
    0..1 (None = follows power: full .. EMBER), lit True = surfaces lit /
    False = dark regardless of power (fx: draw lit=True inside a sense
    ring). Three cached layers (surfaces, lamps, pod glow) are mixed by
    opacity, so any power value is cheap.

    labels: {index or default text: "TEXT" | ("TEXT", "SUB")} or a callable
    (i, (text, sub)) -> ... renames main-tier plates. sleeper_fn(ctx, x, y,
    s, t, seed) draws each sleeper at its ground point (x, y) on the pod
    floor (s 0.75, tiny pod 0.45); sleeper_fns {index or label: fn}
    overrides per pod (e.g. {"JOY": baby}). Sleepers are baked: pass
    sleeper_key (hashable) when you pass sleeper_fn(s).
    Live state: door_open (Curiosity's pod door, 0.12 = ajar), plate_dust /
    plate_wipe (its nameplate), cam_angle / cam_face / cam_led (None =
    blink), pipe_wobble (+ pipe_wobble_t0) after the bonk.
    layer "bg" | "fg" (parts: "rail" = deck front railing, "stair" = stair
    front stringer + handrail (default both); "pipe" = also draw the low pipe
    over the characters) | "shade" (character light: use with
    sets.shaded()).
    """
    n = len(_CW_BANDS)
    ps = _section_powers(power, power_sections, n, lit)
    if pod_glow is None:
        gs = [lerp(EMBER, 1.0, p) for p in _section_powers(power, power_sections, n)]
    else:
        gs = [clamp(float(pod_glow))] * n
    gsp = gs
    bands = CATWALK_MARKS["sections"]
    x0, y0, x1, y1 = _CW_X0, _CW_Y0, _CW_X1, _CW_Y1
    lab = tuple(_cw_labels(labels))
    if layer == "bg":
        _overscan(ctx, x0, y0, x1, y1, "#06141a", "#04121a", "#0b222a", "#0b222a")
        sk = sleeper_key or (getattr(sleeper_fn, "__qualname__", None) if sleeper_fn else None)
        pods_fn = lambda c: _cw_pods_lit(c, sleeper_fn, sleeper_fns, lab)
        lamps_on = lit is None
        wash_on = lit is not True
        if _steady(ps) and all(abs(g - round(g, 2)) < 1e-9 for g in gs):
            # a discrete light state: one precomposed bake (cheap to hold)
            st = (tuple(ps), tuple(round(g, 2) for g in gs), lamps_on, wash_on)
            layer_blit(ctx, ("catwalk_comp", lab, sk, st), x0, y0, x1 - x0, y1 - y0,
                       lambda c: _cw_compose(c, lab, pods_fn, ps, gs, lamps_on, wash_on, bands))
        else:
            # in transition: mix the three cached layers by opacity
            layer_blit(ctx, ("catwalk_base", lab), x0, y0, x1 - x0, y1 - y0, lambda c: _cw_base(c, lab))
            if lamps_on:
                _band_blits(ctx, "catwalk_lamps", (x0, y0, x1 - x0, y1 - y0), _cw_lamps, bands, ps)
            if wash_on:
                _wash_bands(ctx, bands, ps)
            _band_blits(ctx, ("catwalk_pods", lab, sk), (x0, y0, x1 - x0, y1 - y0), pods_fn, bands, gs)
        if pulse:
            # slow shared breathing glow over the main-tier glass (cheap fills)
            a = 0.10 * (0.5 + 0.5 * math.sin(t * TAU * 0.25)) * gs[2]
            if a > 0.01:
                for (x, text, sub, kind) in lab:
                    if kind != "empty":
                        gx, gy, gw, gh = _cw_pod_geo(x, kind)["glass"]
                        _capsule(ctx, gx, gy, gw, gh)
                core.fill(ctx, core.alpha(PAL["power"], a))
        dk = [0.0 if lit is True else DARK_A * (1 - p) for p in ps]
        dmain = dk[2]
        g2 = gsp[2]
        # live: bubbles in the main-tier pods
        if bubbles and g2 > 0.05:
            vx0, vy0, vx1, vy1 = ctx.clip_extents()
            for i, (x, text, sub, kind) in enumerate(_CW_MAIN):
                if kind == "empty" or x + 200 < vx0 or x - 200 > vx1:
                    continue
                gx, gy, gw, gh = _cw_pod_geo(x, kind)["glass"]
                for k in range(2):
                    ph = (t * 0.11 + hash01(k + i * 3, 9)) % 1.0
                    bx = gx + gw * (0.25 + 0.5 * hash01(k + i * 3, 10)) + 6 * math.sin(t * 1.7 + k + i)
                    byy = gy + gh - 40 - ph * (gh - 90)
                    core.circle(ctx, bx, byy, 6 + 4 * hash01(k + i, 11))
                    core.stroke(ctx, (0.88, 1.0, 0.98, 0.7 * g2 * math.sin(ph * math.pi)), 2.5)
        # live (sprite-cached per state): Curiosity's pod door + dusty plate
        g_e = _cw_pod_geo(lab[0][0], "empty")
        gx, gy, gw, gh = g_e["glass"]
        dop = round(float(door_open), 3)
        dim_sprite(ctx, ("cw_door", dop, round(g2, 2)), (gx - 260, gy - 80, gw + 520, gh + 160), dmain,
                   lambda c: _cw_empty_door(c, dop, g2))
        pcx, pcy = g_e["plate_c"]
        pr = _cw_plate_rect(lab[0][1], lab[0][2], pcx, pcy)
        pd, pwp = round(float(plate_dust), 3), round(float(plate_wipe), 3)
        dim_sprite(ctx, ("cw_plate", lab[0][1], lab[0][2], pd, pwp), (pr[0] - 6, pr[1] - 6, pr[2] + 12, pr[3] + 12),
                   dmain, lambda c: props.nameplate(c, pcx, pcy, _CW_PLATE_S, text=lab[0][1], sub=lab[0][2],
                                                    dust=pd, wipe=pwp, seed=5))
        # security camera (its red LED stays bright in the dark)
        cx_, cy_ = _CW_CAM
        ca_, cf_ = round(float(cam_angle), 3), round(float(cam_face), 3)
        dim_sprite(ctx, ("cw_cam", ca_, cf_), (cx_ - 60, cy_ - 80, 420, 420), dmain,
                   lambda c: props.security_camera(c, cx_, cy_, 0.8, 0.0, ca_, 0.0, cf_, glow=0))
        if cam_led is None or cam_led > 0:
            props.security_camera(ctx, cx_, cy_, 0.8, t, cam_angle, cam_led, cam_face, only_led=True)
        # the low pipe (live only while it wobbles)
        px_, py_ = _CW_PIPE
        kk = t - pipe_wobble_t0
        wob = pipe_wobble > 0 and 0 <= kk < 2.4
        pk = ("cw_pipe", round(kk, 3) if wob else None)
        dim_sprite(ctx, pk, (px_ - 900, py_ - 560, 1500, 680), dk[3],
                   lambda c: props.low_pipe(c, px_, py_, 0.75, t=t if wob else 0.0,
                                            wobble=pipe_wobble if wob else 0.0, wobble_t0=pipe_wobble_t0))
    elif layer == "fg":
        parts = parts or ("rail", "stair")
        d3 = 0.0 if lit is True else DARK_A * (1 - ps[3])
        if "stair" in parts:
            sb = (_CW_ST_BOT - 60, _CW_FEET - 300, _CW_ST_TOP - _CW_ST_BOT + 140, 700)
            dim_sprite(ctx, "cw_stair_fg", sb, d3, lambda c: _cw_stair(c, "front"))
        if "pipe" in parts:     # optional: the low pipe OVER the characters
            px_, py_ = _CW_PIPE
            dimmed(ctx, (px_ - 900, py_ - 560, 1500, 680), d3,
                   lambda c: props.low_pipe(c, px_, py_, 0.75, t=t, wobble=pipe_wobble,
                                            wobble_t0=pipe_wobble_t0))
        if "rail" in parts:
            vx0, vy0, vx1, vy1 = ctx.clip_extents()
            for (xa, xb, fy) in ((_CW_ST_TOP + 30, x1, _CW_FRONT), (x0, _CW_ST_BOT + 10, _CW_LAND_FRONT)):
                if fy + 20 < vy0 or fy - 300 > vy1:
                    continue
                k0 = max(0, int((vx0 - xa) // 900) - 1)
                k1 = int((min(vx1, xb) - xa) // 900) + 1
                for k in range(k0, k1 + 1):
                    tx = xa + k * 900
                    if tx >= xb:
                        break
                    ctx.save()
                    if tx + 900 > xb:
                        ctx.rectangle(tx - 12, fy - 310, xb - tx + 14, 340)
                        ctx.clip()
                    ctx.translate(tx, fy)
                    dim_sprite(ctx, "cw_rail_tile", (-12, -300, 924, 320), d3, _cw_rail_tile)
                    ctx.restore()
    elif layer == "shade":
        _wash_bands(ctx, bands, ps, a=DARK_A * 0.94)
        vx0, vy0, vx1, vy1 = ctx.clip_extents()
        for i, (x, text, sub, kind) in enumerate(_CW_MAIN):
            if x + 600 < vx0 or x - 600 > vx1:
                continue
            gx, gy, gw, gh = _cw_pod_geo(x, kind)["glass"]
            core.radial_glow(ctx, x, gy + gh * 0.7, 560, PAL["power"], 0.30 * gsp[2])


def _cw_rail_tile(c):
    """900-px repeat of the deck front railing (local: x 0..900, deck edge y 0)."""
    h = 280
    for k in range(5):
        px = k * 180
        line(c, [(px, 6), (px, -h)], INK, 11)
        line(c, [(px, 6), (px, -h)], "#5d7f8c", 6)
    for (yy, w, col) in ((-h, 12, "#7fa0ac"), (-h * 0.5, 9, "#5d7f8c")):
        line(c, [(-12, yy), (912, yy)], INK, w + 6, cap="butt")
        line(c, [(-12, yy), (912, yy)], col, w, cap="butt")


def _cw_rail(c, xa, xb, fy):
    h = 280
    for k in range(int((xb - xa) / 180) + 1):
        px = xa + k * 180
        line(c, [(px, fy + 6), (px, fy - h)], INK, 11)
        line(c, [(px, fy + 6), (px, fy - h)], "#5d7f8c", 6)
    for (yy, w, col) in ((fy - h, 12, "#7fa0ac"), (fy - h * 0.5, 9, "#5d7f8c")):
        line(c, [(xa, yy), (xb, yy)], INK, w + 6)
        line(c, [(xa, yy), (xb, yy)], col, w)


# ============================================================================
# 14. SHAFT LOWER LEVEL (Episode 2 s03): pipes, crates, stair, floor grates
# ============================================================================
SHAFT_LOWER_W, SHAFT_LOWER_H = 2600, 1920
_SL_X0, _SL_X1, _SL_Y0, _SL_Y1 = -900, 3300, -1000, 2620
_SL_WALL, _SL_FEET = 1300, 1500
_SL_ST = dict(x_top=-150, y_top=420, n=15, rise=72, run=70)
_SL_CRATE_A = (1400, 560, 470)            # centre x, w, h (bottom on the feet line)
_SL_CRATE_B = [(2290, 460, 400, "steel"), (2210, 300, 220, "wood")]
_SL_GRATES = [(260, 420), (1700, 380)]    # x, w (floor grates, glowing from below)
_SL_EXIT = (2470, 640, 300)               # doorway x, top y, w
_SL_LAMPS = [(330, 560), (1980, 560)]


def _sl_stair_steps():
    st = _SL_ST
    return [(st["x_top"] + (i + 0.5) * st["run"], st["y_top"] + (i + 1) * st["rise"]) for i in range(st["n"])]


SHAFT_LOWER_MARKS = {
    "size": (SHAFT_LOWER_W, SHAFT_LOWER_H),
    "drawable": (_SL_X0, _SL_Y0, _SL_X1, _SL_Y1),
    "char_scale": 0.75,
    "feet_y": _SL_FEET,
    "wall_y": _SL_WALL,
    "stair_top": (_SL_ST["x_top"], _SL_ST["y_top"]),        # platform up-left (x < -150)
    "stair_steps": _sl_stair_steps(),                        # tread centres, top first (descend right)
    "stair_bottom": (_SL_ST["x_top"] + _SL_ST["n"] * _SL_ST["run"], _SL_FEET),
    "crate_a": (_SL_CRATE_A[0] - _SL_CRATE_A[1] / 2, _SL_FEET - _SL_CRATE_A[2], _SL_CRATE_A[1], _SL_CRATE_A[2]),
    "hide_feet": (_SL_CRATE_A[0] - _SL_CRATE_A[1] / 2 - 140, _SL_FEET),   # crouched left of crate A
    "hide_feet2": (_SL_CRATE_A[0] - _SL_CRATE_A[1] / 2 - 330, _SL_FEET),
    "crate_b": (_SL_CRATE_B[0][0] - _SL_CRATE_B[0][1] / 2, _SL_FEET - _SL_CRATE_B[0][2], _SL_CRATE_B[0][1],
                _SL_CRATE_B[0][2]),
    "perch": (_SL_CRATE_B[0][0] + 110, _SL_FEET - _SL_CRATE_B[0][2]),    # sit on the lower crate (behind a guard)
    "guard_a": (2120, _SL_FEET),     # gruff guard in front of the crate stack
    "guard_b": (1830, _SL_FEET),
    "puddle": (2150, _SL_FEET + 6),  # floor spot for the shadow puddle
    "grates": [(x, _SL_FEET - 40, w, 110) for (x, w) in _SL_GRATES],
    "exit": (_SL_EXIT[0], _SL_EXIT[1], _SL_EXIT[2], _SL_WALL - _SL_EXIT[1]),
    "exit_feet": (_SL_EXIT[0] + _SL_EXIT[2] / 2, _SL_WALL + 40),
    "pipes": [(-900, 760, 4200, 95), (-900, 985, 4200, 70)],     # x, centre y, length, radius
    "lamps": _SL_LAMPS,
    "cam": {
        "wide": (1300, 1000, 0.6),
        "stair": (420, 1000, 0.95),
        "hide": (1180, 1170, 1.7),
        "troll": (2190, 1060, 1.9),
        "sneak": (1650, 1120, 1.15),
        "exit": (2380, 1100, 1.3),
    },
}


def _sl_wall(c):
    x0, x1, y0, y1 = _SL_X0, _SL_X1, _SL_Y0, _SL_Y1
    g = cairo.LinearGradient(0, y0, 0, _SL_WALL)
    g.add_color_stop_rgba(0, *hexc("#0a1d24"))
    g.add_color_stop_rgba(0.55, *hexc("#1a3a42"))
    g.add_color_stop_rgba(1, *hexc("#24464d"))
    c.rectangle(x0, y0, x1 - x0, _SL_WALL - y0 + 2)
    c.set_source(g)
    c.fill()
    # curved concrete bands of the shaft wall + panel joints
    for k, yy in enumerate(range(260, _SL_WALL, 170)):
        line(c, [(x0, yy), (x1, yy)], "#163238", 5)
        for xx in range(int(x0) + (k % 2) * 210, int(x1), 420):
            line(c, [(xx, yy), (xx, yy + 170)], "#163238", 4)
    for k in range(10):
        sx = hash01(k, 61) * (x1 - x0) + x0
        polyf(c, [(sx - 20, 300 + 400 * hash01(k, 62)), (sx + 20, 300 + 400 * hash01(k, 62)),
                  (sx + 26, _SL_WALL), (sx - 26, _SL_WALL)], (0.05, 0.13, 0.15, 0.35), 0)
    # big level stencil
    core.text(c, "B3", 1720, 610, 220, core.alpha("#0f262c", 0.85), "black")
    rect(c, 1620, 640, 230, 12, core.alpha("#c9a227", 0.55), 0)
    # girders overhead (underside of the catwalks) + darkness above
    for (yy, h) in ((40, 70), (-300, 50)):
        rect(c, x0, yy, x1 - x0, h, "#1b2f36", 5)
        rect(c, x0, yy + h, x1 - x0, 14, "#14252b", 3)
        for k in range(int((x1 - x0) / 260)):
            bx = x0 + k * 260
            line(c, [(bx, yy + h), (bx + 130, yy + h + 140)], "#1b2f36", 12)
            line(c, [(bx + 260, yy + h), (bx + 130, yy + h + 140)], "#1b2f36", 12)
    gt = cairo.LinearGradient(0, y0, 0, 300)
    gt.add_color_stop_rgba(0, 0.01, 0.04, 0.06, 0.95)
    gt.add_color_stop_rgba(1, 0.01, 0.04, 0.06, 0.0)
    c.rectangle(x0, y0, x1 - x0, 300 - y0)
    c.set_source(gt)
    c.fill()


def _sl_pipes(c):
    x0, x1 = _SL_X0, _SL_X1
    for (px, py, L, r) in SHAFT_LOWER_MARKS["pipes"]:
        col = "#3f6670" if r > 80 else "#4a6a62"
        rect(c, px, py - r, L, 2 * r, col, 6)
        line(c, [(px, py - r * 0.55), (px + L, py - r * 0.55)], mixc(col, "#ffffff", 0.22), r * 0.22)
        line(c, [(px, py + r * 0.6), (px + L, py + r * 0.6)], mixc(col, INK, 0.3), r * 0.25)
        for k in range(int(L / 520) + 1):
            fx = px + 260 + k * 520 + (60 if r < 80 else 0)
            rect(c, fx - 18, py - r - 12, 36, 2 * r + 24, "#2f4a52", 5, r=6)
            for yy in (py - r * 0.7, py, py + r * 0.7):
                core.circle(c, fx, yy, 5)
            core.fill(c, "#1d3037")
    # pipe brackets to the wall
    for k in range(9):
        bx = x0 + 300 + k * 480
        rect(c, bx - 14, 870, 28, 50, "#1f363d", 4)
    # vertical riser into the floor with an elbow
    vx, vr = 1080, 80
    rect(c, vx - vr, -400, 2 * vr, _SL_WALL - 60 + 400, "#3f6670", 6)
    line(c, [(vx - vr * 0.5, -400), (vx - vr * 0.5, _SL_WALL - 70)], "#5d838c", 14)
    rect(c, vx - vr - 14, _SL_WALL - 90, 2 * vr + 28, 40, "#2f4a52", 5, r=6)
    rect(c, vx - vr - 14, 600, 2 * vr + 28, 30, "#2f4a52", 5, r=6)
    # twin risers on the right
    for (vx2, vr2) in ((2020, 46), (2130, 46)):
        rect(c, vx2 - vr2, -400, 2 * vr2, _SL_WALL - 30 + 400, "#4a6a62", 5)
        line(c, [(vx2 - vr2 * 0.4, -400), (vx2 - vr2 * 0.4, _SL_WALL - 40)], "#64867c", 8)
    # big red valve wheel + gauge on the main pipe
    wx, wy = 1560, 760
    core.circle(c, wx, wy, 86)
    core.stroke(c, INK, 20)
    core.circle(c, wx, wy, 86)
    core.stroke(c, "#b5544a", 12)
    for a in range(4):
        an = a * math.pi / 4
        line(c, [(wx - math.cos(an) * 86, wy - math.sin(an) * 86), (wx + math.cos(an) * 86, wy + math.sin(an) * 86)],
             "#b5544a", 9)
    core.circle(c, wx, wy, 18)
    fs(c, "#7a2f2a", 4)
    core.circle(c, 760, 985 - 120, 44)
    fs(c, "#e9eef2", 5)
    line(c, [(760, 865), (782, 840)], INK, 4)
    line(c, [(760, 985 - 70), (760, 985 - 76)], INK, 6)
    # junction box + cable tray
    rect(c, 560, 1060, 220, 160, "#34505a", 5, r=8)
    rect(c, 580, 1080, 180, 26, "#24404a", 0, r=4)
    for k in range(3):
        core.circle(c, 610 + k * 40, 1160, 8)
        fs(c, ["#2a5a40", "#5a2a2a", "#2a5a40"][k], 3)
    rect(c, x0, 1150, 400 - x0, 18, "#2a434b", 4)


def _sl_floor(c):
    x0, x1, y1 = _SL_X0, _SL_X1, _SL_Y1
    c.rectangle(x0, _SL_WALL, x1 - x0, y1 - _SL_WALL)
    core.fill(c, "#2c4248")
    props.hazard_band(c, x0, _SL_WALL - 30, x1 - x0, 24, step=44, col1="#9c8530", col2="#1a2a30", lw=3)
    c.rectangle(x0, _SL_WALL, x1 - x0, 24)
    core.fill(c, core.alpha(INK, 0.4))
    # floor plates (perspective seams toward a low VP)
    vpx = 1300
    for k in range(-14, 26):
        xx = k * 180
        line(c, [(xx, _SL_WALL), (vpx + (xx - vpx) * 2.6, y1)], "#24383e", 4)
    for yy in (1380, 1480, 1620, 1820, 2100):
        line(c, [(x0, yy), (x1, yy)], "#24383e", 4)
    # grates (dark slots; the teal glow from below is in the glow pass)
    for (gx, gw) in _SL_GRATES:
        polyf(c, [(gx, _SL_FEET - 40), (gx + gw, _SL_FEET - 40), (gx + gw + 40, _SL_FEET + 70), (gx - 40, _SL_FEET + 70)],
              "#1a2a2f", 5)
        for k in range(1, 9):
            u = k / 9
            line(c, [(gx + gw * u, _SL_FEET - 36), (gx - 40 + (gw + 80) * u, _SL_FEET + 66)], "#3b545b", 6)
    # puddle + oil stain
    ell(c, 2150, 1560, 160, 22, "#24383e", 0)
    ell(c, 640, 1640, 120, 18, "#22343a", 0)


def _sl_grate_glow(c):
    for (gx, gw) in _SL_GRATES:
        core.radial_glow(c, gx + gw / 2, _SL_FEET + 20, gw * 0.8, PAL["power"], 0.30)
        c.save()
        core.poly(c, [(gx, _SL_FEET - 40), (gx + gw, _SL_FEET - 40), (gx + gw + 40, _SL_FEET + 70), (gx - 40, _SL_FEET + 70)])
        c.clip()
        for k in range(9):
            u = (k + 0.5) / 9
            line(c, [(gx + gw * u, _SL_FEET - 36), (gx - 40 + (gw + 80) * u, _SL_FEET + 66)],
                 core.alpha(PAL["power"], 0.55), 12)
        c.restore()


def _sl_stair(c, part="all"):
    st = _SL_ST
    xt, yt, n, rise, run = st["x_top"], st["y_top"], st["n"], st["rise"], st["run"]
    xb, yb = xt + n * run, yt + n * rise
    if part in ("all", "back"):
        # landing platform (top left) + back stringer + rail
        rect(c, _SL_X0, yt, xt - _SL_X0 + 20, 46, "#36545f", 5)
        rect(c, _SL_X0, yt + 46, xt - _SL_X0 + 20, 24, "#24404c", 4)
        polyf(c, [(xt, yt - 30), (xt, yt + 20), (xb, yb + 20), (xb, yb - 30)], "#24404c", 4.5)
        line(c, [(xt, yt - 330), (xb, yb - 330)], INK, 10)
        line(c, [(xt, yt - 330), (xb, yb - 330)], "#5d7f8c", 6)
        for k in range(6):
            px, py = lerp(xt, xb, k / 5), lerp(yt, yb, k / 5)
            line(c, [(px, py - 330), (px, py - 30)], "#46666f", 5)
        for i in range(n):
            xr = xt + (i + 1) * run
            ytr = yt + (i + 1) * rise
            rect(c, xr - run - 6, ytr - 4, run + 12, 20, "#4f6f7b", 4, r=3)
            line(c, [(xr - run, ytr + 1), (xr, ytr + 1)], "#7fa0ac", 3)
        # support column under the stair
        rect(c, xb - 360, yb - 330, 30, 330, "#24404c", 4)
    if part in ("all", "front"):
        polyf(c, [(xt + 10, yt + 30), (xt + 10, yt + 90), (xb - 10, yb + 90), (xb - 10, yb + 30)], "#2c4a56", 5)
        line(c, [(xt + 10, yt - 260), (xb - 10, yb - 260)], INK, 12)
        line(c, [(xt + 10, yt - 260), (xb - 10, yb - 260)], "#7fa0ac", 7)
        for k in range(4):
            px, py = lerp(xt + 10, xb - 10, k / 3), lerp(yt, yb, k / 3)
            line(c, [(px, py - 260), (px, py + 40)], "#5d7f8c", 6)


def _sl_crates(c, which="all"):
    if which in ("all", "a"):
        cx, w, h = _SL_CRATE_A
        props.crate(c, cx, _SL_FEET, 1.0, w=w, h=h, kind="wood", stencil="HUSHCORP", seed=1)
    if which in ("all", "b"):
        for (cx, w, h, kind) in _SL_CRATE_B[:1]:
            props.crate(c, cx, _SL_FEET, 1.0, w=w, h=h, kind=kind, stencil="HC-07")
        cx, w, h, kind = _SL_CRATE_B[1]
        props.crate(c, cx, _SL_FEET - _SL_CRATE_B[0][2] - 4, 1.0, w=w, h=h, kind=kind, stencil=None)
    if which == "all":
        # clutter: a barrel and a small crate under the stair
        bx = 920
        rect(c, bx - 60, _SL_FEET - 220, 120, 220, "#5a6f4a", 5, r=14)
        for yy in (_SL_FEET - 170, _SL_FEET - 60):
            line(c, [(bx - 60, yy), (bx + 60, yy)], "#43553a", 6)
        props.crate(c, 470, _SL_FEET - 10, 1.0, w=220, h=170, kind="steel", stencil=None)


def _sl_exit(c, lit_sign=False):
    ex, et, ew = _SL_EXIT
    rect(c, ex - 30, et - 30, ew + 60, _SL_WALL - et + 30, "#3b4757", 5)
    c.move_to(ex, _SL_WALL)
    c.line_to(ex, et + 60)
    c.curve_to(ex, et, ex + ew, et, ex + ew, et + 60)
    c.line_to(ex + ew, _SL_WALL)
    c.close_path()
    fs(c, "#081418", 4)
    rect(c, ex + 20, et - 110, ew - 40, 60, "#24404c", 4, r=8)
    core.text(c, "SERVICE TUNNEL", ex + ew / 2 - 14, et - 70, 26, "#cfe9ee", "ui")
    polyf(c, [(ex + ew - 40, et - 92), (ex + ew - 26, et - 80), (ex + ew - 40, et - 68)], "#cfe9ee", 0)


def _sl_lamps(c, on):
    for (lx, ly) in _SL_LAMPS:
        props.cage_lamp(c, lx, ly, 0.9, on=on, color="#ffe9b0", halo=False)
        if on:
            by = ly + 92 * 0.9
            core.radial_glow(c, lx, by, 320, "#fff3d0", 0.45)
            gb = cairo.LinearGradient(0, by, 0, _SL_FEET + 60)
            gb.add_color_stop_rgba(0, 1.0, 0.96, 0.85, 0.22)
            gb.add_color_stop_rgba(1, 1.0, 0.96, 0.85, 0.04)
            core.poly(c, [(lx - 30, by), (lx + 30, by), (lx + 380, _SL_FEET + 60), (lx - 380, _SL_FEET + 60)])
            c.set_source(gb)
            c.fill()
            ell(c, lx, _SL_FEET + 60, 400, 70, core.alpha("#fff3d0", 0.16), 0)


def _sl_base(c):
    _sl_wall(c)
    _sl_pipes(c)
    _sl_exit(c)
    _sl_lamps(c, 0.0)
    _sl_floor(c)
    _sl_stair(c, "back")
    _sl_crates(c, "all")


def _sl_emissive(c):
    """What still reads in the dark: grate glow, exit sign, box LEDs."""
    _sl_grate_glow(c)
    ex, et, ew = _SL_EXIT
    core.radial_glow(c, ex + ew / 2, et - 80, 200, "#5fffb0", 0.18)
    core.text(c, "SERVICE TUNNEL", ex + ew / 2 - 14, et - 70, 26, core.alpha("#7dffc0", 0.55), "ui")
    for k in range(3):
        core.circle(c, 610 + k * 40, 1160, 7)
        core.fill(c, ["#3ddc84", "#ff3b5c", "#3ddc84"][k])


def _sl_compose(c, state):
    """state: "lit" (surfaces under neutral light: the flashlight-cone
    version), "dark", or "on" (work lamps on)."""
    _sl_base(c)
    if state == "on":
        _sl_lamps(c, 1.0)
        _sl_grate_glow(c)
    elif state == "dark":
        x0, y0, x1, y1 = c.clip_extents()
        c.rectangle(x0, y0, x1 - x0, y1 - y0)
        core.fill(c, core.alpha(DARK, DARK_A))
        _sl_emissive(c)
    else:
        _sl_grate_glow(c)


def _sl_fg(c, parts):
    if "stair" in parts:
        _sl_stair(c, "front")
    if "crate" in parts:
        _sl_crates(c, "a")


def shaft_lower(ctx, t=0.0, layer="bg", power=0.0, lit=None, parts=None):
    """The lower level of the shaft (world 2600 x 1920, people at s=0.75;
    drawable x -900..3300, y -1000..2620). See SHAFT_LOWER_MARKS.

    A long steel stair comes down from the catwalk platform (top left) to
    the floor; big horizontal pipes with flanges and a red valve wheel, a
    vertical riser, a big crate to hide beside (crate_a), a crate stack to
    perch on behind a guard (crate_b / perch), a barrel, floor grates
    glowing faint teal from below, and the SERVICE TUNNEL doorway (right).

    power 0..1: work lamps (default 0: it is dark in s03). lit: True =
    surfaces as if lit, lamps off: draw it inside a flashlight cone (clip to
    the cone, then call with lit=True); False = the dark version (what is
    outside the cones; same as power=0). Every state is one cached bake;
    power in (0, 1) mixes two of them.
    layer "bg" | "fg" (parts: "stair" = front stringer + handrail
    (default), "crate" = crate A again over someone standing BEHIND it in
    depth) | "shade" (character darkness, sets.shaded()). fg pieces
    follow the same power / lit.
    """
    x0, y0, x1, y1 = _SL_X0, _SL_Y0, _SL_X1, _SL_Y1
    p = clamp(float(power))
    if lit is True:
        states = [("lit", 1.0)]
    elif lit is False or p <= 0.0:
        states = [("dark", 1.0)]
    elif p >= 1.0:
        states = [("on", 1.0)]
    else:
        states = [("dark", 1.0), ("on", p)]
    if layer == "bg":
        _overscan(ctx, x0, y0, x1, y1, "#03080b", "#0e171a", "#0a1d24", "#0a1d24")
        for st, a in states:
            layer_blit(ctx, ("shaft_lower", st), x0, y0, x1 - x0, y1 - y0, lambda c, st=st: _sl_compose(c, st),
                       alpha=a)
    elif layer == "fg":
        parts = tuple(parts or ("stair",))
        cxa, cwa, cha = _SL_CRATE_A
        boxes = {"stair": (x0, 80, 1100 - x0, 1580),
                 "crate": (cxa - cwa / 2 - 12, _SL_FEET - cha - 44, cwa + 50, cha + 56)}
        for part in parts:
            bb = boxes.get(part)
            if bb is None:
                continue
            for st, a in states:
                dim = DARK_A if st == "dark" else 0.0
                sprite(ctx, ("sl_fg", part, st), *bb,
                       lambda c, part=part, dim=dim, bb=bb: _dim_into(c, bb, dim, lambda cc: _sl_fg(cc, (part,))),
                       alpha=a)
    elif layer == "shade":
        if lit is True:
            return
        a = DARK_A * 0.94 * (1 - (p if lit is None else 0.0))
        if a > 0.003:
            vx0, vy0, vx1, vy1 = ctx.clip_extents()
            ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
            core.fill(ctx, core.alpha(DARK, a))


# ============================================================================
# 15. SERVICE TUNNEL (Episode 2 s04-s06): quiet concrete HushCorp corridor
# ============================================================================
TUNNEL_W, TUNNEL_H = 2400, 1920
_TN_X0, _TN_X1, _TN_Y0, _TN_Y1 = -700, 3100, -700, 2620
_TN_CEIL, _TN_WALL, _TN_FEET = 300, 1300, 1500
_TN_MOUTH = (90, 560, 420)                # depth-tunnel opening: x, top, w (bottom = wall base)
_TN_VP = (300, 1010)                      # its vanishing point
_TN_LAMPS = [(700, 520), (1330, 520), (1960, 520)]
_TN_SEAT = (1080, 150)                    # crate centre x, crate height (seat top = feet - h)
_TN_DOOR = (1990, 520, 340, 780)          # keycard door x, top, w, h (bottom = wall base)
_TN_READER = (2400, 960)
_TN_DRIP = (860, 1570)                    # puddle on the floor (drip falls from the pipe joint above)


def tunnel_depth(k, lane=0.0):
    """Walk path into the dark side tunnel: k = 0 at the mouth's floor in
    front (feet on the corridor line) .. 1 deep inside (tiny, near the
    vanishing point). Returns (x, y_feet, scale_factor): multiply the
    character's s by scale_factor. lane -1..1 = left..right wall."""
    k = clamp(k)
    mx, mt, mw = _TN_MOUTH
    cx0, fy0 = mx + mw / 2 + lane * mw * 0.3, _TN_FEET
    f = 1.0 / (1.0 + 5.0 * k)
    x = _TN_VP[0] + (cx0 - _TN_VP[0]) * f
    y = _TN_VP[1] + (fy0 - _TN_VP[1]) * f
    return (x, y, f)


TUNNEL_MARKS = {
    "size": (TUNNEL_W, TUNNEL_H),
    "drawable": (_TN_X0, _TN_Y0, _TN_X1, _TN_Y1),
    "char_scale": 0.75,
    "ceiling_y": _TN_CEIL,
    "wall_y": _TN_WALL,
    "feet_y": _TN_FEET,
    "seat": (_TN_SEAT[0], _TN_FEET - _TN_SEAT[1]),     # hips point on the crate (use ground_from_seat)
    "seat_feet": (_TN_SEAT[0], _TN_FEET),
    "seat_crate": (_TN_SEAT[0] - 180, _TN_FEET - _TN_SEAT[1], 360, _TN_SEAT[1]),
    "beside_seat": (_TN_SEAT[0] + 300, _TN_FEET),       # Curiosity tugging his sleeve
    "lamps": _TN_LAMPS,
    "mouth": (_TN_MOUTH[0], _TN_MOUTH[1], _TN_MOUTH[2], _TN_WALL - _TN_MOUTH[1]),
    "mouth_feet": (_TN_MOUTH[0] + _TN_MOUTH[2] / 2, _TN_FEET),
    "far_end": _TN_VP,               # vanishing point deep in the dark tunnel
    "far_path": [tunnel_depth(k) for k in (0.0, 0.25, 0.5, 0.75, 1.0)],
    "junction_sign": (330, 430),
    "door": _TN_DOOR,
    "door_feet": (_TN_DOOR[0] + _TN_DOOR[2] / 2, _TN_FEET),
    "doorway_feet": (_TN_DOOR[0] + _TN_DOOR[2] / 2, _TN_WALL + 20),   # someone stepping through
    "reader": _TN_READER,            # keycard reader slot centre
    "reader_feet": (_TN_READER[0] - 150, _TN_FEET),
    "drip": _TN_DRIP,
    "cam": {
        "wide": (1200, 1020, 0.62),
        "sit": (1130, 1160, 1.6),
        "sit_close": (1080, 1160, 2.5),
        "leave": (560, 1150, 1.15),       # Curiosity walks off into the dark side tunnel
        "junction": (520, 1130, 1.4),
        "alone": (980, 1150, 1.25),
        "door": (2170, 1050, 1.15),
        "reader": (2360, 1000, 2.6),
    },
}


def _tn_mouth_path(c, inset=0.0):
    mx, mt, mw = _TN_MOUTH
    c.move_to(mx + inset, _TN_WALL)
    c.line_to(mx + inset, mt + 110)
    c.curve_to(mx + inset, mt + inset, mx + mw - inset, mt + inset, mx + mw - inset, mt + 110)
    c.line_to(mx + mw - inset, _TN_WALL)
    c.close_path()


def _tn_mouth(c):
    """The side tunnel receding into darkness (one-point perspective)."""
    mx, mt, mw = _TN_MOUTH
    vx, vy = _TN_VP
    c.save()
    _tn_mouth_path(c)
    c.clip()
    c.rectangle(mx - 10, mt - 10, mw + 20, _TN_WALL - mt + 220)
    core.fill(c, "#2a2b31")
    # receding frames (ribs) getting darker toward the vanishing point
    for k in range(1, 9):
        f = 1.0 / (1.0 + 0.62 * k)
        x0, x1 = vx + (mx - vx) * f, vx + (mx + mw - vx) * f
        yt, yb = vy + (mt - vy) * f, vy + (_TN_FEET + 60 - vy) * f
        dk = clamp(0.25 + k * 0.1)
        core.rrect(c, x0, yt, x1 - x0, yb - yt, (x1 - x0) * 0.3)
        fs(c, mixc("#3a3a40", "#050608", dk), 3, sc=mixc("#2a2a30", "#050608", dk))
    # floor of the side tunnel
    core.poly(c, [(mx, _TN_FEET + 80), (mx + mw, _TN_FEET + 80), (vx + 18, vy + 22), (vx - 18, vy + 22)])
    core.fill(c, (0.05, 0.05, 0.06, 0.55))
    core.radial_glow(c, vx, vy, 160, "#000000", 0.9)
    c.restore()
    _tn_mouth_path(c)
    core.stroke(c, INK, 6)
    _tn_mouth_path(c, -26)
    core.stroke(c, "#5a5a62", 18)
    _tn_mouth_path(c, -26)
    core.stroke(c, INK, 4)


def _tn_door_frame(c):
    dx, dt, dw, dh = _TN_DOOR
    rect(c, dx - 46, dt - 46, dw + 92, dh + 46, "#3b4757", 6)
    props.hazard_band(c, dx - 46, dt - 46, dw + 92, 26, step=40, lw=4)
    rect(c, dx, dt, dw, dh, "#0b1016", 4)
    rect(c, dx + dw / 2 - 110, dt - 128, 220, 60, PAL["hush_dk"], 4.5, r=8)
    spaced_text(c, "CONTROL", dx + dw / 2, dt - 86, 32, "#ffffff", "ui", 0.18)
    rect(c, dx - 10, dt + dh * 0.32, 22, 90, "#2a3440", 0)
    # reader on the wall
    rx, ry = _TN_READER
    rect(c, rx - 40, ry - 80, 80, 150, "#2a3240", 5, r=12)
    rect(c, rx - 24, ry - 60, 48, 30, "#121820", 3, r=4)
    rect(c, rx - 28, ry + 6, 56, 8, "#0b0f15", 0, r=3)
    core.text(c, "LVL 9", rx, ry + 50, 19, "#9fb3c4", "mono")


def _tn_back(c):
    """Seen through the open CONTROL door: the dark control room, monitor glow."""
    dx, dt, dw, dh = _TN_DOOR
    c.rectangle(dx - 4, dt - 4, dw + 8, dh + 8)
    core.fill(c, "#0a1420")
    core.radial_glow(c, dx + dw / 2, dt + dh * 0.45, dw * 1.1, "#5fd8ff", 0.35)
    for i in range(3):
        for j in range(2):
            rect(c, dx + 30 + i * 100, dt + 120 + j * 110, 84, 80, mixc("#1d4f66", "#7fe8ff", 0.35 + 0.2 * ((i + j) % 2)),
                 3, r=4)
    rect(c, dx - 4, dt + dh - 120, dw + 8, 124, "#0c1720", 0)
    # the tall chair's back, silhouetted
    rect(c, dx + dw * 0.5 - 50, dt + 300, 100, 380, "#06090e", 0, r=34)
    rect(c, dx + dw * 0.5 - 12, dt + 680, 24, 70, "#06090e", 0)
    line(c, [(dx + dw * 0.5 - 48, dt + 320), (dx + dw * 0.5 - 48, dt + 640)], core.alpha("#7fe8ff", 0.5), 4)


def _tn_door_panels(ctx, opening):
    dx, dt, dw, dh = _TN_DOOR
    o = clamp(opening) * (dw / 2 - 4)
    ctx.save()
    ctx.rectangle(dx, dt, dw, dh)
    ctx.clip()
    for side in (-1, 1):
        px = dx + (0 if side < 0 else dw / 2) + side * o
        rect(ctx, px, dt, dw / 2, dh, "#8794a2", 5)
        rect(ctx, px + 14, dt + 14, dw / 2 - 28, dh - 28, None, 3.5, sc="#6f7d8c")
        props.hazard_band(ctx, px + (dw / 2 - 30 if side < 0 else 0), dt, 30, dh, step=36, lw=3, slant=0.8)
        rect(ctx, px + 30, dt + 120, dw / 2 - 60, 120, "#5a6878", 3.5, r=6)
        core.text(ctx, "LVL 9", px + dw / 4, dt + 196, 30, "#e9eef2", "ui")
    ctx.restore()


def _tn_reader_light(ctx, light):
    rx, ry = _TN_READER
    col = {"green": PAL["safe"], "red": PAL["danger"]}.get(light)
    if col:
        core.radial_glow(ctx, rx, ry - 45, 70, col, 0.6)
        rect(ctx, rx - 24, ry - 60, 48, 30, col, 3, r=4)
        rect(ctx, rx - 16, ry - 54, 18, 6, (1, 1, 1, 0.6), 0, r=2)


def _tn_static(c):
    x0, x1, y0, y1 = _TN_X0, _TN_X1, _TN_Y0, _TN_Y1
    # ceiling
    c.rectangle(x0, y0, x1 - x0, _TN_CEIL - y0 + 2)
    core.fill(c, "#26262c")
    for (yy, r_, col) in ((150, 40, "#4a5458"), (232, 30, "#5a5148"), (80, 24, "#3e4648")):
        rect(c, x0, yy - r_, x1 - x0, 2 * r_, col, 4.5)
        line(c, [(x0, yy - r_ * 0.45), (x1, yy - r_ * 0.45)], mixc(col, "#ffffff", 0.18), r_ * 0.3)
        for k in range(int((x1 - x0) / 460) + 1):
            fx = x0 + 200 + k * 460 + r_ * 3
            rect(c, fx - 10, yy - r_ - 8, 20, 2 * r_ + 16, "#33383c", 4, r=4)
    rect(c, x0, _TN_CEIL - 16, x1 - x0, 20, "#3b3b42", 4)
    # concrete wall: lower panel, upper panel, form-tie dots, stains
    c.rectangle(x0, _TN_CEIL, x1 - x0, _TN_WALL - _TN_CEIL)
    core.fill(c, "#5b5b62")
    c.rectangle(x0, 960, x1 - x0, _TN_WALL - 960)
    core.fill(c, "#52525a")
    rect(c, x0, 940, x1 - x0, 22, PAL["hush_dk"], 0)
    for xx in range(int(x0), int(x1), 300):
        line(c, [(xx, _TN_CEIL), (xx, _TN_WALL)], "#4c4c53", 4)
        for yy in (420, 640, 860, 1120):
            core.circle(c, xx + 75, yy, 5)
            core.circle(c, xx + 225, yy, 5)
    core.fill(c, "#47474e")
    for k in range(9):
        sx = x0 + hash01(k, 71) * (x1 - x0)
        polyf(c, [(sx - 16, 330 + 200 * hash01(k, 72)), (sx + 16, 330 + 200 * hash01(k, 72)),
                  (sx + 24, _TN_WALL), (sx - 24, _TN_WALL)], (0.2, 0.2, 0.24, 0.35), 0)
    # section stencils
    for (sx, txt) in ((1020, "S-14"), (1640, "S-15")):
        core.text(c, txt, sx, 860, 64, core.alpha("#3a3a42", 0.9), "black")
    # vertical pipe + conduit + junction box
    rect(c, 1500, _TN_CEIL - 40, 64, _TN_WALL - _TN_CEIL + 20, "#5a6466", 5)
    line(c, [(1514, _TN_CEIL), (1514, _TN_WALL - 20)], "#70797b", 8)
    rect(c, 1488, 700, 88, 26, "#3e4648", 4, r=4)
    rect(c, 1488, 1180, 88, 26, "#3e4648", 4, r=4)
    rect(c, 560, 380, 18, 900, "#44484c", 3.5)
    rect(c, 520, 1060, 100, 130, "#4a4e52", 4.5, r=8)
    line(c, [(540, 1100), (600, 1100)], "#ffb020", 5)
    # pipe joint over the puddle (the drip)
    dxp = _TN_DRIP[0]
    rect(c, dxp - 22, 150 - 52, 44, 104, "#3e4648", 4, r=5)
    # side tunnel + junction sign
    _tn_mouth(c)
    sx, sy = TUNNEL_MARKS["junction_sign"]
    rect(c, sx - 160, sy - 60, 320, 120, "#2c3e4a", 4.5, r=10)
    core.text(c, "SHAFT A", sx - 6, sy - 12, 30, "#cfe9ee", "ui")
    polyf(c, [(sx - 140, sy - 22), (sx - 112, sy - 40), (sx - 112, sy - 4)], "#cfe9ee", 0)
    core.text(c, "CONTROL", sx - 10, sy + 40, 30, PAL["hush"], "ui")
    polyf(c, [(sx + 140, sy + 30), (sx + 112, sy + 12), (sx + 112, sy + 48)], PAL["hush"], 0)
    # CONTROL door frame + reader
    _tn_door_frame(c)
    # floor: concrete slabs, drain channel, puddle
    c.rectangle(x0, _TN_WALL, x1 - x0, y1 - _TN_WALL)
    core.fill(c, "#47474d")
    c.rectangle(x0, _TN_WALL, x1 - x0, 26)
    core.fill(c, core.alpha(INK, 0.4))
    rect(c, x0, _TN_WALL - 34, x1 - x0, 34, "#3f3f46", 4)
    for k in range(-10, 24):
        xx = k * 220
        line(c, [(xx, _TN_WALL), (1200 + (xx - 1200) * 2.5, y1)], "#3e3e44", 4)
    for yy in (1400, 1530, 1720, 2000):
        line(c, [(x0, yy), (x1, yy)], "#3e3e44", 4)
    rect(c, x0, 1395, x1 - x0, 20, "#36363c", 3)
    for k in range(int((x1 - x0) / 60)):
        line(c, [(x0 + k * 60, 1397), (x0 + k * 60 + 30, 1413)], "#2a2a30", 3)
    ell(c, _TN_DRIP[0], _TN_DRIP[1], 120, 18, "#3a3e48", 0)
    ell(c, _TN_DRIP[0] - 30, _TN_DRIP[1] - 4, 50, 5, (0.6, 0.65, 0.75, 0.35), 0)
    # the crate he sits on (+ a bigger one behind it)
    props.crate(c, _TN_SEAT[0] + 330, _TN_FEET - 40, 1.0, w=320, h=300, kind="wood", stencil="HC", seed=3)
    props.crate(c, _TN_SEAT[0], _TN_FEET, 1.0, w=360, h=_TN_SEAT[1], kind="wood", stencil=None, seed=4)
    # lamps (off; the lit bulbs + pools are in the light pass)
    for (lx, ly) in _TN_LAMPS:
        props.cage_lamp(c, lx, ly, 0.9, on=0.0, halo=False)
    # clear the door opening so the "back" layer shows through
    dx, dt, dw, dh = _TN_DOOR
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(dx, dt, dw, dh)
    c.fill()
    c.restore()


def _tn_light(c):
    """Warm emergency lamps (static pools) + the falloff into darkness."""
    x0, x1, y0, y1 = _TN_X0, _TN_X1, _TN_Y0, _TN_Y1
    # overall dim
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    core.fill(c, core.alpha("#0b0b12", 0.42))
    for (lx, ly) in _TN_LAMPS:
        props.cage_lamp(c, lx, ly, 0.9, on=1.0, color="#ffb35a", halo=False)
        by = ly + 92 * 0.9
        core.radial_glow(c, lx, by, 420, "#ffa64a", 0.42)
        core.radial_glow(c, lx, by, 140, "#ffd9a0", 0.55)
        ell(c, lx, _TN_FEET + 40, 420, 90, core.alpha("#ff9a40", 0.16), 0)
        ell(c, lx, _TN_FEET + 40, 250, 50, core.alpha("#ffb35a", 0.14), 0)
    # darkness toward the left end and the far right
    for (xa, xb, a) in ((x0, 640, 0.75), (x1, 2500, 0.55)):
        g = cairo.LinearGradient(xa, 0, xb, 0)
        g.add_color_stop_rgba(0, 0.02, 0.02, 0.04, a)
        g.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.0)
        c.rectangle(min(xa, xb), y0, abs(xb - xa), y1 - y0)
        c.set_source(g)
        c.fill()
    g = cairo.LinearGradient(0, y0, 0, _TN_CEIL + 60)
    g.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.7)
    g.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.0)
    c.rectangle(x0, y0, x1 - x0, _TN_CEIL + 60 - y0)
    c.set_source(g)
    c.fill()


def _tn_room(c):
    _tn_static(c)
    _tn_light(c)


def service_tunnel(ctx, t=0.0, layer="bg", door_open=0.0, reader="red", drip=True, parts=None):
    """Quiet concrete HushCorp service corridor, side-on (world 2400 x
    1920, people at s=0.75; drawable x -700..3100). See TUNNEL_MARKS.

    Left to right: a dark side tunnel receding into blackness (the "far
    end" a glowing creature walks off into: tunnel_depth(k) gives the
    path + scale) with a junction sign (SHAFT A / CONTROL), dim warm-orange
    emergency lamps in cages (static light pools), ceiling pipes, a drip
    into a puddle, the low crate he sits on (TUNNEL_MARKS["seat"]) and a
    bigger one behind it, and the heavy CONTROL keycard door (LVL 9) with
    its reader.

    door_open 0..1 slides the door panels apart (the dark control room with
    its monitor glow shows through: layer "back"); reader "red" | "green" |
    None lights the card reader. drip: one slow drip + ripple (s04).
    layer "bg" | "back" (only the room seen through the door) | "room" (bg
    without back: back -> person in the doorway -> room) | "fg" (parts:
    "crate" = the seat crate over someone behind it) | "shade" (warm lamp
    light + the dark ends for characters: sets.shaded()).
    """
    x0, y0, x1, y1 = _TN_X0, _TN_Y0, _TN_X1, _TN_Y1
    dx, dt, dw, dh = _TN_DOOR
    if layer in ("bg", "back"):
        sprite(ctx, "tunnel_back", dx - 6, dt - 6, dw + 12, dh + 12, _tn_back)
        if layer == "back":
            return
    if layer in ("bg", "room"):
        _overscan(ctx, x0, y0, x1, y1, "#141418", "#28282d", "#141418", "#202024")
        layer_blit(ctx, "tunnel_room", x0, y0, x1 - x0, y1 - y0, _tn_room)
        dim = 0.42
        dim_sprite(ctx, ("tunnel_door", round(clamp(door_open), 3)), (dx - 2, dt - 2, dw + 4, dh + 4), dim,
                   lambda c: _tn_door_panels(c, door_open))
        if door_open > 0.02:
            o = clamp(door_open)
            gw_ = dw * o
            core.poly(ctx, [(dx + dw / 2 - gw_ / 2, _TN_WALL), (dx + dw / 2 + gw_ / 2, _TN_WALL),
                            (dx + dw / 2 + gw_ * 0.9, _TN_FEET + 160), (dx + dw / 2 - gw_ * 0.9, _TN_FEET + 160)])
            core.fill(ctx, core.alpha("#7fe8ff", 0.16 * o))
        _tn_reader_light(ctx, reader)
        if drip:
            px_, py_ = _TN_DRIP
            ph = (t % 2.6) / 2.6
            if ph < 0.7:
                yy = 196 + (py_ - 196) * (ph / 0.7) ** 2
                ell(ctx, px_, yy, 5, 8, "#c9d3e0", 2)
            else:
                k = (ph - 0.7) / 0.3
                ell(ctx, px_, py_, 18 + 60 * k, 4 + 8 * k, None, 3, sc=core.alpha("#c9d3e0", 1 - k))
        return
    if layer == "fg":
        parts = parts or ()
        if "crate" in parts:
            sprite(ctx, "tunnel_seat_crate", _TN_SEAT[0] - 200, _TN_FEET - _TN_SEAT[1] - 50, 430, _TN_SEAT[1] + 60,
                   lambda c: _dim_into(c, (_TN_SEAT[0] - 200, _TN_FEET - _TN_SEAT[1] - 50, 430, _TN_SEAT[1] + 60), 0.42,
                                       lambda cc: props.crate(cc, _TN_SEAT[0], _TN_FEET, 1.0, w=360, h=_TN_SEAT[1],
                                                              kind="wood", stencil=None, seed=4)))
    elif layer == "shade":
        sprite(ctx, "tunnel_shade", x0, y0 + 600, x1 - x0, 2000, _tn_shade, max_mp=12.0)


def _tn_shade(c):
    x0, x1 = _TN_X0, _TN_X1
    c.rectangle(x0, _TN_Y0 + 600, x1 - x0, 2000)
    core.fill(c, core.alpha("#0b0b12", 0.30))
    for (lx, ly) in _TN_LAMPS:
        core.radial_glow(c, lx, ly + 300, 520, "#ff9a40", 0.22)
    for (xa, xb, a) in ((x0, 640, 0.75), (x1, 2500, 0.5)):
        g = cairo.LinearGradient(xa, 0, xb, 0)
        g.add_color_stop_rgba(0, 0.02, 0.02, 0.04, a)
        g.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.0)
        c.rectangle(min(xa, xb), _TN_Y0 + 600, abs(xb - xa), 2000)
        c.set_source(g)
        c.fill()
