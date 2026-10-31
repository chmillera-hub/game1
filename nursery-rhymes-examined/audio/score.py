#!/usr/bin/env python3
"""Procedural score + sound design for "Nursery Rhymes, Examined".

Reads build/timeline.json and renders (internally at 24 kHz, upsampled to 48 kHz)
five un-ducked buses into build/audio/work/*.npy:

    bed.npy     mood score (drones, clusters, music box, ostinato, false-hope pad, ...)
    song.npy    the passengers' hummed "merry song" (unison humming choir), hard-cut at songEnd
    cues.npy    word cues (high / low / swell / light / hit)
    amb.npy     beds: wind, discordant hum, engine/road, dripping water, rain/torrent
    events.npy  one-shot sound events (ticks, creak, gears, screech, snap, whoosh, ...)

audio/mix.py treats the voice, ducks these under it and writes the final stems and mix.
All material is original (procedural synthesis, no samples).

Run:  python3 -I audio/score.py
"""
import json
import os
import time
import wave

import numpy as np
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TIMELINE = os.path.join(ROOT, "build", "timeline.json")
WORK = os.path.join(ROOT, "build", "audio", "work")

SR = 24000
OUT_SR = 48000
RNG = np.random.default_rng(19731984)
XF = 2.5            # mood crossfade (s)
# target loudness (LUFS, raw bus) of each mood layer; mix.py sets the absolute level of the bed
MOOD_LEVEL = {"bleak": -14.0, "irony": -16.5, "dread": -14.0, "song": -20.0, "drone": -15.5, "urgent": -12.5,
              "drip": -14.5, "fragile": -12.5, "storm": -12.5, "false_hope": -14.0, "clinical": -15.5,
              "cycle": -14.0, "resigned": -13.5}

K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def loudness(x):
    """BS.1770 integrated loudness (gated) of a 24 kHz buffer (measured at 48 kHz)"""
    y = signal.resample_poly(x.astype(np.float64), 2, 1)
    y = signal.lfilter(*K2, signal.lfilter(*K1, y))
    nb, nh = 19200, 4800
    c = np.concatenate([[0.0], np.cumsum(y * y)])
    st = np.arange(0, len(y) - nb + 1, nh)
    L = -0.691 + 10 * np.log10((c[st + nb] - c[st]) / nb + 1e-20)
    L = L[L > -70]
    if not len(L):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((L + 0.691) / 10))) - 10
    L = L[L > rel]
    return float(-0.691 + 10 * np.log10(np.mean(10 ** ((L + 0.691) / 10))))


# ==========================================================================
# helpers
# ==========================================================================
def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)


def ns(sec):
    return max(1, int(round(sec * SR)))


def rcos_in(n):
    if n <= 0:
        return np.ones(0, np.float32)
    return (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))).astype(np.float32)


def env_ar(n, a, r, shape=1.0):
    e = np.ones(n, np.float32)
    na, nr = min(ns(a), n // 2), min(ns(r), n // 2)
    if na > 0:
        e[:na] = rcos_in(na) ** shape
    if nr > 0:
        e[n - nr:] *= rcos_in(nr)[::-1]
    return e


def lowpass(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "low", fs=SR, output="sos"), x).astype(np.float32)


def highpass(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x).astype(np.float32)


def bandpass(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x).astype(np.float32)


def reson(x, f, q):
    """2-pole resonator (peaking bandpass) normalised to unity peak gain"""
    b, a = signal.iirpeak(f, q, fs=SR)
    return signal.lfilter(b, a, x).astype(np.float32)


def noise(n):
    return RNG.standard_normal(n).astype(np.float32)


def brown(n, a=0.995):
    y = signal.lfilter([1.0], [1.0, -a], RNG.standard_normal(n)).astype(np.float32)
    return y / (np.std(y) + 1e-9)


def tv_lowpass(x, fc, block=128):
    """time-varying 2-pole lowpass (cascaded one-poles); fc = per-sample cutoff array"""
    y = np.empty_like(x)
    z1 = np.zeros(1)
    z2 = np.zeros(1)
    for i in range(0, len(x), block):
        a = np.exp(-2 * np.pi * float(fc[i]) / SR)
        s, z1 = signal.lfilter([1 - a], [1, -a], x[i:i + block], zi=z1)
        y[i:i + block], z2 = signal.lfilter([1 - a], [1, -a], s, zi=z2)
    return y


def smooth_rand(n, rate, lo=0.0, hi=1.0, seed=None):
    """slowly varying random curve (cubic-ish interpolation of random points)"""
    r = RNG if seed is None else np.random.default_rng(seed)
    k = max(4, int(n / SR * rate) + 4)
    pts = r.uniform(lo, hi, k)
    xs = np.linspace(0, n, k)
    c = np.interp(np.arange(n), xs, pts)
    w = max(3, int(SR / rate / 2))
    c = ndimage.uniform_filter1d(c, w, mode="nearest")
    return c.astype(np.float32)


def curve(n, pts):
    """piecewise-linear envelope from [(t_sec, value), ...] relative to buffer start"""
    ts = np.array([p[0] for p in pts]) * SR
    vs = np.array([p[1] for p in pts])
    return np.interp(np.arange(n), ts, vs).astype(np.float32)


class Bus:
    def __init__(self, n):
        self.dry = np.zeros(n, np.float32)
        self.send = np.zeros(n, np.float32)
        self.n = n

    def add(self, t, buf, gain=1.0, send=0.0):
        i0 = int(round(t * SR))
        j0 = 0
        if i0 < 0:
            j0, i0 = -i0, 0
        if i0 >= self.n or j0 >= len(buf):
            return
        m = min(len(buf) - j0, self.n - i0)
        seg = buf[j0:j0 + m]
        if gain:
            self.dry[i0:i0 + m] += gain * seg
        if send:
            self.send[i0:i0 + m] += send * seg


# ==========================================================================
# oscillators / instruments
# ==========================================================================
TS = 4096


def make_table(b, K=20, p=1.0, odd=False):
    k = np.arange(1, K + 1, dtype=np.float64)
    amps = (1.0 / k ** p) * np.exp(-(k - 1) / b)
    if odd:
        amps[1::2] *= 0.08
    ph = np.arange(TS) / TS
    tab = (amps[:, None] * np.sin(2 * np.pi * k[:, None] * ph[None, :])).sum(0)
    return (tab / np.abs(tab).max()).astype(np.float32)


TAB = {
    "sine": np.sin(2 * np.pi * np.arange(TS) / TS).astype(np.float32),
    "dark": make_table(1.0),
    "warm": make_table(2.6),
    "hollow": make_table(3.0, odd=True),     # mostly odd harmonics: hollow, flue-like
}


def osc(tab, f, n, vib_rate=0.0, vib_depth=0.0, drift=0.0, phase0=None):
    t = np.arange(n, dtype=np.float64) / SR
    ph0 = RNG.uniform(0, 1) if phase0 is None else phase0
    if vib_depth or drift:
        inst = f * (1.0 + vib_depth * np.sin(2 * np.pi * vib_rate * t + RNG.uniform(0, 6.28))
                    + drift * np.sin(2 * np.pi * RNG.uniform(0.04, 0.1) * t + RNG.uniform(0, 6.28)))
        ph = np.cumsum(inst) / SR + ph0
    else:
        ph = f * t + ph0
    idx = (ph % 1.0) * TS
    i0 = idx.astype(np.int32)
    fr = (idx - i0).astype(np.float32)
    tb = TAB[tab]
    return tb[i0] * (1 - fr) + tb[(i0 + 1) % TS] * fr


def pad_note(f, dur, a=3.0, r=3.0, tab="dark", voices=3, spread=8.0, drift=0.0008):
    n = ns(dur)
    out = np.zeros(n, np.float32)
    for v in range(voices):
        det = (v - (voices - 1) / 2) * spread + RNG.normal(0, 1.5)
        out += osc(tab, f * 2 ** (det / 1200), n, drift=drift)
    t = np.arange(n) / SR
    am = 1.0 + 0.15 * np.sin(2 * np.pi * RNG.uniform(0.04, 0.09) * t + RNG.uniform(0, 6.28))
    return out * env_ar(n, a, r) * am.astype(np.float32) / np.sqrt(voices)


def bell_note(f, vel=0.4, dur=4.5, sour=0.0):
    """soft glass bell; `sour` detunes the 2nd partial (cents) for a slightly wrong edge"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.zeros(n)
    for ratio, amp, tau in ((1.0, 1.0, 2.4), (2.0 * 2 ** (sour / 1200), 0.25, 1.2), (3.01, 0.08, 0.6), (4.17, 0.03, 0.35)):
        fk = f * ratio
        if fk < 9500:
            out += amp * np.exp(-t / tau) * np.sin(2 * np.pi * fk * t + RNG.uniform(0, 6.28))
    return (vel * out * env_ar(n, 0.008, 0.4)).astype(np.float32)


def musicbox_note(f, vel=0.4, dur=2.2):
    """music-box tine: bright attack, inharmonic upper partials, fast decay, tiny beating"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.exp(-t / 0.9) * (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 1.0015 * t))
    for ratio, amp, tau in ((2.0, 0.10, 0.4), (5.4, 0.12, 0.08), (8.9, 0.04, 0.03)):
        if f * ratio < 10000:
            out += amp * np.exp(-t / tau) * np.sin(2 * np.pi * f * ratio * t + RNG.uniform(0, 6.28))
    return (vel * out * env_ar(n, 0.002, 0.3)).astype(np.float32)


def pluck_note(f, vel=0.4, dur=1.4, tau=0.35):
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.exp(-t / tau) * np.sin(2 * np.pi * f * t)
    out += 0.16 * np.exp(-t / (tau * 0.35)) * np.sin(2 * np.pi * 2 * f * t)
    if 3.93 * f < 9000:
        out += 0.06 * np.exp(-t / 0.05) * np.sin(2 * np.pi * 3.93 * f * t)
    return (vel * out * env_ar(n, 0.003, 0.2)).astype(np.float32)


def water_tone(f, vel=0.4, dur=1.6):
    """'water' pluck: sine with a small upward pitch bloop and soft decay"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    inst = f * (1 + 0.06 * (1 - np.exp(-t / 0.03)))
    ph = 2 * np.pi * np.cumsum(inst) / SR
    out = np.exp(-t / 0.45) * np.sin(ph) + 0.12 * np.exp(-t / 0.15) * np.sin(2 * ph)
    return (vel * out * env_ar(n, 0.004, 0.3)).astype(np.float32)


def deep_note(f, vel=0.5, dur=4.5):
    """deep bowed/organ-like note with sub for 'low' cues"""
    n = ns(dur)
    x = 0.6 * osc("dark", f, n, drift=0.0005) + 0.5 * osc("sine", f / 2, n) + 0.25 * osc("warm", f * 1.004, n)
    return (vel * x * env_ar(n, 0.12, 2.8, shape=0.7)).astype(np.float32)


def felt_hit(f0=50.0, vel=0.6, dur=3.0):
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    inst = f0 * (1 + 0.3 * np.exp(-t / 0.04))
    ph = 2 * np.pi * np.cumsum(inst) / SR
    out = np.exp(-t / 0.9) * np.sin(ph) + 0.4 * np.exp(-t / 0.5) * np.sin(1.504 * ph) + 0.2 * np.exp(-t / 0.3) * np.sin(2 * ph)
    thump = lowpass(noise(n), 220, 2) * np.exp(-t / 0.03).astype(np.float32)
    return (vel * (out + 0.8 * thump) * env_ar(n, 0.003, 0.6)).astype(np.float32)


def whoosh(dur=1.8, f_lo=180, f_hi=1500, vel=0.5):
    n = ns(dur)
    u = np.linspace(0, 1, n)
    shape = np.sin(np.pi * u ** 0.8) ** 2
    y = tv_lowpass(noise(n), f_lo * (f_hi / f_lo) ** shape)
    y = highpass(y, 90)
    return (vel * y * shape ** 1.3 / (np.std(y) + 1e-9) * 0.3).astype(np.float32)


def make_ir(dur, t60, lp_start, lp_end, predelay=0.02, seed=1):
    r = np.random.default_rng(seed)
    n = ns(dur)
    t = np.arange(n) / SR
    nz = r.standard_normal(n).astype(np.float32)
    x = np.linspace(0, 1, n) ** 0.6
    ir = (lowpass(nz, lp_start) * (1 - x) + lowpass(nz, lp_end) * x) * (10 ** (-3 * t / t60))
    ir[:ns(0.006)] *= rcos_in(ns(0.006))
    ir = np.concatenate([np.zeros(ns(predelay), np.float32), ir.astype(np.float32)])
    return ir / np.sqrt(np.sum(ir ** 2))


# ==========================================================================
# the passengers' song: unison humming choir
# ==========================================================================
# formant sets (f, q, gain): "mmm" = closed, nasal, low; "ooo" = rounded; "oh" = a little open.
# Slightly raised (child-like) formants, with a small 3 kHz "brightness" peak.
FORM = {
    "mmm": [(260, 4.0, 1.0), (1050, 6.0, 0.10), (2600, 8.0, 0.04)],
    "ooo": [(370, 5.0, 1.0), (950, 6.0, 0.35), (2500, 8.0, 0.08), (3300, 9.0, 0.05)],
    "oh":  [(520, 5.0, 1.0), (1000, 6.0, 0.45), (2650, 8.0, 0.11), (3400, 9.0, 0.07)],
}


def formant(x, which):
    y = np.zeros_like(x)
    for f, q, g in FORM[which]:
        y += g * reson(x, f, q)
    return y


def glottal(f_inst, amp_harm_bright):
    """band-limited harmonic source with per-sample frequency; bright 0..1 tilts the spectrum"""
    n = len(f_inst)
    ph = 2 * np.pi * np.cumsum(f_inst) / SR
    out = np.zeros(n, np.float32)
    fmax = float(np.max(f_inst))
    K = int(min(24, 5200 / fmax))
    for k in range(1, K + 1):
        a = (1.0 / k ** (1.6 - 0.5 * amp_harm_bright))
        # fade harmonics approaching 5.2 kHz smoothly (alias/harshness guard)
        lim = np.clip((5200 - k * f_inst) / 600, 0, 1).astype(np.float32)
        out += (a * np.sin(k * ph)).astype(np.float32) * lim
    return out


def render_song(song, song_end, t_lo, t_drone):
    """returns (buffer starting at t_lo, ...). Notes: [{t, dur, midi, vel}]"""
    t0 = song[0]["t"] - 0.3
    t1 = song_end + 0.05
    n = ns(t1 - t0)
    tt = np.arange(n) / SR + t0
    out = np.zeros(n, np.float32)
    NV = 6
    for v in range(NV):
        r = np.random.default_rng(1000 + v)
        # per-voice pitch/amp tracks with jittered note boundaries
        midi = np.zeros(n)
        amp = np.zeros(n, np.float32)
        open_ = np.zeros(n, np.float32)
        det = r.normal(0, 7.0) / 100.0          # +-7 cents
        lag = r.uniform(-0.025, 0.035)
        for i, nt in enumerate(song):
            s = nt["t"] + lag - t0
            e = min(s + nt["dur"], t1 - t0)
            if i + 1 < len(song):
                e = min(e, song[i + 1]["t"] + lag - t0)
            a, b = ns(max(0, s)), min(n, ns(e))
            if b <= a:
                continue
            drone = nt["t"] >= t_drone
            loud = nt["vel"] > 0.7
            m = nt["midi"] + det - (0.14 if drone else 0.0)     # drone passage sags a little flat
            # scoop into the note (childish, untrained): start ~40 cents low, glide 60 ms
            L = b - a
            g = np.minimum(1, np.arange(L) / ns(0.06))
            midi[a:b] = m - 0.4 * (1 - g) * r.uniform(0.4, 1.0)
            vel = nt["vel"] ** 1.2 * (1.4 if drone else 1.0) * (1.3 if loud else 1.0)    # low hum reads quieter: compensate
            e_ = env_ar(L, 0.045 if not drone else 0.09, 0.06 if not drone else 0.12)
            # gentle articulation dip at the note start (humming "m-m-m")
            amp[a:b] = vel * (0.72 + 0.28 * e_) * np.minimum(1, (np.arange(L) + 1) / ns(0.02))
            # mouth opening mmm -> ooo (-> oh when loud); drone stays closed and numb
            peak = 0.25 if drone else (0.95 if loud else 0.65)
            sh = np.sin(np.pi * np.clip(np.arange(L) / max(L, 1) * 1.15, 0, 1)) ** 0.8
            open_[a:b] = peak * sh
        # smooth the tracks (legato glides, no zipper)
        k = ns(0.025)
        midi = ndimage.uniform_filter1d(midi, k, mode="nearest")
        amp = np.convolve(amp, np.ones(k) / k, mode="same").astype(np.float32)
        # vibrato: delayed onset, ~5.3 Hz, drone passage almost none
        vib_depth = np.where(tt >= t_drone, 0.06, 0.18)                          # semitones
        vib = vib_depth * np.sin(2 * np.pi * r.uniform(5.0, 5.8) * tt + r.uniform(0, 6.28))
        wob = 0.05 * np.sin(2 * np.pi * r.uniform(0.15, 0.3) * tt + r.uniform(0, 6.28))
        f = mtof(midi + vib + wob)
        f[midi < 1] = 200.0
        bright = np.where(tt >= t_drone, 0.0, 0.8)
        src = glottal(f, float(np.mean(bright)))
        breath = highpass(noise(n), 1500) * 0.015
        x = (src + breath) * amp
        closed = formant(x, "mmm")
        oo = formant(x, "ooo")
        oh = formant(x, "oh")
        o = open_
        y = closed * (1 - np.minimum(o, 0.6) / 0.6) + oo * np.minimum(o, 0.6) / 0.6 * (1 - np.maximum(o - 0.6, 0) / 0.4) \
            + oh * np.maximum(o - 0.6, 0) / 0.4
        # numb: drone passage loses top
        y = np.where(tt >= t_drone, lowpass(y, 1400), y).astype(np.float32)
        out += y
    out /= np.sqrt(NV)
    out = highpass(out, 120)
    # HARD CUT at song_end: 12 ms ramp, nothing after
    ie = ns(song_end - t0)
    r_ = ns(0.012)
    out[ie - r_:ie] *= rcos_in(r_)[::-1]
    out[ie:] = 0
    return t0, out


# ==========================================================================
# score
# ==========================================================================
class Score:
    def __init__(self, tl):
        self.tl = tl
        self.dur = float(tl["duration"])
        self.n = int(np.ceil(self.dur * SR)) + 1
        self.bed = Bus(self.n)
        self.song = Bus(self.n)
        self.cues = Bus(self.n)
        self.hit = Bus(self.n)          # the 'cease' hit: the only music allowed past the cut
        self.amb = Bus(self.n)
        self.events = Bus(self.n)
        self.song_end = float(tl["songEnd"])
        self.part2 = [t for t in tl["titles"] if t["part"] == 1][0]["start"]
        self.moods = tl["music"]["moods"]
        notes = tl["song"]
        # first note of the slow 'drone' passage
        self.t_drone = next(nt["t"] for nt in notes if nt["dur"] > 0.7 and nt["midi"] < 58)
        self.segs = []
        for i, m in enumerate(self.moods):
            t1 = self.moods[i + 1]["t"] if i + 1 < len(self.moods) else self.dur
            self.segs.append((m["t"], t1, m["mood"]))

    def mood_at(self, t):
        cur = self.segs[0][2]
        for a, b, m in self.segs:
            if a <= t:
                cur = m
        return cur

    def span_env(self, t0, t1, fin=XF, fout=XF):
        """segment envelope incl. crossfade tails; returns (start time, n, env)"""
        a = max(0.0, t0 - fin / 2)
        b = min(self.dur, t1 + fout / 2)
        n = ns(b - a)
        e = np.ones(n, np.float32)
        ni = ns(fin) if t0 > 0.01 else ns(0.25)
        no = ns(fout) if t1 < self.dur - 0.01 else 1
        e[:ni] = rcos_in(ni)[:n][: ni] if ni <= n else e[:ni]
        e[n - no:] *= rcos_in(no)[::-1]
        return a, n, e

    # ---------------------------------------------------------------- moods
    def m_bleak(self, t0, t1):
        a, n, e = self.span_env(t0, t1)
        x = 0.55 * pad_note(mtof(38), n / SR, 2.0, 2.0, "dark", 3, 6) + 0.35 * pad_note(mtof(45), n / SR, 4.0, 3.0, "dark", 3, 9)
        x += 0.18 * pad_note(mtof(50), n / SR, 6.0, 3.0, "warm", 2, 12)
        # discordant distant hum: two close tones beating at ~1.3 Hz
        hum = 0.5 * osc("dark", 146.8, n) + 0.5 * osc("dark", 148.1, n)
        x += 0.16 * lowpass(hum, 600) * smooth_rand(n, 0.15, 0.5, 1.0)
        # wind-like breath around the drone (bandpassed noise, slowly moving)
        br = tv_lowpass(brown(n, 0.9), 250 + 300 * smooth_rand(n, 0.12))
        x += 0.10 * highpass(br, 120)
        if t0 < 0.01:   # the title card: the drone emerges slowly out of the wind and hum
            e = e * curve(n, [(0, 0.0), (0.3, 0.25), (3.5, 0.5), (7.0, 1.0), (n / SR, 1.0)])
        self.bed.add(a, x * e, 1.0, 0.35)

    def m_irony(self, t0, t1):
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        x = 0.3 * pad_note(mtof(38), d, 1.0, 3.0, "dark", 2, 6)      # bleak pedal lingers underneath
        for m, g in ((48, 0.35), (55, 0.30), (64, 0.22), (72, 0.10)):   # hollow, faint C major (open)
            x += g * pad_note(mtof(m), d, 3.5, 3.0, "hollow", 2, 4, drift=0.0003)
        self.bed.add(a, lowpass(x, 2200) * e, 0.8, 0.5)

    def m_dread(self, t0, t1, song_over=False):
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        x = 0.45 * pad_note(mtof(26), d, 3.0, 3.0, "dark", 2, 5)       # D1 pedal
        # low cluster swells, ~7 s apart, alternating voicings
        clusters = [(37, 38, 39), (38, 39, 44), (36, 37, 38, 42), (38, 39, 41)]
        t = 0.0
        k = 0
        while t < d - 2:
            L = RNG.uniform(6.5, 8.0)
            for m in clusters[k % len(clusters)]:
                x_ = pad_note(mtof(m), L + 2.0, L * 0.6, L * 0.4 + 1.5, "warm", 2, 10)
                i = ns(t)
                mm = min(len(x_), n - i)
                if mm > 0:
                    x[i:i + mm] += 0.32 * x_[:mm]
            t += L * 0.85
            k += 1
        x = lowpass(x, 900 if song_over else 1300)
        self.bed.add(a, x * e, 1.0, 0.45)

    def m_song(self, t0, t1):
        # placid support: a soft low C pedal + fifth (the song carries this section)
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        x = 0.45 * pad_note(mtof(36), d, 3.0, 3.0, "dark", 2, 5) + 0.25 * pad_note(mtof(43), d, 4.0, 3.0, "dark", 2, 7)
        # a faint sour high sine (D5 a hair sharp) - the wrongness under the cheer
        x += 0.045 * osc("sine", mtof(74) * 1.012, n) * smooth_rand(n, 0.2, 0.0, 1.0)
        self.bed.add(a, x * e, 0.9, 0.35)

    def m_drone(self, t0, t1):
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        x = 0.55 * pad_note(mtof(31), d, 4.0, 3.0, "dark", 3, 5) + 0.35 * pad_note(mtof(38), d, 5.0, 3.0, "dark", 2, 8)
        hum = 0.5 * osc("dark", 98.0, n) + 0.5 * osc("dark", 98.9, n)
        x += 0.18 * hum
        t = np.arange(n) / SR
        x *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.21 * t)).astype(np.float32)    # numb, slow tremolo
        self.bed.add(a, lowpass(x, 800) * e, 1.0, 0.3)

    def m_urgent(self, t0, t1):
        """rising tense pulse under the final Part I line"""
        a, n, e = self.span_env(t0, t1, 1.5, 3.0)
        d = n / SR
        x = np.zeros(n, np.float32)
        t = 0.6
        while t < d - 1.0:
            u = t / d
            bpm = 84 + 66 * u                     # accelerates
            step = 60.0 / bpm / 2                 # eighth notes
            m = 38 + int(u * 7)                   # pedal climbs chromatically D2 -> A2
            acc = 1.0 if int(round(t / step)) % 2 == 0 else 0.6
            p = pluck_note(mtof(m), 0.5 * acc, 0.5, 0.09) + 0.6 * pluck_note(mtof(m - 12), 0.5 * acc, 0.5, 0.12)
            i = ns(t)
            mm = min(len(p), n - i)
            x[i:i + mm] += lowpass(p, 1500)[:mm] * (0.5 + 0.7 * u)
            t += step
        # tense rising string-like line (minor 2nds), filtered
        L = d
        line = pad_note(mtof(50), L, L * 0.8, 2.5, "warm", 3, 14) + pad_note(mtof(51), L, L * 0.9, 2.5, "warm", 2, 14)
        cf = 400 + 1600 * np.linspace(0, 1, n) ** 1.5
        x += 0.35 * tv_lowpass(line, cf)
        x += 0.35 * pad_note(mtof(26), L, 3.0, 2.5, "dark", 2, 5)
        self.bed.add(a, x * e, 0.9, 0.3)

    def m_drip(self, t0, t1):
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        x = 0.25 * pad_note(mtof(33), d, 3.0, 3.0, "dark", 2, 5)
        scale = [69, 72, 74, 76, 79, 81, 84]
        t = RNG.uniform(0.8, 1.5)
        while t < d - 1.5:
            m = scale[RNG.integers(len(scale))]
            p = water_tone(mtof(m), RNG.uniform(0.2, 0.35), 1.6)
            self.bed.add(a + t, p * float(np.interp(ns(t), np.arange(n), e)), 0.6, 0.8)
            t += RNG.uniform(1.6, 3.4)
        self.bed.add(a, x * e, 1.0, 0.3)

    def m_fragile(self, t0, t1):
        """music-box motif in A minor (original), slow, with a thin pad underneath"""
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        pad = 0.22 * pad_note(mtof(45), d, 4, 3, "dark", 2, 6) + 0.14 * pad_note(mtof(52), d, 5, 3, "dark", 2, 6) \
            + 0.07 * pad_note(mtof(60), d, 6, 3, "dark", 2, 8)
        self.bed.add(a, pad * e, 1.0, 0.4)
        # motif: (beats, midi) at 0.42 s per beat; phrase A then answer B, ending on the 5th
        A = [(1, 81), (1, 84), (1, 88), (2, 86), (1, 84), (1, 83), (1, 84), (3, 81)]
        B = [(1, 80), (1, 83), (1, 86), (2, 84), (1, 83), (1, 81), (1, 80), (3, 76)]
        C = [(1, 77), (1, 81), (1, 84), (2, 83), (1, 81), (1, 80), (1, 81), (3, 81)]
        phrases = [A, B, A, C]
        beat = 0.42
        t = 1.5
        k = 0
        while t < d - 4:
            ph = phrases[k % 4]
            for bts, m in ph:
                # the box is old: a rare note slightly out of tune, small timing wobble
                cents = 22 if RNG.random() < 0.08 else 0
                p = musicbox_note(mtof(m) * 2 ** (cents / 1200), 0.18, 2.2)
                gain = float(np.interp(ns(t), np.arange(n), e))
                self.bed.add(a + t + RNG.normal(0, 0.012), p * gain, 1.0, 0.7)
                t += bts * beat * (1 + 0.02 * k)       # winds down very slightly with each phrase
            t += RNG.uniform(3.0, 5.0)               # breath between phrases
            k += 1

    def m_storm(self, t0, t1):
        a, n, e = self.span_env(t0, t1, 3.0, 3.0)
        d = n / SR
        x = 0.5 * pad_note(mtof(21), d, 4, 3, "dark", 3, 10) + 0.4 * pad_note(mtof(28), d, 5, 3, "dark", 3, 14)
        x += 0.3 * pad_note(mtof(33), d, 6, 3, "warm", 4, 18) + 0.2 * pad_note(mtof(34), d, 8, 3, "warm", 3, 18)
        x += 0.12 * pad_note(mtof(40), d, 10, 3, "warm", 4, 22)
        t = 2.0
        while t < d - 3:                              # low swells
            L = RNG.uniform(5.5, 7.5)
            s = pad_note(mtof(RNG.choice([21, 22, 28])), L, L * 0.7, L * 0.3, "warm", 3, 12)
            self.bed.add(a + t, 0.45 * lowpass(s, 500) * float(np.interp(ns(t), np.arange(n), e)), 1.0, 0.4)
            t += L * RNG.uniform(0.9, 1.2)
        # heavier toward the torrent
        g = curve(n, [(0, 0.75), (d * 0.6, 0.9), (d * 0.85, 1.15), (d, 1.1)])
        self.bed.add(a, lowpass(x, 1100) * e * g, 1.0, 0.4)

    def m_false_hope(self, t0, t1):
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        # saccharine F major add9 pad, bright...
        x = np.zeros(n, np.float32)
        for m, g in ((53, 0.3), (65, 0.25), (69, 0.22), (72, 0.18), (79, 0.10)):
            x += g * pad_note(mtof(m), d, 2.5, 2.5, "warm", 3, 6)
        # ...with a sour edge: a sustained A5 ~28 cents flat
        x += 0.05 * osc("sine", mtof(81) * 2 ** (-28 / 1200), n, 5.0, 0.002) * env_ar(n, 4, 3)
        self.bed.add(a, lowpass(x, 3500) * e, 0.8, 0.5)
        # bells: rising major-pentatonic figures, one partial detuned
        pent = [77, 79, 81, 84, 86, 89]
        t = 1.0
        while t < d - 2:
            for j in range(RNG.integers(3, 5)):
                m = pent[min(len(pent) - 1, j + RNG.integers(0, 2))]
                b = bell_note(mtof(m), 0.10, 3.5, sour=35)
                self.bed.add(a + t + j * 0.28, b * float(np.interp(ns(t), np.arange(n), e)), 1.0, 0.8)
            t += RNG.uniform(3.5, 5.0)

    def m_clinical(self, t0, t1):
        a, n, e = self.span_env(t0, t1, 1.8, 1.8)
        x = 0.25 * osc("sine", mtof(76), n) + 0.18 * osc("sine", mtof(83), n) + 0.06 * osc("sine", mtof(90) * 1.003, n)
        x += 0.18 * osc("sine", mtof(52), n)
        self.bed.add(a, x * e, 0.6, 0.25)

    def m_cycle(self, t0, t1):
        """circular ostinato: Am - F - Dm - E, endlessly round"""
        a, n, e = self.span_env(t0, t1)
        d = n / SR
        chords = [(57, 60, 64), (53, 57, 60), (50, 53, 57), (52, 56, 59)]
        step = 0.3
        t = 0.0
        k = 0
        while t < d - 0.5:
            c = chords[(k // 8) % 4]
            pat = [c[0], c[1], c[2], c[1] + 12, c[2], c[1], c[0] + 12, c[1]]
            m = pat[k % 8]
            gain = float(np.interp(ns(t), np.arange(n), e))
            self.bed.add(a + t, musicbox_note(mtof(m + 12), 0.10, 1.4) * gain, 0.8, 0.5)
            self.bed.add(a + t, pluck_note(mtof(m), 0.12, 0.8, 0.18) * gain, 1.0, 0.3)
            if k % 8 == 0:
                self.bed.add(a + t, 0.3 * pad_note(mtof(c[0] - 12), 8 * step + 1.2, 0.3, 1.2, "dark", 2, 6) * gain, 1.0, 0.3)
            t += step
            k += 1

    def m_resigned(self, t0, t1):
        a, n, e = self.span_env(t0, t1, XF, 0.1)
        d = n / SR
        x = 0.22 * pad_note(mtof(45), d, 4, 2, "dark", 2, 6) + 0.12 * pad_note(mtof(52), d, 5, 2, "dark", 2, 6)
        # slow descending low line, each note ~4.5 s, overlapping
        line = [57, 55, 53, 52, 50, 48, 47, 45, 45]
        t = 0.5
        for m in line:
            if t > d - 6:
                break
            p = deep_note(mtof(m - 12), 0.32, 7.0) + 0.5 * pad_note(mtof(m), 7.0, 1.5, 4.0, "warm", 2, 6)
            self.bed.add(a + t, lowpass(p, 1200), 1.0, 0.5)
            t += 4.5
        self.bed.add(a, x * e, 1.0, 0.4)
        # outro: when the narrator stops the mix un-ducks the bed (+9 dB); pull the layer down by
        # about that much, then let it sink to silence over the last ~10 s (cosine-ish glide)
        last = max(b["end"] for b in self.tl["beats"] if b["kind"] == "speech")
        T = self.dur
        tt = np.arange(self.n) / SR
        u = np.clip((tt - (last + 1.0)) / (T - 0.5 - (last + 1.0)), 0, 1)
        fade = np.interp(tt, [0, last - 0.3, last + 1.0, T], [1.0, 1.0, 0.42, 0.42]) * (0.5 + 0.5 * np.cos(np.pi * u)) ** 1.3
        self.bed.dry *= fade.astype(np.float32)
        self.bed.send *= fade.astype(np.float32)

    def render_bed(self):
        """render each mood into its own bus, normalise it to its target loudness, sum"""
        main = self.bed
        report = []
        for t0, t1, m in self.segs:
            if m == "silence":
                continue
            self.bed = Bus(self.n)
            fn = getattr(self, "m_" + m)
            if m == "dread" and t0 > 60:
                fn(t0, t1, song_over=True)
            else:
                fn(t0, t1)
            a, b = ns(t0), ns(min(t1, t0 + 60))
            L = loudness(self.bed.dry[a:b] + 0.6 * self.bed.send[a:b])
            g = 10 ** ((MOOD_LEVEL[m] - L) / 20)
            main.dry += g * self.bed.dry
            main.send += g * self.bed.send
            report.append(f"{m}:{L:.1f}->{MOOD_LEVEL[m]:.1f}")
        self.bed = main
        return report

    # ---------------------------------------------------------------- song
    def render_song(self):
        t0, x = render_song(self.tl["song"], self.song_end, 0, self.t_drone)
        self.song.add(t0, x, 1.0, 0.5)

    # ---------------------------------------------------------------- cues
    def render_cues(self):
        part2 = self.part2
        counts = {}
        for c in self.tl["music"]["cues"]:
            t, k = c["t"], c["kind"]
            counts[k] = counts.get(k, 0) + 1
            mood = self.mood_at(t)
            p2 = t >= part2
            if k == "high":
                # bright high note / bell on a hopeful (ironic) word
                m = {"irony": 84, "false_hope": 89, "fragile": 88}.get(mood, 86 if not p2 else 88)
                sour = 30 if mood in ("false_hope", "irony") else 0
                b = bell_note(mtof(m), 0.22, 4.0, sour) + 0.4 * bell_note(mtof(m + 7), 0.12, 4.0)
                self.cues.add(t - 0.01, b, 1.0, 0.8)
            elif k == "low":
                root = 26 if not p2 else 33
                if mood in ("drone",):
                    root = 31
                b = deep_note(mtof(root + 12), 0.5, 4.5)
                self.cues.add(t - 0.06, lowpass(b, 700), 1.0, 0.4)
            elif k == "swell":
                L = 2.6
                root = 38 if not p2 else 45
                s = np.zeros(ns(L + 0.4), np.float32)
                for m in (root, root + 7, root + 13, root + 19):
                    s += 0.3 * pad_note(mtof(m), L + 0.4, 0.05, 0.4, "warm", 2, 12)
                nn = len(s)
                sh = curve(nn, [(0, 0.0), (L * 0.6, 0.25), (L, 1.0), (L + 0.08, 0.9), (L + 0.4, 0.0)]) ** 1.5
                s = tv_lowpass(s, 300 + 2200 * sh) * sh
                s += 0.25 * whoosh(L + 0.4, 200, 1200, 0.5) * sh
                self.cues.add(t - L, s, 1.0, 0.6)
            elif k == "light":
                m = 81 if not p2 else 88
                self.cues.add(t, pluck_note(mtof(m), 0.25, 1.4, 0.3) + 0.5 * musicbox_note(mtof(m), 0.12, 1.4), 1.0, 0.6)
            elif k == "hit":
                # the 'cease' hit lands exactly on the song cut
                th = self.song_end if c["word"] == "cease" or abs(t - self.song_end) < 0.5 else t
                self.hit.add(th, felt_hit(46.0, 0.30, 2.4), 1.0, 0.25)
        return counts

    # ---------------------------------------------------------------- ambience beds
    def render_amb(self):
        n = self.n
        ts = np.arange(n) / SR
        se = self.song_end
        p2 = self.part2
        # ---- wind: Part I, from 0.0, gusting; fades out going into Part II
        nI = ns(p2 + 2.0)
        w = brown(nI, 0.97)
        gust = smooth_rand(nI, 0.18, 0.0, 1.0, seed=7) ** 1.5
        cf = 260 + 700 * gust
        wind = tv_lowpass(w, cf)
        wind = highpass(wind, 70)
        whistle = reson(noise(nI), 620, 12) * gust ** 2 * 0.25 + reson(noise(nI), 910, 15) * gust ** 3 * 0.15
        wind = wind / (np.std(wind) + 1e-9) * (0.55 + 0.45 * gust) + whistle / (np.std(whistle) + 1e-9) * 0.25
        g = curve(nI, [(0, 1.0), (p2 - 4.0, 1.0), (p2 + 1.8, 0.0), (p2 + 2.0, 0.0)])
        g[:ns(0.05)] *= rcos_in(ns(0.05))
        # the song cut: the wind thins at the same instant (near-silence), then slowly returns
        g *= curve(nI, [(0, 1.0), (se - 0.005, 1.0), (se + 0.05, 0.5), (se + 3.5, 0.55), (se + 9.0, 1.0), (p2 + 2, 1.0)])
        self.amb.add(0, 0.030 * wind * g, 1.0, 0.0)
        self.wind_gain = 0.030
        del w, wind, whistle
        # ---- distant discordant hum: two close tones beating, from 0.0 in the bleak opening
        nh = ns(se)
        th = np.arange(nh) / SR
        hum = (np.sin(2 * np.pi * 110.0 * th) + np.sin(2 * np.pi * 111.4 * th + 1) + 0.4 * np.sin(2 * np.pi * 233.1 * th)
               + 0.35 * np.sin(2 * np.pi * 220.0 * th + 2)).astype(np.float32)
        hum *= smooth_rand(nh, 0.1, 0.6, 1.0, seed=9)
        hg = curve(nh, [(0, 1.0), (21.0, 1.0), (26.0, 0.35), (se, 0.35)])
        hg[:ns(0.03)] *= rcos_in(ns(0.03))
        hg[-ns(0.012):] *= rcos_in(ns(0.012))[::-1]
        self.amb.add(0, 0.006 * lowpass(hum, 500) * hg, 1.0, 0.3)
        # ---- engine + road noise while the bus is on screen (engine cue -> song cut)
        ev = {e["name"]: e["t"] for e in self.tl["sfx"]}
        te = ev["engine"]
        ne = ns(se - te)
        tt = np.arange(ne) / SR
        rpm = 1 + 0.04 * smooth_rand(ne, 0.3, -1, 1, seed=11)
        # the engine labours a touch harder through the loud song and toward the cliff
        rpm *= curve(ne, [(0, 1.0), (60 - te, 1.0), (100 - te, 1.05), (se - te, 1.1)])
        f0 = 31.0 * rpm
        ph = 2 * np.pi * np.cumsum(f0) / SR
        eng = np.zeros(ne, np.float32)
        for h, a_ in ((1, 1.0), (2, 0.7), (3, 0.45), (4, 0.25), (6, 0.12)):
            eng += (a_ * np.sin(h * ph + h)).astype(np.float32)
        eng *= (1 + 0.25 * np.sin(ph / 2)).astype(np.float32)           # firing irregularity
        road = lowpass(brown(ne, 0.98), 300)
        road = road / (np.std(road) + 1e-9)
        hiss = bandpass(noise(ne), 400, 1400) * 0.25
        eng = lowpass(eng, 260) * 0.6 + road * 0.7 + hiss
        eg = curve(ne, [(0, 0.0), (1.5, 1.0), (se - te, 1.0)])
        eg[-ns(0.015):] *= rcos_in(ns(0.015))[::-1]                    # stops dead with the song
        self.amb.add(te, 0.010 * eng * eg, 1.0, 0.0)
        del eng, road, hiss
        # ---- Part II: slow dripping water, continuous to the end
        t = p2 + 0.05
        drips = 0
        while t < self.dur - 2.0:
            big = RNG.random() < 0.25
            f = RNG.uniform(900, 1500) if not big else RNG.uniform(600, 900)
            self.amb.add(t, self.drip(f, 0.9 if big else RNG.uniform(0.4, 0.7)), 1.0, 0.9)
            t += RNG.uniform(1.1, 2.6)
            drips += 1
        self.n_drips = drips
        # ---- rain beds
        self.render_rain(ev)

    def drip(self, f, vel):
        n = ns(0.5)
        t = np.arange(n, dtype=np.float64) / SR
        inst = f * (1 + 0.9 * (1 - np.exp(-t / 0.012)))           # upward 'bloop'
        ph = 2 * np.pi * np.cumsum(inst) / SR
        x = np.exp(-t / 0.035) * np.sin(ph)
        x += 0.3 * np.exp(-t / 0.002) * RNG.standard_normal(n)   # contact tick
        x = lowpass(x.astype(np.float32), 5000)
        return (0.045 * vel * x * env_ar(n, 0.001, 0.05)).astype(np.float32)

    def rain_bed(self, n, density, heavy):
        """steady rain: soft filtered noise + many small droplet ticks (no hiss above ~5 kHz)"""
        base = bandpass(noise(n), 350, 4200, 2)
        base = lowpass(base, 3200)
        base = base / (np.std(base) + 1e-9)
        drops = np.zeros(n, np.float32)
        k = int(n / SR * density)
        pos = RNG.integers(0, n - 200, k)
        amp = RNG.uniform(0.2, 1.0, k) ** 2
        drops[pos] = amp
        drops = signal.lfilter([1.0], [1.0, -0.82], drops).astype(np.float32)
        drops = bandpass(drops, 1200, 4500)
        drops = drops / (np.std(drops) + 1e-9)
        x = 0.6 * base + 0.6 * drops
        if heavy:
            roar = lowpass(brown(n, 0.9), 500)
            x += heavy * roar / (np.std(roar) + 1e-9)
        return x

    def render_rain(self, ev):
        rains = sorted(e["t"] for e in self.tl["sfx"] if e["name"] == "rain")
        tor = ev["torrent"]
        fh = next(a for a, b, m in self.segs if m == "false_hope")
        # 1) main storm: rain -> heavier -> torrent -> splash -> dissolves as the 'sun' appears
        t0 = rains[0]
        t1 = fh + 6.0
        n = ns(t1 - t0)
        x = self.rain_bed(n, 140, 0.0)
        heavy = self.rain_bed(n, 420, 1.2)
        d = n / SR
        g1 = curve(n, [(0, 0), (2.5, 0.8), (tor - t0 - 6, 1.0), (tor - t0, 0.7), (fh - t0, 0.5), (t1 - t0, 0.0)])
        g2 = curve(n, [(0, 0), (tor - t0 - 12, 0.0), (tor - t0 - 2, 0.6), (tor - t0 + 1.5, 1.3), (ev["splash"] - t0, 1.4),
                       (ev["splash"] - t0 + 1.5, 0.6), (fh - t0, 0.25), (fh - t0 + 3.5, 0.0), (d, 0.0)])
        self.amb.add(t0, 0.010 * (x * g1 + heavy * g2), 1.0, 0.2)
        # 2) the rain returns in the cycle ("the climb, the rain, the fall")
        t0 = rains[1]
        n = ns(8.0)
        g = curve(n, [(0, 0), (1.2, 0.9), (4.5, 0.9), (8.0, 0)])
        self.amb.add(t0, 0.009 * self.rain_bed(n, 200, 0.4) * g, 1.0, 0.2)
        # 3) final rain: "the suffering ... remain" -> continues gently into the fade-out
        t0 = rains[2]
        n = ns(self.dur - t0)
        d = n / SR
        g = curve(n, [(0, 0), (3.0, 0.7), (d - 9.0, 0.7), (d - 0.3, 0.0), (d, 0.0)])
        self.amb.add(t0, 0.009 * self.rain_bed(n, 150, 0.0) * g, 1.0, 0.2)

    # ---------------------------------------------------------------- one-shot events
    def ev_wheel_tick(self):
        """wheel ticks: a clicking joint on each revolution (~0.42 s), rolling for ~7 s"""
        L = 7.0
        out = np.zeros(ns(L), np.float32)
        t = 0.05
        while t < L - 0.3:
            n = ns(0.12)
            tt = np.arange(n) / SR
            c = noise(n) * np.exp(-tt / 0.004).astype(np.float32)
            c = bandpass(c, 900, 3500) + 0.6 * (np.sin(2 * np.pi * 1850 * tt) * np.exp(-tt / 0.02)).astype(np.float32)
            g = min(1.0, t / 0.5) * min(1.0, (L - t) / 2.5)
            i = ns(t)
            out[i:i + n] += 0.5 * c[: len(out) - i] * g
            t += 0.42 + RNG.normal(0, 0.006)
        return out * 0.035

    def ev_creak(self):
        """seat creak: stick-slip pulse train through wooden/leather resonances"""
        L = 1.5
        n = ns(L)
        x = np.zeros(n, np.float32)
        rate = 60 + 70 * np.sin(np.linspace(0, np.pi, n)) + 20 * smooth_rand(n, 6, -1, 1)
        ph = np.cumsum(rate) / SR
        idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
        x[idx] = RNG.uniform(0.5, 1.0, len(idx))
        y = reson(x, 520, 8) + 0.7 * reson(x, 1250, 10) + 0.3 * reson(x, 2300, 12)
        y *= env_ar(n, 0.15, 0.4)
        return lowpass(y, 4000) * 0.05

    def ev_gears(self):
        """gears grinding: tooth-rate modulated metallic noise + inharmonic ring"""
        L = 2.8
        n = ns(L)
        t = np.arange(n) / SR
        tooth = 38 + 8 * np.sin(2 * np.pi * 0.7 * t)
        ph = 2 * np.pi * np.cumsum(tooth) / SR
        am = (0.5 + 0.5 * np.sign(np.sin(ph))) ** 1
        grit = bandpass(noise(n), 700, 3000) * am.astype(np.float32)
        ring = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((413, 0.5), (871, 0.3), (1377, 0.2))).astype(np.float32)
        y = grit + 0.4 * ring * (0.6 + 0.4 * am).astype(np.float32)
        y += 0.8 * lowpass(noise(n), 200) * am.astype(np.float32)
        return (y * env_ar(n, 0.25, 0.8) * 0.018).astype(np.float32)

    def ev_screech(self):
        """metal against metal: a wobbling high squeal (kept soft, below 4 kHz)"""
        L = 2.0
        n = ns(L)
        t = np.arange(n) / SR
        f = 1650 * (1 + 0.03 * np.sin(2 * np.pi * 7.3 * t) + 0.05 * smooth_rand(n, 4, -1, 1)) * (1 - 0.08 * t / L)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = (np.sin(ph) + 0.35 * np.sin(2 * ph + 0.4) + 0.15 * np.sin(1.5 * ph)).astype(np.float32)
        y *= (0.6 + 0.4 * smooth_rand(n, 12, 0, 1))
        y += 0.4 * bandpass(noise(n), 1200, 2600)
        y = lowpass(y, 3800)
        return (y * env_ar(n, 0.08, 0.7) * 0.012).astype(np.float32)

    def ev_snap(self):
        """brake cable snap: sharp crack + twang dropping in pitch + small whip"""
        L = 2.2
        n = ns(L)
        t = np.arange(n, dtype=np.float64) / SR
        crack = highpass(noise(n), 800) * np.exp(-t / 0.006).astype(np.float32)
        f = 190 * (1 - 0.35 * (1 - np.exp(-t / 0.25)))
        ph = 2 * np.pi * np.cumsum(f) / SR
        tw = sum(a * np.sin(k * ph) for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (5, 0.15))) * np.exp(-t / 0.45)
        tw *= (1 + 0.3 * np.sin(2 * np.pi * 9 * t))
        whip = whoosh(0.35, 600, 3000, 0.5)
        y = 1.2 * crack + 0.5 * tw.astype(np.float32)
        y[:len(whip)] += 0.6 * whip
        return (lowpass(y, 6000) * env_ar(n, 0.001, 0.5) * 0.06).astype(np.float32)

    def ev_rumble(self):
        L = 5.5
        n = ns(L)
        t = np.arange(n) / SR
        y = lowpass(brown(n, 0.99), 110, 4) * 1.5 + 0.8 * np.sin(2 * np.pi * 33 * t + 2 * smooth_rand(n, 1, -1, 1)).astype(np.float32)
        return (y * curve(n, [(0, 0), (1.6, 1.0), (3.0, 0.8), (L, 0)]) * 0.03).astype(np.float32)

    def ev_skitter(self, vel=1.0, L=1.1):
        """tiny legs: irregular bursts of very short, soft ticks"""
        n = ns(L)
        x = np.zeros(n, np.float32)
        t = 0.02
        while t < L - 0.05:
            i = ns(t)
            x[i] = RNG.uniform(0.3, 1.0)
            t += RNG.uniform(0.012, 0.045) if RNG.random() > 0.12 else RNG.uniform(0.08, 0.18)
        y = bandpass(signal.lfilter([1], [1, -0.6], x).astype(np.float32), 2000, 5500)
        y += 0.5 * bandpass(x, 600, 1500)
        return y * env_ar(n, 0.05, 0.25) * 0.09 * vel

    def ev_squeak(self):
        """slipping legs: two short descending squeaks + a little scrabble"""
        out = np.zeros(ns(1.4), np.float32)
        for t0, f0 in ((0.0, 2100), (0.32, 1750)):
            n = ns(0.28)
            t = np.arange(n) / SR
            f = f0 * (1 - 0.3 * t / 0.28) * (1 + 0.02 * np.sin(2 * np.pi * 28 * t))
            ph = 2 * np.pi * np.cumsum(f) / SR
            y = (np.sin(ph) + 0.2 * np.sin(2 * ph)).astype(np.float32) * env_ar(n, 0.02, 0.1)
            i = ns(t0)
            out[i:i + n] += y
        sk = self.ev_skitter(0.8, 0.8)
        out = out * 0.010
        out[ns(0.5):ns(0.5) + len(sk)] += 0.8 * sk[: len(out) - ns(0.5)]
        return out

    def ev_splash(self):
        L = 2.0
        n = ns(L)
        t = np.arange(n, dtype=np.float64) / SR
        burst = bandpass(noise(n), 300, 4000) * np.exp(-t / 0.18).astype(np.float32)
        thud = lowpass(noise(n), 150) * np.exp(-t / 0.08).astype(np.float32) * 2.5
        y = burst + thud
        y = tv_lowpass(y, 4500 - 3500 * np.linspace(0, 1, n) ** 0.5)
        return (y * env_ar(n, 0.006, 0.8) * 0.06).astype(np.float32)

    def ev_shimmer(self):
        """the sun: a glistening upward cascade of soft high sines"""
        L = 3.2
        out = np.zeros(ns(L), np.float32)
        notes = [84, 88, 91, 93, 96, 98, 100, 103]
        for j, m in enumerate(notes):
            b = bell_note(mtof(m), 0.25 * (1 - j / 12), 2.4)
            i = ns(j * 0.11)
            mm = min(len(b), len(out) - i)
            out[i:i + mm] += b[:mm]
        out = lowpass(out, 7500)
        return out * 0.05

    def ev_pill(self):
        """blister-pack pop + the pill's tiny rattle"""
        n = ns(0.6)
        t = np.arange(n, dtype=np.float64) / SR
        pop = (np.sin(2 * np.pi * 780 * t * (1 + 0.5 * np.exp(-t / 0.01))) * np.exp(-t / 0.025)).astype(np.float32)
        pop += bandpass(noise(n), 1500, 5000) * np.exp(-t / 0.004).astype(np.float32)
        r = np.zeros(n, np.float32)
        for dt in (0.11, 0.17, 0.21, 0.25):
            i = ns(dt)
            r[i:i + ns(0.01)] += bandpass(noise(ns(0.01)), 2500, 6000) * RNG.uniform(0.2, 0.5)
        return (0.05 * (pop + r)).astype(np.float32)

    def render_events(self):
        ev = self.events
        done = []
        for e in self.tl["sfx"]:
            t, nm = e["t"], e["name"]
            if nm == "wheel_tick":
                ev.add(t, self.ev_wheel_tick(), 1.0, 0.1)
            elif nm == "creak":
                ev.add(t, self.ev_creak(), 1.0, 0.25)
            elif nm == "gears":
                ev.add(t, self.ev_gears(), 1.0, 0.2)
            elif nm == "screech":
                ev.add(t, self.ev_screech(), 1.0, 0.3)
            elif nm == "snap":
                ev.add(t, self.ev_snap(), 1.0, 0.3)
            elif nm == "whoosh":
                ev.add(t - 0.6, whoosh(2.2, 160, 1600, 0.06), 1.0, 0.2)
            elif nm == "rumble":
                ev.add(t, self.ev_rumble(), 1.0, 0.1)
            elif nm == "skitter":
                ev.add(t, self.ev_skitter(), 1.0, 0.25)
            elif nm == "squeak":
                ev.add(t, self.ev_squeak(), 1.0, 0.25)
            elif nm == "splash":
                ev.add(t - 0.05, self.ev_splash(), 1.0, 0.3)
            elif nm == "torrent":
                ev.add(t - 1.2, whoosh(3.0, 120, 900, 0.10), 1.0, 0.2)
            elif nm == "shimmer":
                ev.add(t, self.ev_shimmer(), 1.0, 0.7)
            elif nm == "pill":
                ev.add(t, self.ev_pill(), 1.0, 0.2)
            else:
                continue      # beds (wind, hum, engine, drip, rain) and song_start/stop handled elsewhere
            done.append((round(t, 2), nm))
        # occasional extra faint skittering in Part II (the stage direction), in speech pauses
        extra = []
        for b in self.tl["beats"]:
            if b["part"] == 1 and b["kind"] == "speech" and b["id"] in (19, 22, 25, 30, 32, 36):
                t = b["end"] + 0.1
                ev.add(t, self.ev_skitter(0.55, 0.8), 1.0, 0.25)
                extra.append(round(t, 2))
        return done, extra

    # ---------------------------------------------------------------- reverb + output
    def finish(self):
        ir_long = make_ir(4.0, 3.2, 4500, 1000, 0.03, seed=3)
        ir_song = make_ir(1.6, 1.1, 4000, 1400, 0.015, seed=4)
        ir_s = make_ir(1.4, 0.9, 3000, 900, 0.01, seed=5)
        out = {}
        for name, bus, irx, wet in (("bed", self.bed, ir_long, 0.9), ("cues", self.cues, ir_long, 0.9),
                                    ("song", self.song, ir_song, 0.6), ("amb", self.amb, ir_s, 0.6),
                                    ("events", self.events, ir_s, 0.6)):
            w = signal.oaconvolve(bus.send, irx.astype(np.float32))[: self.n].astype(np.float32)
            if name == "song":
                # the cut: the song's room tail dies within ~0.35 s
                ie = ns(self.song_end)
                k = ns(0.35)
                w[ie:ie + k] *= rcos_in(k)[::-1] ** 2
                w[ie + k:] = 0
            out[name] = bus.dry + wet * w
        # the moment after the cut: everything but the wind (amb) and the 'cease' hit (cues) is silent
        ie = ns(self.song_end)
        for name in ("bed", "song", "events", "cues"):
            nz = ns(0.03)
            out[name][ie:ie + nz] *= rcos_in(nz)[::-1]
            urgent0 = next(a for a, b, m in self.segs if m == "urgent") - 0.8
            out[name][ie + nz:ns(urgent0)] = 0
        w = signal.oaconvolve(self.hit.send, ir_s.astype(np.float32))[: self.n].astype(np.float32)
        out["cues"] += self.hit.dry + 0.6 * w
        return out


# ==========================================================================
def write_wav(path, x, sr):
    y = (np.clip(x, -1, 1) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())


def to_out_rate(x, dur):
    y = signal.resample_poly(x, OUT_SR // SR, 1).astype(np.float32)
    n = int(round(dur * OUT_SR))
    if len(y) < n:
        y = np.pad(y, (0, n - len(y)))
    return y[:n]


def main():
    t_all = time.time()
    tl = json.load(open(TIMELINE))
    os.makedirs(WORK, exist_ok=True)
    S = Score(tl)
    print(f"duration {S.dur:.3f}s, songEnd {S.song_end:.3f}s, drone passage from {S.t_drone:.2f}s, Part II at {S.part2:.2f}s")
    t0 = time.time()
    rep = S.render_bed()
    print(f"bed: {len(S.segs)} mood segments ({time.time() - t0:.1f}s), loudness normalised (LUFS):")
    print("   ", ", ".join(rep))
    t0 = time.time()
    S.render_song()
    print(f"song: {len(tl['song'])} notes ({time.time() - t0:.1f}s)")
    print("cues:", S.render_cues())
    t0 = time.time()
    S.render_amb()
    print(f"amb beds: wind, hum, engine, {S.n_drips} drips, rain x3 ({time.time() - t0:.1f}s)")
    done, extra = S.render_events()
    print(f"events: {len(done)} placed; extra faint skitters at {extra}")
    buses = S.finish()
    nf = ns(1.0)
    for k, b in buses.items():
        b[-nf:] *= rcos_in(nf)[::-1]
        np.save(os.path.join(WORK, f"{k}.npy"), to_out_rate(b, S.dur))
        x = b.astype(np.float64)
        print(f"  {k:6s}: peak {20 * np.log10(np.abs(x).max() + 1e-12):6.1f} dBFS, rms {20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12):6.1f} dBFS")
    print(f"score done in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
