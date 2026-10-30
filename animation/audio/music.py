#!/usr/bin/env python3
"""Procedural score for "The Family Inside".

Usage:  python3 audio/music.py [cues.json]
        (default build/cues.json, falling back to build/cues_test.json, then to
        scene spans derived from build/schedule.json)

Writes build/music.wav (48 kHz, stereo, 16-bit, exactly schedule duration long)
and build/music_report.txt.  Everything is re-derived from schedule.json (line and
word timing) + cues.json (scene spans), so the score follows timing changes.
Deterministic: all randomness comes from seeded numpy generators.

Instruments (all synthesized here):
  piano    soft felt piano: inharmonic additive partials, two-stage per-partial
           decay, velocity-dependent brightness, felt hammer thud, damper release
  pad      warm string pad: 3 detuned polyBLEP saws per note, low-passed, slow
           attack/release, gentle vibrato; optional bowed tremolo
  cello    bowed solo cello / contrabass: saw pair + body-resonance filtering,
           delayed vibrato, pitch scoop, bow noise, slow swell
  celesta  celesta / glass bell / music box (bar-mode partial ratios, soft attack)
  pluck    Karplus-Strong plucked strings (pizzicato and guitar-like variants)
  thump    soft low drum / heartbeat;  timpani;  low brass swell / hit
Bus: synthetic stereo convolution reverb, high-pass, speech-band dip (~2.5 kHz),
gentle low-pass, loudness normalisation (~-24 LUFS) and peak safety (< -6 dBFS).
"""
import json
import os
import re
import sys
import time

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000          # output rate
SRL = 16000         # internal rate for band-limited sustained voices (pads, cello, brass)
UP = SR // SRL
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, 'build')

T_START = time.time()

# ----------------------------------------------------------------------------- data
sched = json.load(open(os.path.join(BUILD, 'schedule.json')))
DUR = float(sched['duration'])
N = int(round(DUR * SR))
LINES = {l['id']: l for l in sched['lines']}


def load_cues():
    cands = [sys.argv[1]] if len(sys.argv) > 1 else []
    cands += [os.path.join(BUILD, 'cues.json'), os.path.join(BUILD, 'cues_test.json')]
    for p in cands:
        if p and os.path.exists(p):
            return json.load(open(p)), p
    return None, None


CUES, CUE_PATH = load_cues()


def derive_scenes():
    """Fallback scene spans from the schedule when no cue file exists."""
    def lt(i, k):
        return LINES[i][k] if i in LINES else None
    spec = [('kitchen1', None, 'N1'), ('hearth1', 'N1', 'M5'), ('kitchen2', 'M5', 'F1'),
            ('hearth2', 'F1', 'NA1'), ('memory1', 'NA1', 'N16'), ('hearth3', 'N16', 'S4'),
            ('reflect', 'S4', 'E8'), ('porch', None, None), ('nanahouse', 'E8', 'N19'),
            ('end', 'N19', None)]
    out = []
    for name, a, b in spec:
        t0 = 0.0 if a is None else lt(a, 't0') - 0.4
        t1 = DUR if b is None else lt(b, 't0') - 0.4
        if name == 'porch':
            continue
        out.append({'name': name, 't0': max(0.0, t0), 't1': t1})
    # carve a porch span out of the start of nanahouse
    for s in out:
        if s['name'] == 'nanahouse':
            out.append({'name': 'porch', 't0': s['t0'] - 8.0, 't1': s['t0'] - 4.0})
            s['t0'] -= 4.0
    for s in out:
        if s['name'] == 'reflect':
            s['t1'] = min(s['t1'], [x for x in out if x['name'] == 'porch'][0]['t0'])
    return out


SCENE_LIST = CUES['scenes'] if CUES and CUES.get('scenes') else derive_scenes()
SC = {s['name']: (float(s['t0']), float(s['t1'])) for s in SCENE_LIST}


def scn(name, default=None):
    if name in SC:
        return SC[name]
    return default


def lt0(i, d=None):
    return LINES[i]['t0'] if i in LINES else d


def lt1(i, d=None):
    return LINES[i]['t1'] if i in LINES else d


def norm_word(w):
    w = w.lower()
    w = ''.join(c for c in w if c.isalnum() or c == "'")
    return w.strip("'")


def wt(i, word, key='t0', d=None):
    if i not in LINES:
        return d
    tag = norm_word(word)
    for w in LINES[i]['words']:
        if norm_word(w['w']) == tag:
            return w[key]
    return d


# ----------------------------------------------------------------------------- buses
DRY = np.zeros((2, N))
SEND = np.zeros(N)


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def pan_gains(p):
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.cos(th) * np.sqrt(2), np.sin(th) * np.sqrt(2)


def place(sig, t, pan=0.0, gain=1.0, rev=0.3):
    """Add mono (n,) or stereo (2,n) signal at time t (s) to the dry bus + reverb send."""
    if sig.ndim == 1:
        gl, gr = pan_gains(pan)
        st = np.vstack([sig * gl, sig * gr])
    else:
        st = sig
    i0 = int(round(t * SR))
    n = st.shape[1]
    a, b = 0, n
    if i0 < 0:
        a = -i0
        i0 = 0
    if i0 >= N or a >= n:
        return
    b = min(n, a + (N - i0))
    seg = st[:, a:b] * gain
    DRY[:, i0:i0 + (b - a)] += seg
    SEND[i0:i0 + (b - a)] += seg.mean(axis=0) * rev


def fade_edges(x, sr, fin=0.004, fout=0.01):
    n = len(x)
    a = min(n // 2, max(1, int(fin * sr)))
    b = min(n // 2, max(1, int(fout * sr)))
    x[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    x[n - b:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
    return x


def rc_env(n, sr, att, hold, rel):
    """Raised-cosine attack, hold until `hold` s, raised-cosine release of `rel` s."""
    t = np.arange(n) / sr
    e = np.ones(n)
    if att > 0:
        m = t < att
        e[m] = 0.5 - 0.5 * np.cos(np.pi * t[m] / att)
    m = t > hold
    if rel > 0:
        e[m] *= np.clip(0.5 + 0.5 * np.cos(np.pi * (t[m] - hold) / rel), 0, 1) * (t[m] - hold < rel)
    else:
        e[m] = 0
    return e


def seed_of(*xs):
    h = 2166136261
    for x in xs:
        for c in repr(round(x, 4) if isinstance(x, float) else x).encode():
            h = ((h ^ c) * 16777619) & 0xFFFFFFFF
    return h


def rng_for(*xs):
    return np.random.default_rng(seed_of(*xs))


def up(x):
    return signal.resample_poly(x, UP, 1)


def saw(freq, sr, phase0=0.0):
    """PolyBLEP saw for a per-sample frequency array."""
    dt = freq / sr
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2.0 * ph - 1.0
    m = ph < dt
    x = ph[m] / dt[m]
    y[m] -= x + x - x * x - 1.0
    m = ph > 1.0 - dt
    x = (ph[m] - 1.0) / dt[m]
    y[m] -= x * x + x + x + 1.0
    return y


_SOS = {}


def sos(kind, f, sr, order=2, q=None):
    key = (kind, round(f if np.isscalar(f) else tuple(f), 3) if np.isscalar(f) else tuple(f), sr, order)
    if key not in _SOS:
        if kind == 'bp':
            _SOS[key] = signal.butter(order, f, 'bandpass', fs=sr, output='sos')
        else:
            _SOS[key] = signal.butter(order, f, kind, fs=sr, output='sos')
    return _SOS[key]


def lp(x, f, sr, order=2):
    return signal.sosfilt(sos('lowpass', min(f, sr * 0.45), sr, order), x)


def hp(x, f, sr, order=2):
    return signal.sosfilt(sos('highpass', f, sr, order), x)


def bp(x, f0, f1, sr, order=1):
    return signal.sosfilt(sos('bp', (f0, f1), sr, order), x)


# ----------------------------------------------------------------------------- harmony
PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
QUAL = {'': [0, 4, 7], 'm': [0, 3, 7], 'm7': [0, 3, 7, 10], 'm9': [0, 3, 7, 10, 14],
        'maj7': [0, 4, 7, 11], 'maj9': [0, 4, 7, 11, 14], 'add9': [0, 4, 7, 14],
        '7': [0, 4, 7, 10], 'sus4': [0, 5, 7], 'sus2': [0, 2, 7], '7sus4': [0, 5, 7, 10],
        '9sus4': [0, 5, 7, 10, 14], 'm7b5': [0, 3, 6, 10], 'maj7#11': [0, 4, 7, 11, 18],
        'madd9': [0, 3, 7, 14], '6': [0, 4, 7, 9]}


def pcname(s):
    v = PC[s[0]]
    for c in s[1:]:
        v += {'b': -1, '#': 1}[c]
    return v % 12


def note(s):
    """'D3' -> midi."""
    mm = re.match(r'([A-G][b#]?)(-?\d)', s)
    return pcname(mm.group(1)) + 12 * (int(mm.group(2)) + 1)


class Chord:
    def __init__(self, sym):
        self.sym = sym
        base, _, bass = sym.partition('/')
        mm = re.match(r'([A-G][b#]?)(.*)', base)
        self.root = pcname(mm.group(1))
        self.ints = QUAL[mm.group(2)]
        self.pcs = sorted({(self.root + i) % 12 for i in self.ints})
        self.bass = pcname(bass) if bass else self.root

    def tones(self, lo, hi, core=False):
        pcs = self.pcs
        if core:  # root / third / fifth only (+7th) for cleaner arpeggios
            pcs = sorted({(self.root + i) % 12 for i in self.ints if i < 12})
        return [m for m in range(lo, hi + 1) if m % 12 in pcs]

    def bass_in(self, lo):
        m = lo
        while m % 12 != self.bass:
            m += 1
        return m

    def root_in(self, lo):
        m = lo
        while m % 12 != self.root:
            m += 1
        return m

    def voicing(self, low=52, top=76, bass_lo=38):
        r = self.root_in(low)
        ups = []
        for i in self.ints:
            m = r + i
            while m > top:
                m -= 12
            if m not in ups:
                ups.append(m)
        return [self.bass_in(bass_lo)] + sorted(ups)


TIMELINE = []   # (t0, t1, Chord)


def prog(t0, t1, syms, dur=None):
    """Lay chords sequentially from t0 to t1 (dur=None -> split evenly)."""
    if t1 <= t0:
        return []
    if dur is None:
        dur = (t1 - t0) / len(syms)
    out = []
    t, k = t0, 0
    while t < t1 - 1e-6:
        e = min(t1, t + dur)
        if t1 - e < dur * 0.35:
            e = t1
        out.append((t, e, Chord(syms[k % len(syms)])))
        t, k = e, k + 1
    TIMELINE.extend(out)
    return out


def chord_at(t):
    best = None
    for a, b, c in TIMELINE:
        if a <= t < b:
            best = c
    if best is None:
        prev = [x for x in TIMELINE if x[0] <= t]
        best = max(prev, key=lambda x: x[0])[2] if prev else Chord('Dm')
    return best


# ----------------------------------------------------------------------------- instruments
def piano(m, t, vel=0.5, hold=1.5, pan=None, rev=0.32, gain=1.0):
    f = mtof(m)
    rng = rng_for('pno', m, t)
    vel = float(np.clip(vel, 0.05, 1.0))
    tau1 = float(np.clip(3.2 * (261.6 / f) ** 0.65, 0.7, 9.0))
    damp = 0.16 if m > 40 else 0.3
    nlen = int(min(hold + damp * 6 + 0.05, tau1 * 5.0) * SR)
    nlen = max(nlen, int(0.25 * SR))
    tt = np.arange(nlen) / SR
    y = np.zeros(nlen)
    B = 0.00025 * (f / 261.6) ** 0.7
    fc = 450 + 2600 * vel ** 1.6 + 1.2 * f
    tot = 0.0
    for k in range(1, 30):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > 7500:
            break
        a = (1.0 / k) * (0.25 + abs(np.sin(np.pi * k / 8.3))) / (1 + (fk / fc) ** 2)
        if a < 2e-4:
            continue
        tk = tau1 / (1 + 0.45 * (k - 1) * (f / 261.6) ** 0.4)
        nk = min(nlen, int(tk * 7.0 * SR) + 64)
        ts = tt[:nk]
        ph = rng.uniform(0, 2 * np.pi)
        e = 0.6 * np.exp(-ts / (tk * 0.22)) + 0.4 * np.exp(-ts / tk)
        part = np.sin(2 * np.pi * fk * ts + ph)
        if k <= 3:   # second string, slightly detuned -> gentle beating
            part = 0.62 * part + 0.38 * np.sin(2 * np.pi * fk * (1.0006 + 0.0003 * k) * ts + ph * 1.7)
        y[:nk] += a * e * part
        tot += a
    y /= max(tot, 1e-9) ** 0.85
    # felt hammer thud
    nh = int(0.03 * SR)
    hn = rng.standard_normal(nh) * np.exp(-np.arange(nh) / (0.005 * SR))
    hn = lp(hn, 700 + 900 * vel, SR)
    y[:nh] += hn * 0.05 * vel
    # damper
    m_ = tt > hold
    y[m_] *= np.exp(-(tt[m_] - hold) / damp)
    y = fade_edges(y, SR, 0.002, 0.03)
    amp = 0.48 * vel ** 1.25
    if pan is None:
        pan = np.clip((m - 60) / 45.0, -0.45, 0.45)
    place(y, t, pan, amp * gain, rev)


BELL_TYPES = {
    #            ratios                        amps                       taus (at C5)
    'celesta': ([1.0, 2.0, 3.01, 4.16, 5.43], [1, .30, .07, .14, .04], [2.0, .8, .45, .3, .18]),
    'glass':   ([1.0, 2.76, 5.40, 8.93],      [1, .16, .05, .015],      [2.6, .7, .3, .12]),
    'musicbox': ([1.0, 2.0, 3.9, 6.1],        [1, .18, .10, .03],       [1.1, .35, .15, .07]),
}


def bell(m, t, vel=0.5, kind='celesta', pan=0.3, rev=0.5, gain=1.0, length=None):
    f = mtof(m)
    ratios, amps, taus = BELL_TYPES[kind]
    sc = (523.0 / f) ** 0.5
    L = length or min(6.0, max(taus) * sc * 6)
    nlen = int(L * SR)
    tt = np.arange(nlen) / SR
    y = np.zeros(nlen)
    rng = rng_for('bell', m, t, kind)
    for r, a, ta in zip(ratios, amps, taus):
        fk = f * r
        if fk > 9000:
            continue
        a = a * (0.6 + 0.6 * vel) ** (r - 1) / (1 + (fk / 5000) ** 2)
        y += a * np.exp(-tt / (ta * sc)) * np.sin(2 * np.pi * fk * tt + rng.uniform(0, 6.28))
    y = fade_edges(y, SR, 0.004 if kind != 'musicbox' else 0.002, 0.05)
    place(y, t, pan, 0.16 * vel * gain, rev)


def pluck(m, t, vel=0.5, length=1.0, kind='pizz', pan=0.0, rev=0.25, gain=1.0):
    """Karplus-Strong with fractional delay (linear interp) inside the loop."""
    f = mtof(m)
    rng = rng_for('pl', m, t, kind)
    P = SR / f - 0.5          # loop lowpass adds 0.5 sample delay
    Nd = int(np.floor(P))
    d = P - Nd                # extra linear-interp delay
    if d < 0.0:
        d += 1
        Nd -= 1
    t60 = (0.55 if kind == 'pizz' else 2.6) * (220 / f) ** 0.35
    g = 0.001 ** (1.0 / (f * t60))
    c = np.array([0.5 * (1 - d), 0.5, 0.5 * d]) * g  # taps at Nd, Nd+1, Nd+2
    nlen = int(length * SR)
    exc = rng.uniform(-1, 1, Nd + 2)
    bright = (0.25 if kind == 'pizz' else 0.55) + 0.35 * vel
    exc = signal.lfilter([1 - (1 - bright)], [1, -(1 - bright)], exc)
    exc = lp(np.concatenate([exc, np.zeros(64)]), (900 if kind == 'pizz' else 1800) + 2200 * vel, SR, 2)[:Nd + 2]
    exc /= np.abs(exc).max() + 1e-9
    pos = max(1, int(Nd * (0.18 if kind == 'pizz' else 0.13)))
    exc = exc - np.concatenate([np.zeros(pos), exc[:-pos]])
    x = np.zeros(nlen + Nd + 3)
    y = np.zeros(nlen + Nd + 3)
    x[:len(exc)] = exc
    off = Nd + 2
    # y[n] = x[n] + c0*y[n-Nd] + c1*y[n-Nd-1] + c2*y[n-Nd-2]; chunk size Nd keeps refs in the past
    yb = np.zeros(nlen + off)
    xb = np.concatenate([np.zeros(off), x[:nlen]])
    for s in range(off, nlen + off, Nd):
        e = min(s + Nd, nlen + off)
        yb[s:e] = xb[s:e] + c[0] * yb[s - Nd:e - Nd] + c[1] * yb[s - Nd - 1:e - Nd - 1] + c[2] * yb[s - Nd - 2:e - Nd - 2]
    y = yb[off:]
    if kind == 'guitar':
        y = 0.8 * y + 0.9 * bp(y, 90, 260, SR)
        y = lp(y, 3200 + 1500 * vel, SR)
    else:
        y = lp(y, 1500 + 1500 * vel, SR)
    y = hp(y, 50, SR)
    y = fade_edges(y, SR, 0.001, 0.05)
    y /= 0.6
    place(y, t, pan, (0.42 if kind == 'pizz' else 0.36) * vel * gain, rev)


def pad(notes, t0, t1, gain=0.1, att=1.5, rel=1.8, cutoff=1300, detune=7.0, vib=0.0025,
        trem_rate=0.0, trem_depth=0.0, width=0.65, gfun=None, rev=0.5, cut_end=None):
    """Warm string pad (or tremolo strings). cut_end: cutoff ramps to this by t1."""
    if t1 <= t0:
        return
    dur = t1 - t0
    nlen = int((dur + rel) * SRL)
    tt = np.arange(nlen) / SRL
    L = np.zeros(nlen)
    R = np.zeros(nlen)
    voices = [(-detune, -1.0), (detune * 0.35, 0.15), (detune, 1.0)]
    for k, m in enumerate(notes):
        f = mtof(m)
        rng = rng_for('pad', m, t0, k)
        nv = np.zeros(nlen)
        for vi, (cents, side) in enumerate(voices):
            fr = f * 2 ** (cents / 1200.0)
            lfo = vib * np.sin(2 * np.pi * rng.uniform(4.6, 5.6) * tt + rng.uniform(0, 6.28))
            drift = 0.0012 * np.sin(2 * np.pi * rng.uniform(0.07, 0.2) * tt + rng.uniform(0, 6.28))
            v = saw(fr * (1 + lfo + drift), SRL, rng.uniform())
            if trem_rate > 0:
                r_ = trem_rate * rng.uniform(0.94, 1.06)
                ph = 2 * np.pi * r_ * tt + rng.uniform(0, 6.28)
                am = 1 - trem_depth * (0.5 + 0.5 * np.cos(ph)) ** 1.5
                v = v * am
            gl, gr = pan_gains(side * width * (0.6 + 0.4 * (k % 2)))
            L += v * gl
            R += v * gr
    sc = 1.0 / np.sqrt(len(notes) * len(voices))
    env = rc_env(nlen, SRL, att, dur, rel)
    if gfun is not None:
        env = env * gfun(t0 + tt)
    out = []
    for ch in (L, R):
        if cut_end is None:
            y = lp(lp(ch, cutoff, SRL), cutoff * 1.6, SRL)
        else:  # crossfade dark->bright versions (cheap time-varying filter)
            dark = lp(lp(ch, cutoff, SRL), cutoff * 1.6, SRL)
            brt = lp(lp(ch, cut_end, SRL), cut_end * 1.6, SRL)
            x = np.clip(tt / max(dur, 1e-3), 0, 1)
            y = dark * (1 - x) + brt * x
        y = hp(y, 45, SRL)
        out.append(y * env * sc)
    st = np.vstack([fade_edges(up(o), SR, 0.01, 0.05) for o in out])
    place(st, t0, 0, gain, rev)


def cello(m, t, dur=2.5, vel=0.5, att=0.4, rel=0.6, pan=-0.3, rev=0.38, gain=1.0, deep=False,
          vib=1.0):
    f = mtof(m)
    rng = rng_for('vc', m, t)
    nlen = int((dur + rel) * SRL)
    tt = np.arange(nlen) / SRL
    vdepth = 0.0042 * vib * np.clip((tt - 0.25) / 0.6, 0, 1)
    vrate = 5.2 + 0.3 * np.sin(2 * np.pi * 0.3 * tt)
    vph = 2 * np.pi * np.cumsum(vrate) / SRL
    scoop = -0.007 * np.exp(-tt / 0.07)
    fr = f * (1 + vdepth * np.sin(vph) + scoop)
    x = saw(fr, SRL, rng.uniform()) + 0.45 * saw(fr * 1.0025, SRL, rng.uniform())
    bow = lp(rng.standard_normal(nlen), 1800, SRL) * 0.05
    x = x + bow
    cut = (700 if deep else 1100) + 900 * vel
    y = (0.55 * lp(x, cut, SRL) + 0.9 * bp(x, 180, 320, SRL) + 0.5 * bp(x, 420, 620, SRL)
         + (0.0 if deep else 0.22) * bp(x, 950, 1300, SRL))
    y = lp(y, cut * 1.3, SRL)
    y = hp(y, 28 if deep else 40, SRL)
    # swell envelope: rounded attack, slight crescendo, release
    e = rc_env(nlen, SRL, att, dur, rel) * (0.85 + 0.15 * np.clip(tt / max(dur, .1), 0, 1))
    y = up(y * e)
    y = fade_edges(y, SR, 0.01, 0.04)
    place(y, t, pan, 0.11 * vel * gain, rev)


def brass(notes, t, dur=2.5, vel=0.6, att=0.05, rel=0.9, hit=True, pan=-0.1, rev=0.45, gain=1.0):
    nlen = int((dur + rel) * SRL)
    tt = np.arange(nlen) / SRL
    x = np.zeros(nlen)
    for k, m in enumerate(notes):
        f = mtof(m)
        rng = rng_for('br', m, t, k)
        for c in (-4, 4):
            fr = f * 2 ** (c / 1200) * (1 + 0.002 * np.sin(2 * np.pi * 4.8 * tt + rng.uniform(0, 6)))
            x += saw(fr, SRL, rng.uniform())
    x /= np.sqrt(2 * len(notes))
    env = rc_env(nlen, SRL, att, dur, rel)
    if hit:
        env *= 0.42 + 0.58 * np.exp(-tt / 0.45)
        b = np.exp(-tt / 0.35)
    else:
        b = np.clip(tt / max(dur, 0.1), 0, 1) ** 1.5 * 0.8
    dark = lp(lp(x, 380, SRL), 600, SRL)
    brt = lp(lp(x, 1500, SRL), 2200, SRL)
    y = (dark * (1 - b) + brt * b) * env
    y = hp(y, 30, SRL)
    y = fade_edges(up(y), SR, 0.005, 0.05)
    place(y, t, pan, 0.22 * vel * gain, rev)


def thump(t, f0=55, vel=0.5, decay=0.18, pan=0.0, rev=0.08, gain=1.0):
    nlen = int((decay * 7 + 0.05) * SR)
    tt = np.arange(nlen) / SR
    fr = f0 * (1 + 0.7 * np.exp(-tt / 0.025))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) * np.exp(-tt / decay)
    rng = rng_for('th', t)
    cl = lp(rng.standard_normal(nlen), 260, SR) * np.exp(-tt / 0.01) * 0.25
    y = fade_edges(y + cl, SR, 0.002, 0.03)
    place(y, t, pan, 0.42 * vel * gain, rev)


def heartbeat(t, vel=0.5, gain=1.0):
    thump(t, 52, vel, 0.14, gain=gain)
    thump(t + 0.27, 47, vel * 0.7, 0.16, gain=gain)


def timpani(m, t, vel=0.7, pan=0.0, rev=0.35, gain=1.0):
    f = mtof(m)
    nlen = int(4.0 * SR)
    tt = np.arange(nlen) / SR
    rng = rng_for('timp', m, t)
    y = np.zeros(nlen)
    glide = 1 + 0.025 * np.exp(-tt / 0.12)
    for r, a, ta in zip([1, 1.504, 1.742, 2.0, 2.245, 2.494], [1, .55, .32, .25, .14, .09],
                        [1.4, .8, .6, .5, .35, .25]):
        ph = 2 * np.pi * np.cumsum(f * r * glide) / SR + rng.uniform(0, 6)
        y += a * np.sin(ph) * np.exp(-tt / ta)
    st = lp(rng.standard_normal(nlen), 900, SR) * np.exp(-tt / 0.018) * 0.6
    y = fade_edges(y + st, SR, 0.001, 0.05)
    place(y, t, pan, 0.20 * vel * gain, rev)


# ----------------------------------------------------------------------------- helpers for patterns
def pick(pool, idx):
    if not pool:
        return None
    return pool[int(idx) % len(pool)] if idx >= 0 else pool[max(0, len(pool) + int(idx))]


def humanize(t, amt=0.012):
    r = rng_for('hz', t)
    return t + r.uniform(-amt, amt), r.uniform(0.9, 1.08)


def piano_bars(t0, t1, bar, pattern, lo=57, hi=76, vel=0.4, lh=((0, 0),), lh_lo=36, lh_vel=0.85,
               gfun=None, core=True, hold=1.6):
    """Generic piano: per bar, LH bass events [(beat_frac, interval)] + RH pattern
    [(bar_frac, tone_index, vel_mul)] picking chord tones in [lo, hi]."""
    t = t0
    while t < t1 - 0.05:
        g = gfun(t) if gfun else 1.0
        for off, iv in lh:
            te = t + off * bar
            if te >= t1:
                continue
            c = chord_at(te + 0.01)
            m = c.bass_in(lh_lo) + iv
            if iv == 7 and (m % 12) not in c.pcs:
                m = c.bass_in(lh_lo) + 12
            tj, vj = humanize(te, 0.006)
            piano(m, tj, vel * lh_vel * vj * g, hold=bar * 0.95)
        for ev in pattern:
            off, idx, vm = ev[:3]
            hl = ev[3] if len(ev) > 3 else hold
            te = t + off * bar
            if te >= t1 - 0.02:
                continue
            c = chord_at(te + 0.01)
            m = pick(c.tones(lo, hi, core), idx)
            if m is None:
                continue
            tj, vj = humanize(te)
            piano(m, tj, vel * vm * vj * g, hold=hl)
        t += bar


def pads_for(segs, gain=0.08, xf=1.2, low=52, top=74, bass_lo=38, **kw):
    """One pad per chord segment with crossfades."""
    for i, (a, b, c) in enumerate(segs):
        s = a - (xf / 2 if i > 0 else 0)
        pad(c.voicing(low, top, bass_lo), max(0, s), b + 0 * xf, gain=gain,
            att=xf if i > 0 else kw.pop('first_att', xf), rel=xf, **kw)


def ramp(ta, ga, tb, gb, curve=1.0):
    def f(t):
        x = np.clip((np.asarray(t) - ta) / max(tb - ta, 1e-6), 0, 1) ** curve
        return ga + (gb - ga) * x
    return f


REPORT = []


def rep(t0, t1, text):
    REPORT.append((t0, t1, text))


# ============================================================================= SCORE
def score():
    K1 = scn('kitchen1', (0.0, lt0('N1', 16.8) - 0.5))
    H1 = scn('hearth1', (K1[1], lt0('M5', 78) - 1))
    K2 = scn('kitchen2', (H1[1], lt0('F1', 112.5) - 0.3))
    H2 = scn('hearth2', (K2[1], lt0('NA1', 178) - 2))
    ME = scn('memory1', (H2[1], lt0('N16', 183) - 0.4))
    H3 = scn('hearth3', (ME[1], lt0('S4', 197) - 0.5))
    RF = scn('reflect', (H3[1], lt1('R12', 254.6) + 0.6))
    PO = scn('porch', (RF[1] + 0.7, RF[1] + 4.3))
    NH = scn('nanahouse', (PO[1], lt1('E10', 274.4) + 0.5))
    EN = scn('end', (NH[1], DUR))

    # ---------------------------------------------------------------- kitchen1
    k1_end = H1[0]
    cd = K1[1] / 4.0
    segs = prog(0.0, K1[1], ['Dm9', 'Bbmaj7', 'Fmaj7', 'Gm9'], cd)
    bar = cd
    # sparse felt piano, ~60 bpm (bar = 4 beats of ~1 s)
    piano_bars(0.0, K1[1] - 0.3, bar,
               [(0.0, 3, 0.85, 2.6), (0.25, 5, 0.6, 1.8), (0.5, 4, 0.65, 2.2), (0.8, 6, 0.45, 1.5)],
               lo=57, hi=77, vel=0.36, lh=((0, 0), (0.5, 7)), lh_lo=36, lh_vel=0.8)
    # the film opens mid-moment: a soft string bed already sounding at t=0
    pad(Chord('Dm9').voicing(50, 69, 38), 0.0, cd * 1.05, gain=0.035, att=0.03, rel=2.0, cutoff=800)
    # rising swell into the inner world
    sw0 = max(K1[1] - 3.2, 0.5)
    pad(Chord('Gm9').voicing(55, 77, 43), sw0, k1_end + 0.25, gain=0.09, att=0.4, rel=0.9,
        cutoff=650, cut_end=2200, gfun=ramp(sw0, 0.0, k1_end, 1.0, 2.2))
    asc = Chord('Gm9').tones(67, 86)
    ta = K1[1] - 1.2
    for i, m in enumerate(asc[:7]):
        bell(m, ta + i * 0.17, 0.25 + 0.05 * i, 'celesta', pan=0.4 - 0.12 * i, rev=0.7)
    rep(0, K1[1], 'kitchen1: sparse solo felt piano (~60 bpm) Dm9-Bbmaj7-Fmaj7-Gm9, faint string bed from t=0; '
        'rising Gm9 string swell + ascending celesta into the inner world')

    # ---------------------------------------------------------------- hearth1
    a1 = lt0('A1', H1[0] + 6) - 0.35
    segs = prog(k1_end, a1, ['Fmaj9', 'Bbadd9/F', 'Fmaj7'])
    pads_for(segs, gain=0.085, xf=1.4, low=53, top=74, bass_lo=41, cutoff=1400, first_att=0.5)
    piano_bars(k1_end + 0.3, a1, (a1 - k1_end) / 3,
               [(0.05, 4, 0.5, 2.5), (0.55, 6, 0.4, 2.0)], lo=60, hi=79, vel=0.3, lh=())
    rep(k1_end, a1, 'hearth1 N1-N2: warm string pad swell Fmaj9 -> Bb/F -> Fmaj7, soft piano')

    hey = wt('G1', 'hey', d=lt0('G1', 41.7))
    pz_end = lt1('A4', hey - 0.8) + 0.15
    bt = 0.6
    segs = prog(a1, hey - 0.05, ['F', 'Gm7', 'C7', 'F', 'Dm7', 'Gm7', 'C7', 'F'], bt * 4)
    t = a1
    k = 0
    while t < pz_end - 0.1:
        c = chord_at(t + 0.01)
        b0 = c.bass_in(41)
        for off, mm, v in [(0, b0, 0.55), (2, b0 + 7 if (b0 + 7) % 12 in c.pcs else b0 + 12, 0.42)]:
            te = t + off * bt
            if te < pz_end:
                pluck(mm, te, v, 0.9, 'pizz', pan=-0.25)
        ups = c.tones(60, 74, True)
        pat = [(1.5, 1, 0.38), (2.5, 2, 0.33), (3.0, 3, 0.36)] if k % 2 == 0 else \
              [(1.0, 2, 0.33), (1.5, 1, 0.3), (3.5, 3, 0.36)]
        for off, idx, v in pat:
            te = t + off * bt
            if te >= pz_end:
                continue
            mm = pick(ups, idx)
            if (k + int(off * 2)) % 3 == 0:   # quirky chromatic grace from below
                pluck(mm - 1, te - 0.05, v * 0.6, 0.4, 'pizz', pan=0.3)
            pluck(mm, te, v, 0.8, 'pizz', pan=0.3)
        if k % 4 == 3 and t + 3.75 * bt < pz_end:
            bell(pick(c.tones(72, 86, True), 1), t + 3.75 * bt, 0.2, 'celesta', pan=0.45)
        t += 4 * bt
        k += 1
    rep(a1, pz_end, 'hearth1 A1-A4/N3/N4: light quirky pizzicato (Karplus-Strong) F-Gm7-C7-F, chromatic '
        'grace notes, little celesta ticks; stops after "Anybody?" leaving a short silence')

    # G1 HEY hit is played by the lo-tag handler (brass + timpani).
    n5 = lt0('N5', hey + 3.7)
    n6, n7, n8 = lt0('N6', n5 + 3.5), lt0('N7', n5 + 6.3), lt0('N8', n5 + 11.2)
    n8e = lt1('N8', n8 + 3.6)
    hum = wt('N8', 'humanity', d=n8e - 0.6)
    TIMELINE.append((hey - 0.05, n6 - 0.1, Chord('Dm')))
    TIMELINE.append((n6 - 0.1, n7 - 0.1, Chord('Em7b5')))
    TIMELINE.append((n7 - 0.1, n8 - 0.1, Chord('Gm')))
    TIMELINE.append((n8 - 0.1, n8e + 0.6, Chord('A7sus4')))
    TIMELINE.append((n8e + 0.6, lt0('M2', n8e + 2.4) - 0.4, Chord('A7')))
    os0 = lt1('G1', hey + 2.7) + 0.25
    os1 = n8e + 0.2
    e8 = 60.0 / 104 / 2
    t = os0
    i = 0
    gf = ramp(os0, 0.45, os1, 1.0)
    while t < os1:
        c = chord_at(t + 0.01)
        b0 = c.bass_in(38)
        fifth = b0 + [x for x in c.ints if x in (6, 7)][0]
        third = b0 + [x for x in c.ints if x in (3, 4, 5)][0]
        seq = [b0, b0, fifth, b0, b0 + 12, b0, fifth, third]
        mm = seq[i % 8]
        g = float(gf(t)) * (1.0 if i % 2 == 0 else 0.75)
        cello(mm, t, 0.17, 0.55 * g, att=0.015, rel=0.12, pan=-0.2, rev=0.25, vib=0.0)
        pluck(mm, t, 0.35 * g, 0.5, 'pizz', pan=0.15, rev=0.15)
        if i % 4 == 0:
            thump(t, 48, 0.32 * g, 0.16)
        t += e8
        i += 1
    brass(Chord('Gm').voicing(43, 55, 31), n7 - 0.3, max(0.5, n8 - n7), 0.35, att=2.5, rel=0.4,
          hit=False, gain=0.8)
    brass(Chord('A7sus4').voicing(45, 57, 33), n8 - 0.2, max(0.5, n8e - n8 + 1.0), 0.45, att=1.0,
          rel=1.6, hit=False, gain=0.8)
    pad(Chord('A7').voicing(45, 64, 33), n8e + 0.2, lt0('M2', n8e + 2.4) - 0.2, gain=0.06, att=0.8,
        rel=1.0, cutoff=700)
    rep(hey, os1, 'hearth1 G1-N8: brass+timpani hit on "HEY"; tense low ostinato (spiccato cello + pizz, '
        '104 bpm 8ths) rising D -> Em7b5 -> Gm -> A7sus4, low drum, low brass swells; deep A on "humanity"')

    m2 = lt0('M2', n8e + 2.4) - 0.4
    segs = prog(m2, H1[1], ['Bbmaj9', 'F/A', 'Gm9', 'C9sus4', 'Fadd9'])
    pads_for(segs, gain=0.11, xf=1.6, low=53, top=74, bass_lo=34, cutoff=1400, first_att=1.2)
    piano_bars(m2 + 0.2, H1[1] - 0.5, segs[0][1] - segs[0][0],
               [(0.0, 4, 0.5, 2.4), (0.4, 5, 0.4, 2.0), (0.7, 3, 0.35, 1.6)], lo=60, hi=79, vel=0.3,
               lh=((0, 0),), lh_lo=36, lh_vel=0.8)
    rep(m2, H1[1], 'hearth1 M2-N9: tension resolves (A7 -> Bbmaj9 deceptive cadence), warm pad + piano '
        'Bbmaj9-F/A-Gm9-C9sus4-Fadd9')

    # ---------------------------------------------------------------- kitchen2
    m8e = lt1('M8', K2[0] + 15) + 0.7
    segs = prog(K2[0], m8e, ['Dm9', 'Bbmaj7', 'Fmaj7', 'Gm9'])
    bar = segs[0][1] - segs[0][0]
    piano_bars(K2[0], m8e - 0.2, bar,
               [(0.0, 3, 0.8, 2.4), (0.25, 4, 0.55, 1.6), (0.5, 5, 0.6, 2.0), (0.75, 4, 0.45, 1.4)],
               lo=57, hi=76, vel=0.34, lh=((0, 0), (0.5, 7)), lh_lo=36, lh_vel=0.8)
    pads_for(segs, gain=0.06, xf=1.5, low=50, top=69, bass_lo=38, cutoff=900, first_att=2.0)
    # E5-E6: almost silence, a single faint held D fading away
    m9 = lt0('M9', m8e + 7.5) - 0.45
    TIMELINE.append((m8e, m9, Chord('Dm')))
    pad([50, 57], m8e - 0.6, m8e + 1.5, gain=0.035, att=0.6, rel=2.5, cutoff=600)
    rep(K2[0], m8e, 'kitchen2 M5-M8: tender piano + soft low strings Dm9-Bbmaj7-Fmaj7-Gm9')
    rep(m8e, m9, 'kitchen2 E5-E6: thinned to silence (a faint held D fades out) for Eli\'s confession')

    op = wt('N10', 'open', d=lt0('N10', m9 + 3) + 2)
    segs = prog(m9, op - 0.1, ['Bbmaj7', 'Gm9', 'C9sus4'])
    pads_for(segs, gain=0.085, xf=1.6, low=53, top=72, bass_lo=34, cutoff=1000, first_att=2.2,
             gfun=ramp(m9, 0.6, op, 1.0))
    piano_bars(m9 + 0.6, op - 0.2, (op - 0.1 - m9) / 3, [(0.1, 4, 0.5, 2.2), (0.55, 3, 0.4, 1.8)],
               lo=60, hi=77, vel=0.28, lh=((0, 0),), lh_lo=36, lh_vel=0.75)
    n10e = lt1('N10', op + 1.9) + 1.2
    prog(op - 0.1, n10e, ['Fadd9'])
    pad(Chord('Fadd9').voicing(53, 77, 41), op - 0.6, n10e, gain=0.14, att=0.9, rel=2.2, cutoff=1100,
        cut_end=1900)
    piano(Chord('F').bass_in(29), op - 0.03, 0.45, hold=3.0)
    piano(65, op - 0.02, 0.35, hold=3.0)
    piano(69, op, 0.32, hold=3.0)
    rep(m9, n10e, 'kitchen2 M9-N10: strings re-enter Bbmaj7-Gm9-C9sus4, bell on "alone", warm Fadd9 swell '
        'arriving on "open"')
    prog(n10e, K2[1], ['Bbmaj7#11/E'])
    cello(note('E2'), n10e - 0.4, K2[1] - n10e + 0.6, 0.5, att=1.2, rel=1.2, pan=-0.25)
    pad([58, 62, 65, 69, 64], n10e - 0.6, K2[1] + 0.2, gain=0.05, att=1.4, rel=1.0, cutoff=900,
        trem_rate=5.5, trem_depth=0.35)
    rep(n10e, K2[1], 'kitchen2 E7: uneasy Bbmaj7#11 over low cello E (tritone), light tremolo')

    # ---------------------------------------------------------------- hearth2
    jump = wt('N12', 'jumping', d=lt0('N12', H2[0] + 7) + 0.7)
    n13, n13e = lt0('N13', jump + 1.2), lt1('N13', jump + 4)
    f3 = lt0('F3', n13e + 11)
    f4 = lt0('F4', f3 + 2.3)
    pour = wt('F4', 'pour', 't1', d=lt1('F4', f4 + 3) - 0.8)
    m11 = lt0('M11', lt1('F4', f4 + 4) + 5) - 0.3
    f5e = lt1('F5', m11 + 4) + 1.2
    prog(H2[0], jump - 0.05, ['Dm9'])
    prog(jump - 0.05, n13 - 0.1, ['Bbmaj7'])
    prog(n13 - 0.1, n13e + 0.3, ['Dm'])
    prog(n13e + 0.3, f3 - 0.1, ['Gm9', 'Bbmaj7', 'A7sus4', 'Dm9'])
    prog(f3 - 0.1, f4 - 0.1, ['Dm'])
    prog(f4 - 0.1, lt0('N15', f4 + 4.5) - 0.2, ['Bbmaj7'])
    prog(lt0('N15', f4 + 4.5) - 0.2, m11, ['Gm9', 'A7sus4'])
    # heartbeat: lub-dub, slows from ~80 to ~64 bpm, stops at M11
    t = H2[0] + 0.2
    while t < m11 - 0.3:
        x = (t - H2[0]) / max(m11 - H2[0], 1)
        g = 0.55 if x < 0.5 else 0.55 - 0.5 * (x - 0.5)
        heartbeat(t, g)
        t += 0.75 + 0.2 * x
    # trembling string tremolo, nervous
    for a, b, c in [x for x in TIMELINE if x[0] >= H2[0] - 0.01 and x[1] <= m11 + 0.01]:
        if a >= n13 - 0.2 and b <= n13e + 0.4:
            continue
        pad(c.voicing(50, 68, 38), a - 0.4, b + 0.2, gain=0.065, att=0.6, rel=0.6, cutoff=1100,
            trem_rate=7.5, trem_depth=0.6, vib=0.004)
    # tiger leap accent
    timpani(note('D2'), jump - 0.03, 0.55)
    for mm in Chord('Bbmaj7').tones(50, 65, True)[:4]:
        pluck(mm, jump - 0.02, 0.6, 0.7, 'pizz', pan=0.1)
    brass([note('Bb1'), note('F2'), note('Bb2')], jump - 0.04, 0.5, 0.45, att=0.02, rel=0.5, hit=True)
    # roller-coaster lift hill: steady clicking climb up the D minor scale
    scale = [m for m in range(50, 74) if m % 12 in (2, 4, 5, 7, 9, 10, 0)]
    nst = len(scale)
    span = n13e - n13 - 0.1
    for i, mm in enumerate(scale):
        x = i / (nst - 1)
        te = n13 + span * (x ** 0.92)
        pluck(mm, te, 0.3 + 0.25 * x, 0.6, 'pizz', pan=-0.3 + 0.6 * x)
        if i % 2 == 0:
            piano(mm + 12, te + 0.005, 0.18 + 0.15 * x, hold=0.4)
    pad([38, 45, 50], n13 - 0.3, n13e + 0.3, gain=0.07, att=0.4, rel=0.6, cutoff=800, cut_end=1500,
        trem_rate=8.0, trem_depth=0.5)
    bell(scale[-1] + 12, n13e + 0.25, 0.35, 'glass', pan=0.3)
    # watery descending arpeggio after "pour"
    wat = Chord('Bbmaj7').tones(62, 84)[::-1]
    tt_ = pour + 0.05
    for i, mm in enumerate(wat):
        bell(mm, tt_, 0.33 - 0.015 * i, 'celesta', pan=0.5 - 0.1 * (i % 6), rev=0.75)
        tt_ += 0.11 + 0.012 * i
    rep(H2[0], m11, 'hearth2 F1-N15: soft lub-dub heartbeat (slowing), trembling string tremolo Dm9/Bb/Gm9/A7sus4; '
        'timpani+pizz+brass stab on "jumping"; climbing pizz/piano scale through N13; low notes on "funeral", '
        '"water"; descending watery celesta arpeggio after "pour"')
    # resolve during M11-F5
    segs = prog(m11, f5e, ['Bbmaj7', 'F'])
    pads_for(segs, gain=0.09, xf=1.5, low=53, top=72, bass_lo=34, cutoff=1100, first_att=1.0)
    rep(m11, f5e, 'hearth2 M11-F5: tension resolves into warm Bbmaj7 -> F pad')
    # very tender solo piano + cello, D minor
    tp0 = f5e - 0.3
    segs = prog(tp0, H2[1], ['Dm', 'Bbmaj7', 'Gm9', 'Asus4', 'Dm9', 'Bbmaj7', 'C7sus4'])
    bar = segs[0][1] - segs[0][0]
    piano_bars(tp0, H2[1] - 0.2, bar,
               [(0.0, 3, 0.75, 2.6), (0.25, 4, 0.5, 1.8), (0.5, 5, 0.55, 2.0), (0.75, 4, 0.4, 1.5)],
               lo=57, hi=76, vel=0.33, lh=((0, 0), (0.5, 7)), lh_lo=36, lh_vel=0.8)
    targets = [57, 55, 53, 52, 53, 57, 55, 53]
    prev = 57
    for i, (a, b, c) in enumerate(segs):
        if i == 0:
            continue
        pool = c.tones(45, 62)
        mm = min(pool, key=lambda q: abs(q - targets[i % len(targets)]) + 0.3 * abs(q - prev))
        prev = mm
        cello(mm, a + 0.1, b - a - 0.2, 0.42, att=0.9, rel=0.9, pan=-0.3)
    pad(Chord('Dm').voicing(50, 65, 38), tp0, H2[1], gain=0.03, att=3, rel=1.5, cutoff=700)
    rep(tp0, H2[1], 'hearth2 S1-M15: very tender solo piano with cello counter-line, D minor '
        'Dm-Bbmaj7-Gm9-Asus4-Dm9-Bbmaj7-C7sus4')

    # ---------------------------------------------------------------- memory1
    bar = (ME[1] - ME[0]) / 3.15
    bt = bar / 3
    segs = prog(ME[0], ME[1], ['F', 'Bb/F', 'C7/E', 'F'], bar)
    pads_for(segs, gain=0.06, xf=0.8, low=53, top=69, bass_lo=41, cutoff=1000, first_att=0.6)
    mel = [[('C5', 0), ('F5', 1), ('A5', 2)], [('G5', 0), ('F5', 1), ('D5', 2)],
           [('E5', 0), ('G5', 1), ('Bb5', 2)], [('A5', 0)]]
    for bi, ev in enumerate(mel):
        for nm, b in ev:
            te = ME[0] + 0.15 + bi * bar + b * bt
            if te < ME[1] + 0.3:
                bell(note(nm), te, 0.32, 'musicbox', pan=0.3, rev=0.55)
        c = chord_at(ME[0] + bi * bar + 0.2)
        te = ME[0] + 0.15 + bi * bar
        if te < ME[1]:
            piano(c.bass_in(41), te, 0.3, hold=bar)
            piano(c.tones(57, 67, True)[1], te + bt, 0.22, hold=bt * 1.5)
            piano(c.tones(57, 67, True)[1], te + 2 * bt, 0.2, hold=bt * 1.5)
    rep(ME[0], ME[1], 'memory1: warm music-box lullaby in F major (3/4) over soft pad + piano oom-pah')

    # ---------------------------------------------------------------- hearth3
    segs = prog(ME[1], H3[1], ['Bbmaj9', 'F/A', 'Gm9', 'Csus4', 'F'])
    pads_for(segs, gain=0.09, xf=1.4, low=53, top=72, bass_lo=34, cutoff=1200, first_att=0.8)
    bar = segs[0][1] - segs[0][0]
    piano_bars(ME[1] + 0.1, H3[1] - 0.2, bar,
               [(0.0, 4, 0.55, 2.2), (0.33, 5, 0.4, 1.8), (0.66, 3, 0.4, 1.6)], lo=60, hi=79,
               vel=0.3, lh=((0, 0),), lh_lo=36)
    rep(ME[1], H3[1], 'hearth3: tender comforting pad + piano Bbmaj9-F/A-Gm9-Csus4-F')

    # ---------------------------------------------------------------- reflect
    r9 = lt0('R9', RF[0] + 40) - 0.25
    world = wt('R12', 'world', d=lt1('R12', RF[1] - 1) - 0.4)
    nb = max(4, int(round((r9 - RF[0]) / 6.7)))
    segs1 = prog(RF[0], r9, ['Dm9', 'Bbmaj7', 'Fmaj7', 'Cadd9'], (r9 - RF[0]) / nb)
    segs2 = prog(r9, world - 0.03, ['Bbmaj9', 'F/A', 'Gm9', 'Dm9', 'Bbmaj7', 'Csus4', 'C'])
    climax_end = RF[1] + 1.2
    prog(world - 0.03, climax_end, ['Fadd9'])
    gpno = ramp(RF[0], 0.7, world, 1.25, 1.3)
    # piano ostinato, steady 8ths (72 bpm)
    e8 = 60.0 / 72 / 2
    pat = [0, 2, 1, 3, 0, 2, 1, 3]
    t = RF[0] + 0.1
    i = 0
    while t < world - 0.1:
        c = chord_at(t + 0.01)
        pool = c.tones(57, 74, True)
        mm = pick(pool, pat[i % 8] + (1 if (i // 16) % 2 else 0))
        acc = 1.0 if i % 4 == 0 else 0.78
        tj, vj = humanize(t, 0.006)
        piano(mm, tj, 0.27 * acc * vj * float(gpno(t)), hold=e8 * 1.6)
        t += e8
        i += 1
    for a, b, c in segs1 + segs2:
        piano(c.bass_in(36), a + 0.01, 0.34 * float(gpno(a)), hold=b - a)
        if b - a > 3:
            piano(c.bass_in(36) + 12, a + (b - a) / 2, 0.24 * float(gpno(a)), hold=(b - a) / 2)
    # strings swelling gradually
    r2 = lt0('R2', RF[0] + 6)
    gstr = ramp(r2, 0.22, world, 1.0, 1.6)
    allseg = [s for s in segs1 if s[1] > r2] + segs2
    for i, (a, b, c) in enumerate(allseg):
        s = max(a - 0.8, r2)
        pad(c.voicing(52, 76, 38), s, b + 0.0, gain=0.13, att=1.6 if i else 4.0, rel=1.6,
            cutoff=900 + 900 * float(gstr(a)), gfun=gstr)
    # cello line from R4
    r4 = lt0('R4', RF[0] + 15)
    prev = 57
    for a, b, c in [s for s in segs1 + segs2 if s[0] >= r4 - 0.5]:
        pool = c.tones(45, 64)
        tgt = 52 + 9 * (a - r4) / max(world - r4, 1)
        mm = min(pool, key=lambda q: abs(q - tgt) + 0.4 * abs(q - prev))
        prev = mm
        cello(mm, a + 0.05, b - a - 0.1, 0.35 + 0.3 * float(gstr(a)), att=1.0, rel=0.9, pan=-0.35)
    # build: soft timpani pulses + low brass swell R11-R12
    for a, b, c in segs2:
        timpani(c.bass_in(38) if c.bass_in(38) < 46 else c.bass_in(38) - 12, a, 0.25 + 0.2 * float(gstr(a)))
    r11 = lt0('R11', world - 9)
    brass(Chord('Bbmaj9').voicing(46, 58, 34)[:3], r11, max(1.0, world - r11 - 2.6), 0.32, att=3.0,
          rel=1.2, hit=False, gain=0.8)
    brass(Chord('C').voicing(48, 60, 36), world - 3.0, 2.9, 0.38, att=1.5, rel=0.6, hit=False, gain=0.8)
    # climax on "world": F major
    fv = [note('F1'), note('F2'), note('C3'), note('F3'), note('A3'), note('C4'), note('G4'), note('A4')]
    for k_, mm in enumerate(fv):
        piano(mm, world - 0.03 + 0.012 * k_, 0.55 - 0.02 * k_, hold=3.5)
    pad(Chord('Fadd9').voicing(53, 79, 41) + [note('C3')], world - 0.35, climax_end, gain=0.19, att=0.35,
        rel=2.5, cutoff=1900)
    brass([note('F2'), note('C3'), note('F3')], world - 0.05, climax_end - world, 0.42, att=0.2,
          rel=1.8, hit=False, gain=0.85)
    timpani(note('F2'), world - 0.04, 0.6)
    cello(note('F2'), world - 0.1, climax_end - world, 0.6, att=0.3, rel=1.8)
    rep(RF[0], r9, 'reflect S4-R8: slow build - piano 8th-note ostinato (72 bpm) Dm9-Bbmaj7-Fmaj7-Cadd9, strings '
        'swelling gradually from R2, cello line from R4; low notes on "suffering", deep on "meaningless"')
    rep(r9, climax_end, 'reflect R9-R12: faster harmonic rhythm Bbmaj9-F/A-Gm9-Dm9-Bbmaj7-Csus4-C, timpani pulses, '
        'low brass swell, climax F major (full piano, strings, brass, timpani) on "world"')

    # ---------------------------------------------------------------- porch / nanahouse
    g0 = PO[0]
    g1 = NH[1]
    bar = 3.0
    segs = prog(g0, g1, ['F', 'C/E', 'Dm7', 'Bbadd9'], bar)
    gg = ramp(g0, 0.35, g0 + 6.0, 1.0)
    e8 = bar / 8
    gpat = [0, 2, 3, 4, 1, 3, 2, 4]
    t = g0
    i = 0
    while t < g1 - 0.1:
        c = chord_at(t + 0.01)
        if i % 8 == 0:
            mm = c.bass_in(40)
        else:
            mm = pick(c.tones(52, 72, True), gpat[i % 8])
        tj, vj = humanize(t, 0.01)
        pluck(mm, tj, (0.42 if i % 8 == 0 else 0.32) * vj * float(gg(t)), 2.4, 'guitar', pan=-0.3, rev=0.3)
        t += e8
        i += 1
    piano_bars(g0 + bar, g1 - 0.3, bar, [(0.0, 4, 0.55, 2.0), (0.5, 3, 0.4, 1.5)], lo=65, hi=81,
               vel=0.26, lh=())
    pad(Chord('F').voicing(53, 69, 41), g0 + 2, g1, gain=0.035, att=4, rel=2, cutoff=800)
    rep(g0, g1, 'porch/nanahouse E8-E10: gentle morning - Karplus-Strong guitar arpeggios (80 bpm) + light piano, '
        'F-C/E-Dm7-Bbadd9 in F major')

    # ---------------------------------------------------------------- end
    n20 = lt0('N20', EN[0] + 5)
    n20e = lt1('N20', n20 + 3)
    fin = n20e + 0.15
    segs = prog(EN[0], fin, ['Bbmaj9', 'Csus4', 'C'],)
    segs = [(EN[0], n20 - 0.1, Chord('Bbmaj9')), (n20 - 0.1, n20 + 1.4, Chord('C9sus4')),
            (n20 + 1.4, fin, Chord('C'))]
    TIMELINE[:] = [x for x in TIMELINE if not (x[0] >= EN[0] - 1e-6)] + segs
    pads_for(segs, gain=0.1, xf=1.4, low=53, top=74, bass_lo=34, cutoff=1300, first_att=1.0)
    piano_bars(EN[0] + 0.1, fin - 0.2, (n20 - EN[0]) / 2,
               [(0.0, 4, 0.5, 2.0), (0.33, 5, 0.4, 1.8), (0.66, 3, 0.4, 1.6)], lo=60, hi=79, vel=0.3,
               lh=((0, 0),), lh_lo=36)
    cello(note('Bb2'), EN[0] + 0.2, n20 - EN[0] - 0.4, 0.4, att=1.2, rel=0.8)
    cello(note('C3'), n20 - 0.1, fin - n20, 0.42, att=0.8, rel=0.6)
    prog(fin, DUR + 1, ['Fadd9'])
    tail = DUR - fin
    fv = [note('F1'), note('F2'), note('C3'), note('F3'), note('A3'), note('C4'), note('G4'), note('A4')]
    for k_, mm in enumerate(fv):
        piano(mm, fin + 0.03 * k_, 0.42 - 0.02 * k_, hold=tail)
    pad(Chord('Fadd9').voicing(53, 77, 41), fin - 0.4, DUR + 0.5, gain=0.13, att=1.2, rel=1.0, cutoff=1400)
    cello(note('F2'), fin, tail + 0.5, 0.45, att=1.5, rel=0.5)
    bell(note('C6'), fin + 1.8, 0.42, 'celesta', pan=0.35, rev=0.7, length=6.0)
    bell(note('F6'), fin + 3.6, 0.25, 'glass', pan=0.45, rev=0.75, length=5.0)
    rep(EN[0], DUR, 'end N19-N20: warm pad/piano/cello Bbmaj9-C9sus4-C, then sustained Fadd9 final chord with '
        'last celesta/glass high notes ringing; fade over the final 2 s')
    return dict(K1=K1, H1=H1, K2=K2, H2=H2, ME=ME, H3=H3, RF=RF, PO=PO, NH=NH, EN=EN)


# ----------------------------------------------------------------------------- hi / lo tags
HITS = []


def scene_at(t):
    nm = None
    for s in SCENE_LIST:
        if s['t0'] <= t < s['t1']:
            nm = s['name']
    if nm is None:
        prev = [s for s in SCENE_LIST if s['t0'] <= t]
        nm = max(prev, key=lambda s: s['t0'])['name'] if prev else 'kitchen1'
    return nm


def tags():
    hi_last = [81]
    for l in sched['lines']:
        for kind in ('hi', 'lo'):
            for tag in l.get(kind, []):
                tw = wt(l['id'], tag)
                if tw is None:
                    HITS.append((None, kind, l['id'], tag, None, 'NOT FOUND'))
                    continue
                sc = scene_at(tw)
                if kind == 'hi':
                    t = tw - 0.03
                    c = chord_at(tw + 0.05)
                    pool = c.tones(76, 88)
                    tgt = 81 + (4 if hi_last[-1] <= 79 else -3)
                    if sc == 'reflect':
                        tgt = 84 if l['id'] == 'R12' else 81
                    mm = min(pool, key=lambda q: abs(q - tgt))
                    hi_last.append(mm)
                    if sc == 'memory1':
                        bell(mm, t, 0.8, 'musicbox', pan=0.25, rev=0.6)
                        bell(mm - 12, t, 0.25, 'celesta', pan=0.25)
                        inst = 'music box'
                    elif sc == 'reflect':
                        bell(mm, t, 0.6, 'celesta', pan=0.3, rev=0.65)
                        bell(mm + 12 if mm + 12 < 96 else mm, t + 0.005, 0.18, 'glass', pan=0.4, rev=0.7)
                        pad([mm, mm - 12], t - 0.15, t + 2.0, gain=0.07, att=0.25, rel=2.2,
                            cutoff=3800, width=0.4, rev=0.6)
                        inst = 'celesta + glass + high strings'
                    elif sc in ('porch', 'nanahouse'):
                        g = max(q for q in c.tones(70, mm - 1)) if c.tones(70, mm - 1) else mm - 2
                        bell(g, t - 0.075, 0.35, 'celesta', pan=0.4)
                        bell(mm, t, 0.5, 'celesta', pan=0.3)
                        pluck(mm - 12, t, 0.3, 1.5, 'guitar', pan=0.3)
                        inst = 'celesta grace + main, guitar'
                    else:
                        bell(mm, t, 0.55, 'celesta', pan=0.3)
                        pad([mm], t - 0.1, t + 1.6, gain=0.045, att=0.3, rel=1.8, cutoff=3500,
                            width=0.3, rev=0.6)
                        inst = 'celesta + high string'
                    HITS.append((t, kind, l['id'], tag, mm, inst))
                else:
                    t = tw - 0.05
                    c = chord_at(tw + 0.08)
                    if tag.lower() == 'hey':
                        brass([note('D2'), note('A2'), note('D3'), note('F3')], t, 2.6, 0.9, att=0.03,
                              rel=1.2, hit=True)
                        timpani(note('D2'), t, 1.0)
                        timpani(note('D2'), t + 0.004, 0.4, pan=0.2)
                        thump(t, 40, 0.8, 0.3)
                        cello(note('D2'), t, 2.4, 0.6, att=0.04, rel=1.0, deep=True)
                        HITS.append((t, kind, l['id'], tag, note('D2'), 'low brass + timpani hit'))
                        continue
                    mm = c.bass_in(36)
                    deep = tag.lower() in ('humanity', 'meaningless')
                    cello(mm, t, 2.6, 0.9, att=0.1, rel=1.2, pan=-0.2)
                    piano(mm - 12 if mm - 12 >= 28 else mm, t, 0.45, hold=2.0, pan=-0.2)
                    inst = 'cello + low piano (octave below)'
                    if deep:
                        cello(mm - 12, t, 3.2, 0.9, att=0.12, rel=1.6, pan=0.0, deep=True)
                        thump(t, 42, 0.45, 0.35)
                        inst = 'cello + contrabass octave + low piano + thump'
                    HITS.append((t, kind, l['id'], tag, mm, inst))


# ----------------------------------------------------------------------------- reverb + master
def make_ir(seed=7, length=3.2):
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    pre = int(0.018 * SR)
    irs = []
    for ch in range(2):
        noise = rng.standard_normal(n)
        lo_ = lp(noise, 450, SR, 2)
        mid = bp(noise, 450, 3000, SR, 2)
        hi_ = hp(noise, 3000, SR, 2)
        late = (lo_ * np.exp(-6.9 * t / 2.6) + mid * np.exp(-6.9 * t / 2.0)
                + 0.5 * hi_ * np.exp(-6.9 * t / 0.9))
        late *= 1 - np.exp(-t / 0.03)            # build-up
        ir = np.zeros(n + pre)
        ir[pre:] = late
        for k in range(10):                       # early reflections
            d = pre + int(rng.uniform(0.004, 0.075) * SR)
            ir[d] += rng.uniform(0.3, 0.8) * (1 if rng.uniform() > 0.5 else -1) * 3
        ir = ir[:n]
        ir = fade_edges(ir, SR, 0.0, 0.2)
        irs.append(ir)
    irs = np.array(irs)
    irs /= np.sqrt((irs ** 2).sum(axis=1).mean())
    return irs


def biquad_peak(f0, gain_db, q, sr):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return np.array(b) / a[0], np.array(a) / a[0]


def lufs(x):
    """BS.1770-4 integrated loudness (48 kHz)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=-1), axis=-1)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    ms = []
    for s in range(0, y.shape[1] - blk, hop):
        ms.append((y[:, s:s + blk] ** 2).mean(axis=1).sum())
    ms = np.array(ms)
    L = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[L > -70]
    if len(g) == 0:
        return -99.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = ms[(L > -70) & (L > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def master():
    ir = make_ir()
    wet = np.vstack([signal.oaconvolve(SEND, ir[0])[:N], signal.oaconvolve(SEND, ir[1])[:N]])
    mix = DRY + 0.55 * wet
    b, a = biquad_peak(2500, -4.5, 0.6, SR)            # keep out of the speech band
    mix = signal.lfilter(b, a, mix, axis=-1)
    b, a = biquad_peak(3800, -2.0, 1.0, SR)
    mix = signal.lfilter(b, a, mix, axis=-1)
    mix = signal.sosfilt(signal.butter(2, 32, 'highpass', fs=SR, output='sos'), mix, axis=-1)
    mix = signal.sosfilt(signal.butter(2, 10000, 'lowpass', fs=SR, output='sos'), mix, axis=-1)
    mix -= mix.mean(axis=1, keepdims=True)
    # final fade (last ~2 s) and 5 ms safety fade-in
    nf = int(2.0 * SR)
    mix[:, N - nf:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nf))) ** 1.2
    mix[:, :int(0.005 * SR)] *= np.linspace(0, 1, int(0.005 * SR))
    # loudness normalise to ~-24 LUFS, then peak safety
    L0 = lufs(mix)
    mix *= 10 ** ((-24.0 - L0) / 20)
    thr = 10 ** (-6.5 / 20)
    pk = np.abs(mix).max(axis=0)
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = maximum_filter1d(pk, int(0.01 * SR))
    g = np.minimum(1.0, thr / np.maximum(env, 1e-9))
    g = uniform_filter1d(maximum_filter1d(-g, int(0.02 * SR)) * -1, int(0.01 * SR))
    mix *= g
    mix = np.clip(mix, -thr, thr)
    return mix, L0, float((g < 0.999).mean())


# ----------------------------------------------------------------------------- main
def main():
    spans = score()
    tags()
    t_syn = time.time() - T_START
    mix, L0, limfrac = master()
    out = os.path.join(BUILD, 'music.wav')
    sf.write(out, mix.T.astype(np.float32), SR, subtype='PCM_16')
    rt = time.time() - T_START

    # ---------------- verification
    lines = []
    P = lines.append
    P('The Family Inside - procedural score report (audio/music.py)')
    P(f'cues: {CUE_PATH or "derived from schedule.json"}')
    P(f'duration: schedule {DUR:.3f} s, music {mix.shape[1] / SR:.3f} s ({mix.shape[1]} samples @ {SR} Hz, stereo, 16-bit)')
    fin = np.isfinite(mix).all()
    pk = float(np.abs(mix).max())
    Lf = lufs(mix)
    P(f'finite: {fin}   peak: {20 * np.log10(pk + 1e-12):.2f} dBFS   integrated loudness: {Lf:.2f} LUFS '
      f'(pre-norm {L0:.1f})   limiter active on {100 * limfrac:.2f}% of samples   DC: {mix.mean(axis=1).round(6).tolist()}')
    P(f'render time: {rt:.1f} s (synthesis {t_syn:.1f} s)')
    P('')
    P('RMS per scene (dBFS):')
    for s in SCENE_LIST:
        a, b = int(s['t0'] * SR), int(min(s['t1'], DUR) * SR)
        seg = mix[:, a:b]
        r = np.sqrt((seg ** 2).mean()) if b > a else 0
        P(f'  {s["name"]:10s} {s["t0"]:7.2f}-{s["t1"]:7.2f}  RMS {20 * np.log10(r + 1e-12):6.1f}  '
          f'peak {20 * np.log10(np.abs(seg).max() + 1e-12) if b > a else -99:6.1f}')
    P('')
    P('Spectrum (energy share by band, whole score):')
    mono = mix.mean(axis=0)
    f, pxx = signal.welch(mono, SR, nperseg=8192)
    tot = pxx.sum()
    for lo_, hi_ in [(0, 60), (60, 250), (250, 1000), (1000, 4000), (4000, 8000), (8000, 24000)]:
        m = (f >= lo_) & (f < hi_)
        P(f'  {lo_:5d}-{hi_:5d} Hz  {100 * pxx[m].sum() / tot:6.2f}%')
    P('')
    P('hi/lo hits (note time = word t0 - 30 ms for hi, - 50 ms for lo):')
    for h in sorted(HITS, key=lambda x: (x[0] is None, x[0] or 0)):
        t, kind, lid, tag, mm, inst = h
        if t is None:
            P(f'  {kind} {lid:4s} "{tag}": NOT FOUND in words')
            continue
        tw = wt(lid, tag)
        names = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
        P(f'  {kind}  {lid:4s} "{tag:11s}" word t0 {tw:8.3f}  note {t:8.3f}  {names[mm % 12]}{mm // 12 - 1:<2d} '
          f'({mtof(mm):6.1f} Hz)  [{scene_at(tw)}]  {inst}')
    P('')
    P('What plays when:')
    for a, b, txt in sorted(REPORT):
        P(f'  {a:7.2f}-{b:7.2f}  {txt}')
    P('')
    P('Chord timeline:')
    seen = []
    for a, b, c in sorted(TIMELINE, key=lambda x: x[0]):
        seen.append(f'{a:.1f}:{c.sym}')
    P('  ' + '  '.join(seen))
    P('')
    P('Notes: hi notes are chord tones of the current chord in E5-E6 (celesta / music box / glass + soft high '
      'strings); lo notes are the chord bass in C2-B2 on cello + low piano an octave below (contrabass octave + thump for '
      '"humanity"/"meaningless"; "HEY" = low brass + timpani on D). Bus: synthetic stereo convolution reverb, '
      '32 Hz HPF, -4.5 dB dip at 2.5 kHz + -2 dB at 3.8 kHz (speech band), 10 kHz LPF, normalised to -24 LUFS, '
      'peak ceiling -6.5 dBFS. The mix step is expected to duck this bed under voices.')
    txt = '\n'.join(lines)
    open(os.path.join(BUILD, 'music_report.txt'), 'w').write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
