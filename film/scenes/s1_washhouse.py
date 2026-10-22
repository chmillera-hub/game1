"""s1_washhouse.py -- SCENE 1: THE WASH-HOUSE (late night).  "Self-service."

THE IDEA. Numb, cold isolation in a place full of motion and empty of contact. The wash-house is
built like a church: a long vaulted nave in strict one-point perspective, an arcade of stone piers
marching away on both sides, and in every bay a pair of enchanted tumbling drums (oak barrels on
cradles, brass lids, glass portholes) toed in toward the aisle like pews -- every one tumbling a
stranger's laundry, colourful and rumbling, with nobody there. The aisle runs to one tall black
arched window with the moon in it. Symmetry and repetition are the machine; one hunched dragon on
a milking stool far too small for him is the thing that breaks it. Across the aisle, an elf who is
beautiful and completely closed: hood up, sea-shells humming in her ears, face lit by her mirror.
The empty, moonlit aisle between them -- one lost stocking lying in it -- is the subject: the gap.

BUILD. A 2.5D set in true perspective (Cam3): camera-facing planes (end wall, pier faces, ribs,
characters, plaque, stools) are drawn in their own reference coordinates; receding surfaces (floor,
aisle walls and their windows, pier sides, arcade spandrels, the drums' barrels) are projected every
frame and clipped at the near plane, so dollies, trucks and cranes all have real parallax and the
camera can travel down the nave. Every drawable is a depth-sorted item; each shot names its focus
band (fixed in world depth, so nothing hops between buffers mid-move), and everything deeper is
drawn into a soft reduced-resolution buffer, everything nearer into an even softer one (depth of
field); the band is drawn at full resolution. The portholes in the band are in TRUE perspective
(the props porthole rendered once per frame into a texture and painted through a fine polar grid
of exactly projected triangles), so a lid seen close and steep -- the row shot -- sits exactly on
its barrel; soft far ones use one rim-fitted affine. Drums are culled by their projected extent
(never while any of them is in frame) and their glow fades before they pass the camera. Times
below are the current timeline values; the code derives every one of them from timeline.json.

SHOT A -- 0.0 -> 8.55 (T_CUT_INSERT = s1_tap + 0.25)   WIDE -> TWO-SHOT, one slow dolly-in + crane-down
  s1_fadein (0-1): fade up from black on a room already in motion -- drums tumbling and steaming,
  wisps buzzing and dipping in their iron cages, dust turning in the moon shaft. High camera down
  the nave: the dragon left of centre on the stool beside HIS drum (3/4 left, watching his own
  laundry go round; his emptied laundry sack -- the one he carried in on the prologue's last
  page -- slumped by the stool, a purple sleeve trailing out of it), the elf right of centre on a
  plank form under the SELF-SERVICE plaque.
  Framing: soft dark near piers at both edges, a wicker laundry basket (bottom-left) and an oak
  wash-tub with a beetle-paddle (bottom-right) as soft foreground; the side aisles' tall black
  windows; receding arches overhead; the moon window the far focal point. Eye-trace: the lit gap
  -> the dragon (his porthole's light pooled round the stool, cold rim) -> her mirror glow -> the
  plaque. ~2.75: he shifts his weight on the tiny stool (it wobbles, creaks).
  s1_glance (5.5): THOUGHT -> GLANCE: eyes flick to her (0.14 s), the head follows over 0.4 s;
  6.25 a deliberate blink -- the decision. 6.35-7.25 BREATH + TURN: he swivels round on the stool
  into near-profile toward her, straightening, a little intake of breath (sits up -- the
  anticipation). s1_lean (7.0): he LEANS across the gap (ease-out), his far hand lifts off his
  knee and opens palm-up toward her -- "may I..." -- brows up, wings lifting in hope, the mouth
  opens and STAYS open. Nothing comes out. Hold. 8.3: her far hand starts up -- cut on the reach.
SHOT B -- 8.55 -> 11.0 (s1_tap.end)   INSERT, tight, slow push
  Her lit face (lower left third), the plaque (upper right), her arm the diagonal between. Her
  eyes never leave the mirror (half-lidded, the irises down-left on the glass; runes scrolling,
  thumb idling, shells humming; one calm blink after the taps, none on them). tap (9.02), tap
  (9.42): the board jolts and rocks on its nail each time; then the finger simply stays there
  while she keeps scrolling. SELF-SERVICE large and legible, uncial lettering; the nave soft.
  At this size the mirror's light is held local (a lower key on her, a clamped spill, a higher
  bloom threshold) so her pale green-grey skin keeps its shadow side and cyan underlight, and
  the tap is one long elegant finger (a pointing hand drawn over the rig's, the rest folded).
  The moon shaft lands behind her here, so its dust is drawn soft into the far buffer.
SHOT C -- 11.0 -> 14.5   MEDIUM on him, eye level (framed high: his feet stay above the caption band)
  Cut back: he is still looking up at the sign; the hand has sunk back to his knee, the wings are
  still half-lifted. s1_l1 (11.80) "Self-service." -- read FLAT, a fact: heavy lids, no smile, no
  joke (a small, deadpan jaw); the wings sink all the way down over the line. Then the numb
  sink back (T_SINK 12.96): the eyes drop to his drum, the head follows 0.2 s later, easing
  round over 0.8 s with a blink on the turn, the body after it, landing 0.3 s behind the head.
  (Off screen she lowers her hand.) s1_lookaround: from his drum the eyes start to travel the
  row -- the next drum, the next -- the head follows, slowly, on camera... cut on the look (14.5).
SHOT D -- 14.5 -> 17.4   THE ROW (what he sees; the camera drifts along his side of the nave)
  At porthole height the camera drifts slowly down the nave beside the left arcade: drum after drum
  slides past, lids toward us, each porthole tumbling a different stranger's colourful laundry at
  its own speed, steam curling, runes breathing -- and in front of them the absence: an empty
  milking stool, a basket left on the floor, another empty stool. Nobody there. The moon window at
  the end of it all. (The far drums soft, the passing one sharp.)
SHOT E -- 17.4 -> 25.0   back on him, wider: him left, the receding nave, the elf and her sign right
  He is still looking down the rows. THOUGHT -> GLANCE -> BREATH -> LINE: his eyes go to her (she
  scrolls, oblivious), come back down the rows; a breath. s1_l2 (18.50) "That's the whole city,
  isn't it." -- quiet, to himself, near-profile, a tiny head-shake on "isn't it". The camera holds.
  His gaze sinks; T_SIGH (20.86, a beat after the line) a long sigh -- shoulders drop, eyes close,
  head bows -- and on the still camera a thin wisp of grey smoke leaves his nostrils (21.11),
  builds into a curl and hangs in the air. Only then does the camera pull back and crane up
  (21.71 -> 23.86, eased; about as fast as the old 3.5 s move at its peak): he turns back to his
  drum, small among the spinning drums, the elf scrolling across the aisle, the moon at the end.
  The tableau HOLDS still for over a second, the curl of smoke still thinning above him, to the
  hard cut to S2.

COLOUR / VALUE. Sickly cold teal-green (wisps, portholes), blue-white moonlight, blue-black vault.
His mustard scarf is the one warm note (his key light is near-neutral so it stays mustard); the
machines and furniture are pushed cold: verdigris-tarnished brass (L_BRASS), weathered grey oak
for the stools and her form (L_OAK), grey-olive barrels. Brightest values: the moon window (far),
the portholes, the wisps, her mirror -- each placed to frame a face; the far hall is held down so
the actors carry the frame; haze gathers toward the vanishing point. He is the subject: a little
more exposure and a stronger cold rim on him, a step less on her (and her mirror dims as the last
pull-back opens out). The wisps' buzz flickers the cold rim on him. Grain + teal-black vignette.

PERIOD. Romanesque vault, coursed stone, leaded night windows, caged will-o'-wisps on chains, oak-
and-brass drums with runes, wicker baskets, an oak tub and beetle, a plank form, milking stools, a
painted wooden plaque on a nail, a striped woollen stocking. Nothing modern on screen.

THE STOOL. His milking stool is drawn from inside the dragon rig (DragonPose.seat_prop): after
the coat's back flap, before the coat, his near leg and the lap -- so its little seat shows under
his bulk and its legs stand behind his shins (his far shin is clipped out of it).
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

T_SWIVEL0, T_SWIVEL1 = T_GLANCE + 0.85, T_LEAN + 0.25   # he turns on the stool toward her
T_CUT_INSERT = T_TAP + 0.25          # cut on her reach
T_CUT_BACK = T_TAP_END               # back to him, still looking up at the sign
T_REACH0, T_REACH1 = T_TAP, T_TAP + 0.5
T_HIT1 = T_TAP + 0.72                # finger contacts
T_HIT2 = T_HIT1 + 0.40
T_REST = T_HIT2 + 0.42               # ...and the finger stays on the board
# after the flat line, the numb sink back to his drum: eyes first, the head 0.2 s later (eased
# over 0.8 s, a blink on the turn), the body after the head, landing 0.3 s after it; then his
# eyes start along the row and the head follows them on camera before the cut
T_SINK = L1.end + 0.14               # the eyes drop to his drum
T_HEAD0 = T_SINK + 0.2               # the head starts round...
T_HEAD1 = T_HEAD0 + 0.8              # ...and arrives
T_BODY0 = T_HEAD0 + 0.15             # the body follows the head
T_BODY1 = T_HEAD1 + 0.3
T_ROW0 = max(T_LOOK0 + 0.75, T_HEAD1 + 0.55)   # cut to the row, on his look along it
T_ROW1 = T_LOOK1 - 0.6               # back on him, still looking down the rows
T_GLANCE2 = T_ROW1 + 0.55            # his eyes go to her before the line...
T_BACK2 = T_GLANCE2 + 0.5            # ...and back down the rows
# the button: a beat after the line, the sigh plays on the still medium-wide (the curl of smoke
# forms in front of a camera that has not moved yet); the pull-back starts as the curl completes
# and settles more than a second before the cut, so the small-among-the-drums tableau HOLDS
T_SIGH = L2.end + 0.55
T_SMOKE = T_SIGH + 0.25              # the smoke leaves his nostrils (the exhale takes ~0.9 s)
T_PULL0 = T_SIGH + 0.85              # the last pull-back (a slow ease-in: ~5 % by the curl's end)...
T_PULL1 = min(DUR - 1.1, T_PULL0 + 2.15)   # ...then held still to the cut
_SHAKE0 = next((w[1] for w in tl.word_times("s1_l2") if w[0].lower().startswith("isn")), L2.end - 0.8)

# ----------------------------------------------------------------------------------------
# the hall in 3D (units = px at scale 1.0; X right, h up from the floor, z away from camera)
# Planes facing the camera are drawn in REFERENCE coordinates (the screen at the reference
# camera) with scale s = F / z; receding surfaces are projected point by point every frame.
# ----------------------------------------------------------------------------------------
PX, PY = 960.0, 520.0               # principal point (= vanishing point of the reference view)
F = 1000.0                          # focal length (px)
HC = 540.0                          # reference eye height above the floor
NEAR = 90.0                         # near clipping distance in front of the camera

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
SOCK = (40.0, 1760.0)               # (X, z) one lost stocking on the aisle floor
SACK = (X_DRAGON - 150.0, Z_DRAGON + 25.0)   # (X, z) his emptied laundry sack, by the stool
# (X, h, z, seed): staggered left/right down the nave, so the far cages and chains never stack
# in a line over the end window -- the moon stays the one clean bright thing at the end
LAMPS = [(-150.0, 900.0, 1250.0, 0), (200.0, 980.0, 2110.0, 1), (-240.0, 1010.0, 3010.0, 2),
         (280.0, 1030.0, 3910.0, 3), (-300.0, 1040.0, 4810.0, 4)]
LINES = [(2110.0, 980.0, 11), (3010.0, 1000.0, 12), (3910.0, 1010.0, 13)]     # (z, h, seed)
# nobody there: empty stools and a forgotten basket in front of other people's drums
ABSENT = [("stool", -470.0, 2215.0, 0.45, 3), ("basket", -455.0, 2735.0, 0.0, 4),
          ("stool", -470.0, 3110.0, 0.3, 5), ("stool", 470.0, 3115.0, -0.4, 6),
          ("stool", 470.0, 4010.0, -0.25, 7)]
FG_PIECES = [("basket", -660.0, 830.0), ("tub", 690.0, 880.0)]      # (layer, X, z) on the floor

# lights
L_BASE = ch.LIGHTS["washhouse"]
L_DRAGON = L_BASE.with_(key=(0.9, 0.99, 0.95), rim=(0.70, 0.88, 1.0), rim_strength=0.8, direction=(-0.7, -0.6), exposure=1.06,
                        rim_direction=(0.55, -0.83))
# she is pale and lit by her mirror: held a step below him in value (he is the subject)
L_ELF = L_BASE.with_(rim=(0.70, 0.88, 1.0), rim_strength=0.55, rim_direction=(-0.5, -0.86), exposure=0.74)
# the insert: at ~3.8x her face would otherwise burn out under the mirror light -- a lower key so
# the pale green-grey skin, its shadow side and the cyan underlight survive
L_ELF_B = L_ELF.with_(exposure=0.74, rim_strength=0.45)
L_SET = L_BASE.with_(key=(0.62, 0.84, 0.86), ambient=(0.2, 0.32, 0.36), rim_strength=0.3)
# the machines (drums, strangers' stools): colder still -- tarnished brass and grey oak, so his
# mustard scarf stays the one warm note in the room
L_DRUM = L_BASE.with_(key=(0.47, 0.69, 0.74), ambient=(0.16, 0.28, 0.32), rim_strength=0.3)
# lights that render the props kit's warm oak (stools, her form) as weathered grey oak and its
# gold brass (the porthole rings) as tarnished, verdigris-olive brass: lit/shadow tones solved
# from the props' base colours (palette: lit = base * (1 + (key - 1) * 0.55), shadow = base * ambient)
L_OAK = L_BASE.with_(key=(0.526, 0.993, 1.914), ambient=(0.277, 0.438, 0.751), rim_strength=0.3)
L_OAK_FAR = L_OAK.with_(exposure=0.82)                       # the strangers' empty stools, down the row
L_BRASS = L_BASE.with_(key=(0.265, 0.717, 2.052), ambient=(0.208, 0.352, 0.688), rim_strength=0.3)
L_SACK = L_SET.with_(rim_strength=0.35, exposure=0.74)       # his laundry sack on the floor
_C0 = C = {
    "stone": "#2c4a4a", "stone_lt": "#3d6260", "stone_dk": "#152727", "mortar": "#0b1717",
    "vault": "#0a1415", "aisle": "#0d1a1b", "haze": "#3a6c68", "moon_glow": "#a9c4f0",
    "shaft": "#9cc4ff", "wisp": "#4dffc4", "porthole": "#5fe8d0", "mirror": "#5fe0ff",
    "oak": "#47443a", "oak_dk": "#1d1c17", "oak_lt": "#5f5c50", "brass": "#5f6a56", "hoop_dk": "#2e3228",
    "vig": (0.0, 0.025, 0.035),
}

# expressions (shared MOODS blended with these)
HOPE = B.Expr(brow_in=0.7, brow_out=0.35, brow_y=0.4, lid=0.12, lid_bot=0.04, lid_tilt=0.2, smile=0.05, pupil=1.0)
ELF_B_EYES = B.expr("bored", lid=0.42)           # her eyes in the insert: half-lidded, on the glass
FLAT = B.Expr(brow_in=0.25, brow_out=-0.18, brow_y=-0.08, lid=0.6, lid_bot=0.1, lid_tilt=0.3, smile=-0.12)


# ----------------------------------------------------------------------------------------
# camera
# ----------------------------------------------------------------------------------------

class Cam3:
    """Translation (x, y, z) in 3D units (y = down, so +y lowers the camera), zoom (focal
    multiplier), pan (sx, sy): a lens shift (the projection is shifted on the sensor), so
    vertical and horizontal lines stay true."""
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

    def eye(self):
        return (self.x, HC - self.y, self.z)

    def vp(self):
        return (PX + self.sx, PY + self.sy)

    def ahead(self, z, margin=0.0):
        return z - self.z > NEAR + margin


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
    """A camera whose lens shift puts the 3D point `aim` (X, h, z) at screen point `at`."""
    c = Cam3(cx, cy, cz, zoom)
    x, y = c.p(*aim)
    c.sx, c.sy = at[0] - x, at[1] - y
    return c


def _cam_keys(t, keys):
    """keys: [(t, (cx, cy, cz, zoom, aimX, aimH, aimZ, atx, aty)[, ease])] -> Cam3."""
    v = core.track(t, keys)
    return _framed(v[0], v[1], v[2], v[3], (v[4], v[5], v[6]), (v[7], v[8]))


def _down_nave(cx, cy, cz, vpx, vpy):
    """A camera looking straight down the nave, its vanishing point put at (vpx, vpy)."""
    return (cx, cy, cz, 1.0, cx, HC - cy, cz + 1.0e7, vpx, vpy)


_MID = (0.5 * (X_DRAGON + X_ELF), 300.0, 0.5 * (Z_DRAGON + Z_ELF))
SHOT_A = [(0.0, (0.0, -40.0, 0.0, 1.0) + _MID + (960.0, 560.0)),
          (T_CUT_INSERT, (-40.0, 170.0, 560.0, 1.0) + (_MID[0] - 40.0, 260.0, _MID[2]) + (960.0, 560.0), "inout_sine")]
_TAPPT = (X_ELF + 150.0, 330.0, Z_ELF)
SHOT_B = [(T_CUT_INSERT, (560.0, 200.0, 1150.0, 1.0) + _TAPPT + (930.0, 500.0)),
          (T_CUT_BACK, (560.0, 200.0, 1245.0, 1.0) + _TAPPT + (950.0, 490.0), "inout_sine")]
_HEAD = (X_DRAGON + 20.0, 245.0, Z_DRAGON)
# framed high enough that his feet stay above the caption band during "Self-service."
_MED = (-250.0, 285.0, 830.0, 1.0) + _HEAD + (1010.0, 342.0)
_MED2 = (-252.0, 285.0, 845.0, 1.0) + _HEAD + (1006.0, 336.0)
_MED3 = (-255.0, 285.0, 868.0, 1.0) + _HEAD + (1000.0, 330.0)
SHOT_C = [(T_CUT_BACK, _MED), (L1.end + 0.5, _MED2, "inout_sine"), (T_ROW0, _MED3, "inout_sine")]
SHOT_D = [(T_ROW0, _down_nave(-240.0, 340.0, 1480.0, 1300.0, 440.0)),       # at porthole height
          (T_ROW1, _down_nave(-240.0, 340.0, 1940.0, 1296.0, 442.0), "out_sine")]
_E1 = (-150.0, 245.0, 672.0, 1.0) + _HEAD + (486.0, 470.0)
_E2 = (-149.0, 244.0, 684.0, 1.0) + _HEAD + (488.0, 468.0)
_WIDE_END = (0.0, -80.0, 20.0, 1.0) + _MID + (960.0, 585.0)
SHOT_E = [(T_ROW1, _E1), (T_PULL0, _E2, "inout_sine"), (T_PULL1, _WIDE_END, "inout_sine")]

SHOTS = [("A", 0.0, SHOT_A), ("B", T_CUT_INSERT, SHOT_B), ("C", T_CUT_BACK, SHOT_C),
         ("D", T_ROW0, SHOT_D), ("E", T_ROW1, SHOT_E)]


def camera(t):
    name, keys = SHOTS[0][0], SHOTS[0][2]
    for nm, t0, ks in SHOTS:
        if t >= t0:
            name, keys = nm, ks
    return _cam_keys(t, keys), name


def _focus(shot, cam):
    """The depth band drawn sharp (everything deeper -> soft buffer, nearer -> softer buffer)."""
    if shot == "D":                      # fixed in world z: nothing may hop between buffers mid-move
        return 1700.0, 3000.0
    if shot == "B":
        return 1300.0, 1800.0
    return 1120.0, 1900.0


CAST_SHOTS = ("A", "B", "C", "E")        # the shots that see the actors (D looks down the row)

# ----------------------------------------------------------------------------------------
# helpers: projected polygons, near-plane clipping
# ----------------------------------------------------------------------------------------


def _poly(cr, cam, pts3, color, alpha=None):
    pts3 = _clip_z(pts3, cam.z + NEAR)
    if len(pts3) < 3:
        return
    core.polygon(cr, [cam.p(*q) for q in pts3])
    core.src(cr, color, alpha)
    cr.fill()


def _clip_z(pts3, zmin):
    """Clip a 3D polygon to z >= zmin (Sutherland-Hodgman against one plane)."""
    if all(q[2] >= zmin for q in pts3):
        return pts3
    out = []
    n = len(pts3)
    for i in range(n):
        a, b = pts3[i], pts3[(i + 1) % n]
        ia, ib = a[2] >= zmin, b[2] >= zmin
        if ia:
            out.append(a)
        if ia != ib:
            u = (zmin - a[2]) / (b[2] - a[2])
            out.append(tuple(a[j] + (b[j] - a[j]) * u for j in range(3)))
    return out


def _quad_x(cam, X, h0, h1, z0, z1):
    """A rectangle in the plane X = const (a receding wall)."""
    return [cam.p(X, h0, z0), cam.p(X, h0, z1), cam.p(X, h1, z1), cam.p(X, h1, z0)]


def _visible(cam, P3, N):
    e = cam.eye()
    return (e[0] - P3[0]) * N[0] + (e[1] - P3[1]) * N[1] + (e[2] - P3[2]) * N[2] > 0.0


def _seen(cam, X, z, soft=45.0):
    """0..1: how much of the point (X, z) the camera sees past the piers (plan view), soft at the
    edges so a glow fades rather than pops as a pier slides across it. The light layer is
    additive and knows nothing of walls: a drum hidden behind a pier must not glow through it."""
    ex, ez = cam.x, cam.z
    if z <= ez:
        return 0.0
    v = 1.0
    for zc in PIER_Z:
        z0, z1 = zc - PIER_D / 2.0, zc + PIER_D / 2.0
        za, zb = max(z0, ez), min(z1, z)
        if za >= zb:
            continue
        xa = ex + (X - ex) * (za - ez) / (z - ez)
        xb = ex + (X - ex) * (zb - ez) / (z - ez)
        lo, hi = min(xa, xb), max(xa, xb)
        for sd in (-1.0, 1.0):
            plo, phi = sorted((sd * NAVE, sd * (NAVE + PIER_W)))
            ov = min(hi, phi) - max(lo, plo)                # > 0: the sight line passes through the pier
            v = min(v, 1.0 - core.smoothstep(-soft, soft, ov))
    return v


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


def _draw_basket(c, sharp=False):
    """A wicker laundry basket heaped with linen (origin = its ground centre, 1 unit = 1 px at
    scale 1). As the soft foreground framing piece it is dark, a near-silhouette with cold light
    on its front lip; `sharp` is the small one a stranger left on the floor by a drum (shot D).
    Drawn back to front: body, weave, back rim, the heap, the front lip over the heap, handles."""
    w, h = 300.0, 200.0
    wick = "#3a3524" if sharp else "#22231b"
    wick_dk = "#1a170e" if sharp else "#0e0f0a"
    dk = 0.42 if sharp else 0.78                      # how far the linen is pushed into the shadow

    def body_path():
        c.move_to(-w / 2, -h)
        c.curve_to(-w / 2 - 6, -h * 0.45, -w / 2 + 22, -8, -w / 2 + 40, 0)
        c.line_to(w / 2 - 40, 0)
        c.curve_to(w / 2 - 22, -8, w / 2 + 6, -h * 0.45, w / 2, -h)
        c.close_path()

    body_path()
    c.set_source(core.linear(-w / 2, 0, w / 2, 0, [wick_dk, wick, core.mix(wick, wick_dk, 0.6)]))
    c.fill()
    c.save()                                          # woven rows: alternating short curved strokes
    body_path()
    c.clip()
    c.set_line_width(5.0)
    for r in range(8):
        yy = -h + 14 + r * 24
        for k in range(12):
            xx = -w / 2 + (k + 0.5 * (r % 2)) * (w / 11.0)
            core.src(c, core.tint(wick, 0.25) if (k + r) % 2 else wick_dk, 0.55)
            c.move_to(xx - 11, yy)
            c.curve_to(xx - 4, yy - 7, xx + 4, yy - 7, xx + 11, yy)
            c.stroke()
    c.restore()
    rim = core.tint(wick, 0.15)
    c.new_path()                                      # the back half of the rolled rim
    c.save()
    c.translate(0, -h)
    c.scale(1.0, 22.0 / (w / 2 + 6))
    c.arc(0, 0, w / 2 + 6, math.pi, TAU)
    c.restore()
    c.set_line_width(12)
    core.src(c, rim)
    c.stroke()
    # heaped linen, dim in the basket
    for k, col in enumerate(("#5e5262", "#8a9088", "#465a70", "#6a6a5a")):
        core.src(c, core.mix(col, "#0b1616", dk))
        core.blob(c, -96 + k * 64, -h - 8 + 12 * math.sin(k * 2.3), 54 - 4 * (k % 2), 0.32, 7, seed=k + 3)
        c.fill()
    c.new_path()                                      # the front half of the rim, over the heap
    c.save()
    c.translate(0, -h)
    c.scale(1.0, 22.0 / (w / 2 + 6))
    c.arc(0, 0, w / 2 + 6, 0.0, math.pi)
    c.restore()
    c.set_line_width(12)
    core.src(c, rim)
    c.stroke()
    for sd in (-1, 1):                                # loop handles just under the rim
        c.new_path()
        c.arc(sd * (w / 2 + 4), -h + 30, 20, 0.0, TAU)
        c.set_line_width(8)
        core.src(c, wick)
        c.stroke()
    core.src(c, core.mix("#8a9088", "#0b1616", dk))   # a shirt-sleeve hanging over the side
    core.tapered(c, [(112, -h + 4), (142, -h + 50), (136, -h + 112), (126, -h + 138)], 34, 24)
    c.fill()
    core.src(c, core.mix("#a0a69a", "#0b1616", dk), 0.85)
    core.rounded_rect(c, 112, -h + 128, 26, 16, 6)    # its cuff
    c.fill()
    # cold light catching the front lip only
    c.new_path()
    c.save()
    c.translate(0, -h + 3)
    c.scale(1.0, 22.0 / (w / 2 + 6))
    c.arc(0, 0, w / 2 + 6, 0.35, math.pi - 0.35)
    c.restore()
    c.set_line_width(4)
    core.src(c, "#6fc8b8", 0.42 if sharp else 0.28)
    c.stroke()


def _draw_tub(c):
    """Foreground oak wash-tub with a laundry beetle (paddle) leaning in it (ground centre at origin)."""
    w, h = 300.0, 170.0
    shape = [(-w / 2, -h), (w / 2, -h), (w / 2 - 22, 0), (-w / 2 + 22, 0)]
    core.polygon(c, shape)
    c.set_source(core.linear(-w / 2, 0, w / 2, 0, ["#1c1810", "#33291a", "#120f0a"]))
    c.fill()
    c.save()
    core.polygon(c, shape)
    c.clip()
    c.set_line_width(4)
    core.src(c, "#0c0a06", 0.7)
    for k in range(1, 9):                                 # staves
        u = k / 9.0
        c.move_to(-w / 2 + w * u, -h)
        c.line_to(-w / 2 + 22 + (w - 44) * u, 0)
    c.stroke()
    c.restore()
    for yy in (-h + 26, -40.0):                           # iron hoops
        core.src(c, "#0a0a0a", 0.85)
        c.rectangle(-w / 2 + 4, yy, w - 8, 13)
        c.fill()
        core.src(c, "#5fa89c", 0.18)
        c.rectangle(-w / 2 + 4, yy, w - 8, 3)
        c.fill()
    core.src(c, "#0e1a1a")
    core.ellipse(c, 0, -h, w / 2, 26)
    c.fill()
    core.src(c, "#3c6a64", 0.4)                           # the water, catching the cold light
    core.ellipse(c, 6, -h + 4, w / 2 - 22, 16)
    c.fill()
    core.src(c, "#9fe0d0", 0.25)
    core.ellipse(c, -30, -h + 2, 50, 4)
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
    core.src(c, "#5fa89c", 0.28)
    c.rectangle(-14, -258, 5, 140)
    c.fill()
    c.restore()
    core.src(c, "#5fa89c", 0.3)                           # rim light on the tub's lip
    c.set_line_width(5)
    c.move_to(-w / 2 + 6, -h - 2)
    c.line_to(w / 2 - 6, -h - 2)
    c.stroke()


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


def _aisle_window(cr, cam, sd, zc):
    """A tall round-headed night window in a side aisle's outer wall (X = sd*AISLE_X)."""
    X = sd * AISLE_X
    hw, sill, spring = 120.0, 430.0, 900.0
    if not cam.ahead(zc - hw, 20.0):
        return
    arch = [(X, spring + math.sin(math.pi * i / 12) * hw, zc - math.cos(math.pi * i / 12) * hw) for i in range(13)]
    outline = [(X, sill, zc - hw)] + arch + [(X, sill, zc + hw)]
    pts = [cam.p(*q) for q in outline]
    # the stone reveal, then the dark glass
    core.polygon(cr, [cam.p(X, sill - 18, zc - hw - 22)] + [cam.p(X, spring + math.sin(math.pi * i / 12) * (hw + 22),
                                                                   zc - math.cos(math.pi * i / 12) * (hw + 22)) for i in range(13)]
                 + [cam.p(X, sill - 18, zc + hw + 22)])
    core.src(cr, "#122425")
    cr.fill()
    core.polygon(cr, pts)
    top = cam.p(X, spring + hw, zc)
    bot = cam.p(X, sill, zc)
    cr.set_source(core.linear(0, top[1], 0, bot[1], ["#14304a", "#0c1d30", "#0a1824"]))
    cr.fill()
    # leading: a mullion and transoms
    cr.set_line_width(max(0.6, 3.0 * cam.k(zc)))
    core.src(cr, "#050c12", 0.9)
    a, b = cam.p(X, sill, zc), cam.p(X, spring + hw, zc)
    cr.move_to(*a)
    cr.line_to(*b)
    for hh in (560.0, 700.0, 840.0):
        cr.move_to(*cam.p(X, hh, zc - hw))
        cr.line_to(*cam.p(X, hh, zc + hw))
    cr.stroke()


def _aisles_and_floor(cr, cam):
    """Side-aisle outer walls (with their windows) and ceilings, then the flagstone floor
    (painted after the end wall)."""
    z0, z1 = max(cam.z + 60.0, 200.0), WALL_Z
    for sd in (-1, 1):
        X = sd * AISLE_X
        q = _quad_x(cam, X, 0.0, 1180.0, z0, z1)
        core.polygon(cr, q)
        cr.set_source(core.linear(q[0][0], 0, q[1][0], 0, ["#0d1c1d", "#0a1617"]))
        cr.fill()
        _poly(cr, cam, [(sd * NAVE, 1180.0, z0), (sd * NAVE, 1180.0, z1), (X, 1180.0, z1), (X, 1180.0, z0)], "#060d0e")
        for b in range(len(PIER_Z) - 1):
            _aisle_window(cr, cam, sd, 0.5 * (PIER_Z[b] + PIER_Z[b + 1]))
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
    if not cam.ahead(zb):
        return
    xi, xo = side * NAVE, side * (NAVE + PIER_W)
    e = cam.eye()
    dk = 0.62 if near else 0.0
    C = {k: (core.shade(v, dk) if isinstance(v, str) and k.startswith("stone") else v) for k, v in _C0.items()}
    # inner face (toward the aisle): lit by the lamps down the middle; coursed blocks
    if (e[0] - xi) * (-side) > 0:
        za = max(zf, cam.z + NEAR)
        q = _quad_x(cam, xi, 0.0, VAULT_H, za, zb)
        core.polygon(cr, q)
        cr.set_source(core.linear(0, q[2][1], 0, q[0][1], [C["stone_dk"], C["stone_lt"], C["stone"]]))
        cr.fill()
        kc = cam.k(zc)
        cr.set_line_width(max(0.6, 1.2 * kc))
        core.src(cr, C["mortar"], 0.5)
        hh, row = 64.0, 0
        while hh < VAULT_H:
            a, b = cam.p(xi, hh, za), cam.p(xi, hh, zb)
            cr.move_to(*a)
            cr.line_to(*b)
            if kc > 0.6:                                  # the vertical joints, staggered course by course
                zj = zf + PIER_D * (0.38 if row % 2 else 0.7) + 14.0 * core.hash01(row, int(zc))
                if zj > za:
                    cr.move_to(*cam.p(xi, hh, zj))
                    cr.line_to(*cam.p(xi, hh - 64.0, zj))
            hh += 64.0
            row += 1
        cr.stroke()
    # front face (toward the camera): a plane at zf, dressed with the cached stone texture
    if not cam.ahead(zf):
        return
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
    if not cam.ahead(zb):
        return
    X = side * NAVE
    zc, r = 0.5 * (za + zb), 0.5 * (zb - za)
    zmin = cam.z + NEAR
    n = 14
    curve = []
    for i in range(n + 1):
        a = math.pi * i / n
        curve.append((X, ARC_SPRING + math.sin(a) * r, zc - math.cos(a) * r))
    top = [(X, VAULT_H, zb), (X, VAULT_H, za)]
    _poly(cr, cam, curve + top, C["stone"])
    # voussoirs: a lighter band just above the intrados
    inner = [(X, ARC_SPRING + math.sin(math.pi * i / n) * r, zc - math.cos(math.pi * i / n) * r) for i in range(n + 1)]
    outer = [(X, ARC_SPRING + math.sin(math.pi * i / n) * (r + 46), zc - math.cos(math.pi * i / n) * (r + 46))
             for i in range(n, -1, -1)]
    _poly(cr, cam, inner + outer, C["stone_lt"], 0.75)
    # the soffit shadow line
    vis = [q for q in inner if q[2] >= zmin]
    if len(vis) >= 2:
        cr.set_line_width(max(0.6, 2.0 * cam.k(max(zc, zmin))))
        core.src(cr, "#050c0c", 0.7)
        cr.move_to(*cam.p(*vis[0]))
        for q in vis[1:]:
            cr.line_to(*cam.p(*q))
        cr.stroke()


def _rib(cr, cam, zc):
    """The transverse rib springing from a pier pair, across the nave (camera-facing plane)."""
    zf = zc - PIER_D / 2.0
    if not cam.ahead(zf):
        return
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


_PH = 116.0                     # half-size of the porthole texture, in lid units (ring + hinge + latch)
# the props kit's rune glyphs for the bezel (drum_porthole's band), to lay their glow in the light
# pass; a private helper of the kit, so the glow is simply skipped if it ever goes away
_RUNE_STROKES = getattr(P, "_rune_strokes", None)


def _porthole_projective(cr, cam, Cl, u_dir, sgn, light, t, seed, speed, glow, det, k, runes=1.0):
    """The porthole in TRUE perspective (close drums): drawn once into a texture in lid
    coordinates, then painted through a polar grid of small triangles (16-32 wedges x 6 rings,
    the rings on the porthole's own circles: glass, bezel, rim) whose corners are projected
    exactly. Each triangle is affine inside; the grid is exact at every corner and continuous
    across the seams (adjacent affines agree on a shared edge; the clips are aliased, so no seam
    pixel is painted twice or missed)."""
    R = DRUM_R
    dz = Cl[2] - cam.z
    near_dz = max(30.0, dz - 1.36 * R * abs(u_dir[2]))
    s_tex = core.clamp(1.15 * k * dz / near_dz, 1.0, 4.0)        # the most magnified part, ~1:1
    n_px = int(2 * _PH * s_tex) + 2
    tex = core.new_surface(n_px, n_px)
    c = core.new_context(tex)
    c.scale(s_tex, s_tex)
    c.translate(_PH, _PH + DRUM_AXLE)
    P.drum_porthole(c, 0.0, 0.0, 1.0, light, t, seed=seed, speed=speed, glow=glow, rumble=0.0, vp=None,
                    depth=(0.0, 0.0), runes=runes, detail=det)
    del c
    tex.flush()
    m_lt = cairo.Matrix(s_tex, 0.0, 0.0, s_tex, s_tex * _PH, s_tex * (_PH + DRUM_AXLE))   # lid -> texture px
    ratio = (dz - R * abs(u_dir[2])) / (dz + R * abs(u_dir[2]))     # near/far depth of the rim
    nw = int(core.clamp(16 + 50 * (0.86 - ratio), 16, 32))              # more wedges, stronger perspective
    radii = (0.0, 0.5, 0.75, 0.9, 1.0, 1.18, 1.36)                     # fine enough to stay sub-pixel

    def lid_pt(rad, a):
        ca, sa = math.cos(a), math.sin(a)
        return ((rad * R * ca, -DRUM_AXLE + rad * R * sa),
                cam.p(Cl[0] + rad * R * ca * sgn * u_dir[0], Cl[1] - rad * R * sa, Cl[2] + rad * R * ca * sgn * u_dir[2]))

    grid = [[lid_pt(rad, TAU * i / nw) for i in range(nw)] for rad in radii]
    tris = []
    for ri in range(len(radii) - 1):
        for i in range(nw):
            i2 = (i + 1) % nw
            if ri == 0:
                tris.append((grid[0][0], grid[1][i], grid[1][i2]))
            else:
                a, b = grid[ri][i], grid[ri][i2]
                c_, d = grid[ri + 1][i], grid[ri + 1][i2]
                tris.append((a, c_, d))
                tris.append((a, d, b))
    cr.save()
    cr.identity_matrix()
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    pat = cairo.SurfacePattern(tex)
    pat.set_filter(cairo.FILTER_BILINEAR)
    for (L0, S0_), (L1, S1_), (L2, S2_) in tris:
        xs, ys = (S0_[0], S1_[0], S2_[0]), (S0_[1], S1_[1], S2_[1])
        if max(xs) < 0 or min(xs) > W or max(ys) < 0 or min(ys) > H:
            continue
        # the affine that sends this triangle's three lid corners to their projections
        l1 = (L1[0] - L0[0], L1[1] - L0[1])
        l2 = (L2[0] - L0[0], L2[1] - L0[1])
        s1 = (S1_[0] - S0_[0], S1_[1] - S0_[1])
        s2 = (S2_[0] - S0_[0], S2_[1] - S0_[1])
        dl = l1[0] * l2[1] - l2[0] * l1[1]
        if abs(dl) < 1e-9:
            continue
        a00 = (s1[0] * l2[1] - s2[0] * l1[1]) / dl
        a01 = (s2[0] * l1[0] - s1[0] * l2[0]) / dl
        a10 = (s1[1] * l2[1] - s2[1] * l1[1]) / dl
        a11 = (s2[1] * l1[0] - s1[1] * l2[0]) / dl
        m_sl = cairo.Matrix(a00, a10, a01, a11, S0_[0] - a00 * L0[0] - a01 * L0[1], S0_[1] - a10 * L0[0] - a11 * L0[1])
        try:
            m_sl.invert()
        except cairo.CairoError:
            continue
        cr.save()
        cr.move_to(*S0_)
        cr.line_to(*S1_)
        cr.line_to(*S2_)
        cr.close_path()
        cr.clip()
        pat.set_matrix(m_sl.multiply(m_lt))
        cr.set_source(pat)
        cr.paint()
        cr.restore()
    cr.restore()


def _side_drum(cr, cam, side, z, t, seed, speed=1.0, glow=1.0, light=L_BRASS, rumble=1.0, exact=False):
    """An enchanted drum in a bay of the arcade, its lid toed in toward the aisle and the camera.
    The body is projected here (true perspective); the porthole -- brass ring, runes, glass,
    someone's laundry tumbling -- is the props kit's, put onto the lid's plane (exact=True: in true
    perspective when the drum is close, for the sharp focus band)."""
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
        core.src(cr, C["hoop_dk"])
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
    # the lid: the props porthole (drawn in its own lid-plane coordinates: centre (0, -130),
    # radius 92) put onto the lid in perspective
    S0 = pp(Cl)
    sgn = 1.0 if (pp((Cl[0] + u_dir[0], Cl[1], Cl[2] + u_dir[2]))[0] >= S0[0]) else -1.0   # un-mirrored
    det = 2 if k >= 0.9 else 1 if k >= 0.45 else 0
    ring = None
    if _visible(cam, Cl, n_lid):
        # one affine map fitted to the PROJECTED RIM (its first Fourier terms): the soft buffers
        # draw the porthole through it (within a few px of true perspective, and blurred anyway);
        # the light pass uses it to lay the runes' glow round the bezel
        nrim = 16
        cx_ = cy_ = mxx = mxy = myx = myy = 0.0
        for i in range(nrim):
            a = TAU * i / nrim
            ca, sa = math.cos(a), math.sin(a)
            q = pp((Cl[0] + DRUM_R * ca * sgn * u_dir[0], Cl[1] - DRUM_R * sa, Cl[2] + DRUM_R * ca * sgn * u_dir[2]))
            cx_ += q[0]
            cy_ += q[1]
            mxx += q[0] * ca
            mxy += q[0] * sa
            myx += q[1] * ca
            myy += q[1] * sa
        cx_, cy_ = cx_ / nrim, cy_ / nrim
        f2 = 2.0 / (nrim * DRUM_R)
        mxx, mxy, myx, myy = mxx * f2, mxy * f2, myx * f2, myy * f2
        m_lid = cairo.Matrix(mxx, myx, mxy, myy, cx_ + mxy * DRUM_AXLE, cy_ + myy * DRUM_AXLE)
        if exact:            # the sharp band: always in true perspective (no mode switch, no pop)
            # ...and the runes on its bezel breathe brighter: they must read on the near drums
            _porthole_projective(cr, cam, Cl, u_dir, sgn, light, t, seed, speed, glow, det, k, runes=1.7)
            ring = (m_lid, 0.5 + 0.5 * math.sin(t * 1.4 + seed * 1.3), seed)
        else:
            cr.save()
            cr.transform(m_lid)
            P.drum_porthole(cr, 0.0, 0.0, 1.0, light, t, seed=seed, speed=speed, glow=glow, rumble=0.0,
                            vp=None, depth=(0.0, 0.0), detail=det)
            cr.restore()
    # its light: hidden behind a pier -> none; nearing the camera -> fades before the drum is culled
    near = core.smoothstep(200.0, 430.0, z - cam.z)
    return (S0, DRUM_R * k, glow * _seen(cam, Cl[0], z) * near, ring)


def _drum_on_screen(cam, side, z):
    """Cull a drum only when it has really left the frame: its toed-in lid's far edge and its
    cradle feet reach well into the picture after the lid's centre has passed the camera's side.
    (Never draw one whose near edge is at the camera: the projection would blow up.)"""
    if z - cam.z < DRUM_R + 25.0:
        return False
    u_dir = (-side * math.sin(TOE), 0.0, math.cos(TOE))
    xs = []
    for sg in (-1.0, 1.0):
        for hh in (DRUM_AXLE + DRUM_R, DRUM_AXLE - DRUM_R, 0.0):
            X, zz = side * LID_X + u_dir[0] * DRUM_R * 1.12 * sg, z + u_dir[2] * DRUM_R * 1.12 * sg
            if zz - cam.z > 15.0:
                xs.append(cam.p(X, hh, zz)[0])
    return bool(xs) and max(xs) > -40.0 and min(xs) < W + 40.0


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
            # a fold down the middle, and two wooden pegs on the cord
            cr.set_line_width(max(0.5, 2.0 * s))
            core.src(cr, "#050c0c", 0.35)
            cr.move_to(px + w * 0.05, py + 3 * s)
            cr.curve_to(px + w * 0.1 + sk * 0.5, py + hh * 0.4, px - w * 0.05 + sk, py + hh * 0.7, px + sk * 0.8, py + hh * 0.92)
            cr.stroke()
            core.src(cr, "#2a2216", 0.9)
            for dx in (-0.36, 0.36):
                core.rounded_rect(cr, px + dx * w - 3 * s, py - 6 * s, 6 * s, 16 * s, 2 * s)
            cr.fill()


def _steam(cr, t, x, y, k, seed):
    """Steam curling off a drum, looping (pure function of t)."""
    period = 2.6
    for j in range(2):
        off = core.hash01(seed, 5) * period + j * period * 0.5
        t0 = math.floor((t - off) / period) * period + off
        fx.smoke(cr, t, t0, x, y, n=5, dur=3.2, rise=120.0, drift=(10.0, -4.0), size=12.0, color="#a9d8cc",
                 alpha=0.16, seed=seed * 7 + j, scale=k)


# the lost stocking, lying flat in the aisle as a sock's L (the leg, the heel's corner, the
# foot); outline points in its own little frame, 1 unit = 1 px at scale 1.0, y down
_SOCK_OUT = [(-84.0, -8.0), (-60.0, -9.5), (-36.0, -8.5), (-16.0, -9.0), (-4.0, -7.5),      # leg, top edge
             (6.0, -2.0), (13.0, 7.0), (18.0, 16.0), (22.0, 24.0),                           # the instep
             (24.0, 31.0), (20.0, 36.0), (13.0, 35.0),                                       # the toe
             (8.0, 28.0), (1.0, 20.0), (-6.0, 14.0),                                         # the sole
             (-12.0, 15.5), (-19.0, 14.5), (-24.0, 9.5), (-26.0, 5.5),                       # the heel
             (-40.0, 7.5), (-62.0, 7.0), (-84.0, 7.5), (-87.0, 0.0)]                         # leg, under edge; cuff


def _sock(cr, cam):
    """One lost striped woollen stocking in the aisle: drawn as a sock reads, the L of leg, heel
    and foot (the emoji's silhouette, lying down) with a ribbed cuff, cream stripes and the classic
    contrasting heel and toe. Projected flat onto the flagstones it was a 20 px sliver at these
    grazing angles -- a ribbon or a blade -- so it is drawn in its own camera-facing plane like
    the stools, no outline (set dressing), and kept quiet: muted cream, the faintest moonlit edge."""
    X0, Z0 = SOCK
    if not cam.ahead(Z0, 120.0):
        return
    with plane(cr, cam, Z0) as s:
        gx, gy = ref(X0, 0.0, Z0)
        cr.save()
        cr.translate(gx, gy - 10.0 * s)
        cr.scale(s, s)
        B.contact_shadow(cr, -26.0, 10.0, 66.0, 11.0, alpha=0.42)
        wool, wool_dk = "#4a5a7a", "#2c374a"
        cream, cuff = "#9c9888", "#7f7d70"
        cr.new_path()
        core.smooth_closed(cr, _SOCK_OUT, 0.55)
        shape = B.Path(cr)
        shape.add(cr)
        core.src(cr, wool)
        cr.fill()
        cr.save()
        shape.add(cr)
        cr.clip()
        shape.add(cr, 0.0, -4.0)                         # the near (lower) edge in shadow
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        cr.rectangle(-150.0, -100.0, 300.0, 200.0)
        core.src(cr, wool_dk)
        cr.fill()
        cr.set_fill_rule(cairo.FILL_RULE_WINDING)
        core.src(cr, cream)                              # heel and toe, the stripes
        core.circle(cr, -17.0, 12.5, 9.5)
        cr.fill()
        core.circle(cr, 19.0, 33.0, 10.0)
        cr.fill()
        for x0 in (-66.0, -52.0, -38.0):
            core.polygon(cr, [(x0, -12.0), (x0 + 6.0, -12.0), (x0 + 7.0, 12.0), (x0 + 1.0, 12.0)])
        cr.fill()
        core.src(cr, cuff)                               # the ribbed cuff
        core.polygon(cr, [(-90.0, -12.0), (-78.0, -12.0), (-77.0, 12.0), (-90.0, 12.0)])
        cr.fill()
        cr.set_line_width(1.0)
        core.src(cr, "#55534a", 0.8)
        for xx in (-87.0, -84.0, -81.0):
            cr.move_to(xx, -12.0)
            cr.line_to(xx + 0.5, 12.0)
        cr.stroke()
        cr.restore()
        core.src(cr, "#161c26")                          # the opening
        core.ellipse(cr, -86.0, -0.5, 1.8, 6.5)
        cr.fill()
        cr.set_line_width(1.4)
        core.src(cr, "#a9c6ee", 0.14)                    # a whisper of the moon on its far edge
        core.smooth_open(cr, _SOCK_OUT[:9], 0.55)
        cr.stroke()
        cr.restore()


# his laundry sack (the prologue's last page shows him carrying it in): emptied into his drum,
# it lies crumpled on the flagstones by his stool -- linen, its gathered neck tied with twine and
# pointing at the drum it came from, one purple sleeve still trailing out of the mouth.
# Outline points in its own frame: origin = its ground centre, 1 unit = 1 px at scale 1.0
_SACK_BODY = [(-46.0, -3.0), (-41.0, -15.0), (-27.0, -23.0), (-11.0, -21.0), (4.0, -26.0), (22.0, -32.0),
              (40.0, -31.0), (54.0, -23.0), (60.0, -10.0), (56.0, 1.0), (34.0, 5.0), (6.0, 6.0), (-24.0, 5.0)]
_SACK_NECK = [(-36.0, -11.0), (-50.0, -15.0), (-62.0, -19.0)]
_SACK_MOUTH = [(-60.0, -28.0), (-68.0, -29.0), (-75.0, -23.0), (-74.0, -14.0), (-67.0, -10.0), (-60.0, -13.0)]
_SACK_SLEEVE = [(-70.0, -17.0), (-80.0, -10.0), (-90.0, -2.0), (-101.0, 1.0)]


def _sack(cr, light, detail=2):
    """His emptied laundry sack lying by the stool (see _SACK_BODY): a prop he carried, so it is
    outlined and shaded like the cast's props, held down in value in the room's cold light (dull
    linen, a muted plum sleeve): it tells which drum is his without pulling the eye from him."""
    lw = B.line_for(B.LINE, B.device_scale(cr))
    linen = B.Mat.of("#a99e82", shadow_k=1.2)
    twine = B.Mat.of("#6e6046", shadow_k=1.1)
    plum = B.Mat.of("#76566e", shadow_k=1.25)
    B.contact_shadow(cr, 2.0, 3.0, 78.0, 10.0, alpha=0.55)
    # the sleeve trails out of the mouth onto the floor (behind the frill)
    sp, so = B.taper_paths(cr, _SACK_SLEEVE, 11.0, 9.0, lw)
    B.shade(cr, sp, plum, light, lw, outline=so, size=10, rim=0.4)
    cuff = _SACK_SLEEVE[-1]
    cp, co = B.ellipse_paths(cr, cuff[0] - 1.0, cuff[1] - 0.5, 4.0, 5.5, lw, 0.3)
    B.shade(cr, cp, B.Mat.of("#8a7a8c", shadow_k=1.1), light, lw, outline=co, size=6, rim=0.4)
    # the crumpled body, its gathered neck and the frill of the mouth: one union of linen
    bs, bo = B.smooth_paths(cr, _SACK_BODY, lw, 0.85)
    ns, no = B.taper_paths(cr, _SACK_NECK, 18.0, 12.0, lw, cap=False)
    ms, mo = B.smooth_paths(cr, _SACK_MOUTH, lw, 0.9)
    B.fill_outlines(cr, [bo, no, mo], B.palette(light, linen).line)
    cr.new_path()
    bs.add(cr)
    ns.add(cr)
    ms.add(cr)
    p = B.shade(cr, B.Path(cr), linen, light, lw, outline=False, size=34, rim=0.5)
    # the mouth's dark inside, the sleeve going into it
    core.src(cr, p.deep, 0.85)
    core.ellipse(cr, -68.5, -19.5, 3.6, 6.0, 0.25)
    cr.fill()
    # twine round the neck
    tw = []
    for k, u in enumerate((0.4, 0.62)):
        x = _SACK_NECK[0][0] + (_SACK_NECK[-1][0] - _SACK_NECK[0][0]) * u
        y = _SACK_NECK[0][1] + (_SACK_NECK[-1][1] - _SACK_NECK[0][1]) * u
        tw.append([(x + 2.0, y - 8.0 + k), (x - 1.0, y), (x + 1.5, y + 7.0 - k)])
    B.detail_lines(cr, tw, lw * 1.4, B.palette(light, twine).lit, 0.95, taper=(0.8, 1.0, 0.8))
    if detail >= 1:
        # the folds of the empty linen, gathered toward the neck
        folds = [[(-36.0, -14.0), (-22.0, -16.0), (-6.0, -14.0)],
                 [(-34.0, -5.0), (-8.0, -6.0), (22.0, -9.0), (44.0, -15.0)],
                 [(6.0, -21.0), (24.0, -26.0), (42.0, -25.0)]]
        B.detail_lines(cr, folds, lw * 0.9, p.line, 0.6)


def _sigh_smoke(cr, t, t0, x, y, s, d):
    """The sigh: a curl of grey smoke from his nostrils at t0 -- exhaled forward in a lazy S, the
    tip curling over into a loop, then it hangs, swells, rises and thins away (drawn in his
    plane, so it stays put in the air as the camera moves). It is painted into a small
    device-space buffer and blurred, so it is soft like smoke, not a brush stroke.
    (x, y) the nostril, s his scale, d = +1/-1 the way his snout points."""
    T_EX, T_LIFE = 0.9, 5.2                         # the exhale, then how long it hangs
    if t < t0 or t > t0 + T_LIFE:
        return
    a = t - t0
    grow = core.out_cubic(core.clamp(a / T_EX))     # how much of the curl has left his nostrils
    if grow < 0.02:
        return
    # it hangs on into the held final wide, thinning slowly
    fade = core.clamp(1.0 - (a - 1.6) / (T_LIFE - 1.6)) ** 1.3
    # a wisp first, never a puff: while the curl is short all its segments lie on top of each
    # other, so their alpha and width build with how much of it is out
    g_alpha, g_width = grow ** 0.7, 0.35 + 0.65 * grow
    swell = 1.0 + 1.1 * core.clamp(a / T_LIFE)      # it thickens and loosens as it hangs
    rise = 9.0 * a + 4.0 * a * a                    # ...and drifts up, slowly
    drift = 7.0 * a
    n = 28
    L = 120.0
    th0 = -0.35                                     # leaving ~20 degrees up from the snout line
    kc = 10.0 + 2.0 * core.clamp(a / T_LIFE)        # the loop tightens a little as it hangs
    pts = []
    px, py = 0.0, 0.0
    ds = L * grow / (n - 1)
    for i in range(n):
        u = i / (n - 1)
        ux, uy = cr.user_to_device(x + d * (px + drift * u) * s, y + (py - rise * (0.4 + 0.6 * u)) * s)
        pts.append((ux, uy, u))
        uu = u * grow
        th = th0 - 0.55 * math.sin(uu * math.pi * 1.3) - kc * max(0.0, uu - 0.5) ** 1.6
        px += math.cos(th) * ds
        py += math.sin(th) * ds
    sd = abs(cr.user_to_device_distance(s, 0.0)[0])        # device px per unit of his scale
    wmax = (2.6 + 7.5) * swell * 3.2 * sd
    pad = wmax + 6.0 * sd + 8.0
    x0 = int(min(p[0] for p in pts) - pad)
    y0 = int(min(p[1] for p in pts) - pad)
    x1 = int(max(p[0] for p in pts) + pad)
    y1 = int(max(p[1] for p in pts) + pad)
    if x1 < 0 or y1 < 0 or x0 > W or y0 > H or x1 - x0 > 1400 or y1 - y0 > 1400:
        return
    buf = core.new_surface(x1 - x0, y1 - y0)
    c = core.new_context(buf)
    c.translate(-x0, -y0)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    # three passes (wide and faint -> narrow and brighter), each tapered along its length
    for wk, ak, col in ((3.0, 0.12, "#93a6a4"), (1.8, 0.2, "#afbfbc"), (0.8, 0.3, "#d0dad7")):
        for j in range(n - 1):
            (ax_, ay_, u0), (bx_, by_, u1) = pts[j], pts[j + 1]
            um = 0.5 * (u0 + u1)
            w = (2.6 + 7.5 * um ** 0.8) * swell * wk * sd * g_width
            al = ak * fade * g_alpha * (0.35 + 0.65 * min(1.0, um * 3.0)) * (1.0 - 0.45 * um * core.clamp(a - 1.0))
            c.set_line_width(max(0.8, w))
            core.src(c, col, al)
            c.move_to(ax_, ay_)
            c.line_to(bx_, by_)
            c.stroke()
    # a soft puff where the curl turns over
    hx, hy, _ = pts[int((n - 1) * 0.8)]
    r = (18.0 + 12.0 * core.clamp(a / T_LIFE)) * swell * sd * grow
    if r > 1.0:
        pat = cairo.RadialGradient(hx, hy, 0, hx, hy, r)
        cc = core.col("#c3cecc")
        pat.add_color_stop_rgba(0.0, cc[0], cc[1], cc[2], 0.2 * fade * core.smoothstep(0.15, 0.6, a))
        pat.add_color_stop_rgba(1.0, cc[0], cc[1], cc[2], 0.0)
        c.set_source(pat)
        c.arc(hx, hy, r, 0, TAU)
        c.fill()
    del c
    soft = fx.blur_surface(buf, max(1.0, (1.6 + 1.2 * core.clamp(a / T_LIFE)) * sd))
    cr.save()
    cr.identity_matrix()
    cr.set_source_surface(soft, x0, y0)
    cr.paint()
    cr.restore()


def _stool_under(cr, proj, feet, t, yaw, wobble):
    """His milking stool, drawn from inside the dragon rig (DragonPose.seat_prop): after his far
    leg and the coat's back flap, before the coat, his near leg and the lap -- so the little seat
    shows under his bulk, in front of the coat tail, and its legs stand behind his shins (the near
    one is drawn over it). Body-local coords: origin = the ground under his pelvis, scale 1. His
    far shin and foot were drawn before it but are nearer the camera than any of it: clipped out."""
    far = 1.0 if proj.yaw >= 0 else -1.0
    cr.save()
    for f in feet:
        if f["side"] != far:
            continue
        a = f["ankle"]
        kn, an = proj.xy(f["knee"]), proj.xy(a)
        toe = proj.xy((a[0], a[1] + 14.0, a[2] + 34.0))
        for (p0, r0, p1, r1) in ((kn, 17.0, an, 13.0), (an, 14.0, toe, 13.0)):
            cr.new_path()
            cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cr.rectangle(-700.0, -700.0, 1400.0, 1400.0)
            core.capsule(cr, p0[0], p0[1], r0, p1[0], p1[1], r1)
            cr.clip()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    cr.new_path()
    P.draw_stool(cr, 0.0, 0.0, 1.0, L_OAK, t, yaw=yaw, wobble=wobble)
    cr.restore()


# ----------------------------------------------------------------------------------------
# acting
# ----------------------------------------------------------------------------------------

_YAW_KEYS = [
    (0.0, -0.75), (T_SWIVEL0, -0.75), (T_SWIVEL1, 0.88, "inout_sine"), (T_CUT_INSERT, 0.92),
    (T_CUT_BACK - 0.5, 0.42, "inout_sine"),                                  # (during the insert)
    (T_BODY0, 0.42), (T_BODY1, -0.32, "inout_sine"),                         # back toward his drum
    (T_ROW1 - 0.4, 0.36, "inout_sine"),                                      # opens to the nave (off)
    (T_SIGH + 1.5, 0.34), (T_SIGH + 3.1, -0.62, "inout_sine"), (DUR, -0.64)]


def _body_yaw(t):
    """His body yaw (absolute, rad): -0.75 = 3/4 left watching his drum; +0.88 = near-profile
    toward her for the lean; +0.42 = 3/4 right looking up at the sign; +0.38 open to the nave."""
    return core.track(t, _YAW_KEYS)


def _tail_side(y):
    """Which way the rig lays a seated tail out along the floor for body yaw y (dragon.py's
    _tail_spine: toward the side the camera sees best), -1..1."""
    return core.clamp(0.6 * math.cos(y) - 1.3 * math.sin(y), -1.0, 1.0)


_TAIL_DT, _TAIL_N = 1.0 / 48.0, 72
_TAIL_W = [B.spring((k + 1) * _TAIL_DT, 0.0, 1.3, 0.6) - B.spring(k * _TAIL_DT, 0.0, 1.3, 0.6) for k in range(_TAIL_N)]
_TAIL_W = [w / sum(_TAIL_W) for w in _TAIL_W]


def _tail_drag(t):
    """Overlapping action for the tail: the rig slaves the tail's side to the body yaw, so a turn
    through the front view flips it across in a frame or two. Its side follows a sprung, lagging
    copy of the yaw instead (the impulse response of a 1.3 Hz spring, ~0.2 s late, a little
    overshoot), handed to tail_swing as the difference: the tip trails the turn and swings over."""
    y_lag = sum(w * _body_yaw(t - k * _TAIL_DT) for k, w in enumerate(_TAIL_W))
    return core.clamp(5.0 * (_tail_side(y_lag) - _tail_side(_body_yaw(t))), -2.6, 2.6)


def _dragon_pose(t):
    """The dragon's performance. Eyes lead, the head follows, the body last.
    Body yaw (absolute, rad): -0.75 = 3/4 left watching his drum; +0.88 = near-profile toward her
    for the lean; +0.42 = 3/4 right looking up at the sign; +0.38 open to the nave."""
    yaw = _body_yaw(t)
    # the tiny head-shake on "isn't it"
    shake = 0.065 * math.sin((t - _SHAKE0) * TAU * 2.3) * core.window(t, _SHAKE0 - 0.05, L2.end + 0.05, 0.12, 0.25)
    # where his head points (absolute yaw)
    head_yaw = core.track(t, [
        (0.0, -0.95), (T_GLANCE + 0.12, -0.95), (T_GLANCE + 0.55, 0.35, "inout_sine"),
        (T_SWIVEL1, 0.98), (T_CUT_INSERT, 1.0),
        (T_CUT_BACK, 0.55), (T_HEAD0, 0.5),
        (T_HEAD1, -0.92, "inout_sine"),                                          # down to his own drum
        (T_HEAD1 + 0.22, -0.89), (T_ROW0 + 0.45, -0.42, "inout_sine"),           # ...drum after drum
        (T_ROW1 - 0.3, 0.92, "inout_sine"),                                      # (off) down the nave
        (T_GLANCE2 - 0.05, 0.92), (T_GLANCE2 + 0.3, 1.12, "inout_sine"),         # a look at her
        (T_BACK2, 1.12), (T_BACK2 + 0.35, 0.95, "inout_sine"),                   # back down the rows
        (L2.start + 0.6, 1.0), (L2.end + 0.25, 0.92),
        (L2.end + 1.0, 0.72, "inout_sine"), (T_SIGH + 1.5, 0.58),
        (T_SIGH + 3.0, -0.48, "inout_sine"), (DUR, -0.52)]) + shake
    head_turn = core.clamp((head_yaw - yaw) / 1.1, -1.0, 1.0)
    look = core.track(t, [
        (0.0, (-0.55, 0.55)), (2.2, (-0.5, 0.62)), (3.4, (-0.58, 0.5)), (T_GLANCE, (-0.58, 0.5)),
        (T_GLANCE + 0.14, (0.9, -0.1), "out_cubic"),
        (T_LEAN, (0.85, -0.05)), (T_CUT_INSERT, (0.85, -0.02)),
        (T_CUT_BACK - 0.3, (0.75, -0.32), "inout_sine"),                        # up at the sign
        (L1.start - 0.1, (0.75, -0.3)), (T_SINK, (0.62, -0.18)),
        (T_SINK + 0.32, (-0.78, 0.58), "inout_sine"),                            # eyes sink to his drum
        (T_HEAD0 + 0.1, (-0.78, 0.58)),
        (T_HEAD1, (-0.3, 0.5), "inout_sine"),                                    # (the head catches up)
        (T_HEAD1 + 0.1, (-0.3, 0.5)),
        (T_HEAD1 + 0.22, (0.12, 0.38), "out_cubic"), (T_HEAD1 + 0.42, (0.15, 0.36)),   # the next drum
        (T_HEAD1 + 0.54, (0.45, 0.24), "out_cubic"), (T_ROW0, (0.5, 0.22)),       # the next...
        (T_ROW1 - 0.2, (0.75, 0.05), "inout_sine"),
        (T_GLANCE2, (0.75, 0.05)), (T_GLANCE2 + 0.12, (0.95, 0.12), "out_cubic"),  # her
        (T_BACK2, (0.95, 0.12)), (T_BACK2 + 0.14, (0.7, 0.08), "out_cubic"),     # the rows
        (L2.start + 0.3, (0.72, 0.05)), (L2.end, (0.68, 0.12)),
        (L2.end + 0.6, (0.35, 0.58), "inout_sine"), (T_SIGH + 1.6, (0.25, 0.6)),
        (T_SIGH + 2.9, (-0.6, 0.55), "inout_sine"), (DUR, (-0.6, 0.55))])
    watch = 1.0 - core.ramp(t, T_GLANCE - 0.4, T_GLANCE, "inout_sine") + core.ramp(t, T_SIGH + 3.0, T_SIGH + 3.6, "inout_sine")
    if watch > 0.0:                                   # his eyes ride the tumbling laundry, round and round
        ph = t * TAU * 0.33
        look = (look[0] + 0.07 * math.cos(ph) * watch, look[1] + 0.06 * math.sin(ph) * watch)
    head_nod = core.track(t, [
        (0.0, -0.3), (T_GLANCE + 0.15, -0.3), (T_GLANCE + 0.55, 0.0, "inout_sine"),
        (T_LEAN - 0.3, 0.08), (T_LEAN + 0.5, 0.0, "inout_sine"), (T_CUT_INSERT, 0.0),
        (T_CUT_BACK, 0.12), (L1.start, 0.12), (L1.end - 0.15, 0.04), (T_HEAD0, 0.0),
        (T_HEAD1, -0.25, "inout_sine"), (T_ROW0, -0.12, "inout_sine"), (T_ROW1, 0.0),
        (L2.end, -0.05), (L2.end + 1.0, -0.28, "inout_sine"), (DUR, -0.32)])
    # the lean: a little intake (sits up) -> leans across the gap toward her (ease-out) -> holds
    lean = core.track(t, [
        (0.0, 0.0), (2.4, 0.0), (2.75, 0.12, "inout_sine"), (3.2, -0.02, "inout_sine"), (3.6, 0.0),
        (T_SWIVEL1 - 0.4, 0.0), (T_LEAN + 0.25, -0.16, "inout_sine"),          # the intake: sits up
        (T_LEAN + 0.9, 1.08, "out_cubic"), (T_CUT_INSERT, 1.16),
        (T_CUT_BACK - 0.5, 0.25, "inout_sine"), (L1.end + 0.5, 0.15), (T_LOOK0 + 0.6, 0.0, "inout_sine"),
        (T_ROW1, 0.05), (T_SIGH, 0.08), (T_SIGH + 1.2, 0.22, "inout_sine"), (DUR, 0.15)])
    hunch = core.track(t, [(0.0, 0.9), (T_SWIVEL0, 0.88), (T_LEAN + 0.2, 0.5, "inout_sine"), (T_CUT_INSERT, 0.55),
                           (T_CUT_BACK, 0.72), (L1.end + 0.6, 0.95, "inout_sine"), (T_SIGH, 0.95),
                           (T_SIGH + 1.6, 1.05, "inout_sine"), (DUR, 1.05)])
    wings = core.track(t, [(0.0, -0.9), (T_LEAN + 0.1, -0.9), (T_LEAN + 0.9, 0.3, "out_cubic"), (T_CUT_INSERT, 0.32),
                           (T_CUT_BACK, 0.05, "inout_sine"), (L1.start, 0.0), (L1.end + 0.5, -1.0, "inout_sine"),
                           (DUR, -1.0)])
    # the aborted line: the mouth opens and stays open -- nothing comes out
    gape = core.track(t, [(T_LEAN + 0.4, 0.0), (T_LEAN + 0.7, 0.3, "out_cubic"), (T_CUT_INSERT + 0.2, 0.3),
                          (T_CUT_INSERT + 0.6, 0.0, "inout_sine")])
    # both lines are quiet and flat: a deadpan jaw (half the envelope's size, the dips between
    # syllables pressed toward closed so the consonants articulate), never the laugh-sized gape
    env = tl.talk(SCENE, t, "MAN")
    talk = max(0.58 * core.smoothstep(0.25, 0.95, env), gape)
    hope = core.window(t, T_LEAN - 0.1, T_CUT_INSERT + 0.4, 0.5, 0.3)
    sigh = core.window(t, T_SIGH, T_SIGH + 2.6, 0.55, 1.4)
    blink = None
    for tb in (T_GLANCE + 0.75, T_HEAD0 + 0.04, T_ROW1 + 0.22):
        if tb <= t <= tb + 0.2:
            blink = core.window(t, tb, tb + 0.2, 0.06, 0.12)
        elif blink is None and abs(t - tb) < 0.9:
            blink = 0.0                     # no automatic blink crowding a deliberate one
    if T_LEAN - 0.4 <= t <= T_CUT_INSERT + 0.2 and blink is None:
        blink = 0.0                         # wide-eyed hope: no blink in the held lean
    if L2.end - 0.2 <= t <= T_SIGH + 1.2 and blink is None:
        blink = 0.0                         # the sigh closes his eyes: no blink crowding it
    mood, mood2, mix = "lonely", HOPE, hope * 0.75
    if t >= T_CUT_BACK - 0.3:
        mood, mood2, mix = "tired", FLAT, 0.75 * (1.0 - core.ramp(t, L1.end + 0.6, T_LOOK0, "inout_sine"))
        if t >= L1.end + 0.6:
            mood, mood2, mix = "tired", "sad", core.ramp(t, L1.end + 0.6, T_LOOK0, "inout_sine") * 0.6
    if t >= T_ROW1 - 0.3:
        mood, mood2, mix = "tired", "lonely", core.ramp(t, T_ROW1 - 0.3, L2.start + 0.4)
    tail_swing = -0.25 + 0.12 * B.sway(t, 0.21, 11) + 0.3 * B.wobble(t, T_LEAN + 0.5, 1.6, 2.2) + _tail_drag(t)
    # the attempt: his far hand lifts off the knee and opens palm-up toward her ("may I...")
    reach = core.track(t, [(T_LEAN + 0.2, 0.0), (T_LEAN + 0.95, 1.0, "out_cubic"), (T_CUT_INSERT + 0.1, 1.0),
                           (T_CUT_BACK - 0.8, 0.0, "inout_sine")])
    far = ch.Arm("hand_out_offer", amt=reach, prev="rest") if reach > 0.001 else ch.Arm("rest")
    return ch.DragonPose(facing=0, turn=yaw / 0.6, sit=1.0, seat_h=STOOL_H, hunch=hunch, lean=lean,
                         head_turn=head_turn, head_nod=head_nod, look=look, mood=mood, mood2=mood2,
                         mood_mix=mix, talk=talk, sigh=sigh, blink=blink, wings=wings, tail_curl=0.55,
                         tail_swing=tail_swing, far=far, seed=3)


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


T_WITHDRAW0, T_WITHDRAW1 = L1.end + 0.55, L1.end + 1.35     # (off screen) after his line, not over it


def _elf_pose(t, tap_target):
    reach = core.ramp(t, T_REACH0, T_REACH1, "inout_sine") * (1.0 - core.ramp(t, T_WITHDRAW0, T_WITHDRAW1, "inout_sine"))
    far = (ch.ElfArm("tap_sign", amt=reach, prev="rest", phase=0.95, screen=tap_target)
           if reach > 0 and tap_target is not None else ch.ElfArm("rest"))
    tilt = 0.05 * B.sway(t, 0.12, 41) - 0.04
    groove = 0.035 * math.sin(t * TAU * 1.15) * (1.0 - core.window(t, T_TAP - 0.2, T_WITHDRAW1 + 0.3, 0.3, 0.4))
    return ch.ElfPose(facing=-1, sit=1.0, glow=1.0, shells=0.8 + 0.2 * (0.5 + 0.5 * math.sin(t * TAU * 1.15)),
                      look=(-0.12 + 0.05 * B.sway(t, 0.3, 4), 0.92), head_nod=-0.42 + groove, head_tilt=tilt,
                      near=ch.ElfArm("mirror", phase=t * 0.3), far=far, seed=5)


def _hand_matrix(hf):
    """The base.hand frame of a rig's HandFrame as a matrix: hand units (wrist at the origin, +u
    along the fingers, +v toward the little finger, 1 = the hand's length) -> the caller's
    coordinates (base.hand: translate(wrist), rotate(angle), scale(s, s * flip))."""
    s = hf.scale
    fy = -1.0 if hf.flip else 1.0
    ca, sa = math.cos(hf.angle), math.sin(hf.angle)
    wx, wy = hf.palm[0] - s * 0.21 * ca, hf.palm[1] - s * 0.21 * sa          # palm = wrist + 0.21 along
    return cairo.Matrix(s * ca, s * sa, -s * fy * sa, s * fy * ca, wx, wy)


def _point_hand(cr, hf, mat, light, lw):
    """The insert's tapping hand, drawn over the rig's (whose own is clipped away beyond the
    wrist): at ~3.8x the house 3-finger hand's curled fingers fold sideways in the picture plane
    and read as a V. Here: one long tapered index finger to the rig's own fingertip (so the tap
    lands where the reach was solved), the other fingers folded under the knuckles as a soft
    fist-lobe, the thumb tucked along the side; one outline, the house shading, a little ink."""
    m = _hand_matrix(hf)
    inv = cairo.Matrix(*m)
    inv.invert()
    tx, ty = inv.transform_point(*hf.tips[0])                     # the index tip, in hand units
    lw_h = lw / hf.scale
    cr.save()
    cr.transform(m)
    back = [(-0.04, -0.125), (0.10, -0.142), (0.26, -0.150), (0.40, -0.136), (0.47, -0.092),
            (0.505, -0.02), (0.50, 0.06), (0.46, 0.13), (0.36, 0.165), (0.20, 0.158), (0.06, 0.135), (-0.04, 0.115),
            (-0.075, 0.0)]
    lobe = [(0.42 + 0.115 * math.cos(a), 0.095 + 0.105 * math.sin(a)) for a in (TAU * i / 14 for i in range(14))]
    k0 = (0.44, -0.082)
    dx, dy = tx - k0[0], ty - k0[1]
    Lf = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / Lf, dx / Lf
    j1 = (k0[0] + dx * 0.52 - nx * 0.012, k0[1] + dy * 0.52 - ny * 0.012)
    th0, th1 = (0.13, -0.118), (0.34, -0.112)

    def add_shape(d):
        core.smooth_closed(cr, B.offset_closed(back, d) if d else back, 0.8)
        core.smooth_closed(cr, B.offset_closed(lobe, d) if d else lobe, 0.9)
        core.capsule(cr, k0[0], k0[1], 0.066 + d, j1[0], j1[1], 0.056 + d)
        core.capsule(cr, j1[0], j1[1], 0.056 + d, tx, ty, 0.043 + d)
        core.capsule(cr, th0[0], th0[1], 0.052 + d, th1[0], th1[1], 0.043 + d)
    p = B.palette(light, mat)
    cr.new_path()
    add_shape(lw_h)
    core.src(cr, p.line)
    cr.fill()
    # the hand (back, folded fingers, thumb), then the finger with its own, slimmer crescent
    core.smooth_closed(cr, back, 0.8)
    core.smooth_closed(cr, lobe, 0.9)
    core.capsule(cr, th0[0], th0[1], 0.052, th1[0], th1[1], 0.043)
    B.shade(cr, B.Path(cr), mat, light, lw_h, rim=0.5, size=0.32, shadow=2.3, outline=False)
    cr.save()
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cr.rectangle(-2.0, -2.0, 4.0, 4.0)
    core.smooth_closed(cr, back, 0.8)
    cr.clip()
    cr.set_fill_rule(cairo.FILL_RULE_WINDING)
    core.capsule(cr, k0[0], k0[1], 0.066, j1[0], j1[1], 0.056)
    core.capsule(cr, j1[0], j1[1], 0.056, tx, ty, 0.043)
    B.shade(cr, B.Path(cr), mat, light, lw_h, rim=0.5, size=0.12, shadow=1.8, outline=False)
    cr.restore()
    ux, uy = dx / Lf, dy / Lf
    lines = [[(0.37, 0.03), (0.45, 0.05), (0.52, 0.08)],                     # the folded fingers
             [(0.40, 0.11), (0.47, 0.135), (0.52, 0.15)],
             [(0.17, -0.09), (0.27, -0.082), (0.35, -0.085)],                 # the thumb's edge
             [(j1[0] - nx * 0.03 - ux * 0.02, j1[1] - ny * 0.03 - uy * 0.02), j1,  # the middle joint
              (j1[0] + nx * 0.03 - ux * 0.02, j1[1] + ny * 0.03 - uy * 0.02)]]
    B.detail_lines(cr, lines, lw_h * 0.85, p.line, 0.6)
    cr.restore()


def _elf_light(t):
    """Her light in the wides: a step below him, and a little lower again as the last pull-back
    opens out, so the small hunched dragon holds the final frame. Quantised to 1 % steps (the
    palettes are cached per light; the steps are lost in the grain)."""
    k = round(core.ramp(t, T_PULL0 + 0.5, T_PULL1, "inout_sine") * 10.0) / 10.0
    return L_ELF if k <= 0.0 else L_ELF.with_(exposure=L_ELF.exposure - 0.08 * k)


def _mirror_dim(t):
    """Her mirror's light: steady, then a little lower as the camera pulls back at the end, so the
    small hunched dragon -- not her glow -- holds the final frame."""
    return 1.0 - 0.35 * core.ramp(t, T_PULL0 + 0.5, T_PULL1, "inout_sine")


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


def _wisp_level(t, seed):
    """The flicker of wisp lamp `seed` (the same formula the props kit uses), for the rim it casts."""
    buzz = core.noise1(t * 0.9, seed + 2)
    lv = 0.86 + 0.08 * core.noise1(t * 9.0, seed) + 0.04 * math.sin(t * 50.0 + seed)
    if buzz > 0.55:
        lv *= 0.6 + 0.4 * abs(math.sin(t * 31.0))
    return lv


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
    x0, ytop = ref(-AISLE_X - 400, 2400.0, WALL_Z)
    x1, yfl = ref(AISLE_X + 400, 0.0, WALL_Z)
    st["wall"] = fx.Layer(_draw_end_wall, w=x1 - x0, h=yfl - ytop + 4, x=x0, y=ytop, blur=1.0)
    st["basket"] = fx.Layer(_draw_basket, w=420, h=420, x=-210, y=-330, blur=3.0, res=0.5)
    st["tub"] = fx.Layer(_draw_tub, w=460, h=520, x=-230, y=-440, blur=3.0, res=0.5)
    st["basket_sharp"] = fx.Layer(lambda c: _draw_basket(c, sharp=True), w=420, h=420, x=-210, y=-330, blur=0.6)
    st["bg"] = {"A": _Buf(0.55), "B": _Buf(0.4), "C": _Buf(0.46), "D": _Buf(0.5), "E": _Buf(0.46)}
    st["fg"] = {"A": _Buf(0.33, opaque=False), "B": _Buf(0.3, opaque=False), "C": _Buf(0.3, opaque=False),
                "D": _Buf(0.3, opaque=False), "E": _Buf(0.3, opaque=False)}
    # the plaque, in the reference coordinates of pier 1's front face
    st["plaque_xy"] = ref(X_PLAQUE, H_NAIL, Z_PLAQUE)
    st["plaque_s"] = F / Z_PLAQUE
    scratch = core.frame(8, 8)[1]
    pq = P.draw_plaque(scratch, *st["plaque_xy"], "SELF-SERVICE", st["plaque_s"], L_SET, 0.0, size=30.0)
    st["plaque_rig"] = pq
    st["reach"] = _solve_reach(st)
    # where the sigh leaves his nostrils (fixed in his plane, so the curl stays in the air)
    ts = T_SMOKE
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


def _items(cam, shot, t, st, out):
    """Every drawable as (depth, fn(ctx, soft)), in no particular order. `out` collects light
    sources for the light pass."""
    items = []
    cast = shot in CAST_SHOTS
    # piers, ribs, arcades
    for i, zc in enumerate(PIER_Z):
        for side in (-1, 1):
            items.append((zc - PIER_D / 2.0, lambda c, soft, side=side, zc=zc: _pier(c, cam, side, zc, near=soft == "fg")))
        items.append((zc - PIER_D / 2.0 - 0.5, lambda c, soft, zc=zc: _rib(c, cam, zc)))
    for b in range(len(PIER_Z) - 1):
        za, zb = PIER_Z[b] + PIER_D / 2.0, PIER_Z[b + 1] - PIER_D / 2.0
        d = 0.5 * (max(za, cam.z + NEAR) + zb)            # the visible part's middle
        for side in (-1, 1):
            items.append((d, lambda c, soft, side=side, za=za, zb=zb: _arcade(c, cam, side, za, zb)))
    # drums
    for side, z, seed, spd, bb, j in DRUMS:
        if not _drum_on_screen(cam, side, z):
            continue
        if shot == "B" and side > 0 and bb == 0:      # the insert: no drum looming under her
            continue

        def drum(c, soft, side=side, z=z, seed=seed, spd=spd, bb=bb, j=j):
            g = 1.0 if soft == "mid" else 0.8 if soft == "fg" else 0.7
            r = _side_drum(c, cam, side, z, t, seed, spd, glow=g, exact=(soft == "mid"))
            out["drums"].append(r)
            if side < 0 and bb == HIS_BAY and j == HIS_SLOT:
                out["his"] = r
            if soft == "mid":
                top = cam.p(side * (LID_X + BARREL * 0.4), DRUM_AXLE + DRUM_R, z + 30.0)
                _steam(c, t, top[0], top[1], cam.k(z), seed)
        items.append((z, drum))
    # drying lines and lamps
    for (zl, hl, sdl) in LINES:
        if cam.ahead(zl, 60.0):
            items.append((zl, lambda c, soft, zl=zl, hl=hl, sdl=sdl: _drying_line(c, cam, zl, hl, t, sdl)))
    for (X, h, z, sd) in LAMPS:
        if not cam.ahead(z, 60.0):
            continue

        def lamp(c, soft, X=X, h=h, z=z, sd=sd):
            with plane(c, cam, z) as s:
                lx, ly = ref(X, h, z)
                out["lamps"].append((P.draw_wisp_lamp(c, lx, ly, s, L_SET, t, seed=sd, top=ref(0, 2400, z)[1]), z))
        items.append((z, lamp))
    # nobody there: empty stools and a basket by other people's drums
    for kind, X, z, yaw, sd in ABSENT:
        if not cam.ahead(z, 80.0):
            continue

        def absent(c, soft, kind=kind, X=X, z=z, yaw=yaw):
            with plane(c, cam, z) as s:
                gx, gy = ref(X, 0.0, z)
                if kind == "stool":
                    B.contact_shadow(c, gx, gy + 2 * s, 60 * s, 10 * s, alpha=0.45)
                    P.draw_stool(c, gx, gy, s, L_OAK_FAR, t, yaw=yaw)
                else:
                    c.translate(gx, gy)
                    c.scale(s * 0.42, s * 0.42)
                    B.contact_shadow(c, 0, 4, 170, 24, alpha=0.5)
                    st["basket_sharp"].paint(c)
        items.append((z, absent))
    if cast:
        # the plaque on pier 1 (just in front of the pier's face)
        def plaque(c, soft):
            with plane(c, cam, Z_PLAQUE) as s:
                P.draw_plaque(c, *st["plaque_xy"], "SELF-SERVICE", s, L_SET, t, taps=(T_HIT1, T_HIT2),
                              swing=0.006 * math.sin(t * 0.9), size=30.0)
        items.append((Z_PLAQUE - 0.1, plaque))
        if shot != "B":
            items.append((SOCK[1], lambda c, soft: _sock(c, cam)))

            def sack(c, soft):
                X0, Z0 = SACK
                if not cam.ahead(Z0, 120.0):
                    return
                k = cam.k(Z0)
                with plane(c, cam, Z0) as s:
                    gx, gy = ref(X0, 0.0, Z0)
                    c.translate(gx, gy)
                    c.scale(s, s)
                    _sack(c, L_SACK, 2 if k >= 0.9 else 1 if k >= 0.45 else 0)
            items.append((SACK[1], sack))

        def elf(c, soft):
            tgt, back = st["reach"]
            off = _tap_offset(t)
            target = (tgt[0] + back[0] * off, tgt[1] + back[1] * off)
            with plane(c, cam, Z_ELF) as s:
                ex, ey = ref(X_ELF, 0.0, Z_ELF)
                P.draw_washhouse_bench(c, ex, ey, s, L_OAK, t, yaw=-0.12)
                epose = _elf_pose(t, target)
                if shot == "B":
                    # the close-up: her lids lifted just enough that the irises show, aimed down-
                    # left at the glass -- her eyes never leave it (closed lids read as serene
                    # listening); one calm blink after the taps, none on them
                    epose = epose.with_(mood=ELF_B_EYES, look=(-0.35 + 0.04 * B.sway(t, 0.3, 4), 0.65),
                                        blink=core.window(t, T_REST + 0.45, T_REST + 0.65, 0.06, 0.12))
                elight = L_ELF_B if shot == "B" else _elf_light(t)
                hand = None
                if shot == "B" and epose.far.gesture == "tap_sign":
                    # the insert's hand: find it (a draw on a scratch surface), clip the rig's own
                    # hand away beyond the wrist, draw the pointing hand over it afterwards
                    hand = ch.draw_elf(core.frame(8, 8)[1], ex, ey, s, epose, elight, t).hand_far
                    hm = _hand_matrix(hand)
                    c.save()
                    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
                    c.rectangle(-4000.0, -4000.0, 8000.0, 8000.0)
                    core.polygon(c, [hm.transform_point(u, v) for u, v in ((0.12, -0.6), (1.7, -0.6), (1.7, 0.7), (0.12, 0.7))])
                    c.clip()
                    c.set_fill_rule(cairo.FILL_RULE_WINDING)
                erig = ch.draw_elf(c, ex, ey, s, epose, elight, t)
                if hand is not None:
                    c.restore()
                    k_el = s * ch.REGISTRY["elf"].SIZE_K
                    lw = B.line_for(B.LINE / ch.REGISTRY["elf"].SIZE_K, k_el * B.device_scale(c),
                                    1.0 / ch.REGISTRY["elf"].SIZE_K) * k_el
                    _point_hand(c, erig.hand_far, ch.elf_mats()["skin"], elight, lw)
                if erig.mirror:          # the mirror's spill: a local glow, never a wash over her
                    fx.glow(c, erig.mirror[0], erig.mirror[1], (52 if shot == "B" else 64) * s, C["mirror"],
                            (0.1 if shot == "B" else 0.18) * _mirror_dim(t))
                _shell_hum(c, t, erig, s)
                out["mirror"] = cam.matrix(Z_ELF).transform_point(*erig.mirror) if erig.mirror else None
        items.append((Z_ELF, elf))

        def dragon(c, soft):
            with plane(c, cam, Z_DRAGON) as s:
                dx, dy = ref(X_DRAGON, 0.0, Z_DRAGON)
                dpose = _dragon_pose(t)
                sw = 0.03 * B.wobble(t, 2.75, 3.2, 3.0) + 0.025 * B.wobble(t, T_SWIVEL1 - 0.1, 3.0, 3.0)
                yaw = dpose.turn * 0.6
                # the wisps' buzz flickers the cold rim on him (quantised so the palette cache holds)
                rim = round((0.74 + 0.26 * _wisp_level(t, 0)) * 50.0) / 50.0
                light = L_DRAGON.with_(rim_strength=rim)
                syaw = 0.3 + yaw * 0.25

                def seat(cc, proj, feet, syaw=syaw, sw=sw):
                    _stool_under(cc, proj, feet, t, syaw, sw)
                drig = ch.draw_dragon(c, dx, dy, s, dpose.with_(seat_prop=seat), light, t)
                nx, ny, ndir = st["smoke_at"]
                _sigh_smoke(c, t, T_SMOKE, nx, ny, s, ndir)
                out["head"] = cam.matrix(Z_DRAGON).transform_point(*drig.head)
        items.append((Z_DRAGON, dragon))
        for name, X, z in FG_PIECES:
            if not cam.ahead(z, 40.0):
                continue

            def piece(c, soft, name=name, X=X, z=z):
                with plane(c, cam, z) as s:
                    gx, gy = ref(X, 0.0, z)
                    c.translate(gx, gy)
                    c.scale(s, s)
                    st[name].paint(c)
            items.append((PIER_Z[0] - PIER_D / 2.0 - 5.0, piece))   # framing pieces: over the first piers
    return items


def _shaft(cam, shot):
    """The moon's shaft down the nave: where it lands (a fixed place in the world for each shot,
    so the flagstones never slide under the light) and its two screen end points."""
    z_land = {"D": 2600.0, "B": 1900.0}.get(shot, 1700.0)
    return z_land, cam.p(0.0, 1050.0, WALL_Z), cam.p(40.0, 0.0, z_land)


def _shaft_dust(c, t, cam, shot, size_k=1.0, alpha=0.75):
    """Dust motes turning in the moon shaft."""
    z_land, (sx0, sy0), (sx1, sy1) = _shaft(cam, shot)
    kk = cam.k(z_land)

    def in_shaft(x, y):
        u = core.clamp((y - sy0) / max(1.0, sy1 - sy0))
        cx_ = sx0 + (sx1 - sx0) * u
        half = (45 + 230 * u) * kk
        return core.clamp(1.0 - abs(x - cx_) / max(1.0, half)) * core.smoothstep(0.08, 0.35, u)

    fx.dust(c, t, (min(sx0, sx1) - 300 * kk, sy0, abs(sx1 - sx0) + 600 * kk, sy1 - sy0), n=110,
            color="#d8ecff", alpha=alpha, size=(0.9 * kk * size_k, 2.4 * kk * size_k), seed=3, drift=(5.0, -2.5),
            mask=in_shaft)


def draw(cr, t, st):
    cam, shot = camera(t)
    zn, zf = _focus(shot, cam)
    out = {"drums": [], "lamps": [], "his": None, "head": None, "mirror": None}
    items = sorted(enumerate(_items(cam, shot, t, st, out)), key=lambda e: (-e[1][0], e[0]))
    layers = {"bg": [], "mid": [], "fg": []}
    for _, (d, fn) in items:
        layers["fg" if d < zn else "bg" if d > zf else "mid"].append(fn)

    # ================= far: everything deeper than the focus band -> soft buffer
    bg = st["bg"][shot]
    bc = bg.begin()
    _vault_backdrop(bc, cam)
    with plane(bc, cam, WALL_Z):
        st["wall"].paint(bc)
    _aisles_and_floor(bc, cam)
    for fn in layers["bg"]:
        fn(bc, "bg")
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
    if shot == "B":
        # the insert: the shaft lands behind her (z 1900 > her 1560), so its motes are drawn
        # here, soft, BEHIND her -- not over her face as blemishes or a false tear
        _shaft_dust(bc, t, cam, shot, size_k=1.5, alpha=0.8)
    bg.paint(cr)

    # ================= the focus band, full resolution
    for fn in layers["mid"]:
        fn(cr, "mid")

    # ================= foreground: very soft
    if layers["fg"]:
        fg = st["fg"][shot]
        fc = fg.begin()
        for fn in layers["fg"]:
            fn(fc, "fg")
        fg.paint(cr)

    # ================= light
    lc = st["light"].begin()
    for (S0, r, g, ring) in out["drums"]:
        if g < 0.01:
            continue
        fx.glow(lc, S0[0], S0[1], r * 3.0, C["porthole"], 0.2 * g)
        if r > 22.0:                                 # a wet streak of it on the flagstones below
            fx.light_shaft(lc, S0[0], S0[1] + r * 1.6, S0[0], S0[1] + r * 4.2, r * 0.9, r * 1.4, C["porthole"],
                           alpha=0.07 * g, soft=2, fade_start=0.0, fade_end=1.0)
        if ring is not None and r > 40.0 and _RUNE_STROKES is not None:
            # the runes breathe: a soft cyan glow laid over each glyph on the bezel (the props
            # kit's own rune band, same glyphs and places, through the lid's rim-fitted affine)
            m_lid, pulse, seed = ring
            lc.save()
            lc.transform(m_lid)
            lc.new_path()
            for k in range(12):
                a = k / 12.0 * TAU + 0.13
                for seg in _RUNE_STROKES(k + seed, math.cos(a) * DRUM_R * 0.765,
                                           -DRUM_AXLE + math.sin(a) * DRUM_R * 0.765, 9.0, a + math.pi / 2.0):
                    lc.move_to(*seg[0])
                    lc.line_to(*seg[1])
            lc.restore()
            lc.set_line_width(max(3.0, r * 0.045))
            lc.set_line_cap(cairo.LINE_CAP_ROUND)
            core.src(lc, "#7fffe0", (0.2 + 0.35 * pulse) * g)
            lc.stroke()
    for (lp, z) in out["lamps"]:
        with plane(lc, cam, z) as s:
            P.wisp_light(lc, lp, s, None, 0.8)
        X = (lp.center[0] - PX) / (F / z)
        pc = cam.p(X, 0.0, z)
        kk = cam.k(z)
        fx.light_pool(lc, pc[0], pc[1], 520 * kk, 110 * kk, "#6fffd0", 0.24 * lp.level)
    # the moon: a long cold shaft down the nave, landing in the empty aisle between them -- at a
    # fixed place in the world for each shot, so the flagstones never slide under the light
    z_land, w0, w1 = _shaft(cam, shot)
    fx.light_shaft(lc, w0[0], w0[1], w1[0], w1[1], 90 * cam.k(WALL_Z), 520 * cam.k(z_land), C["shaft"], alpha=0.13,
                   soft=3, fade_start=0.4, fade_end=0.3)
    mp = cam.p(40.0, 0.0, max(2100.0, z_land + 400.0))
    kk = cam.k(max(2100.0, z_land + 400.0))
    fx.light_pool(lc, mp[0], mp[1], 560 * kk, 150 * kk, C["shaft"], 0.2)
    if out["his"] is not None and out["head"] is not None:
        kk = cam.k(Z_DRAGON)
        hp = out["his"][0]
        d_head = out["head"]
        fx.glow(lc, 0.6 * d_head[0] + 0.4 * hp[0], 0.6 * d_head[1] + 0.4 * hp[1], 130 * kk, C["porthole"], 0.09)
        # his porthole's cold light pooled on the floor round the stool
        fp = cam.p(X_DRAGON - 120.0, 0.0, Z_DRAGON + 40.0)
        fx.light_pool(lc, fp[0], fp[1], 360 * kk, 76 * kk, C["porthole"], 0.3)
        fx.glow(lc, d_head[0] - 60 * kk, d_head[1] + 60 * kk, 240 * kk, C["porthole"], 0.1)
    if shot in CAST_SHOTS:
        ep = cam.p(X_ELF - 40.0, 0.0, Z_ELF - 30.0)
        kk = cam.k(Z_ELF)
        md = _mirror_dim(t)
        fx.light_pool(lc, ep[0], ep[1], 260 * kk, 55 * kk, C["mirror"], 0.14 * md)
        if out["mirror"]:
            # sized in world units, but never wider than the wide shot's: in the insert (kk ~3)
            # a 600 px additive wash would bleach her face
            em = out["mirror"]
            fx.glow(lc, em[0], em[1] - 30, 200 * min(kk, 1.1), C["mirror"], (0.08 if shot == "B" else 0.12) * md)
    if shot != "B":                                   # dust motes turning in the shaft
        _shaft_dust(cr, t, cam, shot)
    # the insert is a big pale face beside a bright mirror: a higher bloom threshold, or the
    # bloom of a large bright area lands back on itself and clips her skin
    fx.post(cr, t, light=st["light"], bloom_strength=0.45 if shot == "B" else 0.55,
            threshold=0.74 if shot == "B" else 0.6, bloom_radius=2.2, wide=0.3 if shot == "B" else 0.4,
            grain=0.035, vignette=0.66, vignette_color=C["vig"])
    if t < T_FADE1:
        fx.fade(cr, 1.0 - core.ramp(t, T_FADE0, T_FADE1, "inout_sine"))


# ----------------------------------------------------------------------------------------
# sound cues (the sound designer synthesizes foley from these): (local t, kind, params)
# ----------------------------------------------------------------------------------------
def _drum_landings(seed, spd, t0, t1):
    """When the biggest garment in a drum thumps down, in [t0, t1): the props porthole's tumble
    cycle (garment i is at u = (t * 0.42 * speed + hash01(i, seed + 1)) % 1 and lands as u wraps;
    its size grows with hash01(i, seed + 6))."""
    i = max(range(7), key=lambda k: core.hash01(k, seed + 6))
    ph = core.hash01(i, seed + 1)
    rate = 0.42 * spd
    out, k = [], 1
    while True:
        tt = (k - ph) / rate
        k += 1
        if tt >= t1:
            break
        if tt >= t0:
            out.append(round(tt, 3))
    return out


def _his_drum_landings():
    """His own drum's thumps, while it is on screen (not in the insert or the row)."""
    side, z, seed, spd = next((sd, z, se, sp) for sd, z, se, sp, b, j in DRUMS
                              if sd < 0 and b == HIS_BAY and j == HIS_SLOT)
    return [tt for tt in _drum_landings(seed, spd, T_FADE1, DUR - 0.3)
            if not (T_CUT_INSERT - 0.05 <= tt <= T_CUT_BACK + 0.05)
            and not (T_ROW0 - 0.05 <= tt <= T_ROW1 + 0.05)]


def _row_thunks():
    """The row: each drum sliding past the camera thumps as its biggest garment lands -- only
    while that drum is on screen, panned by where it is in the frame, louder when near."""
    out = []
    frames = range(int(T_ROW0 * 24) + 1, int(T_ROW1 * 24))
    for side, z, seed, spd, bb, j in DRUMS:
        if not (1700.0 <= z <= 3000.0):
            continue
        vis = [f / 24.0 for f in frames if _drum_on_screen(camera(f / 24.0)[0], side, z)]
        if not vis:
            continue
        for tt in _drum_landings(seed, spd, vis[0] + 0.1, vis[-1]):
            cam = camera(tt)[0]
            x = cam.p(side * LID_X, DRUM_AXLE, z)[0]
            near = core.clamp(1.0 - (z - cam.z) / 1400.0, 0.15, 1.0)
            out.append((tt, "drum_spin_thunk", {"gain": round(0.1 + 0.22 * near, 3),
                                                "pan": round(core.clamp((x - W / 2) / (W / 2), -0.9, 0.9), 2),
                                                "size": 0.55}))
    return out


SFX_CUES = sorted([
    (2.75, "bench_creak", {"gain": 0.35, "pan": -0.35, "size": 0.35}),                 # shifts on the tiny stool
    (T_SWIVEL0 + 0.2, "bench_creak", {"gain": 0.45, "pan": -0.35, "size": 0.35}),      # swivels toward her
    (T_SWIVEL0 + 0.25, "cloth_rustle", {"gain": 0.3, "pan": -0.35}),
    (T_LEAN + 0.25, "cloth_rustle", {"gain": 0.4, "pan": -0.3}),                       # leans in, hand lifts
    (T_LEAN + 0.35, "wing_flutter", {"gain": 0.2, "pan": -0.3, "size": 0.3}),          # wings lift in hope
    (T_TAP + 0.05, "cloth_rustle", {"gain": 0.3, "pan": 0.4}),                         # her arm comes up
    (T_HIT1, "tap_wood", {"gain": 0.75, "pan": 0.2}),                                  # tap
    (T_HIT2, "tap_wood", {"gain": 0.8, "pan": 0.2}),                                   # tap
    (T_HIT2 + 0.08, "creak_wood", {"gain": 0.15, "pan": 0.25, "size": 0.2}),           # the board rocks on its nail
    (T_REST, "tap_wood", {"gain": 0.3, "pan": 0.2}),                                   # ...and the finger stays
    (L1.end + 0.25, "wing_flutter", {"gain": 0.15, "pan": 0.0, "size": 0.3}),          # wings sink
    (T_WITHDRAW0 + 0.1, "cloth_rustle", {"gain": 0.18, "pan": 0.85}),                  # she lowers her hand (off)
    (T_BODY0 + 0.12, "bench_creak", {"gain": 0.25, "pan": 0.0, "size": 0.35}),         # turns back to his drum
    (T_SIGH, "sigh", {"gain": 0.75, "pan": -0.4}),
    (T_SMOKE + 0.05, "smoke_puff", {"gain": 0.3, "pan": -0.4}),
    (T_SIGH + 1.6, "bench_creak", {"gain": 0.2, "pan": -0.35, "size": 0.35}),          # back round to his drum
] + _row_thunks() + [(tt, "drum_spin_thunk", {"gain": 0.22, "pan": -0.45, "size": 0.5}) for tt in _his_drum_landings()],
    key=lambda c: c[0])
