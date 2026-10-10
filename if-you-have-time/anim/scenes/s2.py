"""S2 -- "The Symphony" (BIBLE section 4 S2, REVISION 2): the heart of the film.

Quill raises his hand, the lounge goes dark, and the music fills the room with light: note motes,
breathing ribbons, memory bubbles, a galaxy forming in the window. Rae stays SEATED on the bench the whole
time -- moved, eyes wet, memories floating past her -- while ordinary ship life carries on: a cadet strolls
through with his coffee, does a double-take, coughs, mutters "Cool music, Quill.", gets a casual nod, waves
to Rae and gets a tiny teary wave back. Grand pause; the BURST; she sets her mug down on the bench and lays
her hand on her chest; one tear and a trembling smile; the cathedral pull-back; sparks fall like snow and a
last mote goes out in front of her face.

Every time is derived from named beats (core.beat / line_start / scene_span) or from the symphony's own
music data (envelopes.json downbeats / beats / onsets). render(canvas, t) is a pure function of t.

Shot list (absolute times only for orientation -- see _shots()); hard cuts only, on beats or on action:
  two        sym_quill_raise -> 1st note        TWO-SHOT: Quill lifts his hand, the lights dim
  rae_med    1st note -> sym_theme1             MEDIUM Rae: each intro note sends a mote from his palm to her
  wide_rib   sym_theme1 -> bar 5                WIDE push: the ribbons wake; the mug lowers to her lap
  rae_cu1    bar 5 -> bar 6                     MEDIUM CLOSE Rae: brows lift, lips part, pupils wide
  mem_med    bar 6 -> beat before bar 9         MEDIUM-WIDE two-shot: six memories rise around her; "...oh"; tears well
  quill_cu   -> bar 9                           CLOSE Quill watching her, ribbon light across his face
  rae_cu2    bar 9 -> sym_cadet_door            MEDIUM CLOSE Rae: welled tears; the sunset memory beside her; a smile
  cad_enter  sym_cadet_door -> beat 37.5        WIDE: the door slides open, the cadet strolls in with his coffee, the
                                                door shuts behind him; the galaxy starts to gather in the window
  cad_notice -> beat 40.9                       MEDIUM two-shot cadet + Rae: double-take, brows up, eyes flick between
                                                the lights and her, a sip; he walks on (cut on his wipe across her)
  cad_cross  -> beat 42.65                      TWO-SHOT wide: he passes in front of her knees, an awkward little cough
  cad_mutter -> (action) 0.55 s into his wave   MEDIUM Quill + cadet: "Cool music, Quill." as he passes in front of
                                                Quill; Quill's casual nod (hand still raised); the cadet glances back
                                                and waves to Rae
  rae_wave   -> beat 47.2                       MEDIUM Rae: a tiny teary wave and a soft nod back
  exit_wide  -> sym_grand_pause                 WIDE push: the galaxy blazing in the crescendo; the cadet walks off right
  pause      sym_grand_pause -> sym_climax      CLOSE Rae: eyes wide and wet, everything holds its breath
  burst      sym_climax -> sym_tear_roll        WIDE: the BURST; seated, small against it all; she sets the mug on the
                                                bench and lays her right hand on her chest (sym_hand_chest)
  tear       sym_tear_roll -> sym_celesta_echo  CLOSE Rae: one tear, a trembling smile; from sym_peak one pull-back to
                                                the cathedral wide; on the final chord a drift in to the two-shot while
                                                the ribbons fall as sparks and Quill lowers his hand
  last       sym_celesta_echo -> end            MEDIUM CLOSE Rae: the last mote drifts down in front of her face and
                                                goes out

S2 -> S3 handoff (BIBLE section 9): Rae seated at x 230, facing +1, turn 0.3, sit 1, right hand on her chest
(ARMS['hand_on_chest']), far hand on her knee (LAP_L), tear tracks; the mug standing on the bench at MUG_SPOT
(330, 960), drawn with R.draw_mug(c, 330, 960, 1.0, 0.0, <flip of the held mug>) AFTER Rae (in front of her
thigh); Quill at x 545 facing -1 turn 0.35 with arm_r = ARMS['rest']; room light 0.25.
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import skia

from anim import char_quill as Q
from anim import char_rae as R
from anim import env, fx
from anim.core import (Camera, Layer, Track, beat, breathe, clamp, ease_in_out, ease_out, glow, lerp, light_filter,
                       line_end, line_start, mouth, music_env, music_onsets, noise1, scene_span, smoothstep)
from anim.rig import ArmPose, Pose
from config import MUSIC_ENV, H, W

# =========================================================================== timing


@lru_cache(maxsize=1)
def _menv() -> dict:
    p = Path(MUSIC_ENV)
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _T():
    s0, s1 = scene_span("s2")
    n = SimpleNamespace(start=s0, end=s1)
    for attr, name in (("raise_", "sym_quill_raise"), ("dim", "sym_lights_dim"), ("music", "sym_music_start"),
                       ("theme", "sym_theme1"), ("mug", "sym_rae_mug_lower"), ("mem", "sym_memories_start"),
                       ("oh", "sym_rae_oh"), ("glis", "sym_eyes_glisten"), ("build", "sym_build"),
                       ("cdoor", "sym_cadet_door"), ("center", "sym_cadet_enter"), ("notice", "sym_cadet_notice"),
                       ("cough", "sym_cadet_cough"), ("mutter", "sym_cadet_mutter"), ("qnod", "sym_quill_nod"),
                       ("cwave", "sym_cadet_wave"), ("rwave", "sym_rae_wave_back"), ("cexit", "sym_cadet_exit"),
                       ("gp", "sym_grand_pause"), ("climax", "sym_climax"), ("hchest", "sym_hand_chest"),
                       ("tear", "sym_tear_roll"), ("peak", "sym_peak"), ("final", "sym_final_chord"),
                       ("celesta", "sym_celesta_echo")):
        setattr(n, attr, beat(name))
    n.oh_s, n.oh_e = line_start("r09"), line_end("r09")
    n.c01_s, n.c01_e = line_start("c01"), line_end("c01")
    e = _menv().get("symphony", {})
    n.beats = sorted(n.music + b for b in e.get("beats", []))
    n.downbeats = sorted(n.music + b for b in e.get("downbeats", []))
    n.onsets = sorted(music_onsets("symphony"))
    n.first_note = n.onsets[0] if n.onsets else n.music + 0.55
    return n


def _db(local, tol=0.75):
    """Music downbeat nearest to sym_music_start + local seconds (falls back to that time)."""
    T = _T()
    guess = T.music + local
    best = min(T.downbeats, key=lambda d: abs(d - guess), default=guess)
    return best if abs(best - guess) <= tol else guess


def _bt(local, tol=0.4):
    """Music beat nearest to sym_music_start + local seconds (falls back to that time)."""
    T = _T()
    guess = T.music + local
    best = min(T.beats, key=lambda d: abs(d - guess), default=guess)
    return best if abs(best - guess) <= tol else guess


# =========================================================================== small helpers


def _mix(a, b, u):
    u = clamp(u)
    return tuple(int(round(a[i] + (b[i] - a[i]) * u)) for i in range(3))


def _rms(t, key="rms"):
    """Music loudness, lightly smoothed (pure function of t)."""
    return sum(music_env("symphony", t - k * 0.05, key) for k in range(8)) / 8.0


def _gaze_eval(t, sched, target_fn):
    """Gaze from a schedule [(t0, target[, dur])]: a target is (lx, ly) or a name that target_fn(name, t)
    resolves to (lx, ly) -- moving targets (a mote, a memory bubble) are followed continuously. Each entry
    blends in from the previous one over `dur` (default 0.1 s: a saccade, eased out; longer: an eased
    pursuit). Entries are spaced further apart than their blend times."""
    i = 0
    for k in range(len(sched)):
        if sched[k][0] <= t:
            i = k
        else:
            break

    def val(tg):
        return tg if isinstance(tg, tuple) else target_fn(tg, t)

    cur = val(sched[i][1])
    if i == 0 or t < sched[0][0]:
        return cur
    dur = sched[i][2] if len(sched[i]) > 2 else 0.1
    x = (t - sched[i][0]) / dur
    if x >= 1.0:
        return cur
    prev = val(sched[i - 1][1])
    e = ease_out(x) if dur <= 0.13 else ease_in_out(x)
    return (lerp(prev[0], cur[0], e), lerp(prev[1], cur[1], e))


def _blinks(t, times, base=0.17):
    """Explicit blinks: [(t0, dur)] or t0 -> lid multiplier 0..1 (fast close, slower open)."""
    v = 1.0
    for b in times:
        b0, d = (b, base) if not isinstance(b, tuple) else b
        x = (t - b0) / d
        if 0.0 <= x < 1.0:
            c = math.sin(min(1.0, x / 0.38) * math.pi / 2) if x < 0.38 else math.cos((x - 0.38) / 0.62 * math.pi / 2)
            v = min(v, 1.0 - c)
    return v


def _arm(a: ArmPose, **kw) -> ArmPose:
    d = dict(shoulder=a.shoulder, elbow=a.elbow, wrist=a.wrist, hand=a.hand, across=a.across, behind=a.behind)
    d.update(kw)
    return ArmPose(**d)


class ArmTrack:
    """Keyframed ArmPose blending (eased); hand shape switches at the middle of each blend."""

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


def _catmull(pts, u):
    """Point on a Catmull-Rom chain through pts at u in 0..1."""
    n = len(pts) - 1
    u = clamp(u) * n
    i = min(int(u), n - 1)
    f = u - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    f2, f3 = f * f, f * f * f
    return tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * f + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * f2
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * f3) for k in range(2))


def _pulse(t, t0, rise, hold, fall):
    """0 -> 1 -> 0 envelope: eases up over `rise` from t0, holds `hold`, eases down over `fall`."""
    if t <= t0 or t >= t0 + rise + hold + fall:
        return 0.0
    if t < t0 + rise:
        return ease_in_out((t - t0) / rise)
    if t < t0 + rise + hold:
        return 1.0
    return 1.0 - ease_in_out((t - t0 - rise - hold) / fall)


# palette for light (rgb tuples)
C_WIN = (159, 182, 255)
C_TEAL = (127, 255, 233)
C_AMBER = (255, 210, 154)
C_VIOLET = (183, 156, 255)
C_WARM = (255, 228, 196)
C_CORRIDOR = (196, 228, 255)
_RIB = (C_TEAL, C_AMBER, C_VIOLET)
TINT = (20, 30, 70)


def _ribbon_col(t, period=9.0, phase=0.0):
    u = (t / period + phase) % 3.0
    i = int(u)
    return _mix(_RIB[i], _RIB[(i + 1) % 3], smoothstep(u - i))


# =========================================================================== lighting / fx levels


@lru_cache(maxsize=1)
def _light_tracks():
    T = _T()
    D, F1 = T.dim, T.first_note
    CL = T.climax
    d = {}
    # the room: dims for the symphony; at the BURST it briefly lifts (the room floods with light)
    d["room"] = Track([(D, 1.0), (D + 1.5, 0.25, "io"), (CL - 0.02, 0.25), (CL + 0.4, 0.4, "out"),
                       (CL + 2.8, 0.25, "io")])
    d["dark"] = Track([(D, 0.0), (D + 1.5, 1.0, "io")])
    # window: brightens a touch with the dim, breathes, blazes at the climax (kept below clipping), settles
    d["wb"] = Track([(D, 1.0), (D + 1.5, 1.12), (T.build, 1.15), (T.gp - 0.4, 1.3), (T.gp + 0.2, 1.0),
                     (CL - 0.05, 1.02), (CL + 0.35, 1.62, "out"), (T.tear, 1.26), (T.peak, 1.24),
                     (T.peak + 1.6, 1.36), (T.final, 1.28), (T.final + 3.2, 1.05), (T.end, 1.0)])
    # the galaxy gathers in the window through the build (while the cadet strolls through)
    d["swirl"] = Track([(T.build, 0.0), (T.build + 10.5, 0.82, "io"), (CL - 0.2, 0.93), (CL + 1.2, 1.0),
                        (T.final + 3.0, 1.0), (T.end, 0.4, "io")])
    d["rib"] = Track([(T.theme - 0.3, 0.0), (T.theme + 2.8, 0.5, "io"), (T.mug + 2, 0.58), (T.mem, 0.62),
                      (T.build, 0.7), (T.gp - 0.3, 0.92), (CL, 0.95), (CL + 0.3, 1.0),
                      (T.final, 1.0), (T.final + 2.8, 0.0, "io")])
    d["burst"] = Track([(CL - 0.02, 0.0), (CL + 0.6, 0.72, "out"), (T.tear, 0.3),
                        (T.peak, 0.26), (T.peak + 1.5, 0.45), (T.peak + 4.5, 0.3), (T.final, 0.26),
                        (T.final + 2.0, 0.0)])
    d["freeze"] = Track([(T.gp - 0.45, 0.0), (T.gp + 0.1, 1.0, "out"), (CL - 0.18, 1.0),
                         (CL + 0.02, 0.0, "in")])
    d["lburst"] = Track([(CL - 0.02, 0.0), (CL + 0.3, 0.64, "out"), (CL + 3.2, 0.34), (T.peak, 0.3),
                         (T.peak + 1.6, 0.4), (T.final, 0.3), (T.final + 3.0, 0.0)])
    d["flash"] = Track([(CL - 0.01, 0.0), (CL + 0.04, 0.06, "out"), (CL + 0.45, 0.0, "io")])
    d["vign"] = Track([(D, 0.22), (D + 1.5, 0.45), (CL, 0.5), (CL + 0.4, 0.22), (T.peak, 0.3),
                       (T.final + 2, 0.45), (T.end, 0.55)])
    d["sparks"] = Track([(T.final + 0.3, 0.0), (T.final + 3.0, 1.0, "io"), (T.celesta + 1.0, 0.75),
                         (T.end, 0.45)])
    d["motes"] = Track([(T.theme, 0.55), (T.build, 0.7), (T.gp, 0.95), (CL, 0.95), (CL + 0.6, 1.5),
                        (T.final, 1.2), (T.final + 3, 0.6), (T.end, 0.35)])
    d["sparkle_a"] = Track([(F1 - 1, 1.0), (CL - 0.5, 1.0), (CL + 0.5, 0.55), (T.final, 0.6),
                            (T.final + 2, 0.9)])
    # characters: low light, deep-blue tint, rim lit by the nearest light
    d["c_light"] = Track([(D, 1.0), (D + 1.5, 0.33, "io"), (CL - 0.05, 0.33), (CL + 0.3, 0.52, "out"),
                          (T.tear, 0.4), (T.peak + 1.5, 0.44), (T.final, 0.4), (T.final + 3, 0.3)])
    d["c_tint"] = Track([(D, 0.0), (D + 1.5, 0.36, "io"), (CL, 0.36), (CL + 0.3, 0.2), (T.final, 0.22),
                         (T.final + 3, 0.36)])
    d["c_rim"] = Track([(D + 0.3, 0.06), (D + 1.6, 0.38, "io"), (T.build, 0.4), (T.gp, 0.55), (CL, 0.55),
                        (CL + 0.3, 1.0, "out"), (T.tear, 0.75), (T.final, 0.75), (T.final + 3, 0.42)])
    d["c_warm"] = Track([(T.build, 0.0), (T.gp, 0.25), (CL, 0.3), (CL + 0.3, 1.0), (T.final, 0.85),
                         (T.final + 3.5, 0.15)])
    return d


def _freeze_clock(t):
    """Time with the grand-pause freeze taken out (t minus the integral of `freeze`): everything that runs on
    it (dust, ribbons, the window) eases to a hold and resumes without a jump."""
    T = _T()
    t0 = T.gp - 0.5
    if t <= t0:
        return t
    L = _light_tracks()["freeze"]
    n = 48
    t1 = min(t, T.climax + 0.1)
    dt = (t1 - t0) / n
    held = sum(L(t0 + (k + 0.5) * dt) for k in range(n)) * dt
    return t - held


def _rib_clock(t, burst):
    """Ribbon time. fx.draw_ribbons adds 2.6 * smoothstep(burst) to its clock; that is cancelled here and
    replaced by a gentle surge after the climax, so the ribbons never run faster than ~1.8x (and the
    music-driven jitter of `burst` does not jiggle them)."""
    T = _T()
    surge = 0.9 * smoothstep((t - T.climax) / 1.8)
    return _freeze_clock(t) + surge - 2.6 * smoothstep(burst)


def _levels(t):
    L = _light_tracks()
    T = _T()
    rms = _rms(t)
    hi = _rms(t, "high")
    lv = SimpleNamespace()
    lv.rms, lv.hi = rms, hi
    lv.room = L["room"](t)
    lv.dark = L["dark"](t)
    lv.swirl = L["swirl"](t)
    breath = 0.10 * rms if t < T.climax else 0.18 * rms
    lv.wb = L["wb"](t) + breath * (1.0 - L["freeze"](t))
    lv.rib = L["rib"](t)
    lv.burst = L["burst"](t) * (0.85 + 0.3 * rms)
    lv.freeze = L["freeze"](t)
    lv.lburst = L["lburst"](t) * (0.8 + 0.3 * rms)
    lv.flash = L["flash"](t)
    lv.vign = L["vign"](t)
    lv.sparks = L["sparks"](t)
    lv.motes = L["motes"](t)
    lv.sparkle_a = L["sparkle_a"](t)
    # ambient dust only once the theme starts (the intro has its own note motes)
    lv.motes *= smoothstep((t - T.theme) / 3.0)
    # character light
    cl = L["c_light"](t) + 0.05 * rms * lv.dark
    warm = L["c_warm"](t)
    rib_c = _ribbon_col(t, 9.0)
    base_rim_r = _mix(C_WIN, rib_c, 0.35 * smoothstep((t - T.theme) / 3.0))
    base_rim_r = _mix(base_rim_r, C_VIOLET, 0.35 * smoothstep((t - T.build) / 6.0))
    base_rim_q = _mix(C_WIN, C_TEAL, smoothstep((t - T.dim) / 1.5))
    base_rim_q = _mix(base_rim_q, rib_c, 0.3 * smoothstep((t - T.theme) / 3.0))
    lv.rae = dict(light=cl + 0.04 * lv.dark, tint=TINT, tint_amt=L["c_tint"](t), rim=L["c_rim"](t) * (0.92 + 0.15 * rms),
                  rim_color=_mix(base_rim_r, C_WARM, warm))
    lv.quill = dict(light=cl, tint=TINT, tint_amt=L["c_tint"](t), rim=L["c_rim"](t) * (0.95 + 0.1 * rms),
                    rim_color=_mix(base_rim_q, C_WARM, warm))
    # the cadet: same room light; a cool corridor rim while he is near the open door
    near_door = 1.0 - smoothstep((t - (T.cdoor + 2.6)) / 1.6)
    lv.cadet = dict(light=cl + 0.03 * lv.dark, tint=TINT, tint_amt=L["c_tint"](t),
                    rim=L["c_rim"](t) * (0.9 + 0.12 * rms),
                    rim_color=_mix(_mix(base_rim_r, C_CORRIDOR, 0.6 * near_door), C_WARM, warm))
    return lv


# =========================================================================== Rae


SEAT_X = 230.0
MUG_SPOT = (330.0, float(env.BENCH_SEAT_Y))     # BIBLE section 9: the mug rests on the bench here

# Far (left) arm. The rig's far-arm targeting is discontinuous for `across` between ~0.15 and ~0.27 (and its
# draw layer flips at 0.25), so `across` is never animated through that band: it changes only on cuts
# (two -> rae_med: LAP_S1 -> LAP_L; cad_mutter -> rae_wave, where she is off screen before the cut: LAP_L ->
# THIGH_L) and the wave back is animated entirely at across ~0 (the hand lifts out to the side).
LAP_S1 = ArmPose(shoulder=15.0, elbow=55.0, wrist=0.0, hand="relaxed")             # S1's last far-arm pose
LAP_L = ArmPose(shoulder=8.0, elbow=40.0, wrist=6.0, hand="relaxed", across=0.35)   # far hand on top of her knee
THIGH_L = ArmPose(shoulder=12.0, elbow=26.0, wrist=4.0, hand="relaxed")               # far hand on her far thigh
WAVE_L = ArmPose(shoulder=32.0, elbow=118.0, wrist=-14.0, hand="open", across=-0.08)  # the tiny wave back
CHEST_POST = R.ARMS["hand_on_chest"]                                                  # right hand on her heart


@lru_cache(maxsize=1)
def _rae_tracks():
    T = _T()
    S, D, F1, TH, MG, ME = T.start, T.dim, T.first_note, T.theme, T.mug, T.mem
    OH, GL, BU, GP, CL, HC, TR, PK, FC, CE, E = (T.oh, T.glis, T.build, T.gp, T.climax, T.hchest, T.tear, T.peak,
                                                 T.final, T.celesta, T.end)
    NO, CW, RW = T.notice, T.cwave, T.rwave
    d = {}
    # ---- the mug goes down on the bench on sym_hand_chest, then her right hand goes to her heart
    d["reach_t"] = HC - 0.62          # the mug lifts off her lap
    d["place_t"] = HC + 0.14          # ... and touches the bench
    d["turn"] = Track([(S, 0.35), (PK + 0.4, 0.35), (PK + 4.6, 0.3, "io")])   # (inside the pull-back)
    d["lean"] = Track([(S, 2.0), (S + 1.2, 1.0), (F1 + 2.0, 0.5), (TH - 0.5, 2.0), (MG + 1.5, 3.0), (ME, 2.0),
                       (OH - 0.3, 4.0), (BU, 2.0), (BU + 4.0, 1.5), (RW - 0.3, 1.5), (RW + 0.35, 3.0),
                       (RW + 1.3, 1.6), (GP - 0.6, 1.2), (GP + 0.1, 0.3), (CL, 0.3), (CL + 0.45, -2.6, "out"),
                       (HC - 0.55, -1.2), (HC + 0.1, 3.2), (HC + 0.5, 3.0), (HC + 1.4, 0.6), (TR, 0.4),
                       (E, 0.5)])
    d["bounce"] = Track([(CL, 0.0), (CL + 0.28, 1.8, "out"), (CL + 1.1, 0.0)])
    d["shoulders"] = Track([(S, 0.0), (GP - 0.1, 0.0), (GP + 0.35, 0.2), (CL, 0.22), (CL + 0.7, 0.0, "out"),
                            (E, 0.0)])
    # small catches of breath while she cries through the smile (tear roll .. final chord)
    d["hitches"] = [TR + 0.95, TR + 2.55, PK + 0.4, PK + 2.9, PK + 5.6, FC + 1.6]
    # ---- head (looking up is carried by the nod; the gaze adds to it)
    d["nod"] = Track([(S, 0.115), (S + 0.7, 0.1), (D + 0.3, 0.16), (F1, 0.12), (F1 + 2.5, 0.08), (TH - 0.6, 0.24),
                      (MG, 0.18), (MG + 3.2, 0.3), (MG + 5.5, 0.32), (ME + 1.0, 0.12), (OH - 1.5, 0.16), (OH, 0.12),
                      (GL, 0.06), (GL + 4.5, 0.08), (BU - 1.5, 0.22), (BU + 1.5, 0.3), (NO + 2.0, 0.32),
                      (CW, 0.32), (CW + 0.4, 0.2), (RW, 0.17), (RW + 0.24, 0.07, "out"), (RW + 0.62, 0.16),
                      (RW + 1.3, 0.2), (RW + 2.2, 0.34), (GP, 0.4), (CL, 0.42), (CL + 0.7, 0.5, "out"),
                      (HC - 0.5, 0.46), (HC + 0.1, 0.3), (HC + 0.8, 0.32), (HC + 1.6, 0.46), (TR, 0.48),
                      (PK, 0.47), (PK + 5.0, 0.43), (FC, 0.4), (CE, 0.34)])
    d["tilt"] = Track([(S, -3.8), (F1 + 2.3, -3.0), (TH - 0.6, 0.0), (MG, 2.0), (MG + 4.5, 4.0), (ME, 0.5),
                       (ME + 3.5, -3.0), (OH, 4.0), (GL, 6.0), (GL + 4.0, 3.0), (BU, 0.0), (BU + 3.0, 1.5),
                       (CW, 1.0), (RW + 0.3, 4.5), (RW + 1.4, 1.5), (GP, -2.0), (CL, 0.0), (HC, 2.0), (TR, 4.0),
                       (PK, 6.0), (FC, 4.0), (E, 3.0)])
    # ---- gaze (screen space; Quill is up and to her right). |look_x| stays >= 0.3 on every hold so she
    #      never stares into the lens; geometric targets are followed (motes, memory bubbles, his hand)
    d["gaze"] = [
        (S, (0.62, -0.35)),                        # S1 handoff: on Quill
        (S + 0.3, (0.58, -0.22), 0.4),             # his hand comes out from behind his back
        (S + 0.75, (-0.5, -0.5)),                  # the lights go down: a dart up-left
        (S + 1.25, (0.34, -0.64)),                 # ... up at the room
        (S + 1.7, (0.6, -0.42), 0.3),              # back to his raised hand
        (F1 + 0.1, "mote0", 0.12),                 # the first note: a mote leaves his palm; she follows it in
        (F1 + 3.1, (0.6, -0.3), 0.3),              # glance at him: is that you?
        (F1 + 3.9, (-0.52, -0.3)),                 # a mote on her left
        (F1 + 4.8, (0.4, -0.55), 0.5),
        (TH - 0.8, (0.36, -0.7), 0.8),             # eyes lift toward the sound
        (TH + 0.5, (-0.46, -0.48)),                # a ribbon wakes on her left
        (TH + 1.6, (0.4, -0.62), 0.9),
        (TH + 2.8, (0.52, -0.4), 0.8),
        (MG + 0.3, (0.42, -0.36), 0.6),
        (MG + 2.0, (-0.44, -0.5)),
        (MG + 3.2, (0.36, -0.68), 0.6),
        (MG + 4.6, (0.48, -0.52), 1.0),            # wonder: the eyes wander up
        (MG + 5.7, (0.34, -0.74), 1.2),
        (ME + 0.35, "car_window"),                 # the memories: she follows each one
        (ME + 3.0, (0.62, -0.42)),                 # a glance at Quill
        (ME + 3.65, "hands"),                      # ... "oh"
        (OH + 1.1, "dog_door"),
        (OH + 2.5, "kitchen_dawn"),
        (GL + 1.3, "friends_table"),
        (GL + 3.75, "sea_sunset"),
        (GL + 6.8, (0.36, -0.68), 0.7),            # looks up as the build approaches
        (BU + 1.0, (0.4, -0.72), 1.0),             # the galaxy gathering in the window (she never sees the cadet
        (BU + 2.4, (-0.4, -0.62)),                 # gawking at her)
        (BU + 3.3, (0.38, -0.7), 0.5),
        (BU + 5.0, (0.46, -0.6), 1.2),
        (BU + 6.9, (-0.36, -0.66)),
        (BU + 7.8, (0.36, -0.72), 0.7),
        (CW + 0.1, "cadet", 0.14),                 # ... until he waves: she finds him
        (RW + 1.45, (0.4, -0.66), 0.6),            # and goes back to the music
        (GP - 0.4, (0.33, -0.66), 0.3),
        (CL + 0.9, (-0.42, -0.6)),
        (CL + 2.4, (0.38, -0.66), 0.5),
        (TR, (0.34, -0.72), 0.4),
        (TR + 2.2, (0.38, -0.64), 1.3),
        (TR + 3.6, (0.44, -0.7), 1.0),
        (PK + 1.0, (-0.4, -0.6)),
        (PK + 3.0, (0.42, -0.6)),
        (PK + 5.0, (0.36, -0.66), 1.0),
        (FC - 1.6, (0.6, -0.3)),                   # a glance at Quill ...
        (FC - 0.4, (0.4, -0.5), 0.8),
        (FC + 0.6, "qhand", 0.3),                  # ... she watches his hand come down
        (FC + 3.4, (0.42, -0.34), 0.5),
        (CE + 0.15, "final", 0.25),                # the last mote
    ]
    d["blinks"] = [(D + 0.37, 0.2), (F1 + 0.15, 0.18), F1 + 1.9, F1 + 3.85, TH + 0.42, TH + 2.5, (MG + 0.5, 0.3),
                   MG + 1.95, MG + 5.4, ME + 0.3, ME + 3.6, (OH - 0.45, 0.32), OH + 1.05, (GL + 0.5, 0.42),
                   GL + 2.6, GL + 3.7, GL + 5.0, GL + 6.75, BU + 0.9, BU + 2.35, BU + 4.6, (BU + 6.85, 0.2),
                   BU + 9.1, (CW + 0.08, 0.18), (RW + 0.95, 0.22), (RW + 2.6, 0.24), CL + 2.5, (HC + 0.05, 0.2),
                   (TR + 0.15, 0.36), TR + 3.0, PK + 0.95, PK + 2.95, PK + 4.8, PK + 7.0, (FC + 1.3, 0.3),
                   (CE - 0.3, 0.3), (E - 0.75, 0.34)]
    # ---- eyelids / brows
    d["lid"] = Track([(S, 0.72), (D, 0.74), (D + 0.12, 0.88, "out"), (F1 - 0.3, 0.8), (F1 + 2.4, 0.78),
                      (TH - 0.6, 0.93), (MG, 0.95), (MG + 1.0, 0.97), (GL, 0.94), (GL + 2.2, 0.86), (BU, 0.9),
                      (RW - 0.2, 0.9), (RW + 0.3, 0.84), (RW + 1.4, 0.9), (GP - 0.3, 0.95),
                      (GP + 0.12, 1.0, "out"), (CL + 1.2, 1.0), (CL + 2.5, 0.94), (TR, 0.92), (TR + 2.0, 0.88),
                      (PK, 0.88), (FC, 0.82), (CE, 0.84), (E, 0.8)])
    d["wide"] = Track([(D, 0.0), (D + 0.12, 0.18, "out"), (D + 0.9, 0.0), (GP - 0.1, 0.0), (GP + 0.16, 0.48, "out"),
                       (CL, 0.5), (CL + 0.12, 0.6, "out"), (CL + 1.4, 0.15), (TR, 0.0)])
    d["brow_raise"] = Track([(S, 0.1), (S + 0.6, 0.22), (D, 0.24), (D + 0.15, 0.48, "out"), (D + 1.2, 0.15),
                             (F1, 0.15), (F1 + 0.25, 0.32, "out"), (F1 + 2.4, 0.18), (TH - 0.5, 0.36),
                             (MG + 0.4, 0.52), (MG + 5.0, 0.4), (ME + 0.8, 0.5), (OH, 0.55), (GL, 0.38),
                             (BU, 0.46), (CW + 0.1, 0.46), (CW + 0.3, 0.56, "out"), (RW + 1.2, 0.46), (GP, 0.55),
                             (GP + 0.15, 0.72, "out"), (CL, 0.75), (CL + 0.15, 0.85, "out"), (CL + 2.0, 0.5),
                             (TR, 0.38), (FC, 0.3), (E, 0.26)])
    d["worry"] = Track([(S, 0.0), (F1 + 4.0, 0.1), (MG, 0.25), (ME, 0.35), (OH - 0.3, 0.6), (GL, 0.72),
                        (GL + 3.0, 0.78), (BU, 0.6), (BU + 5.0, 0.7), (RW, 0.72), (GP, 0.72), (CL, 0.55),
                        (TR, 0.8), (PK, 0.72), (FC, 0.62), (E, 0.6)])
    d["furrow"] = Track([(S, 0.2), (F1 + 2.4, 0.2), (F1 + 4.8, 0.0)])
    # ---- mouth
    d["smirk"] = Track([(S, 0.7), (S + 0.5, 0.74), (D, 0.72), (D + 0.3, 0.55), (F1, 0.62), (F1 + 2.2, 0.62),
                        (TH - 0.6, 0.05), (MG, 0.0)])
    d["smile"] = Track([(S, 0.1), (F1 + 2.4, 0.08), (TH - 0.5, 0.0), (ME + 0.9, 0.0), (ME + 1.8, 0.14),
                        (ME + 3.6, 0.1), (OH - 0.6, 0.0), (OH + 0.6, -0.05), (GL, -0.08), (GL + 2.5, -0.16),
                        (GL + 4.9, -0.12), (GL + 5.9, 0.16), (GL + 7.2, 0.1), (BU, -0.02), (RW - 0.25, 0.0),
                        (RW + 0.35, 0.22), (RW + 1.5, 0.08), (GP, 0.0), (CL + 0.8, 0.08), (TR + 0.5, 0.12),
                        (TR + 2.0, 0.38), (PK, 0.36), (PK + 5.0, 0.32), (FC, 0.26), (E, 0.16)])
    d["squint"] = Track([(S, 0.072), (S + 0.8, 0.04), (F1 + 2.4, 0.02), (TH, 0.0), (GL + 5.6, 0.0), (GL + 6.2, 0.08),
                         (GL + 7.4, 0.02), (RW - 0.2, 0.02), (RW + 0.35, 0.12), (RW + 1.5, 0.02), (TR + 1.0, 0.0),
                         (TR + 2.2, 0.18), (FC, 0.12), (E, 0.1)])
    d["open"] = Track([(S, 0.0), (F1 + 4.0, 0.02), (MG + 0.2, 0.0), (MG + 1.2, 0.12), (ME, 0.1), (OH - 0.9, 0.08),
                       (OH - 0.35, 0.16), (OH - 0.05, 0.05), (T.oh_e + 0.1, 0.05), (T.oh_e + 0.6, 0.12),
                       (GL, 0.06), (BU, 0.12), (BU + 4.0, 0.1), (RW - 0.2, 0.08), (RW + 0.3, 0.03),
                       (RW + 1.3, 0.1), (GP - 0.2, 0.1), (GP + 0.2, 0.2), (CL, 0.2), (CL + 0.12, 0.4, "out"),
                       (CL + 0.9, 0.22), (TR, 0.08), (TR + 2.0, 0.06), (PK, 0.1), (FC, 0.08), (CE + 0.5, 0.1),
                       (CE + 1.6, 0.16), (E, 0.1)])
    d["round"] = Track([(S, 0.0), (MG, 0.0), (MG + 1.2, 0.2), (ME, 0.25), (GL, 0.1), (GP, 0.3), (CL, 0.35),
                        (CL + 1.5, 0.2), (TR, 0.0)])
    d["tremble"] = Track([(GL + 0.5, 0.0), (GL + 2.5, 0.22), (BU, 0.12), (BU + 5.0, 0.18), (RW, 0.2), (GP, 0.12),
                          (CL + 1.0, 0.2), (TR, 0.4), (TR + 1.6, 0.62), (PK + 2.0, 0.46), (FC, 0.32), (E, 0.25)])
    # ---- tears, eyes
    d["tears"] = Track([(GL, 0.0), (GL + 2.4, 0.7), (BU, 0.72), (RW, 0.78), (GP, 0.86), (TR + 0.35, 0.92),
                        (TR + 1.1, 0.74), (PK, 0.82), (E, 0.74)])
    d["tear_r"] = Track([(TR + 0.3, 0.0), (TR + 1.25, 0.2, "out"), (TR + 3.9, 1.0, "io")])
    d["tear_l"] = Track([(PK + 1.4, 0.0), (PK + 2.4, 0.18, "out"), (PK + 5.4, 1.0, "io")])
    d["shine"] = Track([(D, 0.0), (D + 1.5, 0.18), (MG, 0.25), (MG + 1.5, 0.55), (ME, 0.7), (GL, 0.85),
                        (CL, 1.0), (FC, 0.85), (E, 0.75)])
    d["pupil"] = Track([(D, 1.0), (D + 1.5, 1.12), (MG + 0.3, 1.14), (MG + 2.0, 1.32), (CL, 1.32),
                        (CL + 0.3, 1.18, "out"), (TR, 1.28), (FC, 1.32)])
    d["sniffle"] = Track([(GL, 0.0), (BU, 0.1), (TR, 0.2), (E, 0.26)])
    d["blush"] = Track([(ME, 0.0), (GL + 2, 0.14), (E, 0.2)])
    # ---- arms
    raise_ = R.ARMS["mug_raise"]
    hold = R.ARMS["hold_mug"]
    chest = CHEST_POST
    d["arm_r_pre"] = ArmTrack([(S, raise_), (F1 + 2.4, raise_), (TH - 0.4, ArmPose.blend(raise_, hold, 0.28)),
                               (MG + 0.15, ArmPose.blend(raise_, hold, 0.32)), (MG + 2.1, hold),
                               (d["reach_t"], hold)])
    tp = d["place_t"]
    d["arm_r_post"] = ArmTrack([(tp + 0.2, None), (tp + 0.72, _arm(chest, shoulder=26.0, elbow=98.0, across=0.34)),
                                (tp + 1.25, chest), (TR - 0.4, chest), (TR + 0.6, _arm(chest, wrist=16.0, elbow=122.0)),
                                (PK + 1.0, _arm(chest, wrist=12.0)), (FC, chest)])
    # far hand: on her knee; the tiny wave back; on her knee again
    c_rae = _cut("rae_wave")
    d["arm_l"] = ArmTrack([(S, LAP_S1), (F1 - 0.001, LAP_S1), (F1, LAP_L, "step"),       # (switch on the cut)
                           (c_rae - 0.001, LAP_L), (c_rae, THIGH_L, "step"),             # (switch on the cut)
                           (max(c_rae + 0.02, RW - 0.16), THIGH_L),
                           (RW + 0.04, _arm(THIGH_L, shoulder=14.0, elbow=92.0, wrist=-6.0,
                                                                   hand="open", across=-0.03), "in"),
                           (RW + 0.22, WAVE_L, "out"), (RW + 0.92, WAVE_L),
                           (RW + 1.2, _arm(THIGH_L, shoulder=16.0, elbow=84.0, wrist=-2.0, hand="relaxed"), "in"),
                           (RW + 1.6, THIGH_L, "out"), (CL, THIGH_L),
                           (CL + 0.35, _arm(THIGH_L, elbow=32.0, wrist=10.0, hand="fist"), "out"),
                           (HC + 1.2, _arm(THIGH_L, elbow=29.0, wrist=7.0)), (TR, THIGH_L)])
    return d


def _rae_breath(t):
    """Rae's breathing clock: holds during the grand pause, then resumes without a jump."""
    T = _T()
    held = clamp(t - T.gp - 0.1, 0.0, T.climax - T.gp - 0.1)
    return breathe(t - held, 0.2, 2)


def _rae_body(t) -> Pose:
    """Rae without her right arm (used by the mug-placement solver)."""
    T = _T()
    d = _rae_tracks()
    hitch = 0.0
    for h0 in d["hitches"]:
        x = (t - h0) / 0.55
        if 0.0 <= x < 1.0:
            hitch = max(hitch, math.sin(math.pi * min(1.0, x * 2.2)) * (1.0 - x) ** 0.5)
    br = _rae_breath(t)
    emo = smoothstep((t - T.glis) / 3.0)          # deeper, more visible breathing once she is moved
    arm_l = d["arm_l"](t)
    wv = _pulse(t, T.rwave + 0.1, 0.12, 0.66, 0.2)
    if wv > 0.0:                                  # the wave: two small side-to-side flicks of the hand
        ph = math.sin(2 * math.pi * (t - T.rwave - 0.1) / 0.46)
        arm_l = _arm(arm_l, wrist=arm_l.wrist + wv * 14.0 * ph, elbow=arm_l.elbow - wv * 5.0 * ph)
    p = Pose(x=SEAT_X, y=float(env.FLOOR_Y), facing=1.0, turn=d["turn"](t), sit=1.0, seat_y=float(env.BENCH_SEAT_Y),
             lean=d["lean"](t) - 0.8 * hitch, bounce=d["bounce"](t) - 1.6 * hitch,
             shoulders_up=d["shoulders"](t) + 0.14 * hitch + 0.07 * emo * max(0.0, br),
             arm_l=arm_l, breath=br)
    return p


@lru_cache(maxsize=1)
def _place_arm():
    """Right-arm pose that sets the mug's base exactly on MUG_SPOT at the placement time."""
    d = _rae_tracks()
    tp = d["place_t"]
    body = _rae_body(tp)
    hold = R.ARMS["hold_mug"]
    best = None
    for ac in (0.0, 0.1, 0.22):
        for sh in range(-10, 100, 3):
            for el in range(-10, 140, 3):
                a = _arm(hold, shoulder=float(sh), elbow=float(el), across=ac)
                mp = R.mug_pose(body.copy(arm_r=a, mug="r"), tp)
                if mp is None:
                    continue
                err = math.hypot(mp[0] - MUG_SPOT[0], mp[1] - MUG_SPOT[1]) + 0.15 * abs(mp[3])
                if best is None or err < best[0]:
                    best = (err, sh, el, ac)
    _, sh, el, ac = best
    best = best[:3]
    step = 2.0
    while step > 0.02:
        improved = False
        for dsh, del_ in ((step, 0), (-step, 0), (0, step), (0, -step)):
            a = _arm(hold, shoulder=sh + dsh, elbow=el + del_, across=ac)
            mp = R.mug_pose(body.copy(arm_r=a, mug="r"), tp)
            err = math.hypot(mp[0] - MUG_SPOT[0], mp[1] - MUG_SPOT[1]) + 0.15 * abs(mp[3])
            if err < best[0] - 1e-6:
                best, sh, el, improved = (err, sh + dsh, el + del_), sh + dsh, el + del_, True
                break
        if not improved:
            step *= 0.5
    return _arm(hold, shoulder=sh, elbow=el, across=ac)


def _rae_arm_r(t):
    d = _rae_tracks()
    t0 = d["reach_t"]
    tp = d["place_t"]
    place = _place_arm()
    hold = R.ARMS["hold_mug"]
    if t < t0:
        return d["arm_r_pre"](t)
    if t < tp:
        # lift the mug off her lap, a small arc over her thigh, and set it down on the bench
        mid = ArmPose.blend(hold, place, 0.5)
        lift = _arm(mid, shoulder=mid.shoulder + 7.0, elbow=mid.elbow + 4.0)
        u = (t - t0) / (tp - t0)
        if u < 0.45:
            return ArmPose.blend(hold, lift, smoothstep(u / 0.45))
        return ArmPose.blend(lift, place, smoothstep((u - 0.45) / 0.55))
    # let go: the hand rests on the handle a beat, then lifts away and rises to her chest. The grip opens
    # in stages while it moves (hold -> relaxed -> open) so the fist never snaps into a flat hand in place.
    post = d["arm_r_post"]
    k1 = post.keys[1]
    # (without the mug the rig's "hold" hand is an open C, so the grip that stays on the handle is a "fist")
    t_go = tp + 0.2
    if t < t_go:
        return _arm(place, hand="fist")
    if t < k1[0]:
        u = (t - t_go) / (k1[0] - t_go)
        a = ArmPose.blend(place, k1[1], smoothstep(u))
        return _arm(a, hand="fist" if u < 0.16 else ("relaxed" if u < 0.5 else k1[1].hand))
    return post(t)


def _rae_target(name, t):
    """Gaze (look_x, look_y) toward a moving thing (stage geometry relative to her face)."""
    T = _T()
    pos = None
    sx, sy = 170.0, 150.0
    if name == "mote0":
        m = _note_mote(0, max(t, T.first_note + 0.02))
        if m is not None:
            pos = (m[0], m[1])
    elif name == "qhand":
        qa = _quill_tracks()["arm_r"](t)
        pos = Q.hand_pos(Pose(x=545.0, y=float(env.FLOOR_Y), facing=-1.0, turn=0.35, arm_r=qa), "r")
    elif name == "cadet":
        pos = _cadet_head(round(t, 3))
        if pos is None:
            return (0.75, -0.4)
        sx, sy = 260.0, 260.0          # far away: the eyes travel less per unit
    elif name == "final":
        m = _final_mote(min(t, T.end - 1.0))
        if m is not None:
            pos = (m[0], m[1])
        sx, sy = 120.0, 110.0
    else:
        st = _mem1(_MEM_INDEX[name], t, clamp_age=True)
        pos = (st[2], st[3])
    if pos is None:
        return (0.4, -0.6)
    hx, hy = _rae_face_ref()
    return (clamp((pos[0] - hx) / sx, -1.0, 1.0), clamp((pos[1] - hy) / sy - 0.05, -1.0, 1.0))


def _rae_look(t):
    return _gaze_eval(t, _rae_tracks()["gaze"], _rae_target)


def _rae_pose(t, lv) -> Pose:
    T = _T()
    d = _rae_tracks()
    p = _rae_body(t)
    lx, ly = _rae_look(t)
    # eyes lead, the head follows (lagged gaze drives a little head turn / nod)
    lag = [_rae_look(t - 0.12 - 0.08 * i) for i in range(4)]
    glx = sum(g[0] for g in lag) / 4.0
    gly = sum(g[1] for g in lag) / 4.0
    blink = _blinks(t, d["blinks"])
    lid = d["lid"](t) * blink
    mo, mr = mouth("rae", t)
    gk = smoothstep((t - T.start) / 1.5)          # S2's own head/gaze dynamics fade in from the S1 handoff
    nod = d["nod"](t) + gk * (-0.12 * gly + 0.025 * noise1(t * 0.5, 5))
    if t > T.celesta:                             # (she follows the last mote down)
        nod -=0.22 * smoothstep((t - T.celesta - 0.6) / 2.6)
    tilt = d["tilt"](t) + 1.2 * noise1(t * 0.35, 8)
    hturn = 0.16 * glx * smoothstep((t - T.start) / 1.5) + 0.02 * noise1(t * 0.4, 9)
    gp_hold = 1.0 - smoothstep((t - T.gp) / 0.25) * (1.0 - smoothstep((t - T.climax) / 0.2))
    tilt = lerp(d["tilt"](T.gp), tilt, gp_hold) if T.gp < t < T.climax + 0.2 else tilt
    # the rig's gaze travel is small: exaggerate a little once we're past the S1 handoff
    lx, ly = clamp(lx * (1.0 + 0.3 * gk), -1.15, 1.15), clamp(ly * (1.0 + 0.35 * gk), -1.0, 1.0)
    face = dict(
        lid_l=lid, lid_r=lid * (0.985 + 0.015 * noise1(t * 0.7, 3)), look_x=lx + 0.02 * noise1(t * 2.3, 1) * gp_hold,
        look_y=ly + 0.02 * noise1(t * 2.1, 2) * gp_hold, pupil=d["pupil"](t), squint=d["squint"](t),
        eye_wide=d["wide"](t), brow_raise=d["brow_raise"](t), brow_worry=d["worry"](t),
        brow_furrow=d["furrow"](t), mouth_open=d["open"](t) + 0.8 * mo, mouth_round=clamp(d["round"](t) + mr),
        smile=d["smile"](t), smirk=d["smirk"](t), mouth_tremble=d["tremble"](t), tears=d["tears"](t),
        tear_r=d["tear_r"](t), tear_l=d["tear_l"](t), eye_shine=d["shine"](t), blush=d["blush"](t),
        sniffle=d["sniffle"](t), head_nod=nod, head_tilt=tilt, head_turn=hturn)
    mug = "r" if t < d["place_t"] else None
    return p.copy(arm_r=_rae_arm_r(t), mug=mug, **face, **lv.rae)


def _bench_mug(t):
    """(x, y, scale, angle, flip) of the mug resting on the bench once she lets go of it, else None."""
    d = _rae_tracks()
    tp = d["place_t"]
    if t < tp:
        return None
    mp0 = _place_mug_pose()
    ang = mp0[3] * (1.0 - smoothstep((t - tp) / 0.22))
    return (MUG_SPOT[0], MUG_SPOT[1], mp0[2], ang, mp0[4])


@lru_cache(maxsize=1)
def _place_mug_pose():
    d = _rae_tracks()
    tp = d["place_t"]
    p = _rae_body(tp).copy(arm_r=_place_arm(), mug="r")
    return R.mug_pose(p, tp)


def _draw_bench_mug(c, bm, rp):
    """The mug on the bench, lit like Rae, with a soft contact shadow on the cushion."""
    with Layer(c, cf=light_filter(rp.light ** 0.65, rp.tint, rp.tint_amt),
               bounds=skia.Rect(bm[0] - 46, bm[1] - 56, bm[0] + 46, bm[1] + 14)):
        sh = skia.Paint(AntiAlias=True, Color=skia.Color(6, 8, 20, 120))
        sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0))
        c.drawOval(skia.Rect(bm[0] - 24, bm[1] - 4, bm[0] + 26, bm[1] + 5), sh)
        R.draw_mug(c, *bm)


# =========================================================================== Quill


@lru_cache(maxsize=1)
def _quill_tracks():
    T = _T()
    S, D, F1, FC = T.start, T.dim, T.first_note, T.final
    MU, QN = T.c01_s, T.qnod
    d = {}
    bb = Q.ARMS["behind_back"]
    cond = Q.ARMS["raise_conduct"]
    rest = Q.ARMS["rest"]
    d["arm_r"] = ArmTrack([(S + 0.25, bb), (S + 0.75, ArmPose(shoulder=12.0, elbow=22.0, wrist=-4.0, hand="relaxed")),
                           (S + 1.6, cond), (FC + 0.45, cond),
                           (FC + 1.9, ArmPose(shoulder=30.0, elbow=46.0, wrist=-12.0, hand="relaxed")),
                           (FC + 3.4, rest)])
    # the other hand stays clasped behind his back the whole time: a conductor's poise (and nothing
    # dangling at the frame edge of Rae's singles)
    d["arm_l"] = ArmTrack([(S, bb)])
    # conducting envelope (0 before the first note / during the grand pause / after the final chord)
    d["cond"] = Track([(F1 - 0.3, 0.0), (F1, 1.0), (T.gp - 0.5, 1.0), (T.gp, 0.0), (T.climax, 0.0),
                       (T.climax + 0.4, 1.0), (FC, 1.0), (FC + 0.5, 0.0)])
    d["lift"] = Track([(T.gp - 0.5, 0.0), (T.gp, 5.0, "out"), (T.climax, 5.0), (T.climax + 0.6, 14.0, "out"),
                       (T.climax + 2.6, 7.0), (T.peak, 6.0), (T.peak + 1.6, 10.0), (FC, 6.0), (FC + 0.5, 0.0)])
    d["shoulders"] = Track([(S, 0.0), (S + 0.25, 0.1), (S + 0.9, 0.0)])
    # the cadet's "Cool music, Quill.": the eyes go to him, a small casual nod (the hand keeps conducting)
    d["nod"] = Track([(S, 0.0), (S + 0.3, 0.06), (S + 1.4, 0.02), (QN - 0.06, 0.02), (QN + 0.2, -0.17, "out"),
                      (QN + 0.6, -0.01, "io"), (T.gp - 0.4, 0.0), (T.gp + 0.1, -0.08), (T.climax, -0.07),
                      (T.climax + 0.5, 0.0), (FC + 2.0, -0.06)])
    d["hturn"] = Track([(MU + 0.3, 0.0), (MU + 0.75, -0.1), (QN + 0.8, -0.12), (QN + 1.35, 0.0)])
    d["tilt"] = Track([(S, 2.75), (S + 1.6, 1.0), (T.glis + 1.0, 0.0), (T.glis + 1.6, 1.5), (T.glis + 2.8, 6.0),
                       (T.glis + 4.2, 10.0), (T.build, 7.0), (T.build + 3.0, 3.0), (MU + 0.3, 3.0), (QN, 1.0),
                       (QN + 1.4, 3.0), (T.climax, 2.0), (FC, 3.0), (FC + 3.0, 7.0)])
    d["brow"] = Track([(S, 0.05), (T.glis + 1.4, 0.05), (T.glis + 2.6, 0.32), (T.build, 0.15), (QN - 0.1, 0.15),
                       (QN + 0.15, 0.24), (QN + 0.9, 0.15), (T.climax, 0.15), (T.climax + 0.3, 0.3), (T.tear, 0.18),
                       (FC, 0.12)])
    d["smile"] = Track([(S, 0.06), (S + 1.2, 0.0), (QN - 0.1, 0.0), (QN + 0.25, 0.12), (QN + 1.1, 0.0),
                        (FC + 2.0, 0.0), (FC + 4.0, 0.1)])
    d["glow"] = Track([(S, 0.1), (D, 0.12), (D + 1.5, 0.5), (T.climax, 0.6), (T.climax + 0.3, 1.0), (T.tear, 0.8),
                       (FC, 0.75), (FC + 3.0, 0.35)])
    d["gaze"] = Track([(S, (-0.45, 0.22)), (S + 0.5, (-0.3, -0.02), "out"), (S + 1.4, (-0.46, 0.26)),
                       (T.mem + 1.2, (-0.46, 0.26)), (T.mem + 1.8, (-0.6, 0.0)), (T.mem + 3.0, (-0.6, 0.0)),
                       (T.mem + 3.6, (-0.48, 0.28)), (MU + 0.2, (-0.48, 0.28)), (MU + 0.34, (0.12, 0.4), "out"),
                       (QN - 0.2, (0.3, 0.34)), (QN + 0.75, (0.42, 0.3)), (QN + 0.9, (-0.46, 0.27), "out"),
                       (T.climax + 0.8, (-0.48, 0.3)), (FC + 1.2, (-0.48, 0.3)), (FC + 2.2, (-0.46, 0.34))])
    return d


def _quill_pose(t, lv) -> Pose:
    T = _T()
    d = _quill_tracks()
    arm = d["arm_r"](t)
    c = d["cond"](t) * (0.45 + 0.9 * lv.rms)
    if c > 0.001 or d["lift"](t) > 0.001:
        # small, precise conducting: a soft ictus on every beat, a wider arc on each downbeat
        b = _beat_phase(t, T.beats)
        db = _beat_phase(t, T.downbeats)
        ict = 0.5 + 0.5 * math.cos(2 * math.pi * b)
        arc = 0.5 + 0.5 * math.cos(2 * math.pi * db)
        lift = d["lift"](t)
        arm = _arm(arm, shoulder=arm.shoulder + lift - c * (1.6 * ict + 3.0 * arc),
                   elbow=arm.elbow + c * (2.5 * ict + 4.0 * arc) - 0.4 * lift,
                   wrist=arm.wrist + c * (7.0 * ict - 3.5) + 0.6 * lift)
    lx, ly = d["gaze"](t)
    sway = 0.6 * math.sin(2 * math.pi * _beat_phase(t, T.downbeats)) * d["cond"](t)
    return Pose(x=545.0, y=float(env.FLOOR_Y), facing=-1.0, turn=0.35, arm_r=arm, arm_l=d["arm_l"](t),
                look_x=lx, look_y=ly, head_tilt=d["tilt"](t), head_nod=d["nod"](t), head_turn=d["hturn"](t),
                brow_raise=d["brow"](t), smile=d["smile"](t), glow=d["glow"](t) * (0.85 + 0.25 * lv.rms),
                shoulders_up=d["shoulders"](t), lean=sway, **lv.quill)


def _beat_phase(t, beats):
    """Phase 0..1 between the surrounding beats (0 on a beat)."""
    if not beats or t < beats[0]:
        return 0.0
    lo, hi = 0, len(beats) - 1
    if t >= beats[-1]:
        return 0.0
    while hi - lo > 1:
        m = (lo + hi) // 2
        if beats[m] <= t:
            lo = m
        else:
            hi = m
    return (t - beats[lo]) / max(1e-3, beats[hi] - beats[lo])


def _draw_palm_light(c, t, qp, lv):
    """The music made visible at its source: a soft light in Quill's conducting palm that swells on each
    note of the intro and breathes with the music after (additive, small)."""
    T = _T()
    k = clamp((t - (T.first_note - 0.4)) / 0.4) * (1.0 - smoothstep((t - (T.final + 0.2)) / 1.2))
    if k <= 0.003:
        return
    hx, hy = Q.hand_pos(qp, "r")
    pulse = 0.0
    for o in T.onsets:
        if o > t:
            break
        if t - o < 1.2:
            pulse = max(pulse, math.exp(-(t - o) / 0.35) * (1.0 if o < T.theme else 0.45))
    a = k * (0.16 + 0.14 * lv.rms + 0.35 * pulse) * (1.0 - 0.6 * lv.freeze)
    glow(c, hx, hy, 46.0 + 10.0 * pulse, (170, 255, 240), 0.35 * a)
    glow(c, hx, hy, 15.0 + 4.0 * pulse, (225, 255, 250), 0.8 * a)


# =========================================================================== the cadet (passer-by)


def _C():
    """The cadet rig (anim/char_cadet.py), or None while it is not importable."""
    try:
        from anim import char_cadet as C
        return C
    except Exception:
        return None


CAD_SCALE = 1.0
CAD_FLOOR_IN = float(env.FLOOR_Y)          # in the doorway he walks on the wall line ...
CAD_FLOOR = 1185.0                         # ... and along the front of the room, nearer the camera than the bench
CAD_DOORWAY_X = (-110.0, 70.0)             # x range over which his floor line comes forward
CAD_STOP_X = 50.0                          # where he stops to gawk (his cup stays clear of Rae's face, x ~258)


@lru_cache(maxsize=1)
def _cad_keys():
    """(t, x, dx/dt) keys of the cadet's pelvis: a casual stroll in, a slow-down and stop to gawk (sip), a
    slightly brisker walk past Rae (cough) and in front of Quill (mutter, nod), slower while he glances back
    and waves, then off screen right. Hermite-interpolated (C1), so his speed changes are smooth."""
    T = _T()
    return (
        (T.cdoor - 0.25, -262.0, 88.0),        # a sleepy stroll
        (T.cdoor + 2.5, -20.0, 82.0),          # door_close sfx: the panel slides shut behind him
        (T.notice, 38.0, 36.0),                # he notices: slows ...
        (T.notice + 0.78, CAD_STOP_X, 0.0),    # ... and stops (heel strike: contact pose)
        (T.notice + 1.52, CAD_STOP_X, 0.0),    # (sips) ... walks on
        (T.notice + 2.72, 165.0, 120.0),
        (T.cough, 352.0, 112.0),               # passing in front of Rae's knees: the cough
        (T.c01_s, 465.0, 112.0),               # "Cool music, Quill." as he passes in front of him
        (T.qnod, 620.0, 96.0),                 # past Quill (clear of his face): the nod
        (T.cwave, 690.0, 52.0),                # glances back, waves
        (T.cwave + 1.02, 738.0, 46.0),
        (T.cexit, 985.0, 115.0),               # gone off screen right
        (T.cexit + 2.0, 1215.0, 115.0),
    )


def _herm(t, k0, k1):
    t0, p0, m0 = k0
    t1, p1, m1 = k1
    h = t1 - t0
    u = clamp((t - t0) / h)
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * h * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * h * m1)


def _cad_x(t):
    ks = _cad_keys()
    if t <= ks[0][0]:
        return ks[0][1] + (t - ks[0][0]) * ks[0][2]
    if t >= ks[-1][0]:
        return ks[-1][1] + (t - ks[-1][0]) * ks[-1][2]
    for i in range(1, len(ks)):
        if t < ks[i][0]:
            return _herm(t, ks[i - 1], ks[i])
    return ks[-1][1]


def _cad_floor(x):
    return lerp(CAD_FLOOR_IN, CAD_FLOOR, smoothstep((x - CAD_DOORWAY_X[0]) / (CAD_DOORWAY_X[1] - CAD_DOORWAY_X[0])))


@lru_cache(maxsize=1)
def _cad_advance():
    C = _C()
    if C is None:
        return 130.0
    base = Pose(x=0.0, y=CAD_FLOOR, facing=1.0, turn=0.35, scale=CAD_SCALE)
    fn = getattr(C, "walk_advance", None)
    if fn is not None:
        try:
            return float(fn(base))
        except Exception:
            pass
    return float(getattr(C, "WALK_ADVANCE", 130.0)) * CAD_SCALE


CAD_STOP_PHASE = 0.0          # walk phase (mod 1) at which he stands to gawk: contact pose, near foot forward


def _cad_phase(t):
    """Walk phase from the pelvis travel. The rig's stance foot moves exactly WALK_ADVANCE per cycle, linearly in
    phase, so x = x_stop + A * (phase - CAD_STOP_PHASE) keeps the planted foot still at any walking speed."""
    return CAD_STOP_PHASE + (_cad_x(t) - CAD_STOP_X) / _cad_advance()


def _cad_visible(t):
    T = _T()
    return T.cdoor - 0.3 <= t <= T.cexit + 0.9 and -330.0 < _cad_x(t) < 1080.0


def _cad_strikes():
    """Absolute times of his heel strikes (walk phase crossing a multiple of 0.5 while moving and on screen)."""
    T = _T()
    out = []
    t, dt = T.cdoor - 0.25, 1.0 / 240.0
    prev = _cad_phase(t)
    while t < T.cexit + 1.0:
        t += dt
        ph = _cad_phase(t)
        if math.floor(ph * 2.0 + 1e-9) > math.floor(prev * 2.0 + 1e-9):
            # bisect the crossing
            lo, hi, k = t - dt, t, math.floor(ph * 2.0 + 1e-9) / 2.0
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if _cad_phase(mid) < k:
                    lo = mid
                else:
                    hi = mid
            if _cad_x(hi) > -200.0:
                out.append(round(hi, 3))
        prev = ph
    return out


# coffee in his FAR hand (in front of his belly: across >= 0.3 draws the far arm over the body), so the
# camera-side hand is free for the cough and for the wave back toward Rae
CUP_SIDE = "l"


@lru_cache(maxsize=1)
def _cad_tracks():
    C = _C()
    T = _T()
    NO, CO, MU, ME_, QN, CW, CX = T.notice, T.cough, T.c01_s, T.c01_e, T.qnod, T.cwave, T.cexit
    sip0 = NO + 0.8                       # the sip (stopped, eyes on Rae over the cup)
    d = {"sip0": sip0}
    hold = _arm(C.ARMS["hold_cup"], across=0.34, elbow=88.0)
    sip = C.ARMS["sip_cup"]
    near = ArmPose(shoulder=4.0, elbow=12.0, wrist=0.0, hand="relaxed")
    mouth_ = C.ARMS["hand_to_mouth"]
    d["arm_cup"] = ArmTrack([(T.cdoor, hold), (sip0, hold), (sip0 + 0.32, ArmPose.blend(hold, sip, 0.8), "io"),
                             (sip0 + 0.42, sip, "out"), (sip0 + 0.78, sip), (sip0 + 0.9, ArmPose.blend(hold, sip, 0.8)),
                             (sip0 + 1.25, hold, "io"),
                             (MU + 0.95, hold), (MU + 1.2, _arm(hold, shoulder=16.0, elbow=96.0), "io"),   # a little
                             (QN + 0.2, _arm(hold, shoulder=16.0, elbow=96.0)), (QN + 0.55, hold, "io")])   # cup salute
    d["arm_free"] = ArmTrack([(T.cdoor, near), (CO - 0.3, near), (CO - 0.04, mouth_, "io"), (CO + 0.62, mouth_),
                              (CO + 0.95, _arm(near, shoulder=10.0, elbow=30.0), "io"), (CO + 1.3, near, "io")])
    d["wave"] = Track([(CW - 0.02, 0.0), (CW + 0.3, 0.88, "io"), (CW + 1.0, 0.88), (CW + 1.38, 0.0, "io")])
    d["turn"] = Track([(T.cdoor, 0.36)])
    d["hturn"] = Track([(NO - 0.05, 0.0), (NO + 0.3, -0.06), (NO + 1.6, -0.02), (NO + 2.4, -0.12), (NO + 3.0, 0.02),
                        (MU - 0.2, 0.02), (MU + 0.6, -0.16), (ME_, -0.3), (QN + 0.15, -0.34), (QN + 0.6, 0.0),
                        (CW - 0.12, 0.0), (CW + 0.2, -0.72, "out"), (CW + 1.15, -0.68), (CW + 1.6, 0.0, "io")])
    d["nod"] = Track([(T.cdoor, -0.1), (NO - 0.05, -0.1), (NO + 0.3, 0.12, "out"), (NO + 0.55, 0.06),
                      (NO + 0.8, -0.04), (NO + 1.2, 0.1), (sip0 + 0.3, 0.06), (sip0 + 1.0, 0.04), (CO - 1.2, -0.06),
                      (CO - 0.3, -0.12), (CO + 1.0, -0.12), (MU - 0.1, 0.1), (MU + 0.4, 0.22), (ME_, 0.16),
                      (QN + 0.1, 0.1), (QN + 0.3, -0.06, "out"), (QN + 0.55, 0.0), (CW, -0.02), (CW + 0.3, 0.04),
                      (CW + 1.4, 0.02), (CX, -0.06)])
    d["brow"] = Track([(T.cdoor, 0.05), (NO - 0.05, 0.05), (NO + 0.22, 0.9, "out"), (NO + 2.6, 0.75),
                       (CO - 0.6, 0.45), (CO + 1.0, 0.3), (MU, 0.4), (ME_, 0.35), (CW, 0.3), (CW + 0.3, 0.45),
                       (CW + 1.5, 0.25), (CX, 0.2)])
    d["wide"] = Track([(NO, 0.0), (NO + 0.18, 0.35, "out"), (NO + 1.4, 0.2), (CO - 0.5, 0.0)])
    d["lid"] = Track([(T.cdoor, 0.84), (NO, 0.86), (NO + 0.18, 1.0, "out"), (CO - 0.6, 0.95), (MU, 0.88),
                      (CW, 0.92), (CX, 0.88)])
    d["smile"] = Track([(T.cdoor, 0.0), (NO, 0.0), (MU + 0.7, 0.04), (ME_ - 0.1, 0.22), (QN + 0.6, 0.26),
                        (CW + 0.3, 0.3), (CW + 1.4, 0.18), (CX, 0.1)])
    d["open"] = Track([(NO, 0.0), (NO + 0.25, 0.14), (NO + 1.0, 0.1), (sip0 - 0.1, 0.0), (CO - 0.5, 0.0)])
    d["cough"] = Track([(CO - 0.12, 0.0), (CO + 0.02, 0.85, "out"), (CO + 0.62, 0.7), (CO + 0.9, 0.0, "io")])
    d["gaze"] = [
        (T.cdoor, (0.42, 0.18)),                   # strolling in, half asleep, eyes ahead
        (NO + 0.04, (0.42, -0.72)),                # ... the lights! (up at the swirl over Rae)
        (NO + 0.5, (0.78, 0.62)),                  # ... Rae
        (NO + 0.86, (0.5, -0.66)),                 # ... the lights
        (NO + 1.24, (0.8, 0.58)),                  # ... Rae again, over the rim of the cup
        (NO + 2.02, (0.46, -0.6), 0.3),            # walks on, eyes still up at it all
        (NO + 2.75, (0.62, 0.62), 0.3),            # a look down at her as he comes up to her ...
        (NO + 3.35, (0.02, 0.72), 0.25),           # ... and passes her
        (NO + 3.85, (0.46, 0.28), 0.25),           # ... eyes front, don't stare
        (CO - 0.15, (0.2, 0.5)),                   # the cough: eyes down
        (CO + 0.95, (0.4, 0.15), 0.25),
        (MU - 0.15, (0.12, -0.78), 0.2),           # up at Quill: "Cool music, Quill."
        (ME_ - 0.3, (-0.42, -0.7), 0.4),
        (QN + 0.5, (0.5, 0.05), 0.3),              # nodded at; walks on
        (CW + 0.06, (-0.95, 0.42), 0.18),          # glance back to Rae: the wave
        (CW + 1.25, (0.45, 0.08), 0.3),
    ]
    d["blinks"] = [(NO + 0.05, 0.12), NO + 1.95, (CO - 0.2, 0.22), (MU - 0.25, 0.16), (QN + 0.32, 0.18),
                   (CW + 0.02, 0.16), CW + 1.5, CX - 1.0]
    return d


def _cad_bounce(t):
    """Body jolts on the three bursts of cough_awkward.wav (+0.00, +0.26, +0.52 .. 0.64 s)."""
    T = _T()
    v = 0.0
    for off, a in ((0.0, 2.6), (0.26, 1.4), (0.53, 3.0)):
        x = (t - T.cough - off) / 0.22
        if 0.0 <= x < 1.0:
            v = max(v, a * math.sin(math.pi * min(1.0, x * 3.0)) * (1.0 - x) ** 1.5)
    return v


def _cadet_pose(t, lv):
    C = _C()
    if C is None:
        return None
    T = _T()
    d = _cad_tracks()
    x = _cad_x(t)
    gaze = _gaze_eval(t, d["gaze"], lambda name, tt: (0.4, 0.0))
    blink = _blinks(t, d["blinks"]) * C.blink(t)
    lid = d["lid"](t) * blink
    mo, mr = mouth("cadet", t)
    cough = d["cough"](t)
    jolt = _cad_bounce(t)
    wave = d["wave"](t)
    free = d["arm_free"](t)
    if wave > 0.0:
        # ARMS['wave'] (pop-free wiggle), lifted higher and further out toward Rae so it reads in the medium
        free = C.wave_arm(t - T.cwave, wave, base=free)
        free = _arm(free, shoulder=free.shoulder + 24.0 * wave, elbow=free.elbow - 14.0 * wave,
                    across=free.across - 0.2 * wave)
    stop = smoothstep((t - (T.notice + 0.55)) / 0.4) * (1.0 - smoothstep((t - (T.notice + 1.45)) / 0.4))
    light = lv.cadet if lv is not None else {}
    p = Pose(x=x, y=_cad_floor(x), scale=CAD_SCALE, facing=1.0, turn=d["turn"](t), walk=_cad_phase(t),
             head_turn=d["hturn"](t), head_nod=d["nod"](t) - 0.22 * cough + 0.012 * jolt,
             head_tilt=-2.0 * stop + 1.4 * noise1(t * 0.4, 31),
             lean=1.2 * stop * noise1(t * 0.5, 33) - 0.8 * jolt, bounce=jolt,
             shoulders_up=0.25 * cough + 0.04 * jolt,
             lid_l=lid, lid_r=lid, look_x=gaze[0], look_y=gaze[1], eye_wide=d["wide"](t),
             brow_raise=d["brow"](t), mouth_open=d["open"](t) + 0.85 * mo + 0.3 * cough,
             mouth_round=clamp(mr + 0.5 * cough), smile=d["smile"](t) * (1.0 - cough), squint=0.6 * cough,
             brow_furrow=0.3 * cough, arm_r=free, arm_l=d["arm_cup"](t), mug=CUP_SIDE, **light)
    return p


@lru_cache(maxsize=256)
def _cadet_head(t):
    C = _C()
    if C is None:
        return None
    p = _cadet_pose(t, None)
    if p is None:
        return None
    return C.head_center(p)


def _draw_cadet(c, t, lv, door):
    C = _C()
    if C is None or not _cad_visible(t):
        return
    p = _cadet_pose(t, lv)
    if p is None:
        return
    if p.x < env.DOOR_X1 + 90 and door < 0.999 and t < _T().cdoor + 0.6:
        # still behind the (part-open) door panel (while it closes he is out in front of it)
        c.save()
        c.clipRect(skia.Rect(env.DOOR_X0, env.DOOR_TOP, env.DOOR_X1 - env.DOOR_W * clamp(door), env.FLOOR_Y + 4),
                   skia.ClipOp.kDifference, True)
        C.draw(c, p, t)
        c.restore()
    else:
        C.draw(c, p, t)


@lru_cache(maxsize=1)
def _door_track():
    T = _T()
    shut = T.cdoor + 2.5                           # door_close sfx; its thunk lands at +0.67
    return Track([(T.cdoor, 0.0), (T.cdoor + 0.55, 1.0, "out"), (shut, 1.0), (shut + 0.67, 0.0, "in")])


def _door(t):
    T = _T()
    if t < T.cdoor or t > T.cdoor + 3.3:
        return 0.0
    return _door_track()(t)


# =========================================================================== memories


# kind, birth (s after sym_memories_start), life, radius, layer, ease exponent, rising path (stage coords).
# Left column x ~100-150 (clear of the frame edge and of her face), right column x ~390-440 (between her and
# Quill, behind his raised arm). Front/back alternate so they float around her, never across her face.
_MEM1 = (
    ("car_window", 0.0, 5.6, 92.0, "back", 1.5, ((150, 1190), (116, 990), (122, 800), (140, 600))),
    ("hands", 2.1, 5.7, 90.0, "back", 1.7, ((436, 1210), (446, 990), (420, 800), (416, 650))),
    ("dog_door", 4.2, 5.6, 90.0, "front", 1.5, ((96, 1240), (120, 1020), (100, 830), (100, 640))),
    ("kitchen_dawn", 6.3, 5.6, 88.0, "back", 1.7, ((404, 1230), (424, 1000), (436, 830), (424, 680))),
    ("friends_table", 8.2, 5.6, 90.0, "front", 1.5, ((132, 1250), (108, 1030), (116, 840), (124, 660))),
    ("sea_sunset", 10.9, 6.0, 86.0, "back", 2.3, ((424, 1260), (404, 990), (392, 822), (386, 772))),
)
_MEM_INDEX = {m[0]: i for i, m in enumerate(_MEM1)}
# the climax: all six glow in an arch over the blazing galaxy (angles: 270 = straight up)
_HALO_C = (352.0, 470.0)
_HALO_R = (290.0, 330.0)
_HALO_BR = 68.0
_MEM2 = (("sea_sunset", 205.0), ("car_window", 231.0), ("hands", 257.0), ("kitchen_dawn", 283.0),
         ("dog_door", 309.0), ("friends_table", 335.0))


def _mem1(i, t, clamp_age=False):
    """(layer, kind, x, y, r, alpha, age, glow) of rising memory i at t, or None when not alive."""
    T = _T()
    kind, off, life, r, layer, ex, path = _MEM1[i]
    age = t - (T.mem + off)
    if clamp_age:
        age = clamp(age, 0.0, life)
    elif not 0.0 <= age <= life:
        return None
    u = age / life
    x, y = _catmull(path, 1.0 - (1.0 - u) ** ex)
    x += 8.0 * math.sin(age * 0.8 + i * 1.7)
    y += 5.0 * math.sin(age * 0.65 + i * 2.3)
    a = smoothstep(age / 0.9) * smoothstep((life - age) / 1.3)
    rr = r * (0.8 + 0.2 * ease_out(age / 1.4))
    return (layer, kind, x, y, rr, a, age, 0.0)


def _memories(t):
    """[(layer, kind, x, y, r, alpha, age, glow)]"""
    T = _T()
    out = []
    for i in range(len(_MEM1)):
        m = _mem1(i, t)
        if m is not None:
            out.append(m)
    if t >= T.climax - 0.05:
        age0 = t - T.climax
        fade = 1.0 - smoothstep((t - T.final - 0.2) / 2.4)
        if fade > 0.002:
            gx, gy = _HALO_C
            rx, ry = _HALO_R
            g = 1.0 - 0.55 * smoothstep(age0 / 3.0) + 0.25 * smoothstep((t - T.peak) / 1.5) * (
                1 - smoothstep((t - T.peak - 3.0) / 3.0))
            for i, (kind, ang) in enumerate(_MEM2):
                ai = age0 - 0.07 * abs(i - 2.5)            # they blossom out of the core, middle ones first
                if ai <= 0.0:
                    continue
                appear = ease_out(clamp(ai / 0.75))
                a_ = math.radians(ang + 3.0 * math.sin(age0 * 0.35 + i * 1.3))
                k = (0.5 + 0.5 * appear) * (1.0 + 0.03 * math.sin(age0 * 0.5 + i * 2.1))
                x = gx + math.cos(a_) * rx * k
                y = gy + math.sin(a_) * ry * k - 24.0 * (1 - fade)
                rr = _HALO_BR * (0.5 + 0.5 * appear) * (0.85 + 0.15 * fade)
                out.append(("back", kind, x, y, rr, smoothstep(ai / 0.3) * fade, age0 + 6.0 + i, g))
    return out


def _face_y(rp):
    return R.head_center(rp)[1]


def _bubble_light(rp, mems):
    """Memory bubbles are warm lights: the nearer (and brighter) they are to Rae's face, the more they
    warm her rim and lift her key a little."""
    hx, hy = R.head_center(rp)
    w = 0.0
    for (_, _, x, y, r, a, _, g) in mems:
        dd = max(0.0, math.hypot(x - hx, y - hy) - r)
        w += a * math.exp(-dd / 160.0) * (0.6 if g > 0 else 1.0)
    w = clamp(w)
    if w <= 0.01:
        return rp
    rc = rp.rim_color if isinstance(rp.rim_color, tuple) else C_WIN
    return rp.copy(light=rp.light + 0.07 * w, rim=min(1.0, rp.rim + 0.12 * w),
                   rim_color=_mix(rc, (255, 200, 150), 0.55 * w),
                   tint=_mix(rp.tint, (70, 42, 24), 0.5 * w))


def _draw_memories(c, t, layer, mems, k=1.0):
    for (lay, kind, x, y, r, a, age, g) in mems:
        if lay == layer and a * k > 0.003:
            fx.draw_memory(c, t, kind, x, y, r, alpha=a * k, age=age, glow=g, develop=g <= 0.0)


# =========================================================================== note motes (intro)


_MOTE_COLS = ((150, 255, 236), (255, 222, 170), (214, 196, 255), (255, 244, 226))
_MOTE_ANG = (-25.0, 205.0, -70.0, 160.0, 25.0, 240.0, -115.0, 125.0)     # around her head, both sides


@lru_cache(maxsize=64)
def _mote_src(i):
    """Where intro mote i is born: Quill's conducting palm at its note."""
    T = _T()
    o = T.onsets[i]
    return Q.hand_pos(_quill_pose(o, _levels(o)), "r")


def _note_mote(i, t):
    """(x, y, size, alpha, color) of the mote born on intro note i, or None.
    Each piano/celesta note of the intro releases a mote from Quill's palm that drifts over to Rae and
    lingers in the air around her (never across her face)."""
    T = _T()
    if i >= len(T.onsets):
        return None
    o = T.onsets[i]
    age = t - o
    if age < 0 or o >= T.theme:
        return None
    sx, sy = _mote_src(i)
    hx, hy = _rae_face_ref()
    h = lambda k: ((i * 7919 + k * 104729) % 1000) / 1000.0  # noqa: E731
    ang = math.radians(_MOTE_ANG[i % len(_MOTE_ANG)] + 24.0 * (h(1) - 0.5))
    rad = 125.0 + 95.0 * h(2)
    dx, dy = hx + math.cos(ang) * rad * 1.05, hy - 20.0 + math.sin(ang) * rad * 1.25
    if i == 0:                                 # the first one settles just in front of her, at eye height
        dx, dy = hx + 95.0, hy - 30.0
    travel = 2.4 + 0.6 * h(3)
    u = smoothstep(age / travel)
    cx_, cy_ = (sx + dx) / 2.0, min(sy, dy) - 90.0 - 60.0 * h(4)
    x = (1 - u) ** 2 * sx + 2 * (1 - u) * u * cx_ + u * u * dx
    y = (1 - u) ** 2 * sy + 2 * (1 - u) * u * cy_ + u * u * dy
    drift = max(0.0, age - travel)
    x += 10.0 * math.sin(drift * (0.5 + 0.4 * h(5)) + 6.0 * h(6)) * smoothstep(drift / 1.5)
    y -= 7.0 * drift
    a = smoothstep(age / 0.18)
    a *= 1.0 - smoothstep((t - (T.theme + 1.5 + 2.0 * h(7))) / 2.5)
    if a <= 0.003:
        return None
    size = 1.0 + 0.9 * math.exp(-age / 0.35)
    return (x, y, size * (0.85 + 0.3 * h(8)), a, _MOTE_COLS[i % len(_MOTE_COLS)])


def _draw_note_motes(c, t, rms):
    T = _T()
    if t < T.first_note - 0.05 or t > T.theme + 6.0:
        return
    for i in range(len(T.onsets)):
        if T.onsets[i] > t or T.onsets[i] >= T.theme:
            break
        m = _note_mote(i, t)
        if m is None:
            continue
        x, y, sz, a, colr = m
        tw = 0.85 + 0.15 * math.sin(t * (2.0 + 0.3 * i) + i) + 0.2 * rms
        glow(c, x, y, 26.0 * sz, colr, 0.2 * a * tw)
        glow(c, x, y, 9.0 * sz, colr, 0.65 * a * tw)
        glow(c, x, y, 3.2 * sz, (255, 255, 255), min(1.0, 0.95 * a))


# =========================================================================== the last mote


# path relative to her face: from above-right, down across in front of her chin, toward her hand on her chest
_FM_PATH = ((84.0, -132.0), (66.0, -62.0), (30.0, 18.0), (12.0, 64.0), (2.0, 106.0))


def _final_mote(t):
    """(x, y, brightness, glint) of the last mote drifting down in front of Rae's face, or None."""
    T = _T()
    t0 = T.celesta
    out_t = T.end - 0.95
    if t < t0 - 0.05 or t > out_t + 0.4:
        return None
    hx, hy = _last_face()
    u = clamp((t - t0) / (out_t - t0))
    px, py = _catmull(_FM_PATH, 0.55 * smoothstep(u) + 0.45 * u)
    x = hx + px + 6.0 * math.sin((t - t0) * 1.4)
    y = hy + py
    b = smoothstep((t - t0) / 0.5)
    # a little brighter on each celesta note ...
    for o in T.onsets:
        if t0 - 0.2 <= o <= t:
            b += 0.4 * math.exp(-(t - o) / 0.4)
    # ... a last glint, and it goes out
    gl = math.exp(-((t - (out_t - 0.3)) / 0.11) ** 2)
    b += 0.8 * gl
    b *= 1.0 - smoothstep((t - (out_t - 0.2)) / 0.45)
    if b <= 0.003:
        return None
    return (x, y, b, gl)


def _draw_final_mote(c, t):
    m = _final_mote(t)
    if m is None:
        return
    x, y, b, gl = m
    tw = 0.92 + 0.08 * math.sin(t * 5.3)
    glow(c, x, y, 100.0, (255, 226, 180), 0.15 * b * tw)
    glow(c, x, y, 38.0, (255, 240, 214), 0.48 * b * tw)
    glow(c, x, y, 15.0, (255, 250, 236), 0.85 * b)
    glow(c, x, y, 6.5, (255, 255, 255), min(1.0, 1.1 * b))
    if gl > 0.02:                       # the last glint: a soft four-point star
        p = skia.Paint(AntiAlias=True, Color=skia.Color(255, 246, 228, int(255 * min(1.0, 0.75 * gl))))
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(2.2)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.4))
        p.setBlendMode(skia.BlendMode.kPlus)
        L = 34.0 * gl
        c.drawLine(x - L, y, x + L, y, p)
        c.drawLine(x, y - L * 0.8, x, y + L * 0.8, p)


# =========================================================================== cameras


@lru_cache(maxsize=1)
def _rae_face_ref():
    """Rae's face (seated on the bench, turned toward Quill): the reference for gaze targets and singles."""
    p = Pose(x=SEAT_X, y=float(env.FLOOR_Y), facing=1.0, turn=0.35, sit=1.0, seat_y=float(env.BENCH_SEAT_Y))
    return R.head_center(p)


@lru_cache(maxsize=1)
def _last_face():
    """Her face at sym_celesta_echo (the last shot and the last mote are framed on it)."""
    return _shot_face(_T().celesta)


@lru_cache(maxsize=1)
def _quill_face_ref():
    return Q.head_center(Pose(x=545.0, y=float(env.FLOOR_Y), facing=-1.0, turn=0.35))


def _face_cam(fx_, fy_, z, sx, sy):
    """Camera at zoom z that puts stage point (fx_, fy_) at screen (sx, sy)."""
    return Camera(fx_ + (W / 2 - sx) / z, fy_ + (H / 2 - sy) / z, z)


@lru_cache(maxsize=1)
def _shots():
    T = _T()
    q0, q1 = _bt(29.61), _db(31.5)
    c_notice = _bt(37.53)                  # the beat just before he notices
    c_cross = _bt(40.89)                   # cut on his wipe across Rae
    c_mutter = _bt(42.65)                  # just before "Cool music, Quill."
    c_rae = T.cwave + 0.55                 # on the action: his wave is up -> her answer
    c_exit = _bt(47.18)
    return (
        ("two", T.start, T.first_note),
        ("rae_med", T.first_note, T.theme),
        ("wide_rib", T.theme, _db(14.22)),
        ("rae_cu1", _db(14.22), _db(17.61)),
        ("mem_med", _db(17.61), q0),
        ("quill_cu", q0, q1),
        ("rae_cu2", q1, T.cdoor),
        ("cad_enter", T.cdoor, c_notice),
        ("cad_notice", c_notice, c_cross),
        ("cad_cross", c_cross, c_mutter),
        ("cad_mutter", c_mutter, c_rae),
        ("rae_wave", c_rae, c_exit),
        ("exit_wide", c_exit, T.gp),
        ("pause", T.gp, T.climax),
        ("burst", T.climax, T.tear),
        ("tear", T.tear, T.celesta),
        ("last", T.celesta, T.end + 1.0),
    )


def _cut(name):
    """Start time of shot `name`."""
    for n, a, _ in _shots():
        if n == name:
            return a
    raise KeyError(name)


def _shot_at(t):
    for name, a, b in _shots():
        if a <= t < b:
            return name, a, b
    s = _shots()
    return (s[0] if t < s[0][1] else s[-1])


# the cathedral: the wide the tear close-up pulls back to, and the two-shot it drifts into on the final chord
_CATHEDRAL = Camera(352.0, 790.0, 0.84)
_CATHEDRAL2 = Camera(353.0, 787.0, 0.83)
_CODA_TWO = Camera(366.0, 774.0, 1.0)
_PULL = 5.2         # seconds of the pull-back from sym_peak
_BUMP = (140.0, 0.62)   # lateral swing toward Quill during the pull-back (screen px, end of the swing in v)


def _tear_cam(t, a):
    T = _T()
    fk = _shot_face(a)
    z0, z1 = 3.2, 3.36
    if t < T.peak:
        return _face_cam(fk[0], fk[1], lerp(z0, z1, smoothstep((t - a) / (T.peak - a))), 352.0, 560.0)
    pe = T.peak + _PULL
    if t < pe:
        # one continuous pull-back from the close-up to the cathedral wide. Parametrised by her face's screen
        # position + zoom; the lateral term swings toward Quill as he is revealed, so his head crosses the
        # frame edge quickly instead of sitting half in frame.
        u = (t - T.peak) / _PULL
        v = smoothstep(smoothstep(u))
        cw = _CATHEDRAL
        z = z1 * (cw.zoom / z1) ** v
        s_end = (W / 2 + (fk[0] - cw.cx) * cw.zoom, H / 2 + (fk[1] - cw.cy) * cw.zoom)
        bump = _BUMP[0] * math.sin(math.pi * clamp(v / _BUMP[1])) if v < _BUMP[1] else 0.0
        sx = lerp(352.0, s_end[0], v) + bump
        sy = lerp(560.0, s_end[1], v)
        return _face_cam(fk[0], fk[1], z, sx, sy)
    if t < T.final:
        return Camera.lerp(_CATHEDRAL, _CATHEDRAL2, smoothstep((t - pe) / (T.final - pe)))
    return Camera.lerp(_CATHEDRAL2, _CODA_TWO, ease_in_out((t - T.final) / (T.celesta - T.final)))


def _camera(name, t, a, b):
    T = _T()
    u = clamp((t - a) / max(1e-3, b - a))
    fs = _rae_face_ref()
    if name == "two":
        return Camera.lerp(Camera(396.0, 742.0, 1.1), Camera(392.0, 736.0, 1.14), smoothstep(u))
    if name == "rae_med":
        return _face_cam(fs[0], fs[1], lerp(1.72, 1.9, smoothstep(u)), 332.0, 496.0)
    if name == "wide_rib":
        return Camera.lerp(Camera(350.0, 752.0, 0.9), Camera(318.0, 768.0, 1.1), smoothstep(u))
    if name == "rae_cu1":
        return _face_cam(fs[0], fs[1], lerp(2.14, 2.26, smoothstep(u)), lerp(298.0, 304.0, u), 590.0)
    if name == "mem_med":
        return _face_cam(fs[0], fs[1], lerp(1.06, 1.13, smoothstep(u)), lerp(284.0, 290.0, u),
                         lerp(590.0, 572.0, smoothstep(u)))
    if name == "quill_cu":
        qx, qy = _quill_face_ref()
        return _face_cam(qx, qy, lerp(2.35, 2.48, u), 420.0, 520.0)
    if name == "rae_cu2":
        return _face_cam(fs[0], fs[1], lerp(1.98, 2.06, smoothstep(u)), 288.0, 522.0)
    if name == "cad_enter":
        # the whole lounge, door included (as S1's opening wide); the galaxy starts to gather in the window
        return Camera.lerp(Camera(298.0, 690.0, 0.72), Camera(306.0, 702.0, 0.755), smoothstep(u))
    if name == "cad_notice":
        # medium two-shot: the cadet (left, foreground) gawking at Rae and the lights
        return Camera.lerp(Camera(202.0, 652.0, 1.55), Camera(214.0, 646.0, 1.6), smoothstep(u))
    if name == "cad_cross":
        return Camera.lerp(Camera(404.0, 776.0, 1.0), Camera(416.0, 770.0, 1.03), smoothstep(u))
    if name == "cad_mutter":
        # medium: Quill conducting, the cadet passing in front of him (pans a little with him)
        return Camera.lerp(Camera(578.0, 640.0, 1.45), Camera(622.0, 634.0, 1.5), ease_in_out(u))
    if name == "rae_wave":
        return _face_cam(fs[0], fs[1], lerp(1.96, 2.02, smoothstep(u)), 300.0, 520.0)
    if name == "exit_wide":
        return Camera.lerp(Camera(452.0, 792.0, 0.8), Camera(360.0, 770.0, 1.1), ease_in_out(u))
    if name == "pause":
        fk = _shot_face(a)
        return _face_cam(fk[0], fk[1], lerp(3.25, 3.4, u), 350.0, 600.0)
    if name == "burst":
        e = ease_out(clamp((t - a) / 1.6))
        return Camera(352.0, 790.0 - 6.0 * e, lerp(0.86, 0.78, e))
    if name == "tear":
        return _tear_cam(t, a)
    if name == "last":
        fk = _last_face()
        v = ease_in_out(clamp((t - a) / (T.end - 0.6 - a)))
        return _face_cam(fk[0], fk[1], 1.9 * (2.0 / 1.9) ** v, lerp(345.0, 330.0, v), lerp(532.0, 520.0, v))
    return Camera()


@lru_cache(maxsize=16)
def _shot_face(t):
    """Rae's actual face position at time t (used to frame a close-up from its first frame)."""
    lv = _levels(t)
    return R.head_center(_rae_pose(t, lv))


# =========================================================================== drawing


_RIB_AREA = (-140.0, 60.0, 860.0, 1260.0)
_AIR = (20.0, 230.0, 700.0, 980.0)


def _draw_world(c, t, cam, shot, lv, rp, qp, mems):
    T = _T()
    tw = _freeze_clock(t)
    door = _door(t)
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, tw, light=lv.room, door=door, swirl=lv.swirl, window_bright=lv.wb)
    gx, gy = env.GALAXY_CENTER
    lb = lv.lburst * clamp(1.08 - 0.4 * cam.zoom, 0.2, 0.78)      # the core never blows out in the closer shots
    if lb > 0.003:
        fx.draw_light_burst(c, t, gx, gy + 20.0, lb, radius=1050.0)
    _draw_shockwave(c, t)
    if lv.rib > 0.003:
        fx.draw_ribbons(c, _rib_clock(t, lv.burst), intensity=lv.rib, env=lv.rms, area=_RIB_AREA, seed=3,
                        freeze=0.0, burst=lv.burst, alpha=1.0 - 0.18 * smoothstep(lv.freeze), width=1.25)
    if lv.sparkle_a > 0.01 and t >= T.first_note - 0.1:
        fx.draw_note_sparkles(c, t, T.onsets, area=_AIR, seed=2, life=1.9, alpha=0.85 * lv.sparkle_a,
                              colors=("teal_glow", "amber_soft", "#D9C8FF"), size=0.85)
    last = shot == "last"
    # the last shot belongs to the one last mote: the dust clears and the falling sparks stay behind her
    dust = 1.0 - smoothstep((t - (T.celesta - 1.5)) / 1.5)
    if lv.motes > 0.003 and dust > 0.003:
        fx.draw_motes(c, tw, area=_RIB_AREA, density=lv.motes * 0.6, env=lv.rms, color="teal_glow",
                      seed=5, rise=14.0, alpha=0.8 * dust)
    if last and lv.sparks > 0.003:
        _draw_sparks(c, t, lv.sparks * 0.75)
    mk = 0.45 if shot == "quill_cu" else 1.0          # memories near Rae sit out of focus behind Quill's close-up
    _draw_memories(c, t, "back", mems, mk)
    R.draw(c, rp, t)
    bm = _bench_mug(t)
    if bm is not None:
        # the mug stands on the near edge of the seat, in front of her thigh (where the in-hand mug was drawn)
        _draw_bench_mug(c, bm, rp)
    if shot == "quill_cu":
        with Layer(c):
            Q.draw(c, qp, t)
            _quill_light_band(c, t, qp)
    else:
        Q.draw(c, qp, t)
    _draw_palm_light(c, t, qp, lv)
    _draw_cadet(c, t, lv, door)
    # foreground: the floor-edge shadow; while the cadet comes through the door, also the wall + jamb left of
    # the doorway (no lintel: it would cut the light; the wall redraw is identical to what is under it otherwise)
    if T.cdoor - 0.3 <= t <= T.cdoor + 3.4:
        env.draw_lounge_front(c, t, light=lv.room, door=door, lintel=False)
    else:
        c.save()
        c.clipRect(skia.Rect(-2000.0, 1450.0, 3000.0, 4000.0))
        env.draw_lounge_front(c, t, light=lv.room, lintel=False)
        c.restore()
    _draw_note_motes(c, t, lv.rms)
    _draw_memories(c, t, "front", mems, mk)
    if lv.motes > 0.003 and dust > 0.003:
        fx.draw_motes(c, tw, area=_RIB_AREA, density=lv.motes * 0.45, env=lv.rms, color="amber_soft",
                      seed=9, rise=10.0, alpha=0.75 * dust, size=0.9)
    if lv.sparks > 0.003 and not last:
        _draw_sparks(c, t, lv.sparks)
    _draw_final_mote(c, t)
    c.restore()


def _draw_sparks(c, t, amount, k=1.6):
    """fx.draw_falling_sparks drawn k times larger (the canvas is scaled about the area centre; area, fall
    speed and density are compensated so they still cover the same region at the same speed)."""
    x0, y0, x1, y1 = _RIB_AREA
    ax, ay = (x0 + x1) / 2, (y0 + y1) / 2
    c.save()
    c.translate(ax, ay)
    c.scale(k, k)
    c.translate(-ax, -ay)
    area = (ax + (x0 - ax) / k, ay + (y0 - ay) / k, ax + (x1 - ax) / k, ay + (y1 - ay) / k)
    fx.draw_falling_sparks(c, t, area=area, amount=amount, seed=4, fall=24.0 / k, density=1.6 * k * k * 0.55)
    c.restore()


def _draw_shockwave(c, t):
    """The burst: a soft ring of light racing out of the galaxy core (additive, no full-frame wash)."""
    T = _T()
    age = t - T.climax
    if not 0.0 <= age < 1.4:
        return
    gx, gy = env.GALAXY_CENTER
    u = age / 1.4
    r = 40.0 + 1100.0 * ease_out(u)
    w = 90.0 + 180.0 * u
    a = 0.36 * (1.0 - u) ** 1.5 * smoothstep(age / 0.08)
    cols = [skia.Color(255, 236, 214, 0), skia.Color(255, 236, 214, int(255 * a)), skia.Color(220, 200, 255, 0)]
    r0 = max(0.0, r - w)
    sh = skia.GradientShader.MakeRadial((gx, gy), r + w, cols, [r0 / (r + w), r / (r + w), 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    p.setBlendMode(skia.BlendMode.kPlus)
    c.drawCircle(gx, gy, r + w, p)


def _quill_light_band(c, t, qp):
    """A soft band of ribbon light sliding across Quill during the intercut (drawn src-atop inside his
    own layer, so it only lights him)."""
    a, b = _shot_at(t)[1:]
    u = (t - a) / max(0.5, b - a)
    hx, hy = Q.head_center(qp)
    cx = hx + lerp(-150.0, 150.0, smoothstep(u))
    col = _mix(C_TEAL, C_AMBER, smoothstep(u))
    alpha = 0.38 * math.sin(math.pi * clamp(u * 1.1))
    if alpha <= 0.01:
        return
    sh = skia.GradientShader.MakeLinear(
        [(cx - 70.0, hy - 40.0), (cx + 70.0, hy + 40.0)],
        [skia.Color(*col, 0), skia.Color(*col, int(255 * alpha)), skia.Color(*col, 0)], [0.0, 0.5, 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    p.setBlendMode(skia.BlendMode.kSrcATop)
    c.drawRect(skia.Rect(hx - 400, hy - 300, hx + 400, hy + 900), p)


def render(canvas, t):
    name, a, b = _shot_at(t)
    lv = _levels(t)
    mems = _memories(t)
    rp = _rae_pose(t, lv)
    rp = _bubble_light(rp, mems)
    fm = _final_mote(t)
    if fm is not None:
        k = fm[2] * clamp(1.0 - abs(fm[1] - _face_y(rp)) / 220.0)
        rp = rp.copy(light=rp.light + 0.06 * k, rim_color=_mix(rp.rim_color, (255, 226, 186), 0.6 * k))
    qp = _quill_pose(t, lv)
    if name == "quill_cu":
        # the close-up's own light is there from its first frame (no auto-exposure ramp)
        qp = qp.copy(light=qp.light + 0.1, rim=qp.rim + 0.15)
    cam = _camera(name, t, a, b)
    _draw_world(canvas, t, cam, name, lv, rp, qp, mems)
    canvas.resetMatrix()
    fx.draw_vignette(canvas, lv.vign)
    if lv.flash > 0.003:
        fx.draw_flash(canvas, lv.flash, color="#FFF6E8")
