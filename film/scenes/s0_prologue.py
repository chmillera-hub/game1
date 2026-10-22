"""s0_prologue.py -- SCENE 0, THE PROLOGUE: "A Kingdom of Stone" (the bard's song).  (shot plan: see PLAN)"""

import math
import random

import cairocffi as cairo

from film.lib import core, fx
from film.lib import storybook as sb
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.core import clamp, lerp, smooth
from film.scenes import _s0_pages as PG

SCENE = 0
W, H = core.W, core.H
TAU = math.tau
L_CANDLE = sb.STORY_LIGHT

# ----------------------------------------------------------------------------------------
# timing: everything derives from timeline.json beats/lines and the song's own word times
# ----------------------------------------------------------------------------------------
DUR = tl.scene(SCENE).duration
SONG = PG.SONG
T_FLOURISH = tl.beat("s0_flourish").t
T_OPEN = tl.beat("s0_bookopen").t
T_VAMP = tl.beat("s0_vamp").t
T_TURN1 = tl.beat("s0_page_turn_v2").t
T_LOOKUP = tl.beat("s0_coda_look_up").t
T_BREAK = tl.beat("s0_break").t
T_FINAL = tl.beat("s0_final_chord").t
_OUT = tl.beat("s0_out")
T_OUT0, T_OUT1 = _OUT.t, (_OUT.end if _OUT.end is not None else DUR)
_OPEN_B = tl.beat("s0_open")
T_FADEIN = _OPEN_B.end if _OPEN_B.end is not None else 2.0
LN = {k: tl.line(f"s0_l{k}") for k in range(1, 11)}


def wt(k, word, nth=0):
    """Sung start time of `word` in lyric line k (song_timing.json), falling back to the line start."""
    return SONG.at(f"s0_l{k}", word, nth, LN[k].start)


OPEN_DUR = 1.3                                   # open 0 -> 1 (the cover lands at 0.45 of it)
T_COVER_LAND = T_OPEN + 0.45 * OPEN_DUR
TURN_DUR = 0.85
T_TURN2 = T_BREAK                                # verse 2 -> the coda spread, on the lute's roll as we pull out
T_TURN3 = wt(10, "bread")                         # "...back to BREAD": the page turns to the wash-house
TURN3_DUR = max(0.6, T_FINAL - T_TURN3)          # ...and lands with the final chord
T_CUT_B = wt(4, "pane")                           # cut to the bard on his long note
T_CUT_C = LN[5].start                             # cut back into the book: "Now a dragon..."
T_WINK = wt(9, "how")                             # "...and hear HOW it's said"
T_STOOL = wt(9, "stool")
T_FRIEND = wt(9, "friend")

EV = dict(castle_lights=wt(1, "kingdom"), folk_walk=wt(2, "Lived"), cross=wt(2, "alone"), alone=wt(2, "who"),
          potions=wt(3, "potions"), sleeping=wt(3, "sleeping"), charms=wt(3, "charms"), rain=wt(3, "the") - 0.1,
          lock=wt(4, "lock"), heart=wt(4, "heart"), latch=wt(4, "latch"), pane=wt(4, "pane"),
          sigh=wt(5, "sigh"), wave=wt(6, "waved"), neighbours=wt(6, "neighbours"), hurried=wt(6, "hurried"),
          by=wt(6, "by"), stone=wt(7, "stone"), sell=wt(7, "sell"), but=wt(8, "But"), missing=wt(8, "missing"),
          wasnt=wt(8, "wasn't"), spell=wt(8, "spell"), wash_walk=T_TURN3 - 2.5)

# ----------------------------------------------------------------------------------------
# the set (world px at zoom 1; y down). The nook: stone wall, hearth (left, off the frame's
# edge in most shots), the bard on his stool, the lectern + great book, an empty stool "for you".
# ----------------------------------------------------------------------------------------
WALL_Y = 800.0
BARD_X, BARD_Y, BARD_SC = 800.0, 985.0, 3.0
LECT_X, LECT_Y, LECT_SC, LECT_HT = 1330.0, 930.0, 1.55, 230.0
DESK = (LECT_X, LECT_Y - LECT_HT * LECT_SC)
HEARTH_X, HEARTH_SC = 205.0, 1.45
WIN_X, WIN_Y, WIN_W, WIN_H = 1700.0, 150.0, 150.0, 250.0
STOOL_X, STOOL_Y = 1068.0, 968.0                  # the empty stool (pull up a stool, friend)
STACK_X, STACK_Y = 1740.0, 1004.0                 # old books + a candle stub (right)
FG_CANDLE = (1585.0, 610.0)                       # the near candle we push past (parallax FG_P)
FG_P = 1.32
WALL_P = 0.95
WALL = {"stone_a": "#5a443a", "stone_b": "#46352f", "mortar": "#1f1617", "beam": "#33231a",
        "floor_hi": "#5b3f2c", "floor_lo": "#24170f"}
M = dict(w=2400, h=1500, x=-240, y=-200)          # cached-layer margin (camera moves never show an edge)

VIEW_WIDE, VIEW_BOOK = 0.55, 0.24                 # the desk angle: wide shots / pushed into the page
GILT = {}                                         # id(page) -> gilt polylines (page units)


# ----------------------------------------------------------------------------------------
# the nook's static art (cached once in setup)
# ----------------------------------------------------------------------------------------

def _stone_wall(cr, x0, y0, x1, y1, seed, rows=(54, 70)):
    rng = random.Random(seed)
    core.src(cr, WALL["mortar"])
    cr.rectangle(x0, y0, x1 - x0, y1 - y0)
    cr.fill()
    y, row = y0, 0
    while y < y1:
        hgt = rng.uniform(*rows)
        x = x0 - rng.random() * 80 - (row % 2) * 45
        while x < x1:
            w = rng.uniform(90, 170)
            tone = core.mix(WALL["stone_a"], WALL["stone_b"], rng.random())
            tone = core.mix(tone, "#6a5244", 0.25 * rng.random())
            pts = [(x + 5 + rng.uniform(-2, 2), y + 5 + rng.uniform(-2, 2)), (x + w - 5 + rng.uniform(-2, 2), y + 4 + rng.uniform(-2, 2)),
                   (x + w - 4 + rng.uniform(-2, 2), y + hgt - 5 + rng.uniform(-2, 2)), (x + 4 + rng.uniform(-2, 2), y + hgt - 4 + rng.uniform(-2, 2))]
            cr.new_path()
            core.smooth_closed(cr, pts, 0.35)
            sp = B.Path(cr)
            sp.add(cr)
            core.src(cr, tone)
            cr.fill()
            cr.save()
            sp.add(cr)
            cr.clip()
            cr.set_source(core.linear(0, y, 0, y + hgt, [(0.0, (1.0, 0.86, 0.66, 0.10)), (0.25, (1, 1, 1, 0.0)),
                                                         (0.8, (0, 0, 0, 0.0)), (1.0, (0, 0, 0, 0.28))]))
            cr.paint()
            for _ in range(2):
                sb._bloom(cr, rng.uniform(x, x + w), rng.uniform(y, y + hgt), rng.uniform(10, 26), "#000000", 0.08)
            cr.restore()
            x += w
        y += hgt
        row += 1


def _wall_music(cr, x, y):
    """The bard's frame drum and recorder hung on two wall pegs (the song's other instruments)."""
    for px, py in ((x, y), (x + 120, y + 14)):
        core.src(cr, "#140d0a", 0.5)
        core.circle(cr, px + 3, py + 4, 7.5)
        cr.fill()
        core.src(cr, "#3a2618")
        core.circle(cr, px, py, 6.5)
        cr.fill()
    dx, dy, r = x, y + 76, 50.0
    core.src(cr, "#5e3c26", 0.95)
    cr.set_line_width(2.2)
    cr.move_to(x - 2, y + 4)
    cr.line_to(dx - 16, dy - r + 3)
    cr.move_to(x + 2, y + 4)
    cr.line_to(dx + 16, dy - r + 3)
    cr.stroke()
    core.src(cr, "#140d0a", 0.45)
    core.circle(cr, dx + 7, dy + 9, r + 2)
    cr.fill()
    core.src(cr, "#7a4c2a")
    core.circle(cr, dx, dy, r)
    cr.fill()
    cr.set_source(core.radial(dx - 12, dy - 14, r * 0.95, ["#eedcae", "#d9bf86", "#b8975e"]))
    core.circle(cr, dx, dy, r - 7.0)
    cr.fill()
    for k in range(4):
        a = 0.4 + k * TAU / 4
        jx, jy = dx + math.cos(a) * (r - 3.5), dy + math.sin(a) * (r - 3.5)
        core.src(cr, "#3a2416")
        cr.rectangle(jx - 6, jy - 3, 12, 6)
        cr.fill()
        core.src(cr, "#d9b45a")
        core.circle(cr, jx, jy, 3.4)
        cr.fill()
    rx_, ry_ = x + 120, y + 14
    core.src(cr, "#5e3c26", 0.95)
    cr.set_line_width(2.0)
    cr.move_to(rx_, ry_ + 3)
    cr.line_to(rx_ + 4, ry_ + 22)
    cr.stroke()
    cr.save()
    cr.translate(rx_ + 4, ry_ + 22)
    cr.rotate(-0.12)
    core.src(cr, "#140d0a", 0.45)
    core.rounded_rect(cr, 1.0, 6.0, 14.0, 172.0, 7.0)
    cr.fill()
    cr.set_source(core.linear(-7.0, 0, 7.0, 0, ["#7d4e28", "#c8945a", "#8a5a30"]))
    cr.new_path()
    core.tapered(cr, [(0.0, 0.0), (0.0, 168.0)], 13.0, 10.0)
    cr.fill()
    cr.set_source(core.linear(-7.0, 0, 7.0, 0, ["#5e3a20", "#8a5a30", "#5e3a20"]))
    core.rounded_rect(cr, -7.5, -2.0, 15.0, 16.0, 4.0)
    cr.fill()
    core.rounded_rect(cr, -7.0, 150.0, 14.0, 20.0, 4.0)
    cr.fill()
    core.src(cr, "#2a160c")
    cr.rectangle(-4.0, 16.0, 8.0, 3.0)
    cr.fill()
    for k in range(7):
        core.circle(cr, 0.0, 52.0 + k * 13.0, 2.3)
        cr.fill()
    cr.restore()


def _window(cr):
    wx, wy, ww, wh = WIN_X, WIN_Y, WIN_W, WIN_H
    cr.new_path()
    cr.move_to(wx, wy + wh)
    cr.line_to(wx, wy + ww / 2)
    cr.arc(wx + ww / 2, wy + ww / 2, ww / 2, math.pi, 2 * math.pi)
    cr.line_to(wx + ww, wy + wh)
    cr.close_path()
    win = B.Path(cr)
    core.src(cr, "#1a1414")
    cr.set_line_width(26)
    win.add(cr)
    cr.stroke()
    win.add(cr)
    cr.set_source(core.linear(0, wy, 0, wy + wh, ["#26386a", "#132040"]))
    cr.fill()
    cr.save()
    win.add(cr)
    cr.clip()
    fx.glow(cr, wx + 96, wy + 84, 150, "#9db8f0", 0.45)
    core.src(cr, "#e6eeff", 0.9)
    core.circle(cr, wx + 96, wy + 84, 20)
    cr.fill()
    core.src(cr, "#140e10", 0.95)
    cr.rectangle(wx + ww / 2 - 4, wy, 8, wh)
    for k in range(1, 4):
        cr.rectangle(wx, wy + ww / 2 + k * (wh - ww / 2) / 4 - 3, ww, 6)
    cr.fill()
    cr.restore()
    core.src(cr, "#3b2c26")
    cr.rectangle(wx - 30, wy + wh, ww + 60, 22)
    cr.fill()


def _rug(cr, cx, cy, rx, ry):
    cr.save()
    cr.translate(cx, cy)
    cr.scale(1.0, ry / rx)
    core.src(cr, "#d8c08a", 0.55)
    for k in range(90):
        a = TAU * k / 90
        cr.move_to(math.cos(a) * rx * 0.99, math.sin(a) * rx * 0.99)
        cr.line_to(math.cos(a) * rx * 1.05, math.sin(a) * rx * 1.05)
    cr.set_line_width(3.0)
    cr.stroke()
    for r, c in ((rx, "#4a1a1f"), (rx * 0.95, "#8e2a2a"), (rx * 0.83, "#c09040"), (rx * 0.80, "#25304e")):
        cr.new_path()
        cr.arc(0, 0, r, 0, TAU)
        core.src(cr, c)
        cr.fill()
    core.src(cr, "#d8b060")
    for k in range(30):
        a = TAU * (k + 0.5) / 30
        mx, my = math.cos(a) * rx * 0.89, math.sin(a) * rx * 0.89
        tx, ty = -math.sin(a), math.cos(a)
        cr.move_to(mx + tx * 14, my + ty * 14)
        cr.line_to(mx + math.cos(a) * 9, my + math.sin(a) * 9)
        cr.line_to(mx - tx * 14, my - ty * 14)
        cr.line_to(mx - math.cos(a) * 9, my - math.sin(a) * 9)
        cr.close_path()
    cr.fill()
    for (sx, c) in ((rx * 0.42, "#c09040"), (rx * 0.37, "#8e2a2a"), (rx * 0.2, "#25304e")):
        cr.move_to(-sx * 1.5, 0)
        cr.line_to(0, -sx)
        cr.line_to(sx * 1.5, 0)
        cr.line_to(0, sx)
        cr.close_path()
        core.src(cr, c)
        cr.fill()
    cr.restore()


def _book_stack(cr, x, y):
    rng = random.Random(8)
    core.src(cr, "#000000", 0.35)
    core.ellipse(cr, x + 8, y + 4, 128, 16)
    cr.fill()
    yy = y
    for k, (w, h, c) in enumerate(((214, 38, "#5a2a20"), (190, 32, "#2e4038"), (200, 36, "#6a4224"))):
        dx = rng.uniform(-14, 14)
        x0 = x - w / 2 + dx
        cr.save()
        cr.translate(x0 + w / 2, yy - h / 2)
        cr.rotate(rng.uniform(-0.025, 0.025))
        core.src(cr, core.mix(c, "#000000", 0.25))
        core.rounded_rect(cr, -w / 2, -h / 2, w, h, 6)
        cr.fill()
        core.src(cr, c)
        core.rounded_rect(cr, -w / 2, -h / 2, w, h * 0.28, 4)
        core.rounded_rect(cr, -w / 2, h / 2 - h * 0.26, w, h * 0.26, 4)
        cr.fill()
        core.src(cr, "#cdb98c")
        cr.rectangle(-w / 2 + 10, -h / 2 + h * 0.3, w - 34, h * 0.42)
        cr.fill()
        core.src(cr, "#9a8460", 0.5)
        for j in range(3):
            cr.rectangle(-w / 2 + 10, -h / 2 + h * (0.36 + j * 0.11), w - 34, 1.0)
        cr.fill()
        core.src(cr, core.mix(c, "#000000", 0.1))
        core.rounded_rect(cr, w / 2 - 26, -h / 2, 26, h, 9)
        cr.fill()
        core.src(cr, "#c8a050", 0.85)
        for bx in (w / 2 - 19, w / 2 - 9):
            cr.rectangle(bx, -h / 2 + 3, 2.5, h - 6)
        cr.fill()
        cr.restore()
        yy -= h
    return (x, yy)


def _radial(cx, cy, r, stops):
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    for off, c in stops:
        g.add_color_stop_rgba(off, *c)
    return g


def draw_wall(cr, store):
    """The back wall plane (parallax WALL_P): stone, ceiling beam, hearth, mantel, the drum and
    recorder on their pegs, the night window; the painted light falloff."""
    _stone_wall(cr, -260, -220, W + 260, WALL_Y + 8, 4)
    core.src(cr, WALL["beam"])
    cr.rectangle(-260, -220, W + 520, 260)
    cr.fill()
    cr.set_source_rgba(1, 0.8, 0.6, 0.07)
    cr.rectangle(-260, 36, W + 520, 4)
    cr.fill()
    hr = sb.draw_hearth(cr, HEARTH_X, WALL_Y + 22, HEARTH_SC, L_CANDLE, seed=1)
    store["hearth"] = hr
    mx, my = hr.mantel
    core.src(cr, "#7a4a30")
    cr.new_path()
    core.smooth_closed(cr, [(mx - 120, my), (mx - 128, my - 30), (mx - 118, my - 52), (mx - 106, my - 54), (mx - 96, my - 32),
                            (mx - 102, my)], 0.8)
    cr.fill()
    for (bx, bw, bh, c) in ((mx + 70, 22, 64, "#3c4a3a"), (mx + 94, 18, 56, "#6a2a22")):
        core.src(cr, c)
        cr.rectangle(bx, my - bh, bw, bh)
        cr.fill()
        core.src(cr, "#c8a050", 0.6)
        cr.rectangle(bx + 2, my - bh + 10, bw - 4, 3)
        cr.rectangle(bx + 2, my - 14, bw - 4, 3)
        cr.fill()
    _wall_music(cr, 950, 250)
    _window(cr)
    # light falloff: dark ceiling, a warm pocket round the book and the bard, the hearth's orange
    cr.set_source(core.linear(0, -220, 0, 520, [(0.0, (0.03, 0.01, 0.02, 0.85)), (1.0, (0.03, 0.01, 0.02, 0.0))]))
    cr.rectangle(-260, -220, W + 520, 740)
    cr.fill()
    cr.set_source(_radial(1150, 620, 1250, [(0.0, (0.0, 0.0, 0.0, 0.0)), (0.42, (0.02, 0.0, 0.02, 0.22)),
                                            (1.0, (0.02, 0.0, 0.03, 0.78))]))
    cr.rectangle(-260, -220, W + 520, H + 440)
    cr.fill()
    hx, hy = hr.fire
    cr.set_source(_radial(hx, hy - 120, 760, [(0.0, (1.0, 0.45, 0.15, 0.30)), (0.5, (0.9, 0.35, 0.1, 0.10)),
                                              (1.0, (0.9, 0.3, 0.1, 0.0))]))
    cr.rectangle(-260, -220, W + 520, H + 440)
    cr.fill()


def draw_floor(cr, store):
    """The floor plane (parallax 1, the actors' plane): planks running toward us, the rug, the
    book stack."""
    core.vgrad(cr, -260, WALL_Y, W + 520, H - WALL_Y + 300, [WALL["floor_hi"], WALL["floor_lo"]])
    cr.set_source_rgba(0, 0, 0, 0.32)
    for k in range(-22, 24):
        cr.move_to(960 + k * 44, WALL_Y)
        cr.line_to(960 + k * 150, H + 260)
    cr.set_line_width(2.0)
    cr.stroke()
    cr.set_source(core.linear(0, WALL_Y - 6, 0, WALL_Y + 34, [(0, (0, 0, 0, 0.6)), (1, (0, 0, 0, 0))]))
    cr.rectangle(-260, WALL_Y - 6, W + 520, 40)
    cr.fill()
    _rug(cr, BARD_X + 120, BARD_Y + 10, 360, 74)
    store["stack_top"] = _book_stack(cr, STACK_X, STACK_Y)
    # the floor falls into darkness away from the candles
    cr.set_source(_radial(1150, 900, 1150, [(0.0, (0.0, 0.0, 0.0, 0.0)), (0.5, (0.02, 0.0, 0.02, 0.18)),
                                            (1.0, (0.02, 0.0, 0.03, 0.7))]))
    cr.rectangle(-260, WALL_Y - 10, W + 520, H)
    cr.fill()


def draw_fg_candle(cr):
    """The near candle (parallax FG_P, out of focus): a tall beeswax candle in an iron pricket.
    Drawn once into a blurred layer; its flame + halo are drawn per frame."""
    x, y = FG_CANDLE
    iron = "#1c1412"
    core.src(cr, iron)
    core.rounded_rect(cr, x - 70, y + 330, 140, 30, 10)
    cr.fill()
    core.rounded_rect(cr, x - 13, y + 160, 26, 190, 10)
    cr.fill()
    core.rounded_rect(cr, x - 46, y + 150, 92, 16, 7)
    cr.fill()
    cr.set_source(core.linear(x - 22, 0, x + 22, 0, ["#6e5a40", "#b49a6c", "#5e4a34"]))
    core.rounded_rect(cr, x - 22, y + 10, 44, 146, 9)
    cr.fill()
    cr.set_source(core.linear(0, y + 8, 0, y + 70, [(0.0, (1.0, 0.85, 0.55, 0.85)), (1.0, (1.0, 0.85, 0.55, 0.0))]))
    core.rounded_rect(cr, x - 22, y + 8, 44, 64, 9)
    cr.fill()
    core.src(cr, "#ffe2a8", 0.55)
    for dx_, dl in ((-12, 36), (6, 58), (15, 24)):
        core.rounded_rect(cr, x + dx_ - 3, y + 8, 6, dl, 3)
        cr.fill()
    core.src(cr, "#ffe7b0")
    core.ellipse(cr, x, y + 10, 21, 5)
    cr.fill()


# ----------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------

def view_for_zoom(z):
    """The desk angle follows the camera: the further we push in, the more face-on the page
    (the camera rises over the book as it dives into it)."""
    return lerp(VIEW_WIDE, VIEW_BOOK, smooth((z - 1.95) / (3.9 - 1.95)))


def page_world(side, u, v, view):
    """World point of page fraction (u, v) on the open book's left/right page at `view` (the same
    affine map storybook.draw_book uses for an open page lying on its block)."""
    book_w, book_h, T = 150.0, 200.0, 12.0
    cv, sv = math.cos(view), math.sin(view)
    x0 = 0.8 if side == "right" else -0.8 - book_w
    px = x0 + u * book_w
    py = v * book_h * cv - book_h / 2.0 * cv - T * sv
    return DESK[0] + LECT_SC * px, DESK[1] + LECT_SC * py


def Wk(x, y, z):
    return ("w", x, y, z)


def Pk(side, u, v, dev):
    return ("p", side, u, v, dev)


def _resolve(spec):
    if spec[0] == "w":
        return core.Camera(spec[1], spec[2], spec[3])
    _, side, u, v, dev = spec
    z = dev / LECT_SC
    x, y = page_world(side, u, v, view_for_zoom(z))
    return core.Camera(x, y, z)


def _cam_lerp(a, b, u):
    """Interpolate two cameras as a dolly about the one world point both frames agree on (so a
    push-in radiates from its target and never swings); near-equal zooms move linearly."""
    z0, z1 = a.zoom, b.zoom
    if abs(math.log(z1 / z0)) < 0.04:
        return core.Camera(lerp(a.x, b.x, u), lerp(a.y, b.y, u), lerp(z0, z1, u))
    z = z0 * (z1 / z0) ** u
    px = (b.x * z1 - a.x * z0) / (z1 - z0)
    py = (b.y * z1 - a.y * z0) / (z1 - z0)
    return core.Camera(px - (px - a.x) * z0 / z, py - (py - a.y) * z0 / z, z)


# (time, spec, easing into this key). Three shots: A (0 -> T_CUT_B), B (-> T_CUT_C), C (-> end).
SHOT_A = [
    (0.0, Wk(1088, 668, 1.24)),
    (T_OPEN - 0.1, Wk(1132, 640, 1.60), "inout_sine"),          # slow push past the candle: the closed book
    (T_COVER_LAND - 0.12, Wk(1148, 628, 1.71), "linear"),        # ...creeping on while the cover swings
    (LN[1].start + 0.72, Pk("right", -0.02, 0.36, 5.9), "inout_sine"),  # dive in: the whole spread fills the frame
    (wt(1, "in") - 0.05, Pk("left", 0.9, 0.33, 6.2), "inout_sine"),     # "Once upon a time," -- the quill writes
    (wt(1, "stone") + 0.1, Pk("right", 0.5, 0.245, 10.4), "inout_sine"),  # into the castle on "stone"
    (LN[2].start + 0.35, Pk("right", 0.5, 0.25, 10.5), "linear"),
    (wt(2, "alone"), Pk("right", 0.5, 0.74, 10.8), "inout_sine"),      # tilt down the hill to the town
    (wt(4, "And"), Pk("right", 0.5, 0.775, 11.0), "inout_sine"),        # settle in the street
    (T_CUT_B, Pk("right", 0.53, 0.79, 11.25), "inout_sine"),            # lean in on lock / latch
]
SHOT_B = [
    (T_CUT_B, Wk(1095, 655, 1.66)),
    (T_CUT_C, Wk(1105, 650, 1.74), "linear"),
]
SHOT_C = [
    (T_CUT_C, Pk("left", 0.8, 0.56, 6.2)),                                # the dragon's page; its verse writes below
    (wt(5, "a", 1) - 0.1, Pk("left", 0.64, 0.42, 9.0), "inout_sine"),     # push in on him for "...and a SIGH"
    (wt(6, "by") - 0.1, Pk("left", 0.66, 0.43, 9.2), "inout_sine"),       # the wave, the neighbours hurrying by
    (wt(7, "in"), Pk("right", 0.42, 0.55, 6.6), "inout_sine"),            # glide to the market: "Every merchant..."
    (wt(7, "stone") - 0.1, Pk("right", 0.3, 0.42, 8.6), "inout_sine"),    # in on the stone-seller for "STONE"
    (wt(7, "sell"), Pk("right", 0.42, 0.46, 7.6), "inout_sine"),          # ...all three hold up their wares
    (wt(8, "wasn't"), Pk("right", -0.02, 0.55, 4.6), "inout_sine"),       # pull back: the dragon AND the stalls
    (LN[9].start + 0.15, Wk(1062, 742, 1.45), "inout_sine"),              # out of the book, back to the bard
    (T_WINK - 0.15, Wk(872, 772, 2.15), "inout_sine"),                    # push in on him: the stool, the wink
    (LN[9].end + 0.1, Wk(874, 770, 2.2), "linear"),
    (T_TURN3 - 0.4, Wk(1095, 690, 1.62), "inout_sine"),                   # ease back: him and the book
    (T_FINAL + 0.1, Wk(1108, 682, 1.67), "inout_sine"),                   # the page turns, the final chord
    (T_OUT0 - 0.25, Pk("right", 0.47, 0.55, 7.8), "inout_cubic"),         # push into the wash-house page...
    (DUR, Pk("right", 0.5, 0.64, 12.5), "inout_sine"),                    # ...and on into it as it goes black
]


def camera_at(t):
    keys = SHOT_A if t < T_CUT_B else SHOT_B if t < T_CUT_C else SHOT_C
    if t <= keys[0][0]:
        cam = _resolve(keys[0][1])
    else:
        cam = _resolve(keys[-1][1])
        for i in range(1, len(keys)):
            if t < keys[i][0]:
                k0, k1 = keys[i - 1], keys[i]
                u = core.ease(k1[2] if len(k1) > 2 else "inout_sine", (t - k0[0]) / (k1[0] - k0[0]))
                cam = _cam_lerp(_resolve(k0[1]), _resolve(k1[1]), u)
                break
    # a breathing drift, constant in screen px whatever the zoom
    dx = 2.4 * core.fbm1(t * 0.18, 2, 11) / cam.zoom
    dy = 1.6 * core.fbm1(t * 0.18, 2, 17) / cam.zoom
    return core.Camera(cam.x + dx, cam.y + dy, cam.zoom)


# ----------------------------------------------------------------------------------------
# the book's state: opening, the three page turns
# ----------------------------------------------------------------------------------------

def book_state(t):
    """-> (open, spread, turn)."""
    o = clamp((t - T_OPEN) / OPEN_DUR)
    for (t0, d, k) in ((T_TURN1, TURN_DUR, 0), (T_TURN2, TURN_DUR, 1), (T_TURN3, TURN3_DUR, 2)):
        if t0 <= t < t0 + d:
            return 1.0, k, core.inout_sine((t - t0) / d)
    if t < T_TURN1:
        return o, 0, 0.0
    if t < T_TURN2:
        return 1.0, 1, 0.0
    if t < T_TURN3:
        return 1.0, 2, 0.0
    return 1.0, 3, 0.0


# ----------------------------------------------------------------------------------------
# the bard's staging (the music itself -- strums, chords, beat, singing -- comes from bard_song)
# ----------------------------------------------------------------------------------------

def bard_pose(t):
    song = ch.bard_song(t)
    tune = song.get("tune", 0.0)
    # after the flourish he looks to the book (eyes first, then the head), delighted as it opens
    to_book = smooth((t - (T_FLOURISH + 0.05)) / 0.3) * (1.0 - smooth((t - (T_VAMP + 0.45)) / 0.5))
    to_us_intro = smooth((t - (T_VAMP + 0.45)) / 0.4) * (1.0 - smooth((t - (LN[1].start + 0.2)) / 0.5))
    # the interlude: eyes closed on "paaane", then he opens them and watches the page turn itself
    watch = smooth((t - (LN[4].end + 0.05)) / 0.35) * (1.0 - smooth((t - (T_CUT_C - 0.1)) / 0.3))
    # the coda: up to us on "spell", the stool, the wink
    up = smooth((t - T_LOOKUP) / 0.6)
    stool = smooth((t - (wt(9, "pull") - 0.1)) / 0.25) * (1.0 - smooth((t - (T_FRIEND - 0.12)) / 0.25))
    to_book_end = smooth((t - (LN[10].start - 0.05)) / 0.5)
    look_cam = max(0.45 * to_us_intro, up * (1.0 - 0.75 * stool) * (1.0 - to_book_end))
    look_x = 0.75 * to_book + 0.8 * watch + 0.55 * stool + 0.85 * to_book_end * (1.0 - up * (1 - to_book_end))
    look_y = -0.1 * to_book + 0.65 * stool - 0.05 * watch
    head_turn = 0.35 * smooth((t - (T_FLOURISH + 0.18)) / 0.35) * (1.0 - smooth((t - (T_VAMP + 0.4)) / 0.5))
    head_turn += 0.3 * watch + 0.18 * stool + 0.35 * to_book_end
    nod = -0.35 * math.sin(math.pi * clamp((t - (T_STOOL - 0.15)) / 0.5)) * stool
    wink = smooth((t - T_WINK) / 0.1) * (1.0 - smooth((t - (T_WINK + 0.42)) / 0.18))
    mood, mood2, mix_ = "twinkle", "listen", tune
    if t > T_FRIEND - 0.1 and t < LN[10].start:
        mood, mood2, mix_ = "warm", "sly", smooth((t - (wt(9, "hear") - 0.1)) / 0.25)
    rap = song.get("rapture", 0.0) * (1.0 - 0.8 * up * (1.0 - to_book_end))
    # beak legibility: the rig's "e" barely parts the mandibles (x0.55), and the quiet aside of
    # "...hear how it's said" sings at ~0.4 -- open both up a touch so every syllable reads
    sing = song.get("sing", 0.0)
    if (song.get("vowel") or "a")[:1] in ("e", "i"):
        sing *= 0.75 / 0.55
    sing = clamp(sing) ** 0.85
    song = dict(song, rapture=rap, sing=sing)
    return ch.BardPose(sit=1.0, facing=1, turn=-0.45, look_cam=look_cam, look=(look_x, look_y), head_turn=head_turn,
                       head_nod=nod, mood=mood, mood2=mood2, mood_mix=mix_, wink=wink, tail_swing=-0.6, seed=2,
                       **song)


# ----------------------------------------------------------------------------------------
# setup + draw
# ----------------------------------------------------------------------------------------

def setup():
    st = {"light": fx.LightLayer()}
    store = {}
    st["wall"] = fx.Layer(lambda c: draw_wall(c, store), blur=1.1, opaque=True, **M)
    st["floor"] = fx.Layer(lambda c: draw_floor(c, store), blur=0.6, **M)
    st["fg"] = fx.Layer(draw_fg_candle, blur=9.0, x=FG_CANDLE[0] - 160, y=FG_CANDLE[1] - 120, w=320, h=560)
    st.update(store)
    st["book"] = PG.make_book(EV)
    for sp_ in st["book"].spreads:
        for pg in (sp_.left, sp_.right):
            GILT[id(pg)] = _page_gilt(pg)
    lrig = sb.draw_lectern(core.frame(4, 4)[1], LECT_X, LECT_Y, LECT_SC, L_CANDLE, st["book"], height=LECT_HT,
                           view=VIEW_WIDE)
    st["lectern_candles"] = lrig.candles
    return st


# ---- gold leaf that glints as the light and the camera move -------------------------------

def _flat_loop(build):
    """Flatten a path built by build(cr) into one polyline (page units)."""
    surf, c = core.frame(4, 4)
    c.new_path()
    build(c)
    pts = []
    for kind, xy in c.copy_path_flat():
        if kind in (cairo.PATH_MOVE_TO, cairo.PATH_LINE_TO) and xy:
            pts.append(tuple(xy))
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def _page_gilt(page):
    """The gilt lines of one of our pages, as page-unit polylines: the border rule and the gold
    frame of its illustration (if it has one)."""
    w, h = 150.0, 200.0
    m = w * 0.075
    loops = [[(m, m), (w - m, m), (w - m, h - m), (m, h - m), (m, m)]]
    art = getattr(page, "illus", None)
    if isinstance(art, PG.PageArt) and art.box is not None and art.frame:
        bx, by, bw, bh = art.box[0] * w, art.box[1] * h, art.box[2] * w, art.box[3] * h
        loops.append(_flat_loop(lambda c: sb._frame_path(c, bx, by, bw, bh, art.frame)))
    return loops


def _along_loop(pts, s0, s1, n=10):
    """Points of the closed polyline between arc-length fractions s0..s1 (may wrap)."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    out = []
    for k in range(n + 1):
        u = ((s0 + (s1 - s0) * k / n) % 1.0) * total
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= u:
                f = (u - acc) / max(1e-6, L)
                out.append((lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)))
                break
            acc += L
    return out


def draw_glints(cr, t, cam, brig, book, spread, vis):
    """A burnished highlight sliding along each gilt rule of the open pages: where it sits on the
    loop depends on the camera's position (a specular moves when the eye moves) and drifts with the
    candle; its brightness breathes with the flame."""
    if vis <= 0.01:
        return
    fl = sb.candle_flicker(t, 3)[0]
    sp = book.spread(spread)
    for side, page in (("left", sp.left), ("right", sp.right)):
        M_ = brig.page_matrix.get(side)
        if M_ is None:
            continue
        for k, loop in enumerate(GILT.get(id(page), [])):
            if len(loop) < 3:
                continue
            base = 0.37 * k + (0.13 if side == "right" else 0.61)
            sc = base + 0.035 * t + 0.00042 * cam.x + 0.00031 * cam.y
            for j, off in enumerate((0.0, 0.5)):
                c = sc + off + 0.04 * math.sin(t * 0.7 + j)
                a = vis * (0.55 + 0.45 * math.sin(t * 0.9 + 2.0 * j + k)) * clamp(fl - 0.05)
                if a < 0.05:
                    continue
                pts = [M_.transform_point(*p) for p in _along_loop(loop, c - 0.035, c + 0.035, 12)]
                wpx = (1.6 if k == 0 else 2.2) * LECT_SC
                B.detail_line(cr, pts, wpx, "#fff4cc", 0.8 * a, taper=(0.05, 1.0, 0.05))
                mx, my = pts[len(pts) // 2]
                fx.sparkle(cr, mx, my, 5.0 * LECT_SC, "#fffbe8", 0.85 * a, angle=0.3 * math.sin(t))


def cover_glint(cr, t, t0, t1):
    """Before the book opens: a sheen of candlelight sweeps across the closed cover and its gilt
    title, with a twinkle where it crosses the letters."""
    if not t0 < t < t1:
        return
    u = (t - t0) / (t1 - t0)
    W_, H_, ov = 150.0, 200.0, 6.0
    CW, CH = W_ + ov + 0.8, H_ + 2 * ov
    cv, sv = math.cos(VIEW_WIDE), math.sin(VIEW_WIDE)
    z_h = 2.0 * 12.0 + 4.5 * 0.5
    shift = -(W_ + ov) * 0.5

    def C(bx, by):
        return DESK[0] + LECT_SC * (bx + shift), DESK[1] + LECT_SC * (by * cv - z_h * sv)
    poly = [C(0, -CH / 2), C(CW, -CH / 2), C(CW, CH / 2), C(0, CH / 2)]
    a = math.sin(math.pi * u)
    sx = lerp(-40.0, CW + 40.0, core.inout_sine(u))
    cr.save()
    cr.new_path()
    core.polygon(cr, poly)
    cr.clip()
    g = cairo.LinearGradient(*C(sx - 34, -CH / 2), *C(sx + 34, CH / 2))
    g.add_color_stop_rgba(0.0, 1.0, 0.85, 0.55, 0.0)
    g.add_color_stop_rgba(0.5, 1.0, 0.88, 0.6, 0.22 * a)
    g.add_color_stop_rgba(1.0, 1.0, 0.85, 0.55, 0.0)
    cr.set_source(g)
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.paint()
    cr.restore()
    # the twinkle as the sheen crosses the title's letters
    tx, ty = C(min(CW - 30.0, max(34.0, sx)), -CH * 0.12)
    fx.sparkle(cr, tx, ty, 9.0 * LECT_SC, "#fff6d8", 0.9 * a, angle=0.6 * u)


def drop_cap_glint(cr, t, t0, brig):
    """'Once': the illuminated O catches the light as the first word is sung."""
    if not t0 - 0.05 < t < t0 + 1.1:
        return
    u = (t - t0 + 0.05) / 1.15
    a = math.sin(math.pi * clamp(u * 1.4)) * (1.0 - u * 0.4)
    M_ = brig.page_matrix.get("left")
    if M_ is None:
        return
    size = 150.0 / 17.0
    cap = size * 1.24 * 3 - size * 0.15
    x0, y0 = 150.0 * 0.11, 200.0 * 0.11 + size * 0.12
    cx, cy = M_.transform_point(x0 + cap * 0.32, y0 + cap * 0.3)
    fx.glow(cr, cx, cy, 30.0 * LECT_SC, "#ffd98a", 0.35 * a)
    fx.sparkle(cr, cx, cy, 9.0 * LECT_SC * (0.6 + 0.4 * a), "#fffbe8", 0.95 * a, angle=0.8 * u)
    ex, ey = M_.transform_point(x0 + cap * 0.85, y0 + cap * 0.75)
    fx.sparkle(cr, ex, ey, 5.0 * LECT_SC * a, "#fff2c0", 0.8 * a, angle=-0.5 * u)


# ---- the storyteller's shadow on the wall (Klaus: light is shape) --------------------------

SHADOW_RES = 0.25


def draw_bard_shadow(cr, st, cam, pose, t, strength=1.0):
    """The bard's silhouette cast big and soft on the stone wall behind him by the lectern candles
    (to his right): drawn at quarter resolution through a skew-and-stretch, blurred, and laid on
    the wall as a plum shadow -- it plays the lute along with him."""
    from PIL import Image, ImageFilter
    sw_, sh_ = int(W * SHADOW_RES), int(H * SHADOW_RES)
    surf = st.get("_shadow_surf")
    if surf is None:
        surf = core.new_surface(sw_, sh_)
        st["_shadow_surf"] = surf
    c2 = cairo.Context(surf)
    c2.set_operator(cairo.OPERATOR_CLEAR)
    c2.paint()
    c2.set_operator(cairo.OPERATOR_OVER)
    c2.scale(SHADOW_RES, SHADOW_RES)
    c2.transform(cam.matrix(WALL_P))
    # the shadow transform: about the bard's foot, stretched up the wall and thrown to the left
    fxp, fyp = BARD_X, WALL_Y + 10.0
    c2.translate(fxp - 175.0, fyp)
    c2.transform(cairo.Matrix(1.18, 0.0, -0.32, 1.12, 0.0, 0.0))
    c2.translate(-BARD_X, -BARD_Y)
    ch.draw_bard(c2, BARD_X, BARD_Y, BARD_SC, pose.with_(shadow=False), L_CANDLE, t, detail=0)
    surf.flush()
    img = Image.frombuffer("RGBA", (sw_, sh_), bytes(surf.get_data()), "raw", "BGRA", surf.get_stride(), 1)
    alpha = img.getchannel("A").filter(ImageFilter.GaussianBlur(4.0))
    data = bytearray(sw_ * sh_ * 4)
    data[3::4] = alpha.tobytes()
    mask = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, sw_, sh_, sw_ * 4)
    cr.save()
    with cam.view(cr, WALL_P):                       # only on the wall, above the floor line
        cr.rectangle(-400, -400, W + 800, WALL_Y + 400)
    cr.identity_matrix()
    cr.clip()
    cr.scale(1.0 / SHADOW_RES, 1.0 / SHADOW_RES)
    core.src(cr, "#12060a", 0.5 * strength)
    cr.mask_surface(mask, 0, 0)
    cr.restore()


def wink_ting(cr, t, t0, rig, dur=0.6):
    """The wink's 'ting!': a four-point sparkle popping at the winking (near) eye's outer corner,
    with a smaller one trailing it (bard_twinkle puts it on the comb for a right-facing head)."""
    if not t0 <= t <= t0 + dur or not rig.eyes:
        return
    u = (t - t0) / dur
    s = rig.scale
    ex, ey = rig.eyes[-1]
    side = -1.0 if rig.yaw >= 0 else 1.0                  # the outer corner of the near eye
    pop = core.out_back(clamp(u / 0.25)) * (1.0 - smooth((u - 0.55) / 0.45))
    fx.sparkle(cr, ex + side * 16.0 * s, ey - 13.0 * s, 10.0 * s * pop, "#fff6d8", 0.95 * pop, angle=0.5 * u)
    p2 = math.sin(math.pi * clamp((u - 0.18) / 0.6))
    fx.sparkle(cr, ex + side * 25.0 * s, ey - 4.0 * s, 5.0 * s * p2, "#ffe7a8", 0.8 * p2, angle=-0.4 * u)


def _on_screen(cam, x0, y0, x1, y1, p=1.0, pad=40):
    ax, ay = cam.to_screen(x0, y0, p)
    bx, by = cam.to_screen(x1, y1, p)
    return not (max(ax, bx) < -pad or min(ax, bx) > W + pad or max(ay, by) < -pad or min(ay, by) > H + pad)


def draw(cr, t, st):
    cam = camera_at(t)
    z = cam.zoom
    view = view_for_zoom(z)
    k_book = smooth((z - 2.6) / (4.2 - 2.6))          # 0 in the nook .. 1 deep in the book
    deep = z > 4.6
    flames = []
    # ---- the wall (parallax), the hearth fire
    if not deep:
        with cam.view(cr, WALL_P):
            st["wall"].paint(cr)
            if _on_screen(cam, HEARTH_X - 260, WALL_Y - 400, HEARTH_X + 260, WALL_Y + 40, WALL_P):
                fire = sb.draw_fire(cr, *st["hearth"].fire, HEARTH_SC, t=t, seed=1)
            else:
                fire = sb.FireRig(glow=st["hearth"].fire, flicker=sb.fire_flicker(t, 1))
        bard_vis = _on_screen(cam, BARD_X - 190, BARD_Y - 480, BARD_X + 230, BARD_Y + 30)
        st["_pose"] = bard_pose(t) if bard_vis else None
        if st["_pose"] is not None and z < 2.6:
            draw_bard_shadow(cr, st, cam, st["_pose"], t, strength=1.0 - smooth((z - 2.0) / 0.6))
        with cam.view(cr, 1.0):
            st["floor"].paint(cr)
    else:
        st["_pose"] = None
        core.src(cr, "#140a0c")
        cr.paint()
        fire = sb.FireRig(glow=st["hearth"].fire, flicker=sb.fire_flicker(t, 1))
    o, spread, turn = book_state(t)
    with cam.view(cr, 1.0):
        # ---- the lectern (drawn with the current desk angle) and the great book
        if not deep:
            sb.draw_lectern(cr, LECT_X, LECT_Y, LECT_SC, L_CANDLE, st["book"], height=LECT_HT, view=view)
        brig = sb.draw_book(cr, st["book"], DESK[0], DESK[1], LECT_SC, t=t, open=o, spread=spread, turn=turn,
                            light=L_CANDLE, view=view)
        cover_glint(cr, t, 0.9, T_OPEN + 0.1)
        if o >= 1.0:
            gv = 1.0
            for t0_ in (T_TURN1, T_TURN2, T_TURN3):
                gv = min(gv, smooth(abs(t - t0_) / 0.25) if t < t0_ else 1.0)
                if t0_ <= t < t0_ + (TURN3_DUR if t0_ == T_TURN3 else TURN_DUR) + 0.2:
                    gv = 0.0
            draw_glints(cr, t, cam, brig, st["book"], spread, gv)
        drop_cap_glint(cr, t, LN[1].start + 0.02, brig)
        for i, c in enumerate(st["lectern_candles"]):
            if _on_screen(cam, c[0] - 60, c[1] - 120, c[0] + 60, c[1] + 20):
                cd = sb.draw_candle(cr, c[0], c[1], LECT_SC, t=t + i * 0.9, light=L_CANDLE, seed=i + 2, height=40.0)
                flames.append(cd)
        if not deep:
            # the empty stool, waiting for you
            if _on_screen(cam, STOOL_X - 90, STOOL_Y - 110, STOOL_X + 90, STOOL_Y + 20):
                ch.draw_bard_stool(cr, STOOL_X, STOOL_Y, BARD_SC, L_CANDLE, yaw=0.55)
            # the bard
            if st.get("_pose") is not None:
                pose = st["_pose"]
                ch.draw_bard_stool(cr, BARD_X, BARD_Y, BARD_SC, L_CANDLE, yaw=ch.bard_yaw(pose))
                rig = ch.draw_bard(cr, BARD_X, BARD_Y, BARD_SC, pose, L_CANDLE, t)
                wink_ting(cr, t, T_WINK + 0.06, rig)
            sx, sy = st["stack_top"]
            if _on_screen(cam, sx - 60, sy - 120, sx + 60, sy + 20):
                flames.append(sb.draw_candle(cr, sx + 10, sy, 1.9, t=t + 2.1, light=L_CANDLE, seed=7, height=22.0,
                                             width=12.0, drips=4))
        # gold motes rising off the open pages (the pages come alive)
        if o > 0.3:
            (lx0, ly0), (rx1, ry1) = brig.pages["left"][0], brig.pages["right"][2]
            md = 0.45 * clamp((o - 0.3) / 0.4) * (1.0 - 0.75 * k_book)
            if md > 0.01:
                fx.dust(cr, t, (lx0, ly0 - 60, rx1 - lx0, ry1 - ly0 + 40), n=22, color="#ffe3a0", alpha=md,
                        size=(1.0 / max(1.0, z / 2.0), 2.6 / max(1.0, z / 2.0)), seed=5, drift=(3.0, -12.0), twinkle=1.0)
    # ---- the near candle we push past (out of focus, parallax)
    fgx, fgy = cam.to_screen(FG_CANDLE[0], FG_CANDLE[1], FG_P)
    fz = z ** FG_P
    fg_a = 1.0 - smooth((fz - 2.3) / 0.5)              # the camera has passed it: gone
    fg_vis = fg_a > 0.01 and -300 < fgx < W + 300
    if fg_vis:
        with cam.view(cr, FG_P):
            st["fg"].paint(cr, alpha=fg_a)
    # ---- light: candles, the hearth, a pool on the open book, moonlight, the bard's floor pool
    lc = st["light"].begin()
    zf = min(z, 3.0)
    for cd in flames:
        sxy = cam.to_screen(*cd.flame)
        fx.glow(lc, sxy[0], sxy[1], 320 * zf * cd.flicker, "#ffaa55", 0.36)
    hx, hy = cam.to_screen(*fire.glow, WALL_P)
    fx.glow(lc, hx, hy, min(1400, 900 * z ** WALL_P) * fire.flicker, "#ff7a30", 0.34 * (1 - k_book))
    if o > 0.2:
        bx = (brig.pages["left"][0][0] + brig.pages["right"][1][0]) / 2
        by = (brig.pages["left"][0][1] + brig.pages["left"][3][1]) / 2
        sbx, sby = cam.to_screen(bx, by)
        fl = sb.candle_flicker(t, 3)[0]
        fx.light_pool(lc, sbx, sby, min(1500, 520 * z), min(900, 280 * z), "#ffcf8a",
                      lerp(0.08, 0.16, k_book) * clamp((o - 0.2) / 0.3) * fl)
    if not deep:
        mx, my = cam.to_screen(WIN_X + 75, WIN_Y + 120, WALL_P)
        fx.glow(lc, mx, my, 300 * z, "#7f9fe0", 0.12)
        px, py = cam.to_screen(BARD_X + 60, BARD_Y + 5)
        fx.light_pool(lc, px, py, 420 * z, 90 * z, "#ffa060", 0.14)
    if fg_vis:
        fl = sb.candle_flicker(t, 9)
        quiet = lerp(1.0, 0.45, smooth((t - 3.5) / 1.5))
        fx.glow(lc, fgx, fgy - 8 * fz, min(1100, 520 * fz) * fl[0], "#ffb060", 0.5 * fg_a * quiet)
        fx.glow(lc, fgx, fgy - 4 * fz, 70 * fz * fl[0], "#ffe0a0", 0.55 * fg_a)
    fx.post(cr, t, light=st["light"], bloom_strength=lerp(0.6, 0.28, k_book), threshold=lerp(0.8, 0.92, k_book),
            bloom_radius=2.4, grain=0.035, vignette=lerp(0.55, 0.42, k_book), vignette_color=(0.06, 0.02, 0.04))
    # ---- the fades (the near candle's flame is the first and last thing we see)
    if t < T_FADEIN:
        fx.fade(cr, 1.0 - core.inout_sine(clamp(t / T_FADEIN)))
    if t > T_OUT0:
        fx.fade(cr, core.inout_sine(clamp((t - T_OUT0) / (T_OUT1 - T_OUT0))))
    if fg_vis and t < T_FADEIN + 0.5:
        fl = sb.candle_flicker(t, 9)
        fx.glow(cr, fgx, fgy - 6 * fz, 60 * fz, "#ffd9a0", 0.55 * fl[0] * (1.0 - smooth(t / (T_FADEIN + 0.5))))


# ----------------------------------------------------------------------------------------
# sound: discrete on-screen events for the foley pass (times as the animation uses them)
# ----------------------------------------------------------------------------------------

SFX_CUES = sorted([
    (0.35, "candle_flicker", {"gain": 0.5, "pan": 0.55}),
    (T_COVER_LAND - 0.58, "book_open", {"gain": 0.9, "pan": 0.35}),            # its "land" thump = cover lands
    (EV["lock"], "door_close", {"gain": 0.22, "pan": 0.1, "dist": 0.7}),       # the painted doors slam (muffled)
    (EV["latch"] + 0.3, "tap_wood", {"gain": 0.25, "pan": 0.2, "dist": 0.6}),   # shutters latch
    (EV["latch"] + 0.55, "tap_wood", {"gain": 0.2, "pan": 0.35, "dist": 0.6}),
    (T_TURN1, "page_turn", {"heavy": True, "gain": 0.8, "pan": 0.3}),
    (EV["stone"], "rune_glow", {"gain": 0.25, "pan": 0.3, "dist": 0.5}),       # the rune-stone flares
    (T_TURN2, "page_turn", {"heavy": True, "gain": 0.6, "pan": 0.35}),
    (T_WINK + 0.05, "crystal_chime", {"gain": 0.3, "pan": -0.2}),              # the wink's "ting!"
    (T_TURN3, "page_turn", {"heavy": True, "gain": 0.8, "pan": 0.3}),
    (T_OUT0 - 1.5, "candle_flicker", {"gain": 0.45, "pan": 0.4}),
], key=lambda c: c[0])
