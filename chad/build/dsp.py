"""Small numpy/scipy DSP toolkit used to synthesize every sound effect and music cue.

Everything is mono float64 at SR unless a function says otherwise; stereo arrays
are shaped (n, 2).
"""
import numpy as np
from scipy import signal

SR = 48000


def n_of(dur):
    return max(1, int(round(dur * SR)))


def t_of(n):
    return np.arange(n) / SR


def db(x):
    return 10.0 ** (x / 20.0)


def midi_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) if len(x) else 0
    return x * (peak / m) if m > 1e-9 else x


def pad_to(x, n):
    if len(x) >= n:
        return x[:n]
    shape = (n - len(x),) + x.shape[1:]
    return np.concatenate([x, np.zeros(shape)])


def add_at(buf, x, start):
    """Mix x into buf beginning at sample `start` (clips at buffer edges)."""
    if start >= len(buf):
        return
    if start < 0:
        x = x[-start:]
        start = 0
    end = min(len(buf), start + len(x))
    buf[start:end] += x[: end - start]


# ---------------------------------------------------------------- envelopes
def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    a, b = n_of(fin) if fin else 0, n_of(fout) if fout else 0
    if a:
        a = min(a, len(x))
        ramp = np.linspace(0, 1, a)
        x[:a] = (x[:a].T * ramp).T
    if b:
        b = min(b, len(x))
        ramp = np.linspace(1, 0, b)
        x[-b:] = (x[-b:].T * ramp).T
    return x


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    env = np.full(n, s, dtype=float)
    na, nd, nr = n_of(a), n_of(d), n_of(r)
    na = min(na, n)
    env[:na] = np.linspace(0, 1, na)
    nd = min(nd, max(0, n - na))
    env[na:na + nd] = np.linspace(1, s, nd)
    nr = min(nr, n)
    env[n - nr:] *= np.linspace(1, 0, nr)
    return env


def expdec(n, tau, attack=0.002):
    t = t_of(n)
    env = np.exp(-t / max(tau, 1e-4))
    na = min(n, n_of(attack))
    if na > 1:
        env[:na] *= np.linspace(0, 1, na)
    return env


def smooth_env(x, attack=0.01, release=0.2):
    """One-pole attack/release follower over |x| (vectorized via block lfilter)."""
    rect = np.abs(x)
    # Two passes: fast attack then slow release approximation.
    ra = np.exp(-1.0 / (SR * attack))
    rr = np.exp(-1.0 / (SR * release))
    up = signal.lfilter([1 - ra], [1, -ra], rect)
    down = signal.lfilter([1 - rr], [1, -rr], np.maximum(up, rect))
    return np.maximum(up, down)


# ---------------------------------------------------------------- noise
def white(n, rng):
    return rng.standard_normal(n)


def colored(n, rng, exponent=1.0):
    """1/f^exponent noise (exponent 1 = pink, 2 = brown)."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1] if len(f) > 1 else 1.0
    X /= f ** (exponent / 2.0)
    y = np.fft.irfft(X, n)
    return norm(y, 1.0)


def pink(n, rng):
    return colored(n, rng, 1.0)


def brown(n, rng):
    return colored(n, rng, 2.0)


# ---------------------------------------------------------------- filters
def _sos(kind, fc, order=2):
    fc = np.atleast_1d(fc).astype(float)
    fc = np.clip(fc, 10, SR / 2 * 0.98)
    if kind == "band":
        return signal.butter(order, fc / (SR / 2), btype="bandpass", output="sos")
    return signal.butter(order, fc[0] / (SR / 2), btype=kind, output="sos")


def lowpass(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x, axis=0)


def highpass(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x, axis=0)


def bandpass(x, lo, hi, order=2):
    return signal.sosfilt(_sos("band", [lo, hi], order), x, axis=0)


def peak_band(x, f0, q):
    """Resonant band (constant 0 dB peak) - used for formants."""
    b, a = signal.iirpeak(min(f0, SR / 2 * 0.95), q, fs=SR)
    return signal.lfilter(b, a, x)


def sweep_filter(x, fc_fn, q=2.0, kind="band", block=256):
    """Time-varying biquad: fc_fn(t_seconds_array) gives the cutoff per block."""
    out = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        seg = x[i:i + block]
        fc = float(np.clip(fc_fn(np.array([(i + block / 2) / SR]))[0], 30, SR / 2 * 0.9))
        w0 = 2 * np.pi * fc / SR
        alpha = np.sin(w0) / (2 * q)
        cw = np.cos(w0)
        if kind == "band":
            b = np.array([alpha, 0, -alpha])
        elif kind == "low":
            b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
        else:  # high
            b = np.array([(1 + cw) / 2, -(1 + cw), (1 + cw) / 2])
        a = np.array([1 + alpha, -2 * cw, 1 - alpha])
        b, a = b / a[0], a / a[0]
        y, zi = signal.lfilter(b, a, seg, zi=zi)
        out[i:i + block] = y
    return out


# ---------------------------------------------------------------- oscillators
def osc_phase(freq, n):
    """freq: scalar or per-sample array (Hz) -> phase in radians."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return 2 * np.pi * np.cumsum(f) / SR


def sine(freq, n):
    return np.sin(osc_phase(freq, n))


def additive(freq, n, amps):
    ph = osc_phase(freq, n)
    fmax = np.max(np.broadcast_to(np.asarray(freq, dtype=float), (n,)))
    y = np.zeros(n)
    for k, a in enumerate(amps, start=1):
        if a == 0 or k * fmax >= SR / 2 * 0.9:
            continue
        y += a * np.sin(k * ph)
    return y


def saw(freq, n, harmonics=40):
    return additive(freq, n, [1.0 / k for k in range(1, harmonics + 1)])


def square(freq, n, harmonics=31):
    return additive(freq, n, [(1.0 / k if k % 2 else 0.0) for k in range(1, harmonics + 1)])


def karplus(freq, dur, rng, decay=0.996, bright=0.6, seed_noise=None):
    """Plucked string with exact pitch (integer-period KS + resample)."""
    n = n_of(dur)
    N = max(2, int(round(SR / freq)))
    f_actual = SR / N
    m = int(n * f_actual / freq) + N + 2
    buf = rng.uniform(-1, 1, N) if seed_noise is None else seed_noise[:N]
    if bright < 1:
        buf = lowpass(buf, 400 + bright * 9000, 1)
    blocks = int(np.ceil(m / N)) + 1
    y = np.zeros(blocks * N)
    y[:N] = buf
    for k in range(1, blocks):
        prev = y[(k - 1) * N:k * N]
        shifted = np.concatenate(([y[(k - 1) * N - 1] if k > 1 else 0.0], prev[:-1]))
        y[k * N:(k + 1) * N] = decay * 0.5 * (prev + shifted)
    pos = np.arange(n) * (f_actual / freq)
    return np.interp(pos, np.arange(len(y)), y)


# ---------------------------------------------------------------- space
def pan(x, p):
    """Constant-power pan of a mono signal, p in [-1, 1]."""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def stereo(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1) * np.sqrt(0.5)


_IR_CACHE = {}


def reverb(x, wet=0.25, decay=1.8, predelay=0.02, tone=4000, seed=7):
    """Cheap stereo convolution reverb with a synthetic exponentially-decaying IR."""
    key = (decay, predelay, tone, seed)
    if key not in _IR_CACHE:
        rng = np.random.default_rng(seed)
        n = n_of(decay * 1.4)
        t = t_of(n)
        env = np.exp(-t * 6.9 / decay)
        irs = []
        for _ in range(2):
            ir = rng.standard_normal(n) * env
            ir = lowpass(ir, tone, 1)
            ir = np.concatenate([np.zeros(n_of(predelay)), ir])
            irs.append(ir / np.sqrt(np.sum(ir ** 2)))
        _IR_CACHE[key] = np.stack(irs, axis=1)
    ir = _IR_CACHE[key]
    xs = stereo(x)
    tail = len(ir)
    out = np.zeros((len(xs) + tail, 2))
    out[:len(xs)] += xs * (1 - wet)
    for c in range(2):
        out[:, c][:len(xs) + len(ir) - 1] += wet * signal.fftconvolve(xs[:, c], ir[:, c])[: len(xs) + tail]
    return out


def trim_tail(x, thresh_db=-70):
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    idx = np.where(a > db(thresh_db))[0]
    return x[: idx[-1] + 1] if len(idx) else x[:1]
