"""_s4_sets.py -- private set painting for S4 (the tavern door): the exterior street and the
facade of THE MERRY FLAGON, the hand insert's backdrop, and the interior hall. Scene-local
helpers only (owned by s4_tavern.py); everything is drawn with the library (core / env / fx /
props) and cached in fx.Layers by the scene's setup().

World coordinates are the screen coordinates of each set's wide framing (zoom 1).
"""

import math

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib.characters import base as B

TAU = math.tau

# ----------------------------------------------------------------------------------------
# one clock for the band and one for the laugh (the uncanny part: everyone shares them)
# ----------------------------------------------------------------------------------------

JIG_BPM = 116.0            # the tavern jig: one light pulse per dotted-quarter beat (6/8)
JIG_PERIOD = 60.0 / JIG_BPM


JIG_T0 = 0.0               # beat phase: the scene sets it so a beat lands exactly on s4_swell


def jig_pulse(t, t0=None, lilt=0.45):
    """The muffled music's light pulse, 0..~1.2: a hit on each dotted-quarter beat and a lighter
    one on the beat's last eighth (the jig's long-short lilt)."""
    u = ((t - (JIG_T0 if t0 is None else t0)) / JIG_PERIOD) % 1.0
    a = math.exp(-u / 0.13)
    v = u - 2.0 / 3.0
    b = lilt * math.exp(-v / 0.09) if v >= 0 else 0.0
    return a + b


def jig_beats(t0, t1, phase0=None):
    """Beat times in [t0, t1)."""
    phase0 = JIG_T0 if phase0 is None else phase0
    k = math.ceil((t0 - phase0) / JIG_PERIOD)
    out = []
    while phase0 + k * JIG_PERIOD < t1:
        out.append(phase0 + k * JIG_PERIOD)
        k += 1
    return out


# ----------------------------------------------------------------------------------------
# palettes
# ----------------------------------------------------------------------------------------

EXT = dict(env.PALETTES["night"])
EXT.update(stone="#3a3448", ground="#1a1826", haze="#2c3458", window="#ff9a70", window_dark="#141626")

HOT = "#ff4f9a"            # the tavern's magenta
AMBER = "#ffae4a"          # its amber
HOT_PALE = "#ffc2dc"
COLD = "#8fb4ff"           # moonlight
NIGHT_INK = "#0b0e1c"

# ----------------------------------------------------------------------------------------
# EXTERIOR: THE MERRY FLAGON seen across the street (shots EXT_IN / EXT_OUT)
# ----------------------------------------------------------------------------------------

FAC_X0, FAC_X1 = 505.0, 2240.0        # facade's left corner .. beyond the right edge
FAC_BASE = 836.0                      # where the facade meets the street
JETTY_Y = 440.0                       # the jetty beam (ground storey top)
EAVE_Y = 118.0                        # the eaves
DOOR_CX, DOOR_W, DOOR_TOP = 1230.0, 204.0, 498.0   # the arched door opening (DOOR_TOP = crown)
DOOR_SPRING = DOOR_TOP + DOOR_W / 2   # where the arch springs from the jambs
WIN_L = (690.0, 560.0, 300.0, 196.0)  # ground-floor windows (x, y, w, h)
WIN_R = (1590.0, 566.0, 230.0, 184.0)
WIN_UP = [(780.0, 262.0, 150.0, 168.0), (1230.0, 262.0, 150.0, 168.0), (1690.0, 262.0, 150.0, 168.0)]   # centres
SIGN_AT = (FAC_X0 + 6.0, 476.0)       # the hanging sign's wall bracket
EXT_GROUND = 948.0                    # where the characters stand (in front of the facade)
EXT_LAYER = dict(x=-120.0, y=-90.0, w=2440.0, h=1270.0)


def _arch_path(cr, cx, top, w, base, inset=0.0):
    r = w / 2 - inset
    cr.move_to(cx - r, base)
    cr.line_to(cx - r, top + w / 2)
    cr.arc(cx, top + w / 2, r, math.pi, TAU)
    cr.line_to(cx + r, base)
    cr.close_path()


def door_path(cr, inset=0.0):
    _arch_path(cr, DOOR_CX, DOOR_TOP + inset, DOOR_W - 2 * inset, FAC_BASE, 0.0)


def _beam(cr, x0, y0, x1, y1, w, col, lit, dark):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    core.polygon(cr, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])
    core.src(cr, col)
    cr.fill()
    k = 0.3
    core.polygon(cr, [(x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 - nx * (1 - 2 * k), y1 - ny * (1 - 2 * k)),
                      (x0 - nx * (1 - 2 * k), y0 - ny * (1 - 2 * k))])
    core.src(cr, lit, 0.55)
    cr.fill()
    core.polygon(cr, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 + nx * 0.7, y1 + ny * 0.7), (x0 + nx * 0.7, y0 + ny * 0.7)])
    core.src(cr, dark, 0.7)
    cr.fill()


def _plaster(cr, x, y, w, h, base, seed=0):
    cr.rectangle(x, y, w, h)
    core.src(cr, base)
    cr.fill()
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    env.texture(cr, "plaster", 0.22, 1.0, offset=(seed * 37.0, seed * 11.0))
    cr.restore()


def _hot_wash(cr, x, y, rx, ry, color, alpha):
    """Baked light falloff from a lantern / window on the facade (painted, not additive)."""
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, ry / rx)
    g = core.radial(0, 0, rx, [(0.0, core.alpha(color, alpha)), (0.4, core.alpha(color, alpha * 0.45)),
                               (1.0, core.alpha(color, 0.0))])
    cr.set_source(g)
    cr.arc(0, 0, rx, 0, TAU)
    cr.fill()
    cr.restore()


def draw_ext_sky(cr):
    """Night sky behind the gap left of the tavern: stars and a few soft cloud banks (cached,
    blurred). No stratus streaks: in the narrow gap they read as seams across the night."""
    env.draw_sky(cr, -120, -90, 2440, 1270, kind=EXT, horizon=760, seed=4, moon=False, clouds=False)
    env.draw_clouds(cr, -120, -90, 2440, 850, kind=EXT, seed=4, light_from=(236.0, 150.0), streaks=0, alpha=0.85)


def draw_ext_far(cr):
    """Through the gap left of the tavern: the castle on its hill under the moon and the far
    town's roofs, cold, quiet and small (everything the tavern is not)."""
    k = EXT
    env.draw_moon(cr, 236.0, 150.0, 28.0, kind=k, glow=0.9)
    env.draw_castle_hill(cr, 212, 600, 0.6, kind=k, hill_w=640, hill_h=140, seed=2, windows=6,
                         color="#202b4e", rim="#a8c0f4", window_color="#a8d0ff", window_alpha=0.95, light_dx=-0.25)
    env.draw_haze(cr, -120, 560, 820, 200, k["haze"], 0.0, 0.26)
    env.draw_roofline(cr, -140, 700, 770, 0.1, k, seed=7, lit=0.35, spire=False, haze=0.05)
    cr.rectangle(-140, 770, 820, 160)
    core.src(cr, "#0d1120")
    cr.fill()


def draw_ext_neighbour(cr):
    """The shuttered house next door (left edge): cold and asleep; the tavern's lantern string
    is tied to its timbers."""
    env.draw_house(cr, -330, FAC_BASE + 6, w=560, floors=2, scale=0.78, kind=EXT, seed=21, lit=0.0,
                   roof="side", ground="stone", shutters="closed", shop=False, chimney=False, jetty=26, detail=1)
    cr.rectangle(-140, -100, 300, FAC_BASE + 110)
    cr.set_source(core.linear(-140, 0, 160, 0, [core.alpha("#05070f", 0.55), core.alpha("#05070f", 0.2)]))
    cr.fill()
    # the tavern's glow licks its right edge
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    _hot_wash(cr, 300, 420, 130, 360, "#3a1028", 0.6)
    cr.restore()


def draw_ext_facade(cr):
    """THE MERRY FLAGON's facade (static parts): stone plinth, timber-framed plaster ground
    storey, jetty, half-timbered upper storey, eaves and roof -- with the lantern light baked in
    as warm magenta/amber pools. Openings (windows, door) are painted dark; their light and
    life are drawn per frame."""
    tim, tim_lit, tim_dk = "#2c1c22", "#5a3a40", "#140c10"
    pl_up, pl_dn = "#5a4458", "#4c3a4c"
    # ---- roof (above the eaves, mostly off the top of the frame)
    core.polygon(cr, [(FAC_X0 - 60, EAVE_Y + 8), (FAC_X0 + 40, -100), (FAC_X1 + 60, -100), (FAC_X1 + 60, EAVE_Y + 8)])
    core.src(cr, "#1c1a28")
    cr.fill()
    cr.save()
    core.polygon(cr, [(FAC_X0 - 60, EAVE_Y + 8), (FAC_X0 + 40, -100), (FAC_X1 + 60, -100), (FAC_X1 + 60, EAVE_Y + 8)])
    cr.clip()
    core.src(cr, "#0e0d16", 0.8)
    yy = EAVE_Y
    row = 0
    while yy > -100:
        cr.rectangle(FAC_X0 - 60, yy - 3, FAC_X1 - FAC_X0 + 120, 3.0)
        for k in range(int((FAC_X1 - FAC_X0 + 120) / 46) + 2):
            cr.rectangle(FAC_X0 - 60 + k * 46 + (23 if row % 2 else 0), yy - 30, 2.4, 28)
        yy -= 32
        row += 1
    cr.fill()
    env.texture(cr, "stone", 0.2, 0.8)
    cr.restore()
    # ---- upper storey (jettied 26 px), plaster + timber frame
    ux0, ux1 = FAC_X0 - 26, FAC_X1
    _plaster(cr, ux0, EAVE_Y, ux1 - ux0, JETTY_Y - EAVE_Y, pl_up, seed=3)
    for (cx, cy, w, h) in WIN_UP:                  # warm pools round the upper windows
        _hot_wash(cr, cx, cy + 10, w * 1.25, h * 1.0, HOT, 0.30)
        _hot_wash(cr, cx, cy + 20, w * 0.8, h * 0.7, AMBER, 0.22)
    bays = [ux0 + 14, 600.0, 905.0, 1080.0, 1385.0, 1540.0, 1850.0, 2050.0, ux1]
    for bx in bays:
        _beam(cr, bx, EAVE_Y, bx, JETTY_Y, 22, tim, tim_lit, tim_dk)
    for (a, b) in ((bays[1], bays[2]), (bays[3], bays[4]), (bays[5], bays[6])):
        pass
    # braces in the plain bays (the windowed bays get a sill rail instead)
    for (a, b, kind) in ((bays[0], bays[1], "x"), (bays[3], 1080.0, "none"), (bays[6], bays[7], "v"), (bays[7], bays[8], "x")):
        if kind == "x":
            _beam(cr, a + 8, EAVE_Y + 10, b - 8, JETTY_Y - 10, 16, tim, tim_lit, tim_dk)
            _beam(cr, a + 8, JETTY_Y - 10, b - 8, EAVE_Y + 10, 16, tim, tim_lit, tim_dk)
        elif kind == "v":
            m = (a + b) / 2
            _beam(cr, a + 8, EAVE_Y + 14, m, JETTY_Y - 12, 16, tim, tim_lit, tim_dk)
            _beam(cr, b - 8, EAVE_Y + 14, m, JETTY_Y - 12, 16, tim, tim_lit, tim_dk)
    # a curved "ogee" brace pair either side of the middle window (storybook carpentry)
    for sgn, bx in ((-1, 1080.0), (1, 1385.0)):
        pts = [(bx, JETTY_Y - 14), (bx - sgn * 40, JETTY_Y - 70), (bx - sgn * 70, JETTY_Y - 150)]
        core.tapered(cr, core.spline(pts, 6), 9.0, 7.0)
        core.src(cr, tim)
        cr.fill()
    _beam(cr, ux0 - 6, EAVE_Y + 8, ux1 + 6, EAVE_Y + 8, 22, tim, tim_lit, tim_dk)            # wall plate
    for (cx, cy, w, h) in WIN_UP:                                                          # sill rails
        _beam(cr, cx - w / 2 - 34, cy + h / 2 + 26, cx + w / 2 + 34, cy + h / 2 + 26, 14, tim, tim_lit, tim_dk)
    # grime toward the jetty, cold toward the eaves (the lanterns light it from below)
    cr.rectangle(ux0, EAVE_Y, ux1 - ux0, 120)
    cr.set_source(core.linear(0, EAVE_Y, 0, EAVE_Y + 120, [core.alpha("#0a0c1c", 0.55), core.alpha("#0a0c1c", 0.0)]))
    cr.fill()
    # the eave's shadow line
    cr.rectangle(ux0 - 70, EAVE_Y - 2, ux1 - ux0 + 140, 18)
    core.src(cr, "#07070e", 0.9)
    cr.fill()
    # ---- ground storey
    gx0, gx1 = FAC_X0, FAC_X1
    _plaster(cr, gx0, JETTY_Y, gx1 - gx0, FAC_BASE - JETTY_Y, pl_dn, seed=9)
    # baked warm pools: windows, the door, the string of lanterns under the jetty
    x, y, w, h = WIN_L
    _hot_wash(cr, x + w / 2, y + h / 2, w * 1.0, h * 1.25, HOT, 0.32)
    x, y, w, h = WIN_R
    _hot_wash(cr, x + w / 2, y + h / 2, w * 1.05, h * 1.3, HOT, 0.28)
    _hot_wash(cr, DOOR_CX, 640, 260, 300, AMBER, 0.2)
    for k in range(9):
        _hot_wash(cr, 600 + k * 190, JETTY_Y + 70, 120, 70, AMBER if k % 2 else HOT, 0.16)
    # stone plinth along the foot
    env.draw_stone_wall(cr, gx0, FAC_BASE - 54, gx1 - gx0, 54, kind=EXT, seed=13, block=(70.0, 27.0),
                        color="#3e3446", texture_alpha=0.18)
    posts = [gx0 + 12, 650.0, 1035.0, DOOR_CX - DOOR_W / 2 - 34, DOOR_CX + DOOR_W / 2 + 34, 1530.0, 1880.0, 2100.0]
    for px in posts:
        _beam(cr, px, JETTY_Y, px, FAC_BASE - 50, 24, tim, tim_lit, tim_dk)
    _beam(cr, gx0, FAC_BASE - 56, gx1, FAC_BASE - 56, 18, tim, tim_lit, tim_dk)              # sole plate
    for (a, b) in ((posts[0], posts[1]), (posts[6], posts[7])):
        _beam(cr, a + 10, FAC_BASE - 64, b - 10, JETTY_Y + 14, 16, tim, tim_lit, tim_dk)
    # window surrounds (deep timber frames, a sill, a little hood moulding)
    for (x, y, w, h) in (WIN_L, WIN_R):
        cr.rectangle(x - 18, y - 18, w + 36, h + 36)
        core.src(cr, tim)
        cr.fill()
        cr.rectangle(x - 26, y + h + 12, w + 52, 14)
        core.src(cr, tim_lit)
        cr.fill()
        cr.rectangle(x - 26, y - 30, w + 52, 14)
        core.src(cr, tim)
        cr.fill()
        cr.rectangle(x, y, w, h)
        core.src(cr, "#1a0e18")
        cr.fill()
    for (cx, cy, w, h) in WIN_UP:
        cr.rectangle(cx - w / 2 - 14, cy - h / 2 - 14, w + 28, h + 28)
        core.src(cr, tim)
        cr.fill()
        cr.rectangle(cx - w / 2, cy - h / 2, w, h)
        core.src(cr, "#1a0e18")
        cr.fill()
    # ---- the door: a stone arch of voussoirs round a deep reveal
    st = "#4a4054"
    cr.new_path()
    _arch_path(cr, DOOR_CX, DOOR_TOP - 34, DOOR_W + 68, FAC_BASE - 2)
    core.src(cr, st)
    cr.fill()
    cr.save()
    cr.new_path()
    _arch_path(cr, DOOR_CX, DOOR_TOP - 34, DOOR_W + 68, FAC_BASE - 2)
    cr.clip()
    env.texture(cr, "stone", 0.3, 0.7)
    n = 13
    r0, r1 = DOOR_W / 2, DOOR_W / 2 + 34
    cyc = DOOR_SPRING
    core.src(cr, "#241e2c", 0.9)
    cr.set_line_width(2.6)
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        cr.move_to(DOOR_CX + math.cos(a) * r0, cyc + math.sin(a) * r0)
        cr.line_to(DOOR_CX + math.cos(a) * r1, cyc + math.sin(a) * r1)
    for yy in (cyc + 60, cyc + 130, cyc + 200, cyc + 270):
        for sx in (-1, 1):
            cr.move_to(DOOR_CX + sx * r0, yy)
            cr.line_to(DOOR_CX + sx * r1, yy)
    cr.stroke()
    _hot_wash(cr, DOOR_CX, DOOR_SPRING + 80, 200, 260, AMBER, 0.22)
    cr.restore()
    # keystone carved with a little tankard
    core.polygon(cr, [(DOOR_CX - 15, DOOR_TOP - 40), (DOOR_CX + 15, DOOR_TOP - 40), (DOOR_CX + 11, DOOR_TOP + 4), (DOOR_CX - 11, DOOR_TOP + 4)])
    core.src(cr, "#5a4e62")
    cr.fill()
    # the reveal (the opening's depth) -- the door leaf and its light are per frame
    cr.new_path()
    door_path(cr)
    core.src(cr, "#120a12")
    cr.fill()
    # ---- jetty: bressumer beam + carved brackets under the overhang, the overhang's shadow
    cr.rectangle(gx0 - 30, JETTY_Y, gx1 - gx0 + 60, 34)
    cr.set_source(core.linear(0, JETTY_Y, 0, JETTY_Y + 34, [core.alpha("#05050a", 0.6), core.alpha("#05050a", 0.0)]))
    cr.fill()
    _beam(cr, FAC_X0 - 40, JETTY_Y - 6, FAC_X1 + 20, JETTY_Y - 6, 30, tim, tim_lit, tim_dk)
    for px in posts[1:]:
        core.polygon(cr, [(px - 12, JETTY_Y + 8), (px + 12, JETTY_Y + 8), (px + 5, JETTY_Y + 44), (px - 5, JETTY_Y + 44)])
        core.src(cr, tim_dk)
        cr.fill()
    # ---- barrels stacked by the door (a tavern's honest clutter), lit hot from the window
    for (bx, by, r, lie) in ((1078.0, FAC_BASE + 4, 46.0, False), (1000.0, FAC_BASE + 8, 46.0, False), (1040.0, FAC_BASE - 84, 42.0, True)):
        _barrel(cr, bx, by, r, lie)
    # the corner post's stone quoins (the facade's left edge reads against the dark alley)
    for k in range(10):
        yy = JETTY_Y + 12 + k * 40
        if yy > FAC_BASE - 50:
            break
        core.rounded_rect(cr, FAC_X0 - 8, yy, 34 if k % 2 else 22, 36, 3)
        core.src(cr, "#3c3446")
        cr.fill()
    _night_falloff(cr)


def _night_falloff(cr):
    """It is night: the facade sinks into navy away from its lights (darker up toward the
    eaves and out toward the right), then the hot pools round the windows, the door and the
    lantern strings are lit back in (additive), so the light SOURCES carry the value."""
    x0, x1 = FAC_X0 - 70, FAC_X1 + 60
    cr.save()
    cr.rectangle(x0, -100, x1 - x0, FAC_BASE + 100)
    cr.clip()
    cr.rectangle(x0, -100, x1 - x0, FAC_BASE + 100)
    cr.set_source(core.linear(0, -100, 0, FAC_BASE, [(0.0, core.alpha("#080a1a", 0.78)), (0.35, core.alpha("#0a0c1e", 0.58)),
                                                     (0.62, core.alpha("#0c0c1e", 0.42)), (1.0, core.alpha("#0c0a18", 0.36))]))
    cr.fill()
    cr.rectangle(1820, -100, x1 - 1820, FAC_BASE + 100)
    cr.set_source(core.linear(1820, 0, x1, 0, [core.alpha("#070814", 0.0), core.alpha("#070814", 0.45)]))
    cr.fill()
    cr.set_operator(cairo.OPERATOR_ADD)
    for (x, y, w, h) in (WIN_L, WIN_R):
        _hot_wash(cr, x + w / 2, y + h / 2, w * 0.95, h * 1.35, "#7a1a48", 0.55)
        _hot_wash(cr, x + w / 2, y + h * 0.8, w * 0.7, h * 0.7, "#6a3410", 0.45)
    for (cx, cy, w, h) in WIN_UP:
        _hot_wash(cr, cx, cy, w * 1.05, h * 1.05, "#6a1640", 0.5)
    _hot_wash(cr, DOOR_CX, DOOR_SPRING + 120, 190, 250, "#5a2a10", 0.45)
    for k in range(13):                                  # under the lantern strings
        x = FAC_X0 + 40 + k * 128
        _hot_wash(cr, x, JETTY_Y + 64, 95, 60, "#6a2a3a" if k % 2 else "#5a3410", 0.45)
        _hot_wash(cr, x, EAVE_Y + 70, 90, 56, "#5a2040" if k % 2 else "#4a2e10", 0.4)
    cr.restore()


def _barrel(cr, x, base, r, lying=False):
    """A stout oak barrel standing at (x, base) (or lying on its side on top of others)."""
    oak, oak_dk, iron = "#6a4030", "#2e1a18", "#1c1a20"
    if lying:
        cr.save()
        cr.translate(x, base - r * 0.82)
        core.ellipse(cr, 0, 0, r * 1.25, r * 0.86)
        core.src(cr, oak)
        cr.fill()
        cr.set_source(core.linear(0, -r, 0, r, [core.alpha("#ff9a6a", 0.25), core.alpha("#000000", 0.0), core.alpha("#000000", 0.45)]))
        core.ellipse(cr, 0, 0, r * 1.25, r * 0.86)
        cr.fill()
        for ox in (-0.75, 0.75):
            cr.rectangle(r * ox - 3, -r * 0.84, 6, r * 1.68)
        core.src(cr, iron)
        cr.fill()
        core.ellipse(cr, r * 1.1, 0, r * 0.32, r * 0.78)
        core.src(cr, "#8a5a40")
        cr.fill()
        core.ellipse(cr, r * 1.1, 0, r * 0.2, r * 0.6)
        core.src(cr, "#5a3628")
        cr.fill()
        cr.restore()
        return
    h = r * 2.3
    cr.save()
    cr.translate(x, base)
    pts = [(-r * 0.86, 0), (-r, -h * 0.5), (-r * 0.86, -h), (r * 0.86, -h), (r, -h * 0.5), (r * 0.86, 0)]
    core.smooth_closed(cr, pts, 0.5)
    core.src(cr, oak)
    cr.fill()
    cr.save()
    core.smooth_closed(cr, pts, 0.5)
    cr.clip()
    cr.set_source(core.linear(-r, 0, r, 0, [core.alpha("#000000", 0.5), core.alpha("#000000", 0.0), core.alpha("#ff9a6a", 0.3)]))
    cr.paint()
    core.src(cr, oak_dk, 0.6)
    for k in (-0.55, -0.15, 0.25, 0.62):
        cr.rectangle(k * r - 1, -h, 2.0, h)
    cr.fill()
    core.src(cr, iron)
    for hy in (0.12, 0.42, 0.62, 0.9):
        cr.rectangle(-r * 1.1, -h * hy - 3, r * 2.2, 6)
    cr.fill()
    cr.restore()
    core.ellipse(cr, 0, -h, r * 0.86, r * 0.22)
    core.src(cr, "#7a4c36")
    cr.fill()
    cr.restore()


def draw_ext_street(cr):
    """The wet cobbled street in front of the tavern (after the rain), the gutter at the foot
    of the facade and the facade's contact shadow."""
    env.draw_cobbles(cr, -120, FAC_BASE, 2440, 1180, kind=EXT, seed=31, wet=True, size=(12.0, 52.0), contrast=1.1)
    cr.rectangle(-120, FAC_BASE, 2440, 26)
    cr.set_source(core.linear(0, FAC_BASE, 0, FAC_BASE + 26, [core.alpha("#05040a", 0.7), core.alpha("#05040a", 0.0)]))
    cr.fill()


def ext_lights():
    """Light sources on the facade for the wet-street reflections: (x, y, colour, level, base_y)."""
    out = []
    x, y, w, h = WIN_L
    for k in range(4):
        out.append((x + w * (0.15 + 0.23 * k), y + h * 0.5, HOT if k % 2 else AMBER, 0.85, FAC_BASE + 6))
    x, y, w, h = WIN_R
    for k in range(3):
        out.append((x + w * (0.2 + 0.3 * k), y + h * 0.5, HOT if k % 2 == 0 else AMBER, 0.8, FAC_BASE + 6))
    out.append((DOOR_CX, 650, AMBER, 0.55, FAC_BASE + 6))
    for k in range(12):
        out.append((560 + k * 140, JETTY_Y + 70, (HOT, AMBER, "#ff7a6a")[k % 3], 0.5, FAC_BASE + 6))
    return out


def draw_ext_reflections(cr):
    env.draw_wet_reflections(cr, ext_lights(), stretch=0.62, width=1.25, seed=5, alpha=1.15)


# ----------------------------------------------------------------------------------------
# the synchronized laugh (shared by the window silhouettes and the crowd inside)
# ----------------------------------------------------------------------------------------

LAUGH_BPM = 280.0          # one "HA" per beat (4.7 Hz), as ch.laugh_sync


def laugh_sync(t, t0=0.0):
    """0..1 HA pulse: identical for everyone who is given the same t (the uncanny part)."""
    ph = (t - t0) * LAUGH_BPM / 60.0
    u = ph - math.floor(ph)
    return math.sin(math.pi * min(1.0, u / 0.55)) ** 2 if u < 0.55 else 0.0


# ----------------------------------------------------------------------------------------
# exterior per-frame life: windows, door, lanterns, sign
# ----------------------------------------------------------------------------------------

_SIL_KINDS = ("goblin", "satyr", "dwarf", "minotaur", "elf", "goblin", "satyr", "dwarf")


def _silhouette(cr, x, base, s, kind, lp, k, color):
    """A patron's dark shape seen through the hot glass: head thrown back on each HA, tankard
    raised -- every one of them on exactly the same beat."""
    bob = -7.0 * lp * s
    tilt = -0.22 * lp
    cr.save()
    cr.translate(x, base)
    cr.scale(s, s)
    core.src(cr, color)
    # shoulders / body
    core.ellipse(cr, 0, -40, 38, 46)
    cr.fill()
    cr.save()
    cr.translate(0, -88 + bob / s)
    cr.rotate(tilt)
    hr = {"goblin": 22, "satyr": 21, "dwarf": 25, "minotaur": 28, "elf": 20}[kind]
    core.ellipse(cr, 0, 0, hr, hr * 1.1)
    cr.fill()
    if kind == "goblin":                       # big leaf ears
        for sx in (-1, 1):
            core.polygon(cr, [(sx * hr * 0.7, -6), (sx * (hr + 34), -22), (sx * hr * 0.8, 8)])
            cr.fill()
    elif kind == "elf":
        for sx in (-1, 1):
            core.polygon(cr, [(sx * hr * 0.7, -4), (sx * (hr + 22), -30), (sx * hr * 0.85, 6)])
            cr.fill()
    elif kind == "satyr":                      # curled horns
        cr.set_line_width(7)
        for sx in (-1, 1):
            cr.arc(sx * 14, -18, 12, math.pi if sx < 0 else -math.pi * 0.2, math.pi * 1.6 if sx < 0 else math.pi * 0.9)
            cr.stroke()
    elif kind == "minotaur":                   # wide horns
        for sx in (-1, 1):
            core.tapered(cr, [(sx * 18, -14), (sx * 44, -24), (sx * 52, -46)], 9.0, 2.0)
            cr.fill()
        core.ellipse(cr, 0, 16, 18, 12)
        cr.fill()
    elif kind == "dwarf":                      # the beard + a pointed hood
        core.polygon(cr, [(-18, 6), (18, 6), (0, 40)])
        cr.fill()
        core.polygon(cr, [(-20, -10), (20, -10), (6, -46)])
        cr.fill()
    # an open mouth (the laugh), a notch of light through the head
    if lp > 0.25:
        core.src(cr, HOT_PALE, 0.55 * lp)
        core.ellipse(cr, 6 if k % 2 else -6, 8, 5, 3 + 3 * lp)
        cr.fill()
    cr.restore()
    # the raised tankard arm (all on the same beat)
    core.src(cr, color)
    side = 1 if k % 2 else -1
    up = 0.55 + 0.45 * lp
    ax, ay = side * 30, -62
    hx, hy = side * (46 + 6 * up), -70 - 58 * up
    core.capsule(cr, ax, ay, 10, hx, hy, 8)
    cr.fill()
    core.rounded_rect(cr, hx - 13 + side * 6, hy - 30, 26, 32, 4)
    cr.fill()
    core.src(cr, HOT_PALE, 0.35)
    core.ellipse(cr, hx + side * 6, hy - 31, 13, 5)                    # foam catching the light
    cr.fill()
    cr.restore()


def draw_window_life(cr, rect, pulse, lp, seed=0, crowd=True, level=1.0, upper=False, skip=()):
    """One lit leaded window: the hot room glow (pulsing with the jig), the synchronized laughing
    silhouettes, then the leading and a cold glint of the street on the glass."""
    x, y, w, h = rect
    cr.save()
    cr.rectangle(x, y, w, h)
    cr.clip()
    k = level * (0.82 + 0.18 * min(1.2, pulse))
    top = core.mix("#3a0c2a", HOT, 0.75 * k)
    mid = core.mix("#4a1428", "#ff6a8a", 0.8 * k)
    bot = core.mix("#3a1a10", AMBER, 0.85 * k)
    cr.set_source(core.linear(0, y, 0, y + h, [top, mid, bot]))
    cr.paint()
    # deep in the room: a hot bloom of candle and lantern light
    fx.glow(cr, x + w * (0.35 + 0.3 * core.hash01(seed, 3)), y + h * 0.55, max(w, h) * 0.7, "#fff0c0", 0.35 * k, additive=True)
    if crowd:
        n = max(2, int(w / 72))
        sil = core.mix("#14060e", "#2a0a1a", 0.3)
        for i in range(n):
            if i in skip:
                continue
            u = (i + 0.5) / n
            kind = _SIL_KINDS[(i + seed) % len(_SIL_KINDS)]
            s = (0.52 if upper else 0.62) + 0.12 * core.hash01(i, seed + 11)
            sx = x + w * u + core.jitter(i, w * 0.04, seed)
            _silhouette(cr, sx, y + h + 26, s * h / 196.0, kind, lp, i, sil)
    # lead cames: a diamond lattice, mullion and transom
    cr.set_line_width(2.2)
    core.src(cr, "#1a0a12", 0.85)
    step = 26.0
    kx = -h
    while kx < w + h:
        cr.move_to(x + kx, y)
        cr.line_to(x + kx + h * 0.7, y + h)
        cr.move_to(x + kx, y + h)
        cr.line_to(x + kx + h * 0.7, y)
        kx += step
    cr.stroke()
    core.src(cr, "#1e0e14")
    cr.rectangle(x + w / 2 - 5, y, 10, h)
    cr.rectangle(x, y + h * 0.42 - 4, w, 8)
    if w > 220:
        cr.rectangle(x + w / 4 - 4, y, 8, h)
        cr.rectangle(x + 3 * w / 4 - 4, y, 8, h)
    cr.fill()
    # a cold sliver of the night street on the glass (top-left of each light)
    core.src(cr, COLD, 0.10)
    core.polygon(cr, [(x, y), (x + w * 0.3, y), (x, y + h * 0.5)])
    cr.fill()
    cr.restore()


def draw_ext_windows(cr, pulse, lp, level=1.0):
    # (its middle panes are kept clear: the stamp comes down on his hand in front of them)
    draw_window_life(cr, WIN_L, pulse, lp, seed=1, level=level, skip=(1, 2))
    draw_window_life(cr, WIN_R, pulse, lp, seed=4, level=level)
    for i, (cx, cy, w, h) in enumerate(WIN_UP):
        draw_window_life(cr, (cx - w / 2, cy - h / 2, w, h), pulse * 0.7, lp, seed=7 + i, level=0.78 * level,
                         crowd=i != 1, upper=True)


def draw_door_leaf(cr, open_k, pulse, inner=None):
    """The tavern's arched oak door, hinged on its left jamb and opening INWARD.

    open_k 0 = shut (light leaks round its edges and through the barred peep window) .. 1 = wide
    open (the leaf edge-on against the inner wall). inner(cr) paints whatever stands in the
    lit doorway (the room's glow is painted here first); it is drawn behind the leaf."""
    x0 = DOOR_CX - DOOR_W / 2
    gap = DOOR_W * (1.0 - math.cos(open_k * math.pi / 2))     # visible opening on the latch side
    hot = 0.85 + 0.15 * min(1.2, pulse)
    cr.save()
    door_path(cr)
    cr.clip()
    if open_k > 0.001:
        # the hall's light filling the open doorway
        cr.set_source(core.linear(0, DOOR_TOP, 0, FAC_BASE, [core.mix("#5a1040", HOT, 0.8 * hot),
                                                             core.mix("#6a2a20", "#ffb070", 0.9 * hot)]))
        cr.paint()
        fx.glow(cr, DOOR_CX + DOOR_W * 0.25, DOOR_SPRING + 60, 220, "#fff2d0", 0.5 * hot)
        if inner is not None:
            inner(cr)
    # the leaf: x from the hinge (left jamb) to x0 + (DOOR_W - gap), perspective-pinched as it swings
    lw_ = DOOR_W - gap
    if lw_ > 0.5:
        pinch = 26.0 * math.sin(open_k * math.pi / 2)              # the far edge recedes
        ex = x0 + lw_
        cr.new_path()
        cr.move_to(x0, FAC_BASE)
        cr.line_to(x0, DOOR_SPRING)
        cr.arc(DOOR_CX, DOOR_SPRING, DOOR_W / 2, math.pi, TAU)
        cr.line_to(x0 + DOOR_W, FAC_BASE)
        cr.close_path()
        cr.save()
        cr.clip()
        cr.new_path()
        core.polygon(cr, [(x0, DOOR_TOP - 10), (ex, DOOR_TOP - 10 + pinch), (ex, FAC_BASE - pinch * 0.4), (x0, FAC_BASE)])
        cr.clip()
        shade_k = 0.35 * math.sin(open_k * math.pi / 2)           # turned away from the street light
        oak = core.shade("#4a2a20", shade_k)
        cr.set_source(core.linear(x0, 0, x0 + DOOR_W, 0, [core.shade(oak, 0.35), oak, core.shade(oak, 0.2)]))
        cr.paint()
        cr.set_source(core.linear(0, DOOR_TOP, 0, FAC_BASE, [core.alpha("#ff7a9a", 0.22), core.alpha("#000000", 0.0),
                                                             core.alpha("#000000", 0.35)]))
        cr.paint()
        env.texture(cr, "wood", 0.35, 0.8, sx=0.3, sy=4.0)
        # planks
        core.src(cr, "#1e0f0c", 0.8)
        for k in range(1, 6):
            px = x0 + lw_ * k / 6
            cr.rectangle(px - 1.6, DOOR_TOP - 10, 3.2, FAC_BASE - DOOR_TOP + 10)
        cr.fill()
        # iron strap hinges with curled ends
        core.src(cr, "#17141a")
        for hy in (DOOR_SPRING + 30, FAC_BASE - 80):
            cr.rectangle(x0, hy - 6, lw_ * 0.8, 12)
            core.circle(cr, x0 + lw_ * 0.8, hy, 9)
        cr.fill()
        # the hot light round the leaf's edges and under it
        if open_k < 0.02:
            core.src(cr, "#ffb36a", 0.75 * hot)
            cr.rectangle(x0, FAC_BASE - 4, DOOR_W, 4)
            cr.fill()
            # the peep window: a barred square of hot light at head height
            px, py, ps = DOOR_CX + 10, DOOR_SPRING + 6, 34
            cr.rectangle(px - ps / 2 - 6, py - ps / 2 - 6, ps + 12, ps + 12)
            core.src(cr, "#21120e")
            cr.fill()
            cr.set_source(core.linear(0, py - ps / 2, 0, py + ps / 2, [core.mix("#5a1040", HOT, 0.85 * hot), core.mix("#5a2010", AMBER, hot)]))
            cr.rectangle(px - ps / 2, py - ps / 2, ps, ps)
            cr.fill()
            core.src(cr, "#140a0a")
            for k in (-1, 0, 1):
                cr.rectangle(px + k * 10 - 1.5, py - ps / 2, 3, ps)
            cr.fill()
            # the ring handle
            cr.set_line_width(4.0)
            core.src(cr, "#0e0c10")
            cr.arc(x0 + DOOR_W * 0.82, FAC_BASE - 190, 12, 0, TAU)
            cr.stroke()
        else:
            # the leaf's lit edge (thickness) on the latch side
            core.src(cr, "#ffb070", 0.55 * hot)
            cr.rectangle(ex - 5, DOOR_TOP - 10 + pinch, 5, FAC_BASE - DOOR_TOP - pinch * 1.4)
            cr.fill()
        cr.restore()
    cr.restore()
    if open_k < 0.02:
        # a hot hairline round the arch where the door meets the frame
        cr.save()
        cr.set_line_width(2.0)
        core.src(cr, "#ff9a6a", 0.55 * hot)
        cr.new_path()
        door_path(cr, inset=1.0)
        cr.stroke()
        cr.restore()


def draw_ext_lanterns(cr, t, light, flare=1.0):
    """The strings of candle-lit paper lanterns (returned for the light pass)."""
    out = []
    out += P.draw_lantern_string(cr, (FAC_X0 - 20, JETTY_Y + 4), (FAC_X1, JETTY_Y + 4), t, 1.05, light, n=14, sag=64,
                                 seed=1, palette="tavern", lit=flare)
    out += P.draw_lantern_string(cr, (FAC_X0 - 40, EAVE_Y + 22), (FAC_X1, EAVE_Y + 26), t, 1.0, light, n=14, sag=58,
                                 seed=5, palette="tavern", lit=flare)
    out += P.draw_lantern_string(cr, (FAC_X0 - 30, 300.0), (112.0, 262.0), t, 1.1, light, n=4, sag=62,
                                 seed=9, palette="tavern", lit=flare)
    return out


def draw_ext_sign(cr, t, light):
    return P.draw_hanging_sign(cr, SIGN_AT[0], SIGN_AT[1], kind="flagon", scale=1.32, light=light, t=t, side=-1, seed=3)


def door_spill(cr, door_open, pulse):
    """The open door's light thrown across the wet cobbles (drawn on the street, under the
    characters: it lights the ground, not the people standing in it)."""
    if door_open <= 0.001:
        return
    gap = DOOR_W * (1.0 - math.cos(door_open * math.pi / 2))
    gx = DOOR_CX - DOOR_W / 2 + DOOR_W - gap / 2
    k = min(1.0, gap / 50.0) * (0.85 + 0.15 * min(1.2, pulse))
    fx.light_shaft(cr, gx, FAC_BASE - 4, gx - 120, 1130, gap * 0.9, gap * 2.6 + 40, "#ffb070", 0.42 * k,
                   soft=3, fade_start=1.0, fade_end=0.9)
    fx.light_pool(cr, gx - 30, FAC_BASE + 50, 120 + gap * 0.8, 40, "#ff9a60", 0.35 * k)


def ext_light_pass(lc, pulse, lanterns, door_open=0.0, level=1.0):
    """Big soft light into the LightLayer: the windows' hot halos (pulsing), lantern halos,
    the door's spill on the wet street."""
    k = level * (0.75 + 0.25 * min(1.2, pulse))
    for (x, y, w, h) in (WIN_L, WIN_R):
        fx.glow(lc, x + w / 2, y + h / 2, w * 1.25, HOT, 0.32 * k)
        fx.glow(lc, x + w / 2, y + h * 0.7, w * 0.8, AMBER, 0.25 * k)
        fx.light_pool(lc, x + w / 2, FAC_BASE + 60, w * 0.9, 50, HOT, 0.25 * k)
    for (cx, cy, w, h) in WIN_UP:
        fx.glow(lc, cx, cy, w * 1.1, HOT, 0.22 * k)
    P.lantern_string_light(lc, lanterns, 1.05, 1.15)
    if door_open > 0.001:
        gap = DOOR_W * (1.0 - math.cos(door_open * math.pi / 2))
        gx = DOOR_CX - DOOR_W / 2 + DOOR_W - gap / 2
        fx.glow(lc, gx, DOOR_SPRING + 100, 260 + gap, AMBER, 0.45 * min(1.0, gap / 60.0))
    else:
        fx.glow(lc, DOOR_CX, FAC_BASE - 2, 140, AMBER, 0.18 * k)


# ----------------------------------------------------------------------------------------
# INTERIOR: the hall of THE MERRY FLAGON (shots INT_*). One-point perspective, eye level at
# HORIZON; a character standing on the floor at ground y has scale int_scale(y).
# ----------------------------------------------------------------------------------------

HORIZON = 400.0
VP = (960.0, HORIZON)
WALL_BASE = 690.0                     # where the back wall meets the floor
INT_DOOR_CX, INT_DOOR_W, INT_DOOR_TOP = 190.0, 212.0, 386.0
DAIS = (630.0, 1070.0, 744.0, 28.0)   # x0, x1, front edge y, height (px) -- the band's low stage
INT_LAYER = dict(x=-160.0, y=-110.0, w=2240.0, h=1300.0)
SC_REF, Y_REF = 0.72, 900.0


def int_scale(y):
    """Character scale for a ground point at screen y (the dragon: 0.72 at y 900)."""
    return SC_REF * (y - HORIZON) / (Y_REF - HORIZON)


def _int_door_path(cr, inset=0.0):
    _arch_path(cr, INT_DOOR_CX, INT_DOOR_TOP + inset, INT_DOOR_W - 2 * inset, WALL_BASE + 2, 0.0)


def draw_int_night(cr):
    """What the open door shows: the cold street outside, under the moon."""
    x0 = INT_DOOR_CX - INT_DOOR_W
    cr.rectangle(x0 - 40, INT_DOOR_TOP - 60, INT_DOOR_W * 2 + 80, WALL_BASE - INT_DOOR_TOP + 120)
    cr.set_source(core.linear(0, INT_DOOR_TOP - 60, 0, WALL_BASE + 60, ["#0a1028", "#16224a", "#1e2c52"]))
    cr.fill()
    # the house across the street: a dark timbered wall with one shuttered window
    cr.rectangle(x0 - 40, INT_DOOR_TOP + 30, INT_DOOR_W * 2 + 80, WALL_BASE - INT_DOOR_TOP - 10)
    core.src(cr, "#1a2240")
    cr.fill()
    core.src(cr, "#10162c")
    for bx in (INT_DOOR_CX - 70, INT_DOOR_CX + 40):
        cr.rectangle(bx, INT_DOOR_TOP + 30, 10, WALL_BASE - INT_DOOR_TOP)
    cr.rectangle(x0 - 40, INT_DOOR_TOP + 110, INT_DOOR_W * 2 + 80, 8)
    cr.fill()
    cr.rectangle(INT_DOOR_CX - 30, INT_DOOR_TOP + 140, 46, 60)
    core.src(cr, "#0c1022")
    cr.fill()
    # moonlit wet cobbles
    cr.rectangle(x0 - 40, WALL_BASE - 30, INT_DOOR_W * 2 + 80, 80)
    cr.set_source(core.linear(0, WALL_BASE - 30, 0, WALL_BASE + 20, ["#26355e", "#1a2444"]))
    cr.fill()
    core.src(cr, "#8fb0f0", 0.25)
    for k in range(14):
        cx = x0 + core.hash01(k, 3) * INT_DOOR_W * 2
        core.ellipse(cr, cx, WALL_BASE - 20 + core.hash01(k, 4) * 30, 6 + 6 * core.hash01(k, 5), 1.6)
        cr.fill()


def _bunting(cr, x0, y0, x1, y1, sag, n, seed, scale=1.0):
    """A swag of cloth pennants (hot magenta, amber, red, cream) on a cord."""
    cols = ("#c8336e", "#e0902a", "#b02a30", "#e8d2b0", "#8a2a6a")
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + sag * 4 * u * (1 - u)))
    cr.set_line_width(1.6 * scale)
    core.src(cr, "#2a1418")
    core.smooth_open(cr, pts)
    cr.stroke()
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        c = cols[(i + seed) % len(cols)]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        core.polygon(cr, [(ax + (bx - ax) * 0.08, ay + (by - ay) * 0.08), (bx - (bx - ax) * 0.08, by - (by - ay) * 0.08),
                          (mx + 2 * scale, my + 34 * scale)])
        core.src(cr, c)
        cr.fill()
        core.polygon(cr, [(mx, my), (bx - (bx - ax) * 0.08, by - (by - ay) * 0.08), (mx + 2 * scale, my + 34 * scale)])
        core.src(cr, "#000000", 0.22)
        cr.fill()


def _keg(cr, x, y, r, tap=True):
    """A keg lying on its rack, its round end toward us, a brass tap."""
    core.ellipse(cr, x, y, r * 1.0, r * 1.05)
    core.src(cr, "#5a3226")
    cr.fill()
    cr.set_line_width(r * 0.12)
    core.src(cr, "#1a1216")
    cr.arc(x, y, r * 0.92, 0, TAU)
    cr.stroke()
    cr.arc(x, y, r * 0.55, 0, TAU)
    cr.stroke()
    core.src(cr, "#ff9a6a", 0.18)
    core.ellipse(cr, x - r * 0.3, y - r * 0.35, r * 0.45, r * 0.3)
    cr.fill()
    if tap:
        core.src(cr, "#b8913f")
        cr.rectangle(x - r * 0.08, y + r * 0.35, r * 0.16, r * 0.5)
        cr.rectangle(x - r * 0.2, y + r * 0.78, r * 0.4, r * 0.12)
        cr.fill()


def draw_int_wall(cr):
    """The hall's back wall: lime plaster flushed hot by the room's lanterns, dark oak posts and
    rails, the open entrance door (left), the band's tapestry behind the dais, shelves of
    tankards and jugs, kegs on a rack, high windows on the cold night, bunting and the ceiling
    beams. Openings (the door, the windows) are cut out: the night layer shows through."""
    tim, tim_lit, tim_dk = "#2a1418", "#5a2e30", "#120808"
    top = -110.0
    # plaster with a hot gradient (bright low where the lanterns are, darker up into the roof)
    cr.rectangle(-160, top, 2240, WALL_BASE - top + 20)
    cr.set_source(core.linear(0, top, 0, WALL_BASE, [(0.0, "#1c0818"), (0.32, "#4a1638"), (0.72, "#7e2650"), (1.0, "#742a3c")]))
    cr.fill()
    # the colour structure of the room: cold by the door (left), magenta at the stage (centre),
    # amber over the long table (right)
    cr.rectangle(-160, top, 700, WALL_BASE - top + 20)
    cr.set_source(core.linear(-160, 0, 540, 0, [core.alpha("#1a2048", 0.55), core.alpha("#1a2048", 0.0)]))
    cr.fill()
    cr.save()
    cr.rectangle(-160, top, 2240, WALL_BASE - top + 20)
    cr.clip()
    env.texture(cr, "plaster", 0.22, 1.0)
    cr.set_operator(cairo.OPERATOR_ADD)
    for (x, y, rx, ry, c, a) in ((850, 560, 520, 300, "#7a1448", 0.8), (1480, 500, 520, 280, "#6a3a08", 0.75),
                                 (1850, 560, 380, 240, "#6a2a10", 0.55), (1150, 250, 900, 160, "#3a0a24", 0.5)):
        _hot_wash(cr, x, y, rx, ry, c, a)
    cr.restore()
    # the band's tapestry behind the dais: a magenta banner with a gold flagon
    bx0, bx1 = DAIS[0] + 30, DAIS[1] - 30
    core.polygon(cr, [(bx0, 330), (bx1, 330), (bx1, 640), ((bx0 + bx1) / 2 + 60, 668), ((bx0 + bx1) / 2 - 60, 668), (bx0, 640)])
    cr.set_source(core.linear(0, 330, 0, 668, ["#8a1a52", "#b02a66", "#7a1648"]))
    cr.fill()
    cr.save()
    core.polygon(cr, [(bx0, 330), (bx1, 330), (bx1, 640), ((bx0 + bx1) / 2 + 60, 668), ((bx0 + bx1) / 2 - 60, 668), (bx0, 640)])
    cr.clip()
    env.texture(cr, "paint", 0.3, 0.6)
    core.src(cr, "#000000", 0.25)
    for k in range(7):
        xx = bx0 + (bx1 - bx0) * (k + 0.5) / 7
        cr.rectangle(xx - 3, 330, 6, 340)
    cr.fill()
    cr.restore()
    _tapestry_shield(cr, (bx0 + bx1) / 2, 482, 1.0)
    # a gold-thread fringe along the banner's hem
    cr.save()
    cr.set_line_width(2.0)
    core.src(cr, "#8a6a30", 0.8)
    for k in range(int((bx1 - bx0) / 9)):
        xx = bx0 + 4 + k * 9
        yy = 640 if abs(xx - (bx0 + bx1) / 2) > 60 else 640 + 28 * (1 - abs(xx - (bx0 + bx1) / 2) / 60)
        cr.move_to(xx, yy)
        cr.line_to(xx + 1.0, yy + 12)
    cr.stroke()
    cr.restore()
    cr.rectangle(bx0 - 14, 318, bx1 - bx0 + 28, 16)
    core.src(cr, tim)
    cr.fill()
    # timber frame: posts, the mid rail, the wall plate
    for px in (-80.0, 420.0, 1150.0, 1560.0, 1990.0):
        _beam(cr, px, top, px, WALL_BASE, 30, tim, tim_lit, tim_dk)
    _beam(cr, -160, 300, 2080, 300, 22, tim, tim_lit, tim_dk)
    _beam(cr, -160, WALL_BASE - 14, 2080, WALL_BASE - 14, 26, tim, tim_lit, tim_dk)
    # high windows on the night (cut out below), with deep sills
    for (wx, wy, ww, wh) in INT_WINDOWS:
        cr.rectangle(wx - 12, wy - 12, ww + 24, wh + 24)
        core.src(cr, tim)
        cr.fill()
    # shelves of tankards and jugs over the long table
    for sy in (395.0, 470.0):
        cr.rectangle(1190, sy, 330, 10)
        core.src(cr, tim_lit)
        cr.fill()
        cr.rectangle(1190, sy + 10, 330, 6)
        core.src(cr, "#000000", 0.35)
        cr.fill()
        for k in range(10):
            tx = 1204 + k * 32
            if (k + int(sy)) % 4 == 3:
                core.ellipse(cr, tx + 8, sy - 16, 11, 15)               # a round jug
                core.src(cr, "#8a5a3a")
                cr.fill()
            else:
                core.rounded_rect(cr, tx, sy - 26, 18, 26, 2)          # a tankard
                core.src(cr, "#7a8088" if k % 2 else "#6a4030")
                cr.fill()
                core.ellipse(cr, tx + 9, sy - 26, 9, 3)
                core.src(cr, "#ffb0c8", 0.35)
                cr.fill()
    # kegs on a rack (right)
    cr.rectangle(1640, 600, 300, 16)
    core.src(cr, tim)
    cr.fill()
    for k, kx in enumerate((1690.0, 1785.0, 1880.0)):
        _keg(cr, kx, 560, 44)
    for k, kx in enumerate((1737.0, 1832.0)):
        _keg(cr, kx, 482, 42, tap=False)
    # bunting swags across the wall
    _bunting(cr, -100, 150, 900, 170, 70, 16, 1)
    _bunting(cr, 900, 170, 2080, 150, 80, 18, 3)
    _bunting(cr, 600, 300, 1560, 300, 46, 15, 5, 0.8)
    # the entrance: a deep arched oak frame (the opening is cut out for the night layer)
    cr.new_path()
    _arch_path(cr, INT_DOOR_CX, INT_DOOR_TOP - 26, INT_DOOR_W + 52, WALL_BASE + 2)
    core.src(cr, tim)
    cr.fill()
    # the ceiling: heavy beams and joists, dark
    cr.rectangle(-160, top, 2240, 130 - top)
    cr.set_source(core.linear(0, top, 0, 130, ["#0a0408", "#1a0a12"]))
    cr.fill()
    for k in range(-2, 16):
        jx = 960 + (k * 160 - 960) * 1.0
        core.polygon(cr, [(jx - 10, top), (jx + 10, top), (jx + 6, 130), (jx - 6, 130)])
        core.src(cr, "#241014")
        cr.fill()
    _beam(cr, -160, 118, 2080, 118, 34, tim, tim_lit, tim_dk)
    # cut the openings (door, windows) -- the night layer behind shows through
    cr.save()
    cr.set_operator(cairo.OPERATOR_CLEAR)
    cr.new_path()
    _int_door_path(cr)
    cr.fill()
    for (wx, wy, ww, wh) in INT_WINDOWS:
        cr.rectangle(wx, wy, ww, wh)
        cr.fill()
    cr.restore()
    # the open door leaf, swung in against the wall left of the opening
    lx = INT_DOOR_CX - INT_DOOR_W / 2
    core.polygon(cr, [(lx - 4, INT_DOOR_TOP + 40), (lx - 46, INT_DOOR_TOP + 18), (lx - 46, WALL_BASE + 14), (lx - 4, WALL_BASE + 2)])
    core.src(cr, "#3a2018")
    cr.fill()
    core.src(cr, "#140a08")
    for k in range(3):
        xx = lx - 8 - k * 12
        cr.rectangle(xx - 1, INT_DOOR_TOP + 30 - k * 6, 2, WALL_BASE - INT_DOOR_TOP - 20 + k * 8)
    cr.fill()


INT_WINDOWS = [(1300.0, 196.0, 92.0, 82.0), (1700.0, 196.0, 92.0, 82.0)]


def _tapestry_shield(cr, cx, cy, s):
    """The house arms embroidered on the band's banner: a heater shield, burgundy with a couched
    gold-thread border and a foaming flagon in ochre silk -- thread, not paint and not a lamp
    (its values stay well under the bloom threshold)."""
    w, h = 132.0 * s, 158.0 * s

    def shield(inset):
        x0, x1 = cx - w / 2 + inset, cx + w / 2 - inset
        y0 = cy - h / 2 + inset
        cr.new_path()
        cr.move_to(x0, y0)
        cr.line_to(x1, y0)
        cr.line_to(x1, cy + h * 0.08)
        cr.curve_to(x1, cy + h * 0.36 - inset * 0.5, cx + w * 0.22, cy + h * 0.46 - inset, cx, cy + h / 2 - inset * 1.2)
        cr.curve_to(cx - w * 0.22, cy + h * 0.46 - inset, x0, cy + h * 0.36 - inset * 0.5, x0, cy + h * 0.08)
        cr.close_path()

    shield(-5.0)
    core.src(cr, "#3a0a20", 0.55)                     # its shadow on the banner
    cr.fill()
    shield(0.0)
    core.src(cr, "#7a5222")                           # the gold-thread border (dull, couched)
    cr.fill()
    shield(7.0 * s)
    cr.set_source(core.linear(0, cy - h / 2, 0, cy + h / 2, ["#5e1030", "#4a0c26"]))
    cr.fill()
    cr.save()
    shield(7.0 * s)
    cr.clip()
    env.texture(cr, "paint", 0.25, 0.5)
    cr.restore()
    # the stitches along the border
    cr.save()
    shield(3.5 * s)
    cr.set_line_width(1.4)
    cr.set_dash([5.0, 4.0])
    core.src(cr, "#b08a48", 0.7)
    cr.stroke()
    cr.restore()
    # the flagon: ochre silk, a cream-wool head of foam, darker satin-stitch shading
    k = 2.2 * s
    tx, ty = cx - 4 * k, cy + 4 * k
    core.rounded_rect(cr, tx - 10 * k, ty - 8 * k, 20 * k, 22 * k, 3 * k)
    core.src(cr, "#a8783a")
    cr.fill()
    cr.set_line_width(3.4 * k)
    core.src(cr, "#a8783a")
    cr.arc(tx + 11 * k, ty + 3 * k, 6 * k, -math.pi / 2, math.pi / 2)
    cr.stroke()
    core.src(cr, "#6a4420", 0.8)
    for kk in (-1, 1):
        cr.rectangle(tx + kk * 5 * k - 0.8 * k, ty - 4 * k, 1.6 * k, 16 * k)
    cr.fill()
    core.blob(cr, tx, ty - 10 * k, 11.5 * k, 0.2, 7, seed=4, sy=0.55)
    core.src(cr, "#b8a68a")
    cr.fill()
    cr.set_line_width(1.2)
    core.src(cr, "#3a0a18", 0.6)
    core.rounded_rect(cr, tx - 10 * k, ty - 8 * k, 20 * k, 22 * k, 3 * k)
    cr.stroke()


def draw_int_window_glass(cr):
    """The high windows' leaded panes on the night (behind the wall layer)."""
    for (wx, wy, ww, wh) in INT_WINDOWS:
        cr.rectangle(wx, wy, ww, wh)
        cr.set_source(core.linear(0, wy, 0, wy + wh, ["#101a3a", "#1c2a52"]))
        cr.fill()
        cr.save()
        cr.rectangle(wx, wy, ww, wh)
        cr.clip()
        cr.set_line_width(1.6)
        core.src(cr, "#05060c", 0.8)
        k = -wh
        while k < ww + wh:
            cr.move_to(wx + k, wy)
            cr.line_to(wx + k + wh * 0.7, wy + wh)
            cr.move_to(wx + k, wy + wh)
            cr.line_to(wx + k + wh * 0.7, wy)
            k += 18
        cr.stroke()
        core.src(cr, "#9ab8ff", 0.2)
        core.polygon(cr, [(wx, wy), (wx + ww * 0.4, wy), (wx, wy + wh * 0.6)])
        cr.fill()
        cr.restore()


def draw_int_floor(cr):
    """Wide oak floorboards in one-point perspective toward VP, worn and polished, with the
    lanterns' hot light pooled on them and a dark skirting shadow along the wall."""
    y0, y1 = WALL_BASE - 6, 1200.0
    cr.rectangle(-160, y0, 2240, y1 - y0)
    cr.set_source(core.linear(0, y0, 0, y1, ["#3e1620", "#622a22", "#3c1a16"]))
    cr.fill()
    cr.save()
    cr.rectangle(-160, y0, 2240, y1 - y0)
    cr.clip()
    env.texture(cr, "wood", 0.25, 1.0, sx=0.2, sy=3.0)
    # boards converge to the vanishing point
    core.src(cr, "#1a0a0c", 0.75)
    cr.set_line_width(2.2)
    for k in range(-40, 41):
        xb = VP[0] + k * 120.0
        cr.move_to(VP[0] + (xb - VP[0]) * (y0 - HORIZON) / (y1 - HORIZON), y0)
        cr.line_to(xb, y1)
    cr.stroke()
    # butt joints, staggered, thinning with distance
    for row in range(26):
        yy = y0 + (y1 - y0) * (row / 26.0) ** 1.6
        d = (yy - HORIZON) / (y1 - HORIZON)
        for k in range(-40, 41):
            if (row + k) % 3:
                continue
            xb0 = VP[0] + k * 120.0 * d
            core.src(cr, "#1a0a0c", 0.5)
            cr.rectangle(xb0 + 120.0 * d * core.hash01(row * 97 + k, 3), yy, max(1.0, 2.0 * d), 0.0 + 60.0 * d)
            cr.fill()
    cr.set_operator(cairo.OPERATOR_ADD)
    for (x, y, rx, ry, c, a) in ((850, 790, 600, 130, "#7a1238", 0.75), (1480, 860, 620, 150, "#6a3a08", 0.8),
                                 (960, 1010, 1100, 180, "#4a0e22", 0.45)):
        _hot_wash(cr, x, y, rx, ry, c, a)
    cr.set_operator(cairo.OPERATOR_OVER)
    # the cold spill from the open door onto the boards
    cr.save()
    cr.translate(INT_DOOR_CX + 40, WALL_BASE + 70)
    cr.scale(1.0, 0.28)
    cr.set_source(core.radial(0, 0, 330, [(0.0, core.alpha("#3a5aa0", 0.5)), (1.0, core.alpha("#3a5aa0", 0.0))]))
    cr.arc(0, 0, 330, 0, TAU)
    cr.fill()
    cr.restore()
    cr.restore()
    cr.rectangle(-160, y0, 2240, 22)
    cr.set_source(core.linear(0, y0, 0, y0 + 22, [core.alpha("#050204", 0.75), core.alpha("#050204", 0.0)]))
    cr.fill()


def draw_int_dais(cr):
    """The band's low plank stage (behind the dragon, left of centre)."""
    x0, x1, fy, h = DAIS
    top = fy - h
    back = top - 18
    core.polygon(cr, [(x0 + 14, back), (x1 - 14, back), (x1, top), (x0, top)])
    core.src(cr, "#6a3428")
    cr.fill()
    cr.save()
    core.polygon(cr, [(x0 + 14, back), (x1 - 14, back), (x1, top), (x0, top)])
    cr.clip()
    env.texture(cr, "wood", 0.3, 0.8, sx=4.0, sy=0.25)
    cr.restore()
    cr.rectangle(x0, top, x1 - x0, h)
    core.src(cr, "#3a1a16")
    cr.fill()
    core.src(cr, "#1a0a0a", 0.8)
    for k in range(1, 9):
        cr.rectangle(x0 + (x1 - x0) * k / 9 - 1, top, 2, h)
    cr.fill()
    core.src(cr, "#ff8aa8", 0.25)
    cr.rectangle(x0, top, x1 - x0, 2.5)
    cr.fill()
    cr.rectangle(x0 - 10, fy, x1 - x0 + 20, 14)
    cr.set_source(core.linear(0, fy, 0, fy + 14, [core.alpha("#050204", 0.6), core.alpha("#050204", 0.0)]))
    cr.fill()


# ----------------------------------------------------------------------------------------
# INSERT: the back of his hand under the tavern's light, the fresh pink SMILE
# ----------------------------------------------------------------------------------------

INS_LIGHT = B.Light(key=(1.16, 0.82, 0.82), ambient=(0.34, 0.30, 0.50), rim=(0.62, 0.76, 1.0), rim_strength=0.8,
                    direction=(0.5, -0.86), rim_direction=(-0.75, 0.66), name="s4_insert")
INS_WRIST = (640.0, 548.0)
INS_ANGLE = -0.06                     # the fingers point right, a little up
INS_SIZE = 770.0                      # wrist -> fingertip
INS_PRINT = 0.25                      # where the print sits along the hand (hand lengths from the wrist)
INS_HAND_POSE = dict(curl=(0.13, 0.18, 0.25), spread=0.08, thumb=(-0.45, 0.12))   # between "back" and
                                      # "relaxed": the back of the hand flat to us, fingers a little fanned
INS_INK = "#d9407e"                   # the same pink ink, a touch deeper in the close-up (wet, on dark scales)


def draw_insert_bg(cr):
    """Out-of-focus night behind the hand: the tavern's lanterns and windows as soft discs."""
    cr.rectangle(-120, -90, 2160, 1260)
    cr.set_source(core.linear(0, -90, 0, 1170, ["#1a0c22", "#2a1030", "#140c1e", "#0a0a14"]))
    cr.fill()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(46):
        x = -100 + core.hash01(i, 71) * 2120
        y = -40 + core.hash01(i, 72) ** 1.5 * 700
        r = 26 + 70 * core.hash01(i, 73)
        c = (HOT, AMBER, "#ff7a6a", HOT_PALE, "#f07aa0")[i % 5]
        a = 0.10 + 0.22 * core.hash01(i, 74)
        g = core.radial(x, y, r, [(0.0, core.alpha(c, a)), (0.82, core.alpha(c, a * 0.85)), (1.0, core.alpha(c, 0.0))])
        cr.set_source(g)
        cr.arc(x, y, r, 0, TAU)
        cr.fill()
    for (x, y, rx, ry, c, a) in ((1500, 260, 520, 300, "#5a1838", 0.6), (400, 200, 420, 260, "#4a2a10", 0.45)):
        _hot_wash(cr, x, y, rx, ry, c, a)
    cr.set_operator(cairo.OPERATOR_OVER)
    # the wet street far below: dark navy cobbles carrying long smeared reflections of the
    # windows and lanterns (out of focus -- the layer is blurred hard)
    cr.rectangle(-120, 700, 2160, 470)
    cr.set_source(core.linear(0, 700, 0, 1170, ["#1a1028", "#0e0e1c", "#08080f"]))
    cr.fill()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(26):
        x = -60 + core.hash01(i, 81) * 2060
        c = (HOT, AMBER, "#ff7a6a", HOT_PALE)[i % 4]
        a = 0.10 + 0.16 * core.hash01(i, 82)
        w = 30 + 60 * core.hash01(i, 83)
        cr.rectangle(x - w / 2, 720, w, 420)
        cr.set_source(core.linear(0, 720, 0, 1140, [core.alpha(c, a), core.alpha(c, a * 0.5), core.alpha(c, 0.0)]))
        cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    for k in range(9):                                   # cobble rows (soft bands)
        yy = 740 + 46 * k * (1 + 0.12 * k)
        cr.rectangle(-120, yy, 2160, 6 + k)
        core.src(cr, "#000000", 0.35)
        cr.fill()


def _scales_detail():
    """back_detail for B.hand: overlapping scale scallops on the back of the hand and rings on
    the fingers (hand units), so the close-up reads as a dragon's scaly hand."""
    def cb(cr, kx, pw):
        from film.lib.characters import dragon as DR
        line = B.palette(INS_LIGHT, DR.dragon_mats()["scales"]).line
        cr.save()
        core.ellipse(cr, kx * 0.47, 0.0, kx * 0.62, pw * 0.98)
        cr.clip()
        cr.new_path()
        rows = 6
        for j in range(rows):
            yy = -pw * 0.9 + (j + 0.5) * (1.8 * pw / rows)
            r = 0.027 + 0.004 * (j % 2)
            for i in range(9):
                xx = -0.02 + i * 0.056 + (0.028 if j % 2 else 0.0)
                cr.move_to(xx - r, yy)
                cr.arc_negative(xx, yy, r, math.pi, 0.0)
        cr.set_line_width(0.0055)
        core.src(cr, line, 0.32)
        cr.stroke()
        cr.restore()
        # knuckle bumps + finger rings
        cr.save()
        cr.set_line_width(0.006)
        core.src(cr, line, 0.35)
        for k, yy in enumerate((-pw * 0.6, -pw * 0.05, pw * 0.55)):
            for dx in (0.07, 0.15):
                cr.move_to(kx + dx, yy - 0.032)
                cr.curve_to(kx + dx + 0.012, yy - 0.012, kx + dx + 0.012, yy + 0.012, kx + dx, yy + 0.032)
        cr.stroke()
        cr.restore()
    return cb


def _print_cb(ink, smudge, gloss, t, hand_size=None):
    """The SMILE print for the insert (same mark, seed and angle as P.smile_stamp so S5-S7's faint
    print matches), slightly smudged on one side, wet ink catching the light."""
    hs = INS_SIZE if hand_size is None else hand_size
    k = hs / 56.0                       # this hand vs the dragon's own (HAND_LEN 56)
    size = 0.52 * k * 0.92

    def cb(cr):
        x0 = (INS_PRINT - 0.21) * hs
        col = INS_INK
        if smudge > 0:
            P.draw_smile_mark(cr, x0 + 9.0, 7.0, size, -0.1, ink * 0.22 * smudge, 0, color=col)
            P.draw_smile_mark(cr, x0 + 3.0, 2.0, size * 1.01, -0.1, ink * 0.26 * smudge, 0, color=col)
        P.draw_smile_mark(cr, x0, 0.0, size, -0.1, ink * 0.9, 0, color=col)
        if gloss > 0.01:
            # wet ink: small specular dabs on the letters (the light catches them as they dry)
            for i in range(9):
                gx = x0 + (core.hash01(i, 5) - 0.5) * 64 * size * 0.8
                gy = (core.hash01(i, 6) - 0.5) * 30 * size * 0.5
                tw = 0.6 + 0.4 * math.sin(t * 3.0 + i)
                core.src(cr, "#fff0f6", 0.55 * gloss * tw)
                core.ellipse(cr, gx, gy, 6 + 6 * core.hash01(i, 7), 2.2, -0.1)
                cr.fill()
    return cb


_FIST_GRIP = {}


def _troll_stamp_big(cr, x, die_y, k):
    """The troll's stamp seen huge, IN HIS STONE FIST (as the rig holds it: the handle through the
    fist, the block and the inked die below it), his forearm reaching in from the top right:
    (x, die_y) = the middle of the die's face, k = troll units -> px."""
    from film.lib.characters import troll as TR
    L = INS_LIGHT.with_(exposure=0.7, key=(0.95, 0.82, 0.9))      # granite in the street's shadow, not a pale glove
    M = TR.troll_mats()
    fist = TR.FIST
    ang = math.pi / 2 + 0.22                 # the fingers point down (and a little back): the arm comes from above-right
    if "g" not in _FIST_GRIP:                # where B.hand puts the grip for a wrist at the origin (once)
        c = core.frame(4, 4)[1]
        hf = B.hand(c, 0.0, 0.0, ang, fist, "grip", M["stone"], L, 1.0, finger_w=1.35, finger_len=0.9, palm_w=1.25)
        _FIST_GRIP["g"] = (hf.x, hf.y)
    gx, gy = _FIST_GRIP["g"]
    die_dy = TR._stamp_die_y(fist)           # the die face hangs this far below the grip (upright stamp)
    cr.save()
    cr.translate(x, die_y)
    cr.scale(k, k)
    lw = 4.2 / k
    wx, wy = -gx, -die_dy - gy               # the wrist that puts the grip right above the die
    # the forearm: a stone capsule from off-frame (top right) down to the wrist, a moss patch
    ex, ey = wx + math.cos(ang + math.pi) * 150.0 + 60.0, wy + math.sin(ang + math.pi) * 150.0
    s_, o_ = B.tube_paths(cr, [(ex + 40.0, ey - 120.0), (ex, ey), (wx, wy)], [50.0, 46.0, 42.0], lw, samples=4, tension=0.7)
    B.shade(cr, s_, M["stone"], L, lw, outline=o_, size=110, rim=0.8)
    cr.save()
    s_.add(cr)
    cr.clip()
    core.blob(cr, ex - 18.0, ey + 40.0, 26.0, 0.25, 8, 5)
    core.src(cr, B.palette(L, M["moss"]).lit)
    cr.fill()
    cr.restore()

    def hold(c, f):
        TR.troll_stamp(c, f, L, ink=1.0, die_down=True)

    cr.push_group()
    B.hand(cr, wx, wy, ang, fist, "grip", M["stone"], L, lw, claw=None, show_palm=False, hold=hold,
           finger_w=1.35, finger_len=0.9, palm_w=1.25, detail=2)
    hand = cr.pop_group()
    cr.set_source(hand)
    cr.paint()
    # moss and darker flecks on the stone knuckles (masked to the fist, so they never spill)
    for (bx, by, br, col, a, sd) in ((wx + 30, wy + 26, 15, B.palette(L, M["moss"]).lit, 0.8, 3),
                                     (wx + 18, wy + 36, 8, B.palette(L, M["moss"]).lit, 0.7, 4),
                                     (wx - 14, wy + 70, 5, "#2a2630", 0.3, 7), (wx + 6, wy + 104, 4, "#2a2630", 0.28, 9),
                                     (wx + 36, wy + 88, 4.5, "#2a2630", 0.28, 11), (wx - 26, wy + 112, 3.5, "#2a2630", 0.25, 13)):
        cr.save()
        core.blob(cr, bx, by, br, 0.3, 7, sd)
        cr.clip()
        core.src(cr, col, a)
        cr.mask(hand)
        cr.restore()
    cr.restore()


def _light_hand(cr, hand, wx, wy, ang, pulse):
    """Light the drawn hand (a group pattern used as a mask): a hot magenta rim along its upper
    edges (the lanterns above), a soft amber key across the knuckles, a cool shadow underneath."""
    hot = 0.8 + 0.2 * min(1.2, pulse)
    # shadow under the hand (cool, darker toward its lower edge)
    cr.save()
    cr.set_source(core.linear(0, wy - 140, 0, wy + 130, [core.alpha("#0a0618", 0.0), core.alpha("#0a0618", 0.0),
                                                         core.alpha("#0a0618", 0.45)]))
    cr.mask(hand)
    cr.restore()
    # key: an amber-pink glow over the knuckles
    cr.save()
    kx, ky = wx + math.cos(ang) * INS_SIZE * 0.45, wy - 60
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source(core.radial(kx, ky, 520, [(0.0, core.alpha("#ff8a7a", 0.22 * hot)), (1.0, core.alpha("#ff8a7a", 0.0))]))
    cr.mask(hand)
    cr.restore()
    # rim: the hand's alpha minus itself shifted down a few px = a band along the top edges
    cr.save()
    cr.push_group()
    cr.set_source(hand)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_DEST_OUT)
    cr.translate(-3.0, 9.0)
    cr.set_source(hand)
    cr.paint()
    rim = cr.pop_group()
    cr.restore()
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    core.src(cr, "#ff6aa6", 0.42 * hot)
    cr.mask(rim)
    cr.restore()


def draw_insert(cr, t, u, pulse, st):
    """The insert, local u 0..1. A slow push toward the print; the stamp's block lifts off out of
    frame at the start (motion-blurred), the wet ink glints, the music's light pulses on the
    skin, and his fingers curl in a little as he takes it in."""
    from film.lib.characters import dragon as DR
    M = DR.dragon_mats()
    zoom = 1.0 + 0.07 * core.inout_sine(u)
    px, py = INS_WRIST[0] + math.cos(INS_ANGLE) * INS_SIZE * INS_PRINT, INS_WRIST[1] + math.sin(INS_ANGLE) * INS_SIZE * INS_PRINT
    drift = (6.0 * core.noise1(t * 0.6, 3), 4.0 * core.noise1(t * 0.5, 4))
    cr.save()
    cr.translate(px, py)
    cr.scale(zoom, zoom)
    cr.translate(-px + drift[0], -py + drift[1])
    st["ins_bg"].paint(cr)
    L = INS_LIGHT.with_(exposure=0.96 + 0.07 * min(1.2, pulse))
    breathe = 0.012 * math.sin(t * 1.4)
    ang = INS_ANGLE + breathe
    wx, wy = INS_WRIST[0], INS_WRIST[1] + 6.0 * math.sin(t * 1.4 + 0.5)
    # the coat sleeve and the plum cuff
    lw = 4.2
    sx0, sy0 = wx - math.cos(ang) * 760, wy - math.sin(ang) * 760 + 160
    sl, so = B.tube_paths(cr, [(sx0, sy0), (wx - math.cos(ang) * 300, wy - math.sin(ang) * 300 + 40), (wx - 40, wy)],
                          [150.0, 132.0, 118.0], lw, samples=5, tension=0.7)
    B.shade(cr, sl, M["coat"], L, lw, outline=so, size=420)
    # the coat's wool catches the hot rim along its top
    cr.save()
    sl.add(cr)
    cr.clip()
    cr.set_source(core.linear(0, wy - 150, 0, wy + 60, [core.alpha("#ff5aa0", 0.22), core.alpha("#ff5aa0", 0.0)]))
    cr.paint()
    cr.restore()
    cs, co = B.ellipse_paths(cr, wx - 30, wy, 62.0, 124.0, lw, ang)
    B.shade(cr, cs, M["lining"], L, lw, outline=co, size=80, rim=0.6)
    curl = 0.16 * core.ramp(u, 0.55, 0.95, "inout_sine")
    ink = 0.95
    gloss = 1.0 - core.ramp(u, 0.15, 0.9)
    # the hand goes into a group so the scene's light can touch it (the rig's hands carry no rim)
    cr.push_group()
    B.hand(cr, wx, wy, ang, INS_SIZE, INS_HAND_POSE, M["scales"], L, lw, flip=False, claw=DR.DRAGON_COLORS["claw"],
           claw_len=0.08, pad=DR.DRAGON_COLORS["belly"], show_palm=False, finger_w=1.05, curl_add=curl, detail=2,
           back_detail=_scales_detail())
    hand = cr.pop_group()
    cr.set_source(hand)
    cr.paint()
    _light_hand(cr, hand, wx, wy, ang, pulse)
    # the print goes on AFTER the light (ink is matte and dark-ish: it must not glow like a sign);
    # same frame as base.hand's stamp callback (the back of the hand, x along the fingers)
    cr.save()
    cr.translate(wx + math.cos(ang) * 0.21 * INS_SIZE, wy + math.sin(ang) * 0.21 * INS_SIZE)
    cr.rotate(ang)
    _print_cb(ink, 1.0, gloss, t)(cr)
    cr.restore()
    # the troll's stone fist and his stamp lifting off the hand and out of the top of frame
    # (first ~0.35 s, accelerating): drawn with two trailing ghosts for motion blur
    # (it starts pressed onto the hand, hiding the print, and peels away: in_cubic)
    lift = core.ramp(u, 0.0, 0.16, "in_cubic")
    if lift < 1.0:
        for k, a in ((2, 0.18), (1, 0.4), (0, 1.0)):
            if k > 0 and lift < 0.05 * k + 0.02:
                continue                       # no motion trail while it is still pressed down
            yy = py + 96.0 - 1500.0 * max(0.0, lift - 0.05 * k)
            cr.save()
            cr.push_group()
            _troll_stamp_big(cr, px + 4.0, yy, 6.2)
            cr.pop_group_to_source()
            cr.paint_with_alpha(a)
            cr.restore()
    cr.restore()


# ----------------------------------------------------------------------------------------
# the POV close-up (INT_C): he reads the back of his own hand; the room laughs on, out of focus
# ----------------------------------------------------------------------------------------

POV_LIGHT = B.Light(key=(1.12, 0.80, 0.84), ambient=(0.36, 0.28, 0.44), rim=(1.0, 0.55, 0.78), rim_strength=0.7,
                    direction=(0.55, -0.83), rim_direction=(0.8, -0.6), name="s4_pov")
POV_WRIST = (640.0, 780.0)
POV_ANGLE = -0.30                      # the fingers point away (toward the room), a little up: the word reads
POV_SIZE = 700.0


def draw_hand_pov(cr, t, u, pulse):
    """His own forearm up from the bottom of frame, the back of the hand toward him (and us), SMILE
    big and readable -- the ink dry now, a little smudged. It rises into place (the cut is on the
    action), hangs there with a small tremor, and the fingers slowly curl in."""
    from film.lib.characters import dragon as DR
    M = DR.dragon_mats()
    L = POV_LIGHT.with_(exposure=0.95 + 0.06 * min(1.2, pulse))
    rise = core.out_cubic(core.clamp(u / 0.22, 0.0, 1.0))
    trem = 2.2 * math.sin(t * 13.0) * math.sin(t * 2.1)
    ang = POV_ANGLE + 0.012 * math.sin(t * 1.6) + 0.06 * (1.0 - rise)
    wx = POV_WRIST[0] - 40.0 * (1.0 - rise)
    wy = POV_WRIST[1] + 190.0 * (1.0 - rise) + trem
    lw = 4.0
    # the coat sleeve from the bottom-left corner, the plum cuff
    ca, sa = math.cos(ang), math.sin(ang)
    sl, so = B.tube_paths(cr, [(wx - ca * 720 - 120, wy - sa * 720 + 260), (wx - ca * 300, wy - sa * 300 + 30), (wx - ca * 36, wy - sa * 36)],
                          [150.0, 128.0, 112.0], lw, samples=5, tension=0.7)
    B.shade(cr, sl, M["coat"], L, lw, outline=so, size=420)
    cr.save()
    sl.add(cr)
    cr.clip()
    cr.set_source(core.linear(wx + 200, wy - 200, wx - 300, wy + 300, [core.alpha("#ff6aa6", 0.22), core.alpha("#ff6aa6", 0.0)]))
    cr.paint()
    cr.restore()
    cs, co = B.ellipse_paths(cr, wx - ca * 28, wy - sa * 28, 58.0, 116.0, lw, ang)
    B.shade(cr, cs, M["lining"], L, lw, outline=co, size=80, rim=0.6)
    curl = 0.05 + 0.22 * core.ramp(u, 0.45, 0.95, "inout_sine")
    cr.push_group()
    B.hand(cr, wx, wy, ang, POV_SIZE, INS_HAND_POSE, M["scales"], L, lw, flip=False, claw=DR.DRAGON_COLORS["claw"],
           claw_len=0.08, pad=DR.DRAGON_COLORS["belly"], show_palm=False, finger_w=1.05, curl_add=curl, detail=2,
           back_detail=_scales_detail())
    hand = cr.pop_group()
    cr.set_source(hand)
    cr.paint()
    _light_hand(cr, hand, wx, wy, ang, pulse)
    cr.save()
    cr.translate(wx + ca * 0.21 * POV_SIZE, wy + sa * 0.21 * POV_SIZE)
    cr.rotate(ang)
    _print_cb(0.92, 1.0, 0.0, t, POV_SIZE)(cr)
    cr.restore()
