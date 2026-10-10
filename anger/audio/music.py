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

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import music_lib as ml  # noqa: E402
from music_lib import (QUAL, Cue, Note, P, Part, TempoMap, bass_of, bp, ctl, db, filt, harp_arp,  # noqa: E402,F401
                       hp, lp, mel_avoid, pad_notes, roll, seq, shape_vels, sos_shelf, synth_boom, synth_cymbal,
                       synth_drone, synth_heartbeat, synth_shimmer, synth_sub_pedal, transpose, voice_chords,
                       gliss, synth_bell)

QUAL.update({"mM7": (0, 3, 7, 11), "m7b5": (0, 3, 6, 10), "aug": (0, 4, 8), "7b9": (0, 4, 7, 10, 1),
             "m(add9)": (0, 2, 3, 7), "maj7#11": (0, 4, 6, 7, 11)})

# =========================================================================== themes

THEME = "D3:q. A3:e~ A3:h | F3:q. E3:e D3:q C3:q | D3:w"          # i | bVI v(sus4-3) | i
THEME_ANSWER = "Bb3:q. A3:e G3:q E3:q"                               # iv  V7  (back to i)
THEME_B = "F3:q. C4:e~ C4:h | Bb3:q. A3:e G3:q F3:q | E3:q. F3:e G3:q A3:q"   # III | iv7 | V7


# =========================================================================== helpers


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
    """S1 (0 -> reveal_settle, 39.0 s). Pre-roll drone and a reverse-cymbal rush into the title HIT
    (title_in 0.8); the walk (walk_start 4.0) at his stride: 0.55 s per beat = one taiko per
    footfall, the 3+3+2 galloping celli ostinato, Anger's theme in the horns (dark, low) over a
    wordless low choir; a ritard as he reaches the vines; three brass/taiko stabs on chop1-3
    (14.8/16.0/17.2: Dm - C - F, the third one launching the theme's second phrase in F, horns +
    trombones in octaves, choir); string swishes on the web swipes; the phrase climbs to the dominant
    as he reaches the door (24.6) -> a tense pause on an A tremolo (door tries 26.0/27.5 get soft
    timpani thuds); back_up (29.0) rebuilds on the A pedal (A -> Bb/A crunch -> A7); charge (31.4):
    run-up roll (taiko on his running footfalls, timpani + snare rolls, a violin/viola scale, cymbal
    swell, brass crescendo) into the MASSIVE HIT on door_burst (33.0, D minor tutti); then awe:
    Dm -> Bb/D -> an open Dsus2 at the reveal (36.5) with harp glint, fading by 39.0 under the
    cavern cue (which starts at 36.5)."""
    tm = TempoMap([(-6, 0.8), (0, 4.0), (16, 12.8), (19, 14.8), (21, 16.0), (23, 17.2), (31, 21.9),
                   (35, 24.6), (37, 26.0), (39, 27.5), (41, 29.0), (45, 31.4), (49, 33.0), (55, 36.5),
                   (59, 39.0)])
    B = tm.beat
    S = Score(tm)
    bars = [-7.5, -6, -3, 0, 4, 8, 12, 16, 19, 21, 23, 27, 31, 35, 37, 39, 41, 45, 49, 52, 55, 59]
    chords_ = [(-7.5, -6, "D5"), (-6, 0, "Dm"), (0, 4, "Dm"), (4, 6, "Bb"), (6, 8, "Am"), (8, 12, "Dm"),
               (12, 14, "Gm"), (14, 16, "A7"), (16, 19, "Dm"), (19, 21, "Dm"), (21, 23, "C"), (23, 27, "F"),
               (27, 31, "Gm7"), (31, 35, "A7"), (35, 41, "A5"), (41, 43, "A"), (43, 45, "Bb/A"),
               (45, 49, "A7"), (49, 52, "Dm"), (52, 55, "Bb/D"), (55, 59, "Dsus2")]

    # ---------------------------------------------------------------- the theme (horns, trombones)
    # first statement (the walk): low trombones carry the theme at D3, the horns double it an octave up
    hn = S("horns", "horns", pan=-0.22, send=0.34, legato=0.07, lazy=-0.03, opts={"level": -18.0})
    m1 = seq(THEME + " | " + THEME_ANSWER, 0, 86, "mel", bar=4)
    shape_vels(m1, [92, 98, 88, 82, 80, 84, 92, 88, 82, 80, 84])
    hn.add(transpose(m1, 12))
    hn.add([Note(16, 2.6, P("D4"), 84, "mel")])                         # home as he reaches the vines
    m2 = seq("F4:q. C5:e~ C5:h | Bb4:q. A4:e G4:q F4:q | E4:q. F4:e G4:q A4:q", 23, 100, "mel", bar=4)
    shape_vels(m2, [118, 108, 100, 92, 96, 100, 96, 100, 106, 112])
    hn.add(m2)
    hn.add([Note(35, 1.2, P("A4"), 96, "mel")])                          # arrives on the dominant, lets go
    hn.dyn = [(-0.3, 70), (8, 76), (15.5, 84), (17.5, 66), (18.9, 50), (22.9, 104), (31, 108), (34.8, 112),
              (35.6, 60), (36.3, 0)]
    # chop stabs (the third one IS the phrase's first note) and the door build / burst chords
    hst = S("horns_hits", "horns", pan=-0.1, send=0.36, humanize=0.0, lazy=-0.04, opts={"level": -19.0})
    hst.add([Note(19, 0.7, P(p_), 112) for p_ in ("A3", "D4", "F4")])
    hst.add([Note(21, 0.7, P(p_), 116) for p_ in ("G3", "C4", "E4")])
    hst.add([Note(23, 1.2, P(p_), 120) for p_ in ("A3", "C4")])
    hst.add([Note(43, 2.0, P(p_), 90) for p_ in ("D4", "F4")])            # Bb/A crunch
    hst.add([Note(45, 4.0, P(p_), 100) for p_ in ("C#4", "E4", "G4")])     # A7 into the burst
    hst.add([Note(49, 3.0, P(p_), 127) for p_ in ("D4", "F4", "A4", "D5")])  # BURST
    hst.add([Note(52, 3.0, P(p_), 84) for p_ in ("D4", "F4", "Bb4")])     # awe: Bb/D
    hst.dyn = [(18.8, 100), (23.8, 100), (24.2, 70), (42.8, 30), (45, 60), (48.9, 120), (49, 127),
               (50.2, 76), (52, 64), (53.5, 72), (55, 40), (56.5, 0)]

    trb = S("trombones", "trombone", pan=0.18, send=0.3, legato=0.06, lazy=-0.04, opts={"level": -18.5})
    trb.add([Note(n.beat, n.dur, n.pitch, n.vel) for n in m1] + [Note(16, 2.6, P("D3"), 84)])
    p2 = seq("F3:q. C4:e~ C4:h | Bb3:q. A3:e G3:q F3:q | E3:q. F3:e G3:q A3:q", 23, 100, bar=4)
    shape_vels(p2, [118, 108, 100, 92, 96, 100, 96, 100, 106, 112])
    trb.add(p2)
    trb.add([Note(35, 1.2, P("A3"), 92)])
    trb.dyn = [(-0.3, 76), (4, 80), (8, 84), (12, 88), (15.5, 92), (17.5, 70), (18.6, 30), (18.95, 0),
               (22.9, 100), (24, 92), (27, 98), (31, 104), (34.5, 112), (35.6, 60), (36.3, 0)]
    trh = S("trombones_hits", "trombone", pan=0.12, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -18.0})
    trh.add([Note(-6, 3.0, P(p_), 124) for p_ in ("A2", "D3", "F3")])     # TITLE
    trh.add([Note(19, 0.7, P(p_), 118) for p_ in ("A2", "D3", "F3")])
    trh.add([Note(21, 0.7, P(p_), 120) for p_ in ("G2", "C3", "E3")])
    trh.add([Note(41, 2.0, P(p_), 80) for p_ in ("A2", "C#3", "E3")])     # back_up: A
    trh.add([Note(43, 2.0, P(p_), 92) for p_ in ("Bb2", "D3", "F3")])     # Bb/A
    trh.add([Note(45, 4.0, P(p_), 104) for p_ in ("A2", "C#3", "G3")])    # A7
    trh.add([Note(49, 2.2, P(p_), 127) for p_ in ("A2", "D3", "F3", "A3")])  # BURST
    trh.dyn = [(-6.2, 127), (-5.4, 92), (-4, 54), (-1.5, 30), (0, 0), (18.8, 104), (22, 104),
               (40.9, 26), (43, 60), (45, 76), (48.9, 124), (49, 127), (50.2, 70), (51.2, 0)]

    tpt = S("trumpets", "trumpet", pan=0.05, send=0.4, humanize=0.0, lazy=-0.03, opts={"level": -21.0})
    tpt.add([Note(47, 2.0, P(p_), 96) for p_ in ("C#5", "E5")])
    tpt.add([Note(49, 1.6, P(p_), 127) for p_ in ("D5", "F5", "A5")])
    tpt.dyn = [(46.9, 20), (48.9, 118), (49, 127), (49.8, 90), (50.8, 0)]

    tuba = S("tuba", "tuba", pan=0.0, send=0.22, lazy=-0.05, humanize=0.0, opts={"level": -21.0})
    tuba.add([Note(-6, 4.0, P("D2"), 124), Note(19, 0.7, P("D2"), 120), Note(21, 0.7, P("C2"), 120),
              Note(23, 4, P("F1"), 104), Note(27, 4, P("G1"), 104), Note(31, 4, P("A1"), 108),
              Note(41, 8, P("A1"), 100), Note(49, 2.5, P("D1"), 127), Note(49, 2.5, P("D2"), 127)])
    tuba.dyn = [(-6.2, 124), (-5, 80), (-3, 40), (-2, 0), (18.8, 110), (22.9, 100), (24, 70), (34.5, 92),
                (35.3, 0), (40.9, 20), (45, 70), (48.9, 124), (49, 127), (50.5, 70), (51.4, 0)]

    # ---------------------------------------------------------------- strings
    vc = S("celli_ost", "vc", pan=0.2, send=0.22, humanize=0.006, lazy=-0.03, opts={"level": -19.0})
    g_walk = gallop(0, 17.5, P("D2"))
    g_p2 = gallop(23, 27, P("F2")) + gallop(27, 31, P("G2")) + gallop(31, 35, P("A2"))
    g_build = gallop(41, 45, P("A2"), va=96, vn=60)
    vc.add(g_walk + g_p2 + g_build)
    vc.dyn = [(-0.2, 70), (8, 80), (15.5, 88), (17.6, 40), (18, 0), (22.8, 0), (23, 100), (34.8, 108),
              (35.2, 0), (40.8, 0), (41, 44), (44.9, 104), (45.1, 0)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.2, humanize=0.006, lazy=-0.04, opts={"level": -21.5})
    cbf.add(accents_of(g_walk, P("D2")) + accents_of(g_p2, P("F2")) + accents_of(g_p2, P("G2")) +
            accents_of(g_p2, P("A2")) + accents_of(g_build, P("A2")))
    cbf.dyn = [(d[0], d[1]) for d in vc.dyn]

    cb = S("basses", "cb", pan=0.3, send=0.24, legato=0.1, lazy=-0.1, opts={"level": -22.0})
    cb.add([Note(-7.5, 7.5, P("D2"), 96), Note(16, 3, P("D2"), 90), Note(49, 10, P("D2"), 110)])
    cb.dyn = [(-7.5, 0), (-6.6, 50), (-6, 96), (-4.5, 64), (-1, 50), (0, 0), (15.8, 0), (16.2, 60), (18.9, 92),
              (19.1, 0), (48.9, 0), (49, 127), (50.2, 84), (52, 72), (55, 66), (57.5, 40), (59, 0)]
    trem = [(16, 3, "D3"), (35, 6, "A2"), (45, 4, "A2")]
    vct = S("celli_trem", "vc_trem", pan=0.15, send=0.3, humanize=0.0, opts={"level": -23.0})
    vct.add([Note(b, d, P(p_), 100) for b, d, p_ in trem])
    vct.dyn = [(15.9, 0), (16.3, 40), (18.9, 100), (19.1, 0), (34.9, 0), (35.3, 52), (36.8, 34), (39, 34),
               (40.9, 50), (44.9, 66), (45, 60), (48.95, 124), (49.05, 0)]
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.28, humanize=0.0, opts={"level": -24.0})
    cbt.add([Note(16, 3, P("D2"), 100), Note(35, 6, P("A1"), 100), Note(45, 4, P("A1"), 100)])
    cbt.dyn = list(vct.dyn)
    # the door: a thin high unease over the A pedal; the build: tremolo chords crescendo
    vlt = S("violins_trem", "vln_trem", pan=-0.3, send=0.38, humanize=0.0, opts={"level": -27.0}, eq=sul_pont)
    vlt.add([Note(35.4, 5.6, P("A5"), 70), Note(35.4, 5.6, P("E6"), 60)])
    vlt.add([Note(41, 2, P(p_), 90) for p_ in ("A4", "C#5", "E5")] + [Note(43, 2, P(p_), 96) for p_ in ("Bb4", "D5", "F5")])
    vlt.dyn = [(35.3, 0), (36.2, 40), (40.8, 44), (41, 40), (43, 64), (44.9, 90), (45.05, 0)]
    vlat = S("violas_trem", "vla_trem", pan=0.12, send=0.34, humanize=0.0, opts={"level": -25.0})
    vlat.add([Note(41, 2, P(p_), 90) for p_ in ("E4", "A4")] + [Note(43, 2, P(p_), 96) for p_ in ("F4", "Bb4")])
    vlat.add([Note(45, 4, P(p_), 100) for p_ in ("E4", "G4")])
    vlat.dyn = [(40.9, 0), (41.2, 40), (43, 64), (45, 76), (48.95, 122), (49.05, 0)]

    # swishes on the web swipes + the run-up scale into the burst (16ths), landing on the hit
    vln = S("violins", "vln1", pan=-0.32, send=0.32, humanize=0.0, lazy=-0.02, opts={"level": -20.5})
    for sw in (20.6, 21.9):
        for k, p_ in enumerate(("D4", "F4", "A4", "C5", "D5")):
            vln.add([S.N(sw - 0.26 + k * 0.055, 0.12 if k < 4 else 0.35, p_, 70 + 8 * k)])
    run = ["A3", "Bb3", "C#4", "D4", "E4", "F4", "G4", "A4", "Bb4", "C#5", "D5", "E5", "F5", "G5", "A5", "C#6"]
    for k, p_ in enumerate(run):
        vln.add([Note(45 + k * 0.25, 0.3, P(p_), 70 + 3 * k)])
    vln.add([Note(49, 3.0, P(p_), 127) for p_ in ("D5", "A5", "D6")])    # BURST
    vln.dyn = [(19.5, 96), (23, 96), (44.9, 60), (48.9, 118), (49, 127), (50.4, 80), (51.6, 0)]
    vlar = S("violas", "vla_fast", pan=0.16, send=0.3, humanize=0.0, lazy=-0.02, opts={"level": -22.5})
    for k, p_ in enumerate(run[:12]):
        vlar.add([Note(46 + k * 0.25, 0.3, P(p_), 70 + 3 * k)])
    vlar.add([Note(49, 3.0, P(p_), 127) for p_ in ("F4", "A4", "D5")])
    vlar.dyn = [(45.9, 56), (48.9, 116), (49, 127), (50.4, 80), (51.6, 0)]
    # awe: slow high strings Dm -> Bb/D -> Dsus2 under the choir
    awe = S("violins_awe", "vln_slow", pan=-0.25, send=0.5, lazy=-0.15, opts={"level": -23.5})
    awe.add([Note(49.6, 2.4, P("A5"), 90), Note(49.6, 2.4, P("F5"), 86), Note(52, 3, P("Bb5"), 90),
             Note(52, 3, P("F5"), 86), Note(55, 4, P("A5"), 92), Note(55, 4, P("E5"), 88), Note(55, 4, P("D6"), 84)])
    awe.dyn = [(49.5, 0), (50.6, 60), (52, 70), (54, 80), (55, 86), (56.5, 70), (58.2, 30), (59, 0)]
    vca = S("celli_awe", "vc_slow", pan=0.2, send=0.4, lazy=-0.12, opts={"level": -23.5})
    vca.add([Note(49, 10, P("D3"), 100), Note(49, 3, P("A3"), 96), Note(52, 3, P("Bb3"), 96), Note(55, 4, P("A3"), 96)])
    vca.dyn = [(48.9, 0), (49, 120), (50.2, 76), (52, 70), (55, 74), (57.5, 40), (59, 0)]

    # ---------------------------------------------------------------- choir
    oo = S("low_choir", "oohs", pan=0.05, send=0.45, legato=0.12, lazy=-0.18, opts={"level": -24.0})
    oc = [c for c in chords_ if -6 <= c[0] < 19]
    ov = voice_chords(oc, 3, 45, 62, avoid=mel_avoid(oc, m1, bars=bars), min_gap=3)
    oo.add(pad_notes(oc, ov, {"o": [0, 1, 2]}, 80)["o"])
    oo.add([Note(35.2, 5.8, P(p_), 76) for p_ in ("A2", "E3", "A3")])     # the door: hummed A
    oo.dyn = [(-6.2, 0), (-5.6, 56), (-3, 62), (0, 66), (8, 72), (15.5, 80), (18.9, 70), (19.05, 0),
              (35.1, 0), (36.3, 44), (40.9, 50), (41.1, 0)]
    ch = S("choir", "choir", pan=0.0, send=0.5, legato=0.12, lazy=-0.2, opts={"level": -20.5})
    cc = [c for c in chords_ if 23 <= c[0] < 35]
    cv = voice_chords(cc, 4, 50, 67, top_max=67)
    ch.add(pad_notes(cc, cv, {"c": [0, 1, 2, 3]}, 96)["c"])
    bc = [(41, 43, "A"), (43, 45, "Bb/A"), (45, 49, "A7")]
    bv = voice_chords(bc, 4, 52, 69, prev=cv[-1])
    ch.add(pad_notes(bc, bv, {"c": [0, 1, 2, 3]}, 100)["c"])
    ch.add([Note(49, 3, P(p_), 127) for p_ in ("D3", "A3", "D4", "F4", "A4")])
    ch.add([Note(52, 3, P(p_), 110) for p_ in ("D3", "Bb3", "D4", "F4", "Bb4")])
    ch.add([Note(55, 4, P(p_), 104) for p_ in ("D3", "A3", "E4", "A4")])
    ch.dyn = [(22.8, 0), (23, 84), (27, 92), (31, 100), (34.8, 108), (35.3, 0), (40.9, 0), (41.3, 40),
              (45, 76), (48.9, 122), (49, 127), (50.3, 90), (52, 92), (53.5, 100), (55, 96), (57, 70), (58.6, 30),
              (59, 0)]

    # ---------------------------------------------------------------- percussion (sync-locked)
    tk = S("taiko", "taiko", pan=0.0, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -16.0})
    tkh = S("taiko_hi", "taiko", pan=-0.18, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -20.5})
    tk.add([Note(-6, 2, P("C2"), 127)])
    tkh.add([Note(-6, 2, P("A2"), 112)])
    for b in range(0, 18):                                # the walk: one drum per footfall
        ramp = min(1.0, b / 12)
        if b % 2 == 0:
            tk.add([Note(b, 1, P("C2"), int(98 + 18 * ramp - (14 if b >= 16 else 0)))])
        else:
            tkh.add([Note(b, 1, P("A2"), int(80 + 14 * ramp - (12 if b >= 16 else 0)))])
    tkh.add([Note(7.5, 0.5, P("C3"), 62), Note(15.5, 0.5, P("C3"), 66)])
    for b, v in ((19, 127), (21, 127), (23, 127)):
        tk.add([Note(b, 2, P("C2"), v)])
        tkh.add([Note(b, 2, P("F2"), v - 10)])
    for b in range(24, 35):
        (tk if b % 2 else tkh).add([Note(b, 1, P("C2") if b % 2 else P("A2"), 82 if b % 2 else 70)])
    for sw in (20.6, 21.9):
        tkh.add([S.N(sw, 0.5, "F2", 118)])
    for b, v in ((41, 84), (42, 70), (43, 96), (43.5, 70), (44, 100), (44.5, 84)):
        tk.add([Note(b, 1, P("C2"), v)])
    for k in range(5):                                    # the run: his footfalls, every 0.31 s
        tk.add([S.N(31.4 + 0.31 * k, 0.3, "C2", 104 + 4 * k)])
    for k in range(4):
        tkh.add([S.N(32.6 + 0.1 * k, 0.1, "C3", 84 + 10 * k)])
    tk.add([Note(49, 3, P("C2"), 124)])
    tkh.add([S.N(33.004, 1.5, "F2", 120)])

    boom = S("boom", "boom", synth=synth_boom, pan=0.0, send=0.12, opts={"decay": 0.45, "slap": 0.0, "level": -18.0})
    for b in range(0, 17, 2):
        boom.add([Note(b, 1, P("D1"), 104 if b % 4 == 0 else 86)])
    boom.add([Note(19, 1, P("D1"), 120), Note(21, 1, P("C2"), 116), Note(23, 1, P("F1"), 124),
              Note(27, 1, P("G1"), 104), Note(31, 1, P("A1"), 108), Note(41, 1, P("A1"), 96), Note(43, 1, P("A1"), 104)])
    bigb = S("boom_big", "boom", synth=synth_boom, pan=0.0, send=0.1, opts={"decay": 1.3, "slap": 0.25, "drop": 1.6,
                                                                              "sat": 1.4, "peak": -5.5})
    bigb.add([Note(-6, 2, P("D1"), 118), Note(49, 2, P("D1"), 127), Note(49, 2, P("A1"), 92)])

    timp = S("timpani", "timpani", pan=0.14, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    timp.add([Note(-6, 2, P("D2"), 122)])
    timp.add([Note(b, 1.5, P("D2"), 66) for b in (4, 8, 12)])
    timp.add([Note(19, 1.5, P("D2"), 118), Note(21, 1.5, P("C3"), 118), Note(23, 2, P("F2"), 122),
              Note(27, 2, P("G2"), 96), Note(31, 2, P("A2"), 100)])
    timp.add([S.N(26.0, 0.8, "A2", 60), S.N(27.5, 0.8, "A2", 72)])      # under the locked-door thuds
    timp.add([Note(41, 1, P("A2"), 76), Note(43, 1, P("A2"), 88)])
    timp.add(roll(P("A2"), 45, 48.95, tm, 12, 40, 118))
    timp.add([S.N(33.007, 1.6, "D2", 124)])
    bd = S("gran_cassa", "bass_drum", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    bd.add([Note(-6, 3, P("A1"), 116), Note(23, 3, P("A1"), 96), S.N(33.003, 2.0, "A1", 127)])
    kit = S("snare_cym", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -24.0})
    t = 31.4
    while t < 32.97:
        x = (t - 31.4) / 1.6
        kit.add([S.N(t, 0.05, 38, int(36 + 80 * x ** 1.4))])
        t += 0.055
    kit.add([S.N(33.009, 1.0, 49, 120), S.N(33.012, 1.0, 57, 106), S.N(33.006, 0.3, 38, 116)])
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -24.0})
    cym.opts["events"] = [(0.0, 0.8, 0.55, 0.85, 2.0, 3.6),
                          (20.25, 20.6, 0.22, 0.18, 0.7, 2.5), (21.55, 21.9, 0.22, 0.18, 0.7, 2.5),
                          (31.4, 33.0, 1.0, 1.0, 3.6, 3.4),
                          (35.6, 36.5, 0.18, 0.16, 2.5, 2.0)]
    cym.notes = [cym_note(tm, 0.8, 100), cym_note(tm, 33.0, 127), cym_note(tm, 36.5, 50)]

    # ---------------------------------------------------------------- low end, colour
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, pan=0.0, send=0.0,
            opts={"attack": 0.3, "release": 0.12, "release_end": 1.0, "h2": 0.2, "h3": 0.06, "level": -21.0})
    sub.add([Note(-7.5, 26.5, P("D1"), 100), Note(23, 4, P("F1"), 96), Note(27, 4, P("G1"), 96),
             Note(31, 10, P("A1"), 92), Note(41, 8, P("A1"), 100), Note(49, 10, P("D1"), 110)])
    sub.dyn = [(-7.5, 0), (-6.3, 60), (-6, 110), (-4, 70), (0, 76), (16, 84), (19, 96), (23, 100), (35, 64),
               (41, 70), (48.9, 112), (49, 127), (51, 96), (55, 80), (57.5, 50), (59, 0)]
    harp = S("harp", "harp", pan=-0.4, send=0.55, humanize=0.0, opts={"level": -26.0})
    harp.add(gliss({2, 4, 9}, P("D3"), P("A6"), 54.2, 0.8, 50, 90, ring=4.0))
    cel = S("celesta", "celesta", pan=0.3, send=0.6, humanize=0.0, opts={"level": -28.0})
    cel.add([Note(55, 3, P("A6"), 70), Note(55.5, 3, P("E6"), 60), Note(56.5, 2.5, P("D6"), 56)])
    shim = S("shimmer", "shimmer", synth=synth_shimmer, pan=0.0, send=0.6, opts={"level": -30.0})
    shim.add([Note(51, 8, P("A5"), 80), Note(51, 8, P("E6"), 80)])
    shim.dyn = [(51, 0), (53, 70), (55, 100), (57.5, 60), (59, 0)]

    # clean low end
    for nm, f in (("horns", 70), ("horns_hits", 90), ("trombones", 60), ("trombones_hits", 50), ("trumpets", 180),
                  ("celli_ost", 45), ("basses_ost", 30), ("basses", 30), ("celli_trem", 60), ("basses_trem", 30),
                  ("violins", 160), ("violas", 110), ("violins_awe", 200), ("celli_awe", 60), ("low_choir", 80),
                  ("choir", 100), ("taiko", 30), ("taiko_hi", 40), ("timpani", 32), ("gran_cassa", 25),
                  ("snare_cym", 120), ("harp", 90), ("celesta", 300), ("tuba", 25)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    cb.eq = ml.fundamental_lift(cb.notes, tm, 4.0, lo_pitch=P("A1"), base=hpf(25))

    hits = [(0.8, "title_in"), (4.0, "walk_start"), (14.8, "chop1"), (16.0, "chop2"), (17.2, "chop3"),
            (20.6, "web_swipe1"), (21.9, "web_swipe2"), (24.6, "door_arrive"), (26.0, "door_try1"),
            (27.5, "door_try2"), (29.0, "back_up"), (31.4, "charge"), (33.0, "door_burst"), (36.5, "reveal")]
    # the whole-cue dynamic arc (seconds -> dB): brooding after the title, the walk building, the chops
    # and the second phrase strong, the door hushed, the build, a 100 ms breath, the burst on top
    arc = [(0.0, -3.0), (0.8, 0.0), (1.8, -3.5), (3.0, -8.0), (4.0, -8.5), (8.0, -7.5), (12.6, -6.0),
           (13.6, -7.5), (14.7, -6.0), (14.8, -2.0), (17.2, -1.5), (21.9, -1.5), (24.3, -0.5), (24.6, -3.0),
           (29.0, -6.5), (31.4, -6.5), (32.86, -6.0), (32.97, -15.0), (33.0, 1.5), (34.0, 1.0), (35.0, 0.0),
           (36.5, -1.5), (39.0, -5.0)]
    cue = Cue("descent", tm, bars, chords_, S.list(), rt60=3.2, wet=0.36, predelay=0.03, target_lufs=-16.5,
              fade_in=0.01, fade_out=1.2, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0),
              master_vol=[(B(t_), v_) for t_, v_ in arc], wet_duck=[(32.86, 32.995, 0.35, 0.05)],
              hits=hits, landmarks=[(6.4, "title_out"), (13.5, "vines"), (19.6, "webs")],
              top_parts=("horns",), bass_parts=("basses", "basses_ost", "tuba"))
    cue.notes_txt = compose_descent.__doc__
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
    chords_ = [(a, b, c.replace("DmM7", "DmM7")) for a, b, c in chords_]
    QUAL.setdefault("mM7", (0, 3, 7, 11))

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
    gl = S("glass", "glass_pad", pan=0.0, send=0.6, lazy=-0.3, opts={"level": -27.0})
    gc = [c for c in chords_ if c[0] < 19.5]
    gv = voice_chords(gc, 3, 57, 76, min_gap=3)
    gl.add(pad_notes(gc, gv, {"g": [0, 1, 2]}, 70)["g"])
    gl.dyn = [(0, 0), (2.5, 40), (6, 64), (11.5, 60), (12, 84), (14, 56), (19, 64), (19.5, 0)]
    oo = S("far_choir", "oohs", pan=-0.15, send=0.75, legato=0.2, lazy=-0.25, opts={"level": -27.5})
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
    arc = [(0.0, -6.0), (2.5, -3.0), (11.99, -2.0), (12.0, 0.0), (13.5, -2.0), (15.0, -3.0), (19.4, -1.5), (19.9, -1.5), (21.2, 0.5)]
    hits = [(0.0, "reveal"), (3.0, "look_around"), (7.5, "search_start"), (12.0, "eyes_glow"),
            (13.3, "eyes_scurry"), (19.5, "stone_shift"), (19.9, "torch_fly"), (21.2, "torch_splash (cut)")]
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
    hits = [(0.0, "continue"), (8.6, "wrong_rock"), (9.2, "collapse (cut)")]
    cue = Cue("tension", tm, bars, chords_, S.list(), rt60=3.4, wet=0.36, predelay=0.03, target_lufs=-18.0,
              fade_in=0.2, end_cut=True, send_hp=80.0, comp=(-10.0, 1.3, 20.0, 250.0),
              master_vol=[(B(0.0), -4.0), (B(4.0), -2.0), (B(8.5), 0.0)], hits=hits,
              landmarks=[(beats[k], "") for k in range(0, nb, 4)], top_parts=("violins_harm",),
              bass_parts=("basses_trem",))
    cue.notes_txt = compose_tension.__doc__ + f"\nHeartbeats at: {', '.join(f'{b_:.2f}' for b_ in beats)} s"
    return cue


# =========================================================================== cue: fall


def compose_fall() -> Cue:
    """S3 (collapse 78.3 -> fall_end 95.9; 17.6 s). HIT on the collapse (0.0): an Eb-major-over-D
    shock chord, tutti percussion. grab_ledge (1.0): a horn stab, then the STRAIN (beat = 0.725 s,
    taiko pulse): a chromatic string wedge - violins I climb A5-Bb5-B5-C6 over a held D5 while the
    tremolo violas sink F4-E4-Eb4-D4 - and from slipping (2.7) the trombones drag down A2-G#2-G2,
    each step swelling harder. let_go (6.8): everything stops. falling (7.0): time stops - a solemn
    sustained choir chord (Bb add9) with a high string halo, eyes closing. sword_thrust (10.8): a
    violent SURGE - Anger's theme ff in horns / trumpets / trombones at 100 bpm, driving celli and
    basses, taiko 8ths, a snare roll, screeching sul-ponticello violins gliding upward a fourth -
    timed so the theme's final D IS the impact (15.6): a thunderous short tutti hit with the
    biggest booms of the film, then nothing (only its decay)."""
    tm = TempoMap([(-1, 0.0), (0, 1.0), (8, 6.8), (12, 10.8), (20, 15.6), (24, 17.6)])
    B = tm.beat
    S = Score(tm)
    bars = [-1, 0, 2, 4, 6, 8, 12, 16, 20, 24]
    chords_ = [(-1, 0, "Eb/D"), (0, 2, "Dm"), (2, 4, "Bbmaj7#11/D"), (4, 6, "Abdim/D"), (6, 8, "D7sus4"),
               (8, 12, "Bbadd9"), (12, 16, "Dm"), (16, 18, "Gm7"), (18, 20, "Am"), (20, 24, "Dm")]

    # ---------------------------------------------------------------- strings
    v1 = S("violins_strain", "vln_slow", pan=-0.32, send=0.36, legato=0.1, lazy=-0.12, opts={"level": -19.5})
    v1.add([Note(0, 2, P("A5"), 96), Note(2, 2, P("Bb5"), 100), Note(4, 2, P("B5"), 106), Note(6, 2, P("C6"), 112)])
    v1.dyn = [(-0.2, 0), (0.05, 60), (1.2, 80), (2, 70), (3.2, 92), (4, 80), (5.2, 104), (6, 92), (7.5, 124),
              (7.98, 127), (8.02, 0)]
    v2 = S("violins2_pedal", "vln2", pan=-0.18, send=0.36, lazy=-0.12, opts={"level": -22.0})
    v2.add([Note(0, 8, P("D5"), 96)])
    v2.dyn = [(-0.2, 0), (0.1, 56), (4, 76), (7.5, 110), (7.98, 116), (8.02, 0)]
    vlt = S("violas_trem", "vla_trem", pan=0.12, send=0.34, humanize=0.0, opts={"level": -21.5})
    vlt.add([Note(0, 2, P("F4"), 96), Note(2, 2, P("E4"), 98), Note(4, 2, P("Eb4"), 102), Note(6, 2, P("D4"), 108)])
    vlt.add([Note(12, 8, P(p_), 110) for p_ in ("D4", "F4")])
    vlt.dyn = [(-0.2, 0), (0.1, 54), (2, 66), (4, 80), (6, 96), (7.98, 118), (8.02, 0), (11.98, 0), (12, 110),
               (19.9, 120), (20.0, 0)]
    vcp = S("celli_pulse", "vc", pan=0.2, send=0.25, humanize=0.006, lazy=-0.03, opts={"level": -20.5})
    for k in range(16):
        b = k * 0.5
        vcp.add([Note(b, 0.35, P("D3"), 100 if k % 2 == 0 else 70)])
    vcp.add(gallop(12, 16, P("D2")) + gallop(16, 18, P("G2")) + gallop(18, 20, P("A2")))
    vcp.dyn = [(-0.2, 0), (0.1, 60), (4, 76), (7.9, 112), (8.0, 0), (11.98, 0), (12, 110), (19.9, 124), (20.0, 0)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.22, humanize=0.006, lazy=-0.04, opts={"level": -21.5})
    cbf.add([Note(n.beat, n.dur, n.pitch, n.vel)
             for n in vcp.notes if n.beat >= 12 and n.pitch in (P("D2"), P("G2"), P("A2"))])
    cbf.dyn = [(11.98, 0), (12, 112), (19.9, 124), (20.0, 0)]
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.3, humanize=0.0, opts={"level": -22.5})
    cbt.add([Note(0, 8, P("D2"), 100)])
    cbt.dyn = [(-0.2, 0), (0.1, 60), (7.9, 110), (8.0, 0)]
    # screeching strings on the sword: a sul-ponticello tremolo cluster gliding up a fourth
    scr = S("violins_screech", "vln_trem", pan=-0.25, send=0.4, humanize=0.0, eq=sul_pont, opts={"level": -21.0})
    scr.add([Note(12, 8, P(p_), 110) for p_ in ("A5", "Bb5", "E6")])
    scr.bend = [(12, 0), (12.3, 0), (20, 500)]
    scr.bend_range = 7
    scr.dyn = [(11.98, 0), (12, 124), (12.6, 96), (16, 104), (19.9, 127), (20.0, 0)]
    # the collapse / grab / impact string stabs
    sst = S("strings_hits", "vln1", pan=-0.1, send=0.32, humanize=0.0, lazy=-0.03, opts={"level": -21.0})
    sst.add([Note(-1, 0.8, P(p_), 124) for p_ in ("Eb5", "G5", "Bb5")])
    sst.add([Note(20, 0.45, P(p_), 127) for p_ in ("D5", "A5", "D6")])
    vcs = S("low_strings_hits", "vc", pan=0.22, send=0.28, humanize=0.0, lazy=-0.03, opts={"level": -20.0})
    vcs.add([Note(-1, 0.8, P("D2"), 124), Note(-1, 0.8, P("D3"), 124), Note(20, 0.45, P("D2"), 127),
             Note(20, 0.45, P("D3"), 127)])
    # time stops: a high halo + low strings under the choir
    halo = S("violins_halo", "vln_slow", pan=-0.3, send=0.6, lazy=-0.2, opts={"level": -27.0})
    halo.add([Note(8.3, 3.5, P("D6"), 70), Note(8.3, 3.5, P("F6"), 64)])
    halo.dyn = [(8.2, 0), (9.2, 50), (10.4, 40), (10.75, 0)]
    lowp = S("low_strings_pad", "vc_slow", pan=0.2, send=0.5, lazy=-0.25, opts={"level": -24.0})
    lowp.add([Note(8.2, 3.6, P("Bb2"), 90), Note(8.2, 3.6, P("F3"), 84)])
    lowp.dyn = [(8.1, 0), (9.0, 54), (10.3, 48), (10.75, 0)]

    # ---------------------------------------------------------------- brass
    hn = S("horns", "horns", pan=-0.2, send=0.34, legato=0.05, lazy=-0.04, opts={"level": -17.0})
    hn.add([Note(-1, 0.9, P(p_), 124) for p_ in ("Eb4", "G4", "Bb4")])
    hn.add([Note(0, 0.7, P(p_), 116) for p_ in ("D4", "F4", "A4")])        # grab_ledge
    th = seq(THEME, 12, 112, "mel", bar=4)[:-1]                           # D A F E D C ... (final D = impact)
    shape_vels(th, [116, 124, 110, 104, 108, 112])
    hn.add(transpose(th, 12))
    hn.add([Note(20, 0.45, P(p_), 127, "mel" if p_ == "D4" else "") for p_ in ("D4", "F4", "A4")])
    hn.dyn = [(-1.2, 124), (-0.4, 70), (-0.05, 40), (0, 116), (0.6, 50), (1, 0), (11.95, 0), (12, 120),
              (16, 116), (19.9, 127)]
    tpt = S("trumpets", "trumpet", pan=0.08, send=0.38, legato=0.04, lazy=-0.03, opts={"level": -19.5})
    tpt.add(transpose(th, 24))
    tpt.add([Note(20, 0.45, P(p_), 127) for p_ in ("D5", "F5", "A5")])
    tpt.dyn = [(11.95, 0), (12, 118), (16, 112), (19.9, 127)]
    trb = S("trombones", "trombone", pan=0.18, send=0.3, legato=0.05, lazy=-0.05, opts={"level": -18.5})
    trb.add([Note(-1, 0.9, P(p_), 124) for p_ in ("Eb3", "G3", "Bb3")])
    trb.add([Note(2, 2, P("A2"), 90), Note(4, 2, P("G#2"), 96), Note(6, 2, P("G2"), 104)])   # dragged down
    trb.add(th)
    trb.add([Note(20, 0.45, P(p_), 127) for p_ in ("A2", "D3", "F3", "A3")])
    trb.dyn = [(-1.2, 124), (-0.4, 70), (0, 0), (1.9, 0), (2.4, 50), (3.6, 72), (4, 60), (5.4, 88), (6, 76),
               (7.6, 118), (7.98, 124), (8.02, 0), (11.95, 0), (12, 120), (19.9, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.22, lazy=-0.05, humanize=0.0, opts={"level": -20.0})
    tuba.add([Note(-1, 1, P("D2"), 124), Note(-1, 1, P("D1"), 110), Note(12, 4, P("D2"), 110), Note(16, 2, P("G1"), 112),
              Note(18, 2, P("A1"), 116), Note(20, 0.45, P("D1"), 127), Note(20, 0.45, P("D2"), 127)])
    tuba.dyn = [(-1.2, 124), (-0.3, 60), (0, 0), (11.95, 0), (12, 116), (19.9, 127)]

    # ---------------------------------------------------------------- choir
    ch = S("choir", "choir", pan=0.0, send=0.55, legato=0.15, lazy=-0.25, opts={"level": -19.5})
    ch.add([Note(B(7.0), 11.85 - B(7.0), P(p_), 96) for p_ in ("Bb2", "F3", "D4", "F4", "C5")])
    cc = [(12, 16, "Dm"), (16, 18, "Gm7"), (18, 20, "Am")]
    cv = voice_chords(cc, 4, 50, 67, top_max=65)
    ch.add(pad_notes(cc, cv, {"c": [0, 1, 2, 3]}, 110)["c"])
    ch.add([Note(20, 0.5, P(p_), 127) for p_ in ("D3", "A3", "D4", "F4")])
    ch.dyn = [(B(6.95), 0), (B(7.3), 40), (B(8.4), 84), (B(9.4), 92), (B(10.2), 74), (B(10.65), 56), (11.85, 0),
              (11.95, 0), (12, 104), (19.9, 124), (20.3, 110), (20.5, 0)]

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
    tk.add([Note(20, 2, P("C2"), 127)])
    tkh.add([Note(20, 2, P("F2"), 127), Note(19.75, 0.25, P("A2"), 116)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.55, "slap": 0.1, "level": -18.0})
    boom.add([Note(-1, 1, P("D1"), 124), Note(0, 1, P("D1"), 100), Note(12, 1, P("D1"), 124), Note(14, 1, P("D1"), 104),
              Note(16, 1, P("G1"), 116), Note(18, 1, P("A1"), 116)])
    bigb = S("boom_big", "boom", synth=synth_boom, opts={"decay": 0.95, "slap": 0.3, "drop": 1.8, "sat": 1.4, "peak": -5.0})
    bigb.add([Note(20, 3, P("D1"), 127), Note(20, 3, P("A1"), 96)])
    timp = S("timpani", "timpani", pan=0.14, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -19.5})
    timp.add([Note(-1, 1, P("D2"), 124), Note(0, 1, P("D2"), 110), Note(12, 2, P("D2"), 124), Note(16, 2, P("G2"), 116),
              Note(18, 1, P("A2"), 116)])
    timp.add(roll(P("D2"), 19.0, 19.95, tm, 14, 70, 124))
    timp.add([S.N(15.607, 1.2, "D2", 124)])
    bd = S("gran_cassa", "bass_drum", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -19.0})
    bd.add([Note(-1, 2, P("A1"), 124), Note(12, 2, P("A1"), 116), S.N(15.603, 1.8, "A1", 127)])
    kit = S("snare_cym", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -22.5})
    kit.add([Note(-1, 2, 49, 118), Note(12, 2, 57, 120), S.N(15.609, 1.0, 49, 124), S.N(15.612, 1.0, 57, 116)])
    t_ = 10.8
    while t_ < 15.55:
        x = (t_ - 10.8) / 4.8
        kit.add([S.N(t_, 0.07, 38, int(60 + 40 * x + (14 if abs((t_ - 10.8) / 0.6 - round((t_ - 10.8) / 0.6)) < 0.01 else 0)))])
        t_ += 0.075
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -22.0})
    cym.opts["events"] = [(0.0, 0.0, 0.0, 1.0, 2.2), (10.3, 10.8, 0.6, 0.9, 2.0, 3.6), (14.4, 15.5, 0.6, 1.0, 1.1, 3.4)]
    cym.notes = [cym_note(tm, 0.0, 120), cym_note(tm, 10.8, 116), cym_note(tm, 15.6, 127)]
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.05, "release": 0.1, "release_end": 0.6,
                                                             "h2": 0.22, "h3": 0.06, "level": -21.0})
    sub.add([Note(-1, 9, P("D1"), 100), Note(B(7.0), 12 - B(7.0), P("Bb1"), 70), Note(12, 4, P("D1"), 110),
             Note(16, 2, P("G1"), 104), Note(18, 2, P("A1"), 108), Note(20, 1.2, P("D1"), 127)])
    sub.dyn = [(-1, 127), (-0.3, 70), (0, 80), (7.9, 110), (8.0, 0), (B(7.0), 0), (9.5, 50), (11.8, 30), (12, 120),
               (19.9, 120), (20, 127), (21.2, 0)]

    for nm, f in (("violins_strain", 180), ("violins2_pedal", 160), ("violas_trem", 120), ("celli_pulse", 50),
                  ("basses_ost", 30), ("basses_trem", 30), ("strings_hits", 160), ("low_strings_hits", 40),
                  ("violins_halo", 300), ("low_strings_pad", 45), ("horns", 80), ("trumpets", 180),
                  ("trombones", 55), ("tuba", 25), ("choir", 80), ("taiko", 30), ("taiko_hi", 40), ("timpani", 32),
                  ("gran_cassa", 25), ("snare_cym", 120)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    arc = [(0.0, 2.0), (0.6, -2.0), (1.0, -1.0), (1.6, -4.5), (4.0, -3.0), (6.75, 1.0), (6.8, -1.0), (7.0, 0.0),
           (10.3, 0.0), (10.79, -2.0), (10.8, -2.5), (14.6, -2.0), (15.48, -2.5), (15.585, -12.0), (15.6, 4.0),
           (16.5, 4.0)]
    hits = [(0.0, "collapse"), (1.0, "grab_ledge"), (2.7, "slipping"), (6.8, "let_go"), (7.0, "falling"),
            (10.8, "sword_thrust"), (15.6, "impact")]
    cue = Cue("fall", tm, bars, chords_, S.list(), rt60=3.0, wet=0.34, predelay=0.03, target_lufs=-16.0,
              fade_in=0.0015, fade_out=0.5, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0),
              master_vol=[(B(t_), v_) for t_, v_ in arc], hits=hits, wet_duck=[(6.85, 7.4, 0.5, 0.4), (15.47, 15.6, 0.4, 0.08), (16.1, 17.6, 0.3, 0.6)],
              top_parts=("horns",), bass_parts=("tuba", "basses_ost", "basses_trem"))
    cue.notes_txt = compose_fall.__doc__
    return cue


# =========================================================================== cue: depths


def compose_depths() -> Cue:
    """S4 start (96.5) -> monster_approach (115.5); 19.0 s (the timeline fades it in over 2 s).
    Low aching drones: a breathing additive drone on D1+A1 (independently drifting partials), the
    contrabasses on D2, a slow celli line of minor-second sighs (F3-E3, G3-F3-E3) under a viola
    A3-Bb3-A3, a faint blurred glass halo, and a faint, slightly irregular heartbeat. eyes_again
    (9.0) brings back the cavern sting's colours very softly (sul-ponticello Eb6, celesta G#5/D6);
    pass_out (12.0) dims everything to the drone; wake_noise (15.4) restarts the pulse (a low pizz,
    the heart) and a celli tremolo creeps up; one_arm (17.4): the celli sink to C#3 over the D
    pedal (A/D) with a pp horn A3, handing over to the menace cue."""
    tm = TempoMap.const(60)
    S = Score(tm)
    bars = [0, 4, 8, 12, 15.4, 19]
    chords_ = [(0, 4, "Dm"), (4, 7, "Dm(add9)"), (7, 9, "Gm/D"), (9, 11.5, "Dm"), (11.5, 15.4, "Dm(add9)"),
               (15.4, 17.4, "Dm"), (17.4, 19, "A/D")]
    dr = S("drone", "drone", synth=synth_drone, pan=0.0, send=0.3,
           opts={"attack": 2.5, "release": 2.0, "tilt": 1.1, "kmax": 16, "move": 0.55, "lp": 1800, "level": -21.0})
    dr.add([Note(0, 13.0, P("D1"), 110), Note(0.5, 12.0, P("A1"), 80), Note(12.6, 6.4, P("D1"), 100),
            Note(15.4, 3.6, P("A1"), 76)])
    dr.dyn = [(0, 90), (11.5, 100), (12.5, 70), (14.5, 64), (15.4, 76), (19, 100)]
    cb = S("basses", "cb", pan=0.28, send=0.4, legato=0.1, lazy=-0.15, opts={"level": -25.0})
    cb.add([Note(0.6, 11.8, P("D2"), 90), Note(15.4, 3.6, P("D2"), 90)])
    cb.dyn = [(0.5, 0), (2.5, 50), (8, 60), (11.4, 54), (12.5, 0), (15.3, 0), (16.5, 46), (19, 60)]
    vc = S("celli_sighs", "vc_slow", pan=0.2, send=0.45, legato=0.15, lazy=-0.18, opts={"level": -22.0})
    sighs = [(1.0, 3.0, "F3"), (4.0, 2.6, "E3"), (7.0, 2.0, "G3"), (9.0, 2.5, "F3"), (11.5, 1.6, "E3"),
             (15.6, 1.8, "D3"), (17.4, 1.6, "C#3")]
    vc.add([Note(t_, d_, P(p_), 92, "mel") for t_, d_, p_ in sighs])
    vc.dyn = [(0.8, 0), (2.3, 70), (3.6, 62), (4.0, 66), (5.0, 74), (6.6, 40), (7.0, 50), (8.4, 76), (9.0, 70),
              (10.4, 74), (11.5, 56), (12.6, 30), (13.1, 0), (15.5, 0), (16.4, 52), (17.4, 60), (18.4, 70), (19, 64)]
    vla = S("violas", "vla", pan=-0.1, send=0.45, legato=0.15, lazy=-0.18, opts={"level": -25.0})
    vla.add([Note(1.5, 5.5, P("A3"), 86), Note(7.0, 2.0, P("Bb3"), 90), Note(9.0, 3.0, P("A3"), 84)])
    vla.dyn = [(1.4, 0), (3.5, 54), (6.6, 50), (7.0, 56), (8.3, 70), (9.0, 60), (11.4, 44), (12.4, 0)]
    gl = S("glass", "glass_pad", pan=0.0, send=0.7, lazy=-0.3, opts={"level": -30.0})
    gl.add([Note(0.4, 6.0, P(p_), 60) for p_ in ("D5", "E5", "A5")])
    gl.dyn = [(0.3, 0), (2.2, 50), (4.5, 40), (6.4, 0)]
    hb = S("heartbeat", "heartbeat", synth=synth_heartbeat, opts={"gap": 0.24, "dub": 0.5, "decay": 0.12, "seed": 3,
                                                                  "level": -22.0})
    beats_ = [0.8, 2.0, 3.25, 4.4, 5.6, 6.9, 8.1, 9.3, 10.5, 11.8, 13.4, 15.0, 15.9, 16.85, 17.75, 18.6]
    hb.add([S.N(t_, 0.3, "G1", (54 if 12 < t_ < 15.3 else 80) + (8 if t_ > 15.3 else 0), "mel") for t_ in beats_])
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.6, humanize=0.0, eq=sul_pont, opts={"level": -30.0})
    vt.add([Note(9.0, 2.6, P("Eb6"), 70)])
    vt.dyn = [(8.95, 0), (9.4, 40), (10.8, 30), (11.6, 0)]
    cel = S("celesta", "celesta", pan=0.3, send=0.7, humanize=0.0, opts={"level": -30.0})
    cel.add([Note(9.0, 2.0, P("G#5"), 52), Note(9.0, 2.0, P("D6"), 48)])
    pz = S("pizz", "cb_pizz", pan=0.25, send=0.4, humanize=0.0, opts={"level": -26.0})
    pz.add([Note(15.4, 1.5, P("D2"), 84), Note(17.4, 1.5, P("D2"), 76)])
    vct = S("celli_trem", "vc_trem", pan=0.15, send=0.45, humanize=0.0, opts={"level": -27.0})
    vct.add([Note(16.0, 3.0, P("D3"), 90)])
    vct.dyn = [(15.95, 0), (17.0, 24), (19.0, 60)]
    hn = S("horn", "horns", pan=-0.2, send=0.5, lazy=-0.1, opts={"level": -27.0})
    hn.add([Note(17.4, 1.6, P("A3"), 80)])
    hn.dyn = [(17.3, 0), (18.4, 50), (19.0, 44)]
    for nm, f in (("basses", 30), ("celli_sighs", 55), ("violas", 110), ("glass", 300), ("celesta", 300),
                  ("pizz", 30), ("celli_trem", 60), ("horn", 90)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(0.4, "dazed"), (3.0, "assess"), (9.0, "eyes_again"), (12.0, "pass_out"), (15.4, "wake_noise"),
            (17.4, "one_arm")]
    cue = Cue("depths", tm, bars, chords_, S.list(), rt60=3.8, wet=0.4, predelay=0.04, target_lufs=-19.0,
              fade_in=0.5, end_cut=True, send_hp=70.0, comp=(-10.0, 1.3, 30.0, 400.0),
              master_vol=[(0, 0.0), (11.6, 0.0), (12.8, -4.0), (15.0, -4.0), (16.0, -1.0), (19, 0.0)], hits=hits,
              top_parts=("celli_sighs",), bass_parts=("basses",))
    cue.notes_txt = compose_depths.__doc__
    return cue


# =========================================================================== cue: menace


def compose_menace() -> Cue:
    """monster_approach (115.5) -> rock_hit (123.6); 8.1 s. A creeping crescendo that accelerates
    (0.65 -> 0.49 s per beat): a chromatic pizzicato crawl in celli + basses rising from D2, a tremolo
    semitone cluster creeping upward in violas/violins, the low brass (tuba + trombones, D/Eb) growling
    in from arm_up (2.6), a stopped-horn + boom sting on monster_reveal (4.2), taiko pulses closing
    in, a timpani roll and a cymbal swell, the violins shrieking upward on the lunge (7.6) - and the
    whole orchestra CUT DEAD on rock_hit (8.1)."""
    tm = TempoMap([(0, 0.0), (4, 2.6), (7, 4.2), (14, 7.6), (15, 8.1)])
    B = tm.beat
    S = Score(tm)
    bars = [0, 4, 7, 11, 14, 15]
    chords_ = [(0, 7, "Dm"), (7, 14, "Eb/D"), (14, 15, "Eb/D")]
    crawl = ["D2", "D2", "Eb2", "D2", "E2", "Eb2", "F2", "E2", "F#2", "F2", "G2", "F#2", "Ab2", "G2", "A2", "Ab2",
             "Bb2", "A2", "B2", "Bb2", "C3", "B2", "C#3", "C3", "D3", "C#3", "Eb3", "D3"]
    vcp = S("celli_pizz", "vc_pizz", pan=0.2, send=0.35, humanize=0.0, opts={"level": -21.0})
    vcp.add([Note(0.5 * k, 0.4, P(p_), int(56 + 60 * k / 27), "mel") for k, p_ in enumerate(crawl)])
    cbp = S("basses_pizz", "cb_pizz", pan=0.3, send=0.3, humanize=0.0, opts={"level": -22.0})
    cbp.add([Note(0.5 * k, 0.4, P(p_) - 12 if P(p_) - 12 >= 28 else P(p_), int(60 + 56 * k / 27))
             for k, p_ in enumerate(crawl) if k % 2 == 0])
    cbt = S("basses_trem", "cb_trem", pan=0.3, send=0.35, humanize=0.0, opts={"level": -23.0})
    cbt.add([Note(0, 15.2, P("D2"), 100)])
    cbt.dyn = [(0, 44), (4, 52), (7, 72), (14, 112), (15, 127)]
    vlt = S("violas_trem", "vla_trem", pan=0.1, send=0.4, humanize=0.0, opts={"level": -23.0})
    vlt.add([Note(0, 7, P("A3"), 90), Note(0, 7, P("Bb3"), 90), Note(7, 4, P("B3"), 96), Note(7, 4, P("C4"), 96),
             Note(11, 4.2, P("C#4"), 100), Note(11, 4.2, P("D4"), 100)])
    vlt.dyn = [(0, 20), (4, 40), (7, 72), (11, 90), (14, 116), (15, 127)]
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.4, humanize=0.0, eq=sul_pont, opts={"level": -22.0})
    vt.add([Note(4, 3, P("Eb5"), 80), Note(7, 4, P("E5"), 90), Note(11, 4.2, P("F5"), 100),
            Note(11, 4.2, P("Gb5"), 100)])
    vt.bend = [(13.9, 0), (15, 700)]
    vt.bend_range = 9
    vt.dyn = [(3.9, 0), (4.5, 30), (7, 64), (11, 84), (14, 110), (15, 127)]
    trb = S("trombones", "trombone", pan=0.18, send=0.35, humanize=0.0, lazy=-0.05, opts={"level": -20.0})
    trb.add([Note(4, 11.2, P("D3"), 100), Note(4, 11.2, P("Eb3"), 100), Note(7, 8.2, P("A3"), 100)])
    trb.dyn = [(4, 0), (4.6, 24), (7, 60), (7.4, 50), (11, 80), (14, 118), (15, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.25, humanize=0.0, lazy=-0.05, opts={"level": -21.0})
    tuba.add([Note(4, 11.2, P("D1"), 100), Note(4, 11.2, P("D2"), 100)])
    tuba.dyn = [(4, 0), (5, 30), (7, 64), (11, 84), (14, 120), (15, 127)]
    hs = S("horns_stopped", "horns", pan=-0.2, send=0.45, humanize=0.0, lazy=-0.04,
           eq=lambda x: filt(hp(x, 120), sos_shelf(2200, 5.0)), opts={"level": -21.0})
    hs.add([Note(7, 1.6, P(p_), 124) for p_ in ("A3", "Bb3", "Eb4")])
    hs.add([Note(11, 4.2, P(p_), 100) for p_ in ("Bb3", "Eb4")])
    hs.dyn = [(6.95, 124), (7.5, 64), (8.6, 30), (11, 40), (14, 110), (15, 127)]
    oo = S("choir", "oohs", pan=0.0, send=0.5, humanize=0.0, lazy=-0.2, opts={"level": -25.0})
    oo.add([Note(7, 8.2, P(p_), 90) for p_ in ("D3", "Eb3", "A3")])
    oo.dyn = [(6.9, 0), (8, 30), (11, 56), (14, 96), (15, 120)]
    tk = S("taiko", "taiko", pan=0.0, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -18.5})
    for b, v in ((0, 70), (2, 74), (4, 90), (5.5, 76), (7, 124), (8, 84), (9, 88), (10, 92), (11, 100), (12, 102),
                 (12.5, 90), (13, 108), (13.5, 98), (14, 120), (14.25, 104), (14.5, 112), (14.75, 120)):
        tk.add([Note(b, 0.5, P("C2") if v >= 100 or b % 1 == 0 else P("A2"), v)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.5, "slap": 0.0, "level": -20.0})
    boom.add([Note(7, 1, P("D1"), 124), Note(11, 1, P("D1"), 96), Note(14, 1, P("D1"), 120)])
    timp = S("timpani", "timpani", pan=0.14, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    timp.add([Note(7, 1, P("D2"), 116)])
    timp.add(roll(P("D2"), 12, 15.05, tm, 14, 44, 124))
    pno = S("piano_low", "piano", pan=0.0, send=0.45, humanize=0.0, opts={"level": -25.0})
    pno.add([Note(7, 3, P(p_), 104) for p_ in ("D1", "Eb1", "A1")])
    pno.pedal = [(6.9, 10.5)]
    cym = S("cymbal", "cymbal", synth=synth_cymbal, pan=0.1, send=0.45, opts={"level": -24.0})
    cym.opts["events"] = [(6.4, 8.15, 1.0, 0.0, 1.0, 2.8)]
    cym.notes = [cym_note(tm, 6.4, 90)]
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.6, "h2": 0.25, "level": -24.0})
    sub.add([Note(0, 15.2, P("D1"), 100)])
    sub.dyn = [(0, 60), (7, 84), (15, 127)]
    for nm, f in (("celli_pizz", 50), ("basses_pizz", 30), ("basses_trem", 30), ("violas_trem", 120),
                  ("trombones", 60), ("tuba", 25), ("choir", 90), ("taiko", 35), ("timpani", 32), ("piano_low", 28)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(0.0, "monster_approach"), (2.6, "arm_up"), (4.2, "monster_reveal"), (7.6, "monster_lunge"),
            (8.1, "rock_hit (cut)")]
    cue = Cue("menace", tm, bars, chords_, S.list(), rt60=3.0, wet=0.34, predelay=0.03, target_lufs=-17.0,
              fade_in=0.01, end_cut=True, send_hp=80.0, comp=(-10.0, 1.3, 20.0, 250.0),
              master_vol=[(0, 0.0), (4, -2.0), (6.98, -3.0), (7, 0.0), (8, -2.5), (14, -0.5), (15, 0.0)], hits=hits,
              top_parts=("violins_trem",), bass_parts=("basses_trem",))
    cue.notes_txt = compose_menace.__doc__
    return cue


# =========================================================================== cue: hermit


def compose_hermit() -> Cue:
    """hermit_start/m02 (131.62) -> crunch_end (139.71); 8.09 s (the timeline fades its last 1.5 s).
    The comedy starts: under m02 (0-2.19) only a tiptoeing low pizzicato (D2 / A1, nothing in the
    voice band); glove_grab (2.49) = a pizzicato chord + temple-block tick and the bassoon 'drags'
    the monster off down a chromatic scale (D4 -> G3, legato, swaying); crunch (4.49) starts a quirky
    staccato bassoon march in D minor over an oom-pah of pizzicato basses / violas."""
    tm = TempoMap([(0, 0.0), (5, 2.49), (9, 4.49), (17, 8.49)])
    S = Score(tm)
    bars = [0, 1, 5, 9, 13, 17]
    chords_ = [(0, 5, "Dm"), (5, 9, "Dm"), (9, 11, "Dm"), (11, 13, "A"), (13, 14, "Dm"), (14, 15, "Gm"), (15, 17, "A")]
    cbp = S("basses_pizz", "cb_pizz", pan=0.25, send=0.22, humanize=0.006, opts={"level": -21.0})
    cbp.add(seq("D2:q A1:q D2:q A1:q D2:q", 0, 70, vels=[74, 64, 70, 62, 72]))
    cbp.add(seq("D2:q r:q A1:q r:q | D2:q G1:q A1:q r:q", 9, 84, bar=4))
    cbp.add([Note(5, 1, P("D2"), 110)])
    vcp = S("celli_pizz", "vc_pizz", pan=0.15, send=0.22, humanize=0.006, opts={"level": -23.0})
    vcp.add([Note(5, 1, P(p_), 112) for p_ in ("D3", "A3")])
    vlp = S("violas_pizz", "vla_pizz", pan=-0.15, send=0.24, humanize=0.006, opts={"level": -24.0})
    vlp.add([Note(5, 1, P("F4"), 108)])
    for b_, sym in ((9.5, "Dm"), (10.5, "Dm"), (11.5, "A"), (12.5, "A"), (13.5, "Dm"), (14.5, "Gm"), (15.5, "A"),
                    (16.5, "A")):
        ch_ = {"Dm": ("F3", "A3"), "A": ("E3", "C#4"), "Gm": ("G3", "Bb3")}[sym]
        vlp.add([Note(b_, 0.4, P(p_), 74) for p_ in ch_])
    bsn = S("bassoon", "bassoon", pan=0.05, send=0.24, legato=0.03, humanize=0.008, opts={"level": -17.5})
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
    hits = [(0.0, "m02 / start"), (2.49, "glove_grab"), (4.49, "crunch")]
    cue = Cue("hermit", tm, bars, chords_, S.list(), rt60=1.6, wet=0.22, predelay=0.015, target_lufs=-18.0,
              fade_in=0.02, fade_out=0.3, comp=(-14.0, 1.5, 15.0, 200.0), hits=hits,
              top_parts=("bassoon",), bass_parts=("basses_pizz",))
    cue.notes_txt = compose_hermit.__doc__
    return cue


# =========================================================================== cue: lull


def compose_lull() -> Cue:
    """snore_start (152.94) -> startled (172.46); 19.52 s (timeline fades 2 s in / 2 s out). A soft,
    slightly absurd lullaby in F major, 3/4 at 100 bpm (beat 0 = 0.22 s, so drip1/drip2 land on
    beats 23/25): a harp rocks gently, a tuba breathes the 'oom' of every bar; during a02 (4.0-6.22)
    only those low notes play. From close_eyes (8.02) the tune (original) sings in celesta + music box
    while a sleepy bassoon doubles it two octaves down and YAWNS (a slow downward bend) on the long
    note; drips (14.02, 15.22) get high celesta plinks, hand_wave (15.82) a staccato bassoon 'bup';
    on side_eye_open (17.02) the tune stops on its A and the harmony sours (Bbm/F), a low bassoon
    'huh?' on sees_tongue (18.52)."""
    tm = TempoMap.const(100, start=0.22)
    S = Score(tm)
    bars = [3 * k for k in range(12)]
    chords_ = [(0, 3, "F"), (3, 6, "C7"), (6, 9, "F"), (9, 12, "C7"), (12, 15, "F"), (15, 18, "C7"), (18, 21, "F"),
               (21, 24, "F"), (24, 27, "Bb"), (27, 28, "F/A"), (28, 33, "Bbm/F")]
    tuba = S("tuba", "tuba", pan=0.0, send=0.3, lazy=-0.04, opts={"level": -22.0})
    for b0, b1, sym in chords_:
        if b0 >= 28:
            continue
        root = {"F": "F1", "C7": "C2", "Bb": "Bb1", "F/A": "A1"}[sym]
        tuba.add([Note(b0, 1.6, P(root), 84)])
    tuba.add([Note(28.0, 4, P("F1"), 70)])
    tuba.dyn = [(0, 70), (12, 80), (27, 76), (28, 60), (32, 50)]
    harp = S("harp", "harp", pan=-0.3, send=0.45, humanize=0.008, opts={"level": -23.0})
    rock = {"F": ("F2", "C3", "A3"), "C7": ("C2", "G2", "Bb3"), "Bb": ("Bb1", "F2", "D3"), "F/A": ("A1", "F2", "C3")}
    for b0, b1, sym in chords_:
        if b0 >= 28:
            continue
        lo_, mid, top = rock[sym]
        if b1 - b0 < 3:                                   # the 1-beat F/A: just the bass, damped
            harp.add([Note(b0, b1 - b0, P(lo_), 60)])
            continue
        dialog = 6 <= b0 < 12
        harp.add([Note(b0, 2.8, P(lo_), 62)])
        harp.add([Note(b0 + 1, 1.8, P(mid), 50)])
        if not dialog:
            harp.add([Note(b0 + 2, 1.0, P(top), 46)])
    harp.add([Note(28, 4, P("F2"), 50), Note(28.5, 3.5, P("Db3"), 44)])
    mel = seq("C5:h A4:q | Bb4:h G4:q | A4:q F4:q A4:q | C5:h. | D5:h Bb4:q | A4:h.", 12, 60, "mel", bar=3)
    shape_vels(mel, [62, 54, 58, 50, 56, 52, 58, 66, 64, 56, 60])
    mel[-1].dur = 1.0                                     # stops dead on side_eye_open (beat 28)
    cel = S("celesta", "celesta", pan=0.15, send=0.5, humanize=0.008, opts={"level": -20.0})
    cel.add(mel)
    cel.add([Note(23, 1.5, P("F6"), 64), Note(25, 1.5, P("C7"), 60)])          # the drips
    mb = S("music_box", "musicbox", pan=-0.1, send=0.5, humanize=0.006, opts={"level": -25.0})
    mb.add(transpose(mel, 12, tag=""))
    bsn = S("bassoon", "bassoon", pan=0.1, send=0.32, legato=0.05, humanize=0.01, opts={"level": -21.0})
    bm = transpose(mel, -24, tag="")
    bm[-1].dur = 1.0
    bsn.add(bm)
    bsn.dyn = [(11.9, 56), (12, 60), (21, 66), (22.6, 70), (23.9, 40), (24, 58), (27.9, 50)]
    bsn.bend = [(21.0, 0), (22.4, 0), (23.85, -300), (23.97, 0)]       # the yawn on the long C
    bsn.bend_range = 4
    bfx = S("bassoon_fx", "bassoon", pan=0.12, send=0.32, humanize=0.0, opts={"level": -23.0})
    bfx.add([Note(26, 0.3, P("F2"), 96), Note(30.5, 1.6, P("Db2"), 80)])  # hand_wave 'bup', sees_tongue 'huh?'
    bfx.bend = [(30.5, 0), (31.3, 0), (32.0, 150)]
    bfx.bend_range = 2
    bfx.dyn = [(25.9, 90), (30.4, 70), (31.2, 90), (32.1, 40)]
    vct = S("celli_trem", "vc_trem", pan=0.2, send=0.5, humanize=0.0, opts={"level": -30.0})
    vct.add([Note(28.2, 4.5, P("Db3"), 80), Note(28.2, 4.5, P("F3"), 76)])
    vct.dyn = [(28.1, 0), (29.5, 30), (32.5, 46)]
    for nm, f in (("tuba", 25), ("harp", 40), ("celesta", 300), ("music_box", 500), ("bassoon", 40),
                  ("bassoon_fx", 40), ("celli_trem", 60)):
        S.parts[nm].eq = hpf(f)
    hits = [(0.0, "snore_start"), (2.4, "contemplate"), (8.02, "close_eyes"), (11.02, "sleeping"), (14.02, "drip1"),
            (15.22, "drip2"), (15.82, "hand_wave"), (17.02, "side_eye_open"), (18.52, "sees_tongue")]
    cue = Cue("lull", tm, bars, chords_, S.list(), rt60=1.8, wet=0.3, predelay=0.02, target_lufs=-19.0,
              fade_in=0.3, fade_out=0.3, comp=(-14.0, 1.4, 25.0, 300.0), hits=hits,
              top_parts=("celesta",), bass_parts=("tuba",))
    cue.notes_txt = compose_lull.__doc__
    return cue


# =========================================================================== cue: friend


def compose_friend() -> Cue:
    """startled (172.46) -> end_card (228.226); 55.77 s. Bb major, 1 beat = 0.7 s (beat 0 = 0.14 s,
    so the three sass stomps fall on beats 18/19/20). startled (0.0): a big dumb major chord BWAAMP
    (tuba, trombones, horns, bassoon, timpani, bass drum), gone before a03 (1.6). A bassoon 'hi!'
    before m04; under m04 / a04 / m05 only the friend's low waddle (staccato tuba + pizzicato basses,
    Bb-F oom), with little bassoon waddle licks in the gaps. sass (11.84): the bassoon huffs up
    (bend), a pizzicato pickup, then the stomps (12.74, 13.44, 14.14): tuba + bass drum + timpani +
    a scooping trombone line D-Eb-E rising to F on the button (14.49). wipe_saliva (20.07): a bassoon
    'bleh' sagging down; awkward (20.77): the music stops - only his foot taps (sfx). Under the laugh
    (from 33.6) a deadpan pizzicato tick-tock; m07: a low sinking pedal (tuba D1, contrabass
    tremolo, a bassoon slipping A2-G#2-G2-F#2-F2) ending on a pizzicato 'question' (46.1); a06 in
    silence; the DEADPAN STING at a06's end (49.07): one low muted D-minor 'bwomp' that sags;
    snort (49.87): the bouncy giggle figure (staccato bassoon triplets, pizzicato, tuba oom-pah,
    xylophone), a celesta 'ting' on anger_smirk (51.27), cut off on notices_smirk (52.47); serious
    (53.27): a tiny heroic tag of Anger's theme (horns D-A-F-E, low strings, timpani) whose timpani
    roll swells into the end-card cue (cut at 55.77)."""
    tm = TempoMap.const(60 / 0.7, start=0.14)
    B = tm.beat
    S = Score(tm)
    bars = [-0.2] + [4 * k for k in range(0, 21)]
    chords_ = [(-0.2, 2.5, "Bb"), (5, 28.5, "Bb"), (28.5, 29.5, "Bb"), (B(38.35), B(46.2), "Dm"),
               (B(49.07), B(49.7), "Dm"), (B(49.87), B(50.57), "Bb"), (B(50.57), B(51.27), "F7"), (B(51.27), B(51.97), "Bb"),
               (B(51.97), B(52.47), "F7"), (B(53.27), B(55.77), "Dm")]
    # ---------------------------------------------------------------- 0.0 the reveal: BWAAMP
    trb = S("trombones", "trombone", pan=0.15, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -18.0})
    trb.add([S.N(0.0, 1.4, p_, 124) for p_ in ("Bb2", "D3", "F3")])
    trb.dyn = [(B(0.0), 127), (B(0.5), 96), (B(1.35), 30), (B(1.5), 0)]
    hn = S("horns", "horns", pan=-0.2, send=0.3, humanize=0.0, lazy=-0.05, opts={"level": -21.0})
    hn.add([S.N(0.0, 1.4, p_, 120) for p_ in ("F3", "Bb3", "D4")])
    hn.dyn = list(trb.dyn)
    tuba = S("tuba", "tuba", pan=0.0, send=0.22, humanize=0.0, lazy=-0.05, opts={"level": -19.0})
    tuba.add([S.N(0.0, 1.45, "Bb1", 124)])
    tuba.add([S.N(38.6, 7.5, "D1", 90)])                                 # m07: the sinking pedal
    tuba.dyn = [(B(0.0), 127), (B(0.6), 90), (B(1.45), 0), (B(38.5), 0), (B(40.0), 46), (B(45.5), 56), (B(46.1), 0)]
    bdr = S("bass_drum", "bass_drum", pan=0.0, send=0.25, humanize=0.0, opts={"level": -21.0})
    bdr.add([S.N(0.0, 1.0, "A1", 116)])
    timp = S("timpani", "timpani", pan=0.12, send=0.28, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    timp.add([S.N(0.0, 1.0, "Bb2", 110)])

    # ---------------------------------------------------------------- the waddle (low only under dialogue)
    tst = S("tuba_waddle", "tuba_st", pan=0.0, send=0.2, humanize=0.006, opts={"level": -20.0})
    cbp = S("basses_pizz", "cb_pizz", pan=0.25, send=0.2, humanize=0.006, opts={"level": -22.0})

    # the friend's waddle theme, sung by the tuba in its low register (under the voices: fundamentals
    # 44-87 Hz, staccato), the contrabass pizzicato marking the strong beats an octave up. Phrases
    # rock left-right (Bb-F) and climb by step (Bb C D Eb) like a heavy body shifting its weight.
    WADDLE = {5: [("F1", 1)], 6: [("Bb1", 1)], 7: [("F1", 1)], 8: [("Bb1", 0.5), ("C2", 0.5)], 9: [("D2", 1)],
              10: [("Bb1", 0.5)],
              12: [("Eb2", 1)], 13: [("C2", 1)], 14: [("F1", 1)], 15: [("A1", 0.5), ("C2", 0.5)], 16: [("Bb1", 0.5)],
              21: [("Bb1", 1)], 22: [("F1", 1)], 23: [("Bb1", 0.5), ("C2", 0.5)], 24: [("D2", 1)], 25: [("Eb2", 1)],
              26: [("C2", 1)], 27: [("F1", 0.5), ("A1", 0.5)], 28: [("Bb1", 0.5)]}
    for b0, cells in WADDLE.items():
        b = b0
        for k, (p_, d_) in enumerate(cells):
            strong = (b % 2 == 0) and k == 0
            tst.add([Note(b, 0.42 if d_ >= 1 else 0.3, P(p_), 70 if strong else 62, "mel")])
            if k == 0 and d_ >= 1 or b % 1 == 0:
                cbp.add([Note(b, 0.7, P(p_) + 12, 62 if strong else 52)])
            b += d_

    bsn = S("bassoon", "bassoon_st", pan=0.08, send=0.24, humanize=0.006, opts={"level": -18.0})
    bsn.add([S.N(2.98, 0.14, "Bb2", 92, "mel"), S.N(3.16, 0.14, "D3", 96, "mel"), S.N(3.34, 0.2, "F3", 104, "mel")])
    bsn.add([Note(10.5, 0.3, P("F3"), 96, "mel"), Note(11.0, 0.3, P("D3"), 90, "mel"),
             Note(11.5, 0.35, P("Bb2"), 100, "mel")])                    # the waddle lick
    # the giggle (snort 49.87 -> notices_smirk 52.47): staccato 8th-note triplets at 0.7 s per beat
    # one triplet group per beat, over the tuba's Bb / F7 oom: hee-hee-hee rising D - Eb - F, then a squeal
    gig = ["D3", "D3", "D3", "Eb3", "Eb3", "Eb3", "F3", "F3", "F3", "A3", "C4", "F3"]
    for k, p_ in enumerate(gig):
        t_ = 49.87 + k * 0.7 / 3
        if t_ > 52.35:
            break
        bsn.add([S.N(t_, 0.12, p_, (104 if k % 3 == 0 else 88) + (10 if k >= 9 else 0), "mel")])
    bfx = S("bassoon_fx", "bassoon", pan=0.1, send=0.26, humanize=0.0, opts={"level": -19.0})
    bfx.add([S.N(11.84, 0.5, "F2", 104)])                               # sass: the huff, scooping up
    bfx.add([S.N(20.07, 0.55, "Ab2", 96)])                              # wipe_saliva: 'bleh'
    bfx.add([S.N(t_, 1.35, p_, 78) for t_, p_ in ((38.6, "A2"), (40.0, "G#2"), (41.4, "G2"), (42.8, "F#2"),
                                                     (44.2, "F2"))])     # m07: slipping down
    bfx.bend = [(B(11.84), -300), (B(12.2), 500), (B(12.4), 500), (B(12.5), 0), (B(20.07), 0), (B(20.62), -400),
                (B(20.7), 0)]
    bfx.bend_range = 6
    bfx.dyn = [(B(11.8), 100), (B(12.3), 110), (B(12.35), 0), (B(20.0), 96), (B(20.62), 40), (B(20.7), 0),
               (B(38.5), 0), (B(39.2), 32), (B(45.5), 38), (B(45.6), 0)]

    # ---------------------------------------------------------------- sass (11.84) and the stomps
    cbp.add([S.N(12.39, 0.3, "F2", 92), S.N(12.565, 0.3, "A2", 96)])     # pickup "ba-dum"
    tst.add([S.N(t_, 0.45, "Bb1", 124, "mel") for t_ in (12.74, 13.44, 14.14)])
    bdr.add([S.N(t_, 1.0, "A1", 112 + 6 * k) for k, t_ in enumerate((12.74, 13.44, 14.14))])
    timp.add([S.N(t_, 0.6, "F2" if k < 2 else "Bb2", 104 + 8 * k) for k, t_ in enumerate((12.74, 13.44, 14.14))])
    ts = S("trombone_sass", "trombone", pan=-0.1, send=0.28, humanize=0.0, lazy=-0.02, opts={"level": -18.5})
    ts.add([S.N(12.74, 0.55, "D3", 110), S.N(13.44, 0.55, "Eb3", 114), S.N(14.14, 0.3, "E3", 120),
            S.N(14.49, 0.3, "F3", 124)])
    ts.bend = [(B(12.70), -250), (B(12.86), 0), (B(13.40), 0), (B(13.41), -250), (B(13.56), 0), (B(14.10), 0),
               (B(14.11), -250), (B(14.24), 0)]
    ts.bend_range = 3
    ts.dyn = [(B(12.6), 110), (B(14.8), 120)]
    xy = S("xylophone", "xylo", pan=0.3, send=0.3, humanize=0.0, opts={"level": -24.0})
    xy.add([S.N(14.49, 0.3, "F5", 100), S.N(14.49, 0.3, "Bb5", 96)])
    cbp.add([S.N(14.49, 0.4, "Bb1", 112)])
    # the giggle accompaniment: oom-pah, pizzicato chords, xylophone sparkles
    for k in range(4):
        t_ = 49.87 + 0.7 * k
        if t_ > 52.35:
            break
        tst.add([S.N(t_, 0.3, "Bb1" if k % 2 == 0 else "F1", 100)])
        cbp.add([S.N(t_, 0.4, "Bb2" if k % 2 == 0 else "F2", 96)])
    vlp = S("violas_pizz", "vla_pizz", pan=-0.2, send=0.26, humanize=0.006, opts={"level": -23.0})
    vlp.add([S.N(46.1, 0.4, "Eb4", 70)])                                # the m07 'question'
    for k in range(4):
        t_ = 49.87 + 0.7 * k + 0.35
        if t_ > 52.35:
            break
        vlp.add([S.N(t_, 0.3, p_, 90) for p_ in (("D4", "F4") if k % 2 == 0 else ("C4", "Eb4"))])
    xy.add([S.N(49.87 + k * 0.7, 0.2, p_, 90) for k, p_ in enumerate(("F6", "Eb6", "F6")) if 49.87 + k * 0.7 < 52.3])
    cel = S("celesta", "celesta", pan=0.25, send=0.45, humanize=0.0, opts={"level": -24.0})
    cel.add([S.N(51.27, 1.0, "D6", 80), S.N(51.27, 1.0, "F6", 70)])     # anger_smirk: 'ting'

    # ---------------------------------------------------------------- the laugh: tick-tock; m07: sinking
    cbp.add([S.N(t_, 0.6, "D2", 64) for t_ in (33.6, 35.0, 36.4, 37.8)])
    cbt = S("basses_trem", "cb_trem", pan=0.28, send=0.3, humanize=0.0, opts={"level": -25.0})
    cbt.add([S.N(38.6, 7.5, "D2", 90)])
    cbt.dyn = [(B(38.5), 0), (B(40.0), 34), (B(45.6), 46), (B(46.1), 0)]

    # ---------------------------------------------------------------- the deadpan sting (49.07)
    sting = S("sting_brass", "trombone", pan=0.1, send=0.2, humanize=0.0, lazy=0.0,
              eq=lambda x: lp(hp(x, 60), 2200), opts={"level": -19.0})
    sting.add([S.N(49.07, 0.55, p_, 112) for p_ in ("D3", "F3", "A3")])
    sting.bend = [(B(49.07), 0), (B(49.32), 0), (B(49.62), -180)]
    sting.bend_range = 2
    sting.dyn = [(B(49.0), 112), (B(49.4), 80), (B(49.62), 0)]
    stu = S("sting_tuba", "tuba", pan=0.0, send=0.2, humanize=0.0, lazy=0.0, opts={"level": -21.0})
    stu.add([S.N(49.07, 0.55, "D2", 110)])
    stu.dyn = [(B(49.0), 110), (B(49.4), 80), (B(49.62), 0)]
    stu.bend = [(B(49.07), 0), (B(49.32), 0), (B(49.62), -180)]
    bdr.add([S.N(49.07, 1.0, "A1", 84)])

    # ---------------------------------------------------------------- serious (53.27): the tiny heroic tag
    tag = S("horns_tag", "horns", pan=-0.15, send=0.38, legato=0.05, lazy=-0.04, opts={"level": -18.5})
    q = 0.3
    tag.add([S.N(53.27, 1.5 * q, "D3", 96, "mel"), S.N(53.27 + 1.5 * q, 2.5 * q, "A3", 104, "mel"),
             S.N(53.27 + 4 * q, 1.5 * q, "F3", 96, "mel"), S.N(53.27 + 5.5 * q, 2.6, "E3", 100, "mel")])
    tag.dyn = [(B(53.2), 96), (B(54.9), 100), (B(55.77), 110)]
    lowtag = S("low_strings_tag", "vc_slow", pan=0.2, send=0.38, lazy=-0.1, opts={"level": -21.0})
    lowtag.add([S.N(53.27, 2.6, "D2", 96), S.N(53.27, 2.6, "A2", 90)])
    lowtag.dyn = [(B(53.2), 80), (B(55.77), 104)]
    timp.add([S.N(53.27, 0.4, "D2", 96), S.N(53.72, 0.4, "A2", 90)])
    timp.add(roll(P("D2"), B(54.92), B(55.80), tm, 14, 40, 112))

    for nm, f in (("trombones", 55), ("horns", 70), ("tuba", 25), ("bass_drum", 25), ("timpani", 32),
                  ("tuba_waddle", 25), ("basses_pizz", 30), ("bassoon", 50), ("bassoon_fx", 45),
                  ("trombone_sass", 60), ("sting_tuba", 25), ("xylophone", 400), ("violas_pizz", 120), ("celesta", 300),
                  ("basses_trem", 30), ("horns_tag", 70), ("low_strings_tag", 40)):
        p_ = S.parts[nm]
        p_.eq = chain(p_.eq, hpf(f)) if p_.eq is not None else hpf(f)
    hits = [(0.0, "startled"), (11.84, "sass"), (12.74, "stomp1"), (13.44, "stomp2"), (14.14, "stomp3"),
            (20.07, "wipe_saliva"), (20.77, "awkward"), (29.47, "laugh_start"), (49.07, "a06 end: sting"),
            (49.87, "snort"), (51.27, "anger_smirk"), (52.47, "notices_smirk"), (53.27, "serious"),
            (55.766, "end_card (cut)")]
    cue = Cue("friend", tm, bars, chords_, S.list(), rt60=1.6, wet=0.24, predelay=0.015, target_lufs=-18.0,
              fade_in=0.0, end_cut=True, comp=(-14.0, 1.5, 15.0, 200.0), hits=hits, carve_db=6.0,
              top_parts=("bassoon", "horns_tag"), bass_parts=("tuba_waddle", "basses_pizz"))
    cue.notes_txt = compose_friend.__doc__
    return cue


# =========================================================================== cue: endcard


def compose_endcard() -> Cue:
    """end_card (228.226) -> end (233.226); 5.0 s, the timeline fades the last 1.0 s. Anger's theme
    one last time, full and heroic at 133 bpm: horns + trombones + trumpets in octaves, choir, the
    galloping celli/basses, taiko, booms; harmony i | iv7 - bVII - bVII6 | i (bass D | G C E | D, so
    the outer voices move in contrary motion into the final D). The final D (3.6 s) is the BUTTON:
    one dry tutti stab, the hall choked right after it, silence under the fade."""
    tm = TempoMap.const(60 / 0.45)
    S = Score(tm)
    bars = [0, 4, 8, 11.1]
    chords_ = [(0, 4, "Dm"), (4, 6, "Gm7"), (6, 7, "C"), (7, 8, "C/E"), (8, 9, "Dm")]
    th = seq(THEME, 0, 112, "mel", bar=4)[:-1]
    shape_vels(th, [118, 124, 112, 104, 110, 116])
    hn = S("horns", "horns", pan=-0.2, send=0.3, legato=0.05, lazy=-0.04, opts={"level": -16.5})
    hn.add(transpose(th, 12))
    trb = S("trombones", "trombone", pan=0.18, send=0.28, legato=0.05, lazy=-0.05, opts={"level": -17.5})
    trb.add(th)
    tpt = S("trumpets", "trumpet", pan=0.06, send=0.32, legato=0.04, lazy=-0.03, opts={"level": -19.0})
    tpt.add(transpose(th, 24, tag=""))
    for p_, part_ in ((("D4", "F4", "A4"), hn), (("D3", "A3", "F3"), trb), (("D5", "A5"), tpt)):
        part_.add([Note(8, 0.4, P(x), 127) for x in p_])
    for part_ in (hn, trb, tpt):
        part_.dyn = [(0, 116), (4, 112), (7.5, 124), (8, 127)]
    tuba = S("tuba", "tuba", pan=0.0, send=0.2, lazy=-0.05, humanize=0.0, opts={"level": -19.0})
    tuba.add(seq("D2:w | G1:h C2:q E2:q", 0, 116, bar=4))
    tuba.add([Note(8, 0.4, P("D1"), 127), Note(8, 0.4, P("D2"), 127)])
    vc = S("celli_ost", "vc", pan=0.2, send=0.22, humanize=0.004, lazy=-0.03, opts={"level": -19.0})
    vc.add(gallop(0, 4, P("D2")) + gallop(4, 6, P("G2")) + gallop(6, 7, P("C2")) + gallop(7, 8, P("E2")))
    vc.add([Note(8, 0.4, P("D2"), 127), Note(8, 0.4, P("D3"), 127)])
    vc.dyn = [(0, 110), (8, 127)]
    cbf = S("basses_ost", "cb_fast", pan=0.28, send=0.2, humanize=0.004, lazy=-0.04, opts={"level": -21.0})
    cbf.add([Note(n.beat, n.dur, n.pitch, n.vel) for n in vc.notes if n.vel >= 100 and n.beat < 8])
    cbf.add([Note(8, 0.4, P("D2"), 127)])
    cbf.dyn = [(0, 110), (8, 127)]
    vt = S("violins_trem", "vln_trem", pan=-0.3, send=0.35, humanize=0.0, opts={"level": -21.0})
    vt.add([Note(0, 4, P(p_), 110) for p_ in ("D5", "A5")] + [Note(4, 2, P(p_), 110) for p_ in ("D5", "Bb5")] +
           [Note(6, 2, P(p_), 112) for p_ in ("E5", "G5")])
    vt.add([Note(8, 0.4, P(p_), 127) for p_ in ("D5", "A5", "D6")])
    vt.dyn = [(0, 104), (6, 110), (7.9, 124), (8, 127)]
    ch = S("choir", "choir", pan=0.0, send=0.4, lazy=-0.18, legato=0.1, opts={"level": -20.0})
    cv = voice_chords(chords_[:4], 4, 50, 69, top_max=66)
    ch.add(pad_notes(chords_[:4], cv, {"c": [0, 1, 2, 3]}, 112)["c"])
    ch.add([Note(8, 0.4, P(p_), 127) for p_ in ("D3", "A3", "D4", "F4")])
    ch.dyn = [(0, 110), (8, 124)]
    tk = S("taiko", "taiko", pan=0.0, send=0.24, humanize=0.0, opts={"sat": 1.6, "level": -16.5})
    tkh = S("taiko_hi", "taiko", pan=-0.18, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -21.0})
    for b in range(8):
        (tk if b % 2 == 0 else tkh).add([Note(b, 1, P("C2") if b % 2 == 0 else P("A2"), 116 if b % 2 == 0 else 96)])
    tkh.add([Note(7.5, 0.5, P("A2"), 104), Note(7.75, 0.25, P("C3"), 110)])
    tk.add([Note(8, 1, P("C2"), 127)])
    tkh.add([Note(8, 1, P("F2"), 127)])
    boom = S("boom", "boom", synth=synth_boom, opts={"decay": 0.4, "slap": 0.15, "level": -18.0})
    boom.add([Note(0, 1, P("D1"), 127), Note(2, 1, P("D1"), 104), Note(4, 1, P("G1"), 116), Note(6, 1, P("C2"), 112)])
    bb = S("boom_button", "boom", synth=synth_boom, opts={"decay": 0.28, "slap": 0.3, "peak": -6.0})
    bb.add([Note(0, 1, P("D1"), 116), Note(8, 1, P("D1"), 127)])
    timp = S("timpani", "timpani", pan=0.14, send=0.26, humanize=0.0, opts={"sat": 1.6, "level": -20.0})
    timp.add([Note(0, 1, P("D2"), 124), Note(4, 1, P("G2"), 116), Note(6, 0.5, P("C3"), 112), Note(7, 0.5, P("E2"), 112)])
    timp.add(roll(P("A2"), 7.5, 7.98, tm, 16, 80, 120))
    timp.add([Note(8, 0.6, P("D2"), 127)])
    kit = S("cymbals", "kit", pan=0.08, send=0.3, humanize=0.0, opts={"sat": 1.6, "level": -23.0})
    kit.add([Note(0, 2, 49, 120), Note(0, 2, 57, 110), Note(8, 0.4, 49, 116), Note(8, 0.4, 38, 120)])
    sub = S("sub", "sub_pedal", synth=synth_sub_pedal, opts={"attack": 0.02, "release": 0.06, "release_end": 0.15,
                                                             "h2": 0.2, "level": -21.0})
    sub.add([Note(0, 4, P("D1"), 110), Note(4, 2, P("G1"), 104), Note(6, 1, P("C2"), 96), Note(7, 1, P("E1"), 100),
             Note(8, 0.4, P("D1"), 127)])
    for nm, f in (("horns", 80), ("trombones", 55), ("trumpets", 180), ("tuba", 25), ("celli_ost", 45),
                  ("basses_ost", 30), ("violins_trem", 180), ("choir", 100), ("taiko", 30), ("taiko_hi", 40),
                  ("timpani", 32), ("cymbals", 120)):
        S.parts[nm].eq = hpf(f)
    t_button = tm.sec(8)
    hits = [(0.0, "end_card"), (t_button, "button")]
    cue = Cue("endcard", tm, bars, chords_, S.list(), rt60=2.6, wet=0.3, predelay=0.025, target_lufs=-16.0,
              fade_in=0.0015, fade_out=0.2, send_hp=80.0, comp=(-8.0, 1.3, 20.0, 250.0),
              wet_duck=[(t_button + 0.22, 5.0, 0.06, 0.25)], gates=[(t_button + 0.3, 6.0, set(), 0.22)],
              master_vol=[(0, 0.0), (7.9, 0.5), (8, 2.0), (8.5, 2.0)], hits=hits,
              top_parts=("horns",), bass_parts=("tuba",))
    cue.notes_txt = compose_endcard.__doc__
    return cue


COMPOSERS = {"descent": compose_descent, "cavern": compose_cavern, "tension": compose_tension, "fall": compose_fall,
             "depths": compose_depths, "menace": compose_menace, "hermit": compose_hermit, "lull": compose_lull,
             "friend": compose_friend, "endcard": compose_endcard}


if __name__ == "__main__":
    ml.main(sys.argv[1:], COMPOSERS)
