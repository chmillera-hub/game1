"""S2 -- "The Symphony" (BIBLE section 4 S2): the heart of the film.

Quill raises his hand, the lounge goes dark, and the music fills the room with light: note motes,
breathing ribbons, memory bubbles, a galaxy forming in the window. Rae melts from a skeptical smirk into
awe, sets her mug on the bench and slides to her knees; grand pause; the BURST; one tear and a trembling
smile; the cathedral pull-back; sparks fall like snow and a last mote goes out in front of her face.

Every time is derived from named beats (core.beat / line_start / scene_span) or from the symphony's own
music data (envelopes.json downbeats / beats / onsets). render(canvas, t) is a pure function of t.

Shot list (absolute times only for orientation -- see _shots()); hard cuts only, all on beats:
  two       sym_quill_raise -> 1st note        TWO-SHOT: Quill lifts his hand, the lights dim
  rae_med   1st note -> sym_theme1             MEDIUM Rae: each intro note sends a mote from his palm to her
  wide_rib  sym_theme1 -> bar 5                WIDE push: the ribbons wake; the mug lowers to her lap
  rae_cu1   bar 5 -> bar 6                     MEDIUM CLOSE Rae: brows lift, lips part, pupils wide
  mem_med   bar 6 -> beat before bar 9         MEDIUM-WIDE two-shot: six memories rise around her; "...oh"; tears well
  quill_cu  -> bar 9                           CLOSE Quill watching her, ribbon light across his face
  rae_cu2   bar 9 -> sym_build                 MEDIUM CLOSE Rae: welled tears; the sunset memory beside her; a smile
  build     sym_build -> sym_grand_pause       ONE TAKE: wide on the galaxy forming, a slow push-in while she sets the
                                               mug on the bench and slides to her knees
  pause     sym_grand_pause -> sym_climax      CLOSE Rae: eyes wide and wet, everything holds its breath
  burst     sym_climax -> sym_tear_roll        WIDE: the BURST, the galaxy blazing, the memories glow in an arch
  tear      sym_tear_roll -> sym_celesta_echo  CLOSE Rae: one tear, a trembling smile; from sym_peak one pull-back to
                                               the cathedral wide; on the final chord a drift in to the two-shot while
                                               the ribbons fall as sparks and Quill lowers his hand
  last      sym_celesta_echo -> end            MEDIUM CLOSE Rae: the last mote drifts down in front of her face and
                                               goes out (ends exactly on the framing S3 opens with)
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
                       ("kneel", "sym_kneel_start"), ("gp", "sym_grand_pause"), ("climax", "sym_climax"),
                       ("kdone", "sym_kneel_done"), ("tear", "sym_tear_roll"), ("peak", "sym_peak"),
                       ("final", "sym_final_chord"), ("celesta", "sym_celesta_echo")):
        setattr(n, attr, beat(name))
    n.oh_s, n.oh_e = line_start("r09"), line_end("r09")
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


# palette for light (rgb tuples)
C_WIN = (159, 182, 255)
C_TEAL = (127, 255, 233)
C_AMBER = (255, 210, 154)
C_VIOLET = (183, 156, 255)
C_WARM = (255, 228, 196)
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
    d["swirl"] = Track([(T.build, 0.0), (T.kneel + 3.5, 0.82, "io"), (CL - 0.2, 0.93), (CL + 1.2, 1.0),
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
    return lv


# =========================================================================== Rae


SEAT_X = 230.0
KNEEL_X = 255.0
MUG_SPOT = (330.0, float(env.BENCH_SEAT_Y))     # BIBLE section 9: the mug rests on the bench here

# Far (left) arm. The rig's far-arm targeting is discontinuous for `across` between ~0.15 and ~0.27 (and its
# draw layer flips at 0.25), so `across` is never animated through that band: it changes only on cuts
# (two -> rae_med, tear -> last) and otherwise stays >= 0.35 (hand placed on her body, drawn over it).
LAP_S1 = ArmPose(shoulder=15.0, elbow=55.0, wrist=0.0, hand="relaxed")             # S1's last far-arm pose
LAP_L = ArmPose(shoulder=8.0, elbow=40.0, wrist=6.0, hand="relaxed", across=0.35)   # far hand on top of her knee
HOLD_L = ArmPose(shoulder=20.0, elbow=80.0, wrist=6.0, hand="relaxed", across=0.45)  # holding her middle (the slide)
HEART_L = ArmPose(shoulder=12.0, elbow=118.0, wrist=10.0, hand="open", across=0.58)  # crossed over the other: both
#                                                                                      hands on her heart
THIGH_L = ArmPose(shoulder=14.0, elbow=30.0, wrist=4.0, hand="relaxed", across=0.35)  # back down on her thigh
THIGH_S3 = ArmPose(shoulder=12.0, elbow=26.0, wrist=4.0, hand="relaxed")              # = S3's first far-arm pose


@lru_cache(maxsize=1)
def _rae_tracks():
    T = _T()
    S, D, F1, TH, MG, ME = T.start, T.dim, T.first_note, T.theme, T.mug, T.mem
    OH, GL, BU, KN, GP, CL, KD, TR, PK, FC, CE, E = (T.oh, T.glis, T.build, T.kneel, T.gp, T.climax, T.kdone,
                                                      T.tear, T.peak, T.final, T.celesta, T.end)
    d = {}
    # ---- the slide from the bench to her knees (KN .. KD)
    d["place_t"] = KN + 2.1           # the mug touches the bench
    d["mug_back_t"] = KN + 5.65       # the bench mug goes behind her: mid-slide, where nothing of her overlaps it
    # rig limitation: both legs share one kneel value, so "one knee, then the other" is staged as a weight
    # shift forward, a slow 2 s descent onto the first knee (a lean + tilt to that side), then a second
    # small drop and a tilt back as the other knee comes down
    d["kneel"] = Track([(KN + 4.4, 0.0), (KN + 6.4, 0.62, "io"), (KN + 6.62, 0.66, "out"), (KN + 7.25, 0.8, "io"),
                        (CL + 0.15, 0.81), (KD, 1.0, "io")])
    d["x"] = Track([(KN + 3.3, SEAT_X), (KN + 4.5, SEAT_X + 7.0, "io"), (KN + 6.4, SEAT_X + 18.0, "io"),
                    (KN + 7.25, SEAT_X + 22.0, "io"), (CL, SEAT_X + 22.5), (KD, KNEEL_X, "io")])
    d["turn"] = Track([(KN + 4.0, 0.35), (KD, 0.3)])
    d["lean"] = Track([(S, 2.0), (S + 1.2, 1.0), (F1 + 2.0, 0.5), (TH - 0.5, 2.0), (MG + 1.5, 3.0), (ME, 2.0),
                       (OH - 0.3, 4.0), (BU, 2.0), (KN, 2.0), (KN + 0.6, 4.5), (KN + 2.1, 6.0), (KN + 2.8, 3.0),
                       (KN + 3.4, 3.0), (KN + 4.5, 11.0, "io"), (KN + 5.6, 9.0), (KN + 6.4, 5.5),
                       (KN + 6.58, 7.5, "out"), (KN + 7.3, 2.0), (GP, 1.0), (CL, 1.0), (CL + 0.5, -3.5, "out"),
                       (KD + 0.6, 0.0), (E, 0.5)])
    d["bounce"] = Track([(KN + 6.3, 0.0), (KN + 6.46, 3.2, "out"), (KN + 6.8, 0.6), (KN + 7.02, 0.6),
                         (KN + 7.2, 2.6, "out"), (KN + 7.75, 0.0), (CL, 0.0), (CL + 0.3, 2.5, "out"),
                         (CL + 1.2, 0.0), (KD - 0.2, 0.0), (KD + 0.2, 1.5, "out"), (KD + 0.9, 0.0)])
    d["shoulders"] = Track([(KN + 3.2, 0.0), (KN + 4.3, 0.2), (KN + 6.3, 0.1), (KN + 6.5, 0.2, "out"),
                            (KN + 7.5, 0.04), (GP - 0.1, 0.0), (GP + 0.35, 0.22), (CL, 0.24), (CL + 0.7, 0.0, "out"),
                            (E, 0.0)])
    # small catches of breath while she cries through the smile (tear roll .. final chord)
    d["hitches"] = [TR + 0.95, TR + 2.55, PK + 0.4, PK + 2.9, PK + 5.6, FC + 1.6]
    # ---- head (looking up is carried by the nod; the gaze adds to it)
    d["nod"] = Track([(S, 0.115), (S + 0.7, 0.1), (D + 0.3, 0.16), (F1, 0.12), (F1 + 2.5, 0.08), (TH - 0.6, 0.24),
                      (MG, 0.18), (MG + 3.2, 0.3), (MG + 5.5, 0.32), (ME + 1.0, 0.12), (OH - 1.5, 0.16), (OH, 0.12),
                      (GL, 0.06), (GL + 4.5, 0.08), (BU - 1.5, 0.22), (BU + 1.5, 0.36), (KN, 0.36),
                      (KN + 0.35, -0.12), (KN + 2.2, -0.22), (KN + 2.7, 0.28), (KN + 4.5, 0.3), (KN + 6.0, 0.36),
                      (GP, 0.42), (CL, 0.44), (CL + 0.7, 0.56, "out"), (TR, 0.54), (PK, 0.53), (PK + 5.0, 0.48),
                      (FC, 0.42), (CE, 0.36)])
    d["tilt"] = Track([(S, -3.8), (F1 + 2.3, -3.0), (TH - 0.6, 0.0), (MG, 2.0), (MG + 4.5, 4.0), (ME, 0.5),
                       (ME + 3.5, -3.0), (OH, 4.0), (GL, 6.0), (GL + 4.0, 3.0), (BU, 0.0), (KN + 4.0, 0.0),
                       (KN + 6.3, 2.0), (KN + 6.5, 5.0, "out"), (KN + 7.0, 1.0), (KN + 7.25, -4.0, "out"),
                       (KN + 7.6, -3.0), (GP, -3.0), (CL, 0.0), (TR, 4.0), (PK, 7.0), (FC, 4.0), (E, 3.0)])
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
        (BU + 1.0, (0.4, -0.72), 1.0),
        (BU + 2.4, (-0.4, -0.62)),
        (BU + 3.3, (0.38, -0.7), 0.5),
        (BU + 5.0, (0.46, -0.6), 1.2),
        (KN - 0.6, (0.34, -0.72), 0.6),
        (KN + 0.25, (0.36, 0.62)),                 # the mug ...
        (KN + 1.5, (0.5, 0.8), 0.6),               # ... the bench
        (KN + 2.6, (0.38, -0.6)),
        (KN + 3.6, (0.34, -0.72), 1.0),
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
                   GL + 2.6, GL + 3.7, GL + 5.0, GL + 6.75, BU + 0.9, BU + 2.35, BU + 4.6, BU + 6.3,
                   (KN + 0.22, 0.2), KN + 2.55, (KN + 4.4, 0.24), KN + 6.1, CL + 2.5, (TR + 0.15, 0.36), TR + 3.0,
                   PK + 0.95, PK + 2.95, PK + 4.8, PK + 7.0, (FC + 1.3, 0.3), (CE - 0.3, 0.3), (E - 0.55, 0.34)]
    # ---- eyelids / brows
    d["lid"] = Track([(S, 0.72), (D, 0.74), (D + 0.12, 0.88, "out"), (F1 - 0.3, 0.8), (F1 + 2.4, 0.78),
                      (TH - 0.6, 0.93), (MG, 0.95), (MG + 1.0, 0.97), (GL, 0.94), (GL + 2.2, 0.86), (BU, 0.9),
                      (KN, 0.9), (KN + 0.3, 0.8), (KN + 2.4, 0.8), (KN + 2.8, 0.93), (GP - 0.3, 0.95),
                      (GP + 0.12, 1.0, "out"), (CL + 1.2, 1.0), (CL + 2.5, 0.94), (TR, 0.92), (TR + 2.0, 0.88),
                      (PK, 0.88), (FC, 0.82), (CE, 0.84), (E, 0.8)])
    d["wide"] = Track([(D, 0.0), (D + 0.12, 0.18, "out"), (D + 0.9, 0.0), (GP - 0.1, 0.0), (GP + 0.16, 0.48, "out"),
                       (CL, 0.5), (CL + 0.12, 0.62, "out"), (CL + 1.4, 0.15), (TR, 0.0)])
    d["brow_raise"] = Track([(S, 0.1), (S + 0.6, 0.22), (D, 0.24), (D + 0.15, 0.48, "out"), (D + 1.2, 0.15),
                             (F1, 0.15), (F1 + 0.25, 0.32, "out"), (F1 + 2.4, 0.18), (TH - 0.5, 0.36),
                             (MG + 0.4, 0.52), (MG + 5.0, 0.4), (ME + 0.8, 0.5), (OH, 0.55), (GL, 0.38),
                             (BU, 0.46), (KN, 0.4), (KN + 0.4, 0.22), (KN + 2.6, 0.45), (GP, 0.55),
                             (GP + 0.15, 0.72, "out"), (CL, 0.75), (CL + 0.15, 0.85, "out"), (CL + 2.0, 0.5),
                             (TR, 0.38), (FC, 0.3), (E, 0.26)])
    d["worry"] = Track([(S, 0.0), (F1 + 4.0, 0.1), (MG, 0.25), (ME, 0.35), (OH - 0.3, 0.6), (GL, 0.72),
                        (GL + 3.0, 0.78), (BU, 0.6), (KN + 2.6, 0.7), (KN + 5.0, 0.85), (GP, 0.72), (CL, 0.55),
                        (TR, 0.8), (PK, 0.72), (FC, 0.62), (E, 0.6)])
    d["furrow"] = Track([(S, 0.2), (F1 + 2.4, 0.2), (F1 + 4.8, 0.0)])
    # ---- mouth
    d["smirk"] = Track([(S, 0.7), (S + 0.5, 0.74), (D, 0.72), (D + 0.3, 0.55), (F1, 0.62), (F1 + 2.2, 0.62),
                        (TH - 0.6, 0.05), (MG, 0.0)])
    d["smile"] = Track([(S, 0.1), (F1 + 2.4, 0.08), (TH - 0.5, 0.0), (ME + 0.9, 0.0), (ME + 1.8, 0.14),
                        (ME + 3.6, 0.1), (OH - 0.6, 0.0), (OH + 0.6, -0.05), (GL, -0.08), (GL + 2.5, -0.16),
                        (GL + 4.9, -0.12), (GL + 5.9, 0.16), (GL + 7.2, 0.1), (BU, -0.02), (GP, 0.0), (CL + 0.8, 0.08),
                        (TR + 0.5, 0.12), (TR + 2.0, 0.42), (PK, 0.4), (PK + 5.0, 0.34), (FC, 0.26), (E, 0.16)])
    d["squint"] = Track([(S, 0.072), (S + 0.8, 0.04), (F1 + 2.4, 0.02), (TH, 0.0), (GL + 5.6, 0.0), (GL + 6.2, 0.08),
                         (GL + 7.4, 0.02), (TR + 1.0, 0.0), (TR + 2.2, 0.2), (FC, 0.12), (E, 0.1)])
    d["open"] = Track([(S, 0.0), (F1 + 4.0, 0.02), (MG + 0.2, 0.0), (MG + 1.2, 0.12), (ME, 0.1), (OH - 0.9, 0.08),
                       (OH - 0.35, 0.16), (OH - 0.05, 0.05), (T.oh_e + 0.1, 0.05), (T.oh_e + 0.6, 0.12),
                       (GL, 0.06), (BU, 0.12), (KN + 3.4, 0.1), (KN + 4.0, 0.2), (KN + 5.6, 0.12), (GP - 0.2, 0.1),
                       (GP + 0.2, 0.2), (CL, 0.2), (CL + 0.12, 0.42, "out"), (CL + 0.9, 0.22), (TR, 0.08),
                       (TR + 2.0, 0.06), (PK, 0.1), (FC, 0.08), (CE + 0.5, 0.1), (CE + 1.6, 0.16), (E, 0.1)])
    d["round"] = Track([(S, 0.0), (MG, 0.0), (MG + 1.2, 0.2), (ME, 0.25), (GL, 0.1), (GP, 0.3), (CL, 0.35),
                        (CL + 1.5, 0.2), (TR, 0.0)])
    d["tremble"] = Track([(GL + 0.5, 0.0), (GL + 2.5, 0.22), (BU, 0.12), (KN + 3.0, 0.15), (KN + 5.0, 0.3),
                          (GP, 0.12), (CL + 1.0, 0.2), (TR, 0.4), (TR + 1.6, 0.72), (PK + 2.0, 0.5), (FC, 0.32),
                          (E, 0.25)])
    # ---- tears, eyes
    d["tears"] = Track([(GL, 0.0), (GL + 2.4, 0.7), (BU, 0.72), (GP, 0.86), (TR + 0.35, 0.92), (TR + 1.1, 0.74),
                        (PK, 0.82), (E, 0.74)])
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
    chest = R.ARMS["hand_on_chest"]
    d["arm_r_pre"] = ArmTrack([(S, raise_), (F1 + 2.4, raise_), (TH - 0.4, ArmPose.blend(raise_, hold, 0.28)),
                               (MG + 0.15, ArmPose.blend(raise_, hold, 0.32)), (MG + 2.1, hold),
                               (KN + 0.55, hold)])
    d["arm_r_post"] = ArmTrack([(KN + 2.45, None), (KN + 3.1, _arm(chest, shoulder=30.0, elbow=96.0, across=0.3)),
                                (KN + 3.8, chest), (CL, chest), (CL + 0.4, _arm(chest, wrist=18.0, elbow=122.0)),
                                (TR, _arm(chest, wrist=14.0)), (E, chest)])
    d["arm_l"] = ArmTrack([(S, LAP_S1), (F1 - 0.001, LAP_S1), (F1, LAP_L, "step"),       # (switch on the cut)
                           (KN + 3.0, LAP_L), (KN + 4.1, HOLD_L), (KN + 6.5, HOLD_L), (KN + 7.3, HEART_L),
                           (CL, HEART_L), (CL + 0.4, _arm(HEART_L, elbow=124.0, wrist=16.0), "out"), (TR, HEART_L),
                           (FC + 0.6, HEART_L), (FC + 2.6, THIGH_L), (CE - 0.001, THIGH_L),
                           (CE, THIGH_S3, "step")])                                   # (switch on the cut)
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
    lv_k = d["kneel"](t)
    hitch = 0.0
    for h0 in d["hitches"]:
        x = (t - h0) / 0.55
        if 0.0 <= x < 1.0:
            hitch = max(hitch, math.sin(math.pi * min(1.0, x * 2.2)) * (1.0 - x) ** 0.5)
    br = _rae_breath(t)
    emo = smoothstep((t - T.glis) / 3.0)          # deeper, more visible breathing once she is moved
    p = Pose(x=d["x"](t), y=float(env.FLOOR_Y), facing=1.0, turn=d["turn"](t), sit=1.0, seat_y=float(env.BENCH_SEAT_Y),
             kneel=lv_k, lean=d["lean"](t) - 0.8 * hitch, bounce=d["bounce"](t) - 1.6 * hitch,
             shoulders_up=d["shoulders"](t) + 0.14 * hitch + 0.07 * emo * max(0.0, br),
             arm_l=d["arm_l"](t), breath=br)
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
                mp = R.mug_pose(body.copy(arm_r=a, mug="r"))
                if mp is None:
                    continue
                err = math.hypot(mp[0] - MUG_SPOT[0], mp[1] - MUG_SPOT[1])
                if best is None or err < best[0]:
                    best = (err, sh, el, ac)
    _, sh, el, ac = best
    best = best[:3]
    step = 2.0
    while step > 0.02:
        improved = False
        for dsh, del_ in ((step, 0), (-step, 0), (0, step), (0, -step)):
            a = _arm(hold, shoulder=sh + dsh, elbow=el + del_, across=ac)
            mp = R.mug_pose(body.copy(arm_r=a, mug="r"))
            err = math.hypot(mp[0] - MUG_SPOT[0], mp[1] - MUG_SPOT[1])
            if err < best[0] - 1e-6:
                best, sh, el, improved = (err, sh + dsh, el + del_), sh + dsh, el + del_, True
                break
        if not improved:
            step *= 0.5
    return _arm(hold, shoulder=sh, elbow=el, across=ac)


def _rae_arm_r(t):
    d = _rae_tracks()
    T = _T()
    KN = T.kneel
    tp = d["place_t"]
    place = _place_arm()
    hold = R.ARMS["hold_mug"]
    if t < KN + 0.55:
        return d["arm_r_pre"](t)
    if t < tp:
        # lift the mug off her lap, carry it over her thigh and set it down on the bench
        lift = _arm(ArmPose.blend(hold, place, 0.55), shoulder=ArmPose.blend(hold, place, 0.55).shoulder + 9.0)
        u = (t - (KN + 0.55)) / (tp - (KN + 0.55))
        if u < 0.55:
            return ArmPose.blend(hold, lift, smoothstep(u / 0.55))
        return ArmPose.blend(lift, place, smoothstep((u - 0.55) / 0.45))
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
    ref = "seat"
    sx, sy = 170.0, 150.0
    if name == "mote0":
        m = _note_mote(0, max(t, T.first_note + 0.02))
        if m is not None:
            pos = (m[0], m[1])
    elif name == "qhand":
        ref = "kneel"
        qa = _quill_tracks()["arm_r"](t)
        pos = Q.hand_pos(Pose(x=545.0, y=float(env.FLOOR_Y), facing=-1.0, turn=0.35, arm_r=qa), "r")
    elif name == "final":
        ref = "kneel"
        m = _final_mote(min(t, T.end - 1.0))
        if m is not None:
            pos = (m[0], m[1])
        sx, sy = 120.0, 110.0
    else:
        st = _mem1(_MEM_INDEX[name], t, clamp_age=True)
        pos = (st[2], st[3])
    if pos is None:
        return (0.4, -0.6)
    hx, hy = _rae_face_ref(ref)
    return (clamp((pos[0] - hx) / sx, -1.0, 1.0), clamp((pos[1] - hy) / sy - 0.05, -1.0, 1.0))


def _rae_look(t):
    return _gaze_eval(t, _rae_tracks()["gaze"], _rae_target)


def _rae_pose(t, lv) -> Pose:
    T = _T()
    d = _rae_tracks()
    p = _rae_body(t)
    lx, ly = _rae_look(t)
    mote = _final_mote(t)
    # eyes lead, the head follows (lagged gaze drives a little head turn / nod)
    lag = [_rae_look(t - 0.12 - 0.08 * i) for i in range(4)]
    glx = sum(g[0] for g in lag) / 4.0
    gly = sum(g[1] for g in lag) / 4.0
    blink = _blinks(t, d["blinks"])
    lid = d["lid"](t) * blink
    mo, mr = mouth("rae", t)
    gk = smoothstep((t - T.start) / 1.5)          # S2's own head/gaze dynamics fade in from the S1 handoff
    nod = d["nod"](t) + gk * (-0.12 * gly + 0.025 * noise1(t * 0.5, 5))
    if mote is not None or t > T.celesta:
        nod -= 0.22 * smoothstep((t - T.celesta - 0.6) / 2.6)
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
    return R.mug_pose(p)


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
    d["nod"] = Track([(S, 0.0), (S + 0.3, 0.06), (S + 1.4, 0.02), (T.kneel + 4.0, 0.02), (T.kneel + 7.5, -0.1),
                      (T.climax, -0.08), (T.climax + 0.5, 0.0), (FC + 2.0, -0.06)])
    d["tilt"] = Track([(S, 2.75), (S + 1.6, 1.0), (T.glis + 1.0, 0.0), (T.glis + 1.6, 1.5), (T.glis + 2.8, 6.0),
                       (T.glis + 4.2, 10.0), (T.build, 7.0), (T.build + 3.0, 3.0), (T.climax, 2.0), (FC, 3.0),
                       (FC + 3.0, 7.0)])
    d["brow"] = Track([(S, 0.05), (T.glis + 1.4, 0.05), (T.glis + 2.6, 0.32), (T.build, 0.15), (T.climax, 0.15),
                       (T.climax + 0.3, 0.3), (T.tear, 0.18), (FC, 0.12)])
    d["smile"] = Track([(S, 0.06), (S + 1.2, 0.0), (FC + 2.0, 0.0), (FC + 4.0, 0.1)])
    d["glow"] = Track([(S, 0.1), (D, 0.12), (D + 1.5, 0.5), (T.climax, 0.6), (T.climax + 0.3, 1.0), (T.tear, 0.8),
                       (FC, 0.75), (FC + 3.0, 0.35)])
    d["gaze"] = Track([(S, (-0.45, 0.22)), (S + 0.5, (-0.3, -0.02), "out"), (S + 1.4, (-0.46, 0.26)),
                       (T.mem + 1.2, (-0.46, 0.26)), (T.mem + 1.8, (-0.6, 0.0)), (T.mem + 3.0, (-0.6, 0.0)),
                       (T.mem + 3.6, (-0.48, 0.28)), (T.kneel + 4.5, (-0.48, 0.3)), (T.kneel + 7.0, (-0.5, 0.44)),
                       (T.climax + 0.8, (-0.5, 0.44)), (T.climax + 1.8, (-0.52, 0.36)), (FC + 1.2, (-0.52, 0.36)),
                       (FC + 2.2, (-0.48, 0.42))])
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
                look_x=lx, look_y=ly, head_tilt=d["tilt"](t), head_nod=d["nod"](t), brow_raise=d["brow"](t),
                smile=d["smile"](t), glow=d["glow"](t) * (0.85 + 0.25 * lv.rms), shoulders_up=d["shoulders"](t),
                lean=sway, **lv.quill)


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
    hx, hy = _rae_face_ref("seat")
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


# path relative to her (kneeling) face: from above-right, down across in front of her chin, to her chest
_FM_PATH = ((84.0, -132.0), (66.0, -62.0), (30.0, 18.0), (6.0, 60.0), (-14.0, 112.0))


def _final_mote(t):
    """(x, y, brightness, glint) of the last mote drifting down in front of Rae's face, or None."""
    T = _T()
    t0 = T.celesta
    out_t = T.end - 0.95
    if t < t0 - 0.05 or t > out_t + 0.4:
        return None
    hx, hy = _rae_face_ref("kneel")
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


@lru_cache(maxsize=4)
def _rae_face_ref(kind="seat"):
    if kind == "seat":
        p = Pose(x=SEAT_X, y=float(env.FLOOR_Y), facing=1.0, turn=0.35, sit=1.0, seat_y=float(env.BENCH_SEAT_Y))
    else:       # identical to S3's _kneel_face(): S2 ends on the framing S3 opens with
        p = Pose(x=KNEEL_X, y=float(env.FLOOR_Y), facing=1.0, turn=0.3, sit=1.0, kneel=1.0,
                 seat_y=float(env.BENCH_SEAT_Y), head_nod=0.42)
    return R.head_center(p)


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
    return (
        ("two", T.start, T.first_note),
        ("rae_med", T.first_note, T.theme),
        ("wide_rib", T.theme, _db(14.22)),
        ("rae_cu1", _db(14.22), _db(17.61)),
        ("mem_med", _db(17.61), q0),
        ("quill_cu", q0, q1),
        ("rae_cu2", q1, T.build),
        ("build", T.build, T.gp),
        ("pause", T.gp, T.climax),
        ("burst", T.climax, T.tear),
        ("tear", T.tear, T.celesta),
        ("last", T.celesta, T.end + 1.0),
    )


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
    fs = _rae_face_ref("seat")
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
    if name == "build":
        return Camera.lerp(Camera(356.0, 802.0, 0.9), Camera(358.0, 770.0, 1.3), ease_in_out(u))
    if name == "pause":
        fk = _shot_face(a)
        return _face_cam(fk[0], fk[1], lerp(3.25, 3.4, u), 350.0, 600.0)
    if name == "burst":
        e = ease_out(clamp((t - a) / 1.6))
        return Camera(352.0, 790.0 - 6.0 * e, lerp(0.86, 0.78, e))
    if name == "tear":
        return _tear_cam(t, a)
    if name == "last":
        fk = _rae_face_ref("kneel")
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
    d = _rae_tracks()
    tw = _freeze_clock(t)
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, tw, light=lv.room, swirl=lv.swirl, window_bright=lv.wb)
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
    bm = _bench_mug(t)
    mug_front = bm is not None and t < d["mug_back_t"]
    if bm is not None and not mug_front:
        _draw_bench_mug(c, bm, rp)
    if shot == "quill_cu":
        with Layer(c):
            Q.draw(c, qp, t)
            _quill_light_band(c, t, qp)
    else:
        Q.draw(c, qp, t)
    _draw_palm_light(c, t, qp, lv)
    R.draw(c, rp, t)
    if mug_front:
        # she has just let go: the mug stands on the front of the seat, in front of her thigh (exactly where
        # the in-hand mug was drawn) until her legs have left the seat
        _draw_bench_mug(c, bm, rp)
    # foreground: only the floor-edge shadow (nobody uses the door here, so no lintel / jamb overdraw that
    # would cut the climax light)
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
