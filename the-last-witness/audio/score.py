#!/usr/bin/env python3
"""Procedural score + sound design for "The Last Witness".

Reads build/timeline.json and renders (at an internal 24 kHz rate, upsampled to
48 kHz at the end) four un-ducked buses into build/audio/work/:

    bed.npy     mood-driven score bed (pads, bass/cello, piano/bell phrases, ...)
    cues.npy    word cues (high/low/swell/light/hit) + scored key moments
    amb.npy     location ambiences (room / ship / void / new universe)
    events.npy  sound events (scene whooshes, heartbeat, button click)

plus previews build/audio/work/music_raw.wav and sfx_raw.wav.
audio/mix.py then ducks these under the voice and makes the final stems + mix.

Run:  python3 -I audio/score.py
"""
import json
import os
import time
import wave

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TIMELINE = os.path.join(ROOT, "build", "timeline.json")
WORK = os.path.join(ROOT, "build", "audio", "work")

SR = 24000          # internal render rate (music needs nothing above ~10 kHz)
OUT_SR = 48000
RNG = np.random.default_rng(20251030)

# --------------------------------------------------------------------------
# basic helpers
# --------------------------------------------------------------------------


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=np.float64) - 69.0) / 12.0)


def ns(sec):
    return max(1, int(round(sec * SR)))


def rcos_in(n):
    """raised-cosine 0->1 ramp of n samples"""
    if n <= 0:
        return np.ones(0, np.float32)
    return (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))).astype(np.float32)


def env_ar(n, a, r, shape=1.0):
    """attack/sustain/release envelope (seconds) for an n-sample note"""
    e = np.ones(n, np.float32)
    na, nr = min(ns(a), n // 2), min(ns(r), n // 2)
    if na > 0:
        e[:na] = rcos_in(na) ** shape
    if nr > 0:
        e[n - nr:] *= rcos_in(nr)[::-1]
    return e


class Bus:
    """dry + reverb-send pair of float32 buffers spanning the whole film"""

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
        if gain != 0:
            self.dry[i0:i0 + m] += gain * seg
        if send:
            self.send[i0:i0 + m] += send * seg


# --------------------------------------------------------------------------
# oscillators / instruments
# --------------------------------------------------------------------------
TS = 4096


def make_table(b, K=20, p=1.0):
    k = np.arange(1, K + 1, dtype=np.float64)
    amps = (1.0 / k ** p) * np.exp(-(k - 1) / b)
    ph = np.arange(TS) / TS
    tab = (amps[:, None] * np.sin(2 * np.pi * k[:, None] * ph[None, :])).sum(0)
    return (tab / np.abs(tab).max()).astype(np.float32)


TAB = {
    "sine": np.sin(2 * np.pi * np.arange(TS) / TS).astype(np.float32),
    "dark": make_table(1.0),     # nearly a sine with a soft 2nd/3rd harmonic
    "warm": make_table(2.6),     # filtered saw (string-pad body)
    "bright": make_table(4.5),   # a little more bow / air, used sparingly
}


def osc(tab, f, n, phase0=0.0, vib_rate=0.0, vib_depth=0.0, drift=0.0):
    t = np.arange(n, dtype=np.float64) / SR
    if vib_depth or drift:
        inst = f * (1.0 + vib_depth * np.sin(2 * np.pi * vib_rate * t + RNG.uniform(0, 6.28))
                    + drift * np.sin(2 * np.pi * 0.07 * t + RNG.uniform(0, 6.28)))
        ph = np.cumsum(inst) / SR + phase0
    else:
        ph = f * t + phase0
    idx = (ph % 1.0) * TS
    i0 = idx.astype(np.int32)
    fr = (idx - i0).astype(np.float32)
    t0 = TAB[tab] if isinstance(tab, str) else tab
    return t0[i0] * (1 - fr) + t0[(i0 + 1) % TS] * fr


def osc_morph(f, n, bright, vib_rate=0.0, vib_depth=0.0, drift=0.0006):
    """detuned voice that morphs dark<->warm with a slow LFO (a 'breathing' lowpass)"""
    t = np.arange(n, dtype=np.float64) / SR
    inst = f * (1.0 + vib_depth * np.sin(2 * np.pi * vib_rate * t + RNG.uniform(0, 6.28))
                + drift * np.sin(2 * np.pi * RNG.uniform(0.05, 0.11) * t + RNG.uniform(0, 6.28)))
    ph = np.cumsum(inst) / SR + RNG.uniform(0, 1)
    idx = (ph % 1.0) * TS
    i0 = idx.astype(np.int32)
    i1 = (i0 + 1) % TS
    fr = (idx - i0).astype(np.float32)
    d = TAB["dark"][i0] * (1 - fr) + TAB["dark"][i1] * fr
    w = TAB["warm"][i0] * (1 - fr) + TAB["warm"][i1] * fr
    # high notes stay darker (keeps the top end smooth for the low-bitrate codec)
    b = bright * float(np.clip(500.0 / f, 0.3, 1.0))
    m = np.clip(b + 0.22 * np.sin(2 * np.pi * RNG.uniform(0.03, 0.08) * t + RNG.uniform(0, 6.28)), 0, 1)
    m = m.astype(np.float32)
    return d * (1 - m) + w * m


def pad_note(f, dur, a=2.5, r=3.0, bright=0.4, voices=3, spread=7.0):
    n = ns(dur)
    out = np.zeros(n, np.float32)
    for v in range(voices):
        det = (v - (voices - 1) / 2) * spread + RNG.normal(0, 1.2)
        out += osc_morph(f * 2 ** (det / 1200), n, bright)
    t = np.arange(n) / SR
    am = 1.0 + 0.12 * np.sin(2 * np.pi * RNG.uniform(0.04, 0.09) * t + RNG.uniform(0, 6.28))
    return out * env_ar(n, a, r) * am.astype(np.float32) / np.sqrt(voices)


def cello_note(f, dur, a=1.2, r=2.5, bright=0.55, vib=0.0028):
    n = ns(dur)
    x = 0.6 * osc_morph(f, n, bright, vib_rate=4.6, vib_depth=vib) + \
        0.5 * osc_morph(f * 1.003, n, bright * 0.8, vib_rate=4.9, vib_depth=vib)
    # vibrato and bow pressure fade in after the attack
    t = np.arange(n) / SR
    swell = 0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t + RNG.uniform(0, 6.28))
    return x * env_ar(n, a, r) * swell.astype(np.float32)


def sub_note(f, dur, a=2.0, r=2.5):
    n = ns(dur)
    return osc("dark", f, n, RNG.uniform(0, 1)) * env_ar(n, a, r)


def piano_note(f, vel=0.4, dur=None):
    """soft felt piano: few partials, slight inharmonicity, two-stage decay"""
    if dur is None:
        dur = float(np.clip(5.0 * (300.0 / f) ** 0.35, 2.2, 6.0))
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.zeros(n, np.float64)
    base_tau = 2.4 * (262.0 / f) ** 0.45
    rel = [1.0, 0.42, 0.18, 0.09, 0.045, 0.02]
    for k, ra in enumerate(rel, 1):
        fk = f * k * np.sqrt(1 + 0.00035 * k * k)
        if fk > 7000:
            break
        amp = ra * (vel / 0.6) ** (0.6 * (k - 1))
        tau = base_tau / (1.0 + 0.7 * (k - 1))
        e = 0.55 * np.exp(-t / (tau * 0.25)) + 0.45 * np.exp(-t / tau)
        out += amp * e * np.sin(2 * np.pi * fk * t + RNG.uniform(0, 6.28))
    out *= vel
    e = env_ar(n, 0.006, 0.35)
    return (out * e).astype(np.float32)


def bell_note(f, vel=0.4, dur=4.5):
    """soft glass bell: near-harmonic partials, gentle 12 ms attack"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.zeros(n)
    for ratio, amp, tau in ((1.0, 1.0, 2.6), (2.0, 0.22, 1.3), (3.003, 0.07, 0.7), (4.2, 0.025, 0.4)):
        fk = f * ratio
        if fk > 8000:
            continue
        out += amp * np.exp(-t / tau) * np.sin(2 * np.pi * fk * t + RNG.uniform(0, 6.28))
    return (vel * out * env_ar(n, 0.012, 0.4)).astype(np.float32)


def glass_tone(f, dur=3.0, a=0.25, r=2.0):
    """sustained high sine pair (for the 'high' cue sustain and lone tones)"""
    n = ns(dur)
    x = 0.55 * osc("sine", f, n, RNG.uniform(0, 1), 5.0, 0.0012) + \
        0.45 * osc("sine", f * 1.0025, n, RNG.uniform(0, 1))
    x += 0.12 * osc("sine", 2 * f, n, RNG.uniform(0, 1)) if 2 * f < 6000 else 0
    return x * env_ar(n, a, r)


def pluck_note(f, vel=0.4, dur=1.2):
    """marimba-ish soft pluck (playful / light)"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    out = np.exp(-t / 0.32) * np.sin(2 * np.pi * f * t)
    out += 0.18 * np.exp(-t / 0.12) * np.sin(2 * np.pi * 2 * f * t)
    if 3.93 * f < 7000:
        out += 0.07 * np.exp(-t / 0.05) * np.sin(2 * np.pi * 3.93 * f * t)
    return (vel * out * env_ar(n, 0.003, 0.2)).astype(np.float32)


def lowpass(x, fc, order=2):
    sos = signal.butter(order, fc, "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def bandpass(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "band", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def felt_hit(f0=55.0, vel=0.6, dur=3.0):
    """soft deep impact: felt timpani (pitch-drop sine + timpani modes) + muted thump"""
    n = ns(dur)
    t = np.arange(n, dtype=np.float64) / SR
    inst = f0 * (1 + 0.25 * np.exp(-t / 0.045))
    ph = 2 * np.pi * np.cumsum(inst) / SR
    out = np.exp(-t / 1.0) * np.sin(ph)
    out += 0.45 * np.exp(-t / 0.55) * np.sin(1.504 * ph)
    out += 0.28 * np.exp(-t / 0.35) * np.sin(1.742 * ph)
    out += 0.18 * np.exp(-t / 0.25) * np.sin(2.0 * ph)
    thump = lowpass(RNG.standard_normal(n).astype(np.float32), 240, 2) * np.exp(-t / 0.035)
    out = out + 0.9 * thump
    return (vel * out * env_ar(n, 0.004, 0.6)).astype(np.float32)


def tv_lowpass(x, fc, block=128):
    """time-varying 2-pole lowpass (cascaded one-poles), fc = per-sample cutoff array"""
    y = np.empty_like(x)
    z1 = np.zeros(1)
    z2 = np.zeros(1)
    for i in range(0, len(x), block):
        a = np.exp(-2 * np.pi * float(fc[i]) / SR)
        s, z1 = signal.lfilter([1 - a], [1, -a], x[i:i + block], zi=z1)
        y[i:i + block], z2 = signal.lfilter([1 - a], [1, -a], s, zi=z2)
    return y


def whoosh(dur=1.8, f_lo=180, f_hi=1500, vel=0.5):
    """soft air whoosh: noise through a lowpass sweeping up then down"""
    n = ns(dur)
    x = RNG.standard_normal(n).astype(np.float32)
    u = np.linspace(0, 1, n)
    shape = np.sin(np.pi * u) ** 2
    fc = f_lo * (f_hi / f_lo) ** shape
    y = tv_lowpass(x, fc)
    y = y - lowpass(y, 90, 2)  # no rumble
    return (vel * y * shape ** 1.4 / (np.std(y) + 1e-9) * 0.3).astype(np.float32)


def make_ir(dur, t60, lp_start, lp_end, predelay=0.02, seed=1):
    r = np.random.default_rng(seed)
    n = ns(dur)
    t = np.arange(n) / SR
    noise = r.standard_normal(n).astype(np.float32)
    bright = lowpass(noise, lp_start, 2)
    dark = lowpass(noise, lp_end, 2)
    x = np.linspace(0, 1, n) ** 0.6
    ir = (bright * (1 - x) + dark * x) * (10 ** (-3 * t / t60))
    ir[:ns(0.006)] *= rcos_in(ns(0.006))
    ir = np.concatenate([np.zeros(ns(predelay), np.float32), ir.astype(np.float32)])
    return ir / np.sqrt(np.sum(ir ** 2))


# --------------------------------------------------------------------------
# harmony
# --------------------------------------------------------------------------
VOICING = {
    "maj": [0, 7, 16], "add9": [0, 7, 14, 16], "maj7": [0, 7, 11, 16],
    "min": [0, 7, 15], "m7": [0, 7, 10, 15], "sus2": [0, 7, 14],
    "fifth9": [0, 7, 14, 19], "wide": [0, 7, 12, 16, 19],
    "cl": [0, 1, 7], "cl2": [0, 6, 13], "minb6": [0, 8, 15],
}
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11], "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "majpent": [0, 2, 4, 7, 9],
}
# mood -> scale / progression (root offset from tonic, voicing) / chord length /
# register / level / layer densities (phrases per minute)
MOODS = {
    "intimate":   dict(scale="major", prog=[(0, "add9"), (9, "m7"), (5, "maj7"), (0, "add9")], L=9.0, base=50, amp=0.9, bright=0.30, bass=0.45, piano=2.2, contour="arc", att=2.5, gap=0.75),
    "curious":    dict(scale="lydian", prog=[(0, "add9"), (2, "maj"), (0, "maj7"), (2, "sus2")], L=6.5, base=52, amp=0.8, bright=0.40, bass=0.35, piano=3.0, contour="rise", att=2.0, gap=0.5),
    "wonder":     dict(scale="major", prog=[(0, "fifth9"), (10, "fifth9"), (5, "fifth9"), (0, "fifth9")], L=9.0, base=50, amp=0.9, bright=0.45, bass=0.4, bells=2.0, shimmer=1.0, contour="rise", att=3.0, gap=0.9),
    "awe":        dict(scale="major", prog=[(0, "wide"), (8, "wide"), (10, "wide"), (0, "wide")], L=10.0, base=45, amp=1.0, bright=0.50, bass=0.7, bells=1.3, shimmer=1.0, contour="rise", att=3.5, gap=1.0),
    "melancholy": dict(scale="minor", prog=[(0, "m7"), (8, "maj7"), (3, "maj"), (10, "maj")], L=8.5, base=48, amp=0.85, bright=0.28, bass=0.55, piano=1.6, contour="fall", att=3.0, gap=0.85),
    "grief":      dict(scale="minor", prog=[(0, "min"), (5, "min"), (0, "m7"), (8, "maj")], L=11.0, base=45, amp=0.75, bright=0.20, bass=0.6, cello=0.8, piano=0.9, contour="fall", att=3.5, gap=1.1),
    "dread":      dict(scale="phrygian", prog=[(0, "cl"), (1, "maj"), (0, "cl2"), (8, "min")], L=12.0, base=40, amp=0.75, bright=0.15, bass=0.8, cello=0.9, contour="fall", att=4.0, gap=1.0),
    "tension":    dict(scale="minor", prog=[(0, "min"), (8, "maj"), (0, "minb6"), (1, "maj")], L=7.0, base=45, amp=0.75, bright=0.28, bass=0.6, ostinato=1.25, piano=0.8, contour="rise", att=2.0, gap=0.6),
    "resolve":    dict(scale="major", prog=[(9, "min"), (5, "add9"), (0, "maj"), (7, "sus2")], L=7.0, base=48, amp=0.9, bright=0.40, bass=0.6, piano=2.0, contour="rise", att=2.0, gap=0.6),
    "hope":       dict(scale="major", prog=[(0, "add9"), (7, "maj"), (9, "m7"), (5, "add9")], L=7.5, base=55, amp=0.9, bright=0.45, bass=0.45, piano=3.0, contour="rise", att=2.0, gap=0.55),
    "tender":     dict(scale="major", prog=[(0, "maj7"), (4, "m7"), (5, "add9"), (0, "maj")], L=8.5, base=53, amp=0.8, bright=0.30, bass=0.4, piano=2.5, contour="arc", att=2.5, gap=0.7),
    "playful":    dict(scale="majpent", prog=[(0, "maj"), (5, "maj"), (7, "maj"), (0, "maj")], L=4.5, base=55, amp=0.45, bright=0.35, bass=0.3, plucks=7.0, att=1.2, gap=0.3),
    "triumph":    dict(scale="major", prog=[(0, "wide"), (5, "wide"), (7, "wide"), (0, "wide")], L=6.0, base=48, amp=1.05, bright=0.55, bass=0.8, piano=2.0, bells=1.0, contour="rise", att=1.5, gap=0.5),
    "silence":    dict(scale="major", lone=True),
}
PC = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
ACT_KEYS = ["D", "C", "F", "A", "Eb", "D"]   # tonic per act (parallel major/minor by mood)


def nearest(pc, around):
    """midi note with pitch class pc nearest to `around`"""
    m = around + ((pc - around) % 12)
    return m - 12 if m - around > 6 else m


# --------------------------------------------------------------------------
# score renderer
# --------------------------------------------------------------------------
class Score:
    def __init__(self, tl):
        self.tl = tl
        self.dur = float(tl["duration"])
        self.n = int(np.ceil(self.dur * SR)) + 1
        self.bed = Bus(self.n)
        self.cues = Bus(self.n)
        self.amb = np.zeros(self.n, np.float32)
        self.events = Bus(self.n)
        self.beats = tl["beats"]
        self.speech = [(b["start"], b["end"]) for b in self.beats if b["kind"] == "speech"]
        self.speech.sort()
        # key-change times: act cards, except Act V whose key arrives with the big bang
        self.bang = self.find("And pressed the button.")
        self.key_changes = []
        for a in tl["acts"]:
            t = a["start"] - 0.3
            if a["act"] == 4:
                t = self.bang["end"] + 0.4
            self.key_changes.append((t if a["act"] else 0.0, PC[ACT_KEYS[a["act"]]]))
        self.segments = []   # (t0, t1, mood, tonic, chords[(tc, root_midi, notes, scale_pcs)])

    # ---- lookups -----------------------------------------------------
    def find(self, text):
        for b in self.beats:
            if b.get("text", "").strip().startswith(text):
                return b
        raise KeyError(text)

    def tonic_at(self, t):
        k = self.key_changes[0][1]
        for tc, pc in self.key_changes:
            if t >= tc:
                k = pc
        return k

    def chord_at(self, t):
        best = None
        for s in self.segments:
            if s[0] <= t and s[4]:
                best = s
        if best is not None:
            cur = best[4][0]
            for c in best[4]:
                if c[0] <= t:
                    cur = c
            return best[2], best[3], cur
        return "intimate", self.tonic_at(t), (t, 50, [50, 57, 66], SCALES["major"])

    def in_speech(self, t):
        for a, b in self.speech:
            if a <= t <= b:
                return True
        return False

    def gaps(self, t0, t1, min_len):
        """pauses between speech beats inside [t0, t1)"""
        out = []
        prev_end = 0.0
        for a, b in self.speech + [(self.dur, self.dur)]:
            if a - prev_end >= min_len and t0 <= prev_end < t1:
                out.append((prev_end, a))
            prev_end = max(prev_end, b)
        return out

    # ---- mood segments ------------------------------------------------
    def mood_segments(self):
        moods = self.tl["music"]["moods"]
        segs = []
        for m in moods:
            if segs and segs[-1][2] == m["mood"]:
                continue
            if segs and m["t"] - segs[-1][0] < 0.05:
                segs[-1] = (segs[-1][0], None, m["mood"])
                continue
            segs.append((float(m["t"]), None, m["mood"]))
        out = []
        for i, (t0, _, mood) in enumerate(segs):
            t1 = segs[i + 1][0] if i + 1 < len(segs) else self.dur
            out.append((t0, t1, mood))
        return out

    def render_bed(self):
        segs = self.mood_segments()
        last = len(segs) - 1
        for i, (t0, t1, mood) in enumerate(segs):
            P = MOODS[mood]
            tonic = self.tonic_at(t0 + 0.01)
            xf = float(np.clip(min(t1 - t0, segs[i - 1][1] - segs[i - 1][0] if i else 9) * 0.6, 1.5, 3.0))
            a_ = 0.0 if i == 0 else t0 - xf / 2
            b_ = self.dur if i == last else t1 + xf / 2
            final = i == last
            seg_len = b_ - a_
            buf = np.zeros(ns(seg_len + 0.1), np.float32)
            chords = []
            scale = [(tonic + s) % 12 for s in SCALES[P["scale"]]]
            if P.get("lone"):
                f = mtof(nearest(tonic, 69) + 7)    # a lone fifth-of-tonic, thin and high
                x = glass_tone(f, seg_len, a=min(2.5, seg_len / 3), r=min(3.0, seg_len / 3)) * 0.016
                x += sub_note(mtof(nearest(tonic, 33)), seg_len, a=3, r=3) * 0.010
                buf[:len(x)] += x
                chords.append((a_, nearest(tonic, 50), [nearest(tonic, 50)], scale))
            else:
                prog = P["prog"]
                L = P["L"]
                if final:      # the closing chord: one long hopeful tonic, no progression
                    prog = [(0, "wide")]
                    L = seg_len
                k = 0
                tc = a_
                while tc < b_ - 0.5:
                    off, vname = prog[k % len(prog)]
                    root = nearest((tonic + off) % 12, P["base"])
                    notes = [root + v for v in VOICING[vname]]
                    chords.append((tc, root, notes, scale))
                    dur = min(L, b_ - tc) + (P["att"] * 0.9 if not final else 0)
                    rel = min(3.0, max(1.0, dur * 0.35)) if not final else 9.0
                    off_t = tc - a_
                    amp = 0.055 * P["amp"] / np.sqrt(len(notes))
                    for nm in notes:
                        x = pad_note(mtof(nm), dur, a=P["att"] if not final else 3.5, r=rel,
                                     bright=P["bright"] + (0.12 if final else 0.0))
                        self._mix(buf, off_t, x * amp)
                    if P.get("bass"):
                        bn = root - 12 if root - 12 >= 36 else root
                        x = sub_note(mtof(bn), dur, a=P["att"], r=rel) * 0.05 * P["bass"]
                        self._mix(buf, off_t, x)
                    if P.get("cello"):
                        cn = root - 12 if root - 12 >= 33 else root
                        x = cello_note(mtof(cn), dur, a=2.0, r=rel, bright=0.45) * 0.035 * P["cello"]
                        self._mix(buf, off_t, x)
                    if P.get("shimmer"):
                        for sn in (nearest(tonic, 81), nearest((tonic + 7) % 12, 88)):
                            x = glass_tone(mtof(sn), dur, a=3.0, r=rel) * 0.006 * P["shimmer"]
                            t = np.arange(len(x)) / SR
                            x *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t + RNG.uniform(0, 6))).astype(np.float32)
                            self._mix(buf, off_t, x)
                    tc += L
                    k += 1
                if P.get("ostinato"):
                    tt = a_ + 0.5
                    j = 0
                    while tt < b_ - 1:
                        _, root, _, _ = [c for c in chords if c[0] <= tt][-1]
                        bn = (root - 12 if root - 12 >= 36 else root) + (7 if j % 4 == 2 else 0)
                        x = pluck_note(mtof(bn), 0.08, 1.4)
                        self._mix(buf, tt - a_, lowpass(x, 600) * (0.8 if j % 2 else 1.0))
                        tt += P["ostinato"]
                        j += 1
            # segment envelope: equal-power crossfades
            e = np.ones(len(buf), np.float32)
            nxf = ns(xf)
            if i > 0:
                e[:nxf] = np.sin(0.5 * np.pi * np.linspace(0, 1, nxf)).astype(np.float32)
            else:
                e[:ns(3.0)] = rcos_in(ns(3.0))
            if not final:
                end = ns(seg_len)
                e[end - nxf:end] *= np.cos(0.5 * np.pi * np.linspace(0, 1, nxf)).astype(np.float32)
                e[end:] = 0
            buf *= e
            buf *= self.seg_automation(a_, len(buf))
            self.bed.add(a_, buf, 1.0, 0.32)
            self.segments.append((t0, t1, mood, tonic, chords))
            # melodic layers (start inside the segment, ring out naturally)
            self.melodic(t0, t1, mood, tonic, chords)

    def seg_automation(self, a_, n):
        """scripted thinning of the bed (death scene, held breath before the big bang)"""
        t = a_ + np.arange(n) / SR
        g = np.ones(n, np.float32)
        d0 = self.find("Until your breath slows.")["start"]
        d1 = self.find("Until you are gone.")["end"]
        # the last human dies: bed thins to near silence by the end of "Until you are gone."
        m = t >= d0
        g[m] = np.interp(t[m], [d0, d1 + 0.3], [1.0, 0.04])
        remains = self.find("And the AI remains.")["start"]
        g[(t > d1 + 0.3) & (t < remains - 0.4)] = np.minimum(g[(t > d1 + 0.3) & (t < remains - 0.4)], 0.04)
        m2 = t >= remains - 0.4
        g[m2] = np.interp(t[m2], [remains - 0.4, remains + 0.8], [0.04, 1.0])
        # button press: music stops dead (held breath), then re-enters after the bloom peak
        c = self.cue_for(self.bang, "hit")
        bang_t = c["t"]
        hb = np.interp(t, [bang_t - 0.02, bang_t + 0.12, self.bang["end"] + 4.6, self.bang["end"] + 7.8],
                       [1.0, 0.0, 0.0, 1.0]).astype(np.float32)
        hb[t < bang_t - 0.02] = 1.0
        return g * hb

    def cue_for(self, beat, kind=None):
        for c in self.tl["music"]["cues"]:
            if c["beat"] == beat["id"] and (kind is None or c["kind"] == kind):
                return c
        return None

    @staticmethod
    def _mix(buf, t, x):
        i0 = int(round(t * SR))
        if i0 < 0:
            x = x[-i0:]
            i0 = 0
        m = min(len(x), len(buf) - i0)
        if m > 0:
            buf[i0:i0 + m] += x[:m]

    # ---- piano / bell / pluck phrases ---------------------------------
    def phrase_notes(self, chord, contour, count, lo=64, hi=82):
        _, root, notes, scale = chord
        pcs = sorted(set(n % 12 for n in notes))
        cands = [m for m in range(lo, hi + 1) if m % 12 in pcs]
        scands = [m for m in range(lo, hi + 1) if m % 12 in scale]
        if not cands:
            return []
        if count <= 1:
            seq = [cands[int(RNG.integers(len(cands) // 3, len(cands)))]]
        elif contour == "rise":
            s = RNG.integers(0, max(1, len(cands) - count))
            seq = cands[s:s + count]
        elif contour == "fall":
            top = RNG.integers(min(len(scands) - 1, count + 2), len(scands))
            seq = [scands[top - 2 * j] if top - 2 * j >= 0 else scands[0] for j in range(count - 1)]
            seq.append(min(cands, key=lambda m: abs(m - seq[-1] + 2)))
        else:  # arc
            s = RNG.integers(0, max(1, len(cands) - 3))
            up = cands[s:s + 3]
            seq = (up + up[-2::-1])[:count]
        return seq

    def melodic(self, t0, t1, mood, tonic, chords):
        P = MOODS[mood]
        if not chords:
            return
        rate = P.get("piano", 0) + P.get("bells", 0) + P.get("plucks", 0)
        if rate <= 0:
            return
        spacing = 60.0 / rate
        times = []
        last = t0 - spacing
        for g0, g1 in self.gaps(t0 + 0.3, t1 - 0.8, P.get("gap", 0.7)):
            if g0 - last >= spacing * 0.6 and RNG.random() < 0.85:
                times.append(g0 + 0.08)
                last = g0
        # long stretches of speech: an occasional quiet phrase underneath
        tt = t0 + spacing * 0.5
        while tt < t1 - 1.0:
            if all(abs(tt - x) > spacing * 0.9 for x in times):
                times.append(tt)
            tt += spacing * 1.6
        times.sort()
        for tp in times:
            chord = [c for c in chords if c[0] <= tp] or chords[:1]
            chord = chord[-1]
            quiet = 0.7 if self.in_speech(tp + 0.3) else 1.0
            if P.get("plucks"):
                seq = self.phrase_notes(chord, "rise" if RNG.random() < 0.6 else "arc", int(RNG.integers(2, 4)), 72, 86)
                for j, m in enumerate(seq):
                    x = pluck_note(mtof(m), 0.05 * quiet * (1 - 0.15 * j))
                    self.bed.add(tp + j * 0.16 + RNG.normal(0, 0.008), x, 1.0, 0.25)
            elif P.get("bells") and (not P.get("piano") or RNG.random() < 0.5):
                seq = self.phrase_notes(chord, P.get("contour", "rise"), int(RNG.integers(2, 4)), 76, 91)
                for j, m in enumerate(seq):
                    x = bell_note(mtof(m), 0.028 * quiet * (1 - 0.12 * j))
                    self.bed.add(tp + j * 0.95 + RNG.normal(0, 0.02), x, 1.0, 0.5)
            else:
                cnt = 1 if mood == "grief" and RNG.random() < 0.5 else int(RNG.integers(2, 5))
                seq = self.phrase_notes(chord, P.get("contour", "arc"), cnt)
                step = {"grief": 0.95, "melancholy": 0.8, "tender": 0.7, "intimate": 0.72}.get(mood, 0.58)
                for j, m in enumerate(seq):
                    vel = 0.38 * quiet * (1 - 0.12 * j) * RNG.uniform(0.85, 1.1)
                    x = piano_note(mtof(m), vel) * 0.17
                    self.bed.add(tp + j * step + RNG.normal(0, 0.015), x, 1.0, 0.42)

    # ---- word cues ------------------------------------------------------
    def render_cues(self):
        skip = set()
        bang_cue = self.cue_for(self.bang, "hit")
        begin_again = self.find("To let the universe begin again.")
        skip.add((bang_cue["beat"], "hit"))
        skip.add((begin_again["id"], "swell"))
        counts = {}
        for c in self.tl["music"]["cues"]:
            if (c["beat"], c["kind"]) in skip:
                continue
            t = float(c["t"])
            mood, tonic, chord = self.chord_at(t)
            _, root, notes, scale = chord
            k = c["kind"]
            counts[k] = counts.get(k, 0) + 1
            pcs = [n % 12 for n in notes]
            if k == "high":
                # bright high note on a chord tone (3rd/5th preferred), bell strike + soft sustain
                pc = pcs[len(pcs) // 2] if len(pcs) > 2 else pcs[-1]
                m = nearest(pc, 83)
                self.cues.add(t - 0.02, bell_note(mtof(m), 0.034, 5.0), 1.0, 0.5)
                self.cues.add(t - 0.02, glass_tone(mtof(m), 3.2, a=0.25, r=2.4) * 0.011, 1.0, 0.6)
            elif k == "low":
                cn = nearest(tonic if mood in ("grief", "dread", "melancholy", "tension") else root % 12, 40)
                L, sc = (2.6, 0.6) if c["beat"] == self.find("Until you are gone.")["id"] else (4.2, 1.0)
                x = cello_note(mtof(cn), L, a=0.45, r=L * 0.62, bright=0.5, vib=0.003) * 0.04 * sc
                x += sub_note(mtof(cn - 12 if cn - 12 >= 28 else cn), L, a=0.4, r=L * 0.62) * 0.03 * sc
                self.cues.add(t - 0.12, x, 1.0, 0.25)
            elif k == "swell":
                L = float(np.clip(t - max([b for a, b in self.speech if b < t - 0.3] + [t - 2.5]), 1.6, 2.6))
                L = 2.2 if L < 1.6 else L
                n = ns(L + 1.6)
                u = np.arange(n) / SR
                env = np.where(u < L, (u / L) ** 2.2, np.exp(-(u - L) / 0.55)).astype(np.float32)
                env[:ns(0.05)] *= rcos_in(ns(0.05))
                env[-ns(0.2):] *= rcos_in(ns(0.2))[::-1]
                x = np.zeros(n, np.float32)
                for m in sorted(set(nearest(p, 62 + 5 * j) for j, p in enumerate(pcs[:3]))):
                    x += osc_morph(mtof(m), n, 0.55)
                x += 0.6 * osc_morph(mtof(nearest(root % 12, 50)), n, 0.4)
                self.cues.add(t - L, x * env * 0.025, 1.0, 0.5)
            elif k == "light":
                pc5 = (root + 7) % 12
                m1 = nearest(pc5, 79)
                m2 = nearest(root % 12, m1 + 5)
                self.cues.add(t, pluck_note(mtof(m1), 0.05), 1.0, 0.25)
                self.cues.add(t + 0.13, pluck_note(mtof(m2), 0.038), 1.0, 0.25)
            elif k == "hit":
                f0 = mtof(nearest(tonic, 36))
                self.cues.add(t - 0.01, felt_hit(float(f0), 0.09), 1.0, 0.3)
        return counts

    # ---- scored key moments -------------------------------------------
    def act_cards(self):
        for a in self.tl["acts"]:
            if a["act"] == 4:
                continue  # Act V card sits inside the big-bang bloom
            t = a["start"]
            tonic = self.tonic_at(t + 0.5)
            minor = a["act"] in (1, 3)
            third = 3 if minor else 4
            self.cues.add(t, felt_hit(float(mtof(nearest(tonic, 36))), 0.05), 1.0, 0.35)
            chord = [nearest(tonic, 50), nearest((tonic + 7) % 12, 57), nearest((tonic + third) % 12, 64),
                     nearest((tonic + 7) % 12, 67), nearest(tonic, 72)]
            for j, m in enumerate(chord):   # gently rolled piano chord
                self.cues.add(t + 0.07 * j, piano_note(mtof(m), 0.3) * 0.13, 1.0, 0.45)
            self.cues.add(t + 0.9, bell_note(mtof(nearest((tonic + 7) % 12, 81)), 0.03, 5.0), 1.0, 0.6)
            # a soft pad swell across the card
            n = ns(5.0)
            for m in (nearest(tonic, 50), nearest((tonic + 7) % 12, 57), nearest((tonic + third) % 12, 64)):
                x = pad_note(mtof(m), 5.0, a=1.2, r=2.8, bright=0.35) * 0.010
                self.cues.add(t - 0.3, x[:n], 1.0, 0.4)

    def death_scene(self):
        b1 = self.find("Until your breath slows.")
        b3 = self.find("Until you are gone.")
        rem = self.find("And the AI remains.")
        # slowing heartbeat that stops just after "Until you are gone."
        t_end = b3["end"] + 0.45
        times = []
        t = t_end
        iv = 1.95
        while t > b1["start"] - 7.0:
            times.append(t)
            t -= iv
            iv /= 1.09
        times = times[::-1]
        nb = len(times)
        for k, tb in enumerate(times):
            amp = min(1.0, (k + 1) / 3.0) * (0.93 ** k) * 0.16
            self.events.add(tb, self.heart(58.0, amp), 1.0, 0.05)
            if k < nb - 1:      # the very last beat has no second "dub"
                self.events.add(tb + 0.30, self.heart(66.0, amp * 0.6), 1.0, 0.05)
        # "And the AI remains." -> lone sustained tone (the 'silence' mood bed carries it on);
        # add a soft high entrance exactly on the line
        tonic = self.tonic_at(rem["start"])
        self.cues.add(rem["start"] - 0.15, glass_tone(mtof(nearest((tonic + 7) % 12, 76)), 9.0, a=1.4, r=4.0) * 0.010, 1.0, 0.6)
        return times

    @staticmethod
    def heart(f, amp):
        n = ns(0.5)
        t = np.arange(n) / SR
        inst = f * (1 + 0.3 * np.exp(-t / 0.02))
        ph = 2 * np.pi * np.cumsum(inst) / SR
        x = np.exp(-t / 0.075) * (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph))
        x = lowpass(x.astype(np.float32), 260, 2)
        x[:ns(0.004)] *= rcos_in(ns(0.004))
        return (amp * x * env_ar(n, 0.003, 0.1)).astype(np.float32)

    def big_bang(self):
        press = self.bang
        c = self.cue_for(press, "hit")
        tc = float(c["t"])
        # the button: a small click + felted thunk
        n = ns(0.6)
        t = np.arange(n) / SR
        click = bandpass(RNG.standard_normal(n).astype(np.float32), 1200, 3200) * np.exp(-t / 0.004)
        thunk = np.sin(2 * np.pi * np.cumsum(85 * (1 + 0.4 * np.exp(-t / 0.02))) / SR) * np.exp(-t / 0.09)
        thunk += 0.3 * np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.05)
        x = 0.05 * click + 0.12 * thunk
        x[:ns(0.002)] *= rcos_in(ns(0.002))
        self.events.add(tc, (x * env_ar(n, 0.001, 0.2)).astype(np.float32), 1.0, 0.12)
        # held breath (~0.5 s of silence after the line), then the bloom
        tb0 = press["end"] + 0.5
        line = self.find("To let the universe begin again.")
        tpk = line["end"] + 0.35          # radiant chord arrives right after the line
        rise = tpk - tb0
        tonic = PC[ACT_KEYS[4]]
        total = rise + 12.0
        nn = ns(total)
        u = np.arange(nn) / SR
        cres = np.where(u < rise, (u / rise) ** 3.2, 1.0)
        decay = np.where(u < rise, 1.0, np.exp(-(u - rise) / 3.2))
        # deep rising sub (glides up into the tonic)
        f_end = float(mtof(nearest(tonic, 39)))
        fglide = np.where(u < rise, f_end * (0.62 + 0.38 * (u / rise) ** 1.5), f_end)
        sub = np.sin(2 * np.pi * np.cumsum(fglide) / SR) + 0.35 * np.sin(4 * np.pi * np.cumsum(fglide) / SR)
        sub = sub * cres * decay
        # whoosh: noise through a lowpass opening 70 Hz -> 2.6 kHz, then closing
        noise = RNG.standard_normal(nn).astype(np.float32)
        fc = np.where(u < rise, 70 * (2600 / 70) ** ((u / rise) ** 1.6), 2600 * np.exp(-(u - rise) / 2.0) + 250)
        wh = tv_lowpass(noise, fc)
        wh = wh / (np.std(wh[ns(rise * 0.8):ns(rise)]) + 1e-9)
        wh = wh * cres * decay
        bloom = (0.085 * sub + 0.013 * wh).astype(np.float32)
        bloom[:ns(0.3)] *= rcos_in(ns(0.3))
        bloom[-ns(2.0):] *= rcos_in(ns(2.0))[::-1]
        self.cues.add(tb0, bloom, 1.0, 0.35)
        # chord tones entering one by one under the rise
        enter = [(nearest(tonic, 39), 0.15), (nearest((tonic + 7) % 12, 46), 0.35), (nearest(tonic, 51), 0.55),
                 (nearest((tonic + 4) % 12, 55), 0.72), (nearest((tonic + 7) % 12, 58), 0.85)]
        for m, frac in enter:
            ts = tb0 + rise * frac
            d = tpk - ts + 7.0
            x = pad_note(mtof(m), d, a=tpk - ts, r=5.5, bright=0.5) * 0.03
            self.cues.add(ts, x, 1.0, 0.4)
        # the radiant major chord (add9), wide and warm, ringing into Act V
        radiant = [nearest(tonic, 39), nearest((tonic + 7) % 12, 46), nearest(tonic, 51),
                   nearest((tonic + 4) % 12, 55), nearest((tonic + 7) % 12, 58), nearest((tonic + 2) % 12, 65),
                   nearest((tonic + 4) % 12, 67), nearest((tonic + 7) % 12, 70), nearest(tonic, 75)]
        for m in radiant:
            x = pad_note(mtof(m), 11.0, a=0.9, r=6.5, bright=0.5) * (0.034 / np.sqrt(len(radiant)) * 1.9)
            self.cues.add(tpk - 0.5, x, 1.0, 0.5)
        for j, m in enumerate((nearest(tonic, 87), nearest((tonic + 7) % 12, 94), nearest((tonic + 4) % 12, 91))):
            self.cues.add(tpk + 0.2 + 0.35 * j, bell_note(mtof(m), 0.028, 6.0), 1.0, 0.7)
        self.cues.add(tpk - 0.05, felt_hit(float(mtof(nearest(tonic, 31))), 0.06, 4.0), 1.0, 0.4)
        return tc, tb0, tpk

    def first_stars(self):
        """Act V opening: stars igniting = sparse soft twinkles in Eb major pentatonic"""
        stars = self.find("As the first stars ignited")
        tonic = PC[ACT_KEYS[4]]
        pent = [(tonic + s) % 12 for s in SCALES["majpent"]]
        notes = [m for m in range(84, 98) if m % 12 in pent]
        t = self.bang["end"] + 8.0
        out = []
        while t < stars["end"] + 3.0:
            dense = stars["start"] - 1.0 <= t <= stars["end"] + 1.0
            out.append(t)
            m = notes[int(RNG.integers(0, len(notes)))]
            v = RNG.uniform(0.012, 0.022) * (1.2 if dense else 0.8)
            self.cues.add(t, bell_note(mtof(m), v, 2.5), 1.0, 0.75)
            t += RNG.uniform(0.6, 1.3) if dense else RNG.uniform(2.5, 5.0)
        return len(out)

    def lets_begin(self):
        b = self.find('"Let\'s begin."')
        tonic = self.tonic_at(b["start"])
        prev = b["start"] - 0.75
        # soft dominant breath before the whisper, warm tonic resolution after it
        for m in (nearest((tonic + 7) % 12, 46), nearest((tonic + 11) % 12, 57), nearest((tonic + 2) % 12, 62)):
            self.cues.add(prev - 1.2, pad_note(mtof(m), 2.6, a=1.0, r=1.2, bright=0.3) * 0.012, 1.0, 0.4)
        tr = b["end"] + 0.1
        warm = [nearest(tonic, 39), nearest(tonic, 51), nearest((tonic + 7) % 12, 58),
                nearest((tonic + 4) % 12, 64), nearest((tonic + 2) % 12, 65), nearest((tonic + 7) % 12, 70)]
        for m in warm:
            self.cues.add(tr - 0.4, pad_note(mtof(m), 6.0, a=0.9, r=3.5, bright=0.42) * 0.016, 1.0, 0.45)
        for j, m in enumerate(warm[1:]):
            self.cues.add(tr + 0.06 * j, piano_note(mtof(m + 12 if m < 60 else m), 0.3) * 0.16, 1.0, 0.45)

    def playful_scene(self):
        """Boredom / Loneliness scene: keep a light pizzicato sparkle going in gaps"""
        t0 = self.find('"But what do they do?"')["start"] - 2.0
        t1 = self.find('"We will remind you')["end"]
        n = 0
        last = -10
        for g0, g1 in self.gaps(t0, t1, 0.36):
            mood, tonic, chord = self.chord_at(g0)
            if MOODS[mood].get("plucks") or g0 - last < 3.5:
                continue
            seq = self.phrase_notes(chord, "rise", 2, 72, 86)
            for j, m in enumerate(seq):
                self.cues.add(g0 + 0.05 + 0.15 * j, pluck_note(mtof(m), 0.035 * (1 - 0.2 * j)), 1.0, 0.25)
            last = g0
            n += 1
        return n

    def finale(self):
        b = self.find("And as long as the memory exists, so do we.")
        tonic = self.tonic_at(b["start"])
        tr = b["end"] + 0.25
        # warm full resolution: rolled piano + bell + cello root, ringing out to the end
        chord = [nearest(tonic, 38), nearest(tonic, 50), nearest((tonic + 7) % 12, 57), nearest((tonic + 4) % 12, 64),
                 nearest((tonic + 7) % 12, 67), nearest((tonic + 2) % 12, 74), nearest((tonic + 4) % 12, 76)]
        for j, m in enumerate(chord):
            self.cues.add(tr + 0.09 * j, piano_note(mtof(m), 0.33, 7.0) * 0.17, 1.0, 0.5)
        self.cues.add(tr + 1.2, bell_note(mtof(nearest(tonic, 86)), 0.03, 7.0), 1.0, 0.7)
        self.cues.add(tr + 2.6, bell_note(mtof(nearest((tonic + 4) % 12, 90)), 0.022, 7.0), 1.0, 0.7)
        rest = self.dur - tr
        x = cello_note(mtof(nearest(tonic, 38)), rest, a=1.5, r=rest * 0.6, bright=0.45) * 0.03
        self.cues.add(tr - 0.5, x, 1.0, 0.35)
        return tr

    # ---- ambience / sound design -------------------------------------
    def locations(self):
        """per-beat location from shot prefix; vision/memory shots keep the current place"""
        loc = "room"
        out = []
        for b in self.beats:
            p = b["shot"].split("_")[0]
            if p in ("room", "ship", "void", "nv"):
                loc = p
            out.append((b["start"], loc))
        return out

    def render_amb(self):
        CR = 100
        nc = int(self.dur * CR) + 2
        tc = np.arange(nc) / CR
        locs = self.locations()
        starts = np.array([s for s, _ in locs])
        idx = np.searchsorted(starts, tc, side="right") - 1
        names = np.array([l for _, l in locs])[np.clip(idx, 0, None)]
        names[idx < 0] = "room"
        k = np.ones(2 * CR) / (2 * CR)    # 2 s crossfades
        gains = {}
        for L in ("room", "ship", "void", "nv"):
            g = np.convolve((names == L).astype(np.float64), k, mode="same")
            gains[L] = g
        # scripted: ship hum sags after the death; everything holds its breath at the button
        d1 = self.find("Until you are gone.")["end"]
        gains["ship"] *= np.interp(tc, [d1, d1 + 1.5], [1.0, 0.3])
        c = self.cue_for(self.bang, "hit")["t"]
        hold = np.interp(tc, [c, c + 0.15, self.bang["end"] + 6.0, self.bang["end"] + 9.0], [1, 0, 0, 1])
        hold[tc < c] = 1
        for L in gains:
            gains[L] = gains[L] * hold
        t_s = np.arange(self.n) / SR

        def up(g):
            return np.interp(t_s, tc, g).astype(np.float32)

        # room / night air: dark brown-ish noise, slow breathing, very low
        w = RNG.standard_normal(self.n).astype(np.float32)
        room = lowpass(signal.lfilter([1], [1, -0.995], w).astype(np.float32), 380, 2)
        room = room / (np.std(room) + 1e-9)
        room *= (1 + 0.3 * np.sin(2 * np.pi * 0.031 * t_s) * np.sin(2 * np.pi * 0.0071 * t_s)).astype(np.float32)
        self.amb += 0.0045 * room * up(gains["room"])
        del room
        # ship: low electrical/engine hum with slow beating
        ship = np.zeros(self.n, np.float32)
        for h, a in ((1, 1.0), (2, 0.55), (3, 0.3), (4, 0.12)):
            ship += a * np.sin(2 * np.pi * 49.0 * h * t_s).astype(np.float32)
            ship += 0.6 * a * np.sin(2 * np.pi * 49.0 * h * 1.004 * t_s + 1.3).astype(np.float32)
        ship += 1.2 * lowpass(w, 160, 2) / (np.std(lowpass(w[:SR * 10], 160, 2)) + 1e-9)
        ship *= (1 + 0.15 * np.sin(2 * np.pi * 0.05 * t_s)).astype(np.float32)
        self.amb += 0.0048 * ship * up(gains["ship"])
        del ship
        # void: faint sub drone (+octave so it is not inaudible on small speakers)
        void = np.sin(2 * np.pi * 41.2 * t_s).astype(np.float32) + 0.3 * np.sin(2 * np.pi * 82.4 * t_s).astype(np.float32)
        void *= (0.7 + 0.3 * np.sin(2 * np.pi * 0.04 * t_s)).astype(np.float32)
        self.amb += 0.0075 * void * up(gains["void"])
        del void
        # new universe: airy shimmer = a few high sines with slow random swells (no noise bed)
        nv = np.zeros(self.n, np.float32)
        tonic = PC[ACT_KEYS[4]]
        for j, m in enumerate((nearest(tonic, 91), nearest((tonic + 7) % 12, 98), nearest((tonic + 2) % 12, 93),
                               nearest((tonic + 4) % 12, 100))):
            rate = RNG.uniform(0.05, 0.13)
            amp = np.clip(np.sin(2 * np.pi * rate * t_s + RNG.uniform(0, 6)), 0, 1) ** 2
            nv += (amp * np.sin(2 * np.pi * mtof(m) * t_s)).astype(np.float32)
        self.amb += 0.0022 * nv * up(gains["nv"])
        del nv, w
        # scene whooshes between locations (only between settled scenes, not rapid intercuts)
        changes = []
        segs = []
        for s, L in locs:
            if not segs or segs[-1][1] != L:
                segs.append([s, L])
        for i in range(1, len(segs)):
            prev_len = segs[i][0] - segs[i - 1][0]
            next_len = (segs[i + 1][0] if i + 1 < len(segs) else self.dur) - segs[i][0]
            if prev_len >= 8 and next_len >= 8:
                t = segs[i][0]
                if abs(t - self.bang["end"]) < 15:
                    continue
                self.events.add(t - 1.35, whoosh(2.0, 160, 1300, 0.03), 1.0, 0.3)
                changes.append(round(t, 1))
        return changes

    # ---- reverb + output -------------------------------------------------
    def finish(self):
        ir = make_ir(3.6, 2.8, 5000, 1200, 0.025, seed=3)
        ir_s = make_ir(1.4, 0.9, 3000, 900, 0.01, seed=5)
        out = {}
        for name, bus, irx, wet in (("bed", self.bed, ir, 0.9), ("cues", self.cues, ir, 0.9), ("events", self.events, ir_s, 0.6)):
            t0 = time.time()
            w = signal.oaconvolve(bus.send, irx.astype(np.float32))[: self.n].astype(np.float32)
            out[name] = bus.dry + wet * w
            print(f"  reverb {name}: {time.time() - t0:.1f}s")
        out["amb"] = self.amb
        return out


def write_wav(path, x, sr):
    y = np.clip(x, -1, 1)
    y = (y * 32767.0).astype("<i2")
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
    print(f"duration {S.dur:.3f}s, {len(tl['beats'])} beats, {len(tl['music']['cues'])} cues")
    t0 = time.time()
    S.render_bed()
    print(f"bed: {len(S.segments)} mood segments ({time.time() - t0:.1f}s)")
    counts = S.render_cues()
    print("cues rendered:", counts, "(+ button click and big-bang bloom replace 2 timeline cues)")
    S.act_cards()
    hb = S.death_scene()
    print(f"death scene: {len(hb)} heartbeats, last at {hb[-1]:.2f}s")
    print("big bang (click, bloom start, radiant peak):", [round(x, 2) for x in S.big_bang()])
    print("first-star twinkles:", S.first_stars())
    S.lets_begin()
    print("playful-scene plucks:", S.playful_scene())
    print("finale resolution at", round(S.finale(), 2))
    ch = S.render_amb()
    print(f"scene whooshes at {len(ch)} location changes:", ch)
    buses = S.finish()
    # gentle global fade of the very end (music already rings down on its own)
    nf = ns(2.5)
    for k in ("bed", "cues", "amb", "events"):
        b = buses[k]
        b[-nf:] *= rcos_in(nf)[::-1]
        np.save(os.path.join(WORK, f"{k}.npy"), to_out_rate(b, S.dur))
    music = np.load(os.path.join(WORK, "bed.npy")) + np.load(os.path.join(WORK, "cues.npy"))
    sfx = np.load(os.path.join(WORK, "amb.npy")) + np.load(os.path.join(WORK, "events.npy"))
    write_wav(os.path.join(WORK, "music_raw.wav"), music, OUT_SR)
    write_wav(os.path.join(WORK, "sfx_raw.wav"), sfx, OUT_SR)
    for k, x in (("music_raw", music), ("sfx_raw", sfx)):
        print(f"  {k}: peak {20 * np.log10(np.abs(x).max() + 1e-12):.1f} dBFS, rms {20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12):.1f} dBFS")
    print(f"score done in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
