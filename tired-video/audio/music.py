"""Procedural music for "Nice Try, My Guy".

    render_cue(name, dur, sr=48000, fade_in=0.02, fade_out=1.0, seed=0)
        -> np.ndarray float32, shape (n, 2), n = round(dur * sr), values in [-1, 1]

Cues (see CUES): none, doom, sneaky, ai_calm, tension, beg, heart, resolve.
Each cue is an 8-bar (or 8-chord) composition that loops for any duration with
small per-pass variations; the last `fade_out` seconds fade out so a cue can
end anywhere. Every render is loudness-normalized to TARGET_LUFS (-18 LUFS,
RMS around -20 dBFS) so the mixer only has to balance, not guess.

The first half of this file is a small DSP toolkit (oscillators, filters,
envelopes, reverb, loudness) that audio/sfx.py and audio/mix.py reuse.
"""
import itertools
import math
import re
import zlib
from functools import lru_cache

import numpy as np
from scipy import signal as sps

SR = 48000
TARGET_LUFS = -18.0
CUES = ["none", "doom", "sneaky", "ai_calm", "tension", "beg", "heart", "resolve"]
SQ2 = math.sqrt(2.0)
TAU = 2.0 * math.pi


# =============================================================================
# DSP toolkit
# =============================================================================
def secs(sr, s):
    return max(1, int(round(s * sr)))


def tvec(n, sr):
    return np.arange(n) / sr


def seeded(*parts):
    return np.random.default_rng(zlib.crc32("|".join(str(p) for p in parts).encode()))


def rbj(kind, f0, sr, q=0.7071, gain_db=0.0):
    """RBJ cookbook biquad as a single SOS row."""
    f0 = float(min(max(f0, 5.0), sr * 0.49))
    A = 10.0 ** (gain_db / 40.0)
    w0 = TAU * f0 / sr
    cw, sw = math.cos(w0), math.sin(w0)
    al = sw / (2.0 * q)
    if kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "bandpass":           # 0 dB peak gain
        b = [al, 0.0, -al]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind in ("highshelf", "lowshelf"):
        sq = 2 * math.sqrt(A) * al
        if kind == "highshelf":
            b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw),
                 A * ((A + 1) + (A - 1) * cw - sq)]
            a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw),
                 (A + 1) - (A - 1) * cw - sq]
        else:
            b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw),
                 A * ((A + 1) - (A - 1) * cw - sq)]
            a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw),
                 (A + 1) + (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    return np.array([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]])


def biquad(x, kind, f0, sr, q=0.7071, gain_db=0.0):
    return sps.sosfilt(rbj(kind, f0, sr, q, gain_db), x, axis=0)


def _bsos(kind, fc, sr, order):
    nyq = sr / 2.0
    if kind == "band":
        fc = [max(5.0, fc[0]), min(fc[1], nyq * 0.97)]
    else:
        fc = min(max(fc, 5.0), nyq * 0.97)
    return sps.butter(order, fc, btype=kind, fs=sr, output="sos")


def lp(x, fc, sr, order=2):
    return sps.sosfilt(_bsos("low", fc, sr, order), x, axis=0)


def hp(x, fc, sr, order=2):
    return sps.sosfilt(_bsos("high", fc, sr, order), x, axis=0)


def bp(x, lo, hi, sr, order=2):
    return sps.sosfilt(_bsos("band", [lo, hi], sr, order), x, axis=0)


def tv_filter(x, fc, sr, kind="lowpass", q=0.8, block=256, stages=2):
    """Time-varying biquad cascade. `fc` scalar or per-sample array; it is
    sampled once per block (coefficients change smoothly, state carries over)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    fcs = np.broadcast_to(np.asarray(fc, dtype=float), (n,))
    out = np.empty_like(x)
    zi = np.zeros((stages, 2) + x.shape[1:])
    for s in range(0, n, block):
        e = min(n, s + block)
        sos = np.vstack([rbj(kind, fcs[(s + e) // 2], sr, q)] * stages)
        out[s:e], zi = sps.sosfilt(sos, x[s:e], axis=0, zi=zi)
    return out


def smooth_noise(n, sr, rate, rng):
    """Band-limited random curve (~`rate` Hz), roughly in [-1, 1]."""
    k = max(2, int(n * rate / sr) + 3)
    pts = rng.uniform(-1, 1, k)
    xs = np.linspace(0, n, k)
    return np.interp(np.arange(n), xs, pts)


# --- oscillators ---------------------------------------------------------------
def _phase(f, n, sr, ph0):
    f = np.broadcast_to(np.asarray(f, dtype=float), (n,))
    dt = f / sr
    ph = np.empty(n)
    ph[0] = 0.0
    np.cumsum(dt[:-1], out=ph[1:])
    ph += ph0
    ph %= 1.0
    return ph, dt


def saw(f, n, sr, ph0=0.0):
    """Band-limited (polyBLEP) sawtooth in [-1, 1]."""
    ph, dt = _phase(f, n, sr, ph0)
    dt = np.clip(dt, 1e-9, 0.5)
    y = 2.0 * ph - 1.0
    m = ph < dt
    tt = ph[m] / dt[m]
    y[m] -= tt + tt - tt * tt - 1.0
    m = ph > 1.0 - dt
    tt = (ph[m] - 1.0) / dt[m]
    y[m] -= tt * tt + tt + tt + 1.0
    return y


def pulse(f, n, sr, width=0.5, ph0=0.0):
    y = 0.5 * (saw(f, n, sr, ph0) - saw(f, n, sr, ph0 + width))
    return y - y.mean()


def sine(f, n, sr, ph0=0.0):
    ph, _ = _phase(f, n, sr, ph0)
    return np.sin(TAU * ph)


def tri(f, n, sr, ph0=0.0, harmonics=6):
    ph, _ = _phase(f, n, sr, ph0)
    y = np.zeros(n)
    for k in range(harmonics):
        h = 2 * k + 1
        y += ((-1) ** k) * np.sin(TAU * h * ph) / (h * h)
    return y * (8 / math.pi ** 2)


# --- envelopes / panning -------------------------------------------------------
def env_adsr(n, sr, a, d, s, r, gate, smooth=True):
    """ADSR. a/d/r seconds, s level, gate = key-held seconds. Ends at exactly 0."""
    t = tvec(n, sr)
    a = max(a, 1e-3)

    def level(tt):
        att = np.clip(tt / a, 0.0, 1.0)
        if smooth:
            att = att * att * (3 - 2 * att)
        dec = s + (1 - s) * np.exp(-np.maximum(tt - a, 0.0) / max(d, 1e-3))
        return np.where(tt < a, att, dec)

    e = level(t)
    g = min(max(gate, 0.0), t[-1])
    lg = float(level(np.array([g]))[0])
    rel = t >= g
    e[rel] = lg * np.exp(-(t[rel] - g) / max(r / 5.0, 1e-3))
    k = min(n, max(2, int(0.004 * sr)))
    e[-k:] *= np.linspace(1.0, 0.0, k)
    return e


def perc_env(n, sr, decay, attack=0.002):
    t = tvec(n, sr)
    e = np.exp(-t / decay) * np.clip(t / max(attack, 1e-4), 0, 1)
    k = min(n, max(2, int(0.003 * sr)))
    e[-k:] *= np.linspace(1.0, 0.0, k)
    return e


def fade_edges(x, sr, fin=0.002, fout=0.01):
    n = len(x)
    a = min(n // 2, max(1, int(fin * sr)))
    b = min(n // 2, max(1, int(fout * sr)))
    shp = (slice(None),) + (None,) * (x.ndim - 1)
    x[:a] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a)))[shp]     # raised-cosine: no kinks
    x[n - b:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b)))[shp]
    return x


def pan(x, p=0.0):
    """Mono -> stereo with constant power; center = unity on both channels."""
    th = (float(np.clip(p, -1, 1)) + 1.0) * math.pi / 4.0
    return np.stack([x * math.cos(th) * SQ2, x * math.sin(th) * SQ2], axis=1)


def stereoize(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


# --- reverb --------------------------------------------------------------------
@lru_cache(maxsize=32)
def reverb_ir(sr, rt60=2.0, predelay=0.02, damp=0.5, seed=7, er=0.3):
    """Synthetic stereo IR: decorrelated noise in 3 bands decaying at different
    rates (highs die faster), a soft onset, a few early reflections."""
    rng = np.random.default_rng(seed)
    n = int(sr * min(rt60 * 1.15, 5.0))
    t = tvec(n, sr)
    ir = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        lo = lp(nz, 450, sr, 2)
        hi = hp(nz, 3500, sr, 2)
        mid = nz - lo - hi
        e = lambda r: 10.0 ** (-3.0 * t / r)  # noqa: E731
        ir[:, ch] = (lo * e(rt60 * 1.1) + mid * e(rt60) +
                     hi * e(rt60 * (0.55 - 0.35 * damp)) * (1.0 - 0.6 * damp))
    ir *= (1.0 - np.exp(-t / 0.012))[:, None]
    # early reflections
    for _ in range(10):
        d = int(sr * rng.uniform(0.004, 0.045))
        if d < n:
            ir[d, rng.integers(0, 2)] += er * rng.uniform(-1, 1) * 6
    ir = lp(ir, 9000 - 4000 * damp, sr, 2)
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-12
    pd = int(sr * predelay)
    ir = np.concatenate([np.zeros((pd, 2)), ir])
    ir.flags.writeable = False
    return ir


def reverb(x, sr, rt60=2.0, predelay=0.02, damp=0.5, seed=7, er=0.3):
    """Stereo (or mono->stereo) convolution reverb, output same length as x."""
    x = stereoize(np.asarray(x, dtype=float))
    ir = reverb_ir(sr, round(rt60, 3), round(predelay, 4), round(damp, 3), seed, er)
    out = np.empty_like(x)
    for ch in range(2):
        out[:, ch] = sps.oaconvolve(x[:, ch], ir[:, ch])[:len(x)]
    return out


# --- loudness ------------------------------------------------------------------
@lru_cache(maxsize=8)
def k_sos(sr):
    """ITU-R BS.1770 K-weighting filter (pre-filter shelf + RLB highpass)."""
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / sr)
    Vh = 10 ** (G / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    s1 = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
          1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / sr)
    a0 = 1 + K / Q + K * K
    s2 = [1.0, -2.0, 1.0, 1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    return np.array([s1, s2])


def lufs(x, sr, return_blocks=False):
    """Integrated loudness (BS.1770-4 gating). x mono or (n, ch)."""
    x = np.asarray(x, dtype=float)
    y = sps.sosfilt(k_sos(sr), x, axis=0)
    p = (y ** 2) if y.ndim == 1 else (y ** 2).sum(axis=1)
    n = len(p)
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if n < blk:
        z = np.array([p.mean() + 1e-20])
    else:
        cs = np.concatenate(([0.0], np.cumsum(p)))
        st = np.arange(0, n - blk + 1, hop)
        z = (cs[st + blk] - cs[st]) / blk
    lj = -0.691 + 10 * np.log10(z + 1e-20)
    g1 = lj > -70
    if not g1.any():
        return (-70.0, lj) if return_blocks else -70.0
    rel = -0.691 + 10 * np.log10(z[g1].mean()) - 10
    g2 = g1 & (lj > rel)
    val = float(-0.691 + 10 * np.log10(z[g2].mean()))
    return (val, lj) if return_blocks else val


def true_peak(x, sr, chunk_s=8.0):
    """4x-oversampled peak (linear), chunked to bound memory."""
    x = stereoize(np.asarray(x, dtype=float))
    n = len(x)
    c = int(chunk_s * sr)
    pk = 0.0
    for s in range(0, n, c):
        a, b = max(0, s - 64), min(n, s + c + 64)
        up = sps.resample_poly(x[a:b], 4, 1, axis=0)
        pk = max(pk, float(np.abs(up).max()))
    return pk


def up2(x):
    """Upsample by 2 (instruments rendered at sr/2 -> sr)."""
    return sps.resample_poly(x, 2, 1, axis=0)


def db(x):
    return 20 * math.log10(max(float(x), 1e-12))


def soft_clip(x, ceiling=0.89, knee=0.6):
    """Transparent below `knee`, tanh-saturates smoothly up to `ceiling`."""
    ax = np.abs(x)
    over = ax > knee
    if over.any():
        r = ceiling - knee
        x = x.copy()
        x[over] = np.sign(x[over]) * (knee + r * np.tanh((ax[over] - knee) / r))
    return x


# =============================================================================
# Pitch / harmony
# =============================================================================
NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
       "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
QUAL = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11),
        "m7": (0, 3, 7, 10), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "sus4": (0, 5, 7),
        "sus2": (0, 2, 7), "7sus4": (0, 5, 7, 10), "add9": (0, 4, 7, 14),
        "madd9": (0, 3, 7, 14), "maj9": (0, 4, 7, 11, 14), "m9": (0, 3, 7, 10, 14),
        "9": (0, 4, 7, 10, 14), "dim": (0, 3, 6), "m7b5": (0, 3, 6, 10), "dim7": (0, 3, 6, 9),
        "aug": (0, 4, 8)}


def note(s):
    """'A2' -> 45, 'C#5' -> 73 (MIDI). Ints pass through."""
    if isinstance(s, (int, np.integer)):
        return int(s)
    m = re.match(r"^([A-G][#b]?)(-?\d)$", s)
    return _PC[m.group(1)] + 12 * (int(m.group(2)) + 1)


def hz(m):
    return 440.0 * 2.0 ** ((float(m) - 69.0) / 12.0)


def nname(m):
    m = int(round(m))
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


class Chord:
    def __init__(self, sym):
        self.sym = sym
        main, _, bass = sym.partition("/")
        r = main[:2] if len(main) > 1 and main[1] in "#b" else main[:1]
        self.root = _PC[r]
        self.qual = main[len(r):]
        self.ivs = QUAL[self.qual]
        self.pcs = sorted({(self.root + i) % 12 for i in self.ivs})
        self.bass = _PC[bass] if bass else self.root
        self.third = next((i for i in self.ivs if i in (3, 4)), self.ivs[1])

    def essentials(self):
        ivs = [i % 12 for i in self.ivs]
        if len(ivs) <= 3:
            return {(self.root + i) % 12 for i in ivs}
        return {(self.root + i) % 12 for i in ivs if i != 7}  # drop the 5th first

    def tones(self, lo, hi):
        return [m for m in range(lo, hi + 1) if m % 12 in self.pcs]

    def bass_note(self, lo, hi):
        return next(m for m in range(lo, hi + 1) if m % 12 == self.bass)

    def root_note(self, lo, hi):
        return next(m for m in range(lo, hi + 1) if m % 12 == self.root)


def voicing(chord, prev=None, n=4, lo=52, hi=74):
    """Pick n chord tones in [lo, hi] covering the essential pitch classes with
    the smallest total movement from `prev` (simple voice leading)."""
    cands = chord.tones(lo, hi)
    ess = chord.essentials()
    if len(ess) > n:
        ess = set(list(ess)[:n])
    best, best_cost = None, 1e9
    third_pc = (chord.root + chord.third) % 12
    for combo in itertools.combinations(cands, n):
        pcs = [c % 12 for c in combo]
        if not ess <= set(pcs):
            continue
        cost = 0.0
        if prev:
            cost += sum(abs(a - b) for a, b in zip(combo, sorted(prev)))
        else:
            cost += abs(np.mean(combo) - (lo + hi) / 2) * 1.5
        gaps = np.diff(combo)
        cost += 3.0 * sum(1 for g in gaps if g > 9)          # avoid wide holes
        cost += 4.0 * sum(1 for g, c in zip(gaps, combo) if g < 3 and c < 55)  # mud
        cost += 3.0 * max(0, pcs.count(third_pc) - 1)       # don't double the 3rd
        if cost < best_cost:
            best, best_cost = list(combo), cost
    return best or cands[:n]


# =============================================================================
# Instruments (mono or stereo float64 arrays at the sr passed in)
# =============================================================================
def inst_pad(midis, dur, sr, rng, cutoff=1400.0, attack=0.6, release=1.4, detune=9.0,
             voices=2, vib=0.0, sustain=0.85, wave="saw"):
    n = secs(sr, dur + release + 0.05)
    t = tvec(n, sr)
    L, R = np.zeros(n), np.zeros(n)
    for m in midis:
        f0 = hz(m)
        for v in range(voices):
            c = detune * ((v / (voices - 1)) * 2 - 1 if voices > 1 else 0) + rng.normal(0, 1.5)
            f = f0 * 2 ** (c / 1200)
            if vib:
                f = f * (1 + vib * np.sin(TAU * rng.uniform(4.5, 5.5) * t + rng.uniform(0, TAU)))
            o = saw(f, n, sr, rng.random()) if wave == "saw" else pulse(f, n, sr, 0.5, rng.random())
            if v % 2 == 0:
                L += o * 0.8
                R += o * 0.45
            else:
                R += o * 0.8
                L += o * 0.45
    x = np.stack([L, R], 1) / (len(midis) * voices * 0.55)
    x = lp(x, cutoff, sr, 4)
    return x * env_adsr(n, sr, attack, 1.0, sustain, release, dur)[:, None]


def inst_brass(midis, dur, sr, rng, peak_fc=1900.0, base_fc=260.0, attack=0.09, release=0.9):
    """'BRAAAM' brass cluster: detuned saws + pulse, filter swell, gentle drive."""
    n = secs(sr, dur + release + 0.05)
    t = tvec(n, sr)
    x = np.zeros(n)
    for m in midis:
        f0 = hz(m)
        for c in (-7, 0, 6):
            x += saw(f0 * 2 ** ((c + rng.normal(0, 1)) / 1200), n, sr, rng.random())
        x += 0.5 * pulse(f0 * 1.001, n, sr, 0.35, rng.random())
    x /= len(midis) * 3.5
    fc = base_fc + (peak_fc - base_fc) * (1 - np.exp(-t / 0.18)) * np.exp(-np.maximum(t - 0.35, 0) / 1.2)
    fc = np.maximum(fc, base_fc * 1.6 * np.minimum(1, t / 0.2) + 1)
    x = tv_filter(x, fc, sr, q=1.1, block=128)
    x = np.tanh(2.2 * x) / np.tanh(2.2)
    return x * env_adsr(n, sr, attack, 1.5, 0.7, release, dur)


def inst_choir(midis, dur, sr, rng, vowel="ah", attack=1.0, release=1.6):
    F = {"ah": [(730, 90, 1.0), (1090, 110, 0.55), (2440, 170, 0.2)],
         "oo": [(320, 60, 1.0), (870, 90, 0.3), (2240, 150, 0.08)],
         "oh": [(560, 80, 1.0), (880, 90, 0.55), (2410, 160, 0.13)]}[vowel]
    n = secs(sr, dur + release + 0.05)
    t = tvec(n, sr)
    L, R = np.zeros(n), np.zeros(n)
    k = 0
    for m in midis:
        for v in range(3):
            f0 = hz(m) * 2 ** (rng.normal(0, 6) / 1200)
            vib = 1 + 0.0035 * np.sin(TAU * rng.uniform(4.6, 5.6) * t + rng.uniform(0, TAU))
            jit = 1 + 0.002 * smooth_noise(n, sr, 3, rng)
            src = saw(f0 * vib * jit, n, sr, rng.random())
            near, far = (L, R) if k % 2 == 0 else (R, L)
            near += src
            far += src * 0.5
            k += 1
    x = np.stack([L, R], 1) / max(1, k * 0.6)
    y = 0.12 * lp(x, 900, sr)
    for fc, bw, g in F:
        y += g * biquad(x, "bandpass", fc, sr, q=fc / bw)
    y += 0.02 * pan(bp(rng.standard_normal(n), 2000, 6000, sr), 0)  # breath
    return y * env_adsr(n, sr, attack, 1.5, 0.9, release, dur)[:, None] * 2.2


def inst_drone(m, dur, sr, rng, fc=240.0):
    n = secs(sr, dur)
    t = tvec(n, sr)
    f0 = hz(m)
    x = saw(f0, n, sr, rng.random()) + saw(f0 * 1.004, n, sr, rng.random()) + 0.5 * sine(f0, n, sr)
    fcv = fc * (1 + 0.45 * np.sin(TAU * 0.11 * t + rng.uniform(0, TAU)))
    x = tv_filter(x, fcv, sr, q=1.2, block=512)
    return x * env_adsr(n, sr, 0.5, 1.0, 1.0, 0.6, dur - 0.6) * 0.5


def inst_stacc(m, dur, sr, rng, fc=1300.0):
    """Short bowed/spiccato low string."""
    n = secs(sr, dur + 0.12)
    f0 = hz(m)
    x = saw(f0, n, sr, rng.random()) + saw(f0 * 1.005, n, sr, rng.random())
    x = lp(x, fc, sr, 2) * 0.5
    return x * env_adsr(n, sr, 0.008, 0.12, 0.25, 0.08, dur)


@lru_cache(maxsize=768)
def _ks(m10, nsamp, bright, t60, seed, sr):
    """Karplus-Strong with fractional-delay tuning (4-tap loop filter)."""
    f = hz(m10 / 10.0)
    P = sr / f
    N = int(math.floor(P)) - 1
    fr = P - math.floor(P)
    a = 0.25 * (1.0 - bright) + 0.04          # loop lowpass amount
    h3 = np.array([a, 1 - 2 * a, a])
    h = np.convolve(h3, [1 - fr, fr])         # delay = N + 1 + fr = P
    g = 10.0 ** (-3.0 / (t60 * f))
    hg = g * h
    rng = np.random.default_rng(seed)
    exc_n = int(P)
    exc = rng.uniform(-1, 1, exc_n)
    exc = lp(exc, 1500 + 7000 * bright, sr, 1)
    pos = max(1, int(exc_n * 0.18))           # pluck position comb
    exc = exc - 0.8 * np.concatenate([np.zeros(pos), exc[:-pos]])
    off = N + 4
    y = np.zeros(nsamp + off)
    x = np.zeros(nsamp + off)
    x[off:off + min(exc_n, nsamp)] = exc[:nsamp]
    B = N
    for s in range(off, nsamp + off, B):
        e = min(nsamp + off, s + B)
        acc = x[s:e].copy()
        for k in range(4):
            acc += hg[k] * y[s - N - k:e - N - k]
        y[s:e] = acc
    out = y[off:]
    out.flags.writeable = False
    return out


def inst_pluck(m, dur, sr, vel=1.0, bright=0.6, t60=1.2, release=0.06, seed=0, body=0.0):
    """Plucked string (KS). `dur` = held time; staccato release afterwards."""
    n = secs(sr, dur + release + 0.02)
    y = np.array(_ks(int(round(m * 10)), n, round(bright, 2), round(t60, 2), seed % 6, sr))
    if body:
        t = tvec(n, sr)
        y = y + body * np.sin(TAU * hz(m) * t) * np.exp(-t / (t60 * 0.35)) * np.clip(t / 0.004, 0, 1)
    y *= env_adsr(n, sr, 0.001, 10.0, 1.0, release, dur, smooth=False)
    return y * vel * 1.4


def inst_epiano(m, dur, vel, sr, release=0.35):
    """FM electric piano (2-op + tine ping), returns stereo with gentle autopan."""
    f = hz(m)
    n = secs(sr, dur + release + 0.02)
    t = tvec(n, sr)
    idx = (0.5 + 1.5 * vel) * np.exp(-t / 0.5) + 0.25
    y = np.sin(TAU * f * t + idx * np.sin(TAU * f * t))
    y += 0.10 * vel * np.exp(-t / 0.05) * np.sin(TAU * 4 * f * t) * min(1.0, 1500 / f)
    amp = (0.6 * np.exp(-t / 0.5) + 0.4 * np.exp(-t / 2.6)) * np.clip(t / 0.002, 0, 1)
    y *= amp * env_adsr(n, sr, 0.001, 9, 1.0, release, dur, smooth=False) * vel
    tr = 0.12 * np.sin(TAU * 3.2 * t)
    return np.stack([y * (1 + tr), y * (1 - tr)], 1)


def inst_bell(m, dur, vel, sr, kind="glock"):
    """Glockenspiel (modal) or FM tubular-ish bell."""
    f = hz(m)
    scale = float(np.clip((1000.0 / f) ** 0.5, 0.5, 1.8))
    n = secs(sr, max(dur, 2.6 * scale) + 0.05)
    t = tvec(n, sr)
    y = np.zeros(n)
    if kind == "glock":
        for r, a, d in ((1.0, 1.0, 1.7), (2.76, 0.28, 0.45), (5.40, 0.08, 0.16), (8.93, 0.025, 0.07)):
            if f * r < 9500:
                y += a * np.exp(-t / (d * scale)) * np.sin(TAU * f * r * t + r)
    else:
        idx = 1.6 * np.exp(-t / 0.45) + 0.2
        y = np.sin(TAU * f * t + idx * np.sin(TAU * 3.5 * f * t)) * np.exp(-t / (2.0 * scale))
    y *= np.clip(t / 0.0015, 0, 1)
    k = int(0.004 * sr)
    y[-k:] *= np.linspace(1, 0, k)
    return y * vel


@lru_cache(maxsize=1024)
def _piano(m, nsamp, gate_n, velq, sr):
    vel = velq / 8.0
    f0 = hz(m)
    t = tvec(nsamp, sr)
    T1 = float(np.clip(4.2 * (261.6 / f0) ** 0.6, 0.7, 9.0))
    K = max(1, min(18, int(6500 / f0)))
    B = 0.00025
    y = np.zeros(nsamp)
    rng = np.random.default_rng(m * 7 + velq)
    norm = 0.0
    for k in range(1, K + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 0.45 * sr:
            break
        a = (1.0 / k ** 1.1) * math.exp(-(k - 1) * (0.5 - 0.3 * vel))
        if k % 7 == 0:
            a *= 0.3   # hammer-position notch
        Tk = T1 / (1 + 0.32 * (k - 1) ** 1.15)
        env = 0.62 * np.exp(-t / (Tk * 0.2)) + 0.38 * np.exp(-t / Tk)
        ph = rng.uniform(0, TAU)
        y += a * env * (np.sin(TAU * fk * t + ph) + 0.7 * np.sin(TAU * fk * 1.00035 * t + ph + 0.3))
        norm += a
    y /= 1.7 * max(norm, 1e-9) ** 0.7
    ham = lp(rng.standard_normal(nsamp), 2200, sr, 2) * np.exp(-t / 0.003) * 0.04 * vel
    y += ham
    y *= np.clip(t / 0.0012, 0, 1)
    damp = np.ones(nsamp)
    if gate_n < nsamp:
        damp[gate_n:] = np.exp(-(t[gate_n:] - t[gate_n]) / 0.11)
    y *= damp
    k = int(0.004 * sr)
    y[-k:] *= np.linspace(1, 0, k)
    y.flags.writeable = False
    return y


def inst_piano(m, dur, vel, sr):
    n = secs(sr, dur + 0.6)
    velq = int(np.clip(round(vel * 8), 1, 10))
    return np.array(_piano(int(m), n, secs(sr, dur), velq, sr)) * (0.55 + 0.45 * vel)


def inst_sub(m, dur, sr, attack=0.01, release=0.15, harm=0.3):
    n = secs(sr, dur + release + 0.02)
    f = hz(m)
    ph = TAU * f * tvec(n, sr)
    y = np.sin(ph) + harm * np.sin(2 * ph) + harm * 0.4 * np.sin(3 * ph)
    return y * env_adsr(n, sr, attack, 0.6, 0.8, release, dur)


def legato_line(notes, total, sr, rng, glide=0.07, vib_depth=0.006, vib_rate=5.6,
                vib_delay=0.22, attack=0.12, release=0.3, cutoff=3200.0, voices=2,
                detune=6.0, wave="saw", brightness=1.0):
    """A continuous expressive line (violin/lead). notes = [(t, midi, dur, vel)].
    Returns (n, 2) for the whole `total` seconds."""
    n = secs(sr, total + release + 0.1)
    t = tvec(n, sr)
    notes = sorted(notes)
    if not notes:
        return np.zeros((n, 2))
    # pitch curve with glides
    bt, bm = [0.0], [notes[0][1]]
    for i, (st, m, d, v) in enumerate(notes):
        bt += [st, st + glide]
        bm += [bm[-1] if i else m, m]
    pitch = np.interp(t, bt, bm)
    # per-note vibrato depth (delayed onset) + amplitude
    vd = np.zeros(n)
    amp = np.zeros(n)
    for i, (st, m, d, v) in enumerate(notes):
        i0 = secs(sr, st)
        nxt = notes[i + 1][0] if i + 1 < len(notes) else 1e9
        legato = nxt - (st + d) < 0.05
        seg_end = min(n, secs(sr, st + d + (0.0 if legato else release)))
        tt = t[i0:seg_end] - st
        vd[i0:seg_end] = np.maximum(vd[i0:seg_end], np.clip((tt - vib_delay) / 0.35, 0, 1))
        a_in = np.clip(tt / attack, 0, 1) ** 1.5 if not (i and notes[i - 1][0] + notes[i - 1][2] > st - 0.05) \
            else 0.8 + 0.2 * np.clip(tt / attack, 0, 1)
        swell = 1 + 0.15 * np.sin(np.pi * np.clip(tt / max(d, 0.1), 0, 1))
        rel = np.where(tt > d, np.exp(-(tt - d) / (release / 4)), 1.0)
        amp[i0:seg_end] = np.maximum(amp[i0:seg_end], v * a_in * swell * rel)
    amp = lp(amp, 30, sr, 1)
    vib = vib_depth * vd * np.sin(TAU * vib_rate * t + 0.3 * smooth_noise(n, sr, 1.5, rng))
    out = np.zeros((n, 2))
    for k in range(voices):
        c = detune * ((k / (voices - 1)) * 2 - 1 if voices > 1 else 0)
        f = hz(0) * 2 ** ((pitch + c / 100) / 12) * (1 + vib)
        o = saw(f, n, sr, rng.random()) if wave == "saw" else pulse(f, n, sr, 0.42, rng.random())
        out += pan(o, (k / max(1, voices - 1) * 2 - 1) * 0.35)
    out /= voices
    out = lp(out, cutoff * brightness, sr, 2)
    out = biquad(out, "peak", 450, sr, 1.0, 2.5)
    out = biquad(out, "peak", 2600, sr, 1.5, 2.0 * brightness)
    return out * amp[:, None]


# --- drums -----------------------------------------------------------------------
def dr_kick(sr, rng, vel=1.0, soft=0.0, decay=0.32):
    n = secs(sr, decay * 2.2)
    t = tvec(n, sr)
    f = 47 + 105 * np.exp(-t / 0.028) + 18 * np.exp(-t / 0.12)
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) * np.exp(-t / decay) * np.clip(t / 0.0015, 0, 1)
    y += 0.25 * np.sin(2 * ph) * np.exp(-t / 0.05)       # phone-audible knock
    y += (0.35 * (1 - soft)) * lp(rng.standard_normal(n), 3500, sr) * np.exp(-t / 0.004)
    return fade_edges(y * vel, sr, 0.0005, 0.02)


def dr_taiko(sr, rng, vel=1.0, size=1.0):
    n = secs(sr, 1.3 * size)
    t = tvec(n, sr)
    f0 = 68.0 / size
    f = f0 * (1 + 0.45 * np.exp(-t / 0.035))
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) * np.exp(-t / (0.42 * size))
    y += 0.45 * np.sin(1.52 * ph + 1) * np.exp(-t / 0.16)
    y += 0.25 * np.sin(2.3 * ph + 2) * np.exp(-t / 0.08)
    y += 0.9 * bp(rng.standard_normal(n), 180, 1400, sr) * np.exp(-t / 0.018)
    y *= np.clip(t / 0.0012, 0, 1)
    return fade_edges(np.tanh(1.4 * y * vel) / np.tanh(1.4), sr, 0.0005, 0.03)


def dr_boom(sr, rng, vel=1.0, length=2.6):
    n = secs(sr, length)
    t = tvec(n, sr)
    f = 31 + 62 * np.exp(-t / 0.07)
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) * np.exp(-t / (length * 0.33))
    y += 0.35 * np.sin(2 * ph) * np.exp(-t / 0.25)
    y += 0.7 * lp(rng.standard_normal(n), 260, sr, 2) * np.exp(-t / 0.45)
    y += 0.25 * bp(rng.standard_normal(n), 900, 3500, sr) * np.exp(-t / 0.012)
    y *= np.clip(t / 0.001, 0, 1)
    return fade_edges(np.tanh(1.3 * y * vel), sr, 0.0005, 0.1)


def dr_snare(sr, rng, vel=1.0, soft=0.0):
    n = secs(sr, 0.35)
    t = tvec(n, sr)
    y = 0.6 * np.sin(TAU * 185 * t) * np.exp(-t / 0.05) + 0.3 * np.sin(TAU * 330 * t) * np.exp(-t / 0.03)
    nz = bp(rng.standard_normal(n), 1200, 7000 - 2500 * soft, sr)
    y += 0.9 * nz * np.exp(-t / (0.11 - 0.03 * soft))
    return fade_edges(y * vel, sr, 0.0005, 0.02)


def dr_clap(sr, rng, vel=1.0):
    n = secs(sr, 0.35)
    t = tvec(n, sr)
    nz = bp(rng.standard_normal(n), 900, 3200, sr)
    e = np.zeros(n)
    for k, d in enumerate((0.0, 0.009, 0.019)):
        e += np.where(t >= d, np.exp(-(t - d) / 0.004), 0) * (0.8 + 0.1 * k)
    e += np.where(t >= 0.021, 0.6 * np.exp(-(t - 0.021) / 0.085), 0)
    return fade_edges(nz * e * vel, sr, 0.0005, 0.02)


def dr_hat(sr, rng, vel=1.0, open_=False):
    n = secs(sr, 0.4 if open_ else 0.09)
    t = tvec(n, sr)
    nz = bp(rng.standard_normal(n), 6500, 11000, sr, 2)
    y = nz * np.exp(-t / (0.16 if open_ else 0.025))
    return fade_edges(y * vel * 0.6, sr, 0.0005, 0.01)


def dr_shaker(sr, rng, vel=1.0):
    n = secs(sr, 0.14)
    t = tvec(n, sr)
    nz = bp(rng.standard_normal(n), 3500, 8000, sr)
    e = np.clip(t / 0.018, 0, 1) * np.exp(-np.maximum(t - 0.018, 0) / 0.035)
    return fade_edges(nz * e * vel * 0.6, sr, 0.001, 0.01)


def dr_wood(sr, rng, vel=1.0, f=1100.0):
    n = secs(sr, 0.16)
    t = tvec(n, sr)
    y = np.sin(TAU * f * t) * np.exp(-t / 0.03) + 0.35 * np.sin(TAU * 2.71 * f * t) * np.exp(-t / 0.01)
    y += 0.3 * bp(rng.standard_normal(n), f, f * 3, sr) * np.exp(-t / 0.002)
    return fade_edges(y * vel, sr, 0.0003, 0.01)


def dr_rim(sr, rng, vel=1.0):
    n = secs(sr, 0.12)
    t = tvec(n, sr)
    y = np.sin(TAU * 1700 * t) * np.exp(-t / 0.012) + 0.6 * np.sin(TAU * 520 * t) * np.exp(-t / 0.02)
    y += 0.4 * bp(rng.standard_normal(n), 1500, 5000, sr) * np.exp(-t / 0.004)
    return fade_edges(y * vel * 0.7, sr, 0.0003, 0.01)


def dr_tom(sr, rng, vel=1.0, f=110.0):
    n = secs(sr, 0.7)
    t = tvec(n, sr)
    ff = f * (1 + 0.5 * np.exp(-t / 0.03))
    y = np.sin(TAU * np.cumsum(ff) / sr) * np.exp(-t / 0.22)
    y += 0.3 * bp(rng.standard_normal(n), 200, 2000, sr) * np.exp(-t / 0.01)
    return fade_edges(y * vel, sr, 0.0005, 0.02)


def dr_timpani(sr, rng, m, vel=1.0, length=2.0):
    n = secs(sr, length)
    t = tvec(n, sr)
    f = hz(m)
    y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.0), (1.5, 0.5, 0.6), (1.98, 0.3, 0.45), (2.44, 0.15, 0.3)):
        y += a * np.sin(TAU * f * r * t + r) * np.exp(-t / (d * length / 2))
    y += 0.4 * lp(rng.standard_normal(n), 1200, sr) * np.exp(-t / 0.008)
    y *= np.clip(t / 0.002, 0, 1)
    return fade_edges(y * vel, sr, 0.0005, 0.05)


def dr_swell(sr, rng, length=2.0, lo=2500.0, hi=9000.0):
    """Reverse-cymbal-ish riser, peaks at the very end."""
    n = secs(sr, length)
    t = tvec(n, sr)
    nz = rng.standard_normal(n)
    nz = tv_filter(nz, lo + (hi - lo) * (t / length) ** 2, sr, "lowpass", q=0.9, block=512)
    nz = hp(nz, 400, sr)
    e = (t / length) ** 2.5
    k = int(0.03 * sr)
    e[-k:] *= np.linspace(1, 0, k)
    return nz * e


# =============================================================================
# Score: event placement + reverb bus + normalization
# =============================================================================
class Score:
    def __init__(self, name, dur, sr, seed=0, tail=4.0):
        self.name = name
        self.sr = sr
        self.lo = sr // 2
        self.dur = float(dur)
        self.n = secs(sr, dur)
        N = self.n + secs(sr, tail)
        self.dry = np.zeros((N, 2))
        self.wet = np.zeros((N, 2))
        self.rng = seeded("music", name, seed)
        self.chords = []    # (t, symbol, voicing)
        self.events = []    # (t, instrument, midi)
        self.rev = dict(rt60=2.0, predelay=0.02, damp=0.5)
        self.wet_gain = 0.35
        self.set_tempo(100)

    def set_tempo(self, bpm, beats_per_bar=4):
        self.bpm = bpm
        self.beat = 60.0 / bpm
        self.bar = beats_per_bar * self.beat
        self.nbars = int(math.ceil(self.dur / self.bar - 1e-9))

    def ht(self, t, sd=0.006):
        return max(0.0, t + float(self.rng.normal(0, sd)))

    def hv(self, v, sd=0.07):
        return float(np.clip(v * (1 + self.rng.normal(0, sd)), 0.05, 1.3))

    def up(self, x):
        return up2(x)

    def chord(self, t, sym, v):
        if t < self.dur:
            self.chords.append((round(t, 3), sym, list(v)))

    def ev(self, t, inst, m):
        if t < self.dur:
            self.events.append((round(t, 3), inst, int(m)))

    def add(self, sig, t, gain=1.0, pan_=0.0, rev=0.0):
        if t >= self.dur or gain == 0:
            return
        sig = np.asarray(sig, dtype=float)
        sig = pan(sig, pan_) if sig.ndim == 1 else sig
        i0 = int(round(t * self.sr))
        if i0 < 0:
            sig = sig[-i0:]
            i0 = 0
        e = min(len(self.dry), i0 + len(sig))
        if e <= i0:
            return
        seg = sig[: e - i0] * gain
        self.dry[i0:e] += seg
        if rev:
            self.wet[i0:e] += seg * rev

    def finish(self, fade_in=0.02, fade_out=1.0, normalize=True):
        sr = self.sr
        out = self.dry
        if self.wet.any():
            out = out + self.wet_gain * reverb(self.wet, sr, **self.rev)
        out = out[: self.n]
        out = hp(out, 28, sr, 2)
        out = biquad(out, "highshelf", 9000, sr, 0.7, -3.0)   # keep the top end polite
        if normalize and np.abs(out).max() > 1e-6:
            L = lufs(out, sr)
            g = float(np.clip(TARGET_LUFS - L, -24, 24))
            out = out * 10 ** (g / 20)
        out = soft_clip(out, 0.89, 0.62)
        n = len(out)
        fi = min(n, secs(sr, fade_in)) if fade_in > 0 else 0
        fo = min(n, secs(sr, fade_out)) if fade_out > 0 else 0
        if fi > 1:      # equal-power shapes (cues crossfade in the mixer)
            out[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi))[:, None]
        if fo > 1:
            out[n - fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))[:, None]
        return out.astype(np.float32)


def _bars(S, prog):
    """Yield (bar_index, t_bar, chord_symbol, pass_index) for every bar that fits."""
    for b in range(S.nbars):
        yield b, b * S.bar, prog[b % len(prog)], b // len(prog)


def _mel(spec):
    """'0:A4:1.5:.8 1.5:D5:.5' -> [(beat, midi, len, vel)]"""
    out = []
    for tok in spec.split():
        p = tok.split(":")
        out.append((float(p[0]), note(p[1]), float(p[2]), float(p[3]) if len(p) > 3 else 0.8))
    return out


# =============================================================================
# Cues
# =============================================================================
def _cue_doom(S):
    """Trailer-parody apocalypse: BRAAAMs, booms, taiko, ominous choir. D minor, 70 BPM."""
    S.set_tempo(70)
    S.rev = dict(rt60=3.2, predelay=0.03, damp=0.55)
    S.wet_gain = 0.45
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["Dm", "Bb", "C", "A"]          # i - bVI - bVII - V, two bars each
    roots = {"Dm": 38, "Bb": 34, "C": 36, "A": 33}
    prev = None
    for ci in range(0, S.nbars, 2):
        sym = prog[(ci // 2) % 4]
        ch = Chord(sym)
        t0 = ci * S.bar
        seg = 2 * S.bar
        r = roots[sym]
        brass = [r, r + 7, r + 12, r + 12 + ch.third, r + 19]
        v = voicing(ch, prev, 3, 57, 74)
        prev = v
        S.chord(t0, sym, brass + v)
        pass_ = ci // 8
        S.add(S.up(inst_brass(brass, seg * 0.62, lo, rng, peak_fc=2600, base_fc=420)), t0, 0.75, 0, 0.35)
        S.add(S.up(inst_brass([m + 12 for m in brass[1:4]], seg * 0.5, lo, rng, peak_fc=3200, base_fc=600)),
              t0 + 0.02, 0.40, 0, 0.5)
        S.add(dr_boom(sr, rng, 1.0), t0, 0.55, 0, 0.25)
        S.add(S.up(inst_choir(v, seg + 0.4, lo, rng, "ah" if pass_ % 2 == 0 else "oh")), t0, 0.55, 0, 0.6)
        S.add(S.up(inst_drone(r, seg + 0.8, lo, rng)), t0 - 0.2 if t0 > 0 else 0, 0.22, 0, 0.1)
        for b in range(2):
            bi = ci + b
            if bi >= S.nbars:
                break
            tb = t0 + b * S.bar
            e8 = S.beat / 2
            if bi % 8 < 4 and pass_ == 0:
                pat = [(0, 1.0, 1.0), (4, 0.8, 1.0)]
            else:
                pat = [(0, 1.0, 1.0), (3, 0.5, 0.7), (4, 0.85, 1.0), (6, 0.5, 0.7), (7, 0.65, 0.7)]
            if b == 1:
                pat += [(6.5, 0.35, 0.6), (7.5, 0.45, 0.6)]
            for pos, vv, size in pat:
                S.add(dr_taiko(sr, rng, S.hv(vv), size), S.ht(tb + pos * e8), 0.55,
                      -0.25 if size < 1 else 0.1, 0.35)
                S.ev(tb + pos * e8, "taiko", 0)
            for q in range(4):     # clock tick (tick-tock), very soft
                S.add(dr_wood(sr, rng, 0.5, 2200 if q % 2 == 0 else 1700), tb + q * S.beat, 0.07,
                      0.4 if q % 2 else -0.4, 0.2)
            if pass_ >= 1 or bi % 8 >= 4:   # low string ostinato drives the second half
                for k in range(8):
                    m = r + (12 if k % 4 == 2 else 0)
                    S.add(S.up(inst_stacc(m, e8 * 0.45, lo, rng)), S.ht(tb + k * e8), S.hv(0.22 if k % 2 else 0.3),
                          0, 0.2)
        if (ci // 2) % 4 == 3:
            S.add(dr_swell(sr, rng, seg * 0.9), t0 + seg * 0.1, 0.10, 0, 0.3)


def _cue_sneaky(S):
    """Cartoon villain tip-toe: pizzicato KS bass + plucks, A minor, 104 BPM, staccato."""
    S.set_tempo(104)
    S.rev = dict(rt60=1.1, predelay=0.012, damp=0.6)
    S.wet_gain = 0.3
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["Am", "Am", "Dm", "Am", "F", "E7", "Am", "E7"]
    root = {"Am": 45, "Dm": 38, "F": 41, "E7": 40}
    mel = [
        _mel("0.75:G#4:.18:.5 1:A4:.3:.8 1.75:B4:.18:.5 2:C5:.3:.85 3:E5:.3:.9 3.5:Eb5:.2:.6"),
        _mel("0:D5:.3:.8 .5:C5:.25:.7 1:B4:.3:.75 2:A4:.45:.8 3.5:E4:.2:.55"),
        _mel("0:F4:.3:.8 1:A4:.3:.8 1.75:C#5:.18:.5 2:D5:.3:.85 3:F5:.3:.9 3.5:E5:.22:.6"),
        _mel("0:E5:.3:.8 .5:C5:.22:.65 1:A4:.3:.75 2:E4:.3:.7 2.5:F4:.2:.55 3:E4:.35:.75"),
        _mel("0.75:E4:.18:.5 1:F4:.3:.8 1.75:G#4:.18:.5 2:A4:.3:.8 3:C5:.3:.85 3.5:A4:.2:.6"),
        _mel("0:B4:.3:.8 .5:G#4:.22:.7 1:E4:.3:.7 2:D5:.3:.85 2.5:C5:.22:.7 3:B4:.3:.75"),
        _mel("0:A4:.3:.8 .5:E4:.18:.6 1:A4:.18:.6 1.5:C5:.18:.7 2:E5:.35:.9"),
        _mel("0:E5:.22:.8 .5:D5:.22:.7 1:B4:.22:.7 1.5:G#4:.22:.7 2:E4:.4:.85"),
    ]
    e8 = S.beat / 2
    prev = None
    for b, tb, sym, pass_ in _bars(S, prog):
        ch = Chord(sym)
        r = root[sym]
        alt = r + 7 if r < 42 else r - 5
        nxt = root[prog[(b + 1) % len(prog)]]
        v = voicing(ch, prev, 3, 52, 67)
        prev = v
        S.chord(tb, sym, v)
        # pizzicato bass: root / alt on the beats, chromatic walk-up into a new root
        bass = [(0, r), (2, alt), (4, r), (6, alt)]
        if nxt != r:
            tgt = nxt if abs(nxt - r) <= 7 else nxt + (12 if nxt < r else -12)
            bass[-1] = (6, tgt - 2)
            bass.append((7, tgt - 1))
        for pos, m in bass:
            vel = S.hv(1.0 if pos == 0 else 0.75 if pos in (2, 4, 6) else 0.6)
            S.add(lp(inst_pluck(m, e8 * 0.55, sr, vel, 0.3, 1.6, 0.07, b * 8 + pos, body=0.35), 2500, sr),
                  S.ht(tb + pos * e8), 0.55, -0.05, 0.12)
            S.ev(tb + pos * e8, "pizz", m)
        # melody plucks (variation: 2nd pass up an octave on bars 1-2 & 5-6)
        oct_ = 12 if pass_ % 2 == 1 and b % 4 in (0, 1) else 0
        for beat, m, ln, vel in mel[b % 8]:
            t = S.ht(tb + beat * S.beat)
            mm = m + oct_
            S.add(lp(inst_pluck(mm, ln * S.beat * 0.7, sr, S.hv(vel), 0.4, 1.0, 0.05, int(beat * 4) + b),
                     4200, sr, 2), t, 0.40, 0.18, 0.25)
            S.ev(t, "pluck", mm)
            if pass_ >= 1 or b % 8 >= 4:       # bassoon-ish double an octave below
                S.add(S.up(_reed(mm - 12, ln * S.beat * 0.75, lo, rng, vel)), t, 0.16, -0.2, 0.2)
        # light percussion: woodblock tick/tock on 2 and 4, soft offbeat hat
        for q in (1, 3):
            S.add(dr_wood(sr, rng, S.hv(0.8), 1250 if q == 1 else 950), S.ht(tb + q * S.beat), 0.13, 0.35, 0.15)
        if pass_ >= 1 or b % 8 >= 2:
            for k in (1, 3, 5, 7):
                S.add(dr_hat(sr, rng, S.hv(0.6)), S.ht(tb + k * e8), 0.06, -0.3, 0.05)
        if b % 2 == 0:
            S.add(S.up(inst_pad(v, 2 * S.bar - 0.2, lo, rng, cutoff=700, attack=0.5, release=0.6,
                                detune=6)), tb, 0.08, 0, 0.3)


def _reed(m, dur, sr, rng, vel=0.8):
    n = secs(sr, dur + 0.1)
    f = hz(m)
    x = pulse(f, n, sr, 0.3, rng.random())
    x = lp(x, 900, sr, 2)
    x = biquad(x, "peak", 500, sr, 2.0, 4.0)
    return x * env_adsr(n, sr, 0.015, 0.1, 0.6, 0.07, dur) * vel


def _cue_ai_calm(S):
    """Warm C lydian: pads, FM e-piano arpeggios, bell sparkles, light brushes. 90 BPM."""
    S.set_tempo(90)
    S.rev = dict(rt60=2.2, predelay=0.025, damp=0.45)
    S.wet_gain = 0.4
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["Cmaj7", "D/C", "Em7", "Am7", "Fmaj7", "G6", "Cmaj7/E", "D/F#"]
    prev = None
    rhythm16 = [0, 3, 6, 8, 11, 14]
    order = [0, 1, 2, 3, 2, 1]
    for b, tb, sym, pass_ in _bars(S, prog):
        ch = Chord(sym)
        v = voicing(ch, prev, 4, 52, 72)
        prev = v
        S.chord(tb, sym, v)
        S.add(S.up(inst_pad(v, S.bar + 0.1, lo, rng, cutoff=2300, attack=0.7, release=1.2, detune=10)),
              tb, 0.30, 0, 0.45)
        bn = ch.bass_note(36, 47)
        S.add(S.up(inst_sub(bn, S.bar * 0.9, lo, 0.03, 0.25, 0.5)), S.ht(tb), 0.20, 0, 0)
        S.ev(tb, "bass", bn)
        if b % 2 == 1:
            S.add(S.up(inst_sub(bn + 12, S.beat * 0.4, lo, 0.01, 0.1, 0.5)), S.ht(tb + 3.5 * S.beat), 0.14)
        # e-piano arpeggio over upper chord tones (+9th)
        ext = sorted(set(ch.tones(60, 79)) | {m for m in range(60, 80) if m % 12 == (ch.root + 2) % 12})
        ext = [m for m in ext if m >= v[0]][:4] or ext[:4]
        if pass_ % 2 == 1:
            ext = [m + 12 if m < 67 else m for m in ext]
        for k, s16 in enumerate(rhythm16):
            m = ext[order[k] % len(ext)]
            t = S.ht(tb + s16 * S.beat / 4)
            vel = S.hv(0.75 if k in (0, 3) else 0.55)
            S.add(inst_epiano(m, S.beat * 0.55, vel, sr), t, 0.48, 0, 0.35)
            S.ev(t, "ep", m)
        # bell sparkle
        if b % 2 == 1 or pass_ >= 1:
            bm = ext[-1] + 12
            S.add(inst_bell(bm, 1.5, S.hv(0.6), sr), S.ht(tb + 2.5 * S.beat), 0.09,
                  0.4 if b % 2 else -0.4, 0.6)
            S.ev(tb + 2.5 * S.beat, "bell", bm)
        # light, playful drums from bar 3 on
        if b >= 2:
            for pos, vel in ((0, 0.8), (2.5, 0.55)):
                S.add(dr_kick(sr, rng, S.hv(vel), soft=1.0, decay=0.25), S.ht(tb + pos * S.beat), 0.2)
            for pos in (1, 3):
                S.add(dr_rim(sr, rng, S.hv(0.7)), S.ht(tb + pos * S.beat), 0.15, 0.15, 0.3)
            for k in range(8):
                sw = 0.08 if k % 2 else 0.0
                S.add(dr_shaker(sr, rng, S.hv(0.7 if k % 2 else 0.45)), S.ht(tb + (k * 0.5 + sw) * S.beat),
                      0.08, -0.35, 0.1)


def _cue_tension(S):
    """'Computing': pulsing 16th ostinato with rising filter, A minor, 110 BPM."""
    S.set_tempo(110)
    S.rev = dict(rt60=1.6, predelay=0.02, damp=0.5)
    S.wet_gain = 0.3
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["Am", "Am", "Fmaj7", "Fmaj7", "Dm7", "Dm7", "Esus4", "E"]
    s16 = S.beat / 4
    n_lo = secs(lo, S.dur + 1.0)
    pitch = np.full(n_lo, 57.0)
    gate = np.zeros(n_lo)
    pad = np.zeros((secs(sr, S.dur + 3.0), 2))
    prev = None
    pat = [0, 2, 1, 2, 0, 2, 1, 3, 0, 2, 1, 2, 0, 3, 1, 2]
    for b, tb, sym, pass_ in _bars(S, prog):
        ch = Chord(sym)
        r = ch.root_note(50, 61)
        tones = [r, r + 7, r + 12, r + 12 + ch.third if ch.third in (3, 4) else r + 17]
        v = voicing(ch, prev, 4, 52, 72)
        prev = v
        S.chord(tb, sym, v)
        for k in range(16):
            t = tb + k * s16
            i0, i1 = secs(lo, t), secs(lo, t + s16)
            if i0 >= n_lo:
                break
            pitch[i0:i1] = tones[pat[k]]
            nn = min(i1, n_lo) - i0
            tt = np.arange(nn) / lo
            acc = 1.0 if k % 4 == 0 else 0.62 if k % 2 == 0 else 0.5
            gate[i0:i0 + nn] = np.maximum(gate[i0:i0 + nn], acc * np.exp(-tt / 0.075) * np.clip(tt / 0.003, 0, 1))
            if k == 0:
                S.ev(t, "ost", tones[0])
        if b % 2 == 0:
            pz = S.up(inst_pad(v, 2 * S.bar, lo, rng, cutoff=900, attack=0.4, release=0.8, detune=8))
            i0 = secs(sr, tb)
            e = min(len(pad), i0 + len(pz))
            pad[i0:e] += pz[: e - i0]
        sub = ch.root_note(33, 44)
        S.add(S.up(inst_sub(sub, S.bar * 0.95, lo, 0.02, 0.1, 0.6)), tb, 0.2)
        for q in range(4):
            if b >= 1 or q >= 2:
                S.add(dr_kick(sr, rng, S.hv(0.7), soft=0.7, decay=0.2), S.ht(tb + q * S.beat, 0.003), 0.2)
            S.add(dr_hat(sr, rng, S.hv(0.5)), S.ht(tb + (q + 0.5) * S.beat, 0.004), 0.10, 0.3)
        # computing blips (A minor pentatonic, high and quiet)
        scale = [81, 84, 86, 88, 91, 93]
        for k in range(16):
            if rng.random() < 0.22:
                m = int(rng.choice(scale))
                nb = secs(sr, 0.09)
                tt = tvec(nb, sr)
                blip = np.sin(TAU * hz(m) * tt) * np.exp(-tt / 0.03) * np.clip(tt / 0.002, 0, 1)
                S.add(fade_edges(blip, sr), S.ht(tb + k * s16, 0.002), 0.07, float(rng.uniform(-0.7, 0.7)), 0.5)
                S.ev(tb + k * s16, "blip", m)
    # ostinato oscillator + rising filter (resets every 4 bars)
    pitch = lp(pitch, 300, lo, 1)
    f = hz(0) * 2 ** (pitch / 12)
    x = 0.6 * saw(f, n_lo, lo) + 0.4 * pulse(f * 1.003, n_lo, lo, 0.5)
    tt = tvec(n_lo, lo)
    phr = (tt % (4 * S.bar)) / (4 * S.bar)
    fc = 450 * (4200 / 450) ** (phr ** 1.3)
    fc = lp(fc, 4, lo, 1)
    x = tv_filter(x * gate, fc, lo, q=1.6, block=128)
    S.add(S.up(x), 0.0, 0.55, 0, 0.25)
    # side-chain style pump on the pad (quarter notes)
    tq = tvec(len(pad), sr) % S.beat
    pump = 1 - 0.55 * np.exp(-tq / 0.11) * np.clip(tq / 0.004, 0, 1)
    S.add(pad * pump[:, None], 0.0, 0.26, 0, 0.35)


def _cue_beg(S):
    """Over-the-top melodramatic strings: D minor, 66 BPM, sobbing violin line."""
    S.set_tempo(66)
    S.rev = dict(rt60=2.8, predelay=0.03, damp=0.45)
    S.wet_gain = 0.5
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["Dm", "Gm", "Bb", "A7", "Dm", "Gm", "Eb", "A7"]
    mel = [
        _mel("0:A4:1.5:.75 1.5:D5:.5:.8 2:F5:2:.95"),
        _mel("0:A5:1.5:1 1.5:G5:2.5:.85"),
        _mel("0:F5:1:.85 1:D5:1:.75 2:Bb4:1:.7 3:D5:1:.8"),
        _mel("0:E5:1.5:.9 1.5:C#5:.5:.75 2:E5:1:.85 3:G5:1:.95"),
        _mel("0:F5:2.5:1 2.5:E5:.5:.8 3:D5:1:.8"),
        _mel("0:Bb5:2:1 2:A5:1:.9 3:G5:1:.85"),
        _mel("0:G5:1.5:.95 1.5:F5:.5:.8 2:Eb5:2:.9"),
        _mel("0:E5:1:.9 1:C#5:1:.8 2:A4:2:.85"),
    ]
    prev = None
    notes = []
    for b, tb, sym, pass_ in _bars(S, prog):
        ch = Chord(sym)
        v = voicing(ch, prev, 4, 55, 74)
        prev = v
        bass = ch.root_note(38, 49)
        S.chord(tb, sym, [bass] + v)
        sw = S.up(inst_strings_sect(v, S.bar + 0.15, lo, rng))
        S.add(sw, tb, 0.42, 0, 0.5)
        S.add(S.up(inst_strings_sect([bass, bass + 12], S.bar + 0.15, lo, rng, cutoff=1200)), tb, 0.30, 0, 0.4)
        for beat, m, ln, vel in mel[b % 8]:
            notes.append((tb + beat * S.beat, m + (12 if pass_ % 2 == 1 and b % 8 in (4, 5) else 0),
                          ln * S.beat, vel))
        if b % 4 == 0:
            S.add(dr_timpani(sr, rng, bass - 12 if bass - 12 >= 36 else bass, 1.0, 2.5), tb, 0.45, 0, 0.3)
        if b % 4 == 3:     # timpani roll into the next downbeat
            m = 45 if sym.startswith("A") else ch.root_note(36, 47)
            t = tb + 1.5 * S.beat
            while t < tb + S.bar - 0.03:
                frac = (t - tb) / S.bar
                S.add(dr_timpani(sr, rng, m, 0.25 + 0.6 * frac, 1.0), t, 0.30, 0, 0.3)
                t += 0.055 + 0.01 * rng.random()
        if b % 8 == 0:     # harp glissando pickup
            scale = [62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81, 82, 84, 86]
            g0 = max(0.0, tb - 0.75 if b else 0.0)
            for i, m in enumerate(scale):
                S.add(inst_pluck(m, 0.6, sr, 0.5 + 0.03 * i, 0.75, 1.8, 0.4, i), g0 + i * 0.045, 0.18,
                      -0.5 + i / len(scale), 0.6)
    for (t, m, d, vv) in notes:
        S.ev(t, "violin", m)
    line = legato_line(notes, S.dur, lo, rng, glide=0.09, vib_depth=0.011, vib_rate=6.3,
                       vib_delay=0.15, attack=0.18, release=0.5, cutoff=3800, voices=3, detune=7)
    S.add(S.up(line), 0.0, 0.5, 0.05, 0.45)


def inst_strings_sect(midis, dur, sr, rng, cutoff=2600.0, attack=0.45, release=0.9):
    """String section: detuned saws with independent vibrato, swelling dynamics."""
    n = secs(sr, dur + release + 0.05)
    t = tvec(n, sr)
    L, R = np.zeros(n), np.zeros(n)
    k = 0
    for m in midis:
        for v in range(3):
            f0 = hz(m) * 2 ** (rng.normal(0, 5) / 1200)
            onset = np.clip((t - 0.2) / 0.4, 0, 1)
            vib = 1 + 0.0045 * onset * np.sin(TAU * rng.uniform(5.2, 6.2) * t + rng.uniform(0, TAU))
            o = saw(f0 * vib, n, sr, rng.random())
            near, far = (L, R) if k % 2 == 0 else (R, L)
            near += o * 0.85
            far += o * 0.4
            k += 1
    x = np.stack([L, R], 1) / max(1, k * 0.55)
    x = lp(x, cutoff, sr, 2)
    x = biquad(x, "peak", 350, sr, 0.9, 2.5)
    swell = 0.7 + 0.3 * np.sin(np.pi * np.clip(t / max(dur, 0.2), 0, 1))
    return x * (env_adsr(n, sr, attack, 1.0, 1.0, release, dur) * swell)[:, None]


def _cue_heart(S):
    """Sincere soft piano + gentle pad. G major, 72 BPM."""
    S.set_tempo(72)
    S.rev = dict(rt60=2.4, predelay=0.02, damp=0.6)
    S.wet_gain = 0.42
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["G", "D/F#", "Em7", "Cadd9", "G/B", "C", "Am7", "Dsus4|D"]
    mel = [
        _mel("0:D5:1.5:.7 1.5:E5:.5:.6 2:D5:1:.65 3:B4:1:.6"),
        _mel("0:A4:2:.65 2:D5:1:.6 3:E5:1:.6"),
        _mel("0:E5:1.5:.7 1.5:F#5:.5:.6 2:G5:1:.7 3:B4:1:.55"),
        _mel("0:D5:3:.65 3:C5:1:.55"),
        _mel("0:B4:1.5:.65 1.5:C5:.5:.55 2:D5:1:.65 3:G5:1:.7"),
        _mel("0:E5:2:.7 2:D5:1:.6 3:C5:1:.55"),
        _mel("0:C5:1.5:.65 1.5:B4:.5:.55 2:A4:1:.6 3:E5:1:.6"),
        _mel("0:D5:2:.65 2:F#4:2:.6"),
    ]
    prev = None
    for b, tb, sym, pass_ in _bars(S, prog):
        halves = sym.split("|")
        for h, hs in enumerate(halves):
            ch = Chord(hs)
            th = tb + h * S.bar / len(halves)
            span = S.bar / len(halves)
            v = voicing(ch, prev, 3, 59, 72)
            prev = v
            bn = ch.bass_note(38, 49)
            S.chord(th, hs, [bn] + v)
            # left hand: bass + broken fifth / octave / tenth, pedal held to bar end
            lh = [bn, bn + 7, bn + 12, bn + 16 if ch.third == 4 and ch.bass == ch.root else bn + 12 + 3]
            if ch.bass != ch.root:
                r = ch.root_note(bn, bn + 11)
                lh = [bn, r, r + 7, r + 12]
            steps = 4 if len(halves) == 1 else 2
            for k in range(steps):
                t = S.ht(th + k * S.beat)
                vel = S.hv(0.62 if k == 0 else 0.42)
                S.add(S.up(inst_piano(lh[k], span - k * S.beat + 0.2, vel, lo)), t, 0.40, -0.15, 0.35)
                S.ev(t, "pianoL", lh[k])
            # right hand chord, gently rolled, on 1 and (softer) on 3
            for k, pos in enumerate((0, 2) if len(halves) == 1 else (0,)):
                for j, m in enumerate(v):
                    t = S.ht(th + pos * S.beat + 0.022 * j, 0.004)
                    S.add(S.up(inst_piano(m, 1.8 * S.beat, S.hv(0.5 if k == 0 else 0.36), lo)), t, 0.28, 0.12, 0.35)
                    S.ev(t, "pianoR", m)
            S.add(S.up(inst_pad(v, span + 0.2, lo, rng, cutoff=850, attack=0.9, release=1.3, detune=7)),
                  th, 0.13, 0, 0.5)
        if pass_ >= 1 or b >= 4:
            for beat, m, ln, vel in mel[b % 8]:
                t = S.ht(tb + beat * S.beat)
                S.add(S.up(inst_piano(m + 12, ln * S.beat * 0.95, S.hv(vel), lo)), t, 0.30, 0.05, 0.4)
                S.ev(t, "melody", m + 12)


def _cue_resolve(S):
    """Hopeful build: D major, bells + pads + light drums, 96 BPM. Layers enter
    as the cue progresses (relative to its own duration)."""
    S.set_tempo(96)
    S.rev = dict(rt60=2.3, predelay=0.025, damp=0.45)
    S.wet_gain = 0.4
    lo, sr, rng = S.lo, S.sr, S.rng
    prog = ["D", "A/C#", "Bm7", "G", "D/F#", "G", "Em7", "Asus4|A"]
    mel = [
        _mel("0:F#5:1.5:.8 1.5:E5:.5:.7 2:D5:1:.75 3:A4:1:.7"),
        _mel("0:E5:1.5:.8 1.5:F#5:.5:.7 2:E5:1:.75 3:C#5:1:.7"),
        _mel("0:D5:1.5:.8 1.5:E5:.5:.7 2:F#5:1:.8 3:A5:1:.85"),
        _mel("0:B5:2:.9 2:A5:1:.8 3:G5:1:.75"),
        _mel("0:F#5:1.5:.85 1.5:G5:.5:.75 2:A5:1:.85 3:D6:1:.9"),
        _mel("0:B5:1.5:.85 1.5:A5:.5:.75 2:G5:1:.8 3:B5:1:.85"),
        _mel("0:A5:1.5:.85 1.5:G5:.5:.75 2:F#5:1:.8 3:E5:1:.75"),
        _mel("0:E5:3:.85 3:A4:1:.7"),
    ]
    bars_total = max(1, S.nbars)
    prev = None
    lead = []
    for b, tb, sym, pass_ in _bars(S, prog):
        sec = min(3, int(4 * b / bars_total)) if bars_total >= 4 else min(3, b)
        if bars_total >= 8:
            sec = min(3, (4 * (b - b % 2)) // bars_total)
        halves = sym.split("|")
        for h, hs in enumerate(halves):
            ch = Chord(hs)
            th = tb + h * S.bar / len(halves)
            span = S.bar / len(halves)
            v = voicing(ch, prev, 4, 54, 74)
            prev = v
            bn = ch.bass_note(38, 49)
            S.chord(th, hs, [bn] + v)
            S.add(S.up(inst_pad(v, span + 0.1, lo, rng, cutoff=1300 + 500 * sec, attack=0.5, release=1.0,
                                detune=11)), th, 0.30 + 0.03 * sec, 0, 0.45)
            if sec >= 2:
                S.add(S.up(inst_strings_sect(v, span + 0.1, lo, rng, cutoff=3000, attack=0.3)), th, 0.18, 0, 0.5)
            # bass: whole notes, then 8th pulses from section 1
            if sec == 0:
                S.add(S.up(inst_sub(bn, span * 0.95, lo, 0.03, 0.2, 0.6)), th, 0.28)
            else:
                for k in range(int(round(span / (S.beat / 2)))):
                    S.add(S.up(inst_sub(bn, S.beat * 0.4, lo, 0.005, 0.06, 0.6)), S.ht(th + k * S.beat / 2, 0.003),
                          S.hv(0.28 if k % 2 == 0 else 0.21))
            S.ev(th, "bass", bn)
            # bell arpeggio: quarters in section 0, 8ths later
            tones = sorted(set(ch.tones(74, 90)))[:4]
            step = S.beat if sec == 0 else S.beat / 2
            k = 0
            t = th
            while t < th + span - 1e-6:
                m = tones[[0, 1, 2, 3, 2, 1][k % 6] % len(tones)]
                S.add(inst_bell(m, 1.0, S.hv(0.55 if k % 2 else 0.7), sr), S.ht(t, 0.004), 0.12,
                      0.3 if k % 2 else -0.3, 0.45)
                S.ev(t, "bell", m)
                t += step
                k += 1
        # drums
        if sec >= 1:
            kicks = (0, 2) if sec == 1 else (0, 1, 2, 3)
            for q in kicks:
                S.add(dr_kick(sr, rng, S.hv(0.85), soft=0.5), S.ht(tb + q * S.beat, 0.003), 0.28)
            for q in (1, 3):
                S.add(dr_clap(sr, rng, S.hv(0.7)), S.ht(tb + q * S.beat, 0.004), 0.20, 0.1, 0.35)
            for k in range(8):
                S.add(dr_shaker(sr, rng, S.hv(0.7 if k % 2 else 0.45)), S.ht(tb + k * S.beat / 2, 0.004),
                      0.09, -0.3, 0.1)
        if sec >= 3:
            for k in (1, 3, 5, 7):
                S.add(dr_hat(sr, rng, S.hv(0.5), open_=True), S.ht(tb + k * S.beat / 2), 0.06, 0.3, 0.2)
            if b % 8 == 7:
                for j, f in enumerate((180, 150, 120, 95)):
                    S.add(dr_tom(sr, rng, 0.7 + 0.08 * j, f), tb + (2 + j * 0.5) * S.beat, 0.30, 0.4 - 0.25 * j, 0.3)
        if sec >= 2:
            for beat, m, ln, vel in mel[b % 8]:
                lead.append((tb + beat * S.beat, m, ln * S.beat * 0.97, vel))
                if sec >= 3:
                    S.add(inst_bell(m + 12, 1.2, vel * 0.6, sr), S.ht(tb + beat * S.beat, 0.003), 0.07, 0.2, 0.5)
    for (t, m, d, vv) in lead:
        S.ev(t, "lead", m)
    if lead:
        line = legato_line(lead, S.dur, lo, rng, glide=0.05, vib_depth=0.004, vib_rate=5.2, vib_delay=0.3,
                           attack=0.06, release=0.35, cutoff=2400, voices=2, detune=5, wave="pulse")
        S.add(S.up(line), 0.0, 0.38, 0, 0.45)
    if bars_total >= 6:      # cymbal-ish swell into the last section
        b3 = next((b for b in range(S.nbars) if (4 * (b - b % 2)) // bars_total >= 3), None)
        if b3:
            S.add(dr_swell(sr, rng, 2 * S.beat), b3 * S.bar - 2 * S.beat, 0.12, 0, 0.3)


_CUE_FN = {"doom": _cue_doom, "sneaky": _cue_sneaky, "ai_calm": _cue_ai_calm,
           "tension": _cue_tension, "beg": _cue_beg, "heart": _cue_heart, "resolve": _cue_resolve}


def compose(name, dur, sr=SR, seed=0):
    """Build (but do not finish) a Score — exposes chords/events for inspection."""
    S = Score(name, dur, sr, seed)
    _CUE_FN[name](S)
    return S


def render_cue(name, dur, sr=SR, fade_in=0.02, fade_out=1.0, seed=0):
    """Render cue `name` for `dur` seconds -> float32 (round(dur*sr), 2)."""
    n = secs(sr, dur)
    if not name or name == "none" or name not in _CUE_FN or dur <= 0:
        if name and name != "none" and name not in _CUE_FN:
            print(f"[music] unknown cue '{name}', rendering silence")
        return np.zeros((n, 2), np.float32)
    S = compose(name, dur, sr, seed)
    out = S.finish(fade_in=fade_in, fade_out=min(fade_out, dur / 2))
    if len(out) < n:
        out = np.concatenate([out, np.zeros((n - len(out), 2), np.float32)])
    return out[:n]


def describe(name, dur=20.0, sr=SR):
    """Human-readable chord/melody summary (for sanity checks)."""
    S = compose(name, dur, sr)
    lines = [f"{name}: {S.bpm} BPM, bar {S.bar:.2f}s"]
    for t, sym, v in S.chords:
        lines.append(f"  {t:6.2f}s {sym:8s} " + " ".join(nname(m) for m in v))
    return "\n".join(lines), S


if __name__ == "__main__":
    import sys
    import time
    import soundfile as sf
    for c in sys.argv[1:] or CUES[1:]:
        t = time.time()
        y = render_cue(c, 20)
        sf.write(f"/tmp/music_{c}.wav", y, SR)
        print(c, f"{time.time()-t:.2f}s", f"lufs {lufs(y, SR):.1f}", f"peak {db(np.abs(y).max()):.1f}")
