"""Small numpy/scipy audio toolkit: STFT, whisper effect, reverb, filters."""
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy import signal


def stft(x, n=1024, hop=256):
    win = np.hanning(n).astype(np.float64)
    pad = np.concatenate([np.zeros(n), x, np.zeros(n)])
    frames = 1 + (len(pad) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(frames)[:, None]
    return np.fft.rfft(pad[idx] * win, axis=1), len(x)


def istft(X, length, n=1024, hop=256):
    win = np.hanning(n)
    frames = np.fft.irfft(X, n=n, axis=1) * win
    out = np.zeros(hop * (len(frames) - 1) + n)
    norm = np.zeros_like(out)
    for i, f in enumerate(frames):
        out[i * hop:i * hop + n] += f
        norm[i * hop:i * hop + n] += win ** 2
    out /= np.maximum(norm, 1e-6)
    return out[n:n + length]


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def whisperize(x, sr, seed=0, smooth_hz=260, tilt=0.35):
    """Keep the voice's spectral envelope, replace the excitation with noise."""
    rng = np.random.default_rng(seed)
    X, n = stft(x)
    mag = np.abs(X)
    bins = max(3, int(smooth_hz / (sr / 1024)))
    k = np.hanning(bins * 2 + 1)
    k /= k.sum()
    env = np.apply_along_axis(lambda r: np.convolve(r, k, mode="same"), 1, mag)
    freqs = np.fft.rfftfreq(1024, 1 / sr)
    env *= (1 + tilt * (freqs / 3000.0))[None, :]
    ph = rng.uniform(0, 2 * np.pi, X.shape)
    y = istft(env * np.exp(1j * ph), n)
    return y * (rms(x) / rms(y))


def make_ir(sr, t60=2.0, damp=0.6, predelay=0.015, seed=1, width=1.0):
    """Stereo reverb impulse response with frequency-dependent decay."""
    rng = np.random.default_rng(seed)
    n = int(sr * t60 * 1.1)
    out = []
    for ch in range(2):
        nfft, hop = 512, 128
        frames = n // hop + 1
        freqs = np.fft.rfftfreq(nfft, 1 / sr)
        t60f = t60 * (1 - damp * np.sqrt(freqs / (sr / 2))) + 0.04
        times = np.arange(frames) * hop / sr
        mag = 10 ** (-3 * times[:, None] / t60f[None, :])
        ph = rng.uniform(0, 2 * np.pi, mag.shape)
        ir = istft(mag * np.exp(1j * ph), n, nfft, hop)
        ir = np.pad(ir, (0, max(0, n - len(ir))))[:n]
        ir *= np.minimum(1, np.arange(n) / (0.004 * sr))  # soft onset
        ir = np.concatenate([np.zeros(int(predelay * sr)), ir])
        out.append(ir / np.sqrt(np.sum(ir ** 2)))
    L, R = out
    mid, side = (L + R) / 2, (L - R) / 2 * width
    return np.stack([mid + side, mid - side], 1)


def reverb(x, ir, wet=0.3, dry=1.0):
    """x mono or stereo; returns stereo, same length + tail."""
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    tail = len(ir)
    out = np.zeros((len(x) + tail - 1, 2))
    for c in range(2):
        out[:, c] = signal.oaconvolve(x[:, c], ir[:, c]) * wet
        out[:len(x), c] += x[:, c] * dry
    return out


def lowpass(x, sr, hz, order=2):
    sos = signal.butter(order, hz, "low", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def highpass(x, sr, hz, order=2):
    sos = signal.butter(order, hz, "high", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def bandpass(x, sr, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "band", fs=sr, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def ffmpeg_filter(x, sr, af):
    """Run a mono float signal through an ffmpeg audio filter chain."""
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/i.wav", x.astype(np.float32), sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/i.wav", "-af", af,
                        "-ar", str(sr), "-ac", "1", "-c:a", "pcm_f32le", f"{d}/o.wav"], check=True)
        y, _ = sf.read(f"{d}/o.wav", dtype="float64")
    return y


def pitch(x, sr, ratio):
    """Pitch-shift (formants move too) keeping duration."""
    y = ffmpeg_filter(x, sr, f"rubberband=pitch={ratio}:transients=smooth")
    return y[:len(x)] if len(y) >= len(x) else np.pad(y, (0, len(x) - len(y)))


def resample(x, sr_in, sr_out):
    from math import gcd
    g = gcd(sr_in, sr_out)
    return signal.resample_poly(x, sr_out // g, sr_in // g, axis=0)


def fade(x, sr, fin=0.01, fout=0.01):
    x = x.copy()
    a, b = int(fin * sr), int(fout * sr)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim > 1 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim > 1 else np.linspace(1, 0, b)
    return x
