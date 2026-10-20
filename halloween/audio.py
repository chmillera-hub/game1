"""Original score, sound design and final mix, all timed to the voice timeline.

  python3 audio.py   ->  build/mix.wav (48 kHz stereo float)
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import oaconvolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402
import timeline  # noqa: E402

SR = S.SR
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")

# chord name -> (bass, accompaniment)
CH = {
    "Dm": ("D2", ("A3", "D4", "F4")), "A7": ("A1", ("G3", "C#4", "E4")), "Gm": ("G2", ("G3", "Bb3", "D4")),
    "F": ("F2", ("A3", "C4", "F4")), "Bb": ("Bb1", ("F3", "Bb3", "D4")), "C": ("C2", ("G3", "C4", "E4")),
    "C7": ("C2", ("Bb3", "C4", "E4")), "D": ("D2", ("A3", "D4", "F#4")), "G": ("G2", ("G3", "B3", "D4")),
    "A": ("A1", ("A3", "C#4", "E4")), "Bm": ("B1", ("F#3", "B3", "D4")), "Em": ("E2", ("G3", "B3", "E4")),
    "E7": ("E2", ("G#3", "D4", "E4")),
}
THEME_A = [("A4", 1), ("D5", 2), ("F5", 2), ("E5", 1), ("D5", 1), ("C#5", 1), ("D5", 1), ("A4", 3),
           ("Bb4", 2), ("A4", 1), ("G4", 2), ("F4", 1), ("E4", 1), ("F4", 1), ("G4", 1), ("A4", 3),
           ("A4", 1), ("D5", 2), ("F5", 2), ("A5", 1), ("G5", 1), ("F5", 1), ("E5", 1), ("D5", 3)]
CHORDS_A = ["Dm", "Dm", "A7", "Dm", "Gm", "Dm", "A7", "A7", "Dm", "F", "A7", "Dm"]
THEME_B = [("A4", 1), ("D5", 2), ("F#5", 2), ("E5", 1), ("D5", 1), ("E5", 1), ("F#5", 1), ("A5", 3),
           ("G5", 2), ("F#5", 1), ("E5", 2), ("D5", 1), ("C#5", 1), ("D5", 1), ("E5", 1), ("D5", 3)]
CHORDS_B = ["D", "D", "Bm", "D", "G", "D", "A7", "D"]
MICE = [("F4", 1), ("A4", 1), ("C5", 1), ("D5", 2), ("C5", 1), ("Bb4", 1), ("G4", 1), ("E4", 1), ("F4", 3),
        ("A4", 1), ("C5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1), ("Bb4", 1), ("A4", 1), ("G4", 1), ("F4", 3)]
CHORDS_MICE = ["F", "Bb", "C7", "F", "F", "C", "C7", "F"]
CAT = [("D3", 1), ("F3", 1), ("A3", 1), ("G#3", 2), ("A3", 1), ("Bb3", 1), ("A3", 1), ("F3", 1), ("E3", 3),
       ("D3", 1), ("F3", 1), ("A3", 1), ("C4", 2), ("Bb3", 1), ("A3", 1), ("G#3", 1), ("E3", 1), ("D3", 3)]
CHORDS_CAT = ["Dm", "E7", "Gm", "A7", "Dm", "F", "E7", "Dm"]


def shift(note, semis):
    return S.midi(note) + semis


class Mix:
    def __init__(self, dur):
        self.n = int((dur + 4.0) * SR)
        self.bus = {k: np.zeros((self.n, 2), np.float32) for k in ("mus", "stg", "sfx", "amb", "voice")}

    def add(self, bus, t, y, gain=1.0, pan=0.0):
        if t < 0:
            y = y[int(-t * SR):]
            t = 0.0
        i = int(t * SR)
        if i >= self.n or len(y) == 0:
            return
        m = min(len(y), self.n - i)
        a = (pan + 1) * math.pi / 4
        self.bus[bus][i:i + m, 0] += y[:m] * gain * math.cos(a)
        self.bus[bus][i:i + m, 1] += y[:m] * gain * math.sin(a)


def fade(t, t0, t1, fin=1.0, fout=1.5):
    g = 1.0
    if fin > 0:
        g *= min(1.0, max(0.0, (t - t0) / fin))
    if fout > 0:
        g *= min(1.0, max(0.0, (t1 - t) / fout))
    return g


def waltz(M, t0, t1, bpm, chords, melody=None, mel="celesta", mel_vel=0.5, bass="pizz", bass_vel=0.55,
          comp="pizz", comp_vel=0.22, oct_mel=0, fin=1.0, fout=1.5, pad_vel=0.0, start_bar=0, swing=0.0, gain=1.0,
          comp_pattern=(1, 2)):
    beat = 60.0 / bpm
    bar = 3 * beat
    # melody timeline
    mel_events = []
    if melody:
        tt = t0
        seq = list(melody)
        skip = start_bar * 3      # skip into the melody to the start bar
        i = 0
        while tt < t1:
            note, beats = seq[i % len(seq)]
            if skip > 0:
                skip -= beats
                i += 1
                continue
            mel_events.append((tt, note, beats * beat))
            tt += beats * beat
            i += 1
    b = 0
    while True:
        ts = t0 + b * bar
        if ts >= t1:
            break
        name = chords[(b + start_bar) % len(chords)]
        root, upper = CH[name]
        g = fade(ts, t0, t1, fin, fout) * gain
        if g > 0.001:
            if bass:
                y = S.pizz(root, 0.9, bass_vel) if bass == "pizz" else S.cello(root, bar * 0.95, bass_vel, 0.05, 0.3)
                M.add("mus", ts, y, g, -0.15)
            if comp:
                for k in comp_pattern:
                    tb = ts + k * beat + (swing * beat if k == 2 else 0)
                    for j, nt in enumerate(upper):
                        y = S.pizz(nt, 0.5, comp_vel) if comp == "pizz" else S.celesta(nt, 0.8, comp_vel)
                        M.add("mus", tb + j * 0.006, y, g, 0.25 - 0.15 * j)
            if pad_vel > 0:
                y = S.pad([root] + list(upper), bar * 1.02, pad_vel, attack=0.4, release=0.8)
                M.add("mus", ts, y, g, 0.0)
        b += 1
    for (tt, note, d) in mel_events:
        g = fade(tt, t0, t1, fin, fout) * gain
        if g <= 0.001:
            continue
        nt = shift(note, oct_mel)
        if mel == "celesta":
            y = S.celesta(nt, d + 0.6, mel_vel)
        elif mel == "glock":
            y = S.glock(nt, d + 0.4, mel_vel)
        elif mel in ("bassoon", "clarinet"):
            y = S.reed(nt, d * 0.92, mel_vel, kind=mel)
        elif mel == "bassoon_st":
            y = S.reed(nt, min(d, 0.3), mel_vel, kind="bassoon", stacc=True)
        elif mel == "cello":
            y = S.cello(nt, d * 0.98, mel_vel, 0.18, 0.4)
        elif mel == "harp":
            y = S.harp(nt, d + 0.5, mel_vel)
        else:
            raise ValueError(mel)
        M.add("mus", tt, y, g, 0.1)


def pads(M, t0, t1, chords, bar, vel=0.3, cutoff=1500, choir_vel=0.0, vowel="oo", fin=1.5, fout=2.0):
    k = 0
    while True:
        ts = t0 + k * bar
        if ts >= t1:
            break
        root, upper = CH[chords[k % len(chords)]]
        g = fade(ts + bar / 2, t0, t1, fin, fout)
        notes = [root] + list(upper)
        M.add("mus", ts, S.pad(notes, bar * 1.05, vel * g, attack=0.6, release=1.0, cutoff=cutoff))
        if choir_vel > 0:
            M.add("mus", ts, S.choir([shift(n, 12) for n in upper], bar * 1.05, choir_vel * g, vowel, 0.8, 1.2))
        k += 1


def stingers(M, T):
    """High notes on hopeful words, low notes on heavy ones."""
    major_from = T.s("p4") - 1.0
    for d in T.lines:
        for w in d["words"]:
            if not w["mark"]:
                continue
            t = w["start"] + 0.03
            bright = t >= major_from or d["id"] in ("c1", "c6", "n7")
            if w["mark"] == "hi":
                top = ["D6", "F#6", "A6"] if bright else ["F6", "A6", "C7"]
                t = w["start"] + min(0.16, (w["end"] - w["start"]) * 0.5)
                M.add("stg", t, S.glock(top[0], 1.6, 0.55), 1.0, -0.2)
                M.add("stg", t + 0.1, S.celesta(top[1], 1.8, 0.45), 1.0, 0.25)
                M.add("stg", t + 0.2, S.glock(top[2], 1.4, 0.32), 1.0, 0.0)
                M.add("stg", w["end"], S.choir([top[0], top[1]], 1.4, 0.06, "oo", 0.3, 1.0))
            else:
                M.add("stg", t, S.piano_low("D2", 0.75, 4.0), 1.0, -0.1)
                M.add("stg", t, S.cello("D2", 1.8, 0.45, 0.08, 1.2), 1.0, 0.1)
                M.add("stg", t, S.bell("D3", 0.22, 4.0), 1.0, 0.0)


def build_score(M, T):
    # ================================================================ PROLOGUE
    # music box lullaby from the very first frame (no silent intro)
    t_end = T.s("n4") + 2.0
    waltz(M, 0.0, t_end, 88, CHORDS_A, THEME_A, mel="celesta", mel_vel=0.46, bass="pizz", bass_vel=0.45,
          comp="celesta", comp_vel=0.08, fin=0.0, fout=3.0, pad_vel=0.08)
    M.add("amb", 0.0, S.fx_wind(T.e("n5") + 2, 0.42, seed=1), 1.0, 0.0)
    M.add("sfx", T.s("wind1") - 0.4, S.fx_whistle(2.0, 0.5), 1.0, -0.4)
    M.add("sfx", S_word(T, "n3", "note") - 0.2, S.fx_scribble(4.2, 0.3), 1.0, 0.1)
    M.add("mus", T.s("letters") + 0.1, S.harp("D5", 2.0, 0.4), 1.0, 0.0)
    for i, nt in enumerate(("A4", "D5", "F5", "A5", "D6")):
        M.add("mus", T.s("letters") + 0.05 + i * 0.09, S.glock(nt, 1.2, 0.3), 1.0, -0.3 + i * 0.15)
    # stairs: little creaks of small feet, the lamp switch
    for i in range(6):
        M.add("sfx", T.s("n4") + 0.4 + i * 1.1, S.fx_creak(0.35, 0.18, 30, 60, seed=10 + i), 1.0, 0.3)
    M.add("sfx", S_word(T, "n4", "goodnight", "end") + 0.08, S.fx_click(0.35), 1.0, 0.4)
    # clock: tick-tock suspense under n5
    t = T.s("stairs") + 0.2
    k = 0
    while t < T.s("chimes"):
        M.add("sfx", t, S.fx_tick(0.32, 1.0 if k % 2 == 0 else 0.78), 1.0, 0.2)
        t += 0.62
        k += 1
    M.add("mus", T.s("stairs"), S.cello("D2", T.s("chimes") - T.s("stairs") + 1.0, 0.32, 1.5, 1.5), 1.0, 0.0)
    M.add("mus", T.s("n5") + 1.0, S.pad(["A4", "D5"], T.s("chimes") - T.s("n5") - 0.6, 0.10, 1.5, 0.8, 2600), 1.0, 0.0)
    tw = S_word(T, "n5", "trick")
    for i, nt in enumerate(("F4", "A4", "D5")):
        M.add("mus", tw + i * 0.16, S.pizz(nt, 0.4, 0.5), 1.0, 0.2)
    # midnight: four bongs, then the magic
    for i, o in enumerate((0.2, 1.45, 2.7, 3.95)):
        M.add("sfx", T.s("chimes") + o, S.bell("D3", 0.9 if i < 3 else 1.1, 6.0), 1.0, 0.0)
    tm = T.s("chimes") + 3.95
    M.add("mus", tm + 0.3, S.choir(["D4", "F#4", "A4", "D5"], max(0.5, T.s("w1") - tm - 1.8), 0.32, "ah", 1.2, 1.4), 1.0, 0.0)
    M.add("mus", tm + 0.5, S.sparkle(max(0.5, T.s("w1") - tm - 1.2), 0.32, density=9), 1.0, 0.0)
    for i in range(12):
        M.add("mus", tm + 0.4 + i * 0.07, S.harp(["D4", "F#4", "A4", "D5", "F#5", "A5"][i % 6] if i < 6
                                                 else ["D5", "F#5", "A5", "D6", "F#6", "A6"][i % 6], 1.6, 0.32), 1.0,
              -0.5 + i * 0.08)

    # ================================================================ WAKING / MICE
    tw = T.s("w1")
    pads(M, tw - 0.5, T.e("w1"), ["D", "G", "D", "A"], 2.0, vel=0.12, cutoff=1400, choir_vel=0.0, fin=1.0, fout=1.0)
    for i in range(10):
        M.add("mus", tw + 0.3 + i * 0.55, S.celesta(["A6", "F#6", "D7", "A6", "E7"][i % 5], 1.0, 0.12), 1.0,
              -0.4 + (i % 5) * 0.2)
    M.add("sfx", S_word(T, "w1", "tail") + 0.1, S.fx_plip(0.4, 700), 1.0, 0.2)
    M.add("sfx", T.e("w1") + 0.1, S.fx_pop(0.5), 1.0, 0.0)
    for i in range(4):
        M.add("sfx", T.s("b1") - 0.15 + i * 0.05, S.fx_plip(0.3, 600 + 140 * i), 1.0, -0.5 + i * 0.3)
    # playful tiptoe waltz for the discovery (b1, c1)
    waltz(M, T.s("b1") - 0.1, T.s("p1") - 0.2, 126, CHORDS_MICE, MICE, mel="bassoon_st", mel_vel=0.42, bass_vel=0.5,
          comp="pizz", comp_vel=0.22, fin=0.3, fout=0.8)
    waltz(M, T.s("b1") - 0.1, T.s("p1") - 0.2, 126, CHORDS_MICE, MICE, mel="glock", mel_vel=0.16, bass=None,
          comp=None, oct_mel=12, fin=0.3, fout=0.8)
    # Pip in the dark, Wedge's comfort
    pads(M, T.s("p1") - 0.3, T.e("p1") + 0.2, ["Dm", "Bb", "Gm", "A7"], 1.8, vel=0.15, cutoff=1200, fin=0.8, fout=0.8)
    pads(M, T.s("w2") - 0.4, T.s("popup") + 0.4, ["F", "C", "Bb", "F"], 1.6, vel=0.2, cutoff=1800, choir_vel=0.07,
         fin=0.6, fout=0.6)
    waltz(M, T.s("w2") - 0.2, T.s("popup") + 0.2, 80, ["F", "C", "Bb", "F"],
          [("C5", 1), ("F5", 2), ("A5", 2), ("G5", 1), ("F5", 3), ("C5", 3)], mel="celesta", mel_vel=0.32,
          bass=None, comp=None, fin=0.5, fout=0.5)
    # pop-up letters: one rising note per letter
    up_notes = ["D5", "E5", "F#5", "G5", "A5", "B5", "C#6", "D6", "E6", "F#6", "G6", "A6", "B6", "D7"]
    for i in range(14):
        tt = T.s("popup") + 0.1 + (i * 0.4 / 14 + 0.0) / 1.4 * 1.9 + i * 0.075
        M.add("sfx", tt, S.fx_pop(0.32), 1.0, -0.6 + i * 0.09)
        M.add("mus", tt + 0.02, S.glock(up_notes[i], 0.9, 0.3), 1.0, -0.6 + i * 0.09)
    # Crumb reads: plucks per letter, then the mischievous waltz under the jokes
    letters_read = [w for w in T.items["c2"]["words"] if w["text"] in ("T...", "O...")]
    for k, w in enumerate(letters_read):
        M.add("mus", w["start"], S.pizz(["D4", "F4", "A4"][k % 3], 0.5, 0.5), 1.0, 0.0)
        M.add("sfx", w["start"] - 0.2, S.fx_plip(0.25, 500 + 150 * k), 1.0, 0.0)
    waltz(M, T.s("b2") - 0.3, T.s("oooo") + 0.05, 120, CHORDS_MICE, MICE, mel="bassoon_st", mel_vel=0.32,
          bass_vel=0.42, comp="pizz", comp_vel=0.16, fin=0.6, fout=0.08, start_bar=4)
    to = S_word(T, "c3", "Oooo")
    M.add("mus", to - 0.05, S.theremin(lambda t: 520 + 260 * np.sin(np.pi * t / 0.9) - 120 * t, 1.1, 0.35), 1.0,
          0.3)
    # the wind answers
    t = T.s("oooo")
    M.add("sfx", t + 0.05, S.fx_ghost_howl(3.3, 0.95, 300.0), 1.0, -0.3)
    M.add("amb", t, S.fx_wind(3.6, 1.2, seed=4), 1.0, 0.0)
    M.add("mus", t + 0.4, S.cello("D2", 7.4, 0.3, 1.5, 1.5), 1.0, 0.0)
    M.add("mus", t + 3.0, S.cello("A4", 4.3, 0.06, 1.0, 1.0, trem=1.0), 1.0, 0.3)
    M.add("mus", t + 3.0, S.cello("G#4", 4.3, 0.05, 1.0, 1.0, trem=1.0), 1.0, -0.3)

    # ================================================================ THE CAT
    t = T.s("eyes")
    M.add("mus", t, S.organ(["D2", "A2"], 2.6, 0.32, 1.2, 1.0), 1.0, 0.0)
    M.add("mus", t + 0.8, S.theremin(lambda tt: 440 * (1 - 0.05 * tt) + 0 * tt, 2.0, 0.22), 1.0, 0.4)
    for i in range(3):
        M.add("sfx", t + 0.5 + i * 0.75, S.fx_heartbeat(0.45), 1.0, 0.0)
    tr = S_word(T, "k1", "table") - 0.4
    M.add("mus", tr, S.organ(["D2", "A2", "D3", "F3", "G#3"], 2.8, 0.42, 0.9, 1.5), 1.0, 0.0)
    M.add("mus", tr, S.choir(["D3", "A3", "D4"], 3.0, 0.22, "oo", 1.2, 1.8), 1.0, 0.0)
    M.add("sfx", tr + 0.2, S.fx_purr(2.5, 0.35), 1.0, 0.4)
    # the cat's sneaky waltz: from the rise to the end of the prophecy
    waltz(M, T.s("catrise"), S_word(T, "k3", "And"), 84, CHORDS_CAT, CAT, mel="clarinet", mel_vel=0.32, bass_vel=0.5,
          comp="pizz", comp_vel=0.12, fin=1.0, fout=1.5)
    td = S_word(T, "k3", "And")
    M.add("mus", td - 0.2, S.cello("D2", T.e("k3") - td + 1.0, 0.36, 0.8, 1.5), 1.0, -0.1)
    M.add("mus", td - 0.2, S.cello("A2", T.e("k3") - td + 1.0, 0.22, 0.8, 1.5), 1.0, 0.1)
    for i, nt in enumerate(("A3", "F3", "D3")):
        M.add("mus", S_word(T, "k3", "guts") + i * 0.22, S.pizz(nt, 0.5, 0.45), 1.0, 0.0)
    # sorrow: Pip asks, the cat answers
    pads(M, T.s("p3") - 0.4, T.e("k4") + 1.2, ["Dm", "Gm", "Dm", "A7"], 2.4, vel=0.14, cutoff=900, fin=1.0, fout=1.5)
    M.add("mus", T.e("k4"), S.cello("D2", T.e("w4") - T.e("k4") + 1.0, 0.18, 1.5, 2.0), 1.0, 0.0)
    for i, nt in enumerate(("D4", "F4", "A3", "D4")):
        M.add("mus", T.s("silence") + 0.3 + i * 1.6, S.celesta(nt, 1.5, 0.16), 1.0, 0.0)
    # hope: the paper remembers
    tc = T.s("crumbwalks")
    waltz(M, tc, T.s("p4") - 0.6, 72, ["Bb", "F", "C", "Dm", "Bb", "F", "C", "F"],
          [("F4", 1), ("A4", 1), ("C5", 1), ("D5", 2), ("C5", 1), ("Bb4", 2), ("A4", 1), ("A4", 3),
           ("F4", 1), ("A4", 1), ("C5", 1), ("F5", 2), ("E5", 1), ("D5", 1), ("C5", 1), ("Bb4", 1), ("A4", 3)],
          mel="celesta", mel_vel=0.34, bass="pizz", bass_vel=0.32, comp="celesta", comp_vel=0.07, fin=1.5, fout=0.8,
          pad_vel=0.08)
    tr = S_word(T, "c6", "remembers")
    M.add("mus", tr, S.sparkle(2.4, 0.3, notes=("C6", "F6", "A6", "C7", "F5"), density=10), 1.0, 0.0)
    M.add("mus", tr, S.choir(["F4", "A4", "C5"], 3.2, 0.2, "ah", 0.4, 2.0), 1.0, 0.0)
    # Pip's realization: theme B, the 'too' theme
    pads(M, T.s("p4") - 0.6, S_word(T, "p4", "first"), ["D", "Bm", "G", "D", "A"], 1.8, vel=0.14, cutoff=1100,
         fin=1.2, fout=0.4)
    waltz(M, S_word(T, "p4", "first") - 0.1, T.e("b4") + 0.8, 76, CHORDS_B, THEME_B, mel="celesta", mel_vel=0.3,
          bass="pizz", bass_vel=0.34, comp="celesta", comp_vel=0.08, fin=0.3, fout=1.2, pad_vel=0.13)
    pads(M, T.e("p4") - 0.2, T.e("b4") + 0.8, ["D", "G", "D", "A"], 2.4, vel=0.0, choir_vel=0.07,
         vowel="oo", fin=1.0, fout=1.5)
    # the cat's confession
    pads(M, T.s("k5") - 0.6, T.e("k5") + 0.6, ["Dm", "Bb", "Gm", "A7"], 2.0, vel=0.14, cutoff=900, fin=1.0, fout=1.0)
    waltz(M, T.s("k5") - 0.2, T.e("k5") + 0.4, 64, ["Dm"], [("A3", 1), ("D4", 2), ("F4", 2), ("E4", 1), ("D4", 1),
                                                             ("C#4", 1), ("D4", 1), ("A3", 3)],
          mel="cello", mel_vel=0.28, bass=None, comp=None, fin=0.8, fout=1.0)
    # Crumb's offer: soft major warmth
    pads(M, T.s("c7") - 0.4, T.e("k6") + 0.4, ["F", "C", "F"], 1.6, vel=0.14, cutoff=1600, fin=0.8, fout=0.6)
    for i, nt in enumerate(("C5", "F5", "A5", "C6")):
        M.add("mus", T.s("c7") + 0.2 + i * 0.6, S.celesta(nt, 1.2, 0.2), 1.0, -0.3 + i * 0.2)
    M.add("mus", T.s("k6") + 0.1, S.pizz("F5", 0.4, 0.4), 1.0, 0.2)
    M.add("sfx", T.s("k6") - 0.6, S.fx_purr(1.8, 0.32), 1.0, 0.3)

    # ================================================================ THE MONSTER
    t = T.s("thumps")
    for o in (0.05, 1.15, 3.25):
        M.add("sfx", t + o, S.fx_thump(0.95, 50, 0.8), 1.0, 0.0)
        M.add("mus", t + o, S.timpani("D2", 0.55), 1.0, 0.0)
    M.add("sfx", t + 2.2, S.fx_creak(1.0, 0.45, 20, 70, seed=21), 1.0, 0.4)
    for o in (1.7, 2.35, 3.0):
        M.add("sfx", t + o, S.fx_thump(0.35, 70, 0.4), 1.0, 0.3)
    M.add("mus", t + 0.2, S.cello("D3", 4.0, 0.12, 2.5, 0.3, trem=1.0), 1.0, -0.2)
    M.add("mus", t + 0.2, S.cello("Eb3", 4.0, 0.10, 2.5, 0.3, trem=1.0), 1.0, 0.2)
    M.add("mus", t + 2.9, S.organ(["D2", "G#2", "D3"], 2.0, 0.3, 0.1, 0.8), 1.0, 0.0)
    # panic ostinato
    tp, te = T.s("b5") - 0.2, T.s("scramble")
    pat = ["D3", "F3", "A3", "F3", "D3", "F3", "G#3", "F3"]
    k = 0
    tt = tp
    while tt < te:
        g = fade(tt, tp, te, 0.3, 0.2)
        M.add("mus", tt, S.pizz(pat[k % 8], 0.3, 0.42 * g), 1.0, -0.2 if k % 2 else 0.2)
        if k % 4 == 0:
            M.add("mus", tt, S.pizz("D2", 0.4, 0.5 * g), 1.0, 0.0)
        if k % 8 == 0:
            M.add("mus", tt, S.timpani("D2", 0.3 * g, 0.8), 1.0, 0.0)
        tt += 0.19
        k += 1
    M.add("mus", tp, S.cello("D2", te - tp, 0.25, 0.3, 0.3), 1.0, 0.0)
    # scramble back to the page
    ts = T.s("scramble")
    for i, nt in enumerate(("D6", "A5", "F5", "D5", "A4", "F4", "D4")):
        M.add("mus", ts + i * 0.06, S.glock(nt, 0.6, 0.35), 1.0, 0.4 - i * 0.12)
    M.add("sfx", ts, S.fx_rustle(1.6, 0.5), 1.0, 0.0)
    for o in (0.25, 0.55, 0.85, 1.45):
        M.add("sfx", ts + o, S.fx_plip(0.45, 520), 1.0, 0.0)
    M.add("sfx", ts + 1.9, S.fx_heartbeat(0.4), 1.0, 0.0)
    # Mom in the doorway: slow steps, a creak, an organ chord, then... a yawn
    tm = T.s("momenter")
    for o in (0.2, 1.1):
        M.add("sfx", tm + o, S.fx_thump(0.55, 62, 0.5), 1.0, 0.0)
    M.add("sfx", tm + 0.6, S.fx_creak(0.7, 0.35, 30, 80, seed=31), 1.0, -0.2)
    M.add("mus", tm, S.organ(["D2", "A2", "C3", "F3"], 1.7, 0.3, 0.3, 0.6), 1.0, 0.0)
    M.add("mus", tm + 1.7, S.fx_yawn_horn(0.45), 1.0, 0.0)
    # sleepy music box under 'who left the pumpkin burning'
    waltz(M, T.s("m1") - 0.6, T.s("pickup") + 0.8, 76, ["Dm", "A7"], [("A4", 3), ("F4", 2), ("E4", 1)],
          mel="celesta", mel_vel=0.25, bass="pizz", bass_vel=0.24, comp=None, fin=0.5, fout=0.6)
    tpk = T.s("pickup")
    M.add("mus", tpk + 0.1, S.harp("A4", 1.8, 0.3), 1.0, -0.3)
    M.add("mus", tpk + 0.25, S.harp("D5", 1.8, 0.3), 1.0, 0.0)
    M.add("mus", tpk + 0.4, S.harp("F#5", 2.0, 0.3), 1.0, 0.3)
    M.add("sfx", tpk + 0.8, S.fx_rustle(0.5, 0.35, seed=8), 1.0, 0.1)

    # ================================================================ MOM READS IT
    t0 = T.s("m2") - 0.6
    t1 = T.e("m5") + 1.5
    pads(M, t0, T.s("m4") - 0.4, ["D", "G", "Bm", "A"], 2.5, vel=0.15, cutoff=1500, fin=1.5, fout=0.8)
    waltz(M, T.s("m2") + 0.3, T.s("m4") - 0.4, 70, CHORDS_B, THEME_B, mel="celesta", mel_vel=0.26, bass=None,
          comp=None, fin=1.5, fout=1.0)
    pads(M, T.s("m4") - 0.6, T.s("hug"), ["Bm", "G", "D", "A"], 1.9, vel=0.16, cutoff=1200, fin=0.8, fout=0.6)
    M.add("sfx", T.s("hug") + 0.15, S.fx_heartbeat(0.55), 1.0, 0.0)
    M.add("sfx", T.s("hug") + 1.05, S.fx_heartbeat(0.5), 1.0, 0.0)
    M.add("mus", T.s("hug") - 0.2, S.choir(["D4", "F#4", "A4"], 2.4, 0.16, "oo", 1.0, 1.0), 1.0, 0.0)
    pads(M, T.s("m5") - 0.3, t1, ["D", "G", "A", "D"], 1.6, vel=0.2, cutoff=2400, choir_vel=0.12, vowel="ah",
         fin=0.6, fout=1.5)
    waltz(M, T.s("m5") - 0.2, t1, 80, ["D", "G", "A7", "D"], [("A5", 3), ("F#5", 2), ("E5", 1), ("D5", 3), ("D5", 3)],
          mel="celesta", mel_vel=0.3, bass="pizz", bass_vel=0.28, comp=None, fin=0.4, fout=1.2)
    # fridge: the page is pinned with a magnet; a light playful waltz
    tf = T.s("fridge")
    M.add("sfx", tf + 0.3, S.fx_whoosh(0.7, 0.3), 1.0, 0.3)
    M.add("sfx", tf + 1.8, S.fx_click(0.55), 1.0, 0.0)
    waltz(M, tf + 1.9, T.s("momleave") + 1.6, 108, ["D", "A7", "D", "G", "D", "A7", "D", "D"],
          [("F#5", 1), ("A5", 1), ("F#5", 1), ("E5", 2), ("C#5", 1), ("D5", 1), ("E5", 1), ("F#5", 1), ("G5", 3),
           ("F#5", 1), ("E5", 1), ("D5", 1), ("C#5", 2), ("E5", 1), ("D5", 3), ("D5", 3)],
          mel="glock", mel_vel=0.18, bass="pizz", bass_vel=0.3, comp="pizz", comp_vel=0.1, fin=0.8, fout=1.5)
    M.add("sfx", T.s("mrrp") + 0.1, S.fx_mrrp(0.55), 1.0, -0.3)
    tl = T.s("momleave")
    M.add("mus", tl + 0.4, S.fx_yawn_horn(0.3), 1.0, 0.2)
    for o in (1.3, 1.9, 2.5):
        M.add("sfx", tl + o, S.fx_thump(0.25, 65, 0.4), 1.0, 0.6)

    # ================================================================ THE FRIDGE
    tw = T.s("wake2")
    M.add("mus", tw, S.sparkle(2.2, 0.28, notes=("D6", "F#6", "A6", "E6"), density=8), 1.0, 0.0)
    M.add("mus", tw + 0.2, S.choir(["D4", "F#4", "A4"], 2.0, 0.12, "oo", 0.8, 1.0), 1.0, 0.0)
    tb = S_word(T, "g1", "Boo")
    M.add("mus", tb - 0.05, S.theremin(lambda t: 700 - 380 * t / 0.8, 0.8, 0.4), 1.0, 0.2)
    M.add("mus", tb + 0.6, S.reed("F2", 0.25, 0.4, stacc=True), 1.0, 0.0)
    M.add("mus", tb + 0.85, S.reed("E2", 0.4, 0.4, stacc=True), 1.0, 0.0)
    waltz(M, T.s("s1") - 0.4, T.s("catcurl"), 96, ["D", "G", "A7", "D", "D", "G", "A7", "D"], THEME_B, mel="glock",
          mel_vel=0.2, bass="pizz", bass_vel=0.28, comp="celesta", comp_vel=0.07, fin=1.0, fout=1.2, pad_vel=0.07)
    tb6 = T.s("b6")
    M.add("mus", S_word(T, "b6", "Could"), S.reed("A2", 0.3, 0.4, stacc=True), 1.0, 0.0)
    M.add("mus", S_word(T, "b6", "Could") + 0.35, S.reed("G#2", 0.5, 0.35, stacc=False), 1.0, 0.0)
    tc = T.s("catcurl")
    M.add("sfx", tc + 0.1, S.fx_whoosh(0.8, 0.25), 1.0, -0.4)
    M.add("sfx", tc + 1.0, S.fx_thump(0.2, 90, 0.3), 1.0, 0.0)
    M.add("sfx", tc + 1.2, S.fx_purr(T.e("b7") + 3 - tc - 1.2, 0.28), 1.0, -0.2)
    pads(M, tc, T.e("b7") + 1.5, ["D", "Bm", "G", "A"], 2.4, vel=0.12, cutoff=1500, fin=1.0, fout=1.5)
    for i, nt in enumerate(("A5", "F#5", "D5", "A4")):
        M.add("mus", T.s("k8") + i * 0.5, S.celesta(nt, 1.2, 0.18), 1.0, 0.0)
    M.add("mus", S_word(T, "t1", "Did") - 0.6, S.fx_yawn_horn(0.26), 1.0, 0.0)
    M.add("mus", T.e("b7") + 0.05, S.pizz("D4", 0.4, 0.45), 1.0, 0.0)
    M.add("mus", T.e("b7") + 0.25, S.pizz("D3", 0.5, 0.45), 1.0, 0.0)

    # ================================================================ EPILOGUE
    te = T.s("exterior")
    M.add("amb", te, S.fx_wind(T.s("morning") - te + 1.0, 0.4, seed=9), 1.0, 0.0)
    M.add("sfx", te + 0.4, S.fx_owl(0.35), 1.0, -0.6)
    waltz(M, te - 0.2, T.e("n6") + 0.4, 66, CHORDS_A, THEME_A, mel="celesta", mel_vel=0.32, bass="pizz", bass_vel=0.3,
          comp="celesta", comp_vel=0.07, fin=1.2, fout=1.0, pad_vel=0.1, start_bar=8)
    waltz(M, T.e("n6") - 0.2, T.s("morning") + 0.6, 66, CHORDS_B, THEME_B, mel="celesta", mel_vel=0.36, bass="pizz",
          bass_vel=0.32, comp="celesta", comp_vel=0.08, fin=0.6, fout=0.8, pad_vel=0.14)
    pads(M, T.e("n6") - 0.2, T.s("morning") + 0.6, ["D", "G", "Bm", "A"], 2.7, vel=0.0, choir_vel=0.09, vowel="ah",
         fin=1.5, fout=1.0)
    # morning: bright music box, final chord, sparkle
    tmo = T.s("morning")
    waltz(M, tmo, T.duration, 92, ["D", "G", "A7", "D", "D", "D"],
          [("A5", 1), ("D6", 2), ("F#6", 2), ("E6", 1), ("D6", 1), ("E6", 1), ("F#6", 1), ("A6", 3), ("D6", 9)],
          mel="glock", mel_vel=0.3, bass="pizz", bass_vel=0.3, comp="celesta", comp_vel=0.09, fin=0.2, fout=1.0)
    M.add("mus", T.s("n8") + 0.05, S.bell("D4", 0.35, 5.0), 1.0, 0.0)
    M.add("mus", T.s("end") + 0.4, S.pad(["D3", "A3", "D4", "F#4", "A4"], 3.6, 0.2, 1.0, 1.8, 2400), 1.0, 0.0)
    M.add("mus", T.s("end") + 0.4, S.choir(["D4", "F#4", "A4", "D5"], 3.4, 0.14, "ah", 1.0, 1.8), 1.0, 0.0)
    M.add("mus", T.s("end") + 0.6, S.sparkle(2.5, 0.25, density=7), 1.0, 0.0)


def S_word(T, lid, word, edge="start"):
    return T.word(lid, word, 0, edge)


def reverb_ir(seconds=2.4, seed=3, damp=3000.0):
    n = int(seconds * SR)
    rr = np.random.default_rng(seed)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2), np.float32)
    for ch in range(2):
        x = rr.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / seconds)
        ir[:, ch] = S.filt(x, "lp", damp, 0.6)
    pre = int(0.018 * SR)
    ir = np.vstack([np.zeros((pre, 2), np.float32), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def convolve_stereo(x, ir):
    out = np.zeros_like(x)
    for ch in range(2):
        out[:, ch] = oaconvolve(x[:, ch], ir[:, ch])[: len(x)]
    return out


def band_duck(x, duck, d_low, d_mid, d_high, low_gain=0.72):
    """Duck a stereo bus mostly in the speech band (250 Hz - 3.5 kHz); tame sub-bass for phone speakers."""
    from scipy.signal import butter, sosfiltfilt
    lo = butter(4, 250, btype="low", fs=SR, output="sos")
    hi = butter(4, 3500, btype="high", fs=SR, output="sos")
    sub = butter(2, 45, btype="high", fs=SR, output="sos")
    out = np.zeros_like(x)
    for ch in range(2):
        low = sosfiltfilt(lo, x[:, ch]).astype(np.float32)
        high = sosfiltfilt(hi, x[:, ch]).astype(np.float32)
        mid = x[:, ch] - low - high
        dk = duck[:, 0]
        low = sosfiltfilt(sub, low).astype(np.float32) * low_gain
        out[:, ch] = low * (1 - d_low * dk) + mid * (1 - d_mid * dk) + high * (1 - d_high * dk)
    return out


def main():
    T = timeline.get()
    M = Mix(T.duration)
    # ---- voices: loudness-matched, placed on the timeline
    vdir = os.path.join(OUT, "voices")
    for d in T.lines:
        y, sr = sf.read(os.path.join(vdir, f"{d['id']}.wav"), dtype="float32")
        rms = np.sqrt(np.mean(y[np.abs(y) > 0.01] ** 2)) if np.any(np.abs(y) > 0.01) else 0.1
        g = 0.105 / max(rms, 1e-4)
        if d["who"] == "CAT":
            g *= 1.08
        if d["id"] in ("m8",):
            g *= 0.8
        y = np.tanh(y * g * 1.2) / 1.2
        M.add("voice", d["start"], y, 1.0, 0.0)
    build_score(M, T)
    stingers(M, T)
    # ---- ducking from the voice envelope
    v = np.abs(M.bus["voice"][:, 0]) + np.abs(M.bus["voice"][:, 1])
    hop = SR // 100
    nb = len(v) // hop
    e = v[: nb * hop].reshape(nb, hop).max(axis=1)
    act = np.clip(e / 0.06, 0, 1)
    sm = np.zeros_like(act)
    s = 0.0
    for i in range(nb):  # 40ms attack, 450ms release
        a = act[i]
        s = s + (a - s) * (0.4 if a > s else 0.022)
        sm[i] = s
    sm = np.convolve(sm, np.ones(8) / 8, mode="same")
    sm = np.concatenate([sm[3:], np.repeat(sm[-1:], 3)])  # ~30 ms look-ahead
    duck = np.repeat(sm, hop)
    duck = np.pad(duck, (0, len(v) - len(duck)), mode="edge")[:, None]
    mus = band_duck(M.bus["mus"], duck, 0.6, 0.93, 0.55)
    amb = band_duck(M.bus["amb"], duck, 0.6, 0.85, 0.6, low_gain=0.5)
    stg = band_duck(M.bus["stg"], duck, 0.25, 0.85, 0.3)
    sfx = band_duck(M.bus["sfx"], duck, 0.3, 0.7, 0.3)
    from scipy.signal import butter, sosfiltfilt
    vh = butter(2, 85, btype="high", fs=SR, output="sos")
    voice = np.stack([sosfiltfilt(vh, M.bus["voice"][:, ch]) for ch in range(2)], axis=1).astype(np.float32)
    # ---- reverbs
    hall = reverb_ir(2.6, 3, 3500)
    room = reverb_ir(0.9, 5, 4500)
    mus_w = convolve_stereo(mus * 0.9 + stg * 0.9 + sfx * 0.35, hall)
    voice_w = convolve_stereo(voice, room)
    bg = mus * 0.62 + mus_w * 0.15 + stg * 0.5 + sfx * 0.8 + amb * 0.45
    mix = voice * 1.0 + voice_w * 0.07 + bg
    np.save(os.path.join(OUT, "dbg_voice.npy"), voice[::8, 0].astype(np.float32))
    np.save(os.path.join(OUT, "dbg_bg.npy"), bg[::8].mean(axis=1).astype(np.float32))
    # gentle bus limiting
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / max(peak, 1e-6) * 1.6) / np.tanh(1.6) * 0.9
    n_out = int(math.ceil(T.duration * SR))
    mix = mix[:n_out]
    os.makedirs(OUT, exist_ok=True)
    sf.write(os.path.join(OUT, "mix.wav"), mix.astype(np.float32), SR, subtype="FLOAT")
    for k in ("voice", "mus", "sfx"):
        sf.write(os.path.join(OUT, f"stem_{k}.wav"), M.bus[k][:n_out].astype(np.float32), SR, subtype="FLOAT")
    print("mix:", mix.shape, "peak", float(np.max(np.abs(mix))))


if __name__ == "__main__":
    main()
