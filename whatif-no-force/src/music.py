"""Procedural score for video 2: Rhodes, felt piano, upright, brushes, strings, celesta.

render_score(tl) returns stereo buses (music, accents) as reverberated stereo
arrays plus the harmony track used to keep word accents consonant.

Moods come from direction.MUSIC; each mood instance renders into its own
buffer, is loudness-normalized to its target, and crossfades into the next.
"""
import math

import numpy as np
from scipy import signal
import pyloudnorm

from audio_dsp import (SR, bp, convolve, env_points, fade_edges, lp, hp, make_ir, midi_hz, ns, pan, saw, sine,
                       smooth_curve, square, tarr, tri, eq)
import anchors
import direction

LOW_SR = 16000  # pads / strings / drones are synthesized here and upsampled
UP = SR // LOW_SR

# ----------------------------------------------------------------------------
# harmony
# ----------------------------------------------------------------------------

PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
      "Bb": 10, "B": 11}
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10],
        "9": [0, 4, 7, 10, 14], "m9": [0, 3, 7, 10, 14], "7sus4": [0, 5, 7, 10],
        "add9": [0, 4, 7, 14], "madd9": [0, 3, 7, 14], "sus4": [0, 5, 7], "sus2": [0, 2, 7], "6": [0, 4, 7, 9],
        "dim": [0, 3, 6]}


def chord(name):
    bass = None
    if "/" in name:
        name, b = name.split("/")
        bass = PC[b]
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    q = name[len(root):]
    r = PC[root]
    return dict(name=name + ("/" + [k for k, v in PC.items() if v == bass][0] if bass is not None else ""),
                root=r, ivs=QUAL[q], bass=r if bass is None else bass,
                pcs=sorted({(r + i) % 12 for i in QUAL[q]}))


def tones(ch, lo, hi):
    return [m for m in range(lo, hi + 1) if m % 12 in ch["pcs"]]


def bass_note(ch, lo=31, hi=44):
    for m in range(lo, hi + 1):
        if m % 12 == ch["bass"]:
            return m
    return lo


def root_note(ch, lo, hi):
    for m in range(lo, hi + 1):
        if m % 12 == ch["root"]:
            return m
    return lo


def voicing(ch, center=60, n=4):
    cand = tones(ch, center - 9, center + 12)
    cand.sort(key=lambda m: abs(m - center - 1.5))
    v = sorted(cand[:n])
    return v


DMAJ = [2, 4, 6, 7, 9, 11, 1]
DMIN = [2, 4, 5, 7, 9, 10, 0]
FMAJ = [5, 7, 9, 10, 0, 2, 4]

# ----------------------------------------------------------------------------
# instruments
# ----------------------------------------------------------------------------

_cache = {}


def piano(m, vel=0.5, dur=3.0, bright=0.5):
    key = ("pno", m, round(vel, 2), round(min(dur, 9.0) * 4) / 4, round(bright, 1))
    if key in _cache:
        return _cache[key]
    f0 = midi_hz(m)
    nat = float(np.clip(10.0 * (65.0 / f0) ** 0.5, 1.6, 10.0))
    L = min(dur, nat) + 0.4
    n = ns(L)
    t = tarr(n).astype(np.float32)
    rng = np.random.default_rng(int(m * 131 + vel * 1000))
    br = 0.3 + 0.55 * vel * (0.6 + 0.8 * bright)
    B = 0.00018 * (f0 / 262.0) ** 0.6
    out = np.zeros(n, np.float32)
    norm = 0.0
    K = int(min(18, 9000 / f0))
    for k in range(1, K + 1):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 11000:
            break
        strike = abs(math.sin(math.pi * k * 0.117)) + 0.05
        ak = strike / k ** (1.75 - 0.7 * br)
        T1 = nat * 0.30 / (1 + 0.6 * (k - 1))
        T2 = nat / (1 + 0.28 * (k - 1))
        env = 0.62 * np.exp(-6.9 * t / T1) + 0.38 * np.exp(-6.9 * t / T2)
        det = 1 + 0.00042 * (1 + 0.6 * rng.random())
        p1, p2 = rng.uniform(0, 2 * np.pi, 2)
        w = np.float32(2 * np.pi * fk)
        out += np.float32(ak) * env * (np.sin(w * t + np.float32(p1)) + 0.75 * np.sin(w * np.float32(det) * t + np.float32(p2)))
        norm += ak * ak
    out /= math.sqrt(norm) * 1.6
    a = ns(0.003 + 0.010 * (1 - vel))
    out[:a] *= np.sin(np.linspace(0, np.pi / 2, a, dtype=np.float32)) ** 2
    th = ns(0.035)
    thump = lp(rng.standard_normal(th), 300 + 700 * vel, 2) * np.exp(-np.arange(th) / ns(0.007))
    out[:th] += (0.05 * vel * thump).astype(np.float32)
    if dur < nat:
        r0 = ns(dur)
        r = ns(0.32)
        if r0 < n:
            seg = min(r, n - r0)
            out[r0:r0 + seg] *= np.cos(np.linspace(0, np.pi / 2, seg, dtype=np.float32)) ** 2
            out[r0 + seg:] = 0
    out = lp(out, 700 + 5200 * br ** 1.6, 2).astype(np.float32)
    out *= vel ** 1.3
    fade_edges(out, 0.0, 0.05)
    _cache[key] = out
    return out


def celesta(m, vel=0.5, ring=2.4):
    key = ("cel", m, round(vel, 2), ring)
    if key in _cache:
        return _cache[key]
    f0 = midi_hz(m)
    n = ns(ring)
    t = tarr(n)
    sc = (523.0 / f0) ** 0.35
    out = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.5), (2.0, 0.26, 0.6), (3.0, 0.08, 0.3), (4.17, 0.05, 0.18), (5.4, 0.02, 0.1)):
        if f0 * r < 14000:
            out += a * np.exp(-t / (d * sc)) * np.sin(2 * np.pi * f0 * r * t + r)
    rng = np.random.default_rng(m)
    click = hp(rng.standard_normal(ns(0.004)), 3000) * np.linspace(1, 0, ns(0.004))
    out[:len(click)] += 0.04 * click
    out[:ns(0.0015)] *= np.linspace(0, 1, ns(0.0015))
    out *= 0.45 * vel ** 1.2
    fade_edges(out, 0.0, 0.08)
    _cache[key] = out
    return out


def glock(m, vel=0.5, ring=3.0):
    key = ("glk", m, round(vel, 2), ring)
    if key in _cache:
        return _cache[key]
    f0 = midi_hz(m)
    n = ns(ring)
    t = tarr(n)
    out = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 2.0), (2.756, 0.38, 0.7), (5.404, 0.16, 0.3), (8.933, 0.06, 0.12)):
        if f0 * r < 15000:
            out += a * np.exp(-t / d) * np.sin(2 * np.pi * f0 * r * t)
    out[:ns(0.001)] *= np.linspace(0, 1, ns(0.001))
    out *= 0.4 * vel ** 1.2
    fade_edges(out, 0.0, 0.1)
    _cache[key] = out
    return out


def pluck(m, vel=0.6, t60=0.5, bright=0.5, length=None):
    """Karplus-Strong with an all-pass fractional delay for exact tuning."""
    key = ("plk", m, round(vel, 2), round(t60, 2), round(bright, 1))
    if key in _cache:
        return _cache[key]
    f0 = midi_hz(m)
    N = SR / f0
    Ld = int(math.floor(N - 0.5))
    frac = N - Ld - 0.5
    c = (1 - frac) / (1 + frac)
    g = 0.001 ** (1.0 / (f0 * t60))
    g = min(g, 0.9999)
    a = np.zeros(Ld + 3)
    a[0] = 1.0
    a[1] = c
    a[Ld] -= 0.5 * g * c
    a[Ld + 1] -= 0.5 * g * (1 + c)
    a[Ld + 2] -= 0.5 * g
    b = np.array([1.0, c])
    n = ns(length or min(3.0, t60 * 1.3 + 0.1))
    rng = np.random.default_rng(int(m * 17 + vel * 100))
    x = np.zeros(n)
    exc = rng.standard_normal(Ld)
    exc = lp(exc, 800 + 6000 * bright * vel, 1)
    exc -= exc.mean()
    x[:Ld] = exc * np.hanning(Ld) ** 0.5
    y = signal.lfilter(b, a, x)
    y = eq(y, ("peak", 280, 1.0, 3.0), ("highshelf", 3500, 0.7, -4.0))
    y = hp(y, 60, 2)
    pk = np.max(np.abs(y)) + 1e-9
    y = y / pk * 0.5 * vel ** 1.2
    fade_edges(y, 0.0, 0.05)
    _cache[key] = y
    return y


def blip(m, dur=0.16, vel=0.6, bend=-0.03):
    """Bassoon-ish comic blip."""
    f0 = midi_hz(m)
    n = ns(dur + 0.08)
    t = tarr(n)
    f = f0 * (1 - 0.018 * np.exp(-t / 0.025)) * (1 + bend * smooth_curve(n, ns(dur * 0.6), ns(dur + 0.05)))
    src = 0.7 * square(f, n, duty=0.32) + 0.3 * saw(f, n)
    src = lp(src, 2600, 2)
    y = eq(src, ("peak", 500, 2.0, 9.0), ("peak", 1150, 3.0, 5.0), ("highpass", 90, 0.7, 0.0))
    env = env_points(n, [(0, 0), (0.012, 1), (0.04, 0.8), (dur, 0.7), (dur + 0.07, 0)])
    y = y * env
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.45 * vel
    return fade_edges(y, 0.001, 0.01)


def _low(x):
    """Upsample a LOW_SR signal to SR."""
    return signal.resample_poly(x, UP, 1, axis=-1)


def _lp_low(x, fc, order=2):
    fc = min(fc, LOW_SR * 0.45)
    return signal.sosfilt(signal.butter(order, fc, "low", fs=LOW_SR, output="sos"), x, axis=-1)


def _hp_low(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=LOW_SR, output="sos"), x, axis=-1)


def _osc_low(kind, f, n, ph=0.0):
    dt = np.broadcast_to(np.asarray(f, np.float64), (n,)) / LOW_SR
    p = (ph + np.concatenate([[0.0], np.cumsum(dt[:-1])])) % 1.0
    if kind == "saw":
        y = 2 * p - 1
        m1 = p < dt
        x = p[m1] / dt[m1]
        y[m1] -= x + x - x * x - 1
        m2 = p > 1 - dt
        x = (p[m2] - 1) / dt[m2]
        y[m2] -= x * x + x + x + 1
        return y
    if kind == "tri":
        return 4 * np.abs(p - 0.5) - 1
    return np.sin(2 * np.pi * p)


def pad(midis, dur, attack=1.5, release=2.0, bright=0.4, width=0.8, seed=0, lfo=0.12):
    """Warm analog-style pad (stereo)."""
    L = dur + release
    n = ns(L) // UP + 1
    rng = np.random.default_rng(seed)
    out = np.zeros((2, n))
    t = np.arange(n) / LOW_SR
    for i, m in enumerate(midis):
        f0 = midi_hz(m)
        for j, cents in enumerate((-7, 0, 7)):
            f = f0 * 2 ** (cents / 1200) * (1 + 0.0015 * np.sin(2 * np.pi * (0.13 + 0.05 * j) * t + rng.uniform(0, 6)))
            v = _osc_low("saw", f, n, rng.random()) * (0.5 if j == 1 else 0.38)
            p = (j - 1) * width * 0.8 + rng.uniform(-0.15, 0.15)
            th = (np.clip(p, -1, 1) + 1) * np.pi / 4
            out[0] += v * math.cos(th)
            out[1] += v * math.sin(th)
        if m > 52:
            v = _osc_low("tri", f0 / 2, n, rng.random()) * 0.25
            out += v
    fc = 500 + 2600 * bright ** 1.3
    out = _lp_low(out, fc, 2)
    out = _lp_low(out, fc * 1.6, 1)
    out = _hp_low(out, 70, 1)
    am = 1 + 0.12 * np.sin(2 * np.pi * lfo * t + rng.uniform(0, 6))
    env = np.interp(np.arange(n), np.array([0, attack, max(attack, dur), L]) * LOW_SR, [0, 1, 1, 0])
    env = env ** 1.6
    out *= env * am / (len(midis) ** 0.5 * 2.2)
    return _low(out)


def strings(midis, dur, attack=0.8, release=1.6, bright=0.5, vel=0.6, seed=0, swell=False, vib=1.0):
    """String ensemble (stereo). swell=True: crescendo over the whole note."""
    L = dur + release
    n = ns(L) // UP + 1
    rng = np.random.default_rng(seed + 991)
    out = np.zeros((2, n))
    t = np.arange(n) / LOW_SR
    vib_on = np.clip((t - 0.35) / 0.6, 0, 1)
    for m in midis:
        f0 = midi_hz(m)
        for j in range(3):
            cents = (j - 1) * 7 + rng.uniform(-2, 2)
            vr = 5.0 + rng.uniform(-0.4, 0.4)
            f = f0 * 2 ** (cents / 1200) * (1 + 0.0028 * vib * vib_on * np.sin(2 * np.pi * vr * t + rng.uniform(0, 6)))
            v = _osc_low("saw", f, n, rng.random())
            p = (j - 1) * 0.7 + rng.uniform(-0.2, 0.2)
            th = (np.clip(p, -1, 1) + 1) * np.pi / 4
            out[0] += v * math.cos(th)
            out[1] += v * math.sin(th)
    top = max(midis)
    fc = 1500 + 3000 * bright * (1 if top < 80 else 0.7)
    out = _lp_low(out, fc, 2)
    out = _hp_low(out, 110 if min(midis) > 50 else 55, 2)
    if swell:
        env = np.clip(t / max(0.05, dur), 0, 1) ** 2.2
        env = np.where(t > dur, np.clip(1 - (t - dur) / release, 0, 1), env)
    else:
        env = np.interp(np.arange(n), np.array([0, attack, max(attack, dur), L]) * LOW_SR, [0, 1, 1, 0]) ** 1.4
    out *= env * vel / (len(midis) ** 0.5 * 3.0)
    return _low(out)


def cello(m, dur, vel=0.6, attack=0.12, release=0.8, vib=1.0, seed=0):
    L = dur + release
    n = ns(L) // UP + 1
    rng = np.random.default_rng(seed + m)
    t = np.arange(n) / LOW_SR
    f0 = midi_hz(m)
    vib_on = np.clip((t - 0.25) / 0.5, 0, 1)
    y = np.zeros(n)
    for j, c in enumerate((-4, 0, 4)):
        f = f0 * 2 ** (c / 1200) * (1 + 0.0035 * vib * vib_on * np.sin(2 * np.pi * (5.0 + 0.3 * j) * t + j))
        y += _osc_low("saw", f, n, rng.random())
    y = _lp_low(y, 1500, 2)
    y = signal.sosfilt(np.concatenate([_biq_low("peak", 220, 1.0, 4.0), _biq_low("peak", 650, 1.4, 2.5)]), y)
    y = _hp_low(y, 40, 2)
    env = np.interp(np.arange(n), np.array([0, attack, max(attack, dur), L]) * LOW_SR, [0, 1, 0.9, 0]) ** 1.3
    y = y * env * vel * 0.16
    return _low(y)


def _biq_low(kind, f0, q, g):
    A = 10 ** (g / 40)
    w = 2 * np.pi * f0 / LOW_SR
    cw, sw = math.cos(w), math.sin(w)
    al = sw / (2 * q)
    b = [1 + al * A, -2 * cw, 1 - al * A]
    a = [1 + al / A, -2 * cw, 1 - al / A]
    return np.array([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]])


def drone(m, dur, vel=0.5, attack=2.0, release=3.0, cutoff=380, seed=0):
    L = dur + release
    n = ns(L) // UP + 1
    rng = np.random.default_rng(seed + 5)
    t = np.arange(n) / LOW_SR
    f0 = midi_hz(m)
    y = _osc_low("saw", f0, n, rng.random()) + _osc_low("saw", f0 * 1.0035, n, rng.random())
    if f0 / 2 > 40:
        y = y + 0.8 * _osc_low("sin", f0 / 2, n)
    y = _lp_low(y, cutoff, 2)
    y *= 1 + 0.2 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6))
    env = np.interp(np.arange(n), np.array([0, attack, max(attack, dur), L]) * LOW_SR, [0, 1, 1, 0]) ** 1.5
    y = y * env * vel * 0.25
    return _low(y)


def timpani(m, vel=0.7):
    f0 = midi_hz(m)
    n = ns(2.6)
    t = tarr(n)
    glide = 1 + 0.015 * np.exp(-t / 0.12)
    ph = 2 * np.pi * np.cumsum(f0 * glide) / SR
    y = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 1.4), (1.504, 0.5, 0.8), (1.742, 0.3, 0.6), (2.0, 0.25, 0.45), (2.245, 0.15, 0.35)):
        y += a * np.exp(-t / d) * np.sin(ph * r)
    rng = np.random.default_rng(m)
    th = lp(rng.standard_normal(ns(0.06)), 500, 2) * np.exp(-np.arange(ns(0.06)) / ns(0.012))
    y[:len(th)] += 0.6 * th
    y[:ns(0.002)] *= np.linspace(0, 1, ns(0.002))
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.5 * vel
    return fade_edges(y, 0.0, 0.1)


def heartbeat(vel=0.6):
    n = ns(0.75)
    t = tarr(n)
    y = np.zeros(n)
    for off, a in ((0.0, 1.0), (0.26, 0.7)):
        tt = np.clip(t - off, 0, None)
        e = np.where(t >= off, np.exp(-tt / 0.09) * (1 - np.exp(-tt / 0.006)), 0)
        y += a * e * np.sin(2 * np.pi * (48 + 20 * np.exp(-tt / 0.04)) * tt)
    return y / (np.max(np.abs(y)) + 1e-9) * 0.5 * vel


# ----------------------------------------------------------------------------
# section rendering
# ----------------------------------------------------------------------------

class Sec:
    def __init__(self, t0, t1, pre=2.5, post=9.0):
        self.t0, self.t1 = t0, t1
        self.a = t0 - pre
        self.n = ns(t1 + post - self.a)
        self.dry = np.zeros((2, self.n))
        self.room = np.zeros((2, self.n))
        self.hall = np.zeros((2, self.n))

    def put(self, sig, t, gain=1.0, p=0.0, room=0.0, hall=0.0):
        if gain <= 0:
            return
        st = pan(sig, p) if sig.ndim == 1 else sig
        i = ns(t - self.a)
        k0 = 0
        if i < 0:
            k0 = -i
            i = 0
        if k0 >= st.shape[1] or i >= self.n:
            return
        j = min(self.n, i + st.shape[1] - k0)
        seg = st[:, k0:k0 + (j - i)] * gain
        self.dry[:, i:j] += seg
        if room:
            self.room[:, i:j] += seg * room
        if hall:
            self.hall[:, i:j] += seg * hall


class Ctx:
    def __init__(self, tl):
        self.tl = tl
        sp = []
        for ln in tl["lines"]:
            for a, b in ln["chunks"]:
                sp.append((a - 0.08, b + 0.12))
        self.speech = sorted(sp)
        self.harmony = []  # (t0, t1, chord, scale)
        self.sfx = [(anchors.resolve(a), k) for a, k, _ in direction.SFX]

    def speaking(self, t):
        for a, b in self.speech:
            if a <= t <= b:
                return True
            if a > t:
                break
        return False

    def gaps(self, t0, t1, minlen=1.0):
        out = []
        cur = t0
        for a, b in self.speech:
            if b < t0 or a > t1:
                continue
            if a - cur >= minlen:
                out.append((cur, a))
            cur = max(cur, b)
        if t1 - cur >= minlen:
            out.append((cur, t1))
        return out

    def sfx_times(self, kind, t0=-1e9, t1=1e9):
        return [t for t, k in self.sfx if k == kind and t0 <= t <= t1]


def chord_grid(t0, t1, prog, bar, bpc=1, pre=1.0, offset=0):
    """Cycle a progression from t0 - pre; returns [(ts, te, chord)]."""
    out = []
    t = t0 - pre
    i = offset
    while t < t1 + 0.5:
        d = bar * bpc
        out.append((t, t + d, chord(prog[i % len(prog)])))
        t += d
        i += 1
    return out


def beats_in(ts, te, beat):
    k = 0
    out = []
    while ts + k * beat < te - 1e-6:
        out.append(ts + k * beat)
        k += 1
    return out


def hum(rng, s=0.008):
    return rng.uniform(-s, s)

def play_motif(S, ctx, t, beat, which, inst="piano", vel=0.4, transpose=0, gain=1.0, room=0.3, hall=0.25,
               rng=None):
    notes, rhythm = which
    tt = t
    for m, d in zip(notes, rhythm):
        mm = m + transpose
        dur = d * beat
        jitter = hum(rng, 0.01) if rng is not None else 0
        if inst == "piano":
            S.put(piano(mm, vel, dur + 0.6), tt + jitter, gain, 0.1, room, hall)
        elif inst == "celesta":
            S.put(celesta(mm, vel), tt + jitter, gain, 0.15, room, hall)
        elif inst == "rhodes":
            S.put(rhodes_st(mm, vel, dur + 0.5, mm), tt + jitter, gain, 0, room, hall)
        elif inst == "strings":
            S.put(strings([mm, mm - 12], dur + 0.1, attack=min(0.35, dur * 0.5), release=0.9, vel=vel, seed=mm),
                  tt, gain, 0, room, hall)
        tt += dur
    return tt


def lay_pad(S, chords, gain, center=57, bright=0.35, attack=1.4, release=2.2, bass=False, room=0.2, hall=0.35,
            seed=0, n=4, width=0.8):
    for i, (ts, te, ch) in enumerate(chords):
        notes = voicing(ch, center, n)
        if bass:
            notes = [bass_note(ch, 38, 50)] + notes
        S.put(pad(notes, te - ts + 0.3, attack, release, bright, width, seed + i), ts, gain, 0, room, hall)


def lay_piano_arp(S, ctx, chords, beat, gain, div=2, lo=50, hi=76, vel=0.38, pattern=None, rng=None,
                  sparse=True, bass=True, room=0.3, hall=0.18, bright=0.45, skip_prob=0.0):
    pattern = pattern or [0, 2, 1, 3, 2, 4, 3, 1]
    for ts, te, ch in chords:
        tl = tones(ch, lo, hi)
        if not tl:
            continue
        if bass:
            S.put(piano(bass_note(ch, 33, 45), vel * 1.05, te - ts + 0.5, bright), ts + hum(rng, 0.004), gain, -0.15,
                  room, hall)
        step = beat / div
        for k, bt in enumerate(beats_in(ts, te, step)):
            if bass and k == 0:
                continue
            idx = pattern[k % len(pattern)]
            m = tl[min(idx + 1, len(tl) - 1)] if len(tl) > 2 else tl[idx % len(tl)]
            spk = ctx.speaking(bt)
            if sparse and spk and (k % div != 0 or rng.random() < 0.35):
                continue
            if rng.random() < skip_prob:
                continue
            v = vel * (1.0 if k % (div * 2) == 0 else 0.82) * (0.85 if spk else 1.0) * rng.uniform(0.9, 1.05)
            S.put(piano(m, v, te - bt + 0.4, bright), bt + hum(rng), gain, rng.uniform(-0.35, 0.35), room, hall)


def lay_twinkle(S, ctx, chords, gain, rate=0.6, lo=84, hi=98, rng=None, vel=(0.18, 0.42), hall=0.55, inst="glock"):
    for ts, te, ch in chords:
        tl = tones(ch, lo, hi)
        t = ts + rng.exponential(1 / rate)
        while t < te:
            m = tl[rng.integers(len(tl))]
            v = rng.uniform(*vel) * (0.7 if ctx.speaking(t) else 1.0)
            sig = glock(m, v) if inst == "glock" else celesta(m, v)
            S.put(sig, t, gain, rng.uniform(-0.8, 0.8), 0.0, hall)
            t += rng.exponential(1 / rate)


def lay_strings(S, chords, gain, center=62, n=4, attack=1.0, release=1.8, bright=0.45, vel=0.6, room=0.15,
                hall=0.45, seed=0, swell=False, bass=False):
    for i, (ts, te, ch) in enumerate(chords):
        notes = voicing(ch, center, n)
        if bass:
            notes = [root_note(ch, 38, 49)] + notes
        S.put(strings(notes, te - ts + 0.2, attack, release, bright, vel, seed + i, swell=swell), ts, gain, 0,
              room, hall)


def lay_pizz_bass(S, chords, beat, gain, beats=(0, 2), meter=4, vel=0.6, rng=None, fifth=True, room=0.2, hall=0.1):
    for ts, te, ch in chords:
        r = bass_note(ch, 36, 47)
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if (k % meter) in beats:
                m = r if (not fifth or (k // meter + k % meter) % 2 == 0 or (k % meter) == 0) else r + 7
                S.put(pluck(m, vel * rng.uniform(0.9, 1.05), 0.55, 0.45), bt + hum(rng, 0.005), gain,
                      -0.2, room, hall)


def lay_pizz_chords(S, chords, beat, gain, beats=(1, 3), meter=4, center=62, vel=0.45, rng=None, room=0.25,
                    hall=0.1):
    for ts, te, ch in chords:
        notes = voicing(ch, center, 3)
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if (k % meter) in beats:
                for j, m in enumerate(notes):
                    S.put(pluck(m, vel * rng.uniform(0.85, 1.0), 0.3, 0.55), bt + j * 0.006 + hum(rng, 0.004),
                          gain, -0.4 + 0.4 * j, room, hall)


def lay_celesta_arp(S, ctx, chords, beat, gain, div=2, lo=74, hi=93, vel=0.32, rng=None, room=0.2, hall=0.35,
                    sparse=True, up=True):
    for ts, te, ch in chords:
        tl = tones(ch, lo, hi)
        if not tl:
            continue
        seq = tl if up else tl[::-1]
        for k, bt in enumerate(beats_in(ts, te, beat / div)):
            spk = ctx.speaking(bt)
            if sparse and spk and k % 2 == 1:
                continue
            m = seq[k % len(seq)]
            S.put(celesta(m, vel * (0.75 if spk else 1.0) * rng.uniform(0.85, 1.05)), bt + hum(rng, 0.006), gain,
                  rng.uniform(-0.5, 0.5), room, hall)


# ----------------------------------------------------------------------------
# video-2 instruments: Rhodes, upright bass, brushes, tremolo strings
# ----------------------------------------------------------------------------

def rhodes(m, vel=0.5, dur=2.0):
    """Electric-piano tine: 1:1 FM whose index decays (bark -> mellow), plus a tine ping."""
    key = ("rho", m, round(vel, 2), round(min(dur, 8.0) * 4) / 4)
    if key in _cache:
        return _cache[key]
    f0 = midi_hz(m)
    nat = float(np.clip(6.5 * (110.0 / f0) ** 0.35, 1.2, 7.5))
    L = min(dur, nat) + 0.35
    n = ns(L)
    t = tarr(n)
    idx = (0.5 + 1.5 * vel) * np.exp(-t / 0.09) + 0.22
    w = 2 * np.pi * f0 * t
    car = np.sin(w + idx * np.sin(w))
    body = 0.30 * np.sin(2 * w + 0.5 * np.sin(w)) * np.exp(-t / (nat * 0.35))
    tine = 0.18 * vel * np.sin(w * 7.08 + 1.0) * np.exp(-t / 0.045)
    env = 0.55 * np.exp(-t / (nat * 0.22)) + 0.45 * np.exp(-t / (nat * 0.75))
    y = car * env + body + tine
    y[:ns(0.002)] *= np.linspace(0, 1, ns(0.002))
    if dur < nat:
        r0, r = ns(dur), ns(0.22)
        if r0 < n:
            seg = min(r, n - r0)
            y[r0:r0 + seg] *= np.cos(np.linspace(0, np.pi / 2, seg)) ** 2
            y[r0 + seg:] = 0
    y = lp(y, 3200 + 2600 * vel, 2)
    y = hp(y, 55, 1)
    y *= 0.30 * vel ** 1.15
    fade_edges(y, 0.0, 0.04)
    _cache[key] = y
    return y


def rhodes_st(m, vel=0.5, dur=2.0, phase=0.0, depth=0.22, rate=4.6):
    """Rhodes with the classic stereo tremolo (auto-pan)."""
    y = rhodes(m, vel, dur)
    t = tarr(len(y))
    s = np.sin(2 * np.pi * rate * t + phase)
    return np.stack([y * (1 + depth * s), y * (1 - depth * s)]) * 0.75


def upright(m, vel=0.6, dur=1.2):
    key = ("upr", m, round(vel, 2), round(min(dur, 3.0) * 4) / 4)
    if key in _cache:
        return _cache[key]
    y = pluck(m, vel, t60=1.25, bright=0.2, length=min(2.6, dur + 0.6)).copy()
    y = eq(y, ("peak", 105, 0.9, 4.0), ("peak", 700, 1.2, -3.0), ("highshelf", 1600, 0.7, -7.0))
    if dur + 0.15 < len(y) / SR:
        r0 = ns(dur)
        r = min(ns(0.15), len(y) - r0)
        y[r0:r0 + r] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 2
        y[r0 + r:] = 0
    _cache[key] = y
    return y


def brush_swish(vel=0.5, dur=0.35, seed=0):
    rng = np.random.default_rng(9000 + seed)
    n = ns(dur)
    y = lp(bp(rng.standard_normal(n), 1500, 7000, 2), 5000, 2)  # soft, dark sweep
    env = env_points(n, [(0, 0), (dur * 0.55, 1), (dur, 0)]) ** 1.5
    return y * env * 0.2 * vel


def brush_tap(vel=0.5, seed=0):
    rng = np.random.default_rng(9500 + seed)
    n = ns(0.12)
    y = bp(rng.standard_normal(n), 1500, 7000, 2) * np.exp(-tarr(n) / 0.03)
    return y * 0.25 * vel


def trem_strings(midis, dur, rate=8.0, depth=0.55, **kw):
    s = strings(midis, dur, **kw)
    t = tarr(s.shape[1])
    mod = 1 - depth * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t))
    return s * mod[None, :]


# ----------------------------------------------------------------------------
# the Hale & Kai motif: a question (rising, unresolved) and an answer (falling home)
# ----------------------------------------------------------------------------

MOTIF_Q_MIN = ([69, 72, 74, 76], [0.5, 0.5, 0.5, 1.5])
MOTIF_A_MIN = ([77, 76, 74], [0.5, 0.5, 2.0])
MOTIF_Q_MAJ = ([72, 74, 77, 79], [0.5, 0.5, 0.5, 1.5])
MOTIF_A_MAJ = ([81, 79, 77], [0.5, 0.5, 2.0])
MOTIF_MIN = (MOTIF_Q_MIN[0] + MOTIF_A_MIN[0], MOTIF_Q_MIN[1] + MOTIF_A_MIN[1])
MOTIF_MAJ = (MOTIF_Q_MAJ[0] + MOTIF_A_MAJ[0], MOTIF_Q_MAJ[1] + MOTIF_A_MAJ[1])


def W(lid, word, which="start", off=0.0, nth=0):
    return anchors.resolve(anchors.Wd(lid, word, which, off, nth))


def lay_rhodes_chords(S, ctx, chords, beat, gain, center=62, n=4, vel=0.32, stab=True, rng=None, room=0.25,
                      hall=0.22):
    for i, (ts, te, ch) in enumerate(chords):
        notes = voicing(ch, center, n)
        for j, m in enumerate(notes):
            S.put(rhodes_st(m, vel, min(te - ts, beat * 2.2) + 0.2, i * 1.3 + j), ts + 0.011 * j + hum(rng, 0.004),
                  gain, 0, room, hall)
        if stab:
            t2 = ts + 1.5 * beat
            if t2 < te - 0.1 and (not ctx.speaking(t2) or rng.random() < 0.25):
                for j, m in enumerate(notes[1:]):
                    S.put(rhodes_st(m, vel * 0.72, beat * 0.45, i + j + 5), t2 + 0.008 * j, gain, 0, room, hall)


def lay_upright(S, chords, beat, gain, vel=0.55, fifth=True, rng=None):
    for ts, te, ch in chords:
        r = bass_note(ch, 33, 45)
        S.put(upright(r, vel * rng.uniform(0.92, 1.04), min(te - ts, beat * 1.9)), ts + hum(rng, 0.004), gain, -0.12,
              0.2, 0.06)
        if fifth and te - ts > 2.5 * beat:
            f = r + 7 if r + 7 <= 47 else r - 5
            S.put(upright(f, vel * 0.88, beat * 1.8), ts + 2 * beat + hum(rng, 0.004), gain, -0.12, 0.2, 0.06)


# ----------------------------------------------------------------------------
# moods
# ----------------------------------------------------------------------------

def m_rain_night(S, ctx, rng, inst):
    beat = 60 / 62
    bar = beat * 4
    prog = ["Dm9", "Bbmaj7", "Gm7", "A7sus4", "Dm9", "Bbmaj7", "Gm7", "A7"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.0)
    ctx.harmony += [(a, b, c, DMIN) for a, b, c in ch]
    for i, (ts, te, chn) in enumerate(ch):
        for j, m in enumerate(voicing(chn, 60, 4)):
            S.put(rhodes_st(m, 0.30, te - ts + 0.4, i * 0.9 + j), max(0.02, ts) + 0.014 * j, 1.0, 0, 0.25, 0.32)
        S.put(upright(bass_note(chn, 33, 45), 0.48, te - ts), max(0.02, ts), 0.9, -0.1, 0.2, 0.1)
    lay_pad(S, ch, 0.32, center=55, bright=0.16, attack=2.6, seed=inst + 3)
    # the motif, alone in the rain: first heard here (minor)
    play_motif(S, ctx, 0.55, beat, MOTIF_MIN, "rhodes", 0.46, 0, 0.9, 0.25, 0.4, rng)
    late = [(a, b, c) for a, b, c in ch if a >= 14.0]
    lay_strings(S, late, 0.34, center=57, n=3, attack=2.6, release=2.6, bright=0.2, vel=0.4, hall=0.5,
                seed=inst + 9)


def m_conversation(S, ctx, rng, inst):
    beat = 60 / 84
    bar = beat * 4
    prog = ["Fmaj7", "Dm7", "Gm7", "C9", "Bbmaj7", "Am7", "Gm7", "C7sus4"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.6)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    lay_rhodes_chords(S, ctx, ch, beat, 1.0, center=62, n=4, vel=0.3, rng=rng)
    lay_upright(S, ch, beat, 1.0, vel=0.52, rng=rng)
    for i, (ts, te, chn) in enumerate(ch):
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if k % 2 == 1:
                S.put(brush_swish(0.55, beat * 0.8, i * 4 + k), bt - beat * 0.42, 0.33, 0.3, 0.1, 0.0)
            elif rng.random() < 0.5:
                S.put(brush_tap(0.35, i * 4 + k), bt + beat * 0.5, 0.36, 0.35, 0.1, 0.0)
    # a short Rhodes fill in the longer breaths of the conversation
    for a, b in ctx.gaps(S.t0 + 1.0, S.t1 - 0.6, 0.95)[:4]:
        chn = None
        for ts, te, c in ch:
            if ts <= a < te:
                chn = c
        if chn is None:
            continue
        tl_ = tones(chn, 67, 81)
        t = a + 0.08
        for k in range(3):
            if t > b - 0.15:
                break
            S.put(rhodes_st(tl_[(k * 2 + 1) % len(tl_)], 0.27, beat * 0.9, k), t, 0.9, 0, 0.25, 0.25)
            t += beat / 2


def m_toolkit(S, ctx, rng, inst):
    beat = 60 / 96
    bar = beat * 4
    prog = ["F", "C/E", "Dm7", "Bbmaj7", "F/A", "Gm7", "Csus4", "C"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.6)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    dur = S.t1 - S.t0
    for ts, te, chn in ch:
        tl_ = tones(chn, 60, 79)
        for k, bt in enumerate(beats_in(ts, te, beat / 2)):
            pr = float(np.clip((bt - S.t0) / dur, 0, 1))
            if ctx.speaking(bt) and k % 2 == 1 and pr < 0.45:
                continue
            m = tl_[(k * 2 + k // 4) % len(tl_)]
            S.put(pluck(m, (0.26 + 0.2 * pr) * rng.uniform(0.9, 1.05), 0.3, 0.5), bt + hum(rng, 0.004), 1.0,
                  rng.uniform(-0.45, 0.45), 0.2, 0.15)
    lay_upright(S, ch, beat, 1.0, vel=0.55, rng=rng)
    lay_pad(S, ch, 0.32, center=60, bright=0.35, attack=1.0, seed=inst + 20)
    late = [(a, b, c) for a, b, c in ch if a > S.t0 + 9]
    for i, (ts, te, chn) in enumerate(late):
        pr = float(np.clip((ts - S.t0) / dur, 0, 1))
        S.put(strings(voicing(chn, 67, 3), te - ts + 0.2, 0.9, 1.4, 0.32 + 0.3 * pr, 0.28 + 0.4 * pr, 40 + i), ts,
              1.0, 0, 0.1, 0.4)
    lay_celesta_arp(S, ctx, [(a, b, c) for a, b, c in ch if a > S.t0 + 10.5], beat, 0.65, div=2, lo=77, hi=93,
                    vel=0.25, rng=rng)


def m_cost(S, ctx, rng, inst):
    bar = 4.1
    prog = ["Dm", "Bb/D", "Gm/D", "A/C#", "Dm", "Bb", "Gm", "A"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.8)
    ctx.harmony += [(a, b, c, DMIN) for a, b, c in ch]
    for i, (ts, te, chn) in enumerate(ch):
        S.put(cello(bass_note(chn, 38, 50), te - ts + 0.2, 0.5, 0.5, 1.2, 0.8, i), ts, 1.0, -0.1, 0.1, 0.4)
        S.put(strings(voicing(chn, 57, 3), te - ts + 0.3, 1.4, 1.8, 0.24, 0.42, 60 + i), ts, 1.0, 0, 0.1, 0.5)
        S.put(piano(bass_note(chn, 26, 38), 0.34, te - ts + 0.6, 0.2), ts, 0.8, -0.1, 0.2, 0.45)
    lay_pad(S, ch, 0.28, center=50, bright=0.12, attack=2.0, seed=inst + 30)


def m_cells(S, ctx, rng, inst):
    t_open = W("L18", "opens")
    t_sick = W("L18", "sick")
    t_terr = W("L18", "terrible")
    t_conv = W("L18", "convicted")
    ch = [(S.t0 - 0.8, t_open - 1.3, chord("Bb")), (t_open - 1.3, t_open, chord("Csus4")),
          (t_open, t_open + 3.6, chord("F")), (t_open + 3.6, t_conv - 0.2, chord("C/E")),
          (t_conv - 0.2, t_sick - 0.3, chord("Dm7")), (t_sick - 0.3, t_terr - 1.8, chord("Gm")),
          (t_terr - 1.8, t_terr, chord("A7sus4")), (t_terr, S.t1 + 1.0, chord("Dm"))]
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    # rising swell into the doors opening
    S.put(strings([53, 58, 62, 65], t_open - (S.t0 - 0.6), 0.1, 0.6, 0.45, 0.6, 801, swell=True), S.t0 - 0.6, 1.0, 0,
          0.1, 0.5)
    # the bloom: warm F major, piano + strings + a shower of celesta light
    for j, m in enumerate([41, 53, 60, 65, 69, 72]):
        S.put(piano(m, 0.40 if j < 2 else 0.34, 4.0, 0.5), t_open + 0.03 * j, 1.0, -0.3 + 0.12 * j, 0.25, 0.4)
    for k, m in enumerate([84, 89, 93, 96, 91, 88]):
        S.put(celesta(m, 0.30), t_open + 0.15 + 0.22 * k, 0.75, 0.6 - 0.24 * k, 0.1, 0.5)
    for i, (ts, te, chn) in enumerate(ch[2:]):
        dark = ts >= t_sick - 0.4
        S.put(strings(voicing(chn, 64 if not dark else 58, 4), te - ts + 0.3, 0.6, 1.6, 0.45 if not dark else 0.28,
                      0.55 if not dark else 0.4, 810 + i), ts, 1.0, 0, 0.1, 0.5)
        S.put(cello(bass_note(chn, 38, 50), te - ts + 0.2, 0.5 if not dark else 0.58, 0.3, 1.0, 0.7, 820 + i), ts,
              1.0, -0.1, 0.1, 0.4)
    lay_pad(S, ch, 0.3, center=58, bright=0.3, attack=1.2, seed=inst + 50)
    # unease creeping back in under "sick, addicted, poor"
    S.put(trem_strings([74, 75], t_terr - t_sick + 0.8, 7.0, 0.6, attack=1.2, release=1.0, bright=0.3, vel=0.22,
                       seed=830), t_sick - 0.2, 0.8, 0, 0.0, 0.45)


def m_fear(S, ctx, rng, inst):
    bar = 3.7
    prog = ["Dm", "Dm/C#", "Dm/C", "Bbmaj7", "Gm", "A7sus4", "A7", "Dm"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.8)
    ctx.harmony += [(a, b, c, DMIN) for a, b, c in ch]
    for i, (ts, te, chn) in enumerate(ch):
        S.put(trem_strings(voicing(chn, 62, 3), te - ts + 0.25, 7.5, 0.5, attack=0.8, release=1.2, bright=0.3,
                           vel=0.32, seed=900 + i), ts, 1.0, 0, 0.1, 0.45)
        r = bass_note(chn, 36, 47)
        for k, bt in enumerate(beats_in(ts, te, bar / 4)):
            if k % 2 == 0:
                S.put(pluck(r, 0.42, 0.45, 0.25), bt + hum(rng, 0.004), 0.9, -0.15, 0.15, 0.15)
    S.put(drone(26, S.t1 - S.t0 + 1.0, 0.3, 2.5, 2.0, 220, inst), S.t0 - 0.8, 0.7, 0, 0, 0.3)


def m_boundary(S, ctx, rng, inst):
    beat = 60 / 70
    bar = beat * 4
    prog = ["F", "Am7", "Bbmaj7", "C", "Dm7", "Bbmaj7", "F/A", "Csus4"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.8)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.4, center=60, bright=0.32, attack=1.3, seed=inst + 60)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=57, hi=81, vel=0.34, rng=rng, bright=0.45,
                  pattern=[0, 2, 1, 3, 2, 4, 3, 1])
    t_door = W("L22", "door")
    late = [(a, b, c) for a, b, c in ch if b > t_door - 1.5]
    lay_strings(S, late, 0.45, center=67, n=3, attack=1.5, release=2.0, bright=0.4, vel=0.45, seed=inst + 61)
    lay_twinkle(S, ctx, [(a, b, c) for a, b, c in ch if a > t_door], 0.5, rate=0.5, lo=84, hi=96, rng=rng,
                inst="celesta")


def m_lightness(S, ctx, rng, inst):
    beat = 60 / 112
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["F", "Bb", "C7", "F"], bar, 1, pre=0.4)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    lay_pizz_bass(S, ch, beat, 1.0, beats=(0, 2), rng=rng, vel=0.55)
    lay_pizz_chords(S, ch, beat, 0.7, beats=(1, 3), center=65, rng=rng, vel=0.4)
    lay_rhodes_chords(S, ctx, ch, beat, 0.5, center=64, n=3, vel=0.26, stab=False, rng=rng)
    # a little two-note "button" after "The shortcut."
    tb = anchors.resolve(anchors.L("L27", "end", 0.12))
    S.put(pluck(84, 0.5, 0.25, 0.75), tb, 0.8, 0.3, 0.1, 0.15)
    S.put(pluck(89, 0.5, 0.25, 0.75), tb + beat / 2, 0.8, 0.35, 0.1, 0.15)


def m_care(S, ctx, rng, inst):
    beat = 60 / 76
    bar = beat * 4
    prog = ["Bb", "F/A", "Gm7", "C", "F", "Dm7", "Bbmaj7", "C"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.8)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    dur = S.t1 - S.t0
    lay_pad(S, ch, 0.42, center=60, bright=0.38, attack=1.0, seed=inst + 70)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=55, hi=83, vel=0.34, rng=rng, bright=0.52,
                  pattern=[0, 2, 4, 3, 2, 1])
    for i, (ts, te, chn) in enumerate(ch):
        pr = float(np.clip((ts - S.t0) / dur, 0, 1))
        S.put(strings(voicing(chn, 67, 3) + [root_note(chn, 38, 49)], te - ts + 0.3, 0.9, 1.5, 0.35 + 0.25 * pr,
                      0.25 + 0.45 * pr, 700 + i), ts, 1.0, 0, 0.1, 0.45)
    lay_twinkle(S, ctx, [(a, b, c) for a, b, c in ch if a > S.t0 + 8], 0.55, rate=0.6, lo=84, hi=96, rng=rng,
                inst="celesta")


def m_refusal(S, ctx, rng, inst):
    beat = 60 / 100
    bar = beat * 4
    t_study = W("L30", "study")
    t_twice = W("L30", "twice")
    ch = chord_grid(S.t0, t_study - 0.1, ["Dm", "Bb", "C", "Dm"], bar, 1, pre=0.6)
    ch = [(a, min(b, t_study - 0.1), c) for a, b, c in ch if a < t_study - 0.1]
    ch += [(t_study - 0.1, t_study + 1.9, chord("Bb")), (t_study + 1.9, t_twice - 0.9, chord("C")),
           (t_twice - 0.9, t_twice, chord("Csus4")), (t_twice, S.t1 + 1.0, chord("F"))]
    ctx.harmony += [(a, b, c, DMIN if a < t_twice else FMAJ) for a, b, c in ch]
    span = max(1.0, t_twice - S.t0)
    for i, (ts, te, chn) in enumerate(ch):
        r = bass_note(chn, 36, 47)
        last = ts >= t_twice - 0.01
        if not last:
            for k, bt in enumerate(beats_in(ts, te, beat / 2)):
                pr = float(np.clip((bt - S.t0) / span, 0, 1))
                v = (0.36 + 0.4 * pr) * (1.0 if k % 2 == 0 else 0.72)
                S.put(cello(r if k % 4 != 3 else r + 12, beat / 2 * 0.8, v, 0.012, 0.1, 0.0, k), bt + hum(rng, 0.003),
                      1.0, -0.1, 0.12, 0.2)
                if k % 4 == 0 and pr > 0.3:
                    S.put(timpani(bass_note(chn, 38, 49), 0.25 + 0.4 * pr), bt, 0.7, 0, 0.1, 0.3)
        pr = float(np.clip((ts - S.t0) / span, 0, 1))
        S.put(strings(voicing(chn, 64 if not last else 69, 4), te - ts + 0.3, 0.7 if not last else 0.2, 1.6,
                      0.32 + 0.3 * pr, 0.32 + 0.4 * pr if not last else 0.8, 1000 + i), ts, 1.0, 0, 0.1, 0.45)
    # the lift: bright F major with piano and a celesta shimmer
    for j, m in enumerate([41, 53, 60, 65, 69, 72, 77]):
        S.put(piano(m, 0.42 if j < 2 else 0.34, 3.5, 0.55), t_twice + 0.025 * j, 1.0, -0.3 + 0.1 * j, 0.25, 0.4)
    for k, m in enumerate([89, 93, 96, 101]):
        S.put(celesta(m, 0.3), t_twice + 0.25 + 0.2 * k, 0.7, 0.5 - 0.3 * k, 0.1, 0.5)


def m_turn(S, ctx, rng, inst):
    dur = S.t1 - S.t0
    ctx.harmony.append((S.t0 - 1.0, S.t1 + 1.0, chord("Dm"), DMIN))
    S.put(drone(26, dur + 1.0, 0.55, 3.0, 3.0, 170, inst), S.t0 - 0.6, 1.0, 0, 0, 0.3)
    S.put(drone(33, dur + 1.0, 0.32, 3.5, 3.0, 230, inst + 4), S.t0, 0.8, 0, 0, 0.3)
    # a single, barely-there high harmonic when Kai says where it happened
    t = W("L33", "Fourth")
    S.put(strings([81, 88], 7.0, 3.0, 3.0, 0.22, 0.2, 1100), t, 0.6, 0, 0.0, 0.6)


def m_reckoning(S, ctx, rng, inst):
    beat = 60 / 52
    bar = beat * 4
    prog = ["Dm", "Bbmaj7", "F/A", "Gm7", "Dm/F", "Bb", "Csus4", "C", "Dm", "Bbmaj7", "F", "C"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=0.6)
    ctx.harmony += [(a, b, c, DMIN) for a, b, c in ch]
    t_listen = W("L42", "listen")
    for i, (ts, te, chn) in enumerate(ch):
        warm = ts > t_listen - 2.0
        S.put(piano(bass_note(chn, 33, 45), 0.32, te - ts + 0.8, 0.25), ts + hum(rng, 0.004), 1.0, -0.2, 0.2, 0.45)
        tl_ = tones(chn, 62, 79)
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if k == 0 or (ctx.speaking(bt) and k % 2 == 1) or rng.random() < 0.45:
                continue
            m = tl_[rng.integers(len(tl_))]
            S.put(piano(m, 0.26 * rng.uniform(0.85, 1.1), 2.6, 0.3), bt + hum(rng, 0.012), 0.95,
                  rng.uniform(-0.3, 0.35), 0.2, 0.5)
        S.put(strings(voicing(chn, 62 if not warm else 66, 3), te - ts + 0.4, 2.0, 2.4, 0.22 if not warm else 0.32,
                      0.30 if not warm else 0.4, 1200 + i), ts, 1.0, 0, 0.1, 0.55)
    lay_pad(S, ch, 0.25, center=55, bright=0.15, attack=2.2, seed=inst + 80)


def m_dawn(S, ctx, rng, inst):
    beat = 60 / 66
    bar = beat * 4
    prog = ["F", "C/E", "Dm7", "Bbmaj7", "F/A", "Gm7", "Csus4", "C"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1, pre=1.0)
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    dur = S.t1 - S.t0
    lay_pad(S, ch, 0.42, center=60, bright=0.4, attack=1.4, seed=inst + 90)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=57, hi=81, vel=0.32, rng=rng, bright=0.5,
                  pattern=[0, 1, 2, 3, 4, 3, 2, 1])
    for i, (ts, te, chn) in enumerate(ch):
        pr = float(np.clip((ts - S.t0) / dur, 0, 1))
        S.put(strings(voicing(chn, 66, 3), te - ts + 0.3, 1.4, 1.8, 0.3 + 0.25 * pr, 0.25 + 0.3 * pr, 1300 + i), ts,
              1.0, 0, 0.1, 0.45)
    # the motif comes home in major: the musical question right before Hale's question,
    # and the answer right before Kai's
    q = anchors.resolve(anchors.L("L43", "end", 0.12))
    a = anchors.resolve(anchors.L("L44", "end", 0.08))
    play_motif(S, ctx, q, beat, MOTIF_Q_MAJ, "piano", 0.42, 0, 0.95, 0.25, 0.4, rng)
    play_motif(S, ctx, a, beat * 0.85, MOTIF_A_MAJ, "celesta", 0.4, 0, 0.85, 0.15, 0.45, rng)


def m_finale(S, ctx, rng, inst):
    acc = [a for a in ctx.tl["accents"] if a["kind"] == "swell" and S.t0 <= a["t"] <= S.t1 + 2]
    t_land = acc[-1]["t"] - 0.02 if acc else S.t1 - 4.0
    pre = [("Dm", 2.6), ("Bb", 2.4), ("F/A", 2.2), ("Gm7", 2.2), ("Csus4", 1.2), ("C", 1.0)]
    total_pre = sum(d for _, d in pre)
    scale = max(0.6, (t_land - (S.t0 - 0.8)) / total_pre)
    t = t_land - total_pre * scale
    ch = []
    for name, d in pre:
        ch.append((t, t + d * scale, chord(name)))
        t += d * scale
    end = ctx.tl["total"]
    ch.append((t_land, end + 0.5, chord("F")))
    ctx.harmony += [(a, b, c, FMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.5, center=60, bright=0.42, attack=1.0, release=3.0, seed=inst + 95, n=5, hall=0.5)
    for i, (ts, te, chn) in enumerate(ch[:-1]):
        S.put(strings(voicing(chn, 65, 4) + [root_note(chn, 38, 49)], te - ts + 0.25, 0.7, 1.2, 0.42,
                      0.4 + 0.07 * i, 1400 + i), ts, 1.0, 0, 0.1, 0.5)
        for j, m in enumerate([bass_note(chn, 33, 45)] + voicing(chn, 60, 3)):
            S.put(piano(m, 0.33, te - ts + 0.5, 0.45), ts + 0.04 * j, 1.0, -0.2 + 0.13 * j, 0.25, 0.35)
    ts, te, chn = ch[-1]
    # the landing on "care": warm F major, a rising string swell into it, the motif's answer after
    S.put(strings([53, 60, 65, 69, 72, 77], 2.2, 0.1, 1.0, 0.5, 0.6, 1450, swell=True), ts - 2.2, 1.0, 0, 0.1, 0.5)
    S.put(strings([41, 53, 60, 65, 69, 72, 77, 81], end - ts - 0.6, 0.25, 2.5, 0.52, 0.85, 1451), ts, 1.0, 0, 0.1,
          0.55)
    for j, m in enumerate([29, 41, 53, 60, 65, 69, 72, 77]):
        S.put(piano(m, 0.42 if j < 2 else 0.35, 6.0, 0.5), ts + 0.03 * j, 1.0, -0.3 + 0.08 * j, 0.25, 0.4)
    play_motif(S, ctx, ts + 1.4, 60 / 66, MOTIF_A_MAJ, "celesta", 0.36, 12, 0.75, 0.1, 0.5, rng)


MOODS = dict(rain_night=m_rain_night, conversation=m_conversation, toolkit=m_toolkit, cost=m_cost, cells=m_cells,
             fear=m_fear, boundary=m_boundary, lightness=m_lightness, care=m_care, refusal=m_refusal, turn=m_turn,
             reckoning=m_reckoning, dawn=m_dawn, finale=m_finale)

# target loudness of each mood's music (LUFS, before ducking / master)
TARGET = dict(rain_night=-30.0, conversation=-31.5, toolkit=-30.0, cost=-29.5, cells=-27.5, fear=-30.5,
              boundary=-29.5, lightness=-30.0, care=-29.0, refusal=-27.5, turn=-41.0, reckoning=-31.0, dawn=-29.5,
              finale=-27.0)


_IRS = {}


def irs():
    if not _IRS:
        _IRS["room"] = make_ir(t60=1.4, predelay=0.016, bright=0.4, seed=21, early=6)
        _IRS["hall"] = make_ir(t60=3.6, predelay=0.03, bright=0.3, seed=22, early=4)
    return _IRS["room"], _IRS["hall"]


def xfade_len(prev, nxt):
    if nxt == "turn":
        return 1.2
    if prev == "turn":
        return 2.2
    if nxt == "lightness" or prev == "lightness":
        return 0.8
    if nxt == "finale":
        return 2.0
    return 1.6


def section_env(n, a, t0, t1, fin, fout):
    """Equal-power fade in around t0 and fade out around t1 (times absolute)."""
    tt = a + np.arange(n) / SR
    e = np.ones(n)
    if fin > 0:
        x = np.clip((tt - (t0 - fin / 2)) / fin, 0, 1)
        e *= np.sin(x * np.pi / 2)
    if fout > 0:
        x = np.clip((tt - (t1 - fout / 2)) / fout, 0, 1)
        e *= np.cos(x * np.pi / 2)
    return e


def render_score(tl, verbose=True):
    """Returns (music_bus_stereo_wet, ctx, report)."""
    total = tl["total"]
    N = ns(total)
    ctx = Ctx(tl)
    secs = [(anchors.resolve(a), m) for a, m in direction.MUSIC]
    bus = np.zeros((2, N))
    meter = pyloudnorm.Meter(SR)
    counts = {}
    report = []
    ir_room, ir_hall = irs()
    for i, (t0, mood) in enumerate(secs):
        t1 = secs[i + 1][0] if i + 1 < len(secs) else total
        inst = counts.get(mood, 0)
        counts[mood] = inst + 1
        prev = secs[i - 1][1] if i > 0 else None
        nxt = secs[i + 1][1] if i + 1 < len(secs) else None
        fin = 0.0 if i == 0 else xfade_len(prev, mood)
        fout = 0.0 if nxt is None else xfade_len(mood, nxt)
        S = Sec(t0, t1, pre=max(2.5, fin), post=9.0)
        rng = np.random.default_rng(2000 + i)
        MOODS[mood](S, ctx, rng, inst)
        wet = S.dry + 0.55 * convolve(S.room, ir_room) + 0.6 * convolve(S.hall, ir_hall)
        wet = hp(wet, 40, 2)
        if nxt is None:
            env = section_env(S.n, S.a, t0, t1, fin, 0.0)
            tt = S.a + np.arange(S.n) / SR
            env *= np.clip((total - tt) / 3.0, 0, 1) ** 1.5
        else:
            env = section_env(S.n, S.a, t0, t1, fin, fout)
        i0 = ns(max(0.0, t0) - S.a)
        i1 = ns(t1 - S.a)
        core = wet[:, i0:max(i0 + ns(0.5), i1)]
        try:
            lu = meter.integrated_loudness(core.T)
        except Exception:
            lu = -70
        g = 10 ** ((TARGET[mood] - lu) / 20) if np.isfinite(lu) and lu > -70 else 1.0
        g = min(g, 30.0)
        report.append((mood, t0, t1, lu, 20 * np.log10(g)))
        a = ns(S.a)
        lo, hi = max(0, a), min(N, a + S.n)
        k0 = lo - a
        k1 = k0 + (hi - lo)
        bus[:, lo:hi] += wet[:, k0:k1] * env[k0:k1] * g
        if verbose:
            print(f"  music {mood:12s} {t0:7.2f}-{t1:7.2f} raw {lu:6.1f} LUFS gain {20*np.log10(g):+5.1f} dB",
                  flush=True)
    return bus, ctx, report


# ----------------------------------------------------------------------------
# word accents
# ----------------------------------------------------------------------------

def harmony_at(ctx, t):
    best = None
    for a, b, ch, sc in ctx.harmony:
        if a <= t < b:
            best = (ch, sc)
    if best is None:
        return chord("F"), FMAJ
    return best


ACCENT_OFFSET_DB = dict(hi=-9.5, lo=-13.0, swell=-11.0, comic=-10.0, boom=-9.0)
ACCENT_RANGE_DB = dict(hi=(-30, -17), lo=(-32, -19), swell=(-30, -17), comic=(-30, -18), boom=(-26, -12))


def render_accents(tl, ctx, voice_mono=None):
    """Each accent is rendered on its own, then scaled so its peak sits a fixed
    distance below the voice peak around the word (clamped to a sane range)."""
    N = ns(tl["total"])
    dry = np.zeros((2, N))
    hall = np.zeros((2, N))
    rng = np.random.default_rng(78)
    acs = tl["accents"]
    for n_ac, ac in enumerate(acs):
        t = ac["t"] - 0.02
        ch, sc = harmony_at(ctx, ac["t"])
        kind = ac["kind"]
        L = ns(6.0)
        pre = ns(1.8) if kind == "swell" else ns(0.05)
        bd = np.zeros((2, L + pre))
        bh = np.zeros((2, L + pre))

        def put(sig, dt, gain, p=0.0, h=0.3):
            st = pan(sig, p) if sig.ndim == 1 else sig
            i = pre + ns(dt)
            j = min(L + pre, i + st.shape[1])
            if j <= i:
                return
            bd[:, i:j] += st[:, : j - i] * gain
            bh[:, i:j] += st[:, : j - i] * gain * h

        if kind == "hi":
            cand = tones(ch, 81, 93)
            pref = [m for m in cand if (m - ch["root"]) % 12 in (4, 7, 3)] or cand
            m = pref[rng.integers(len(pref))]
            put(celesta(m, 0.6), 0.0, 1.0, 0.15, 0.45)
            put(glock(m + 12, 0.24), 0.01, 0.6, 0.3, 0.6)
            put(rhodes_st(m - 12, 0.34, 1.6, 0.3), 0.005, 0.8, 0.0, 0.35)
        elif kind == "lo":
            r = root_note(ch, 38, 49)
            put(cello(r, 2.4, 0.75, 0.07, 1.2, 0.8), 0.0, 1.0, -0.05, 0.35)
            put(piano(r - 12, 0.5, 3.0, 0.3), 0.0, 0.8, 0.0, 0.35)
            put(strings([r + 7, r + 12], 2.4, 0.25, 1.4, 0.3, 0.45, 31), 0.0, 0.6, 0.0, 0.5)
        elif kind == "boom":
            r = root_note(ch, 36, 47)
            put(timpani(r, 0.9), 0.0, 1.0, 0, 0.4)
        elif kind == "comic":
            r = root_note(ch, 45, 56)
            put(blip(r + 7, 0.11, 0.7, 0.0), 0.0, 1.0, 0.2, 0.15)
            put(blip(r, 0.2, 0.7, -0.06), 0.15, 1.0, 0.2, 0.15)
        elif kind == "swell":
            notes = voicing(ch, 65, 4) + [root_note(ch, 38, 49)]
            put(strings(notes, 1.7, 0.1, 2.2, 0.5, 0.75, 51, swell=True), -1.7, 1.0, 0, 0.5)
            put(glock(tones(ch, 86, 98)[0], 0.32), 0.0, 0.55, 0.35, 0.6)
        gap = acs[n_ac + 1]["t"] - ac["t"] if n_ac + 1 < len(acs) else 99.0
        if gap < 4.5:  # release before the next accent so that one reads as its own gesture
            f0, f1 = pre + ns(max(0.3, gap - 0.65)), pre + ns(max(0.4, gap - 0.1))
            ramp = np.ones(L + pre)
            ramp[f0:f1] = np.cos(np.linspace(0, np.pi / 2, f1 - f0)) ** 2
            ramp[f1:] = 0.0
            bd *= ramp
            bh *= ramp
        pk = np.max(np.abs(bd)) + 1e-9
        vpk = 0.1
        if voice_mono is not None:
            a0, a1 = max(0, ns(ac["t"] - 0.4)), min(len(voice_mono), ns(ac["t"] + 0.6))
            vpk = float(np.max(np.abs(voice_mono[a0:a1]))) if a1 > a0 else 0.1
        tgt = 20 * np.log10(max(vpk, 1e-4)) + ACCENT_OFFSET_DB[kind]
        lo_, hi_ = ACCENT_RANGE_DB[kind]
        tgt = min(max(tgt, lo_), hi_)
        g = 10 ** (tgt / 20) / pk
        i0 = ns(t) - pre
        k0 = 0
        if i0 < 0:
            k0, i0 = -i0, 0
        j = min(N, i0 + bd.shape[1] - k0)
        dry[:, i0:j] += bd[:, k0:k0 + j - i0] * g
        hall[:, i0:j] += bh[:, k0:k0 + j - i0] * g
    return dry, hall
