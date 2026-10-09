"""S5 - "Coda" (BIBLE section 4, S5).

Rae has fled. Quill stands alone, the holo-cards fading from his palm; he lowers his hand.
"...Was that a yes?" The door whooshes open, Rae leans in - red-eyed, sniffly, pointing -
"Send me all eight." - and is gone again. Quill's rare, tiny smile; his iris glow warms to amber.
"Sending." Eight little lights lift from his palm and stream to the door. Dissolve to the stars,
the title returns with "8 symphonies sent", fade to black.

render(canvas, t) is a pure function of absolute time t. Both performances run continuously through
every cut (cuts only choose a camera), so nothing pops. All times derive from named beats, line
starts/ends and the SFX placements in build/timeline.json.

Shot list (absolute times only for orientation):
  1 alone     quill_alone -> q13-0.3          MEDIUM-WIDE cut-in (x1.65 on S4's wide; pose + fan picked up exactly
                                              from S4's last frame): on the first piano note the cards swoop back
                                              into his palm (his eyes follow them), the light sinks into the palm,
                                              the hand lowers; slow push in on him
  2 cu_q13    -> rae_return_door              CLOSE-UP: "...Was that a yes?" tilt, one robotic blink, a
                                              short inconclusive "compute" flicker while he waits
  3 wide_in   rae_return_door -> r17-0.1      WIDE (door + Quill): whoosh, Rae leans in, points
  4 rae_med   -> sniff+0.36                   MEDIUM Rae in the doorway: "SEND me all EIGHT." (point at his face,
                                              two jabs on the stressed vowels) + sniff
  5 wide_out  -> rae_return_close+0.9         WIDE (same set-up): she pulls out, the door shuts on Quill
  6 cu_smile  -> q14 end                      CLOSE-UP: blink, compute, then the tiny smile + amber glow,
                                              "Sending." (palm starts up just out of frame)
  7 wide_send -> end                          WIDE pull-back: light gathers in his palm, eight lights stream to
                                              the door; end_card: dissolve to the starfield (the lights ride on
                                              top of the dissolve), title + "8 symphonies sent" (the check mark
                                              lands a beat later), fade to black over the last 1.5 s
"""
from __future__ import annotations

import math

import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Layer, Track, auto_blink, beat, breathe, clamp, ease_in_out, glow, line_end,
                       line_start, mouth, noise1, paint, remap, scene_span, smoothstep, timeline)
from anim.rig import ArmPose, Pose
from config import H, W

# =========================================================================== timing (all derived from names)
T0, T1 = scene_span("s5")


def _sfx(name):
    for s in timeline()["sfx"]:
        if s["name"] == name and T0 - 1e-6 <= s["start"] < T1:
            return s["start"]
    raise KeyError(name)


S, E = line_start, line_end
ALONE = beat("quill_alone")
DOOR_O = beat("rae_return_door")
DOOR_C = beat("rae_return_close")
SMILE = beat("quill_smile")
ENDC = beat("end_card")
END = beat("end")
SNIFF = _sfx("sniff")                 # sniff sfx: inhale peaks ~+0.25
CHIME = _sfx("send_chime")            # rises to its peak ~+0.5
DOOR_SHUT = DOOR_C + 0.67             # door_close sfx: panel slides, thunk at +0.67

# ---------------------------------------------------------------- cuts
CUT_CU1 = S("q13") - 0.3
CUT_WIDE_IN = DOOR_O                  # cut on the whoosh
CUT_RAE = S("r17") - 0.1
CUT_WIDE_OUT = SNIFF + 0.36           # cut on her pull-back (after the sniff reads in the medium)
CUT_CU2 = DOOR_C + 0.9
CUT_WIDE_SEND = E("q14") + 0.03
DISSOLVE = 1.4                        # end_card dissolve length

# ---------------------------------------------------------------- reference geometry
QUILL_X = 545.0
RAE_X = -215.0                        # pelvis in the corridor, behind the wall left of the doorway
QA, RA = Q.ARMS, R.ARMS
LIGHT = env.char_light(1.0)
TITLE_Y = 610.0
SUB_TEXT = "8 symphonies sent ✓"

_qh = Q.head_center(Pose(x=QUILL_X, facing=-1, turn=0.35))           # ~ (522, 454)


def _cam_on(head, zoom, sx, sy):
    """Camera that puts stage point `head` at screen fraction (sx, sy)."""
    return Camera(head[0] + (0.5 - sx) * W / zoom, head[1] + (0.5 - sy) * H / zoom, zoom)


# =========================================================================== small animation helpers
class ArmSeq:
    """Keyframed ArmPose sequence: [(t, ArmPose, ease), ...] (ease = how we arrive, like Track)."""

    def __init__(self, keys):
        self.keys = sorted([(k[0], k[1], k[2] if len(k) > 2 else "io") for k in keys], key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for i in range(1, len(ks)):
            if t < ks[i][0]:
                t0, a0, _ = ks[i - 1]
                t1, a1, e = ks[i]
                return ArmPose.blend(a0, a1, Track.EASES[e]((t - t0) / (t1 - t0)))
        return ks[-1][1]


def arm_add(a: ArmPose, ds=0.0, de=0.0, dw=0.0, hand=None) -> ArmPose:
    return ArmPose(a.shoulder + ds, a.elbow + de, a.wrist + dw, hand or a.hand, a.across, a.behind)


def gaze(keys, dur=0.11):
    """Saccade track. keys: [(t, (lx, ly)) or (t, (lx, ly), dur)] - eyes snap there over `dur`."""
    ks = []
    prev = keys[0][1]
    ks.append((keys[0][0] - 1.0, prev))
    for k in keys:
        t, v = k[0], k[1]
        d = k[2] if len(k) > 2 else dur
        ks.append((t, prev, "lin"))
        ks.append((t + d, v, "out" if d <= 0.2 else "io"))
        prev = v
    return Track(ks)


def blink_amt(t, times):
    """0..1 lid closure from (start, duration) blinks: fast close, slower open (organic, for Rae)."""
    best = 0.0
    for b0, d in times:
        x = (t - b0) / d
        if 0.0 <= x < 1.0:
            v = math.sin(min(1.0, x / 0.38) * math.pi / 2) if x < 0.38 else math.cos((x - 0.38) / 0.62 * math.pi / 2)
            best = max(best, v)
    return best


# =========================================================================== S4 -> S5 handoff
def _s4_end():
    """Quill's face/head and the card fan exactly as S4 leaves them at the boundary (read from S4 itself,
    so the handoff stays matched if S4 is re-timed); falls back to the values S4 hands over today."""
    d = dict(hturn=-0.144, nod=-0.046, tilt=-1.8, look=(-0.9, 0.08), brow=0.3, worry=0.155, glow=0.184,
             smile=0.0, card_alpha=0.85, hidden=(5, 6, 7))
    try:
        from anim.scenes import s4 as _s4
        q = _s4.quill_pose(T0)
        fs = _s4.fan_state(T0)
        d.update(hturn=q.head_turn, look=(q.look_x, q.look_y), brow=q.brow_raise, worry=q.brow_worry,
                 glow=q.glow, smile=q.smile, card_alpha=fs["alpha"], hidden=tuple(fs["hidden"]),
                 # S4 and S5 add the same idle noise (same seeds) on top of their tracks: strip it here
                 nod=q.head_nod - 0.012 * noise1(T0 * 0.3, 41), tilt=q.head_tilt - 0.35 * noise1(T0 * 0.25, 43))
    except Exception:                 # pragma: no cover - S4 mid-edit: keep S5 renderable
        pass
    return d


Q0 = _s4_end()

# =========================================================================== Quill
PRESENT = QA["present"]
REST = QA["rest"]
# wrist trails on the way down; the hand goes palm_up -> open -> relaxed in two soft steps (no single pop)
LOWER_MID = ArmPose(shoulder=12.0, elbow=40.0, wrist=10.0, hand="open")
LIFT_MID = ArmPose(shoulder=12.0, elbow=48.0, wrist=-14.0, hand="open")          # palm turning up on the way
OFFER = ArmPose(shoulder=30.0, elbow=60.0, wrist=-16.0, hand="palm_up")           # palm lifted a touch: "go"

GATHER0 = ALONE + 0.35                # first piano note: the fan folds back into his palm...
GATHER1 = ALONE + 1.07                # (the last card lands)
HAND_DOWN0 = ALONE + 1.12             # ...and only then does the hand come down
HAND_DOWN1 = ALONE + 2.02
LIFT0 = S("q14") + 0.2                # the palm starts to come up on "Sending." (enters the close-up's bottom edge)
LIFT1 = CHIME - 0.1                   # palm up just before the chime
SEND0 = CHIME + 0.05
SEND_DUR = 2.05                       # lights: launch over ~0.85 s, all arrive ~SEND0 + 2.0
LOWER2_0 = ENDC + 0.35
LOWER2_1 = ENDC + 1.45

q_arm_r = ArmSeq([
    (T0, PRESENT), (HAND_DOWN0, PRESENT),
    (HAND_DOWN0 + 0.46, LOWER_MID, "in"), (HAND_DOWN1, REST, "out"),
    (LIFT0, REST), (LIFT0 + 0.36, LIFT_MID, "in"), (LIFT1, PRESENT, "out"),
    (SEND0 + 0.25, PRESENT), (SEND0 + 0.75, OFFER, "io"),
    (LOWER2_0, OFFER), (LOWER2_0 + 0.5, LOWER_MID, "in"), (LOWER2_1, REST, "out"),
])

# Quill's blinks are robotic: perfectly periodic, both lids identical, on the same clock as S1/S4
# (auto_blink seed 0, every 4.6 s). In S5 that gives exactly one blink in the q13 close-up, a second
# after "...yes?" (then he computes), one just after the cut to the smile close-up, one in the dissolve.


def q_blink(t):
    return 1.0 - auto_blink(t, seed=0, rate=4.6, robotic=True)


Q_DOOR = (-0.62, 0.0)                 # gaze at the door (screen-left: he faces -1)
q_look = gaze([
    (T0, Q0["look"]),                              # still on the door she just went through (S4)
    (GATHER0 - 0.08, (-0.74, -0.1), 0.16),         # to the fan (up-left, at his eye level) on the first note
    (GATHER0 + 0.3, (-0.6, 0.06), 0.3),            # ...follows the cards as they fold in...
    (GATHER0 + 0.6, (-0.34, 0.4), 0.26),           # ...down into his palm
    (HAND_DOWN0 + 0.55, (-0.6, 0.02), 0.16),       # back to the door she left by (hand still settling)
    (CUT_CU1 + 0.22, (-0.16, 0.12), 0.14),         # inward: "...was that a yes?"
    (S("q13") + 0.62, (-0.26, 0.06)),
    (E("q13") + 0.75, (-0.52, 0.02)),              # a glance at the door...
    (E("q13") + 1.3, (-0.14, 0.18)),               # ...and back: computing
    (DOOR_O + 0.07, (-0.7, -0.02), 0.08),          # whoosh: eyes snap to the door
    (DOOR_O + 0.75, (-0.66, 0.0)),
    (DOOR_SHUT + 0.12, (-0.22, 0.2), 0.16),        # thunk: eyes drop, thinking
    (CUT_CU2 + 0.3, (-0.12, 0.26)),
    (SMILE - 0.16, (-0.42, -0.02), 0.2),           # look up toward the door; the smile follows
    (S("q14") + 0.1, (-0.34, 0.02)),
    (CHIME + 0.02, (-0.42, 0.34), 0.14),           # the palm as the lights lift
    (CHIME + 0.5, (-0.6, -0.16), 0.22),            # follow them toward the door
    (CHIME + 1.25, (-0.72, -0.04), 0.3),
], dur=0.09)

q_hturn = Track([
    (T0, Q0["hturn"]), (GATHER0 - 0.02, Q0["hturn"]), (GATHER0 + 0.45, 0.0, "io"), (GATHER1, -0.04, "io"),
    (HAND_DOWN0 + 0.58, -0.04), (HAND_DOWN0 + 1.0, 0.08, "io"),
    (CUT_CU1 + 0.3, 0.08), (S("q13") + 0.3, 0.02, "io"),
    (E("q13") + 0.8, 0.02), (E("q13") + 1.1, 0.06, "io"), (E("q13") + 1.6, 0.02, "io"),
    (DOOR_O + 0.12, 0.02), (DOOR_O + 0.42, 0.16, "out"), (DOOR_O + 0.75, 0.14, "io"),
    (DOOR_SHUT + 0.15, 0.14), (DOOR_SHUT + 0.7, 0.05, "io"),
    (SMILE - 0.12, 0.05), (SMILE + 0.4, 0.09, "io"),
    (CHIME + 0.5, 0.09), (CHIME + 1.3, 0.15, "io"),
])
q_nod = Track([
    (T0, Q0["nod"]), (GATHER0, Q0["nod"]), (GATHER0 + 0.3, -0.02, "io"), (GATHER1 + 0.05, -0.14, "io"),
    (HAND_DOWN0 + 0.55, -0.12), (HAND_DOWN0 + 0.95, 0.0, "io"),
    (S("q13"), 0.0), (S("q13") + 0.3, 0.03, "io"), (E("q13") + 0.3, 0.0, "io"),
    (DOOR_O + 0.1, 0.0), (DOOR_O + 0.3, 0.05, "out"), (DOOR_O + 0.7, 0.02, "io"),
    (E("r17") - 0.3, 0.02), (E("r17"), -0.04, "io"), (E("r17") + 0.35, 0.02, "io"),   # "all eight" registers
    (DOOR_SHUT + 0.1, 0.02), (DOOR_SHUT + 0.6, -0.07, "io"),
    (SMILE - 0.2, -0.07), (SMILE + 0.4, 0.0, "io"),
    (S("q14") + 0.04, 0.0), (S("q14") + 0.2, -0.07, "out"), (S("q14") + 0.55, 0.0, "io"),  # "Sending." nod
    (CHIME, 0.0), (CHIME + 0.18, -0.06, "io"), (CHIME + 0.75, 0.05, "io"),
])
q_tilt = Track([
    (T0, Q0["tilt"]), (GATHER0 + 0.05, Q0["tilt"]), (GATHER1 + 0.1, 1.5, "io"), (HAND_DOWN1, 0.0, "io"),
    (S("q13") + 0.15, 0.0), (S("q13") + 0.95, 9.0, "io"),                 # curious bird tilt on the question
    (E("q13") + 1.5, 9.0), (DOOR_O - 0.15, 4.0, "io"),
    (DOOR_O + 0.2, 4.0), (DOOR_O + 0.6, 1.5, "io"),
    (S("r17") + 0.5, 1.5), (E("r17") + 0.2, 5.0, "io"), (DOOR_SHUT + 0.6, 3.0, "io"),
    (SMILE, 3.0), (SMILE + 0.7, 5.0, "io"),
])
q_brow = Track([
    (T0, Q0["brow"]), (ALONE + 0.3, Q0["brow"]), (ALONE + 1.1, 0.04, "io"),
    (S("q13") + 0.45, 0.06), (S("q13") + 0.9, 0.3, "io"), (E("q13") + 0.6, 0.22, "io"),
    (E("q13") + 1.2, 0.1, "io"),
    (DOOR_O + 0.05, 0.1), (DOOR_O + 0.22, 0.32, "out"), (DOOR_O + 0.9, 0.2, "io"),
    (E("r17") - 0.35, 0.2), (E("r17") + 0.05, 0.36, "io"), (DOOR_SHUT + 0.5, 0.12, "io"),
    (SMILE, 0.08), (SMILE + 0.6, 0.16, "io"), (S("q14"), 0.16), (S("q14") + 0.3, 0.08, "io"),
])
q_worry = Track([(T0, Q0["worry"]), (ALONE + 0.6, 0.14, "io"), (HAND_DOWN1 + 0.4, 0.1), (S("q13") + 0.2, 0.0, "io")])
q_process = Track([
    (T0, 0.0), (E("q13") + 1.2, 0.0), (E("q13") + 1.45, 0.55, "io"), (E("q13") + 1.95, 0.5),     # inconclusive
    (E("q13") + 2.2, 0.0, "io"),
    (CUT_CU2 + 0.3, 0.0), (CUT_CU2 + 0.5, 0.6, "io"), (SMILE - 0.14, 0.55), (SMILE + 0.08, 0.0, "io"),  # resolved
])
q_glow = Track([
    (T0, Q0["glow"]), (ALONE + 1.2, 0.14, "io"),
    (E("q13") + 1.2, 0.14), (E("q13") + 1.45, 0.38, "io"), (E("q13") + 2.25, 0.14, "io"),
    (CUT_CU2 + 0.3, 0.14), (CUT_CU2 + 0.5, 0.42, "io"), (SMILE, 0.36),
    (SMILE + 0.9, 0.62, "io"), (CHIME, 0.62), (CHIME + 0.4, 0.7, "io"), (ENDC + 0.8, 0.6, "io"),
])
q_warm = Track([(SMILE - 0.05, 0.0), (SMILE + 1.0, 1.0, "io")])
q_smile = Track([(T0, Q0["smile"]), (ALONE + 0.5, 0.0), (SMILE - 0.05, 0.0), (SMILE + 0.75, 0.3, "io"), (S("q14"), 0.3),
                 (S("q14") + 0.3, 0.26, "io"), (E("q14") + 0.2, 0.3, "io")])
q_squint = Track([(SMILE, 0.0), (SMILE + 0.75, 0.12, "io")])
q_lid = Track([(T0, 1.0), (ALONE + 0.3, 1.0), (ALONE + 0.6, 0.93, "io"), (HAND_DOWN1, 0.93), (HAND_DOWN1 + 0.3, 1.0, "io"),
               (SMILE, 1.0), (SMILE + 0.75, 0.93, "io")])
q_mouth_k = Track([(T0, 0.9), (SMILE, 0.9), (SMILE + 0.5, 0.62, "io")])      # "Sending." spoken through the smile


def quill_pose(t: float) -> Pose:
    mo, mr = mouth("quill", t)
    lx, ly = q_look(t)
    # micro saccades so held gazes stay alive (tiny; he is precise)
    lx += 0.015 * noise1(t * 1.3, 51)
    ly += 0.012 * noise1(t * 1.1, 53)
    lid = q_lid(t) * (1.0 - q_blink(t))
    return Pose(
        x=QUILL_X, y=env.FLOOR_Y, facing=-1.0, turn=0.35,
        head_turn=q_hturn(t), head_nod=q_nod(t) + 0.012 * noise1(t * 0.3, 41),
        head_tilt=q_tilt(t) + 0.35 * noise1(t * 0.25, 43),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly,
        brow_raise=q_brow(t), brow_worry=q_worry(t),
        smile=q_smile(t), squint=q_squint(t),
        mouth_open=q_mouth_k(t) * mo, mouth_round=mr * (0.45 + 0.55 * (q_mouth_k(t) - 0.62) / 0.28),
        glow=q_glow(t), process=q_process(t),
        arm_r=q_arm_r(t), arm_l=REST, **LIGHT,
    )


# =========================================================================== Rae (in the doorway)
LEAN_IN0 = DOOR_O + 0.16              # she starts leaning in while the panel is still sliding
LEAN_IN1 = DOOR_O + 0.52
OUT0 = SNIFF + 0.29                   # she yanks herself back out just as the panel starts to slide
OUT1 = SNIFF + 0.6

# stressed syllables of "SEND me all EIGHT." (vowel onsets measured on build/vo/r17.wav: +0.14 / +0.64)
SEND_T = S("r17") + 0.13
EIGHT_T = S("r17") + 0.63

r_lean = Track([
    (T0, 0.0), (LEAN_IN0, 0.0), (LEAN_IN1, 31.0, "out"), (LEAN_IN1 + 0.22, 27.5, "io"), (CUT_RAE + 0.12, 28.4, "io"),
    (SEND_T - 0.1, 28.2, "io"), (SEND_T + 0.02, 31.2, "out"), (SEND_T + 0.3, 28.7, "io"),          # "SEND"
    (EIGHT_T - 0.12, 28.3, "io"), (EIGHT_T + 0.02, 31.6, "out"), (EIGHT_T + 0.32, 29.0, "io"),     # "EIGHT"
    (E("r17") + 0.1, 28.6, "io"), (SNIFF, 28.4, "io"), (SNIFF + 0.08, 29.2, "io"), (OUT0, 28.0, "io"),
    (OUT1, 0.0, "in"),
])
r_tilt = Track([
    (T0, 0.0), (LEAN_IN0, 0.0), (LEAN_IN0 + 0.2, 2.0, "io"), (LEAN_IN1 + 0.15, -15.0, "out"),   # head lags the lean
    (LEAN_IN1 + 0.4, -12.0, "io"), (SEND_T, -12.6, "io"), (SEND_T + 0.32, -10.6, "io"),
    (EIGHT_T, -9.6, "io"), (EIGHT_T + 0.4, -11.6, "io"), (SNIFF + 0.05, -10.4, "io"), (SNIFF + 0.18, -14.0, "io"),
    (OUT1, -4.0, "io"),
])
r_nod = Track([
    (T0, 0.0), (LEAN_IN1, 0.05), (S("r17") - 0.06, 0.06, "io"),
    (SEND_T + 0.03, -0.11, "out"), (SEND_T + 0.3, 0.03, "io"),                     # "SEND" (emphatic nod)
    (EIGHT_T - 0.08, 0.06, "io"), (EIGHT_T + 0.05, -0.15, "out"), (EIGHT_T + 0.38, 0.0, "io"),   # "...EIGHT."
    (E("r17") + 0.12, 0.02, "io"), (SNIFF + 0.03, 0.02), (SNIFF + 0.2, 0.2, "out"), (SNIFF + 0.4, 0.08, "io"),
])
r_shoulders = Track([(T0, 0.0), (SNIFF + 0.02, 0.0), (SNIFF + 0.18, 0.3, "out"), (SNIFF + 0.45, 0.05, "io")])

# The `point` preset is tuned for an upright body; leaning ~29 deg into the doorway it would aim at the floor.
# Raised + bent a touch more it points at Quill's chest/face (her upper arm still clear of her mouth).
POINT_S5 = ArmPose(shoulder=98.0, elbow=30.0, wrist=0.0, hand="point")
JAB = arm_add(POINT_S5, ds=8.0, de=-18.0)            # forearm snaps out straight at him
COCK = arm_add(POINT_S5, ds=-3.0, de=6.0)            # tiny draw-back before the second jab
DROOP = arm_add(POINT_S5, ds=-12.0, de=15.0)         # the point sags on the sniff
TUCK = ArmPose(shoulder=-30.0, elbow=30.0, wrist=0.0, hand="relaxed")            # hidden behind the jamb
r_arm_r = ArmSeq([
    (T0, TUCK), (LEAN_IN0 + 0.08, TUCK), (LEAN_IN1 - 0.02, arm_add(POINT_S5, 8.0, 10.0), "out"),
    (LEAN_IN1 + 0.2, POINT_S5, "io"),
    (SEND_T - 0.1, POINT_S5), (SEND_T, JAB, "out"), (SEND_T + 0.25, POINT_S5, "io"),              # jab
    (EIGHT_T - 0.1, COCK, "io"), (EIGHT_T, JAB, "out"), (EIGHT_T + 0.25, POINT_S5, "io"),        # jab
    (SNIFF + 0.04, arm_add(POINT_S5, -2.0, 3.0), "io"), (SNIFF + 0.24, DROOP, "io"),
    (OUT0 + 0.08, arm_add(POINT_S5, -26.0, 36.0), "io"), (OUT1, TUCK, "in"),
])
R_FAR = ArmPose(shoulder=-38.0, elbow=30.0, wrist=0.0, hand="hold")             # mug kept out of sight, behind her

# eyes open and locked on him as she appears (no blink in the wide); one blink just after the cut to her
# medium, gathering herself before the line; the sniff is the next "blink"
RAE_BLINKS = [(CUT_RAE + 0.03, 0.17)]
R_AT_Q = (0.6, -0.5)                                 # up at Quill's face (she is leaning low in the doorway)
r_look = gaze([
    (T0, R_AT_Q),
    (S("r17") + 0.42, (0.57, -0.46), 0.08),          # tiny saccade between his eyes
    (EIGHT_T - 0.12, (0.61, -0.52), 0.08),
    (SNIFF + 0.04, (0.3, 0.16), 0.12),               # sniff: eyes drop away, a little embarrassed
])
# lids: clear and determined on the stressed words (not drowsy), squeezed on the sniff
r_lid = Track([(T0, 0.9), (S("r17") - 0.05, 0.9), (SEND_T + 0.02, 0.96, "out"), (SEND_T + 0.35, 0.91, "io"),
               (EIGHT_T - 0.05, 0.92), (EIGHT_T + 0.04, 0.97, "out"), (E("r17") + 0.1, 0.9, "io"),
               (SNIFF + 0.03, 0.9), (SNIFF + 0.18, 0.5, "out"), (SNIFF + 0.42, 0.74, "io")])
r_squint = Track([(T0, 0.08), (SNIFF + 0.03, 0.08), (SNIFF + 0.18, 0.4, "out"), (SNIFF + 0.42, 0.2, "io")])
r_furrow = Track([(T0, 0.3), (S("r17") - 0.1, 0.32), (SEND_T + 0.03, 0.46, "out"), (SEND_T + 0.4, 0.38, "io"),
                  (EIGHT_T + 0.04, 0.48, "out"), (E("r17") + 0.15, 0.36, "io"), (SNIFF + 0.18, 0.22, "io")])
r_worry = Track([(T0, 0.34), (S("r17"), 0.3), (EIGHT_T, 0.24, "io"), (SNIFF + 0.15, 0.45, "io"), (OUT1, 0.4)])
r_brow_raise = Track([(T0, 0.12), (LEAN_IN1 + 0.3, 0.05, "io"), (EIGHT_T - 0.1, 0.05), (EIGHT_T + 0.1, 0.16, "io"),
                      (E("r17") + 0.2, 0.06, "io")])
r_mouth_x = Track([(T0, 0.1), (S("r17") - 0.05, 0.04, "io"), (E("r17"), 0.0), (SNIFF + 0.02, 0.0),
                   (SNIFF + 0.4, 0.06, "io")])


def rae_pose(t: float) -> Pose:
    lx, ly = r_look(t)
    lx += 0.03 * noise1(t * 1.7, 9)
    ly += 0.02 * noise1(t * 1.5, 13)
    lid = r_lid(t) * (1.0 - blink_amt(t, RAE_BLINKS))
    mo, mr = mouth("rae", t)
    p = Pose(
        x=RAE_X, y=env.FLOOR_Y, facing=1.0, turn=0.3, lean=r_lean(t),
        head_tilt=r_tilt(t) + 1.2 * noise1(t * 0.5, 5), head_nod=r_nod(t) + 0.03 * noise1(t * 0.45, 3),
        breath=breathe(t, 0.32, 2),
        lid_l=lid, lid_r=lid, look_x=lx, look_y=ly, squint=r_squint(t),
        brow_raise=r_brow_raise(t), brow_worry=r_worry(t), brow_furrow=r_furrow(t),
        mouth_open=r_mouth_x(t) + 0.8 * mo, mouth_round=mr, smile=0.04, mouth_tremble=0.18,
        tears=0.42, sniffle=0.8, pupil=1.08, shoulders_up=r_shoulders(t),
        arm_r=r_arm_r(t), arm_l=R_FAR, mug="l", **LIGHT,
    )
    return p


def rae_visible(t):
    return DOOR_O < t < OUT1 + 0.05


# =========================================================================== door
door = Track([(T0, 0.0), (DOOR_O, 0.0), (DOOR_O + 0.5, 1.0, "out"), (DOOR_C, 1.0), (DOOR_SHUT, 0.0, "in")])


def _door_clip_rect(d):
    """Stage rect of the (partly) open door panel still covering the doorway: Rae is behind it."""
    return skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(d), env.FLOOR_Y + 4)


# =========================================================================== holo cards (leftover from S4)
CARD_A0 = Q0["card_alpha"]            # S4 hands over with the fan up but already beginning to fade
CARD_DUR = 0.56                       # each card's flight back into the palm
CARD_STAGGER = 0.16                   # the farthest card (No. 1) leaves first, the nearest (No. 8) last
card_alpha = Track([(T0, CARD_A0), (GATHER0, CARD_A0), (GATHER0 + 0.3, CARD_A0 * 0.9, "io")])
palm_absorb = Track([(GATHER1 - 0.42, 0.0), (GATHER1 - 0.04, 1.0, "io"), (GATHER1 + 0.55, 0.0, "io")])
try:                                  # same fan geometry as S3/S4 (anim/scenes/s3.py FAN_GEOM) for the handoff
    from anim.scenes.s3 import FAN_GEOM
except Exception:                     # pragma: no cover - keep S5 renderable on its own
    FAN_GEOM = dict(radius=300.0, center=(-26.0, 20.0), angles=(-50.0, 8.0), card_scale=0.36)


def _card_fold(num, t):
    """0..1 flight of card `num` from its place in the fan into the palm."""
    k = (num - 1) / 7.0
    return ease_in_out(clamp((t - (GATHER0 + CARD_STAGGER * k)) / CARD_DUR))


def _cards_visible(t):
    return t < GATHER0 + CARD_STAGGER + CARD_DUR + 0.02


def _draw_cards(canvas, t, hx, hy, alpha):
    """The fan as S4 leaves it (same layout as s3.draw_fan; the theremin cards 5-7 already folded away),
    then each card swoops back down into his palm - shrinking, straightening and fading only as it lands."""
    for (num, x, y, rot, scl, vis) in fx.card_fan_layout(hx, hy, 1.0, **FAN_GEOM):
        if num in Q0["hidden"]:
            continue
        e = _card_fold(num, t)
        if e >= 0.999:
            continue
        cx = x + (hx - x) * e
        cy = y + (hy - 12.0 - y) * e - 30.0 * math.sin(math.pi * e) * (0.4 + 0.6 * (x < hx - 120))
        a = alpha * vis * (1.0 - smoothstep(remap(e, 0.62, 1.0)))
        fx.draw_holo_card(canvas, t, cx, cy, scl * (1.0 - 0.78 * e), num, fx.CARD_TITLES.get(num, ""),
                          fx.CARD_ICONS.get(num, "symphony"), 0.25 * math.sin(math.pi * e), a, rot=rot * (1.0 - e))


# =========================================================================== send lights
def send_progress(t):
    return clamp((t - SEND0) / SEND_DUR)


SEND_DST = (env.DOOR_CX + 6.0, 640.0)


# =========================================================================== cameras
# shot 1: a cut-in from S4's closing wide (zoom 0.86 -> 1.42) on the same eyeline height; the whole fan fits,
# Quill on the right third with the empty room to the left; as the fan folds away the camera eases in on him
MED_WIDE_A = _cam_on(_qh, 1.42, 0.79, 0.31)
MED_WIDE_B = _cam_on(_qh, 1.54, 0.66, 0.32)
CU1_A = _cam_on(_qh, 2.7, 0.5, 0.41)
CU1_B = _cam_on(_qh, 2.78, 0.5, 0.41)
WIDE_DOOR = Camera(196.0, 684.0, 0.8)
RAE_MED = Camera(-40.0, 711.0, 2.1)
CU2_A = _cam_on((_qh[0] + 6, _qh[1] + 6), 3.3, 0.52, 0.42)
CU2_B = _cam_on((_qh[0] + 6, _qh[1] + 6), 3.45, 0.52, 0.42)
SEND_A = Camera(276.0, 676.0, 0.8)
SEND_B = Camera(286.0, 640.0, 0.73)


def _drift(a: Camera, b: Camera, t, t0, t1, ease=smoothstep):
    return Camera.lerp(a, b, ease(clamp((t - t0) / (t1 - t0))))


def shot(t):
    if t < CUT_CU1:
        return "alone"
    if t < CUT_WIDE_IN:
        return "cu_q13"
    if t < CUT_RAE:
        return "wide_in"
    if t < CUT_WIDE_OUT:
        return "rae_med"
    if t < CUT_CU2:
        return "wide_out"
    if t < CUT_WIDE_SEND:
        return "cu_smile"
    return "wide_send"


def camera(t: float) -> Camera:
    s = shot(t)
    if s == "alone":
        return _drift(MED_WIDE_A, MED_WIDE_B, t, GATHER0 + 0.25, CUT_CU1 + 0.25)
    if s == "cu_q13":
        return _drift(CU1_A, CU1_B, t, CUT_CU1, CUT_WIDE_IN)
    if s == "wide_in":
        return WIDE_DOOR
    if s == "rae_med":
        return _drift(RAE_MED, Camera(RAE_MED.cx + 4, RAE_MED.cy - 2, RAE_MED.zoom * 1.02), t, CUT_RAE, CUT_WIDE_OUT)
    if s == "wide_out":
        return WIDE_DOOR
    if s == "cu_smile":
        return _drift(CU2_A, CU2_B, t, CUT_CU2, CUT_WIDE_SEND)
    return _drift(SEND_A, SEND_B, t, CUT_WIDE_SEND, ENDC + DISSOLVE + 0.6)


# =========================================================================== render
def _draw_stage(canvas, t, cam, qp, rp, d):
    canvas.save()
    cam.apply(canvas, t)
    env.draw_lounge(canvas, t, light=1.0, door=d)
    if rp is not None:
        canvas.save()
        canvas.clipRect(_door_clip_rect(d), skia.ClipOp.kDifference, True)
        R.draw(canvas, rp, t)
        canvas.restore()
    Q.draw(canvas, qp, t, warm=q_warm(t))
    env.draw_lounge_front(canvas, t, light=1.0, door=d)
    # the leftover fan, gathering back into his palm as it fades
    ca = card_alpha(t) if _cards_visible(t) else 0.0
    pa = palm_absorb(t)
    if ca > 0.003 or pa > 0.003:
        hx, hy = Q.hand_pos(qp, "r")
        if ca > 0.003:
            _draw_cards(canvas, t, hx, hy, ca)
        if pa > 0.003:                    # the light of the cards sinks into his palm
            glow(canvas, hx, hy - 10, 46, "#7FFFE9", 0.3 * pa)
            glow(canvas, hx, hy - 8, 14, "#E6FFFB", 0.45 * pa)
    canvas.restore()


palm_glow = Track([(LIFT1 - 0.1, 0.0), (SEND0 + 0.12, 1.0, "io"), (SEND0 + 0.75, 0.55, "io"), (SEND0 + 1.3, 0.0, "io")])


def _draw_send(canvas, t, cam, qp):
    pr = send_progress(t)
    pg = palm_glow(t)
    if (pr <= 0.0 or pr >= 1.0) and pg <= 0.003:
        return
    canvas.save()
    cam.apply(canvas, t)
    src = Q.hand_pos(qp.copy(arm_r=PRESENT), "r")     # launched from the open palm (held there while they leave)
    if pg > 0.003:                                     # warm light gathers in his palm as the lights form
        hx, hy = Q.hand_pos(qp, "r")
        glow(canvas, hx, hy - 8, 64, "#FFC37A", 0.4 * pg)
        glow(canvas, hx, hy - 8, 20, "#FFF1D6", 0.65 * pg)
    if 0.0 < pr < 1.0:
        fx.draw_send_lights(canvas, t, pr, src, SEND_DST, n=8, color="#FFC37A", size=1.6)
    canvas.restore()


def _end_card(canvas, t):
    """Screen-space starfield + title (under the dissolving stage)."""
    env.draw_space(canvas, t, drift=0.55, brightness=1.0)


def render(canvas, t):
    cam = camera(t)
    qp = quill_pose(t)
    rp = rae_pose(t) if rae_visible(t) else None
    d = door(t)
    diss = smoothstep(remap(t, ENDC, ENDC + DISSOLVE))
    if diss <= 0.0:
        _draw_stage(canvas, t, cam, qp, rp, d)
    else:
        _end_card(canvas, t)
        if diss < 0.999:
            with Layer(canvas, alpha=1.0 - diss):
                _draw_stage(canvas, t, cam, qp, rp, d)
    # the eight lights ride on top of the dissolve: they are still arriving as the stars come up
    _draw_send(canvas, t, cam, qp)
    canvas.resetMatrix()
    # title + the little line (its check mark lands a beat later: "delivered"), then fade to black
    ta = smoothstep(remap(t, TITLE_IN0, TITLE_IN1))
    sa = smoothstep(remap(t, SUB_IN0, SUB_IN1))
    if ta > 0.003:
        _title(canvas, t, ta, sa)
    fb = smoothstep(remap(t, END - 1.5, END))
    if fb > 0.003:
        canvas.drawRect(skia.Rect(0, 0, W, H), paint("#000000", fb, aa=False))


# =========================================================================== end-card title
TITLE_SIZE, SUB_SIZE = 44.0, 20.0
# the title comes back as the coda's last chord lands (~ENDC+0.9), the line follows, the check mark lands a
# beat after the words - leaving ~2 s of the finished card before the fade to black
TITLE_IN0, TITLE_IN1 = ENDC + 0.7, ENDC + 2.2
SUB_IN0, SUB_IN1 = ENDC + 2.3, ENDC + 3.2
CHECK_T = ENDC + 3.5
check_a = Track([(CHECK_T, 0.0), (CHECK_T + 0.18, 1.0, "out")])
_CHECK = None


def _check_box():
    """Screen rect + centre of the trailing check mark, using fx.draw_title's sub-line layout."""
    global _CHECK
    if _CHECK is None:
        from anim.core import font
        f = font(SUB_SIZE, "Inter Display", 300)
        tr = SUB_SIZE * 0.12
        ws = [f.measureText(ch) for ch in SUB_TEXT]
        total = sum(ws) + tr * (len(SUB_TEXT) - 1)
        x0 = W / 2 - total / 2 + sum(ws[:-1]) + tr * (len(SUB_TEXT) - 1)
        base = TITLE_Y + TITLE_SIZE * 0.95 + SUB_SIZE * 0.4
        rect = skia.Rect(x0 - 3.0, base - SUB_SIZE * 1.15, x0 + ws[-1] + 7.0, base + 7.0)
        _CHECK = (rect, (x0 + ws[-1] * 0.5, base - SUB_SIZE * 0.35))
    return _CHECK


def _title(canvas, t, ta, sa):
    rect, (cx, cy) = _check_box()
    ca = check_a(t)

    def draw(sub_alpha):
        fx.draw_title(canvas, t, "IF YOU HAVE TIME", TITLE_Y, alpha=ta, size=TITLE_SIZE, sub=SUB_TEXT,
                      sub_alpha=sub_alpha, rise=8, sub_size=SUB_SIZE)

    canvas.save()
    canvas.clipRect(rect, skia.ClipOp.kDifference, True)
    draw(sa)
    canvas.restore()
    if ca > 0.003:
        canvas.save()
        canvas.clipRect(rect, skia.ClipOp.kIntersect, True)
        draw(sa * ca)
        canvas.restore()
        pulse = math.exp(-(t - CHECK_T) / 0.35) * min(1.0, (t - CHECK_T) / 0.08)
        if pulse > 0.01:
            glow(canvas, cx, cy, 30.0, "#7FFFE9", 0.45 * pulse)
