"""audiolib — small stereo float DSP toolkit for the film's audio (music, SFX, final mix).

Conventions
  * Audio is a float32 numpy array shaped (n, 2) (stereo) at SR = 44100 unless stated otherwise.
    Every function also accepts mono (n,) arrays and returns the same layout it was given, except
    `place`, `pan` and `to_stereo`, which always return stereo.
  * Gains are in dB, times in seconds, pan in -1 (left) .. +1 (right).
  * Nothing here clips: values may exceed 1.0 until `limit()` / `save()`.

Main API (see docs/audio.md for the full reference)
  load, save, to_stereo, to_mono, resample, silence, db2lin, lin2db
  gain_db, fade_in, fade_out, fades, pan, remove_dc, peak_normalize
  highpass, lowpass, bandpass, peaking_eq, low_shelf, high_shelf
  make_reverb_ir, reverb, reverb_wet
  compress, duck, place, render_sfx_events, mix_film
  loudness (BS.1770-4 integrated LUFS), normalize_loudness, true_peak, limit, master
  analyze, spectrogram_png

CLI:
  python3 audio/audiolib.py check a.wav [b.wav ...]            # peak / true-peak / LUFS / DC / NaN / jumps
  python3 audio/audiolib.py spectro in.wav out.png [--max-hz 8000] [--seconds a:b]
  python3 audio/audiolib.py mix --music out/music.wav [--sfx data/sfx_events.json] [--out out/mix.wav]
"""
import json
import math
import os
import sys
from fractions import Fraction
from functools import lru_cache

import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------------------------
# basics


def db2lin(db):
    return 10.0 ** (np.asarray(db, dtype=np.float64) / 20.0)


def lin2db(x, floor=-200.0):
    x = np.asarray(x, dtype=np.float64)
    return np.maximum(20.0 * np.log10(np.maximum(np.abs(x), 1e-12)), floor)


def _f32(x):
    return np.ascontiguousarray(np.asarray(x, dtype=np.float32))


def to_stereo(x):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2]


def to_mono(x):
    x = np.asarray(x, dtype=np.float32)
    return x if x.ndim == 1 else x.mean(axis=1)


def silence(seconds, sr=SR, channels=2):
    n = max(0, int(round(seconds * sr)))
    return np.zeros((n, channels) if channels > 1 else n, dtype=np.float32)


def resample(x, sr_from, sr_to):
    """Band-limited polyphase resampling (works on mono or (n, ch))."""
    if sr_from == sr_to:
        return _f32(x)
    fr = Fraction(int(sr_to), int(sr_from)).limit_denominator(1000)
    y = signal.resample_poly(np.asarray(x, dtype=np.float64), fr.numerator, fr.denominator, axis=0)
    return _f32(y)


def load(path, sr=SR, stereo=True):
    """Read any soundfile-readable file → float32 (n, 2) at `sr` (or mono (n,) if stereo=False)."""
    x, fsr = sf.read(path, dtype="float32", always_2d=True)
    if fsr != sr:
        x = resample(x, fsr, sr)
        if x.ndim == 1:
            x = x[:, None]
    if stereo:
        return to_stereo(x)
    return x.mean(axis=1).astype(np.float32)


def save(path, x, sr=SR, subtype="PCM_16", dither=True):
    """Write a wav. PCM_16 gets TPDF dither (±1 LSB). Samples are clamped to [-1, 1]."""
    x = np.asarray(x, dtype=np.float64)
    x = np.nan_to_num(x)
    if subtype == "PCM_16" and dither:
        rng = np.random.default_rng(12345)
        lsb = 1.0 / 32768.0
        x = x + (rng.random(x.shape) - rng.random(x.shape)) * lsb
    x = np.clip(x, -1.0, 1.0 - 1.0 / 32768.0)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sf.write(path, x.astype(np.float32), sr, subtype=subtype)
    return path


# --------------------------------------------------------------------------------------------
# gain / fades / pan


def gain_db(x, db):
    return _f32(np.asarray(x, dtype=np.float32) * float(db2lin(db)))


def _curve(p, shape):
    p = np.clip(p, 0.0, 1.0)
    if shape == "linear":
        return p
    if shape == "exp":  # perceptually even (fast at the start of a fade-in)
        return p * p
    if shape == "log":
        return np.sqrt(p)
    return np.sin(0.5 * np.pi * p)  # 'sine' = equal-power


def fade_in(x, seconds, shape="sine", sr=SR):
    x = np.array(x, dtype=np.float32, copy=True)
    n = min(len(x), int(round(seconds * sr)))
    if n > 0:
        g = _curve(np.arange(n) / n, shape).astype(np.float32)
        x[:n] *= g if x.ndim == 1 else g[:, None]
    return x


def fade_out(x, seconds, shape="sine", sr=SR):
    x = np.array(x, dtype=np.float32, copy=True)
    n = min(len(x), int(round(seconds * sr)))
    if n > 0:
        g = _curve(1.0 - (np.arange(n) + 1) / n, shape).astype(np.float32)
        x[len(x) - n:] *= g if x.ndim == 1 else g[:, None]
    return x


def fades(x, fin=0.005, fout=0.01, sr=SR, shape="sine"):
    return fade_out(fade_in(x, fin, shape, sr), fout, shape, sr)


def pan_gains(p):
    """Equal-power pan law normalised to unity at centre: p=-1 → (1.414, 0), 0 → (1, 1), +1 → (0, 1.414)."""
    p = float(np.clip(p, -1, 1))
    a = (p + 1.0) * np.pi / 4.0
    return math.cos(a) * math.sqrt(2.0), math.sin(a) * math.sqrt(2.0)


def pan(x, p):
    """Mono → equal-power panned stereo (centre = the mono signal on both sides).
    Stereo → balance (the far side is attenuated, the near side kept at unity)."""
    x = np.asarray(x, dtype=np.float32)
    p = float(np.clip(p, -1, 1))
    if x.ndim == 1:
        gl, gr = pan_gains(p)
        return _f32(np.stack([x * gl, x * gr], axis=1))
    gl = min(1.0, 1.0 - p)
    gr = min(1.0, 1.0 + p)
    return _f32(to_stereo(x) * np.array([gl, gr], dtype=np.float32))


def remove_dc(x, hz=12.0, sr=SR):
    """Remove DC / sub-sonic drift (mean subtraction + gentle 2nd-order high-pass)."""
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean(axis=0)
    sos = signal.butter(2, hz, "highpass", fs=sr, output="sos")
    return _f32(signal.sosfiltfilt(sos, x, axis=0))


def peak_normalize(x, peak_db=-3.0):
    x = np.asarray(x, dtype=np.float32)
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    return x if m <= 0 else _f32(x * (db2lin(peak_db) / m))


# --------------------------------------------------------------------------------------------
# filters (causal unless zero_phase=True)


def _apply_sos(sos, x, zero_phase=False):
    x = np.asarray(x, dtype=np.float64)
    y = signal.sosfiltfilt(sos, x, axis=0) if zero_phase else signal.sosfilt(sos, x, axis=0)
    return _f32(y)


def highpass(x, hz, order=2, sr=SR, zero_phase=False):
    return _apply_sos(signal.butter(order, hz, "highpass", fs=sr, output="sos"), x, zero_phase)


def lowpass(x, hz, order=2, sr=SR, zero_phase=False):
    hz = min(hz, sr * 0.49)
    return _apply_sos(signal.butter(order, hz, "lowpass", fs=sr, output="sos"), x, zero_phase)


def bandpass(x, lo, hi, order=2, sr=SR, zero_phase=False):
    return _apply_sos(signal.butter(order, [lo, min(hi, sr * 0.49)], "bandpass", fs=sr, output="sos"), x, zero_phase)


def _biquad(kind, f0, gain, q, sr):
    """RBJ audio-EQ-cookbook biquad → sos (1, 6)."""
    A = 10 ** (gain / 40.0)
    w0 = 2 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    if kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "lowshelf":
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
        a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
    elif kind == "highshelf":
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sa)]
        a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sa]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return np.concatenate([b, a])[None, :]


def peaking_eq(x, hz, gain, q=1.0, sr=SR):
    return _apply_sos(_biquad("peak", hz, gain, q, sr), x)


def low_shelf(x, hz, gain, q=0.707, sr=SR):
    return _apply_sos(_biquad("lowshelf", hz, gain, q, sr), x)


def high_shelf(x, hz, gain, q=0.707, sr=SR):
    return _apply_sos(_biquad("highshelf", hz, gain, q, sr), x)


def eq_chain(x, chain, sr=SR):
    """Apply a list of EQ steps: ('hp', hz[, order]) ('lp', hz[, order]) ('peak', hz, dB, q)
    ('ls', hz, dB) ('hs', hz, dB)."""
    for st in chain or []:
        k = st[0]
        if k == "hp":
            x = highpass(x, st[1], st[2] if len(st) > 2 else 2, sr)
        elif k == "lp":
            x = lowpass(x, st[1], st[2] if len(st) > 2 else 2, sr)
        elif k == "peak":
            x = peaking_eq(x, st[1], st[2], st[3] if len(st) > 3 else 1.0, sr)
        elif k == "ls":
            x = low_shelf(x, st[1], st[2], sr=sr)
        elif k == "hs":
            x = high_shelf(x, st[1], st[2], sr=sr)
        else:
            raise ValueError(st)
    return x


# --------------------------------------------------------------------------------------------
# reverb


@lru_cache(maxsize=16)
def make_reverb_ir(decay=2.4, predelay=0.02, damping=0.5, size=0.6, cross=0.3, seed=7, sr=SR, hp=70.0):
    """Synthetic true-stereo room/hall impulse response.

    decay    RT60 in seconds of the mid band (time for the tail to fall 60 dB)
    predelay seconds before the first reflection
    damping  0..1 — how much faster highs die than mids (0 = bright, 1 = very dark tail)
    size     0..1 — spreads early reflections and slows the diffuse build-up (small room .. cathedral)
    cross    0..1 — amount of L→R / R→L wet bleed (keeps panned sources from sounding one-sided)
    Returns float32 array (n, 2, 2): ir[:, in_ch, out_ch]; each output's total energy is 1.
    The four paths use independent noise, so the wet signal is decorrelated left/right (wide, diffuse).
    """
    rng = np.random.default_rng(seed)
    tail_len = min(decay * 1.3 + 0.05, 10.0)
    n_pre = int(predelay * sr)
    n = int(tail_len * sr)
    t = np.arange(n) / sr
    bands = [(None, 250.0), (250.0, 1200.0), (1200.0, 4500.0), (4500.0, None)]
    factors = [1.08, 1.0, 1.0 - 0.45 * damping, 1.0 - 0.78 * damping]
    build_tau = 0.004 + 0.035 * size
    er_win = 0.012 + 0.07 * size
    out = np.zeros((n_pre + n, 2, 2), dtype=np.float64)
    for i in range(2):
        for o in range(2):
            noise = rng.standard_normal(n)
            tail = np.zeros(n)
            for (lo, hi), f in zip(bands, factors):
                if lo is None:
                    sos = signal.butter(2, hi, "lowpass", fs=sr, output="sos")
                elif hi is None:
                    sos = signal.butter(2, lo, "highpass", fs=sr, output="sos")
                else:
                    sos = signal.butter(2, [lo, hi], "bandpass", fs=sr, output="sos")
                rt = max(0.06, decay * f)
                tail += signal.sosfiltfilt(sos, noise) * 10.0 ** (-3.0 * t / rt)
            tail *= 1.0 - np.exp(-t / build_tau)
            tail *= np.clip(t / (er_win * 0.6), 0, 1) ** 0.5 * 0.85 + 0.15  # diffuse field grows in
            # early reflections: sparse signed taps whose density grows with time
            n_taps = int(8 + 18 * size)
            er = np.zeros(n)
            times = np.sort(rng.random(n_taps) ** 1.6) * er_win
            for k, tt in enumerate(times):
                idx = int(tt * sr)
                if idx < n:
                    er[idx] += rng.choice([-1.0, 1.0]) * (0.55 + 0.45 * rng.random()) * math.exp(-tt / (er_win * 0.9))
            er = signal.sosfilt(signal.butter(1, 6500 - 3000 * damping, "lowpass", fs=sr, output="sos"), er)
            tail = tail / (np.sqrt(np.sum(tail ** 2)) + 1e-12)
            er = er / (np.sqrt(np.sum(er ** 2)) + 1e-12)
            er_share = 0.30 - 0.18 * size
            path = np.sqrt(1 - er_share) * tail + np.sqrt(er_share) * er
            # the cross paths start a hair later and skip the first reflections (more spacious)
            if i != o:
                path = np.sqrt(1 - er_share) * tail * np.clip(t / 0.01, 0, 1)
            out[n_pre:, i, o] = path
    # global tone: remove mud below hp, gentle top roll-off
    sos_hp = signal.butter(2, hp, "highpass", fs=sr, output="sos")
    sos_lp = signal.butter(2, 11000 - 5000 * damping, "lowpass", fs=sr, output="sos")
    for i in range(2):
        for o in range(2):
            out[:, i, o] = signal.sosfilt(sos_lp, signal.sosfilt(sos_hp, out[:, i, o]))
    # energy: direct path 1, cross path `cross`, normalised so each output has unit energy
    for o in range(2):
        for i in range(2):
            e = np.sqrt(np.sum(out[:, i, o] ** 2)) + 1e-12
            out[:, i, o] *= (1.0 if i == o else cross) / e
        tot = np.sqrt(np.sum(out[:, :, o] ** 2))
        out[:, :, o] /= tot
    # tiny end fade so the IR never stops abruptly
    nf = int(0.05 * sr)
    out[-nf:] *= np.linspace(1, 0, nf)[:, None, None]
    return out.astype(np.float32)


def reverb_wet(x, decay=2.4, predelay=0.02, damping=0.5, size=0.6, cross=0.3, width=1.0, seed=7, sr=SR):
    """Wet-only stereo reverb signal (length = len(x) + IR length). For noise-like input its RMS ≈ input RMS."""
    xs = to_stereo(x).astype(np.float32)
    ir = make_reverb_ir(round(float(decay), 3), round(float(predelay), 4), round(float(damping), 3),
                        round(float(size), 3), round(float(cross), 3), int(seed), int(sr))
    n = len(xs) + len(ir) - 1
    y = np.zeros((n, 2))
    for i in range(2):
        if not np.any(xs[:, i]):
            continue
        xi = np.ascontiguousarray(xs[:, i])
        for o in range(2):
            # float32 FFT convolution: ~2x faster, error floor far below -100 dB
            y[:, o] += signal.oaconvolve(xi, np.ascontiguousarray(ir[:, i, o]))
    if width != 1.0:
        m = 0.5 * (y[:, 0] + y[:, 1])
        s = 0.5 * (y[:, 0] - y[:, 1]) * width
        y = np.stack([m + s, m - s], axis=1)
    return _f32(y)


def reverb(x, wet=0.25, dry=1.0, keep_tail=True, **kw):
    """dry·x + wet·reverb_wet(x). keep_tail=True extends the output by the reverb tail."""
    xs = to_stereo(x)
    w = reverb_wet(xs, **kw)
    if not keep_tail:
        w = w[: len(xs)]
    out = w * wet
    out[: len(xs)] += xs * dry
    return _f32(out)


# --------------------------------------------------------------------------------------------
# dynamics


def _envelope_db(x, hop, sr, win=None):
    """RMS level per hop (stereo-linked) in dBFS, centred windows."""
    m = np.asarray(x, dtype=np.float64)
    m = (m ** 2).mean(axis=1) if m.ndim == 2 else m ** 2
    win = win or hop * 2
    k = np.ones(win) / win
    ms = np.convolve(m, k, mode="same")[::hop]
    return 10 * np.log10(ms + 1e-12)


def _smooth_gain(target_db, att_coef, rel_coef):
    """One-pole smoothing of a gain curve in dB: falling (more reduction) uses attack, rising uses release."""
    out = np.empty_like(target_db)
    g = 0.0
    for i, tg in enumerate(target_db):
        c = att_coef if tg < g else rel_coef
        g = tg + (g - tg) * c
        out[i] = g
    return out


def compress(x, threshold_db=-18.0, ratio=3.0, attack=0.01, release=0.15, knee_db=6.0, makeup_db=0.0,
             sidechain=None, sr=SR):
    """Soft-knee feed-forward RMS compressor (stereo-linked). `sidechain` (optional) drives the detector."""
    x = np.asarray(x, dtype=np.float32)
    det = x if sidechain is None else np.asarray(sidechain, dtype=np.float32)
    hop = 32
    lev = _envelope_db(det, hop, sr, win=int(0.01 * sr))
    over = lev - threshold_db
    gr = np.where(2 * over < -knee_db, 0.0,
                  np.where(2 * np.abs(over) <= knee_db, (1 / ratio - 1) * (over + knee_db / 2) ** 2 / (2 * max(knee_db, 1e-6)),
                           (1 / ratio - 1) * over))
    hop_t = hop / sr
    g = _smooth_gain(gr, math.exp(-hop_t / max(attack, 1e-4)), math.exp(-hop_t / max(release, 1e-4)))
    gs = np.interp(np.arange(len(x)), np.arange(len(g)) * hop, g)
    gl = db2lin(gs + makeup_db).astype(np.float32)
    return _f32(x * (gl if x.ndim == 1 else gl[:, None]))


def duck(music, voice, depth_db=-9.0, attack=0.08, release=0.5, threshold_db=-45.0, hold=0.25,
         lookahead=None, knee_db=8.0, sr=SR, return_gain=False):
    """Side-chain ducking: lower `music` by up to `depth_db` while `voice` is present.

    voice      mono or stereo array (any length; aligned to music sample 0) — e.g. the dialogue stem
    attack     seconds to reach the ducked level;  release: seconds to come back up
    hold       keep ducked through gaps shorter than this (avoids pumping between words)
    lookahead  start ducking this early (default = attack, so music is fully down at the first syllable)
    threshold_db / knee_db: voice RMS (dBFS) where ducking starts / is complete (threshold + knee)
    """
    music = to_stereo(music)
    v = to_mono(voice)
    if len(v) < len(music):
        v = np.concatenate([v, np.zeros(len(music) - len(v), dtype=np.float32)])
    v = v[: len(music)]
    hop = int(0.005 * sr)
    lev = _envelope_db(v, hop, sr, win=int(0.03 * sr))
    amt = np.clip((lev - threshold_db) / knee_db, 0.0, 1.0)
    hold_n = max(1, int(hold * sr / hop / 2))
    from scipy.ndimage import maximum_filter1d
    amt = maximum_filter1d(amt, size=2 * hold_n + 1, mode="nearest")  # centred → shift so it only holds forward
    amt = np.concatenate([np.full(hold_n, amt[0]), amt[:-hold_n]]) if len(amt) > hold_n else amt
    target = depth_db * amt
    la = attack if lookahead is None else lookahead
    shift = int(la * sr / hop)
    if shift > 0:
        target = np.concatenate([target[shift:], np.full(shift, target[-1] if len(target) else 0.0)])
    hop_t = hop / sr
    g = _smooth_gain(target, math.exp(-hop_t / max(attack / 3, 1e-4)), math.exp(-hop_t / max(release / 3, 1e-4)))
    gs = np.interp(np.arange(len(music)), np.arange(len(g)) * hop, g)
    out = _f32(music * db2lin(gs).astype(np.float32)[:, None])
    return (out, gs) if return_gain else out


# --------------------------------------------------------------------------------------------
# placement / sfx events


def place(track, clip, at_seconds, gain_db=0.0, pan=0.0, sr=SR):
    """Add `clip` into `track` starting at `at_seconds` (may be negative: the head is cut).
    Mono clips are equal-power panned; stereo clips are balanced. The track grows if needed.
    Returns the (possibly new) track array — always use the return value."""
    track = to_stereo(track) if track is not None else silence(0, sr)
    c = globals()["pan"](clip, pan) if (np.asarray(clip).ndim == 1 or pan != 0) else to_stereo(clip)
    c = c * float(db2lin(gain_db))
    start = int(round(at_seconds * sr))
    if start < 0:
        c = c[-start:]
        start = 0
    end = start + len(c)
    if end > len(track):
        track = np.concatenate([track, np.zeros((end - len(track), 2), dtype=np.float32)])
    track[start:end] += c
    return track


def change_rate(x, rate):
    """Varispeed (pitch+tempo) by resampling: rate 1.2 = 20% faster & higher."""
    if abs(rate - 1.0) < 1e-4:
        return x
    fr = Fraction(rate).limit_denominator(200)
    return _f32(signal.resample_poly(np.asarray(x, dtype=np.float64), fr.denominator, fr.numerator, axis=0))


def render_sfx_events(events, duration, sfx_dir=None, sr=SR):
    """Render a list of SFX events (format of data/sfx_events.json from tools/collect_sfx.mjs):
       {name, at, until|null, gain (dB), loop (bool), pan (-1..1), fade (s), rate}
    Looped sounds repeat (with a short crossfade) until `until`; any sound cut by `until` fades out over `fade`.
    Returns a stereo track of `duration` seconds."""
    sfx_dir = sfx_dir or os.path.join(ROOT, "audio", "sfx")
    track = silence(duration, sr)
    cache = {}
    for e in events:
        name = e["name"]
        if name not in cache:
            p = os.path.join(sfx_dir, name + ".wav")
            if not os.path.exists(p):
                print(f"[render_sfx_events] missing {p}", file=sys.stderr)
                cache[name] = None
                continue
            cache[name] = load(p, sr)
        clip = cache[name]
        if clip is None:
            continue
        clip = change_rate(clip, e.get("rate", 1) or 1)
        at = float(e["at"])
        until = e.get("until")
        fade = float(e.get("fade", 0.3) or 0.0)
        if e.get("loop") and until is not None:
            need = int((float(until) - at) * sr) + 1
            body = clip.copy()
            typ = float(np.median(np.abs(np.diff(body[: min(len(body), 4000)], axis=0)))) if len(body) > 2 else 0.0
            seamless = float(np.max(np.abs(body[0] - body[-1]))) <= 3.0 * typ + 1e-4
            if seamless:  # files rendered as exact loops (alarm_bell, heartbeat): butt-join
                reps = int(math.ceil(need / len(body)))
                out = np.concatenate([body] * max(1, reps))
            else:  # anything else: 40 ms equal-gain crossfade at each repeat
                xf = min(int(0.04 * sr), len(clip) // 4)
                out = body.copy()
                ramp = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
                while len(out) < need:
                    head = out[:-xf] if xf else out
                    joint = out[-xf:] * (1 - ramp) + body[:xf] * ramp if xf else np.zeros((0, 2), np.float32)
                    out = np.concatenate([head, joint, body[xf:]])
            clip = fade_in(out[:need], 0.006, sr=sr)
            clip = fade_out(clip, max(fade, 0.02), sr=sr)
        elif until is not None:
            need = int((float(until) - at) * sr)
            if 0 < need < len(clip):
                clip = fade_out(clip[:need], max(fade, 0.02), sr=sr)
        track = place(track, clip, at, e.get("gain", 0) or 0, e.get("pan", 0) or 0, sr)
    return track[: int(round(duration * sr))]


# --------------------------------------------------------------------------------------------
# loudness (ITU-R BS.1770-4 / EBU R128) and true-peak limiting


def _k_weighting_sos(sr):
    # libebur128 formulation (exactly reproduces the BS.1770 48 kHz coefficients at any rate)
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / sr)
    Vh = 10 ** (G / 20.0)
    Vb = Vh ** 0.4996667741545416
    a0 = 1.0 + K / Q + K * K
    pb = [(Vh + Vb * K / Q + K * K) / a0, 2.0 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0]
    pa = [1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0]
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / sr)
    rb = [1.0, -2.0, 1.0]
    ra = [1.0, 2.0 * (K * K - 1.0) / (1.0 + K / Q + K * K), (1.0 - K / Q + K * K) / (1.0 + K / Q + K * K)]
    return np.array([pb + pa, rb + ra])


def loudness(x, sr=SR):
    """Integrated loudness in LUFS (BS.1770-4: K-weighting, 400 ms blocks / 75 % overlap,
    absolute gate -70 LUFS, relative gate -10 LU). Returns -inf for silence."""
    x = to_stereo(x)
    if len(x) < int(0.4 * sr):
        x = np.concatenate([x, np.zeros((int(0.4 * sr) - len(x), 2), np.float32)])
    sos = _k_weighting_sos(sr)
    # per channel on contiguous 1-D data (much faster than filtering/cumsumming along axis 0);
    # L and R have weight 1, so their K-weighted powers are simply summed
    p = np.zeros(len(x))
    for c in range(2):
        yc = signal.sosfilt(sos, np.ascontiguousarray(x[:, c], dtype=np.float64))
        p += yc * yc
    blk, step = int(0.4 * sr), int(0.1 * sr)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, len(p) - blk + 1, step)
    zs = (cs[starts + blk] - cs[starts]) / blk  # (nblocks,) channel-summed mean square
    lj = -0.691 + 10 * np.log10(zs + 1e-20)
    g1 = lj > -70.0
    if not np.any(g1):
        return float("-inf")
    rel = -0.691 + 10 * np.log10(zs[g1].mean()) - 10.0
    g2 = g1 & (lj > rel)
    return float(-0.691 + 10 * np.log10(zs[g2].mean()))


def normalize_loudness(x, target_lufs=-16.0, sr=SR):
    L = loudness(x, sr)
    if not np.isfinite(L):
        return _f32(x)
    return gain_db(x, target_lufs - L)


def _tp_envelope(x, ref, oversample=4, margin_db=6.0, blk=8192):
    """Per-sample true-peak magnitude (max over channels and `oversample` interpolated phases).

    Only blocks whose *sample* peak comes within `margin_db` of `ref` are oversampled — inter-sample
    overs on real audio stay well under +6 dB, so everything else cannot reach `ref`; elsewhere the
    sample peak is returned. Quiet material (most of a film score) is then metered/limited several
    times faster; a loud, dense mix costs about as much as full oversampling."""
    xs = np.asarray(x, dtype=np.float64)
    xa = _absmax_ch(xs)
    pk = xa.copy()
    n = len(xa)
    if n == 0 or ref <= 0:
        return pk
    thr = ref * 10 ** (-margin_db / 20.0)
    starts = np.arange(0, n, blk)
    cand = np.nonzero(np.maximum.reduceat(xa, starts) > thr)[0]
    if len(cand) == 0:
        return pk
    # merge consecutive candidate blocks into runs (≤ 64 blocks each) and oversample each run once
    runs, r0, prev = [], cand[0], cand[0]
    for b in cand[1:]:
        if b != prev + 1 or b - r0 >= 64:
            runs.append((r0, prev))
            r0 = b
        prev = b
    runs.append((r0, prev))
    pad = 64
    for b0, b1 in runs:
        a0, a1 = b0 * blk, min(n, (b1 + 1) * blk)
        s0, s1 = max(0, a0 - pad), min(n, a1 + pad)
        up = _absmax_ch(signal.resample_poly(xs[s0:s1], oversample, 1, axis=0))
        ph = up[: (s1 - s0) * oversample].reshape(s1 - s0, oversample)
        u = ph[:, 0].copy()
        for k in range(1, oversample):  # (np.maximum on columns: far faster than .max(axis=1))
            np.maximum(u, ph[:, k], out=u)
        pk[a0:a1] = np.maximum(pk[a0:a1], u[a0 - s0: a1 - s0])
    return pk


def _absmax_ch(x):
    """max(|x|) across channels per sample (1-D in → |x|)."""
    if x.ndim == 1:
        return np.abs(x)
    out = np.abs(x[:, 0])
    for c in range(1, x.shape[1]):
        np.maximum(out, np.abs(x[:, c]), out=out)
    return out


def true_peak(x, sr=SR, oversample=4):
    """Estimated true peak in dBTP (4x polyphase oversampling, BS.1770 Annex 2 style)."""
    xs = np.asarray(x, dtype=np.float64)
    if xs.size == 0:
        return -200.0
    ref = float(np.max(np.abs(xs)))
    return float(lin2db(_tp_envelope(xs, ref, oversample).max()))


def limit(x, ceiling_db=-1.0, lookahead=0.005, release=0.08, sr=SR, oversample=4):
    """Look-ahead brick-wall limiter with true-peak detection. Gain is smooth (no clicks):
    required gain → sliding min over the look-ahead window → moving average (reaches the target
    exactly at the peak) → exponential release of the gain-reduction depth. Output true peak ≤ ceiling
    (verified, re-run if needed)."""
    x = to_stereo(x).astype(np.float64)
    ceil = float(db2lin(ceiling_db))
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    for _ in range(4):
        pk = _tp_envelope(x, ceil, oversample)
        req = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
        if req.min() >= 1.0:
            break
        L = max(1, int(lookahead * sr))
        # centred min over ±L, then centred mean over L+1: the result never exceeds `req`
        # and ramps down smoothly over ~L samples before each peak.
        m = minimum_filter1d(req, size=2 * L + 1, mode="nearest")
        a = np.minimum(uniform_filter1d(m, size=L + 1, mode="nearest"), req)
        # release, block-wise and vectorised: depth d_i = max_j r_j·rc^(i-j)  (peak hold + exponential
        # decay of the gain reduction), computed in the log domain with a running maximum.
        blk = 16
        nb = int(math.ceil(len(a) / blk))
        pad = np.concatenate([a, np.full(nb * blk - len(a), 1.0)])
        r = 1.0 - pad.reshape(nb, blk).min(axis=1)
        lrc = -blk / (release * sr)
        j = np.arange(nb, dtype=np.float64)
        with np.errstate(divide="ignore"):
            lr = np.log(np.maximum(r, 0.0))
        d = np.exp(np.maximum.accumulate(lr - j * lrc) + j * lrc)
        out = 1.0 - d
        gs = np.interp(np.arange(len(a)), np.arange(nb) * blk + blk / 2, out)
        gs = np.minimum(gs, a)
        x = x * gs[:, None]
    return _f32(x)


def master(x, target_lufs=-16.0, ceiling_db=-1.0, sr=SR):
    """Loudness-normalise, true-peak limit, then re-trim (≤ 2 passes) so the limited result really
    lands on `target_lufs` (limiting otherwise leaves it a few tenths of a dB short)."""
    y = normalize_loudness(x, target_lufs, sr)
    out = limit(y, ceiling_db, sr=sr)
    for _ in range(2):
        L = loudness(out, sr)
        if not np.isfinite(L) or abs(L - target_lufs) < 0.05:
            break
        y = gain_db(y, target_lufs - L)
        out = limit(y, ceiling_db, sr=sr)
    return out


# --------------------------------------------------------------------------------------------
# analysis


def analyze(x, sr=SR):
    """Dict of health metrics: peak dBFS, true-peak dBTP, RMS dBFS, LUFS, DC offset, NaN count,
    largest sample-to-sample jump (relative to a 2-pole-smoothed prediction → click detector)."""
    xs = to_stereo(x).astype(np.float64)
    nan = int(np.sum(~np.isfinite(xs)))
    xs = np.nan_to_num(xs)
    d = np.diff(xs, axis=0)
    # click detector: second difference compared with local signal slope scale
    dd = _absmax_ch(np.diff(xs, n=2, axis=0)) if len(xs) > 3 else np.zeros(1)
    loc = np.convolve(_absmax_ch(d), np.ones(64) / 64, mode="same")[1:] if len(d) > 64 else np.ones_like(dd)
    ratio = dd / (loc[: len(dd)] + 1e-4)
    return {
        "seconds": round(len(xs) / sr, 3),
        "peak_db": round(float(lin2db(np.abs(xs).max() if len(xs) else 0)), 2),
        "true_peak_db": round(true_peak(xs, sr), 2) if len(xs) else -200,
        "rms_db": round(float(lin2db(np.sqrt(np.mean(xs ** 2)) if len(xs) else 0)), 2),
        "lufs": round(loudness(xs, sr), 2),
        "dc": round(float(np.abs(xs.mean(axis=0)).max()), 6),
        "nan": nan,
        "max_jump": round(float(np.abs(d).max()) if len(d) else 0, 4),
        "click_score": round(float(ratio.max()) if len(ratio) else 0, 1),
        "start_abs": round(float(np.abs(xs[0]).max()) if len(xs) else 0, 5),
        "end_abs": round(float(np.abs(xs[-1]).max()) if len(xs) else 0, 5),
    }


def _colormap(v):
    """v in 0..1 → RGB (dark violet → magenta → orange → pale yellow), smooth."""
    stops = np.array([[0.0, 4, 3, 12], [0.25, 50, 18, 90], [0.5, 150, 40, 120], [0.75, 240, 120, 60], [1.0, 255, 245, 190]])
    r = np.interp(v, stops[:, 0], stops[:, 1])
    g = np.interp(v, stops[:, 0], stops[:, 2])
    b = np.interp(v, stops[:, 0], stops[:, 3])
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


def spectrogram_png(x, path, sr=SR, max_hz=8000, width=1400, height=420, db_range=80, log_freq=True,
                    title=None, marks=None, env=True):
    """Spectrogram (+ RMS envelope strip) as a PNG using numpy + PIL. `marks` = [(sec, label), ...]."""
    from PIL import Image, ImageDraw
    m = to_mono(x).astype(np.float64)
    n = len(m)
    nfft = 2048 if n / sr > 6 else 1024
    hop = max(64, int(n / width))
    win = np.hanning(nfft)
    pad = np.concatenate([np.zeros(nfft // 2), m, np.zeros(nfft)])
    cols = []
    for i in range(width):
        s = i * hop
        if s + nfft > len(pad):
            break
        seg = pad[s: s + nfft] * win
        cols.append(np.abs(np.fft.rfft(seg)) + 1e-9)
    S = 20 * np.log10(np.array(cols).T + 1e-12)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    fmin = 30.0
    if log_freq:
        ys = np.geomspace(fmin, max_hz, height)
    else:
        ys = np.linspace(0, max_hz, height)
    idx = np.clip(np.searchsorted(freqs, ys), 0, len(freqs) - 1)
    img = S[idx][::-1]
    top = img.max()
    v = np.clip((img - (top - db_range)) / db_range, 0, 1)
    rgb = _colormap(v)
    env_h = 80 if env else 0
    H = height + env_h + 22
    canvas = Image.new("RGB", (rgb.shape[1], H), (12, 10, 20))
    canvas.paste(Image.fromarray(rgb), (0, 22))
    d = ImageDraw.Draw(canvas)
    # frequency grid
    for f in [100, 250, 500, 1000, 2000, 4000, 8000, 16000]:
        if f > max_hz or f < fmin:
            continue
        yy = 22 + (height - 1 - int(np.searchsorted(ys, f)))
        d.line([(0, yy), (rgb.shape[1], yy)], fill=(90, 90, 120))
        d.text((3, yy - 11), f"{f}Hz" if f < 1000 else f"{f // 1000}k", fill=(200, 200, 230))
    secs = n / sr
    step = 1 if secs <= 12 else 5 if secs <= 60 else 10 if secs <= 200 else 20
    for s in np.arange(0, secs, step):
        xx = int(s * sr / hop)
        d.line([(xx, 22 + height), (xx, H)], fill=(70, 70, 90))
        d.text((xx + 2, 22 + height + 2), f"{s:g}s", fill=(180, 180, 200))
    if env:
        st = to_stereo(x).astype(np.float64)
        e = []
        for i in range(rgb.shape[1]):
            seg = st[i * hop: i * hop + hop]
            e.append(np.sqrt(np.mean(seg ** 2)) if len(seg) else 0)
        e = lin2db(np.array(e))
        pk = []
        for i in range(rgb.shape[1]):
            seg = st[i * hop: i * hop + hop]
            pk.append(np.abs(seg).max() if len(seg) else 0)
        pk = lin2db(np.array(pk))
        y0 = 22 + height
        def ymap(db):
            return y0 + env_h - 2 - int(np.clip((db + 60) / 60, 0, 1) * (env_h - 18))
        for i in range(1, len(e)):
            d.line([(i - 1, ymap(pk[i - 1])), (i, ymap(pk[i]))], fill=(110, 160, 255))
            d.line([(i - 1, ymap(e[i - 1])), (i, ymap(e[i]))], fill=(255, 210, 90))
        d.text((rgb.shape[1] - 230, y0 + 14), "rms(yellow) peak(blue) -60..0 dB", fill=(200, 200, 200))
    for (sec, lab) in marks or []:
        xx = int(sec * sr / hop)
        d.line([(xx, 22), (xx, 22 + height)], fill=(120, 255, 200))
        d.text((xx + 3, 24), str(lab), fill=(160, 255, 220))
    d.text((4, 4), title or os.path.basename(path), fill=(235, 235, 245))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    canvas.save(path)
    return path


# --------------------------------------------------------------------------------------------
# film mix

# recommended event gains (dB) for a dialogue stem at -18 LUFS (files in audio/sfx peak at -3 dBFS);
# used by sfx_events_from_timeline. Scene sfx entries should start from these values.
SFX_GAIN = {
    "alarm_bell": -18, "alarm_pull": -6, "footsteps": -9, "door_whoosh": -13, "crowd_murmur": -14,
    "heartbeat": -12, "breath_shaky": -13, "sob": -12, "cage_close": -5, "lock_click": -10, "cage_creak": -12,
    "key_turn": -9, "rumble_low": -14, "shimmer": -15, "twinkle": -18, "console_beeps": -24,
    "paper_rustle": -12, "lamp_click": -8, "cloth_rustle": -15, "rust_creak": -17,
}


def _timeline_lines(tl):
    beats = tl.get("beats", {})
    recs = beats.items() if isinstance(beats, dict) else [(b[0], b[1]) if isinstance(b, list) else (b.get("id"), b) for b in beats]
    return [(bid, r) for bid, r in recs if r.get("kind") == "line" and r.get("audio")]


def sfx_events_from_timeline(tl, offset=0.15):
    """Fallback SFX events from the screenplay's per-beat `sfx` lists (beat start + offset, recommended gains)."""
    beats = tl.get("beats", {})
    recs = beats.values() if isinstance(beats, dict) else [b[1] if isinstance(b, list) else b for b in beats]
    ev = []
    for r in recs:
        for nm in r.get("sfx", []) or []:
            ev.append({"name": nm, "at": float(r["start"]) + offset, "until": None, "gain": SFX_GAIN.get(nm, -12),
                       "loop": False, "pan": 0, "fade": 0.3, "rate": 1})
    return sorted(ev, key=lambda e: e["at"])


def mix_film(timeline="data/timeline.json", music=None, sfx_events=None, out="out/mix.wav", duration=None,
             voice_lufs=-18.0, music_lufs=-25.0, duck_db=-8.0, sfx_db=0.0, master_lufs=-16.0, ceiling_db=-1.0,
             verbose=True):
    """Dialogue + music + SFX → mastered stereo wav.

    timeline   data/timeline.json (beats of kind 'line' with 'audio' paths are placed at their 'start')
    music      wav from audio/music.py (normalised to `music_lufs`, then ducked under the dialogue by `duck_db`)
    sfx_events list or path (data/sfx_events.json from tools/collect_sfx.mjs); None → derived from the
               timeline's per-beat sfx lists with SFX_GAIN; [] → no SFX
    The sum is loudness-normalised to `master_lufs` and true-peak limited to `ceiling_db`."""
    rp = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    tl = json.load(open(rp(timeline)))
    dur = float(duration or tl["duration"])
    n = int(round(dur * SR))
    voice = silence(dur)
    for bid, r in _timeline_lines(tl):
        p = rp(r["audio"])
        if os.path.exists(p):
            voice = place(voice, load(p), float(r["start"]), 0.0, 0.0)
    voice = voice[:n]
    voice = normalize_loudness(voice, voice_lufs)
    mixbuf = voice.astype(np.float64).copy()
    stems = {"voice": voice}
    if music:
        m = load(rp(music))
        m = np.concatenate([m, np.zeros((max(0, n - len(m)), 2), np.float32)])[:n]
        m = normalize_loudness(m, music_lufs)
        m = duck(m, voice, depth_db=duck_db)
        mixbuf += m
        stems["music"] = m
    if sfx_events is None:
        ev = sfx_events_from_timeline(tl)
    elif isinstance(sfx_events, str):
        ev = json.load(open(rp(sfx_events)))
    else:
        ev = sfx_events
    if ev:
        s = gain_db(render_sfx_events(ev, dur), sfx_db)
        mixbuf += s
        stems["sfx"] = s
    y = master(mixbuf, master_lufs, ceiling_db)
    save(rp(out), y)
    if verbose:
        for k, v in stems.items():
            print(f"  {k:6s} LUFS {loudness(v):6.1f}  peak {lin2db(np.abs(v).max()):6.1f} dBFS", file=sys.stderr)
        print(f"  mix    {json.dumps(analyze(y))}", file=sys.stderr)
    return y


# --------------------------------------------------------------------------------------------
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("check", "spectro", "mix"):
        print(__doc__)
        sys.exit(0)
    if a[0] == "mix":
        import argparse
        ap = argparse.ArgumentParser(prog="audiolib.py mix")
        ap.add_argument("--timeline", default="data/timeline.json")
        ap.add_argument("--music", default=None)
        ap.add_argument("--sfx", default=None, help="sfx events json; 'none' for no SFX; default: from timeline")
        ap.add_argument("--out", default="out/mix.wav")
        ap.add_argument("--voice-lufs", type=float, default=-18.0)
        ap.add_argument("--music-lufs", type=float, default=-25.0)
        ap.add_argument("--duck", type=float, default=-8.0)
        ap.add_argument("--sfx-db", type=float, default=0.0)
        ap.add_argument("--lufs", type=float, default=-16.0)
        o = ap.parse_args(a[1:])
        sfx = [] if o.sfx == "none" else o.sfx
        mix_film(o.timeline, o.music, sfx, o.out, None, o.voice_lufs, o.music_lufs, o.duck, o.sfx_db, o.lufs)
        print(o.out)
    elif a[0] == "check":
        for p in a[1:]:
            print(os.path.basename(p), json.dumps(analyze(load(p))))
    else:
        x = load(a[1])
        mh = 8000
        if "--max-hz" in a:
            mh = float(a[a.index("--max-hz") + 1])
        if "--seconds" in a:
            s0, s1 = [float(v) for v in a[a.index("--seconds") + 1].split(":")]
            x = x[int(s0 * SR): int(s1 * SR)]
        spectrogram_png(x, a[2], max_hz=mh)
        print(a[2])
