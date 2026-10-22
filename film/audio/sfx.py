#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- procedural foley, scene ambiences and crowd walla (SPEC section 5).

    from film.audio import sfx
    y = sfx.render_cue("stamp_thunk", {"gain_db": -2, "pan": 0.1}, seed=7)   # (n, 2) float64, 48 kHz
    a = sfx.ambience(3, ctx)                                                  # scene 3 rain bed, (n, 2)
    python3 film/audio/sfx.py --sheet       # every foley kind back to back -> film/build/audio/foley_sheet.wav
    python3 film/audio/sfx.py --amb 3       # one scene's ambience -> film/build/audio/amb_s3.wav

FOLEY (one deterministic synthesis function per SFX kind; `KINDS`)
  Physical-ish models, all numpy: resonant MODES (sums of exponentially decaying sinusoids) excited by
  short noise bursts / impulses for wood, stone, glass, brass and iron; stick-slip pulse trains through a
  wood-body modal response for creaks; GRANULAR streams (Poisson clicks through band-passes) for gravel,
  crust crackle, crumbs, embers, sand and paper; Karplus-Strong (song.py's ks_string + lute body) for the
  lute pluck; formant-filtered breath for the sigh; pitched AM tones for the pigeon coo.  Every cue gets its
  own seed (scene, index, kind, time), and each model randomises its modes, timings and levels from it, so
  repeated cues never sound identical while the whole film stays reproducible.

  Cue params (all optional; unknown keys are ignored, non-dict params are tolerated):
    gain_db / gain / db   level offset in dB (default 0 = the kind's calibrated level)
    vol / volume / level  linear gain multiplier
    pan / x               stereo position -1 (left) .. 1 (right); x in 0..1920 px is also accepted
    dist / distance       0 (close) .. 1 (far): quieter, duller, more of the scene's room
    vel / intensity       0..1 strength for the kinds that model force (default ~0.7)
    dur / duration        seconds, for kinds with a length (creaks, scrapes, rustles, glows)
    plus kind-specific keys: surface (stone|cobble|wood|gravel|grass), weight (0..1), claws (bool),
    material (glass|jar|pills|candle|book|wood|pewter|crystal|door), count / n, size (dragon|bird|small),
    midi / pitch, heavy (bool), dir (up|down), who.
  Unknown kinds map to the nearest known kind (alias table, then difflib) with a warning.

AMBIENCES (`ambience(scene, ctx)`; ctx = {"dur", "beats", "lines", "cues", "walla", ...}, all scene-local)
  S0 cosy hearth (roar, crackle, snaps), candle flutter, warm room tone
  S1 wash-house: tumbling wooden drums (rotation rumble, cloth swish, tumbling thumps, brass rattles,
     axle creaks), buzzing caged wisp-lamps (detuned cluster with flicker), cold night wind at the windows
  S2 apothecary: humming white light-orbs (beating cluster + a glassy singing overtone), bubbling alembic,
     shop room tone
  S3 rain in layers (far hiss, mid patter, near drops on cobbles/puddles, hits on shutters), a gutter
     spout, eave drips, distant thunder rolls, a far-off watchman's handbell
  S4 tavern: outside street wind + muffled chatter through the door; inside loud chatter + tankards; the
     swell roar; perspective switches (outside / inside / outside) are hard, at s4_inside and the door
  S5 square at evening: wind, far town, a crowd cheering (layered Piper walla) that CUTS to near-silence
     at s5_silence, then sparse uneasy murmurs that thin out as the crowd turns away
  S6 dusk garden: blackbirds/robins settling (fewer as it darkens), "chink" roost calls, pigeon coos,
     castle bells far off during the long pause, breeze in the oak
  S7 the same garden warming: more pigeons, a warm murmur that grows as the bench fills
  S8 night: crickets, an owl between the voice-over lines, soft close conversation murmur
  S9 near-silence (the faintest warm room tone)

WALLA (`Walla`)
  Many LibriTTS-R / VCTK Piper speakers (hand-picked lists below, never the film's cast voices) saying
  period crowd words ("Have at him!", "Huzzah!", "Fight! Fight!", tavern chatter, gentle bench talk),
  synthesized deterministically through song.py's TimedPiper (seeded noise inputs, duration control) and
  cached in film/build/audio/walla/.  The tavern's uncanny synchronized laughter and the swell's unison
  "Hey!" force IDENTICAL phoneme durations on every speaker, so all heads laugh in perfect sync; a laugh cue
  that carries the picture's laugh clock ({"dur", "bpm"}, as S4 does) gets exactly round(dur*bpm/60) HAs
  whose vowels land on that beat (+-10 ms), so the crowd's mouths and the sound start and stop together.
"""
from __future__ import annotations

import difflib
import hashlib
import math
import os
import sys
import zlib

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, oaconvolve, resample_poly, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from film.audio import song as SONG  # noqa: E402  (KS lute, hall IR, biquads, loudness)

SR = 48000
BUILD = os.path.join(FILM, "build", "audio")
WALLA_DIR = os.path.join(BUILD, "walla")

_WARNED = set()


def warn(msg):
    if msg not in _WARNED:
        _WARNED.add(msg)
        print("[sfx] warning:", msg, file=sys.stderr, flush=True)


def seed_of(*parts) -> int:
    """Stable 31-bit seed from any parts (scene, index, kind, time ...)."""
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


# ================================================================================================
# DSP helpers
# ================================================================================================
def ns(sec: float) -> int:
    return max(1, int(round(sec * SR)))


def tvec(n: int) -> np.ndarray:
    return np.arange(n) / SR


_SOS = {}


def _sos(kind, a, b=None, order=2):
    key = (kind, round(a, 3), None if b is None else round(b, 3), order)
    s = _SOS.get(key)
    if s is None:
        ny = SR / 2
        if kind == "low":
            s = butter(order, min(a, 0.45 * SR) / ny, "low", output="sos")
        elif kind == "high":
            s = butter(order, max(a, 5.0) / ny, "high", output="sos")
        else:
            lo, hi = max(a, 5.0), min(b, 0.45 * SR)
            s = butter(order, [lo / ny, max(hi, lo * 1.05) / ny], "band", output="sos")
        _SOS[key] = s
    return s


def lp(x, fc, order=2):
    return sosfilt(_sos("low", fc, order=order), x, axis=0)


def hp(x, fc, order=2):
    return sosfilt(_sos("high", fc, order=order), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(_sos("band", lo, hi, order), x, axis=0)


def peq(x, f, gain_db, q=1.0):
    b, a = SONG.biquad_peak(f, gain_db, q)
    return lfilter(b, a, x, axis=0)


def shelf(x, f, gain_db, high=True):
    b, a = SONG.biquad_shelf(f, gain_db, high=high)
    return lfilter(b, a, x, axis=0)


def reson(x, f, q):
    """Constant-0dB-peak resonant band-pass (RBJ BPF)."""
    w = 2 * np.pi * min(f, 0.45 * SR) / SR
    al = np.sin(w) / (2 * q)
    b = np.array([al, 0.0, -al])
    a = np.array([1 + al, -2 * np.cos(w), 1 - al])
    return lfilter(b / a[0], a / a[0], x, axis=0)


def white(rng, n):
    return rng.standard_normal(n)


def pink(rng, n):
    """Pink (1/f power) noise, unit std."""
    m = 1 << int(np.ceil(np.log2(max(n, 2))))
    X = np.fft.rfft(rng.standard_normal(m))
    f = np.fft.rfftfreq(m, 1 / SR)
    f[0] = f[1]
    X /= np.sqrt(f)
    y = np.fft.irfft(X, m)[:n]
    return y / (y.std() + 1e-12)


def brown(rng, n, leak=0.9985):
    y = lfilter([1.0], [1.0, -leak], rng.standard_normal(n))
    y -= y.mean()
    return y / (y.std() + 1e-12)


def smooth_rand(rng, n, rate_hz, lo=0.0, hi=1.0):
    """Slow random curve in [lo, hi] with ~rate_hz independent points per second (cosine-interpolated at a
    2 kHz control rate, then linearly to audio rate)."""
    k = max(2, int(n / SR * rate_hz) + 3)
    pts = rng.uniform(lo, hi, k)
    m = max(2, int(n / SR * 2000) + 2)
    x = np.linspace(0, k - 2.0001, m)
    i = np.floor(x).astype(int)
    f = x - i
    f = 0.5 - 0.5 * np.cos(np.pi * f)
    c = pts[i] * (1 - f) + pts[i + 1] * f
    return np.interp(np.linspace(0, m - 1, n), np.arange(m), c)


def env_ar(n, att, rel, shape=1.0):
    """Attack (raised cosine) then exponential release with time constant `rel` (s)."""
    t = tvec(n)
    a = np.clip(t / max(att, 1e-4), 0, 1)
    a = (0.5 - 0.5 * np.cos(np.pi * a)) ** shape
    return a * np.exp(-np.maximum(t - att, 0) / max(rel, 1e-4))


def hump(n, peak_frac=0.4, p=1.6):
    """Smooth 0 -> 1 -> 0 bump."""
    x = np.linspace(0, 1, n)
    a = np.clip(x / max(peak_frac, 1e-3), 0, 1)
    b = np.clip((1 - x) / max(1 - peak_frac, 1e-3), 0, 1)
    return (np.sin(0.5 * np.pi * a) * np.sin(0.5 * np.pi * b)) ** p


def modes(rng, spec, n, jitter=0.03, amp_jit=0.25):
    """Impulse response of resonant modes: spec = [(freq, tau_s, amp), ...] (randomized slightly)."""
    t = tvec(n)
    y = np.zeros(n)
    for f, tau, a in spec:
        f = f * (1 + jitter * rng.standard_normal())
        if f >= 0.47 * SR:
            continue
        tau = tau * (1 + 0.15 * rng.standard_normal())
        m = min(n, ns(max(tau, 1e-4) * 9))
        a = a * (1 + amp_jit * rng.standard_normal())
        y[:m] += a * np.exp(-t[:m] / max(tau, 1e-4)) * np.sin(2 * np.pi * f * t[:m] + rng.uniform(0, 2 * np.pi))
    k = min(n, 15)                                        # 0.3 ms onset: no step at t=0 (random phases)
    y[:k] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))
    return y


def excite(src, ir):
    if len(src) > 16 * len(ir) and len(ir) > 64:
        return oaconvolve(src, ir)[: len(src) + len(ir) - 1]
    return fftconvolve(src, ir)[: len(src) + len(ir) - 1]


def fit(x, n):
    """Trim / zero-pad x (axis 0) to exactly n samples."""
    if len(x) >= n:
        return x[:n]
    return np.pad(x, [(0, n - len(x))] + [(0, 0)] * (x.ndim - 1))


def burst(rng, n, tau, lo=None, hi=None):
    """Noise burst with exponential decay, optionally band-passed."""
    y = white(rng, n) * np.exp(-tvec(n) / max(tau, 1e-4))
    k = min(n, 8)                                         # 0.15 ms attack: no digital step
    y[:k] *= np.linspace(0.0, 1.0, k)
    if lo and hi:
        y = bp(y, lo, hi)
    elif hi:
        y = lp(y, hi)
    elif lo:
        y = hp(y, lo)
    return y


def grains(rng, n, rate, dur_s=None, amp_sigma=0.6, env=None):
    """Sparse impulse train: Poisson onsets at `rate` per second (optionally times env), log-normal amps."""
    total = n / SR if dur_s is None else dur_s
    k = rng.poisson(max(rate * total, 0.0))
    y = np.zeros(n)
    if k <= 0:
        return y
    pos = rng.integers(0, n, k)
    amp = np.exp(amp_sigma * rng.standard_normal(k)) * rng.choice([-1.0, 1.0], k)
    if env is not None:
        keep = rng.uniform(0, 1, k) < np.clip(env[pos], 0, 1)
        pos, amp = pos[keep], amp[keep] * np.clip(env[pos[keep]], 0, 1) ** 0.5
    np.add.at(y, pos, amp)
    return np.convolve(y, (0.25, 0.5, 0.25), "same")          # no energy at Nyquist: soft, not digital


def grain_bank(rng, n, rate, f_lo, f_hi, tau=(0.0008, 0.003), banks=10, amp_sigma=0.7, env=None):
    """Granular stream whose grains ring at MANY random resonances (no fixed tonal bands): rain, crackle."""
    y = np.zeros(n)
    for _ in range(banks):
        g = grains(rng, n, rate / banks, amp_sigma=amp_sigma, env=env)
        f = math.exp(rng.uniform(math.log(f_lo), math.log(f_hi)))
        ir = modes(rng, [(f, rng.uniform(*tau), 1.0), (f * rng.uniform(1.4, 2.3), rng.uniform(*tau) * 0.7, 0.45)],
                   ns(0.02))
        y += oaconvolve(g, ir)[:n]
    return y


def place(dst, src, i0):
    """dst[i0:i0+len(src)] += src (bounds-safe; 1-D or 2-D)."""
    i0 = int(i0)
    if i0 >= len(dst) or i0 + len(src) <= 0:
        return dst
    a = max(0, -i0)
    b = min(len(src), len(dst) - i0)
    dst[i0 + a: i0 + b] += src[a:b]
    return dst


def stereo(x, p=0.0):
    """Equal-power pan of mono x (p -1..1) -> (n, 2)."""
    p = float(np.clip(p, -1, 1))
    th = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], 1)


def wide(rng, maker, n, width=1.0):
    """Two decorrelated renders of a mono maker(rng, n) -> stereo, mid/side width."""
    a, b = maker(rng, n), maker(rng, n)
    m, s = 0.5 * (a + b), 0.5 * (a - b) * width
    return np.stack([m + s, m - s], 1)


def peak_norm(x, peak=1.0):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


def fade(x, fin=0.002, fout=0.006):
    n = len(x)
    a, b = min(n // 2, ns(fin)), min(n // 2, ns(fout))
    if a > 1:
        x[:a] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a)))[:, None] if x.ndim == 2 else \
            0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if b > 1:
        r = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
        x[-b:] *= r[:, None] if x.ndim == 2 else r
    return x


def varispeed(x, ratio):
    """Resample by `ratio` (> 1 = higher and shorter), linear interpolation (fine for walla / foley)."""
    if abs(ratio - 1.0) < 1e-4:
        return x
    n = int(len(x) / ratio)
    pos = np.arange(n) * ratio
    if x.ndim == 1:
        return np.interp(pos, np.arange(len(x)), x)
    return np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], 1)


_KW = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585],
       [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def lufs(x):
    """BS.1770-4 integrated loudness (48 kHz K-weighting, 400 ms blocks / 75 % overlap, -70 LUFS absolute and
    -10 LU relative gates), vectorized; -70 for silence."""
    x = np.asarray(x, np.float64)
    if not np.any(x):
        return -70.0
    if x.ndim == 1:
        x = x[:, None]
    b1, a1, b2, a2 = _KW
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < blk:
        return -70.0
    cs = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y * y, axis=0)])
    idx = np.arange(0, len(y) - blk + 1, hop)
    z = ((cs[idx + blk] - cs[idx]) / blk).sum(axis=1)
    lj = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lj > -70]
    if len(z1) == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(z1)) - 10
    z2 = z[lj > max(rel, -70)]
    return float(-0.691 + 10 * np.log10(np.mean(z2) + 1e-20))


def to_lufs(x, target):
    """Scale x so its integrated loudness is `target` LUFS (deterministic level calibration)."""
    lv = lufs(x)
    if lv <= -69.0:
        return x
    return x * 10 ** ((target - lv) / 20)


def softclip(x, drive=1.5):
    return np.tanh(drive * x) / np.tanh(drive)


def no_sub(x, fc=45.0):
    """Remove the subsonic part of a rumble (brown noise piles most of its energy below ~40 Hz: inaudible on
    laptops/phones, a woofer-pumping, headroom-eating offset on big systems) and give the audible band back
    its loudness (K-weighted), so the rumble sounds as big as before."""
    y = hp(x, fc, 4)
    l0, l1 = lufs(x), lufs(y)
    return y * 10 ** ((l0 - l1) / 20) if (l0 > -69 and l1 > -69) else y


# ================================================================================================
# acoustic spaces (stereo IRs, unit energy per channel) -- cached
# ================================================================================================
_IR = {}


def outdoor_ir(rt60=0.8, slaps=((0.045, 0.35), (0.071, 0.25), (0.113, 0.16)), seed=5, tail_db=-6.0,
               lp_hz=6000.0):
    """Open-air space: a few discrete facade reflections + a short, dark diffuse tail."""
    rng = np.random.default_rng(seed)
    n = ns(rt60 * 1.2 + 0.15)
    t = tvec(n)
    out = []
    for ch in range(2):
        y = white(rng, n) * np.exp(-6.91 * t / rt60) * np.clip((t - 0.02) / 0.03, 0, 1) * 10 ** (tail_db / 20)
        y = lp(y, lp_hz)
        for d, g in slaps:
            k = ns(d * (1 + 0.06 * rng.standard_normal()))
            if k < n:
                y[k] += g * (1.0 if rng.uniform() > 0.3 else -1.0)
        y[0] = 0.0
        out.append(y / np.sqrt(np.sum(y * y) + 1e-12))
    return np.stack(out, 1)


def space(name):
    """Named scene spaces."""
    if name in _IR:
        return _IR[name]
    if name == "nook":
        ir = SONG.hall_ir(0.6, 0.006, seed=21)
    elif name == "stonehall":
        ir = SONG.hall_ir(1.75, 0.024, seed=22)
    elif name == "shop":
        ir = SONG.hall_ir(0.5, 0.005, seed=23)
    elif name == "street":
        ir = outdoor_ir(0.9, ((0.031, 0.42), (0.052, 0.3), (0.083, 0.22), (0.129, 0.12)), seed=24)
    elif name == "tavern":
        ir = SONG.hall_ir(0.95, 0.010, seed=25)
    elif name == "square":
        ir = outdoor_ir(1.25, ((0.062, 0.4), (0.094, 0.3), (0.151, 0.2), (0.23, 0.12)), seed=26, tail_db=-3)
    elif name == "garden":
        ir = outdoor_ir(0.55, ((0.09, 0.18), (0.21, 0.1)), seed=27, tail_db=-9, lp_hz=4500)
    elif name == "vo":
        ir = SONG.hall_ir(0.42, 0.003, seed=28)
        ir = lp(ir, 5200)
        ir /= np.sqrt(np.sum(ir * ir, axis=0, keepdims=True))
    elif name == "shimmer":     # the speaking stone's faint magical shimmer: bright, slightly longer
        ir = SONG.hall_ir(1.3, 0.012, seed=29)
        ir = hp(ir, 2500)
        ir /= np.sqrt(np.sum(ir * ir, axis=0, keepdims=True))
    elif name == "far":         # distant sources (bells, thunder): long dark tail
        ir = outdoor_ir(2.4, ((0.12, 0.3), (0.26, 0.2)), seed=30, tail_db=0, lp_hz=3000)
    else:
        raise KeyError(name)
    _IR[name] = ir
    return ir


SCENE_SPACE = {0: "nook", 1: "stonehall", 2: "shop", 3: "street", 4: "tavern", 5: "square",
               6: "garden", 7: "garden", 8: "garden", 9: "nook"}


def reverb(x, name):
    ir = space(name)
    if x.ndim == 1:
        x = np.stack([x, x], 1) * 0.7071
    return np.stack([fftconvolve(x[:, 0], ir[:, 0]), fftconvolve(x[:, 1], ir[:, 1])], 1)


# ================================================================================================
# FOLEY KINDS.  Each: f(rng, p) -> mono (or stereo) float64, peak ~1.  Calibrated level in LEVEL_DB.
# ================================================================================================
def _num(p, keys, default):
    for k in keys:
        if k in p and p[k] is not None:
            try:
                return float(p[k])
            except (TypeError, ValueError):
                pass
    return default


def _str(p, keys, default):
    for k in keys:
        if k in p and p[k] is not None:
            return str(p[k]).lower()
    return default


def _impact(rng, n, f_low, tau_low, vel=0.7, click_hz=3000.0):
    """Generic body impact: pitched-down low thump + short broadband knock."""
    t = tvec(n)
    f = f_low * (1 + 0.35 * np.exp(-t / 0.008))
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau_low)
    kn = burst(rng, n, 0.0035, hi=click_hz)
    return th * (0.7 + 0.3 * vel) + 0.45 * vel * kn


WOOD_FLOOR = [(118, 0.035, 1.0), (243, 0.026, 0.7), (387, 0.018, 0.55), (611, 0.013, 0.4), (934, 0.009, 0.28),
              (1420, 0.006, 0.18), (2150, 0.004, 0.1)]
WOOD_COUNTER = [(162, 0.04, 0.8), (331, 0.03, 1.0), (523, 0.022, 0.75), (887, 0.016, 0.5), (1310, 0.011, 0.35),
                (1980, 0.007, 0.22), (2870, 0.005, 0.12)]
WOOD_PLAQUE = [(436, 0.022, 1.0), (861, 0.016, 0.75), (1347, 0.012, 0.6), (2093, 0.008, 0.4), (3180, 0.005, 0.2),
               (4410, 0.003, 0.1)]
STONE = [(1620, 0.006, 0.6), (2730, 0.005, 0.5), (3980, 0.004, 0.35), (5650, 0.003, 0.2)]
GLASS_BOTTLE = [(1180, 0.32, 0.6), (2413, 0.24, 1.0), (3955, 0.16, 0.6), (5612, 0.1, 0.35), (7410, 0.06, 0.2)]
GLASS_JAR = [(860, 0.12, 0.8), (1720, 0.09, 1.0), (2940, 0.06, 0.6), (4310, 0.04, 0.3)]
BRASS_BELL = [(2093, 1.3, 1.0), (4856, 0.75, 0.55), (8890, 0.32, 0.3), (1410, 0.9, 0.18), (6300, 0.45, 0.2)]
IRON = [(312, 0.12, 0.6), (697, 0.09, 0.8), (1265, 0.06, 0.6), (2087, 0.04, 0.4), (3311, 0.025, 0.25)]
PEWTER = [(880, 0.09, 1.0), (1530, 0.07, 0.7), (2610, 0.05, 0.45), (3890, 0.03, 0.25)]


def k_footstep(rng, p):
    surface = _str(p, ("surface", "material", "floor"), "stone")
    weight = float(np.clip(_num(p, ("weight", "size_f"), 0.6), 0, 1))
    who = _str(p, ("who", "character", "speaker"), "")
    if any(k in who for k in ("troll", "minotaur", "dragon", "orc")):
        weight = max(weight, 0.75)
    if any(k in who for k in ("gnome", "pixie", "faun", "lioness", "elf")):
        weight = min(weight, 0.35)
    claws = bool(p.get("claws", "dragon" in who))
    vel = _num(p, ("vel", "intensity"), 0.7)
    n = ns(0.42)
    y = np.zeros(n)
    t_toe = rng.uniform(0.04, 0.075) * (1 + 0.5 * weight)
    for k, (t0, a) in enumerate(((0.0, 1.0), (t_toe, rng.uniform(0.4, 0.6)))):
        m = n - ns(t0)
        hit = _impact(rng, m, 85 - 35 * weight + rng.uniform(-8, 8), 0.016 + 0.03 * weight, vel,
                      1800 + 1500 * (1 - weight)) * a
        if surface in ("stone", "cobble", "cobbles", "street"):
            grit = burst(rng, m, rng.uniform(0.008, 0.016), 1400, 6500) * 0.35
            ring = excite(burst(rng, ns(0.002), 0.0008), modes(rng, STONE, ns(0.05)))[:m] * 0.08
            hit = hit + grit + np.pad(ring, (0, max(0, m - len(ring))))[:m]
        elif surface in ("wood", "floor", "boards"):
            body = excite(burst(rng, ns(0.004), 0.0012), modes(rng, WOOD_FLOOR, ns(0.25)))[:m]
            hit = 0.7 * hit + 0.06 * np.pad(body, (0, max(0, m - len(body))))[:m]
        elif surface in ("gravel", "path", "garden"):
            gr = grains(rng, m, rng.uniform(350, 600) * (0.7 + 0.6 * weight))
            g_env = env_ar(m, 0.004, 0.05 + 0.04 * weight)
            hit = 0.6 * hit + 0.9 * bp(gr * g_env, 1500, 8000)
        elif surface in ("grass", "soft"):
            hit = 0.5 * hit + 0.3 * lp(white(rng, m) * env_ar(m, 0.01, 0.06), 3000)
        y[ns(t0):] += hit
    if claws and surface not in ("grass", "soft"):     # dragon claws tick on hard ground
        for _ in range(rng.integers(1, 3)):
            i0 = ns(t_toe + rng.uniform(0.0, 0.02))
            tk = excite(burst(rng, ns(0.001), 0.0004), modes(rng, [(4200, 0.004, 1), (6100, 0.003, 0.6)], ns(0.02)))
            place(y, 0.12 * tk, i0)
    scuff = bp(white(rng, n) * hump(n, 0.25) * np.exp(-tvec(n) / 0.12), 900, 4200) * 0.08 * (0.5 + weight)
    return fade(peak_norm(y + scuff), 0.0005, 0.03)


def _droplets(rng, n, count, t_from=0.02, t_to=0.25, f_lo=1100, f_hi=3600, amp=0.25):
    y = np.zeros(n)
    for _ in range(count):
        m = ns(rng.uniform(0.008, 0.02))
        f0 = rng.uniform(f_lo, f_hi)
        tt = tvec(m)
        f = f0 * (1 + 0.5 * tt / tt[-1])                       # Minnaert-style upward chirp
        d = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (m / SR / 3)) * np.clip(tt / 0.0008, 0, 1)
        place(y, amp * rng.uniform(0.3, 1.0) * d, ns(rng.uniform(t_from, t_to)))
    return y


def k_footstep_wet(rng, p):
    vel = _num(p, ("vel", "intensity"), 0.7)
    n = ns(0.5)
    t = tvec(n)
    y = 0.6 * k_footstep(rng, dict(p, surface="stone"))[:n]
    y = np.pad(y, (0, n - len(y)))
    slap = bp(white(rng, n), 450, 3200) * np.exp(-t / rng.uniform(0.010, 0.02)) * 0.6
    squish = bp(white(rng, n) * env_ar(n, 0.012, 0.05), 300, 1600) * smooth_rand(rng, n, 60, 0.3, 1.0) * 0.35
    y = y + slap * vel + squish + _droplets(rng, n, rng.integers(3, 8), 0.02, 0.22, amp=0.22)
    return fade(peak_norm(y), 0.0005, 0.03)


def k_splash(rng, p):
    vel = _num(p, ("vel", "intensity"), 0.8)
    n = ns(1.0)
    t = tvec(n)
    body = bp(white(rng, n), 300, 5200) * env_ar(n, 0.004, rng.uniform(0.07, 0.12))
    low = lp(white(rng, n) * env_ar(n, 0.003, 0.04), 400) * 0.8
    y = (body + low) * vel + _droplets(rng, n, rng.integers(18, 34), 0.06, 0.7, 900, 3800, 0.3)
    y += 0.5 * _impact(rng, n, 70, 0.03, vel)
    return fade(peak_norm(y), 0.0005, 0.05)


def _creak(rng, dur, rate0, rate_dev, body, body_dur=0.12, noise_amt=0.06, bright=1.0):
    """Stick-slip friction: an irregular pulse train (rate drifts = the creak's 'pitch') through body modes."""
    n = ns(dur)
    rate = rate0 * (1 + rate_dev * (smooth_rand(rng, n, 3.0, -1, 1) + 0.4 * smooth_rand(rng, n, 11.0, -1, 1)))
    rate = np.maximum(rate, 8.0)
    ph = np.cumsum(rate / SR)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    idx = np.clip(idx + rng.integers(-ns(0.0006), ns(0.0006) + 1, len(idx)), 0, n - 1)
    amp_env = hump(n, rng.uniform(0.25, 0.6), 0.8) * smooth_rand(rng, n, 9.0, 0.35, 1.0)
    pulses = np.zeros(n)
    np.add.at(pulses, idx, amp_env[idx] * np.exp(0.35 * rng.standard_normal(len(idx))))
    pulses = lp(pulses, 5000 * bright)
    y = excite(pulses, modes(rng, body, ns(body_dur)))[:n]
    y += noise_amt * bp(white(rng, n) * amp_env, 800, 5000)
    return y


CREAK_BODY = [(287, 0.008, 0.6), (553, 0.006, 1.0), (861, 0.005, 0.8), (1230, 0.004, 0.6), (1790, 0.003, 0.45),
              (2510, 0.0025, 0.3), (3420, 0.002, 0.15)]


def k_creak_wood(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.5, 0.9)), 0.15, 3.0))
    mat = _str(p, ("material", "what"), "wood")
    if mat in ("door", "hinge", "gate"):
        y = _creak(rng, dur, rng.uniform(140, 260), 0.45, CREAK_BODY + IRON[:3], 0.15, 0.05, 1.2)
    elif mat in ("book", "spine", "leather"):
        y = _creak(rng, dur, rng.uniform(60, 110), 0.35, [(f * 0.7, tau * 0.6, a) for f, tau, a in CREAK_BODY], 0.08,
                   0.12, 0.7)
    elif mat in ("stool", "chair", "floor", "boards"):
        y = _creak(rng, dur, rng.uniform(70, 140), 0.4, [(f * 0.8, tau, a) for f, tau, a in CREAK_BODY], 0.12)
    else:
        y = _creak(rng, dur, rng.uniform(90, 170), 0.4, CREAK_BODY, 0.12)
    return fade(peak_norm(y), 0.01, 0.04)


def k_bench_creak(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.7, 1.1)), 0.3, 3.0))
    weight = float(np.clip(_num(p, ("weight",), 0.6), 0, 1))
    n = ns(dur + 0.2)
    y = np.zeros(n)
    settle = excite(burst(rng, ns(0.006), 0.002, hi=1500), modes(rng, WOOD_FLOOR, ns(0.3)))
    place(y, 0.5 * (0.5 + weight) * settle, 0)
    cr = _creak(rng, dur, rng.uniform(45, 85) * (1.2 - 0.4 * weight), 0.35,
                [(f * 0.75, tau * 1.2, a) for f, tau, a in CREAK_BODY], 0.14, 0.04)
    place(y, cr, ns(0.03))
    groan = _creak(rng, dur * 0.8, rng.uniform(30, 50), 0.2, [(f, tau * 0.3, a) for f, tau, a in IRON], 0.1, 0.0,
                   0.6)                                                  # iron frame groan
    place(y, 0.2 * groan, ns(0.08))
    return fade(peak_norm(y), 0.002, 0.05)


def k_bench_scrape(rng, p):
    """A bench dragged over gravel: heaving pulls, gravel crunch stream, wooden/iron legs resonating."""
    dur = float(np.clip(_num(p, ("dur", "duration"), 2.5), 0.4, 6.0))
    n = ns(dur + 0.3)
    t = tvec(n)
    pulls = rng.integers(3, 5) if dur > 1.2 else 1
    env = np.zeros(n)
    edges = np.sort(rng.uniform(0, 1, pulls - 1)) if pulls > 1 else np.array([])
    bounds = np.concatenate([[0], edges, [1]]) * dur
    for a, b in zip(bounds[:-1], bounds[1:]):
        i0, i1 = ns(a + 0.03), ns(max(a + 0.15, b - 0.08))
        if i1 > i0:
            env[i0:i1] = np.maximum(env[i0:i1], hump(i1 - i0, 0.3, 0.9) * rng.uniform(0.7, 1.0))
    gr = bp(grains(rng, n, 900, env=env), 1200, 9000)
    legs = excite(grains(rng, n, 140, env=env) * 0.6, modes(rng, [(f * 0.9, tau * 0.5, a) for f, tau, a in WOOD_FLOOR]
                                                           + [(f, tau * 0.15, a * 0.3) for f, tau, a in IRON[:2]],
                                                           ns(0.12)))[:n]
    rumble = lp(white(rng, n) * env, 220) * 0.6
    y = 0.8 * gr + 0.18 * legs + rumble
    end = excite(burst(rng, ns(0.005), 0.002, hi=1200), modes(rng, WOOD_FLOOR, ns(0.3)))  # set down
    place(y, 0.6 * end, ns(dur) - 1)
    y *= 1.0 - 0.0 * t
    return fade(peak_norm(y), 0.01, 0.08)


def k_page_turn(rng, p):
    heavy = bool(p.get("heavy", False)) or _str(p, ("material",), "") in ("vellum", "parchment", "book")
    count = int(np.clip(_num(p, ("count", "n"), 1), 1, 8))
    lo, hi = (800, 6500) if heavy else (1500, 9500)
    out = np.zeros(ns(0.55 * count + 0.4))
    tcur = 0.0
    for k in range(count):
        d = rng.uniform(0.28, 0.42) * (1.2 if heavy else 1.0) * (0.75 if count > 2 else 1.0)
        m = ns(d)
        sw = bp(white(rng, m), lo, hi) * hump(m, rng.uniform(0.45, 0.7), 1.3)
        sw *= smooth_rand(rng, m, 35, 0.45, 1.0)                 # paper flexing
        flap = burst(rng, ns(0.03), 0.004, hi=6000) * 0.6
        thup = lp(burst(rng, ns(0.05), 0.012), 350) * (0.8 if heavy else 0.4)
        y = np.zeros(m + ns(0.06))
        y[:m] += sw
        place(y, flap + 0.0, m - ns(0.02))
        place(y, thup, m - ns(0.02))
        place(out, y * rng.uniform(0.7, 1.0), ns(tcur))
        tcur += d * rng.uniform(0.55, 0.8) if count > 1 else d
    return fade(peak_norm(out), 0.005, 0.04)


def k_book_open(rng, p):
    n = ns(1.6)
    y = np.zeros(n)
    spine = k_creak_wood(rng, dict(material="book", dur=rng.uniform(0.45, 0.6)))
    place(y, 0.55 * spine, 0)
    m = ns(0.35)
    whoosh = lp(white(rng, m), 1400) * hump(m, 0.6, 1.2)
    place(y, 0.35 * whoosh, ns(0.25))
    land = _impact(rng, ns(0.25), 95, 0.03, 0.6, 1500) + 0.4 * fit(excite(burst(rng, ns(0.004), 0.0015),
                                                                           modes(rng, WOOD_COUNTER, ns(0.2))), ns(0.25))
    place(y, 0.9 * land, ns(0.58))
    flutter = k_page_turn(rng, dict(heavy=True, count=rng.integers(3, 5)))
    place(y, 0.35 * flutter, ns(0.64))
    return fade(peak_norm(y), 0.004, 0.05)


def k_book_close(rng, p):
    n = ns(0.6)
    y = np.zeros(n)
    m = ns(0.12)
    place(y, 0.3 * lp(white(rng, m), 1200) * hump(m, 0.8), 0)
    thump = _impact(rng, ns(0.4), 105, 0.035, 0.8, 1600)
    body = excite(burst(rng, ns(0.004), 0.0015), modes(rng, WOOD_COUNTER, ns(0.25)))[:ns(0.4)]
    clap = burst(rng, ns(0.03), 0.003, 600, 5000) * 0.5
    place(y, thump + 0.35 * np.pad(body, (0, max(0, ns(0.4) - len(body))))[:ns(0.4)], ns(0.11))
    place(y, clap, ns(0.11))
    return fade(peak_norm(y), 0.004, 0.04)


def k_paper_slide(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.55, 0.85)), 0.2, 2.5))
    n = ns(dur + 0.1)
    env = hump(ns(dur), rng.uniform(0.35, 0.55), 1.0)
    env = np.pad(env, (0, n - len(env))) * smooth_rand(rng, n, 18, 0.55, 1.0)
    fr = bp(white(rng, n), 1100, 6500) * env
    counter = excite(grains(rng, n, 220, env=env) * 0.4, modes(rng, WOOD_COUNTER, ns(0.12)))[:n]
    tap = burst(rng, ns(0.02), 0.003, 800, 5000)
    y = fr + 0.12 * counter
    place(y, 0.5 * tap, 0)
    return fade(peak_norm(y), 0.004, 0.04)


def k_item_set_down(rng, p):
    mat = _str(p, ("material", "item", "what"), "wood")
    vel = _num(p, ("vel", "intensity"), 0.7)
    n = ns(0.9)
    y = np.zeros(n)
    exc = burst(rng, ns(0.004), 0.0012, hi=4000 + 3000 * vel)
    counter = excite(exc, modes(rng, WOOD_COUNTER, ns(0.3)))
    place(y, 0.7 * counter, 0)
    place(y, 0.5 * _impact(rng, ns(0.2), rng.uniform(95, 140), 0.02, vel), 0)
    if mat in ("glass", "potion", "bottle", "draught", "sleep", "sleep_draught"):
        place(y, 0.32 * excite(exc, modes(rng, GLASS_BOTTLE, ns(0.8))), 0)
        slosh = bp(white(rng, ns(0.25)), 300, 1400) * hump(ns(0.25), 0.3) * smooth_rand(rng, ns(0.25), 25, 0.2, 1)
        place(y, 0.12 * slosh, ns(0.02))
    elif mat in ("jar", "pills", "vitamins", "berries"):
        place(y, 0.32 * excite(exc, modes(rng, GLASS_JAR, ns(0.5))), 0)
        rat = np.zeros(ns(0.35))
        for _ in range(rng.integers(18, 34)):
            tk = excite(burst(rng, ns(0.001), 0.0003), modes(rng, [(rng.uniform(2500, 5500), 0.004, 1)], ns(0.012)))
            place(rat, tk * rng.uniform(0.2, 1.0) * math.exp(-rng.uniform(0, 3)), ns(rng.exponential(0.06)))
        place(y, 0.35 * rat, ns(0.008))
    elif mat in ("candle", "calm", "wax"):
        place(y, 0.22 * excite(exc, modes(rng, [(f * 0.6, tau * 0.4, a) for f, tau, a in GLASS_JAR], ns(0.3))), 0)
        place(y, 0.45 * _impact(rng, ns(0.2), 160, 0.015, vel), 0)
    elif mat in ("book", "coloring_book", "paper", "colouring_book"):
        slap = burst(rng, ns(0.03), 0.004, 300, 5000)
        air = lp(white(rng, ns(0.08)) * hump(ns(0.08), 0.2), 900) * 0.5
        y *= 0.55
        place(y, 0.9 * slap, 0)
        place(y, air, ns(0.004))
    elif mat in ("bag", "satchel", "sack"):
        y *= 0.5
        place(y, 0.6 * k_cloth_rustle(rng, dict(dur=0.35, weight=0.7)), 0)
    elif mat in ("stone", "rune", "rune_stone"):
        place(y, 0.25 * excite(exc, modes(rng, STONE, ns(0.06))), 0)
    return fade(peak_norm(y), 0.0005, 0.06)


def k_glass_clink(rng, p):
    mat = _str(p, ("material",), "glass")
    n = ns(1.4)
    y = np.zeros(n)
    hits = 2 if rng.uniform() < 0.7 else 1
    for h in range(hits):
        exc = burst(rng, ns(0.0015), 0.0003, hi=12000)
        if mat in ("pewter", "tankard", "tankards", "metal"):
            spec = PEWTER
            clunk = 0.4 * _impact(rng, ns(0.12), 300, 0.01, 0.6, 3000)
        elif mat in ("crystal",):
            spec = [(f * 1.6, tau * 2.0, a) for f, tau, a in GLASS_BOTTLE]
            clunk = 0.0
        else:
            spec = [(f * rng.uniform(1.0, 1.5), tau * 1.6, a) for f, tau, a in GLASS_BOTTLE]
            clunk = 0.0
        z = excite(exc, modes(rng, spec, ns(1.2)))
        if not np.isscalar(clunk):
            z[:len(clunk)] += clunk
        place(y, z * (1.0 if h == 0 else rng.uniform(0.5, 0.8)), ns(h * rng.uniform(0.006, 0.02)))
    return fade(peak_norm(y), 0.0003, 0.08)


def k_till_bell(rng, p):
    """Brass till: 'ka-' (lever + ratchet clicks) '-ching' (bright desk bell) + the drawer rolling out."""
    n = ns(2.4)
    y = np.zeros(n)
    for k in range(rng.integers(3, 5)):
        tk = excite(burst(rng, ns(0.002), 0.0005, hi=9000), modes(rng, IRON[2:] + [(4200, 0.006, 0.5)], ns(0.05)))
        place(y, 0.45 * tk * rng.uniform(0.6, 1.0), ns(0.028 * k + rng.uniform(0, 0.006)))
    t_bell = 0.11 + rng.uniform(0, 0.02)
    bell = excite(burst(rng, ns(0.0012), 0.0003, hi=14000), modes(rng, BRASS_BELL, ns(2.0), jitter=0.01))
    place(y, 0.9 * bell, ns(t_bell))
    m = ns(0.28)
    roll = lp(white(rng, m), 900) * hump(m, 0.5) * smooth_rand(rng, m, 40, 0.5, 1)
    place(y, 0.25 * roll, ns(t_bell + 0.06))
    stop = _impact(rng, ns(0.2), 140, 0.02, 0.8, 2500) + 0.5 * fit(excite(burst(rng, ns(0.004), 0.001),
                                                                           modes(rng, WOOD_COUNTER, ns(0.2))), ns(0.2))
    place(y, 0.55 * stop, ns(t_bell + 0.36))
    return fade(peak_norm(y), 0.0005, 0.1)


def k_receipt(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.7, 1.0)), 0.3, 2.0))
    n = ns(dur + 0.4)
    rate = rng.uniform(28, 38)
    m = ns(dur)
    ph = np.cumsum(np.full(m, rate) * (1 + 0.05 * smooth_rand(rng, m, 4, -1, 1)) / SR)
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    clicks = np.zeros(n)
    np.add.at(clicks, idx, rng.uniform(0.5, 1.0, len(idx)))
    clicks = excite(clicks, modes(rng, [(2600, 0.003, 1), (4300, 0.002, 0.6), (1450, 0.004, 0.4)], ns(0.02)))[:n]
    fr = bp(white(rng, n), 2000, 8500) * np.pad(hump(m, 0.5, 0.7), (0, n - m)) * 0.25
    y = 0.6 * clicks + fr
    place(y, 0.5 * k_page_turn(rng, {}), m - ns(0.05))
    return fade(peak_norm(y), 0.003, 0.05)


def k_stamp_thunk(rng, p):
    """The troll's wooden stamp on the back of a scaly hand: heavy, dull, a little wet."""
    vel = _num(p, ("vel", "intensity"), 0.9)
    n = ns(0.5)
    t = tvec(n)
    y = 1.1 * _impact(rng, n, rng.uniform(92, 118), 0.045, vel, 1400)
    knock = excite(burst(rng, ns(0.003), 0.001), modes(rng, [(430, 0.016, 1), (690, 0.012, 0.7), (980, 0.008, 0.4)],
                                                        ns(0.12)))
    place(y, 0.45 * knock, 0)
    sq = bp(white(rng, ns(0.06)), 700, 2600) * hump(ns(0.06), 0.15) * 0.25
    place(y, sq, ns(0.006))
    tick = excite(burst(rng, ns(0.001), 0.0003), modes(rng, [(3600, 0.003, 1)], ns(0.01)))
    place(y, 0.08 * tick, 0)
    y = lp(y, 5000) * (1 - 0.0 * t)
    return fade(peak_norm(y), 0.0003, 0.05)


def k_door_open(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.8, 1.2)), 0.3, 3.0))
    n = ns(dur + 0.5)
    y = np.zeros(n)
    for k in range(2):                                   # iron latch lifts: click-clack + rattle
        tk = excite(burst(rng, ns(0.002), 0.0005, hi=8000), modes(rng, IRON, ns(0.15)))
        place(y, 0.6 * tk * (1.0 if k == 0 else 0.7), ns(0.04 * k))
    cr = k_creak_wood(rng, dict(material="door", dur=dur))
    place(y, 0.55 * cr, ns(0.12))
    m = ns(dur)
    place(y, 0.25 * lp(white(rng, m), 700) * hump(m, 0.4), ns(0.15))
    return fade(peak_norm(y), 0.0005, 0.08)


def k_door_close(rng, p):
    vel = _num(p, ("vel", "intensity"), 0.85)
    n = ns(1.0)
    y = np.zeros(n)
    m = ns(0.18)
    place(y, 0.35 * lp(white(rng, m), 600) * hump(m, 0.8), 0)
    t0 = ns(0.16)
    slab = 1.2 * _impact(rng, ns(0.6), rng.uniform(62, 78), 0.075, vel, 1000)
    body = excite(burst(rng, ns(0.006), 0.002, hi=2000), modes(rng, [(f * 0.55, tau * 1.8, a) for f, tau, a in WOOD_FLOOR],
                                                                ns(0.45)))[:ns(0.6)]
    place(y, slab + 0.5 * np.pad(body, (0, max(0, ns(0.6) - len(body))))[:ns(0.6)], t0)
    latch = excite(burst(rng, ns(0.002), 0.0005, hi=9000), modes(rng, IRON, ns(0.2)))
    place(y, 0.45 * latch, t0 + ns(rng.uniform(0.03, 0.05)))
    rattle = excite(grains(rng, ns(0.12), 120) * 0.5, modes(rng, IRON[1:], ns(0.08)))
    place(y, 0.2 * rattle, t0 + ns(0.06))
    return fade(peak_norm(y), 0.002, 0.08)


def k_cloth_rustle(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.45, 0.8)), 0.15, 3.0))
    weight = float(np.clip(_num(p, ("weight",), 0.5), 0, 1))
    n = ns(dur)
    moves = rng.integers(2, 5)
    env = np.zeros(n)
    for _ in range(moves):
        c = rng.uniform(0.1, 0.9)
        w = rng.uniform(0.12, 0.35)
        x = (np.linspace(0, 1, n) - c) / w
        env += rng.uniform(0.4, 1.0) * np.exp(-x * x * 4)
    env = env / (env.max() + 1e-9) * hump(n, 0.3, 0.3)
    lo, hi = (350, 3800) if weight > 0.6 else (700, 7000)
    y = bp(white(rng, n), lo, hi) * env * smooth_rand(rng, n, 50, 0.5, 1.0)
    y += 0.4 * bp(grains(rng, n, 300, env=env), 2500, 9000)    # crisp fibre crackle
    return fade(peak_norm(y), 0.01, 0.03)


def _pixie_buzz(rng, p):
    """A pixie's wings: an insect-quick buzz (wingbeat ~70 Hz) that flits and fades as she darts off."""
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.7, 1.1)), 0.2, 3.0))
    n = ns(dur)
    t = tvec(n)
    fb = rng.uniform(62, 82) * (1 + 0.08 * smooth_rand(rng, n, 6, -1, 1)) * (1 - 0.12 * t / dur)
    ph = 2 * np.pi * np.cumsum(fb) / SR
    tone = sum(np.sin(k * ph + k) / k ** 0.8 for k in range(1, 9))
    hiss = bp(white(rng, n), 1500, 7000) * (0.5 + 0.5 * np.sin(ph)) ** 2
    y = (0.6 * tone + 0.5 * hiss) * hump(n, 0.15, 0.8) * smooth_rand(rng, n, 5, 0.5, 1.0)
    return fade(peak_norm(lp(y, 8000)), 0.01, 0.06)


def k_wing_flutter(rng, p):
    if p.get("_scene") == 5 and not p.get("who") or "pixie" in _str(p, ("who", "size"), ""):
        return _pixie_buzz(rng, p)
    size = _str(p, ("size", "who"), "dragon")
    count = int(np.clip(_num(p, ("count", "n", "beats"), rng.integers(2, 4)), 1, 12))
    leathery = any(k in size for k in ("dragon", "cockatrice", "bard", "pixie", "leather", "big"))
    period = rng.uniform(0.28, 0.4) if leathery else rng.uniform(0.09, 0.13)
    n = ns(period * count + 0.5)
    y = np.zeros(n)
    for k in range(count):
        m = ns(period * 1.1)
        air = lp(white(rng, m), 650 if leathery else 1500) * env_ar(m, period * 0.25, period * 0.3)
        snap = bp(white(rng, m), 300, 2200 if leathery else 6000) * env_ar(m, 0.004, 0.025)
        b = air + (0.5 if leathery else 0.3) * snap
        if not leathery:
            b += 0.4 * bp(white(rng, m), 2000, 8000) * env_ar(m, 0.01, 0.04)
        place(y, b * rng.uniform(0.75, 1.0) * (0.85 ** k), ns(k * period * rng.uniform(0.95, 1.05)))
    return fade(peak_norm(y), 0.005, 0.05)


def k_pigeon_flap(rng, p):
    count = int(np.clip(_num(p, ("count", "n", "birds"), rng.integers(1, 4)), 1, 10))
    land = _str(p, ("dir", "action"), "off") in ("land", "landing", "in", "down")
    n = ns(1.6)
    y = np.zeros(n)
    for b in range(count):
        rate = rng.uniform(8.5, 11.5)
        dur = rng.uniform(0.45, 0.9)
        t0 = rng.uniform(0, 0.35) * (b > 0)
        kk = int(dur * rate)
        for k in range(kk):
            g = (k + 1) / kk if land else 1 - k / kk * 0.7
            clap = burst(rng, ns(0.06), rng.uniform(0.004, 0.008), 600, 6500)
            whirr = bp(white(rng, ns(0.06)), 1200, 4500) * hump(ns(0.06), 0.4) * 0.3
            place(y, (clap + whirr) * g * rng.uniform(0.6, 1.0), ns(t0 + k / rate + rng.uniform(-0.004, 0.004)))
    return fade(peak_norm(y), 0.002, 0.06)


def pigeon_coo_wave(rng, f0=None):
    """'oo -- rrr-oo -- oo': low nearly-pure tone with a rolling throat tremolo in the middle."""
    f0 = f0 or rng.uniform(330, 470)
    parts = [(rng.uniform(0.10, 0.16), 1.0, 0.0, 1.06, 0.97),       # (dur, amp, roll depth, pitch from, to)
             (rng.uniform(0.04, 0.07), 0.0, 0.0, 1.0, 1.0),
             (rng.uniform(0.38, 0.55), 1.0, 0.7, 1.07, 0.90),
             (rng.uniform(0.02, 0.05), 0.0, 0.0, 1.0, 1.0),
             (rng.uniform(0.10, 0.18), 0.7, 0.0, 0.95, 0.88)]
    if rng.uniform() < 0.35:
        parts = parts[:3]
    total = sum(d for d, *_ in parts) + 0.1
    n = ns(total)
    f = np.full(n, f0)
    a = np.zeros(n)
    i = 0
    roll_rate = rng.uniform(26, 36)
    for d, amp, roll, p0, p1 in parts:
        m = ns(d)
        if amp > 0:
            seg_t = tvec(m)
            f[i:i + m] = f0 * np.linspace(p0, p1, m)
            e = hump(m, 0.3, 0.7) * amp
            if roll > 0:
                e *= 1 - roll * (0.5 + 0.5 * np.sin(2 * np.pi * roll_rate * seg_t))
            a[i:i + m] = e
        i += m
    a = lp(a, 120)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.25 * np.sin(2 * ph + 0.4) + 0.08 * np.sin(3 * ph + 1.1)) * a
    y += 0.05 * bp(white(rng, n), 400, 1800) * a
    return lp(y, 1600)


def k_pigeon_coo(rng, p):
    count = int(np.clip(_num(p, ("count", "n"), 1), 1, 6))
    out = np.zeros(ns(1.2 * count + 0.3))
    t = 0.0
    for _ in range(count):
        c = pigeon_coo_wave(rng)
        place(out, c * rng.uniform(0.7, 1.0), ns(t))
        t += len(c) / SR + rng.uniform(0.15, 0.5)
    return fade(peak_norm(out), 0.004, 0.05)


def k_bread_tear(rng, p):
    """Crusty loaf torn: dense crust crackle, then the soft fibrous tear of the crumb, a few crumbs."""
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.6, 0.9)), 0.3, 2.0))
    n = ns(dur + 0.3)
    y = np.zeros(n)
    m = ns(rng.uniform(0.18, 0.32))
    env = env_ar(m, 0.01, m / SR * 0.45)
    cr = grains(rng, m, rng.uniform(900, 1500), env=env / (env.max() + 1e-9))
    cr = excite(cr, modes(rng, [(3200, 0.003, 1), (5100, 0.002, 0.7), (2100, 0.004, 0.5), (7400, 0.0015, 0.4)],
                          ns(0.012)))[:m]
    place(y, cr, 0)
    k = ns(dur * 0.8)
    tear = lp(white(rng, k), 2600) * hump(k, 0.35, 0.9) * smooth_rand(rng, k, 60, 0.2, 1.0) ** 2
    place(y, 0.5 * tear, ns(0.05))
    place(y, 0.3 * k_crumbs(rng, dict(count=8)), ns(dur * 0.6))
    return fade(peak_norm(y), 0.001, 0.05)


def k_crumbs(rng, p):
    count = int(np.clip(_num(p, ("count", "n"), rng.integers(12, 26)), 2, 80))
    spread = _num(p, ("dur", "duration", "spread"), rng.uniform(0.35, 0.7))
    n = ns(spread + 0.15)
    y = np.zeros(n)
    for _ in range(count):
        tk = excite(burst(rng, ns(0.0008), 0.0002), modes(rng, [(rng.uniform(2500, 7000), 0.002, 1),
                                                                 (rng.uniform(1200, 2500), 0.003, 0.4)], ns(0.008)))
        place(y, tk * rng.uniform(0.2, 1.0), ns(spread * rng.beta(1.3, 2.2)))
    return fade(peak_norm(y), 0.0005, 0.02)


def k_ember_crackle(rng, p):
    """The dragon's warm puff of golden embers: a soft 'fwoomp', then dwindling pops, sparkle hiss."""
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(1.0, 1.4)), 0.3, 4.0))
    n = ns(dur + 0.3)
    t = tvec(n)
    y = np.zeros(n)
    m = ns(0.32)
    place(y, 0.6 * lp(white(rng, m), 900) * hump(m, 0.3, 1.0), 0)
    env = np.exp(-t / (dur * 0.4))
    pops = grains(rng, n, rng.uniform(26, 40), env=env)
    pops = excite(pops, modes(rng, [(1900, 0.004, 1), (3100, 0.003, 0.8), (4700, 0.002, 0.5), (1200, 0.006, 0.3)],
                              ns(0.02)))[:n]
    y += 0.9 * pops
    y += 0.07 * hp(white(rng, n), 4500) * env * smooth_rand(rng, n, 12, 0.3, 1)
    for _ in range(rng.integers(1, 3)):
        snap = excite(burst(rng, ns(0.001), 0.0003), modes(rng, [(2400, 0.006, 1), (3900, 0.004, 0.6)], ns(0.03)))
        place(y, 0.8 * snap, ns(rng.uniform(0.05, dur * 0.6)))
    return fade(peak_norm(y), 0.004, 0.08)


def k_smoke_puff(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.6, 0.9)), 0.2, 3.0))
    n = ns(dur)
    y = bp(white(rng, n), 350, 2600) * env_ar(n, 0.08, dur * 0.35)
    y = peq(y, 950, 6, 1.5)
    y += 0.35 * lp(white(rng, n), 150) * env_ar(n, 0.05, dur * 0.3)
    return fade(peak_norm(y), 0.01, 0.06)


def _formant_noise(rng, n, formants, src):
    y = np.zeros(n)
    for f, q, a in formants:
        y += a * reson(src, f, q)
    return y


def k_sigh(rng, p):
    """A weary dragon's sigh: a small inhale, then a long breathy 'haaah' with a little voicing at the top."""
    scale = 0.82 if "dragon" in _str(p, ("who",), "dragon") else 1.0
    n = ns(1.5)
    y = np.zeros(n)
    m = ns(0.3)
    inh = bp(white(rng, m), 1400, 5200) * hump(m, 0.7, 1.2) * 0.25
    place(y, inh, 0)
    ex_t = 0.38
    m = ns(1.05)
    tt = tvec(m)
    env = env_ar(m, 0.07, 0.42)
    asp = white(rng, m) * env
    fm = [(680 * scale, 4.5, 1.0), (1150 * scale, 6.0, 0.55), (2450 * scale, 8.0, 0.25), (3400 * scale, 9, 0.1)]
    breath = _formant_noise(rng, m, fm, asp)
    f0 = (108 - 30 * np.clip(tt / 0.6, 0, 1)) * scale
    ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.01 * smooth_rand(rng, m, 20, -1, 1))) / SR
    voc = sum(np.sin(k * ph) / (k * k) for k in range(1, 14)) * env * np.exp(-tt / 0.25)
    voiced = _formant_noise(rng, m, fm, voc) * 0.8
    chest = np.sin(2 * np.pi * 62 * tt) * env * np.exp(-tt / 0.3) * 0.05
    place(y, breath + voiced + chest, ns(ex_t))
    return fade(peak_norm(lp(y, 6000)), 0.01, 0.08)


def k_tap_wood(rng, p):
    count = int(np.clip(_num(p, ("count", "n", "taps"), 2), 1, 10))
    gap = _num(p, ("interval", "gap"), rng.uniform(0.2, 0.26))
    n = ns(gap * count + 0.25)
    y = np.zeros(n)
    for k in range(count):
        exc = burst(rng, ns(0.0015), 0.0004, hi=6000)
        tok = excite(exc, modes(rng, WOOD_PLAQUE, ns(0.12))) + 0.4 * excite(exc, modes(rng, WOOD_FLOOR[:3],
                                                                                         ns(0.12)))
        place(y, tok * (1.0 if k == 0 else rng.uniform(0.8, 0.95)), ns(k * gap * rng.uniform(0.95, 1.05)))
    return fade(peak_norm(y), 0.0003, 0.03)


def k_lute_pluck(rng, p):
    midi = p.get("midi", p.get("pitch", p.get("note", 62)))
    notes = midi if isinstance(midi, (list, tuple)) else [midi]
    vel = _num(p, ("vel", "intensity"), 0.5)
    n = ns(2.6)
    y = np.zeros(n)
    for i, m in enumerate(notes):
        try:
            m = int(m)
        except (TypeError, ValueError):
            m = 62
        s = SONG.ks_string(float(SONG.midi_hz(m)), 2.4, t60=2.0, damp=0.18, pick=0.17, vel=vel, soft=0.6, rng=rng)
        place(y, s, ns(0.02 * i))
    y = fftconvolve(y, SONG.lute_body_ir())[:n]
    return fade(peak_norm(hp(y, 70)), 0.0005, 0.2)


def k_laugh_crowd_burst(rng, p):
    """In the tavern (S4): the uncanny laugh -- a dozen voices laughing in PERFECT sync at the same level.
    Anywhere else (S5's ring of onlookers): a natural crowd reaction burst ('Ooh!', 'Ha!', 'Huzzah!'),
    many voices, loosely together, as each shove lands."""
    w = _WALLA_FOR_CUES
    nvo = int(np.clip(_num(p, ("count", "n", "voices"), 12), 3, 24))
    scene = p.get("_scene", 4)
    try:
        if scene == 4 or p.get("sync"):
            dur_p, bpm_p = _num(p, ("dur", "duration"), 0.0), _num(p, ("bpm", "rate"), 0.0)
            if dur_p > 0.3 and bpm_p > 30.0:        # the module's laugh clock: n HAs exactly on its beat
                n_ha = int(np.clip(round(dur_p * bpm_p / 60.0), 1, 16))
                y = w.sync_laugh_grid(n_ha, bpm_p, variant=int(rng.integers(0, 3)), voices=nvo)
            else:
                y = w.sync_laugh(variant=int(rng.integers(0, 3)), voices=nvo)
        else:
            pool = w.pool(["Ooh!", "Ha!", "Huzzah!", "Oh!", "Whoa!", "Hey!", "Ha ha!", "Get him!"], 16, seed=909)
            n = ns(1.6)
            y = np.zeros(n)
            for _ in range(nvo):
                u = varispeed(pool[rng.integers(len(pool))], rng.uniform(0.98, 1.15))
                u = softclip(peq(u, 2600, 3.0, 0.9) * 1.6, 1.4)
                place(y, u * rng.uniform(0.4, 1.0), ns(abs(rng.normal(0.05, 0.06))))
            y = peak_norm(lp(y, 7000))
    except Exception as e:  # pragma: no cover - TTS unavailable: procedural fallback
        warn(f"crowd walla unavailable ({e}); procedural laugh")
        y = _proc_laugh(rng, nvo)
    return y


def _proc_laugh(rng, voices):
    n = ns(1.5)
    y = np.zeros(n)
    for v in range(voices):
        f0 = rng.uniform(110, 230)
        for k in range(5):
            m = ns(0.12)
            tt = tvec(m)
            ph = 2 * np.pi * f0 * (1 - 0.05 * k) * tt
            src = sum(np.sin(j * ph) / j for j in range(1, 18)) * hump(m, 0.25)
            src += 0.4 * white(rng, m) * hump(m, 0.1)
            z = _formant_noise(rng, m, [(750, 5, 1.0), (1250, 6, 0.6), (2600, 8, 0.3)], src)
            place(y, z, ns(0.05 + 0.21 * k))
    return peak_norm(y)


def k_crystal_chime(rng, p):
    dirn = _str(p, ("dir", "direction"), "")
    midi = _num(p, ("midi", "pitch"), rng.choice([88, 90, 93, 95]))
    f0 = float(SONG.midi_hz(midi))
    n = ns(2.0)
    t = tvec(n)
    y = np.zeros(n)
    glide = np.ones(n)
    if dirn in ("down", "lower", "lowered"):
        glide = 2 ** (-1.5 * np.clip(t / 0.9, 0, 1) / 12)
    elif dirn in ("up", "raise", "raised"):
        glide = 2 ** (1.5 * np.clip(t / 0.9, 0, 1) / 12)
    for r, tau, a in ((1.0, 1.1, 1.0), (2.32, 0.6, 0.45), (3.81, 0.35, 0.25), (5.1, 0.2, 0.15)):
        for det in (0.0, rng.uniform(1.2, 2.8)):
            f = f0 * r + det
            if f * 1.1 > 0.45 * SR:
                continue
            ph = 2 * np.pi * np.cumsum(f * glide) / SR + rng.uniform(0, 6.28)
            y += a * 0.5 * np.sin(ph) * np.exp(-t / tau) * np.clip(t / 0.012, 0, 1)
    y += 0.15 * hp(burst(rng, n, 0.01), 6000)
    return fade(peak_norm(y), 0.002, 0.15)


def k_rune_glow(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.8, 1.2)), 0.2, 4.0))
    midi = _num(p, ("midi", "pitch"), 81)
    n = ns(dur + 0.6)
    t = tvec(n)
    env = np.clip(t / (dur * 0.45), 0, 1) ** 1.5 * np.exp(-np.maximum(t - dur * 0.55, 0) / 0.35)
    rise = 2 ** (2.0 * np.clip(t / dur, 0, 1) / 12)
    y = np.zeros(n)
    for k, iv in enumerate((0, 7, 12, 16, 19, 24)):
        f = float(SONG.midi_hz(midi + iv - 12)) * rise * (1 + 0.003 * np.sin(2 * np.pi * (4.5 + k) * t))
        trem = 0.75 + 0.25 * np.sin(2 * np.pi * (6.0 + 0.7 * k) * t + k)
        y += np.sin(2 * np.pi * np.cumsum(f) / SR + k) * trem / (1 + 0.4 * k)
    y = y * env + 0.25 * bp(white(rng, n), 2200, 7000) * env
    return fade(peak_norm(y), 0.01, 0.1)


def k_thud_shove(rng, p):
    vel = _num(p, ("vel", "intensity"), 0.85)
    n = ns(0.7)
    y = 1.0 * _impact(rng, n, rng.uniform(58, 80), 0.06, vel, 900)
    slap = bp(white(rng, ns(0.05)), 500, 4200) * np.exp(-tvec(ns(0.05)) / 0.012)
    place(y, 0.55 * slap, 0)
    m = ns(0.18)
    grunt = bp(white(rng, m), 300, 1500) * hump(m, 0.25) * 0.35
    place(y, grunt, ns(0.02))
    scuff = k_footstep(rng, dict(surface="stone", weight=0.9))
    place(y, 0.35 * scuff, ns(rng.uniform(0.08, 0.16)))
    leather = _creak(rng, 0.18, 120, 0.3, CREAK_BODY, 0.06, 0.1)
    place(y, 0.25 * leather, ns(0.03))
    return fade(peak_norm(y), 0.0005, 0.06)


def k_hug_rustle(rng, p):
    n = ns(1.6)
    y = np.zeros(n)
    place(y, k_cloth_rustle(rng, dict(dur=1.1, weight=0.8)), 0)
    for k, tp in enumerate((rng.uniform(0.45, 0.55), rng.uniform(0.75, 0.9))):
        pat = lp(_impact(rng, ns(0.2), rng.uniform(110, 150), 0.025, 0.5, 900), 600)
        place(y, 0.5 * pat * (1 if k == 0 else 0.8), ns(tp))
    leather = _creak(rng, 0.25, 90, 0.3, CREAK_BODY, 0.06, 0.1)
    place(y, 0.15 * leather, ns(0.2))
    return fade(peak_norm(y), 0.01, 0.06)


def k_hourglass_flip(rng, p):
    n = ns(1.6)
    y = np.zeros(n)
    m = ns(0.18)
    place(y, 0.3 * lp(white(rng, m), 1500) * hump(m, 0.6), 0)
    exc = burst(rng, ns(0.002), 0.0005, hi=7000)
    clunk = fit(excite(exc, modes(rng, WOOD_PLAQUE[:4], ns(0.1))), ns(0.3)) + \
        0.5 * fit(excite(exc, modes(rng, GLASS_JAR, ns(0.3))), ns(0.3))
    place(y, 0.7 * clunk, ns(0.16))
    k = ns(1.2)
    env = np.exp(-tvec(k) / 0.6) * np.clip(tvec(k) / 0.05, 0, 1)
    sand = bp(grains(rng, k, 2500, env=env), 3000, 11000) * 0.35
    place(y, sand, ns(0.2))
    return fade(peak_norm(y), 0.004, 0.08)


def k_drum_spin_thunk(rng, p):
    vel = _num(p, ("vel", "intensity"), 0.6)
    n = ns(0.6)
    y = 0.9 * lp(_impact(rng, n, rng.uniform(70, 95), 0.06, vel, 600), 900)
    shell = excite(burst(rng, ns(0.005), 0.0015, hi=1500),
                   modes(rng, [(156, 0.05, 1), (287, 0.04, 0.7), (433, 0.03, 0.5)], ns(0.25)))
    place(y, 0.45 * shell, 0)
    m = ns(0.14)
    place(y, 0.3 * lp(white(rng, m), 700) * hump(m, 0.2), 0)
    if rng.uniform() < 0.7:
        rat = excite(grains(rng, ns(0.06), 200), modes(rng, [(2600, 0.008, 1), (3900, 0.006, 0.6)], ns(0.03)))
        place(y, 0.12 * rat, ns(0.01))
    return fade(peak_norm(y), 0.002, 0.06)


def k_candle_flicker(rng, p):
    dur = float(np.clip(_num(p, ("dur", "duration"), rng.uniform(0.5, 0.9)), 0.2, 3.0))
    n = ns(dur)
    fl = smooth_rand(rng, n, rng.uniform(9, 15), 0.0, 1.0) ** 2
    y = lp(white(rng, n), 520) * fl * hump(n, 0.3, 0.6)
    if rng.uniform() < 0.4:
        place(y, 0.15 * bp(burst(rng, ns(0.05), 0.012), 3000, 8000), ns(rng.uniform(0, dur * 0.7)))
    return fade(peak_norm(y), 0.01, 0.05)


# kind -> (function, calibrated peak level dBFS at dist 0, default pan spread)
KINDS = {
    "footstep": (k_footstep, -21.0), "footstep_wet": (k_footstep_wet, -21.0), "splash": (k_splash, -18.0),
    "creak_wood": (k_creak_wood, -24.0), "bench_creak": (k_bench_creak, -22.0), "bench_scrape": (k_bench_scrape, -17.0),
    "page_turn": (k_page_turn, -24.0), "book_open": (k_book_open, -16.0), "book_close": (k_book_close, -17.0),
    "paper_slide": (k_paper_slide, -22.0), "item_set_down": (k_item_set_down, -14.0), "glass_clink": (k_glass_clink, -22.0),
    "till_bell": (k_till_bell, -16.0), "receipt": (k_receipt, -24.0), "stamp_thunk": (k_stamp_thunk, -9.0),
    "door_open": (k_door_open, -17.0), "door_close": (k_door_close, -10.0), "cloth_rustle": (k_cloth_rustle, -28.0),
    "wing_flutter": (k_wing_flutter, -21.0), "pigeon_flap": (k_pigeon_flap, -20.0), "pigeon_coo": (k_pigeon_coo, -24.0),
    "bread_tear": (k_bread_tear, -19.0), "crumbs": (k_crumbs, -30.0), "ember_crackle": (k_ember_crackle, -24.0),
    "smoke_puff": (k_smoke_puff, -30.0), "sigh": (k_sigh, -21.0), "tap_wood": (k_tap_wood, -17.0),
    "lute_pluck": (k_lute_pluck, -20.0), "laugh_crowd_burst": (k_laugh_crowd_burst, -13.0),
    "crystal_chime": (k_crystal_chime, -26.0), "rune_glow": (k_rune_glow, -27.0), "thud_shove": (k_thud_shove, -12.0),
    "hug_rustle": (k_hug_rustle, -20.0), "hourglass_flip": (k_hourglass_flip, -27.0),
    "drum_spin_thunk": (k_drum_spin_thunk, -20.0), "candle_flicker": (k_candle_flicker, -36.0),
}

ALIASES = {
    "step": "footstep", "steps": "footstep", "foot": "footstep", "walk": "footstep", "footsteps": "footstep",
    "footstep_gravel": "footstep", "footstep_stone": "footstep", "footstep_wood": "footstep",
    "wet_step": "footstep_wet", "puddle": "splash", "water": "splash", "drip": "splash",
    "creak": "creak_wood", "wood_creak": "creak_wood", "stool_creak": "creak_wood", "floor_creak": "creak_wood",
    "sit": "bench_creak", "bench": "bench_creak", "bench_sit": "bench_creak", "scrape": "bench_scrape",
    "drag": "bench_scrape", "bench_drag": "bench_scrape", "page": "page_turn", "pages": "page_turn",
    "page_flip": "page_turn", "flip": "page_turn", "book": "book_open", "open_book": "book_open",
    "close_book": "book_close", "note_slide": "paper_slide", "slide": "paper_slide", "paper": "paper_slide",
    "set_down": "item_set_down", "put_down": "item_set_down", "item": "item_set_down", "thunk": "item_set_down",
    "place": "item_set_down", "clink": "glass_clink", "glass": "glass_clink", "tankard": "glass_clink",
    "cheers": "glass_clink", "bell": "till_bell", "ring": "till_bell", "register": "till_bell", "till": "till_bell",
    "ka_ching": "till_bell", "kaching": "till_bell", "paper_curl": "receipt", "stamp": "stamp_thunk",
    "door": "door_open", "door_slam": "door_close", "slam": "door_close", "rustle": "cloth_rustle",
    "cloth": "cloth_rustle", "coat": "cloth_rustle", "wings": "wing_flutter", "wing": "wing_flutter",
    "flutter": "wing_flutter", "wing_flap": "wing_flutter", "flap": "pigeon_flap", "pigeons": "pigeon_flap",
    "pigeon": "pigeon_coo", "coo": "pigeon_coo", "bread": "bread_tear", "tear": "bread_tear", "crumb": "crumbs",
    "toss_crumbs": "crumbs", "embers": "ember_crackle", "ember": "ember_crackle", "sparks": "ember_crackle",
    "fire": "ember_crackle", "crackle": "ember_crackle", "smoke": "smoke_puff", "puff": "smoke_puff",
    "breath": "sigh", "exhale": "sigh", "tap": "tap_wood", "knock": "tap_wood", "tap_plaque": "tap_wood",
    "pluck": "lute_pluck", "lute": "lute_pluck", "strum": "lute_pluck", "laugh": "laugh_crowd_burst",
    "crowd_laugh": "laugh_crowd_burst", "laughter": "laugh_crowd_burst", "chime": "crystal_chime",
    "crystal": "crystal_chime", "glow": "rune_glow", "rune": "rune_glow", "magic": "rune_glow",
    "shimmer": "rune_glow", "stone_glow": "rune_glow", "shove": "thud_shove", "thud": "thud_shove",
    "push": "thud_shove", "punch": "thud_shove", "hug": "hug_rustle", "embrace": "hug_rustle",
    "hourglass": "hourglass_flip", "drum": "drum_spin_thunk", "drum_thunk": "drum_spin_thunk",
    "tumble": "drum_spin_thunk", "candle": "candle_flicker", "flicker": "candle_flicker",
}


def resolve_kind(kind):
    """Known kind -> itself; else alias / nearest name (warns). Returns None if hopeless."""
    k = str(kind).strip().lower().replace("-", "_").replace(" ", "_")
    if k in KINDS:
        return k
    if k in ALIASES:
        warn(f"unknown SFX kind {kind!r} -> {ALIASES[k]!r}")
        return ALIASES[k]
    parts = [p for p in k.split("_") if p]
    for size in range(len(parts) - 1, 0, -1):          # longest word run first: bench_drag_gravel -> bench_drag
        for i in range(len(parts) - size + 1):
            sub = "_".join(parts[i:i + size])
            hit = sub if sub in KINDS else ALIASES.get(sub)
            if hit:
                warn(f"unknown SFX kind {kind!r} -> {hit!r}")
                return hit
    m = difflib.get_close_matches(k, list(KINDS) + list(ALIASES), n=1, cutoff=0.5)
    if m:
        r = ALIASES.get(m[0], m[0])
        warn(f"unknown SFX kind {kind!r} -> {r!r} (nearest)")
        return r
    warn(f"unknown SFX kind {kind!r}: no match, skipped")
    return None


def norm_params(params):
    if params is None:
        return {}
    if isinstance(params, dict):
        p = dict(params)
        sz = p.get("size")
        if isinstance(sz, (int, float)) and not isinstance(sz, bool):      # scene modules: size = 0..1 strength
            p.setdefault("vel", float(np.clip(0.35 + 0.65 * float(sz), 0.2, 1.0)))
            p.setdefault("weight", float(np.clip(float(sz), 0.0, 1.0)))
            p["size"] = "big" if sz >= 0.7 else "small"
        return p
    if isinstance(params, (int, float)):
        return {"gain_db": float(params)}
    if isinstance(params, str):
        return {"variant": params, "material": params, "surface": params}
    if isinstance(params, (list, tuple)):
        out = {}
        for it in params:
            if isinstance(it, dict):
                out.update(it)
        return out
    return {}


def cue_gain_db(p):
    g = _num(p, ("gain_db", "db", "gain"), 0.0)
    if "gain" in p and "gain_db" not in p and "db" not in p:
        try:                                           # a 'gain' of 0..2 is a linear factor, else dB
            v = float(p["gain"])
            if 0.0 < v <= 2.0:
                g = 20 * math.log10(v)
        except (TypeError, ValueError):
            pass
    for k in ("vol", "volume", "level", "amp"):
        if k in p:
            try:
                g += 20 * math.log10(max(float(p[k]), 1e-4))
            except (TypeError, ValueError):
                pass
    return g


def cue_pan(p, default=0.0):
    if "pan" in p:
        return float(np.clip(_num(p, ("pan",), default), -1, 1))
    if "x" in p:
        x = _num(p, ("x",), 960.0)
        if x > 2.0:                                    # pixels
            return float(np.clip((x - 960.0) / 960.0 * 0.8, -0.9, 0.9))
        return float(np.clip((x - 0.5) * 1.6, -0.9, 0.9))   # normalized 0..1
    return default


def render_cue(kind, params=None, seed=0, scene=None, gain_offset_db=0.0):
    """-> (stereo float64 (n,2) dry at calibrated level, wet-send amount 0..1). None if kind unknown.
    gain_offset_db is added to the cue's own gain (the mix uses it to calibrate scene modules' linear gains)."""
    k = resolve_kind(kind)
    if k is None:
        return None, 0.0
    p = norm_params(params)
    if scene is not None:
        p["_scene"] = scene
    rng = np.random.default_rng(int(seed))
    fn, lvl = KINDS[k]
    y = fn(rng, p)
    y = np.asarray(y, np.float64)
    if y.ndim == 2:
        y = y.mean(axis=1)
    # repeated cues never identical: +-2.5 % pitch/length and +-1 dB level from the seed
    vr = 1.0 + 0.025 * rng.uniform(-1, 1)
    if k not in ("lute_pluck", "laugh_crowd_burst", "till_bell", "crystal_chime", "rune_glow"):
        y = varispeed(y, vr)
    dist = float(np.clip(_num(p, ("dist", "distance"), 0.0), 0, 1))
    if dist > 0:
        y = lp(y, 16000 * (2500 / 16000) ** dist)
    g_db = lvl + cue_gain_db(p) + gain_offset_db + rng.uniform(-1.0, 1.0) - 12.0 * dist
    y = peak_norm(y) * 10 ** (g_db / 20)
    st = stereo(y, cue_pan(p, float(rng.uniform(-0.15, 0.15))))
    wet = 0.25 + 0.6 * dist
    return st, wet


# ================================================================================================
# WALLA: many Piper speakers, deterministic + cached
# ================================================================================================
# hand-picked from the casting scans (f0, HNR); never the cast voices (LibriTTS-R 448/510/515, VCTK 102)
LIBRI_MALE = [3, 50, 303, 318, 327, 339, 371, 437, 459, 460, 483, 514, 531, 543, 569, 627, 663, 700, 716, 730,
              740, 752, 804, 834, 838, 861, 882, 891]
LIBRI_FEMALE = [62, 83, 87, 99, 126, 142, 144, 169, 170, 192, 208, 239, 242, 319, 345, 372, 378, 487, 545, 560,
                614, 626, 702, 754, 759, 832, 864, 881]
VCTK_MALE = [9, 25, 28, 50, 57, 61, 64, 96, 97, 105]
VCTK_FEMALE = [0, 11, 18, 22, 30, 44, 68, 85, 89, 91]
LIBRI = "en_US-libritts_r-medium"
VCTK = "en_GB-vctk-medium"

CHEER = ["Have at him!", "Huzzah!", "Ooh!", "Fight! Fight!", "Get him!", "Hit him!", "Go on!", "Come on!",
         "Smite him!", "Again!", "Oi!", "Knock him down!", "Have at thee!", "Strike!", "Thrash him!", "Ha!",
         "Yes!", "Hey!", "Give him one!", "Go on, then!", "Mind the horns!", "Get stuck in!", "Huzzah! Huzzah!",
         "Ooh, right in the snout!", "Fight!"]
MURMUR_UNEASY = ["Hmm.", "Well...", "Um.", "Oh.", "What...", "Huh.", "How odd.", "Strange.", "Is he...",
                 "I don't...", "Right then.", "Erm.", "Hm.", "Odd.", "Well, I never."]
TAVERN = ["Another round for the table!", "And then he says to me, he says...", "You don't say!",
          "Pass the ale, would you?", "To the king!", "Well met, friend!", "Aye, that's the one!",
          "No, no, listen to this.", "My cousin's goat ate the whole cart!", "Barkeep! More mead!", "Cheers!",
          "Ha! Good one!", "Who's buying?", "I swear on my beard!", "Sing it again!", "One more song!",
          "Oh, stop it!", "That's what I told him!", "Another!", "Ha ha!", "Drink up, drink up!",
          "Where's my tankard?", "Ho there!"]
BENCH = ["Thank you kindly.", "Is this seat free?", "Lovely evening, isn't it.", "Oh, that's good bread.",
         "Where are you from, then?", "My mother baked like this.", "Here, have some more.", "Mind the crumbs.",
         "I've passed this bench a hundred times.", "Long day?", "Aye, a long day.", "Ha, that's true.",
         "Mm, still warm.", "What's your name?", "Sit, sit.", "The pigeons know you.", "Is it always this quiet?",
         "I'd like that.", "Tell me about it."]


class Walla:
    """Deterministic multi-speaker Piper utterances (48 kHz float32), cached on disk."""

    def __init__(self, cache_dir=WALLA_DIR, verbose=True):
        self.cache_dir = cache_dir
        self.verbose = verbose
        self._tp = {}
        os.makedirs(cache_dir, exist_ok=True)

    def _piper(self, model):
        tp = self._tp.get(model)
        if tp is None:
            if self.verbose:
                print(f"[walla] loading {model} ...", flush=True)
            tp = SONG.TimedPiper(model, 0)
            self._tp[model] = tp
        return tp

    def _key(self, *parts):
        return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:20]

    def say(self, model, sid, text, seed, ls=1.0, ns_=0.667, nw=0.8):
        key = self._key("say2", model, sid, text, seed, round(ls, 3), ns_, nw)
        path = os.path.join(self.cache_dir, key + ".npy")
        if not os.path.exists(path):
            tp = self._piper(model)
            tp.sid = int(sid)
            ids = tp.voice.phonemes_to_ids(tp.phonemize(text))
            _, dur = tp.run(ids, np.ones(len(ids)), ns_, ls, nw, seed)
            audio, _ = tp.run(ids, dur, ns_, ls, nw, seed)
            y = hp(resample_poly(audio, 320, 147), 90)          # 22050 -> 48000
            np.save(path, (y / (np.abs(y).max() + 1e-9) * 0.8).astype(np.float32))
        return fade(np.load(path).astype(np.float64), 0.003, 0.01)   # one path: identical first and cached

    def say_sync(self, model, sid, text, seed, durations, ns_=0.6, nw=0.0):
        """Fixed per-phoneme durations (frames): every speaker in perfect rhythmic sync."""
        key = self._key("sync2", model, sid, text, seed, tuple(np.round(durations, 2)), ns_, nw)
        path = os.path.join(self.cache_dir, key + ".npy")
        if not os.path.exists(path):
            tp = self._piper(model)
            tp.sid = int(sid)
            ids = tp.voice.phonemes_to_ids(tp.phonemize(text))
            if len(ids) != len(durations):
                raise RuntimeError("duration/phoneme mismatch")
            audio, _ = tp.run(ids, np.asarray(durations, np.float32), ns_, 1.0, nw, seed)
            y = hp(resample_poly(audio, 320, 147), 90)
            np.save(path, (y / (np.abs(y).max() + 1e-9) * 0.8).astype(np.float32))
        return fade(np.load(path).astype(np.float64), 0.003, 0.01)

    def sync_durations(self, text, frames_vowel=7.0, frames_cons=3.0):
        """A mechanical, identical rhythm for `text`: every vowel / consonant id gets a fixed frame count."""
        key = self._key("durs1", text, frames_vowel, frames_cons)
        path = os.path.join(self.cache_dir, key + ".json")
        if os.path.exists(path):
            import json as _json
            with open(path) as fh:
                return _json.load(fh)
        dur = self._sync_durations(text, frames_vowel, frames_cons)
        import json as _json
        with open(path, "w") as fh:
            _json.dump(dur, fh)
        return dur

    def _sync_durations(self, text, frames_vowel, frames_cons):
        tp = self._piper(LIBRI)
        ph = tp.phonemize(text)
        ids = tp.voice.phonemes_to_ids(ph)
        inv = {}
        for sym, v in tp.voice.config.phoneme_id_map.items():
            for i in v:
                inv[i] = sym
        dur = []
        for i in ids:
            s = inv.get(i, "")
            if s in ("_", "^", "$", " ", "!", ".", ","):
                dur.append(1.0 if s == "_" else 2.0)
            elif any(c in "aeiouæɐɑɒɔəɛɜɪʊʌ" for c in s):
                dur.append(frames_vowel)
            elif s in ("ˈ", "ˌ", "ː"):
                dur.append(1.0)
            else:
                dur.append(frames_cons)
        return dur

    def sync_laugh(self, variant=0, voices=12):
        """N voices laughing in perfect sync, each normalized to the same RMS (uncanny), mono."""
        text = ["Ha ha ha ha ha!", "Ha ha ha ha!", "Ha ha ha ha ha ha!"][variant % 3]
        dur = self.sync_durations(text, 6.0 + variant * 0.5, 3.0)
        spk = (LIBRI_MALE[::2] + LIBRI_FEMALE[::3])
        out = None
        for v in range(voices):
            sid = spk[(v * 5 + variant * 3) % len(spk)]
            y = self.say_sync(LIBRI, sid, text, seed=1000 + 17 * v + variant, durations=dur)
            y = y / (np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) + 1e-9)
            out = y if out is None else (out[:len(y)] + y[:len(out)] if len(out) != len(y) else out + y)
        return peak_norm(out)

    def sync_laugh_grid(self, n_ha, bpm, variant=0, voices=12, lead=0.05):
        """Exactly `n_ha` HAs on the picture's laugh clock: each HA's vowel onset at lead + k * 60/bpm seconds.
        Every voice speaks 'Ha ha ... ha!' on identical phoneme durations (so they are already in sync with one
        another and the 'h' onsets are known exactly); the HA period those durations give (19 frames =
        0.221 s) is pulled onto 60/bpm by one tiny varispeed of the sum (~3 %), and the vowel onsets (50 %
        energy rise, median over the HAs) are set `lead` after the cue start -- S4 starts each volley cue
        40 ms before the mouths begin to open, so the vowel arrives as the mouths open."""
        n_ha = int(max(1, n_ha))
        text = " ".join(["Ha"] + ["ha"] * (n_ha - 1)) + "!"
        dur = self.sync_durations(text, 7.0, 3.0)
        spk = (LIBRI_MALE[::2] + LIBRI_FEMALE[::3])
        out = None
        for v in range(voices):
            sid = spk[(v * 5 + variant * 3) % len(spk)]
            y = self.say_sync(LIBRI, sid, text, seed=1000 + 17 * v + variant, durations=dur)
            y = y / (np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) + 1e-9)
            k = len(y) if out is None else min(len(out), len(y))
            out = y[:k] if out is None else out[:k] + y[:k]
        # HA onsets from the durations themselves ('h' starts), then each HA's energy peak from the sum
        tp = self._piper(LIBRI)
        inv = {}
        for sym, ids_ in tp.voice.config.phoneme_id_map.items():
            for i in ids_:
                inv[i] = sym
        ids = tp.voice.phonemes_to_ids(tp.phonemize(text))
        fr = 256.0 / 22050.0
        cum = np.concatenate([[0.0], np.cumsum(dur)])
        on = np.array([cum[j] * fr for j, i in enumerate(ids) if inv.get(i) == "h"])
        if len(on) < 1:
            return peak_norm(out)
        period = float(np.median(np.diff(on))) if len(on) > 1 else 19 * fr
        env = np.sqrt(np.convolve(out ** 2, np.ones(ns(0.015)) / ns(0.015), "same"))
        rise = []
        for a in on:                                 # each HA's vowel onset: first 50 % crossing in its slot
            i0, i1 = ns(a), min(len(env), ns(a + period))
            if i1 > i0 + 1:
                seg = env[i0:i1]
                rise.append(int(np.argmax(seg >= 0.5 * seg.max())) / SR)
        off = float(np.median(rise)) if rise else 0.07
        ratio = period / (60.0 / bpm)
        y = varispeed(out, ratio)
        first = (on[0] + off) / ratio                # where the first vowel onset is after the varispeed
        shift = ns(abs(first - lead))
        if first > lead:
            y = y[shift:]
        else:
            y = np.concatenate([np.zeros(shift), y])
        return peak_norm(fade(y.copy(), 0.004, 0.02))

    def unison(self, text, voices=12, seed=0, frames_vowel=8.0):
        dur = self.sync_durations(text, frames_vowel, 3.0)
        spk = LIBRI_MALE[1::2] + LIBRI_FEMALE[1::3]
        out = None
        for v in range(voices):
            y = self.say_sync(LIBRI, spk[(v * 7 + seed) % len(spk)], text, seed=2000 + 13 * v + seed,
                              durations=dur, ns_=0.667, nw=0.0)
            y = y / (np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) + 1e-9)
            n = min(len(out), len(y)) if out is not None else len(y)
            out = y[:n] if out is None else out[:n] + y[:n]
        return peak_norm(out)

    def pool(self, phrases, n, seed, mix=(0.45, 0.45, 0.05, 0.05), ls=(0.88, 1.08)):
        """n utterances (cycling phrases) from a speaker mix (libri M, libri F, vctk M, vctk F)."""
        rng = np.random.default_rng(seed)
        groups = [(LIBRI, LIBRI_MALE), (LIBRI, LIBRI_FEMALE), (VCTK, VCTK_MALE), (VCTK, VCTK_FEMALE)]
        out = []
        for i in range(n):
            g = rng.choice(4, p=np.asarray(mix) / np.sum(mix))
            model, spk = groups[g]
            sid = spk[rng.integers(len(spk))]
            text = phrases[(i * 7 + seed) % len(phrases)]
            out.append(self.say(model, sid, text, seed=int(rng.integers(1, 1 << 30)),
                                ls=float(rng.uniform(*ls)), ns_=0.667, nw=0.8))
        return out


_WALLA_FOR_CUES = None


def set_walla(w):
    global _WALLA_FOR_CUES
    _WALLA_FOR_CUES = w


def crowd_layer(rng, pool, n, t_lo, t_hi, count, rate=(0.94, 1.1), gain_db=(-6.0, 0.0), pan=0.85,
                lp_hz=None, density=None, shout=0.0):
    """Scatter `count` utterances from `pool` over [t_lo, t_hi] s (optionally weighted by density(t))."""
    out = np.zeros((n, 2))
    for i in range(count):
        u = pool[rng.integers(len(pool))]
        u = fade(varispeed(u, rng.uniform(*rate)).copy(), 0.003, 0.01)
        if shout > 0:
            u = softclip(peq(u, 2600, 4.0 * shout, 0.9) * (1 + 2 * shout), 1.0 + shout)
        for _ in range(8):
            t0 = rng.uniform(t_lo, max(t_lo + 1e-3, t_hi - 0.3))
            if density is None or rng.uniform() < density(t0):
                break
        g = 10 ** (rng.uniform(*gain_db) / 20)
        place(out, stereo(u * g, rng.uniform(-pan, pan)), ns(t0))
    if lp_hz:
        out = lp(out, lp_hz)
    return out


def babble_bed(rng, n, voices=24, f_lo=95, f_hi=240, syl=(3.5, 6.0), lp_hz=3500):
    """Procedural crowd babble (glottal-ish sources through wandering formants, syllabic AM) -> stereo.
    Rendered at 16 kHz (it lives below ~4.5 kHz) and upsampled."""
    from scipy.signal import butter as _butter
    sr = SR // 3
    m = n // 3 + 2
    t = np.arange(m) / sr
    L, R = np.zeros(m), np.zeros(m)

    def sm(rate, lo, hi):                       # smooth_rand at the low rate
        k = max(2, int(m / sr * rate) + 3)
        pts = rng.uniform(lo, hi, k)
        x = np.linspace(0, k - 2.0001, m)
        i = np.floor(x).astype(int)
        f = 0.5 - 0.5 * np.cos(np.pi * (x - i))
        return pts[i] * (1 - f) + pts[i + 1] * f

    def rs(x, fc, q):
        w = 2 * np.pi * fc / sr
        al = np.sin(w) / (2 * q)
        bb = np.array([al, 0.0, -al])
        aa = np.array([1 + al, -2 * np.cos(w), 1 - al])
        return lfilter(bb / aa[0], aa / aa[0], x)
    for v in range(voices):
        f0 = rng.uniform(f_lo, f_hi) * (1 + 0.08 * sm(2.0, -1, 1))
        ph = np.cumsum(f0 / sr)
        src = (ph % 1.0) - 0.5 + 0.3 * rng.standard_normal(m)
        sylr = rng.uniform(*syl)
        am = np.clip(sm(sylr * 2.0, -0.6, 1.0), 0, 1) ** 1.5
        am *= np.clip(sm(0.4, -0.3, 1.0), 0, 1)
        g1 = (sm(sylr, 350, 800) - 350) / 450
        y = rs(src, 450, 3.5) * (1 - g1) + rs(src, 700, 3.5) * g1 + 0.6 * rs(src, 1500, 3.5) + 0.25 * rs(src, 2600, 3.5)
        y *= am
        th = (rng.uniform(-0.9, 0.9) + 1) * np.pi / 4
        L += y * np.cos(th)
        R += y * np.sin(th)
    out = np.stack([L, R], 1)
    out = sosfilt(_butter(2, [120 / (sr / 2), min(lp_hz, 0.45 * sr) / (sr / 2)], "band", output="sos"), out, axis=0)
    out = resample_poly(out, 3, 1, axis=0)[:n]
    if len(out) < n:
        out = np.pad(out, ((0, n - len(out)), (0, 0)))
    return out / (np.abs(out).max() + 1e-9)


# ================================================================================================
# AMBIENCE BUILDING BLOCKS
# ================================================================================================
def room_tone(rng, n, lo=40, hi=1300, target=-60.0):
    y = wide(rng, lambda r, m: pink(r, m), n, 0.8)
    y = lp(hp(y, lo), hi)
    return to_lufs(y, target)


def wind(rng, n, target=-40.0, lo=120, hi=900, gust=0.12):
    def one(r, m):
        base = brown(r, m, 0.995) * 0.5 + pink(r, m) * 0.5
        y = np.zeros(m)
        for fc, q in ((260, 1.2), (480, 1.5), (820, 1.8)):
            y += reson(base, fc * r.uniform(0.85, 1.15), q) * smooth_rand(r, m, gust * 3, 0.2, 1.0)
        return y * smooth_rand(r, m, gust, 0.25, 1.0)
    y = wide(rng, one, n, 0.9)
    y = lp(hp(y, lo), hi)
    return to_lufs(y, target)


def hearth(rng, n, target=-42.0):
    """Hearth fire: low roar, crackle stream, occasional snaps and sap hiss."""
    t = tvec(n)
    roar = wide(rng, lambda r, m: lp(brown(r, m, 0.997), 260) * smooth_rand(r, m, 0.8, 0.5, 1.0), n, 0.6)
    roar = to_lufs(hp(roar, 50.0, 4), target - 4)                 # the fire's roar lives at 50-260 Hz
    cr = np.zeros((n, 2))
    for ch in range(2):
        cr[:, ch] = grain_bank(rng, n, 9.0, 1000, 6000, (0.0015, 0.005), banks=8, amp_sigma=0.8)
    for _ in range(int(n / SR / 2.5)):
        snap = excite(burst(rng, ns(0.001), 0.0003), modes(rng, [(2200, 0.006, 1), (3500, 0.004, 0.7),
                                                                 (1300, 0.01, 0.5)], ns(0.05)))
        place(cr, stereo(snap * rng.uniform(1.5, 4.0), rng.uniform(-0.4, 0.4)), rng.integers(0, n))
    cr = to_lufs(cr, target - 1)
    hiss = wide(rng, lambda r, m: hp(white(r, m), 5000) * np.clip(smooth_rand(r, m, 0.5, -1.5, 1.0), 0, 1), n, 0.5)
    hiss = to_lufs(hiss, target - 14) if np.any(hiss) else hiss
    return roar + cr + hiss + 0 * t[:, None]


def rain_layers(rng, n, target=-26.0):
    """Rain on cobbles: far hiss + mid patter + near drops (cobble/puddle) + hits on wooden shutters."""
    far = wide(rng, lambda r, m: bp(pink(r, m), 500, 9000) * smooth_rand(r, m, 0.2, 0.85, 1.0), n, 1.0)
    far = to_lufs(far, target - 3)
    patter = np.zeros((n, 2))
    for ch in range(2):
        patter[:, ch] = bp(grain_bank(rng, n, 1700, 1400, 8000, (0.0006, 0.002), banks=14), 1200, 10000)
    patter = to_lufs(patter, target - 4)
    near = np.zeros((n, 2))
    k = int(n / SR * 26)
    for _ in range(k):
        m = ns(0.03)
        f0 = rng.uniform(1300, 4200)
        tt = tvec(m)
        plip = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * tt / tt[-1])) / SR) * np.exp(-tt / 0.006)
        plip += 0.6 * burst(rng, m, 0.0015, 1500, 9000)
        place(near, stereo(plip * math.exp(0.5 * rng.standard_normal()), rng.uniform(-0.9, 0.9)), rng.integers(0, n))
    near = to_lufs(near, target - 7)
    shut = np.zeros((n, 2))
    for _ in range(int(n / SR * 7)):
        tok = excite(burst(rng, ns(0.0015), 0.0005, hi=5000), modes(rng, WOOD_PLAQUE[:4], ns(0.06)))
        place(shut, stereo(tok * rng.uniform(0.3, 1.0), rng.uniform(-1, -0.3) if rng.uniform() < 0.6 else
                           rng.uniform(0.3, 1.0)), rng.integers(0, n))
    shut = to_lufs(shut, target - 13)
    return far + patter + near + shut


def gutter(rng, n, target=-36.0, pan=-0.55):
    src = bp(white(rng, n), 250, 2600)
    bab = np.zeros(n)
    for fc in (420, 760, 1300, 2100):
        bab += reson(src, fc, 6.0) * smooth_rand(rng, n, 14.0, 0.0, 1.0) ** 3
    y = bab + 0.3 * src * smooth_rand(rng, n, 1.0, 0.6, 1.0)
    st = stereo(y, pan) + 0.15 * stereo(y, -pan)
    return to_lufs(st, target)


def drips(rng, n, period=(0.7, 1.4), target=-38.0, pan=0.5, f=(1300, 2200)):
    y = np.zeros(n)
    t = rng.uniform(0, period[1])
    f0 = rng.uniform(*f)
    while t < n / SR:
        m = ns(0.08)
        tt = tvec(m)
        ff = f0 * (1 + rng.uniform(-0.06, 0.06)) * (1 + 0.8 * np.exp(-tt / 0.004))
        d = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-tt / 0.02) * np.clip(tt / 0.0005, 0, 1)
        place(y, d * rng.uniform(0.6, 1.0), ns(t))
        t += rng.uniform(*period)
    return to_lufs(stereo(y, pan), target)


def thunder(rng, dur=5.0, n_rolls=3):
    """Distant thunder: no crack, a slow rise and long irregular rolling rumble."""
    n = ns(dur)
    t = tvec(n)
    env = np.zeros(n)
    for k in range(n_rolls):
        c = rng.uniform(0.2, 0.55) * dur * (k + 1) / n_rolls
        w = rng.uniform(0.25, 0.6)
        env += rng.uniform(0.5, 1.0) * np.exp(-np.maximum(t - c, 0) / (w * 2.5)) * np.clip((t - c + w) / w, 0, 1)
    env *= np.clip(t / 0.35, 0, 1)
    y = wide(rng, lambda r, m: lp(brown(r, m, 0.999), 140) + 0.3 * lp(pink(r, m), 400), n, 0.7)
    y *= env[:, None]
    return fade(hp(y, 32, 4), 0.05, 0.6)


BELL_PARTIALS = [(0.5, 9.0, 0.55), (1.0, 5.5, 0.8), (1.19, 3.6, 0.5), (1.5, 3.0, 0.38), (2.0, 2.4, 1.0),
                 (2.52, 1.6, 0.35), (2.67, 1.4, 0.32), (3.01, 1.1, 0.3), (4.16, 0.7, 0.2), (5.43, 0.45, 0.12)]


def bell(rng, f_nominal, dur=6.0, partials=BELL_PARTIALS):
    """Minor-third church bell (hum, prime, tierce, quint, nominal, ...); f_nominal = the strike pitch."""
    n = ns(dur)
    t = tvec(n)
    y = np.zeros(n)
    f1 = f_nominal / 2.0
    for r, tau, a in partials:
        for det in (0.0, rng.uniform(0.4, 1.1)):            # doublets: the slow 'wah' beating of a bell
            f = f1 * r + det
            if f > 0.45 * SR:
                continue
            y += 0.5 * a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / tau)
    y += 0.3 * burst(rng, n, 0.004, 1000, 6000)
    return fade(y * np.clip(t / 0.002, 0, 1), 0.0, 0.3)


def handbell(rng, f0, dur=2.2):
    return bell(rng, f0, dur, [(1.0, 1.4, 1.0), (2.0, 0.9, 0.5), (2.76, 0.6, 0.45), (4.07, 0.35, 0.3),
                               (5.4, 0.2, 0.2), (0.5, 1.6, 0.15)])


def blackbird_phrase(rng):
    """Fluty blackbird phrase: 3-7 gliding whistles + a twittery squeak at the end."""
    notes = rng.integers(3, 8)
    out = []
    for k in range(notes):
        d = rng.uniform(0.06, 0.22)
        m = ns(d)
        tt = tvec(m)
        f0 = rng.uniform(1500, 3300)
        f1 = f0 * rng.uniform(0.8, 1.3)
        f = f0 + (f1 - f0) * (tt / tt[-1]) ** rng.uniform(0.6, 1.6)
        f *= 1 + 0.01 * np.sin(2 * np.pi * rng.uniform(20, 40) * tt)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out.append((np.sin(ph) + 0.12 * np.sin(2 * ph)) * hump(m, 0.3, 0.8))
        out.append(np.zeros(ns(rng.uniform(0.02, 0.08))))
    if rng.uniform() < 0.6:
        m = ns(rng.uniform(0.15, 0.3))
        tt = tvec(m)
        f = rng.uniform(4500, 6500) + 900 * np.sin(2 * np.pi * rng.uniform(25, 45) * tt)
        out.append(0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * hump(m, 0.5))
    return np.concatenate(out)


def robin_trill(rng):
    m = ns(rng.uniform(0.6, 1.2))
    tt = tvec(m)
    f = rng.uniform(3500, 5200) * (1 + 0.18 * np.sin(2 * np.pi * rng.uniform(14, 22) * tt)) * \
        (1 + 0.15 * smooth_rand(rng, m, 6, -1, 1))
    am = np.clip(np.sin(2 * np.pi * rng.uniform(12, 18) * tt), 0, 1) ** 2
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * am * hump(m, 0.4)


def chink(rng):
    """Blackbird's 'chink-chink' roosting call (dusk)."""
    y = []
    for _ in range(rng.integers(2, 5)):
        m = ns(0.035)
        tt = tvec(m)
        f = rng.uniform(5000, 6200) * (1 - 0.25 * tt / tt[-1])
        y.append(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.012) * np.clip(tt / 0.001, 0, 1))
        y.append(np.zeros(ns(rng.uniform(0.09, 0.16))))
    return np.concatenate(y)


def birds(rng, n, rate_curve, target=-40.0):
    """Evening birdsong: rate_curve(t) -> events per second (decreasing = birds settling)."""
    out = np.zeros((n, 2))
    t = rng.uniform(0, 0.8)
    while t < n / SR:
        r = rng.uniform()
        y = blackbird_phrase(rng) if r < 0.55 else (robin_trill(rng) if r < 0.8 else chink(rng))
        dist = rng.uniform(0.3, 1.0)
        y = lp(y, 9000 - 5000 * dist) * (1.1 - 0.7 * dist)
        place(out, stereo(y, rng.uniform(-0.95, 0.95)), ns(t))
        t += rng.exponential(1.0 / max(rate_curve(t), 0.05))
    return to_lufs(out, target) if np.any(out) else out


def leaves(rng, n, target=-42.0):
    """Breeze in the oak: gusts of leaf rustle (dense granular clicks) + soft air."""
    gust = smooth_rand(rng, n, 0.25, 0.1, 1.0) ** 2

    def one(r, m):
        g = grains(r, m, 2400, env=gust[:m])
        return bp(g, 1800, 9000) + 0.4 * bp(white(r, m) * gust[:m], 300, 2500)
    y = wide(rng, one, n, 1.0)
    return to_lufs(y, target)


def crickets(rng, n, count=7, target=-36.0):
    out = np.zeros((n, 2))
    for c in range(count):
        fc = rng.uniform(4100, 5200)
        syl = rng.uniform(0.012, 0.018)
        syl_rate = rng.uniform(26, 34)
        nsyl = rng.integers(3, 5)
        chirp_period = rng.uniform(0.35, 0.7)
        dist = rng.uniform(0.2, 1.0)
        y = np.zeros(n)
        m = ns(syl)
        tt = tvec(m)
        s = np.sin(2 * np.pi * fc * tt) * hump(m, 0.4, 0.8)
        t = rng.uniform(0, chirp_period)
        while t < n / SR:
            for k in range(nsyl):
                place(y, s, ns(t + k / syl_rate))
            t += chirp_period * rng.uniform(0.9, 1.1)
            if rng.uniform() < 0.04:
                t += rng.uniform(0.5, 2.0)                       # a cricket pauses
        y = lp(y, 9000 - 4000 * dist) * (1.2 - 0.8 * dist)
        out += stereo(y, rng.uniform(-0.95, 0.95))
    return to_lufs(out, target)


def owl_hoot(rng):
    """Storybook tawny owl: 'hoo ... hoo-hoo-hooooo' (breathy, slight tremolo on the long note)."""
    f0 = rng.uniform(380, 450)
    segs = [(0.35, 1.0, 0.0), (0.55, 0.0, 0.0), (0.12, 0.7, 0.0), (0.06, 0.0, 0.0), (0.14, 0.75, 0.0),
            (0.05, 0.0, 0.0), (0.9, 0.9, 0.3)]
    out = []
    for d, a, trem in segs:
        m = ns(d)
        tt = tvec(m)
        if a == 0:
            out.append(np.zeros(m))
            continue
        f = f0 * (1.02 - 0.05 * tt / max(d, 1e-3))
        ph = 2 * np.pi * np.cumsum(f) / SR
        e = hump(m, 0.25, 0.8) * a * (1 - trem * (0.5 + 0.5 * np.sin(2 * np.pi * 13 * tt)))
        y = (np.sin(ph) + 0.15 * np.sin(2 * ph)) * e
        y += 0.08 * bp(white(rng, m), 300, 1500) * e
        out.append(y)
    return lp(np.concatenate(out), 1800)


def bubbling(rng, n, rate=4.5, target=-44.0):
    y = np.zeros(n)
    k = rng.poisson(rate * n / SR)
    for _ in range(k):
        m = ns(rng.uniform(0.015, 0.045))
        tt = tvec(m)
        f0 = rng.uniform(700, 2600)
        b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.25 * tt / tt[-1])) / SR) * np.exp(-tt / (m / SR / 3.5)) * \
            np.clip(tt / 0.001, 0, 1) * np.clip((tt[-1] - tt) / 0.003, 0, 1)
        place(y, b * rng.uniform(0.3, 1.0), rng.integers(0, n))
    st = stereo(y, 0.35) + 0.2 * stereo(y, -0.4)
    return to_lufs(st, target)


def hum_cluster(rng, n, freqs, harmonics, flicker=0.0, target=-40.0, pans=None, buzz=0.0, drift=0.002):
    """Sum of tones (with harmonics) + optional flicker dips and a buzzy edge.  drift: slow pitch wander
    (fraction); mains-locked hum never wanders, a living wisp-flame does."""
    t = tvec(n)
    out = np.zeros((n, 2))
    for i, f in enumerate(freqs):
        fm = 1 + 0.002 * smooth_rand(rng, n, 1.5, -1, 1)
        if drift > 0.002:
            fm = fm + (drift - 0.002) * smooth_rand(rng, n, 0.3, -1, 1)
        ph = 2 * np.pi * np.cumsum(f * fm) / SR + rng.uniform(0, 6.28)
        y = sum(a * np.sin((k + 1) * ph) for k, a in enumerate(harmonics))
        if buzz > 0:
            y += buzz * np.sign(np.sin(ph)) * 0.3
        if flicker > 0:
            dips = np.ones(n)
            for _ in range(int(n / SR * flicker)):
                c = rng.integers(0, n)
                w = ns(rng.uniform(0.03, 0.15))
                lo, hi = max(0, c - w), min(n, c + w)
                dips[lo:hi] *= 1 - rng.uniform(0.3, 0.8) * hump(hi - lo, 0.5, 0.5)
            y *= dips
        p = pans[i] if pans else rng.uniform(-0.7, 0.7)
        out += stereo(y, p)
    out = lp(out, 4500)
    return to_lufs(out, target) + 0 * t[:, None]


def drums_rumble(rng, n, count=5, target=-31.0):
    """Rows of enchanted tumbling drums: rotation rumble, cloth swish, tumbling thumps, brass rattle."""
    out = np.zeros((n, 2))
    t = tvec(n)
    for d in range(count):
        rot = rng.uniform(0.62, 0.95)                             # rotations per second
        phase = rng.uniform(0, 1)
        dist = d / max(count - 1, 1)
        pan = np.linspace(-0.8, 0.8, count)[d] + rng.uniform(-0.1, 0.1)
        rotm = 0.5 + 0.5 * np.sin(2 * np.pi * (rot * t + phase))
        rumble = no_sub(lp(brown(rng, n, 0.996), 170), 45.0) * (0.2 + 0.8 * rotm ** 2)
        swish = bp(white(rng, n), 300, 1600) * (0.15 + 0.85 * rotm ** 3) * 0.45
        y = rumble + swish
        thumps = np.zeros(n)
        tk = (1.0 - phase) / rot
        while tk < n / SR:
            th = k_drum_spin_thunk(rng, {"vel": rng.uniform(0.4, 0.8)})
            place(thumps, th * rng.uniform(0.5, 1.0), ns(tk + rng.uniform(-0.05, 0.05)))
            tk += 1.0 / rot * rng.choice([1, 1, 1, 0.5])
        y = y + 3.2 * thumps
        y = lp(y, 2400 - 1200 * dist) * (1.0 - 0.45 * dist)
        out += stereo(y, pan)
    for _ in range(int(n / SR / 6)):                              # an axle creaks now and then
        cr = k_creak_wood(rng, dict(material="stool", dur=rng.uniform(0.3, 0.6)))
        place(out, stereo(0.08 * cr, rng.uniform(-0.8, 0.8)), rng.integers(0, n))
    return to_lufs(out, target)


# ================================================================================================
# SCENE AMBIENCES.  ctx: dur (s), beats {id: (t, end)}, lines [(id, start, end, speaker)], cues, walla,
#                   pre/post margins (s).  Return stereo (n, 2) covering [-pre, dur + post].
# ================================================================================================
def _beat(ctx, bid, default):
    b = ctx.get("beats", {}).get(bid)
    return default if b is None else b[0]


def _beat_end(ctx, bid, default):
    b = ctx.get("beats", {}).get(bid)
    return default if (b is None or b[1] is None) else b[1]


def _span(ctx):
    pre, post = ctx.get("pre", 0.5), ctx.get("post", 0.5)
    n = ns(ctx["dur"] + pre + post)
    return n, pre


def amb_s0(ctx, rng):
    n, pre = _span(ctx)
    y = hearth(rng, n, -43.0) + room_tone(rng, n, target=-58.0)
    fl = np.zeros(n)
    for _ in range(int(ctx["dur"] / 4)):
        c = k_candle_flicker(rng, {})
        place(fl, c, rng.integers(0, n))
    y += to_lufs(stereo(fl, 0.25), -56.0)
    return y


def amb_s1(ctx, rng):
    n, pre = _span(ctx)
    drums = drums_rumble(rng, n, 5, -31.5)
    wisps = hum_cluster(rng, n, [151.0, 166.7, 179.3], [1.0, 0.55, 0.35, 0.22, 0.12, 0.08], flicker=0.7,
                        target=-41.0, pans=[-0.6, 0.15, 0.7], buzz=0.25, drift=0.007)
    sizzle = wide(rng, lambda r, m: bp(white(r, m), 3200, 6500) * (0.6 + 0.4 * np.sin(2 * np.pi * 166.7 * tvec(m))),
                  n, 0.5)
    sizzle = to_lufs(sizzle, -58.0)
    night = wind(rng, n, -45.0, 150, 700, 0.1)
    y = drums + wisps + sizzle + night + room_tone(rng, n, target=-58.0)
    return reverb_mix(y, "stonehall", 0.35, n)


def amb_s2(ctx, rng):
    n, pre = _span(ctx)
    orbs = hum_cluster(rng, n, [523.3, 528.1, 1046.5], [1.0, 0.25, 0.1], flicker=0.0, target=-47.0,
                       pans=[-0.4, 0.4, 0.0])
    # the orbs' glassy 'singing' overtone (G7 = 3 x C6, slowly beating, its level breathing like a wet finger
    # on a goblet) -- the clinical edge without a steady electronic whine (a pure 7.9 kHz sine read as coil
    # whine: period rule)
    sing = np.zeros(n)
    for f0, ph0 in ((3136.0, 0.0), (3140.6, 1.3)):
        f = f0 * (1 + 0.0008 * smooth_rand(rng, n, 0.6, -1, 1))
        sing += np.sin(2 * np.pi * np.cumsum(f) / SR + ph0)
    sing *= smooth_rand(rng, n, 0.25, 0.25, 1.0) ** 2
    glass = to_lufs(stereo(sing, 0.25) + 0.3 * stereo(sing, -0.5), -62.0)
    y = orbs + glass + bubbling(rng, n, 4.0, -46.0) + room_tone(rng, n, 50, 1500, -55.0)
    for _ in range(int(ctx["dur"] / 7)):                                  # the old floorboards
        cr = k_creak_wood(rng, dict(material="floor", dur=rng.uniform(0.3, 0.5)))
        place(y, stereo(0.025 * cr, rng.uniform(-0.6, 0.6)), rng.integers(0, n))
    return reverb_mix(y, "shop", 0.2, n)


def amb_s3(ctx, rng):
    n, pre = _span(ctx)
    y = rain_layers(rng, n, -27.0) + gutter(rng, n, -37.0, -0.6) + drips(rng, n, (0.75, 1.3), -40.0, 0.55)
    y += drips(rng, n, (1.1, 2.0), -44.0, -0.2, (1800, 2600))
    for t0, dur, g in ((3.2, 6.0, -36.0), (16.6, 5.0, -34.0)):           # distant thunder rolls
        th = thunder(rng, dur, 3)
        th = to_lufs(th, g)
        place(y, th, ns(pre + t0 * ctx["dur"] / 20.0))
    hb = np.zeros(n)                                                      # far-off watchman's handbell
    t_bell = pre + _beat(ctx, "s3_hold", 10.0) + 1.6
    for k in range(3):
        place(hb, handbell(rng, 659.3), ns(t_bell + 0.62 * k))
    hb = lp(hb, 2200)
    y += to_lufs(reverb(stereo(hb, 0.6), "far")[:n], -46.0)
    return reverb_mix(y, "street", 0.12, n)


def tavern_perspective(ctx):
    """[(t_from, t_to, 'out'|'in')] scene-local: outside until s4_inside, inside until the door closes."""
    t_in = _beat(ctx, "s4_inside", 6.3)
    t_close = ctx.get("door_close_t")
    if t_close is None:
        t_close = _beat(ctx, "s4_exit", 20.0) + 2.6
    return [(-10.0, t_in, "out"), (t_in, t_close, "in"), (t_close, 1e9, "out")]


def perspective_gain(ctx, n, pre, inside=True, xf=0.012):
    """Per-sample weight of the 'inside' (inside=True) or 'outside' render, hard switches (12 ms xfades)."""
    g = np.zeros(n)
    t = tvec(n) - pre
    for a, b, kind in tavern_perspective(ctx):
        if (kind == "in") == inside:
            g = np.maximum(g, np.clip(np.minimum((t - a) / xf + 0.5, (b - t) / xf + 0.5), 0, 1))
    return g


def muffle(x):
    """Heard through a heavy door / timber wall: dark, thin, a little boomy."""
    y = lp(x, 620, 4)
    y = peq(y, 170, 3.0, 0.9)
    return y * 10 ** (-13.0 / 20)


def amb_s4(ctx, rng):
    """Tavern: inside chatter + tankards (+ the swell roar); outside: street + muffled chatter."""
    n, pre = _span(ctx)
    w = ctx.get("walla")
    t_sw = _beat(ctx, "s4_swell", 10.8)
    chatter = babble_bed(rng, n, 26, 95, 230, (3.5, 6.0), 4000)
    chatter = to_lufs(chatter, -25.0)
    if w is not None:
        pool = w.pool(TAVERN, 30, seed=401, mix=(0.42, 0.33, 0.15, 0.10))
        lay = crowd_layer(rng, pool, n, 0.0, n / SR, 70, gain_db=(-9, 0), pan=0.9, lp_hz=6500)
        chatter = chatter + to_lufs(lay, -24.0)
        hey = w.unison("Hey!", voices=14, seed=4)
        huz = w.unison("Huzzah!", voices=14, seed=5)
        roar = crowd_layer(rng, w.pool(CHEER[:6] + ["Huzzah!", "Hey!", "Ha ha!"], 16, seed=402), n,
                           pre + t_sw + 0.1, pre + t_sw + 2.6, 30, gain_db=(-6, 0), pan=0.9, shout=0.6)
        roar = to_lufs(roar, -21.0) if np.any(roar) else roar
        place(roar, stereo(peak_norm(hey) * 0.55, 0.0), ns(pre + t_sw - 0.02))
        place(roar, stereo(peak_norm(huz) * 0.45, 0.1), ns(pre + t_sw + 3.0))
        sw_env = np.clip((tvec(n) - pre - t_sw) / 0.08, 0, 1) * np.clip((pre + t_sw + 4.2 - tvec(n)) / 1.4, 0, 1)
        chatter = chatter * (1 + 1.2 * sw_env)[:, None] + roar
    clinks = np.zeros((n, 2))
    for _ in range(int(ctx["dur"] * 1.3)):
        c, _w = render_cue("glass_clink", {"material": "pewter" if rng.uniform() < 0.7 else "glass"},
                           int(rng.integers(1, 1 << 30)))
        place(clinks, c * rng.uniform(0.3, 1.0), rng.integers(0, n))
    for _ in range(int(ctx["dur"] * 0.5)):
        c, _w = render_cue("bench_scrape", {"dur": rng.uniform(0.25, 0.5)}, int(rng.integers(1, 1 << 30)))
        place(clinks, 0.15 * c, rng.integers(0, n))
    inside = reverb_mix(chatter + to_lufs(clinks, -33.0), "tavern", 0.35, n)
    g_in = perspective_gain(ctx, n, pre, True)
    g_out = perspective_gain(ctx, n, pre, False)
    street = wind(rng, n, -44.0, 150, 800, 0.15) + room_tone(rng, n, 40, 900, -60.0)
    creaks = np.zeros((n, 2))
    for _ in range(int(ctx["dur"] / 5)):                                  # lantern strings creak in the wind
        cr = k_creak_wood(rng, dict(material="door", dur=rng.uniform(0.25, 0.5)))
        place(creaks, stereo(0.04 * cr, rng.uniform(-0.8, 0.8)), rng.integers(0, n))
    outside = street + creaks + muffle(inside) * 1.4
    return inside * g_in[:, None] + outside * g_out[:, None]


def amb_s5(ctx, rng):
    """Square: crowd cheering -> HARD cut to near-silence at s5_silence -> sparse uneasy murmurs."""
    n, pre = _span(ctx)
    w = ctx.get("walla")
    t_sil = _beat(ctx, "s5_silence", 10.0)
    t_stop = _beat(ctx, "s5_stop", 8.5)
    t_low = _beat(ctx, "s5_lower", 10.8)
    t_low_end = _beat_end(ctx, "s5_lower", 13.0)
    l3_end = max([e for (lid, s, e, spk) in ctx.get("lines", []) if lid == "s5_l3"] or [21.7])
    t = tvec(n) - pre
    base = wind(rng, n, -47.0, 120, 700, 0.12) + room_tone(rng, n, 40, 800, -62.0)
    far = to_lufs(lp(babble_bed(rng, n, 10, 100, 220, (3, 5), 900), 700), -52.0)
    cheer = to_lufs(babble_bed(rng, n, 30, 100, 260, (4.5, 7.0), 4500), -26.0)
    if w is not None:
        pool = w.pool(CHEER, 36, seed=501, mix=(0.42, 0.3, 0.16, 0.12), ls=(0.85, 1.02))
        dens = (lambda tt: 0.55 + 0.45 * np.clip((tt - pre) / max(t_stop, 1), 0, 1))
        lay = crowd_layer(rng, pool, n, 0.0, pre + t_sil, 95, rate=(0.97, 1.14), gain_db=(-8, 0), pan=0.9,
                          lp_hz=7000, density=dens, shout=0.7)
        ooh = crowd_layer(rng, w.pool(["Ooh!", "Oh!", "Ooh?", "Eh?", "Wha..."], 10, seed=502), n,
                          pre + t_stop + 0.25, pre + t_sil - 0.2, 14, gain_db=(-6, 0), pan=0.8)
        cheer = cheer + to_lufs(lay, -22.5) + (to_lufs(ooh, -27.0) if np.any(ooh) else 0)
    cheer = reverb_mix(cheer, "square", 0.35, n)
    # the crowd builds toward the stop, wavers on the hug, and is CUT at s5_silence (5 ms: no click)
    build = 0.75 + 0.25 * np.clip(t / max(t_stop, 1.0), 0, 1)
    cut = np.clip((t_sil - t) / 0.005, 0, 1)
    cheer = cheer * (build * cut)[:, None]
    tail = reverb(lp(cheer[max(0, ns(pre + t_sil) - ns(0.08)): ns(pre + t_sil)].mean(axis=1), 3000) * 0.0 +
                  cheer[max(0, ns(pre + t_sil) - ns(0.08)): ns(pre + t_sil)].mean(axis=1), "square")
    tailbuf = np.zeros((n, 2))
    place(tailbuf, tail * 0.06, ns(pre + t_sil) - ns(0.08))
    # near-silence: the base drops to almost nothing at the cut, then creeps back a little
    quiet = np.where(t < t_sil, 1.0, 0.12 + 0.5 * np.clip((t - t_low_end) / 6.0, 0, 1))
    y = base * quiet[:, None] + far * np.where(t < t_sil, 1.0, 0.0)[:, None] + cheer + tailbuf
    if w is not None:
        mp = w.pool(MURMUR_UNEASY, 14, seed=503, mix=(0.45, 0.35, 0.1, 0.1), ls=(0.95, 1.15))
        l3_start = min([s_ for (lid, s_, e_, spk) in ctx.get("lines", []) if lid == "s5_l3"] or [18.8])
        dens = (lambda tt: float(np.clip(1.0 - (tt - pre - l3_start) / max(l3_end - l3_start, 1.0), 0.0, 1.0)))
        mur = crowd_layer(rng, mp, n, pre + t_low + 0.4, pre + l3_end - 0.6, 16, rate=(0.92, 1.02),
                          gain_db=(-9, -2), pan=0.85, lp_hz=2600, density=dens)
        mur = reverb_mix(to_lufs(mur, -42.0) if np.any(mur) else mur, "square", 0.3, n)
        y += mur
    return y


def amb_garden(ctx, rng, scene):
    n, pre = _span(ctx)
    dur = ctx["dur"]
    t = tvec(n) - pre
    w = ctx.get("walla")
    y = room_tone(rng, n, 40, 700, -62.0)
    if scene in (6, 7):
        y += leaves(rng, n, -44.0 if scene == 6 else -46.0)
        y += wind(rng, n, -50.0, 100, 500, 0.1)
        if scene == 6:
            rate = (lambda tt: 0.9 * max(0.15, 1.0 - tt / (dur * 1.3)))
        else:
            rate = (lambda tt: 0.25 * max(0.1, 1.0 - tt / dur))
        y += birds(rng, n, rate, -43.0 if scene == 6 else -47.0)
        coo = np.zeros(n)
        tc = rng.uniform(0.5, 2.0)
        while tc < n / SR:
            place(coo, pigeon_coo_wave(rng) * rng.uniform(0.5, 1.0), ns(tc))
            tc += rng.uniform(2.5, 5.0) if scene == 6 else rng.uniform(1.0, 2.6)
        y += to_lufs(stereo(coo, -0.2) + stereo(coo * 0.4, 0.5), -44.0 if scene == 6 else -41.0)
        if scene == 6:                                       # castle bells far off, during the long pause
            t_b = _beat(ctx, "s6_pause", 4.0) + 0.6
            bells = np.zeros(n)
            for k, f in enumerate((587.3, 440.0, 587.3, 440.0)):
                place(bells, bell(rng, f, 7.0) * (1.0 if k % 2 == 0 else 0.8), ns(pre + t_b + 1.25 * k))
            bells = lp(bells, 2500)
            y += to_lufs(reverb(stereo(bells, 0.45), "far")[:n], -47.0)
    if scene == 7 and w is not None:                         # warm murmur that grows as the bench fills
        t_a = _beat(ctx, "s7_teensit", 9.8)
        t_full = _beat(ctx, "s7_full", 15.0)
        pool = w.pool(BENCH, 26, seed=701, mix=(0.35, 0.35, 0.15, 0.15), ls=(0.95, 1.12))
        dens = (lambda tt: float(np.clip((tt - pre - t_a) / max(t_full - t_a, 1.0), 0.15, 1.0)))
        mur = crowd_layer(rng, pool, n, pre + t_a, n / SR, 34, rate=(0.95, 1.05), gain_db=(-8, 0), pan=0.6,
                          lp_hz=3000, density=dens)
        grow = np.clip((t - t_a) / max(t_full + 3.0 - t_a, 1.0), 0, 1) ** 0.8
        mur = to_lufs(mur, -36.0) * (0.2 + 0.8 * grow)[:, None]
        y += reverb_mix(mur, "garden", 0.25, n)
    if scene == 8:
        y += crickets(rng, n, 8, -37.0)
        y += wind(rng, n, -54.0, 100, 400, 0.08)
        owl = np.zeros(n)
        lines = sorted(ctx.get("lines", []), key=lambda r: r[1])
        if len(lines) >= 2:
            gaps = [(lines[0][2], lines[1][1]), (lines[-1][2], dur - 2.5)]
        else:
            gaps = [(4.6, 6.8), (15.0, 17.5)]
        for a, b in gaps:
            if b - a > 1.6:
                place(owl, owl_hoot(rng), ns(pre + a + 0.25))
        y += to_lufs(reverb(stereo(owl, -0.55), "far")[:n], -46.0) if np.any(owl) else 0
        if w is not None:
            pool = w.pool(BENCH, 22, seed=801, mix=(0.35, 0.35, 0.15, 0.15), ls=(0.98, 1.15))
            mur = crowd_layer(rng, pool, n, 0.0, n / SR, 28, rate=(0.93, 1.02), gain_db=(-9, 0), pan=0.5,
                              lp_hz=2400)
            y += reverb_mix(to_lufs(mur, -42.0), "garden", 0.3, n)
    return y


def amb_s9(ctx, rng):
    n, pre = _span(ctx)
    return room_tone(rng, n, 40, 800, -68.0)


def reverb_mix(x, name, wet, n):
    r = reverb(x, name)[:n]
    return x + wet * r * (np.sqrt(np.mean(x * x)) / (np.sqrt(np.mean(r * r)) + 1e-12))


def ambience(scene, ctx):
    """Stereo ambience bed for `scene` over [-pre, dur + post] (scene-local), deterministic."""
    rng = np.random.default_rng(seed_of("amb", scene))
    if ctx.get("walla") is not None:
        set_walla(ctx["walla"])
    fn = {0: amb_s0, 1: amb_s1, 2: amb_s2, 3: amb_s3, 4: amb_s4, 5: amb_s5, 9: amb_s9}.get(scene)
    if fn is not None:
        return fn(ctx, rng)
    if scene in (6, 7, 8):
        return amb_garden(ctx, rng, scene)
    n, _ = _span(ctx)
    return np.zeros((n, 2))


# ================================================================================================
# CLI: foley sheet + ambience previews (for inspection)
# ================================================================================================
def _write(path, x):
    import soundfile as sf
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(x, -1, 1), SR, subtype="PCM_24")


def foley_sheet(path=None, reps=2):
    """Every kind `reps` times (different seeds) with 0.35 s gaps; returns [(t, kind)]."""
    w = Walla()
    set_walla(w)
    chunks, index, t = [], [], 0.0
    for kind in KINDS:
        for r in range(reps):
            y, _ = render_cue(kind, {}, seed_of("sheet", kind, r))
            index.append((round(t, 3), kind))
            chunks.append(y)
            gap = np.zeros((ns(0.35), 2))
            chunks.append(gap)
            t += (len(y) + len(gap)) / SR
    x = np.concatenate(chunks)
    if path:
        _write(path, x)
    return x, index


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="procedural foley / ambience")
    ap.add_argument("--sheet", action="store_true", help="render every foley kind -> build/audio/foley_sheet.wav")
    ap.add_argument("--amb", type=int, nargs="*", help="render scene ambience(s) -> build/audio/amb_sN.wav")
    a = ap.parse_args()
    if a.sheet:
        x, idx = foley_sheet(os.path.join(BUILD, "foley_sheet.wav"))
        with open(os.path.join(BUILD, "foley_sheet.json"), "w") as fh:
            json.dump(idx, fh, indent=0)
        print("wrote", os.path.join(BUILD, "foley_sheet.wav"), f"{len(x) / SR:.1f} s")
    if a.amb:
        from film.lib import timeline as TL
        wl = Walla()
        for s in a.amb:
            sc = TL.scene(s)
            ctx = {"dur": sc.duration, "pre": 0.5, "post": 0.5, "walla": wl,
                   "beats": {b.id: (b.t, b.end) for b in TL.beats_in(s)},
                   "lines": [(l.id, l.start, l.end, l.speaker) for l in TL.lines_in(s)]}
            y = ambience(s, ctx)
            _write(os.path.join(BUILD, f"amb_s{s}.wav"), y)
            print(f"S{s}: {len(y) / SR:.1f} s, {lufs(y):.1f} LUFS, peak {20 * np.log10(np.abs(y).max() + 1e-9):.1f} dBFS")
