"""Small DSP helpers: synthetic-impulse reverb, filters, resampling."""
import numpy as np
from scipy import signal

_ir_cache = {}


def butter(x, sr, kind, f, order=2):
    if kind in ("bandpass", "bandstop"):
        sos = signal.butter(order, [f[0] / (sr / 2), f[1] / (sr / 2)], btype=kind, output="sos")
    else:
        sos = signal.butter(order, f / (sr / 2), btype=kind, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def make_ir(sr, rt60=1.2, predelay=0.012, damp=6000, early=(), seed=1, stereo=True, width=1.0):
    key = (sr, rt60, predelay, damp, tuple(early), seed, stereo, width)
    if key in _ir_cache:
        return _ir_cache[key]
    rng = np.random.default_rng(seed)
    n = int(sr * (predelay + rt60 * 1.1))
    t = np.arange(n) / sr
    decay = np.exp(-6.91 * np.maximum(t - predelay, 0) / rt60)
    decay[t < predelay] = 0
    chans = []
    for c in range(2 if stereo else 1):
        noise = rng.standard_normal(n)
        # high frequencies decay faster: crossfade a bright and a dark tail
        dark = butter(noise, sr, "lowpass", damp * 0.35)
        bright = butter(noise, sr, "lowpass", damp)
        mixw = np.exp(-t / (rt60 * 0.25))
        tail = (bright * mixw + dark * (1 - mixw)) * decay
        for (dt, g) in early:
            i = int((predelay + dt * (1 + 0.07 * c)) * sr)
            if i < n:
                tail[i] += g * (1 if c == 0 else 0.9)
        tail /= np.sqrt(np.sum(tail ** 2)) + 1e-9
        chans.append(tail)
    ir = np.stack(chans, axis=1) if stereo else chans[0]
    if stereo and width != 1.0:
        mid = (ir[:, 0] + ir[:, 1]) / 2
        side = (ir[:, 0] - ir[:, 1]) / 2
        ir = np.stack([mid + side * width, mid - side * width], axis=1)
    _ir_cache[key] = ir
    return ir


def reverb(x, sr, wet=0.25, **kw):
    """x mono -> stereo (n + tail, 2)."""
    ir = make_ir(sr, **kw)
    out_l = signal.fftconvolve(x, ir[:, 0])
    out_r = signal.fftconvolve(x, ir[:, 1])
    dry = np.zeros_like(out_l)
    dry[: len(x)] = x
    return np.stack([dry * (1 - wet * 0.5) + out_l * wet, dry * (1 - wet * 0.5) + out_r * wet], axis=1)


def resample(x, sr_in, sr_out):
    if sr_in == sr_out:
        return x
    g = np.gcd(sr_in, sr_out)
    return signal.resample_poly(x, sr_out // g, sr_in // g, axis=0)


ENV = {
    # name: reverb kwargs + wet + optional filters
    "dry": dict(wet=0.08, rt60=0.35, predelay=0.004, damp=7000),
    "narr": dict(wet=0.10, rt60=0.6, predelay=0.006, damp=6500),
    "room_warm": dict(wet=0.20, rt60=0.7, predelay=0.008, damp=5000, early=((0.011, 0.5), (0.019, 0.35))),
    "street": dict(wet=0.16, rt60=0.9, predelay=0.02, damp=5000, early=((0.045, 0.45), (0.09, 0.25))),
    "cell": dict(wet=0.30, rt60=1.05, predelay=0.006, damp=4200, early=((0.007, 0.6), (0.013, 0.5), (0.021, 0.35))),
    "memory": dict(wet=0.42, rt60=1.8, predelay=0.03, damp=3500),
    "desert": dict(wet=0.10, rt60=0.5, predelay=0.03, damp=6000),
    "divine": dict(wet=0.55, rt60=3.6, predelay=0.045, damp=6000, width=1.3),
    "soft_divine": dict(wet=0.40, rt60=2.6, predelay=0.03, damp=6500, width=1.2),
    "outdoor": dict(wet=0.12, rt60=0.8, predelay=0.03, damp=6000),
}


def place_voice(x, sr, env, fx=None):
    """Return stereo voice with environment treatment."""
    kw = dict(ENV.get(env, ENV["dry"]))
    wet = kw.pop("wet")
    if fx == "memory":
        x = butter(x, sr, "bandpass", (260, 4200))
        kw = dict(ENV["memory"]); wet = kw.pop("wet")
        x = x * 0.8
    if fx in ("divine", "soft_divine"):
        kw = dict(ENV[fx]); wet = kw.pop("wet")
        # gentle doubling for a sense of presence
        d = int(0.018 * sr)
        x = x + 0.25 * np.concatenate([np.zeros(d), x[:-d]])
    return reverb(x, sr, wet=wet, **kw)
