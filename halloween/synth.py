"""Tiny numpy synthesizer: instruments and sound effects (mono float32 arrays)."""
import math

import numpy as np
from scipy.signal import lfilter

SR = 48000
RNG = np.random.default_rng(7)

NOTE_IDX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    """'C#4' / 'Bb3' / 62 -> midi number."""
    if isinstance(name, (int, float)):
        return name
    n = NOTE_IDX[name[0]]
    i = 1
    while i < len(name) and name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def hz(m):
    return 440.0 * 2 ** ((midi(m) - 69) / 12.0)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, sustain_len=None):
    """Simple ADSR over n samples (release fills the tail)."""
    e = np.zeros(n, np.float32)
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    S = n - A - D - R if sustain_len is None else int(sustain_len * SR)
    S = max(0, S)
    idx = 0
    seg = min(A, n - idx)
    e[idx:idx + seg] = np.linspace(0, 1, A, endpoint=False)[:seg]
    idx += seg
    seg = min(D, n - idx)
    e[idx:idx + seg] = np.linspace(1, s, D, endpoint=False)[:seg]
    idx += seg
    seg = min(S, n - idx)
    e[idx:idx + seg] = s
    idx += seg
    seg = n - idx
    if seg > 0:
        e[idx:] = np.linspace(s, 0, seg)
    return e


# ------------------------------------------------------------------ filters
def biquad(kind, f0, q=0.707, gain_db=0.0):
    w = 2 * math.pi * f0 / SR
    cw, sw = math.cos(w), math.sin(w)
    alpha = sw / (2 * q)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bp":
        b = [alpha, 0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def filt(x, kind, f0, q=0.707):
    b, a = biquad(kind, min(f0, SR * 0.45), q)
    return lfilter(b, a, x).astype(np.float32)


def sweep_filter(x, kind, f_curve, q=4.0, block=512):
    """Time-varying biquad: f_curve(t_sec) -> Hz, updated per block."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        f0 = f_curve((i + block / 2) / SR)
        b, a = biquad(kind, max(30.0, min(f0, SR * 0.45)), q)
        y[i:i + block], zi = lfilter(b, a, x[i:i + block], zi=zi)
    return y


def noise(n):
    return RNG.standard_normal(n).astype(np.float32)


def pink(n):
    w = noise(n)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    return (lfilter(b, a, w) * 8).astype(np.float32)


# ------------------------------------------------------------------ oscillators
def saw(freq, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(freq, t.shape) / SR) + phase if np.ndim(freq) else freq * t + phase
    return (2 * (ph % 1.0) - 1).astype(np.float32)


def osc_phase(freq_arr):
    return np.cumsum(freq_arr) / SR


# ------------------------------------------------------------------ instruments
def celesta(note, dur=1.6, vel=0.6):
    f = hz(note)
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for ratio, amp, dec in ((1, 1.0, 1.3), (2, 0.32, 2.6), (3, 0.10, 4.0), (4.07, 0.07, 6.0), (0.5, 0.05, 1.0)):
        if f * ratio < SR * 0.45:
            y += amp * np.sin(2 * math.pi * f * ratio * t + ratio) * np.exp(-dec * t)
    att = np.minimum(1, t / 0.003)
    click = noise(n) * np.exp(-t * 300) * 0.08
    y = (y * att + filt(click, "hp", 3000)) * vel * 0.5
    return y


def glock(note, dur=1.2, vel=0.6):
    f = hz(note)
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for ratio, amp, dec in ((1, 1.0, 1.6), (2.76, 0.38, 4.0), (5.40, 0.16, 7.0), (8.93, 0.06, 11.0)):
        if f * ratio < SR * 0.45:
            y += amp * np.sin(2 * math.pi * f * ratio * t) * np.exp(-dec * t)
    return y * np.minimum(1, t / 0.0015) * vel * 0.42


def pizz(note, dur=0.6, vel=0.6, bright=1.0):
    f = hz(note)
    n = int((dur + 0.4) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    k = 1
    while f * k < 6000 and k <= 14:
        y += (1.0 / k) * np.sin(2 * math.pi * f * k * t + k * 0.7) * np.exp(-t * (3.5 + 1.6 * k / bright))
        k += 1
    y *= np.minimum(1, t / 0.002)
    return y * vel * 0.55


def harp(note, dur=1.5, vel=0.5):
    f = hz(note)
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for k in range(1, 9):
        if f * k > 9000:
            break
        y += (1.0 / k ** 1.3) * np.sin(2 * math.pi * f * k * t) * np.exp(-t * (1.0 + 0.7 * k))
    return y * np.minimum(1, t / 0.002) * vel * 0.5


def pad(notes, dur, vel=0.35, attack=0.8, release=1.2, cutoff=1800, voices=4, vowel=None):
    """String pad: detuned saws -> lowpass."""
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for note in notes:
        f = hz(note)
        for v in range(voices):
            det = 1 + (v - (voices - 1) / 2) * 0.0035
            vib = 1 + 0.002 * np.sin(2 * math.pi * (4.8 + v * 0.37) * t + v)
            ph = np.cumsum(f * det * vib) / SR + v * 0.31
            y += (2 * (ph % 1.0) - 1).astype(np.float32)
    y /= (len(notes) * voices) ** 0.5
    y = filt(filt(y, "lp", cutoff, 0.6), "lp", cutoff * 1.4, 0.6)
    e = env_adsr(n, attack, 0.3, 0.85, release, sustain_len=max(0.0, dur - attack - 0.3))
    return y * e * vel * 0.5


def choir(notes, dur, vel=0.3, vowel="oo", attack=1.0, release=1.5):
    F = {"oo": ((320, 1.0, 6), (800, 0.45, 8), (2250, 0.12, 10)),
         "ah": ((720, 1.0, 6), (1100, 0.6, 8), (2500, 0.18, 10)),
         "mm": ((260, 1.0, 5), (1900, 0.08, 8), (2700, 0.05, 10))}[vowel]
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    src = np.zeros(n, np.float32)
    for note in notes:
        f = hz(note)
        for v in range(3):
            vib = 1 + 0.006 * np.sin(2 * math.pi * (5.2 + v * 0.4) * t + v * 2)
            ph = np.cumsum(f * (1 + (v - 1) * 0.004) * vib) / SR + v * 0.2
            src += (2 * (ph % 1.0) - 1).astype(np.float32)
    y = np.zeros(n, np.float32)
    for f0, amp, q in F:
        y += amp * filt(src, "bp", f0, q)
    y /= (len(notes) * 3) ** 0.5
    e = env_adsr(n, attack, 0.4, 0.85, release, sustain_len=max(0.0, dur - attack - 0.4))
    return y * e * vel * 1.6


def reed(note, dur, vel=0.4, kind="bassoon", stacc=False):
    f = hz(note)
    n = int((dur + 0.15) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * math.pi * 5.5 * t) * np.minimum(1, t / 0.3)
    ph = np.cumsum(f * vib) / SR
    if kind == "clarinet":
        y = np.sign(np.sin(2 * math.pi * ph)).astype(np.float32) * 0.6
        y = filt(y, "lp", 1600, 0.7)
    else:
        y = (2 * (ph % 1.0) - 1).astype(np.float32)
        y = filt(y, "lp", 1100, 0.7) + 0.6 * filt(y, "bp", 500, 3)
    if stacc:
        e = env_adsr(n, 0.01, 0.08, 0.4, 0.08)
    else:
        e = env_adsr(n, 0.04, 0.1, 0.8, 0.12)
    return y * e * vel * 0.5


def theremin(f_curve, dur, vel=0.3, vib=0.014):
    """f_curve: array of Hz per sample (len >= dur*SR) or callable t->Hz."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f_curve(t) if callable(f_curve) else f_curve[:n]
    f = f * (1 + vib * np.sin(2 * math.pi * 6.2 * t) * np.minimum(1, t / 0.25))
    ph = np.cumsum(f) / SR
    y = np.sin(2 * math.pi * ph) + 0.18 * np.sin(4 * math.pi * ph)
    e = env_adsr(n, 0.12, 0.1, 0.9, 0.35)
    return (y * e * vel * 0.45).astype(np.float32)


def organ(notes, dur, vel=0.3, attack=0.15, release=0.6):
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for note in notes:
        f = hz(note)
        for k, amp in ((0.5, 0.5), (1, 1.0), (2, 0.6), (3, 0.3), (4, 0.25), (6, 0.1)):
            if f * k < 8000:
                y += amp * np.sin(2 * math.pi * f * k * t)
    y *= (1 + 0.12 * np.sin(2 * math.pi * 5.8 * t))
    y /= len(notes) ** 0.5 * 2.2
    e = env_adsr(n, attack, 0.2, 0.9, release, sustain_len=max(0.0, dur - attack - 0.2))
    return y * e * vel * 0.5


def cello(note, dur, vel=0.4, attack=0.25, release=0.5, trem=0.0):
    f = hz(note)
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.005 * np.sin(2 * math.pi * 5.2 * t) * np.minimum(1, t / 0.6)
    ph = np.cumsum(f * vib) / SR
    y = (2 * (ph % 1.0) - 1).astype(np.float32)
    y = filt(filt(y, "lp", 1400, 0.6), "lp", 2200, 0.6) + 0.3 * filt(y, "bp", 300, 2)
    if trem > 0:
        y *= (1 - trem * 0.5 * (1 + np.sign(np.sin(2 * math.pi * 11 * t))) * 0.6)
    e = env_adsr(n, attack, 0.2, 0.9, release, sustain_len=max(0.0, dur - attack - 0.2))
    return y * e * vel * 0.5


def timpani(note, vel=0.6, dur=1.6):
    f = hz(note)
    n = int(dur * SR)
    t = np.arange(n) / SR
    fe = f * (1 + 0.12 * np.exp(-t * 18))
    ph = np.cumsum(fe) / SR
    y = np.sin(2 * math.pi * ph) * np.exp(-t * 2.4) + 0.4 * np.sin(2 * math.pi * 1.5 * ph) * np.exp(-t * 4)
    y += filt(noise(n), "lp", 400) * np.exp(-t * 30) * 0.4
    return (y * vel * 0.6).astype(np.float32)


def bell(note, vel=0.6, dur=6.0):
    """Big church/clock bell."""
    f = hz(note)
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for ratio, amp, dec in ((0.5, 0.7, 0.35), (1.0, 1.0, 0.5), (1.183, 0.55, 0.7), (1.5, 0.4, 0.8), (2.0, 0.6, 1.0),
                            (2.51, 0.3, 1.4), (3.01, 0.22, 1.8), (4.1, 0.12, 2.4), (5.3, 0.06, 3.0)):
        y += amp * np.sin(2 * math.pi * f * ratio * t + ratio) * np.exp(-dec * t)
    y += filt(noise(n), "bp", 2400, 1.0) * np.exp(-t * 40) * 0.5
    return y * np.minimum(1, t / 0.002) * vel * 0.32


def piano_low(note, vel=0.6, dur=3.5):
    f = hz(note)
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for k in range(1, 12):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 7000:
            break
        y += (1.0 / k ** 1.1) * np.sin(2 * math.pi * fk * t) * np.exp(-t * (0.6 + 0.35 * k))
    y += filt(noise(n), "lp", 900) * np.exp(-t * 60) * 0.3
    return y * np.minimum(1, t / 0.004) * vel * 0.42


# ------------------------------------------------------------------ sound effects
def fx_wind(dur, amount=1.0, seed=0):
    n = int(dur * SR)
    rr = np.random.default_rng(seed)
    x = pink(n)
    phase = rr.uniform(0, 6)
    curve = lambda s: 420 + 260 * math.sin(s * 0.37 + phase) + 140 * math.sin(s * 1.13 + 2 * phase)
    howl = sweep_filter(x, "bp", curve, q=5.0)
    body = filt(x, "lp", 700) * 0.35
    gust = 0.6 + 0.4 * np.sin(2 * math.pi * 0.11 * np.arange(n) / SR + phase) ** 2
    y = (howl * 0.9 + body) * gust
    y /= (np.max(np.abs(y)) + 1e-9)
    return (y * 0.35 * amount).astype(np.float32)


def fx_ghost_howl(dur=3.0, vel=0.8, f0=320.0):
    """'OOOOoooo' through the keyhole: a breathy resonant moan."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.35 * np.exp(-((t - 0.6) ** 2) / 0.3) - 0.18 * t / dur) * (1 + 0.02 * np.sin(2 * math.pi * 5.5 * t))
    tone = theremin(f, dur, vel=0.5, vib=0.0)
    breath = sweep_filter(pink(n), "bp", lambda s: f0 * (1.2 + 0.4 * math.sin(s * 2.2)), q=9.0) * 0.6
    e = env_adsr(n, 0.35, 0.3, 0.8, dur * 0.45)
    y = (tone * 0.7 + breath) * e
    return (y / (np.max(np.abs(y)) + 1e-9) * vel * 0.6).astype(np.float32)


def fx_whistle(dur=1.4, vel=0.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 780 + 180 * np.sin(2 * math.pi * t / dur * 0.8) + 25 * np.sin(2 * math.pi * 6 * t)
    y = theremin(f, dur, vel=0.4, vib=0.0) + 0.3 * filt(pink(n), "bp", 900, 6)
    e = env_adsr(n, 0.3, 0.2, 0.8, 0.5)
    return (y * e * vel).astype(np.float32)


def fx_tick(vel=0.3, pitch=1.0):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    y = filt(noise(n), "bp", 3200 * pitch, 3) * np.exp(-t * 160)
    y += np.sin(2 * math.pi * 1600 * pitch * t) * np.exp(-t * 120) * 0.3
    return (y * vel).astype(np.float32)


def fx_thump(vel=0.8, f=55.0, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = np.cumsum(f * (1 + 1.2 * np.exp(-t * 25))) / SR
    y = np.sin(2 * math.pi * ph) * np.exp(-t * 7)
    y += filt(noise(n), "lp", 300) * np.exp(-t * 25) * 0.6
    return (y * vel).astype(np.float32)


def fx_creak(dur=0.9, vel=0.4, f_lo=25.0, f_hi=90.0, seed=1):
    """Stick-slip wood creak: jittery impulse train through resonances."""
    n = int(dur * SR)
    rr = np.random.default_rng(seed)
    x = np.zeros(n, np.float32)
    t = 0.0
    while t < dur:
        u = t / dur
        rate = f_lo + (f_hi - f_lo) * math.sin(math.pi * u)
        i = int(t * SR)
        if i < n:
            x[i] = rr.uniform(0.5, 1.0)
        t += (1.0 / rate) * rr.uniform(0.85, 1.15)
    y = filt(x, "bp", 620, 6) + 0.7 * filt(x, "bp", 1350, 8) + 0.4 * filt(x, "bp", 2400, 10)
    y *= env_adsr(n, 0.05, 0.1, 0.9, 0.2)
    return (y / (np.max(np.abs(y)) + 1e-9) * vel).astype(np.float32)


def fx_purr(dur=2.0, vel=0.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = filt(noise(n), "lp", 180, 0.8)
    am = 0.5 + 0.5 * np.sin(2 * math.pi * 24 * t) ** 2
    breath = 0.55 + 0.45 * np.sin(2 * math.pi * t / 1.6) ** 2
    y = x * am * breath * env_adsr(n, 0.3, 0.1, 0.9, 0.5)
    return (y / (np.max(np.abs(y)) + 1e-9) * vel).astype(np.float32)


def fx_mrrp(vel=0.5):
    dur = 0.42
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 380 + 300 * (t / dur) ** 0.7
    ph = np.cumsum(f) / SR
    src = (2 * (ph % 1.0) - 1).astype(np.float32)
    trill = 0.55 + 0.45 * np.sign(np.sin(2 * math.pi * 28 * t))
    y = filt(src, "bp", 700, 3) + 0.6 * filt(src, "bp", 1500, 5)
    y = y * trill * env_adsr(n, 0.03, 0.05, 0.9, 0.12)
    return (y / (np.max(np.abs(y)) + 1e-9) * vel).astype(np.float32)


def fx_pop(vel=0.4):
    dur = 0.16
    n = int(dur * SR)
    y = sweep_filter(noise(n), "bp", lambda s: 900 + 6000 * s / dur, q=2.5, block=128)
    y *= env_adsr(n, 0.005, 0.03, 0.6, 0.1)
    return (y * vel * 0.6).astype(np.float32)


def fx_plip(vel=0.4, f=900.0):
    dur = 0.18
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = np.cumsum(f * (1 + 0.8 * np.exp(-t * 40))) / SR
    return (np.sin(2 * math.pi * ph) * np.exp(-t * 26) * vel * 0.5).astype(np.float32)


def fx_rustle(dur=0.5, vel=0.4, seed=3):
    n = int(dur * SR)
    rr = np.random.default_rng(seed)
    x = filt(noise(n), "hp", 2200)
    am = np.zeros(n, np.float32)
    for _ in range(int(dur * 18)):
        c = rr.integers(0, n)
        w = int(rr.uniform(0.01, 0.04) * SR)
        am[c:c + w] += np.hanning(min(w, n - c)) * rr.uniform(0.3, 1.0)
    return (x * am * vel * 0.4).astype(np.float32)


def fx_scribble(dur=2.5, vel=0.3, seed=5):
    n = int(dur * SR)
    rr = np.random.default_rng(seed)
    x = filt(filt(noise(n), "bp", 3500, 1.2), "hp", 1500)
    t = np.arange(n) / SR
    strokes = 0.5 + 0.5 * np.sin(2 * math.pi * (5.0 + 2 * np.sin(t * 1.7)) * t) ** 2
    gaps = (np.sin(2 * math.pi * 0.9 * t + rr.uniform(0, 6)) > -0.6).astype(np.float32)
    return (x * strokes * gaps * vel * 0.25 * env_adsr(n, 0.05, 0.1, 1.0, 0.1)).astype(np.float32)


def fx_heartbeat(vel=0.7):
    a = fx_thump(vel, 48, 0.45)
    b = fx_thump(vel * 0.8, 58, 0.45)
    out = np.zeros(int(0.9 * SR), np.float32)
    out[:len(a)] += a
    k = int(0.26 * SR)
    out[k:k + len(b)] += b[: len(out) - k]
    return out


def fx_click(vel=0.4):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    y = filt(noise(n), "bp", 2600, 2) * np.exp(-t * 90) + np.sin(2 * math.pi * 2200 * t) * np.exp(-t * 60) * 0.4
    return (y * vel).astype(np.float32)


def fx_owl(vel=0.35):
    out = np.zeros(int(1.5 * SR), np.float32)
    for k, (st, f0, d) in enumerate(((0.0, 410, 0.42), (0.62, 390, 0.62))):
        n = int(d * SR)
        t = np.arange(n) / SR
        f = f0 * (1 + 0.05 * np.exp(-t * 8)) * (1 - 0.06 * t / d)
        y = theremin(f, d, vel=1.0, vib=0.003)
        y = filt(y, "lp", 900) + 0.2 * filt(pink(n), "bp", f0, 5)
        i = int(st * SR)
        out[i:i + n] += y * env_adsr(n, 0.06, 0.05, 0.9, 0.2)
    return out * vel


def fx_whoosh(dur=0.7, vel=0.3, up=True):
    n = int(dur * SR)
    f = (lambda s: 300 + 3000 * (s / dur) ** 1.5) if up else (lambda s: 3300 - 3000 * (s / dur) ** 0.7)
    y = sweep_filter(noise(n), "bp", f, q=1.5, block=256) * env_adsr(n, dur * 0.4, 0.1, 0.8, dur * 0.4)
    return (y * vel * 0.5).astype(np.float32)


def fx_yawn_horn(vel=0.35):
    """Comic descending bassoon 'waaah' for the yawn."""
    dur = 1.1
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz("D3") * (1.12 - 0.25 * (t / dur) ** 1.4)
    ph = np.cumsum(f * (1 + 0.01 * np.sin(2 * math.pi * 6 * t))) / SR
    y = (2 * (ph % 1.0) - 1).astype(np.float32)
    y = filt(y, "lp", 900, 0.7) + 0.6 * filt(y, "bp", 480, 3)
    return (y * env_adsr(n, 0.06, 0.1, 0.85, 0.3) * vel).astype(np.float32)


def sparkle(dur=2.0, vel=0.25, notes=("D6", "F#6", "A6", "C#7", "E6", "A5"), seed=11, density=10):
    n = int((dur + 1.2) * SR)
    out = np.zeros(n, np.float32)
    rr = np.random.default_rng(seed)
    k = int(dur * density)
    for i in range(k):
        st = int(rr.uniform(0, dur) * SR)
        g = glock(notes[rr.integers(0, len(notes))], 0.6, vel * rr.uniform(0.4, 1.0))
        out[st:st + len(g)] += g[: n - st]
    return out
