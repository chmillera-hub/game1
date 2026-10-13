"""Deterministic sound-effect synthesis for "Brindle Cross".

Public API
----------
    sfx(name, out_wav, duration=None, seed=0, **params) -> dict

Writes a 48 kHz stereo float32 WAV and returns
    {'path', 'duration', 'sync', 'kind', 'peak_db', 'lufs_m', 'lufs_i', 'mix_gain_db'}

* sync         -- time (s) in the file of the main event (impact / first step / first
                  syllable); place the file at  t_event - sync  on the timeline.
* kind         -- 'oneshot' (peak-normalised to -1 dBFS, 10 ms of lead silence, tail
                  trimmed at about -70 dB), 'seq' (a timed sequence, peak-normalised, exact
                  duration) or 'bed' (exact duration, normalised to -23 LUFS integrated,
                  peak capped at -1 dBFS).
* mix_gain_db  -- suggested gain to apply in the mix when dialogue sits at about -16 LUFS.
                  It is measured on the rendered file (max momentary loudness for
                  one-shots/seq, integrated loudness for beds) against TARGETS below.
* lufs_m/lufs_i -- BS.1770 max-momentary / gated integrated loudness of the file.

Common params: gain_db (extra gain applied to the file, default 0), mix=True (bake the
suggested mix gain into the file, so it can be summed at unity; mix_gain_db then
returns 0), fade_in / fade_out (seconds, beds/seq only).

Everything is a pure function of (name, seed, duration, params): numpy RNGs are seeded
with crc32(name) and seed; fluidsynth, rubberband and Kokoro are deterministic. The WAV
writer adds no timestamped PEAK chunk, so identical arguments give byte-identical files.
Unknown params raise TypeError.

Ingredients: numpy/scipy modal, noise and granular DSP for most effects; FluidR3 GM via
fluidsynth for 'woodblock', 'cymbal_tap' and the celesta in 'gas_lamp_on'; Kokoro TTS
(tts.py next to this file) plus rubberband for the laughs.

    python3 sfx_lib.py OUT_DIR [name ...]   # render the effects and print levels
"""
from __future__ import annotations

import functools
import os
import struct
import subprocess
import sys
import tempfile
import zlib

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.interpolate import PchipInterpolator
from scipy.linalg import solve_toeplitz

SR = 48000
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
PEAK_DBFS = -1.0
BED_REF_LUFS = -23.0
LEAD = 0.01          # silence before every one-shot (fade-in happens inside it)

# ----------------------------------------------------------------------------- basics


def _n(sec):
    return max(0, int(round(sec * SR)))


def _t(n):
    return np.arange(n) / SR


def _db(x):
    return 10.0 ** (x / 20.0)


def _sos(btype, fc, order):
    nyq = SR / 2.0
    if btype in ('bandpass', 'bandstop'):
        lo, hi = fc
        lo = min(max(lo, 5.0), nyq * 0.9)
        hi = min(max(hi, lo * 1.01), nyq * 0.95)
        return signal.butter(order, [lo / nyq, hi / nyq], btype=btype, output='sos')
    return signal.butter(order, min(max(fc, 5.0), nyq * 0.95) / nyq, btype=btype, output='sos')


def lp(x, fc, order=2):
    return signal.sosfilt(_sos('lowpass', fc, order), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos('highpass', fc, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos('bandpass', (lo, hi), order), x, axis=0)


def peak(x, f, q, gain=1.0):
    """Add a resonant peak (iirpeak, unity gain at f) scaled by gain."""
    b, a = signal.iirpeak(min(f, SR * 0.45), q, fs=SR)
    return x + gain * signal.lfilter(b, a, x, axis=0)


def reson(x, f, q):
    b, a = signal.iirpeak(min(f, SR * 0.45), q, fs=SR)
    return signal.lfilter(b, a, x, axis=0)


def _pn(x):
    m = np.max(np.abs(x)) if len(x) else 0.0
    return x / m if m > 0 else x


def _unit(x):
    s = np.std(x)
    return x / s if s > 0 else x


def _conv(a, b):
    if len(a) == 0 or len(b) == 0:
        return np.zeros(0)
    if min(len(a), len(b)) < 64:
        return np.convolve(a, b)
    return signal.fftconvolve(a, b)


def _place(dst, src, t, gain=1.0):
    i = _n(t) if not isinstance(t, (int, np.integer)) else int(t)
    if i >= len(dst) or len(src) == 0:
        return
    if i < 0:
        src = src[-i:]
        i = 0
    m = min(len(src), len(dst) - i)
    s = src[:m]
    if dst.ndim == 2 and s.ndim == 1:
        s = s[:, None]
    dst[i:i + m] += gain * s


def _st(y):
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        return np.stack([y, y], axis=1)
    return y


def _pan(x, p):
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2.0)


def _fade(x, fi, fo):
    x = x.copy()
    ni, no = min(_n(fi), len(x)), min(_n(fo), len(x))
    if ni > 0:
        w = np.sin(0.5 * np.pi * np.arange(ni) / ni) ** 2
        x[:ni] *= w if x.ndim == 1 else w[:, None]
    if no > 0:
        w = np.cos(0.5 * np.pi * (np.arange(no) + 1) / no) ** 2
        x[len(x) - no:] *= w if x.ndim == 1 else w[:, None]
    return x


# ----------------------------------------------------------------------------- noise / envelopes


def _pink(n, rng, alpha=1.0, fmin=12.0):
    """Coloured gaussian noise, PSD ~ 1/f^alpha, unit std."""
    if n <= 0:
        return np.zeros(0)
    from scipy.fft import irfft, next_fast_len
    m = next_fast_len(n, real=True)
    k = m // 2 + 1
    X = rng.standard_normal(k) + 1j * rng.standard_normal(k)
    f = np.fft.rfftfreq(m, 1.0 / SR)
    g = 1.0 / np.maximum(f, fmin) ** (alpha / 2.0)
    g[0] = 0.0
    y = irfft(X * g, n=m)[:n]
    return _unit(y)


def _smooth(n, rate, rng, lo=0.0, hi=1.0):
    """Smooth random curve (PCHIP through random knots at `rate` Hz) in [lo, hi]."""
    if n <= 0:
        return np.zeros(0)
    dur = n / SR
    k = int(np.ceil(dur * rate)) + 4
    xs = (np.arange(k) - 1.5) / rate
    v = rng.uniform(lo, hi, k)
    return PchipInterpolator(xs, v)(_t(n))


def _curve(n, times, vals):
    times = np.asarray(times, float)
    return PchipInterpolator(times, np.asarray(vals, float), extrapolate=False)(np.clip(_t(n), times[0], times[-1]))


def _burst(rng, dur, tau, att=0.0):
    """White noise with exponential decay (tau, s) after an optional sin^2 attack."""
    n = _n(dur)
    t = _t(n)
    env = np.exp(-np.maximum(t - att, 0) / max(tau, 1e-5))
    if att > 0:
        env = np.where(t < att, np.sin(0.5 * np.pi * t / att) ** 2, env)
    return rng.standard_normal(n) * env


def _exc(rng, width_ms=0.5, noise=0.0, tau_ms=0.5):
    """Impact excitation: unit-area half-sine (contact time width_ms) + decaying noise
    of unit energy scaled by `noise`."""
    w = max(1, _n(width_ms / 1000.0))
    L = max(w, _n(6 * tau_ms / 1000.0) if noise else w)
    e = np.zeros(L)
    hs = np.sin(np.pi * (np.arange(w) + 0.5) / w)
    e[:w] = hs / hs.sum()
    if noise:
        nz = rng.standard_normal(L) * np.exp(-_t(L) / max(tau_ms / 1000.0, 1e-5))
        e += noise * nz / np.sqrt(np.sum(nz ** 2))
    return e


def _modal(freqs, t60, amps, dur, split=None):
    """Sum of exponentially decaying sines (impulse response of a modal body)."""
    n = _n(dur)
    y = np.zeros(n)
    for i, (f, T, a) in enumerate(zip(freqs, t60, amps)):
        if f <= 0 or f >= 0.45 * SR or a == 0:
            continue
        m = min(n, _n(T * 1.8) + 1)
        t = _t(m)
        env = np.exp(-6.9078 * t / T)
        d = 0.0 if split is None else 0.5 * split[i]
        if d:
            y[:m] += 0.5 * a * env * (np.sin(2 * np.pi * (f - d) * t) + np.sin(2 * np.pi * (f + d) * t))
        else:
            y[:m] += a * env * np.sin(2 * np.pi * f * t)
    return y


def _crackle(rng, n, rate, f_lo, f_hi, tau_ms=(0.2, 1.5), spread=0.7, K=10, tilt=0.0):
    """Poisson stream of tiny noise grains, each band-limited to a random band in
    [f_lo, f_hi]; `rate` (events/s) may be an array of length n."""
    rate = np.broadcast_to(np.asarray(rate, float), (n,))
    idx = np.nonzero(rng.random(n) < rate / SR)[0]
    if len(idx) == 0:
        return np.zeros(n)
    edges = np.geomspace(f_lo, f_hi, K + 1)
    pad = _n(tau_ms[1] * 6 / 1000.0) + 2
    acc = np.zeros((K, n + pad))
    bins = rng.integers(0, K, len(idx))
    amps = np.exp(rng.normal(0, spread, len(idx)))
    taus = np.exp(rng.uniform(np.log(tau_ms[0]), np.log(tau_ms[1]), len(idx))) / 1000.0
    for i, k, a, tau in zip(idx, bins, amps, taus):
        L = max(4, _n(tau * 5))
        acc[k, i:i + L] += a * rng.standard_normal(L) * np.exp(-_t(L) / tau)
    y = np.zeros(n + pad)
    for k in range(K):
        if np.any(acc[k]):
            fc = np.sqrt(edges[k] * edges[k + 1])
            y += bp(acc[k], edges[k], edges[k + 1], 2) * np.sqrt(edges[k + 1] / edges[k] - 1) * (fc / 1000.0) ** (-tilt / 2)
    return y[:n]


def _sinesweep(f, amps=(1.0,)):
    ph = 2 * np.pi * np.cumsum(f) / SR
    return sum(a * np.sin((k + 1) * ph) for k, a in enumerate(amps))


# ----------------------------------------------------------------------------- reverb

_REV = {
    # cold small-town square: stone facades -> slap echoes, short dark tail
    'square': dict(rt60=1.1, pre=0.012, damp=2800, er_lp=3500, wet=-17.0,
                   er=[(0.043, .28, -.5), (0.068, .22, .6), (0.101, .15, -.3), (0.147, .10, .4),
                       (0.205, .07, -.6), (0.290, .045, .2)]),
    # stone clock chamber in the tower
    'stone_room': dict(rt60=0.75, pre=0.004, damp=3200, er_lp=5000, wet=-9.0,
                       er=[(0.009, .45, -.4), (0.016, .38, .5), (0.024, .30, -.2), (0.035, .22, .3),
                           (0.048, .15, -.5)]),
    'shop': dict(rt60=0.5, pre=0.003, damp=5000, er_lp=7000, wet=-13.0,
                 er=[(0.005, .35, .3), (0.009, .28, -.4), (0.014, .20, .5), (0.021, .14, -.2)]),
    'bakery': dict(rt60=0.8, pre=0.004, damp=3500, er_lp=6000, wet=-10.0,
                   er=[(0.007, .4, .3), (0.012, .3, -.4), (0.019, .25, .2), (0.028, .18, -.3)]),
    'tower': dict(rt60=3.0, pre=0.01, damp=1800, er_lp=3000, wet=-5.0,
                  er=[(0.014, .5, -.3), (0.023, .4, .4), (0.037, .3, -.1), (0.052, .22, .3)]),
    'close': dict(rt60=0.35, pre=0.002, damp=6000, er_lp=8000, wet=-24.0,
                  er=[(0.004, .2, .2), (0.007, .15, -.3)]),
}


def _ir(rng, rt60, pre, er, damp, er_lp, **_):
    L = _n(pre + rt60 * 1.15 + 0.02)
    t = _t(L)
    npre = _n(pre)
    tail = np.zeros((L, 2))
    for c in range(2):
        w = rng.standard_normal(L)
        y = (lp(w, 300) * 10 ** (-3 * t / (rt60 * 1.3)) + bp(w, 300, damp) * 10 ** (-3 * t / rt60)
             + 0.7 * hp(w, damp) * 10 ** (-3 * t / (rt60 * 0.35)))
        y *= 1 - np.exp(-t / 0.015)
        tail[npre:, c] = y[:L - npre]
    tail /= np.sqrt(np.sum(tail ** 2) / 2) + 1e-12
    eri = np.zeros((L, 2))
    for d, g, p in er:
        i = _n(d)
        if i < L:
            a = (p + 1) * np.pi / 4
            eri[i, 0] += g * np.cos(a) * np.sqrt(2)
            eri[i, 1] += g * np.sin(a) * np.sqrt(2)
    eri = lp(eri, er_lp, 2)
    return tail, eri


def _reverb(x, preset, rng, wet_db=None, er_scale=1.0):
    p = _REV[preset]
    tail, eri = _ir(rng, **p)
    wet = _db(p['wet'] if wet_db is None else wet_db)
    xs = _st(x)
    L = len(xs) + len(tail) - 1
    out = np.zeros((L, 2))
    out[:len(xs)] += xs
    for c in range(2):
        out[:, c] += wet * signal.fftconvolve(xs[:, c], tail[:, c])[:L]
        if er_scale:
            out[:, c] += er_scale * signal.fftconvolve(xs[:, c], eri[:, c])[:L]
    return out


# ----------------------------------------------------------------------------- loudness


def _kweight(x):
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def loudness(x):
    """(max momentary LUFS, gated integrated LUFS) per BS.1770 (48 kHz)."""
    x = _st(x)
    z = _kweight(x)
    win, hop = _n(0.4), _n(0.1)
    if len(z) < win:
        z = np.concatenate([z, np.zeros((win - len(z), 2))])
    c = np.concatenate([np.zeros((1, 2)), np.cumsum(z ** 2, axis=0)])
    starts = np.arange(0, len(z) - win + 1, hop)
    ms = np.sum((c[starts + win] - c[starts]) / win, axis=1)
    lm = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[lm > -70]
    if len(g) == 0:
        return -99.0, -99.0
    li = -0.691 + 10 * np.log10(np.mean(g))
    g2 = g[-0.691 + 10 * np.log10(g) > li - 10]
    li = -0.691 + 10 * np.log10(np.mean(g2))
    return float(lm.max()), float(li)


# ----------------------------------------------------------------------------- external tools


def _vlq(v):
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append(0x80 | (v & 0x7F))
        v >>= 7
    return bytes(reversed(out))


def _midi(notes, end, programs=None):
    """notes: [(t, dur, ch, note, vel)], 1 beat = 1 s."""
    ppq = 960
    ev = [(0, 0, bytes([0xC0 | ch, prog])) for ch, prog in (programs or {}).items()]
    for (t, d, ch, nt, vel) in notes:
        ev.append((int(round(t * ppq)), 1, bytes([0x90 | ch, nt, vel])))
        ev.append((int(round((t + d) * ppq)), 0, bytes([0x80 | ch, nt, 0])))
    ev.append((int(round(end * ppq)), 2, bytes([0xB0, 121, 0])))
    ev.sort(key=lambda e: (e[0], e[1]))
    trk = bytearray(b'\x00\xff\x51\x03' + (1000000).to_bytes(3, 'big'))
    last = 0
    for tk, _, msg in ev:
        trk += _vlq(tk - last) + msg
        last = tk
    trk += b'\x00\xff\x2f\x00'
    return b'MThd' + struct.pack('>IHHH', 6, 0, 1, ppq) + b'MTrk' + struct.pack('>I', len(trk)) + bytes(trk)


def _fluid(notes, end, programs=None, gain=0.5):
    """Render GM notes with FluidR3 (reverb/chorus off). Returns stereo float64."""
    with tempfile.TemporaryDirectory() as d:
        mp, wp = os.path.join(d, 'a.mid'), os.path.join(d, 'a.wav')
        with open(mp, 'wb') as fh:
            fh.write(_midi(notes, end, programs))
        subprocess.run(['fluidsynth', '-ni', '-q', '-g', str(gain), '-r', str(SR), '-R', '0', '-C', '0',
                        '-O', 'float', '-T', 'wav', '-F', wp, SF2, mp], check=True, capture_output=True)
        y, sr = sf.read(wp, dtype='float64', always_2d=True)
    assert sr == SR
    return y[:_n(end)]


def _rubberband(x, sr, semis, formant=True):
    if abs(semis) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'a.wav'), os.path.join(d, 'b.wav')
        sf.write(a, x.astype(np.float32), sr, subtype='FLOAT')
        cmd = ['rubberband', '-q', '-3', '-p', '%.4f' % semis, '-t', '1']
        if formant:
            cmd.append('-F')
        subprocess.run(cmd + [a, b], check=True, capture_output=True)
        y, _ = sf.read(b, dtype='float64')
    if y.ndim > 1:
        y = y.mean(1)
    if len(y) < len(x):
        y = np.concatenate([y, np.zeros(len(x) - len(y))])
    return y[:len(x)]


_TTS = None


def _tts():
    global _TTS
    if _TTS is None:
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        import tts as _m
        _TTS = _m
    return _TTS


def _kokoro(ph, mix, speed):
    """Raw Kokoro from a phoneme string. Returns (wav@24k, chars, token edges in s)."""
    T = _tts()
    sess, _, tok = T._load()
    chars = [c for c in ph if c in tok.vocab]
    ids = [tok.vocab[c] for c in chars]
    st = T.style_vec(mix, len(ids))
    wav, dur = sess.run(None, {'input_ids': np.array([[0, *ids, 0]], dtype=np.int64), 'style': st,
                               'speed': np.array([speed], dtype=np.float32)})
    wav = wav[0].astype(np.float64)
    dur = np.asarray(dur).ravel().astype(np.float64)
    edges = np.concatenate([[0.0], np.cumsum(dur)]) * (len(wav) / dur.sum()) / 24000.0
    return wav, chars, edges


# ----------------------------------------------------------------------------- registry

_FX = {}


def _fx(name, kind='oneshot', target=-24.0, meas=None, doc=''):
    def deco(fn):
        _FX[name] = dict(fn=fn, kind=kind, target=target, meas=meas or ('i' if kind == 'bed' else 'm'), doc=doc)
        return fn
    return deco


def effects():
    """{name: (kind, one-line doc)}"""
    return {k: (v['kind'], v['doc']) for k, v in _FX.items()}


def _target(name, params):
    t = _FX[name]['target']
    return t(params) if callable(t) else t


def _trim_tail(y, rel_db=-70.0, keep=0.03):
    m = np.abs(y).max(axis=1)
    fr = _n(0.01)
    nf = len(m) // fr
    if nf < 2:
        return y
    e = np.sqrt(np.mean(m[:nf * fr].reshape(nf, fr) ** 2, axis=1))
    thr = e.max() * _db(rel_db)
    idx = np.nonzero(e > thr)[0]
    end = min(len(y), (idx[-1] + 1) * fr + _n(keep)) if len(idx) else len(y)
    return y[:end]


def _write_wav(path, y):
    """Byte-deterministic 48 kHz float32 WAV (WAVE_FORMAT_IEEE_FLOAT, 18-byte fmt with
    cbSize=0, fact chunk, no timestamped PEAK chunk) -- identical bytes for identical
    samples, and sox reads it without the 'missing extended part' warning."""
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        y = y[:, None]
    nch = y.shape[1]
    data = y.astype('<f4').tobytes()
    fmt = struct.pack('<HHIIHHH', 3, nch, SR, SR * nch * 4, nch * 4, 32, 0)
    chunks = (b'fmt ' + struct.pack('<I', len(fmt)) + fmt +
              b'fact' + struct.pack('<II', 4, y.shape[0]) +
              b'data' + struct.pack('<I', len(data)) + data)
    with open(path, 'wb') as fh:
        fh.write(b'RIFF' + struct.pack('<I', 4 + len(chunks)) + b'WAVE' + chunks)


def _fit(y, duration, min_fade=0.02):
    """Pad/cut to exact duration. Cutting through a loud tail uses a longer fade."""
    if duration is None:
        return y, min_fade
    n = _n(duration)
    if len(y) >= n:
        cut_level = np.sqrt(np.mean(y[max(0, n - _n(0.05)):n] ** 2)) + 1e-12
        # loudest 50 ms of the file (moving average via cumsum: O(n), not O(n*w))
        w = min(_n(0.05), len(y))
        c = np.concatenate([[0.0], np.cumsum(np.mean(y ** 2, axis=1))])
        ref = np.sqrt(max(0.0, np.max(c[w:] - c[:-w]) / max(w, 1))) + 1e-12 if w else 1e-12
        fo = min_fade
        if 20 * np.log10(cut_level / ref) > -45:
            fo = max(min_fade, min(1.5, 0.2 * duration))
        return y[:n], fo
    return np.concatenate([y, np.zeros((n - len(y), 2))]), min_fade


def sfx(name: str, out_wav: str, duration: float | None = None, seed: int = 0, **params) -> dict:
    """Render effect `name` to `out_wav` (48 kHz stereo float32). See module doc."""
    if name not in _FX:
        raise KeyError('unknown sfx %r; known: %s' % (name, ', '.join(sorted(_FX))))
    spec = _FX[name]
    gain_db = float(params.pop('gain_db', 0.0))
    mix = bool(params.pop('mix', False))
    fade_in = params.pop('fade_in', None)
    fade_out = params.pop('fade_out', None)
    rng = np.random.default_rng([zlib.crc32(name.encode()), int(seed) & 0xFFFFFFFF])
    y, sync = spec['fn'](rng, duration, **params)
    y = hp(_st(y), 15.0, 2)                       # DC / subsonic
    kind = spec['kind']
    if kind == 'oneshot':
        y = np.concatenate([np.zeros((_n(LEAD), 2)), y])
        sync += LEAD
        if duration is None:
            y = _trim_tail(y)
        y, fo = _fit(y, duration)
        y = _fade(y, 0.005, fo if fade_out is None else fade_out)
        y *= _db(PEAK_DBFS) / (np.abs(y).max() + 1e-12)
    else:
        y, fo = _fit(y, duration if duration is not None else len(y) / SR)
        y = _fade(y, 0.02 if fade_in is None else fade_in, max(fo, 0.02) if fade_out is None else fade_out)
        if kind == 'seq':
            y *= _db(PEAK_DBFS) / (np.abs(y).max() + 1e-12)
        else:
            y *= _db(BED_REF_LUFS - loudness(y)[1])
            pk = np.abs(y).max()
            if pk > _db(PEAK_DBFS):
                y *= _db(PEAK_DBFS) / pk
    lm, li = loudness(y)
    meas = lm if spec['meas'] == 'm' else li
    mg = _target(name, params) - meas
    g = gain_db + (mg if mix else 0.0)
    y *= _db(g)
    pk = np.abs(y).max()
    if pk > _db(PEAK_DBFS):
        y *= _db(PEAK_DBFS) / pk
        g += 20 * np.log10(_db(PEAK_DBFS) / pk)
    lm, li = loudness(y)
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    _write_wav(out_wav, y)
    return dict(path=out_wav, duration=len(y) / SR, sync=float(sync), kind=kind,
                peak_db=float(20 * np.log10(np.abs(y).max() + 1e-12)), lufs_m=lm, lufs_i=li,
                mix_gain_db=float(round(_target(name, params) - (lm if spec['meas'] == 'm' else li), 1)))


# ============================================================================= clock tower


def _tick_dry(rng, variant=0):
    s = (1.0 if variant % 2 == 0 else 0.935) * (1 + rng.normal(0, 0.004))
    f = np.array([176, 338, 521, 757, 1046, 1418, 1890, 2610, 3480]) * s
    T = [0.08, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
    a = np.array([0.3, 0.6, 1.0, 0.9, 0.7, 0.5, 0.35, 0.25, 0.12]) * rng.uniform(0.85, 1.15, 9)
    y = _conv(_exc(rng, 0.35, 0.3, 0.5), _modal(f, T, a, 0.3))
    k = bp(_burst(rng, 0.03, 0.004), 700, 3000) * 0.05
    y[:len(k)] += k
    return y


def _tick_space(rng, y, distance):
    y = _reverb(y, 'stone_room', rng)
    y = lp(y, 7000 - 3000 * distance, 2)
    y = hp(y, 110, 2)
    return _reverb(y, 'square', rng, wet_db=-16 + 4 * distance)


@_fx('tower_tick', target=-25.0, doc='heavy tower-clock tock across the square (variant=0 tick / 1 tock, distance 0..1)')
def _tower_tick(rng, duration, variant=0, distance=1.0):
    return _tick_space(rng, _tick_dry(rng, variant), distance), 0.0


@_fx('tower_ticks', kind='seq', target=-25.0, doc='bed of tower ticks every `interval` s (default 1.0) from `start`')
def _tower_ticks(rng, duration, interval=1.0, start=0.05, distance=1.0):
    duration = 10.0 if duration is None else duration
    dry = np.zeros(_n(duration + 0.5))
    var = [_tick_dry(rng, v % 2) for v in range(4)]
    k, t = 0, start
    while t < duration - 0.35:
        _place(dry, var[(k % 2) + 2 * int(rng.integers(0, 2))], t + rng.normal(0, 0.002), _db(rng.normal(0, 0.6)))
        t += interval
        k += 1
    return _tick_space(rng, dry, distance)[:_n(duration)], start


@_fx('clock_clunk', target=-20.0, doc='heavy clunk of the tower minute hand advancing (sync = main clunk)')
def _clock_clunk(rng, duration, distance=0.6):
    y = np.zeros(_n(1.2))
    rel = _conv(_exc(rng, 0.1, 0.3, 0.3), _modal([2650, 3920, 5230, 7100], [0.05, 0.04, 0.03, 0.02], [1, .7, .5, .3], 0.12))
    _place(y, rel, 0.0, 0.25)
    g = bp(rng.standard_normal(_n(0.07)), 1200, 4200) * np.sin(np.pi * np.linspace(0, 1, _n(0.07))) ** 2
    _place(y, g, 0.004, 0.02)
    t0 = 0.075
    f = np.array([64, 97, 143, 205, 288, 410, 590, 870, 1270, 1850, 2600]) * rng.uniform(0.98, 1.02)
    T = [0.30, 0.28, 0.27, 0.26, 0.24, 0.20, 0.18, 0.15, 0.12, 0.08, 0.06]
    a = np.array([0.15, 0.3, 0.55, 0.8, 1.0, 0.9, 0.75, 0.6, 0.45, 0.3, 0.15]) * rng.uniform(0.85, 1.15, 11)
    ir = _modal(f, T, a, 0.9, [0, 0, 0.8, 0, 1.3, 0, 2.1, 0, 3.0, 0, 0])
    _place(y, _conv(_exc(rng, 0.9, 0.3, 0.6), ir), t0)
    _place(y, _conv(_exc(rng, 0.6, 0.3, 0.4), ir), t0 + 0.042, 0.22)
    _place(y, _conv(_exc(rng, 0.6, 0.3, 0.4), ir), t0 + 0.071, 0.09)
    y = _reverb(y, 'stone_room', rng)
    y = hp(lp(y, 8000 - 3000 * distance, 2), 45, 2)
    return _reverb(y, 'square', rng, wet_db=-17 + 4 * distance), t0


@_fx('bong_muffled', target=-20.0, doc='big tower bell, struck inside, heard muffled outside; default 10 s, long decay')
def _bong(rng, duration, f_prime=147.0, muffle=1200.0):
    d = 10.0 if duration is None else duration
    r = np.array([0.5, 1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.433, 6.796])
    T = [45, 28, 18, 9, 14, 7, 6, 4.5, 3.0, 2.0, 1.4]
    a = np.array([0.35, 0.4, 0.75, 0.35, 1.0, 0.45, 0.35, 0.35, 0.25, 0.15, 0.08]) * rng.uniform(0.9, 1.1, 11)
    sp = np.array([0.15, 0.35, 0.5, 0.6, 0.8, 1.0, 1.1, 1.3, 1.8, 2.4, 3.0]) * rng.uniform(0.8, 1.2, 11)
    ir = _modal(f_prime * r, T, a, d, sp)
    y = _conv(_exc(rng, 0.7, 0.2, 0.5), ir)[:len(ir)]
    _place(y, bp(_burst(rng, 0.05, 0.004), 800, 4000), 0.0, 0.05)
    y = _reverb(y, 'tower', rng)
    y = lp(lp(y, muffle, 2), muffle * 1.6, 2)
    y = _reverb(y, 'square', rng, wet_db=-14)[:_n(d)]
    fo = min(3.0, 0.35 * d)
    y[_n(d - fo):] *= np.cos(0.5 * np.pi * np.linspace(0, 1, len(y) - _n(d - fo)))[:, None] ** 2
    return y, 0.0


# ============================================================================= ambience beds


@_fx('wind', kind='bed', target=-34.0, doc='cold winter wind bed, slowly gusting, soft (intensity 0..1, whistle 0..1)')
def _wind(rng, duration, intensity=0.5, whistle=0.3, gust_rate=0.12):
    d = 30.0 if duration is None else duration
    n = _n(d)
    g0 = 0.65 * _smooth(n, gust_rate, rng) + 0.35 * _smooth(n, gust_rate / 3, rng)
    common = _pink(n, rng, 1.0)
    fcs = [90, 140, 210, 310, 450, 650, 950, 1400, 2000]
    lag = min(_n(0.35), max(n - 1, 0))
    out = np.zeros((n, 2))
    for c in range(2):
        g = 0.75 * g0 + 0.25 * _smooth(n, gust_rate * 1.5, rng)
        if c == 1 and lag:
            g = np.concatenate([np.full(lag, g[0]), g[:n - lag]])
        g = np.clip((g - 0.5) * (0.8 + intensity) + 0.5, 0, 1)
        base = 0.55 * common + 0.835 * _pink(n, rng, 1.0)
        shift = 0.5 * (g - 0.5) + 0.25 * (intensity - 0.5)
        y = np.zeros(n)
        for fc in fcs:
            shape = np.exp(-0.5 * (np.log2(fc / 380.0) / 1.3) ** 2)
            y += bp(base, fc / 1.3, fc * 1.3, 2) * shape * np.exp(shift * np.log(fc / 300.0))
        y *= 0.2 + 0.8 * g ** 1.4
        if whistle > 0:
            wc = 520 + 380 * g
            ws = np.zeros(n)
            for fw in (560, 640, 735, 850):
                nb = _unit(bp(rng.standard_normal(n), fw * 0.985, fw * 1.015, 2))
                ws += nb * np.exp(-0.5 * ((fw - wc) / 90.0) ** 2)
            y += whistle * 0.35 * np.std(y) * ws * np.clip(g - 0.55, 0, None) ** 1.5 * 6
        out[:, c] = y
    return hp(lp(out, 2600, 2), 55, 2), 0.0


@_fx('town_room_tone', kind='bed', target=-45.0, doc='very quiet outdoor room tone: distant town hum + faint air')
def _room_tone(rng, duration, hum=1.0, air=1.0):
    d = 30.0 if duration is None else duration
    n = _n(d)
    rumble = _unit(lp(_pink(n, rng, 2.0), 140, 4))
    f = 98.0 * (1 + 0.002 * (2 * _smooth(n, 0.1, rng) - 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tonal = np.sin(ph) + 0.35 * np.sin(1.5 * ph + 0.3) + 0.5 * np.sin(2 * ph + 1.1) + 0.15 * np.sin(3 * ph + 2.0)
    tonal *= 0.8 + 0.2 * _smooth(n, 0.05, rng)
    out = np.zeros((n, 2))
    for c in range(2):
        mid = _unit(bp(_pink(n, rng, 1.0), 150, 900)) * (0.8 + 0.4 * _smooth(n, 0.07, rng))
        a = _unit(bp(_pink(n, rng, 1.0), 400, 5000))
        out[:, c] = rumble * (0.85 + 0.3 * _smooth(n, 0.03, rng)) + 0.35 * mid + 0.18 * air * a + 0.06 * hum * tonal
    return hp(out, 25, 2), 0.0


@_fx('oven_hum', kind='bed', target=-40.0, doc='low muffled bakery oven hum through a brick wall')
def _oven_hum(rng, duration, wall=1.0):
    d = 30.0 if duration is None else duration
    n = _n(d)
    roar_c = _pink(n, rng, 1.0)
    f0 = 49.8 * (1 + 0.003 * (2 * _smooth(n, 0.2, rng) - 1))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    motor = sum(a * np.sin(k * ph + 0.7 * k) for k, a in [(1, 0.5), (2, 1.0), (3, 0.4), (4, 0.25), (6, 0.1)])
    out = np.zeros((n, 2))
    for c in range(2):
        roar = lp(0.75 * roar_c + 0.66 * _pink(n, rng, 1.0), 300, 2) * (1 + 0.15 * (2 * _smooth(n, 0.2, rng) - 1))
        fan = bp(_pink(n, rng, 1.0), 180, 400) * 0.3
        y = _unit(roar) + 0.25 * fan + 0.18 * motor
        out[:, c] = y
    fc = 260 - 60 * wall
    return hp(lp(out, fc, 4), 30, 2), 0.0


# ============================================================================= footsteps


def _step_cobble(rng, snow=0.25, hard=1.0):
    y = np.zeros(_n(0.42))
    sc = rng.uniform(0.93, 1.07)
    thud_ir = _modal(np.array([112, 182, 268, 390]) * sc, [0.04, 0.035, 0.03, 0.025], [0.6, .8, .6, .4], 0.2)
    ping_ir = _modal(np.array([2050, 2830, 3720, 4950, 6100]) * rng.uniform(0.9, 1.1),
                     [0.025, 0.022, 0.018, 0.014, 0.01], rng.uniform(0.4, 1.0, 5), 0.08)

    def strike(t0, g):
        _place(y, _conv(_exc(rng, rng.uniform(1.6, 2.6)), thud_ir), t0, 0.3 * g)
        _place(y, bp(_burst(rng, 0.02, rng.uniform(0.0008, 0.0016)), 1500, 7500), t0, 0.09 * g * hard)
        _place(y, _conv(_exc(rng, 0.15, 0.2, 0.3), ping_ir), t0, 0.35 * g * hard)

    strike(0.0, 1.0)
    dt = rng.uniform(0.045, 0.075)
    strike(dt, rng.uniform(0.35, 0.55))
    if rng.random() < 0.35:
        s = bp(_burst(rng, 0.09, 0.03, att=0.01), 700, 3500)
        _place(y, s, dt, 0.012)
    if snow > 0:
        rate = np.zeros(len(y))
        rate[:_n(0.03)] = 700
        rate[_n(dt):_n(dt + 0.03)] = 500
        y += snow * 0.05 * _crackle(rng, len(y), rate, 1800, 6500, (0.1, 0.6))
    return y


@_fx('footsteps_cobble', target=-28.0, doc='ordinary footsteps on cobbles; n, interval (s), snow 0..1')
def _footsteps_cobble(rng, duration, n=6, interval=0.55, snow=0.25, distance=0.0):
    y = np.zeros((_n((n - 1) * interval + 0.6), 2))
    for i in range(int(n)):
        t = i * interval + (rng.normal(0, 0.01) if i else 0.0)
        s = _step_cobble(rng, snow) * _db(rng.normal(0, 1.5))
        _place(y, _pan(s, 0.08 if i % 2 else -0.08), max(t, 0.0))
    if distance:
        y = lp(y, 9000 / (1 + 4 * distance), 2)
    return _reverb(y, 'square', rng, wet_db=-20 + 10 * distance), 0.0


def _squeak(rng, dur=0.09, f0=1100.0, f1=1350.0):
    n = _n(dur)
    t = _t(n)
    f = f0 + (f1 - f0) * t / dur + f0 * 0.02 * (2 * _smooth(n, 60, rng) - 1)
    w = _sinesweep(f, (1.0, 0.35, 0.19, 0.12))
    env = np.minimum(np.sin(0.5 * np.pi * np.minimum(t / 0.012, 1)) ** 2, np.clip((dur - t) / 0.035, 0, 1))
    am = 1 + 0.25 * (2 * _smooth(n, 150, rng) - 1)
    return bp(w * env * am, 800, 6000)


def _step_waddle(rng, squeak=False):
    y = np.zeros(_n(0.55))
    sc = rng.uniform(0.95, 1.05)
    heel_ir = _modal(np.array([88, 132, 190, 268, 380]) * sc, [0.08, 0.075, 0.065, 0.055, 0.045], [0.5, .9, 1, .7, .45], 0.3)
    hollow = _modal(np.array([215, 335, 530]) * sc, [0.07, 0.06, 0.05], [1, .7, .4], 0.2)
    _place(y, _conv(_exc(rng, 3.5, 0.05, 2), heel_ir), 0.0)
    _place(y, _conv(_exc(rng, 2.0, 0.05, 1), hollow), 0.0, 0.5)
    st = rng.uniform(0.038, 0.06)
    slap_ir = _modal(np.array([150, 245, 410, 690]) * sc, [0.045, 0.04, 0.035, 0.03], [.6, .6, .4, .25], 0.15)
    _place(y, _conv(_exc(rng, 2.5), slap_ir), st, 0.6)
    _place(y, bp(_burst(rng, 0.03, 0.005), 500, 3200), st, 0.1)
    if squeak:
        up = rng.random() < 0.5
        f0, f1 = (1050, 1380) if up else (1400, 1000)
        _place(y, _squeak(rng, rng.uniform(0.07, 0.11), f0 * sc, f1 * sc), st + 0.01, 0.12)
    return y


@_fx('footsteps_waddle', target=-22.0, doc='comic bouncy waddle of big clown boots; n, interval, squeak 0..1')
def _footsteps_waddle(rng, duration, n=8, interval=0.36, squeak=0.5):
    n = int(n)
    y = np.zeros((_n(n * interval * 1.1 + 0.7), 2))
    t = 0.0
    sq = rng.random(n) < squeak
    if squeak > 0 and n > 1 and not sq.any():
        sq[1] = True
    for i in range(n):
        s = _step_waddle(rng, bool(sq[i])) * _db((1.0 if i % 2 else -0.5) + rng.normal(0, 0.8))
        _place(y, _pan(s, 0.18 if i % 2 else -0.18), t)
        t += interval * (1.07 if i % 2 == 0 else 0.93) * rng.uniform(0.97, 1.03)
    return _reverb(y, 'square', rng, wet_db=-18), 0.0


@_fx('footsteps_distant', kind='bed', target=-38.0, doc='faint distant footsteps of a few passers-by (bed)')
def _footsteps_distant(rng, duration, walkers=3):
    d = 20.0 if duration is None else duration
    y = np.zeros((_n(d), 2))
    for w in range(int(walkers)):
        span = rng.uniform(5, 14)
        t0 = rng.uniform(-span * 0.5, d - span * 0.5)
        iv = rng.uniform(0.5, 0.62)
        p0, p1 = rng.uniform(-0.8, 0.8, 2)
        lvl = rng.uniform(0.5, 1.0)
        t = t0
        while t < t0 + span:
            if 0 <= t < d:
                u = (t - t0) / span
                env = np.sin(np.pi * u) ** 1.5
                s = _step_cobble(rng, 0.15, hard=0.7) * env * lvl * _db(rng.normal(0, 1.5))
                _place(y, _pan(s, p0 + (p1 - p0) * u), t)
            t += iv * rng.uniform(0.96, 1.04)
    y = hp(lp(y, 1600, 2), 160, 2)
    return _reverb(y, 'square', rng, wet_db=-8)[:len(y)], 0.0


# ============================================================================= shop door


@_fx('shop_bell', target=-21.0, doc='two-tone small brass shop-door bell jingle (strikes, space shop|square)')
def _shop_bell(rng, duration, strikes=9, f_a=1720.0, f_b=2165.0, space='shop'):
    ratios = np.array([1.0, 2.42, 4.11, 6.03, 8.55])
    amps = [1.0, 0.5, 0.3, 0.16, 0.07]
    T = np.array([1.9, 1.05, 0.6, 0.38, 0.22])
    sp = np.array([2.3, 3.6, 5.1, 6.4, 7.7])
    ir = [_modal(f_a * ratios * rng.uniform(0.995, 1.005), T, amps, 2.6, sp * rng.uniform(0.8, 1.2, 5)),
          _modal(f_b * ratios * rng.uniform(0.995, 1.005), T * 0.9, amps, 2.6, sp * rng.uniform(0.8, 1.2, 5))]
    times = [0, 0.085, 0.16, 0.245, 0.335, 0.44, 0.56, 0.71, 0.88, 1.06, 1.25, 1.45]
    which = [0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0]
    y = np.zeros(_n(4.2))
    for k in range(min(int(strikes), len(times))):
        v = 0.83 ** k * rng.uniform(0.8, 1.1)
        _place(y, _conv(_exc(rng, 0.08, 0.35, 0.15), ir[which[k]]), times[k] + (rng.normal(0, 0.008) if k else 0), v)
    return _reverb(y, space, rng), 0.0


_DOOR_F = [72, 118, 166, 231, 312, 425, 566, 790]


@_fx('door_thunk', target=-22.0, doc='wooden shop door closing (sync = impact)')
def _door_thunk(rng, duration, glass=0.5, space='square'):
    y = np.zeros(_n(1.2))
    sw = lp(rng.standard_normal(_n(0.2)), 500) * np.sin(np.pi * np.linspace(0, 1, _n(0.2))) ** 2
    _place(y, _pn(sw), 0.0, _db(-30))
    t0 = 0.18
    ir = _modal(np.array(_DOOR_F) * rng.uniform(0.97, 1.03), [0.22, 0.2, 0.17, 0.15, 0.12, 0.1, 0.08, 0.06],
                np.array([0.4, 0.8, 0.9, .8, .7, .55, .4, .3]) * rng.uniform(0.85, 1.15, 8), 0.6)
    _place(y, _pn(_conv(_exc(rng, 1.2, 0.15, 1.0), ir)), t0)
    _place(y, _pn(bp(_burst(rng, 0.03, 0.003), 900, 3500)), t0, _db(-14))
    latch = _modal([2870, 4130, 5580, 7350], [0.05, 0.04, 0.03, 0.02], [1, .8, .5, .3], 0.1)
    _place(y, _pn(_conv(_exc(rng, 0.1, 0.3, 0.2), latch)), t0 + 0.013, _db(-12))
    if glass:
        gl = _pn(_modal([1210, 1760, 2390, 3150], [0.18, 0.14, 0.11, 0.08], [1, .7, .5, .3], 0.3))
        for dt, g in [(0.004, 1.0), (0.031, 0.45), (0.052, 0.25)]:
            _place(y, _conv(_exc(rng, 0.2, 0.2, 0.2), gl), t0 + dt, _db(-20) * glass * g)
    return _reverb(y, space, rng), t0


def _creak(rng, dur, f_start=45.0, f_peak=115.0, f_end=70.0):
    n = _n(dur)
    kv = np.array([f_start, f_peak * 0.8, f_peak, f_peak * 0.85, f_end]) * (1 + rng.normal(0, 0.05, 5))
    rate = _curve(n, np.array([0, 0.15, 0.45, 0.75, 1.0]) * dur, kv)
    rate *= 1 + 0.06 * (2 * _smooth(n, 25, rng) - 1)
    ph = np.cumsum(rate) / SR
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    imp = np.zeros(n)
    imp[idx] = np.clip(1 + 0.35 * rng.standard_normal(len(idx)), 0.2, None)
    g = rng.standard_normal(_n(0.0015)) * np.exp(-_t(_n(0.0015)) / 0.0003)
    p = _conv(imp, g)[:n]
    y = np.zeros(n)
    for f, q, a in [(380, 6, .8), (640, 8, 1.0), (1020, 9, .8), (1580, 10, .5), (2400, 10, .3)]:
        y += a * reson(p, f * rng.uniform(0.95, 1.05), q)
    env = _curve(n, np.array([0, 0.12, 0.5, 0.8, 1.0]) * dur, [0, 1, 0.85, 1, 0])
    return y * env


@_fx('door_open', target=-24.0, doc='door latch click-clack then a wooden hinge creak (sync = latch release)')
def _door_open(rng, duration, creak=1.0, space='square'):
    y = np.zeros(_n(1.6))
    latch = _modal([2450, 3480, 4720, 6300], [0.06, 0.05, 0.04, 0.025], [1, .8, .5, .3], 0.15)
    _place(y, _pn(_conv(_exc(rng, 0.1, 0.3, 0.2), latch)), 0.0, _db(-6))
    sc = bp(rng.standard_normal(_n(0.07)), 1800, 6000) * np.sin(np.pi * np.linspace(0, 1, _n(0.07)))
    _place(y, _pn(sc), 0.02, _db(-24))
    _place(y, _pn(_conv(_exc(rng, 0.2, 0.3, 0.3), latch)), 0.11)
    door = _modal(_DOOR_F[:5], [0.12, 0.1, 0.09, 0.08, 0.07], [0.5, 1, .8, .6, .4], 0.3)
    _place(y, _pn(_conv(_exc(rng, 1.2), door)), 0.112, _db(-10))
    _place(y, _pn(_creak(rng, 0.95)), 0.22, _db(-5) * creak)
    air = lp(rng.standard_normal(_n(0.8)), 400) * np.sin(np.pi * np.linspace(0, 1, _n(0.8))) ** 2
    _place(y, _pn(air), 0.2, _db(-30))
    return _reverb(y, space, rng), 0.11


# ============================================================================= comic hits


@_fx('clong', target=-14.0, doc='head hits a hollow cast-iron lamppost: inharmonic, beating, long ring')
def _clong(rng, duration, pitch=1.0, ring=1.0):
    f = np.array([167, 327, 541, 806, 898, 1123, 1492, 1985, 2541, 3290, 4870]) * pitch * rng.uniform(0.99, 1.01)
    T = np.array([2.6, 3.1, 2.7, 2.3, 2.0, 1.6, 1.2, 0.9, 0.7, 0.5, 0.3]) * ring
    a = np.array([0.45, 0.8, 1.0, 0.8, 0.9, 0.55, 0.45, 0.3, 0.3, 0.15, 0.08]) * rng.uniform(0.85, 1.15, 11)
    sp = np.array([0.6, 0.9, 1.4, 1.1, 2.3, 1.7, 2.9, 3.4, 4.1, 5.0, 6.0]) * rng.uniform(0.85, 1.15, 11)
    ir = _modal(f, T, a, 4.0, sp)
    y = np.zeros(_n(4.2))
    _place(y, _conv(_exc(rng, 1.1, 0.12, 0.3), ir), 0.0)
    head = _modal([92, 141, 212, 330], [0.09, 0.08, 0.06, 0.05], [1, .8, .5, .3], 0.3)
    _place(y, _conv(_exc(rng, 6.0), head), 0.0, 1.2)
    lant = _modal([2210, 3170, 4430], [0.06, 0.05, 0.04], [1, .7, .5], 0.1)
    for dt, g in [(0.024, 1.0), (0.061, 0.6), (0.097, 0.35), (0.141, 0.2)]:
        _place(y, _conv(_exc(rng, 0.1, 0.3, 0.1), lant), dt + rng.normal(0, 0.004), 0.05 * g)
    return _reverb(y, 'square', rng, wet_db=-15), 0.0


@_fx('slide_whistle_down', target=-19.0, doc='classic comic slide whistle falling ~1900->520 Hz (glide s)')
def _slide_whistle(rng, duration, f_start=1900.0, f_end=520.0, glide=0.6):
    if duration is not None:
        glide = max(0.15, duration - 0.12)
    n = _n(glide + 0.08)
    t = _t(n)
    u = np.clip(t / glide, 0, 1)
    lf = np.log(f_start) + (np.log(f_end) - np.log(f_start)) * (1 - (1 - u) ** 1.4)
    lf -= 0.06 * np.exp(-t / 0.012)
    f = np.exp(lf) * (1 + 0.004 * np.sin(2 * np.pi * 6.2 * t))
    w = _sinesweep(f, (1.0, 0.10, 0.035))
    env = np.minimum(np.sin(0.5 * np.pi * np.minimum(t / 0.02, 1)) ** 2, np.clip((glide + 0.06 - t) / 0.06, 0, 1))
    env *= 1 - 0.15 * u
    br = bp(rng.standard_normal(n), 600, 4000) * env * 0.03
    ch = bp(_burst(rng, 0.03, 0.006), 1000, 5000) * 0.08
    y = w * env + br
    y[:len(ch)] += ch
    return _reverb(y, 'square', rng, wet_db=-20), 0.0


@_fx('thump_fall', target=-17.0, doc='person landing on their backside on cobbles (sync = impact)')
def _thump_fall(rng, duration):
    y = np.zeros(_n(1.2))
    t0 = 0.06
    wh = bp(rng.standard_normal(_n(t0)), 250, 2200) * np.linspace(0, 1, _n(t0)) ** 2
    _place(y, _pn(wh), 0.0, _db(-26))
    body = _modal(np.array([62, 95, 140, 200, 290, 420]) * rng.uniform(0.95, 1.05),
                  [0.18, 0.15, 0.12, 0.10, 0.08, 0.06], [0.6, 1, .9, .7, .5, .3], 0.6)
    _place(y, _pn(_conv(_exc(rng, 5.0, 0.03, 2), body)), t0)
    _place(y, _pn(bp(_burst(rng, 0.08, 0.01), 200, 2000)), t0, _db(-9))
    _place(y, _pn(bp(_burst(rng, 0.3, 0.06, att=0.008), 400, 3000)), t0 - 0.003, _db(-16))
    small = _modal([140, 230, 360, 540], [0.06, 0.05, 0.04, 0.03], [1, .8, .5, .3], 0.2)
    _place(y, _pn(_conv(_exc(rng, 3.0, 0.05, 1), small)), t0 + 0.11, _db(-12))
    _place(y, _pn(_conv(_exc(rng, 2.5, 0.05, 1), small)), t0 + 0.2, _db(-18))
    gr = _crackle(rng, _n(0.3), np.r_[np.full(_n(0.04), 900), np.zeros(_n(0.26))], 1500, 6000, (0.1, 0.6))
    _place(y, _pn(gr), t0, _db(-24))
    return _reverb(hp(y, 40, 2), 'square', rng, wet_db=-18), t0


def _gm_hit(notes, end, programs=None):
    y = _fluid(notes, end, programs)
    m = np.abs(y).max(axis=1)
    on = int(np.argmax(m > 0.02 * m.max()))
    return y[max(0, on - _n(0.002)):]


@_fx('woodblock', target=-20.0, doc="single woodblock 'tok' (GM drum; pitch 'hi'|'lo', velocity)")
def _woodblock(rng, duration, pitch='hi', velocity=100):
    note = 76 if pitch == 'hi' else 77
    try:
        y = _gm_hit([(0.05, 0.3, 9, note, int(velocity))], 1.0)
    except Exception:
        f0 = 1020 if pitch == 'hi' else 820
        y = _conv(_exc(rng, 0.3, 0.2, 0.2), _modal([f0, f0 * 2.47, f0 * 4.1], [0.12, 0.05, 0.03], [1, .4, .2], 0.4))
    return y, 0.002


@_fx('cymbal_tap', target=-24.0, doc="light cymbal tap (GM; kind 'ride'|'crash'|'splash'|'bell', velocity)")
def _cymbal_tap(rng, duration, kind='ride', velocity=60):
    note = {'ride': 51, 'crash': 49, 'splash': 55, 'bell': 53}[kind]
    y = _gm_hit([(0.05, 0.5, 9, note, int(velocity))], 3.5)
    return y, 0.002


# ============================================================================= small objects


def _roll_drop(rng):
    y = np.zeros(_n(0.35))
    ir = _modal(np.array([240, 410, 620, 900, 1300]) * rng.uniform(0.9, 1.1), [0.035, 0.03, 0.025, 0.02, 0.015],
                [0.8, 1, .8, .5, .3], 0.12)
    _place(y, _pn(_conv(_exc(rng, rng.uniform(1.4, 2.0), 0.05, 0.5), ir)), 0.0)
    rate = np.zeros(len(y))
    rate[:_n(0.025)] = 500
    y += _db(-14) * _pn(_crackle(rng, len(y), rate, 1500, 6000, (0.1, 0.5)))
    tb = rng.uniform(0.07, 0.11)
    _place(y, _pn(_conv(_exc(rng, 1.2, 0.03, 0.5), ir)), tb, rng.uniform(0.2, 0.35))
    for k in range(int(rng.integers(1, 4))):
        _place(y, _pn(_conv(_exc(rng, 1.0), ir)), tb + 0.04 + 0.035 * k + rng.uniform(0, 0.02), 0.08 / (k + 1))
    return hp(y, 100, 2)


@_fx('thump_soft', target=-28.0, doc='small bread roll landing on cobbles; n rolls spaced `interval` (0.18 s)')
def _thump_soft(rng, duration, n=1, interval=0.18):
    n = int(n)
    y = np.zeros(_n((n - 1) * interval + 0.5))
    for i in range(n):
        _place(y, _roll_drop(rng), i * interval + (rng.normal(0, 0.008) if i else 0.0), _db(rng.normal(0, 1.5)))
    return _reverb(y, 'square', rng, wet_db=-21), 0.0


def _coin(rng, onto_coins):
    y = np.zeros(_n(0.6))
    sc = rng.uniform(0.9, 1.12)
    f = np.array([3150, 5420, 7350, 9900, 12300]) * sc
    T = np.array([0.10, 0.07, 0.05, 0.035, 0.025]) * (2.2 if onto_coins else 1.0)
    ir = _modal(f, T, [1, .7, .5, .35, .2], 0.4)
    if onto_coins:
        ir += 0.5 * _modal(np.array([3150, 5420, 7350, 9900]) * rng.uniform(0.9, 1.12), T[:4] * 1.3, [1, .7, .5, .35], 0.4)
    _place(y, _conv(_exc(rng, 0.12, 0.3, 0.1), ir), 0.0)
    _place(y, lp(_burst(rng, 0.03, 0.006), 700), 0.0, 0.08)
    tb = rng.uniform(0.035, 0.06)
    _place(y, _conv(_exc(rng, 0.12, 0.3, 0.1), ir), tb, 0.35)
    _place(y, _conv(_exc(rng, 0.12, 0.3, 0.1), ir), tb + rng.uniform(0.02, 0.03), 0.12)
    return y


@_fx('coin_plink', target=-27.0, doc='coin dropping into a felt hat (soft plink); n coins spaced ~interval')
def _coin_plink(rng, duration, n=1, interval=0.45):
    n = int(n)
    y = np.zeros(_n((n - 1) * interval * 1.2 + 0.8))
    t = 0.0
    for i in range(n):
        _place(y, _coin(rng, i > 0), t, _db(rng.normal(0, 1.5)))
        t += interval * rng.uniform(0.85, 1.15)
    return _reverb(y, 'square', rng, wet_db=-20), 0.0


@_fx('paper_rustle', target=-26.0, doc='stiff brown paper folded back (crackle + swish), ~1.1 s')
def _paper_rustle(rng, duration, length=1.1):
    d = length if duration is None else max(0.3, duration - 0.06)
    n = _n(d + 0.1)
    t = _t(n)
    env = sum(a * np.exp(-0.5 * ((t - c * d / 1.1) / (w * d / 1.1)) ** 2)
              for c, w, a in [(0.08, 0.06, 0.7), (0.38, 0.09, 1.0), (0.72, 0.07, 0.6)])
    env *= 1 + 0.3 * (2 * _smooth(n, 12, rng) - 1)
    y = _crackle(rng, n, 900 * env ** 1.3, 900, 7000, (0.2, 1.5))
    y += 1.6 * _crackle(rng, n, 60 * env, 500, 2000, (1.5, 5.0))
    y += 0.25 * bp(_pink(n, rng, 0.5), 400, 4000) * env
    return _reverb(y, 'close', rng), 0.0


@_fx('cloth_rustle', target=-24.0, doc='heavy wool coat swung around shoulders (whoosh + settle), sync = settle')
def _cloth_rustle(rng, duration):
    n = _n(1.35)
    t = _t(n)
    env = _curve(n, [0, .1, .35, .5, .7, .85, 1.0, 1.35], [0, .15, .7, 1, .6, .25, .1, 0])
    pos = _curve(n, [0, .45, 1.35], [0.2, 1.0, 0.3])
    base = _pink(n, rng, 0.8)
    wh = np.zeros(n)
    for fc in (180, 300, 500, 800, 1300, 2100):
        wh += bp(base, fc / 1.4, fc * 1.4) * np.exp(-((np.log(fc) - np.log(250 + 900 * pos)) ** 2) / (2 * 0.7 ** 2))
    y = _unit(wh) * env
    y += 0.5 * _crackle(rng, n, 2500 * env, 800, 5000, (0.1, 0.6)) * np.std(y) / 0.05
    rough = bp(rng.standard_normal(n), 1000, 4500) * env * _smooth(n, 40, rng) ** 2
    y += 0.25 * rough
    ts = 0.86
    th = _conv(_exc(rng, 9.0, 0.05, 2), _modal([120, 190, 290], [0.06, 0.05, 0.04], [1, .7, .4], 0.15))
    _place(y, th, ts, 2.5 * np.max(np.abs(y)) / (np.max(np.abs(th)) + 1e-9) * 0.4)
    se = np.exp(-0.5 * ((t - ts - 0.08) / 0.06) ** 2)
    y += 0.6 * _unit(bp(rng.standard_normal(n), 600, 4000)) * se * np.std(y)
    return _reverb(lp(y, 6000, 2), 'close', rng), ts


@_fx('wool_strain_ping', target=-22.0, doc='wool straining, then a button pops with a small ping (sync = pop)')
def _wool_strain(rng, duration, strain=0.9):
    n = _n(strain + 1.0)
    t = _t(n)
    se = np.clip(t / strain, 0, 1) ** 1.6 * (t < strain)
    fib = _crackle(rng, n, 40 + 900 * se, 1200, 6000, (0.1, 0.5), tilt=0.8) * se
    cr = np.zeros(n)
    c = _creak(rng, strain, 18, 40, 55)
    cr[:len(c)] = c
    groan = bp(_pink(n, rng, 0.5), 200, 1200) * se * _smooth(n, 30, rng)
    st = _pn(fib) + 0.6 * _pn(cr * se) + 0.3 * _pn(groan)
    y = _db(-10) * _pn(st)
    tp = strain + 0.02
    _place(y, _pn(hp(_burst(rng, 0.01, 0.0006), 1200)), tp)
    m = _n(0.6)
    tt = _t(m)
    fping = 2650 * (1 - 0.03 * (1 - np.exp(-tt / 0.08)))
    ping = np.sin(2 * np.pi * np.cumsum(fping) / SR) * np.exp(-6.9 * tt / 0.35) + \
        0.35 * np.sin(2 * np.pi * np.cumsum(fping * 2.61) / SR) * np.exp(-6.9 * tt / 0.15)
    _place(y, _pn(ping) * np.minimum(tt / 0.001, 1), tp + 0.002, _db(-4))
    tick = _modal([3800, 5900, 8100], [0.02, 0.015, 0.01], [1, .6, .3], 0.05)
    for dt, g in [(0.33, -14), (0.5, -18), (0.6, -23)]:
        _place(y, _pn(_conv(_exc(rng, 0.08, 0.2, 0.1), tick)), tp + dt, _db(g))
    return _reverb(y, 'close', rng), tp


@_fx('knee_stone', target=-28.0, doc='a knee (in trousers) touching down on stone')
def _knee_stone(rng, duration):
    y = np.zeros(_n(0.45))
    t0 = 0.03
    pre = bp(rng.standard_normal(_n(t0)), 400, 2500) * np.linspace(0, 1, _n(t0))
    _place(y, _pn(pre), 0.0, _db(-26))
    ir = _modal(np.array([160, 255, 380, 560, 820]) * rng.uniform(0.95, 1.05), [0.04, 0.035, 0.03, 0.025, 0.02],
                [0.7, 1, .8, .5, .3], 0.2)
    _place(y, _pn(_conv(_exc(rng, 2.5, 0.05, 0.6), ir)), t0)
    _place(y, _pn(bp(_burst(rng, 0.12, 0.03, att=0.004), 350, 2800)), t0, _db(-14))
    rate = np.zeros(len(y))
    rate[_n(t0):_n(t0 + 0.03)] = 1200
    y += _db(-22) * _pn(_crackle(rng, len(y), rate, 1800, 6000, (0.1, 0.5)))
    return _reverb(hp(y, 70, 2), 'square', rng, wet_db=-24), t0


@_fx('knee_crack', target=-27.0, doc='knee joints cracking as someone stands up (3-4 pops over ~0.5 s)')
def _knee_crack(rng, duration):
    y = np.zeros(_n(0.75))
    for tp, g in [(0.04, 1.0), (0.29, 0.7), (0.325, 0.9), (0.47, 0.35)]:
        fc = rng.uniform(900, 2600)
        p = _conv(_exc(rng, 0.05, 0.4, 0.3), _modal([fc, fc * 1.7, 180], [0.012, 0.009, 0.02], [1, .5, .4], 0.05))
        _place(y, p, tp + rng.normal(0, 0.004), g)
    pk = np.max(np.abs(y))
    cl = bp(_pink(len(y), rng, 0.5), 400, 3000) * np.sin(np.pi * np.linspace(0, 1, len(y))) ** 2
    y += 0.03 * pk * _unit(cl)
    return _reverb(y, 'close', rng), 0.04


@_fx('cane_click', target=-28.0, doc='wooden walking cane laid down on stone: tip click, shaft clack, small bounce (sync = tip)')
def _cane_click(rng, duration, bounce=1.0, space='square'):
    y = np.zeros(_n(0.7))
    t0 = 0.0
    tip = _modal(np.array([1650, 2480, 3610, 5020]) * rng.uniform(0.95, 1.05), [0.03, 0.025, 0.02, 0.014],
                 [1, .7, .45, .25], 0.08)
    _place(y, _pn(_conv(_exc(rng, 0.12, 0.3, 0.15), tip)), t0, 0.8)
    wood = _modal(np.array([310, 520, 860, 1310, 1900]) * rng.uniform(0.95, 1.05), [0.09, 0.08, 0.065, 0.05, 0.035],
                  np.array([0.6, 1, .8, .55, .3]) * rng.uniform(0.85, 1.15, 5), 0.25)
    _place(y, _pn(_conv(_exc(rng, 0.5, 0.1, 0.3), wood)), t0 + 0.002, 0.35)
    ts = t0 + rng.uniform(0.13, 0.18)                  # the shaft / crook lands
    _place(y, _pn(_conv(_exc(rng, 0.6, 0.15, 0.3), wood)), ts, 1.0)
    _place(y, _pn(bp(_burst(rng, 0.02, 0.003), 800, 5000)), ts, _db(-16))
    if bounce:
        tb = ts + rng.uniform(0.05, 0.07)
        _place(y, _pn(_conv(_exc(rng, 0.5, 0.1, 0.3), wood)), tb, 0.3 * bounce)
        _place(y, _pn(_conv(_exc(rng, 0.4), wood)), tb + rng.uniform(0.03, 0.045), 0.1 * bounce)
    return _reverb(hp(y, 120, 2), space, rng, wet_db=-22), t0


@_fx('typewriter', target=-26.0, doc='brisk typewriter burst (n keystrokes at ~rate/s, optional carriage bell), sync = first strike')
def _typewriter(rng, duration, n=9, rate=9.0, bell=False):
    n = int(n)
    y = np.zeros(_n(n / rate * 1.3 + (1.6 if bell else 0.4)))
    t, last = 0.0, 0.0
    sync = None
    for i in range(n):
        key = _modal(np.array([240, 410, 690]) * rng.uniform(0.92, 1.08), [0.025, 0.02, 0.016], [1, .7, .4], 0.06)
        bar = _modal(np.array([1780, 2650, 3870, 5230, 7100]) * rng.uniform(0.96, 1.04),
                     [0.05, 0.04, 0.03, 0.022, 0.015], np.array([0.8, 1, .8, .5, .3]) * rng.uniform(0.8, 1.2, 5), 0.12)
        g = _db(rng.normal(0, 1.2))
        _place(y, _pn(_conv(_exc(rng, 0.8, 0.1, 0.4), key)), t, 0.35 * g)                # key goes down
        ts = t + rng.uniform(0.018, 0.026)                                                  # typebar hits the platen
        _place(y, _pn(_conv(_exc(rng, 0.08, 0.35, 0.12), bar)), ts, g)
        _place(y, _pn(bp(_burst(rng, 0.012, 0.0015), 2000, 9000)), ts, 0.25 * g)
        esc = _modal([6200, 8300], [0.012, 0.008], [1, .6], 0.03)                           # escapement tick
        _place(y, _pn(_conv(_exc(rng, 0.05), esc)), ts + rng.uniform(0.012, 0.02), 0.12 * g)
        sync = ts if sync is None else sync
        last = ts
        t += rng.uniform(0.7, 1.35) / rate
    if bell:
        tb = last + 0.18
        ding = _modal(np.array([2093, 2093 * 2.76, 2093 * 5.4]), [1.2, 0.5, 0.25], [1, .35, .12], 1.3, [1.5, 3.0, 4.0])
        _place(y, _pn(_conv(_exc(rng, 0.06, 0.2, 0.1), ding)), tb, 0.45)
        rat = _crackle(rng, _n(0.3), np.linspace(900, 300, _n(0.3)), 1500, 6000, (0.1, 0.5))
        _place(y, _pn(rat), tb + 0.12, 0.15)
    return _reverb(hp(y, 150, 2), 'close', rng), sync


# ============================================================================= bakery


@_fx('tray_clatter', target=-30.0, doc='metal baking tray clattering inside, muffled behind shop glass')
def _tray_clatter(rng, duration, glass=1.0):
    nm = 36
    f = np.sort(np.exp(rng.uniform(np.log(180), np.log(5000), nm)))
    T = np.clip(0.6 * (f / 500) ** -0.4, 0.15, 1.0)
    irs = []
    for _ in range(3):
        a = np.exp(rng.normal(0, 0.6, nm)) * (f / 500) ** -0.3
        irs.append(_modal(f, T, a, 1.2, rng.uniform(0.5, 3.0, nm)))
    times = [0, 0.11, 0.24, 0.33, 0.40, 0.455, 0.50, 0.535, 0.565, 0.59, 0.61, 0.627, 0.64]
    amps = [1, .7, .55, .45, .4, .33, .28, .22, .18, .14, .1, .07, .05]
    y = np.zeros(_n(2.0))
    for i, (tt, a) in enumerate(zip(times, amps)):
        _place(y, _conv(_exc(rng, 0.3, 0.3, 0.3), irs[i % 3]), tt + (rng.normal(0, 0.004) if i else 0), a)
    ts = _n(0.66)
    y[ts:] *= np.exp(-_t(len(y) - ts) / 0.08)
    y = _reverb(y, 'bakery', rng)
    fc = 1100 / (0.4 + 0.6 * glass)
    y = lp(lp(y, fc, 2), fc * 1.5, 2)
    return peak(y, 420, 2.0, 0.5), 0.0


@_fx('crust_crack', target=-24.0, doc='crusty rye loaf torn by hand (crack, crackling tear, final snap)')
def _crust_crack(rng, duration, length=0.8):
    d = length if duration is None else max(0.3, duration - 0.12)
    n = _n(d + 0.15)
    t = _t(n)
    rate = np.zeros(n)
    rate[_n(0.02):_n(0.045)] = 6000
    tear = np.clip(1 - (t - 0.05) / (d * 0.7), 0, 1) * (t > 0.05) * (0.5 + 0.5 * _smooth(n, 14, rng)) ** 2
    rate += 900 * tear
    fin = _n(d * 0.78)
    rate[fin:fin + _n(0.02)] += 4000
    y = _crackle(rng, n, rate, 700, 7000, (0.15, 1.5), tilt=1.2)
    sc = np.std(y) + 1e-9
    rip = bp(_pink(n, rng, 0.5), 300, 2500) * _smooth(n, 60, rng) ** 2
    y += 0.9 * sc * _unit(rip) * tear
    body = _conv(_exc(rng, 1.5), _modal([250, 400, 620], [0.04, 0.035, 0.03], [1, .7, .4], 0.08))
    _place(y, body, 0.02, 0.3 * np.max(np.abs(y)) / (np.max(np.abs(body)) + 1e-9))
    return _reverb(y, 'close', rng), 0.02


@_fx('sack_thump', target=-21.0, doc='flour sack dropped on stone (heavy soft thud + flour puff), sync = impact')
def _sack_thump(rng, duration):
    y = np.zeros(_n(1.0))
    t0 = 0.02
    ir = _modal(np.array([70, 105, 150, 210, 300, 430]) * rng.uniform(0.95, 1.05),
                [0.12, 0.10, 0.085, 0.07, 0.055, 0.045], [0.7, 1, .9, .7, .45, .25], 0.5)
    _place(y, _pn(_conv(_exc(rng, 7.0, 0.03, 2), ir)), t0)
    rate = np.zeros(len(y))
    rate[_n(t0):_n(t0 + 0.05)] = 3000
    y += _db(-16) * _pn(_crackle(rng, len(y), rate, 700, 4000, (0.3, 1.5)))
    m = _n(0.6)
    puff = bp(_pink(m, rng, 0.6), 400, 3000) * np.exp(-_t(m) / 0.12) * np.minimum(_t(m) / 0.006, 1)
    _place(y, _pn(puff), t0 + 0.005, _db(-12))
    _place(y, _pn(_conv(_exc(rng, 6.0, 0.02, 2), ir)), t0 + 0.095, _db(-14))
    ru = bp(rng.standard_normal(_n(0.3)), 500, 3000) * np.sin(np.pi * np.linspace(0, 1, _n(0.3))) ** 2
    _place(y, _pn(ru), t0 + 0.1, _db(-24))
    return _reverb(hp(y, 40, 2), 'square', rng, wet_db=-19), t0


@_fx('gas_lamp_on', target=-24.0, doc="gas lamp ignites: soft 'fwump' + brief hiss + celesta ting (note=88)")
def _gas_lamp(rng, duration, note=88, ting=1.0, ting_delay=0.12):
    y = np.zeros(_n(2.8))
    t0 = 0.03
    m = _n(0.6)
    tt = _t(m)
    env = np.where(tt < 0.018, np.sin(0.5 * np.pi * tt / 0.018) ** 2, np.exp(-(tt - 0.018) / 0.09))
    fw = _unit(lp(rng.standard_normal(m), 350, 2)) * env
    fw += 0.6 * np.sin(2 * np.pi * np.cumsum(55 + 40 * np.exp(-tt / 0.04)) / SR) * env
    fw += 0.25 * _unit(bp(rng.standard_normal(m), 300, 1200)) * env * np.exp(-tt / 0.05)
    fw /= np.max(np.abs(fw))
    _place(y, fw, t0)
    hm = _n(0.9)
    th = _t(hm)
    henv = np.where(th < 0.03, th / 0.03, 0.3 + 0.7 * np.exp(-(th - 0.03) / 0.08)) * np.clip((0.9 - th) / 0.5, 0, 1)
    _place(y, _unit(bp(rng.standard_normal(hm), 2500, 9000)) * henv, t0 + 0.05, 0.05)
    if ting:
        tg = _gm_hit([(0.05, 1.2, 0, int(note), 80)], 2.6, programs={0: 8}).mean(axis=1)
        tg = tg / (np.max(np.abs(tg)) + 1e-9)
        _place(y, tg, t0 + ting_delay, 0.4 * ting)
    return _reverb(y, 'square', rng, wet_db=-18), t0


# ============================================================================= breaths


def _formant_noise(rng, n, formants, broad=0.15, hpf=150, alpha=0.0):
    x = _pink(n, rng, alpha) if alpha else rng.standard_normal(n)
    y = broad * lp(x, 5000, 2)
    for f, q, a in formants:
        y += a * reson(x, f, q)
    return hp(y, hpf, 2)


@_fx('breath_exhale', target=-30.0, doc='soft human exhale/sigh (length s, nose=False)')
def _exhale(rng, duration, length=1.1, nose=False):
    d = length if duration is None else max(0.2, duration - 0.06)
    n = _n(d)
    fm = [(320, 4, 1.0), (1000, 5, .4), (2300, 6, .15)] if nose else [(550, 3, 1.0), (1500, 4, .45), (2550, 5, .2), (3500, 6, .08)]
    y = _formant_noise(rng, n, fm, broad=0.1, hpf=200 if nose else 150, alpha=0.8)
    env = _curve(n, np.array([0, .12, .3, .75, 1.0]) * d, [0, 1, .8, .25, 0])
    env *= 1 + 0.15 * (2 * _smooth(n, 8, rng) - 1)
    return _reverb(y * env, 'close', rng), 0.0


@_fx('sniff', target=-30.0, doc='a short nasal sniff (n sniffs, interval)')
def _sniff(rng, duration, n=1, interval=0.32):
    n = int(n)
    y = np.zeros(_n((n - 1) * interval + 0.4))
    for i in range(n):
        L = 0.22 if i == 0 else 0.15
        m = _n(L)
        x = _formant_noise(rng, m, [(1200, 4, 1.0), (2500, 5, .6), (4200, 5, .25)], broad=0.2, hpf=700, alpha=0.6)
        env = _curve(m, [0, 0.03, 0.55 * L, L - 0.03, L], [0, 0.6, 1.0, 0.9, 0]) * (1 + 0.2 * (2 * _smooth(m, 30, rng) - 1))
        _place(y, x * env, i * interval, 1.0 if i == 0 else 0.7)
    return _reverb(y, 'close', rng), 0.0


# ============================================================================= laughter (Kokoro TTS)

# voice presets: Kokoro style mix, laugh-syllable phoneme string, speed, formant shift
# (semitones, via resampling) and the pitch shifts (semitones, rubberband -F) to prepare
_VOICES = {
    'young_man': dict(mix=(('am_michael', 0.5), ('am_puck', 0.5)), ph='hˈɑhɑhɑhɑhɑhɑ', speed=1.35, fs=0.0,
                      shifts=(3, 4, 5, 6, 7)),
    'woman': dict(mix=(('af_bella', 0.6), ('af_heart', 0.4)), ph='hˈʌhɑhʌhɑhʌhɑ', speed=1.4, fs=0.0,
                  shifts=(3, 4, 5, 6)),
    'old_man': dict(mix=(('am_santa', 0.6), ('bm_george', 0.4)), ph='hˈɛhɛhɛhɛhɛ', speed=1.15, fs=0.0,
                    shifts=(-1, 0, 1, 2)),
    'old_woman': dict(mix=(('bf_emma', 0.8), ('bm_george', 0.2)), ph='hˈɑhɑhɑhɑhɑ', speed=1.25, fs=0.0,
                      shifts=(1, 2, 3, 4)),
    'child': dict(mix=(('af_sky', 0.7), ('am_puck', 0.3)), ph='hˈihɪhihɪhihɪ', speed=1.55, fs=4.0,
                  shifts=(6, 7, 8, 9)),
    'man': dict(mix=(('am_michael', 1.0),), ph='hˈʌhʌhʌhʌ', speed=1.3, fs=0.0, shifts=(1, 2, 3)),
}
_HUM_PH = 'hˈmhmhmhm'


@functools.lru_cache(maxsize=128)
def _syllables(mix, ph, speed, semis, fs):
    """Kokoro laugh string -> list of syllables (48 kHz arrays), cut at the 'h' onsets."""
    wav, chars, edges = _kokoro(ph, dict(mix), speed)
    starts = [edges[i + 1] for i, c in enumerate(chars) if c == 'h']
    end_v = edges[len(chars) + 1]
    wav = _rubberband(wav, 24000, semis, formant=True)
    r = 2.0 ** (fs / 12.0)
    x = signal.resample_poly(wav, 2000, int(round(1000 * r)))   # -> 48 kHz, formants*r
    starts = [s / r for s in starts]
    end_v /= r
    out = []
    for k, s in enumerate(starts):
        a = max(0, _n(s) - _n(0.012))
        b = _n(starts[k + 1]) if k + 1 < len(starts) else _n(end_v) + _n(0.06)
        seg = x[a:b].copy()
        if len(seg) > _n(0.04):
            out.append(seg)
    return tuple(out)


def _bank(voice):
    v = _VOICES[voice] if isinstance(voice, str) else voice
    return {s: _syllables(v['mix'], v['ph'], v['speed'], float(s), v['fs']) for s in v['shifts']}


def _lpc(x, order=24):
    x = x * np.hanning(len(x))
    r = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * len(x))) ** 2)[:order + 1]
    r[0] = r[0] * 1.001 + 1e-12
    a = solve_toeplitz(r[:order], -r[1:order + 1])
    return np.concatenate([[1.0], a * 0.994 ** np.arange(1, order + 1)])


def _env_follow(x, win=0.01):
    w = _n(win)
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same'))
    return e


def _inhale(rng, dur=0.3, bright=1.0):
    n = _n(dur)
    x = _formant_noise(rng, n, [(450, 3, 1.0), (1900, 5, .8 * bright), (2900, 6, .5 * bright)], broad=0.3, hpf=500)
    env = _curve(n, [0, 0.7 * dur, dur], [0, 1, 0]) ** 1.5
    return x * env


def _aspirate(rng, seg, h_len, hgain=0.3, breath=0.3):
    """Prepend an [h] of h_len s and add breath noise, both shaped by the syllable's
    own LPC spectral envelope. Returns the longer segment (voice onset at h_len)."""
    pre = np.append(seg[0], seg[1:] - 0.9 * seg[:-1])
    a = _lpc(pre)
    nh = _n(h_len)
    L = nh + len(seg)
    nz = _unit(lp(signal.lfilter([1.0], a, rng.standard_normal(L)), 7000, 2))
    e = _env_follow(seg)
    ep = e.max() + 1e-12
    t = _t(L)
    env_h = np.where(t < h_len, np.sin(0.5 * np.pi * np.clip(t / max(h_len, 1e-3), 0, 1)) ** 1.5,
                     np.exp(-(t - h_len) / 0.03))
    env_b = np.concatenate([np.zeros(nh), e / ep])
    out = np.concatenate([np.zeros(nh), seg])
    return out + nz * ep * (hgain * env_h + breath * env_b)


def _bout(rng, bank, n, period, p0, p1, slow=0.25, breath=0.3, hboost=0.3, maxlen=1.25, decay=0.9, lead=0.08):
    """One laugh bout of n syllables. Returns (mono, vowel onset times, end time)."""
    keys = sorted(bank)
    times, t = [], lead
    for i in range(n):
        times.append(t)
        t += period * (1 + slow * i / max(1, n - 1)) * rng.uniform(0.9, 1.1)
    y = np.zeros(_n(t + 0.8))
    for i, t0 in enumerate(times):
        tgt = p0 + (p1 - p0) * i / max(1, n - 1) + rng.normal(0, 0.3)
        k = min(keys, key=lambda s_: abs(s_ - tgt))
        syls = bank[k]
        last = i == n - 1
        if len(syls) > 2:
            j = len(syls) - 1 if (last and rng.random() < 0.5) else int(rng.integers(1, len(syls) - 1))
        else:
            j = len(syls) - 1
        seg = syls[j]
        per = (times[i + 1] - t0) if not last else period * 1.8
        m = min(len(seg), _n(per * (1.6 if last else maxlen)))
        seg = _fade(seg[:m], 0.004, min(0.04, m / SR / 3))
        lev = np.max(_env_follow(seg, 0.03)) + 1e-9
        h_len = rng.uniform(0.05, 0.08)
        seg = _aspirate(rng, seg / lev, h_len, hboost, breath)
        g = (0.8 if i == 0 else 1.0) * decay ** i * _db(rng.normal(0, 1.0))
        _place(y, seg, t0 - h_len, g)
    # continuous airflow between syllables (a laugh is never gated to silence)
    w = _n(0.12)
    env = np.sqrt(np.convolve(y ** 2, np.ones(w) / w, 'same'))
    air = _formant_noise(rng, len(y), [(650, 3, 1.0), (1300, 4, .5), (2500, 5, .25)], broad=0.2, hpf=300, alpha=0.5)
    y += 0.25 * _unit(air) * env
    return y, times, t


def _slap(rng):
    ir = _modal([150, 240, 380, 620, 1100], [0.04, 0.035, 0.03, 0.02, 0.015], [1, .8, .6, .4, .25], 0.12)
    y = _conv(_exc(rng, 0.4, 0.6, 0.8), ir)
    s = bp(_burst(rng, 0.03, 0.002), 600, 5000)
    y[:len(s)] += 0.05 * s
    return y / np.max(np.abs(y))


def _laugher(rng, voice, plan, total, inhale_gain=0.12, extend=True):
    """plan: [(start, n, period, p0, p1, gain)]; extends with decaying bouts up to total."""
    bank = _bank(voice)
    plan = list(plan)
    if extend:
        st, n, per, p0, p1, g = plan[-1]
        end = st + n * per * 1.15
        while True:
            st2 = end + rng.uniform(0.25, 0.45)
            n2 = int(rng.integers(3, 6))
            if st2 + n2 * per * 1.15 + 0.3 > total:
                break
            g *= 0.75
            p0, p1 = p0 - 0.5, p1 - 0.5
            plan.append((st2, n2, per * 1.05, p0, p1, g))
            end = st2 + n2 * per * 1.15
    y = np.zeros(_n(total + 2.0))
    onsets = []
    for j, (st, n, per, p0, p1, g) in enumerate(plan):
        b, times, end = _bout(rng, bank, n, per, p0, p1)
        _place(y, b, st, g)
        onsets.append([st + x for x in times])
        if j + 1 < len(plan):
            gap = plan[j + 1][0] - (st + end)
            if gap > 0.1:
                d = min(0.35, gap + 0.08)
                _place(y, _inhale(rng, d), st + end - 0.04, g * inhale_gain)
    return y, onsets


@_fx('crowd_laugh', target=lambda p: -18.0 if p.get('intensity', 'big') == 'big' else -23.0,
     doc="three people laughing outdoors (woman behind glove, young man slapping knee, older man chuckling); intensity 'big'|'small'")
def _crowd_laugh(rng, duration, intensity='big'):
    big = intensity == 'big'
    total = duration if duration is not None else (2.9 if big else 1.6)
    if big:
        ym_plan = [(0.0, 7, 0.185, 7, 4, 1.0), (1.85, 4, 0.2, 5, 3, 0.65)]
        wo_plan = [(0.1, 6, 0.17, 6, 4, 1.0), (1.55, 4, 0.18, 5, 3, 0.7)]
        om_plan = [(0.3, 5, 0.25, 1.5, -0.5, 1.0), (1.95, 3, 0.27, 0.5, -1, 0.6)]
    else:
        ym_plan = [(0.0, 4, 0.19, 5, 3, 0.85)]
        wo_plan = [(0.12, 3, 0.18, 4.5, 3, 0.8)]
        om_plan = [(0.28, 3, 0.26, 0.5, -1, 0.8)]
    ym, ym_on = _laugher(rng, 'young_man', ym_plan, total)
    wo, _ = _laugher(rng, 'woman', wo_plan, total)
    om, _ = _laugher(rng, 'old_man', om_plan, total)
    # woman laughs into her glove: dark, slightly boxy
    wo = peak(lp(lp(wo, 1500, 2), 2400, 2), 650, 2.5, 0.6)
    om = lp(om, 5500, 2)
    # knee slaps under the young man's laugh
    pk = np.max(np.abs(ym))
    slaps = [1, 3] if big else [1]
    for k in slaps:
        if k < len(ym_on[0]):
            _place(ym, _slap(rng), ym_on[0][k] + 0.015, 0.6 * pk * (1.0 if k == 1 else 0.8))
    lev = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-12
    ref = lev(ym)
    parts = [_pan(ym, -0.3), _pan(wo * ref / lev(wo) * 0.6, 0.28), _pan(om * ref / lev(om) * 0.7, 0.05)]
    y = np.zeros((max(len(p) for p in parts), 2))
    for p in parts:
        _place(y, p, 0)
    y = _reverb(y, 'square', rng, wet_db=-15)
    return y, ym_on[0][0]


@_fx('child_giggle', target=-22.0, doc='a small boy giggling (~1.5 s)')
def _child_giggle(rng, duration):
    total = duration if duration is not None else 1.5
    y, on = _laugher(rng, 'child', [(0.0, 6, 0.135, 9, 7, 1.0), (1.05, 3, 0.14, 8.5, 7, 0.7)], total,
                     inhale_gain=0.18, extend=duration is not None)
    return _reverb(y, 'square', rng, wet_db=-18), on[0][0]


@_fx('laugh_old_woman', target=-19.0, doc='a short bright laugh from an elderly woman (3-4 syllables + breath)')
def _laugh_old_woman(rng, duration, voice='old_woman'):
    bank = _bank(voice)
    b, times, end = _bout(rng, bank, 4, 0.2, 4, 2, slow=0.35, breath=0.4, hboost=0.35, decay=0.85)
    sync = times[0]
    n = len(b)
    t = _t(n)
    b *= 1 + 0.18 * np.sin(2 * np.pi * 5.8 * t + rng.uniform(0, 6.28))
    pk = np.max(np.abs(b))
    ex = _formant_noise(rng, _n(0.35), [(600, 4, 1.0), (1600, 5, .6), (2600, 6, .3)])
    ex *= _curve(len(ex), [0, 0.04, 0.35], [0, 1, 0])
    _place(b, ex / np.max(np.abs(ex)), end - 0.05, 0.12 * pk)
    b = peak(b, 3000, 1.5, 0.3)
    return _reverb(b, 'square', rng, wet_db=-19), sync


@_fx('huff_laugh', target=-24.0, doc="a startled single breath of laughter (voice preset: man|woman|old_woman|old_man|young_man|child)")
def _huff_laugh(rng, duration, voice='man'):
    bank = _bank(voice)
    syls = bank[sorted(bank)[len(bank) // 2]]
    seg = syls[1 if len(syls) > 1 else 0]
    seg = seg / (np.max(np.abs(seg)) + 1e-9)
    pre = np.append(seg[0], seg[1:] - 0.9 * seg[:-1])
    a = _lpc(pre)
    n = _n(0.45)
    t = _t(n)
    nz = _unit(lp(signal.lfilter([1.0], a, rng.standard_normal(n)), 6000, 2))
    env = np.minimum(t / 0.006, 1) * np.exp(-t / 0.11)
    y = nz * env
    v = _fade(seg[:_n(0.09)], 0.004, 0.03)
    _place(y, v / (np.max(np.abs(v)) + 1e-9), 0.008, 0.5)
    return _reverb(y, 'close', rng), 0.0


@_fx('nasal_laugh', target=-28.0, doc='a tiny laugh through the nose (n bursts, voice preset)')
def _nasal_laugh(rng, duration, voice='woman', n=2):
    v = dict(_VOICES[voice])
    v['ph'] = _HUM_PH
    v['shifts'] = (sorted(v['shifts'])[0] + 1,)
    bank = _bank(v)
    syls = list(bank.values())[0]
    n = int(n)
    y = np.zeros(_n(0.15 * n + 0.4))
    for i in range(n):
        m = _n(0.11)
        tt = _t(m)
        nz = _formant_noise(rng, m, [(1000, 3, .8), (2500, 4, 1.0), (3800, 5, .4)], broad=0.3, hpf=300)
        env = np.minimum(tt / 0.005, 1) * np.exp(-tt / 0.035)
        burst = nz * env / (np.max(np.abs(nz * env)) + 1e-9)
        seg = syls[(i + 1) % len(syls)]
        hum = _fade(lp(seg[:m], 2500, 2), 0.004, 0.03)
        hum = hum / (np.max(np.abs(hum)) + 1e-9)
        t0 = i * 0.145 + (rng.normal(0, 0.008) if i else 0)
        g = 0.75 ** i
        _place(y, burst, t0, g)
        _place(y, hum, t0 + 0.005, 0.3 * g)
    return _reverb(y, 'close', rng), 0.0


# ----------------------------------------------------------------------------- CLI

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    names = sys.argv[2:] or list(_FX)
    for nm in names:
        r = sfx(nm, os.path.join(out, 'sfx_%s.wav' % nm))
        print('%-20s dur %6.2f  sync %5.3f  peak %6.1f  Lm %6.1f  Li %6.1f  mix_gain %+5.1f dB' %
              (nm, r['duration'], r['sync'], r['peak_db'], r['lufs_m'], r['lufs_i'], r['mix_gain_db']))
