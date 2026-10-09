"""Character rig contract shared by anim/char_quill.py, anim/char_rae.py and the scenes.

Scenes build a Pose and call   char_X.draw(canvas, pose, t)
with the camera transform already applied to the canvas (stage coordinates).

Each character module MUST export:
    draw(canvas, pose: Pose, t: float) -> None
    head_center(pose) -> (x, y)        stage coords of the face center (between the eyes)
    hand_pos(pose, side: str) -> (x, y) stage coords of the palm, side in {"l", "r"}
    ARMS: dict[str, ArmPose]           named arm presets (see per-character lists in BIBLE.md)
    HEIGHT: float                      standing height in stage units at scale 1

Conventions
    * pose.x, pose.y is the point on the floor between the feet (stage units).
      When sitting, y is still the floor; the seat height comes from pose.seat_y.
    * "l"/"r" mean the CHARACTER's left/right. With facing=+1 the character is turned
      toward screen-right; facing=-1 toward screen-left (mirror).
    * turn: 0 = full front, 0.5 = clear three-quarter toward `facing`. Values up to ~0.7.
    * Any field left as None is animated automatically (blink, breath).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from anim.core import lerp


@dataclass
class ArmPose:
    """Angles in degrees. shoulder: 0 = hanging straight down, +90 = raised forward/outward
    to horizontal, 180 = straight up. elbow: 0 = straight, + = bends the forearm up/inward.
    wrist: small tilt. hand: one of "relaxed", "open", "fist", "point", "hold", "palm_up", "palm_out".
    across: 0..1 how much the arm crosses in front of the torso (for hand-on-chest, sip, etc.)."""
    shoulder: float = 8.0
    elbow: float = 10.0
    wrist: float = 0.0
    hand: str = "relaxed"
    across: float = 0.0
    behind: float = 0.0     # 0..1 arm goes behind the torso (hands behind back)

    @staticmethod
    def blend(a: "ArmPose", b: "ArmPose", t: float) -> "ArmPose":
        return ArmPose(lerp(a.shoulder, b.shoulder, t), lerp(a.elbow, b.elbow, t), lerp(a.wrist, b.wrist, t),
                       b.hand if t >= 0.5 else a.hand, lerp(a.across, b.across, t), lerp(a.behind, b.behind, t))


@dataclass
class Pose:
    # ---- placement
    x: float = 360.0
    y: float = 1150.0           # floor contact
    scale: float = 1.0
    facing: float = 1.0         # +1 screen-right, -1 screen-left
    turn: float = 0.3           # 0 front .. 0.7 strong three-quarter
    back: float = 0.0           # >0.5 draw from behind (Quill looking out the window)
    lean: float = 0.0           # body lean, degrees (+ = toward facing direction)
    head_tilt: float = 0.0      # degrees, + = tilt toward facing direction
    head_nod: float = 0.0       # -1 chin down .. +1 chin up
    head_turn: float = 0.0      # extra head-only turn added on top of `turn` (-0.5..0.5)
    breath: float | None = None
    # ---- eyes
    lid_l: float | None = None  # 1 open, 0 closed; None = auto blink
    lid_r: float | None = None
    look_x: float = 0.0         # gaze -1..1 (+ = toward screen-right)
    look_y: float = 0.0         # gaze -1 up .. +1 down
    pupil: float = 1.0          # dilation multiplier (awe ~1.3)
    squint: float = 0.0         # lower lids up (smile / crying squeeze)
    eye_wide: float = 0.0       # 0..1 upper lids retract (shock)
    brow_raise: float = 0.0     # -1 lowered .. +1 raised
    brow_worry: float = 0.0     # 0..1 inner ends up (sad / moved)
    brow_furrow: float = 0.0    # 0..1 inner ends down & together (confused / annoyed)
    # ---- mouth
    mouth_open: float = 0.0     # 0..1 (lip-sync adds here)
    mouth_round: float = 0.0    # 0 wide .. 1 round
    smile: float = 0.0          # -1 frown .. +1 smile
    smirk: float = 0.0          # -1..1 one-sided smile
    mouth_tremble: float = 0.0  # 0..1 lip quiver (animated from t)
    # ---- emotion extras
    tears: float = 0.0          # 0..1 welling (glossy lower lid, bigger highlights)
    tear_l: float = 0.0         # 0..1 progress of a tear rolling down the left cheek (0 = none)
    tear_r: float = 0.0
    eye_shine: float = 0.0      # 0..1 extra sparkle in the eyes (awe)
    blush: float = 0.0
    # ---- body
    arm_l: ArmPose = field(default_factory=ArmPose)
    arm_r: ArmPose = field(default_factory=ArmPose)
    sit: float = 0.0            # 0 standing .. 1 seated (seat at seat_y)
    seat_y: float = 960.0
    kneel: float = 0.0          # 0 .. 1 kneeling on the floor
    walk: float | None = None   # walk-cycle phase in cycles (None = not walking)
    shoulders_up: float = 0.0   # 0..1 shrug / tension
    bounce: float = 0.0         # vertical body offset in stage units (laughs, sobs, head-bob)
    foot_tap: float = 0.0       # 0..1 amount of tapping foot (animated from t)
    # ---- props
    mug: str | None = None      # "r" / "l" = held in that hand, None = not held
    # ---- lighting
    light: float = 1.0          # overall brightness multiplier
    tint: tuple = (20, 30, 70)  # color the character is pushed toward in low light
    tint_amt: float = 0.0
    rim: float = 0.0            # 0..1 rim light glow around the silhouette
    rim_color: str = "#7FFFE9"
    # ---- android only (Quill)
    glow: float = 0.0           # iris glow 0..1
    process: float = 0.0        # 0..1 "computing" animation in the irises
    # ---- human only (Rae)
    sniffle: float = 0.0        # 0..1 red nose / puffy eyes after crying

    def copy(self, **kw) -> "Pose":
        return replace(self, **kw)
