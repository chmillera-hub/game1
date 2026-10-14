"""Shared DSP helpers for the Psalm 22 soundtrack (music.py, sfx.py, mix.py).

Pure numpy/scipy. All signals are float64 arrays, mono (n,) or stereo (n, 2), at SR = 48 kHz.
"""
import json, os
import numpy as np
from scipy.signal import oaconvolve, sosfilt, sosfiltfilt, resample_poly

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # psalm22/
WORK = os.environ.get("WORK", "/opt/work/psalm22")
AUDIO = os.path.join(WORK, "audio")
DEV = os.path.join(WORK, "dev", "audio")


# ----------------------------------------------------------------------------- timing
def load_timing():
    """Read timeline.json + phrases.json and return a dict with shots, blocks, phrases (seconds)."""
    tl = json.load(open(os.environ.get("TIMELINE", os.path.join(ROOT, "timeline.json"))))
    ph = json.load(open(os.environ.get("PHRASES", os.path.join(AUDIO, "phrases.json"))))
    fps = tl["fps"]
    total = tl["total_frames"] / fps
    shots = []
    for s in tl["shots"]:
        t0 = s["start_frame"] / fps
        shots.append({"id": s["id"], "block": s["block"], "t0": t0, "t1": t0 + s["nframes"] / fps,
                      "transition_in": s.get("transition_in", "cut"), "title": s.get("title", ""),
                      "mood": s.get("mood", "")})
    blocks, order = {}, []
    for s in shots:
        if s["block"] not in blocks:
            blocks[s["block"]] = {"t0": s["t0"]}
            order.append(s["block"])
        blocks[s["block"]]["t1"] = s["t1"]
    phrases = ph["phrases"]
    for p in phrases:
        blocks[p["block"]].setdefault("phrases", []).append(p)
    return {"fps": fps, "total": total, "shots": shots, "shot": {s["id"]: s for s in shots},
            "blocks": blocks, "order": order, "phrases": phrases}


# ----------------------------------------------------------------------------- basic utils
def stereo(x):
    x = np.asarray(x)
    if x.dtype not in (np.float32, np.float64):
        x = x.astype(np.float64)
    return np.stack([x, x], 1) if x.ndim == 1 else x


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-12))


def undb(d):
    return 10 ** (np.asarray(d) / 20.0)


def fade(x, fin=0.0, fout=0.0, sr=SR):
    x = np.array(x, dtype=np.float64, copy=True)
    n = len(x)
    a, b = int(fin * sr), int(fout * sr)
    if a > 0:
        w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, min(a, n)))
        x[:len(w)] = (x[:len(w)].T * w).T
    if b > 0:
        w = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, min(b, n)))
        x[n - len(w):] = (x[n - len(w):].T * w).T
    return x


def place(buf, x, t, gain=1.0, sr=SR):
    """Add x into buf starting at time t (seconds); clips at buffer edges."""
    i = int(round(t * sr))
    x = np.asarray(x) * gain
    if buf.ndim == 2 and x.ndim == 1:
        x = np.stack([x, x], 1)
    a, b = max(0, i), min(len(buf), i + len(x))
    if b > a:
        buf[a:b] += x[a - i:b - i]
    return buf


def pan(x, p):
    """Equal-power pan of mono x; p in [-1, 1]."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def env_curve(points, n, sr=SR):
    """Piecewise-linear envelope from [(t, value), ...] sampled at n samples."""
    t = np.arange(n) / sr
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    return np.interp(t, ts, vs)


def smooth(x, sec, sr=SR):
    """One-pole smoothing forwards+backwards (zero phase)."""
    if sec <= 0:
        return x
    a = np.exp(-1.0 / (sec * sr))
    from scipy.signal import lfilter
    y = lfilter([1 - a], [1, -a], x)
    return lfilter([1 - a], [1, -a], y[::-1])[::-1]


# ----------------------------------------------------------------------------- filters (RBJ biquads)
def _biquad(kind, f, q=0.707, gain_db=0.0, sr=SR):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f / sr
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * q)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == "bp":
        b = [al, 0, -al]; a = [1 + al, -2 * cw, 1 - al]
    elif kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == "lowshelf":
        s = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + s), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - s)]
        a = [(A + 1) + (A - 1) * cw + s, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - s]
    elif kind == "highshelf":
        s = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + s), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - s)]
        a = [(A + 1) - (A - 1) * cw + s, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - s]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]; a = np.array(a) / a[0]
    return np.concatenate([b, a])[None, :]


def filt(x, kind, f, q=0.707, gain_db=0.0, order=1, sr=SR):
    """Apply an RBJ biquad (cascaded `order` times) along axis 0."""
    sos = np.concatenate([_biquad(kind, f, q, gain_db, sr)] * order, 0)
    return sosfilt(sos, x, axis=0)


def lp(x, f, order=1, q=0.707):
    return filt(x, "lp", f, q, order=order)


def hp(x, f, order=1, q=0.707):
    return filt(x, "hp", f, q, order=order)


def bp(x, f, q=1.0, order=1):
    return filt(x, "bp", f, q, order=order)


def tv_lowpass(x, fc, sr=SR):
    """Time-varying one-pole low-pass; fc is an array (Hz) of len(x) or scalar."""
    fc = np.broadcast_to(np.asarray(fc, dtype=np.float64), (len(x),))
    a = np.exp(-2 * np.pi * fc / sr)
    y = np.empty_like(x)
    s = np.zeros(x.shape[1:]) if x.ndim > 1 else 0.0
    # vectorised in chunks: within a chunk use a fixed coefficient (chunk = 64 samples)
    from scipy.signal import lfilter
    C = 256
    zi = None
    for i in range(0, len(x), C):
        ai = a[min(i + C // 2, len(x) - 1)]
        seg = x[i:i + C]
        if zi is None:
            zi = np.zeros((1,) + seg.shape[1:])
        y[i:i + C], zi = lfilter([1 - ai], [1, -ai], seg, axis=0, zi=zi)
    return y


# ----------------------------------------------------------------------------- noise & reverb
def noise(n, rng, color="white"):
    w = rng.standard_normal(n)
    if color == "white":
        return w
    f = np.fft.rfftfreq(n, 1 / SR)
    F = np.fft.rfft(w)
    f[0] = f[1]
    if color == "pink":
        F /= np.sqrt(f)
    elif color == "brown":
        F /= f
    y = np.fft.irfft(F, n)
    return y / (np.std(y) + 1e-12)


def hall_ir(rt60=3.0, predelay=0.03, length=None, seed=7, bright=1.0, er=True, width=1.0):
    """Synthetic stereo hall impulse response.

    Band-wise exponentially decaying noise (high bands decay faster), sparse early reflections,
    smooth onset, decorrelated L/R. Normalised to unit energy.
    """
    rng = np.random.default_rng(seed)
    length = length or rt60 * 1.25
    n = int(length * SR)
    t = np.arange(n) / SR
    bands = [(20, 250, 1.15), (250, 1000, 1.0), (1000, 4000, 0.75), (4000, 9000, 0.5 * bright), (9000, 20000, 0.3 * bright)]
    out = np.zeros((n, 2))
    for ch in range(2):
        acc = np.zeros(n)
        w = rng.standard_normal(n)
        F = np.fft.rfft(w)
        f = np.fft.rfftfreq(n, 1 / SR)
        for lo, hi, k in bands:
            m = (f >= lo) & (f < hi)
            if not m.any():
                continue
            sig = np.fft.irfft(F * m, n)
            rt = max(0.15, rt60 * k)
            acc += sig * np.exp(-6.91 * t / rt)
        # build-up of diffuse field
        acc *= 1 - np.exp(-t / 0.025)
        out[:, ch] = acc
    if er:
        for _ in range(18):
            d = rng.uniform(0.004, 0.09)
            g = rng.uniform(0.15, 0.5) * np.exp(-d / 0.05)
            i = int(d * SR)
            out[i, 0] += g * rng.choice([-1, 1]) * 4
            out[int((d + rng.uniform(0.0005, 0.004)) * SR), 1] += g * rng.choice([-1, 1]) * 4
    # stereo width
    mid = (out[:, 0] + out[:, 1]) / 2
    side = (out[:, 0] - out[:, 1]) / 2 * width
    out = np.stack([mid + side, mid - side], 1)
    out = np.concatenate([np.zeros((int(predelay * SR), 2)), out], 0)
    out = fade(out, 0, min(0.3, length * 0.2))
    return out / np.sqrt(np.sum(out ** 2) / 2)


def reverb(x, ir, wet=0.3, dry=1.0):
    """Convolution reverb (true-ish stereo: L->L, R->R with decorrelated IR channels)."""
    x = stereo(x)
    y = np.zeros_like(x)
    for c in range(2):
        y[:, c] = oaconvolve(x[:, c], ir[:, c], mode="full")[:len(x)]
    return dry * x + wet * y


# ----------------------------------------------------------------------------- dynamics & loudness
def loudness(x):
    """Integrated loudness (BS.1770-4, pyloudnorm)."""
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    x = np.asarray(x)
    return meter.integrated_loudness(x if x.ndim == 1 else x)


def true_peak_db(x, os_factor=4):
    return 20 * np.log10(max(float(peak_envelope(x, os_factor).max()), 1e-12))


def peak_envelope(x, os_factor=4, block=10 * SR):
    """Per-sample |x| maximum over channels and 4x-oversampled inter-sample peaks (chunked)."""
    x = stereo(x)
    n = len(x)
    pk = np.empty(n, dtype=np.float32)
    pad = 64
    for i in range(0, n, block):
        a, b = max(0, i - pad), min(n, i + block + pad)
        up = np.abs(resample_poly(x[a:b], os_factor, 1, axis=0)).max(1)
        up = up[: (b - a) * os_factor].reshape(b - a, os_factor).max(1)
        pk[i:min(n, i + block)] = np.maximum(up[i - a:i - a + min(block, n - i)],
                                             np.abs(x[i:i + block]).max(1))
    return pk


def limiter(x, ceiling_db=-1.2, lookahead=0.004, release=0.12, os_factor=4):
    """Look-ahead brickwall limiter on the 4x-oversampled peak envelope (approx. true-peak)."""
    x = stereo(x)
    ceil = undb(ceiling_db)
    pk = peak_envelope(x, os_factor)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9)).astype(np.float64)
    del pk
    la = max(1, int(lookahead * SR))
    from scipy.ndimage import minimum_filter1d
    from scipy.signal import lfilter
    # H[j] <= need[i] for every i within +-la of j, so any average of H over a window of
    # half-width la never exceeds the required gain at the window centre.
    H = minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    del need
    a = np.exp(-1.0 / (release * SR))
    sm = 1 - lfilter([1 - a], [1, -a], 1 - H)        # slow release (lagging smoother)
    G0 = np.minimum(H, sm)
    del H, sm
    k = np.hanning(2 * la + 1); k /= k.sum()
    from scipy.signal import oaconvolve
    gain = oaconvolve(np.pad(G0, la, mode="edge"), k, mode="valid")   # smooth attack (look-ahead)
    y = (x * gain[:, None]).astype(np.float32)
    return y, gain.astype(np.float32)


def write(path, x, subtype="FLOAT"):
    import soundfile as sf
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.asarray(x, dtype=np.float32), SR, subtype=subtype)


def read(path, dtype="float32"):
    import soundfile as sf
    x, sr = sf.read(path, always_2d=False, dtype=dtype)
    if sr != SR:
        from math import gcd
        g = gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g, axis=0)
    return x
