"""s01 - "The empty pod" (TIREDNESS Episode 2: Lights Out).

CalmCorp gives the creatures bland, flattening names (SPECIMEN 001 / THING 1 ...); the creature
is anything but a thing: it hears the name and is visibly, intelligently offended.

Shot list (scene-local; every time is derived from info cues / lines / lip data):
  S0a [peer, drop)        THUMBNAIL (frame 0, bright): close on the glowing THING 2 pod (the
                          neighbour two pods along, past the tiny THING 7 pod). Thing 1 perches
                          on the pod's base cap, face close to the glass, looking in at its
                          SMALLER sibling curled asleep inside (draw_specimen perch, s 0.5,
                          breathing). A soft yearning look (lids soften, head tilts, its paw
                          rises to the glass, breath fog), held; then a small decisive set
                          (lids/brow slant firm up, ears lift, a breath in and a tiny nod),
                          held; its paw comes off the glass and its eyes go down to the deck.
  S0b [drop, trot)        medium: the pod and the deck. It hops down: anticipation squash, a
                          small arcing hop, a landing squash on the grating (thump), ears
                          follow through; it glances back left along the deck (the way he
                          will come).
  rev 4: the old POV beat (Thing 1 behind the glass of its own empty pod) is gone. Geography:
  THING 2 lies off to the LEFT, down on the lower walkway; Thing 1's own empty pod (THING 1)
  stands to the RIGHT, at the top of the short stair (the same stair they go down in s02).
  S0c [trot, c1)          same framing, no cut: its pupils slide right, the head follows over its
                          shoulder, ears lift (decided); a little hop-turn (it flips at the apex)
                          and it trots off screen-RIGHT (walk cycle x3.3 = 300 px/s).
  S1  [c1, join)          the stair + its pod (it enters screen-LEFT, still trotting): three
                          bounds up the stair, it lands by its pod, sits, and looks back over its
                          shoulder down the stair, waiting. His footsteps (off) -> ears perk.
                          Tiredness walks in from screen-LEFT along the landing and climbs the
                          stair toward it (his feet behind the stair stringer); it tracks him
                          up, looks up at him as he tops the stair, he glances down at it, and as
                          he passes it turns its head to follow him; he walks on to the pod,
                          stops on its far side and turns back (same end positions as rev 3).
                          The camera eases from the stair framing into rev 3's S2 framing.
  S2  [join, touch)       = rev 3 from 0.6 s after his stop: pupils pod -> creature -> pod (head
                          follows); l01 (soft); on "kept you" he crouches down to its level.
  Everything from `join` on is rev 3 frame for frame: rendered on rev 3's clock
  (t - d, with d = the time the new entrance added; see _Rev3View).
  S3  [touch, plate)      Curiosity close-up: slow nod with a slow blink, ears lowering a little;
                          its eyes go to the dusty nameplate (motivates the insert).
  S4  [plate, c5)         insert: the dusty plate; his bandaged hand comes in, the thumb wipes
                          left -> right revealing SPECIMEN 001 / THING 1; l02 "...Thing One."
                          read flatly over it.
  S5a [c5, c5b)           Curiosity CU, the plate beside it: a beat of hope (ears up), then it
                          processes the name: a slow contemptuous blink that opens on flat
                          half-lids, ears sagging, chin up, a tiny huff through the nose.
                          Name tag THING 1 / "according to CalmCorp".
  S5b [c5b, c6)           Tiredness CU (crouched), the plate in frame: l03 "Wow. Creative."
                          deadpan, one brow up a hair, a slow judging blink; his eyes slide from
                          the plate to the creature.
  S6  [c6, plates)        crouched two-shot: it looks up at him, a shared look, it rolls its
                          eyes toward the plate (he follows), then back to him: a small smirk,
                          his faint smirk + tiny nod. They agree. He glances along the row.
  S7  [plates, frown)     his POV: slow pan from NOTHING TO SEE HERE over THING 3 / THING 4 to
                          the next NOTHING TO SEE HERE over THING 5 / THING 6, sleepers inside
                          (rev 4: the pods right of the empty pod are relabelled, SLEEP_R, since
                          THING 2 now lies to the left).
  S8  [frown, c10)        Tiredness CU (standing) under the wall camera: inner brows up, a lip
                          press, silence; l03b "...They're not just things." quiet, to the
                          creature below (glassy eyes); "just" gets a small stress (brows knit a
                          hair more, a tiny head shake, his eyes hold on it), the lids sink on
                          "things"; a press after it. At "camera" the red LED blinks
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

import cairocffi as cairo

from engine import core, sets, props, fx
from engine import human as H
from engine import creatures as CR
from engine.core import (seg, tween, lerp, clamp, smoothstep, ease_in_out, ease_out, ease_in,
                         ease_out_back, state_at)
from audio import sfx
from engine.timeline import LIP_RATE

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


# ---- the opening: Thing 1's smaller sibling asleep in the THING 2 pod -------------------
P2 = next(p for p in CW["pods"] if p["label"] == "THING 2")
P2_GLASS = P2["glass"]
SIB_S = 0.5                    # the sibling: a smaller adult of the species (not baby Joy)
SIB_DX = -20                   # its ground point vs the pod floor point (head on the right,
SIB_TINT = 0.12                # toward Thing 1); teal liquid tint over it


def _sibling(c, x, y, s, t, seed=0, pulse=0.0):
    """Thing 1's little sibling curled asleep (draw_specimen perch, eyes shut), a gentle
    breathing bob; (x, y) = the pod's floor point (sleeper_fn signature). Tinted by the
    pod's liquid so it sits behind the glass. Clipped to the capsule by the caller (the set)
    or by _sibling_live."""
    gx, gy = x + SIB_DX * s / 0.75, y + 2
    br = math.sin(t * math.tau / 4.2)                  # in phase with the rig's own breath
    c.push_group()
    c.save()
    c.translate(gx, gy)
    c.scale(1.0 - 0.006 * br, 1.0 + 0.022 * br)
    c.translate(-gx, -gy)
    CR.draw_specimen(c, gx, gy, SIB_S * s / 0.75, t, pose="perch", expr="calm", flip=False,
                     glow=0.85, ears=0.3)
    c.restore()
    c.set_operator(cairo.OPERATOR_ATOP)
    c.rectangle(gx - 200, gy - 200, 400, 260)
    core.fill(c, core.alpha(core.PAL["power"], SIB_TINT + pulse))
    c.pop_group_to_source()
    c.paint()


def _sibling_live(c, t):
    """The sibling drawn live (breathing) over a bake whose THING 2 pod is empty."""
    gx, gy, gw, gh = P2_GLASS
    c.save()
    core.rrect(c, gx, gy, gw, gh, gw / 2)
    c.clip()
    pulse = 0.10 * (0.5 + 0.5 * math.sin(t * math.tau * 0.25))    # = the set's pod pulse
    _sibling(c, P2["ground"][0], P2["ground"][1], P2["sleeper_s"], t, pulse=pulse)
    c.restore()


def _no_sleeper(*a, **k):
    pass


SLEEP = dict(sleeper_fn=_sleeper, sleeper_fns={"THING 7": _baby, "THING 2": _sibling},
             sleeper_key="s01_sleepers_v4")
SLEEP_LIVE = dict(sleeper_fn=_sleeper, sleeper_fns={"THING 7": _baby, "THING 2": _no_sleeper},
                  sleeper_key="s01_sleepers_v4_live")
# rev 4: THING 2 (the sibling's pod, the opening) now lies to the LEFT of the empty pod, so the
# main-tier pods to its right are other THINGs (S7's pan, the S13 wide): relabelled, ordinary
# sleepers. Only the opening (SLEEP_LIVE: the region around the set's x 1990) shows THING 2.
LABELS_R = {2: ("THING 3", "SPECIMEN 003"), 3: ("THING 4", "SPECIMEN 004"),
            4: ("THING 5", "SPECIMEN 005"), 5: ("THING 6", "SPECIMEN 006"),
            6: ("THING 8", "SPECIMEN 008")}
SLEEP_R = dict(sleeper_fn=_sleeper, sleeper_fns={"THING 7": _baby}, sleeper_key="s01_sleepers_r4",
               labels=LABELS_R)


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
    T = {n: c(n) for n in ("peer", "drop", "open", "pod", "touch", "plate", "perk", "grin", "plates",
                           "frown", "camera", "reach", "click", "dark", "end")}
    # ---- the opening (S0a peer / S0b drop) ----------------------------------------------
    pd = T["drop"] - T["peer"]
    T["p_soft0"] = T["peer"] + 0.22                 # lids soften, head tilts (pupils already on it)
    T["p_soft1"] = T["p_soft0"] + 0.45
    T["p_paw0"] = T["peer"] + 0.42                  # its paw rises to the glass
    T["p_paw1"] = T["p_paw0"] + 0.55
    T["p_fog"] = T["p_paw1"] - 0.1                  # a soft breath fogs the glass
    T["p_set0"] = T["peer"] + max(1.42, 0.55 * pd)  # the decisive set: lids / slant firm up,
    T["p_set1"] = T["p_set0"] + 0.32                # ears lift, a breath in
    T["p_nod"] = T["p_set1"] + 0.02                 # ... and a tiny nod
    T["p_down"] = T["drop"] - 0.34                  # paw off the glass, eyes to the deck
    T["d_head"] = T["drop"] + 0.06                  # (S0b) the head follows the eyes down
    T["d_ant0"] = T["drop"] + 0.34                  # anticipation squash
    T["d_jump"] = T["d_ant0"] + 0.3                 # launch
    T["d_land"] = T["d_jump"] + 0.42                # contact on the grating
    T["d_look"] = T["d_land"] + 0.45                # it looks off along the deck (left)
    for lid, nm, who in (("s01_l01", "l01", "tired"), ("s01_l02", "l02", "tired"),
                         ("s01_l03", "l03", "tired"), ("s01_l03b", "l03b", "tired"),
                         ("s01_l04", "l04", "boss"), ("s01_l05", "l05", "boss")):
        T[nm] = info.line(lid).start
        T[nm + "e"] = info.line(lid).end
        T[nm + "v0"], T[nm + "v"] = _voice_span(info, who, lid)     # voiced span
    T["kept"] = info.word_time("s01_l01", -2)
    T["wow"] = info.word_time("s01_l03", 0)
    T["creative"] = info.word_time("s01_l03", -1)
    T["not"] = info.word_time("s01_l03b", 1)        # "...They're not just things."
    T["just"] = info.word_time("s01_l03b", 2)
    T["things"] = info.word_time("s01_l03b", -1)
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
    T["c5b"] = T["l03"] - 0.25                                  # -> his CU ("Wow. Creative.")
    # S6: the shared look, the eye-roll toward the plate, the smirk
    T["roll"] = T["grin"] - 0.2
    T["c6"] = min(T["l03v"] + 0.25, T["roll"] - 0.4)
    T["tag_out"] = min(T["l03v"], T["c6"] - 0.35)       # gone before the cut to the two-shot
    T["roll_end"] = T["roll"] + ROLL_DUR
    T["smirk"] = T["roll_end"] + 0.12
    T["stand2"] = T["plates"] + 0.4             # he stands up off-screen during the pan
    # S8 + the camera
    T["look_up"] = T["camera"] + 0.65           # his pupils slide up to the camera
    T["c10"] = T["l04"] - 0.95                  # room to settle on her face before the line
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
    # rev 3: "...They're not JUST things." -- the stress lands on "just": the brows knit a
    # hair more (held through "things"), one tiny head shake across "not just"; on
    # "things" the lids sink a little more and the eyes get a touch glassier
    k_ou = 1 - _ramp(t, T["look_up"], T["look_up"] + 0.5)
    k_just = _ramp(t, T["just"] - 0.1, T["just"] + 0.14) * k_ou
    face["brow_in"] += 0.06 * k_just * k_fr_out
    face["brow_ang"] += 0.06 * k_just * k_fr_out
    face["head_turn"] += 0.03 * math.sin(math.tau * seg(t, T["not"] - 0.05, T["just"] + 0.3)) * \
        _pulse(t, T["not"] - 0.05, T["just"] + 0.3)
    k_th = _ramp(t, T["things"], T["things"] + 0.35) * k_ou
    face["lid"] += 0.025 * k_th
    face["head_nod"] += 0.03 * k_th
    kw["tears"] = (0.22 + 0.08 * k_th) * _ramp(t, T["l03b"], T["l03bv"] + 0.2) * \
        (1 - _ramp(t, T["look_up"], T["look_up"] + 0.6))
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
    st = dict(SLEEP_R)
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
# S0a / S0b: the new opening (Thing 1 peers in at its little sibling, then hops down)
# ----------------------------------------------------------------------------
# Scene-local faces for the peer (the rig switches expressions instantly, so the opening
# blends between these through quantised in-between dicts, see _xmix):
#   pa  frame 0: big open soft eyes, looking in (hopeful, small open mouth)
#   pb  the yearning: softened lids, inner corners raised, wet eyes, mouth closes softly
#   pc  the decisive set: lid slant firms (the "brows" of this rig), a slight squint from
#       below, smaller pupils, a firm closed mouth
CR._SPX.setdefault("s01_pa", dict(CR._SPX["hopeful"], es=1.13, up=0.05, upt=-0.24, lo=0.02, pr=0.72,
                                  wet=0.6, tilt=0.0, look=(0, 0), mouth="hope"))
CR._SPX.setdefault("s01_pb", dict(CR._SPX["hopeful"], es=1.12, up=0.27, upt=-0.46, lo=0.10, pr=0.80,
                                  wet=0.95, tilt=0.0, look=(0, 0), mouth="small"))
CR._SPX.setdefault("s01_pc", dict(CR._SPX["hopeful"], es=1.05, up=0.12, upt=0.15, lo=0.17, pr=0.60,
                                  wet=0.4, tilt=0.0, look=(0, 0), mouth="flat"))
_XNUM = ("es", "up", "upt", "lo", "pr", "pw", "ears", "split", "tilt", "wet")


def _xmix(a, b, k, steps=16):
    """Name of a registered in-between of scene expressions a -> b at k (quantised)."""
    q = int(round(clamp(k) * steps))
    if q == 0:
        return a
    if q == steps:
        return b
    name = f"s01m_{a}_{b}_{q:02d}"
    if name not in CR._SPX:
        A, B = CR._SPX[a], CR._SPX[b]
        u = q / steps
        d = dict(A if u < 0.5 else B)
        for kk in _XNUM:
            d[kk] = lerp(A.get(kk, 0.0), B.get(kk, 0.0), u)
        d["look"] = (lerp(A["look"][0], B["look"][0], u), lerp(A["look"][1], B["look"][1], u))
        CR._SPX[name] = d
    return name


PERCH = (2165, 1284)           # Thing 1 sits on THING 2's base cap (right of the glass, facing left)
LAND = (1905, 1500)            # where it lands on the deck (front-left of the pod)
PAW_UP = 0.294                 # wave pose_t: paw fully up with no swing (sin(2pi*1.7*t) = 0)
LOOK_SIB = (-0.5, 0.68)        # from its eyes down-left to the sibling's sleeping face
LOOK_DECK = (-0.55, 0.83)      # down to the deck where it will land
FOG_XY = (2078, 1128)          # its breath on the glass, just in front of the nose
PEER_CAM = ((2066, 1178, 2.82), (2066, 1172, 2.94))
DROP_CAM = (2000, 1192, 1.75)
FACE_LIGHT = (2050, 1112)      # the glass right in front of its face (pod light on it)
PEER_BOX = (1880, 820, 560, 560)   # world rects holding the creature (shade-group clip)
DROP_BOX = (1560, 840, 900, 760)


def peer_kw(t, T):
    """Thing 1 at the THING 2 glass (S0a): soft yearning, then the decisive set."""
    k_ab = smoothstep(seg(t, T["p_soft0"], T["p_soft1"]))
    k_bc = smoothstep(seg(t, T["p_set0"] + 0.08, T["p_set0"] + 0.3))   # behind the blink
    expr = _xmix("s01_pa", "s01_pb", k_ab) if k_bc <= 0.0 else _xmix("s01_pb", "s01_pc", k_bc)
    # eyes on the sibling the whole time; at the end they go down to the deck (planning)
    look = tween(t, [(T["peer"], LOOK_SIB), (T["p_down"], LOOK_SIB), (T["p_down"] + 0.2, LOOK_DECK)],
                 ease_in_out)
    # the head: a soft yearning tilt toward it (follows the softening), the chin lifts a
    # hair with the resolve, a tiny nod, then it follows the eyes down
    tilt = 0.12 * k_ab
    tilt += -0.05 * smoothstep(seg(t, T["p_set0"] + 0.25, T["p_set0"] + 0.55))
    tilt += 0.075 * _pulse(t, T["p_set0"] + 0.55, T["p_set0"] + 0.9)
    tilt += 0.1 * _ramp(t, T["p_down"] + 0.14, T["p_down"] + 0.4)
    # ears: lowered a little with the longing, then they lift with the decision
    ears = lerp(0.44, 0.33, smoothstep(seg(t, T["p_soft0"], T["p_soft1"] + 0.2)))
    ears += (0.76 - 0.33) * ease_out_back(seg(t, T["p_set0"] + 0.22, T["p_set0"] + 0.55), 1.4)
    # the paw rises softly to the glass, rests, and comes off it at the end
    paw = tween(t, [(T["p_paw0"], 0.0), (T["p_paw1"], 1.0), (T["p_down"], 1.0), (T["p_down"] + 0.3, 0.0)],
                ease_in_out)
    # lids: frame 0 open; the thought changes on a slow blink (soft lids close, firm ones open)
    b0 = T["p_set0"]
    blink = tween(t, [(b0, 0.0), (b0 + 0.17, 1.0), (b0 + 0.24, 1.0), (b0 + 0.5, 0.0)]) \
        if b0 <= t <= b0 + 0.5 else 0.0
    return dict(pose="wave", pose_t=PAW_UP * paw, expr=expr, look=look, tilt=tilt, ears=ears,
                face=0.5, blink=blink, glow=1.0, flip=True)


def _breath(t, T):
    """(sx, sy) about the feet: the breath in with the decision (S0a)."""
    k = tween(t, [(T["p_set0"] + 0.1, 0.0), (T["p_set0"] + 0.55, 1.0), (T["p_set0"] + 1.15, 0.4)], ease_in_out)
    return 1.0 - 0.008 * k, 1.0 + 0.028 * k


def _scaled_about(ctx, x, y, sx, sy, fn):
    if sx == 1.0 and sy == 1.0:
        return fn()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sx, sy)
    ctx.translate(-x, -y)
    a = fn()
    ctx.restore()
    return a


class _shaded_box:
    """= sets.shaded(ctx, sets.catwalk, t, layer="shade") at full power, for a creature inside
    `box` (world rect): the (static) shade light is cached as a bitmap for the box instead of
    re-filling three frame-sized radial gradients every frame (perf, same look)."""
    def __init__(self, ctx, box, key, light=None):
        self.ctx, self.box, self.key = ctx, box, key
        self.light = light or (lambda cc: sets.catwalk(cc, 0.0, layer="shade"))

    def __enter__(self):
        c = self.ctx
        c.save()
        c.rectangle(*self.box)
        c.clip()
        c.push_group()
        return c

    def __exit__(self, *exc):
        c = self.ctx
        c.save()
        c.set_operator(cairo.OPERATOR_ATOP)
        core.cached(c, ("s01_cwshade", self.key), *self.box, self.light)
        c.restore()
        c.pop_group_to_source()
        c.paint()
        c.restore()


# ---- rev 3b: Thing 1 is OUTSIDE the glass, the sibling INSIDE ----------------------
# The THING 2 glass gets a visible front surface (cooler tint + curved sheen streaks) drawn
# over the sibling and the bubbles but UNDER Thing 1, so its silhouette cuts the sheen.
# Thing 1 is no longer washed with the catwalk's uniform teal shade: it keeps its own solid
# indigo, lit from the front by the glass (teal-white falloff from the pod; the far side
# stays dark indigo), with its teal rim. Its paw leaves a soft contact smudge on the glass.
PAW_XY = (2040, 1108)          # where the raised paw meets the glass (rig anchor at full raise)
GLASS_LIGHT = (2000, 1060)     # the pod glass, as the light source on Thing 1


def _glass_front(c):
    """THING 2's glass front surface (world coords; draw after the sibling, before Thing 1)."""
    gx, gy, gw, gh = P2_GLASS
    c.save()
    core.rrect(c, gx, gy, gw, gh, gw / 2)
    c.clip()
    c.rectangle(gx, gy, gw, gh)
    core.fill(c, (0.03, 0.16, 0.22, 0.13))            # a touch cooler / darker over the inside
    # curved sheen streaks: a long one from the upper right over the bubbles to the sleeper's
    # back, and a second one that runs BEHIND Thing 1's head and paw (its silhouette cuts it)
    for (pts, bands) in (
            ([(gx + gw * 0.95, gy + gh * 0.10), (gx + gw * 0.62, gy + gh * 0.42),
              (gx + gw * 0.30, gy + gh * 0.74), (gx + gw * 0.04, gy + gh * 0.98)],
             ((0, 64, 0.08), (-6, 13, 0.26))),
            ([(gx + gw * 1.02, gy + gh * 0.40), (gx + gw * 0.80, gy + gh * 0.60),
              (gx + gw * 0.50, gy + gh * 0.79), (gx + gw * 0.12, gy + gh * 1.04)],
             ((0, 54, 0.09), (-4, 11, 0.30), (26, 5, 0.22)))):
        for (dx, w_, a_) in bands:
            c.move_to(pts[0][0] + dx, pts[0][1])
            c.curve_to(pts[1][0] + dx, pts[1][1], pts[2][0] + dx, pts[2][1], pts[3][0] + dx, pts[3][1])
            core.stroke(c, (1.0, 1.0, 1.0, a_), w_, cap="round")
    c.restore()
    # the glass edge catching the light (left rim)
    c.new_sub_path()
    c.arc(gx + gw / 2, gy + gw / 2, gw / 2 - 7, math.pi * 1.05, math.pi * 1.45)
    core.stroke(c, (0.92, 1.0, 1.0, 0.45), 4, cap="round")


def _glass_lit(c):
    """Thing 1's light (painted ATOP it, cached): the glass in front of it lights its near
    side teal-white; the far side keeps its own dark indigo."""
    core.radial_glow(c, GLASS_LIGHT[0], GLASS_LIGHT[1], 330, "#bdfcf3", 0.5)
    core.radial_glow(c, FACE_LIGHT[0], FACE_LIGHT[1], 170, "#e9fffd", 0.18)


def _contact(c, k_paw, k_print):
    """On the glass, under Thing 1: a soft glow where the paw presses, and the paw print it
    leaves when it lifts off (fading)."""
    if k_paw > 0.003:
        core.radial_glow(c, PAW_XY[0], PAW_XY[1], 58, "#e6fffb", 0.28 * k_paw)     # fog smudge
        core.radial_glow(c, PAW_XY[0], PAW_XY[1], 38, "#f6fffd", 0.62 * k_paw)     # contact glow
    if k_print > 0.003:
        _paw_print(c, PAW_XY[0] - 2, PAW_XY[1] + 2, 0.82, k_print)


def _ledge_shadow(c, x, y, k):
    if k > 0.003:
        core.ellipse(c, x + 18, y + 2, 112, 10)
        core.fill(c, core.alpha(core.PAL["ink"], 0.34 * k))


def _contact_k(t, T):
    """(paw pressing, paw print) amounts on the THING 2 glass."""
    k_paw = tween(t, [(T["p_paw1"] - 0.08, 0.0), (T["p_paw1"] + 0.06, 1.0), (T["p_down"], 1.0),
                      (T["p_down"] + 0.12, 0.0)])
    k_print = tween(t, [(T["p_paw1"] - 0.05, 0.0), (T["p_paw1"] + 0.15, 0.85), (T["p_down"] + 0.1, 0.85),
                        (T["p_down"] + 0.2, 0.75), (T["drop"] + 0.9, 0.0)])
    return k_paw, k_print


def shot_peer(ctx, t, T, info):
    k = ease_in_out(seg(t, T["peer"], T["drop"]))
    cam = _cam_lerp(PEER_CAM, k)
    fog = tween(t, [(T["p_fog"], 0.0), (T["p_fog"] + 0.35, 0.55), (T["p_fog"] + 0.6, 0.5),
                    (T["p_fog"] + 1.5, 0.0)])
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, plate_dust=1.0, **SLEEP_LIVE)
        _sibling_live(ctx, t)
        _glass_front(ctx)
        _contact(ctx, *_contact_k(t, T))
        _ledge_shadow(ctx, PERCH[0], PERCH[1], 1.0)
        with _shaded_box(ctx, PEER_BOX, "peer_lit", light=_glass_lit):
            kw = peer_kw(t, T)
            sx, sy = _breath(t, T)
            _scaled_about(ctx, PERCH[0], PERCH[1], sx, sy,
                          lambda: CR.draw_specimen(ctx, PERCH[0], PERCH[1], S, t, **kw))
            if fog > 0.003:
                # its breath on the glass, behind its snout (drawn under the creature)
                ctx.set_operator(cairo.OPERATOR_DEST_OVER)
                core.radial_glow(ctx, FOG_XY[0], FOG_XY[1], 46, "#f2fffd", 0.75 * fog)
                ctx.set_operator(cairo.OPERATOR_OVER)


def drop_kw(t, T):
    """Thing 1 hops down from the pod cap to the deck (S0b). -> (x, y, sx, sy, kw)."""
    j, ld = T["d_jump"], T["d_land"]
    dur = ld - j
    if t < j:
        x, y = PERCH
        pose, pose_from, mix = "sit", None, 1.0
    elif t < ld:
        u = (t - j) / dur
        h = 82.0                                    # a small hop up, then the fall (parabola)
        x = lerp(PERCH[0], LAND[0], u)
        y = PERCH[1] + (LAND[1] - PERCH[1]) * u - 4 * h * u * (1 - u)
        pose, pose_from, mix = "stand", "sit", smoothstep(seg(t, j, j + 0.24))
    else:
        x, y = LAND
        pose, pose_from, mix = "stand", None, 1.0
    # squash & stretch about the ground point
    ka = ease_in_out(seg(t, T["d_ant0"], j))
    sx, sy = 1.0 + 0.07 * ka, 1.0 - 0.13 * ka                          # anticipation squash
    if j <= t < ld:
        u = (t - j) / dur
        st = tween(u, [(0.0, -0.13), (0.18, 0.12), (0.45, 0.03), (0.9, 0.08), (1.0, 0.08)])
        sx, sy = 1.0 - 0.55 * st, 1.0 + st                             # launch stretch .. fall
    elif t >= ld:
        q = tween(t, [(ld, 0.08), (ld + 0.07, -0.16), (ld + 0.2, 0.035), (ld + 0.34, -0.01),
                      (ld + 0.44, 0.0)], ease_in_out)
        sx, sy = 1.0 - 0.6 * q, 1.0 + q                                # landing squash, settle
    # ears: pinned a little for the jump, they stream up in the fall, flop on the landing and
    # spring back
    ears = tween(t, [(T["drop"], 0.76), (T["d_ant0"], 0.76), (j, 0.6), (j + 0.16, 0.7),
                     (ld - 0.02, 0.95), (ld + 0.09, 0.42), (ld + 0.42, 0.7)], ease_in_out)
    look = tween(t, [(T["drop"], LOOK_DECK), (j - 0.05, LOOK_DECK), (j + 0.2, (-0.4, 0.7)),
                     (ld + 0.12, (-0.4, 0.7)), (ld + 0.3, (-0.3, 0.1)),
                     (T["d_look"], (-0.3, 0.1)), (T["d_look"] + 0.16, (-0.95, -0.1))], ease_in_out)
    # head: follows the eyes down, a dip on the impact; then it looks off along the deck
    # (left: toward its own pod), the head following the pupils
    tilt = 0.1 + 0.1 * _ramp(t, T["d_head"], T["d_head"] + 0.25)
    tilt -= 0.14 * _ramp(t, j - 0.08, j + 0.2)
    tilt += 0.05 * _pulse(t, ld, ld + 0.3)
    tilt -= 0.1 * _ramp(t, T["d_look"] + 0.15, T["d_look"] + 0.45)
    face = lerp(0.5, 0.8, _ramp(t, j, j + 0.25))
    face = lerp(face, 1.0, _ramp(t, T["d_look"] + 0.15, T["d_look"] + 0.45))
    blink = 0.0
    if ld <= t <= ld + 0.3:
        blink = tween(t, [(ld, 0.0), (ld + 0.06, 0.55), (ld + 0.12, 0.55), (ld + 0.28, 0.0)])
    # body pitch in the hop: nose up a hair at the launch, nose down in the fall (it faces
    # left, so nose-down is counter-clockwise), level on the landing
    rot = 0.0
    if j <= t < ld:
        u = (t - j) / dur
        rot = -tween(u, [(0.0, -0.08), (0.35, 0.02), (0.85, 0.2), (1.0, 0.2)], ease_in_out)
    elif t >= ld:
        rot = -0.2 * (1.0 - ease_out(seg(t, ld - 0.02, ld + 0.08)))
    kw = dict(pose=pose, pose_from=pose_from, pose_mix=mix, expr="s01_pc", look=look, tilt=tilt,
              ears=ears, face=face, blink=blink, glow=1.0, flip=True)
    return x, y, sx, sy, rot, kw


def shot_drop(ctx, t, T, info):
    # follow the fall down a little
    k = ease_in_out(seg(t, T["d_jump"] - 0.05, T["d_land"] + 0.35))
    cam = (DROP_CAM[0] - 14 * k, DROP_CAM[1] + 40 * k, DROP_CAM[2])
    x, y, sx, sy, rot, kw = drop_kw(t, T)
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, plate_dust=1.0, **SLEEP_LIVE)
        _sibling_live(ctx, t)
        _glass_front(ctx)
        _contact(ctx, *_contact_k(t, T))
        _ledge_shadow(ctx, PERCH[0], PERCH[1], 1.0 - smoothstep(seg(t, T["d_jump"] - 0.02, T["d_jump"] + 0.12)))
        # its contact shadow on the grating grows as it comes down
        ks = smoothstep(seg(t, T["d_jump"] + 0.05, T["d_land"]))
        if ks > 0.0:
            core.ellipse(ctx, LAND[0] + 4, LAND[1] + 4, 120 * lerp(0.55, 1.0, ks), 16 * lerp(0.55, 1.0, ks))
            core.fill(ctx, core.alpha(core.PAL["ink"], 0.32 * ks))
        with _shaded_box(ctx, DROP_BOX, "drop_lit", light=_glass_lit):
            ctx.save()
            if rot:
                ctx.translate(x, y - 120 * S)          # pitch about the body centre
                ctx.rotate(rot)
                ctx.translate(-x, -(y - 120 * S))
            _scaled_about(ctx, x, y, sx, sy, lambda: CR.draw_specimen(ctx, x, y, S, t, **kw))
            ctx.restore()


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
        sets.catwalk(ctx, 1.0, plate_dust=0.0, plate_wipe=1.0, cam_led=1.0, cam_face=1.0, **SLEEP_R)
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


SW_FINGER_LOW = 1289.0     # lowest fingertip y she reaches on the toggle's line (pivot cap top)


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
        # anat pass: the knob at OFF (y 1336) is out of her reach, and the clamped arm slid the
        # finger off the bat to the right (S12, from the frame after the click). The finger now
        # follows the knob down to the lowest point it can reach on the toggle's line (the top
        # of the pivot cap) and stays there while the toggle snaps over. Before the click the
        # target (y 1258.8) is untouched.
        gy = min(gy, SW_FINGER_LOW)
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


BOSS_CAM_Y0 = 760          # the big monitor (CCTV) fills the upper frame, her chair below
BOSS_CAM_Y1 = 1061         # her face at screen y ~830, chin ~970: well clear of the caption band


def shot_control(ctx, t, T, info):
    # start on the monitor, tilt down to her; settled before "Right on time." begins
    t_end = T["l04"] - 0.05
    k = ease_in_out(seg(t, min(T["c10"] + 0.35, t_end - 0.45), t_end))
    k2 = seg(t, t_end, T["reach"])
    cam = (lerp(1700, 1660, k), lerp(BOSS_CAM_Y0, BOSS_CAM_Y1, k) - 6 * k2, 1.9 + 0.05 * k2)
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


def _s2_cam(t, T, info):
    """rev 3's S2 camera: the camera eases in as he arrives, then down and in with him as he
    crouches (from wstop + 0.6 it no longer depends on his walk-in)."""
    xt = tired_kw(t, T, info)["x"]
    kt = ease_in_out(seg(t, T["wstop"] - 0.9, T["wstop"] + 0.6))
    cx0 = lerp(xt - 140, 1008, kt)                # track him in, then settle on the pod
    k0 = ease_in_out(seg(t, T["wstop"], T["wstop"] + 1.0))
    k1 = ease_in_out(seg(t, T["cr0"] - 0.2, T["touch"] - 0.1))
    return (lerp(cx0 + 5 * k0, 962, k1), lerp(lerp(1185, 1195, k0), 1212, k1),
            lerp(lerp(1.3, 1.48, k0), 1.92, k1))


def _render_rev3(ctx, t, info):
    """rev 3's render, unchanged, on rev 3's clock (info = _Rev3View). Used for the opening
    (t < trot) and for everything from `join` on; the old POV beat and the walk-in are replaced
    by the new entrance (shot_turn / shot_meet)."""
    T = TT(info)
    if t < T["drop"]:
        shot_peer(ctx, t, T, info)
    elif t < T["open"]:
        shot_drop(ctx, t, T, info)
    elif t < T["touch"]:
        # S2 (from 0.6 s after his stop): l01, crouch on "kept you"
        catwalk_shot(ctx, t, T, info, _s2_cam(t, T, info), rail=False)
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
        fx.name_tag(ctx, "THING 1", "according to CalmCorp", t, T["tag_in"], T["tag_out"],
                    x=90, y=170, color="curiosity")


# ============================================================================
# rev 4: the new entrance (S0c: it turns and trots off screen-right; S1: up the stair to its
# own pod, it waits, he climbs up toward it, they meet at the pod)
# ============================================================================
REV3_OPEN = 2.2      # rev 3's POV hold ('open' -> 'pod'). The beats after it keep rev 3's
                     # clock: d = (trot -> pod) - REV3_OPEN is the time the new entrance adds


class _ShLine:
    def __init__(self, L, d):
        self.id, self.who, self.text, self.caption = L.id, L.who, L.text, L.caption
        self.meta, self.nocap = L.meta, L.nocap
        # (engine.timeline rounds line times to 4 decimals: this gives rev 3's exact floats)
        self.start, self.end = round(L.start - d, 4), round(L.end - d, 4)

    @property
    def dur(self):
        return self.end - self.start


class _Rev3View:
    """The live timeline as rev 3 saw it: the cues and lines after the entrance moved back by
    d, and 'open' = 'trot'. TT(view) is rev 3's T, so every later beat is rendered on rev 3's
    clock: frame f of this cut is rev 3's frame f - 24 d (pixel-identical).
    Bit-exactness: d is snapped to whole frames, line times are rebuilt the way the timeline
    rounds them, lip samples are looked up the way rev 3 indexed them, and a T value that
    lands exactly on a frame (the first light cut, casc) is nudged up one ulp: rev 3's float
    cue sums put it just after its frame (see _view)."""
    def __init__(self, info):
        self._i = info
        self.id = info.id
        self.tr = info.cue("trot") if "trot" in info.cues else info.cue("open")
        d = info.cue("pod") - self.tr - REV3_OPEN
        if abs(d * core.FPS - round(d * core.FPS)) < 1e-6:
            d = round(d * core.FPS) / core.FPS
        self.d = d
        self.dur = info.dur - d
        self._lines = [_ShLine(L, d) for L in info.lines]
        self._by_id = {L.id: L for L in self._lines}

    def _sh(self, v):
        return v - self.d if v > self.tr + 1e-6 else v

    def cue(self, name, default=None):
        if name in ("open", "trot"):
            return self.tr
        return self._sh(self._i.cue(name, default))

    def line(self, lid):
        return self._by_id[lid]

    def mouth(self, who, t):
        for L in self._lines:
            if L.who == who and L.start <= t < L.end:
                i = int((t - L.start) * LIP_RATE)          # = rev 3's sample index
                Ln = self._i.line(L.id)
                return self._i.mouth(who, min(Ln.start + (i + 0.5) / LIP_RATE, Ln.end - 1e-6))
        return (0.0, 0.0)

    def word_time(self, lid, k):
        Ln = self._i.line(lid)          # (the lip-sync word starts are stored to 3 decimals)
        return self._by_id[lid].start + round(self._i.word_time(lid, k) - Ln.start, 6)

    def snap(self, t):
        """rev 3's frame time for t - d (exact float)."""
        tp = t - self.d
        f = round(tp * core.FPS)
        return f / core.FPS if abs(tp * core.FPS - f) < 1e-6 else tp


_VIEWS = {}


def _view(info):
    v = _VIEWS.get(id(info))
    if v is None or v._i is not info or abs(v.dur + v.d - info.dur) > 1e-9:
        v = _VIEWS[id(info)] = _Rev3View(info)
        T = TT(v)
        for k_, val in T.items():          # frame-coincident thresholds: as rev 3's floats had them
            if val > v.tr + 1e-6 and abs(val * core.FPS - round(val * core.FPS)) < 1e-9:
                T[k_] = math.nextafter(val, math.inf)
    return v


# ---- geography -------------------------------------------------------------------------
ST = CW["stair_steps"]                       # tread centres, top first (rise 45, run 86)
ST_TOP = CW["stair_top"][0]                  # 640: the deck starts here
ST_RISE = ST[0][1] - FEET
ST_RUN = ST[0][0] - ST[1][0]
LANDY = CW["landing_feet_y"]                 # the lower walkway (1770)


def _stair_ramp(x):
    """The line through the tread centres (deck -> stair -> landing)."""
    return clamp(FEET + ST_RISE * ((ST_TOP - x) / ST_RUN + 0.5), FEET, LANDY)


def _tired_ground(x):
    """His ground: on the stair it sits 40 px under the treads so his shoes go behind the front
    stringer (drawn over him) instead of sliding on the open treads; landing / deck exact."""
    off = 40.0 * smoothstep(seg(x, 175, 255)) * (1.0 - smoothstep(seg(x, 560, 668)))
    return _stair_ramp(x) + off


def _climb_rate(x):
    """Walk-cycle rate (1 = the flat walk): a slower, heavier step up the stair."""
    return 1.0 - 0.15 * smoothstep(seg(x, 150, 230)) * (1.0 - smoothstep(seg(x, 600, 680)))


def _eyes_tired(x, y):
    return (x + 48, y - 592)                 # his eye midpoint (walk / stand, turn ~0.55, s 0.75)


def _eyes_cur(face):
    return (CUR_X + lerp(35, 60, (face + 1) / 2), FEET - 180)     # sitting by its pod


def _aim(frm, to, ln=1.0):
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    n = math.hypot(dx, dy) or 1.0
    return (ln * dx / n, ln * dy / n)


# ---- shot A (S0c) ---------------------------------------------------------------------
TROT_V = 300.0                               # its trot: the walk cycle at x3.33 (paws planted)
CUR_STEP = CR.SPEC_WALK_SPEED * S            # 90 px of travel per walk-phase second
A_EXIT = 2330                                # cut when its head and half its body are out (right)
BOX_A = (1560, 840, 1340, 760)               # shade box for the trot off (DROP_BOX, wider)
# ---- shot B (S1) ----------------------------------------------------------------------
B_CAM0 = (520, 1290, 1.25)                   # the stair (left) + its pod (right): it waits screen-right
B_CAM1 = (528, 1284, 1.27)                   # slow push while it waits
B_X0 = -10                                   # it trots in along the landing (its head in frame at the cut)
B_TAKE1 = 142                                # first bound from the landing
B_HOPS = (((ST[3][0], ST[3][1]), 0.25, 50.0), ((ST[1][0], ST[1][1]), 0.24, 48.0),
          ((CUR_X, FEET), 0.32, 62.0))       # (landing point, air time, apex height)
B_GROUND = (0.10, 0.12)                      # time on a tread between bounds
HOP_PITCH = -0.45                            # nose-up along the stair slope while on it


def _trot_x(t, go):
    """x travelled since `go` (speed eases 0 -> TROT_V over 0.3 s)."""
    u = seg(t, go, go + 0.3)
    dist = TROT_V * 0.3 * (u ** 3 - 0.5 * u ** 4)
    if t > go + 0.3:
        dist = TROT_V * 0.15 + TROT_V * (t - go - 0.3)
    return dist


_NT = {}


def NT(info):
    """Timing of the new entrance (absolute scene seconds; all from the cues)."""
    k = (id(info), info.dur)
    if k in _NT:
        return _NT[k]
    V = _view(info)
    T = TT(V)
    d, tr = V.d, V.tr
    N = dict(d=d, tr=tr)
    # ---- shot A: same framing as the landing (no cut)
    N["a_eye"] = tr + 0.06                   # pupils slide right (behind it: toward its own pod)
    N["a_head0"] = tr + 0.2                  # the head follows, over its shoulder
    N["a_head1"] = tr + 0.58
    N["a_set"] = tr + 0.62                   # ears lift, a tiny nod: that way
    N["a_ant"] = tr + 0.86                   # anticipation squash
    N["a_jump"] = tr + 1.0                   # the hop-turn (flips at the apex)
    N["a_land"] = N["a_jump"] + 0.22
    N["a_go"] = N["a_land"] + 0.06           # first trot step
    N["c1"] = N["a_go"] + 0.3 + (A_EXIT - LAND[0] - TROT_V * 0.15) / TROT_V
    # ---- shot B: it trots in, bounds up the stair, sits, looks back
    c1 = N["c1"]
    hops = []
    take = c1 + (B_TAKE1 - B_X0) / TROT_V
    p0 = (B_TAKE1, LANDY)
    for i, (p1, air, h) in enumerate(B_HOPS):
        hops.append(dict(take=take, land=take + air, p0=p0, p1=p1, h=h))
        p0 = p1
        if i < len(B_GROUND):
            take = take + air + B_GROUND[i]
    N["hops"] = hops
    N["sat"] = hops[-1]["land"]              # last bound lands by its pod
    N["sit0"], N["sit1"] = N["sat"] + 0.1, N["sat"] + 0.45
    N["back0"] = N["sat"] + 0.6              # pupils go back down the stair...
    N["back1"] = N["back0"] + 0.52           # ... the head follows over its shoulder
    # ---- Tiredness: walks in along the landing, up the stair, along the deck to rev 3's stop
    N["wstop"] = T["wstop"] + d
    N["P"] = T["pod"] + d
    N["join"] = N["wstop"] + 0.6             # from here on: rev 3, frame for frame
    tab = []
    v0 = _V_WALK
    tt, x, ph = N["wstop"], TIR_X - 0.15 * v0, T["wstop"] - T["w0"]
    dt = 1.0 / 480.0
    while x > -700:
        tab.append((tt, x, ph))
        r = _climb_rate(x)
        tt, x, ph = tt - dt, x - v0 * r * dt, ph - r * dt
    tab.reverse()
    N["walk"] = tab

    def t_at_x(xx):
        for (t0, x0, _) in tab:
            if x0 >= xx:
                return t0
        return tab[-1][0]
    N["t_x"] = t_at_x
    N["enter"] = t_at_x(-10)                 # his leading shoulder crosses the frame edge
    N["climb0"] = t_at_x(167)                # first step up
    N["top"] = t_at_x(ST_TOP)                # on the deck
    N["near"] = t_at_x(690)                  # right beside it
    N["pass"] = t_at_x(900)                  # past it, walking on to the pod
    # his steps (walk contacts: the phase crosses a multiple of 0.5); the creature hears the
    # first one that comes after it has looked back
    steps = []
    for (a, b) in zip(tab, tab[1:]):
        if math.floor(a[2] / 0.5) != math.floor(b[2] / 0.5):
            steps.append((b[0], b[1]))
    N["steps_all"] = steps
    N["steps"] = [s for s in steps if s[0] >= N["back1"] + 0.45]
    N["perk"] = (N["steps"][0][0] if N["steps"] else N["enter"] - 0.4) + 0.1
    # the camera leaves the stair framing when he starts up the stair
    N["cam0"] = max(N["climb0"], N["back1"] + 0.3)
    _NT[k] = N
    return N


def _walk_at(N, t):
    tab = N["walk"]
    if t <= tab[0][0]:
        return tab[0][1], tab[0][2]
    lo, hi = 0, len(tab) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if tab[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    (t0, x0, p0), (t1, x1, p1) = tab[lo], tab[hi]
    u = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return lerp(x0, x1, u), lerp(p0, p1, u)


# ---- shot A: Thing 1 turns toward its pod and trots off screen-right -----------------
def turn_kw(t, T, N):
    """S0c, continuing drop_kw (it stands where it landed, facing left, glancing left).
    -> (x, y, sx, sy, rot, kw)"""
    x, y, sx, sy, rot, kw = drop_kw(t, T)
    j, ld, go = N["a_jump"], N["a_land"], N["a_go"]
    # its pupils slide right (behind it: its own pod is that way), the head follows over its
    # shoulder; after the hop-turn it faces right and looks ahead
    look = tween(t, [(N["tr"], (-0.95, -0.1)), (N["a_eye"], (-0.95, -0.1)), (N["a_eye"] + 0.16, (0.95, -0.12)),
                     (go + 0.1, (0.95, -0.12)), (go + 0.35, (0.9, 0.08))], ease_in_out)
    face = tween(t, [(N["a_head0"], 1.0), (N["a_head1"], -1.0)], ease_in_out)
    flip = t < j + 0.11                      # it flips at the apex of the hop-turn
    if not flip:
        face = 1.0                           # (flipped: looking right = forward)
    # a quick blink with the head turn; the decided ears lift, a tiny nod
    blink = 0.0
    b0 = N["a_head0"] + 0.04
    if b0 <= t <= b0 + 0.26:
        blink = tween(t, [(b0, 0.0), (b0 + 0.08, 1.0), (b0 + 0.12, 1.0), (b0 + 0.26, 0.0)])
    ears = 0.7 + 0.1 * ease_out_back(seg(t, N["a_set"], N["a_set"] + 0.3), 1.6)
    ears = tween(t, [(j - 0.05, ears), (j + 0.12, 0.62), (ld - 0.02, 0.86), (ld + 0.08, 0.6),
                     (go + 0.35, 0.72)]) if t >= j - 0.05 else ears
    tilt = kw["tilt"] + 0.07 * _pulse(t, N["a_set"], N["a_set"] + 0.32)
    tilt = lerp(tilt, 0.0, _ramp(t, j, j + 0.2))
    # the hop-turn: anticipation squash, a small hop in place (flip at the apex), landing squash
    if t < j:
        ka = ease_in_out(seg(t, N["a_ant"], j))
        sx, sy = 1.0 + 0.06 * ka, 1.0 - 0.11 * ka
    elif t < ld:
        u = (t - j) / (ld - j)
        y = LAND[1] - 4 * 38.0 * u * (1 - u)
        st = tween(u, [(0.0, -0.11), (0.2, 0.09), (0.5, 0.02), (0.85, 0.05), (1.0, 0.05)])
        sx, sy = 1.0 - 0.55 * st, 1.0 + st
    else:
        q = tween(t, [(ld, 0.05), (ld + 0.06, -0.12), (ld + 0.18, 0.02), (ld + 0.3, 0.0)], ease_in_out)
        sx, sy = 1.0 - 0.6 * q, 1.0 + q
    # the trot (walk cycle, x3.33): position and phase together, so the paws stay planted
    pose, pose_from, mix, pose_t = "stand", None, 1.0, None
    if t >= go:
        dist = _trot_x(t, go)
        x = LAND[0] + dist
        pose, pose_from, mix, pose_t = "walk", "stand", smoothstep(seg(t, go, go + 0.16)), dist / CUR_STEP
    kw.update(pose=pose, pose_from=pose_from, pose_mix=mix, pose_t=pose_t, look=look, face=face,
              flip=flip, blink=blink, ears=ears, tilt=tilt)
    return x, y, sx, sy, 0.0, kw


def shot_turn(ctx, t, T, N, info):
    cam = (DROP_CAM[0] - 14, DROP_CAM[1] + 40, DROP_CAM[2])      # = shot_drop's settled framing
    x, y, sx, sy, rot, kw = turn_kw(t, T, N)
    j, ld = N["a_jump"], N["a_land"]
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, t, plate_dust=1.0, **SLEEP_LIVE)
        _sibling_live(ctx, t)
        _glass_front(ctx)
        _contact(ctx, *_contact_k(t, T))
        # its contact shadow (shrinks a little in the hop)
        hk = 1.0 - 0.3 * (_pulse(t, j, ld) if j <= t <= ld else 0.0)
        core.ellipse(ctx, x + 4, LAND[1] + 4, 120 * hk, 16 * hk)
        core.fill(ctx, core.alpha(core.PAL["ink"], 0.32 * hk))
        box, key = (DROP_BOX, "drop_lit") if t < j else (BOX_A, "trot_lit")
        with _shaded_box(ctx, box, key, light=_glass_lit):
            _scaled_about(ctx, x, y, sx, sy, lambda: CR.draw_specimen(ctx, x, y, S, t, **kw))


# ---- shot B: up the stair to its pod; he climbs up toward it; they meet ---------------
def _cur_path(t, N):
    """Thing 1 in S1 -> dict(x, y, sx, sy, rot, pose, pose_from, mix, pose_t, air)."""
    c1, hops = N["c1"], N["hops"]
    o = dict(sx=1.0, sy=1.0, rot=0.0, pose="stand", pose_from=None, mix=1.0, pose_t=None, air=False)
    h0 = hops[0]
    if t < h0["take"]:
        x = B_X0 + TROT_V * (t - c1)
        ka = ease_in_out(seg(t, h0["take"] - 0.07, h0["take"]))       # running crouch
        o.update(x=x, y=LANDY, pose="walk", pose_t=(x - B_X0) / CUR_STEP,
                 sx=1.0 + 0.05 * ka, sy=1.0 - 0.09 * ka)
        return o
    take_walk = (h0["p0"][0] - B_X0) / CUR_STEP
    for i, h in enumerate(hops):
        nxt = hops[i + 1] if i + 1 < len(hops) else None
        last = nxt is None
        if t < h["land"]:
            u = (t - h["take"]) / (h["land"] - h["take"])
            (x0, y0), (x1, y1) = h["p0"], h["p1"]
            x = lerp(x0, x1, u)
            y = y0 + (y1 - y0) * u - 4 * h["h"] * u * (1 - u)
            st = tween(u, [(0.0, -0.09), (0.16, 0.10), (0.5, 0.02), (0.85, 0.05), (1.0, 0.05)])
            r0 = 0.0 if i == 0 else HOP_PITCH
            r1 = 0.08 if last else HOP_PITCH
            rot = tween(u, [(0.0, r0 - 0.06), (0.45, -0.26), (1.0, r1)], ease_in_out)
            o.update(x=x, y=y, sx=1.0 - 0.55 * st, sy=1.0 + st, rot=rot, air=True)
            if i == 0:
                o.update(pose_from="walk", mix=smoothstep(seg(t, h["take"] - 0.04, h["take"] + 0.1)),
                         pose_t=take_walk)
            return o
        if last or t < nxt["take"]:
            (x1, y1) = h["p1"]
            ld = h["land"]
            q = tween(t, [(ld, 0.05), (ld + 0.06, -0.13), (ld + 0.16, 0.03), (ld + 0.26, 0.0)], ease_in_out)
            if not last:
                ka = ease_in_out(seg(t, nxt["take"] - 0.06, nxt["take"]))
                q = min(q, -0.09 * ka) if ka > 0 else q
            rot = HOP_PITCH if not last else 0.08 * (1.0 - ease_out(seg(t, ld - 0.02, ld + 0.1)))
            o.update(x=x1, y=y1, sx=1.0 - 0.6 * q, sy=1.0 + q, rot=rot)
            if last:
                o.update(pose="sit", pose_from="stand", mix=smoothstep(seg(t, N["sit0"], N["sit1"])))
            return o
    return o


def meet_cur_kw(t, T, N, V):
    """Thing 1 in S1 (it ends exactly in rev 3's state: sitting by its pod, looking at him)."""
    tp = t - N["d"]
    R = cur_kw(tp, T, V)
    wb = smoothstep(seg(t, N["P"] + 0.45, N["P"] + 1.55))
    if wb >= 1.0:
        return R, None
    p = _cur_path(t, N)
    off = CR._SPX["hopeful"]["look"]
    sat = t >= N["sat"]
    # where its eyes go (true gaze; the expression's own offset is removed below)
    xt, _ph = _walk_at(N, t)
    he = _eyes_tired(xt, _tired_ground(xt))
    if not sat:
        gaze = (0.75, -0.4) if p["air"] or t > N["hops"][0]["take"] else (0.8, -0.2)   # up the stair
        face = 1.0
    else:
        gaze = tween(t, [(N["sat"], (0.75, -0.3)), (N["sat"] + 0.25, (0.6, -0.1)),
                         (N["back0"], (0.6, -0.1)), (N["back0"] + 0.16, (-0.85, 0.35)),
                         (N["perk"] - 0.05, (-0.85, 0.35)), (N["perk"] + 0.12, (-0.92, 0.42))], ease_in_out)
        # once he is in view its eyes follow his face up the stair
        k_trk = _ramp(t, N["enter"] - 0.15, N["enter"] + 0.2)
        if k_trk > 0.0:
            fc = tween(t, [(N["near"], -1.0), (N["pass"], 0.62)], ease_in_out)
            ag = _aim(_eyes_cur(fc), he)
            gaze = (lerp(gaze[0], ag[0], k_trk), lerp(gaze[1], ag[1], k_trk))
        face = tween(t, [(N["sat"], 1.0), (N["sat"] + 0.3, 0.62), (N["back0"] + 0.12, 0.62),
                         (N["back1"], -1.0), (N["near"], -1.0), (N["pass"], 0.62)], ease_in_out)
    look = (gaze[0] - off[0], gaze[1] - off[1])
    # ears: up in the bounds, flop on the landings; waiting (lower), perk at his steps, a hair up
    # when he tops the stair
    ears = 0.62
    for h in N["hops"]:
        if h["take"] - 0.05 <= t <= h["land"] + 0.4:
            ears = tween(t, [(h["take"] - 0.05, 0.62), (h["take"] + 0.1, 0.74), (h["land"] - 0.02, 0.88),
                             (h["land"] + 0.09, 0.52), (h["land"] + 0.4, 0.64)])
    if sat:
        ears = tween(t, [(N["sat"] + 0.4, 0.64), (N["back1"] + 0.2, 0.52), (N["perk"] - 0.02, 0.5),
                         (N["perk"] + 0.16, 0.72), (N["perk"] + 0.5, 0.62), (N["top"] - 0.3, 0.62),
                         (N["top"] + 0.1, 0.68)])
    # head: a little down while it looks down the stair, nose up to his face as he tops it
    tilt = tween(t, [(N["back0"], 0.0), (N["back1"], 0.03), (N["top"] - 0.6, 0.03), (N["top"], -0.05),
                     (N["pass"], 0.0)], ease_in_out) if sat else 0.0
    tail = 0.3 * _ramp(t, N["top"] - 0.2, N["top"] + 0.4)          # its tail tip curls: he came
    # blinks: its own natural blinks (the rig's, same seed as rev 3), a half-blink on the landing
    blink = core.blink_amount(tp, seed=23, rate=0.22)
    ld = N["sat"]
    if ld <= t <= ld + 0.3:
        blink = max(blink, tween(t, [(ld, 0.0), (ld + 0.06, 0.5), (ld + 0.12, 0.5), (ld + 0.28, 0.0)]))
    if not sat or N["back0"] - 0.05 <= t <= N["back1"] + 0.1:
        blink = 0.0 if not (ld <= t <= ld + 0.3) else blink
    # eyes open for the meeting (he tops the stair, they look at each other), then a soft slow
    # blink as he passes and it turns to follow him
    if N["top"] - 0.45 <= t <= N["near"] + 0.35:
        blink = 0.0
    b1 = N["pass"] + 0.1
    if b1 <= t <= b1 + 0.45:
        blink = max(blink, tween(t, [(b1, 0.0), (b1 + 0.15, 1.0), (b1 + 0.25, 1.0), (b1 + 0.45, 0.0)]))
    kw = dict(pose=p["pose"], pose_from=p["pose_from"], pose_mix=p["mix"], pose_t=p["pose_t"], glow=1.0,
              expr="hopeful", look=look, ears=ears, tilt=tilt, blink=blink, face=face, tail_curl=tail)
    if wb > 0.0:
        # settle into rev 3's state (same pose / place by now)
        kw["look"] = (lerp(look[0], R["look"][0], wb), lerp(look[1], R["look"][1], wb))
        for nm in ("ears", "tilt", "face", "tail_curl"):
            kw[nm] = lerp(kw[nm], R[nm], wb)
        kw.update(pose=R["pose"], pose_from=None, pose_mix=1.0, pose_t=R["pose_t"])
    return kw, p


def meet_tired_kw(t, T, N, V):
    """Tiredness in S1 -> (kw, ground y); from wstop + 0.45 it is rev 3's tired_kw exactly."""
    tp = t - N["d"]
    R = tired_kw(tp, T, V)
    if tp >= T["wstop"] + 0.45:
        return R, FEET
    kw = dict(R)
    wst = N["wstop"]
    if t < wst:
        x, ph = _walk_at(N, t)
    else:
        u = seg(t, wst, wst + 0.3)
        x = TIR_X - 0.15 * _V_WALK + _V_WALK * 0.3 * (u - 0.5 * u * u)    # decelerate into the stop
        ph = tp - T["w0"]
    y = _tired_ground(x)
    pose = state_at(t, [(-99, "walk"), (wst, "stand")], 0.3)
    turn = lerp(-WALK_TURN, -0.8, smoothstep(seg(t, wst - 0.05, wst + 0.45)))   # turns back to the pod
    # eyes: up the stair at it, down at it beside him (a tiny nod), ahead to the pod, then they
    # lead his turn back to it (rev 3's keys take over at wstop + 0.3)
    ce = _eyes_cur(-1.0)
    he = _eyes_tired(x, y)
    at_it = _aim(he, ce, 0.95)
    look = tween(t, [(N["enter"] - 0.3, (0.7, -0.25)), (N["climb0"] - 0.2, at_it), (N["near"] + 0.1, at_it),
                     (N["pass"], (0.85, 0.05)), (wst - 0.12, (0.85, 0.05)), (wst + 0.25, (-0.9, 0.05)),
                     (wst + 0.3, (-0.9, 0.05))], ease_in_out)
    if t < N["near"] + 0.1:
        look = _aim(he, ce, 0.95) if t >= N["climb0"] - 0.2 else look
    face = dict(R["face"])
    face["head_nod"] = face.get("head_nod", 0.0) + 0.06 * _pulse(t, N["top"] - 0.05, N["near"] + 0.45)
    kw.update(x=x, pose=pose, turn=turn, pose_t=ph, reach=None, look=look, face=face)
    if N["top"] - 0.45 <= t <= N["near"] + 0.35:
        kw["blink"] = 0.0                  # eyes open while he looks down at it (the meeting)
    return kw, y


def _meet_cam(t, T, N, V):
    """Holds the stair framing (slow push), then eases into rev 3's S2 camera at `join`
    (position and velocity matched, so the hand-over is invisible)."""
    c1, t0, t1 = N["c1"], N["cam0"], N["join"]
    if t < t0:
        u = seg(t, c1, t0)
        return tuple(lerp(a, b, u) for a, b in zip(B_CAM0, B_CAM1))
    d = N["d"]
    p1 = _s2_cam(t1 - d, T, V)
    e = 1e-3
    p1b = _s2_cam(t1 - d + e, T, V)
    v1 = [(b - a) / e for a, b in zip(p1, p1b)]
    v0 = [(b - a) / (t0 - c1) for a, b in zip(B_CAM0, B_CAM1)]
    D = t1 - t0
    s = clamp((t - t0) / D)
    h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
    h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return tuple(h00 * a + h10 * D * va + h01 * b + h11 * D * vb
                 for a, b, va, vb in zip(B_CAM1, p1, v0, v1))


def _sign_glyph_fix(ctx):
    """sets.catwalk's LEVEL B2 sign draws "SHAFT A  ▼" but the ui font has no U+25BC, so a tofu
    box shows. This shot frames the sign: paint the box over and draw the arrow."""
    core.rrect(ctx, 483.5, 1121, 22, 35, 3)
    core.fill(ctx, "#24434f")
    core.poly(ctx, [(486.5, 1131), (501.5, 1131), (494, 1145)])
    core.fill(ctx, "#2fd1c5")


def shot_meet(ctx, t, T, N, V):
    tp = t - N["d"]
    cam = _meet_cam(t, T, N, V)
    st = cw_state(tp, T)
    ckw, p = meet_cur_kw(t, T, N, V)
    tkw, ty = meet_tired_kw(t, T, N, V)
    tx = tkw.pop("x")
    with core.camera(ctx, *cam):
        sets.catwalk(ctx, tp, **st)
        _sign_glyph_fix(ctx)
        with sets.shaded(ctx, sets.catwalk, tp, layer="shade"):
            if p is None:
                draw_cur(ctx, tp, T, V)
            else:
                x, y = p["x"], p["y"]

                def _c():
                    return CR.draw_specimen(ctx, x, y, S, tp, **ckw)
                ctx.save()
                if p["rot"]:
                    ctx.translate(x, y - 120 * S)        # pitch about the body centre
                    ctx.rotate(p["rot"])
                    ctx.translate(-x, -(y - 120 * S))
                _scaled_about(ctx, x, y, p["sx"], p["sy"], _c)
                ctx.restore()
            H.draw_person(ctx, "tired", tx, ty, S, tp, **tkw)
        sets.catwalk(ctx, tp, layer="fg", parts=("stair",))


# ----------------------------------------------------------------------------
# render
# ----------------------------------------------------------------------------
def render(ctx, t, info):
    V = _view(info)
    T = TT(V)
    N = NT(info)
    if t < N["tr"]:
        _render_rev3(ctx, t, V)                  # the opening (peer, drop): untouched
    elif t < N["c1"]:
        shot_turn(ctx, t, T, N, V)
    elif t < N["join"]:
        shot_meet(ctx, t, T, N, V)
    else:
        _render_rev3(ctx, V.snap(t), V)          # rev 3 from 0.6 s after his stop, frame for frame


# ----------------------------------------------------------------------------
# sound
# ----------------------------------------------------------------------------
def _sfx_rev3(info):
    """rev 3's events on rev 3's clock, without the room tone (re-laid on the new clock) and the
    old walk-in (his steps along the pods, its ear twitch), which the new entrance replaces."""
    T = TT(info)
    ev = []
    # the opening: a soft longing coo with its paw on the glass; the ears lift with the
    # decision; the hop and the landing on the grating
    ev.append((T["p_paw1"] + 0.12, "creature_chirp_sad", -13, 0.2))
    ev.append((T["p_set0"] + 0.26, "ears_perk", -5, 0.2))
    ev.append((T["d_jump"] - 0.02, "whoosh", -17, 0.0))
    ev.append((T["d_land"] - 0.01, "body_thud", -9, -0.25))
    ev.append((T["wstop"] + 0.28, "footstep", -5, 0.22))     # feet come together
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


def SFX(info):
    V = _view(info)
    T = TT(V)
    N = NT(info)
    d = V.d
    ev = [(e[0] + d if e[0] > V.tr else e[0],) + tuple(e[1:]) for e in _sfx_rev3(V)]
    # shaft room tone (pods), not in the control room
    ev += sfx.loop_events("pod_hum", 0.0, T["c10"] + d + 0.1, -8)
    ev += sfx.loop_events("pod_hum", T["c13"] + d, T["casc"] + d + 1.2, -8)
    # S0c: the ears lift (decided), the little hop-turn, the trot off right
    ev.append((N["a_set"], "ears_perk", -7, -0.1))
    ev.append((N["a_jump"] - 0.02, "whoosh", -22, 0.0))
    ev.append((N["a_land"], "foot_tap", -9, 0.0))
    ev.append((N["a_go"] + 0.02, "scurry", -7, 0.15))
    # S1: it patters in, three bounds up the stair, the landing by its pod
    ev.append((N["c1"], "scurry", -9, -0.45))
    for i, h in enumerate(N["hops"]):
        ev.append((h["land"], "foot_tap", -8 if i < 2 else -5, lerp(-0.45, 0.25, i / 2)))
    ev.append((N["perk"], "ears_perk", -6, 0.25))
    # his steps: off screen along the landing (quieter), then up the stair and along the deck
    for (tt, x) in N["steps"]:
        if tt > N["wstop"] + 1e-6:
            continue
        g = lerp(-9, 0, smoothstep(seg(x, -300, 60))) + (1 if tt > N["wstop"] - 0.05 else 0)
        ev.append((tt, "footstep", g, clamp((x - 600) / 900, -0.6, 0.3)))
    return ev
