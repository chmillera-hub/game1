"""s5_crowd.py -- SCENE 5: THE CROWD  (25.0 s, evening; a corner of the town square)

    "We'll film a fight. But someone gets gentle, and everybody looks away."

EMOTION. Cold voyeurism, then a tenderness nobody can bear to watch. The square is a ring of
cold cyan crystal-light around two brawlers; the light IS the voyeurism (every glow is an eye).
When the orc hugs the minotaur the ring falls silent and the eyes go out one by one. The dragon,
across the street in the dark, is the only one who keeps looking. The last image is the two of
them holding on, alone on the cobbles, the first faint warmth of the film resting on them.

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

SHOTS (cuts are derived from the timeline; times below are for the current timeline.json)
 1  0.00-3.92  MASTER WIDE, across the street, slow dolly-in (zoom x1.07). Framing device: the
               dark stone arch of the arcade the dragon stands under (left pier, the arch ring
               over the top), out of focus. The dragon left, near profile, hands in his coat
               pockets, wings drooped, in the arcade's shadow (a stop darker than the square, a
               cold cyan rim from the crystals). Beyond him the ring: 14 creatures (goblins,
               kobolds, elves, dwarves, two harpies) with crystals raised, cheering; the pixie
               hovers high over them, filming. In the middle the orc (red jerkin) and the minotaur
               (grey hooded tunic) shove each other. Eye trace: the cyan ring (brightest) -> the
               brawl -> back along the dragon's gaze. Two shoves, each with a wind-up (lean back),
               a thrust, an impact and a stagger; at each impact the dragon winces.
 2  3.92-5.36  INSERT: ONE CRYSTAL. A kobold's claw holds a scrying crystal up in the foreground;
               the fight is sharp and small inside it (its red recording rune pulsing), the real
               brawl behind it is soft bokeh -- they watch the screen, not the people. A nearer
               crystal glows out of focus at the left. The hand trembles with excitement. Cut on
               the impact of the orc's next shove.
 3  5.36-13.00 IN THE CIRCLE, long lens (zoom 2.3): only the fighters' plane is sharp; the far
               arc falls soft (crystals turn to bokeh), the near arc is soft, dark and backlit.
               Handheld while they fight (shake on impacts), locked off from the stop. The
               shoving ESCALATES (each faster and harder); the minotaur's 4th is the biggest, the
               orc reels, recovers and winds up the payback -- s5_stop: frozen mid wind-up (a held
               beat; his brows jump: "what am I doing?"), then the arms FALL, the head sinks.
               Eyes down ... eyes up to the minotaur; he walks in. The wary minotaur, guard still
               up, flinches as he comes close (leans back, hands up and out) -- s5_hug: the orc
               wraps his arms round him, face to his chest, eyes shut. The minotaur stands
               frozen, arms out, eyes wide. s5_silence: the cheering mouths close, arms come down,
               bodies freeze. s5_lower: the crystals come down one by one (each glow dimming, the
               cyan pool on the cobbles draining), heads drop, uneasy glances. The minotaur's
               arms hover, hesitate ... and slowly begin to close round the orc.
 4 13.00-15.65 THE PIXIE, medium close-up (her own set-up nearer the lens; the square behind
               her soft). Her crystal sinking, her lip curls, chin up -- "Ew." (head pulled
               back, brows knit) "What is he doing?" (one brow up, head tilted) -- an eye-roll,
               then the crystal back up to her face and she turns to it.
 5 15.65-22.14 THE DRAGON, medium close-up from the arcade (the arch pier and ring frame the
               left and top): he fills the left, the ring and the pair on the right. Thought ->
               glance -> breath -> line: his eyes drop on the thought, 'We'll film a fight.'
               (quiet; eyes back up on 'fight'); three extras already drift off, bored. A breath.
               'But someone gets gentle,' (his brows soften) 'and everybody looks away.' -- on
               the line the whole ring turns its back on the pair, crystals glowing again in
               their faces, and walks off in every direction; the circle dissolves. A small
               sigh, a curl of grey smoke.
 6 22.14-25.00 THE EMPTIED SQUARE (s5_alone): the master's frame again, bookending shot 1 --
               everything changed (an ellipsis: the last walkers are already at the edges, their
               cold glows scattering away). The pair alone in the middle, still holding on,
               rocking a little, the minotaur's chin resting on the orc's head (two slow pats).
               A break in the cloud: one soft warm shaft and a rose-gold pool on them only, motes
               drifting in it, a warm rim on them -- quiet, almost holy. Slow push toward them;
               the dragon stays in the arcade's shadow, his brows softening, wings lifting a
               fraction.

COLOUR / VALUE. Dominant grey-blue (sky #2c3650 -> #b4b8c0, stone #6a7286); the one accent is
the crystals' cyan (#5fe0ff) -- the brightest values in the frame while they are raised, and
they bloom; the orc's red jerkin is the only warm hue until the end. The circle is lit from
inside (a cyan pool on the cobbles, a haze glow above the ring, cyan rims on the brawlers);
when the crystals lower that light drains and the frame goes flat and grey -- then at the end
the pair alone get a little warmth (rose-gold rim, pool, shaft). The dragon sits a stop darker
than the square (the arcade's shadow) so the eye goes past him. Vignette tinted deep blue.

ACTING. Eyes lead, then the head, then the body. Every hold moves (breathing, blinks, sway,
the pixie's buzzing wings, the minotaur's tail). The orc: fury -> a frozen beat -> the anger
drains (brows lift, then fall) -> eyes down -> eyes up to the minotaur -> two steps -> the hug.
The minotaur: fury -> confusion (one brow up, guard still up: a trick?) -> a flinch as the orc
comes close (leans back, hands up and out) -> frozen stiff (arms out, eyes wide) -> hesitation
(hands hovering) -> surrender (hugs back, chin on the orc's head, eyes closed). The crowd:
glee -> confusion -> shock -> silence -> discomfort (they glance at each other) -> they look
away. Lip-sync: the pixie only on s5_l1, the dragon only on s5_l2/s5_l3 (timeline.talk); the
extras' mouths move only while they cheer and are shut from s5_silence on.
"""

import math
import random

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
SHOVES = [("orc", T_STOP - 8.35, 2.30, 0.80),
          ("mino", T_STOP - 6.05, 2.10, 1.00),
          ("orc", T_STOP - 3.95, 1.85, 1.25),
          ("mino", T_STOP - 2.10, 1.75, 1.60),
          ("orc", T_STOP - 0.38, 1.60, 1.80)]
IMPACT_U = 0.42                                   # cycle fraction where the hands land


def _impact_t(i):
    who, t0, per, pw = SHOVES[i]
    return t0 + IMPACT_U * per


IMPACTS = [(_impact_t(i), SHOVES[i][3], SHOVES[i][0]) for i in range(4)]
T_HUGBACK = (T_HUG + 1.4, T_HUG + 4.0)            # the minotaur's slow, hesitant hug back
T_WALK_IN = (T_STOP + 0.6, T_HUG + 0.12)          # the orc's steps into the hug

# shot boundaries
T_INS = IMPACTS[1][0] + 0.55                      # the insert: one crystal, the fight inside it
T_CIRCLE = IMPACTS[2][0]                          # cut on the impact of the orc's 2nd shove
T_PIXIE = min(T_LOW1, L1.start - 0.4)             # the pixie, just before "Ew."
T_DRAGON = L2.start - 0.65                        # the dragon, a breath before his line
T_EMPTY = T_ALONE                                 # the emptied square
T_GENTLE = _word("s5_l3", 3, L3.start + 0.94)     # "gentle,"
T_EVERY = _word("s5_l3", 5, L3.start + 1.68)      # "everybody"
T_SIGH = T_ALONE + 0.75                           # in the emptied square: he sighs, watching them
E_SKIP = 4.2                                      # the cut to shot 6 skips this much of the dispersal

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
WARM = "#ffbf8a"
WARM_POOL = "#ffa860"
WARM_SHAFT = "#ffd2a0"

# ----------------------------------------------------------------------------------------
# the fight -> the hug (a local, escalating take on characters.draw_brawl)
# ----------------------------------------------------------------------------------------

GAP = 262.0                                       # anchors apart while they square up (body px)
ORC_BASE, MINO_BASE = -GAP * 0.45, GAP * 0.55
HUG_DIST = 94.0
YAW_FIGHT = 1.2                                   # nearly side-on: chests and palms read across the gap
YAW_HUG = 1.0                                     # 3/4 in the hug: both faces open to the lens
_BUILD = {"orc": ORC.ORC_BUILD, "mino": MN.MINOTAUR_BUILD}
ORC_SHOVE_Y = 188.0                               # the orc's palms: this far above his pelvis


def _stride(who, yaw):
    """Anchor travel (body px) per walk cycle at this yaw (so the planted feet do not slide)."""
    b = _BUILD[who]
    return b.stride * abs(math.sin(yaw)) * b.fit


# scene-local gestures, registered under s5_* names in the orc's and the minotaur's gesture
# tables (new keys only: the library's own gestures are untouched)

def _g_square(q, sk, side, arm):
    """Squared up for a shoving match: chest out, fists low and a little wide, elbows back --
    the chest stays open (no boxing guard for the palms to land on)."""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.20 * AL, 0.80 * AL, 0.04 * AL)), "fist", 0.2, "auto",
                (side * 1.0, -0.1, -0.8), "fwd")


def _g_shove(q, sk, side, arm):
    """A two-handed chest shove from the squared stance: phase 0..0.35 the hands come up to the
    chest (elbows cocked back), 0.35..0.55 they shoot out flat into the other's chest (aimed by
    pose.shove_y), 0.55..1 back down to the stance."""
    AL = FK._AL(q)
    ph = arm.phase
    sq = _g_square(q, sk, side, arm).target
    back = B.v_add(sk, (-side * 0.02 * AL, 0.40 * AL, 0.02 * AL))
    out = B.v_add(sk, (-side * 0.10 * AL, 0.22 * AL, 0.98 * AL))
    sy = getattr(q.pose, "shove_y", None)
    if sy is None and q.b is ORC.ORC_BUILD:
        sy = ORC_SHOVE_Y                          # the orc reaches UP to the minotaur's chest
    if sy is not None:
        y = q.S["pelvis"][1] - sy
        dy = y - out[1]
        out = (out[0], y, out[2] - 0.25 * max(0.0, dy))
        back = (back[0], back[1] + 0.5 * dy, back[2])
    if ph < 0.35:
        p = B.v_lerp(sq, back, core.inout_sine(ph / 0.35))
    elif ph < 0.55:
        p = B.v_lerp(back, out, core.out_cubic((ph - 0.35) / 0.2))
    else:
        p = B.v_lerp(out, sq, core.inout_sine((ph - 0.55) / 0.45))
    k = core.inout_sine(clamp((ph - 0.04) / 0.24)) * (1.0 - core.inout_sine(clamp((ph - 0.62) / 0.3)))
    return FK.G(p, "flat" if k > 0.5 else "fist", lerp(0.2, -1.25, k), "auto", (side * 0.7, 1.0, -0.6),
                "in" if k > 0.5 else "fwd")


def _g_whoa(q, sk, side, arm):
    """Hands up and open in front of the chest, palms out: 'whoa -- what are you doing?'"""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.02 * AL, 0.30 * AL, 0.46 * AL)), "open", -1.15, "auto",
                (side * 0.8, 1.0, -0.5), "in")


def _g_aside(q, sk, side, arm):
    """An arm let down on the outside, away from the partner (the minotaur's hesitation:
    his near hand comes down at his side before it dares go round the orc)."""
    AL = FK._AL(q)
    return FK.G(B.v_add(sk, (side * 0.30 * AL, 0.80 * AL, -0.32 * AL)), "relaxed", 0.1, "auto",
                (side * 0.8, 0.2, -1.0), "fwd")


for _tbl in (ORC.ORC_GESTURES, MN.MINOTAUR_GESTURES):
    _tbl.setdefault("s5_aside", _g_aside)
    _tbl.setdefault("s5_square", _g_square)
    _tbl.setdefault("s5_shove", _g_shove)
    _tbl.setdefault("s5_whoa", _g_whoa)


def _shove_shape(u):
    """One shove cycle u 0..1 -> (arm phase, the target's recoil, the shover's step, the
    shover's lean). Anticipation: he draws back (leans and shifts back) during the wind-up,
    then steps in with the thrust; the hands land at IMPACT_U and the other reels back."""
    shove = clamp(u / 0.75)
    back = math.sin(math.pi * clamp(u / 0.30)) if u < 0.30 else 0.0
    step = core.out_cubic(clamp((u - 0.25) / 0.17)) * (1.0 - core.inout_sine(clamp((u - 0.6) / 0.4)))
    recoil = core.out_cubic(clamp((u - IMPACT_U) / 0.2)) * (1.0 - core.inout_sine(clamp((u - 0.64) / 0.36)))
    return shove, recoil, step - 0.45 * back, 0.5 * step - 0.3 * back


def _fight_state(t):
    """While they fight: positions (body px from the fight centre), who shoves, who staggers."""
    ox, mx = ORC_BASE, MINO_BASE
    st = {"orc_shove": None, "mino_shove": None, "orc_stagger": 0.0, "mino_stagger": 0.0,
          "orc_pow": 1.0, "mino_pow": 1.0, "orc_lean": 0.0, "mino_lean": 0.0, "phase": 0.0, "impact": 0.0,
          "power": 0.0}
    for who, t0, per, pw in SHOVES:
        if not (t0 <= t < t0 + per):
            continue
        u = (t - t0) / per
        shove, recoil, stepin, lean = _shove_shape(u)
        if who == "orc":
            ox += 46.0 * pw * stepin
            mx += 60.0 * pw * recoil
            st["orc_shove"], st["orc_pow"], st["orc_lean"] = shove, pw, lean
            st["mino_stagger"] = max(st["mino_stagger"], recoil)
            st["mino_pow"] = pw
        else:
            mx -= 46.0 * pw * stepin
            ox -= 60.0 * pw * recoil
            st["mino_shove"], st["mino_pow"], st["mino_lean"] = shove, pw, lean
            st["orc_stagger"] = max(st["orc_stagger"], recoil)
            st["orc_pow"] = pw
        st["phase"] = u
        st["impact"] = max(st["impact"], clamp(1.0 - abs(u - IMPACT_U) / 0.08))
        st["power"] = pw
    st["orc_x"], st["mino_x"] = ox, mx
    return st


_STOP_STATE = _fight_state(T_STOP - 1e-4)
ORC_STOP_X = _STOP_STATE["orc_x"]
STOP_PHASE = _STOP_STATE["orc_shove"] if _STOP_STATE["orc_shove"] is not None else 0.3
ORC_REST_X = ORC_STOP_X - 10.0                    # he sags back a little as his arms drop
MINO_HUG_X = MINO_BASE - 18.0                     # the puzzled minotaur half-steps in: "what?"
ORC_HUG_X = MINO_HUG_X - HUG_DIST
T_BRACE = SHOVES[4][1] + 0.12                     # the minotaur sees the payback coming


def _xs(t):
    """(orc x, minotaur x): anchor offsets from the fight centre (body px) at time t."""
    if t < T_STOP:
        st = _fight_state(t)
        return st["orc_x"], st["mino_x"]
    sag = core.inout_sine(clamp((t - T_STOP - 0.3) / 0.35))
    walk_u = core.inout_sine(clamp((t - T_WALK_IN[0]) / (T_WALK_IN[1] - T_WALK_IN[0])))
    ox = lerp(lerp(ORC_STOP_X, ORC_REST_X, sag), ORC_HUG_X, walk_u)
    bump = 6.0 * math.sin(math.pi * clamp((t - T_HUG - 0.1) / 0.6))       # rocked back a hair
    half = core.inout_sine(clamp((t - T_STOP - 0.4) / 0.5))              # the minotaur's half-step
    return ox, lerp(MINO_BASE, MINO_HUG_X, half) + bump


def _impact_pulse_for(t, who, tau=0.3):
    """0..1 pulse after an impact that lands ON `who` (the face flash, the head whip)."""
    v = 0.0
    for ti, pw, shover in IMPACTS:
        if shover != who and t >= ti:
            dt = t - ti
            v = max(v, min(1.0, pw) * clamp(dt / 0.05) * math.exp(-dt / tau))
    return v


def pair_state(t):
    h = 1.0 / 48.0
    ox, mx = _xs(t)
    o0, m0 = _xs(t - h)
    o1, m1 = _xs(t + h)
    vo, vm = (o1 - o0) / (2 * h), (m1 - m0) / (2 * h)
    if t < T_STOP:
        st = _fight_state(t)
        st.update(fight=True, stop=0.0, hug=0.0, hug_back=0.0)
        oyaw, myaw = YAW_FIGHT, YAW_FIGHT
    else:
        st = {"fight": False, "orc_shove": None, "mino_shove": None, "orc_stagger": 0.0, "mino_stagger": 0.0,
              "impact": 0.0, "phase": 0.0, "power": 0.0}
        st["stop"] = core.inout_sine(clamp((t - T_STOP) / 0.5))
        walk_u = core.inout_sine(clamp((t - T_WALK_IN[0]) / (T_WALK_IN[1] - T_WALK_IN[0])))
        st["walk_u"] = walk_u
        st["hug"] = core.inout_sine(clamp((t - (T_HUG - 0.3)) / 0.45))
        st["hug_close"] = core.inout_sine(clamp((t - T_HUG) / 0.7))
        oyaw = lerp(YAW_FIGHT, YAW_HUG, walk_u)
        myaw = lerp(YAW_FIGHT, YAW_HUG, core.inout_sine(clamp((t - T_HUG) / 0.6)))
    st["orc_x"], st["mino_x"] = ox, mx
    st["orc_yaw"], st["mino_yaw"] = oyaw, myaw
    # stepping: the feet follow the anchor (phase from the displacement, so nothing slides)
    st["orc_walk"] = clamp(abs(vo) / 70.0)
    st["mino_walk"] = clamp(abs(vm) / 70.0)
    st["orc_phase"] = (ox - ORC_BASE) / _stride("orc", oyaw)
    st["mino_phase"] = -(mx - MINO_BASE) / _stride("mino", myaw)
    return st


def _expr(*pairs):
    """Blend moods: _expr(("angry", 1), ("sad", u), ...) -> an Expr (sequential blends)."""
    e = B.expr(pairs[0][0])
    for m, u in pairs[1:]:
        if u > 0:
            e = e.blend(B.expr(m), clamp(u))
    return e


def orc_pose(t, st, sgn=1.0):
    walk, phase = st["orc_walk"], st["orc_phase"]
    if st["fight"]:
        hit = _impact_pulse_for(t, "orc")
        whip = _impact_pulse_for(t, "orc", 0.16)
        if st["orc_shove"] is not None:
            arm = ch.Arm("s5_shove", phase=st["orc_shove"])
            lean = st["orc_lean"] * (0.8 + 0.2 * st["orc_pow"])
        elif st["orc_stagger"] > 0.02:
            arm = ch.Arm("stagger", amt=clamp(st["orc_stagger"] * 2.0), prev="s5_square", phase=st["phase"])
            lean = -0.5 * st["orc_stagger"] * min(1.5, st["orc_pow"])
        else:
            arm = ch.Arm("s5_square")
            lean = 0.0
        thrust = st["orc_shove"] is not None and 0.3 < st["orc_shove"] < 0.75
        e = _expr(("angry", 1.0), ("surprised", 0.75 * hit))
        return ORC.OrcPose(yaw=sgn * st["orc_yaw"], mood=e, snarl=0.45 + 0.45 * thrust - 0.4 * hit, stance=0.5 * sgn,
                           hunch=0.62, lean=lean, head_nod=0.5 * whip - 0.08 * thrust, look=(0.0, -0.1),
                           walk=walk, phase=phase, near=arm, far=arm, seed=3)
    ts = t - T_STOP
    frozen = _STOP_STATE
    lean0 = frozen["orc_lean"] * (0.8 + 0.2 * frozen["orc_pow"])
    drop = core.in_quad(clamp((ts - 0.30) / 0.30))                 # a frozen beat, then the arms FALL
    arms = ch.Arm("slump", amt=drop, prev="s5_shove", phase=STOP_PHASE)
    hug = st["hug"]
    if hug > 0.0:
        arms = ch.Arm("hug", amt=hug, prev="slump", phase=1.0 - st["hug_close"])
    realise = core.window(ts, 0.04, 0.62, 0.1, 0.3)                # brows jump: "what am I doing?"
    sad = core.inout_sine(clamp((ts - 0.3) / 0.4))
    tender = st["hug_close"]
    e = _expr(("angry", 1.0), ("raised", realise), ("sad", sad), ("kind", tender))
    look_down = core.inout_sine(clamp((ts - 0.34) / 0.2))
    look_up = core.inout_sine(clamp((ts - 0.58) / 0.18))          # eyes down ... then up at him: go
    look_y = (0.55 * look_down * (1.0 - look_up) - 0.12 * look_up) * (1.0 - tender) + 0.3 * tender
    nod = (-0.32 * look_down * (1.0 - 0.7 * lagged_u(t, ts, 0.58))) * (1.0 - tender) - 0.12 * tender
    return ORC.OrcPose(yaw=sgn * st["orc_yaw"], mood=e, snarl=0.8 * (1.0 - core.inout_sine(clamp((ts - 0.3) / 0.35))),
                       stance=0.5 * sgn * (1.0 - st["stop"]),
                       hunch=lerp(0.62, 0.9, core.inout_sine(clamp((ts - 0.3) / 0.35))) - 0.15 * hug,
                       lean=lean0 * (1.0 - core.inout_sine(clamp((ts - 0.3) / 0.4))) + 0.08 * st["walk_u"] * (1 - hug)
                       + 0.34 * hug,
                       head_tilt=0.22 * tender * sgn, head_turn=-0.3 * tender * sgn, head_nod=nod,
                       look=(0.0, look_y), blink=clamp((tender - 0.4) * 2.5) if tender > 0.4 else None,
                       walk=walk, phase=phase, near=arms, far=arms, seed=3,
                       hug_reach=(st["mino_x"] - st["orc_x"]) / math.sin(abs(st["orc_yaw"])),
                       hug_w=74.0, hug_d=52.0, hug_y=112.0)


def lagged_u(t, ts, t0, dur=0.18):
    """The head following the eyes a beat later (ease from t0 + lag)."""
    return core.inout_sine(clamp((ts - t0 - 0.08) / dur))


def mino_pose(t, st, sgn=1.0):
    walk, phase = st["mino_walk"], st["mino_phase"]
    if st["fight"]:
        hit = _impact_pulse_for(t, "mino")
        whip = _impact_pulse_for(t, "mino", 0.16)
        brace = core.inout_sine(clamp((t - T_BRACE) / 0.22))         # the payback coming: he flinches
        if st["mino_shove"] is not None:
            arm = ch.Arm("s5_shove", phase=st["mino_shove"])
            lean = st["mino_lean"] * (0.8 + 0.2 * st["mino_pow"])
        elif st["mino_stagger"] > 0.02:
            arm = ch.Arm("stagger", amt=clamp(st["mino_stagger"] * 2.0), prev="s5_square", phase=st["phase"])
            lean = -0.5 * st["mino_stagger"] * min(1.5, st["mino_pow"])
        else:
            arm = ch.Arm("guard", amt=brace, prev="s5_square") if brace > 0 else ch.Arm("s5_square")
            lean = -0.08 * brace
        thrust = st["mino_shove"] is not None and 0.3 < st["mino_shove"] < 0.75
        e = _expr(("angry", 1.0), ("surprised", 0.75 * hit), ("worried", 0.45 * brace))
        e = e.with_(lid_bot=max(e.lid_bot, 0.4 * brace))
        return MN.MinotaurPose(yaw=-sgn * st["mino_yaw"], mood=e, stance=0.5 * -sgn, hunch=0.55 + 0.25 * brace,
                               lean=lean, head_nod=0.5 * whip - 0.08 * thrust - 0.22 * brace, look=(0.0, 0.1),
                               walk=walk, phase=phase, near=arm, far=arm, seed=5, shove_y=62.0,
                               tail_swing=0.6 * math.sin(t * 2.3) + 0.5 * whip)
    ts = t - T_STOP
    # brace -> the guard comes down (what?) -> wary as he walks in (whoa) -> the hug: stunned,
    # arms up and out, head back -> frozen -> eyes dart, then down at him -> hands hover ->
    # they settle on his back, head bows, eyes close
    unbrace = core.inout_sine(clamp((ts - 0.25) / 0.6))
    whoa = core.inout_sine(clamp((t - (T_WALK_IN[0] + 0.15)) / 0.35))
    stun = core.inout_sine(clamp((t - (T_HUG - 0.05)) / 0.32))
    tb = T_HUGBACK[0]
    hover = core.inout_sine(clamp((t - tb) / 0.9))                  # far arm: over his shoulder
    close = core.inout_sine(clamp((t - (tb + 0.85)) / 1.1))
    drop_n = core.inout_sine(clamp((t - (tb + 0.1)) / 0.55))        # near arm: down to his side first,
    hover_n = core.inout_sine(clamp((t - (tb + 0.6)) / 0.7))        # then round the orc's waist
    close_n = core.inout_sine(clamp((t - (tb + 1.15)) / 1.0))
    settle = core.inout_sine(clamp((t - (tb + 1.7)) / 0.9))
    arms = ch.Arm("s5_square", amt=unbrace, prev="guard")
    if whoa > 0.0:
        arms = ch.Arm("s5_whoa", amt=whoa, prev="s5_square")
    if stun > 0.0:
        arms = ch.Arm("surprised", amt=stun, prev="s5_whoa")
    near = far = arms
    if hover > 0.0:
        far = ch.Arm("hug", amt=hover, prev="surprised", phase=lerp(1.0, 0.18, close) * (1.0 - settle))
    if drop_n > 0.0:
        near = ch.Arm("s5_aside", amt=drop_n, prev="surprised")
    if hover_n > 0.0:
        u = (t - T_HUGBACK[1] - 0.6) % 4.2 if t > T_HUGBACK[1] + 0.6 else 9.0
        pat = 0.14 * math.sin(math.pi * u / 0.34) ** 2 if u < 0.68 else 0.0    # slow pats on his back
        near = ch.Arm("hug", amt=hover_n, prev="s5_aside", phase=lerp(1.0, 0.18, close_n) * (1.0 - settle) + pat)
    confused = core.window(ts, 0.35, T_WALK_IN[0] - T_STOP + 0.3, 0.3, 0.25)
    # frozen: his eyes dart to the crowd, then come down to the orc
    dart = core.track(t, [(T_HUG + 0.5, 0.0), (T_HUG + 0.68, -0.55, "inout_sine"), (T_HUG + 0.92, -0.55),
                          (T_HUG + 1.1, 0.5, "inout_sine"), (T_HUG + 1.3, 0.5), (T_HUGBACK[0] + 0.05, 0.0, "inout_sine")])
    down = core.inout_sine(clamp((t - (T_HUGBACK[0] - 0.15)) / 0.4))
    tender = close
    e = _expr(("angry", 1.0 - unbrace), ("skeptical", confused), ("worried", whoa * (1.0 - stun)),
              ("surprised", stun * (1.0 - 0.7 * down)), ("worried", 0.6 * down * (1.0 - tender)), ("kind", tender))
    e = e.with_(open=e.open * (1.0 - down))
    yaw = -sgn * (st["mino_yaw"] - 0.3 * settle)
    return MN.MinotaurPose(yaw=yaw, mood=e,
                           lean=-0.12 * whoa * (1 - stun) - 0.1 * stun * (1.0 - hover) + 0.05 * close,
                           hunch=0.55 - 0.15 * stun * (1.0 - hover) + 0.4 * close,
                           head_nod=0.22 * stun * (1.0 - hover) - 0.18 * down * (1.0 - close) - 0.5 * close + 0.06 * whoa,
                           head_tilt=(-0.22 * close + 0.12 * confused) * sgn,
                           head_turn=(0.5 * close) * sgn,
                           look=(dart * (1.0 - down), 0.1 + 0.45 * down * (1.0 - close)),
                           near=near, far=far, seed=5, stance=0.5 * -sgn * (1 - st["stop"]),
                           blink=clamp((close - 0.75) * 4.0) if close > 0.75 else None,
                           walk=walk, phase=phase,
                           hug_reach=(st["mino_x"] - st["orc_x"]) / math.sin(abs(st["mino_yaw"])),
                           hug_w=66.0, hug_d=46.0, hug_y=-6.0, hug_y_far=78.0,
                           tail_swing=lerp(0.6 * math.sin(t * 2.3), 0.25 * math.sin(t * 0.9), st["stop"]))


def draw_pair(cr, cx, gy, sc, t, light_orc, light_mino=None, detail=None):
    """The orc and the minotaur at anchor (cx, gy) (the fight centre), z-correct (the hug
    interleaves their layers like characters.draw_brawl). Returns (orc_rig, mino_rig)."""
    st = pair_state(t)
    lm = light_mino or light_orc
    op, mp = orc_pose(t, st), mino_pose(t, st)
    hug = st.get("hug", 0.0)
    rock = 3.5 * hug * math.sin((t - T_HUG) * TAU * 0.21) if not st["fight"] else 0.0
    ox, mx = cx + (st["orc_x"] + rock) * sc, cx + (st["mino_x"] + rock) * sc
    if st["fight"] or hug <= 0.05:
        m_rig = MN.draw_minotaur(cr, mx, gy, sc, mp, lm, t, detail)
        o_rig = ORC.draw_orc(cr, ox, gy + 1.0, sc, op, light_orc, t, detail)
        return o_rig, m_rig
    # interleaved: both back arms, the minotaur's body, the orc (his face on the minotaur's chest,
    # arms round his waist), then the minotaur's head -- bowed, his chin comes to rest on the
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
        self.t_walk = self.t_turn + 0.45
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
    Member(0, 22, "harpy", 517, 1.0, 6, 0.8, "sneer", (_W + 0.55, 0.8, 0.6, 1.15)),
    Member(1, 47, "elf", 503, 1.0, 2, 0.35, "skeptical", (_W + 0.3, 0.45, 0.9, 1.1), hat="hood"),
    Member(2, 72, "dwarf", 541, 1.0, 0, 0.9, "worried", (_W + 1.35, 0.15, 1.0, 1.3)),
    Member(3, 101, "goblin", 524, 1.0, 1, 1.0, "sneer", (_W + 0.95, -0.3, 1.0, 1.35), laugh=True),
    Member(4, 127, "elf", 512, 1.0, 4, 0.35, "bored", (_E1, -0.2, 1.0, 1.15), cloth="#5A4A6E"),
    Member(5, 155, "kobold", 533, 1.0, 9, 0.9, "worried", (_W + 1.55, -0.5, 0.85, 1.4)),
    Member(14, 160, "elf", 561, 1.2, 5, 0.3, "skeptical", (_W + 0.45, -0.1, 1.0, 1.1)),
    # the sides
    Member(6, 0, "goblin", 545, 1.0, 7, 0.9, "skeptical", (_E1 + 1.25, 1.0, 0.3, 1.45), hat="cap"),
    Member(7, 180, "dwarf", 529, 1.0, 8, 0.8, "sad", (_W + 1.15, -0.35, 1.0, 1.3)),
    # front arc: backs to us, crystals showing the fight; the middle stays open
    Member(8, -22, "elf", 507, 1.0, 3, 0.3, "skeptical", (_E1 + 0.65, 1.0, 0.2, 1.25)),
    Member(9, -47, "dwarf", 522, 1.0, 10, 0.9, "worried", (_W + 1.95, 1.0, 0.15, 1.35)),
    Member(10, -128, "goblin", 536, 1.0, 11, 1.0, "sneer", (_W + 1.65, -0.12, 1.0, 1.35), laugh=True),
    Member(11, -153, "kobold", 548, 1.06, 12, 1.0, "bored", (_W + 0.75, 0.05, 1.0, 1.4)),
    Member(13, 141, "harpy", 538, 1.24, 13, 0.7, "sneer", (_W + 0.85, -0.45, 0.9, 1.15)),
]
N_LOWER = 15                                      # 14 crystals + the pixie's (last)


def lower_window(order):
    span = (T_LOW1 - 0.8) - T_LOW0
    t0 = T_LOW0 + span * order / (N_LOWER - 1)
    return t0, t0 + 0.8


def lower_amount(m, t):
    t0, t1 = lower_window(m.order)
    return core.inout_sine(clamp((t - t0) / (t1 - t0)))


def member_ground(m, t):
    """Where member m stands at t: (X, D, walking 0..1, distance walked)."""
    if t <= m.t_walk:
        return m.X, m.D, 0.0, 0.0
    tw = t - m.t_walk
    acc = 0.5
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
    return base


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
        return ch.DragonPose(facing=1, turn=0.55, near=ch.Arm("pockets"), far=ch.Arm("pockets"), mood=e,
                             look=(0.55, 0.05), wings=-0.85, hunch=0.6, head_nod=-0.05 - 0.05 * wince, blink=blink,
                             tail_curl=0.5, seed=1)
    if shot == 5:
        think = core.window(t, T_DRAGON + 0.3, L2.start + 0.2, 0.15, 0.25)
        on_fight = core.window(t, _word("s5_l2", 3, L2.start + 0.74) - 0.1, L2.end + 0.6, 0.15, 0.5)
        breath = core.window(t, L3.start - 0.5, L3.start + 0.1, 0.25, 0.25)
        soft = core.window(t, T_GENTLE - 0.1, L3.end + 0.6, 0.3, 0.6)
        track = core.window(t, T_EVERY - 0.2, L3.end + 0.2, 0.3, 0.5)
        e = _expr(("lonely", 1.0), ("sad", 0.35 + 0.25 * on_fight), ("kind", 0.45 * soft))
        look = (0.55 - 0.15 * think + 0.18 * track, 0.05 + 0.4 * think - 0.05 * on_fight + 0.12 * track)
        blink = None
        if T_DRAGON + 0.05 < t < T_DRAGON + 0.25:
            blink = core.window(t, T_DRAGON + 0.05, T_DRAGON + 0.25, 0.08, 0.1)
        return ch.DragonPose(facing=1, turn=0.3, near=ch.Arm("pockets"), far=ch.Arm("pockets"), mood=e,
                             look=look, wings=-0.85, hunch=0.62 - 0.06 * breath, lean=-0.04 * breath,
                             head_nod=-0.12 - 0.12 * think + 0.06 * breath, head_turn=0.05 * track,
                             talk=talk, blink=blink, tail_curl=0.5, seed=1)
    # shot 6: the emptied square -- he keeps looking; a sigh of longing (a little grey smoke),
    # then his brows soften and his wings lift a fraction: the warmth reaches him too
    sigh = core.window(t, T_SIGH, T_SIGH + 1.3, 0.35, 0.7)
    soften = core.inout_sine(clamp((t - (T_SIGH + 0.9)) / 1.4))
    e = _expr(("lonely", 1.0), ("sigh", 0.55 * sigh), ("kind", 0.4 * soften))
    return ch.DragonPose(facing=1, turn=0.55, near=ch.Arm("pockets"), far=ch.Arm("pockets"), mood=e,
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
CAM_C = cam_at(HUG_SX, 640.0, 600.0, 560.0, 1.0)
CAM_D0 = cam_at(HUG_SX, 640.0, 1440.0, 560.0, 1.1)
CAM_E0 = CAM_A0                                   # the bookend: the master's first framing ...
CAM_E1 = zoom_cam(CAM_A0, 1205.0, 660.0, 1.07)    # ... and a slow push toward the pair

# the dragon and the arch, placed per framing in SCREEN space (at the set-up's base camera)
DRAGON_AT = {1: (292.0, 1238.0, 1.30, 1.3), 5: (468.0, 1420.0, 2.12, 1.2)}
ARCH_AT = {1: (150.0, 395.0, (1180.0, -190.0)), 5: (40.0, 300.0, (1250.0, -330.0))}

# shots: 1 master, 2 insert (the crystal), 3 the circle, 4 the pixie, 5 the dragon, 6 the
# emptied square (the master's set-up again)
SHOT_STARTS = ((0.0, 1), (T_INS, 2), (T_CIRCLE, 3), (T_PIXIE, 4), (T_DRAGON, 5), (T_EMPTY, 6))


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
        settle = clamp((t - T_STOP) / 0.6)
        return CAM_B.shake(t, amp=2.0 * (1.0 - settle), freq=2.4, seed=11)
    if shot == 4:
        return CAM_C.drift(t, amp=3.0, freq=0.2, seed=4)
    if shot == 5:
        return cam_d(t)
    u = core.inout_sine(clamp((t - T_EMPTY) / (DUR - T_EMPTY)))
    return core.Camera.lerp(CAM_E0, CAM_E1, u)


def set_of(shot):
    """Which baked set-up a shot uses (the emptied square is the master's)."""
    return 1 if shot == 6 else shot


def base_cam(shot):
    return {1: CAM_A0, 2: CAM_I, 3: CAM_B, 4: CAM_C, 5: CAM_D0, 6: CAM_A0}[shot]


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
    return core.inout_sine(clamp((t - (T_EMPTY + 0.15)) / 2.0)) if t >= T_EMPTY else 0.0


def pair_light(t):
    g = crystal_level(t)
    cold = LS.with_(exposure=1.06, rim=(0.55, 0.92, 1.0), rim_strength=0.4 + 0.45 * g, name="s5_pair")
    warm = B.Light(key=(1.06, 0.98, 0.93), ambient=(0.48, 0.47, 0.6), rim=(1.0, 0.82, 0.64), rim_strength=0.8,
                   direction=(-0.35, -0.94), exposure=1.04, name="s5_grace")
    w = _q(warmth(t), 24)
    return B.Light.lerp(cold, warm, 0.9 * w) if w > 0 else cold


def grace_motes(cr, t, cam):
    """Motes drifting in the warm shaft over the pair (the end)."""
    w = warmth(t)
    if w <= 0.02:
        return
    px, py, _, _ = circle3((HUG_SX - CX0) / PSC, D0, 430.0, 0.0)
    x0, y0, x1, y1 = px - 300, -260.0, px + 5, py - 10

    def mask(x, y):
        u = clamp((y - y0) / (y1 - y0))
        cx_ = lerp(x0, x1, u)
        half = lerp(60.0, 150.0, u)
        return w * clamp(1.0 - abs(x - cx_) / half) * clamp(u * 3.0) * clamp((1.0 - u) * 4.0 + 0.2)

    with cam.view(cr, 1.0):
        fx.dust(cr, t, (px - 460, -100, 560, py - 20), n=70, color="#ffe2b8", alpha=0.55, size=(1.0, 2.4),
                seed=7, drift=(5.0, 7.0), twinkle=0.5, mask=mask)


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
        w = warmth(t)
        if w > 0:
            px, py, prx, pry = circle3((HUG_SX - CX0) / PSC, D0, 430.0, 0.0)
            fx.light_pool(lc, px, py, prx, pry * 1.2, WARM_POOL, 0.36 * w)
            fx.light_pool(lc, px, py, prx * 0.45, pry * 0.5, WARM, 0.22 * w)
            hy = py - 400.0 * PSC                     # their heads and shoulders catch it most
            fx.glow(lc, px - 10, hy, 190, WARM_SHAFT, 0.20 * w)
            # a break in the cloud: one soft shaft falling on them only
            fx.light_shaft(lc, px - 300, -260, px + 5, py - 10, 100, 250, WARM_SHAFT, 0.34 * w, soft=5,
                           fade_start=0.2, fade_end=0.3)
            fx.glow(lc, px - 300, -120, 420, WARM_SHAFT, 0.10 * w)


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
    st["mist"] = env.Mist(-700, HOUSE_GY - 140, 3400, 260, PAL["haze"], 0.14, seed=3, speed=10)
    return st


# ----------------------------------------------------------------------------------------
# drawing
# ----------------------------------------------------------------------------------------

def world_items(t, skip_pixie=False, crowd_dt=0.0):
    """Everything that moves in the square, far to near: [(D, kind, member)]."""
    items = []
    tc = t + crowd_dt
    for m in MEMBERS:
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
KOBOLD_SLEEVE = B.Mat.of("#3E4A6A", shadow_k=1.1)
INS_WRIST = (1470.0, 1035.0)                      # the hero crystal's holder: a kobold's claw


def big_feed(t):
    """The insert's crystal: what it 'sees' -- the fight, framed tight and sharp."""
    def fn(c, w, h):
        core.vgrad(c, 0, 0, w, h, ["#3d4e68", "#1c2534"])
        c.save()
        c.translate(w / 2, h * 0.9)
        c.scale(1.0, 0.28)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, w * 0.6)
        g.add_color_stop_rgba(0.0, 0.37, 0.88, 1.0, 0.35)
        g.add_color_stop_rgba(1.0, 0.37, 0.88, 1.0, 0.0)
        c.set_source(g)
        c.paint()
        c.restore()
        sc = 0.3                                     # (the pair low and left of the rec-rune)
        draw_pair(c, w * 0.45 - 15.0 * sc, h * 0.95, sc, t, LS)
    return ch.crystal_feed(fn, 200, 280)


def draw_insert_hand(cr, t):
    """A kobold's clawed hand holds the crystal up, filming: it trembles with excitement and
    jolts when the shoves land. Returns the crystal centre (screen)."""
    e = cheer_energy(t)
    jx = 7.0 * core.noise1(t * 2.7, 3) + 3.0 * math.sin(t * TAU * 3.1) * e
    jy = 6.0 * core.noise1(t * 2.7, 9) + 9.0 * abs(math.sin(t * TAU * 1.6)) * e - 14.0 * impact_pulse(t)
    wx, wy = INS_WRIST[0] + jx, INS_WRIST[1] + jy
    ang = math.pi * 1.06 + 0.03 * core.noise1(t * 1.9, 5)
    lw = B.line_for(B.LINE, 3.2)
    hold = ch.crystal_hold(face=1.0, size=1.62, thumb=big_feed(t), t=t, tilt=-0.06 + 0.04 * core.noise1(t * 1.3, 7))
    B.hand(cr, wx, wy, ang, 300.0, "grip", KOBOLD_SKIN, L_INS, lw, claw="#2E2A26", finger_w=0.9, palm_w=0.9,
           hold=hold)
    # the sleeve (blue-grey wool) from below the frame, its cuff over the wrist
    d = (math.cos(ang), math.sin(ang))
    cuff = (wx - d[0] * 18.0, wy - d[1] * 18.0)
    pts = [(cuff[0] + 520.0, cuff[1] + 470.0), (cuff[0] + 230.0, cuff[1] + 170.0), cuff]
    shp, so = B.taper_paths(cr, pts, 250.0, 150.0, lw)
    B.shade(cr, shp, KOBOLD_SLEEVE, L_INS, lw, outline=so, size=150.0)
    B.detail_lines(cr, [[(cuff[0] + 30, cuff[1] - 60), (cuff[0] + 10, cuff[1] + 5), (cuff[0] + 32, cuff[1] + 70)]],
                   lw * 0.9, B.palette(L_INS, KOBOLD_SLEEVE).line, 0.6)
    # its cold light falls on the claw (a halo below the face, not over it)
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
        draw_items(soft.begin(), items, t, cam, feed, sfeed, glows=glows, dy_front=170.0, detail=0)
        soft.end(cr, 3.5)
        ch.draw_pixie(cr, 1270.0, 1240.0, 9.0, pixie_pose(t, feed, staged=True), L_PIX, t)
    else:
        dt = E_SKIP if shot == 6 else 0.0
        items = world_items(t, skip_pixie=(shot >= 5 and t > L1.end + 2.4), crowd_dt=dt)
        draw_items(cr, items, t, cam, feed, sfeed, glows=glows, crowd_dt=dt)
    if shot in (1, 5, 6):
        draw_dragon_fg(cr, t, shot, cam)
        st["arch"][set_of(shot)].paint(cr, cam, 1.5)
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
    cues.append((round(SHOVES[4][1] + 0.05, 3), "cloth_rustle", {"gain": 0.3, "pan": pan_pair(T_STOP)}))   # payback wind-up
    cues.append((round(T_STOP + 0.3, 3), "cloth_rustle", {"gain": 0.45, "pan": pan_pair(T_STOP)}))         # arms drop
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
        acc = 0.5
        for k in range(1, 40):
            dist = k * step
            d_acc = m.speed * acc / 2.0
            tw = math.sqrt(2 * acc * dist / m.speed) if dist < d_acc else dist / m.speed + acc * 0.5
            tc = m.t_walk + tw                                       # on the crowd's clock
            if tc < T_EMPTY:
                ts = tc
            elif tc >= T_EMPTY + E_SKIP:
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
