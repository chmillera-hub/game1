import numpy as np
from scipy import signal
SR = 48000
rng = np.random.default_rng(7)

NOTE = {"C":0,"C#":1,"Db":1,"D":2,"Eb":3,"E":4,"F":5,"F#":6,"G":7,"Ab":8,"A":9,"Bb":10,"B":11}
def chord_notes(name, base_oct=3, transpose=0):
    root = name[0] + (name[1] if len(name) > 1 and name[1] in "#b" else "")
    q = name[len(root):]
    r = NOTE[root] + 12 * (base_oct + 1) + transpose
    if q == "m": iv = [0, 3, 7]
    elif q == "7": iv = [0, 4, 7, 10]
    else: iv = [0, 4, 7]
    return [r + i for i in iv]

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def tarr(d): return np.arange(int(d * SR)) / SR

def piano(m, dur, vel=0.5):
    f = hz(m); T = dur + 2.5; t = tarr(T); y = np.zeros_like(t)
    B = 0.00035
    for k in range(1, 13):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > 12000: break
        rate = 0.6 + 0.45 * k + f / 900
        y += (1 / k ** 1.25) * np.exp(-t * rate) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6))
    env = np.minimum(1, t / 0.004)
    off = t > dur
    env[off] *= np.exp(-(t[off] - dur) * 6)
    y *= env * vel
    # hammer
    n = int(0.01 * SR); y[:n] += rng.normal(0, 0.02 * vel, n) * np.linspace(1, 0, n)
    return y

def strings(ms, dur, vel=0.12, att=1.2, rel=1.8, bright=2200):
    T = dur + rel; t = tarr(T); y = np.zeros_like(t)
    for m in ms:
        f = hz(m)
        for d in (-7, 0, 6):
            fd = f * 2 ** (d / 1200)
            vib = 1 + 0.003 * np.sin(2 * np.pi * (4.8 + rng.uniform(-.3, .3)) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(fd * vib) / SR
            for k in range(1, 16):
                if k * fd > 6000: break
                y += np.sin(k * ph + rng.uniform(0, 6)) / k * np.exp(-k * fd / bright)
    env = np.clip(t / att, 0, 1) ** 1.5
    off = t > dur; env[off] *= np.clip(1 - (t[off] - dur) / rel, 0, 1) ** 2
    return y * env * vel / len(ms)

FORM = {"a": [(800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.12), (3900, 130, 0.06)],
        "o": [(450, 70, 1.0), (800, 80, 0.35), (2830, 100, 0.06), (3800, 120, 0.03)],
        "u": [(325, 50, 1.0), (700, 60, 0.15), (2530, 170, 0.03)]}
def choir(ms, dur, vel=0.1, vowel="a", att=1.5, rel=2.0, voices=4):
    T = dur + rel; t = tarr(T); y = np.zeros_like(t)
    fm = FORM[vowel]
    for m in ms:
        f = hz(m)
        for v in range(voices):
            fd = f * 2 ** (rng.uniform(-12, 12) / 1200)
            vib = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(4.5, 5.8) * t + rng.uniform(0, 6))
            drift = 1 + 0.002 * np.interp(t, np.linspace(0, T, 8), rng.normal(0, 1, 8))
            ph = 2 * np.pi * np.cumsum(fd * vib * drift) / SR
            for k in range(1, 40):
                fk = k * fd
                if fk > 5000: break
                a = sum(g / (1 + ((fk - F) / bw) ** 2) for F, bw, g in fm) / k ** 0.3
                y += a * np.sin(k * ph + rng.uniform(0, 6))
    env = np.clip(t / att, 0, 1) ** 2
    off = t > dur; env[off] *= np.clip(1 - (t[off] - dur) / rel, 0, 1) ** 2
    y = y * env
    # breath
    br = signal.sosfilt(signal.butter(2, [2500, 7000], "bandpass", fs=SR, output="sos"), rng.normal(0, 1, len(t)))
    y += br * env * 0.02 * len(ms)
    return y * vel / (len(ms) * voices) * 3

def bell(m, dur=4.0, vel=0.3):
    f = hz(m); t = tarr(dur); y = np.zeros_like(t)
    for r, a, dcy in [(1, 1, 1.2), (2.0, .5, 2), (2.76, .4, 2.8), (4.07, .25, 4), (5.4, .2, 5.5), (6.8, .1, 7)]:
        y += a * np.exp(-t * dcy) * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6))
    return y * vel * np.minimum(1, t / 0.002)

def colored_noise(n, alpha=1.0):
    w = rng.normal(0, 1, n)
    W = np.fft.rfft(w); fr = np.fft.rfftfreq(n, 1 / SR); fr[0] = fr[1]
    W /= fr ** (alpha / 2)
    y = np.fft.irfft(W, n)
    return y / (np.abs(y).max() + 1e-9)

def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)

def smooth_rand(n, points, lo=0, hi=1):
    xs = np.linspace(0, n, points); v = rng.uniform(lo, hi, points)
    return np.interp(np.arange(n), xs, v)

def rain(dur, muffled=False):
    n = int(dur * SR)
    y = bp(colored_noise(n, 0.6), 500, 9000) * 0.5
    # drips
    drips = np.zeros(n)
    k = int(dur * 60)
    pos = rng.integers(0, n - 2000, k)
    for p in pos:
        drips[p] += rng.uniform(0.2, 1.0) * rng.choice([-1, 1])
    drips = bp(drips, 1500, 6000) * 0.6
    y = y + drips
    y *= 0.8 + 0.2 * smooth_rand(n, int(dur / 3) + 2)
    if muffled: y = lp(y, 1200, 4) * 1.4
    return y

def wind(dur, intensity=1.0):
    n = int(dur * SR); base = colored_noise(n, 1.2); y = np.zeros(n)
    for c in (180, 320, 520, 800):
        y += bp(base, c * 0.85, c * 1.15) * smooth_rand(n, int(dur / 2) + 3, 0.1, 1.0)
    return y / (np.abs(y).max() + 1e-9) * intensity

def thunder(dur=7.0, crack=True, vel=1.0):
    n = int(dur * SR); t = tarr(dur)
    r = lp(colored_noise(n, 2.0), 260, 2) * 2
    env = np.minimum(1, t / 0.08) * np.exp(-t / (dur * 0.28))
    mod = 0.4 + 0.6 * smooth_rand(n, int(dur * 6), 0, 1) ** 2
    y = r * env * mod
    if crack:
        c = hp(rng.normal(0, 1, n), 800) * np.exp(-t / 0.05) * 0.5
        c += bp(rng.normal(0, 1, n), 200, 2500) * np.exp(-t / 0.25) * 0.4 * (smooth_rand(n, 60) > 0.5)
        y += c
    return y / (np.abs(y).max() + 1e-9) * vel

def heartbeat(vel=0.8):
    t = tarr(0.9); y = np.zeros_like(t)
    for off, a in ((0, 1.0), (0.28, 0.7)):
        tt = t - off; m = tt >= 0
        f = 60 * np.exp(-tt[m] * 6) + 38
        y[m] += a * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt[m] / 0.09)
    return y * vel

def footstep(vel=0.4, wet=True):
    t = tarr(0.25)
    y = lp(rng.normal(0, 1, len(t)), 2500) * np.exp(-t / 0.02) * 0.6
    y += np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.04)
    if wet: y += hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t / 0.06) * 0.15
    return y * vel

def door_creak(dur=1.2, vel=0.3):
    t = tarr(dur)
    rate = 25 + 70 * (t / dur) ** 0.6 + 10 * np.sin(2 * np.pi * 3 * t)
    ph = np.cumsum(rate) / SR
    clicks = ((ph % 1) < (np.roll(ph, 1) % 1)).astype(float)
    y = bp(clicks, 500, 1800, 3) * 6 + bp(clicks, 1800, 3200, 2) * 3
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    return y * env * vel

def door_thud(vel=0.6):
    t = tarr(0.8)
    y = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.08) + lp(rng.normal(0, 1, len(t)), 600) * np.exp(-t / 0.05) * 0.8
    return y * vel

def drone(dur, ms, vel=0.15):
    t = tarr(dur); y = np.zeros_like(t)
    for m in ms:
        f = hz(m)
        for d in (-4, 4):
            y += np.sin(2 * np.pi * f * 2 ** (d / 1200) * t + rng.uniform(0, 6))
            y += 0.3 * np.sin(2 * np.pi * 2 * f * 2 ** (d / 1200) * t)
    sw = 0.6 + 0.4 * smooth_rand(len(t), int(dur / 4) + 2)
    return y * sw * vel / len(ms)

def shimmer(dur, vel=0.1):
    """high glassy cluster for the divine light"""
    t = tarr(dur); y = np.zeros_like(t)
    for m in (88, 91, 95, 96, 100):
        y += np.sin(2 * np.pi * hz(m) * t + rng.uniform(0, 6)) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.2, 0.7) * t + rng.uniform(0, 6)))
    env = np.clip(t / 3, 0, 1) * np.clip((dur - t) / 3, 0, 1)
    return y * env * vel / 5

def reverb_ir(rt60=2.5, pre=0.02, bright=6000):
    n = int(rt60 * SR); t = tarr(rt60)
    irs = []
    for ch in range(2):
        x = rng.normal(0, 1, n) * np.exp(-6.9 * t / rt60)
        x = lp(x, bright)
        x = np.concatenate([np.zeros(int(pre * SR)), x])
        irs.append(x / np.sqrt(np.sum(x ** 2)))
    return irs
