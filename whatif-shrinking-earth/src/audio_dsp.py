"""DSP building blocks for the score, sound effects and mix (numpy/scipy)."""
import math

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d

SR = 48000


def ns(t):
    return int(round(t * SR))


def midi_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def tarr(n):
    return np.arange(n, dtype=np.float64) / SR


# ----------------------------------------------------------------------------
# oscillators
# ----------------------------------------------------------------------------

def _phase(freq, n, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, np.float64), (n,))
    dt = f / SR
    ph = phase0 + np.concatenate([[0.0], np.cumsum(dt[:-1])])
    return ph % 1.0, dt


def _polyblep(t, dt):
    out = np.zeros_like(t)
    m = t < dt
    if np.any(m):
        x = t[m] / dt[m]
        out[m] = x + x - x * x - 1.0
    m2 = t > 1.0 - dt
    if np.any(m2):
        x = (t[m2] - 1.0) / dt[m2]
        out[m2] = x * x + x + x + 1.0
    return out


def saw(freq, n, phase0=0.0):
    ph, dt = _phase(freq, n, phase0)
    return 2.0 * ph - 1.0 - _polyblep(ph, dt)


def square(freq, n, phase0=0.0, duty=0.5):
    ph, dt = _phase(freq, n, phase0)
    y = np.where(ph < duty, 1.0, -1.0)
    y += _polyblep(ph, dt)
    y -= _polyblep((ph + (1.0 - duty)) % 1.0, dt)
    return y


def tri(freq, n, phase0=0.0):
    ph, _ = _phase(freq, n, phase0)
    return 4.0 * np.abs(ph - 0.5) - 1.0


def sine(freq, n, phase0=0.0):
    ph, _ = _phase(freq, n, phase0)
    return np.sin(2 * np.pi * ph)


# ----------------------------------------------------------------------------
# envelopes
# ----------------------------------------------------------------------------

def env_points(n, pts):
    """Piecewise-linear envelope from (time_s, value) points."""
    ts = np.array([p[0] for p in pts]) * SR
    vs = np.array([p[1] for p in pts])
    return np.interp(np.arange(n), ts, vs)


def env_adsr(n, a, d, s, rel_start, r):
    return env_points(n, [(0, 0), (a, 1), (a + d, s), (max(a + d, rel_start), s), (max(a + d, rel_start) + r, 0)])


def fade_edges(x, fin=0.003, fout=0.01):
    n = x.shape[-1]
    a = min(n // 2, ns(fin))
    b = min(n // 2, ns(fout))
    if a > 0:
        x[..., :a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if b > 0:
        x[..., -b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return x


def smooth_curve(n, t0, t1):
    """0 before t0, 1 after t1, smootherstep in between (in samples)."""
    i = np.arange(n)
    x = np.clip((i - t0) / max(1, (t1 - t0)), 0, 1)
    return x * x * x * (x * (x * 6 - 15) + 10)


# ----------------------------------------------------------------------------
# filters
# ----------------------------------------------------------------------------

def _sos(kind, f, order=2):
    nyq = SR / 2
    if isinstance(f, (list, tuple)):
        f = [min(max(10.0, v), nyq * 0.98) for v in f]
    else:
        f = min(max(10.0, f), nyq * 0.98)
    return signal.butter(order, f, kind, fs=SR, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x, axis=-1)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x, axis=-1)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("band", [lo, hi], order), x, axis=-1)


def biquad(kind, f0, q=0.707, gain_db=0.0):
    """RBJ cookbook biquad as an sos row."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * min(f0, SR * 0.49) / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * q)
    if kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
        a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    elif kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "bandpass":
        b = [al, 0, -al]
        a = [1 + al, -2 * cw, 1 - al]
    else:
        raise ValueError(kind)
    return np.array([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]])


def eq(x, *bands):
    """bands: (kind, f0, q, gain_db) tuples."""
    sos = np.concatenate([biquad(k, f, q, g) for (k, f, q, g) in bands], 0)
    return signal.sosfilt(sos, x, axis=-1)


def sweep(x, fc, kind="low", q=0.9, block=64):
    """Time-varying resonant biquad; fc is an array (per sample) or callable."""
    n = len(x)
    out = np.empty(n)
    zi = np.zeros((1, 2))
    fcs = np.broadcast_to(np.asarray(fc, np.float64), (n,))
    rbj = {"low": "lowpass", "high": "highpass", "band": "bandpass"}[kind]
    for i in range(0, n, block):
        sos = biquad(rbj, float(fcs[i]), q)
        out[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return out


# ----------------------------------------------------------------------------
# stereo + reverb
# ----------------------------------------------------------------------------

def pan(x, p=0.0):
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)]) * np.sqrt(2) * 0.7071


def make_ir(t60=2.0, predelay=0.02, bright=0.5, seed=0, early=6, width=1.0, length=None):
    """Synthetic stereo IR: decaying noise with frequency-dependent decay."""
    rng = np.random.default_rng(seed)
    L = length or (predelay + t60 * 1.15)
    n = ns(L)
    t = tarr(n)
    noise = rng.standard_normal((2, n))
    if width < 1.0:
        mid = noise.mean(0, keepdims=True)
        noise = mid * (1 - width) + noise * width
    lo = lp(noise, 450, 2)
    mi = bp(noise, 450, 3500, 2)
    hi = hp(noise, 3500, 2)

    def e(T):
        return np.exp(-6.9 * np.clip(t - predelay, 0, None) / max(0.05, T))

    ir = lo * e(t60 * 1.15) + mi * e(t60 * (0.75 + 0.2 * bright)) * (0.6 + 0.3 * bright) \
        + hi * e(t60 * (0.25 + 0.35 * bright)) * (0.25 + 0.5 * bright)
    ir[:, : ns(predelay)] = 0
    # soften onset of the diffuse tail
    on = smooth_curve(n, ns(predelay), ns(predelay + 0.03))
    ir *= on
    # early reflections
    for k in range(early):
        d = predelay * 0.4 + rng.uniform(0.004, predelay + 0.035)
        g = rng.uniform(0.25, 0.6) * (0.8 ** k)
        for ch in range(2):
            idx = ns(d + rng.uniform(0, 0.004))
            if idx < n:
                ir[ch, idx] += g * (1 if rng.random() > 0.3 else -1)
    ir /= np.sqrt(np.sum(ir ** 2) / 2)
    return ir


def convolve(x, ir):
    """x: (2, n) or (n,) ; ir: (2, m). Returns (2, n) (tail truncated)."""
    if x.ndim == 1:
        x = np.stack([x, x])
    n = x.shape[1]
    out = np.empty((2, n))
    for ch in range(2):
        out[ch] = signal.oaconvolve(x[ch], ir[ch], mode="full")[:n]
    return out


# ----------------------------------------------------------------------------
# dynamics
# ----------------------------------------------------------------------------

def block_rms_db(x, block=0.01):
    """RMS level (dBFS) per block of a mono or stereo signal."""
    if x.ndim > 1:
        x = np.sqrt(np.mean(x ** 2, axis=0))
    b = ns(block)
    n = len(x) // b
    r = np.sqrt(np.mean(x[: n * b].reshape(n, b) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(r + 1e-12), b


def ar_smooth(v, attack, release, step):
    """One-pole attack/release smoothing of a block-rate control signal."""
    aa = math.exp(-step / max(1e-4, attack))
    ra = math.exp(-step / max(1e-4, release))
    out = np.empty_like(v)
    y = v[0]
    for i, x in enumerate(v):
        c = aa if x > y else ra
        y = c * y + (1 - c) * x
        out[i] = y
    return out


def upsample_ctrl(v, b, n):
    xs = (np.arange(len(v)) + 0.5) * b
    return np.interp(np.arange(n), xs, v)


def compress(x, thresh_db=-24.0, ratio=2.5, attack=0.005, release=0.08, makeup_db=0.0, knee=6.0):
    lev, b = block_rms_db(x, 0.002)
    over = lev - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    gr = ar_smooth(gr, attack, release, 0.002)
    g = 10 ** ((-gr + makeup_db) / 20)
    return x * upsample_ctrl(g, b, x.shape[-1])


def true_peak(x, os=4):
    if x.ndim == 1:
        x = x[None]
    m = 0.0
    for ch in x:
        # chunked to bound memory
        step = SR * 20
        for i in range(0, len(ch), step):
            seg = ch[max(0, i - 64): i + step + 64]
            y = signal.resample_poly(seg, os, 1)
            m = max(m, float(np.max(np.abs(y))))
    return m


def limiter(x, ceiling_db=-1.6, look=0.004, release=0.12, os=4):
    """Look-ahead true-peak limiter for a (2, n) signal."""
    ceil = 10 ** (ceiling_db / 20)
    n = x.shape[1]
    # oversampled peak envelope per sample (max over channels)
    pk = np.zeros(n)
    step = SR * 20
    for i in range(0, n, step):
        a, b_ = max(0, i - 64), min(n, i + step + 64)
        seg = x[:, a:b_]
        y = np.abs(signal.resample_poly(seg, os, 1, axis=1)).max(axis=0)
        y = y.reshape(-1, os).max(axis=1)
        pk[i:min(n, i + step)] = y[i - a: i - a + min(step, n - i)]
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    La = max(2, ns(look))
    # g1[n] <= need[m] for every m within La samples of n
    g1 = minimum_filter1d(need, size=2 * La + 1, mode="nearest")
    # centered moving average over < La samples stays below need (smooth attack)
    W = La
    g2 = signal.oaconvolve(np.concatenate([np.full(W, g1[0]), g1, np.full(W, g1[-1])]),
                           np.ones(W) / W, mode="same")[W:-W]
    g2 = np.minimum(g2, 1.0)
    # slow release on 1 ms blocks (instant drop, smooth recovery)
    bs = ns(0.001)
    nb = n // bs + 1
    gpad = np.concatenate([g2, np.ones(nb * bs - n)])
    gb = gpad.reshape(nb, bs).min(axis=1)
    rel = math.exp(-0.001 / release)
    out = np.empty(nb)
    y = 1.0
    for i, v in enumerate(gb):
        y = v if v < y else (rel * y + (1 - rel) * v)
        out[i] = y
    g3 = np.interp(np.arange(n), (np.arange(nb) + 0.5) * bs, out)
    gs = np.minimum(g2, g3)
    return x * gs[None, :], gs
