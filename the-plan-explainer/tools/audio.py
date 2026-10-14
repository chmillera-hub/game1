#!/usr/bin/env python3
"""Soundtrack: narration + synthesized music + sound effects -> build/mix.wav (+ preview.mp3)

Everything here is generated from numbers, no samples: a cheerful corporate
ukulele jingle that slowly falls apart, waiting-room muzak with a tape stop, a
quiet piano pad for the honest part, and a box of little sound effects.
Timing comes from build/timeline.json (narration) and build/cues.json (what
src/scenes.js asks for), so sound always lines up with the picture.
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
SR = 48000
RNG = np.random.default_rng(1234)


# ---------------------------------------------------------------------------- helpers
def secs(n):
    return int(round(n * SR))


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def m(name):
    """'C5' -> midi number."""
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTE[pitch]


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def fade(x, a=0.005, b=0.005):
    x = x.copy()
    na, nb = min(len(x), secs(a)), min(len(x), secs(b))
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nb:
        x[-nb:] *= np.linspace(1, 0, nb)
    return x


def bandpass(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lowpass(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def highpass(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def noise(n):
    return RNG.uniform(-1, 1, n)


def add(buf, x, at, gain=1.0, pan=0.0):
    """Mix mono or stereo x into stereo buf at time `at` (seconds)."""
    i = secs(at)
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    if n <= 0:
        return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        buf[i:i + n, 0] += x[:n] * gain * l * 1.414
        buf[i:i + n, 1] += x[:n] * gain * r * 1.414
    else:
        buf[i:i + n] += x[:n] * gain


# ---------------------------------------------------------------------------- instruments
_pluck_cache = {}


def pluck(freq, dur=1.2, bright=0.6, decay=0.9965, seed=0):
    """Karplus-Strong plucked string (ukulele-ish), cached per pitch."""
    key = (round(freq, 2), dur, bright, decay, seed)
    if key in _pluck_cache:
        return _pluck_cache[key]
    n = secs(dur)
    p = max(2, int(round(SR / freq)))
    rng = np.random.default_rng(seed + int(freq))
    burst = rng.uniform(-1, 1, p)
    burst = lfilter([bright, 1 - bright], [1], burst)  # soften the attack
    x = np.zeros(n)
    x[:p] = burst
    a = np.zeros(p + 2)
    a[0] = 1
    a[p] = -0.5 * decay
    a[p + 1] = -0.5 * decay
    y = lfilter([1], a, x)
    y = highpass(y, 120)
    y = fade(y, 0.001, 0.05) / (np.max(np.abs(y)) + 1e-9)
    _pluck_cache[key] = y
    return y


def bell(freq, dur=1.4, bright=1.0):
    """Glockenspiel / music box: inharmonic partials with fast decays."""
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, amp, tau in [(1, 1.0, 0.9), (2.76, 0.45 * bright, 0.35), (5.4, 0.22 * bright, 0.15), (8.93, 0.1 * bright, 0.07)]:
        if freq * ratio < SR / 2.2:
            y += amp * np.sin(2 * np.pi * freq * ratio * t) * env_exp(n, tau)
    return fade(y, 0.002, 0.02) * 0.6


def whistle(freq, dur):
    """Human-ish whistle: sine with scoop, vibrato and a little breath."""
    n = secs(dur + 0.08)
    t = np.arange(n) / SR
    scoop = 1 - 0.018 * np.exp(-t / 0.035)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.12) / 0.15, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * scoop * vib) / SR
    y = np.sin(ph) + 0.08 * np.sin(2 * ph)
    breath = bandpass(noise(n), freq * 0.8, min(freq * 1.6, 20000)) * 0.12
    e = np.clip(t / 0.04, 0, 1) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)
    return (y + breath) * e * 0.5


def bass(freq, dur):
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    e = np.minimum(1, t / 0.006) * (0.55 + 0.45 * np.exp(-t / 0.18))
    return fade(np.tanh(1.4 * y * e) * 0.7, 0.002, 0.05)


def kick():
    n = secs(0.3)
    t = np.arange(n) / SR
    f = 45 + 70 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)


def clap():
    n = secs(0.25)
    x = np.zeros(n)
    for k, d in enumerate([0, 0.009, 0.019]):
        i = secs(d)
        seg = noise(secs(0.012)) * (0.7 + 0.15 * k)
        x[i:i + len(seg)] += seg
    tail = noise(n) * np.exp(-np.arange(n) / (0.055 * SR)) * 0.6
    tail[: secs(0.02)] = 0
    return bandpass(x + tail, 900, 3500) * 0.9


def shaker(acc=1.0):
    n = secs(0.07)
    e = np.minimum(1, np.arange(n) / (0.015 * SR)) * np.exp(-np.arange(n) / (0.02 * SR))
    return highpass(noise(n), 6000) * e * 0.35 * acc


def piano(freq, dur=2.5, vel=0.8):
    n = secs(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(1, 9):
        fk = k * freq * np.sqrt(1 + 0.0004 * k * k)
        if fk > SR / 2.2:
            break
        y += (1 / k ** 1.4) * np.sin(2 * np.pi * fk * t) * np.exp(-t / (1.8 / k ** 0.7))
    ham = lowpass(noise(secs(0.01)), 3000) * 0.15
    y[: len(ham)] += ham
    return fade(y * vel * 0.45, 0.003, 0.3)


def epiano(freq, dur=1.6, vel=0.8):
    """Two-operator FM electric piano (waiting-room muzak)."""
    n = secs(dur)
    t = np.arange(n) / SR
    idx = 0.25 + 1.2 * np.exp(-t / 0.35)
    mod = np.sin(2 * np.pi * freq * t)
    y = np.sin(2 * np.pi * freq * t + idx * mod) * np.exp(-t / 1.1)
    y += 0.12 * np.sin(2 * np.pi * freq * 14 * t) * np.exp(-t / 0.05)
    return fade(y * vel * 0.4, 0.002, 0.25)


def pad(freqs, dur, attack=1.4, release=1.8):
    n = secs(dur + release)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.0045):
            ff = f * (1 + det)
            y += np.sin(2 * np.pi * ff * t + RNG.uniform(0, 6.28)) + 0.18 * np.sin(4 * np.pi * ff * t)
    e = np.clip(t / attack, 0, 1) * np.clip((dur + release - t) / release, 0, 1)
    return lowpass(y * e, 2400) / (len(freqs) * 3) * 0.9


# ---------------------------------------------------------------------------- the jingle
CHORDS = {  # ukulele-range voicings
    "C": ["G4", "C5", "E5", "C6"], "G": ["G4", "B4", "D5", "G5"],
    "Am": ["A4", "C5", "E5", "A5"], "F": ["A4", "C5", "F5", "A5"],
}
ROOTS = {"C": "C3", "G": "G2", "Am": "A2", "F": "F2"}
PROG = ["C", "G", "Am", "F"]
# melody: (beat in 16-beat phrase, note, beats)
MEL_A = [(0, "E5", .5), (.5, "G5", .5), (1, "C6", 1), (2, "G5", .5), (2.5, "E5", .5), (3, "G5", 1),
         (4, "D5", .5), (4.5, "G5", .5), (5, "B5", 1), (6, "A5", .5), (6.5, "G5", .5), (7, "D5", 1),
         (8, "C5", .5), (8.5, "E5", .5), (9, "A5", 1), (10, "G5", .5), (10.5, "E5", .5), (11, "C5", 1),
         (12, "A4", .5), (12.5, "C5", .5), (13, "F5", 1), (14, "E5", .5), (14.5, "D5", .5), (15, "C5", 1)]
MEL_B = [(0, "G5", 1), (1, "E5", .5), (1.5, "G5", .5), (2, "C6", 1.5), (3.5, "B5", .5),
         (4, "B5", 1), (5, "G5", .5), (5.5, "A5", .5), (6, "B5", 1.5), (7.5, "D6", .5),
         (8, "C6", 1), (9, "A5", .5), (9.5, "G5", .5), (10, "E5", 1.5), (11.5, "G5", .5),
         (12, "F5", 1), (13, "E5", .5), (13.5, "D5", .5), (14, "C5", 2)]
STRUM = [(0, "D", 1.0), (1, "D", 0.8), (1.5, "U", 0.6), (2.5, "U", 0.6), (3, "D", 0.85), (3.5, "U", 0.6)]


def jingle(t0, t1, bpm=112, decay=None, intro=True, start_bar=0):
    """The corporate ukulele jingle from t0 to t1 (seconds).

    decay: (d0, d1) times between which the band falls apart: it slows down,
    goes out of tune, gets muffled and players drop out.
    """
    dur = t1 - t0
    out = np.zeros((secs(dur) + secs(3), 2))
    rng = np.random.default_rng(7)

    def dec(t):
        if not decay:
            return 0.0
        return float(np.clip((t - decay[0]) / (decay[1] - decay[0]), 0, 1))

    # beat grid with a tempo that sags as the decay sets in
    beats = []
    t = t0
    while t < t1 + 0.5:
        beats.append(t)
        t += 60.0 / (bpm - 18 * dec(t))
    beat_times = np.array(beats)

    def at_beat(x):
        i = int(np.floor(x))
        if i + 1 >= len(beat_times):
            return beat_times[-1]
        return beat_times[i] + (beat_times[i + 1] - beat_times[i]) * (x - i)

    def cents(d):
        return 2 ** ((rng.normal(0, 1) * 30 * d) / 1200)

    nbars = len(beat_times) // 4
    for bar in range(nbars):
        gbar = bar + start_bar
        chord = PROG[gbar % 4]
        bt = bar * 4
        tb = at_beat(bt)
        if tb >= t1:
            break
        d = dec(tb)
        full = not (intro and gbar == 0)
        # ukulele strums
        for beat, direction, acc in STRUM:
            ts = at_beat(bt + beat)
            notes = CHORDS[chord] if direction == "D" else CHORDS[chord][::-1]
            for k, nn in enumerate(notes):
                f = midi(m(nn)) * cents(d)
                y = pluck(f, 1.0, 0.55, 0.996 - 0.002 * d, seed=k)
                add(out, y, ts - t0 + k * 0.011, 0.20 * acc * (1 - 0.35 * d), pan=-0.35)
        if full:
            # bass
            for beat, dl in [(0, 1.6), (2, 1.2), (3.5, 0.4)]:
                if d > 0.9 and beat == 3.5:
                    continue
                f = midi(m(ROOTS[chord]) + (7 if beat == 3.5 else 0)) * cents(d * 0.5)
                add(out, bass(f, dl * 60 / bpm), at_beat(bt + beat) - t0, 0.42)
            # drums: leave one by one
            if d < 0.8:
                for beat in (0, 2):
                    add(out, kick(), at_beat(bt + beat) - t0, 0.55 * (1 - d))
                for beat in (1, 3):
                    add(out, clap(), at_beat(bt + beat) - t0, 0.24 * (1 - d), pan=0.1)
            if d < 0.4:
                for e8 in range(8):
                    add(out, shaker(1.0 if e8 % 2 else 0.6), at_beat(bt + e8 * 0.5) - t0, 0.5 * (1 - d / 0.4), pan=0.4)
            # melody: glockenspiel phrase A, whistled phrase B
            phrase = (gbar - 1) // 4
            mel = MEL_A if phrase % 2 == 0 else MEL_B
            for beat, nn, ln in mel:
                if int(beat // 4) != (gbar - 1) % 4:
                    continue
                if d > 0.55 and rng.random() < d * 0.7:
                    continue  # the lead player keeps missing notes
                tm = at_beat(bt + beat % 4) - t0
                f = midi(m(nn)) * cents(d)
                if phrase % 2 == 0:
                    add(out, bell(f, 1.2), tm, 0.30 * (1 - 0.4 * d), pan=0.35)
                else:
                    add(out, whistle(f, ln * 60 / bpm * 0.95), tm, 0.26 * (1 - 0.4 * d), pan=0.25)
    out = out[: secs(dur) + secs(1.5)]

    if decay:
        # muffle progressively: block-wise low-pass with a falling cutoff
        blk = 1024
        zis = [np.zeros(2), np.zeros(2)]
        res = np.zeros_like(out)
        for i in range(0, len(out), blk):
            tt = t0 + i / SR
            cutoff = 15000 * (1 - dec(tt)) ** 1.6 + 1300
            b_, a_ = butter(2, min(cutoff, 20000), fs=SR)
            for ch in range(2):
                res[i:i + blk, ch], zis[ch] = lfilter(b_, a_, out[i:i + blk, ch], zi=zis[ch])
        out = res
    return out


def muzak(t0, t1):
    """Waiting-room version: slow electric piano through a tiny ceiling speaker."""
    dur = t1 - t0
    out = np.zeros(secs(dur) + secs(2))
    bpm = 84
    beat = 60 / bpm
    nbars = int(dur / (beat * 4)) + 2
    for bar in range(nbars):
        chord = PROG[bar % 4]
        tb = bar * 4 * beat
        for k, nn in enumerate(CHORDS[chord][:3]):
            y = epiano(midi(m(nn) - 12), 4 * beat + 0.4, 0.5)
            i = secs(tb + k * 0.02)
            n = min(len(y), len(out) - i)
            if n > 0:
                out[i:i + n] += y[:n] * 0.5
        mel = MEL_A if (bar // 4) % 2 == 0 else MEL_B
        for bt, nn, ln in mel:
            if int(bt // 4) != bar % 4:
                continue
            y = epiano(midi(m(nn)), ln * beat + 0.6, 0.7)
            i = secs(tb + (bt % 4) * beat)
            n = min(len(y), len(out) - i)
            if n > 0:
                out[i:i + n] += y[:n] * 0.8
    out = out[: secs(dur)]
    # wobbly tape + tiny speaker + hiss
    t = np.arange(len(out)) / SR
    wow = 1 + 0.003 * np.sin(2 * np.pi * 0.55 * t) + 0.0012 * np.sin(2 * np.pi * 6.1 * t)
    pos = np.clip(np.cumsum(wow) - wow[0], 0, len(out) - 1)
    out = np.interp(pos, np.arange(len(out)), out)
    out = bandpass(out, 320, 3200, 3) + highpass(noise(len(out)), 4000) * 0.004
    # tape stop over the last 0.75 s
    ns = secs(0.75)
    if len(out) > ns:
        head, tail = out[:-ns], out[-ns:]
        rate = (1 - np.linspace(0, 1, ns)) ** 1.4
        p = np.cumsum(rate)
        p = p / p[-1] * (ns * 0.42)
        stopped = np.interp(p, np.arange(ns), tail) * np.linspace(1, 0.2, ns)
        out = np.concatenate([head, stopped])
    return np.stack([out, out], axis=1)


SAD = [("Am", ["A3", "C4", "E4"], "A2"), ("F", ["F3", "A3", "C4"], "F2"),
       ("C", ["E3", "G3", "C4"], "C3"), ("G", ["D3", "G3", "B3"], "G2")]


def sincere(t0, t1, swell_at=None):
    """Quiet piano and pad for the honest part."""
    dur = t1 - t0
    out = np.zeros((secs(dur) + secs(4), 2))
    beat = 60 / 66
    bar_len = 4 * beat
    nbars = int(dur / bar_len) + 1
    for bar in range(nbars):
        name, tones, root = SAD[bar % 4]
        tb = bar * bar_len
        p = pad([midi(m(x)) for x in tones] + [midi(m(root))], bar_len + 0.2, attack=1.2, release=1.6)
        add(out, p, tb, 0.55)
        late = swell_at is not None and t0 + tb >= swell_at - 0.5
        pattern = [(0, m(root) + 12), (1, m(tones[1]) + 12), (2, m(tones[2]) + 12), (3, m(tones[1]) + 12)]
        if late:
            pattern += [(0.5, m(tones[2]) + 24), (2.5, m(tones[0]) + 24)]
        for bt, nn in pattern:
            add(out, piano(midi(nn), 2.6, 0.55 if bt in (0, 2) else 0.4), tb + bt * beat, 0.5, pan=-0.15 + 0.1 * (bt % 2))
    out = out[: secs(dur)]
    # fade in, swell, and a quick fade out at the hard cut to the end card
    t = np.arange(len(out)) / SR + t0
    g = np.clip((t - t0) / 2.5, 0, 1)
    if swell_at is not None:
        g *= 1 + 0.5 * np.clip((t - swell_at) / 1.5, 0, 1)
    g *= np.clip((t1 - t) / 0.12, 0, 1)
    return out * g[:, None]


def sting(t0, t1):
    """The System brings its jingle with it: one bright bar."""
    out = np.zeros((secs(t1 - t0) + secs(2), 2))
    beat = 60 / 112
    for k, nn in enumerate(["C5", "E5", "G5", "C6"]):
        add(out, bell(midi(m(nn)), 1.2), k * beat * 0.5, 0.3, pan=0.3)
    for bt, direction, acc in STRUM[:4]:
        notes = CHORDS["C"] if direction == "D" else CHORDS["C"][::-1]
        for k, nn in enumerate(notes):
            add(out, pluck(midi(m(nn)), 1.0, 0.55, seed=k), bt * beat + k * 0.011, 0.2 * acc, pan=-0.35)
    add(out, bass(midi(m("C3")), 1.5), 0, 0.4)
    n = secs(t1 - t0)
    out = out[:n]
    out[-secs(0.4):] *= np.linspace(1, 0, secs(0.4))[:, None]
    return out


# ---------------------------------------------------------------------------- sound effects
def sweep(f0, f1, dur):
    n = secs(dur)
    t = np.linspace(0, 1, n)
    f = f0 * (f1 / f0) ** t
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def place(parts, total):
    """Sum (offset_seconds, signal) pairs into one buffer `total` seconds long."""
    out = np.zeros(secs(total))
    for off, x in parts:
        i = secs(off)
        n = min(len(x), len(out) - i)
        if n > 0:
            out[i:i + n] += x[:n]
    return out


def sfx_bank():
    S = {}
    n = secs(0.09)
    S["pop"] = sweep(380, 950, 0.09) * np.exp(-np.arange(n) / (0.025 * SR)) * 0.8
    n = secs(0.06)
    S["tiny"] = sweep(900, 1600, 0.06) * np.exp(-np.arange(n) / (0.015 * SR)) * 0.6
    for name, dur, f0, f1 in [("whoosh", 0.7, 400, 5000), ("swoosh", 0.4, 600, 6000), ("slide", 0.6, 3000, 500)]:
        n = secs(dur)
        x = noise(n)
        y = np.zeros(n)
        blk = 512
        zi = np.zeros(4)  # 2nd-order band-pass = 4 state values
        for i in range(0, n, blk):
            k = i / n
            fc = f0 * (f1 / f0) ** k
            b_, a_ = butter(2, [max(80, fc * 0.6), min(20000, fc * 1.4)], btype="band", fs=SR)
            y[i:i + blk], zi = lfilter(b_, a_, x[i:i + blk], zi=zi)
        e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
        S[name] = y * e * 0.9
    n = secs(0.2)
    S["swipe"] = highpass(noise(n), 1500) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 0.5
    S["chime"] = place([(i * 0.07, bell(midi(x), 1.6)) for i, x in enumerate([84, 88, 91])], 1.8)
    S["sparkle"] = place([(i * 0.045, bell(midi(x), 0.8, 0.6) * 0.6) for i, x in enumerate([91, 95, 98, 100, 103])], 1.2)
    S["ding"] = bell(midi(81), 1.4)
    S["dingdong"] = place([(0, bell(midi(76), 1.6, 0.5)), (0.55, bell(midi(72), 1.6, 0.5))], 2.4)
    n = secs(0.3)
    t = np.arange(n) / SR
    S["coin"] = (np.sin(2 * np.pi * 2093 * t) + 0.6 * np.sin(2 * np.pi * 3520 * t) + 0.3 * np.sin(2 * np.pi * 5274 * t)) * np.exp(-t / 0.07) * 0.35
    n = secs(1.0)
    t = np.arange(n) / SR
    bellk = (np.sin(2 * np.pi * 2637 * t) + 0.7 * np.sin(2 * np.pi * 3951 * t)) * np.exp(-t / 0.35) * 0.4
    drawer = np.zeros(n)
    drawer[: secs(0.12)] = bandpass(noise(secs(0.12)), 300, 2500) * np.linspace(1, 0, secs(0.12)) * 0.5
    S["kaching"] = drawer + place([(0.08, bellk)], 1.0)
    n = secs(0.22)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.07)
    S["stamp"] = thump * 0.9 + lowpass(noise(n), 1800) * np.exp(-t / 0.025) * 0.6
    n = secs(0.35)
    t = np.arange(n) / SR
    S["thud"] = np.sin(2 * np.pi * np.cumsum(40 + 40 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.12)
    bz = np.zeros(secs(0.45))
    for i, f in enumerate([330, 247]):
        nn = secs(0.16)
        tt = np.arange(nn) / SR
        tone = np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.sin(2 * np.pi * f * tt) * 0.5
        bz[secs(i * 0.18): secs(i * 0.18) + nn] += lowpass(tone, 1800) * np.exp(-tt / 0.12)
    S["buzz"] = bz * 0.7
    n = secs(0.18)
    t = np.arange(n) / SR
    S["drop"] = np.sin(2 * np.pi * np.cumsum(90 + 120 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.05) * 0.6 + bandpass(noise(n), 1500, 6000) * np.exp(-t / 0.02) * 0.25
    n = secs(0.03)
    S["tick"] = highpass(noise(n), 2500) * np.exp(-np.arange(n) / (0.004 * SR)) * 0.7
    S["clock"] = bandpass(noise(n), 1800, 5000) * np.exp(-np.arange(n) / (0.003 * SR)) * 0.9
    n = secs(0.6)
    S["door"] = np.concatenate([S["tick"] * 1.2, lowpass(noise(n), 900) * np.sin(np.pi * np.linspace(0, 1, n)) * 0.35])
    sw = np.zeros(secs(0.1))
    click = highpass(noise(secs(0.006)), 2000) * 0.9
    sw[: len(click)] += click
    sw[secs(0.03): secs(0.03) + len(click)] += click * 0.7
    S["switch"] = sw
    ty = np.zeros(secs(0.55))
    for i in range(7):
        c = bandpass(noise(secs(0.012)), 1500, 7000) * np.exp(-np.arange(secs(0.012)) / (0.003 * SR))
        o = secs(i * 0.07 + RNG.uniform(0, 0.02))
        ty[o: o + len(c)] += c * RNG.uniform(0.5, 1.0)
    S["type"] = ty * 0.8
    n = secs(0.45)
    am = np.abs(lowpass(noise(n), 30)) * 4
    S["paper"] = bandpass(noise(n), 1200, 7000) * am * np.sin(np.pi * np.linspace(0, 1, n)) * 0.35
    n = secs(0.4)
    S["marker"] = bandpass(noise(n), 2200, 4500) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.5 * 0.3
    rp = np.zeros(secs(1.4))
    for i in range(12):
        o = secs(i * 0.09)
        rp[o: o + len(S["tiny"])] += S["tiny"] * (0.4 + 0.04 * i)
    S["ripple"] = rp
    sh = np.zeros(secs(1.8))
    for i, x in enumerate([69, 72, 76, 79, 81, 84, 88]):
        b_ = bell(midi(x), 1.2, 0.4) * 0.5
        o = secs(i * 0.11)
        sh[o: o + len(b_)] += b_[: len(sh) - o]
    S["shimmer"] = sh
    n = secs(0.25)
    t = np.arange(n) / SR
    S["balloonpop"] = highpass(noise(n), 800) * np.exp(-t / 0.012) * 0.9 + np.sin(2 * np.pi * 80 * t) * np.exp(-t / 0.04) * 0.4
    n = secs(0.5)
    t = np.arange(n) / SR
    cr = bandpass(noise(n), 1500, 8000) * np.exp(-t / 0.05)
    for f in (1900, 2600, 3700):
        cr += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.08) * 0.15
    S["crack"] = cr * 0.8
    return {k: fade(v.astype(np.float64), 0.001, 0.01) for k, v in S.items()}


# ---------------------------------------------------------------------------- narration
def load_voice(path):
    a, sr = sf.read(path, dtype="float64")
    if sr != SR:
        a = resample_poly(a, SR, sr)
    return a


def narration(tl, total):
    track = np.zeros(total)
    for lid in tl["order"]:
        L = tl["lines"][lid]
        a = load_voice(os.path.join(ROOT, L["wav"]))
        a = highpass(a, 75)
        # level each line to the same speech loudness
        active = a[np.abs(a) > 0.02]
        rms = np.sqrt(np.mean(active ** 2)) if len(active) else 0.1
        a *= 0.115 / rms
        for b0, b1 in L["bleeps"]:
            # the censor tone replaces the word, crossfading in and out over a few ms
            i0, i1 = secs(b0), min(secs(b1), len(a))
            seg = i1 - i0
            ramp = min(secs(0.006), seg // 2)
            mask = np.ones(seg)
            mask[:ramp] = np.linspace(0, 1, ramp)
            mask[-ramp:] = np.linspace(1, 0, ramp)
            tone = np.sin(2 * np.pi * 1000 * np.arange(seg) / SR) * 0.22 * mask
            a[i0:i1] = a[i0:i1] * (1 - mask) + tone
        if L.get("cut") is not None:
            a = a[: secs(L["cut"])]
            a[-secs(0.004):] *= np.linspace(1, 0, secs(0.004))
        i = secs(L["start"])
        n = min(len(a), total - i)
        track[i:i + n] += a[:n]
    return track


def reverb_ir(seconds=1.4, seed=3):
    n = secs(seconds)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], axis=1) * np.exp(-t / (seconds / 6.9))[:, None]
    ir[: secs(0.012)] = 0
    ir = np.stack([lowpass(ir[:, 0], 6000), lowpass(ir[:, 1], 6000)], axis=1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def follow(x, attack=0.03, release=0.35):
    """Envelope follower on |x| (for ducking)."""
    e = np.abs(x)
    hop = 240
    frames = e[: len(e) // hop * hop].reshape(-1, hop).max(axis=1)
    out = np.zeros_like(frames)
    ga, gr = np.exp(-hop / (attack * SR)), np.exp(-hop / (release * SR))
    v = 0.0
    for i, f in enumerate(frames):
        g = ga if f > v else gr
        v = g * v + (1 - g) * f
        out[i] = v
    full = np.repeat(out, hop)
    return np.pad(full, (0, len(x) - len(full)), mode="edge")


# ---------------------------------------------------------------------------- main
def main():
    with open(os.path.join(BUILD, "timeline.json")) as f:
        tl = json.load(f)
    with open(os.path.join(BUILD, "cues.json")) as f:
        cues = json.load(f)
    total = secs(tl["duration"])

    print("  narration")
    voice = narration(tl, total)
    ir = reverb_ir(1.1)
    vwet = np.stack([fftconvolve(voice, ir[:, 0])[:total], fftconvolve(voice, ir[:, 1])[:total]], axis=1)
    voice_st = np.stack([voice, voice], axis=1) + vwet * 0.05

    print("  music")
    mus = np.zeros((total + secs(5), 2))
    for c in cues["music"]:
        name, t0, t1 = c["name"], c["t0"], c["t1"]
        if name == "plan":
            part = jingle(t0, t1, decay=(c["decayFrom"], c["decayTo"]))
            n = secs(t1 - t0)
            part = part[:n]
            part[-secs(0.7):] *= np.linspace(1, 0, secs(0.7))[:, None]
            tt = np.arange(len(part)) / SR + t0
            quiet = np.ones(len(part))
            q0, q1 = c["quietFrom"], c["quietTo"]
            quiet -= 0.6 * np.clip((tt - q0) / 0.6, 0, 1) * np.clip((q1 - tt) / 0.8, 0, 1)
            add(mus, part * quiet[:, None], t0, 0.5)
        elif name == "muzak":
            part = muzak(t0, t1)
            part[: secs(0.6)] *= np.linspace(0, 1, secs(0.6))[:, None]
            add(mus, part, t0, 0.9)
        elif name == "sincere":
            add(mus, sincere(t0, t1, c.get("swellAt")), t0, 0.8)
        elif name == "sting":
            add(mus, sting(t0, t1), t0, 0.5)
        elif name == "jingle":
            part = jingle(t0, t1 + 0.5, intro=False, start_bar=1)[: secs(t1 - t0)]
            part[-secs(0.004):] *= np.linspace(1, 0, secs(0.004))[:, None]
            add(mus, part, t0, 0.6)
    mus = mus[:total]
    mir = reverb_ir(1.6, seed=9)
    mwet = np.stack([fftconvolve(mus[:, 0], mir[:, 0])[:total], fftconvolve(mus[:, 1], mir[:, 1])[:total]], axis=1)
    mus = mus + mwet * 0.12

    # duck the music under the voice
    env = follow(voice, 0.04, 0.45)
    duck = 1 - 0.62 * np.clip(env / 0.1, 0, 1)
    mus *= duck[:, None]

    print("  sound effects")
    bank = sfx_bank()
    fx = np.zeros((total + secs(3), 2))
    for c in cues["sfx"]:
        x = bank.get(c["name"])
        if x is None:
            print("    unknown sfx", c["name"])
            continue
        if c["name"] == "coin":
            x = resample_poly(x, 100, int(100 * RNG.uniform(0.92, 1.1)))
        add(fx, x, c["t"], 0.5 * c["gain"], pan=float(RNG.uniform(-0.15, 0.15)))
    fx = fx[:total]

    mix = voice_st + mus * 0.55 + fx * 0.6
    if os.environ.get("PLAN_STEMS"):
        os.makedirs(os.path.join(BUILD, "stems"), exist_ok=True)
        for name, stem in [("voice", voice_st), ("music", mus * 0.55), ("sfx", fx * 0.6)]:
            sf.write(os.path.join(BUILD, "stems", name + ".wav"), stem.astype(np.float32), SR, subtype="FLOAT")
    # nothing after the hard cut
    cut = max((L["start"] + L["cut"]) for L in tl["lines"].values() if L.get("cut") is not None)
    mix[secs(cut):] = 0
    peak = np.max(np.abs(mix))
    print(f"  raw peak {20 * np.log10(peak):.1f} dBFS")
    mix = np.tanh(mix / max(peak, 1e-9) * 1.2) * max(peak, 1e-9) / 1.2 if peak > 0.98 else mix
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, mix.astype(np.float32), SR, subtype="FLOAT")

    # broadcast-style loudness: two-pass loudnorm to -16 LUFS, -1.5 dBTP
    print("  loudness")
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(probe[probe.rindex("{"): probe.rindex("}") + 1])
    flt = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
           "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**js)
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", flt, "-ar", str(SR), "-c:a", "pcm_s16le", out], check=True)
    # MP3 plays in every browser, including Chromium builds without AAC
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-c:a", "libmp3lame", "-b:a", "160k", os.path.join(BUILD, "preview.mp3")], check=True)
    os.remove(raw)
    print(f"wrote build/mix.wav and build/preview.mp3 (input was {js['input_i']} LUFS)")


if __name__ == "__main__":
    sys.exit(main())
