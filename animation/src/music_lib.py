"""Brindle Cross -- deterministic music-cue renderer.

Every cue is composed in code as note lists (in beats), mapped through a
tempo map (ritardando / accelerando), humanised with a seeded RNG (micro-
timing, velocities, chord spread, legato CC64 pedalling), written as a
Standard MIDI File, rendered with fluidsynth + FluidR3_GM (its own reverb and
chorus off) and post-processed with numpy/scipy: per-stem EQ, a synthetic-IR
room reverb, gated-RMS normalisation, a look-ahead peak limiter and fades.

Public API
----------
    render_cue(name, out_wav, duration, **params) -> dict
        {'path', 'duration', 'sr', 'events': [beat times, s],
         'downbeats': [bar starts, s], 'markers': {...}, 'tempo', 'peak_db', 'rms_db'}
    CUES           tuple of cue names
    MOTIF          the four-note name motif, MIDI pitches A4 G4 F4 C5 (F major, quarters)
    MOTIF_DEGREES  (3, 2, 1, 5)
    pitch(), chord(), voice(), write_wav(), TempoMap   helpers

Every cue fills exactly round(duration*48000) samples. The structure (number of
bars, intro/tag bars) and a tempo trim (within about +/-10 %) are chosen so the
music ends on its own cadence with a natural ring-out. Very short requests
start part-way into the closing cadence instead of rushing the tempo
(name_piano and civic_slow keep the whole motif down to ~5 s, by
allowing up to +30 % tempo and a shorter ring before trimming).

Cues and params (all cues also accept seed=int (humanisation), gain_db=float,
reverb=float (wet multiplier), fade_out=seconds, pcm16=bool, and cut=bool: stop dead
at `duration` mid-phrase -- the cue is composed longer and cut with a 30 ms fade,
markers['stop'] = duration; for civic/civic_slow it means end='cut'). Unknown
parameters raise TypeError instead of being silently ignored:
    civic        C major walking theme, solo piano, ~88 bpm, dry and slightly
                 vintage-EQ'd.   end='phrase'|'cut', tempo=88, intro_bars=None (0-3, cut mode)
    rag          honky-tonk ragtime in F (2/4, stride LH in 8ths, GM0 + detuned GM0 +
                 GM3 layers), starts with a two-note pickup.   stop_at=None (s), tempo=112
                 stop_at: a C7(b9) chord is struck 0.1-0.4 s before stop_at and the
                 music is cut dead at stop_at (30 ms fade), silence afterwards;
                 markers['stop'] == stop_at (clamped to [0.15, duration]).
    tiptoe       pizzicato (GM45) sneak in D minor, ends with one ride-bell tap
                 (markers['bell']).   tempo=100
    vamp         lazy swung F6 <-> Bb9 honky-tonk vamp, winds down, rolled F6/9.  tempo=84
    cello_note   single pp cello (GM42) note, swells in and fades.   pitch='C2'
    name_piano   motif stated plainly, then a tender continuation, quiet F cadence.
                 with_strings=False, strings_at=None (s; default half-way), tempo=60
    rag_motif    the motif picked up on the honky-tonk, accelerating into the rag;
                 cymbal crash + full stride at crash_at.   crash_at=None (s, >= 0.6),
                 stop_at=None, tempo=112
                 Default crash_at is ~45 % of duration (of stop_at when stop_at is given).
                 stop_at after the crash: hanging C7(b9) + cut as in 'rag'; stop_at at or
                 before the crash: plain 30 ms cut at stop_at. When no build-up plan can
                 be stretched to fill the time before the crash (e.g. crash_at > ~48 s),
                 the build-up starts late, after silence (markers['motif'] says when).
    civic_slow   civic theme at ~66 bpm in F with the motif folded in (bar 3 and the
                 coda), piano + faint string pad.   end='phrase'|'cut', tempo=66,
                 key='F' (any note name; 'C' = down a 4th)
    final_chord  one soft rolled add9 piano chord.   key='F' (any note name), roll=0.12,
                 with_strings=None (auto: a faint pad holds the chord when duration > 14 s)

Output: 48 kHz stereo WAV (float32, or 16-bit with pcm16=True), byte-identical
for identical arguments, peak <= -1 dBFS, DC-free, 8 ms fade-in.
"""
import inspect
import itertools
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
FLUIDSYNTH = shutil.which('fluidsynth') or '/usr/bin/fluidsynth'
PEAK_CEIL_DB = -1.0

CUES = ('civic', 'rag', 'tiptoe', 'vamp', 'cello_note', 'name_piano',
        'rag_motif', 'civic_slow', 'final_chord')

# --------------------------------------------------------------------------
# pitch / chord helpers
# --------------------------------------------------------------------------
_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
_NOTE_RE = re.compile(r'([A-Ga-g])([#b]*)(-?\d)$')


def pitch(name):
    """'C4' -> 60, 'Bb3' -> 58, 'F#5' -> 78. Ints pass through."""
    if isinstance(name, (int, np.integer)):
        return int(name)
    m = _NOTE_RE.match(name.strip())
    if not m:
        raise ValueError('bad note name %r' % name)
    pc = _PC[m.group(1).upper()] + m.group(2).count('#') - m.group(2).count('b')
    return 12 * (int(m.group(3)) + 1) + pc


def _pc(name):
    return (_PC[name[0].upper()] + name[1:].count('#') - name[1:].count('b')) % 12


MOTIF_DEGREES = (3, 2, 1, 5)
MOTIF = (pitch('A4'), pitch('G4'), pitch('F4'), pitch('C5'))   # F major, quarters

_QUAL = {
    '': (0, 4, 7), 'm': (0, 3, 7), '7': (0, 4, 7, 10), 'm7': (0, 3, 7, 10),
    'maj7': (0, 4, 7, 11), '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9),
    'dim': (0, 3, 6), 'dim7': (0, 3, 6, 9), '9': (0, 4, 7, 10, 14),
    'maj9': (0, 4, 7, 11, 14), 'add9': (0, 4, 7, 14), 'sus4': (0, 5, 7),
    '7sus4': (0, 5, 7, 10), 'm9': (0, 3, 7, 10, 14), '7b9': (0, 4, 7, 10, 13),
    '69': (0, 4, 7, 9, 14),
}
_CHORD_RE = re.compile(r'([A-G][#b]?)([^/]*)(?:/([A-G][#b]?))?$')


def chord(sym):
    """'C7' -> {'root','pcs','ivs','bass'} (pitch classes)."""
    m = _CHORD_RE.match(sym)
    if not m or m.group(2) not in _QUAL:
        raise ValueError('bad chord %r' % sym)
    root = _pc(m.group(1))
    ivs = _QUAL[m.group(2)]
    pcs = [(root + i) % 12 for i in ivs]
    bass = _pc(m.group(3)) if m.group(3) else root
    return {'root': root, 'pcs': pcs, 'ivs': ivs, 'bass': bass}


def voice(sym, lo, hi, prev=None, n=3, max_span=12):
    """Close voicing of `sym` with n notes in [lo, hi], voice-led from prev.

    Always keeps the 3rd (and the 7th when the chord has one)."""
    c = chord(sym)
    pcs = list(dict.fromkeys(c['pcs']))
    need = set()
    if len(c['ivs']) > 1:
        need.add(c['pcs'][1])
    if len(c['ivs']) > 3 and c['ivs'][3] in (9, 10, 11):
        need.add(c['pcs'][3])
    cand = [p for p in range(lo, hi + 1) if p % 12 in pcs]
    best, bcost = None, 1e9
    centre = (lo + hi) / 2.0
    for combo in itertools.combinations(cand, n):
        if combo[-1] - combo[0] > max_span:
            continue
        s = set(p % 12 for p in combo)
        if not need <= s:
            continue
        if len(s) < min(n, len(pcs)):
            continue
        if any(b - a < 2 for a, b in zip(combo, combo[1:])) and n <= 3:
            cost_cl = 1.5
        else:
            cost_cl = 0.0
        if prev:
            pv = sorted(prev)
            cost = sum(abs(a - b) for a, b in zip(combo, pv[:len(combo)]))
        else:
            cost = abs(np.mean(combo) - centre)
        if c['root'] not in s:
            cost += 0.8
        cost += cost_cl
        if cost < bcost:
            best, bcost = list(combo), cost
    if best is None:
        best = sorted(cand[:n])
    return best


def harmony_below(p, pcs, prefs=(3, 4, 8, 9, 5)):
    for d in prefs:
        if (p - d) % 12 in pcs:
            return p - d
    return None


# --------------------------------------------------------------------------
# note-string parser:  'C5:1.5 B4:.5 A4 G4 | r:2 G#4~A4:.5 C4+E4+G4:1>'
#   ':d' duration in beats (carried over), 'r' rest, '+' chord,
#   'X~Y' grace note X into Y, trailing '>' accent, '|' bar line.
# --------------------------------------------------------------------------
def parse(s):
    out, t, dur = [], 0.0, 1.0
    for tok in s.split():
        if tok == '|':
            continue
        acc = tok.endswith('>')
        tok = tok.rstrip('>')
        if ':' in tok:
            body, d = tok.split(':')
            dur = float(d)
        else:
            body = tok
        if body != 'r':
            grace = None
            if '~' in body:
                g, body = body.split('~')
                grace = pitch(g)
            ps = [pitch(x) for x in body.split('+')]
            out.append({'o': t, 'd': dur, 'p': ps, 'acc': acc, 'grace': grace})
        t += dur
    return out, t


def parse_bar(s, length):
    notes, total = parse(s)
    if abs(total - length) > 1e-6:
        raise ValueError('bar %r is %.3f beats, expected %.3f' % (s, total, length))
    return notes


# --------------------------------------------------------------------------
# tempo map (bpm linearly interpolated between control points)
# --------------------------------------------------------------------------
class TempoMap:
    def __init__(self, pts, end_beat, t0=0.0):
        pts = sorted(pts)
        self.xs = np.array([p[0] for p in pts], float)
        self.ys = np.array([p[1] for p in pts], float)
        self.t0 = t0
        self.end = max(float(end_beat), 1e-3)
        g = np.linspace(0.0, self.end, int(self.end * 96) + 2)
        per = 60.0 / np.interp(g, self.xs, self.ys)
        cum = np.concatenate([[0.0], np.cumsum(0.5 * (per[1:] + per[:-1]) * np.diff(g))])
        self.g, self.cum = g, cum

    def bpm(self, b):
        return float(np.interp(b, self.xs, self.ys))

    def t(self, b):
        b = np.asarray(b, float)
        out = np.interp(b, self.g, self.cum)
        out = np.where(b > self.end, self.cum[-1] + (b - self.end) * 60.0 / self.ys[-1], out)
        out = np.where(b < 0, b * 60.0 / self.ys[0], out)
        out = out + self.t0
        return float(out) if out.ndim == 0 else out


def _rit_pts(bpm, end_beat, rit_beats, amount):
    """Constant tempo, then linear slowdown by `amount` over the last rit_beats."""
    if rit_beats <= 0 or amount <= 0:
        return [(0.0, bpm)]
    s = max(0.0, end_beat - rit_beats)
    return [(0.0, bpm), (s, bpm), (end_beat, bpm * (1.0 - amount))]


def _scale_pts(pts, k):
    return [(b, v * k) for b, v in pts]


def _choose(D, cands, tail_nom, tail_min, tail_max, tol):
    """cands: [(key, seconds_at_nominal_tempo)] -> (key, k, tail)."""
    best = None
    for cand in cands:
        key, T1 = cand[0], cand[1]
        pen = cand[2] if len(cand) > 2 else 0.0
        avail = D - tail_nom
        k = T1 / avail if avail > 0.05 else 99.0
        k = float(np.clip(k, 1 - tol, 1 + tol))
        tail = D - T1 / k
        cost = ((k - 1) / tol) ** 2 + 2.0 * ((tail - tail_nom) / (tail_max - tail_min)) ** 2
        if tail < tail_min:
            cost += 50 + 100 * (tail_min - tail)
        if tail > tail_max:
            cost += 10 + 5 * (tail - tail_max)
        cost += pen
        if best is None or cost < best[0]:
            best = (cost, key, k, tail, T1)
    cost, key, k, tail, T1 = best
    pre = 0.0
    if tail < tail_min:      # too short even at +tol: start part-way in (trim the head)
        want = max(D - tail_min, 0.4 * D)
        pre = T1 / k - want
        tail = D - want
    return key, k, tail, pre


def _trimmed_map(pts, end_beat, pre, t0):
    """TempoMap shifted so that `pre` seconds (rounded up to whole beats) of
    content fall before t=0. Returns (tm, first_kept_beat)."""
    if pre <= 1e-6:
        return TempoMap(pts, end_beat, t0=t0), 0.0
    tm0 = TempoMap(pts, end_beat)
    b = 0.0
    while tm0.t(b) < pre - 1e-6 and b < end_beat - 1:
        b += 1.0
    return TempoMap(pts, end_beat, t0=t0 - tm0.t(b)), b


# --------------------------------------------------------------------------
# score -> MIDI
# --------------------------------------------------------------------------
class Score:
    def __init__(self):
        self.notes = []      # [t, dur, pitch, vel, ch]
        self.ccs = []        # [t, ch, num, val]
        self.setup_ = {}     # ch -> dict

    def setup(self, ch, prog, bank=0, volume=100, pan=64, cents=0.0, expression=127):
        self.setup_[ch] = dict(prog=prog, bank=bank, volume=volume, pan=pan,
                               cents=cents, expression=expression)

    def note(self, t, dur, p, vel, ch):
        v = int(np.clip(round(vel), 1, 127))
        self.notes.append([max(0.004, float(t)), max(0.03, float(dur)), int(p), v, ch])

    def cc(self, t, ch, num, val):
        self.ccs.append([max(0.0, float(t)), ch, num, int(np.clip(round(val), 0, 127))])

    def pedal(self, chans, t, down):
        for ch in chans:
            self.cc(t, ch, 64, 127 if down else 0)

    def write_midi(self, path, end_time):
        evs = []   # (ms, order, bytes)
        for ch, s in sorted(self.setup_.items()):
            if ch != 9:
                evs.append((0, 0, bytes([0xB0 | ch, 0, s['bank']])))
                evs.append((0, 0, bytes([0xC0 | ch, s['prog']])))
            evs.append((0, 0, bytes([0xB0 | ch, 7, s['volume']])))
            evs.append((0, 0, bytes([0xB0 | ch, 10, s['pan']])))
            evs.append((0, 0, bytes([0xB0 | ch, 11, s['expression']])))
            evs.append((0, 0, bytes([0xB0 | ch, 91, 0])))
            evs.append((0, 0, bytes([0xB0 | ch, 93, 0])))
            if s['cents']:
                v = int(np.clip(8192 + round(8192 * s['cents'] / 200.0), 0, 16383))
                evs.append((0, 0, bytes([0xE0 | ch, v & 0x7F, v >> 7])))
        # resolve same-pitch overlaps per channel
        bykey = {}
        for n in self.notes:
            bykey.setdefault((n[4], n[2]), []).append(n)
        for lst in bykey.values():
            lst.sort(key=lambda n: n[0])
            for a, b in zip(lst, lst[1:]):
                if a[0] + a[1] > b[0] - 0.002:
                    a[1] = max(0.02, b[0] - 0.003 - a[0])
        for t, d, p, v, ch in self.notes:
            on = int(round(t * 1000)) + 5
            off = max(on + 1, int(round((t + d) * 1000)) + 5)
            evs.append((on, 2, bytes([0x90 | ch, p, v])))
            evs.append((off, 1, bytes([0x80 | ch, p, 0])))
        for t, ch, num, val in self.ccs:
            evs.append((int(round(t * 1000)) + 5, 1 if num == 64 and val == 0 else 3,
                        bytes([0xB0 | ch, num, val])))
        evs.append((int(round(end_time * 1000)) + 5, 9, bytes([0xBF, 110, 0])))
        evs.sort(key=lambda e: (e[0], e[1]))
        trk = bytearray(_vlq(0) + bytes([0xFF, 0x51, 3]) + (1000000).to_bytes(3, 'big'))
        last = 0
        for ms, _, b in evs:
            trk += _vlq(ms - last) + b
            last = ms
        trk += _vlq(0) + bytes([0xFF, 0x2F, 0])
        with open(path, 'wb') as f:      # tempo 1 s / quarter, 1000 ticks -> 1 tick = 1 ms
            f.write(b'MThd' + struct.pack('>IHHH', 6, 0, 1, 1000))
            f.write(b'MTrk' + struct.pack('>I', len(trk)) + bytes(trk))


def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


# --------------------------------------------------------------------------
# realisation: beats -> seconds with humanisation
# --------------------------------------------------------------------------
PIANO = [(0, 1.0, 0.0)]
HONKY = [(0, 1.0, 0.0), (1, 0.82, 0.006), (2, 0.78, -0.003)]


def _setup_piano(sc):
    sc.setup(0, 0, volume=100)


def _setup_honky(sc):
    sc.setup(0, 0, volume=100, pan=60)
    sc.setup(1, 0, volume=92, pan=70, cents=+12)      # detuned copy
    sc.setup(2, 3, volume=86, pan=64, cents=-4)       # GM 3 honky-tonk


def swing_map(b, ratio):
    if ratio is None or ratio == 0.5:
        return b
    i = np.floor(b + 1e-9)
    f = b - i
    f2 = np.where(f < 0.5, f * (ratio / 0.5), ratio + (f - 0.5) * ((1 - ratio) / 0.5))
    return i + f2


class Realiser:
    def __init__(self, score, tm, rng, layers=PIANO, sigma=0.006, vsd=3.0,
                 offsets=None, art=None, swing=None, spread=0.004, vel_fn=None, min_beat=0.0):
        self.sc, self.tm, self.rng = score, tm, rng
        self.min_beat = min_beat
        self.layers, self.sigma, self.vsd = layers, sigma, vsd
        self.offsets = offsets or {}
        self.art = art or {}
        self.swing = swing
        self.spread = spread
        self.vel_fn = vel_fn

    def bt(self, b):
        return self.tm.t(swing_map(b, self.swing))

    def add(self, items):
        groups = {}
        for it in items:
            if it['b'] < self.min_beat - 1e-6:
                continue
            groups.setdefault((round(it['b'], 4), it.get('kind', 'mel')), []).append(it)
        for (b, kind), grp in sorted(groups.items()):
            grp.sort(key=lambda it: it['p'])
            for rank, it in enumerate(grp):
                self._one(it, rank if kind in ('chord', 'harm', 'pad') else 0)

    def _one(self, it, rank):
        kind = it.get('kind', 'mel')
        b, d = it['b'], it['d']
        t0 = self.bt(b)
        t1 = self.bt(b + d)
        jit = float(np.clip(self.rng.normal(0, self.sigma), -2.5 * self.sigma, 2.5 * self.sigma))
        t = t0 + self.offsets.get(kind, 0.0) + jit + rank * self.spread
        if it.get('abs_t') is not None:
            t = it['abs_t']
        dur = it.get('dur_s') or max(0.04, (t1 - t0) * self.art.get(kind, 0.95))
        v = it['v'] + self.rng.normal(0, self.vsd)
        if self.vel_fn is not None:
            v = v * self.vel_fn(t)
        for ch, vs, dt in self.layers:
            lj = float(self.rng.normal(0, 0.0015)) if dt else 0.0
            self.sc.note(t + dt + lj, dur, it['p'], v * vs, ch)
            if it.get('grace') is not None:
                self.sc.note(t + dt - 0.055, 0.07, it['grace'], v * vs * 0.8, ch)


# --------------------------------------------------------------------------
# DSP
# --------------------------------------------------------------------------
def _biquad(kind, f0, gain_db=0.0, q=0.707):
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    if kind == 'pk':
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == 'ls':
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw),
             A * ((A + 1) - (A - 1) * cw - sa)]
        a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw),
             (A + 1) + (A - 1) * cw - sa]
    elif kind == 'hs':
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw),
             A * ((A + 1) + (A - 1) * cw - sa)]
        a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw),
             (A + 1) - (A - 1) * cw - sa]
    else:
        raise ValueError(kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def apply_eq(x, eq):
    for e in eq:
        kind = e[0]
        if kind in ('hp', 'lp'):
            sos = signal.butter(2, e[1], 'highpass' if kind == 'hp' else 'lowpass',
                                fs=SR, output='sos')
            x = signal.sosfilt(sos, x, axis=0)
        else:
            b, a = _biquad(kind, *e[1:])
            x = signal.lfilter(b, a, x, axis=0)
    return x


def make_ir(rt60=1.2, predelay=0.015, seed=7, damp=0.45, length=None):
    """Synthetic stereo room IR: sparse early reflections + band-split
    exponentially decaying noise (highs decay faster). Unit energy per channel."""
    n = int((length or min(4.0, rt60 * 1.15 + 0.1)) * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    lo_sos = signal.butter(2, 450, 'lowpass', fs=SR, output='sos')
    hi_sos = signal.butter(2, 3500, 'highpass', fs=SR, output='sos')
    ir = np.zeros((n, 2))
    for ch in range(2):
        noise = rng.standard_normal(n)
        lo = signal.sosfilt(lo_sos, noise)
        hi = signal.sosfilt(hi_sos, noise)
        mid = noise - lo - hi
        env = lambda rt: np.exp(-6.91 * t / rt)
        tail = 1.15 * lo * env(rt60 * 1.1) + mid * env(rt60) + 0.8 * hi * env(rt60 * damp)
        tail *= 1.0 - np.exp(-t / 0.025)                    # diffuse build-up
        er = np.zeros(n)
        for k in range(10):                                  # early reflections
            d = 0.004 + 0.045 * rng.random()
            er[int(d * SR)] += (0.7 - 0.05 * k) * rng.choice([-1, 1]) * np.exp(-d / 0.05)
        sig = 0.35 * er / max(1e-9, np.sqrt(np.sum(er ** 2))) + tail / np.sqrt(np.sum(tail ** 2))
        pd = int(predelay * SR)
        sig = np.concatenate([np.zeros(pd), sig])[:n]
        ir[:, ch] = sig / np.sqrt(np.sum(sig ** 2))
    return ir


def _db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def gated_rms(x, block=0.4, gate_db=20.0):
    mono = x.mean(axis=1) if x.ndim == 2 else x
    nb = int(block * SR)
    if len(mono) == 0:
        return 1e-10
    if len(mono) < nb:
        return np.sqrt(np.mean(mono ** 2) + 1e-20)
    m = len(mono) // nb
    p = np.mean(mono[:m * nb].reshape(m, nb) ** 2, axis=1)
    thr = p.max() * 10 ** (-gate_db / 10)
    sel = p[p >= thr]
    return np.sqrt(np.mean(sel) + 1e-20)


def limiter(x, ceil_lin, look=0.004):
    L = max(1, int(look * SR))
    a = np.max(np.abs(x), axis=1)
    g = np.minimum(1.0, ceil_lin / np.maximum(a, 1e-12))
    if g.min() >= 1.0:
        return x
    g1 = minimum_filter1d(g, size=2 * L + 1, mode='nearest')
    g2 = uniform_filter1d(g1, size=2 * L + 1, mode='nearest')
    return x * g2[:, None]


def write_wav(path, x, pcm16=False, seed=0):
    """Byte-deterministic RIFF writer (no timestamped PEAK chunk).
    float32 (WAVE_FORMAT_IEEE_FLOAT) by default, or 16-bit PCM with seeded TPDF dither."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    nch = x.shape[1]
    if pcm16:
        r = np.random.default_rng(seed)
        d = (r.random(x.shape) - r.random(x.shape)) / 32768.0
        data = np.clip(np.round((x + d) * 32767.0), -32768, 32767).astype('<i2').tobytes()
        fmt = struct.pack('<HHIIHH', 1, nch, SR, SR * nch * 2, nch * 2, 16)
        chunks = b'fmt ' + struct.pack('<I', len(fmt)) + fmt
    else:
        data = x.astype('<f4').tobytes()
        fmt = struct.pack('<HHIIHHH', 3, nch, SR, SR * nch * 4, nch * 4, 32, 0)
        chunks = (b'fmt ' + struct.pack('<I', len(fmt)) + fmt +
                  b'fact' + struct.pack('<II', 4, x.shape[0]))
    chunks += b'data' + struct.pack('<I', len(data)) + data
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 4 + len(chunks)) + b'WAVE' + chunks)


def _fade(n, kind='cos'):
    if n <= 0:
        return np.ones(0)
    u = np.linspace(0.0, 1.0, n)
    return 0.5 - 0.5 * np.cos(np.pi * u) if kind == 'cos' else u


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def _render_midi(mid, wav):
    cmd = [FLUIDSYNTH, '-ni', '-q', '-R', '0', '-C', '0', '-g', '0.45', '-r', str(SR),
           '-O', 'float', '-T', 'wav', '-o', 'synth.polyphony=512',
           '-o', 'synth.sample-rate=%d' % SR, '-F', wav, SF2, mid]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0 or not os.path.exists(wav):
        raise RuntimeError('fluidsynth failed: %s' % r.stderr.decode(errors='replace')[-800:])
    x, sr = sf.read(wav, dtype='float64', always_2d=True)
    assert sr == SR, sr
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def _render_stems(stems, n_total):
    tmp = tempfile.mkdtemp(prefix='music_lib_')
    try:
        jobs = []
        for i, st in enumerate(stems):
            mid = os.path.join(tmp, 's%d.mid' % i)
            wav = os.path.join(tmp, 's%d.wav' % i)
            st['score'].write_midi(mid, n_total / SR + 0.25)
            jobs.append((mid, wav))
        with ThreadPoolExecutor(max_workers=min(4, len(jobs))) as ex:
            outs = list(ex.map(lambda j: _render_midi(*j), jobs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    res = []
    for x in outs:
        y = np.zeros((n_total, 2))
        m = min(n_total, len(x))
        y[:m] = x[:m]
        res.append(y)
    return res


def _width(x, w):
    if w == 1.0:
        return x
    m = 0.5 * (x[:, 0] + x[:, 1])
    s = 0.5 * (x[:, 0] - x[:, 1]) * w
    return np.stack([m + s, m - s], axis=1)


# --------------------------------------------------------------------------
# small composition helpers
# --------------------------------------------------------------------------
def _beats_events(tm, b_start, b_end, beats_per_bar, first_bar_beat=None):
    beats = [round(tm.t(b), 4) for b in np.arange(b_start, b_end + 1e-6, 1.0)]
    fb = b_start if first_bar_beat is None else first_bar_beat
    downs = [round(tm.t(b), 4) for b in np.arange(fb, b_end + 1e-6, beats_per_bar)]
    return beats, downs


def _rng(name, seed):
    return np.random.default_rng(zlib.crc32(('brindle:%s:%d' % (name, seed)).encode()))


# ==========================================================================
# 1. CIVIC -- plodding municipal walking theme, C major, 88 bpm
# ==========================================================================
CIVIC_BARS = {
    1: ('C', 'C5:1.5 B4:.5 A4:1 G4:1', [48, 50, 52, 53]),
    2: ('G7', 'F4:1 A4:1 G4:2', [55, 53, 50, 47]),
    3: ('C', 'E4:1 G4:1 C5:1 E5:1', [48, 52, 55, 54]),
    4: ('G7', 'D5:2 r:1 G4:1', [43, 47, 50, 47]),
    5: ('C', 'C5:1.5 B4:.5 A4:1 G4:1', [48, 47, 45, 43]),
    6: ('F', 'A4:1 C5:1 F5:2', [41, 45, 48, 42]),
    7: ('G7', 'E5:1 D5:1 B4:1 D5:1', [43, 47, 50, 47]),
    8: ('C', 'C5:2 r:2', [48, 47, 45, 43]),
    9: ('F', 'A4:1 A4:1 C5:1 A4:1', [41, 45, 48, 47]),
    10: ('C', 'G4:1 G4:1 E4:2', [48, 45, 47, 49]),
    11: ('D7', 'F#4:1 A4:1 D5:1 C5:1', [50, 54, 57, 54]),
    12: ('G7', 'B4:2 r:1 G4:1', [55, 53, 50, 47]),
    13: ('C', 'C5:1.5 B4:.5 A4:1 G4:1', [48, 52, 55, 52]),
    14: ('F', 'A4:1 C5:1 F5:2', [53, 48, 45, 42]),
    15: ('G7', 'E5:1 D5:1 B4:1 D5:1', [43, 47, 50, 47]),
    16: ('C', 'C5:2 r:2', [48, 43, 45, 47]),
}
CIVIC_PHR = {'A': [1, 2, 3, 4], 'A2': [5, 6, 7, 8], 'B': [9, 10, 11, 12], 'A3': [13, 14, 15, 16]}
CIVIC_INTRO = {
    0: [],
    1: [('C', None, [48, 43, 45, 47])],
    2: [('C', None, [48, 52, 55, 52]), ('G7', None, [43, 47, 50, 47])],
    3: [('C', None, [48, 52, 55, 54]), ('G7', None, [55, 53, 50, 47]), ('C', None, [48, 43, 45, 47])],
}


def _key_shift(key):
    """Semitone shift from F major to `key` ('F' -> 0, 'C' -> -5, 'G' -> +2, 'Bb' -> +5),
    nearest direction. Raises ValueError for anything that is not a note name."""
    if not isinstance(key, str) or not re.match(r'^[A-Ga-g][#b]?$', key.strip()):
        raise ValueError('bad key %r (use a note name such as F, C, G, Bb)' % (key,))
    return ((_pc(key.strip()) - 5 + 6) % 12) - 6


def _civic_phrases(P):
    full = ['A', 'A2', 'B', 'A3']
    rem = {0: [], 1: ['A3'], 2: ['A', 'A2'], 3: ['A', 'B', 'A3']}
    k, r = divmod(P, 4)
    seq = full * k + rem[r]
    if k >= 1 and r == 1:
        seq[-1] = 'A2'
    return seq


CIVIC_INTRO_PEN = {0: 0.0, 1: 0.1, 2: 0.4, 3: 1.5}


def _civic_plan(n):
    """n content bars (n >= 3) -> (penalty, intro_bars, phrases, tag_bars)."""
    best = None
    for tag in (0, 2):
        for i in range(4):
            m = n - i - tag + 1
            if m >= 4 and m % 4 == 0:
                pen = CIVIC_INTRO_PEN[i] + (0.35 if tag else 0.0)
                if best is None or pen < best[0]:
                    best = (pen, i, m // 4, tag)
    return best


def _civic_bars(n, end):
    """Returns list of (chord, melody|None, bass, pass_idx) content bars."""
    if end == 'cut' or n >= 3:
        if end == 'cut':
            P, i, tag = n, 1, 0
        else:
            _, i, P, tag = _civic_plan(n)
        bars = [(c, m, list(b), 0) for c, m, b in CIVIC_INTRO[i]]
        for pi, ph in enumerate(_civic_phrases(P)):
            for bid in CIVIC_PHR[ph]:
                c, m, b = CIVIC_BARS[bid]
                bars.append((c, m, list(b), pi // 4))
        if end != 'cut':
            bars = bars[:-1]           # last cadential bar becomes the final chord
            for bid in ([14, 15] if tag else []):     # 'and again' tag ending
                c, m, b = CIVIC_BARS[bid]
                bars.append((c, m, list(b), 0))
        return bars
    ids = [15] if n == 1 else [14, 15]
    return [(CIVIC_BARS[k][0], CIVIC_BARS[k][1], list(CIVIC_BARS[k][2]), 0) for k in ids]


def _fix_walk(bars, final_root=None):
    for j in range(len(bars)):
        nxt = bars[j + 1][2][0] if j + 1 < len(bars) else final_root
        if nxt is None:
            continue
        b = bars[j][2]
        if abs(b[3] - nxt) > 2:
            b[3] = nxt - 1 if b[2] < nxt else nxt + 1


def cue_civic(D, rng, end='phrase', tempo=88.0, intro_bars=None, **_):
    T0 = float(tempo)
    if end == 'cut':
        bar_s = 4 * 60.0 / T0
        n = int(np.ceil(D / (4 * bar_s))) + 2
        bars = _civic_bars(n, 'cut')
        if intro_bars is not None:
            bars = [(c, m, list(b), 0) for c, m, b in CIVIC_INTRO[int(intro_bars)]] + bars[1:]
        k, tail = 1.0, 0.0
        nb = len(bars)
        pts = [(0.0, T0)]
    else:
        cands = []
        for n in range(1, 64):
            pts = _rit_pts(T0, 4 * n, 3, 0.16)
            T1 = TempoMap(pts, 4 * n).t(4 * n)
            cands.append((n, T1, _civic_plan(n)[0] if n >= 3 else 0.3))
            if T1 > D * 1.3:
                break
        n, k, tail, pre = _choose(D, cands, 2.4, 1.5, 4.2, 0.09)
        bars = _civic_bars(n, 'phrase')
        nb = len(bars)
        pts = _scale_pts(_rit_pts(T0, 4 * nb, 3, 0.16), k)
    _fix_walk(bars, 48 if end != 'cut' else None)
    tm, b_min = _trimmed_map(pts, 4 * nb + 4, 0.0 if end == 'cut' else pre, 0.0)
    sc = Score()
    _setup_piano(sc)
    re_ = Realiser(sc, tm, rng, PIANO, sigma=0.005, vsd=3.0,
                   offsets={'bass': 0.004, 'mel': 0.0, 'harm': 0.003},
                   art={'bass': 0.62, 'mel': 0.9, 'harm': 0.85}, spread=0.002, min_beat=b_min)
    items = []
    for j, (csym, mel, bass, pas) in enumerate(bars):
        b0 = 4 * j
        for q, p in enumerate(bass):
            v = 60 + (6 if q == 0 else 2 if q == 2 else 0)
            items.append({'b': b0 + q, 'd': 1.0, 'p': p, 'v': v, 'kind': 'bass'})
        if mel:
            pcs = chord(csym)['pcs']
            notes = parse_bar(mel, 4)
            for nt in notes:
                p = nt['p'][0]
                arch = 4.0 * np.sin(np.pi * ((j % 4) + nt['o'] / 4.0) / 4.0)
                v = 68 + arch + (3 if nt['o'] == 0 else 0)
                items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p, 'v': v, 'kind': 'mel'})
                if (nt['d'] >= 2 or pas % 2 == 1) and nt['o'] in (0, 1, 2, 3):
                    h = harmony_below(p, pcs)
                    if h is not None and h >= 55:
                        items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': h, 'v': v - 14, 'kind': 'harm'})
    re_.add(items)
    markers = {}
    if end != 'cut':
        bf = 4 * nb
        tf = tm.t(bf)
        for p, v in [(36, 60), (48, 58), (64, 50), (67, 52), (72, 62)]:
            sc.note(tf + rng.normal(0, 0.004), D - tf, p, v + rng.normal(0, 2), 0)
        sc.pedal([0], tf + 0.03, True)
        markers['final_chord'] = round(tf, 4)
    beats, downs = _beats_events(tm, b_min, 4 * nb if end != 'cut' else 4 * nb - 1, 4,
                                 first_bar_beat=4 * np.ceil(b_min / 4))
    beats = [b for b in beats if b < D]
    downs = [b for b in downs if b < D]
    stems = [dict(score=sc, send=1.0, gain=1.0, width=0.6,
                  eq=[('hp', 70), ('ls', 180, -1.5), ('pk', 1500, 1.5, 0.9), ('hs', 5200, -4.5), ('lp', 10500)])]
    return dict(stems=stems, ir=dict(rt60=0.75, predelay=0.010), wet=0.11, level=-20.0,
                fade_out=(0.03 if end == 'cut' else min(1.2, max(0.4, 0.45 * tail))),
                cut=(D if end == 'cut' else None), beats=beats, downbeats=downs,
                markers=markers, tempo=tm.bpm(0))


# ==========================================================================
# 2. RAG -- honky-tonk upright, F major, 2/4, LH stride in 8ths
# ==========================================================================
RAG_A = [
    (('F', 'F'), 'D5:.25 F5:.5 D5:.25 C5:.5 A4:.5'),
    (('F', 'F'), 'C5:.25 Eb5:.5 D5:.25 C5:1'),
    (('C7', 'C7'), 'Bb4:.25 C5:.5 Bb4:.25 G4:.5 E4:.5'),
    (('C7', 'C7'), 'G4:.5 E4:.5 C5:.5 C#5:.5'),
    (('F', 'F'), 'D5:.25 F5:.5 D5:.25 C5:.5 A4:.5'),
    (('F', 'F'), 'C5:.25 Eb5:.5 D5:.25 C5:.5 A4:.5'),
    (('G7', 'G7'), 'G5:.25 F5:.5 D5:.25 B4:.5 G4:.5'),
    (('C7', 'C7'), 'C5:.25 E5:.5 G5:.25 Bb5:1'),
    (('F', 'F'), 'A5:.25 F5:.5 C5:.25 A5:.5 F5:.5'),
    (('F7', 'F7'), 'Eb5:.25 F5:.5 Eb5:.25 C5:.5 A4:.5'),
    (('Bb', 'Bb'), 'D5:.25 F5:.5 D5:.25 Bb4:.5 F4:.5'),
    (('Bdim7', 'Bdim7'), 'Ab4:.25 B4:.5 D5:.25 F5:.5 Ab5:.5'),
    (('F/C', 'F/C'), 'A5:.25 G5:.5 F5:.25 C5:.5 A4:.5'),
    (('D7', 'D7'), 'F#5:.25 A5:.5 F#5:.25 D5:.5 C5:.5'),
    (('G7', 'C7'), 'B4:.25 D5:.5 G5:.25 Bb4:.25 C5:.5 E5:.25'),
    (('F', 'F'), 'F5:.5 A4:.5 C5:.5 C#5:.5'),
]
RAG_B = [
    (('Bb', 'Bb'), 'F5:.25 F5:.5 F5:.25 D5:.5 Bb4:.5'),
    (('Bdim7', 'Bdim7'), 'F5:.25 F5:.5 F5:.25 D5:.5 B4:.5'),
    (('F/C', 'F/C'), 'F5:.25 A5:.5 F5:.25 C5:.5 A4:.5'),
    (('D7', 'D7'), 'F#5:.25 A5:.5 C6:.25 A5:.5 F#5:.5'),
    (('G7', 'G7'), 'D5:.25 E5:.5 F5:.25 F#5:.5 G5:.5'),
    (('C7', 'C7'), 'G5:.25 E5:.5 C5:.25 Bb4:.5 G4:.5'),
    (('F', 'D7'), 'A4:.25 C5:.5 F5:.25 A5:.5 F#5:.5'),
    (('G7', 'C7'), 'D5:.5 B4:.5 C5:.5 C#5:.5'),
]
RAG_PHR = {'A1': RAG_A[0:4], 'A2': RAG_A[4:8], 'A3': RAG_A[8:12], 'A4': RAG_A[12:16],
           'B1': RAG_B[0:4], 'B2': RAG_B[4:8]}
RAG_CYCLE = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B1', 'B2']
RAG_TAG = {0: [], 1: [14], 2: [13, 14], 3: [12, 13, 14]}   # indices into RAG_A (0-based)


def _rag_seq_bars(n, ending=True):
    """Content bars [(chords, melody_notes, phrase_start)] for n bars.
    With ending=True the last bar is followed by the F 'button'."""
    def pb(b, start=False):
        return (b[0], parse_bar(b[1], 2), start)

    def phrase(ph):
        return [pb(b, i == 0) for i, b in enumerate(RAG_PHR[ph])]
    if not ending:
        out, i = [], 0
        while len(out) < n:
            out += phrase(RAG_CYCLE[i % len(RAG_CYCLE)])
            i += 1
        return out[:n]
    if n <= 2:
        return [pb(b) for b in RAG_A[15 - n:15]]
    P, e = (n + 1) // 4, (n + 1) % 4
    seq = [RAG_CYCLE[i % len(RAG_CYCLE)] for i in range(P - 1)] + ['A4']
    out = []
    for ph in seq:
        out += phrase(ph)
    out = out[:-1]                         # bar 16 -> button
    out += [pb(RAG_A[i], j == 0) for j, i in enumerate(RAG_TAG[e])]
    return out[:n]


def _rag_fix_pickups(bars):
    """At phrase joins, replace the last beat of the previous bar with a
    chromatic 2-note pickup when the new phrase's first note is not
    already approached by step."""
    for j in range(len(bars) - 1):
        cur, nxt = bars[j][1], bars[j + 1][1]
        if not bars[j + 1][2]:
            continue
        if not cur or not nxt or nxt[0]['o'] > 0:
            continue
        target = max(nxt[0]['p'])
        last = max(cur[-1]['p'])
        if abs(last - target) <= 2:
            continue
        if not any(n['o'] >= 1.0 - 1e-6 for n in cur):
            continue
        keep = [n for n in cur if n['o'] < 1.0 - 1e-6]
        for n in keep:
            n['d'] = min(n['d'], 1.0 - n['o'])
        keep += [{'o': 1.0, 'd': 0.5, 'p': [target - 2], 'acc': False, 'grace': None},
                 {'o': 1.5, 'd': 0.5, 'p': [target - 1], 'acc': False, 'grace': None}]
        bars[j] = (bars[j][0], keep, bars[j][2])
    return bars


def _stride_items(bars, b0, vel=1.0, rh_oct=True, prev_voicing=None, energy=1.0):
    items = []
    pv = prev_voicing
    for j, bar in enumerate(bars):
        chs, mel = bar[0], bar[1]
        bb = b0 + 2 * j
        for k in (0, 1):
            sym = chs[k]
            c = chord(sym)
            new = (k == 0) or chs[k] != chs[k - 1]
            if new:
                bpc = c['bass']
            else:
                bpc = c['root'] if c['bass'] != c['root'] else c['pcs'][2]
            bp = 29 + ((bpc - 29) % 12)
            vb = (86 if k == 0 else 78) * vel * energy
            items.append({'b': bb + k, 'd': 0.45, 'p': bp, 'v': vb, 'kind': 'bass'})
            items.append({'b': bb + k, 'd': 0.45, 'p': bp + 12, 'v': vb - 6, 'kind': 'bass'})
            vc = voice(sym, 52, 67, pv, n=3)
            pv = vc
            for p in vc:
                items.append({'b': bb + k + 0.5, 'd': 0.32, 'p': p, 'v': 64 * vel * energy, 'kind': 'chord'})
        for nt in mel:
            for p in nt['p']:
                sync = abs((nt['o'] % 0.5) - 0.25) < 1e-6 and nt['d'] >= 0.5
                v = (84 + (10 if sync else 0) + (8 if nt['acc'] else 0) + (4 if nt['o'] in (0.0, 1.0) else 0)) * vel
                items.append({'b': bb + nt['o'], 'd': nt['d'], 'p': p, 'v': v, 'kind': 'mel',
                              'grace': nt['grace']})
                if rh_oct and nt['d'] >= 0.5 and len(nt['p']) == 1:
                    items.append({'b': bb + nt['o'], 'd': nt['d'], 'p': p - 12, 'v': v - 18, 'kind': 'harm'})
    return items, pv


HONKY_EQ = [('hp', 45), ('ls', 170, -2.5), ('pk', 1100, 2.0, 0.8), ('hs', 3200, 3.5)]


def _rag_body(D_body, rng, tempo, t0, stop_rel=None, pickup=True, energy=1.0, sc=None):
    """Rag from time t0 (absolute) lasting D_body seconds.
    Returns (score, items-free info dict)."""
    T0 = float(tempo)
    pk = 1.0 if pickup else 0.0
    info = {}
    if stop_rel is not None:
        nbars = int(np.ceil((stop_rel / (60.0 / T0) - pk) / 2.0)) + 2
        bars = _rag_fix_pickups(_rag_seq_bars(max(nbars, 1), ending=False))
        k, tail = 1.0, None
        pts = [(0.0, T0)]
    else:
        cands = []
        for n in range(0, 200):
            if n == 0:
                cands.append((0, pk * 60.0 / T0))
                continue
            bt = pk + 2 * n
            pts = _rit_pts(T0, bt, 1.5, 0.08)
            T1 = TempoMap(pts, bt).t(bt)
            cands.append((n, T1))
            if T1 > D_body * 1.3:
                break
        n, k, tail, pre = _choose(D_body, cands, 1.5, 0.9, 2.8, 0.07)
        bars = _rag_fix_pickups(_rag_seq_bars(n, ending=True)) if n > 0 else []
        pts = _scale_pts(_rit_pts(T0, pk + 2 * len(bars), 1.5, 0.08), k)
    nb = len(bars)
    if stop_rel is None and pre > 0 and pickup:
        tm, b_min = _trimmed_map(pts, pk + 2 * nb + 4, pre, t0)
    else:
        tm, b_min = TempoMap(pts, pk + 2 * nb + 4, t0=t0), 0.0
    if sc is None:
        sc = Score()
        _setup_honky(sc)
    re_ = Realiser(sc, tm, rng, HONKY, sigma=0.006, vsd=4.0,
                   offsets={'mel': -0.004, 'harm': -0.002, 'bass': 0.0, 'chord': 0.006},
                   art={'mel': 0.86, 'harm': 0.8, 'bass': 0.5, 'chord': 0.55}, spread=0.003,
                   min_beat=b_min)
    items = []
    if pickup:
        first = max(bars[0][1][0]['p']) if bars and bars[0][1] else pitch('F5')
        items += [{'b': 0.0, 'd': 0.5, 'p': first - 2, 'v': 80, 'kind': 'mel'},
                  {'b': 0.5, 'd': 0.5, 'p': first - 1, 'v': 86, 'kind': 'mel'}]
    body, _ = _stride_items(bars, pk, energy=energy)
    items += body
    if stop_rel is not None:
        # stop dead: last struck 8th-grid chord before the stop hangs (C7b9)
        stop_abs = t0 + stop_rel
        g = np.floor((stop_rel - 0.11) / (60.0 / T0 / 2.0)) * 0.5
        g = max(0.0, g)
        while tm.t(g) > stop_abs - 0.09 and g > 0:
            g -= 0.5
        items = [it for it in items if it['b'] < g - 1e-6]
        hang = [24, 36, 58, 61, 64, 67]
        for p in hang:
            items.append({'b': g, 'd': 6.0, 'p': p, 'v': 104 if p > 40 else 96, 'kind': 'chord'})
        re_.add(items)
        sc.pedal([0, 1, 2], tm.t(g) + 0.02, True)
        info['hang_chord'] = round(tm.t(g), 4)
        info['stop'] = round(stop_abs, 4)
        bend = pk + 2 * nb
        beats, downs = _beats_events(tm, 0, bend, 2, first_bar_beat=pk)
        info['beats'] = [b for b in beats if b < stop_abs]
        info['downbeats'] = [b for b in downs if b < stop_abs]
    else:
        bf = pk + 2 * nb
        for p, v in [(29, 92), (41, 88), (65, 86), (69, 88), (72, 90), (77, 100)]:
            items.append({'b': bf, 'd': 1.0, 'p': p, 'v': v, 'kind': 'chord', 'dur_s': 1.3})
        re_.add(items)
        tf = tm.t(bf)
        sc.pedal([0, 1, 2], tf + 0.02, True)
        sc.pedal([0, 1, 2], tf + min(1.1, max(0.5, (tail or 1.0) * 0.6)), False)
        info['button'] = round(tf, 4)
        beats, downs = _beats_events(tm, b_min, bf, 2, first_bar_beat=pk + 2 * np.ceil(max(0, b_min - pk) / 2))
        info['beats'], info['downbeats'] = beats, downs
        info['tail'] = tail
    info['tempo'] = tm.bpm(pk)
    info['tm'] = tm
    return sc, info


def _check_time(name, v, D, lo=0.0):
    """Validate a time parameter (s) and clamp it into [lo, D]."""
    v = float(v)
    if not np.isfinite(v) or v < 0:
        raise ValueError('%s must be a time >= 0 s, got %r' % (name, v))
    return float(np.clip(v, lo, D))


def cue_rag(D, rng, stop_at=None, tempo=112.0, **_):
    t0 = 0.01                                   # the rag's time origin (first pickup note)
    if stop_at is not None:
        stop_at = _check_time('stop_at', stop_at, D, lo=min(0.15, D))
    # stop_rel is measured from t0, so markers['stop'] == stop_at == the audio cut
    stop_rel = None if stop_at is None else stop_at - t0
    sc, info = _rag_body(D, rng, tempo, t0, stop_rel=stop_rel)
    markers = {k: info[k] for k in ('hang_chord', 'stop', 'button') if k in info}
    tail = info.get('tail') or 1.0
    return dict(stems=[dict(score=sc, send=1.0, gain=1.0, width=0.85, eq=HONKY_EQ)],
                ir=dict(rt60=0.8, predelay=0.008), wet=0.12, level=-18.0,
                fade_out=min(0.8, max(0.3, 0.4 * tail)), cut=stop_at,
                beats=info['beats'], downbeats=info['downbeats'], markers=markers,
                tempo=info['tempo'])


# ==========================================================================
# 3. TIPTOE -- pizzicato sneak in D minor, ends with a ride-bell tap
# ==========================================================================
TIPTOE = [
    ('Dm', 'D4:.5 r:.5 F4:.5 E4:.5 D4:.5 r:.5 A3:.5 r:.5'),
    ('Dm', 'D4:.5 r:.5 F4:.5 G4:.5 G#4:.5 A4:.5 r:1'),
    ('A7', 'A4:.5 r:1 G4:.5 r:.5 F4:.5 r:.5 E4:.5'),
    ('Dm', 'D4:.5 r:.5 C#4:.5 r:.5 D4:.5 r:1.5'),
    ('Gm', 'G4:.5 r:.5 Bb4:.5 A4:.5 G4:.5 r:.5 D4:.5 r:.5'),
    ('Dm', 'F4:.5 r:.5 A4:.5 Bb4:.5 B4:.5 C5:.5 r:1'),
    ('A7', 'C#5:.5 r:.5 E5:.5 r:.5 G5:.5 r:.5 E5:.5 C#5:.5'),
    ('Dm', 'D5:.5 r:.5 A4:.5 r:.5 D4:.5 r:1.5'),
]
TIPTOE_BASS = {'Dm': (38, 33), 'A7': (33, 40), 'Gm': (43, 38)}
TIPTOE_DYAD = {'Dm': (53, 57), 'A7': (49, 55), 'Gm': (55, 58)}


def cue_tiptoe(D, rng, tempo=100.0, **_):
    T0 = float(tempo)
    cands = []
    for n in range(1, 80):
        bt = 4 * n
        T1 = TempoMap([(0.0, T0)], bt).t(bt)
        cands.append((n, T1))
        if T1 > D * 1.3:
            break
    n, k, tail, pre = _choose(D, cands, 1.9, 1.2, 3.4, 0.08)
    if n < 4:
        content = [(TIPTOE[j], 0) for j in range(8 - n, 8)]
    else:
        P, i = n // 4, n % 4
        intro = {0: [], 1: ['Dm'], 2: ['Dm', 'A7'], 3: ['Dm', 'Dm', 'A7']}[i]
        content = [((c, None), 0) for c in intro]
        for ph in range(P):
            half = TIPTOE[0:4] if ph % 2 == 0 else TIPTOE[4:8]
            content += [(b, ph // 2) for b in half]
    nb = len(content)
    tm, b_min = _trimmed_map([(0.0, T0 * k)], 4 * nb + 4, pre, 0.02)
    sc = Score()
    sc.setup(0, 45, volume=110, pan=72)     # upper line
    sc.setup(1, 45, volume=108, pan=54)     # bass pizz
    sc.setup(9, 0, volume=114, pan=70)
    re_ = Realiser(sc, tm, rng, [(0, 1.0, 0.0)], sigma=0.007, vsd=4.0,
                   art={'mel': 0.55}, offsets={'mel': 0.0}, min_beat=b_min)
    reb = Realiser(sc, tm, rng, [(1, 1.0, 0.0)], sigma=0.006, vsd=3.0,
                   art={'bass': 0.6, 'chord': 0.5}, offsets={'chord': 0.008}, spread=0.006,
                   min_beat=b_min)
    mi, bi = [], []
    for j, ((csym, mel), pas) in enumerate(content):
        b0 = 4 * j
        hb, lb = TIPTOE_BASS[csym]
        bi.append({'b': b0, 'd': 0.5, 'p': hb, 'v': 74, 'kind': 'bass'})
        bi.append({'b': b0 + 2, 'd': 0.5, 'p': lb, 'v': 66, 'kind': 'bass'})
        for q in (1, 3):
            for p in TIPTOE_DYAD[csym]:
                bi.append({'b': b0 + q, 'd': 0.4, 'p': p, 'v': 44, 'kind': 'chord'})
        if mel:
            for nt in parse_bar(mel, 4):
                p = nt['p'][0]
                off = nt['o'] % 1.0 > 0.25
                v = 70 + (6 if off else 0) + 3 * np.sin(np.pi * (j % 4 + nt['o'] / 4) / 4)
                mi.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p, 'v': v, 'kind': 'mel'})
                if pas % 2 == 1:
                    mi.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p + 12, 'v': v - 18, 'kind': 'mel'})
    re_.add(mi)
    reb.add(bi)
    tb = tm.t(4 * nb)
    sc.note(tb, 1.5, 53, 118, 9)            # ride bell -- single bright tap
    beats, downs = _beats_events(tm, b_min, 4 * nb, 4, first_bar_beat=4 * np.ceil(b_min / 4))
    stems = [dict(score=sc, send=1.0, gain=1.0, width=1.0, eq=[('hp', 38), ('hs', 7000, 1.5)])]
    return dict(stems=stems, ir=dict(rt60=1.25, predelay=0.014), wet=0.17, level=-22.0,
                fade_out=min(1.4, max(0.5, 0.5 * tail)), cut=None, beats=beats, downbeats=downs,
                markers={'bell': round(tb, 4)}, tempo=T0 * k)


# ==========================================================================
# 4. VAMP -- lazy two-chord honky-tonk vamp, F6 <-> Bb9, swung, 84 bpm
# ==========================================================================
VAMP_LH = {'F6': (41, 36, [57, 60, 62]), 'Bb9': (34, 41, [56, 60, 62]), 'C9': (36, 43, [58, 62, 64])}
VAMP_LICKS = {
    'F6': ['r:1 G#4~A4:.5 C5:.5 D5:.5 C5:.5 r:1',
           'F5:1.5 D5:.5 C5:.5 A4:.5 r:1',
           'r:2 A4+D5:.5 r:.5 A4+C5:1',
           'C5:.5 D5:.5 F5:.5 G#5~A5:1.5 r:1',
           'r:1.5 D5+F5:.5 r:1 C5+F5:1'],
    'Bb9': ['r:1 F5:.5 Ab5:.5 F5:.5 D5:1.5',
            'D5+Ab5:1 r:.5 C5+F5:.5 r:2',
            'r:2 C5:.5 D5:.5 F5:1',
            'Ab4:.5 C5:.5 D5:.5 F5:.5 Ab5:1 r:1',
            'r:4'],
    'C9': ['Bb4:1 C5:.5 D5:.5 E5:2', 'E5:.5 G5:.5 Bb5:.5 G5:.5 E5:1 r:1'],
}


def cue_vamp(D, rng, tempo=84.0, **_):
    T0 = float(tempo)
    cands = []
    for n in range(1, 80):
        bt = 4 * n
        T1 = TempoMap(_rit_pts(T0, bt, 6, 0.18), bt).t(bt)
        cands.append((n, T1))
        if T1 > D * 1.3:
            break
    n, k, tail, pre = _choose(D, cands, 2.8, 1.8, 4.8, 0.08)
    syms = ['F6' if j % 2 == 0 else 'Bb9' for j in range(n)]
    if n % 2 == 1:
        syms[-1] = 'C9' if n > 1 else 'Bb9'
    pts = _scale_pts(_rit_pts(T0, 4 * n, 6, 0.18), k)
    tm, b_min = _trimmed_map(pts, 4 * n + 4, pre, 0.02)
    sc = Score()
    _setup_honky(sc)
    tf = tm.t(4 * n)
    vel_fn = lambda t: 1.0 - 0.16 * min(1.0, t / max(tf, 1e-3))     # winding down
    lh = Realiser(sc, tm, rng, HONKY, sigma=0.010, vsd=4.0,
                  offsets={'bass': 0.004, 'chord': 0.016},
                  art={'bass': 0.75, 'chord': 0.6}, swing=0.63, spread=0.006, vel_fn=vel_fn,
                  min_beat=b_min)
    rh = Realiser(sc, tm, rng, HONKY, sigma=0.014, vsd=5.0,
                  offsets={'mel': 0.020}, art={'mel': 0.8}, swing=0.63, spread=0.008, vel_fn=vel_fn,
                  min_beat=b_min)
    li, ri = [], []
    last = None
    for j, s in enumerate(syms):
        b0 = 4 * j
        r1, r5, ch = VAMP_LH[s]
        li += [{'b': b0, 'd': 1.0, 'p': r1, 'v': 64, 'kind': 'bass'},
               {'b': b0 + 2, 'd': 1.0, 'p': r5, 'v': 58, 'kind': 'bass'}]
        if j == 0:
            li.append({'b': b0, 'd': 1.0, 'p': r1 - 12, 'v': 48, 'kind': 'bass'})
        for q in (1, 3):
            for p in ch:
                li.append({'b': b0 + q, 'd': 0.8, 'p': p, 'v': 46, 'kind': 'chord'})
        if j % 2 == 0 or rng.random() < 0.5 or s == 'C9':
            pool = VAMP_LICKS[s]
            idx = int(rng.integers(len(pool)))
            if pool[idx] == last:
                idx = (idx + 1) % len(pool)
            last = pool[idx]
            for nt in parse_bar(pool[idx], 4):
                for p in nt['p']:
                    ri.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p,
                               'v': 60 + (4 if nt['o'] in (0, 2) else 0), 'kind': 'mel',
                               'grace': nt['grace'] if p == max(nt['p']) else None})
    lh.add(li)
    rh.add(ri)
    # final: lazy rolled F6/9
    for i, (p, v) in enumerate([(29, 48), (41, 54), (57, 44), (60, 44), (62, 44), (67, 46), (69, 50), (74, 52)]):
        sc_t = tf + 0.022 * i + rng.normal(0, 0.003)
        for ch, vs, dt in HONKY:
            sc.note(sc_t + dt, D - sc_t, p, v * vs * 0.95, ch)
    sc.pedal([0, 1, 2], tf + 0.05, True)
    beats, downs = _beats_events(tm, b_min, 4 * n, 4, first_bar_beat=4 * np.ceil(b_min / 4))
    return dict(stems=[dict(score=sc, send=1.0, gain=1.0, width=0.85, eq=HONKY_EQ[:3] + [('hs', 3200, 2.0)])],
                ir=dict(rt60=0.95, predelay=0.010), wet=0.14, level=-21.0,
                fade_out=min(1.8, max(0.6, 0.5 * tail)), cut=None, beats=beats, downbeats=downs,
                markers={'final_chord': round(tf, 4)}, tempo=T0 * k)


# ==========================================================================
# 5. CELLO_NOTE -- single pp low cello note that swells in and fades
# ==========================================================================
def cue_cello_note(D, rng, pitch_='C2', **kw):
    p = pitch(kw.get('pitch', pitch_))
    sc = Score()
    sc.setup(0, 42, volume=100, pan=60, expression=0)
    t_on = 0.02
    sc.note(t_on, D - 0.05, p, 46, 0)
    t_in = min(0.38 * D, 7.0)
    t_out = min(0.45 * D, 9.0)
    ts = np.arange(0.0, D, 0.02)
    def ss(u):
        u = np.clip(u, 0, 1)
        return u * u * u * (u * (u * 6 - 15) + 10)
    env = np.minimum(ss(ts / t_in), ss((D - 0.12 - ts) / t_out))
    env = env * (1 + 0.04 * np.sin(2 * np.pi * ts / 4.7))     # slow breathing
    last = -1
    for t, e in zip(ts, env):
        v = int(round(np.clip(e, 0, 1) * 96))
        if v != last:
            sc.cc(t, 0, 11, v)
            last = v
    stems = [dict(score=sc, send=1.0, gain=1.0, width=0.8, eq=[('hp', 28), ('hs', 2500, -3)])]
    return dict(stems=stems, ir=dict(rt60=2.1, predelay=0.020), wet=0.26, level=-33.0,
                fade_out=0.05, cut=None, beats=[], downbeats=[],
                markers={'peak': round(float(ts[np.argmax(env)]), 3)}, tempo=None)


# ==========================================================================
# 6. NAME_PIANO -- the name motif, plain and tender, F major
# ==========================================================================
NP_BARS = {   # chords [(beat, sym)], RH, LH
    'M1': ([(0, 'F')], 'A4:1 G4:1 F4:1 C5:1', 'F2+C3:4'),
    'M2': ([(0, 'Bbmaj7')], 'r:1 D5:1 C5:2', 'Bb1+Bb2:1 F3:1 A3:1 D4:1'),
    'M3': ([(0, 'F'), (1, 'C/E'), (2, 'Dm'), (3, 'Bbmaj7')], 'A4:1 G4:1 F4:1 C5:1',
           'F2+C3:1 E2+C3:1 D2+A2:1 Bb1+F2+A2:1'),
    'M4': ([(0, 'Gm7'), (2, 'C7')], 'D5:1.5 C5:.5 Bb4:2', 'G2+D3+F3:2 C2+Bb2+E3:2'),
    'C1a': ([(0, 'Gm7')], 'Bb4:1 A4:1 G4:1 D5:1', 'G2:1 D3:1 F3:1 Bb3:1'),
    'C1b': ([(0, 'C7sus4'), (2, 'C7')], 'C5:2 Bb4:1 G4:1', 'C2+Bb2:2 E2+Bb2:2'),
    'C2a': ([(0, 'F/A'), (2, 'Dm7')], 'A4:1.5 G4:.5 F4:1 A4:1', 'A1+F2+C3:2 D2+A2+C3:2'),
    'C2b': ([(0, 'Gm7'), (2, 'C7')], 'G4:3 E4:1', 'G2+D3+F3:2 C2+Bb2+E3:2'),
    'Mm1': ([(0, 'Dm7')], 'C5:1 D5:1 F5:2', 'D2:1 A2:1 F3:2'),
    'Mm2': ([(0, 'C7'), (2, 'F')], 'E5:1 D5:1 C5:2', 'C2+Bb2:2 F2+A2:2'),
    'Mm3': ([(0, 'Bb'), (2, 'F/A')], 'D5:1 C5:1 Bb4:1 A4:1', 'Bb1+F2:2 A1+F2:2'),
    'Mm4': ([(0, 'Gm7'), (2, 'C7')], 'G4:2 A4:1 Bb4:1', 'G2+D3:2 C2+Bb2:2'),
}
NP_FINAL = ([(0, 'F')], [41, 48, 57, 60, 65])


def _np_structure(k):
    T = {1: ['M1'], 2: ['M1', 'M2'], 3: ['M1', 'C1a', 'C1b'], 4: ['M1', 'M2', 'C1a', 'C1b'],
         5: ['M1', 'C1a', 'C1b', 'C2a', 'C2b'], 6: ['M1', 'M2', 'C1a', 'C1b', 'C2a', 'C2b'],
         7: ['M1', 'M3', 'M4', 'C1a', 'C1b', 'C2a', 'C2b'],
         8: ['M1', 'M2', 'M3', 'M4', 'C1a', 'C1b', 'C2a', 'C2b']}
    if k in T:
        return T[k]
    mid_cycle = ['Mm1', 'Mm2', 'Mm3', 'Mm4', 'M3', 'M4']
    mid = [mid_cycle[i % len(mid_cycle)] for i in range(k - 8)]
    return ['M1', 'M2', 'M3', 'M4'] + mid + ['C1a', 'C1b', 'C2a', 'C2b']


def _breath_pts(T, nbars, rit_last=0.22):
    """Gentle rubato: a small breath at the end of each 2-bar group, ritard at the end."""
    pts = [(0.0, T)]
    for g in range(2, nbars, 2):
        b = 4 * g
        pts += [(b - 1.0, T), (b - 0.05, T * 0.9), (b + 0.6, T)]
    end = 4 * nbars
    pts += [(end - 2.5, T), (end, T * (1 - rit_last))]
    return sorted(pts)


def _pad_items(chords_abs, lo, hi, v, start_b=None):
    """chords_abs: [(beat, sym, until_beat)] -> sustained low pad items:
    the chord's bass note in [lo, lo+11] plus two guide tones (3rd + 7th/5th)
    voice-led inside [lo+10, hi]."""
    out, pv = [], None
    for b, sym, until in chords_abs:
        if start_b is not None and until <= start_b:
            continue
        c = chord(sym)
        bass = lo + ((c['bass'] - lo) % 12)
        up = voice(sym, max(bass + 3, lo + 10), hi, pv, n=2, max_span=10)
        pv = up
        bs = b if start_b is None else max(b, start_b)
        for p in [bass] + up:
            out.append({'b': bs, 'd': until - bs + 0.08, 'p': p, 'v': v, 'kind': 'pad'})
    return out


def _pedal_from_changes(sc, tm, change_beats, chans, end_t=None):
    first = True
    for b in change_beats:
        t = tm.t(b)
        if not first:
            sc.pedal(chans, t + 0.008, False)
        sc.pedal(chans, t + 0.085, True)
        first = False


def cue_name_piano(D, rng, with_strings=False, strings_at=None, tempo=60.0, **_):
    T0 = float(tempo)
    cands = []
    for kb in range(1, 40):
        T1 = TempoMap(_breath_pts(T0, kb), 4 * kb).t(4 * kb)
        cands.append((kb, T1))
        if T1 > D * 1.3:
            break
    kb, k, tail, pre = _choose(D, cands, 4.0, 2.4, 7.5, 0.12)
    if pre > 0:      # short request: keep the whole motif (quicker, shorter ring) before trimming
        kb, k, tail, pre = _choose(D, cands, 2.4, 1.6, 7.5, 0.30)
    struct_ = _np_structure(kb)
    tm, b_min = _trimmed_map(_scale_pts(_breath_pts(T0, kb), k), 4 * kb + 4, pre, 0.03)
    sc = Score()
    _setup_piano(sc)
    re_ = Realiser(sc, tm, rng, PIANO, sigma=0.008, vsd=2.5,
                   offsets={'mel': 0.012, 'bass': 0.0, 'harm': 0.004},
                   art={'mel': 1.0, 'bass': 1.0}, spread=0.012, min_beat=b_min)
    items, changes, chords_abs = [], [], []
    motif_times = []
    for j, bid in enumerate(struct_):
        chs, rh, lh = NP_BARS[bid]
        b0 = 4 * j
        for q, (cb, sym) in enumerate(chs):
            changes.append(b0 + cb)
            until = b0 + (chs[q + 1][0] if q + 1 < len(chs) else 4)
            chords_abs.append((b0 + cb, sym, until))
        if bid in ('M1', 'M3') and b0 >= b_min:
            motif_times.append(round(tm.t(b0), 4))
        for i, nt in enumerate(parse_bar(rh, 4)):
            shape = [47, 44, 42, 49][i] if bid in ('M1', 'M3') else 44
            for p in nt['p']:
                items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p, 'v': shape, 'kind': 'mel'})
        for nt in parse_bar(lh, 4):
            for p in nt['p']:
                items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p,
                              'v': 33 if nt['o'] == 0 else 30, 'kind': 'bass'})
    bf = 4 * kb
    tf = tm.t(bf)
    for i, p in enumerate(NP_FINAL[1]):
        items.append({'b': bf, 'd': 4, 'p': p, 'v': 36 if p < 60 else 42, 'kind': 'harm',
                      'dur_s': D - tf - 0.02})
    changes.append(bf)
    chords_abs.append((bf, 'F', bf + 64))
    re_.add(items)
    _pedal_from_changes(sc, tm, changes, [0])
    stems = [dict(score=sc, send=1.0, gain=1.0, width=0.9, eq=[('hp', 30), ('hs', 6000, -2.5)])]
    markers = {'motif': motif_times, 'final_chord': round(tf, 4)}
    if with_strings:
        s_at = float(strings_at) if strings_at is not None else 0.5 * tf
        s_at = float(np.clip(s_at, 0.0, max(0.0, D - 1.0)))
        # beat at s_at
        bgrid = np.linspace(0, bf + 64, int((bf + 64) * 50) + 1)
        sb = max(b_min, float(np.interp(s_at, tm.t(bgrid), bgrid)))
        ss = Score()
        ss.setup(0, 49, volume=100, pan=58, expression=0)
        ss.setup(1, 48, volume=80, pan=74, expression=0)
        pad = _pad_items(chords_abs, 38, 57, 44, start_b=sb)
        rs = Realiser(ss, tm, rng, [(0, 1.0, 0.0), (1, 0.8, 0.02)], sigma=0.01, vsd=2.0,
                      art={'pad': 1.0}, spread=0.02)
        for it in pad:
            it['dur_s'] = max(0.1, tm.t(it['b'] + it['d']) - tm.t(it['b']))
            if it['b'] >= bf:
                it['dur_s'] = D - tm.t(it['b']) - 0.02
        rs.add(pad)
        t_bloom = max(2.5, min(6.0, 0.4 * (D - s_at)))
        for t in np.arange(0, D, 0.03):
            u = np.clip((t - s_at) / t_bloom, 0, 1)
            e = u * u * (3 - 2 * u)
            fo = np.clip((D - 0.1 - t) / max(1.5, 0.6 * tail), 0, 1)
            val = 84 * e * (fo * fo * (3 - 2 * fo))
            for ch in (0, 1):
                ss.cc(t, ch, 11, val)
        stems.append(dict(score=ss, send=1.6, gain=0.45, width=1.0,
                          eq=[('hp', 45), ('ls', 120, -2), ('hs', 3500, -6), ('lp', 7000)]))
        markers['strings_at'] = round(s_at, 4)
    beats, downs = _beats_events(tm, b_min, bf, 4, first_bar_beat=4 * np.ceil(b_min / 4))
    return dict(stems=stems, ir=dict(rt60=1.9, predelay=0.018), wet=0.22, level=-25.0,
                fade_out=min(3.0, max(1.0, 0.6 * tail)), cut=None, beats=beats, downbeats=downs,
                markers=markers, tempo=T0 * k)


# ==========================================================================
# 7. RAG_MOTIF -- the name motif on the honky-tonk, building into the rag
# ==========================================================================
RM_BLOCKS = {
    'B0': [(('F', 'F'), 'A4:.25 G4:.5 F4:.25 C5:.5> r:.5', None)],
    'B1': [(('F', 'F'), 'G#4~A4:1 G4:1', 'F2+C3:1 r:1'),
           (('F', 'F'), 'F4:1 C5:.5> r:.5', 'r:1.5 C2:.5>')],
    'B2': [(('F', 'F'), 'A5:.25 G5:.5 F5:.25 C6:.5> r:.5', 'r:2'),
           (('C7', 'F'), 'r:2', 'C2:.5 r:.5 F1+F2:.5> r:.5')],
    'B3': [(('F', 'F'), 'A4:.25 G4:.5 F4:.25 C5:.5> r:.5', None),
           (('C7', 'C7'), 'Bb4:.25 A4:.5 G4:.25 C5:.5> r:.5', None),
           (('F', 'F'), 'A4:.25 G4:.5 F4:.25 C5:.5 F5:.5>', None),
           (('C7', 'C7'), 'E5:.25 C5:.5 Bb4:.25 G4:.5 E4:.5', None)],
    'B4': [(('Bb', 'Bb'), 'D5:.25 C5:.5 Bb4:.25 F5:.5> r:.5', None),
           (('Bdim7', 'Bdim7'), 'D5:.25 C5:.5 B4:.25 F5:.5> Ab5:.5', None),
           (('F/C', 'F/C'), 'A5:.25 G5:.5 F5:.25 C6:.5> r:.5', None),
           (('C7', 'C7'), 'G5:.25 E5:.5 C5:.25 Bb4:.5 G4:.5', None)],
}
RM_PLANS = [['B0'], ['B1'], ['B1', 'B2'], ['B1', 'B3'], ['B1', 'B2', 'B3'], ['B1', 'B3', 'B4'],
            ['B1', 'B2', 'B3', 'B4'], ['B1', 'B2', 'B3', 'B3+', 'B4'],
            ['B1', 'B2', 'B1', 'B2', 'B3', 'B3+', 'B4'],
            ['B1', 'B2', 'B1', 'B2', 'B3', 'B3+', 'B4', 'B3+', 'B4']]


def _rm_pts(plan_bars, Ts, Te):
    """Tempo: steady Ts through the B1/B2 statement, accelerando to Te at the crash."""
    nbeats = 2 * len(plan_bars) + 1
    ramp0 = 0.0
    for i, (blk, _) in enumerate(plan_bars):
        if blk in ('B1', 'B2'):
            ramp0 = 2 * (i + 1)
    if ramp0 >= nbeats - 1:
        ramp0 = 0.0
    return [(0.0, Ts), (ramp0, Ts), (float(nbeats), Te)], nbeats


def _rm_default_crash(span):
    return float(np.clip(0.45 * span, min(4.0, 0.5 * span), max(0.5 * span, span - 3.0)))


def cue_rag_motif(D, rng, crash_at=None, stop_at=None, tempo=112.0, **_):
    Te = float(tempo)
    if stop_at is not None:
        stop_at = _check_time('stop_at', stop_at, D)
    span = D if stop_at is None else stop_at     # default crash is placed inside [0, stop_at]
    if crash_at is None:
        crash_at = _rm_default_crash(span)
    crash_at = _check_time('crash_at', crash_at, D, lo=min(0.6, D))
    t0 = 0.02
    avail = crash_at - t0
    best = None
    for plan in RM_PLANS:
        pb = [(blk, bar) for blk in plan for bar in RM_BLOCKS[blk.rstrip('+')]]
        def f(Ts, pb=pb):
            pts, nb = _rm_pts(pb, Ts, Te)
            return TempoMap(pts, nb).t(nb)
        lo, hi = 56.0, 150.0
        if avail < f(hi):
            continue
        late = 0.0
        if avail > f(lo):
            # cannot stretch this plan any further: play it at the slowest tempo and
            # start it late (silence before it) so it still lands on the crash
            Ts, late = lo, avail - f(lo)
        else:
            for _ in range(50):
                mid = 0.5 * (lo + hi)
                if f(mid) > avail:
                    lo = mid
                else:
                    hi = mid
            Ts = 0.5 * (lo + hi)
        cost = abs(np.log(Ts / 92.0)) + (0.0 if Ts <= Te * 1.05 else 1.0) + \
            (0.6 if plan == ['B0'] else 0.0) + 3.0 * late / max(avail, 1e-6)
        if best is None or cost < best[0]:
            best = (cost, plan, pb, Ts, late)
    if best is None:
        plan, pb, Ts = [], [], Te
    else:
        _, plan, pb, Ts, late = best
        t0 += late
    if pb:
        pts, nbeats = _rm_pts(pb, Ts, Te)
    else:                                   # no room for the motif: just the pickup
        nbeats = 1
        bpm = max(Te, 60.0 / max(0.12, avail))
        pts = [(0.0, bpm)]
        t0 = crash_at - 60.0 / bpm
    tm = TempoMap(pts, nbeats + 4, t0=t0)
    sc = Score()
    _setup_honky(sc)
    re_ = Realiser(sc, tm, rng, HONKY, sigma=0.008, vsd=4.0,
                   offsets={'mel': -0.003, 'chord': 0.008, 'bass': 0.0},
                   art={'mel': 0.82, 'harm': 0.8, 'bass': 0.5, 'chord': 0.55}, spread=0.003)
    items, pv = [], None
    nbars = len(pb)
    motif_times = []
    for j, (blk, (chs, rh, lh)) in enumerate(pb):
        b0 = 2 * j
        prog = (j + 1) / max(1, nbars)
        dyn = 0.66 + 0.34 * prog
        up = 12 if blk == 'B3+' else 0
        if j == 0 or (blk == 'B1' and pb[j - 1][0] != 'B1'):
            motif_times.append(round(tm.t(b0), 4))
        mel = parse_bar(rh, 2)
        if lh is None:
            its, pv = _stride_items([(chs, [dict(n, p=[p + up for p in n['p']]) for n in mel])], b0,
                                    vel=dyn, rh_oct=(blk != 'B3'), prev_voicing=pv)
            items += its
        else:
            for nt in mel:
                for p in nt['p']:
                    items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p + up,
                                  'v': (74 + (12 if nt['acc'] else 0)) * dyn, 'kind': 'mel',
                                  'grace': nt['grace']})
            for nt in parse_bar(lh, 2):
                for p in nt['p']:
                    items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p,
                                  'v': (70 + (14 if nt['acc'] else 0)) * dyn, 'kind': 'bass'})
    # post-crash rag
    D_body = D - crash_at
    stop_rel = None if stop_at is None else float(stop_at) - crash_at
    hard_stop = None
    if stop_rel is not None and stop_rel <= 0:
        # stop requested at/before the crash: no hang chord, but still honour the stop
        # (hard 30 ms cut at stop_at, silence afterwards)
        stop_rel = None
        hard_stop = stop_at
    sc, info = _rag_body(max(D_body, 0.05), rng, Te, crash_at, stop_rel=stop_rel, pickup=False,
                         sc=sc)
    # pickup into the crash: chromatic approach to the first rag note, LH in octaves
    first_note = None
    for n in sc.notes:
        if n[0] >= crash_at - 0.02 and n[4] == 0 and n[2] >= 60:
            if first_note is None or n[0] < first_note[0] - 0.005 or \
                    (abs(n[0] - first_note[0]) < 0.005 and n[2] > first_note[2]):
                first_note = n
    target = first_note[2] if first_note is not None else pitch('D5')
    pb_beat = 2 * nbars
    for q, dp in enumerate((-2, -1)):
        p = target + dp
        lp = 36 + ((p - 36) % 12)
        items += [{'b': pb_beat + 0.5 * q, 'd': 0.5, 'p': p, 'v': 92, 'kind': 'mel'},
                  {'b': pb_beat + 0.5 * q, 'd': 0.5, 'p': p - 12, 'v': 74, 'kind': 'harm'},
                  {'b': pb_beat + 0.5 * q, 'd': 0.45, 'p': lp, 'v': 84, 'kind': 'bass'},
                  {'b': pb_beat + 0.5 * q, 'd': 0.45, 'p': lp - 12, 'v': 80, 'kind': 'bass'}]
    re_.add(items)
    sc.setup(9, 0, volume=88, pan=76)
    sc.note(crash_at, 2.5, 49, 98, 9)           # crash cymbal
    sc.note(crash_at + 0.002, 2.0, 57, 56, 9)
    sc.note(crash_at, 0.4, 36, 72, 9)           # a soft kick under it
    beats_pre, downs_pre = _beats_events(tm, 0, nbeats - 1, 2)
    markers = {'motif': motif_times, 'crash': round(crash_at, 4)}
    for kk in ('hang_chord', 'stop', 'button'):
        if kk in info:
            markers[kk] = info[kk]
    if hard_stop is not None:
        markers['stop'] = round(hard_stop, 4)
        markers.pop('button', None)
        info['beats'] = [b for b in info['beats'] if b < hard_stop]
        info['downbeats'] = [b for b in info['downbeats'] if b < hard_stop]
        beats_pre = [b for b in beats_pre if b < hard_stop]
        downs_pre = [b for b in downs_pre if b < hard_stop]
        if crash_at >= hard_stop:
            markers.pop('crash', None)
    tail = info.get('tail') or 1.0
    return dict(stems=[dict(score=sc, send=1.0, gain=1.0, width=0.85, eq=HONKY_EQ)],
                ir=dict(rt60=0.85, predelay=0.008), wet=0.12, level=-18.0,
                fade_out=min(0.8, max(0.3, 0.4 * tail)), cut=stop_at,
                beats=beats_pre + info['beats'], downbeats=downs_pre + info['downbeats'],
                markers=markers, tempo=Te)


# ==========================================================================
# 8. CIVIC_SLOW -- the civic theme, slower and tender, motif folded in
# ==========================================================================
CS_BARS = {   # F major: chords [(beat, sym)], melody, walking bass (quarters)
    1: ([(0, 'F')], 'F5:1.5 E5:.5 D5:1 C5:1', [41, 43, 45, 46]),
    2: ([(0, 'C7')], 'Bb4:1 D5:1 C5:2', [48, 46, 43, 40]),
    3: ([(0, 'F'), (1, 'C/E'), (2, 'Dm'), (3, 'Bbmaj7')], 'A4:1 G4:1 F4:1 C5:1', [41, 40, 38, 34]),
    4: ([(0, 'C7')], 'G4:2 r:1 C5:1', [36, 40, 43, 40]),
    5: ([(0, 'F')], 'F5:1.5 E5:.5 D5:1 C5:1', [41, 40, 38, 36]),
    6: ([(0, 'Bbmaj7')], 'D5:1 F5:1 A5:2', [34, 38, 41, 42]),
    7: ([(0, 'Gm7'), (2, 'C7')], 'A5:1 G5:1 E5:1 G5:1', [43, 46, 36, 40]),
    8: ([(0, 'F')], 'F5:2 r:2', [41, 36, 38, 40]),
    9: ([(0, 'F'), (1, 'C/E'), (2, 'Dm'), (3, 'Bb')], 'A4:1 G4:1 F4:1 C5:1', [41, 40, 38, 34]),
}


def _cs_structure(n):
    T = {1: [9], 2: [3, 4], 3: [1, 2, 9], 4: [1, 2, 3, 4], 5: [1, 2, 3, 4, 9],
         6: [1, 2, 3, 4, 6, 7], 7: [1, 2, 3, 4, 5, 6, 7], 8: [1, 2, 3, 4, 5, 6, 7, 9],
         9: [1, 2, 3, 4, 5, 6, 7, 8, 9]}
    if n in T:
        return T[n]
    return [1, 2, 3, 4, 5, 6, 7, 8] + _cs_structure(n - 8)


def cue_civic_slow(D, rng, end='phrase', tempo=66.0, key='F', **_):
    T0 = float(tempo)
    tr = _key_shift(key)
    if end == 'cut':
        n = int(np.ceil(D / (4 * 60.0 / T0))) + 2
        k, tail = 1.0, 0.0
        seq = _cs_structure(n)[:n]
        pts = [(0.0, T0)]
    else:
        cands = []
        for n in range(1, 40):
            T1 = TempoMap(_rit_pts(T0, 4 * n, 2.5, 0.2), 4 * n).t(4 * n)
            cands.append((n, T1))
            if T1 > D * 1.3:
                break
        n, k, tail, pre = _choose(D, cands, 3.6, 2.3, 6.5, 0.10)
        if pre > 0:  # short request: keep the motif bar whole (quicker, shorter ring)
            n, k, tail, pre = _choose(D, cands, 2.3, 1.6, 6.5, 0.30)
        seq = _cs_structure(n)
        pts = _scale_pts(_rit_pts(T0, 4 * n, 2.5, 0.2), k)
    nb = len(seq)
    tm, b_min = _trimmed_map(pts, 4 * nb + 4, 0.0 if end == 'cut' else pre, 0.03)
    sc = Score()
    _setup_piano(sc)
    re_ = Realiser(sc, tm, rng, PIANO, sigma=0.007, vsd=2.5,
                   offsets={'mel': 0.010, 'harm': 0.004, 'bass': 0.0},
                   art={'mel': 0.98, 'harm': 0.95, 'bass': 0.97}, spread=0.006, min_beat=b_min)
    items, changes, chords_abs, motif_times = [], [], [], []
    for j, bid in enumerate(seq):
        chs, mel, bass = CS_BARS[bid]
        b0 = 4 * j
        for q, (cb, sym) in enumerate(chs):
            until = b0 + (chs[q + 1][0] if q + 1 < len(chs) else 4)
            chords_abs.append((b0 + cb, sym, until))
        for q in range(4):
            changes.append(b0 + q)
        if bid in (3, 9) and b0 >= b_min:
            motif_times.append(round(tm.t(b0), 4))
        for q, p in enumerate(bass):
            items.append({'b': b0 + q, 'd': 1.0, 'p': p + tr, 'v': 40 + (4 if q == 0 else 0), 'kind': 'bass'})
        for i, nt in enumerate(parse_bar(mel, 4)):
            p = nt['p'][0]
            sym = [s for cb, s in chs if cb <= nt['o'] + 1e-6][-1]
            arch = 5 * np.sin(np.pi * ((j % 4) + nt['o'] / 4) / 4)
            v = 50 + arch + (3 if bid in (3, 9) else 0)
            items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': p + tr, 'v': v, 'kind': 'mel'})
            if nt['d'] >= 1:
                h = harmony_below(p, chord(sym)['pcs'])
                if h is not None:
                    items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': h + tr, 'v': v - 13, 'kind': 'harm'})
                    h2 = harmony_below(h, chord(sym)['pcs'], prefs=(3, 4, 5))
                    if h2 is not None and h2 >= 55 and nt['d'] >= 2:
                        items.append({'b': b0 + nt['o'], 'd': nt['d'], 'p': h2 + tr, 'v': v - 16, 'kind': 'harm'})
    markers = {'motif': motif_times}
    if end != 'cut':
        bf = 4 * nb
        tf = tm.t(bf)
        for p, v in [(29, 34), (41, 40), (48, 36), (57, 38), (60, 38), (65, 44)]:
            items.append({'b': bf, 'd': 4, 'p': p + tr, 'v': v, 'kind': 'harm', 'dur_s': D - tf - 0.02})
        changes.append(bf)
        chords_abs.append((bf, 'F', bf + 64))
        markers['final_chord'] = round(tf, 4)
    re_.add(items)
    _pedal_from_changes(sc, tm, changes, [0])
    # faint string pad
    ss = Score()
    ss.setup(0, 49, volume=100, pan=56, expression=0)
    ss.setup(1, 48, volume=78, pan=76, expression=0)
    pad = _pad_items(chords_abs, 45, 64, 40)
    for it in pad:
        if it['b'] >= 4 * nb:
            it['dur_s'] = D - tm.t(it['b']) - 0.02
        else:
            it['dur_s'] = max(0.1, tm.t(it['b'] + it['d']) - tm.t(it['b']))
        it['p'] += tr
    for it in pad:
        if it['b'] < b_min:
            t_end = tm.t(it['b']) + it['dur_s']
            it['b'] = b_min
            it['dur_s'] = max(0.05, t_end - tm.t(b_min))
    rs = Realiser(ss, tm, rng, [(0, 1.0, 0.0), (1, 0.8, 0.025)], sigma=0.01, vsd=2.0,
                  art={'pad': 1.0}, spread=0.02)
    rs.add(pad)
    for t in np.arange(0, D, 0.03):
        u = np.clip(t / 2.5, 0, 1)
        fo = np.clip((D - 0.1 - t) / max(1.5, 0.7 * max(tail, 2.0)), 0, 1)
        val = 66 * (u * u * (3 - 2 * u)) * (fo * fo * (3 - 2 * fo))
        for ch in (0, 1):
            ss.cc(t, ch, 11, val)
    stems = [dict(score=sc, send=1.0, gain=1.0, width=0.9, eq=[('hp', 30), ('hs', 6000, -2.5)]),
             dict(score=ss, send=1.5, gain=0.55, width=1.0,
                  eq=[('hp', 50), ('ls', 140, -2), ('hs', 3500, -6), ('lp', 7000)])]
    beats, downs = _beats_events(tm, b_min, 4 * nb if end != 'cut' else 4 * nb - 1, 4,
                                 first_bar_beat=4 * np.ceil(b_min / 4))
    beats = [b for b in beats if b < D]
    downs = [b for b in downs if b < D]
    return dict(stems=stems, ir=dict(rt60=1.7, predelay=0.016), wet=0.2, level=-23.0,
                fade_out=(0.03 if end == 'cut' else min(2.5, max(0.8, 0.5 * tail))),
                cut=(D if end == 'cut' else None), beats=beats, downbeats=downs,
                markers=markers, tempo=tm.bpm(0))


# ==========================================================================
# 9. FINAL_CHORD -- one warm soft add9 chord ringing out
# ==========================================================================
def cue_final_chord(D, rng, key='F', roll=0.12, with_strings=None, **_):
    tr = _key_shift(key)
    voicing = [p + tr for p in (41, 48, 57, 67, 72)]
    vels = [40, 36, 38, 40, 46]
    sc = Score()
    _setup_piano(sc)
    t0 = 0.03
    sc.pedal([0], 0.0, True)
    for i, (p, v) in enumerate(zip(voicing, vels)):
        t = t0 + roll * (i / max(1, len(voicing) - 1)) ** 1.2 + rng.normal(0, 0.003)
        sc.note(t, D - t - 0.02, p, v + rng.normal(0, 1.5), 0)
    stems = [dict(score=sc, send=1.0, gain=1.0, width=0.9, eq=[('hp', 30), ('hs', 6000, -2.0)])]
    if with_strings is None:
        with_strings = D > 14.0
    if with_strings:
        # the piano decays below -60 dB after ~11 s; a faint pad keeps the chord alive
        ss = Score()
        ss.setup(0, 49, volume=100, pan=56, expression=0)
        ss.setup(1, 48, volume=76, pan=76, expression=0)
        for i, p in enumerate([41 + tr, 48 + tr, 57 + tr, 67 + tr]):
            for ch, vs, dt in ((0, 1.0, 0.0), (1, 0.8, 0.03)):
                ss.note(0.6 + 0.05 * i + dt, D - 0.7, p, 42 * vs, ch)
        t_in = min(10.0, 0.35 * D)
        for t in np.arange(0, D, 0.03):
            u = np.clip((t - 0.6) / t_in, 0, 1)
            fo = np.clip((D - 0.1 - t) / (0.45 * D), 0, 1)
            val = 58 * (u * u * (3 - 2 * u)) * (fo * fo * (3 - 2 * fo))
            for ch in (0, 1):
                ss.cc(t, ch, 11, val)
        stems.append(dict(score=ss, send=1.6, gain=0.18, width=1.0,
                          eq=[('hp', 45), ('ls', 140, -2), ('hs', 3000, -7), ('lp', 6500)]))
    return dict(stems=stems, ir=dict(rt60=2.0, predelay=0.018), wet=0.24, level=-25.0,
                fade_out=max(0.3, min(0.35 * D, 8.0)) if not with_strings else 0.45 * D,
                cut=None, beats=[0.03], downbeats=[0.03], markers={'chord': t0}, tempo=None)


_CUE_FUNCS = {
    'civic': cue_civic, 'rag': cue_rag, 'tiptoe': cue_tiptoe, 'vamp': cue_vamp,
    'cello_note': cue_cello_note, 'name_piano': cue_name_piano, 'rag_motif': cue_rag_motif,
    'civic_slow': cue_civic_slow, 'final_chord': cue_final_chord,
}


def _cue_params(name):
    """Names of the cue-specific keyword parameters `name` accepts."""
    sig = inspect.signature(_CUE_FUNCS[name])
    ps = {p.name for p in sig.parameters.values()
          if p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)} - {'D', 'rng'}
    if name == 'cello_note':
        ps = (ps - {'pitch_'}) | {'pitch'}
    return ps


# ==========================================================================
# public entry point
# ==========================================================================
def render_cue(name, out_wav, duration, **params):
    """Render cue `name` to `out_wav` (48 kHz stereo float32), exactly `duration` s."""
    if name not in _CUE_FUNCS:
        raise ValueError('unknown cue %r (have %s)' % (name, ', '.join(CUES)))
    D = float(duration)
    if D <= 0.1:
        raise ValueError('duration too short')
    seed = int(params.pop('seed', 0))
    gain_db = float(params.pop('gain_db', 0.0))
    rev_mul = float(params.pop('reverb', 1.0))
    fade_override = params.pop('fade_out', None)
    pcm16 = bool(params.pop('pcm16', False))
    cut_dead = bool(params.pop('cut', False))
    allowed = _cue_params(name)
    unknown = sorted(set(params) - allowed)
    if unknown:
        raise TypeError('cue %r got unknown parameter(s) %s; it accepts %s plus the common '
                        'seed, gain_db, reverb, fade_out, pcm16, cut'
                        % (name, ', '.join(unknown), ', '.join(sorted(allowed)) or 'nothing else'))
    rng = _rng(name, seed)
    D_comp = D
    if cut_dead:
        # stop dead at `duration`, mid-phrase: compose a longer cue and cut it (30 ms fade)
        if name in ('civic', 'civic_slow'):
            params.setdefault('end', 'cut')
        elif not (name in ('rag', 'rag_motif') and params.get('stop_at') is not None):
            if name == 'rag_motif' and params.get('crash_at') is None:
                params['crash_at'] = _rm_default_crash(D)
            D_comp = D + max(3.0, 0.5 * D)
    cue = _CUE_FUNCS[name](D_comp, rng, **params)
    # markers are only meaningful inside the file
    cue['markers'] = {k_: ([v for v in v_ if v < D] if isinstance(v_, list) else v_)
                      for k_, v_ in cue.get('markers', {}).items()}
    if cut_dead:
        cue['markers']['stop'] = round(D, 4)
    if D_comp > D:
        cue['cut'] = D
        cue['beats'] = [b for b in cue.get('beats', []) if b < D]
        cue['downbeats'] = [b for b in cue.get('downbeats', []) if b < D]
        mk = {}
        for k_, v_ in cue.get('markers', {}).items():
            if isinstance(v_, list):
                mk[k_] = [v for v in v_ if v < D]
            elif v_ is None or v_ < D:
                mk[k_] = v_
        mk['stop'] = round(D, 4)
        cue['markers'] = mk
    N = int(round(D * SR))
    n_render = N + int(0.3 * SR)
    audios = _render_stems(cue['stems'], n_render)
    dry = np.zeros((n_render, 2))
    send = np.zeros(n_render)
    for st, a in zip(cue['stems'], audios):
        a = apply_eq(a, st.get('eq', []))
        a = _width(a, st.get('width', 1.0)) * st.get('gain', 1.0)
        dry += a
        send += st.get('send', 1.0) * a.mean(axis=1)
    irp = cue['ir']
    ir = make_ir(rt60=irp['rt60'], predelay=irp['predelay'], seed=zlib.crc32(name.encode()) & 0xFFFF)
    wet = np.stack([signal.fftconvolve(send, ir[:, c])[:n_render] for c in range(2)], axis=1)
    mix = dry + cue['wet'] * rev_mul * wet
    sos = signal.butter(2, 22.0, 'highpass', fs=SR, output='sos')
    mix = signal.sosfiltfilt(sos, mix, axis=0)
    mix = mix[:N]
    if len(mix) < N:
        mix = np.concatenate([mix, np.zeros((N - len(mix), 2))])
    cut = cue.get('cut')
    ref = mix
    if cut is not None and cut <= D + 1e-9:
        ci = min(N, int(round(cut * SR)))
        # loudness reference: the music up to the stop (at least 0.4 s of it, measured
        # before the cut so a very early stop cannot blow the gain up or divide by zero)
        ref = mix[:max(ci, min(N, int(0.4 * SR)))].copy()
        fl = int(0.03 * SR)
        a0 = max(0, ci - fl)
        mix[a0:ci] *= (1.0 - _fade(ci - a0))[:, None]
        mix[ci:] = 0.0
    # loudness normalisation (gated RMS) + transparent limiting to the ceiling
    g_rms = gated_rms(ref)
    target = 10 ** ((cue['level'] + gain_db) / 20.0)
    g = target / max(g_rms, 1e-9) if np.isfinite(g_rms) else 1.0
    ceil_lin = 10 ** (PEAK_CEIL_DB / 20.0) * 0.985
    pk = np.max(np.abs(mix)) * g
    if pk > ceil_lin * 1.6:                     # never limit more than ~4 dB
        g *= ceil_lin * 1.6 / pk
    mix = limiter(mix * g, ceil_lin)
    # fades
    fi = int(0.008 * SR)
    mix[:fi] *= _fade(fi)[:, None]
    if cut is None or cut > D:
        fo = float(fade_override) if fade_override is not None else float(cue['fade_out'])
        fo_n = max(int(0.01 * SR), int(fo * SR))
        fo_n = min(fo_n, N // 2)
        mix[N - fo_n:] *= (1.0 - _fade(fo_n))[:, None]
    mix[-1] = 0.0
    if not np.all(np.isfinite(mix)):
        raise RuntimeError('render_cue(%r): non-finite samples' % name)
    pk = np.max(np.abs(mix))
    if pk > ceil_lin:
        mix *= ceil_lin / pk
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    write_wav(out_wav, mix, pcm16=pcm16, seed=seed)
    rms_all = np.sqrt(np.mean(mix ** 2))
    return {
        'path': os.path.abspath(out_wav), 'duration': N / SR, 'sr': SR,
        'events': [float(b) for b in cue.get('beats', [])],
        'downbeats': [float(b) for b in cue.get('downbeats', [])],
        'markers': cue.get('markers', {}),
        'tempo': cue.get('tempo'),
        'peak_db': round(_db(np.max(np.abs(mix))), 2),
        'rms_db': round(_db(rms_all), 2),
    }


if __name__ == '__main__':
    import json
    import sys
    name = sys.argv[1]
    out = sys.argv[2]
    dur = float(sys.argv[3])
    kw = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    r = render_cue(name, out, dur, **kw)
    r['events'] = r['events'][:8]
    r['downbeats'] = r['downbeats'][:8]
    print(json.dumps(r, indent=1))
