#!/usr/bin/env python3
"""Music for "ANGER": composes AND renders every cue of BIBLE section 5.

    python3 audio/music.py                    # every cue in script_data.MUSIC_CUES
    python3 audio/music.py fall friend        # only the named cues (envelopes.json is merged)
    python3 audio/music.py --no-cache ...     # force fluidsynth re-renders

Outputs (build/music/):
    <cue>.wav          48 kHz stereo float32, EXACTLY MUSIC_CUES[cue] seconds, peak <= -1.5 dBFS
    <cue>.mid          the whole score (one named track per part, numpy parts with GM stand-ins)
    score_<cue>.txt    bar-by-bar score dump (chords, every part's notes, dynamics, melody-vs-chord
                       analysis) + CHECKS: length, peak, LUFS, sync-hit onsets, dialogue-band levels,
                       range and outer-voice parallel checks
    envelopes.json     {cue: {"rms", "low", "high": per-frame 0..1 at 24 fps, "onsets": [s],
                              "beats": [s], "downbeats": [s]}}
    build/tests/music/<cue>.png/.jpg   spectrogram + envelopes + loudness with hits and dialogue

Every sync point is a timeline beat expressed relative to the cue start (see HITS below and the
tempo-map anchors in each composer): hits are placed at exact seconds (percussion is never
humanized; sustaining instruments lean in by their attack time so their accent lands on the hit).

Anger's theme (original, D minor, low brass):  D-A-F-E | D-C-D
    | D3:q. A3:e~A3:h | F3:q. E3:e D3:q C3:q | D3:w |     (i | bVI v(4-3) | i)
The friend's waddle (original, Bb major, tuba/bassoon/pizzicato) and the lullaby (F major,
celesta + a sleepy bassoon) are the comedy material.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music_lib as ml  # noqa: E402
from music_lib import (QUAL, Cue, Note, P, Part, TempoMap, filt, gliss, hp, lp, mel_avoid, pad_notes,  # noqa: E402
                       roll, seq, shape_vels, sos_shelf, synth_boom, synth_cymbal, synth_drone, synth_heartbeat,
                       synth_shimmer, synth_sub_pedal, transpose, voice_chords)

QUAL.update({"mM7": (0, 3, 7, 11), "m7b5": (0, 3, 6, 10), "aug": (0, 4, 8), "7b9": (0, 4, 7, 10, 1),
             "m(add9)": (0, 2, 3, 7), "maj7#11": (0, 4, 6, 7, 11)})

# =========================================================================== themes

THEME = "D3:q. A3:e~ A3:h | F3:q. E3:e D3:q C3:q | D3:w"          # i | bVI v(sus4-3) | i
THEME_ANSWER = "Bb3:q. A3:e G3:q E3:q"                               # iv  V7  (back to i)
THEME_B = "F3:q. C4:e~ C4:h | Bb3:q. A3:e G3:q F3:q | E3:q. F3:e G3:q A3:q"   # III | iv7 | V7


# =========================================================================== helpers


class TL:
    """Cue-local view of build/timeline.json: beats[name], lines[id] = (t0, t1), sfx[name] = [t, ...]
    (seconds relative to the cue's start). Every sync point in the score is read from here."""

    def __init__(self, cue_name):
        tl = json.loads(Path(ml.TIMELINE).read_text())
        self.c0 = [m for m in tl["music"] if m["cue"] == cue_name][0]["start"]
        self.beats = {k: round(v - self.c0, 4) for k, v in tl["beats"].items()}
        self.lines = {ln["id"]: (round(ln["start"] - self.c0, 4), round(ln["end"] - self.c0, 4)) for ln in tl["lines"]}
        self.sfx = {}
        for sx in tl["sfx"]:
            self.sfx.setdefault(sx["name"], []).append(round(sx["start"] - self.c0, 4))

    def __getitem__(self, k):
        return self.beats[k]


class Score:
    """Collects the parts of one cue in creation order."""

    def __init__(self, tm: TempoMap):
        self.tm = tm
        self.parts = {}

    def __call__(self, name, inst, **kw) -> Part:
        p = Part(name, inst, **kw)
        self.parts[name] = p
        return p

    def N(self, sec, dur_s, pitch, vel, tag=""):
        """A note at absolute cue seconds (exact sync), duration in seconds."""
        b0, b1 = self.tm.beat(sec), self.tm.beat(sec + dur_s)
        return Note(b0, b1 - b0, P(pitch) if isinstance(pitch, str) else pitch, int(vel), tag)

    def chord_at(self, sec, dur_s, pitches, vel, tag=""):
        return [self.N(sec, dur_s, p_, vel, tag) for p_ in pitches.split()]

    def list(self, order=None):
        if order is None:
            return list(self.parts.values())
        return [self.parts[k] for k in order]


def hpf(f):
    return lambda x: hp(x, f)


def chain(*fs):
    def eq(x):
        for f in fs:
            x = f(x)
        return x
    return eq


def sul_pont(x):
    """Sul ponticello colour for tremolo strings: thin the body, lift the glassy upper partials."""
    return filt(hp(x, 700), sos_shelf(3500, 6.0))


def gallop(b0, b1, root, step=0.5, va=100, vn=64, acc=(0, 3, 6), dur=0.8, hi=12):
    """The epic 3+3+2 octave ostinato: accents on the root (low), the rest an octave above."""
    out, b, k = [], b0, 0
    while b < b1 - 1e-6:
        a = (k % 8) in acc
        out.append(Note(b, step * dur, root if a else root + hi, va if a else vn))
        b += step
        k += 1
    return out


def accents_of(notes, root):
    return [Note(n.beat, n.dur, n.pitch, n.vel) for n in notes if n.pitch == root]


def cym_note(tm, sec, vel=100):
    return Note(tm.beat(sec), 1.0, 49, vel)


# =========================================================================== cue: descent


def compose_descent() -> Cue:
    """S1 (0 -> reveal_settle, 43.6 s), under narration n01-n08 (every hit falls between lines).
    Pre-roll drone and a reverse-cymbal rush into the title HIT (title_in 0.8). The walk: from
    walk_start (4.0) one beat = 0.55 s = one footfall, so the taiko strikes EXACTLY on
    walk_start + k * 0.55 (k = 0..21, the last at 15.55 before the vines at 15.9); the 3+3+2
    galloping celli/bass ostinato and a wordless low choir; one intro bar, then Anger's theme in low
    trombones with horns an octave up (4 bars incl. the answer), coming home on D as he reaches the
    vines; a held breath (tremolo) and three brass/taiko stabs on chop1-3 (Dm - C - F); the F lifts
    the theme's second phrase (horns + trombones in octaves, choir) over four bars at his walking
    pace - F | Gm7 | A7 | Bb/A-A - with string swishes on web_swipe1/2; the dominant reached on
    door_arrive -> a tense pause on an A tremolo (soft timpani under door_try1/2, nothing under 'It was
    locked.'); back_up rebuilds on the A pedal (A -> Bb/A -> A7); charge: the run-up roll (taiko on
    his running footfalls every 0.31 s, timpani + snare rolls, a violin/viola scale, cymbal swell,
    brass crescendo) surging after n07 ends, a 100 ms breath, then the MASSIVE D-minor tutti HIT on
    door_burst; awe under 'Only in open ones.': Dm -> Bb/D -> an open Dsus2 with a harp glint on
    the reveal, fading by reveal_settle under the cavern cue. Mid-band melodic parts step back
    3-5 dB inside the narration windows (bridged across short gaps); the hits are untouched."""
    T = TL("descent")
    ws, vines = T["walk_start"], T["vines"]
    nw = int(math.floor((vines - ws) / 0.55 + 1e-9))          # last footfall on the grid before the vines
    anchors = [(-6, T["title_in"]), (0, ws), (nw, ws + nw * 0.55), (24, T["chop1"]), (26, T["chop2"]),
               (28, T["chop3"]), (36, T["web_swipe1"]), (38.5, T["web_swipe2"]), (44, T["door_arrive"]), (46, T["door_try1"]), (48, T["door_try2"]),
               (51, T["back_up"]), (55, T["charge"]), (59, T["door_burst"]), (65, T["reveal"]), (69, T["reveal_settle"])]
    tm = TempoMap(anchors)
    B = tm.beat
    S = Score(tm)
    t_burst, t_charge = T["door_burst"], T["charge"]
    bars = [B(0.0), -6, -3, 0, 4, 8, 12, 16, 20, nw, 24, 26, 28, 32, 36, 40, 44, 46, 48, 51, 55, 59, 62, 65, 69]
    chords_ = [(B(0.0), -6, "D5"), (-6, 0, "Dm"), (0, 4, "Dm"), (4, 8, "Dm"), (8, 10, "Bb"), (10, 12, "Am"),
               (12, 16, "Dm"), (16, 18, "Gm"), (18, 20, "A7"), (20, 24, "Dm"), (24, 26, "Dm"), (26, 28, "C"),
               (28, 32, "F"), (32, 36, "Gm7"), (36, 40, "A7"), (40, 42, "Bb/A"), (42, 44, "A"), (44, 51, "A5"),
               (51, 53, "A"), (53, 55, "Bb/A"), (55, 59, "A7"), (59, 62, "Dm"), (62, 65, "Bb/D"), (65, 69, "Dsus2")]

    # ---------------------------------------------------------------- the theme (trombones + horns 8va)
    hn = S("horns", "horns", pan=-0.22, send=0.34, legato=0.07, lazy=-0.03, opts={"level": -18.0, "vo_duck": 4.0})
    m1 = seq(THEME + " | " + THEME_ANSWER, 4, 86, "mel", bar=4)
    shape_vels(m1, [92, 98, 88, 82, 80, 84, 92, 88, 82, 80, 84])
    hn.add(transpose(m1, 12))
    hn.add([Note(20, 3.0, P("D4"), 84, "mel")])                          # home as he reaches the vines
    m2 = seq("F4:q. C5:e~ C5:h | Bb4:q. A4:e G4:q F4:q | E4:q. F4:e G4:q A4:q | Bb4:h A4:h", 28, 100, "mel", bar=4)
    shape_vels(m2, [118, 108, 100, 92, 96, 100, 96, 100, 106, 112, 116, 104])
    hn.add(m2)
    hn.dyn = [(3.7, 70), (12, 78), (19.5, 84), (21.5, 66), (22.9, 50), (27.9, 108), (36, 108), (39.8, 116),
              (43.6, 96), (44.3, 50), (45, 0)]
    # chop stabs (the third one IS phrase 2's first note) and the build / burst / awe chords
    hst = S("horns_hits", "horns", pan=-0.1, send=0.36, humanize=0.0, lazy=-0.04, opts={"level": -19.0})
    hst.add([Note(24, 0.7, P(p_), 112) for p_ in ("A3", "D4", "F4")])
    hst.add([Note(26, 0.7, P(p_), 116) for p_ in ("G3", "C4", "E4")])
    hst.add([Note(28, 1.2, P(p_), 120) for p_ in ("A3", "C4")])
    hst.add([Note(53, 2.0, P(p_), 90) for p_ in ("D4", "F4")])            # Bb/A crunch
    hst.add([Note(55, 4.0, P(p_), 100) for p_ in ("C#4", "E4", "G4")])     # A7 into the burst
    hst.add([Note(59, 3.0, P(p_), 127) for p_ in ("D4", "F4", "A4", "D5")])  # BURST
    hst.add([Note(62, 3.0, P(p_), 80) for p_ in ("D4", "F4", "Bb4")])     # awe: Bb/D
    hst.dyn = [(23.8, 100), (28.8, 100), (29.2, 70), (52.8, 30), (55, 56), (B(36.86), 76), (58.9, 120), (59, 127),
               (60.2, 70), (62, 54), (63.5, 60), (65, 36), (66.5, 0)]

    trb = S("trombones", "trombone", pan=0.18, send=0.3, legato=0.06, lazy=-0.04, opts={"level": -18.5, "vo_duck": 2.0})
    trb.add([Note(n.beat, n.dur, n.pitch, n.vel) for n in m1] + [Note(20, 3.0, P("D3"), 84)])
    p2 = seq("F3:q. C4:e~ C4:h | Bb3:q. A3:e G3:q F3:q | E3:q. F3:e G3:q A3:q | Bb3:h A3:h", 28, 100, bar=4)
    shape_vels(p2, [118, 108, 100, 92, 96, 100, 96, 100, 106, 112, 116, 104])
    trb.add(p2)
    trb.dyn = [(3.7, 76), (8, 80), (12, 84), (16, 88), (19.5, 92), (21.5, 70), (22.6, 30), (23.2, 0),
               (27.9, 100), (29, 92), (32, 98), (36, 104), (39.8, 112), (43.6, 96), (44.3, 50), (45, 0)]
    trh = S("trombones_hits", "trombone", pan=0.12, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -18.0})
    trh.add([Note(-6, 3.0, P(p_), 124) for p_ in ("A2", "D3", "F3")])     # TITLE
    trh.add([Note(24, 0.7, P(p_), 118) for p_ in ("A2", "D3", "F3")])
    trh.add([Note(26, 0.7, P(p_), 120) for p_ in ("G2", "C3", "E3")])
    trh.add([Note(51, 2.0, P(p_), 80) for p_ in ("A2", "C#3", "E3")])     # back_up: A
    trh.add([Note(53, 2.0, P(p_), 92) for p_ in ("Bb2", "D3", "F3")])     # Bb/A
    trh.add([Note(55, 4.0, P(p_), 104) for p_ in ("A2", "C#3", "G3")])    # A7
    trh.add([Note(59, 2.2, P(p_), 127) for p_ in ("A2", "D3", "F3", "A3")])  # BURST
    trh.dyn = [(-6.2, 127), (-5.4, 92), (-4, 54), (-1.5, 30), (0, 0), (23.8, 104), (27, 104),
               (50.9, 26), (53, 56), (55, 66), (B(36.86), 84), (58.9, 124), (59, 127), (60.2, 70), (61.2, 0)]
    tpt = S("trumpets", "trumpet", pan=0.05, send=0.4, humanize=0.0, lazy=-0.03, opts={"level": -21.0})
    tpt.add([Note(57, 2.0, P(p_), 96) for p_ in ("C#5", "E5")])
    tpt.add([Note(59, 1.6, P(p_), 127) for p_ in ("D5", "F5", "A5")])
    tpt.dyn = [(56.9, 20), (58.9, 118), (59, 127), (59.8, 90), (60.8, 0)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.22, lazy=-0.05, humanize=0.0, opts={"level": -21.0})
    tuba.add([Note(-6, 4.0, P("D2"), 124), Note(24, 0.7, P("D2"), 120), Note(26, 0.7, P("C2"), 120),
              Note(28, 4, P("F1"), 104), Note(32, 4, P("G1"), 104), Note(36, 8, P("A1"), 108),
              Note(51, 8, P("A1"), 100), Note(59, 2.5, P("D1"), 127), Note(59, 2.5, P("D2"), 127)])
    tuba.dyn = [(-6.2, 124), (-5, 80), (-3, 40), (-2, 0), (23.8, 110), (27.9, 100), (29, 70), (39.5, 92),
                (44.3, 0), (50.9, 20), (55, 64), (B(36.86), 80), (58.9, 124), (59, 127), (60.5, 70), (61.4, 0)]

    # ---------------------------------------------------------------- strings
    vc = S("celli_ost", "vc", pan=0.2, send=0.22, humanize=0.006, lazy=-0.03, opts={"level": -19.0})
    g_walk = gallop(0, nw + 0.5, P("D2"))
    g_p2 = gallop(28, 32, P("F2")) + gallop(32, 36, P("G2")) + gallop(36, 44, P("A2"))
    g_build = gallop(51, 55, P("A2"), va=96, vn=60)
    vc.add(g_walk + g_p2 + g_build)
    vc.dyn = [(-0.2, 70), (8, 80), (19.5, 88), (nw + 0.6, 40), (nw + 1, 0), (27.8, 0), (28, 100), (43.8, 108),
              (44.2, 0), (50.8, 0), (51, 44), (54.9, 104), (55.1, 0)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.2, humanize=0.006, lazy=-0.04, opts={"level": -21.5})
    cbf.add(accents_of(g_walk, P("D2")) + accents_of(g_p2, P("F2")) + accents_of(g_p2, P("G2")) +
            accents_of(g_p2, P("A2")) + accents_of(g_build, P("A2")))
    cbf.dyn = [(d[0], d[1]) for d in vc.dyn]
    cb = S("basses", "cb", pan=0.3, send=0.24, legato=0.1, lazy=-0.1, opts={"level": -22.0})
    cb.add([Note(B(0.0), -B(0.0), P("D2"), 96), Note(21, 3, P("D2"), 90), Note(59, 10, P("D2"), 110)])
    cb.dyn = [(B(0.0), 0), (-6.6, 50), (-6, 96), (-4.5, 64), (-1, 50), (0, 0), (20.8, 0), (21.3, 60), (23.9, 92),
              (24.1, 0), (58.9, 0), (59, 127), (60.2, 84), (62, 72), (65, 66), (67.5, 40), (69, 0)]
    trem = [(21, 3, "D3"), (44, 7, "A2"), (55, 4, "A2")]
    vct = S("celli_trem", "vc_trem", pan=0.15, send=0.3, humanize=0.0, opts={"level": -23.0})
    vct.add([Note(b, d, P(p_), 100) for b, d, p_ in trem])
    vct.dyn = [(20.9, 0), (21.3, 40), (23.9, 100), (24.1, 0), (43.9, 0), (44.3, 52), (45.8, 34), (49, 30),
               (50.9, 50), (54.9, 66), (55, 60), (58.95, 124), (59.05, 0)]
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.28, humanize=0.0, opts={"level": -24.0})
    cbt.add([Note(21, 3, P("D2"), 100), Note(44, 7, P("A1"), 100), Note(55, 4, P("A1"), 100)])
    cbt.dyn = list(vct.dyn)
    vlt = S("violins_trem", "vln_trem", pan=-0.3, send=0.38, humanize=0.0, opts={"level": -27.0}, eq=sul_pont)
    vlt.add([Note(44.4, 6.6, P("A5"), 70), Note(44.4, 6.6, P("E6"), 60)])
    vlt.add([Note(51, 2, P(p_), 90) for p_ in ("A4", "C#5", "E5")] + [Note(53, 2, P(p_), 96) for p_ in ("Bb4", "D5", "F5")])
    vlt.dyn = [(44.3, 0), (45.2, 40), (50.8, 44), (51, 36), (53, 52), (54.9, 70), (55.05, 0)]
    vlat = S("violas_trem", "vla_trem", pan=0.12, send=0.34, humanize=0.0, opts={"level": -25.0})
    vlat.add([Note(51, 2, P(p_), 90) for p_ in ("E4", "A4")] + [Note(53, 2, P(p_), 96) for p_ in ("F4", "Bb4")])
    vlat.add([Note(55, 4, P(p_), 100) for p_ in ("E4", "G4")])
    vlat.dyn = [(50.9, 0), (51.2, 36), (53, 56), (55, 64), (B(36.86), 80), (58.95, 122), (59.05, 0)]
    # swishes on the web swipes + the run-up scale into the burst (16ths), landing on the hit
    vln = S("violins", "vln1", pan=-0.32, send=0.32, humanize=0.0, lazy=-0.02, opts={"level": -20.5})
    for sw in (T["web_swipe1"], T["web_swipe2"]):
        for k, p_ in enumerate(("D4", "F4", "A4", "C5", "D5")):
            vln.add([S.N(sw - 0.26 + k * 0.055, 0.12 if k < 4 else 0.35, p_, 70 + 8 * k)])
    run = ["A3", "Bb3", "C#4", "D4", "E4", "F4", "G4", "A4", "Bb4", "C#5", "D5", "E5", "F5", "G5", "A5", "C#6"]
    for k, p_ in enumerate(run):
        vln.add([Note(55 + k * 0.25, 0.3, P(p_), 70 + 3 * k)])
    vln.add([Note(59, 3.0, P(p_), 127) for p_ in ("D5", "A5", "D6")])    # BURST
    vln.dyn = [(35.5, 96), (39, 96), (54.9, 56), (B(36.86), 80), (58.9, 118), (59, 127), (60.4, 80), (61.6, 0)]
    vlar = S("violas", "vla_fast", pan=0.16, send=0.3, humanize=0.0, lazy=-0.02, opts={"level": -22.5})
    for k, p_ in enumerate(run[:12]):
        vlar.add([Note(56 + k * 0.25, 0.3, P(p_), 70 + 3 * k)])
    vlar.add([Note(59, 3.0, P(p_), 127) for p_ in ("F4", "A4", "D5")])
    vlar.dyn = [(55.9, 50), (B(36.86), 80), (58.9, 116), (59, 127), (60.4, 80), (61.6, 0)]
    # awe (under 'Only in open ones.'): slow high strings Dm -> Bb/D -> Dsus2
    awe = S("violins_awe", "vln_slow", pan=-0.25, send=0.5, lazy=-0.15, opts={"level": -23.5, "vo_duck": 3.0})
    awe.add([Note(59.6, 2.4, P("A5"), 90), Note(59.6, 2.4, P("F5"), 86), Note(62, 3, P("Bb5"), 90),
             Note(62, 3, P("F5"), 86), Note(65, 4, P("A5"), 92), Note(65, 4, P("E5"), 88), Note(65, 4, P("D6"), 84)])
    awe.dyn = [(59.5, 0), (60.6, 56), (62, 64), (64, 74), (65, 84), (66.5, 70), (68.2, 30), (69, 0)]
    vca = S("celli_awe", "vc_slow", pan=0.2, send=0.4, lazy=-0.12, opts={"level": -23.5})
    vca.add([Note(59, 10, P("D3"), 100), Note(59, 3, P("A3"), 96), Note(62, 3, P("Bb3"), 96), Note(65, 4, P("A3"), 96)])
    vca.dyn = [(58.9, 0), (59, 120), (60.2, 72), (62, 64), (65, 72), (67.5, 40), (69, 0)]

    # ---------------------------------------------------------------- choir
    oo = S("low_choir", "oohs", pan=0.05, send=0.45, legato=0.12, lazy=-0.18, opts={"level": -24.0, "vo_duck": 3.0})
    oc = [c for c in chords_ if -6 <= c[0] < 24]
    ov = voice_chords(oc, 3, 45, 62, avoid=mel_avoid(oc, m1, bars=bars), min_gap=3)
    oo.add(pad_notes(oc, ov, {"o": [0, 1, 2]}, 80)["o"])
    oo.add([Note(44.2, 6.8, P(p_), 76) for p_ in ("A2", "E3", "A3")])     # the door: hummed A
    oo.dyn = [(-6.2, 0), (-5.6, 56), (-3, 62), (0, 66), (8, 72), (19.5, 80), (23.9, 70), (24.05, 0),
              (44.1, 0), (45.3, 44), (50.9, 50), (51.1, 0)]
    ch = S("choir", "choir", pan=0.0, send=0.5, legato=0.12, lazy=-0.2, opts={"level": -20.5, "vo_duck": 4.0})
    cc = [c for c in chords_ if 28 <= c[0] < 44]
    cv = voice_chords(cc, 4, 50, 67, top_max=67)
    ch.add(pad_notes(cc, cv, {"c": [0, 1, 2, 3]}, 96)["c"])
    bc = [(51, 53, "A"), (53, 55, "Bb/A"), (55, 59, "A7")]
    bv = voice_chords(bc, 4, 52, 69, prev=cv[-1])
    ch.add(pad_notes(bc, bv, {"c": [0, 1, 2, 3]}, 100)["c"])
    ch.add([Note(59, 3, P(p_), 127) for p_ in ("D3", "A3", "D4", "F4", "A4")])
    ch.add([Note(62, 3, P(p_), 110) for p_ in ("D3", "Bb3", "D4", "F4", "Bb4")])
    ch.add([Note(65, 4, P(p_), 104) for p_ in ("D3", "A3", "E4", "A4")])
    ch.dyn = [(27.8, 0), (28, 84), (32, 92), (36, 100), (43.8, 108), (44.3, 0), (50.9, 0), (51.3, 36),
              (55, 64), (B(36.86), 84), (58.9, 122), (59, 127), (60.3, 84), (62, 86), (63.5, 94), (65, 92), (67, 70),
              (68.6, 30), (69, 0)]

    # ---------------------------------------------------------------- percussion (sync-locked)
    tk = S("taiko", "taiko", pan=0.0, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -16.0})
    tkh = S("taiko_hi", "taiko", pan=-0.18, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -20.5})
    tk.add([Note(-6, 2, P("C2"), 127)])
    tkh.add([Note(-6, 2, P("A2"), 112)])
    S.footfalls = []
    for k in range(nw + 1):                               # the walk: one drum per footfall, exactly on the grid
        ramp = min(1.0, k / 14)
        t_ = ws + 0.55 * k
        S.footfalls.append(round(t_, 3))
        if k % 2 == 0:
            tk.add([S.N(t_, 0.5, "C2", int(98 + 18 * ramp - (14 if k >= nw - 1 else 0)))])
        else:
            tkh.add([S.N(t_, 0.5, "A2", int(80 + 14 * ramp - (12 if k >= nw - 1 else 0)))])
    tkh.add([Note(7.5, 0.5, P("C3"), 62), Note(15.5, 0.5, P("C3"), 66)])
    for b, v in ((24, 127), (26, 127), (28, 127)):
        tk.add([Note(b, 2, P("C2"), v)])
        tkh.add([Note(b, 2, P("F2"), v - 10)])
    for b in range(29, 44):
        (tk if b % 2 else tkh).add([Note(b, 1, P("C2") if b % 2 else P("A2"), 80 if b % 2 else 68)])
    for sw in (T["web_swipe1"], T["web_swipe2"]):
        tkh.add([S.N(sw, 0.5, "F2", 118)])
    for b, v in ((51, 84), (52, 70), (53, 96), (53.5, 70), (54, 100), (54.5, 84)):
        tk.add([Note(b, 1, P("C2"), v)])
    S.run_footfalls = []
    k = 0
    while t_charge + 0.31 * k < t_burst - 0.3:            # the run: his footfalls, every 0.31 s
        S.run_footfalls.append(round(t_charge + 0.31 * k, 3))
        tk.add([S.N(t_charge + 0.31 * k, 0.3, "C2", 100 + 5 * k)])
        k += 1
    for k in range(4):
        tkh.add([S.N(t_burst - 0.4 + 0.1 * k, 0.1, "C3", 84 + 10 * k)])
    tk.add([Note(59, 3, P("C2"), 124)])
    tkh.add([S.N(t_burst + 0.004, 1.5, "F2", 120)])
    boom = S("boom", "boom", synth=synth_boom, pan=0.0, send=0.12, opts={"decay": 0.45, "slap": 0.0, "level": -18.0})
    for k in range(0, nw + 1, 2):
        boom.add([S.N(ws + 0.55 * k, 0.5, "D1", 104 if k % 4 == 0 else 86)])
    boom.add([Note(24, 1, P("D1"), 120), Note(26, 1, P("C2"), 116), Note(28, 1, P("F1"), 124),
              Note(32, 1, P("G1"), 104), Note(36, 1, P("A1"), 108), Note(51, 1, P("A1"), 96), Note(53, 1, P("A1"), 104)])
    bigb = S("boom_big", "boom", synth=synth_boom, pan=0.0, send=0.1, opts={"decay": 1.3, "slap": 0.25, "drop": 1.6,
                                                                              "sat": 1.4, "peak": -5.5})
    bigb.add([Note(-6, 2, P("D1"), 118), Note(59, 2, P("D1"), 127), Note(59, 2, P("A1"), 92)])
    timp = S("timpani", "timpani", pan=0.14, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    timp.add([Note(-6, 2, P("D2"), 122)])
    timp.add([Note(b, 1.5, P("D2"), 66) for b in (4, 8, 12, 16)])
    timp.add([Note(24, 1.5, P("D2"), 118), Note(26, 1.5, P("C3"), 118), Note(28, 2, P("F2"), 122),
              Note(32, 2, P("G2"), 96), Note(36, 2, P("A2"), 100)])
    timp.add([S.N(T["door_try1"], 0.8, "A2", 60), S.N(T["door_try2"], 0.8, "A2", 72)])   # under the locked-door thuds
    timp.add([Note(51, 1, P("A2"), 76), Note(53, 1, P("A2"), 88)])
    timp.add(roll(P("A2"), 55, 58.95, tm, 12, 40, 118))
    timp.add([S.N(t_burst + 0.007, 1.6, "D2", 124)])
    bd = S("gran_cassa", "bass_drum", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    bd.add([Note(-6, 3, P("A1"), 116), Note(28, 3, P("A1"), 96), S.N(t_burst + 0.003, 2.0, "A1", 127)])
    kit = S("snare_cym", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -24.0})
    t_ = t_charge
    while t_ < t_burst - 0.03:
        x = (t_ - t_charge) / (t_burst - t_charge)
        kit.add([S.N(t_, 0.05, 38, int(36 + 80 * x ** 1.4))])
        t_ += 0.055
    kit.add([S.N(t_burst + 0.009, 1.0, 49, 120), S.N(t_burst + 0.012, 1.0, 57, 106), S.N(t_burst + 0.006, 0.3, 38, 116)])
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -24.0})
    sw1, sw2 = T["web_swipe1"], T["web_swipe2"]
    cym.opts["events"] = [(0.0, T["title_in"], 0.55, 0.85, 2.0, 3.6),
                          (sw1 - 0.35, sw1, 0.22, 0.18, 0.7, 2.5), (sw2 - 0.35, sw2, 0.22, 0.18, 0.7, 2.5),
                          (t_charge, t_burst, 1.0, 1.0, 3.6, 3.4),
                          (T["reveal"] - 0.9, T["reveal"], 0.18, 0.16, 2.5, 2.0)]
    cym.notes = [cym_note(tm, T["title_in"], 100), cym_note(tm, t_burst, 127), cym_note(tm, T["reveal"], 50)]

    # ---------------------------------------------------------------- low end, colour
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, pan=0.0, send=0.0,
            opts={"attack": 0.3, "release": 0.12, "release_end": 1.0, "h2": 0.2, "h3": 0.06, "level": -21.0})
    sub.add([Note(B(0.0), 28 - B(0.0), P("D1"), 100), Note(28, 4, P("F1"), 96), Note(32, 4, P("G1"), 96),
             Note(36, 15, P("A1"), 92), Note(51, 8, P("A1"), 100), Note(59, 10, P("D1"), 110)])
    sub.dyn = [(B(0.0), 0), (-6.3, 60), (-6, 110), (-4, 70), (0, 76), (20, 84), (24, 96), (28, 100), (44, 64),
               (51, 70), (58.9, 112), (59, 127), (61, 96), (65, 80), (67.5, 50), (69, 0)]
    harp = S("harp", "harp", pan=-0.4, send=0.55, humanize=0.0, opts={"level": -26.0})
    harp.add(gliss({2, 4, 9}, P("D3"), P("A6"), 64.2, 0.8, 50, 90, ring=4.0))
    cel = S("celesta", "celesta", pan=0.3, send=0.6, humanize=0.0, opts={"level": -28.0})
    cel.add([Note(65, 3, P("A6"), 70), Note(65.5, 3, P("E6"), 60), Note(66.5, 2.5, P("D6"), 56)])
    shim = S("shimmer", "shimmer", synth=synth_shimmer, pan=0.0, send=0.6, opts={"level": -30.0})
    shim.add([Note(61, 8, P("A5"), 80), Note(61, 8, P("E6"), 80)])
    shim.dyn = [(61, 0), (63, 70), (65, 100), (67.5, 60), (69, 0)]

    for nm, f in (("horns", 70), ("horns_hits", 90), ("trombones", 60), ("trombones_hits", 50), ("trumpets", 180),
                  ("celli_ost", 45), ("basses_ost", 30), ("basses", 30), ("celli_trem", 60), ("basses_trem", 30),
                  ("violins", 160), ("violas", 110), ("violins_awe", 200), ("celli_awe", 60), ("low_choir", 80),
                  ("choir", 100), ("taiko", 30), ("taiko_hi", 40), ("timpani", 32), ("gran_cassa", 25),
                  ("snare_cym", 120), ("harp", 90), ("celesta", 300), ("tuba", 25)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    cb.eq = ml.fundamental_lift(cb.notes, tm, 4.0, lo_pitch=P("A1"), base=hpf(25))

    hits = [(T[k], k) for k in ("title_in", "walk_start", "chop1", "chop2", "chop3", "web_swipe1", "web_swipe2",
                                "door_arrive", "door_try1", "door_try2", "back_up", "charge", "door_burst", "reveal")]
    n07_end = T.lines["n07"][1]
    # the whole-cue dynamic arc (seconds -> dB): brooding after the title, the walk building, the chops and
    # the second phrase strong, the door hushed, the build held under n07 then surging, a 100 ms breath,
    # the burst on top, awe settling under n08
    arc = [(0.0, -3.0), (T["title_in"] - 0.06, -1.0), (T["title_in"] - 0.012, -8.0), (T["title_in"], 0.0), (1.8, -3.5), (3.0, -8.0), (ws, -8.5), (9.0, -7.5), (14.5, -6.0),
           (15.6, -7.5), (T["chop1"] - 0.1, -6.0), (T["chop1"], -2.0), (T["chop3"], -1.5), (sw2, -1.5),
           (T["door_arrive"] - 0.3, -0.5), (T["door_arrive"], -3.0), (T["back_up"], -6.5), (t_charge, -7.0),
           (n07_end, -6.5), (t_burst - 0.14, -5.0), (t_burst - 0.03, -15.0), (t_burst, -0.5), (t_burst + 1.0, -1.0),
           (t_burst + 2.0, -2.0), (T["reveal"], -1.5), (T["reveal_settle"], -5.0)]
    cue = Cue("descent", tm, bars, chords_, S.list(), rt60=3.2, wet=0.36, predelay=0.03, target_lufs=-17.0,
              fade_in=0.01, fade_out=1.2, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0), carve_db=4.0,
              master_vol=[(B(t_), v_) for t_, v_ in arc], wet_duck=[(t_burst - 0.14, t_burst - 0.005, 0.35, 0.05)],
              hits=hits, landmarks=[(T["title_out"], "title_out"), (T["vines"], "vines"), (T["webs"], "webs")],
              top_parts=("horns",), bass_parts=("basses", "basses_ost", "tuba"))
    cue.notes_txt = (compose_descent.__doc__ + "\nTaiko footfalls (walk, s): " + ", ".join(f"{x:.2f}" for x in S.footfalls)
                     + "\nTaiko footfalls (charge run, s): " + ", ".join(f"{x:.2f}" for x in S.run_footfalls))
    return cue


# =========================================================================== cue: cavern


def compose_cavern() -> Cue:
    """S2 (reveal 36.5 -> torch_splash 57.7; 21.2 s, cue-local seconds below). Vast mystery at 60 bpm
    over a D pedal: the open Dsus2 inherited from the descent's reveal, wide low string pad + bowed
    glass, a distant high choir line (A4 - Bb4 - A4), harp and celesta glints in D Dorian from
    look_around (3.0), a soft pizzicato pulse from search_start (7.5). STING on eyes_glow (12.0):
    sul-ponticello violin cluster C#6-D6-Eb6, stopped horns A3/Bb3, a low piano cluster, timpani and
    a cold celesta tritone; a skittering pizzicato run on eyes_scurry (13.3); unease (Eb/D -> Dm(maj7))
    creeping up; a stumble accent on stone_shift (19.5); on torch_fly (19.9) everything surges (A7b9,
    timpani roll, rising tremolo glissando, cymbal swell) and is CUT DEAD at torch_splash (21.2)."""
    tm = TempoMap.const(60)
    S = Score(tm)
    bars = [0, 4, 8, 12, 16, 19.5, 21.2]
    chords_ = [(0, 3, "Dsus2"), (3, 7.5, "Dm(add9)"), (7.5, 12, "Bbmaj7/D"), (12, 16, "Eb/D"),
               (16, 19.5, "DmM7"), (19.5, 21.2, "A7b9")]

    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 1.5, "release_end": 0.05, "h2": 0.25,
                                                             "h3": 0.08, "level": -24.0})
    sub.add([Note(0, 19.5, P("D1"), 90), Note(19.5, 1.75, P("A1"), 100)])
    sub.dyn = [(0, 30), (3, 70), (12, 80), (19.4, 76), (19.6, 70), (21.2, 120)]
    cb = S("basses", "cb", pan=0.28, send=0.4, legato=0.1, lazy=-0.1, opts={"level": -24.0})
    cb.add([Note(0.0, 19.5, P("D2"), 90)])
    cb.dyn = [(0, 0), (2.5, 50), (8, 56), (12, 70), (13.5, 50), (19.4, 60), (19.55, 0)]
    vcp = S("celli_pad", "vc_slow", pan=0.18, send=0.45, legato=0.12, lazy=-0.15, opts={"level": -25.0})
    vcp.add([Note(0.3, 7.2, P("A2"), 84), Note(0.3, 11.7, P("D3"), 84), Note(7.5, 4.5, P("F3"), 80),
             Note(12, 4, P("Eb3"), 86), Note(12, 4, P("G3"), 80), Note(16, 3.5, P("F3"), 84), Note(16, 3.5, P("A3"), 80)])
    vcp.dyn = [(0, 0), (2.8, 48), (7.5, 52), (11.8, 50), (12, 80), (13.2, 52), (16, 56), (19.4, 64), (19.55, 0)]
    gl = S("glass", "glass_pad", pan=0.0, send=0.6, lazy=-0.3, opts={"level": -27.0, "vo_duck": 2.0})
    gc = [c for c in chords_ if c[0] < 19.5]
    gv = voice_chords(gc, 3, 57, 76, min_gap=3)
    gl.add(pad_notes(gc, gv, {"g": [0, 1, 2]}, 70)["g"])
    gl.dyn = [(0, 0), (2.5, 40), (6, 64), (11.5, 60), (12, 84), (14, 56), (19, 64), (19.5, 0)]
    oo = S("far_choir", "oohs", pan=-0.15, send=0.75, legato=0.2, lazy=-0.25, opts={"level": -27.5, "vo_duck": 3.0})
    oo.add(seq("A4:4.5 Bb4:4.5 A4:7.5", 3.0, 70, "mel"))
    oo.dyn = [(3, 0), (4.5, 50), (7.5, 58), (9.5, 64), (11.8, 56), (12, 72), (13.5, 50), (19.3, 58), (19.5, 0)]

    harp = S("harp", "harp", pan=-0.42, send=0.6, humanize=0.006, opts={"level": -24.0})
    glint = [(3.0, "D5"), (3.5, "A5"), (4.25, "E6"), (5.25, "F5"), (6.0, "C6"), (6.75, "G5"), (7.5, "D4"),
             (8.0, "A4"), (8.5, "F5"), (9.0, "A5"), (9.5, "D4"), (10.0, "Bb4"), (10.5, "F5"), (11.0, "C6"),
             (11.5, "D4"), (14.5, "D4"), (15.0, "Bb4"), (16.5, "D4"), (17.0, "F4"), (17.5, "C#5"), (18.5, "D4"),
             (19.0, "A4")]
    for t_, p_ in glint:
        harp.add([Note(t_, 2.5, P(p_), 58 if P(p_) > 62 else 50, "mel" if P(p_) > 62 else "")])
    cel = S("celesta", "celesta", pan=0.35, send=0.7, humanize=0.006, opts={"level": -27.0})
    cel.add(seq("r:3.75 E6:1 r:1 A6:1.25 r:1 D7:1 r:1.5 F6:1 r:1.5 C7:1", 0, 46, "mel"))
    cel.add([Note(12.0, 2.5, P("G#6"), 96), Note(12.0, 2.5, P("D7"), 90)])       # the eyes: cold tritone
    pz = S("pizz_pulse", "cb_pizz", pan=0.25, send=0.4, humanize=0.006, opts={"level": -26.0})
    pz.add([Note(b, 1.5, P("D2"), 70 + (6 if k % 2 == 0 else 0)) for k, b in enumerate((7.5, 9.5, 11.5, 15.5, 17.5))])
    pz.add([Note(19.5, 1.0, P("D2"), 110)])                                    # stone_shift

    # ---------------------------------------------------------------- the sting (eyes_glow 12.0)
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.5, humanize=0.0, lazy=-0.03, eq=sul_pont,
           opts={"level": -24.0})
    vt.add([Note(12, 4, P(p_), 112) for p_ in ("C#6", "D6", "Eb6")])
    vt.add([Note(16, 3.5, P("C#6"), 80)])
    vt.add([Note(19.9, 1.35, P(p_), 100) for p_ in ("A5", "Bb5")])
    vt.bend = [(19.9, 0), (21.2, 500)]
    vt.bend_range = 7
    vt.dyn = [(11.95, 120), (12.25, 92), (13.3, 44), (15.9, 40), (16.3, 28), (19.4, 36), (19.85, 0), (19.9, 50),
              (21.2, 127)]
    hs = S("horns_stopped", "horns", pan=-0.2, send=0.5, humanize=0.0, lazy=-0.04,
           eq=lambda x: filt(hp(x, 120), sos_shelf(2200, 5.0)), opts={"level": -22.0})
    hs.add([Note(12, 1.4, P("A3"), 124), Note(12, 1.4, P("Bb3"), 124)])
    hs.add([Note(19.9, 1.35, P(p_), 100) for p_ in ("C#4", "G4", "Bb4")])
    hs.dyn = [(11.95, 124), (12.4, 70), (13.3, 0), (19.85, 0), (19.9, 30), (21.2, 127)]
    pno = S("piano_low", "piano", pan=0.0, send=0.5, humanize=0.0, opts={"level": -24.0})
    pno.add([Note(12, 3, P(p_), 100) for p_ in ("D1", "Eb1", "A1")])
    pno.pedal = [(11.9, 15.5)]
    timp = S("timpani", "timpani", pan=0.12, send=0.4, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    timp.add([Note(12, 2, P("D2"), 92), Note(19.5, 0.5, P("D2"), 104)])
    timp.add(roll(P("A2"), 19.95, 21.2, tm, 13, 40, 120))
    sk = S("scurry_pizz", "vln_pizz", pan=0.35, send=0.5, humanize=0.0, opts={"level": -25.0})
    run = ["Eb6", "D6", "C#6", "C6", "B5", "Bb5", "A5", "G#5", "G5", "F#5"]
    sk.add([S.N(13.3 + 0.055 * k, 0.2, p_, 96 - 3 * k) for k, p_ in enumerate(run)])
    skv = S("scurry_pizz_lo", "vla_pizz", pan=-0.2, send=0.5, humanize=0.0, opts={"level": -27.0})
    skv.add([S.N(13.33 + 0.07 * k, 0.2, p_, 84 - 3 * k) for k, p_ in enumerate(["G#4", "G4", "F#4", "F4", "E4", "Eb4"])])

    # ---------------------------------------------------------------- unease + the torch swell
    vct = S("celli_trem", "vc_trem", pan=0.15, send=0.45, humanize=0.0, opts={"level": -24.0})
    vct.add([Note(13.5, 6.0, P("D3"), 90), Note(19.9, 1.35, P("A2"), 100)])
    vct.dyn = [(13.4, 0), (14.5, 30), (19.4, 64), (19.55, 30), (19.9, 50), (21.2, 127)]
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.4, humanize=0.0, opts={"level": -25.0})
    cbt.add([Note(19.9, 1.35, P("A1"), 100)])
    cbt.dyn = [(19.85, 0), (19.9, 40), (21.2, 127)]
    vlt = S("violas_trem", "vla_trem", pan=0.1, send=0.45, humanize=0.0, opts={"level": -25.0})
    vlt.add([Note(16, 3.5, P("F4"), 80), Note(16, 3.5, P("A4"), 76)])
    vlt.add([Note(19.9, 1.35, P(p_), 100) for p_ in ("E4", "G4")])
    vlt.dyn = [(15.9, 0), (16.6, 30), (19.4, 50), (19.6, 30), (19.9, 46), (21.2, 127)]
    trb = S("trombones", "trombone", pan=0.18, send=0.4, humanize=0.0, lazy=-0.06, opts={"level": -21.0})
    trb.add([Note(19.9, 1.35, P(p_), 100) for p_ in ("A2", "E3", "G3")])
    trb.dyn = [(19.85, 0), (19.9, 24), (21.2, 127)]
    ch = S("choir", "choir", pan=0.0, send=0.55, humanize=0.0, lazy=-0.2, opts={"level": -23.0})
    ch.add([Note(19.7, 1.55, P(p_), 100) for p_ in ("A3", "C#4", "G4", "Bb4")])
    ch.dyn = [(19.65, 0), (19.9, 30), (21.2, 127)]
    tk = S("taiko", "taiko", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    tk.add([S.N(19.5, 0.5, "A2", 96)])
    for k in range(7):
        tk.add([S.N(20.5 + 0.1 * k, 0.1, "C2", 70 + 8 * k)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.5, "slap": 0.0, "level": -21.0})
    boom.add([Note(12, 1, P("D1"), 110), Note(19.5, 1, P("D1"), 100)])
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.5, opts={"level": -23.0})
    cym.opts["events"] = [(19.9, 21.25, 1.0, 0.0, 1.0, 2.6)]
    cym.notes = [cym_note(tm, 19.9, 90)]
    shim = S("shimmer", "shimmer", synth=synth_shimmer, pan=0.0, send=0.7, opts={"level": -31.0})
    shim.add([Note(0, 7.5, P("A5"), 80), Note(0, 7.5, P("E6"), 80)])
    shim.dyn = [(0, 70), (3, 100), (6, 60), (7.5, 0)]

    for nm, f in (("basses", 30), ("celli_pad", 55), ("glass", 140), ("far_choir", 150), ("harp", 60),
                  ("celesta", 300), ("pizz_pulse", 30), ("piano_low", 28), ("timpani", 32), ("scurry_pizz", 300),
                  ("scurry_pizz_lo", 150), ("celli_trem", 60), ("basses_trem", 30), ("violas_trem", 120),
                  ("trombones", 60), ("choir", 100), ("taiko", 40)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    arc = [(0.0, -6.0), (2.5, -3.0), (11.99, -2.0), (12.0, -1.5), (13.5, -2.5), (15.0, -3.0), (19.4, -1.5), (19.9, -1.5), (21.2, 0.5)]
    T = TL("cavern")
    hits = [(T[k], k) for k in ("reveal", "look_around", "search_start", "eyes_glow", "eyes_scurry", "stone_shift",
                                "torch_fly")] + [(T["torch_splash"], "torch_splash (cut)")]
    assert [round(h[0], 3) for h in hits] == [0.0, 3.0, 7.5, 12.0, 13.3, 19.5, 19.9, 21.2], hits
    cue = Cue("cavern", tm, bars, chords_, S.list(), rt60=4.2, wet=0.42, predelay=0.04, target_lufs=-17.5,
              fade_in=0.3, end_cut=True, send_hp=70.0, comp=(-8.0, 1.3, 25.0, 300.0),
              master_vol=arc, hits=hits, top_parts=("far_choir", "harp", "celesta"), bass_parts=("basses",))
    cue.notes_txt = compose_cavern.__doc__
    return cue


# =========================================================================== cue: tension


def compose_tension() -> Cue:
    """continue (69.1) -> collapse (78.3); 9.2 s. A felt heartbeat (lub-dub) that quickens from
    ~68 to ~86 bpm while he creeps forward; contrabass tremolo on D, a chromatic viola creep
    (A3 -> Bb3 -> B3) and a glassy sul-ponticello violin harmonic note above; at wrong_rock (8.6) the
    heart stops - only a reverse swell and a low brass/choir crescendo rise into the cut at 9.2,
    exactly where the fall cue's collapse HIT begins."""
    beats = [0.25]
    iv = 0.88
    while beats[-1] + iv < 8.45:
        beats.append(beats[-1] + iv)
        iv = max(0.70, iv * 0.968)
    anchors = [(k, t_) for k, t_ in enumerate(beats)]
    nb = len(beats)
    anchors.append((nb, 9.2))
    tm = TempoMap(anchors)
    S = Score(tm)
    bars = [0, 4, 8, nb]
    chords_ = [(0, nb - 1, "Dm"), (nb - 1, nb, "Bb/D")]
    hb = S("heartbeat", "heartbeat", synth=synth_heartbeat, opts={"gap": 0.2, "dub": 0.6, "decay": 0.1,
                                                                  "level": -18.0})
    hb.add([Note(k, 0.5, P("A1"), int(88 + 30 * k / max(1, nb - 1)), "mel") for k in range(nb)])
    B = tm.beat
    cbt = S("basses_trem", "cb_trem", pan=0.25, send=0.35, humanize=0.0, opts={"level": -23.0})
    cbt.add([Note(B(0.0), B(8.6) - B(0.0), P("D2"), 100)])
    cbt.dyn = [(B(0.0), 20), (B(4.0), 46), (B(8.4), 70), (B(8.6), 0)]
    vlt = S("violas_trem", "vla_trem", pan=0.1, send=0.4, humanize=0.0, opts={"level": -25.0})
    vlt.add([Note(B(0.4), B(3.4) - B(0.4), P("A3"), 90), Note(B(3.4), B(6.2) - B(3.4), P("Bb3"), 92),
             Note(B(6.2), B(8.6) - B(6.2), P("B3"), 96)])
    vlt.dyn = [(B(0.3), 0), (B(1.5), 34), (B(5), 52), (B(8.4), 76), (B(8.6), 0)]
    vh = S("violins_harm", "vln_trem", pan=-0.3, send=0.5, humanize=0.0, eq=sul_pont, opts={"level": -28.0})
    vh.add([Note(B(0.0), B(8.7) - B(0.0), P("D6"), 70)])
    vh.dyn = [(B(0.0), 0), (B(1.2), 30), (B(8.0), 50), (B(8.6), 60), (B(9.2), 90)]
    trb = S("low_brass", "trombone", pan=0.12, send=0.4, humanize=0.0, lazy=-0.05, opts={"level": -21.0})
    trb.add([Note(B(8.5), B(9.25) - B(8.5), P(p_), 100) for p_ in ("D3", "F3", "Bb3")])
    trb.dyn = [(B(8.5), 0), (B(8.6), 20), (B(9.2), 120)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -22.0})
    tuba.add([Note(B(8.5), B(9.25) - B(8.5), P("D2"), 100)])
    tuba.dyn = [(B(8.5), 0), (B(8.6), 20), (B(9.2), 120)]
    rc = S("rev_cymbal", "rev_cym", pan=0.0, send=0.3, humanize=0.0, opts={"level": -24.0})
    # the sampled reverse cymbal peaks 1.37 s after its note-on (measured): start it so it peaks at the cut
    rc.add([S.N(9.2 - 1.37, 1.4, 60, 110)])
    ch = S("choir", "oohs", pan=0.0, send=0.5, humanize=0.0, lazy=-0.2, opts={"level": -25.0})
    ch.add([Note(B(8.4), B(9.25) - B(8.4), P(p_), 100) for p_ in ("D3", "F3", "Bb3", "D4")])
    ch.dyn = [(B(8.4), 0), (B(8.7), 30), (B(9.2), 110)]
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.8, "h2": 0.2, "level": -26.0})
    sub.add([Note(B(0.0), B(9.2) - B(0.0), P("D1"), 90)])
    sub.dyn = [(B(0.0), 40), (B(8.0), 70), (B(8.6), 50), (B(9.2), 110)]
    for nm, f in (("basses_trem", 30), ("violas_trem", 120), ("low_brass", 60), ("tuba", 25), ("choir", 90),
                  ("rev_cymbal", 300)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    T = TL("tension")
    hits = [(T["continue"], "continue"), (T["cracks_seen"], "cracks_seen"), (T["wrong_rock"], "wrong_rock"),
            (T["collapse"], "collapse (cut)")]
    assert abs(T["wrong_rock"] - 8.6) < 1e-6 and abs(T["collapse"] - 9.2) < 1e-6
    # cracks_seen: a faint, cold glint far above the voice band (thin cracks spreading)
    gk = S("crack_glint", "glock", pan=0.3, send=0.6, humanize=0.0, opts={"level": -31.0})
    gk.add([S.N(T["cracks_seen"], 0.6, "C#7", 60), S.N(T["cracks_seen"] + 0.07, 0.6, "G7", 52),
            S.N(T["cracks_seen"] + 0.19, 0.6, "D7", 44)])
    gk.eq = hpf(1500)
    cue = Cue("tension", tm, bars, chords_, S.list(), rt60=3.4, wet=0.36, predelay=0.03, target_lufs=-18.0,
              fade_in=0.2, end_cut=True, send_hp=80.0, comp=(-10.0, 1.3, 20.0, 250.0),
              master_vol=[(B(0.0), -4.0), (B(4.0), -2.0), (B(8.5), 0.0)], hits=hits,
              landmarks=[(beats[k], "") for k in range(0, nb, 4)], top_parts=("violins_harm",),
              bass_parts=("basses_trem",))
    cue.notes_txt = compose_tension.__doc__ + f"\nHeartbeats at: {', '.join(f'{b_:.2f}' for b_ in beats)} s"
    return cue


# =========================================================================== cue: fall


def compose_fall() -> Cue:
    """S3 (collapse -> fall_end; 20.0 s) under narration n16-n20. HIT on the collapse (0.0): an
    Eb-major-over-D shock chord, tutti percussion. grab_ledge (1.0): a horn stab, then the STRAIN
    under n16 (beat = 0.725 s, taiko pulse): a chromatic string wedge - violins I climb A5-Bb5-B5-C6
    over a held D5 while the tremolo violas sink F4-E4-Eb4-D4 - and from slipping (2.7) the trombones
    drag down A2-G#2-G2, each step swelling harder. let_go (6.8): everything stops. falling (7.0):
    time stops - a solemn, soft sustained choir chord (Bb add9) with a high string halo under 'Anger
    did not scream.' / 'He simply closed his eyes.', a short inhale into sword_thrust (12.2): the
    SURGE - Anger's theme ff in horns / trumpets / trombones (0.544 s per beat), driving celli and
    basses, taiko 8ths, a snare roll, screeching sul-ponticello violins gliding upward - timed so the
    theme's arrival IS sword_clang (16.55): a violent short Eb/D stop-hit (booms, taiko, gran cassa,
    crash) and the screech and the whole surge CUT DEAD (stems and hall); freefall (16.7): a fast
    A7b9 crescendo from nothing (low brass, choir, tremolo strings, timpani roll, reverse cymbal), a
    100 ms breath, and the thunderous final D-minor HIT on impact (18.0) with the biggest booms of the
    film, then nothing (only its decay) to fall_end. Mid-band parts step back under the narration."""
    T = TL("fall")
    tc, tclang, tff, timp_t = T["sword_thrust"], T["sword_clang"], T["freefall"], T["impact"]
    tm = TempoMap([(-1, T["collapse"]), (0, T["grab_ledge"]), (8, T["let_go"]), (12, tc), (20, tclang),
                   (24, timp_t), (26, T["fall_end"])])
    B = tm.beat
    S = Score(tm)
    bars = [-1, 0, 2, 4, 6, 8, 12, 16, 20, 24, 26]
    bff = B(tff)
    chords_ = [(-1, 0, "Eb/D"), (0, 2, "Dm"), (2, 4, "Bbmaj7#11/D"), (4, 6, "Abdim/D"), (6, 8, "D7sus4"),
               (8, 12, "Bbadd9"), (12, 16, "Dm"), (16, 18, "Gm7"), (18, 20, "Am"), (20, bff, "Eb/D"),
               (bff, 24, "A7b9"), (24, 26, "Dm")]

    # ---------------------------------------------------------------- strings
    v1 = S("violins_strain", "vln_slow", pan=-0.32, send=0.36, legato=0.1, lazy=-0.12,
           opts={"level": -19.5, "vo_duck": 3.0})
    v1.add([Note(0, 2, P("A5"), 96), Note(2, 2, P("Bb5"), 100), Note(4, 2, P("B5"), 106), Note(6, 2, P("C6"), 112)])
    v1.dyn = [(-0.2, 0), (0.05, 60), (1.2, 80), (2, 70), (3.2, 92), (4, 80), (5.2, 104), (6, 92), (7.5, 124),
              (7.98, 127), (8.02, 0)]
    v2 = S("violins2_pedal", "vln2", pan=-0.18, send=0.36, lazy=-0.12, opts={"level": -22.0, "vo_duck": 3.0})
    v2.add([Note(0, 8, P("D5"), 96)])
    v2.dyn = [(-0.2, 0), (0.1, 56), (4, 76), (7.5, 110), (7.98, 116), (8.02, 0)]
    vlt = S("violas_trem", "vla_trem", pan=0.12, send=0.34, humanize=0.0, opts={"level": -21.5, "vo_duck": 2.0})
    vlt.add([Note(0, 2, P("F4"), 96), Note(2, 2, P("E4"), 98), Note(4, 2, P("Eb4"), 102), Note(6, 2, P("D4"), 108)])
    vlt.add([Note(12, 8, P(p_), 110) for p_ in ("D4", "F4")])
    vlt.add([Note(bff, 24 - bff, P(p_), 110) for p_ in ("E4", "G4")])                   # freefall
    vlt.dyn = [(-0.2, 0), (0.1, 54), (2, 66), (4, 80), (6, 96), (7.98, 118), (8.02, 0), (11.98, 0), (12, 110),
               (19.9, 120), (19.98, 0), (bff, 20), (23.7, 124), (23.9, 0)]
    vcp = S("celli_pulse", "vc", pan=0.2, send=0.25, humanize=0.006, lazy=-0.03, opts={"level": -20.5})
    for k in range(16):
        vcp.add([Note(k * 0.5, 0.35, P("D3"), 100 if k % 2 == 0 else 70)])
    vcp.add(gallop(12, 16, P("D2")) + gallop(16, 18, P("G2")) + gallop(18, 20, P("A2")))
    vcp.dyn = [(-0.2, 0), (0.1, 60), (4, 76), (7.9, 112), (8.0, 0), (11.98, 0), (12, 110), (19.9, 124), (19.98, 0)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.22, humanize=0.006, lazy=-0.04, opts={"level": -21.5})
    cbf.add([Note(n.beat, n.dur, n.pitch, n.vel)
             for n in vcp.notes if n.beat >= 12 and n.pitch in (P("D2"), P("G2"), P("A2"))])
    cbf.dyn = [(11.98, 0), (12, 112), (19.9, 124), (19.98, 0)]
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.3, humanize=0.0, opts={"level": -22.5})
    cbt.add([Note(0, 8, P("D2"), 100), Note(bff, 24 - bff, P("A1"), 100)])
    cbt.dyn = [(-0.2, 0), (0.1, 60), (7.9, 110), (8.0, 0), (bff, 20), (23.7, 124), (23.9, 0)]
    vct = S("celli_trem", "vc_trem", pan=0.18, send=0.3, humanize=0.0, opts={"level": -23.0})
    vct.add([Note(bff, 24 - bff, P("A2"), 100)])
    vct.dyn = [(bff, 20), (23.7, 124), (23.9, 0)]
    # screeching strings on the sword: a sul-ponticello tremolo cluster gliding up a fourth, CUT at the clang
    scr = S("violins_screech", "vln_trem", pan=-0.25, send=0.4, humanize=0.0, eq=sul_pont,
            opts={"level": -21.0, "vo_duck": 4.0})
    scr.add([Note(12, 8, P(p_), 110) for p_ in ("A5", "Bb5", "E6")])
    scr.bend = [(12, 0), (12.3, 0), (20, 500)]
    scr.bend_range = 7
    scr.dyn = [(11.98, 0), (12, 124), (12.6, 96), (16, 104), (19.9, 127), (19.97, 0)]
    # the collapse / clang / impact string stabs
    sst = S("strings_hits", "vln1", pan=-0.1, send=0.32, humanize=0.0, lazy=-0.03, opts={"level": -21.0})
    sst.add([Note(-1, 0.8, P(p_), 124) for p_ in ("Eb5", "G5", "Bb5")])
    sst.add([Note(20, 0.35, P(p_), 124) for p_ in ("Eb5", "G5", "Bb5")])
    sst.add([Note(24, 0.45, P(p_), 127) for p_ in ("D5", "A5", "D6")])
    vcs = S("low_strings_hits", "vc", pan=0.22, send=0.28, humanize=0.0, lazy=-0.03, opts={"level": -20.0})
    vcs.add([Note(b, 0.8 if b < 0 else 0.4, P(p_), 124) for b in (-1, 20, 24) for p_ in ("D2", "D3")])
    # time stops: a high halo + low strings under the choir (seconds)
    halo = S("violins_halo", "vln_slow", pan=-0.3, send=0.6, lazy=-0.2, opts={"level": -27.0, "vo_duck": 2.0})
    halo.add([S.N(7.2, 4.7, "D6", 70), S.N(7.2, 4.7, "F6", 64)])
    halo.dyn = [(B(7.2), 0), (B(8.6), 50), (B(10.8), 44), (B(11.9), 0)]
    lowp = S("low_strings_pad", "vc_slow", pan=0.2, send=0.5, lazy=-0.25, opts={"level": -24.0})
    lowp.add([S.N(7.1, 4.95, "Bb2", 90), S.N(7.1, 4.95, "F3", 84)])
    lowp.dyn = [(B(7.1), 0), (B(8.3), 54), (B(11.0), 48), (B(12.0), 0)]

    # ---------------------------------------------------------------- brass
    hn = S("horns", "horns", pan=-0.2, send=0.34, legato=0.05, lazy=-0.04, opts={"level": -17.0, "vo_duck": 2.0})
    hn.add([Note(-1, 0.9, P(p_), 124) for p_ in ("Eb4", "G4", "Bb4")])
    hn.add([Note(0, 0.7, P(p_), 116) for p_ in ("D4", "F4", "A4")])        # grab_ledge
    th = seq(THEME, 12, 112, "mel", bar=4)[:-1]                           # D A F E D C ... (arrival = the clang)
    shape_vels(th, [116, 124, 110, 104, 108, 112])
    th[-1].dur = 0.96                                                     # the last C runs right into the clang
    hn.add(transpose(th, 12))
    hn.add([Note(20, 0.35, P(p_), 127) for p_ in ("Eb4", "G4", "Bb4")])   # CLANG: stop dead
    hn.add([Note(bff, 24 - bff, P(p_), 104) for p_ in ("C#4", "G4", "Bb4")])   # freefall
    hn.add([Note(24, 0.45, P(p_), 127, "mel" if p_ == "D4" else "") for p_ in ("D4", "F4", "A4")])
    hn.dyn = [(-1.2, 124), (-0.4, 70), (-0.05, 40), (0, 116), (0.6, 50), (1, 0), (11.95, 0), (12, 120),
              (16, 116), (19.95, 127), (20.3, 110), (20.4, 0), (bff, 16), (23.7, 124), (23.95, 127)]
    tpt = S("trumpets", "trumpet", pan=0.08, send=0.38, legato=0.04, lazy=-0.03, opts={"level": -19.5, "vo_duck": 5.0})
    tpt.add(transpose(th, 24))
    tpt.add([Note(20, 0.3, P(p_), 127) for p_ in ("Eb5", "Bb5")])
    tpt.add([Note(24, 0.45, P(p_), 127) for p_ in ("D5", "F5", "A5")])
    tpt.dyn = [(11.95, 0), (12, 118), (16, 112), (19.95, 127), (20.3, 110), (20.4, 0), (23.5, 0), (23.95, 127)]
    trb = S("trombones", "trombone", pan=0.18, send=0.3, legato=0.05, lazy=-0.05, opts={"level": -18.5})
    trb.add([Note(-1, 0.9, P(p_), 124) for p_ in ("Eb3", "G3", "Bb3")])
    trb.add([Note(2, 2, P("A2"), 90), Note(4, 2, P("G#2"), 96), Note(6, 2, P("G2"), 104)])   # dragged down
    trb.add(th)
    trb.add([Note(20, 0.35, P(p_), 127) for p_ in ("Eb3", "G3", "Bb3")])
    trb.add([Note(bff, 24 - bff, P(p_), 104) for p_ in ("A2", "E3", "G3")])
    trb.add([Note(24, 0.45, P(p_), 127) for p_ in ("A2", "D3", "F3", "A3")])
    trb.dyn = [(-1.2, 124), (-0.4, 70), (0, 0), (1.9, 0), (2.4, 50), (3.6, 72), (4, 60), (5.4, 88), (6, 76),
               (7.6, 118), (7.98, 124), (8.02, 0), (11.95, 0), (12, 120), (19.95, 127), (20.3, 110), (20.4, 0),
               (bff, 18), (23.7, 124), (23.95, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.22, lazy=-0.05, humanize=0.0, opts={"level": -20.0})
    tuba.add([Note(-1, 1, P("D2"), 124), Note(-1, 1, P("D1"), 110), Note(12, 4, P("D2"), 110), Note(16, 2, P("G1"), 112),
              Note(18, 1.96, P("A1"), 116), Note(20, 0.35, P("D1"), 127), Note(20, 0.35, P("D2"), 127),
              Note(bff, 24 - bff, P("A1"), 104), Note(24, 0.45, P("D1"), 127), Note(24, 0.45, P("D2"), 127)])
    tuba.dyn = [(-1.2, 124), (-0.3, 60), (0, 0), (11.95, 0), (12, 116), (19.95, 127), (20.3, 110), (20.4, 0),
                (bff, 20), (23.7, 124), (23.95, 127)]

    # ---------------------------------------------------------------- choir
    ch = S("choir", "choir", pan=0.0, send=0.55, legato=0.15, lazy=-0.25, opts={"level": -19.5, "vo_duck": 3.0})
    ch.add([S.N(T["falling"], tc - 0.2 - T["falling"], p_, 96) for p_ in ("Bb2", "F3", "D4", "F4", "C5")])
    cc = [(12, 16, "Dm"), (16, 18, "Gm7"), (18, 20, "Am")]
    cv = voice_chords(cc, 4, 50, 67, top_max=65)
    ch.add(pad_notes(cc, cv, {"c": [0, 1, 2, 3]}, 110)["c"])
    ch.add([Note(bff - 0.3, 24.3 - bff, P(p_), 100) for p_ in ("A3", "C#4", "G4", "Bb4")])
    ch.add([Note(24, 0.5, P(p_), 127) for p_ in ("D3", "A3", "D4", "F4")])
    ch.dyn = [(B(6.95), 0), (B(7.3), 40), (B(8.4), 80), (B(9.4), 88), (B(10.6), 80), (B(11.5), 60), (B(11.9), 56),
              (B(12.0), 0), (11.95, 0), (12, 104), (19.9, 124), (19.98, 0), (bff, 10), (23.7, 120), (24, 124),
              (24.3, 110), (24.5, 0)]

    # ---------------------------------------------------------------- percussion (sync-locked)
    tk = S("taiko", "taiko", pan=0.0, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -16.5})
    tkh = S("taiko_hi", "taiko", pan=-0.18, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    tk.add([Note(-1, 1, P("C2"), 127), Note(0, 1, P("C2"), 116)])
    tkh.add([Note(-1, 1, P("F2"), 120)])
    for k in range(1, 8):                                    # the strain: one slow pulse per beat
        tk.add([Note(k, 1, P("C2"), 80 + 4 * k)])
    tkh.add([Note(6.5, 0.5, P("A2"), 70), Note(7.5, 0.5, P("A2"), 84), Note(7.75, 0.25, P("A2"), 92)])
    for k in range(16):                                      # the surge: 8ths
        b = 12 + 0.5 * k
        if k % 2 == 0:
            tk.add([Note(b, 0.5, P("C2"), 124 if k % 4 == 0 else 110)])
        else:
            tkh.add([Note(b, 0.5, P("A2"), 96 + (k % 4) * 4)])
    tk.add([Note(20, 1, P("C2"), 127), Note(24, 2, P("C2"), 127)])      # clang, impact
    tkh.add([S.N(tclang + 0.004, 0.5, "F2", 124), S.N(timp_t + 0.004, 1.5, "F2", 127)])
    for k in range(5):                                       # the last fall: taiko 16ths swelling into the impact
        tkh.add([S.N(timp_t - 0.5 + 0.09 * k, 0.09, "C3", 70 + 11 * k)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.55, "slap": 0.1, "level": -18.0})
    boom.add([Note(-1, 1, P("D1"), 124), Note(0, 1, P("D1"), 100), Note(12, 1, P("D1"), 124), Note(14, 1, P("D1"), 104),
              Note(16, 1, P("G1"), 116), Note(18, 1, P("A1"), 116), Note(20, 1, P("D1"), 124)])
    bigb = S("boom_big", "boom", synth=synth_boom, opts={"decay": 0.95, "slap": 0.3, "drop": 1.8, "sat": 1.4, "peak": -5.0})
    bigb.add([Note(24, 2, P("D1"), 127), Note(24, 2, P("A1"), 96)])
    timp = S("timpani", "timpani", pan=0.14, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -19.5})
    timp.add([Note(-1, 1, P("D2"), 124), Note(0, 1, P("D2"), 110), Note(12, 2, P("D2"), 124), Note(16, 2, P("G2"), 116),
              Note(18, 1, P("A2"), 116), S.N(tclang + 0.007, 0.4, "D2", 124)])
    timp.add(roll(P("A2"), B(tff + 0.05), 23.9, tm, 14, 40, 124))
    timp.add([S.N(timp_t + 0.007, 1.2, "D2", 124)])
    bd = S("gran_cassa", "bass_drum", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -19.0})
    bd.add([Note(-1, 2, P("A1"), 124), Note(12, 2, P("A1"), 116), S.N(tclang + 0.003, 1.0, "A1", 120),
            S.N(timp_t + 0.003, 1.8, "A1", 127)])
    kit = S("snare_cym", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -22.5})
    kit.add([Note(-1, 2, 49, 118), Note(12, 2, 57, 120), S.N(tclang + 0.005, 0.25, 57, 124), S.N(tclang + 0.002, 0.2, 38, 124),
             S.N(timp_t + 0.009, 1.0, 49, 124), S.N(timp_t + 0.012, 1.0, 57, 116)])
    t_ = tc
    while t_ < tclang - 0.04:
        x = (t_ - tc) / (tclang - tc)
        kit.add([S.N(t_, 0.07, 38, int(60 + 40 * x))])
        t_ += 0.068
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -22.0})
    cym.opts["events"] = [(0.0, 0.0, 0.0, 1.0, 2.2), (tc - 0.5, tc, 0.6, 0.9, 2.0, 3.6),
                          (tclang, tclang, 0.0, 0.6, 0.35), (tff, timp_t, 0.7, 1.0, 1.1, 3.0)]
    cym.notes = [cym_note(tm, 0.0, 120), cym_note(tm, tc, 116), cym_note(tm, tclang, 110), cym_note(tm, timp_t, 127)]
    rc = S("rev_cymbal", "rev_cym", pan=0.0, send=0.3, humanize=0.0, opts={"level": -24.0})
    rc.add([S.N(timp_t - 1.37, 1.4, 60, 110)])                 # the sample peaks 1.37 s after note-on
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.05, "release": 0.1, "release_end": 0.6,
                                                             "h2": 0.22, "h3": 0.06, "level": -21.0})
    sub.add([Note(-1, 9, P("D1"), 100), S.N(T["falling"], tc - T["falling"], "Bb1", 70), Note(12, 4, P("D1"), 110),
             Note(16, 2, P("G1"), 104), Note(18, 2, P("A1"), 108), Note(20, 0.4, P("D1"), 124),
             Note(bff, 24 - bff, P("A1"), 100), Note(24, 1.6, P("D1"), 127)])
    sub.dyn = [(-1, 127), (-0.3, 70), (0, 80), (7.9, 110), (8.0, 0), (B(7.0), 0), (B(9.0), 50), (B(11.8), 30),
               (12, 120), (19.9, 120), (20, 124), (20.4, 0), (bff, 20), (23.9, 120), (24, 127), (25.6, 0)]

    for nm, f in (("violins_strain", 180), ("violins2_pedal", 160), ("violas_trem", 120), ("celli_pulse", 50),
                  ("basses_ost", 30), ("basses_trem", 30), ("celli_trem", 50), ("strings_hits", 160),
                  ("low_strings_hits", 40), ("violins_halo", 300), ("low_strings_pad", 45), ("horns", 80),
                  ("trumpets", 180), ("trombones", 55), ("tuba", 25), ("choir", 80), ("taiko", 30), ("taiko_hi", 40),
                  ("timpani", 32), ("gran_cassa", 25), ("snare_cym", 120), ("rev_cymbal", 300)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    arc = [(0.0, 2.0), (0.6, -2.0), (1.0, -1.0), (1.6, -4.5), (4.0, -3.0), (6.75, 1.0), (6.8, -1.0), (7.0, 0.0),
           (tc - 0.5, 0.0), (tc - 0.01, -2.0), (tc, -2.5), (tclang - 0.3, -2.5), (tclang - 0.045, -2.5),
           (tclang - 0.008, -10.0), (tclang, 2.0), (tclang + 0.1, 0.5), (tclang + 0.2, -9.0), (tff, -13.0),
           (tff + 0.5, -9.0), (timp_t - 0.15, -5.5),
           (timp_t - 0.105, -6.0), (timp_t - 0.01, -14.0), (timp_t, 1.5), (timp_t + 1.0, 1.5)]
    hits = [(T[k], k) for k in ("collapse", "grab_ledge", "slipping", "let_go", "falling", "sword_thrust",
                                "sword_clang", "freefall", "impact")]
    cue = Cue("fall", tm, bars, chords_, S.list(), rt60=3.0, wet=0.34, predelay=0.03, target_lufs=-16.5,
              fade_in=0.0015, fade_out=0.5, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0), carve_db=4.0,
              master_vol=[(B(t_), v_) for t_, v_ in arc], hits=hits,
              wet_duck=[(T["let_go"] + 0.05, T["let_go"] + 0.6, 0.5, 0.4), (tclang + 0.08, tff + 0.1, 0.25, 0.06),
                        (tclang - 0.05, tclang, 0.4, 0.03), (timp_t - 0.13, timp_t, 0.4, 0.08),
                        (timp_t + 0.5, T["fall_end"], 0.3, 0.6)],
              top_parts=("horns",), bass_parts=("tuba", "basses_ost", "basses_trem"))
    cue.notes_txt = compose_fall.__doc__
    return cue


# =========================================================================== cue: depths


def compose_depths() -> Cue:
    """S4 start -> monster_approach (22.184 s; the timeline fades it in over 2 s), under n21-n24.
    Low aching drones: a breathing additive drone on D1+A1 (independently drifting partials), the
    contrabasses on D2, a slow celli line of minor-second sighs (F3-E3, G3-F3-E3) under a viola
    A3-Bb3-A3, a faint blurred glass halo after dazed, and a faint, slightly irregular heartbeat.
    eyes_again brings back the cavern sting's colours very softly (sul-ponticello Eb6, celesta
    G#5/D6); pass_out dims everything to the drone and a fainter, slower heart; wake_noise restarts
    the pulse (a low pizz, the heart quickens) and a celli tremolo creeps up; one_arm: the celli sink
    to C#3 over the D pedal (A/D) with a pp horn A3, handing over to the menace cue at level."""
    T = TL("depths")
    dz, asv, eg, po, wk, oa, end = (T[k] for k in ("dazed", "assess", "eyes_again", "pass_out", "wake_noise",
                                                   "one_arm", "monster_approach"))
    tm = TempoMap.const(60)
    S = Score(tm)
    bars = [0, asv, eg, po, wk, oa, end]
    chords_ = [(0, asv, "Dm"), (asv, 7.0, "Dm(add9)"), (7.0, eg, "Gm/D"), (eg, eg + 2.6, "Dm"),
               (eg + 2.6, wk, "Dm(add9)"), (wk, oa, "Dm"), (oa, end, "A/D")]
    dr = S("drone", "drone", synth=synth_drone, pan=0.0, send=0.3,
           opts={"attack": 2.5, "release": 2.0, "tilt": 1.1, "kmax": 16, "move": 0.55, "lp": 1800, "level": -21.0})
    dr.add([Note(0, po + 0.9, P("D1"), 110), Note(0.5, po - 0.5, P("A1"), 80), Note(po - 0.4, end - po + 0.4, P("D1"), 100),
            Note(wk, end - wk, P("A1"), 76)])
    dr.dyn = [(0, 90), (po - 1.5, 100), (po - 0.5, 70), (wk - 2.0, 64), (wk, 76), (end, 100)]
    cb = S("basses", "cb", pan=0.28, send=0.4, legato=0.1, lazy=-0.15, opts={"level": -25.0})
    cb.add([Note(0.6, po - 0.6, P("D2"), 90), Note(wk, end - wk, P("D2"), 90)])
    cb.dyn = [(0.5, 0), (2.5, 50), (8, 60), (po - 0.7, 54), (po + 0.4, 0), (wk - 0.1, 0), (wk + 1.1, 46), (end, 60)]
    vc = S("celli_sighs", "vc_slow", pan=0.2, send=0.45, legato=0.15, lazy=-0.18, opts={"level": -22.0, "vo_duck": 2.0})
    sighs = [(1.0, asv - 1.0, "F3"), (asv, 2.8, "E3"), (7.0, eg - 7.0, "G3"), (eg, 2.6, "F3"), (eg + 2.6, po - eg - 2.4, "E3"),
             (wk + 0.2, oa - wk - 0.2, "D3"), (oa, end - oa, "C#3")]
    vc.add([Note(t_, d_, P(p_), 92, "mel") for t_, d_, p_ in sighs])
    vc.dyn = [(0.8, 0), (2.3, 70), (asv - 0.2, 62), (asv, 66), (asv + 1.0, 74), (6.6, 40), (7.0, 50), (eg - 0.5, 76),
              (eg, 70), (eg + 1.4, 74), (eg + 2.6, 56), (po + 0.2, 30), (po + 0.7, 0), (wk + 0.1, 0), (wk + 1.0, 52),
              (oa, 60), (oa + 1.6, 70), (end, 64)]
    vla = S("violas", "vla", pan=-0.1, send=0.45, legato=0.15, lazy=-0.18, opts={"level": -25.0, "vo_duck": 2.0})
    vla.add([Note(1.5, 5.5, P("A3"), 86), Note(7.0, eg - 7.0, P("Bb3"), 90), Note(eg, po - eg, P("A3"), 84)])
    vla.dyn = [(1.4, 0), (3.5, 54), (6.6, 50), (7.0, 56), (eg - 0.6, 70), (eg, 60), (po - 0.7, 44), (po + 0.3, 0)]
    gl = S("glass", "glass_pad", pan=0.0, send=0.7, lazy=-0.3, opts={"level": -30.0})
    gl.add([Note(dz, 6.0, P(p_), 60) for p_ in ("D5", "E5", "A5")])
    gl.dyn = [(dz - 0.1, 0), (2.2, 50), (4.5, 40), (dz + 6.0, 0)]
    hb = S("heartbeat", "heartbeat", synth=synth_heartbeat, opts={"gap": 0.24, "dub": 0.5, "decay": 0.12, "seed": 3,
                                                                  "level": -22.0})
    beats_, t_ = [], 0.8
    while t_ < end - 0.4:
        beats_.append(round(t_, 3))
        if t_ < po:
            t_ += 1.18 + 0.06 * math.sin(t_ * 1.7)
        elif t_ < wk:
            t_ += 1.55
        else:
            t_ += 0.92
    hb.add([S.N(x, 0.3, "G1", (54 if po < x < wk - 0.1 else 80) + (8 if x > wk - 0.1 else 0), "mel") for x in beats_])
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.6, humanize=0.0, eq=sul_pont, opts={"level": -30.0})
    vt.add([Note(eg, 2.6, P("Eb6"), 70)])
    vt.dyn = [(eg - 0.05, 0), (eg + 0.4, 40), (eg + 1.8, 30), (eg + 2.6, 0)]
    cel = S("celesta", "celesta", pan=0.3, send=0.7, humanize=0.0, opts={"level": -30.0})
    cel.add([Note(eg, 2.0, P("G#5"), 52), Note(eg, 2.0, P("D6"), 48)])
    pz = S("pizz", "cb_pizz", pan=0.25, send=0.4, humanize=0.0, opts={"level": -26.0})
    pz.add([Note(wk, 1.5, P("D2"), 84), Note(oa, 1.5, P("D2"), 76)])
    vct = S("celli_trem", "vc_trem", pan=0.15, send=0.45, humanize=0.0, opts={"level": -27.0})
    vct.add([Note(wk + 0.6, end - wk - 0.6, P("D3"), 90)])
    vct.dyn = [(wk + 0.55, 0), (wk + 1.6, 24), (end, 60)]
    hn = S("horn", "horns", pan=-0.2, send=0.5, lazy=-0.1, opts={"level": -27.0})
    hn.add([Note(oa, end - oa, P("A3"), 80)])
    hn.dyn = [(oa - 0.1, 0), (oa + 1.4, 50), (end, 44)]
    for nm, f in (("basses", 30), ("celli_sighs", 55), ("violas", 110), ("glass", 300), ("celesta", 300),
                  ("pizz", 30), ("celli_trem", 60), ("horn", 90)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(T[k], k) for k in ("dazed", "assess", "eyes_again", "pass_out", "wake_noise", "one_arm")]
    cue = Cue("depths", tm, bars, chords_, S.list(), rt60=3.8, wet=0.4, predelay=0.04, target_lufs=-19.0,
              fade_in=0.5, end_cut=True, send_hp=70.0, comp=(-10.0, 1.3, 30.0, 400.0),
              master_vol=[(0, 0.0), (po - 0.4, 0.0), (po + 0.8, -4.0), (wk - 0.4, -4.0), (wk + 0.6, -1.0), (end, 0.0)],
              hits=hits, top_parts=("celli_sighs",), bass_parts=("basses",))
    cue.notes_txt = compose_depths.__doc__
    return cue


# =========================================================================== cue: menace


def compose_menace() -> Cue:
    """monster_approach -> rock_hit (10.458 s), n25 over the first half. A creeping crescendo that
    accelerates (0.76 -> 0.49 s per beat): a chromatic pizzicato crawl in celli + basses rising from
    D2, a tremolo semitone cluster creeping upward in violas/violins, the low brass (tuba +
    trombones, D/Eb) growling in from arm_up, a stopped-horn + boom sting on monster_reveal, taiko
    pulses closing in, a timpani roll and a cymbal swell, the violins shrieking upward on the lunge -
    and the whole orchestra CUT DEAD on rock_hit."""
    T = TL("menace")
    tm = TempoMap([(0, T["monster_approach"]), (6, T["arm_up"]), (9, T["monster_reveal"]), (16, T["monster_lunge"]),
                   (17, T["rock_hit"])])
    S = Score(tm)
    bars = [0, 3, 6, 9, 13, 16, 17]
    chords_ = [(0, 9, "Dm"), (9, 16, "Eb/D"), (16, 17, "Eb/D")]
    crawl = ["D2", "D2", "Eb2", "D2", "E2", "Eb2", "F2", "E2", "F#2", "F2", "G2", "F#2", "Ab2", "G2", "A2", "Ab2",
             "Bb2", "A2", "B2", "Bb2", "C3", "B2", "C#3", "C3", "D3", "C#3", "Eb3", "D3", "E3", "Eb3", "F3", "E3",
             "F#3", "F3"]
    vcp = S("celli_pizz", "vc_pizz", pan=0.2, send=0.35, humanize=0.0, opts={"level": -21.0})
    vcp.add([Note(0.5 * k, 0.4, P(p_), int(56 + 60 * k / 33), "mel") for k, p_ in enumerate(crawl)])
    cbp = S("basses_pizz", "cb_pizz", pan=0.3, send=0.3, humanize=0.0, opts={"level": -22.0})
    cbp.add([Note(0.5 * k, 0.4, P(p_) - 12 if P(p_) - 12 >= 28 else P(p_), int(60 + 56 * k / 33))
             for k, p_ in enumerate(crawl) if k % 2 == 0])
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.35, humanize=0.0, opts={"level": -23.0})
    cbt.add([Note(0, 17.2, P("D2"), 100)])
    cbt.dyn = [(0, 44), (6, 52), (9, 72), (16, 112), (17, 127)]
    vlt = S("violas_trem", "vla_trem", pan=0.1, send=0.4, humanize=0.0, opts={"level": -23.0})
    vlt.add([Note(0, 9, P("A3"), 90), Note(0, 9, P("Bb3"), 90), Note(9, 4, P("B3"), 96), Note(9, 4, P("C4"), 96),
             Note(13, 4.2, P("C#4"), 100), Note(13, 4.2, P("D4"), 100)])
    vlt.dyn = [(0, 20), (6, 40), (9, 72), (13, 90), (16, 116), (17, 127)]
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.4, humanize=0.0, eq=sul_pont, opts={"level": -22.0})
    vt.add([Note(6, 3, P("Eb5"), 80), Note(9, 4, P("E5"), 90), Note(13, 4.2, P("F5"), 100), Note(13, 4.2, P("Gb5"), 100)])
    vt.bend = [(15.9, 0), (17, 700)]
    vt.bend_range = 9
    vt.dyn = [(5.9, 0), (6.5, 30), (9, 64), (13, 84), (16, 110), (17, 127)]
    trb = S("trombones", "trombone", pan=0.18, send=0.35, humanize=0.0, lazy=-0.05, opts={"level": -20.0})
    trb.add([Note(6, 11.2, P("D3"), 100), Note(6, 11.2, P("Eb3"), 100), Note(9, 8.2, P("A3"), 100)])
    trb.dyn = [(6, 0), (6.6, 24), (9, 60), (9.4, 50), (13, 80), (16, 118), (17, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.25, humanize=0.0, lazy=-0.05, opts={"level": -21.0})
    tuba.add([Note(6, 11.2, P("D1"), 100), Note(6, 11.2, P("D2"), 100)])
    tuba.dyn = [(6, 0), (7, 30), (9, 64), (13, 84), (16, 120), (17, 127)]
    hs = S("horns_stopped", "horns", pan=-0.2, send=0.45, humanize=0.0, lazy=-0.04,
           eq=lambda x: filt(hp(x, 120), sos_shelf(2200, 5.0)), opts={"level": -21.0})
    hs.add([Note(9, 1.6, P(p_), 124) for p_ in ("A3", "Bb3", "Eb4")])
    hs.add([Note(13, 4.2, P(p_), 100) for p_ in ("Bb3", "Eb4")])
    hs.dyn = [(8.95, 124), (9.5, 64), (10.6, 30), (13, 40), (16, 110), (17, 127)]
    oo = S("choir", "oohs", pan=0.0, send=0.5, humanize=0.0, lazy=-0.2, opts={"level": -25.0})
    oo.add([Note(9, 8.2, P(p_), 90) for p_ in ("D3", "Eb3", "A3")])
    oo.dyn = [(8.9, 0), (10, 30), (13, 56), (16, 96), (17, 120)]
    tk = S("taiko", "taiko", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -18.5})
    for b, v in ((0, 70), (2, 72), (4, 74), (6, 90), (7.5, 76), (9, 124), (10, 84), (11, 88), (12, 92), (13, 100),
                 (14, 102), (14.5, 90), (15, 108), (15.5, 98), (16, 120), (16.25, 104), (16.5, 112), (16.75, 120)):
        tk.add([Note(b, 0.5, P("C2") if v >= 100 or b % 1 == 0 else P("A2"), v)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.5, "slap": 0.0, "level": -20.0})
    boom.add([Note(9, 1, P("D1"), 124), Note(13, 1, P("D1"), 96), Note(16, 1, P("D1"), 120)])
    timp = S("timpani", "timpani", pan=0.14, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    timp.add([Note(9, 1, P("D2"), 116)])
    timp.add(roll(P("D2"), 14, 17.05, tm, 14, 44, 124))
    pno = S("piano_low", "piano", pan=0.0, send=0.45, humanize=0.0, opts={"level": -25.0})
    pno.add([Note(9, 3, P(p_), 104) for p_ in ("D1", "Eb1", "A1")])
    pno.pedal = [(8.9, 12.5)]
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -24.0})
    t_cut = T["rock_hit"]
    cym.opts["events"] = [(t_cut - 1.7, t_cut + 0.05, 1.0, 0.0, 1.0, 2.8)]
    cym.notes = [cym_note(tm, t_cut - 1.7, 90)]
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.6, "h2": 0.25, "level": -24.0})
    sub.add([Note(0, 17.2, P("D1"), 100)])
    sub.dyn = [(0, 60), (9, 84), (17, 127)]
    for nm, f in (("celli_pizz", 50), ("basses_pizz", 30), ("basses_trem", 30), ("violas_trem", 120),
                  ("trombones", 60), ("tuba", 25), ("choir", 90), ("taiko", 35), ("timpani", 32), ("piano_low", 28)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(T[k], k) for k in ("monster_approach", "arm_up", "monster_reveal", "monster_lunge")] + \
        [(T["rock_hit"], "rock_hit (cut)")]
    cue = Cue("menace", tm, bars, chords_, S.list(), rt60=3.0, wet=0.34, predelay=0.03, target_lufs=-17.0,
              fade_in=0.01, end_cut=True, send_hp=80.0, comp=(-10.0, 1.3, 20.0, 250.0),
              master_vol=[(0, 0.0), (6, -2.0), (8.98, -3.0), (9, 0.0), (10, -2.5), (16, -0.5), (17, 0.0)], hits=hits,
              top_parts=("violins_trem",), bass_parts=("basses_trem",))
    cue.notes_txt = compose_menace.__doc__
    return cue


# =========================================================================== cue: hermit


def compose_hermit() -> Cue:
    """m02 -> crunch_end (8.34 s; the timeline fades its last 1.5 s). The comedy starts: under m02
    (0-2.24) only a tiptoeing low pizzicato (D2 / A1, nothing in the voice band); glove_grab (2.74) =
    a pizzicato chord + temple-block tick and the bassoon 'drags' the monster off down a chromatic
    scale (D4 -> G3); crunch (4.74) starts a quirky staccato bassoon march in D minor over an oom-pah
    of pizzicato basses / violas, stepping back under n27 ('Anger had no idea how to feel about
    this.'), ending on a half cadence."""
    T = TL("hermit")
    tm = TempoMap([(0, 0.0), (5, T["glove_grab"]), (9, T["crunch"]), (17, T["crunch"] + 4.0)])
    S = Score(tm)
    bars = [0, 1, 5, 9, 13, 17]
    chords_ = [(0, 5, "Dm"), (5, 9, "Dm"), (9, 11, "Dm"), (11, 13, "A"), (13, 14, "Dm"), (14, 15, "Gm"), (15, 17, "A")]
    cbp = S("basses_pizz", "cb_pizz", pan=0.25, send=0.22, humanize=0.006, opts={"level": -21.0})
    cbp.add(seq("D2:q A1:q D2:q A1:q D2:q", 0, 70, vels=[74, 64, 70, 62, 72]))
    cbp.add(seq("D2:q r:q A1:q r:q | D2:q G1:q A1:q r:q", 9, 84, bar=4))
    cbp.add([Note(5, 1, P("D2"), 110)])
    vcp = S("celli_pizz", "vc_pizz", pan=0.15, send=0.22, humanize=0.006, opts={"level": -23.0})
    vcp.add([Note(5, 1, P(p_), 112) for p_ in ("D3", "A3")])
    vlp = S("violas_pizz", "vla_pizz", pan=-0.15, send=0.24, humanize=0.006, opts={"level": -24.0, "vo_duck": 3.0})
    vlp.add([Note(5, 1, P("F4"), 108)])
    for b_, sym in ((9.5, "Dm"), (10.5, "Dm"), (11.5, "A"), (12.5, "A"), (13.5, "Dm"), (14.5, "Gm"), (15.5, "A"),
                    (16.5, "A")):
        ch_ = {"Dm": ("F3", "A3"), "A": ("E3", "C#4"), "Gm": ("G3", "Bb3")}[sym]
        vlp.add([Note(b_, 0.4, P(p_), 74) for p_ in ch_])
    bsn = S("bassoon", "bassoon", pan=0.05, send=0.24, legato=0.03, humanize=0.008, opts={"level": -17.5, "vo_duck": 4.0})
    drag = seq("D4:e C#4:e C4:e B3:e Bb3:e A3:e Ab3:e G3:e", 5, 92, "mel")
    shape_vels(drag, [104, 84, 90, 80, 86, 78, 84, 88])
    bsn.add(drag)
    march = seq("A2:e D3:e F3:e A3:e G#3:q A3:e r:e | F3:e D3:e Bb2:e G2:e C#3:q r:q | "
                "A2:e D3:e F3:e A3:e D4:q C#4:e r:e | Bb3:e G3:e E3:e C#3:e D3:q r:q", 9, 96, "mel", bar=4)
    for k, nt in enumerate(march):
        nt.dur = min(nt.dur, 0.32) if nt.dur <= 0.5 else 0.7          # staccato, the quarters a bit longer
        nt.vel = 100 if k % 4 == 0 else 86
    bsn.add(march)
    bsn.dyn = [(4.9, 96), (8.9, 84), (9, 100), (17, 100)]
    tb = S("temple_block", "tblocks", pan=0.3, send=0.25, humanize=0.0, opts={"level": -26.0})
    tb.add([Note(5, 0.5, 60, 100)])
    for nm, f in (("basses_pizz", 30), ("celli_pizz", 50), ("violas_pizz", 110), ("bassoon", 50),
                  ("temple_block", 200)):
        S.parts[nm].eq = hpf(f)
    hits = [(0.0, "cue_start (m02 in)"), (T["glove_grab"], "glove_grab"), (T["crunch"], "crunch")]
    cue = Cue("hermit", tm, bars, chords_, S.list(), rt60=1.6, wet=0.22, predelay=0.015, target_lufs=-18.0,
              fade_in=0.02, fade_out=0.3, comp=(-14.0, 1.5, 15.0, 200.0), hits=hits,
              top_parts=("bassoon",), bass_parts=("basses_pizz",))
    cue.notes_txt = compose_hermit.__doc__
    return cue


# =========================================================================== cue: lull


def compose_lull() -> Cue:
    """snore_start -> startled (32.866 s; timeline fades 2 s in / 2 s out), under n30-n34 and a02. A
    soft, slightly absurd lullaby in F major, 3/4 at 100 bpm, the grid placed so drip1/drip2 land on
    beats 38/40: a harp rocks gently, a tuba breathes the 'oom' of every bar. Phrase A (celesta +
    music box, a sleepy bassoon two octaves down that YAWNS - a slow downward bend - on the long
    note) under n31; under a02 only the harp's low strings and the tuba; phrase B (Bb | F | C7 | F)
    as he gives up and closes his eyes; phrase A again as he sleeps, with high celesta plinks on the
    two drips and a staccato bassoon 'bup' on hand_wave; on side_eye_open the tune stops and the
    harmony sours (Bbm/F), a low pizzicato + bassoon 'huh?' on sees_tongue. Melodic parts step
    back under the narration."""
    T = TL("lull")
    t0 = T["drip1"] - 0.6 * 38
    tm = TempoMap.const(100, start=t0)
    B = tm.beat
    S = Score(tm)
    b_end = B(T["startled"])
    b_side, b_tongue = B(T["side_eye_open"]), B(T["sees_tongue"])
    bars = [3 * k for k in range(19)]
    chords_ = [(0, 3, "F"), (3, 6, "C7"), (6, 9, "F"), (9, 12, "C7"), (12, 15, "F"), (15, 18, "F"), (18, 21, "F"),
               (21, 24, "C7"), (24, 27, "Bb"), (27, 30, "F"), (30, 33, "C7"), (33, 36, "F"), (36, 39, "F"),
               (39, 42, "C7"), (42, 45, "F"), (45, 48, "F"), (48, b_side, "F"), (b_side, b_end, "Bbm/F")]
    tuba = S("tuba", "tuba", pan=0.0, send=0.3, lazy=-0.04, opts={"level": -22.0})
    roots = {"F": "F1", "C7": "C2", "Bb": "Bb1"}
    for b0, b1, sym in chords_:
        if b0 >= 48 or b1 - b0 < 3:
            continue
        tuba.add([Note(b0, 1.6, P(roots[sym]), 84)])
    tuba.add([Note(48, b_end - 48, P("F1"), 70)])
    tuba.dyn = [(0, 70), (12, 80), (45, 76), (48, 60), (b_end, 50)]
    harp = S("harp", "harp", pan=-0.3, send=0.45, humanize=0.008, opts={"level": -23.0})
    rock = {"F": ("F2", "C3", "A3"), "C7": ("C2", "G2", "Bb3"), "Bb": ("Bb1", "F2", "D3")}
    a02 = (B(T.lines["a02"][0]) - 0.5, B(T.lines["a02"][1]) + 0.3)
    for b0, b1, sym in chords_:
        if b0 >= 48:
            continue
        lo_, mid, top = rock[sym]
        harp.add([Note(b0, 2.8, P(lo_), 62), Note(b0 + 1, 1.8, P(mid), 50)])
        if not (a02[0] <= b0 + 2 <= a02[1]):
            harp.add([Note(b0 + 2, 1.0, P(top), 46)])
    harp.add([Note(48, 2.5, P("F2"), 52), Note(49, 1.5, P("C3"), 44), Note(b_side, b_end - b_side, P("F2"), 50),
              Note(b_side + 0.5, b_end - b_side - 0.5, P("Db3"), 44)])
    A = "C5:h A4:q | Bb4:h G4:q | A4:q F4:q A4:q | C5:h."
    Bm = "D5:h Bb4:q | A4:h F4:q | G4:q E4:q G4:q | F4:h."
    mel = seq(A, 6, 60, "mel", bar=3) + seq(Bm, 24, 60, "mel", bar=3) + seq(A, 36, 60, "mel", bar=3)
    shape_vels(mel, [62, 54, 58, 50, 56, 52, 58, 66] + [64, 56, 60, 54, 56, 52, 56, 60] + [60, 52, 56, 48, 54, 50, 56, 62])
    cel = S("celesta", "celesta", pan=0.15, send=0.5, humanize=0.008, opts={"level": -20.0, "vo_duck": 5.0})
    cel.add(mel)
    cel.add([Note(38, 1.5, P("F6"), 64), Note(40, 1.5, P("C7"), 60)])          # the drips
    mb = S("music_box", "musicbox", pan=-0.1, send=0.5, humanize=0.006, opts={"level": -25.0, "vo_duck": 5.0})
    mb.add(transpose(mel, 12, tag=""))
    bsn = S("bassoon", "bassoon", pan=0.1, send=0.32, legato=0.05, humanize=0.01, opts={"level": -21.0, "vo_duck": 2.0})
    bsn.add(transpose(mel, -24, tag=""))
    bsn.dyn = [(5.9, 56), (6, 60), (15, 66), (16.6, 70), (17.9, 40), (18, 0), (23.9, 0), (24, 58), (35.9, 56),
               (36, 58), (45, 66), (46.6, 70), (47.9, 40), (48.2, 0)]
    bsn.bend = [(15.0, 0), (16.4, 0), (17.85, -300), (17.97, 0), (45.0, 0), (46.4, 0), (47.85, -300), (47.97, 0)]
    bsn.bend_range = 4                                     # the two yawns on the long C
    bfx = S("bassoon_fx", "bassoon", pan=0.12, send=0.32, humanize=0.0, opts={"level": -23.0})
    bfx.add([Note(41, 0.3, P("F2"), 96), Note(b_tongue, 1.6, P("Db2"), 80)])   # hand_wave 'bup', sees_tongue 'huh?'
    bfx.bend = [(b_tongue, 0), (b_tongue + 0.8, 0), (b_tongue + 1.5, 150)]
    bfx.bend_range = 2
    bfx.dyn = [(40.9, 90), (b_tongue - 0.1, 70), (b_tongue + 0.7, 90), (b_tongue + 1.6, 40)]
    pz = S("pizz", "vc_pizz", pan=0.15, send=0.35, humanize=0.0, opts={"level": -24.0})
    pz.add([Note(b_tongue, 1.0, P("Db2"), 96), Note(b_tongue, 1.0, P("Db3"), 80)])
    vct = S("celli_trem", "vc_trem", pan=0.2, send=0.5, humanize=0.0, opts={"level": -30.0})
    vct.add([Note(b_side + 0.2, b_end - b_side, P("Db3"), 80), Note(b_side + 0.2, b_end - b_side, P("F3"), 76)])
    vct.dyn = [(b_side + 0.1, 0), (b_side + 1.3, 30), (b_end, 46)]
    for nm, f in (("tuba", 25), ("harp", 40), ("celesta", 300), ("music_box", 500), ("bassoon", 40),
                  ("bassoon_fx", 40), ("celli_trem", 60), ("pizz", 40)):
        S.parts[nm].eq = hpf(f)
    hits = [(T[k], k) for k in ("snore_start", "contemplate", "close_eyes", "sleeping", "drip1", "drip2", "hand_wave",
                                "side_eye_open", "sees_tongue")]
    cue = Cue("lull", tm, bars, chords_, S.list(), rt60=1.8, wet=0.3, predelay=0.02, target_lufs=-19.0,
              fade_in=0.3, fade_out=0.3, comp=(-14.0, 1.4, 25.0, 300.0), hits=hits,
              top_parts=("celesta",), bass_parts=("tuba",))
    cue.notes_txt = compose_lull.__doc__
    return cue


# =========================================================================== cue: friend


def compose_friend() -> Cue:
    """startled -> end_card (77.383 s). Bb major, 1 beat = 0.7 s, the grid placed so the FOUR sass
    stomps fall on beats 30-33. startled: a big dumb major chord BWAAMP (tuba, trombones, horns,
    timpani, bass drum), gone before a03. A bassoon 'hi!' before m04; under m04 / n35 / a04 / m05 the
    friend's waddle theme stays in the tuba's low register (staccato, pizzicato basses on the strong
    beats), little bassoon licks answer in the gaps. n36 ('The creature did not like that.'): the
    waddle stops, a low bassoon grumble swells. sass: the bassoon huffs up (bend), a pizzicato
    pickup, then the four stomps: tuba + bass drum + timpani + a scooping trombone line D-Eb-E-F,
    and a Bb button. wipe_saliva: a bassoon 'bleh' sagging down under n37; awkward: the music stops -
    only the foot taps and n38. Under the tail of the laugh a deadpan pizzicato tick-tock; m07: a
    low sinking pedal (tuba D1, contrabass tremolo, a bassoon slipping A2-G#2-G2-F#2-F2) ending on a
    pizzicato 'question'; a06 in silence; the DEADPAN STING at a06's end: one low muted D-minor 'bwomp'
    that sags; snort: the bouncy giggle (staccato bassoon triplets D-Eb-F rising to a squeal over a
    Bb / F7 oom-pah, pizzicato, xylophone), a celesta 'ting' on anger_smirk, cut dead on
    notices_smirk; serious: a tiny heroic tag of Anger's theme (horns D-A, timpani) that sinks
    softly F-E-D under n39 and blooms into a warm D-major chord (low strings, horns pp, harp, a
    celesta glint) - the smile he almost had - fading just before the end card."""
    T = TL("friend")
    stomps = sorted(t for t in T.sfx["stomp"] if 0 < t < 77)
    tm = TempoMap.const(60 / 0.7, start=stomps[0] - 30 * 0.7)
    B = tm.beat
    S = Score(tm)
    end = T["end_card"]
    bars = [B(0.0)] + [4 * k for k in range(0, int(B(end) / 4) + 1)] + [B(end)]
    ln = T.lines
    sass, wipe, awk, laugh = T["sass"], T["wipe_saliva"], T["awkward"], T["laugh_start"]
    a06_end, snort, smirk, notices, serious = ln["a06"][1], T["snort"], T["anger_smirk"], T["notices_smirk"], T["serious"]
    m07_0, m07_1 = ln["m07"]
    chords_ = [(B(0.0), B(1.2), "Bb"), (B(ln["m04"][0]), B(ln["m05"][1]), "Bb"), (B(m07_0), B(m07_1 + 0.4), "Dm"),
               (B(a06_end), B(a06_end + 0.6), "Dm"), (B(snort), B(snort + 0.7), "Bb"), (B(snort + 0.7), B(snort + 1.4), "F7"),
               (B(snort + 1.4), B(snort + 2.1), "Bb"), (B(snort + 2.1), B(notices), "F7"), (B(serious), B(serious + 1.8), "Dm"),
               (B(serious + 1.8), B(end), "D")]

    # ---------------------------------------------------------------- startled: BWAAMP (before a03)
    t_a03 = ln["a03"][0]
    trb = S("trombones", "trombone", pan=0.15, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -18.0})
    trb.add([S.N(0.0, t_a03 - 0.1, p_, 124) for p_ in ("Bb2", "D3", "F3")])
    trb.dyn = [(B(0.0), 127), (B(0.45), 96), (B(t_a03 - 0.15), 30), (B(t_a03), 0)]
    hn = S("horns", "horns", pan=-0.2, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -21.0})
    hn.add([S.N(0.0, t_a03 - 0.1, p_, 120) for p_ in ("F3", "Bb3", "D4")])
    hn.dyn = list(trb.dyn)
    tuba = S("tuba", "tuba", pan=0.0, send=0.22, humanize=0.0, lazy=-0.05, opts={"level": -19.0})
    tuba.add([S.N(0.0, t_a03 - 0.05, "Bb1", 124)])
    tuba.add([S.N(m07_0 + 0.25, m07_1 - m07_0 - 0.1, "D1", 90)])          # m07: the sinking pedal
    tuba.dyn = [(B(0.0), 127), (B(0.5), 90), (B(t_a03 - 0.05), 0), (B(m07_0 + 0.15), 0), (B(m07_0 + 1.6), 46),
                (B(m07_1 - 0.5), 56), (B(m07_1 + 0.15), 0)]
    bdr = S("bass_drum", "bass_drum", pan=0.0, send=0.25, humanize=0.0, opts={"level": -21.0})
    bdr.add([S.N(0.0, 1.0, "A1", 116)])
    timp = S("timpani", "timpani", pan=0.12, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    timp.add([S.N(0.0, 1.0, "Bb2", 110)])

    # ---------------------------------------------------------------- the waddle (low only under the voices)
    tst = S("tuba_waddle", "tuba_st", pan=0.0, send=0.2, humanize=0.006, opts={"level": -20.0})
    cbp = S("basses_pizz", "cb_pizz", pan=0.25, send=0.2, humanize=0.006, opts={"level": -22.0})
    # the friend's waddle theme in the tuba's low register (fundamentals 44-87 Hz, staccato); phrases
    # rock left-right (Bb-F) and climb by step (Bb C D Eb) like a heavy body shifting its weight
    PH = [[("F1", 1)], [("Bb1", 1)], [("F1", 1)], [("Bb1", 0.5), ("C2", 0.5)], [("D2", 1)], [("Eb2", 1)], [("C2", 1)],
          [("F1", 1)], [("A1", 0.5), ("C2", 0.5)], [("Bb1", 1)]]

    def waddle(t0, t1, v=68):
        b = math.ceil(B(t0 + 0.05))
        k = 0
        while tm.sec(b + 1) <= t1 + 0.35:
            cell = PH[k % len(PH)]
            bb = b
            for j, (p_, d_) in enumerate(cell):
                strong = (b % 2 == 0) and j == 0
                tst.add([Note(bb, 0.42 if d_ >= 1 else 0.3, P(p_), v + (6 if strong else 0), "mel")])
                if j == 0:
                    cbp.add([Note(bb, 0.7, P(p_) + 12, v - (4 if strong else 14))])
                bb += d_
            b += 1
            k += 1
    for lid in ("m04", "n35", "a04", "m05"):
        waddle(*ln[lid])
    bsn = S("bassoon", "bassoon_st", pan=0.08, send=0.24, humanize=0.006, opts={"level": -18.0})
    g0 = ln["a03"][1] + 0.08                                               # "hi!" before m04
    bsn.add([S.N(g0, 0.14, "Bb2", 92, "mel"), S.N(g0 + 0.18, 0.14, "D3", 96, "mel"), S.N(g0 + 0.36, 0.2, "F3", 104, "mel")])
    for t_a, t_b in ((ln["m04"][1], ln["n35"][0]), (ln["n35"][1], ln["a04"][0])):   # the waddle lick in the gaps
        if t_b - t_a > 0.45:
            st = t_a + 0.06
            bsn.add([S.N(st, 0.12, "F3", 96, "mel"), S.N(st + 0.17, 0.12, "D3", 90, "mel"),
                     S.N(st + 0.34, 0.16, "Bb2", 100, "mel")])
    # the giggle (snort -> notices_smirk): staccato 8th-note triplets, one group per 0.7 s beat
    gig = ["D3", "D3", "D3", "Eb3", "Eb3", "Eb3", "F3", "F3", "F3", "A3", "C4", "F3"]
    for k, p_ in enumerate(gig):
        t_ = snort + k * 0.7 / 3
        if t_ > notices - 0.12:
            break
        bsn.add([S.N(t_, 0.12, p_, (104 if k % 3 == 0 else 88) + (10 if k >= 9 else 0), "mel")])
    bfx = S("bassoon_fx", "bassoon", pan=0.1, send=0.26, humanize=0.0, opts={"level": -19.0, "vo_duck": 3.0})
    n36_0, n36_1 = ln["n36"]
    bfx.add([S.N(n36_0 + 0.1, sass - n36_0 - 0.25, "G2", 70)])            # 'did not like that': a grumble
    bfx.add([S.N(sass, 0.5, "F2", 104)])                                   # sass: the huff, scooping up
    bfx.add([S.N(wipe, 0.55, "Ab2", 96)])                                  # wipe_saliva: 'bleh'
    step = (m07_1 - m07_0 - 0.4) / 5
    bfx.add([S.N(m07_0 + 0.25 + k * step, step - 0.05, p_, 78)
             for k, p_ in enumerate(("A2", "G#2", "G2", "F#2", "F2"))])    # m07: slipping down
    bfx.bend = [(B(n36_0), 0), (B(sass - 0.4), 0), (B(sass - 0.16), 60), (B(sass - 0.15), -300), (B(sass + 0.36), 500),
                (B(sass + 0.56), 500), (B(sass + 0.66), 0), (B(wipe), 0), (B(wipe + 0.55), -400), (B(wipe + 0.63), 0)]
    bfx.bend_range = 6
    bfx.dyn = [(B(n36_0), 0), (B(n36_0 + 0.6), 40), (B(sass - 0.2), 70), (B(sass - 0.16), 100), (B(sass + 0.46), 110),
               (B(sass + 0.51), 0), (B(wipe - 0.07), 96), (B(wipe + 0.55), 40), (B(wipe + 0.63), 0), (B(m07_0 + 0.15), 0),
               (B(m07_0 + 0.8), 32), (B(m07_1 - 0.5), 38), (B(m07_1 - 0.4), 0)]

    # ---------------------------------------------------------------- sass and the four stomps
    cbp.add([S.N(stomps[0] - 0.35, 0.3, "F2", 92), S.N(stomps[0] - 0.175, 0.3, "A2", 96)])   # pickup "ba-dum"
    tst.add([S.N(t_, 0.45, "Bb1", 124, "mel") for t_ in stomps])
    bdr.add([S.N(t_, 1.0, "A1", 108 + 6 * k) for k, t_ in enumerate(stomps)])
    timp.add([S.N(t_, 0.6, "F2" if k < 3 else "Bb2", 100 + 8 * k) for k, t_ in enumerate(stomps)])
    ts = S("trombone_sass", "trombone", pan=-0.1, send=0.28, humanize=0.0, lazy=-0.02, opts={"level": -18.5})
    ts.add([S.N(t_, 0.55 if k < 3 else 0.32, p_, 110 + 4 * k) for k, (t_, p_) in enumerate(zip(stomps, ("D3", "Eb3", "E3", "F3")))])
    t_btn = stomps[-1] + 0.35
    ts.add([S.N(t_btn, 0.3, "D3", 120)])
    bend = []
    for t_ in stomps:
        bend += [(B(t_ - 0.04), 0), (B(t_ - 0.03), -250), (B(t_ + 0.12), 0)]
    ts.bend = bend
    ts.bend_range = 3
    ts.dyn = [(B(stomps[0] - 0.2), 110), (B(t_btn + 0.4), 120)]
    xy = S("xylophone", "xylo", pan=0.3, send=0.3, humanize=0.0, opts={"level": -24.0})
    xy.add([S.N(t_btn, 0.3, "F5", 100), S.N(t_btn, 0.3, "Bb5", 96)])
    cbp.add([S.N(t_btn, 0.4, "Bb1", 112)])
    # the giggle accompaniment: oom-pah, pizzicato chords, xylophone sparkles
    for k in range(4):
        t_ = snort + 0.7 * k
        if t_ > notices - 0.12:
            break
        tst.add([S.N(t_, 0.3, "Bb1" if k % 2 == 0 else "F1", 100)])
        cbp.add([S.N(t_, 0.4, "Bb2" if k % 2 == 0 else "F2", 96)])
    vlp = S("violas_pizz", "vla_pizz", pan=-0.2, send=0.26, humanize=0.006, opts={"level": -23.0})
    vlp.add([S.N(m07_1 + 0.15, 0.4, "Eb4", 70)])                          # the m07 'question'
    for k in range(4):
        t_ = snort + 0.7 * k + 0.35
        if t_ > notices - 0.12:
            break
        vlp.add([S.N(t_, 0.3, p_, 90) for p_ in (("D4", "F4") if k % 2 == 0 else ("C4", "Eb4"))])
    xy.add([S.N(snort + k * 0.7, 0.2, p_, 90) for k, p_ in enumerate(("F6", "Eb6", "F6")) if snort + k * 0.7 < notices - 0.12])
    cel = S("celesta", "celesta", pan=0.25, send=0.45, humanize=0.0, opts={"level": -24.0})
    cel.add([S.N(smirk, 1.0, "D6", 80), S.N(smirk, 1.0, "F6", 70)])       # anger_smirk: 'ting'

    # ---------------------------------------------------------------- the laugh: tick-tock; m07: sinking
    lt0 = max(laugh + 3.5, ln["m06"][1] - 4.4)
    cbp.add([S.N(lt0 + 1.4 * k, 0.6, "D2", 64) for k in range(4) if lt0 + 1.4 * k < m07_0 - 0.3])
    cbt = S("basses_trem", "cb_trem", pan=0.28, send=0.3, humanize=0.0, opts={"level": -25.0})
    cbt.add([S.N(m07_0 + 0.25, m07_1 - m07_0 - 0.1, "D2", 90)])
    cbt.dyn = [(B(m07_0 + 0.15), 0), (B(m07_0 + 1.6), 34), (B(m07_1 - 0.4), 46), (B(m07_1 + 0.15), 0)]

    # ---------------------------------------------------------------- the deadpan sting (a06's end)
    sting = S("sting_brass", "trombone", pan=0.1, send=0.2, humanize=0.0, lazy=0.0,
              eq=lambda x: lp(hp(x, 60), 2200), opts={"level": -19.0})
    sting.add([S.N(a06_end, 0.55, p_, 112) for p_ in ("D3", "F3", "A3")])
    sting.bend = [(B(a06_end), 0), (B(a06_end + 0.25), 0), (B(a06_end + 0.55), -180)]
    sting.bend_range = 2
    sting.dyn = [(B(a06_end - 0.07), 112), (B(a06_end + 0.33), 80), (B(a06_end + 0.55), 0)]
    stu = S("sting_tuba", "tuba", pan=0.0, send=0.2, humanize=0.0, lazy=0.0, opts={"level": -21.0})
    stu.add([S.N(a06_end, 0.55, "D2", 110)])
    stu.dyn = [(B(a06_end - 0.07), 110), (B(a06_end + 0.33), 80), (B(a06_end + 0.55), 0)]
    stu.bend = [(B(a06_end), 0), (B(a06_end + 0.25), 0), (B(a06_end + 0.55), -180)]
    bdr.add([S.N(a06_end, 1.0, "A1", 84)])

    # ---------------------------------------------------------------- serious: the tiny heroic tag -> the smile
    tag = S("horns_tag", "horns", pan=-0.15, send=0.4, legato=0.06, lazy=0.0, opts={"level": -18.5, "vo_duck": 3.0})
    q = 0.3
    d_end = end - 0.5
    tag.add([S.N(serious, 1.5 * q, "D3", 100, "mel"), S.N(serious + 1.5 * q, 2.5 * q, "A3", 108, "mel"),
             S.N(serious + 4 * q, 2.0 * q, "F3", 84, "mel"), S.N(serious + 6 * q, 1.6 * q, "E3", 78, "mel"),
             S.N(serious + 7.6 * q, d_end - serious - 7.6 * q, "D3", 70, "mel"),
             S.N(serious + 7.8 * q, d_end - serious - 7.8 * q, "F#3", 60), S.N(serious + 7.8 * q, d_end - serious - 7.8 * q, "A3", 56)])
    tag.dyn = [(B(serious - 0.05), 104), (B(serious + 1.2), 100), (B(serious + 1.9), 70), (B(serious + 3.0), 52),
               (B(d_end - 1.0), 40), (B(d_end), 0)]
    lowtag = S("low_strings_tag", "vc_slow", pan=0.2, send=0.45, lazy=0.0, opts={"level": -21.0, "vo_duck": 2.0})
    lowtag.add([S.N(serious, 2.3, "D2", 96), S.N(serious, 2.3, "A2", 90)])
    lowtag.add([S.N(serious + 2.3, d_end - serious - 2.3, p_, 80) for p_ in ("D2", "A2", "F#3")])
    lowtag.dyn = [(B(serious - 0.05), 86), (B(serious + 1.5), 76), (B(serious + 2.3), 52), (B(serious + 3.3), 56),
                  (B(d_end - 1.0), 46), (B(d_end), 0)]
    timp.add([S.N(serious, 0.4, "D2", 96), S.N(serious + 1.5 * q, 0.4, "A2", 90)])
    harp = S("harp", "harp", pan=-0.35, send=0.5, humanize=0.006, opts={"level": -25.0})
    t_h = serious + 7.8 * q
    harp.add([S.N(t_h + 0.07 * i, d_end - t_h, p_, 64 - 2 * i)
              for i, p_ in enumerate(("D2", "A2", "D3", "F#3", "A3", "D4", "F#4", "A4", "D5"))])
    cel.add([S.N(t_h + 1.2, 1.6, "F#6", 52), S.N(t_h + 1.2, 1.6, "A6", 46)])

    for nm, f in (("trombones", 55), ("horns", 70), ("tuba", 25), ("bass_drum", 25), ("timpani", 32),
                  ("tuba_waddle", 25), ("basses_pizz", 30), ("bassoon", 50), ("bassoon_fx", 45),
                  ("trombone_sass", 60), ("sting_tuba", 25), ("xylophone", 400), ("violas_pizz", 120), ("celesta", 300),
                  ("basses_trem", 30), ("horns_tag", 70), ("low_strings_tag", 40), ("harp", 60)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(T["startled"], "startled"), (sass, "sass")] + [(t_, f"stomp{k + 1}") for k, t_ in enumerate(stomps)] + \
        [(wipe, "wipe_saliva"), (awk, "awkward"), (laugh, "laugh_start"), (a06_end, "a06 end: sting"), (snort, "snort"),
         (smirk, "anger_smirk"), (notices, "notices_smirk"), (serious, "serious")]
    cue = Cue("friend", tm, bars, chords_, S.list(), rt60=1.6, wet=0.24, predelay=0.015, target_lufs=-18.0,
              fade_in=0.0, fade_out=0.3, comp=(-14.0, 1.5, 15.0, 200.0), hits=hits, carve_db=6.0,
              top_parts=("bassoon", "horns_tag"), bass_parts=("tuba_waddle", "basses_pizz"))
    cue.notes_txt = compose_friend.__doc__
    return cue


# =========================================================================== cue: endcard


def compose_endcard() -> Cue:
    """end_card -> end (6.0 s; the timeline fades the last 1.0 s), under the closing narration n40
    (0.3-5.25). Anger's theme one last time, broad and heroic but leaving room for the voice: a hit on
    the title (0.0, before the voice), then the theme at ~91 bpm in horns + trombones (octaves, mf,
    the horns stepping back under the line) over galloping celli/basses, sustained strings, a soft
    choir and taiko pulses; harmony i | iv7 - bVII - bVII6 | I (bass D | G C E | D, contrary outer
    voices into the final D). The final D, timed just after the voice ends, is the BUTTON: one dry
    tutti D-MAJOR stab (the strangest friendship), the hall choked right after it."""
    T = TL("endcard")
    n40_0, n40_1 = T.lines["n40"]
    t_btn = n40_1 + 0.06
    tm = TempoMap([(0, 0.0), (8, t_btn)])
    S = Score(tm)
    bars = [0, 4, 8, tm.beat(T["end"])]
    chords_ = [(0, 4, "Dm"), (4, 6, "Gm7"), (6, 7, "C"), (7, 8, "C/E"), (8, 9, "D")]
    th = seq(THEME, 0, 104, "mel", bar=4)[:-1]
    shape_vels(th, [118, 112, 102, 96, 100, 106])
    hn = S("horns", "horns", pan=-0.2, send=0.34, legato=0.06, lazy=-0.04, opts={"level": -17.5, "vo_duck": 3.0})
    hn.add(transpose(th, 12))
    trb = S("trombones", "trombone", pan=0.18, send=0.3, legato=0.06, lazy=-0.05, opts={"level": -18.5, "vo_duck": 1.5})
    trb.add(th)
    tpt = S("trumpets", "trumpet", pan=0.06, send=0.32, humanize=0.0, lazy=-0.03, opts={"level": -20.0})
    for p_, part_ in ((("D4", "F#4", "A4"), hn), (("D3", "A3", "F#3"), trb), (("D5", "F#5", "A5"), tpt)):
        part_.add([Note(8, 0.4, P(x), 127) for x in p_])
    hn.dyn = [(0, 112), (1.0, 96), (7.0, 100), (7.9, 112), (8, 127)]
    trb.dyn = [(0, 116), (1.0, 98), (7.0, 102), (7.9, 112), (8, 127)]
    tpt.dyn = [(7.5, 90), (8, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.2, lazy=-0.05, humanize=0.0, opts={"level": -20.0})
    tuba.add(seq("D2:w | G1:h C2:q E2:q", 0, 108, bar=4))
    tuba.add([Note(8, 0.4, P("D1"), 127), Note(8, 0.4, P("D2"), 127)])
    vc = S("celli_ost", "vc", pan=0.2, send=0.22, humanize=0.005, lazy=-0.03, opts={"level": -20.0})
    vc.add(gallop(0, 4, P("D2"), va=96, vn=60) + gallop(4, 6, P("G2"), va=96, vn=60) + gallop(6, 7, P("C2"), va=96, vn=60)
           + gallop(7, 8, P("E2"), va=96, vn=60))
    vc.add([Note(8, 0.4, P("D2"), 127), Note(8, 0.4, P("D3"), 127)])
    vc.dyn = [(0, 100), (1, 86), (7, 96), (8, 127)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.2, humanize=0.005, lazy=-0.04, opts={"level": -22.0})
    cbf.add([Note(n.beat, n.dur, n.pitch, n.vel) for n in vc.notes if n.vel >= 96 and n.beat < 8])
    cbf.add([Note(8, 0.4, P("D2"), 127)])
    cbf.dyn = list(vc.dyn)
    pad = S("strings_pad", "vla", pan=-0.1, send=0.4, lazy=-0.15, opts={"level": -23.0, "vo_duck": 2.0})
    pv = voice_chords(chords_[:4], 3, 55, 69, top_max=66)
    pad.add(pad_notes(chords_[:4], pv, {"p": [0, 1, 2]}, 90)["p"])
    pad.dyn = [(0, 80), (8, 92)]
    vt = S("violins", "vln_slow", pan=-0.3, send=0.4, lazy=-0.12, opts={"level": -23.0, "vo_duck": 3.0})
    vt.add([Note(0, 4, P("A5"), 90), Note(4, 2, P("Bb5"), 90), Note(6, 2, P("G5"), 92)])
    vt.add([Note(8, 0.4, P(p_), 127) for p_ in ("D5", "F#5", "A5", "D6")])
    vt.dyn = [(0, 70), (4, 74), (7.6, 90), (8, 127)]
    ch = S("choir", "oohs", pan=0.0, send=0.45, lazy=-0.18, legato=0.1, opts={"level": -24.0, "vo_duck": 3.0})
    cv = voice_chords(chords_[:4], 4, 50, 67, top_max=64)
    ch.add(pad_notes(chords_[:4], cv, {"c": [0, 1, 2, 3]}, 100)["c"])
    ch.add([Note(8, 0.4, P(p_), 127) for p_ in ("D3", "A3", "D4", "F#4")])
    ch.dyn = [(0, 84), (7.6, 96), (8, 124)]
    tk = S("taiko", "taiko", pan=0.0, send=0.24, humanize=0.0, opts={"sat": 1.6, "level": -17.5})
    tkh = S("taiko_hi", "taiko", pan=-0.18, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -22.0})
    tk.add([Note(0, 1, P("C2"), 127)])
    for b in range(1, 8):
        (tk if b % 2 == 0 else tkh).add([Note(b, 1, P("C2") if b % 2 == 0 else P("A2"), 96 if b % 2 == 0 else 80)])
    tkh.add([Note(7.5, 0.5, P("A2"), 96), Note(7.75, 0.25, P("C3"), 104)])
    tk.add([Note(8, 1, P("C2"), 127)])
    tkh.add([Note(8, 1, P("F2"), 127)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.4, "slap": 0.15, "level": -19.0})
    boom.add([Note(2, 1, P("D1"), 96), Note(4, 1, P("G1"), 104), Note(6, 1, P("C2"), 100)])
    bb = S("boom_button", "boom", synth=synth_boom, opts={"decay": 0.28, "slap": 0.3, "sat": 1.4, "peak": -6.0})
    bb.add([Note(0, 1, P("D1"), 124), Note(8, 1, P("D1"), 127)])
    timp = S("timpani", "timpani", pan=0.14, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    timp.add([Note(0, 1, P("D2"), 124), Note(4, 1, P("G2"), 104), Note(6, 0.5, P("C3"), 100), Note(7, 0.5, P("E2"), 104)])
    timp.add(roll(P("A2"), 7.5, 7.98, tm, 16, 70, 116))
    timp.add([Note(8, 0.6, P("D2"), 127)])
    kit = S("cymbals", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -24.0})
    kit.add([Note(0, 2, 49, 116), Note(8, 0.4, 49, 116), Note(8, 0.4, 38, 120)])
    harp = S("harp", "harp", pan=-0.4, send=0.5, humanize=0.0, opts={"level": -27.0})
    harp.add(gliss({2, 6, 9}, P("D3"), P("D6"), 7.2, 0.75, 50, 84, ring=1.2))      # D-major sweep into the button
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.02, "release": 0.06, "release_end": 0.15,
                                                             "h2": 0.2, "level": -21.0})
    sub.add([Note(0, 4, P("D1"), 110), Note(4, 2, P("G1"), 100), Note(6, 1, P("C2"), 92), Note(7, 1, P("E1"), 96),
             Note(8, 0.4, P("D1"), 127)])
    for nm, f in (("horns", 80), ("trombones", 55), ("trumpets", 180), ("tuba", 25), ("celli_ost", 45),
                  ("basses_ost", 30), ("strings_pad", 110), ("violins", 200), ("choir", 100), ("taiko", 30),
                  ("taiko_hi", 40), ("timpani", 32), ("cymbals", 120), ("harp", 90)):
        S.parts[nm].eq = hpf(f)
    hits = [(T["end_card"], "end_card"), (t_btn, "button")]
    cue = Cue("endcard", tm, bars, chords_, S.list(), rt60=2.6, wet=0.3, predelay=0.025, target_lufs=-16.5,
              fade_in=0.0015, fade_out=0.2, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0), carve_db=5.0,
              wet_duck=[(t_btn + 0.22, T["end"], 0.06, 0.25)], gates=[(t_btn + 0.3, T["end"] + 1.0, set(), 0.22)],
              master_vol=[(0, 1.0), (0.6, -1.5), (7.88, 0.0), (7.93, -1.0), (7.985, -9.0), (8, 2.5), (8.5, 2.5)],
              hits=hits,
              top_parts=("horns",), bass_parts=("tuba",))
    cue.notes_txt = compose_endcard.__doc__
    return cue


COMPOSERS = {"descent": compose_descent, "cavern": compose_cavern, "tension": compose_tension, "fall": compose_fall,
             "depths": compose_depths, "menace": compose_menace, "hermit": compose_hermit, "lull": compose_lull,
             "friend": compose_friend, "endcard": compose_endcard}


if __name__ == "__main__":
    ml.main(sys.argv[1:], COMPOSERS)
