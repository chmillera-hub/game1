#!/usr/bin/env python3
"""music.py — the film's original score, rendered from the timeline with the FluidR3 GM soundfont.

    python3 audio/music.py                      # plan (if missing/stale) + render -> out/music.wav
    python3 audio/music.py --replan             # re-derive data/music_plan.json from the screenplay first
    python3 audio/music.py --plan-only          # just (re)write the plan
    python3 audio/music.py --timeline T.json --screenplay S.json --out out/music.wav --roll out/music_roll.png

Inputs: data/timeline.json (scene/beat times, dialogue, ^/~ word marks with absolute times),
        data/screenplay.json (scene `music` {mood, instrumentation, intensity}; ^/~ marks when the timeline is
        only an estimate), data/music_plan.json (the cue plan — derived automatically, hand-editable),
        data/music_hits.json + data/cues/*.json `hits` (comic hits), data/sfx_events.json-equivalent from
        tools/collect_sfx.py (auto hits: kick_thump -> stop-time, block_thunk -> wah-wah).
Outputs: out/music.wav (44.1 kHz stereo, -18 LUFS, ≤ -1 dBTP: bed + features),
         out/stems/music_bed.wav + out/stems/music_features.wav (float; bed + features = music.wav before
         limiting; mix.py ducks the bed under speech and the features — word-painting accents and comic hits —
         only lightly), data/music_report.json (cues, accents with their landing times, hits).

THE MUSIC (all original):
  Leitmotifs — JESUS "the reach" (F major: 1-6-5-3, a rising sixth that opens like arms, answered 2-3-5-2 /
  4-3-2-1); the VOID (D minor: 1-5-b6-5, a vast slow breath whose b6 sighs; it turns major/tender as 1-5-6-5
  — the same 6-5 sigh that ends Jesus's reach, so the two themes fit together and walk off as counterpoint);
  FEAR/anxiety (a skittering neighbour-note flicker 3-2-3-2-3 . 5; in Part Two it becomes Fear's own hopeful
  3-2-3-5 cell, a callback to the creator's earlier film, and blooms lydian among the galaxies).
  Keys — Part One lives in F major with the Void's D minor as its shadow (the same notes, darker centre);
  the bonus scene shifts to D (chromatic-mediant 'other world' at the dissolve): creepy D minor, then D major.
  Moods (18) = textures: chase, arrival, sly, sneaky, romp, dry, tender, sincere, exit, bittersweet, walkoff,
  hush, creep, still, suspense, slapstick, innocent, cosmos. Under speech every texture thins to pads, soft pulses
  and high pings; melodies only enter the gaps.
  Word-painting: every ^word gets a high bell (celesta/glock/harp, chord tone of the moment, its attack ON the
  word onset), every ~word a low note (contrabass + low piano + soft timpani on the current root).
  Hits: sting, stop (stop-time: the music cuts dead, optional orchestral stab), swell, wahwah (muted-trumpet
  wah-wah-wah-waah, or a one-note 'doink'), tada, creep, pluck, ping. A hit's time is a timeline ref/seconds or
  an SFX anchor {"sfx": "block_thunk", "scene": "s14"}; "until" sets its length.
"""
import argparse
import itertools
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audiolib as A  # noqa: E402

SR = A.SR
SF2 = os.path.join(ROOT, "models", "FluidR3_GM.sf2")
PRE, POST = 2.0, 4.0     # cue render padding (pickups before, release/fade after), seconds

# ============================================================================================
# pitch & chords

PCS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
       "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11}
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def midi(name):
    i = 2 if len(name) > 2 and name[1] in "#b" else 1
    return 12 * (int(name[i:]) + 1) + PCS[name[:i]]


def note_name(k):
    return f"{NAMES[k % 12]}{k // 12 - 1}"


def key_pc(key):
    k = key.strip()
    k = k[:-1] if k.endswith("m") and k[:-1] in PCS else k
    return PCS[k]


def fold(semi):
    semi %= 12
    return semi - 12 if semi > 5 else semi


QUAL = {
    "": [0, 4, 7], "6": [0, 4, 7, 9], "m": [0, 3, 7], "5": [0, 7], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9], "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "9": [0, 4, 7, 10, 14], "maj9": [0, 4, 7, 11, 14],
    "m9": [0, 3, 7, 10, 14], "add9": [0, 4, 7, 14], "m(add9)": [0, 3, 7, 14], "sus4": [0, 5, 7],
    "sus2": [0, 2, 7], "7sus4": [0, 5, 7, 10], "dim": [0, 3, 6], "m7b5": [0, 3, 6, 10], "7b9": [0, 4, 7, 10, 13],
    "13": [0, 4, 7, 10, 14, 21], "maj7#11": [0, 4, 7, 11, 18], "6/9": [0, 4, 7, 9, 14], "aug": [0, 4, 8],
    "9sus4": [0, 5, 7, 10, 14],
}
_CH_RE = re.compile(r"^([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?$")
_chord_cache = {}


def chord(name, shift=0):
    """'Bb/D' → dict(root pc, pcs list (root first, then by importance), bass pc, ivs)."""
    key = (name, shift)
    if key in _chord_cache:
        return _chord_cache[key]
    m = _CH_RE.match(name)
    if not m or m.group(2) not in QUAL:
        raise SystemExit(f"[music] unknown chord {name!r}")
    root = (PCS[m.group(1)] + shift) % 12
    ivs = QUAL[m.group(2)]
    bass = (PCS[m.group(3)] + shift) % 12 if m.group(3) else root
    c = dict(name=name, root=root, ivs=ivs, pcs=[(root + i) % 12 for i in ivs], bass=bass)
    _chord_cache[key] = c
    return c


def in_range(pc, lo, hi):
    return [k for k in range(lo, hi + 1) if k % 12 == pc]


def bass_of(c, lo=36, hi=48):
    ks = in_range(c["bass"], lo, hi)
    return ks[0] if ks else in_range(c["bass"], lo, hi + 12)[0]


def voice(c, lo, hi, n, prev=None):
    """Voice-led chord: n distinct notes in [lo, hi] from the chord's pcs; the 3rd and 7th (and the 9th if
    written) are kept, roots may be dropped when the bass has them; nearest to the previous voicing."""
    ivs = c["ivs"]
    pcs = c["pcs"]
    imp = []
    for i, iv in enumerate(ivs):
        r = iv % 12
        w = 3.0 if r in (3, 4) else 2.5 if r in (10, 11) else 1.6 if iv >= 13 else 1.2 if r in (5, 2, 9) else 1.0 if r == 0 else 0.6
        imp.append((pcs[i], w))
    cand = sorted(k for pc, _ in imp for k in in_range(pc, lo, hi))
    if len(cand) < n:
        n = max(1, len(cand))
    best, bc = None, 1e9
    pv = sorted(prev) if prev else None
    for combo in itertools.combinations(cand, n):
        got = {k % 12 for k in combo}
        cost = sum(w * 4.0 for pc, w in imp if pc not in got)
        cost += 3.0 * (n - len(got))
        gaps = np.diff(combo)
        cost += sum(1.5 for g in gaps if g == 1) + sum(0.4 for g in gaps if g == 2) + sum(0.3 * (g - 7) for g in gaps if g > 7)
        if pv and len(pv) == n:
            cost += 0.35 * sum(abs(a - b) for a, b in zip(combo, pv))
        else:
            cost += 0.15 * abs(np.mean(combo) - (lo + hi) / 2)
        if cost < bc:
            best, bc = combo, cost
    return list(best)


# ============================================================================================
# instruments (FluidR3 GM presets; bank 128 = drum kits). cal: reference key for loudness calibration
# (vel 64 → -24 dBFS RMS after EQ), perc: decaying sound (calibrate on the attack). level: dB trim.

INSTR = {
    "piano":    dict(prog=0, cal=62, perc=True, level=6, pan=-0.1, send=0.28, bus="hall", width=0.0, vmax=96,
                     eq=[("hp", 40), ("lp", 3200), ("ls", 220, 2.0), ("peak", 900, -1.5, 0.8)]),
    "lowpiano": dict(prog=0, cal=38, perc=True, level=4, pan=0.0, send=0.3, bus="hall", width=0.0, vmax=90,
                     eq=[("hp", 28), ("lp", 1800)]),
    "celesta":  dict(prog=8, cal=84, perc=True, level=2, pan=0.25, send=0.45, bus="vast", width=0.0, eq=[("hp", 300), ("lp", 9500)]),
    "glock":    dict(prog=9, cal=84, perc=True, level=-3, pan=0.18, send=0.35, bus="hall", width=0.0, vmax=78,
                     eq=[("hp", 400), ("lp", 8500), ("hs", 5000, -3)]),
    "musicbox": dict(prog=10, cal=81, perc=True, level=1, pan=0.15, send=0.4, bus="hall", width=0.0, eq=[("hp", 260), ("lp", 8000)]),
    "vibes":    dict(prog=11, cal=72, perc=True, level=2, pan=0.2, send=0.3, bus="hall", width=0.0, eq=[("hp", 150), ("lp", 7000)]),
    "marimba":  dict(prog=12, cal=72, perc=True, level=2, pan=0.15, send=0.2, bus="hall", width=0.0, eq=[("hp", 120), ("lp", 7000)]),
    "xylo":     dict(prog=13, cal=84, perc=True, level=4, pan=0.2, send=0.22, bus="hall", width=0.0, eq=[("hp", 300), ("lp", 8000)]),
    "harp":     dict(prog=46, cal=62, perc=True, level=4, pan=-0.25, send=0.4, bus="vast", width=0.0, eq=[("hp", 70), ("lp", 7500)]),
    "timpani":  dict(prog=47, cal=41, perc=True, level=-1, pan=0.0, send=0.35, bus="hall", width=0.0, eq=[("hp", 28), ("lp", 1300)]),
    "strings":  dict(prog=48, cal=62, level=-2, pan=0.05, send=0.32, bus="hall", width=0.2,
                     eq=[("hp", 60), ("lp", 5200), ("peak", 2800, -2.5, 1.0)]),
    "slowstr":  dict(prog=49, cal=62, level=-1.5, pan=0.0, send=0.36, bus="hall", width=0.25,
                     eq=[("hp", 60), ("lp", 5000), ("peak", 2800, -2.5, 1.0)]),
    "lowstr":   dict(prog=49, cal=43, level=-1, pan=-0.05, send=0.32, bus="hall", width=0.2, eq=[("hp", 30), ("lp", 1500)]),
    "tremolo":  dict(prog=44, cal=74, level=-6, pan=0.12, send=0.35, bus="hall", width=0.25, eq=[("hp", 200), ("lp", 5000)]),
    "pizz":     dict(prog=45, cal=55, perc=True, level=1, pan=-0.18, send=0.22, bus="hall", width=0.0, eq=[("hp", 55), ("lp", 4500)]),
    "pizzlow":  dict(prog=45, cal=40, perc=True, level=2, pan=-0.05, send=0.2, bus="hall", width=0.0, eq=[("hp", 35), ("lp", 2500)]),
    "upright":  dict(prog=32, cal=40, perc=True, level=1, pan=-0.05, send=0.15, bus="hall", width=0.0, eq=[("hp", 35), ("lp", 2500)]),
    "cello":    dict(prog=42, cal=50, level=3, pan=-0.15, send=0.33, bus="hall", width=0.1, eq=[("hp", 55), ("lp", 4200), ("peak", 2500, -2, 1)]),
    "contrabass": dict(prog=43, cal=33, level=2, pan=0.0, send=0.3, bus="hall", width=0.1, eq=[("hp", 28), ("lp", 1600)]),
    "violin":   dict(prog=40, cal=79, level=-3, pan=0.15, send=0.38, bus="hall", width=0.15, eq=[("hp", 250), ("lp", 6000), ("peak", 3000, -3, 1)]),
    "choir":    dict(prog=52, cal=67, level=-4, pan=0.0, send=0.5, bus="vast", width=0.3, eq=[("hp", 160), ("lp", 5200)]),
    "horns":    dict(prog=60, cal=55, level=-1, pan=0.12, send=0.4, bus="hall", width=0.15, eq=[("hp", 50), ("lp", 2600)]),
    "tuba":     dict(prog=58, cal=36, level=-4, pan=0.05, send=0.18, bus="hall", width=0.0, eq=[("hp", 30), ("lp", 1500)]),
    "mtrumpet": dict(prog=59, cal=64, level=3, pan=0.15, send=0.25, bus="hall", width=0.0, eq=[("hp", 180), ("lp", 4500)]),
    "flute":    dict(prog=73, cal=76, level=0, pan=0.2, send=0.35, bus="hall", width=0.05, eq=[("hp", 250), ("lp", 7000)]),
    "clarinet": dict(prog=71, cal=55, level=-2, pan=0.22, send=0.28, bus="hall", width=0.05, eq=[("hp", 110), ("lp", 4500)]),
    "bassoon":  dict(prog=70, cal=46, level=0, pan=-0.12, send=0.25, bus="hall", width=0.05, eq=[("hp", 50), ("lp", 3500)]),
    "pad":      dict(prog=89, cal=62, level=-6, pan=0.0, send=0.3, bus="hall", width=0.35, eq=[("hp", 80), ("lp", 2600)]),
    "glass":    dict(prog=92, cal=79, level=-3, pan=0.0, send=0.5, bus="vast", width=0.45, eq=[("hp", 250), ("lp", 6500)]),
    "space":    dict(prog=91, cal=62, level=-6, pan=0.0, send=0.5, bus="vast", width=0.45, eq=[("hp", 150), ("lp", 3500)]),
    "kit":      dict(prog=0, bank=128, drums=True, cal=76, perc=True, level=-6, pan=0.1, send=0.18, bus="hall", width=0.0,
                     eq=[("hp", 60), ("lp", 8000)]),
    "brushkit": dict(prog=40, bank=128, drums=True, cal=38, perc=True, level=-10, pan=0.05, send=0.2, bus="hall", width=0.0,
                     eq=[("hp", 120), ("lp", 7000)]),
    "orchkit":  dict(prog=48, bank=128, drums=True, cal=57, perc=True, level=-12, pan=0.0, send=0.35, bus="hall", width=0.0,
                     eq=[("hp", 40), ("lp", 9000), ("hs", 6000, -3)]),
}
# drum keys (GM)
WB_HI, WB_LO, TRI_OPEN, TRI_MUTE, BRUSH_SN, BRUSH_SWIRL, KICK, CRASH, RIDE, CLAVES = 76, 77, 81, 80, 38, 40, 36, 49, 51, 75

# ============================================================================================
# leitmotifs & phrases — (onset beats, dur beats, note) in their `ref` key; `ch` = harmonisation (beat, chord)
PHRASES = {
    # JESUS — "the reach": 1-6-5-3 (rising sixth), answered 2-3-5-2 (half cadence) / 4-3-2-1 (home)
    "jesus":       dict(ref="F", stem="piano", n=[(0, 1, "F4"), (1, 1.5, "D5"), (2.5, .5, "C5"), (3, 1, "A4"), (4, .5, "G4"),
                                                  (4.5, .5, "A4"), (5, 1, "C5"), (6, 2.5, "G4")],
                        ch=[(0, "F"), (2, "Dm7"), (4, "C/E"), (6, "C7sus4")]),
    "jesus_b":     dict(ref="F", stem="piano", n=[(0, 1, "F4"), (1, 1.5, "D5"), (2.5, .5, "C5"), (3, 1, "A4"), (4, .5, "Bb4"),
                                                  (4.5, .5, "A4"), (5, 1, "G4"), (6, 2.5, "F4")],
                        ch=[(0, "F"), (2, "Dm7"), (4, "Gm7"), (5, "C7"), (6, "Fadd9")]),
    "jesus_short": dict(ref="F", stem="piano", n=[(0, 1, "F4"), (1, 1.5, "D5"), (2.5, .5, "C5"), (3, 2, "A4")],
                        ch=[(0, "F"), (2.5, "Dm7")]),
    "jesus_cell":  dict(ref="F", stem="piano", n=[(0, 1, "F4"), (1, 2.5, "D5")], ch=[(0, "F6")]),
    "jesus_cad":   dict(ref="F", stem="piano", n=[(0, .5, "Bb4"), (.5, .5, "A4"), (1, 1, "G4"), (2, 3, "F4")],
                        ch=[(0, "Gm7"), (1, "C7"), (2, "Fadd9")]),
    # THE VOID — 1-5-b6-5 (vast breath, sighing b6); tender 1-5-6-5; sad (borrowed b6); blooming (opens to 3)
    "void":        dict(ref="Dm", stem="cello", n=[(0, 2, "D3"), (2, 2, "A3"), (4, 1.5, "Bb3"), (5.5, 2.5, "A3")],
                        ch=[(0, "Dm"), (4, "Bb"), (5.5, "Dm/A")]),
    "void_cell":   dict(ref="Dm", stem="cello", n=[(0, 1.5, "D3"), (1.5, 3, "A3")], ch=[(0, "Dm")]),
    "void_sigh":   dict(ref="F", stem="cello", n=[(0, 1.5, "D4"), (1.5, 3, "C4")], ch=[(0, "Dm7"), (1.5, "F/C")]),
    "void_tender": dict(ref="F", stem="cello", n=[(0, 2, "F3"), (2, 2, "C4"), (4, 1.5, "D4"), (5.5, 2.5, "C4")],
                        ch=[(0, "F"), (4, "Dm7"), (5.5, "F/C")]),
    "void_sad":    dict(ref="F", stem="cello", n=[(0, 2, "F3"), (2, 2, "C4"), (4, 1.5, "Db4"), (5.5, 2.5, "C4")],
                        ch=[(0, "F"), (4, "Bbm6"), (5.5, "F/C")]),
    "void_bloom":  dict(ref="D", stem="horns", n=[(0, 2, "D4"), (2, 2, "A4"), (4, 1.5, "B4"), (5.5, 1, "A4"), (6.5, 3.5, "F#4")],
                        ch=[(0, "Dadd9"), (4, "Gmaj7"), (5.5, "D/A"), (6.5, "Bm7")]),
    # FEAR / anxiety — skittering neighbour flicker; Fear's own 3-2-3-5 (callback), its question and wonder
    "skitter":     dict(ref="Dm", stem="flute", n=[(0, .25, "F5"), (.25, .25, "E5"), (.5, .25, "F5"), (.75, .25, "E5"),
                                                   (1, .5, "F5"), (1.75, 1.25, "A5")], ch=[(0, "Dm")]),
    "skitter_maj": dict(ref="D", stem="flute", n=[(0, .25, "F#5"), (.25, .25, "E5"), (.5, .25, "F#5"), (.75, .25, "E5"),
                                                  (1, .5, "F#5"), (1.75, 1.25, "A5")], ch=[(0, "D")]),
    "fear_hope":   dict(ref="D", stem="celesta", n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1, "F#5"), (2, 1, "A5"), (3, 1, "B5"),
                                                    (4, 2.5, "A5")], ch=[(0, "Dadd9"), (2, "Bm7"), (3, "Gadd9")]),
    "fear_hope_short": dict(ref="D", stem="celesta", n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1, "F#5"), (2, 2, "A5")],
                            ch=[(0, "Dadd9"), (2, "Bm7")]),
    "fear_question": dict(ref="D", stem="flute", n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1.5, "F#5"), (2.5, 2, "B5")],
                          ch=[(0, "D"), (2.5, "G6")]),
    "fear_wonder": dict(ref="D", stem="celesta", n=[(0, .5, "F#5"), (.5, .5, "E5"), (1, 1, "F#5"), (2, 1, "A5"), (3, 1.5, "G#5"),
                                                    (4.5, 2.5, "A5")], ch=[(0, "Dmaj9"), (3, "E/D"), (4.5, "Dmaj9")]),
    "whome":       dict(ref="D", stem="bassoon", n=[(0, .4, "A2"), (.75, 1.6, "E3")], ch=[(0, "D")]),
    # sly / creeping / comic comments
    "sly":         dict(ref="Dm", stem="clarinet", n=[(0, .5, "A4"), (.5, .5, "G#4"), (1, .5, "A4"), (1.5, .5, "C5"), (2, 1, "B4"),
                                                      (3, .5, "A4"), (3.5, .5, "F4"), (4, 2, "D4")],
                        ch=[(0, "Dm7"), (2, "G9"), (4, "Dm7")]),
    "sly_short":   dict(ref="Dm", stem="clarinet", n=[(0, .5, "A4"), (.5, .5, "G#4"), (1, .5, "A4"), (1.5, 1.5, "D4")],
                        ch=[(0, "Dm7")]),
    "creep":       dict(ref="Dm", stem="clarinet", n=[(0, .5, "D4"), (.5, .5, "Eb4"), (1, .5, "D4"), (1.5, .5, "C#4"), (2, 1, "D4"),
                                                      (3, .5, "F4"), (3.5, .5, "E4"), (4, 1, "Eb4"), (5, 2, "D4")],
                        ch=[(0, "Dm"), (4, "Eb/D"), (5, "Dm")]),
    "creep_short": dict(ref="Dm", stem="clarinet", n=[(0, .5, "D4"), (.5, .5, "Eb4"), (1, .5, "D4"), (1.5, .5, "C#4"), (2, 1.5, "D4")],
                        ch=[(0, "Dm")]),
    "grumble":     dict(ref="Dm", stem="bassoon", n=[(0, .5, "D3"), (.5, .5, "E3"), (1, .5, "F3"), (1.5, .5, "E3"), (2, 1, "D3"),
                                                     (3, 1, "A2")], ch=[(0, "Dm"), (3, "A7")]),
    "romp_tune":   dict(ref="F", stem="bassoon", n=[(0, .5, "F3"), (.5, .5, "C3"), (1, .5, "D3"), (1.5, .5, "C3"), (2, .5, "F3"),
                                                    (2.5, .5, "A3"), (3, 1, "C4")], ch=[(0, "F"), (3, "C7")]),
    "glock_run":   dict(ref="F", stem="glock", n=[(0, .5, "C6"), (.25, .5, "D6"), (.5, .5, "F6"), (.75, .5, "G6"), (1, .5, "A6"),
                                                  (1.25, 1.2, "C7")], ch=[]),
    "bwomp":       dict(ref="F", stem="bassoon", n=[(0, .4, "C3"), (.6, 1.3, "F2")], ch=[]),
    "plink":       dict(ref="F", stem="pizz", n=[(0, .3, "C5"), (.5, .6, "F4")], ch=[]),
    "shrug":       dict(ref="F", stem="pizz", n=[(0, .25, "A4"), (.5, .25, "C5"), (1, .6, "F4")], ch=[]),
}
for _nm, _P in PHRASES.items():
    _P.setdefault("name", _nm)

# rhythmic patterns: (beat position, chord-tone index, velocity multiplier)
PAT = {
    "arp_q": [(0, 0, 1.0), (1, 1, .75), (2, 2, .85), (3, 1, .72)],
    "arp_8": [(0, 0, 1.0), (.5, 1, .62), (1, 2, .75), (1.5, 1, .6), (2, 3, .82), (2.5, 2, .6), (3, 1, .72), (3.5, 2, .58)],
    "arp_8up": [(0, 0, 1.0), (.5, 1, .65), (1, 2, .72), (1.5, 3, .66), (2, 4, .8), (2.5, 3, .62), (3, 2, .7), (3.5, 1, .6)],
    "skitter8": [(0, 0, 1.0), (.5, 2, .55), (1, 1, .8), (1.5, 2, .55), (2, 0, .9), (2.5, 2, .55), (3, 1, .8), (3.5, 2, .6)],
    "offbeats": [(.5, 0, .9), (1.5, 0, .8), (2.5, 0, .9), (3.5, 0, .8)],
    "twofour": [(1, 0, 1.0), (3, 0, .9)],
    "tiptoe": [(0, 0, 1.0), (1.5, 1, .7), (2.5, 0, .78), (3.5, 1, .6)],
    "plod": [(0, 0, 1.0), (1, 1, .8), (2, 2, .9), (3, 1, .8)],
    "oompah": [(0, 0, 1.0), (2, 1, .85)],
    "stomp": [(0, 0, 1.0), (1, 0, .7), (2, 0, .9), (3, 0, .7)],
    "tick": [(0, 0, 1.0), (1, 0, .8), (2, 0, .9), (3, 0, .8)],
}

# ============================================================================================
# moods: reference key, tempo, progression (chord, beats), loudness trim (dB), family, accent colour

MOODS = {
    "chase":       dict(key="Dm", bpm=112, db=-3, fam="comic", hi="glock",
                        prog=[("Dm", 4), ("Bb/D", 4), ("Gm/D", 4), ("A7", 4)]),
    "arrival":     dict(key="F", bpm=72, db=-1, fam="lyrical", hi="celesta",
                        prog=[("Fadd9", 4), ("Dm7", 4), ("Bbmaj7", 4), ("C7sus4", 2), ("C7", 2)]),
    "sly":         dict(key="Dm", bpm=96, db=-3, fam="comic", hi="glock",
                        prog=[("Dm7", 4), ("G9", 4), ("Dm7", 4), ("G13", 2), ("A7b9", 2)]),
    "sneaky":      dict(key="Dm", bpm=88, db=-3, fam="comic", hi="glock",
                        prog=[("Dm", 4), ("Dm/C", 4), ("Bbmaj7", 4), ("A7", 4)]),
    "romp":        dict(key="F", bpm=126, db=-3, fam="comic", hi="glock",
                        prog=[("F", 4), ("C7", 4), ("F", 4), ("Bb", 4), ("F/C", 4), ("C7", 4), ("F", 4), ("F", 4)]),
    "dry":         dict(key="F", bpm=84, db=-2, fam="sparse", hi="celesta", prog=[("Fadd9", 8), ("Dm9", 8)]),
    "tender":      dict(key="F", bpm=66, db=0, fam="lyrical", hi="harp",
                        prog=[("F", 4), ("C/E", 4), ("Dm7", 4), ("Bbmaj7", 4), ("F/A", 4), ("Gm7", 4), ("C7sus4", 2), ("C7", 2)]),
    "sincere":     dict(key="F", bpm=68, db=0, fam="lyrical", hi="harp",
                        prog=[("F", 4), ("Am7", 4), ("Bbmaj7", 4), ("C7sus4", 4), ("Dm7", 4), ("Bbmaj7", 4), ("Gm7", 4), ("C7", 4)]),
    "exit":        dict(key="Dm", bpm=108, db=-3, fam="comic", hi="glock",
                        prog=[("Dm", 4), ("Gm/Bb", 4), ("A7", 4), ("Dm", 4)]),
    "bittersweet": dict(key="F", bpm=63, db=0, fam="lyrical", hi="harp",
                        prog=[("F", 4), ("Am/E", 4), ("Dm7", 4), ("Bbm6", 4), ("F/C", 4), ("C7sus4", 4)]),
    "walkoff":     dict(key="F", bpm=84, db=-1, fam="lyrical", hi="celesta", swing=True,
                        prog=[("F", 4), ("Dm7", 4), ("Gm7", 4), ("C7", 4), ("Am7", 4), ("Dm7", 4), ("Gm7", 4), ("C7", 4)]),
    "hush":        dict(key="D", bpm=66, db=-1, fam="lyrical", hi="celesta",
                        prog=[("Dadd9", 4), ("Bm(add9)", 4), ("Gmaj7", 4), ("Asus4", 2), ("A", 2)]),
    "creep":       dict(key="Dm", bpm=80, db=-3, fam="dark", hi="glock",
                        prog=[("Dm", 4), ("Eb/D", 4), ("Dm", 4), ("A7b9", 4)]),
    "suspense":    dict(key="Dm", bpm=72, db=-2, fam="dark", hi="celesta", prog=[("Dm(add9)", 8), ("Bbmaj7#11", 8)]),
    "slapstick":   dict(key="Dm", bpm=84, db=-3, fam="comic", hi="glock",
                        prog=[("Dm", 4), ("Gm/D", 4), ("Dm", 4), ("A7", 4)]),
    "innocent":    dict(key="D", bpm=76, db=-2, fam="sparse", hi="celesta",
                        prog=[("D", 4), ("G/D", 4), ("D", 4), ("A7sus4", 4)]),
    "still":       dict(key="Dm", bpm=60, db=0, fam="dark", hi="celesta", prog=[("Dm(add9)", 8), ("Bbmaj7", 8)]),
    "cosmos":      dict(key="D", bpm=63, db=-2, fam="lyrical", hi="celesta",
                        prog=[("Dmaj7", 4), ("Bm7", 4), ("Gmaj9", 4), ("A7sus4", 2), ("A7", 2), ("F#m7", 4), ("Bm7", 4),
                              ("Gmaj7", 4), ("Asus4", 2), ("A", 2)]),
}
# cue loudness targets (LUFS of the cue's dry sum, before the whole score is normalised): every cue is
# calibrated to its mood's target + 5 dB per unit of intensity above 0.4 (±2.5 dB), so hand-edited moods,
# keys and densities keep a consistent dramatic level. Swells/ramps inside a cue are kept.
TARGET = {"chase": -20.0, "arrival": -20.5, "sly": -24.0, "sneaky": -24.0, "romp": -19.5, "dry": -29.0, "tender": -22.0,
          "sincere": -21.5, "exit": -22.5, "bittersweet": -23.0, "walkoff": -21.0, "hush": -24.0, "creep": -24.0,
          "suspense": -25.0, "slapstick": -24.0, "innocent": -25.0, "cosmos": -18.5, "still": -28.0}
CADENCE = {"F": [("Gm7", 2), ("C7sus4", 1), ("C7", 1)], "D": [("Em7", 2), ("A7sus4", 1), ("A7", 1)],
           "Dm": [("Gm7", 2), ("A7sus4", 1), ("A7", 1)]}
FINAL = {"F": "Fadd9", "D": "Dadd9", "Dm": "Dm(add9)"}
QUIET_VOCALS = {"whisper", "mmhm", "sigh", "hum", "gasp", "whimper", "gulp"}

# ============================================================================================
# synth


class Synth:
    def __init__(self, sf2=SF2):
        import tinysoundfont as tsf
        self.syn = tsf.Synth(samplerate=SR, gain=0)
        self.sfid = self.syn.sfload(sf2, max_voices=256)
        self.cal = {}

    def render(self, ins, events, n):
        """events: (sample, kind, key, val): kind 1 = on, 0 = off, 2 = pitch bend (val 0..16383)."""
        s = self.syn
        s.sounds_off()
        s.generate(4096)
        s.program_select(0, self.sfid, ins.get("bank", 0), ins["prog"], is_drums=ins.get("drums", False))
        s.pitchbend(0, 8192)
        s.pitchbend_range(0, 2.0)
        out = np.zeros((n, 2), dtype=np.float32)
        pos = 0
        for idx, kind, key, val in sorted(events, key=lambda e: (e[0], e[1])):
            idx = int(min(max(idx, 0), n))
            if idx > pos:
                out[pos:idx] = np.frombuffer(s.generate(idx - pos), dtype=np.float32).reshape(-1, 2)
                pos = idx
            if kind == 1:
                s.noteon(0, int(key), int(max(1, min(127, val))))
            elif kind == 0:
                s.noteoff(0, int(key))
            else:
                s.pitchbend(0, int(val))
        if pos < n:
            out[pos:] = np.frombuffer(s.generate(n - pos), dtype=np.float32).reshape(-1, 2)
        s.notes_off()
        s.sounds_off()
        s.pitchbend(0, 8192)
        return out

    def calibration(self, name):
        if name not in self.cal:
            ins = INSTR[name]
            n = int(1.6 * SR)
            x = A.eq_chain(self.render(ins, [(0, 1, ins["cal"], 64), (int(1.2 * SR), 0, ins["cal"], 0)], n), ins["eq"])
            seg = x[: int(0.5 * SR)] if ins.get("perc") else x[int(0.4 * SR): int(1.2 * SR)]
            self.cal[name] = float(A.db2lin(-24.0)) / float(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        return self.cal[name]


# ============================================================================================
# cue model


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


class Cue:
    def __init__(self, spec, idx, ctx, seed=0):
        self.spec, self.idx = spec, idx
        self.start, self.end = float(spec["start"]), float(spec["end"])
        self.D = self.end - self.start
        self.mood = spec["mood"]
        if self.mood not in MOODS:
            raise SystemExit(f"[music] unknown mood {self.mood!r} (choose from {', '.join(MOODS)})")
        self.M = MOODS[self.mood]
        self.ref = self.M["key"]
        self.key = spec.get("key") or self.ref
        self.shift = fold(key_pc(self.key) - key_pc(self.ref))
        self.tonic = (key_pc(self.ref) + self.shift) % 12
        self.minor = self.ref.endswith("m")
        self.I = float(np.clip(spec.get("intensity", 0.35), 0.0, 1.0))
        self.ramp = spec.get("ramp") or [[0, 1.0], [1, 1.0]]
        self.bpm = float(spec.get("bpm") or self.M["bpm"])
        self.beat = 60.0 / self.bpm
        self.swing = bool(spec.get("swing", self.M.get("swing", False)))
        self.rng = np.random.default_rng(7919 * (idx + 1) + 104729 * seed + sum(map(ord, self.mood)))
        loc = lambda iv: [(a - self.start, b - self.start) for a, b in iv if b > self.start - 1 and a < self.end + 1]
        self.speech = loc(ctx["speech"])
        self.quiet = loc(ctx["quiet"])
        self.vocal_events = [(t - self.start, kind, spk) for t, kind, spk in ctx["vocal_events"] if self.start <= t < self.end]
        self.lines = [(a - self.start, b - self.start, spk, txt) for a, b, spk, txt in ctx.get("lines", []) if self.start <= a < self.end]
        self.hits = [dict(h, lt=h["t"] - self.start) for h in ctx["hits"] if self.start - 0.01 <= h["t"] < self.end]
        self.stops = [(h["lt"], h["lt"] + h.get("len", 2.5)) for h in self.hits if h["kind"] == "stop"]
        self.swells = [(h["lt"], float(h.get("len", 4.0))) for h in self.hits if h["kind"] == "swell"]
        self.phrase_iv, self.blocked = [], []
        self.layers_off = set(spec.get("layers_off", []))
        self.melody_stem = spec.get("melody_stem")
        self.trans = spec.get("transition_in", "crossfade")
        self.trans_out = spec.get("transition_out", "crossfade")
        self.ending = bool(spec.get("ending"))
        self.end_at = None
        self.notes = []

    # queries (local seconds)
    def speech_at(self, t, pre=0.25, post=0.15):
        return any(a - pre <= t <= b + post for a, b in self.speech + self.quiet)

    def line_at(self, t, pre=0.2, post=0.1):
        return any(a - pre <= t <= b + post for a, b in self.speech)

    def stopped(self, t):
        return any(a - 0.01 <= t < b for a, b in self.stops)

    def in_phrase(self, t, pad=0.15):
        return any(a - pad <= t <= b + pad for a, b in self.phrase_iv)

    def I_at(self, t):
        r = np.array(self.ramp, dtype=float)
        v = self.I * float(np.interp(t / max(self.D, 1e-6), r[:, 0], r[:, 1]))
        for ts, ln in self.swells:
            v += 0.3 * float(_smooth((t - ts) / max(ln, 0.1)))
        return float(np.clip(v, 0.0, 1.0))

    def gaps(self, lead=0.5, tail=0.6, pre=0.3, post=0.25, min_len=0.3):
        lo, hi = lead, (self.end_at if self.end_at is not None else self.D) - tail
        if hi <= lo:
            return []
        blocks = sorted([(a - pre, b + post) for a, b in self.speech + self.quiet] + list(self.stops)
                        + [(a - 0.3, b + 0.3) for a, b in self.blocked])
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
        return [(a, b) for a, b in out if b - a > min_len]


class Writer:
    def __init__(self, cue):
        self.cue = cue
        self.notes = []   # (stem, t, dur, key, vel)
        self.bends = []   # (stem, t, value)
        self.auto = {}    # stem -> [(t, dB)]

    def add(self, stem, t, dur, key, vel, jitter=0.006, force=False):
        c = self.cue
        if not force and (t < -0.001 or t >= c.D - 0.05 or c.stopped(t)):
            return
        if jitter:
            t = t + float(np.clip(c.rng.normal(0, jitter), -2.5 * jitter, 2.5 * jitter))
            vel = vel + float(c.rng.integers(-3, 4))
        k = int(key)
        while k < 21:
            k += 12
        while k > 108:
            k -= 12
        v = int(np.clip(round(vel), 1, INSTR[stem.split("#")[0]].get("vmax", 112)))
        self.notes.append((stem, float(t), float(max(0.05, dur)), k, v))

    def vel(self, base, t, lo=0.6, hi=0.8):
        i = self.cue.I_at(t)
        return base * (lo + hi * i) / (lo + hi * 0.4)


# ============================================================================================
# form: harmony timeline + bar grid


def build_form(cue):
    M = cue.M
    beat = cue.beat
    harm, t, i = [], 0.0, 0
    prog = [(chord(c, cue.shift), b) for c, b in (cue.spec.get("prog") and [(x[0], x[1]) for x in cue.spec["prog"]] or M["prog"])]
    while t < cue.D + 4 * beat:
        ch, nb = prog[i % len(prog)]
        harm.append([t, t + nb * beat, ch])
        t += nb * beat
        i += 1
    grid = []
    t = 0.0
    while t < cue.D:
        grid.append(t)
        t += 4 * beat
    if cue.ending:
        last_speech = max([b for a, b in cue.speech + cue.quiet if a < cue.D] + [0.0])
        ea = max(last_speech + 0.6, cue.D - float(cue.spec.get("ending_hold", 6.0)))
        ea = grid[0] + math.ceil((ea - grid[0]) / beat - 1e-6) * beat
        ea = min(ea, cue.D - 2.5)
        if ea > 4 * beat:
            cue.end_at = ea
            cad = CADENCE.get(cue.ref.rstrip("m") if not cue.minor else cue.ref, CADENCE["F"])
            cad = [(chord(c, cue.shift), b) for c, b in cad]
            tc = ea - sum(b for _, b in cad) * beat
            new = [list(h) for h in harm if h[0] < tc - 1e-6]
            if new:
                new[-1][1] = tc
            tt_ = tc
            for c, b in cad:
                new.append([tt_, tt_ + b * beat, c])
                tt_ += b * beat
            new.append([ea, cue.D + 8, chord(FINAL.get(cue.ref, "Fadd9"), cue.shift)])
            harm[:] = new
    return harm, grid


def chord_at(harm, t):
    for a, b, c in harm:
        if a - 1e-6 <= t < b:
            return c
    return harm[-1][2] if harm else None


def patch_harmony(harm, t0, t1, chords):
    out = []
    for a, b, c in harm:
        if b <= t0 or a >= t1:
            out.append([a, b, c])
        else:
            if a < t0:
                out.append([a, t0, c])
            if b > t1:
                out.append([t1, b, c])
    for i, (t, c) in enumerate(chords):
        te = chords[i + 1][0] if i + 1 < len(chords) else t1
        if te > t:
            out.append([t, te, c])
    out.sort(key=lambda h: h[0])
    harm[:] = out


# ============================================================================================
# texture helpers


def pad(w, harm, stem, lo, hi, n, vel, min_I=0.0, overlap=0.2, until=None, top=False):
    """Sustained voice-led chords; common tones tie across chord changes."""
    cue = w.cue
    active, prev = {}, None
    end_lim = cue.D if until is None else until
    for a, b, c in harm:
        if a >= end_lim:
            break
        b = min(b, end_lim)
        keys = set()
        if cue.I_at(a) >= min_I and not cue.stopped(a + 0.01):
            vs = voice(c, lo, hi, n, prev)
            prev = vs
            keys = set(vs[-1:] if top else vs)
        for k in list(active):
            if k not in keys:
                s0, v0 = active.pop(k)
                w.add(stem, s0, a + overlap - s0, k, v0, jitter=0, force=True)
        for j, k in enumerate(sorted(keys)):
            if k not in active:
                active[k] = (max(0.0, a) + 0.03 * j * float(cue.rng.random()), w.vel(vel, a))
    tend = min(end_lim, cue.D) + overlap
    for k, (s0, v0) in active.items():
        w.add(stem, s0, tend - s0, k, v0, jitter=0, force=True)


def bass_hold(w, harm, stem, lo, hi, vel, min_I=0.0, octave_up=False):
    cue = w.cue
    for a, b, c in harm:
        if a >= cue.D or cue.I_at(a) < min_I:
            continue
        k = bass_of(c, lo, hi)
        w.add(stem, max(0.0, a), min(b, cue.D) - max(0.0, a) + 0.15, k, w.vel(vel, a), jitter=0)
        if octave_up:
            w.add(stem, max(0.0, a), min(b, cue.D) - max(0.0, a) + 0.15, k + 12, w.vel(vel * 0.7, a), jitter=0)


def swing_pos(cue, pos):
    if cue.swing and abs(pos % 1 - 0.5) < 1e-6:
        return pos + 1 / 6.0
    return pos


def pattern(w, harm, grid, stem, pat, pool, vel, dur=0.5, speech="thin", thin=(0, 2), min_I=0.0, every=1,
            skip_phrase=False, max_t=None, min_t=0.0, quiet_scale=0.7):
    """A rhythmic figure on the bar grid. pool(chord) -> list of keys (low→high) indexed by the pattern."""
    cue = w.cue
    pat = PAT[pat] if isinstance(pat, str) else pat
    lim = cue.end_at if (cue.end_at is not None and max_t is None) else (max_t if max_t is not None else cue.D)
    for bi, g in enumerate(grid):
        if bi % every:
            continue
        for pos, idx, vm in pat:
            t = g + swing_pos(cue, pos) * cue.beat
            if t < min_t or t >= lim or cue.I_at(t) < min_I:
                continue
            c = chord_at(harm, t)
            sp = cue.speech_at(t)
            if sp and speech == "gap":
                continue
            v = w.vel(vel, t) * vm
            if sp and speech == "thin":
                if pos not in thin:
                    continue
                v *= quiet_scale
            if skip_phrase and cue.in_phrase(t):
                continue
            ks = pool(c)
            if not ks:
                continue
            k = ks[idx % len(ks)] + 12 * (idx // len(ks))
            w.add(stem, t, dur * cue.beat, k, v)


def perc(w, grid, stem, pat, vel, speech="thin", thin=(), min_I=0.0, every=1, max_t=None):
    """pat: [(pos, drum_key, vel_mul)]"""
    cue = w.cue
    lim = cue.end_at if (cue.end_at is not None and max_t is None) else (max_t if max_t is not None else cue.D)
    for bi, g in enumerate(grid):
        if bi % every:
            continue
        for pos, key, vm in pat:
            t = g + swing_pos(cue, pos) * cue.beat
            if t >= lim or cue.I_at(t) < min_I:
                continue
            sp = cue.speech_at(t)
            if sp and (speech == "gap" or (speech == "thin" and pos not in thin)):
                continue
            w.add(stem, t, 0.4, key, w.vel(vel, t) * vm * (0.7 if sp else 1.0), jitter=0.004)


def walking(w, harm, grid, stem, vel, lo=36, hi=52, speech="keep"):
    """Walking bass: root on 1, chord tones on 2-3, a half-step (or scale-step) approach to the next root on 4."""
    cue = w.cue
    lim = cue.end_at if cue.end_at is not None else cue.D
    prev = None
    near = lambda pc, ref: min(in_range(pc, lo, hi), key=lambda x: abs(x - ref))
    for g in grid:
        for b in range(4):
            t = g + b * cue.beat
            if t >= lim:
                return
            c = chord_at(harm, t)
            ref = prev if prev is not None else bass_of(c, lo, lo + 12)
            if b == 0:
                k = near(c["bass"], ref)
            elif b == 3:
                nc = chord_at(harm, g + 4 * cue.beat)
                tgt = near(nc["bass"], ref)
                k = tgt - 1 if ref < tgt else tgt + 1
                if (k % 12) not in c["pcs"] and cue.rng.random() < 0.4:
                    k = tgt - 2 if ref < tgt else tgt + 2
            else:
                tones = [p for p in c["pcs"][1:3] if p != c["bass"]] or c["pcs"]
                k = near(tones[(b - 1) % len(tones)], ref)
            sp = cue.speech_at(t)
            v = w.vel(vel, t) * (1.0 if b in (0, 2) else 0.85) * (0.8 if sp and speech != "keep" else 1.0)
            w.add(stem, t + (cue.beat / 6 if (cue.swing and False) else 0), 0.8 * cue.beat, k, v)
            prev = k


def sparkles(w, harm, stem, vel, lo=79, hi=96, per_gap=2, min_gap=1.0, spacing=0.75):
    cue = w.cue
    for a, b in cue.gaps(lead=0.4, tail=0.4):
        if b - a < min_gap:
            continue
        t, cnt = a + 0.15, 0
        while t < b - 0.2 and cnt < per_gap:
            if not cue.in_phrase(t, 0.3):
                c = chord_at(harm, t)
                ks = [k for p in c["pcs"] for k in in_range(p, lo, hi)]
                if ks:
                    w.add(stem, t, 1.8, ks[int(cue.rng.integers(0, len(ks)))], w.vel(vel, t) * (1.0 - 0.18 * cnt))
                    cnt += 1
            t += spacing * cue.beat * (1.0 + 0.5 * float(cue.rng.random()))


def pings(w, harm, grid, stem, vel, lo=76, hi=88, every=2, pos=2.0):
    """Very soft single high notes under speech (keeps the music alive without competing)."""
    cue = w.cue
    for bi, g in enumerate(grid):
        if bi % every != every - 1:
            continue
        t = g + pos * cue.beat
        if t >= (cue.end_at or cue.D) or not cue.speech_at(t) or cue.in_phrase(t, 0.5):
            continue
        c = chord_at(harm, t)
        ks = [k for p in c["pcs"] for k in in_range(p, lo, hi)]
        if ks:
            w.add(stem, t, 3 * cue.beat, ks[(bi // every) % len(ks)], w.vel(vel, t))


def place_phrase(w, harm, P, t0, beat, stem, shift, octave=0, vel=50, doubles=(), patch=True):
    cue = w.cue
    last = max(o + d for o, d, _ in P["n"])
    t1 = t0 + last * beat
    if patch and P.get("ch"):
        patch_harmony(harm, t0, min(t1, cue.D), [(t0 + o * beat, chord(c, shift + cue.shift)) for o, c in P["ch"] if t0 + o * beat < cue.D])
    n = len(P["n"])
    for i, (o, d, nm) in enumerate(P["n"]):
        lean = 0.025 * beat if i in (2, 3) else 0.0
        vm = 1.0 if i < n - 1 else 0.88
        t = t0 + o * beat + lean
        hold = d * beat * (1.25 if stem in ("piano", "celesta", "harp", "glock", "pizz") else 1.0)
        k = midi(nm) + shift + cue.shift + octave
        w.add(stem, t, hold, k, vel * vm, jitter=0.005)
        for st, oc, vmul in doubles:
            w.add(st, t, hold, k + oc, vel * vm * vmul, jitter=0.005)
    cue.phrase_iv.append((t0, t1))
    return t1


def phrase_shift(cue, P):
    """Semitones from the phrase's ref key to the cue's REF key (the cue's own transposition is added later)."""
    return fold(key_pc(cue.ref) - key_pc(P["ref"]))


def melodies(w, harm, grid, names, vel=50, stem=None, octave=0, doubles=(), rest_beats=3.0, max_count=99,
             counter=None, tail_ok=None, under_vel=0.72):
    """Place phrases (cycling through `names`) into the dialogue gaps; the first candidate that fits wins.
    Lyrical moods (tail_ok): a phrase only needs its HEAD (first three notes) in the gap; the rest may continue
    softly (× under_vel) under the next line — film-scoring style. Comic moods keep whole phrases in the gaps.
    counter: (phrase, stem, octave, vel) placed together with every 'jesus*' phrase (themes in counterpoint)."""
    cue = w.cue
    if not names:
        return
    if tail_ok is None:
        tail_ok = cue.M["fam"] == "lyrical"
    count, seq = 0, 0
    lim = cue.end_at if cue.end_at is not None else cue.D
    for a, b in cue.gaps(pre=0.15 if tail_ok else 0.3):
        t = a
        while t < b - 0.5 and count < max_count:
            if any(pa - 0.3 < t < pb for pa, pb in cue.phrase_iv):
                t = max(pb for pa, pb in cue.phrase_iv if pa - 0.3 < t < pb) + 0.3
                continue
            g0 = max([g for g in grid if g <= t] + [0.0])
            hb = cue.beat / 2
            q = g0 + math.ceil((t - g0) / hb - 1e-6) * hb
            if q - t < 0.3 and b - q > 2.5:
                t = q
            room = b - t
            chosen = None
            order = names[seq % len(names):] + names[: seq % len(names)]
            for nm in order:
                P = PHRASES[nm]
                ons = sorted(o for o, _, _ in P["n"])
                span = max(o + d for o, d, _ in P["n"])
                need = (ons[min(2, len(ons) - 1)] if tail_ok else ons[-1]) * cue.beat + 0.35
                if t + span * cue.beat * 0.9 > lim + 0.5:
                    continue
                if need <= room:
                    chosen = (nm, cue.beat)
                    break
                if need * 0.9 <= room:
                    chosen = (nm, cue.beat * 0.9)
                    break
            if not chosen:
                break
            nm, bt = chosen
            P = PHRASES[nm]
            st = cue.melody_stem or stem or P["stem"]
            n0 = len(w.notes)
            end = place_phrase(w, harm, P, t, bt, st, phrase_shift(cue, P), octave, w.vel(vel, t), doubles)
            if counter and nm.startswith("jesus") and nm != "jesus_cell":
                cp, cst, coct, cvel = counter
                CP = PHRASES[cp]
                place_phrase(w, harm, CP, t, bt, cst, phrase_shift(cue, CP), coct, w.vel(cvel, t), patch=False)
            for i in range(n0, len(w.notes)):  # tails under speech: softer
                st_, tn, dn, kn, vn = w.notes[i]
                if cue.line_at(tn):
                    w.notes[i] = (st_, tn, dn, kn, max(1, int(vn * under_vel)))
            count += 1
            seq += 1
            t = end + rest_beats * cue.beat


def gliss(w, t_end, direction, pcs, lo, hi, stem="harp", dur=0.9, vel=40, force=True):
    """Harp-style glissando through `pcs` from lo to hi (up) or hi to lo (down), arriving at t_end."""
    ks = [k for k in range(lo, hi + 1) if k % 12 in pcs]
    if direction == "down":
        ks = ks[::-1]
    n = len(ks)
    for i, k in enumerate(ks):
        t = t_end - dur + dur * (i / max(1, n - 1)) ** 0.9
        w.add(stem, t, 1.6, k, vel * (0.55 + 0.45 * i / max(1, n - 1)), jitter=0.003, force=force)


def rolled(w, t, c, stem, lo, hi, n, vel, dur=5.0, spread=0.05, force=True):
    vs = [bass_of(c, lo - 12, lo)] + voice(c, lo, hi, n)
    for j, k in enumerate(vs):
        w.add(stem, t + spread * j, dur, k, vel * (1.0 if j == 0 else 0.8), jitter=0.002, force=force)


def pool_mid(lo=55, hi=74):
    return lambda c: sorted(k for p in c["pcs"] for k in in_range(p, lo, hi))


def pool_bass_arp(lo=41):
    """bass + 5th + 10th style broken chord pool (felt-piano left hand)."""
    def f(c):
        b = bass_of(c, lo, lo + 11)
        up = sorted(k for p in c["pcs"] for k in in_range(p, b + 5, b + 19) if k != b)
        return [b] + up[:4]
    return f


# ============================================================================================
# moods


def m_chase(w, cue, harm, grid):
    melodies(w, harm, grid, ["skitter"], vel=58, doubles=(("pizz", 0, 0.5),), rest_beats=2)
    pattern(w, harm, grid, "pizz", "skitter8", pool_mid(57, 72), 50, dur=0.4, thin=(0, 1, 2, 3))
    # the Void's waddle behind: bassoon + low pizz plodding 1-5-b6-5 on the bar's bass
    plod = lambda c: [bass_of(c, 38, 49), bass_of(c, 38, 49) + 7, bass_of(c, 38, 49) + 8]
    pattern(w, harm, grid, "bassoon", "plod", plod, 54, dur=0.45, speech="keep")
    pattern(w, harm, grid, "pizzlow", "plod", lambda c: [k - 12 for k in plod(c)], 50, dur=0.4, speech="keep")
    perc(w, grid, "kit", [(1.75, WB_HI, .7), (2.5, WB_LO, .5), (3.25, WB_HI, .6), (3.75, WB_HI, .8)], 44, speech="gap")
    pattern(w, harm, grid, "timpani", [(0, 0, 1.0)], lambda c: [bass_of(c, 38, 50)], 40, dur=1.0, speech="keep", min_I=0.35)
    pad(w, harm, "slowstr", 55, 72, 3, 22)


def m_arrival(w, cue, harm, grid):
    if True:  # Jesus appears: a harp glissando sweeps up into the first downbeat
        gliss(w, 0.02, "up", [cue.tonic, (cue.tonic + 2) % 12, (cue.tonic + 4) % 12, (cue.tonic + 7) % 12, (cue.tonic + 9) % 12],
              55, 86, dur=1.0, vel=46)
    melodies(w, harm, grid, ["jesus_short", "jesus", "jesus_cell"], vel=50, stem="horns", doubles=(("celesta", 12, 0.35),))
    pad(w, harm, "horns", 53, 67, 3, 34, min_I=0.25, until=8 * cue.beat)
    pad(w, harm, "slowstr", 55, 74, 4, 32)
    bass_hold(w, harm, "lowstr", 36, 48, 30)
    pattern(w, harm, grid, "harp", "arp_q", pool_mid(55, 79), 38, dur=2.0, thin=(0,), skip_phrase=True)
    sparkles(w, harm, "celesta", 30, per_gap=2)
    pings(w, harm, grid, "celesta", 22)


def m_sly(w, cue, harm, grid, low=False):
    melodies(w, harm, grid, ["sly", "sly_short"] + (["void_cell"] if low else []), vel=56, octave=-12 if low else 0, rest_beats=2)
    walking(w, harm, grid, "upright", 52, speech="thin")
    pattern(w, harm, grid, "vibes", [(1.5, 0, 1.0), (3.5, 1, .8)], pool_mid(57, 72), 30, dur=0.6, thin=(1.5,))
    perc(w, grid, "brushkit", [(1, BRUSH_SN, 1.0), (3, BRUSH_SN, .9)], 40, speech="thin", thin=(1, 3), min_I=0.25)
    if low:
        perc(w, grid, "kit", [(1, WB_LO, 0.8), (3, WB_LO, 0.7)], 30, speech="gap", every=2)
    pad(w, harm, "pad", 55, 69, 3, 24)


def m_sneaky(w, cue, harm, grid):
    m_sly(w, cue, harm, grid, low=True)


def m_romp(w, cue, harm, grid):
    melodies(w, harm, grid, ["glock_run", "romp_tune"], vel=56, rest_beats=1)
    pattern(w, harm, grid, "tuba", "oompah", lambda c: [bass_of(c, 33, 45), bass_of(c, 33, 45) + 7], 56, dur=0.4, speech="keep")
    pattern(w, harm, grid, "pizz", [(1, 0, 1.0), (3, 0, .9)], lambda c: [voice(c, 60, 72, 3)[0]], 44, dur=0.3, thin=(1, 3))
    pattern(w, harm, grid, "pizz", [(1, 0, 1.0), (3, 0, .9)], lambda c: [voice(c, 60, 72, 3)[1]], 40, dur=0.3, thin=(1, 3))
    pattern(w, harm, grid, "bassoon", [(0, 0, 1.0), (.5, 1, .7), (1, 2, .8), (1.5, 1, .7)],
            lambda c: [bass_of(c, 41, 53), bass_of(c, 41, 53) + 7, bass_of(c, 41, 53) + 9], 46, dur=0.4, speech="gap", every=2)
    pad(w, harm, "strings", 60, 76, 3, 26, min_I=0.45)
    # laughter sparkles: a glock 'ting' (and a little run when loud) on each laugh/giggle of the Void
    for t, kind, spk in cue.vocal_events:
        if spk == "VOID" and kind in ("laugh_maniacal", "giggle", "laugh_soft", "snort"):
            c = chord_at(harm, t)
            ks = [k for p in c["pcs"] for k in in_range(p, 84, 96)]
            for j in range(3 if kind == "laugh_maniacal" else 1):
                w.add("glock", t + 0.1 + 0.11 * j, 1.0, ks[(j * 2) % len(ks)], 50 - 6 * j)
    # timpani roll + cymbal swell into the end of the cue (the big galaxy)
    if cue.D > 6 and cue.I >= 0.4:
        s = cue.D - 3.2
        for i in range(int(3.0 / 0.08)):
            f = i / (3.0 / 0.08)
            w.add("timpani", s + i * 0.08, 0.3, bass_of(chord_at(harm, s), 38, 50), 12 + 50 * f ** 1.5, jitter=0.004)
        for i in range(int(2.4 / 0.07)):
            f = i / (2.4 / 0.07)
            w.add("orchkit", s + 0.6 + i * 0.07, 0.3, RIDE, 8 + 40 * f ** 2, jitter=0.003)


def m_dry(w, cue, harm, grid):
    # one held high tone (violin harmonic-like), very soft; plinks and bwomps only in the gaps
    for g in grid[::2]:
        c = chord_at(harm, g)
        k = min([x for p in c["pcs"][:3] for x in in_range(p, 81, 89)], key=lambda x: abs(x - 84))
        w.add("violin", g + 0.05, 7.0 * cue.beat, k, w.vel(20, g), jitter=0)
    pad(w, harm, "pad", 53, 67, 3, 18, min_I=0.22)
    k = 0
    for a, b in cue.gaps(lead=0.3, tail=0.3, min_len=1.0):
        P = PHRASES["plink" if k % 2 == 0 else "bwomp"]
        place_phrase(w, harm, P, a + 0.2, cue.beat, P["stem"], phrase_shift(cue, P), 0, w.vel(48, a), patch=False)
        k += 1


def m_tender(w, cue, harm, grid, sincere=False):
    names = (["jesus_short", "void_tender", "jesus", "void_sigh", "jesus_cell"] if not sincere
             else ["jesus", "jesus_b", "jesus_short", "void_sigh", "jesus_cell"])
    melodies(w, harm, grid, names, vel=50, doubles=(("slowstr", -12, 0.3),) if sincere else ())
    pattern(w, harm, grid, "piano", "arp_8" if (sincere and cue.I >= 0.35) else "arp_q", pool_bass_arp(41), 34, dur=2.5,
            thin=(0, 2), quiet_scale=0.8)
    pad(w, harm, "slowstr", 53, 72, 4, 26 if not sincere else 30)
    bass_hold(w, harm, "lowstr", 36, 48, 26 if not sincere else 30, min_I=0.2)
    if sincere:
        pattern(w, harm, grid, "harp", [(0, 0, 1.0), (.5, 1, .7), (1, 2, .8), (1.5, 3, .7)], pool_mid(62, 84), 30,
                dur=1.5, speech="gap", every=2, min_I=0.3, skip_phrase=True)
        pings(w, harm, grid, "celesta", 18, lo=79, hi=91)
    else:
        pings(w, harm, grid, "piano", 20, lo=74, hi=86)


def m_sincere(w, cue, harm, grid):
    m_tender(w, cue, harm, grid, sincere=True)


def m_exit(w, cue, harm, grid):
    melodies(w, harm, grid, ["grumble"], vel=56, rest_beats=2)
    pattern(w, harm, grid, "bassoon", "stomp", lambda c: [bass_of(c, 38, 50)], 56, dur=0.5, speech="keep")
    pattern(w, harm, grid, "pizzlow", "stomp", lambda c: [bass_of(c, 26, 38)], 54, dur=0.4, speech="keep")
    pattern(w, harm, grid, "pizz", "offbeats", lambda c: [voice(c, 57, 69, 3)[0]], 34, dur=0.3, thin=())
    pattern(w, harm, grid, "timpani", [(0, 0, 1.0), (2, 0, .7)], lambda c: [bass_of(c, 38, 50)], 36, dur=0.8, speech="keep", min_I=0.4)


def m_bittersweet(w, cue, harm, grid):
    gs = cue.gaps(lead=0.2, tail=0.4, min_len=0.9)
    if gs:  # a little pizzicato 'shrug' in the first breath
        P = PHRASES["shrug"]
        place_phrase(w, harm, P, gs[0][0] + 0.1, cue.beat * 0.6, "pizz", phrase_shift(cue, P), 0, 46, patch=False)
    melodies(w, harm, grid, ["void_sad", "jesus_cell", "void_sigh"], vel=48, rest_beats=2)
    pattern(w, harm, grid, "piano", "arp_q", pool_bass_arp(41), 32, dur=3.0, thin=(0, 2), quiet_scale=0.8)
    pad(w, harm, "slowstr", 53, 70, 3, 24)
    bass_hold(w, harm, "lowstr", 36, 48, 24)
    pad(w, harm, "clarinet", 65, 72, 1, 20, min_I=0.3, top=True)


def m_walkoff(w, cue, harm, grid):
    melodies(w, harm, grid, ["jesus", "jesus_b", "jesus_short", "jesus_cell"], vel=52, stem="celesta",
             doubles=(("glock", 0, 0.18),), counter=("void_tender", "cello", 0, 44), rest_beats=1)
    walking(w, harm, grid, "upright", 50)
    perc(w, grid, "brushkit", [(0, BRUSH_SWIRL, .6), (1, BRUSH_SN, 1.0), (2, BRUSH_SWIRL, .5), (3, BRUSH_SN, .9)], 34,
         speech="thin", thin=(1, 3), min_I=0.3)
    pad(w, harm, "slowstr", 55, 72, 4, 28)
    pattern(w, harm, grid, "piano", [(1, 0, 1.0), (2.5, 0, .7)], lambda c: [voice(c, 58, 72, 3)[1]], 26, dur=1.0, thin=(1,))
    for t, kind, spk in cue.vocal_events:
        if spk == "VOID" and kind in ("giggle", "laugh_soft", "snort"):
            c = chord_at(harm, t)
            ks = [k for p in c["pcs"] for k in in_range(p, 86, 96)]
            w.add("glock", t + 0.08, 1.0, ks[len(ks) // 2], 44)
            w.add("glock", t + 0.22, 1.0, ks[-1], 36)
    _ending(w, cue, harm, stems=(("harp", 52, 76, 4, 50), ("piano", 53, 72, 3, 40), ("celesta", 74, 91, 3, 32)))


def _ending(w, cue, harm, stems):
    if cue.end_at is None:
        return
    c = chord_at(harm, cue.end_at + 0.01)
    for st, lo, hi, n, v in stems:
        rolled(w, cue.end_at, c, st, lo, hi, n, v, dur=max(4.0, cue.D - cue.end_at), spread=0.06 if st == "harp" else 0.03)
    pad(w, [[cue.end_at, cue.D + 2, c]], "slowstr", 55, 72, 4, 30)
    cue.phrase_iv.append((cue.end_at, cue.D))


def m_hush(w, cue, harm, grid):
    if cue.trans in ("dissolve", "crossfade"):
        gliss(w, 2.2, "down", [cue.tonic, (cue.tonic + 2) % 12, (cue.tonic + 4) % 12, (cue.tonic + 7) % 12, (cue.tonic + 9) % 12],
              62, 93, dur=1.6, vel=40)
    melodies(w, harm, grid, ["fear_hope", "fear_hope_short"], vel=44, stem="celesta", rest_beats=2)
    pad(w, harm, "pad", 50, 66, 3, 30)
    bass_hold(w, harm, "lowstr", 36, 48, 28)
    pattern(w, harm, grid, "musicbox", [(0, 2, 1.0), (1.5, 1, .7), (2.5, 3, .8)], pool_mid(74, 91), 26, dur=1.5,
            speech="gap", every=2, skip_phrase=True)
    sparkles(w, harm, "celesta", 24, per_gap=1)


def m_creep(w, cue, harm, grid):
    melodies(w, harm, grid, ["creep", "creep_short"], vel=56, doubles=(("bassoon", -12, 0.6),), rest_beats=2)
    pattern(w, harm, grid, "pizzlow", "tiptoe", lambda c: [bass_of(c, 38, 50), bass_of(c, 38, 50) + 7], 50, dur=0.35,
            speech="keep", quiet_scale=0.8)
    pad(w, harm, "lowstr", 38, 50, 1, 26, top=False)
    pad(w, harm, "glass", 81, 86, 1, 14, min_I=0.3, top=True)
    perc(w, grid, "kit", [(2, CLAVES, 0.6)], 26, speech="gap", every=2)
    pattern(w, harm, grid, "timpani", [(0, 0, 1.0)], lambda c: [bass_of(c, 38, 50)], 30, dur=1.0, speech="keep", every=2, min_I=0.35)


def m_suspense(w, cue, harm, grid):
    pad(w, harm, "tremolo", 79, 91, 3, 24)
    pattern(w, harm, grid, "pizz", "tick", lambda c: [k for k in in_range((cue.tonic + 7) % 12, 55, 60)], 28, dur=0.25, speech="keep")
    bass_hold(w, harm, "cello", 38, 50, 28)
    pad(w, harm, "pad", 53, 67, 3, 20)
    melodies(w, harm, grid, ["skitter"], vel=36, stem="celesta", rest_beats=4, max_count=2)


def m_slapstick(w, cue, harm, grid):
    first_stop = min([a for a, b in cue.stops] + [cue.D])
    melodies(w, harm, grid, ["sly_short", "creep_short"], vel=50, octave=-12, rest_beats=2)
    pattern(w, harm, grid, "pizzlow", "tiptoe", lambda c: [bass_of(c, 38, 50), bass_of(c, 38, 50) + 7], 46, dur=0.35,
            speech="keep", max_t=first_stop)
    pattern(w, harm, grid, "pizz", [(1, 0, 1.0), (3, 1, .8)], pool_mid(62, 74), 32, dur=0.3, speech="thin", thin=(1,), max_t=first_stop)
    pad(w, harm, "pad", 53, 67, 3, 18, until=first_stop)
    # after each stop-time: a xylophone tumble and a tiny triangle (cartoon aftermath), then near-silence
    for a, b in cue.stops:
        if b < cue.D - 1.0:
            c = chord_at(harm, b)
            run = sorted({k for p in c["pcs"] for k in in_range(p, 72, 91)}, reverse=True)[:8]
            for i, k in enumerate(run):
                w.add("xylo", b + 0.3 + 0.06 * i, 0.5, k, 52 - 3 * i, force=True)
            w.add("kit", b + 0.3 + 0.06 * len(run) + 0.35, 1.5, TRI_OPEN, 40, force=True)
    pad(w, [[a, b2, c] for a, b2, c in harm if a >= first_stop], "pad", 53, 67, 3, 14)


def m_innocent(w, cue, harm, grid):
    """Comic innocence, told by three little gestures anchored to the dialogue: a solo-flute question right after
    the first question asked, a two-note bassoon 'who, me?' on the Void's shrug, a rising celesta answer after the
    last line (trust). Falls back to the dialogue gaps when the scene has no such lines."""
    q = next((b for a, b, spk, txt in cue.lines if "?" in txt), None)
    shrug = next((t for t, kind, spk in cue.vocal_events if spk == "VOID"), None)
    if shrug is None:
        shrug = next((a + 0.4 for a, b, spk, txt in cue.lines if "shrug" in txt.lower()), None)
    last = max([b for a, b, spk, txt in cue.lines] + [-1.0])
    gs = cue.gaps(lead=0.2, tail=0.3, min_len=1.0)
    spots = [("fear_question", q + 0.08 if q is not None else (gs[0][0] + 0.1 if gs else None), 0.85),
             ("whome", shrug if shrug is not None else (gs[1][0] + 0.1 if len(gs) > 1 else None), 0.9)]
    for nm, t, vm in spots:
        if t is None or t >= cue.D - 1.0:
            continue
        P = PHRASES[nm]
        place_phrase(w, harm, P, t, cue.beat * 0.85, P["stem"], phrase_shift(cue, P), 0, w.vel(50, t) * vm)
    a = last + 0.12 if last > 0 and last < cue.D - 1.2 else (gs[-1][0] if gs else None)
    if a is not None:
        c = chord_at(harm, a)
        run = sorted({k for p in c["pcs"] + [(c["root"] + 2) % 12] for k in in_range(p, 74, 98)})
        for i, k in enumerate(run):
            w.add("celesta", a + 0.09 * i, 1.4, k, 28 + 14 * i / max(1, len(run) - 1))
    pad(w, harm, "pad", 53, 67, 3, 20)
    bass_hold(w, harm, "lowstr", 36, 48, 20, min_I=0.3)
    pings(w, harm, grid, "celesta", 18, lo=79, hi=91)


def m_cosmos(w, cue, harm, grid):
    pcs = [cue.tonic, (cue.tonic + 2) % 12, (cue.tonic + 4) % 12, (cue.tonic + 7) % 12, (cue.tonic + 9) % 12]
    gliss(w, 0.05, "up", pcs, 62, 98, dur=1.4, vel=42)
    gliss(w, 0.15, "up", pcs, 74, 98, stem="celesta", dur=1.1, vel=30)
    melodies(w, harm, grid, ["void_bloom", "fear_wonder", "jesus_short", "fear_hope", "fear_hope_short"], vel=50,
             doubles=(), rest_beats=1.0)
    pad(w, harm, "slowstr", 55, 76, 4, 34)
    bass_hold(w, harm, "lowstr", 33, 45, 32)
    pad(w, harm, "choir", 62, 74, 3, 30, min_I=0.35)
    pad(w, harm, "glass", 81, 88, 2, 14, min_I=0.5)
    pattern(w, harm, grid, "harp", "arp_8up", pool_mid(55, 79), 34, dur=1.5, thin=(0, 2), skip_phrase=False)
    pattern(w, harm, grid, "celesta", [(p * 0.25, i, 0.8 - 0.03 * i) for i, p in enumerate(range(16))],
            lambda c: sorted(k for p in c["pcs"] for k in in_range(p, 79, 98)), 22, dur=0.8, speech="gap", every=2,
            skip_phrase=True, min_I=0.4)
    sparkles(w, harm, "celesta", 24, per_gap=1)
    _ending(w, cue, harm, stems=(("harp", 50, 79, 5, 50), ("celesta", 74, 93, 3, 34), ("piano", 50, 74, 4, 36)))


def m_still(w, cue, harm, grid):
    """A quiet truth: everything thins to single low piano notes and a breath of pad."""
    for g in grid:
        c = chord_at(harm, g)
        w.add("piano", g + 0.02, 4 * cue.beat, bass_of(c, 38, 50), w.vel(40, g), jitter=0)
        if cue.rng.random() < 0.5 and not cue.speech_at(g + 2 * cue.beat):
            w.add("piano", g + 2 * cue.beat, 2 * cue.beat, voice(c, 57, 69, 3)[1], w.vel(26, g), jitter=0)
    pad(w, harm, "pad", 50, 62, 2, 16)


MOOD_FN = {"still": m_still, "chase": m_chase, "arrival": m_arrival, "sly": m_sly, "sneaky": m_sneaky, "romp": m_romp, "dry": m_dry,
           "tender": m_tender, "sincere": m_sincere, "exit": m_exit, "bittersweet": m_bittersweet, "walkoff": m_walkoff,
           "hush": m_hush, "creep": m_creep, "suspense": m_suspense, "slapstick": m_slapstick, "innocent": m_innocent,
           "cosmos": m_cosmos}


def swell_layers(w, harm, cue):
    for i, (ts, ln) in enumerate(cue.swells):
        sub = [[max(a, ts), b, c] for a, b, c in harm if b > ts]
        stems = ("slowstr", "choir") if cue.M["fam"] == "lyrical" else ("slowstr",)
        for st in stems:
            key = f"{st}#swell{i}"
            pad(w, sub, key, 60, 79, 3, 40)
            w.auto[key] = [(ts - 0.01, -40.0)] + [(ts + ln * k / 8, -40.0 + 40.0 * float(_smooth(k / 8)) ** 0.7) for k in range(1, 9)]


# ============================================================================================
# plan derivation (screenplay scene `music` text -> moods)

KEYS_TEXT = {
    "chase": ["chase", "scurr", "running", "flee", "tense-comic", "anxious", "tom pulse", "scurry"],
    "arrival": ["arriv", "appear", "twinkly", "surprise", "glint", "harp roll", "old friends", "wonder"],
    "sly": ["sly", "conspira", "light on its feet", "playful", "tiptoe", "brushed snare"],
    "sneaky": ["sneak", "suspicious", "side-eye", "woodblock", "wood-block", "curious", "walking pizz"],
    "romp": ["romp", "erupt", "laugh", "oom", "bounc", "glockenspiel burst", "cymbal", "eruption"],
    "dry": ["held breath", "near-silence", "punchline", "dry", "suspension", "cheeky", "record-scratch", "dead air",
            "held note", "drains", "one held", "a stop", "silence", "awkward", "sulky"],
    "tender": ["tender", "simple", "felt piano", "gentle", "heart", "warm cello"],
    "sincere": ["sincer", "hopeful", "intimate", "meaningful", "polite", "warm strings"],
    "exit": ["stomp", "exit", "brisk", "storm", "staccato", "grumpy", "huff", "sulk", "grumbl"],
    "bittersweet": ["bittersweet", "wry", "sad smile", "fair enough", "sad", "ache", "lonely", "wistful"],
    "walkoff": ["horizon", "walking theme", "swing", "resolv", "fading with distance", "walk", "lazy upright"],
    "hush": ["hush", "mystery", "reprise", "bonus", "music-box", "music box"],
    "creep": ["creep", "lurk", "villain", "magician", "bass clarinet", "slither", "low clarinet", "contrabassoon"],
    "suspense": ["suspense", "suspend", "tension", "corner of", "ticking", "held under"],
    "slapstick": ["kick", "crash", "slapstick", "slam", "tumble", "comic hit", "slide-whistle"],
    "innocent": ["innocen", "noise", "question", "who, me", "shrug"],
    "cosmos": ["awe", "galax", "nebula", "choir", "shimmering", "payoff", "warm swell"],
    "still": ["quiet truth", "single low piano", "thins to", "stillness"],
}
KEYS_BEAT = {  # words in a beat's text/action/sfx/vocal that show where a second mood begins inside a scene
    "arrival": ["appear", "jesus", "now"], "romp": ["laugh", "giggl", "maniac"], "creep": ["magician", "lurk", "dagger"],
    "cosmos": ["galax", "nebula", "cosmos"], "dry": ["silent", "stare", "awkward"], "walkoff": ["horizon", "walk off"],
    "slapstick": ["kick"], "innocent": ["noise"], "tender": ["smile", "hand on"], "exit": ["storm", "stomp"],
    "still": ["doesn't want", "truth", "feeling anything"],
}
LOC_MOODS = {"THE_EDGE": ["chase", "arrival", "sly", "sneaky", "romp", "dry", "tender", "sincere", "exit", "bittersweet", "walkoff"],
             "MIND_BACKROOM": ["hush", "creep", "suspense", "slapstick", "innocent", "cosmos", "still"]}
# a mood that belongs to the other world is translated into this location's equivalent
LOC_REMAP = {"MIND_BACKROOM": {"dry": "suspense", "tender": "hush", "sincere": "hush", "bittersweet": "hush", "sly": "creep",
                               "sneaky": "creep", "chase": "slapstick", "exit": "slapstick", "romp": "slapstick",
                               "arrival": "cosmos", "walkoff": "cosmos"},
             "THE_EDGE": {"suspense": "dry", "hush": "tender", "creep": "sneaky", "slapstick": "exit", "innocent": "dry",
                          "cosmos": "arrival", "still": "dry"}}


def classify(text, loc, extra="", instr=""):
    """Score every mood's keywords: mood text ×3, instrumentation ×1.5, slug/purpose ×1; remap to the location."""
    t, e, ins = text.lower(), extra.lower(), instr.lower()
    allowed = LOC_MOODS.get(loc, list(MOODS))
    remap = LOC_REMAP.get(loc, {})
    scores = {}
    for m, kws in KEYS_TEXT.items():
        sc = sum(3.0 for k in kws if k in t) + sum(1.5 for k in kws if k in ins) + sum(1.0 for k in kws if k in e)
        if sc:
            mm = m if m in allowed else remap.get(m)
            if mm:
                scores[mm] = scores.get(mm, 0.0) + (sc if mm == m else 0.5 * sc)
    if not scores:
        return None, 0.0
    m = max(scores, key=lambda k: (scores[k], -allowed.index(k)))
    return m, scores[m]


def derive_plan(tl, sp):
    scenes = tl["scenes"]
    sp_sc = {s["id"]: s for s in (sp or {}).get("scenes", [])}
    beats, order = tl["beats"], tl["order"]
    raw = []
    for si, sc in enumerate(scenes):
        mu = sc.get("music") or {}
        src = sp_sc.get(sc["id"], {})
        mood_txt = mu.get("mood", "")
        extra = " ".join([mu.get("instrumentation", ""), sc.get("slug", "").replace("_", " "), src.get("purpose", "")])
        loc = sc.get("location", "THE_EDGE")
        I = float(mu.get("intensity", 0.35) or 0.35)
        parts = re.split(r"[;,]?\s+then\s+|;\s*", mood_txt) if mood_txt else []
        m_all, _ = classify(mood_txt, loc, extra, mu.get("instrumentation", ""))
        segs = []
        if len(parts) >= 2:
            m1, s1 = classify(parts[0], loc)
            m2, s2 = classify(" ".join(parts[1:]), loc)
            if m1 and not m2:
                m2 = m1
            if m2 and not m1:
                m1 = m2
            if m1 and m2 and m1 != m2:
                sb = [b for b in order if beats[b]["scene"] == sc["id"]]
                split = None
                for b in sb[1:]:
                    B = beats[b]
                    bt = " ".join([B.get("text") or "", B.get("vocal") or "", " ".join(B.get("sfx") or [])]).lower()
                    if src:
                        sbeat = next((x for x in src.get("beats", []) if x["id"] == b), {})
                        bt += " " + (sbeat.get("action", "") or "").lower()
                    if any(k in bt for k in KEYS_BEAT.get(m2, [])):
                        split = b
                        break
                if split and beats[split]["start"] - sc["start"] >= 4.0 and sc["end"] - beats[split]["start"] >= 4.0:
                    segs = [(m1, sc["id"], split, parts[0]), (m2, split, sc["id"] + ".end", " then ".join(parts[1:]))]
                elif split:
                    m_all = m2 if beats[split]["start"] - sc["start"] < 4.0 else m1
        hits = []
        last_part = parts[-1] if parts else mood_txt
        sb_all = [b for b in order if beats[b]["scene"] == sc["id"]]
        if sb_all and re.search(r"dead stop|cuts? out|stops dead|music stops|then silence", last_part.lower()):
            lb = beats[sb_all[-1]]
            if lb["kind"] == "silent" and lb["end"] - lb["start"] >= 1.0:
                hits.append({"t": sb_all[-1], "kind": "stop", "len": round(sc["end"] - lb["start"] + 0.2, 2), "stab": False})
        if not segs:
            m = m_all
            if m is None:  # nothing matched: a neutral choice by location and intensity
                m = ("tender" if I < 0.3 else "sneaky") if loc == "THE_EDGE" else ("creep" if I >= 0.3 else "hush")
            segs = [(m, sc["id"], sc["id"] + ".end", mood_txt)]
        for j, (m, fr, to, ptxt) in enumerate(segs):
            raw.append(dict(scenes=[sc["id"]], mood=m, frm=fr, to=to, I=I, loc=loc, txt=ptxt, hits=hits if j == len(segs) - 1 else [],
                            dissolve=(sc.get("transition_in") == "dissolve" and fr == sc["id"]), instr=mu.get("instrumentation", "")))
    # endings: last cue of each location block; last cue overall must resolve
    for i, r in enumerate(raw):
        nxt = raw[i + 1] if i + 1 < len(raw) else None
        r["ending"] = nxt is None or nxt["loc"] != r["loc"] or nxt["dissolve"]
    if raw:
        last_edge = [r for r in raw if r["loc"] == "THE_EDGE"]
        if last_edge and last_edge[-1]["mood"] in ("tender", "sincere", "bittersweet", "sly"):
            last_edge[-1]["mood"] = "walkoff"
        last = raw[-1]
        if last["loc"] == "MIND_BACKROOM" and last["mood"] not in ("cosmos",):
            last["mood"] = "cosmos"
    # merge neighbours with the same mood (continuous music across the picture cut)
    cues = []
    for r in raw:
        if cues and cues[-1]["mood"] == r["mood"] and not r["dissolve"] and cues[-1]["loc"] == r["loc"]:
            c = cues[-1]
            c["scenes"] = sorted(set(c["scenes"] + r["scenes"]), key=lambda s: [x["id"] for x in scenes].index(s))
            c["to"] = r["to"]
            c["I"] = round((c["I"] + r["I"]) / 2, 3)
            c["ending"] = r["ending"]
            c["txt"] += " | " + r["txt"]
            c["hits"] = c.get("hits", []) + r.get("hits", [])
        else:
            cues.append(dict(r))
    out = []
    for i, c in enumerate(cues):
        prev = cues[i - 1] if i else None
        tr = "dissolve" if c["dissolve"] else "crossfade"
        txt = c["txt"].lower()
        if prev is not None and not c["dissolve"]:
            first = re.split(r"[;,]?\s+then\s+|;\s*", txt)[0]
            last_prev = re.split(r"[;,]?\s+then\s+|;\s*", prev["txt"].lower())[-1]
            if re.search(r"^\s*(a\s+)?(record-scratch|stop|dead stop|near-silence|silence)|stops dead|dead stop", first) \
                    or re.search(r"stops dead|dead stop|cuts out", last_prev):
                tr = "cut"
            elif c["mood"] in ("dry", "exit", "slapstick") and prev["mood"] in ("chase", "romp", "sly", "sneaky", "exit"):
                tr = "cut"
        M = MOODS[c["mood"]]
        ramp = None
        if c["mood"] == "romp":
            ramp = [[0, 0.7], [1, 1.0]]
        elif c["mood"] == "sincere":
            ramp = [[0, 0.85], [0.8, 1.15], [1, 1.0]]
        elif c["mood"] == "cosmos":
            ramp = [[0, 0.85], [0.5, 1.25], [0.85, 0.95], [1, 0.8]]
        elif c["mood"] == "walkoff":
            ramp = [[0, 1.0], [0.6, 1.0], [1, 0.6]]
        out.append({"id": f"c{i + 1:02d}", "scenes": c["scenes"], "from": c["frm"], "to": c["to"], "mood": c["mood"],
                    "key": M["key"], "bpm": M["bpm"], "intensity": round(min(0.8, max(0.15, c["I"])), 3),
                    **({"ramp": ramp} if ramp else {}), "transition_in": tr,
                    **({"ending": True} if c["ending"] else {}),
                    **({"hits": c["hits"]} if c.get("hits") else {}),
                    "source": c["txt"][:300]})
    return out


OVERRIDES = os.path.join(ROOT, "data", "music_overrides.json")


def load_overrides():
    if os.path.exists(OVERRIDES):
        try:
            return json.load(open(OVERRIDES))
        except Exception as e:  # noqa: BLE001
            print(f"[music] {OVERRIDES} unreadable ({e}) — ignored", file=sys.stderr)
    return {}


def scene_signature(tl):
    import hashlib
    sig = [f"{s['id']}:{s.get('slug', '')}:{s.get('location', '')}:"
           + hashlib.md5(json.dumps(s.get("music", {}), sort_keys=True).encode()).hexdigest()[:8] for s in tl["scenes"]]
    ov = load_overrides()
    if ov.get("scenes"):
        sig.append("overrides:" + hashlib.md5(json.dumps(ov["scenes"], sort_keys=True).encode()).hexdigest()[:8])
    return sig


def apply_overrides(cues, tl, ov):
    """Composer edits that survive screenplay revisions: data/music_overrides.json {"scenes": {"s02": {...},
    "s18:still": {...}}}. Keys address the cue that starts with that scene (or, with ':mood', the cue of that
    mood containing it); "hits+" appends hits to the cue containing the scene. References that no longer exist
    are skipped with a warning."""
    R = A.TimeRefs(tl)

    def ok(v):
        try:
            R(v)
            return True
        except KeyError:
            return False

    for key, edits in (ov.get("scenes") or {}).items():
        if key.startswith("_"):
            continue
        sid, _, mood = key.partition(":")
        cont = [c for c in cues if sid in c["scenes"] and (not mood or c["mood"] == mood)]
        if not cont:
            print(f"[music] override {key}: no cue for that scene/mood — skipped", file=sys.stderr)
            continue
        first = next((c for c in cont if c["scenes"][0] == sid), cont[0])
        for k, v in edits.items():
            if k.startswith("_"):
                continue
            if k in ("hits", "hits+"):
                good = []
                for h in v:
                    refs = [h[x] for x in ("t", "until") if x in h] + ([h["scene"]] if h.get("scene") else [])
                    if all(ok(r) for r in refs):
                        good.append(h)
                    else:
                        print(f"[music] override {key}: hit {h} refers to a missing beat — skipped", file=sys.stderr)
                tgt = cont[0] if k == "hits+" else first
                tgt["hits"] = (tgt.get("hits", []) if k == "hits+" else []) + good
            elif k in ("from", "to"):
                if ok(v):
                    first[k] = v
                else:
                    print(f"[music] override {key}: {k}={v!r} refers to a missing beat — skipped", file=sys.stderr)
            else:
                first[k] = v
        first["overridden"] = sorted(set(first.get("overridden", []) + [key]))
    return cues


PLAN_HELP = ("Cue plan for audio/music.py — edit freely, then re-run `python3 audio/music.py`. Each cue: from/to "
             "(timeline refs: 's03', 's03.end', 's03b05', 's03b05+0.4'), mood (one of: " + ", ".join(MOODS) + "), key "
             "(the mood's mode is kept; folded to ±6 semitones), bpm, intensity 0..1, optional ramp [[frac, mult]...] "
             "(intensity multiplier across the cue), transition_in (crossfade | cut | dissolve), ending (true: final "
             "cadence + held chord after the last line), melody_stem (override the phrase instrument), prog "
             "([[chord, beats], ...] in the mood's ref key), hits ([{t, kind, len}]). Global: accents (word-painting) "
             "and auto_hits settings. If the screenplay's scene list changes, the plan is re-derived automatically "
             "(the old one is kept as data/music_plan.json.bak). ending_hold: seconds the final chord rings (default 6).")


def load_or_make_plan(tl, sp, path, replan=False):
    sig = scene_signature(tl)
    R = A.TimeRefs(tl)

    def fits(plan):
        try:
            for c in plan.get("cues", []):
                R(c["from"]), R(c["to"])
        except KeyError:
            return False
        return plan.get("signature") == sig

    if os.path.exists(path) and not replan:
        plan = json.load(open(path))
        if fits(plan):
            return plan, False
        # a stale timeline (or an older screenplay) earlier may have pushed the right plan into a backup: restore it
        import glob as _glob
        for bak in sorted(_glob.glob(path.replace(".json", "") + ".*.bak.json"), reverse=True):
            try:
                old = json.load(open(bak))
            except Exception:  # noqa: BLE001
                continue
            if fits(old):
                import time
                os.replace(path, path.replace(".json", "") + time.strftime(".%Y%m%d-%H%M%S.bak.json"))
                json.dump(old, open(path, "w"), indent=1)
                print(f"[music] restored the matching plan from {bak}", file=sys.stderr)
                return old, False
        import time
        bak = path.replace(".json", "") + time.strftime(".%Y%m%d-%H%M%S.bak.json")
        os.replace(path, bak)
        print(f"[music] the scenes or their music notes changed (or a plan reference no longer exists): re-deriving "
              f"the plan — your previous plan is kept as {bak}", file=sys.stderr)
    plan = {"_help": PLAN_HELP, "signature": sig,
            "music_lufs": -18.0,
            "accents": {"enabled": True, "gain_db": 0.0, "min_spacing": 0.9, "skip": [],
                        "_help": "skip: ['s04b06:teehee', ...] (beat:word); gain_db scales all word-painting notes"},
            "auto_hits": {"kick_thump": "stop", "block_thunk": "wahwah", "enabled": True},
            "cues": apply_overrides(derive_plan(tl, sp), tl, load_overrides())}
    json.dump(plan, open(path, "w"), indent=1)
    return plan, True


# ============================================================================================
# context: speech, vocals, marks, hits


def load_context(tl, sp, plan, verbose=True):
    beats, order = tl["beats"], tl["order"]
    speech, quiet, vev, lines = [], [], [], []
    for bid in order:
        b = beats[bid]
        if b["kind"] == "line":
            speech.append((b["start"], b["end"]))
            lines.append((b["start"], b["end"], b.get("speaker"), b.get("text") or ""))
        elif b["kind"] == "vocal":
            if b.get("vocal") in QUIET_VOCALS:
                quiet.append((b["start"], b["end"]))
            vev.append((b["start"], b.get("vocal"), b.get("speaker")))
    # word marks: absolute from the timeline (after TTS), else estimated from the screenplay text
    sp_beats = {x["id"]: x for s in (sp or {}).get("scenes", []) for x in s.get("beats", [])}
    marks = []
    for bid in order:
        b = beats[bid]
        if b["kind"] != "line":
            continue
        if b.get("marks"):
            for m in b["marks"]:
                marks.append(dict(t=float(m["start"]), end=float(m["end"]), word=m["word"], kind=m["kind"], beat=bid, est=False))
        elif bid in sp_beats:
            toks = sp_beats[bid].get("text", "").split()
            dur = max(0.3, b["end"] - b["start"] - 0.3)
            total = sum(len(re.sub(r"[\^~]", "", x)) + 1 for x in toks)
            acc = 0
            for x in toks:
                mm = re.match(r"^([\"'(]*)([\^~])(.+)$", x)
                if mm:
                    t = b["start"] + dur * acc / total
                    marks.append(dict(t=round(t, 3), end=round(t + 0.35, 3), word=re.sub(r"[^A-Za-z']", "", mm.group(3)),
                                      kind="high" if mm.group(2) == "^" else "low", beat=bid, est=True))
                acc += len(re.sub(r"[\^~]", "", x)) + 1
    # hits: cue files + music_hits.json + plan + auto (from the SFX events)
    R = A.TimeRefs(tl)
    hits = []
    try:
        from collect_sfx import load_cue_files, collect
        _, hit_entries = load_cue_files()
    except Exception as e:  # noqa: BLE001
        print(f"[music] could not read cue files: {e}", file=sys.stderr)
        hit_entries, collect = [], None
    for c in plan.get("cues", []):
        hit_entries += [dict(h, _src=f"plan:{c['id']}") for h in c.get("hits", [])]
    ev_all = None
    for h in hit_entries:
        try:
            if h.get("sfx"):  # anchored to a sound effect: {"sfx": "block_thunk", "scene": "s14", "offset": 0}
                if ev_all is None:
                    ev_all = collect_events_cached(collect, tl) if collect else []
                sc_lo, sc_hi = (R(h["scene"]), R(h["scene"] + ".end")) if h.get("scene") else (0.0, 1e9)
                cand = [e["t"] for e in ev_all if e["name"] == h["sfx"] and sc_lo <= e["t"] < sc_hi]
                if not cand:
                    print(f"[music] hit from {h.get('_src')}: no {h['sfx']} event{' in ' + h['scene'] if h.get('scene') else ''} — skipped", file=sys.stderr)
                    continue
                t = cand[0] + float(h.get("offset", 0.0))
            else:
                t = R(h.get("t", h.get("at")))
            ln = float(h["len"]) if h.get("len") else None
            if h.get("until") is not None:
                ln = max(0.1, R(h["until"]) - t)
        except KeyError as e:
            print(f"[music] hit from {h.get('_src')}: {e} — skipped", file=sys.stderr)
            continue
        kind = h.get("kind", h.get("type", "sting"))
        if kind not in HIT_KINDS:
            print(f"[music] hit kind {kind!r} unknown ({h.get('_src')}) — skipped", file=sys.stderr)
            continue
        hits.append(dict(t=t, kind=kind, len=ln, src=h.get("_src", "?"), stab=h.get("stab", kind == "stop"),
                         notes=int(h.get("notes", 4))))
    ah = plan.get("auto_hits", {})
    if ah.get("enabled", True) and collect is not None:
        try:
            ev = collect_events_cached(collect, tl)
        except Exception as e:  # noqa: BLE001
            print(f"[music] auto hits: could not collect sfx events ({e})", file=sys.stderr)
            ev = []
        for e in ev:
            kind = ah.get(e["name"])
            if not kind:
                continue
            if any(abs(h["t"] - e["t"]) < 1.0 and h["kind"] == kind for h in hits):
                continue  # an explicit hit already covers it
            h = dict(t=e["t"] + (0.25 if kind == "wahwah" else 0.0), kind=kind, len=None, src=f"auto:{e['name']}", stab=True, notes=4)
            if kind == "stop":  # stop-time through the flight and the crash, then a beat of silence
                crash = [x["t"] for x in ev if x["name"] in ("crash_buckets", "mop_clatter", "bucket_bonk") and 0 < x["t"] - e["t"] < 8]
                h["len"] = (max(crash) - e["t"] + 1.3) if crash else 2.5
            hits.append(h)
    for h in hits:
        if h["len"] is None:
            h["len"] = {"stop": 2.5, "swell": 4.0}.get(h["kind"], 2.0)
    hits.sort(key=lambda h: h["t"])
    if verbose:
        print(f"[music] {len(speech)} lines, {len(quiet)} quiet vocals, {len(vev)} vocal beats, {len(marks)} word marks"
              f"{' (estimated times)' if any(m['est'] for m in marks) else ''}, {len(hits)} hits", file=sys.stderr)
    return dict(speech=speech, quiet=quiet, vocal_events=vev, marks=marks, hits=hits, lines=lines)


HIT_KINDS = ("sting", "stop", "swell", "wahwah", "tada", "creep", "pluck", "ping")
_EV_CACHE = {}


def collect_events_cached(collect, tl):
    key = id(tl)
    if key not in _EV_CACHE:
        _EV_CACHE[key] = collect(tl)
    return _EV_CACHE[key]


# ============================================================================================
# features: word-painting accents + hits (one global writer, absolute times)


class Feature:
    def __init__(self):
        self.notes, self.bends = [], []

    def add(self, stem, t, dur, key, vel):
        self.notes.append((stem, float(t), float(dur), int(key), int(np.clip(round(vel), 1, INSTR[stem].get("vmax", 112)))))


def cue_at(cues, t):
    best = None
    for c in cues:
        if c.start - 0.05 <= t < c.end + 0.05:
            best = c
    return best


HIGH_TARGETS = [89, 93, 86, 91, 88]   # where the high word-painting notes aim (F6, A6, D6, G6, E6): a gentle variety


def accent_notes(F, cues, marks, cfg):
    skip = {s.lower() for s in cfg.get("skip", [])}
    nh = 0
    min_sp = float(cfg.get("min_spacing", 0.9))
    out, last_t = [], -9.0
    for m in sorted(marks, key=lambda m: m["t"]):
        tag = f"{m['beat']}:{m['word']}".lower()
        if tag in skip or m["t"] - last_t < min_sp:
            out.append(dict(m, placed=False, why="skip" if tag in skip else "spacing"))
            continue
        cue = cue_at(cues, m["t"])
        if cue is None:
            out.append(dict(m, placed=False, why="no cue"))
            continue
        lt = m["t"] - cue.start
        # inside a stop-time only the bed is silent: a lone accent there is good cartoon punctuation, but never
        # right on top of the stop's own stab
        if any(abs(lt - a) < 0.35 for a, b in cue.stops):
            out.append(dict(m, placed=False, why="on a stop-time stab"))
            continue
        c = chord_at(cue.harm, lt) if cue.harm else chord(FINAL.get(cue.ref, "F"), cue.shift)
        t = m["t"]
        fam = cue.M["fam"]
        if m["kind"] == "high":
            # chord tone nearest E6/F6, preferring the 3rd/5th/root (consonant, bright)
            tgt = HIGH_TARGETS[nh % len(HIGH_TARGETS)]
            nh += 1
            cand = [(abs(k - tgt) - (1.5 if (k - c["root"]) % 12 in (4, 3, 7) else 0), k) for p in c["pcs"][:4] for k in in_range(p, 82, 95)]
            k = min(cand)[1]
            up = min([x for p in c["pcs"][:3] for x in in_range(p, k + 3, k + 9)] or [k + 12])
            hi = cfg.get("high_instr") or cue.M.get("hi", "celesta")
            if hi == "glock":
                F.add("glock", t - 0.004, 1.6, k, 62)
                F.add("celesta", t - 0.004, 2.0, k - 12, 48)
                F.add("glock", t + 0.085, 1.4, up, 44)
            elif hi == "harp":
                F.add("harp", t - 0.006, 2.5, k - 12, 58)
                F.add("celesta", t - 0.004, 2.4, k, 54)
                F.add("celesta", t + 0.09, 2.0, up, 38)
            else:
                F.add("celesta", t - 0.004, 2.4, k, 60)
                F.add("glock", t - 0.004, 1.4, k, 30)
                F.add("celesta", t + 0.09, 2.0, up, 40)
            out.append(dict(m, placed=True, note=note_name(k), instr=hi, chord=c["name"], cue=cue.spec["id"]))
        else:
            r = c["bass"] if fam != "dark" else c["root"]
            kb = in_range(r, 28, 39)[0]
            F.add("contrabass", t - 0.07, 2.6, kb, 76)      # bowed: its slow attack is pre-rolled onto the word
            F.add("lowpiano", t - 0.004, 3.0, kb, 58)
            F.add("lowpiano", t - 0.004, 3.0, kb + 12, 44)
            F.add("timpani", t - 0.006, 2.5, in_range(r, 38, 49)[0], 46)
            F.add("cello", t - 0.06, 2.2, kb + 12, 40)
            out.append(dict(m, placed=True, note=note_name(kb), instr="low", chord=c["name"], cue=cue.spec["id"]))
        last_t = m["t"]
    return out


def hit_notes(F, cues, hits):
    rep = []
    for h in hits:
        t = h["t"]
        cue = cue_at(cues, t)
        if cue is None:
            rep.append(dict(h, placed=False))
            continue
        lt = t - cue.start
        c = chord_at(cue.harm, lt) if cue.harm else chord(FINAL.get(cue.ref, "F"), cue.shift)
        tonic = cue.tonic
        dark = cue.M["fam"] == "dark" or cue.minor
        k = h["kind"]
        if k == "sting" or (k == "stop" and h.get("stab")):
            r = c["root"]
            F.add("timpani", t - 0.005, 2.0, in_range(r, 38, 49)[0], 70 if k == "stop" else 58)
            F.add("pizzlow", t - 0.005, 0.6, in_range(r, 31, 42)[0], 84)
            F.add("pizz", t - 0.005, 0.5, voice(c, 55, 67, 3)[0], 70)
            F.add("pizz", t - 0.005, 0.5, voice(c, 55, 67, 3)[-1], 66)
            if k == "stop":
                F.add("orchkit", t - 0.003, 0.5, KICK, 80)
            else:
                F.add("glock", t + 0.02, 1.5, in_range(c["pcs"][1], 84, 95)[0], 50 if not dark else 36)
        elif k == "swell":
            pass  # handled inside the cue (swell layers + level)
        elif k == "wahwah":
            base = in_range((tonic + 7) % 12, 64, 75)[0]
            nn = int(np.clip(h.get("notes", 4), 1, 4))
            seq = [(0.0, base, 0.42), (0.48, base - 1, 0.42), (0.96, base - 2, 0.42), (1.44, base - 3, 1.3)][4 - nn:]
            seq = [(dt - seq[0][0], kk, d) for dt, kk, d in seq]
            if nn == 1:  # a single 'doink'
                seq = [(0.0, base, 0.6)]
            for (dt, kk, d) in seq:
                F.add("mtrumpet", t + dt, d, kk, 88)
            # droop + wobble on the last note
            t_last = t + seq[-1][0] + 0.16
            for i in range(40):
                F.bends.append(("mtrumpet", t_last + i * 0.03, int(8192 - 900 * min(1.0, i / 30) + 500 * math.sin(i * 0.9) * (1 - i / 40))))
            F.bends.append(("mtrumpet", t_last + 1.4, 8192))
            F.add("pizzlow", t + seq[-1][0], 0.6, in_range(tonic, 31, 42)[0], 60)
            F.wah = getattr(F, "wah", []) + [(t, [dt for dt, _, _ in seq])]
        elif k == "tada":
            ks = sorted(set(voice(c, 60, 79, 4)))
            for i, kk in enumerate(ks):
                F.add("harp", t - 0.2 + 0.05 * i, 1.5, kk, 60)
                F.add("glock", t - 0.2 + 0.05 * i, 1.0, kk + 12, 40)
            for kk in voice(c, 55, 72, 4):
                F.add("horns", t, 1.2, kk, 64)
            F.add("timpani", t, 1.5, in_range(c["root"], 38, 49)[0], 64)
            F.add("pizzlow", t, 0.5, in_range(c["root"], 31, 42)[0], 76)
            F.add("orchkit", t + 0.01, 1.5, CRASH, 34)
        elif k == "pluck":  # one tiny pizzicato (a comic button)
            F.add("pizz", t - 0.005, 0.5, voice(c, 60, 72, 3)[-1], 64)
            F.add("pizzlow", t - 0.005, 0.5, in_range(c["root"], 36, 47)[0], 52)
        elif k == "ping":  # one glockenspiel note (a wink)
            F.ping = getattr(F, "ping", 0) + 1
            ks = sorted(kk for p in c["pcs"][:3] for kk in in_range(p, 84, 96))
            F.add("glock", t - 0.004, 1.4, ks[(F.ping * 2) % len(ks)], 58)
        elif k == "creep":
            for i, (dt, d, nm) in enumerate([(0, .3, 0), (.3, .3, 1), (.6, .3, 0), (.9, .3, -1), (1.2, .9, 0)]):
                kk = in_range(tonic, 50, 61)[0] + nm
                F.add("clarinet", t + dt, d, kk, 62)
                F.add("bassoon", t + dt, d, kk - 12, 56)
            F.add("glass", t, 2.0, in_range((tonic + 6) % 12, 79, 90)[0], 30)
            F.add("pizzlow", t, 0.4, in_range(tonic, 31, 42)[0], 56)
        rep.append(dict(h, placed=True, cue=cue.spec["id"]))
    return rep


# ============================================================================================
# rendering


def automation_curve(pts, n, offset):
    pts = sorted(pts)
    ts = (np.array([p[0] for p in pts]) + offset) * SR
    return A.db2lin(np.interp(np.arange(n), ts, np.array([p[1] for p in pts]))).astype(np.float32)


def widen(x, amount):
    if amount <= 0:
        return x
    d = int(0.013 * SR)
    m = x.mean(axis=1)
    dl = A.lowpass(np.concatenate([np.zeros(d, np.float32), m[:-d]]), 5000)
    out = x.copy()
    out[:, 0] += amount * dl
    out[:, 1] -= amount * dl
    return out


def render_stems(syn, notes, bends, n, origin):
    """notes: (stem, t, dur, key, vel) with t relative to `origin` seconds before buffer start → dry, sends."""
    stems = {}
    for st, t, d, k, v in notes:
        stems.setdefault(st, []).append((t, d, k, v))
    per = {}
    for st, nl in sorted(stems.items()):
        base = st.split("#")[0]
        ins = INSTR[base]
        nl.sort()
        last_end, fixed = {}, []
        for t, d, k, v in nl:
            s0, s1 = int((t + origin) * SR), int((t + d + origin) * SR)
            if k in last_end and last_end[k][0] > s0:
                j = last_end[k][1]
                if s0 - fixed[j][0] < int(0.04 * SR):
                    fixed[j] = (fixed[j][0], max(fixed[j][1], s1), k, max(fixed[j][3], v))
                    last_end[k] = (fixed[j][1], j)
                    continue
                fixed[j] = (fixed[j][0], max(fixed[j][0] + 1, s0 - 1), k, fixed[j][3])
            fixed.append((s0, s1, k, v))
            last_end[k] = (s1, len(fixed) - 1)
        ev = []
        for s0, s1, k, v in fixed:
            ev.append((s0, 1, k, v))
            ev.append((min(s1, n - 1), 0, k, 0))
        for bst, bt, val in bends:
            if bst == st:
                ev.append((int((bt + origin) * SR), 2, 0, val))
        x = syn.render(ins, ev, n)
        x = A.eq_chain(x, ins["eq"])
        x *= syn.calibration(base) * float(A.db2lin(ins.get("level", 0.0)))
        x = widen(x, ins.get("width", 0.0))
        per[st] = x
    return per


def mix_stems(per, autos, n, origin):
    dry = np.zeros((n, 2), np.float32)
    sends = {"hall": np.zeros((n, 2), np.float32), "vast": np.zeros((n, 2), np.float32)}
    for st, x in per.items():
        ins = INSTR[st.split("#")[0]]
        if st in autos:
            x = x * automation_curve(autos[st], n, origin)[:, None]
        x = A.pan(x, ins["pan"])
        dry += x
        sends[ins["bus"]] += x * ins["send"]
    return dry, sends


def cue_envelope(cue, n, nxt_trans):
    """Per-sample gain for the cue buffer (index 0 = cue.start - PRE): level × fades × ramps."""
    hop = 64
    m = n // hop + 2
    tt_ = np.arange(m) * hop / SR - PRE
    fi = {"cut": 0.02, "crossfade": 0.5, "dissolve": 2.0}.get(cue.trans, 0.5)
    pre = {"cut": 0.0, "crossfade": 0.25, "dissolve": 1.5}.get(nxt_trans, 0.25)
    post = {"cut": 0.1, "crossfade": 1.4, "dissolve": 3.0}.get(nxt_trans, 1.4)
    if cue.ending and cue.end_at is not None:  # the final chord has rung: clear out before the next world begins
        pre, post = 2.5, 1.2
    g_in = np.where(tt_ < 0, 1.0, np.sin(0.5 * np.pi * np.clip(tt_ / fi, 0, 1)))
    a, b = cue.D - pre, cue.D + post
    g_out = np.where(tt_ < a, 1.0, np.cos(0.5 * np.pi * np.clip((tt_ - a) / max(b - a, 1e-3), 0, 1)))
    lvl_db = cue.M["db"] - 9.0 * (1.0 - min(1.0, cue.I / 0.6))
    I_rel = np.array([cue.I_at(max(0.0, x)) / max(cue.I, 1e-3) for x in tt_])
    db = lvl_db + 5.0 * np.log2(np.clip(I_rel, 0.25, 2.0))
    g = A.db2lin(db) * g_in * g_out
    return np.interp(np.arange(n), np.arange(m) * hop, g).astype(np.float32)


REVERBS = {"hall": dict(decay=2.3, predelay=0.022, damping=0.55, size=0.62, cross=0.3, ret=0.45),
           "vast": dict(decay=5.0, predelay=0.04, damping=0.65, size=0.95, cross=0.4, ret=0.5)}


def stop_gate(hits, N):
    """Global gate for stop-time: the score (dry and reverb) drops to silence in ~30 ms, returns over 0.35 s."""
    g = np.ones(N, np.float32)
    for h in hits:
        if h["kind"] != "stop":
            continue
        a, b = int(h["t"] * SR), int((h["t"] + h["len"]) * SR)
        f = int(0.03 * SR)
        r = int(0.35 * SR)
        a0 = max(0, a)
        seg = np.ones(N, np.float32)
        seg[a0:min(N, a0 + f)] = np.linspace(1, 0, min(N, a0 + f) - a0)
        seg[min(N, a0 + f):min(N, b)] = 0.0
        if b < N:
            seg[b:min(N, b + r)] = np.linspace(0, 1, min(N, b + r) - b) ** 2
        g = np.minimum(g, seg)
    return g


def render(tl, sp, plan, verbose=True, seed=0):
    R = A.TimeRefs(tl)
    dur = float(tl["duration"])
    N = int(round(dur * SR))
    ctx = load_context(tl, sp, plan, verbose)
    specs = []
    for c in plan["cues"]:
        s = dict(c)
        s["start"] = max(0.0, R(c["from"]))
        s["end"] = min(dur, R(c["to"]))
        if s["end"] - s["start"] < 0.5:
            print(f"[music] cue {c['id']} is empty/too short — skipped", file=sys.stderr)
            continue
        specs.append(s)
    for i, s in enumerate(specs):  # the last cue holds to the end of the film
        if i == len(specs) - 1:
            s["end"] = dur
    cues = [Cue(s, i, ctx, seed) for i, s in enumerate(specs)]
    syn = Synth()
    dry = np.zeros((N, 2), np.float32)
    buses = {b: np.zeros((N, 2), np.float32) for b in REVERBS}
    report = {"cues": [], "accents": [], "hits": []}
    for i, cue in enumerate(cues):
        harm, grid = build_form(cue)
        w = Writer(cue)
        MOOD_FN[cue.mood](w, cue, harm, grid)
        swell_layers(w, harm, cue)
        cue.harm = harm
        notes = [x for x in w.notes if x[0].split("#")[0] not in cue.layers_off]
        cue.notes_abs = [(st, cue.start + t, d, k, v) for st, t, d, k, v in notes]
        n = int((cue.D + PRE + POST) * SR)
        per = render_stems(syn, notes, w.bends, n, PRE)
        d, sends = mix_stems(per, w.auto, n, PRE)
        nxt = cues[i + 1].trans if i + 1 < len(cues) else "crossfade"
        env = cue_envelope(cue, n, nxt)[:, None]
        body = (d * env)[int(PRE * SR): int((PRE + cue.D) * SR)]
        Lc = A.loudness(body) if len(body) > SR else float("-inf")
        tgt = TARGET.get(cue.mood, -22.0) + float(np.clip(5.0 * (cue.I - 0.4), -2.5, 2.5)) + float(cue.spec.get("gain_db", 0.0))
        cal = float(np.clip(tgt - Lc, -12.0, 12.0)) if np.isfinite(Lc) else 0.0
        env = env * float(A.db2lin(cal))
        s0 = int(round((cue.start - PRE) * SR))
        a0, b0 = max(0, s0), min(N, s0 + n)
        if b0 > a0:
            dry[a0:b0] += (d * env)[a0 - s0:b0 - s0]
            for b in sends:
                buses[b][a0:b0] += (sends[b] * env)[a0 - s0:b0 - s0]
        cnt = {}
        for st, *_ in notes:
            cnt[st.split("#")[0]] = cnt.get(st.split("#")[0], 0) + 1
        rec = {"id": cue.spec["id"], "mood": cue.mood, "key": cue.key, "bpm": cue.bpm, "start": round(cue.start, 2), "cal_db": round(cal, 1),
               "end": round(cue.end, 2), "intensity": cue.I, "transition_in": cue.trans, "phrases": len(cue.phrase_iv),
               "ending_at": round(cue.start + cue.end_at, 2) if cue.end_at else None, "notes": cnt,
               "chords": [f"{round(cue.start + a, 2)}:{c['name']}@{NAMES[(c['root'] + 0) % 12]}" for a, b, c in harm if a < cue.D][:64]}
        report["cues"].append(rec)
        if verbose:
            print(f"  {cue.spec['id']} {cue.mood:11s} {cue.key:3s} {cue.bpm:5.0f}bpm {cue.start:7.2f}-{cue.end:7.2f} "
                  f"I={cue.I:.2f} {cue.trans:9s} phrases={len(cue.phrase_iv)} notes={sum(cnt.values())}", file=sys.stderr)
    bed = dry.astype(np.float64)
    for b, p in REVERBS.items():
        if np.any(buses[b]):
            wet = A.reverb_wet(buses[b], p["decay"], p["predelay"], p["damping"], p["size"], p["cross"])
            bed += p["ret"] * wet[:N]
    gate = stop_gate(ctx["hits"], N)
    bed *= gate[:, None]
    bed = A.eq_chain(bed, [("hp", 32), ("ls", 100, -1.5)]).astype(np.float64)  # tidy sub (phones / AAC headroom)
    # features (accents + hits)
    F = Feature()
    acfg = plan.get("accents", {})
    if acfg.get("enabled", True):
        report["accents"] = accent_notes(F, cues, ctx["marks"], acfg)
    report["hits"] = hit_notes(F, cues, ctx["hits"])
    feat = np.zeros((N, 2), np.float64)
    if F.notes:
        per = render_stems(syn, F.notes, F.bends, N, 0.0)
        if "mtrumpet" in per and getattr(F, "wah", None):
            per["mtrumpet"] = wah_filter(per["mtrumpet"], F.wah)
        d, sends = mix_stems(per, {}, N, 0.0)
        feat += d
        for b, p in REVERBS.items():
            if np.any(sends[b]):
                feat += p["ret"] * A.reverb_wet(sends[b], p["decay"], p["predelay"], p["damping"], p["size"], p["cross"])[:N]
        feat *= float(A.db2lin(acfg.get("gain_db", 0.0)))
    report["_features"] = F.notes
    report["_speech"] = ctx["speech"] + ctx["quiet"]
    report["_marks"] = ctx["marks"]
    return bed, feat, report, cues


def wah_filter(x, wahs):
    """Plunger-mute 'wah' on the muted trumpet: brightness opens and closes on each note (crossfade between a
    dark low-passed copy and the open sound)."""
    dark = A.lowpass(A.lowpass(x, 700), 900)
    n = len(x)
    env = np.zeros(n, np.float32)
    for t0, onsets in wahs:
        for i, dt in enumerate(onsets):
            a = int((t0 + dt) * SR)
            L = int((0.42 if i < len(onsets) - 1 else 1.4) * SR)
            k = np.arange(L) / SR
            shape = np.sin(np.pi * np.clip(k / (0.42 if i < len(onsets) - 1 else 0.5), 0, 1)) ** 1.5
            if i == len(onsets) - 1:
                shape = np.where(k < 0.25, np.sin(np.pi * k / 0.5), 0.5 + 0.5 * np.cos(2 * np.pi * 3.5 * (k - 0.25)) * np.exp(-(k - 0.25) / 0.6))
            seg = env[a:a + L]
            env[a:a + L] = np.maximum(seg, shape[: len(seg)].astype(np.float32))
    env = env[:, None]
    return (dark * (1 - env) + x * env).astype(np.float32)


# ============================================================================================
# debug output


STEM_COLORS = {"piano": (255, 214, 120), "lowpiano": (200, 160, 90), "pad": (120, 110, 200), "strings": (120, 200, 170),
               "slowstr": (110, 190, 160), "lowstr": (70, 150, 130), "tremolo": (220, 90, 120), "pizz": (200, 160, 90),
               "pizzlow": (170, 130, 70), "upright": (190, 120, 60), "cello": (240, 150, 80), "contrabass": (200, 100, 60),
               "violin": (240, 200, 160), "celesta": (170, 240, 255), "glock": (210, 250, 255), "musicbox": (255, 200, 240),
               "harp": (140, 220, 255), "choir": (250, 250, 250), "glass": (180, 180, 255), "space": (150, 130, 230),
               "timpani": (255, 90, 70), "horns": (230, 200, 60), "tuba": (200, 170, 40), "mtrumpet": (255, 160, 40),
               "flute": (160, 255, 160), "clarinet": (120, 230, 120), "bassoon": (90, 190, 90), "vibes": (160, 200, 255),
               "marimba": (220, 150, 120), "xylo": (255, 230, 150), "kit": (150, 150, 150), "brushkit": (120, 120, 120),
               "orchkit": (180, 180, 180)}


def piano_roll(cues, F_notes, speech, marks, path, px_per_s=10, dur=None):
    from PIL import Image, ImageDraw
    dur = dur or max(c.end for c in cues)
    W, H = int(dur * px_per_s) + 40, 640
    img = Image.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(img)
    y = lambda k: H - 30 - int((k - 21) / 88 * (H - 60))
    for a, b in speech:
        d.rectangle([int(a * px_per_s), 20, int(b * px_per_s), H - 30], fill=(30, 30, 46))
    for c in cues:
        x0 = int(c.start * px_per_s)
        d.line([(x0, 0), (x0, H)], fill=(90, 90, 120))
        d.text((x0 + 2, 2), f"{c.spec['id']} {c.mood} {c.key}", fill=(200, 200, 230))
        for st, t, du, k, v in c.notes_abs:
            col = STEM_COLORS.get(st.split("#")[0], (200, 200, 200))
            col = tuple(int(cc * (0.35 + 0.65 * v / 100)) for cc in col)
            d.line([(int(t * px_per_s), y(k)), (int((t + du) * px_per_s), y(k))], fill=col, width=2)
    for st, t, du, k, v in F_notes:
        d.rectangle([int(t * px_per_s) - 1, y(k) - 2, int(t * px_per_s) + 2, y(k) + 2], fill=(255, 80, 200))
    for m in marks:
        x = int(m["t"] * px_per_s)
        d.line([(x, H - 28), (x, H - 18)], fill=(255, 255, 0) if m["kind"] == "high" else (0, 200, 255), width=2)
    for s in range(0, int(dur) + 1, 10):
        d.text((int(s * px_per_s), H - 14), f"{s}", fill=(150, 150, 170))
    img.save(path)


# ============================================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default="data/timeline.json")
    ap.add_argument("--screenplay", default="data/screenplay.json")
    ap.add_argument("--plan", default="data/music_plan.json")
    ap.add_argument("--out", default="out/music.wav")
    ap.add_argument("--stems", default="out/stems")
    ap.add_argument("--report", default="data/music_report.json")
    ap.add_argument("--replan", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--roll", default=None, help="write a piano-roll PNG")
    ap.add_argument("--seed", type=int, default=0)
    o = ap.parse_args()
    rp = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    tl = json.load(open(rp(o.timeline)))
    sp = None
    for cand in [o.screenplay, "data/screenplay.json"]:
        if os.path.exists(rp(cand)):
            sp = json.load(open(rp(cand)))
            ids = {x["id"] for s in sp["scenes"] for x in s["beats"]}
            if not set(tl["order"]) <= ids:
                print(f"[music] {cand} does not match the timeline's beats — screenplay ignored", file=sys.stderr)
                sp = None
            else:
                break
    plan, new = load_or_make_plan(tl, sp, rp(o.plan), o.replan)
    print(f"[music] plan {'derived' if new else 'loaded'}: {o.plan} ({len(plan['cues'])} cues)", file=sys.stderr)
    if o.plan_only:
        for c in plan["cues"]:
            print(f"  {c['id']} {','.join(c['scenes']):12s} {c['mood']:11s} {c['key']:3s} I={c['intensity']:.2f} "
                  f"{c['transition_in']:9s}{' END' if c.get('ending') else ''}  {c['from']} -> {c['to']}")
        return
    bed, feat, report, cues = render(tl, sp, plan, seed=o.seed)
    total = bed + feat
    L = A.loudness(total)
    target = float(plan.get("music_lufs", -18.0))
    g = float(A.db2lin(target - L)) if np.isfinite(L) else 1.0
    bed, feat = (bed * g).astype(np.float32), (feat * g).astype(np.float32)
    mix = A.limit(bed + feat, -1.0)
    mix = A.fade_in(A.fade_out(mix, 0.8), 0.01)
    A.save(rp(o.out), mix)
    os.makedirs(rp(o.stems), exist_ok=True)
    A.save(os.path.join(rp(o.stems), "music_bed.wav"), bed, subtype="FLOAT", dither=False)
    A.save(os.path.join(rp(o.stems), "music_features.wav"), feat, subtype="FLOAT", dither=False)
    an = A.analyze(mix)
    if o.roll:
        piano_roll(cues, report["_features"], report["_speech"], report["_marks"], rp(o.roll), dur=float(tl["duration"]))
    for k in ("_features", "_speech", "_marks"):
        report.pop(k, None)
    report["file"] = an
    report["gain_db"] = round(target - L, 2)
    json.dump(report, open(rp(o.report), "w"), indent=1)
    pa = [a for a in report["accents"] if a.get("placed")]
    print(f"[music] {o.out}: {an['seconds']}s  LUFS {an['lufs']}  TP {an['true_peak_db']} dBTP  "
          f"accents {len(pa)}/{len(report['accents'])}  hits {sum(1 for h in report['hits'] if h.get('placed'))}", file=sys.stderr)


if __name__ == "__main__":
    main()
