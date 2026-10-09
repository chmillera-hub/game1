#!/usr/bin/env python3
"""Music for "If You Have Time": composes AND renders every cue of BIBLE section 5.

    python3 audio/music.py                     # every cue in MUSIC_CUES
    python3 audio/music.py symphony alt_kazoo  # only the named cues (envelopes.json is merged)
    python3 audio/music.py --no-cache ...      # force fluidsynth re-renders

Outputs (build/music/):
    <cue>.wav          48 kHz stereo float32, EXACTLY MUSIC_CUES[cue] seconds, peak <= -1 dBFS
    <cue>.mid          the composed score (one track per part, absolute-time, 1 tick = 1 ms)
    score_<cue>.txt    bar-by-bar score dump: chord, every part's notes (beat, pitch, length,
                       velocity), dynamics, melody-vs-chord analysis, range + parallel checks
    envelopes.json     {cue: {"rms":  [per-frame 0..1 at 24 fps],
                              "low":  [... <200 Hz band], "high": [... >3 kHz band],
                              "onsets":    [local s, sorted] melody/celesta/piano note onsets,
                              "beats":     [local s] every beat of the cue's tempo map,
                              "downbeats": [local s] every bar line}}
    build/tests/music/<cue>.png  spectrogram + envelope + short-term loudness, with landmarks

Envelope mapping: rms/low/high are frame RMS in dB relative to the cue's loudest frame
(per band), mapped linearly from -42 dB -> 0 to 0 dB -> 1, lightly smoothed
(fast attack, ~120 ms release) so visuals can "breathe" with the music without flicker.

How it works
    * Every cue is a `Cue`: a tempo map (beat -> seconds with rubato, anchored so the symphony's
      landmarks land exactly on 7.5 / 35 / 49.4 / 50.5 / 66 s), bar lines, a chord timeline and
      a list of `Part`s holding `Note`s (beats) + dynamics keyframes.
    * SoundFont parts are written to MIDI (absolute ms timing, humanized +-8 ms, legato overlaps,
      CC2 dynamics for MuseScore "Expr." presets / CC11 for the rest, CC64 pedal) and rendered one
      stem at a time with the fluidsynth CLI (<= 2 processes).
    * Synth parts (kazoo, chiptune, theremin, lo-fi drums/bass, suspended cymbal) are numpy.
    * Stems are panned, summed, sent to a synthesized stereo convolution hall, bus-compressed,
      loudness-normalized (pyloudnorm-compatible BS.1770 K-weighting), peak-limited and faded.
"""
from __future__ import annotations

import hashlib
import itertools
import zlib
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import mido
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import BUILD, FPS, MUSIC_DIR, MUSIC_ENV, SOUNDFONT, SOUNDFONT_ALT, SR  # noqa: E402
from script_data import MUSIC_CUES  # noqa: E402

TEST_DIR = BUILD / "tests" / "music"
CACHE_DIR = MUSIC_DIR / ".cache"
MAX_JOBS = 2                 # machine is shared: never more than 2 fluidsynth processes
FS_GAIN = 0.35
RENDER_VERSION = "v3"        # bump to invalidate the fluidsynth stem cache
USE_CACHE = True

# =========================================================================== pitch & chords

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]


def P(name: str) -> int:
    """'F#5' -> 78 (MIDI). Accepts #, b, ## and bb."""
    m = re.fullmatch(r"([A-G])([#b]{0,2})(-?\d)", name.strip())
    if not m:
        raise ValueError(f"bad pitch {name!r}")
    pc = _PC[m.group(1)] + m.group(2).count("#") - m.group(2).count("b")
    return pc + 12 * (int(m.group(3)) + 1)


def pname(m: int) -> str:
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def pc_of(name: str) -> int:
    return (_PC[name[0]] + name[1:].count("#") - name[1:].count("b")) % 12


QUAL = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
        "sus4": (0, 5, 7), "7sus4": (0, 5, 7, 10), "sus2": (0, 2, 7), "add9": (0, 2, 4, 7),
        "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "maj9": (0, 2, 4, 7, 11), "m9": (0, 2, 3, 7, 10),
        "9": (0, 2, 4, 7, 10), "dim": (0, 3, 6), "5": (0, 7), "(no5)": (0, 4)}


@dataclass(frozen=True)
class Chord:
    sym: str
    root: int
    ivs: tuple
    bass: int

    @property
    def pcs(self) -> set:
        return {(self.root + i) % 12 for i in self.ivs}

    def required(self, n: int) -> set:
        """Pitch classes a voicing of n notes must contain (3rd, 7th, 6th, sus tone, root if room)."""
        has7 = any(i in (10, 11) for i in self.ivs)
        req = set()
        for i in self.ivs:
            if i in (0, 7) or (i == 2 and has7 and n < 5):
                continue
            req.add((self.root + i) % 12)
        if len(req) < n:
            req.add(self.root)
        return req

    @property
    def third(self):
        for i in self.ivs:
            if i in (3, 4):
                return (self.root + i) % 12
        return None

    @property
    def seventh(self):
        for i in self.ivs:
            if i in (10, 11):
                return (self.root + i) % 12
        return None


def chord(sym: str) -> Chord | None:
    if sym in ("N.C.", "NC", "-"):
        return None
    m = re.fullmatch(r"([A-G][#b]?)([^/]*)(?:/([A-G][#b]?))?", sym)
    if not m or m.group(2) not in QUAL:
        raise ValueError(f"bad chord {sym!r}")
    root = pc_of(m.group(1))
    return Chord(sym, root, QUAL[m.group(2)], pc_of(m.group(3)) if m.group(3) else root)


# =========================================================================== notes, parts, cues

DUR = {"w": 4.0, "h.": 3.0, "h": 2.0, "q.": 1.5, "q": 1.0, "e.": 0.75, "e": 0.5, "s": 0.25,
       "t": 1 / 3, "x": 0.125}


@dataclass
class Note:
    beat: float
    dur: float
    pitch: int
    vel: int = 80
    tag: str = ""            # "mel" -> exported as a visual onset / used as the melody line


@dataclass
class Inst:
    bank: int
    prog: int
    lo: int                  # idiomatic sounding range (MIDI) used by the range check
    hi: int
    expr: bool = False       # MuseScore "Expr." preset: dynamics + timbre on CC2
    label: str = ""


INST = {
    # strings (MuseScore_General sectional presets)
    "vln1":      Inst(21, 48, 55, 100, True, "Violins I (fast, expr)"),
    "vln_slow":  Inst(21, 49, 55, 100, True, "Violins (slow, expr)"),
    "vln2":      Inst(26, 49, 55, 96, True, "Violins II (slow, expr)"),
    "vln2_fast": Inst(26, 48, 55, 96, True, "Violins II (fast, expr)"),
    "vln2_trem": Inst(26, 44, 55, 96, True, "Violins II tremolo (expr)"),
    "vla":       Inst(31, 49, 48, 88, True, "Violas (slow, expr)"),
    "vla_trem":  Inst(31, 44, 48, 88, True, "Violas tremolo (expr)"),
    "vc":        Inst(41, 48, 36, 81, True, "Celli (fast, expr)"),
    "vc_slow":   Inst(41, 49, 36, 81, True, "Celli (slow, expr)"),
    "vc_trem":   Inst(41, 44, 36, 81, True, "Celli tremolo (expr)"),
    "cb":        Inst(51, 49, 28, 67, True, "Contrabasses (slow, expr)"),
    "cb_trem":   Inst(51, 44, 28, 67, True, "Contrabasses tremolo (expr)"),
    # winds / brass / voices
    "horns":     Inst(17, 60, 35, 77, True, "French horns (expr)"),
    "brass":     Inst(17, 61, 40, 82, True, "Brass section (expr)"),
    "trombone":  Inst(17, 57, 40, 72, True, "Trombones (expr)"),
    "choir":     Inst(17, 52, 40, 81, True, "Choir aahs (expr)"),
    "flute":     Inst(0, 73, 60, 96, False, "Flute"),
    # keys / plucked / percussion
    "piano":     Inst(0, 0, 21, 108, False, "Grand piano"),
    "mellow":    Inst(8, 0, 21, 108, False, "Mellow grand piano"),
    "rhodes":    Inst(0, 4, 28, 100, False, "Tine electric piano"),
    "celesta":   Inst(0, 8, 60, 108, False, "Celesta"),
    "glock":     Inst(0, 9, 79, 108, False, "Glockenspiel"),
    "musicbox":  Inst(0, 10, 60, 108, False, "Music box"),
    "harp":      Inst(0, 46, 23, 103, False, "Harp"),
    "ukulele":   Inst(8, 24, 60, 81, False, "Ukulele"),
    "timpani":   Inst(0, 47, 38, 57, False, "Timpani"),
    # pads
    "warm_pad":  Inst(0, 89, 36, 96, False, "Warm pad"),
    "halo_pad":  Inst(0, 94, 36, 96, False, "Halo pad"),
}
SYNTH_RANGES = {"shimmer": (60, 100), "kazoo": (55, 84), "chip_lead": (57, 96), "chip_echo": (57, 96), "chip_arp": (48, 84),
                "chip_tri": (28, 60), "theremin": (48, 84), "sub_bass": (28, 52)}


@dataclass
class Part:
    name: str
    inst: str                         # INST key, or a synth kind for synth parts
    notes: list = field(default_factory=list)
    dyn: list = field(default_factory=list)   # [(beat, 0..127)] -> CC2 (expr) / CC11 (others)
    gain_db: float = 0.0
    pan: float = 0.0                  # -1 left .. +1 right (balance on the stereo stem)
    send: float = 0.25                # reverb send
    humanize: float = 0.008           # max timing jitter (s)
    legato: float = 0.0               # overlap (s) added when a note runs into the next
    pedal: list = field(default_factory=list)  # [(down_beat, up_beat)]
    synth: object = None              # callable(part, cue, n) -> (n, 2) for numpy instruments
    eq: object = None                 # callable(stereo) -> stereo, per-stem tone shaping
    lazy: float = 0.0                 # constant timing offset in seconds (laid-back feel)
    vol: list = field(default_factory=list)   # [(beat, dB)] fader automation applied to the stem
    opts: dict = field(default_factory=dict)

    def add(self, notes):
        self.notes.extend(notes)
        return self


class TempoMap:
    """beat -> seconds. Anchors pin exact (beat, sec) pairs; between anchors the relative beat
    lengths follow weight(beat) (rubato: >1 = slower), normalized so every anchor lands exactly."""

    def __init__(self, anchors, weight=None, res=96):
        if len(anchors) < 2:
            raise ValueError("need >= 2 anchors")
        weight = weight or (lambda b: 1.0)
        bs, ss = [], []
        for (b0, s0), (b1, s1) in zip(anchors[:-1], anchors[1:]):
            k = max(2, int(round((b1 - b0) * res)))
            grid = np.linspace(b0, b1, k + 1)
            mid = (grid[:-1] + grid[1:]) / 2
            w = np.array([max(0.05, weight(x)) for x in mid])
            cum = np.concatenate([[0.0], np.cumsum(w)])
            seg = s0 + (s1 - s0) * cum / cum[-1]
            if bs:
                grid, seg = grid[1:], seg[1:]
            bs.extend(grid)
            ss.extend(seg)
        self.b = np.array(bs)
        self.s = np.array(ss)
        self.d0 = (self.s[1] - self.s[0]) / (self.b[1] - self.b[0])
        self.d1 = (self.s[-1] - self.s[-2]) / (self.b[-1] - self.b[-2])
        self.anchors = anchors

    def sec(self, beat: float) -> float:
        if beat < self.b[0]:
            return float(self.s[0] + (beat - self.b[0]) * self.d0)
        if beat > self.b[-1]:
            return float(self.s[-1] + (beat - self.b[-1]) * self.d1)
        return float(np.interp(beat, self.b, self.s))

    def beat(self, sec: float) -> float:
        if sec < self.s[0]:
            return float(self.b[0] + (sec - self.s[0]) / self.d0)
        if sec > self.s[-1]:
            return float(self.b[-1] + (sec - self.s[-1]) / self.d1)
        return float(np.interp(sec, self.s, self.b))

    def bpm(self, beat: float) -> float:
        return 60.0 / max(1e-6, (self.sec(beat + 0.05) - self.sec(beat - 0.05)) / 0.1)

    @staticmethod
    def const(bpm: float, start: float = 0.0, beat0: float = 0.0):
        return TempoMap([(beat0, start), (beat0 + 1000, start + 1000 * 60.0 / bpm)])


@dataclass
class Cue:
    name: str
    tmap: TempoMap
    bars: list                        # beat of every bar line (first..last)
    chords: list                      # [(b0, b1, symbol)]
    parts: list
    rt60: float = 2.0
    wet: float = 0.3
    predelay: float = 0.02
    target_lufs: float = -16.0
    st_target: float | None = None    # if set: normalize so max short-term loudness == this
    fade_in: float = 0.004
    fade_out: float = 0.25
    gates: list = field(default_factory=list)   # [(t0, t1, {part names kept open})]
    wet_duck: list = field(default_factory=list)  # [(t0, t1, gain, ramp_s)] extra decay on the reverb return
    master_vol: list = field(default_factory=list)  # [(beat, dB)] whole-cue fader (pre-reverb)
    post: object = None               # callable(stereo, cue) -> stereo, after reverb
    comp: tuple = (-22.0, 1.6, 25.0, 300.0)       # threshold dB (rel. to peak RMS), ratio, att ms, rel ms
    landmarks: list = field(default_factory=list)  # [(sec, label)]
    top_parts: tuple = ()
    bass_parts: tuple = ()
    notes_txt: str = ""

    @property
    def length(self) -> float:
        return MUSIC_CUES[self.name]

    def part(self, name) -> Part:
        for p in self.parts:
            if p.name == name:
                return p
        raise KeyError(name)


# --------------------------------------------------------------------------- notation helpers


def seq(spec: str, start: float = 0.0, vel=80, tag: str = "", bar: float | None = None, vels=None) -> list:
    """Parse 'A4:q D5:q F#5:h | E5:q ...' into Notes starting at beat `start`.

    token  = PITCH:DUR[@VEL][~]   PITCH = 'F#5' | 'r' (rest) | '(D4,F#4,A4)' (chord)
    DUR    = w h. h q. q e. e s t x  or a number of beats.   '~' ties into the next note.
    `|` marks bar lines; with `bar` set, every complete bar is checked to sum to `bar` beats.
    `vels` (list) overrides velocities note-by-note (rests skipped)."""
    notes, b, acc, ties = [], start, 0.0, {}
    vi = 0
    for tok in spec.replace("|", " | ").split():
        if tok == "|":
            if bar is not None and abs(acc - bar) > 1e-6:
                raise ValueError(f"bar sums to {acc} not {bar} in {spec!r}")
            acc = 0.0
            continue
        p, rest = tok.split(":")
        tie = rest.endswith("~")
        rest = rest.rstrip("~")
        if "@" in rest:
            dur_s, v = rest.split("@")
            v = int(v)
        else:
            dur_s, v = rest, vel
        d = DUR[dur_s] if dur_s in DUR else float(dur_s)
        if p != "r":
            if vels is not None and vi < len(vels):
                v = vels[vi]
            vi += 1
            new_ties = {}
            for ps in p.strip("()").split(","):
                m = P(ps)
                prev = ties.get(m)
                if prev is not None and abs(prev.beat + prev.dur - b) < 1e-6:
                    prev.dur += d
                    nt = prev
                else:
                    nt = Note(b, d, m, int(v), tag)
                    notes.append(nt)
                if tie:
                    new_ties[m] = nt
            ties = new_ties
        else:
            ties = {}
        b += d
        acc += d
    if bar is not None and acc > 1e-6 and abs(acc - bar) > 1e-6:
        raise ValueError(f"last bar sums to {acc} not {bar} in {spec!r}")
    return notes


def ctl(spec: str, start: float = 0.0) -> list:
    """'D:4 Bm:4 Gm:2 A7:2' -> [(b0, b1, sym), ...]"""
    out, b = [], start
    for tok in spec.split():
        sym, d = tok.rsplit(":", 1)
        out.append((b, b + float(d), sym))
        b += float(d)
    return out


def transpose(notes, semis: int, tag=None) -> list:
    return [Note(n.beat, n.dur, n.pitch + semis, n.vel, n.tag if tag is None else tag) for n in notes]








def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def bump(b, c, w):
    return math.exp(-((b - c) / w) ** 2)


def rit(b, b0, b1):
    """0 before b0, smooth rise to 1 at b1, 0 again from b1 (use with anchors at b1)."""
    return 0.0 if (b < b0 or b >= b1) else smoothstep((b - b0) / (b1 - b0))


def dyn_at(keys, b):
    if not keys:
        return 90.0
    if b <= keys[0][0]:
        return float(keys[0][1])
    for (b0, v0), (b1, v1) in zip(keys, keys[1:]):
        if b < b1:
            x = (b - b0) / (b1 - b0) if b1 > b0 else 1.0
            x = 0.5 - 0.5 * math.cos(math.pi * x)
            return v0 + (v1 - v0) * x
    return float(keys[-1][1])


def roll(pitch, b0, b1, tmap, rate=11.0, v0=50, v1=100, tag=""):
    """Timpani-style roll: strokes at `rate` per second from beat b0 to b1, velocity v0 -> v1."""
    t0, t1 = tmap.sec(b0), tmap.sec(b1)
    k = max(2, int((t1 - t0) * rate))
    out = []
    for i in range(k):
        ts = t0 + (t1 - t0) * i / k
        bb = tmap.beat(ts)
        nb = tmap.beat(ts + 1.0 / rate)
        x = i / (k - 1)
        out.append(Note(bb, nb - bb, pitch, int(v0 + (v1 - v0) * x + (3 if i % 2 else 0)), tag))
    return out


def gliss(pcs, p0, p1, b0, beats, v0, v1):
    """Harp glissando over the scale pcs from pitch p0 up to p1 in `beats` beats."""
    ps = [p for p in range(p0, p1 + 1) if p % 12 in pcs]
    n = len(ps)
    return [Note(b0 + beats * i / n, max(0.25, beats * 1.5), p, int(v0 + (v1 - v0) * i / max(1, n - 1)))
            for i, p in enumerate(ps)]


def harp_arp(chords_, base_pitch_lo=50, step=0.5, pattern=None, v=(46, 60), low=True, low_vel=None):
    """Rolling harp arpeggios: per chord, bass note then open chord tones rising (1-5-8-10-12-15...).
    base_pitch_lo: lowest allowed pitch for the bass of the figure."""
    out = []
    for (b0, b1, sym) in chords_:
        ch = chord(sym)
        if ch is None:
            continue
        bass = ch.bass
        bp = base_pitch_lo + ((bass - base_pitch_lo) % 12)
        tones = sorted({(ch.root + i) % 12 for i in ch.ivs if i != 2})
        stack = [bp]
        fifth_above = [p for p in range(bp + 5, bp + 12) if p % 12 in tones]
        if fifth_above:
            stack.append(fifth_above[-1] if len(fifth_above) > 1 else fifth_above[0])
        p = bp + 12
        while len(stack) < 12:
            if p % 12 in tones:
                stack.append(p)
            p += 1
        nsteps = int(round((b1 - b0) / step))
        pat = pattern or list(range(nsteps))
        for i in range(nsteps):
            idx = pat[i % len(pat)]
            vel = v[0] + (v[1] - v[0]) * (idx / max(1, max(pat)))
            out.append(Note(b0 + i * step, step * 3.0, stack[idx], int(vel)))
        if low and bp - 12 >= INST["harp"].lo:
            out.append(Note(b0, (b1 - b0), bp - 12, int(low_vel or v[1])))
    return out


# --------------------------------------------------------------------------- voicing


def _parallels(prev, cur, bass_prev=None, bass_cur=None):
    """Count parallel perfect 5ths/8ves between voice pairs (and each voice vs the bass)."""
    cnt = 0
    vp = list(prev) + ([bass_prev] if bass_prev is not None else [])
    vc = list(cur) + ([bass_cur] if bass_cur is not None else [])
    if len(vp) != len(vc):
        return 0
    for i in range(len(vp)):
        for j in range(i + 1, len(vp)):
            a0, b0, a1, b1 = vp[i], vp[j], vc[i], vc[j]
            if a0 == a1 or b0 == b1:
                continue
            i0, i1 = (b0 - a0) % 12, (b1 - a1) % 12
            if i0 == i1 and i0 in (0, 7) and (a1 - a0) * (b1 - b0) > 0:
                cnt += 1
    return cnt


def voice_chords(chords_, n, lo, hi, bass=None, prev=None, top_max=None, top_min=None, force_top=None,
                 spacing=12):
    """Smooth voice-leading for a chord timeline: for each chord pick the n-note voicing in [lo, hi]
    that contains the required tones, avoids doubled leading tones/7ths, avoids parallel 5ths/8ves
    (among the voices and against `bass`), and moves least from the previous voicing.
    bass: list of bass MIDI pitches per chord (or None). top_max/top_min/force_top: per-chord
    values (list) or scalars."""
    def per(v, i):
        return v[i] if isinstance(v, (list, tuple)) else v

    out = []
    bass_prev = None
    for ci, (b0, b1, sym) in enumerate(chords_):
        ch = chord(sym)
        if ch is None:
            out.append(None)
            continue
        bc = bass[ci] if bass else None
        tmax, tmin, ftop = per(top_max, ci), per(top_min, ci), per(force_top, ci)
        cands = [p for p in range(lo, hi + 1) if p % 12 in ch.pcs]
        req = ch.required(n)
        best = None
        for relax in (0, 1):
            for combo in itertools.combinations(cands, n):
                if ftop is not None and combo[-1] != ftop:
                    continue
                if tmax is not None and combo[-1] > tmax:
                    continue
                if tmin is not None and combo[-1] < tmin:
                    continue
                pcs = [p % 12 for p in combo]
                need = req if relax == 0 else (req - {ch.root})
                if not need <= set(pcs):
                    continue
                if any(combo[k + 1] - combo[k] > spacing for k in range(1, n - 1)):
                    continue
                if n >= 2 and combo[1] - combo[0] > spacing + 7:
                    continue
                cost = 0.0
                cnt = Counter(pcs)
                if ch.third is not None and cnt[ch.third] > 1:
                    cost += 5.0 if 4 in ch.ivs else 1.5
                    if ch.seventh is not None and ch.ivs[1] == 4:
                        cost += 12.0          # doubled leading tone of a dominant 7th
                if ch.seventh is not None and cnt[ch.seventh] > 1:
                    cost += 12.0
                if len(cnt) < min(len(ch.pcs), n):
                    cost += 1.0
                for k in range(n - 1):
                    if combo[k + 1] - combo[k] < 5 and combo[k] < 52:
                        cost += 6.0           # muddy close interval in the low register
                if bc is not None and combo[0] - bc < 3:
                    cost += 4.0
                if prev is not None and len(prev) == n:
                    cost += sum(abs(a - b) for a, b in zip(combo, prev))
                    cost += 40.0 * _parallels(prev, combo, bass_prev, bc)
                elif prev is not None:
                    cost += abs(sum(combo) / n - sum(prev) / len(prev)) * n
                else:
                    cost += abs(sum(combo) / n - (lo + hi) / 2) * 0.6
                if best is None or cost < best[0]:
                    best = (cost, combo)
            if best is not None:
                break
        if best is None:
            raise ValueError(f"no voicing for {sym} n={n} in [{lo},{hi}] top<={tmax}")
        out.append(best[1])
        prev = best[1]
        bass_prev = bc
    return out


def pad_notes(chords_, voicings, assign: dict, vel=70, tie=True, tail=0.0) -> dict:
    """Turn voicings into sustained notes; common tones are tied across chord changes.
    assign: {part_name: [voice indices from the bottom]}."""
    out = {k: [] for k in assign}
    open_ = {}
    for (b0, b1, sym), v in zip(chords_, voicings):
        new_open = {}
        if v is None:
            open_ = {}
            continue
        for part, idxs in assign.items():
            for i in idxs:
                if i >= len(v):
                    continue
                p = v[i]
                prev = open_.get((part, p))
                if tie and prev is not None and abs(prev.beat + prev.dur - b0) < 1e-6:
                    prev.dur = b1 - prev.beat
                    new_open[(part, p)] = prev
                else:
                    nt = Note(b0, b1 - b0, p, vel)
                    out[part].append(nt)
                    new_open[(part, p)] = nt
        open_ = new_open
    if tail:
        for k in out:
            for nt in out[k]:
                nt.dur += tail
    return out


def bass_of(chords_, notes):
    """Bass pitch sounding at each chord start (lowest note of `notes`)."""
    res = []
    for (b0, b1, sym) in chords_:
        c = [n.pitch for n in notes if n.beat - 1e-6 <= b0 < n.beat + n.dur - 1e-6]
        res.append(min(c) if c else None)
    return res


# =========================================================================== DSP helpers


def db(x):
    return 10 ** (x / 20)




def sos_shelf(f0, gain_db, high=True, s=0.8):
    A = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * f0 / SR
    al = math.sin(w0) / 2 * math.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    c = math.cos(w0)
    if high:
        b = [A * ((A + 1) + (A - 1) * c + 2 * math.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - 2 * math.sqrt(A) * al)]
        a = [(A + 1) - (A - 1) * c + 2 * math.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - 2 * math.sqrt(A) * al]
    else:
        b = [A * ((A + 1) - (A - 1) * c + 2 * math.sqrt(A) * al), 2 * A * ((A - 1) - (A + 1) * c),
             A * ((A + 1) - (A - 1) * c - 2 * math.sqrt(A) * al)]
        a = [(A + 1) + (A - 1) * c + 2 * math.sqrt(A) * al, -2 * ((A - 1) + (A + 1) * c),
             (A + 1) + (A - 1) * c - 2 * math.sqrt(A) * al]
    return np.array([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]])


def filt(x, sos):
    return signal.sosfilt(sos, x, axis=0)


def lp(x, f, order=2):
    return filt(x, signal.butter(order, f, "low", fs=SR, output="sos"))


def hp(x, f, order=2):
    return filt(x, signal.butter(order, f, "high", fs=SR, output="sos"))


def bp(x, f0, f1, order=2):
    return filt(x, signal.butter(order, [f0, f1], "band", fs=SR, output="sos"))


def stereo(x):
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def pan_st(x, p):
    gl = math.cos((p + 1) * math.pi / 4) * math.sqrt(2)
    gr = math.sin((p + 1) * math.pi / 4) * math.sqrt(2)
    return x * np.array([gl, gr])


def make_ir(rt60, seed=0, predelay=0.02, bright=1.0, er=0.35, width=1.0):
    """Synthetic stereo hall impulse response: 4-band exponentially decaying noise (highs die
    faster), a soft diffusion build-up, a handful of early reflections, unit energy."""
    rng = np.random.default_rng(seed)
    n = int((rt60 * 1.15) * SR)
    t = np.arange(n) / SR
    bands = [(None, 280, 1.25), (280, 1400, 1.0), (1400, 4500, 0.78 * bright), (4500, None, 0.5 * bright)]
    out = np.zeros((n, 2))
    for c in range(2):
        noise = rng.standard_normal(n)
        ir = np.zeros(n)
        for lo_, hi_, k in bands:
            if lo_ is None:
                s = signal.butter(2, hi_, "low", fs=SR, output="sos")
            elif hi_ is None:
                s = signal.butter(2, lo_, "high", fs=SR, output="sos")
            else:
                s = signal.butter(2, [lo_, hi_], "band", fs=SR, output="sos")
            ir += signal.sosfilt(s, noise) * np.exp(-6.9078 * t / (rt60 * k))
        ir *= np.clip(t / 0.045, 0, 1) ** 1.3
        dens = np.sqrt(np.mean(ir[: int(0.2 * SR)] ** 2)) + 1e-9
        for _ in range(9):
            d = rng.uniform(0.004, 0.075)
            i = int(d * SR)
            ir[i] += rng.choice([-1, 1]) * er * dens * 30 * math.exp(-d / 0.06) * rng.uniform(0.5, 1.0)
        out[:, c] = ir
    mid = (out[:, 0] + out[:, 1]) / 2
    side = (out[:, 0] - out[:, 1]) / 2 * width
    out = np.stack([mid + side, mid - side], axis=1)
    out = np.concatenate([np.zeros((int(predelay * SR), 2)), out])
    out /= np.sqrt(np.sum(out ** 2) / 2) + 1e-12
    # fade the very end of the IR
    m = int(0.1 * SR)
    out[-m:] *= np.linspace(1, 0, m)[:, None]
    return out


def convolve(x, ir):
    n = len(x)
    return np.stack([signal.oaconvolve(x[:, c], ir[:, c])[:n] for c in range(2)], axis=1)


def _block_env(x, block=48):
    n = len(x)
    nb = (n + block - 1) // block
    pw = np.pad(np.mean(x ** 2, axis=1), (0, nb * block - n)).reshape(nb, block).mean(axis=1)
    return pw, nb


def compressor(x, thresh_db, ratio, att_ms=25.0, rel_ms=300.0, knee=6.0):
    """Feed-forward RMS bus compressor (1 ms blocks, soft knee). thresh_db is absolute dBFS."""
    block = 48
    pw, nb = _block_env(x, block)
    # RMS detector smoothing (~30 ms)
    pw = signal.lfilter([1 - math.exp(-1 / 30)], [1, -math.exp(-1 / 30)], pw)
    lvl = 10 * np.log10(pw + 1e-12)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    a = math.exp(-1 / att_ms)
    r = math.exp(-1 / rel_ms)
    g = np.empty(nb)
    cur = 0.0
    for i in range(nb):
        target = gr[i]
        cur = target + (cur - target) * (a if target > cur else r)
        g[i] = cur
    gs = np.interp(np.arange(len(x)), np.arange(nb) * block + block / 2, g)
    return x * db(-gs)[:, None]


def limiter(x, ceiling_db=-1.2, block=48, look=4, release_ms=120.0):
    ceil = db(ceiling_db)
    n = len(x)
    nb = (n + block - 1) // block
    pk = np.pad(np.max(np.abs(x), axis=1), (0, nb * block - n)).reshape(nb, block).max(axis=1)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, size=2 * look + 1)
    rel = math.exp(-block / (release_ms * SR / 1000))
    g = np.empty(nb)
    cur = 1.0
    for i in range(nb):
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * rel
        g[i] = cur
    gs = np.interp(np.arange(n), np.arange(nb) * block + block / 2, g)
    return np.clip(x * gs[:, None], -ceil, ceil)


# BS.1770 K-weighting at 48 kHz (identical to pyloudnorm's default filters)
_K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
_K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def kweight(x):
    y = signal.lfilter(*_K1, x, axis=0)
    return signal.lfilter(*_K2, y, axis=0)


def integrated_lufs(x):
    z = kweight(x)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(z) < blk:
        return -70.0
    idx = np.arange(0, len(z) - blk + 1, hop)
    ms = np.array([np.sum(np.mean(z[i:i + blk] ** 2, axis=0)) for i in idx])
    L = -0.691 + 10 * np.log10(ms + 1e-15)
    g = ms[L > -70]
    if len(g) == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    g2 = ms[(L > -70) & (L > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(g2) + 1e-15))


def short_term(x, win=3.0, hop=0.1):
    """(times, LUFS) short-term loudness, window centered."""
    z = kweight(x)
    p = np.sum(z ** 2, axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    w = int(win * SR)
    times = np.arange(0, len(x) / SR, hop)
    out = []
    for t in times:
        i0 = int(max(0, t * SR - w / 2))
        i1 = int(min(len(x), t * SR + w / 2))
        ms = (c[i1] - c[i0]) / max(1, i1 - i0)
        out.append(-0.691 + 10 * np.log10(ms + 1e-15))
    return times, np.array(out)


# =========================================================================== synthesizers (numpy)

OS = 2                       # oversampling factor for nonlinear synths


def bl_harm(phase, f, sr, amp_fn, kmax=64, fmax=19000.0):
    out = np.zeros_like(phase)
    for k in range(1, kmax + 1):
        g = np.clip((fmax - k * f) / 1500.0, 0.0, 1.0)
        if not np.any(g):
            break
        out += g * amp_fn(k) * np.sin(k * phase)
    return out


def bl_pulse(phase, f, duty, kmax=64, fmax=17000.0):
    out = np.zeros_like(phase)
    sh = 2 * np.pi * duty
    for k in range(1, kmax + 1):
        g = np.clip((fmax - k * f) / 1500.0, 0.0, 1.0)
        if not np.any(g):
            break
        out += g * (np.sin(k * phase) - np.sin(k * (phase + sh))) / k
    return out * (2 / np.pi)


def bl_tri(phase, f, kmax=41, fmax=15000.0):
    out = np.zeros_like(phase)
    for k in range(1, kmax + 1, 2):
        g = np.clip((fmax - k * f) / 1500.0, 0.0, 1.0)
        if not np.any(g):
            break
        out += g * ((-1) ** ((k - 1) // 2)) * np.sin(k * phase) / (k * k)
    return out * (8 / np.pi ** 2)


def lp_noise(n, fc, sr, rng):
    x = rng.standard_normal(n)
    s = signal.butter(2, fc, "low", fs=sr, output="sos")
    y = signal.sosfilt(s, x)
    return y / (np.std(y) + 1e-9)


def mono_line(ev, n, sr, *, glide=0.03, legato_gap=0.05, scoop=0.0, scoop_tau=0.05, vib_depth=0.0,
              vib_rate=5.6, vib_delay=0.15, vib_ramp=0.25, vib_min=0.22, jitter=0.0, attack=0.01,
              release=0.05, sustain=1.0, decay=0.12, seed=0):
    """Monophonic performance curves. ev = [(t0, t1, midi, vel)] sorted.
    Returns (midi pitch per sample, amplitude per sample)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / sr
    midi = np.full(n, float(ev[0][2]))
    amp = np.zeros(n)
    prev_p, prev_end = None, -9.0
    for i, (t0, t1, p, v) in enumerate(ev):
        i0 = max(0, int(t0 * sr))
        j1 = min(n, int(ev[i + 1][0] * sr)) if i + 1 < len(ev) else n
        if i0 >= n:
            break
        tt = t[i0:j1] - t0
        legato_in = prev_p is not None and (t0 - prev_end) < legato_gap
        if legato_in:
            seg = p + (prev_p - p) * np.exp(-tt / max(glide, 1e-4))
        else:
            seg = p + scoop * np.exp(-tt / max(scoop_tau, 1e-4))
        if vib_depth and (t1 - t0) >= vib_min:
            d = vib_depth * np.clip((tt - vib_delay) / vib_ramp, 0.0, 1.0)
            rate = vib_rate * (1 + 0.04 * np.sin(2 * np.pi * 0.7 * tt + rng.uniform(0, 6)))
            seg = seg + d * np.sin(2 * np.pi * np.cumsum(rate) / sr)
        midi[i0:j1] = seg
        # amplitude envelope (attack, decay to sustain, release after t1)
        g = (v / 127.0) ** 1.3
        k1 = min(n, int((t1 + release * 6) * sr))
        te = t[i0:k1] - t0
        env = np.clip(te / max(attack, 1e-4), 0, 1)
        env = env * (sustain + (1 - sustain) * np.exp(-np.maximum(te - attack, 0) / max(decay, 1e-4)))
        rel = np.where(te > (t1 - t0), np.exp(-(te - (t1 - t0)) / max(release, 1e-4)), 1.0)
        amp[i0:k1] = np.maximum(amp[i0:k1], g * env * rel)
        prev_p, prev_end = p, t1
    if jitter:
        midi += jitter * lp_noise(n, 6.0, sr, rng)
    return midi, amp


def _notes_ev(part, cue, offset=0.0):
    ns = sorted(part.notes, key=lambda x: x.beat)
    return [(cue.tmap.sec(x.beat) + offset, cue.tmap.sec(x.beat + x.dur) + offset, x.pitch, x.vel) for x in ns]


def _decimate(y):
    return signal.resample_poly(y, 1, OS, axis=0)


def synth_kazoo(part, cue, n):
    """Kazoo: bright buzzy harmonic source (hummed pitch with scoops, vibrato and wobble), an
    asymmetric 'membrane' soft-clip, pitch-synchronous rasp noise and nasal formant peaks."""
    sr = SR * OS
    m = n * OS
    rng = np.random.default_rng(7)
    ev = _notes_ev(part, cue)
    midi, amp = mono_line(ev, m, sr, glide=0.045, legato_gap=0.03, scoop=-0.55, scoop_tau=0.045,
                          vib_depth=0.32, vib_rate=5.9, vib_delay=0.13, vib_ramp=0.22, vib_min=0.3,
                          jitter=0.05, attack=0.022, release=0.045, sustain=0.86, decay=0.09, seed=3)
    f = 440.0 * 2 ** ((midi - 69) / 12)
    ph = 2 * np.pi * np.cumsum(f) / sr
    src = bl_harm(ph, f, sr, lambda k: k ** -0.62, kmax=48)
    src /= np.max(np.abs(src)) + 1e-9
    buzz = np.tanh(2.8 * src + 0.4) - math.tanh(0.4)
    pulse = ((1 + np.cos(ph)) / 2) ** 8
    rasp = signal.sosfilt(signal.butter(2, 1800, "high", fs=sr, output="sos"), rng.standard_normal(m)) * pulse
    x = 0.62 * buzz + 0.3 * src + 0.22 * rasp
    for f0, gdb, q in ((470, 6, 1.8), (1180, 8, 2.6), (2450, 9, 3.5), (3650, 5, 4.0)):
        A = 10 ** (gdb / 40)
        w0 = 2 * math.pi * f0 / sr
        al = math.sin(w0) / (2 * q)
        b = [1 + al * A, -2 * math.cos(w0), 1 - al * A]
        a = [1 + al / A, -2 * math.cos(w0), 1 - al / A]
        x = signal.lfilter(b, a, x)
    x = signal.sosfilt(signal.butter(2, 230, "high", fs=sr, output="sos"), x)
    x = signal.sosfilt(signal.butter(2, 8000, "low", fs=sr, output="sos"), x)
    jit = 1 + 0.08 * lp_noise(m, 28.0, sr, rng)
    y = x * amp * jit
    y = _decimate(y)[:n]
    y /= np.max(np.abs(y)) + 1e-9
    return stereo(y * 0.5)


_LFSR = {}


def lfsr(short=False):
    if short not in _LFSR:
        reg, tap, out = 1, (6 if short else 1), []
        for _ in range(32767):
            bit = (reg ^ (reg >> tap)) & 1
            reg = (reg >> 1) | (bit << 14)
            out.append(reg & 1)
        _LFSR[short] = np.array(out, float) * 2 - 1
    return _LFSR[short]


def nes_noise(m, clk, sr, short=False):
    s = lfsr(short)
    idx = (np.arange(m) * (clk / sr)).astype(np.int64) % len(s)
    return s[idx]


def synth_chip(part, cue, n):
    """Chiptune voices: kind in part.opts['kind']: lead / echo (band-limited pulse with duty,
    vibrato), arp (fast chord arpeggio on a pulse), tri (stepped triangle bass), noise (drums)."""
    kind = part.opts["kind"]
    sr = SR * OS
    m = n * OS
    t = np.arange(m) / sr
    if kind in ("lead", "echo", "arp"):
        if kind == "arp":
            ev = []
            for nt in sorted(part.notes, key=lambda x: x.beat):
                ev.append((cue.tmap.sec(nt.beat), cue.tmap.sec(nt.beat + nt.dur), nt.pitch, nt.vel))
            midi, amp = mono_line(ev, m, sr, glide=0.0005, legato_gap=0.004, attack=0.002, release=0.008,
                                  sustain=0.8, decay=0.05)
        else:
            off = part.opts.get("delay", 0.0)
            midi, amp = mono_line(_notes_ev(part, cue, off), m, sr, glide=0.012, legato_gap=0.01,
                                  vib_depth=0.22, vib_rate=6.2, vib_delay=0.16, vib_ramp=0.12, vib_min=0.38,
                                  attack=0.003, release=0.03, sustain=0.72, decay=0.09)
        f = 440.0 * 2 ** ((midi - 69) / 12)
        ph = 2 * np.pi * np.cumsum(f) / sr
        duty = part.opts.get("duty", 0.25)
        if callable(duty):
            duty = duty(t)
        x = bl_pulse(ph, f, duty)
        amp = np.round(amp * 15) / 15          # 4-bit volume steps
        y = x * amp
    elif kind == "tri":
        midi, amp = mono_line(_notes_ev(part, cue), m, sr, glide=0.001, legato_gap=0.004, attack=0.002,
                              release=0.012, sustain=1.0)
        f = 440.0 * 2 ** ((midi - 69) / 12)
        ph = 2 * np.pi * np.cumsum(f) / sr
        x = bl_tri(ph, f)
        x = np.round(x * 7.5) / 7.5            # gentle 4-bit stepping
        y = x * (amp > 0.02) * 0.9
        y = signal.sosfilt(signal.butter(2, 9000, "low", fs=sr, output="sos"), y)
    else:  # noise drums
        y = np.zeros(m)
        for nt in part.notes:
            ts = cue.tmap.sec(nt.beat)
            i0 = int(ts * sr)
            g = nt.vel / 127
            if nt.pitch == 36:      # kick: triangle pitch drop + short low noise
                L = int(0.16 * sr)
                tt = np.arange(L) / sr
                fk = 55 + 170 * np.exp(-tt / 0.025)
                hit = bl_tri(2 * np.pi * np.cumsum(fk) / sr, fk) * np.exp(-tt / 0.07)
                hit += 0.25 * nes_noise(L, 3000, sr) * np.exp(-tt / 0.012)
            elif nt.pitch == 38:    # snare
                L = int(0.2 * sr)
                tt = np.arange(L) / sr
                hit = 0.8 * nes_noise(L, 14000, sr) * np.exp(-tt / 0.07)
                fs_ = 190 * np.ones(L)
                hit += 0.35 * bl_tri(2 * np.pi * np.cumsum(fs_) / sr, fs_) * np.exp(-tt / 0.03)
            elif nt.pitch == 42:    # closed hat (short periodic noise = metallic)
                L = int(0.06 * sr)
                tt = np.arange(L) / sr
                hit = 0.45 * nes_noise(L, 40000, sr, short=True) * np.exp(-tt / 0.018)
            else:                   # crash
                L = int(1.2 * sr)
                tt = np.arange(L) / sr
                hit = 0.5 * nes_noise(L, 30000, sr) * np.exp(-tt / 0.35)
            j = min(m, i0 + len(hit))
            if j > i0:
                y[i0:j] += g * hit[: j - i0]
        y = np.round(y * 12) / 12
    y = _decimate(y)[:n]
    return stereo(y * 0.5)


def synth_theremin(part, cue, n):
    """Theremin: almost-pure sine following a hand-drawn pitch path with swoops/overshoots,
    a wide vibrato that gets wider and faster (a bit unhinged), and a swelling amplitude."""
    sr = SR * OS
    m = n * OS
    t = np.arange(m) / sr
    rng = np.random.default_rng(11)
    keys = part.opts["path"]                      # [(sec, midi)]
    ks = np.array([k[0] for k in keys])
    kv = np.array([k[1] for k in keys])
    seg = np.clip(np.searchsorted(ks, t, side="right") - 1, 0, len(ks) - 2)
    x = np.clip((t - ks[seg]) / (ks[seg + 1] - ks[seg]), 0, 1)
    x = 0.5 - 0.5 * np.cos(np.pi * x)
    midi = kv[seg] + (kv[seg + 1] - kv[seg]) * x
    vd = np.interp(t, [0, 0.35, 0.8, 1.3, 1.8], [0.15, 0.25, 0.55, 0.85, 0.9])
    vr = np.interp(t, [0, 0.6, 1.3, 1.8], [5.0, 5.4, 6.6, 7.2])
    midi = midi + vd * np.sin(2 * np.pi * np.cumsum(vr) / sr) + 0.04 * lp_noise(m, 4, sr, rng)
    f = 440.0 * 2 ** ((midi - 69) / 12)
    ph = 2 * np.pi * np.cumsum(f) / sr
    y = np.sin(ph) + 0.13 * np.sin(2 * ph + 0.3) + 0.05 * np.sin(3 * ph)
    y = np.tanh(1.3 * y) / math.tanh(1.3)
    a = np.interp(t, part.opts["amp_t"], part.opts["amp_v"])
    a *= 1 + 0.06 * np.sin(2 * np.pi * 3.1 * t)
    y = _decimate(y * a)[:n]
    return stereo(y * 0.55)


def synth_drums_lofi(part, cue, n):
    """Dusty boom-bap kit: 36 kick, 38 snare, 42 closed hat, 46 open hat, 37 rim."""
    rng = np.random.default_rng(5)
    y = np.zeros(n)
    for nt in part.notes:
        ts = cue.tmap.sec(nt.beat) + part.lazy
        i0 = int(ts * SR)
        g = (nt.vel / 127) ** 1.2
        if nt.pitch == 36:
            L = int(0.45 * SR)
            tt = np.arange(L) / SR
            fk = 47 + 75 * np.exp(-tt / 0.045)
            hit = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tt / 0.2)
            hit += 0.18 * lp(rng.standard_normal(L), 2500) * np.exp(-tt / 0.006)
            hit = np.tanh(1.8 * hit)
        elif nt.pitch == 38:
            L = int(0.3 * SR)
            tt = np.arange(L) / SR
            nz = bp(rng.standard_normal(L), 900, 5200) * np.exp(-tt / 0.085)
            body = np.sin(2 * np.pi * 185 * tt) * np.exp(-tt / 0.045)
            hit = 0.75 * nz / (np.std(nz[:2000]) + 1e-9) * 0.35 + 0.6 * body
        elif nt.pitch in (42, 46):
            L = int((0.25 if nt.pitch == 46 else 0.07) * SR)
            tt = np.arange(L) / SR
            hit = hp(rng.standard_normal(L), 6500) * np.exp(-tt / (0.09 if nt.pitch == 46 else 0.022)) * 0.5
        else:
            L = int(0.08 * SR)
            tt = np.arange(L) / SR
            hit = bp(rng.standard_normal(L), 1500, 4500) * np.exp(-tt / 0.015) * 0.6
        j = min(n, i0 + len(hit))
        if j > i0 >= 0:
            y[i0:j] += g * hit[: j - i0]
    y = lp(y, 7000)
    y = np.tanh(1.6 * y) / 1.6
    return stereo(y * 0.9)


def synth_sub(part, cue, n):
    """Soft rounded sub bass (sine + a little 2nd harmonic)."""
    midi, amp = mono_line(_notes_ev(part, cue, part.lazy), n, SR, glide=0.02, legato_gap=0.02,
                          attack=0.012, release=0.09, sustain=0.75, decay=0.5)
    f = 440.0 * 2 ** ((midi - 69) / 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.18 * np.sin(2 * ph)) * amp
    y = np.tanh(1.4 * y)
    return stereo(y * 0.6)


def _metal(L, rng, fmin=320, fmax=13500, k=90):
    t = np.arange(L) / SR
    fr = np.exp(rng.uniform(math.log(fmin), math.log(fmax), k))
    am = (fr / 1000) ** -0.15 * rng.uniform(0.3, 1.0, k)
    y = np.zeros(L)
    for f_, a_ in zip(fr, am):
        y += a_ * np.sin(2 * np.pi * f_ * t + rng.uniform(0, 6.28))
    y /= np.std(y) + 1e-9
    nz = bp(rng.standard_normal(L), 2500, 14000)
    nz /= np.std(nz) + 1e-9
    return 0.55 * y + 0.65 * nz


def synth_cymbal(part, cue, n):
    """Suspended cymbal: soft-mallet roll swells (crescendo with mallet flutter) into a crash
    with a bright fast decay over a darker long wash. part.opts['events'] =
    [(t_swell_start, t_hit, swell_gain, hit_gain, decay_s)] in seconds."""
    rng = np.random.default_rng(23)
    out = np.zeros((n, 2))
    for (ts, th, gs, gh, dec) in part.opts["events"]:
        i0 = int(ts * SR)
        ih = int(th * SR)
        L = min(n, ih + int(dec * 1.6 * SR)) - i0
        if L <= 0:
            continue
        t = np.arange(L) / SR
        for c in range(2):
            base = _metal(L, rng)
            x = np.zeros(L)
            hs = ih - i0
            if hs > 0 and gs > 0:
                u = np.clip(t / (hs / SR), 0, 1)
                sw = gs * (np.exp(3.2 * u) - 1) / (math.exp(3.2) - 1)
                flutter = 1 + 0.22 * np.abs(lp_noise(L, 22, SR, rng))
                sw = np.where(t <= hs / SR, sw * flutter, 0.0)
                x += base * sw * 0.6
            th_ = t - hs / SR
            hit = np.where(th_ >= 0, np.exp(-np.maximum(th_, 0) / dec) * np.clip(th_ / 0.004, 0, 1), 0.0)
            bright = np.where(th_ >= 0, np.exp(-np.maximum(th_, 0) / (dec * 0.25)), 0.0)
            x += gh * base * hit * 0.55 + gh * hp(base, 6000) * bright * 0.35
            seg = slice(i0, i0 + L)
            out[seg, c] += x
    out = lp(hp(out, 350), 15000)
    return out * 0.18


def synth_shimmer(part, cue, n):
    """Glassy space shimmer: each note = a pair of slightly detuned sines (slow beating) plus a
    faint octave, shaped by the part's dyn keyframes (0..127 -> linear gain)."""
    t = np.arange(n) / SR
    y = np.zeros((n, 2))
    rng = np.random.default_rng(17)
    beats = np.array([cue.tmap.beat(tt) for tt in np.arange(0, n / SR + 0.05, 0.05)])
    gk = np.array([dyn_at(part.dyn, b) / 127.0 for b in beats]) if part.dyn else np.ones(len(beats))
    g = np.interp(t, np.arange(len(beats)) * 0.05, gk) ** 1.5
    for nt in part.notes:
        t0, t1 = cue.tmap.sec(nt.beat), cue.tmap.sec(nt.beat + nt.dur)
        f = 440.0 * 2 ** ((nt.pitch - 69) / 12)
        env = np.clip((t - t0) / 1.5, 0, 1) * np.clip((t1 + 1.5 - t) / 1.5, 0, 1)
        for c, det in enumerate((-2.5, 2.5)):
            fd = f * 2 ** (det / 1200)
            ph = rng.uniform(0, 6.28)
            y[:, c] += env * (np.sin(2 * np.pi * fd * t + ph) + 0.18 * np.sin(4 * np.pi * fd * t + ph)
                              + 0.5 * np.sin(2 * np.pi * f * 2 ** (-det / 1200) * t + 1.1))
    return y * g[:, None] * 0.12


def synth_vinyl(n, rng, density=11.0, hiss_db=-50.0):
    x = np.zeros((n, 2))
    k = rng.poisson(density * n / SR)
    pos = rng.integers(0, n - 200, k)
    amps = np.clip(rng.pareto(2.5, k) * 0.03, 0, 0.35)
    w = 40
    shape = np.exp(-np.arange(w) / 6.0)
    for p_, a_ in zip(pos, amps):
        c = rng.integers(0, 2)
        x[p_:p_ + w, c] += a_ * rng.choice([-1, 1]) * shape * rng.uniform(0.6, 1.0)
        x[p_:p_ + w, 1 - c] += 0.4 * a_ * rng.choice([-1, 1]) * shape
    x = hp(x, 900)
    hiss = lp(hp(rng.standard_normal((n, 2)), 2500), 9000)
    hiss /= np.std(hiss) + 1e-9
    rumble = lp(rng.standard_normal((n, 2)), 60)
    rumble /= np.std(rumble) + 1e-9
    return x + hiss * db(hiss_db) + rumble * db(hiss_db - 6)


def wow_flutter(x, wow_cents=7.0, wow_hz=0.55, fl_cents=2.0, fl_hz=6.3):
    n = len(x)
    t = np.arange(n) / SR
    aw = wow_cents / (1731.0 * 2 * math.pi * wow_hz)
    af = fl_cents / (1731.0 * 2 * math.pi * fl_hz)
    d = (aw * (1 + np.sin(2 * math.pi * wow_hz * t)) + af * (1 + np.sin(2 * math.pi * fl_hz * t + 1.3))) * SR
    idx = np.arange(n) - d
    return np.stack([np.interp(idx, np.arange(n), x[:, c]) for c in range(2)], axis=1)


# =========================================================================== MIDI + fluidsynth


def soundfont() -> Path:
    for p in (SOUNDFONT, SOUNDFONT_ALT):
        if Path(p).exists():
            return Path(p)
    raise FileNotFoundError("no soundfont found")


def part_events(part: Part, cue: Cue, rng) -> list:
    """Absolute-time (s) MIDI events for one SoundFont part: [(t, prio, msg_dict)]."""
    inst = INST[part.inst]
    tm = cue.tmap
    ev = [(0.0, 0, dict(type="control_change", control=0, value=inst.bank)),
          (0.0, 0, dict(type="program_change", program=inst.prog)),
          (0.0, 0, dict(type="control_change", control=7, value=100)),
          (0.0, 0, dict(type="control_change", control=10, value=64)),
          (0.0, 0, dict(type="control_change", control=64, value=0))]
    cc = 2 if inst.expr else 11
    if part.dyn:
        b0, b1 = part.dyn[0][0], part.dyn[-1][0]
        last = None
        bb = b0
        while bb <= b1 + 1e-9:
            v = int(round(max(0, min(127, dyn_at(part.dyn, bb)))))
            if v != last:
                ev.append((max(0.0, tm.sec(bb)), 0, dict(type="control_change", control=cc, value=v)))
                last = v
            bb += 1 / 24
        v = int(round(dyn_at(part.dyn, b1)))
        ev.append((max(0.0, tm.sec(b1)), 0, dict(type="control_change", control=cc, value=v)))
        if cc == 2:
            ev.append((0.0, 0, dict(type="control_change", control=11, value=127)))
    else:
        ev.append((0.0, 0, dict(type="control_change", control=cc, value=110 if cc == 2 else 127)))
    for (d, u) in part.pedal:
        ev.append((max(0.0, tm.sec(d)), 0, dict(type="control_change", control=64, value=127)))
        ev.append((max(0.0, tm.sec(u)), 0, dict(type="control_change", control=64, value=0)))
    notes = sorted(part.notes, key=lambda x: (x.beat, x.pitch))
    starts = sorted({round(x.beat, 6) for x in notes})
    spans = []
    for nt in notes:
        j = float(np.clip(rng.normal(0, part.humanize / 2.2), -part.humanize, part.humanize)) if part.humanize else 0.0
        s = tm.sec(nt.beat) + j + part.lazy
        e = tm.sec(nt.beat + nt.dur) + part.lazy
        if part.legato:
            end_b = nt.beat + nt.dur
            if any(abs(sb - end_b) < 0.03 for sb in starts):
                e += part.legato
        e += float(np.clip(rng.normal(0, 0.004), -0.008, 0.008))
        v = int(np.clip(nt.vel + rng.integers(-3, 4), 1, 127))
        spans.append([max(0.0, s), max(s + 0.03, e), nt.pitch, v])
    by_pitch = {}
    for sp in sorted(spans, key=lambda x: x[0]):
        by_pitch.setdefault(sp[2], []).append(sp)
    for lst in by_pitch.values():
        for a, b in zip(lst, lst[1:]):
            if a[1] > b[0] - 0.004:
                a[1] = max(a[0] + 0.01, b[0] - 0.004)
    for s, e, p, v in spans:
        ev.append((s, 2, dict(type="note_on", note=p, velocity=v)))
        ev.append((e, 1, dict(type="note_off", note=p, velocity=0)))
    ev.append((cue.length + 0.6, 3, dict(type="control_change", control=20, value=0)))
    return ev


def events_to_track(ev, channel=0, name=None):
    tr = mido.MidiTrack()
    if name:
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
    last = 0
    for t, _, m in sorted(ev, key=lambda x: (x[0], x[1])):
        tick = int(round(t * 1000))
        tr.append(mido.Message(time=tick - last, channel=channel, **m))
        last = tick
    return tr


def midi_file(tracks):
    mf = mido.MidiFile(ticks_per_beat=1000)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))
    mf.tracks.append(meta)
    mf.tracks.extend(tracks)
    return mf


def fluid_render(mid_path: Path, wav_path: Path):
    cmd = ["fluidsynth", "-ni", "-q", "-F", str(wav_path), "-T", "wav", "-O", "float", "-r", str(SR),
           "-g", str(FS_GAIN), "-o", "synth.dynamic-sample-loading=1", "-o", "synth.reverb.active=0",
           "-o", "synth.chorus.active=0", "-o", "synth.polyphony=1024", "-o", "synth.cpu-cores=1",
           str(soundfont()), str(mid_path)]
    subprocess.run(cmd, check=True, capture_output=True)


def render_sf_part(part: Part, cue: Cue, n: int, seed: int) -> tuple:
    """Render one SoundFont part with fluidsynth -> ((n, 2) float array, cache file used).
    Stems are cached per cue as 24-bit FLAC keyed by the MIDI content."""
    rng = np.random.default_rng(seed)
    ev = part_events(part, cue, rng)
    mf = midi_file([events_to_track(ev, 0, part.name)])
    cdir = CACHE_DIR / cue.name
    with tempfile.TemporaryDirectory() as td:
        mp = Path(td) / "p.mid"
        mf.save(mp)
        key = hashlib.sha1(mp.read_bytes() + f"{soundfont()}{FS_GAIN}{RENDER_VERSION}".encode()).hexdigest()[:20]
        cached = cdir / f"{part.name}_{key}.flac"
        if not (USE_CACHE and cached.exists()):
            wp = Path(td) / "p.wav"
            fluid_render(mp, wp)
            x, sr = sf.read(wp, always_2d=True, dtype="float64")
            assert sr == SR
            cdir.mkdir(parents=True, exist_ok=True)
            pk = float(np.max(np.abs(x))) if len(x) else 0.0
            scale = 1.0 if pk < 0.99 else 0.99 / pk
            sf.write(cached.with_suffix(".tmp.flac"), (x * scale)[: n + SR], SR, subtype="PCM_24")
            cached.with_suffix(".tmp.flac").rename(cached)
            (cdir / f"{part.name}_{key}.scale").write_text(repr(scale))
    x, sr = sf.read(cached, always_2d=True, dtype="float64")
    sc = cdir / f"{part.name}_{key}.scale"
    if sc.exists():
        x = x / float(sc.read_text())
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    out = np.zeros((n, 2))
    k = min(n, len(x))
    out[:k] = x[:k]
    return out, cached


# =========================================================================== the theme


THEME_A = ("A4:q D5:q F#5:h | E5:q D5:q B4:h | B4:q D5:q G5:h | F#5:h E5:h | "
           "A4:q D5:q F#5:q A5:q | B5:h. A5:q | G5:h E5:q C#5:q | D5:w")
THEME_A_CHORDS = "D:4 Bm:4 G:4 A:4 D/F#:4 G:4 Gm:2 A7:2 D:4"
THEME_BARS_1_4 = "A4:q D5:q F#5:h | E5:q D5:q B4:h | B4:q D5:q G5:h | F#5:h E5:h"


def theme(start=0.0, semis=0, vel=80, tag="mel"):
    return transpose(seq(THEME_A, start, vel, tag, bar=4), semis)


# =========================================================================== cue: symphony


def compose_symphony() -> Cue:
    # ---------------------------------------------------------------- form & tempo
    # beats: intro 0-8 | theme 8-40 | build 40-56 | GP 56-57 | climax (E major) 57-73 | coda 73-84
    def w(b):
        x = 1.0
        x += 0.07 * bump(b, 2.0, 0.6) + 0.14 * rit(b, 5.5, 8.0)                 # intro: breathe, settle
        x += 0.07 * bump(b, 20.0, 0.7) + 0.12 * bump(b, 28.0, 1.0)              # appoggiatura, high point
        x += 0.16 * bump(b, 35.0, 1.6)                                          # minor iv -> cadence
        if 40 <= b < 56:
            x += -0.05 + 0.05 * smoothstep((b - 46) / 4) + 0.32 * rit(b, 52.0, 56.0)  # push, then broaden
        if 57 <= b < 73:
            x += 0.16 * bump(b, 57.0, 0.7) + 0.06 * bump(b, 61.0, 0.6)           # arrival weight
            x += 0.14 * bump(b, 65.0, 0.9) + 0.38 * rit(b, 69.0, 73.0)          # high point, ache, rit
        if 76 <= b < 82:
            x += 0.18 * rit(b, 79.5, 82.0)
        return x

    tm = TempoMap([(0, 0.55), (8, 7.5), (40, 35.0), (56, 49.4), (57, 50.5), (73, 66.0), (76, 68.4),
                   (82, 72.8)], w)
    bars = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 57, 61, 65, 69, 73, 76, 80, 84]
    intro_c = ctl("D:4 Bm:4", 0)
    theme_c = ctl(THEME_A_CHORDS, 8)
    build_c = ctl("Bm:4 G:4 D/F#:2 Em7:2 A7sus4:2 A7:2", 40)
    clim_c = ctl("E:4 B:4 A:4 Am:2 B7:2", 57)
    coda_c = ctl("E:3 E:4 E6:4", 73)
    chords_ = intro_c + theme_c + build_c + [(56, 57, "N.C.")] + clim_c + coda_c

    # shared dynamic shapes (CC2 for the Expr presets)
    # climax arc: arrival -> tender 6-5 (dip) -> swell to the high point -> the ache (iv) -> B7 -> home
    CLIMAX = [(57, 124), (58.5, 116), (60.8, 112), (61.2, 106), (63.0, 108), (64.6, 124), (65, 127),
              (67.5, 120), (69, 114), (70.2, 118), (71, 122), (72.8, 126)]
    CODA_STR = [(73.2, 116), (74.5, 84), (76, 58), (78, 36), (80, 20), (82, 0)]
    CODA_VOL = [(72.9, 0.0), (74.5, -5.0), (76, -11.0), (78, -18.0), (80, -26.0), (82, -40.0)]
    CODA_FAST = [(72.9, 0.0), (74, -6.0), (75, -14.0), (76, -30.0)]

    parts = {}

    def part(name, inst, **kw):
        parts[name] = Part(name, inst, **kw)
        return parts[name]

    # ---------------------------------------------------------------- bass line (cb) + celli 8va
    cb = part("cb", "cb", pan=0.38, send=0.22, legato=0.08)
    cb.add(seq("D2:w | B1:w", 0))
    cb.add(seq("D2:w | B1:w | G1:w | A1:w | F#1:w | G1:w | G1:h A1:h | D2:w", 8, bar=4))
    cb.add(seq("B1:w | G1:w | F#1:h E1:h | A1:w", 40, bar=4))
    cb.add(seq("E1:w | B1:w | A1:w | A1:h B1:h", 57, bar=4))
    cb.add(seq("E1:10", 73))
    cb.dyn = [(-0.6, 0), (0.3, 22), (6, 26), (8, 36), (20, 42), (24, 48), (36, 50), (40, 64), (47.6, 76),
              (48, 54), (52, 88), (55.8, 114), (57, 120), (65, 124), (69, 116), (72.8, 122)] + CODA_STR
    cb.vol = [(-1, -4.0), (7.5, -4.0), (8.5, 0.0)] + CODA_VOL

    vc2 = part("vc2", "vc_slow", pan=0.3, send=0.25, legato=0.08)
    vc2.add(seq("B2:w | G2:w | F#2:h E2:h | A2:w", 40, bar=4))
    vc2.add(seq("E2:w | B2:w | A2:w | A2:h B2:h", 57, bar=4))
    vc2.add(seq("(E2,B2):10", 73))
    vc2.dyn = [(39.5, 0), (40, 60), (47.6, 72), (48, 52), (52, 88), (55.8, 114), (57, 118), (65, 122),
               (69, 112), (72.8, 120)] + CODA_STR
    vc2.vol = [(72, 0.0)] + CODA_VOL

    # ---------------------------------------------------------------- melody carriers
    vc = part("vc", "vc", pan=0.26, send=0.3, legato=0.075, gain_db=2.0)
    vc.add(theme(8, -12, 76, "mel"))                                     # Theme A, cellos, 8vb
    assert [(n.beat - 8, n.dur, n.pitch + 12) for n in vc.notes] == \
        [(n.beat, n.dur, n.pitch) for n in seq(THEME_A, bar=4)], "Theme A must be exact"
    vc.add(seq("B3:q D4:q F#4:h | B3:q E4:q G4:h | A4:h B4:h | D5:h C#5:h", 40, 84, bar=4))
    vc.add(seq("B3:q E4:q G#4:h~ | G#4:h F#4:h | C#5:h. B4:q | A4:h F#4:q D#4:q", 57, 100, bar=4))
    vc.add(seq("E4:9", 73, 96))
    vc.dyn = [(7.4, 0), (7.9, 52), (8.6, 60), (11, 66), (12.2, 63), (15, 62), (17, 70), (19, 78), (20.2, 83),
              (22, 72), (23.6, 66), (24.5, 70), (27, 82), (28.3, 94), (30.5, 86), (32.2, 92), (34, 86),
              (35.2, 82), (36.4, 78), (39.2, 80), (40, 84), (43.6, 92), (44.2, 88), (47.6, 96), (48, 72),
              (52, 100), (55.8, 120)] + CLIMAX + CODA_STR
    vc.vol = [(72, 0.0)] + CODA_VOL

    vln1 = part("vln1", "vln1", pan=-0.34, send=0.3, legato=0.07, gain_db=4.0)
    # soaring countermelody over theme bars 4-8 (enters ~19.5 s), kept a touch under the celli
    vln1.add(seq("r:h A4:q C#5:q | D5:h A5:h | G5:h. A5:q | Bb5:h A5:q G5:q | F#5:h E5:q C#5:q", 20, 70, bar=4))
    # B-section melody (develops the head motive, rising F#5 G5 A5 B5 D6 C#6)
    vln1.add(seq("B4:q D5:q F#5:h | B4:q E5:q G5:h | A5:h B5:h | D6:h C#6:h", 40, 92, "mel", bar=4))
    # climax: Theme A in E major, violins I an octave above violins II, horns + celli an octave below
    vln1.add(seq("B5:q E6:q G#6:h~ | G#6:h F#6:h | C#7:h. B6:q | A6:h F#6:q D#6:q", 57, 110, "mel", bar=4))
    vln1.add(seq("E6:7", 73, 104, "mel"))
    vln1.dyn = [(21.6, 0), (21.9, 46), (23, 54), (24.3, 60), (26.5, 70), (28.3, 74), (31, 70), (32.3, 84),
                (34, 76), (36.3, 70), (39, 66), (40, 82), (43.5, 88), (44.2, 86), (47.6, 94), (48, 76),
                (52, 102), (54, 114), (55.8, 124)] + CLIMAX + CODA_STR
    vln1.vol = [(19, -5.0), (39, -5.0), (40.5, 0.0), (72, 0.0)] + CODA_VOL

    vln2m = part("vln2_mel", "vln2_fast", pan=-0.16, send=0.3, legato=0.07, gain_db=3.0)
    vln2m.add(seq("B4:q E5:q G#5:h~ | G#5:h F#5:h | C#6:h. B5:q | A5:h F#5:q D#5:q", 57, 110, bar=4))
    vln2m.add(seq("E5:9", 73, 100))
    vln2m.dyn = [(56.6, 0), (56.95, 120)] + CLIMAX + CODA_STR
    vln2m.vol = [(72, 0.0)] + CODA_VOL

    horns = part("horns", "horns", pan=-0.18, send=0.42, gain_db=-1.5)
    horns.add(seq("B3:q E4:q G#4:h | G#4:h F#4:h | C#5:h. B4:q | A4:h F#4:q D#4:q", 57, 108, bar=4))

    # ---------------------------------------------------------------- intro: piano + celesta
    cel = part("celesta", "celesta", pan=0.2, send=0.55, humanize=0.006, gain_db=7.0)
    cel.add(seq("A5:q D6:q F#6:h | E6:q D6:q B5:h", 0, 56, "mel", bar=4, vels=[58, 56, 64, 56, 52, 50]))
    cel.add(seq("B5:q E6:q G#6:h | F#6:q E6:q C#6:h", 76, 54, "mel", bar=4, vels=[56, 54, 60, 54, 50, 54]))
    pno = part("piano", "mellow", pan=0.0, send=0.4, humanize=0.006, gain_db=6.0)
    pno.add(seq("A4:q D5:q F#5:h | E5:q D5:q B4:h", 0, 46, "mel", bar=4, vels=[46, 45, 52, 46, 42, 40]))
    pno.add(seq("(D2,A2):w | (B1,F#2):w", 0, 32))
    pno.pedal = [(-0.2, 3.92), (4.02, 9.0)]

    # ---------------------------------------------------------------- string pads
    vla = part("vla", "vla", pan=0.12, send=0.3)
    vln2 = part("vln2", "vln2", pan=-0.14, send=0.3)
    iv = voice_chords(intro_c, 3, 54, 66)
    for k, v in pad_notes(intro_c, iv, {"vla": [0, 1, 2]}, vel=50, tail=0.3).items():
        parts[k].add(v)
    # pad harmony; in theme bar 4 the 5th (E) waits until the celli resolve F#->E (keeps the appoggiatura clean)
    pad_c = theme_c[:3] + [(20, 22, "A(no5)"), (22, 24, "A")] + theme_c[4:]
    tb = bass_of(pad_c, cb.notes)
    tv1 = voice_chords(pad_c[:5], 3, 61, 78, bass=tb[:5], top_max=76)
    tv2 = voice_chords(pad_c[5:], 3, 59, 74, bass=tb[5:], prev=tv1[-1], top_max=73)
    for k, v in pad_notes(pad_c, tv1 + tv2, {"vla": [0, 1], "vln2": [2]}, vel=56).items():
        parts[k].add(v)
    bb = bass_of(build_c, cb.notes)
    bv1 = voice_chords(build_c[:2], 4, 52, 72, bass=bb[:2], prev=None, top_max=[69, 71])
    for k, v in pad_notes(build_c[:2], bv1, {"vla": [0, 1], "vln2": [2, 3]}, vel=70).items():
        parts[k].add(v)
    vla.add(seq("(G#3,B3,E4):10", 73, 90))
    vla.dyn = [(-0.6, 0), (0.4, 24), (4, 28), (7.4, 30), (8.3, 30), (16, 36), (20, 40), (24, 42), (28, 50),
               (32, 48), (36, 44), (40, 58), (47.5, 72), (47.95, 56), (48.1, 0), (72.9, 0), (73.05, 106)] + CODA_STR
    vla.vol = [(-1, -6.0), (7.0, -6.0), (8.5, -2.0), (20, -2.0), (24, 0.0)] + CODA_VOL
    vln2.dyn = [(7.4, 0), (8.3, 28), (16, 36), (20, 40), (24, 42), (28, 50), (32, 48), (36, 44), (40, 58),
                (47.5, 72), (47.95, 56), (48.1, 0)]
    vln2.vol = [(7, -3.0), (24, -1.0)]

    vln2t = part("vln2_trem", "vln2_trem", pan=-0.14, send=0.3)
    vlat = part("vla_trem", "vla_trem", pan=0.12, send=0.3, gain_db=-3.0)
    bv2 = voice_chords(build_c[2:], 4, 55, 79, bass=bb[2:], prev=bv1[-1], top_max=[78, 79, 80, 79])
    for k, v in pad_notes(build_c[2:], bv2, {"vla_trem": [0, 1], "vln2_trem": [2, 3]}, vel=80).items():
        parts[k].add(v)
    vln2t.dyn = [(47.9, 0), (48.05, 34), (50, 50), (52, 74), (55.8, 116), (56.3, 0)]
    cbass = bass_of(clim_c, cb.notes)
    cv = voice_chords(clim_c, 3, 55, 72, bass=cbass)
    for k, v in pad_notes(clim_c, cv, {"vla_trem": [0, 1, 2]}, vel=100).items():
        parts[k].add(v)
    vlat.dyn = [(47.9, 0), (48.05, 34), (50, 50), (52, 74), (55.8, 116)] + CLIMAX[:-1] + [(72.9, 118), (73.1, 0)]

    # ---------------------------------------------------------------- horns, brass, choir, trombones
    hv = voice_chords(build_c, 3, 52, 71, bass=bb, top_max=[66, 67, 69, 69, 69, 69])
    for k, v in pad_notes(build_c, hv, {"horns": [0, 1, 2]}, vel=80).items():
        parts[k].add(v)
    horns.add(seq("(E3,B3,E4,G#4):9", 73, 100))
    horns.dyn = [(39.6, 0), (40.2, 40), (44, 50), (47.6, 62), (48, 40), (52, 78), (55.8, 116)] + CLIMAX + \
        [(73.2, 108), (76, 40)]
    horns.vol = [(41, -3.0), (52, -1.0), (56, 0.0)] + CODA_FAST

    choir = part("choir", "choir", pan=0.0, send=0.5, legato=0.1, gain_db=-3.5)
    cb_choir = bass_of(build_c[1:], cb.notes)
    chv = voice_chords(build_c[1:], 4, 52, 79, bass=cb_choir, top_max=[74, 76, 76, 77, 76])
    for k, v in pad_notes(build_c[1:], chv, {"choir": [0, 1, 2, 3]}, vel=80).items():
        parts[k].add(v)
    clv = voice_chords(clim_c, 4, 52, 79, bass=cbass, prev=chv[-1], force_top=[None, None, None, 72, 71])
    for k, v in pad_notes(clim_c, clv, {"choir": [0, 1, 2, 3]}, vel=100).items():
        parts[k].add(v)
    choir.add(seq("(E3,B3,G#4,E5):5", 73, 96))
    choir.dyn = [(43.8, 0), (44.6, 18), (47.6, 34), (48, 28), (52, 64), (55.8, 110)] + CLIMAX + \
        [(73.2, 104), (76, 20), (76.6, 0)]
    choir.vol = [(56, 0.0)] + CODA_FAST

    brass = part("brass", "brass", pan=0.08, send=0.38, gain_db=-6.5)
    brv = voice_chords(build_c[4:], 4, 50, 72, bass=bb[4:], top_max=69)
    for k, v in pad_notes(build_c[4:], brv, {"brass": [0, 1, 2, 3]}, vel=96).items():
        parts[k].add(v)
    clb = voice_chords(clim_c, 4, 52, 72, bass=cbass, prev=brv[-1], top_max=[68, 71, 69, 69, 69])
    for k, v in pad_notes(clim_c, clb, {"brass": [0, 1, 2, 3]}, vel=104).items():
        parts[k].add(v)
    brass.add(seq("(E3,G#3,B3,E4):4", 73, 100))
    brass.dyn = [(51.8, 0), (52.2, 66), (55.8, 114)] + CLIMAX + [(73.2, 100), (75.6, 0)]
    brass.vol = [(56, 0.0)] + CODA_FAST

    trb = part("trombone", "trombone", pan=0.24, send=0.35, gain_db=-5.0)
    trb.add(seq("E2:w | B2:w | A2:w | A2:h B2:h | E2:4", 57, 100))
    trb.dyn = [(56.6, 0), (56.95, 108)] + CLIMAX + [(73.2, 100), (75, 30), (76, 0)]

    # ---------------------------------------------------------------- harp, timpani, glock, cymbal
    harp = part("harp", "harp", pan=-0.45, send=0.38, humanize=0.006)
    harp.add(harp_arp(theme_c, base_pitch_lo=48, v=(44, 58), low_vel=50))
    harp.add(harp_arp(build_c[:2], base_pitch_lo=50, v=(54, 68)))
    harp.add(harp_arp(build_c[2:4], base_pitch_lo=50, v=(40, 54)))                       # subito p
    harp.add(harp_arp(build_c[4:], base_pitch_lo=52, step=0.25, v=(56, 84), low=True))
    harp.add(gliss({4, 6, 8, 9, 11, 1, 3}, P("E3"), P("E6"), 57.0, 0.62, 58, 100))
    harp.add(harp_arp(clim_c, base_pitch_lo=64, v=(72, 90), low=False))
    harp.add([Note(73 + i * 0.09, 6.0, p, 74 - i * 2) for i, p in
              enumerate([P(x) for x in ("E2", "B2", "E3", "G#3", "B3", "E4", "G#4", "B4", "E5")])])
    harp.vol = [(70, 0.0), (76, -8.0), (80, -20.0)]

    timp = part("timpani", "timpani", pan=0.16, send=0.32, humanize=0.004)
    timp.add(roll(P("A2"), 52.0, 55.9, tm, 12, 30, 112))
    timp.add([Note(57, 2, P("E2"), 124), Note(61, 2, P("B2"), 104)])
    timp.add(roll(P("B2"), 63.0, 64.96, tm, 12, 50, 112))
    timp.add([Note(65, 2, P("A2"), 122), Note(69, 2, P("A2"), 108)])
    timp.add(roll(P("B2"), 71.0, 72.96, tm, 12, 58, 118))
    timp.add([Note(73, 2, P("E2"), 120)])
    timp.add(roll(P("E2"), 73.4, 75.6, tm, 11, 60, 24))

    glock = part("glock", "glock", pan=-0.24, send=0.4, gain_db=-5.0, humanize=0.004)
    glock.add(seq("B5:q E6:q G#6:h | r:h F#6:h | C#7:h. B6:q | A6:h r:h | E6:q", 57, 60))

    vgp = part("vln_gp", "vln_slow", pan=-0.25, send=0.45, gain_db=6.0)
    vgp.add([Note(56.05, 1.0, P("E6"), 52)])
    vgp.dyn = [(55.9, 0), (56.1, 28), (56.6, 34), (56.98, 28), (57.1, 0)]

    cym = part("cymbal", "cymbal", pan=0.1, send=0.45, synth=synth_cymbal, gain_db=-8.0)
    cym.opts["events"] = [(tm.sec(56.6), tm.sec(57.0), 0.8, 1.0, 3.2),
                          (tm.sec(63.6), tm.sec(65.0), 0.45, 0.5, 3.0),
                          (tm.sec(71.6), tm.sec(73.0), 0.35, 0.45, 3.5)]
    cym.notes = [Note(57, 1, 49, 110), Note(65, 1, 49, 80), Note(73, 1, 49, 70)]

    order = ["celesta", "piano", "glock", "harp", "vln_gp", "vln1", "vln2_mel", "vln2", "vln2_trem", "vla",
             "vla_trem", "vc", "vc2", "cb", "horns", "brass", "trombone", "choir", "timpani", "cymbal"]
    cue = Cue("symphony", tm, bars, chords_, [parts[k] for k in order], rt60=2.6, wet=0.42, predelay=0.024,
              target_lufs=-18.0, st_target=-12.5, fade_out=1.3,
              gates=[(49.40, 50.47, {"vln_gp", "cymbal"})],
              wet_duck=[(49.42, 50.48, 0.1, 0.45)],
              comp=(-6.0, 1.3, 30.0, 400.0),
              master_vol=[(0, 0.0), (7, 0.0), (9, -2.5), (39, -2.5), (41, -3.5), (48, -3.5), (55.5, -1.0),
                          (57.2, 0.0), (59.5, -1.5), (61.5, -3.0), (63.2, -2.5), (64.8, 0.0), (68.5, 0.0),
                          (69.5, -0.8), (71.5, 0.0)],
              landmarks=[(0.0, "intro"), (7.5, "theme"), (19.5, "vln I"), (35.0, "build"), (42.0, "sub p"),
                         (49.4, "GP"), (50.5, "CLIMAX (E)"), (54.2, "6-5"), (58.0, "high pt"), (61.7, "iv"),
                         (66.0, "coda"), (68.4, "celesta"), (74.0, "end")],
              top_parts=("vc", "vln1"), bass_parts=("cb",))
    cue.notes_txt = ("Top line for the outer-voice check: Theme A in the celli (beats 8-40), violins I "
                     "(countermelody, B-section, climax 8va). Bass: contrabasses.")
    return cue


# =========================================================================== cue: opening


def compose_opening() -> Cue:
    tm = TempoMap.const(66, start=10.0 - 12 * 60 / 66)        # beat 12 (bar 4) lands at 10.0 s
    bars = [0, 4, 8, 12, 16, 20, 24]
    c = ctl("Dadd9:7 G/D:4 D:4 Bm7:5", 1)
    parts = []
    cb = Part("cb", "cb", pan=0.3, send=0.3).add(seq("D2:15", 1)).add(seq("B1:5", 16))
    cb.dyn = [(0.9, 0), (3, 26), (12, 32), (16, 30), (18.5, 20), (20.8, 0)]
    parts.append(cb)
    sv = voice_chords(c, 4, 43, 66, bass=[P("D2")] * 3 + [P("B1")])
    st = pad_notes(c, sv, {"vc": [0, 1], "vla": [2, 3]}, vel=50, tail=0.2)
    vc = Part("vc_pad", "vc_slow", pan=0.2, send=0.4).add(st["vc"])
    vla = Part("vla_pad", "vla", pan=-0.1, send=0.4).add(st["vla"])
    for p_ in (vc, vla):
        p_.dyn = [(0.9, 0), (2.5, 30), (6, 42), (9, 38), (11.5, 33), (14, 38), (17.6, 54), (18.6, 34), (20.8, 0)]
    parts += [vc, vla]
    pv = voice_chords(c, 3, 57, 74)
    pad = Part("pad", "halo_pad", pan=0.0, send=0.5, gain_db=-7.0).add(pad_notes(c, pv, {"p": [0, 1, 2]}, 60)["p"])
    pad.dyn = [(1, 30), (5, 90), (11, 70), (14, 84), (17.6, 112), (18.6, 70), (20.8, 25)]
    parts.append(pad)
    glass = Part("shimmer", "shimmer", synth=synth_shimmer, pan=0.0, send=0.7, gain_db=-21.0)
    glass.add(seq("(A5,E6):10", 2, 60)).add(seq("(F#5,C#6):8", 13, 60))
    glass.dyn = [(2, 0), (6, 80), (10, 64), (12, 40), (14, 60), (17.6, 90), (19.5, 30), (21, 0)]
    parts.append(glass)
    cel = Part("celesta", "celesta", pan=0.15, send=0.85, humanize=0.005, gain_db=10.0)
    cel.add(seq("A5:q D6:q F#6:h | E6:q D6:q B5:h", 12, 52, "mel", bar=4, vels=[52, 52, 58, 52, 49, 50]))
    parts.append(cel)
    gl = Part("glock", "glock", pan=-0.2, send=0.85, gain_db=-6.0, humanize=0.005)
    gl.add(seq("A6:q D7:q F#7:h | E7:q D7:q B6:h", 12, 34, bar=4))
    parts.append(gl)
    return Cue("opening", tm, bars, c, parts, rt60=4.2, wet=0.55, predelay=0.03, target_lufs=-17.0,
               fade_out=2.5, comp=(-24.0, 1.4, 40.0, 500.0),
               landmarks=[(3.0, "title in"), (10.0, "celesta"), (11.0, "title out"), (12.5, "dive"),
                          (15.5, "fade")],
               top_parts=("celesta", "pad"), bass_parts=("cb",))


# =========================================================================== cue: lounge


def compose_lounge() -> Cue:
    tm = TempoMap.const(60 / 1.375)                           # 4 beats = 5.5 s per bar
    bars = [0, 4, 8, 12, 16, 20, 24, 28, 32]
    c = ctl("D:4 Bm:4 G:4 A:4 D/F#:4 Bm7:4 Gmaj7:4 A7sus4:2 A:2", 0)
    parts = []
    cb = Part("cb", "cb", pan=0.3, send=0.25)
    cb.add(seq("D2:w | B1:w | G1:w | A1:w | F#1:w | B1:w | G1:w | A1:w", 0, bar=4))
    cb.dyn = [(0, 24)] + [(b + d, v) for b in range(0, 32, 4) for d, v in ((0.2, 26), (2.0, 32), (3.8, 25))]
    parts.append(cb)
    sv = voice_chords(c, 4, 45, 67, bass=bass_of(c, cb.notes))
    st = pad_notes(c, sv, {"vc": [0, 1], "vla": [2, 3]}, vel=48, tail=0.15)
    vc = Part("vc_pad", "vc_slow", pan=0.18, send=0.35).add(st["vc"])
    vla = Part("vla_pad", "vla", pan=-0.12, send=0.35).add(st["vla"])
    sw = [(0, 26)] + [(b + d, v) for b in range(0, 32, 4) for d, v in ((0.3, 30), (2.0, 40), (3.85, 31))]
    vc.dyn = list(sw)
    vla.dyn = [(b, v - 2) for b, v in sw]
    parts += [vc, vla]
    pv = voice_chords(c, 3, 55, 72)
    pad = Part("pad", "warm_pad", pan=0.0, send=0.35, gain_db=-10.0).add(pad_notes(c, pv, {"p": [0, 1, 2]}, 55)["p"])
    pad.dyn = [(0, 80)]
    parts.append(pad)
    drops = [("F#5", 1.5, 34), ("A5", 3.0, 28), ("D6", 4.75, 31), ("B5", 9.5, 30), ("G5", 11.25, 26),
             ("C#6", 13.0, 29), ("E5", 14.75, 25), ("A5", 16.5, 30), ("F#6", 18.25, 24), ("D6", 21.5, 29),
             ("A5", 23.0, 26), ("F#5", 24.5, 28), ("B5", 26.25, 30), ("E6", 29.0, 26), ("C#6", 31.0, 24)]
    pno = Part("piano", "mellow", pan=0.1, send=0.5, humanize=0.006, gain_db=12.0)
    pno.add([Note(b, 2.5, P(p_), v, "mel") for p_, b, v in drops])
    pno.pedal = [(b + 0.05, b + 3.95) for b in range(0, 32, 4)]
    parts.append(pno)
    harp = Part("harp", "harp", pan=-0.35, send=0.4, humanize=0.006, gain_db=7.0)
    harp.add(seq("(D3,A3):w r:w (G2,D3):w r:w (F#2,D3):w r:w (G2,B2):w r:w", 0, 38))
    parts.append(harp)
    return Cue("lounge", tm, bars, c, parts, rt60=2.2, wet=0.38, target_lufs=-18.0, fade_out=2.0,
               comp=(-26.0, 1.4, 40.0, 500.0), top_parts=("vla_pad",), bass_parts=("cb",),
               landmarks=[(4.6, "r01"), (26.95, "q02"), (42.0, "end in film")])


# =========================================================================== cue: alt_kazoo


def compose_alt_kazoo() -> Cue:
    def w(b):
        return 1.0 + 0.12 * rit(b, 6.0, 8.0)
    tm = TempoMap([(0, 0.08), (6, 0.08 + 6 * 60 / 112), (8, 4.6), (10, 5.84)], w)
    bars = [0, 2, 4, 6, 8, 10]
    c = ctl("D:2 Bm:2 G:2 A:2 D:2", 0)
    kz = Part("kazoo", "kazoo", synth=synth_kazoo, pan=0.0, send=0.18, gain_db=-9.0)
    kz.add(seq("A4:e D5:e F#5:q | E5:e D5:e B4:q | B4:e D5:e G5:q | F#5:q E5:q | D5:q. r:e", 0, 100, "mel",
               bar=2, vels=[96, 100, 112, 100, 98, 104, 98, 102, 114, 112, 100, 108]))
    lh = Part("piano_lh", "piano", pan=-0.1, send=0.15, humanize=0.006, gain_db=7.0)
    rh = Part("piano_rh", "piano", pan=0.15, send=0.15, humanize=0.006, gain_db=4.0)
    uke = Part("ukulele", "ukulele", pan=0.35, send=0.18, humanize=0.003, gain_db=2.0)
    shapes = {"D": ("D2", "A2", "(F#3,A3,D4)", ("D4", "F#4", "A4")),
              "Bm": ("B1", "F#2", "(F#3,B3,D4)", ("D4", "F#4", "B4")),
              "G": ("G2", "D2", "(G3,B3,D4)", ("D4", "G4", "B4")),
              "A": ("A2", "C#2", "(A3,C#4,E4)", ("C#4", "E4", "A4"))}
    for (b0, b1, sym) in c[:4]:
        bass1, bass2, ch_, uk = shapes[sym]
        lh.add(seq(f"{bass1}:e r:e {bass2}:e r:e", b0, 74))
        rh.add(seq(f"r:e {ch_}:e r:e {ch_}:e", b0, 58))
        for k, beat in enumerate((b0 + 0.5, b0 + 1.5)):
            order = uk if k % 2 == 0 else uk[::-1]
            uke.add([Note(beat + j * 0.022, 0.4, P(p_), 62 + 6 * (j == 0)) for j, p_ in enumerate(order)])
    lh.add(seq("(D2,D3):q.", 8, 80))
    rh.add(seq("(F#3,A3,D4):q.", 8, 66))
    uke.add([Note(8 + j * 0.03, 1.5, P(p_), 66) for j, p_ in enumerate(("D4", "F#4", "A4"))])
    gl = Part("glock", "glock", pan=0.0, send=0.35, gain_db=5.0).add(seq("D6:q. A6:e", 8, 60))
    return Cue("alt_kazoo", tm, bars, c, [kz, lh, rh, uke, gl], rt60=0.9, wet=0.22, predelay=0.012,
               target_lufs=-16.0, fade_out=0.35, comp=(-16.0, 2.0, 15.0, 200.0),
               top_parts=("kazoo",), bass_parts=("piano_lh",),
               landmarks=[(0.08, "kazoo"), (4.6, "button")])


# =========================================================================== cue: alt_chip


def compose_alt_chip() -> Cue:
    tm = TempoMap.const(150, start=0.03)
    bars = [0, 4, 8, 12, 13.6]
    c = ctl("D:2 Bm:2 G:2 A:2 Gm:1 A7:1 D:2", 0)
    lead = Part("lead", "chip_lead", synth=synth_chip, pan=-0.08, send=0.08, opts={"kind": "lead", "duty": 0.25})
    lead.add(seq("A4:e D5:e F#5:q E5:e D5:e B4:q | B4:e D5:e G5:q F#5:q E5:q | "
                 "G5:q E5:e C#5:e D5:s F#5:s A5:s D6:s D6:q", 0, 112, "mel", bar=4))
    lead.notes[-1].dur = 1.55
    for nt in lead.notes:
        if nt.dur >= 1.0:
            nt.vel = 118
    duty_t = [tm.sec(b) for b in (0, 8, 10)]
    lead.opts["duty"] = lambda t: np.where(t < duty_t[1], 0.25, np.where(t < duty_t[2], 0.125, 0.25))
    echo = Part("echo", "chip_echo", synth=synth_chip, pan=0.35, send=0.08, gain_db=-11.0,
                opts={"kind": "echo", "duty": 0.125, "delay": 60 / 150 * 0.75})
    echo.add([Note(n.beat, n.dur, n.pitch, n.vel) for n in lead.notes])
    arp = Part("arp", "chip_arp", synth=synth_chip, pan=0.25, send=0.06, gain_db=-9.0, opts={"kind": "arp", "duty": 0.5})
    step = 1 / 6        # 16th-note triplet arpeggio steps
    for (b0, b1, sym) in c:
        ch = chord(sym)
        tones = sorted({(ch.root + i) % 12 for i in ch.ivs})
        ps = sorted([57 + ((tn - 57) % 12) for tn in tones])
        b = b0
        k = 0
        while b < b1 - 1e-6:
            if k % 3 != 2:                     # gated: 2 steps on, 1 off per 8th
                arp.notes.append(Note(b, step * 0.95, ps[k % len(ps)], 90))
            b += step
            k += 1
    tri = Part("tri", "chip_tri", synth=synth_chip, pan=0.0, send=0.04, gain_db=-4.5, opts={"kind": "tri"})
    roots = {"D": "D2", "Bm": "B1", "G": "G1", "A": "A1", "Gm": "G1", "A7": "A1"}
    for (b0, b1, sym) in c[:-1]:
        r = P(roots[sym])
        b = b0
        k = 0
        while b < b1 - 1e-6:
            tri.notes.append(Note(b, 0.42, r + (12 if k % 2 else 0), 100))
            b += 0.5
            k += 1
    tri.add([Note(10, 0.5, P("D2"), 100), Note(10.5, 0.5, P("A2"), 100), Note(11, 1.7, P("D2"), 100)])
    nz = Part("noise", "chip_noise", synth=synth_chip, pan=0.05, send=0.05, gain_db=1.0, opts={"kind": "noise"})
    for bar0 in (0, 4, 8):
        for b in (0, 2, 2.5):
            if bar0 + b < 11.9:
                nz.notes.append(Note(bar0 + b, 0.2, 36, 120))
        for b in (1, 3):
            nz.notes.append(Note(bar0 + b, 0.2, 38, 104))
        for k in range(8):
            if bar0 + k * 0.5 < 12:
                nz.notes.append(Note(bar0 + k * 0.5, 0.1, 42, 70 if k % 2 else 52))
    nz.notes += [Note(7.5, 0.2, 38, 90), Note(7.75, 0.2, 38, 100), Note(12, 1, 49, 100), Note(12, 0.2, 36, 120)]
    return Cue("alt_chip", tm, bars, c, [lead, echo, arp, tri, nz], rt60=0.5, wet=0.1, predelay=0.006,
               target_lufs=-16.0, fade_out=0.25, comp=(-15.0, 1.8, 10.0, 150.0),
               top_parts=("lead",), bass_parts=("tri",), landmarks=[(4.83, "level clear")])


# =========================================================================== cue: alt_lofi


def compose_alt_lofi() -> Cue:
    tm = TempoMap.const(80, start=0.15)
    bars = [0, 4, 8, 8.4]
    c = ctl("Dmaj9:3.5 Bm9:2.5 Gmaj9:1.5 Gm6:0.9", 0)
    rh = Part("rhodes", "rhodes", pan=-0.05, send=0.3, humanize=0.01, lazy=0.012)
    rh.add(seq("(D3,F#3,A3,C#4,E4):3.4", 0, 58))
    rh.add(seq("(B2,A3,C#4,D4,F#4):2.4", 3.5, 54))
    rh.add(seq("(G2,F#3,A3,B3,D4):1.45", 6, 52))
    rh.add(seq("(G2,E3,Bb3,D4):1.4", 7.5, 46))
    for i, nt in enumerate(rh.notes):
        nt.beat += 0.03 * (i % 5) / 4        # soft hand-rolled spread
    fl = Part("flute", "flute", pan=0.12, send=0.35, humanize=0.01, lazy=0.035, gain_db=9.0)
    fl.add(seq("A4:q D5:q F#5:h | E5:q D5:q B4:q. r:e", 0, 62, "mel", bar=4, vels=[60, 62, 68, 62, 58, 56]))
    fl.dyn = [(0, 92), (2, 104), (3.6, 88), (4, 96), (6.5, 84), (7.6, 70)]
    bass = Part("sub", "sub_bass", synth=synth_sub, pan=0.0, send=0.05, gain_db=-26.0, lazy=0.01)
    bass.add(seq("D2:3.4", 0, 100)).add(seq("B1:2.4", 3.5, 96)).add(seq("G1:2.3", 6, 96))
    dr = Part("drums", "drums_lofi", synth=synth_drums_lofi, pan=0.0, send=0.1, gain_db=-21.0, lazy=0.006)
    swing = 0.07
    for bar0 in (0, 4):
        for b, v in ((0, 118), (1.75, 92), (2.5, 106)):
            dr.notes.append(Note(bar0 + b, 0.3, 36, v))
        for b in (1, 3):
            dr.notes.append(Note(bar0 + b, 0.3, 38, 104))
        for k in range(8):
            b = k * 0.5 + (swing if k % 2 else 0)
            dr.notes.append(Note(bar0 + b, 0.1, 46 if (bar0 == 4 and k == 7) else 42, 70 if k % 2 == 0 else 50))
        dr.notes.append(Note(bar0 + 3.75 + swing, 0.1, 37, 40))
    dr.notes.append(Note(8, 0.3, 36, 96))

    def post(x, cue):
        rng = np.random.default_rng(31)
        x = np.tanh(1.5 * x) / 1.5
        x = lp(x, 3300)
        x = hp(x, 45)
        x = wow_flutter(x, 8.0, 0.55, 2.2, 6.4)
        mid = (x[:, 0] + x[:, 1]) / 2
        side = (x[:, 0] - x[:, 1]) / 2 * 0.65
        x = np.stack([mid + side, mid - side], axis=1)
        vin = lp(synth_vinyl(len(x), rng, density=10.0, hiss_db=-40.0), 7000)
        rm = np.sqrt(np.mean(x ** 2)) + 1e-9
        return x + vin * (rm * db(-24.0) / (np.sqrt(np.mean(vin ** 2)) + 1e-12))

    return Cue("alt_lofi", tm, bars, c, [rh, fl, bass, dr], rt60=1.1, wet=0.25, predelay=0.015,
               target_lufs=-16.0, fade_in=0.06, fade_out=0.45, post=post, comp=(-16.0, 2.2, 8.0, 160.0),
               top_parts=("flute",), bass_parts=("sub",), landmarks=[(0.15, "bar 1"), (3.15, "bar 2")])


# =========================================================================== cue: alt_theremin


def compose_alt_theremin() -> Cue:
    tm = TempoMap.const(60)
    bars = [0, 1.8]
    c = ctl("D5:1.8", 0)
    th = Part("theremin", "theremin", synth=synth_theremin, pan=0.0, send=0.45, gain_db=-16.0)
    th.opts["path"] = [(0.0, 52.0), (0.15, 69.6), (0.24, 68.9), (0.38, 69.0), (0.5, 74.7), (0.58, 73.9),
                       (0.72, 74.0), (0.84, 78.8), (0.94, 77.9), (1.3, 78.0), (1.72, 63.0), (1.8, 62.0)]
    th.opts["amp_t"] = [0.0, 0.07, 0.4, 1.0, 1.3, 1.55, 1.78, 1.8]
    th.opts["amp_v"] = [0.0, 0.75, 0.85, 1.0, 1.0, 0.75, 0.0, 0.0]
    th.notes = [Note(0.0, 0.42, P("A4"), 100, "mel"), Note(0.42, 0.4, P("D5"), 100, "mel"),
                Note(0.82, 0.48, P("F#5"), 110, "mel"), Note(1.3, 0.45, P("D#4"), 80)]
    trem = Part("low_trem", "vc_trem", pan=0.15, send=0.4, humanize=0.003)
    trem.add(seq("(D2,A2,D3):1.75", 0, 110))
    trem.dyn = [(0, 112), (0.12, 52), (1.0, 92), (1.45, 70), (1.72, 0)]
    cbt = Part("bass_trem", "cb_trem", pan=0.3, send=0.35, humanize=0.003, gain_db=-2.0)
    cbt.add(seq("D2:1.75", 0, 110))
    cbt.dyn = [(0, 112), (0.12, 50), (1.0, 90), (1.72, 0)]
    timp = Part("timpani", "timpani", pan=0.1, send=0.4).add([Note(0.0, 1.5, P("D2"), 110)])
    return Cue("alt_theremin", tm, bars, c, [th, trem, cbt, timp], rt60=2.3, wet=0.4, predelay=0.02,
               target_lufs=-16.0, fade_out=0.12, comp=(-16.0, 1.6, 15.0, 200.0),
               top_parts=("theremin",), bass_parts=("low_trem",), landmarks=[(0.84, "F#5 wail"), (1.3, "fall")])


# =========================================================================== cue: alt_lullaby


def compose_alt_lullaby() -> Cue:
    def w(b):
        return 1.0 + 0.06 * bump(b, 3.0, 0.5) + 0.06 * bump(b, 11.0, 0.5) + 0.3 * rit(b, 12.0, 16.0)
    tm = TempoMap([(0, 0.12), (12, 8.12), (16, 11.25)], w)
    bars = [0, 4, 8, 12, 16]
    c = ctl("D:4 Bm:4 G:4 A:3.2 D:0.8", 0)
    mb = Part("musicbox", "musicbox", pan=0.05, send=0.45, humanize=0.004)
    mb.add(transpose(seq(THEME_BARS_1_4, 0, 74, "mel", bar=4, vels=[70, 72, 80, 72, 70, 68, 70, 74, 84, 82, 74]), 12))
    cel = Part("celesta", "celesta", pan=-0.12, send=0.45, humanize=0.008, gain_db=-4.0)
    # soft broken chords above a held tonic pedal (celesta stays >= C4): D | Bm/D | G/D | A/C# -> D
    cel.add(seq("D4:w | D4:w | D4:w | C#4:3.2 r:0.8", 0, 34, bar=4))
    cel.add(seq("r:q A4:q D5:q A4:q | r:q F#4:q B4:q F#4:q | r:q G4:q B4:q G4:q | r:q E4:q A4:q r:q", 0, 30,
                bar=4, vels=[32, 34, 29, 31, 33, 28, 31, 33, 28, 30, 32]))
    cel.add(seq("(D4,A4):2", 15.2, 34))
    pad = Part("pad", "warm_pad", pan=0.0, send=0.4, gain_db=-15.0)
    pv = voice_chords(c, 3, 55, 71)
    pad.add(pad_notes(c, pv, {"p": [0, 1, 2]}, 50, tail=0.5)["p"])
    pad.dyn = [(0, 40), (3, 64), (12, 60), (16, 40), (17, 0)]
    return Cue("alt_lullaby", tm, bars, c, [mb, cel, pad], rt60=1.7, wet=0.36, predelay=0.015,
               target_lufs=-16.0, fade_out=1.1, comp=(-18.0, 1.6, 20.0, 300.0),
               top_parts=("musicbox",), bass_parts=("celesta",),
               landmarks=[(5.0, "rae stands"), (8.12, "F#->E"), (9.6, "E rings")])


# =========================================================================== cue: coda


def compose_coda() -> Cue:
    def w(b):
        return (1.0 + 0.1 * bump(b, 0.0, 0.5) + 0.08 * bump(b, 3.5, 0.6) + 0.08 * bump(b, 7.5, 0.6)
                + 0.1 * bump(b, 11.5, 0.7) + 0.28 * rit(b, 13.0, 16.0))
    tm = TempoMap([(0, 0.35), (16, 12.72)], w)               # final D chord lands on end_card
    bars = [0, 4, 8, 12, 16, 20, 24]
    c = ctl("D:4 Bm:4 G:4 A:4 D:9", 0)
    rh = Part("piano_rh", "piano", pan=0.06, send=0.42, humanize=0.006)
    mel = seq(THEME_BARS_1_4 + " | D5:w", 0, 50, "mel", bar=4, vels=[44, 46, 52, 47, 44, 42, 45, 48, 54, 52, 44, 42])
    rh.add(mel)
    rh.add(seq("r:h A4:h | r:h F#4:h | r:h B4:h | A4:h C#5:h | (F#4,A4):w", 0, 32, bar=4))
    rh.notes[-1].dur = rh.notes[-2].dur = 7.5
    [n_ for n_ in rh.notes if n_.beat == 16 and n_.tag == "mel"][0].dur = 7.5
    lh = Part("piano_lh", "piano", pan=-0.08, send=0.42, humanize=0.008)
    lh.add(seq("D2:e A2:e F#3:h. | B1:e F#2:e D3:h. | G1:e D2:e B2:h. | A1:e E2:e C#3:h. | D2:e A2:e (F#3,A3):h.",
               0, 34, bar=4, vels=[36, 30, 32, 35, 29, 31, 35, 29, 32, 36, 30, 33, 34, 28, 30]))
    for nt in lh.notes:
        if nt.beat >= 16:
            nt.dur = 7.5
    ped = [(b + 0.06, b + 3.96) for b in (0, 4, 8, 12)] + [(16.06, 26)]
    rh.pedal = lh.pedal = ped

    def felt(x):
        x = lp(x, 2600, order=2)
        return filt(x, sos_shelf(180, 2.0, high=False))
    rh.eq = lh.eq = felt
    pad = Part("strings", "vla", pan=0.0, send=0.5, gain_db=-8.0).add(seq("(A3,D4,F#4):8", 16, 60))
    padc = Part("strings_lo", "vc_slow", pan=0.2, send=0.5, gain_db=-9.0).add(seq("D3:8", 16, 60))
    pad.dyn = padc.dyn = [(15.6, 0), (17, 30), (20, 27), (23, 0)]
    pad.eq = padc.eq = lambda x: lp(x, 4500)
    return Cue("coda", tm, bars, c, [rh, lh, pad, padc], rt60=2.3, wet=0.36, predelay=0.02,
               target_lufs=-18.0, fade_out=4.0, comp=(-22.0, 1.5, 30.0, 400.0),
               top_parts=("piano_rh",), bass_parts=("piano_lh",),
               landmarks=[(2.2, "q13"), (12.72, "end card"), (15.8, "fade")])


COMPOSERS = {"opening": compose_opening, "lounge": compose_lounge, "symphony": compose_symphony,
             "alt_kazoo": compose_alt_kazoo, "alt_chip": compose_alt_chip, "alt_lofi": compose_alt_lofi,
             "alt_theremin": compose_alt_theremin, "alt_lullaby": compose_alt_lullaby, "coda": compose_coda}


# =========================================================================== render pipeline


def render_stems(cue: Cue, n: int) -> dict:
    stems = {}
    used = set()
    sf_parts = [p for p in cue.parts if p.synth is None]
    with ThreadPoolExecutor(MAX_JOBS) as ex:
        futs = {p.name: ex.submit(render_sf_part, p, cue, n, zlib.crc32(f"{cue.name}/{p.name}".encode()))
                for p in sf_parts}
        for p in cue.parts:
            if p.synth is not None:
                stems[p.name] = p.synth(p, cue, n)
        for k, f in futs.items():
            stems[k], path = f.result()
            used.update({path.name, path.with_suffix(".scale").name})
    cdir = CACHE_DIR / cue.name
    if cdir.exists():                         # prune stale stems of this cue
        for f in cdir.iterdir():
            if f.name not in used:
                f.unlink()
    return stems


def _gate_env(n, t0, t1, fade_out=0.04, fade_in=0.025):
    g = np.ones(n)
    a, b = int(t0 * SR), int(t1 * SR)
    fo, fi = int(fade_out * SR), int(fade_in * SR)
    g[a:a + fo] = np.minimum(g[a:a + fo], np.linspace(1, 0, len(g[a:a + fo])))
    g[a + fo:b - fi] = 0.0
    seg = g[b - fi:b]
    g[b - fi:b] = np.linspace(0, 1, len(seg))
    return g


def process_stem(p: Part, cue: Cue, x: np.ndarray) -> np.ndarray:
    """Per-stem chain: tone EQ -> fader automation -> grand-pause gates -> pan -> gain."""
    n = len(x)
    if p.eq is not None:
        x = p.eq(x)
    if p.vol:
        tt = np.array([cue.tmap.sec(b) for b, _ in p.vol])
        vv = np.array([v for _, v in p.vol], float)
        x = x * db(np.interp(np.arange(n) / SR, tt, vv))[:, None]
    for (t0, t1, keep) in cue.gates:
        if p.name not in keep:
            x = x * _gate_env(n, t0, t1)[:, None]
    return pan_st(x, p.pan) * db(p.gain_db)


def mix_cue(cue: Cue, stems: dict, n: int):
    dry = np.zeros((n, 2))
    send = np.zeros((n, 2))
    levels = {}
    mv = None
    if cue.master_vol:
        tt = np.array([cue.tmap.sec(b) for b, _ in cue.master_vol])
        mv = db(np.interp(np.arange(n) / SR, tt, np.array([v for _, v in cue.master_vol], float)))[:, None]
    for p in cue.parts:
        x = process_stem(p, cue, stems[p.name])
        if mv is not None:
            x = x * mv
        act = np.sqrt(np.mean(x ** 2, axis=1))
        on = act > (np.max(act) * 0.05 if np.max(act) > 0 else 1)
        levels[p.name] = 20 * np.log10(np.sqrt(np.mean(x[on] ** 2)) + 1e-12) if on.any() else -120.0
        dry += x
        send += x * p.send
    ir = make_ir(cue.rt60, seed=len(cue.name), predelay=cue.predelay)
    wet = convolve(send, ir) * cue.wet
    for (t0, t1, g, ramp) in cue.wet_duck:
        env = np.ones(n)
        a, b = int(t0 * SR), int(t1 * SR)
        r = min(b - a, int(ramp * SR))
        env[a:a + r] = np.exp(np.linspace(0, math.log(g), r))
        env[a + r:b] = g
        k = int(0.06 * SR)
        env[b:b + k] = np.linspace(g, 1, len(env[b:b + k]))
        wet *= env[:, None]
    x = dry + wet
    if cue.post is not None:
        x = cue.post(x, cue)
    return x, levels


def master(cue: Cue, x: np.ndarray):
    n = len(x)
    x = hp(x, 18.0)                                                    # DC / subsonic blocker
    pw = np.concatenate([[0.0], np.cumsum(np.mean(x ** 2, axis=1))])
    k = 4800
    pk_rms = 10 * np.log10(np.max((pw[k:] - pw[:-k]) / k) + 1e-12)       # loudest 100 ms
    th, ratio, att, rel = cue.comp
    x = compressor(x, pk_rms + th, ratio, att, rel)
    # loudness normalization (integrated, or short-term max for the symphony)
    for _ in range(4):
        if cue.st_target is not None:
            _, st = short_term(x)
            err = cue.st_target - np.max(st)
        else:
            err = cue.target_lufs - integrated_lufs(x)
        x = limiter(x * db(err), -1.2)
        if abs(err) < 0.15:
            break
    # fades + exact length
    fi, fo = int(cue.fade_in * SR), int(cue.fade_out * SR)
    env = np.ones(n)
    if fi > 0:
        env[:fi] = np.linspace(0, 1, fi) ** 2
    if fo > 0:
        env[-fo:] = np.minimum(env[-fo:], 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, fo)))
    env[-1] = 0.0
    x = x * env[:, None]
    return x.astype(np.float32)


# =========================================================================== analysis outputs


def envelopes(x: np.ndarray, cue: Cue) -> dict:
    n = len(x)
    nf = int(math.ceil(cue.length * FPS - 1e-9))
    win = int(SR / FPS)

    def env_of(sig):
        p = np.mean(sig ** 2, axis=1)
        c = np.concatenate([[0.0], np.cumsum(p)])
        vals = []
        for i in range(nf):
            a = int(max(0, (i + 0.5) * SR / FPS - win))
            b = int(min(n, (i + 0.5) * SR / FPS + win))
            vals.append((c[b] - c[a]) / max(1, b - a))
        d = 10 * np.log10(np.array(vals) + 1e-14)
        d -= np.max(d)
        e = np.clip((d + 42.0) / 42.0, 0, 1)
        out = np.empty_like(e)
        cur = 0.0
        rel = math.exp(-1 / (0.12 * FPS))
        for i, v in enumerate(e):
            cur = v if v > cur else v + (cur - v) * rel
            out[i] = cur
        return [round(float(v), 4) for v in out]

    lo_ = lp(x, 200, order=4)
    hi_ = hp(x, 3000, order=4)
    onsets = []
    for p in cue.parts:
        for nt in p.notes:
            if nt.tag == "mel":
                t = cue.tmap.sec(nt.beat) + p.lazy
                if 0 <= t < cue.length:
                    onsets.append(t)
    onsets = sorted(onsets)
    ded = []
    for t in onsets:
        if not ded or t - ded[-1] > 0.05:
            ded.append(round(t, 3))
    beats, downs = [], []
    b = math.floor(cue.tmap.beat(0.0))
    while True:
        t = cue.tmap.sec(b)
        if t >= cue.length:
            break
        if t >= 0:
            beats.append(round(t, 3))
        b += 1
    for bb in cue.bars:
        t = cue.tmap.sec(bb)
        if 0 <= t < cue.length:
            downs.append(round(t, 3))
    return {"rms": env_of(x), "low": env_of(lo_), "high": env_of(hi_), "onsets": ded, "beats": beats,
            "downbeats": downs}


def analysis_png(cue: Cue, x: np.ndarray, env: dict, path: Path):
    from PIL import Image, ImageDraw
    W_, SPEC_H, ENV_H, LU_H, PAD = 1600, 260, 150, 120, 24
    mono = x.mean(axis=1)
    f, t, S = signal.spectrogram(mono, SR, nperseg=2048, noverlap=1536)
    S = 10 * np.log10(S + 1e-14)
    lf = np.logspace(np.log10(40), np.log10(16000), SPEC_H)
    idx = np.clip(np.searchsorted(f, lf), 0, len(f) - 1)
    S = S[idx][::-1]
    S = np.clip((S + 120) / 95, 0, 1)
    cols = np.clip((np.arange(W_) / W_ * S.shape[1]).astype(int), 0, S.shape[1] - 1)
    S = S[:, cols]
    rgb = np.stack([S ** 0.8 * 255, S ** 1.6 * 230, (1 - S) * S * 3.2 * 255], axis=-1).clip(0, 255).astype(np.uint8)
    H_ = SPEC_H + ENV_H + LU_H + PAD * 2 + 40
    img = Image.new("RGB", (W_, H_), (12, 12, 18))
    img.paste(Image.fromarray(rgb), (0, 20))
    d = ImageDraw.Draw(img)
    L = cue.length

    def X(sec):
        return int(sec / L * (W_ - 1))
    d.text((6, 3), f"{cue.name}  {L:.2f}s  spectrogram 40 Hz-16 kHz (log)", fill=(220, 220, 220))
    y0 = 20 + SPEC_H + PAD
    d.rectangle([0, y0, W_, y0 + ENV_H], fill=(20, 20, 28))
    for lvl in (0.25, 0.5, 0.75):
        yy = y0 + ENV_H - int(lvl * ENV_H)
        d.line([(0, yy), (W_, yy)], fill=(45, 45, 60))
    for key, colr in (("low", (240, 150, 60)), ("high", (90, 200, 255)), ("rms", (255, 255, 255))):
        arr = env[key]
        pts = [(X((i + 0.5) / FPS), y0 + ENV_H - int(v * (ENV_H - 2))) for i, v in enumerate(arr)]
        d.line(pts, fill=colr, width=2 if key == "rms" else 1)
    for o in env["onsets"]:
        d.line([(X(o), y0), (X(o), y0 + 8)], fill=(255, 230, 120))
    d.text((6, y0 + 2), "env rms (white) low (orange) high (blue), onsets (yellow ticks)", fill=(200, 200, 200))
    y1 = y0 + ENV_H + PAD
    tt, st = short_term(x.astype(np.float64))
    d.rectangle([0, y1, W_, y1 + LU_H], fill=(20, 24, 22))
    for lvl in (-12, -18, -24, -36):
        yy = y1 + LU_H - int((lvl + 48) / 48 * LU_H)
        d.line([(0, yy), (W_, yy)], fill=(50, 60, 55))
        d.text((W_ - 60, yy - 11), f"{lvl} LUFS", fill=(140, 160, 150))
    pts = [(X(a), y1 + LU_H - int(np.clip((b + 48) / 48, 0, 1) * LU_H)) for a, b in zip(tt, st)]
    d.line(pts, fill=(120, 230, 150), width=2)
    d.text((6, y1 + 2), "short-term loudness (3 s)", fill=(200, 200, 200))
    for sec, lab in cue.landmarks:
        xx = X(sec)
        d.line([(xx, 20), (xx, y1 + LU_H)], fill=(255, 80, 120), width=1)
        d.text((xx + 2, 20 + SPEC_H - 12), lab, fill=(255, 140, 170))
    for s in range(0, int(L) + 1):
        xx = X(s)
        d.line([(xx, H_ - 18), (xx, H_ - 12)], fill=(180, 180, 180))
        if L < 12 or s % 5 == 0:
            d.text((xx + 1, H_ - 12), str(s), fill=(180, 180, 180))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def dyn_mark(v):
    for th, m in ((1, "-"), (30, "ppp"), (42, "pp"), (56, "p"), (70, "mp"), (84, "mf"), (100, "f"), (116, "ff")):
        if v < th:
            return m
    return "fff"


def check_outer(cue: Cue):
    """Parallel 5ths/8ves between the outer voices, evaluated at every onset of either line.
    Two top lines are checked: the melody (notes tagged 'mel' in top_parts) and the actual
    highest sounding note of top_parts. Bass = lowest note of bass_parts."""
    bass = [nt for p in cue.parts if p.name in cue.bass_parts for nt in p.notes]

    def sounding(ns, t, f):
        c = [x.pitch for x in ns if x.beat - 1e-6 <= t < x.beat + x.dur - 1e-6]
        return f(c) if c else None
    issues = []
    allp = [nt for p in cue.parts if p.name in cue.top_parts for nt in p.notes]
    for label, top in (("melody", [nt for nt in allp if nt.tag == "mel"]), ("top", allp)):
        if not top:
            continue
        times = sorted({round(nt.beat, 4) for nt in top + bass})
        seqv = [(t, sounding(top, t, max), sounding(bass, t, min)) for t in times]
        for (t0, a0, b0), (t1, a1, b1) in zip(seqv, seqv[1:]):
            if None in (a0, b0, a1, b1) or a0 == a1 or b0 == b1:
                continue
            i0, i1 = (a0 - b0) % 12, (a1 - b1) % 12
            if i0 == i1 and i0 in (0, 7) and (a1 - a0) * (b1 - b0) > 0:
                msg = (f"parallel {'8ve' if i0 == 0 else '5th'} beat {t0:g}->{t1:g}: "
                       f"{pname(a0)}/{pname(b0)} -> {pname(a1)}/{pname(b1)}")
                if msg not in [m.split('] ', 1)[-1] for m in issues]:
                    issues.append(f"[{label}] {msg}")
    return issues


def check_ranges(cue: Cue):
    out = []
    for p in cue.parts:
        lo_, hi_ = (INST[p.inst].lo, INST[p.inst].hi) if p.inst in INST else SYNTH_RANGES.get(p.inst, (0, 127))
        if p.inst in ("cymbal", "chip_noise", "drums_lofi"):
            continue
        for nt in p.notes:
            if not lo_ <= nt.pitch <= hi_:
                out.append(f"{p.name}: {pname(nt.pitch)} at beat {nt.beat:g} outside {pname(lo_)}-{pname(hi_)}")
    return out


def chord_at(cue: Cue, b):
    for (b0, b1, s) in cue.chords:
        if b0 - 1e-6 <= b < b1 - 1e-6:
            return s
    return None


def score_dump(cue: Cue, path: Path, stats: dict):
    tm = cue.tmap
    L = []
    L.append(f"SCORE  {cue.name}   length {cue.length:.2f} s   (generated by audio/music.py)")
    L.append("=" * 100)
    if cue.notes_txt:
        L.append(cue.notes_txt)
    L.append("Parts: " + ", ".join(f"{p.name} [{INST[p.inst].label if p.inst in INST else 'numpy ' + p.inst}]"
                                    for p in cue.parts))
    L.append("Notation: PITCH@beat(1-based in bar) len=beats v=velocity ; dyn = CC2/CC11 dynamic at bar start")
    L.append("")
    for bi in range(len(cue.bars) - 1):
        b0, b1 = cue.bars[bi], cue.bars[bi + 1]
        t0, t1 = tm.sec(b0), tm.sec(b1)
        if t0 >= cue.length:
            break
        chs = [s for (c0, c1, s) in cue.chords if c0 < b1 - 1e-6 and c1 > b0 + 1e-6]
        L.append(f"Bar {bi + 1:>2}  beats {b0:g}-{b1:g}  {t0:6.2f}-{t1:6.2f} s  ~{tm.bpm(b0 + 0.01):.0f} bpm   "
                 f"chord: {' | '.join(chs) if chs else '-'}")
        for p in cue.parts:
            ns = sorted([x for x in p.notes if b0 - 1e-6 <= x.beat < b1 - 1e-6], key=lambda x: (x.beat, x.pitch))
            if not ns and not p.dyn:
                continue
            groups = {}
            for x in ns:
                groups.setdefault(round(x.beat, 4), []).append(x)
            items = []
            for bt, g in groups.items():
                ps = ",".join(pname(x.pitch) for x in g)
                ps = f"({ps})" if len(g) > 1 else ps
                items.append(f"{ps}@{bt - b0 + 1:g} len={g[0].dur:g} v={g[0].vel}")
            dy = ""
            if p.dyn:
                v = dyn_at(p.dyn, b0 + 0.01)
                dy = f"  [dyn {dyn_mark(v)} {v:.0f}]"
            if items or (p.dyn and dyn_at(p.dyn, b0 + 0.01) > 0):
                txt = "  ".join(items) if items else "(held)"
                L.append(f"    {p.name:10s}{dy:16s} {txt}")
        # melody vs harmony analysis for this bar
        mel = sorted([x for p in cue.parts if p.name in cue.top_parts for x in p.notes
                      if x.tag == "mel" and b0 - 1e-6 <= x.beat < b1 - 1e-6], key=lambda x: x.beat)
        ana = []
        seen = set()
        for x in mel:
            k = round(x.beat, 3)
            if k in seen:
                continue
            seen.add(k)
            s = chord_at(cue, x.beat)
            ch = chord(s) if s else None
            if ch is None:
                ana.append(f"{pname(x.pitch)}:-")
                continue
            ct = x.pitch % 12 in ch.pcs
            strong = abs((x.beat - b0) % 2) < 1e-6
            ana.append(f"{pname(x.pitch)}{'' if ct else '(NCT' + (',strong' if strong else '') + ')'}/{s}")
        if ana:
            L.append(f"    {'~melody':10s}{'':16s} " + "  ".join(ana))
        L.append("")
    L.append("-" * 100)
    L.append("CHECKS")
    for k, v in stats.items():
        if isinstance(v, list):
            L.append(f"  {k}: {len(v)}")
            for it in v[:60]:
                L.append(f"     {it}")
        else:
            L.append(f"  {k}: {v}")
    path.write_text("\n".join(L) + "\n")


def tempo_report(cue: Cue):
    rows = []
    for bi in range(len(cue.bars) - 1):
        b0, b1 = cue.bars[bi], cue.bars[bi + 1]
        bpms = [cue.tmap.bpm(b0 + (b1 - b0) * k / 4 + 0.01) for k in range(4)]
        rows.append(f"bar {bi + 1}: " + "/".join(f"{v:.0f}" for v in bpms))
    return rows


# =========================================================================== main


def render_cue(name: str) -> dict:
    cue = COMPOSERS[name]()
    n = int(round(cue.length * SR))
    stems = render_stems(cue, n)
    x, levels = mix_cue(cue, stems, n)
    y = master(cue, x)
    assert len(y) == n and y.shape[1] == 2, (name, y.shape)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    sf.write(MUSIC_DIR / f"{name}.wav", y, SR, subtype="FLOAT")
    # verify what was written
    chk, sr = sf.read(MUSIC_DIR / f"{name}.wav", always_2d=True, dtype="float32")
    assert sr == SR and chk.shape == (n, 2), (name, chk.shape)
    assert abs(len(chk) / SR - MUSIC_CUES[name]) < 1e-9
    peak = 20 * math.log10(float(np.max(np.abs(chk))) + 1e-12)
    lufs = integrated_lufs(chk.astype(np.float64))
    _, st = short_term(chk.astype(np.float64))
    env = envelopes(chk.astype(np.float64), cue)
    # MIDI of the whole score (for inspection)
    rng = np.random.default_rng(0)
    tracks = [events_to_track(part_events(p, cue, rng), 0, p.name) for p in cue.parts if p.synth is None]
    if tracks:
        midi_file(tracks).save(MUSIC_DIR / f"{name}.mid")
    stats = {"duration_s": f"{len(chk) / SR:.6f} (target {MUSIC_CUES[name]})",
             "peak_dBFS": f"{peak:.2f}", "integrated_LUFS": f"{lufs:.2f}", "max_short_term_LUFS": f"{np.max(st):.2f}",
             "stem_levels_dBFS(pre-master)": ", ".join(f"{k} {v:.1f}" for k, v in levels.items()),
             "tempo_bpm_per_quarter_bar": tempo_report(cue),
             "range_violations": check_ranges(cue), "outer_voice_parallels": check_outer(cue)}
    score_dump(cue, MUSIC_DIR / f"score_{name}.txt", stats)
    analysis_png(cue, chk.astype(np.float64), env, TEST_DIR / f"{name}.png")
    print(f"{name:13s} {len(chk) / SR:7.3f}s  peak {peak:6.2f} dBFS  integrated {lufs:6.2f} LUFS  "
          f"max short-term {np.max(st):6.2f} LUFS  onsets {len(env['onsets'])}  "
          f"ranges {len(stats['range_violations'])}  parallels {len(stats['outer_voice_parallels'])}", flush=True)
    return env


def main(argv):
    global USE_CACHE
    args = [a for a in argv if not a.startswith("--")]
    if "--no-cache" in argv:
        USE_CACHE = False
    names = args or list(MUSIC_CUES)
    for nm in names:
        if nm not in COMPOSERS:
            raise SystemExit(f"unknown cue {nm!r}; choose from {', '.join(COMPOSERS)}")
    missing = set(MUSIC_CUES) - set(COMPOSERS)
    if missing:
        raise SystemExit(f"no composer for {missing}")
    envs = {}
    p = Path(MUSIC_ENV)
    if p.exists():
        try:
            envs = json.loads(p.read_text())
        except json.JSONDecodeError:
            envs = {}
    for nm in names:
        envs[nm] = render_cue(nm)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({k: envs[k] for k in MUSIC_CUES if k in envs}, separators=(",", ":")))
    print(f"wrote {p}")


if __name__ == "__main__":
    main(sys.argv[1:])
