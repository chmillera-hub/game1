"""Procedural music tracks (mono, 48 kHz)."""
import numpy as np
from scipy import signal
from audio_lib import (SR, tt, mtof, lp, hp, bp, peak, additive, phase_of, reverb, norm, fade, place,
                       rng, tv_lowpass, fart, balloon_squeal, smooth_noise, VOW_AH, honk)

# ------------------------------------------------------------ instruments

def harpsichord(f, dur):
    L = dur + 0.6
    t = tt(L)
    x = np.zeros(len(t))
    for det, g in ((1.0, 1.0), (1.0035, 0.8), (2.0, 0.35)):
        ff = f * det
        for k in range(1, 26):
            if k * ff > SR * 0.42:
                break
            a = (k ** -0.75) * abs(np.sin(np.pi * k * 0.13)) * g
            x += a * np.sin(2 * np.pi * k * ff * t + k) * np.exp(-t * (1.0 + 0.35 * k))
    rel = np.clip((L - t) / 0.08, 0, 1) * np.where(t > dur, np.exp(-(t - dur) / 0.06), 1)
    click = rng(int(f)).standard_normal(len(t)) * np.exp(-t / 0.003) * 0.3
    return (x + hp(click, 2000)) * rel


def pizz(f, dur):
    L = max(dur, 0.5)
    t = tt(L)
    x = sum((k ** -1.4) * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (5 + 2.5 * k)) for k in range(1, 9) if k * f < SR * 0.4)
    return fade(x * np.minimum(t / 0.004, 1), 0.001, 0.05)


def glock(f, dur):
    t = tt(1.6)
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / d) for m, a, d in ((1, 1, 0.7), (2.76, .3, .25), (5.4, .12, .1), (8.93, .05, .05)))
    return fade(x, 0.001, 0.05)


def ep(f, dur):
    L = dur + 0.4
    t = tt(L)
    I = 1.6 * np.exp(-t * 5) + 0.25
    x = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * t))
    x += 0.15 * np.sin(2 * np.pi * 7 * f * t) * np.exp(-t * 18)
    env = np.exp(-t * 1.0) * np.minimum(t / 0.004, 1) * np.where(t > dur, np.exp(-(t - dur) / 0.12), 1)
    return x * env * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))


def upright(f, dur):
    L = dur + 0.2
    t = tt(L)
    x = sum(a * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (2.5 + 1.8 * k)) for k, a in ((1, 1), (2, .5), (3, .25), (4, .12), (5, .06)))
    thump = lp(rng(3).standard_normal(len(t)), 300) * np.exp(-t / 0.01) * 0.3
    env = np.minimum(t / 0.006, 1) * np.where(t > dur, np.exp(-(t - dur) / 0.05), 1)
    return (x + thump) * env


def tuba(f, dur):
    t = tt(dur)
    fv = f * 2 ** ((-0.35 * np.exp(-t / 0.05)) / 12)
    x = additive(fv, 14, lambda k: (k ** -1.2) * np.exp(-k / 4.5))
    env = np.minimum(t / 0.04, 1) * np.clip((dur - t) / 0.08, 0, 1) * (1 - 0.3 * np.minimum(t / 0.5, 1))
    return x * env


def kazoo(f, dur, seed=0):
    t = tt(dur)
    vib = 1 + 0.018 * np.minimum(t / 0.35, 1) * np.sin(2 * np.pi * 5.3 * t + seed)
    fv = f * vib * 2 ** ((-0.25 * np.exp(-t / 0.06)) / 12)
    x = additive(fv, 35, lambda k: 1 / k)
    x = np.tanh(1.5 * x)
    y = 0.6 * peak(x, 700, 3) + 0.5 * peak(x, 1600, 4) + 0.3 * peak(x, 2900, 5) + 0.1 * x
    env = np.minimum(t / 0.03, 1) * np.clip((dur - t) / 0.06, 0, 1)
    return y * env


def accordion(f, dur):
    t = tt(dur)
    x = np.zeros(len(t))
    for det in (0.996, 1.004):
        x += additive(np.full(len(t), f * det), 10, lambda k: (k ** -0.9) * (0.6 if k % 2 == 0 else 1))
    env = np.minimum(t / 0.03, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return lp(x, 3000) * env


def strings(f, dur, att=0.4, rel=0.6):
    L = dur + rel
    t = tt(L)
    x = np.zeros(len(t))
    for i, det in enumerate((0.997, 1.0, 1.0035)):
        fv = f * det * (1 + 0.003 * np.sin(2 * np.pi * (5 + i * 0.4) * t + i))
        x += additive(fv, 16, lambda k: (1 / k) * np.exp(-k / 7))
    env = np.minimum(t / att, 1) * np.where(t > dur, np.exp(-(t - dur) / (rel / 3)), 1)
    return x * env


def choir(f, dur, att=0.5):
    x = strings(f, dur, att, 0.8)
    return sum(g * peak(x, ff, q) for ff, q, g in VOW_AH)


def flute(f, dur):
    t = tt(dur)
    vib = 1 + 0.006 * np.minimum(t / 0.3, 1) * np.sin(2 * np.pi * 5 * t)
    ph = 2 * np.pi * phase_of(f * vib)
    x = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.04 * np.sin(3 * ph)
    breath = peak(rng(int(f)).standard_normal(len(t)), f, 8) * 0.08
    env = np.minimum(t / 0.06, 1) * np.clip((dur - t) / 0.08, 0, 1)
    return (x + breath) * env


def vibes(f, dur):
    t = tt(max(dur, 1.0) + 0.5)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 6)
    return fade(x * np.exp(-t * 1.6) * (1 + 0.3 * np.sin(2 * np.pi * 5.5 * t)), 0.002, 0.05)


def piano(f, dur):
    L = dur + 0.5
    t = tt(L)
    x = np.zeros(len(t))
    for k in range(1, 11):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > SR * 0.42:
            break
        x += (k ** -1.1) * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.7 + 0.45 * k))
    env = np.minimum(t / 0.003, 1) * np.where(t > dur, np.exp(-(t - dur) / 0.1), 1)
    return x * env


def square_lead(f, dur):
    t = tt(dur)
    fv = f * (1 + 0.01 * np.minimum(t / 0.2, 1) * np.sin(2 * np.pi * 6 * t))
    x = additive(fv, 25, lambda k: (1 / k) if k % 2 else 0)
    env = np.minimum(t / 0.01, 1) * np.clip((dur - t) / 0.04, 0, 1)
    return lp(x, 4000) * env


def kick(punch=1.0):
    t = tt(0.45)
    f = 48 + 110 * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * phase_of(f)) * np.exp(-t / 0.16)
    x += hp(rng(5).standard_normal(len(t)), 3000) * np.exp(-t / 0.003) * 0.3 * punch
    return np.tanh(1.5 * x)


def snare(soft=False):
    t = tt(0.3)
    nz = bp(rng(6).standard_normal(len(t)), 1500, 9000) * np.exp(-t / (0.05 if soft else 0.09))
    tone = np.sin(2 * np.pi * phase_of(190 + 60 * np.exp(-t / 0.01))) * np.exp(-t / 0.05)
    return nz * 0.8 + tone * 0.6


def clap():
    t = tt(0.35)
    nz = bp(rng(7).standard_normal(len(t)), 900, 6000)
    env = np.zeros(len(t))
    for o in (0, 0.011, 0.022):
        env += np.where(t >= o, np.exp(-(t - o) / 0.008), 0)
    env += np.where(t >= 0.03, np.exp(-(t - 0.03) / 0.11), 0)
    return nz * env


def hat(open_=False, seed=8):
    t = tt(0.3 if open_ else 0.06)
    return hp(rng(seed).standard_normal(len(t)), 7000) * np.exp(-t / (0.09 if open_ else 0.015))


def shaker(seed=9):
    t = tt(0.08)
    return bp(rng(seed).standard_normal(len(t)), 4000, 12000) * np.sin(np.pi * t / 0.08) ** 2


def rim():
    t = tt(0.08)
    return (np.sin(2 * np.pi * 1700 * t) * 0.5 + bp(rng(10).standard_normal(len(t)), 2000, 6000)) * np.exp(-t / 0.012)


def sub808(f, dur):
    t = tt(dur)
    fv = f * (1 + 0.8 * np.exp(-t / 0.02))
    x = np.tanh(1.8 * np.sin(2 * np.pi * phase_of(fv)))
    return x * np.minimum(t / 0.003, 1) * np.clip((dur - t) / 0.05, 0, 1)


def fart_bass(f, dur, seed=0):
    t = tt(dur)
    n = len(t)
    fv = f * (1 + 0.04 * smooth_noise(n, 12, seed)) * (1 - 0.06 * np.exp(-t / 0.03))
    ph = 2 * np.pi * phase_of(fv)
    src = np.tanh(4 * np.sin(ph)) + 0.4 * np.sin(2 * ph + 0.5)
    flutter = lp(0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 22 * t)), 120)
    y = lp(src * flutter, 900)
    y = y + 0.6 * np.sin(ph) * 0.8
    return y * np.minimum(t / 0.008, 1) * np.clip((dur - t) / 0.04, 0, 1)


def squeak_lead(f, dur, seed=0):
    t = tt(dur)
    n = len(t)
    fv = f * (1 + 0.02 * np.sin(2 * np.pi * 7 * t) + 0.012 * smooth_noise(n, 20, seed))
    ph = 2 * np.pi * phase_of(fv)
    src = np.tanh(2.5 * np.sin(ph)) + 0.3 * np.sin(3 * ph)
    y = bp(src * (0.75 + 0.25 * np.sin(2 * np.pi * 26 * t)), 300, 6000)
    return y * np.minimum(t / 0.015, 1) * np.clip((dur - t) / 0.04, 0, 1)


# ------------------------------------------------------------ helpers

def seq(buf, inst, notes, t0, beat, gain=1.0, **kw):
    """notes: list of (beat_pos, midi or list of midi, dur_beats[, vel])."""
    for nt in notes:
        pos, m, d = nt[:3]
        vel = nt[3] if len(nt) > 3 else 1.0
        ms = m if isinstance(m, (list, tuple)) else [m]
        for mm in ms:
            if mm is None:
                continue
            place(buf, inst(float(mtof(mm)), d * beat, **kw), t0 + pos * beat, gain * vel)


CH = {  # chord tones (midi, mid register)
    "C": [60, 64, 67], "Cmaj7": [60, 64, 67, 71], "Am7": [57, 60, 64, 67], "Dm7": [62, 65, 69, 72],
    "G7": [55, 59, 62, 65], "Dm": [62, 65, 69], "A7": [57, 61, 64, 67], "Gm": [55, 58, 62],
    "C7": [60, 64, 67, 70], "F": [53, 57, 60], "Bb": [58, 62, 65], "Fmaj7": [53, 57, 60, 64],
    "Gm7": [55, 58, 62, 65], "Bbmaj7": [58, 62, 65, 69], "Am": [57, 60, 64], "E7": [52, 56, 59, 62],
    "Em": [52, 55, 59], "Dm_": [50, 53, 57],
}


# ------------------------------------------------------------ tracks

def track_creator(dur=16.0):
    bpm = 100
    b = 60 / bpm
    out = np.zeros(int((dur + 2) * SR))
    prog = ["Cmaj7", "Am7", "Dm7", "G7"]
    mel = [(0, 76, .5), (.5, 79, .5), (1, 81, .5), (1.5, 79, .5), (2, 76, 1), (3, 74, .5), (3.5, 72, .5)]
    mel2 = [(0, 72, .5), (.5, 74, .5), (1, 76, .5), (1.5, 74, .5), (2, 72, .5), (2.5, 69, .5), (3, 71, 1)]
    nbars = int(dur / (4 * b)) + 1
    for bar in range(nbars):
        t0 = bar * 4 * b
        c = CH[prog[bar % 4]]
        seq(out, ep, [(0, c, 1.4, .5), (1.5, c, .9, .35), (3, c, .9, .3)], t0, b, 0.22)
        root = c[0] - 24
        seq(out, pizz, [(0, root, 1), (2, root + 7, 1)], t0, b, 0.5)
        seq(out, glock, mel if bar % 2 == 0 else mel2, t0, b, 0.16)
        for k in range(4):
            place(out, kick(0.5), t0 + k * b * 2, 0.35) if k < 2 else None
        place(out, snare(True), t0 + b, 0.12)
        place(out, snare(True), t0 + 3 * b, 0.12)
        for k in range(8):
            place(out, hat(seed=k), t0 + k * b / 2, 0.05)
    return out


def track_lord(dur=32.0):
    bpm = 108
    b = 60 / bpm
    out = np.zeros(int((dur + 2) * SR))
    prog = [("Dm", 50), ("A7", 49), ("Dm", 50), ("Gm", 46), ("C7", 48), ("F", 53), ("Gm", 43), ("A7", 45)]
    nbars = int(dur / (4 * b)) + 1
    for bar in range(nbars):
        t0 = bar * 4 * b
        name, bass = prog[bar % 8]
        c = CH[name]
        tones = [c[0] + 12, c[1] + 12, c[2] + 12, c[1] + 12]
        notes = []
        for beat in range(4):
            pat = [tones[0], tones[2], tones[1], tones[2]] if beat % 2 == 0 else [tones[0] + 12 if beat == 3 else tones[1], tones[2], tones[0], tones[2]]
            for s in range(4):
                notes.append((beat + s * 0.25, pat[s], 0.25, 0.8 if s == 0 else 0.55))
        seq(out, harpsichord, notes, t0, b, 0.13)
        bl = [(0, bass, 1), (1, bass + 12, 1, .7), (2, bass + 7, 1), (3, bass + 12, 1, .7)]
        seq(out, harpsichord, bl, t0, b, 0.2)
        seq(out, tuba, [(0, bass - 12, 1.8), (2, bass - 5, 1.8)], t0, b, 0.12)
    return out


def track_tension(dur=24.0):
    out = np.zeros(int((dur + 2) * SR))
    t = 0.0
    k = 0
    while t < dur:
        u = t / dur
        b = 60 / (100 + 70 * u)
        m = [40, 40, 41, 40][k % 4] + (1 if u > 0.5 else 0)
        place(out, strings(float(mtof(m)), b * 0.45, 0.01, 0.1), t, 0.25 + 0.25 * u)
        place(out, strings(float(mtof(m - 12)), b * 0.45, 0.01, 0.1), t, 0.2 + 0.2 * u)
        t += b / 2
        k += 1
    tr = tt(dur)
    trem = (0.5 + 0.5 * np.sin(2 * np.pi * 11 * tr))
    hi = strings(float(mtof(76)), dur, 3.0, 0.5)[: len(tr)] + strings(float(mtof(77)), dur, 3.0, 0.5)[: len(tr)]
    place(out, hi * trem * (tr / dur) ** 1.5, 0, 0.12)
    rise = np.sin(2 * np.pi * phase_of(np.geomspace(110, 440, len(tr)))) * (tr / dur) ** 2
    place(out, rise, 0, 0.1)
    return out


def track_muzak(dur=48.0):
    bpm = 116
    b = 60 / bpm
    out = np.zeros(int((dur + 2) * SR))
    prog = ["Fmaj7", "Bbmaj7", "Gm7", "C7"]
    melody = [
        [(0, 69, 2), (2, 67, 1), (3, 65, 1)],
        [(0, 74, 3), (3, 72, 1)],
        [(0, 70, 1.5), (1.5, 69, .5), (2, 67, 2)],
        [(0, 64, 1), (1, 65, 1), (2, 67, 2)],
        [(0, 69, 2), (2, 72, 1), (3, 77, 1)],
        [(0, 76, 3), (3, 74, 1)],
        [(0, 72, 1.5), (1.5, 70, .5), (2, 69, 1), (3, 67, 1)],
        [(0, 65, 4)],
    ]
    nbars = int(dur / (4 * b)) + 1
    for bar in range(nbars):
        t0 = bar * 4 * b
        c = CH[prog[bar % 4]]
        seq(out, ep, [(0, c, 1.4, .45), (1.5, c, 0.4, .3), (2.5, c, 1.2, .35)], t0, b, 0.15)
        r = c[0] - 24 if c[0] - 24 >= 28 else c[0] - 12
        seq(out, upright, [(0, r, 1.4), (1.5, r + 7, .5, .8), (2, r + 7, 1.4), (3.5, r, .5, .8)], t0, b, 0.5)
        seq(out, vibes, melody[bar % 8], t0, b, 0.18)
        for k in range(16):
            place(out, shaker(k), t0 + k * b / 4, 0.05 if k % 2 else 0.08)
        for p in (0, 1.5, 3) if bar % 2 == 0 else (1, 2.5):
            place(out, rim(), t0 + p * b, 0.06)
        place(out, kick(0.2), t0, 0.2)
        place(out, kick(0.2), t0 + 2 * b, 0.15)
    return out


def track_sad_clown(dur=40.0):
    bpm = 88
    b = 60 / bpm
    out = np.zeros(int((dur + 3) * SR))
    prog = ["Am", "Am", "E7", "E7", "Am", "Am", "Dm", "E7", "Am", "Am", "E7", "E7", "Dm", "Am", "E7", "Am"]
    mel = [
        [(0, 69, 1), (1, 72, 1), (2, 71, 1)], [(0, 69, 2), (2, 64, 1)],
        [(0, 68, 1), (1, 71, 1), (2, 69, 1)], [(0, 68, 2), (2, 64, 1)],
        [(0, 69, 1), (1, 72, 1), (2, 76, 1)], [(0, 74, 2), (2, 72, 1)],
        [(0, 71, 1), (1, 69, 1), (2, 65, 1)], [(0, 64, 3)],
        [(0, 72, 1), (1, 71, 1), (2, 69, 1)], [(0, 64, 2), (2, 60, 1)],
        [(0, 62, 1), (1, 64, 1), (2, 68, 1)], [(0, 71, 2), (2, 68, 1)],
        [(0, 69, 1), (1, 65, 1), (2, 62, 1)], [(0, 60, 1), (1, 64, 1), (2, 69, 1)],
        [(0, 68, 1.5), (1.5, 66, .5), (2, 64, 1)], [(0, 57, 3)],
    ]
    nbars = int(dur / (3 * b)) + 1
    for bar in range(nbars):
        t0 = bar * 3 * b
        c = CH[prog[bar % 16]]
        root = c[0] - 24
        seq(out, tuba, [(0, root if bar % 2 == 0 else root + 7, 0.9)], t0, b, 0.45)
        seq(out, accordion, [(1, c, 0.6, .6), (2, c, 0.6, .5)], t0, b, 0.07)
        seq(out, kazoo, mel[bar % 16], t0, b, 0.11)
    return out


def track_outro(dur=26.0):
    bpm = 92
    b = 60 / bpm
    out = np.zeros(int((dur + 4) * SR))
    prog = [("F", 41), ("C", 40), ("Dm", 38), ("Bb", 34), ("F", 41), ("C", 36), ("Bb", 34), ("C", 36), ("F", 41)]
    mel = [
        [(0, 72, 1), (1, 74, 1), (2, 76, 2)], [(0, 76, 1), (1, 74, 1), (2, 72, 2)],
        [(0, 74, 1), (1, 76, 1), (2, 77, 2)], [(0, 77, 1), (1, 76, 1), (2, 74, 2)],
        [(0, 72, 1), (1, 76, 1), (2, 79, 2)], [(0, 79, 1), (1, 81, 1), (2, 79, 2)],
        [(0, 77, 1), (1, 76, 1), (2, 74, 2)], [(0, 74, 2), (2, 76, 2)], [(0, 77, 4)],
    ]
    nbars = min(len(prog), int(dur / (4 * b)) + 1)
    for bar in range(nbars):
        t0 = bar * 4 * b
        name, bass = prog[bar]
        c = CH[name]
        last = bar == nbars - 1
        place(out, sum_inst(strings, c, 4 * b * (1.6 if last else 1.0)), t0, 0.09)
        seq(out, piano, [(0, bass, 4)], t0, b, 0.3)
        arp = [(i * 0.5, c[i % 3] + 12, 0.6, 0.5) for i in range(8)]
        seq(out, piano, arp, t0, b, 0.12)
        seq(out, glock, mel[bar], t0, b, 0.13)
        place(out, kick(0.3), t0, 0.2)
        if not last:
            place(out, kick(0.3), t0 + 2 * b, 0.15)
            place(out, snare(True), t0 + b, 0.06)
            place(out, snare(True), t0 + 3 * b, 0.06)
    return out


def sum_inst(inst, chord, dur):
    parts = [inst(float(mtof(m)), dur) for m in chord]
    L = max(len(p) for p in parts)
    out = np.zeros(L)
    for p in parts:
        out[: len(p)] += p
    return out


# ------------------------------------------------------------ vocoder remix

def channel_vocoder(mod, carrier, nb=28, lo=90, hi=8000):
    edges = np.geomspace(lo, hi, nb + 1)
    out = np.zeros(len(mod))
    for i in range(nb):
        sos = signal.butter(2, [edges[i], edges[i + 1]], "band", fs=SR, output="sos")
        mb = signal.sosfilt(sos, mod)
        env = lp(np.abs(mb), 45)
        cb = signal.sosfilt(sos, carrier)
        cenv = lp(np.abs(cb), 20) + 1e-3
        out += cb / cenv * env
    sib = hp(mod, 5000) * 0.6
    return out + sib


def syllable_onsets(x, min_gap=0.11):
    env = lp(np.abs(x), 18)
    hop = int(0.01 * SR)
    e = env[::hop]
    d = np.diff(e, prepend=0)
    thr = 0.15 * e.max()
    ons = []
    for i in range(1, len(e) - 1):
        if d[i] > 0.012 * e.max() and d[i] >= d[i - 1] and d[i] >= d[i + 1] and e[i + 3 if i + 3 < len(e) else i] > thr:
            t = i * hop / SR
            if not ons or t - ons[-1] > min_gap:
                ons.append(t)
    return ons


def autotune_voice(x, notes):
    """x: voice @SR. notes: midi per syllable (cycled). Returns robotic sung version."""
    ons = syllable_onsets(x)
    if not ons:
        ons = [0.0]
    n = len(x)
    f = np.full(n, float(mtof(notes[0])))
    for i, o in enumerate(ons):
        f[int(o * SR):] = float(mtof(notes[i % len(notes)]))
    f = lp(f, 40)  # tiny glide
    car = additive(f, 60, lambda k: 1 / k) + 0.5 * additive(f * 2, 30, lambda k: 1 / k)
    v = channel_vocoder(x, car)
    return norm(v, 0.9)


def track_remix(voice_r1, voice_r2, honk_sfx, wheeze_sfx, dur=16.0):
    bpm = 120
    b = 60 / bpm
    bar = 4 * b
    out = np.zeros(int((dur + 2) * SR))
    prog = [("Dm", 38), ("Bb", 34), ("F", 41), ("C", 36)]
    v1 = autotune_voice(voice_r1, [57, 57, 60, 57, 53, 50])
    v2 = autotune_voice(voice_r2, [53, 55, 57, 55, 50, 50])
    nbars = int(dur / bar)
    vox_bus = np.zeros_like(out)
    hook = [(0, 74, .5), (.75, 74, .25), (1, 72, .5), (1.5, 69, .5), (2.5, 67, .5), (3, 69, 1)]
    for i in range(nbars):
        t0 = i * bar
        name, bass = prog[i % 4]
        c = CH[name]
        full = i >= 2
        # vocals (placed on a separate bus, see below)
        place(vox_bus, v1 if i % 2 == 0 else v2, t0 + 0.05, 1.0)
        if i == 1:
            place(out, honk_sfx, t0 + 3 * b, 0.35)
        if full:
            for k in range(4):
                place(out, kick(), t0 + k * b, 0.75)
                place(out, hat(True, k), t0 + k * b + b / 2, 0.12)
            place(out, clap(), t0 + b, 0.35)
            place(out, clap(), t0 + 3 * b, 0.35)
            bl = [(0, bass, .45), (.5, bass, .4), (1.5, bass + 12, .4), (2, bass, .45), (2.75, bass + 7, .4), (3.5, bass + 12, .4)]
            seq(out, fart_bass, bl, t0, b, 0.42)
            seq(out, squeak_lead, hook if i % 2 == 0 else [(0, 77, .5), (.5, 76, .5), (1, 74, 1), (2.5, 72, .5), (3, 74, 1)], t0, b, 0.12)
            place(out, sum_inst(strings, [m + 12 for m in c], bar), t0, 0.03)
            if i % 2 == 1:
                place(out, honk_sfx, t0 + 3.5 * b, 0.3)
        else:
            place(out, kick(), t0, 0.6)
            seq(out, fart_bass, [(0, bass, 1.5)], t0, b, 0.3)
            place(out, sum_inst(strings, [m + 12 for m in c], bar), t0, 0.05)
        if i == nbars - 1:
            # stutter wheeze chops
            for k in range(4):
                place(out, wheeze_sfx[: int(0.12 * SR)], t0 + 2 * b + k * b / 4, 0.4)
    venv = lp(np.abs(vox_bus), 6)
    venv = venv / (venv.max() + 1e-9)
    duck = lp(1 - 0.55 * np.clip(venv * 4, 0, 1), 8)
    out = out / (np.sqrt(np.mean(out ** 2)) + 1e-9) * 0.12
    vox_bus = vox_bus / (np.sqrt(np.mean(vox_bus[vox_bus != 0] ** 2)) + 1e-9) * 0.16
    return out * duck + hp(vox_bus, 150)


TRACKS = {
    "creator": track_creator, "lord": track_lord, "tension": track_tension, "muzak": track_muzak,
    "sad_clown": track_sad_clown, "outro": track_outro,
}


# ------------------------------------------------------------ v2: TD-PSOLA hard autotune (keeps words intelligible)

def f0_track(x, hop=240, win=1440, fmin=70, fmax=420):
    n = len(x)
    frames = range(0, max(1, n - win), hop)
    f0 = []
    lag_min, lag_max = int(SR / fmax), int(SR / fmin)
    for i in frames:
        seg = x[i:i + win] * np.hanning(win)
        e = np.sum(seg ** 2)
        if e < 1e-4 * win * (np.max(np.abs(x)) ** 2 + 1e-12):
            f0.append(0.0)
            continue
        ac = np.correlate(seg, seg, "full")[win - 1:]
        ac = ac / (ac[0] + 1e-12)
        k = lag_min + int(np.argmax(ac[lag_min:lag_max]))
        f0.append(SR / k if ac[k] > 0.45 else 0.0)
    f0 = np.array(f0)
    # median-smooth
    sm = f0.copy()
    for i in range(1, len(f0) - 1):
        trio = f0[i - 1:i + 2]
        if np.all(trio > 0):
            sm[i] = np.median(trio)
    return sm, hop


def psola_retune(x, notes):
    """Hard-snap each syllable of x to the next note in `notes` (midi) using TD-PSOLA."""
    f0, hop = f0_track(x)
    times = np.arange(len(f0)) * hop + 720
    voiced = np.interp(np.arange(len(x)), times, (f0 > 0).astype(float)) > 0.5
    f0s = np.interp(np.arange(len(x)), times[f0 > 0], f0[f0 > 0]) if np.any(f0 > 0) else np.full(len(x), 120.0)
    # analysis pitch marks (periodic through voiced regions)
    marks = []
    i = 0
    while i < len(x):
        if voiced[i]:
            p = int(SR / f0s[i])
            seg = x[i:i + p]
            if len(seg) == 0:
                break
            marks.append(i + int(np.argmax(seg)))
            i = marks[-1] + max(20, int(SR / f0s[marks[-1]] * 0.9))
        else:
            i += 48
    marks = np.array(marks)
    ons = syllable_onsets(x) or [0.0]
    tgt = np.full(len(x), float(mtof(notes[0])))
    for k, o in enumerate(ons):
        tgt[int(o * SR):] = float(mtof(notes[k % len(notes)]))
    out = np.zeros(len(x) + 4000)
    wsum = np.zeros(len(x) + 4000)
    if len(marks) > 2:
        t = marks[0]
        while t < len(x) - 1:
            if not voiced[min(t, len(x) - 1)]:
                t += 48
                continue
            j = int(np.argmin(np.abs(marks - t)))
            m = marks[j]
            P = int(SR / f0s[m])
            a, b = max(0, m - P), min(len(x), m + P)
            g = x[a:b] * np.hanning(b - a)
            o0 = t - (m - a)
            if o0 >= 0:
                out[o0:o0 + len(g)] += g
                wsum[o0:o0 + len(g)] += np.hanning(b - a)
            t += int(SR / tgt[t])
    vm = lp(voiced.astype(float), 30)
    y = out[: len(x)] * vm + x * (1 - vm)
    return y


def autotune_voice(x, notes):
    """Intelligible 'autotuned' vocal: pitch-snapped dry voice + quiet vocoder harmony."""
    x = x / (np.max(np.abs(x)) + 1e-9)
    sung = psola_retune(x, notes)
    ons = syllable_onsets(x) or [0.0]
    f = np.full(len(x), float(mtof(notes[0])))
    for i, o in enumerate(ons):
        f[int(o * SR):] = float(mtof(notes[i % len(notes)]))
    f = lp(f, 40)
    car = additive(f, 60, lambda k: 1 / k) + 0.5 * additive(f * 1.5, 30, lambda k: 1 / k)
    harm = channel_vocoder(x, car)
    y = norm(sung) + 0.22 * norm(harm)
    y = y + 0.18 * np.concatenate([np.zeros(int(0.012 * SR)), y[:-int(0.012 * SR)]])
    return norm(reverb(y, 0.6, 0.12)[: len(x) + int(0.3 * SR)], 0.9)
