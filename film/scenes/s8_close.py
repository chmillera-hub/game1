"""s8_close.py -- SCENE 8, CLOSE (20 s). The film's last image: one warm lantern in the dark.

THE IDEA (SPEC 0.3, S8)
  Everything the city handed him was a stone: SELF-SERVICE, a pile of remedies, a queue on a
  speaking stone, a SMILE stamp, a crowd that looked away. Now it is night in the castle garden
  and he sits in a ring of company under ONE iron lantern. The image is the parable: a small
  pool of warmth -- company, honesty, bread -- in a big dark world; far away on the castle hill
  the places that handed him stones (the wash-house, the apothecary's green cross, the tavern's
  lantern strings) glow small and cold. The voice-over says what he learned; the picture shows
  it: on "break" HE breaks his bread and holds half out to the grandmother who first broke hers
  for him (she gave away the last of hers in S7). The given-to becomes the giver; she leans her
  head on his arm. Then the night closes gently round the light, like a storybook closing.

ONE SHOT -- a very slow pull-back, no cuts: the stillest shot of the film
  0.0 -> 16.9  one eased pull-back, Camera(1170, 716) z1.33 -> Camera(1060, 628) z1.10, with a
               barely-there breathing drift. It opens on ~S7's last framing (S7 ends on a slow
               pull-back over this ring at blue hour), so the move carries on across the cut and
               the cut reads as time passing. Multiplane: sky 0.06, the castle hill + town 0.28,
               the near hills 0.45, the garden 1.0, soft foreground grass 1.3 -- the warm ring
               gets smaller in a world that gets bigger; the oak comes in to frame the left.
  16.9 -> 20   the final painting holds (only life moves: breath, the bard's silent strum,
               fireflies, the flame). s8_fade 17.5 -> 19.8: the night closes in from the edges
               toward the lantern's pool (a storybook iris), then black; the last 5 frames are
               black for a clean cut to S9's fade-in.

THE RING (world px, the shared layout of film/scenes/_garden.py; S7 hands these over -- S7_END)
  bench 1: the faun (u 0.20), three pigeons roosting on the seat (u 0.34-0.46, S7's), the gnome
  (u 0.60), the dragon (u 0.845, front-on, tail curled round in front of his feet, wings
  relaxed); the tied-open apothecary sack -- the stones -- forgotten in the dark at the bench
  end. The griffin courier dozes on his haunches on the grass left of bench 1 (520, 956).
  bench 2 (G.BENCH2, angled in): the cockatrice BARD (u 0.14, silent cameo, quietly strumming,
  eyes half closed -- the storyteller of S0 has joined the tale he told), the dwarf (u 0.45, his
  cap candle lit), and an elf in a plum cloak, hood down, ear-shells dark (the wash-house
  stranger of S1 who pointed at SELF-SERVICE: even she came). Two pigeons roost at the lamp's foot.

COMPOSITION / EYE-TRACE
  The lantern post is the axis between the two benches, which angle toward each other round it
  like hands cupped round a candle. Values: the flame is the brightest point; the faces nearest
  it (the dragon, the gnome, the bard, the dwarf) are keyed warm FROM the lamp's direction and
  rimmed cool by the moon on their far sides (light_at); the garden falls away into a cached
  night falloff beyond the ring (_draw_dark), so the eye goes lamp -> dragon -> gnome -> their
  hands, where the story happens. The far town lights sit between the heads (never behind one)
  and clear of the post through the whole move. Depth: foreground grass (1.3, blurred, nearly
  black) / the ring / the hedges / mist in the valley / the town and the castle on its hill
  against a band of moonlit haze / the sky. The caption band (bottom 180 px) holds only gravel,
  bench feet and fireflies.

COLOUR / VALUE SCRIPT (light is kindness, STYLE 6)
  Dominant deep night blue (#0b1226 .. #1d2a4a), graded cooler in the shadows (_night_lut) and
  graduated darker toward the top (_sky_grad). ONE accent: the lantern's amber -- its halo, a
  soft cone of light falling onto the ring, the warm pool on the gravel (and the dwarf's tiny
  cap candle). Far away, three small COLD accents: wash-house teal, apothecary mint-green, tavern
  magenta -- the stones, still lit, no longer the subject. At the break the bread gives off a
  soft warm breath of light and a curl of steam (as her loaf did in S7): the warmth now comes
  from his hands. Fireflies (yellow-green) and moths round the lamp are the only other lights.

ACTING (thought -> glance -> breath -> line; the VO is his THOUGHT: NOBODY'S lips move on it --
  checked: every mouth is closed during s8_l1..l3, and the ring's laugh is a silent chuckle)
  0.3-2.2   the dwarf tells a tale in gestures (an explaining hand, head bobbing); the ring
            listens toward him. The dragon cradles a small round of bread in his lap.
  L1 2.50   "They kept handing me stones." -- his eyes drift off the dwarf down to the bread
            (2.62), the head follows; a slow blink on "stones" (3.79). Remembering.
  4.65      the dwarf's punchline (both open hands up); 4.97 the ring chuckles together, silently
            (closed smiles, squeezed eyes, heads and shoulders bobbing; the dragon's wings lift);
            the seat pigeons stir; the courier wakes with a start and yawns.
  L2 7.00   "We were hungry for bread the whole time." -- he looks round at the people near him:
            eyes first, then the head -- down to her (7.05; she looks up at him on "bread"), past
            her to the faun (8.47), across the ring to the bard and the dwarf (8.91). A warm
            smile; he settles (10.06). The faun bites his crust (10.36); the courier dozes off.
  L3 11.80  "All it took was somebody to break it." -- on "somebody" (12.85) his eyes go down to
            the bread; he lifts it a little out of his lap, the hands take a grip (13.64), a
            strain, and on "break" it snaps in two (14.15): crumbs, a warm breath of light, steam.
            His face softens to tender. His near hand turns palm-up and holds her half out at
            the edge of his lap (14.49-14.99). She looks at it, up at him ("for me?"), hops once
            along the seat to him (15.29, her S6 hop), takes it off his palm (15.84) -- tiny hand,
            huge claw -- looks up at him with a hand to her heart (16.24; her spectacles catch
            the lamplight) and leans her head against his arm, eyes closing (16.69). He looks
            down at her, his head tipping toward hers, and gives one slow content blink.
  16.9-     the final painting; the night closes in (s8_fade). The bard has nodded to them.

PERIOD (SPEC 0.1): an iron candle lantern, wrought-iron-and-oak benches, a gravel walk, clipped
hedges, a paper apothecary sack tied with twine, wool, linen, leather, felt, a lute, a miner's
cap candle, bread; the castle and a medieval roofline far away; the town's lights are candle-lit
signs, portholes and paper lanterns (cold only in colour). Nothing electric, nothing modern.

TECHNICAL: the static art is merged per plane into cached layers (build_planes: far = haze +
castle hill + the town's houses; garden = lawn, hedges, walk, beds + the warm pool); the benches
never move and are cached in tight supersampled layers (build_benches); level of detail is fixed
per character for the whole shot (LOD) because the pull-back crosses the library's automatic
thresholds; the bread's two-hand grips and both hand-overs are measured once in setup
(_calibrate_grips, _solve_handoff) so the bread never jumps between hands.

SOUND: SFX_CUES (module level) lists every on-screen event with its local time, computed from the
same constants the animation uses. The bard's strumming is silent (the score carries the music);
the VO, crickets and the murmur are handled elsewhere.
"""

import math

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.scenes import _garden as G

SCENE = 8
DUR = tl.scene(SCENE).duration

# ----------------------------------------------------------------------------------------
# timing: everything derives from the timeline's lines, words and the s8_fade beat
# ----------------------------------------------------------------------------------------
L1, L2, L3 = tl.line("s8_l1"), tl.line("s8_l2"), tl.line("s8_l3")
B_FADE = tl.beat("s8_fade")


def _word(line_id, k):
    """Start time of word k of a line (aligned to the speech envelope)."""
    return tl.word_times(line_id)[k][1]


W_STONES = _word("s8_l1", 4)
W_HUNGRY, W_BREAD, W_WHOLE = _word("s8_l2", 2), _word("s8_l2", 4), _word("s8_l2", 6)
W_SOMEBODY, W_BREAK = _word("s8_l3", 4), _word("s8_l3", 6)

T_TALE0, T_TALE1 = 0.3, L1.start - 0.3         # the dwarf's tale (his beard wags; no line of his)
T_DOWN = L1.start + 0.12                         # L1: the dragon's eyes drift down to the bread
T_PUNCH = L1.end + 0.2                           # the dwarf's punchline: both hands out
T_LAUGH = T_PUNCH + 0.32                         # the ring laughs together (softly)
T_LAUGH1 = min(T_LAUGH + 1.35, L2.start - 0.45)
T_LOOK_G = L2.start + 0.05                       # L2: eyes to her (the head follows) ...
T_LOOK_F = W_BREAD + 0.38                        # ... past her to the faun ...
T_LOOK_R = W_WHOLE + 0.25                        # ... across the ring to the bard and the dwarf
T_SETTLE = L2.end + 0.5
T_BITE = L2.end + 0.8                            # the faun bites his crust (his hand reached his mouth)
T_LIFT = W_SOMEBODY - 0.08                       # L3: he lifts the bread a little, looks at it
T_GRIP = W_BREAK - 0.45                          # the far hand takes the other side
T_SNAP = W_BREAK + 0.06                          # it snaps on "break"
T_PART = T_SNAP + 0.3                            # the halves apart
T_OFFER0 = T_PART + 0.04                         # his near hand turns palm-up and holds her half out to her,
T_OFFER = T_OFFER0 + 0.5                         # beside his knee
T_HOP = T_OFFER + 0.3                            # she scoots along the seat to him: one little hop (her S6 hops)
T_HANDOFF = T_HOP + 0.55                         # she takes it off his palm
T_LOOKUP = T_HANDOFF + 0.4                       # she looks up at him, a hand to her heart ...
T_LEAN = T_LOOKUP + 0.45                         # ... and leans her head against his arm, eyes closed
T_GIVE0 = T_OFFER0                               # (alias: the giving begins)
T_CAM_END = 16.9                                 # the pull-back settles: the final painting
T_FADE0 = B_FADE.t                               # the night closes in toward the lantern ...
T_FADE1 = DUR - 0.2                              # ... black (the last frames are black: a clean cut to S9)

# ----------------------------------------------------------------------------------------
# the set and the ring
# ----------------------------------------------------------------------------------------
SC = G.SCALE
U1 = {"faun": 0.2, "gnome": 0.6, "dragon": 0.845}             # bench 1 (BenchRig.place fractions)
U2 = {"bard": 0.14, "dwarf": 0.45, "elf": 0.76}               # bench 2
GRIFFIN = (520.0, 956.0)                                      # on the grass at bench 1's left end
PIGEONS = [(1336.0, 921.0, -1, 71), (1366.0, 926.0, -1, 72)]  # roosting at the lantern's foot (x, y, facing, seed)
SEAT_BIRDS = [(0.40, -1, 101), (0.34, 1, 77), (0.46, -1, 78)]     # S7's three seat pigeons (u, facing, seed), roosting
SACK = (1118.0, 876.0)                                        # the apothecary sack (grip), forgotten by the bench end
# the far town (hills plane, PARALLAX["hills"]): the three cold lights of the places that
# handed him stones -- positions in that plane's world coordinates
TOWN = {"washhouse": (690.0, 545.0), "apothecary": (1076.0, 524.0), "tavern": (1342.0, 553.0)}
TOWN_PLANE = "far"                   # they stand on the castle hill's slopes, under the castle

# level of detail, fixed for the whole shot: the slow pull-back crosses the library's automatic
# LOD thresholds, and a mid-shot switch would pop (knit, stitches, creases appearing/vanishing).
# The leads keep everything; the ring, small and partly in the dark, draws at detail 1.
LOD = {"dragon": 2, "gnome": 2, "faun": 1, "bard": 1, "elf": 1, "griffin": 1, "dwarf": 1, "props": 1}

Cam = core.Camera
CAM_A = Cam(1170.0, 716.0, 1.33)       # ~S7's last framing: its slow pull-back continues across the cut
CAM_B = Cam(1060.0, 628.0, 1.1)        # the garden in the night round the ring: the final painting

_STATE = {}
_GX = {}                               # per-frame gesture targets (body space) for the dragon's s8_* gestures
_CAP = {}                              # device-space captures from hold callbacks (setup calibration)


# ----------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------

def _r(t, a, b, e="inout_sine"):
    return core.ramp(t, a, b, e)


def _win(t, a, b, fi=0.2, fo=0.3):
    return core.window(t, a, b, fi, fo)


def _track(t, keys, ease="inout_sine"):
    return core.track(t, keys, ease)


def _bump(t, t0, dur):
    u = (t - t0) / dur
    return math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0


def _blink_at(t, times, dur=0.18):
    """Lid closure from deliberate blink times (fast close, slower open)."""
    best = 0.0
    for tb in times:
        u = (t - tb) / dur
        if 0.0 <= u <= 1.0:
            best = max(best, core.smooth(u / 0.35) if u < 0.35 else 1.0 if u < 0.45 else 1.0 - core.smooth((u - 0.45) / 0.55))
    return best


def _v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)


def _scratch():
    return core.frame(8, 8)[1]


# ----------------------------------------------------------------------------------------
# camera: one slow pull-back, settling into the final painting
# ----------------------------------------------------------------------------------------

def pull(t):
    """0 -> 1: how far the camera has pulled back (eased in and out, settled by T_CAM_END)."""
    return core.ramp(t, 0.0, T_CAM_END, "inout_sine")


def camera(t):
    cam = Cam.lerp(CAM_A, CAM_B, pull(t))
    return cam.drift(t, amp=1.6 / cam.zoom, freq=0.08, seed=8)


# ----------------------------------------------------------------------------------------
# light: ONE warm lantern; everything else is the cold night
# ----------------------------------------------------------------------------------------
WARM_KEY = (1.16, 0.84, 0.52)
WARM_AMB = (0.22, 0.23, 0.42)
MOON_RIM = (0.6, 0.72, 1.0)
NIGHT = ch.Light(key=(0.5, 0.58, 0.86), ambient=(0.16, 0.18, 0.36), rim=MOON_RIM, rim_strength=0.45,
                 direction=(0.55, -0.83), exposure=0.5, name="s8_night")


def lamp():
    return _STATE.get("lamp", (1253.0, 446.0))


def flicker(t):
    """The candle in the lantern: a soft, slow flicker (shared by the pool, the halo, the key)."""
    return 0.93 + 0.05 * core.noise1(t * 5.0, 3) + 0.02 * math.sin(t * 13.0)


def warmth_at(x, y):
    """0..1: how much of the lantern's light reaches the world point (x, y)."""
    lx, ly = lamp()
    d = math.hypot(x - lx, (y - ly) * 0.9)
    return 1.0 - core.smoothstep(200.0, 960.0, d)


def light_at(x, y, boost=1.0, rim_k=1.0):
    """The light on a creature or prop at world (x, y): a warm key FROM the lamp's direction,
    falling off with distance into the cold night, and a cool moonlit rim on the side away
    from the lamp (Klaus-style: warm key, cold edge)."""
    lx, ly = lamp()
    dx, dy = lx - x, ly - y
    n = math.hypot(dx, dy) or 1.0
    kd = (dx / n, dy / n)
    side = 1.0 if dx >= 0 else -1.0
    rd = (-0.72 * side, -0.69)
    k = core.clamp(warmth_at(x, y) * boost)
    warm = ch.Light(key=WARM_KEY, ambient=WARM_AMB, rim=MOON_RIM, rim_strength=0.5 * rim_k, direction=kd,
                    rim_direction=rd, exposure=1.26, name="s8_lamp")
    night = NIGHT.with_(rim_direction=rd, rim_strength=0.45 * rim_k)
    return ch.Light.lerp(night, warm, k)


# ----------------------------------------------------------------------------------------
# the dragon: front-on, settled, tail curled round the bench leg, bread in his lap
# ----------------------------------------------------------------------------------------
_ELEV = 0.12


def _lap(c):
    """The middle of his lap (body space): over the thighs, between the knees."""
    hip = _v_lerp(c["hip"][-1.0], c["hip"][1.0], 0.5)
    kn = _v_lerp(c["knee"][0], c["knee"][1], 0.5)
    return _v_add(_v_lerp(hip, kn, 0.62), (0.0, -24.0, 16.0))


def _g_s8_probe(sk, side, c):
    # setup only: record the seated skeleton (hips, knees) the hand targets are built from
    _STATE["probe"] = {"hip": dict(c["hip"]), "knee": list(c["knee"])}
    return ch.DRAGON_GESTURES["rest"](sk, side, c)


def _g_s8_give(sk, side, c):
    # the near hand (targets solved per frame in _GX): holds her half out on his open palm beside
    # his knee, then comes home to cradle his own half in his lap
    return _GX.get("give", _v_add(c["chest"], (-60.0, 90.0, 80.0))), _GX.get("give_hand", "grip"), 0.0, "front"


def _g_s8_keep(sk, side, c):
    # the far hand keeps his half, settling back onto his lap (_GX["keep"])
    return _GX.get("keep", _v_add(c["chest"], (40.0, 90.0, 80.0))), "grip", 0.0, "front"


for _name, _fn in (("s8_probe", _g_s8_probe), ("s8_give", _g_s8_give), ("s8_keep", _g_s8_keep)):
    ch.DRAGON_GESTURES[_name] = _fn


def _world_to_body(wx, wy, ax, ay, yaw, depth):
    """A world point -> the dragon's body space (anchor (ax, ay), scale SC, yaw) at camera depth."""
    xb, yb = (wx - ax) / SC, (wy - ay) / SC
    c, s = math.cos(yaw), math.sin(yaw)
    X = c * xb - s * depth
    Z = s * xb + c * depth
    Y = (yb - depth * math.sin(_ELEV)) / math.cos(_ELEV)
    return (X, Y, Z)


D_TURN = 0.4                        # front-on, opened a touch toward the lamp (yaw ~0.24)
D_YAW = D_TURN * 0.6


def dragon_anchor():
    return _STATE["b1"].place(U1["dragon"])


BREAD_SIZE = ch.GNOME_LOAF * 1.0    # the round of bread he kept from her loaf
HALF_DX = 9.0                       # each half sits this far in from its grip (body px): the torn faces show
OFFER_LIFT = 15.0                   # on the open palm the half sits this much above the grip (body px)
OFFER_AT = (-74.0, -4.0, 18.0)      # her half on his palm: at the near edge of his lap (body px from its middle)


def _bread_cb(state, face=1.0, key=None, light=None, dx=0.0, dy=0.0, size=BREAD_SIZE):
    """Hold callback drawing HER bread (gnome_bread, so every piece in the film matches) upright at
    the grip + (dx, dy) body px; records the device position of its centre in _CAP[key]."""
    def cb(cr, f):
        cr.save()
        cr.rotate(-f.angle)
        cx, cy = dx, dy - size * 0.12
        ch.gnome_bread(cr, cx, cy, size, light or _STATE.get("L_bread"), state, face=face)
        if key:
            _CAP[key] = cr.user_to_device(cx, cy)
        cr.restore()
    return cb


def lift_at(t):
    """0..1: the bread raised a little out of his lap to look at it (L3, "somebody")."""
    return _track(t, [(0.0, 0.0), (T_LIFT, 0.0), (T_LIFT + 0.6, 0.6), (T_SNAP, 0.66), (T_PART, 0.75)])


def part_at(t):
    """0..1: the break -- the hands pull apart (fast out of the snap, easing)."""
    return core.out_cubic(core.clamp((t - T_SNAP) / (T_PART - T_SNAP))) if t >= T_SNAP else 0.0


def hold_targets(t):
    """Body-space wrist targets (near, far) while both hands hold the bread in his lap: cradled
    in his cupped palms (the bread sits ON them, so it shows), lifted a little to look at it,
    gripped, then pulled apart with a small upward arc (breaking bread)."""
    lap = _STATE["lap"]
    lift, part = lift_at(t), part_at(t)
    grip = _r(t, T_GRIP - 0.3, T_GRIP + 0.1)
    strain = 1.4 * math.sin((t - T_GRIP) * 40.0) * _win(t, T_SNAP - 0.25, T_SNAP + 0.02, 0.08, 0.02)
    half = 25.0 - 3.0 * grip + 30.0 * part + strain
    y = lap[1] + 6.0 - 30.0 * lift - 8.0 * math.sin(math.pi * part) + 8.0 * grip
    z = lap[2] + 18.0 + 26.0 * lift + 6.0 * part
    return (lap[0] - half, y, z), (lap[0] + half, y, z)


def hold_hand(t):
    """The hands' pose while holding the bread: cupped under it, then gripping it to break."""
    return "cup" if t < T_GRIP - 0.12 else "grip"


def _grips_at(t):
    """Calibrated grip offsets (near, far) from the two-hand prop's frame origin (body px,
    upright), interpolated from the table measured in setup."""
    tab = _STATE.get("grips")
    if not tab:
        return (-16.0, 0.0), (16.0, 0.0)
    if t <= tab[0][0]:
        return tab[0][1], tab[0][2]
    for (t0, n0, f0), (t1, n1, f1) in zip(tab, tab[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            return core.lerp_pt(n0, n1, u), core.lerp_pt(f0, f1, u)
    return tab[-1][1], tab[-1][2]


def _two_cb(t, light):
    """The bread between both hands (the two-hand prop frame: upright, at the midpoint between
    the forearms' grip points). Whole -- a tear opening as he strains -- until the snap; then
    each half follows its own hand's grip (calibrated), so the hand-over to the one-hand holds
    after the break is seamless."""
    def cb(cr, f):
        cr.save()
        n, fa = _grips_at(t)
        if t < T_SNAP:
            mx, my = (n[0] + fa[0]) * 0.5, (n[1] + fa[1]) * 0.5
            crack = core.clamp((t - (T_SNAP - 0.25)) / 0.25)
            seat = BREAD_SIZE * (0.42 - 0.3 * _r(t, T_GRIP - 0.3, T_GRIP + 0.1))   # on the palms -> in the grip
            ch.gnome_bread(cr, mx, my - seat, BREAD_SIZE, light, "loaf", crack=0.6 * crack)
            _CAP["whole"] = cr.user_to_device(mx, my - seat)
        else:
            for (gx_, gy_), face, sgn in ((n, 1.0, 1.0), (fa, -1.0, -1.0)):
                ch.gnome_bread(cr, gx_ + sgn * HALF_DX, gy_ - BREAD_SIZE * 0.12, BREAD_SIZE, light, "half", face=face)
        cr.restore()
    return cb


def dragon_arms(t, light):
    """(near, far) Arms. Front-on, near = screen-left (toward her). Every target is computed
    here in body space (hold_targets, _GX), so no rig-side blend can jump."""
    if t < T_PART:
        tn, tf = hold_targets(t)
        hp = hold_hand(t)
        return (ch.Arm("hold_book", target=tn, hand=hp, hold=_two_cb(t, light)),
                ch.Arm("hold_book", target=tf, hand=hp))
    tn0, tf0 = hold_targets(T_PART)
    # far: keeps his half, settling back onto his lap
    u = _r(t, T_PART, T_PART + 1.0)
    keep_rest = _v_add(_STATE["lap"], (18.0, -4.0, 20.0))
    _GX["keep"] = _v_add(_v_lerp(tf0, keep_rest, u), (0.0, -6.0 * math.sin(math.pi * u), 0.0))
    far = ch.Arm("s8_keep", hold=_bread_cb("half", -1.0, "keep", light, dx=-HALF_DX))
    # near: her half held out on his open palm beside his knee; after she takes it, home to his lap
    offer = _STATE["offer_body"]
    if t < T_HANDOFF:
        u = core.inout_sine(core.clamp((t - T_OFFER0) / (T_OFFER - T_OFFER0)))
        p = _v_lerp(tn0, offer, u)
        # a breath of motion while he waits for her: the palm lifts a hair toward her
        wait = _r(t, T_OFFER, T_HANDOFF - 0.1)
        p = _v_add(p, (-4.0 * wait, -5.0 * wait, 3.0 * wait))
        _GX["give"] = _v_add(p, (-4.0 * math.sin(math.pi * u), -10.0 * math.sin(math.pi * u), 8.0 * math.sin(math.pi * u)))
        _GX["give_hand"] = "grip" if u < 0.4 else "offer"
        near = ch.Arm("s8_give", hold=_bread_cb("half", 1.0, "give", light, dx=HALF_DX * (1.0 - u),
                                                dy=-OFFER_LIFT * core.smooth(core.clamp((u - 0.25) / 0.5))))
    else:
        u = _r(t, T_HANDOFF + 0.25, T_HANDOFF + 1.1)
        held = _v_add(offer, (-4.0, -5.0, 3.0))
        let_go = _v_add(held, (3.0 * _r(t, T_HANDOFF, T_HANDOFF + 0.25), 6.0 * _r(t, T_HANDOFF, T_HANDOFF + 0.25), 0.0))
        home = _v_add(_STATE["lap"], (-8.0, 4.0, 24.0))
        p = _v_lerp(let_go, home, u)
        _GX["give"] = _v_add(p, (0.0, -8.0 * math.sin(math.pi * u), 8.0 * math.sin(math.pi * u)))
        _GX["give_hand"] = "open" if u < 0.35 else "cup"
        near = ch.Arm("s8_give")
    return near, far


# his face tonight: content -- heavy, soft lids, a small closed smile (not the wide-eyed stare)
CONTENT = ch.Expr(brow_in=0.36, brow_out=0.05, brow_y=0.16, lid=0.44, lid_bot=0.34, lid_tilt=0.14, smile=0.45,
                  cheek=0.4)
# the ring's laugh is SILENT on the soundtrack (the VO and the score carry S8), so every laugh is a
# closed-mouth chuckle -- squeezed smiling eyes, shoulders and heads bobbing (as her S6 chuckle)
RING_CHUCKLE = ch.Expr(brow_in=0.3, brow_out=0.25, brow_y=0.4, lid=0.58, lid_bot=0.62, lid_tilt=-0.12, smile=1.0,
                       open=0.0, mouth="", cheek=1.0)


def chuckle_bob(t, k, rate=4.2, phase=0.0):
    """The chuckle's quick little nods (scaled by k)."""
    return 0.07 * k * math.sin((t - T_LAUGH) * math.tau * rate + phase)


# his silent chuckle with the ring: smiling eyes squeezed up, a wide closed smile
CHUCKLE = ch.Expr(brow_in=0.3, brow_out=0.3, brow_y=0.35, lid=0.6, lid_bot=0.62, lid_tilt=-0.1, smile=1.0,
                  cheek=1.0)
TENDER = ch.Expr(brow_in=0.58, brow_out=0.12, brow_y=0.3, lid=0.16, lid_bot=0.4, lid_tilt=0.18, smile=0.62,
                 cheek=0.6)


def dragon_pose(t):
    x, y = dragon_anchor()
    # eyes lead, the head follows ~0.18 s later, the body last
    look = _track(t, [(0.0, (0.75, 0.12)), (T_DOWN - 0.05, (0.75, 0.12)), (T_DOWN + 0.25, (-0.05, 0.85)),   # L1: to the bread
                      (T_PUNCH - 0.1, (-0.05, 0.85)), (T_PUNCH + 0.12, (0.7, 0.15)),                     # the punchline
                      (T_LOOK_G - 0.02, (0.6, 0.2)), (T_LOOK_G + 0.18, (-0.85, 0.62)),                    # L2: to her
                      (T_LOOK_F - 0.05, (-0.85, 0.62)), (T_LOOK_F + 0.25, (-0.95, 0.2)),                  # the faun
                      (T_LOOK_R - 0.05, (-0.95, 0.2)), (T_LOOK_R + 0.35, (0.8, 0.12)),                    # across the ring
                      (T_SETTLE, (0.55, 0.15)), (W_SOMEBODY - 0.2, (0.5, 0.2)), (W_SOMEBODY + 0.1, (-0.1, 0.9)),  # the bread
                      (T_GIVE0 + 0.05, (-0.1, 0.9)), (T_GIVE0 + 0.25, (-0.8, 0.75)),                      # to her
                      (T_LOOKUP + 0.6, (-0.8, 0.7)), (DUR, (-0.75, 0.62))])
    head_turn = _track(t, [(0.0, 0.32), (T_DOWN + 0.1, 0.32), (T_DOWN + 0.5, 0.05), (T_PUNCH, 0.05), (T_PUNCH + 0.35, 0.3),
                           (T_LOOK_G + 0.15, 0.3), (T_LOOK_G + 0.6, -0.42), (T_LOOK_F + 0.15, -0.42),
                           (T_LOOK_F + 0.5, -0.5), (T_LOOK_R + 0.12, -0.5), (T_LOOK_R + 0.75, 0.36),
                           (T_SETTLE + 0.4, 0.25), (W_SOMEBODY, 0.22), (W_SOMEBODY + 0.4, 0.0),
                           (T_GIVE0 + 0.15, 0.0), (T_GIVE0 + 0.55, -0.4), (DUR, -0.38)])
    head_nod = _track(t, [(0.0, -0.05), (T_DOWN + 0.1, -0.05), (T_DOWN + 0.55, -0.32), (T_PUNCH, -0.3),
                          (T_PUNCH + 0.35, -0.02), (T_LOOK_G + 0.15, -0.02), (T_LOOK_G + 0.6, -0.3),
                          (T_LOOK_R + 0.12, -0.25), (T_LOOK_R + 0.75, 0.0), (W_SOMEBODY, 0.0),
                          (W_SOMEBODY + 0.45, -0.34), (T_GIVE0 + 0.2, -0.34), (T_GIVE0 + 0.6, -0.4), (DUR, -0.36)])
    head_tilt = 0.05 * _win(t, T_LOOK_G + 0.3, T_LOOK_F + 0.2, 0.3, 0.4) + 0.07 * _r(t, T_HANDOFF, T_HANDOFF + 0.8)
    head_tilt -= 0.1 * _r(t, T_LEAN + 0.1, T_LEAN + 0.9)          # toward her as she leans on him
    # the silent chuckle: shoulders and head shake a little, closed smile, wings lift
    chk = _win(t, T_LAUGH + 0.05, T_LAUGH1, 0.15, 0.6)
    head_nod += 0.06 * chk * math.sin((t - T_LAUGH) * math.tau * 3.6)
    smile = 0.42 + 0.3 * chk + 0.18 * _win(t, W_BREAD - 0.2, T_SETTLE + 1.0, 0.4, 0.8) + 0.2 * _r(t, T_HANDOFF, T_HANDOFF + 0.8)
    mood, mood2, mix = CONTENT, None, 0.0
    # L1: a reflective look -- the smile softens while he remembers
    refl = _win(t, T_DOWN, T_PUNCH, 0.35, 0.3)
    if refl > 0:
        mood2, mix = "tired", 0.55 * refl
        smile -= 0.3 * refl
    happy = chk
    if happy > mix:
        mood2, mix = CHUCKLE, happy
    tender = _r(t, T_SNAP + 0.2, T_GIVE0 + 0.4)
    if tender > 0:
        mood2, mix = TENDER, tender
    # blinks are acted: on thought changes; never while she looks up at him (that look must land)
    blink = _blink_at(t, [1.4, T_LAUGH + 1.6, T_LOOK_F - 0.25, T_SETTLE + 0.8, T_LIFT + 0.5])
    if T_LEAN + 0.45 < t < T_LEAN + 1.05:                             # a slow, content blink as she leans on him
        blink = max(blink, math.sin(math.pi * (t - (T_LEAN + 0.45)) / 0.6) ** 0.7)
    if abs(t - (W_STONES + 0.2)) < 0.25:                               # a slow blink on "stones"
        blink = max(blink, math.sin(math.pi * core.clamp((t - (W_STONES - 0.05)) / 0.5)))
    hunch_shake = 0.05 * chk * math.sin((t - T_LAUGH) * math.tau * 3.6 + 0.6)  # the shoulders go with it
    wings = 0.18 + 0.45 * chk + 0.12 * _r(t, T_HANDOFF, T_HANDOFF + 1.0)
    hunch = 0.4 + 0.08 * B.breathing(t, 0.2, 8) + 0.1 * _win(t, T_GIVE0, T_HANDOFF + 0.6, 0.3, 0.6) + hunch_shake
    lean = 0.08 + 0.12 * _win(t, T_GIVE0, T_HANDOFF + 0.5, 0.3, 0.6) + 0.08 * _win(t, T_LIFT, T_PART + 0.2, 0.4, 0.5)
    near, far = dragon_arms(t, light_at(x, y - 150.0, boost=1.1))
    pose = ch.DragonPose(facing=0, turn=D_TURN, sit=1.0, tail_front=True, wings=wings, hunch=hunch, lean=lean,
                         head_turn=head_turn, head_nod=head_nod, head_tilt=head_tilt, look=look, mood=mood,
                         mood2=mood2 if mix > 0 else None, mood_mix=mix, smile=core.clamp(smile, -1.0, 1.0),
                         talk=0.0, blink=blink, tail_curl=0.7, near=near, far=far, seed=8)
    return x, y, pose


# ----------------------------------------------------------------------------------------
# the gnome: beside him, turned to him; she receives the half
# ----------------------------------------------------------------------------------------

U_GNOME_HOP = 0.085                    # how far along the seat her last hop takes her (fraction)
LEAN_MAX = 0.24                        # rad: her lean against his arm


def hop_at(t):
    """(progress 0..1, height 0..1) of her little hop toward him."""
    u = core.clamp((t - T_HOP) / 0.32)
    return core.inout_sine(u), (math.sin(math.pi * u) if 0.0 < u < 1.0 else 0.0)


def lean_at(t):
    return LEAN_MAX * core.inout_sine(core.clamp((t - T_LEAN) / 0.75))


def gnome_anchor(t=0.0):
    prog, hgt = hop_at(t)
    x, y = _STATE["b1"].place(U1["gnome"] + U_GNOME_HOP * prog)
    return x, y - 7.0 * hgt


def gnome_pivot(x, y):
    """Her seat point: she leans about it."""
    return x, y - ch.GNOME_SEAT_H * SC


_GXG = {}                              # her custom-gesture state (per frame): anchor, lean, arm keys


def _g_frame_point(pt):
    """A world point -> her local (unscaled, un-leaned) drawing coordinates."""
    x, y, lean = _GXG["x"], _GXG["y"], _GXG["lean"]
    px, py = gnome_pivot(x, y)
    if lean:
        c, s_ = math.cos(-lean), math.sin(-lean)
        dx, dy = pt[0] - px, pt[1] - py
        pt = (px + dx * c - dy * s_, py + dx * s_ + dy * c)
    return (pt[0] - x) / SC, (pt[1] - y) / SC


def _gn_target(spec, sk, side, c):
    kind, v = spec
    if kind == "g":
        return ch.GNOME_GESTURES[v](sk, side, c)[0]
    lx, ly = _g_frame_point(v)
    yaw = _GXG["yaw"]
    cs, sn = math.cos(yaw), math.sin(yaw)
    se, ce = math.sin(_ELEV), math.cos(_ELEV)
    depth = (-sk[0] * sn + sk[2] * cs) + 16.0           # her shoulder's depth + 16 (as GnomeArm.screen)
    return (lx * cs - depth * sn, (ly - depth * se) / ce, lx * sn + depth * cs)


def _g_s8_gn(sk, side, c):
    """Her arms tonight: a blend between two targets -- a library gesture ("g", name) or a world
    point ("p", (x, y)) -- so reaching out, taking the bread and a hand to her heart all flow."""
    a, b_, u, hp = _GXG[side]
    ta, tb = _gn_target(a, sk, side, c), _gn_target(b_, sk, side, c)
    e = core.inout_sine(core.clamp(u))
    arc = math.sin(math.pi * e) * 5.0 if a != b_ else 0.0
    return _v_add(_v_lerp(ta, tb, e), (side * arc * 0.5, -arc * 0.5, arc)), hp, 0.0, "front"


ch.GNOME_GESTURES["s8_gn"] = _g_s8_gn


def _keys_at(t, keys):
    """[(t, spec, hand)] -> (spec_a, spec_b, u, hand)."""
    if t <= keys[0][0]:
        return keys[0][1], keys[0][1], 0.0, keys[0][2]
    for (t0, a, ha), (t1, b_, hb) in zip(keys, keys[1:]):
        if t < t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            return a, b_, u, (ha if u < 0.5 else hb)
    return keys[-1][1], keys[-1][1], 1.0, keys[-1][2]


G_TURN = -0.32


def gnome_pose(t):
    x, y = gnome_anchor(t)
    lean = lean_at(t)
    look = _track(t, [(0.0, (0.9, -0.05)), (T_PUNCH, (0.9, -0.05)),
                      (W_BREAD - 0.12, (0.9, -0.05)), (W_BREAD + 0.08, (0.55, -0.9)),      # he looks at her: up at him
                      (T_LOOK_R + 0.2, (0.55, -0.9)), (T_LOOK_R + 0.45, (0.85, -0.1)),      # back to the bard
                      (W_SOMEBODY + 0.3, (0.85, -0.1)), (W_SOMEBODY + 0.5, (0.65, -0.35)), # the bread in his hands
                      (T_OFFER0 + 0.1, (0.65, -0.35)), (T_OFFER0 + 0.3, (0.75, 0.3)),       # it is held out to her
                      (T_OFFER + 0.05, (0.75, 0.3)), (T_OFFER + 0.2, (0.6, -0.9)),            # up at him: for me?
                      (T_HOP + 0.25, (0.6, -0.9)), (T_HOP + 0.4, (0.7, 0.45)),                # to the bread, taking it
                      (T_LOOKUP - 0.05, (0.45, 0.6)), (T_LOOKUP + 0.12, (0.6, -0.95)),       # up at him
                      (DUR, (0.6, -0.95))])
    head_turn = _track(t, [(0.0, 0.15), (W_BREAD, 0.15), (W_BREAD + 0.3, 0.05), (T_LOOK_R + 0.3, 0.05),
                           (T_LOOK_R + 0.7, 0.15), (T_GIVE0, 0.15), (T_GIVE0 + 0.4, 0.05), (DUR, 0.05)])
    head_nod = _track(t, [(0.0, 0.0), (W_BREAD + 0.05, 0.0), (W_BREAD + 0.3, 0.25), (T_LOOK_R + 0.3, 0.25),
                          (T_LOOK_R + 0.7, 0.0), (T_GIVE0 + 0.2, 0.0), (T_GIVE0 + 0.5, -0.25),
                          (T_LOOKUP, -0.25), (T_LOOKUP + 0.3, 0.3), (T_LEAN, 0.3), (T_LEAN + 0.6, 0.12), (DUR, 0.12)])
    head_tilt = 0.14 * core.inout_sine(core.clamp((t - T_LEAN) / 0.7))       # her cheek to his arm
    # listening nods to the dwarf's tale
    head_nod += 0.08 * _win(t, 0.8, T_TALE1 + 0.3, 0.3, 0.3) * math.sin((t - 0.8) * math.tau * 0.7)
    chk = _win(t, T_LAUGH, T_LAUGH1, 0.12, 0.45)
    head_nod += chuckle_bob(t, chk, 4.6, 0.3) - 0.08 * chk
    mood, mood2, mix = "kind", None, 0.0
    if chk > 0:
        mood2, mix = RING_CHUCKLE, chk
    if t > T_HANDOFF:
        mood, mood2, mix = "warm", "happy", 0.7 * _r(t, T_LOOKUP - 0.2, T_LOOKUP + 0.5)
    smile = 0.5 + 0.25 * _win(t, W_BREAD, T_LOOK_R + 0.5, 0.2, 0.5) + 0.35 * _r(t, T_LOOKUP - 0.1, T_LOOKUP + 0.5)
    # arms: hands in her lap; both reach up for the half, she takes it (far hand), brings it in
    # to her chest, a hand to her heart, then lets the bread rest in her lap as she leans on him
    near_side = -1.0
    far_side = 1.0
    _GXG.update(x=x, y=y, lean=lean, yaw=1.0 + G_TURN * 0.6)
    reach = _STATE.get("gnome_reach", (x + 60.0, y - 110.0))
    home = (x + 14.0 * SC, y - (ch.GNOME_SEAT_H + 22.0) * SC)
    lap = (x + 12.0 * SC, y - (ch.GNOME_SEAT_H + 4.0) * SC)
    r_near = (reach[0] - 9.0, reach[1] + 5.0)
    far_keys = [(T_HOP + 0.05, ("g", "rest"), "relaxed"), (T_HANDOFF, ("p", reach), "grip"),
                (T_HANDOFF + 0.1, ("p", reach), "grip"), (T_HANDOFF + 0.62, ("p", home), "grip"),
                (T_LEAN, ("p", home), "grip"), (T_LEAN + 0.8, ("p", lap), "grip")]
    near_keys = [(T_HOP + 0.12, ("g", "rest"), "relaxed"), (T_HANDOFF - 0.04, ("p", r_near), "cup"),
                 (T_HANDOFF + 0.1, ("p", r_near), "cup"), (T_HANDOFF + 0.62, ("p", (home[0] - 9.0, home[1] + 5.0)), "cup"),
                 (T_LOOKUP, ("p", (home[0] - 9.0, home[1] + 5.0)), "cup"), (T_LOOKUP + 0.5, ("g", "hand_on_chest"), "flat")]
    _GXG[far_side] = _keys_at(t, far_keys)
    _GXG[near_side] = _keys_at(t, near_keys)
    Lb = light_at(x, y - 160.0, boost=1.25)
    far = ch.GnomeArm("s8_gn", hold=_bread_cb("half", 1.0, "gnome", Lb) if t >= T_HANDOFF else None)
    near = ch.GnomeArm("s8_gn")
    blink = _blink_at(t, [2.1, T_LAUGH1 + 0.4, W_BREAD + 0.6, 11.0, T_LOOKUP + 0.25])
    # leaning on him: her eyes close, content
    blink = max(blink, 0.92 * core.smooth(core.clamp((t - (T_LEAN + 0.25)) / 0.45)))
    glint = core.clamp((t - (T_LOOKUP + 0.15)) / 0.5) if T_LOOKUP + 0.15 <= t <= T_LOOKUP + 0.65 else -1.0
    prog, hgt = hop_at(t)
    kick = 0.25 + 0.6 * hgt
    pose = ch.GnomePose(facing=1, turn=G_TURN, sit=1.0, look=look, head_turn=head_turn, head_nod=head_nod,
                        head_tilt=head_tilt, mood=mood, mood2=mood2, mood_mix=mix, smile=core.clamp(smile, -1, 1),
                        laugh=0.0, talk=0.0, blink=blink, glint=glint, near=near, far=far, satchel="empty",
                        satchel_side=-1, kick=kick,
                        hood_swing=0.5 * B.wobble(t, T_HOP + 0.32, 2.6, 3.0) / 1.35 + 0.3 * chk * math.sin((t - T_LAUGH) * 29.0),
                        seed=11)
    return x, y, pose


def draw_seat_birds(cr, t, bench):
    """S7's three pigeons, roosting on the seat between the faun and her: puffed up, asleep,
    breathing; the ring's laugh wakes them for a moment (an eye, a ruffle), then they settle."""
    for i, (u, f, seed) in enumerate(SEAT_BIRDS):
        x, y = bench._pt((u - 0.5) * (G.BENCH1.length - 60.0), -P.BENCH_SEAT_H - 1.0, 14.0)
        wake = _win(t, T_LAUGH + 0.1 + 0.12 * i, T_LAUGH + 1.3 + 0.25 * i, 0.12, 0.5)
        blink = 1.0 - 0.9 * wake
        look = (0.6 * f) if wake > 0.3 else None
        pose = ch.PigeonPose(facing=f, puff=0.9 + 0.08 * B.breathing(t, 0.3, seed) - 0.3 * wake, blink=blink,
                             look=look, tilt=0.12 * wake, seed=seed)
        ch.draw_pigeon(cr, x, y, SC, pose, light_at(x, y - 20.0), t)


def draw_sack(cr, t):
    """The apothecary sack of remedies -- the stones -- forgotten on the gravel by his foot."""
    x, y = SACK
    L = light_at(x, y + 40.0)
    P.draw_apothecary_bag(cr, x, y, SC, L.with_(exposure=L.exposure * 0.42, rim_strength=0.2), t, angle=0.05,
                          state="open", detail=LOD["props"])


def draw_gnome_leaning(cr, t, gx, gy, gpose):
    """Her, leaning (about her seat point) toward him at the end."""
    lean = lean_at(t)
    if lean:
        px, py = gnome_pivot(gx, gy)
        cr.save()
        cr.translate(px, py)
        cr.rotate(lean)
        cr.translate(-px, -py)
    rig = ch.draw_gnome(cr, gx, gy, SC, gpose, light_at(gx, gy - 160.0, boost=1.25), t, detail=LOD["gnome"])
    if lean:
        cr.restore()
    return rig


# ----------------------------------------------------------------------------------------
# the rest of the ring (idle life: listening, a laugh, a strum, a doze)
# ----------------------------------------------------------------------------------------

def faun_pose(t):
    x, y = _STATE["b1"].place(U1["faun"])
    laugh = _win(t, T_LAUGH + 0.05, T_LAUGH1, 0.12, 0.5)
    bite = _win(t, T_BITE - 0.45, T_BITE + 0.7, 0.35, 0.45)
    p = ch.FaunPose(facing=1, turn=-0.25, sit=1.0, hood=0.0, lean=0.18 + 0.12 * laugh,
                    look=_track(t, [(0.0, (0.9, 0.0)), (T_LOOK_F + 0.2, (0.9, 0.0)), (T_LOOK_F + 0.45, (0.7, -0.1)),
                                    (T_OFFER0, (0.7, -0.1)), (T_OFFER0 + 0.3, (0.95, 0.35)), (DUR, (0.95, 0.35))]),
                    head_nod=-0.05 + 0.08 * laugh + chuckle_bob(t, laugh, 4.0, 1.1), mood="warm",
                    mood2=RING_CHUCKLE if laugh > 0 else None, mood_mix=laugh, laugh=0.0, talk=0.0,
                    near=ch.Arm("eat", phase=max(0.002, bite), hold=ch.gnome_bread_hold("piece", light_at(x, y - 200))),
                    far=ch.Arm("knees"), seed=21)
    return x, y, p


def griffin_pose(t):
    x, y = GRIFFIN
    awake = _r(t, T_LAUGH + 0.05, T_LAUGH + 0.3)
    doze = _r(t, 12.6, 15.5)
    yawn = _win(t, T_LAUGH + 0.45, T_LAUGH + 1.65, 0.35, 0.45)
    blink = 1.0 - awake * (1.0 - doze * 0.85)
    blink = max(blink, 0.0) if yawn < 0.3 else max(blink, 0.8)
    head_nod = -0.32 * (1.0 - awake) - 0.3 * doze + 0.08 * B.breathing(t, 0.18, 31) + 0.2 * yawn
    p = ch.GriffinPose(facing=1, turn=-0.1, sit=1.0, mood="tired", blink=core.clamp(blink), head_nod=head_nod,
                       yawn=yawn, look=(0.5, 0.1), wings=-0.1 + 0.25 * yawn, tail_curl=1.0, seed=31)
    return x, y, p


def bard_pose(t):
    x, y = _STATE["b2"].place(U2["bard"])
    laugh = _win(t, T_LAUGH, T_LAUGH1, 0.15, 0.5)
    nod = 0.12 * _bump(t, T_LOOKUP + 0.3, 0.9)                         # a nod to the two of them
    p = ch.bard_cameo_pose(t, facing=-1, turn=0.32, period=1.4, seed=3, head_nod=-0.05 + 0.1 * laugh - nod,
                           smile=0.55 + 0.35 * laugh)
    return x, y, p


from film.lib.characters import _folk as _F    # noqa: E402  (the folk rig's gesture tuple)


def _g_s8_tale(q, sk, side, arm):
    """The dwarf's storytelling hand: hands on the knees (phase 0) <-> explaining at waist height
    (phase 1), lifted a little more for the punchline (_GX["dw_lift"]), with a lively wiggle. One
    continuous target with a constant hand, thumb and layer -- blending two library gestures would
    flip the hand and swap the arm's layer mid-move (a pop)."""
    k = core.inout_sine(core.clamp(arm.phase))
    kn = _F.g_knees(q, sk, side, arm)
    AL = q.b.upper_arm + q.b.forearm
    w = _GX.get("dw_wiggle", 0.0) * k
    lift = _GX.get("dw_lift", 0.0) * (1.0 if side == q.near else 0.7)
    talk = _v_add(sk, (side * (0.17 + 0.14 * lift) * AL, (0.46 + 0.05 * w - 0.2 * lift) * AL, (0.3 + 0.04 * lift) * AL))
    tgt = _v_lerp(kn.target, talk, k)
    arc = math.sin(math.pi * k) * 0.04 * AL
    return _F.G(_v_add(tgt, (0.0, -arc, arc)), "relaxed", kn.hang, kn.layer, kn.pole, kn.thumb)


ch.REGISTRY["dwarf"].DWARF_GESTURES["s8_tale"] = _g_s8_tale


def dwarf_pose(t):
    x, y = _STATE["b2"].place(U2["dwarf"])
    tale = _win(t, T_TALE0, T_TALE1, 0.25, 0.35)
    punch = _win(t, T_PUNCH - 0.12, T_LAUGH1 - 0.2, 0.12, 0.4)
    laugh = _win(t, T_LAUGH, T_LAUGH1 + 0.2, 0.1, 0.5)
    # the tale: his near hand explains; the punchline: both hands come up ("...and THAT was the
    # last of the cheese!"); one custom gesture throughout (no hand flips, no layer swaps)
    _GX["dw_wiggle"] = math.sin(t * math.tau * 1.2)
    _GX["dw_lift"] = punch
    near = ch.Arm("s8_tale", phase=max(tale, punch))
    far = ch.Arm("s8_tale", phase=0.85 * punch)
    nod = 0.07 * tale * math.sin(t * 4.3) + 0.12 * laugh + 0.1 * punch
    nod += chuckle_bob(t, laugh, 3.8, 2.0)
    # his tale is told in gestures (no line of his on the soundtrack: the beard stays still)
    p = ch.DwarfPose(facing=-1, turn=0.55, sit=1.0, lamp_lit=True, mood="happy",
                     mood2=RING_CHUCKLE if laugh > 0 else None, mood_mix=laugh, laugh=0.0, talk=0.0,
                     lean=0.15 * tale - 0.12 * laugh + 0.08 * punch, head_nod=nod, look=(-0.8, -0.1), near=near,
                     far=far, seed=41)
    return x, y, p


def elf_pose(t):
    x, y = _STATE["b2"].place(U2["elf"])
    laugh = _win(t, T_LAUGH + 0.1, T_LAUGH1 + 0.1, 0.2, 0.5)
    p = ch.ElfPose(facing=-1, turn=0.1, sit=1.0, hood=0.0, shells=0.0, glow=0.0, mood="kind",
                   mood2=RING_CHUCKLE if laugh > 0 else None, mood_mix=0.75 * laugh, smile=0.35 + 0.45 * laugh,
                   look=(-0.85, 0.0), head_nod=0.04 * laugh + chuckle_bob(t, 0.6 * laugh, 3.5, 0.4), seed=51)
    return x, y, p


# ----------------------------------------------------------------------------------------
# the set: the garden's cached layers, painted plane by plane with S8's night additions
# ----------------------------------------------------------------------------------------
_SET_KEYS = ("sky", "far", "hills", "back", "ground", "oak")


def _draw_moonhaze(cr):
    """A pale band of moonlit haze low in the sky behind the castle hill (far plane, cached): the
    castle, the hill and the town's roofs stand out against it as soft silhouettes."""
    cr.save()
    cr.translate(1000.0, 548.0)
    cr.scale(1.0, 0.16)
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, 1250.0)
    c = core.col("#5a6c9c")
    for off, a in ((0.0, 0.42), (0.35, 0.3), (0.7, 0.12), (1.0, 0.0)):
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], a)
    cr.set_source(pat)
    cr.arc(0, 0, 1250.0, 0, math.tau)
    cr.fill()
    cr.restore()


def paint_set(cr, cam, t, st):
    """Sky, stars, the moonlit haze, the castle on its hill, the town's cold lights on the hill's
    slopes, a drifting mist in the valley, the near hills, the garden and the oak -- back to front
    (Garden.paint_back's planes, with S8's additions slotted in at their depths; the static ones
    pre-merged per plane in setup: build_planes)."""
    g = st["g"]
    if "far_all" not in st:                          # (if the garden's internals ever change)
        g.paint_back(cr, cam, t, "night")
        draw_town(cr, cam, t, buildings=True)
        with cam.view(cr, G.PARALLAX["garden"]):
            st["pool"].paint(cr, alpha=0.96, operator=cairo.OPERATOR_ADD)
        return
    Lk = g.L["night"]
    PX = G.PARALLAX
    with cam.view(cr, PX["sky"]):
        Lk["sky"].paint(cr)
        if "stars" in Lk:
            Lk["stars"].draw(cr, t, alpha=1.0)
    _sky_grad(cr)
    with cam.view(cr, PX["far"]):
        st["far_all"].paint(cr)                      # moonlit haze + castle hill + the town's houses
    draw_town(cr, cam, t)
    with cam.view(cr, PX["far"]):
        st["mist"].draw(cr, t)
    with cam.view(cr, PX["hills"]):
        Lk["hills"].paint(cr)
    with cam.view(cr, PX["garden"]):
        st["garden_all"].paint(cr)                   # lawn, hedges, walk, beds + the lantern's warm pool
        Lk["oak"].draw(cr, t, alpha=1.0)


# the benches never move tonight: each part is cached once in a tight layer, supersampled so the
# camera's zoom never softens their outlines (world-px bounds x, y, w, h)
BENCH_BOX = {1: (540.0, 680.0, 640.0, 320.0), 2: (1330.0, 700.0, 560.0, 340.0)}
BENCH_RES = 1.45


def bench_light(which):
    if which == 1:
        return light_at(G.BENCH1.x + 120.0, G.BENCH1.y - 90.0)
    return light_at(G.BENCH2.x - 80.0, G.BENCH2.y - 90.0)


def build_benches(st):
    g = st["g"]
    for which in (1, 2):
        x, y, w, h = BENCH_BOX[which]
        L = bench_light(which)
        for part in ("back", "front"):
            st[f"bench{which}_{part}"] = fx.Layer(
                lambda cr, which=which, part=part, L=L: g.draw_bench(cr, 0.0, L, which=which, part=part, dim=BENCH_DIM),
                w=w, h=h, x=x, y=y, res=BENCH_RES)


def paint_bench(cr, st, which, part):
    """A bench part (inside the action-plane camera view)."""
    lay = st.get(f"bench{which}_{part}")
    if lay is not None:
        lay.paint(cr)
    else:
        st["g"].draw_bench(cr, 0.0, bench_light(which), which=which, part=part, dim=BENCH_DIM)


def build_planes(st):
    """Pre-merge the static art of each plane into one cached layer (one paint per plane per
    frame): far = moonlit haze + the garden's castle hill + the town's three houses; garden = the
    garden's back strip + near ground + the lantern's warm pool (baked at its mean flicker)."""
    g = st["g"]
    Lk = getattr(g, "L", {}).get("night", {})
    if any(k not in Lk for k in _SET_KEYS):
        return

    def far_all(cr):
        st["moonhaze"].paint(cr)
        Lk["far"].paint(cr)
        _town_static(cr)

    def garden_all(cr):
        Lk["back"].paint(cr)
        Lk["ground"].paint(cr)
        st["pool"].paint(cr, alpha=0.96, operator=cairo.OPERATOR_ADD)

    st["far_all"] = env.layer(far_all)
    st["garden_all"] = env.layer(garden_all)


# ----------------------------------------------------------------------------------------
# the far town: three small cold lights on the castle hill (far plane)
# ----------------------------------------------------------------------------------------
TOWN_DARK = "#111a33"
TOWN_ROOF = "#0c1328"
TEAL, MINT, MAGENTA, AMBER_TAV = "#5fe0d0", "#62f0a0", "#ff5fa8", "#ffb35a"
TK = 1.1                               # the town's drawing scale (its plane's px)


def _town_static(cr):
    """The three buildings, a step lighter than the roofline band behind them (cached): the
    wash-house (a long hall, a vent), the apothecary (a tall narrow house) and the tavern
    (a broad house with two gables)."""
    def poly(pts, col_):
        core.src(cr, col_)
        core.polygon(cr, pts)
        cr.fill()

    x, y = TOWN["washhouse"]
    k = TK
    poly([(x - 34 * k, y + 22 * k), (x - 34 * k, y - 2 * k), (x + 34 * k, y - 2 * k), (x + 34 * k, y + 22 * k)], TOWN_DARK)
    poly([(x - 38 * k, y - 1 * k), (x - 20 * k, y - 15 * k), (x + 20 * k, y - 15 * k), (x + 38 * k, y - 1 * k)], TOWN_ROOF)
    poly([(x + 14 * k, y - 13 * k), (x + 14 * k, y - 23 * k), (x + 21 * k, y - 23 * k), (x + 21 * k, y - 13 * k)], TOWN_ROOF)
    x, y = TOWN["apothecary"]
    poly([(x - 11 * k, y + 26 * k), (x - 11 * k, y - 6 * k), (x + 11 * k, y - 6 * k), (x + 11 * k, y + 26 * k)], TOWN_DARK)
    poly([(x - 14 * k, y - 5 * k), (x, y - 24 * k), (x + 14 * k, y - 5 * k)], TOWN_ROOF)
    x, y = TOWN["tavern"]
    poly([(x - 38 * k, y + 24 * k), (x - 38 * k, y - 2 * k), (x + 38 * k, y - 2 * k), (x + 38 * k, y + 24 * k)], TOWN_DARK)
    poly([(x - 41 * k, y - 1 * k), (x - 24 * k, y - 20 * k), (x - 7 * k, y - 1 * k)], TOWN_ROOF)
    poly([(x - 2 * k, y - 1 * k), (x + 19 * k, y - 23 * k), (x + 41 * k, y - 1 * k)], TOWN_ROOF)


def draw_town(cr, cam, t, k=1.0, buildings=False):
    """Per frame, in the hills plane: the cold lights (crisp cores; their halos are in the light
    layer, town_light). Each place keeps its colour from its own scene: the wash-house's teal
    porthole windows (the drums), the apothecary's green cross, the tavern's magenta lanterns."""
    K = TK
    with cam.view(cr, G.PARALLAX[TOWN_PLANE]):
        if buildings:
            _town_static(cr)
        # the wash-house: a row of round porthole windows glowing teal, a lit sign on a bracket
        x, y = TOWN["washhouse"]
        fl = 0.86 + 0.14 * math.sin(t * 2.3)
        for i in range(4):
            wx = x - 22 * K + 14.7 * K * i
            core.src(cr, "#2a6c70", 0.95 * k)
            core.circle(cr, wx, y + 8 * K, 4.6 * K)
            cr.fill()
            core.src(cr, TEAL, 0.95 * k * fl)
            core.circle(cr, wx, y + 8 * K, 3.4 * K)
            cr.fill()
        core.src(cr, TOWN_ROOF)
        cr.rectangle(x - 40 * K, y + 1 * K, 8 * K, 1.2 * K)
        cr.fill()
        core.src(cr, "#a8f2e6", 0.9 * k)
        core.rounded_rect(cr, x - 43 * K, y + 3 * K, 7 * K, 5 * K, 1.0 * K)
        cr.fill()
        # steam off the vent, drifting away
        for i in range(3):
            u = (t * 0.11 + i / 3.0) % 1.0
            core.src(cr, "#8fa8bc", 0.2 * (1.0 - u) * k)
            core.circle(cr, x + 17.5 * K + 9 * K * u + 2.5 * math.sin(t * 0.8 + i), y - 25 * K - 20 * K * u, (2.2 + 3.6 * u) * K)
            cr.fill()
        # the apothecary: a cold-lit window and the hanging sign's green cross
        x, y = TOWN["apothecary"]
        core.src(cr, "#bfffe2", 0.5 * k)
        cr.rectangle(x - 6 * K, y + 9 * K, 5 * K, 8 * K)
        cr.rectangle(x + 2 * K, y + 9 * K, 5 * K, 8 * K)
        cr.fill()
        sx, sy = x + 17 * K, y + 2 * K
        core.src(cr, TOWN_ROOF)
        cr.rectangle(x + 10 * K, y - 4.5 * K, 12 * K, 1.2 * K)
        cr.fill()
        core.src(cr, "#16243a")
        core.rounded_rect(cr, sx - 6 * K, sy - 6 * K, 12 * K, 12 * K, 1.5 * K)
        cr.fill()
        core.src(cr, MINT, 0.97 * k * (0.9 + 0.1 * math.sin(t * 1.3)))
        cr.rectangle(sx - 1.5 * K, sy - 4.6 * K, 3.0 * K, 9.2 * K)
        cr.rectangle(sx - 4.6 * K, sy - 1.5 * K, 9.2 * K, 3.0 * K)
        cr.fill()
        # the tavern: hot pink windows, two sagging strings of little paper lanterns
        x, y = TOWN["tavern"]
        for wx in (-26, -12, 10, 24):
            core.src(cr, MAGENTA, 0.6 * k)
            cr.rectangle(x + (wx - 3) * K, y + 7 * K, 6 * K, 8 * K)
            cr.fill()
        for row, (y0, n, x0, x1) in enumerate(((y - 1.0 * K, 8, x - 40 * K, x + 40 * K), (y + 19.0 * K, 7, x - 36 * K, x + 36 * K))):
            cr.set_line_width(0.6 * K)
            core.src(cr, "#3a2a3a", 0.8)
            cr.move_to(x0, y0)
            cr.curve_to(x0 + (x1 - x0) * 0.3, y0 + 9 * K, x0 + (x1 - x0) * 0.7, y0 + 9 * K, x1, y0)
            cr.stroke()
            for i in range(n):
                u = (i + 0.5) / n
                px = core.lerp(x0, x1, u)
                py = y0 + 6.8 * K * math.sin(math.pi * u)
                c = (MAGENTA, AMBER_TAV, "#e0508a")[(i + row) % 3]
                tw = 0.72 + 0.28 * math.sin(t * 3.1 + i * 1.7 + row)
                core.src(cr, c, 0.97 * k * tw)
                core.ellipse(cr, px, py + 1.0 * K, 1.6 * K, 2.0 * K)
                cr.fill()


def town_light(lc, cam, t, k=1.0):
    """The town's cold halos (light layer)."""
    K = TK
    with cam.view(lc, G.PARALLAX[TOWN_PLANE]):
        x, y = TOWN["washhouse"]
        fx.glow(lc, x, y + 8 * K, 62.0 * K, TEAL, 0.34 * k)
        x, y = TOWN["apothecary"]
        fx.glow(lc, x + 17 * K, y + 2 * K, 44.0 * K, MINT, 0.44 * k * (0.9 + 0.1 * math.sin(t * 1.3)))
        x, y = TOWN["tavern"]
        fx.glow(lc, x, y + 9 * K, 66.0 * K, MAGENTA, 0.3 * k)


BENCH_DIM = 0.72                       # the benches' wood a step under the cast (and it is night)


def _sky_grad(cr):
    """A graduated filter over the top of the frame: the sky deepens upward, so the moonlit
    clouds never compete with the lantern."""
    cr.save()
    cr.rectangle(0, 0, core.W, 400)
    cr.set_source(core.linear(0, 0, 0, 400, [(0.0, (0.01, 0.015, 0.05, 0.46)), (0.5, (0.01, 0.015, 0.05, 0.2)),
                                              (1.0, (0.01, 0.015, 0.05, 0.0))]))
    cr.fill()
    cr.restore()


_LUT = {}


def _night_lut():
    """The night grade: shadows deepen and cool toward ultramarine, mids lose a little red,
    highlights (the lamp, the faces in its light) stay warm."""
    if "n" not in _LUT:
        _LUT["n"] = fx.make_lut(r=lambda x: min(1.0, (x ** 1.06) * 1.04),
                                g=lambda x: min(1.0, (x ** 1.06) * 1.01),
                                b=lambda x: min(1.0, 0.012 + (x ** 0.97) * 0.99))
    return _LUT["n"]


# ----------------------------------------------------------------------------------------
# the dark: a cached world-space falloff (the garden falls away into night beyond the ring)
# ----------------------------------------------------------------------------------------
POOL_C = (1240.0, 935.0)               # the middle of the warm pool on the ground (under the lamp)
DARK_C = (1235.0, 770.0)               # the centre of the light's reach (between the lamp and its pool)


def _draw_dark(cr):
    """The night beyond the ring (world space, cached): clear round the lamp, darkening with
    distance; the sky above the hedges is spared (moon, stars, castle), the oak sinks into
    silhouette, the near ground darkens toward the lens."""
    cx, cy = DARK_C
    cr.push_group()
    cr.save()
    cr.translate(cx, cy)
    cr.scale(1.0, 0.6)
    R = 1150.0
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, R)
    for off, a in ((0.0, 0.0), (0.22, 0.0), (0.36, 0.14), (0.5, 0.36), (0.65, 0.57), (0.8, 0.72), (1.0, 0.84)):
        pat.add_color_stop_rgba(off, 0.006, 0.012, 0.035, a)
    cr.set_source(pat)
    cr.paint()
    cr.restore()
    cr.pop_group_to_source()
    cr.mask(core.linear(0, 520.0, 0, 720.0, [(0.0, (0, 0, 0, 0.0)), (1.0, (0, 0, 0, 1.0))]))
    # the old oak's crown: a dark silhouette against the night sky
    cr.save()
    cr.translate(G.OAK[0] + 40.0, 470.0)
    cr.scale(1.0, 0.62)
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, 560.0)
    pat.add_color_stop_rgba(0.0, 0.006, 0.012, 0.035, 0.55)
    pat.add_color_stop_rgba(0.7, 0.006, 0.012, 0.035, 0.42)
    pat.add_color_stop_rgba(1.0, 0.006, 0.012, 0.035, 0.0)
    cr.set_source(pat)
    cr.paint()
    cr.restore()


def _draw_pool(cr):
    """The lantern's warm pool on the gravel and grass (world space, cached; painted ADD)."""
    cx, cy = POOL_C
    cr.save()
    cr.translate(cx, cy)
    cr.scale(1.0, 0.25)
    R = 720.0
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, R)
    c = core.col("#ffae5c")
    for off, a in ((0.0, 0.5), (0.15, 0.42), (0.35, 0.26), (0.6, 0.11), (0.82, 0.035), (1.0, 0.0)):
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], a)
    cr.set_source(pat)
    cr.arc(0, 0, R, 0, math.tau)
    cr.fill()
    cr.restore()
    # light on the back hedge behind the lamp (it lights what is behind it too)
    cr.save()
    cr.translate(cx + 10.0, 760.0)
    cr.scale(1.0, 0.45)
    pat = cairo.RadialGradient(0, 0, 0, 0, 0, 520.0)
    for off, a in ((0.0, 0.16), (0.5, 0.06), (1.0, 0.0)):
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], a)
    cr.set_source(pat)
    cr.arc(0, 0, 520.0, 0, math.tau)
    cr.fill()
    cr.restore()


# ----------------------------------------------------------------------------------------
# cast shadows: everything in the pool throws a soft shadow AWAY from the lamp
# ----------------------------------------------------------------------------------------

def _shadows(cr, cam, casters):
    """Soft shadows radiating from the lamp's foot across the ground (quarter-res, one upscale)."""
    buf = _STATE["shadow_buf"]
    c = cairo.Context(buf)
    c.set_operator(cairo.OPERATOR_CLEAR)
    c.paint()
    c.set_operator(cairo.OPERATOR_OVER)
    c.scale(0.25, 0.25)
    c.transform(cam.matrix(1.0))
    lx = lamp()[0]
    gy = G.GROUND_Y + 12.0
    for (x, y, w, h, a) in casters:
        dx = x - lx
        n = math.hypot(dx, 120.0)
        ux, uy = dx / n, 120.0 / n * 0.35
        L = h * 0.55 * (0.6 + 0.4 * min(1.0, abs(dx) / 300.0))
        tip = (x + ux * L, y + uy * L)
        c.new_path()
        core.tapered(c, [(x, y), ((x + tip[0]) * 0.5, (y + tip[1]) * 0.5), tip], w * 0.9, w * 0.5, cap=True)
        c.set_source(core.linear(x, y, tip[0], tip[1], [(0.0, core.alpha("#04060f", 0.5 * a)),
                                                         (1.0, core.alpha("#04060f", 0.0))]))
        c.fill()
    buf.flush()
    cr.save()
    cr.identity_matrix()
    cr.scale(4.0, 4.0)
    cr.set_source_surface(buf, 0, 0)
    cr.get_source().set_filter(cairo.FILTER_BILINEAR)
    cr.paint()
    cr.restore()


# ----------------------------------------------------------------------------------------
# life in the air: fireflies over the dark lawn, moths round the lamp
# ----------------------------------------------------------------------------------------

def _moths(cr, t):
    lx, ly = lamp()
    for i in range(6):
        a = t * (1.9 + 0.8 * core.hash01(i, 81)) + i * 1.9
        r = 22.0 + 26.0 * core.hash01(i, 82)
        px = lx + math.cos(a) * r + 8.0 * core.noise1(t * 1.3 + i, 83)
        py = ly + 6.0 + math.sin(a * 1.27) * r * 0.6 + 6.0 * core.noise1(t * 1.5 + i, 84)
        flap = 0.5 + 0.5 * math.sin(t * 38.0 + i * 2.0)
        core.src(cr, "#fff0d0", 0.75)
        core.ellipse(cr, px, py, 1.1 + 1.3 * flap, 0.9)
        cr.fill()


def _fireflies(cr, t, k=1.0):
    fx.fireflies(cr, t, (-60.0, 760.0, 700.0, 300.0), n=9, color="#d8ff7a", size=2.0, seed=91, alpha=0.85 * k, speed=0.8)
    fx.fireflies(cr, t, (1780.0, 720.0, 260.0, 330.0), n=5, color="#d8ff7a", size=2.0, seed=92, alpha=0.85 * k, speed=0.8)
    fx.fireflies(cr, t, (300.0, 640.0, 1500.0, 120.0), n=8, color="#c8f070", size=1.6, seed=93, alpha=0.7 * k, speed=0.7)
    fx.fireflies(cr, t, (200.0, 1000.0, 1700.0, 140.0), n=6, color="#d8ff7a", size=2.3, seed=94, alpha=0.8 * k, speed=0.9)


# ----------------------------------------------------------------------------------------
# sound cues (the sound designer synthesizes foley from these; times follow the animation)
# ----------------------------------------------------------------------------------------

def _pan(x_world, t):
    cam = Cam.lerp(CAM_A, CAM_B, pull(t))
    sx, _ = cam.to_screen(x_world, 800.0)
    return round(core.clamp((sx - 960.0) / 960.0, -1.0, 1.0), 2)


def _sfx_cues():
    """Every on-screen event that should make a sound, at the times the animation uses. (The ring's
    laugh is silent -- closed-mouth chuckles -- so it gets only the bodies' small sounds; the
    bard's strumming is silent: the score carries the music; crickets/murmur are ambience.)"""
    xb1 = lambda u: G.BENCH1.x + (u - 0.5) * (G.BENCH1.length - 60.0) * SC          # noqa: E731
    xb2 = lambda u: G.BENCH2.x + (u - 0.5) * (G.BENCH2.length - 60.0) * SC * math.cos(G.BENCH2.yaw)  # noqa: E731
    xd, xg, xf, xw = xb1(U1["dragon"]), xb1(U1["gnome"]), xb1(U1["faun"]), xb2(U2["dwarf"])
    xbird = xb1(SEAT_BIRDS[0][0])
    cues = [
        # the dwarf's punchline: both hands up; the ring's silent chuckle (bodies, bench, wings)
        (T_PUNCH - 0.05, "cloth_rustle", {"gain": 0.18, "pan": _pan(xw, T_PUNCH), "size": 0.3, "dist": 0.3}),
        (T_LAUGH + 0.06, "bench_creak", {"gain": 0.22, "pan": _pan(xw, T_LAUGH), "size": 0.3, "dist": 0.3}),
        (T_LAUGH + 0.1, "cloth_rustle", {"gain": 0.16, "pan": _pan(xf, T_LAUGH), "size": 0.3, "dist": 0.2}),
        (T_LAUGH + 0.12, "wing_flutter", {"gain": 0.16, "pan": _pan(xd, T_LAUGH), "size": 0.3}),
        (T_LAUGH + 0.22, "bench_creak", {"gain": 0.18, "pan": _pan(xd, T_LAUGH), "size": 0.25}),
        # the roosting seat pigeons stir, and the courier's big yawn
        (T_LAUGH + 0.3, "pigeon_coo", {"gain": 0.1, "pan": _pan(xbird, T_LAUGH), "dist": 0.2}),
        (T_LAUGH + 0.6, "sigh", {"gain": 0.24, "pan": _pan(GRIFFIN[0], T_LAUGH + 0.6), "who": "griffin"}),
        # the faun's bite of crust
        (T_BITE, "bread_tear", {"gain": 0.16, "pan": _pan(xf, T_BITE), "size": 0.2, "dist": 0.2}),
        # L3: he lifts the bread; it breaks on "break" (crust, crumbs)
        (T_LIFT + 0.05, "cloth_rustle", {"gain": 0.12, "pan": _pan(xd, T_LIFT), "size": 0.25}),
        (T_SNAP, "bread_tear", {"gain": 0.6, "pan": _pan(xd - 10.0, T_SNAP), "size": 0.6}),
        (T_SNAP + 0.04, "crumbs", {"gain": 0.2, "pan": _pan(xd - 10.0, T_SNAP)}),
        # he holds her half out on his palm; she hops along the seat to him and takes it
        (T_OFFER0 + 0.1, "cloth_rustle", {"gain": 0.12, "pan": _pan(xd - 30.0, T_OFFER0), "size": 0.25}),
        (T_HOP + 0.02, "cloth_rustle", {"gain": 0.14, "pan": _pan(xg, T_HOP), "size": 0.2}),
        (T_HOP + 0.32, "bench_creak", {"gain": 0.18, "pan": _pan(xg, T_HOP), "size": 0.2}),
        (T_HANDOFF, "cloth_rustle", {"gain": 0.1, "pan": _pan(xg + 40.0, T_HANDOFF), "size": 0.15}),
        # she leans her head against his coat
        (T_LEAN + 0.1, "cloth_rustle", {"gain": 0.12, "pan": _pan(xg + 30.0, T_LEAN), "size": 0.2}),
    ]
    out = [(round(tc, 3), k, p) for tc, k, p in cues if 0.0 <= tc < DUR]
    return sorted(out, key=lambda c: c[0])


SFX_CUES = _sfx_cues()


# ----------------------------------------------------------------------------------------
# setup
# ----------------------------------------------------------------------------------------

def setup():
    st = {}
    _STATE.clear()
    _CAP.clear()
    g = G.Garden(kinds=("night",))
    st["g"] = g
    _STATE["g"] = g
    _STATE["b1"] = g.bench(1)
    _STATE["b2"] = g.bench(2)
    st["light"] = fx.LightLayer()
    _STATE["shadow_buf"] = core.new_surface(core.W // 4, core.H // 4)
    post = g.draw_lantern(_scratch(), 0.0, G.light_for("night"), lit=1.0)
    _STATE["lamp"] = post.lamp
    st["dark"] = env.layer(_draw_dark)
    st["moonhaze"] = env.layer(_draw_moonhaze, blur=4.0)
    st["mist"] = env.Mist(-90.0, 538.0, 2100.0, 70.0, "#4c5a86", alpha=0.32, seed=8, speed=3.0, scale=2.6)
    st["pool"] = env.layer(_draw_pool)
    build_planes(st)
    build_benches(st)
    _probe_dragon()
    _calibrate_grips()
    _CAP.pop("whole", None)
    _rig_at(T_SNAP - 1e-3)
    _STATE["snap_at"] = _CAP.get("whole", dragon_anchor())
    _solve_handoff()
    return st


def _probe_dragon():
    """Record his seated skeleton once (scratch draw) and build the hands' rest points from it."""
    x, y = dragon_anchor()
    pose = ch.DragonPose(facing=0, turn=D_TURN, sit=1.0, tail_front=True, hunch=0.4, lean=0.08,
                         near=ch.Arm("s8_probe"), far=ch.Arm("rest"), seed=8)
    ch.draw_dragon(_scratch(), x, y, SC, pose, NIGHT, 0.0)
    c = _STATE.pop("probe")
    _STATE["lap"] = _lap(c)
    kn = c["knee"][0]
    hip = c["hip"][-1.0]
    _STATE["knee_rest"] = _v_add(_v_lerp(hip, kn, 0.6), (-8.0, -24.0, -8.0))     # the seated "rest" target
    # her half, held out on his open palm at the near edge of his own lap: his arm stays at his side
    # (it never crosses her); she comes to him to take it
    _STATE["offer_body"] = _v_add(_STATE["lap"], OFFER_AT)


def _rig_at(t):
    x, y, pose = dragon_pose(t)
    return ch.draw_dragon(_scratch(), x, y, SC, pose, NIGHT, t)


def _calibrate_grips():
    """The two-hand prop draws in a frame at the midpoint of the forearms' grip points, before the
    hands; measure where each hand's own grip lands relative to that frame (scratch draws over the
    lift and the break), so the bread -- and each half after the snap -- sits exactly in the hands."""
    _STATE["grips"] = None
    ts = [0.0, T_LIFT - 0.05]
    k = T_LIFT
    while k < T_PART - 1e-3:
        ts.append(k)
        k += 1.0 / 48.0
    ts.append(T_PART - 1e-4)
    tab = []
    for tt in sorted(set(ts)):
        _CAP.pop("frame0", None)

        def probe(cr, f):
            _CAP["frame0"] = cr.user_to_device(0.0, 0.0)
        x, y, pose = dragon_pose(tt)
        pose = pose.with_(near=pose.near.__class__(**{**pose.near.__dict__, "hold": probe}))
        rig = ch.draw_dragon(_scratch(), x, y, SC, pose, NIGHT, tt)
        ox, oy = _CAP["frame0"]
        n = ((rig.hand_near.x - ox) / SC, (rig.hand_near.y - oy) / SC)
        f = ((rig.hand_far.x - ox) / SC, (rig.hand_far.y - oy) / SC)
        tab.append((tt, n, f))
    _STATE["grips"] = tab


def _solve_handoff():
    """Where her half changes hands: on his open palm at T_HANDOFF (a scratch draw), then her far
    wrist target solved (fixed-point steps on the measured bread) so the bread in HER hand sits on
    exactly that spot at the hand-over -- no jump between the hands."""
    _CAP.pop("give", None)
    _rig_at(T_HANDOFF - 1e-3)
    want = _CAP.get("give", dragon_anchor())
    _STATE["handoff_at"] = want
    reach = (want[0] - 4.0, want[1] + 6.0)
    for _ in range(5):
        _STATE["gnome_reach"] = reach
        _CAP.pop("gnome", None)
        gx_, gy_, gp = gnome_pose(T_HANDOFF + 1e-3)
        ch.draw_gnome(_scratch(), gx_, gy_, SC, gp, NIGHT, T_HANDOFF + 1e-3)
        got = _CAP.get("gnome", want)
        reach = (reach[0] + (want[0] - got[0]), reach[1] + (want[1] - got[1]))
    _STATE["gnome_reach"] = reach
    _CAP.pop("gnome", None)
    gx_, gy_, gp = gnome_pose(T_HANDOFF + 1e-3)
    ch.draw_gnome(_scratch(), gx_, gy_, SC, gp, NIGHT, T_HANDOFF + 1e-3)
    _STATE["gnome_got"] = _CAP.get("gnome", want)


# ----------------------------------------------------------------------------------------
# draw
# ----------------------------------------------------------------------------------------

def draw(cr, t, st):
    g = st["g"]
    cam = camera(t)
    b1, b2 = _STATE["b1"], _STATE["b2"]
    Lnight = G.light_for("night")
    dx, dy, dpose = dragon_pose(t)
    gx, gy, gpose = gnome_pose(t)
    fx_, fy_, fpose = faun_pose(t)
    rx, ry, rpose = griffin_pose(t)
    bx, by, bpose = bard_pose(t)
    wx, wy, wpose = dwarf_pose(t)
    ex, ey, epose = elf_pose(t)

    # ---- the set: sky, castle, town, garden
    paint_set(cr, cam, t, st)
    fl = flicker(t)
    casters = [(dx, dy, 90.0, 300.0, 1.0), (gx, gy, 40.0, 180.0, 0.8), (fx_, fy_, 60.0, 260.0, 0.8),
               (bx, by, 50.0, 190.0, 0.9), (wx, wy, 60.0, 230.0, 0.8), (ex, ey, 50.0, 270.0, 0.6),
               (rx, ry, 110.0, 280.0, 0.5), (G.BENCH1.x, G.BENCH1.y, 300.0, 200.0, 0.6),
               (G.BENCH2.x, G.BENCH2.y, 260.0, 200.0, 0.6)]
    _shadows(cr, cam, casters)

    with cam.view(cr, 1.0):
        post = g.draw_lantern(cr, t, Lnight.with_(exposure=0.8), lit=1.0)
        # bench 1 and its sitters
        paint_bench(cr, st, 1, "back")
        draw_seat_birds(cr, t, b1)
        ch.draw_faun(cr, fx_, fy_, SC, fpose, light_at(fx_, fy_ - 230.0), t, detail=LOD["faun"])
        ch.draw_dragon(cr, dx, dy, SC, dpose, light_at(dx, dy - 260.0, boost=1.1), t, detail=LOD["dragon"])
        draw_gnome_leaning(cr, t, gx, gy, gpose)       # at the seat's front edge: in front of his near side
        draw_sack(cr, t)                                # set down by the bench end: its leg in front
        paint_bench(cr, st, 1, "front")
        # the little spray of crumbs when the bread snaps, and a curl of steam from the soft crumb
        # (as from her loaf in S7): warm breath in the cold night air -- the break is the event
        if T_SNAP <= t < T_SNAP + 2.8 and "snap_at" in _STATE:
            sx_, sy_ = _STATE["snap_at"]
            fx.crumbs(cr, t, T_SNAP, sx_, sy_, n=7, seed=8, vx=(-60.0, 60.0), vy=(-90.0, -10.0),
                      ground_y=G.GROUND_Y + 16.0, size=2.0, color=ch.GNOME_COLORS["crumb"],
                      crust=ch.GNOME_COLORS["crust"], scale=SC, release=0.05)
            fx.smoke(cr, t, T_SNAP + 0.02, sx_, sy_ - 6.0, n=8, dur=2.4, rise=110.0, drift=(-12.0, 0.0), size=4.6,
                     color="#f6e6cc", alpha=0.55, seed=12, scale=SC, spread=0.5)
        # bench 2 and its sitters
        paint_bench(cr, st, 2, "back")
        ch.draw_bard(cr, bx, by, SC, bpose, light_at(bx, by - 170.0, boost=1.1), t, detail=LOD["bard"])
        ch.draw_dwarf(cr, wx, wy, SC, wpose, light_at(wx, wy - 200.0), t, detail=LOD["dwarf"])
        Le = light_at(ex, ey - 220.0)
        ch.draw_elf(cr, ex, ey, SC, epose, Le.with_(exposure=Le.exposure * 0.8), t, detail=LOD["elf"])
        paint_bench(cr, st, 2, "front")
        # the griffin on the grass, the pigeons roosting by the post
        ch.draw_griffin(cr, rx, ry, SC, rpose, light_at(rx, ry - 200.0, rim_k=1.3), t, detail=LOD["griffin"])
        for (px, py, f, seed) in PIGEONS:
            ch.draw_pigeon(cr, px, py, SC, ch.PigeonPose(facing=f, puff=0.9 + 0.08 * B.breathing(t, 0.33, seed),
                                                         blink=1.0, seed=seed), light_at(px, py - 20.0), t)
    # the night beyond the ring
    with cam.view(cr, 1.0):
        st["dark"].paint(cr)
        _moths(cr, t)
        _fireflies(cr, t)
    g.paint_fg(cr, cam, t, "night")

    # ---- light
    lc = st["light"].begin()
    g.light(lc, cam, t, "night")
    town_light(lc, cam, t)
    with cam.view(lc, 1.0):
        lx, ly = lamp()
        fx.glow(lc, lx, ly, 420.0, "#ffb05a", 0.3 * fl)
        # the light falling from the lantern: a soft warm cone down onto the ring and the gravel
        fx.light_shaft(lc, lx, ly + 18.0, lx - 70.0, G.GROUND_Y + 30.0, 70.0, 820.0, "#ffb468", 0.11 * fl,
                       soft=4, fade_start=0.2, fade_end=0.55)
        fx.glow(lc, lx, ly, 110.0, "#ffe2a8", 0.45 * fl)
        fx.glow(lc, DARK_C[0] - 60.0, DARK_C[1], 700.0, "#ff9d50", 0.05 * fl)
        # the break: a soft warm breath of light from the torn crumb, swelling and settling
        if "snap_at" in _STATE:
            k = _win(t, T_SNAP - 0.05, T_SNAP + 1.6, 0.12, 1.1)
            if k > 0:
                bx_, by_ = _STATE["snap_at"]
                fx.glow(lc, bx_, by_, 120.0, "#ffc070", 0.28 * k)
        # the lamplight's warm radiance round the ring (it lights the faces nearest it most)
        fx.glow(lc, lx - 170.0, 735.0, 470.0, "#ffa860", 0.13 * fl)
        fx.glow(lc, lx + 230.0, 790.0, 330.0, "#ffa860", 0.07 * fl)
    fx.grade_lut(cr, _night_lut())
    fx.post(cr, t, light=st["light"], bloom_strength=0.62, threshold=0.6, bloom_radius=2.2, wide=0.4, grain=0.038,
            vignette=0.56, vignette_color=(0.01, 0.01, 0.04))
    # ---- the night closes in toward the lantern, then black
    if t > T_FADE0:
        _fade(cr, cam, t)


def _fade(cr, cam, t):
    u = core.clamp((t - T_FADE0) / (T_FADE1 - T_FADE0))
    lx, ly = cam.to_screen(*lamp())
    cx, cy = (lx + cam.to_screen(*POOL_C)[0]) * 0.5, (ly + cam.to_screen(*POOL_C)[1]) * 0.5
    r0 = core.lerp(1500.0, 0.0, core.inout_sine(u))
    pat = cairo.RadialGradient(cx, cy, r0 * 0.25, cx, cy, r0 + 700.0)
    pat.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
    pat.add_color_stop_rgba(1.0, 0, 0, 0, 1.0)
    cr.save()
    cr.set_source(pat)
    cr.paint_with_alpha(core.smooth(core.clamp(u * 1.6)))
    cr.restore()
    fx.fade(cr, core.ramp(t, T_FADE0 + 0.8, T_FADE1, "in_quad"))
