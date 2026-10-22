"""s1_washhouse.py -- SCENE 1: THE WASH-HOUSE (late night).  "Self-service."

THE IDEA. Numb, cold isolation in a place full of motion and empty of contact. The wash-house is
built like a church: a long vaulted nave in strict one-point perspective, an arcade of stone piers
marching away on both sides, and in every bay a pair of enchanted tumbling drums (oak barrels on
cradles, brass lids, glass portholes) toed in toward the aisle like pews -- every one tumbling a
stranger's laundry, colourful and rumbling, with nobody there. The aisle runs to one tall black
arched window with the moon in it. Symmetry and repetition are the machine; one hunched dragon on
a milking stool far too small for him is the thing that breaks it. Across the aisle, an elf who is
beautiful and completely closed: hood up, sea-shells humming in her ears, face lit by her mirror.
The empty, moonlit aisle between them is the subject of the opening -- the gap.

BUILD. A 2.5D set in true perspective (Cam3): camera-facing planes (end wall, pier faces, ribs,
characters, plaque) are drawn in their own reference coordinates; receding surfaces (floor,
aisle walls, pier sides, arcade spandrels, the drums' barrels) are projected every frame, so
dollies, trucks and cranes all have real parallax. The drums' bodies are projected here; their
portholes are the props kit's, mapped onto each lid's plane. Depth of field: everything deeper
than the actors is drawn into a reduced-resolution buffer (soft), the near piers and the
foreground basket/tub into an even softer one; the focus band (the actors, his drum, the pier
with the plaque) is drawn at full resolution. Times below are the current timeline values; the
code derives every one of them from timeline.json beats and lines.

SHOT A -- 0.0 -> 8.55 (T_CUT_INSERT = s1_tap + 0.25)   WIDE, dolly-in + crane-down
  s1_fadein (0-1): fade up from black on a room already in motion -- drums tumbling, wisps
  buzzing and dipping in their iron cages, dust turning in the moon shaft. High camera, looking
  down the nave: the dragon left of centre on the stool beside HIS drum (body 3/4 left, watching
  its porthole), the elf right of centre on a plank form under the SELF-SERVICE plaque. A lone
  striped stocking lies in the moonlit aisle between them. Framing: near piers (dark, soft) at
  both edges, a wicker laundry basket bottom-left and an oak wash-tub with a beetle-paddle bottom-
  right (soft foreground), receding arches overhead, the moon window as the far focal point.
  Eye-trace: the lit gap -> the dragon (porthole light pooled round his stool, rim light) -> the
  elf's mirror glow -> the plaque. Slow push 0 -> 8.5: dolly in 560, crane down 210 to eye level.
  ~2.4-3.6: he shifts his weight on the tiny stool (it wobbles and creaks).
  s1_glance (5.5): THOUGHT -> GLANCE: eyes flick to her first (0.14 s), the head follows over
  0.4 s; 6.25 a deliberate blink (the decision); 6.45-7.15 BREATH: he swivels round on the stool
  to face her, straightening (hunch eases); s1_lean (7.0): leans in (ease-out), one hand lifts
  off his knee palm-up -- "may I...", brows up, wings lift a little in hope, the mouth opens and
  STAYS open: nothing comes out. Hold on the open mouth.
SHOT B -- 8.55 -> 11.0 (s1_tap.end)   INSERT, cut on her reach
  The elf and the plaque, tight. Her eyes never leave the mirror (runes scrolling, thumb idling).
  Her far hand comes up over her shoulder: tap (9.02), tap (9.42) -- the board jolts and rocks
  on its nail each time -- then the finger simply stays there, pointing, while she keeps
  scrolling. SELF-SERVICE large and legible in uncial lettering; the nave soft behind her.
SHOT C -- 11.0 -> 25.0   MEDIUM on him (eye level, long lens), then a drift, then the pull-back
  Cut back: he is still looking up at the sign, mouth closed, hand back on his knee.
  s1_l1 (11.80) "Self-service." -- read flatly, a fact, not a joke; tired lids, the wings sink
  all the way down over the line. A blink. (She lowers her hand off-screen.)
  12.8-13.5: his gaze drops from the sign to his own drum; the body turns back toward it.
  s1_lookaround (13.5-18.0): from his drum his EYES travel the row -- the next drum, the next,
  little saccades -- and the head follows, drum after drum, all the way down the nave toward the
  moon; the body opens to the room last. The camera drifts the same way, pulling back and
  panning right until the nave and both rows of spinning drums fill the frame beside him, and
  the oblivious elf and her sign come back into frame on the right.
  s1_l2 (18.50) "That's the whole city, isn't it." -- said in near-profile, looking down the
  rows, quiet; a tiny head-shake on "isn't it". Camera holds (only a breath of drift).
  s1_hold (21.0-25): his gaze sinks; T_SIGH (21.35) a long sigh -- shoulders drop, eyes close,
  head bows -- and a little curl of grey smoke rises from his nostrils and hangs in the air. He
  turns back to his drum. The camera pulls back and cranes up from 21.8 until he is small among
  the spinning drums, the nave and the moon as at the start; it settles ~0.5 s before the cut.
  Hard cut to S2.

COLOUR / VALUE. Sickly cold teal-green (wisps, portholes), blue-white moonlight, blue-black vault.
His mustard scarf is the one warm note (his key light is near-neutral so it stays mustard);
brass and oak sit under a darker, colder set light and the haze. Brightest values: the moon
window (far), the portholes, the wisps, her mirror -- each placed to frame a face; the far hall
is held down by a vignette-like wash so the actors carry the frame. Haze gathers toward the
vanishing point. Grain + teal-black vignette on every frame.

PERIOD. Romanesque vault, coursed stone, leaded night windows, caged will-o'-wisps on chains, oak-
and-brass drums with runes, a wicker basket, an oak tub and beetle, a plank form, a milking
stool, a painted wooden plaque on a nail, a darned woollen stocking. Nothing modern on screen.
"""


import math

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B

SCENE = 1
W, H = core.W, core.H
TAU = math.tau

# ----------------------------------------------------------------------------------------
# timing: everything derives from timeline.json beats and lines
# ----------------------------------------------------------------------------------------
DUR = tl.scene(SCENE).duration
_FADE = tl.beat("s1_fadein")
T_FADE0, T_FADE1 = _FADE.t, (_FADE.end if _FADE.end is not None else _FADE.t + 1.0)
T_GLANCE = tl.beat("s1_glance").t
T_LEAN = tl.beat("s1_lean").t
_TAP = tl.beat("s1_tap")
T_TAP = _TAP.t
T_TAP_END = _TAP.end if _TAP.end is not None else T_TAP + 2.7
_LOOK = tl.beat("s1_lookaround")
T_LOOK0 = _LOOK.t
T_LOOK1 = _LOOK.end if _LOOK.end is not None else T_LOOK0 + 4.5
T_HOLD = tl.beat("s1_hold").t
L1 = tl.line("s1_l1")
L2 = tl.line("s1_l2")

T_SWIVEL0, T_SWIVEL1 = T_GLANCE + 0.95, T_LEAN + 0.15   # he turns on the stool toward her
T_CUT_INSERT = T_TAP + 0.25          # cut on her reach
T_CUT_BACK = T_TAP_END               # back to him, still looking up at the sign
T_REACH0, T_REACH1 = T_TAP, T_TAP + 0.5
T_HIT1 = T_TAP + 0.72                # finger contacts
T_HIT2 = T_HIT1 + 0.40
T_REST = T_HIT2 + 0.42               # ...and the finger stays on the board
T_SIGH = T_HOLD + 0.35

# ----------------------------------------------------------------------------------------
# the hall in 3D (units = px at scale 1.0; X right, h up from the floor, z away from camera)
# Planes facing the camera are drawn in REFERENCE coordinates (the screen at the reference
# camera) with scale s = F / z; receding surfaces are projected point by point every frame.
# ----------------------------------------------------------------------------------------
PX, PY = 960.0, 520.0               # principal point (= vanishing point of the reference view)
F = 1000.0                          # focal length (px)
HC = 540.0                          # reference eye height above the floor

NAVE = 560.0                        # inner faces of the arcade piers (X = +-NAVE)
PIER_W, PIER_D = 230.0, 170.0       # pier front-face width (X) and depth (z)
PIER_Z = [760.0 + 900.0 * k for k in range(6)]          # 760 1660 2560 3460 4360 5260
WALL_Z = 5760.0                     # the nave's end wall
AISLE_X = 1420.0                    # outer walls of the side aisles
ARC_SPRING = 760.0                  # arcade arches spring here (their crowns reach ~1125)
VAULT_H = 1300.0                    # transverse ribs spring here (pier tops)
LID_X = 600.0                       # drum lids sit just inside the arcade line
TOE = math.radians(24.0)            # drums toed in toward the aisle (and the camera)
BARREL = 190.0
DRUM_R, DRUM_AXLE = 92.0, 130.0
BAY_DRUMS = [-185.0, 185.0]         # two drums per bay, around the bay centre (z)

# the cast and their props
Z_DRAGON, X_DRAGON = 1300.0, -335.0
Z_ELF, X_ELF = 1560.0, 432.0
STOOL_H = 72.0
HIS_BAY, HIS_SLOT = 0, 1            # his drum: left side, bay 0, the far one of the pair
Z_PLAQUE = PIER_Z[1] - PIER_D / 2.0  # the plaque hangs on pier 1's front face (right)
X_PLAQUE, H_NAIL = NAVE + PIER_W / 2.0 - 10.0, 448.0
SOCK = (55.0, 1760.0)               # (X, z) one lost stocking on the aisle floor
LAMPS = [(-150.0, 900.0, 1250.0, 0), (0.0, 980.0, 2110.0, 1), (0.0, 1010.0, 3010.0, 2),
         (0.0, 1030.0, 3910.0, 3), (0.0, 1040.0, 4810.0, 4)]          # (X, h, z, seed)
Z_FOCUS_NEAR, Z_FOCUS_FAR = 1120.0, 1900.0   # what is drawn sharp (full res)

# lights
L_BASE = ch.LIGHTS["washhouse"]
L_DRAGON = L_BASE.with_(key=(0.9, 0.99, 0.95), rim=(0.70, 0.88, 1.0), rim_strength=0.8, direction=(-0.7, -0.6),
                        rim_direction=(0.55, -0.83))
L_ELF = L_BASE.with_(rim=(0.70, 0.88, 1.0), rim_strength=0.7, rim_direction=(-0.5, -0.86))
L_SET = L_BASE.with_(key=(0.62, 0.84, 0.86), ambient=(0.2, 0.32, 0.36), rim_strength=0.3)
_C0 = C = {
    "stone": "#2c4a4a", "stone_lt": "#3d6260", "stone_dk": "#152727", "mortar": "#0b1717",
    "vault": "#0a1415", "aisle": "#0d1a1b", "haze": "#3a6c68", "moon_glow": "#a9c4f0",
    "shaft": "#9cc4ff", "wisp": "#4dffc4", "porthole": "#5fe8d0", "mirror": "#5fe0ff",
    "oak": "#5a4a36", "oak_dk": "#2a2218", "oak_lt": "#7a6a50", "brass": "#8a7d48",
    "vig": (0.0, 0.025, 0.035),
}


# ----------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------

class Cam3:
    """Translation (x, y, z) in 3D units (y = down, so +y lowers the camera), zoom (focal
    multiplier), pan (sx, sy): a small rotation applied as a uniform screen shift."""
    __slots__ = ("x", "y", "z", "zoom", "sx", "sy")

    def __init__(self, x=0.0, y=0.0, z=0.0, zoom=1.0, sx=0.0, sy=0.0):
        self.x, self.y, self.z, self.zoom, self.sx, self.sy = x, y, z, zoom, sx, sy

    def k(self, z):
        return self.zoom * F / max(1.0, z - self.z)

    def p(self, X, h, z):
        """3D point -> screen."""
        k = self.k(z)
        return (PX + self.sx + (X - self.x) * k, PY + self.sy + (HC - h - self.y) * k)

    def matrix(self, z):
        """Reference coordinates of the camera-facing plane at depth z -> screen."""
        s = F / z
        k = self.k(z)
        m = k / s
        return cairo.Matrix(m, 0, 0, m, PX + self.sx - PX * m - self.x * k, PY + self.sy - PY * m - self.y * k)

    def mag(self, z):
        return self.k(z) * z / F

    def eye(self):
        return (self.x, HC - self.y, self.z)

    def vp(self):
        return (PX + self.sx, PY + self.sy)


def ref(X, h, z):
    """3D point -> reference coordinates of its camera-facing plane."""
    s = F / z
    return (PX + X * s, PY + (HC - h) * s)


class plane:
    """`with plane(cr, cam, z) as s:` -- draw in the reference coords of the plane at depth z."""

    def __init__(self, cr, cam, z):
        self.cr, self.m, self.s = cr, cam.matrix(z), F / z

    def __enter__(self):
        self.cr.save()
        self.cr.transform(self.m)
        return self.s

    def __exit__(self, *a):
        self.cr.restore()


def _framed(cx, cy, cz, zoom, aim, at):
    """A camera whose pan puts the 3D point `aim` (X, h, z) at screen point `at`."""
    c = Cam3(cx, cy, cz, zoom)
    x, y = c.p(*aim)
    c.sx, c.sy = at[0] - x, at[1] - y
    return c


def _cam_keys(t, keys):
    """keys: [(t, (cx, cy, cz, zoom, aimX, aimH, aimZ, atx, aty)[, ease])] -> Cam3."""
    v = core.track(t, keys)
    return _framed(v[0], v[1], v[2], v[3], (v[4], v[5], v[6]), (v[7], v[8]))


_MID = (0.5 * (X_DRAGON + X_ELF), 300.0, 0.5 * (Z_DRAGON + Z_ELF))
SHOT_A = [(0.0, (0.0, -40.0, 0.0, 1.0) + _MID + (960.0, 560.0)),
          (T_CUT_INSERT, (-40.0, 170.0, 560.0, 1.0) + (_MID[0] - 40.0, 260.0, _MID[2]) + (960.0, 560.0), "inout_sine")]
SHOT_B = [(T_CUT_INSERT, (300.0, 205.0, 1100.0, 1.0, X_ELF + 70.0, 395.0, Z_ELF, 905.0, 540.0)),
          (T_CUT_BACK, (300.0, 205.0, 1122.0, 1.0, X_ELF + 70.0, 397.0, Z_ELF, 905.0, 540.0), "inout_sine")]
_HEAD = (X_DRAGON + 20.0, 245.0, Z_DRAGON)
_MED = (-250.0, 285.0, 830.0, 1.0) + _HEAD + (1010.0, 455.0)
_MED2 = (-252.0, 285.0, 845.0, 1.0) + _HEAD + (1006.0, 452.0)
_LOOKED = (-150.0, 245.0, 672.0, 1.0) + _HEAD + (486.0, 470.0)
_LINE2 = (-149.0, 244.0, 688.0, 1.0) + _HEAD + (488.0, 468.0)
_WIDE_END = (0.0, -95.0, -40.0, 1.0) + _MID + (960.0, 590.0)
SHOT_C = [(T_CUT_BACK, _MED),
          (L1.end + 0.5, _MED2, "inout_sine"),
          (T_LOOK1 + 0.2, _LOOKED, "inout_sine"),
          (T_SIGH + 0.45, _LINE2, "inout_sine"),
          (DUR - 0.55, _WIDE_END, "inout_sine")]


def camera(t):
    if t < T_CUT_INSERT:
        return _cam_keys(t, SHOT_A), "A"
    if t < T_CUT_BACK:
        return _cam_keys(t, SHOT_B), "B"
    return _cam_keys(t, SHOT_C), "C"


# ----------------------------------------------------------------------------------------
# helpers: projected polygons
# ----------------------------------------------------------------------------------------

def _poly(cr, cam, pts3, color, alpha=None):
    core.polygon(cr, [cam.p(*q) for q in pts3])
    core.src(cr, color, alpha)
    cr.fill()


def _quad_x(cam, X, h0, h1, z0, z1):
    """A rectangle in the plane X = const (a receding wall)."""
    return [cam.p(X, h0, z0), cam.p(X, h0, z1), cam.p(X, h1, z1), cam.p(X, h1, z0)]


def _visible(cam, P3, N):
    e = cam.eye()
    return (e[0] - P3[0]) * N[0] + (e[1] - P3[1]) * N[1] + (e[2] - P3[2]) * N[2] > 0.0


# ----------------------------------------------------------------------------------------
# static art: the end wall (cached, in its plane)
# ----------------------------------------------------------------------------------------

def _night(c, x, y, w, h, moon=None):
    c.set_source(core.linear(0, y, 0, y + h, ["#16304e", "#0d1e34", "#0c1b2a"]))
    c.paint()
    for i in range(10):
        core.src(c, "#d8e6ff", 0.25 + 0.45 * core.hash01(i, 7))
        core.circle(c, x + core.hash01(i, 5) * w, y + core.hash01(i, 6) * h * 0.6, 0.5 + 0.6 * core.hash01(i, 8))
        c.fill()
    if moon:
        mx, my, mr = moon
        fx.glow(c, mx, my, mr * 8.0, C["moon_glow"], 0.6)
        core.src(c, "#f0f5ff")
        core.circle(c, mx, my, mr)
        c.fill()
        core.src(c, "#b6c6e6", 0.55)
        for k in range(3):
            core.circle(c, mx - mr * 0.32 + k * mr * 0.27, my + mr * (0.12 - 0.16 * k), mr * (0.17 + 0.05 * k))
        c.fill()


def _leading(c, cx, sill, w, h, lw=1.2):
    core.src(c, "#060f16", 0.95)
    c.rectangle(cx - lw * 1.6, sill - h, lw * 3.2, h)
    for k in range(1, 7):
        c.rectangle(cx - w / 2, sill - h + w / 2 + k * (h - w / 2) / 7 - lw, w, lw * 2)
    c.fill()
    c.save()
    c.set_line_width(lw * 0.5)
    core.src(c, "#08141c", 0.5)
    st = w / 4.0
    for k in range(-16, 16):
        c.move_to(cx - w / 2 + k * st, sill)
        c.line_to(cx - w / 2 + k * st + h * 0.45, sill - h)
        c.move_to(cx + w / 2 - k * st, sill)
        c.line_to(cx + w / 2 - k * st - h * 0.45, sill - h)
    c.stroke()
    c.restore()


def _draw_end_wall(c):
    """The far end of the nave and its side aisles (plane WALL_Z, reference coords)."""
    z = WALL_Z
    s = F / z
    x0, y0 = ref(-AISLE_X - 400, 0.0, z)
    x1, ytop = ref(AISLE_X + 400, 2400.0, z)
    yfl = ref(0, 0, z)[1]
    env.draw_stone_wall(c, x0, ytop, x1 - x0, yfl - ytop + 1, kind="washhouse", seed=6, block=(70 * s, 38 * s),
                        texture_alpha=0.12, light_top=0.03, variation=0.08, color=C["stone"])
    # the nave window: tall, arched, the moon in it
    cx = PX
    sill = ref(0, 330.0, z)[1]
    ww, wh = 520.0 * s, 1180.0 * s
    moon = (cx + 34 * s, sill - wh + 300 * s, 34 * s)

    def fill(cc):
        _night(cc, cx - ww / 2, sill - wh, ww, wh, moon)
        _leading(cc, cx, sill, ww, wh, 1.0)

    env.draw_arch(c, cx, sill, ww, wh, "washhouse", fill=fill, depth=60 * s, seed=4, color=C["stone_lt"])
    core.src(c, "#2e5050")
    c.rectangle(cx - ww / 2 - 30 * s, sill, ww + 60 * s, 26 * s)
    c.fill()
    # the side-aisle end windows (smaller, no moon)
    for sd in (-1, 1):
        ax = PX + sd * (NAVE + (AISLE_X - NAVE) * 0.5) * s
        asill = ref(0, 300.0, z)[1]

        def afill(cc, ax=ax, asill=asill):
            _night(cc, ax - 130 * s, asill - 560 * s, 260 * s, 560 * s)
            _leading(cc, ax, asill, 260 * s, 560 * s, 0.8)

        env.draw_arch(c, ax, asill, 260 * s, 560 * s, "washhouse", fill=afill, depth=40 * s, seed=8 + sd)
    # the nave's vault meets the end wall: a big blind arch over everything
    c.set_line_width(70 * s)
    core.src(c, C["stone_dk"], 0.9)
    vx, vy = ref(0, VAULT_H, z)
    c.arc(vx, vy, NAVE * s, math.pi, TAU)
    c.stroke()
    # the arcade line meets the end wall: dark half-piers
    for sd in (-1, 1):
        a = ref(sd * NAVE, 0, z)
        b = ref(sd * (NAVE + PIER_W), VAULT_H, z)
        c.rectangle(min(a[0], b[0]), b[1], abs(b[0] - a[0]), a[1] - b[1])
        core.src(c, C["stone_dk"])
        c.fill()
    # darkness in the vault and the aisles
    c.rectangle(x0, ytop, x1 - x0, yfl - ytop)
    c.set_source(core.linear(0, ytop, 0, yfl, [(0.0, core.alpha("#020707", 0.95)), (0.3, core.alpha("#020707", 0.55)),
                                                (0.55, core.alpha("#020707", 0.08)), (1.0, core.alpha("#020707", 0.25))]))
    c.fill()
    # the window again on top, so the moon stays the one clean bright thing at the end
    env.draw_arch(c, cx, sill, ww, wh, "washhouse", fill=fill, depth=60 * s, seed=4, color=C["stone_lt"])


def _draw_basket(c):
    """Foreground wicker laundry basket (drawn at the origin = its ground centre, 1 unit = 1 px at
    scale 1; it is painted soft and dark, a framing silhouette with cold light on its rim)."""
    w, h = 300.0, 230.0
    c.set_source(core.linear(0, -h, 0, 40, ["#2c2e22", "#17170f", "#0b0b07"]))
    core.rounded_rect(c, -w / 2, -h, w, h + 60, 40)
    c.fill()
    c.set_line_width(7)
    for k in range(9):
        yy = -h + 18 + k * 26
        core.src(c, "#060604", 0.65)
        c.move_to(-w / 2 + 12, yy)
        c.curve_to(-w / 4, yy + 9, w / 4, yy - 9, w / 2 - 12, yy)
        c.stroke()
    core.src(c, "#5fa89c", 0.35)                         # cold light along the rim
    c.set_line_width(6)
    c.move_to(-w / 2 + 20, -h + 4)
    c.curve_to(-w / 6, -h - 6, w / 6, -h - 6, w / 2 - 20, -h + 4)
    c.stroke()
    for k, col in enumerate(("#6e5a5a", "#9a9a8c", "#4a5e74")):
        core.src(c, core.mix(col, "#0e1c1c", 0.68))
        core.blob(c, -90 + k * 82, -h - 8 + 10 * math.sin(k * 2.3), 58, 0.35, 7, seed=k + 3)
        c.fill()
    core.src(c, core.mix("#9a9a8c", "#0e1c1c", 0.68))     # a shirt-sleeve hanging over the side
    core.tapered(c, [(118, -h + 6), (146, -h + 60), (138, -h + 120)], 36, 28)
    c.fill()


def _draw_tub(c):
    """Foreground oak wash-tub with a laundry beetle (paddle) leaning in it (ground centre at origin)."""
    w, h = 300.0, 170.0
    c.set_source(core.linear(-w / 2, 0, w / 2, 0, ["#1c1810", "#2e2618", "#120f0a"]))
    c.move_to(-w / 2, -h)
    c.line_to(w / 2, -h)
    c.line_to(w / 2 - 22, 0)
    c.line_to(-w / 2 + 22, 0)
    c.close_path()
    c.fill()
    for yy in (-h + 26, -38.0):                           # iron hoops
        core.src(c, "#0a0a0a", 0.8)
        c.rectangle(-w / 2 + 4, yy, w - 8, 12)
        c.fill()
    core.src(c, "#0e1a1a")
    core.ellipse(c, 0, -h, w / 2, 26)
    c.fill()
    core.src(c, "#3c6a64", 0.35)
    core.ellipse(c, 6, -h + 4, w / 2 - 22, 16)
    c.fill()
    # the beetle: a flat oak paddle leaning out of the tub
    c.save()
    c.translate(60, -h + 10)
    c.rotate(0.38)
    core.src(c, "#2a2216")
    core.rounded_rect(c, -14, -260, 28, 150, 10)
    c.fill()
    core.rounded_rect(c, -36, -120, 72, 130, 18)
    c.fill()
    core.src(c, "#5fa89c", 0.25)
    c.rectangle(-14, -258, 5, 140)
    c.fill()
    c.restore()


FG_PIECES = [("basket", -660.0, 830.0), ("tub", 690.0, 880.0)]      # (layer, X, z) on the floor


_TEX = {}


def _build_pier_textures(res=1.5):
    """Dressed stone for the piers' camera-facing faces (PIER_W x VAULT_H units), two variants."""
    out = []
    for seed in (11, 23):
        w, h = int(PIER_W * res) + 1, int(VAULT_H * res) + 1
        surf = core.new_surface(w, h)
        c = core.new_context(surf)
        c.scale(res, res)
        env.draw_stone_wall(c, 0, 0, PIER_W, VAULT_H, kind="washhouse", seed=seed, block=(96.0, 52.0),
                            color=_C0["stone"], texture_alpha=0.18, light_top=0.04, variation=0.11)
        surf.flush()
        out.append((surf, res))
    return out


# ----------------------------------------------------------------------------------------
# live architecture (projected every frame)
# ----------------------------------------------------------------------------------------

def _vault_backdrop(cr, cam):
    """Everything above the arcade: dark stone fading into black (painted first)."""
    cr.save()
    cr.rectangle(-20, -20, W + 40, H + 40)
    cr.set_source(core.linear(0, cam.p(0, 2000, WALL_Z)[1], 0, cam.p(0, 0, WALL_Z)[1],
                              ["#020707", "#081314", "#0f1f20"]))
    cr.fill()
    cr.restore()


ROW_D = 150.0                         # flagstone courses (z)


def _row_joints(r):
    """Deterministic, staggered joint positions (X) for flagstone course r."""
    xs, x = [], -AISLE_X - 120.0 * core.hash01(r, 91)
    i = 0
    while x < AISLE_X:
        xs.append(x)
        x += 120.0 + 120.0 * core.hash01(r * 37 + i, 92)
        i += 1
    xs.append(x)
    return xs


ROWS = {r: _row_joints(r) for r in range(0, 48)}


def _aisles_and_floor(cr, cam):
    """Side-aisle outer walls and ceilings, then the flagstone floor (painted after the end wall)."""
    z0, z1 = max(cam.z + 60.0, 200.0), WALL_Z
    for sd in (-1, 1):
        X = sd * AISLE_X
        q = _quad_x(cam, X, 0.0, 1180.0, z0, z1)
        core.polygon(cr, q)
        cr.set_source(core.linear(q[0][0], 0, q[1][0], 0, ["#0d1c1d", "#0a1617"]))
        cr.fill()
        _poly(cr, cam, [(sd * NAVE, 1180.0, z0), (sd * NAVE, 1180.0, z1), (X, 1180.0, z1), (X, 1180.0, z0)], "#060d0e")
    # the floor: a cold base, darker toward us, damp and moonlit down the aisle
    yh = cam.p(0, 0, WALL_Z)[1]
    yb = H + 60
    cr.save()
    cr.rectangle(-20, yh, W + 40, yb - yh)
    cr.set_source(core.linear(0, yh, 0, yb, ["#1e3536", "#172b2c", "#0e1c1d", "#091213"]))
    cr.fill()
    a0, a1 = cam.p(-230, 0, WALL_Z), cam.p(230, 0, WALL_Z)
    b0, b1 = cam.p(-470, 0, z0 + 400), cam.p(470, 0, z0 + 400)
    core.polygon(cr, [a0, a1, b1, b0])
    cr.set_source(core.linear(0, a0[1], 0, b0[1], [core.alpha("#8ab4d4", 0.16), core.alpha("#8ab4d4", 0.06),
                                                    core.alpha("#8ab4d4", 0.0)]))
    cr.fill()
    # staggered flagstones: per-stone tone, then the joints as thin projected quads
    rows = []
    r = 0
    while True:
        za = 300.0 + r * ROW_D
        if za >= WALL_Z or r >= 48:
            break
        zb = min(WALL_Z, za + ROW_D)
        if zb > z0:
            rows.append((r, max(za, z0), zb))
        r += 1
    tone_lt, tone_dk = [], []
    for r, za, zb in rows:
        if cam.k(zb) < 0.16:
            continue
        xs = ROWS[r]
        for i in range(len(xs) - 1):
            v = core.hash01(r * 53 + i, 93)
            if 0.3 < v < 0.72:
                continue
            q = [cam.p(xs[i], 0, za), cam.p(xs[i + 1], 0, za), cam.p(xs[i + 1], 0, zb), cam.p(xs[i], 0, zb)]
            if max(p[0] for p in q) < -20 or min(p[0] for p in q) > W + 20 or q[0][1] > H + 20:
                continue
            (tone_lt if v >= 0.72 else tone_dk).append(q)
    for qs, col, a in ((tone_lt, "#4f7a78", 0.07), (tone_dk, "#000000", 0.14)):
        for q in qs:
            core.polygon(cr, q)
        core.src(cr, col, a)
        cr.fill()
    for lo, hi, a in ((2600.0, 99999.0, 0.32), (1600.0, 2600.0, 0.45), (0.0, 1600.0, 0.55)):
        for r, za, zb in rows:
            if not (lo <= za < hi):
                continue
            jw = 3.2
            q = [cam.p(-AISLE_X, 0, za - jw), cam.p(AISLE_X, 0, za - jw), cam.p(AISLE_X, 0, za + jw), cam.p(-AISLE_X, 0, za + jw)]
            core.polygon(cr, q)
            for X in ROWS[r]:
                core.polygon(cr, [cam.p(X - jw, 0, za), cam.p(X + jw, 0, za), cam.p(X + jw, 0, zb), cam.p(X - jw, 0, zb)])
        core.src(cr, "#030808", a)
        cr.fill()
    cr.restore()


def _pier(cr, cam, side, zc, near=False):
    """One arcade pier: its inner (aisle-facing) side, then its camera-facing front, the impost
    band at the arcade springing, the plinth. near=True: a dark foreground silhouette."""
    zf, zb = zc - PIER_D / 2.0, zc + PIER_D / 2.0
    xi, xo = side * NAVE, side * (NAVE + PIER_W)
    e = cam.eye()
    dk = 0.62 if near else 0.0
    C = {k: (core.shade(v, dk) if isinstance(v, str) and k.startswith("stone") else v) for k, v in _C0.items()}
    # inner face (toward the aisle): lit by the lamps down the middle
    if (e[0] - xi) * (-side) > 0:
        q = _quad_x(cam, xi, 0.0, VAULT_H, zf, zb)
        core.polygon(cr, q)
        cr.set_source(core.linear(0, q[2][1], 0, q[0][1], [C["stone_dk"], C["stone_lt"], C["stone"]]))
        cr.fill()
        cr.set_line_width(max(0.6, 1.2 * cam.k(zc)))
        core.src(cr, C["mortar"], 0.5)
        hh = 64.0
        while hh < VAULT_H:
            a, b = cam.p(xi, hh, zf), cam.p(xi, hh, zb)
            cr.move_to(*a)
            cr.line_to(*b)
            hh += 64.0
        cr.stroke()
    # front face (toward the camera): a plane at zf, dressed with the cached stone texture
    with plane(cr, cam, zf) as s:
        (ax, ay), (bx, by) = ref(xi, 0.0, zf), ref(xo, VAULT_H, zf)
        x0, x1 = min(ax, bx), max(ax, bx)
        tex = _TEX.get("pier")
        cr.save()
        cr.rectangle(x0, by, x1 - x0, ay - by)
        cr.clip()
        if tex is not None:
            surf, res = tex[int(abs(zc) / 900.0) % len(tex)]
            cr.translate(x0, by)
            cr.scale(s / res, s / res)
            if side < 0:
                cr.translate(PIER_W * res, 0)
                cr.scale(-1, 1)
            cr.set_source_surface(surf, 0, 0)
            cr.get_source().set_filter(cairo.FILTER_BILINEAR)
            cr.paint()
            cr.restore()
            cr.save()
            cr.rectangle(x0, by, x1 - x0, ay - by)
            cr.clip()
        # light: the inner edge catches the lamps down the aisle, the outer edge falls into shadow
        stops = [(0.0, core.alpha("#7fd8c8", 0.10)), (0.25, core.alpha("#000000", 0.0)), (1.0, core.alpha("#000000", 0.55))]
        if side < 0:
            stops = [(0.0, core.alpha("#000000", 0.55)), (0.75, core.alpha("#000000", 0.0)), (1.0, core.alpha("#7fd8c8", 0.10))]
        cr.set_source(core.linear(x0, 0, x1, 0, stops))
        cr.paint()
        cr.set_source(core.linear(0, by, 0, ay, [core.alpha("#000000", 0.55), core.alpha("#000000", 0.0),
                                                 core.alpha("#000000", 0.0), core.alpha("#000000", 0.25)]))
        cr.paint()
        if near:
            core.src(cr, "#010404", 0.62)
            cr.paint()
        cr.restore()
        # impost band at the arcade springing and the plinth
        for hh, th, col in ((ARC_SPRING, 34.0, C["stone_lt"]), (0.0, 52.0, C["stone_dk"])):
            p0 = ref(xi - side * 14.0, hh + th, zf)
            p1 = ref(xo + side * 14.0, hh, zf)
            cr.rectangle(min(p0[0], p1[0]), p0[1], abs(p1[0] - p0[0]), p1[1] - p0[1])
            core.src(cr, col)
            cr.fill()
            cr.rectangle(min(p0[0], p1[0]), p1[1] - 4 * s, abs(p1[0] - p0[0]), 4 * s)
            core.src(cr, "#000000", 0.35)
            cr.fill()
        B.contact_shadow(cr, (ax + bx) / 2, ay + 2 * s, abs(bx - ax) * 0.8, 16 * s, alpha=0.45)


def _arcade(cr, cam, side, za, zb):
    """The arch between two piers (in the plane X = side*NAVE) and the wall above it up to the
    vault, as one projected shape; the voussoir band along the curve."""
    X = side * NAVE
    zc, r = 0.5 * (za + zb), 0.5 * (zb - za)
    n = 14
    curve = []
    for i in range(n + 1):
        a = math.pi * i / n
        curve.append((X, ARC_SPRING + math.sin(a) * r, zc - math.cos(a) * r))
    top = [(X, VAULT_H, zb), (X, VAULT_H, za)]
    core.polygon(cr, [cam.p(*q) for q in curve + top])
    core.src(cr, C["stone"])
    cr.fill()
    # voussoirs: a lighter band just above the intrados
    inner = [cam.p(X, ARC_SPRING + math.sin(math.pi * i / n) * r, zc - math.cos(math.pi * i / n) * r) for i in range(n + 1)]
    outer = [cam.p(X, ARC_SPRING + math.sin(math.pi * i / n) * (r + 46), zc - math.cos(math.pi * i / n) * (r + 46))
             for i in range(n, -1, -1)]
    core.polygon(cr, inner + outer)
    core.src(cr, C["stone_lt"], 0.75)
    cr.fill()
    # the soffit shadow line
    cr.set_line_width(max(0.6, 2.0 * cam.k(zc)))
    core.src(cr, "#050c0c", 0.7)
    cr.move_to(*inner[0])
    for p in inner[1:]:
        cr.line_to(*p)
    cr.stroke()


def _rib(cr, cam, zc):
    """The transverse rib springing from a pier pair, across the nave (camera-facing plane)."""
    zf = zc - PIER_D / 2.0
    with plane(cr, cam, zf) as s:
        cx, cy = ref(0.0, VAULT_H, zf)
        R = NAVE * s
        cr.new_path()
        cr.arc(cx, cy, R + 60 * s, math.pi, TAU)
        cr.arc_negative(cx, cy, R, TAU, math.pi)
        cr.close_path()
        cr.set_source(core.linear(0, cy - R - 60 * s, 0, cy, [C["stone_dk"], C["stone"]]))
        cr.fill()
        cr.set_line_width(5 * s)
        core.src(cr, C["stone_lt"], 0.4)
        cr.arc(cx, cy, R + 4 * s, math.pi * 1.05, math.pi * 1.95)
        cr.stroke()


def _side_drum(cr, cam, side, z, t, seed, speed=1.0, glow=1.0, light=L_SET, rumble=1.0):
    """An enchanted drum in a bay of the arcade, its lid toed in toward the aisle and the camera.
    The body is projected here (true perspective); the porthole -- brass ring, runes, glass,
    someone's laundry tumbling -- is the props kit's, mapped onto the lid's plane."""
    ct, st_ = math.cos(TOE), math.sin(TOE)
    n_lid = (-side * ct, 0.0, -st_)                  # outward normal of the lid (left row faces +X)
    u_dir = (-side * st_, 0.0, ct)                   # along the lid, deeper into the hall
    jx = rumble * 0.9 * core.noise1(t * 21.0, seed)
    jy = rumble * 0.7 * core.noise1(t * 24.0, seed + 9)
    Cl = (side * LID_X + jx, DRUM_AXLE + jy, z)
    Cb = (Cl[0] - n_lid[0] * BARREL, Cl[1], Cl[2] - n_lid[2] * BARREL)
    k = cam.k(z)
    oak = C["oak"]
    e = cam.eye()

    def ring(c0, r, m=20):
        out = []
        for i in range(m):
            a = TAU * i / m
            ca, sa = math.cos(a), math.sin(a)
            out.append(((c0[0] + sa * r * u_dir[0], c0[1] + ca * r, c0[2] + sa * r * u_dir[2]), ca, sa))
        return out

    def pp(q):
        return cam.p(*q)

    # cradle: two A-frames across the barrel, and a contact shadow
    for f in (0.18, 0.82):
        cx_, cz_ = Cl[0] - n_lid[0] * BARREL * f, Cl[2] - n_lid[2] * BARREL * f
        for sg in (-1.0, 1.0):
            top_u, foot_u = 0.38 * DRUM_R * sg, 0.95 * DRUM_R * sg
            quad = [(cx_ + u_dir[0] * top_u - 5 * n_lid[0], DRUM_AXLE - 0.62 * DRUM_R, cz_ + u_dir[2] * top_u),
                    (cx_ + u_dir[0] * (top_u + 14 * sg) - 5 * n_lid[0], DRUM_AXLE - 0.55 * DRUM_R, cz_ + u_dir[2] * (top_u + 14 * sg)),
                    (cx_ + u_dir[0] * (foot_u + 8 * sg), 0.0, cz_ + u_dir[2] * (foot_u + 8 * sg)),
                    (cx_ + u_dir[0] * (foot_u - 6 * sg), 0.0, cz_ + u_dir[2] * (foot_u - 6 * sg))]
            core.polygon(cr, [pp(q) for q in quad])
            core.src(cr, C["oak_dk"])
            cr.fill()
    g0 = pp((0.5 * (Cl[0] + Cb[0]), 0.0, 0.5 * (Cl[2] + Cb[2])))
    B.contact_shadow(cr, g0[0], g0[1], 150 * k, 22 * k, alpha=0.5)
    # barrel body
    lid_ring = ring(Cl, DRUM_R)
    back_ring = ring(Cb, DRUM_R * 0.93)
    hull = core.convex_hull([pp(q[0]) for q in lid_ring + back_ring])
    core.polygon(cr, hull)
    core.src(cr, oak)
    cr.fill()
    cr.save()
    core.polygon(cr, hull)
    cr.clip()
    # underside in shadow, a rim of cold light on top
    ylo = pp((Cl[0], DRUM_AXLE - 0.25 * DRUM_R, Cl[2]))[1]
    cr.rectangle(-50, ylo, W + 100, H)
    core.src(cr, C["oak_dk"], 0.75)
    cr.fill()
    rot = t * TAU * 0.3 * speed + seed
    cr.set_line_width(max(0.6, 2.0 * k))
    core.src(cr, "#140f08", 0.7)
    for i in range(18):
        a = rot + TAU * i / 18
        ca, sa = math.cos(a), math.sin(a)
        p0 = (Cl[0] + sa * DRUM_R * u_dir[0], Cl[1] + ca * DRUM_R, Cl[2] + sa * DRUM_R * u_dir[2])
        nrm = (sa * u_dir[0], ca, sa * u_dir[2])
        if (e[0] - p0[0]) * nrm[0] + (e[1] - p0[1]) * nrm[1] + (e[2] - p0[2]) * nrm[2] <= 0:
            continue
        p1 = (Cb[0] + sa * DRUM_R * 0.93 * u_dir[0], Cb[1] + ca * DRUM_R * 0.93, Cb[2] + sa * DRUM_R * 0.93 * u_dir[2])
        cr.move_to(*pp(p0))
        cr.line_to(*pp(p1))
    cr.stroke()
    # brass hoops (visible arcs)
    for f in (0.28, 0.74):
        c0 = (Cl[0] - n_lid[0] * BARREL * f, Cl[1], Cl[2] - n_lid[2] * BARREL * f)
        pts = ring(c0, DRUM_R * (1.0 - 0.07 * f), 24)
        vis = [_visible(cam, q, (sa * u_dir[0], ca, sa * u_dir[2])) for q, ca, sa in pts]
        cr.set_line_width(max(0.8, 7.0 * k))
        core.src(cr, "#3a3218")
        for i in range(24):
            if vis[i] and vis[(i + 1) % 24]:
                cr.move_to(*pp(pts[i][0]))
                cr.line_to(*pp(pts[(i + 1) % 24][0]))
        cr.stroke()
        cr.set_line_width(max(0.5, 3.2 * k))
        core.src(cr, C["brass"])
        for i in range(24):
            if vis[i] and vis[(i + 1) % 24]:
                cr.move_to(*pp(pts[i][0]))
                cr.line_to(*pp(pts[(i + 1) % 24][0]))
        cr.stroke()
    cr.restore()
    # the lid: the props porthole through the lid plane's local Jacobian
    S0 = pp(Cl)
    dz = z - cam.z
    dxdX = k
    dxdz = -(Cl[0] - cam.x) * k / dz
    dydz = -((HC - Cl[1]) - cam.y) * k / dz
    du = (dxdX * u_dir[0] + dxdz * u_dir[2], dydz * u_dir[2])
    if du[0] < 0:                                    # keep the porthole un-mirrored
        du = (-du[0], -du[1])
    m = cairo.Matrix(du[0], du[1], 0.0, k, S0[0], S0[1] + DRUM_AXLE * k)
    det = 2 if k >= 0.9 else 1 if k >= 0.45 else 0
    if _visible(cam, Cl, n_lid):
        cr.save()
        cr.transform(m)
        P.drum_porthole(cr, -jx * 0.0, 0.0, 1.0, light, t, seed=seed, speed=speed, glow=glow, rumble=0.0,
                        vp=None, depth=(0.0, 0.0), detail=det)
        cr.restore()
    return (S0, DRUM_R * k, glow)


def _drum_list():
    """[(side, z, seed, speed, bay, slot)] for every drum in the arcade (bays 0..4). Bay 0 keeps
    only its far slot: nothing big and bright in the foreground corners."""
    out = []
    for b in range(len(PIER_Z) - 1):
        zc = 0.5 * (PIER_Z[b] + PIER_Z[b + 1])
        for j, dz in enumerate(BAY_DRUMS):
            if b == 0 and j == 0:
                continue
            for side in (-1, 1):
                seed = 30 + b * 7 + j * 3 + (side > 0) * 50
                spd = 0.75 + 0.6 * core.hash01(seed, 3)
                out.append((side, zc + dz, seed, spd, b, j))
    return out


DRUMS = _drum_list()


# ----------------------------------------------------------------------------------------
# small set pieces
# ----------------------------------------------------------------------------------------

_SOCK_LINE = [(-64.0, 0.0), (-30.0, -4.0), (0.0, -3.0), (18.0, 4.0), (28.0, 18.0), (36.0, 34.0), (48.0, 44.0)]
_SOCK_W = [13.0, 13.5, 13.0, 12.5, 11.5, 11.0, 9.0]


LINES = [(2110.0, 980.0, 11), (3010.0, 1000.0, 12), (3910.0, 1010.0, 13)]     # (z, h, seed)


def _drying_line(cr, cam, z, h, t, seed):
    """A cord strung across the nave with linens hanging near the piers (the middle left clear,
    so the moon window at the end stays the one clean shape). Sways a little."""
    with plane(cr, cam, z) as s:
        x0, y0 = ref(-NAVE, h, z)
        x1, y1 = ref(NAVE, h, z)
        sag = 70.0 * s
        sw = 0.6 * math.sin(t * 0.7 + seed)
        cr.set_line_width(max(0.6, 3.0 * s))
        core.src(cr, "#081010", 0.85)
        cr.move_to(x0, y0)
        cr.curve_to(x0 + (x1 - x0) * 0.3, y0 + sag, x0 + (x1 - x0) * 0.7, y0 + sag, x1, y1)
        cr.stroke()
        for i, u in enumerate((0.1, 0.22, 0.78, 0.9)):
            px = x0 + (x1 - x0) * u
            py = y0 + sag * 4 * u * (1 - u) * 0.75
            w = (70 + 60 * core.hash01(i, seed)) * s
            hh = (110 + 90 * core.hash01(i, seed + 1)) * s
            sk = (4.0 + 3.0 * math.sin(t * 0.9 + i + seed)) * s * (1.0 + sw)
            col = core.mix(["#8fa4a8", "#9a8a80", "#7f94a6", "#a8aea6"][int(core.hash01(i, seed + 2) * 4)], "#10201f", 0.66)
            cr.move_to(px - w / 2, py)
            cr.line_to(px + w / 2, py + 2 * s)
            cr.curve_to(px + w / 2 + sk, py + hh * 0.6, px + w / 2 - 4 * s + sk, py + hh, px + w * 0.25 + sk, py + hh)
            cr.line_to(px - w * 0.3 + sk, py + hh * (0.9 + 0.15 * core.hash01(i, seed + 3)))
            cr.curve_to(px - w / 2 + sk, py + hh * 0.7, px - w / 2 + 2 * s, py + hh * 0.3, px - w / 2, py)
            cr.close_path()
            core.src(cr, col, 0.85)
            cr.fill()
            # a fold down the middle and a damp, darker hem
            cr.set_line_width(max(0.5, 2.0 * s))
            core.src(cr, "#050c0c", 0.35)
            cr.move_to(px + w * 0.05, py + 3 * s)
            cr.curve_to(px + w * 0.1 + sk * 0.5, py + hh * 0.4, px - w * 0.05 + sk, py + hh * 0.7, px + sk * 0.8, py + hh * 0.92)
            cr.stroke()


def _steam(cr, t, x, y, k, seed):
    """Steam curling off a drum, looping (pure function of t)."""
    period = 2.6
    for j in range(2):
        off = core.hash01(seed, 5) * period + j * period * 0.5
        t0 = math.floor((t - off) / period) * period + off
        fx.smoke(cr, t, t0, x, y, n=5, dur=3.2, rise=120.0, drift=(10.0, -4.0), size=12.0, color="#a9d8cc",
                 alpha=0.16, seed=seed * 7 + j, scale=k)


def _sock(cr, cam):
    """One lost striped stocking on the flagstones of the aisle (built on the floor, projected)."""
    X0, Z0 = SOCK
    pts = [(X0 + dx, Z0 + dz) for dx, dz in _SOCK_LINE]
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / n * _SOCK_W[i], tx / n * _SOCK_W[i]
        left.append(cam.p(x + nx, 0.0, z + nz))
        right.append(cam.p(x - nx, 0.0, z - nz))
    k = cam.k(Z0)
    cx, cy = cam.p(X0, 0.0, Z0)
    B.contact_shadow(cr, cx, cy + 3 * k, 80 * k, 10 * k, alpha=0.35)
    outline = left + right[::-1]
    core.smooth_closed(cr, outline, 0.6)
    core.src(cr, "#4e6178")
    cr.fill()
    core.smooth_closed(cr, [cam.p(x, 0.0, z) for x, z in [(X0 + 28, Z0 + 26), (X0 + 52, Z0 + 38), (X0 + 44, Z0 + 52), (X0 + 26, Z0 + 40)]], 0.8)
    core.src(cr, "#a9b6bd")                         # a pale darned toe
    cr.fill()
    for xs in (-52.0, -38.0, -24.0):                 # cream stripes round the leg
        q = [cam.p(X0 + xs, 0.0, Z0 - 13), cam.p(X0 + xs + 6, 0.0, Z0 - 13), cam.p(X0 + xs + 6, 0.0, Z0 + 12),
             cam.p(X0 + xs, 0.0, Z0 + 12)]
        core.polygon(cr, q)
    core.src(cr, "#c9c7b4", 0.9)
    cr.fill()


# ----------------------------------------------------------------------------------------
# acting
# ----------------------------------------------------------------------------------------

def _dragon_pose(t):
    """The dragon's performance. Body yaw starts at -0.75 (3/4 left: facing his drum), swivels
    toward her (+0.42) before the lean, opens toward the room during the look-around and comes
    back round to his drum after the last line. Eyes lead, the head follows, the body last."""
    yaw = core.track(t, [
        (0.0, -0.75), (T_SWIVEL0, -0.75), (T_SWIVEL1, 0.42, "inout_sine"),
        (L1.end + 0.2, 0.42), (T_LOOK0 + 0.1, -0.2, "inout_sine"),                  # sinks back toward his drum
        (T_LOOK1 - 0.3, 0.38, "inout_sine"), (L2.end + 0.2, 0.38),                 # opens to the nave
        (L2.end + 2.2, -0.62, "inout_sine"), (DUR, -0.62)])
    shake = 0.06 * math.sin((t - (L2.end - 0.75)) * TAU * 2.4) * core.window(t, L2.end - 0.75, L2.end + 0.1, 0.15, 0.3)
    # where his head points (absolute yaw): eyes lead it along the row of drums toward the moon
    head_yaw = core.track(t, [
        (0.0, -0.95), (T_GLANCE + 0.12, -0.95), (T_GLANCE + 0.55, 0.35, "inout_sine"),
        (T_SWIVEL1, 0.62), (T_TAP + 0.6, 0.55), (L1.end + 0.3, 0.5),
        (T_LOOK0 - 0.05, -0.9, "inout_sine"),                                       # down to his own drum
        (T_LOOK0 + 0.55, -0.85), (T_LOOK0 + 1.9, -0.25, "inout_sine"),              # drum after drum...
        (T_LOOK0 + 2.5, -0.1), (T_LOOK1 - 0.1, 0.95, "inout_sine"),                 # ...down the nave
        (L2.start + 0.6, 1.0), (L2.end + 0.25, 0.92),
        (L2.end + 1.0, 0.7, "inout_sine"), (T_SIGH + 1.6, 0.55), (DUR - 1.6, -0.45, "inout_sine"),
        (DUR, -0.5)]) + shake
    head_turn = core.clamp((head_yaw - yaw) / 1.1, -1.0, 1.0)
    look = core.track(t, [
        (0.0, (-0.55, 0.55)), (2.2, (-0.5, 0.62)), (3.4, (-0.58, 0.5)), (T_GLANCE, (-0.58, 0.5)),
        (T_GLANCE + 0.14, (0.9, -0.1), "out_cubic"),
        (T_TAP + 0.05, (0.9, -0.1)), (T_TAP + 0.45, (0.72, -0.62), "inout_sine"),
        (L1.start - 0.1, (0.72, -0.6)), (L1.end + 0.2, (0.6, -0.4)),
        (L1.end + 0.5, (-0.7, 0.6), "inout_sine"),                                   # eyes sink to his drum
        (T_LOOK0, (-0.65, 0.55)),
        (T_LOOK0 + 0.3, (-0.2, 0.3), "out_cubic"), (T_LOOK0 + 0.9, (-0.1, 0.3)),     # the next drum
        (T_LOOK0 + 1.15, (0.35, 0.15), "out_cubic"), (T_LOOK0 + 1.9, (0.4, 0.12)),   # the next
        (T_LOOK0 + 2.15, (0.8, 0.05), "out_cubic"), (T_LOOK1 - 0.4, (0.85, 0.0)),    # all the way down
        (L2.start + 0.3, (0.9, -0.05)), (L2.end, (0.75, 0.05)),
        (L2.end + 0.6, (0.3, 0.55), "inout_sine"), (T_SIGH + 1.6, (0.25, 0.6)),
        (DUR - 1.8, (-0.6, 0.55), "inout_sine"), (DUR, (-0.6, 0.55))])
    watch = 1.0 - core.ramp(t, T_GLANCE - 0.4, T_GLANCE, "inout_sine") + core.ramp(t, DUR - 2.2, DUR - 1.2, "inout_sine")
    if watch > 0.0:
        ph = t * TAU * 0.33
        look = (look[0] + 0.07 * math.cos(ph) * watch, look[1] + 0.06 * math.sin(ph) * watch)
    head_nod = core.track(t, [
        (0.0, -0.3), (T_GLANCE + 0.15, -0.3), (T_GLANCE + 0.55, 0.0, "inout_sine"),
        (T_LEAN + 0.4, 0.1), (T_TAP + 0.6, 0.32, "inout_sine"), (L1.start, 0.32), (L1.end - 0.15, 0.2),
        (T_LOOK0 - 0.1, -0.25, "inout_sine"), (T_LOOK0 + 1.9, -0.05), (T_LOOK1, 0.06),
        (L2.end, 0.0), (L2.end + 1.0, -0.3, "inout_sine"), (DUR, -0.32)])
    lean = core.track(t, [
        (0.0, 0.0), (2.4, 0.0), (2.75, 0.12, "inout_sine"), (3.2, -0.02, "inout_sine"), (3.6, 0.0),
        (T_LEAN - 0.3, -0.06, "inout_sine"), (T_LEAN + 0.55, 0.55, "out_cubic"), (T_TAP + 0.2, 0.55),
        (T_TAP + 1.4, 0.15, "inout_sine"), (T_LOOK0 + 1.5, -0.05, "inout_sine"), (T_LOOK1, 0.05),
        (DUR, 0.1)])
    hunch = core.track(t, [(0.0, 0.9), (T_LEAN - 0.6, 0.9), (T_LEAN - 0.1, 0.7, "inout_sine"),
                           (T_TAP + 0.4, 0.75), (L1.end + 0.6, 0.95, "inout_sine"), (T_SIGH, 0.95),
                           (T_SIGH + 1.6, 1.05, "inout_sine"), (DUR, 1.05)])
    wings = core.track(t, [(0.0, -0.9), (T_LEAN - 0.1, -0.9), (T_LEAN + 0.7, -0.25, "out_cubic"),
                           (T_TAP + 0.3, -0.25), (L1.start - 0.4, -0.45), (L1.end + 0.5, -1.0, "inout_sine"),
                           (DUR, -1.0)])
    # the aborted line: the mouth opens and stays open -- nothing comes out
    gape = core.track(t, [(T_LEAN + 0.15, 0.0), (T_LEAN + 0.45, 0.24, "out_cubic"), (T_TAP + 0.15, 0.24),
                          (T_TAP + 0.45, 0.0, "inout_sine")])
    talk = max(tl.talk(SCENE, t, "MAN"), gape)
    hope = core.window(t, T_LEAN - 0.2, T_TAP + 0.5, 0.45, 0.4)
    sigh = core.window(t, T_SIGH, T_SIGH + 2.6, 0.55, 1.4)
    blink = None
    for tb in (T_GLANCE + 0.75, L1.end + 0.35, T_LOOK1 + 0.15, L2.end + 0.45):
        if tb <= t <= tb + 0.2:
            blink = core.window(t, tb, tb + 0.2, 0.06, 0.12)
        elif blink is None and abs(t - tb) < 0.9:
            blink = 0.0                     # no automatic blink crowding a deliberate one
    mood, mood2, mix = "lonely", "worried", hope * 0.55
    if t >= T_TAP + 0.4:
        mood, mood2, mix = "tired", "sad", core.ramp(t, L1.end + 0.3, T_LOOK0, "inout_sine") * 0.6
    if t >= T_LOOK1 - 0.5:
        mood, mood2, mix = "tired", "lonely", core.ramp(t, T_LOOK1 - 0.5, L2.start + 0.4)
    tail_swing = -0.25 + 0.12 * B.sway(t, 0.21, 11) + 0.25 * B.wobble(t, T_LEAN, 1.6, 2.2)
    # a small, specific gesture on the attempt: one hand lifts off his knee toward her... and sinks back
    reach = core.track(t, [(T_LEAN + 0.05, 0.0), (T_LEAN + 0.6, 0.72, "out_cubic"), (T_TAP + 0.1, 0.66),
                           (T_TAP + 0.75, 0.0, "inout_sine")])
    near = ch.Arm("hand_out_offer", amt=reach, prev="rest") if reach > 0.001 else ch.Arm("rest")
    return ch.DragonPose(facing=0, turn=yaw / 0.6, sit=1.0, seat_h=STOOL_H, hunch=hunch, lean=lean,
                         head_turn=head_turn, head_nod=head_nod, look=look, mood=mood, mood2=mood2,
                         mood_mix=mix, talk=talk, sigh=sigh, blink=blink, wings=wings, tail_curl=0.55,
                         tail_swing=tail_swing, near=near, seed=3)


def _tap_offset(t):
    """0 = finger on the board, 1 = pulled back between taps."""
    if t < T_HIT1 - 0.18:
        return 1.0
    for th in (T_HIT1, T_HIT2):
        if th - 0.18 <= t <= th:
            return 1.0 - core.in_quad((t - (th - 0.18)) / 0.18)
        if th < t <= th + 0.22 and (th == T_HIT1 or t < T_REST - 0.3):
            return core.out_cubic((t - th) / 0.22)
    if t < T_HIT2 + 0.22:
        return 1.0
    return 1.0 - core.inout_sine(core.clamp((t - (T_REST - 0.3)) / 0.3))


T_WITHDRAW0, T_WITHDRAW1 = T_CUT_BACK + 0.7, T_CUT_BACK + 1.5


def _elf_pose(t, tap_target):
    reach = core.ramp(t, T_REACH0, T_REACH1, "inout_sine") * (1.0 - core.ramp(t, T_WITHDRAW0, T_WITHDRAW1, "inout_sine"))
    far = (ch.ElfArm("tap_sign", amt=reach, prev="rest", phase=0.95, screen=tap_target)
           if reach > 0 and tap_target is not None else ch.ElfArm("rest"))
    tilt = 0.05 * B.sway(t, 0.12, 41) - 0.04
    groove = 0.035 * math.sin(t * TAU * 1.15) * (1.0 - core.window(t, T_TAP - 0.2, T_WITHDRAW1 + 0.3, 0.3, 0.4))
    return ch.ElfPose(facing=-1, sit=1.0, glow=1.0, shells=0.8 + 0.2 * (0.5 + 0.5 * math.sin(t * TAU * 1.15)),
                      look=(-0.12 + 0.05 * B.sway(t, 0.3, 4), 0.92), head_nod=-0.42 + groove, head_tilt=tilt,
                      near=ch.ElfArm("mirror", phase=t * 0.3), far=far, seed=5)


def _shell_hum(cr, t, rig, scale):
    """Tiny cold rings of sound humming out of her ear-shells."""
    for i, (x, y) in enumerate(rig.shells):
        for k in range(3):
            u = (t * 0.9 + k / 3.0 + i * 0.37) % 1.0
            r = (4.0 + 22.0 * u) * scale
            a = 0.5 * (1.0 - u) * min(1.0, u * 5.0)
            cr.new_path()
            cr.arc(x + 6.0 * scale, y - 2.0 * scale, r, -0.9, 0.9)
            cr.set_line_width(max(0.8, 1.6 * scale))
            core.src(cr, "#9ff4ff", a)
            cr.stroke()


# ----------------------------------------------------------------------------------------
# buffers for depth of field
# ----------------------------------------------------------------------------------------

class _Buf:
    """A reduced-resolution buffer: drawing into it is cheaper, and upscaling it is soft."""

    def __init__(self, res, opaque=True):
        self.res, self.opaque = res, opaque
        self.surf = core.new_surface(int(W * res) + 2, int(H * res) + 2)

    def begin(self):
        c = core.new_context(self.surf)
        c.set_operator(cairo.OPERATOR_SOURCE)
        if self.opaque:
            c.set_source_rgba(0.02, 0.05, 0.06, 1.0)
        else:
            c.set_source_rgba(0, 0, 0, 0)
        c.paint()
        c.set_operator(cairo.OPERATOR_OVER)
        c.scale(self.res, self.res)
        return c

    def paint(self, cr, alpha=1.0):
        self.surf.flush()
        cr.save()
        cr.identity_matrix()
        cr.scale(1.0 / self.res, 1.0 / self.res)
        cr.set_source_surface(self.surf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        if alpha >= 0.999:
            cr.paint()
        else:
            cr.paint_with_alpha(alpha)
        cr.restore()


# ----------------------------------------------------------------------------------------
# setup / draw
# ----------------------------------------------------------------------------------------

def setup():
    st = {"light": fx.LightLayer()}
    _TEX["pier"] = _build_pier_textures()
    s = F / WALL_Z
    x0, ytop = ref(-AISLE_X - 400, 2400.0, WALL_Z)
    x1, yfl = ref(AISLE_X + 400, 0.0, WALL_Z)
    st["wall"] = fx.Layer(_draw_end_wall, w=x1 - x0, h=yfl - ytop + 4, x=x0, y=ytop, blur=1.0)
    st["basket"] = fx.Layer(_draw_basket, w=420, h=420, x=-210, y=-330, blur=3.0, res=0.5)
    st["tub"] = fx.Layer(_draw_tub, w=460, h=520, x=-230, y=-440, blur=3.0, res=0.5)
    st["bg"] = {"A": _Buf(0.55), "B": _Buf(0.4), "C": _Buf(0.46)}
    st["fg"] = {"A": _Buf(0.33, opaque=False), "B": _Buf(0.3, opaque=False), "C": _Buf(0.3, opaque=False)}
    # the plaque, in the reference coordinates of pier 1's front face
    st["plaque_xy"] = ref(X_PLAQUE, H_NAIL, Z_PLAQUE)
    st["plaque_s"] = F / Z_PLAQUE
    scratch = core.frame(8, 8)[1]
    pq = P.draw_plaque(scratch, *st["plaque_xy"], "SELF-SERVICE", st["plaque_s"], L_SET, 0.0, size=30.0)
    st["plaque_rig"] = pq
    st["reach"] = _solve_reach(st)
    # where the sigh leaves his nostrils (fixed in his plane, so the curl stays in the air)
    ts = T_SIGH + 0.3
    dx, dy = ref(X_DRAGON, 0.0, Z_DRAGON)
    nr = ch.draw_dragon(scratch, dx, dy, F / Z_DRAGON, _dragon_pose(ts), L_DRAGON, ts)
    st["smoke_at"] = (nr.nose[0], nr.nose[1], 1.0 if nr.nose[0] >= nr.head[0] else -1.0)
    return st


def _solve_reach(st):
    """Once, in setup: the wrist target (in her plane's reference coordinates) that puts her
    pointing fingertip on the board's lower-left corner, and the pull-back direction between taps.
    The board hangs 15 units behind her hand plane -- the parallax between them is sub-pixel."""
    pq = st["plaque_rig"]
    sp = st["plaque_s"]
    w, h = pq.size
    gx, gy = pq.center[0] - w * 0.5 + 18.0 * sp, pq.center[1] + h * 0.2
    X, hh = (gx - PX) / sp, HC - (gy - PY) / sp           # the touch point in 3D...
    goal = ref(X, hh, Z_ELF)                              # ...in her plane
    scratch = core.frame(8, 8)[1]
    s_elf = F / Z_ELF
    ex, ey = ref(X_ELF, 0.0, Z_ELF)
    tgt = goal
    hf = None
    for _ in range(5):
        rig = ch.draw_elf(scratch, ex, ey, s_elf, _elf_pose(T_REST + 0.5, tgt).with_(
            far=ch.ElfArm("tap_sign", amt=1.0, phase=0.95, screen=tgt)), L_ELF, T_REST + 0.5)
        hf = rig.hand_far
        tip = max(hf.tips, key=lambda p: (p[0] - hf.palm[0]) ** 2 + (p[1] - hf.palm[1]) ** 2)
        tgt = (tgt[0] + goal[0] - tip[0], tgt[1] + goal[1] - tip[1])
    dx, dy = goal[0] - hf.palm[0], goal[1] - hf.palm[1]
    n = math.hypot(dx, dy) or 1.0
    back = (-dx / n * 13.0 * s_elf, -dy / n * 13.0 * s_elf + 3.0 * s_elf)
    return tgt, back


def draw(cr, t, st):
    cam, shot = camera(t)
    # ================= far: everything deeper than the focus band -> soft buffer
    bg = st["bg"][shot]
    bc = bg.begin()
    _vault_backdrop(bc, cam)
    with plane(bc, cam, WALL_Z):
        st["wall"].paint(bc)
    _aisles_and_floor(bc, cam)
    drum_lights = []
    lamps = []
    for b in range(len(PIER_Z) - 2, -1, -1):
        za, zb = PIER_Z[b], PIER_Z[b + 1]
        if zb > Z_FOCUS_FAR + 80:                      # the pier closing this bay (behind it)
            for side in (-1, 1):
                _pier(bc, cam, side, zb)
            _rib(bc, cam, zb)
        if b == 0:
            continue
        for side, z, seed, spd, bb, j in DRUMS:
            if bb == b and z > Z_FOCUS_FAR:
                drum_lights.append(_side_drum(bc, cam, side, z, t, seed, spd, glow=0.7))
        for side in (-1, 1):
            _arcade(bc, cam, side, za + PIER_D / 2, zb - PIER_D / 2)
        for (zl, hl, sdl) in LINES:
            if za < zl <= zb:
                _drying_line(bc, cam, zl, hl, t, sdl)
        for (X, h, z, sd) in LAMPS:
            if za < z <= zb and z > Z_FOCUS_FAR:
                with plane(bc, cam, z) as s:
                    lx, ly = ref(X, h, z)
                    lamps.append((P.draw_wisp_lamp(bc, lx, ly, s, L_SET, t, seed=sd, top=ref(0, 2400, z)[1]), z))
    # atmospheric depth: haze gathers toward the far end of the nave
    vx, vy = cam.vp()
    rad = 760.0 * cam.zoom
    bc.save()
    bc.set_source(core.radial(vx, vy + 40, rad, [(0.0, core.alpha(C["haze"], 0.34)), (0.45, core.alpha(C["haze"], 0.14)),
                                                  (1.0, core.alpha(C["haze"], 0.0))]))
    bc.rectangle(-20, -20, W + 40, H + 40)
    bc.fill()
    # hold the far hall down in value so the people and their glows carry the frame (in the
    # reduced-resolution buffer: a full-frame radial gradient is expensive at full size)
    bc.set_source(core.radial(vx, vy, 1300.0, [(0.0, core.alpha("#020707", 0.05)), (0.5, core.alpha("#020707", 0.22)),
                                                (1.0, core.alpha("#020707", 0.42))]))
    bc.rectangle(-20, -20, W + 40, H + 40)
    bc.fill()
    bc.restore()
    bg.paint(cr)

    # ================= the focus band, full resolution
    # bay 0: the arcade arches and the drums at the characters' depth (his drum among them)
    for side in (-1, 1):
        _arcade(cr, cam, side, PIER_Z[0] + PIER_D / 2, PIER_Z[1] - PIER_D / 2)
    for side in (-1, 1):
        _pier(cr, cam, side, PIER_Z[1])
    _rib(cr, cam, PIER_Z[1])
    his = None
    for side, z, seed, spd, bb, j in DRUMS:
        if Z_FOCUS_NEAR <= z <= Z_FOCUS_FAR:
            r = _side_drum(cr, cam, side, z, t, seed, spd, glow=1.0)
            drum_lights.append(r)
            if side < 0 and bb == HIS_BAY and j == HIS_SLOT:
                his = r
            top = cam.p(side * (LID_X + BARREL * 0.4), DRUM_AXLE + DRUM_R, z + 30.0)
            _steam(cr, t, top[0], top[1], cam.k(z), seed)
    # the plaque on pier 1
    with plane(cr, cam, Z_PLAQUE) as s:
        P.draw_plaque(cr, *st["plaque_xy"], "SELF-SERVICE", s, L_SET, t, taps=(T_HIT1, T_HIT2),
                      swing=0.006 * math.sin(t * 0.9), size=30.0)
    _sock(cr, cam)
    # the elf on her form
    tgt, back = st["reach"]
    off = _tap_offset(t)
    target = (tgt[0] + back[0] * off, tgt[1] + back[1] * off)
    with plane(cr, cam, Z_ELF) as s:
        ex, ey = ref(X_ELF, 0.0, Z_ELF)
        P.draw_washhouse_bench(cr, ex, ey, s, L_SET, t, yaw=-0.12)
        erig = ch.draw_elf(cr, ex, ey, s, _elf_pose(t, target), L_ELF, t)
        if erig.mirror:
            fx.glow(cr, erig.mirror[0], erig.mirror[1], 70 * s, C["mirror"], 0.32)
        _shell_hum(cr, t, erig, s)
        m_elf = cam.matrix(Z_ELF)
        e_mirror = m_elf.transform_point(*erig.mirror) if erig.mirror else None
    # the dragon on the far-too-small stool
    with plane(cr, cam, Z_DRAGON) as s:
        dx, dy = ref(X_DRAGON, 0.0, Z_DRAGON)
        dpose = _dragon_pose(t)
        sw = 0.03 * B.wobble(t, 2.75, 3.2, 3.0) + 0.025 * B.wobble(t, T_SWIVEL1 - 0.1, 3.0, 3.0)
        yaw = dpose.turn * 0.6
        P.draw_stool(cr, dx, dy, s, L_SET, t, yaw=0.3 + yaw * 0.25, part="back", wobble=sw)
        drig = ch.draw_dragon(cr, dx, dy, s, dpose, L_DRAGON, t)
        P.draw_stool(cr, dx, dy, s, L_SET, t, yaw=0.3 + yaw * 0.25, part="front", wobble=sw)
        # the sigh: a little curl of grey smoke from his nostrils
        nx, ny, ndir = st["smoke_at"]
        fx.smoke(cr, t, T_SIGH + 0.3, nx, ny, n=10, dur=3.0, rise=95.0, drift=(46.0 * ndir, -8.0), size=9.5,
                 color="#b9c6c4", alpha=0.6, seed=7, scale=s)
        m_d = cam.matrix(Z_DRAGON)
        d_head = m_d.transform_point(*drig.head)
    for (X, h, z, sd) in LAMPS:
        if z <= Z_FOCUS_FAR:
            with plane(cr, cam, z) as s:
                lx, ly = ref(X, h, z)
                lamps.append((P.draw_wisp_lamp(cr, lx, ly, s, L_SET, t, seed=sd, top=ref(0, 2400, z)[1]), z))

    # ================= foreground: the first piers and the basket, very soft
    fg = st["fg"][shot]
    fc = fg.begin()
    for side in (-1, 1):
        _pier(fc, cam, side, PIER_Z[0], near=True)
    _rib(fc, cam, PIER_Z[0])
    for side, z, seed, spd, bb, j in DRUMS:
        if z < Z_FOCUS_NEAR:
            drum_lights.append(_side_drum(fc, cam, side, z, t, seed, spd, glow=0.8))
    for name, X, z in FG_PIECES:
        if z - cam.z < 60.0:
            continue
        with plane(fc, cam, z) as s:
            gx, gy = ref(X, 0.0, z)
            fc.translate(gx, gy)
            fc.scale(s, s)
            st[name].paint(fc)
    fg.paint(cr)

    # ================= light
    lc = st["light"].begin()
    for (S0, r, g) in drum_lights:
        fx.glow(lc, S0[0], S0[1], r * 3.0, C["porthole"], 0.2 * g)
        if r > 22.0:                                 # a wet streak of it on the flagstones below
            fx.light_shaft(lc, S0[0], S0[1] + r * 1.6, S0[0], S0[1] + r * 4.2, r * 0.9, r * 1.4, C["porthole"],
                           alpha=0.07 * g, soft=2, fade_start=0.0, fade_end=1.0)
    for (lp, z) in lamps:
        with plane(lc, cam, z) as s:
            P.wisp_light(lc, lp, s, None, 0.8)
        X = (lp.center[0] - PX) / (F / z)
        pc = cam.p(X, 0.0, z)
        kk = cam.k(z)
        fx.light_pool(lc, pc[0], pc[1], 520 * kk, 110 * kk, "#6fffd0", 0.24 * lp.level)
    # the moon: a long cold shaft down the nave, landing in the empty aisle between them
    w0 = cam.p(0.0, 1050.0, WALL_Z)
    w1 = cam.p(40.0, 0.0, 1700.0)
    fx.light_shaft(lc, w0[0], w0[1], w1[0], w1[1], 90 * cam.k(WALL_Z), 520 * cam.k(1700.0), C["shaft"], alpha=0.13,
                   soft=3, fade_start=0.4, fade_end=0.3)
    mp = cam.p(40.0, 0.0, 2100.0)
    fx.light_pool(lc, mp[0], mp[1], 560 * cam.k(2100.0), 150 * cam.k(2100.0), C["shaft"], 0.2)
    if his is not None:
        kk = cam.k(Z_DRAGON)
        hp = his[0]
        fx.glow(lc, 0.6 * d_head[0] + 0.4 * hp[0], 0.6 * d_head[1] + 0.4 * hp[1], 130 * kk, C["porthole"], 0.07)
        # his porthole's cold light pooled on the floor round the stool
        fp = cam.p(X_DRAGON - 120.0, 0.0, Z_DRAGON + 40.0)
        kk = cam.k(Z_DRAGON)
        fx.light_pool(lc, fp[0], fp[1], 360 * kk, 76 * kk, C["porthole"], 0.3)
        fx.glow(lc, d_head[0] - 60 * kk, d_head[1] + 60 * kk, 240 * kk, C["porthole"], 0.08)
    ep = cam.p(X_ELF - 40.0, 0.0, Z_ELF - 30.0)
    kk = cam.k(Z_ELF)
    fx.light_pool(lc, ep[0], ep[1], 260 * kk, 55 * kk, C["mirror"], 0.16)
    if e_mirror:
        fx.glow(lc, e_mirror[0], e_mirror[1] - 30, 200 * cam.k(Z_ELF), C["mirror"], 0.14)
    # dust motes turning in the shaft
    sx0, sy0 = w0
    sx1, sy1 = w1
    kk = cam.k(1700.0)

    def in_shaft(x, y):
        u = core.clamp((y - sy0) / max(1.0, sy1 - sy0))
        cx_ = sx0 + (sx1 - sx0) * u
        half = (45 + 230 * u) * kk
        return core.clamp(1.0 - abs(x - cx_) / max(1.0, half)) * core.smoothstep(0.08, 0.35, u)

    fx.dust(cr, t, (min(sx0, sx1) - 300 * kk, sy0, abs(sx1 - sx0) + 600 * kk, sy1 - sy0), n=110,
            color="#d8ecff", alpha=0.75, size=(0.9 * kk, 2.4 * kk), seed=3, drift=(5.0, -2.5), mask=in_shaft)
    fx.post(cr, t, light=st["light"], bloom_strength=0.55, threshold=0.6, bloom_radius=2.2, wide=0.4,
            grain=0.035, vignette=0.66, vignette_color=C["vig"])
    if t < T_FADE1:
        fx.fade(cr, 1.0 - core.ramp(t, T_FADE0, T_FADE1, "inout_sine"))


# ----------------------------------------------------------------------------------------
# sound cues (the sound designer synthesizes foley from these): (local t, kind, params)
# ----------------------------------------------------------------------------------------
def _his_drum_landings():
    """When the biggest garment in his drum thumps down (the props porthole's tumble cycle)."""
    side, z, seed, spd = next((sd, z, se, sp) for sd, z, se, sp, b, j in DRUMS
                              if sd < 0 and b == HIS_BAY and j == HIS_SLOT)
    i = max(range(7), key=lambda k: core.hash01(k, seed + 6))
    ph = core.hash01(i, seed + 1)
    rate = 0.42 * spd
    out, k = [], 1
    while True:
        tt = (k - ph) / rate
        k += 1
        if tt >= DUR - 0.3:
            break
        if tt > T_FADE1 and not (T_CUT_INSERT - 0.05 <= tt <= T_CUT_BACK + 0.05):
            out.append(round(tt, 3))
    return out


SFX_CUES = sorted([
    (2.75, "bench_creak", {"gain": 0.35, "pan": -0.35, "size": 0.35}),                 # shifts on the tiny stool
    (T_SWIVEL0 + 0.2, "bench_creak", {"gain": 0.45, "pan": -0.35, "size": 0.35}),      # swivels toward her
    (T_SWIVEL0 + 0.25, "cloth_rustle", {"gain": 0.3, "pan": -0.35}),
    (T_LEAN + 0.05, "cloth_rustle", {"gain": 0.4, "pan": -0.35}),                      # leans in, hand lifts
    (T_LEAN + 0.3, "wing_flutter", {"gain": 0.18, "pan": -0.35, "size": 0.3}),         # wings lift in hope
    (T_TAP + 0.05, "cloth_rustle", {"gain": 0.3, "pan": 0.4}),                         # her arm comes up
    (T_HIT1, "tap_wood", {"gain": 0.75, "pan": 0.2}),                                  # tap
    (T_HIT2, "tap_wood", {"gain": 0.8, "pan": 0.2}),                                   # tap
    (T_HIT2 + 0.08, "creak_wood", {"gain": 0.15, "pan": 0.25, "size": 0.2}),           # the board rocks on its nail
    (T_REST, "tap_wood", {"gain": 0.3, "pan": 0.2}),                                   # ...and the finger stays
    (L1.end + 0.25, "wing_flutter", {"gain": 0.15, "pan": 0.0, "size": 0.3}),          # wings sink
    (T_WITHDRAW0 + 0.1, "cloth_rustle", {"gain": 0.18, "pan": 0.85}),                  # she lowers her hand (off)
    (L1.end + 0.45, "bench_creak", {"gain": 0.25, "pan": 0.0, "size": 0.35}),          # turns back to his drum
    (T_LOOK0 + 2.2, "bench_creak", {"gain": 0.2, "pan": -0.3, "size": 0.35}),          # opens to the room
    (T_SIGH, "sigh", {"gain": 0.75, "pan": -0.4}),
    (T_SIGH + 0.35, "smoke_puff", {"gain": 0.3, "pan": -0.4}),
    (L2.end + 1.3, "bench_creak", {"gain": 0.2, "pan": -0.35, "size": 0.35}),          # back round to his drum
] + [(tt, "drum_spin_thunk", {"gain": 0.22, "pan": -0.45, "size": 0.5}) for tt in _his_drum_landings()],
    key=lambda c: c[0])
