"""Instrument, effect and reverb building blocks (shared with the "Alice" short)."""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

HERE = os.path.dirname(__file__)
BUILD = os.path.join(HERE, 'build')
SR = 48000
RNG = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a=0.01, r=0.1, sustain_tau=None):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4))
    if sustain_tau:
        e *= np.exp(-np.maximum(0, t - a) / sustain_tau)
    rel = int(r * SR)
    if rel and n > rel:
        e[-rel:] *= np.linspace(1, 0, rel) ** 1.5
    return e


def additive(f, dur, partials, vib=0.0, vib_rate=5.0, detune=0.0, phase_rng=True):
    """Sum of partials: list of (ratio, amp, decay_tau or None)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f * (1 + detune)
    if vib:
        inst = freq * (1 + vib * np.sin(2 * np.pi * vib_rate * t + RNG.uniform(0, 6)) *
                       np.minimum(1, t / 0.35))
        ph = 2 * np.pi * np.cumsum(inst) / SR
    else:
        ph = 2 * np.pi * freq * t
    out = np.zeros(n)
    for ratio, amp, tau in partials:
        if f * ratio > 16000:
            continue
        p0 = RNG.uniform(0, 2 * np.pi) if phase_rng else 0
        s = amp * np.sin(ph * ratio + p0)
        if tau:
            s *= np.exp(-t / tau)
        out += s
    return out


# ── instruments ──────────────────────────────────────────────────────────────
def celesta(f, dur, v):
    d = max(dur, 1.6)
    s = additive(f, d, [(1, 1, 1.4), (2, .38, .6), (3, .12, .35), (4.2, .07, .2), (8.0, .03, .06)])
    return v * s * env_adsr(len(s), 0.002, 0.08)


def glock(f, dur, v):
    d = max(dur, 2.2)
    s = additive(f, d, [(1, 1, 2.0), (2.76, .45, .7), (5.4, .22, .3), (8.93, .1, .12)])
    return v * s * env_adsr(len(s), 0.001, 0.1)


def musicbox(f, dur, v):
    d = max(dur, 1.8)
    s = additive(f, d, [(1, 1, 1.1), (3.0, .2, .3), (5.1, .12, .15), (6.7, .05, .08)])
    return v * s * env_adsr(len(s), 0.001, 0.1)


def pizz(f, dur, v):
    d = 0.9
    parts = [(k, 1 / k ** 1.1, 0.42 / (1 + 0.45 * (k - 1))) for k in range(1, 12)]
    s = additive(f, d, parts)
    return v * 0.6 * s * env_adsr(len(s), 0.003, 0.08)


def harp(f, dur, v):
    d = max(dur, 2.0)
    parts = [(k, 1 / k ** 1.6, 1.6 / (1 + 0.6 * (k - 1))) for k in range(1, 9)]
    s = additive(f, d, parts)
    return v * 0.7 * s * env_adsr(len(s), 0.002, 0.1)


def tuba(f, dur, v):
    d = dur + 0.12
    parts = [(1, 1, None), (2, .55, None), (3, .3, None), (4, .16, None), (5, .08, None), (6, .04, None)]
    s = additive(f, d, parts, vib=0.003, vib_rate=4.5)
    return v * 0.5 * s * env_adsr(len(s), 0.04, 0.12, sustain_tau=0.9)


def bassoon(f, dur, v):
    d = dur + 0.08
    def w(k):                       # reedy formant around 450 Hz and 1100 Hz
        fk = f * k
        return (np.exp(-((fk - 450) / 260) ** 2) + 0.5 * np.exp(-((fk - 1150) / 400) ** 2) + 0.08) / k ** 0.3
    parts = [(k, w(k), None) for k in range(1, 16)]
    s = additive(f, d, parts, vib=0.004, vib_rate=5.2)
    return v * 0.45 * s * env_adsr(len(s), 0.025, 0.07)


def strings(f, dur, v, attack=0.35):
    d = dur + 0.6
    out = 0
    for det in (-0.004, 0.0, 0.0045):
        parts = [(k, (1 / k) * np.exp(-k * f / 3500), None) for k in range(1, 24)]
        out = out + additive(f, d, parts, vib=0.005, vib_rate=5.3, detune=det)
    return v * 0.28 * out * env_adsr(int(d * SR), attack, 0.6)


VOWELS = {'oo': [(330, 90, 1.0), (760, 110, .5), (2500, 200, .08)],
          'ah': [(730, 110, 1.0), (1150, 120, .55), (2600, 200, .15)]}


def choir(f, dur, v, vowel='oo', attack=0.5):
    d = dur + 0.8
    out = 0
    for det in (-0.006, -0.002, 0.003, 0.007):
        def amp(k):
            fk = f * k
            return sum(a * np.exp(-((fk - fc) / bw) ** 2) for fc, bw, a in VOWELS[vowel]) + 0.01
        parts = [(k, amp(k), None) for k in range(1, int(4000 / f))]
        out = out + additive(f, d, parts, vib=0.006, vib_rate=4.8, detune=det)
    return v * 0.35 * out * env_adsr(int(d * SR), attack, 0.8)


def theremin(f, dur, v):
    d = dur + 0.2
    s = additive(f, d, [(1, 1, None), (2, .12, None), (3, .05, None)], vib=0.012, vib_rate=6.2)
    return v * 0.5 * s * env_adsr(len(s), 0.12, 0.2)


def timpani(f, dur, v):
    d = 2.5
    s = additive(f, d, [(1, 1, .9), (1.5, .5, .5), (1.99, .3, .4), (2.44, .2, .25)])
    noise = sosfilt(butter(2, 300, 'low', fs=SR, output='sos'), RNG.normal(0, 1, len(s))) * np.exp(-np.arange(len(s)) / SR / 0.06)
    return v * (s + 0.5 * noise) * env_adsr(len(s), 0.004, 0.2)


INSTR = dict(celesta=celesta, glock=glock, musicbox=musicbox, pizz=pizz, harp=harp, tuba=tuba,
             bassoon=bassoon, strings=strings, choir=choir, theremin=theremin, timpani=timpani)
PAN = dict(celesta=0.25, glock=-0.2, musicbox=0.15, pizz=-0.3, harp=0.3, tuba=-0.1, bassoon=0.2,
           strings=0.0, choir=0.0, theremin=0.35, timpani=0.0)
WET = dict(celesta=.45, glock=.5, musicbox=.5, pizz=.25, harp=.45, tuba=.2, bassoon=.25,
           strings=.55, choir=.7, theremin=.55, timpani=.4)


class Bus:
    def __init__(self, length):
        self.dry = np.zeros((2, length))
        self.wet = np.zeros((2, length))

    def note(self, instr, t, midi, dur, v, gain_env=None, **kw):
        if t < 0:
            return
        s = INSTR[instr](mtof(midi), dur, v, **kw)
        i0 = int(t * SR)
        i1 = min(i0 + len(s), self.dry.shape[1])
        if i1 <= i0:
            return
        s = s[:i1 - i0]
        if gain_env is not None:
            s = s * gain_env[i0:i1]
        p = PAN[instr]
        l, r = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
        self.dry[0, i0:i1] += s * l
        self.dry[1, i0:i1] += s * r
        w = WET[instr]
        self.wet[0, i0:i1] += s * l * w
        self.wet[1, i0:i1] += s * r * w


# ── sound effects ────────────────────────────────────────────────────────────
def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def chirp(f0, f1, dur, tau=None, shape=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / dur) ** shape
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    e = np.exp(-t / tau) if tau else np.ones(n)
    e *= np.minimum(1, t / 0.003)
    return s * e


class Sfx:
    def __init__(self, length):
        self.buf = np.zeros((2, length))
        self.wet = np.zeros((2, length))

    def add(self, t, s, v=1.0, pan=0.0, wet=0.2):
        i0 = int(t * SR)
        if i0 < 0 or i0 >= self.buf.shape[1]:
            return
        s = s[:self.buf.shape[1] - i0] * v
        l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        self.buf[0, i0:i0 + len(s)] += s * l
        self.buf[1, i0:i0 + len(s)] += s * r
        self.wet[0, i0:i0 + len(s)] += s * l * wet
        self.wet[1, i0:i0 + len(s)] += s * r * wet

    def pop(self, t, v=0.25, f=500, pan=0.0):
        self.add(t, chirp(f * 0.6, f * 1.8, 0.06, tau=0.025), v, pan)

    def bubble(self, t, v=0.12, f=None, pan=-0.3):
        f = f or RNG.uniform(180, 420)
        self.add(t, chirp(f, f * RNG.uniform(1.8, 2.6), RNG.uniform(0.03, 0.07), tau=0.03), v, pan, 0.3)

    def blorp(self, t, v=0.4, pan=-0.3):
        s = chirp(70, 240, 0.35, tau=0.15, shape=2)
        s[:int(0.3 * SR)] += 0.4 * chirp(140, 480, 0.3, tau=0.1, shape=2)
        self.add(t, lp(s, 1200), v, pan, 0.3)

    def plop(self, t, v=0.45, pan=-0.3):
        s = chirp(700, 160, 0.14, tau=0.07, shape=0.6)
        n = lp(RNG.normal(0, 1, int(0.25 * SR)), 1800) * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.06)
        s = np.concatenate([s, np.zeros(int(0.25 * SR) - len(s))]) + 0.35 * n
        self.add(t, s, v, pan, 0.35)
        for k in range(4):
            self.bubble(t + 0.12 + k * 0.07, 0.12, pan=pan)

    def boink(self, t, v=0.3, f=330, pan=0.0):
        n = int(0.3 * SR)
        tt = np.arange(n) / SR
        fr = f * (1 + 0.5 * np.exp(-tt / 0.05)) * (1 + 0.06 * np.sin(2 * np.pi * 28 * tt))
        s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / 0.09)
        self.add(t, s, v, pan, 0.25)

    def plink(self, t, v=0.18, f=1900, pan=0.0):
        s = additive(f, 0.5, [(1, 1, .12), (2.7, .4, .05), (5.1, .2, .03)])
        self.add(t, s, v, pan, 0.35)

    def slide(self, t, f0, f1, dur, v=0.16, pan=0.0):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        fr = (f0 * (f1 / f0) ** (tt / dur)) * (1 + 0.015 * np.sin(2 * np.pi * 7 * tt))
        s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_adsr(n, 0.03, 0.08)
        s += 0.15 * np.sin(2 * 2 * np.pi * np.cumsum(fr) / SR) * env_adsr(n, 0.03, 0.08)
        self.add(t, s, v, pan, 0.3)

    def gulp(self, t, v=0.35):
        s = np.concatenate([chirp(260, 120, 0.07, tau=0.04), np.zeros(int(0.04 * SR)), chirp(200, 90, 0.08, tau=0.04)])
        self.add(t, lp(s, 900), v, 0.1, 0.15)

    def roll(self, t, dur, v=0.12, pan=-0.2):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        s = lp(RNG.normal(0, 1, n), 380) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt)) * np.linspace(1, 0.2, n)
        self.add(t, s, v, pan, 0.15)

    def whoosh(self, t, dur, v=0.18, lo=300, hi=2400, pan=0.0):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        noise = RNG.normal(0, 1, n)
        out = np.zeros(n)
        seg = int(0.02 * SR)
        for i in range(0, n, seg):
            c = lo + (hi - lo) * np.sin(np.pi * min(1, i / n)) ** 1.5
            out[i:i + seg] = bp(noise[max(0, i - 2000):i + seg], c * 0.7, c * 1.3)[-len(out[i:i + seg]):]
        out *= np.sin(np.pi * tt / dur) ** 2
        self.add(t, out, v, pan, 0.3)

    def sparkle(self, t, n=6, v=0.05, spread=0.6, pan=0.0):
        for _ in range(n):
            m = RNG.choice([86, 90, 93, 98, 102])
            self.add(t + RNG.uniform(0, spread), glock(mtof(m), 1.0, 1.0), v * RNG.uniform(0.5, 1), pan + RNG.uniform(-.3, .3), 0.6)

    def flutter(self, t, dur, v=0.07, pan=0.4):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        s = bp(RNG.normal(0, 1, n), 600, 2600) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 13 * tt))) * np.sin(np.pi * tt / dur)
        self.add(t, s, v, pan, 0.2)
        for k in range(3):
            self.add(t + RNG.uniform(0, dur), chirp(5200, 3800, 0.05, tau=0.03), 0.025, pan, 0.4)

    def hoot(self, t, v=0.07):
        for k, d in ((0, 0.28), (0.42, 0.55)):
            n = int(d * SR)
            s = additive(390 if k == 0 else 360, d, [(1, 1, None), (2, .05, None)], vib=0.01, vib_rate=7)
            self.add(t + k, lp(s * env_adsr(n, 0.06, 0.15), 1000), v, -0.6, 0.6)

    def inhale(self, t, dur, v=0.16):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        noise = RNG.normal(0, 1, n)
        s = bp(noise, 700, 3800) * (tt / dur) ** 1.3 * env_adsr(n, 0.05, 0.25)
        self.add(t, s, v, 0.0, 0.3)

    def tink(self, t, v=0.05):
        self.add(t, additive(2600, 0.4, [(1, 1, .1), (2.1, .3, .05)]), v, 0.1, 0.5)

    def bed_bubbles(self, t0, t1, rate=3.0, v=0.06, pan=-0.35):
        t = t0
        while t < t1:
            t += RNG.exponential(1 / rate)
            self.bubble(t, v * RNG.uniform(0.5, 1.2), pan=pan + RNG.uniform(-.1, .1))

    def bed_fire(self, t0, t1, v=0.05):
        n = int((t1 - t0) * SR)
        if n <= 0:
            return
        s = lp(RNG.normal(0, 1, n), 500) * 0.5
        clicks = np.zeros(n)
        idx = RNG.integers(0, n, size=int((t1 - t0) * 9))
        clicks[idx] = RNG.uniform(-1, 1, len(idx))
        s += bp(clicks, 1500, 6000) * 6
        fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.8 * SR))
        self.add(t0, s * fade, v, -0.35, 0.1)

    def bed_wind(self, t0, t1, v=0.05):
        n = int((t1 - t0) * SR)
        if n <= 0:
            return
        tt = np.arange(n) / SR
        s = bp(RNG.normal(0, 1, n), 180, 900) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * tt + 1) * np.sin(2 * np.pi * 0.07 * tt))
        fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (1.0 * SR))
        self.add(t0, s * fade, v, 0.0, 0.3)


def reverb_ir(seconds=2.6, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for c in range(2):
        noise = r.normal(0, 1, n)
        noise = lp(noise, 6000)
        ir[c] = noise * np.exp(-t * 6.9 / seconds)
        for _ in range(14):                        # a few early reflections
            k = int(r.uniform(0.008, 0.07) * SR)
            ir[c, k] += r.uniform(-0.6, 0.6) * 6
    ir[:, :int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    return ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))


def apply_reverb(wet, ir):
    out = np.zeros_like(wet)
    for c in range(2):
        out[c] = fftconvolve(wet[c], ir[c])[:wet.shape[1]]
    return out


def smooth(x, attack, release, rate):
    """One-pole envelope follower (separate attack/release, in seconds)."""
    out = np.empty_like(x)
    a = np.exp(-1 / (attack * rate))
    r = np.exp(-1 / (release * rate))
    y = 0.0
    for i, v in enumerate(x):
        c = a if v > y else r
        y = c * y + (1 - c) * v
        out[i] = y
    return out
