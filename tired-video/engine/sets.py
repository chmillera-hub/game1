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


MAX_LAYER_MP = 16.0  # above this many megapixels a static layer is tiled


def static_layer(ctx, key, x0, y0, w, h, draw_fn):
    """core.cached() wrapper: one bitmap when small, visible tiles when big.

    Tiles are ~2048 px bitmaps; they overlap by core's pad, so use this
    for OPAQUE layers (small translucent layers go straight to core.cached).
    """
    if not _visible(ctx, x0, y0, w, h):
        return
    q = _qscale(ctx)
    if q <= 0:
        return
    if w * h * q * q <= MAX_LAYER_MP * 1e6:
        core.cached(ctx, key, x0, y0, w, h, draw_fn)
        return
    T = max(160, int(2040 / q) // 32 * 32)
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


def _bd_static(c):
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
    blob(c, [(1240, 2150), (1300, 2110), (1380, 2120), (1400, 2170), (1330, 2200), (1260, 2190)],
         "#2f2b3d", 5)                                       # game controller
    core.circle(c, 1290, 2155, 10); core.circle(c, 1360, 2150, 10)
    core.fill(c, "#ff6f61")

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

    # clear the doorway so the hallway (layer 'back') shows through
    c.save()
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.rectangle(dx, dt, dw, dh)
    c.fill()
    c.restore()


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


_BD_POSTERS = [  # (kind, pin x, pin y)
    (1, 795, 330),
    (0, 1595, 360) if False else (0, 2195, 380),
    (2, 1650, 330) if False else (2, 1750, 860 - 520),
]


def _bd_posters(ctx, t, shake):
    for i, (kind, px, py) in enumerate(((1, 795, 334), (0, 2205, 360), (2, 1760, 360))):
        rot = 0.0
        if shake > 0:
            rot = shake * (0.10 * math.sin(t * 21 + i * 2.1) + 0.05 * math.sin(t * 34 + i))
        rot += (-0.02, 0.025, -0.015)[i]
        with core.saved(ctx, px, py, 0.92 if kind == 2 else 1.0, rot):
            if kind == 2:
                pass
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
        if on:
            core.radial_glow(ctx, 0, 300, 230, "#ffe7a0", 0.30)
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
            shake=0.0, frame_fallen=False, screen_fn=None, screen_on=True, game_speed=1.0,
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
        core.cached(ctx, "bedroom_hall", dx - 12, dt - 12, dw + 24, dh + 24, _bd_hall)
        if layer == "back":
            return
    if layer in ("bg", "room"):
        e = _BD_EXT
        _overscan(ctx, -e[0], -e[1], W + e[2], H + e[3], C["bd_ceil"], C["wood"], C["bd_wall_sh"],
                  C["bd_wall_sh"])
        static_layer(ctx, "bedroom_room", -e[0], -e[1], W + e[0] + e[2], H + e[1] + e[3], _bd_static)
        _bd_door_casing(ctx)
        _bd_door_panel(ctx, door_open)
        _bd_closet_panel(ctx, closet_open)
        # sun patch from the (off-screen) side window, over closet + wall
        _sun_patch(ctx, [(1560, 520), (1810, 492), (1850, 1060), (1590, 1100)], 0.5)
        _sun_patch(ctx, [(1580, 560), (1676, 549), (1692, 770), (1596, 784)], 0.22, "#ffffff")
        _sun_patch(ctx, [(600, 640), (860, 610), (930, 1060), (660, 1110)], 0.22)
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
    "lean_face": (540, 760),     # face position of someone leaning to the glass
    "lean_hips": (540, 1500),    # hips (below the sill, hidden) for s~1.45
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
        core.cached(ctx, "window_ext_in", gx - 4, gy - 4, gw + 8, gh + 8, _wext_interior)
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
        core.cached(ctx, "house_back", dx - 12, dt - 12, dw + 24, dh + 24, _h_back)
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
            core.cached(ctx, "house_hedges", 660, 1360, 1580, 150,
                        lambda c: [_h_bush(c, x - 50, _HG + 4, w + 100, 120, seed=int(x)) for (x, y, w, h) in _H_WIN])
        if "fence" in parts:
            core.cached(ctx, "house_fence_fg", -560, 1580, 2800, 240, _h_fence)


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
        core.cached(ctx, "living_table", 1900, 1050, 520, 560, lambda c: _lv_table(c, "all"))
        core.cached(ctx, "living_rail", 2180, _LV_LANDING_Y - 340, 1300, 1340 - _LV_LANDING_Y + 340,
                    _lv_railing)
        # dim afternoon: soft darkening toward the far right/left ends (static)
        return
    if layer == "fg":
        parts = parts or ("table", "stairs")
        if "table" in parts:
            core.cached(ctx, "living_table_fg", 1900, 1050, 520, 560, lambda c: _lv_table(c, "fg"))
        if "stairs" in parts:
            core.cached(ctx, "living_rail", 2180, _LV_LANDING_Y - 340, 1300, 1340 - _LV_LANDING_Y + 340,
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
    # steps descending to the left
    for k in range(1, _HL_N + 2):
        x1 = tx - (k - 1) * _HL_RUN
        x0 = x1 - _HL_RUN
        y = FLOOR + k * _HL_RISE - _HL_RISE
        # riser (front face, toward us below the tread), tread
        rect(c, x0, y + 16, _HL_RUN + 6, _HL_RISE - 16, C["wood"], 3.5)
        rect(c, x0 - 6, y, _HL_RUN + 12, 18, C["wood_hi"], 4, r=4)
        rect(c, x0 + 14, y + 2, _HL_RUN - 22, 12, "#8a4a63", 0, r=3)
    # landing floor edge + nosing
    rect(c, tx - 8, FLOOR - 4, 40, 22, C["wood_hi"], 4, r=4)
    # stair stringer (solid side of the staircase under the treads)
    pts = [(tx + 30, FLOOR + 18)]
    for k in range(1, _HL_N + 2):
        x1 = tx - (k - 1) * _HL_RUN
        y = FLOOR + k * _HL_RISE - _HL_RISE
        pts += [(x1, y + 18), (x1 - _HL_RUN, y + 18)]
    pts += [(-e[0], H + e[3]), (tx + 30, H + e[3])]
    polyf(c, pts, "#efe2c8", 5)
    for k in range(1, 5):
        line(c, [(tx + 30 - k * 260, FLOOR + 140 + k * 160), (tx + 30 - k * 260 + 160, FLOOR + 140 + k * 160 - 100)],
             C["lv_wain_sh"], 4)
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
    core.fill(c, (0.12, 0.08, 0.20, 0.30))
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
    polyf(ctx, q, "#efe6d6", 6)
    if op < 0.97:
        def P(u, v):
            top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
            bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
            return (lerp(top[0], bot[0], v), lerp(top[1], bot[1], v))
        for (u0, v0, u1, v1) in ((0.16, 0.07, 0.84, 0.44), (0.16, 0.53, 0.84, 0.92)):
            polyf(ctx, [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)], None, 4, sc=C["trim_sh"])
        kx, ky = P(0.89, 0.55)
        core.circle(ctx, kx, ky, 15 * (1 - 0.6 * op))
        fs(ctx, "#f2c14e", 4)
        # hanging sign on the knob
        if op < 0.3:
            sx, sy = P(0.89, 0.62)
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
                (dx + dw, dt + dh), (dx + dw, dt), (dx, dt), (dx, dt + dh), (dx - trim, dt + dh)], C["trim"], 5)


def _hl_railing(c):
    tx = _HL_TOP_X
    hr = 300
    a = (tx + 30, _HL_FLOOR - hr)
    b = (tx - (_HL_N + 1) * _HL_RUN, _HL_FLOOR + _HL_N * _HL_RISE - hr)
    for k in range(1, _HL_N + 2):
        bx = tx - (k - 0.5) * _HL_RUN
        by = _HL_FLOOR + (k - 1) * _HL_RISE
        yr = lerp(a[1], b[1], (bx - a[0]) / (b[0] - a[0]))
        rect(c, bx - 7, yr, 14, by - yr, C["trim"], 3)
    line(c, [a, b], INK, 24)
    line(c, [a, b], C["wood_dk"], 15)
    rect(c, tx + 8, _HL_FLOOR - hr - 30, 46, hr + 40, C["wood_dk"], 5, r=6)   # newel
    core.circle(c, tx + 31, _HL_FLOOR - hr - 42, 26); fs(c, C["wood_dk"], 5)


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
        core.cached(ctx, "hall_back", dx - 12, dt - 12, dw + 24, dh + 24, _hl_back)
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
            core.cached(ctx, "hall_rail", -560, 600, 1400, 1330, _hl_railing)
        return
    if layer == "fg":
        parts = parts or ("railing",)
        if "door" in parts:
            _hl_casing(ctx)
            if door_open > 0.02:
                _hl_door_panel(ctx, door_open, burst, t)
        if "railing" in parts:
            core.cached(ctx, "hall_rail", -560, 600, 1400, 1330, _hl_railing)
