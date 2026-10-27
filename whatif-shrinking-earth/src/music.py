"""Procedural score: felt piano, pads, strings, celesta, plucks, cello, drones.

render_score(tl) returns stereo buses (music, accents) as reverberated stereo
arrays plus the harmony track used to keep word accents consonant.

Moods come from direction.MUSIC; each mood instance renders into its own
buffer, is loudness-normalized to its target, and crossfades into the next.
"""
import math

import numpy as np
from scipy import signal
import pyloudnorm

from audio_dsp import (SR, convolve, env_points, fade_edges, lp, hp, make_ir, midi_hz, ns, pan, saw, sine,
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


MOTIF_MAJ = ([69, 74, 76, 78, 76, 74], [0.5, 0.5, 0.5, 1.5, 0.5, 2.0])
MOTIF_MIN = ([66, 71, 73, 74, 73, 71], [0.5, 0.5, 0.5, 1.5, 0.5, 2.0])
MOTIF_DMIN = ([69, 74, 76, 77, 76, 74], [0.5, 0.5, 0.5, 1.5, 0.5, 2.0])


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
# moods
# ----------------------------------------------------------------------------

def m_night(S, ctx, rng, inst):
    bpm = 66
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["Bm", "G", "D", "A"], bar, 1, pre=0.0 if S.t0 < 0.1 else 1.0)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.55, center=57, bright=0.22, attack=1.8, seed=inst)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=50, hi=74, vel=0.34, rng=rng, bright=0.35)
    # the sisters' motif (minor) in the first gaps
    done = 0
    for a, b in ctx.gaps(S.t0, S.t1 - 2, 1.0):
        if done >= 2:
            break
        play_motif(S, ctx, a + 0.15, beat, MOTIF_MIN, "piano", 0.42, 12, 0.9, 0.3, 0.3, rng)
        done += 1
    lay_strings(S, ch, 0.28, center=66, n=2, attack=2.2, release=2.4, bright=0.25, vel=0.4, hall=0.5, seed=inst + 3)


def m_curious(S, ctx, rng, inst):
    bpm = 92
    beat = 60 / bpm
    bar = beat * 4
    prog = ["D", "A/C#", "Bm", "G", "D", "A", "G", "A"] if inst % 2 == 0 else ["G", "D/F#", "Em", "A"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.5, center=60, bright=0.35, attack=0.9, seed=inst * 10)
    lay_celesta_arp(S, ctx, ch, beat, 0.9, div=2, lo=74, hi=91, vel=0.3, rng=rng)
    lay_pizz_bass(S, ch, beat, 0.9, beats=(0, 2), rng=rng, vel=0.55)
    for a, b in ctx.gaps(S.t0 + 1, S.t1 - 1.5, 1.4)[:2]:
        play_motif(S, ctx, a + 0.1, beat, MOTIF_MAJ, "celesta", 0.4, 12, 0.8, 0.2, 0.4, rng)


def m_deflate(S, ctx, rng, inst):
    beat = 1.0
    ch = [(S.t0 - 0.8, S.t0 + 3.6, chord("Bm")), (S.t0 + 3.6, S.t1 + 1.0, chord("G"))]
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.45, center=55, bright=0.15, attack=1.2, seed=inst + 40)
    S.put(cello(35, S.t1 - S.t0 + 0.5, 0.55, 0.6, 1.5), S.t0 - 0.3, 1.0, -0.1, 0.1, 0.4)
    t = S.t0 + 0.2
    for m in (78, 76, 74, 71):
        if t < S.t1:
            S.put(piano(m, 0.33, 2.2, 0.3), t, 0.9, 0.2, 0.3, 0.35)
        t += 1.45


def m_playful(S, ctx, rng, inst):
    bpm = 112
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["D", "G", "A7", "D"], bar, 1, pre=0.5)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pizz_bass(S, ch, beat, 1.0, beats=(0, 2), rng=rng, vel=0.6)
    lay_pizz_chords(S, ch, beat, 0.75, beats=(1, 3), rng=rng)
    lay_pad(S, ch, 0.25, center=62, bright=0.3, attack=0.4, release=0.8, seed=inst + 70)
    for a, b in ctx.gaps(S.t0, S.t1 - 0.5, 0.7)[:3]:
        t = a + 0.05
        for m in (74, 76, 78, 79, 81):
            if t > b:
                break
            S.put(pluck(m + 12, 0.45, 0.3, 0.7), t, 0.6, 0.3, 0.2, 0.1)
            t += beat / 2


def m_waltz(S, ctx, rng, inst):
    # 3/4 music box; starts slow, accelerates on "pull them in", stops dead when
    # Pip shouts, then resumes gently.
    t_pull = anchors.resolve(anchors.Wd("L22", "pull"))
    t_stop = anchors.resolve(anchors.L("L23", "start", -0.06))
    t_res = anchors.resolve(anchors.Wd("L24", "But", "start", -0.2))
    prog = ["D", "D", "A7", "A7", "A7", "A7", "D", "D", "G", "G", "D", "A7"]
    beats = []
    t = S.t0 - 0.2
    while t < S.t1 + 0.2:
        if t_stop - 0.01 <= t < t_res:
            t = t_res
            continue
        if t < t_pull:
            bpm = 126
        elif t < t_stop:
            bpm = 126 + 90 * min(1, (t - t_pull) / 0.8)
        else:
            bpm = 132
        beats.append((t, bpm))
        t += 60 / bpm
    melody = [78, 81, 86, 85, 83, 81, 79, 78, 76, 78, 81, 83, 81, 79, 78, 76, 74, 76, 78, 81, 79, 76, 74, 73]
    # harmony entries (one chord per bar)
    for bi in range(0, len(beats), 3):
        ts = beats[bi][0]
        te = beats[bi + 3][0] if bi + 3 < len(beats) else S.t1 + 0.5
        chn = chord(prog[(bi // 3) % len(prog)])
        ctx.harmony.append((ts, te, chn, DMAJ))
    for k, (bt, bpm) in enumerate(beats):
        bar_i = k // 3
        chn = chord(prog[bar_i % len(prog)])
        pos = k % 3
        spk = ctx.speaking(bt)
        if pos == 0:
            S.put(pluck(bass_note(chn, 38, 49), 0.62, 0.6, 0.4), bt, 1.0, -0.2, 0.2, 0.1)
        else:
            for j, m in enumerate(voicing(chn, 69, 3)):
                S.put(celesta(m, 0.22 * (0.8 if spk else 1.0)), bt + 0.004 * j, 0.8, -0.3 + 0.3 * j, 0.2, 0.25)
        if pos == 0 or (pos == 2 and k % 2 == 0):
            mm = melody[(k // 2) % len(melody)]
            if mm % 12 not in chn["pcs"] and pos == 0:
                mm = min(tones(chn, mm - 3, mm + 3) or [mm], key=lambda x: abs(x - mm))
            S.put(glock(mm, 0.3 * (0.75 if spk else 1.0)), bt, 0.85, 0.25, 0.15, 0.3)
    # the stop: one surprised plink
    S.put(pluck(86, 0.5, 0.25, 0.8), t_stop + 0.02, 0.8, 0.35, 0.1, 0.2)
    S.put(pluck(74, 0.5, 0.25, 0.8), t_stop + 0.13, 0.7, 0.35, 0.1, 0.2)


def m_tender(S, ctx, rng, inst):
    beat = 60 / 60
    prog = ["Bm", "G", "D", "A"] if inst % 2 == 0 else ["G", "D/F#", "Em", "D"]
    ch = chord_grid(S.t0, S.t1, prog, beat * 4 * (0.75 if inst % 2 == 0 else 0.5), 1, pre=0.8)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.45, center=59, bright=0.2, attack=1.2, seed=inst + 90)
    for ts, te, chn in ch:
        notes = voicing(chn, 62, 3)
        for j, m in enumerate([bass_note(chn, 38, 50)] + notes):
            S.put(piano(m, 0.33 if j else 0.36, te - ts + 0.8, 0.3), ts + 0.045 * j + hum(rng, 0.004), 1.0,
                  -0.2 + 0.15 * j, 0.3, 0.35)
    if inst % 2 == 1:
        lay_twinkle(S, ctx, ch, 0.6, rate=0.8, lo=81, hi=93, rng=rng, inst="celesta")


def m_tension(S, ctx, rng, inst):
    bpm = 90
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["Bm", "Bm", "G", "G", "Em", "Em", "F#sus4", "F#"], bar, 1)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    dur = S.t1 - S.t0
    for ts, te, chn in ch:
        r = bass_note(chn, 35, 46)
        for k, bt in enumerate(beats_in(ts, te, beat / 2)):
            prog = np.clip((bt - S.t0) / dur, 0, 1)
            v = (0.42 + 0.35 * prog) * (1.0 if k % 2 == 0 else 0.75)
            m = r if k % 4 != 3 else r + 12
            S.put(cello(m, beat / 2 * 0.8, v, 0.015, 0.12, 0.0, k), bt + hum(rng, 0.004), 1.0, -0.1, 0.15, 0.2)
        prog = np.clip((ts - S.t0) / dur, 0, 1)
        S.put(strings(voicing(chn, 64, 4), te - ts + 0.2, 0.9, 1.4, 0.35 + 0.3 * prog, 0.35 + 0.45 * prog,
                      int(ts * 10)), ts, 1.0, 0, 0.1, 0.4)
        if prog > 0.45:
            S.put(timpani(bass_note(chn, 38, 49), 0.35 + 0.4 * prog), ts, 0.8, 0, 0.1, 0.35)
    lay_pad(S, ch, 0.3, center=55, bright=0.25, attack=1.0, seed=inst + 120)


def m_somber(S, ctx, rng, inst):
    ch = [(S.t0 - 0.6, S.t0 + 2.2, chord("Bm")), (S.t0 + 2.2, S.t0 + 4.2, chord("Em/G")),
          (S.t0 + 4.2, S.t1 + 1.0, chord("F#sus4"))]
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    for ts, te, chn in ch:
        notes = [bass_note(chn, 31, 43)] + voicing(chn, 52, 3)
        for j, m in enumerate(notes):
            S.put(piano(m, 0.36, te - ts + 1.0, 0.2), max(S.t0 - 0.2, ts) + 0.05 * j, 1.0, -0.2 + 0.12 * j, 0.3,
                  0.4)
    S.put(cello(35, S.t1 - S.t0 + 0.6, 0.45, 0.8, 1.6), S.t0, 0.9, 0, 0.1, 0.4)
    lay_pad(S, ch, 0.35, center=55, bright=0.15, attack=1.5, seed=inst + 140)


def m_rise(S, ctx, rng, inst):
    dur = S.t1 - S.t0
    ch = [(S.t0 - 0.5, S.t0 + dur * 0.5, chord("G")), (S.t0 + dur * 0.5, S.t1 + 0.8, chord("A"))]
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    line = [55, 57, 59, 62, 64, 66, 69, 71, 74]
    step = (dur + 0.6) / len(line)
    for k, m in enumerate(line):
        t = S.t0 - 0.3 + k * step
        S.put(strings([m, m + 12], step * 1.2, 0.08, 0.5, 0.4 + 0.05 * k, 0.4 + 0.05 * k, k), t, 1.0, 0, 0.1, 0.45)
        S.put(celesta(m + 24, 0.25 + 0.03 * k), t, 0.7, 0.4 * math.sin(k), 0.1, 0.5)
    S.put(strings([50, 57, 62, 66], dur + 0.6, 0.1, 1.5, 0.5, 0.7, 7, swell=True), S.t0 - 0.3, 0.9, 0, 0.1, 0.5)


def m_cosmic(S, ctx, rng, inst):
    bar = 4.0
    prog = ["Dmaj7", "Gmaj7", "Bm7", "Aadd9"] if inst % 2 == 0 else ["Gmaj7", "Dmaj7", "Em7", "Aadd9"]
    ch = chord_grid(S.t0, S.t1, prog, bar, 1)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.8, center=62, bright=0.5, attack=2.0, release=3.0, seed=inst + 160, n=5, width=1.0,
            room=0.0, hall=0.6)
    lay_strings(S, ch, 0.5, center=74, n=3, attack=2.0, release=2.5, bright=0.35, vel=0.45, hall=0.6, seed=inst)
    lay_twinkle(S, ctx, ch, 0.7, rate=0.7, rng=rng)
    S.put(drone(26, S.t1 - S.t0 + 1.0, 0.5, 3.0, 3.0, 220, inst), S.t0 - 1.0, 0.8, 0, 0.0, 0.3)


def m_comic(S, ctx, rng, inst):
    bpm = 120
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["D", "G", "A", "D"], bar, 1, pre=0.25)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    for ts, te, chn in ch:
        r = bass_note(chn, 33, 44)
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if k % 2 == 0:
                S.put(blip(r + (0 if k % 4 == 0 else 7), 0.16, 0.65), bt + hum(rng, 0.004), 1.0, -0.15, 0.2, 0.05)
            else:
                for j, m in enumerate(voicing(chn, 64, 3)):
                    S.put(pluck(m, 0.42, 0.25, 0.6), bt + 0.005 * j, 0.7, -0.3 + 0.3 * j, 0.2, 0.05)
    for a, b in ctx.gaps(S.t0, S.t1, 0.6)[:2]:
        t = a + 0.05
        for m in (86, 85, 83, 81, 79, 78):
            if t > b:
                break
            S.put(celesta(m, 0.35), t, 0.7, 0.3, 0.1, 0.2)
            t += beat / 4


def m_awe(S, ctx, rng, inst):
    bar = 4.6
    ch = chord_grid(S.t0, S.t1, ["D", "Bm", "G", "A", "Bm", "G", "Em", "F#"], bar, 1)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    for i, (ts, te, chn) in enumerate(ch):
        S.put(strings(voicing(chn, 62, 4) + [root_note(chn, 38, 49)], te - ts + 0.3, 1.6, 2.0, 0.45, 0.6,
                      i + 300), ts, 1.0, 0, 0.1, 0.55)
    lay_pad(S, ch, 0.6, center=66, bright=0.45, attack=2.0, release=2.5, seed=inst + 180, n=4, hall=0.6, room=0)
    S.put(drone(26, S.t1 - S.t0 + 1.0, 0.55, 3.0, 3.0, 260, inst + 1), S.t0 - 1.0, 0.9, 0, 0, 0.3)
    lay_twinkle(S, ctx, ch, 0.45, rate=0.35, rng=rng)


def m_dread(S, ctx, rng, inst):
    dur = S.t1 - S.t0
    ch = [(S.t0 - 1.0, S.t1 + 1.0, chord("Dm"))]
    ctx.harmony += [(a, b, c, DMIN) for a, b, c in ch]
    S.put(drone(26, dur + 1.0, 0.75, 2.5, 2.0, 300, inst), S.t0 - 1.0, 1.0, 0, 0, 0.3)
    S.put(drone(33, dur + 1.0, 0.45, 3.0, 2.0, 420, inst + 2), S.t0 - 0.5, 0.8, 0, 0, 0.3)
    implode = ctx.sfx_times("implode", S.t0, S.t1)
    boom = ctx.sfx_times("boom", S.t0, S.t1)
    chirp = ctx.sfx_times("gw_chirp", S.t0, S.t1)
    climax = implode[0] if implode else (chirp[0] + 3.5 if chirp else S.t1)
    # heartbeat accelerating toward the climax
    t = S.t0 + 0.3
    while t < climax - 0.3:
        prog = np.clip((t - S.t0) / max(1.0, climax - S.t0), 0, 1)
        bpm = (58 + 34 * prog) if not chirp else (72 + 50 * prog)
        S.put(heartbeat(0.45 + 0.4 * prog), t, 1.0, 0, 0.0, 0.15)
        t += 60 / bpm
    # dissonant string cluster swells
    clusters = [[62, 63, 69], [58, 62, 63], [60, 62, 63, 68], [62, 63, 69, 70]]
    t = S.t0
    k = 0
    while t < climax - 1.0:
        L = min(4.2, climax - t)
        prog = np.clip((t - S.t0) / max(1.0, climax - S.t0), 0, 1)
        S.put(strings(clusters[k % len(clusters)], L, attack=L * 0.8, release=1.2, bright=0.4 + 0.3 * prog,
                      vel=0.35 + 0.4 * prog, seed=k + inst * 7, swell=True), t, 1.0, 0, 0.05, 0.5)
        t += L * 0.92
        k += 1
    if chirp:
        # rising tremolo line during the chirp
        c0 = chirp[0]
        for j in range(14):
            tt = c0 + j * 0.27
            m = 62 + j
            S.put(strings([m, m + 12], 0.3, 0.03, 0.15, 0.6, 0.35 + 0.03 * j, j + 50), tt, 0.9, 0, 0.0, 0.25)
    if implode:
        # hollow after "gravity wins": only a high eerie tone until the boom
        b = boom[0] if boom else climax + 5
        S.put(strings([86, 87], b - climax, 1.5, 0.6, 0.25, 0.25, 77), climax + 0.4, 0.8, 0, 0.0, 0.6)
        S.put(strings([38, 45, 50, 53], 5.0, 0.02, 3.0, 0.35, 0.9, 88), b, 1.0, 0, 0.0, 0.5)
        S.put(timpani(38, 1.0), b, 1.0, 0, 0.0, 0.4)
        S.put(drone(26, 6.0, 0.8, 0.05, 3.5, 200, 9), b, 1.0, 0, 0.0, 0.3)


def m_lonely(S, ctx, rng, inst):
    bpm = 54
    beat = 60 / bpm
    bar = beat * 4
    prog = ["Bm", "G", "Em", "F#"] if inst % 2 == 0 else ["Bm", "G", "D", "F#m", "Em", "Bm", "G", "F#"]
    pre = 0.5
    t_start = S.t0 + (3.5 if inst % 2 == 1 else 0.0)
    ch = chord_grid(t_start, S.t1, prog, bar, 1, pre=pre)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    for ts, te, chn in ch:
        S.put(piano(bass_note(chn, 31, 43), 0.36, te - ts + 1.0, 0.25), ts, 1.0, -0.2, 0.2, 0.5)
        tl = tones(chn, 71, 86)
        for k, bt in enumerate(beats_in(ts, te, beat)):
            if ctx.speaking(bt) and k % 2 == 1:
                continue
            if rng.random() < 0.35:
                continue
            m = tl[rng.integers(len(tl))]
            S.put(piano(m, 0.30 * rng.uniform(0.85, 1.1), 2.5, 0.35), bt + hum(rng, 0.015), 0.9,
                  rng.uniform(-0.3, 0.4), 0.2, 0.55)
    lay_strings(S, ch, 0.45, center=74, n=3, attack=2.5, release=2.5, bright=0.25, vel=0.35, hall=0.6,
                seed=inst + 400)
    gaps = ctx.gaps(t_start, S.t1 - 3, 2.0)
    if gaps:
        play_motif(S, ctx, gaps[0][0] + 0.2, beat, MOTIF_MIN, "piano", 0.34, 12, 0.85, 0.2, 0.55, rng)


def m_warm(S, ctx, rng, inst):
    bpm = 76
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["D", "A", "Bm", "G"], bar, 1, pre=0.8)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.5, center=60, bright=0.35, attack=1.2, seed=inst + 200)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=57, hi=81, vel=0.36, rng=rng, bright=0.5,
                  pattern=[0, 1, 2, 3, 4, 3, 2, 1])
    late = [(a, b, c) for a, b, c in ch if a > S.t0 + 8]
    lay_strings(S, late, 0.45, center=66, n=3, attack=1.6, release=2.0, bright=0.4, vel=0.45, seed=inst)
    lay_pizz_bass(S, ch, beat, 0.6, beats=(0, 2), rng=rng, vel=0.45)
    for a, b in ctx.gaps(S.t0 + 1, S.t1 - 2, 1.6)[:2]:
        play_motif(S, ctx, a + 0.1, beat, MOTIF_MAJ, "celesta", 0.38, 12, 0.75, 0.2, 0.4, rng)


def m_hope(S, ctx, rng, inst):
    bpm = 66
    beat = 60 / bpm
    bar = beat * 4
    ch = chord_grid(S.t0, S.t1, ["G", "D/F#", "Em", "A", "Bm", "G", "D", "A"], bar / 2, 1, pre=1.0)
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    dur = S.t1 - S.t0
    lay_pad(S, ch, 0.5, center=60, bright=0.4, attack=1.0, seed=inst + 220)
    lay_piano_arp(S, ctx, ch, beat, 1.0, div=2, lo=55, hi=83, vel=0.36, rng=rng, bright=0.55,
                  pattern=[0, 2, 4, 3, 2, 1])
    for i, (ts, te, chn) in enumerate(ch):
        prog = np.clip((ts - S.t0) / dur, 0, 1)
        S.put(strings(voicing(chn, 67, 3) + [root_note(chn, 38, 49)], te - ts + 0.3, 0.9, 1.5, 0.4 + 0.2 * prog,
                      0.35 + 0.35 * prog, i + 500), ts, 1.0, 0, 0.1, 0.45)
    for a, b in ctx.gaps(S.t0, S.t1 - 2, 1.2)[:2]:
        play_motif(S, ctx, a + 0.1, beat, MOTIF_MAJ, "strings", 0.55, 0, 0.7, 0.1, 0.45, rng)


def m_finale(S, ctx, rng, inst):
    acc = [a for a in ctx.tl["accents"] if a["kind"] == "swell" and S.t0 <= a["t"] <= S.t1 + 2]
    t_land = acc[-1]["t"] - 0.02 if acc else S.t1 - 4.0
    pre = [("G", 2.6), ("A", 2.4), ("Bm", 2.1), ("G", 2.0), ("Asus4", 1.0), ("A", 1.0)]
    total_pre = sum(d for _, d in pre)
    scale = max(0.6, (t_land - (S.t0 - 0.8)) / total_pre)
    t = t_land - total_pre * scale
    ch = []
    for name, d in pre:
        ch.append((t, t + d * scale, chord(name)))
        t += d * scale
    end = ctx.tl["total"]
    ch.append((t_land, end + 0.5, chord("D")))
    ctx.harmony += [(a, b, c, DMAJ) for a, b, c in ch]
    lay_pad(S, ch, 0.55, center=62, bright=0.45, attack=1.0, release=3.0, seed=inst + 240, n=5, hall=0.5)
    for i, (ts, te, chn) in enumerate(ch[:-1]):
        S.put(strings(voicing(chn, 66, 4) + [root_note(chn, 38, 49)], te - ts + 0.25, 0.7, 1.2, 0.45,
                      0.45 + 0.06 * i, i + 600), ts, 1.0, 0, 0.1, 0.5)
        for j, m in enumerate([bass_note(chn, 33, 45)] + voicing(chn, 60, 3)):
            S.put(piano(m, 0.34, te - ts + 0.5, 0.45), ts + 0.04 * j, 1.0, -0.2 + 0.13 * j, 0.25, 0.35)
    ts, te, chn = ch[-1]
    # the landing: big warm D major, rising string swell into it, celesta sparkles after
    S.put(strings([50, 57, 62, 66, 69, 74], 2.2, 0.1, 1.0, 0.5, 0.6, 700, swell=True), ts - 2.2, 1.0, 0, 0.1, 0.5)
    S.put(strings([38, 50, 57, 62, 66, 69, 74, 78], end - ts - 0.6, 0.25, 2.5, 0.55, 0.85, 701), ts, 1.0, 0,
          0.1, 0.55)
    for j, m in enumerate([26, 38, 50, 57, 62, 66, 69, 74]):
        S.put(piano(m, 0.42 if j < 2 else 0.36, 6.0, 0.5), ts + 0.03 * j, 1.0, -0.3 + 0.08 * j, 0.25, 0.4)
    for k, m in enumerate([90, 86, 81, 78, 74]):
        S.put(celesta(m, 0.32), ts + 1.2 + k * 0.38, 0.8, 0.5 - 0.25 * k, 0.1, 0.5)


def m_silence(S, ctx, rng, inst):
    return


MOODS = dict(night=m_night, curious=m_curious, deflate=m_deflate, playful=m_playful, waltz=m_waltz,
             tender=m_tender, tension=m_tension, somber=m_somber, rise=m_rise, cosmic=m_cosmic, comic=m_comic,
             awe=m_awe, dread=m_dread, lonely=m_lonely, silence=m_silence, warm=m_warm, hope=m_hope,
             finale=m_finale)

# target short-term loudness of each mood's music (LUFS, before ducking/master)
TARGET = dict(night=-29.5, curious=-29.5, deflate=-30.5, playful=-29.5, waltz=-29.5, tender=-30.5,
              tension=-27.5, somber=-30.5, rise=-27.0, cosmic=-28.5, comic=-29.0, awe=-28.0, dread=-28.5,
              lonely=-30.5, silence=-99, warm=-29.5, hope=-28.5, finale=-26.5)


_IRS = {}


def irs():
    if not _IRS:
        _IRS["room"] = make_ir(t60=1.6, predelay=0.018, bright=0.4, seed=21, early=6)
        _IRS["hall"] = make_ir(t60=4.2, predelay=0.035, bright=0.28, seed=22, early=4)
    return _IRS["room"], _IRS["hall"]


def xfade_len(prev, nxt):
    if nxt == "silence":
        return 0.3
    if prev == "silence":
        return 2.6
    if nxt == "comic" or prev == "comic":
        return 0.7
    if nxt in ("somber",) and prev == "tension":
        return 0.9
    if nxt == "finale":
        return 2.2
    return 1.6


def section_env(n, a, t0, t1, fin, fout, end_cut=None):
    """Equal-power fade in around t0 and fade out around t1 (times absolute)."""
    tt = a + np.arange(n) / SR
    e = np.ones(n)
    if fin > 0:
        x = np.clip((tt - (t0 - fin / 2)) / fin, 0, 1)
        e *= np.sin(x * np.pi / 2)
    if fout > 0:
        x = np.clip((tt - (t1 - fout / 2)) / fout, 0, 1)
        e *= np.cos(x * np.pi / 2)
    if end_cut is not None:
        x = np.clip((tt - end_cut) / 0.04, 0, 1)
        e *= 1 - x
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
    # abrupt stop of the music when the gravitational-wave chirp ends
    chirp_end = None
    try:
        chirp_end = anchors.resolve(anchors.Wd("L47", "space", "end", 0.12))
    except Exception:
        pass
    for i, (t0, mood) in enumerate(secs):
        t1 = secs[i + 1][0] if i + 1 < len(secs) else total
        inst = counts.get(mood, 0)
        counts[mood] = inst + 1
        prev = secs[i - 1][1] if i > 0 else None
        nxt = secs[i + 1][1] if i + 1 < len(secs) else None
        fin = 0.0 if i == 0 else xfade_len(prev, mood)
        fout = 0.0 if nxt is None else xfade_len(mood, nxt)
        S = Sec(t0, t1, pre=max(2.5, fin), post=9.0)
        rng = np.random.default_rng(1000 + i)
        MOODS[mood](S, ctx, rng, inst)
        if mood == "silence":
            report.append((mood, t0, t1, None, 0.0))
            continue
        wet = S.dry + 0.55 * convolve(S.room, ir_room) + 0.6 * convolve(S.hall, ir_hall)
        wet = hp(wet, 42, 2)
        cut = None
        if chirp_end is not None and t0 < chirp_end < t1 + 0.5 and nxt == "silence":
            cut = chirp_end
        if nxt is None:
            env = section_env(S.n, S.a, t0, t1, fin, 0.0)
            tt = S.a + np.arange(S.n) / SR
            env *= np.clip((total - tt) / 3.0, 0, 1) ** 1.5
        else:
            env = section_env(S.n, S.a, t0, t1, fin, fout, cut)
        # normalize the (reverberated) section to its target loudness over its core span
        i0 = ns(t0 - S.a)
        i1 = ns((min(t1, cut) if cut else t1) - S.a)
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
            print(f"  music {mood:8s} {t0:7.2f}-{t1:7.2f} raw {lu:6.1f} LUFS gain {20*np.log10(g):+5.1f} dB", flush=True)
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
        return chord("D"), DMAJ
    return best


ACCENT_OFFSET_DB = dict(hi=-9.0, lo=-13.0, swell=-11.0, comic=-9.5, boom=-9.0)
ACCENT_RANGE_DB = dict(hi=(-30, -17), lo=(-32, -19), swell=(-30, -17), comic=(-30, -18), boom=(-26, -12))


def render_accents(tl, ctx, voice_mono=None):
    """Each accent is rendered on its own, then scaled so its peak sits a fixed
    distance below the voice peak around the word (clamped to a sane range)."""
    N = ns(tl["total"])
    dry = np.zeros((2, N))
    hall = np.zeros((2, N))
    booms = ctx.sfx_times("boom") + ctx.sfx_times("implode") + ctx.sfx_times("boom_small")
    rng = np.random.default_rng(77)
    for ac in tl["accents"]:
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
            put(celesta(m, 0.62), 0.0, 1.0, 0.15, 0.45)
            put(glock(m + 12, 0.28), 0.01, 0.7, 0.3, 0.6)
            put(celesta(m - 12, 0.35), 0.005, 0.7, -0.1, 0.4)
        elif kind == "lo":
            r = root_note(ch, 38, 49)
            put(cello(r, 2.4, 0.75, 0.07, 1.2, 0.8), 0.0, 1.0, -0.05, 0.35)
            put(piano(r - 12, 0.5, 3.0, 0.3), 0.0, 0.8, 0.0, 0.35)
            put(strings([r + 7, r + 12], 2.4, 0.25, 1.4, 0.3, 0.45, 31), 0.0, 0.6, 0.0, 0.5)
        elif kind == "boom":
            r = root_note(ch, 36, 47)
            near = any(abs(b - ac["t"]) < 0.45 for b in booms)
            put(timpani(r, 0.9), 0.0, 0.6 if near else 1.0, 0, 0.4)
            third = r + 15 if 3 in [(i % 12) for i in ch["ivs"]] else r + 16
            put(strings([r, r + 7, r + 12, third], 1.6, 0.01, 1.6, 0.35, 0.8, 41), 0.0, 0.8, 0, 0.5)
        elif kind == "comic":
            r = root_note(ch, 45, 56)
            put(blip(r + 7, 0.11, 0.7, 0.0), 0.0, 1.0, 0.2, 0.15)
            put(blip(r, 0.2, 0.7, -0.06), 0.15, 1.0, 0.2, 0.15)
        elif kind == "swell":
            notes = voicing(ch, 66, 4) + [root_note(ch, 38, 49)]
            put(strings(notes, 1.7, 0.1, 2.2, 0.5, 0.75, 51, swell=True), -1.7, 1.0, 0, 0.5)
            put(glock(tones(ch, 86, 98)[0], 0.35), 0.0, 0.55, 0.35, 0.6)
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
