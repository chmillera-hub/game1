#!/usr/bin/env python3
"""Psalm 22 - original score.

A hand-written harmonic/melodic sketch (SCORE below, one entry per text block) is arranged
algorithmically for orchestra + choir (voice-leading search, tied pedals, expression curves,
humanisation), written as MIDI, rendered with FluidSynth + MuseScore_General.sf2 (MIT) and
finished with a synthetic-hall convolution reverb.

Every section is stretched to the block boundaries found in timeline.json, and the climax is
anchored to the start of the last narration phrase ("He has done it!") from phrases.json, so the
script can simply be re-run after the timeline is regenerated.

Usage:  /opt/venv/bin/python psalm22/audio/music.py [--check] [--keep-midi-only]
Outputs ($WORK/audio):
  music.wav                 48 kHz stereo float, full score (sum of the stems)
  stems/music_<stem>.wav    strings, solo, choir, brass, perc, harp
  midi/<stem>.mid           the rendered MIDI files
  music_cues.json           section map (times, tempo, chords) used by docs/mix
"""
import argparse, itertools, json, os, subprocess, sys
import numpy as np
import mido

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402

SR = dsp.SR
SF2 = os.environ.get("SF2", "/opt/assets/soundfonts/MuseScore_General.sf2")
SF2_FALLBACK = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
OUT = dsp.AUDIO
SEED = 22

# ============================================================================ music theory
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "dim": [0, 3, 6], "dim7": [0, 3, 6, 9], "aug": [0, 4, 8],
        "sus4": [0, 5, 7], "sus2": [0, 2, 7], "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10],
        "maj7": [0, 4, 7, 11], "add9": [0, 4, 7, 2], "madd9": [0, 3, 7, 2], "6": [0, 4, 7, 9],
        "m6": [0, 3, 7, 9], "5": [0, 7], "7sus4": [0, 5, 7, 10], "m7b5": [0, 3, 6, 10],
        "7b9": [0, 4, 7, 10, 1]}


def _pc(s):
    p = NOTE[s[0]]
    i = 1
    while i < len(s) and s[i] in "#b":
        p += 1 if s[i] == "#" else -1
        i += 1
    return p % 12, i


def pitch(name):
    """'Bb4' -> 70 (C4 = 60)."""
    p, i = NOTE[name[0]], 1
    while name[i] in "#b":
        p += 1 if name[i] == "#" else -1
        i += 1
    return 12 * (int(name[i:]) + 1) + p


def parse_chord(sym):
    main, _, bass = sym.partition("/")
    root, i = _pc(main)
    qual = main[i:]
    ivs = QUAL[qual]
    pcs = [(root + v) % 12 for v in ivs]
    sus = "sus" in qual
    third = next(((root + v) % 12 for v in ivs if v in (3, 4)), None)
    # tone priority when there are fewer voices than chord tones
    order = []
    if third is not None:
        order.append(third)
    if sus:
        order += [(root + v) % 12 for v in ivs if v in (2, 5)]
    order.append(root)
    order += [(root + v) % 12 for v in ivs if v in (10, 11, 9, 1) or (v == 2 and not sus)]
    order += [(root + v) % 12 for v in ivs if v in (6, 8)]
    order += [(root + v) % 12 for v in ivs if v == 7]
    prio = []
    for p in order:
        if p not in prio:
            prio.append(p)
    return {"sym": sym, "root": root, "pcs": pcs, "prio": prio, "third": third,
            "bass": _pc(bass)[0] if bass else root}


def parse_seq(s):
    """'Dm:2 A/C#:1' -> [(chord, beats)]"""
    out = []
    for tok in s.split():
        sym, d = tok.rsplit(":", 1)
        out.append((parse_chord(sym), float(d)))
    return out


def parse_mel(s):
    """'A4:1.75~ Bb4/A4:1 r:.5' -> notes [{p, d, scoop, grace}] ('~' = scoop, 'X/Y' = grace X)."""
    out = []
    for tok in s.split():
        name, d = tok.rsplit(":", 1)
        scoop = d.endswith("~")
        d = float(d.rstrip("~"))
        grace = None
        if "/" in name:
            g, name = name.split("/")
            grace = pitch(g)
        out.append({"p": None if name == "r" else pitch(name), "d": d, "scoop": scoop, "grace": grace})
    return out


# ============================================================================ the score
# Each block: N beats (stretched to the block length), chords "Sym:beats", dyn = intensity
# breakpoints (beat, 0..1), layers = gain or (gain, from_beat, to_beat) or a list of those,
# mel = (instrument, start_beat, notes, gain); notes may spill into the following blocks.
# perc = timpani / bass drum / cymbal events. Key: D minor with Hijaz (Phrygian-dominant)
# colour, turning to D major at the resurrection (b15).
SCORE = {
    # -- title: open fifth drone, the duduk's Hijaz call (A-Bb-A-G-F#-Eb-D) over it
    "intro": dict(N=4, chords="D5:4", dyn=[(0, .55), (2, .6), (4, .52)], top=74,
                  layers=dict(bass=.85, celli=.8, upper=.5, oohs=.45),
                  mel=[("duduk", .25, "A4:1.75~ Bb4:.25 A4:.25 G4:.5 F#4:.5 Eb4:.5 D4:3.5~", .9)],
                  perc=[("boom", 0.0, 82, "D2")]),
    # -- My God, my God... (lament; i - iv/D - i - VI - V)
    "b01": dict(N=11, chords="Dm:4 Gm/D:2 Dm:1 Bb:2 A:2", dyn=[(0, .45), (9, .42), (11, .47)], top=[(0, 69), (11, 69)],
                layers=dict(bass=.8, celli=.7, upper=.6, oohs=(.3, 0, 4)),
                mel=[("cello", 4, "Bb3:2 A3:1 D4:2 C#4:2", .55),
                     ("duduk", 9.5, "D5:.5 C#5:.5 Bb4:.5 A4:1.5~", .85)]),
    # -- day and night: descending lament bass D-C-Bb-A, ticking pizzicato pulse
    "b02": dict(N=8, chords="Dm:2 Dm/C:2 Gm/Bb:2 A:2", dyn=[(0, .42), (8, .45)],
                layers=dict(bass=.75, celli=.7, upper=.5, pizz=(.65, 0, 6.5)),
                mel=[("duduk", 6.75, "E5:.5 D5:.25 C#5:.25 D5:1.5~", .8)]),
    # -- enthroned: brightening to the relative major, choir, harp glissando
    "b03": dict(N=8, chords="Bb:2 F/A:2 Gm:1 Dm:1 Csus4:1 C:1", dyn=[(0, .48), (4, .6), (8, .66)], top=[(0, 74), (8, 76)],
                layers=dict(bass=.7, celli=.7, upper=.75, aahs=(.55, .25, 8)),
                mel=[("vln_hi", 0, "F5:4 D5:2 C5:2", .35)],
                harp=[("gliss", 0, 1.5, "up")],
                perc=[("roll", 7, 8, 25, 95, "C2")]),
    # -- the Red Sea / Moses: noble horn theme in F, harp, timpani
    "b04": dict(N=14, chords="F:2 C/E:1 Dm:1 Bb:1 C:1 F:2 Dm:1 Gm:1 Bb:1 C:1 F:1 A:1",
                dyn=[(0, .74), (6, .8), (12, .74), (13, .52), (14, .36)], top=[(0, 77), (6, 81), (12, 77), (14, 69)],
                layers=dict(bass=.85, celli=.85, upper=.8, top8=(.55, 0, 12.5), horns=(.5, 6, 12.5),
                            aahs=(.55, 6, 12.5), harp=(.5, 0, 12)),
                mel=[("horn_mel", 0, "C4:1 F4:1 E4:.5 G4:.5 A4:1 Bb4:1 G4:.5 E4:.5 F4:2 A4:1 Bb4:.75 A4:.25 F4:1 G4:1 A4:1", .8),
                     ("duduk", 13, "D5:.5 C#5:.5 Bb4:.5 A4:1.5~", .8)],
                perc=[("hit", 0, 105, "F2"), ("crash", 0, 72), ("hit", 6, 88, "F2")]),
    # -- a worm: almost nothing; low solo cello
    "b05": dict(N=8, chords="Dm:3 Gm/D:2 Dm:1 Bb/D:1 A/C#:1", dyn=[(0, .32), (8, .36)], top=[(0, 65), (8, 64)],
                layers=dict(bass=.55, celli=.45, upper=(.25, 3, 8)),
                mel=[("cello", 0, "r:.5 D3:1.5 F3:1 E3:.5 D3:.5 G3:1.5 A3:.5 Bb3:1 A3:1", .65)]),
    # -- mocking crowd: tremolo, Phrygian bII over the D pedal, low trombones
    "b06": dict(N=15, chords="Dm:3 Eb/D:2 Dm:1 Gm/D:2 Eb/D:1 Dm:1 Bb/D:2 Eb/D:1 A7/C#:2",
                dyn=[(0, .42), (6, .55), (13, .6), (15, .45)],
                layers=dict(bass=.8, celli=.6, trem=.8, upper=.3),
                mel=[("tbn", 0, "r:6 D2:2 Eb2:1 D2:3 Eb2:1 C#2:2", .55),
                     ("duduk", 13.75, "D5:.5 C#5:.5 Bb4:.5 A4:1.25~", .8)]),
    # -- nativity lullaby (F major, oboe + harp) -> Mary at the cross (cello)
    "b07": dict(N=14, chords="F:2 Bb:2 F/A:1 Gm7:1 Csus4:.5 C:.5 Dm:2 Bb:1 F/A:1 Gm:1 Gm6/Bb:1 Asus4:.5 A:.5",
                dyn=[(0, .46), (7, .42), (14, .42)], top=[(0, 72), (7, 69), (14, 67)],
                layers=dict(bass=.6, celli=.6, upper=.55, oohs=(.35, 0, 7), harp=(.6, 0, 7)),
                harp_div=3,
                mel=[("oboe", 0, "C5:1 A4:.5 F4:.5 Bb4:1 D5:.5 C5:1.5 Bb4:.5 A4:.5 G4:1", .7),
                     ("cello", 7, "A3:1.5 G3:.5 F3:1 C4:1 Bb3:1 G3:.5 E3:1 C#3:.5 D3:2", .65)]),
    # -- trouble is near: tremolo crescendo, the heartbeat starts far away
    "b08": dict(N=7, chords="Dm:2 Bdim/D:2 Gm/D:1 Eb/D:1 A7/C#:1", dyn=[(0, .36), (7, .6)],
                layers=dict(bass=.7, celli=.6, trem=.75, upper=.3),
                mel=[("tbn", 5, "D2:1 C#2:1", .45),
                     ("duduk", 5.75, "D5:.5 C#5:.5 Bb4:.5 A4:1~", .75)],
                perc=[("heart", 0, 7, 58, 30, 55)]),
    # -- bulls and lions: heartbeat, trombone ostinato D-Eb, horn swell for the lion
    "b09": dict(N=12, chords="Dm:2 Eb/D:1 Dm:1 Eb/D:1 Dm:1 Gm/D:2 Eb/D:1 C#dim7:1 Dm:2",
                dyn=[(0, .6), (6, .76), (12, .6)],
                layers=dict(bass=.85, celli=.7, trem=.85, upper=.35, horns=(.75, 5.75, 8.5)),
                mel=[("tbn", 0, "D2:1.5 Eb2:1.5 D2:1 Eb2:1 D2:3 Eb2:1 C#2:1 D2:2", .75)],
                perc=[("heart", 0, 11.6, 66, 55, 78), ("hit", 5.8, 100, "D2")]),
    # -- poured out like water: chromatic lament bass D-C#-C-B-Bb-A; celesta drops for the candle
    "b10": dict(N=12, chords="Dm:2 A/C#:1 Dm/C:1 G/B:1 Gm/Bb:1 Dm/A:1 A:1 Dm:1 Bb:1 Gm6/Bb:1 A7:1",
                dyn=[(0, .42), (12, .36)],
                layers=dict(bass=.6, celli=.55, upper=.5),
                mel=[("duduk", 0, "F4:2 E4:1 F4:1 D4:2 F4:1 E4:1 D4:2 Bb3:1 C#4:1", .55),
                     ("celesta", 6, "A5:2 F5:2 E5:2", .4)]),
    # -- potsherd / dust of death: dry open fifth, a thin high violin line
    "b11": dict(N=10, chords="D5:6 Gm/D:2 Dm:2", dyn=[(0, .4), (10, .44)], top=[(0, 69), (10, 69)],
                layers=dict(bass=.6, celli=.5, upper=.35, oohs=(.45, 6, 10)),
                mel=[("vln_hi", 0, "A5:6 Bb5:2 A5:2", .3),
                     ("duduk", 8.75, "A4:.5 G4:.25 F4:.25 E4:.5 D4:1.5~", .8)]),
    # -- dogs / they pierce: fast heartbeat; sudden drop when the hammer rises; impact
    "b12": dict(N=8, chords="Dm:2 Eb/D:1 Dm:1 Eb/D:1 Gm/D:2 A7/C#:1",
                dyn=[(0, .56), (4.3, .68), (4.42, .1), (4.98, .1), (5.02, .78), (6.5, .42), (8, .4)],
                layers=dict(bass=.85, celli=.7, trem=(.85, 0, 4.45), upper=.4),
                mel=[("tbn", 0, "D2:2 Eb2:1 D2:1.4 r:.6 D2:2 C#2:1", .7)],
                perc=[("heart", 0, 4.3, 76, 60, 80), ("boom", "hammer", 112, "D2")]),
    # -- stare / casting lots: bleak; Neapolitan cadence; final Hijaz lament into darkness
    "b13": dict(N=13, chords="Dm:2 Gm/Bb:1 A/C#:1 Dm:2 Bb:1 Gm:1 Eb/G:1 A7:1 D5:3",
                dyn=[(0, .42), (10, .36), (12.4, .2), (13, .1)],
                layers=dict(bass=.6, celli=.55, upper=.5),
                mel=[("cello", 0, "F3:2 G3:1 E3:1 F3:1.5 E3:.5 D3:1 Bb2:1 Eb3:1 C#3:1 D3:3", .6),
                     ("duduk", 10.5, "A4:.75~ Bb4:.25 A4:.25 G4:.25 F#4:.5 Eb4:.5 D4:1.5~", .9)]),
    # -- THE TURN: a single high note in the dark, then a rising bass and growing strings
    "b14": dict(N=22, chords="Bb:4 C:2 Dm:2 C/E:2 F:2 Gm:2 F/A:1 Bb:1 C:1 Dm:1 Bb:1 A7sus4:1.5 A7:1.5",
                dyn=[(0, .22), (4, .34), (8, .46), (12, .56), (16, .66), (19, .76), (22, 1.0)],
                top=[(0, 74), (4, 76), (8, 77), (12, 79), (16, 81), (19, 81), (22, 85)],
                layers=dict(upper=(.85, 1.5, 22), celli=(.75, 2, 22), bass=(.7, 4, 22), oohs=(.5, 4, 12.5),
                            aahs=(.7, 12, 22), top8=(.6, 12, 22), horns=(.6, 16, 22), harp=(.4, 4, 19)),
                mel=[("vln_hi", 0, "D6:4", .45),
                     ("horn_mel", 12, "D4:1 G4:1 A4:1 Bb4:1 C5:1 D5:1 Bb4:.5 C5:.5 D5:1.5 C#5:1.5", .85)],
                perc=[("roll", 19, 22, 18, 112, "A1")]),
    # -- RESURRECTION: D major tutti, hymn theme
    "b15": dict(N=7, chords="D:2 G/D:1 D:1 Bm:1 G:1 A:1", dyn=[(0, 1.0), (1.2, .84), (7, .8)], top=[(0, 78), (7, 76)],
                layers=dict(bass=1, celli=1, upper=1, top8=.85, aahs=1, horns=.85, harp=.5),
                mel=[("vln_hi", 0, "D6:1.5 C#6:.5 B5:1 A5:1 B5:.5 C#6:.5 D6:1 C#6:1", .7),
                     ("horn_mel", 0, "D4:1.5 C#4:.5 B3:1 A3:1 B3:.5 C#4:.5 D4:1 C#4:1", .75)],
                harp=[("gliss", 0, 1.2, "up")],
                perc=[("boom", 0, 120, "D2"), ("crash", 0, 100), ("roll", 0, 1.5, 70, 20, "D2")]),
    # -- praise him! / scarred hand (cello) / face in the light (oboe)
    "b16": dict(N=22, chords="D:2 A/C#:1 Bm:1 G:1 D/F#:1 G:1 A:1 Bm:1 Asus4:.5 A:.5 "
                             "D/F#:2 G:1 Em7:1 A:1 Bm:1 G:2 D/F#:1 Em7:1 Asus4:1 A:1",
                dyn=[(0, .76), (9.5, .72), (10.5, .5), (16, .55), (22, .6)],
                top=[(0, 78), (10, 76), (10.5, 72), (16, 71), (17, 76), (22, 76)],
                layers=dict(bass=.8, celli=.8, upper=.8, aahs=[(.7, 0, 10), (.55, 16, 22)],
                            horns=(.6, 0, 10), oohs=(.5, 10, 16), harp=.5),
                mel=[("cello", 10, "F#3:1 A3:.75 G3:.25 B3:1 G3:1 E3:.75 F#3:1.25", .65),
                     ("oboe", 16, "B4:1 D5:1 A4:1 G4:1 D5:1 C#5:1", .65)]),
    # -- the great assembly sings / bread broken
    "b17": dict(N=18, chords="D:2 G:1 D/F#:1 Em:1 A:1 Bm:1 G:1 A:1 D:2 F#m:1 Bm:1 G:1 Em7:1 A:1 D:2",
                dyn=[(0, .66), (9, .56), (18, .64)], top=[(0, 74), (9, 76), (18, 74)],
                layers=dict(bass=.75, celli=.75, upper=.65, aahs=(.75, 0, 9.2), oohs=(.55, 9, 18),
                            horns=(.45, 0, 9), harp=.55),
                harp_div=[(0, 2), (9, 3)]),
    # -- ends of the earth / nations bow: majestic horn theme
    "b18": dict(N=16, chords="G:2 D/F#:2 Em:1 A:1 Bm:2 G:1 A:1 D:2 Bm:1 G:1 Em7:1 A:1",
                dyn=[(0, .76), (10, .82), (16, .74)], top=[(0, 76), (10, 79), (16, 78)],
                layers=dict(bass=.9, celli=.9, upper=.9, top8=.65, aahs=.85, horns=.5, harp=.5),
                mel=[("horn_mel", 0, "D4:1 G4:1 A4:1.5 F#4:.5 G4:1 E4:.5 A4:.5 B4:1.5 A4:.5 G4:1 A4:1 F#4:1 A4:1 B4:1 D5:1 B4:1 C#5:1", .85)],
                perc=[("roll", 0, 1.5, 55, 20, "G2"), ("roll", 9, 10, 20, 70, "A1"), ("hit", 10, 85, "D2")]),
    # -- humility: crowns laid down, an old man kneels (cello descends to the dust)
    "b19": dict(N=12, chords="D:2 G/B:1 A/C#:1 Bm:2 G:1 D/F#:1 Em:1 C:1 G/B:1 Asus4:.5 A:.5",
                dyn=[(0, .56), (12, .56)], top=[(0, 74), (12, 71)],
                layers=dict(bass=.6, celli=.55, upper=.55, oohs=.55, harp=.35),
                mel=[("cello", 0, "F#3:1 A3:1 D4:1 C#4:.5 E4:.5 D4:1.5 C#4:.5 B3:1 A3:1 G3:1 E3:1 D3:1.5 C#3:.5", .7)]),
    # -- to the next generation / river of lights -> bVI-bVII-I into the climax
    "b20": dict(N=13, chords="D:2 Bm:1 G:1 D/F#:1 Em7:1 A:1 Bm:1 G:1 D/F#:1 Em7:1 Bb:1 C:1",
                dyn=[(0, .5), (7, .6), (10, .8), (13, 1.0)], top=[(0, 72), (7, 74), (13, 81)],
                layers=dict(bass=.75, celli=.75, upper=.85, oohs=(.5, 0, 7.2), aahs=(.85, 7, 13),
                            horns=(.6, 7, 13), top8=(.7, 9, 13), harp=.6),
                harp_div=[(0, 2), (7, 3)],
                mel=[("oboe", 0, "A4:1 F#4:.5 A4:.5 B4:1 D5:.5 B4:.5 A4:1 G4:1 E4:.5 C#5:.5", .6),
                     ("tpt", 7, "F#4:1 G4:1 A4:1 B4:1 D5:1 E5:1 F#5:2.5 E5:.5 D5:1", .8)],
                perc=[("roll", 11, 12, 40, 80, "Bb1"), ("roll", 12, 13, 80, 122, "C2")]),
    # -- HE HAS DONE IT! climax, plagal 'amen', sustained D major under the end title
    "outro": dict(N=9, chords="D:4 G/D:2 D:3", dyn=[(0, 1.0), (1.5, .9), (4, .74), (6, .6), (9, .42)],
                  top=[(0, 81), (4, 79), (9, 78)],
                  layers=dict(bass=1, celli=1, upper=1, top8=(1, 0, 6), aahs=1, horns=1, harp=.5),
                  mel=[("horn_mel", 0, "A4:4 B4:2 A4:3", .8)],
                  harp=[("gliss", 0, 1.5, "up")],
                  perc=[("boom", 0, 127, "D2"), ("crash", 0, 112), ("roll", 0, 2.5, 80, 15, "D2"),
                        ("hit", 6, 50, "D2")]),
}
GENERIC = dict(N=8, chords="D5:8", dyn=[(0, .4), (8, .4)], layers=dict(bass=.7, celli=.6, upper=.4))

# ============================================================================ instruments
# name: (stem, channel, bank, program, expressive(CC2 dynamics), pan 0..127, CC7 volume)
INST = {
    "basses":   ("strings", 0, 51, 49, True, 92, 112),
    "celli":    ("strings", 1, 41, 49, True, 82, 104),
    "violas":   ("strings", 2, 31, 49, True, 70, 96),
    "vln2":     ("strings", 3, 26, 49, True, 56, 94),
    "vln1":     ("strings", 4, 21, 49, True, 44, 98),
    "vln_hi":   ("strings", 5, 21, 49, True, 50, 92),
    "trem":     ("strings", 6, 31, 44, True, 60, 98),
    "trem_lo":  ("strings", 7, 41, 44, True, 80, 100),
    "pizz":     ("strings", 8, 40, 45, False, 76, 104),
    "cello":    ("solo", 0, 17, 42, True, 64, 112),
    "duduk":    ("solo", 1, 17, 69, True, 60, 112),
    "oboe":     ("solo", 2, 17, 68, True, 58, 96),
    "aahs":     ("choir", 0, 17, 52, True, 64, 104),
    "oohs":     ("choir", 1, 17, 53, True, 64, 104),
    "horns":    ("brass", 0, 17, 60, True, 48, 92),
    "horn_mel": ("brass", 1, 17, 60, True, 54, 104),
    "tbn":      ("brass", 2, 17, 57, True, 80, 100),
    "tpt":      ("brass", 3, 17, 56, True, 60, 94),
    "timp":     ("perc", 0, 0, 47, False, 70, 116),
    "bd":       ("perc", 1, 8, 116, False, 64, 100),
    "kit":      ("perc", 9, 128, 48, False, 64, 92),
    "harp":     ("harp", 0, 0, 46, False, 40, 104),
    "celesta":  ("harp", 1, 0, 8, False, 84, 92),
}
STEMS = ["strings", "solo", "choir", "brass", "perc", "harp"]
# post-processing per stem: reverb wet, dry, target active-RMS (dB, relative), hall rt60
STEM_FX = {
    "strings": dict(wet=.42, dry=.9, level=0.0, rt=3.0),
    "solo":    dict(wet=.34, dry=.95, level=-1.5, rt=2.6),
    "choir":   dict(wet=.6, dry=.75, level=-4.0, rt=3.4),
    "brass":   dict(wet=.5, dry=.85, level=-4.0, rt=3.0),
    "perc":    dict(wet=.65, dry=.75, level=-3.0, rt=3.4),
    "harp":    dict(wet=.45, dry=.9, level=-8.0, rt=2.6),
}
LAYER_INST = {"bass": ["basses"], "celli": ["celli"], "upper": ["violas", "vln2", "vln1"],
              "top8": ["vln_hi"], "trem": ["trem", "trem_lo"], "aahs": ["aahs"], "oohs": ["oohs"],
              "horns": ["horns"], "harp": ["harp"], "pizz": ["pizz"]}
VIBRATO = {"cello": 52, "duduk": 40, "oboe": 34, "horn_mel": 12, "tpt": 16, "vln_hi": 30, "tbn": 0}


# ============================================================================ timeline
class Plan:
    def __init__(self, T):
        self.T = T
        ph = T["phrases"]
        self.climax = ph[-1]["start"]
        self.total = T["total"]
        segs = []
        for b in T["order"]:
            bt = T["blocks"][b]
            name = "intro" if b == "intro" else b
            if b == T["order"][-1]:
                segs.append([name, bt["t0"], self.climax])
                segs.append(["outro", self.climax, self.total])
            else:
                segs.append([name, bt["t0"], None])
        for i in range(len(segs) - 1):
            if segs[i][2] is None:
                segs[i][2] = segs[i + 1][1]
        self.segs = []
        for name, t0, t1 in segs:
            sc = SCORE.get(name, GENERIC)
            if name not in SCORE:
                print("WARNING: no score for block %s - using generic drone" % name)
            N = sc["N"]
            bl = (t1 - t0) / N
            if not .7 <= bl <= 1.4:
                print("WARNING: %s beat length %.2f s is far from the planned ~1 s" % (name, bl))
            self.segs.append({"name": name, "t0": t0, "t1": t1, "N": N, "bl": bl, "sc": sc})
        self.index = {s["name"]: i for i, s in enumerate(self.segs)}

    def tb(self, si, b):
        """Beat b of segment si -> seconds (beats beyond the segment spill into the next ones)."""
        while b > self.segs[si]["N"] and si + 1 < len(self.segs):
            b -= self.segs[si]["N"]
            si += 1
        while b < 0 and si > 0:
            si -= 1
            b += self.segs[si]["N"]
        s = self.segs[si]
        return s["t0"] + b * s["bl"]

    def seg_at(self, t):
        for i, s in enumerate(self.segs):
            if t < s["t1"]:
                return i
        return len(self.segs) - 1

    def beat_at(self, t):
        si = self.seg_at(t)
        s = self.segs[si]
        return si, (t - s["t0"]) / s["bl"]

    def dyn(self, si, b):
        d = self.segs[si]["sc"]["dyn"]
        return float(np.interp(b, [p[0] for p in d], [p[1] for p in d]))

    def top(self, si, b):
        """Planned pitch of the highest string voice (None = free voice-leading)."""
        t = self.segs[si]["sc"].get("top")
        if t is None:
            return None
        if isinstance(t, (int, float)):
            return float(t)
        return float(np.interp(b, [p[0] for p in t], [p[1] for p in t]))

    def layer_gain(self, si, layer, b):
        v = self.segs[si]["sc"]["layers"].get(layer)
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        wins = v if isinstance(v, list) else [v]
        for g, b0, b1 in wins:
            if b0 <= b < b1:
                return g
        return 0.0

    def anchor(self, si, b):
        """Beat value or a named anchor ('hammer' = the impact on 'they pierce')."""
        if b == "hammer":
            name = self.segs[si]["name"]
            ph = self.T["blocks"].get(name, {}).get("phrases", [])
            t = (ph[1]["start"] if len(ph) > 1 else self.segs[si]["t0"]) + HAMMER_OFFSET
            return (t - self.segs[si]["t0"]) / self.segs[si]["bl"]
        return b


HAMMER_OFFSET = 0.32   # seconds after the start of "they pierce my hands..." (shared with sfx.py)


# ============================================================================ voice leading
RANGES = {
    "upper": [(50, 72), (55, 79), (60, 86)],
    "trem":  [(45, 62), (50, 67), (55, 72)],
    "choir": [(48, 64), (55, 72), (60, 79)],
    "horns": [(50, 65), (53, 69), (57, 72)],
}
TOP_OFFSET = {"upper": 0, "trem": -10, "choir": -3, "horns": -9}   # relative to the section 'top' plan
CENTERS = {"upper": [57, 64, 70], "trem": [52, 57, 62], "choir": [55, 62, 68], "horns": [55, 60, 65]}


def choose_voicing(ch, prev, prev_bass, bass, ranges, centers, top=None):
    """Smallest-motion voicing that contains the essential chord tones.

    top: desired pitch of the highest voice (register plan of the section) or None.
    """
    n = len(ranges)
    req = set(ch["prio"][:min(n, len(ch["prio"]))])
    cands = [[p for p in range(lo, hi + 1) if p % 12 in ch["pcs"]] for lo, hi in ranges]
    if top is not None:
        centers = [c + (top - centers[-1]) for c in centers]
    best = None
    for v in itertools.product(*cands):
        if any(v[i] >= v[i + 1] or v[i + 1] - v[i] > 12 for i in range(n - 1)):
            continue
        s = {p % 12 for p in v}
        if not req <= s:
            continue
        if top is None:
            c = 0.12 * sum(abs(a - m) for a, m in zip(v, centers))
        else:
            c = 0.9 * abs(v[-1] - top) + 0.3 * sum(abs(a - m) for a, m in zip(v[:-1], centers[:-1]))
        if prev:
            c += sum(abs(a - b) for a, b in zip(v, prev)) * (1.0 if top is None else .6)
            pv, cv = [prev_bass] + list(prev), [bass] + list(v)
            for i in range(len(cv)):
                for j in range(i + 1, len(cv)):
                    i0, i1 = (pv[j] - pv[i]) % 12, (cv[j] - cv[i]) % 12
                    if i0 == i1 and i0 in (0, 7) and pv[i] != cv[i]:
                        c += 6
        if ch["third"] is not None and sum(1 for p in v if p % 12 == ch["third"]) > 1:
            c += 4
        if best is None or c < best[0]:
            best = (c, v)
    if best is None:   # relax: root + third only
        ch2 = dict(ch, prio=[x for x in ch["prio"] if x in (ch["root"], ch["third"])])
        return choose_voicing(ch2, prev, prev_bass, bass, ranges, centers, top)
    return list(best[1])


# ============================================================================ arrangement
class Arranger:
    def __init__(self, P):
        self.P = P
        self.rng = np.random.default_rng(SEED)
        self.notes = {k: [] for k in INST}       # inst -> [t0, t1, pitch, vel]
        self.extra_cc = {k: [] for k in INST}    # inst -> [(t, cc, val)]
        self.bends = {k: [] for k in INST}       # inst -> [(t, value)]
        self.mel_notes = {}                      # inst -> list for expression shaping
        self.chords = []                         # (t0, t1, chord, si, b0, b1)
        self.warnings = []

    # -------------------------------------------------- chord timeline
    def build_chords(self):
        for si, s in enumerate(self.P.segs):
            b = 0.0
            seq = parse_seq(s["sc"]["chords"])
            tot = sum(d for _, d in seq)
            if abs(tot - s["N"]) > 1e-6:
                raise ValueError("%s: chords sum to %.2f beats, N=%d" % (s["name"], tot, s["N"]))
            for ch, d in seq:
                self.chords.append((self.P.tb(si, b), self.P.tb(si, b + d), ch, si, b, b + d))
                b += d

    def chord_at(self, t):
        for c in self.chords:
            if c[0] <= t < c[1]:
                return c
        return self.chords[-1]

    # -------------------------------------------------- helpers
    def vel(self, level, jitter=5):
        return int(np.clip(38 + 72 * level + self.rng.normal(0, jitter / 2), 20, 124))

    def add(self, inst, t0, t1, p, v):
        if t1 - t0 > 0.02:
            self.notes[inst].append([t0, t1, int(p), int(v)])

    def active(self, layer, si, b):
        return self.P.layer_gain(si, layer, b) > 0

    def span_windows(self, layer, si, b0, b1):
        """Sub-spans of [b0,b1) where the layer is active (sampled every 1/8 beat)."""
        out, cur = [], None
        steps = max(1, int(round((b1 - b0) * 8)))
        for k in range(steps):
            bb = b0 + (b1 - b0) * k / steps
            on = self.active(layer, si, bb)
            if on and cur is None:
                cur = bb
            if not on and cur is not None:
                out.append((cur, bb)); cur = None
        if cur is not None:
            out.append((cur, b1))
        return out

    # -------------------------------------------------- bass / chords
    def arrange_harmony(self):
        P = self.P
        prev_bass, prev = 38, {}
        bass_line = []
        for (t0, t1, ch, si, b0, b1) in self.chords:
            cands = [p for p in range(36, 53) if p % 12 == ch["bass"]]
            bp_ = min(cands, key=lambda p: (abs(p - prev_bass), abs(p - 43)))
            bass_line.append(bp_)
            vo = {}
            topt = P.top(si, (b0 + b1) / 2)
            for fam in ("upper", "trem", "choir", "horns"):
                tt = None if topt is None else topt + TOP_OFFSET[fam]
                if fam == "choir" and tt is not None:
                    tt = min(tt, 77)
                vo[fam] = choose_voicing(ch, prev.get(fam), prev_bass, bp_, RANGES[fam], CENTERS[fam], tt)
            prev = vo
            prev_bass = bp_
            for layer in ("bass", "celli", "upper", "top8", "trem", "aahs", "oohs", "horns"):
                for w0, w1 in self.span_windows(layer, si, b0, b1):
                    ta, tb_ = P.tb(si, w0), P.tb(si, w1)
                    lv = P.dyn(si, w0) * P.layer_gain(si, layer, w0)
                    if layer == "bass":
                        p = bp_ - 12 if bp_ - 12 >= 26 else bp_
                        self.add("basses", ta, tb_, p, self.vel(lv))
                    elif layer == "celli":
                        self.add("celli", ta, tb_, bp_, self.vel(lv))
                    elif layer == "upper":
                        for inst, p in zip(("violas", "vln2", "vln1"), vo["upper"]):
                            off = abs(self.rng.normal(0, .012))
                            self.add(inst, ta + off, tb_, p, self.vel(lv))
                    elif layer == "top8":
                        p = vo["upper"][-1] + 12
                        if p <= 91:
                            self.add("vln_hi", ta, tb_, p, self.vel(lv))
                    elif layer == "trem":
                        for p in vo["trem"]:
                            self.add("trem", ta, tb_, p, self.vel(lv))
                        self.add("trem_lo", ta, tb_, bp_ if bp_ >= 36 else bp_ + 12, self.vel(lv))
                    elif layer in ("aahs", "oohs"):
                        cb = bp_ if bp_ >= 41 else bp_ + 12        # choir bass sings the bass line
                        for p in [cb] + vo["choir"]:
                            self.add(layer, ta + abs(self.rng.normal(0, .015)), tb_, p, self.vel(lv))
                    elif layer == "horns":
                        for p in vo["horns"]:
                            self.add("horns", ta, tb_, p, self.vel(lv))
        self.bass_line = bass_line

    def tie(self):
        """Merge touching notes of the same pitch (sustained pedals / common tones)."""
        for inst, ns in self.notes.items():
            if inst in ("timp", "bd", "kit", "harp", "celesta", "pizz"):
                continue
            ns.sort(key=lambda n: (n[2], n[0]))
            out = []
            for n in ns:
                if out and out[-1][2] == n[2] and abs(out[-1][1] - n[0]) < 0.03:
                    out[-1][1] = max(out[-1][1], n[1])
                else:
                    out.append(n)
            self.notes[inst] = sorted(out, key=lambda n: n[0])

    # -------------------------------------------------- harp / pizz
    def arrange_harp_pizz(self):
        P = self.P
        for k, (t0, t1, ch, si, b0, b1) in enumerate(self.chords):
            sc = P.segs[si]["sc"]
            div = sc.get("harp_div", 2)
            for w0, w1 in self.span_windows("harp", si, b0, b1):
                pcs = sorted(set(ch["pcs"]))
                tones = [p for p in range(50, 82) if p % 12 in pcs]
                bassn = self.bass_line[k]
                seq = [bassn if bassn >= 40 else bassn + 12] + tones[::1]
                bb = w0
                i = 0
                up = True
                while bb < w1 - 1e-6:
                    d = div if isinstance(div, (int, float)) else [v for (bx, v) in div if bx <= bb][-1]
                    step = 1.0 / d
                    lv = P.dyn(si, bb) * P.layer_gain(si, "harp", bb)
                    p = seq[i]
                    acc = 1.0 if abs(bb - round(bb)) < 1e-6 else .85
                    ta = P.tb(si, bb) + self.rng.normal(0, .006)
                    self.add("harp", ta, ta + 2.2, p, self.vel(lv * acc * .9))
                    # walk up the chord, then back down (gentle wave over ~2 octaves)
                    if up:
                        i += 1
                        if i >= min(len(seq) - 1, 7):
                            up = False
                    else:
                        i -= 1
                        if i <= 1:
                            up = True
                    bb += step
            for w0, w1 in self.span_windows("pizz", si, b0, b1):
                bb = w0
                bassn = self.bass_line[k]
                fifth = bassn + 7 if (bassn + 7) % 12 in ch["pcs"] else bassn + 12
                j = 0
                while bb < w1 - 1e-6:
                    lv = P.dyn(si, bb) * P.layer_gain(si, "pizz", bb)
                    p = bassn if j % 2 == 0 else fifth
                    ta = P.tb(si, bb)
                    self.add("pizz", ta, ta + .4, p + (12 if p < 40 else 0), self.vel(lv * (1 if j % 2 == 0 else .8)))
                    bb += .5
                    j += 1
        for si, s in enumerate(P.segs):
            for (kind, b, dur, direction) in s["sc"].get("harp", []):
                t0 = P.tb(si, b)
                t1 = P.tb(si, b + dur)
                ch = self.chord_at(t0 + .01)[2]
                tones = [p for p in range(43, 96) if p % 12 in ch["pcs"]]
                if direction == "down":
                    tones = tones[::-1]
                for i, p in enumerate(tones):
                    ta = t0 + (t1 - t0) * (i / len(tones)) ** 1.2
                    lv = .45 + .4 * i / len(tones)
                    self.add("harp", ta, ta + 2.5, p, self.vel(lv))

    # -------------------------------------------------- melodies
    def arrange_melodies(self):
        P = self.P
        for si, s in enumerate(P.segs):
            for (inst, start, text, gain) in s["sc"].get("mel", []):
                b = start
                for n in parse_mel(text):
                    if n["p"] is not None:
                        t0, t1 = P.tb(si, b), P.tb(si, b + n["d"])
                        self.check_note(inst, n["p"], si, b, n["d"], t0, t1)
                        lv = P.dyn(*P.beat_at(t0)) * gain
                        self.add(inst, t0, t1 + (.04 if inst not in ("celesta",) else 1.5), n["p"], self.vel(lv, 3))
                        self.mel_notes.setdefault(inst, []).append((t0, t1, n, lv))
                        if n["grace"] is not None:
                            self.add(inst, t0 - .085, t0 + .01, n["grace"], self.vel(lv * .9, 2))
                        if n["scoop"]:
                            self.bends[inst] += [(t0 - .002, -0.55), (t0 + .16, 0.0)]
                    b += n["d"]

    def check_note(self, inst, p, si, b, d, t0, t1):
        """Flag melody notes that sit more than ~half a beat on a chord they don't belong to."""
        if inst in ("tbn",):
            return
        bl = self.P.segs[si]["bl"]
        for (c0, c1, ch, *_r) in self.chords:
            ov = min(t1, c1) - max(t0, c0)
            if ov / bl > .55 and p % 12 not in ch["pcs"] and p % 12 != ch["bass"]:
                self.warnings.append("%s %s beat %.2f: %s over %s (%.2f beats)" % (
                    self.P.segs[si]["name"], inst, b, p, ch["sym"], ov / bl))

    # -------------------------------------------------- percussion
    def arrange_perc(self):
        P = self.P
        for si, s in enumerate(P.segs):
            for ev in s["sc"].get("perc", []):
                kind = ev[0]
                if kind in ("boom", "hit"):
                    b = P.anchor(si, ev[1])
                    t = P.tb(si, b)
                    v, p = ev[2], pitch(ev[3])
                    self.add("timp", t, t + 3.5, p, v)
                    if kind == "boom":
                        self.add("bd", t + .004, t + 3.5, 36, min(127, v))
                        self.add("timp", t + .01, t + 3.5, p - 12 if p - 12 >= 33 else p, int(v * .8))
                elif kind == "crash":
                    t = P.tb(si, ev[1])
                    self.add("kit", t, t + 3, 57, ev[2])
                    self.add("kit", t + .01, t + 3, 49, int(ev[2] * .8))
                elif kind == "roll":
                    _, b0, b1, v0, v1, note = ev
                    t0, t1 = P.tb(si, b0), P.tb(si, b1)
                    p = pitch(note)
                    t = t0
                    while t < t1:
                        u = (t - t0) / max(1e-6, t1 - t0)
                        v = v0 + (v1 - v0) * u ** 1.4
                        self.add("timp", t, t + .5, p, int(np.clip(v + self.rng.normal(0, 4), 8, 127)))
                        t += 1 / 15.0 + self.rng.normal(0, .004)
                elif kind == "heart":
                    _, b0, b1, bpm, v0, v1 = ev
                    t0, t1 = P.tb(si, b0), P.tb(si, b1)
                    per = 60.0 / bpm
                    t = t0 + .05
                    while t < t1 - .3:
                        u = (t - t0) / max(1e-6, t1 - t0)
                        v = v0 + (v1 - v0) * u
                        self.add("timp", t, t + 1.2, pitch("D2"), int(v))
                        self.add("bd", t + .003, t + 1.2, 36, int(v * .85))
                        self.add("timp", t + .26 * per / .85, t + 1.2, pitch("D2"), int(v * .62))
                        self.add("bd", t + .26 * per / .85, t + 1.2, 36, int(v * .5))
                        t += per

    # -------------------------------------------------- expression (CC2 / CC11 / CC1 curves)
    def expression(self):
        """Per-instrument dynamics automation, sampled every 40 ms."""
        P = self.P
        dt = .04
        ts = np.arange(0, P.total + 2, dt)
        seg_b = [P.beat_at(t) for t in ts]
        dyn = np.array([P.dyn(si, b) for si, b in seg_b])
        self.cc = {}
        for layer, insts in LAYER_INST.items():
            g = np.array([P.layer_gain(si, layer, b) for si, b in seg_b])
            g = dsp.smooth(g, .12, sr=1 / dt)
            lv = dyn * g
            for inst in insts:
                self.cc[inst] = (ts, lv)
        # melodic instruments: base level x note shape (messa di voce on long notes)
        for inst, ns in self.mel_notes.items():
            lv = np.zeros_like(ts)
            for (t0, t1, n, l) in ns:
                m = (ts >= t0 - .05) & (ts < t1 + .2)
                u = np.clip((ts[m] - t0) / max(.05, t1 - t0), 0, 1)
                long_ = (t1 - t0) > .8
                shape = .82 + .3 * np.sin(np.pi * u) ** 1.5 if long_ else np.ones_like(u)
                if long_:
                    shape *= np.where(u > .8, 1 - (u - .8) * 1.0, 1)
                lv[m] = np.maximum(lv[m], l * shape)
            lv = dsp.smooth(lv, .06, sr=1 / dt)
            if inst in self.cc:                      # e.g. vln_hi = octave doubling + melody
                lv = np.maximum(lv, self.cc[inst][1])
            self.cc[inst] = (ts, lv)
            vib = VIBRATO.get(inst, 0)
            if vib:
                for (t0, t1, n, l) in ns:
                    if t1 - t0 > .6:
                        self.extra_cc[inst] += [(t0, 1, 0), (t0 + .35, 1, int(vib * .3)),
                                                (t0 + .9, 1, vib), (t1, 1, int(vib * .6))]
                    else:
                        self.extra_cc[inst] += [(t0, 1, int(vib * .2))]

    # -------------------------------------------------- MIDI writing
    def write_midi(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        P = self.P
        end_t = P.total + 3.0
        paths = {}
        for stem in STEMS:
            ev = []          # (t, order, msg)
            for inst, (st, chn, bank, prog, expr, pan_, vol) in INST.items():
                if st != stem or (not self.notes[inst] and inst not in self.cc):
                    continue
                if not self.notes[inst]:
                    continue
                ev.append((0, 0, mido.Message("control_change", channel=chn, control=0, value=bank if chn != 9 else 0)))
                ev.append((0, 1, mido.Message("program_change", channel=chn, program=prog)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=7, value=vol)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=10, value=pan_)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=11, value=127)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=1, value=0)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=91, value=0)))
                ev.append((0, 2, mido.Message("control_change", channel=chn, control=93, value=0)))
                for t0, t1, p, v in self.notes[inst]:
                    ev.append((max(0, t0), 5, mido.Message("note_on", channel=chn, note=p, velocity=v)))
                    ev.append((max(0, t1), 3, mido.Message("note_off", channel=chn, note=p, velocity=0)))
                if inst in self.cc and expr:
                    ts, lv = self.cc[inst]
                    last = -1
                    for t, l in zip(ts, lv):
                        v = int(np.clip(round(8 + 119 * np.clip(l, 0, 1) ** .85), 0, 127))
                        if v != last:
                            ev.append((t, 4, mido.Message("control_change", channel=chn, control=2, value=v)))
                            last = v
                for (t, c, v) in self.extra_cc[inst]:
                    ev.append((max(0, t), 4, mido.Message("control_change", channel=chn, control=c, value=int(v))))
                for (t, semis) in self.bends[inst]:
                    val = int(np.clip(semis / 2.0 * 8191, -8192, 8191))
                    ev.append((max(0, t), 4, mido.Message("pitchwheel", channel=chn, pitch=val)))
                # final fade of the whole orchestra over the last seconds of the film
                for k in range(26):
                    t = P.total - 2.6 + k * .1
                    v = int(127 * (1 - k / 25) ** 1.5)
                    ev.append((t, 4, mido.Message("control_change", channel=chn, control=11, value=v)))
            if not ev:
                continue
            ev.append((end_t, 9, mido.Message("control_change", channel=15, control=7, value=0)))
            ev.sort(key=lambda e: (e[0], e[1]))
            mid = mido.MidiFile(ticks_per_beat=480)
            tr = mido.MidiTrack()
            mid.tracks.append(tr)
            tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))   # 960 ticks / s
            last = 0
            for t, _, m in ev:
                tick = int(round(t * 960))
                tr.append(m.copy(time=tick - last))
                last = tick
            path = os.path.join(outdir, stem + ".mid")
            mid.save(path)
            paths[stem] = path
        return paths


# ============================================================================ render + post
def render(paths, outdir):
    sf2 = SF2 if os.path.exists(SF2) else SF2_FALLBACK
    if sf2 != SF2:
        print("WARNING: %s missing, using %s" % (SF2, sf2))
    wavs = {}
    for stem, mid in paths.items():
        wav = os.path.join(outdir, "raw_%s.wav" % stem)
        cmd = ["fluidsynth", "-ni", "-q", "-R", "0", "-C", "0", "-r", str(SR), "-O", "float", "-T", "wav",
               "-g", "0.5", "-o", "synth.polyphony=512", "-F", wav, sf2, mid]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wavs[stem] = wav
    return wavs


def active_rms_db(x):
    m = np.mean(dsp.stereo(x) ** 2, 1)
    hop = SR // 10
    n = len(m) // hop
    e = m[:n * hop].reshape(n, hop).mean(1)
    if e.max() <= 0:
        return -120.0
    act = e[e > e.max() * 10 ** (-30 / 10)]
    return 10 * np.log10(np.mean(act) + 1e-20)


def post(wavs, total, outdir):
    stems = {}
    n = int(round(total * SR))
    irs = {}
    for stem, wav in wavs.items():
        x = dsp.stereo(dsp.read(wav))
        x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), 2))])
        fx = STEM_FX[stem]
        x = dsp.hp(x, 32, order=2)
        x = dsp.filt(x, "highshelf", 9000, gain_db=-2.5)     # tame GM sample fizz
        if stem == "perc":
            x = dsp.lp(x, 5000)
        key = fx["rt"]
        if key not in irs:
            irs[key] = dsp.hall_ir(rt60=key, predelay=.028, seed=int(key * 10))
        x = dsp.reverb(x, irs[key], wet=fx["wet"], dry=fx["dry"])
        g = dsp.undb(fx["level"] - 12 - active_rms_db(x))       # balance on active RMS
        stems[stem] = x * g
    mix = sum(stems.values())
    peak = np.max(np.abs(mix))
    norm = dsp.undb(-3) / peak                                 # leave headroom; mix.py sets loudness
    os.makedirs(os.path.join(outdir, "stems"), exist_ok=True)
    for stem, x in stems.items():
        x = dsp.fade(x * norm, 0.0, .05)
        dsp.write(os.path.join(outdir, "stems", "music_%s.wav" % stem), x)
        stems[stem] = x
    mix = dsp.fade(mix * norm, 0.0, .05)
    dsp.write(os.path.join(outdir, "music.wav"), mix)
    return mix, stems


def cue_sheet(P, A):
    cues = []
    for si, s in enumerate(P.segs):
        chords = [c[2]["sym"] for c in A.chords if c[3] == si]
        cues.append({"section": s["name"], "start": round(s["t0"], 3), "end": round(s["t1"], 3),
                     "beats": s["N"], "bpm": round(60 / s["bl"], 1), "chords": " ".join(chords),
                     "layers": sorted(s["sc"].get("layers", {}).keys()),
                     "solo": sorted({m[0] for m in s["sc"].get("mel", [])})})
    return {"climax": P.climax, "total": P.total, "sections": cues}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only build + check the arrangement")
    ap.add_argument("--keep-raw", action="store_true", help="keep the raw FluidSynth renders")
    a = ap.parse_args()
    T = dsp.load_timing()
    P = Plan(T)
    A = Arranger(P)
    A.build_chords()
    A.arrange_harmony()
    A.arrange_harp_pizz()
    A.arrange_melodies()
    A.arrange_perc()
    A.tie()
    A.expression()
    for w in A.warnings:
        print("CHECK:", w)
    for s in P.segs:
        print("%-6s %7.2f-%7.2f  %2d beats @ %5.1f bpm" % (s["name"], s["t0"], s["t1"], s["N"], 60 / s["bl"]))
    nn = sum(len(v) for v in A.notes.values())
    print("notes:", nn, {k: len(v) for k, v in A.notes.items() if v})
    if a.check:
        return
    mdir = os.path.join(OUT, "midi")
    paths = A.write_midi(mdir)
    wavs = render(paths, mdir)
    mix, stems = post(wavs, P.total, OUT)
    json.dump(cue_sheet(P, A), open(os.path.join(OUT, "music_cues.json"), "w"), indent=1)
    if not a.keep_raw:
        for w in wavs.values():
            os.remove(w)
    print("music.wav %.1f s, peak %.1f dBFS" % (len(mix) / SR, dsp.db(np.max(np.abs(mix)))))


if __name__ == "__main__":
    main()
