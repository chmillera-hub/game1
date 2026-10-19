"""Score, sound effects and the final mix — all synthesized, nothing sampled.

The music is an original spooky-sweet waltz in D minor (celesta, pizzicato,
tuba, choir, theremin) that changes mood scene by scene, turns to D major once
Alice can finally taste something, and lands little "stingers" on the words
the story cares about: bright twinkles on hopeful words, deep swells on heavy ones.

Writes build/mix.wav and build/lipsync.npz (mouth movement data per character).
"""
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


# ── harmony and the theme ────────────────────────────────────────────────────
# chord: (bass midi, [chord tones midi in the 3rd/4th octave])
CH = {
    'Dm': (38, [53, 57, 62]), 'D': (38, [54, 57, 62]), 'A7': (33, [55, 57, 61, 64]),
    'A': (33, [57, 61, 64]), 'Gm': (43, [55, 58, 62]), 'G': (43, [55, 59, 62]),
    'F': (41, [53, 57, 60]), 'C': (36, [55, 60, 64]), 'Bb': (34, [53, 58, 62]),
    'F#m': (42, [54, 57, 61]), 'Em': (40, [55, 59, 64]), 'Bm': (35, [54, 59, 62]),
}
THEME = [  # 16 bars of 3/4 — (beat, beats, midi)
    [(0, 1, 69), (1, 1, 74), (2, 1, 76)], [(0, 3, 77)],
    [(0, 1, 76), (1, 1, 74), (2, 1, 73)], [(0, 1, 74), (1, 2, 69)],
    [(0, 1, 70), (1, 1, 74), (2, 1, 79)], [(0, 1, 77), (1, 1, 76), (2, 1, 74)],
    [(0, 1, 73), (1, 1, 76), (2, 1, 81)], [(0, 3, 74)],
    [(0, 1, 77), (1, 1, 81), (2, 1, 77)], [(0, 1, 76), (1, 1, 79), (2, 1, 76)],
    [(0, 1, 74), (1, 1, 77), (2, 1, 74)], [(0, 2, 73), (2, 1, 69)],
    [(0, 1, 70), (1, 1, 73), (2, 1, 76)], [(0, 1, 79), (1, 1, 77), (2, 1, 76)],
    [(0, 1, 74), (1, 1, 73), (2, 1, 76)], [(0, 3, 74)],
]
CHORDS_MINOR = ['Dm', 'Dm', 'A7', 'Dm', 'Gm', 'Dm', 'A7', 'Dm',
                'F', 'C', 'Dm', 'A', 'Gm', 'Gm', 'A7', 'Dm']
CHORDS_MAJOR = ['D', 'D', 'A7', 'D', 'G', 'D', 'A7', 'D',
                'F#m', 'A7', 'D', 'A', 'Em', 'G', 'A7', 'D']


def major(m):
    """Lift the D-minor theme into D major (F->F#, Bb->B)."""
    return m + 1 if m % 12 in (5, 10) else m


def waltz(bus, t0, t1, bpm, lead, mode='minor', lead_v=0.16, accomp=1.0, choir_v=0.0,
          tuba_v=0.0, theremin_bars=(), start_bar=0, ducker=None, glock_v=0.0, lead_oct=0):
    beat = 60.0 / bpm
    bar = 3 * beat
    chords = CHORDS_MINOR if mode == 'minor' else CHORDS_MAJOR
    n = int((t1 - t0) / bar) + 1
    for b in range(n):
        tb = t0 + b * bar
        if tb >= t1:
            break
        idx = (start_bar + b) % 16
        bass, tones = CH[chords[idx]]
        # oom
        bus.note('pizz', tb, bass, beat, 0.22 * accomp)
        if tuba_v:
            bus.note('tuba', tb, bass + 12 if bass < 36 else bass, beat * 0.9, tuba_v * accomp)
        # pah pah
        for k in (1, 2):
            for m in tones[:3]:
                bus.note('pizz', tb + k * beat + RNG.uniform(0, 0.012), m, beat, 0.075 * accomp)
        if choir_v and b % 2 == 0:
            for m in tones[:3]:
                bus.note('choir', tb, m + 12, bar * 2 - 0.2, choir_v)
        for beat_i, dur_b, m in THEME[idx]:
            mm = (m if mode == 'minor' else major(m)) + 12 * lead_oct
            bus.note(lead, tb + beat_i * beat, mm, dur_b * beat * 0.95, lead_v)
            if glock_v:
                bus.note('glock', tb + beat_i * beat, mm + 12, dur_b * beat, glock_v)
            if idx in theremin_bars:
                bus.note('theremin', tb + beat_i * beat, mm - 12, dur_b * beat * 1.02, 0.07)


def arps(bus, t0, t1, bpm, prog, instr='celesta', v=0.1, pad_v=0.05, choir_v=0.0,
         octave=12, pattern=(0, 1, 2, 1, 2, 1), low=True):
    """Slow tender arpeggios: one chord per 3/4 bar, six eighth notes per bar."""
    eighth = 30.0 / bpm
    bar = 6 * eighth
    b = 0
    while t0 + b * bar < t1:
        tb = t0 + b * bar
        bass, tones = CH[prog[b % len(prog)]]
        for i, p in enumerate(pattern):
            bus.note(instr, tb + i * eighth, tones[p % len(tones)] + octave, eighth * 2, v * (1.0 if i == 0 else 0.8))
        if pad_v:
            bus.note('strings', tb, bass + 12, bar, pad_v)
            if low:
                bus.note('strings', tb, bass, bar, pad_v * 0.7)
        if choir_v:
            for m in tones[:3]:
                bus.note('choir', tb, m + 12, bar, choir_v)
        b += 1


def stinger(bus, t, kind, level, key_major):
    third = 66 if key_major else 65
    if kind == 'hi':
        if level == 1:
            bus.note('celesta', t, 81, 0.3, 0.12)
            bus.note('celesta', t + 0.11, 86, 0.6, 0.12)
        elif level == 2:
            for i, m in enumerate([74, third + 12, 81, 86, 90 if key_major else 89]):
                bus.note('glock', t + i * 0.065, m, 0.6, 0.07)
            bus.note('choir', t, 74, 1.4, 0.05, vowel='ah', attack=0.15)
            bus.note('choir', t, 81, 1.4, 0.04, vowel='ah', attack=0.15)
        else:
            for i, m in enumerate([62, 66, 69, 74, 78, 81, 86, 90, 93]):
                bus.note('harp', t - 0.35 + i * 0.045, m if key_major else major(m), 0.8, 0.09)
            for m in (74, 78, 81, 86):
                bus.note('glock', t + 0.06, m, 1.0, 0.05)
            for m in (62, 66, 69, 74):
                bus.note('choir', t, m + 12, 2.0, 0.05, vowel='ah', attack=0.25)
    else:
        bus.note('strings', t - 0.05, 38, 1.8 + 0.8 * level, 0.10 + 0.04 * level, attack=0.25)
        bus.note('strings', t - 0.05, 26, 1.8 + 0.8 * level, 0.07 + 0.03 * level, attack=0.3)
        bus.note('bassoon', t, 38, 1.2 + 0.6 * level, 0.10)
        if level >= 2:
            bus.note('timpani', t, 26, 2.0, 0.22)


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


# ── assemble ─────────────────────────────────────────────────────────────────
def main():
    tl = json.load(open(os.path.join(BUILD, 'timeline.json')))
    T = tl['duration'] + 0.4
    L = int(T * SR)
    acts = {}
    for t, name, dur in tl['acts']:
        acts.setdefault(name, []).append((t, dur))
    scenes = tl['scenes']
    scene_at = {name: t for t, name in scenes}
    beats = {i: (s, e) for s, e, i in tl['beats']}

    def beat_start(i):
        return beats[i][0]

    def act(name, k=0):
        return acts[name][k]

    # ── voice bus + lipsync data ────────────────────────────────────────────
    voice = np.zeros(L)
    rate = 100
    nfr = int(T * rate) + 1
    lips = {c: np.zeros(nfr) for c in 'AS'}
    bright = {c: np.zeros(nfr) for c in 'AS'}
    narr_mask = np.zeros(L)
    for t, spk, idx, dur, gain in tl['speech']:
        a, sr = sf.read(os.path.join(BUILD, 'voice', f'{idx:03d}.wav'), dtype='float64')
        a = a / (np.sqrt(np.mean(a[np.abs(a) > 0.02] ** 2)) + 1e-9) * 0.11 * gain
        i0 = int(t * SR)
        voice[i0:i0 + len(a)] += a[:L - i0]
        if spk == 'N':
            narr_mask[i0:i0 + len(a)] = 1
            continue
        hop = SR // rate
        frames = len(a) // hop
        seg = a[:frames * hop].reshape(frames, hop)
        rms = np.sqrt((seg ** 2).mean(axis=1))
        hi = np.abs(np.diff(seg, axis=1)).mean(axis=1) / (np.abs(seg).mean(axis=1) + 1e-6)
        ref = np.percentile(rms[rms > 0.005], 90) if (rms > 0.005).any() else 1
        o = np.clip(rms / ref, 0, 1.2)
        o = np.where(o < 0.08, 0, o) ** 0.7
        f0 = int(t * rate)
        lips[spk][f0:f0 + frames] = np.maximum(lips[spk][f0:f0 + frames], o[:nfr - f0])
        bright[spk][f0:f0 + frames] = np.clip((hi - 0.15) / 0.35, 0, 1)[:nfr - f0]
    for c in 'AS':
        lips[c] = smooth(lips[c], 0.025, 0.06, rate)
    np.savez(os.path.join(BUILD, 'lipsync.npz'), rate=rate, A=lips['A'], S=lips['S'],
             Ab=bright['A'], Sb=bright['S'])

    # gentle room on the voices; the narrator gets a touch more "storybook" space
    ir = reverb_ir(1.4, seed=11)
    vwet = np.stack([voice * (0.10 + 0.08 * narr_mask)] * 2)
    voice_st = np.stack([voice, voice]) + apply_reverb(vwet, ir)

    # ── score ───────────────────────────────────────────────────────────────
    bus = Bus(L)
    t_kitchen = scene_at['kitchen']
    t_wake = act('simmer_wakes')[0]
    t_hope = beat_start(23)                     # "Nobody remembers the soup..."
    t_fetch = act('fetch_drop')[0]
    t_inhale, d_inhale = act('inhale')
    t_fill = act('heart_fill')[0]
    t_supper = scene_at['supper']
    t_end = scene_at['end']

    sections = []

    def section(t0, t1, fn, fade_in=0.05, fade_out=1.2):
        sections.append((t0, t1, fn, fade_in, fade_out))

    section(0.0, t_kitchen, lambda b: waltz(b, 0.0, t_kitchen, 132, 'celesta', lead_v=0.15,
                                            choir_v=0.022, tuba_v=0.12, theremin_bars=(4, 5, 6, 7)))
    section(t_kitchen, t_wake, lambda b: waltz(b, t_kitchen, t_wake, 146, 'bassoon', lead_v=0.13,
                                               accomp=0.9, start_bar=8, glock_v=0.0, lead_oct=-1))
    section(t_wake, t_hope, lambda b: arps(b, t_wake + 0.8, t_hope, 64, ['Dm', 'Bb', 'Gm', 'A'],
                                           v=0.06, pad_v=0.035, choir_v=0.010), fade_in=1.5, fade_out=2.5)
    section(t_hope, t_fetch, lambda b: arps(b, t_hope, t_fetch, 70, ['F', 'C', 'Dm', 'Bb'],
                                            instr='harp', v=0.07, pad_v=0.04, choir_v=0.012), fade_in=1.5, fade_out=1.5)
    section(t_fetch, t_inhale, lambda b: arps(b, t_fetch, t_inhale, 84, ['D', 'Bm', 'G', 'A'],
                                              instr='harp', v=0.08, pad_v=0.04, choir_v=0.016,
                                              pattern=(0, 1, 2, 3, 2, 1)), fade_in=0.8, fade_out=1.0)
    section(t_inhale, t_fill, lambda b: [b.note('strings', t_inhale + 0.3, m, t_fill - t_inhale, 0.05, attack=1.5)
                                         for m in (74, 78, 81)] + [b.note('choir', t_inhale + 0.6, m, t_fill - t_inhale, 0.025, vowel='ah', attack=1.5)
                                                                    for m in (62, 69)], fade_in=0.5, fade_out=0.8)
    section(t_fill + 0.4, t_supper, lambda b: waltz(b, t_fill + 0.4, t_supper, 138, 'celesta', mode='major',
                                                    lead_v=0.13, glock_v=0.05, choir_v=0.02, tuba_v=0.1),
            fade_in=0.6, fade_out=1.5)
    section(t_supper, t_end, lambda b: waltz(b, t_supper, t_end, 100, 'musicbox', mode='major', lead_v=0.13,
                                             accomp=0.55, choir_v=0.016), fade_in=1.0, fade_out=1.0)

    def finale(b):
        for i, m in enumerate([69, 74, 78, 81]):
            b.note('celesta', t_end + 0.2 + i * 0.25, m, 1.5, 0.12)
        for m in (50, 57, 62, 66, 69, 74):
            b.note('strings', t_end + 1.2, m, 4.0, 0.05, attack=0.8)
            b.note('choir', t_end + 1.2, m + 12, 3.8, 0.02, vowel='ah', attack=0.8)
        b.note('pizz', t_end + 1.2, 38, 1, 0.3)
        b.note('glock', t_end + 1.25, 86, 2.0, 0.08)
        b.note('harp', t_end + 1.2, 62, 2.0, 0.1)
    section(t_end, T, finale, fade_in=0.01, fade_out=0.01)

    music = np.zeros((2, L))
    music_wet = np.zeros((2, L))
    t_ax = np.arange(L) / SR
    for t0, t1, fn, fi, fo in sections:
        sub = Bus(L)
        fn(sub)
        g = np.clip((t_ax - (t0 - fi)) / max(fi, 1e-3), 0, 1) * np.clip(((t1 + fo) - t_ax) / max(fo, 1e-3), 0, 1)
        music += sub.dry * g
        music_wet += sub.wet * g

    # stingers ride on their own bus so they duck less under speech
    st = Bus(L)
    for t, kind, level in tl['stingers']:
        stinger(st, t, kind, level, key_major=t >= t_fill or t_fetch <= t < t_inhale)

    # ── sound effects ───────────────────────────────────────────────────────
    fx = Sfx(L)
    fx.bed_wind(0, t_kitchen + 0.5, 0.05)
    fx.hoot(1.6)
    fx.bed_wind(t_supper - 0.3, T, 0.035)
    fx.bed_fire(t_kitchen - 0.2, t_supper + 0.3, 0.045)
    fx.bed_bubbles(t_kitchen, t_wake, rate=1.2, v=0.03)
    fx.bed_bubbles(t_wake, t_fetch, rate=2.0, v=0.045)
    fx.bed_bubbles(t_fetch + 3.0, t_supper, rate=4.0, v=0.05)
    for t, _ in acts.get('bats', []):
        fx.flutter(t + 0.2, 1.6)
        fx.flutter(t + 1.4, 1.2, pan=0.1)
    for t, _ in acts.get('bubbles_in', []):
        for k in range(5):
            fx.pop(t + 0.08 * k, 0.12, 400 + 120 * k, pan=-0.3 + 0.15 * k)
    for t, _ in acts.get('yum_text', []):
        fx.sparkle(t + 0.05, 4, 0.04, 0.3)
    for t, _ in acts.get('eat_fail_1', []):
        fx.whoosh(t + 0.1, 0.5, 0.08)
        fx.gulp(t + 1.0)
        fx.slide(t + 1.08, 1300, 380, 0.55)
        for k, (dt, f) in enumerate(((1.68, 340), (2.12, 380), (2.45, 420), (2.68, 460))):
            fx.boink(t + dt, 0.28 * 0.75 ** k, f, pan=-0.1 * k)
        fx.roll(t + 2.7, 0.9)
    for t, _ in acts.get('eat_fail_2', []):
        fx.whoosh(t + 0.05, 0.35, 0.08)
        fx.gulp(t + 0.62)
        fx.slide(t + 0.68, 1500, 420, 0.45)
        for k, dt in enumerate((1.15, 1.45, 1.68, 1.86, 2.0)):
            fx.plink(t + dt, 0.2 * 0.8 ** k, 1800 + 120 * k, pan=-0.12 * k)
        fx.roll(t + 2.0, 0.9, 0.1)
    for t, _ in acts.get('simmer_wakes', []):
        fx.blorp(t + 0.3, 0.35)
        fx.blorp(t + 0.95, 0.25)
    for t, _ in acts.get('heart_show', []):
        fx.add(t, celesta(mtof(62), 1.5, 1.0), 0.06, 0, 0.6)
    for t, _ in acts.get('tear', []):
        fx.tink(t + 1.0, 0.04)
    for t, _ in acts.get('fetch_drop', []):
        fx.whoosh(t + 0.2, 0.9, 0.1)
        fx.whoosh(t + 1.6, 1.0, 0.1, 500, 3000)
        fx.plop(t + 3.2)
        fx.plop(t + 3.7, 0.4)
        fx.blorp(t + 3.95, 0.3)
        fx.sparkle(t + 3.9, 8, 0.035, 0.8, pan=-0.3)
    for t, d in acts.get('steam_rise', []):
        fx.whoosh(t, 4.0, 0.07, 600, 2600, pan=-0.2)
        fx.sparkle(t + 0.5, 10, 0.03, 3.5, pan=-0.2)
    for t, _ in acts.get('wisp_face', []):
        fx.sparkle(t, 4, 0.04, 0.3)
    for t, d in acts.get('inhale', []):
        fx.inhale(t + 1.2, 2.0, 0.17)
        fx.sparkle(t + 3.0, 6, 0.03, 1.0)
    for t, _ in acts.get('heart_fill', []):
        for m in (62, 66, 69, 74):
            fx.add(t, glock(mtof(m + 12), 2.0, 1.0), 0.04, 0, 0.6)
    for t, d in acts.get('spin', []):
        fx.whoosh(t, 0.6, 0.1, 500, 2600)
    for t, _ in acts.get('hearts_burst', []):
        for k in range(8):
            fx.pop(t + 0.04 * k, 0.08, 600 + 70 * k, pan=RNG.uniform(-.5, .5))
        fx.sparkle(t + 0.1, 8, 0.03, 1.2)
    for t, _ in acts.get('hearts_float', []):
        fx.sparkle(t + 0.2, 5, 0.03, 1.5)

    # ── mix ─────────────────────────────────────────────────────────────────
    ir_music = reverb_ir(2.6)
    music = music + apply_reverb(music_wet, ir_music) * 0.9
    stb = st.dry + apply_reverb(st.wet, ir_music) * 0.9
    sfx = fx.buf + apply_reverb(fx.wet, reverb_ir(1.2, seed=5)) * 0.8

    # duck music under dialogue (the narrator lets the music breathe a bit more)
    hop = 480
    v_env = np.sqrt(np.convolve(voice[:L // hop * hop].reshape(-1, hop).__pow__(2).mean(axis=1), np.ones(5) / 5, 'same'))
    speaking = (v_env > 0.01).astype(float)
    narr = narr_mask[:L // hop * hop].reshape(-1, hop).max(axis=1)
    duck_db = smooth(speaking * np.where(narr > 0, 7.0, 10.0), 0.08, 0.6, SR / hop)
    duck = 10 ** (-np.interp(np.arange(L) / hop, np.arange(len(duck_db)), duck_db) / 20)
    duck_st = 10 ** (-np.interp(np.arange(L) / hop, np.arange(len(duck_db)), duck_db * 0.35) / 20)

    mus = music * duck * 0.62
    mix = voice_st * 1.0 + mus + stb * duck_st * 0.75 + sfx * 0.9
    sp_mask = np.repeat(speaking, hop)[:L] > 0
    def db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    print(f'balance: voice {db(voice[:len(sp_mask)][sp_mask]):.1f} dB | music under speech '
          f'{db(mus[0][:len(sp_mask)][sp_mask]):.1f} dB | music in gaps {db(mus[0][:len(sp_mask)][~sp_mask]):.1f} dB | '
          f'sfx {db(sfx[0]):.1f} dB')
    # master: gentle high-pass, then a soft limiter
    mix = np.stack([sosfilt(butter(2, 35, 'high', fs=SR, output='sos'), ch) for ch in mix])
    # only tame the rare spikes here; loudness is normalized in encode.py
    peak = np.percentile(np.abs(mix), 99.99)
    mix = np.tanh(mix / peak * 0.8) * 0.8
    mix[:, -int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
    sf.write(os.path.join(BUILD, 'mix.wav'), mix.T.astype(np.float32), SR, subtype='FLOAT')
    print(f'mix {T:.1f}s  peak {np.abs(mix).max():.3f}')


if __name__ == '__main__':
    main()
