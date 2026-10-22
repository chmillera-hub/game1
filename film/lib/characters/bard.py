"""bard.py -- THE BARD (speaker BARD): the plump, twinkly COCKATRICE MINSTREL who frames the film.

A rooster with a dragon's small leathery wings and a scaly green dragon tail (a nod to Alan-a-Dale
and a mythic cousin of our hero): a golden-chestnut head with a floppy red comb and wattles, a
cream face mask, bright clever green eyes, a short horn-yellow beak that opens to sing, a ruff of
hackle feathers over a patched burgundy-and-gold doublet stretched over a round belly, scaly
yellow hands with little claws, feathered drumstick thighs and chicken feet in soft leather boots
(claw tips poking out), a felt beret with a long white plume, and a well-loved LUTE (pear-shaped
ribbed bowl, carved rose, bent-back pegbox, a red ribbon) strummed with one of his own quills.

    from film.lib import characters as ch
    pose = ch.BardPose(sit=1, facing=1, turn=-0.45, look_cam=0.5, **ch.bard_song(t))   # the prologue
    ch.draw_bard_stool(cr, x, ground_y, sc, light, yaw=ch.bard_yaw(pose))  # his little stool (seat 28)
    rig = ch.draw_bard(cr, x, ground_y, sc, pose, light, t)   # rig.mouth, rig.lute["rose"], ...

bard_song(t) reads film/assets/song/song_timing.json and returns EVERY music-driven pose field at
song time t (strokes, chords, beat/groove, tuning, singing with vowels and long-note rapture);
staging (where he looks, the wink, the cap tip) stays with the scene. Without the song file, build
the same fields from bard_beat / bard_strum / bard_chords / bard_sing.

Scale 1.0, standing: ground -> top of his plume = BARD_HEIGHT = 178 px (the beret on, as drawn;
the comb top is ~156, the eyes ~124, the beak ~109): the gnome's height plus his comb and plume,
about a third of the dragon. Seated on his own little stool (BARD_STOOL_H = 28) his boots are
planted and his eyes are ~113 px above the ground (plume ~153); on the standard bench (125) his
boots dangle (eyes ~209). Anchor (x, y) = the ground point below his pelvis (pose.anchor="seat":
the seat point). 3D-lite like the dragon: joints in body space (X = his left, Y down, Z forward)
projected with the body yaw, so he (and the lute) turn continuously. Best seated angle: 3/4
(facing=1, turn=-0.45): the thighs, the stool and the draped tail all read.
"""

import bisect
import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path as _FsPath

from .. import core, fx
from ..core import clamp, lerp, smooth
from . import base as B
from .base import (Mat, Path, Proj, m_mul, m_rot_x, m_rot_y, m_rot_z, m_vec, v_add, v_cross, v_dot,
                   v_lerp, v_mul, v_norm, v_sub)

TAU = math.tau

__all__ = ["BardPose", "BardArm", "BardRig", "draw_bard", "draw_bard_stool", "bard_beat", "bard_strum",
           "bard_chord", "bard_chords", "bard_sing", "bard_song", "bard_song_timing", "bard_cameo_pose",
           "bard_twinkle", "bard_stride", "bard_walk_phase", "bard_yaw", "BARD_HEIGHT", "BARD_STOOL_H", "BARD_LINE",
           "BARD_COLORS", "BARD_MOODS", "BARD_CHORDS", "BARD_CHORD_NAMES", "BARD_LIGHTS", "BARD_GESTURES",
           "bard_mats"]

# ----------------------------------------------------------------------------------------
# design constants (body space px at scale 1.0)
# ----------------------------------------------------------------------------------------
BARD_HEIGHT = 178.0                 # ground -> plume top, standing (comb top ~156, eyes ~124)
BARD_STOOL_H = 28.0                 # his own little three-legged stool: boots planted, knees up
BARD_LINE = B.LINE                  # 2.2, the house weight

PELVIS_Y = -44.0
HIP_W = 10.5
THIGH, SHIN, ANKLE_H = 19.0, 18.0, 9.0
SHOULDER_W = 24.0
UPPER_ARM, FOREARM, HAND_LEN = 26.0, 24.0, 20.0
STRIDE = 50.0                       # body-space distance per walk cycle (two strutting steps)
ELEV = 0.12
SEAT_DY = 5.0
SIT_SWAP = 0.5
HEAD_CHEAT = 0.22                   # the head turns (1 - this) x the body yaw: the face stays readable
HR = (21.0, 22.0, 21.0)             # skull radii (head space)

# the lute (lute space: u along the strings from the tail end toward the neck, v across the
# soundboard toward the treble side, w out of the soundboard)
LUTE_LB, LUTE_R, LUTE_D = 54.0, 19.5, 15.5      # body length, half width, bowl depth
LUTE_LN, LUTE_LP = 37.0, 17.0                    # neck, pegbox
LUTE_WIDE = 0.40                                 # widest point (fraction of the body)
LUTE_NECK_W = 4.8
LUTE_ROSE, LUTE_ROSE_R = 0.63, 7.2
LUTE_BRIDGE = 0.15
LUTE_ANGLE = 30.0                                # neck rise above horizontal (deg)
LUTE_O = (-25.0, -3.0, 30.0)                     # tail end, pelvis-relative (before the body tilt)
LUTE_STRINGS = 7
LUTE_SCALE = LUTE_LB * (1.0 - LUTE_BRIDGE) + LUTE_LN
PEGBOX_BEND = math.radians(72.0)

STRUM_SWEEP = 0.075                 # s for the hand to cross the strings
STRUM_SPAN = 14.0                   # half-span of the stroke across the strings (lute units)
STRUM_U = 0.36                      # where he strums (fraction of the body, between rose and bridge)

# chord shapes: (hand position along the neck from the nut, 0..1 of the neck; extra finger curl)
BARD_CHORDS = [(0.42, 0.00), (0.30, 0.12), (0.56, -0.06), (0.36, 0.18), (0.66, 0.06), (0.24, 0.10), (0.48, 0.14)]
# the song's chord names (film/assets/song/song_timing.json) -> BARD_CHORDS shapes
BARD_CHORD_NAMES = {"D": 0, "G": 1, "A": 2, "C": 3, "Bm": 4, "A7": 5, "Em": 6}

BARD_COLORS = {
    "head": "#B9692F",       # golden-chestnut head
    "hackle": "#CC8A3C",     # the golden hackle ruff
    "plumage": "#93502E",    # chestnut body plumage (thighs, tail tuft)
    "plumage_dk": "#6A3620",
    "cream": "#F0DCB0",      # breast, cuffs, plume tuft
    "face": "#E8BC78",       # the lighter golden face round the eyes and cheeks
    "brow": "#6B3A22",
    "comb": "#D9443A",       # the floppy comb + wattles
    "beak": "#ECBA4C",       # horn-yellow beak
    "scaly": "#E3A548",      # scaly hands and shanks
    "claw": "#7A5636",
    "eye": "#3FA266",        # bright clever green (the cockatrice's fabled gaze -- harmless here)
    "eye_hi": "#A9EBA4",
    "dragon": "#4E8350",     # scaly green tail + wing bones: a cousin of the hero's teal
    "dragon_dk": "#33603A",
    "membrane": "#8DB475",
    "tail_belly": "#CBC88A",
    "doublet": "#7C2334",    # burgundy: HIS signature accent (with the gold and the red comb)
    "gold": "#D9AA45",       # slashes, trim, buttons
    "patch": "#C08E3E",      # ochre patch
    "patch2": "#3F6470",     # slate-teal patch
    "belt": "#4D3222",
    "pouch": "#7A5236",
    "beret": "#2F5B4B",      # deep green felt
    "plume": "#F3EEE3",
    "jewel": "#C4303C",
    "boot": "#5E3B2B",
    "boot_cuff": "#48291D",
    "mouth": "#6E2430",
    "tongue": "#D46C74",
    # the lute
    "top": "#E4C27F", "bowl": "#8C4C27", "bowl2": "#B0703C", "neck": "#5A3420", "board": "#2F2019",
    "rose": "#22150E", "bridge": "#3A2418", "string": "#F6E9C6", "fret": "#C9B48A", "nut": "#EFE3C6",
    "peg": "#4A2C1C", "ribbon": "#C13A2E", "quill": "#E9D9B4",
}

# the prologue's candlelight (the same values as storybook.STORY_LIGHT; base.LIGHTS has no candle)
BARD_LIGHTS = {
    "candle": B.Light(key=(1.16, 0.88, 0.60), ambient=(0.42, 0.32, 0.42), rim=(1.0, 0.70, 0.40),
                      rim_strength=0.7, direction=(0.65, -0.76), rim_direction=(-0.8, -0.6),
                      name="candle"),
}

BARD_MOODS = {
    "twinkle": B.Expr(brow_in=0.15, brow_out=0.32, brow_y=0.22, lid=0.2, lid_bot=0.32, lid_tilt=0.04,
                      smile=0.55, cheek=0.45),
    "sing": B.Expr(brow_in=0.55, brow_out=0.3, brow_y=0.5, lid=0.12, lid_bot=0.14, smile=0.35, cheek=0.25),
    "rapture": B.Expr(brow_in=0.75, brow_out=0.15, brow_y=0.55, lid=1.0, lid_bot=0.3, lid_tilt=0.1,
                      smile=0.4, cheek=0.4),
    "listen": B.Expr(brow_in=0.4, brow_out=-0.1, brow_y=0.08, brow_asym=0.5, lid=0.6, lid_bot=0.2, smile=0.12),
    "sly": B.Expr(brow_in=-0.25, brow_out=0.35, brow_asym=0.6, lid=0.34, lid_bot=0.32, smile=0.65, cheek=0.55),
}

_MATS = {}


def bard_mats():
    """Materials used by the bard (also handy for props that should match him)."""
    if not _MATS:
        C = BARD_COLORS
        _MATS.update({
            "head": Mat.of(C["head"], line_k=0.5),
            "hackle": Mat.of(C["hackle"], line_k=0.5, shadow_k=0.95),
            "plumage": Mat.of(C["plumage"], line_k=0.55),
            "plumage_dk": Mat.of(C["plumage_dk"]),
            "cream": Mat.of(C["cream"], shadow_k=0.95, line_k=0.5, sss=0.15),
            "face": Mat.of(C["face"], line_k=0.5, sss=0.2),
            "brow": Mat.of(C["brow"]),
            "comb": Mat.of(C["comb"], sss=0.45, line_k=0.5),
            "beak": Mat.of(C["beak"], sheen=0.5, line_k=0.5),
            "scaly": Mat.of(C["scaly"], sss=0.2, line_k=0.5),
            "claw": Mat.of(C["claw"], sheen=0.4),
            "dragon": Mat.of(C["dragon"], sss=0.15),
            "dragon_dk": Mat.of(C["dragon_dk"]),
            "membrane": Mat.of(C["membrane"], sss=0.6),
            "tail_belly": Mat.of(C["tail_belly"], sss=0.4),
            "doublet": Mat.of(C["doublet"], shadow_k=1.1, line_k=0.6),
            "gold": Mat.of(C["gold"], sheen=0.6, line_k=0.5),
            "patch": Mat.of(C["patch"], shadow_k=1.05),
            "patch2": Mat.of(C["patch2"], shadow_k=1.05),
            "belt": Mat.of(C["belt"], sheen=0.3),
            "pouch": Mat.of(C["pouch"], sheen=0.2),
            "beret": Mat.of(C["beret"], shadow_k=1.1),
            "plume": Mat.of(C["plume"], shadow_k=0.9, line_k=0.62),
            "jewel": Mat.of(C["jewel"], sheen=0.9),
            "boot": Mat.of(C["boot"], sheen=0.25),
            "boot_cuff": Mat.of(C["boot_cuff"]),
            "mouth": Mat.of(C["mouth"]),
            "tongue": Mat.of(C["tongue"], sss=0.5),
            "top": Mat.of(C["top"], sheen=0.3, line_k=0.5),
            "bowl": Mat.of(C["bowl"], sheen=0.5),
            "bowl2": Mat.of(C["bowl2"], sheen=0.5),
            "neck": Mat.of(C["neck"], sheen=0.3),
            "board": Mat.of(C["board"], sheen=0.3),
            "peg": Mat.of(C["peg"], sheen=0.4),
            "ribbon": Mat.of(C["ribbon"], sss=0.2),
            "quill": Mat.of(C["quill"], line_k=0.6),
        })
    return _MATS


# ----------------------------------------------------------------------------------------
# pose
# ----------------------------------------------------------------------------------------

@dataclass
class BardArm:
    """One arm's gesture (names: BARD_GESTURES). His RIGHT arm strums, his LEFT arm frets.

    gesture  "play" (right: strum, left: fret -- only with lute="play"), "rest", "present" (an open
             palm flourish toward the story), "wave", "tip_cap", "point", or explicitly "strum"/"fret"
    amt      0..1 blend from `prev` into `gesture` (hands travel on an arc)
    hold     hold(cr, frame) callback: a prop in the hand (z-correct, see base.hand)
    hand     hand pose override; target: explicit wrist target in body space; phase: gesture 0..1
    """
    gesture: str = "play"
    amt: float = 1.0
    prev: str = "play"
    hold: object = None
    hand: str = None
    target: tuple = None
    phase: float = 0.0


@dataclass
class BardPose:
    """Everything that poses the bard. All fields are optional.

    facing, turn  +1 3/4 right / -1 3/4 left / 0 front, plus extra yaw (x0.6 rad); default front,
              turned a little toward screen-right (yaw 0.33): his face and the lute's both read
    sit, seat_h   0 standing .. 1 seated; seat height (default his stool, 28; the bench is 125)
    walk, phase   strut cycle (bard_walk_phase) with the rooster head-thrust
    lean, head_turn, head_tilt, head_nod, look   as on the dragon
    look_cam  0..1: the head (and eyes) turn to look straight into the camera
    mood      BARD_MOODS / base.MOODS name or Expr (default "twinkle"); mood2 + mood_mix
    sing      0..1 beak opening from the vocal envelope (bard_sing); vowel "a"/"o"/"e"/"m" or None
    rapture   0..1 long-note bliss: eyes close, brows lift, head tips up (bard_sing computes it)
    talk      spoken lines (same as sing); smile -1..1 override; wink 0..1 (near eye); blink None=auto
    lute      "play" (in his lap / against the belly), "back" (slung on his back) or "none"
    right/left  BardArm (default "play": the strum hand and the fret hand)
    strum_t, strum_next, strum_dir, strum_next_dir, strum_amt   from bard_strum(t, strums): time
              since the last stroke / to the next one, their directions (+1 down / -1 up), size
    chord     float chord index (BARD_CHORDS; fractional = sliding between adjacent shapes; bard_chord);
              chord_to + chord_mix 0..1: sliding from `chord` to any other shape (bard_chords)
    tune      0..1 the tuning gesture (fret hand at the pegbox turning a peg, head cocked,
              listening); tune_phase = the peg-turning phase
    beat, groove  continuous beat count (bard_beat) and 0..1 how much he bobs, sways and taps
    tap       foot-tap amount (x groove); wings -1 drooped .. +1 lifted; tail_curl, tail_swing
    cap       wear the beret; cap_lift 0..1 lifts it (tip_cap)
    anchor    "ground" or "seat"; elev camera elevation; shadow draw the contact shadow; seed
    """
    facing: int = 0
    turn: float = 0.55
    sit: float = 0.0
    seat_h: float = BARD_STOOL_H
    walk: float = 0.0
    phase: float = 0.0
    lean: float = 0.0
    head_turn: float = 0.0
    head_tilt: float = 0.0
    head_nod: float = 0.0
    look: tuple = (0.0, 0.0)
    look_cam: float = 0.0
    mood: object = "twinkle"
    mood2: object = None
    mood_mix: float = 0.0
    talk: float = 0.0
    sing: float = 0.0
    vowel: str = None
    rapture: float = 0.0
    smile: float = None
    wink: float = 0.0
    blink: float = None
    lute: str = "play"
    right: BardArm = field(default_factory=BardArm)
    left: BardArm = field(default_factory=BardArm)
    strum_t: float = None
    strum_next: float = None
    strum_dir: int = 1
    strum_next_dir: int = -1
    strum_amt: float = 1.0
    chord: float = 0.0
    chord_to: float = None
    chord_mix: float = 0.0
    tune: float = 0.0
    tune_phase: float = 0.0
    beat: float = None
    groove: float = 0.0
    tap: float = 1.0
    wings: float = 0.0
    tail_curl: float = 0.5
    tail_swing: float = 0.0
    cap: bool = True
    cap_lift: float = 0.0
    anchor: str = "ground"
    elev: float = ELEV
    shadow: bool = True
    seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


@dataclass
class BardRig:
    """Attach points returned by draw_bard, all in the CALLER's coordinates."""
    hand_near: B.HandFrame = None
    hand_far: B.HandFrame = None
    hand_right: B.HandFrame = None     # his strumming hand
    hand_left: B.HandFrame = None      # his fretting hand
    head: tuple = (0.0, 0.0)
    mouth: tuple = (0.0, 0.0)          # between the mandibles (song breath, sparkles)
    beak: tuple = (0.0, 0.0)           # beak tip
    eyes: list = field(default_factory=list)
    top: tuple = (0.0, 0.0)            # top of the beret (or the comb without it)
    comb: tuple = (0.0, 0.0)
    plume_tip: tuple = (0.0, 0.0)
    chest: tuple = (0.0, 0.0)
    lap: tuple = (0.0, 0.0)
    feet: list = field(default_factory=list)
    seat: tuple = (0.0, 0.0)
    lute: dict = field(default_factory=dict)   # rose, bridge, nut, pegbox, center, strum
    scale: float = 1.0
    facing: float = 1.0
    yaw: float = 0.0


def _yaw_of(facing, turn):
    base = {1: 1.0, -1: -1.0, 0: 0.0}.get(int(facing), 0.0)
    return clamp(base + turn * 0.6, -1.45, 1.45)


def bard_yaw(pose):
    """The body yaw (rad) a BardPose is drawn at: pass it to draw_bard_stool(yaw=...) so the stool
    turns with him."""
    return _yaw_of(pose.facing, pose.turn)


def bard_stride(scale=1.0, facing=1, turn=0.0):
    """Screen px the anchor travels per strut cycle (feet don't slide)."""
    return STRIDE * abs(math.sin(_yaw_of(facing, turn))) * scale


def bard_walk_phase(distance_px, scale=1.0, facing=1, turn=0.0):
    st = bard_stride(scale, facing, turn)
    return (distance_px / st) % 1.0 if st > 1e-6 else 0.0


# ----------------------------------------------------------------------------------------
# music helpers: beat grid / strums / chords / vocal envelope -> pose fields
# ----------------------------------------------------------------------------------------

def bard_beat(t, beats):
    """Continuous beat count (k + phase, phase 0 = on beat k) from a sorted list of beat times;
    extrapolates before the first and after the last beat. None if there are no beats."""
    if not beats:
        return None
    n = len(beats)
    if n == 1:
        return (t - beats[0]) / 0.5
    k = bisect.bisect_right(beats, t) - 1
    if k < 0:
        return (t - beats[0]) / max(1e-6, beats[1] - beats[0])
    if k >= n - 1:
        return (n - 1) + (t - beats[-1]) / max(1e-6, beats[-1] - beats[-2])
    return k + (t - beats[k]) / max(1e-6, beats[k + 1] - beats[k])


def bard_strum(t, strums, amt=1.0):
    """Strum-hand pose fields from the song's strum times: a sorted list of times (alternating
    down/up strokes) or of (time, dir) pairs (dir +1 down, -1 up). Splat into BardPose(**...)."""
    if not strums:
        return {"strum_t": None, "strum_next": None, "strum_amt": amt}
    times, dirs = [], []
    for i, s in enumerate(strums):
        if isinstance(s, (tuple, list)):
            times.append(float(s[0]))
            dirs.append(1 if s[1] >= 0 else -1)
        else:
            times.append(float(s))
            dirs.append(1 if i % 2 == 0 else -1)
    k = bisect.bisect_right(times, t) - 1
    since = t - times[k] if k >= 0 else None
    until = times[k + 1] - t if k + 1 < len(times) else None
    d_last = dirs[k] if k >= 0 else -dirs[0]
    d_next = dirs[k + 1] if k + 1 < len(times) else -d_last
    return {"strum_t": since, "strum_next": until, "strum_dir": d_last, "strum_next_dir": d_next,
            "strum_amt": amt}


def bard_chord(t, changes, slide=0.16):
    """Float chord value from [(time, chord_index)]: the fret hand slides to each new shape in
    the `slide` seconds BEFORE the change lands (like a real player)."""
    if not changes:
        return 0.0
    times = [c[0] for c in changes]
    k = bisect.bisect_right(times, t) - 1
    cur = changes[k][1] if k >= 0 else changes[0][1]
    if k + 1 < len(changes):
        tn, cn = changes[k + 1]
        u = clamp((t - (tn - slide)) / max(1e-6, slide))
        return lerp(cur, cn, core.inout_sine(u))
    return float(cur)


def bard_chords(t, changes, slide=0.16):
    """Like bard_chord, but as pose fields {"chord", "chord_to", "chord_mix"}: the fret hand
    slides straight to ANY next shape (bard_chord's float only blends adjacent shapes)."""
    if not changes:
        return {"chord": 0.0, "chord_to": None, "chord_mix": 0.0}
    times = [c[0] for c in changes]
    k = bisect.bisect_right(times, t) - 1
    cur = changes[k][1] if k >= 0 else changes[0][1]
    if k + 1 < len(changes):
        tn, cn = changes[k + 1]
        u = clamp((t - (tn - slide)) / max(1e-6, slide))
        if u > 0.0:
            return {"chord": float(cur), "chord_to": float(cn), "chord_mix": core.inout_sine(u)}
    return {"chord": float(cur), "chord_to": None, "chord_mix": 0.0}


def bard_sing(t, env, thr=0.2, hold=0.45, fps=48.0):
    """sing + rapture from a vocal envelope callable env(t) -> 0..1 (e.g. lambda tt:
    timeline.talk(0, tt, "BARD")). Rapture grows when a note has been held longer than `hold`
    seconds: his eyes close and his brows lift on the long notes."""
    s = clamp(env(t))
    k = 0
    while k < 72 and env(t - k / fps) > thr:
        k += 1
    held = k / fps
    rap = smooth((held - hold) / 0.6) * smooth(s / 0.35)
    return {"sing": clamp(s * 1.1), "rapture": rap}


# ---- the song: film/assets/song/song_timing.json (film/audio/song.py) drives everything at once

_SONG_FILE = _FsPath(__file__).resolve().parents[2] / "assets" / "song" / "song_timing.json"
_SONG = {}
_PIECES = {}
# stroke kind -> (direction: +1 down, -1 up, 0 alternate with the previous stroke; size)
_STROKES = {"down": (1, 1.0), "up": (-1, 0.85), "roll": (1, 0.95), "flourish": (1, 1.0), "final": (1, 1.0),
            "bass": (1, 0.55), "pluck": (0, 0.42), "run": (0, 0.32), "tune": (1, 0.3), "harmonic": (1, 0.25)}
_GROOVE = {"intro": 0.35, "v1": 1.0, "v2": 1.0, "coda": 0.8, "outro": 0.45}


def bard_song_timing(path=None):
    """The song's timing (film/assets/song/song_timing.json, cached); None if it isn't there."""
    key = str(path or _SONG_FILE)
    if key not in _SONG:
        try:
            with open(key) as fh:
                _SONG[key] = json.load(fh)
        except (OSError, ValueError):
            _SONG[key] = None
    return _SONG[key]


def _song_piece(timing, piece):
    key = (id(timing), piece)
    if key in _PIECES:
        return _PIECES[key]
    P = timing[piece]
    st = sorted(P.get("strokes") or [{"t": x, "kind": "down" if i % 2 == 0 else "up"}
                                     for i, x in enumerate(P.get("strums", []))], key=lambda s: s["t"])
    times, dirs, amts, tunes = [], [], [], []
    last = -1
    for s in st:
        rule, size = _STROKES.get(s.get("kind"), (0, 0.5))
        d = rule if rule != 0 else -last
        last = d
        times.append(float(s["t"]))
        dirs.append(d)
        amts.append(clamp(size * (0.6 + 0.65 * float(s.get("vel", 0.6)))))
        if s.get("kind") in ("tune", "harmonic"):
            tunes.append(float(s["t"]))
    tune_end = None
    if tunes:
        later = [x for x, s in zip(times, st) if x > tunes[-1] and s.get("kind") not in ("tune", "harmonic")]
        tune_end = later[0] if later else tunes[-1] + 0.8
    names = BARD_CHORD_NAMES
    chords = [(float(c["t"]), float(names.get(c.get("chord"), sum(map(ord, str(c.get("chord")))) % len(BARD_CHORDS))))
              for c in P.get("chords", [])]
    lines = sorted(P.get("lines", []), key=lambda ln: ln["start"])
    secs = sorted(((v[0], v[1], k) for k, v in (P.get("sections") or {}).items()))
    out = {"times": times, "dirs": dirs, "amts": amts, "tunes": tunes, "tune_end": tune_end, "chords": chords,
           "beats": [float(b) for b in P.get("beats", [])], "lines": lines, "starts": [ln["start"] for ln in lines],
           "sections": secs}
    _PIECES[key] = out
    return out


def _vowel(syl, prog):
    w = "".join(ch for ch in syl.lower() if ch.isalpha())
    if not w:
        return "a"
    if prog > 0.72 and w[-1] in "mnbp":
        return "m"
    for pat, v in (("ee", "e"), ("ea", "e"), ("ey", "e"), ("oo", "o"), ("ou", "o"), ("ow", "o"), ("oa", "o"),
                   ("igh", "a"), ("ai", "e"), ("ay", "e")):
        if pat in w:
            return v
    vs = [i for i, ch in enumerate(w) if ch in "aeiouy"]
    if not vs:
        return "m" if prog > 0.5 else "a"
    i = vs[0]
    ch = w[i]
    if ch in "io" and len(w) >= i + 3 and w[-1] == "e" and w[i + 1] not in "aeiou":
        return "a" if ch == "i" else "o"          # time, rhyme / stone, alone
    if ch == "y" and i == len(w) - 1:
        return "a"                                 # by, my
    return {"a": "a", "o": "o", "u": "a", "e": "e", "i": "e", "y": "e"}[ch]


def bard_song(t, piece="prologue", timing=None, offset=0.0):
    """EVERY music-driven BardPose field at song time t - offset (seconds from the start of the
    piece: "prologue" or "reprise"), from film/assets/song/song_timing.json: the strum hand on
    every stroke (down/up strums, the quill picking bass + plucks, runs, rolls, the flourish and the
    final chord; sizes from the velocities), the fret hand sliding to each chord, the tuning gesture
    over the intro's tuning strokes, beat + groove (bob, sway, foot tap) and the singing (beak from
    the 24 fps line envelopes, vowel shapes from the syllables, eyes closing on long notes).
    Splat it: BardPose(sit=1, facing=1, turn=-0.45, **bard_song(t)). {} if there is no timing."""
    timing = timing if timing is not None else bard_song_timing()
    if not timing or piece not in timing:
        return {}
    S = _song_piece(timing, piece)
    tt = t - offset
    out = {}
    # strokes
    times, n = S["times"], len(S["times"])
    if n:
        k = bisect.bisect_right(times, tt) - 1
        since = tt - times[k] if k >= 0 else None
        until = times[k + 1] - tt if k + 1 < n else None
        d_last = S["dirs"][k] if k >= 0 else -S["dirs"][0]
        d_next = S["dirs"][k + 1] if k + 1 < n else -d_last
        a_last = S["amts"][k] if k >= 0 else S["amts"][0]
        a_next = S["amts"][k + 1] if k + 1 < n else a_last
        w = 1.0 - smooth(clamp(until / 0.18)) if until is not None else 0.0
        out.update(strum_t=since, strum_next=until, strum_dir=d_last, strum_next_dir=d_next,
                   strum_amt=lerp(a_last, a_next, w))
    # chords, beat, groove
    out.update(bard_chords(tt, S["chords"]))
    if S["beats"]:
        out["beat"] = bard_beat(tt, S["beats"])
    g = 0.0
    for a, b, name in S["sections"]:
        if a <= tt < b:
            g = _GROOVE.get(name, 0.8)
    out["groove"] = g
    # the tuning gesture over the intro's tuning strokes
    tune = 0.0
    if S["tunes"]:
        t0, t1 = S["tunes"][0], S["tune_end"]
        tune = smooth((tt - (t0 - 0.45)) / 0.4) * (1.0 - smooth((tt - (t1 - 0.32)) / 0.3))
    out["tune"] = tune
    out["tune_phase"] = tt * 0.9
    # singing
    sing, rap, vowel = 0.0, 0.0, None
    j = bisect.bisect_right(S["starts"], tt + 0.08) - 1
    if j >= 0:
        ln = S["lines"][j]
        if tt <= ln["end"] + 0.2:
            env = ln.get("env") or []
            x = (tt - ln["start"]) * 24.0
            if env and 0.0 <= x < len(env):
                i0 = int(x)
                f = x - i0
                e0 = env[i0]
                e1 = env[i0 + 1] if i0 + 1 < len(env) else 0.0
                sing = clamp(lerp(e0, e1, f) * 1.05)
            for sy in ln.get("syllables", []):
                if sy["start"] - 0.03 <= tt < sy["end"]:
                    dur = max(1e-3, sy["end"] - sy["start"])
                    prog = clamp((tt - sy["start"]) / dur)
                    vowel = _vowel(sy.get("s", ""), prog)
                    held = tt - sy["start"]
                    rap = (smooth((held - 0.28) / 0.35) * smooth((dur - 0.42) / 0.2)
                           * (1.0 - smooth((tt - (sy["end"] - 0.1)) / 0.1)) * smooth(sing / 0.3))
                    break
    out.update(sing=sing, rapture=rap, vowel=vowel)
    return out


def bard_cameo_pose(t, facing=-1, turn=0.35, period=1.4, seed=0, **kw):
    """S8: seated on the standard bench among the crowd, quietly strumming (silent -- the score
    carries the music), eyes half closed, swaying. Extra kw override BardPose fields."""
    beat = t / period
    since = t % period
    k = int(beat)
    chords = (0, 2, 3, 1)
    cur = chords[(k // 4) % 4]
    nxt = chords[((k + 1) // 4) % 4]
    u = clamp((since - (period - 0.2)) / 0.2) if (k + 1) % 4 == 0 else 0.0
    p = dict(facing=facing, turn=turn, sit=1.0, seat_h=B.BENCH_SEAT_H, mood="twinkle", beat=beat,
             groove=0.45, tap=0.0, strum_t=since, strum_next=period - since, strum_dir=1,
             strum_next_dir=1, strum_amt=0.5, chord=lerp(cur, nxt, core.inout_sine(u)),
             rapture=0.25 + 0.2 * math.sin(t * 0.37 + seed), seed=seed)
    p.update(kw)
    return BardPose(**p)


def bard_twinkle(cr, t, t0, rig, scale=None, dur=0.55, color="#fff6d8"):
    """The wink's 'ting!': a little four-point sparkle by his winking eye from t0."""
    if t < t0 or t > t0 + dur or not rig.eyes:
        return
    s = rig.scale if scale is None else scale
    u = (t - t0) / dur
    a = math.sin(math.pi * u)
    ex, ey = rig.eyes[-1]
    fx.sparkle(cr, ex + 14.0 * s * rig.facing, ey - 14.0 * s, 9.0 * s * (0.6 + 0.4 * a), color, 0.95 * a,
               angle=0.6 * u)


# ----------------------------------------------------------------------------------------
# small geometry helpers
# ----------------------------------------------------------------------------------------

def _area(pts):
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


def _pos(pts):
    """Wind a polygon like convex hulls and arcs, so unions never cancel into holes."""
    return pts if _area(pts) >= 0.0 else pts[::-1]


def _circ(c, r, n=10, sy=1.0):
    return [(c[0] + math.cos(TAU * i / n) * r, c[1] + math.sin(TAU * i / n) * r * sy) for i in range(n)]


def _tube_pts(pts, radii, samples=4, tension=0.8):
    return _pos(B.tube_outline(pts, radii, samples, tension, (0.0,))[0])


def _ring(proj, c, a, cz, n=14, dy=0.0):
    return [proj.xy((c[0] + math.sin(TAU * i / n) * a, c[1] + dy, c[2] + math.cos(TAU * i / n) * cz)) for i in range(n)]


class _Q:
    """Per-draw context."""
    __slots__ = ("cr", "proj", "light", "lw", "detail", "micro", "t", "pose", "yaw", "sit", "M", "S", "pal",
                 "F", "st", "vib")

    def P(self, mat):
        p = self.pal.get(mat)
        if p is None:
            p = self.pal[mat] = B.palette(self.light, mat)
        return p

    def shade(self, path, mat, lw=None, **kw):
        kw.setdefault("bounce", 0.0)
        return B.shade(self.cr, path, mat, self.light, self.lw if lw is None else lw, **kw)


def _union(q, polys, mat, size, lw=None, circles=(), tension=0.85, **kw):
    """Closed point lists (+ (center, r) circles) -> ONE silhouette: the dilated pieces filled once
    in the line colour, then the union shaded once. Returns the union Path."""
    cr = q.cr
    lw = q.lw if lw is None else lw
    polys = [_pos(p) for p in polys if len(p) >= 3]
    cr.new_path()
    for p in polys:
        core.smooth_closed(cr, B.offset_closed(p, lw), tension)
    for (c, r) in circles:
        core.circle(cr, c[0], c[1], r + lw)
    core.src(cr, q.P(mat).line)
    cr.fill()
    for p in polys:
        core.smooth_closed(cr, p, tension)
    for (c, r) in circles:
        core.circle(cr, c[0], c[1], r)
    path = Path(cr)
    q.shade(path, mat, lw=lw, outline=False, size=size, **kw)
    return path


def _flat(q, pts, mat, lw=None, tone=0.0, tension=0.85):
    """Small parts: outline + one lit fill (tone > 0 mixes toward the shadow)."""
    cr = q.cr
    lw = q.lw if lw is None else lw
    p = q.P(mat)
    pts = _pos(pts)
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(pts, lw), tension)
    core.src(cr, p.line)
    cr.fill()
    core.smooth_closed(cr, pts, tension)
    path = Path(cr)
    path.add(cr)
    core.src(cr, core.mix(p.lit, p.shadow, tone) if tone else p.lit)
    cr.fill()
    return path, p


def _ribbon(q, pts, w0, w1, mat, lw=None, size=None, rim=0.5, cap=True, flat=False):
    """A tapered ribbon (trim, belt, plume, ribbon tails) with a dilated outline."""
    cr = q.cr
    lw = q.lw if lw is None else lw
    if len(pts) < 2:
        return None
    sh, so = B.taper_paths(cr, pts, w0, w1, lw, cap=cap)
    if flat:
        p = q.P(mat)
        so.add(cr)
        core.src(cr, p.line)
        cr.fill()
        sh.add(cr)
        core.src(cr, p.lit)
        cr.fill()
        return sh
    q.shade(sh, mat, lw=lw, outline=so, size=size or max(w0, w1), rim=rim)
    return sh


# ----------------------------------------------------------------------------------------
# skeleton (body space)
# ----------------------------------------------------------------------------------------

def _tap_curve(ph):
    """Foot-tap toe lift over one beat: down on the beat, rising through the second half,
    slapping down again on the next beat (plus a tiny rebound)."""
    if ph < 0.12:
        return 0.06 * math.sin(math.pi * ph / 0.12)
    if ph < 0.45:
        return 0.0
    if ph < 0.88:
        return 0.42 * smooth((ph - 0.45) / 0.43)
    return 0.42 * (1.0 - core.in_quad((ph - 0.88) / 0.12))


def _skeleton(pose, t, sit, seat_h, yaw):
    S = {}
    br = B.breathing(t, 0.3, pose.seed)                 # small and round: a quicker breath
    k = smooth(sit)
    walk = clamp(pose.walk) * (1.0 - k)
    wc = B.walk_cycle(pose.phase, stride=STRIDE, lift=7.0, bob=2.2, swing=1.0)
    groove = clamp(pose.groove) if pose.beat is not None else 0.0
    beat = pose.beat if pose.beat is not None else 0.0
    ph = beat % 1.0
    dip = groove * (0.5 + 0.5 * math.cos(TAU * ph)) ** 3          # 1 right on the beat
    dip_lag = groove * (0.5 + 0.5 * math.cos(TAU * (ph - 0.13))) ** 3
    sway_bar = groove * math.sin(math.pi * beat)                   # one swing per two beats
    S.update(br=br, walk=walk, wc=wc, sit_k=k, groove=groove, ph=ph, dip=dip, dip_lag=dip_lag,
             sway_bar=sway_bar, beat=beat)

    arc = math.sin(math.pi * clamp(sit))
    stand_pel = (walk * wc.hip_sway * 2.4, PELVIS_Y + walk * (wc.hip_dy + 1.0) + 1.6 * dip, 0.0)
    sit_pel = (0.0, -seat_h - SEAT_DY + 0.8 * dip, -4.0)
    pel = v_add(v_lerp(stand_pel, sit_pel, k), (0.0, -10.0 * arc, -5.0 * arc))
    S["pelvis"] = pel
    idle = B.sway(t, 0.23, pose.seed + 4)
    rap = clamp(pose.rapture)
    tilt = (0.30 * pose.lean + 0.05 * k - 0.07 * walk + 0.02 * idle + 0.012 * br + 0.035 * dip - 0.05 * rap)
    roll = walk * wc.hip_sway * 0.07 + 0.04 * sway_bar + 0.018 * B.sway(t, 0.17, pose.seed + 9)
    R = m_mul(m_rot_z(roll), m_rot_x(-tilt))
    S["R"], S["tilt"] = R, tilt

    def T(v):
        return v_add(pel, m_vec(R, v))

    S["T"] = T
    S["chest"] = T((0.0, -38.0, 8.0 + 0.6 * br))
    S["belly"] = T((0.0, -24.0, 10.0 + 0.8 * br))
    sh_y = -48.0 - 0.8 * br
    S["shoulders"] = {s: T((s * SHOULDER_W, sh_y, -2.0)) for s in (-1.0, 1.0)}
    S["neck"] = T((0.0, -55.0, 2.0))

    # head: bob on the beat, tip up into the long notes, cock toward the pegbox when tuning
    talk = clamp(max(pose.talk, pose.sing))
    tune = clamp(pose.tune)
    wink = clamp(pose.wink)
    nod = (pose.head_nod * 0.38 - 0.11 * dip + 0.15 * rap + 0.015 * br + 0.03 * talk * math.sin(t * 6.1)
           + 0.02 * B.sway(t, 0.27, pose.seed + 2) - 0.4 * tilt - 0.14 * tune)
    hy = clamp(pose.head_turn, -1.2, 1.2) * 0.95 - HEAD_CHEAT * yaw + 0.3 * tune
    hy = lerp(hy, -yaw, clamp(pose.look_cam))
    hr = (pose.head_tilt + 0.06 * sway_bar + 0.02 * B.sway(t, 0.19, pose.seed + 6) - 0.22 * tune
          + 0.12 * wink)
    RH = m_mul(m_rot_y(hy), m_mul(m_rot_x(nod), m_rot_z(hr)))
    S["RH"], S["head_yaw"], S["head_roll"] = RH, hy, hr
    saw = (pose.phase * 2.0) % 1.0
    thrust = (smooth(saw / 0.35) if saw < 0.35 else 1.0 - smooth((saw - 0.35) / 0.65)) * 2.0 - 1.0
    S["head_c"] = v_add(S["neck"], v_add(m_vec(RH, (0.0, -24.0, 4.0)),
                                         (0.0, walk * wc.head_bob * 0.6, walk * thrust * 4.0)))

    # legs: standing strut <-> seated (boots planted in front of a low stool, dangling from a high one)
    feet = []
    u_feet = smooth((sit - 0.45) / 0.55)
    tap = _tap_curve(ph) * groove * clamp(pose.tap)
    for s in (-1.0, 1.0):
        hip = v_add(pel, m_vec(R, (s * HIP_W, 5.0, 0.0)))
        fz, lift, toe, _pl = wc.feet[0 if s < 0 else 1]
        stand_ank = (s * (HIP_W + 1.5) + stand_pel[0] * 0.3, -ANKLE_H - lift * walk, fz * walk + 1.0)
        hip_s = v_add(sit_pel, (s * HIP_W, 5.0, 0.0))
        plant = (s * (HIP_W + 6.0), -ANKLE_H, 13.0 + 0.1 * seat_h)
        reach = B.v_len(v_sub(plant, hip_s))
        f_plant = clamp(((THIGH + SHIN) * 0.985 - reach) / 4.0 + 0.5)
        sw = (0.18 + 0.08 * math.sin(t * 1.1 + s * 1.3 + pose.seed)
              + 0.22 * groove * math.sin(math.pi * beat + (0.0 if s < 0 else math.pi)))
        knee_s = v_add(hip_s, (s * 3.0, -1.0, THIGH * 0.95))
        dangle = v_add(knee_s, (0.0, SHIN * math.cos(sw), SHIN * math.sin(sw)))
        seat_ank = v_lerp(dangle, plant, f_plant)
        ankle = v_lerp(stand_ank, seat_ank, u_feet)
        knee, ank = B.ik3(hip, ankle, THIGH, SHIN, (s * lerp(0.25, 0.45, k), lerp(0.05, -0.7, k), 1.0))
        pitch = lerp(toe * walk, lerp(-0.3 + 0.3 * (sw - 0.18), 0.0, f_plant), u_feet)
        if s < 0:
            pitch += tap * lerp(1.0, f_plant, u_feet)
        feet.append({"hip": hip, "knee": knee, "ankle": ank, "pitch": pitch, "side": s})
    S["feet"] = feet
    S["knee"] = {-1.0: feet[0]["knee"], 1.0: feet[1]["knee"]}
    return S


# ----------------------------------------------------------------------------------------
# the strum: stroke dynamics (anticipation, sweep through the strings, follow-through, recovery)
# ----------------------------------------------------------------------------------------

def _strum_pos(s, u, d, dn):
    """Hand position across the strings (-1 bass side .. +1 treble side) and lift (0 on the
    strings .. 1 clear of them) `s` seconds after a stroke in direction d (+1 down, -1 up),
    with the next stroke (direction dn) `u` seconds away (None: unknown)."""
    if s < STRUM_SWEEP:
        k = core.out_cubic(clamp(s / STRUM_SWEEP))
        return lerp(-d, d, k), 0.0
    se = s - STRUM_SWEEP
    gap = (u + se) if u is not None else 0.9
    n0 = -dn                                     # where the next stroke starts
    follow = d * (1.0 + 0.34 * math.sin(math.pi * clamp(se / 0.2)))
    rec = core.inout_sine(clamp((se - 0.08) / max(0.1, gap - 0.2)))
    pos = lerp(follow, n0 * 0.8, rec)
    cross = 1.0 if d == dn else 0.0              # same direction again: travel back over the strings
    lift = cross * math.sin(math.pi * rec) + 0.25 * math.sin(math.pi * rec)
    if u is not None:
        wu = 1.0 - smooth(clamp(u / 0.13))       # anticipation: wind up just before the stroke
        pos = lerp(pos, n0 * 1.1, wu)
        lift *= 1.0 - wu
    return pos, lift


def _strum_state(pose):
    s, u = pose.strum_t, pose.strum_next
    d = 1 if (pose.strum_dir or 1) >= 0 else -1
    dn = 1 if (pose.strum_next_dir if pose.strum_next_dir is not None else -d) >= 0 else -1
    if s is None or s < 0.0:
        if u is None:
            return {"pos": -0.3, "lift": 1.0, "twist": 0.0, "act": 0.0, "env": 0.0, "rock": 0.0}
        wu = 1.0 - smooth(clamp(u / 0.13))
        act = 1.0 - smooth((u - 0.35) / 0.5)
        pos = lerp(-dn * 0.8, -dn * 1.1, wu)
        return {"pos": lerp(-0.3, pos, act), "lift": lerp(1.0, 0.2, act), "twist": 0.0, "act": act,
                "env": 0.0, "rock": 0.0}
    pos, lift = _strum_pos(s, u, d, dn)
    p2, _ = _strum_pos(max(0.0, s - 0.03), (u + 0.03) if u is not None else None, d, dn)
    vel = (pos - p2) / 0.03
    twist = clamp(-vel * 0.045, -1.0, 1.0)
    env = smooth(clamp(s / 0.035)) * math.exp(-s / 0.32)
    a_after = 1.0 - smooth((s - 1.2) / 0.8)
    a_before = (1.0 - smooth((u - 0.35) / 0.5)) if u is not None else 0.0
    act = max(a_after, a_before)
    return {"pos": lerp(-0.3, pos, act), "lift": lerp(1.0, lift, act), "twist": twist * act, "act": act,
            "env": env, "rock": env * d}


# ----------------------------------------------------------------------------------------
# the lute: frame, geometry, drawing
# ----------------------------------------------------------------------------------------

def _lute_frame(q):
    S, pose = q.S, q.pose
    T, R = S["T"], S["R"]
    if pose.lute == "back":
        # slung across his back: bowl outward, neck up past his right shoulder
        u = v_norm((-0.4, -0.9, -0.06))
        w0 = (0.15, 0.0, -1.0)
        O = (16.0, 6.0, -27.0)
    else:
        a = math.radians(LUTE_ANGLE) + 0.035 * q.st["rock"] - 0.02 * S["dip"]
        u = v_norm((math.cos(a), -math.sin(a), -0.12))
        w0 = (-0.30, -0.24, 1.0)
        O = LUTE_O
    w = v_norm(v_sub(w0, v_mul(u, v_dot(w0, u))))
    v = v_cross(w, u)
    return {"O": T(O), "u": m_vec(R, u), "v": m_vec(R, v), "w": m_vec(R, w)}


def _L(F, a, b, c):
    O, u, v, w = F["O"], F["u"], F["v"], F["w"]
    return (O[0] + u[0] * a + v[0] * b + w[0] * c, O[1] + u[1] * a + v[1] * b + w[1] * c,
            O[2] + u[2] * a + v[2] * b + w[2] * c)


def _lute_hw(s):
    """Half width of the pear-shaped soundboard at s (0 tail .. 1 neck joint)."""
    s = clamp(s)
    if s <= LUTE_WIDE:
        k = (LUTE_WIDE - s) / LUTE_WIDE
        return LUTE_R * math.sqrt(max(0.0, 1.0 - k * k))
    k = (s - LUTE_WIDE) / (1.0 - LUTE_WIDE)
    return LUTE_NECK_W + (LUTE_R - LUTE_NECK_W) * math.cos(math.pi * 0.5 * k) ** 1.25


_LUTE_S = (0.0, 0.025, 0.07, 0.13, 0.21, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


def _string_v(i, s_frac):
    """v offset of string i at the bridge (s_frac 0) .. the nut (s_frac 1)."""
    k = (i / (LUTE_STRINGS - 1)) * 2.0 - 1.0
    return k * lerp(8.0, 3.3, s_frac)


def _lute_vib(q):
    """Per-string vibration amplitude right now (lute units): the strings shimmer briefly after a
    stroke (a single string when tuning)."""
    st, pose = q.st, q.pose
    env = st["env"] * clamp(pose.strum_amt) * (1.0 - 0.8 * clamp(pose.tune))
    out = []
    for i in range(LUTE_STRINGS):
        a = env * 1.5 * (0.75 + 0.5 * core.hash01(i, 77))
        if pose.tune > 0.5 and st["env"] > 0:
            a = st["env"] * 1.7 if i == 2 else 0.0
        out.append(a)
    return out


def _lute(q, F):
    """The whole lute (back to front). Returns its attach points in body-local 2D."""
    proj = q.proj
    face = proj.depth(F["w"])
    if face > 0.0:
        _pegbox(q, F)
    _bowl(q, F, face)
    if face > -0.15:
        _soundboard(q, F)
    _neck(q, F)
    if face > -0.15:
        _strings(q, F)
    if face <= 0.0:
        _pegbox(q, F)
    _lute_ribbon(q, F)
    X = lambda a, b, c: proj.xy(_L(F, a, b, c))  # noqa: E731
    nut = LUTE_LB + LUTE_LN
    dp = _pegbox_dir(F)
    return {"rose": X(LUTE_ROSE * LUTE_LB, 0.0, 0.0), "bridge": X(LUTE_BRIDGE * LUTE_LB, 0.0, 1.0),
            "nut": X(nut, 0.0, 1.5), "center": X(LUTE_WIDE * LUTE_LB, 0.0, 0.0),
            "strum": X(STRUM_U * LUTE_LB, 0.0, 2.0),
            "pegbox": proj.xy(v_add(_L(F, nut, 0.0, 0.5), v_mul(dp, LUTE_LP)))}


def _bowl(q, F, face):
    """The ribbed pear-shaped bowl: a union of hulls between cross-sections, staves inked."""
    cr, proj, M = q.cr, q.proj, q.M
    secs = []
    for s in _LUTE_S:
        hw = _lute_hw(s)
        d = LUTE_D * (hw / LUTE_R) ** 0.7
        secs.append([proj.xy(_L(F, s * LUTE_LB, math.cos(math.pi * j / 8) * hw, -math.sin(math.pi * j / 8) * d))
                     for j in range(9)])
    groups = ((0, 7), (6, 10), (9, len(secs)))
    hulls = [core.convex_hull([p for sec in secs[a:b] for p in sec]) for a, b in groups]
    path = _union(q, hulls, M["bowl"], size=26, rim=0.9, tension=0.6)
    if q.detail >= 2 and face < 0.92:
        cr.save()
        path.add(cr)
        cr.clip()
        bp = q.P(M["bowl"])
        b2 = q.P(M["bowl2"])
        staves = []
        for j in range(1, 8):
            ph = math.pi * j / 8
            line = []
            for s in _LUTE_S[1:-1]:
                hw = _lute_hw(s)
                d = LUTE_D * (hw / LUTE_R) ** 0.7
                line.append(proj.xy(_L(F, s * LUTE_LB, math.cos(ph) * hw, -math.sin(ph) * d)))
            staves.append(line)
        # every other stave a lighter wood (yew and maple ribs)
        for j in range(0, len(staves) - 1, 2):
            cr.new_path()
            core.polygon(cr, staves[j] + staves[j + 1][::-1])
            core.src(cr, core.mix(b2.lit, b2.shadow, 0.3), 0.55)
            cr.fill()
        B.detail_lines(cr, staves, q.lw * 0.6, bp.line, 0.55, taper=(0.2, 1.0, 0.2))
        cr.restore()


def _soundboard(q, F):
    cr, proj, M = q.cr, q.proj, q.M
    right = [proj.xy(_L(F, s * LUTE_LB, _lute_hw(s), 0.0)) for s in _LUTE_S]
    left = [proj.xy(_L(F, s * LUTE_LB, -_lute_hw(s), 0.0)) for s in _LUTE_S[::-1]]
    pts = right + left[1:-1]
    sh, so = B.smooth_paths(cr, pts, q.lw * 0.9, 0.7)
    tp = q.shade(sh, M["top"], lw=q.lw * 0.9, outline=so, size=34, shadow=0.55, rim=0.7)
    cr.save()
    sh.add(cr)
    cr.clip()
    # well-loved: the worn patch where the quill strikes, and a darker halo round the rose
    wc = proj.xy(_L(F, STRUM_U * LUTE_LB, -2.0, 0.0))
    B.occlusion(cr, wc[0], wc[1], 13.0, 10.0, core.mix(tp.shadow, tp.line, 0.4), 0.32)
    if q.detail >= 1:
        # purfling just inside the edge
        inset = [proj.xy(_L(F, s * LUTE_LB, (_lute_hw(s) - 2.0) * sg, 0.0))
                 for sg, ss in ((1, _LUTE_S[1:-1]), (-1, _LUTE_S[-2:0:-1])) for s in ss]
        cr.new_path()
        core.smooth_closed(cr, inset, 0.7)
        cr.set_line_width(q.lw * 0.45)
        core.src(cr, tp.line, 0.55)
        cr.stroke()
    if q.detail >= 2:
        grain = []
        for vv in (-13.0, -7.0, 6.0, 12.0):
            grain.append([proj.xy(_L(F, s * LUTE_LB, vv, 0.0)) for s in (0.1, 0.4, 0.75)
                          if abs(vv) < _lute_hw(s) - 2.5])
        B.detail_lines(cr, [g for g in grain if len(g) >= 2], q.lw * 0.4, tp.line, 0.22)
    cr.restore()
    # the carved rose
    rc = LUTE_ROSE * LUTE_LB
    rr = LUTE_ROSE_R
    hole = [proj.xy(_L(F, rc + math.cos(TAU * i / 18) * rr, math.sin(TAU * i / 18) * rr, 0.0)) for i in range(18)]
    if q.detail >= 1:
        ring = [proj.xy(_L(F, rc + math.cos(TAU * i / 18) * rr * 1.32, math.sin(TAU * i / 18) * rr * 1.32, 0.0))
                for i in range(18)]
        cr.new_path()
        core.smooth_closed(cr, ring, 0.9)
        cr.set_line_width(q.lw * 0.5)
        core.src(cr, tp.line, 0.7)
        cr.stroke()
    cr.new_path()
    core.smooth_closed(cr, hole, 0.9)
    hp = Path(cr)
    hp.add(cr)
    core.src(cr, BARD_COLORS["rose"])
    cr.fill()
    if q.detail >= 1:
        cr.save()
        hp.add(cr)
        cr.clip()
        cr.new_path()
        # a six-fold rosette lattice carved into the top (in soundboard wood)
        for k in range(6):
            a0 = TAU * k / 6
            pet = [proj.xy(_L(F, rc + math.cos(a0) * rr * 0.52 + math.cos(a0 + TAU * i / 8) * rr * 0.34 * (1.0 if i % 2 else 0.55),
                              math.sin(a0) * rr * 0.52 + math.sin(a0 + TAU * i / 8) * rr * 0.34 * (1.0 if i % 2 else 0.55), 0.0))
                   for i in range(8)]
            core.smooth_closed(cr, pet, 0.9)
        ring2 = [proj.xy(_L(F, rc + math.cos(TAU * i / 16) * rr * 0.86, math.sin(TAU * i / 16) * rr * 0.86, 0.0)) for i in range(16)]
        core.smooth_closed(cr, ring2, 0.9)
        cr.set_line_width(q.lw * (0.55 if q.detail >= 2 else 0.8))
        core.src(cr, core.mix(tp.lit, tp.shadow, 0.35))
        cr.stroke()
        cr.restore()
    # the bridge
    bu = LUTE_BRIDGE * LUTE_LB
    bri = [proj.xy(_L(F, bu + du, dv, 1.2)) for du, dv in ((-1.8, -9.5), (1.8, -9.5), (1.8, 9.5), (-1.8, 9.5))]
    sh_b = [(x + 1.0, y + 1.6) for x, y in bri]
    cr.new_path()
    core.polygon(cr, sh_b)
    core.src(cr, tp.shadow, 0.7)
    cr.fill()
    _flat(q, bri, Mat.of(BARD_COLORS["bridge"], sheen=0.3), lw=q.lw * 0.5, tension=0.3)


def _neck(q, F, local=False):
    """Neck (rounded back), fingerboard, tied gut frets, the bone nut."""
    cr, proj, M = q.cr, q.proj, q.M
    j0, nut = LUTE_LB - 2.5, LUTE_LB + LUTE_LN
    back = _tube_pts([proj.xy(_L(F, j0, 0.0, -2.4)), proj.xy(_L(F, (j0 + nut) / 2, 0.0, -2.2)),
                      proj.xy(_L(F, nut, 0.0, -2.0))], [5.3, 4.9, 4.4])
    _union(q, [back], M["neck"], size=9, rim=0.7)
    board = [proj.xy(_L(F, LUTE_LB - 1.0, -4.6, 1.2)), proj.xy(_L(F, nut, -3.9, 1.4)),
             proj.xy(_L(F, nut, 3.9, 1.4)), proj.xy(_L(F, LUTE_LB - 1.0, 4.6, 1.2))]
    bp, bpal = _flat(q, board, M["board"], lw=q.lw * 0.6, tension=0.15)
    if q.detail >= 1:
        frets = []
        for kf in range(1, 9):
            uu = nut - LUTE_SCALE * (1.0 - 2.0 ** (-kf / 12.0))
            hw = lerp(3.9, 4.6, (nut - uu) / LUTE_LN)
            frets.append([proj.xy(_L(F, uu, -hw, 1.5)), proj.xy(_L(F, uu, hw, 1.5))])
        B.detail_lines(cr, frets, q.lw * 0.5, BARD_COLORS["fret"], 0.85, taper=(0.6, 1.0, 0.6))
    nb = [proj.xy(_L(F, nut - 1.2, -4.2, 1.6)), proj.xy(_L(F, nut + 0.6, -4.2, 1.8)),
          proj.xy(_L(F, nut + 0.6, 4.2, 1.8)), proj.xy(_L(F, nut - 1.2, 4.2, 1.6))]
    _flat(q, nb, Mat.of(BARD_COLORS["nut"]), lw=q.lw * 0.4, tension=0.2)


def _strings(q, F, region=None):
    """The seven strings from the bridge to the nut; right after a stroke they shimmer (drawn as
    the two extreme positions of their vibration -- the cartoon blur)."""
    cr, proj = q.cr, q.proj
    vib = q.vib
    bu, nut = LUTE_BRIDGE * LUTE_LB, LUTE_LB + LUTE_LN
    col = core.mix(BARD_COLORS["string"], q.P(q.M["top"]).lit, 0.25)
    ds = B.device_scale(cr)
    lwv = max(q.lw * 0.32, 0.55 / max(ds, 1e-6))
    still, shim = [], []
    for i in range(LUTE_STRINGS):
        a = proj.xy(_L(F, bu, _string_v(i, 0.0), 2.0))
        b = proj.xy(_L(F, nut, _string_v(i, 1.0), 2.6))
        amp = vib[i] if vib else 0.0
        if amp > 0.15:
            mu = 0.45
            vm = _string_v(i, mu)
            for sg in (-1.0, 1.0):
                m = proj.xy(_L(F, lerp(bu, nut, mu), vm + sg * amp, 2.3))
                shim.append((a, m, b))
        else:
            still.append((a, b))
    cr.save()
    cr.set_line_cap(1)
    cr.set_line_width(lwv)
    if still:
        cr.new_path()
        for a, b in still:
            cr.move_to(*a)
            cr.line_to(*b)
        core.src(cr, col, 0.9)
        cr.stroke()
    if shim:
        cr.new_path()
        for a, m, b in shim:
            cr.move_to(*a)
            cr.curve_to(a[0] + (m[0] - a[0]) * 1.3, a[1] + (m[1] - a[1]) * 1.3,
                        b[0] + (m[0] - b[0]) * 1.3, b[1] + (m[1] - b[1]) * 1.3, *b)
        core.src(cr, col, 0.55)
        cr.stroke()
    cr.restore()


def _pegbox_dir(F):
    return v_norm(v_add(v_mul(F["u"], math.cos(PEGBOX_BEND)), v_mul(F["w"], -math.sin(PEGBOX_BEND))))


def _pegbox(q, F):
    """The bent-back pegbox with its pegs (and the string ends running into it)."""
    cr, proj, M = q.cr, q.proj, q.M
    nut = LUTE_LB + LUTE_LN
    N3 = _L(F, nut, 0.0, 0.5)
    dp = _pegbox_dir(F)
    E3 = v_add(N3, v_mul(dp, LUTE_LP))
    pegs_far, pegs_near = [], []
    nk = 3 if q.detail >= 1 else 0
    for k in range(nk):
        f = 0.2 + 0.62 * k / max(1, nk - 1)
        base = v_add(N3, v_mul(dp, LUTE_LP * f))
        for sg in (-1.0, 1.0):
            a = v_add(base, v_mul(F["v"], sg * 3.0))
            b = v_add(v_add(base, v_mul(F["v"], sg * 8.5)), v_mul(dp, 1.2))
            ent = (proj.xy(a), proj.xy(b), sg, k)
            (pegs_near if proj.depth(v_mul(F["v"], sg)) >= 0 else pegs_far).append(ent)
    pp = q.P(M["peg"])

    def draw_pegs(lst):
        if not lst:
            return
        cr.new_path()
        for a, b, sg, k in lst:
            core.tapered(cr, [a, b], 2.4 + 2 * q.lw * 0.5, 1.8 + 2 * q.lw * 0.5)
            core.circle(cr, b[0], b[1], 2.9 + q.lw * 0.5)
        core.src(cr, pp.line)
        cr.fill()
        cr.new_path()
        for a, b, sg, k in lst:
            core.tapered(cr, [a, b], 2.4, 1.8)
            core.circle(cr, b[0], b[1], 2.9)
        core.src(cr, pp.lit)
        cr.fill()

    draw_pegs(pegs_far)
    box = _tube_pts([proj.xy(N3), proj.xy(v_lerp(N3, E3, 0.5)), proj.xy(E3)], [4.2, 3.7, 3.2])
    _union(q, [box], M["neck"], size=7, rim=0.7)
    if q.detail >= 1:
        # the open slot (the strings' ends wind in there) and a carved finial
        sl = [proj.xy(v_add(v_lerp(N3, E3, f), v_mul(F["u"], 1.6))) for f in (0.12, 0.5, 0.86)]
        B.detail_lines(cr, [sl], q.lw * 1.1, q.P(M["neck"]).deep, 0.85, taper=(0.4, 1.0, 0.5))
        ends = [[proj.xy(_L(F, nut, _string_v(i, 1.0), 2.6)), proj.xy(v_add(v_lerp(N3, E3, 0.15 + 0.1 * (i % 4)), v_mul(F["u"], 1.5)))]
                for i in range(0, LUTE_STRINGS, 2)]
        B.detail_lines(cr, ends, q.lw * 0.3, BARD_COLORS["string"], 0.5)
    draw_pegs(pegs_near)


def _lute_ribbon(q, F):
    """A red minstrel's ribbon tied at the pegbox, its two tails swaying."""
    proj, M, t = q.proj, q.M, q.t
    if q.detail < 1:
        return
    nut = LUTE_LB + LUTE_LN
    N3 = _L(F, nut, 0.0, 0.5)
    dp = _pegbox_dir(F)
    anchor = v_add(N3, v_mul(dp, 3.5))
    sw = B.chain(t, 4, freq=0.5, delay=0.14, amp=0.9 + 0.8 * q.st["env"], seed=q.pose.seed + 41, grow=2.2)
    for k, (L, off) in enumerate(((17.0, -1.5), (22.0, 1.8))):
        pts = [proj.xy(anchor)]
        p = anchor
        acc = 0.0
        for i in range(1, 4):
            acc += sw[i] * (1.0 if k else -0.8)
            p = v_add(p, (off * 0.5 + acc * 6.0, L / 3.0, 1.0 + acc * 2.0))
            pts.append(proj.xy(p))
        _ribbon(q, pts, 3.6, 2.6, M["ribbon"], lw=q.lw * 0.6, size=4, rim=0.4)
    a = proj.xy(anchor)
    _flat(q, _circ(a, 2.6, 8), M["ribbon"], lw=q.lw * 0.6)


# ----------------------------------------------------------------------------------------
# arms + hands
# ----------------------------------------------------------------------------------------

def _chord_shape(c):
    n = len(BARD_CHORDS)
    c = max(0.0, c)
    i = int(math.floor(c)) % n
    j = (i + 1) % n
    f = c - math.floor(c)
    (p0, k0), (p1, k1) = BARD_CHORDS[i], BARD_CHORDS[j]
    return lerp(p0, p1, f), lerp(k0, k1, f)


def _strum_grip(q):
    F, st, pose = q.F, q.st, q.pose
    amt = clamp(pose.strum_amt)
    tune = clamp(pose.tune)
    pos = st["pos"] * lerp(amt, 0.25, tune)
    u_s = STRUM_U * LUTE_LB + 2.0 * tune
    v_s = pos * STRUM_SPAN + 2.0 * tune
    w_s = 5.5 + 6.5 * st["lift"]
    grip = _L(F, u_s, v_s, w_s)
    d = v_norm(v_add(v_add(v_mul(F["v"], 0.80), v_mul(F["w"], -0.42)), v_mul(F["u"], -0.25 + 0.45 * st["twist"])))
    return grip, v_sub(grip, v_mul(d, HAND_LEN * 0.5)), d


def _fret_grip(q):
    F, pose = q.F, q.pose
    pos, curl = _chord_shape(pose.chord)
    if pose.chord_to is not None and pose.chord_mix > 0.0:
        p2, c2 = _chord_shape(pose.chord_to)
        pos, curl = lerp(pos, p2, clamp(pose.chord_mix)), lerp(curl, c2, clamp(pose.chord_mix))
    u_f = LUTE_LB + LUTE_LN * (1.0 - pos)
    grip = _L(F, u_f, 3.2, 1.2)
    d = v_norm(v_add(v_mul(F["v"], -0.82), v_mul(F["w"], 0.5)))
    hp = "grip"
    tune = clamp(pose.tune)
    if tune > 0:
        # up at the pegbox, pinching a peg and turning it
        nut = LUTE_LB + LUTE_LN
        dp = _pegbox_dir(F)
        peg = v_add(v_add(_L(F, nut, 0.0, 0.5), v_mul(dp, LUTE_LP * 0.45)), v_mul(F["v"], 9.5))
        wig = 0.25 * math.sin(TAU * pose.tune_phase)
        dt = v_norm(v_add(v_add(v_mul(F["v"], -0.55), v_mul(dp, 0.55 + wig)), v_mul(F["w"], 0.35)))
        u = core.inout_sine(tune)
        grip = v_lerp(grip, peg, u)
        d = v_norm(v_lerp(d, dt, u))
        curl = lerp(curl, 0.1, u)
        if u > 0.5:
            hp = "pinch"
    return grip, v_sub(grip, v_mul(d, HAND_LEN * 0.5)), d, curl, hp


def _gesture(q, side, arm, name=None, phase=None):
    """-> dict(wrist (body space), hand pose, d finger direction (body space) or None, curl,
    layer, palm, kind)."""
    S = q.S
    name = name or arm.gesture
    phase = arm.phase if phase is None else phase
    sk = S["shoulders"][side]
    if name == "play":
        name = "strum" if side < 0 else "fret"
    if name in ("strum", "fret") and (q.F is None or q.pose.lute != "play"):
        name = "rest"
    g = {"kind": name, "hand": "relaxed", "d": None, "curl": 0.0, "layer": "front", "palm": False}
    if name == "strum":
        _grip, wrist, d = _strum_grip(q)
        g.update(wrist=wrist, hand="pinch" if q.pose.tune < 0.5 else "point", d=d, layer="lute")
    elif name == "fret":
        _grip, wrist, d, curl, hp = _fret_grip(q)
        g.update(wrist=wrist, hand=hp, d=d, curl=curl, layer="lute")
    elif name == "present":
        g.update(wrist=v_add(sk, (side * 33.0, 2.0, 20.0)), hand="offer", palm=True)
    elif name == "wave":
        g.update(wrist=v_add(sk, (side * (20.0 + 6.0 * math.sin(phase * TAU * 2.0)), -27.0, 10.0)), hand="open",
                 palm=True)
    elif name == "tip_cap":
        hc = S["head_c"]
        g.update(wrist=v_add(hc, (side * 15.0, -10.0 - 9.0 * clamp(phase), 4.0)), hand="pinch")
    elif name == "point":
        g.update(wrist=v_add(sk, (side * 10.0, 6.0, 36.0)), hand="point")
    else:                                   # "rest" (and anything unknown)
        k = S["sit_k"]
        stand = v_add(sk, (side * 8.0, 40.0, 6.0))
        lap = v_add(S["knee"][side], (-side * 2.0, -10.0, -6.0))
        sw = S["wc"].arms[0 if side < 0 else 1] * S["walk"]
        stand = v_add(stand, (side * abs(sw) * 3.0, -abs(sw) * 4.0, sw * 14.0))
        g.update(kind="rest", wrist=v_lerp(stand, lap, k), layer="auto")
    return g


BARD_GESTURES = ("play", "strum", "fret", "rest", "present", "wave", "tip_cap", "point")


def _solve_arm(q, side, arm):
    S = q.S
    g = _gesture(q, side, arm)
    tgt = g["wrist"]
    g["d0"], g["u"] = None, 1.0
    if arm.amt < 1.0:
        g0 = _gesture(q, side, arm, name=arm.prev, phase=0.0)
        u = core.inout_sine(clamp(arm.amt))
        arc = math.sin(math.pi * u) * 7.0
        tgt = v_add(v_lerp(g0["wrist"], tgt, u), (side * arc * 0.5, -arc * 0.6, arc))
        if u < 0.5:
            g["hand"], g["palm"], g["layer"] = g0["hand"], g0["palm"], g0["layer"] if g["layer"] == "auto" else g["layer"]
        g["curl"] = lerp(g0["curl"], g["curl"], u)
        g["d0"], g["u"] = g0["d"], u
        if g0["kind"] in ("strum", "fret") or g["kind"] in ("strum", "fret"):
            g["layer"] = "lute"
    if arm.target is not None:
        tgt = arm.target
    if arm.hand:
        g["hand"] = arm.hand
    sk = S["shoulders"][side]
    dv = v_sub(tgt, sk)
    dl = B.v_len(dv)
    reach = (UPPER_ARM + FOREARM) * 0.97
    if dl > reach:                          # the shoulder follows a long reach a little
        sk = v_add(sk, v_mul(dv, min(7.0, dl - reach) / dl))
    if g["kind"] == "strum":
        pole = (side * 1.0, 0.15, -0.95)       # elbow out and back: the forearm over the lute's edge
    elif g["kind"] == "fret":
        pole = (side * 1.0, 0.55, -0.5)
    else:
        pole = (side * 1.0, 0.75, -0.45)
    el, wr = B.ik3(sk, tgt, UPPER_ARM, FOREARM, pole)
    g.update(sh=sk, el=el, wr=wr, side=side, arm=arm)
    return g


def _quill_hold(q):
    """The plectrum: a little quill of his own, pinched between thumb and index, tip at the
    strings, the vane sticking out of the back of the fist."""
    M = q.M
    lw = q.lw * 0.55

    def draw(cr, f):
        cr.save()
        cr.rotate(0.35)
        qp = q.P(M["quill"])
        vane = [(-3.0, -1.2), (-7.0, -4.2), (-11.0, -5.2), (-9.0, -2.2), (-5.0, 0.4)]
        cr.new_path()
        core.smooth_closed(cr, B.offset_closed(_pos(vane), lw), 0.8)
        core.tapered(cr, [(-4.0, -1.0), (6.0, 1.0)], 1.5 + 2 * lw, 0.7 + 2 * lw)
        core.src(cr, qp.line)
        cr.fill()
        cr.new_path()
        core.smooth_closed(cr, _pos(vane), 0.8)
        core.tapered(cr, [(-4.0, -1.0), (6.0, 1.0)], 1.5, 0.7)
        core.src(cr, qp.lit)
        cr.fill()
        cr.restore()
    return draw


def _hand_screen(q, wr3, d):
    a = q.proj.xy(wr3)
    b = q.proj.xy(v_add(wr3, v_mul(d, 10.0)))
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return math.atan2(dy, dx), clamp(L / 10.0, 0.6, 1.0)


def _arm(q, A, parts="all"):
    """Puffed burgundy sleeve with gold slashes, a cream feather cuff, the scaly hand."""
    cr, proj, M = q.cr, q.proj, q.M
    side = A["side"]
    arm = A["arm"]
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    fdx, fdy = core.normalize((wr[0] - el[0], wr[1] - el[1]))
    fore_ang = math.atan2(fdy, fdx)
    if parts in ("all", "sleeve"):
        mid = ((sh[0] + el[0]) / 2.0, (sh[1] + el[1]) / 2.0)
        puff = _tube_pts([sh, mid, el], [7.8, 9.0, 6.4])
        fore = _tube_pts([el, wr], [6.3, 5.2])
        path = _union(q, [puff, fore], M["doublet"], size=17, rim=0.8)
        if q.detail >= 1:
            cr.save()
            path.add(cr)
            cr.clip()
            ux, uy = core.normalize((el[0] - sh[0], el[1] - sh[1]))
            nx, ny = -uy, ux
            sl, dk = [], []
            for f in (-0.45, 0.45):
                line = []
                for tt, rr in ((0.12, 7.6), (0.5, 9.0), (0.86, 6.6)):
                    bx, by = lerp(sh[0], el[0], tt), lerp(sh[1], el[1], tt)
                    line.append((bx + nx * rr * f, by + ny * rr * f))
                sl.append(line)
                dk.append([(x + nx * 1.6, y + ny * 1.6) for x, y in line])
            gp = q.P(M["gold"])
            B.detail_lines(cr, dk, q.lw * 1.5, q.P(M["doublet"]).deep, 0.5, taper=(0.1, 1.0, 0.1))
            B.detail_lines(cr, sl, q.lw * 1.45, gp.lit, 1.0, taper=(0.1, 1.0, 0.1))
            cr.restore()
        # the cream feather cuff at the wrist
        cx_, cy_ = wr[0] - fdx * 1.0, wr[1] - fdy * 1.0
        cuff = []
        for i in range(10):
            a = TAU * i / 10
            r = (5.0 if i % 2 == 0 else 3.6)
            lx, ly = math.cos(a) * r * 0.75 + (1.8 if math.cos(a) > 0.3 else 0.0), math.sin(a) * (7.4 if i % 2 == 0 else 6.2)
            cuff.append((cx_ + lx * fdx - ly * fdy, cy_ + lx * fdy + ly * fdx))
        _flat(q, cuff, M["cream"], lw=q.lw * 0.8, tension=0.6)
    if parts == "sleeve":
        return None
    hp = A["hand"]
    if A["d"] is not None or A.get("d0") is not None:
        angs = []
        fs = 1.0
        for dd in (A.get("d0"), A["d"]):
            if dd is None:
                angs.append(fore_ang)
            else:
                ang_, fs_ = _hand_screen(q, A["wr"], dd)
                angs.append(ang_)
                fs = min(fs, fs_) if dd is A["d"] else fs
        u = A.get("u", 1.0)
        ang = core.lerp_angle(angs[0], angs[1], u) if A.get("d0") is not None or A["d"] is None else angs[1]
        if A["d"] is None:
            ang = core.lerp_angle(angs[0], fore_ang, u)
    else:
        ang = fore_ang
        fs = 1.0
    flip = (side > 0) == (q.yaw >= 0)
    hold = arm.hold
    if A["kind"] == "strum" and hold is None and q.pose.tune < 0.5:
        hold = _quill_hold(q)
    if A["kind"] == "fret" and hold is None and A.get("u", 1.0) > 0.5 and q.pose.tune < 0.5:
        hold = _neck_over(q, wr, ang, fs)
    return B.hand(cr, wr[0] + fdx * 1.5, wr[1] + fdy * 1.5, ang, HAND_LEN * fs, hp, M["scaly"], q.light, q.lw,
                  flip=flip, claw=None, show_palm=A["palm"],
                  pad=BARD_COLORS["cream"], hold=hold, curl_add=A["curl"], detail=q.detail, palm_w=1.12,
                  finger_w=1.08)


def _neck_over(q, wr, ang, fs):
    """Fret hand: a hold callback that redraws the neck between the palm (behind it) and the
    curled fingers (over it), clipped round the hand -- the neck sits IN the hand."""
    m_local = q.cr.get_matrix()
    L = HAND_LEN * fs
    cx, cy = wr[0] + math.cos(ang) * L * 0.42, wr[1] + math.sin(ang) * L * 0.42
    F = q.F

    def cb(cr, f):
        cr.save()
        cr.set_matrix(m_local)
        cr.new_path()
        core.circle(cr, cx, cy, L * 0.62)
        cr.clip()
        _neck(q, F)
        _strings(q, F)
        cr.restore()
    return cb


# ----------------------------------------------------------------------------------------
# legs + boots
# ----------------------------------------------------------------------------------------

def _leg(q, f):
    cr, proj, M = q.cr, q.proj, q.M
    knee, ank = proj.xy(f["knee"]), proj.xy(f["ankle"])
    # the scaly shank (a thin chicken leg) ...
    _union(q, [_tube_pts([knee, ank], [3.6, 3.0])], M["scaly"], size=6, rim=0.5)
    # ... into the soft boot ...
    _boot(q, f)
    # ... under a plump feathered drumstick
    hip = proj.xy(f["hip"])
    th = core.convex_hull(_circ(hip, 9.6, 12) + _circ(knee, 6.8, 12))
    tp = _union(q, [th], M["plumage"], size=15, rim=0.6)
    if q.detail >= 1:
        cr.save()
        tp.add(cr)
        cr.clip()
        pal = q.P(M["plumage"])
        ux, uy = core.normalize((knee[0] - hip[0], knee[1] - hip[1]))
        nx, ny = -uy, ux
        marks = []
        for tt, off in ((0.35, -0.35), (0.55, 0.3), (0.75, -0.1), (0.2, 0.25)):
            bx, by = lerp(hip[0], knee[0], tt) + nx * 6.0 * off, lerp(hip[1], knee[1], tt) + ny * 6.0 * off
            marks.append([(bx - nx * 2.6 - ux * 1.5, by - ny * 2.6 - uy * 1.5), (bx + ux * 1.4, by + uy * 1.4),
                          (bx + nx * 2.6 - ux * 1.5, by + ny * 2.6 - uy * 1.5)])
        B.detail_lines(cr, marks, q.lw * 0.7, pal.line, 0.5, taper=(0.2, 1.0, 0.2))
        cr.restore()


def _boot(q, f):
    """A slouchy soft leather boot shaped round three chicken toes, claw tips poking out."""
    cr, proj, M = q.cr, q.proj, q.M
    a3 = f["ankle"]
    kn3 = f["knee"]
    pitch = f["pitch"]
    base = (a3[0], a3[1] + ANKLE_H, a3[2])
    c, s = math.cos(pitch), math.sin(pitch)

    def FP(dx, dy, dz):
        zz = dz + 4.0
        return proj.xy((base[0] + dx, base[1] + dy * c - zz * s, base[2] + dy * s + zz * c - 4.0))

    up = v_norm(v_sub(kn3, a3))
    top3 = v_add(a3, v_mul(up, 5.5))
    shaft = []
    for i in range(10):
        a = TAU * i / 10
        shaft.append(proj.xy((top3[0] + math.sin(a) * 5.0, top3[1], top3[2] + math.cos(a) * 4.6)))
    foot = []
    for i in range(8):
        a = TAU * i / 8
        ca, sa = math.cos(a), math.sin(a)
        foot.append(FP(ca * 5.2, -7.5 + sa * 1.5, sa * 4.6))           # ankle
        foot.append(FP(ca * 4.2, -3.6 + sa * 3.4, -5.0))               # heel
        foot.append(FP(ca * 6.4, -3.4 + sa * 3.2, 5.0))                # ball
    hull = core.convex_hull(shaft + foot)
    toes = [(FP(tx, -3.3, tz), r) for tx, tz, r in ((-4.7, 10.2, 3.3), (0.0, 12.2, 3.7), (4.7, 10.2, 3.3))]
    bp = _union(q, [hull], M["boot"], size=12, rim=0.6, circles=toes)
    pal = q.P(M["boot"])
    # the slouched cuff
    cuff = []
    for i in range(12):
        a = TAU * i / 12
        cuff.append(proj.xy((top3[0] + math.sin(a) * 6.3, top3[1] + 1.2 + 1.4 * math.cos(a * 2.0 + 0.5), top3[2] + math.cos(a) * 5.6)))
    cuff = core.convex_hull(cuff)
    _flat(q, cuff, M["boot_cuff"], lw=q.lw * 0.8, tone=0.15)
    if q.detail >= 1:
        cr.save()
        bp.add(cr)
        cr.clip()
        seams = [[FP(-2.4, -4.4, 8.6), FP(-2.8, -5.4, 6.0)], [FP(2.4, -4.4, 8.6), FP(2.8, -5.4, 6.0)]]
        B.detail_lines(cr, seams, q.lw * 0.6, pal.line, 0.55)
        cr.restore()
    # claw tips poking out of the toe ends
    cp = q.P(M["claw"])
    cr.new_path()
    for tx, tz in ((-4.7, 10.2), (0.0, 12.2), (4.7, 10.2)):
        a0, a1 = FP(tx, -2.4, tz + 2.6), FP(tx, -0.4, tz + 6.2)
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]
        L = math.hypot(dx, dy)
        if L < 0.8:
            continue
        nx, ny = -dy / L * 1.5, dx / L * 1.5
        cr.move_to(a0[0] + nx, a0[1] + ny)
        cr.line_to(a1[0], a1[1])
        cr.line_to(a0[0] - nx, a0[1] - ny)
        cr.close_path()
    B.flat(cr, Path(cr), cp.lit, q.lw * 0.45, cp.line)


# ----------------------------------------------------------------------------------------
# torso: the patched burgundy doublet over a round belly
# ----------------------------------------------------------------------------------------

def _torso_rings(q):
    S = q.S
    T = S["T"]
    br = S["br"]
    return [
        (T((0.0, -55.5, 0.0)), 13.0, 11.0),                               # 0 collar
        (T((0.0, -49.0, 0.0)), 25.0, 20.0),                               # 1 shoulders
        (T((0.0, -39.0, 4.0 + 0.4 * br)), 30.5, 26.0),                    # 2 chest
        (T((0.0, -25.0, 8.0 + 0.8 * br)), 34.0 + 0.5 * br, 30.0 + 0.6 * br),   # 3 belly (widest)
        (T((0.0, -11.0, 7.0)), 32.0, 28.0),                               # 4 belt
        (T((0.0, 1.0, 4.0)), 28.0, 24.5),                                 # 5 hem
    ]


def _rp(ring, phi, dy=0.0, k=1.0):
    c, a, cz = ring
    return (c[0] + math.sin(phi) * a * k, c[1] + dy, c[2] + math.cos(phi) * cz * k)


def _rl(r0, r1, u):
    return (v_lerp(r0[0], r1[0], u), lerp(r0[1], r1[1], u), lerp(r0[2], r1[2], u))


def _vis(q, phi):
    return q.proj.depth((math.sin(phi), 0.0, math.cos(phi)))


def _torso(q):
    cr, proj, M = q.cr, q.proj, q.M
    rings = _torso_rings(q)
    pts = []
    for r in rings:
        pts += [proj.xy(_rp(r, TAU * i / 12)) for i in range(12)]
    hull = core.convex_hull(pts)
    hem = rings[-1]
    dags = []
    nd = 14
    for k in range(nd):
        phi = -math.pi + (k + 0.5) * TAU / nd
        if _vis(q, phi) < -0.25:
            continue
        w = math.pi / nd * 0.95
        dags.append(core.convex_hull([proj.xy(_rp(hem, phi - w, -2.0)), proj.xy(_rp(hem, phi + w, -2.0)),
                                      proj.xy(_rp(hem, phi + w * 0.55, 4.2)), proj.xy(_rp(hem, phi, 6.4)),
                                      proj.xy(_rp(hem, phi - w * 0.55, 4.2))]))
    path = _union(q, [hull] + dags, M["doublet"], size=62, shadow=0.85, rim=1.0)
    dp = q.P(M["doublet"])
    gp = q.P(M["gold"])
    front = proj.depth((0.0, 0.0, 1.0))
    cr.save()
    path.add(cr)
    cr.clip()
    # hem trim (gold band above the dags)
    run = [proj.xy(_rp(hem, phi, -2.6, 1.01)) for phi in [-math.pi + TAU * i / 32 for i in range(33)]
           if _vis(q, phi) > 0.02]
    if len(run) >= 2:
        _ribbon(q, run, 2.8, 2.8, M["gold"], lw=q.lw * 0.6, size=3, rim=0.6, cap=False)
    # the V neck showing his cream breast feathers
    r0, r1, r2 = rings[0], rings[1], rings[2]
    if front > -0.2:
        vpts = [proj.xy(_rp(r0, -0.8)), proj.xy(_rp(_rl(r0, r1, 0.5), -0.55)), proj.xy(_rp(r2, 0.0, 3.0, 1.01)),
                proj.xy(_rp(_rl(r0, r1, 0.5), 0.55)), proj.xy(_rp(r0, 0.8)), proj.xy(_rp(r0, 0.0, -4.0))]
        vp = _union(q, [core.convex_hull(vpts)], M["cream"], size=16, rim=0.4, lw=q.lw * 0.7)
        if q.detail >= 1:
            cpal = q.P(M["cream"])
            cr.save()
            vp.add(cr)
            cr.clip()
            sc = []
            for (ph, dy) in ((-0.25, -1.0), (0.25, -1.0), (0.0, 3.5), (-0.18, 8.0), (0.18, 8.0)):
                c3 = _rp(_rl(r1, r2, 0.3), ph, dy * 0.6, 1.01)
                c2 = proj.xy(c3)
                sc.append([(c2[0] - 3.0, c2[1] - 1.0), (c2[0], c2[1] + 1.8), (c2[0] + 3.0, c2[1] - 1.0)])
            B.detail_lines(cr, sc, q.lw * 0.6, cpal.line, 0.45)
            cr.restore()
            edges = [[proj.xy(_rp(r0, -0.85)), proj.xy(_rp(_rl(r0, r1, 0.5), -0.6)), proj.xy(_rp(r2, 0.0, 3.2, 1.01))],
                     [proj.xy(_rp(r0, 0.85)), proj.xy(_rp(_rl(r0, r1, 0.5), 0.6)), proj.xy(_rp(r2, 0.0, 3.2, 1.01))]]
            B.detail_lines(cr, edges, q.lw * 1.3, gp.lit, 1.0, taper=(1.0, 1.0, 0.4))
    # closure seam, buttons straining over the belly
    if front > 0.0:
        seam = [proj.xy(_rp(rings[k], 0.04, 0.0, 1.01)) for k in (2, 3, 4)] + [proj.xy(_rp(hem, 0.04, -2.0, 1.01))]
        B.detail_lines(cr, [seam], q.lw * 0.9, dp.line, 0.75, taper=(0.4, 1.0, 0.6))
    if q.detail >= 2:
        folds = []
        for sg in (-1.0, 1.0):
            a3 = _rp(_rl(rings[2], rings[3], 0.7), 0.1 * sg, 0.0, 1.01)
            b3 = _rp(_rl(rings[2], rings[3], 0.55), 0.55 * sg, 0.0, 1.01)
            if _vis(q, 0.4 * sg) > 0.1:
                folds.append([proj.xy(a3), proj.xy(v_lerp(a3, b3, 0.5)), proj.xy(b3)])
        B.detail_lines(cr, folds, q.lw * 0.8, dp.line, 0.4, taper=(0.1, 1.0, 0.1))
    # patches: an ochre one on his left belly, a slate one on his right chest
    for (ra, rb, u, phi, dphi, dy, mat, seed) in ((3, 4, 0.45, 0.82, 0.2, 6.5, "patch", 1),
                                                  (1, 2, 0.6, -0.62, 0.15, 4.5, "patch2", 2)):
        if _vis(q, phi) < 0.18:
            continue
        rr = _rl(rings[ra], rings[rb], u)
        corners = [proj.xy(_rp(rr, phi - dphi, -dy, 1.015)), proj.xy(_rp(rr, phi + dphi, -dy * 0.9, 1.015)),
                   proj.xy(_rp(rr, phi + dphi * 1.05, dy, 1.015)), proj.xy(_rp(rr, phi - dphi * 0.95, dy * 1.1, 1.015))]
        pp, ppal = _flat(q, corners, M[mat], lw=q.lw * 0.6, tension=0.35)
        if q.detail >= 1:
            ticks = []
            nc = len(corners)
            for i in range(nc):
                a, b = corners[i], corners[(i + 1) % nc]
                for k in range(1, 4):
                    m = core.lerp_pt(a, b, k / 4.0)
                    cx_, cy_ = sum(p[0] for p in corners) / nc, sum(p[1] for p in corners) / nc
                    ix, iy = core.normalize((cx_ - m[0], cy_ - m[1]))
                    ticks.append([(m[0] - ix * 1.4, m[1] - iy * 1.4), (m[0] + ix * 1.4, m[1] + iy * 1.4)])
            B.detail_lines(cr, ticks, q.lw * 0.5, ppal.line, 0.85, taper=(1.0, 1.0, 1.0))
    cr.restore()
    # the belt under the belly, a brass buckle, his purse
    belt = rings[4]
    run = [proj.xy(_rp(belt, phi, 0.0, 1.02)) for phi in [-math.pi + TAU * i / 36 for i in range(37)] if _vis(q, phi) > -0.02]
    if len(run) >= 2:
        _ribbon(q, run, 5.4, 5.4, M["belt"], lw=q.lw * 0.7, size=5, rim=0.5, cap=False)
        if _vis(q, 0.1) > 0.15:
            bc = proj.xy(_rp(belt, 0.1, 0.0, 1.03))
            bk = [(bc[0] - 3.6, bc[1] - 3.4), (bc[0] + 3.6, bc[1] - 3.4), (bc[0] + 3.6, bc[1] + 3.4), (bc[0] - 3.6, bc[1] + 3.4)]
            _flat(q, bk, M["gold"], lw=q.lw * 0.6, tension=0.4)
            core.src(cr, gp.line)
            cr.rectangle(bc[0] - 1.4, bc[1] - 1.6, 2.8, 3.2)
            cr.fill()
    if _vis(q, -1.05) > 0.0:
        top = proj.xy(_rp(belt, -1.05, 2.0, 1.03))
        pouch = [(top[0] - 5.5, top[1] - 1.0), (top[0] + 5.0, top[1] - 1.0), (top[0] + 6.5, top[1] + 7.5),
                 (top[0] + 2.0, top[1] + 12.0), (top[0] - 4.0, top[1] + 11.5), (top[0] - 7.0, top[1] + 6.0)]
        _union(q, [pouch], M["pouch"], size=10, rim=0.5, lw=q.lw * 0.8)
        flap = [(top[0] - 5.6, top[1] - 1.5), (top[0] + 5.2, top[1] - 1.5), (top[0] + 4.0, top[1] + 4.0), (top[0] - 4.6, top[1] + 4.2)]
        _flat(q, flap, M["belt"], lw=q.lw * 0.6, tone=0.1, tension=0.5)
    # buttons (over the belt line's top)
    if front > 0.05:
        bts = []
        for u in (0.15, 0.42, 0.7, 0.95):
            rr = _rl(rings[2], rings[4], u)
            if _vis(q, 0.06) > 0.1:
                bts.append(proj.xy(_rp(rr, 0.06, 0.0 if u < 0.9 else -2.5, 1.03)))
        if bts:
            lwb = q.lw * 0.6
            cr.new_path()
            for p in bts:
                core.circle(cr, p[0], p[1], 2.7 + lwb)
            core.src(cr, gp.line)
            cr.fill()
            for p in bts:
                core.circle(cr, p[0], p[1], 2.7)
            q.shade(Path(cr), M["gold"], lw=lwb, outline=False, size=5, rim=0.6)
            for p in bts:
                B.sheen(cr, p[0] - 0.8, p[1] - 0.9, 1.3, 1.0, alpha=0.8)
    return path


def _strap(q):
    """Lute slung on the back: the strap across his chest (right shoulder -> left hip)."""
    S, proj = q.S, q.proj
    T = S["T"]
    pts = [proj.xy(T(v)) for v in ((-20.0, -52.0, 12.0), (-6.0, -42.0, 27.0), (12.0, -24.0, 33.0), (26.0, -8.0, 22.0))]
    _ribbon(q, pts, 5.0, 5.0, q.M["belt"], lw=q.lw * 0.7, size=5, rim=0.5, cap=False)


def _ruff(q):
    """The hackle ruff: two rows of pointed golden-chestnut feathers over the collar."""
    cr, proj, M, S = q.cr, q.proj, q.M, q.S
    T = S["T"]
    c = T((0.0, -53.0, 1.0))
    for (n, L, W, a, cz, dy, off) in ((11, 17.0, 10.5, 17.0, 14.5, 0.0, 0.0),):
        leaves, veins = [], []
        for k in range(n):
            phi = TAU * (k + off) / n
            out = (math.sin(phi), 0.0, math.cos(phi))
            if proj.depth(out) < -0.35:
                continue
            base = (c[0] + out[0] * a, c[1] + dy, c[2] + out[2] * cz)
            tan = (math.cos(phi), 0.0, -math.sin(phi))
            tip = v_add(base, (out[0] * L * 0.22, L, out[2] * L * 0.28))
            mid = v_lerp(base, tip, 0.35)
            p3 = [v_add(base, v_mul(tan, -W * 0.5)), v_add(mid, v_mul(tan, -W * 0.5)), tip,
                  v_add(mid, v_mul(tan, W * 0.5)), v_add(base, v_mul(tan, W * 0.5)), v_add(base, (0.0, -3.0, 0.0))]
            leaves.append(core.convex_hull([proj.xy(p) for p in p3]))
            veins.append([proj.xy(base), proj.xy(v_lerp(base, tip, 0.78))])
        if not leaves:
            continue
        _union(q, leaves, M["hackle"], size=13, rim=0.7, tension=0.7)
        if q.detail >= 1:
            B.detail_lines(cr, veins, q.lw * 0.6, q.P(M["hackle"]).line, 0.3, taper=(0.5, 1.0, 0.1))


# ----------------------------------------------------------------------------------------
# wings + tail (the dragon in him)
# ----------------------------------------------------------------------------------------

def _wing(q, side):
    cr, proj, M, pose, t, S = q.cr, q.proj, q.M, q.pose, q.t, q.S
    w = clamp(pose.wings + 0.3 * S["dip"] + 0.25 * clamp(pose.rapture), -1.0, 1.0)
    lift = (w + 1.0) / 2.0
    flutter = 0.05 * math.sin(t * 2.6 + side) + 0.05 * S["dip_lag"]
    T = S["T"]
    root = T((side * 12.0, -45.0, -19.0))
    wrist = v_add(root, (side * (9.0 + 9.0 * lift), -5.0 - 24.0 * lift + flutter * 26.0, -7.0 - 5.0 * lift))
    tips = []
    for k in range(3):
        ang = lerp(0.18 + 0.24 * k, -1.0 + 0.45 * k, lift) + flutter
        L = 27.0 - 4.5 * k
        tips.append(v_add(wrist, (side * ((3.0 + 5.0 * k) * (0.4 + lift) + math.sin(ang) * L * 0.35),
                                  math.cos(ang) * L, -6.0 - 5.0 * k - 8.0 * lift)))
    pr, pw = proj.xy(root), proj.xy(wrist)
    t0, t1, t2 = (proj.xy(p) for p in tips)
    back_pt = proj.xy(v_add(root, (side * 2.0, 22.0, 5.0)))
    cr.new_path()
    cr.move_to(*pr)
    cr.line_to(*pw)
    cr.line_to(*t0)

    def scallop(a, b):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        cx_, cy_ = lerp(mx, pw[0], 0.32), lerp(my, pw[1], 0.32)
        cr.curve_to(lerp(a[0], cx_, 0.6), lerp(a[1], cy_, 0.6), lerp(b[0], cx_, 0.6), lerp(b[1], cy_, 0.6), b[0], b[1])

    scallop(t0, t1)
    scallop(t1, t2)
    cr.curve_to(lerp(t2[0], back_pt[0], 0.4), lerp(t2[1], back_pt[1], 0.2), back_pt[0], back_pt[1] - 6, back_pt[0], back_pt[1])
    cr.close_path()
    q.shade(Path(cr), M["membrane"], size=22, rim=0.8)
    lw = q.lw
    bones = [([pr, ((pr[0] + pw[0]) / 2, (pr[1] + pw[1]) / 2 - 1.0), pw], 5.2, 3.8)]
    bones += [([pw, ((pw[0] + tp[0]) / 2, (pw[1] + tp[1]) / 2), tp], 3.0, 1.0) for tp in (t0, t1, t2)]
    sp_ = q.P(M["dragon"])
    cr.new_path()
    for b_pts, w0, w1 in bones:
        core.tapered(cr, b_pts, w0 + 2 * lw * 0.8, w1 + 2 * lw * 0.8)
    core.src(cr, sp_.line)
    cr.fill()
    for b_pts, w0, w1 in bones:
        core.tapered(cr, b_pts, w0, w1)
    core.src(cr, core.mix(sp_.lit, sp_.shadow, 0.3))
    cr.fill()
    cp = q.P(M["claw"])
    sx = side if q.yaw >= 0 else -side
    cr.new_path()
    cr.move_to(pw[0] - 2.4, pw[1] + 0.6)
    cr.curve_to(pw[0] - 1.8, pw[1] - 4.2, pw[0] + sx * 1.8, pw[1] - 6.6, pw[0] + sx * 3.6, pw[1] - 7.2)
    cr.line_to(pw[0] + 2.4, pw[1])
    cr.close_path()
    B.flat(cr, Path(cr), cp.lit, q.lw * 0.5, cp.line)


def _tail_spine(q):
    S = q.S
    pel = S["pelvis"]
    stand = [v_add(pel, (0.0, 2.0, -22.0)), (3.0, -24.0, -34.0), (10.0, -10.0, -48.0), (22.0, -5.5, -60.0),
             (36.0, -6.0, -68.0), (49.0, -11.0, -70.0), (57.0, -21.0, -66.0)]
    if q.sit <= 0.0:
        return stand
    sg = clamp(0.6 * math.cos(q.yaw) - 1.3 * math.sin(q.yaw), -1.0, 1.0)
    base = v_add(pel, (0.0, 2.0, -20.0))
    # off the back of the seat: it hangs (from a high bench) or lies along the floor (from his
    # little stool) and curls up toward the side the camera sees best
    rel = [(sg * 5.0, 14.0, -10.0), (sg * 12.0, 32.0, -28.0), (sg * 24.0, 46.0, -40.0), (sg * 38.0, 54.0, -42.0),
           (sg * 50.0, 50.0, -36.0), (sg * 56.0, 40.0, -27.0)]
    floor = (-12.0, -5.5, -6.0, -6.0, -11.0, -21.0)
    seat = [base]
    for (dx, dy, dz), fl in zip(rel, floor):
        y_ = min(base[1] + dy, fl)
        seat.append((dx, y_, dz))
    k = smooth(q.sit)
    return [v_lerp(a, b, k) for a, b in zip(stand, seat)]


def _tail(q):
    """Scaly green dragon tail, dorsal spikes, a pale belly stripe, and a tuft of rooster feathers
    at the tip that flicks (and taps the beat)."""
    cr, proj, M, pose, t, S = q.cr, q.proj, q.M, q.pose, q.t, q.S
    swing = pose.tail_swing + 0.22 * B.sway(t * 0.6, 0.5, pose.seed + 3)
    curl = clamp(pose.tail_curl + 0.12 * math.sin(t * 0.7 + 1.3) + 0.25 * S["dip_lag"])
    wav = B.chain(t, 7, freq=0.32, delay=0.18, amp=0.5, seed=pose.seed + 11, grow=2.4)
    pts = _tail_spine(q)
    out = []
    n = len(pts)
    acc = 0.0
    for i, p in enumerate(pts):
        u = i / (n - 1)
        if i:
            acc += wav[min(i, len(wav) - 1)]
        dx = (swing * 30.0 * u * u + acc * 26.0 * u) * (1.0 - 0.5 * q.sit)
        lift = -curl * 14.0 * smooth((u - 0.6) / 0.4)
        out.append(proj.xy((p[0] + dx, p[1] + lift, p[2])))
    radii = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.3]
    sp = core.spline(out, n=4, tension=0.8)
    if q.detail >= 1:
        cr.new_path()
        ns = len(sp)
        for k in range(3, ns - 4, 3):
            p0, p1 = sp[k], sp[k + 1]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            nx, ny = uy, -ux
            if ny > 0:
                nx, ny = -nx, -ny
            u = k / ns
            rr = radii[0] + (radii[-1] - radii[0]) * u
            h = 5.5 * (1.0 - u) + 2.0
            bx, by = p0[0] + nx * rr * 0.7, p0[1] + ny * rr * 0.7
            cr.move_to(bx - ux * h * 0.8, by - uy * h * 0.8)
            cr.curve_to(bx + nx * h * 0.5, by + ny * h * 0.5, bx + nx * h + ux * h * 0.1, by + ny * h + uy * h * 0.1,
                        bx + nx * h * 1.05 + ux * h * 0.55, by + ny * h * 1.05 + uy * h * 0.55)
            cr.line_to(bx + ux * h * 0.8, by + uy * h * 0.8)
            cr.close_path()
        spikes = Path(cr)
        B.outline_under(cr, spikes, q.lw * 0.8, q.P(M["dragon_dk"]).line)
        q.shade(spikes, M["dragon_dk"], outline=False, rim=0.0, size=4, shadow=0.6)
    tail = _tube_pts(out, radii, samples=4, tension=0.85)
    tp = _union(q, [tail], M["dragon"], size=13, rim=0.8, tension=0.9)
    if q.detail >= 1:
        cr.save()
        tp.add(cr)
        cr.clip()
        ns = len(sp)
        under = [(sp[i][0], sp[i][1] + (radii[0] + (radii[-1] - radii[0]) * i / (ns - 1)) * 1.02) for i in range(ns)]
        bpal = q.P(M["tail_belly"])
        cr.new_path()
        core.tapered(cr, under, 5.5, 1.5)
        core.src(cr, core.mix(bpal.shadow, bpal.lit, 0.35))
        cr.fill()
        if q.detail >= 2:
            sc = []
            for i in range(2, ns - 3, 2):
                p0, p1 = sp[i], sp[i + 1]
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                L = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / L, dx / L
                r = (radii[0] + (radii[-1] - radii[0]) * i / (ns - 1)) * 0.45
                sc.append([(p0[0] - nx * r, p0[1] - ny * r), (p0[0] + dx / L * 2.0, p0[1] + dy / L * 2.0),
                           (p0[0] + nx * r, p0[1] + ny * r)])
            B.detail_lines(cr, sc, q.lw * 0.5, tp and q.P(M["dragon"]).line, 0.35)
        cr.restore()
    # the tuft: rooster feathers fanned at the tip, flicking
    tip, prev = out[-1], sp[-3]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    flick = 0.25 * S["dip_lag"] + 0.12 * math.sin(t * 2.9 + pose.seed)
    for k, (da, L, w, mat) in enumerate(((-0.75, 10.0, 4.0, "plumage_dk"), (-0.35, 13.0, 4.6, "plumage"),
                                         (0.05, 15.0, 5.0, "cream"), (0.45, 13.0, 4.6, "plumage"),
                                         (0.85, 10.0, 4.0, "head"))):
        ang = a + da + flick * (1.0 + 0.3 * k) + 0.06 * math.sin(t * 4.3 + k)
        dx, dy = math.cos(ang), math.sin(ang)
        pts2 = [(tip[0] - dx * 1.0, tip[1] - dy * 1.0), (tip[0] + dx * L * 0.5 - dy * 0.8, tip[1] + dy * L * 0.5 + dx * 0.8),
                (tip[0] + dx * L, tip[1] + dy * L)]
        _ribbon(q, pts2, w, 0.6, M[mat], lw=q.lw * 0.7, flat=True)


# ----------------------------------------------------------------------------------------
# head: the rooster
# ----------------------------------------------------------------------------------------

def _mood(m):
    if isinstance(m, B.Expr):
        return m
    if m in BARD_MOODS:
        return BARD_MOODS[m]
    return B.MOODS.get(m, BARD_MOODS["twinkle"])


def _expr(pose):
    e = _mood(pose.mood)
    if pose.mood2 is not None and pose.mood_mix > 0:
        e = e.blend(_mood(pose.mood2), pose.mood_mix)
    if pose.sing > 0:
        e = e.blend(BARD_MOODS["sing"], clamp(pose.sing * 1.5) * 0.6)
    if pose.rapture > 0:
        e = e.blend(BARD_MOODS["rapture"], clamp(pose.rapture))
    if pose.tune > 0:
        e = e.blend(BARD_MOODS["listen"], clamp(pose.tune))
    if pose.smile is not None:
        e = e.with_(smile=pose.smile)
    return e


COMB_LOBES = ((14.2, 6.0, 2.6), (9.8, 9.2, 3.0), (5.0, 10.4, 3.2), (0.2, 9.0, 2.9), (-4.2, 6.2, 2.5))
COMB_ZC = 5.0          # the comb's middle (head-space z): the camera-facing cheat turns it about here
COMB_CHEAT = 0.6       # 0 = physically correct (edge-on from the front) .. 1 = always seen side-on
PLUME_SPREAD = 0.85    # the plume's sweep always turns at least this far (rad) from edge-on


def _comb_outline():
    """The comb blade in its own plane: (z along the head, h above the skull)."""
    pts = [(17.4, -3.0), (17.6, 1.5)]
    for i, (z, h, r) in enumerate(COMB_LOBES):
        for k in range(5):
            a = math.pi * (0.08 + 0.84 * k / 4)
            pts.append((z + math.cos(a) * r, h + math.sin(a) * r * 0.92))
        if i + 1 < len(COMB_LOBES):
            z2, h2, _r2 = COMB_LOBES[i + 1]
            pts.append(((z + z2) / 2.0, min(h, h2) - 3.6))
    pts += [(-7.0, 2.6), (-6.8, -3.0)]
    return pts


_COMB = _comb_outline()


def _skull_top(z):
    zc = clamp(z, -20.0, 20.0)
    return -HR[1] * math.sqrt(max(0.06, 1.0 - (zc / (HR[2] + 1.5)) ** 2)) + 1.6


def _beret_tf(q):
    lift = clamp(q.pose.cap_lift)
    Rb = m_mul(m_rot_x(0.55 + 0.35 * lift), m_rot_z(-0.16))     # front edge tipped UP: worn on the back
    c = v_add((1.0, -15.5, -13.5), (0.0, -10.0 * lift, 4.0 * lift))
    return lambda v: v_add(c, m_vec(Rb, v)), Rb


def _head(q):
    cr, proj, M, S, pose, t = q.cr, q.proj, q.M, q.S, q.pose, q.t
    RH, HC = S["RH"], S["head_c"]
    e = _expr(pose)
    lw = q.lw
    hyaw = q.yaw + S["head_yaw"]
    near = -1.0 if hyaw >= 0 else 1.0
    far = -near
    xy = proj.xy

    def P(v):
        w = m_vec(RH, v)
        return xy((HC[0] + w[0], HC[1] + w[1], HC[2] + w[2]))

    def nz(v):
        w = m_vec(RH, v)
        return -w[0] * proj.s + w[2] * proj.c

    sing = clamp(max(pose.sing, pose.talk * 0.85))
    vowel = (pose.vowel or "a").lower()[:1]
    open_ = clamp(max(sing, e.open))
    if vowel == "o":
        open_ *= 0.8
    elif vowel in ("e", "i"):
        open_ *= 0.55
    elif vowel == "m":
        open_ *= 0.08
    bt, Rb = _beret_tf(q)
    plume_near = nz(m_vec(Rb, (1.0, 0.0, 0.0))) > 0.0
    plume_tip = None
    if pose.cap and not plume_near:
        plume_tip = _plume(q, P, nz, bt)
    top = P((0.0, -HR[1] - 14.0, 3.0))
    if pose.cap:
        # the felt dome sits on the back of his head: drawn BEFORE the skull, so the head hides
        # whatever of it is behind; the band that wraps round the head is drawn over it later
        top = _beret(q, P, nz, bt, Rb, "dome")

    # ---- skull + cheeks + neck stub: one form
    skull = core.convex_hull(B.ellipsoid_pts(P, (0.0, 0.0, -1.0), HR[0], HR[1], HR[2], 9))
    stub = core.convex_hull(B.ellipsoid_pts(P, (0.0, 17.0, -4.0), 12.5, 8.0, 11.0, 6))
    ck = 1.0 + 0.1 * e.cheek
    cheeks = [(P((s * 12.0, 7.0, 8.0)), 9.6 * ck) for s in (-1.0, 1.0) if nz((s * 0.7, 0.2, 0.6)) > -0.4]
    hp = _union(q, [skull, stub], M["head"], size=42, shadow=0.85, circles=cheeks)
    hpal = q.P(M["head"])
    # the lighter golden face round the eyes and down the cheeks (a soft mask, not a disc)
    mask3 = []
    for s in (-1.0, 1.0):
        mask3 += [(s * 5.5, -12.5, 18.0), (s * 14.5, -12.0, 12.5), (s * 19.5, -4.0, 7.0), (s * 18.0, 7.0, 6.5),
                  (s * 12.5, 13.5, 10.5), (s * 5.0, 12.0, 15.5)]
    mask3 += [(0.0, -10.5, 20.5), (0.0, 11.0, 17.5)]
    mpts = [P(v) for v in mask3 if nz(v) > -2.0]
    cr.save()
    hp.add(cr)
    cr.clip()
    if len(mpts) >= 3:
        mh = core.convex_hull(mpts)
        cr.new_path()
        core.smooth_closed(cr, mh, 0.9)
        q.shade(Path(cr), M["face"], outline=False, size=30, shadow=0.8, rim=0.4)
        if q.detail >= 1:
            # a feathered edge where the face meets the chestnut crown
            ticks = []
            for (x_, y_, z_) in ((-10.0, -13.0, 15.5), (-15.5, -9.0, 11.5), (10.0, -13.0, 15.5), (15.5, -9.0, 11.5),
                                 (-19.0, 2.0, 6.0), (19.0, 2.0, 6.0), (-4.5, -13.2, 18.0), (4.5, -13.2, 18.0)):
                if nz((x_, y_, z_)) < 3.0:
                    continue
                a0 = P((x_, y_, z_))
                a1 = P((x_ * 1.04, y_ + 3.0, z_ + 1.0))
                ticks.append([a0, a1])
            B.detail_lines(cr, ticks, lw * 0.9, hpal.lit, 0.95, taper=(1.0, 0.7, 0.1))
    if q.detail >= 1:
        # a few feather marks on the crown and the back of the head
        marks = []
        for (x_, y_, z_) in ((-9.0, -17.0, 6.0), (9.0, -17.0, 6.0), (0.0, -19.5, -6.0), (-15.0, -10.0, -8.0),
                             (15.0, -10.0, -8.0), (-17.0, 3.0, -9.0), (17.0, 3.0, -9.0), (0.0, -10.0, -18.0)):
            if nz((x_, y_, z_)) < 4.0:
                continue
            c0 = P((x_, y_, z_))
            marks.append([(c0[0] - 2.6, c0[1] - 1.2), (c0[0], c0[1] + 1.6), (c0[0] + 2.6, c0[1] - 1.2)])
        B.detail_lines(cr, marks, lw * 0.6, hpal.line, 0.4)
    cr.restore()

    # ---- eyes (the shared eye: big, bright, clever)
    blink = B.auto_blink(t, pose.seed + 23) if pose.blink is None else pose.blink
    wink = clamp(pose.wink)
    look = (lerp(pose.look[0], 0.0, clamp(pose.look_cam)), lerp(pose.look[1], 0.0, clamp(pose.look_cam)))
    eyes = []
    for s in (far, near):
        ec = P((s * 11.8, -4.2, 15.6))
        eyes.append(ec)
        fz = nz((s * 0.6, -0.15, 0.78))
        if fz < 0.05:
            continue
        fore = clamp(0.3 + fz * 0.85, 0.3, 1.0)
        op = P((s * 18.0, -3.6, 10.5))
        outer = 1.0 if op[0] > ec[0] else -1.0
        ang = math.atan2((op[1] - ec[1]) * outer, (op[0] - ec[0]) * outer)
        bl, sq = blink, 0.0
        lid, lidb = e.lid, e.lid_bot
        if wink > 0:
            if s == near:
                bl, sq = max(bl, smooth(wink / 0.7)), 1.0
            else:
                lid = lerp(lid, 0.04, wink)
        if e.lid >= 0.97:
            sq = 0.0
        B.eye(cr, ec[0], ec[1], 6.6 * fore, 8.0, q.light, lw * 0.85, angle=ang * 0.6,
              look=(look[0] * outer, look[1]), lid=lid, lid_bot=lidb, tilt=e.lid_tilt, outer=outer, blink=bl,
              squint_arc=sq, iris=BARD_COLORS["eye"], iris_hi=BARD_COLORS["eye_hi"], pupil="#1d120c",
              pupil_size=0.5 * e.pupil, skin=BARD_COLORS["face"], crease=0.3, bags=0.0, iris_size=0.72,
              line=q.P(M["brow"]).line, lid_shade=0.12, lash=0.95, lash_flick=0.35)
    cr.save()
    hp.add(cr)
    cr.clip()
    _brows(q, P, nz, e, near, wink)
    cr.restore()

    # ---- wattles (behind the beak), then the beak (opens to sing)
    a_low = open_ * 0.62
    _wattles(q, P, nz, open_, a_low, near)
    mouth, beak_tip, a_low = _beak(q, P, nz, e, open_, near)

    # ---- the beret's band round the head, the comb flopping in front of it, the plume
    if pose.cap:
        _beret(q, P, nz, bt, Rb, "band")
    comb_top = _comb(q, P, nz)
    if not pose.cap:
        top = comb_top
    if pose.cap and plume_near:
        plume_tip = _plume(q, P, nz, bt)
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mouth, "beak": beak_tip, "eyes": eyes, "top": top,
            "comb": comb_top, "plume": plume_tip or top}


def _brows(q, P, nz, e, near, wink):
    """Expressive feather brows (chestnut tufts with a flick at the outer end)."""
    cr, M = q.cr, q.M
    pal = q.P(M["brow"])
    lwb = q.lw * 0.8
    for s in (-1.0, 1.0):
        if nz((s * 0.5, -0.5, 0.7)) < -0.05:
            continue
        asym = e.brow_asym * (1.0 if s == near else -0.4)
        wk = wink * (-0.55 if s == near else 0.75)
        li = (e.brow_in * 0.6 + e.brow_y + asym + wk) * 5.5
        lo = (e.brow_out * 0.5 + e.brow_y + asym + wk) * 5.0
        pts = [P((s * 4.6, -16.0 - li, 18.4)), P((s * 11.2, -17.6 - (li + lo) * 0.5, 16.0)), P((s * 17.0, -14.0 - lo, 11.2))]
        flick = P((s * 19.4, -15.0 - lo * 1.15, 8.6))

        def prof(u):
            return 4.4 * (0.55 + 0.45 * math.sin(math.pi * min(1.0, u * 1.15))) * (1.0 - 0.35 * u)

        sh, so = B.taper_paths(cr, pts, 4.0, 1.8, lwb, profile=prof)
        q.shade(sh, M["brow"], lw=lwb, outline=so, size=4, rim=0.6)
        B.detail_lines(cr, [[pts[-1], flick]], q.lw * 1.2, pal.lit, 1.0, taper=(1.0, 0.8, 0.1))


BEAK_HINGE = (0.0, 8.0, 14.0)


def _brot(v, a):
    """Rotate a head-space point about the beak's hinge axis (X through BEAK_HINGE); + opens."""
    hy, hz = BEAK_HINGE[1], BEAK_HINGE[2]
    y, z = v[1] - hy, v[2] - hz
    c, s = math.cos(a), math.sin(a)
    return (v[0], hy + y * c + z * s, hz - y * s + z * c)


def _beak(q, P, nz, e, open_, near):
    """A short, stout, slightly hooked rooster beak; the lower mandible drops to sing."""
    cr, M = q.cr, q.M
    lw = q.lw * 0.85
    a_low = open_ * 0.62
    a_up = -open_ * 0.07
    up3 = [(math.cos(TAU * i / 12) * 7.0, 3.8 + math.sin(TAU * i / 12) * 4.5, 16.5) for i in range(12)]
    up3 += [(0.0, 0.6, 23.5), (-4.1, 5.0, 23.5), (4.1, 5.0, 23.5), (0.0, 8.0, 25.0), (0.0, 11.0, 33.0),
            (0.0, 12.8, 31.0), (-2.1, 8.6, 29.8), (2.1, 8.6, 29.8), (0.0, 4.0, 29.5)]
    lo3 = [(math.cos(TAU * i / 10) * 6.0, 9.6 + math.sin(TAU * i / 10) * 2.4, 15.5) for i in range(10)]
    lo3 += [(-3.4, 10.8, 22.5), (3.4, 10.8, 22.5), (0.0, 12.0, 29.0), (0.0, 10.2, 27.0)]
    up = core.convex_hull([P(_brot(v, a_up)) for v in up3])
    lo = core.convex_hull([P(_brot(v, a_low)) for v in lo3])
    bp = q.P(M["beak"])
    _union(q, [lo], M["beak"], size=6, lw=lw, rim=0.5, tension=0.8)
    if open_ > 0.04:
        in3 = [(-6.8, 8.2, 14.5), (6.8, 8.2, 14.5)]
        in3 += [_brot(v, a_up) for v in ((-3.8, 8.6, 22.5), (3.8, 8.6, 22.5), (0.0, 9.6, 29.5))]
        in3 += [_brot(v, a_low) for v in ((-3.2, 9.8, 21.5), (3.2, 9.8, 21.5), (0.0, 10.6, 26.5))]
        ih = core.convex_hull([P(v) for v in in3])
        _flat(q, ih, M["mouth"], lw=lw, tension=0.8)
        cr.save()
        cr.new_path()
        core.smooth_closed(cr, _pos(ih), 0.8)
        cr.clip()
        tg = P(_brot((0.0, 10.4, 21.0), a_low * 0.85))
        core.src(cr, q.P(M["tongue"]).lit)
        core.ellipse(cr, tg[0], tg[1], 3.8, 2.0)
        cr.fill()
        cr.restore()
    _union(q, [up], M["beak"], size=10, lw=lw, rim=0.8, tension=0.8)
    # a dab of shine on the culmen, the nostrils, the gape line and the smile curls
    sx_, sy_ = P(_brot((0.0, 2.4, 24.5), a_up))
    B.sheen(cr, sx_, sy_, 2.6, 1.5, alpha=0.55)
    lines = []
    side_on = abs(math.sin(q.yaw + q.S["head_yaw"]))
    for s in ((near,) if side_on > 0.35 else ()):
        n0 = P(_brot((s * 2.7, 3.0, 21.0), a_up))
        n1 = P(_brot((s * 3.2, 3.6, 23.6), a_up))
        lines.append([n0, n1])
    if lines:
        B.detail_lines(cr, lines, q.lw * 0.9, bp.line, 0.85, taper=(1.0, 0.8, 0.3))
    sm = e.smile
    curls = []
    for s in (near, -near):
        if nz((s * 0.8, 0.3, 0.5)) < -0.1:
            continue
        g0 = P((s * 7.0, 8.2, 14.4))
        if open_ < 0.05 and (s == near and side_on > 0.3):
            curls.append([g0, P(_brot((s * 3.8, 9.6, 23.0), a_low)), P(_brot((0.0, 10.8, 30.5), a_low))])
        if sm > 0.2:
            curls.append([P((s * 6.4, 8.8, 15.0)), g0, P((s * 9.0, 8.2 - 3.6 * sm, 11.6))])
    if curls:
        B.detail_lines(cr, curls, q.lw * 0.9, bp.line, 0.85, taper=(0.4, 1.0, 0.2))
    mouth = P(_brot((0.0, 9.6, 24.0), a_low * 0.5))
    tip = P(_brot((0.0, 11.0, 33.0), a_up))
    return mouth, tip, a_low


def _wattles(q, P, nz, open_, a_low, near):
    """Two red wattles hanging under the lower mandible, swinging a beat late (and jiggling
    when he sings). Drawn before the beak, which overlaps their tops."""
    t, S = q.t, q.S
    for s in (-near, near):
        if s == -near and nz((s * 0.6, 0.6, 0.4)) < -0.5:
            continue
        anc = _brot((s * 2.6, 12.2, 15.0), a_low * 0.8)
        sw = (0.1 * math.sin(t * 2.0 + s) + 0.22 * open_ * math.sin(t * 15.0 + s) + 0.18 * S["dip_lag"]
              - 0.3 * S["head_roll"])
        bot = (anc[0] + s * 0.9 + math.sin(sw) * 2.0, anc[1] + math.cos(sw) * 7.6, anc[2] - 1.2 - math.sin(sw) * 5.0)
        a2, b2 = P(anc), P(bot)
        h = core.convex_hull(_circ(a2, 2.5, 10) + _circ(b2, 3.7, 12))
        _union(q, [h], q.M["comb"], size=7, rim=0.6)


def _comb(q, P, nz):
    """The floppy red comb: five rounded lobes from the base of the beak back over the crown,
    flopped over to his right (more toward the tips), flopping a beat behind the head bob."""
    cr, S, pose, t = q.cr, q.S, q.pose, q.t
    flop = (0.30 + 0.10 * B.sway(t, 0.45, pose.seed + 13) + 0.22 * S["dip_lag"] + 0.5 * S["head_roll"]
            - 0.25 * clamp(pose.cap_lift))
    # cartoon cheat: a comb is a thin blade -- turn it toward the camera so its lobes always read
    hy = q.yaw + S["head_yaw"]
    sg = 1.0 if hy >= 0.0 else -1.0
    gam = sg * COMB_CHEAT * max(0.0, math.pi / 2 - abs(hy))
    cg, sgm = math.cos(gam), math.sin(gam)

    def C3(z, h):
        hh = max(h, -3.0)
        rho = flop * (0.35 + 0.65 * clamp(hh / 10.0)) if hh > 0 else 0.0
        x0, y0, z0 = -math.sin(rho) * hh, _skull_top(z) - math.cos(rho) * hh, z - COMB_ZC
        return (x0 * cg + z0 * sgm, y0, COMB_ZC - x0 * sgm + z0 * cg)

    pts = [P(C3(z, h)) for (z, h) in _COMB]
    sh, so = B.smooth_paths(cr, pts, q.lw, 0.85)
    pal = q.shade(sh, q.M["comb"], outline=so, size=10, rim=0.9)
    if q.detail >= 1:
        cr.save()
        sh.add(cr)
        cr.clip()
        lines = []
        for i in range(len(COMB_LOBES) - 1):
            z, h, _r = COMB_LOBES[i]
            z2, h2, _ = COMB_LOBES[i + 1]
            zm, hm = (z + z2) / 2.0, min(h, h2) - 3.6
            lines.append([P(C3(zm, hm)), P(C3(zm + 0.4, hm * 0.45))])
        B.detail_lines(cr, lines, q.lw * 0.7, pal.line, 0.55)
        cr.restore()
    z, h, _r = COMB_LOBES[2]
    return P(C3(z, h + 3.0))


def _beret(q, P, nz, bt, Rb, part="dome"):
    """The soft felt beret, worn well back on his head and tipped to his left; a gold band.
    part "dome": the felt (drawn before the skull); "band": the gold band (after it)."""
    cr, M = q.cr, q.M

    def PB(v):
        return P(bt(v))

    if part == "band":
        _beret_band(q, PB, nz, Rb)
        return PB((0.0, -12.0, 0.0))
    pts = B.ellipsoid_pts(PB, (0.0, -3.0, 0.0), 18.8, 6.4, 17.0, 10)
    pts += [PB((math.sin(TAU * i / 14) * 16.0, 3.0, math.cos(TAU * i / 14) * 14.8)) for i in range(14)]
    hull = core.convex_hull(pts)
    nub = core.convex_hull(B.ellipsoid_pts(PB, (0.0, -10.0, 0.0), 2.3, 2.3, 2.3, 4))
    bp = _union(q, [hull, nub], M["beret"], size=22, shadow=0.85, rim=0.9)
    if q.detail >= 1:
        cr.save()
        bp.add(cr)
        cr.clip()
        pal = q.P(M["beret"])
        folds = [[PB((-13.0, -5.0, 7.0)), PB((-4.0, -9.0, 9.0)), PB((7.0, -7.5, 11.0))],
                 [PB((6.0, -8.5, -9.0)), PB((13.0, -5.5, -2.0))]]
        B.detail_lines(cr, folds, q.lw * 0.8, pal.line, 0.4, taper=(0.1, 1.0, 0.1))
        cr.restore()
    return PB((0.0, -12.0, 0.0))


def _beret_band(q, PB, nz, Rb):
    M = q.M
    run, best = [], []
    for i in range(33):
        a = -math.pi + TAU * i / 32
        n = m_vec(Rb, (math.sin(a), 0.0, math.cos(a)))
        if nz(n) > -0.05:
            run.append(PB((math.sin(a) * 16.4, 3.3, math.cos(a) * 15.2)))
        else:
            if len(run) > len(best):
                best = run
            run = []
    if len(run) > len(best):
        best = run
    if len(best) >= 2:
        _ribbon(q, best, 3.4, 3.4, M["gold"], lw=q.lw * 0.6, size=4, rim=0.7, cap=False)
    return PB((0.0, -12.0, 0.0))


def _plume(q, P, nz, bt):
    """The long white plume pinned to the beret's left side with a gold brooch: it sweeps up
    and back and droops at the tip (an ostrich plume with a ruffled edge), swaying, and
    following the beat a little late."""
    cr, M, S, pose, t = q.cr, q.M, q.S, q.pose, q.t
    base = bt((17.0, 1.0, 4.0))
    sw = B.chain(t, 8, freq=0.32, delay=0.13, amp=0.6, seed=pose.seed + 31, grow=3.0)
    offs = [(0.0, 0.0, 0.0), (2.0, -7.5, -5.0), (4.0, -15.0, -12.0), (6.0, -21.0, -22.0), (7.0, -24.0, -34.0),
            (7.0, -23.0, -47.0), (5.5, -18.5, -58.0), (3.5, -12.0, -66.0)]
    # cartoon cheat (like the comb): the plume sweeps straight back, which is edge-on -- a white
    # stick -- whenever he faces the camera. Turn the sweep about the head's vertical so it always
    # shows at least PLUME_SPREAD side-on, trailing away from the way his face is turned.
    hy = q.yaw + S["head_yaw"]
    sgn = (1.0 if hy >= 0.0 else -1.0) if abs(hy) > 1e-3 else (1.0 if q.yaw >= 0.0 else -1.0)
    g = sgn * max(0.0, PLUME_SPREAD - abs(hy))
    cg, sg_ = math.cos(g), math.sin(g)
    offs = [(o[0] * cg + o[2] * sg_, o[1], -o[0] * sg_ + o[2] * cg) for o in offs]
    pts3 = []
    acc = 0.0
    n = len(offs)
    for i, o in enumerate(offs):
        u = i / (n - 1)
        acc += sw[i]
        pts3.append((base[0] + o[0] + acc * 18.0 * u, base[1] + o[1] + acc * 6.0 * u + S["dip_lag"] * 5.0 * u * u,
                     base[2] + o[2]))
    pts = [P(p) for p in pts3]

    def prof(u):
        return (13.0 * math.sin(math.pi * min(1.0, 0.05 + u * 0.97)) ** 0.55 * (1.0 - 0.25 * u)
                * (1.0 + 0.10 * math.sin(u * 26.0)) + 0.8)

    lwp = q.lw * 0.8
    sh, so = B.taper_paths(cr, pts, 1.0, 1.0, lwp, profile=prof)
    pal = q.shade(sh, M["plume"], lw=lwp, outline=so, size=9, rim=0.8, shadow=0.7)
    if q.detail >= 1:
        sp = core.spline(pts, n=4)
        barbs = []
        m = len(sp)
        for i in range(1, m - 1):
            p0, p1 = sp[i - 1], sp[i + 1]
            tx, ty = core.normalize((p1[0] - p0[0], p1[1] - p0[1]))
            nx, ny = -ty, tx
            w = prof(i / (m - 1)) * 0.5
            c0 = sp[i]
            for sg in (-1.0, 1.0):
                barbs.append([(c0[0] + nx * w * 0.15 * sg, c0[1] + ny * w * 0.15 * sg),
                              (c0[0] + nx * w * 0.85 * sg - tx * 3.5, c0[1] + ny * w * 0.85 * sg - ty * 3.5)])
        B.detail_lines(cr, barbs, q.lw * 0.55, pal.line, 0.38, taper=(0.3, 1.0, 0.1))
        B.detail_lines(cr, [sp], q.lw * 0.6, pal.line, 0.55, taper=(1.0, 0.8, 0.1))
    b2 = P(base)
    _flat(q, _circ(b2, 3.4, 10), M["gold"], lw=q.lw * 0.6)
    _flat(q, _circ(b2, 1.7, 8), M["jewel"], lw=q.lw * 0.3)
    B.sheen(cr, b2[0] - 0.6, b2[1] - 0.8, 1.0, 0.8, alpha=0.9)
    return pts[-1]


# ----------------------------------------------------------------------------------------
# the rig
# ----------------------------------------------------------------------------------------

def draw_bard(cr, x, y, scale=1.0, pose=None, light=None, t=0.0, detail=None):
    """Draw the bard with his anchor at (x, y) (see module doc). Returns a BardRig.
    t drives the idle life (breathing, blinks, comb, wattles, plume, ribbon, tail tuft)."""
    pose = pose or BardPose()
    light = light or B.LIGHTS["neutral"]
    q = _Q()
    q.cr, q.M, q.light, q.t, q.pose, q.pal = cr, bard_mats(), light, t, pose, {}
    yaw = _yaw_of(pose.facing, pose.turn)
    q.yaw = yaw
    proj = Proj(yaw, pose.elev)
    q.proj = proj
    sit = clamp(pose.sit)
    q.sit = sit
    seat_h = pose.seat_h
    dev = scale * B.device_scale(cr)
    if detail is None:
        detail = 2 if dev >= 0.9 else 1 if dev >= 0.55 else 0
    q.detail = detail
    q.micro = detail >= 2 and dev >= 1.4
    q.lw = B.line_for(BARD_LINE, dev)

    cr.save()
    cr.translate(x, y + (seat_h * scale * sit if pose.anchor == "seat" else 0.0))
    cr.scale(scale, scale)
    S = _skeleton(pose, t, sit, seat_h, yaw)
    q.S = S
    q.st = _strum_state(pose)
    q.F = _lute_frame(q) if pose.lute in ("play", "back") else None
    q.vib = _lute_vib(q) if pose.lute == "play" else None
    rig = BardRig(scale=scale, facing=1.0 if yaw >= 0 else -1.0, yaw=yaw)

    if pose.shadow:
        fa = [proj.xy(f["ankle"]) for f in S["feet"]]
        cxs = (fa[0][0] + fa[1][0]) / 2.0
        k = smooth(sit)
        B.contact_shadow(cr, lerp(cxs, cxs * 0.5, k), 1.5, lerp(40.0, 44.0, k), lerp(8.5, 9.5, k),
                         alpha=lerp(0.34, 0.28, k))

    A = {s: _solve_arm(q, s, pose.right if s < 0 else pose.left) for s in (-1.0, 1.0)}
    near_side = -1.0 if yaw >= 0 else 1.0
    far_side = -near_side
    seated = sit >= SIT_SWAP
    playing = pose.lute == "play"

    # ---------------- back to front
    if pose.lute == "back":
        _lute(q, q.F)
    _tail(q)
    _wing(q, far_side)
    _wing(q, near_side)
    for s in (far_side,):
        if A[s]["layer"] == "auto" and abs(yaw) > 0.38:
            A[s]["done"] = True
            _arm(q, A[s])
    if not seated:
        for f in sorted(S["feet"], key=lambda f: proj.depth(f["ankle"])):
            _leg(q, f)
    _torso(q)
    if seated:
        for f in sorted(S["feet"], key=lambda f: proj.depth(f["ankle"])):
            _leg(q, f)
    if pose.lute == "back":
        _strap(q)
    _ruff(q)
    # arms not on the lute that hang at the sides / rest in the lap
    for s in (far_side, near_side):
        if not A[s].get("done") and A[s]["layer"] == "auto":
            A[s]["done"] = True
            hf = _arm(q, A[s])
            if s == near_side:
                rig.hand_near = hf
            else:
                rig.hand_far = hf
            if s < 0:
                rig.hand_right = hf
            else:
                rig.hand_left = hf
    head = _head(q)
    if playing:
        fret_s, strum_s = 1.0, -1.0
        if A[fret_s]["layer"] == "lute":
            _arm(q, A[fret_s], parts="sleeve")
        rig.lute = _lute(q, q.F)
        for s in (fret_s, strum_s):
            if A[s].get("done"):
                continue
            A[s]["done"] = True
            if A[s]["layer"] == "lute" and s == fret_s:
                hf = _arm(q, A[s], parts="hand")
            else:
                hf = _arm(q, A[s])
            if s < 0:
                rig.hand_right = hf
            else:
                rig.hand_left = hf
    for s in (far_side, near_side):
        if not A[s].get("done"):
            A[s]["done"] = True
            hf = _arm(q, A[s])
            if s < 0:
                rig.hand_right = hf
            else:
                rig.hand_left = hf
    rig.hand_near = rig.hand_right if near_side < 0 else rig.hand_left
    rig.hand_far = rig.hand_left if near_side < 0 else rig.hand_right
    if pose.lute == "back":
        rig.lute = {}

    # ---------------- attach points -> caller coordinates
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()

    def C(p):
        dx, dy = m.transform_point(p[0], p[1])
        return inv.transform_point(dx, dy)

    rig.head = C(head["center"])
    rig.mouth = C(head["mouth"])
    rig.beak = C(head["beak"])
    rig.eyes = [C(e) for e in head["eyes"]]
    rig.top = C(head["top"])
    rig.comb = C(head["comb"])
    rig.plume_tip = C(head["plume"])
    rig.chest = C(proj.xy(S["chest"]))
    rig.lap = C(proj.xy(v_lerp(S["knee"][-1.0], S["knee"][1.0], 0.5)))
    rig.feet = [C(proj.xy(f["ankle"])) for f in S["feet"]]
    rig.seat = C((0.0, -seat_h * sit))
    rig.lute = {k: C(v) for k, v in (rig.lute or {}).items()}
    for hf in (rig.hand_right, rig.hand_left):
        if hf is not None:
            hf.x, hf.y = C((hf.x, hf.y))
            hf.tips = [C(tp) for tp in hf.tips]
            hf.palm = C(hf.palm)
            hf.scale *= scale
    return rig


# ----------------------------------------------------------------------------------------
# his little stool
# ----------------------------------------------------------------------------------------

def draw_bard_stool(cr, x, y, scale=1.0, light=None, seat_h=BARD_STOOL_H, yaw=0.0, detail=None):
    """A little three-legged milking stool built to his seat height; (x, y) = the ground point
    below the seat centre (the same anchor as the bard). Draw it BEFORE the bard. Returns the
    seat point in caller coordinates."""
    light = light or BARD_LIGHTS["candle"]
    wood = Mat.of("#A0703F", sheen=0.3)                # paler than his boots: furniture, not legs
    pal = B.palette(light, wood)
    dev = scale * B.device_scale(cr)
    lw = B.line_for(BARD_LINE, dev)
    proj = Proj(yaw, ELEV)
    cr.save()
    cr.translate(x, y)
    cr.scale(scale, scale)
    B.contact_shadow(cr, 0.0, 1.5, 36.0, 8.5, alpha=0.3)
    legs = []
    for k, a in enumerate((math.pi * 0.5 + 0.3, math.pi * 1.5 - 0.3, -0.25 * math.pi + math.pi * 2)):
        top3 = (math.sin(a) * 14.0, -seat_h + 4.0, math.cos(a) * 12.0)
        foot3 = (math.sin(a) * 23.0, 0.0, math.cos(a) * 21.0)
        legs.append((proj.depth(foot3), proj.xy(top3), proj.xy(foot3)))
    legs.sort()
    for dz, a2, b2 in legs:
        sh, so = B.taper_paths(cr, [a2, b2], 7.0, 5.4, lw * 0.9)
        B.shade(cr, sh, wood, light, lw * 0.9, outline=so, size=6, rim=0.5, bounce=0.0)
    # the round seat slab (top + rim)
    top = [proj.xy((math.sin(TAU * i / 20) * 25.0, -seat_h, math.cos(TAU * i / 20) * 22.0)) for i in range(20)]
    bot = [proj.xy((math.sin(TAU * i / 20) * 25.0, -seat_h + 7.0, math.cos(TAU * i / 20) * 22.0)) for i in range(20)]
    sh, so, _h = B.hull_paths(cr, top + bot, lw)
    B.shade(cr, sh, wood, light, lw, outline=so, size=10, rim=0.7, bounce=0.0)
    cr.new_path()
    core.smooth_closed(cr, core.convex_hull(top), 0.9)
    core.src(cr, core.mix(pal.lit, pal.hi, 0.25))
    cr.fill()
    if detail is None or detail >= 1:
        rings = [[proj.xy((math.sin(TAU * i / 12) * r, -seat_h, math.cos(TAU * i / 12) * r * 0.9)) for i in range(12)]
                 for r in (9.0, 18.0)]
        for rg in rings:
            cr.new_path()
            core.smooth_closed(cr, rg, 0.9)
            cr.set_line_width(lw * 0.45)
            core.src(cr, pal.line, 0.3)
            cr.stroke()
    m = cr.get_matrix()
    cr.restore()
    inv = cr.get_matrix()
    inv.invert()
    dx, dy = m.transform_point(0.0, -seat_h)
    return inv.transform_point(dx, dy)


# ----------------------------------------------------------------------------------------
# character sheet (python3 film/render.py --sheet --only bard)
# ----------------------------------------------------------------------------------------

def lineup():
    """The bard on the cast height chart (his beret and plume included in the drawing)."""
    return [B.LineupItem("bard", lambda cr, x, y, sc: draw_bard(cr, x, y, sc, BardPose(facing=1, turn=-0.4, lute="none"),
                                                                 t=0.4), 120.0)]


def _head_frame(pose, scale, light, t=0.4):
    s, c = core.frame(4, 4)
    rig = draw_bard(c, 0.0, 0.0, scale, pose, light, t=t)
    return rig.head


def _bench(cr, x, ground, sc, seat_h, w=220.0, light=None):
    light = light or B.LIGHTS["neutral"]
    oak = Mat.of("#7a5232", sheen=0.2)
    pal = B.palette(light, oak)
    core.src(cr, pal.shadow)
    for lx in (x - w * 0.4, x + w * 0.4):
        cr.rectangle(lx - 5 * sc, ground - seat_h * sc, 10 * sc, seat_h * sc)
    cr.fill()
    core.src(cr, pal.lit)
    core.rounded_rect(cr, x - w / 2, ground - seat_h * sc - 8 * sc, w, 11 * sc, 3 * sc)
    cr.fill()


def sheet_items():
    """Character sheet cells for render.py --sheet (see API.md: sheet convention)."""
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]
    candle = BARD_LIGHTS["candle"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    # ---- turnaround (scale 2: he is small; standing, lute in playing position)
    for label, pose in (("3/4 left", BardPose(facing=-1, turn=0.3)), ("front", BardPose(facing=0, turn=0.0)),
                        ("3/4 right (default)", BardPose()), ("near profile", BardPose(facing=1, turn=0.6)),
                        ("lute on his back", BardPose(facing=0, turn=0.35, lute="back", left=BardArm("rest"),
                                                      right=BardArm("rest"))),
                        ("presenting the tale", BardPose(facing=0, turn=0.5, lute="back", right=BardArm("present"),
                                                         left=BardArm("rest"), mood="sly"))):
        def fn(cr, p=pose):
            B.sheet_bg(cr, 290, 600, floor=540)
            draw_bard(cr, 150, 556, 2.4, p, neutral, t=0.4)
        add(label, 290, 600, fn, "turnaround & walk")
    for ph in (0.0, 0.25, 0.5, 0.75):
        def fn(cr, ph=ph):
            B.sheet_bg(cr, 210, 380, floor=340)
            draw_bard(cr, 100, 352, 1.6, BardPose(facing=1, turn=0.0, walk=1.0, phase=ph, lute="back",
                                                  left=BardArm("rest"), right=BardArm("rest")), neutral, t=ph)
        add(f"strut {ph:.2f} (head thrust)", 210, 380, fn, "turnaround & walk")
    # ---- playing on his stool (candlelight)
    play = [
        ("strum: wind-up", dict(strum_t=0.30, strum_next=0.05, strum_dir=-1, strum_next_dir=1)),
        ("strum: DOWN through", dict(strum_t=0.035, strum_next=0.4, strum_dir=1, strum_next_dir=-1)),
        ("down: follow-through", dict(strum_t=0.16, strum_next=0.3, strum_dir=1, strum_next_dir=-1)),
        ("strum: UP through", dict(strum_t=0.035, strum_next=0.4, strum_dir=-1, strum_next_dir=1)),
        ("chord 0 (strings ringing)", dict(chord=0.0, strum_t=0.12, strum_next=0.5)),
        ("chord 1", dict(chord=1.0)), ("chord 2", dict(chord=2.0)), ("chord 3", dict(chord=3.0)),
        ("tuning (intro)", dict(tune=1.0, tune_phase=0.25, strum_t=0.1, strum_next=0.8)),
        ("singing, beak open", dict(sing=0.9, strum_t=0.1, strum_next=0.3, beat=4.0, groove=1.0)),
        ("long note: rapture", dict(sing=0.75, rapture=1.0, vowel="o")),
        ("wink to camera", dict(wink=1.0, look_cam=1.0, mood="sly")),
        ("look to camera", dict(look_cam=1.0)),
        ("beat bob + foot tap (off-beat)", dict(beat=4.8, groove=1.0, sing=0.3)),
    ]
    stage = dict(sit=1.0, facing=1, turn=-0.45, tail_swing=-0.5)      # the prologue's 3/4 staging
    for label, kw in play:
        def fn(cr, kw=kw):
            B.sheet_bg(cr, 290, 420, "neutral", floor=380)
            p = BardPose(**stage, **kw)
            draw_bard_stool(cr, 150, 392, 2.0, candle, yaw=bard_yaw(p))
            draw_bard(cr, 150, 392, 2.0, p, candle, t=0.4)
        add(label, 290, 420, fn, "playing (candlelight, on his stool)")
    for label, tt in (("bard_song(0.9): tuning (intro)", 0.9), ("bard_song(5.9): '...a TIME'", 5.9),
                      ("bard_song(14.3): 'the RAIN' (long note)", 14.3), ("bard_song(40.9): '...back to BREAD'", 40.9)):
        def fn(cr, tt=tt):
            B.sheet_bg(cr, 290, 420, "neutral", floor=380)
            p = BardPose(look_cam=0.5, **stage, **bard_song(tt))
            draw_bard_stool(cr, 150, 392, 2.0, candle, yaw=bard_yaw(p))
            draw_bard(cr, 150, 392, 2.0, p, candle, t=tt)
        add(label, 290, 420, fn, "playing (candlelight, on his stool)")
    # ---- faces
    moods = [("twinkle (default)", dict()), ("singing 'a'", dict(sing=1.0)), ("singing 'o'", dict(sing=0.9, vowel="o")),
             ("singing 'e'", dict(sing=0.9, vowel="e")), ("rapture (long note)", dict(sing=0.7, rapture=1.0)),
             ("wink", dict(wink=1.0, mood="sly")), ("sly", dict(mood="sly")), ("listening (tuning)", dict(tune=1.0)),
             ("surprised", dict(mood="surprised")), ("warm laugh", dict(mood="laugh", sing=0.6)),
             ("kind", dict(mood="kind")), ("worried", dict(mood="worried")), ("blink", dict(blink=1.0)),
             ("front: twinkle", dict(facing=0, turn=0.0)), ("front: singing", dict(facing=0, turn=0.0, sing=0.9)),
             ("front: wink", dict(facing=0, turn=0.0, wink=1.0, mood="sly")),
             ("3/4 left: singing", dict(facing=-1, turn=0.35, sing=0.8)), ("profile: singing", dict(facing=1, turn=0.6, sing=0.9))]
    for label, kw in moods:
        kw = dict(kw)
        pose = BardPose(lute="none", **kw)

        def fn(cr, p=pose):
            B.sheet_bg(cr, 230, 230)
            hx, hy = _head_frame(p, 2.9, neutral)
            draw_bard(cr, 115 - hx, 140 - hy, 2.9, p, neutral, t=0.4)
        add(label, 230, 230, fn, "faces")
    # ---- lights + film scale + the S8 cameo on a bench
    for name, lt in (("candle (prologue)", candle), ("neutral", neutral), ("lantern_night (S8)", L["lantern_night"]),
                     ("golden", L["golden"]), ("dusk", L["dusk"])):
        def fn(cr, lt=lt, name=name):
            B.sheet_bg(cr, 230, 400, name.split(" ")[0] if name.split(" ")[0] in B.SHEET_BG else "golden", floor=360)
            p = BardPose(sing=0.4, strum_t=0.1, strum_next=0.4, **stage)
            draw_bard_stool(cr, 120, 372, 1.7, lt, yaw=bard_yaw(p))
            draw_bard(cr, 120, 372, 1.7, p, lt, t=0.4)
        add(name, 230, 400, fn, "lights, scale, cameo")

    def cameo(cr):
        B.sheet_bg(cr, 520, 400, "lantern_night", floor=330)
        sc = 0.9
        _bench(cr, 260, 345, sc, B.BENCH_SEAT_H, w=440, light=L["lantern_night"])
        try:
            from . import dragon as D
            D.draw_dragon(cr, 150, 345, sc, D.DragonPose(facing=0, turn=0.4, sit=1.0, mood="kind", tail_front=True),
                          L["lantern_night"], t=0.4)
        except Exception:
            pass
        draw_bard(cr, 360, 345, sc, bard_cameo_pose(2.3), L["lantern_night"], t=2.3)
    add("S8 cameo: on the bench beside the dragon (scale 0.9)", 520, 400, cameo, "lights, scale, cameo")
    for label, sc in (("600 px tall (scale 3.4)", 600 / BARD_HEIGHT), ("350 px (2.0)", 350 / BARD_HEIGHT),
                      ("200 px (1.14)", 200 / BARD_HEIGHT), ("seated, 0.9 (S8 plane)", 0.9)):
        w = 300 if sc > 2.5 else 200

        def fn(cr, sc=sc, w=w):
            B.sheet_bg(cr, w, 660, floor=620)
            if sc < 1.0:
                _bench(cr, w / 2, 636, sc, B.BENCH_SEAT_H, w=120)
                draw_bard(cr, w / 2, 636, sc, bard_cameo_pose(1.0), neutral, t=1.0)
            else:
                draw_bard(cr, w / 2, 636, sc, BardPose(sing=0.5, strum_t=0.1, strum_next=0.4), neutral, t=0.4)
        add(label, w, 660, fn, "lights, scale, cameo")
    return items
