#!/usr/bin/env python3
"""sfx.py — synthesise every sound effect of the film into audio/sfx/<name>.wav (44.1 kHz stereo PCM16).

    python3 audio/sfx.py                    # all
    python3 audio/sfx.py alarm_bell sob     # some
    python3 audio/sfx.py --spectro out      # also write out/spectro_sfx_<name>.png
    python3 audio/sfx.py --list

Everything is procedural and deterministic (fixed seeds): modal synthesis (struck metal/plastic/glass),
resonator banks driven by stick-slip pulse trains (creaks), formant-filtered glottal sources (walla, sob),
shaped noise (breath, cloth, paper, whoosh). Each file is DC-free, faded (except seamless loops) and
peak-normalised to -3 dBFS. Loop-seamless files: alarm_bell (3.0 s), heartbeat (1.3 s).
"""
import math
import os
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audiolib as A  # noqa: E402

SR = A.SR
OUT = os.path.join(HERE, "sfx")

# ============================================================================================
# building blocks


def N(sec):
    return int(round(sec * SR))


def tt(n):
    return np.arange(n) / SR


def white(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def pink(n, seed):
    """1/f noise (FFT shaped), unit RMS."""
    w = np.fft.rfft(white(n, seed))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    p = np.fft.irfft(w / np.sqrt(f), n)
    return p / (np.std(p) + 1e-12)


def brown(n, seed):
    b = np.cumsum(white(n, seed))
    b = signal.sosfilt(signal.butter(1, 15, "highpass", fs=SR, output="sos"), b)
    return b / (np.std(b) + 1e-12)


def bp(x, f, q=4.0):
    """RBJ constant-0-dB-peak band-pass."""
    w0 = 2 * np.pi * min(f, SR * 0.45) / SR
    al = np.sin(w0) / (2 * q)
    b = [al, 0, -al]
    a = [1 + al, -2 * np.cos(w0), 1 - al]
    return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, min(f, SR * 0.45), "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def bandn(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR * 0.45)], "bandpass", fs=SR, output="sos"), x)


def resonator(exc, f, tau):
    """2-pole resonator: an impulse of height 1 rings as sin(2πft)·e^(−t/τ) (unit amplitude)."""
    r = math.exp(-1.0 / (tau * SR))
    w = 2 * math.pi * f / SR
    return signal.lfilter([math.sin(w)], [1, -2 * r * math.cos(w), r * r], exc)


def modal(exc, modes):
    """Sum of resonators: modes = [(freq, amp, tau), ...] driven by the same excitation."""
    out = np.zeros(len(exc))
    for f, a, tau in modes:
        if f < SR * 0.45:
            out += a * resonator(exc, f, tau)
    return out


def impulses(n, times, amps=None):
    x = np.zeros(n)
    for i, t in enumerate(times):
        k = int(round(t * SR))
        if 0 <= k < n:
            x[k] += 1.0 if amps is None else amps[i]
    return x


def burst(n, at, dur, seed, lo=500, hi=8000, shape=2.0, amp=1.0):
    """A short band-limited noise burst (exponential-ish envelope) placed at `at` seconds."""
    m = N(dur)
    e = np.exp(-np.linspace(0, shape * 3, m))
    e[: max(1, N(0.0008))] *= np.linspace(0, 1, max(1, N(0.0008)))
    b = bandn(white(m, seed), lo, hi) * e * amp
    x = np.zeros(n)
    k = N(at)
    x[k:k + m] += b[: max(0, min(m, n - k))]
    return x


def smooth_env(points, n):
    """Piecewise-linear envelope from [(sec, value), ...] smoothed with a raised-cosine between points."""
    ts = np.array([p[0] for p in points]) * SR
    vs = np.array([p[1] for p in points])
    i = np.arange(n)
    idx = np.clip(np.searchsorted(ts, i, side="right") - 1, 0, len(ts) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    f = np.clip((i - t0) / np.maximum(t1 - t0, 1), 0, 1)
    f = 0.5 - 0.5 * np.cos(np.pi * f)
    return vs[idx] + (vs[idx + 1] - vs[idx]) * f


def slow_noise(n, rate_hz, seed):
    """Smooth random control signal in [-1, 1] changing at about `rate_hz`."""
    k = max(4, int(n / SR * rate_hz) + 4)
    pts = np.random.default_rng(seed).uniform(-1, 1, k)
    x = np.interp(np.linspace(0, k - 3, n), np.arange(k), pts)
    return lp(x, max(rate_hz * 1.5, 0.5), 1) if n > 32 else x


def glottal(f0, seed, n_harm=24, tilt=1.25, jitter=0.01):
    """Band-limited glottal-ish source from a per-sample f0 contour."""
    n = len(f0)
    f = f0 * (1 + jitter * slow_noise(n, 30, seed))
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros(n)
    for k in range(1, n_harm + 1):
        m = (k * f) < 5000
        out += np.where(m, np.sin(k * ph) / k ** tilt, 0.0)
    return out


FORMANTS = {  # vowel → (F1, F2, F3) Hz
    "a": (730, 1100, 2450), "e": (530, 1750, 2450), "i": (320, 2200, 2900), "o": (520, 900, 2400),
    "u": (360, 850, 2250), "uh": (600, 1200, 2400), "eh": (580, 1600, 2500),
}


def formant(x, vowel, shift=1.0, bw=(80, 100, 140)):
    F = FORMANTS[vowel]
    y = np.zeros(len(x))
    for i, (f, g) in enumerate(zip(F, (1.0, 0.6, 0.28))):
        y += g * bp(x, f * shift, q=f * shift / bw[i])
    return y


def stereo(x, width=0.0, seed=0, pan=0.0):
    """Mono → stereo with optional decorrelation (complementary short comb) and pan."""
    x = np.asarray(x, dtype=np.float64)
    if width > 0:
        d = N(0.009 + 0.004 * (seed % 3))
        dl = np.concatenate([np.zeros(d), x[:-d]])
        L, R = x + width * dl, x - width * dl
    else:
        L, R = x, x
    gl, gr = A.pan_gains(pan)
    return np.stack([L * gl, R * gr], axis=1)


def room(x, wet=0.15, decay=0.6, size=0.25, damping=0.5, predelay=0.008, seed=3):
    xs = A.to_stereo(np.asarray(x, dtype=np.float32))
    y = A.reverb(xs, wet=wet, dry=1.0, keep_tail=False, decay=decay, size=size, damping=damping,
                 predelay=predelay, seed=seed)
    return y.astype(np.float64)


def finish(x, peak_db=-3.0, fin=0.004, fout=0.03, loop=False):
    """DC removal, natural fades (skipped for seamless loops), peak normalisation, stereo float32."""
    x = A.to_stereo(np.asarray(x, dtype=np.float32)).astype(np.float64)
    if loop:
        x = x - x.mean(axis=0)
    else:
        x = A.remove_dc(x, 18).astype(np.float64)
        x = A.fades(x, fin, fout)
    x = A.peak_normalize(x, peak_db)
    return x.astype(np.float32)


def periodic_render(fn, loop_sec, reps=3):
    """Render fn(total_seconds) for `reps` identical loops; return the middle loop (seamless)."""
    y = fn(loop_sec * reps)
    n = N(loop_sec)
    return y[n: 2 * n]


# ============================================================================================
# the sounds


def alarm_bell():
    """Classic electric fire-alarm bell: a solenoid striker at 22 Hz on a steel gong with
    inharmonic partials around 1–5 kHz (split modes beat slowly). 3.0 s, loop-seamless."""
    rate = 22.0
    per = 1.0 / rate
    loop = 3.0
    k_loop = int(round(loop * rate))  # 66 strikes per loop
    r = np.random.default_rng(11)
    jit_t = r.normal(0, 0.0005, k_loop)
    jit_a = 1 + r.normal(0, 0.1, k_loop)
    jit_m = 1 + r.normal(0, 0.18, (k_loop, 8))
    modes = [(1180, 0.50, 0.85), (2405, 1.00, 0.70), (2830, 0.62, 0.55), (3385, 0.75, 0.45),
             (3975, 0.42, 0.36), (4720, 0.22, 0.28), (5590, 0.10, 0.20), (7080, 0.04, 0.12)]

    def render(total):
        n = N(total)
        reps = int(round(total / loop))
        times, amps_by_mode = [], [[] for _ in modes]
        for rp in range(reps):
            for k in range(k_loop):
                times.append(rp * loop + k * per + 0.004 + jit_t[k])
                for m in range(len(modes)):
                    amps_by_mode[m].append(jit_a[k] * jit_m[k, m])
        out = np.zeros(n)
        for m, (f, a, tau) in enumerate(modes):
            exc = impulses(n, times, amps_by_mode[m])
            # split (doublet) modes → slow beating, like a real bell
            out += a * (0.62 * resonator(exc, f, tau) + 0.38 * resonator(exc, f * 1.0021, tau * 0.9))
        # contact damping: the clapper briefly mutes the gong each time it strikes (gives the "rrr")
        tk = np.array(times)
        since = np.full(n, 1.0)
        idx = (tk * SR).astype(int)
        for i0 in idx:
            if 0 <= i0 < n:
                m = min(n, i0 + N(0.03))
                since[i0:m] = np.minimum(since[i0:m], np.arange(m - i0) / SR)
        out *= 1 - 0.72 * np.exp(-since / 0.0065)
        # striker tick + solenoid buzz (mechanical body)
        tick = np.zeros(n)
        nb = N(0.0025)
        tw = bandn(white(nb, 5), 2500, 9000) * np.exp(-np.linspace(0, 6, nb))
        for i0 in idx:
            if 0 <= i0 < n - nb:
                tick[i0:i0 + nb] += tw
        ph = (np.arange(n) / SR) * rate
        buzz = bandn(np.sign(np.sin(2 * np.pi * ph)) * (1 + 0.2 * np.sin(4 * np.pi * ph)), 70, 420)
        y = out / np.max(np.abs(out)) + 0.12 * tick + 0.035 * buzz
        y = lp(y, 7000)
        y = A.high_shelf(y, 4500, -4.0).astype(np.float64)
        y = A.peaking_eq(y, 3300, -2.0, 1.2).astype(np.float64)
        return room(y, wet=0.2, decay=0.7, size=0.3, seed=4)

    y = periodic_render(render, loop)
    return finish(y, loop=True)


def alarm_pull():
    """Pull-station lever: a short plastic scrape, a hard plastic/metal clack, a small latch click."""
    n = N(0.6)
    x = np.zeros(n)
    # scrape (30 ms) leading into the clack
    sc = burst(n, 0.0, 0.05, 21, 900, 6000, shape=0.4, amp=0.18)
    x += sc * smooth_env([(0, 0), (0.02, 1), (0.05, 0.3), (0.06, 0)], n)
    # clack: broadband impulse + plastic housing modes (fast decay) + a low knock
    exc = impulses(n, [0.055], [1.0]) + burst(n, 0.055, 0.004, 22, 800, 10000, amp=0.6)
    x += modal(exc, [(780, 0.6, 0.035), (1460, 0.5, 0.03), (2310, 0.6, 0.022), (3270, 0.35, 0.018),
                     (4890, 0.2, 0.012), (190, 0.5, 0.05)])
    # latch (metal) 85 ms later
    exc2 = impulses(n, [0.14], [0.45]) + burst(n, 0.14, 0.003, 23, 2000, 12000, amp=0.25)
    x += modal(exc2, [(2950, 0.4, 0.03), (4410, 0.35, 0.025), (6230, 0.2, 0.015), (1720, 0.2, 0.03)])
    x = room(x, wet=0.16, decay=0.5, size=0.2, seed=5)
    return finish(x, fout=0.08)


def footsteps():
    """Four soft steps (heel thump + sole scuff), alternating feet, ~0.56 s apart."""
    n = N(2.5)
    out = np.zeros((n, 2))
    for i in range(4):
        t0 = 0.08 + i * 0.56 + 0.012 * math.sin(i * 1.7)
        g = (0.8, 1.0, 0.85, 0.95)[i]
        x = np.zeros(n)
        # heel: low damped thump with slight pitch drop
        m = N(0.12)
        tl = np.arange(m) / SR
        f = 95 * (1 + 0.25 * np.exp(-tl / 0.02)) * (1 + 0.04 * i % 2)
        th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.028) * (1 - np.exp(-tl / 0.002))
        k = N(t0)
        x[k:k + m] += 0.9 * th
        x += burst(n, t0, 0.07, 40 + i, 150, 1600, shape=1.2, amp=0.5)
        # sole roll / scuff
        x += burst(n, t0 + 0.07 + 0.01 * (i % 2), 0.12, 60 + i, 700, 4000, shape=0.9, amp=0.16)
        out += stereo(x * g, pan=-0.12 if i % 2 == 0 else 0.12)
    out = lp(out.T, 5000).T
    out = room(out, wet=0.14, decay=0.5, size=0.25, seed=6)
    return finish(out, fout=0.1)


def door_whoosh():
    """A door swinging past: band-swept noise moving L→R, ending in a soft settle-thud."""
    n = N(1.3)
    t = tt(n)
    src = pink(n, 70)
    env = smooth_env([(0, 0), (0.15, 0.25), (0.45, 1.0), (0.75, 0.55), (1.05, 0.1), (1.3, 0)], n)
    # sweep the band centre up then down (Doppler-ish)
    fc = 250 + 1300 * np.sin(np.pi * np.clip(t / 0.95, 0, 1)) ** 1.5
    frames = 64
    y = np.zeros(n)
    hop = n // frames
    win = np.hanning(2 * hop)
    for i in range(frames):
        a = max(0, i * hop - hop // 2)
        b = min(n, a + 2 * hop)
        seg = src[a:b]
        f = fc[min(n - 1, (a + b) // 2)]
        z = bandn(seg, f * 0.55, f * 1.9)
        y[a:b] += z * win[: b - a]
    y *= env
    thud_exc = impulses(n, [1.0], [0.6])
    thud = modal(thud_exc, [(85, 0.8, 0.05), (160, 0.4, 0.04), (310, 0.2, 0.03)])
    y = y / (np.max(np.abs(y)) + 1e-9) + 0.35 * thud / (np.max(np.abs(thud)) + 1e-9)
    p = np.clip((t - 0.1) / 0.9, 0, 1)
    L = y * np.cos(p * np.pi / 2 * 0.8 + 0.1)
    R = y * np.sin(p * np.pi / 2 * 0.8 + 0.1)
    out = np.stack([L, R], axis=1)
    out = room(out, wet=0.18, decay=0.6, size=0.3, seed=7)
    return finish(out, fin=0.02, fout=0.15)


def crowd_murmur():
    """Soft indistinct worried walla: 8 voices babbling syllables (formant-filtered glottal source +
    breath), rising question-like pitch contours, distant and indistinct. 4.0 s."""
    dur = 4.0
    n = N(dur)
    out = np.zeros((n, 2))
    vowels = list(FORMANTS)
    for v in range(8):
        r = np.random.default_rng(100 + v)
        base = r.uniform(120, 240) if v % 3 else r.uniform(190, 270)
        shift = 1.0 + (base - 160) / 900
        x = np.zeros(n)
        t = r.uniform(0.0, 0.5)
        while t < dur - 0.2:
            nsyl = int(r.integers(3, 8))
            rate = r.uniform(4.2, 6.2)
            phrase_rise = r.uniform(0.05, 0.25)  # worried: phrases drift upward
            for s in range(nsyl):
                sd = 1.0 / rate * r.uniform(0.75, 1.25)
                if t + sd > dur:
                    break
                m = N(sd)
                tl = np.arange(m) / m
                f0 = base * (1 + phrase_rise * s / nsyl + 0.06 * np.sin(np.pi * tl) + r.normal(0, 0.03))
                f0 = np.full(m, 1.0) * f0
                src = glottal(f0, int(r.integers(1e6)), n_harm=18, tilt=1.4)
                src += 0.25 * white(m, int(r.integers(1e6)))
                y = formant(src, vowels[int(r.integers(len(vowels)))], shift)
                e = np.sin(np.pi * tl) ** 1.5 * r.uniform(0.5, 1.0)
                k = N(t)
                x[k:k + m] += (y * e)[: max(0, min(m, n - k))]
                t += sd
            t += r.uniform(0.25, 0.9)
        x = x / (np.max(np.abs(x)) + 1e-9) * r.uniform(0.5, 1.0) * (0.7 if v >= 5 else 1.0)
        pan = -0.8 + 1.6 * (v / 7.0)
        out += stereo(x, pan=pan * 0.8)
    out = lp(out.T, 2600, 2).T  # distance / indistinct
    out = hp(out.T, 140).T
    out *= smooth_env([(0, 0), (0.35, 1), (dur - 0.6, 1), (dur, 0)], n)[:, None]
    out = room(out, wet=0.35, decay=1.1, size=0.5, seed=8)
    return finish(out, fin=0.05, fout=0.3)


def heartbeat():
    """One heartbeat cycle, 1.3 s (loop-seamless): 'lub' (deeper, longer) then 'dub' 0.28 s later."""
    n = N(1.3)
    x = np.zeros(n)

    def thump(at, f0, dec, amp):
        m = N(0.35)
        tl = np.arange(m) / SR
        f = f0 * (1 + 0.6 * np.exp(-tl / 0.015))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR)
        e = np.exp(-tl / dec) * (1 - np.exp(-tl / 0.004))
        k = N(at)
        x[k:k + m] += amp * (s * e)[: max(0, min(m, n - k))]
        x[k:k + m] += amp * 0.25 * (lp(white(m, int(at * 1000)), 220) * e)[: max(0, min(m, n - k))]

    thump(0.06, 52, 0.075, 1.0)
    thump(0.34, 64, 0.055, 0.72)
    # a little soft saturation adds harmonics (audible on phone speakers) without clicks
    x = np.tanh(2.2 * x) / np.tanh(2.2)
    x = lp(x, 900)
    return finish(np.stack([x, x], axis=1), fin=0.002, fout=0.05)


def breath_shaky():
    """A trembling inhale (with two little catches) and a shaky exhale. ~2.9 s."""
    n = N(2.9)
    t = tt(n)
    src = pink(n, 300) * 0.6 + white(n, 301) * 0.4
    inh = bandn(src, 900, 5200) * 0.8 + bp(src, 1500, 3) * 0.6 + bp(src, 2800, 4) * 0.4
    exh = bandn(src, 300, 2600) * 0.9 + bp(src, 700, 2) * 0.5
    trem = 1 + 0.45 * np.sin(2 * np.pi * (7.5 + 1.5 * slow_noise(n, 2, 302)) * t) * (0.6 + 0.4 * slow_noise(n, 3, 303))
    e_in = smooth_env([(0, 0), (0.15, 0.55), (0.42, 0.75), (0.47, 0.12), (0.55, 0.7), (0.82, 0.85), (0.86, 0.15),
                       (0.93, 0.8), (1.2, 0.9), (1.32, 0.0), (2.9, 0)], n)
    e_out = smooth_env([(0, 0), (1.42, 0), (1.55, 0.7), (1.9, 0.55), (2.4, 0.3), (2.85, 0.0), (2.9, 0)], n)
    y = inh * e_in * trem + exh * e_out * (1 + 0.3 * (trem - 1))
    y = A.high_shelf(y, 6000, -6).astype(np.float64)
    out = stereo(y, width=0.15, seed=1)
    out = room(out, wet=0.12, decay=0.45, size=0.18, seed=9)
    return finish(out, fin=0.02, fout=0.2)


def sob():
    """A small soft hitched sob: three catching inhales, a tiny voiced whimper, a trembling exhale."""
    n = N(1.9)
    t = tt(n)
    x = np.zeros(n)
    # hitched inhales (short breathy bursts with rising formant)
    for i, (a, d) in enumerate([(0.05, 0.11), (0.21, 0.09), (0.35, 0.13)]):
        m = N(d)
        b = bandn(pink(m, 400 + i), 1000, 4800) + 0.6 * bp(white(m, 410 + i), 1700 + 300 * i, 4)
        e = np.sin(np.pi * np.linspace(0, 1, m)) ** 0.8 * (0.7 + 0.15 * i)
        k = N(a)
        x[k:k + m] += b * e
    # whimper: voiced, wavering pitch, through an 'u/uh' mouth, very soft
    a0, d0 = 0.56, 0.5
    m = N(d0)
    tl = np.arange(m) / SR
    f0 = 330 * (1 + 0.06 * np.exp(-tl / 0.08)) * (1 - 0.12 * tl / d0) * (1 + 0.018 * np.sin(2 * np.pi * 9 * tl))
    v = glottal(f0, 420, n_harm=14, tilt=1.6) * 0.7 + 0.5 * white(m, 421)
    v = 0.6 * formant(v, "u", 1.15) + 0.4 * formant(v, "uh", 1.15)
    ev = smooth_env([(0, 0), (0.06, 1), (0.3, 0.7), (d0, 0)], m) * (1 + 0.25 * np.sin(2 * np.pi * 8 * tl))
    k = N(a0)
    x[k:k + m] += 0.55 * v * ev / (np.max(np.abs(v)) + 1e-9) * np.max(np.abs(x[:k])) * 1.6
    # trembling exhale
    m = N(0.75)
    tl = np.arange(m) / SR
    ex = bandn(pink(m, 430), 350, 2400) * smooth_env([(0, 0), (0.08, 0.8), (0.4, 0.45), (0.75, 0)], m)
    ex *= 1 + 0.4 * np.sin(2 * np.pi * 7 * tl)
    k = N(1.1)
    x[k:k + m] += 0.8 * ex * np.max(np.abs(x[:k])) / (np.max(np.abs(ex)) + 1e-9)
    out = stereo(x, width=0.12, seed=2)
    out = room(out, wet=0.13, decay=0.5, size=0.2, seed=10)
    return finish(out, fin=0.01, fout=0.15)


def _metal_modes(f0, ratios, seed, amp_tilt=0.85, tau0=1.6, tau_tilt=0.55):
    r = np.random.default_rng(seed)
    modes = []
    for i, q in enumerate(ratios):
        f = f0 * q * (1 + r.normal(0, 0.004))
        modes.append((f, amp_tilt ** i * r.uniform(0.6, 1.0), tau0 * tau_tilt ** (i * 0.5) * r.uniform(0.8, 1.2)))
    return modes


def cage_close():
    """A small metal cage gate swinging shut: impact on several bars (free-free bar modes),
    frame rattle bounces, then the latch. ~2.6 s."""
    n = N(2.6)
    bar = [1.0, 2.756, 5.404, 8.933, 13.34]
    x = np.zeros(n)
    hit = 0.03
    for j, f0 in enumerate([395, 463, 528, 611, 352]):
        exc = impulses(n, [hit + 0.002 * j], [1.0 / (1 + 0.25 * j)])
        x += modal(exc, _metal_modes(f0, bar, 500 + j, tau0=0.5, tau_tilt=0.6))
    # gate plate / frame: denser inharmonic cluster
    exc = impulses(n, [hit], [0.8])
    x += modal(exc, [(611, 0.5, 0.3), (937, 0.6, 0.26), (1283, 0.45, 0.22), (1771, 0.4, 0.17), (2380, 0.3, 0.13),
                     (3170, 0.25, 0.1), (4210, 0.15, 0.07), (182, 0.35, 0.12)])
    x += burst(n, hit, 0.006, 510, 1000, 12000, amp=2.0)
    # rattles: the gate bouncing in its frame (decreasing, quickening)
    rt, ra = [], []
    tcur, gap, amp = hit + 0.07, 0.065, 0.5
    for i in range(7):
        rt.append(tcur)
        ra.append(amp)
        tcur += gap
        gap *= 0.78
        amp *= 0.62
    exc = impulses(n, rt, ra)
    x += modal(exc, [(1490, 0.6, 0.05), (2210, 0.5, 0.04), (3330, 0.4, 0.03), (5120, 0.2, 0.02), (410, 0.4, 0.06)])
    for i, (tk, ak) in enumerate(zip(rt, ra)):
        x += burst(n, tk, 0.003, 520 + i, 2000, 9000, amp=ak * 0.8)
    # latch catch
    exc = impulses(n, [hit + 0.42], [0.35])
    x += modal(exc, [(2650, 0.5, 0.04), (3980, 0.4, 0.03), (5400, 0.2, 0.02), (980, 0.3, 0.05)])
    x = A.high_shelf(x, 5000, -3).astype(np.float64)
    out = stereo(x, width=0.2, seed=3)
    out = room(out, wet=0.22, decay=1.0, size=0.45, seed=11)
    return finish(out, fout=0.3)


def lock_click():
    """A latch/padlock click: two spring clicks 38 ms apart with a small body knock. ~0.3 s."""
    n = N(0.32)
    x = np.zeros(n)
    for at, a, sd in [(0.02, 1.0, 600), (0.058, 0.7, 601)]:
        exc = impulses(n, [at], [a])
        x += modal(exc, [(2480, 0.5, 0.025), (3710, 0.6, 0.02), (5230, 0.35, 0.015), (7120, 0.15, 0.01),
                         (430, 0.35, 0.03)])
        x += burst(n, at, 0.002, sd, 3000, 14000, amp=a * 1.2)
    x = room(x, wet=0.12, decay=0.4, size=0.15, seed=12)
    return finish(x, fout=0.05)


def _stick_slip(n, f_contour, amp_env, seed, jitter=0.08, grit=0.0, drop=0.0):
    """Excitation for friction sounds: a pulse train whose instantaneous rate follows f_contour,
    with timing/amplitude jitter; optional 'grit' (random extra micro-slips) and dropouts."""
    r = np.random.default_rng(seed)
    x = np.zeros(n)
    ph = 0.0
    i = 0
    pulse = np.array([1.0, 0.55, -0.35, -0.45, -0.2])
    while i < n - 8:
        f = max(5.0, f_contour[i])
        ph += f / SR
        if ph >= 1.0:
            ph -= 1.0 + r.normal(0, jitter)
            if r.random() >= drop:
                a = amp_env[i] * (1 + r.normal(0, 0.25))
                x[i:i + 5] += a * pulse
                if grit and r.random() < grit:
                    j = i + int(r.integers(10, 60))
                    if j < n - 5:
                        x[j:j + 5] += 0.5 * a * pulse * r.uniform(-1, 1)
        i += 1
    return x


def cage_creak():
    """Slow hinge creak: stick-slip pulses gliding 70→180→110 Hz through hinge/gate resonances. ~2.2 s."""
    n = N(2.2)
    t = tt(n)
    f = 70 + 110 * np.sin(np.pi * np.clip(t / 1.6, 0, 1)) ** 1.2 + 40 * np.clip((t - 1.6) / 0.6, 0, 1)
    f *= 1 + 0.06 * slow_noise(n, 6, 700)
    env = smooth_env([(0, 0), (0.15, 0.6), (0.7, 1.0), (1.4, 0.8), (1.9, 0.5), (2.2, 0)], n)
    exc = _stick_slip(n, f, env, 701, jitter=0.06, grit=0.15)
    y = modal(exc, [(520, 0.6, 0.03), (870, 0.8, 0.025), (1410, 1.0, 0.02), (2240, 0.6, 0.015),
                    (3150, 0.3, 0.01)])
    y += 0.05 * bandn(white(n, 702), 1500, 5000) * env
    y = hp(y, 150)
    out = stereo(y, width=0.15, seed=4)
    out = room(out, wet=0.2, decay=0.9, size=0.4, seed=13)
    return finish(out, fin=0.03, fout=0.2)


def key_turn():
    """Key slides in (pin ticks over a scrape), turns (short grind), and the bolt clunks. ~0.95 s."""
    n = N(0.95)
    x = np.zeros(n)
    sc = bandn(white(n, 800), 2500, 9000) * smooth_env([(0, 0), (0.03, 0.3), (0.2, 0.25), (0.24, 0), (0.95, 0)], n)
    x += 0.35 * sc
    ticks = [0.05, 0.085, 0.115, 0.15, 0.18, 0.205]
    exc = impulses(n, ticks, [0.25, 0.3, 0.22, 0.3, 0.25, 0.35])
    x += modal(exc, [(3820, 0.5, 0.012), (5260, 0.4, 0.01), (6900, 0.2, 0.008)])
    # turn: gritty grind
    gr = _stick_slip(n, np.full(n, 140.0), smooth_env([(0, 0), (0.42, 0), (0.48, 0.5), (0.62, 0.6), (0.66, 0), (0.95, 0)], n),
                     801, jitter=0.2, grit=0.4)
    x += 0.6 * modal(gr, [(1830, 0.5, 0.008), (2970, 0.5, 0.006), (4400, 0.3, 0.005)])
    # bolt clunk
    exc = impulses(n, [0.68], [1.0])
    x += modal(exc, [(380, 0.6, 0.05), (1120, 0.5, 0.04), (2650, 0.4, 0.03), (4100, 0.25, 0.02)])
    x += burst(n, 0.68, 0.003, 802, 1500, 10000, amp=0.8)
    x = room(x, wet=0.12, decay=0.45, size=0.18, seed=14)
    return finish(x, fout=0.08)


def rumble_low():
    """Sub-bass swell: a 41 Hz tone with slow wobble + low brown noise, rising 2.6 s then fading. ~5 s."""
    n = N(5.0)
    t = tt(n)
    f = 41 * (1 + 0.02 * np.sin(2 * np.pi * 0.37 * t))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    nz = lp(brown(n, 900), 110, 4)
    y = 0.8 * tone + 0.9 * nz / (np.std(nz) + 1e-9) * 0.35
    env = smooth_env([(0, 0), (2.6, 1.0), (3.4, 0.85), (5.0, 0)], n)
    y = y * env
    # gentle harmonics so it reads on small speakers
    y = np.tanh(1.6 * y / (np.max(np.abs(y)) + 1e-9)) * 0.9
    y = lp(y, 260, 2)
    out = stereo(y, width=0.25, seed=5)
    return finish(out, fin=0.05, fout=0.3)


def _celesta_note(freq, dur, amp=1.0):
    m = N(dur)
    tl = np.arange(m) / SR
    s = (np.sin(2 * np.pi * freq * tl) * np.exp(-tl / 0.9)
         + 0.28 * np.sin(2 * np.pi * freq * 4.02 * tl) * np.exp(-tl / 0.18)
         + 0.08 * np.sin(2 * np.pi * freq * 9.8 * tl) * np.exp(-tl / 0.05))
    s *= 1 - np.exp(-tl / 0.0015)
    return amp * s


def midi_hz(k):
    return 440.0 * 2 ** ((k - 69) / 12)


def shimmer():
    """Bowed-glass + celesta sparkle wash in D lydian: sustained glass cluster swelling in and out,
    with sparkles growing denser then thinning. 3.0 s (+ tail inside)."""
    dur = 3.0
    n = N(dur)
    t = tt(n)
    y = np.zeros(n)
    # bowed glass: pure partials with slow vibrato/beating, soft bowing noise
    for k, a in [(81, 0.5), (85, 0.4), (88, 0.35), (92, 0.25), (93, 0.18)]:  # A5 C#6 E6 G#6 A6
        f = midi_hz(k) * (1 + 0.0025 * np.sin(2 * np.pi * (4.5 + k % 3) * t + k))
        y += a * np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * t + k))
    y *= smooth_env([(0, 0), (1.0, 0.6), (1.8, 0.7), (3.0, 0)], n)
    y += 0.03 * bandn(white(n, 950), 3000, 9000) * smooth_env([(0, 0), (1.0, 1), (3.0, 0)], n)
    # sparkles
    r = np.random.default_rng(951)
    scale = [74, 76, 78, 80, 81, 83, 85, 86, 88, 90, 92, 93, 95, 97, 98]  # D lydian, upper octaves
    sp = np.zeros((n, 2))
    tcur = 0.12
    while tcur < dur - 0.4:
        dens = 0.08 + 0.12 * (1 - abs(tcur / dur - 0.45) * 1.6)
        k = scale[int(r.integers(len(scale)))]
        note = _celesta_note(midi_hz(k), min(1.2, dur - tcur), amp=r.uniform(0.15, 0.4))
        m = len(note)
        a = N(tcur)
        gl, gr = A.pan_gains(r.uniform(-0.8, 0.8))
        sp[a:a + m, 0] += note[: n - a] * gl
        sp[a:a + m, 1] += note[: n - a] * gr
        tcur += max(0.04, r.exponential(dens))
    out = stereo(y, width=0.3, seed=6) + sp
    out = room(out, wet=0.45, decay=2.2, size=0.8, damping=0.4, seed=15)
    out *= smooth_env([(0, 1), (dur - 0.5, 1), (dur, 0)], n)[:, None]
    return finish(out, fin=0.05, fout=0.3)


def twinkle():
    """Three celesta notes (A6, E7, F#6 — bright, from the score's D major/lydian). ~1.9 s."""
    n = N(1.9)
    out = np.zeros((n, 2))
    for at, k, a, p in [(0.02, 93, 0.9, 0.25), (0.2, 100, 0.65, 0.35), (0.42, 90, 0.75, 0.15)]:
        note = _celesta_note(midi_hz(k), 1.9 - at, a)
        m = N(at)
        gl, gr = A.pan_gains(p)
        out[m:m + len(note), 0] += note[: n - m] * gl
        out[m:m + len(note), 1] += note[: n - m] * gr
    out = room(out, wet=0.35, decay=1.6, size=0.6, damping=0.4, seed=16)
    return finish(out, fout=0.25)


def console_beeps():
    """Soft friendly UI blips: three rounded sine/triangle blips rising E6 → A6 → C#7, then a lower answer."""
    n = N(1.0)
    x = np.zeros(n)
    for at, k, d, a in [(0.02, 88, 0.075, 0.8), (0.13, 93, 0.075, 0.7), (0.24, 97, 0.12, 0.75), (0.48, 90, 0.16, 0.5)]:
        m = N(d + 0.15)
        tl = np.arange(m) / SR
        f = midi_hz(k)
        tri = signal.sawtooth(2 * np.pi * f * tl, 0.5)
        s = 0.7 * np.sin(2 * np.pi * f * tl) + 0.3 * lp(tri, 4000)
        e = (1 - np.exp(-tl / 0.004)) * np.where(tl < d, 1.0, np.exp(-(tl - d) / 0.03))
        k0 = N(at)
        x[k0:k0 + m] += a * (s * e)[: max(0, min(m, n - k0))]
    out = stereo(x, width=0.1, seed=7)
    out = room(out, wet=0.18, decay=0.5, size=0.2, seed=17)
    return finish(out, fout=0.08)


def paper_rustle():
    """Handling and turning an old notebook page: crinkle micro-clicks over a soft swish. ~1.1 s."""
    n = N(1.1)
    t = tt(n)
    env = smooth_env([(0, 0), (0.1, 0.35), (0.3, 0.6), (0.5, 1.0), (0.68, 0.45), (0.85, 0.2), (1.1, 0)], n)
    sw = bandn(pink(n, 1000), 900, 7000) * env * 0.5
    r = np.random.default_rng(1001)
    cr = np.zeros(n)
    i = 0
    while i < n - 200:
        rate = 30 + 400 * env[i]
        i += int(SR / rate * r.exponential(1.0)) + 1
        if i >= n - 200:
            break
        m = int(r.integers(30, 160))
        cr[i:i + m] += r.normal(0, 1, m) * np.exp(-np.arange(m) / (m / 4)) * r.uniform(0.2, 1.0) * env[i]
    cr = bandn(cr, 1500, 10000)
    y = 0.7 * sw + 1.3 * cr / (np.max(np.abs(cr)) + 1e-9) * np.max(np.abs(sw))
    out = stereo(y, width=0.25, seed=8)
    out = room(out, wet=0.1, decay=0.4, size=0.15, seed=18)
    return finish(out, fin=0.01, fout=0.12)


def lamp_click():
    """A desk-lamp switch: a firm plastic click (press) and a softer, higher release tick 90 ms later."""
    n = N(0.3)
    x = np.zeros(n)
    for at, a, modes, sd in [(0.02, 1.0, [(1650, 0.6, 0.02), (2900, 0.6, 0.015), (4300, 0.3, 0.01), (620, 0.3, 0.025)], 1100),
                             (0.11, 0.45, [(2300, 0.5, 0.012), (3800, 0.5, 0.01), (5600, 0.2, 0.008)], 1101)]:
        exc = impulses(n, [at], [a])
        x += modal(exc, modes)
        x += burst(n, at, 0.0015, sd, 2000, 14000, amp=a)
    x = room(x, wet=0.12, decay=0.35, size=0.12, seed=19)
    return finish(x, fout=0.04)


def cloth_rustle():
    """Soft fabric movement: overlapping swishes of shaped noise with fibre-grain flutter. ~1.0 s."""
    n = N(1.0)
    y = np.zeros(n)
    for i, (a, d, lo, hi, g) in enumerate([(0.0, 0.6, 350, 3000, 1.0), (0.28, 0.5, 500, 3800, 0.7),
                                           (0.5, 0.48, 300, 2600, 0.6)]):
        m = N(d)
        s = bandn(pink(m, 1200 + i), lo, hi)
        s *= 1 + 0.5 * slow_noise(m, 25, 1210 + i)  # grain
        e = np.sin(np.pi * np.linspace(0, 1, m)) ** 1.6
        k = N(a)
        y[k:k + m] += g * (s * e)[: max(0, min(m, n - k))]
    y = A.high_shelf(lp(y, 4200), 2500, -4).astype(np.float64)
    out = stereo(y, width=0.3, seed=9)
    out = room(out, wet=0.08, decay=0.35, size=0.12, seed=20)
    return finish(out, fin=0.02, fout=0.15)


def rust_creak():
    """A rusty gate creak: grainier, higher, more broken stick-slip (rough rate, dropouts, grit). ~1.7 s."""
    n = N(1.7)
    t = tt(n)
    f = 160 + 140 * np.sin(np.pi * np.clip(t / 1.3, 0, 1)) + 60 * slow_noise(n, 9, 1300)
    env = smooth_env([(0, 0), (0.1, 0.5), (0.5, 1.0), (1.0, 0.7), (1.45, 0.4), (1.7, 0)], n)
    exc = _stick_slip(n, f, env, 1301, jitter=0.18, grit=0.5, drop=0.12)
    y = modal(exc, [(1180, 0.7, 0.02), (2050, 1.0, 0.016), (3370, 0.7, 0.012), (4620, 0.35, 0.008),
                    (760, 0.3, 0.02)])
    y += 0.12 * bandn(white(n, 1302), 2000, 7000) * env * (1 + slow_noise(n, 40, 1303))
    y = hp(y, 300)
    y = A.high_shelf(y, 6000, -4).astype(np.float64)
    out = stereo(y, width=0.15, seed=10)
    out = room(out, wet=0.18, decay=0.8, size=0.35, seed=21)
    return finish(out, fin=0.02, fout=0.2)


SFX = {
    "alarm_bell": alarm_bell, "alarm_pull": alarm_pull, "footsteps": footsteps, "door_whoosh": door_whoosh,
    "crowd_murmur": crowd_murmur, "heartbeat": heartbeat, "breath_shaky": breath_shaky, "sob": sob,
    "cage_close": cage_close, "lock_click": lock_click, "cage_creak": cage_creak, "key_turn": key_turn,
    "rumble_low": rumble_low, "shimmer": shimmer, "twinkle": twinkle, "console_beeps": console_beeps,
    "paper_rustle": paper_rustle, "lamp_click": lamp_click, "cloth_rustle": cloth_rustle, "rust_creak": rust_creak,
}
LOOPS = {"alarm_bell", "heartbeat"}


def main():
    args = sys.argv[1:]
    spectro = None
    if "--list" in args:
        for k, f in SFX.items():
            print(f"{k:14s} {f.__doc__.strip().splitlines()[0]}")
        return
    if "--spectro" in args:
        i = args.index("--spectro")
        spectro = args[i + 1]
        del args[i:i + 2]
    names = args or list(SFX)
    os.makedirs(OUT, exist_ok=True)
    for nm in names:
        x = SFX[nm]()
        p = A.save(os.path.join(OUT, nm + ".wav"), x)
        h = A.analyze(x)
        seam = ""
        if nm in LOOPS:
            seam = f" seam_jump={float(np.max(np.abs(x[0] - x[-1]))):.4f}"
        print(f"{nm:14s} {h['seconds']:5.2f}s peak {h['peak_db']:6.2f} tp {h['true_peak_db']:6.2f} "
              f"rms {h['rms_db']:6.1f} dc {h['dc']:.5f} jump {h['max_jump']:.3f} click {h['click_score']:5.1f}"
              f" ends {h['start_abs']:.4f}/{h['end_abs']:.4f}{seam}")
        if spectro:
            A.spectrogram_png(x, os.path.join(spectro, f"spectro_sfx_{nm}.png"), max_hz=12000,
                              width=900, height=320, title=f"{nm}.wav  {h['seconds']}s")


if __name__ == "__main__":
    main()
