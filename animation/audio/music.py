#!/usr/bin/env python3
"""music.py — render the film score from a cue sheet (MuseScore_General.sf2 via tinysoundfont).

    python3 audio/music.py data/music_cues.json out/music.wav [--lufs -18] [--seed 0] [--quiet]
                                                              [--cue-dir out/cues]   # also write each cue (debug)

CUE SHEET (times are seconds OR timeline anchors: 's05b03', 's05b03.end-0.4', 's07', 'film.end' ...)
{
  "timeline": "data/timeline.json",           # optional: anchors + dialogue (default data/timeline.json)
  "speech_from": "data/timeline.json",        # optional: dialogue = beats with kind == "line". DEFAULT: the
                                              #   timeline above, so melodies avoid dialogue even when omitted;
                                              #   false disables
  "speech": [[5.1, 7.09], ...],               # optional: extra dialogue intervals
  "duration": "film.end",                     # output length (s or anchor; default: timeline duration)
  "cues": [
    {"start": 0.0, "end": 13.6, "mood": "tender_memory", "intensity": 0.3,     # (or "from"/"to")
     "key": "D",          # optional tonic (C, C#, Db ... B). Mode comes from the mood. Default D.
     "bpm": 66,           # optional tempo override (moods default to 60-72)
     "fade_in": 0.8, "fade_out": 2.0,          # equal-power fades inside [start, end]
     "open_at": "s14b01", # reveal_wonder only: void sonority until here, then it opens
     "hits": [{"t": 9.0, "type": "swell", "len": 4.5}]}                        # (or "at")
  ]
}
data/music_plan.json (tools/resolve_music.py's input) can be rendered directly.
Moods: tender_memory, curious_unease, alarm_chaos, void_presence, confrontation, sorrow, stillness,
       dread, reveal_wonder, belonging, resolution, outro.
Hits:  swell   gentle crescendo over `len` s (default 4.5, 3..6): adds a strings (+choir/horns) swell layer,
               raises the cue level ~+3 dB and the local intensity (+0.25) for the rest of the cue
       sting   a soft-but-sudden accent, music continues: dark moods = timpani + low strings b9 cluster +
               low piano; bright moods = the current chord, warm (timpani on its root, strings, piano, a glint)
       drop    music falls to near silence (-26 dB) in 0.35 s; no new notes until the next hit
       silence holds nothing: fades to zero in 0.2 s; no notes until the next hit (reverb tail rings out)
       resolve cadence on the tonic exactly at t (dominant/plagal before it; a melodic phrase that ENDS
               on the tonic is placed if the dialogue leaves room); after t the tonic is held. Brings the
               level back up (0.3 s) after a drop/silence.
Melodic phrases (leitmotifs) are only placed in dialogue gaps, outside the cue's fades, never over another
cue's phrase and never more than ~12 % faster than the cue tempo; under speech the moods keep to pads, low
strings and occasional very soft high piano notes.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audiolib as A  # noqa: E402

SR = A.SR
SF2 = os.path.join(ROOT, "models", "MuseScore_General.sf2")

# ============================================================================================
# pitch helpers
PCS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
       "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11}


def midi(name):
    """'F#3' → 54 (C4 = 60)."""
    i = 2 if len(name) > 2 and name[1] in "#b" else 1
    return 12 * (int(name[i:]) + 1) + PCS[name[:i]]


def notes(s):
    return [midi(x) for x in s.split()]


def key_offset(key):
    """Semitones from D to the requested tonic, folded into -6..+5 so registers stay sensible."""
    if not key:
        return 0
    k = key.strip().replace("m", "") if key.strip() not in PCS else key.strip()
    k = k[0].upper() + k[1:]
    off = (PCS[k] - 2) % 12
    return off - 12 if off > 5 else off


# ============================================================================================
# instruments  (prog = General MIDI preset in MuseScore_General.sf2, bank 0)
#   cal: reference key for loudness calibration;  perc: decaying instrument (calibrate on the attack)
#   send: reverb send;  bus: 'hall' or 'vast' (long dark reverb);  width: mono→stereo spread 0..0.5
#   level: dB trim after calibration (sets the orchestral balance: the felt piano and solo lines sit on top)
INSTR = {
    "piano":    dict(level=9, prog=0,  cal=62, perc=True, vmax=70, pan=-0.10, send=0.30, bus="hall", width=0.0,
                     eq=[("hp", 40), ("lp", 3300), ("ls", 220, 2.0), ("peak", 900, -1.5, 0.8)]),
    "pad":      dict(level=-3, prog=89, cal=62, pan=0.0, send=0.30, bus="hall", width=0.35, eq=[("hp", 70), ("lp", 2800)]),
    "darkpad":  dict(level=0, prog=89, cal=50, pan=0.0, send=0.45, bus="vast", width=0.4, eq=[("hp", 32), ("lp", 650)]),
    "strings":  dict(level=-1.5, prog=49, cal=62, pan=0.04, send=0.34, bus="hall", width=0.2,
                     eq=[("hp", 55), ("lp", 5200), ("peak", 2800, -2.5, 1.0)]),
    "lowstr":   dict(level=0, prog=49, cal=43, pan=-0.04, send=0.32, bus="hall", width=0.2, eq=[("hp", 30), ("lp", 1500)]),
    "strfast":  dict(level=0, prog=48, cal=45, pan=0.0, send=0.22, bus="hall", width=0.15, eq=[("hp", 38), ("lp", 2200)]),
    "tremolo":  dict(level=0, prog=44, cal=62, pan=0.12, send=0.32, bus="hall", width=0.2, eq=[("hp", 110), ("lp", 2600)]),
    "pizz":     dict(level=2, prog=45, cal=50, perc=True, pan=-0.22, send=0.30, bus="hall", width=0.0, eq=[("hp", 50), ("lp", 4000)]),
    "cello":    dict(level=5, prog=42, cal=50, pan=-0.16, send=0.34, bus="hall", width=0.1, eq=[("hp", 55), ("lp", 4200), ("peak", 2500, -2, 1)]),
    "viola":    dict(level=3, prog=41, cal=57, pan=0.20, send=0.34, bus="hall", width=0.1, eq=[("hp", 90), ("lp", 4500)]),
    "celesta":  dict(level=3, prog=8,  cal=86, perc=True, pan=0.28, send=0.50, bus="vast", width=0.0, eq=[("hp", 300), ("lp", 9000)]),
    "musicbox": dict(level=3, prog=10, cal=81, perc=True, pan=0.18, send=0.45, bus="hall", width=0.0, eq=[("hp", 260), ("lp", 8000)]),
    "harp":     dict(level=7, prog=46, cal=62, perc=True, pan=-0.28, send=0.42, bus="vast", width=0.0, eq=[("hp", 70), ("lp", 7000)]),
    "choir":    dict(level=-2.5, prog=52, cal=69, pan=0.0, send=0.55, bus="vast", width=0.25, eq=[("hp", 160), ("lp", 5200)]),
    "glass":    dict(level=2, prog=92, cal=81, pan=0.0, send=0.55, bus="vast", width=0.45, eq=[("hp", 220), ("lp", 6500)]),
    "timpani":  dict(level=-2, prog=47, cal=38, perc=True, pan=0.0, send=0.35, bus="hall", width=0.0, eq=[("hp", 28), ("lp", 1100)]),
    "horns":    dict(level=0, prog=60, cal=50, pan=0.10, send=0.42, bus="hall", width=0.15, eq=[("hp", 45), ("lp", 2000)]),
    "space":    dict(level=0, prog=91, cal=62, pan=0.0, send=0.55, bus="vast", width=0.45, eq=[("hp", 150), ("lp", 3000)]),
}

# ============================================================================================
# harmony  — every voicing is written in D (tonic D) and transposed per cue.
#   b = bass, p = pad/inner voicing, a = broken-chord (piano LH / harp), u = upper tones (celesta, choir, pings)
_CH = {
    # D major family
    "D":         ("D2",  "A3 D4 F#4",      "D2 A2 D3 F#3",   "D5 F#5 A5"),
    "Dadd9":     ("D2",  "A3 D4 E4 F#4",   "D2 A2 E3 F#3",   "A4 D5 E5 F#5"),
    "Dmaj9":     ("D2",  "F#3 A3 C#4 E4",  "D2 A2 E3 F#3",   "A4 C#5 E5 F#5"),
    "D/F#":      ("F#2", "A3 D4 F#4",      "F#2 A2 D3 F#3",  "D5 F#5 A5"),
    "D/A":       ("A1",  "A3 D4 F#4",      "A1 A2 D3 F#3",   "D5 F#5 A5"),
    "A":         ("A1",  "A3 C#4 E4",      "A1 E2 A2 C#3",   "A4 C#5 E5"),
    "A/C#":      ("C#2", "A3 C#4 E4",      "C#2 A2 C#3 E3",  "A4 C#5 E5"),
    "Asus4":     ("A1",  "A3 D4 E4",       "A1 E2 A2 D3",    "A4 D5 E5"),
    "A7":        ("A1",  "G3 C#4 E4",      "A1 E2 G2 C#3",   "G4 A4 C#5 E5"),
    "A7sus4":    ("A1",  "G3 A3 D4 E4",    "A1 E2 G2 D3",    "G4 A4 D5 E5"),
    "Bm7":       ("B1",  "A3 B3 D4 F#4",   "B1 F#2 A2 D3",   "B4 D5 F#5 A5"),
    "Bm(add9)":  ("B1",  "B3 C#4 D4 F#4",  "B1 F#2 C#3 D3",  "B4 C#5 D5 F#5"),
    "Gmaj7":     ("G1",  "B3 D4 F#4",      "G1 D2 B2 F#3",   "B4 D5 F#5"),
    "Gadd9":     ("G1",  "A3 B3 D4",       "G1 D2 A2 B2",    "G4 A4 B4 D5"),
    "Gmaj7#11":  ("G1",  "B3 C#4 F#4",     "G1 D2 B2 F#3",   "B4 C#5 D5 F#5"),
    "G/D":       ("D2",  "B3 D4 G4",       "D2 G2 B2 D3",    "G4 B4 D5"),
    "Gadd9/D":   ("D2",  "A3 B3 D4 G4",    "D2 G2 A2 B2",    "G4 A4 B4 D5"),
    "Em7":       ("E2",  "G3 B3 D4",       "E2 B2 D3 G3",    "E5 G5 B5"),
    "E/D":       ("D2",  "G#3 B3 E4",      "D2 E3 G#3 B3",   "E5 G#5 B5"),
    # D minor family
    "Dm":        ("D2",  "A3 D4 F4",       "D2 A2 D3 F3",    "D5 F5 A5"),
    "Dm(add9)":  ("D2",  "A3 D4 E4 F4",    "D2 A2 E3 F3",    "D5 E5 F5 A5"),
    "Dm9":       ("D2",  "F3 A3 C4 E4",    "D2 A2 C3 E3",    "F5 A5 C6 E6"),
    "Dm/C":      ("C2",  "A3 D4 F4",       "C2 A2 D3 F3",    "D5 F5 A5"),
    "Dm/F":      ("F2",  "A3 D4 F4",       "F2 A2 D3 F3",    "D5 F5 A5"),
    "Dm/A":      ("A1",  "A3 D4 F4",       "A1 A2 D3 F3",    "D5 F5 A5"),
    "Bb":        ("Bb1", "Bb3 D4 F4",      "Bb1 F2 Bb2 D3",  "Bb4 D5 F5"),
    "Bbmaj7":    ("Bb1", "A3 D4 F4",       "Bb1 F2 A2 D3",   "Bb4 D5 F5 A5"),
    "Bbmaj7#11": ("Bb1", "A3 D4 E4",       "Bb1 F2 A2 D3",   "A4 D5 E5 F5"),
    "F":         ("F2",  "A3 C4 F4",       "F2 C3 F3 A3",    "F5 A5 C6"),
    "F/A":       ("A1",  "A3 C4 F4",       "A1 F2 C3 F3",    "F5 A5 C6"),
    "Gm":        ("G1",  "Bb3 D4 G4",      "G1 D2 G2 Bb2",   "G4 Bb4 D5"),
    "Gm7":       ("G1",  "F3 Bb3 D4",      "G1 D2 F2 Bb2",   "G4 Bb4 D5 F5"),
    "Gm(add9)":  ("G1",  "A3 Bb3 D4",      "G1 D2 A2 Bb2",   "G4 A4 Bb4 D5"),
    "Gm6":       ("G1",  "Bb3 D4 E4",      "G1 D2 Bb2 E3",   "G4 Bb4 D5 E5"),
    "Gm/Bb":     ("Bb1", "Bb3 D4 G4",      "Bb1 G2 D3 G3",   "G4 Bb4 D5"),
    "A7b9":      ("A1",  "G3 Bb3 C#4 E4",  "A1 E2 G2 C#3",   "G4 Bb4 C#5 E5"),
    # the VOID sonority: low open fifths (u = bowed-glass fifth far above)
    "V5":        ("D1",  "D2 A2 D3",       "D2 A2",          "A4 E5"),
    "V5e":       ("D1",  "D2 A2 E3",       "D2 A2",          "A4 E5"),
    "V5f":       ("D1",  "D2 A2 F3",       "D2 A2",          "A4 D5"),
    # alarm pedal chords over D
    "P_m":       ("D2",  "A3 D4 F4",       "D2 D3",          "A4 D5"),
    "P_b6":      ("D2",  "Bb3 D4 F4",      "D2 D3",          "Bb4 D5"),
    "P_N":       ("D2",  "Bb3 Eb4 G4",     "D2 D3",          "G4 Bb4"),
    "P_V":       ("D2",  "A3 C#4 G4",      "D2 D3",          "G4 A4"),
    # dread: held dissonance over a D pedal
    "DR1":       ("D2",  "A2 D3 Eb3",      "D2 A2",          "A4 Bb4"),
    "DR2":       ("D2",  "Ab2 D3 F3",      "D2 Ab2",         "E5 F5"),
}
CH = {k: dict(b=notes(v[0]), p=notes(v[1]), a=notes(v[2]), u=notes(v[3])) for k, v in _CH.items()}

# ============================================================================================
# leitmotifs and phrases — (onset_beats, dur_beats, note) written in D; `ch` = harmonisation (beat, chord)
#   FEAR MOTIF = scale degrees 3-2-3 . 5 (hesitant: two quick notes, a lean, a breath, a reach up)
PHRASES = {
    # opening "memory" theme (major; its middle 3-2-3 quietly foreshadows Fear's motif)
    "memory":        dict(n=[(0, 1, "A4"), (1, .5, "F#4"), (1.5, .5, "E4"), (2, 1.5, "F#4"), (3.5, .5, "D4"), (4, 3, "E4")],
                          ch=[(0, "Dadd9"), (2, "Bm7"), (4, "Gmaj7")]),
    "memory_short":  dict(n=[(0, 1, "A4"), (1, .5, "F#4"), (1.5, 2.5, "E4")], ch=[(0, "Dadd9")]),
    # Fear, fragile, minor
    "fear_minor":    dict(n=[(0, .5, "F4"), (.5, .5, "E4"), (1, 1.25, "F4"), (2.5, 2.5, "A4")],
                          ch=[(0, "Dm(add9)"), (2.5, "Bbmaj7")]),
    "fear_minor_short": dict(n=[(0, .5, "F4"), (.5, .5, "E4"), (1, 2, "F4")], ch=[(0, "Dm(add9)")]),
    # Fear, questioning: reaches up to the (dorian) 6th and hangs there over IV — unresolved
    "fear_question": dict(n=[(0, .5, "F4"), (.5, .5, "E4"), (1, 1.25, "F4"), (2.5, 1, "A4"), (3.5, 2.5, "B4")],
                          ch=[(0, "Dm(add9)"), (2.5, "F"), (3.5, "Gadd9")]),
    "fear_question_short": dict(n=[(0, .5, "F4"), (.5, .5, "E4"), (1, 1, "F4"), (2, 2, "A4")],
                                ch=[(0, "Dm(add9)"), (2, "F")]),
    # Fear, hopeful (major, open ending on 5)
    "fear_hope":     dict(n=[(0, .5, "F#4"), (.5, .5, "E4"), (1, 1, "F#4"), (2, 1, "A4"), (3, 1, "B4"), (4, 2.5, "A4")],
                          ch=[(0, "D"), (2, "Bm7"), (3, "Gadd9")]),
    "fear_hope_short": dict(n=[(0, .5, "F#4"), (.5, .5, "E4"), (1, 1, "F#4"), (2, 2, "A4")], ch=[(0, "D"), (2, "Bm7")]),
    # Fear, resolved: 3-2-3-5 | 4-3-2-1 over a cadential 6/4 — warm, home
    "fear_resolved": dict(n=[(0, .5, "F#4"), (.5, .5, "E4"), (1, 1, "F#4"), (2, 1, "A4"), (3, 1, "G4"), (4, .5, "F#4"),
                             (4.5, .5, "E4"), (5, 3, "D4")],
                          ch=[(0, "Dadd9"), (2, "Bm7"), (3, "Gmaj7"), (4, "D/A"), (4.5, "A7"), (5, "Dadd9")]),
    "fear_resolved_short": dict(n=[(0, .5, "F#4"), (.5, .5, "E4"), (1, 2.5, "D4")], ch=[(0, "Gadd9/D"), (1, "Dadd9")]),
    # Fear, in wonder (lydian: the raised 4th glows and lifts to 5)
    "wonder":        dict(n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1, "F#5"), (2, 1, "A5"), (3, 1.5, "G#5"), (4.5, 2.5, "A5")],
                          ch=[(0, "Dmaj9"), (3, "E/D"), (4.5, "Dmaj9")]),
    "wonder_short":  dict(n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1, "F#5"), (2, 2, "A5")], ch=[(0, "Dmaj9"), (2, "E/D")]),
    # sorrow: falling lament 5-4-3-2-1 (cello)
    "lament":        dict(n=[(0, 1.5, "A4"), (1.5, .5, "G4"), (2, 1, "F4"), (3, 1, "E4"), (4, 2.5, "D4")],
                          ch=[(0, "Dm"), (2, "Bbmaj7"), (3, "A7sus4"), (4, "Dm")]),
}

# rhythmic patterns: (beat position, chord-tone index, velocity multiplier)
PAT = {
    "arp_h": [(0, 0, 1.0), (2, 2, 0.8)],
    "arp_q": [(0, 0, 1.0), (1, 1, 0.75), (2, 2, 0.85), (3, 3, 0.72)],
    "arp_e": [(0, 0, 1.0), (.5, 1, .66), (1, 2, .78), (1.5, 3, .66), (2, 4, .82), (2.5, 3, .64), (3, 2, .74), (3.5, 1, .6)],
    "bass1": [(0, 0, 1.0)],
    "tiptoe": [(0, 0, 1.0), (1.5, 1, .7), (2.5, 0, .78), (3.5, 1, .6)],
    "osti": [(0, 0, 1.0), (.5, 0, .55), (1, 1, .8), (1.5, 0, .95), (2, 0, .55), (2.5, 1, .8), (3, 0, .95), (3.5, 1, .7)],
}

# ============================================================================================
# moods: tempo, mode, progression (chord, beats), cadence before a resolve, tonic hold after it.
MOODS = {
    "tender_memory": dict(bpm=66, prog=[("Dadd9", 4), ("Bm7", 4), ("Gmaj7", 4), ("Asus4", 2), ("A", 2),
                                        ("D/F#", 4), ("Gadd9", 4), ("Em7", 4), ("A7sus4", 4)],
                          cadence=[("Gadd9", 2), ("A7sus4", 2)], tonic=[("Dadd9", 4), ("Gadd9/D", 4)],
                          phrases=["memory", "memory_short"], phrase_stem="piano", resolve_phrase="fear_resolved_short"),
    "curious_unease": dict(bpm=62, prog=[("Dm(add9)", 4), ("Bbmaj7#11", 4), ("Gm6", 4), ("A7sus4", 2), ("A7b9", 2),
                                         ("Dm/C", 4), ("Bbmaj7", 4), ("Gm(add9)", 4), ("Asus4", 4)],
                           cadence=[("Gm6", 2), ("A7sus4", 2)], tonic=[("Dm(add9)", 8)],
                           phrases=["fear_minor", "fear_minor_short"], phrase_stem="musicbox", phrase_oct=12),
    "alarm_chaos": dict(bpm=72, prog=[("P_m", 4), ("P_b6", 4), ("P_N", 4), ("P_V", 4)],
                        cadence=[("P_V", 4)], tonic=[("P_m", 8)], phrases=[]),
    "void_presence": dict(bpm=60, prog=[("V5", 8), ("V5e", 8), ("V5", 8), ("V5f", 8)],
                          cadence=[("V5f", 4)], tonic=[("V5e", 8)], phrases=[]),
    "confrontation": dict(bpm=66, prog=[("Dm(add9)", 4), ("Bbmaj7", 4), ("F/A", 4), ("Gm7", 4), ("Dm/F", 4),
                                        ("Gm(add9)", 4), ("Asus4", 2), ("A", 2), ("Dm", 4)],
                          cadence=[("Gm(add9)", 2), ("A7sus4", 2)], tonic=[("Dm(add9)", 8)],
                          phrases=["fear_question", "fear_question_short"], phrase_stem="piano"),
    "sorrow": dict(bpm=60, prog=[("Dm", 4), ("Dm/C", 4), ("Bbmaj7", 4), ("A7sus4", 2), ("A", 2), ("Gm/Bb", 4),
                                 ("Dm/A", 4), ("Gm6", 4), ("Asus4", 2), ("A7", 2)],
                   cadence=[("Gm6", 2), ("A7", 2)], tonic=[("Dm", 8)],
                   phrases=["lament", "fear_minor", "fear_minor_short"], phrase_stem="cello", phrase_oct=-12),
    "stillness": dict(bpm=60, prog=[("V5", 16)], cadence=[], tonic=[("Dadd9", 8)], phrases=[]),
    "dread": dict(bpm=60, prog=[("DR1", 16), ("DR2", 8), ("DR1", 8)], cadence=[("DR2", 4)], tonic=[("DR1", 8)],
                  phrases=[]),
    "reveal_wonder": dict(bpm=64, prog=[("Dmaj9", 4), ("E/D", 4), ("Dmaj9", 4), ("E/D", 4), ("Bm(add9)", 4),
                                        ("Gmaj7#11", 4), ("Asus4", 2), ("A", 2), ("Dmaj9", 4)],
                          cadence=[("Gmaj7#11", 2), ("A", 2)], tonic=[("Dmaj9", 4), ("E/D", 4)],
                          phrases=["wonder", "wonder_short"], phrase_stem="celesta"),
    "belonging": dict(bpm=66, prog=[("D", 4), ("A/C#", 4), ("Bm7", 4), ("Gmaj7", 4), ("D/F#", 4), ("Gadd9", 4),
                                    ("Em7", 4), ("A7sus4", 2), ("A", 2)],
                      cadence=[("Gadd9", 2), ("A7sus4", 2)], tonic=[("D", 4), ("Gadd9/D", 4)],
                      phrases=["fear_hope", "fear_hope_short"], phrase_stem="piano", resolve_phrase="fear_resolved"),
    "resolution": dict(bpm=63, prog=[("Dadd9", 4), ("G/D", 4), ("Dadd9", 4), ("Gadd9/D", 4), ("Bm7", 4), ("Gmaj7", 4),
                                     ("Asus4", 2), ("A", 2), ("Dadd9", 4)],
                       cadence=[("Gadd9", 2), ("A7sus4", 2)], tonic=[("Dadd9", 4), ("Gadd9/D", 4)],
                       phrases=["fear_resolved", "fear_resolved_short"], phrase_stem="piano", resolve_phrase="fear_resolved"),
    "outro": dict(bpm=60, prog=[("Dadd9", 4), ("Gmaj7", 4), ("Bm7", 4), ("A7sus4", 2), ("A", 2)],
                  cadence=[("D/A", 2), ("A7", 2)], tonic=[("Dadd9", 8)],
                  phrases=["fear_resolved", "fear_resolved_short"], phrase_stem="piano", resolve_phrase="fear_resolved"),
}

# ============================================================================================
# time anchors (same syntax as src/timeline.mjs): 12.5 | 's05b03' | 's05b03.end' | 's05b03.mid' |
# 's05b03+1.2' | 's05b03.end-0.4' | 's07' (scene start) | 's07.end' | 'film.end'
import re  # noqa: E402

_ANCHOR = re.compile(r"^([A-Za-z0-9_]+)(\.(start|end|mid))?([+-][0-9.]+)?$")


class Anchors:
    def __init__(self, timeline=None):
        self.beats, self.scenes, self.duration = {}, {}, None
        if timeline:
            beats = timeline.get("beats", {})
            items = beats.items() if isinstance(beats, dict) else [(b[0], b[1]) if isinstance(b, list) else (b.get("id"), b) for b in beats]
            self.beats = {k: v for k, v in items}
            self.scenes = {sc["id"]: sc for sc in timeline.get("scenes", [])}
            self.duration = timeline.get("duration")

    def __call__(self, v):
        if isinstance(v, (int, float)):
            return float(v)
        m = _ANCHOR.match(str(v).strip())
        if not m:
            raise SystemExit(f"[music] bad time/anchor: {v!r}")
        bid, which, off = m.group(1), m.group(3) or "start", m.group(4)
        if bid == "film":
            if self.duration is None:
                raise SystemExit("[music] 'film' anchor needs a timeline")
            rec = {"start": 0.0, "end": float(self.duration)}
        else:
            rec = self.beats.get(bid) or self.scenes.get(bid)
        if rec is None:
            raise SystemExit(f"[music] unknown anchor id {bid!r} in {v!r} (not a beat/scene of the timeline)")
        a, b = float(rec["start"]), float(rec["end"])
        base = b if which == "end" else (a + b) / 2 if which == "mid" else a
        return base + (float(off) if off else 0.0)


def _field(d, *names):
    for k in names:
        if k in d:
            return d[k]
    raise SystemExit(f"[music] missing field {names[0]!r} in {d}")


def resolve_sheet(sheet, anchors):
    """Copy of the cue sheet with every time field resolved to absolute seconds.
    Accepts the plan spelling too (data/music_plan.json): cue `from`/`to` for `start`/`end`, hit `at` for `t`."""
    out = dict(sheet)
    if "duration" in sheet:
        out["duration"] = anchors(sheet["duration"])
    elif anchors.duration is not None:
        out["duration"] = float(anchors.duration)
    else:
        raise SystemExit("[music] the cue sheet needs a 'duration' (or a timeline to take it from)")
    cues = []
    for c in sheet["cues"]:
        c2 = dict(c)
        c2["start"] = max(0.0, anchors(_field(c, "start", "from")))
        c2["end"] = min(out["duration"], anchors(_field(c, "end", "to")))
        c2["hits"] = [dict(h, t=anchors(_field(h, "t", "at"))) for h in c.get("hits", [])]
        if c.get("open_at") is not None:
            c2["open_at"] = anchors(c["open_at"])
        cues.append(c2)
    out["cues"] = cues
    return out


# ============================================================================================
# synth engine


class Synth:
    def __init__(self, sf2=SF2):
        import tinysoundfont as tsf
        self.syn = tsf.Synth(samplerate=SR, gain=0)
        self.sfid = self.syn.sfload(sf2)
        self.cal = {}

    def render(self, prog, events, n, bank=0):
        """events: list of (sample_index, is_on, key, vel) — rendered sample-accurately in blocks."""
        s = self.syn
        s.sounds_off()
        s.generate(4096)  # let any quick-release voices from the previous stem die away
        s.program_select(0, self.sfid, bank, prog)
        s.pitchbend(0, 8192)
        out = np.zeros((n, 2), dtype=np.float32)
        pos = 0
        for idx, on, key, vel in sorted(events, key=lambda e: (e[0], e[1])):  # offs before ons
            idx = int(min(max(idx, 0), n))
            if idx > pos:
                out[pos:idx] = np.frombuffer(s.generate(idx - pos), dtype=np.float32).reshape(-1, 2)
                pos = idx
            if on:
                s.noteon(0, int(key), int(max(1, min(127, vel))))
            else:
                s.noteoff(0, int(key))
        if pos < n:
            out[pos:] = np.frombuffer(s.generate(n - pos), dtype=np.float32).reshape(-1, 2)
        s.notes_off()
        s.sounds_off()
        return out

    def calibration(self, name):
        """Linear gain that brings a vel-64 reference note (after the stem EQ) to -24 dBFS RMS."""
        if name not in self.cal:
            ins = INSTR[name]
            n = int(1.6 * SR)
            ev = [(0, True, ins["cal"], 64), (int(1.2 * SR), False, ins["cal"], 0)]
            x = A.eq_chain(self.render(ins["prog"], ev, n), ins["eq"])
            seg = x[: int(0.5 * SR)] if ins.get("perc") else x[int(0.4 * SR): int(1.2 * SR)]
            rms = float(np.sqrt(np.mean(seg ** 2)) + 1e-9)
            self.cal[name] = float(A.db2lin(-24.0)) / rms
        return self.cal[name]


# ============================================================================================
# cue model


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


class Cue:
    def __init__(self, spec, idx, speech_abs, seed=0):
        self.spec = spec
        self.idx = idx
        self.start = float(spec["start"])
        self.end = float(spec["end"])
        self.D = self.end - self.start
        self.mood = spec["mood"]
        if self.mood not in MOODS:
            raise SystemExit(f"unknown mood '{self.mood}' (choose from {', '.join(MOODS)})")
        self.M = MOODS[self.mood]
        self.I = float(np.clip(spec.get("intensity", 0.4), 0.0, 1.0))
        self.koff = key_offset(spec.get("key", "D"))
        self.bpm = float(spec.get("bpm", self.M["bpm"]))
        self.beat = 60.0 / self.bpm
        self.fade_in = max(0.02, float(spec.get("fade_in", 1.5)))
        self.fade_out = max(0.05, float(spec.get("fade_out", 2.0)))
        hits = []
        for h in spec.get("hits", []):
            t = float(h["t"]) - self.start
            if -1e-6 <= t < self.D:
                hits.append((max(0.0, t), h["type"], h))
        self.hits = sorted(hits, key=lambda h: h[0])
        self.speech = [(a - self.start, b - self.start) for a, b in speech_abs if b > self.start and a < self.end]
        self.has_speech_info = speech_abs is not None and len(speech_abs) > 0
        self.rng = np.random.default_rng(1009 * (idx + 1) + 7919 * seed + sum(map(ord, self.mood)))
        self.muted = []      # (a, b) local: no new note-ons
        self.phrase_iv = []  # (a, b) local: where a melodic phrase is sounding
        self.blocked = []    # (a, b) local: phrases of other (overlapping) cues — no melody here
        # reveal_wonder: the void sonority holds until open_at, then opens (local seconds)
        oa = spec.get("open_at")
        self.open_at = (float(oa) - self.start) if oa is not None and 0.5 < float(oa) - self.start < self.D else None
        self.phrase_from = 0.0  # no melodic phrase starts before this (local s)
        self.swells = [(t, float(h.get("len", 4.5))) for t, ty, h in self.hits if ty == "swell"]
        self.resolves = [t for t, ty, h in self.hits if ty == "resolve"]
        # melodic material (cue may override the mood's defaults)
        self.phrases = list(spec.get("phrases", self.M.get("phrases", [])))
        self.phrase_seq = spec.get("phrase_seq")
        self.phrase_stem = spec.get("phrase_stem", self.M.get("phrase_stem", "piano"))
        self.phrase_oct = int(spec.get("phrase_oct", self.M.get("phrase_oct", 0)))

    # ---- queries
    def speech_at(self, t, pre=0.25, post=0.12):
        for a, b in self.speech:
            if a - pre <= t <= b + post:
                return True
        return False

    def speech_in(self, t0, t1, pre=0.25, post=0.12):
        for a, b in self.speech:
            if a - pre < t1 and b + post > t0:
                return True
        return False

    def is_muted(self, t):
        return any(a - 1e-6 <= t < b for a, b in self.muted)

    def after_resolve(self, t, rest):
        return any(r - 0.05 <= t < r + rest for r in self.resolves)

    def in_phrase(self, t, pad=0.15):
        return any(a - pad <= t <= b + pad for a, b in self.phrase_iv)

    def I_at(self, t):
        v = self.I
        for ts, ln in self.swells:
            v += 0.25 * float(_smooth((t - ts) / max(ln, 0.1)))
        return float(min(1.0, v))

    def gaps(self, lead=0.9, tail=0.7, pre=0.3, post=0.2):
        """Speech-free, unmuted intervals inside the cue (local seconds). Melodies also stay out of the
        cue's fade-in / fade-out (where a neighbouring cue is crossfading) and away from other cues' phrases."""
        lo = max(lead, 0.7 * self.fade_in, self.phrase_from)
        hi = self.D - max(tail, self.fade_out)
        if hi <= lo:
            return []
        blocks = ([(a - pre, b + post) for a, b in self.speech] + list(self.muted)
                  + [(a - pre, b + 0.3) for a, b in self.blocked])
        blocks.sort()
        out, cur = [], lo
        for a, b in blocks:
            if b <= cur:
                continue
            if a > cur:
                out.append((cur, min(a, hi)))
            cur = max(cur, b)
            if cur >= hi:
                break
        if cur < hi:
            out.append((cur, hi))
        return [(a, b) for a, b in out if b - a > 0.3]


class Writer:
    """Collects notes for one cue; handles transposition, humanisation, muting and intensity."""

    def __init__(self, cue):
        self.cue = cue
        self.notes = []   # (stem, t, dur, key, vel)
        self.auto = {}    # stem → [(t, dB), ...] gain automation (piecewise linear in dB)

    def add(self, stem, t, dur, key, vel, jitter=0.008, transpose=True, force=False):
        c = self.cue
        if not force and (t < 0 or t >= c.D - 0.2 or c.is_muted(t)):
            return
        if jitter:
            t = max(0.0, t + float(np.clip(c.rng.normal(0, jitter), -2.5 * jitter, 2.5 * jitter)))
            vel = vel + float(c.rng.integers(-3, 4))
        k = key + (c.koff if transpose else 0)
        while k < 23:
            k += 12
        while k > 108:
            k -= 12
        base = stem.split("#")[0]
        vmax = INSTR[base].get("vmax", 110)
        v = int(np.clip(round(vel), 1, vmax))
        self.notes.append((stem, float(t), float(max(0.05, dur)), int(k), v))

    def vel(self, base, t, lo=0.55, hi=0.9):
        """Scale a base velocity (written for intensity 0.5) by the local intensity."""
        i = self.cue.I_at(t)
        return base * (lo + hi * i) / (lo + hi * 0.5)


# ============================================================================================
# form: segments → harmony timeline + bar grid


def build_form(cue):
    M = cue.M
    bounds = [(0.0, "start", {})] + [(t, ty, h) for t, ty, h in cue.hits]
    if cue.open_at is not None:  # reveal: the progression starts afresh (on a downbeat) where the void opens
        bounds.append((cue.open_at, "open", {}))
        bounds.sort(key=lambda b: b[0])
    segs = []
    for i, (t, ty, h) in enumerate(bounds):
        t1 = bounds[i + 1][0] if i + 1 < len(bounds) else cue.D
        if t1 - t > 1e-3:
            segs.append(dict(t0=t, t1=t1, kind=ty, hit=h))
    for s in segs:
        if s["kind"] in ("drop", "silence"):
            cue.muted.append((s["t0"], s["t1"]))
    harm, grid = [], []
    prog, pi = M["prog"], 0
    bar_beats = 4
    for si, s in enumerate(segs):
        t0, t1, kind = s["t0"], s["t1"], s["kind"]
        nxt = segs[si + 1] if si + 1 < len(segs) else None
        if kind == "silence":
            continue
        if kind == "drop":
            last = harm[-1][2] if harm else M["tonic"][0][0]
            harm.append([t0, t1, last])
            continue
        if kind == "open":
            pi = 0
        L = t1 - t0
        nb = max(1, int(round(L / (bar_beats * cue.beat))))
        beat = L / (nb * bar_beats)
        if not (0.9 * cue.beat <= beat <= 1.12 * cue.beat):
            beat = cue.beat
            nb = int(math.ceil(L / (bar_beats * beat) - 1e-6))
        for k in range(nb):
            bt = t0 + k * bar_beats * beat
            if bt < t1 - 0.05:
                grid.append((bt, beat, bar_beats, kind))
        # chords
        if kind == "resolve":
            seq = list(M["tonic"])
            items = [seq[i % len(seq)] for i in range(64)]
        else:
            items = [prog[(pi + i) % len(prog)] for i in range(256)]
        cad = M["cadence"] if (nxt is not None and nxt["kind"] == "resolve" and M["cadence"]) else []
        cad_beats = sum(b for _, b in cad)
        cad_start = t1 - cad_beats * beat if cad else t1
        if cad and cad_start < t0 + 0.5 * beat:
            cad_start = t0
        t = t0
        used = 0
        while t < cad_start - 1e-6:
            ch, nbt = items[used]
            used += 1
            d = nbt * beat
            harm.append([t, min(t + d, cad_start), ch])
            t += d
        if kind != "resolve":
            pi = (pi + used) % len(prog)
        if cad:
            # fit the cadence into what is left
            left = t1 - cad_start
            scale = left / (cad_beats * beat) if cad_beats else 1
            tt = cad_start
            for ch, nbt in cad:
                d = nbt * beat * scale
                harm.append([tt, tt + d, ch])
                tt += d
    # merge identical neighbours
    merged = []
    for h in harm:
        if merged and merged[-1][2] == h[2] and abs(merged[-1][1] - h[0]) < 1e-6:
            merged[-1][1] = h[1]
        else:
            merged.append(list(h))
    return segs, merged, grid


def chord_at(harm, t):
    for a, b, c in harm:
        if a - 1e-6 <= t < b:
            return c
    return None


def patch_harmony(harm, t0, t1, chords):
    """Replace harmony in [t0, t1) by `chords` [(t, name)], snapping tiny leftovers."""
    # pull the start back to a chord boundary that is very close
    for a, b, c in harm:
        if 0 < t0 - a < 0.5 and a <= t0 < b:
            chords = [(a, chords[0][1])] + [(t, n) for t, n in chords[1:]]
            t0 = a
            break
    for a, b, c in harm:
        if a < t1 < b and b - t1 < 0.8:
            t1 = b
            break
    out = []
    for a, b, c in harm:
        if b <= t0 or a >= t1:
            out.append([a, b, c])
        else:
            if a < t0:
                out.append([a, t0, c])
            if b > t1:
                out.append([t1, b, c])
    for i, (t, n) in enumerate(chords):
        te = chords[i + 1][0] if i + 1 < len(chords) else t1
        if te > t:
            out.append([t, te, n])
    out.sort(key=lambda h: h[0])
    merged = []
    for h in out:
        if merged and merged[-1][2] == h[2] and abs(merged[-1][1] - h[0]) < 1e-6:
            merged[-1][1] = h[1]
        else:
            merged.append(h)
    harm[:] = merged


# ============================================================================================
# texture helpers


def pad_layer(w, harm, stem, src="p", vel=40, octave=0, sel=None, overlap=0.15, stagger=0.035, min_I=0.0,
              tie=True, vel_lo=0.55, vel_hi=0.9):
    """Sustained chords; common tones are tied across chord changes (smooth voice-leading)."""
    cue = w.cue
    active = {}  # key → (t_start, vel)
    prev_end = None
    for a, b, ch in harm:
        if ch is None:
            continue
        if cue.I_at(a) < min_I:
            keys = set()
        else:
            ks = CH[ch][src] if isinstance(src, str) else src(CH[ch])
            if sel is not None:
                ks = sel(ks)
            keys = set(k + 12 * octave for k in ks)
        gap = prev_end is not None and a - prev_end > 1e-3
        for k in list(active):
            if k not in keys or gap or not tie:
                s0, v0 = active.pop(k)
                end = (prev_end if gap else a) + overlap
                w.add(stem, s0, end - s0, k, v0, jitter=0, force=True)
        for j, k in enumerate(sorted(keys)):
            if k not in active and not cue.is_muted(a):
                active[k] = (a + j * stagger * float(cue.rng.random()), w.vel(vel, a, vel_lo, vel_hi))
        prev_end = b
    for k, (s0, v0) in active.items():
        w.add(stem, s0, (prev_end or s0) + overlap - s0, k, v0, jitter=0, force=True)


def pattern_layer(w, grid, harm, stem, pattern, src="a", vel=40, dur=2.0, octave=0, speech="thin", thin=(0,),
                  min_I=0.0, every=1, skip_phrase=False, vel_lo=0.55, vel_hi=0.9, max_t=None, resolve_rest=2.0,
                  min_t=None):
    """Grid-based figure: each event picks the chord sounding at its time.
    speech: 'keep' (always), 'thin' (only positions in `thin`, softer), 'gap' (never under speech)."""
    cue = w.cue
    pat = PAT[pattern] if isinstance(pattern, str) else pattern
    for bi, (t0, beat, nbeats, kind) in enumerate(grid):
        if bi % every:
            continue
        for pos, idx, vm in pat:
            if pos >= nbeats:
                continue
            t = t0 + pos * beat
            if (max_t is not None and t > max_t) or (min_t is not None and t < min_t - 1e-6):
                continue
            if cue.I_at(t) < min_I or cue.after_resolve(t, resolve_rest * beat):
                continue
            ch = chord_at(harm, t)
            if ch is None:
                continue
            sp = cue.speech_at(t)
            if sp and speech == "gap":
                continue
            v = w.vel(vel, t, vel_lo, vel_hi) * vm
            if sp and speech == "thin":
                if pos not in thin:
                    continue
                v *= 0.78
            if skip_phrase and cue.in_phrase(t):
                continue
            ks = CH[ch][src] if isinstance(src, str) else src(CH[ch])
            k = ks[idx % len(ks)] + 12 * (idx // len(ks)) + 12 * octave
            w.add(stem, t, dur * beat, k, v)


def pings(w, grid, harm, stem="piano", vel=24, every=2, pos=2.0, src="u", octave=0, pick=1, only_speech=True):
    """Occasional single soft high notes (what plays under dialogue)."""
    cue = w.cue
    for bi, (t0, beat, nbeats, kind) in enumerate(grid):
        if bi % every != (every - 1 if every > 1 else 0):
            continue
        t = t0 + pos * beat
        if only_speech and not cue.speech_at(t):
            continue
        if cue.in_phrase(t, 0.5) or cue.after_resolve(t, 2.5 * beat):
            continue
        ch = chord_at(harm, t)
        if ch is None:
            continue
        ks = CH[ch][src]
        k = ks[(pick + bi // max(every, 1)) % len(ks)] + 12 * octave
        w.add(stem, t, 3.0 * beat, k, w.vel(vel, t))


def sparkles(w, harm, stem="celesta", src="u", octave=12, vel=30, per_gap=2, min_gap=1.0, spacing=0.75):
    """A few bell-like notes inside dialogue gaps (avoiding melodic phrases)."""
    cue = w.cue
    for a, b in cue.gaps(lead=0.6, tail=0.5):
        if b - a < min_gap:
            continue
        t = a + 0.15
        cnt = 0
        while t < b - 0.2 and cnt < per_gap:
            if not cue.in_phrase(t, 0.3):
                ch = chord_at(harm, t)
                if ch:
                    ks = CH[ch][src]
                    k = ks[int(cue.rng.integers(0, len(ks)))] + octave
                    w.add(stem, t, 1.8, k, w.vel(vel, t) * (1.0 - 0.18 * cnt))
                    cnt += 1
            t += spacing * cue.beat * (1.0 + 0.5 * float(cue.rng.random()))


def place_phrase(w, harm, name, t0, beat, stem, octave=0, vel=50, doubles=()):
    P = PHRASES[name]
    cue = w.cue
    last = max(o + d for o, d, _ in P["n"])
    t1 = t0 + last * beat
    patch_harmony(harm, t0, min(t1, cue.D), [(t0 + o * beat, c) for o, c in P["ch"] if t0 + o * beat < cue.D])
    n = len(P["n"])
    for i, (o, d, nm) in enumerate(P["n"]):
        # hesitation: the 3rd and 4th notes of the motif lean late, the final note is a touch softer
        lean = 0.03 * beat if i in (2, 3) else 0.0
        vm = 1.0 if i < n - 1 else 0.86
        t = t0 + o * beat + lean
        hold = d * beat * (1.25 if stem in ("piano", "celesta", "harp", "musicbox") else 1.0)
        w.add(stem, t, hold, midi(nm) + octave, vel * vm, jitter=0.006)
        for st, oc, vmul in doubles:
            w.add(st, t, hold, midi(nm) + octave + oc, vel * vm * vmul, jitter=0.006)
    cue.phrase_iv.append((t0, t1))
    return t1


def place_phrases(w, harm, grid, stem=None, octave=None, vel=50, doubles=(), min_I=0.0, rest_beats=4.0,
                  names=None, max_count=99):
    cue = w.cue
    names = names if names is not None else cue.phrases
    if (not names and not cue.phrase_seq) or cue.I < min_I:
        return
    stem = cue.phrase_stem if stem is None else stem
    octave = cue.phrase_oct if octave is None else octave
    count = 0
    all_names = names
    seq_i = 0
    for gi, (a, b) in enumerate(cue.gaps()):
        t = a
        while t < b - 0.6 and count < max_count:
            if cue.phrase_seq:
                nm0 = cue.phrase_seq[seq_i % len(cue.phrase_seq)]
                names = [nm0] + ([nm0 + "_short"] if nm0 + "_short" in PHRASES else [])
            else:
                names = all_names
            # skip if a phrase already sounds here (e.g. a resolve phrase)
            if any(pa - 0.3 < t < pb for pa, pb in cue.phrase_iv):
                t = max(pb for pa, pb in cue.phrase_iv if pa - 0.3 < t < pb) + 0.3
                continue
            room = b - t
            # the next phrase (this cue's, e.g. a resolve phrase, or another cue's): the whole phrase,
            # held last note included, must be over before it starts
            nxt_phrase = min([pa for pa, pb in cue.phrase_iv + cue.blocked if pa > t] + [1e9])
            room_span = nxt_phrase - t - 0.25
            # the local beat of the bar grid (so melody and accompaniment share one pulse)
            gbar = next(((g0, gb, nbt) for g0, gb, nbt, _k in grid if g0 <= t < g0 + nbt * gb), None)
            gbeat = gbar[1] if gbar else cue.beat
            # snap the start to the grid's half-beats when that costs < 0.25 s
            if gbar:
                g0, gb, nbt = gbar
                hb = gb / 2
                qp = g0 + math.floor((t - g0) / hb + 1e-6) * hb
                qn = qp + hb if qp < t - 1e-6 else qp
                if t - qp <= 0.1:
                    room += t - qp
                    t = qp
                elif qn - t < 0.25:
                    room -= qn - t
                    t = qn
            chosen = None
            for nm in names:
                P = PHRASES[nm]
                last_on = max(o for o, _, _ in P["n"])
                span = max(o + d for o, d, _ in P["n"])
                sc = min(1.0, (room - 0.15) / max(last_on * gbeat, 1e-6), room_span / max(span * gbeat, 1e-6))
                if gbeat * sc >= 0.88 * cue.beat:  # never more than ~12 % faster than the cue's tempo
                    chosen = (nm, gbeat * sc)
                    break
            if not chosen:
                break
            nm, bt = chosen
            end = place_phrase(w, harm, nm, t, bt, stem, octave, w.vel(vel, t), doubles)
            count += 1
            seq_i += 1
            t = end + rest_beats * cue.beat


def resolve_hits(w, harm, stem=None, octave=None, vel=52, doubles=(), chord_stem="piano", roll=True,
                 extra=None):
    """At each resolve hit: a tonic chord (rolled piano), and if there is room a phrase ending on the tonic."""
    cue, M = w.cue, w.cue.M
    stem = cue.phrase_stem if stem is None else stem
    octave = cue.phrase_oct if octave is None else octave
    for t, ty, h in cue.hits:
        if ty != "resolve":
            continue
        rp = h.get("phrase", M.get("resolve_phrase"))
        if rp:
            P = PHRASES[rp]
            last_on = max(o for o, _, _ in P["n"])
            for sc in (1.0, 0.94, 0.88):
                st = t - last_on * cue.beat * sc
                if (st > max(0.3, cue.phrase_from) and not cue.speech_in(st - 0.1, t - 0.2)
                        and not any(a < t and b > st for a, b in cue.muted)
                        and not any(a < t + 1.0 and b > st - 0.3 for a, b in cue.blocked + cue.phrase_iv)):
                    place_phrase(w, harm, rp, st, cue.beat * sc, stem, octave, w.vel(vel, st), doubles)
                    break
        tonic = M["tonic"][0][0]
        c = CH[tonic]
        ks = [c["b"][0]] + c["a"][1:] + c["p"]
        sounding = {k - cue.koff for st, t0, d, k, v in w.notes if st == chord_stem and abs(t0 - t) < 0.3}
        ks = sorted(set(ks) - sounding)
        for j, k in enumerate(ks):
            w.add(chord_stem, t + (0.045 * j if roll else 0.0), 6.0, k, w.vel(34 + 10 * (j == 0), t), jitter=0.004,
                  force=True)
        if extra:
            extra(t)


def swell_layers(w, harm, stems=("strings",), src="p", vel=44, octave=0):
    """For each swell hit: a sustained layer that crescendos from silence over `len` s, then holds."""
    cue = w.cue
    for i, (ts, ln) in enumerate(cue.swells):
        nxt = [t for t, ty, h in cue.hits if t > ts + 1e-3]
        te = nxt[0] if nxt else cue.D
        sub = [[max(a, ts), min(b, te), c] for a, b, c in harm if b > ts and a < te]
        for st in stems:
            key = f"{st}#swell{i}"
            pad_layer(w, sub, key, src=src if st != "choir" else "u", vel=vel, octave=octave)
            pts = [(ts - 0.01, -40.0)]
            for k in range(1, 9):
                f = k / 8
                pts.append((ts + ln * f, -40.0 + 40.0 * float(_smooth(f)) ** 0.7))
            w.auto[key] = pts


DARK_MOODS = {"curious_unease", "alarm_chaos", "void_presence", "confrontation", "sorrow", "stillness", "dread"}


def stings(w, harm):
    """Soft-but-sudden accent at each `sting` hit. Dark moods: timpani + low strings on a b9 cluster over
    the tonic pedal (a jolt). Bright moods: the chord sounding at t, voiced warm (timpani on its root,
    low strings, piano octave, one celesta glint) — an accent, not a scare."""
    cue = w.cue
    for t, ty, h in cue.hits:
        if ty != "sting":
            continue
        if cue.mood in DARK_MOODS:
            w.add("timpani", t, 2.5, midi("D2"), 62, jitter=0, force=True)
            w.add("timpani", t + 0.02, 2.5, midi("A1"), 40, jitter=0, force=True)
            for k, v in (("D2", 54), ("A2", 46), ("Eb3", 40), ("D3", 38)):
                w.add("strfast", t, 1.4, midi(k), v, jitter=0.003, force=True)
            for k, v in (("D1", 50), ("D2", 44)):
                w.add("piano", t, 3.0, midi(k), v, jitter=0, force=True)
            continue
        c = CH[chord_at(harm, t + 0.01) or cue.M["tonic"][0][0]]
        root = c["b"][0]
        tk = root
        while tk < 36:
            tk += 12
        while tk > 47:
            tk -= 12
        w.add("timpani", t, 2.5, tk, 50, jitter=0, force=True)
        for j, (k, v) in enumerate(((root, 50), (root + 12, 44), (c["p"][0], 38), (c["p"][-1], 36))):
            w.add("strfast", t + 0.004 * j, 1.6, k, v, jitter=0, force=True)
        for k, v in ((root, 48), (root + 12, 42)):
            w.add("piano", t, 3.0, k, v, jitter=0, force=True)
        w.add("celesta", t + 0.03, 2.0, c["u"][-1] + 12, 30, jitter=0, force=True)


# ============================================================================================
# moods (composed textures)


def mood_tender_memory(w, cue, harm, grid):
    resolve_hits(w, harm)
    place_phrases(w, harm, grid, vel=50)
    pad_layer(w, harm, "pad", vel=40)
    pattern_layer(w, grid, harm, "piano", "arp_e" if cue.I >= 0.55 else "arp_q", src="a", vel=36, dur=3.0,
                  speech="thin", thin=(0, 2))
    pings(w, grid, harm, "piano", vel=22, every=2, pos=2.0)
    if cue.I >= 0.2:
        sparkles(w, harm, "celesta", vel=26, per_gap=2, min_gap=1.4)
    pad_layer(w, harm, "lowstr", src="b", vel=30, octave=1, min_I=0.4)
    pad_layer(w, harm, "strings", src="p", vel=26, min_I=0.55)
    stings(w, harm)
    swell_layers(w, harm, ("strings",))


def mood_curious_unease(w, cue, harm, grid):
    resolve_hits(w, harm, stem="piano", octave=0)
    place_phrases(w, harm, grid, vel=58)
    pad_layer(w, harm, "pad", vel=34)
    pattern_layer(w, grid, harm, "pizz", "tiptoe", src="a", vel=46, dur=0.6, speech="thin", thin=(0, 2.5))
    # an eerie bowed-glass 9th floating far above (very soft)
    pad_layer(w, harm, "glass", src=lambda c: [c["u"][-1] + 12], vel=16, min_I=0.25)
    pings(w, grid, harm, "piano", vel=20, every=2, pos=3.0, src="u")
    pad_layer(w, harm, "lowstr", src="b", vel=26, octave=1, min_I=0.45)
    stings(w, harm)
    swell_layers(w, harm, ("strings",))


def mood_alarm_chaos(w, cue, harm, grid):
    resolve_hits(w, harm)  # a resolve lands the pedal on a plain D-minor chord (the ostinato rests 2 beats)
    place_phrases(w, harm, grid, vel=50)  # only if the cue asks for phrases (none by default: no melody)
    # pulsing low-string ostinato (3+3+2 accents) on a D pedal; held tremolo dissonance; NO melody
    pattern_layer(w, grid, harm, "strfast", "osti", src=lambda c: [c["b"][0], c["b"][0] + 12], vel=58, dur=0.32,
                  speech="keep")
    pattern_layer(w, grid, harm, "lowstr", "bass1", src=lambda c: [c["b"][0] - 12], vel=34, dur=4.0, speech="keep")
    pad_layer(w, harm, "tremolo", vel=30, min_I=0.0)
    # timpani: a soft thud on each downbeat, a second one on beat 3 when intense
    pattern_layer(w, grid, harm, "timpani", [(0, 0, 1.0), (2.5, 0, 0.6)] if cue.I >= 0.55 else [(0, 0, 1.0)],
                  src=lambda c: [c["b"][0]], vel=34, dur=1.5, speech="keep", min_I=0.3)
    stings(w, harm)
    swell_layers(w, harm, ("strings",), vel=40)


def mood_void_presence(w, cue, harm, grid):
    place_phrases(w, harm, grid, vel=44)  # only if the cue asks for phrases
    # still and immense: low open fifths, a dark pad, a bowed-glass fifth far above that slowly breathes
    pad_layer(w, harm, "lowstr", src=lambda c: [c["b"][0] + 12] + c["a"], vel=40)
    pad_layer(w, harm, "darkpad", src="p", vel=50)
    pad_layer(w, harm, "glass", src="u", vel=22)
    pad_layer(w, harm, "space", src=lambda c: [c["a"][0] + 24, c["a"][1] + 24], vel=16, min_I=0.5)
    # glass breathing: slow ±3 dB swell, 14 s period
    pts = []
    for k in range(int(cue.D / 0.5) + 2):
        t = k * 0.5
        pts.append((t, -3.0 + 3.0 * math.sin(2 * math.pi * t / 14.0)))
    w.auto["glass"] = pts
    # a distant timpani roll at the start (and after swells)
    if cue.I >= 0.3:
        starts = [0.4] + [t for t, ln in cue.swells]
        for s in starts:
            n = int(3.2 / 0.085)
            for i in range(n):
                f = i / n
                v = 5 + 19 * math.sin(math.pi * f) ** 1.5
                w.add("timpani", s + i * 0.085, 0.4, midi("D2"), v * (0.7 + 0.6 * cue.I), jitter=0.006)
    stings(w, harm)
    swell_layers(w, harm, ("lowstr", "glass"), src="p", vel=36)
    resolve_hits(w, harm, stem="piano")


def mood_confrontation(w, cue, harm, grid):
    resolve_hits(w, harm)
    place_phrases(w, harm, grid, vel=52)
    pad_layer(w, harm, "strings", src="p", vel=34)
    pad_layer(w, harm, "lowstr", src="b", vel=36, octave=1)
    # composed viola line (one note per bar, voice-leading through the progression)
    line = {"Dm(add9)": "A3", "Bbmaj7": "Bb3", "F/A": "C4", "Gm7": "D4", "Dm/F": "C4", "Gm(add9)": "Bb3",
            "Asus4": "D4", "A": "C#4", "Dm": "D4", "A7sus4": "D4", "F": "C4", "Gadd9": "B3"}
    prev = None
    for a, b, ch in harm:
        nm = line.get(ch)
        if nm and not w.cue.in_phrase(a + 0.1) and nm != prev:
            w.add("viola", a + 0.05, (b - a) + 0.1, midi(nm), w.vel(30, a))
        prev = nm
    # single sustained piano notes, one per bar (softer under speech)
    pattern_layer(w, grid, harm, "piano", [(0, 1, 1.0)], src="u", vel=26, dur=3.5, speech="keep", skip_phrase=True)
    stings(w, harm)
    swell_layers(w, harm, ("strings",))


def mood_sorrow(w, cue, harm, grid):
    resolve_hits(w, harm, stem="cello", octave=-12)
    place_phrases(w, harm, grid, vel=56)
    pad_layer(w, harm, "lowstr", src=lambda c: [c["b"][0] + 12] + c["p"][:2], vel=30)
    pad_layer(w, harm, "pad", vel=24, min_I=0.3)
    # solo cello: a slow descending line of long tones (5-4-3-2 | 1 ...) that sits under the voice
    line = {"Dm": "A3", "Dm/C": "G3", "Bbmaj7": "F3", "A7sus4": "E3", "A": "E3", "Gm/Bb": "D3", "Dm/A": "F3",
            "Gm6": "E3", "Asus4": "E3", "A7": "C#3"}
    if cue.I >= 0.25:
        prev = None
        for a, b, ch in harm:
            nm = line.get(ch)
            if nm and nm != prev and not cue.in_phrase(a + 0.1) and not cue.in_phrase(b - 0.1):
                w.add("cello", a + 0.08, (b - a) + 0.05, midi(nm), w.vel(30, a))
            prev = nm
    # sparse piano: bass + fifth on the downbeat; a high single note on beat 3 in gaps
    pattern_layer(w, grid, harm, "piano", [(0, 0, 1.0), (0.02, 1, 0.7)], src="a", vel=30, dur=3.5, speech="keep")
    pattern_layer(w, grid, harm, "piano", [(2, 1, 1.0)], src="u", vel=26, dur=3.0, speech="gap", skip_phrase=True)
    pings(w, grid, harm, "piano", vel=20, every=2, pos=2.0)
    stings(w, harm)
    swell_layers(w, harm, ("strings",))


def mood_stillness(w, cue, harm, grid):
    place_phrases(w, harm, grid, vel=44)
    # almost nothing: one held high tone (strings harmonics + glass), a faint low D if intensity allows
    tone = cue.spec.get("tone", "high")  # 'high' (A5 harmonic), 'low' (D2), 'both'
    playing = [(s["t0"], s["t1"]) for s in w.segs if s["kind"] in ("start", "swell", "sting")]
    for a, b in playing:
        if b - a < 0.5:
            continue
        if tone in ("high", "both"):
            w.add("strings", a + 0.05, b - a, midi("A5"), w.vel(26, a), jitter=0)
            w.add("glass", a + 0.4, b - a - 0.3, midi("A5"), w.vel(14, a), jitter=0)
        if tone in ("low", "both") or cue.I >= 0.2:
            w.add("darkpad", a + 0.2, b - a, midi("D2"), w.vel(34 if tone == "high" else 30, a), jitter=0)
        if tone in ("low", "both"):
            w.add("lowstr", a + 0.1, b - a, midi("D2"), w.vel(20, a), jitter=0)
    # resolve: "a single warm low piano chord" + pad
    for t, ty, h in cue.hits:
        if ty == "resolve":
            for j, k in enumerate(["D2", "A2", "F#3", "A3", "D4", "E4"]):
                w.add("piano", t + 0.05 * j, 7.0, midi(k), 42 - 2 * j, jitter=0.004, force=True)
            nxt = [x for x, _, _ in cue.hits if x > t]
            te = nxt[0] if nxt else cue.D
            for k in ["A3", "D4", "F#4"]:
                w.add("pad", t + 0.3, te - t - 0.3, midi(k), 30, jitter=0, force=True)
    stings(w, harm)
    swell_layers(w, harm, ("strings",), vel=30)


def mood_dread(w, cue, harm, grid):
    place_phrases(w, harm, grid, vel=44)  # only if the cue asks for phrases
    pad_layer(w, harm, "lowstr", src="p", vel=32)
    pad_layer(w, harm, "darkpad", src="b", vel=40, octave=1)
    pad_layer(w, harm, "glass", src="u", vel=12, min_I=0.35)
    # heartbeat on the timpani: lub-dub, slowing from ~66 to ~42 bpm across the cue
    t = 0.3
    D = cue.D
    while t < D - 0.4:
        f = t / max(D, 1e-6)
        period = 0.92 + 0.5 * f
        if not cue.is_muted(t):
            v = w.vel(46, t)
            w.add("timpani", t, 0.6, midi("D2"), v, jitter=0.004)
            w.add("timpani", t + 0.27, 0.6, midi("D2"), v * 0.62, jitter=0.004)
        t += period
    # low horns hold a semitone rub (A2/Bb2) when intense
    pad_layer(w, harm, "horns", src=lambda c: [c["b"][0] + 7, c["b"][0] + 8], vel=24, min_I=0.4)
    stings(w, harm)
    swell_layers(w, harm, ("horns", "lowstr"), src=lambda c: [c["b"][0] + 7, c["b"][0] + 8, c["b"][0] + 12], vel=40)
    resolve_hits(w, harm, stem="piano")


def mood_reveal_wonder(w, cue, harm, grid):
    ot = cue.open_at
    if ot is not None:
        # THE VOID OPENS. Until `open_at` the void sonority holds (low open fifths D–A on dark pad + low
        # strings, a bowed-glass fifth A–E far above); at `open_at` a harp glissando rises into the
        # downbeat and the same fifths become the root of a luminous Dmaj9 / E/D (lydian) cluster:
        # strings + choir bloom in, celesta and harp sparkle. The D–A drone stays underneath (the
        # cosmos is *inside* the void), slowly receding.
        patch_harmony(harm, 0.0, ot, [(0.0, "V5")])
        cue.phrase_from = ot
        whole = [[0.0, cue.D, "V5"]]
        pad_layer(w, whole, "darkpad#void", src="p", vel=48)
        pad_layer(w, whole, "lowstr#void", src=lambda c: [c["b"][0] + 12, c["a"][1]], vel=38)
        pad_layer(w, [[0.0, min(cue.D, ot + 9.0), "V5"]], "glass#void", src="u", vel=22)
        w.auto["darkpad#void"] = [(0.0, 0.0), (ot, 0.0), (ot + 10.0, -9.0)]
        w.auto["lowstr#void"] = [(0.0, 0.0), (ot + 2.0, 0.0), (ot + 12.0, -6.0)]
        w.auto["glass#void"] = [(0.0, 0.0), (ot, 0.0), (ot + 8.5, -14.0)]
        # the glissando: a rising Dmaj9 sweep that lands on the opening downbeat
        sweep = ["D3", "A3", "C#4", "E4", "F#4", "A4", "C#5", "E5", "F#5", "A5"]
        for j, nm in enumerate(sweep):
            w.add("harp", ot - 0.72 + 0.08 * j, 3.0, midi(nm), 30 + 2.2 * j, jitter=0.004, force=True)
        w.add("celesta", ot + 0.02, 2.5, midi("A6"), 34, jitter=0, force=True)
        # bright layers fade in over the first seconds of the opening (no hard entry)
        w.auto["strings"] = [(ot - 0.01, -16.0), (ot + 3.5, 0.0)]
        w.auto["choir"] = [(ot - 0.01, -20.0), (ot + 5.0, 0.0)]
    resolve_hits(w, harm, stem="celesta")
    place_phrases(w, harm, grid, vel=58, doubles=(("harp", -12, 0.55),))
    # (after the phrases: they re-harmonise their span)
    lit = harm if ot is None else [[max(a, ot), b, c] for a, b, c in harm if b > ot + 1e-3]
    pad_layer(w, lit, "strings", src="p", vel=40)
    pad_layer(w, lit, "lowstr", src="b", vel=34, octave=1)
    pad_layer(w, lit, "choir", src="u", vel=30, min_I=0.35)
    pad_layer(w, lit, "glass", src=lambda c: [c["u"][-1] + 12], vel=16, min_I=0.3)
    # celesta cascades: rising 16ths over the upper chord tones (gaps), a light 3-note figure under speech
    casc = [(0, 0, 1.0), (.25, 1, .8), (.5, 2, .85), (.75, 3, .75), (1, 4, .8), (1.25, 5, .7), (1.5, 6, .62)]
    pattern_layer(w, grid, harm, "celesta", casc, src="u", vel=34, dur=2.0, octave=1, speech="thin",
                  thin=(0, .5, 1), min_I=0.3, skip_phrase=True, min_t=ot)
    # harp: an upward arpeggio at each bar, from the bass up
    harp = [(2 + i * 0.125, i, 0.9 - 0.04 * i) for i in range(8)]
    pattern_layer(w, grid, harm, "harp", harp, src="a", vel=40, dur=3.0, speech="gap", min_I=0.4, skip_phrase=True,
                  min_t=ot)
    pattern_layer(w, grid, harm, "harp", [(0, 0, 1.0), (0.12, 1, .8)], src="a", vel=32, dur=3.0, speech="keep",
                  min_I=0.4, min_t=(ot + 0.5) if ot is not None else None)
    stings(w, harm)
    swell_layers(w, lit, ("strings",), src="u", vel=40)


def mood_belonging(w, cue, harm, grid):
    resolve_hits(w, harm)
    place_phrases(w, harm, grid, vel=52, doubles=(("strings", 0, 0.4),) if cue.I >= 0.45 else ())
    pad_layer(w, harm, "strings", src="p", vel=36)
    pad_layer(w, harm, "lowstr", src="b", vel=34, octave=1)
    pattern_layer(w, grid, harm, "piano", "arp_q", src="a", vel=34, dur=3.0, speech="thin", thin=(0, 2))
    # warm cello counter-line (tenor register) when the scene opens up
    line = {"D": "F#3", "A/C#": "E3", "Bm7": "D3", "Gmaj7": "D3", "D/F#": "A3", "Gadd9": "B3", "Em7": "G3",
            "A7sus4": "G3", "A": "E3", "Gadd9/D": "B3", "Dadd9": "F#3"}
    if cue.I >= 0.42:
        for a, b, ch in harm:
            nm = line.get(ch)
            if nm and cue.I_at(a) >= 0.42:
                w.add("cello", a + 0.04, (b - a) + 0.12, midi(nm), w.vel(34, a))
    pings(w, grid, harm, "piano", vel=22, every=2, pos=2.0)
    if cue.I >= 0.4:
        sparkles(w, harm, "celesta", vel=26, per_gap=2)
    stings(w, harm)
    swell_layers(w, harm, ("strings",), vel=44)


def mood_resolution(w, cue, harm, grid):
    resolve_hits(w, harm)
    place_phrases(w, harm, grid, vel=48)
    pad_layer(w, harm, "pad", vel=40)
    pad_layer(w, harm, "lowstr", src="b", vel=28, octave=1, min_I=0.35)
    pattern_layer(w, grid, harm, "piano", "arp_h", src="a", vel=34, dur=3.5, speech="keep")
    pings(w, grid, harm, "piano", vel=22, every=2, pos=3.0)
    if cue.I >= 0.3:
        sparkles(w, harm, "celesta", vel=22, per_gap=1, min_gap=1.6)
    stings(w, harm)
    swell_layers(w, harm, ("strings",), vel=38)


def mood_outro(w, cue, harm, grid):
    def twinkle(t):
        for j, k in enumerate(["D6", "A6", "E6"]):
            w.add("celesta", t + 1.2 + 0.55 * j, 2.5, midi(k), 24 - 4 * j, jitter=0.01, force=True)
    resolve_hits(w, harm, extra=twinkle)
    place_phrases(w, harm, grid, vel=46)
    pattern_layer(w, grid, harm, "piano", "arp_q", src="a", vel=28, dur=3.0, speech="thin", thin=(0,),
                  resolve_rest=99.0)
    # solo piano: the soft pad bed only joins at intensity ≥ 0.4
    pad_layer(w, harm, "pad", vel=26, min_I=0.4)
    pings(w, grid, harm, "piano", vel=20, every=2, pos=2.0)
    stings(w, harm)
    swell_layers(w, harm, ("strings",), vel=30)


MOOD_FN = {
    "tender_memory": mood_tender_memory, "curious_unease": mood_curious_unease, "alarm_chaos": mood_alarm_chaos,
    "void_presence": mood_void_presence, "confrontation": mood_confrontation, "sorrow": mood_sorrow,
    "stillness": mood_stillness, "dread": mood_dread, "reveal_wonder": mood_reveal_wonder,
    "belonging": mood_belonging, "resolution": mood_resolution, "outro": mood_outro,
}
# mix level of each mood (dB) before the cue's own intensity scaling
MOOD_DB = {"tender_memory": 0, "curious_unease": -1, "alarm_chaos": -2, "void_presence": -5, "confrontation": -1,
           "sorrow": 0, "stillness": 3, "dread": -1, "reveal_wonder": -5.5, "belonging": -1.5, "resolution": -1,
           "outro": 1.5}


# ============================================================================================
# rendering


def cue_envelope(cue, n):
    """Per-sample gain for the cue: fades × hit dynamics (drop/silence/swell/resolve/sting)."""
    hop = 64
    m = n // hop + 2
    tt = np.arange(m) * hop / SR
    db = np.zeros(m)
    level = 0.0
    for i, (t, ty, h) in enumerate(cue.hits):
        nxt = cue.hits[i + 1][0] if i + 1 < len(cue.hits) else cue.D + 10
        sel = (tt >= t) & (tt < nxt)
        if ty == "drop":
            target, ramp = -26.0, 0.35
        elif ty == "silence":
            target, ramp = -96.0, 0.2
        elif ty == "swell":
            target, ramp = 3.0, float(h.get("len", 4.5))
        elif ty in ("resolve", "sting"):
            # back to full level after a drop/silence (never lower: a cadence after a swell keeps its glow);
            # a resolve comes up over 0.3 s so notes held through a drop don't jump, a sting is immediate
            target, ramp = max(level, 0.0), (0.3 if ty == "resolve" else 0.06)
        else:
            continue
        f = _smooth((tt[sel] - t) / max(ramp, 1e-3)) if ty == "swell" else np.clip((tt[sel] - t) / max(ramp, 1e-3), 0, 1)
        if ty == "silence":
            f = np.sin(0.5 * np.pi * f)
        db[sel] = level + (target - level) * f
        level = target
    g = A.db2lin(db)
    g[db <= -90] = 0.0
    # fades
    fi = np.clip(tt / cue.fade_in, 0, 1)
    fo = np.clip((cue.D - tt) / cue.fade_out, 0, 1)
    g *= np.sin(0.5 * np.pi * fi) * np.sin(0.5 * np.pi * fo)
    g[tt >= cue.D] = 0.0
    return np.interp(np.arange(n), np.arange(m) * hop, g).astype(np.float32)


def widen(x, amount, sr=SR):
    """Mono-compatible stereo spread for mono samples: L = x + a·d(x), R = x − a·d(x), d = 13 ms delay."""
    if amount <= 0:
        return x
    d = int(0.013 * sr)
    m = x.mean(axis=1)
    dl = np.concatenate([np.zeros(d, dtype=np.float32), m[:-d]]) if len(m) > d else np.zeros_like(m)
    dl = A.lowpass(dl, 5000)
    out = x.copy()
    out[:, 0] += amount * dl
    out[:, 1] -= amount * dl
    return out


def automation_curve(pts, n):
    pts = sorted(pts)
    ts = np.array([p[0] for p in pts]) * SR
    ds = np.array([p[1] for p in pts])
    return A.db2lin(np.interp(np.arange(n), ts, ds)).astype(np.float32)


def render_cue(syn, cue, verbose=True):
    segs, harm, grid = build_form(cue)
    w = Writer(cue)
    w.segs = segs
    MOOD_FN[cue.mood](w, cue, harm, grid)
    cue.notes = list(w.notes)
    cue.harm = [list(h) for h in harm]
    n = int(math.ceil(cue.D * SR)) + 1
    dry = np.zeros((n, 2), np.float32)
    sends = {"hall": np.zeros((n, 2), np.float32), "vast": np.zeros((n, 2), np.float32)}
    stems = {}
    for st, t, d, k, v in w.notes:
        stems.setdefault(st, []).append((t, d, k, v))
    for st, nl in sorted(stems.items()):
        base = st.split("#")[0]
        ins = INSTR[base]
        ev = []
        nl.sort()
        # same-key overlaps: end the earlier note just before the re-strike
        last_end = {}
        fixed = []
        for t, d, k, v in nl:
            s0, s1 = int(t * SR), int((t + d) * SR)
            if k in last_end and last_end[k][0] > s0:
                j = last_end[k][1]
                if s0 - fixed[j][0] < int(0.04 * SR):  # (near-)simultaneous duplicate: merge
                    fixed[j] = (fixed[j][0], max(fixed[j][1], s1), k, max(fixed[j][3], v))
                    last_end[k] = (fixed[j][1], j)
                    continue
                fixed[j] = (fixed[j][0], max(fixed[j][0] + 1, s0 - 1), k, fixed[j][3])
            fixed.append((s0, s1, k, v))
            last_end[k] = (s1, len(fixed) - 1)
        for s0, s1, k, v in fixed:
            ev.append((s0, True, k, v))
            ev.append((min(s1, n - 1), False, k, 0))
        x = syn.render(ins["prog"], ev, n)
        x = A.eq_chain(x, ins["eq"])
        x *= syn.calibration(base) * float(A.db2lin(ins.get("level", 0.0)))
        x = widen(x, ins.get("width", 0.0))
        if st in w.auto:
            x *= automation_curve(w.auto[st], n)[:, None]
        x = A.pan(x, ins["pan"])
        dry += x
        sends[ins["bus"]] += x * ins["send"]
    lvl = float(A.db2lin(MOOD_DB.get(cue.mood, 0) - 7.0 * (1.0 - cue.I)))
    env = cue_envelope(cue, n)[:, None] * lvl
    dry *= env
    for b in sends:
        sends[b] *= env
    if verbose:
        cnt = {k: len(v) for k, v in stems.items()}
        print(f"  cue {cue.idx:2d} {cue.mood:15s} {cue.start:7.2f}-{cue.end:7.2f}  I={cue.I:.2f}  "
              f"phrases={len(cue.phrase_iv)}  notes={cnt}", file=sys.stderr)
    return dry, sends


REVERBS = {
    "hall": dict(decay=2.6, predelay=0.024, damping=0.55, size=0.65, cross=0.3, ret=0.48),
    "vast": dict(decay=5.5, predelay=0.045, damping=0.68, size=0.95, cross=0.4, ret=0.52),
}


def load_speech(sheet, sheet_dir, verbose=False):
    """Dialogue intervals (absolute s): the sheet's `speech` list + every `kind: "line"` beat of the
    timeline named by `speech_from`. When `speech_from` is absent the timeline used for anchors
    (default data/timeline.json) is read, so melodies stay out of the dialogue even for cue sheets
    written without it (e.g. tools/resolve_music.py output). `"speech_from": false` disables it."""
    iv = [tuple(map(float, s)) for s in sheet.get("speech", [])]
    src = sheet.get("speech_from", "__default__")
    tl, label = None, None
    if src == "__default__":
        tl = find_timeline(sheet, sheet_dir)
        label = sheet.get("timeline") or "data/timeline.json"
        if tl is None and verbose:
            print("[music] no timeline found: melodies are NOT kept out of the dialogue", file=sys.stderr)
    elif src:
        cands = [src, os.path.join(sheet_dir, src), os.path.join(ROOT, src)]
        path = next((p for p in cands if os.path.exists(p)), None)
        if path is None:
            print(f"[music] speech_from not found: {src}", file=sys.stderr)
        else:
            tl, label = json.load(open(path)), src
    if tl is not None:
        beats = tl.get("beats", {})
        recs = beats.values() if isinstance(beats, dict) else [b[1] if isinstance(b, list) else b for b in beats]
        nl = 0
        for r in recs:
            if r.get("kind") == "line" and "start" in r and "end" in r:
                iv.append((float(r["start"]), float(r["end"])))
                nl += 1
        if verbose:
            print(f"[music] dialogue: {nl} lines from {label}", file=sys.stderr)
    iv.sort()
    merged = []
    for a, b in iv:
        if merged and a <= merged[-1][1] + 0.05:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [tuple(m) for m in merged]


def find_timeline(sheet, sheet_dir):
    src = sheet.get("timeline") or sheet.get("speech_from")
    cands = []
    if src:
        cands = [src, os.path.join(sheet_dir, src), os.path.join(ROOT, src)]
    cands.append(os.path.join(ROOT, "data", "timeline.json"))
    for p in cands:
        if os.path.exists(p):
            return json.load(open(p))
    return None


def render_sheet(sheet, sheet_dir=".", lufs=-18.0, seed=0, verbose=True, cue_dir=None):
    sheet = resolve_sheet(sheet, Anchors(find_timeline(sheet, sheet_dir)))
    dur = float(sheet["duration"])
    speech = load_speech(sheet, sheet_dir, verbose)
    N = int(round(dur * SR))
    syn = Synth()
    dry = np.zeros((N, 2), np.float32)
    buses = {b: np.zeros((N, 2), np.float32) for b in REVERBS}
    cues = [Cue(c, i, speech, seed) for i, c in enumerate(sheet["cues"])]
    melody = []  # absolute intervals of every placed phrase: overlapping cues never sing at once
    for cue in cues:
        cue.blocked = [(a - cue.start, b - cue.start) for a, b in melody if b > cue.start and a < cue.end]
        d, sends = render_cue(syn, cue, verbose)
        melody += [(cue.start + a, cue.start + b) for a, b in cue.phrase_iv]
        s0 = int(round(cue.start * SR))
        m = min(len(d), N - s0)
        if m <= 0:
            continue
        dry[s0:s0 + m] += d[:m]
        for b in sends:
            buses[b][s0:s0 + m] += sends[b][:m]
        if cue_dir:
            A.save(os.path.join(cue_dir, f"cue{cue.idx:02d}_{cue.mood}.wav"), A.peak_normalize(d, -6), subtype="PCM_16")
    mix = dry.astype(np.float64)
    for b, p in REVERBS.items():
        if np.any(buses[b]):
            wet = A.reverb_wet(buses[b], p["decay"], p["predelay"], p["damping"], p["size"], p["cross"])
            mix += p["ret"] * wet[:N]
    mix = A.highpass(mix, 28, order=2)
    mix = A.compress(mix, threshold_db=-26, ratio=1.7, attack=0.04, release=0.5, knee_db=10)
    mix = A.master(mix, lufs, -1.0) if lufs is not None else A.limit(mix, -1.0)
    mix = A.fade_out(mix, 0.6)  # the reverb tail still rings at the film's end: fade it, don't cut it
    return mix, cues


STEM_COLORS = {"piano": (255, 214, 120), "pad": (120, 110, 200), "darkpad": (80, 70, 150), "strings": (120, 200, 170),
               "lowstr": (70, 150, 130), "strfast": (240, 120, 100), "tremolo": (220, 90, 120), "pizz": (200, 160, 90),
               "cello": (240, 150, 80), "viola": (230, 170, 110), "celesta": (170, 240, 255), "musicbox": (255, 200, 240),
               "harp": (140, 220, 255), "choir": (250, 250, 250), "glass": (180, 180, 255), "timpani": (255, 90, 70),
               "horns": (230, 200, 60), "space": (150, 130, 230)}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def note_name(k):
    return f"{NAMES[k % 12]}{k // 12 - 1}"


def piano_roll(cues, speech, path, t0=0.0, t1=None, px_per_s=12, title=None):
    """Debug PNG: every note of every cue (colour = stem), speech shaded, cue starts marked."""
    from PIL import Image, ImageDraw
    t1 = t1 or max(c.end for c in cues)
    W = int((t1 - t0) * px_per_s) + 120
    lo, hi = 24, 100
    rowh = 5
    H = (hi - lo) * rowh + 60
    im = Image.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(im)
    X = lambda t: 100 + int((t - t0) * px_per_s)
    Y = lambda k: 30 + (hi - k) * rowh
    for a, b in speech:
        if b > t0 and a < t1:
            d.rectangle([X(max(a, t0)), 30, X(min(b, t1)), H - 30], fill=(34, 30, 50))
    for k in range(lo, hi):
        if k % 12 == 2:
            d.line([(100, Y(k)), (W, Y(k))], fill=(50, 50, 70))
            d.text((4, Y(k) - 6), note_name(k), fill=(160, 160, 190))
    for c in cues:
        if c.end < t0 or c.start > t1:
            continue
        d.line([(X(c.start), 18), (X(c.start), H - 20)], fill=(90, 200, 160))
        d.text((X(c.start) + 2, 4), f"{c.idx}:{c.mood}", fill=(150, 255, 210))
        for st, t, du, k, v in getattr(c, "notes", []):
            ta = c.start + t
            tb = min(ta + du, c.end)
            if tb < t0 or ta > t1:
                continue
            col = STEM_COLORS.get(st.split("#")[0], (200, 200, 200))
            f = 0.35 + 0.65 * min(1.0, v / 70)
            col = tuple(int(cc * f) for cc in col)
            d.rectangle([X(ta), Y(k) - rowh + 1, max(X(ta) + 1, X(tb)), Y(k)], fill=col)
    step = 1 if (t1 - t0) < 40 else 5
    s = math.ceil(t0)
    while s <= t1:
        if int(s) % step == 0:
            d.text((X(s), H - 18), f"{s:g}", fill=(170, 170, 190))
        s += 1
    lx = 110
    for nm, col in STEM_COLORS.items():
        d.rectangle([lx, H - 8, lx + 8, H - 2], fill=col)
        d.text((lx + 10, H - 12), nm, fill=col)
        lx += 12 + 7 * len(nm)
    if title:
        d.text((W - 300, 4), title, fill=(230, 230, 240))
    im.save(path)
    return path


def report(mix, cues):
    rows = []
    for c in cues:
        a, b = int(c.start * SR), int(min(c.end, len(mix) / SR) * SR)
        seg = mix[a:b]
        if len(seg) == 0:
            continue
        rms = float(A.lin2db(np.sqrt(np.mean(seg.astype(np.float64) ** 2))))
        pk = float(A.lin2db(np.abs(seg).max()))
        rows.append((c.idx, c.mood, c.start, c.end, c.I, rms, pk, A.loudness(seg), len(c.phrase_iv)))
    print(f"{'#':>2} {'mood':15s} {'start':>7} {'end':>7} {'I':>4} {'RMS dB':>7} {'peak dB':>7} {'LUFS':>6} phrases")
    for r in rows:
        print(f"{r[0]:2d} {r[1]:15s} {r[2]:7.2f} {r[3]:7.2f} {r[4]:4.2f} {r[5]:7.1f} {r[6]:7.1f} {r[7]:6.1f} {r[8]}")
    h = A.analyze(mix)
    print("whole:", json.dumps(h))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cues")
    ap.add_argument("out")
    ap.add_argument("--lufs", type=float, default=-18.0, help="integrated loudness target (default -18 LUFS)")
    ap.add_argument("--seed", type=int, default=0, help="humanisation seed")
    ap.add_argument("--cue-dir", default=None, help="also write each cue's dry render here (debug)")
    ap.add_argument("--roll", default=None, help="write a piano-roll PNG of every note (debug)")
    ap.add_argument("--notes", default=None, help="write a text dump of every note (debug)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    sheet = json.load(open(a.cues))
    sdir = os.path.dirname(os.path.abspath(a.cues))
    mix, cues = render_sheet(sheet, sdir, a.lufs, a.seed, not a.quiet, a.cue_dir)
    A.save(a.out, mix)
    if not a.quiet:
        report(mix, cues)
    if a.roll:
        piano_roll(cues, load_speech(sheet, sdir), a.roll, title=os.path.basename(a.out), t1=len(mix) / SR)
    if a.notes:
        with open(a.notes, "w") as f:
            for c in cues:
                f.write(f"== cue {c.idx} {c.mood} {c.start:.2f}-{c.end:.2f} I={c.I}\n")
                f.write("   harmony: " + " | ".join(f"{c.start + h[0]:.1f} {h[2]}" for h in c.harm) + "\n")
                for st, t, du, k, v in sorted(c.notes, key=lambda n: (n[1], n[0])):
                    f.write(f"   {c.start + t:8.3f} {du:5.2f}s {st:16s} {note_name(k):4s} v{v}\n")
    print(a.out)


if __name__ == "__main__":
    main()
