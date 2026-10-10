"""Shared machinery for audio/music.py ("ANGER"): notation, voicing, tempo maps, numpy synths, MIDI ->
fluidsynth stem rendering, mixing/mastering, envelopes, analysis images and score dumps.

Adapted from ../if-you-have-time/audio/music.py (same Cue/Part/TempoMap model), extended with:
    * per-part pitch-bend automation (RPN bend range) for glissandi / straining slides / comic bends,
    * GM drum-kit parts on MIDI channel 10 (Orchestra kit: concert snare, cymbals, toms),
    * numpy heartbeat / riser / drone synths, hit-locked percussion that ignores humanization,
    * a dialogue "carve" on the master (300-3000 Hz band dipped inside the timeline's line windows),
    * "cut dead" endings (a 4 ms fade on the final samples, reverb included) and hit verification.
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
from config import BUILD, FPS, MUSIC_DIR, MUSIC_ENV, SOUNDFONT, SOUNDFONT_ALT, SR, TIMELINE  # noqa: E402
from script_data import MUSIC_CUES  # noqa: E402

TEST_DIR = BUILD / "tests" / "music"
CACHE_DIR = MUSIC_DIR / ".cache"
MAX_JOBS = 2                 # machine is shared: never more than 2 fluidsynth processes
FS_GAIN = 0.35
RENDER_VERSION = "anger-v1"        # bump to invalidate the fluidsynth stem cache
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
        "9": (0, 2, 4, 7, 10), "dim": (0, 3, 6), "5": (0, 7), "(no5)": (0, 4),
        "6add9": (0, 2, 4, 7, 9), "m11": (0, 3, 5, 7, 10)}


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
    "vln_trem":  Inst(21, 44, 55, 100, True, "Violins I tremolo (expr)"),
    "vln_pizz":  Inst(20, 45, 55, 96, False, "Violins pizzicato"),
    "vln2":      Inst(26, 49, 55, 96, True, "Violins II (slow, expr)"),
    "vln2_fast": Inst(26, 48, 55, 96, True, "Violins II (fast, expr)"),
    "vln2_trem": Inst(26, 44, 55, 96, True, "Violins II tremolo (expr)"),
    "vla":       Inst(31, 49, 48, 88, True, "Violas (slow, expr)"),
    "vla_fast":  Inst(31, 48, 48, 88, True, "Violas (fast, expr)"),
    "vla_trem":  Inst(31, 44, 48, 88, True, "Violas tremolo (expr)"),
    "vla_pizz":  Inst(30, 45, 48, 84, False, "Violas pizzicato"),
    "vc":        Inst(41, 48, 36, 81, True, "Celli (fast, expr)"),
    "vc_slow":   Inst(41, 49, 36, 81, True, "Celli (slow, expr)"),
    "vc_trem":   Inst(41, 44, 36, 81, True, "Celli tremolo (expr)"),
    "vc_pizz":   Inst(40, 45, 36, 72, False, "Celli pizzicato"),
    "cb":        Inst(51, 49, 28, 67, True, "Contrabasses (slow, expr)"),
    "cb_fast":   Inst(51, 48, 28, 67, True, "Contrabasses (fast, expr)"),
    "cb_trem":   Inst(51, 44, 28, 67, True, "Contrabasses tremolo (expr)"),
    "cb_pizz":   Inst(50, 45, 28, 67, False, "Contrabasses pizzicato"),
    # winds / brass / voices
    "flute":     Inst(17, 73, 60, 96, True, "Flute (expr)"),
    "oboe":      Inst(17, 68, 58, 91, True, "Oboe (expr)"),
    "clarinet":  Inst(17, 71, 50, 89, True, "Clarinet (expr)"),
    "bassoon":   Inst(17, 70, 34, 72, True, "Bassoon (expr)"),
    "bassoon_st": Inst(0, 70, 34, 72, False, "Bassoon (staccato, velocity only)"),
    "horns":     Inst(17, 60, 35, 77, True, "French horns (expr)"),
    "trumpet":   Inst(17, 56, 54, 86, True, "Trumpets (expr)"),
    "brass":     Inst(17, 61, 40, 82, True, "Brass section (expr)"),
    "trombone":  Inst(17, 57, 40, 72, True, "Trombones (expr)"),
    "tuba":      Inst(17, 58, 26, 65, True, "Tuba (expr)"),
    "tuba_st":   Inst(0, 58, 26, 65, False, "Tuba (short notes, velocity only)"),
    "choir":     Inst(17, 52, 40, 81, True, "Choir aahs (expr)"),
    "oohs":      Inst(17, 53, 40, 81, True, "Choir oohs (expr)"),
    # keys / plucked / mallets / percussion
    "piano":     Inst(0, 0, 21, 108, False, "Grand piano"),
    "mellow":    Inst(8, 0, 21, 108, False, "Mellow grand piano"),
    "celesta":   Inst(0, 8, 60, 108, False, "Celesta"),
    "glock":     Inst(0, 9, 79, 108, False, "Glockenspiel"),
    "musicbox":  Inst(0, 10, 60, 108, False, "Music box"),
    "xylo":      Inst(0, 13, 65, 108, False, "Xylophone"),
    "marimba":   Inst(0, 12, 45, 96, False, "Marimba"),
    "harp":      Inst(0, 46, 23, 103, False, "Harp"),
    "timpani":   Inst(0, 47, 38, 57, False, "Timpani"),
    "bass_drum": Inst(8, 116, 24, 60, False, "Concert bass drum (gran cassa)"),
    "taiko":     Inst(0, 116, 24, 72, False, "Taiko drum"),
    "rev_cym":   Inst(0, 119, 48, 72, False, "Reverse cymbal"),
    "tblocks":   Inst(1, 115, 60, 63, False, "Temple blocks"),
    "kit":       Inst(128, 48, 27, 87, False, "Orchestra kit (MIDI ch 10: 38 snare, 49/57 cymbals)"),
    # pads
    "warm_pad":  Inst(0, 89, 36, 96, False, "Warm pad"),
    "halo_pad":  Inst(0, 94, 36, 96, False, "Halo pad"),
    "glass_pad": Inst(17, 92, 36, 96, True, "Bowed glass (expr)"),
}
SYNTH_RANGES = {"shimmer": (60, 100), "bell": (60, 108), "sub_bass": (28, 52), "sub_pedal": (14, 52),
                "drone": (14, 60),
                "whale": (36, 84), "boom": (20, 60)}


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
    bend: list = field(default_factory=list)  # [(beat, cents)] pitch-bend automation (whole part)
    bend_range: int = 2                       # semitones (sent as RPN 0)

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
    gates: list = field(default_factory=list)   # [(t0, t1, {part names kept open}[, release s])]
    wet_duck: list = field(default_factory=list)  # [(t0, t1, gain, ramp_s)] extra decay on the reverb return
    master_vol: list = field(default_factory=list)  # [(beat, dB)] whole-cue fader (pre-reverb)
    post: object = None               # callable(stereo, cue) -> stereo, after reverb
    send_hp: float = 0.0              # >0: high-pass the reverb send (Hz) so the hall never blooms in the sub
    comp: tuple = (-22.0, 1.6, 25.0, 300.0)       # threshold dB (rel. to peak RMS), ratio, att ms, rel ms
    landmarks: list = field(default_factory=list)  # [(sec, label)]
    top_parts: tuple = ()
    bass_parts: tuple = ()
    notes_txt: str = ""
    hits: list = field(default_factory=list)       # [(sec, beat name)] sync points verified after render
    carve_db: float = 6.0             # 300-3000 Hz dip inside dialogue windows (0 = off)
    end_cut: bool = False             # True: the cue ends at full level, cut dead (4 ms fade, reverb incl.)
    dialogue: list = field(default_factory=list)   # [(t0, t1, line id)] filled from the timeline

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


def shape_vels(notes, vels):
    """Phrase-shaped velocities: assign `vels` to `notes` in time order (returns notes)."""
    for nt, v in zip(sorted(notes, key=lambda x: (x.beat, x.pitch)), vels):
        nt.vel = int(v)
    return notes


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


def gliss(pcs, p0, p1, b0, beats, v0, v1, ring=None):
    """Harp glissando over the pitch classes `pcs` from p0 up to p1 in `beats` beats (pedals set
    to a chord -> a pure chord sweep). Every string rings until b0 + `ring` beats."""
    ps = [p for p in range(p0, p1 + 1) if p % 12 in pcs]
    n = len(ps)
    ring = beats * 2.5 if ring is None else ring
    return [Note(b0 + beats * i / n, max(0.25, b0 + ring - (b0 + beats * i / n)), p,
                 int(v0 + (v1 - v0) * i / max(1, n - 1))) for i, p in enumerate(ps)]


HARP_FIGS = {
    "rise": [0, 1, 2, 3, 4, 5, 6, 7],          # bass, then open chord tones climbing
    "wave": [0, 1, 2, 3, 4, 3, 2, 1],          # up and back down
    "turn": [0, 1, 2, 3, 5, 4, 3, 2],          # climb, a little turn at the top
    "thirds": [0, 2, 1, 3, 2, 4, 3, 5],        # broken, rocking
    "lift": [0, 1, 2, 3, 4, 5, None, None],    # climb, then leave space for the melody
    "high": [4, 5, 6, 7],                      # second half of a split bar continues upward
}


def harp_arp(chords_, base_pitch_lo=50, step=0.5, pattern=None, v=(46, 60), low=True, low_vel=None,
             figures=None, ring=3.0, seed=0, avoid=None):
    """Rolling harp arpeggios: per chord, bass note then open chord tones rising (1-5-8-10-12-15...).

    base_pitch_lo: lowest allowed pitch for the bass of the figure.
    pattern: one index list for every chord; figures: per-chord list of HARP_FIGS names / index
    lists (cycled) for variety (None in a list = rest). Each note rings `ring` steps but is
    damped at the chord change unless its pitch class belongs to the next chord too, so no
    string rings through a harmony it does not belong to. Velocities follow the figure's contour
    (higher = a little louder) with a light accent on the first note and +-3 humanized variation.
    avoid: per-chord pitch sets (see mel_avoid); such a step becomes a rest."""
    rng = np.random.default_rng(seed)
    hi_lim = INST["harp"].hi
    out = []
    for ci, (b0, b1, sym) in enumerate(chords_):
        ch = chord(sym)
        if ch is None:
            continue
        nxt = None
        if ci + 1 < len(chords_) and abs(chords_[ci + 1][0] - b1) < 1e-6:
            nxt = chord(chords_[ci + 1][2])
        bass = ch.bass
        bp = base_pitch_lo + ((bass - base_pitch_lo) % 12)
        tones = sorted({(ch.root + i) % 12 for i in ch.ivs if i != 2} | {bass})
        stack = [bp]
        fifth_above = [p for p in range(bp + 5, bp + 12) if p % 12 in tones]
        if fifth_above:
            stack.append(fifth_above[-1] if len(fifth_above) > 1 else fifth_above[0])
        p = bp + 12
        while len(stack) < 12 and p <= hi_lim:
            if p % 12 in tones:
                stack.append(p)
            p += 1
        nsteps = int(round((b1 - b0) / step))
        if figures is not None:
            fig = figures[ci % len(figures)]
            pat = HARP_FIGS[fig] if isinstance(fig, str) else fig
        else:
            pat = pattern or list(range(nsteps))
        top = max(i for i in pat if i is not None)
        for i in range(nsteps):
            idx = pat[i % len(pat)]
            if idx is None:
                continue
            idx = min(idx, len(stack) - 1)
            onset = b0 + i * step
            pitch = stack[idx]
            if avoid and pitch in avoid[ci]:
                continue                      # leave the string silent rather than rub the tune
            dur = step * ring
            if onset + dur > b1 + 1e-6 and not (nxt is not None and pitch % 12 in nxt.pcs):
                dur = max(step * 0.9, b1 - onset)
            vel = v[0] + (v[1] - v[0]) * (idx / max(1, top)) + (4 if i == 0 else 0) + rng.integers(-3, 4)
            out.append(Note(onset, dur, pitch, int(np.clip(vel, 1, 127))))
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


def mel_avoid(chords_, mel_notes, width=2, bars=None):
    """Per chord: the set of pitches lying 1..`width` semitones (same octave) from an accented
    melody non-chord tone sounding during that chord - an NCT on beat 1/3 or lasting >= 2 beats
    (e.g. Theme A's E over Bm). Feed to voice_chords(avoid=...) so the sustained accompaniment
    never sits a 2nd away from an appoggiatura (a pad F#4 under the cello's E4). Weak passing
    tones are ignored - they are supposed to rub briefly. `bars` (bar-line beats) locates beats 1/3
    when bars do not start on even beats (the symphony's 1-beat grand-pause bar shifts the climax)."""
    bl = sorted(bars) if bars else [0.0]
    res = []
    for (b0, b1, sym) in chords_:
        ch = chord(sym)
        s = set()
        for m in mel_notes:
            if ch is None or not (m.beat < b1 - 1e-6 and m.beat + m.dur > b0 + 1e-6):
                continue
            b0_ = max([b for b in bl if b <= m.beat + 1e-6] or [0.0])
            accented = abs((m.beat - b0_) % 2) < 1e-6 or m.dur >= 2
            if m.pitch % 12 not in ch.pcs and accented:
                for d in range(1, width + 1):
                    s.update((m.pitch - d, m.pitch + d))
        res.append(s)
    return res


def voice_chords(chords_, n, lo, hi, bass=None, prev=None, top_max=None, top_min=None, force_top=None,
                 spacing=12, avoid=None, min_gap=0):
    """Smooth voice-leading for a chord timeline: for each chord pick the n-note voicing in [lo, hi]
    that contains the required tones, avoids doubled leading tones/7ths, avoids parallel 5ths/8ves
    (among the voices and against `bass`), and moves least from the previous voicing.
    bass: list of bass MIDI pitches per chord (or None). top_max/top_min/force_top: per-chord
    values (list) or scalars. avoid: per-chord sets of pitches to stay off (strong cost, see
    mel_avoid). min_gap: adjacent voices closer than this (semitones) cost extra (open voicings)."""
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
        av = avoid[ci] if avoid else set()
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
                cost += 30.0 * sum(1 for p in combo if p in av)
                if min_gap:
                    cost += 4.0 * sum(1 for k in range(n - 1) if combo[k + 1] - combo[k] < min_gap)
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
    # RMS detector smoothing (~30 ms). The detector starts from the level of the first 30 ms
    # (not from silence) so a cue that opens on a chord is compressed from its first sample.
    k = math.exp(-1 / 30)
    zi = signal.lfilter_zi([1 - k], [1, -k]) * float(np.mean(pw[:30]))
    pw, _ = signal.lfilter([1 - k], [1, -k], pw, zi=zi)
    lvl = 10 * np.log10(pw + 1e-12)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    a = math.exp(-1 / att_ms)
    r = math.exp(-1 / rel_ms)
    g = np.empty(nb)
    cur = float(gr[0])
    for i in range(nb):
        target = gr[i]
        cur = target + (cur - target) * (a if target > cur else r)
        g[i] = cur
    gs = np.interp(np.arange(len(x)), np.arange(nb) * block + block / 2, g)
    return x * db(-gs)[:, None]


def limiter(x, ceiling_db=-1.2, block=48, look=8, smooth=4, release_ms=150.0):
    """Lookahead peak limiter on 1 ms blocks. The needed gain is spread `look` blocks ahead of every
    peak (minimum filter), followed with instant attack / exponential release, then smoothed by a
    Hann window of +-`smooth` blocks (smooth <= look keeps the gain at every peak block <= what that
    peak needs), so a big hit is turned down over ~9 ms instead of a 1 ms gain step (no tick on
    the low end). Gain interpolated per sample; a final clip only catches inter-block slivers."""
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
    if smooth > 0:
        w = np.hanning(2 * smooth + 3)[1:-1]
        w /= w.sum()
        g = np.convolve(np.pad(g, smooth, mode="edge"), w, mode="valid")
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


def synth_sub(part, cue, n):
    """Soft rounded sub bass (sine + a little 2nd harmonic)."""
    midi, amp = mono_line(_notes_ev(part, cue, part.lazy), n, SR, glide=0.02, legato_gap=0.02,
                          attack=0.012, release=0.09, sustain=0.75, decay=0.5)
    f = 440.0 * 2 ** ((midi - 69) / 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.18 * np.sin(2 * ph)) * amp
    y = np.tanh(1.4 * y)
    return stereo(y * 0.6)


def fundamental_lift(notes, tm, gain_db, lo_pitch=0, width=1.12, fade=0.08, base=None):
    """Coherent low-end reinforcement for a sampled bass stem (a Part.eq): for every note at or above
    `lo_pitch`, the stem's OWN fundamental (zero-phase band-pass f0/width..f0*width, so it is exactly in
    phase with what it lifts) is added back under a raised-cosine window over the note -> +gain_db on
    the fundamental (gain_db may be a callable note -> dB). A zero-phase band-pass has a real, non-negative response, so unlike a layered
    sine it can never cancel the sample's fundamental (no notes that mysteriously go thin).
    tm: the cue's TempoMap; base: optional eq applied first (e.g. a high-pass)."""
    def eq(x):
        x = base(x) if base is not None else x
        n = len(x)
        add = np.zeros_like(x)
        for nt in notes:
            if nt.pitch < lo_pitch:
                continue
            k = 10 ** ((gain_db(nt) if callable(gain_db) else gain_db) / 20) - 1
            f0 = 440.0 * 2 ** ((nt.pitch - 69) / 12)
            t0, t1 = tm.sec(nt.beat), tm.sec(nt.beat + nt.dur)
            i0, i1 = max(0, int((t0 - 0.15) * SR)), min(n, int((t1 + 0.35) * SR))
            if i1 - i0 < int(0.2 * SR):
                continue
            seg = signal.sosfiltfilt(signal.butter(2, [f0 / width, f0 * width], "band", fs=SR, output="sos"),
                                     x[i0:i1], axis=0)
            tt = np.arange(i0, i1) / SR
            w = (0.5 - 0.5 * np.cos(np.pi * np.clip((tt - t0 + fade / 2) / fade, 0, 1))) * \
                (0.5 + 0.5 * np.cos(np.pi * np.clip((tt - t1 - 0.05) / fade, 0, 1)))
            add[i0:i1] += seg * w[:, None] * k
        return x + add
    return eq


def _dyn_gain(part, cue, n, power=1.6):
    """Per-sample linear gain from a part's dyn keyframes (0..127 -> (v/127)**power)."""
    if not part.dyn:
        return np.ones(n)
    tg = np.arange(0, n / SR + 0.05, 0.02)
    gk = np.array([dyn_at(part.dyn, cue.tmap.beat(tt)) / 127.0 for tt in tg])
    return np.interp(np.arange(n) / SR, tg, np.clip(gk, 0, 1)) ** power


def synth_sub_pedal(part, cue, n):
    """Orchestral sub reinforcement (the low 'organ pedal' under the basses): per note a sine on the
    fundamental + a faint 2nd/3rd harmonic (so small speakers still hear the pitch), raised-cosine
    attack, a short release when the next note follows (a clean cross-fade, no long beating of two
    low pitches) and a long one at the end of a phrase. Level = dyn keyframes x velocity. Pure sines
    (no aliasing), DC-free, mono in the center."""
    t = np.arange(n) / SR
    y = np.zeros(n)
    att = part.opts.get("attack", 0.2)
    rel_leg, rel_end = part.opts.get("release", 0.1), part.opts.get("release_end", 0.7)
    h2, h3 = part.opts.get("h2", 0.28), part.opts.get("h3", 0.08)
    ns = sorted(part.notes, key=lambda x: x.beat)
    starts = [cue.tmap.sec(x.beat) for x in ns]
    for k, nt in enumerate(ns):
        t0, t1 = starts[k], cue.tmap.sec(nt.beat + nt.dur)
        legato = k + 1 < len(ns) and starts[k + 1] - t1 < 0.06
        rel = rel_leg if legato else rel_end
        i0, i1 = max(0, int(t0 * SR)), min(n, int((t1 + rel) * SR) + 1)
        if i1 <= i0:
            continue
        tt = t[i0:i1] - t0
        a = 0.5 - 0.5 * np.cos(np.pi * np.clip(tt / att, 0, 1))
        r = 0.5 + 0.5 * np.cos(np.pi * np.clip((tt - (t1 - t0)) / rel, 0, 1))
        ph = 2 * np.pi * (440.0 * 2 ** ((nt.pitch - 69) / 12)) * tt
        y[i0:i1] += (nt.vel / 127.0) * a * r * (np.sin(ph) + h2 * np.sin(2 * ph + 0.4) + h3 * np.sin(3 * ph + 1.1))
    return stereo(y * _dyn_gain(part, cue, n) * 0.5)


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
    [(t_swell_start, t_hit, swell_gain, hit_gain, decay_s[, curve])] in seconds; a larger
    `curve` (default 3.2) keeps the roll quiet longer and rushes up at the end (an inhale)."""
    rng = np.random.default_rng(23)
    out = np.zeros((n, 2))
    for ev in part.opts["events"]:
        ts, th, gs, gh, dec = ev[:5]
        curve = ev[5] if len(ev) > 5 else 3.2
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
                sw = gs * (np.exp(curve * u) - 1) / (math.exp(curve) - 1)
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


def synth_bell(part, cue, n):
    """Soft sine 'tine ring' (tuning-fork-like): fundamental + faint 2nd/3rd partials, 4 ms attack,
    exponential decay part.opts['ring'] seconds (time constant), a cent of L/R detune for gentle
    beating. Used under a music box, whose sampled tine dies within ~0.6 s, so a last note can
    actually ring out."""
    t = np.arange(n) / SR
    y = np.zeros((n, 2))
    tau = part.opts.get("ring", 1.2)
    for nt in part.notes:
        t0 = cue.tmap.sec(nt.beat)
        i0 = max(0, int(t0 * SR))
        tt = t[i0:] - t0
        env = np.clip(tt / 0.004, 0, 1) * (nt.vel / 127.0) ** 1.5
        f = 440.0 * 2 ** ((nt.pitch - 69) / 12)
        for c, det in enumerate((-1.0, 1.0)):
            fd = f * 2 ** (det / 1200)
            y[i0:, c] += env * (np.exp(-tt / tau) * np.sin(2 * np.pi * fd * tt)
                                + 0.22 * np.exp(-tt / (tau * 0.45)) * np.sin(2 * np.pi * 2.0 * fd * tt + 0.7)
                                + 0.06 * np.exp(-tt / (tau * 0.25)) * np.sin(2 * np.pi * 3.01 * fd * tt + 1.9))
    return y * 0.4


def kf(keys, t, ease=True):
    """Keyframe curve [(sec, value)] sampled at times t; cosine-eased between keys (a key repeated
    = a hold), constant outside the keyed range."""
    ks = np.array([k[0] for k in keys], float)
    kv = np.array([k[1] for k in keys], float)
    if len(ks) == 1:
        return np.full(len(t), kv[0])
    seg = np.clip(np.searchsorted(ks, t, side="right") - 1, 0, len(ks) - 2)
    x = np.clip((t - ks[seg]) / np.maximum(ks[seg + 1] - ks[seg], 1e-9), 0, 1)
    if ease:
        x = 0.5 - 0.5 * np.cos(np.pi * x)
    return kv[seg] + (kv[seg + 1] - kv[seg]) * x

def synth_boom(part, cue, n):
    """Epic low drum 'booms' (the weight under the taiko skins): per note a sine that falls from
    (1 + opts['drop'], default 2.2)x to the note's pitch in ~45 ms, an exponential body decay (opts['decay'] s, longer when
    louder and lower), a felt-mallet thud (low-passed noise, 18 ms), gentle tanh saturation, then a
    crisp skin 'slap' (band-passed noise, ~9 ms, opts['slap']) so every hit reads on small speakers;
    every hit window ends in a 15 ms fade (no clicks). Mono, centered."""
    y = np.zeros(n)
    rng = np.random.default_rng(29)
    for nt in part.notes:
        i0 = int(cue.tmap.sec(nt.beat) * SR)
        dec = part.opts.get("decay", 0.5) * (0.55 + 0.45 * nt.vel / 127) * (1.0 if nt.pitch < 40 else 0.55)
        L = min(n - i0, int(dec * 6.5 * SR))
        if L <= 0 or i0 < 0:
            continue
        tt = np.arange(L) / SR
        fe = 440.0 * 2 ** ((nt.pitch - 69) / 12)
        f = fe * (1 + part.opts.get("drop", 1.2) * np.exp(-tt / 0.045))
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / dec) * np.clip(tt / 0.0015, 0, 1)
        th = lp(rng.standard_normal(L), 900)
        th = th / (np.std(th[: int(0.03 * SR)]) + 1e-9) * np.exp(-tt / 0.018) * 0.22
        hit = np.tanh(1.7 * (body + th)) / math.tanh(1.7)
        sl = bp(rng.standard_normal(L), 700, 5200)
        hit += part.opts.get("slap", 0.0) * sl / (np.std(sl[: int(0.02 * SR)]) + 1e-9) * np.exp(-tt / 0.009)
        hit[-int(0.015 * SR):] *= np.linspace(1, 0, int(0.015 * SR))
        y[i0:i0 + L] += (nt.vel / 127.0) ** 1.4 * hit
    return stereo(y * 0.5)

def synth_heartbeat(part, cue, n):
    """A felt heartbeat: every note = 'lub' (at the note) + 'dub' (opts['gap'] s later, opts['dub']
    x as loud). Each thump is a sine that drops from 1.6x to the note's pitch in ~25 ms with a
    ~opts['decay'] s body, a soft low-passed knock, a touch of 2nd harmonic (so it reads on small
    speakers) and tanh rounding. Mono, centered; no humanization (sync-locked)."""
    y = np.zeros(n)
    rng = np.random.default_rng(part.opts.get("seed", 13))
    gap, dub, dec = part.opts.get("gap", 0.19), part.opts.get("dub", 0.62), part.opts.get("decay", 0.11)
    for nt in part.notes:
        t0 = cue.tmap.sec(nt.beat)
        for k, (off, g) in enumerate(((0.0, 1.0), (gap, dub))):
            i0 = int((t0 + off) * SR)
            L = min(n - i0, int(dec * 7 * SR))
            if L <= 0 or i0 < 0:
                continue
            tt = np.arange(L) / SR
            f0 = 440.0 * 2 ** ((nt.pitch - (2 if k else 0) - 69) / 12)
            f = f0 * (1 + 0.6 * np.exp(-tt / 0.025))
            ph = 2 * np.pi * np.cumsum(f) / SR
            env = np.exp(-tt / (dec * (0.85 if k else 1.0))) * np.clip(tt / 0.004, 0, 1)
            body = (np.sin(ph) + 0.22 * np.sin(2 * ph + 0.5)) * env
            kn = lp(rng.standard_normal(L), 380)
            kn = kn / (np.std(kn[: int(0.02 * SR)]) + 1e-9) * np.exp(-tt / 0.012) * 0.18
            hit = np.tanh(1.5 * (body + kn)) / math.tanh(1.5)
            hit[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
            y[i0:i0 + L] += g * (nt.vel / 127.0) ** 1.3 * hit
    return stereo(y * _dyn_gain(part, cue, n, 1.0) * 0.6)


def synth_drone(part, cue, n):
    """Aching low drone: per note additive harmonics (tilt k^-opts['tilt']) whose amplitudes drift
    slowly and independently (random 0.03-0.25 Hz), so the timbre 'breathes' and moans; L/R copies
    detuned +-opts['detune'] cents (slow beating = width), long raised-cosine attack/release
    (opts['attack'] / opts['release'] s), level = velocity x dyn keyframes."""
    o = part.opts
    t = np.arange(n) / SR
    rng = np.random.default_rng(o.get("seed", 5))
    att, rel = o.get("attack", 2.0), o.get("release", 2.0)
    tilt, kmax, det = o.get("tilt", 1.25), o.get("kmax", 14), o.get("detune", 4.0)
    y = np.zeros((n, 2))
    hop = 240
    tg = t[::hop]
    for nt in part.notes:
        t0, t1 = cue.tmap.sec(nt.beat), cue.tmap.sec(nt.beat + nt.dur)
        i0, i1 = max(0, int((t0 - 0.01) * SR)), min(n, int((t1 + rel) * SR) + 1)
        if i1 <= i0:
            continue
        tt = t[i0:i1] - t0
        env = (0.5 - 0.5 * np.cos(np.pi * np.clip(tt / att, 0, 1))) * \
              (0.5 + 0.5 * np.cos(np.pi * np.clip((tt - (t1 - t0)) / rel, 0, 1)))
        f0 = 440.0 * 2 ** ((nt.pitch - 69) / 12)
        for c, sgn in enumerate((-1, 1)):
            f = f0 * 2 ** (sgn * det / 1200)
            acc = np.zeros(i1 - i0)
            for k in range(1, kmax + 1):
                if k * f > 9000:
                    break
                drift = lp_noise(len(tg), rng.uniform(0.03, 0.25), SR / hop, rng)
                a = k ** -tilt * np.clip(1 + o.get("move", 0.45) * drift, 0, None)
                a = np.interp(t[i0:i1], tg, a)
                acc += a * np.sin(2 * np.pi * k * f * tt + rng.uniform(0, 6.28))
            y[i0:i1, c] += acc * env * (nt.vel / 127.0)
    y = lp(y, o.get("lp", 2400))
    return y * _dyn_gain(part, cue, n, 1.0)[:, None] * 0.25


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
    ev = [] if inst.bank == 128 else [(0.0, 0, dict(type="control_change", control=0, value=inst.bank))]
    ev += [(0.0, 0, dict(type="program_change", program=inst.prog)),
           (0.0, 0, dict(type="control_change", control=7, value=100)),
           (0.0, 0, dict(type="control_change", control=10, value=64)),
           (0.0, 0, dict(type="control_change", control=64, value=0))]
    rng_st = part.bend_range
    # RPN 0 = pitch-bend sensitivity (semitones), then RPN null
    for c_, v_ in ((101, 0), (100, 0), (6, rng_st), (38, 0), (101, 127), (100, 127)):
        ev.append((0.0, 0, dict(type="control_change", control=c_, value=v_)))
    base_c = float(part.opts.get("bend_cents", 0.0))  # a constant tuning offset (ensemble detune)

    def wheel(cents):
        return int(np.clip(round(cents / (rng_st * 100.0) * 8192), -8192, 8191))
    if part.bend:
        keys = sorted(part.bend)
        t0, t1 = tm.sec(keys[0][0]), tm.sec(keys[-1][0])
        ks = [(tm.sec(b), c) for b, c in keys]
        last = None
        tt = 0.0
        ev.append((0.0, 0, dict(type="pitchwheel", pitch=wheel(base_c + ks[0][1]))))
        tt = max(0.0, t0)
        while tt <= t1 + 0.005:
            c = float(kf(ks, np.array([tt]))[0]) + base_c
            w_ = wheel(c)
            if w_ != last:
                ev.append((max(0.0, tt), 0, dict(type="pitchwheel", pitch=w_)))
                last = w_
            tt += 0.01
    elif base_c:
        ev.append((0.0, 0, dict(type="pitchwheel", pitch=wheel(base_c))))
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


# GM stand-ins used only in the inspection MIDI (<cue>.mid) for parts that are synthesized in numpy
SYNTH_GM = {"sub_bass": 38, "shimmer": 92, "bell": 10, "sub_pedal": 38, "drone": 38}
DRUM_KINDS = {"cymbal", "boom", "heartbeat", "riser", "kit"}


def score_midi(cue: Cue) -> mido.MidiFile:
    """Whole-score MIDI for inspection: one named track per part (SoundFont AND numpy parts),
    absolute time (1 tick = 1 ms). Each distinct instrument gets its own channel (drum-like parts
    on channel 10); a score with more than 15 distinct instruments reuses channels round-robin."""
    rng = np.random.default_rng(0)
    chans = {}
    free = [c for c in range(16) if c != 9]
    tracks = []
    for p in cue.parts:
        if p.inst in DRUM_KINDS or (p.inst in INST and INST[p.inst].bank == 128):
            ch = 9
        else:
            key = (INST[p.inst].bank, INST[p.inst].prog) if p.inst in INST else (0, SYNTH_GM.get(p.inst, 0))
            if key not in chans:
                chans[key] = free[len(chans) % len(free)]
            ch = chans[key]
        if p.synth is None:
            ev = part_events(p, cue, rng)
        else:
            ev = [] if ch == 9 else [(0.0, 0, dict(type="program_change", program=SYNTH_GM.get(p.inst, 0)))]
            off = p.lazy + p.opts.get("delay", 0.0)
            for nt in p.notes:
                s = cue.tmap.sec(nt.beat) + off
                e = cue.tmap.sec(nt.beat + nt.dur) + off
                ev.append((max(0.0, s), 2, dict(type="note_on", note=int(nt.pitch), velocity=int(nt.vel))))
                ev.append((max(s + 0.01, e), 1, dict(type="note_off", note=int(nt.pitch), velocity=0)))
        tracks.append(events_to_track(ev, ch, p.name))
    return midi_file(tracks)


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
    mf = midi_file([events_to_track(ev, 9 if INST[part.inst].bank == 128 else 0, part.name)])
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


def _gate_env(n, t0, t1, fade_out=0.15, fade_in=0.025):
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
    if p.opts.get("sat"):
        # drum-bus style soft saturation: tanh on the peak-normalized stem trims the transient spikes
        # (a few dB of crest) so a tutti hit keeps its body under the master ceiling
        pk = float(np.max(np.abs(x))) + 1e-12
        k = float(p.opts["sat"])
        x = np.tanh(k * x / pk) / math.tanh(k) * pk
    if p.vol:
        tt = np.array([cue.tmap.sec(b) for b, _ in p.vol])
        vv = np.array([v for _, v in p.vol], float)
        x = x * db(np.interp(np.arange(n) / SR, tt, vv))[:, None]
    for g in cue.gates:                       # (t0, t1, keep[, release_s])
        t0, t1, keep = g[:3]
        if p.name not in keep:
            x = x * _gate_env(n, t0, t1, *(g[3:4] or ()))[:, None]
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
        if "level" in p.opts or "peak" in p.opts:
            # target-level balancing: 'level' = RMS (dBFS) over the stem's active 10 ms frames (within
            # 30 dB of its loudest frame), 'peak' = sample peak (dBFS); gain_db is then a trim on top
            if "level" in p.opts:
                fr = np.sqrt(np.mean(x[: len(x) // 480 * 480].reshape(-1, 480, 2) ** 2, axis=(1, 2)))
                on_ = fr > np.max(fr) * db(-30) if np.max(fr) > 0 else fr > 1
                cur = 20 * np.log10(np.sqrt(np.mean(fr[on_] ** 2)) + 1e-12) if on_.any() else -120.0
                want = p.opts["level"]
            else:
                cur = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
                want = p.opts["peak"]
            if cur > -110:
                x = x * db(want - cur)
        if mv is not None:
            x = x * mv
        act = np.sqrt(np.mean(x ** 2, axis=1))
        on = act > (np.max(act) * 0.05 if np.max(act) > 0 else 1)
        levels[p.name] = 20 * np.log10(np.sqrt(np.mean(x[on] ** 2)) + 1e-12) if on.any() else -120.0
        dry += x
        send += x * p.send
    if cue.send_hp:
        send = hp(send, cue.send_hp)
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


def dialogue_gain(cue: Cue, n: int, ramp=0.12, pre=0.10, post=0.18) -> np.ndarray:
    """Per-sample 0..1 weight: 1 inside every dialogue window (with a little pre-roll / tail), cosine
    ramps in and out."""
    t = np.arange(n) / SR
    w = np.zeros(n)
    for t0, t1, _ in cue.dialogue:
        a, b = t0 - pre, t1 + post
        up = np.clip((t - (a - ramp)) / ramp, 0, 1)
        dn = np.clip(((b + ramp) - t) / ramp, 0, 1)
        w = np.maximum(w, np.minimum(up, dn))
    return 0.5 - 0.5 * np.cos(np.pi * w)


def carve(cue: Cue, x: np.ndarray) -> np.ndarray:
    """Dialogue carve: the 300-3000 Hz band (zero-phase band-pass, so the complement is exact) is
    dipped by cue.carve_db wherever somebody speaks; everything below/above is untouched."""
    if not cue.carve_db or not cue.dialogue:
        return x
    w = dialogue_gain(cue, len(x))
    if not np.any(w > 0):
        return x
    mid = signal.sosfiltfilt(signal.butter(2, [300, 3000], "band", fs=SR, output="sos"), x, axis=0)
    g = 1.0 - (1.0 - db(-cue.carve_db)) * w
    return x + mid * (g - 1.0)[:, None]


LAST_MASTER = {}


def master(cue: Cue, x: np.ndarray):
    n = len(x)
    x = hp(x, 18.0)                                                    # DC / subsonic blocker
    x = carve(cue, x)
    pw = np.concatenate([[0.0], np.cumsum(np.mean(x ** 2, axis=1))])
    k = 4800
    pk_rms = 10 * np.log10(np.max((pw[k:] - pw[:-k]) / k) + 1e-12)       # loudest 100 ms
    th, ratio, att, rel = cue.comp
    x = compressor(x, pk_rms + th, ratio, att, rel)
    # loudness normalization: the limiter always works on the UNLIMITED signal x0 * gain, and the
    # gain converges so that the limited result meets the target
    x0 = x
    g = 0.0
    for _ in range(6):
        pre = x0 * db(g)
        x = limiter(pre, -1.5)                                        # margin for inter-sample peaks
        if cue.st_target is not None:
            _, st = short_term(x)
            err = cue.st_target - np.max(st)
        else:
            err = cue.target_lufs - integrated_lufs(x)
        if abs(err) < 0.1:
            break
        g += err
    # how hard the limiter worked (dB of gain reduction on the loudest 10 ms frames)
    fr = len(x) // 480 * 480
    a_ = np.max(np.abs(pre[:fr]).reshape(-1, 480, 2), axis=(1, 2))
    b_ = np.max(np.abs(x[:fr]).reshape(-1, 480, 2), axis=(1, 2))
    gr = 20 * np.log10(np.maximum(a_, 1e-9) / np.maximum(b_, 1e-9))
    top = np.argsort(gr)[::-1][:3]
    LAST_MASTER["limiter_gr"] = ", ".join(f"{gr[i]:.1f} dB @ {i * 0.01:.2f}s" for i in top)
    # fades + exact length ("cut dead" endings: 4 ms, the reverb tail is cut with everything else)
    fi = int(cue.fade_in * SR)
    fo = int((0.004 if cue.end_cut else cue.fade_out) * SR)
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
        d -= np.percentile(d, 99.5)          # robust reference: one stray transient can't own 1.0
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
    """Spectrogram (40 Hz-16 kHz log, 300/3000 Hz guides) + envelopes + short-term loudness, with
    dialogue windows (grey bars), sync hits (cyan) and landmarks (pink). Writes <path>.png and a
    JPEG twin (<= 1400 px wide) for quick viewing."""
    from PIL import Image, ImageDraw
    W_, SPEC_H, ENV_H, LU_H, PAD = 1400, 280, 130, 110, 22
    mono = x.mean(axis=1)
    f, t, S = signal.spectrogram(mono, SR, nperseg=2048, noverlap=1536)
    S = 10 * np.log10(S + 1e-14)
    lf = np.logspace(np.log10(40), np.log10(16000), SPEC_H)
    idx = np.clip(np.searchsorted(f, lf), 0, len(f) - 1)
    S = S[idx][::-1]
    S = np.clip((S + 120) / 95, 0, 1)
    tcol = (np.arange(W_) + 0.5) / W_ * cue.length
    cols = np.clip(np.searchsorted(t, tcol), 0, S.shape[1] - 1)
    S = S[:, cols]
    rgb = np.stack([S ** 0.8 * 255, S ** 1.6 * 230, (1 - S) * S * 3.2 * 255], axis=-1).clip(0, 255).astype(np.uint8)
    H_ = SPEC_H + ENV_H + LU_H + PAD * 2 + 40
    img = Image.new("RGB", (W_, H_), (12, 12, 18))
    img.paste(Image.fromarray(rgb), (0, 20))
    d = ImageDraw.Draw(img)
    L = cue.length

    def X(sec):
        return int(sec / L * (W_ - 1))

    def Yf(hz):
        return 20 + SPEC_H - 1 - int(np.searchsorted(lf, hz))
    for hz in (300, 3000):
        d.line([(0, Yf(hz)), (W_, Yf(hz))], fill=(70, 70, 90))
        d.text((2, Yf(hz) - 11), f"{hz} Hz", fill=(150, 150, 170))
    d.text((6, 3), f"{cue.name}  {L:.2f}s  spectrogram 40 Hz-16 kHz (log); grey = dialogue, cyan = sync hits",
           fill=(220, 220, 220))
    for t0, t1, lid in cue.dialogue:
        d.rectangle([X(max(0, t0)), 21, X(min(L, t1)), 27], fill=(150, 150, 150))
        d.text((X(max(0, t0)) + 2, 28), lid, fill=(200, 200, 200))
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
    tt, st = short_term(x.astype(np.float64), win=1.0, hop=0.05)
    d.rectangle([0, y1, W_, y1 + LU_H], fill=(20, 24, 22))
    for lvl in (-12, -18, -24, -36):
        yy = y1 + LU_H - int((lvl + 48) / 48 * LU_H)
        d.line([(0, yy), (W_, yy)], fill=(50, 60, 55))
        d.text((W_ - 60, yy - 11), f"{lvl} LUFS", fill=(140, 160, 150))
    pts = [(X(a), y1 + LU_H - int(np.clip((b + 48) / 48, 0, 1) * LU_H)) for a, b in zip(tt, st)]
    d.line(pts, fill=(120, 230, 150), width=2)
    d.text((6, y1 + 2), "loudness (1 s window)", fill=(200, 200, 200))
    for sec, lab in cue.landmarks:
        xx = X(sec)
        d.line([(xx, 40), (xx, y1 + LU_H)], fill=(255, 80, 120), width=1)
        d.text((xx + 2, 20 + SPEC_H - 12), lab, fill=(255, 140, 170))
    for k, (sec, lab) in enumerate(cue.hits):
        xx = X(sec)
        d.line([(xx, 40), (xx, y1 + LU_H)], fill=(60, 230, 255), width=1)
        d.text((xx + 2, 44 + 12 * (k % 4)), lab, fill=(120, 240, 255))
    for s_ in range(0, int(L) + 1):
        xx = X(s_)
        d.line([(xx, H_ - 18), (xx, H_ - 12)], fill=(180, 180, 180))
        if L < 12 or s_ % 5 == 0:
            d.text((xx + 1, H_ - 12), str(s_), fill=(180, 180, 180))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    img.save(path.with_suffix(".jpg"), quality=85)


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
        if p.inst in DRUM_KINDS:
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



# =========================================================================== verification


def hit_report(cue: Cue, x: np.ndarray) -> list:
    """For every sync hit: the strongest 20 ms level rise within +-60 ms of the hit (offset in ms) and
    the level step (dB, 120 ms before vs 150 ms after). A hit at the very end of the cue (a 'cut
    dead') reports the level of the final 50 ms instead."""
    mono = np.mean(x, axis=1)
    mono = bp(mono, 40, 8000)
    hop = int(0.005 * SR)
    p_ = np.convolve(mono ** 2, np.ones(2 * hop) / (2 * hop), mode="same")[::hop]
    e = 10 * np.log10(p_ + 1e-12)
    out = []
    for sec, lab in cue.hits:
        if sec >= cue.length - 0.02:
            tail = 20 * np.log10(np.sqrt(np.mean(x[-int(0.05 * SR):] ** 2)) + 1e-12)
            body = 20 * np.log10(np.sqrt(np.mean(x[-int(0.6 * SR):-int(0.1 * SR)] ** 2)) + 1e-12)
            out.append(f"{lab:16s} {sec:7.3f}s  END: last 50 ms at {tail:6.1f} dBFS rms (preceding 0.5 s "
                       f"{body:6.1f}) -> cut dead at the cue end")
            continue
        i = int(sec / 0.005)
        flux = np.full(len(e), -99.0)
        flux[4:] = e[4:] - e[:-4]
        lo_, hi_ = max(4, i - 12), min(len(e) - 1, i + 12)
        j = lo_ + int(np.argmax(flux[lo_:hi_ + 1]))
        # the rise peaks ~half a window after the true onset; report the frame where the rise starts
        k = j
        while k > lo_ and flux[k - 1] > 0.5 * flux[j]:
            k -= 1
        on = (k - 2) * 0.005
        pre = 10 * np.log10(np.mean(p_[max(0, i - 24):max(1, i - 6)]) + 1e-12)
        post = 10 * np.log10(np.mean(p_[i:i + 30]) + 1e-12)
        out.append(f"{lab:16s} {sec:7.3f}s  onset {1000 * (on - sec):+5.0f} ms   step {post - pre:+5.1f} dB "
                   f"({pre:6.1f} -> {post:6.1f} dB)")
    return out


def dialogue_report(cue: Cue, x: np.ndarray) -> list:
    """300-3000 Hz band level inside each dialogue window vs the louder of the cue's non-dialogue
    passages (median of 0.5 s blocks above -60 dBFS)."""
    if not cue.dialogue:
        return []
    band = signal.sosfiltfilt(signal.butter(4, [300, 3000], "band", fs=SR, output="sos"), x, axis=0)
    w = dialogue_gain(cue, len(x), ramp=0.01, pre=0.0, post=0.0)
    blk = int(0.5 * SR)
    lv = []
    for a in range(0, len(x) - blk, blk):
        if np.max(w[a:a + blk]) > 0:
            continue
        v = 20 * np.log10(np.sqrt(np.mean(band[a:a + blk] ** 2)) + 1e-12)
        if v > -60:
            lv.append(v)
    ref = float(np.median(lv)) if lv else float("nan")
    full = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    out = [f"reference (non-dialogue 0.5 s blocks, median) {ref:6.1f} dBFS in 300-3000 Hz; cue full-band rms {full:6.1f}"]
    for t0, t1, lid in cue.dialogue:
        a, b = int(max(0, t0) * SR), int(min(cue.length, t1) * SR)
        if b - a < SR // 10:
            continue
        v = 20 * np.log10(np.sqrt(np.mean(band[a:b] ** 2)) + 1e-12)
        out.append(f"{lid}: {t0:6.2f}-{t1:6.2f}s  band {v:6.1f} dBFS  ({v - ref:+5.1f} dB vs reference)")
    return out


def dialogue_windows(cue_name: str) -> list:
    """[(t0, t1, line id)] in cue-local seconds for every line overlapping the cue in build/timeline.json."""
    try:
        tl = json.loads(Path(TIMELINE).read_text())
    except (OSError, json.JSONDecodeError):
        return []
    mus = [m for m in tl.get("music", []) if m["cue"] == cue_name]
    if not mus:
        return []
    c0 = mus[0]["start"]
    c1 = c0 + MUSIC_CUES[cue_name]
    return [(ln["start"] - c0, ln["end"] - c0, ln["id"]) for ln in tl.get("lines", [])
            if ln["end"] > c0 and ln["start"] < c1]


def true_peak_db(x: np.ndarray) -> float:
    up = signal.resample_poly(x, 4, 1, axis=0)
    return 20 * math.log10(float(np.max(np.abs(up))) + 1e-12)


def render_cue(name: str, composers: dict) -> dict:
    cue = composers[name]()
    cue.dialogue = dialogue_windows(name)
    n = int(round(cue.length * SR))
    stems = render_stems(cue, n)
    x, levels = mix_cue(cue, stems, n)
    y = master(cue, x)
    assert len(y) == n and y.shape[1] == 2, (name, y.shape)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    sf.write(MUSIC_DIR / f"{name}.wav", y, SR, subtype="FLOAT")
    chk, sr = sf.read(MUSIC_DIR / f"{name}.wav", always_2d=True, dtype="float32")
    assert sr == SR and chk.shape == (n, 2), (name, chk.shape)
    assert abs(len(chk) / SR - MUSIC_CUES[name]) < 1e-9
    c64 = chk.astype(np.float64)
    peak = 20 * math.log10(float(np.max(np.abs(chk))) + 1e-12)
    tpk = true_peak_db(c64)
    lufs = integrated_lufs(c64)
    _, st = short_term(c64)
    env = envelopes(c64, cue)
    score_midi(cue).save(MUSIC_DIR / f"{name}.mid")
    first = float(np.max(np.abs(chk[:48]))) if n > 48 else 0.0
    last = float(np.max(np.abs(chk[-48:])))
    stats = {"duration_s": f"{len(chk) / SR:.6f} (target {MUSIC_CUES[name]})",
             "peak_dBFS": f"{peak:.2f} (true peak {tpk:.2f} dBTP)", "integrated_LUFS": f"{lufs:.2f}",
             "max_short_term_LUFS": f"{np.max(st):.2f}",
             "edges": f"first 1 ms max {first:.4f}, last 1 ms max {last:.4f}",
             "limiter_gain_reduction(max)": LAST_MASTER.get("limiter_gr", ""),
             "sync_hits": hit_report(cue, c64),
             "dialogue_band_300_3000": dialogue_report(cue, c64),
             "stem_levels_dBFS(pre-master)": ", ".join(f"{k} {v:.1f}" for k, v in levels.items()),
             "tempo_bpm_per_quarter_bar": tempo_report(cue),
             "range_violations": check_ranges(cue), "outer_voice_parallels": check_outer(cue)}
    score_dump(cue, MUSIC_DIR / f"score_{name}.txt", stats)
    analysis_png(cue, c64, env, TEST_DIR / f"{name}.png")
    print(f"{name:9s} {len(chk) / SR:7.3f}s  peak {peak:6.2f} dBFS (TP {tpk:6.2f})  integrated {lufs:6.2f} LUFS  "
          f"max ST {np.max(st):6.2f}  ranges {len(stats['range_violations'])}  "
          f"parallels {len(stats['outer_voice_parallels'])}  limiter GR {LAST_MASTER.get('limiter_gr', '')}", flush=True)
    for h in stats["sync_hits"]:
        print("    hit " + h)
    for h in stats["dialogue_band_300_3000"]:
        print("    dlg " + h)
    return {k: env[k] for k in ("rms", "low", "high", "onsets", "beats", "downbeats")}


def main(argv, composers: dict):
    global USE_CACHE
    args = [a for a in argv if not a.startswith("--")]
    if "--no-cache" in argv:
        USE_CACHE = False
    names = args or list(MUSIC_CUES)
    for nm in names:
        if nm not in composers:
            raise SystemExit(f"unknown cue {nm!r}; choose from {', '.join(composers)}")
    missing = set(MUSIC_CUES) - set(composers)
    if missing and not args:
        raise SystemExit(f"no composer for {missing}")
    envs = {}
    p = Path(MUSIC_ENV)
    if p.exists():
        try:
            envs = json.loads(p.read_text())
        except json.JSONDecodeError:
            envs = {}
    for nm in names:
        envs[nm] = render_cue(nm, composers)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({k: envs[k] for k in MUSIC_CUES if k in envs}, separators=(",", ":")))
    print(f"wrote {p}")
