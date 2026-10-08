"""Synth instruments, effects and a stereo track helper (shared with the first video)."""
import math, random
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = max(1, min(A, n))
    e[:A] = np.linspace(0, 1, A)
    D = min(D, n - A)
    if D > 0:
        e[A:A + D] = np.linspace(1, s, D)
    if R > 0 and R < n:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments

def epiano(f, dur, vel=0.5):
    t = tvec(dur + 0.6)
    out = np.zeros_like(t)
    for k, (amp, dec) in enumerate(((1.0, 1.6), (0.32, 0.9), (0.1, 0.5), (0.05, 0.3))):
        out += amp * np.sin(2 * np.pi * f * (k + 1) * t) * np.exp(-t / dec)
    out += 0.06 * np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.05)
    out *= 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    env = np.ones_like(t)
    rel = int(0.5 * SR)
    env[int(dur * SR):] = np.linspace(1, 0, len(t) - int(dur * SR))
    return out * env * vel * 0.25


def piano(f, dur, vel=0.5):
    t = tvec(dur + 1.2)
    out = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 9000:
            break
        out += (1 / k ** 1.4) * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.6 + 0.5 * k) * (f / 400) ** 0.3)
    att = np.minimum(1, t / 0.004)
    env = np.ones_like(t)
    env[int(dur * SR):] = np.exp(-np.arange(len(t) - int(dur * SR)) / SR / 0.25)
    return out * att * env * vel * 0.22


def marimba(f, vel=0.5):
    t = tvec(1.2)
    out = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) + 0.3 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.08)
           + 0.08 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.03))
    return out * np.minimum(1, t / 0.002) * vel * 0.3


def glock(f, vel=0.5, dec=1.2):
    t = tvec(dec * 2.5)
    out = (np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / (dec * 0.4))
           + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / (dec * 0.2)))
    return out * np.minimum(1, t / 0.002) * vel * 0.2


def additive(f, dur, spectrum, vib=0.0, att=0.6, rel=1.2, detune=(-5, 0, 5)):
    t = tvec(dur + rel)
    out = np.zeros_like(t)
    vibm = 1 + vib * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6))
    for cents in detune:
        f0 = f * 2 ** (cents / 1200)
        ph = 2 * np.pi * f0 * np.cumsum(vibm) / SR
        k = 1
        while f0 * k < 7000 and k < 40:
            a = spectrum(f0 * k, k)
            if a > 1e-3:
                out += a * np.sin(k * ph + rng.uniform(0, 6))
            k += 1
    n_on = int(dur * SR)
    env = np.ones_like(t)
    A = int(att * SR)
    env[:A] = np.linspace(0, 1, A) ** 1.5
    env[n_on:] = np.linspace(1, 0, len(t) - n_on) ** 2
    return out * env / len(detune)


def pad(f, dur, vel=0.3, att=1.0, rel=1.6):
    return additive(f, dur, lambda fk, k: 1 / k * math.exp(-fk / 1800), 0.002, att, rel) * vel


def strings(f, dur, vel=0.3, att=0.9, rel=1.8):
    return additive(f, dur, lambda fk, k: 1 / k ** 0.9 * math.exp(-fk / 2600), 0.006, att, rel) * vel


def choir(f, dur, vel=0.3, att=1.2, rel=2.0):
    formants = ((750, 90), (1150, 110), (2600, 160))

    def sp(fk, k):
        g = sum(math.exp(-((fk - F) / bw) ** 2) * w for (F, bw), w in zip(formants, (1.0, 0.6, 0.25)))
        return (0.15 + g) / k ** 0.5
    return additive(f, dur, sp, 0.008, att, rel, detune=(-9, -3, 3, 9)) * vel


def bass(f, dur, vel=0.5):
    t = tvec(dur + 0.1)
    out = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return out * adsr(len(t), 0.005, 0.2, 0.6, 0.08) * vel * 0.35


def kick(vel=0.6):
    t = tvec(0.4)
    f = 45 + 90 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) * vel


def snare(vel=0.3, dur=0.2, lo=900, hi=6000):
    t = tvec(dur)
    n = bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t / (dur * 0.3))
    return n * vel


def hat(vel=0.15):
    t = tvec(0.06)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / 0.015) * vel


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def reverb_ir(sec=2.0, damp=3000, seed=1):
    r = np.random.default_rng(seed)
    t = tvec(sec)
    ir = r.standard_normal(len(t)) * np.exp(-t / (sec / 6.5))
    ir = lp(ir, damp)
    ir[0] = 0
    return ir / np.sqrt((ir ** 2).sum())


IR_L, IR_R = reverb_ir(2.4, 3500, 1), reverb_ir(2.4, 3500, 2)
ROOM_L, ROOM_R = reverb_ir(0.7, 4500, 3), reverb_ir(0.7, 4500, 4)


def verb(x, wet=0.25, room=False):
    L, R = (ROOM_L, ROOM_R) if room else (IR_L, IR_R)
    yl = fftconvolve(x, L)[: len(x)]
    yr = fftconvolve(x, R)[: len(x)]
    return np.stack([x + wet * yl, x + wet * yr])


# ---------------------------------------------------------------- track helper

class Track:
    def __init__(self, total):
        self.n = int((total + 2) * SR)
        self.buf = np.zeros((2, self.n))

    def add(self, t, x, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= self.n or i < -len(x if x.ndim == 1 else x[0]):
            return
        if x.ndim == 1:
            l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
            x = np.stack([x * l * 1.414, x * r * 1.414])
        if i < 0:
            x = x[:, -i:]
            i = 0
        m = min(x.shape[1], self.n - i)
        self.buf[:, i:i + m] += x[:, :m] * gain


def gate(track, segments, total, fade=0.15):
    """Multiply a track by 1 inside segments, 0 outside (with fades)."""
    g = np.zeros(track.n)
    for a, b in segments:
        ia, ib = int(a * SR), int(b * SR)
        g[ia:ib] = 1
    k = int(fade * SR)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    track.buf *= g


# ---------------------------------------------------------------- sfx

def sfx_pop():
    t = tvec(0.12)
    f = 500 + 900 * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04) * 0.4


def sfx_ding(f=1320):
    return glock(f, 0.9, 0.6)


def sfx_whoosh(dur=0.7, up=True):
    n = noise(dur)
    t = tvec(dur)
    env = np.sin(np.pi * t / dur) ** 2
    out = np.zeros_like(n)
    seg = int(0.02 * SR)
    for i in range(0, len(n), seg):
        u = i / len(n)
        fc = 300 + 3000 * (u if up else 1 - u)
        out[i:i + seg] = bp(n[max(0, i - 2000):i + seg], fc * 0.6, fc * 1.4)[-len(n[i:i + seg]):]
    return out * env * 0.5


def sfx_kaching():
    out = np.zeros(int(1.6 * SR))
    for k, f in enumerate((2093, 2637, 3136)):
        g = glock(f, 0.8, 0.7)
        out[int(0.09 * k * SR):int(0.09 * k * SR) + len(g)] += g[: len(out) - int(0.09 * k * SR)]
    out[: int(0.05 * SR)] += snare(0.4, 0.05, 2000, 8000)
    return out * 1.6


def sfx_coin():
    f = rng.uniform(2500, 4200)
    return glock(f, 0.35, 0.15)


def sfx_scratch():
    t = tvec(0.45)
    f = 200 + 1600 * np.abs(np.sin(2 * np.pi * 2.2 * t)) * np.exp(-t / 0.3)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bp(noise(0.45), 800, 4000) * 0.4
    return s * np.exp(-t / 0.25)


def sfx_tick():
    t = tvec(0.04)
    return hp(noise(0.04), 2500) * np.exp(-t / 0.004) * 0.5 + np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.006) * 0.3


def sfx_cricket():
    t = tvec(0.35)
    car = np.sin(2 * np.pi * 4300 * t)
    am = (np.sin(2 * np.pi * 30 * t) > 0.2).astype(float)
    return car * am * np.sin(np.pi * t / 0.35) * 0.05


def sfx_thump(f=70, dur=0.35, vel=0.9):
    t = tvec(dur)
    fr = f + 60 * np.exp(-t / 0.03)
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / (dur * 0.35)) + lp(noise(dur), 900) * np.exp(-t / 0.03) * 0.5) * vel


def sfx_spit():
    t = tvec(0.6)
    n = bp(noise(0.6), 800, 5000) * np.exp(-t / 0.15)
    n[: int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))
    return n * 0.7


def sfx_step():
    t = tvec(0.12)
    return lp(noise(0.12), 600) * np.exp(-t / 0.03) * 0.35


def sfx_creak():
    t = tvec(0.7)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.15
    return bp(s, 300, 2500) * np.sin(np.pi * t / 0.7) * 0.5


def sfx_click():
    t = tvec(0.03)
    return hp(noise(0.03), 1500) * np.exp(-t / 0.003) * 0.5


def sfx_shimmer(dur=2.0):
    out = np.zeros(int((dur + 1.5) * SR))
    r = random.Random(3)
    for k in range(18):
        f = mtof(r.choice([74, 78, 81, 86, 90, 93]))
        g = glock(f, 0.18, 0.5)
        i = int(k / 18 * dur * SR)
        out[i:i + len(g)] += g[: len(out) - i]
    return out


def sfx_chirp():
    t = tvec(0.18)
    f = 3000 + 1500 * np.sin(np.pi * t / 0.18) + 400 * np.sin(2 * np.pi * 25 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.18) ** 2 * 0.12


def sfx_squeak():
    t = tvec(0.15)
    f = 1100 + 500 * t / 0.15
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.15) * 0.05


