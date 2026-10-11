"""s01 - "The empty pod" (TIREDNESS Episode 2: Lights Out).

HushCorp gives the creatures bland, flattening names (SPECIMEN 001 / THING 1 ...); the creature
is anything but a thing: it hears the name and is visibly, intelligently offended.

Shot list (scene-local; every time is derived from info cues / lines / lip data):
  S1  [0, pod)            POD POV thumbnail: Curiosity's face through its empty pod's glass,
                          paw pressed to the glass, breath fog blooms and fades; slow push-in.
  S2  [pod, touch)        catwalk medium-wide: the camera tracks Tiredness walking in along the
                          pods (right -> left) and settles on the empty pod where Curiosity sits;
                          he stops; pupils pod -> creature -> pod (head follows); l01 (soft); on
                          "kept you" he crouches down to its level (camera eases down/in).
  S3  [touch, plate)      Curiosity close-up: slow nod with a slow blink, ears lowering a little;
                          its eyes go to the dusty nameplate (motivates the insert).
  S4  [plate, c5)         insert: the dusty plate; his bandaged hand comes in, the thumb wipes
                          left -> right revealing SPECIMEN 001 / THING 1; l02 "...Thing One."
                          read flatly over it.
  S5a [c5, c5b)           Curiosity CU, the plate beside it: a beat of hope (ears up), then it
                          processes the name: a slow contemptuous blink that opens on flat
                          half-lids, ears sagging, chin up, a tiny huff through the nose.
                          Name tag THING 1 / "according to HushCorp".
  S5b [c5b, c6)           Tiredness CU (crouched), the plate in frame: l03 "Wow. Creative."
                          deadpan, one brow up a hair, a slow judging blink; his eyes slide from
                          the plate to the creature.
  S6  [c6, plates)        crouched two-shot: it looks up at him, a shared look, it rolls its
                          eyes toward the plate (he follows), then back to him: a small smirk,
                          his faint smirk + tiny nod. They agree. He glances along the row.
  S7  [plates, frown)     his POV: slow pan from NOTHING TO SEE HERE over THING 2 / THING 3 to
                          the next NOTHING TO SEE HERE over THING 4 / THING 5, sleepers inside.
  S8  [frown, c10)        Tiredness CU (standing) under the wall camera: inner brows up, a lip
                          press, silence; l03b "...They're not things." quiet, to the creature
                          below (glassy eyes); a press after it. At "camera" the red LED blinks
                          on, the lens whirs and swivels to them; his pupils slide up, head follows.
  S10 [c10, reach)        control room: start on the big monitor (CCTV of the two looking up),
                          tilt down to the Boss in her chair, turned 3/4 to us, face clear; l04
                          into the lens.
  S11 [reach, c12)        medium: her eyes slide to the SHAFT POWER switch, her hand follows, a
                          finger rests on the toggle; l05 into the lens; slow push-in.
  S12 [c12, c13)          insert: she flips the switch OFF (click), lamp goes red.
  S13 [c13, end)          the shaft: lights die section by section from the top (chunks), pods to
                          embers; push in through the dark to two pairs of teal eyes, which blink.
"""
import math


from engine import core, sets, props, fx
from engine import human as H
from engine import creatures as CR
from engine.core import (seg, tween, lerp, clamp, smoothstep, ease_in_out, ease_out, ease_in,
                         ease_out_back, state_at)
from audio import sfx

W, HGT = core.W, core.H
CW = sets.CATWALK_MARKS
KM = sets.CONTROL_MARKS
FEET = CW["feet_y"]
S = 0.75                       # character scale in the catwalk / control room
CUR_X = 750                    # Curiosity sits left of its empty pod, facing right (glass / him)
TIR_X = 1240                   # where Tiredness stops (right of the pod), facing left
PLATE = CW["empty_plate"]      # (x, y, w, h) of Curiosity's nameplate (world)
PLATE_C = (PLATE[0] + PLATE[2] / 2, PLATE[1] + PLATE[3] / 2)
WALK_TURN = -0.55
# The rig's walk "speed" anchor / cycle_speed() is ~1.57x too slow for the visible planted foot
# (measured with foot strips at s 0.75, turn -0.55..-0.8: the shoe slides back at the documented
# speed). Use the measured no-slide speed instead.
WALK_FIX = 1.57
STAND_TURN2 = 0.3              # after he stands up again (looking along the row of pods)
WAVE_STILL = 1.0 / 1.7         # pose_t for "wave": paw fully raised, no swing
SWITCH = KM["power_switch"]
CHAIR_X = KM["chair"][0] - 60          # her chair, near the SHAFT POWER pedestal (drawn by this scene)
CHAIR_TURN = 0.9                       # props.boss_chair: 1 = facing camera, 0.5 = profile
BOSS_SEAT = (CHAIR_X, KM["boss_seat"][1])
BOSS_GY = H.ground_from_seat("boss", BOSS_SEAT[1], S)
BOSS_TURN = -0.35                      # 3/4 toward camera (slightly to the switch): face reads
SIGNS_X = (2235, 3215)                 # sets.catwalk: the two hanging NOTHING TO SEE HERE signs
ROLL_DUR = 1.0                         # Curiosity's eye-roll (the rig's 1.25 s roll, a bit brisker)

# crouch: both hands draped over the knees (world targets for reach=)
CROUCH = "crouch"
KNEE_L = (TIR_X - 90, 1330)
KNEE_R = (TIR_X - 30, 1340)

# Curiosity's small knowing smirk (s01 "grin"): the rig has no small closed smirk, so register
# one scene-local expression (flat half-lids, one cocked brow, a small closed smile).
CR._SPX.setdefault("s01_smirk", dict(CR._SPX["annoyed"], up=0.40, lo=0.24, pr=0.5, mouth="grin",
                                     brow=1.0, lcurve=0.12, tilt=0.02))


def _sleeper(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s, t, seed=seed)


def _baby(c, x, y, s, t, seed):
    CR.draw_specimen_pod_sleeper(c, x, y, s * 1.6, t, seed=seed, baby=True)


SLEEP = dict(sleeper_fn=_sleeper, sleeper_fns={"THING 7": _baby}, sleeper_key="s01_sleepers_v3")


# ----------------------------------------------------------------------------
# timing (all from cues / lines / lip data)
# ----------------------------------------------------------------------------
_TC = {}


def _voice_span(info, who, lid):
    """(first, last) moment the mouth is really open on line lid (the TTS has silent tails)."""
    L = info.line(lid)
    t0, t1 = L.start, L.end
    t = t0
    first = None
    while t <= t1:
        if info.mouth(who, t)[0] > 0.08:
            first = t
            break
        t += 0.02
    t = t1
    last = None
    while t >= t0:
        if info.mouth(who, t)[0] > 0.08:
            last = t
            break
        t -= 0.02
    if first is None or last is None or last <= first:
        return t0, t1
    return first, last


def TT(info):
    k = (id(info), info.dur)
    if k in _TC:
        return _TC[k]
    c = info.cue
    T = {n: c(n) for n in ("pod", "touch", "plate", "perk", "grin", "plates", "frown", "camera",
                           "reach", "click", "dark", "end")}
    for lid, nm, who in (("s01_l01", "l01", "tired"), ("s01_l02", "l02", "tired"),
                         ("s01_l03", "l03", "tired"), ("s01_l03b", "l03b", "tired"),
                         ("s01_l04", "l04", "boss"), ("s01_l05", "l05", "boss")):
        T[nm] = info.line(lid).start
        T[nm + "e"] = info.line(lid).end
        T[nm + "v0"], T[nm + "v"] = _voice_span(info, who, lid)     # voiced span
    T["kept"] = info.word_time("s01_l01", -2)
    T["wow"] = info.word_time("s01_l03", 0)
    T["creative"] = info.word_time("s01_l03", -1)
    # walk-in: starts a little before the cut, four steps, stops on a contact
    T["w0"] = T["pod"] - 0.5
    T["wstop"] = T["w0"] + 2.0
    # crouch during "kept you"
    T["cr0"] = T["kept"] - 0.12
    # plate insert: hand in, wipe, hand out
    T["hand_in"] = T["plate"] + 0.15
    T["wipe0"] = T["plate"] + 0.62
    T["wipe1"] = T["wipe0"] + 0.95
    T["hand_out"] = T["wipe1"] + 0.15
    # S5a: Curiosity hears "Thing One." -- a beat of hope, then the slow contemptuous blink,
    # the ears sag, a tiny huff
    T["c5"] = max(T["l02v"] + 0.35, T["hand_out"] + 0.6)
    T["bo"] = max(T["perk"] + 0.05, T["c5"] + 0.4)              # slow blink starts
    T["flip"] = T["bo"] + 0.24                                  # lids shut: hopeful -> annoyed
    T["huff"] = T["bo"] + 1.0
    T["tag_in"] = T["bo"] + 0.5
    T["tag_out"] = T["l03v"]
    T["c5b"] = T["l03"] - 0.25                                  # -> his CU ("Wow. Creative.")
    # S6: the shared look, the eye-roll toward the plate, the smirk
    T["roll"] = T["grin"] - 0.2
    T["c6"] = min(T["l03v"] + 0.25, T["roll"] - 0.4)
    T["roll_end"] = T["roll"] + ROLL_DUR
    T["smirk"] = T["roll_end"] + 0.12
    T["stand2"] = T["plates"] + 0.4             # he stands up off-screen during the pan
    # S8 + the camera
    T["look_up"] = T["camera"] + 0.65           # his pupils slide up to the camera
    T["c10"] = T["l04"] - 0.65
    T["c12"] = T["click"] - 0.2
    T["c13"] = T["click"] + 0.55
    # lights out
    T["casc"] = T["click"] + 0.85               # first light section dies
    cuts = sets.shaft_power_times(T["casc"], 4, 0.55)
    T["casc_end"] = cuts[-1] + 0.16
    T["push0"] = cuts[2] + 0.15                 # push in as the main tier dies
    T["push1"] = max(T["push0"] + 1.2, T["end"] - 0.3)
    _TC[k] = T
    return T


def _ramp(t, a, b, e=ease_in_out):
    return e(seg(t, a, b))


def _pulse(t, a, b):
    """0 -> 1 -> 0 over [a, b] (sine)."""
    return math.sin(math.pi * seg(t, a, b)) if a <= t <= b else 0.0


# ----------------------------------------------------------------------------
# Tiredness on the catwalk (one continuous performance used by every catwalk shot)
# ----------------------------------------------------------------------------
_V_WALK = abs(H.cycle_speed("tired", "walk", WALK_TURN)) * S * WALK_FIX


def tired_kw(t, T, info):
    kw = dict(outfit="sewer", bandage=True, power=0.6, headphones=None, hood=0.0)
    face = {}
    # ---- position / pose -------------------------------------------------
    x_stop = TIR_X
    if t < T["stand2"]:
        v = _V_WALK
        x_ts = x_stop + v * 0.15                      # where the last contact lands
        x0 = x_ts + v * (T["wstop"] - T["w0"])
        if t < T["wstop"]:
            x = x0 - v * (t - T["w0"])
        else:
            u = seg(t, T["wstop"], T["wstop"] + 0.3)
            x = x_ts - v * 0.3 * (u - 0.5 * u * u)    # decelerate into the stop
        pst = state_at(t, [(-99, "walk"), (T["wstop"], "stand")], 0.3)
        turn = lerp(WALK_TURN, -0.8, smoothstep(seg(t, T["wstop"] - 0.1, T["wstop"] + 0.45)))
        reach = None
        if t >= T["cr0"]:
            kc = smoothstep(seg(t, T["cr0"], T["cr0"] + 0.65))
            pose = ("stand", CROUCH, kc)
            reach = {"l": (KNEE_L[0], KNEE_L[1], kc), "r": (KNEE_R[0], KNEE_R[1], kc)}
            # a small anticipation dip of the head before the crouch, then settle
            face["head_nod"] = 0.06 * math.sin(math.pi * seg(t, T["cr0"] - 0.15, T["cr0"] + 0.25))
        else:
            pose = pst
        kw.update(x=x, pose=pose, turn=turn, pose_t=t - T["w0"], reach=reach)
    else:
        kw.update(x=x_stop, pose="stand", turn=STAND_TURN2, pose_t=None, reach=None)

    # ---- eyes / face -----------------------------------------------------
    POD = (-0.85, 0.15)          # the empty pod glass (left, level) while standing
    CUR_ST = (-0.7, 0.85)        # Curiosity (left-down) while standing
    CUR_CR = (-0.8, 0.5)         # Curiosity while crouched
    PLT = (-0.42, 0.95)          # the plate (down-left) while crouched
    ROW = (0.75, 0.05)           # along the row of pods (standing)
    DOWN = (-0.55, 0.75)         # down to the creature (standing CU)
    look = tween(t, [
        (T["pod"], (-0.9, 0.05)),
        (T["wstop"] + 0.3, (-0.9, 0.05)), (T["wstop"] + 0.45, POD),     # at the pod
        (T["wstop"] + 0.85, POD), (T["wstop"] + 1.0, CUR_ST),             # -> the creature
        (T["l01"] - 0.35, CUR_ST), (T["l01"] - 0.2, POD),                 # -> the pod again
        (T["kept"] - 0.1, POD), (T["kept"] + 0.12, CUR_ST),               # "kept YOU": to it
        (T["cr0"] + 0.65, CUR_CR),
        (T["plate"] - 0.25, CUR_CR), (T["plate"] - 0.05, PLT),            # notices the plate
        (T["bo"] + 0.3, PLT), (T["bo"] + 0.48, CUR_CR),                   # (off) its face falls
        (T["c5b"] - 0.3, CUR_CR), (T["c5b"] - 0.12, PLT),                 # back to the plate
        (T["l03v"] + 0.02, PLT), (T["l03v"] + 0.2, CUR_CR),               # "...Creative." -> to it
        (T["roll"] + 0.5, CUR_CR), (T["roll"] + 0.66, PLT),               # follows its roll
        (T["smirk"] - 0.06, PLT), (T["smirk"] + 0.1, CUR_CR),             # back to it: agreed
        (T["plates"] - 0.24, CUR_CR), (T["plates"] - 0.05, (0.7, -0.05)),  # glance along the row
        (T["stand2"], ROW),
        (T["frown"] + 1.15, ROW), (T["frown"] + 1.3, (0.6, 0.15)),
        (T["l03b"] - 0.45, (0.6, 0.15)), (T["l03b"] - 0.25, DOWN),        # to the creature below
        (T["look_up"] + 0.12, DOWN), (T["look_up"] + 0.32, (0.5, -1.0)),   # up at the camera
        (T["casc"] - 0.1, (0.5, -1.0)), (T["casc"] + 0.25, (0.15, -0.9)),
        (T["casc"] + 1.3, (-0.3, -0.7)), (T["push0"] + 0.3, (-0.55, 0.4)),  # finds Curiosity
    ], ease_in_out)

    # expression base
    if t < T["l01"] - 0.4:
        expr = "bored"
    elif t < T["l03"] - 0.25:
        expr = "neutral"
    elif t < T["stand2"]:
        expr = state_at(t, [(-99, "neutral"), (T["l03"] - 0.25, "deadpan")], 0.25)
    else:
        expr = "neutral"
    # soft for "So this is where they kept you."
    k_soft = _ramp(t, T["l01"] - 0.4, T["l01"]) * (1 - _ramp(t, T["plate"], T["plate"] + 0.4))
    face["brow_ang"] = 0.18 * k_soft
    face["lid"] = -0.02 * k_soft
    # reading the plate (flatly): the lids sink a hair
    k_read = _ramp(t, T["plate"] + 0.2, T["plate"] + 0.6) * (1 - _ramp(t, T["c5b"] - 0.3, T["c5b"]))
    face["lid"] += 0.04 * k_read
    # pupils lead, the head follows ~0.15 s later (pod -> creature -> pod)
    face["head_nod"] = face.get("head_nod", 0.0) + 0.1 * _ramp(t, T["wstop"] + 1.12, T["wstop"] + 1.4) * \
        (1 - _ramp(t, T["l01"] - 0.22, T["l01"] - 0.02))
    face["head_turn"] = -0.08 * _ramp(t, T["wstop"] + 0.5, T["wstop"] + 0.8) * (1 - _ramp(t, T["cr0"], T["cr0"] + 0.4))
    # head down to the plate, up to it on "...Creative.", down to the plate with its roll
    k_hd = _ramp(t, T["plate"] - 0.1, T["plate"] + 0.3) * (1 - _ramp(t, T["bo"] + 0.45, T["bo"] + 0.8))
    k_hd = max(k_hd, _ramp(t, T["c5b"] - 0.25, T["c5b"] + 0.05) * (1 - _ramp(t, T["l03v"] + 0.15, T["l03v"] + 0.45)))
    k_hd = max(k_hd, 0.5 * _ramp(t, T["roll"] + 0.62, T["roll"] + 0.85) * (1 - _ramp(t, T["smirk"] + 0.05, T["smirk"] + 0.3)))
    face["head_nod"] += 0.12 * k_hd
    # "Wow. Creative.": deadpan sarcasm, one brow up a hair (held into the shared look)
    k_brow = _ramp(t, T["wow"] - 0.1, T["wow"] + 0.18) * (1 - _ramp(t, T["smirk"] + 0.3, T["plates"]))
    face["brow_r"] = 0.32 * k_brow
    face["brow_l"] = -0.04 * k_brow
    # the shared joke: the faintest smirk + a tiny nod (they agree)
    k_sm = tween(t, [(T["smirk"], 0.0), (T["smirk"] + 0.25, 1.0), (T["plates"] - 0.15, 1.0),
                     (T["plates"], 0.0)])
    face["curve"] = 0.2 * k_sm
    face["smirk"] = -0.28 * k_sm
    face["head_nod"] += 0.06 * _pulse(t, T["smirk"] + 0.08, T["smirk"] + 0.5)
    # the meaning lands: inner brows up a hair, then a lip press (released to speak)
    k_fr = _ramp(t, T["frown"] + 0.25, T["frown"] + 0.6)
    k_fr_out = 1 - _ramp(t, T["c10"], T["c10"] + 0.1)
    k_line = _ramp(t, T["l03b"] - 0.2, T["l03bv"]) * (1 - _ramp(t, T["look_up"], T["look_up"] + 0.5))
    face["brow_ang"] += (0.26 * k_fr + 0.1 * k_line) * k_fr_out
    face["brow_in"] = (0.12 * k_fr + 0.06 * k_line) * k_fr_out
    k_pr = _ramp(t, T["frown"] + 0.85, T["frown"] + 1.15) * (1 - _ramp(t, T["l03b"] - 0.3, T["l03b"] - 0.05))
    k_pr = max(k_pr, _ramp(t, T["l03bv"] + 0.05, T["l03bv"] + 0.35))
    face["press"] = 0.45 * k_pr * (1 - _ramp(t, T["look_up"] + 0.3, T["look_up"] + 0.6))
    face["head_turn"] += 0.18 * _ramp(t, T["stand2"], T["stand2"] + 0.3)
    # "...They're not things.": the head drops a little toward the creature, lids heavy
    k_dn = _ramp(t, T["l03b"] - 0.12, T["l03b"] + 0.2) * (1 - _ramp(t, T["look_up"] + 0.2, T["look_up"] + 0.5))
    face["head_turn"] += -0.12 * k_dn
    face["head_nod"] += 0.07 * k_dn
    face["lid"] += 0.04 * k_dn
    kw["tears"] = 0.22 * _ramp(t, T["l03b"], T["l03bv"] + 0.2) * (1 - _ramp(t, T["look_up"], T["look_up"] + 0.6))
    # camera: pupils lead, the head follows 0.15 s later; lids lift a little
    k_up = _ramp(t, T["look_up"] + 0.27, T["look_up"] + 0.55)
    face["head_nod"] += -0.12 * k_up
    face["head_tilt"] = 0.04 * k_up
    # (looking up lifts his heavy lids by itself; hold them near rest: only s06 opens them)
    face["lid"] += 0.05 * _ramp(t, T["look_up"] + 0.15, T["look_up"] + 0.35)
    # the dark: brows up, lids lift a hair as the lights die
    k_dk = _ramp(t, T["casc"], T["casc"] + 0.5)
    face["brow"] = 0.15 * k_dk
    face["lid"] += -0.04 * k_dk
    kw.update(expr=expr, look=look, face=face, mouth=info.mouth("tired", t))
    # blinks: "Wow." ... a slow judging blink ... "Creative."
    kw["blink"] = None
    b0 = T["wow"] + 0.22
    if T["c5b"] - 0.1 <= t < b0:
        kw["blink"] = 0.0                   # no stray blink at the cut into his CU
    if b0 <= t <= b0 + 0.7:
        kw["blink"] = tween(t, [(b0, 0.0), (b0 + 0.18, 1.0), (b0 + 0.3, 1.0), (b0 + 0.62, 0.0)])
    # the shared look: no stray blinks
    if T["c6"] - 0.1 <= t <= T["plates"]:
        kw["blink"] = 0.0
    # the meaning lands: slow blinks only (after the press, after the line)
    if T["frown"] <= t <= T["camera"] + 1.6:
        kw["blink"] = 0.0
        for b1 in (T["frown"] + 1.0, T["l03bv"] + 0.3):
            if b1 <= t <= b1 + 0.62:
                kw["blink"] = tween(t, [(b1, 0.0), (b1 + 0.2, 1.0), (b1 + 0.32, 1.0), (b1 + 0.6, 0.0)])
    return kw


def draw_tired(ctx, t, T, info, **over):
    kw = tired_kw(t, T, info)
    kw.update(over)
    x = kw.pop("x")
    return H.draw_person(ctx, "tired", x, FEET, S, t, **kw)


# ----------------------------------------------------------------------------
# Curiosity on the catwalk
# ----------------------------------------------------------------------------
def _roll_blink(pt, hold=0.5):
    """Extra lid for the rig's eye-roll so it starts from flat half-lids (no lid pop)."""
    up_e = CR._eyeroll(pt)[2]
    d = lerp(hold, up_e, ease_in_out(seg(pt, 0.0, 0.25)))
    return clamp((d - up_e) / (1.0 - up_e)) if d > up_e else 0.0


def cur_kw(t, T, info):
    kw = dict(pose="sit", glow=1.0, tail_curl=0.0)
    GLASS = (0.45, -0.8)
    HIM_ST = (0.85, -0.5)
    HIM_CR = (0.8, -0.5)
    PLT = (0.9, 0.12)          # the plate: right of it, at eye level
    look = tween(t, [
        (T["pod"], GLASS), (T["pod"] + 0.35, GLASS), (T["pod"] + 0.55, HIM_ST),   # footsteps
        (T["l01"] + 0.6, HIM_ST), (T["l01"] + 0.8, GLASS),                          # "...where"
        (T["kept"], GLASS), (T["kept"] + 0.2, HIM_ST), (T["cr0"] + 0.65, HIM_CR),   # follows him down
        (T["touch"] + 1.3, HIM_CR), (T["touch"] + 1.5, PLT),                        # to the plate
        (T["c6"] + 0.1, PLT), (T["c6"] + 0.26, HIM_CR),                             # S6: up at him
        (T["roll_end"], PLT), (T["roll_end"] + 0.12, HIM_CR),                       # roll -> plate -> him
        (T["casc"] - 0.2, HIM_CR), (T["casc"] + 0.2, (0.2, -0.9)),                  # the lights
        (T["casc"] + 1.2, (0.55, -0.85)), (T["push0"] + 0.3, (0.85, -0.55)),        # to him
    ], ease_in_out)
    if T["c6"] + 0.26 <= t < T["roll"]:
        look = HIM_CR
    # ears: wistful 0.4; twitch at his steps; lowering on the nod; hope rises while the plate is
    # wiped (off-screen); the name lands: they sag degree by degree; a flick on the huff
    ears = tween(t, [(T["pod"], 0.40), (T["pod"] + 0.15, 0.40), (T["pod"] + 0.28, 0.62),
                     (T["pod"] + 0.6, 0.44), (T["touch"] + 0.2, 0.40), (T["touch"] + 1.3, 0.27),
                     (T["plate"] + 0.8, 0.27), (T["c5"] - 0.2, 0.62), (T["bo"] + 0.12, 0.65),
                     (T["bo"] + 0.8, 0.31), (T["c5b"], 0.27), (T["roll"], 0.25),
                     (T["roll_end"], 0.30), (T["smirk"] + 0.05, 0.31), (T["smirk"] + 0.4, 0.44),
                     (T["plates"], 0.46)])
    ears += 0.06 * _pulse(t, T["huff"] - 0.05, T["huff"] + 0.3)
    if t >= T["casc"]:
        ears = lerp(0.46, 0.9, _ramp(t, T["casc"], T["casc"] + 0.3))
    tilt = 0.0
    # the slow nod (touch)
    tn = T["touch"]
    tilt += 0.26 * tween(t, [(tn + 0.25, 0.0), (tn + 0.8, 1.0), (tn + 1.05, 1.0), (tn + 1.55, 0.0)])
    # the name lands: the head sinks a hair as the face falls, then the huff lifts the chin
    # (nose in the air) and it keeps a little offended dignity
    tilt += 0.04 * _ramp(t, T["bo"] + 0.15, T["bo"] + 0.6) * (1 - _ramp(t, T["huff"] - 0.2, T["huff"]))
    tilt += -0.07 * _pulse(t, T["huff"] - 0.15, T["huff"] + 0.35)
    tilt += -0.03 * _ramp(t, T["huff"] + 0.1, T["huff"] + 0.4) * (1 - _ramp(t, T["c6"] + 0.2, T["c6"] + 0.5))
    # S6: chin up to him (head follows the pupils), then a knowing chin-dip with the smirk
    tilt += -0.04 * _ramp(t, T["c6"] + 0.22, T["c6"] + 0.42) * (1 - _ramp(t, T["roll"], T["roll"] + 0.2))
    tilt += 0.035 * _ramp(t, T["smirk"], T["smirk"] + 0.3) * (1 - _ramp(t, T["plates"] - 0.1, T["plates"]))
    # expressions (switch on cuts or behind a closed blink)
    blink = None
    pose_t = None
    if t < T["touch"]:
        expr = "hopeful"
    elif t < T["c5"]:
        expr = "teary"
        kw["tears"] = 0.12
    elif t < T["flip"]:
        expr = "hopeful"
    elif t < T["roll"]:
        expr = "annoyed"
    elif t < T["roll_end"]:
        expr = "eyeroll"
        pose_t = (t - T["roll"]) * (CR.EYEROLL_DUR / ROLL_DUR)
        blink = _roll_blink(pose_t)
        look = PLT                       # the roll settles on the plate
    elif t < T["smirk"]:
        expr = "annoyed"
    elif t < T["plates"]:
        expr = "s01_smirk"
        kw["tail_curl"] = 0.35 * _ramp(t, T["smirk"] + 0.1, T["smirk"] + 0.6)
    elif t < T["casc"]:
        expr = "calm"
    else:
        expr = "wide"
    # the expression's own gaze offset is added by the rig: aim the true gaze
    if expr != "eyeroll":
        off = CR._SPX.get(expr, CR._SPX["calm"])["look"]
        look = (look[0] - off[0], look[1] - off[1])
    # blinks: the nod's slow blink; the slow contemptuous blink that opens on half-lids; a
    # deeper lid drop after the huff, which lifts again to meet his eyes
    b0 = tn + 0.6
    if b0 <= t <= b0 + 0.9:
        blink = tween(t, [(b0, 0.0), (b0 + 0.3, 1.0), (b0 + 0.45, 1.0), (b0 + 0.85, 0.0)])
    if T["c5"] - 0.05 <= t < T["roll"]:
        bo = T["bo"]
        blink = tween(t, [(bo, 0.0), (bo + 0.18, 1.0), (bo + 0.3, 1.0), (bo + 0.66, 0.0),
                          (T["huff"] + 0.35, 0.0), (T["huff"] + 0.8, 0.14), (T["c6"] + 0.1, 0.14),
                          (T["c6"] + 0.3, 0.0)])
    if T["roll_end"] <= t < T["plates"]:
        blink = 0.0
    face = 0.62
    kw.update(expr=expr, look=look, ears=ears, tilt=tilt, blink=blink, face=face, pose_t=pose_t)
    return kw


def _huff_squash(t, T):
    """(sx, sy) about the feet: a little intake of breath, then the deflating huff."""
    k_in = _pulse(t, T["huff"] - 0.3, T["huff"] + 0.02)
    k_out = _pulse(t, T["huff"], T["huff"] + 0.38)
    return 1.0 - 0.012 * k_in + 0.016 * k_out, 1.0 + 0.025 * k_in - 0.03 * k_out


def draw_cur(ctx, t, T, info, **over):
    kw = cur_kw(t, T, info)
    kw.update(over)
    sx, sy = _huff_squash(t, T)
    if sx != 1.0 or sy != 1.0:
        ctx.save()
        ctx.translate(CUR_X, FEET)
        ctx.scale(sx, sy)
        ctx.translate(-CUR_X, -FEET)
        a = CR.draw_specimen(ctx, CUR_X, FEET, S, t, **kw)
        ctx.restore()
        return a
    return CR.draw_specimen(ctx, CUR_X, FEET, S, t, **kw)


def _huff_puff(ctx, t, T, nose):
    """The tiny huff: two little breath puffs out of the nose (forward and a bit down)."""
    age = t - T["huff"]
    if not (0.0 <= age <= 0.6) or nose is None:
        return
    nx, ny = nose
    for i, (ang, dl, sz) in enumerate(((-0.12, 0.0, 1.0), (0.42, 0.07, 0.8))):
        a_ = age - dl
        if a_ <= 0.0:
            continue
        k = clamp(a_ / 0.5)
        a = (1.0 - k) ** 1.4 * smoothstep(seg(a_, 0.0, 0.05))
        d = 8 + 46 * ease_out(k)
        cx_, cy_ = nx + 6 + d * math.cos(ang), ny + 4 + d * math.sin(ang)
        r = (4.5 + 8 * ease_out(k)) * sz
        for (ox, oy, rr) in ((0, 0, 1.0), (-0.7, 0.5, 0.7), (0.6, 0.55, 0.65)):
            core.circle(ctx, cx_ + ox * r, cy_ + oy * r, rr * r)
        core.fill(ctx, (0.86, 1.0, 1.0, 0.62 * a))
        ctx.new_sub_path()
        ctx.arc(cx_, cy_, r * 1.05, -2.4, -0.6)
        core.stroke(ctx, (1.0, 1.0, 1.0, 0.75 * a), 2.2, cap="round")


# ----------------------------------------------------------------------------
# catwalk set state
# ----------------------------------------------------------------------------
def cw_state(t, T):
    st = dict(SLEEP)
    st["plate_dust"] = 1.0
    st["plate_wipe"] = clamp(_wipe_k(t, T))
    # the security camera: off, LED blinks on, swivels toward them
    cam0 = T["camera"]
    if t < cam0 + 0.3:
        st["cam_led"] = 0.0
    elif t < cam0 + 0.42:
        st["cam_led"] = clamp((t - cam0 - 0.3) / 0.12)
    else:
        st["cam_led"] = 1.0
    sw = _ramp(t, cam0 + 0.5, cam0 + 1.25)
    st["cam_face"] = round(sw, 3)
    st["cam_angle"] = round(0.25 + 0.12 * sw, 3)
    # lights out
    ps = sets.shaft_power_sections(t, T["casc"], 4, 0.55)
    st["power_sections"] = ps
    return st


def _wipe_k(t, T):
    return ease_in_out(seg(t, T["wipe0"], T["wipe1"]))


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _to_screen(cam, p):
    cx, cy, z = cam
    return (W / 2 + (p[0] - cx) * z, HGT / 2 + (p[1] - cy) * z)


def catwalk_shot(ctx, t, T, info, cam, chars=True, rail=True, light=None, draw_t=True, draw_c=True,
                 over_t=None, over_c=None):
    """The catwalk with both characters (lit by the set) under camera `cam`."""
    st = cw_state(t, T)
    if light:
        st.update(light)
    li = {k: st[k] for k in ("power_sections",) if k in st}
    if "pod_glow" in st:
        li["pod_glow"] = st["pod_glow"]
    an = {}
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, **st)
        if chars:
            with sets.shaded(ctx, sets.catwalk, t, layer="shade", **li):
                if draw_c:
                    an["cur"] = draw_cur(ctx, t, T, info, **(over_c or {}))
                if draw_t:
                    an["tir"] = draw_tired(ctx, t, T, info, **(over_t or {}))
            if draw_c:
                _huff_puff(ctx, t, T, an["cur"].get("nose"))
        parts = ("rail", "stair") if rail else ("stair",)
        sets.catwalk(ctx, t, layer="fg", parts=parts, **li)
    return an


# ----------------------------------------------------------------------------
# S1: the thumbnail (looking out of the empty pod)
# ----------------------------------------------------------------------------
POV_X, POV_Y, POV_S = 404, 1585, 2.9   # creature ground point / scale: face at ~(540, 875)


def _paw_print(ctx, x, y, s, k=1.0):
    """The paw pressed flat on the glass: pale flattened pads + a breath of fog."""
    if k <= 0.01:
        return
    core.radial_glow(ctx, x, y + 6 * s, 52 * s, "#e6fffb", 0.30 * k)
    core.ellipse(ctx, x + 2 * s, y + 10 * s, 19 * s, 15 * s)
    core.fill(ctx, (0.80, 0.98, 1.0, 0.40 * k))
    for (dx, dy, r) in ((-15, -10, 6.5), (-4, -19, 7), (9, -18, 6.5), (18, -8, 6)):
        core.circle(ctx, x + dx * s, y + dy * s, r * s)
    core.fill(ctx, (0.85, 1.0, 1.0, 0.42 * k))


def shot_pov(ctx, t, T, info):
    k = ease_in_out(seg(t, 0.0, T["pod"]))
    q = T["pod"] / 2.4                    # beats authored for a 2.4 s hold; keyed to the cue
    cam = (lerp(540, 552, k), lerp(960, 918, k), lerp(1.0, 1.08, k))
    fog = tween(t, [(0.45 * q, 0.0), (0.95 * q, 0.72), (1.25 * q, 0.66), (2.35 * q, 0.0)])
    ears = tween(t, [(0.0, 0.45), (2.4 * q, 0.38)])
    look = tween(t, [(0.0, (0.0, -0.05)), (1.5 * q, (0.0, -0.05)), (1.75 * q, (-0.18, -0.12)),
                     (2.4 * q, (-0.18, -0.12))])
    blink = 0.0 if t < 0.6 * q else tween(t, [(1.2 * q, 0.0), (1.2 * q + 0.22, 1.0), (1.2 * q + 0.35, 1.0),
                                              (1.2 * q + 0.65, 0.0)])
    tilt = 0.05 * math.sin(math.pi * seg(t, 0.4 * q, 2.4 * q))
    with core.camera(ctx, *cam):
        sets.pod_pov(ctx, t)
        with sets.shaded(ctx, sets.pod_pov, t, layer="shade"):
            a = CR.draw_specimen(ctx, POV_X, POV_Y, POV_S, t, pose="wave", pose_t=WAVE_STILL, face=0.0,
                                 expr="hopeful", ears=ears, look=look, blink=blink, tilt=tilt)
        px, py = a["paw"]
        _paw_print(ctx, px - 7, py + 5, POV_S / 2.2)
        mx, my = a["mouth"]
        sets.pod_pov(ctx, t, layer="fg", fog=fog, fog_xy=(mx + 10, my + 18))


# ----------------------------------------------------------------------------
# S4: the nameplate insert (thumb wipe)
# ----------------------------------------------------------------------------
INS_CAM = (1012, 1300, 3.3)


def _thumb_pos(t, T):
    """World thumb-tip position + presence for the wipe."""
    x0, x1 = PLATE[0] + 14, PLATE[0] + PLATE[2] - 14
    yy = PLATE_C[1] + 2
    off = (PLATE[0] + PLATE[2] + 120, PLATE[1] - 150)     # off-frame (upper right)
    if t < T["wipe0"]:
        k = ease_out(seg(t, T["hand_in"], T["wipe0"] - 0.05))
        return (lerp(off[0], x0, k), lerp(off[1], yy - 6, k) + 8 * math.sin(math.pi * k)), k
    if t < T["wipe1"]:
        k = _wipe_k(t, T)
        return (lerp(x0, x1, k), yy - 6 + 5 * math.sin(math.pi * k)), 1.0
    k = ease_in(seg(t, T["hand_out"], T["hand_out"] + 0.4))
    return (lerp(x1, off[0] + 60, k), lerp(yy - 6, off[1] - 40, k)), 1.0 - k


def _draw_hand(ctx, x, y, s, press=0.0):
    """His bandaged right hand reaching in from the upper right; the thumb pad presses the
    plate at (x, y) (world, s = 0.75 character scale)."""
    ink = core.PAL["ink"]
    skin, skin_sh = core.PAL["t_skin"], core.PAL["t_skin_sh"]
    lw = 5.5
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ang = -0.72                                   # forearm direction (wrist -> elbow), up-right
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    wx, wy = 92, -64                              # wrist

    def seg_(ax, ay, bx, by, r, col):
        for w_, c_ in ((2 * r + 2 * lw, ink), (2 * r, col)):
            ctx.move_to(ax, ay)
            ctx.line_to(bx, by)
            core.stroke(ctx, c_, w_, cap="round")

    # hoodie sleeve (pushed up to the elbow), then the bandaged forearm
    sx_, sy_ = wx + 175 * ca, wy + 175 * sa
    seg_(sx_, sy_, sx_ + 260 * ca, sy_ + 260 * sa, 33, core.PAL["t_hoodie"])
    seg_(wx + 6 * ca, wy + 6 * sa, sx_ + 8 * ca, sy_ + 8 * sa, 22, "#f2efe6")
    for k in range(6):
        u = 26 + k * 25
        px, py = wx + u * ca, wy + u * sa
        ctx.move_to(px + nx * 21 - 7 * ca, py + ny * 21 - 7 * sa)
        ctx.line_to(px - nx * 21 + 7 * ca, py - ny * 21 + 7 * sa)
        core.stroke(ctx, (0.56, 0.58, 0.64, 0.75), 2.6)
    ctx.move_to(sx_ + 8 * ca + nx * 33, sy_ + 8 * sa + ny * 33)
    ctx.line_to(sx_ + 8 * ca - nx * 33, sy_ + 8 * sa - ny * 33)
    core.stroke(ctx, core.PAL["t_hoodie_dk"], 12, cap="round")
    # back of the hand (loose fist), knuckles toward the lower left
    ctx.save()
    ctx.translate(58, -42)
    ctx.rotate(ang + math.pi)                     # local +x points down-left (away from the wrist)
    core.rrect(ctx, -38, -30, 74, 60, 26)
    core.fill_stroke(ctx, skin, ink, lw)
    # curled fingers: four rounded segments folded under the knuckles
    for k in range(4):
        fy = -22 + k * 14.5
        core.rrect(ctx, 22, fy - 7, 26, 15, 7)
        core.fill_stroke(ctx, skin, ink, 3.6)
    ctx.move_to(-10, -24)
    ctx.curve_to(4, -28, 14, -26, 22, -20)
    core.stroke(ctx, skin_sh, 3.0)
    ctx.restore()
    # thumb: from the base of the hand to the pad on the plate (slightly flattened while pressing)
    sq = 1.0 - 0.14 * press
    ctx.save()
    ctx.translate(0, 0)
    ctx.rotate(-0.42)
    core.rrect(ctx, -4, -13 * sq, 66, 26 * sq, 13 * sq)
    core.fill_stroke(ctx, skin, ink, lw)
    core.rrect(ctx, 2, -11 * sq, 17, 11 * sq, 5)      # nail
    core.fill(ctx, (1.0, 0.92, 0.84, 0.9))
    ctx.move_to(32, -12 * sq)
    ctx.curve_to(36, -4, 36, 4, 32, 12 * sq)          # knuckle crease
    core.stroke(ctx, skin_sh, 2.6)
    ctx.restore()
    ctx.restore()


def shot_plate(ctx, t, T, info):
    cam = (INS_CAM[0] - 6 * seg(t, T["plate"], T["c5"]), INS_CAM[1], INS_CAM[2] * (1 + 0.03 * seg(t, T["plate"], T["c5"])))
    st = cw_state(t, T)
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, **st)
        (tx, ty), k = _thumb_pos(t, T)
        if k > 0.001:
            with sets.shaded(ctx, sets.catwalk, t, layer="shade"):
                press = 1.0 if T["wipe0"] <= t <= T["wipe1"] else 0.0
                _draw_hand(ctx, tx, ty, S * 1.1, press)
        # a few dust flecks shed by the thumb
        if T["wipe0"] <= t <= T["wipe1"] + 1.0:
            for i in range(7):
                ti = T["wipe0"] + (T["wipe1"] - T["wipe0"]) * (i + 0.5) / 7
                age = t - ti
                if 0 <= age <= 0.9:
                    fx0 = lerp(PLATE[0] + 14, PLATE[0] + PLATE[2] - 14, _wipe_k(ti, T))
                    px = fx0 + 6 * math.sin(i * 2.1) - 10 * age
                    py = PLATE_C[1] + 30 + 70 * age * age + 8 * core.hash01(i, 4)
                    core.circle(ctx, px, py, 2.2 + 1.2 * core.hash01(i, 5))
                    core.fill(ctx, (0.62, 0.56, 0.48, 0.75 * (1 - age / 0.9)))


# ----------------------------------------------------------------------------
# S7: pan along the pods (THING 2 .. THING 5 under the NOTHING TO SEE HERE signs)
# ----------------------------------------------------------------------------
def _trapezoid(u, ramp=0.22):
    """0..1 -> 0..1 with eased ends and a constant-speed middle (calm, readable pans)."""
    u = clamp(u)
    r = ramp
    vmax = 1.0 / (1.0 - r)
    if u < r:
        return 0.5 * vmax * u * u / r
    if u > 1 - r:
        v = 1 - u
        return 1.0 - 0.5 * vmax * v * v / r
    return 0.5 * vmax * r + vmax * (u - r)


PAN_Z = 1.25                   # two plates (490 apart) + the sign between them fill x 60..930
PAN_DX = 36                    # centre the pair in the safe zone (x 60..930), not the frame
PAN_CY = 1110                  # signs at y ~375, plates at ~1235 (above the caption band)


def shot_plates(ctx, t, T, info):
    u = seg(t, T["plates"] + 0.25, T["frown"] - 0.5)
    x = lerp(SIGNS_X[0] + PAN_DX, SIGNS_X[1] + PAN_DX, _trapezoid(u, 0.34))
    cam = (x, PAN_CY, PAN_Z)
    st = cw_state(t, T)
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, **st)
        sets.catwalk(ctx, t, layer="fg", parts=("rail",))


# ----------------------------------------------------------------------------
# control room
# ----------------------------------------------------------------------------
def _feed(ctx, x, y, w, h, t, T=None, info=None):
    """SHAFT CAM 03: the two of them at the empty pod, looking up into the lens."""
    zz = w / 880.0
    with core.camera(ctx, 1000, 1080, zz, sx=x + w / 2, sy=y + h / 2):
        sets.catwalk(ctx, 1.0, plate_dust=0.0, plate_wipe=1.0, cam_led=1.0, cam_face=1.0, **SLEEP)
        CR.draw_specimen(ctx, CUR_X, FEET, S, t, pose="sit", expr="calm", look=(0.5, -0.85), ears=0.8,
                         face=0.62, tail_curl=0.2)
        H.draw_person(ctx, "tired", TIR_X, FEET, S, t, pose="stand", turn=STAND_TURN2, outfit="sewer",
                      bandage=True, power=0.6, look=(0.5, -1.0), face={"head_nod": -0.12, "head_turn": 0.18},
                      drift=False)


def _boss_chair(ctx, part):
    cx, cy = CHAIR_X, KM["chair"][1]
    sets.sprite(ctx, ("s01_chair2", part), cx - 330, cy - 1080 * S, 660, 1100 * S,
                lambda c: props.boss_chair(c, cx, cy, S, CHAIR_TURN, part=part, dir=-1))


def _switch_tip(on):
    # tip of the SHAFT POWER toggle (power_switch at s 0.55: ~35 px up at ON .. down at OFF)
    return (SWITCH[0], lerp(1336.2, 1265.8, clamp(on)))


def _switch_on(t, T):
    return 1.0 - ease_in(seg(t, T["click"], T["click"] + 0.12))


def boss_kw(t, T, info):
    face = {}
    LENS = (0.08, -0.06)                  # into our lens (= the shaft camera: she is watching)
    SW = (-0.8, 0.72)                     # the SHAFT POWER switch (down-left)
    # "Right on time.": calm, lids lowering a hair, the faintest knowing smirk at the end
    k1 = _ramp(t, T["l04e"] - 0.3, T["l04e"] + 0.3)
    face["lid"] = 0.06 * k1
    face["smirk"] = -0.25 * k1 * (1 - _ramp(t, T["reach"] + 0.2, T["reach"] + 0.6))
    # glances: on the monitors below the lens while the camera tilts down, up into the lens for
    # the line, then to the switch; back to the lens for "Lights out.", then the switch
    look = tween(t, [(T["c10"], (0.35, 0.25)), (T["l04"] - 0.2, (0.35, 0.25)), (T["l04"] + 0.0, LENS),
                     (T["reach"] - 0.05, LENS), (T["reach"] + 0.12, SW),
                     (T["l05"] - 0.25, SW), (T["l05"] - 0.08, LENS),
                     (T["l05e"] + 0.05, LENS), (T["l05e"] + 0.22, SW)], ease_in_out)
    face["head_nod"] = 0.06 * _ramp(t, T["reach"] + 0.15, T["reach"] + 0.45) * \
        (1 - 0.6 * _ramp(t, T["l05"] - 0.1, T["l05"] + 0.15)) + \
        0.04 * _ramp(t, T["l05e"] + 0.2, T["l05e"] + 0.5)
    face["head_turn"] = -0.12 * _ramp(t, T["reach"] + 0.15, T["reach"] + 0.45) * \
        (1 - _ramp(t, T["l05"] - 0.1, T["l05"] + 0.15)) - 0.1 * _ramp(t, T["l05e"] + 0.2, T["l05e"] + 0.5)
    # "Lights out.": a slow lid drop on the line, a slow blink after it
    face["lid"] += 0.05 * _ramp(t, T["l05"], T["l05e"])
    # she barely blinks: one slow blink after each line
    blink = 0.0
    for b0 in (min(T["l04v"] + 0.15, T["reach"] - 0.75), T["l05v"] + 0.1):
        if b0 <= t <= b0 + 0.7:
            blink = tween(t, [(b0, 0.0), (b0 + 0.25, 1.0), (b0 + 0.37, 1.0), (b0 + 0.66, 0.0)])
    # the reach: hand to the toggle tip, rests, then pushes it down with the toggle
    tip = _switch_tip(_switch_on(t, T))
    kr = ease_in_out(seg(t, T["reach"] + 0.22, T["reach"] + 0.85))
    reach = None
    a_pt = 1.95                                  # index finger aimed down-left at the knob
    if kr > 0.0:
        gx, gy = tip[0] + 2, tip[1] - 7          # "point": the grip point is the fingertip
        reach = {"l": (gx, gy, kr, a_pt)}
    lean = 0.1 * kr
    pose = {"base": "sit_chair", "al_h": "point", "lean": lean} if kr > 0.5 else \
        {"base": "sit_chair", "lean": lean}
    return dict(pose=pose, turn=BOSS_TURN, expr="cold", look=look, face=face, blink=blink, reach=reach,
                mouth=info.mouth("boss", t))


def control_shot(ctx, t, T, info, cam, feed=True):
    sw = _switch_on(t, T)
    mf = {3: lambda c, x, y, w, h, tt: fx.monitor_feed(c, x, y, w, h, tt, _feed, label="SHAFT CAM 03")} if feed else None
    with core.camera(ctx, *cam):
        sets.control_room(ctx, t, chair=False, switch=round(sw, 3), monitor_fns=mf)
        _boss_chair(ctx, "behind")
        with sets.shaded(ctx, sets.control_room, t, layer="shade"):
            kw = boss_kw(t, T, info)
            a = H.draw_person(ctx, "boss", BOSS_SEAT[0], BOSS_GY, S, t, **kw)
        _boss_chair(ctx, "front")
        sets.control_room(ctx, t, layer="fg", chair=False)
    return a


def shot_control(ctx, t, T, info):
    k = ease_in_out(seg(t, T["c10"] + 0.3, T["c10"] + 1.05))
    cam = (lerp(1700, 1660, k), lerp(540, 935, k), 1.9)
    cam = (cam[0], cam[1] + 12 * seg(t, T["c10"] + 1.05, T["reach"]), cam[2])
    control_shot(ctx, t, T, info, cam)


def shot_reach(ctx, t, T, info):
    k = ease_in_out(seg(t, T["l05"] - 0.3, T["c12"]))
    cam = (lerp(1540, 1545, k), lerp(1105, 1080, k), lerp(1.68, 1.95, k))
    control_shot(ctx, t, T, info, cam)


def shot_switch(ctx, t, T, info):
    cam = (1430, 1255, 3.0)
    control_shot(ctx, t, T, info, cam, feed=False)


# ----------------------------------------------------------------------------
# S13: lights out
# ----------------------------------------------------------------------------
DARK_CAM0 = (1000, 700, 0.6)
DARK_CAM1 = (1010, 1105, 1.35)        # = s02's first framing (S01_DARK_CAM there)


def shot_dark(ctx, t, T, info):
    k = ease_in_out(seg(t, T["push0"], T["push1"]))
    z = DARK_CAM0[2] * (DARK_CAM1[2] / DARK_CAM0[2]) ** k
    cuts = sets.shaft_power_times(T["casc"], 4, 0.55)
    # the heavy near relays jolt the catwalk a little (short, decaying)
    dx, dy = core.shake(t, cuts[2], 0.45, 4, seed=11)
    dx2, dy2 = core.shake(t, cuts[3], 0.6, 7, seed=12)
    cam = (lerp(DARK_CAM0[0], DARK_CAM1[0], k) + (dx + dx2) / z, lerp(DARK_CAM0[1], DARK_CAM1[1], k) + (dy + dy2) / z, z)
    ps = sets.shaft_power_sections(t, T["casc"], 4, 0.55)
    with core.cache_steps(1):
        an = catwalk_shot(ctx, t, T, info, cam, rail=True)
    # deepen the dark once everything is out (the pods' embers fade to nearly nothing)
    deep = _ramp(t, T["casc_end"], T["casc_end"] + 1.2)
    if deep > 0.0:
        ctx.rectangle(0, 0, W, HGT)
        core.fill(ctx, core.alpha(sets.DARK, 0.8 * deep))
    # the two pairs of eyes, brighter as their light section dies
    dk_main = 1.0 - ps[2]
    amt = smoothstep(clamp(dk_main * 1.1))
    if amt > 0.01 and "cur" in an and "tir" in an:
        ca, ta = an["cur"], an["tir"]
        ce = ((ca["eye_l"][0] + ca["eye_r"][0]) / 2, (ca["eye_l"][1] + ca["eye_r"][1]) / 2)
        te = ((ta["eye_l"][0] + ta["eye_r"][0]) / 2, (ta["eye_l"][1] + ta["eye_r"][1]) / 2)
        cs = S * z * 0.95
        cdist = math.hypot(ca["eye_r"][0] - ca["eye_l"][0], ca["eye_r"][1] - ca["eye_l"][1]) * z
        tdist = math.hypot(ta["eye_r"][0] - ta["eye_l"][0], ta["eye_r"][1] - ta["eye_l"][1]) * z
        ts_ = S * z * 1.25
        sx, sy = _to_screen(cam, ce)
        lk = cur_kw(t, T, info)["look"]
        cb = None
        e0 = T["end"] - 1.05
        if e0 - 0.05 <= t <= e0 + 0.6:
            cb = tween(t, [(e0, 0.0), (e0 + 0.12, 1.0), (e0 + 0.22, 1.0), (e0 + 0.4, 0.0)])
        fx.eyes_in_dark(ctx, sx, sy, cs, t, "curiosity", blink=cb, look=(lk[0] * 0.6, lk[1] * 0.6),
                        amount=amt, gap=cdist / cs, seed=3)
        sx2, sy2 = _to_screen(cam, te)
        tb = None
        e1 = T["end"] - 0.8
        if e1 - 0.05 <= t <= e1 + 0.8:
            tb = tween(t, [(e1, 0.0), (e1 + 0.25, 1.0), (e1 + 0.4, 1.0), (e1 + 0.7, 0.0)])
        tl = tired_kw(t, T, info)["look"]
        fx.eyes_in_dark(ctx, sx2, sy2, ts_, t, "tired", blink=tb, look=(tl[0] * 0.5, tl[1] * 0.5),
                        amount=amt * 0.9, gap=tdist / ts_, seed=5)


# ----------------------------------------------------------------------------
# render
# ----------------------------------------------------------------------------
CAM_S5A = ((845, 1290, 2.92), (848, 1292, 3.06))      # Curiosity CU (the plate's edge at right)
CAM_S5B = ((1112, 1200, 2.2), (1108, 1196, 2.28))     # his CU (crouched), the plate lower left
CAM_S6 = ((950, 1218, 1.62), (954, 1220, 1.7))          # the crouched two-shot


def _cam_lerp(pair, k):
    a, b = pair
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k))


def render(ctx, t, info):
    T = TT(info)
    if t < T["pod"]:
        shot_pov(ctx, t, T, info)
    elif t < T["touch"]:
        # S2: walk in, l01, crouch on "kept you"; the camera eases in as he arrives, then down
        # and in with him as he crouches
        xt = tired_kw(t, T, info)["x"]
        kt = ease_in_out(seg(t, T["wstop"] - 0.9, T["wstop"] + 0.6))
        cx0 = lerp(xt - 140, 1008, kt)                # track him in, then settle on the pod
        k0 = ease_in_out(seg(t, T["wstop"], T["wstop"] + 1.0))
        k1 = ease_in_out(seg(t, T["cr0"] - 0.2, T["touch"] - 0.1))
        cam = (lerp(cx0 + 5 * k0, 962, k1), lerp(lerp(1185, 1195, k0), 1212, k1),
               lerp(lerp(1.3, 1.48, k0), 1.92, k1))
        catwalk_shot(ctx, t, T, info, cam, rail=False)
    elif t < T["plate"]:
        # S3: Curiosity close-up, the nod
        k = seg(t, T["touch"], T["plate"])
        cam = (835, 1292, 3.0 + 0.08 * k)
        catwalk_shot(ctx, t, T, info, cam, rail=False)
    elif t < T["c5"]:
        shot_plate(ctx, t, T, info)
    elif t < T["c5b"]:
        # S5a: Curiosity CU: it hears the name (slow push-in through the reaction)
        k = ease_in_out(seg(t, T["c5"], T["c5b"]))
        catwalk_shot(ctx, t, T, info, _cam_lerp(CAM_S5A, k), rail=False)
    elif t < T["c6"]:
        # S5b: his CU: "Wow. Creative."
        k = ease_in_out(seg(t, T["c5b"], T["c6"]))
        catwalk_shot(ctx, t, T, info, _cam_lerp(CAM_S5B, k), rail=False)
    elif t < T["plates"]:
        # S6: the shared look
        k = ease_in_out(seg(t, T["c6"], T["plates"]))
        catwalk_shot(ctx, t, T, info, _cam_lerp(CAM_S6, k), rail=False)
    elif t < T["frown"]:
        shot_plates(ctx, t, T, info)
    elif t < T["c10"]:
        # S8: his CU under the wall camera; at "camera" the LED blinks on, the lens swivels to
        # look at them, his pupils slide up to it (one continuous shot, gentle tilt up)
        k = seg(t, T["frown"], T["camera"])
        k2 = ease_in_out(seg(t, T["camera"] + 0.2, T["camera"] + 1.2))
        k3 = seg(t, T["camera"] + 1.2, T["c10"])
        cam = (1300 + 5 * k2, 872 - 4 * k - 34 * k2 - 6 * k3, 2.62 + 0.06 * k - 0.14 * k2 + 0.05 * k3)
        catwalk_shot(ctx, t, T, info, cam, rail=False)
    elif t < T["reach"]:
        shot_control(ctx, t, T, info)
    elif t < T["c12"]:
        shot_reach(ctx, t, T, info)
    elif t < T["c13"]:
        shot_switch(ctx, t, T, info)
    else:
        shot_dark(ctx, t, T, info)
    # overlays (screen space)
    if T["tag_in"] <= t < T["tag_out"] + 0.4:
        fx.name_tag(ctx, "THING 1", "according to HushCorp", t, T["tag_in"], T["tag_out"],
                    x=90, y=170, color="curiosity")


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def SFX(info):
    T = TT(info)
    ev = []
    # shaft room tone (pods), not in the control room
    ev += sfx.loop_events("pod_hum", 0.0, T["c10"] + 0.1, -8)
    ev += sfx.loop_events("pod_hum", T["c13"], T["casc"] + 1.2, -8)
    # his footsteps on the grating (walk contacts every 0.5 s)
    for k in range(1, 5):
        tt = T["w0"] + 0.5 * k
        if tt >= T["pod"] - 0.05:
            ev.append((tt, "footstep", 0 if k < 4 else 1, 0.25))
    ev.append((T["wstop"] + 0.28, "footstep", -5, 0.22))     # feet come together
    # Curiosity's ear twitch at the steps
    ev.append((T["pod"] + 0.2, "ears_perk", -6, -0.3))
    # crouch (cloth)
    ev.append((T["cr0"] + 0.05, "cloth_rustle", -5, 0.2))
    # the nod: a small sad coo
    ev.append((T["touch"] + 0.35, "creature_chirp_sad", -9, -0.1))
    # the wipe
    ev.append((T["hand_in"] + 0.05, "cloth_rustle", -8, 0.3))
    ev.append((T["wipe0"], "cloth_rustle", -9, 0.1))
    # the name lands: a tiny unimpressed huff through the nose
    ev.append((T["huff"] - 0.04, "sigh", -9, -0.25))
    # the shared joke: a short pleased purr with the smirk
    ev.append((T["smirk"] + 0.05, "creature_purr", -3, -0.2))
    # he stands up (off-screen, under the pan)
    ev.append((T["stand2"], "cloth_rustle", -10, 0.2))
    # the security camera
    ev.append((T["camera"] + 0.3, "mouse_click", -4, 0.3))
    ev.append((T["camera"] + 0.48, "camera_whir", 1, 0.3))
    # control room: her sleeve, the switch
    ev.append((T["reach"] + 0.2, "cloth_rustle", -12, -0.2))
    ev.append((T["click"], "latch_click", 3, -0.15))
    # the lights-out cascade: far up the shaft first, then section by section toward us
    cuts = sets.shaft_power_times(T["casc"], 4, 0.55)
    ev.append((T["casc"] - 0.5, "lights_out_far", -9, 0.4))
    ev.append((cuts[0], "lights_out_far", -5, -0.35))
    ev.append((cuts[1], "lights_out", -5, 0.3))
    ev.append((cuts[2], "lights_out", -2, -0.2))
    ev.append((cuts[3], "lights_out", 0, 0.0))
    return ev
