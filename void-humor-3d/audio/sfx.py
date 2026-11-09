#!/usr/bin/env python3
"""sfx.py — synthesise every sound effect of the film into audio/sfx/<name>.wav (+ variants) and the two
ambience beds, plus audio/sfx/meta.json (durations, sync points, variants, loopability, design levels).

    python3 audio/sfx.py                    # everything (~20 s)
    python3 audio/sfx.py kick_thump crash_buckets      # some
    python3 audio/sfx.py --list             # names + one-line descriptions
    python3 audio/sfx.py --spectro out/sfx_spectro     # also write a spectrogram PNG per file

Vocabulary = data/SCREENPLAY_FORMAT.md; ambience beds: amb_edge (THE_EDGE dusk air + distant chimes),
amb_backroom (MIND_BACKROOM room tone + distant hum + far drips). Everything is procedural and deterministic
(fixed seeds): modal synthesis (struck metal/wood/glass), stick-slip resonators (creaks), shaped noise
(whooshes, cloth, wind), pitch-swept sines (pops, gulps, slide whistle), additive bells. Building blocks are
adapted from the creator's earlier film's sfx.py.

Files are stereo 44.1 kHz PCM16, DC-free, faded, and loudness-designed: each one-shot's *momentary-max*
loudness (400 ms window) is set to its `lufs` design level in SFX (beds: integrated), so an event with
`gain_db: 0` already sits at a sensible level against dialogue at about -18 LUFS. True peaks stay below -1 dBFS.
`sync` (meta.json) = where the audible hit sits inside the file: collect_sfx/mix place the file at t - sync,
so an event's `t` is the moment the sound LANDS (the kick, the crash, the first footfall).
Tonal SFX (twinkle, shimmer, star_pop, sparkle_appear, nebula_swell, ding, birdies) use only D, E and A, which
sit consonantly in both of the score's home keys (F major for Part One, D major/minor for Part Two).
"""
import json
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


def periodic_noise(n, seed, slope=0.5, lo=20.0, hi=20000.0):
    """Perfectly periodic (loop-seamless) coloured noise of length n: random phases, |X| ~ f^-slope."""
    r = np.random.default_rng(seed)
    f = np.fft.rfftfreq(n, 1 / SR)
    mag = np.where((f >= lo) & (f <= hi), 1.0 / np.maximum(f, 1.0) ** slope, 0.0)
    X = mag * np.exp(1j * r.uniform(0, 2 * np.pi, len(f)))
    x = np.fft.irfft(X, n)
    return x / (np.std(x) + 1e-12)


def bp(x, f, q=4.0):
    """RBJ constant-0-dB-peak band-pass."""
    w0 = 2 * np.pi * min(f, SR * 0.45) / SR
    al = np.sin(w0) / (2 * q)
    return signal.lfilter([al, 0, -al], [1 + al, -2 * np.cos(w0), 1 - al], x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, min(f, SR * 0.45), "lowpass", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x, axis=0)


def bandn(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR * 0.45)], "bandpass", fs=SR, output="sos"), x, axis=0)


def resonator(exc, f, tau):
    """2-pole resonator: an impulse of height 1 rings as sin(2πft)·e^(−t/τ)."""
    r = math.exp(-1.0 / (tau * SR))
    w = 2 * math.pi * f / SR
    return signal.lfilter([math.sin(w)], [1, -2 * r * math.cos(w), r * r], exc)


def modal(exc, modes):
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


def soft_exc(n, at, ms=2.0, amp=1.0):
    """A raised-cosine push (softer than an impulse: rounder, less clicky attack)."""
    x = np.zeros(n)
    q = max(2, N(ms / 1000))
    k = N(at)
    seg = amp * (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(q) / q))
    x[k:k + q] += seg[: max(0, min(q, n - k))]
    return x


def burst(n, at, dur, seed, lo=500, hi=8000, shape=2.0, amp=1.0):
    m = N(dur)
    e = np.exp(-np.linspace(0, shape * 3, m))
    e[: max(1, N(0.0008))] *= np.linspace(0, 1, max(1, N(0.0008)))
    b = bandn(white(m, seed), lo, hi) * e * amp
    x = np.zeros(n)
    k = N(at)
    x[k:k + m] += b[: max(0, min(m, n - k))]
    return x


def sweep_tone(n, at, f0, f1, dur, tau=None, amp=1.0, curve=1.0, harm=0.0):
    """A sine whose pitch glides f0→f1 over dur (exponential glide), decaying with tau (or held)."""
    m = N(dur)
    tl = np.arange(m) / SR
    p = (tl / max(dur, 1e-6)) ** curve
    f = f0 * (f1 / f0) ** p
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + harm * np.sin(2 * ph)
    e = np.exp(-tl / tau) if tau else np.ones(m)
    e *= 1 - np.exp(-tl / 0.0015)
    nf = min(m, N(0.01))
    e[m - nf:] *= np.linspace(1, 0, nf)
    x = np.zeros(n)
    k = N(at)
    x[k:k + m] += (amp * s * e)[: max(0, min(m, n - k))]
    return x


def smooth_env(points, n):
    ts = np.array([p[0] for p in points]) * SR
    vs = np.array([p[1] for p in points])
    i = np.arange(n)
    idx = np.clip(np.searchsorted(ts, i, side="right") - 1, 0, len(ts) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    f = np.clip((i - t0) / np.maximum(t1 - t0, 1), 0, 1)
    f = 0.5 - 0.5 * np.cos(np.pi * f)
    return vs[idx] + (vs[idx + 1] - vs[idx]) * f


def slow_noise(n, rate_hz, seed):
    k = max(4, int(n / SR * rate_hz) + 4)
    pts = np.random.default_rng(seed).uniform(-1, 1, k)
    x = np.interp(np.linspace(0, k - 3, n), np.arange(k), pts)
    return lp(x, max(rate_hz * 1.5, 0.5), 1) if n > 32 else x


def stereo(x, width=0.0, seed=0, pan=0.0, circular=False):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 2:
        return x
    if width > 0:
        d = N(0.009 + 0.004 * (seed % 3))
        dl = np.roll(x, d) if circular else np.concatenate([np.zeros(d), x[:-d]])
        L, R = x + width * dl, x - width * dl
    else:
        L, R = x, x
    gl, gr = A.pan_gains(pan)
    return np.stack([L * gl, R * gr], axis=1)


def add_st(out, x, at, pan=0.0):
    """Add mono x into stereo out at time `at` with equal-power pan."""
    gl, gr = A.pan_gains(pan)
    k = N(at)
    m = max(0, min(len(x), len(out) - k))
    out[k:k + m, 0] += x[:m] * gl
    out[k:k + m, 1] += x[:m] * gr
    return out


def room(x, wet=0.15, decay=0.6, size=0.25, damping=0.5, predelay=0.008, seed=3):
    xs = A.to_stereo(np.asarray(x, dtype=np.float32))
    return A.reverb(xs, wet=wet, dry=1.0, keep_tail=False, decay=decay, size=size, damping=damping,
                    predelay=predelay, seed=seed).astype(np.float64)


def midi_hz(k):
    return 440.0 * 2 ** ((k - 69) / 12)


def bell_note(freq, dur, amp=1.0, bright=1.0, tau=0.9):
    """Celesta/glock-like struck bar: fundamental + 4.0x and 9.8x partials (short), soft mallet."""
    m = N(dur)
    tl = np.arange(m) / SR
    s = (np.sin(2 * np.pi * freq * tl) * np.exp(-tl / tau)
         + 0.28 * bright * np.sin(2 * np.pi * freq * 4.02 * tl) * np.exp(-tl / (tau * 0.2))
         + 0.08 * bright * np.sin(2 * np.pi * freq * 9.8 * tl) * np.exp(-tl / (tau * 0.055)))
    s *= 1 - np.exp(-tl / 0.0015)
    nf = min(m, N(0.03))
    s[m - nf:] *= np.linspace(1, 0, nf)  # never stop a ringing bar abruptly
    return amp * s


# pitch set shared by every tonal SFX: D, E, A (consonant in F major and in D major/minor)
DEA = [62, 64, 69, 74, 76, 81, 86, 88, 93, 98, 100, 105]


def momentary_max(x):
    """Max BS.1770 momentary loudness (400 ms windows, 100 ms hop) — the 'how loud does it hit' measure."""
    xs = A.to_stereo(x).astype(np.float64)
    if len(xs) < N(0.4):
        xs = np.concatenate([xs, np.zeros((N(0.4) - len(xs), 2))])
    sos = A._k_weighting_sos(SR)
    p = np.zeros(len(xs))
    for c in range(2):
        y = signal.sosfilt(sos, xs[:, c])
        p += y * y
    cs = np.concatenate([[0.0], np.cumsum(p)])
    blk, step = N(0.4), N(0.05)
    st = np.arange(0, len(p) - blk + 1, step)
    z = (cs[st + blk] - cs[st]) / blk
    return float(-0.691 + 10 * np.log10(z.max() + 1e-20))


def finish(x, fin=0.004, fout=0.03, loop=False):
    x = A.to_stereo(np.asarray(x, dtype=np.float32)).astype(np.float64)
    if loop:
        x = x - x.mean(axis=0)
    else:
        x = A.remove_dc(x, 18).astype(np.float64)
        x = A.fades(x, fin, fout)
    return x.astype(np.float32)


def level(x, lufs, bed=False, tp_max=-1.0):
    """Scale to the design loudness (momentary max, or integrated for beds); keep true peak ≤ tp_max."""
    L = A.loudness(x) if bed else momentary_max(x)
    if np.isfinite(L):
        x = x * float(A.db2lin(lufs - L))
    tp = A.true_peak(x)
    if tp > tp_max:
        x = x * float(A.db2lin(tp_max - tp))
    return x.astype(np.float32)


def periodic_reverb(x, wet=0.3, **kw):
    """Reverb for a loop: circular convolution (the tail wraps into the head) so the loop stays seamless."""
    xs = A.to_stereo(np.asarray(x, dtype=np.float32)).astype(np.float64)
    n = len(xs)
    ir = A.make_reverb_ir(**kw)
    out = xs.copy()
    for o in range(2):
        acc = np.zeros(n)
        for i in range(2):
            h = np.zeros(n)
            m = min(n, len(ir))
            h[:m] = ir[:m, i, o]
            acc += np.fft.irfft(np.fft.rfft(xs[:, i]) * np.fft.rfft(h), n)
        out[:, o] += wet * acc
    return out


# ============================================================================================
# footsteps (files are whole cycles: n_steps × interval, so variants butt-join with a steady cadence)


def _step(n, t0, seed, heel_f=95, heel_amp=0.85, crunch=0.5, scuff=0.28, knock=0.8, pan=0.0, grass=True):
    x = np.zeros(n)
    m = N(0.13)
    tl = np.arange(m) / SR
    f = heel_f * (1 + 0.25 * np.exp(-tl / 0.02))
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.03) * (1 - np.exp(-tl / 0.002))
    th_h = bandn(np.tanh(4.0 * th), 170, 700)
    k = N(t0)
    seg = heel_amp * th + 0.55 * th_h / (np.max(np.abs(th_h)) + 1e-9)
    x[k:k + m] += seg[: max(0, min(m, n - k))]
    if knock:
        exc = np.zeros(m)
        q = N(0.003)
        exc[:q] = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(q) / q)
        kn = modal(exc, [(190 + 13 * (seed % 3), 1.0, 0.022), (310, 0.7, 0.016), (480, 0.4, 0.011)])
        x[k:k + m] += (knock * kn / (np.max(np.abs(kn)) + 1e-9))[: max(0, min(m, n - k))]
    if grass:  # crackly grass/dirt crunch: a burst of micro-clicks through a 1-5 kHz band
        r = np.random.default_rng(seed)
        cr = np.zeros(n)
        for j in range(14):
            at = t0 + 0.004 + r.exponential(0.025)
            kk = N(at)
            ln = int(r.integers(20, 120))
            if kk + ln < n:
                cr[kk:kk + ln] += r.normal(0, 1, ln) * np.exp(-np.arange(ln) / (ln / 4)) * r.uniform(0.2, 1.0)
        x += crunch * bandn(cr, 900, 5200) * 0.6
    x += burst(n, t0 + 0.06, 0.12, seed + 7, 600, 3800, shape=0.9, amp=scuff)
    return stereo(np.tanh(1.3 * x) / 1.3, pan=pan)


def footsteps_soft(v=1):
    """Unhurried soft steps on a grassy dusk path: 4 steps, 0.55 s apart (2.2 s cycle)."""
    iv, ns = 0.55, 4
    n = N(iv * ns)
    out = np.zeros((n, 2))
    for i in range(ns):
        g = (0.8, 1.0, 0.86, 0.94)[(i + v) % 4]
        out += g * _step(n, 0.03 + i * iv + 0.012 * math.sin(i * 1.7 + v), 100 * v + i, heel_f=92 + 4 * v,
                         crunch=0.45, scuff=0.22, pan=-0.1 if i % 2 == 0 else 0.1)
    out = lp(out, 5200)
    out = room(out, wet=0.1, decay=0.45, size=0.2, seed=6)
    return finish(out, fout=0.06)


def footsteps_run(v=1):
    """Quick light sneaker patter (running away): 8 steps, 0.17 s apart (1.36 s cycle)."""
    iv, ns = 0.17, 8
    n = N(iv * ns)
    out = np.zeros((n, 2))
    r = np.random.default_rng(300 + v)
    for i in range(ns):
        g = (1.0 if i % 2 == 0 else 0.82) * r.uniform(0.85, 1.0)
        out += g * _step(n, 0.02 + i * iv + r.normal(0, 0.004), 300 + 10 * v + i, heel_f=118, heel_amp=0.6,
                         crunch=0.55, scuff=0.18, knock=0.6, pan=-0.14 if i % 2 == 0 else 0.14)
    # cloth swish of the hoodie on every other stride
    for i in range(0, ns, 2):
        out += stereo(0.08 * burst(n, 0.06 + i * iv, 0.16, 360 + i + v, 400, 3000, shape=0.7))
    out = lp(out, 5500)
    out = room(out, wet=0.08, decay=0.4, size=0.2, seed=7)
    return finish(out, fout=0.03)


def footsteps_stomp(v=1):
    """Comic stomps (storming off / the Void's fat feet): 3 heavy steps 0.5 s apart, low 'thoomp' + dust."""
    iv, ns = 0.5, 3
    n = N(iv * ns)
    out = np.zeros((n, 2))
    for i in range(ns):
        t0 = 0.02 + i * iv
        x = np.zeros(n)
        m = N(0.25)
        tl = np.arange(m) / SR
        f = (66 + 6 * v) * (1 + 0.6 * np.exp(-tl / 0.025))
        th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.07) * (1 - np.exp(-tl / 0.003))
        sat = bandn(np.tanh(5 * th), 160, 900)
        k = N(t0)
        x[k:k + m] += th + 0.45 * sat / (np.max(np.abs(sat)) + 1e-9)
        exc = soft_exc(n, t0, 4.0)
        x += 0.5 * modal(exc, [(140, 1.0, 0.05), (230, 0.6, 0.035), (370, 0.35, 0.02)]) / 3
        x += burst(n, t0 + 0.01, 0.2, 400 + i + 10 * v, 300, 2500, shape=0.8, amp=0.22)  # dust puff
        out += stereo(np.tanh(1.2 * x), pan=-0.08 if i % 2 == 0 else 0.08) * (1.0, 0.9, 0.96)[i]
    out = lp(out, 4500)
    out = room(out, wet=0.12, decay=0.55, size=0.3, seed=8)
    return finish(out, fout=0.05)


# ============================================================================================
# one-shots


def sparkle_appear():
    """Magical arrival: airy swell + a rising glassy arpeggio that blooms into a soft bell chord at 0.55 s."""
    n = N(2.4)
    out = np.zeros((n, 2))
    air = bandn(pink(n, 501), 2500, 11000) * smooth_env([(0, 0), (0.5, 0.5), (0.7, 0.25), (2.4, 0)], n)
    out += stereo(0.18 * air, width=0.4, seed=1)
    seq = [69, 74, 76, 81, 86, 88, 93]
    for j, k in enumerate(seq):
        at = 0.08 + j * 0.065
        out = add_st(out, bell_note(midi_hz(k), 1.4, 0.22 + 0.05 * j, bright=0.7), at, pan=-0.6 + 0.2 * j)
    for k, a, p in [(86, 0.6, -0.2), (93, 0.5, 0.25), (100, 0.32, 0.0), (81, 0.45, 0.1)]:
        out = add_st(out, bell_note(midi_hz(k), 1.8, a, bright=0.5, tau=1.1), 0.55, pan=p)
    t = tt(n)
    gl = sum(a * np.sin(2 * np.pi * midi_hz(k) * t * (1 + 0.002 * np.sin(2 * np.pi * 5 * t + k)))
             for k, a in [(81, 0.3), (88, 0.25), (93, 0.2)])
    out += stereo(0.25 * gl * smooth_env([(0, 0), (0.55, 0.8), (1.0, 0.5), (2.4, 0)], n), width=0.3, seed=2)
    out = room(out, wet=0.4, decay=1.8, size=0.7, damping=0.4, seed=15)
    return finish(out, fin=0.02, fout=0.4)


def thud_sit():
    """Plopping down on one's backside in the grass: a soft 'bump-bump' (thump + tiny bounce) + grass crunch."""
    n = N(0.7)
    x = np.zeros(n)
    for at, a, f0 in [(0.01, 1.0, 88), (0.12, 0.38, 104)]:
        m = N(0.2)
        tl = np.arange(m) / SR
        f = f0 * (1 + 0.5 * np.exp(-tl / 0.02))
        th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.05) * (1 - np.exp(-tl / 0.003))
        k = N(at)
        x[k:k + m] += a * (th + 0.4 * bandn(np.tanh(4 * th), 180, 800))
    x += burst(n, 0.012, 0.15, 520, 500, 4000, shape=1.0, amp=0.25)
    x += _step(n, 0.012, 521, heel_amp=0.0, crunch=0.8, scuff=0.0, knock=0.0)[:, 0] * 0.6
    out = stereo(np.tanh(1.2 * x), width=0.1, seed=3)
    out = room(out, wet=0.08, decay=0.4, size=0.2, seed=9)
    return finish(out, fout=0.1)


def cloth_rustle(v=1):
    """Soft fabric movement (robe, hoodie, velvet sleeve): overlapping swishes with fibre-grain flutter."""
    n = N(1.0)
    y = np.zeros(n)
    sets = {1: [(0.0, 0.6, 350, 3000, 1.0), (0.28, 0.5, 500, 3800, 0.7), (0.5, 0.48, 300, 2600, 0.6)],
            2: [(0.0, 0.45, 400, 3400, 0.9), (0.2, 0.62, 300, 2800, 1.0)],
            3: [(0.0, 0.35, 450, 3600, 0.8), (0.15, 0.4, 350, 3000, 0.7), (0.42, 0.5, 300, 2500, 0.9)]}[v]
    for i, (a, d, lo, hi, g) in enumerate(sets):
        m = N(d)
        s = bandn(pink(m, 1200 + i + 10 * v), lo, hi)
        s *= 1 + 0.5 * slow_noise(m, 25, 1210 + i + 10 * v)
        e = np.sin(np.pi * np.linspace(0, 1, m)) ** 1.6
        k = N(a)
        y[k:k + m] += g * (s * e)[: max(0, min(m, n - k))]
    y = A.high_shelf(lp(y, 4200), 2500, -4).astype(np.float64)
    out = stereo(y, width=0.3, seed=9)
    out = room(out, wet=0.08, decay=0.35, size=0.12, seed=20)
    return finish(out, fin=0.02, fout=0.15)


def whoosh(v=1):
    """A soft air whoosh (a turn, a huff, a fast gesture): band-swept noise peaking at 0.28 s, moving across."""
    n = N(0.75)
    t = tt(n)
    env = smooth_env([(0, 0), (0.28, 1.0), (0.75, 0)], n) ** 1.3
    x = pink(n, 600 + v)
    fc = 500 + 1800 * np.sin(np.pi * np.clip(t / 0.6, 0, 1)) ** 2
    # smooth sweep: three fixed bands cross-faded by the sweep position
    b1, b2, b3 = bandn(x, 300, 900), bandn(x, 800, 2200), bandn(x, 1800, 5000)
    w = (fc - 500) / 1800
    y = b1 * (1 - w) + b2 * (1 - np.abs(w - 0.6)) + b3 * w ** 2 * 0.7
    y *= env
    p0, p1 = (-0.5, 0.5) if v == 1 else (0.5, -0.4)
    pn = p0 + (p1 - p0) * np.clip(t / 0.6, 0, 1)
    out = np.stack([y * np.cos((pn + 1) * np.pi / 4), y * np.sin((pn + 1) * np.pi / 4)], axis=1) * 1.41
    out = room(out, wet=0.1, decay=0.4, size=0.2, seed=21)
    return finish(out, fin=0.01, fout=0.1)


def star_pop(v=1):
    """A cartoon 'pop!' (a little bubble 'bloop' sweeping up) + a bright glass tinkle from the D/E/A set."""
    n = N(0.9)
    out = np.zeros((n, 2))
    f0 = [320, 380, 280, 350][v - 1]
    pop = sweep_tone(n, 0.003, f0, f0 * 3.0, 0.035, tau=0.02, amp=0.9, curve=0.7)
    pop += burst(n, 0.002, 0.008, 700 + v, 1500, 6000, amp=0.25)
    pan = [-0.3, 0.3, 0.1, -0.15][v - 1]
    out = add_st(out, pop, 0.0, pan)
    notes = [[93, 100], [98, 105], [100, 93], [88, 98]][v - 1]
    for j, k in enumerate(notes):
        out = add_st(out, bell_note(midi_hz(k), 0.8, 0.4 - 0.15 * j, bright=0.6, tau=0.4), 0.03 + 0.07 * j, pan + 0.2 * j)
    out = room(out, wet=0.3, decay=1.2, size=0.5, damping=0.4, seed=22)
    return finish(out, fout=0.15)


def galaxy_whirl():
    """A swirling galaxy: rotating filtered air (circling pan), a phasing shimmer and a soft rising glass
    fifth (A–E–A); swells to ~1.3 s, settles by 3.2 s."""
    n = N(3.2)
    t = tt(n)
    env = smooth_env([(0, 0), (1.3, 1.0), (2.2, 0.6), (3.2, 0)], n)
    x = pink(n, 801)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * t)
    y = bandn(x, 400, 1400) * (1 - lfo) + bandn(x, 1200, 4200) * lfo * 0.8
    d = (0.0015 + 0.001 * np.sin(2 * np.pi * 0.7 * t)) * SR  # phaser-ish moving comb
    idx = np.clip(np.arange(n) - d, 0, n - 1)
    y = 0.6 * y + 0.4 * np.interp(idx, np.arange(n), y)
    y *= env * 0.5
    ang = 2 * np.pi * 0.55 * t
    out = np.stack([y * (0.7 + 0.3 * np.cos(ang)), y * (0.7 - 0.3 * np.cos(ang))], axis=1)
    for k, a in [(57, 0.18), (64, 0.15), (69, 0.12), (76, 0.07)]:
        f = midi_hz(k) * (1 + 0.012 * smooth_env([(0, -1), (1.3, 0), (3.2, 0.3)], n) / 12)
        tone = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * 5.3 * t + k))) / SR)
        out += stereo(a * tone * env, width=0.4, seed=k)
    out = room(out, wet=0.4, decay=2.2, size=0.8, damping=0.5, seed=23)
    return finish(out, fin=0.05, fout=0.3)


def bleep():
    """A comedic censor bleep (1 kHz). (tts.py already appends one to bleeped lines; collect_sfx skips the
    beat-level bleep when the line audio carries it.)"""
    n = N(0.45)
    t = tt(n)
    x = 0.5 * np.sin(2 * np.pi * 1000 * t) + 0.08 * np.sin(2 * np.pi * 2000 * t)
    return finish(stereo(x), fin=0.008, fout=0.02)


def phone_tap(v=1):
    """Fingertip taps on a phone screen: tiny glassy ticks with a little plastic body."""
    n = N(0.4)
    x = np.zeros(n)
    times = [(0.01, 1.0), (0.15, 0.8)] if v == 1 else [(0.01, 0.9), (0.09, 0.6), (0.22, 0.85)]
    for i, (at, a) in enumerate(times):
        x += burst(n, at, 0.004, 900 + i + 10 * v, 2500, 7000, amp=a * 0.9)
        x += a * 0.5 * modal(soft_exc(n, at, 1.0), [(950, 1.0, 0.012), (2300, 0.5, 0.008), (4100, 0.3, 0.005)])
    out = stereo(x, width=0.05, seed=4)
    out = room(out, wet=0.06, decay=0.3, size=0.1, seed=24)
    return finish(out, fout=0.05)


def notification_ding():
    """A friendly app 'ding-ding' (E6 then A6; soft sine bells)."""
    n = N(1.4)
    out = np.zeros((n, 2))
    for at, k, a in [(0.005, 88, 0.7), (0.12, 93, 0.6)]:
        m = N(1.2)
        tl = np.arange(m) / SR
        f = midi_hz(k)
        s = (np.sin(2 * np.pi * f * tl) + 0.12 * np.sin(2 * np.pi * 2 * f * tl) * np.exp(-tl / 0.1)
             + 0.05 * np.sin(2 * np.pi * 3.01 * f * tl) * np.exp(-tl / 0.05)) * np.exp(-tl / 0.35)
        s *= 1 - np.exp(-tl / 0.002)
        s[-N(0.05):] *= np.linspace(1, 0, N(0.05))
        out = add_st(out, a * s, at, 0.05)
    out = room(out, wet=0.12, decay=0.6, size=0.2, seed=25)
    return finish(out, fout=0.2)


def block_thunk():
    """The 'BLOCKED' moment: a heavy, satisfying, dull THUNK (big wooden door / stamp) — low, round, no sizzle."""
    n = N(0.9)
    x = np.zeros(n)
    m = N(0.35)
    tl = np.arange(m) / SR
    f = 62 * (1 + 0.9 * np.exp(-tl / 0.02))
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.09) * (1 - np.exp(-tl / 0.002))
    k = N(0.01)
    x[k:k + m] += 1.0 * th
    x[k:k + m] += 0.5 * bandn(np.tanh(6 * th), 150, 900)
    exc = soft_exc(n, 0.01, 3.0)
    x += 0.35 * modal(exc, [(160, 1.0, 0.06), (245, 0.8, 0.045), (390, 0.6, 0.03), (610, 0.35, 0.02),
                            (980, 0.15, 0.012)]) / 2.5
    x += burst(n, 0.01, 0.03, 950, 300, 2500, shape=1.5, amp=0.3)
    x = lp(x, 3500)
    out = stereo(np.tanh(1.1 * x), width=0.1, seed=5)
    out = room(out, wet=0.15, decay=0.6, size=0.35, seed=26)
    return finish(out, fout=0.15)


def wind_soft():
    """A gentle dusk breeze (12 s, loop-seamless): soft gusting air, slowly moving filter, wide stereo."""
    L = N(12.0)
    t = tt(L)
    out = np.zeros((L, 2))
    for c in range(2):
        x = periodic_noise(L, 1000 + c, slope=0.5, lo=120, hi=4000)
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(L, 1 / SR)
        X *= 1.0 / (1 + (f / 900) ** 2)  # gentle low-pass (keeps periodicity)
        x = np.fft.irfft(X, L)
        g = 0.75 + 0.25 * np.sin(2 * np.pi * t * 2 / 12 + c) + 0.12 * np.sin(2 * np.pi * t * 5 / 12 + 1.3 * c)
        out[:, c] = x / np.std(x) * g
    # a whistly band that comes and goes (air over grass)
    wb = periodic_noise(L, 1003, slope=0.0, lo=1500, hi=2600)
    out += stereo(0.12 * wb * (0.5 + 0.5 * np.sin(2 * np.pi * t * 3 / 12)) ** 2, width=0.4, seed=1, circular=True)
    return finish(out, loop=True)


def shimmer():
    """Bowed-glass + celesta sparkle wash (D/E/A only), swelling in and out over 3 s."""
    dur = 3.0
    n = N(dur)
    t = tt(n)
    y = np.zeros(n)
    for k, a in [(81, 0.5), (86, 0.4), (88, 0.35), (93, 0.25)]:
        f = midi_hz(k) * (1 + 0.0025 * np.sin(2 * np.pi * (4.5 + k % 3) * t + k))
        y += a * np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * t + k))
    y *= smooth_env([(0, 0), (1.0, 0.6), (1.8, 0.7), (3.0, 0)], n)
    y += 0.03 * bandn(white(n, 950), 3000, 9000) * smooth_env([(0, 0), (1.0, 1), (3.0, 0)], n)
    r = np.random.default_rng(951)
    sp = np.zeros((n, 2))
    tcur = 0.12
    while tcur < dur - 0.4:
        dens = 0.08 + 0.12 * (1 - abs(tcur / dur - 0.45) * 1.6)
        k = DEA[int(r.integers(5, len(DEA)))]
        sp = add_st(sp, bell_note(midi_hz(k), min(1.2, dur - tcur), amp=r.uniform(0.15, 0.4), tau=0.6),
                    tcur, r.uniform(-0.8, 0.8))
        tcur += max(0.04, r.exponential(max(0.05, dens)))
    out = stereo(y, width=0.3, seed=6) + sp
    out = room(out, wet=0.45, decay=2.2, size=0.8, damping=0.4, seed=15)
    out *= smooth_env([(0, 1), (dur - 0.5, 1), (dur, 0)], n)[:, None]
    return finish(out, fin=0.05, fout=0.3)


def twinkle(v=1):
    """Three celesta-like notes (from D/E/A, high), a little sparkle on a smile or a star."""
    n = N(1.9)
    out = np.zeros((n, 2))
    seqs = {1: [(0.02, 93, 0.9, 0.25), (0.2, 100, 0.65, 0.35), (0.42, 98, 0.75, 0.15)],
            2: [(0.02, 98, 0.85, -0.2), (0.16, 93, 0.7, -0.05), (0.33, 100, 0.6, 0.2)],
            3: [(0.02, 88, 0.8, 0.1), (0.14, 93, 0.7, 0.25), (0.27, 98, 0.65, 0.4)]}[v]
    for at, k, a, p in seqs:
        out = add_st(out, bell_note(midi_hz(k), 1.9 - at, a), at, p)
    out = room(out, wet=0.35, decay=1.6, size=0.6, damping=0.4, seed=16)
    return finish(out, fout=0.25)


def nebula_swell():
    """A slow celestial bloom: glassy D–A–E–A tones with gentle beating + an 'aah' of formant-filtered air,
    swelling to a peak at ~2.2 s and dissolving by 5 s."""
    n = N(5.0)
    t = tt(n)
    env = smooth_env([(0, 0), (2.2, 1.0), (3.2, 0.7), (5.0, 0)], n)
    out = np.zeros((n, 2))
    for i, (k, a) in enumerate([(50, 0.35), (57, 0.3), (64, 0.25), (69, 0.22), (76, 0.12)]):
        for det, side in [(-0.003, 0), (0.003, 1)]:
            f = midi_hz(k) * (1 + det + 0.002 * np.sin(2 * np.pi * (0.25 + 0.07 * i) * t))
            s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.2 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            out[:, side] += a * s * env
    air = pink(n, 1101)
    aah = bp(air, 700, 6) + 0.6 * bp(air, 1150, 7) + 0.3 * bp(air, 2600, 9)
    out += stereo(0.6 * aah * env, width=0.4, seed=7)
    out = lp(out, 7000)
    out = room(out, wet=0.55, decay=3.5, size=0.95, damping=0.6, seed=27)
    return finish(out, fin=0.1, fout=0.5)


def rumble_low():
    """Sub-bass swell (41 Hz + churn + harmonics that read on phone speakers): rises 2.6 s, fades by 5 s."""
    n = N(5.0)
    t = tt(n)
    f = 41 * (1 + 0.02 * np.sin(2 * np.pi * 0.37 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.35 * np.sin(1.5 * ph)
    nz = lp(brown(n, 900), 110, 4)
    sub = 0.8 * tone + 0.9 * nz / (np.std(nz) + 1e-9) * 0.35
    sub = np.tanh(1.6 * sub / (np.max(np.abs(sub)) + 1e-9)) * 0.9
    harm = 0.5 * np.sin(2 * ph + 0.3) + 0.3 * np.sin(3 * ph + 1.1) + 0.15 * np.sin(4 * ph + 2.0)
    churn = bandn(brown(n, 901), 70, 350)
    churn = churn / (np.std(churn) + 1e-9) * (0.75 + 0.25 * slow_noise(n, 1.8, 902))
    mid = 0.22 * harm * (1 + 0.3 * slow_noise(n, 0.9, 903)) + 0.2 * churn
    sat = bandn(np.tanh(5.0 * (np.sin(ph) + 0.5 * churn / (np.max(np.abs(churn)) + 1e-9))), 190, 520, 3)
    grit = bandn(brown(n, 904), 180, 700)
    upper = (0.5 * sat / (np.std(sat) + 1e-9) * (0.8 + 0.2 * slow_noise(n, 0.7, 905))
             + 0.6 * grit / (np.std(grit) + 1e-9) * (0.7 + 0.3 * slow_noise(n, 2.3, 906)))
    env = smooth_env([(0, 0), (2.6, 1.0), (3.4, 0.85), (5.0, 0)], n)
    y = (lp(sub, 260, 2) + lp(mid, 420, 2) + 0.55 * lp(upper, 800, 2)) * env
    return finish(stereo(y, width=0.25, seed=5), fin=0.05, fout=0.3)


def _stick_slip(n, f_contour, amp_env, seed, jitter=0.08, grit=0.0, drop=0.0):
    r = np.random.default_rng(seed)
    x = np.zeros(n)
    ph = 0.0
    i = 0
    pulse = np.array([1.0, 0.55, -0.35, -0.45, -0.2])
    while i < n - 8:
        ph += max(5.0, f_contour[i]) / SR
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
    """The little time-out cage's hinge: a slow stick-slip creak gliding 70→180→110 Hz. ~2.2 s."""
    n = N(2.2)
    t = tt(n)
    f = 70 + 110 * np.sin(np.pi * np.clip(t / 1.6, 0, 1)) ** 1.2 + 40 * np.clip((t - 1.6) / 0.6, 0, 1)
    f *= 1 + 0.06 * slow_noise(n, 6, 700)
    env = smooth_env([(0, 0), (0.15, 0.6), (0.7, 1.0), (1.4, 0.8), (1.9, 0.5), (2.2, 0)], n)
    exc = _stick_slip(n, f, env, 701, jitter=0.06, grit=0.15)
    y = modal(exc, [(520, 0.6, 0.03), (870, 0.8, 0.025), (1410, 1.0, 0.02), (2240, 0.6, 0.015), (3150, 0.3, 0.01)])
    y += 0.05 * bandn(white(n, 702), 1500, 5000) * env
    y = hp(y, 150)
    out = room(stereo(y, width=0.15, seed=4), wet=0.2, decay=0.9, size=0.4, seed=13)
    return finish(out, fin=0.03, fout=0.2)


def lock_click():
    """The cage's latch: two spring clicks 38 ms apart with a small body knock. ~0.3 s."""
    n = N(0.32)
    x = np.zeros(n)
    for at, a, sd in [(0.02, 1.0, 600), (0.058, 0.7, 601)]:
        exc = impulses(n, [at], [a])
        x += modal(exc, [(2480, 0.5, 0.025), (3710, 0.6, 0.02), (5230, 0.35, 0.015), (7120, 0.15, 0.01), (430, 0.35, 0.03)])
        x += burst(n, at, 0.002, sd, 3000, 12000, amp=a * 1.0)
    x = lp(x, 9000)
    return finish(room(x, wet=0.12, decay=0.4, size=0.15, seed=12), fout=0.05)


def kick_thump():
    """The Void's fat-leg back-kick: a quick leg-swing 'fff' (0–0.12 s) then a round, punchy cartoon THWUMP
    in the chest at 0.13 s (pitch-dropping body + soft velvet slap). Punchy, not harsh."""
    n = N(0.8)
    x = np.zeros(n)
    sw = bandn(pink(n, 1201), 500, 3000) * smooth_env([(0, 0), (0.11, 1.0), (0.13, 0.2), (0.2, 0), (0.8, 0)], n)
    x += 0.22 * sw
    hit = 0.13
    m = N(0.4)
    tl = np.arange(m) / SR
    f = 52 * (1 + 2.0 * np.exp(-tl / 0.018))
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.11) * (1 - np.exp(-tl / 0.0015))
    k = N(hit)
    x[k:k + m] += th
    x[k:k + m] += 0.45 * bandn(np.tanh(5 * th), 140, 1000)
    x += burst(n, hit, 0.05, 1202, 250, 2600, shape=1.6, amp=0.55)   # velvet slap
    x += 0.5 * lp(burst(n, hit, 0.14, 1203, 60, 500, shape=1.0, amp=1.0), 400)  # whump
    x = lp(x, 5000)
    out = stereo(np.tanh(1.3 * x) / 1.1, width=0.08, seed=6)
    out = room(out, wet=0.16, decay=0.8, size=0.45, seed=28)
    return finish(out, fin=0.01, fout=0.15)


def whoosh_fly():
    """The magician goes flying: a big doppler whoosh moving L→R plus a soft slide-whistle 'fwee-ooo'."""
    n = N(1.5)
    t = tt(n)
    env = smooth_env([(0, 0), (0.12, 1.0), (0.55, 0.85), (1.2, 0.25), (1.5, 0)], n)
    x = pink(n, 1301)
    lfo = smooth_env([(0, 0), (0.3, 1.0), (1.5, 0.2)], n)
    y = (bandn(x, 300, 1100) * (1 - lfo) + bandn(x, 900, 3800) * lfo) * env * 0.7
    pn = -0.7 + 1.4 * np.clip(t / 1.2, 0, 1)
    out = np.stack([y * np.cos((pn + 1) * np.pi / 4), y * np.sin((pn + 1) * np.pi / 4)], axis=1) * 1.41
    f = np.where(t < 0.35, 650 * (1750 / 650) ** (t / 0.35), 1750 * (520 / 1750) ** np.clip((t - 0.35) / 0.85, 0, 1))
    f = f * (1 + 0.012 * np.sin(2 * np.pi * 6.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    wh = (np.sin(ph) + 0.15 * np.sin(2 * ph)) * smooth_env([(0, 0), (0.06, 0.9), (0.9, 0.7), (1.25, 0), (1.5, 0)], n)
    wh += 0.05 * bandn(white(n, 1302), 1500, 6000) * smooth_env([(0, 0), (0.1, 1), (1.2, 0), (1.5, 0)], n)
    out += np.stack([wh * np.cos((pn + 1) * np.pi / 4), wh * np.sin((pn + 1) * np.pi / 4)], axis=1) * 0.22
    out = room(out, wet=0.15, decay=0.7, size=0.4, seed=29)
    return finish(out, fin=0.01, fout=0.2)


def _bucket(n, at, f0, amp, seed, tau=0.45):
    r = np.random.default_rng(seed)
    ratios = [1.0, 1.59, 2.14, 2.65, 3.42, 4.07, 5.2]
    modes = [(f0 * q * (1 + r.normal(0, 0.006)), (0.8 ** i) * r.uniform(0.6, 1.0), tau * (0.75 ** i) * r.uniform(0.8, 1.2))
             for i, q in enumerate(ratios)]
    exc = soft_exc(n, at, 0.8, amp)
    y = modal(exc, modes)
    y += burst(n, at, 0.004, seed + 1, 1200, 7000, amp=amp * 0.6)
    return y


def crash_buckets():
    """Slapstick crash into the janitor's corner: metal buckets clang and bounce, spray bottles clack, a
    broom knocks, one bucket rolls and wobbles to a stop. Crisp, cartoony, no harsh sizzle. ~2.8 s."""
    n = N(2.8)
    out = np.zeros((n, 2))
    hits = [(0.02, 330, 1.0, -0.2), (0.07, 410, 0.8, 0.25), (0.15, 290, 0.6, -0.35), (0.24, 450, 0.55, 0.3),
            (0.33, 380, 0.42, 0.0), (0.45, 350, 0.3, -0.25), (0.6, 420, 0.22, 0.2)]
    for i, (at, f0, a, p) in enumerate(hits):
        out = add_st(out, _bucket(n, at, f0, a, 1400 + i), 0.0, p)
    # body impact thump (the magician landing)
    m = N(0.3)
    tl = np.arange(m) / SR
    th = np.sin(2 * np.pi * np.cumsum(70 * (1 + np.exp(-tl / 0.02))) / SR) * np.exp(-tl / 0.08)
    body = np.zeros(n)
    body[N(0.02):N(0.02) + m] += th
    out = add_st(out, 0.8 * body + 0.3 * bandn(np.tanh(4 * body), 150, 800), 0.0, 0.0)
    # plastic spray bottles / wood broom clacks
    for i, (at, p) in enumerate([(0.1, 0.4), (0.18, -0.4), (0.29, 0.5), (0.52, -0.1)]):
        y = modal(soft_exc(n, at, 0.6, 0.6), [(1250 + 90 * i, 1.0, 0.018), (2100, 0.6, 0.012), (3300, 0.3, 0.008)])
        out = add_st(out, y * 0.7, 0.0, p)
    # a bucket rolling: quickening wobble taps, then settling
    r = np.random.default_rng(1450)
    tcur, gap, amp = 0.8, 0.16, 0.25
    while tcur < 2.4 and amp > 0.02:
        out = add_st(out, _bucket(n, tcur, 360 + 30 * r.random(), amp, int(1460 + tcur * 100), tau=0.2), 0.0, 0.35)
        tcur += gap
        gap *= 0.86
        amp *= 0.8
    out = lp(out, 8500)
    out = A.high_shelf(out, 4500, -3).astype(np.float64)
    out = np.tanh(out / (np.max(np.abs(out)) + 1e-9) * 1.4)
    out = room(out, wet=0.22, decay=0.9, size=0.5, seed=30)
    return finish(out, fout=0.3)


def mop_clatter():
    """A mop handle toppling: wooden clacks bouncing faster and faster, plus the soggy 'flump' of the mop head."""
    n = N(1.4)
    out = np.zeros((n, 2))
    times = [0.02, 0.2, 0.32, 0.4, 0.455, 0.495, 0.525]
    for i, at in enumerate(times):
        a = 1.0 * 0.78 ** i
        y = modal(soft_exc(n, at, 0.7, a), [(640 + 40 * (i % 2), 1.0, 0.03), (1380, 0.7, 0.02), (2150, 0.45, 0.012),
                                            (3400, 0.2, 0.007)])
        y += burst(n, at, 0.003, 1500 + i, 1500, 6000, amp=a * 0.3)
        out = add_st(out, y, 0.0, -0.3 + 0.1 * i)
    flump = lp(burst(n, 0.06, 0.3, 1520, 80, 900, shape=0.8, amp=0.9), 700)
    out = add_st(out, flump, 0.0, 0.1)
    out = room(out, wet=0.2, decay=0.8, size=0.45, seed=31)
    return finish(out, fout=0.2)


def bucket_bonk(v=1):
    """A bucket lands on the magician's head: a hollow cartoon BONNG with a comic wobble."""
    n = N(1.4)
    t = tt(n)
    f0 = 410 if v == 1 else 520
    y = _bucket(n, 0.005, f0, 1.0, 1600 + v, tau=0.7)
    m = N(0.15)
    tl = np.arange(m) / SR
    tok = np.sin(2 * np.pi * np.cumsum(180 * (1 + np.exp(-tl / 0.01))) / SR) * np.exp(-tl / 0.04)
    y[:m] += 0.5 * tok
    wob = 1 + 0.35 * np.sin(2 * np.pi * 6.5 * t) * np.exp(-t / 0.5)
    y *= wob
    y = lp(y, 7000)
    out = room(stereo(y, width=0.1, seed=7), wet=0.18, decay=0.8, size=0.4, seed=32)
    return finish(out, fout=0.3)


def cartoon_birdies():
    """Little circling birdies/stars over a dazed head: soft chirp pairs and tiny bells circling L↔R. 2.6 s."""
    n = N(2.6)
    t = tt(n)
    mono = np.zeros(n)
    r = np.random.default_rng(1700)
    tcur = 0.02
    while tcur < 2.3:
        for j in range(2):
            f0 = r.uniform(2600, 3000)
            mono += sweep_tone(n, tcur + j * 0.09, f0, f0 * 1.3, 0.06, tau=0.035, amp=0.35, curve=0.5)
        tcur += r.uniform(0.32, 0.45)
    bells = np.zeros(n)
    for i, at in enumerate(np.arange(0.15, 2.3, 0.38)):
        k = [93, 98, 100, 98][i % 4]
        b = bell_note(midi_hz(k), 0.6, 0.3, bright=0.4, tau=0.3)
        bells[N(at):N(at) + len(b)] += b[: max(0, n - N(at))]
    y = lp(mono, 6000) + bells
    ang = 2 * np.pi * 0.85 * t
    out = np.stack([y * (0.75 + 0.25 * np.cos(ang)), y * (0.75 - 0.25 * np.cos(ang))], axis=1)
    out *= smooth_env([(0, 0), (0.05, 1), (2.2, 1), (2.6, 0)], n)[:, None]
    out = room(out, wet=0.2, decay=0.8, size=0.4, seed=33)
    return finish(out, fout=0.2)


def dust_sparkle():
    """The magician's numbing dust: a dry, grey glitter-hiss with muted, slightly drooping glassy tinkles
    (colour draining away). ~1.8 s."""
    n = N(1.8)
    t = tt(n)
    env = smooth_env([(0, 0), (0.15, 1.0), (0.9, 0.6), (1.8, 0)], n)
    hiss = bandn(white(n, 1800), 3500, 9000) * env * 0.12
    r = np.random.default_rng(1801)
    grains = np.zeros(n)
    for _ in range(160):
        at = r.uniform(0.01, 1.6) ** 1.3 / 1.6 ** 0.3
        k = N(at)
        ln = int(r.integers(15, 60))
        if k + ln < n:
            grains[k:k + ln] += r.normal(0, 1, ln) * np.exp(-np.arange(ln) / (ln / 5)) * r.uniform(0.1, 0.6)
    grains = bandn(grains, 2500, 8000) * env
    out = stereo(hiss + 0.5 * grains, width=0.5, seed=8)
    for i, (at, k) in enumerate([(0.05, 93), (0.3, 88), (0.55, 86), (0.85, 81)]):
        f = midi_hz(k)
        m = N(1.0)
        tl = np.arange(m) / SR
        s = np.sin(2 * np.pi * np.cumsum(f * (1 - 0.01 * tl)) / SR) * np.exp(-tl / 0.35) * (1 - np.exp(-tl / 0.003))
        s[-N(0.05):] *= np.linspace(1, 0, N(0.05))
        out = add_st(out, 0.18 * lp(s, 3000), at, -0.4 + 0.25 * i)
    out = room(out, wet=0.25, decay=1.2, size=0.5, damping=0.7, seed=34)
    return finish(out, fin=0.01, fout=0.3)


def dagger_shing():
    """The wavy little dagger: a quick metallic scrape and a bright ring ('shing'), lowpassed so it never hurts."""
    n = N(1.3)
    t = tt(n)
    sc = bandn(white(n, 1900), 2500, 7500) * smooth_env([(0, 0), (0.02, 0.6), (0.09, 1.0), (0.12, 0.1), (0.2, 0), (1.3, 0)], n)
    exc = soft_exc(n, 0.1, 0.5, 1.0)
    ring = modal(exc, [(2093, 0.8, 0.55), (3120, 0.6, 0.4), (4440, 0.45, 0.25), (5870, 0.25, 0.15), (1310, 0.35, 0.3)])
    ring *= 1 + 0.08 * np.sin(2 * np.pi * 7 * t)
    y = 0.4 * sc + 0.5 * ring / (np.max(np.abs(ring)) + 1e-9)
    y = lp(y, 8000)
    y = A.high_shelf(y, 5000, -3).astype(np.float64)
    out = room(stereo(y, width=0.25, seed=9), wet=0.25, decay=1.1, size=0.5, seed=35)
    return finish(out, fin=0.005, fout=0.25)


def gulp():
    """A cartoon gulp: a little closed-mouth 'glk' (pitch-dropping resonance + throat click) and a tiny echo."""
    n = N(0.5)
    x = np.zeros(n)
    x += sweep_tone(n, 0.05, 820, 240, 0.09, tau=0.05, amp=0.8, curve=0.6, harm=0.2)
    x += burst(n, 0.045, 0.006, 2000, 800, 4000, amp=0.35)
    x += sweep_tone(n, 0.2, 520, 200, 0.07, tau=0.04, amp=0.3, curve=0.6)
    x = lp(x, 5000)
    return finish(room(stereo(x), wet=0.08, decay=0.3, size=0.1, seed=36), fout=0.08)


def pat_pat(v=1):
    """Two gentle pats on a (velvet) shoulder: muffled hand-on-cloth slaps with a little body."""
    n = N(0.6)
    x = np.zeros(n)
    times = [(0.01, 1.0), (0.2, 0.8)] if v == 1 else [(0.01, 0.9), (0.17, 0.75)]
    for i, (at, a) in enumerate(times):
        x += burst(n, at, 0.05, 2100 + i + 10 * v, 300, 2200, shape=1.4, amp=a * 0.7)
        m = N(0.08)
        tl = np.arange(m) / SR
        b = np.sin(2 * np.pi * (170 + 20 * v) * tl) * np.exp(-tl / 0.022) * (1 - np.exp(-tl / 0.002))
        k = N(at)
        x[k:k + m] += a * 0.6 * b
    x = lp(x, 3500)
    return finish(room(stereo(x, width=0.1), wet=0.08, decay=0.35, size=0.15, seed=37), fout=0.08)


# ============================================================================================
# ambience beds (40 s, loop-seamless)


def amb_edge():
    """THE_EDGE: soft dusk air (gentle, slowly breathing), a faint far breeze band, and distant wind
    chimes (D/E/A) every few seconds, deep in a soft reverb."""
    L = N(40.0)
    t = tt(L)
    out = np.zeros((L, 2))
    for c in range(2):
        x = periodic_noise(L, 3000 + c, slope=0.55, lo=100, hi=6000)
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(L, 1 / SR)
        X *= 1.0 / (1 + (f / 1400) ** 2)
        x = np.fft.irfft(X, L)
        g = 0.8 + 0.2 * np.sin(2 * np.pi * t * 3 / 40 + 2 * c) + 0.1 * np.sin(2 * np.pi * t * 7 / 40 + c)
        out[:, c] = x / np.std(x) * g
    chimes = np.zeros((L, 2))
    r = np.random.default_rng(3010)
    tcur = 1.0
    pitches = [81, 86, 88, 93, 98, 100]
    while tcur < 39.0:
        for j in range(int(r.integers(1, 4))):
            k = pitches[int(r.integers(len(pitches)))]
            f0 = midi_hz(k)
            m = N(3.0)
            tl = np.arange(m) / SR
            s = (np.sin(2 * np.pi * f0 * tl) * np.exp(-tl / 1.4) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * tl) * np.exp(-tl / 0.5)
                 + 0.12 * np.sin(2 * np.pi * f0 * 5.4 * tl) * np.exp(-tl / 0.25)) * (1 - np.exp(-tl / 0.002))
            s = lp(s, 5000) * r.uniform(0.2, 0.45)
            s[-N(0.1):] *= np.linspace(1, 0, N(0.1))
            st = N(tcur + j * r.uniform(0.15, 0.35))
            idx = (st + np.arange(m)) % L
            gl, gr = A.pan_gains(r.uniform(-0.6, 0.6))
            np.add.at(chimes[:, 0], idx, s * gl)
            np.add.at(chimes[:, 1], idx, s * gr)
        tcur += r.uniform(3.0, 6.5)
    chimes = periodic_reverb(chimes, wet=1.2, decay=2.8, size=0.85, damping=0.55, predelay=0.04, seed=40)
    out = out * 0.5 + chimes * 0.18
    return finish(out, loop=True)


def amb_backroom():
    """MIND_BACKROOM: a low, cozy room tone (dark air), a distant mains-like hum that slowly beats, and a
    couple of far-off drips — quiet, cavernous."""
    L = N(40.0)
    t = tt(L)
    out = np.zeros((L, 2))
    for c in range(2):
        x = periodic_noise(L, 3100 + c, slope=1.0, lo=30, hi=1500)
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(L, 1 / SR)
        X *= 1.0 / (1 + (f / 350) ** 2)
        x = np.fft.irfft(X, L)
        out[:, c] = x / np.std(x) * (0.9 + 0.1 * np.sin(2 * np.pi * t * 2 / 40 + c))
    hum = np.zeros(L)
    for h, a in [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15), (5, 0.08)]:
        # frequencies chosen as whole cycles per loop (exactly periodic): ~55 Hz family, +2 slow beats
        k = round(55.0 * h * 40)
        hum += a * (np.sin(2 * np.pi * k * t / 40) + 0.6 * np.sin(2 * np.pi * (k + 2) * t / 40 + h))
    hum *= 0.8 + 0.2 * np.sin(2 * np.pi * t * 1 / 40)
    out += stereo(0.12 * hum, width=0.2, seed=2, circular=True)
    drips = np.zeros((L, 2))
    for at, k, p in [(7.3, 88, -0.5), (21.8, 86, 0.4), (33.1, 88, -0.2)]:
        m = N(0.4)
        tl = np.arange(m) / SR
        f = midi_hz(k) * (1 + 0.6 * np.exp(-tl / 0.01))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl / 0.06) * 0.25
        s[-N(0.02):] *= np.linspace(1, 0, N(0.02))
        st = N(at)
        gl, gr = A.pan_gains(p)
        drips[st:st + m, 0] += s * gl
        drips[st:st + m, 1] += s * gr
    drips = periodic_reverb(drips, wet=1.5, decay=2.2, size=0.8, damping=0.6, predelay=0.03, seed=41)
    out = out * 0.6 + drips * 0.25
    return finish(out, loop=True)


# ============================================================================================
# registry: name -> (fn, variants, sync s, design loudness, bed/loop, description)

SFX = {
    "footsteps_soft": (footsteps_soft, 3, 0.03, -30, False, "soft steps on a grassy path, 4 × 0.55 s cycle (loopable)"),
    "footsteps_run": (footsteps_run, 3, 0.02, -28, False, "quick light sneaker patter, 8 × 0.17 s cycle (loopable)"),
    "footsteps_stomp": (footsteps_stomp, 2, 0.02, -24, False, "heavy comic stomps, 3 × 0.5 s cycle (loopable)"),
    "sparkle_appear": (sparkle_appear, 1, 0.55, -25, False, "magical arrival: rising glassy arpeggio blooming at 0.55 s"),
    "thud_sit": (thud_sit, 1, 0.01, -24, False, "plop onto one's backside in the grass (bump-bump)"),
    "cloth_rustle": (cloth_rustle, 3, 0.0, -32, False, "soft fabric movement"),
    "whoosh": (whoosh, 2, 0.28, -28, False, "soft air whoosh, peak at 0.28 s"),
    "star_pop": (star_pop, 4, 0.0, -27, False, "cartoon pop + glass tinkle"),
    "galaxy_whirl": (galaxy_whirl, 1, 0.0, -27, False, "swirling galaxy (circling air + glass fifth), peak ~1.3 s"),
    "bleep": (bleep, 1, 0.0, -21, False, "comedic censor bleep (1 kHz)"),
    "phone_tap": (phone_tap, 2, 0.01, -31, False, "fingertip taps on the phone"),
    "notification_ding": (notification_ding, 1, 0.005, -25, False, "friendly app ding-ding (E6, A6)"),
    "block_thunk": (block_thunk, 1, 0.01, -21, False, "the BLOCK: heavy round thunk"),
    "wind_soft": (wind_soft, 1, 0.0, -36, True, "gentle dusk breeze, 12 s seamless loop"),
    "shimmer": (shimmer, 1, 0.0, -28, False, "bowed glass + celesta sparkle wash (D/E/A)"),
    "twinkle": (twinkle, 3, 0.02, -28, False, "three high celesta notes"),
    "nebula_swell": (nebula_swell, 1, 0.0, -26, False, "slow celestial bloom, peak ~2.2 s"),
    "rumble_low": (rumble_low, 1, 0.0, -27, False, "sub rumble swell (with phone-audible harmonics), peak 2.6 s"),
    "cage_creak": (cage_creak, 1, 0.1, -27, False, "the time-out cage's hinge creak"),
    "lock_click": (lock_click, 1, 0.02, -27, False, "the cage latch click"),
    "kick_thump": (kick_thump, 1, 0.13, -19, False, "leg swing + cartoon THWUMP at 0.13 s"),
    "whoosh_fly": (whoosh_fly, 1, 0.02, -23, False, "flying away: doppler whoosh L→R + soft slide whistle"),
    "crash_buckets": (crash_buckets, 1, 0.02, -17, False, "buckets/bottles/broom crash, a bucket rolls to a stop"),
    "mop_clatter": (mop_clatter, 1, 0.02, -22, False, "mop handle topples and clatters"),
    "bucket_bonk": (bucket_bonk, 2, 0.005, -21, False, "hollow cartoon BONNG with wobble"),
    "cartoon_birdies": (cartoon_birdies, 1, 0.0, -27, False, "circling chirps + tiny bells over a dazed head"),
    "dust_sparkle": (dust_sparkle, 1, 0.0, -29, False, "numbing dust: grey glitter hiss, drooping muted tinkles"),
    "dagger_shing": (dagger_shing, 1, 0.1, -25, False, "dagger scrape + bright ring ('shing' at 0.1 s)"),
    "gulp": (gulp, 1, 0.05, -26, False, "cartoon gulp"),
    "pat_pat": (pat_pat, 2, 0.01, -27, False, "two soft pats on a velvet shoulder"),
    "amb_edge": (amb_edge, 1, 0.0, -40, True, "THE_EDGE ambience: dusk air + distant chimes, 40 s seamless loop"),
    "amb_backroom": (amb_backroom, 1, 0.0, -42, True, "MIND_BACKROOM ambience: room tone + distant hum + far drips, 40 s loop"),
}
LOOPABLE = {"footsteps_soft", "footsteps_run", "footsteps_stomp", "wind_soft", "amb_edge", "amb_backroom"}


def files_for(name, nvar):
    return [f"{name}.wav"] + [f"{name}_{v}.wav" for v in range(2, nvar + 1)]


def build(name, spectro_dir=None):
    fn, nvar, sync, lufs, bed, desc = SFX[name]
    out = []
    for v in range(1, nvar + 1):
        x = fn(v) if nvar > 1 else fn()
        x = level(x, lufs, bed=bed)
        f = files_for(name, nvar)[v - 1]
        A.save(os.path.join(OUT, f), x)
        out.append((f, len(x) / SR))
        if spectro_dir:
            A.spectrogram_png(x, os.path.join(spectro_dir, f.replace(".wav", ".png")), max_hz=12000, width=700,
                              height=260, title=f"{f}  sync {sync}s")
    return {"files": [f for f, _ in out], "dur": round(out[0][1], 3), "sync": sync, "lufs": lufs,
            "loop": name in LOOPABLE, "bed": bed, "desc": desc}


def main():
    a = sys.argv[1:]
    if "--list" in a:
        for k, v in SFX.items():
            print(f"{k:18s} x{v[1]}  sync {v[2]:.2f}s  {v[3]:4d} LUFS  {v[5]}")
        return
    spectro = None
    if "--spectro" in a:
        i = a.index("--spectro")
        spectro = a[i + 1]
        a = a[:i] + a[i + 2:]
    names = [x for x in a if not x.startswith("--")] or list(SFX)
    bad = [x for x in names if x not in SFX]
    if bad:
        raise SystemExit(f"unknown sfx: {bad}")
    os.makedirs(OUT, exist_ok=True)
    mp = os.path.join(OUT, "meta.json")
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    for nm in names:
        meta[nm] = build(nm, spectro)
        x = A.load(os.path.join(OUT, meta[nm]["files"][0]))
        print(f"{nm:18s} {len(meta[nm]['files'])} file(s) {meta[nm]['dur']:5.2f}s  peak {A.lin2db(np.abs(x).max()):6.1f} dBFS"
              f"  momentary-max {momentary_max(x):6.1f} LUFS", flush=True)
    json.dump(meta, open(mp, "w"), indent=1)


if __name__ == "__main__":
    main()
