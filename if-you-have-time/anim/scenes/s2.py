"""S2 -- "The Symphony" (BIBLE section 4 S2): the heart of the film.

Quill raises his hand, the lounge goes dark, and the music fills the room with light: note motes,
breathing ribbons, memory bubbles, a galaxy forming in the window. Rae melts from a skeptical smirk into
awe, sets her mug on the bench and slides to her knees; grand pause; the BURST; one tear and a trembling
smile; the cathedral pull-back; sparks fall like snow and a last mote goes out in front of her face.

Every time is derived from named beats (core.beat / line_start / scene_span) or from the symphony's own
music data (envelopes.json downbeats / beats / onsets). render(canvas, t) is a pure function of t.

Shot list (absolute times are only for orientation -- see _shots()):
  two       sym_quill_raise -> 1st note       TWO-SHOT: Quill lifts his hand, lights dim
  rae_med   1st note -> sym_theme1           MEDIUM Rae: note motes, smirk melts, eyes lift
  wide_rib  sym_theme1 -> bar 5               WIDE push: ribbons wake up, the mug lowers
  rae_cu1   bar 5 -> bar 6                    CLOSE Rae: brows lift, lips part, pupils wide
  mem_med   bar 6 -> bar 9                    MEDIUM-WIDE: memory bubbles rise around her, "...oh", eyes glisten
  quill_cu  bar 9 (+2.2 s)                    CLOSE Quill: watching, ribbon light across his face, head tilt
  rae_cu2   -> sym_build                      CLOSE Rae: tears welled, memories drift past
  window    sym_build -> bar 13               WIDE: the stars swirl into a galaxy, ribbons intensify
  kneel     bar 13 -> sym_grand_pause         MEDIUM-WIDE: mug onto the bench, slides to her knees
  pause     sym_grand_pause -> sym_climax     CLOSE Rae: eyes wide and wet, ribbons frozen
  burst     sym_climax -> sym_tear_roll       WIDE: the BURST (blown back), galaxy blazing, all memories glow
  tear      sym_tear_roll -> sym_final_chord  CLOSE Rae: one tear, trembling smile; from sym_peak a slow pull
                                              back to a cathedral of light
  coda      sym_final_chord -> end            DISSOLVE to a medium two-shot: sparks fall like snow, Quill lowers
                                              his hand; slow push to Rae: the last mote goes out
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
from anim.core import (Camera, Layer, Track, beat, breathe, clamp, ease_out, glow, lerp, light_filter, line_end,
                       line_start, mouth, music_env, music_onsets, noise1, scene_span, smoothstep)
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


# =========================================================================== small helpers


def _mix(a, b, u):
    u = clamp(u)
    return tuple(int(round(a[i] + (b[i] - a[i]) * u)) for i in range(3))


def _rms(t, key="rms"):
    """Music loudness, lightly smoothed (pure function of t)."""
    return sum(music_env("symphony", t - k * 0.05, key) for k in range(8)) / 8.0


def _gaze(keys):
    """Gaze track from [(t, (lx, ly)[, dur[, ease]])]: quick saccades (0.09 s) by default, longer
    eased pursuits when a duration is given. Holds between keys."""
    ks = []
    prev = None
    for k in keys:
        tt, v = k[0], k[1]
        dur = k[2] if len(k) > 2 else 0.09
        ease = k[3] if len(k) > 3 else ("out" if dur <= 0.12 else "io")
        if prev is None:
            ks.append((tt, v))
        else:
            ks.append((tt, prev, "lin"))
            ks.append((tt + dur, v, ease))
        prev = v
    return Track(ks)


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
    d = {}
    d["room"] = Track([(D, 1.0), (D + 1.5, 0.25, "io")])
    d["dark"] = Track([(D, 0.0), (D + 1.5, 1.0, "io")])
    # window: brightens a touch with the dim, breathes, blazes at the climax, settles on the final chord
    d["wb"] = Track([(D, 1.0), (D + 1.5, 1.12), (T.build, 1.15), (T.gp - 0.4, 1.32), (T.gp + 0.2, 1.0),
                     (T.climax - 0.05, 1.02), (T.climax + 0.35, 2.05, "out"), (T.tear, 1.65), (T.peak, 1.6),
                     (T.peak + 1.6, 1.85), (T.final, 1.6), (T.final + 3.2, 1.05), (T.end, 1.0)])
    d["swirl"] = Track([(T.build, 0.0), (T.kneel + 3.5, 0.82, "io"), (T.climax - 0.2, 0.93), (T.climax + 1.2, 1.0),
                        (T.final + 3.0, 1.0), (T.end, 0.4, "io")])
    d["rib"] = Track([(T.theme - 0.3, 0.0), (T.theme + 2.8, 0.5, "io"), (T.mug + 2, 0.58), (T.mem, 0.62),
                      (T.build, 0.7), (T.gp - 0.3, 0.92), (T.climax, 0.95), (T.climax + 0.3, 1.0),
                      (T.final, 1.0), (T.final + 2.8, 0.0, "io")])
    d["burst"] = Track([(T.climax - 0.02, 0.0), (T.climax + 0.55, 1.0, "out"), (T.tear, 0.35),
                        (T.peak, 0.3), (T.peak + 1.5, 0.55), (T.peak + 4.5, 0.35), (T.final, 0.3),
                        (T.final + 2.0, 0.0)])
    d["freeze"] = Track([(T.gp - 0.45, 0.0), (T.gp + 0.1, 1.0, "out"), (T.climax - 0.18, 1.0),
                         (T.climax + 0.02, 0.0, "in")])
    d["lburst"] = Track([(T.climax - 0.02, 0.0), (T.climax + 0.3, 0.78, "out"), (T.climax + 3.2, 0.42),
                         (T.peak, 0.38), (T.peak + 1.6, 0.52), (T.final, 0.36), (T.final + 3.0, 0.0)])
    d["flash"] = Track([(T.climax - 0.01, 0.0), (T.climax + 0.04, 0.07, "out"), (T.climax + 0.45, 0.0, "io")])
    d["vign"] = Track([(D, 0.22), (D + 1.5, 0.45), (T.climax, 0.5), (T.climax + 0.4, 0.22), (T.peak, 0.3),
                       (T.final + 2, 0.45), (T.end, 0.55)])
    d["sparks"] = Track([(T.final + 0.3, 0.0), (T.final + 3.0, 1.0, "io"), (T.celesta + 1.0, 0.75),
                         (T.end, 0.45)])
    d["motes"] = Track([(T.theme, 0.55), (T.build, 0.7), (T.gp, 0.95), (T.climax, 0.95), (T.climax + 0.6, 1.5),
                        (T.final, 1.2), (T.final + 3, 0.6), (T.end, 0.35)])
    d["sparkle_a"] = Track([(F1 - 1, 1.0), (T.climax - 0.5, 1.0), (T.climax + 0.5, 0.55), (T.final, 0.6),
                            (T.final + 2, 0.9)])
    # characters: low light, deep-blue tint, rim lit by the nearest light
    d["c_light"] = Track([(D, 1.0), (D + 1.5, 0.33, "io"), (T.climax - 0.05, 0.33), (T.climax + 0.3, 0.52, "out"),
                          (T.tear, 0.4), (T.peak + 1.5, 0.44), (T.final, 0.4), (T.final + 3, 0.3)])
    d["c_tint"] = Track([(D, 0.0), (D + 1.5, 0.36, "io"), (T.climax, 0.36), (T.climax + 0.3, 0.2), (T.final, 0.22),
                         (T.final + 3, 0.36)])
    d["c_rim"] = Track([(D + 0.3, 0.06), (D + 1.6, 0.38, "io"), (T.build, 0.4), (T.gp, 0.55), (T.climax, 0.55),
                        (T.climax + 0.3, 1.0, "out"), (T.tear, 0.75), (T.final, 0.75), (T.final + 3, 0.42)])
    d["c_warm"] = Track([(T.build, 0.0), (T.gp, 0.25), (T.climax, 0.3), (T.climax + 0.3, 1.0), (T.final, 0.85),
                         (T.final + 3.5, 0.15)])
    return d


def _freeze_clock(t):
    """Time with the grand-pause freeze taken out (t minus the integral of `freeze`), so drifting dust
    slows to a hold and resumes without jumping."""
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
    breath = 0.10 * rms if t < T.climax else 0.22 * rms
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
    base_rim_q = _mix(C_TEAL, rib_c, 0.3 * smoothstep((t - T.theme) / 3.0))
    lv.rae = dict(light=cl + 0.04 * lv.dark, tint=TINT, tint_amt=L["c_tint"](t), rim=L["c_rim"](t) * (0.92 + 0.15 * rms),
                  rim_color=_mix(base_rim_r, C_WARM, warm))
    lv.quill = dict(light=cl, tint=TINT, tint_amt=L["c_tint"](t), rim=L["c_rim"](t) * (0.95 + 0.1 * rms),
                    rim_color=_mix(base_rim_q, C_WARM, warm))
    return lv


# =========================================================================== Rae


SEAT_X = 230.0
KNEEL_X = 255.0
MUG_SPOT = (330.0, float(env.BENCH_SEAT_Y))     # BIBLE section 9: the mug rests on the bench here

LAP_L = ArmPose(shoulder=3.0, elbow=46.0, wrist=8.0, hand="relaxed")
BRACE_L = ArmPose(shoulder=-24.0, elbow=10.0, wrist=-14.0, hand="open")
THIGH_L = ArmPose(shoulder=12.0, elbow=26.0, wrist=4.0, hand="relaxed")
OPEN_L = ArmPose(shoulder=36.0, elbow=24.0, wrist=-10.0, hand="open", across=-0.3)


@lru_cache(maxsize=1)
def _rae_tracks():
    T = _T()
    S, D, F1, TH, MG, ME = T.start, T.dim, T.first_note, T.theme, T.mug, T.mem
    OH, GL, BU, KN, GP, CL, KD, TR, PK, FC, CE, E = (T.oh, T.glis, T.build, T.kneel, T.gp, T.climax, T.kdone,
                                                      T.tear, T.peak, T.final, T.celesta, T.end)
    d = {}
    # ---- the slide from the bench to her knees (KN .. KD)
    d["place_t"] = KN + 2.1           # mug touches the bench
    # rig limitation: both legs share one kneel value, so "one knee, then the other" is a two-stage drop
    # (to the first knee, a weight shift, then down onto both) rather than truly separate legs
    d["kneel"] = Track([(KN + 4.3, 0.0), (KN + 5.6, 0.74, "io"), (KN + 6.3, 0.77), (KN + 7.3, 0.93, "io"),
                        (CL, 0.94), (KD, 1.0, "io")])
    d["x"] = Track([(KN + 4.2, SEAT_X), (KN + 5.6, SEAT_X + 17.0, "io"), (KN + 6.3, SEAT_X + 18.0),
                    (KN + 7.3, SEAT_X + 23.0, "io"), (CL, SEAT_X + 23.5), (KD, KNEEL_X, "io")])
    d["turn"] = Track([(KN + 4.0, 0.35), (KD, 0.3)])
    d["lean"] = Track([(S, 2.0), (S + 1.2, 1.0), (F1 + 2.0, 0.5), (TH - 0.5, 2.0), (MG + 1.5, 3.0), (ME, 2.0), (OH - 0.3, 4.0),
                       (BU, 2.0), (KN, 2.0), (KN + 0.6, 3.5), (KN + 2.1, 4.0), (KN + 2.8, 3.0),
                       (KN + 4.1, 12.0), (KN + 5.2, 6.0, "io"), (KN + 6.2, 7.0), (KN + 7.2, 2.0),
                       (GP, 1.0), (CL, 1.0), (CL + 0.5, -3.5, "out"), (KD + 0.6, 0.0), (E, 0.5)])
    d["bounce"] = Track([(KN + 5.35, 0.0), (KN + 5.6, 4.5, "out"), (KN + 6.2, 0.0), (KN + 7.2, 0.0),
                         (KN + 7.45, 3.0, "out"), (KN + 8.0, 0.0), (CL, 0.0), (CL + 0.3, 2.5, "out"),
                         (CL + 1.2, 0.0), (KD - 0.2, 0.0), (KD + 0.2, 1.5, "out"), (KD + 0.9, 0.0)])
    d["shoulders"] = Track([(KN + 3.3, 0.0), (KN + 4.0, 0.22), (KN + 5.4, 0.05), (GP - 0.1, 0.0),
                            (GP + 0.35, 0.22), (CL, 0.24), (CL + 0.7, 0.0, "out"), (E, 0.0)])
    # small catches of breath while she cries through the smile (tear roll .. final chord)
    d["hitches"] = [TR + 0.95, TR + 2.55, PK + 0.4, PK + 2.9, PK + 5.6, FC + 1.6]
    # ---- head
    d["nod"] = Track([(S, 0.07), (S + 0.7, 0.08), (D + 0.3, 0.14), (F1, 0.1), (F1 + 2.5, 0.05), (TH - 0.6, 0.18),
                      (MG, 0.12), (MG + 4.5, 0.2), (ME + 1.0, 0.1), (OH - 1.5, 0.18), (OH, 0.14), (GL, 0.08),
                      (GL + 4.5, 0.12), (BU - 1.0, 0.24), (BU + 1.5, 0.36), (KN, 0.36), (KN + 0.35, -0.12),
                      (KN + 2.2, -0.22), (KN + 2.7, 0.28), (KN + 4.5, 0.34), (KN + 6.0, 0.4), (GP, 0.44),
                      (CL, 0.46), (CL + 0.7, 0.58, "out"), (TR, 0.56), (PK, 0.55), (PK + 5.0, 0.5), (FC, 0.42), (CE, 0.34)])
    d["tilt"] = Track([(S, -3.0), (F1 + 2.3, -3.0), (TH - 0.6, 0.0), (MG, 2.0), (MG + 4.5, 4.0), (ME, 0.5),
                       (ME + 3.5, -3.0), (OH, 4.0), (GL, 6.0), (GL + 4.0, 3.0), (BU, 0.0), (KN + 4.0, 0.0),
                       (KN + 5.7, 3.0), (KN + 6.4, -5.0), (KN + 7.4, -3.0), (GP, -3.0), (CL, 0.0), (TR, 4.0), (PK, 7.0), (FC, 4.0), (E, 3.0)])
    # ---- gaze (screen space; Quill is up and to her right)
    d["gaze"] = _gaze([
        (S, (0.62, -0.35)), (S + 0.35, (0.55, -0.16), 0.5), (S + 0.9, (0.62, -0.38), 0.8),   # his hand rises
        (D + 0.15, (-0.25, -0.45)), (D + 0.65, (0.3, -0.55)), (D + 1.15, (0.55, -0.24)),   # the room goes dark
        (F1 + 0.12, (0.05, -0.42)), (F1 + 1.0, (0.25, -0.32), 0.5), (F1 + 2.2, (0.5, -0.16)),  # the sound -> him
        (F1 + 3.6, (0.22, -0.34), 1.4), (F1 + 5.0, (0.06, -0.45), 1.2), (TH - 0.7, (0.14, -0.5), 0.8),
        (TH + 0.5, (-0.32, -0.42)), (TH + 1.6, (0.08, -0.55), 1.0), (TH + 2.8, (0.35, -0.36), 0.8),
        (MG + 0.3, (0.15, -0.3), 0.6), (MG + 2.0, (-0.1, -0.4), 1.4), (MG + 3.6, (0.05, -0.36)),
        (MG + 4.7, (0.22, -0.44)), (MG + 5.8, (0.02, -0.38), 0.6),
        (ME + 0.7, (-0.62, 0.22)), (ME + 1.6, (-0.6, -0.08), 1.2), (ME + 2.9, (-0.52, -0.36), 1.2),
        (ME + 3.6, (0.55, 0.12)), (ME + 4.6, (0.5, -0.18), 1.2), (OH - 0.2, (0.45, -0.3), 0.8),
        (OH + 1.0, (-0.55, -0.02)), (OH + 2.2, (-0.5, -0.3), 1.2),
        (GL + 0.3, (0.45, 0.02)), (GL + 1.4, (0.42, -0.12), 1.0),
        (GL + 3.4, (-0.4, -0.1)), (GL + 4.7, (0.4, -0.05)), (GL + 5.9, (0.42, -0.25), 1.0),
        (BU - 1.0, (0.1, -0.5), 0.8),
        (BU + 0.4, (0.05, -0.66), 1.0), (BU + 2.2, (-0.1, -0.7), 1.6), (BU + 4.2, (0.1, -0.68), 1.6),
        (KN - 0.6, (0.0, -0.72), 1.0),
        (KN + 0.25, (0.32, 0.62)), (KN + 1.5, (0.48, 0.78), 0.6),             # the mug, the bench
        (KN + 2.6, (0.12, -0.55)), (KN + 3.6, (0.0, -0.7), 1.0),
        (GP - 0.4, (0.0, -0.62), 0.3),
        (CL + 0.9, (-0.12, -0.62), 0.4), (CL + 2.4, (0.1, -0.66), 0.8),
        (TR, (0.05, -0.72), 0.4), (TR + 2.2, (0.0, -0.66), 1.4), (TR + 3.6, (0.15, -0.7), 1.0),
        (PK + 1.0, (-0.1, -0.6), 1.6), (PK + 3.0, (0.2, -0.6), 1.8), (PK + 5.0, (0.0, -0.66), 1.6),
        (FC - 1.6, (0.6, -0.3)), (FC - 0.4, (0.25, -0.5), 0.8),              # a glance to Quill, back up
        (FC + 0.4, (0.1, -0.22), 2.0), (FC + 2.8, (0.15, -0.38), 1.2),
    ])
    d["blinks"] = [(D + 0.08, 0.2), (F1 + 0.15, 0.18), F1 + 1.9, F1 + 4.4, TH + 0.35, TH + 2.5,
                   (MG + 0.5, 0.3), MG + 2.6, MG + 5.4, ME + 0.6, ME + 3.5, (OH - 0.45, 0.32), OH + 1.85,
                   (GL + 0.5, 0.42), GL + 4.0, GL + 6.3, BU + 0.9, BU + 3.7, BU + 6.0, (KN + 0.22, 0.2),
                   KN + 2.55, (KN + 4.4, 0.24), KN + 6.1, CL + 2.5, (TR + 0.15, 0.36), TR + 3.0,
                   PK + 2.1, PK + 4.8, PK + 7.0, (FC + 1.3, 0.3), (CE - 0.3, 0.3)]
    # ---- eyelids / brows
    d["lid"] = Track([(S, 0.72), (D, 0.74), (D + 0.12, 0.88, "out"), (F1 - 0.3, 0.8), (F1 + 2.4, 0.78),
                      (TH - 0.6, 0.93), (MG, 0.95), (MG + 1.0, 0.97), (GL, 0.94), (GL + 2.2, 0.86), (BU, 0.9),
                      (KN, 0.9), (KN + 0.3, 0.8), (KN + 2.4, 0.8), (KN + 2.8, 0.93), (GP - 0.3, 0.95),
                      (GP + 0.12, 1.0, "out"), (CL + 1.2, 1.0), (CL + 2.5, 0.94), (TR, 0.92), (TR + 2.0, 0.88), (PK, 0.88),
                      (FC, 0.82), (CE, 0.82), (E, 0.8)])
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
    d["furrow"] = Track([(S, 0.22), (F1 + 2.4, 0.2), (F1 + 4.8, 0.0)])
    # ---- mouth
    d["smirk"] = Track([(S, 0.7), (S + 0.5, 0.74), (D, 0.72), (D + 0.3, 0.55), (F1, 0.62), (F1 + 2.2, 0.62),
                        (TH - 0.6, 0.05), (MG, 0.0)])
    d["smile"] = Track([(S, 0.1), (F1 + 2.4, 0.08), (TH - 0.5, 0.0), (ME + 0.9, 0.0), (ME + 1.8, 0.14),
                        (ME + 3.6, 0.1), (OH - 0.6, 0.0), (OH + 0.6, -0.05), (GL, -0.08), (GL + 2.5, -0.16),
                        (GL + 4.6, -0.12), (GL + 5.6, 0.12), (GL + 7.0, 0.08), (BU, -0.02), (GP, 0.0), (CL + 0.8, 0.08), (TR + 0.5, 0.12), (TR + 2.0, 0.42),
                        (PK, 0.4), (PK + 5.0, 0.34), (FC, 0.26), (E, 0.16)])
    d["open"] = Track([(S, 0.0), (F1 + 4.0, 0.02), (MG + 0.2, 0.0), (MG + 1.2, 0.12), (ME, 0.1), (OH - 0.9, 0.08),
                       (OH - 0.35, 0.16), (OH - 0.05, 0.05), (T.oh_e + 0.1, 0.05), (T.oh_e + 0.6, 0.12),
                       (GL, 0.06), (BU, 0.12), (KN + 3.4, 0.1), (KN + 4.0, 0.2), (KN + 5.6, 0.12), (GP - 0.2, 0.1),
                       (GP + 0.2, 0.2), (CL, 0.2), (CL + 0.12, 0.42, "out"), (CL + 0.9, 0.22), (TR, 0.08),
                       (TR + 2.0, 0.06), (PK, 0.1), (FC, 0.08), (E, 0.1)])
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
    d["squint"] = Track([(TR + 1.0, 0.0), (TR + 2.2, 0.2), (FC, 0.12), (E, 0.1)])
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
    d["arm_l"] = ArmTrack([(S, R.ARMS["rest"]), (F1 + 2.5, R.ARMS["rest"]), (F1 + 5.0, LAP_L), (KN + 3.0, LAP_L), (KN + 3.9, BRACE_L), (KN + 5.2, THIGH_L),
                           (CL, THIGH_L), (CL + 0.8, OPEN_L, "out"), (CL + 3.0, OPEN_L),
                           (TR + 0.5, ArmPose.blend(THIGH_L, OPEN_L, 0.25)), (FC + 1.0, THIGH_L)])
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
    if t < KN + 2.45:
        # set down; the hand lingers on the mug for a beat, fingers opening
        return _arm(place, hand="open") if t > tp + 0.18 else place
    post = d["arm_r_post"]
    keys = post.keys
    if t < keys[1][0]:
        u = smoothstep((t - keys[0][0]) / (keys[1][0] - keys[0][0]))
        return ArmPose.blend(_arm(place, hand="open"), keys[1][1], u)
    return post(t)


def _rae_look(t):
    """Rae's gaze (look_x, look_y): keyed saccades/pursuits, plus geometric tracking of the first note
    mote (from Quill's hand to her) and of the last mote (going out in front of her face)."""
    T = _T()
    d = _rae_tracks()
    lx, ly = d["gaze"](t)
    k0 = smoothstep((t - (T.first_note + 0.25)) / 0.35) * (1.0 - smoothstep((t - (T.first_note + 3.0)) / 0.4))
    if k0 > 0.0:
        m = _note_mote(0, t)
        if m is not None:
            hx, hy = _rae_face_ref("seat")
            lx = lerp(lx, clamp((m[0] - hx) / 170.0, -1, 1), k0)
            ly = lerp(ly, clamp((m[1] - hy) / 150.0 - 0.05, -1, 1), k0)
    mote = _final_mote(t)
    if mote is not None:
        hx, hy = _rae_face_ref("kneel")
        k = smoothstep((t - T.celesta) / 0.6)
        lx = lerp(lx, clamp((mote[0] - hx) / 150.0, -1, 1), k)
        ly = lerp(ly, clamp((mote[1] - hy) / 120.0 - 0.1, -1, 1), k)
    return lx, ly


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
    nod = d["nod"](t) - 0.12 * gly + 0.025 * noise1(t * 0.5, 5)
    if mote is not None:
        nod -= 0.28 * smoothstep((t - T.celesta - 0.6) / 2.6)
    tilt = d["tilt"](t) + 1.2 * noise1(t * 0.35, 8)
    hturn = 0.16 * glx * smoothstep((t - T.start) / 1.5) + 0.02 * noise1(t * 0.4, 9)
    gp_hold = 1.0 - smoothstep((t - T.gp) / 0.25) * (1.0 - smoothstep((t - T.climax) / 0.2))
    tilt = lerp(d["tilt"](T.gp), tilt, gp_hold) if T.gp < t < T.climax + 0.2 else tilt
    # the rig's gaze travel is small: exaggerate a little once we're past the S1 handoff
    gk = smoothstep((t - T.start) / 1.5)
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
    d["arm_l"] = ArmTrack([(S + 0.35, bb), (S + 1.3, rest)])
    # conducting envelope (0 before the first note / during the grand pause / after the final chord)
    d["cond"] = Track([(F1 - 0.3, 0.0), (F1, 1.0), (T.gp - 0.5, 1.0), (T.gp, 0.0), (T.climax, 0.0),
                       (T.climax + 0.4, 1.0), (FC, 1.0), (FC + 0.5, 0.0)])
    d["lift"] = Track([(T.gp - 0.5, 0.0), (T.gp, 5.0, "out"), (T.climax, 5.0), (T.climax + 0.6, 14.0, "out"),
                       (T.climax + 2.6, 7.0), (T.peak, 6.0), (T.peak + 1.6, 10.0), (FC, 6.0), (FC + 0.5, 0.0)])
    d["shoulders"] = Track([(S, 0.0), (S + 0.25, 0.1), (S + 0.9, 0.0)])
    d["nod"] = Track([(S, 0.0), (S + 0.3, 0.06), (S + 1.4, 0.02), (T.kneel + 4.0, 0.02), (T.kneel + 7.5, -0.1),
                      (T.climax, -0.08), (T.climax + 0.5, 0.0), (FC + 2.0, -0.06)])
    d["tilt"] = Track([(S, 2.75), (S + 1.6, 1.0), (T.glis + 1.0, 0.0), (T.glis + 1.6, 1.5), (T.glis + 2.8, 10.0), (T.build, 7.0),
                       (T.build + 3.0, 3.0), (T.climax, 2.0), (FC, 3.0), (FC + 3.0, 7.0)])
    d["brow"] = Track([(S, 0.05), (T.glis + 1.4, 0.05), (T.glis + 2.6, 0.32), (T.build, 0.15), (T.climax, 0.15),
                       (T.climax + 0.3, 0.3), (T.tear, 0.18), (FC, 0.12)])
    d["smile"] = Track([(S, 0.06), (S + 1.2, 0.0), (FC + 2.0, 0.0), (FC + 4.0, 0.1)])
    d["glow"] = Track([(S, 0.12), (D, 0.12), (D + 1.5, 0.5), (T.climax, 0.6), (T.climax + 0.3, 1.0), (T.tear, 0.8), (FC, 0.75),
                       (FC + 3.0, 0.35)])
    d["gaze"] = _gaze([(S, (-0.45, 0.22)), (S + 0.5, (-0.3, -0.02)), (S + 1.4, (-0.46, 0.26), 0.3),
                       (T.mem + 1.2, (-0.6, 0.0), 0.6), (T.mem + 3.0, (-0.48, 0.28), 0.6),
                       (T.kneel + 4.5, (-0.5, 0.44), 2.5), (T.climax + 1.0, (-0.52, 0.36), 1.0),
                       (FC + 1.2, (-0.48, 0.42), 1.0)])
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


# =========================================================================== memories


# kind, start offset from sym_memories_start, life, radius, layer, rising path (stage coords)
_MEM1 = (
    ("car_window", 0.0, 5.8, 96.0, "front", ((104, 1090), (74, 880), (98, 660), (128, 462))),
    ("hands", 2.4, 5.8, 90.0, "back", ((446, 1110), (462, 890), (432, 672), (448, 478))),
    ("dog_door", 4.9, 5.8, 98.0, "front", ((58, 1140), (30, 910), (70, 700), (52, 510))),
    ("kitchen_dawn", 7.3, 5.6, 92.0, "back", ((398, 1160), (416, 930), (392, 720), (412, 494))),
    ("friends_table", 9.7, 5.6, 100.0, "front", ((112, 1170), (70, 925), (88, 712), (74, 500))),
    ("sea_sunset", 12.0, 5.8, 100.0, "back", ((436, 1180), (418, 952), (448, 732), (426, 512))),
)
# the climax halo: kind, angle around the galaxy core (deg, 0 = screen right, 90 = down), radius
_MEM2 = (
    ("sea_sunset", 152.0, 92.0), ("car_window", 197.0, 96.0), ("hands", 240.0, 90.0),
    ("kitchen_dawn", 287.0, 90.0), ("dog_door", 330.0, 94.0), ("friends_table", 28.0, 92.0),
)


def _memories(t):
    """[(layer, kind, x, y, r, alpha, age, glow)]"""
    T = _T()
    out = []
    for i, (kind, off, life, r, layer, path) in enumerate(_MEM1):
        t0 = T.mem + off
        age = t - t0
        if not 0.0 <= age <= life:
            continue
        u = age / life
        x, y = _catmull(path, 0.08 + 0.92 * (1 - (1 - u) ** 1.35))
        x += 9.0 * math.sin(age * 0.8 + i * 1.7)
        a = smoothstep(age / 0.9) * smoothstep((life - age) / 1.3)
        rr = r * (0.8 + 0.2 * ease_out(age / 1.4))
        out.append((layer, kind, x, y, rr, a, age, 0.0))
    if t >= T.climax - 0.05:
        age0 = t - T.climax
        appear = ease_out(clamp(age0 / 0.6))
        fade = 1.0 - smoothstep((t - T.final - 0.2) / 2.4)
        if fade > 0.002:
            gx, gy = env.GALAXY_CENTER
            spin = age0 * 1.6
            g = 1.0 - 0.55 * smoothstep(age0 / 3.0) + 0.25 * smoothstep((t - T.peak) / 1.5) * (
                1 - smoothstep((t - T.peak - 3.0) / 3.0))
            for i, (kind, ang, r) in enumerate(_MEM2):
                a = math.radians(ang + spin + 2.0 * math.sin(age0 * 0.4 + i))
                rad = (360.0 + 40.0 * (1 - appear)) * (1.0 + 0.04 * math.sin(age0 * 0.5 + i * 2.1))
                x = gx + math.cos(a) * rad * 1.02
                y = gy + math.sin(a) * rad * 1.1 - 30.0 * (1 - fade)
                rr = r * (0.55 + 0.45 * appear) * (0.85 + 0.15 * fade)
                out.append(("back", kind, x, y, rr, clamp(age0 / 0.25) * fade, age0 + 6.0 + i, g))
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


def _draw_memories(c, t, layer, mems):
    for (lay, kind, x, y, r, a, age, g) in mems:
        if lay == layer and a > 0.003:
            fx.draw_memory(c, t, kind, x, y, r, alpha=a, age=age, glow=g, develop=g <= 0.0)


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


def _final_mote(t):
    """(x, y, brightness) of the last mote drifting down in front of Rae's face, or None."""
    T = _T()
    t0 = T.celesta
    if t < t0 - 0.05 or t > T.end:
        return None
    hx, hy = _rae_face_ref("kneel")
    u = (t - t0) / max(0.5, (T.end - 0.9) - t0)
    x = hx + 52.0 + 10.0 * math.sin((t - t0) * 1.1) - 8.0 * u
    y = hy - 175.0 + 270.0 * smoothstep(clamp(u) * 0.85 + 0.15 * clamp(u))
    b = smoothstep((t - t0) / 0.5)
    # a little brighter on each celesta note, then it fades and goes out
    for o in T.onsets:
        if t0 - 0.2 <= o <= t:
            b += 0.35 * math.exp(-(t - o) / 0.35)
    out_t = T.end - 0.95
    b *= 1.0 - smoothstep((t - (out_t - 0.7)) / 0.7)
    if b <= 0.003:
        return None
    return (x, y, b)


def _draw_final_mote(c, t):
    m = _final_mote(t)
    if m is None:
        return
    x, y, b = m
    tw = 0.9 + 0.1 * math.sin(t * 5.3)
    glow(c, x, y, 58.0, (255, 226, 180), 0.16 * b * tw)
    glow(c, x, y, 22.0, (255, 240, 214), 0.5 * b * tw)
    glow(c, x, y, 8.0, (255, 250, 236), 0.85 * b)
    glow(c, x, y, 3.6, (255, 255, 255), min(1.0, 1.1 * b))


# =========================================================================== cameras


@lru_cache(maxsize=4)
def _rae_face_ref(kind="seat"):
    if kind == "seat":
        p = Pose(x=SEAT_X, y=float(env.FLOOR_Y), facing=1.0, turn=0.35, sit=1.0, seat_y=float(env.BENCH_SEAT_Y))
    else:
        p = Pose(x=KNEEL_X, y=float(env.FLOOR_Y), facing=1.0, turn=0.3, sit=1.0, kneel=1.0,
                 seat_y=float(env.BENCH_SEAT_Y), head_nod=0.42)
    return R.head_center(p)


@lru_cache(maxsize=1)
def _quill_face_ref():
    return Q.head_center(Pose(x=545.0, y=float(env.FLOOR_Y), facing=-1.0, turn=0.35))


def _face_cam(fx_, fy_, z, sx, sy):
    """Camera at zoom z that puts stage point (fx_, fy_) at screen (sx, sy)."""
    return Camera(fx_ + (W / 2 - sx) / z, fy_ + (H / 2 - sy) / z, z)


def _cam_between(c0, c1, u):
    return Camera.lerp(c0, c1, u)


@lru_cache(maxsize=1)
def _shots():
    T = _T()
    q_end = _db(27.9) + 2.2
    return (
        ("two", T.start, T.first_note),
        ("rae_med", T.first_note, T.theme),
        ("wide_rib", T.theme, _db(14.22)),
        ("rae_cu1", _db(14.22), _db(17.61)),
        ("mem_med", _db(17.61), _db(27.9)),
        ("quill_cu", _db(27.9), q_end),
        ("rae_cu2", q_end, T.build),
        ("window", T.build, _db(41.76)),
        ("kneel", _db(41.76), T.gp),
        ("pause", T.gp, T.climax),
        ("burst", T.climax, T.tear),
        ("tear", T.tear, T.final),
        ("coda", T.final, T.end + 1.0),
    )


def _shot_at(t):
    for name, a, b in _shots():
        if a <= t < b:
            return name, a, b
    s = _shots()
    return (s[0] if t < s[0][1] else s[-1])


def _camera(name, t, a, b):
    T = _T()
    u = clamp((t - a) / max(1e-3, b - a))
    fs = _rae_face_ref("seat")
    if name == "two":
        return Camera.lerp(Camera(396.0, 742.0, 1.1), Camera(392.0, 736.0, 1.14), smoothstep(u))
    if name == "rae_med":
        return _face_cam(fs[0], fs[1], lerp(1.72, 1.9, smoothstep(u)), 332.0, 496.0)
    if name == "wide_rib":
        return Camera.lerp(Camera(350.0, 742.0, 0.88), Camera(316.0, 768.0, 1.1), smoothstep(u))
    if name == "rae_cu1":
        return _face_cam(fs[0], fs[1], lerp(2.05, 2.2, u), 334.0, 520.0)
    if name == "mem_med":
        return _face_cam(fs[0], fs[1], lerp(1.12, 1.36, smoothstep(u)), lerp(318.0, 330.0, u), 486.0)
    if name == "quill_cu":
        qx, qy = _quill_face_ref()
        return _face_cam(qx, qy, lerp(2.35, 2.5, u), 420.0, 520.0)
    if name == "rae_cu2":
        return _face_cam(fs[0], fs[1], lerp(2.6, 2.82, smoothstep(u)), 338.0, 540.0)
    if name == "window":
        return Camera.lerp(Camera(350.0, 650.0, 0.8), Camera(340.0, 690.0, 0.87), smoothstep(u))
    if name == "kneel":
        hx, hy = _smoothed_head(t)
        z = lerp(1.12, 1.28, smoothstep(u))
        return _face_cam(hx, hy, z, 326.0, 500.0)
    if name == "pause":
        fk = _shot_face(a)
        return _face_cam(fk[0], fk[1], lerp(3.25, 3.4, u), 350.0, 600.0)
    if name == "burst":
        z = lerp(0.8, 0.705, ease_out(clamp((t - a) / 1.6)))
        return Camera(348.0, 668.0 - 10.0 * ease_out(clamp((t - a) / 1.6)), z)
    if name == "tear":
        fk = _shot_face(a)
        z0, z1 = 3.2, 3.36
        if t < T.peak:
            return _face_cam(fk[0], fk[1], lerp(z0, z1, smoothstep((t - a) / (T.peak - a))), 352.0, 560.0)
        v = smoothstep((t - T.peak) / (b - T.peak))
        z = z1 * (0.74 / z1) ** v
        sx = lerp(352.0, 360.0 + (fk[0] - 345.0) * 0.74, v)
        sy = lerp(560.0, 640.0 + (fk[1] - 655.0) * 0.74, v)
        return _face_cam(fk[0], fk[1], z, sx, sy)
    if name == "coda":
        fk = _rae_face_ref("kneel")
        c0 = Camera(398.0, 760.0, 1.04)
        v = smoothstep((t - (T.celesta - 1.2)) / 3.4)
        z = 1.04 * (1.95 / 1.04) ** v
        c1 = _face_cam(fk[0], fk[1], z, 330.0, 520.0)
        cam = Camera.lerp(c0, c1, v) if v > 0 else c0
        cam.zoom = z
        if t > T.celesta + 2.2:
            cam.zoom = z * (1.0 + 0.03 * smoothstep((t - T.celesta - 2.2) / 2.0))
        return cam
    return Camera()


@lru_cache(maxsize=16)
def _shot_face(t):
    """Rae's actual face position at time t (used to frame a close-up from its first frame)."""
    lv = _levels(t)
    return R.head_center(_rae_pose(t, lv))


def _smoothed_head(t):
    xs = ys = 0.0
    n = 6
    for i in range(n):
        p = _rae_body(t - 0.12 * i)
        hx, hy = R.head_center(p.copy(arm_r=R.ARMS["hold_mug"]))
        xs += hx
        ys += hy
    return xs / n, ys / n


# =========================================================================== drawing


_RIB_AREA = (-140.0, 60.0, 860.0, 1260.0)
_AIR = (20.0, 230.0, 700.0, 980.0)


def _draw_world(c, t, cam, shot, lv, rp, qp, mems):
    T = _T()
    c.save()
    cam.apply(c, t)
    env.draw_lounge(c, t, light=lv.room, swirl=lv.swirl, window_bright=lv.wb)
    gx, gy = env.GALAXY_CENTER
    lb = lv.lburst * clamp(1.25 - 0.3 * cam.zoom, 0.4, 1.0)
    if lb > 0.003:
        fx.draw_light_burst(c, t, gx, gy + 20.0, lb, radius=1050.0)
    _draw_shockwave(c, t)
    if lv.rib > 0.003:
        fx.draw_ribbons(c, t, intensity=lv.rib, env=lv.rms, area=_RIB_AREA, seed=3, freeze=lv.freeze,
                        burst=lv.burst, alpha=1.0, width=1.25)
    if lv.sparkle_a > 0.01 and t >= T.first_note - 0.1:
        fx.draw_note_sparkles(c, t, T.onsets, area=_AIR, seed=2, life=1.9, alpha=0.85 * lv.sparkle_a,
                              colors=("teal_glow", "amber_soft", "#D9C8FF"), size=0.85)
    if lv.motes > 0.003:
        fx.draw_motes(c, _freeze_clock(t), area=_RIB_AREA, density=lv.motes * 0.6, env=lv.rms, color="teal_glow",
                      seed=5, rise=14.0, alpha=0.8)
    _draw_memories(c, t, "back", mems)
    bm = _bench_mug(t)
    if bm is not None:
        with Layer(c, cf=light_filter(rp.light ** 0.65, rp.tint, rp.tint_amt),
                   bounds=skia.Rect(bm[0] - 40, bm[1] - 50, bm[0] + 40, bm[1] + 10)):
            R.draw_mug(c, *bm)
    if shot == "quill_cu":
        with Layer(c):
            Q.draw(c, qp, t)
            _quill_light_band(c, t, qp)
    else:
        Q.draw(c, qp, t)
    R.draw(c, rp, t)
    env.draw_lounge_front(c, t, light=lv.room)
    _draw_note_motes(c, t, lv.rms)
    _draw_memories(c, t, "front", mems)
    if lv.motes > 0.003:
        fx.draw_motes(c, _freeze_clock(t), area=_RIB_AREA, density=lv.motes * 0.45, env=lv.rms, color="amber_soft",
                      seed=9, rise=10.0, alpha=0.75, size=0.9)
    if lv.sparks > 0.003:
        fx.draw_falling_sparks(c, t, area=_RIB_AREA, amount=lv.sparks, seed=4, fall=24.0, density=1.6)
    _draw_final_mote(c, t)
    c.restore()


def _draw_shockwave(c, t):
    """The burst: a soft ring of light racing out of the galaxy core (additive, no full-frame wash)."""
    T = _T()
    age = t - T.climax
    if not 0.0 <= age < 1.3:
        return
    gx, gy = env.GALAXY_CENTER
    u = age / 1.3
    r = 40.0 + 1100.0 * ease_out(u)
    w = 70.0 + 160.0 * u
    a = 0.55 * (1.0 - u) ** 1.5 * smoothstep(age / 0.06)
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
    T = _T()
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
        k = smoothstep((t - a) / 0.3)
        qp = qp.copy(light=qp.light + 0.1 * k, rim=qp.rim + 0.15 * k)
    cam = _camera(name, t, a, b)
    diss = 1.0
    if name == "coda":
        diss = smoothstep((t - T.final) / 1.1)
    if diss < 0.999:
        prev = [s for s in _shots() if s[0] == "tear"][0]
        _draw_world(canvas, t, _camera("tear", t, prev[1], prev[2]), "tear", lv, rp, qp, mems)
        with Layer(canvas, alpha=diss):
            _draw_world(canvas, t, cam, name, lv, rp, qp, mems)
    else:
        _draw_world(canvas, t, cam, name, lv, rp, qp, mems)
    canvas.resetMatrix()
    fx.draw_vignette(canvas, lv.vign)
    if lv.flash > 0.003:
        fx.draw_flash(canvas, lv.flash, color="#FFF6E8")
