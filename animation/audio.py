"""Builds the soundtrack for both parts: voices, the song, the storm, the mix.

    python3 audio.py            # writes build/partN.wav and build/timeline_partN.json

Everything is synthesized here from scratch (the song is an original melody,
sung wordlessly by a formant-synthesis voice); the speaking voices come from
Piper TTS models in ./voices (see README.md).
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

import script as S

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
VOICE_DIR = os.environ.get("PIPER_VOICES", os.path.join(HERE, "voices"))
rng = np.random.default_rng(7)


# ----------------------------------------------------------------- helpers

def secs(n):
    return int(round(n * SR))


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def butter(x, kind, freq, order=2):
    sos = signal.butter(order, freq, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def ramp(t, t0, t1, v0=0.0, v1=1.0):
    """Linear ramp from v0 at t0 to v1 at t1, clamped (t can be an array)."""
    u = np.clip((t - t0) / max(t1 - t0, 1e-9), 0, 1)
    return v0 + (v1 - v0) * u


def smoothstep(t, t0, t1):
    u = np.clip((t - t0) / max(t1 - t0, 1e-9), 0, 1)
    return u * u * (3 - 2 * u)


def make_ir(length, decay, bright=0.5, seed=1):
    r = np.random.default_rng(seed)
    n = secs(length)
    t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-6.9 * t / decay)[:, None]
    # darker tail: low-pass progressively by mixing with a filtered copy
    dark = butter(ir, "low", 2500 + 6000 * bright)
    mix = np.clip(t / decay, 0, 1)[:, None]
    ir = ir * (1 - mix) + dark * mix
    ir[: secs(0.008)] *= np.linspace(0, 1, secs(0.008))[:, None]
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, length=2.5, decay=2.2, wet=0.3, bright=0.5, seed=1):
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    ir = make_ir(length, decay, bright, seed)
    w = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return x * (1 - wet) + w * wet * 0.6


def pan(mono, p):
    """p in [-1, 1]; constant power."""
    a = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)], axis=1)


def add(bus, clip, t0):
    i0 = secs(t0)
    if i0 >= len(bus):
        return
    if i0 < 0:
        clip = clip[-i0:]
        i0 = 0
    n = min(len(clip), len(bus) - i0)
    if clip.ndim == 1:
        bus[i0:i0 + n] += clip[:n, None]
    else:
        bus[i0:i0 + n] += clip[:n]


def rms(x):
    return float(np.sqrt(np.mean(x ** 2) + 1e-12))


# ----------------------------------------------------------------- voices

def tts(speaker, text, spk_id=None):
    cfg = S.VOICES[speaker]
    key = hashlib.sha1(json.dumps([cfg, text, spk_id]).encode()).hexdigest()[:16]
    path = os.path.join(BUILD, "voices", f"{speaker}_{key}.wav")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cmd = [sys.executable, "-m", "piper", "-m", os.path.join(VOICE_DIR, cfg["model"] + ".onnx"),
               "-f", path, "--length-scale", str(cfg["length"]),
               "--noise-scale", str(cfg["noise"]), "--noise-w-scale", str(cfg["noise_w"])]
        if spk_id is not None:
            cmd += ["-s", str(S.WHISPER_SPEAKERS[spk_id])]
        subprocess.run(cmd, input=text.encode(), check=True, capture_output=True)
    x, sr = sf.read(path, dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = signal.resample_poly(x, SR, sr)
    # trim leading/trailing silence
    a = np.abs(x)
    idx = np.where(a > 0.02 * a.max())[0]
    x = x[max(idx[0] - secs(0.03), 0): idx[-1] + secs(0.12)]
    return x / (rms(x) + 1e-9) * 0.1


def whisperize(x, seed):
    """Keep the spectral envelope, scramble the phase -> breathy whisper."""
    f, t, Z = signal.stft(x, SR, nperseg=1024)
    r = np.random.default_rng(seed)
    ph = np.exp(1j * r.uniform(0, 2 * np.pi, Z.shape))
    _, w = signal.istft(np.abs(Z) * ph, SR, nperseg=1024)
    w = w[: len(x)]
    # a little of the voiced original, pitched down, so words stay clear
    low = signal.resample_poly(x, 100, 92)[: len(x)]
    low = np.pad(low, (0, len(x) - len(low)))
    y = 0.75 * butter(w, "high", 400) + 0.4 * low
    return y / (rms(y) + 1e-9) * 0.1


def voice_fx(x, fx, seed):
    if fx == "inner":
        x = butter(x, "high", 90)
        out = reverb(x, 0.9, 0.7, wet=0.18, bright=0.4, seed=seed)
    elif fx == "room":
        x = butter(x, "high", 110)
        out = reverb(x, 1.2, 0.9, wet=0.22, seed=seed)
    elif fx == "warm":
        x = butter(x, "high", 70)
        x = x + 0.35 * butter(x, "low", 300)
        out = reverb(x, 2.6, 2.2, wet=0.26, bright=0.35, seed=seed)
    elif fx == "whisper":
        x = whisperize(x, seed)
        x = np.concatenate([x, np.zeros(secs(2.5))])
        p = [-0.7, 0.6, -0.35, 0.8, -0.85, 0.3, -0.5, 0.7][seed % 8]
        st = pan(x, p)
        # a fainter second voice repeating it from the other side
        echo = np.zeros_like(st)
        d = secs(0.23)
        echo[d:] = pan(x, -p * 0.8)[:-d] * 0.45
        out = reverb(st + echo, 3.0, 2.6, wet=0.45, bright=0.3, seed=seed)
    else:
        out = np.stack([x, x], axis=1)
    return out


# ----------------------------------------------------------------- the song

# 8 bars: (midi, beats) — an original melody over F G Em Am F G Em G
MELODY = [
    [(69, 1), (72, 1), (76, 2)],
    [(74, 1.5), (72, .5), (71, 1), (67, 1)],
    [(71, 1), (72, 1), (74, 1), (76, 1)],
    [(72, 3), (69, 1)],
    [(69, 1), (72, 1), (77, 2)],
    [(76, 1.5), (74, .5), (74, 1), (79, 1)],
    [(79, 1), (76, 1), (74, 1), (72, 1)],
    [(74, 2), (76, 2)],
]
VOWELS = ["a", "a", "o", "a", "a", "e", "o", "u"]  # a vowel colour per bar
CHORDS = {
    "F": (41, [53, 57, 60, 65]), "G": (43, [55, 59, 62, 67]),
    "Em": (40, [52, 55, 59, 64]), "Am": (45, [57, 60, 64, 69]),
    "C": (36, [48, 55, 60, 64]),
}
PROG = ["F", "G", "Em", "Am", "F", "G", "Em", "G"]
ENDING_MELODY = [[(69, 1), (72, 1), (77, 2)], [(76, 2), (74, 2)], [(72, 4)], [(72, 4)]]
ENDING_PROG = ["F", "G", "C", "C"]


def melody_notes(start, loops, ending=False):
    """-> list of (t0, dur, midi, vowel)"""
    notes, t = [], start
    bars = MELODY * loops
    vowels = VOWELS * loops
    if ending:
        bars = bars + ENDING_MELODY
        vowels = vowels + ["a", "o", "a", "u"]
    for bi, (bar, v) in enumerate(zip(bars, vowels)):
        for k, (m, b) in enumerate(bar):
            d = b * S.BEAT
            if k == len(bar) - 1 and bi % 4 == 3:
                d -= 0.4 * S.BEAT  # breathe at the end of each 4-bar phrase
            notes.append((t, d, m, v))
            t += b * S.BEAT
    return notes


def chord_bars(start, loops, ending=False):
    prog = PROG * loops + (ENDING_PROG if ending else [])
    return [(start + i * S.BAR, CHORDS[c]) for i, c in enumerate(prog)]


FORMANTS = {  # (freqs, gains, bandwidths) — female singing voice
    "a": ([800, 1150, 2900, 3900, 4950], [1.0, 0.50, 0.30, 0.20, 0.08], [110, 120, 160, 200, 220]),
    "o": ([450, 800, 2830, 3800, 4950], [1.0, 0.35, 0.12, 0.10, 0.05], [90, 110, 160, 200, 220]),
    "u": ([350, 600, 2700, 3800, 4950], [1.0, 0.12, 0.04, 0.03, 0.02], [80, 100, 160, 200, 220]),
    "e": ([420, 1700, 2750, 3400, 4950], [1.0, 0.35, 0.25, 0.15, 0.05], [90, 120, 160, 200, 220]),
}
ROUND = {"a": 0.0, "e": 0.15, "o": 0.6, "u": 1.0}


def sing(notes, total, octave=0, vib_depth=0.33, breath=0.05, seed=3, detune=0.0):
    """Additive formant synthesis of a wordless sung line.

    Returns (audio, amplitude_envelope, roundness) at SR.
    """
    r = np.random.default_rng(seed)
    n = secs(total)
    CR = 64  # control rate decimation
    nc = n // CR + 2
    tc = np.arange(nc) * CR / SR
    logf = np.full(nc, np.nan)
    amp = np.zeros(nc)
    vstart = np.full(nc, -10.0)
    F, G, B = FORMANTS["a"]
    vow_f = np.tile(F, (nc, 1)).astype(float)
    vow_g = np.tile(G, (nc, 1)).astype(float)
    vow_b = np.tile(B, (nc, 1)).astype(float)
    roundness = np.zeros(nc)
    for i, (t0, d, m, v) in enumerate(notes):
        m = m + 12 * octave
        a, b = int(t0 * SR / CR), int((t0 + d) * SR / CR)
        if a >= nc:
            break
        b = min(b, nc)
        nxt = notes[i + 1] if i + 1 < len(notes) else None
        legato = nxt is not None and abs(nxt[0] - (t0 + d)) < 1e-3
        prev = notes[i - 1] if i > 0 else None
        first = prev is None or abs(prev[0] + prev[1] - t0) > 1e-3
        logf[a:b] = m
        tt = tc[a:b] - t0
        att = 0.16 if first else 0.05
        env = np.clip(tt / att, 0, 1)
        # soft articulation dip at the start of each legato note
        if not first:
            env = 0.72 + 0.28 * np.clip(tt / 0.09, 0, 1)
        env = env * (1.0 - 0.12 * np.clip(tt / max(d, 0.1), 0, 1))  # slight decay
        if not legato:
            rel = 0.22
            env = env * np.clip((d - tt) / rel, 0, 1)
        amp[a:b] = np.maximum(amp[a:b], env)
        vstart[a:b] = t0
        F, G, B = FORMANTS[v]
        vow_f[a:b] = F; vow_g[a:b] = G; vow_b[a:b] = B
        roundness[a:b] = ROUND[v]
        # scoop into each note from slightly below
        logf[a:b] -= 0.35 * np.exp(-tt / 0.05)
    voiced = ~np.isnan(logf)
    # fill gaps so smoothing does not jump
    idx = np.arange(nc)
    if voiced.any():
        logf = np.interp(idx, idx[voiced], logf[voiced])
    else:
        return np.zeros((n, 2)), np.zeros(n), np.zeros(n)
    # portamento: smooth the pitch contour (~60 ms)
    k = signal.windows.hann(int(0.06 * SR / CR) * 2 + 1)
    logf = np.convolve(logf, k / k.sum(), mode="same")
    for arr in (vow_f, vow_g, vow_b):
        kk = signal.windows.hann(int(0.15 * SR / CR) * 2 + 1)
        for j in range(5):
            arr[:, j] = np.convolve(arr[:, j], kk / kk.sum(), mode="same")
    kk = signal.windows.hann(int(0.12 * SR / CR) * 2 + 1)
    roundness = np.convolve(roundness, kk / kk.sum(), mode="same")
    # vibrato that blooms after the onset of each note
    since = tc - vstart
    vib_amt = np.clip((since - 0.22) / 0.45, 0, 1) * vib_depth
    rate = 5.2 + 0.4 * np.sin(2 * np.pi * 0.13 * tc + 1.0)
    vib_phase = 2 * np.pi * np.cumsum(rate) * CR / SR
    jitter = np.convolve(r.standard_normal(nc), np.ones(40) / 40, mode="same") * 0.25
    logf = logf + vib_amt * np.sin(vib_phase) + jitter * 0.15 + detune
    f0c = midi_hz(logf)
    amp = np.convolve(amp, np.ones(5) / 5, mode="same")
    shimmer = 1 + 0.04 * np.convolve(r.standard_normal(nc), np.ones(20) / 20, mode="same")
    ampc = amp * shimmer

    # upsample control signals
    ts = np.arange(n) / SR
    f0 = np.interp(ts, tc, f0c)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(n)
    NH = 24
    for h in range(1, NH + 1):
        fh = h * f0c
        g = np.zeros(nc)
        for j in range(5):
            g += vow_g[:, j] / (1 + ((fh - vow_f[:, j]) / (vow_b[:, j] * 0.5)) ** 2)
        g *= h ** -0.55
        g *= np.clip((7000 - fh) / 1500, 0, 1)
        if not np.any(g > 1e-4):
            continue
        out += np.interp(ts, tc, g * ampc) * np.sin(h * phase + r.uniform(0, 6.28))
    # breath noise
    ampu = np.interp(ts, tc, ampc)
    br = butter(r.standard_normal(n), "band", [1800, 7000]) * breath
    out += br * ampu
    rnd = np.interp(ts, tc, roundness)
    return out, ampu, rnd


def piano(chords, total, vel=0.5, seed=5):
    n = secs(total)
    out = np.zeros(n)
    r = np.random.default_rng(seed)
    for t0, (bass, tones) in chords:
        # pattern of eighth notes: bass, then broken chord
        seq = [bass, tones[0], tones[1], tones[2], tones[3], tones[2], tones[1], tones[0]]
        for k, m in enumerate(seq):
            tk = max(t0 + k * S.BEAT / 2 + r.normal(0, 0.006), 0)
            v = vel * (1.0 if k == 0 else 0.55) * (0.9 + 0.2 * r.random())
            note = piano_note(m, 3.2, v)
            i0 = secs(tk)
            j = min(len(note), n - i0)
            if j > 0:
                out[i0:i0 + j] += note[:j]
    return out


_pcache = {}


def piano_note(m, dur, v):
    key = (m, dur)
    if key not in _pcache:
        f = midi_hz(m)
        t = np.arange(secs(dur)) / SR
        x = np.zeros_like(t)
        tau = 1.6 * (261.0 / f) ** 0.5
        for h in range(1, 9):
            fh = f * h * np.sqrt(1 + 0.0004 * h * h)
            if fh > 9000:
                break
            x += (h ** -1.3) * np.exp(-t / (tau / (1 + 0.7 * (h - 1)))) * np.sin(2 * np.pi * fh * t)
        x *= np.clip(t / 0.004, 0, 1)
        x *= np.clip((dur - t) / 0.4, 0, 1)
        _pcache[key] = x * 0.25
    return _pcache[key] * v


def pad(chords, total, level=0.3, attack=1.2, seed=9, bright=10):
    n = secs(total)
    out = np.zeros((n, 2))
    r = np.random.default_rng(seed)
    for t0, (bass, tones) in chords:
        d = S.BAR + 1.6
        t = np.arange(secs(d)) / SR
        env = np.clip(t / attack, 0, 1) * np.clip((d - t) / 1.6, 0, 1)
        for m in [bass + 12] + tones[:3]:
            f = midi_hz(m)
            for side, det in ((0, -0.07), (1, 0.07)):
                fd = f * 2 ** (det / 12)
                x = np.zeros_like(t)
                for h in range(1, bright + 1):
                    if fd * h > 6000:
                        break
                    x += np.sin(2 * np.pi * fd * h * t + r.uniform(0, 6.28)) / h ** 1.4
                i0 = secs(t0)
                j = min(len(x), n - i0)
                if j > 0:
                    out[i0:i0 + j, side] += (x * env)[:j] * level * 0.05
    return out


def musicbox(notes, total, level=0.25):
    n = secs(total)
    out = np.zeros(n)
    for t0, d, m, v in notes:
        f = midi_hz(m + 12)
        t = np.arange(secs(2.5)) / SR
        x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9)
             + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.25)
             + 0.12 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08))
        x *= np.clip(t / 0.002, 0, 1)
        i0 = secs(t0)
        j = min(len(x), n - i0)
        if j > 0:
            out[i0:i0 + j] += x[:j] * level
    return out


def choir(chords, total, level=0.25):
    """Sustained 'ah/oo' voices on the chord tones."""
    n = secs(total)
    out = np.zeros((n, 2))
    voices = [[], [], [], []]
    for t0, (bass, tones) in chords:
        for k, m in enumerate([bass + 12, tones[0], tones[1], tones[2]]):
            voices[k].append((t0, S.BAR, m, "a" if k % 2 else "o"))
    for k, notes in enumerate(voices):
        for side in (0, 1):
            x, _, _ = sing(notes, total, vib_depth=0.15, breath=0.08, seed=20 + 2 * k + side,
                           detune=(-0.08 if side else 0.08))
            out[:, side] += x * level * (0.8 if k == 0 else 1.0)
    return out


# ----------------------------------------------------------------- sound fx

def noise(n, color="white", seed=0):
    r = np.random.default_rng(seed)
    w = r.standard_normal(n)
    if color == "pink":
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        w = signal.lfilter(b, a, w) * 5
    elif color == "brown":
        w = np.cumsum(w)
        w = butter(w, "high", 20) * 0.02
    return w


def rain(total, level_fn, seed=11):
    n = secs(total)
    t = np.arange(n) / SR
    x = butter(noise(n, "pink", seed), "band", [500, 9000]) * 0.5
    st = np.stack([x, np.roll(x, 3001)], axis=1)
    # droplets
    r = np.random.default_rng(seed)
    drops = np.zeros(n)
    k = r.integers(0, n, size=int(total * 60))
    drops[k] = r.uniform(-1, 1, size=len(k))
    drops = butter(drops, "band", [2000, 8000]) * 1.5
    st += pan(drops, 0.3) * 0.7
    return st * level_fn(t)[:, None]


def thunder(seed, big=False):
    r = np.random.default_rng(seed)
    d = 7.0 if big else 5.0
    n = secs(d)
    t = np.arange(n) / SR
    crack = butter(r.standard_normal(n), "high", 900) * np.exp(-t / 0.06) * 0.9
    rumble = np.zeros(n)
    for _ in range(9 if big else 6):
        c = r.uniform(0.05, d * 0.5)
        rumble += np.exp(-np.abs(t - c) / r.uniform(0.25, 0.9)) * r.uniform(0.4, 1.0)
    low = butter(noise(n, "brown", seed + 1), "low", 160) * 25
    mid = butter(r.standard_normal(n), "band", [60, 500]) * 0.6
    x = (low + mid) * rumble * np.exp(-t / (d * 0.45)) + crack
    x = np.tanh(x * 1.5)
    return reverb(x, 2.5, 2.0, wet=0.35, bright=0.3, seed=seed) * (0.3 if big else 0.22)


def drone(total, level_fn, notes=(33, 34, 40, 45), seed=13):
    n = secs(total)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    r = np.random.default_rng(seed)
    for m in notes:
        f = midi_hz(m)
        for side in (0, 1):
            fd = f * 2 ** (r.uniform(-0.1, 0.1) / 12)
            x = np.zeros(n)
            for h in range(1, 14):
                x += np.sin(2 * np.pi * fd * h * t + r.uniform(0, 6.28)) / h
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * r.uniform(0.05, 0.15) * t + r.uniform(0, 6.28))
            out[:, side] += x * lfo
    out = butter(out, "low", 700) * 0.04
    return out * level_fn(t)[:, None]


def wind(total, level_fn, seed=17):
    n = secs(total)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for i, (lo, hi) in enumerate([(150, 400), (300, 800), (600, 1500)]):
        x = butter(noise(n, "pink", seed + i), "band", [lo, hi])
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.07 + 0.05 * i) * t + i * 2)
        out += pan(x * lfo, [-0.5, 0.5, 0.0][i])
    return out * 0.6 * level_fn(t)[:, None]


def heartbeat(t0, t1, period=0.95):
    n = secs(t1 - t0 + 1)
    out = np.zeros(n)
    tt = np.arange(secs(0.25)) / SR
    thump = np.sin(2 * np.pi * 48 * tt) * np.exp(-tt / 0.06)
    k = 0.0
    while k < t1 - t0:
        for off, a in ((0, 1.0), (0.28, 0.7)):
            i = secs(k + off)
            j = min(len(thump), n - i)
            if j > 0:
                out[i:i + j] += thump[:j] * a
        k += period
    return butter(out, "low", 200) * 0.9


def whoosh(d, rising=True, seed=19):
    n = secs(d)
    t = np.arange(n) / SR
    x = noise(n, "pink", seed)
    env = (t / d) ** 2 if rising else np.exp(-t / (d * 0.3))
    x = butter(x, "band", [200, 3000]) * env
    return pan(x, 0) * 0.5


def footsteps(times, wet=True, seed=23):
    r = np.random.default_rng(seed)
    clip_len = secs(0.18)
    tt = np.arange(clip_len) / SR
    out = []
    for t in times:
        x = r.standard_normal(clip_len) * np.exp(-tt / 0.03)
        x = butter(x, "band", [150, 2500 if wet else 1200])
        if wet:
            x += butter(r.standard_normal(clip_len), "high", 3000) * np.exp(-tt / 0.06) * 0.3
        out.append((t, x * 0.35))
    return out


def door_creak(seed=29):
    r = np.random.default_rng(seed)
    d = 1.6
    n = secs(d)
    t = np.arange(n) / SR
    f = 260 + 140 * np.sin(np.pi * t / d) + 30 * np.convolve(r.standard_normal(n), np.ones(800) / 800, "same")
    ph = 2 * np.pi * np.cumsum(f) / SR
    stick = (np.convolve(r.random(n) > 0.995, np.ones(60), "same") > 0).astype(float)
    x = signal.sawtooth(ph) * (0.3 + 0.7 * stick)
    x = butter(x, "band", [300, 2500]) * np.sin(np.pi * t / d) ** 0.5 * 0.25
    return reverb(x, 1.0, 0.8, wet=0.25)


def shimmer(d, level=0.08, seed=31):
    """High crystalline tone for the spark."""
    r = np.random.default_rng(seed)
    n = secs(d)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for m in (96, 100, 103, 108):
        f = midi_hz(m)
        for side in (0, 1):
            trem = 0.5 + 0.5 * np.sin(2 * np.pi * r.uniform(0.3, 1.2) * t + r.uniform(0, 6.28))
            out[:, side] += np.sin(2 * np.pi * f * (1 + r.uniform(-0.002, 0.002)) * t) * trem
    return out * level / 4


def ting(level=0.3):
    t = np.arange(secs(4)) / SR
    x = np.zeros_like(t)
    for f, a, d in ((2093, 1, 2.5), (2093 * 2.0, 0.4, 1.2), (2093 * 3.01, 0.2, 0.6), (1046.5, 0.3, 3)):
        x += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    x *= np.clip(t / 0.003, 0, 1)
    return reverb(x * level, 4.0, 3.5, wet=0.5, bright=0.8)


def embers(t0, t1, seed=37):
    r = np.random.default_rng(seed)
    n = secs(t1 - t0)
    x = np.zeros(n)
    k = r.integers(0, n, size=int((t1 - t0) * 40))
    x[k] = r.uniform(-1, 1, size=len(k)) * np.linspace(1, 0.2, n)[k]
    x = butter(x, "band", [1500, 9000])
    return reverb(pan(x, 0) * 7.0, 1.5, 1.2, wet=0.3)


def tape_warp(x, t, rate):
    """Read x at a variable speed: rate(t) array (1 = normal)."""
    pos = np.cumsum(rate) - rate[0]
    pos = np.clip(pos, 0, len(x) - 1)
    out = np.empty_like(x)
    idx = np.arange(len(x))
    for c in range(x.shape[1]):
        out[:, c] = np.interp(pos, idx, x[:, c])
    return out


def frame_env(x, fps, total, gain=None):
    """Per-video-frame envelope (0..1) of a mono signal."""
    nf = int(np.ceil(total * fps))
    hop = SR / fps
    e = np.zeros(nf)
    for i in range(nf):
        a, b = int(i * hop), int((i + 1) * hop)
        seg = x[a:b]
        if len(seg):
            e[i] = np.sqrt(np.mean(seg ** 2))
    if gain is None:
        p = np.percentile(e[e > 1e-5], 95) if np.any(e > 1e-5) else 1
        gain = 1 / (p + 1e-9)
    e = np.clip(e * gain, 0, 1)
    # gentle smoothing so the mouth does not flicker
    out = np.zeros_like(e)
    y = 0
    for i, v in enumerate(e):
        y = y + (v - y) * (0.75 if v > y else 0.45)
        out[i] = y
    return out


# ----------------------------------------------------------------- parts

def place_lines(part, total, bus, timeline):
    """Synthesize, process and place dialogue. Returns dict of dry speech per speaker."""
    dry = {k: np.zeros(secs(total)) for k in S.VOICES}
    cues = []
    lines = sorted(part["lines"], key=lambda l: l[1])
    for i, line in enumerate(lines):
        spk, t0, text = line[:3]
        sid = line[3] if len(line) > 3 else None
        x = tts(spk, text, sid)
        dur = len(x) / SR
        lvl = {"listener": 1.35, "singer": 1.2, "jesus": 1.35, "whisper": 1.4}[spk]
        wet = voice_fx(x, S.VOICES[spk]["fx"], seed=i + 100 * (sid or 0)) * lvl
        add(bus, wet, t0)
        i0 = secs(t0)
        j = min(len(x), len(dry[spk]) - i0)
        dry[spk][i0:i0 + j] += x[:j]
        cues.append(dict(speaker=spk, text=text, start=round(t0, 3), end=round(t0 + dur, 3)))
        # warn about overlaps between non-whisper lines
        for c in cues[:-1]:
            if c["speaker"] != "whisper" and spk != "whisper" and c["end"] > t0 + 0.05:
                print(f"  ! overlap: '{c['text']}' ends {c['end']:.2f} > '{text}' at {t0:.2f}")
    timeline["cues"] = cues
    return dry


def duck_curve(dry_all, total, depth=0.45):
    x = np.abs(dry_all)
    hop = 256
    c = np.array([x[i:i + hop].max() for i in range(0, len(x), hop)])
    c = (c > 0.02).astype(float)
    # attack fast, release slow at control rate
    out = np.zeros_like(c)
    y = 0
    for i, v in enumerate(c):
        y = y + (v - y) * (0.3 if v > y else 0.01)
        out[i] = y
    g = 1 - depth * out
    return np.interp(np.arange(len(x)), np.arange(len(g)) * hop, g)


def build_part1(timeline):
    P = S.PARTS[1]
    T = P["duration"]
    n = secs(T)
    t = np.arange(n) / SR
    voice_bus = np.zeros((n, 2))
    dry = place_lines(P, T, voice_bus, timeline)

    sp = P["song"]
    start, loops = sp["vocal_start"], sp["loops"]
    notes = melody_notes(start, loops)
    vocal, vamp, vround = sing(notes, T)
    gate = smoothstep(t, start - 0.1, start + 0.1) * (1 - smoothstep(t, sp["vocal_stop"] - 0.05, sp["vocal_stop"]))
    vocal *= gate
    vamp *= gate
    chords = chord_bars(start, loops)
    pno = piano(chords, T, vel=0.42)
    strings = pad(chords, T, level=0.6)
    song = pan(vocal * 0.55, -0.05) + pan(pno * 0.5, 0.15) + strings * ramp(t, 40, 70, 0.4, 1.0)[:, None]
    song = reverb(song, 3.0, 2.6, wet=0.32, bright=0.5, seed=2)
    # heard through the wall at first
    muff = butter(song, "low", 650) * 0.55
    mix = smoothstep(t, sp["muffle_until"] - 1.2, sp["muffle_until"] + 0.3)[:, None]
    song = muff * (1 - mix) + song * mix
    # the song bends as the storm rises: wow + extra reverb, then a tape slow-down
    warp = smoothstep(t, sp["warp_from"], 160)
    wow = 0.004 * warp * np.sin(2 * np.pi * 0.35 * t) + 0.002 * warp * np.sin(2 * np.pi * 1.7 * t)
    slow = smoothstep(t, 162, 178.5) * 0.45
    song = tape_warp(song, t, 1 + wow - slow)
    wet = reverb(song, 4.0, 3.8, wet=1.0, bright=0.2, seed=4)
    song = song * (1 - 0.5 * warp[:, None]) + wet * 0.7 * warp[:, None]
    song *= (1 - 0.35 * smoothstep(t, 118, 150))[:, None]
    song *= (1 - smoothstep(t, 178.3, 178.6))[:, None]

    # ambience
    rain_lvl = lambda tt: (0.22 * (1 - smoothstep(tt, 31, 33)) + 0.07 * smoothstep(tt, 31, 33)
                          + 0.25 * smoothstep(tt, 116, 140)) * (1 - smoothstep(tt, 178.3, 178.6))
    amb = rain(T, rain_lvl)
    amb += wind(T, lambda tt: 0.05 + 0.35 * smoothstep(tt, 112, 150) * (1 - smoothstep(tt, 178.3, 178.6)))
    amb += drone(T, lambda tt: smoothstep(tt, 108, 140) * 0.8 * (1 - smoothstep(tt, 178.3, 178.6))
                 + 0.6 * smoothstep(tt, 160, 176) * (1 - smoothstep(tt, 178.3, 178.6)))
    city = butter(noise(n, "brown", 41), "low", 120) * 2.0
    amb += pan(city, 0) * (0.25 * (1 - smoothstep(t, 31, 33)))[:, None]
    for k, th in enumerate(P["thunder"]):
        add(amb, thunder(50 + k, big=(th >= 164)), th)
    add(amb, whoosh(13.0, seed=3) * 0.8, 162)
    for ft, clip in footsteps(np.arange(16.3, 22.0, 0.55)):
        add(amb, pan(clip, 0), ft)
    for ft, clip in footsteps(np.arange(29.0, 31.6, 0.6)):
        add(amb, pan(clip, 0.1), ft)
    for ft, clip in footsteps(np.arange(36.5, 43.5, 0.8), wet=False):
        add(amb, pan(clip, -0.3) * 0.6, ft)
    add(amb, door_creak() * 0.8, 33.0)
    add(amb, pan(heartbeat(178.8, 186.0), 0) * 0.9, 178.8)

    timeline["env"] = {
        "singer": frame_env(vocal * gate, S.FPS, T).round(3).tolist(),
        "singerRound": [round(float(v), 2) for v in vround[:: SR // S.FPS][: int(np.ceil(T * S.FPS))]],
        "jesus": [0] * int(np.ceil(T * S.FPS)),
    }
    music = song + amb
    duck = duck_curve(dry["listener"] + dry["singer"] + dry["jesus"], T, depth=0.4)
    return music * duck[:, None] + voice_bus


def build_part2(timeline):
    P = S.PARTS[2]
    T = P["duration"]
    n = secs(T)
    t = np.arange(n) / SR
    voice_bus = np.zeros((n, 2))
    dry = place_lines(P, T, voice_bus, timeline)
    sp = P["song"]

    # --- the storm at its peak (0-24), cut to near silence when the spark appears
    storm_gate = lambda tt: (smoothstep(tt, 0, 1.5) * (1 - smoothstep(tt, 23.6, 24.4)))
    amb = rain(T, lambda tt: 0.45 * storm_gate(tt) + 0.03 * smoothstep(tt, 24, 30) * (1 - smoothstep(tt, 62, 80))
               + 0.1 * smoothstep(tt, 100, 101) * (1 - smoothstep(tt, 158, 172)))
    amb += wind(T, lambda tt: 0.45 * storm_gate(tt) + 0.06 * smoothstep(tt, 158, 165))
    amb += drone(T, lambda tt: 1.1 * storm_gate(tt))
    for k, th in enumerate(P["thunder"]):
        add(amb, thunder(80 + k, big=True), th)
    # warped echo of the song inside the storm
    ghost_notes = melody_notes(-6.0, 2)
    gv, _, _ = sing(ghost_notes, 30, octave=-1, vib_depth=0.5, seed=8)
    ghost = reverb(pan(gv, 0), 5, 4.5, wet=0.85, bright=0.15) * 0.25
    ghost = tape_warp(ghost, t[: len(ghost)], 0.75 + 0.01 * np.sin(2 * np.pi * 0.4 * t[: len(ghost)]))
    ghost *= storm_gate(t[: len(ghost)])[:, None]
    add(amb, ghost, 0)

    # --- the spark: a ting, then a high shimmer that grows
    add(amb, ting(0.22), 24.4)
    sh = shimmer(76, level=0.1)
    sh *= (smoothstep(np.arange(len(sh)) / SR, 0, 6) * (1 - smoothstep(np.arange(len(sh)) / SR, 60, 76)))[:, None]
    add(amb, reverb(sh, 3, 3, wet=0.5), 24.5)
    # music box version of the melody
    mb_notes = melody_notes(sp["musicbox_start"], 2)
    mb = musicbox([nt for nt in mb_notes if nt[0] < 100], T, level=0.18)
    mb = reverb(pan(mb, 0.1), 3.5, 3.2, wet=0.45, bright=0.7) * (1 - smoothstep(t, 96, 102))[:, None]

    # --- transformation: embers, whoosh, choir swell with strings
    add(amb, embers(70, 84), 70)
    add(amb, whoosh(6, seed=5) * 0.5, 64)
    c_start = sp["choir_start"]
    cchords = chord_bars(c_start, 2)[:12]  # runs on through the change, into the room
    ch = choir(cchords, T, level=0.22)
    ch *= (smoothstep(t, c_start, c_start + 6) * (1 + 0.5 * smoothstep(t, 80, 85)) * (1 - smoothstep(t, 98, 105)))[:, None]
    strings1 = pad(cchords, T, level=0.7, attack=2.5)
    strings1 *= (1 - smoothstep(t, 98, 105))[:, None]
    add(amb, whoosh(5.5, seed=7) * 0.7, 78.6)  # rising into the flash of light
    add(amb, ting(0.25), 84.0)

    # --- the room again: the singer sings, stops, then sings again with everything
    va0, va1 = sp["vocal_a"]
    # enter mid-song so the melody is already flowing
    notes_a = melody_notes(va0 - 2 * S.BAR, 1)
    vb = sp["vocal_b_start"]
    notes_b = melody_notes(vb, 2, ending=True)
    vocal_a, amp_a, rnd_a = sing(notes_a, T, seed=4)
    gate_a = smoothstep(t, va0, va0 + 1.5) * (1 - smoothstep(t, va1 - 0.25, va1))
    vocal_a *= gate_a
    amp_a *= gate_a
    vocal_b, amp_b, rnd_b = sing(notes_b, T, seed=6)
    vocal = vocal_a + vocal_b
    chords_a = chord_bars(va0 - 2 * S.BAR, 1)
    chords_b = chord_bars(vb, 2, ending=True)
    pno = piano(chords_a, T, vel=0.35) * (smoothstep(t, va0, va0 + 1.5) * (1 - smoothstep(t, va1, va1 + 2.5)))
    pno += piano(chords_b, T, vel=0.42)
    strings2 = pad(chords_b, T, level=0.7) * smoothstep(t, vb + 8, vb + 20)[:, None]
    ch2 = choir(chord_bars(vb + S.LOOP, 1, ending=True), T, level=0.12) * smoothstep(t, vb + S.LOOP, vb + S.LOOP + 8)[:, None]
    song = pan(vocal * 0.55, -0.05) + pan(pno * 0.5, 0.15) + strings2 + ch2
    song = reverb(song, 3.0, 2.6, wet=0.32, bright=0.5, seed=2)
    # outside, the song fades behind him as he walks away, then returns for the finale
    outside = smoothstep(t, 156, 160) * (1 - smoothstep(t, 188, 192))
    song = song * (1 - 0.45 * outside)[:, None] + butter(song, "low", 1200) * (0.25 * outside)[:, None]

    for ft, clip in footsteps(np.arange(146.0, 156.0, 0.85), wet=False):
        add(amb, pan(clip, -0.2) * 0.6, ft)
    for ft, clip in footsteps(np.arange(158.5, 176.0, 0.7)):
        add(amb, pan(clip, 0) * 0.5, ft)
    add(amb, door_creak(31) * 0.7, 154.5)
    add(amb, ting(0.2), 136.5)
    add(amb, ting(0.18), 170.0)
    # night crickets once the rain stops
    cr = np.zeros(n)
    cri = np.arange(secs(0.03))
    chirp = np.sin(2 * np.pi * 4300 * cri / SR) * np.hanning(len(cri))
    r = np.random.default_rng(3)
    for k in np.arange(166, 205, 0.31):
        for q in range(3):
            i = secs(k + q * 0.045 + r.normal(0, 0.01))
            cr[i:i + len(chirp)] += chirp
    amb += pan(cr * 0.02, 0.4) * (smoothstep(t, 166, 172) * (1 - smoothstep(t, 200, 208)))[:, None]

    music = mb + ch + strings1 + song + amb
    music *= (1 - smoothstep(t, 205, 210))[:, None]

    nf = int(np.ceil(T * S.FPS))
    vround = (rnd_a * (amp_a > 0.01) + rnd_b * (amp_b > 0.01))
    sing_env = frame_env(vocal_a + vocal_b, S.FPS, T)
    speak_env = frame_env(dry["singer"], S.FPS, T)
    timeline["env"] = {
        "singer": np.maximum(sing_env, speak_env).round(3).tolist(),
        "singerRound": [round(float(v), 2) for v in vround[:: SR // S.FPS][:nf]],
        "jesus": frame_env(dry["jesus"], S.FPS, T).round(3).tolist(),
    }
    duck = duck_curve(dry["listener"] + dry["singer"] + dry["jesus"], T, depth=0.45)
    return music * duck[:, None] + voice_bus


def master(x):
    x = butter(x, "high", 30)
    peak = np.percentile(np.abs(x), 99.95)
    x = x / (peak + 1e-9) * 0.8
    x = np.tanh(x * 1.1) / np.tanh(1.1)
    return x / np.max(np.abs(x)) * 0.93


def main(parts=(1, 2)):
    os.makedirs(BUILD, exist_ok=True)
    for p in parts:
        P = S.PARTS[p]
        print(f"part {p}: building audio...")
        tl = dict(part=p, title=P["title"], fps=S.FPS, width=S.W, height=S.H,
                  duration=P["duration"], shots=P["shots"], thunder=P["thunder"],
                  subtitles=P["subtitles"])
        mix = (build_part1 if p == 1 else build_part2)(tl)
        sf.write(os.path.join(BUILD, f"part{p}.wav"), master(mix).astype(np.float32), SR, subtype="PCM_16")
        with open(os.path.join(BUILD, f"timeline_part{p}.json"), "w") as f:
            json.dump(tl, f)
        print(f"part {p}: done ({P['duration']:.0f}s)")


if __name__ == "__main__":
    main(tuple(int(a) for a in sys.argv[1:]) or (1, 2))
