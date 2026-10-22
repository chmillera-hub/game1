"""s5_crowd.py -- SCENE 5: THE CROWD  (25.0 s, evening; a corner of the town square)

    "We'll film a fight. But someone gets gentle, and everybody looks away."

EMOTION. Cold voyeurism, then a tenderness nobody can bear to watch. The square is a ring of
cold cyan crystal-light around two brawlers; the light IS the voyeurism (every glow is an eye).
When the orc stops himself and hugs the minotaur, the ring falls silent and the eyes go out one
by one. The dragon, across the street in the arcade's shadow, is the only one who keeps looking.
The last image: the two of them holding on, alone on the cobbles, a pale shaft of grace falling
on them through a break in the cloud -- the scene's only warmth, and only "a little" (SPEC 0.3:
the first warm light that comes from HIM is his laugh in S6; this one falls from the sky).

WORLD (one perspective model for every shot). Ground point (X lateral, D depth) projects to
sx = 960 + X*F/D, sy = 470 + 560*F/D (horizon 470, camera 560 units up, F = 1000), so a creature
standing there is drawn at scale F/D: the ring (D 1354..2185) runs 0.74 -> 0.46, the fighters
at D0 = 1724 are 0.58. Far side of the square (D 4300): a row of half-timbered houses, shutters
closed, against the last pale band of evening sky. In the square: a stone well with a shingled
roof and windlass (right), closed market stalls under lashed canvas, crates, barrels, a hand-cart
and an unlit lantern post. The near side is screen-space: the dragon stands under the stone
arcade of a house across the street -- its dark pier and arch frame the left and top edges.
Period: stone, oak, canvas, wool, iron; the "phones" are scrying crystals. Nothing modern.
Each set-up's backdrop is baked once at its own framing with its own depth of field (Baked);
moving cameras paint it through the residual transform, the foreground with extra parallax.

SHOTS (cuts derive from the timeline; times below are for the current timeline.json)
 1  0.00-3.88  MASTER WIDE across the street, slow dolly-in. Framing device: the dark arch of
               the arcade (pier at the left, the arch ring over the top), out of focus. The
               dragon left, near profile, hands in his coat pockets, wings drooped, a stop
               darker than the square with a cold cyan rim. Beyond him the ring of 14 creatures
               (goblins, kobolds, elves, dwarves, two harpies) holds crystals up, cheering; the
               pixie hovers over them, filming. Eye trace: the cyan ring (brightest) -> the
               brawl -> back along the dragon's gaze. Two shoves (anticipation, thrust, impact,
               stagger); the dragon winces at each impact.
 2  3.88-5.33  INSERT: ONE CRYSTAL. A kobold's claw holds a scrying crystal up in the
               foreground; it GLOWS (a halo of cold light, rune motes rising off it, a glint
               round the brass collar) -- the brightest thing in the film so far; inside, the
               fight, small and sharp, under the pulsing red recording rune; the real brawl
               behind is soft bokeh: they watch the image, not the people. Cut on the impact.
 3  5.33-13.00 IN THE CIRCLE, long lens: only the fighters' plane is sharp (far arc soft,
               crystals turned to bokeh; near arc soft, dark, backlit). Handheld while they
               fight (a jolt on every impact). The shoving ESCALATES -- the minotaur's 4th is
               the hardest, the orc reels -- and the orc goes for real: he cocks a FIST back by
               his ear, the minotaur flinches, eyes squeezed shut, face turned away ...
               s5_stop: the fist freezes at the top of the wind-up (a jolt, held, trembling);
               the minotaur's eyes pop open (no blow?); the orc's brows jump -- what am I
               doing? -- the fist uncurls, the arms FALL, the head sinks; eyes down ... eyes up
               to him; two quick steps in. The minotaur's hands go up and out of the way
               ("whoa") -- s5_hug: the orc wraps his arms round him, his cheek on the
               minotaur's chest, his face turned to us, eyes sinking shut, a small smile. The
               minotaur freezes with both hands up ("I didn't do anything!"). The camera locks
               off and pushes in slowly from the stop. s5_silence: the cheering mouths close,
               arms come down. s5_lower: the crystals come down one by one, the cyan pool on
               the cobbles drains, uneasy glances. His eyes dart to the crowd, come down to the
               orc ... his far arm comes over the orc's shoulders, the near one round his back
               (low: nothing crosses the orc's face), his head turns to us, his jaw comes to
               rest on the orc's crown, eyes closing.
 4 13.00-15.65 THE PIXIE, medium close-up (her own set-up near the lens, 3/4 toward the pair,
               who sit soft on the left third behind her). Her crystal comes down off her face;
               she stares down at the hug and her face curdles (lip curl, knit brows) -- "Ew."
               (the head jerks back, nose up) -- "What is he doing?" (head cocked, one brow up,
               her free hand flicks out at them, palm up) -- an eye-roll up and away, and the
               crystal comes back up to her chin, its cold light washing over her face.
 5 15.65-22.14 THE DRAGON, medium close-up from the arcade (the pier and arch at the left and
               top), slow push-in; the square beyond him a little soft so he reads first, a
               soft cold bounce off the square on his face. Thought -> glance -> breath ->
               line: his eyes drop on the thought; "We'll film a fight." with a dry, rueful
               half-smile on "fight"; his eyes follow the bored ones drifting off; a breath in;
               "But someone gets gentle," (his brows lift and soften toward the two of them)
               "and everybody looks away." -- on the line the whole ring turns its back on the
               pair, crystals glowing in their faces again, and walks off in every direction;
               his eyes sweep after the turning backs, then sink; a slow blink.
 6 22.14-25.00 THE EMPTIED SQUARE (s5_alone): the master's frame again, bookending shot 1 --
               an ellipsis: the crowd is gone but for a few far figures at the edges, their
               cold glows scattering away. The evening sinks in round the two of them, still
               holding on, rocking a little (two slow pats on the orc's back). A break in the
               cloud opens: one soft shaft of pale rose-gold (a few rays breathing inside it,
               motes drifting) falls on them only, a pool at their feet, a warm rim on their
               heads and shoulders -- quiet, almost holy. Slow push in on them. The dragon
               stays in the arcade's shadow, watching; a sigh (a curl of grey smoke), his
               brows soften, his wings lift a fraction, the faintest warmth on his face.

COLOUR / VALUE. Dominant grey-blue (sky #2c3650 -> #b4b8c0, stone #6a7286); the one accent is
the crystals' cyan (#5fe0ff) -- the brightest values in the frame while they are raised, and
they bloom; the orc's red jerkin is the only warm hue. The circle is lit from inside (a cyan
pool on the cobbles, a haze glow over the ring, cyan rims on the brawlers); when the crystals
lower, that light drains and the frame goes flat and grey; at the end the square darkens round
the pair and a pale warm shaft lifts them out of it -- the brightest, warmest place in the
frame, and the only one. The dragon sits a stop darker than the square (the arcade's shadow)
in the wides; in his close-up a cold bounce lifts his face. Vignette tinted deep blue.

ACTING. Eyes lead, then the head, then the body. Every hold moves (breathing, blinks, sway,
the pixie's buzzing wings, the minotaur's tail). The orc: fury -> the punch wound up -> frozen
-> the anger drains (brows jump, then fall; the fist opens) -> eyes down -> eyes up to the
minotaur -> two steps -> the hug, face to us, eyes closing, a small smile. The minotaur: fury
-> a flinch (eyes shut, face turned away) -> eyes open: no blow? -> wary (hands up and away as
the orc comes) -> frozen, hands up -> eyes dart to the crowd, then down to the orc -> his arms
close round him, head turned to us, jaw on the orc's crown, eyes closed. The crowd: glee ->
confusion -> shock -> silence -> discomfort (glances) -> they look away. Lip-sync: the pixie
only on s5_l1 (her close-up), the dragon only on s5_l2/s5_l3 (his close-up), from
timeline.talk; none of the lines is voiceover; the extras' cheering mouths are procedural and
shut from s5_silence on.

SOUND. SFX_CUES (bottom of the file) are derived from the same constants the animation uses:
the four shove impacts (+ crowd bursts and the stumble), the punch wind-up and the flinch, the
arms falling, the steps in, the hug, the crystals coming down one by one (chimes), the
minotaur's arms and pats, the pixie's wings, the crowd turning away and walking off (footsteps
only while a walker is on screen; after the ellipsis only the few still in the square), the
dragon's sigh and smoke.
"""

import math
import random
from dataclasses import dataclass, replace

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib import timeline as tl
from film.lib import characters as ch
from film.lib.characters import base as B
from film.lib.characters import crowd as CW
from film.lib.characters import minotaur as MN
from film.lib.characters import orc as ORC
from film.lib.characters import _folk as FK
from film.lib.characters import pixie as PX

SCENE = 5
W, H = core.W, core.H
TAU = math.tau
clamp, lerp, smooth = core.clamp, core.lerp, core.smooth

# ----------------------------------------------------------------------------------------
# timing (all from the timeline; nothing hard-coded but derived offsets)
# ----------------------------------------------------------------------------------------

DUR = tl.scene(SCENE).duration
T_STOP = tl.beat("s5_stop").t
T_HUG = tl.beat("s5_hug").t
T_SIL = tl.beat("s5_silence").t
_LOW = tl.beat("s5_lower")
T_LOW0, T_LOW1 = _LOW.t, (_LOW.end if _LOW.end is not None else _LOW.t + 2.2)
L1, L2, L3 = tl.line("s5_l1"), tl.line("s5_l2"), tl.line("s5_l3")
T_ALONE = tl.beat("s5_alone").t if tl.has_beat("s5_alone") else L3.end + 0.4


def _word(line_id, k, default):
    try:
        return tl.word_times(line_id)[k][1]
    except Exception:
        return default


# the shoves escalate: each faster and harder (who, wind-up start, cycle length, power).
# The last one is the orc's payback -- frozen in its wind-up at s5_stop, never thrown.
# Four shoves escalate; then the orc, shoved hardest, goes for real: he cocks a FIST back by his
# ear (body twisting away, the minotaur flinching with his eyes shut) -- and freezes at the top
# of the wind-up at s5_stop. The fist never comes.
IMPACT_U = 0.42                                   # cycle fraction where the hands land
T_COCK = T_STOP - 0.62                            # the punch wind-up starts (it peaks at s5_stop)
T_DROP = T_STOP + 0.45                            # ... the fist opens, then his arms fall (0.26 s)
SHOVES = [("orc", T_STOP - 8.35, 2.30, 0.80),
          ("mino", T_STOP - 6.05, 2.10, 1.00),
          ("orc", T_STOP - 3.95, 1.85, 1.25),
          ("mino", T_STOP - 2.10, 1.43, 1.60)]           # fastest; settles before the wind-up


def _impact_t(i):
    who, t0, per, pw = SHOVES[i]
    return t0 + IMPACT_U * per


IMPACTS = [(_impact_t(i), SHOVES[i][3], SHOVES[i][0]) for i in range(4)]
T_HUGBACK = (T_HUG + 1.4, T_HUG + 4.0)            # the minotaur's slow, hesitant hug back
T_WALK_IN = (T_STOP + 0.6, T_HUG + 0.12)          # the orc's steps into the hug

# shot boundaries
T_INS = IMPACTS[1][0] + 0.55                      # the insert: one crystal, the fight inside it
T_CIRCLE = IMPACTS[2][0]                          # cut on the impact of the orc's 2nd shove
T_REACT = T_SIL - 0.08                            # cutaway: the watchers' faces as the silence falls ...
T_REACT1 = T_LOW0 - 0.04                          # ... back to the pair as the crystals start coming down
T_PIXIE = min(T_LOW1, L1.start - 0.4)             # the pixie, just before "Ew."
T_DRAGON = L2.start - 0.65                        # the dragon, a breath before his line
T_EMPTY = T_ALONE                                 # the emptied square
T_GENTLE = _word("s5_l3", 3, L3.start + 0.94)     # "gentle,"
T_EVERY = _word("s5_l3", 5, L3.start + 1.68)      # "everybody"
T_SIGH = T_ALONE + 0.75                           # in the emptied square: he sighs, watching them
E_SKIP = 8.0                                      # the cut to shot 6 skips this much of the dispersal
SHOT6_KEEP = (1, 2, 3)                            # ... by then only these few are still in the square, far
                                                  # off: on the cobbles (in front of the stalls and the house
                                                  # fronts) and clear of the dragon (checked over the shot)

# ----------------------------------------------------------------------------------------
# the world: one perspective model (see the docstring)
# ----------------------------------------------------------------------------------------

Y_H, H_CAM, F_LEN, CX0 = 470.0, 560.0, 1000.0, 960.0


def gp(X, D):
    """Ground point (X, D) -> (screen x, screen y, scale) at the master camera."""
    s = F_LEN / D
    return CX0 + X * s, Y_H + H_CAM * s, s


def p3(X, Y, D):
    """A 3D point (X lateral, Y up, D depth) -> screen (x, y) at the master camera."""
    s = F_LEN / D
    return CX0 + X * s, Y_H + (H_CAM - Y) * s


def circle3(X, D, r, Y=0.0):
    """A horizontal circle of radius r at height Y around ground point (X, D) -> its screen
    ellipse (cx, cy, rx, ry)."""
    s = F_LEN / D
    return CX0 + X * s, Y_H + (H_CAM - Y) * s, r * s, r * s * (H_CAM - Y) / D


def view_yaw(yaw_world, X, D):
    """Body yaw as seen by the camera (a creature off-axis is seen a little from its side)."""
    return yaw_world + math.atan2(X, D)


def yaw_toward(dX, dD):
    """World yaw of a creature facing along ground direction (dX, dD): 0 = facing the camera,
    +pi/2 = facing screen-right, pi = facing away."""
    return math.atan2(dX, -dD)


X0, D0 = 70.0, 1724.0                             # the centre of the ring
RING_R, RING_RD = 520.0, 470.0
PAIR_DX = -15.0                                   # draw offsets are relative to the fight centre
PAIR_X = X0 + PAIR_DX
PCX, PGY, PSC = gp(PAIR_X, D0)                    # pair anchor (screen) and scale at the master

LS = ch.LIGHTS["square"]
CYAN = "#5fe0ff"
# the end's light: a pale rose-gold from a break in the cloud -- only "a little warmer" (SPEC
# 0.3: the first warm light that comes from HIM is his laugh in S6; this one falls on them)
WARM = "#ffc9a4"
WARM_POOL = "#f0a888"
WARM_SHAFT = "#ffdcc0"

# ----------------------------------------------------------------------------------------
# the fight -> the hug (a local, escalating take on characters.draw_brawl)
# ----------------------------------------------------------------------------------------

GAP = 262.0                                       # anchors apart while they square up (body px)
ORC_BASE, MINO_BASE = -GAP * 0.45, GAP * 0.55
HUG_DIST = 110.0
YAW_FIGHT = 1.2                                   # nearly side-on: chests and palms read across the gap
# the hug is staged so BOTH faces read, stacked: the orc opens toward the lens as he walks in
# (his cheek on the minotaur's chest, face to us), the minotaur turns a little toward us as he
# gives in (his face over the orc's crown, his jaw resting on it). His near arm goes round the
# orc's back LOW (it never crosses the orc's face), the far arm over the orc's shoulders.
YAW_HUG_O = 0.8
YAW_STUN_M = 1.08
YAW_HUG_M = 0.95
_BUILD = {"orc": ORC.ORC_BUILD, "mino": MN.MINOTAUR_BUILD}
ORC_SHOVE_Y = 130.0                               # the orc's palms: this far above his pelvis -- into the
                                                  # taller minotaur's lower chest, BELOW the orc's own chin
                                                  # (any higher and his near hand crosses his face)
MINO_SHOVE_Y = 62.0                               # the minotaur's: down onto the shorter orc's chest
CHEST_D = {"orc": 46.0, "mino": 56.0}             # chest half-depth (the hug gesture's partner)
PALM_GAP = 10.0                                   # a shoving wrist stops this far short of the partner's
                                                  # torso edge (body units): the flat palm just meets it


@dataclass
class OrcPoseS5(ORC.OrcPose):
    s5_front: tuple = None                        # the shove's partner torso edge (see torso_front)


@dataclass
class MinoPoseS5(MN.MinotaurPose):
    s5_front: tuple = None


# the torso cross-sections (centre, half-width, half-depth) of orc._torso / minotaur._torso,
# shoulders to waist: the silhouette a shove's palms land on
_RINGS = {
    "orc": lambda h, br: (((0.0, -140.0 + 4 * h, 4.0), 78.0 + br, 46.0), ((0.0, -112.0, 9.0), 80.0 + 1.5 * br, 52.0 + br),
                          ((0.0, -76.0, 7.0), 64.0, 48.0), ((0.0, -40.0, 4.0), 53.0, 43.0)),
    "mino": lambda h, br: (((0.0, -166.0 + 5 * h, 3.0), 92.0 + br, 52.0), ((0.0, -132.0, 12.0), 90.0 + 1.5 * br, 60.0 + br),
                           ((0.0, -86.0, 12.0), 80.0, 58.0), ((0.0, -44.0, 6.0), 68.0, 50.0)),
}


def torso_front(who, pose, t, dx, shover):
    """`who`'s torso edge on the side facing the other one (shoulders, chest, belly, waist),
    from his own skeleton (no drawing, ~0.1 ms), as ((y, x), ...) top to bottom in the
    SHOVER's local units; dx = who's anchor minus the shover's (pair px)."""
    b = _BUILD[who]
    q = FK.Q()
    q.b, q.pose, q.t, q.sit = b, pose, t, clamp(pose.sit)
    q.yaw = FK.yaw_of(pose)
    q.proj = B.Proj(q.yaw, pose.elev)
    q.near = -1.0 if math.sin(q.yaw) >= 0 else 1.0
    q.far = -q.near
    S = FK.skeleton(q)
    d = 1.0 if math.sin(q.yaw) >= 0 else -1.0     # +1: he faces screen-right (his front edge is his right)
    fw, fs = b.fit, _BUILD[shover].fit
    out = []
    for c, a, cz in _RINGS[who](S["hunch"], S["br"]):
        x, y, hw = q.proj.ellipse(S["T"](c), a, cz)
        out.append((y * fw / fs, (dx + (x + d * hw) * fw) / fs))
    return tuple(out)


def _front_x(front, y):
    """The partner's torso edge (pose.s5_front, top to bottom) at local height y."""
    if y <= front[0][0]:
        return front[0][1]
    for (y0, x0), (y1, x1) in zip(front, front[1:]):
        if y <= y1:
            return lerp(x0, x1, (y - y0) / max(1e-6, y1 - y0))
    return front[-1][1]


def _stride(who, yaw):
    """Anchor travel (body px) per walk cycle at this yaw (so the planted feet do not slide)."""
    b = _BUILD[who]
    return b.stride * abs(math.sin(yaw)) * b.fit


# ---- hands: a REAL fist ------------------------------------------------------------------
# base.hand's "fist" bends only the middle finger joints; held up by the ear it reads as a flat
# hand with bent fingertips (a salute). The fighters' fists are drawn by _draw_fist instead: the
# fingers fold at the knuckles AND the middle joints (a compact block, the thumb wrapped across
# it), and the same drawing uncurls continuously to an open hand (the stop: the fist OPENS).
# A hand pose dict carrying "s5_fist" (the open amount) is routed to it by a hook on base.hand
# that is installed only while this scene draws its two fighters (_FistHook).

def fist_pose(open_u=0.0):
    return {"s5_fist": clamp(open_u), "curl": (1.0, 1.0, 1.0), "spread": 0.0, "thumb": (-0.1, 0.7)}


FIST0 = fist_pose(0.0)


def _draw_fist(cr, x, y, angle, size, open_u, mat, light, lw=B.LINE, *, flip=False, claw=None, claw_len=0.085,
               pad=None, show_palm=False, hold=None, stamp=None, fingers=3, finger_len=1.0, finger_w=1.0,
               thumb=True, palm_w=1.0, curl_add=0.0, back_detail=None, knuckles=True, detail=2, hold_behind=False):
    """base.hand's frame and house style (one union, dilated outline, base.shade), as a side
    view: wrist at the origin, +x toward the knuckles, +y the palm side. open_u 0 = a fist,
    1 = an open hand (fingers straight, spread, the thumb out)."""
    o = core.smooth(clamp(open_u))
    pal = B.palette(light, mat if isinstance(mat, B.Mat) else B.Mat.of(mat))
    s = size
    fy = -1.0 if flip else 1.0
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(s, s * fy)
    lwu = lw / s
    kx = 0.42
    pw = 0.15 * palm_w
    palm_pts = [(-0.03, -pw * 0.80), (kx * 0.5, -pw * 1.0), (kx, -pw * 0.92), (kx + 0.035, -pw * 0.2),
                (kx + 0.03, pw * 0.45), (kx - 0.01, pw * 1.0), (kx * 0.5, pw * 1.02), (-0.03, pw * 0.82),
                (-0.06, 0.0)]
    fl = 0.56 * finger_len
    fw = 0.062 * finger_w
    lens = (0.95, 1.0, 0.86)
    spread = 0.24 * o
    fold1 = (1.0 - o) * 1.55                      # the knuckles
    fold2 = (1.0 - o) * 1.85                      # the middle joints
    geo = []
    for i in range(3):
        u = i - 1.0
        b0 = (kx - 0.03, u * pw * lerp(0.30, 0.66, o) - 0.005)
        L = fl * lens[i]
        a0 = u * spread + fold1
        a1 = a0 + fold2
        j1 = (b0[0] + math.cos(a0) * L * 0.52, b0[1] + math.sin(a0) * L * 0.52)
        j2 = (j1[0] + math.cos(a1) * L * 0.48, j1[1] + math.sin(a1) * L * 0.48)
        geo.append((b0, j1, j2, fw * (1.05 - 0.08 * abs(u)), a0, a1))
    tb = (0.11, -pw * 0.78)
    ta0 = lerp(0.72, -1.05, o)
    tj1 = (tb[0] + math.cos(ta0) * 0.21, tb[1] + math.sin(ta0) * 0.21)
    ta1 = ta0 + lerp(0.55, 0.0, o) * 1.5 + 0.2
    tj2 = (tj1[0] + math.cos(ta1) * 0.15, tj1[1] + math.sin(ta1) * 0.15)
    tr = fw * 1.12

    def add_fingers(d=0.0):
        for (b0, j1, j2, r0, _a0, _a1) in geo:
            core.capsule(cr, b0[0], b0[1], r0 + d, j1[0], j1[1], r0 * 0.95 + d)
            core.capsule(cr, j1[0], j1[1], r0 * 0.95 + d, j2[0], j2[1], r0 * 0.82 + d)

    def add_thumb(d=0.0):
        core.capsule(cr, tb[0], tb[1], tr + d, tj1[0], tj1[1], tr * 0.9 + d)
        core.capsule(cr, tj1[0], tj1[1], tr * 0.9 + d, tj2[0], tj2[1], tr * 0.75 + d)

    thumb_over = o < 0.5                          # wrapped across the fist: its own outline on top
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(palm_pts, lwu))
    add_fingers(lwu)
    if not thumb_over:
        add_thumb(lwu)
    core.src(cr, pal.line)
    cr.fill()
    core.smooth_closed(cr, palm_pts)
    add_fingers()
    if not thumb_over:
        add_thumb()
    B.shade(cr, B.Path(cr), mat, light, lwu, rim=0.0, size=0.3, outline=False)
    ink = []
    if detail >= 1:
        if o < 0.6:                               # the knuckle ridge and the folded fingers' seams
            k = 1.0 - o / 0.6
            ink.append([(kx - 0.05, -pw * 0.75), (kx + 0.05, -pw * 0.1), (kx + 0.06, pw * 0.55)])
            for i in range(2):
                (_b, j1a, j2a, _r, _a, _a1), (_b2, j1b, j2b, _r2, _a2, _a3) = geo[i], geo[i + 1]
                m1 = ((j1a[0] + j1b[0]) / 2, (j1a[1] + j1b[1]) / 2)
                m2 = ((j2a[0] + j2b[0]) / 2, (j2a[1] + j2b[1]) / 2)
                ink.append([(m1[0] + 0.03, m1[1] - 0.03), m1, (lerp(m1[0], m2[0], 0.6), lerp(m1[1], m2[1], 0.6))])
            B.detail_lines(cr, ink, lwu * 0.9, pal.line, 0.75 * k + 0.2)
        else:
            for i in range(2):
                (b0, j1a, _j2a, _r, a1a, _), (b1, j1b, _j2b, _r1, a1b, _) = geo[i], geo[i + 1]
                m0 = ((b0[0] + b1[0]) / 2 - 0.05, (b0[1] + b1[1]) / 2)
                m1 = ((j1a[0] + j1b[0]) / 2, (j1a[1] + j1b[1]) / 2)
                ink.append([m0, m1])
            B.detail_lines(cr, ink, lwu * 0.8, pal.line, 0.6)
    if thumb_over:
        cr.new_path()
        add_thumb(lwu)
        core.src(cr, pal.line)
        cr.fill()
        add_thumb()
        B.shade(cr, B.Path(cr), mat, light, lwu, rim=0.0, size=0.2, outline=False)
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def tocaller(px, py):
        dx, dy = m.transform_point(px, py)
        return inv.transform_point(dx, dy)

    gx, gy = tocaller(kx + 0.08, 0.06)
    return B.HandFrame(gx, gy, angle, s, [tocaller(*g[2]) for g in geo], tocaller(kx * 0.5, 0.0), flip)


_BASE_HAND = B.hand


def _hand_hook(cr, x, y, angle, size, pose, mat, light, lw=B.LINE, **kw):
    if isinstance(pose, dict) and "s5_fist" in pose:
        return _draw_fist(cr, x, y, angle, size, pose["s5_fist"], mat, light, lw, **kw)
    return _BASE_HAND(cr, x, y, angle, size, pose, mat, light, lw, **kw)


class _FistHook:
    """Route fist_pose() hands to _draw_fist while the fighters draw (and only then)."""

    def __enter__(self):
        B.hand = _hand_hook

    def __exit__(self, *exc):
        B.hand = _BASE_HAND
        return False


# ---- arms: blends that keep the elbow continuous ---------------------------------------
# solve_arm's own amt/prev blend lerps the IK pole; when that pole sweeps through the
# shoulder->wrist line the elbow flips sides in one frame (the reviewed pops at 9.37 and 11.3).
# mix() blends two arms with the ELBOW's bend direction interpolated instead (each end's
# solved elbow, slerped), and arm_track() chains timed moves (a move that starts before the
# last one ends blends from it, still moving: overlapping action, never a jump).

@dataclass
class MixArm(ch.Arm):
    a0: object = None
    a1: object = None
    u: float = 0.0
    arc: float = 1.0


def mix(a0, a1, u, arc=1.0):
    """Arm a0 -> a1 at u (already eased; may overshoot a little, e.g. inout_back)."""
    if u <= 0.0 and u > -1e-9:
        return a0
    if u >= 1.0 and u < 1.0 + 1e-9:
        return a1
    return MixArm("s5_mix", hold=a1.hold if u >= 0.5 else a0.hold, a0=a0, a1=a1, u=u, arc=arc)


def arm_track(t, keys):
    """keys = [(t0, dur, Arm[, ease[, arc]]), ...] by start time; the first is the starting arm.
    Each move blends from whatever the arm is doing at that moment."""
    state = keys[0][2]
    for k in keys[1:]:
        t0, dur, arm = k[0], k[1], k[2]
        if t <= t0:
            break
        raw = clamp((t - t0) / max(dur, 1e-6))
        u = core.ease(k[3] if len(k) > 3 else "inout_sine", raw)
        # done only when the TIME is up (an easing may overshoot past 1 and settle back)
        state = arm if raw >= 1.0 else mix(state, arm, u, arc=k[4] if len(k) > 4 else 1.0)
    return state


def drop_ease(u):
    """Arms falling under their own weight: they accelerate (in_quad) for most of the drop and
    are caught at the bottom over the last ~40% (a cubic with zero end slope): heavy, but the
    velocity stays continuous -- never a dead stop. (An overshoot past the hang would ask the
    IK for more than a straight arm.)"""
    u = clamp(u)
    a, c = 0.6, 0.65
    if u <= a:
        return c * (u / a) ** 2
    s = (u - a) / (1.0 - a)
    m0 = 2.0 * c / a * (1.0 - a)
    h00, h10, h01 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2
    return h00 * c + h10 * m0 + h01


def _tab(q):
    return ORC.ORC_GESTURES if q.b is ORC.ORC_BUILD else MN.MINOTAUR_GESTURES


def _arm_g(q, sk, side, arm):
    """An arm's gesture G with its own overrides and solve_arm's walk swing applied (so a blend
    that ends on a plain arm ends exactly where solve_arm puts it)."""
    tab = _tab(q)
    if isinstance(arm, MixArm):
        return _g_mix(q, sk, side, arm)
    if arm.amt < 1.0:
        return _g_mix(q, sk, side, MixArm("s5_mix", a0=ch.Arm(arm.prev), a1=replace(arm, amt=1.0),
                                          u=core.inout_sine(clamp(arm.amt))))
    g = tab.get(arm.gesture, tab["rest"])(q, sk, side, arm)
    tgt = arm.target if arm.target is not None else g.target
    if arm.gesture in ("rest", "slump") and q.sit < 0.6:
        S = q.S
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"]
        tgt = B.v_add(tgt, (0.0, -abs(sw) * 0.03 * FK._AL(q), sw * 0.17 * FK._AL(q) + 1.5 * math.sin(q.t * 0.9 + side)))
    return g._replace(target=tgt, hand=arm.hand or g.hand, pole=g.pole or (side * 0.9, 0.8, -0.3))


def _bend(q, sk, g):
    """Unit direction from the shoulder->wrist line to the elbow of g's IK solution."""
    b = q.b
    e, w = B.ik3(sk, g.target, b.upper_arm, b.forearm, g.pole)
    d = B.v_sub(w, sk)
    L = B.v_len(d)
    if L < 1e-6:
        return B.v_norm(g.pole)
    u = B.v_mul(d, 1.0 / L)
    v = B.v_sub(e, sk)
    p = B.v_sub(v, B.v_mul(u, B.v_dot(v, u)))
    n = B.v_len(p)
    return B.v_mul(p, 1.0 / n) if n > 1e-6 else B.v_norm(g.pole)


def _swivel_frame(sk, tgt, side):
    """An orthonormal frame round the shoulder->wrist axis. Its reference points 'back and
    across the body' -- where no arm in this scene ever points -- so it is never degenerate."""
    a = B.v_norm(B.v_sub(tgt, sk))
    r = (-side * 0.6, 0.0, -0.8)
    e1 = B.v_sub(r, B.v_mul(a, B.v_dot(a, r)))
    L = B.v_len(e1)
    if L < 1e-4:
        r = (0.0, 1.0, 0.0)
        e1 = B.v_sub(r, B.v_mul(a, B.v_dot(a, r)))
        L = B.v_len(e1)
    e1 = B.v_mul(e1, 1.0 / L)
    return a, e1, B.v_cross(a, e1)


def _phi(sk, tgt, side, n):
    """The elbow's swivel angle round the shoulder->wrist axis (for a bend direction n)."""
    _a, e1, e2 = _swivel_frame(sk, tgt, side)
    return math.atan2(B.v_dot(n, e2), B.v_dot(n, e1))


def _swivel(sk, tgt, side, phi):
    """The bend direction at swivel angle phi (always perpendicular to the arm: a safe pole)."""
    _a, e1, e2 = _swivel_frame(sk, tgt, side)
    return B.v_add(B.v_mul(e1, math.cos(phi)), B.v_mul(e2, math.sin(phi)))


def _lerp_phi(p0, p1, u):
    return p0 + core.wrap_angle(p1 - p0) * u


def _g_mix(q, sk, side, arm):
    g0 = _arm_g(q, sk, side, arm.a0)
    g1 = _arm_g(q, sk, side, arm.a1)
    u = arm.u
    AL = FK._AL(q)
    arc = math.sin(math.pi * clamp(u)) * 0.07 * AL * arm.arc        # hands travel on an arc
    tgt = B.v_add(B.v_lerp(g0.target, g1.target, u), (side * arc * 0.5, -arc * 0.4, arc))
    # the elbow swivels round the arm from one end's angle to the other's: continuous, and the
    # pole is always perpendicular to the arm, so the IK can never flip it
    p0 = _phi(sk, g0.target, side, _bend(q, sk, g0))
    p1 = _phi(sk, g1.target, side, _bend(q, sk, g1))
    pole = _swivel(sk, tgt, side, _lerp_phi(p0, p1, u))
    hang = lerp(g0.hang, g1.hang, u)
    hand, thumb = (g0.hand, g0.thumb) if u < 0.5 else (g1.hand, g1.thumb)
    layer = g0.layer if (u < 0.5 and g0.layer != "auto") else g1.layer
    return FK.G(tgt, hand, hang, layer, pole, thumb)


# ---- scene-local gestures (new keys in the orc's and the minotaur's tables) --------------

def _g_square(q, sk, side, arm):
    """Squared up for a shoving match: chest out, fists low and a little wide, elbows back --
    the chest stays open (no boxing guard for the palms to land on)."""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.20 * AL, 0.80 * AL, 0.04 * AL)), FIST0, 0.2, "auto",
                (side * 1.0, -0.1, -0.8), "fwd")


SHOVE_UP = {"orc": 0.95, "mino": 0.35}            # the flat hand's fingers: this far above level (rad)
SHOVE_DROP = {"orc": 10.0, "mino": 26.0}          # the far hand lands this much lower (body units)


def _g_shove(q, sk, side, arm):
    """A two-handed chest shove from the squared stance: phase 0..0.35 the hands come up to the
    shover's OWN chest (loaded, elbows back), 0.35..0.55 they shoot out flat into the other's
    chest (height: pose.shove_y above the pelvis), 0.55..1 back down to the stance. The palms
    land ON the other's chest and never pass it: each wrist is clamped ON SCREEN to the
    partner's torso silhouette (pose.s5_front, from his own skeleton, set by draw_pair) --
    the far arm included, which a depth clamp alone lets through (in 3/4 its shoulder
    projects nearer the partner). The flat hands turn so the fingers point forward and UP
    whatever the forearm does: the palm faces the other's chest (never a limp, fingers-down
    hand)."""
    AL = FK._AL(q)
    ph = arm.phase
    who = "orc" if q.b is ORC.ORC_BUILD else "mino"
    near = side == q.near
    d = 1.0 if math.sin(q.yaw) >= 0 else -1.0    # +1 faces screen-right
    sq = _g_square(q, sk, side, arm).target
    sy = getattr(q.pose, "shove_y", None)
    if sy is None:
        sy = ORC_SHOVE_Y if who == "orc" else MINO_SHOVE_Y
    y_t = q.S["pelvis"][1] - sy + (0.0 if near else SHOVE_DROP[who])
    back = (sk[0] - side * 0.05 * AL, max(sk[1] + 0.40 * AL, y_t + 0.10 * AL), sk[2] + 0.16 * AL)
    out = (sk[0] - side * 0.10 * AL, y_t, sk[2] + 0.98 * AL)
    front = getattr(q.pose, "s5_front", None)
    if front:
        xs, ys = q.proj.xy(out)
        lim = _front_x(front, ys) - d * PALM_GAP
        if (xs - lim) * d > 0.0 and abs(q.proj.s) > 1e-3:
            out = (out[0], out[1], out[2] + (lim - xs) / q.proj.s)
    # the elbows: out and back in the stance, straight back with the hands at the chest, down
    # and out on the thrust -- swivelled round the arm (no pole sweep, no flip)
    b = q.b
    sqp = (side * 1.0, -0.1, -0.8)
    e_sq, w_sq = B.ik3(sk, sq, b.upper_arm, b.forearm, sqp)
    n_sq = B.v_norm(B.v_sub(B.v_sub(e_sq, sk), B.v_mul(B.v_norm(B.v_sub(w_sq, sk)),
                                                        B.v_dot(B.v_sub(e_sq, sk), B.v_norm(B.v_sub(w_sq, sk))))))
    f_sq = _phi(sk, sq, side, n_sq)
    f_back = _phi(sk, back, side, B.v_norm((side * 0.45, 0.8, -0.8)))
    f_out = _phi(sk, out, side, B.v_norm((side * 0.55, 1.0, -0.15)))
    if ph < 0.35:
        e = core.inout_sine(ph / 0.35)
        p, f = B.v_lerp(sq, back, e), _lerp_phi(f_sq, f_back, e)
    elif ph < 0.55:
        e = core.out_cubic((ph - 0.35) / 0.2)
        p, f = B.v_lerp(back, out, e), _lerp_phi(f_back, f_out, e)
    else:
        e = core.inout_sine((ph - 0.55) / 0.45)
        p, f = B.v_lerp(out, sq, e), _lerp_phi(f_out, f_sq, e)
    # the fists stay bunched through the load and burst open as they shoot out (continuously:
    # no pose pop), flat on his chest through the thrust, closing again on the way back down
    k = core.inout_sine(clamp((ph - 0.22) / 0.17)) * (1.0 - core.inout_sine(clamp((ph - 0.62) / 0.3)))
    pole = _swivel(sk, p, side, f)
    # the hand's screen angle: _folk.hand draws it at (forearm angle + hang * sgn), so solve the
    # arm here and pick the hang that points the fingers forward-and-up (the palm on his chest).
    # While loading the open hands simply follow the forearms (two hands pressed together with
    # the fingers up at his own chest would read as praying); they turn up for the thrust.
    el, wr = B.ik3(sk, p, b.upper_arm, b.forearm, pole)
    (ex, ey), (wx, wy) = q.proj.xy(el), q.proj.xy(wr)
    ang = math.atan2(wy - ey, wx - ex)
    up = SHOVE_UP[who]
    want = math.atan2(-math.sin(up), d * math.cos(up))
    sgn = (1.0 if side < 0 else -1.0) * d
    turn_up = core.inout_sine(clamp((ph - 0.33) / 0.14)) * (1.0 - core.inout_sine(clamp((ph - 0.62) / 0.22)))
    hang = core.wrap_angle(want - ang) * sgn * turn_up
    return FK.G(p, fist_pose(k), lerp(0.2, hang, k), "auto", pole, "in" if k > 0.5 else "fwd")


def _g_flinch(q, sk, side, arm):
    """The minotaur flinching from the punch: forearms up in front of his own face and throat,
    palms out, elbows down and tucked -- shielding, not reaching (his hands stay on his side of
    the gap: nothing touches the orc)."""
    AL = FK._AL(q)
    near = side == q.near
    tgt = B.v_add(sk, (-side * (0.30 if near else 0.22) * AL, (-0.04 if near else -0.16) * AL,
                       (0.26 if near else 0.22) * AL))
    return FK.G(tgt, "open", -0.25, "auto", (side * 0.35, 1.0, 0.25), "in")


def _g_what(q, sk, side, arm):
    """'What?': the guard comes down to open hands low in front of him, palms up, elbows down
    at his sides (no fists: he is not squaring up again). From here the hands rise straight
    up into 'whoa' with the elbows staying down (never a chicken wing)."""
    AL = FK._AL(q)
    near = side == q.near
    # low and close to his own belly (he towers over the orc: any higher and the open hands
    # are at the orc's face)
    if near:
        return FK.G(B.v_add(sk, (side * 0.26 * AL, 0.78 * AL, 0.20 * AL)), "open", -0.6, "auto",
                    (side * 0.4, 1.0, -0.3), "in")
    # the far hand is on the orc's side of him: it stays down by his hip, out of the orc's way
    return FK.G(B.v_add(sk, (side * 0.12 * AL, 0.86 * AL, 0.06 * AL)), "open", -0.4, "auto",
                (side * 0.4, 1.0, -0.3), "in")


def _g_whoa(q, sk, side, arm):
    """Hands lifted and open at shoulder height, out to the sides and a little back: 'whoa --
    what are you doing?' Seen 3/4, his far hand is on the partner's side; the near one goes out
    and BACK (a near hand 'out to the side' would come straight at the lens and over the faces).
    Elbows down (the poles are well clear of the shoulder->wrist lines: no flips)."""
    AL = FK._AL(q)
    if side == q.near:
        return FK.G(B.v_add(sk, (side * 0.30 * AL, -0.04 * AL, -0.30 * AL)), "open", -0.5, "auto",
                    (side * 0.2, 1.0, 0.1), "in")
    # the far hand is on the orc's side (he is walking in there): up and BACK over his own
    # shoulder, out of the orc's way
    return FK.G(B.v_add(sk, (side * 0.22 * AL, -0.24 * AL, -0.16 * AL)), "open", -0.5, "auto",
                (side * 0.3, 1.0, 0.0), "in")


def _g_stun(q, sk, side, arm):
    """Being hugged: arms frozen up and out, hands open -- 'I didn't do anything!' The far
    hand goes up by his head (well above the orc's on his chest), the near one out and back at
    shoulder height (clear of both faces): a clear silhouette with the sound off."""
    AL = FK._AL(q)
    if side == q.near:
        return FK.G(B.v_add(sk, (side * 0.32 * AL, 0.04 * AL, -0.34 * AL)), "open", -0.35, "auto",
                    (side * 0.2, 1.0, 0.15), "in")
    return FK.G(B.v_add(sk, (side * 0.56 * AL, -0.04 * AL, 0.02 * AL)), "open", -0.35, "auto",
                (side * 0.3, 1.0, 0.0), "in")


def _g_cock(q, sk, side, arm):
    """A punch wound up: the fist drawn back past the ear, the elbow back and out at shoulder
    height (a clear silhouette in profile)."""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.14 * AL, -0.26 * AL, -0.46 * AL)), FIST0, 0.35, "auto",
                (side * 0.45, 1.0, -0.35), "fwd")


def _g_aside(q, sk, side, arm):
    """An arm let down on the outside, away from the partner (the minotaur's hesitation:
    his near hand comes down at his side before it dares go round the orc)."""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.30 * AL, 0.80 * AL, -0.32 * AL)), "relaxed", 0.1, "auto",
                (side * 0.9, -0.15, -0.8), "fwd")


for _tbl in (ORC.ORC_GESTURES, MN.MINOTAUR_GESTURES):
    _tbl.setdefault("s5_aside", _g_aside)
    _tbl.setdefault("s5_square", _g_square)
    _tbl.setdefault("s5_shove", _g_shove)
    _tbl.setdefault("s5_whoa", _g_whoa)
    _tbl.setdefault("s5_what", _g_what)
    _tbl.setdefault("s5_stun", _g_stun)
    _tbl.setdefault("s5_cock", _g_cock)
    _tbl.setdefault("s5_flinch", _g_flinch)
    _tbl.setdefault("s5_mix", _g_mix)


def _shove_shape(u):
    """One shove cycle u 0..1 -> (arm phase, the target's recoil, the shover's step, the
    shover's lean). Anticipation: he draws back (leans and shifts back) during the wind-up,
    then steps in with the thrust; the hands land at IMPACT_U and the other reels back."""
    shove = clamp(u / 0.75)
    back = math.sin(math.pi * clamp(u / 0.30)) if u < 0.30 else 0.0
    step = core.out_cubic(clamp((u - 0.25) / 0.17)) * (1.0 - core.inout_sine(clamp((u - 0.6) / 0.4)))
    recoil = core.out_cubic(clamp((u - IMPACT_U) / 0.2)) * (1.0 - core.inout_sine(clamp((u - 0.64) / 0.36)))
    return shove, recoil, step - 0.45 * back, 0.5 * step - 0.3 * back


STEP_IN = {"orc": 46.0, "mino": 14.0}             # the taller minotaur barely steps: long arms


def _fight_state(t):
    """While they fight: positions (body px from the fight centre), who shoves, who staggers."""
    ox, mx = ORC_BASE, MINO_BASE
    st = {"orc_shove": None, "mino_shove": None, "orc_stagger": 0.0, "mino_stagger": 0.0,
          "orc_pow": 1.0, "mino_pow": 1.0, "orc_lean": 0.0, "mino_lean": 0.0, "phase": 0.0, "impact": 0.0,
          "power": 0.0, "orc_thrust": 0.0, "mino_thrust": 0.0, "orc_walk": 0.0, "mino_walk": 0.0}
    st["orc_cock"] = None
    if t >= T_COCK:
        # the punch wind-up: a little dip (anticipation), then the fist goes back and up, the
        # body twists and leans away; it peaks (and freezes) at s5_stop
        u = clamp((t - T_COCK) / (T_STOP - T_COCK))
        st["orc_cock"] = core.inout_back(u) if u < 1.0 else 1.0
        st["orc_lean"] = -0.10 * math.sin(math.pi * clamp(u / 0.35)) * (u < 0.35) - 0.26 * core.inout_sine(clamp((u - 0.2) / 0.8))
        ox -= 14.0 * core.inout_sine(u)
    for k, (who, t0, per, pw) in enumerate(SHOVES):
        if not (t0 <= t < t0 + per):
            continue
        u = (t - t0) / per
        shove, recoil, stepin, lean = _shove_shape(u)
        thrust = core.window(u, 0.33, 0.62, 0.07, 0.14)          # the effort: face set, teeth bared
        # the legs: eased envelopes over the cycle (never read from the speed: the steps and the
        # recoil start with a velocity step, and the legs would snap to mid-stride in a frame) --
        # the shover's feet work through his wind-up, step in and step back; the one shoved
        # stumbles from the impact until he has his footing again
        step_w = core.window(u, 0.0, 1.0, 0.16, 0.26) * clamp(STEP_IN[who] * pw / 40.0)
        stag_w = core.window(u, IMPACT_U - 0.03, 1.0, 0.1, 0.26)
        if who == "orc":
            st["orc_walk"], st["mino_walk"] = step_w, stag_w
        else:
            st["mino_walk"], st["orc_walk"] = step_w, stag_w
        if who == "orc":
            ox += STEP_IN["orc"] * pw * stepin
            mx += 60.0 * pw * recoil
            st["orc_shove"], st["orc_pow"], st["orc_lean"], st["orc_thrust"] = shove, pw, lean, thrust
            st["mino_stagger"] = max(st["mino_stagger"], recoil)
            st["mino_pow"] = pw
        else:
            mx -= STEP_IN["mino"] * pw * stepin
            ox -= 60.0 * pw * recoil
            st["mino_shove"], st["mino_pow"], st["mino_thrust"] = shove, pw, thrust
            # the taller one stays upright and shoves from the shoulders, chin up: his head
            # never drops onto the orc's crown
            st["mino_lean"] = min(0.09, lean * (0.8 + 0.2 * pw))
            st["orc_stagger"] = max(st["orc_stagger"], recoil)
            st["orc_pow"] = pw
        st["phase"] = u
        st["impact"] = max(st["impact"], clamp(1.0 - abs(u - IMPACT_U) / 0.08))
        st["power"] = pw
    st["orc_x"], st["mino_x"] = ox, mx
    return st


_STOP_STATE = _fight_state(T_STOP - 1e-4)
ORC_STOP_X = _STOP_STATE["orc_x"]
MINO_HUG_X = MINO_BASE                            # he stays put (a lean, not a step: no leg pops)
ORC_HUG_X = MINO_HUG_X - HUG_DIST
T_BRACE = T_COCK + 0.12                           # the minotaur sees the punch coming: he flinches
YAW_WALK = 0.5 * (YAW_FIGHT + YAW_HUG_O)
# the walk-in is two steps; its phase is offset so the last step ENDS in the passing position
# (feet together, the lifted foot coming down as the walk fades): no leg pop at the hug
_WALK_STRIDE = _stride("orc", YAW_WALK)
_WALK_PH0 = 0.25 - ((ORC_HUG_X - ORC_STOP_X) / _WALK_STRIDE) % 0.5


def _xs(t):
    """(orc x, minotaur x): anchor offsets from the fight centre (body px) at time t."""
    if t < T_STOP:
        st = _fight_state(t)
        return st["orc_x"], st["mino_x"]
    walk_u = core.inout_sine(clamp((t - T_WALK_IN[0]) / (T_WALK_IN[1] - T_WALK_IN[0])))
    return lerp(ORC_STOP_X, ORC_HUG_X, walk_u), MINO_HUG_X


def _impact_pulse_for(t, who, tau=0.3):
    """0..1 pulse after an impact that lands ON `who` (the face flash, the head whip)."""
    v = 0.0
    for ti, pw, shover in IMPACTS:
        if shover != who and t >= ti:
            dt = t - ti
            v = max(v, min(1.0, pw) * clamp(dt / 0.05) * math.exp(-dt / tau))
    return v


def pair_state(t):
    ox, mx = _xs(t)
    if t < T_STOP:
        st = _fight_state(t)
        st.update(fight=True, stop=0.0, hug=0.0, hug_back=0.0)
        oyaw, myaw = YAW_FIGHT, YAW_FIGHT
        # (orc_walk / mino_walk: eased per-cycle envelopes from _fight_state)
        st["orc_phase"] = (ox - ORC_BASE) / _stride("orc", oyaw)
        st["mino_phase"] = -(mx - MINO_BASE) / _stride("mino", myaw)
    else:
        st = {"fight": False, "orc_shove": None, "mino_shove": None, "orc_stagger": 0.0, "mino_stagger": 0.0,
              "impact": 0.0, "phase": 0.0, "power": 0.0}
        st["stop"] = core.inout_sine(clamp((t - T_STOP) / 0.5))
        walk_u = core.inout_sine(clamp((t - T_WALK_IN[0]) / (T_WALK_IN[1] - T_WALK_IN[0])))
        st["walk_u"] = walk_u
        st["hug"] = core.inout_sine(clamp((t - (T_HUG - 0.3)) / 0.45))
        st["hug_close"] = core.inout_sine(clamp((t - T_HUG) / 0.7))
        st["hb_close"] = core.inout_sine(clamp((t - (T_HUGBACK[0] + 0.85)) / 1.1))
        open_u = core.inout_sine(clamp((t - T_WALK_IN[0]) / (T_HUG + 0.55 - T_WALK_IN[0])))
        oyaw = lerp(YAW_FIGHT, YAW_HUG_O, open_u)
        myaw = lerp(lerp(YAW_FIGHT, YAW_STUN_M, core.inout_sine(clamp((t - T_HUG) / 0.6))), YAW_HUG_M,
                    st["hb_close"])
        # two steps in: the walk weight eases in and out with the move (never from a velocity
        # clamp), the phase follows the distance; the minotaur does not step at all
        st["orc_walk"] = core.window(t, T_WALK_IN[0] - 0.04, T_WALK_IN[1] + 0.06, 0.16, 0.24)
        st["mino_walk"] = 0.0
        st["orc_phase"] = _WALK_PH0 + (ox - ORC_STOP_X) / _WALK_STRIDE
        st["mino_phase"] = 0.0
    st["orc_x"], st["mino_x"] = ox, mx
    st["orc_yaw"], st["mino_yaw"] = oyaw, myaw
    return st


def _expr(*pairs):
    """Blend moods: _expr(("angry", 1), ("sad", u), ...) -> an Expr (sequential blends)."""
    e = B.expr(pairs[0][0])
    for m, u in pairs[1:]:
        if u > 0:
            e = e.blend(B.expr(m), clamp(u))
    return e


# fury reads at 3/4: brows driven hard down and in, the eyes OPEN in a glare (the orc's eyes
# already sit under a heavy lid, +0.2, the minotaur's +0.06: a high upper lid here, a tight
# lower one, the angry slant), the mouth corners down; each thrust opens a yell (jaw dropped,
# the tusks bared), each hit lands as a pained wince (brows up, eyes squeezed, a grimace)
FURY_O = B.expr("angry").with_(brow_in=-1.45, brow_out=0.45, brow_y=-0.42, lid=0.02, lid_bot=0.32, lid_tilt=-0.9,
                               smile=-0.75, pupil=0.85)
FURY_M = B.expr("angry").with_(brow_in=-1.35, brow_out=0.4, brow_y=-0.38, lid=0.1, lid_bot=0.3, lid_tilt=-0.85,
                               smile=-0.7, pupil=0.85)
FURY = FURY_O
WINCE = B.Expr(brow_in=1.0, brow_out=-0.2, brow_y=0.2, lid=0.72, lid_bot=0.5, lid_tilt=0.35, smile=-0.6, open=0.2)
FLINCH = B.Expr(brow_in=1.0, brow_out=-0.15, brow_y=0.3, lid=0.9, lid_bot=0.6, lid_tilt=0.3, smile=-0.7, open=0.1)


def _fight_face(thrust, hit, snarl_open=0.0, fury=FURY_O):
    e = fury
    if thrust > 0.0:
        # the effort: the jaw drops on a grunt-yell, the brows crush down, the eyes narrow
        e = e.with_(open=0.5 * thrust, brow_in=e.brow_in - 0.3 * thrust, lid=e.lid + 0.1 * thrust)
    if snarl_open > e.open:
        e = e.with_(open=snarl_open)
    if hit > 0.0:
        e = e.blend(WINCE, clamp(1.3 * hit))
    return e


def orc_pose(t, st, sgn=1.0):
    walk, phase = st["orc_walk"], st["orc_phase"]
    reach = (st["mino_x"] - st["orc_x"]) / math.sin(abs(st["orc_yaw"]))
    SQ = ch.Arm("s5_square")
    if st["fight"]:
        hit = _impact_pulse_for(t, "orc")
        whip = _impact_pulse_for(t, "orc", 0.16)
        cock = st.get("orc_cock")
        if cock is not None:
            near, far = mix(SQ, ch.Arm("s5_cock"), cock, arc=0.6), SQ
            lean = st["orc_lean"]
        elif st["orc_shove"] is not None:
            near = far = ch.Arm("s5_shove", phase=st["orc_shove"])
            lean = st["orc_lean"] * (0.8 + 0.2 * st["orc_pow"])
        elif st["orc_stagger"] > 0.02:
            near = far = mix(SQ, ch.Arm("stagger", phase=st["phase"]), core.inout_sine(clamp(st["orc_stagger"] * 2.0)))
            lean = -0.5 * st["orc_stagger"] * min(1.5, st["orc_pow"])
        else:
            near = far = SQ
            lean = 0.0
        ck = clamp(cock or 0.0)
        thrust = st["orc_thrust"]
        e = _fight_face(thrust, hit, 0.3 * ck)
        return OrcPoseS5(yaw=sgn * st["orc_yaw"], mood=e, snarl=0.6 + 0.4 * max(thrust, ck) - 0.4 * hit,
                           stance=0.5 * sgn, hunch=0.62, lean=lean,
                           head_nod=0.5 * whip + 0.07 - 0.05 * thrust + 0.06 * ck,
                           look=(0.38 * sgn, -0.2), walk=walk, phase=phase, near=near, far=far, seed=3,
                           hug_reach=reach, hug_d=CHEST_D["mino"])
    ts = t - T_STOP
    frozen = _STOP_STATE
    # frozen at the top of the wind-up (a jolt, then held, the fist trembling) -- he sees the
    # minotaur flinching, eyes shut; the brows jump (what am I doing?); the fist OPENS (over
    # five frames, the open palm held a beat); then the arms FALL, heavy, the head sinks, and
    # the eyes come up to the minotaur's face
    jolt = 0.05 * math.sin(ts * TAU * 4.5) * math.exp(-ts * 9.0)
    lean0 = frozen["orc_lean"] + jolt
    open_u = core.inout_sine(clamp((ts - T_OPEN0) / 0.21))
    COCK = ch.Arm("s5_cock", hand=fist_pose(open_u))
    hug_arm = ch.Arm("hug", phase=1.0 - st["hug_close"])
    near = arm_track(t, [(T_STOP - 1.0, 0.0, COCK), (T_DROP, 0.36, ch.Arm("slump"), drop_ease, 0.4),
                         (T_HUG - 0.3, 0.45, hug_arm)])
    far = arm_track(t, [(T_STOP - 1.0, 0.0, SQ), (T_DROP, 0.36, ch.Arm("slump"), drop_ease, 0.4),
                        (T_HUG - 0.3, 0.45, hug_arm)])
    hug = st["hug"]
    realise = core.window(ts, 0.06, 0.7, 0.08, 0.3)                # brows jump: "what am I doing?"
    sad = core.inout_sine(clamp((ts - 0.40) / 0.4))
    tender = st["hug_close"]
    # once he holds on: his cheek on the minotaur's chest, his face turned to us, eyes sinking
    # shut (a sliver stays open: a closed green lid would not read at this size), a small smile
    rest = core.inout_sine(clamp((t - (T_HUG + 0.25)) / 0.9))
    fury = FURY_O.with_(open=0.3 * (1.0 - core.inout_sine(clamp((ts - 0.08) / 0.3))))
    e = fury.blend(B.expr("raised"), clamp(realise))
    for m, u in (("sad", sad), ("kind", tender), ("warm", 0.45 * rest)):
        if u > 0:
            e = e.blend(B.expr(m), clamp(u))
    look_down = core.inout_sine(clamp((ts - 0.44) / 0.16))
    look_up = core.inout_sine(clamp((ts - 0.62) / 0.14))          # eyes down ... then up at him: go
    look_y = ((0.55 * look_down * (1.0 - look_up) - 0.12 * look_up) * (1.0 - tender) + 0.3 * tender)
    look_x = 0.3 * sgn * (1.0 - core.inout_sine(clamp(ts / 0.4))) * (1.0 - tender)
    nod = (0.13 * (1.0 - core.inout_sine(clamp(ts / 0.3)))
           - 0.32 * look_down * (1.0 - 0.7 * lagged_u(t, ts, 0.62))) * (1.0 - tender) - 0.05 * tender
    tremble = 0.025 * math.sin(t * TAU * 7.3) * core.window(ts, 0.08, T_OPEN0 + 0.1, 0.06, 0.06)   # the held fist quivers
    sag = 0.07 * core.inout_sine(clamp((ts - 0.45) / 0.4)) * (1.0 - st["walk_u"])     # the anger drains out of him
    blink = None
    if tender > 0.3:
        blink = 0.8 * core.inout_sine(clamp((tender - 0.3) / 0.7))
    return OrcPoseS5(yaw=sgn * st["orc_yaw"], mood=e, snarl=0.9 * (1.0 - core.inout_sine(clamp((ts - 0.1) / 0.45))),
                       stance=0.5 * sgn * (1.0 - st["stop"]),
                       hunch=lerp(0.62, 0.9, core.inout_sine(clamp((ts - 0.45) / 0.32))) - 0.02 * hug,
                       lean=lean0 * (1.0 - core.inout_sine(clamp((ts - 0.45) / 0.4))) + tremble - sag
                       + 0.08 * st["walk_u"] * (1 - hug) + 0.35 * hug,
                       head_tilt=0.3 * tender * sgn, head_turn=-0.55 * tender * sgn, head_nod=nod,
                       look=(look_x, look_y), blink=blink,
                       walk=walk, phase=phase, near=near, far=far, seed=3,
                       hug_reach=(st["mino_x"] - st["orc_x"]) / math.sin(abs(st["orc_yaw"])),
                       hug_w=74.0, hug_d=52.0, hug_y=112.0)


def lagged_u(t, ts, t0, dur=0.18):
    """The head following the eyes a beat later (ease from t0 + lag)."""
    return core.inout_sine(clamp((ts - t0 - 0.08) / dur))


T_OPEN0 = 0.16                                    # the fist starts to open (s after s5_stop)


def mino_pose(t, st, sgn=1.0):
    walk, phase = st["mino_walk"], st["mino_phase"]
    reach = (st["mino_x"] - st["orc_x"]) / math.sin(abs(st["mino_yaw"]))
    SQ = ch.Arm("s5_square")
    if st["fight"]:
        hit = _impact_pulse_for(t, "mino")
        whip = _impact_pulse_for(t, "mino", 0.16)
        brace = core.inout_sine(clamp((t - T_BRACE) / 0.22))         # the payback coming: he flinches
        if st["mino_shove"] is not None:
            arm = ch.Arm("s5_shove", phase=st["mino_shove"])
            lean = st["mino_lean"]
        elif st["mino_stagger"] > 0.02:
            arm = mix(SQ, ch.Arm("stagger", phase=st["phase"]), core.inout_sine(clamp(st["mino_stagger"] * 2.0)))
            lean = -0.5 * st["mino_stagger"] * min(1.5, st["mino_pow"])
        else:
            arm = mix(SQ, ch.Arm("s5_flinch"), brace, arc=0.5)
            lean = -0.2 * brace
        thrust = st["mino_thrust"]
        e = _fight_face(thrust, hit, fury=FURY_M)
        if brace > 0.0:
            e = e.blend(FLINCH, brace)
        # the punch coming: he flinches -- eyes squeezed shut, face turned away, shoulders up
        return MinoPoseS5(yaw=-sgn * st["mino_yaw"], mood=e, stance=0.5 * -sgn,
                               hunch=0.55 - 0.2 * thrust + 0.25 * brace,
                               lean=lean, head_nod=0.5 * whip + 0.24 * thrust - 0.02 - 0.2 * brace,
                               look=(-0.38 * sgn, 0.24), head_turn=0.45 * brace * sgn,
                               blink=0.92 * brace if brace > 0.02 else None,
                               walk=walk, phase=phase, near=arm, far=arm, seed=5, shove_y=MINO_SHOVE_Y,
                               hug_reach=reach, hug_d=CHEST_D["orc"],
                               tail_swing=0.6 * math.sin(t * 2.3) + 0.5 * whip)
    ts = t - T_STOP
    # brace -> the guard comes down (what?) -> wary as he walks in (whoa) -> the hug: stunned,
    # arms up and out, head back -> frozen -> eyes dart, then down at him -> hands hover ->
    # they settle on his back, head bows, eyes close
    unbrace = core.inout_sine(clamp((ts - 0.25) / 0.6))
    flinch = 1.0 - core.inout_sine(clamp((ts - 0.3) / 0.5))           # the flinch eases off ...
    peek = core.inout_sine(clamp((ts - 0.2) / 0.16))                 # ... the eyes pop open: no blow?
    whoa = core.inout_sine(clamp((t - (T_WALK_IN[0] - 0.06)) / 0.36))        # hands up and away as he comes
    stun = core.inout_sine(clamp((t - (T_HUG - 0.05)) / 0.32))
    tb = T_HUGBACK[0]
    hover = core.inout_sine(clamp((t - tb) / 0.9))                  # far arm: over his shoulder
    close = core.inout_sine(clamp((t - (tb + 0.85)) / 1.1))
    close_n = core.inout_sine(clamp((t - (tb + 1.15)) / 1.0))
    settle = core.inout_sine(clamp((t - (tb + 1.7)) / 0.9))
    u = (t - T_HUGBACK[1] - 0.6) % 4.2 if t > T_HUGBACK[1] + 0.6 else 9.0
    pat = 0.14 * math.sin(math.pi * u / 0.34) ** 2 if u < 0.68 else 0.0    # slow pats on his back
    common = [(T_STOP - 1.0, 0.0, ch.Arm("s5_flinch")), (T_STOP + 0.22, 0.42, ch.Arm("s5_what")),
              (T_WALK_IN[0] - 0.06, 0.36, ch.Arm("s5_whoa")), (T_HUG - 0.05, 0.32, ch.Arm("s5_stun"))]
    # far arm over the orc's shoulders: it starts from a half-open wrap (a tight arc over his
    # shoulder, not a wide level reach)
    far = arm_track(t, common + [(tb, 1.15, ch.Arm("hug", phase=lerp(0.55, 0.18, close) * (1.0 - settle)), "inout_sine", 0.5)])
    # near arm: down out of the frozen 'I didn't do anything' -- it comes down and in, elbow
    # down, to HOVER by the orc's back without touching (the hesitation), then settles on it
    near = arm_track(t, common + [(tb + 0.12, 0.8, ch.Arm("hug", phase=lerp(0.62, 0.18, close_n) * (1.0 - settle) + pat),
                                   "inout_sine", 0.4)])
    confused = core.window(ts, 0.35, T_WALK_IN[0] - T_STOP + 0.3, 0.3, 0.25)
    # frozen: his eyes dart to the crowd, then come down to the orc
    dart = core.track(t, [(T_HUG + 0.5, 0.0), (T_HUG + 0.68, -0.55, "inout_sine"), (T_HUG + 0.92, -0.55),
                          (T_HUG + 1.1, 0.5, "inout_sine"), (T_HUG + 1.3, 0.5), (T_HUGBACK[0] + 0.05, 0.0, "inout_sine")])
    down = core.inout_sine(clamp((t - (T_HUGBACK[0] - 0.15)) / 0.4))
    tender = close
    e = FURY_M.blend(FLINCH, flinch).blend(B.expr("neutral"), clamp(unbrace * (1.0 - flinch)))
    for m, k in (("skeptical", confused), ("worried", whoa * (1.0 - stun)), ("surprised", stun * (1.0 - 0.7 * down)),
                 ("worried", 0.6 * down * (1.0 - tender)), ("kind", tender)):
        if k > 0:
            e = e.blend(B.expr(m), clamp(k))
    e = e.with_(open=e.open * (1.0 - down))
    blink = None
    if peek < 1.0:
        blink = 0.92 * (1.0 - peek)
    elif close > 0.55:
        blink = clamp((close - 0.55) * 2.5)
    # puzzled, he leans in a hair ("what?") instead of stepping; rocked back a hair by the hug
    curious = core.window(ts, 0.4, T_HUG - T_STOP - 0.1, 0.4, 0.3)
    rocked = 0.05 * math.sin(math.pi * clamp((t - T_HUG - 0.05) / 0.7)) ** 2
    # giving in: his head turns to us and tilts so his jaw comes to rest on the orc's crown (it
    # stays ABOVE the orc's face: no bow), eyes closing
    yaw = -sgn * st["mino_yaw"]
    return MinoPoseS5(yaw=yaw, mood=e,
                           lean=-0.2 * flinch + 0.07 * curious - 0.12 * whoa * (1 - stun) - 0.1 * stun * (1.0 - hover)
                           + 0.05 * close - rocked,
                           hunch=0.55 + 0.25 * flinch - 0.15 * stun * (1.0 - hover) + 0.35 * close,
                           head_nod=-0.2 * flinch + 0.22 * stun * (1.0 - hover) - 0.18 * down * (1.0 - close)
                           - 0.07 * close + 0.06 * whoa,
                           head_tilt=(-0.42 * close + 0.12 * confused) * sgn,
                           head_turn=(0.45 * flinch + 0.85 * close) * sgn,
                           look=(dart * (1.0 - down) - 0.3 * close * sgn, 0.1 + 0.45 * down),
                           near=near, far=far, seed=5, stance=0.5 * -sgn * (1 - st["stop"]),
                           blink=blink,
                           walk=walk, phase=phase,
                           hug_reach=(st["mino_x"] - st["orc_x"]) / math.sin(abs(st["mino_yaw"])),
                           hug_w=66.0, hug_d=46.0, hug_y=20.0, hug_y_far=105.0,
                           tail_swing=lerp(0.6 * math.sin(t * 2.3), 0.25 * math.sin(t * 0.9), st["stop"]))


def pair_poses(t, st):
    """(orc pose, minotaur pose) at t; a shover's pose carries his partner's torso edge
    (s5_front) so the palms land on it (see _g_shove)."""
    op, mp = orc_pose(t, st), mino_pose(t, st)
    if st["fight"]:
        if st["orc_shove"] is not None:
            op = replace(op, s5_front=torso_front("mino", mp, t, st["mino_x"] - st["orc_x"], "orc"))
        if st["mino_shove"] is not None:
            mp = replace(mp, s5_front=torso_front("orc", op, t, st["orc_x"] - st["mino_x"], "mino"))
    return op, mp


def draw_pair(cr, cx, gy, sc, t, light_orc, light_mino=None, detail=None):
    """The orc and the minotaur at anchor (cx, gy) (the fight centre), z-correct (the hug
    interleaves their layers like characters.draw_brawl). Returns (orc_rig, mino_rig)."""
    st = pair_state(t)
    lm = light_mino or light_orc
    op, mp = pair_poses(t, st)
    hug = st.get("hug", 0.0)
    rock = 3.5 * hug * math.sin((t - T_HUG) * TAU * 0.21) if not st["fight"] else 0.0
    ox, mx = cx + (st["orc_x"] + rock) * sc, cx + (st["mino_x"] + rock) * sc
    with _FistHook():
        if st["fight"] or hug <= 0.05:
            # the minotaur, the orc, then the minotaur's near arm: when he shoves, his palms land
            # ON the orc's chest (in front of it), never behind him
            MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("back", "body", "mid", "head"))
            o_rig = ORC.draw_orc(cr, ox, gy + 1.0, sc, op, light_orc, t, detail)
            m_rig = MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("front",))
            return o_rig, m_rig
        # interleaved: both back arms, the minotaur's body, the orc (his face on the minotaur's
        # chest, arms round his waist), then the minotaur's head -- his chin comes to rest on the
        # orc's crown -- and last his near arm across the orc's back
        MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("back",))
        ORC.draw_orc(cr, ox, gy + 1.0, sc, op, light_orc, t, detail, parts=("back",))
        MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("body", "mid"))
        o_rig = ORC.draw_orc(cr, ox, gy + 1.0, sc, op, light_orc, t, detail, parts=("body", "mid", "head", "front"))
        MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("head",))
        m_rig = MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail, parts=("front",))
    return o_rig, m_rig


def crystal_level(t):
    """Average brightness of the raised crystals (drives the cyan light of the ring)."""
    k = sum(lower_amount(m, t) for m in MEMBERS) / len(MEMBERS)
    return 1.0 - 0.78 * k


def impact_pulse(t):
    """Excitement after each shove's impact (0..1+), decaying."""
    v = 0.0
    for ti, pw, _ in IMPACTS:
        if t >= ti:
            v += pw * math.exp(-(t - ti) / 0.55) * min(1.0, (t - ti) / 0.06 + 0.3)
    return v


# ----------------------------------------------------------------------------------------
# the crowd: a ring of 14 creatures + the pixie
# ----------------------------------------------------------------------------------------

class Member:
    def __init__(self, i, theta, kind, seed, rf=1.0, order=0, cheer=0.6, mood_after="worried",
                 leave=(None, 0.0, 1.0, 230.0), hat=None, laugh=False, cloth=None):
        self.i, self.theta, self.kind, self.seed, self.rf = i, math.radians(theta), kind, seed, rf
        self.order, self.cheer, self.mood_after, self.laugh = order, cheer, mood_after, laugh
        self.t_turn, ldx, ldd, kspeed = leave
        n = math.hypot(ldx, ldd) or 1.0
        self.dir = (ldx / n, ldd / n)
        self.spec = ch.random_creature(seed, kind)
        b = CW.BUILDS[kind]
        self.speed = b.stride * b.fit * 1.05 * kspeed * self.spec.size      # ~2 steps a second
        if hat is not None:
            self.spec.hat = hat
        if cloth is not None:
            self.spec.cloth = cloth
        self.X = X0 + RING_R * rf * math.cos(self.theta)
        self.D = D0 + RING_RD * rf * math.sin(self.theta)
        self.yaw0 = yaw_toward(X0 - self.X, D0 - self.D)
        self.yaw1 = yaw_toward(self.dir[0], self.dir[1])
        self.t_walk = self.t_turn + 0.3                # a beat to turn, then away
        r = random.Random(seed * 31 + 7)
        self.ph = r.random() * TAU
        self.bouncy = r.random() < 0.55


# theta: 90 = behind the fight, -90 = in front (backs to us). order = when its crystal comes
# down (0 first). leave = (turn time, walk direction dX, dD, speed units/s). Two bored ones
# drift off during the dragon's first line; the rest turn their backs on "everybody looks away".
_E1 = L2.start - 0.25
_W = L3.start - 0.2
MEMBERS = [
    # back arc: faces lit by their crystals, cheering (a tall elf peeks from a second row)
    Member(0, 22, "harpy", 517, 1.0, 6, 0.8, "sneer", (_W + 0.55, 0.85, 0.5, 1.3)),
    Member(1, 47, "elf", 503, 1.0, 2, 0.35, "skeptical", (_W + 0.3, 0.75, 0.66, 1.25), hat="hood"),
    Member(2, 72, "dwarf", 541, 1.0, 0, 0.9, "worried", (_W + 1.35, 0.45, 0.9, 1.45)),
    Member(3, 101, "goblin", 524, 1.0, 1, 1.0, "sneer", (_W + 0.95, -0.3, 0.95, 1.2), laugh=True),
    Member(4, 127, "elf", 512, 1.0, 4, 0.35, "bored", (_E1, -0.75, 0.66, 1.25), cloth="#5A4A6E"),
    Member(5, 155, "kobold", 533, 1.0, 9, 0.9, "worried", (_W + 1.55, -0.85, 0.5, 1.55)),
    Member(14, 160, "elf", 561, 1.2, 5, 0.3, "skeptical", (_W + 0.45, -0.9, 0.45, 1.25)),
    # the sides
    Member(6, 0, "goblin", 545, 1.0, 7, 0.9, "skeptical", (_E1 + 1.25, 1.0, 0.3, 1.6), hat="cap"),
    Member(7, 180, "dwarf", 529, 1.0, 8, 0.8, "sad", (_W + 1.15, -0.95, 0.3, 1.45)),
    # front arc: backs to us, crystals showing the fight; the middle stays open
    Member(8, -22, "elf", 507, 1.0, 3, 0.3, "skeptical", (_E1 + 0.65, 1.0, 0.2, 1.35)),
    Member(9, -47, "dwarf", 522, 1.0, 10, 0.9, "worried", (_W + 1.95, 1.0, 0.15, 1.5)),
    Member(10, -128, "goblin", 536, 1.0, 11, 1.0, "sneer", (_W + 1.65, -0.9, 0.35, 1.5), laugh=True),
    Member(11, -153, "kobold", 548, 1.06, 12, 1.0, "bored", (_W + 0.75, -0.95, 0.3, 1.55)),
    Member(13, 141, "harpy", 538, 1.24, 13, 0.7, "sneer", (_W + 0.85, -0.8, 0.6, 1.3)),
]
MEMBER_BY_ID = {m.i: m for m in MEMBERS}
N_LOWER = 15                                      # 14 crystals + the pixie's (last)


def lower_window(order):
    span = (T_LOW1 - 0.8) - T_LOW0
    t0 = T_LOW0 + span * order / (N_LOWER - 1)
    return t0, t0 + 0.8


def lower_amount(m, t):
    t0, t1 = lower_window(m.order)
    return core.inout_sine(clamp((t - t0) / (t1 - t0)))


WALK_ACC = 0.4                                    # s to reach walking speed


def member_ground(m, t):
    """Where member m stands at t: (X, D, walking 0..1, distance walked)."""
    if t <= m.t_walk:
        return m.X, m.D, 0.0, 0.0
    tw = t - m.t_walk
    acc = WALK_ACC
    dist = m.speed * (tw * tw / (2 * acc) if tw < acc else (tw - acc * 0.5))
    walk = clamp(tw / 0.35)
    return m.X + m.dir[0] * dist, m.D + m.dir[1] * dist, walk, dist


def _energy_fight(t):
    rise = sum(0.1 * clamp((t - ti) / 0.4) for ti, _, _ in IMPACTS[:3])   # each shove winds them up
    return min(1.0, 0.45 + rise + 0.35 * impact_pulse(t))


_E_STOP = _energy_fight(T_STOP)


def cheer_energy(t):
    if t < T_STOP:
        return _energy_fight(t)
    # confusion after the stop: the cheering dies away (the gasp at the hug, then silence)
    return _E_STOP * (1.0 - core.inout_sine(clamp((t - T_STOP) / 0.9)))


def member_pose(m, t, feed, scroll_feed):
    """The CrowdPose of member m at time t (plus a vertical hop in body px)."""
    X, D, walking, dist = member_ground(m, t)
    spec = m.spec
    low = lower_amount(m, t)
    turn_u = core.inout_sine(clamp((t - m.t_turn) / 0.8))
    yaw_w = core.lerp_angle(m.yaw0, m.yaw1, turn_u) if turn_u > 0 else m.yaw0
    # a little head follow of the fight + idle
    yaw = view_yaw(yaw_w, X, D)
    hop = 0.0
    E = cheer_energy(t)
    if t < T_SIL:
        chatter = 0.55 + 0.45 * math.sin(t * TAU * 3.1 + m.ph) * math.sin(t * TAU * 1.3 + 2 * m.ph)
        talk = clamp(E * m.cheer * (0.5 + 0.5 * chatter) * 1.25)
        gasp = core.window(t, T_HUG + 0.1, T_SIL, 0.12, 0.12)
        talk = max(talk * (1.0 - gasp), 0.35 * gasp) * (1.0 - clamp((t - T_SIL + 0.12) / 0.12))
        cheer_amt = clamp(E * 1.6 * m.cheer) if m.cheer > 0.55 else 0.0
        mood = _expr(("happy", 1.0), ("laugh", 0.6 if m.laugh else 0.0), ("raised", core.window(t, T_STOP + 0.2, T_HUG, 0.3, 0.2)),
                     ("surprised", core.window(t, T_HUG, T_SIL + 0.4, 0.15, 0.3)))
        mood = mood.with_(open=mood.open * (1.0 - core.inout_sine(clamp((t - T_SIL) / 0.3))))
        if m.bouncy:
            hop = 7.0 * impact_pulse(t) * abs(math.sin(t * TAU * 2.2 + m.ph)) * (t < T_STOP)
        pose = ch.crowd_pose("film", t, spec, yaw=yaw, thumb=feed, mood=mood, talk=talk,
                             far=ch.Arm("cheer", amt=cheer_amt, prev="rest", phase=t * 1.7 + m.ph * 0.2))
        if cheer_amt <= 0.0:
            pose = pose.with_(far=ch.Arm("rest"))
        return pose, X, D, hop
    if turn_u <= 0.0:
        # silent: the crystal comes down (one by one), they stare at the hug, uneasy
        mood = _expr(("surprised", 1.0), (m.mood_after, core.inout_sine(clamp((t - T_SIL) / 1.2))))
        mood = mood.with_(open=mood.open * (1.0 - core.inout_sine(clamp((t - T_SIL) / 0.3))))
        if low <= 0.0:
            pose = ch.crowd_pose("film", t, spec, yaw=yaw, thumb=feed, mood=mood, talk=0.0)
        else:
            pose = ch.crowd_pose("lower", t, spec, yaw=yaw, thumb=feed, amount=low, mood=mood, talk=0.0)
            # they keep staring at the pair a while, then glance at each other
            glance = core.window(t, T_LOW1 + 0.6 + 0.4 * (m.i % 4), T_LOW1 + 2.0 + 0.4 * (m.i % 4), 0.4, 0.5)
            side = 1.0 if m.i % 2 else -1.0
            pose = pose.with_(head_nod=-0.18 * low, look=(0.35 * side * glance, 0.15 * low),
                              head_turn=0.35 * side * glance)
        return pose, X, D, 0.0
    # they look away: back to their crystals, glowing again in their faces, and walk off
    revive = core.inout_sine(clamp((t - m.t_turn - 0.2) / 0.8))
    pose = ch.crowd_pose("lower", t, spec, yaw=yaw, thumb=scroll_feed, amount=1.0, glow=1.0 + 3.0 * revive,
                         mood=_expr((m.mood_after, 1.0), ("bored", revive)), talk=0.0)
    if walking > 0.0:
        b = CW.BUILDS[spec.kind]
        pose = pose.with_(walk=walking, phase=(dist / (b.stride * b.fit)) % 1.0)
    pose = pose.with_(head_nod=-0.45, look=(0.0, 0.7))
    return pose, X, D, 0.0


# the pixie: hovering above the right of the ring, filming from on high
PIX_X, PIX_D, PIX_HOVER = 400.0, 1650.0, 400.0  # in the fighters' (sharp) plane, over the ring


def pixie_pose(t, feed, staged=False):
    """Her performance. staged=True: the close-up set-up (shot 3), turned more to the lens.
    Thought -> glance -> breath -> line: she watches the hug curdle her face, chin up, "Ew."
    (head pulled back, brows knit), a beat, "What is he doing?" (one brow up, head tilted),
    an eye-roll, then her crystal back up to her face and she turns to it."""
    low = pixie_low(t)
    talk = tl.talk(SCENE, t, "CROWD")
    w_what = _word("s5_l1", 1, L1.start + 0.7)
    curdle = core.inout_sine(clamp((t - (T_LOW1 - 0.2)) / 0.5))
    ew = core.window(t, L1.start - 0.12, w_what + 0.1, 0.12, 0.25)
    what = core.window(t, w_what, L1.end + 0.25, 0.2, 0.3)
    roll = core.window(t, L1.end + 0.12, L1.end + 0.75, 0.18, 0.3)
    back = core.inout_sine(clamp((t - (L1.end + 0.5)) / 0.45))
    glee = (0.35 + 0.3 * clamp(impact_pulse(t))) * (1.0 - core.inout_sine(clamp((t - T_STOP) / 0.6)))
    e = _expr(("sneer", 1.0), ("happy", glee), ("surprised", core.window(t, T_HUG, T_SIL + 0.3, 0.15, 0.4)),
              ("angry", 0.4 * ew), ("skeptical", 0.7 * what), ("bored", 0.8 * roll + 0.6 * back))
    disgust = max(curdle, core.inout_sine(clamp((t - T_HUG) / 0.5)) * 0.6) * (1.0 - 0.4 * back)
    if disgust > 0.0:
        e = e.with_(smile=lerp(e.smile, -0.75, disgust))
    turn = (0.6 - 0.75 * back) if staged else -0.25
    yaw = -1.0 + 0.6 * turn
    dim = 1.0 - 0.75 * low * (1.0 - back)
    hold = ch.crystal_hold(face=clamp(-math.cos(yaw) * 1.4, -1.0, 1.0), size=1.7 if staged else 1.6,
                           thumb=feed, t=t, glow=dim)
    if low <= 0.0:
        near = ch.Arm("raise_crystal_film", hold=hold)
    else:
        near = ch.Arm("lower_crystal", amt=low * (1.0 - back), prev="raise_crystal_film", hold=hold)
        if back > 0.0:
            near = ch.Arm("raise_crystal_film", amt=back, prev="lower_crystal", hold=hold)
    look = (-0.72 + 1.0 * back, 0.38 + 0.12 * ew - 0.1 * what)      # chin up, eyes DOWN at the pair
    if roll > 0:
        look = (lerp(look[0], 0.3, roll), lerp(look[1], -0.85, roll))
    head_nod = 0.12 + 0.2 * ew + 0.06 * curdle - 0.08 * what + 0.1 * roll
    return ch.PixiePose(facing=-1, turn=turn, hover=PIX_HOVER if not staged else 40.0, talk=talk, mood=e,
                        head_nod=head_nod, head_tilt=0.25 * what - 0.08 * ew, look=look, far=ch.Arm("hip"),
                        near=near, seed=2)


PIX_MCU = (1330.0, 1262.0, 12.5)                  # her medium close-up: anchor x, ground y (below frame), scale


class _SoftWings:
    """Her close-up: at this size the library's buzz (three hard-edged copies at unrelated
    angles every frame plus a speed arc) strobes like a wireframe fan beside her face. Here the
    beat is a soft motion smear -- the wing drawn at several positions across its stroke,
    blurred -- under one faint crisp wing that only sways gently. Active only while the
    close-up pixie draws (it swaps the pixie module's private wing painter)."""

    N = 13
    AMP = 0.5                                     # half the stroke (rad), like pixie_wing_buzz's range

    def __init__(self, t, blur=9.0):
        self.t, self.blur = t, blur

    def __enter__(self):
        self.orig_w, self.orig_b = PX._wings, PX.pixie_wing_buzz
        PX._wings = self._draw
        return self

    def __exit__(self, *exc):
        PX._wings, PX.pixie_wing_buzz = self.orig_w, self.orig_b
        return False

    def _paint_wings(self, q, c2, flap, buzz_pose):
        """One library wing set at flap angle `flap` (rad), drawn into c2."""
        cr0, pose0 = q.cr, q.pose
        q.cr, q.pose = c2, buzz_pose
        PX.pixie_wing_buzz = lambda t, seed=0: flap / 0.25        # buzz 0 -> flap = 0.25 x this
        try:
            self.orig_w(q)
        finally:
            q.cr, q.pose = cr0, pose0
            PX.pixie_wing_buzz = self.orig_b

    def _draw(self, q):
        cr = q.cr
        m = cr.get_matrix()
        root = q.proj.xy(q.S["T"]((0.0, -0.80 * q.b.sh_y, -3.0)))
        R = 58.0
        corners = [cr.user_to_device(root[0] + sx * R, root[1] + sy * R) for sx in (-1, 1) for sy in (-1, 1)]
        pad = 3.0 * self.blur
        x0 = int(min(c[0] for c in corners) - pad)
        y0 = int(min(c[1] for c in corners) - pad)
        x1 = int(max(c[0] for c in corners) + pad)
        y1 = int(max(c[1] for c in corners) + pad)
        if x1 <= x0 or y1 <= y0:
            return
        still = q.pose.with_(buzz=0.0)
        # the smear: the wing across its whole stroke, at half resolution, blurred
        k = 0.5
        surf = core.new_surface(int((x1 - x0) * k) + 2, int((y1 - y0) * k) + 2)
        c2 = cairo.Context(surf)
        c2.scale(k, k)
        c2.translate(-x0, -y0)
        c2.transform(m)
        for i in range(self.N):
            self._paint_wings(q, c2, self.AMP * math.cos(math.pi * i / (self.N - 1)), still)
        surf.flush()
        soft = fx.blur_surface(surf, self.blur * k)
        cr.save()
        cr.identity_matrix()
        cr.translate(x0, y0)
        cr.scale(1.0 / k, 1.0 / k)
        cr.set_source_surface(soft, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint_with_alpha(0.42)
        cr.restore()
        # one crisp wing over it (veins, spot): a slow sway, never the aliased buzz
        self._paint_wings(q, cr, 0.12 * math.sin(self.t * TAU * 1.3), still)


def pixie_mcu_pose(t, feed):
    """Shot 4, her medium close-up (staged 3/4 toward the pair, who sit soft on the left third
    behind her). Thought -> glance -> line: she stares down at the hug and her face curdles
    (lip curl, brows knit) -- "Ew." (the head jerks back, nose up) -- "What is he doing?" (head
    cocked, one brow up, her free hand flicks out at them, palm up) -- an eye-roll up and away
    -- and the crystal comes back up to her face, its cold light washing over it."""
    low = core.inout_sine(clamp((t - (T_PIXIE - 0.3)) / 0.55))    # the crystal comes down off her face
    talk = tl.talk(SCENE, t, "CROWD")
    w_what = _word("s5_l1", 1, L1.start + 0.2)
    curdle = core.inout_sine(clamp((t - (T_PIXIE - 0.3)) / 0.45))
    ew = core.window(t, L1.start - 0.1, w_what + 0.15, 0.1, 0.3)
    what = core.window(t, w_what - 0.05, L1.end + 0.2, 0.25, 0.3)
    flick = core.window(t, w_what + 0.1, L1.end + 0.05, 0.22, 0.35)
    roll = core.window(t, L1.end + 0.08, L1.end + 0.62, 0.16, 0.24)
    back = core.inout_sine(clamp((t - (L1.end + 0.38)) / 0.4))
    e = _expr(("sneer", 1.0), ("angry", 0.45 * ew), ("skeptical", 0.85 * what), ("bored", 0.85 * roll + 0.7 * back))
    disgust = curdle * (1.0 - 0.5 * back)
    e = e.with_(smile=lerp(e.smile, -0.8, disgust), brow_asym=e.brow_asym + 0.35 * what)
    hold = ch.crystal_hold(face=-1.0, size=1.55, thumb=feed, t=t, glow=0.35 + 0.65 * back)
    near = ch.Arm("lower_crystal", amt=low, prev="raise_crystal_film", hold=hold)
    if back > 0.0:                                 # ... back up to her chin: she reads it, bored
        near = ch.Arm("raise_crystal_film", amt=0.42 * back, prev="lower_crystal", hold=hold)
    far = ch.Arm("talk", amt=flick, prev="hip", phase=t * 0.8) if flick > 0.0 else ch.Arm("hip")
    look = (-0.88 + 1.1 * back, 0.78 - 0.25 * ew + 0.05 * what - 0.6 * back)   # eyes DOWN on the pair
    if roll > 0.0:
        look = (lerp(look[0], 0.45, roll), lerp(look[1], -0.9, roll))
    return ch.PixiePose(facing=-1, turn=0.35 - 0.55 * back, hover=3.0, bob=1.2, talk=talk, mood=e,
                        head_nod=0.14 + 0.24 * ew + 0.06 * curdle - 0.06 * what + 0.12 * roll - 0.1 * back,
                        head_tilt=0.28 * what - 0.1 * ew, head_turn=0.25 * back, look=look,
                        lean=-0.12 * ew, near=near, far=far, seed=2, shadow=False)


def pixie_low(t):
    """Her crystal comes down last of all (mid-way at the cut to her close-up)."""
    return core.inout_sine(clamp((t - (T_LOW1 - 0.5)) / 0.95))


# ----------------------------------------------------------------------------------------
# the dragon
# ----------------------------------------------------------------------------------------

def dragon_light(t):
    g = crystal_level(t) if t < T_EMPTY else 0.25
    base = B.Light(key=(0.62, 0.68, 0.82), ambient=(0.30, 0.34, 0.48), rim=(0.55, 0.88, 1.0), rim_strength=0.45 + 0.35 * g,
                   direction=(-0.4, -0.92), rim_direction=(1.0, -0.3), name="s5_arcade")
    if t >= T_EMPTY:
        # the emptied square: he stands deeper in the arcade's shadow; the warmth that falls on
        # the two of them catches the edge of his face (a warm rim from their side)
        w = _q(warmth(t), 16)
        base = base.with_(exposure=0.86, rim=core.lerp_tuple((0.55, 0.8, 0.95), (1.0, 0.78, 0.58), w),
                          rim_strength=0.4 + 0.35 * w, name="s5_arcade_end")
    return base


BAG_DAMP = 0.35                                   # the S3 rain drying off it (S4 0.6 .. S6 dry)


def dragon_bag(t):
    """The apothecary's sack he has carried since S2 (S3 -> S4 -> S6): open at the neck, the
    remedies peeking out, hanging from his LEFT hand (his far arm: he faces right), the right
    hand in his coat pocket. It sways a hair with his breathing."""
    swing = 0.04 * math.sin(t * 1.3) + 0.02 * math.sin(t * 2.9 + 1.0)
    return ch.Arm("carry_bag", hold=P.bag_hold(dragon_light(t).with_(exposure=0.82), t, swing, state="open",
                                               damp=BAG_DAMP))


def dragon_pose(t, shot):
    """shot 1: the master; 5: his medium close-up (the lines); 6: the emptied square."""
    blink = None
    wince = 0.0
    for ti, pw, _ in IMPACTS:
        wince = max(wince, core.window(t, ti + 0.05, ti + 0.6, 0.06, 0.4) * min(1.0, pw))
    talk = tl.talk(SCENE, t, "MAN")
    if shot == 1:
        e = _expr(("lonely", 1.0), ("worried", 0.5 * wince))
        if wince > 0.6:
            blink = clamp((wince - 0.6) * 4.0)
        return ch.DragonPose(facing=1, turn=0.55, near=ch.Arm("pockets"), far=dragon_bag(t), mood=e,
                             look=(0.55, 0.05), wings=-0.85, hunch=0.6, head_nod=-0.05 - 0.05 * wince, blink=blink,
                             tail_curl=0.5, seed=1)
    if shot == 5:
        # thought -> glance -> breath -> line. He watches the pair; the thought drops his eyes;
        # "We'll film a fight." with a dry, rueful half-smile on "fight"; his eyes follow the
        # bored ones drifting off; a breath in; "But someone gets gentle," -- his brows lift,
        # his face softens toward the two of them -- "and everybody looks away." -- his eyes
        # sweep after the turning backs, then sink, and a slow blink
        w_fight = _word("s5_l2", 3, L2.start + 0.74)
        think = core.window(t, T_DRAGON + 0.35, L2.start + 0.15, 0.15, 0.22)
        irony = core.window(t, w_fight - 0.15, L2.end + 0.45, 0.15, 0.45)
        follow = core.window(t, L2.end + 0.25, L3.start - 0.35, 0.45, 0.4)
        breath = core.window(t, L3.start - 0.6, L3.start + 0.05, 0.3, 0.2)
        gentle = core.window(t, T_GENTLE - 0.25, L3.end + 0.9, 0.35, 0.6)
        sweep = core.inout_sine(clamp((t - T_EVERY) / max(0.3, L3.end - T_EVERY)))
        track = core.window(t, T_EVERY - 0.15, L3.end + 0.1, 0.25, 0.45)
        sink = core.inout_sine(clamp((t - (L3.end - 0.25)) / 0.6))
        e = _expr(("lonely", 1.0), ("sad", 0.3 + 0.2 * think), ("kind", 0.55 * gentle), ("sad", 0.35 * sink))
        e = e.with_(smile=e.smile + 0.22 * irony, brow_asym=e.brow_asym + 0.35 * irony,
                    brow_in=e.brow_in + 0.25 * gentle)
        look = (0.5 - 0.12 * think + 0.32 * follow + (0.25 * sweep - 0.05) * track,
                0.08 + 0.42 * think - 0.04 * irony + 0.1 * track + 0.18 * sink)
        blink = None
        if T_DRAGON + 0.05 < t < T_DRAGON + 0.25:
            blink = core.window(t, T_DRAGON + 0.05, T_DRAGON + 0.25, 0.08, 0.1)
        elif L3.end + 0.05 < t < L3.end + 0.55:                      # a slow blink as it lands
            blink = core.window(t, L3.end + 0.05, L3.end + 0.55, 0.18, 0.25)
        return ch.DragonPose(facing=1, turn=0.3, near=ch.Arm("pockets"), far=dragon_bag(t), mood=e,
                             look=look, wings=-0.85, hunch=0.62 - 0.08 * breath + 0.05 * sink, lean=-0.04 * breath,
                             head_nod=-0.12 - 0.12 * think + 0.07 * breath - 0.08 * sink,
                             head_turn=0.06 * follow + 0.06 * track * sweep, head_tilt=0.05 * gentle,
                             talk=talk, blink=blink, tail_curl=0.5, seed=1)
    # shot 6: the emptied square -- he keeps looking; a sigh of longing (a little grey smoke),
    # then his brows soften and his wings lift a fraction: the warmth reaches him too
    sigh = core.window(t, T_SIGH, T_SIGH + 1.3, 0.35, 0.7)
    soften = core.inout_sine(clamp((t - (T_SIGH + 0.9)) / 1.4))
    e = _expr(("lonely", 1.0), ("sigh", 0.55 * sigh), ("kind", 0.4 * soften))
    return ch.DragonPose(facing=1, turn=0.55, near=ch.Arm("pockets"), far=dragon_bag(t), mood=e,
                         look=(0.6, 0.12 + 0.1 * sigh), wings=-0.85 + 0.3 * soften, hunch=0.6 + 0.06 * sigh - 0.05 * soften,
                         head_nod=-0.06 - 0.06 * sigh + 0.04 * soften, sigh=0.75 * sigh, tail_curl=0.5, seed=1)


# ----------------------------------------------------------------------------------------
# static art: sky, the far side of the square, the square, the cobbles, the arcade
# ----------------------------------------------------------------------------------------

PAL = env.palette("evening")
HOUSE_D = 4300.0
HOUSE_GY = gp(0.0, HOUSE_D)[1]
HOUSE_SC = F_LEN / HOUSE_D
NIGHT_BLUE = (0.07, 0.09, 0.15)


def _grade(cr, y0, y1, a0, a1, color=NIGHT_BLUE):
    """Darken what this part has drawn so far (ATOP keeps it inside the drawn pixels):
    alpha a0 at world y0 .. a1 at world y1 -- the evening value plan."""
    cr.save()
    cr.set_operator(cairo.OPERATOR_ATOP)
    cr.set_source(core.linear(0, y0, 0, y1, [(0.0, core.alpha(color, a0)), (1.0, core.alpha(color, a1))]))
    cr.paint()
    cr.restore()


def draw_sky(cr):
    env.draw_sky(cr, -600, -500, 3100, 1400, kind="evening", horizon=HOUSE_GY - 60, seed=5, clouds=True)
    _grade(cr, -500, HOUSE_GY - 200, 0.38, 0.0)
    # the last of the daylight low behind the roofs: a pale cold band (the roofs read against it)
    cr.save()
    cr.rectangle(-600, HOUSE_GY - 420, 3100, 420)
    cr.set_source(core.linear(0, HOUSE_GY - 420, 0, HOUSE_GY, [(0.0, core.alpha("#c8d0dc", 0.0)),
                                                               (1.0, core.alpha("#c8d0dc", 0.35))]))
    cr.fill()
    cr.restore()


def draw_houses(cr):
    env.draw_street_row(cr, -700, 2700, HOUSE_GY, HOUSE_SC, "evening", seed=31, lit=0.0,
                        floors=(1, 2), widths=(560.0, 780.0), alley=0.3)
    # the houses stand against the pale evening sky: their faces in cool shadow
    _grade(cr, HOUSE_GY - 420, HOUSE_GY, 0.42, 0.62)
    env.draw_haze(cr, -700, HOUSE_GY - 520, 3400, 540, PAL["haze"], 0.0, 0.16)


def draw_ground(cr):
    env.draw_cobbles(cr, -700, HOUSE_GY - 6, 3400, 1700, kind="evening", seed=5, vp=(CX0, Y_H), size=(3.5, 52.0),
                     contrast=0.85)
    # far rows catch the sky; near the camera the street sinks into the arcade's shadow
    _grade(cr, HOUSE_GY, 1200, 0.18, 0.62)


def _fill(cr, color, tex="paint", alpha=0.14, scale=0.8):
    core.src(cr, color)
    cr.fill_preserve()
    cr.save()
    cr.clip()
    env.texture(cr, tex, alpha, scale)
    cr.restore()
    cr.new_path()


def _quad(cr, pts):
    cr.new_path()
    core.polygon(cr, pts)


def _box(cr, X0_, X1_, D0_, D1_, Y0_, Y1_, front, top, side, tex="wood"):
    """An axis-aligned box in the square: front face, top and the visible end."""
    fp = [p3(X0_, Y0_, D0_), p3(X1_, Y0_, D0_), p3(X1_, Y1_, D0_), p3(X0_, Y1_, D0_)]
    tp = [p3(X0_, Y1_, D0_), p3(X1_, Y1_, D0_), p3(X1_, Y1_, D1_), p3(X0_, Y1_, D1_)]
    if X1_ < 0:            # left of the axis: we see its right end
        sp = [p3(X1_, Y0_, D0_), p3(X1_, Y0_, D1_), p3(X1_, Y1_, D1_), p3(X1_, Y1_, D0_)]
    else:
        sp = [p3(X0_, Y0_, D0_), p3(X0_, Y0_, D1_), p3(X0_, Y1_, D1_), p3(X0_, Y1_, D0_)]
    if Y1_ < H_CAM:
        _quad(cr, tp)
        _fill(cr, top, tex, 0.12)
    if not (X0_ < 0 < X1_):
        _quad(cr, sp)
        _fill(cr, side, tex, 0.12)
    _quad(cr, fp)
    _fill(cr, front, tex, 0.14)


def _haze(c, D, k=1.0):
    return env.haze_toward(c, PAL["haze"], clamp((D - 1500.0) / 3200.0) * 0.55 * k)


def _drum_path(cr, X, D, r, h, bulge=1.0):
    """Outline of a vertical drum (well, barrel): front half of the base, sides, front half of
    the top rim. Returns (top ellipse, base ellipse)."""
    cx_, cy_, rx, ry = circle3(X, D, r, h)
    bx_, by_, brx, bry = circle3(X, D, r, 0.0)
    bl = rx * bulge
    cr.new_path()
    cr.move_to(cx_ - rx, cy_)
    if bulge != 1.0:
        cr.curve_to(cx_ - bl, lerp(cy_, by_, 0.3), cx_ - bl, lerp(cy_, by_, 0.7), bx_ - brx, by_)
    else:
        cr.line_to(bx_ - brx, by_)
    cr.save()
    cr.translate(bx_, by_)
    cr.scale(brx, bry)
    cr.arc_negative(0, 0, 1.0, math.pi, 0.0)
    cr.restore()
    if bulge != 1.0:
        cr.curve_to(cx_ + bl, lerp(cy_, by_, 0.7), cx_ + bl, lerp(cy_, by_, 0.3), cx_ + rx, cy_)
    else:
        cr.line_to(cx_ + rx, cy_)
    cr.save()
    cr.translate(cx_, cy_)
    cr.scale(rx, ry)
    cr.arc(0, 0, 1.0, 0.0, math.pi)
    cr.restore()
    cr.close_path()
    return (cx_, cy_, rx, ry), (bx_, by_, brx, bry)


def _ellipse_path(cr, cx_, cy_, rx, ry, a0=0.0, a1=TAU):
    cr.save()
    cr.translate(cx_, cy_)
    cr.scale(rx, ry)
    cr.arc(0, 0, 1.0, a0, a1)
    cr.restore()


def _side_shade(cr, path, x0, x1, alpha=0.5):
    """Shadow the right side of a form (the evening sky lights from the upper left)."""
    cr.save()
    cr.append_path(path)
    cr.clip()
    cr.set_source(core.linear(x0, 0, x1, 0, [(0.0, core.alpha(NIGHT_BLUE, 0.0)), (0.55, core.alpha(NIGHT_BLUE, alpha * 0.4)),
                                             (1.0, core.alpha(NIGHT_BLUE, alpha))]))
    cr.paint()
    cr.restore()


def draw_well(cr, X, D):
    s = F_LEN / D
    stone = _haze(core.mix(PAL["stone"], "#7c8496", 0.4), D)
    stone_dk = core.shade(stone, 0.35)
    wood = _haze("#5b4a3e", D)
    wood_dk = core.shade(wood, 0.4)
    roof = _haze(core.mix(PAL["roof"], "#4a4f60", 0.5), D)
    r, h = 120.0, 100.0
    env.draw_ground_shadow(cr, *gp(X + 30, D + 30)[:2], 160 * s, 34 * s, alpha=0.45)
    for sgn in (-1.0, 1.0):                         # the two posts
        x0, y0 = p3(X + sgn * (r - 14), h - 10, D)
        _, y1 = p3(X + sgn * (r - 14), 330, D)
        w = 13.0 * s
        cr.rectangle(x0 - w / 2, y1, w, y0 - y1)
        _fill(cr, wood if sgn < 0 else wood_dk, "wood", 0.2)
    ax0, ay = p3(X - r + 14, 262, D)                # windlass, crank, rope, bucket
    ax1, _ = p3(X + r - 14, 262, D)
    cr.rectangle(ax0, ay - 6 * s, ax1 - ax0, 12 * s)
    _fill(cr, wood, "wood", 0.2)
    hx, hy = p3(X + r + 8, 262, D)
    cr.set_line_width(5 * s)
    core.src(cr, wood_dk)
    cr.move_to(ax1, ay)
    cr.line_to(hx + 4, hy)
    cr.line_to(hx + 4, hy + 34 * s)
    cr.stroke()
    rx_, ry_ = p3(X + 10, 262, D)
    bx, by = p3(X + 10, 175, D)
    cr.set_line_width(2.2 * s)
    core.src(cr, core.shade(wood, 0.2))
    cr.move_to(rx_, ry_)
    cr.line_to(bx, by)
    cr.stroke()
    bw, bh = 26 * s, 30 * s
    _quad(cr, [(bx - bw * 0.6, by), (bx + bw * 0.6, by), (bx + bw * 0.45, by + bh), (bx - bw * 0.45, by + bh)])
    _fill(cr, wood, "wood", 0.2)
    a = p3(X - r - 40, 318, D)                     # a little shingled gable roof
    b = p3(X + r + 40, 318, D)
    c = p3(X, 420, D)
    _quad(cr, [a, c, b, (b[0], b[1] + 14 * s), (a[0], a[1] + 14 * s)])
    _fill(cr, roof, "plaster", 0.18)
    cr.save()
    _quad(cr, [a, c, b])
    cr.clip()
    cr.set_line_width(1.6 * s)
    core.src(cr, core.shade(roof, 0.3), 0.6)
    for k in range(1, 6):
        y = lerp(c[1], a[1], k / 6.0)
        cr.move_to(a[0] - 10, y)
        cr.line_to(b[0] + 10, y)
    cr.stroke()
    cr.restore()
    cr.set_line_width(3.0 * s)
    core.src(cr, core.tint(roof, 0.25), 0.7)
    cr.move_to(a[0], a[1])
    cr.line_to(*c)
    cr.stroke()
    top, base = _drum_path(cr, X, D, r, h)          # the stone drum
    pth = cr.copy_path()
    _fill(cr, stone, "stone", 0.22)
    cx_, cy_, rx, ry = top
    by_ = base[1]
    cr.save()
    cr.append_path(pth)
    cr.clip()
    cr.set_line_width(1.6 * s)
    core.src(cr, stone_dk, 0.7)
    for k in range(1, 3):
        _ellipse_path(cr, cx_, lerp(cy_, by_, k / 3.0), rx, ry, 0.0, math.pi)
        cr.stroke()
    rr = random.Random(5)
    for k in range(3):
        y0 = lerp(cy_, by_, k / 3.0)
        y1 = lerp(cy_, by_, (k + 1) / 3.0)
        for j in range(7):
            ang = (j + 0.5 * (k % 2) + rr.random() * 0.2) / 7.0 * math.pi
            xx = cx_ + rx * math.cos(ang)
            cr.move_to(xx, y0 + ry * math.sin(ang))
            cr.line_to(xx, y1 + ry * math.sin(ang))
    cr.stroke()
    cr.restore()
    _side_shade(cr, pth, cx_ - rx, cx_ + rx, 0.55)
    _ellipse_path(cr, cx_, cy_, rx, ry)              # the coping ring and the dark water
    _fill(cr, core.tint(stone, 0.18), "stone", 0.2)
    _ellipse_path(cr, cx_, cy_ + ry * 0.05, rx * 0.78, ry * 0.7)
    core.src(cr, core.shade(PAL["near"], 0.45))
    cr.fill()


def draw_barrel(cr, X, D, r=34.0, h=78.0, seed=0):
    wood = _haze(core.mix("#5e4a3a", "#6a5a4c", core.hash01(seed, 3)), D)
    top, base = _drum_path(cr, X, D, r, h, bulge=1.08)
    pth = cr.copy_path()
    _fill(cr, wood, "wood", 0.2)
    cx_, cy_, rx, ry = top
    cr.save()
    cr.append_path(pth)
    cr.clip()
    cr.set_line_width(2.5 * F_LEN / D)
    core.src(cr, core.shade(wood, 0.45), 0.8)
    for f in (0.18, 0.82):
        _ellipse_path(cr, cx_, lerp(cy_, base[1], f), rx * 1.07, ry, 0.0, math.pi)
        cr.stroke()
    cr.restore()
    _side_shade(cr, pth, cx_ - rx, cx_ + rx, 0.5)
    _ellipse_path(cr, cx_, cy_, rx, ry)
    _fill(cr, core.tint(wood, 0.12), "wood", 0.2)


def draw_stall(cr, X, D, w=440.0, seed=0, canvas="#6a6f86"):
    """A closed market stall: a plank counter on trestles, two posts, the awning rolled and
    tied on its beam, the goods under a lashed canvas."""
    s = F_LEN / D
    wood = _haze("#5a4a3e", D)
    wood_lt = core.tint(wood, 0.15)
    wood_dk = core.shade(wood, 0.4)
    can = _haze(canvas, D)
    x0, x1 = X - w / 2, X + w / 2
    env.draw_ground_shadow(cr, *gp(X + 30, D + 40)[:2], w * 0.62 * s, 30 * s, alpha=0.4)
    for xx in (x0 + 10, x1 - 10):                   # back posts
        a, b = p3(xx, 0, D + 110), p3(xx, 330, D + 110)
        cr.rectangle(a[0] - 5 * s, b[1], 10 * s, a[1] - b[1])
        _fill(cr, wood_dk, "wood", 0.15)
    pts = []                                        # the goods under canvas (lumpy)
    rr = random.Random(seed)
    n = 7
    for k in range(n + 1):
        xx = lerp(x0 + 20, x1 - 20, k / n)
        pts.append(p3(xx, 118 + 70 * math.sin(math.pi * k / n) + rr.uniform(-14, 22), D + 50))
    base_l, base_r = p3(x0 + 10, 112, D + 4), p3(x1 - 10, 112, D + 4)
    cr.new_path()
    cr.move_to(*base_l)
    core.smooth_open(cr, pts, 0.5, move=False)
    cr.line_to(*base_r)
    cr.close_path()
    gp_ = cr.copy_path()
    _fill(cr, can, "plaster", 0.2)
    _side_shade(cr, gp_, base_l[0], base_r[0], 0.45)
    cr.set_line_width(1.6 * s)
    core.src(cr, core.shade(can, 0.35), 0.6)
    for k in range(1, 4):                           # lashing ropes
        xa = lerp(x0 + 40, x1 - 40, k / 4.0)
        cr.move_to(*p3(xa, 112, D + 4))
        cr.line_to(*p3(xa + 20, 180, D + 50))
    cr.stroke()
    _box(cr, x0, x1, D, D + 100, 70, 112, wood, wood_lt, wood_dk)      # the counter
    for xx in (x0 + 30, x1 - 30):                   # trestle legs
        a, b = p3(xx, 0, D + 10), p3(xx, 72, D + 10)
        cr.rectangle(a[0] - 6 * s, b[1], 12 * s, a[1] - b[1])
        _fill(cr, wood_dk, "wood", 0.15)
    for xx in (x0, x1):                             # front posts
        a, b = p3(xx, 0, D - 4), p3(xx, 300, D - 4)
        cr.rectangle(a[0] - 7 * s, b[1], 14 * s, a[1] - b[1])
        _fill(cr, wood, "wood", 0.18)
    a, b = p3(x0 - 20, 300, D - 4), p3(x1 + 20, 300, D - 4)            # the rolled awning
    rad = 18 * s
    cr.new_path()
    core.rounded_rect(cr, a[0], a[1] - rad, b[0] - a[0], rad * 2.0, rad)
    _fill(cr, core.tint(can, 0.08), "plaster", 0.2)
    cr.set_line_width(3 * s)
    core.src(cr, core.shade(can, 0.4), 0.8)
    for k in range(1, 4):
        xx = lerp(a[0], b[0], k / 4.0)
        cr.move_to(xx, a[1] - rad)
        cr.line_to(xx, a[1] + rad)
    cr.stroke()


def draw_crate(cr, X, D, sz=60.0, seed=0):
    wood = _haze(core.mix("#6a5642", "#5a4a3c", core.hash01(seed, 1)), D)
    _box(cr, X - sz / 2, X + sz / 2, D, D + sz, 0, sz * 0.85, wood, core.tint(wood, 0.15), core.shade(wood, 0.35))
    cr.set_line_width(1.5 * F_LEN / D)
    core.src(cr, core.shade(wood, 0.45), 0.7)
    cr.move_to(*p3(X - sz / 2, sz * 0.42, D))
    cr.line_to(*p3(X + sz / 2, sz * 0.42, D))
    cr.stroke()


def draw_cart(cr, X, D):
    """A hand-cart resting with its shafts on the cobbles (side-on)."""
    wood = _haze("#5e4c3e", D)
    wood_dk = core.shade(wood, 0.4)
    s = F_LEN / D
    env.draw_ground_shadow(cr, *gp(X, D + 20)[:2], 190 * s, 20 * s, alpha=0.4)
    _quad(cr, [p3(X - 150, 95, D), p3(X + 120, 95, D), p3(X + 135, 150, D), p3(X - 160, 150, D)])
    _fill(cr, wood, "wood", 0.2)
    cr.set_line_width(2 * s)
    core.src(cr, wood_dk, 0.7)
    for f in (0.33, 0.66):
        cr.move_to(*p3(X - 155, lerp(95, 150, f), D))
        cr.line_to(*p3(X + 128, lerp(95, 150, f), D))
    cr.stroke()
    cr.set_line_width(9 * s)
    core.src(cr, wood_dk)
    cr.move_to(*p3(X + 120, 110, D))
    cr.line_to(*p3(X + 330, 0, D))
    cr.stroke()
    wx, wy = p3(X - 20, 62, D + 30)
    rr = 62 * s
    cr.new_path()
    core.circle(cr, wx, wy, rr)
    cr.set_line_width(9 * s)
    cr.stroke()
    cr.set_line_width(4 * s)
    for k in range(6):
        ang = k / 6.0 * math.pi
        cr.move_to(wx - math.cos(ang) * rr, wy - math.sin(ang) * rr)
        cr.line_to(wx + math.cos(ang) * rr, wy + math.sin(ang) * rr)
    cr.stroke()


WELL = (1180.0, 2500.0)
POST = (-760.0, 2500.0)


def draw_square(cr):
    """Everything standing in the square, far to near."""
    items = [
        (3650.0, lambda: draw_stall(cr, -1450.0, 3650.0, 470.0, 1, "#6c6a80")),
        (3600.0, lambda: draw_stall(cr, -880.0, 3600.0, 430.0, 2, "#7a6a5a")),
        (3550.0, lambda: draw_stall(cr, 1700.0, 3550.0, 450.0, 3, "#5e6a7a")),
        (3450.0, lambda: draw_crate(cr, -1130.0, 3450.0, 64.0, 1)),
        (3420.0, lambda: draw_crate(cr, -1080.0, 3410.0, 54.0, 2)),
        (3400.0, lambda: draw_barrel(cr, 1400.0, 3400.0, seed=1)),
        (3380.0, lambda: draw_barrel(cr, 1335.0, 3440.0, seed=2)),
        (3200.0, lambda: draw_cart(cr, -1750.0, 3200.0)),
        (WELL[1], lambda: draw_well(cr, *WELL)),
        (2350.0, lambda: draw_barrel(cr, 1560.0, 2350.0, 30, 70, seed=4)),
        (2300.0, lambda: draw_crate(cr, 1640.0, 2300.0, 58.0, 5)),
        (POST[1], lambda: P.draw_lantern_post(cr, *gp(*POST)[:2], F_LEN / POST[1], LS, 0.0, lit=0.0,
                                              style="crook", side=1, height=640, seed=2)),
    ]
    for d, fn in sorted(items, key=lambda k: -k[0]):
        fn()
    _grade(cr, HOUSE_GY - 300, 900, 0.25, 0.4)


def draw_arch(cr, pier_x, spring_y, crown, ring=82.0, focus=1.0):
    """The near side, in SCREEN space: the dragon stands under the arcade of a house across the
    street. A stone pier at the left and the arch springing from it, rising out of the top of
    the frame (the right of the frame stays open on the square). Dark: it is in shadow."""
    cx, cy = crown                                  # the arch's crown (may be above the frame)
    ax, ay = cx - pier_x, spring_y - cy             # quarter-ellipse radii of the intrados
    stone = "#1b1d27"
    stone_lt = "#2a2e3c"

    def arc_pt(u, grow=0.0):                        # u 0 = springing .. 1 = crown
        a = math.pi + u * math.pi / 2
        return (cx + (ax + grow) * math.cos(a), spring_y + (ay + grow) * math.sin(a))

    cr.new_path()                                   # the masonry: pier + spandrel
    cr.move_to(-400, 1500)
    cr.line_to(pier_x, 1500)
    cr.line_to(pier_x, spring_y)
    for k in range(1, 41):
        cr.line_to(*arc_pt(k / 40.0))
    cr.line_to(cx + 400, cy)
    cr.line_to(cx + 400, -600)
    cr.line_to(-400, -600)
    cr.close_path()
    core.src(cr, stone)
    cr.fill()
    cr.save()                                       # the arch ring: voussoirs
    cr.new_path()
    cr.move_to(*arc_pt(0.0))
    for k in range(1, 41):
        cr.line_to(*arc_pt(k / 40.0))
    for k in range(40, -1, -1):
        cr.line_to(*arc_pt(k / 40.0, ring))
    cr.close_path()
    core.src(cr, stone_lt)
    cr.fill()
    cr.set_line_width(3.0)
    core.src(cr, "#101219", 0.9)
    for k in range(1, 14):
        u = k / 14.0
        cr.move_to(*arc_pt(u))
        cr.line_to(*arc_pt(u, ring))
    cr.stroke()
    cr.restore()
    # impost moulding at the springing, pier courses
    cr.rectangle(pier_x - 520, spring_y - 6, 520 + 26, 34)
    core.src(cr, stone_lt)
    cr.fill()
    cr.set_line_width(2.5)
    core.src(cr, "#101219", 0.8)
    y = spring_y + 120
    k = 0
    while y < 1300:
        cr.move_to(-400, y)
        cr.line_to(pier_x, y)
        x = pier_x - 90 - 60 * (k % 2)
        cr.move_to(x, y)
        cr.line_to(x, y + 112)
        y += 112
        k += 1
    cr.stroke()
    # the cold sky light catching the intrados edge and the pier's arris
    cr.set_line_width(4.0)
    core.src(cr, "#5c6a86", 0.55)
    cr.move_to(pier_x, 1300)
    cr.line_to(pier_x, spring_y + 28)
    cr.stroke()
    cr.move_to(*arc_pt(0.02))
    for k in range(2, 41):
        cr.line_to(*arc_pt(k / 40.0))
    cr.stroke()
    cr.save()
    cr.rectangle(-400, -600, cx + 800, 2100)
    cr.clip()
    env.texture(cr, "stone", 0.22 * focus, 1.6)
    cr.restore()


# ----------------------------------------------------------------------------------------
# baking: each shot's backdrop rendered once at its own framing (crisp, with its own DOF)
# ----------------------------------------------------------------------------------------

class Baked:
    """A backdrop rendered at a base camera; painted with the residual of the moving camera.
    parts = [(draw(cr), blur px, parallax)]; a draw with parallax None is in screen space."""

    def __init__(self, cam, parts, margin=48, opaque=True, grade=None):
        self.cam, self.margin = cam, margin
        wd, ht = W + 2 * margin, H + 2 * margin
        out = core.new_surface(wd, ht)
        oc = cairo.Context(out)
        self._grade = grade
        for k, (fn, blur, par) in enumerate(parts):
            tmp = core.new_surface(wd, ht)
            c = core.new_context(tmp)
            c.translate(margin, margin)
            if par is not None:
                c.transform(cam.matrix(par))
            fn(c)
            tmp.flush()
            if blur > 0:
                tmp = fx.blur_surface(tmp, blur, opaque_edges=(k == 0 and opaque))
            oc.set_source_surface(tmp, 0, 0)
            oc.paint()
        if grade is not None:
            oc.save()
            oc.translate(margin, margin)
            oc.transform(cam.matrix(1.0))
            grade(oc)
            oc.restore()
        out.flush()
        self.surface = out

    def paint(self, cr, cam_t, p=1.0):
        cr.save()
        cr.transform(residual(self.cam, cam_t, p))
        cr.set_source_surface(self.surface, -self.margin, -self.margin)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()


def residual(cam_base, cam_t, p):
    """Screen-space transform from the base framing to the current one at parallax p."""
    m = cam_base.matrix(p)
    m.invert()
    return m.multiply(cam_t.matrix(p))


class Soft:
    """Draw moving things soft (depth of field): half-res scratch surface, blur, upscale."""

    def __init__(self, res=0.5):
        self.res = res
        self.surf = core.new_surface(int(W * res), int(H * res))

    def begin(self):
        c = core.new_context(self.surf)
        c.set_operator(cairo.OPERATOR_CLEAR)
        c.paint()
        c.set_operator(cairo.OPERATOR_OVER)
        c.scale(self.res, self.res)
        return c

    def end(self, cr, radius, alpha=1.0):
        self.surf.flush()
        s2 = fx.blur_surface(self.surf, radius * self.res) if radius > 0 else self.surf
        cr.save()
        cr.identity_matrix()
        cr.scale(1.0 / self.res, 1.0 / self.res)
        cr.set_source_surface(s2, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint_with_alpha(alpha)
        cr.restore()


def cam_at(wx, wy, sx, sy, z):
    """The camera that shows world point (wx, wy) at screen point (sx, sy) with zoom z."""
    return core.Camera(wx - (sx - W / 2) / z, wy - (sy - H / 2) / z, z)


def zoom_cam(c, sx, sy, k):
    """Camera c pushed in by k about screen point (sx, sy)."""
    wx, wy = c.to_world(sx, sy)
    return cam_at(wx, wy, sx, sy, c.zoom * k)


FIGHT_SX, FIGHT_SY = PCX, PGY                      # the fight's anchor in world (master) coords
HUG_SX = PCX + (MINO_HUG_X + ORC_HUG_X) / 2.0 * PSC     # the hug's centre (world screen-x)

CAM_A0 = cam_at(FIGHT_SX, FIGHT_SY, 1105.0, 812.0, 1.24)
CAM_A1 = zoom_cam(CAM_A0, 1105.0, 640.0, 1.07)
CAM_I = cam_at(FIGHT_SX + 25.0, 650.0, 700.0, 610.0, 2.45)       # the insert, behind the crystal
CAM_B = cam_at(FIGHT_SX, 640.0, 960.0, 548.0, 2.3)
CAM_C = cam_at(HUG_SX, 640.0, 560.0, 610.0, 1.32)    # behind the pixie: the pair on the left third
CAM_D0 = cam_at(HUG_SX, 640.0, 1440.0, 560.0, 1.1)
CAM_E0 = CAM_A0                                   # the bookend: the master's first framing ...
PAIR_SCR = CAM_A0.to_screen(HUG_SX, PGY - 190.0)
CAM_E1 = zoom_cam(CAM_A0, PAIR_SCR[0], PAIR_SCR[1], 1.2)    # ... and a slow push in on the pair

# the dragon and the arch, placed per framing in SCREEN space (at the set-up's base camera)
DRAGON_AT = {1: (292.0, 1238.0, 1.30, 1.3), 5: (468.0, 1420.0, 2.12, 1.2)}
ARCH_AT = {1: (150.0, 395.0, (1180.0, -190.0)), 5: (40.0, 300.0, (1250.0, -330.0))}

# shots: 1 master, 2 insert (the crystal), 3 the circle, 4 the pixie, 5 the dragon, 6 the
# emptied square (the master's set-up again)
SHOT_STARTS = ((0.0, 1), (T_INS, 2), (T_CIRCLE, 3), (T_REACT, 7), (T_REACT1, 3), (T_PIXIE, 4), (T_DRAGON, 5),
               (T_EMPTY, 6))
CAM_R = zoom_cam(CAM_B, 960.0, 240.0, 1.45)       # the watchers: the far side soft behind their faces


def cam_d(t):
    u = core.inout_sine(clamp((t - T_DRAGON) / (T_EMPTY - T_DRAGON)))
    return zoom_cam(CAM_D0, 600.0, 420.0, lerp(1.0, 1.05, u))


def camera_for(t, shot):
    if shot == 1:
        return core.Camera.lerp(CAM_A0, CAM_A1, core.inout_sine(clamp(t / T_INS)))
    if shot == 2:
        u = core.inout_sine(clamp((t - T_INS) / (T_CIRCLE - T_INS)))
        return zoom_cam(CAM_I, 1240.0, 560.0, lerp(1.0, 1.04, u))
    if shot == 3:
        if t < T_STOP:
            return CAM_B.shake(t, amp=2.0 + 9.0 * impact_pulse(t), freq=2.4, seed=11)
        # locked off at the stop, then a slow push in on the two of them (the crowd falls away
        # to the frame edges) as the hug happens and the crystals come down
        settle = clamp((t - T_STOP) / 0.6)
        push = core.inout_sine(clamp((t - (T_STOP + 0.35)) / (T_PIXIE - T_STOP - 0.35)))
        c = zoom_cam(CAM_B, *CAM_B.to_screen(HUG_SX, PGY - 200.0), lerp(1.0, 1.16, push))
        return c.shake(t, amp=2.0 * (1.0 - settle), freq=2.4, seed=11)
    if shot == 4:
        return CAM_C.drift(t, amp=3.0, freq=0.2, seed=4)
    if shot == 7:
        return CAM_R.drift(t, amp=2.0, freq=0.3, seed=9)
    if shot == 5:
        return cam_d(t)
    u = core.inout_sine(clamp((t - T_EMPTY) / (DUR - T_EMPTY)))
    return core.Camera.lerp(CAM_E0, CAM_E1, u)


def set_of(shot):
    """Which baked set-up a shot uses (the emptied square is the master's; the watchers'
    cutaway paints the circle's set-up, pushed in and soft)."""
    return {6: 1, 7: 3}.get(shot, shot)


def base_cam(shot):
    return {1: CAM_A0, 2: CAM_I, 3: CAM_B, 4: CAM_C, 5: CAM_D0, 6: CAM_A0, 7: CAM_B}[shot]


def shot_of(t):
    k = 1
    for t0, n in SHOT_STARTS:
        if t >= t0:
            k = n
    return k


# ----------------------------------------------------------------------------------------
# reflected feeds in the crystals
# ----------------------------------------------------------------------------------------

FEED_FPS = 12.0                                   # the little reflections refresh at 12 fps
_FEED = {}


def make_feed(t):
    """The fight as the crystals see it (a portrait thumbnail, the crystal face's aspect),
    rendered once per 1/12 s (a pure function of the quantized time)."""
    tq = math.floor(t * FEED_FPS + 1e-6) / FEED_FPS
    hit = _FEED.get("k")
    if hit is not None and hit[0] == tq:
        return hit[1]

    def fn(c, w, h):
        core.vgrad(c, 0, 0, w, h, ["#3a4a62", "#1c2534"])
        sc = 0.088
        draw_pair(c, w * 0.45 - 15.0 * sc, h - 5, sc, tq, LS, detail=0)
    feed = ch.crystal_feed(fn, 60, 84)
    _FEED["k"] = (tq, feed)
    return feed


def scroll_thumb(t):
    """What they look at once they turn away: their own scrolling scrying-runes."""
    def thumb(cr, w, h):
        core.vgrad(cr, 0, 0, w, h, ["#20304a", "#152032"])
        off = (t * 26.0) % 18.0
        for k in range(-1, 4):
            y = k * 18.0 - off + 4
            core.src(cr, "#7fe8ff", 0.55)
            cr.rectangle(w * 0.18, y, w * 0.64, 9)
            cr.fill()
            core.src(cr, "#cfffff", 0.7)
            cr.rectangle(w * 0.24, y + 2, w * 0.2, 2.2)
            cr.fill()
    return thumb


# ----------------------------------------------------------------------------------------
# light
# ----------------------------------------------------------------------------------------

L_CROWD = LS.with_(exposure=0.86, rim=(0.5, 0.86, 1.0), rim_strength=0.55, name="s5_crowd")
L_BACK = B.Light(key=(0.62, 0.68, 0.84), ambient=(0.24, 0.28, 0.42), rim=(0.5, 0.9, 1.0), rim_strength=0.9,
                 direction=(-0.4, -0.92), rim_direction=(0.0, -1.0), exposure=0.82, name="s5_backlit")
L_INS = LS.with_(exposure=1.0, rim=(0.55, 0.92, 1.0), rim_strength=0.85, rim_direction=(-0.5, -0.85),
                 name="s5_insert")
L_PIX = LS.with_(exposure=1.0, rim=(0.55, 0.9, 1.0), rim_strength=0.75, rim_direction=(0.8, -0.6), name="s5_pixie")


def warmth(t):
    """The break in the cloud over the emptied square: already faintly there at the cut, it
    opens up over 1.5 s and then holds."""
    return 0.22 + 0.78 * core.inout_sine(clamp((t - T_EMPTY) / 1.5)) if t >= T_EMPTY else 0.0


def pair_light(t):
    g = crystal_level(t)
    cold = LS.with_(exposure=1.06, rim=(0.55, 0.92, 1.0), rim_strength=0.4 + 0.45 * g, name="s5_pair")
    warm = B.Light(key=(1.04, 0.98, 0.96), ambient=(0.46, 0.46, 0.6), rim=(1.0, 0.86, 0.76), rim_strength=0.85,
                   direction=(-0.35, -0.94), exposure=1.06, name="s5_grace")
    w = _q(warmth(t), 24)
    return B.Light.lerp(cold, warm, 0.9 * w) if w > 0 else cold


WARM_SKY = "#f6d2c0"
GRACE_SRC = (HUG_SX - 330.0, -170.0)               # the break in the cloud, up over the roofs (world)
GRACE_HIT = (HUG_SX + 6.0, PGY + 4.0)              # where the shaft lands: on the two of them


def grace_motes(cr, t, cam):
    """Motes drifting in the warm shaft over the pair (the end)."""
    w = warmth(t)
    if w <= 0.02:
        return
    (x0, y0), (x1, y1) = GRACE_SRC, GRACE_HIT

    def mask(x, y):
        u = clamp((y - y0) / (y1 - y0))
        cx_ = lerp(x0, x1, u)
        half = lerp(70.0, 165.0, u)
        return w * clamp(1.0 - abs(x - cx_) / half) * clamp(u * 2.5) * clamp((1.0 - u) * 5.0 + 0.15)

    with cam.view(cr, 1.0):
        fx.dust(cr, t, (x0 - 120, 40, x1 - x0 + 300, y1 - 60), n=90, color="#ffe4bc", alpha=0.6, size=(1.0, 2.6),
                seed=7, drift=(4.0, 6.0), twinkle=0.55, mask=mask)


def _shaft(cr, x0, y0, x1, y1, w0, w1, color, alpha, stops, soft=6):
    """A soft additive beam (like fx.light_shaft) with its own brightness profile along it:
    stops = [(offset 0..1 from (x0, y0), k)]; nested quads make the edges soft."""
    c = core.col(color)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    for k in range(soft):
        f = 1.0 - 0.55 * k / max(1, soft - 1)
        h0, h1 = w0 * 0.5 * f, w1 * 0.5 * f
        cr.move_to(x0 + nx * h0, y0 + ny * h0)
        cr.line_to(x1 + nx * h1, y1 + ny * h1)
        cr.line_to(x1 - nx * h1, y1 - ny * h1)
        cr.line_to(x0 - nx * h0, y0 - ny * h0)
        cr.close_path()
        pat = cairo.LinearGradient(x0, y0, x1, y1)
        for off, kk in stops:
            pat.add_color_stop_rgba(off, c[0], c[1], c[2], alpha * kk / soft)
        cr.set_source(pat)
        cr.fill()
    cr.restore()


def grace_light(lc, t, cam):
    """The end: a break in the cloud -- one soft warm shaft (a few rays breathing inside it)
    falls on the two of them only; a rose-gold pool on the cobbles round their feet; their
    heads and shoulders catch it. Light layer (additive, quarter-res)."""
    w = warmth(t)
    if w <= 0.0:
        return
    (sx0, sy0), (px, py) = GRACE_SRC, GRACE_HIT
    breathe = 0.92 + 0.08 * core.noise1(t * 0.5, 17)
    ang = math.atan2(py - sy0, px - sx0)
    L = math.hypot(px - sx0, py - sy0)
    with cam.view(lc, 1.0):
        # the shaft, from the ground UP: it dissolves into the pool at their feet, is brightest
        # round the two of them and thins out toward the cloud (the far roofs barely catch it)
        _shaft(lc, px, py + 70, sx0, sy0, 280, 120, WARM_SHAFT, 0.58 * w * breathe,
               ((0.0, 0.0), (0.09, 0.55), (0.2, 1.0), (0.4, 0.62), (0.62, 0.3), (1.0, 0.1)))
        fx.god_rays(lc, sx0, sy0, ang, 0.10, L * 0.97, WARM_SHAFT, t, n=4, width=(18, 70), alpha=0.15 * w,
                    seed=5, shimmer=0.5)
        fx.light_pool(lc, px + 6, py + 4, 230, 58, WARM_POOL, 0.30 * w)                 # the pool, in perspective
        fx.light_pool(lc, px, py + 2, 120, 30, WARM, 0.08 * w)
        fx.glow(lc, px - 16, py - 300.0, 175, WARM_SHAFT, 0.17 * w)               # heads and shoulders


def ring_light(lc, t, cam, glows):
    """The cyan of the raised crystals on the cobbles, in the air and round each crystal; the
    first warmth on the pair at the end."""
    g = crystal_level(t) * (1.0 - warmth(t))
    cx, cy, rx, ry = circle3(X0, D0, 560.0, 0.0)
    with cam.view(lc, 1.0):
        fx.light_pool(lc, cx, cy, rx, ry * 1.25, CYAN, 0.42 * g)
        fx.glow(lc, cx, cy - 230, 560, CYAN, 0.12 * g)
        for (x, y, s, gl) in glows:
            fx.glow(lc, x, y, 190 * s, CYAN, 0.16 * gl)
    grace_light(lc, t, cam)


def draw_dusk(cr):
    """The emptied square sinks into the evening round the two of them (world coords; cached):
    an elliptical darkening centred on the pair, clear over them, deep at the edges."""
    cr.save()
    cr.translate(HUG_SX - 40.0, PGY - 190.0)
    cr.scale(1.0, 0.6)
    pat = cairo.RadialGradient(0, 0, 90.0, 0, 0, 1300.0)
    c = NIGHT_BLUE
    for off, a in ((0.0, 0.0), (0.18, 0.06), (0.42, 0.30), (0.75, 0.48), (1.0, 0.6)):
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], a)
    cr.set_source(pat)
    cr.paint()
    cr.restore()


# ----------------------------------------------------------------------------------------
# setup
# ----------------------------------------------------------------------------------------

def stage_grade(cr):
    """The ring is a stage: the square darkens away from it (ATOP: only what is drawn)."""
    cx, cy, rx, ry = circle3(X0, D0, 900.0, 0.0)
    cr.save()
    cr.set_operator(cairo.OPERATOR_ATOP)
    cr.translate(cx, cy - 120)
    cr.scale(1.0, 0.55)
    pat = cairo.RadialGradient(0, 0, rx * 0.35, 0, 0, rx * 1.9)
    c = NIGHT_BLUE
    pat.add_color_stop_rgba(0.0, c[0], c[1], c[2], 0.0)
    pat.add_color_stop_rgba(0.5, c[0], c[1], c[2], 0.22)
    pat.add_color_stop_rgba(1.0, c[0], c[1], c[2], 0.5)
    cr.set_source(pat)
    cr.paint()
    cr.restore()


def _world_parts(sky_b, far_b, ground_b, house_b, sq_b):
    return [(draw_sky, sky_b, 0.25), (draw_ground, ground_b, 1.0), (draw_houses, house_b, 1.0),
            (draw_square, sq_b, 1.0)]


def setup():
    st = {"light": fx.LightLayer(), "soft": Soft(0.5), "softq": Soft(0.25)}
    st["bake"] = {1: Baked(CAM_A0, _world_parts(3.0, 2.4, 0.5, 1.2, 0.8), grade=stage_grade),
                  2: Baked(CAM_I, _world_parts(10.0, 9.0, 5.0, 8.0, 7.0), grade=stage_grade),
                  3: Baked(CAM_B, _world_parts(7.0, 6.0, 1.4, 4.0, 3.0), grade=stage_grade),
                  4: Baked(CAM_C, _world_parts(8.0, 7.0, 3.6, 5.5, 4.5), grade=stage_grade),
                  5: Baked(CAM_D0, _world_parts(4.0, 3.5, 1.2, 2.4, 1.8), grade=stage_grade)}
    st["arch"] = {1: Baked(CAM_A0, [(lambda c: draw_arch(c, *ARCH_AT[1]), 4.0, None)], margin=140, opaque=False),
                  5: Baked(CAM_D0, [(lambda c: draw_arch(c, *ARCH_AT[5], focus=0.6), 9.0, None)], margin=140,
                           opaque=False)}
    st["soft2"] = Soft(0.25)
    st["dusk"] = fx.Layer(draw_dusk, res=0.25, **env.MARGIN)
    st["mist"] = env.Mist(-700, HOUSE_GY - 140, 3400, 260, PAL["haze"], 0.14, seed=3, speed=10)
    st["watch_off"] = watcher_offsets()
    return st


# ----------------------------------------------------------------------------------------
# drawing
# ----------------------------------------------------------------------------------------

def world_items(t, skip_pixie=False, crowd_dt=0.0):
    """Everything that moves in the square, far to near: [(D, kind, member)]."""
    items = []
    tc = t + crowd_dt
    for m in MEMBERS:
        if crowd_dt > 0.0 and m.i not in SHOT6_KEEP:
            continue                                  # gone home (the ellipsis)
        X, D, _, _ = member_ground(m, tc)
        items.append((D, "m", m))
    items.append((D0, "pair", None))
    if not skip_pixie:
        items.append((PIX_D, "pixie", None))
    items.sort(key=lambda k: -k[0])
    return items


def _q(u, n=12):
    return round(clamp(u) * n) / n


def member_light(m, tc):
    """The front arc stands between us and the ring: backlit, dark, a cold rim -- until they
    turn round to their own crystals."""
    if m.D >= D0 - 150:
        return L_CROWD
    turn_u = _q(core.inout_sine(clamp((tc - m.t_turn) / 0.8)))
    return L_BACK if turn_u <= 0 else B.Light.lerp(L_BACK, L_CROWD, turn_u)


def draw_items(cr, items, t, cam, feed, sfeed, *, glows=None, crowd_dt=0.0, dy_front=0.0, detail=None):
    """Draw world items (from world_items) under cam. detail=0 for passes that get blurred."""
    tc = t + crowd_dt
    with cam.view(cr, 1.0):
        for D, kind, m in items:
            if kind == "m":
                pose, X, D, hop = member_pose(m, tc, feed, sfeed)
                sx, sy, s = gp(X, D)
                if sx < -400 or sx > W + 900:
                    continue                          # long gone
                dy = dy_front if D < D0 - 150 else 0.0
                rig = ch.draw_crowd(cr, sx, sy + dy - hop * s, s, m.spec, pose, member_light(m, tc), tc, detail)
                if glows is not None and "crystal" in rig.points and pose.crystal is not None:
                    glows.append((*rig.points["crystal"], s, clamp(pose.crystal.glow)))
            elif kind == "pair":
                draw_pair(cr, PCX, PGY, PSC, t, pair_light(t), detail=detail)
            else:
                sx, sy, s = gp(PIX_X, PIX_D)
                fly = pixie_flyoff(t)
                rig = ch.draw_pixie(cr, sx + fly[0], sy + fly[1], s, pixie_pose(t, feed), L_CROWD, t, detail)
                if glows is not None and "crystal" in rig.points:
                    glows.append((*rig.points["crystal"], s, 1.0 - 0.75 * pixie_low(t)))


# ----------------------------------------------------------------------------------------
# the watchers: a cutaway on three faces as the silence falls (s5_silence)
# ----------------------------------------------------------------------------------------
# Seen from the ring centre: the back arc faces the pair, so a reverse on them shows their faces
# lit from below by their own raised crystals, the far side of the square soft behind them.
# Staged in screen space (a cheat, like any reaction shot): (member, head target, scale, yaw,
# eye line, cheering arm, glance). At the cut they are mid-gasp; on the silence the mouths
# SNAP shut, the eyes stay wide and frozen, the cheering fist stops in the air and sinks.

@dataclass
class Watcher:
    i: int
    head: tuple
    scale: float
    yaw: float
    look: tuple
    cheer: bool = False
    glance: float = 0.0
    sharp: bool = True


WATCHERS = [Watcher(14, (250.0, 318.0), 1.75, 0.42, (0.25, 0.25), sharp=False),
            Watcher(2, (1745.0, 575.0), 2.05, -0.5, (-0.3, 0.3), sharp=False),
            Watcher(1, (585.0, 300.0), 2.4, 0.55, (0.32, 0.28), glance=0.55),
            Watcher(5, (1425.0, 430.0), 3.0, -0.62, (-0.4, 0.3), cheer=True),
            Watcher(3, (985.0, 505.0), 3.05, 0.18, (-0.08, 0.3), cheer=True, glance=-0.6)]


def _g_film_high(q, sk, side, arm):
    """The crystal held up high and out beside the head (filming over the crowd): the face
    stays clear under its glow even when the holder faces us."""
    AL = FK._AL(q)
    hc = q.S["head_c"]
    tgt = (sk[0] + side * 0.28 * AL, hc[1] - 0.34 * AL, hc[2] + 0.12 * AL)
    return FK.G(tgt, "grip", -0.9, "front", (side * 1.0, 0.7, -0.3), "up")


FK.GESTURES.setdefault("s5_film_high", _g_film_high)


def watcher_pose(m, w, t, feed, k):
    """A watcher's face and arms during the cutaway (k: its index, staggers the details)."""
    shut = core.inout_sine(clamp((t - (T_SIL + 0.03 + 0.03 * (k % 2))) / 0.08))   # the mouths SNAP shut
    e = B.expr("surprised")
    uneasy = core.inout_sine(clamp((t - (T_SIL + 0.3)) / 0.4))
    e = e.blend(B.expr(m.mood_after), 0.3 * uneasy)
    e = e.with_(open=0.85 * (1.0 - shut), mouth="o" if shut < 0.5 else "", lid=min(e.lid, 0.04),
                smile=lerp(0.0, -0.35, shut), pupil=0.75)
    glance = core.window(t, T_SIL + 0.3, T_SIL + 0.62, 0.1, 0.12) * w.glance
    look = (w.look[0] + glance, w.look[1] - 0.15 * abs(glance))
    # a frozen stare: no idle blinks -- only the elf's one slow blink of disbelief
    blink = core.window(t, T_SIL + 0.42, T_SIL + 0.72, 0.12, 0.14) if w.i == 1 else 0.0
    pose = ch.crowd_pose("film", t, m.spec, yaw=w.yaw, thumb=feed, mood=e, talk=0.6 * (1.0 - shut), look=look,
                         head_nod=0.04 - 0.06 * shut, blink=blink)
    pose = pose.with_(near=ch.Arm("s5_film_high", hold=pose.crystal))
    if w.cheer:
        # the fist pumping in the air stops dead at the hush ... and sinks
        ph = min(t, T_SIL + 0.05) * 1.7 + m.ph * 0.2
        sink = core.inout_sine(clamp((t - (T_SIL + 0.28)) / 0.55))
        pose = pose.with_(far=ch.Arm("cheer", amt=1.0 - 0.75 * sink, prev="rest", phase=ph))
    return pose


def draw_watchers(cr, t, st, cam, lc):
    """Shot 7: the watchers' faces, the far side of the square soft behind them."""
    feed = make_feed(t)
    off = st["watch_off"]
    soft = st["soft"]
    sc = soft.begin()
    for k, w in enumerate(WATCHERS):
        if w.sharp:
            continue
        m = MEMBER_BY_ID[w.i]
        ox, oy = off[w.i]
        rig = ch.draw_crowd(sc, w.head[0] - ox * w.scale, w.head[1] - oy * w.scale, w.scale, m.spec,
                            watcher_pose(m, w, t, feed, k), L_CROWD, t, 1)
        if "crystal" in rig.points:
            fx.glow(lc, *rig.points["crystal"], 150.0 * w.scale, CYAN, 0.2)
    soft.end(cr, 5.0)
    for k, w in enumerate(WATCHERS):
        if not w.sharp:
            continue
        m = MEMBER_BY_ID[w.i]
        ox, oy = off[w.i]
        rig = ch.draw_crowd(cr, w.head[0] - ox * w.scale, w.head[1] - oy * w.scale, w.scale, m.spec,
                            watcher_pose(m, w, t, feed, k), L_CROWD, t)
        if "crystal" in rig.points:
            cx_, cy_ = rig.points["crystal"]
            fx.glow(lc, cx_, cy_, 170.0 * w.scale, CYAN, 0.24)
            fx.glow(lc, cx_, cy_ + 90.0 * w.scale, 150.0 * w.scale, CYAN, 0.1)    # on the face below it


def watcher_offsets():
    """Each watcher's head offset from its anchor at scale 1 (a dry run): the cutaway places
    the HEADS where the composition wants them."""
    out = {}
    feed = ch.demo_thumb if hasattr(ch, "demo_thumb") else None
    for k, w in enumerate(WATCHERS):
        m = MEMBER_BY_ID[w.i]
        rig = ch.draw_crowd(_SCRATCH_CR, 0.0, 0.0, 1.0, m.spec, watcher_pose(m, w, T_REACT, feed, k), L_CROWD, T_REACT)
        out[w.i] = rig.head
    return out


def pixie_flyoff(t):
    u = core.in_quad(clamp((t - (L1.end + 0.9)) / 1.4))
    return (520.0 * u, -420.0 * u)


def draw_dragon_fg(cr, t, shot, cam, soft=None):
    """The dragon under the arcade (screen space at the shot's base framing), with extra
    parallax for the camera's motion."""
    x, gy, sc, p = DRAGON_AT[set_of(shot)]
    target = soft if soft is not None else cr
    target.save()
    target.transform(residual(base_cam(shot), cam, p))
    rig = ch.draw_dragon(target, x, gy, sc, dragon_pose(t, shot), dragon_light(t), t)
    if shot == 6:
        ch.dragon_smoke(target, t, T_SIGH + 0.25, rig, alpha=0.62)
    target.restore()
    return rig


def post(cr, t, st, bloom=0.55):
    fx.post(cr, t, light=st["light"], bloom_strength=bloom, threshold=0.62, grain=0.042, vignette=0.55,
            vignette_color=(0.02, 0.03, 0.09))


KOBOLD_SKIN = B.Mat.of("#C8643A", sss=0.4)
_SCRATCH_CR = cairo.Context(core.new_surface(4, 4))     # for dry runs (rig positions only)
KOBOLD_SLEEVE = B.Mat.of("#3E4A6A", shadow_k=1.1)
INS_WRIST = (1470.0, 1035.0)                      # the hero crystal's holder: a kobold's claw


def big_feed(t):
    """The insert's crystal: what it 'sees' -- the fight, framed tight and sharp."""
    def fn(c, w, h):
        core.vgrad(c, 0, 0, w, h, ["#5d7c9a", "#2a3a52"])
        c.save()                                     # the scrying light welling up from within
        c.translate(w * 0.5, h * 0.55)
        c.scale(1.0, 1.25)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, w * 0.62)
        g.add_color_stop_rgba(0.0, 0.62, 0.95, 1.0, 0.55)
        g.add_color_stop_rgba(0.55, 0.37, 0.85, 1.0, 0.22)
        g.add_color_stop_rgba(1.0, 0.37, 0.88, 1.0, 0.0)
        c.set_source(g)
        c.paint()
        c.restore()
        sc = 0.3                                     # (the pair low and left of the rec-rune)
        draw_pair(c, w * 0.45 - 15.0 * sc, h * 0.95, sc, t, LS)
        c.save()                                     # a drifting veil of mist over the image
        c.set_operator(cairo.OPERATOR_ADD)
        for k in range(3):
            yy = (h * (0.25 + 0.3 * k) + 18.0 * math.sin(t * 0.9 + 2.1 * k)) % h
            gg = cairo.LinearGradient(0, yy - 26, 0, yy + 26)
            gg.add_color_stop_rgba(0.0, 0.5, 0.9, 1.0, 0.0)
            gg.add_color_stop_rgba(0.5, 0.5, 0.9, 1.0, 0.10)
            gg.add_color_stop_rgba(1.0, 0.5, 0.9, 1.0, 0.0)
            c.set_source(gg)
            c.rectangle(0, yy - 26, w, 52)
            c.fill()
        c.restore()
    return ch.crystal_feed(fn, 200, 280)


def _halo(cr, x, y, r0, r1, sy, color, alpha):
    """An additive elliptical halo that starts at r0 (the edge of what it surrounds, at full
    alpha) and fades out by r1 -- the light round a glowing object, not hidden behind it."""
    c = core.col(color)
    cr.save()
    cr.translate(x, y)
    cr.scale(1.0, sy)
    pat = cairo.RadialGradient(0, 0, r0 * 0.6, 0, 0, r1)
    for off, k in ((0.0, 1.0), (0.22, 0.55), (0.45, 0.22), (0.7, 0.07), (1.0, 0.0)):
        pat.add_color_stop_rgba(off, c[0], c[1], c[2], alpha * k)
    cr.set_operator(cairo.OPERATOR_ADD)
    cr.set_source(pat)
    cr.arc(0, 0, r1, 0, TAU)
    cr.fill()
    cr.restore()


def draw_insert_hand(cr, t):
    """A kobold's clawed hand holds the crystal up, filming: it trembles with excitement and
    jolts when the shoves land. Returns the crystal centre (screen)."""
    e = cheer_energy(t)
    jx = 7.0 * core.noise1(t * 2.7, 3) + 3.0 * math.sin(t * TAU * 3.1) * e
    jy = 6.0 * core.noise1(t * 2.7, 9) + 9.0 * abs(math.sin(t * TAU * 1.6)) * e - 14.0 * impact_pulse(t)
    wx, wy = INS_WRIST[0] + jx, INS_WRIST[1] + jy
    ang = math.pi * 1.06 + 0.03 * core.noise1(t * 1.9, 5)
    lw = B.line_for(B.LINE, 3.2)
    tilt = -0.06 + 0.04 * core.noise1(t * 1.3, 7)
    # a dry run (no image, on a scratch surface) finds the crystal, so its glow can go BEHIND it
    probe = ch.crystal_hold(face=1.0, size=1.62, thumb=None, t=t, tilt=tilt)
    B.hand(_SCRATCH_CR, wx, wy, ang, 300.0, "grip", KOBOLD_SKIN, L_INS, lw, claw="#2E2A26", finger_w=0.9,
           palm_w=0.9, hold=probe, detail=0)
    gx, gy = probe.center_dev if probe.center_dev else (wx, wy - 300)
    pulse = 0.9 + 0.1 * math.sin(t * TAU * 1.2)
    _halo(cr, gx, gy, 170.0, 640.0, 1.35, CYAN, 0.55 * pulse)          # the scrying light round it
    hold = ch.crystal_hold(face=1.0, size=1.62, thumb=big_feed(t), t=t, tilt=tilt)
    B.hand(cr, wx, wy, ang, 300.0, "grip", KOBOLD_SKIN, L_INS, lw, claw="#2E2A26", finger_w=0.9, palm_w=0.9,
           hold=hold)
    # magic: rune motes rising off it, and a glint travelling round the brass collar
    cr.save()
    cr.set_operator(cairo.OPERATOR_ADD)
    for i in range(14):
        life = 1.8 + 0.8 * core.hash01(i, 81)
        u = ((t + core.hash01(i, 82) * life) % life) / life
        side = -1.0 if i % 2 else 1.0
        mx = gx + side * (190.0 + 140.0 * core.hash01(i, 83)) + 14.0 * math.sin(t * 1.7 + i)
        my = gy + 260.0 - u * 560.0
        a_ = 0.75 * math.sin(math.pi * u) * (0.5 + 0.5 * core.hash01(i, 84))
        core.src(cr, "#d8fbff", a_)
        core.circle(cr, mx, my, 2.2 + 2.6 * core.hash01(i, 85) * (1.0 - 0.5 * u))
        cr.fill()
    cr.restore()
    ga = (t * 0.55) % 1.0
    fx.sparkle(cr, gx + 205.0 * math.cos(ga * TAU), gy + 285.0 * math.sin(ga * TAU), 26.0, "#fff4d6",
               0.55 * math.sin(math.pi * ((t * 1.1) % 1.0)), angle=0.3)
    # the sleeve (blue-grey wool) from below the frame, its cuff over the wrist
    d = (math.cos(ang), math.sin(ang))
    cuff = (wx - d[0] * 18.0, wy - d[1] * 18.0)
    pts = [(cuff[0] + 520.0, cuff[1] + 470.0), (cuff[0] + 230.0, cuff[1] + 170.0), cuff]
    shp, so = B.taper_paths(cr, pts, 250.0, 150.0, lw)
    B.shade(cr, shp, KOBOLD_SLEEVE, L_INS, lw, outline=so, size=150.0)
    B.detail_lines(cr, [[(cuff[0] + 30, cuff[1] - 60), (cuff[0] + 10, cuff[1] + 5), (cuff[0] + 32, cuff[1] + 70)]],
                   lw * 0.9, B.palette(L_INS, KOBOLD_SLEEVE).line, 0.6)
    # its cold light falls on the claw
    c = cr.device_to_user(*hold.center_dev) if hold.center_dev else (wx, wy - 300)
    fx.glow(cr, c[0] + 40, c[1] + 330, 260.0, CYAN, 0.16)
    return c


def draw_insert(cr, t, st, cam, lc):
    """Shot 2: one crystal held up, the fight sharp inside it; the real brawl behind, soft."""
    feed = make_feed(t)
    sfeed = scroll_thumb(t)
    glows = []
    draw_items(st["softq"].begin(), world_items(t), t, cam, feed, sfeed, glows=glows, detail=0)
    st["softq"].end(cr, 6.5)
    # a nearer holder's crystal at the left edge: a big out-of-focus glow
    sc2 = st["soft2"].begin()
    ch.draw_scrying_crystal(sc2, 230.0 + 6.0 * core.noise1(t * 2.0, 21), 1010.0 + 5.0 * core.noise1(t * 2.0, 22), 7.5,
                            -0.12, L_INS, face=-1.0, glow=1.0, t=t)
    st["soft2"].end(cr, 16.0)
    c = draw_insert_hand(cr, t)
    with cam.view(lc, 1.0):
        for (x, y, s_, gl) in glows:
            fx.glow(lc, x, y, 190 * s_, CYAN, 0.14 * gl)
    fx.glow(lc, c[0], c[1], 560.0, CYAN, 0.12)
    fx.glow(lc, 200.0, 760.0, 420.0, CYAN, 0.22)


def draw(cr, t, st):
    shot = shot_of(t)
    cam = camera_for(t, shot)
    lc = st["light"].begin()
    glows = []
    st["bake"][set_of(shot)].paint(cr, cam)
    if shot == 2:
        draw_insert(cr, t, st, cam, lc)
        post(cr, t, st, bloom=0.3)
        return
    if shot == 7:
        draw_watchers(cr, t, st, cam, lc)
        post(cr, t, st, bloom=0.5)
        return
    feed = make_feed(t)
    sfeed = scroll_thumb(t)
    soft = st["soft"]
    if shot in (1, 6):
        with cam.view(cr, 1.0):
            st["mist"].draw(cr, t)
    if shot == 3:
        # long lens: only the fighters' plane is sharp; the far side of the ring falls soft
        # (the crystals become bokeh), the near side is soft, dark and backlit
        items = world_items(t)
        far = [it for it in items if it[0] > D0 + 120]
        mid = [it for it in items if D0 - 120 <= it[0] <= D0 + 120]
        near = [it for it in items if it[0] < D0 - 120]
        draw_items(soft.begin(), far, t, cam, feed, sfeed, glows=glows, detail=0)
        soft.end(cr, 2.6)
        draw_items(cr, mid, t, cam, feed, sfeed, glows=glows)
        draw_items(st["softq"].begin(), near, t, cam, feed, sfeed, glows=glows, detail=0)
        st["softq"].end(cr, 6.0)
    elif shot == 4:
        # the pixie's close-up: the square behind her soft, she is staged near the lens
        items = world_items(t, skip_pixie=True)
        draw_items(soft.begin(), items, t, cam, feed, sfeed, glows=glows, dy_front=150.0, detail=0)
        soft.end(cr, 4.0)
        px_, py_, ps_ = PIX_MCU
        dx = 4.0 * core.noise1(t * 0.7, 31)                  # she hangs in the air, drifting a hair
        with _SoftWings(t):
            rig = ch.draw_pixie(cr, px_ + dx, py_, ps_, pixie_mcu_pose(t, feed), L_PIX, t)
        if "crystal" in rig.points:                          # its cold light from below on her face
            cx_, cy_ = rig.points["crystal"]
            fx.glow(lc, cx_, cy_ - 40.0, 520.0, CYAN, 0.10 + 0.22 * core.inout_sine(clamp((t - (L1.end + 0.38)) / 0.4)))
    elif shot == 6:
        # the emptied square: the last walkers far off (their cold glows scattering), the
        # evening sinking in round the two of them, the shaft's shadow under them, the pair
        items = world_items(t, skip_pixie=True, crowd_dt=E_SKIP)
        draw_items(cr, [it for it in items if it[1] == "m"], t, cam, feed, sfeed, glows=glows, crowd_dt=E_SKIP)
        w = warmth(t)
        with cam.view(cr, 1.0):
            st["dusk"].paint(cr, alpha=0.55 + 0.45 * w)
            env.draw_ground_shadow(cr, HUG_SX + 62.0, PGY + 14.0, 150.0, 22.0, alpha=0.3 * w)
        draw_items(cr, [it for it in items if it[1] == "pair"], t, cam, feed, sfeed, glows=glows)
    elif shot == 5:
        # his medium close-up: the square beyond him falls a little soft (depth of field), so
        # he reads first -- the ring turning its back is still clear
        items = world_items(t, skip_pixie=(t > L1.end + 2.4))
        draw_items(soft.begin(), items, t, cam, feed, sfeed, glows=glows, detail=1)
        soft.end(cr, 2.2)
    else:
        items = world_items(t)
        draw_items(cr, items, t, cam, feed, sfeed, glows=glows)
    if shot in (1, 5, 6):
        drig = draw_dragon_fg(cr, t, shot, cam)
        st["arch"][set_of(shot)].paint(cr, cam, 1.5)
        x, gy, sc, p = DRAGON_AT[set_of(shot)]
        hx, hy = residual(base_cam(shot), cam, p).transform_point(*drig.head)
        if shot == 5:
            # his close-up: a soft cold bounce off the square on his face, so he reads first
            fx.glow(lc, hx + 60.0 * sc, hy + 20.0 * sc, 230.0 * sc, "#a9d4ff", 0.12)
        elif shot == 6:
            # the warmth on the two of them reaches him too, faintly, as his face softens
            fx.glow(lc, hx + 50.0 * sc, hy + 10.0 * sc, 200.0 * sc, WARM, 0.07 * warmth(t))
    if shot == 6:
        grace_motes(cr, t, cam)
    ring_light(lc, t, cam, glows)
    post(cr, t, st)


# ----------------------------------------------------------------------------------------
# sound cues (local scene seconds), derived exactly as the animation uses them
# ----------------------------------------------------------------------------------------

def _pan_world(X, D, t):
    cam = camera_for(t, shot_of(t))
    sx, sy, _ = gp(X, D)
    x, _ = cam.to_screen(sx, sy)
    return round(clamp((x - W / 2) / (W / 2), -1.0, 1.0), 2)


def _build_cues():
    cues = []
    pan_pair = lambda tt: _pan_world(PAIR_X, D0, tt)  # noqa: E731
    for k, (ti, pw, who) in enumerate(IMPACTS):
        cues.append((round(ti, 3), "thud_shove", {"gain": round(0.55 + 0.25 * pw, 2), "pan": pan_pair(ti), "size": round(pw, 2)}))
        cues.append((round(ti + 0.06, 3), "laugh_crowd_burst", {"gain": round(0.35 + 0.2 * pw, 2), "pan": 0.0}))
        for j in range(2):                                           # the stumble of the one shoved
            cues.append((round(ti + 0.16 + 0.17 * j, 3), "footstep", {"gain": round(0.35 + 0.1 * pw, 2), "pan": pan_pair(ti)}))
    cues.append((round(T_COCK + 0.12, 3), "cloth_rustle", {"gain": 0.35, "pan": pan_pair(T_STOP)}))        # the punch wound up
    cues.append((round(T_BRACE + 0.16, 3), "cloth_rustle", {"gain": 0.25, "pan": pan_pair(T_STOP)}))       # the flinch
    cues.append((round(T_DROP + 0.22, 3), "cloth_rustle", {"gain": 0.45, "pan": pan_pair(T_STOP)}))        # arms fall
    w0, w1 = T_WALK_IN
    for j in range(3):                                               # his steps in
        cues.append((round(w0 + 0.12 + j * (w1 - w0 - 0.2) / 2.5, 3), "footstep", {"gain": 0.4, "pan": pan_pair(w0)}))
    cues.append((round(T_HUG + 0.45, 3), "hug_rustle", {"gain": 0.6, "pan": pan_pair(T_HUG)}))
    for m in sorted(MEMBERS, key=lambda mm: mm.order):               # the crystals come down
        t0, _ = lower_window(m.order)
        cues.append((round(t0 + 0.1, 3), "crystal_chime", {"gain": round(0.22 - 0.008 * m.order, 3),
                                                           "pan": _pan_world(m.X, m.D, t0)}))
    cues.append((round(T_LOW1 - 0.2, 3), "crystal_chime", {"gain": 0.2, "pan": 0.5}))              # the pixie's
    cues.append((round(T_HUGBACK[0] + 1.0, 3), "cloth_rustle", {"gain": 0.25, "pan": pan_pair(T_HUGBACK[0])}))
    cues.append((round(T_HUGBACK[1] - 0.3, 3), "hug_rustle", {"gain": 0.4, "pan": pan_pair(T_HUGBACK[1])}))
    t_p = T_HUGBACK[1] + 0.6
    while t_p < DUR - 0.5:                                           # the minotaur's slow pats
        cues.append((round(t_p + 0.17, 3), "hug_rustle", {"gain": 0.15, "pan": pan_pair(t_p)}))
        t_p += 4.2
    cues.append((round(T_PIXIE + 0.05, 3), "wing_flutter", {"gain": 0.3, "pan": 0.4}))
    cues.append((round(L1.end + 0.9, 3), "wing_flutter", {"gain": 0.4, "pan": 0.6}))              # she buzzes off
    for m in MEMBERS:                                                # they turn away and walk off
        cues.append((round(m.t_turn, 3), "cloth_rustle", {"gain": 0.18, "pan": _pan_world(m.X, m.D, m.t_turn)}))
        b = CW.BUILDS[m.spec.kind]
        step = b.stride * b.fit * 0.5
        acc = WALK_ACC
        for k in range(1, 40):
            dist = k * step
            d_acc = m.speed * acc / 2.0
            tw = math.sqrt(2 * acc * dist / m.speed) if dist < d_acc else dist / m.speed + acc * 0.5
            tc = m.t_walk + tw                                       # on the crowd's clock
            if tc < T_EMPTY:
                ts = tc
            elif tc >= T_EMPTY + E_SKIP:
                if m.i not in SHOT6_KEEP:
                    break                                            # gone home (the ellipsis)
                ts = tc - E_SKIP                                     # after the ellipsis
            else:
                continue
            if ts > DUR - 0.05:
                break
            X, D, _, _ = member_ground(m, tc)
            sx, sy, _ = gp(X, D)
            x, _ = camera_for(ts, shot_of(ts)).to_screen(sx, sy)
            if not (-60 < x < W + 60):
                continue                                             # out of frame: silent
            cues.append((round(ts, 3), "footstep", {"gain": round(0.12 * clamp(1300.0 / D, 0.4, 1.0), 3),
                                                    "pan": round(clamp((x - W / 2) / (W / 2), -1.0, 1.0), 2)}))
    cues.append((round(T_SIGH, 3), "sigh", {"gain": 0.35, "pan": -0.7}))
    cues.append((round(T_SIGH + 0.25, 3), "smoke_puff", {"gain": 0.2, "pan": -0.7}))
    cues.sort(key=lambda c: c[0])
    return [c for c in cues if 0.0 <= c[0] < DUR]


SFX_CUES = _build_cues()
