"""Procedural score. Each cue returns {"bed": stereo, "lead": stereo} so the mixer
can duck the melody harder than the accompaniment under the voiceover."""
import numpy as np

from dsp import (SR, n_of, t_of, add_at, adsr, expdec, fade, white, pink, brown, lowpass,
                 highpass, bandpass, sine, additive, saw, square, karplus, pan, stereo, reverb,
                 midi_hz, norm)
from sfx import formant_voice

_CACHE = {}


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


# ------------------------------------------------------------------ instruments
def pluck(m, dur=1.5, bright=0.55, decay=0.995, var=0):
    def make():
        rng = np.random.default_rng(1000 + m * 7 + var)
        y = karplus(midi_hz(m), dur, rng, decay=decay, bright=bright)
        return fade(y * expdec(len(y), dur * 0.5, 0.001), 0, 0.05) * 0.7
    return cached(("pluck", m, dur, bright, decay, var), make)


def bass(m, dur=0.7):
    def make():
        n = n_of(dur)
        f = midi_hz(m)
        y = (sine(f, n) + 0.4 * sine(2 * f, n) + 0.12 * sine(3 * f, n)) * expdec(n, 0.32, 0.006)
        return fade(y, 0, 0.04) * 0.8
    return cached(("bass", m, dur), make)


def whistle(m, dur):
    def make():
        rng = np.random.default_rng(m)
        n = n_of(dur)
        t = t_of(n)
        f = midi_hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.25, 0, 1))
        y = sine(f, n) * adsr(n, 0.04, 0.05, 0.85, min(0.09, dur / 3))
        y += bandpass(white(n, rng), 2500, 6000) * 0.02 * adsr(n, 0.02, 0.05, 0.6, 0.05)
        return y * 0.5
    return cached(("whistle", m, round(dur, 3)), make)


def clarinet(m, dur):
    def make():
        n = n_of(dur)
        y = additive(midi_hz(m), n, [1, 0.05, 0.5, 0.03, 0.28, 0.02, 0.14, 0, 0.07])
        return lowpass(y, 2400) * adsr(n, 0.025, 0.05, 0.8, min(0.06, dur / 3)) * 0.45
    return cached(("clar", m, round(dur, 3)), make)


def chip(m, dur):
    def make():
        n = n_of(dur)
        y = square(midi_hz(m), n, 9) * adsr(n, 0.003, 0.06, 0.35, min(0.04, dur / 3))
        return lowpass(y, 3500) * 0.3
    return cached(("chip", m, round(dur, 3)), make)


def choir(m, dur, var=0):
    def make():
        rng = np.random.default_rng(m * 31 + var)
        n = n_of(dur)
        t = t_of(n)
        out = np.zeros(n)
        for v in range(2):
            f0 = midi_hz(m) * (1 + (v - 0.5) * 0.007) * (1 + 0.005 * np.sin(2 * np.pi * (4.6 + v) * t + rng.uniform(0, 6)))
            out += formant_voice(f0, rng, [(780, 5, 1.0), (1150, 6, 0.45), (2700, 8, 0.12)], breath=0.06)
        return norm(out, 0.3) * adsr(n, min(0.7, dur / 3), 0.2, 0.85, min(1.0, dur / 3))
    return cached(("choir", m, round(dur, 3), var), make)


def strings(m, dur, attack=0.25, cutoff=1600, var=0):
    def make():
        rng = np.random.default_rng(m * 13 + var)
        n = n_of(dur)
        t = t_of(n)
        out = np.zeros(n)
        for v in range(3):
            f = midi_hz(m) * (1 + (v - 1) * 0.004) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6)))
            out += saw(f, n, 30)
        y = lowpass(out, cutoff, 2) * adsr(n, attack, 0.1, 0.85, min(0.4, dur / 3))
        return y * 0.12
    return cached(("str", m, round(dur, 3), attack, cutoff, var), make)


def piano(m, dur=3.0):
    def make():
        rng = np.random.default_rng(m)
        n = n_of(dur)
        f = midi_hz(m)
        y = np.zeros(n)
        for k in range(1, 9):
            fk = k * f * np.sqrt(1 + 0.0004 * k * k)
            if fk > SR / 2.2:
                break
            y += (1 / k ** 1.3) * sine(fk, n) * expdec(n, 2.2 / (1 + 0.7 * k), 0.003)
        y[:n_of(0.004)] += highpass(white(n_of(0.004), rng), 2000) * 0.2
        return fade(y, 0, 0.3) * 0.4
    return cached(("piano", m, dur), make)


def kick():
    def make():
        n = n_of(0.35)
        t = t_of(n)
        y = sine(48 + 90 * np.exp(-t / 0.03), n) * expdec(n, 0.12, 0.001)
        return y * 0.9
    return cached(("kick",), make)


def snare(var=0):
    def make():
        rng = np.random.default_rng(50 + var)
        n = n_of(0.25)
        y = bandpass(white(n, rng), 1200, 8000) * expdec(n, 0.06) * 0.5 + sine(185, n) * expdec(n, 0.04) * 0.4
        return y
    return cached(("snare", var), make)


def hat(var=0):
    def make():
        rng = np.random.default_rng(80 + var)
        n = n_of(0.06)
        return highpass(white(n, rng), 7000) * expdec(n, 0.015) * 0.35
    return cached(("hat", var), make)


def shaker(var=0):
    def make():
        rng = np.random.default_rng(90 + var)
        n = n_of(0.09)
        return bandpass(white(n, rng), 4500, 11000) * adsr(n, 0.02, 0.02, 0.5, 0.04) * 0.3
    return cached(("shaker", var), make)


def clap(var=0):
    def make():
        rng = np.random.default_rng(70 + var)
        n = n_of(0.3)
        y = np.zeros(n)
        for i in range(3):
            add_at(y, bandpass(white(n_of(0.012), rng), 900, 3500) * 0.6, n_of(i * 0.011))
        add_at(y, bandpass(white(n_of(0.15), rng), 900, 3500) * expdec(n_of(0.15), 0.04) * 0.5, n_of(0.033))
        return y
    return cached(("clap", var), make)


def taiko(var=0):
    def make():
        rng = np.random.default_rng(60 + var)
        n = n_of(0.9)
        t = t_of(n)
        y = sine(42 + 40 * np.exp(-t / 0.05), n) * expdec(n, 0.35, 0.002)
        y += lowpass(white(n, rng), 600) * expdec(n, 0.04) * 0.4
        return y
    return cached(("taiko", var), make)


# ------------------------------------------------------------------ helpers
class Stem:
    def __init__(self, dur):
        self.buf = np.zeros((n_of(dur + 4.0), 2))

    def put(self, t, y, p=0.0, g=1.0):
        if t < 0:
            return
        add_at(self.buf, pan(y, p) * g if y.ndim == 1 else y * g, n_of(t))


CHORDS = {
    "G": [43, 55, 59, 62, 67], "C": [48, 55, 60, 64, 67], "D": [50, 57, 62, 66, 69],
    "Em": [40, 55, 59, 64, 67], "Am": [45, 57, 60, 64, 69], "F": [41, 57, 60, 65, 69],
    "Dm": [38, 57, 62, 65, 69], "Bb": [34, 58, 62, 65, 70], "A": [33, 57, 61, 64, 69],
    "Bm": [35, 54, 59, 62, 66], "A/C#": [37, 57, 61, 64, 69],
    "D/F#": [42, 57, 62, 66, 69],
}


def farm(dur, rng, bpm=116, claps=False):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["G", "C", "G", "D", "G", "C", "D", "G"]
    roll = [1, 2, 3, 4, 3, 2, 3, 4]
    melody = [  # (beat in 8-bar phrase, midi, beats)
        (0, 71, 1), (1, 74, 1), (2, 79, 1.5), (3.5, 78, 0.5),
        (4, 76, 1), (5, 72, 1), (6, 76, 1), (7, 79, 1),
        (8, 74, 1.5), (9.5, 71, 0.5), (10, 67, 1), (11, 71, 1),
        (12, 69, 2), (15, 74, 1),
        (16, 71, 1), (17, 74, 1), (18, 79, 1.5), (19.5, 78, 0.5),
        (20, 76, 1), (21, 79, 1), (22, 76, 1), (23, 72, 1),
        (24, 74, 1), (25, 78, 1), (26, 81, 1), (27, 78, 1),
        (28, 79, 3),
    ]
    bar = 0
    t0 = 0.0
    while t0 < dur:
        ch = CHORDS[prog[bar % 8]]
        for i, idx in enumerate(roll):
            bed.put(t0 + i * beat / 2, pluck(ch[idx], 1.2, 0.6, 0.994, var=i % 3), p=-0.25, g=0.45 if i % 2 else 0.6)
        bed.put(t0, bass(ch[0] + 12 if ch[0] < 40 else ch[0], 0.9), g=0.9)
        fifth = ch[0] + 7 if ch[0] + 7 < 52 else ch[0] - 5
        bed.put(t0 + 2 * beat, bass(fifth, 0.9), g=0.75)
        for i in range(8):
            bed.put(t0 + i * beat / 2, shaker(i % 2), p=0.35, g=0.6 if i % 2 else 0.3)
        if claps:
            bed.put(t0 + beat, clap(0), p=0.1, g=0.6)
            bed.put(t0 + 3 * beat, clap(1), p=-0.1, g=0.6)
        if bar % 8 == 0:
            for b, m, d in melody:
                lead.put(t0 + b * beat, whistle(m, d * beat * 0.95), p=0.15, g=0.8)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.18, 1.2), "lead": reverb(lead.buf, 0.25, 1.4)}


def sneaky(dur, rng, bpm=96):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    walk = [40, 43, 45, 46, 47, 46, 45, 43, 40, 43, 45, 46, 47, 50, 47, 35]
    tune = [(0.5, 64, 0.35), (1.5, 67, 0.35), (2.5, 66, 0.35), (3.5, 63, 0.35),
            (4.5, 64, 0.35), (5.5, 59, 0.9), (7.0, 60, 0.35), (7.5, 59, 0.35),
            (8.5, 64, 0.35), (9.5, 67, 0.35), (10.5, 71, 0.35), (11.5, 70, 0.35),
            (12.0, 69, 0.3), (12.5, 67, 0.3), (13.0, 66, 0.3), (13.5, 63, 0.3), (14.0, 64, 1.5)]
    t0 = 0.0
    k = 0
    while t0 < dur:
        for i, m in enumerate(walk):
            bed.put(t0 + i * beat, pluck(m, 0.35, 0.5, 0.97, var=i % 2), p=-0.2, g=0.9)
            if i % 2 == 1:
                bed.put(t0 + (i + 0.5) * beat, pluck(m + 36, 0.3, 0.8, 0.96), p=0.4, g=0.18)
            bed.put(t0 + (i + 0.5) * beat, hat(i % 2), p=0.3, g=0.25)
        if k % 2 == 0:
            for b, m, d in tune:
                lead.put(t0 + b * beat, clarinet(m - 12, d * beat), p=0.1, g=0.8)
        k += 1
        t0 += 16 * beat
    return {"bed": reverb(bed.buf, 0.2, 1.0), "lead": reverb(lead.buf, 0.2, 1.0)}


def brains(dur, rng, bpm=120):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["Am", "F", "C", "G"]
    t0 = 0.0
    bar = 0
    while t0 < dur:
        ch = CHORDS[prog[bar % 4]]
        notes = [ch[1], ch[2], ch[3], ch[4], ch[3] + 12 if ch[3] < 72 else ch[3], ch[4], ch[3], ch[2]]
        for i in range(16):
            lead.put(t0 + i * beat / 4, chip(notes[i % 8], beat / 4 * 0.9), p=0.2 if i % 2 else -0.2, g=0.55)
        for i in range(8):
            bed.put(t0 + i * beat / 2, chip(ch[0] + 12, beat / 2 * 0.8), g=0.6)
            bed.put(t0 + i * beat / 2 + beat / 4, hat(i % 2), p=0.3, g=0.5)
        bed.put(t0, kick(), g=0.8)
        bed.put(t0 + 2 * beat, kick(), g=0.8)
        bed.put(t0 + beat, snare(0), g=0.35)
        bed.put(t0 + 3 * beat, snare(1), g=0.35)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.15, 0.8), "lead": reverb(lead.buf, 0.2, 0.9)}


def jesus(dur, rng, bpm=66):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["D", "A/C#", "Bm", "G"]
    t0 = 0.6
    bar = 0
    while t0 < dur:
        name = prog[bar % 4]
        ch = CHORDS[name]
        span = 4 * beat
        for j, m in enumerate(ch[1:4]):
            bed.put(t0, choir(m, span * 1.05, var=j), p=(j - 1) * 0.4, g=0.9)
        root = ch[0] + 12 if ch[0] < 42 else ch[0]
        bed.put(t0, strings(root, span * 1.05, attack=0.8, cutoff=900), g=0.6)
        for i in range(8):
            m = ch[1:][i % 4] + 12
            lead.put(t0 + i * beat / 2, pluck(m, 2.0, 0.35, 0.997, var=i % 3), p=0.3 - 0.08 * i, g=0.4)
        bar += 1
        t0 += span
    return {"bed": reverb(bed.buf, 0.35, 3.0), "lead": reverb(lead.buf, 0.4, 2.5)}


def tension(dur, rng, bpm=84):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["Dm", "Dm", "Bb", "A"]
    t0 = 0.0
    bar = 0
    while t0 < dur:
        ch = CHORDS[prog[bar % 4]]
        span = 4 * beat
        bed.put(t0, strings(ch[0] + 12, span * 1.02, attack=0.5, cutoff=700), g=1.0)
        bed.put(t0, strings(ch[0] + 19, span * 1.02, attack=0.6, cutoff=900, var=1), g=0.6)
        crescendo = 0.5 + 0.5 * min(1.0, t0 / max(dur, 1))
        for i in range(8):
            lead.put(t0 + i * beat / 2, strings(ch[0] + 24, beat / 2 * 0.7, attack=0.01, cutoff=2200), p=0.2, g=0.7 * crescendo)
        bed.put(t0, taiko(bar % 2), g=0.45)
        bar += 1
        t0 += span
    return {"bed": reverb(bed.buf, 0.25, 1.8), "lead": reverb(lead.buf, 0.2, 1.4)}


def riot(dur, rng, bpm=120, anchor=1.5):
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["Dm", "C", "Bb", "A"]
    # build-up roll before the first stomp
    t = 0.0
    while t < anchor - 0.05:
        k = t / max(anchor, 0.1)
        bed.put(t, snare(int(t * 10) % 2), g=0.15 + 0.35 * k)
        t += beat / 4
    t0 = anchor
    bar = 0
    while t0 < dur:
        ch = CHORDS[prog[bar % 4]]
        for i in range(4):
            bed.put(t0 + i * beat, taiko(i % 2), g=0.7 if i % 2 == 0 else 0.5)
        for m in ch[1:4]:
            bed.put(t0, strings(m - 12, beat * 1.6, attack=0.01, cutoff=1500), g=0.9)
            bed.put(t0 + 2 * beat, strings(m - 12, beat * 1.2, attack=0.01, cutoff=1500, var=1), g=0.7)
        for i in range(16):
            lead.put(t0 + i * beat / 4, strings(ch[0] % 12 + 48, beat / 4 * 0.8, attack=0.005, cutoff=2600), p=0.25 if i % 2 else -0.25, g=0.6)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.25, 1.5), "lead": reverb(lead.buf, 0.2, 1.2)}


def aftermath(dur, rng):
    bed, lead = Stem(dur), Stem(dur)
    n = len(bed.buf)
    t = t_of(n)
    drone = sine(midi_hz(38), n) * 0.35 + lowpass(saw(midi_hz(45), n, 20), 300) * 0.25
    swell = np.clip((t - (dur - 9.0)) / 8.0, 0, 1)
    drone *= 0.6 + 0.6 * swell
    air = bandpass(pink(n, rng), 200, 900) * (0.05 + 0.25 * swell)
    bed.buf += stereo(fade(drone + air, 2.0, 0.0))
    notes = [(1.2, 62), (3.6, 65), (6.0, 69), (8.4, 64), (10.8, 60), (13.2, 62), (15.0, 57), (16.8, 58)]
    for when, m in notes:
        if when < dur - 2:
            lead.put(when, piano(m, 3.5), p=0.2 if m % 2 else -0.2, g=0.8)
    return {"bed": reverb(bed.buf, 0.3, 3.0), "lead": reverb(lead.buf, 0.45, 3.5)}


def dawn(dur, rng, bpm=84):
    """The morning after: the farm tune slowed into something warm and hopeful."""
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = ["G", "D/F#", "Em", "C", "G", "D/F#", "C", "D"]
    roll = [1, 2, 3, 4, 3, 2]
    melody = [(0, 71, 1.5), (1.5, 74, 0.5), (2, 79, 2), (4, 78, 1.5), (5.5, 74, 0.5), (6, 76, 2),
              (8, 76, 1.5), (9.5, 74, 0.5), (10, 71, 2), (12, 72, 1.5), (13.5, 71, 0.5), (14, 69, 2),
              (16, 71, 1.5), (17.5, 74, 0.5), (18, 79, 2), (20, 78, 1.5), (21.5, 76, 0.5), (22, 74, 2),
              (24, 72, 1.5), (25.5, 76, 0.5), (26, 74, 2), (28, 79, 4)]
    t0 = 0.0
    bar = 0
    while t0 < dur:
        ch = CHORDS[prog[bar % 8]]
        for i, idx in enumerate(roll):
            bed.put(t0 + i * beat * 4 / 6, pluck(ch[idx], 2.2, 0.4, 0.997, var=i % 3), p=-0.2 + 0.08 * i, g=0.45)
        root = ch[0] + 12 if ch[0] < 40 else ch[0]
        bed.put(t0, bass(root, 1.6), g=0.7)
        bed.put(t0, strings(ch[2], 4 * beat * 1.05, attack=0.9, cutoff=1200, var=bar % 2), p=0.25, g=0.5)
        if bar % 8 == 0 and t0 > 0.5:
            for b, m, d in melody:
                lead.put(t0 + b * beat, whistle(m, d * beat * 0.95), p=0.1, g=0.75)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.3, 2.2), "lead": reverb(lead.buf, 0.35, 2.4)}


def epic(dur, rng, bpm=96):
    """Power-up: pounding taiko, rising low strings and choir that climbs a half step every 4 bars."""
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    t0, bar = 0.0, 0
    while t0 < dur:
        up = bar // 4
        root = 38 + up
        for i in range(4):
            bed.put(t0 + i * beat, taiko(i % 2), g=0.7 if i in (0, 2) else 0.45)
            bed.put(t0 + i * beat + beat / 2, taiko(1), g=0.25)
        bed.put(t0, strings(root, 4 * beat * 1.02, attack=0.4, cutoff=900), g=1.0)
        bed.put(t0, strings(root + 7, 4 * beat * 1.02, attack=0.5, cutoff=1000, var=1), g=0.6)
        for i in range(8):
            lead.put(t0 + i * beat / 2, strings(root + 24 + (3 if i % 4 == 3 else 0), beat / 2 * 0.7, attack=0.01, cutoff=2400), p=0.2, g=0.55)
        if bar % 2 == 0:
            for j, m in enumerate([root + 12, root + 15, root + 19]):
                bed.put(t0, choir(m + 12, 8 * beat, var=j), p=(j - 1) * 0.4, g=0.5)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.3, 2.0), "lead": reverb(lead.buf, 0.2, 1.4)}


def chill(dur, rng, bpm=84):
    """Village: warm electric-piano chords, soft bass and brushed hats."""
    beat = 60 / bpm
    bed, lead = Stem(dur), Stem(dur)
    prog = [[50, 57, 60, 64, 69], [45, 55, 59, 62, 67], [43, 55, 59, 62, 66], [45, 57, 61, 64, 67]]
    t0, bar = 0.0, 0
    while t0 < dur:
        ch = prog[bar % 4]
        for j, m in enumerate(ch[1:]):
            bed.put(t0 + j * 0.02, piano(m, 4 * beat), p=-0.3 + 0.2 * j, g=0.5)
            bed.put(t0 + 2.5 * beat + j * 0.02, piano(m, 1.5 * beat), p=-0.3 + 0.2 * j, g=0.3)
        bed.put(t0, bass(ch[0], 1.2), g=0.8)
        bed.put(t0 + 2.5 * beat, bass(ch[0] + 7 if ch[0] + 7 < 52 else ch[0] - 5, 0.8), g=0.6)
        for i in range(8):
            bed.put(t0 + i * beat / 2, shaker(i % 2), p=0.3, g=0.35 if i % 2 else 0.2)
        bed.put(t0 + beat, snare(0), g=0.12)
        bed.put(t0 + 3 * beat, snare(1), g=0.12)
        mel = [(0.5, 2), (1.5, 3), (2.5, 4), (3.5, 3)]
        if bar % 2 == 1:
            for b, idx in mel:
                lead.put(t0 + b * beat, pluck(ch[idx] + 12, 1.2, 0.5, 0.996, var=idx % 3), p=0.2, g=0.35)
        bar += 1
        t0 += 4 * beat
    return {"bed": reverb(bed.buf, 0.25, 1.6), "lead": reverb(lead.buf, 0.3, 1.8)}


CUES = {
    "farm": farm,
    "farm2": lambda d, r: farm(d, r, bpm=126, claps=True),
    "sneaky": sneaky,
    "brains": brains,
    "jesus": jesus,
    "tension": tension,
    "riot": riot,
    "aftermath": aftermath,
    "dawn": dawn,
    "epic": epic,
    "chill": chill,
    "tender": jesus,
}
