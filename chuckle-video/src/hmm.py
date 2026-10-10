"""A soft, breathy, thoughtful 'hmm' (closed-mouth nasal hum) for the therapist."""
import numpy as np
from scipy import signal


def airy_hmm(sr=24000, dur=0.85, f_start=228, seed=3):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * sr)) / sr
    u = t / dur
    # thoughtful contour: gentle dip, then a small lift at the end
    f0 = f_start * (1 - 0.09 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) + 0.05 * np.clip((u - 0.65) / 0.35, 0, 1))
    f0 *= 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
    ph = 2 * np.pi * np.cumsum(f0) / sr
    src = sum((k ** -1.7) * np.sin(k * ph) for k in range(1, 25))
    breath = rng.standard_normal(len(t))
    # aspirated 'h' onset, then breathy voicing
    h_env = np.exp(-((t - 0.05) / 0.045) ** 2)
    v_env = np.clip((t - 0.06) / 0.08, 0, 1) * np.clip((dur - t) / 0.22, 0, 1)
    x = src * v_env + breath * (0.22 * v_env + 0.9 * h_env)
    def pk(y, f, q):
        b, a = signal.iirpeak(f, q, fs=sr)
        return signal.lfilter(b, a, y)
    # closed-mouth nasal murmur: strong low resonance, weak upper ones
    y = 1.0 * pk(x, 270, 2.5) + 0.25 * pk(x, 1050, 4) + 0.12 * pk(x, 2300, 5)
    y = signal.sosfilt(signal.butter(2, 2600, "low", fs=sr, output="sos"), y)
    y += 0.15 * signal.sosfilt(signal.butter(2, [1500, 5000], "band", fs=sr, output="sos"), breath) * h_env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)
