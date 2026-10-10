"""Score, sound design and final mix -> build/mix.wav (48 kHz stereo).

Everything is synthesised here (no samples): drones, pads, a ney-like flute in the
Hijaz mode, Karplus-Strong oud plucks, frame drum, wordless choir, bells, wind,
footsteps, the gate, the shared sigh. Cues are keyed to build/timeline.json.
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy import signal

import dsp

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SR = 48000
TL = json.load(open(os.path.join(BUILD, "timeline.json")))
MARKS = TL["marks"]
ITEMS = {it["id"]: it for it in TL["items"]}
TOTAL = MARKS["total"]
N = int((TOTAL + 0.5) * SR)
rng = np.random.default_rng(7)


def S(i):
    return ITEMS[i]["start"] if i in ITEMS else MARKS[i]


def E(i):
    return ITEMS[i]["end"]


def CAP(i, k):
    c = ITEMS[i]["caps"]
    return c[max(-len(c), min(k, len(c) - 1))][0]


NOTES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
         "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(n):
    if isinstance(n, (int, float)):
        return float(n)
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((NOTES[name] + 12 * (octv + 1) - 69) / 12)


# ------------------------------------------------------------------ buses
class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, t, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
            sig = np.stack([sig * l, sig * r], 1) * 1.414
        i = int(t * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        n = min(len(sig), N - i)
        if n > 0:
            self.x[i:i + n] += sig[:n] * gain


music, sfx, amb, voice = Bus(), Bus(), Bus(), Bus()


# ------------------------------------------------------------------ oscillators & envelopes
def _table(nh):
    ph = np.arange(4096) / 4096 * 2 * np.pi
    w = sum(np.sin(k * ph) / k for k in range(1, nh + 1))
    return w / np.abs(w).max()


TABLES = {}


def osc(f, n, vib=0.0, rate=5.0, ph0=0.0, nh=None):
    t = np.arange(n) / SR
    nh = nh or max(1, min(24, int(9000 / max(f, 1))))
    if nh not in TABLES:
        TABLES[nh] = _table(nh)
    fi = f * (1 + vib * np.sin(2 * np.pi * rate * t + ph0 * 7))
    ph = ph0 + np.cumsum(fi) / SR
    return TABLES[nh][((ph % 1.0) * 4096).astype(np.int64)]


def env(n, a=0.01, r=0.1, shape=1.0):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na) ** shape
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** shape
    return e


def sine(f, n, ph=0.0):
    return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)


def noise(n):
    return rng.uniform(-1, 1, n)


# ------------------------------------------------------------------ instruments
def pad(notes, dur, bright=0.4, attack=2.0, release=2.5, detune=0.005):
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for k, nt in enumerate(notes):
        f = hz(nt)
        for v, pan in ((-1, -0.7), (0, 0.0), (1, 0.7)):
            s = osc(f * (1 + v * detune), n, vib=0.002, rate=0.3 + 0.1 * v, ph0=rng.uniform())
            l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
            out[:, 0] += s * l
            out[:, 1] += s * r
    out = dsp.lowpass(out, SR, 500 + 3200 * bright)
    out *= env(n, attack, release, 1.5)[:, None]
    return out / (len(notes) * 2.2)


def choir(notes, dur, attack=2.0, release=3.0, vowel="ah"):
    n = int(dur * SR)
    src = np.zeros((n, 2))
    for nt in notes:
        f = hz(nt)
        for v in range(4):
            s = osc(f * (1 + rng.uniform(-0.006, 0.006)), n, vib=0.006, rate=4.6 + 0.6 * v, ph0=rng.uniform())
            pan = -0.8 + 0.53 * v
            src[:, 0] += s * np.sqrt(0.5 * (1 - pan))
            src[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    F = {"ah": [(800, 1.0), (1150, 0.55), (2900, 0.22)], "oo": [(350, 1.0), (800, 0.4), (2400, 0.1)]}[vowel]
    out = sum(g * dsp.bandpass(src, SR, f * 0.88, f * 1.12) for f, g in F)
    out *= env(n, attack, release, 1.5)[:, None]
    return out / (len(notes) * 1.2)


def ney(phrase, t0, gain=0.25, bus=None, pan=0.1):
    """phrase: [(note or 'R', dur)], monophonic breathy flute with glides and late vibrato."""
    dur = sum(d for _, d in phrase) + 0.6
    n = int(dur * SR)
    f = np.zeros(n)
    a = np.zeros(n)
    t = 0.0
    prev = None
    for nt, d in phrase:
        i0, i1 = int(t * SR), int((t + d) * SR)
        m = i1 - i0
        if nt == "R":
            f[i0:i1] = prev or 300
        else:
            fr = hz(nt)
            fg = np.full(m, fr)
            if prev:
                g = min(m, int(0.07 * SR))
                fg[:g] = np.linspace(prev, fr, g)
            tt = np.arange(m) / SR
            vib = 1 + 0.007 * np.sin(2 * np.pi * 5.3 * tt) * np.clip((tt - 0.3) / 0.4, 0, 1)
            f[i0:i1] = fg * vib
            e = np.minimum(1, tt / 0.09) * (0.85 + 0.15 * np.exp(-tt / 0.3))
            rel = np.clip((d - tt) / 0.12, 0, 1)
            a[i0:i1] = e * rel
            prev = fr
        t += d
    ph = np.cumsum(f) / SR * 2 * np.pi
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
    breath = dsp.bandpass(noise(n), SR, 1200, 5000) * 0.35
    s = (tone + breath) * a
    s = dsp.lowpass(s, SR, 5000)
    (bus or music).add(s, t0, gain, pan)


def ks(f, dur=2.8, bright=0.6, decay=0.997):
    n = int(dur * SR)
    P = max(2, int(SR / f))
    y = np.zeros(n + P)
    b = noise(P)
    b = bright * b + (1 - bright) * np.convolve(b, np.ones(6) / 6, mode="same")
    y[:P] = b
    i = P
    while i < n + P:
        k = min(P, n + P - i)
        a = y[i - P:i - P + k]
        b = np.empty(k)
        b[0] = y[i - P - 1] if i - P - 1 >= 0 else 0.0
        b[1:] = a[:-1]
        y[i:i + k] = decay * 0.5 * (a + b)
        i += k
    out = dsp.bandpass(y[P:], SR, 110, 4500)
    return out * env(n, 0.002, 0.3)


def oud(nt, t0, gain=0.22, pan=0.0, dur=2.6):
    music.add(ks(hz(nt), dur), t0, gain, pan)


def bell(nt, t0, gain=0.12, pan=0.0, dur=4.0, bus=None):
    f = hz(nt)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt / d)
            for r, a, d in ((1, 1, 1.6), (2.0, 0.45, 1.0), (2.76, 0.35, 0.7), (5.4, 0.2, 0.35), (8.9, 0.08, 0.2)))
    (bus or music).add(s * env(n, 0.002, 0.2), t0, gain, pan)


def doum(t0, gain=0.5):
    n = int(0.7 * SR)
    tt = np.arange(n) / SR
    f = 52 + 75 * np.exp(-tt / 0.045)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.28)
    s += 0.25 * dsp.lowpass(noise(n), SR, 1800) * np.exp(-tt / 0.012)
    music.add(s, t0, gain)


def tek(t0, gain=0.18, pan=0.2):
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    s = dsp.bandpass(noise(n), SR, 1500, 7000) * np.exp(-tt / 0.025) + 0.4 * np.sin(2 * np.pi * 820 * tt) * np.exp(-tt / 0.04)
    music.add(s, t0, gain, pan)


def boom(t0, gain=0.6, bus=None):
    n = int(3.0 * SR)
    tt = np.arange(n) / SR
    f = 32 + 40 * np.exp(-tt / 0.15)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 1.0)
    s += 0.5 * dsp.lowpass(noise(n), SR, 220) * np.exp(-tt / 0.35)
    (bus or sfx).add(s, t0, gain)


def whoosh(t0, dur, gain=0.2, f0=300, f1=2400, pan=0.0, bus=None):
    n = int(dur * SR)
    X, ln = dsp.stft(noise(n), 1024, 256)
    fr = np.fft.rfftfreq(1024, 1 / SR)
    k = X.shape[0]
    cf = np.geomspace(f0, f1, k)
    mask = np.exp(-0.5 * ((np.log(fr[None, :] + 1) - np.log(cf[:, None])) / 0.35) ** 2)
    s = dsp.istft(X * mask, ln, 1024, 256)
    s *= np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    (bus or sfx).add(s / (np.abs(s).max() + 1e-9), t0, gain, pan)


def wind(t0, t1, gain=0.12, gust=0.5, seed=1, bright=900):
    n = int((t1 - t0) * SR)
    r = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    tt = np.arange(n) / SR
    for c in range(2):
        w = r.uniform(-1, 1, n)
        w = 0.6 * dsp.lowpass(w, SR, bright) + 0.25 * dsp.bandpass(w, SR, 1200, 3000)
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt + c) * np.sin(2 * np.pi * 0.19 * tt + 2 * c)
        g = 1 + gust * np.clip(np.sin(2 * np.pi * 0.05 * tt + seed), 0, 1) ** 3
        out[:, c] = w * lfo * g
    out *= env(n, 1.5, 1.5)[:, None]
    amb.add(out / np.abs(out).max(), t0, gain)


def step(t0, gain=0.12, pan=0.0, soft=False):
    n = int(0.22 * SR)
    tt = np.arange(n) / SR
    grit = noise(n) * (rng.uniform(size=n) > (0.6 if soft else 0.85))
    s = dsp.bandpass(noise(n) * 0.4 + grit, SR, 700, 5000) * np.exp(-tt / 0.06)
    s += 0.6 * np.sin(2 * np.pi * 75 * tt) * np.exp(-tt / 0.05)
    sfx.add(s * env(n, 0.004, 0.05), t0, gain, pan)


def thud(t0, gain=0.7):
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    f = 40 + 50 * np.exp(-tt / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.22)
    s += 0.5 * dsp.lowpass(noise(n), SR, 400) * np.exp(-tt / 0.12)
    s += 0.35 * dsp.bandpass(noise(n), SR, 1200, 6000) * np.exp(-tt / 0.35)  # dust and grit
    sfx.add(s, t0, gain)


def clank(t0, gain=0.15, pan=0.0):
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * 430 * r * tt) * np.exp(-tt / d)
            for r, a, d in ((1, 1, 0.3), (2.32, 0.7, 0.2), (4.25, 0.5, 0.12), (6.63, 0.3, 0.08)))
    s += 0.5 * dsp.highpass(noise(n), SR, 3000) * np.exp(-tt / 0.01)
    sfx.add(s, t0, gain, pan)


def creak(t0, dur, gain=0.12, seed=3):
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    walk = np.cumsum(r.normal(0, 1, n // 480 + 2))
    walk = (walk - walk.min()) / (np.ptp(walk) + 1e-9)
    f = 70 + 120 * np.interp(np.arange(n), np.arange(len(walk)) * 480, walk)
    ph = np.cumsum(f) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    s = dsp.bandpass(signal.lfilter([1], [1, -0.97], pulses), SR, 250, 2600)
    s *= env(n, 0.1, 0.2) * (0.6 + 0.4 * np.sin(np.linspace(0, 9, n)) ** 2)
    sfx.add(s / (np.abs(s).max() + 1e-9), t0, gain)


def stone_crack(t0, gain=0.25):
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(9):
        i = int(rng.uniform(0, 0.35) * SR)
        m = int(0.03 * SR)
        s[i:i + m] += noise(m) * np.exp(-np.arange(m) / (0.004 * SR))
    s = dsp.bandpass(s, SR, 800, 8000) + 0.4 * dsp.lowpass(noise(n), SR, 150) * np.exp(-tt / 0.3)
    sfx.add(s, t0, gain)


def heartbeat(t0, t1, bpm0=70, bpm1=105, gain=0.35):
    t = t0
    while t < t1:
        u = (t - t0) / (t1 - t0)
        bpm = bpm0 + (bpm1 - bpm0) * u
        for dt, a in ((0.0, 1.0), (0.24, 0.7)):
            n = int(0.35 * SR)
            tt = np.arange(n) / SR
            s = np.sin(2 * np.pi * (48 + 20 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.09)
            sfx.add(s, t + dt, gain * a)
        t += 60 / bpm


def crackle(t0, dur, gain=0.12):
    n = int(dur * SR)
    s = np.zeros(n)
    for k in range(int(dur * 40)):
        i = int(rng.uniform(0, dur - 0.02) * SR)
        m = int(0.004 * SR)
        s[i:i + m] += noise(m) * rng.uniform(0.2, 1.0)
    s = dsp.bandpass(s, SR, 1500, 9000) + 0.6 * dsp.lowpass(noise(n), SR, 160)
    sfx.add(s * env(n, 0.3, 0.8), t0, gain)


def gasp(t0, gain=0.08, pan=0.0, scale=1.0):
    n = int(0.32 * SR)
    tt = np.arange(n) / SR
    src = noise(n)
    s = dsp.bandpass(src, SR, 550 * scale, 900 * scale) + 0.6 * dsp.bandpass(src, SR, 1500 * scale, 2300 * scale)
    e = np.clip(tt / 0.22, 0, 1) ** 1.5 * np.clip((0.32 - tt) / 0.05, 0, 1)
    sfx.add(s * e, t0, gain, pan)


def breath_sigh(t0, scale=1.0, gain=0.25, pan=0.0, voiced=0.2, bus=None):
    """Inhale through the nose, then a long, weary 'haaah'."""
    n = int(3.4 * SR)
    tt = np.arange(n) / SR
    src = noise(n)
    inh = dsp.bandpass(src, SR, 900 * scale, 3200 * scale) * np.clip(np.sin(np.pi * np.clip(tt / 1.05, 0, 1)), 0, 1) * 0.35
    ex_env = np.where(tt > 1.1, np.clip((tt - 1.1) / 0.12, 0, 1) * np.exp(-np.clip(tt - 1.25, 0, None) / 0.75), 0)
    form = (dsp.bandpass(src, SR, 620 * scale, 860 * scale) + 0.6 * dsp.bandpass(src, SR, 1000 * scale, 1300 * scale)
            + 0.25 * dsp.bandpass(src, SR, 2400 * scale, 2900 * scale))
    glott = osc(105 * scale, n, nh=12)
    vo = (dsp.bandpass(glott, SR, 600 * scale, 900 * scale) + 0.5 * dsp.bandpass(glott, SR, 1000 * scale, 1300 * scale))
    vo *= np.where(tt > 1.1, np.exp(-np.clip(tt - 1.1, 0, None) / 0.35), 0)
    s = inh + form * ex_env * 1.4 + voiced * vo * 0.6
    (bus or sfx).add(s, t0, gain, pan)


def crickets(t0, t1, gain=0.02):
    for c, (rate, pan, f) in enumerate(((0.9, -0.6, 4300), (1.3, 0.5, 4700), (1.1, 0.1, 3900))):
        t = t0 + c * 0.37
        while t < t1:
            n = int(0.2 * SR)
            tt = np.arange(n) / SR
            s = np.sin(2 * np.pi * f * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 32 * tt)) * env(n, 0.01, 0.05)
            amb.add(s, t, gain, pan)
            t += rate * rng.uniform(0.8, 1.2)


def knock(t0, gain=0.1, pan=0.0):
    n = int(0.15 * SR)
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d) for f, a, d in ((420, 1, 0.04), (1150, 0.5, 0.02),
                                                                           (2300, 0.3, 0.01)))
    sfx.add(s, t0, gain, pan)


def babble(t0, t1, gain=0.05):
    path = os.path.join(BUILD, "babble.wav")
    if not os.path.exists(path):
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(HERE, "models/kokoro-v1.0.onnx"), os.path.join(HERE, "models/voices-v1.0.bin"))
        lines = ["Did you bring the bread from the oven?", "The well is low again this year.",
                 "Hush now, the Elder is speaking.", "My cousin says the caravan is late.",
                 "Yes, yes, I heard him the first time.", "The lamb is fat, it will fetch a good price.",
                 "Mind the children near the gate.", "We should go before the heat comes.",
                 "Is that the new cloth? It is very fine.", "Quiet, quiet, listen to him."]
        voices = ["am_eric", "af_sarah", "bm_lewis", "af_nicole", "am_liam", "bf_isabella", "am_adam", "af_sky",
                  "bm_daniel", "af_river"]
        mix = np.zeros(int(14 * 24000))
        for i, (ln, v) in enumerate(zip(lines, voices)):
            a, sr = k.create(ln, voice=v, speed=1.1)
            st = int(rng.uniform(0, 10) * sr)
            m = min(len(a), len(mix) - st)
            mix[st:st + m] += a[:m]
        mix = dsp.lowpass(dsp.resample(mix, 24000, SR), SR, 2200)
        sf.write(path, mix.astype(np.float32), SR)
    b, _ = sf.read(path)
    b = b / (np.abs(b).max() + 1e-9)
    t = t0
    while t < t1:
        seg = b[:int(min(len(b) / SR, t1 - t) * SR)]
        amb.add(seg * env(len(seg), 0.8, 0.8), t, gain, rng.uniform(-0.3, 0.3))
        t += len(b) / SR - 1.0


# ------------------------------------------------------------------ the score
def score():
    v, fear, sp, el2, ex, al, pr, v2, end = (MARKS[k] for k in ("village", "fear", "speech", "elder2", "expel",
                                                               "alone", "presence", "village2", "end"))
    tot = TOTAL
    # 1. OPENING: dawn drone, a lone ney in Hijaz, the memory of the bush
    music.add(pad(["D2", "A2"], v + 1.5, bright=0.2, attack=3.5, release=2.5), 0, 0.55)
    music.add(pad(["D3", "A3", "E4", "F4"], v - 1, bright=0.35, attack=4, release=3), 1.0, 0.32)
    ney([("A4", 1.2), ("G4", 0.5), ("F#4", 0.6), ("Eb4", 1.1), ("D4", 2.4)], 3.9, 0.15)
    g0 = S("g0")
    music.add(choir(["D4", "F#4", "A4"], 3.4, attack=0.9, release=1.6), g0 - 0.4, 0.3)
    bell("D6", g0 - 0.2, 0.06, -0.3)
    bell("A5", g0 + 0.25, 0.05, 0.3)
    crackle(g0 - 0.3, 3.2, 0.04)
    ney([("D4", 0.6), ("Eb4", 0.5), ("F#4", 0.5), ("G4", 0.5), ("A4", 1.6), ("Bb4", 0.5), ("A4", 2.2)],
        S("n2") + 3.1, 0.13)
    wind(0, v + 0.5, 0.075, seed=2)
    for t in np.arange(2.4, CAP("n1", 1), 1 / 1.7):
        step(t, 0.035 * min(1, (t - 2.4) / 3), 0.1, soft=True)
    for t in np.arange(CAP("n1", 1), S("g0") - 0.6, 1 / 1.6):
        step(t, 0.08, 0.0, soft=True)
    T = 1.15
    t0f = CAP("n2", 1)
    for t in np.arange(t0f - (t0f % (T / 2)), E("n2") + 0.25, T / 2):
        if t >= t0f:
            step(t, 0.16, 0.0)
    # 2. VILLAGE: the rigid pulse of order
    music.add(pad(["G2", "D3", "Bb3"], fear - v + 1.0, bright=0.2, attack=2.0, release=1.2), v, 0.36)
    music.add(pad(["D2"], fear - v + 1.0, bright=0.1, attack=2.0, release=1.2), v, 0.4)
    beat = 60 / 84
    t = S("n3b")
    k = 0
    while t < fear - 0.3:
        if k % 4 in (0, 2):
            doum(t, 0.22)
        else:
            tek(t, 0.07)
        if k % 2 == 0:
            oud(["D3", "D3", "Eb3", "D3", "C3", "D3", "Eb3", "D3"][(k // 2) % 8], t, 0.07, -0.2, 1.4)
        t += beat
        k += 1
    babble(S("n3b"), S("e1a") + 0.5, 0.06)
    babble(E("e1c") - 0.2, fear + 1.0, 0.035)
    wind(v, fear, 0.03, seed=3, bright=600)
    # 3. FEAR: cluster, heartbeat, the ghost; then the fire breaks through
    n5 = S("n5")
    music.add(pad(["D2", "Eb2", "A2"], n5 - fear + 1.2, bright=0.15, attack=2.5, release=0.8), fear - 0.3, 0.34)
    sh = np.zeros(int((n5 - S("f1") + 1.0) * SR))
    tt = np.arange(len(sh)) / SR
    for f in (2350, 2390, 2810, 2860):
        sh += np.sin(2 * np.pi * f * tt)
    music.add(sh * env(len(sh), 1.0, 0.6) * 0.018, S("f1") - 0.5, 1.0)
    heartbeat(S("n4") + 1.0, n5 + 0.2, 64, 104, 0.24)
    whoosh(S("f1") - 0.4, 2.2, 0.06, 2000, 300, -0.6)
    whoosh(n5 - 0.6, 2.0, 0.15, 200, 3000)
    crackle(n5 + 0.1, 4.0, 0.08)
    music.add(choir(["D3", "F#3", "A3", "D4"], 6.5, attack=1.0, release=3.0), n5 + 0.1, 0.42)
    music.add(pad(["D2", "A2", "F#3", "D4"], 7.0, bright=0.45, attack=0.8, release=3), n5 + 0.1, 0.45)
    bell("D5", n5 + 0.3, 0.07)
    music.add(pad(["D3", "A3", "E4"], sp - S("n5b") + 1.5, bright=0.3, attack=2.5, release=2), S("n5b"), 0.3)
    for t in np.arange(S("n5b") - 0.3, S("n5b") + 3.0, 1 / 1.7):
        step(t, 0.07, -0.4, soft=True)
    babble(S("n5b"), S("n5b") + 2.0, 0.03)
    # 4. SPEECH: gentle oud, the vessel, light through the cracks
    music.add(pad(["D3", "A3", "E4"], S("m4") - sp + 2, bright=0.3, attack=3, release=2.5), sp, 0.3)
    arp = ["D4", "A4", "F#4", "E4", "A3", "D4"]
    t, k = sp + 1.0, 0
    while t < S("m4"):
        oud(arp[k % len(arp)], t, 0.1, 0.25 * ((k % 3) - 1))
        t += 2.4
        k += 1
    music.add(pad(["B2", "F#3", "D4"], S("m5") - S("m4") + 2, bright=0.25, attack=2, release=2), S("m4"), 0.32)
    light = S("m5") + 1.0
    whoosh(light - 0.6, 2.6, 0.08, 400, 4000)
    for k, nt in enumerate(["A5", "D6", "F#6", "A6", "E6"]):
        bell(nt, light + k * 0.22, 0.045, -0.5 + 0.25 * k)
    music.add(choir(["G3", "B3", "D4"], 3.2, attack=1.0, release=1.6), light - 0.3, 0.3)
    music.add(choir(["D3", "F#3", "A3", "D4"], el2 - light - 2.4, attack=1.5, release=2.5), light + 2.4, 0.26)
    music.add(pad(["D2", "A2", "F#3", "E4"], el2 - S("m6") + 1.0, bright=0.4, attack=2.5, release=2.0), S("m6"),
              0.34)
    ney([("A4", 0.9), ("F#4", 0.6), ("E4", 0.6), ("D4", 2.5)], E("m7") - 0.6, 0.11)
    # 5. THE ELDER SNAPS: the warmth drains, tension
    music.add(pad(["D2", "Ab2"], ex - el2 + 0.5, bright=0.15, attack=3, release=0.5), el2, 0.45)
    stone_crack(CAP("n6", -1) + 0.05, 0.3)
    boom(S("e2a") - 0.4, 0.3)
    trem = np.zeros(int((ex - S("e2a")) * SR))
    trem_t = np.arange(len(trem)) / SR
    for nt in ("D3", "Eb3"):
        trem += osc(hz(nt), len(trem)) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * trem_t))
    music.add(dsp.lowpass(trem, SR, 1500) * env(len(trem), 0.5, 0.6) * 0.05, S("e2a"), 1.0)
    for t in np.arange(S("e2c") + 1.2, ex + 0.5, 0.55):
        step(t, 0.05, 0.5)
    # 6. EXPULSION: march, gasps, gate, the fall
    clank(S("n7") + 0.1, 0.12, -0.5)
    clank(S("n7") + 0.25, 0.1, 0.5)
    for k, t in enumerate(np.arange(CAP("n7", 1) - 0.2, CAP("n7", 2), 0.85)):
        doum(t, 0.18 + 0.05 * k)
    for k in range(6):
        gasp(CAP("n7", 1) + 0.15 + k * 0.23, 0.06, -0.7 + 0.28 * k, 0.9 + 0.15 * (k % 3))
    c2 = CAP("n7", 2)
    creak(c2 - 0.2, 1.1, 0.1, 4)
    whoosh(c2 + 0.9, 0.8, 0.12, 300, 1500)
    land = E("n7") - 0.1
    thud(land, 0.6)
    boom(land, 0.25)
    th = S("throw")
    creak(th + 0.5, 1.0, 0.09, 5)
    boom(th + 1.45, 0.55)
    knock(th + 1.48, 0.35)
    knock(th + 1.6, 0.12)
    # 7. ALONE: wind, a lone low string, a few falling notes; then nothing
    wind(al - 1.0, pr + 3.0, 0.11, gust=0.6, seed=5)
    music.add(pad(["D2"], S("n9") - al, bright=0.18, attack=4, release=3), al + 1.5, 0.35)
    for k, (nt, t) in enumerate((("A3", S("n8b") + 0.5), ("F3", S("n8b") + 3.0), ("D3", S("mp1") - 0.4),
                                 ("C3", S("mp3") - 0.5), ("A2", S("mp4") + 1.0))):
        oud(nt, t, 0.08, -0.3 + 0.15 * k, 3.5)
    whoosh(S("n9") + 0.5, 3.5, 0.18, 200, 1200, -0.3)
    # 8. THE PRESENCE
    music.add(pad(["D5", "A5", "E6"], S("g1") - S("n10") + 2, bright=0.6, attack=4, release=2.5,
                  detune=0.003), S("n10") + 0.4, 0.07)
    warmth = CAP("n10b", 3)
    music.add(pad(["D2", "A2", "F#3"], pr + 46 - CAP("n10b", 2), bright=0.3, attack=4, release=4),
              CAP("n10b", 2), 0.4)
    music.add(choir(["D3", "A3", "F#4"], S("g1") - warmth + 1, attack=3, release=2), warmth, 0.22)
    t = S("n10c")
    pent = ["D6", "E6", "F#6", "A6", "B6", "D7", "A5", "F#5"]
    while t < S("g1") - 0.3:
        bell(pent[int(rng.integers(len(pent)))], t, 0.02, rng.uniform(-0.8, 0.8), 2.5)
        t += rng.uniform(0.25, 0.7)
    g2 = S("g2")
    swell = E("g2") + 0.1
    music.add(choir(["D3", "A3", "D4", "F#4", "E5"], v2 - swell + 1.5, attack=2.5, release=4), swell, 0.36)
    music.add(pad(["D2", "A2", "D3", "F#3", "A3", "E4"], v2 - swell + 1.5, bright=0.45, attack=2.5,
                  release=4), swell, 0.36)
    bell("D6", swell, 0.05, -0.3)
    bell("A5", swell + 0.4, 0.04, 0.4)
    bell("F#6", swell + 0.9, 0.03, 0.0)
    sg = S("sigh")
    breath_sigh(sg, 1.0, 0.22, -0.25, voiced=0.25)
    cosmic = np.zeros((int(5 * SR), 2))
    tmp = Bus.__new__(Bus)
    tmp.x = cosmic
    breath_sigh(0, 0.62, 0.3, 0.3, voiced=0.15, bus=tmp)
    cosmic = dsp.reverb(cosmic, dsp.make_ir(SR, 3.5, 0.6, 0.04, 9), wet=0.8, dry=0.5)
    sfx.add(cosmic[:int(6 * SR)], sg + 0.05, 0.9)
    boom(sg + 1.15, 0.12)
    # 9. BACK IN THE VILLAGE
    crickets(v2 - 0.5, end + 3, 0.012)
    for t in np.arange(v2 + 0.2, v2 + 2.3, 0.62):
        knock(t, 0.09, -0.3)
    wh = np.zeros(int(6 * SR))
    tw = np.arange(len(wh)) / SR
    wh = (np.sin(2 * np.pi * 88 * tw) * 0.5 + dsp.bandpass(noise(len(wh)), SR, 300, 900)) * np.exp(-tw / 2.0)
    amb.add(wh * env(len(wh), 0.5, 1), CAP("n13", 3) - 0.5, 0.04, 0.4)
    music.add(pad(["D3", "F3", "A3"], S("p1") - v2 + 1, bright=0.25, attack=2.5, release=1.5), v2, 0.26)
    for k, nt in enumerate(["F4", "E4", "D4", "A3"]):
        oud(nt, v2 + 1.0 + k * 1.9, 0.08, 0.2)
    music.add(pad(["D2", "A2"], S("p3") - S("p1") + 0.5, bright=0.15, attack=1.5, release=0.8), S("p1"), 0.25)
    cage = CAP("n14", 2)
    music.add(pad(["D2", "A2"], cage - S("n14") + 0.5, bright=0.15, attack=2, release=0.5), S("n14"), 0.3)
    music.add(pad(["Bb1", "F2", "D3"], S("n14b") - cage + 0.5, bright=0.2, attack=0.3, release=1.2), cage, 0.42)
    boom(cage + 0.05, 0.2)
    clank(cage + 0.1, 0.05)
    bell("A5", S("n14b") - 0.4, 0.07, 0.3, 5)
    bell("D6", S("n14b") + 1.4, 0.05, 0.0, 5)
    mir = S("n14c") - 0.3
    whoosh(mir, 3.0, 0.07, 300, 5000)
    music.add(choir(["D3", "A3", "D4", "F#4", "A4"], tot - mir + 0.4, attack=2.0, release=3.5), mir, 0.36)
    music.add(pad(["D2", "A2", "D3", "F#3", "E4"], tot - mir + 0.4, bright=0.45, attack=2.0, release=3.5), mir,
              0.38)
    ney([("D4", 0.5), ("Eb4", 0.4), ("F#4", 0.5), ("G4", 0.5), ("A4", 1.2), ("F#4", 0.5), ("A4", 0.5),
         ("D5", 2.6)], mir + 0.8, 0.12)
    for k, nt in enumerate(["D5", "F#5", "A5", "D6"]):
        bell(nt, mir + 0.3 + k * 0.3, 0.035, -0.4 + 0.27 * k)


# ------------------------------------------------------------------ voices & mix
LEVEL = {"narrator": -20.5, "moses": -19.5, "moses_w": -21.0, "elder": -19.5, "potter": -19.5, "fear": -20.5,
         "god": -19.5}


def place_voices():
    for it in TL["items"]:
        if it["kind"] != "line":
            continue
        x, sr = sf.read(os.path.join(BUILD, "voices", it["id"] + ".wav"))
        dry_len = int((it["end"] - it["start"]) * SR)
        cur = 20 * np.log10(dsp.rms(x[:dry_len]) + 1e-9)
        g = 10 ** ((LEVEL[it["speaker"]] - cur) / 20)
        voice.add(x, it["start"], g)
    # an echo of the Lord's promise beneath Moses quoting it
    x, _ = sf.read(os.path.join(BUILD, "voices", "g0.wav"))
    sfx.add(x, CAP("m7", 2) + 0.05, 0.08 * 10 ** ((LEVEL["god"] + 26) / 20))


def duck_curve(v, depth_db=9.0):
    e = np.sqrt(signal.sosfilt(signal.butter(1, 6, fs=SR, output="sos"), (v ** 2).mean(1)))
    act = np.clip((20 * np.log10(e + 1e-9) + 48) / 18, 0, 1)
    # attack fast, release slow
    out = np.zeros_like(act)
    a_up, a_dn = np.exp(-1 / (0.06 * SR)), np.exp(-1 / (0.6 * SR))
    hop = 240
    small = act[::hop]
    sm = np.zeros_like(small)
    prev = 0.0
    for i, a in enumerate(small):
        coef = a_up ** hop if a > prev else a_dn ** hop
        prev = coef * prev + (1 - coef) * a
        sm[i] = prev
    out = np.interp(np.arange(len(act)), np.arange(len(sm)) * hop, sm)
    return 10 ** (-depth_db * out / 20)


def main():
    score()
    place_voices()
    ir = dsp.make_ir(SR, 2.6, 0.55, 0.03, 11)
    mus = dsp.reverb(music.x, ir, wet=0.32, dry=1.0)[:N]
    duck = duck_curve(voice.x)
    mix = voice.x + mus * duck[:, None] * 0.9 + sfx.x + amb.x * (0.55 + 0.45 * duck[:, None])
    mix = dsp.highpass(mix, SR, 28)
    peak = np.abs(mix).max()
    mix *= 0.89 / peak
    sf.write(os.path.join(BUILD, "mix.wav"), mix.astype(np.float32), SR, subtype="FLOAT")
    for name, b in (("voice", voice.x), ("music", mus * duck[:, None] * 0.9), ("sfx", sfx.x), ("amb", amb.x)):
        sf.write(os.path.join(BUILD, f"stem_{name}.wav"), (b * 0.89 / peak).astype(np.float32), SR, subtype="FLOAT")
    print(f"mix: {len(mix) / SR:.1f}s, peak before norm {peak:.2f}")


if __name__ == "__main__":
    main()
