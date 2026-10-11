"""s07 -- release (TIREDNESS Episode 2: Lights Out).  Music: "chaos:stop=0.779".

Everything happens in ONE simulated control room (sets.control_room, people
at s=0.75); every shot is a camera on that world, so positions, props and
damage always match from cut to cut. All timing comes from info.cue/line.

Shots:
  S1  smash    medium: eyes to the case, wind-up, the punch, the glass bursts
  S2  pull     close on face + hands: both fists GRIP the T-handle (world-space
               reach on the handle mark, held through the strain and the whole
               travel down); lean back, strain (sweat, teal glow, groan); the
               lever gives -> camera pulls back with it -> clunk
  S3  button   the Boss in her chair: eyes slide to LOCKDOWN, the hand follows,
               press -> "Lockdown."; the monitors behind her flash LOCKDOWN
  S4  shutters the window: a red LOCKDOWN sign flashing over the shaft; the
               pods' doors creep open... two pop open and two small creatures
               leap out and dash away; then heavy hazard-striped steel shutters
               slam down over the pods tier by tier (clang, sparks, shake each),
               red LOCKED lamps; the room shakes, dust falls
  S5a one_pod  two-shot: faces fall, ears lower; a hiss -> eyes snap right
  S5b          pan to the one tiny pod by the console (THING 38): seal hisses,
               the glass slides up
  S6  baby     the baby tumbles out, blinks, toddles, giggles; Curiosity bounds
               over and nuzzles it
  S7  alarm    red alarm, guards' light under the doors; he dashes over and
               scoops the baby up
  S8  s07_l02  the hatch bursts open: Embarrassment ducks out, small wave
  S9  run      they run through the hatch (Curiosity first), Emb last
  S10 hatch    Emb pulls it shut: SLAM; empty room
  S11a watch   insert: her hatch-cam monitor rewinds and freezes on Emb at the
               hatch (glancing back), a red ID bracket on his face. "Oh."
  S11b s07_l03 the Boss, 3/4, half-lidded, eyes up on that monitor: "...You
               too, Embarrassment."  flat, numb
  S11c numb    wider: her alone in the big chair, the frozen Emb on the monitor
               beside her. A slow blink; her eyes slide off it into nothing;
               "No matter. I'll catch you." -- eyes back to him, no feeling, no
               smirk; eyes drift away, a second slow blink; slow push-in
"""
import math

from engine import core, sets, props, fx, human, creatures as CR
from audio import sfx
from engine.core import tween, seg, clamp, lerp, smoothstep, ease_in_out, ease_out, ease_in, ease_out_back
from engine.human import P, IK, A, L, W

M = sets.CONTROL_MARKS
SP = 0.75                     # people (set char_scale)
SC = 0.75                     # Curiosity
SB = 0.64                     # the baby
FEET = M["feet_y"]            # 1500
CUR_Y = 1516                  # creatures stand a hair in front of the people line
BABY_Y = 1542

# the one tiny pod: stands on the floor between the release console and the
# LOCKDOWN pedestal, right under the observation window
POD_X, POD_Y, POD_S = 1290.0, 1522.0, 0.46
POD_FLOOR = POD_Y - 122 * POD_S          # interior floor (world y) where the baby sleeps
POD_TEXT, POD_SUB = "THING 38", "SPECIMEN 038"

SMASH_X = M["smash_feet"][0]   # 855
HAUL_X = 1015.0                # close enough that both hands reach the T-handle UP
GRIP = 30.0                    # the two fists sit +-GRIP px from the T-bar centre (bar shows between)
TIRED_X1 = 640.0               # stepped back from the console to see the window
CUR_X0 = 590.0
TIRED_X2 = 1012.0              # where he scoops the baby up
HATCH = M["hatch"]             # (40, 700, 290, 600)
HATCH_FEET = 1330.0            # threshold line for someone ducking through
EMB_X = -105.0                 # Emb standing left of the hatch (in front of its open panel)
HATCH_CX = HATCH[0] + HATCH[2] / 2

H_UP = M["release_handle_up"]
H_DN = M["release_handle_down"]
IMPACT = (1094.0, 932.0)

# ducking poses (the hatch is only 600 px tall)
DUCK = dict(P(L("l", 1.05, 0.1, 1.75, 0.2), L("r", 0.7, 0.1, 1.45, 0.3),
              A("l", 0.6, 0.2, 0.9), A("r", 0.6, 0.2, 0.9)), lean=0.55, neck=0.3, nod=0.2, hunch=0.7)
DUCK_DEEP = dict(P(L("l", 1.25, 0.1, 2.05, 0.2), L("r", 0.9, 0.1, 1.75, 0.3),
                   A("l", 0.6, 0.2, 0.9), A("r", 0.6, 0.2, 0.9)), lean=0.62, neck=0.32, nod=0.22, hunch=0.8)
# carrying the baby: it sits on his forearms in front of his chest (drawn over the arms)
_CRAD = P(IK("r", -0.02, 0.42, 0.24, "cup", layer="mid", tf=-1.0, wa=0.0, wabs=0.5),
          IK("l", 0.02, 0.50, 0.26, "relaxed", layer="front", wa=0.6, wabs=0.5))
RUN_CRADLE = {"base": "run", **_CRAD, "hold": 2.0, "lean": 0.16}
CRADLE = {"base": "stand", **_CRAD, "hold": 2.0, "nod": 0.18, "hunch": 0.3}
DUCK_CRADLE = dict(DUCK)
DUCK_CRADLE.update(P(IK("r", -0.02, 0.34, 0.26, "cup", layer="mid", tf=-1.0, wa=0.0, wabs=0.5),
                     IK("l", 0.02, 0.41, 0.28, "relaxed", layer="front", wa=0.6, wabs=0.5)))
DUCK_CRADLE["hold"] = 2.0
# the haul: both fists closed on the T-handle ("grip" hands, world-space reach).
# The lean is limited while the handle is UP (shoulder height) so both hands
# really reach it; he hangs back further only as the lever comes down.
_HAUL_ARMS = {"al_h": "grip", "ar_h": "grip", "al_layer": "mid", "ar_layer": "back"}   # head over the near arm
HAUL_GRIP = {"base": "haul", "lean": -0.22, "neck": -0.22, "nod": -0.26, "head_face": 0.35, **_HAUL_ARMS}
HAUL_STRAIN = {"base": "haul_strain", "lean": W(-0.28, 0.02, 0.0), "neck": -0.3, "nod": W(-0.34, 0.02, 0.4),
               "head_face": 0.35, **_HAUL_ARMS}
HAUL_FOLLOW = {"base": "haul", "lean": -0.8, "hunch": 0.95, "nod": 0.05, "neck": -0.2, "head_face": 0.3,
               **_HAUL_ARMS}
GUARD_IN = {"base": "guard_fists", "al_layer": "mid", "ar_layer": "back"}   # same layers as the haul
CROUCH = {"base": "crouch", "lean": 0.45, "neck": 0.05, "nod": 0.1}


# ============================================================================
# timing (all derived from the timeline)
# ============================================================================
class _Times:
    pass


_TCACHE = {}


def times(info):
    key = (info.id, tuple(sorted(info.cues.items())))
    T = _TCACHE.get(key)
    if T is not None:
        return T
    T = _Times()
    c = info.cue
    T.pull, T.button, T.shut = c("pull"), c("button"), c("shutters")
    T.pod, T.baby, T.alarm = c("one_pod"), c("baby"), c("alarm")
    T.run, T.hatch, T.watch, T.end = c("run"), c("hatch"), c("watch"), info.dur
    T.numb = c("numb")
    T.L1, T.L2, T.L3 = info.line("s07_l01"), info.line("s07_l02"), info.line("s07_l03")
    T.L3b = info.line("s07_l03b")
    # smash
    T.hit = max(0.6, T.pull - 0.5)          # the fist lands
    T.p0 = T.hit - 0.62                     # punch_cycle start (wind-up 0.48 s in)
    # pull
    T.grab = T.pull + 0.34
    T.give = T.button - 0.74
    T.clunk = T.give + 0.3
    # button
    T.press = T.L1.start - 0.2
    T.reach0 = T.press - 0.6
    T.lock_on = T.press + 0.08               # LOCKDOWN signs light up
    # shutters: the pods creep open from the clunk; two pop and get out; then
    # four tiers of steel shutters slam top -> bottom
    T.open0 = T.clunk + 0.25
    T.popA = T.shut + 0.12                   # near tier: door pops, a creature dashes LEFT
    T.popB = T.shut + 0.50                   # 2nd tier: door pops, a creature dashes RIGHT
    T.rows = [T.shut + 0.95 + i * 0.38 for i in range(4)]
    # one pod
    T.hiss = T.pod + 1.05
    T.pan0, T.pan1 = T.hiss + 0.25, T.hiss + 0.75
    T.glass0, T.glass1 = T.hiss + 0.12, T.hiss + 0.95
    # baby
    T.roll0 = T.baby + 0.08
    T.roll1 = T.roll0 + 0.72
    T.blink0 = T.roll1 + 0.04
    T.wob0, T.wob1 = T.blink0 + 0.95, T.blink0 + 1.45
    T.giggle = T.wob1
    T.cur_go = T.baby + 1.0
    T.cur_land = T.cur_go + 0.74
    T.nuzzle = T.cur_land + 0.18
    # alarm: he dashes to the baby and scoops it up; the hatch bursts open
    T.al0 = T.alarm
    vr = abs(human.cycle_speed("tired", "run", 0.9) * SP)
    T.dash0 = T.al0 + 0.3
    T.dash1 = T.dash0 + (TIRED_X2 - TIRED_X1) / vr
    T.scoop1 = T.dash1 + 0.34                # baby in his hand
    T.cradle1 = T.scoop1 + 0.34              # up, baby against his chest
    T.burst = T.L2.start - 0.35
    T.emb_out0, T.emb_out1 = T.burst + 0.1, T.burst + 0.52
    # run
    T.run0 = T.run + 0.22
    T.cur_run0 = T.run + 0.0
    T.emb_duck0 = T.hatch - 0.86
    T.emb_duck1 = T.emb_duck0 + 0.36
    T.emb_gone = T.emb_duck1 + 0.32
    T.slam0 = T.hatch - 0.2                  # the panel swings shut -> SLAM at T.hatch
    # watch: her hatch-cam feed rewinds to Emb's glance back, and freezes
    T.t_freeze = min(_tired_duck_t_raw(T) + 0.38, T.emb_duck0 - 0.03)
    T.rew0 = T.watch + 0.18
    T.rew1 = T.rew0 + 0.55
    T.wcut = info.word_time("s07_l03", 1) - 0.14      # insert -> her face on "You too"
    T.wcut2 = T.L3.end + 0.32                         # -> wider: her + the monitor (numb)
    _TCACHE[key] = T
    return T


def _tired_duck_t_raw(T):
    v = abs(human.cycle_speed("tired", "run", -0.9) * SP)
    return T.run0 + (TIRED_X2 + 10 - 330) / v


def _run_x(T, t):
    """Tiredness's x while running left with the baby (no foot sliding)."""
    v = human.cycle_speed("tired", "run", -0.9) * SP           # negative (left)
    return TIRED_X2 + 10 + v * max(0.0, t - T.run0)


def _tired_duck_t(T):
    """When his run reaches the hatch and he ducks in."""
    return _tired_duck_t_raw(T)


# ============================================================================
# characters: state at time t (one simulated world)
# ============================================================================
def _grip_targets(hx, hy, w=1.0):
    return {"l": (hx - GRIP, hy, w), "r": (hx + GRIP, hy, w)}


def tired_state(T, info, t):
    st = dict(x=SMASH_X, y=FEET, pose="stand", pose_t=None, turn=0.85, expr="determined",
              face={"lid": 0.15}, look=(0.0, 0.0), blink=None, power=0.68, reach=None,
              hold_mode=None, clip=None, visible=True, aura=0.0, depth=0.0, sweat=0.0)
    f = st["face"]
    if t < T.pull:
        # ---- the smash
        k_look = smoothstep(seg(t, 0.0, 0.18))
        st["look"] = (lerp(0.2, 0.75, k_look), lerp(-0.1, 0.08, k_look))
        f["head_turn"] = -0.22 + 0.1 * smoothstep(seg(t, 0.12, 0.32))
        f["brow"] = -0.25
        f["brow_ang"] = -0.3
        pt = clamp(t - T.p0, 0.0, 1.19)        # lands, holds, then pulls back to guard
        if t < T.p0:
            st["pose"] = ("stand", "punch_cycle", smoothstep(seg(t, T.p0 - 0.3, T.p0)))
        else:
            st["pose"] = "punch_cycle"
        st["pose_t"] = pt
        w = smoothstep(seg(pt, 0.5, 0.62)) * (1 - smoothstep(seg(pt, 0.88, 1.05)))
        if w > 0:
            st["reach"] = {"l": (IMPACT[0], IMPACT[1], w)}
        if T.hit - 0.12 < t < T.hit + 0.25:      # squint into the impact
            f["lower"] = 0.35 * (1 - seg(t, T.hit, T.hit + 0.25))
            f["squash"] = 0.06 * (1 - seg(t, T.hit, T.hit + 0.2))
        f["teeth"] = 0.6 * seg(t, T.p0 + 0.3, T.hit)
        f["press"] = 0.3
        st["blink"] = 0.0
        return st
    st["x"] = HAUL_X
    if t < T.pod:
        # ---- the haul: both fists closed on the T-handle the whole time
        lv = lever_at(T, t)
        hx, hy = props.release_console_handle(*M["release"], SP, lv)
        kf = smoothstep(seg(lv, 0.35, 1.0))      # hangs back further only as the handle comes down
        if t < T.grab:
            k = smoothstep(seg(t, T.pull, T.grab))
            st["pose"] = (GUARD_IN, HAUL_GRIP, k)
            st["reach"] = _grip_targets(hx, hy, k)
        elif t < T.give:
            st["pose"] = (HAUL_GRIP, HAUL_STRAIN, smoothstep(seg(t, T.grab, T.grab + 0.3)))
            st["pose_t"] = t - T.grab
            st["reach"] = _grip_targets(hx, hy)
        elif t < T.clunk + 0.7:
            k2 = smoothstep(seg(t, T.clunk + 0.1, T.clunk + 0.7))
            st["pose"] = (HAUL_STRAIN, HAUL_FOLLOW, kf * (1 - 0.6 * k2))
            st["pose_t"] = t - T.grab
            st["reach"] = _grip_targets(hx, hy)
        else:
            # lets go, straightens, steps back to see the window (offscreen: the Boss's shot)
            k = smoothstep(seg(t, T.clunk + 0.7, T.clunk + 1.3))
            st["pose"] = ((HAUL_STRAIN, HAUL_FOLLOW, 0.4), "stand", k)
            st["reach"] = _grip_targets(hx, hy, 1 - k)
            st["turn"] = lerp(1.0, 0.55, k)
            st["x"] = lerp(HAUL_X, TIRED_X1, k)
        # face: grit -> all-out squeeze -> it gives
        if t < T.grab + 0.2:
            f.update(brow=-0.3, brow_ang=-0.3, teeth=0.4, press=0.2)
            st["look"] = (0.5, -0.45)
        elif t < T.give - 0.38:
            st["expr"] = "determined"
            k = seg(t, T.grab, T.give - 0.4)
            f.update(lid=0.15 + 0.08 * k, brow=-0.5, brow_ang=-0.45, teeth=1.0, lip_up=0.55,
                     lip_low=0.3, open=0.12, flare=0.6 * k, cheek=0.15)
            st["look"] = (0.45, -0.5)
            st["power"] = lerp(0.7, 0.95, k)
            st["aura"] = 0.55 * smoothstep(seg(t, T.grab, T.grab + 0.6)) + 0.3 * k
            st["sweat"] = 0.55 * smoothstep(seg(t, T.grab + 0.2, T.grab + 0.8))
        elif t < T.give:
            st["expr"] = "pain"
            f = st["face"] = {"teeth": 1.0, "squash": 0.04, "flare": 0.8}
            st["power"] = 0.95
            st["aura"] = 0.95
            st["sweat"] = 0.6
        else:
            k = seg(t, T.give, T.give + 0.25)
            st["expr"] = "determined"
            f.update(lid=lerp(0.0, 0.18, seg(t, T.clunk, T.clunk + 0.5)), brow=0.2 * (1 - k),
                     open=0.35 * (1 - seg(t, T.clunk + 0.3, T.clunk + 1.0)), teeth=0.0)
            st["power"] = lerp(0.95, 0.72, seg(t, T.clunk, T.clunk + 0.8))
            st["aura"] = 0.95 * (1 - seg(t, T.give, T.clunk + 0.6))
            st["look"] = tween(t, [(T.clunk + 0.2, (0.5, 0.1)), (T.clunk + 0.45, (0.45, -0.8))])
            f["head_nod"] = -0.12 * smoothstep(seg(t, T.clunk + 0.4, T.clunk + 0.8))
        return st
    # ---- after the lever: standing back from the console
    st["turn"] = 0.55
    st["x"] = TIRED_X1
    if t < T.hiss:
        # S5a: the shutters landed. Faces fall.
        k = smoothstep(seg(t, T.pod, T.pod + 0.6))
        st["expr"] = "determined"
        f.update(lid=lerp(0.2, 0.3, k), brow=0.15 * k, brow_ang=0.5 * k, press=0.55 * k,
                 frown=0.3 * k, head_nod=-0.22)
        st["look"] = (0.4, -0.75)
        st["power"] = 0.68
        if t > T.pod + 0.55:          # a slow, heavy blink
            st["blink"] = tween(t, [(T.pod + 0.55, 0.0), (T.pod + 0.75, 1.0), (T.pod + 0.85, 1.0),
                                     (T.pod + 1.05, 0.0)])
        return st
    if t < T.run:
        # the hiss: pupils snap right, the head follows; then he watches the baby
        st["expr"] = "determined"
        ks = smoothstep(seg(t, T.hiss + 0.02, T.hiss + 0.16))
        kh = smoothstep(seg(t, T.hiss + 0.15, T.hiss + 0.4))
        f.update(lid=lerp(0.3, 0.2, ks), brow=lerp(0.15, 0.35, ks), brow_ang=lerp(0.5, 0.1, ks),
                 press=lerp(0.55, 0.0, ks), head_turn=0.28 * kh, head_nod=lerp(-0.1, 0.05, kh))
        st["look"] = (lerp(0.4, 0.95, ks), lerp(-0.75, 0.15, ks))
        if t >= T.giggle:              # the faintest smile at the giggle
            kk = smoothstep(seg(t, T.giggle + 0.2, T.giggle + 0.8))
            f.update(curve=0.25 * kk, lid=0.2 + 0.08 * kk, brow_ang=0.15 * kk)
        if t >= T.al0:
            # the alarm: lids lift, eyes up to the beacon... then he dashes to the baby
            ka = smoothstep(seg(t, T.al0 + 0.05, T.al0 + 0.2))
            f.update(lid=lerp(f.get("lid", 0.2), 0.12, ka), brow=0.45 * ka, curve=0.0,
                     brow_ang=0.25, head_nod=lerp(0.05, -0.12, ka), head_turn=0.1)
            st["look"] = (0.25, -0.9)
            st["power"] = 0.72
            if t >= T.dash0 - 0.12:
                st["look"] = (0.9, 0.45)
                f["head_nod"] = 0.1
        if t >= T.dash0:
            return _tired_scoop(T, t, st, f)
        return st
    # ---- the run (holding the baby)
    st["face"] = f = {"lid": 0.14, "brow": -0.1, "brow_ang": -0.2, "press": 0.2}
    st["power"] = 0.72
    st["x"] = TIRED_X2
    st["hold_mode"] = "both"
    td = _tired_duck_t(T)
    if t < T.run0:
        st["pose"] = CRADLE
        st["turn"] = -0.9
        st["look"] = (-0.95, 0.0)
    elif t < td:
        st["pose"] = (CRADLE, RUN_CRADLE, smoothstep(seg(t, T.run0, T.run0 + 0.14)))
        st["pose_t"] = t - T.run0
        st["turn"] = -0.9
        st["x"] = _run_x(T, t)
        st["look"] = (-0.9, 0.05)
        f["brow"] = -0.25
    else:
        # duck through: up onto the threshold, then into the crawlway
        x_d = _run_x(T, td)
        k = smoothstep(seg(t, td, td + 0.26))
        st["pose"] = (RUN_CRADLE, DUCK_CRADLE, k)
        st["pose_t"] = t - T.run0
        st["turn"] = -1.0
        st["x"] = lerp(x_d, HATCH_CX + 10, k)
        st["y"] = lerp(FEET + 6, HATCH_FEET, k)
        st["look"] = (-0.9, 0.2)
        st["clip"] = "hatch" if k > 0.8 else None
        st["depth"] = smoothstep(seg(t, td + 0.24, td + 0.62))
        if st["depth"] >= 1:
            st["visible"] = False
    if t < td:
        st["y"] = FEET + 6
    return st


def _tired_scoop(T, t, st, f):
    """The alarm: he dashes over, scoops the baby up, turns toward the hatch."""
    st["power"] = 0.72
    if t < T.dash1:
        k = (t - T.dash0)
        st["pose"] = ("stand", "run", smoothstep(seg(t, T.dash0, T.dash0 + 0.1)))
        st["pose_t"] = k
        st["turn"] = 0.9
        vr = abs(human.cycle_speed("tired", "run", 0.9) * SP)
        st["x"] = TIRED_X1 + vr * k
        st["look"] = (0.9, 0.45)
        f.update(lid=0.12, brow=0.2, brow_ang=0.0)
        return st
    st["x"] = TIRED_X2
    if t < T.scoop1:
        k = smoothstep(seg(t, T.dash1, T.dash1 + 0.24))
        st["pose"] = ("run", "pick_up", k)
        st["pose_t"] = T.dash1 - T.dash0
        st["turn"] = lerp(0.9, 0.7, k)
        bx = baby_rest_x(T) - CR.BABY_WALK_SPEED * SB * (T.wob1 - T.wob0)
        st["reach"] = {"r": (bx - 6, BABY_Y - 38, smoothstep(seg(t, T.dash1 + 0.04, T.scoop1)))}
        st["look"] = (0.7, 0.85)
        st["hold_mode"] = "r"
        f.update(lid=0.14, brow=0.1, head_nod=0.12)
        return st
    if t < T.cradle1:
        k = smoothstep(seg(t, T.scoop1, T.cradle1))
        st["pose"] = ("pick_up", CRADLE, k)
        bx = baby_rest_x(T) - CR.BABY_WALK_SPEED * SB * (T.wob1 - T.wob0)
        st["reach"] = {"r": (bx - 6, BABY_Y - 38, 1 - smoothstep(seg(t, T.scoop1, T.scoop1 + 0.2)))}
        st["turn"] = lerp(0.7, -0.9, smoothstep(seg(t, T.scoop1 + 0.06, T.cradle1)))
        st["look"] = tween(t, [(T.scoop1, (0.5, 0.7)), (T.cradle1, (-0.6, 0.3))])
        st["hold_mode"] = "r" if k < 0.5 else "both"
        f.update(lid=0.16, brow=0.1)
        return st
    # holding it close; eyes on the doors (the footsteps), then the hatch bursting open
    st["pose"] = CRADLE
    st["turn"] = -0.9
    st["hold_mode"] = "both"
    st["look"] = tween(t, [(T.cradle1, (-0.6, 0.3)), (T.cradle1 + 0.15, (-0.95, -0.05)),
                           (T.burst + 0.05, (-0.95, -0.05)), (T.burst + 0.15, (-1.0, 0.05))])
    f.update(lid=lerp(0.16, 0.08, seg(t, T.burst, T.burst + 0.12)), brow=0.3, brow_ang=0.2)
    return st


def lever_at(T, t):
    if t < T.grab + 0.3:
        return 0.0
    if t < T.give:
        # resists: creeps a few degrees in two jerks
        return 0.05 * smoothstep(seg(t, T.grab + 0.35, T.grab + 0.7)) + \
               0.05 * smoothstep(seg(t, T.give - 0.55, T.give - 0.3))
    return lerp(0.1, 1.0, ease_in(seg(t, T.give, T.clunk)))


def _bound(t, t0, x0, x1, n, dur, gy, s=SC):
    """Curiosity bounding from x0 to x1 in n leaps: (x, y, pose, airborne)."""
    k = clamp((t - t0) / dur)
    if k >= 1:
        return x1, gy, "stand", False
    ph = k * n
    i = min(n - 1, int(ph))
    q = ph - i
    xa = lerp(x0, x1, i / n)
    xb = lerp(x0, x1, (i + 1) / n)
    if q < 0.18:                     # contact: crouched, gathering
        return lerp(xa, xb, q * 0.4), gy, "crouch", False
    u = (q - 0.18) / 0.82
    x = lerp(lerp(xa, xb, 0.18 * 0.4), xb, u)
    y = gy - 112 * s - 120 * s * math.sin(math.pi * u)
    return x, y, "leap", True


def cur_state(T, info, t):
    st = dict(x=CUR_X0, y=CUR_Y, pose="sit", expr="hopeful", look=(0.3, -0.6), ears=None, tilt=0.0,
              face=None, flip=False, tail_curl=0.0, pose_t=None, blink=None, clip=None, visible=True,
              pose_from=None, pose_mix=1.0, airborne=False, depth=0.0)
    if t < T.pull:
        if t < T.hit:
            st["expr"] = "curious"
            st["look"] = (0.45, -0.6)
            st["ears"] = 0.6
        else:
            k = ease_out_back(seg(t, T.hit, T.hit + 0.18))
            st["expr"] = "wide"
            st["ears"] = lerp(0.6, 1.0, k)
            st["tilt"] = -0.12 * (1 - seg(t, T.hit + 0.2, T.hit + 0.6))
            st["look"] = (0.7, -0.45)
        return st
    if t < T.pod:
        st["expr"] = "hopeful"
        st["ears"] = 0.8 if t < T.clunk else lerp(0.8, 1.0, ease_out_back(seg(t, T.clunk, T.clunk + 0.2)))
        st["look"] = (0.35, -0.55) if t < T.clunk + 0.2 else (0.55, -0.8)
        st["tail_curl"] = 0.35 * smoothstep(seg(t, T.grab, T.grab + 0.8))
        return st
    if t < T.hiss:
        # the shutters landed: ears lower degree by degree
        st["expr"] = "sad"
        st["ears"] = lerp(0.62, 0.12, ease_in_out(seg(t, T.pod + 0.05, T.hiss - 0.05)))
        st["look"] = (0.45, -0.95)
        st["tail_curl"] = 0.0
        return st
    if t < T.cur_go:
        ke = ease_out_back(seg(t, T.hiss + 0.03, T.hiss + 0.22))
        st["expr"] = "surprised_soft"
        st["ears"] = lerp(0.12, 0.95, ke)
        st["look"] = (lerp(0.45, 0.95, smoothstep(seg(t, T.hiss, T.hiss + 0.12))), 0.1)
        st["tilt"] = -0.08 * ke
        if t > T.baby:
            st["expr"] = "hopeful"
            st["look"] = (0.9, 0.3)
        return st
    if t < T.run:
        bx_end = baby_rest_x(T)
        x_to = bx_end - 212
        if t < T.cur_land:
            x, y, pose, air = _bound(t, T.cur_go, CUR_X0, x_to, 2, T.cur_land - T.cur_go, CUR_Y)
            st.update(x=x, y=y, pose=pose, airborne=air, expr="hopeful", ears=0.95, look=(0.8, 0.2),
                      tail_curl=0.2)
            return st
        st["x"] = x_to
        st["pose"] = "stand"
        if t < T.nuzzle:
            st.update(expr="hopeful", ears=0.9, look=(0.5, 0.5), tilt=0.15)
        else:
            # head lowered to the baby, rubbing cheek to cheek, tail tip curling
            k = smoothstep(seg(t, T.nuzzle, T.nuzzle + 0.3))
            ph = (t - T.nuzzle) * math.tau / 1.1
            st.update(expr="content", ears=0.55, tilt=0.55 * k + 0.07 * math.sin(ph) * k,
                      tail_curl=0.7 * smoothstep(seg(t, T.nuzzle, T.nuzzle + 0.8)),
                      pose="crouch", pose_from="stand", pose_mix=0.7 * k)
            st["x"] = x_to + 7 * math.sin(ph) * k
        if t >= T.al0:
            # alarm: ears shoot up, head up, a hop back as he swoops in for the baby
            ka = ease_out_back(seg(t, T.al0 + 0.08, T.al0 + 0.26))
            st.update(expr="wide", ears=lerp(0.55, 1.0, ka), tilt=lerp(0.4, -0.1, ka), tail_curl=0.0,
                      pose="crouch", pose_from="stand",
                      pose_mix=0.7 * (1 - smoothstep(seg(t, T.al0 + 0.05, T.al0 + 0.3))))
            if st["pose_mix"] <= 0.01:
                st.update(pose="stand", pose_from=None, pose_mix=1.0)
            st["x"] = x_to - 70 * smoothstep(seg(t, T.dash0 + 0.1, T.dash1 + 0.1))
            st["look"] = tween(t, [(T.al0 + 0.1, (0.2, -0.9)), (T.dash0, (0.2, -0.9)),
                                   (T.dash0 + 0.15, (0.6, -0.4)), (T.cradle1, (0.3, -0.7)),
                                   (T.burst + 0.05, (0.3, -0.7)), (T.burst + 0.2, (-0.9, -0.2))])
            if t >= T.burst + 0.1:
                st["face"] = tween(t, [(T.burst + 0.1, 1.0), (T.burst + 0.4, -1.0)])
        return st
    # ---- the run: bound to the hatch and dive through
    x_from = baby_rest_x(T) - 212 - 70
    st["flip"] = True
    st.update(expr="wide", ears=0.9, look=(-0.6, 0.0))
    t_dive = T.run + 0.8
    if t < T.cur_run0:
        st["pose"] = "stand"
        st["x"] = x_from
        st["face"] = -1.0
        st["flip"] = False
        return st
    if t < t_dive:
        x, y, pose, air = _bound(t, T.cur_run0, x_from, 300, 3, t_dive - T.cur_run0, CUR_Y)
        st.update(x=x, y=y, pose=pose, airborne=air)
        return st
    # the dive: up onto the threshold and away up the crawlway
    k = seg(t, t_dive, t_dive + 0.3)
    st["pose"] = "leap"
    st["airborne"] = True
    st["x"] = lerp(300, HATCH_CX - 10, k)
    st["y"] = lerp(CUR_Y, HATCH_FEET, k) - 112 * SC - 90 * SC * math.sin(math.pi * k)
    st["clip"] = "hatch" if k > 0.6 else None
    st["depth"] = smoothstep(seg(t, t_dive + 0.25, t_dive + 0.6))
    if st["depth"] >= 1:
        st["visible"] = False
    return st


def baby_rest_x(T):
    r = 1.15 * math.pi
    return POD_X - 18 - r * CR.BABY_ROLL_RADIUS * SB


def baby_state(T, info, t):
    st = dict(x=POD_X, y=POD_FLOOR, pose="curl", expr="calm", look=None, flip=True, roll=None,
              pose_t=None, ears=None, tilt=0.0, inside=True, held=False, visible=True, tail_curl=0.0)
    if t < T.roll0:
        if t > T.glass1:
            st["expr"] = "calm"
        return st
    st["inside"] = False
    if t < T.roll1:
        k = seg(t, T.roll0, T.roll1)
        r = 1.15 * math.pi * ease_out(k)
        st["pose"] = "tumble"
        st["roll"] = -r
        st["flip"] = False
        st["x"] = POD_X - 18 - r * CR.BABY_ROLL_RADIUS * SB
        # drops off the pod's base onto the floor with a small bounce
        yk = seg(t, T.roll0, T.roll0 + 0.3)
        y = lerp(POD_FLOOR + 4, BABY_Y, yk * yk)
        if k > 0.42:
            y -= 22 * math.sin(math.pi * seg(t, T.roll0 + 0.3, T.roll0 + 0.55))
        st["y"] = y
        return st
    st["x"] = baby_rest_x(T)
    st["y"] = BABY_Y
    if t < T.wob0:
        st["pose"] = "sit"
        st["expr"] = "blink"
        st["pose_t"] = t - T.blink0
        st["tilt"] = 0.1 * math.sin((t - T.blink0) * 7.0) * (1 - seg(t, T.blink0, T.blink0 + 0.6))
        st["look"] = (-0.3, 0.1)
    elif t < T.wob1:
        st["pose"] = "wobble_walk"
        st["pose_t"] = t - T.wob0
        st["expr"] = "curious"
        st["x"] = baby_rest_x(T) - CR.BABY_WALK_SPEED * SB * (t - T.wob0)
        st["look"] = (-0.6, 0.0)
    else:
        st["pose"] = "sit"
        st["x"] = baby_rest_x(T) - CR.BABY_WALK_SPEED * SB * (T.wob1 - T.wob0)
        st["expr"] = "giggle"
        st["tail_curl"] = 0.6
        if t >= T.al0 + 0.1:
            st["expr"] = "curious"
            st["ears"] = 0.9
            st["look"] = (0.0, -0.9)
            st["tail_curl"] = 0.0
    if t >= T.scoop1:
        st["flip"] = True
        st["held"] = True
        st["pose"] = "held"
        st["expr"] = "calm" if t < T.run0 - 0.1 else "giggle"
        st["tail_curl"] = 0.5
    return st


def emb_state(T, info, t):
    st = dict(x=HATCH_CX, y=HATCH_FEET, pose=DUCK_DEEP, pose_t=None, turn=0.6, expr="alarmed", face={},
              look=(0.8, 0.0), reach=None, visible=False, clip="hatch", depth=0.0, blush=0.25,
              sweat=0.25, front_of_panel=False)
    if t < T.burst + 0.02 or t >= T.emb_gone:
        return st
    st["visible"] = True
    f = st["face"]
    if t < T.emb_out0:
        # coming up the crawlway toward us
        st["depth"] = 1.0 - smoothstep(seg(t, T.burst, T.emb_out0))
        return st
    if t < T.emb_out1:
        # steps out and aside (left of the opening, in front of the open panel)
        k = smoothstep(seg(t, T.emb_out0, T.emb_out1))
        st["x"] = lerp(HATCH_CX, EMB_X, k)
        st["y"] = lerp(HATCH_FEET, FEET - 6, k)
        st["pose"] = (DUCK_DEEP, "stand", k)
        st["clip"] = "hatch" if k < 0.12 else None
        st["front_of_panel"] = k > 0.5
        return st
    st["clip"] = None
    st["front_of_panel"] = True
    st["x"], st["y"] = EMB_X, FEET - 6
    if t < T.emb_duck0:
        wave_on = T.emb_out1 - 0.05
        wave_off = T.run + 0.3
        if t < wave_on:
            st["pose"] = "stand"
        elif t < wave_off:
            st["pose"] = ("stand", "wave_small", smoothstep(seg(t, wave_on, wave_on + 0.12)))
            st["pose_t"] = t - wave_on
        else:
            st["pose"] = ("wave_small", "stand", smoothstep(seg(t, wave_off, wave_off + 0.25)))
            st["pose_t"] = t - wave_on
        st["expr"] = "alarmed" if t < T.L2.start else "determined"
        f.update(brow=0.25, brow_ang=0.35)
        st["mouth"] = info.mouth("embar", t)
        # on "This way!" his head tips toward the hatch
        tw = info.word_time("s07_l02", 2)
        f["head_turn"] = tween(t, [(tw - 0.05, 0.0), (tw + 0.1, -0.25), (T.L2.end, -0.25),
                                   (T.L2.end + 0.2, 0.0)])
        # watching them come -> into the hatch past him -> a nervous glance back at the Boss
        tdk = _tired_duck_t(T)
        st["look"] = tween(t, [(T.emb_out1, (0.9, 0.0)), (tw - 0.05, (0.9, 0.0)), (tw + 0.08, (0.5, 0.1)),
                               (T.L2.end, (0.5, 0.1)), (T.L2.end + 0.15, (0.9, 0.05)),
                               (tdk - 0.05, (0.4, 0.1)), (tdk + 0.12, (0.4, 0.1)),
                               (tdk + 0.24, (0.95, -0.05)), (T.emb_duck0 - 0.05, (0.95, -0.05)),
                               (T.emb_duck0, (0.6, 0.1))])
        if t > tdk + 0.24:
            f["head_turn"] = tween(t, [(tdk + 0.24, 0.0), (tdk + 0.4, 0.22), (T.emb_duck0 - 0.1, 0.22),
                                       (T.emb_duck0, 0.0)])
            st["expr"] = "alarmed"
            st["sweat"] = 0.45
        return st
    # ducks in after them, then away up the crawlway
    k = smoothstep(seg(t, T.emb_duck0, T.emb_duck1))
    st["pose"] = ("stand", DUCK_DEEP, k)
    st["turn"] = lerp(0.6, 0.9, k)
    st["x"] = lerp(EMB_X, HATCH_CX, k)
    st["y"] = lerp(FEET - 6, HATCH_FEET, k)
    st["look"] = (0.4, 0.1)
    st["expr"] = "determined"
    st["front_of_panel"] = k < 0.55
    st["clip"] = "hatch" if k > 0.85 else None
    st["depth"] = smoothstep(seg(t, T.emb_duck1, T.emb_gone))
    return st


# the Boss's gaze targets for the ending (eye look, screen-ish)
B_MON = (0.72, -0.5)          # up-right: the hatch-cam monitor beside her
B_AWAY = (-0.18, 0.38)        # down and a little left: nothing in particular
B_REST = (-0.75, 0.02)        # (s06/s07 default: toward Tiredness's side of the room)


def boss_state(T, info, t):
    ct = 1.0 - 0.2 * smoothstep(seg(t, T.watch + 0.05, T.watch + 0.75))
    st = dict(chair_turn=ct, turn=3.5 * (1 - ct), expr="cold", blink=None, pose="sit_chair",
              face={}, look=B_REST, reach=None, pressed=0.0, mouth=info.mouth("boss", t))
    f = st["face"]
    bx, by = M["lockdown"]
    # LOCKDOWN: the hand travels from the armrest to the button, presses, rests, returns
    if T.reach0 <= t < T.L1.end + 1.0:
        w = smoothstep(seg(t, T.reach0, T.press - 0.06))
        w *= 1 - smoothstep(seg(t, T.L1.end + 0.3, T.L1.end + 0.9))
        dip = 9 * math.sin(math.pi * seg(t, T.press - 0.06, T.press + 0.16))
        st["reach"] = {"l": (bx + 2, by - 24 + dip, w)}
    st["pressed"] = clamp(seg(t, T.press - 0.02, T.press + 0.06))
    if t < T.watch:
        st["look"] = tween(t, [(T.reach0 - 0.12, B_REST), (T.reach0 + 0.02, (-0.55, 0.6)),
                               (T.press + 0.08, (-0.55, 0.6)), (T.press + 0.22, (-0.8, 0.0))])
        f["head_turn"] = tween(t, [(T.reach0, -0.12), (T.reach0 + 0.18, -0.2), (T.press + 0.2, -0.2),
                                   (T.press + 0.4, -0.16)])
        f["head_nod"] = tween(t, [(T.reach0, 0.0), (T.reach0 + 0.18, 0.08), (T.press + 0.2, 0.08),
                                  (T.press + 0.4, 0.0)])
        f["lid"] = 0.05 * smoothstep(seg(t, T.L1.end - 0.4, T.L1.end + 0.2))
        if t >= T.hatch:
            f["lid"] = 0.0
        return st
    # ---- the ending: bored, sad, numb. Half-lidded, flat mouth, no smirk.
    st["expr"] = "bored"
    tb1 = T.wcut2 + 0.12                  # slow blink in the numb beat: eyes leave the monitor
    tg = T.L3b.start + (info.word_time("s07_l03b", 2) - T.L3b.start) - 0.12   # back up on "I'll"
    tb2 = T.L3b.end + 1.0                 # a second, slower blink after the line
    st["look"] = tween(t, [(T.watch + 0.1, B_REST), (T.watch + 0.3, B_MON),          # (offscreen)
                           (tb1 + 0.2, B_MON), (tb1 + 0.45, B_AWAY),               # during the blink
                           (tg, B_AWAY), (tg + 0.22, B_MON),
                           (T.L3b.end + 0.55, B_MON), (T.L3b.end + 0.95, (0.1, 0.4))])
    # the head follows the pupils ~0.15 s later
    f["head_turn"] = tween(t, [(T.watch + 0.4, 0.0), (T.watch + 0.7, 0.16),
                               (tb1 + 0.35, 0.16), (tb1 + 0.7, 0.02),
                               (tg + 0.15, 0.02), (tg + 0.45, 0.14),
                               (T.L3b.end + 0.7, 0.14), (T.L3b.end + 1.2, 0.04)])
    f["head_nod"] = tween(t, [(T.watch + 0.4, 0.0), (T.watch + 0.7, -0.07),
                              (tb1 + 0.35, -0.07), (tb1 + 0.7, 0.07),
                              (tg + 0.15, 0.07), (tg + 0.45, -0.04),
                              (T.L3b.end + 0.7, -0.04), (T.L3b.end + 1.2, 0.08)])
    heavy = (0.20 + 0.06 * smoothstep(seg(t, T.L3.end, T.L3.end + 0.6))
             + 0.06 * smoothstep(seg(t, tb2 + 0.4, tb2 + 1.0)))
    f.update(lid=heavy, lid_ang=0.22, brow=-0.04, brow_ang=0.16, curve=-0.07, frown=0.1,
             press=0.0, smirk=0.0, width=-0.04)
    # unfocused while she stares at nothing
    f["focus"] = -0.35 * smoothstep(seg(t, tb1 + 0.3, tb1 + 0.7)) * (1 - smoothstep(seg(t, tg, tg + 0.25))) \
        - 0.35 * smoothstep(seg(t, T.L3b.end + 0.7, T.L3b.end + 1.2))
    # slow blinks (0.35-0.45 s close, hold, open); no auto-blinks in between
    if t < T.wcut:
        st["blink"] = None
    elif t < tb2 - 0.2:
        st["blink"] = tween(t, [(tb1, 0.0), (tb1 + 0.38, 1.0), (tb1 + 0.52, 1.0), (tb1 + 0.95, 0.0)])
    else:
        st["blink"] = tween(t, [(tb2, 0.0), (tb2 + 0.45, 1.0), (tb2 + 0.65, 1.0), (tb2 + 1.15, 0.0)])
    # a faint breath out in the numb beat (shoulders sink a hair)
    sink = smoothstep(seg(t, T.L3.end + 0.1, T.L3.end + 0.8))
    st["pose"] = {"base": "sit_chair", "hunch": 0.12 * (1 - sink), "nod": 0.03 * sink}
    return st


# ============================================================================
# props drawn by the scene
# ============================================================================
def _pod_open(T, t):
    return ease_in_out(seg(t, T.glass0, T.glass1))


def draw_joy_pod(ctx, T, t, inside_fn=None):
    """The one tiny pod (THING 38) by the console. Anchor = floor under it."""
    op = _pod_open(T, t)
    pw = core.PAL["power"]
    pulse = 0.85 + 0.15 * math.sin(t * math.tau * 0.25)
    g = pulse * (1.0 + 0.25 * seg(t, T.hiss, T.hiss + 0.3))
    s = POD_S
    # floor light pool + halo (behind)
    core.ellipse(ctx, POD_X, POD_Y + 4, 230 * s * (1 + 0.7 * op), 36 * s)
    core.fill(ctx, core.alpha(pw, 0.12 + 0.14 * op))
    core.radial_glow(ctx, POD_X, POD_Y - 360 * s, 520 * s, pw, 0.22 * g)
    with core.saved(ctx, POD_X, POD_Y, s):
        # tubes up into the wall
        for sd in (-1, 1):
            props.curve(ctx, [(sd * 110, -670), (sd * 170, -720), (sd * 175, -820)], props.INK, 22)
            props.curve(ctx, [(sd * 110, -670), (sd * 170, -720), (sd * 175, -820)], "#3b4757", 12)
        # interior: a lit teal capsule; once open it reads as a hollow seat
        core.rrect(ctx, -135, -600, 270, 480, 135)
        props.fs(ctx, core.mixc(core.mixc("#0b3a40", pw, 0.42 + 0.18 * g), "#0a2a30", 0.55 * op), 0)
        ctx.save()
        core.rrect(ctx, -135, -600, 270, 480, 135)
        ctx.clip()
        core.radial_glow(ctx, 0, -200 - 100 * (1 - op), 300, pw, 0.5 * g)
        if op > 0.01:      # inner back wall shading + ribs (it is open now)
            core.rrect(ctx, -105, -570, 210, 430, 105)
            core.stroke(ctx, core.alpha("#062026", 0.6 * op), 10)
            for k in range(3):
                props.line(ctx, [(-70, -470 + k * 90), (70, -470 + k * 90)], core.alpha("#0d4a52", 0.7 * op), 6)
        for k in range(4):
            ph = (t * 0.3 + core.hash01(k, 71)) % 1.0
            bx = -80 + 160 * core.hash01(k, 72) + 8 * math.sin(t * 2 + k)
            byy = -140 - ph * 420
            core.circle(ctx, bx, byy, 7 + 5 * core.hash01(k, 73))
            core.stroke(ctx, (0.85, 1.0, 0.98, 0.6 * (1 - op)), 3)
        if inside_fn is not None:
            ctx.save()
            ctx.scale(1 / s, 1 / s)
            inside_fn(ctx)
            ctx.restore()
        # glass front (slides up into the top cap)
        dy = -470 * op
        if op < 0.999:
            core.rrect(ctx, -135, -600 + dy, 270, 480, 135)
            core.fill(ctx, (0.75, 1.0, 0.97, 0.16))
            core.poly(ctx, [(-95, -560 + dy), (-58, -575 + dy), (-58, -170 + dy), (-95, -150 + dy)])
            core.fill(ctx, (1, 1, 1, 0.2))
            core.poly(ctx, [(40, -540 + dy), (56, -548 + dy), (56, -300 + dy), (40, -292 + dy)])
            core.fill(ctx, (1, 1, 1, 0.12))
            core.rrect(ctx, -135, -600 + dy, 270, 480, 135)
            core.stroke(ctx, (0.85, 1.0, 1.0, 0.7), 5)
        ctx.restore()
        # the opening's steel rim (the seal)
        core.rrect(ctx, -135, -600, 270, 480, 135)
        core.stroke(ctx, props.INK, 14)
        core.rrect(ctx, -135, -600, 270, 480, 135)
        core.stroke(ctx, core.mixc("#2a3646", "#8fa3b3", op), 6)
        # the seal line flashes on the hiss
        if T.hiss - 0.02 < t < T.hiss + 0.5:
            a = 1 - seg(t, T.hiss + 0.1, T.hiss + 0.5)
            props.line(ctx, [(-120, -128), (120, -128)], (0.9, 1.0, 1.0, 0.9 * a), 8)
        # caps
        props.rect(ctx, -160, -690, 320, 96, "#4a5868", 7, r=26)
        props.line(ctx, [(-130, -642), (130, -642)], "#6b7a8c", 6)
        if op > 0.6:   # the glass lip peeks out under the top cap once it is up
            props.rect(ctx, -110, -600, 220, 14, (0.8, 1.0, 1.0, 0.5), 3, r=6)
        for k in range(3):
            core.circle(ctx, -50 + k * 50, -618 - 6, 8)
            props.fs(ctx, pw if op < 0.5 else "#7cf2b0", 3)
        props.rect(ctx, -170, -130, 340, 130, "#4a5868", 7, r=24)
        props.rect(ctx, -170, -34, 340, 34, "#3b4757", 0, r=10)
        props.rect(ctx, -170, -130, 340, 130, None, 7, r=24)
        props.nameplate(ctx, 0, -70, 0.95, text=POD_TEXT, sub=POD_SUB, seed=3)


class _ClosedPod:
    hiss = glass0 = glass1 = 1e9


def joy_pod_closed(ctx, t):
    """The tiny THING 38 pod, sealed, with the baby asleep inside, at (POD_X, POD_Y)
    in CONTROL_MARKS world coords (for continuity in s06's control-room shots)."""
    def inside(c):
        CR.draw_specimen(c, 0, -122 * POD_S, SB, t, baby=True, pose="curl", expr="calm", flip=True)
    draw_joy_pod(ctx, _ClosedPod, t, inside)


def draw_pod_steam(ctx, T, t):
    """Pneumatic hiss: a few soft puffs from the seal (<= 8 pieces)."""
    if not (T.hiss <= t < T.hiss + 1.4):
        return
    s = POD_S
    for i in range(8):
        sd = -1 if i % 2 else 1
        t0 = T.hiss + 0.06 * (i // 2)
        k = seg(t, t0, t0 + 1.1)
        if k <= 0 or k >= 1:
            continue
        h = core.hash01(i, 91)
        x = POD_X + sd * (150 + 260 * ease_out(k) * (0.6 + 0.4 * h)) * s
        y = POD_Y - 128 * s - (40 + 220 * k) * s * (0.5 + 0.5 * h)
        r = (26 + 70 * ease_out(k)) * s
        core.circle(ctx, x, y, r)
        core.fill(ctx, (0.85, 0.97, 1.0, 0.42 * (1 - k)))


# ============================================================================
# the window onto the shaft: four tiers of pods behind shutter housings; a
# LOCKDOWN sign over the shaft; two pods pop and their creatures get out; then
# heavy hazard-striped steel shutters slam down tier by tier
# ============================================================================
WIN = M["window"]                       # (905, 380, 400, 420)
_TIER_TOP = (52, 124, 208, 304)         # px below the window top (far -> near)
_TIER_H = (72, 84, 96, 116)
_TIER_N = (7, 6, 6, 5)
_TIER_W = (0.84, 0.9, 0.97, 1.04)       # x window width
ESCAPE = {(3, 1): ("A", -1), (2, 4): ("B", 1)}   # (tier, pod) -> who, run direction
STEEL = "#5d6a76"
STEEL_DK = "#3d4853"
STEEL_LT = "#8796a3"


def _tier(r):
    x, y, w, h = WIN
    yt, th = y + _TIER_TOP[r], _TIER_H[r]
    tw, n = w * _TIER_W[r], _TIER_N[r]
    cx = x + w / 2
    sp = tw / n
    ph = 0.64 * th
    pw = 0.6 * ph
    hh = 0.15 * th
    py = yt + hh + 0.07 * th + ph / 2
    ly = yt + 0.88 * th
    pods = [(cx + (k + 0.5 - n / 2) * sp, py) for k in range(n)]
    return dict(r=r, yt=yt, th=th, tw=tw, cx=cx, sp=sp, ph=ph, pw=pw, hh=hh, py=py, ly=ly, pods=pods,
                x0=cx - tw / 2 - 10, x1=cx + tw / 2 + 10)


_TIERS = [_tier(r) for r in range(4)]


def _sleeper(ctx, px, py, pw, ph, seed):
    """A dark curled creature shape asleep in a pod (amorphous, a hint of an ear)."""
    sd = -1 if seed % 2 else 1
    by = py + ph * 0.2
    core.ellipse(ctx, px, by, pw * 0.36, ph * 0.13)
    core.ellipse(ctx, px + sd * pw * 0.2, by - ph * 0.09, pw * 0.16, ph * 0.1)
    core.fill(ctx, "#0e2a33")
    ctx.move_to(px + sd * pw * 0.26, by - ph * 0.15)
    ctx.line_to(px + sd * pw * 0.05, by - ph * 0.3)
    ctx.line_to(px + sd * pw * 0.12, by - ph * 0.12)
    ctx.close_path()
    core.fill(ctx, "#0e2a33")


def _win_static(c):
    """Everything in the window that never changes (cached)."""
    import cairocffi as cairo
    x, y, w, h = WIN
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgba(0, *core.hexc("#05121a"))
    g.add_color_stop_rgba(1, *core.hexc("#0f3943"))
    c.rectangle(x, y, w, h)
    c.set_source(g)
    c.fill()
    # the shaft's far wall: faint vertical ribs
    for i in range(9):
        xx = x + w * (0.06 + 0.11 * i)
        props.line(c, [(xx, y), (xx, y + h)], (0.3, 0.6, 0.65, 0.10), 6)
    core.radial_glow(c, x + w / 2, y + h * 0.72, w * 0.62, core.PAL["power"], 0.20)
    # the LOCKDOWN sign's housing (unlit)
    bx, by, bw, bh = x + 52, y + 9, w - 104, 36
    props.rect(c, bx - 4, by - 4, bw + 8, bh + 8, "#232b33", 2.5, r=6)
    props.hazard_band(c, bx, by, 26, bh, step=20, lw=1.5)
    props.hazard_band(c, bx + bw - 26, by, 26, bh, step=20, lw=1.5)
    props.rect(c, bx + 30, by + 3, bw - 60, bh - 6, "#2a0a10", 1.5, r=3)
    for g_ in _TIERS:
        # back wall band + ledge
        c.rectangle(x - 10, g_["yt"] + g_["hh"], w + 20, g_["ly"] - g_["yt"] - g_["hh"])
        core.fill(c, (0.02, 0.10, 0.13, 0.55))
        props.rect(c, x - 10, g_["ly"], w + 20, g_["yt"] + g_["th"] - g_["ly"], "#29505a", 0)
        props.line(c, [(x - 10, g_["ly"] + 1), (x + w + 10, g_["ly"] + 1)], "#6fb3b8", 1.5 + g_["r"] * 0.5)
        pw, ph = g_["pw"], g_["ph"]
        lw = 1.2 + 0.35 * g_["r"]
        for k, (px, py) in enumerate(g_["pods"]):
            # capsule with a teal-lit interior
            core.rrect(c, px - pw / 2, py - ph / 2, pw, ph, pw / 2)
            props.fs(c, core.mixc("#11555a", "#3ff2e0", 0.38 + 0.08 * g_["r"]), lw)
            core.rrect(c, px - pw * 0.34, py - ph * 0.36, pw * 0.68, ph * 0.72, pw * 0.34)
            core.fill(c, (0.75, 1.0, 0.95, 0.18))
            if (g_["r"], k) not in ESCAPE:
                _sleeper(c, px, py, pw, ph, k + 3 * g_["r"])
            # caps
            props.rect(c, px - pw * 0.6, py - ph / 2 - ph * 0.08, pw * 1.2, ph * 0.13, STEEL_DK, lw * 0.8,
                       r=2)
            props.rect(c, px - pw * 0.6, py + ph / 2 - ph * 0.06, pw * 1.2, ph * 0.13, STEEL_DK, lw * 0.8,
                       r=2)
        # the shutter housing: a heavy steel beam over the tier (the shutter rolls out of it)
        hx0, hx1 = g_["x0"] - 4, g_["x1"] + 4
        props.rect(c, hx0, g_["yt"], hx1 - hx0, g_["hh"], STEEL_DK, lw, r=2)
        props.line(c, [(hx0 + 3, g_["yt"] + 2.5), (hx1 - 3, g_["yt"] + 2.5)], STEEL_LT, 1.2)
        props.line(c, [(hx0, g_["yt"] + g_["hh"] - 1.5), (hx1, g_["yt"] + g_["hh"] - 1.5)], "#11171d", 2.5)
        for kk in range(7):
            core.circle(c, hx0 + (hx1 - hx0) * (0.08 + 0.14 * kk), g_["yt"] + g_["hh"] * 0.5, 1.3 + 0.3 * g_["r"])
        core.fill(c, STEEL_LT)
        # lock lamps (dark until the tier is sealed)
        for lx in (hx0 + 10, hx1 - 10):
            core.circle(c, lx, g_["yt"] + g_["hh"] * 0.5, 2.6 + 0.6 * g_["r"])
            props.fs(c, "#3a0d14", 1.0)


def _pods_open(T, t):
    """0..0.45: every pod's glass door creeps up after the release (heavy, slow)."""
    return 0.45 * smoothstep(seg(t, T.open0, T.open0 + 2.8))


def _row_shutter(T, t, r):
    """Shutter r: 0 = up in its housing .. 1 = down; a fast drop + a bounce."""
    t1 = T.rows[r]
    if t < t1 - 0.13:
        return 0.0
    if t < t1:
        return ease_in(seg(t, t1 - 0.13, t1))
    return 1.0 - 0.09 * math.sin(math.pi * seg(t, t1, t1 + 0.12)) * (1 - 0.0) \
        - 0.03 * math.sin(math.pi * seg(t, t1 + 0.12, t1 + 0.22))


def _esc_times(T, who):
    return T.popA if who == "A" else T.popB


def _esc_creature(T, t, g_, k, who, d):
    """(x, y, pose, flip, airborne) of an escaping creature, or None."""
    t0 = _esc_times(T, who)
    px, py = g_["pods"][k]
    s = g_["pw"] / 480.0
    if t < t0 + 0.06:
        return None
    gy = g_["ly"] + 1
    if t < t0 + 0.2:                      # crouched in the open pod, gathering
        return px, py + g_["ph"] * 0.32, "crouch", d < 0, False, s
    if t < t0 + 0.42:                     # leaps out onto the ledge
        u = seg(t, t0 + 0.2, t0 + 0.42)
        x = lerp(px, px + d * g_["sp"] * 0.45, u)
        y = lerp(py + g_["ph"] * 0.1, gy - 112 * s, u) - 40 * s * 6 * math.sin(math.pi * u) * 0.25
        return x, y, "leap", d < 0, True, s
    x0 = px + d * g_["sp"] * 0.45
    x1 = (WIN[0] - 70) if d < 0 else (WIN[0] + WIN[2] + 70)
    xx, yy, pose, air = _bound(t, t0 + 0.42, x0, x1, 2, 0.55, gy, s)
    if t > t0 + 0.97:
        return None
    return xx, yy, pose, d < 0, air, s


def _draw_banner(ctx, T, t, lit_scale=1.0):
    x, y, w, h = WIN
    if t < T.lock_on:
        return
    bx, by, bw, bh = x + 52, y + 9, w - 104, 36
    on = smoothstep(seg(t, T.lock_on, T.lock_on + 0.12))
    p = 0.5 + 0.5 * math.cos(math.tau * (t - T.lock_on) / 0.9)       # smooth 0.9 s flash (no strobe)
    a = on * (0.45 + 0.55 * p) * lit_scale
    props.rect(ctx, bx + 30, by + 3, bw - 60, bh - 6, core.mixc("#2a0a10", "#c4142c", a), 1.5, r=3)
    core.radial_glow(ctx, x + w / 2, by + bh / 2, 150, core.PAL["danger"], 0.45 * a)
    core.text(ctx, "LOCKDOWN", x + w / 2, by + bh * 0.5 + 9, 25, core.mixc("#5a1a22", "#fff1f2", a), "black")


def window_fn_for(T):
    x, y, w, h = WIN

    def window_fn(ctx, x_, y_, w_, h_, t):
        core.cached(ctx, "s07_window_static", x, y, w, h, _win_static)
        op = _pods_open(T, t)
        # glass doors (slide up into the top caps), escapee pods pop wide open
        for g_ in _TIERS:
            r = g_["r"]
            pw, ph = g_["pw"], g_["ph"]
            for k, (px, py) in enumerate(g_["pods"]):
                esc = ESCAPE.get((r, k))
                o = op
                if esc:
                    t0 = _esc_times(T, esc[0])
                    o = max(o, clamp(ease_out_back(seg(t, t0, t0 + 0.16), 1.6), 0.0, 1.06))
                    if t < t0 + 0.06:
                        _sleeper(ctx, px, py, pw, ph, k + 3 * r)
                if o > 0.01:   # the open gap at the bottom of the capsule: brighter interior light
                    core.rrect(ctx, px - pw * 0.42, py + ph / 2 - ph * o * 0.95, pw * 0.84, ph * o * 0.95,
                               min(pw * 0.42, ph * o * 0.45))
                    core.fill(ctx, (0.72, 1.0, 0.96, 0.32))
                ctx.save()
                core.rrect(ctx, px - pw / 2, py - ph / 2, pw, ph, pw / 2)
                ctx.clip()
                dy = -ph * o
                core.rrect(ctx, px - pw * 0.44, py - ph * 0.46 + dy, pw * 0.88, ph * 0.92, pw * 0.44)
                core.fill(ctx, (0.80, 1.0, 0.98, 0.20))
                core.poly(ctx, [(px - pw * 0.30, py - ph * 0.36 + dy), (px - pw * 0.14, py - ph * 0.40 + dy),
                                (px - pw * 0.14, py + ph * 0.10 + dy), (px - pw * 0.30, py + ph * 0.16 + dy)])
                core.fill(ctx, (1, 1, 1, 0.30))
                ctx.restore()
                if esc and seg(t, _esc_times(T, esc[0]), _esc_times(T, esc[0]) + 0.25) not in (0.0, 1.0):
                    kk = seg(t, _esc_times(T, esc[0]), _esc_times(T, esc[0]) + 0.25)
                    core.circle(ctx, px, py + ph * 0.3, pw * (0.4 + 0.8 * kk))
                    core.stroke(ctx, (1, 1, 1, 0.8 * (1 - kk)), 1.5 + 2 * (1 - kk))
        # the two that get out
        for (r, k), (who, d) in ESCAPE.items():
            g_ = _TIERS[r]
            cr = _esc_creature(T, t, g_, k, who, d)
            if cr is None:
                continue
            cx_, cy_, pose, flip, air, s = cr
            CR.draw_specimen(ctx, cx_, cy_, s, t, form=1.0, pose=pose, expr="wide", flip=flip,
                             look=(-0.6 if flip else 0.6, 0.0), glow=1.6, ears=0.95, pose_t=t - _esc_times(T, who))
        # LOCKDOWN sign over the shaft
        _draw_banner(ctx, T, t)
        # the shutters: thick corrugated steel, hazard stripes on the leading edge
        for g_ in _TIERS:
            r = g_["r"]
            sh = _row_shutter(T, t, r)
            if sh <= 0.0:
                continue
            x0, x1 = g_["x0"], g_["x1"]
            top = g_["yt"] + g_["hh"]
            full = g_["ly"] - top
            bot = top + full * sh
            hz = 0.15 * g_["th"]
            lw = 1.4 + 0.4 * r
            ctx.rectangle(x0, top, x1 - x0, bot - top)
            core.fill(ctx, STEEL)
            step = 0.11 * g_["th"]
            yy = bot - hz - step * 0.5
            while yy > top + 1:
                props.line(ctx, [(x0, yy), (x1, yy)], STEEL_DK, 1.6 + 0.3 * r)
                props.line(ctx, [(x0, yy + 1.8), (x1, yy + 1.8)], STEEL_LT, 0.9)
                yy -= step
            for kk in range(1, 4):
                xx = lerp(x0, x1, kk / 4)
                props.line(ctx, [(xx, top), (xx, bot - hz)], STEEL_DK, 1.2 + 0.2 * r)
            props.hazard_band(ctx, x0, bot - hz, x1 - x0, hz, step=hz * 1.5, lw=0)
            props.line(ctx, [(x0, bot - hz), (x1, bot - hz)], props.INK, lw)
            ctx.rectangle(x0, top, x1 - x0, bot - top)
            core.stroke(ctx, props.INK, lw)
            if sh >= 0.9:
                # locked: the lamps go red
                la = smoothstep(seg(t, T.rows[r] + 0.08, T.rows[r] + 0.2))
                for lx in (g_["x0"] + 6, g_["x1"] - 6):
                    core.circle(ctx, lx, g_["yt"] + g_["hh"] * 0.5, 2.6 + 0.6 * r)
                    core.fill(ctx, core.mixc("#3a0d14", "#ff3b5c", la))
                    core.radial_glow(ctx, lx, g_["yt"] + g_["hh"] * 0.5, 14 + 3 * r, core.PAL["danger"], 0.5 * la)
        # sparks where each shutter lands (<= 2 tiers alive: <= 20 streaks)
        for g_ in _TIERS:
            t1 = T.rows[g_["r"]]
            if t1 <= t < t1 + 0.55:
                for j, (sx, ang) in enumerate(((g_["x0"] + 22, -2.3), (g_["x1"] - 22, -0.85))):
                    fx.sparks(ctx, sx, g_["ly"], t, t1, seed=g_["r"] * 7 + j, s=0.2 + 0.03 * g_["r"], n=5,
                              angle=ang, spread=1.5, dur=0.5, speed=620)
    return window_fn


MON_DELAY = 0.45     # the monitors' shutters land just after the window's


def _lock_overlay(ctx, T, x, y, w, h, t):
    """LOCKDOWN flashing across a monitor after the button."""
    if t < T.lock_on:
        return
    on = smoothstep(seg(t, T.lock_on, T.lock_on + 0.1))
    p = 0.5 + 0.5 * math.cos(math.tau * (t - T.lock_on) / 0.9)
    a = on * (0.55 + 0.45 * p)
    bh = h * 0.26
    ctx.rectangle(x, y + h * 0.5 - bh / 2, w, bh)
    core.fill(ctx, core.alpha("#b0122a", 0.85 * a))
    core.text(ctx, "LOCKDOWN", x + w / 2, y + h * 0.5 + bh * 0.3, bh * 0.8, core.alpha("#fff1f2", a), "black")


def _mon_slab(ctx, x0, y0, w, hfull, sh, lw=1.2):
    if sh <= 0:
        return
    hh = hfull * sh
    ctx.rectangle(x0, y0, w, hh)
    core.fill(ctx, STEEL)
    hz = min(hfull * 0.2, hh)
    props.hazard_band(ctx, x0, y0 + hh - hz, w, hz, step=max(4.0, hz * 1.5), lw=0)
    ctx.rectangle(x0, y0, w, hh)
    core.stroke(ctx, props.INK, lw)


# --- monitors: the "pods" feeds get the same cascade + LOCKDOWN
def _mon_pods(T, i):
    base = sets._cr2_feed

    def fn(ctx, x, y, w, h, t):
        base(ctx, x, y, w, h, "pods", sets._CR2_FEEDS[i][1])
        op = _pods_open(T, t) / 0.45
        for r in range(3):
            sh = _row_shutter(T, t - MON_DELAY, min(3, r + 1))
            py = y + h * (0.2 + 0.3 * r)
            if op > 0.01 and sh < 0.5:
                for k in range(6):
                    px = x + w * (0.1 + 0.17 * k) + (w * 0.08 if r % 2 else 0)
                    props.line(ctx, [(px - w * 0.03, py + h * 0.08), (px + w * 0.03, py + h * 0.08)],
                               (1, 1, 1, 0.8 * op), 1 + 1.5 * op)
            _mon_slab(ctx, x, py - h * 0.12, w, h * 0.24, sh)
        _lock_overlay(ctx, T, x, y, w, h, t)
    return fn


def _mon_catwalk(T, i, label):
    base = sets._cr2_feed

    def fn(ctx, x, y, w, h, t):
        base(ctx, x, y, w, h, "catwalk", label)
        op = _pods_open(T, t) / 0.45
        sh = _row_shutter(T, t - MON_DELAY, 3)
        if op > 0.01 and sh < 0.5:
            for k in range(5):
                px = x + w * (0.12 + 0.2 * k)
                props.line(ctx, [(px - w * 0.05, y + h * 0.6), (px + w * 0.05, y + h * 0.6)],
                           (1, 1, 1, 0.85 * op), 1.5 + 2 * op)
        _mon_slab(ctx, x, y + h * 0.16, w, h * 0.56, sh, 1.6)
        _lock_overlay(ctx, T, x, y, w, h, t)
    return fn


# --- the hatch camera (CAM 07): live, then (at the watch beat) rewound and
# frozen on Emb glancing back at the hatch
FEED_X0, FEED_Y0, FEED_W = -300.0, 600.0, 640.0
FACE_ZOOM = 1.28                       # the digital push-in on his face while frozen


def feed_time(T, t):
    if t < T.rew0:
        return t
    if t < T.rew1:
        return lerp(T.rew0, T.t_freeze, ease_in_out(seg(t, T.rew0, T.rew1)) ** 0.85)
    return T.t_freeze


def _feed_zoom(T, t):
    return lerp(1.0, FACE_ZOOM, ease_in_out(seg(t, T.rew1 + 0.1, T.rew1 + 0.9)))


def _hatch_world(c, T, info, tt):
    """The maintenance-hatch corner of the room at (feed) time tt."""
    hop = hatch_open(T, tt)
    sets.control_room(c, tt, "bg", hatch_open=hop, alarm=0.0, case_broken=1.0, lever=1.0,
                      pressed=1.0, chair_turn=1.0)
    es, ts = emb_state(T, info, tt), tired_state(T, info, tt)
    cs, bb = cur_state(T, info, tt), baby_state(T, info, tt)
    _hatch_people(c, T, info, tt, es, cs, ts, bb)
    if es["visible"] and es.get("clip") != "hatch" and not es["front_of_panel"]:
        _draw_emb(c, info, tt, es)
    if hop > 0.02:
        sets.control_room(c, tt, "fg", hatch_open=hop, alarm=0.0, alarm_tint=False, parts=("hatch",))
    if es["visible"] and es.get("clip") != "hatch" and es["front_of_panel"]:
        _draw_emb(c, info, tt, es)
    return es


def _feed_xform(T, info, x, y, w, h, zoom):
    """(scale, world x0, world y0) mapping the hatch-cam window into the rect."""
    k = w / FEED_W
    wh = FEED_W * h / w
    cx0, cy0 = FEED_X0 + FEED_W / 2, FEED_Y0 + wh / 2
    fxw, fyw = EMB_X + 40, 830.0              # Emb's face (where the push-in goes)
    q = (zoom - 1.0) / (FACE_ZOOM - 1.0) if FACE_ZOOM > 1 else 0.0
    cx = lerp(cx0, lerp(cx0, fxw, 0.8), q)
    cy = lerp(cy0, lerp(cy0, fyw, 0.8), q)
    kz = k * zoom
    return kz, cx - (w / 2) / kz, cy - (h / 2) / kz


def _hatch_feed_draw(T, info, zoom):
    def draw_feed(c, x, y, w, h, tt):
        kz, wx0, wy0 = _feed_xform(T, info, x, y, w, h, zoom)
        c.save()
        c.translate(x, y)
        c.scale(kz, kz)
        c.translate(-wx0, -wy0)
        _hatch_world(c, T, info, tt)
        c.rectangle(wx0, wy0, w / kz, h / kz)
        core.fill(c, (1, 1, 1, 0.22))
        c.restore()
    return draw_feed


def _id_bracket(ctx, T, info, x, y, w, h, zoom, t):
    """A red ID bracket over Emb's face on the frozen frame."""
    a = smoothstep(seg(t, T.rew1 + 0.35, T.rew1 + 0.55))
    if a <= 0:
        return
    kz, wx0, wy0 = _feed_xform(T, info, x, y, w, h, zoom)
    fx_, fy_ = (EMB_X + 30 - wx0) * kz + x, (812 - wy0) * kz + y
    s = (1.25 - 0.25 * a) * kz
    bw, bh = 120 * s, 150 * s
    L_ = 30 * s
    col = core.alpha("#ff3b5c", 0.95 * a)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = fx_ + sx * bw / 2, fy_ + sy * bh / 2
            props.line(ctx, [(cx - sx * L_, cy), (cx, cy), (cx, cy - sy * L_)], col, max(1.5, 5 * s / kz * kz * 0.6))


def _rew_marks(ctx, T, x, y, w, h, t):
    """REW / PAUSE indicator (top-right) + rewind tracking bands."""
    sc = w / 600.0
    if t < T.rew0:
        return
    ix, iy = x + w - 70 * sc, y + 52 * sc
    if t < T.rew1:
        for k in range(2):           # two triangles: rewind
            ox = ix - 34 * sc * k
            core.poly(ctx, [(ox, iy - 15 * sc), (ox, iy + 15 * sc), (ox - 26 * sc, iy)])
            core.fill(ctx, "#eafff4")
        core.text(ctx, "REW", ix - 76 * sc, iy + 9 * sc, 26 * sc, "#eafff4", "mono", "right")
        for k in range(2):           # rolling tracking bands
            yy = y + h * ((seg(t, T.rew0, T.rew1) * 2.6 + 0.45 * k) % 1.0)
            ctx.rectangle(x, yy, w, h * 0.05)
            core.fill(ctx, (0.85, 1.0, 0.92, 0.22))
            ctx.rectangle(x, yy + h * 0.012, w, h * 0.008)
            core.fill(ctx, (1, 1, 1, 0.35))
    else:
        a = 0.65 + 0.35 * math.cos(math.tau * (t - T.rew1) / 1.4)
        for k in range(2):           # two bars: pause
            ctx.rectangle(ix - 30 * sc + 18 * sc * k, iy - 15 * sc, 10 * sc, 30 * sc)
        core.fill(ctx, core.alpha("#eafff4", a))
        core.text(ctx, "PAUSE", ix - 46 * sc, iy + 9 * sc, 26 * sc, core.alpha("#eafff4", a), "mono", "right")


HATCH_MON = 10      # the monitor beside her chair (upper right of her face)


def draw_hatch_feed(ctx, T, info, x, y, w, h, t):
    """The CAM 07 hatch feed at scene time t (live -> rewind -> frozen)."""
    tt = feed_time(T, t)
    zoom = _feed_zoom(T, t)
    frozen = t >= T.rew1 + 0.95
    fx.monitor_feed(ctx, x, y, w, h, tt, _hatch_feed_draw(T, info, zoom), style="night",
                    label="CAM 07  MAINT.", rec=t < T.rew0, res=0.5,
                    cache_key=("s07_freeze", round(zoom, 3)) if frozen else None)
    _id_bracket(ctx, T, info, x, y, w, h, zoom, t)
    _rew_marks(ctx, T, x, y, w, h, t)


def _hatch_mon_fn(T, info):
    pods = _mon_pods(T, HATCH_MON)

    def fn(ctx, x, y, w, h, t):
        if t < T.hatch - 0.3:
            pods(ctx, x, y, w, h, t)
            return
        draw_hatch_feed(ctx, T, info, x, y, w, h, t)
    return fn


def alarm_at(T, t):
    return smoothstep(seg(t, T.al0, T.al0 + 0.35))


def hatch_open(T, t):
    if t < T.burst:
        v = 0.0
    elif t < T.slam0:
        v = clamp(ease_out_back(seg(t, T.burst, T.burst + 0.32), 1.2))
    else:
        v = 1.0 - ease_in(seg(t, T.slam0, T.hatch))
    # work around sets._cr2_hatch_panel: cos(opening*95deg)**0.5 goes complex for
    # opening in (0.947, 1) and raises; snap that last 5 degrees of swing
    return 1.0 if v > 0.94 else v


# ============================================================================
# drawing the world
# ============================================================================
def _clip_hatch(ctx, feet_y, depth=0.0):
    hx, ht, hw, hh = HATCH
    y1 = lerp(max(ht + hh, feet_y + 40), ht + hh, smoothstep(clamp(depth * 3)))
    ctx.rectangle(hx, ht, hw, y1 - ht)
    ctx.clip()


def _deep(st):
    """Someone receding up the crawlway: smaller, higher, toward the centre."""
    d = st.get("depth", 0.0)
    if d <= 0:
        return st, 1.0
    q = dict(st)
    q["x"] = lerp(st["x"], HATCH_CX, d)
    q["y"] = lerp(st["y"], HATCH[1] + HATCH[3] - 60, d)
    return q, lerp(1.0, 0.5, d)


def _draw_tired(ctx, T, info, t, st, baby_st):
    def hold(c, side, hx, hy, ang):
        if not baby_st["held"]:
            return
        if side == "both":
            bx, by, fc = hx + 4, hy - 65 * SB, 0.3
        else:
            bx, by, fc = hx + 4, hy - 12 * SB, 0.8
        CR.draw_specimen(c, bx, by, SB, t, baby=True, pose="held", expr=baby_st["expr"], flip=True,
                         tail_curl=baby_st["tail_curl"], look=(-0.2, 0.1), glow=1.7, face=fc)
    kw = dict(pose=st["pose"], pose_t=st["pose_t"], turn=st["turn"], expr=st["expr"], face=st["face"],
              look=st["look"], blink=st["blink"], power=st["power"], outfit="sewer", bandage=True,
              headphones=None, hood=0.0, reach=st["reach"], mouth=info.mouth("tired", t),
              sweat=st.get("sweat", 0.0))
    if baby_st["held"]:
        kw["hold"] = hold
        if st["hold_mode"] == "r":
            kw["hold_sides"] = "r"
        else:
            kw["hold_layer"] = "front"
    return human.draw_person(ctx, "tired", st["x"], st["y"], SP, t, **kw)


def _draw_cur(ctx, t, st):
    return CR.draw_specimen(ctx, st["x"], st["y"], SC, t, form=1.0, pose=st["pose"], expr=st["expr"],
                            look=st["look"], ears=st["ears"], tilt=st["tilt"], face=st["face"],
                            flip=st["flip"], tail_curl=st["tail_curl"], pose_t=st["pose_t"],
                            blink=st["blink"], pose_from=st["pose_from"], pose_mix=st["pose_mix"],
                            glow=1.25)


def _draw_baby(ctx, t, st):
    return CR.draw_specimen(ctx, st["x"], st["y"], SB, t, baby=True, pose=st["pose"], expr=st["expr"],
                            look=st["look"], flip=st["flip"], roll=st["roll"], pose_t=st["pose_t"],
                            ears=st["ears"], tilt=st["tilt"], tail_curl=st["tail_curl"], glow=1.5)


def _draw_emb(ctx, info, t, st):
    return human.draw_person(ctx, "embar", st["x"], st["y"], SP, t, pose=st["pose"], pose_t=st["pose_t"],
                             turn=st["turn"], expr=st["expr"], face=st["face"], look=st["look"],
                             reach=st["reach"], mouth=st.get("mouth", (0.0, 0.0)), blush=st["blush"],
                             sweat=st["sweat"], pocket_side="near")


def _draw_boss(ctx, info, t, st):
    gy = FEET
    return human.draw_person(ctx, "boss", M["chair"][0], gy, SP, t, pose=st["pose"], turn=st["turn"],
                             expr=st["expr"], face=st["face"], look=st["look"], reach=st["reach"],
                             mouth=st["mouth"], blink=st["blink"])


def _door_leaks(ctx, T, t):
    """Guards coming: flashlight light leaking under and between the doors,
    with the shadows of running feet crossing the gap."""
    dx0, dt0, dw, dh = M["doors"]
    k = smoothstep(seg(t, T.al0 + 0.3, T.al0 + 1.6)) * (0.75 + 0.25 * math.sin(t * 5.3) * math.sin(t * 2.1))
    yb = dt0 + dh
    ctx.rectangle(dx0 + 6, yb - 7, dw - 12, 7)
    core.fill(ctx, core.alpha("#ffd9a0", 0.85 * k))
    core.ellipse(ctx, dx0 + dw / 2, yb + 4, dw * 0.55, 16)
    core.fill(ctx, core.alpha("#ffcf8a", 0.18 * k))
    for i in range(3):
        u = ((t - T.al0) * (0.55 + 0.2 * i) + 0.31 * i) % 1.0
        fx_ = dx0 + 6 + (dw - 30) * u
        ctx.rectangle(fx_, yb - 7, 22, 7)
    core.fill(ctx, core.alpha("#0a0a10", 0.8 * k))
    sx = dx0 + dw / 2
    sweep = 0.5 + 0.5 * math.sin(t * 3.1)
    ctx.rectangle(sx - 1.5, dt0 + 20 + 500 * sweep, 3, 160)
    core.fill(ctx, core.alpha("#ffe2b0", 0.7 * k))


def _alarm_p(t):
    return 0.5 + 0.5 * math.sin(math.tau * t / 1.2)


def _char_shade(c, t, al, pod_glow):
    """Light on the characters: a light darkness wash, cool monitor light from
    the right, the teal window, the pod's teal glow, and the red alarm."""
    vx0, vy0, vx1, vy1 = c.clip_extents()
    c.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
    core.fill(c, core.alpha("#04070d", 0.30 + 0.06 * al))
    core.radial_glow(c, 1700, 640, 900, "#5fd8ff", 0.20 * (1 - 0.5 * al))
    core.radial_glow(c, 1105, 820, 620, core.PAL["power"], 0.14 * (1 - 0.6 * al))
    if pod_glow > 0:
        core.radial_glow(c, POD_X - 60, POD_Y - 120, 600, core.PAL["power"], 0.13 * pod_glow)
    if al > 0.003:
        c.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
        core.fill(c, core.alpha("#c0142a", al * (0.16 + 0.07 * _alarm_p(t))))


def _boss_feed_light(c, t, k):
    """The green CCTV light from the monitor beside her on her face (ending)."""
    if k > 0:
        mx, my, mw, mh = M["monitors"][HATCH_MON]
        core.radial_glow(c, mx + mw * 0.3, my + mh * 0.6, 420, "#7dffb0", 0.16 * k)


def _alarm_tint(ctx, t, al, a0=0.20, a1=0.08):
    if al <= 0.003:
        return
    vx0, vy0, vx1, vy1 = ctx.clip_extents()
    ctx.rectangle(vx0, vy0, vx1 - vx0, vy1 - vy0)
    core.fill(ctx, core.alpha("#9a0c1c", al * (a0 + a1 * _alarm_p(t))))


def _visible_x(view, x0, x1):
    return not (x1 < view[0] or x0 > view[2])


def _hatch_people(ctx, T, info, t, es, cs, ts, bb):
    """Whoever is in the hatch opening (clipped to it; the open panel goes over them)."""
    for who, st0 in (("emb", es), ("cur", cs), ("tired", ts)):
        if st0.get("clip") == "hatch" and st0["visible"]:
            st, k = _deep(st0)
            ctx.save()
            _clip_hatch(ctx, st0["y"], st0.get("depth", 0.0))

            def fn(c, who=who, st=st, k=k):
                ox, oy = st["x"], st["y"]
                c.save()
                c.translate(ox, oy)
                c.scale(k, k)
                c.translate(-ox, -oy)
                if who == "emb":
                    _draw_emb(c, info, t, st)
                elif who == "cur":
                    _draw_cur(c, t, st)
                else:
                    _draw_tired(c, T, info, t, st, bb)
                c.restore()
            sets.dimmed(ctx, (HATCH[0] - 10, HATCH[1] - 10, HATCH[2] + 20, 900),
                        lerp(0.4, 0.92, st0.get("depth", 0.0)), fn)
            ctx.restore()


def draw_world(ctx, T, info, t, cam):
    al = alarm_at(T, t)
    bs = boss_state(T, info, t)
    ts = tired_state(T, info, t)
    cs = cur_state(T, info, t)
    bb = baby_state(T, info, t)
    es = emb_state(T, info, t)
    lever = lever_at(T, t) if t >= T.pull else 0.0
    broken = 1.0 if t >= T.hit else 0.0
    hop = hatch_open(T, t)
    room = dict(case_broken=broken, lever=lever, pressed=bs["pressed"], alarm=al, alarm_tint=False,
                hatch_open=hop, chair_turn=bs["chair_turn"], window_fn=window_fn_for(T),
                monitor_fns={0: _mon_catwalk(T, 0, "CAM 02"), 3: _mon_catwalk(T, 3, "CAM 01  SHAFT A"),
                             4: _mon_pods(T, 4), 7: _mon_pods(T, 7), HATCH_MON: _hatch_mon_fn(T, info)})
    sets.control_room(ctx, t, "bg", **room)
    _alarm_tint(ctx, t, al)
    view = ctx.clip_extents()
    if t > T.al0 + 0.3 and _visible_x(view, 420, 800):
        _door_leaks(ctx, T, t)
    _hatch_people(ctx, T, info, t, es, cs, ts, bb)
    # the tiny pod (the baby sleeps inside until it tumbles out)
    if _visible_x(view, POD_X - 200, POD_X + 200):
        inside = None
        if bb["inside"]:
            def inside(c):
                CR.draw_specimen(c, 0, -122 * POD_S + 0, SB, t, baby=True, pose="curl",
                                 expr=bb["expr"], flip=True)
        draw_joy_pod(ctx, T, t, inside)
    # the haul: his strength glows teal around him (soft, behind)
    if ts["aura"] > 0.01 and ts["visible"]:
        a = ts["aura"] * (0.85 + 0.15 * math.sin(t * 9.0))
        core.radial_glow(ctx, ts["x"] + 70, ts["y"] - 560, 330, core.PAL["power"], 0.30 * a)
        core.radial_glow(ctx, H_UP[0] - 20, lerp(H_UP[1], H_DN[1], lever) + 10, 170, "#bffff8", 0.30 * a)
    pod_glow = 0.0 if not _visible_x(view, POD_X - 600, POD_X + 600) else 1.0
    with sets.shaded(ctx, _char_shade, t, al, pod_glow):
        if _visible_x(view, 1450, 1950):
            _boss_feed_light(ctx, t, smoothstep(seg(t, T.hatch - 0.3, T.hatch)))
            _draw_boss(ctx, info, t, bs)
        if es["visible"] and es.get("clip") != "hatch" and not es["front_of_panel"] and \
                _visible_x(view, es["x"] - 200, es["x"] + 200):
            _draw_emb(ctx, info, t, es)
        order = []
        if ts["visible"] and ts.get("clip") != "hatch":
            order.append((ts["y"], 0, "tired"))
        if cs["visible"] and cs.get("clip") != "hatch":
            order.append((cs["y"] + (112 * SC if cs["airborne"] else 0), 1, "cur"))
        if not bb["inside"] and not bb["held"]:
            order.append((bb["y"] + 10, 2, "baby"))
        for _, _, who in sorted(order):
            if who == "tired" and _visible_x(view, ts["x"] - 260, ts["x"] + 300):
                _draw_tired(ctx, T, info, t, ts, bb)
            elif who == "cur" and _visible_x(view, cs["x"] - 300, cs["x"] + 300):
                _draw_cur(ctx, t, cs)
            elif who == "baby":
                _draw_baby(ctx, t, bb)
    if _visible_x(view, 1450, 1950):
        sets.control_room(ctx, t, "fg", chair_turn=bs["chair_turn"], alarm=al, alarm_tint=False,
                          parts=("chair",))
    if hop > 0.02 and _visible_x(view, -100, 600):
        # the open hatch panel (over whoever goes through), tinted by the alarm
        import cairocffi as cairo
        ctx.push_group()
        sets.control_room(ctx, t, "fg", hatch_open=hop, alarm=al, alarm_tint=False, parts=("hatch",))
        ctx.set_operator(cairo.OPERATOR_ATOP)
        _alarm_tint(ctx, t, al)
        ctx.pop_group_to_source()
        ctx.paint()
    if es["visible"] and es.get("clip") != "hatch" and es["front_of_panel"]:
        with sets.shaded(ctx, _char_shade, t, al, 0.0):
            _draw_emb(ctx, info, t, es)
    # ---- world fx
    if t >= T.hit:
        props.shards(ctx, t, T.hit, IMPACT[0] + 10, IMPACT[1], seed=4, n=9, s=SP, floor_y=FEET + 20,
                     dir=1, spread=0.8)
        props.shards(ctx, t, T.hit, IMPACT[0] - 10, IMPACT[1] + 10, seed=9, n=5, s=SP,
                     floor_y=FEET + 30, dir=-1, spread=0.5)
        fx.impact_star(ctx, IMPACT[0], IMPACT[1], 0.55, t, T.hit, dur=0.3, color="#e8fbff",
                       inner="#ffffff", spikes=9)
    if T.rows[-1] <= t < T.rows[-1] + 1.4 and _visible_x(view, WIN[0] - 50, WIN[0] + WIN[2] + 50):
        # the last (biggest) slam shakes dust off the window frame: the room reacts
        fx.plaster_dust(ctx, WIN[0] + WIN[2] / 2, WIN[1] - 6, 0.45, t, T.rows[-1], seed=7, width=340, n=8,
                        fall=260)
    if _visible_x(view, POD_X - 250, POD_X + 250):
        draw_pod_steam(ctx, T, t)
    if T.hatch <= t < T.hatch + 0.9:
        fx.dust_puff(ctx, HATCH[0] + HATCH[2] / 2, HATCH[1] + HATCH[3] + 10, 0.9, t, T.hatch, seed=5)


# ============================================================================
# the monitor insert (S11a, screen space): her hatch-cam monitor up close
# ============================================================================
INS = (96.0, 520.0, 830.0, 581.0)       # feed rect on screen (x, y, w, h); aspect = monitor 10's


def draw_insert(ctx, T, info, t):
    x, y, w, h = INS
    core.bg(ctx, "#0a1018")
    # neighbouring screens of the monitor wall, cut by the frame edges
    for (rx, ry, rw, rh, col) in ((-260, 560, 300, 500, "#123842"), (968, 600, 300, 470, "#1a2f3a"),
                                  (130, 150, 360, 300, "#0f2f38"), (560, 170, 420, 280, "#123842"),
                                  (150, 1190, 380, 300, "#152a33"), (590, 1190, 380, 300, "#0f2f38")):
        props.rect(ctx, rx - 18, ry - 18, rw + 36, rh + 36, "#1a2028", 4, r=10)
        ctx.rectangle(rx, ry, rw, rh)
        core.fill(ctx, col)
    core.radial_glow(ctx, x + w / 2, y + h / 2, 760, "#7dffb0", 0.10)
    # the bezel
    props.rect(ctx, x - 30, y - 30, w + 60, h + 60, "#1c232c", 6, r=16)
    props.rect(ctx, x - 10, y - 10, w + 20, h + 20, "#0b0f14", 3, r=10)
    draw_hatch_feed(ctx, T, info, x, y, w, h, t)
    core.circle(ctx, x + w + 2, y + h + 18, 5)
    core.fill(ctx, "#7cf2b0")
    # the room's alarm wash reaches the glass too
    al = alarm_at(T, t)
    if al > 0:
        ctx.rectangle(0, 0, core.W, core.H)
        core.fill(ctx, core.alpha("#9a0c1c", al * (0.10 + 0.05 * _alarm_p(t))))
    fx.vignette(ctx, 0.45)


# ============================================================================
# cameras
# ============================================================================
def _shake(t, t0, dur, amp, seed=3):
    return core.shake(t, t0, dur, amp, seed)


def camera_at(T, t):
    """(cx, cy, zoom, dx, dy) for the shot at time t."""
    dx = dy = 0.0
    if t < T.pull:                                     # S1 the smash
        z = lerp(1.46, 1.54, seg(t, 0.0, T.pull))
        cx, cy = 945.0, 1105.0
        dx, dy = _shake(t, T.hit, 0.32, 12)
    elif t < T.button:                                 # S2 the haul: close on face + hands
        k = smoothstep(seg(t, T.pull, T.give))
        cx, cy, z = lerp(1046, 1052, k), lerp(975, 955, k), lerp(2.0, 2.12, k)
        if t >= T.give - 0.05:                         # it gives: pull back with it
            kk = ease_out(seg(t, T.give - 0.05, T.clunk + 0.3))
            cx, cy, z = lerp(1052, 1010, kk), lerp(955, 1085, kk), lerp(2.12, 1.52, kk)
        dx, dy = _shake(t, T.clunk, 0.6, 14)
    elif t < T.shut:                                   # S3 the Boss presses LOCKDOWN
        k = seg(t, T.button, T.shut)
        cx, cy, z = 1600.0, lerp(1015, 1000, k), lerp(1.82, 1.9, k)
    elif t < T.pod:                                    # S4 the window: escape, then the shutters
        k = seg(t, T.shut, T.pod)
        cx, cy, z = 1105.0, lerp(626, 616, k), lerp(2.06, 2.16, k)
        for r, t1 in enumerate(T.rows):
            last = r == len(T.rows) - 1
            sx, sy = _shake(t, t1, 0.65 if last else 0.3, 13 if last else 6, seed=11 + r)
            dx += sx
            dy += sy
    elif t < T.pan0:                                   # S5a their faces fall
        k = seg(t, T.pod, T.pan0)
        cx, cy, z = lerp(642, 646, k), 1195.0, lerp(1.7, 1.76, k)
    elif t < T.baby:                                   # S5b pan to the pod
        k = ease_in_out(seg(t, T.pan0, T.pan1))
        cx, cy, z = lerp(646, 1240, k), lerp(1195, 1395, k), lerp(1.76, 2.3, k)
    elif t < T.al0:                                    # S6 the baby
        k = ease_in_out(seg(t, T.baby + 0.35, T.cur_land))
        cx, cy, z = lerp(1240, 1005, k), lerp(1395, 1430, k), lerp(2.3, 2.4, k)
    elif t < T.burst - 0.12:                           # S7 alarm: he swoops in for the baby
        k = seg(t, T.al0, T.burst)
        cx, cy, z = lerp(905, 915, k), lerp(1175, 1160, k), lerp(1.3, 1.36, k)
    elif t < T.run:                                    # S8 the hatch bursts: Emb
        k = seg(t, T.burst - 0.12, T.run)
        cx, cy, z = 160.0, lerp(1060, 1050, k), lerp(1.5, 1.56, k)
    elif t < T.hatch:                                  # S9 the run (tracking left)
        tx = tired_x_for_cam(T, t)
        cx = clamp(tx - 110, 175, 900)
        cy = lerp(1110, 1060, seg(900 - cx, 0, 725))
        z = 1.42
    elif t < T.watch:                                  # S10 the shut hatch
        k = seg(t, T.hatch, T.watch)
        cx, cy, z = 175.0, 1060.0, lerp(1.42, 1.3, smoothstep(k))
        sx, sy = _shake(t, T.hatch, 0.6, 12)
        dx, dy = sx, sy
    elif t < T.wcut:                                   # S11a the monitor insert (screen space)
        cx, cy, z = 1700.0, 900.0, 2.0
    elif t < T.wcut2:                                  # S11b the Boss MCU: "You too, Embarrassment."
        k = seg(t, T.wcut, T.wcut2)
        cx, cy, z = lerp(1758, 1754, k), lerp(1022, 1016, k), lerp(2.5, 2.58, k)
    else:                                              # S11c her + the monitor: numb
        k = smoothstep(seg(t, T.wcut2, T.end))
        cx, cy, z = lerp(1846, 1836, k), lerp(905, 925, k), lerp(1.98, 2.14, k)
    return cx, cy, z, dx, dy


def tired_x_for_cam(T, t):
    if t < T.run0:
        return TIRED_X2
    return max(_run_x(T, min(t, _tired_duck_t(T))), 300)


# ============================================================================
# scene API
# ============================================================================
def render(ctx, t, info):
    T = times(info)
    if T.watch <= t < T.wcut:
        draw_insert(ctx, T, info, t)
        return
    cx, cy, z, dx, dy = camera_at(T, t)
    core.bg(ctx, "#06090e")
    with core.camera(ctx, cx, cy, z, 0.0, 540 + dx, 960 + dy):
        draw_world(ctx, T, info, t, (cx, cy, z))


def SFX(info):
    T = times(info)
    ev = []
    # smash
    ev.append((max(0.0, T.p0 + 0.05), "cloth_rustle", -4, -0.1))
    ev.append((T.hit - 0.02, "glass_case_smash", 0, 0.1))
    # haul
    ev.append((T.pull + 0.05, "footstep", 0, -0.1))
    ev.append((T.grab - 0.05, "latch_click", 2, 0.1))
    ev.append((T.grab + 0.05, "lever_strain", 0, 0.1))
    ev.append((T.give - 0.9, "lever_strain", -3, 0.1))
    ev.append((T.give - 0.4, "power_surge", -10, 0.0))
    ev.append((T.clunk - 0.02, "lever_clunk", 0, 0.1))
    ev.append((T.open0, "pod_hiss", -12, -0.4))
    ev.append((T.open0 + 0.5, "pod_hiss", -12, 0.4))
    # LOCKDOWN
    ev.append((T.press - 0.02, "recorder_click", 3, 0.2))
    ev.append((T.press + 0.02, "latch_click", 0, 0.2))
    ev.append((T.shut - 0.05, "alarm", -12, 0.1))                 # the lockdown klaxon, once
    # two get out
    ev.append((T.popA - 0.02, "pod_hiss", -7, -0.3))
    ev.append((T.popA + 0.2, "critter_squeak", -6, -0.35))
    ev.append((T.popA + 0.4, "scurry", -9, -0.5))
    ev.append((T.popB - 0.02, "pod_hiss", -8, 0.35))
    ev.append((T.popB + 0.22, "critter_squeak", -7, 0.4))
    ev.append((T.popB + 0.42, "scurry", -10, 0.5))
    # the shutters, tier by tier: rattle down -> SLAM -> a heavy clang each
    pans = (-0.35, 0.3, -0.15, 0.0)
    gains = (-6, -5, -3, -1)
    for r, t1 in enumerate(T.rows):
        ev.append((t1 - 0.3, "shutter_slam", gains[r], pans[r]))
        ev.append((t1 - 0.01, "lever_clunk", gains[r] - 2, pans[r]))
    ev.append((T.rows[-1], "hatch_slam", -7, 0.0))                 # the last one booms
    # one pod: faces fall... then the hiss
    ev.append((T.pod + 0.25, "creature_chirp_sad", -6, -0.2))
    ev.append((T.hiss - 0.02, "pod_hiss", -3, 0.3))
    ev.append((T.hiss + 0.06, "ears_perk", 2, -0.2))
    # baby
    ev.append((T.roll0 + 0.3, "body_thud", -18, 0.2))
    ev.append((T.blink0 + 0.1, "baby_coo", -2, 0.1))
    ev.append((T.cur_go, "creature_chitter", -4, -0.2))
    ev.append((T.cur_go + 0.05, "scurry", -8, -0.1))
    ev.append((T.giggle, "baby_giggle", -1, 0.1))
    ev.append((T.nuzzle + 0.2, "creature_purr", 2, 0.0))
    # alarm + footsteps outside (left, coming closer)
    ev += sfx.loop_events("alarm_soft", T.al0, T.end, -2, 0.0)
    ev.append((T.al0 + 0.5, "footsteps_run", -17, -0.7))
    ev.append((T.al0 + 1.5, "footsteps_run", -13, -0.7))
    ev.append((T.L2.end + 0.2, "footsteps_run", -10, -0.6))
    ev.append((T.run + 1.3, "footsteps_run", -8, -0.6))
    # he swoops in for the baby
    ev.append((T.dash0, "footsteps_run", -6, 0.1))
    ev.append((T.dash1 + 0.05, "cloth_rustle", -2, 0.2))
    ev.append((T.scoop1 + 0.1, "baby_coo", -3, 0.15))
    # the hatch bursts open
    ev.append((T.burst - 0.02, "latch_click", 2, -0.5))
    ev.append((T.burst + 0.02, "whoosh", -10, -0.5))
    ev.append((T.burst + 0.3, "hatch_slam", -14, -0.6))           # the panel bangs open
    ev.append((T.emb_out1 - 0.05, "footstep", -2, -0.5))
    # the run
    ev.append((T.run0 - 0.1, "baby_giggle", -6, 0.0))
    ev.append((T.run0, "footsteps_run", -3, -0.2))
    ev.append((T.cur_run0, "scurry", -6, -0.3))
    ev.append((T.run + 0.8, "creature_chitter", -8, -0.5))
    ev.append((_tired_duck_t(T), "whoosh", -8, -0.5))
    ev.append((T.emb_duck0, "cloth_rustle", -4, -0.5))
    # SLAM (sync with the chaos cue's last hit)
    ev.append((T.hatch - 0.03, "hatch_slam", 0, -0.4))
    # watch: her chair turns a hair; the feed rewinds (tape zip) and pauses (click)
    ev.append((T.watch + 0.05, "chair_creak", -10, 0.2))
    ev.append((T.rew0, "smear_zip", -12, 0.1))
    ev.append((T.rew1, "mouse_click", -4, 0.1))
    return ev
