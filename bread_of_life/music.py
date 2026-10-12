"""Score: programmatic MIDI cues rendered with FluidSynth (FluidR3 GM), then a
convolution hall reverb, then placed on the film timeline with crossfades.

Musical plan (D minor / Dorian, with brief Hijaz colour for tension):
  opening      harp + slow strings + ney-like pan flute theme
  mystery      choir over a D pedal for "I am here because my Father has willed it"
  teaching1    soft strings under Jesus' first words
  exchange     cello ostinato, oud plucks with Hijaz colour under Eli's challenge
  father       strings rising, choir enters on "my Father"
  plea         a single held note under Miriam's plea
  bread        D MAJOR bloom with choir on "I am the bread of life"
  murmur       low drone + uneasy plucks in the synagogue
  authority    calm strings for "Stop grumbling" / "taught by God"
  living       choir swell, then a sorrowful suspension on "my flesh ... for the life of the world"
  uproar       tremolo strings + timpani under the argument, cut dead before the hardest words
  drone        almost silence: low D drone under "unless you eat ..."
  communion    strings rebuild, tender harp for "remains in me, and I in them"
  final        warm swell resolving on "will live forever"
  lament       solo flute over a thin pad as many walk away
  question     one held string note under "You do not want to leave too?"
  confession   hope rising into D major on "the Holy One of God", a theme phrase as the bread is broken
  prayer       a still D-major bed under Jesus' prayer, the theme's cadence under the end title
"""
import os
import subprocess

import mido
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, resample_poly

from config import SR, WORK
from timeline import Timeline

T = Timeline()
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
OUT = os.path.join(WORK, "music")
os.makedirs(OUT, exist_ok=True)

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "7": [0, 4, 7, 10],
        "sus4": [0, 5, 7], "sus2": [0, 2, 7], "add9": [0, 4, 7, 14], "madd9": [0, 3, 7, 14], "m9": [0, 3, 7, 10, 14],
        "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9], "7b9": [0, 4, 7, 10, 13], "dim": [0, 3, 6], "maj9": [0, 4, 7, 11, 14],
        "7sus4": [0, 5, 7, 10]}

PROG = {"strings": 49, "strings_fast": 48, "trem": 44, "pizz": 45, "cello": 42, "bass": 43, "harp": 46,
        "timp": 47, "choir": 52, "oohs": 53, "panflute": 75, "shaku": 77, "oboe": 68, "ehorn": 69, "flute": 73,
        "oud": 24, "pad": 89, "padchoir": 91}


def parse(sym):
    bass = None
    if "/" in sym:
        sym, bass = sym.split("/")
    root = sym[:2] if len(sym) > 1 and sym[1] in "#b" else sym[:1]
    q = sym[len(root):]
    pcs = [NOTE[root] + i for i in QUAL[q]]
    return NOTE[root], pcs, (NOTE[bass] if bass else NOTE[root])


def voice(pcs, prev, lo=55, hi=79, n=4):
    """Choose an upper-structure voicing (n notes in [lo, hi]) close to the previous one."""
    cands = []
    pcs = sorted(set(p % 12 for p in pcs))
    base_notes = [p for p in range(lo, hi + 1) if p % 12 in pcs]
    import itertools
    best = None
    for combo in itertools.combinations(base_notes, n):
        if max(combo) - min(combo) > 16:
            continue
        if len(set(c % 12 for c in combo)) < min(n, len(pcs)):
            continue
        gaps = np.diff(combo)
        if np.any(gaps < 2):
            continue
        score = 0.0
        if prev:
            score += sum(min(abs(a - b) for b in prev) for a in combo)
        else:
            score += abs(np.mean(combo) - (lo + hi) / 2)
        if best is None or score < best[0]:
            best = (score, list(combo))
    return best[1] if best else [lo + pcs[0]]


class Cue:
    def __init__(self, name, start, end, bpm=60, gain=1.0, fade_in=1.5, fade_out=2.5):
        self.name = name
        self.start = start
        self.end = end
        self.bpm = bpm
        self.gain = gain
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.ev = []  # (beat, type, ch, a, b)
        self.ch = {}

    @property
    def beats(self):
        return (self.end - self.start) * self.bpm / 60.0

    def b(self, seconds):
        return seconds * self.bpm / 60.0

    def inst(self, key, ch, vol=100, rev=60, pan=64):
        self.ch[key] = ch
        self.ev.append((0, "prog", ch, PROG[key], 0))
        self.ev.append((0, "cc", ch, 7, vol))
        self.ev.append((0, "cc", ch, 10, pan))
        self.ev.append((0, "cc", ch, 91, 0))
        self.ev.append((0, "cc", ch, 11, 100))

    def note(self, key, beat, dur, pitch, vel):
        ch = self.ch[key]
        vel = int(max(1, min(127, vel)))
        self.ev.append((beat, "on", ch, int(pitch), vel))
        self.ev.append((beat + dur, "off", ch, int(pitch), 0))

    def expr(self, key, beat, value):
        self.ev.append((beat, "cc", self.ch[key], 11, int(max(0, min(127, value)))))

    def ramp(self, key, b0, b1, v0, v1, steps=24):
        for i in range(steps + 1):
            u = i / steps
            self.expr(key, b0 + (b1 - b0) * u, v0 + (v1 - v0) * u)

    def write(self, path):
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=int(60e6 / self.bpm)))
        order = {"prog": 0, "cc": 1, "off": 2, "on": 3}
        evs = sorted(self.ev, key=lambda e: (e[0], order[e[1]]))
        last = 0
        for beat, typ, ch, a, b in evs:
            tick = int(round(beat * 480))
            dt = max(0, tick - last)
            last = max(last, tick)
            if typ == "prog":
                tr.append(mido.Message("program_change", channel=ch, program=a, time=dt))
            elif typ == "cc":
                tr.append(mido.Message("control_change", channel=ch, control=a, value=b, time=dt))
            elif typ == "on":
                tr.append(mido.Message("note_on", channel=ch, note=a, velocity=b, time=dt))
            else:
                tr.append(mido.Message("note_off", channel=ch, note=a, velocity=0, time=dt))
        mid.save(path)


# ---------------------------------------------------------------------------
# building blocks
# ---------------------------------------------------------------------------

def pad_chords(c, key, chords, beat0, beats_each, vel=50, lo=55, hi=77, n=4, swell=False):
    prev = None
    b = beat0
    for sym in chords:
        root, pcs, bass = parse(sym)
        v = voice(pcs, prev, lo, hi, n)
        prev = v
        for p in v:
            c.note(key, b, beats_each + 0.15, p, vel)
        b += beats_each
    return b


def bass_line(c, key, chords, beat0, beats_each, vel=50, octave=36, rearticulate=None):
    b = beat0
    for sym in chords:
        root, pcs, bass = parse(sym)
        p = octave + bass
        if p > octave + 7:
            p -= 12
        if rearticulate:
            k = 0.0
            while k < beats_each - 1e-6:
                c.note(key, b + k, rearticulate * 0.95, p, vel)
                k += rearticulate
        else:
            c.note(key, b, beats_each + 0.1, p, vel)
        b += beats_each
    return b


def harp_arps(c, key, chords, beat0, beats_each, vel=55, step=0.5, pattern=(0, 1, 2, 3, 4, 3), low=50):
    b = beat0
    for sym in chords:
        root, pcs, bass = parse(sym)
        notes = []
        base = low + ((bass - low) % 12)
        tones = sorted(set(p % 12 for p in pcs))
        # build ascending chord tones from the bass upward
        p = base
        notes.append(p)
        while len(notes) < 8:
            p += 1
            if p % 12 in tones:
                notes.append(p)
        k = 0.0
        i = 0
        while k < beats_each - 1e-6:
            idx = pattern[i % len(pattern)]
            accent = 1.0 if i % len(pattern) == 0 else 0.82
            c.note(key, b + k, step * 3.0, notes[min(idx, len(notes) - 1)], vel * accent)
            k += step
            i += 1
        b += beats_each
    return b


def melody(c, key, notes, beat0, vel=70, legato=1.0):
    """notes: list of (pitch or None, beats)."""
    b = beat0
    for pitch, d in notes:
        if pitch is not None:
            c.note(key, b, d * legato, pitch, vel)
        b += d
    return b


THEME_MIN = [(69, 2), (74, 1), (76, 1), (77, 3), (76, 1), (74, 2), (72, 1), (74, 1), (69, 4),
             (70, 2), (72, 1), (74, 1), (76, 2), (77, 1), (76, 1), (74, 3), (73, 1), (74, 4)]
THEME_MIN_CH = ["Dm", "F", "Bb", "A", "Gm", "C", "A", "Dm"]
THEME_MAJ = [(69, 2), (74, 1), (76, 1), (78, 3), (76, 1), (74, 2), (71, 1), (74, 1), (69, 4),
             (67, 2), (69, 1), (71, 1), (74, 2), (76, 1), (78, 1), (76, 2), (73, 2), (74, 4)]
THEME_MAJ_CH = ["D", "Bm", "G", "A", "Em", "Bm7", "A", "D"]


def shift(notes, semis):
    return [(None if p is None else p + semis, d) for p, d in notes]


# ---------------------------------------------------------------------------
# cues
# ---------------------------------------------------------------------------

def build_cues():
    C = []
    # 1 opening ------------------------------------------------------------
    c = Cue("opening", 0.0, T("L03b") - 1.0, bpm=66, gain=0.9, fade_in=0.02, fade_out=2.6)
    c.inst("harp", 0, 95, pan=50)
    c.inst("strings", 1, 80)
    c.inst("cello", 2, 80, pan=58)
    c.inst("panflute", 3, 80, pan=70)
    ch = ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A"]
    harp_arps(c, "harp", ch * 2, 0, 4, vel=52)
    pad_chords(c, "strings", ch * 2, 0, 4, vel=42)
    c.ramp("strings", 0, 6, 70, 100)
    bass_line(c, "cello", ch * 2, 0, 4, vel=48, octave=38)
    melody(c, "panflute", shift(THEME_MIN, -12), 16, vel=62)
    C.append(c)
    # 1b mystery: "I am here because my Father has willed it" ---------------
    c = Cue("mystery", T("L03b") - 1.4, T("L04") - 0.3, bpm=54, gain=2.2, fade_in=2.2, fade_out=1.8)
    c.inst("strings", 1, 72)
    c.inst("cello", 2, 70)
    c.inst("choir", 3, 72)
    c.inst("harp", 0, 70, pan=58)
    ch = ["Dm", "Bb/D", "Gm/D", "A/D", "Dm", "Bb/D", "Gm/D", "Dsus2"]
    e = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, e, vel=34, lo=55, hi=74, n=3)
    pad_chords(c, "choir", ch, 0, e, vel=40, lo=62, hi=79, n=3)
    fb = c.b(T("L03b", seg=1) - c.start)
    c.ramp("choir", 0, fb, 30, 70)
    c.ramp("choir", fb, fb + 6, 70, 105)
    c.note("cello", 0, c.beats, 38, 40)  # low D pedal
    for k, b in enumerate(range(2, int(c.beats) - 2, 5)):
        c.note("harp", b, 3.0, [74, 81, 76, 69][k % 4], 34)
    C.append(c)
    # 2 teaching1 ----------------------------------------------------------
    c = Cue("teaching1", T("L04") - 0.8, T("L07") - 0.2, bpm=60, gain=1.5)
    c.inst("strings", 1, 85)
    c.inst("cello", 2, 75)
    c.inst("harp", 0, 80, pan=50)
    ch = ["Dm", "Bbmaj7", "F", "C", "Gm", "Bb", "F", "A7sus4", "A"]
    pad_chords(c, "strings", ch, 0, 3.4, vel=40)
    bass_line(c, "cello", ch, 0, 3.4, vel=42, octave=38)
    harp_arps(c, "harp", ch, 0, 3.4, vel=36, step=1.0, pattern=(0, 2, 4))
    C.append(c)
    # 3 exchange -----------------------------------------------------------
    c = Cue("exchange", T("L07") - 0.6, T("L10") - 0.3, bpm=72, gain=1.6)
    c.inst("strings", 1, 70)
    c.inst("cello", 2, 85)
    c.inst("oud", 3, 70, pan=80)
    c.inst("pad", 4, 60)
    ch = ["Dm", "Dm", "Gm", "C", "F", "A7", "Dm", "Dm"]
    pad_chords(c, "strings", ch, 0, 4, vel=34)
    # cello ostinato
    beats = c.beats
    b = 0.0
    pat = [50, 50, 57, 50, 53, 50, 57, 55]
    while b < beats:
        c.note("cello", b, 0.45, pat[int(b * 2) % len(pat)] - 12, 44)
        b += 0.5
    # Hijaz colour from Eli's challenge
    hb = c.b(T("L09") - c.start)
    hij = [62, 63, 66, 67, 69, 70, 72]
    figure = [(69, 1), (70, 0.5), (69, 0.5), (67, 1), (66, 0.5), (67, 0.5), (69, 2), (None, 2),
              (66, 1), (67, 0.5), (66, 0.5), (63, 1), (62, 1), (None, 2)]
    melody(c, "oud", figure, hb + 1, vel=58)
    melody(c, "oud", figure, hb + 13, vel=52)
    pad_chords(c, "pad", ["D", "Eb/D", "D", "Gm/D"], hb, 4, vel=30, lo=50, hi=70, n=3)
    C.append(c)
    # 4 father -------------------------------------------------------------
    c = Cue("father", T("L10") - 0.8, T("L12") - 0.3, bpm=60, gain=0.82)
    c.inst("strings", 1, 92)
    c.inst("cello", 2, 82)
    c.inst("choir", 3, 75)
    c.inst("harp", 0, 78, pan=48)
    ch = ["Dm", "Bb", "F", "C", "Dm", "Gm", "Bb", "C", "F", "A"]
    pad_chords(c, "strings", ch, 0, 2.2, vel=46)
    c.ramp("strings", 0, c.beats, 70, 118)
    bass_line(c, "cello", ch, 0, 2.2, vel=48, octave=38)
    harp_arps(c, "harp", ch, 0, 2.2, vel=40, step=0.55, pattern=(0, 1, 2, 3))
    cb = c.b(T("L10", seg=2) - c.start)
    pad_chords(c, "choir", ["F", "C", "Dm", "Gm", "Bb", "C", "F", "A"], cb, (c.beats - cb) / 8, vel=46, lo=60, hi=76, n=3)
    c.ramp("choir", cb, c.beats, 50, 110)
    C.append(c)
    # 5 plea ---------------------------------------------------------------
    c = Cue("plea", T("L12") - 0.6, T("L13") - 0.4, bpm=60, gain=1.0, fade_in=0.8, fade_out=0.8)
    c.inst("strings", 1, 80)
    c.inst("harp", 0, 70)
    c.note("strings", 0, c.beats, 69, 36)
    c.note("strings", 0, c.beats, 62, 30)
    c.note("harp", 1.0, 3, 74, 34)
    c.note("harp", 2.5, 3, 69, 30)
    C.append(c)
    # 6 bread of life (D major bloom) ---------------------------------------
    c = Cue("bread", T("L13") - 0.15, T.scene_end["shore"] + 2.6, bpm=58, gain=0.95, fade_in=0.4, fade_out=3.0)
    c.inst("strings", 1, 100)
    c.inst("choir", 3, 92)
    c.inst("cello", 2, 85)
    c.inst("harp", 0, 85)
    c.inst("oboe", 4, 70, pan=72)
    ch = ["D", "G/D", "D", "A/C#", "Bm", "G", "D/A", "A", "D"]
    each = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, each, vel=52, lo=57, hi=81, n=4)
    c.ramp("strings", 0, 3, 60, 115)
    pad_chords(c, "choir", ch, 0, each, vel=58, lo=60, hi=79, n=3)
    c.ramp("choir", 0, 2.5, 40, 112)
    c.ramp("choir", c.beats - 6, c.beats, 112, 60)
    bass_line(c, "cello", ch, 0, each, vel=55, octave=38)
    # rising harp gesture at "I am"
    for k, p in enumerate([50, 54, 57, 62, 66, 69, 74, 78, 81]):
        c.note("harp", k * 0.18, 3, p, 50 + k * 3)
    harp_arps(c, "harp", ch[1:], each, each, vel=40, step=0.6, pattern=(0, 2, 4, 5, 4, 2))
    melody(c, "oboe", THEME_MAJ[:9], c.b(T("L14", "end") - c.start) - 2, vel=50)
    C.append(c)
    # 7 synagogue murmur ---------------------------------------------------
    c = Cue("murmur", T.scene_end["shore"] + 0.6, T("L19") - 0.5, bpm=56, gain=1.3, fade_in=3.0)
    c.inst("bass", 2, 85)
    c.inst("pad", 4, 70)
    c.inst("oud", 3, 70, pan=40)
    c.inst("strings", 1, 70)
    c.note("bass", 0, c.beats, 38, 50)
    c.note("pad", 0, c.beats, 50, 40)
    c.note("pad", 0, c.beats, 57, 34)
    pad_chords(c, "strings", ["Dm", "Eb/D", "Dm", "Gm/D", "Dm"], 2, (c.beats - 2) / 5, vel=30, lo=53, hi=72, n=3)
    fig = [(62, 1), (63, 0.5), (62, 0.5), (None, 1.5), (60, 0.5), (62, 2), (None, 3)]
    melody(c, "oud", fig, 4, vel=48)
    melody(c, "oud", shift(fig, 7), 13, vel=44)
    C.append(c)
    # 8 authority ----------------------------------------------------------
    c = Cue("authority", T("L19") - 0.4, T("L22") - 0.9, bpm=60, gain=1.45)
    c.inst("strings", 1, 82)
    c.inst("cello", 2, 75)
    c.inst("harp", 0, 72)
    ch = ["F", "C/E", "Dm", "Bb", "F/A", "Gm", "C", "F", "Dm", "Bb", "C"]
    each = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, each, vel=38)
    bass_line(c, "cello", ch, 0, each, vel=40, octave=38)
    harp_arps(c, "harp", ch, 0, each, vel=32, step=1.0, pattern=(0, 2, 4, 2))
    C.append(c)
    # 9 living bread -------------------------------------------------------
    c = Cue("living", T("L22") - 1.2, T("L24") - 0.3, bpm=56, gain=0.85, fade_out=1.5)
    c.inst("strings", 1, 95)
    c.inst("choir", 3, 88)
    c.inst("cello", 2, 82)
    c.inst("harp", 0, 75)
    b1 = c.b(T("L23", seg=1) - c.start)
    ch1 = ["Bb", "F/A", "Gm", "Dm", "Bb", "C"]
    e1 = b1 / len(ch1)
    pad_chords(c, "strings", ch1, 0, e1, vel=48)
    pad_chords(c, "choir", ch1, 0, e1, vel=52, lo=60, hi=77, n=3)
    c.ramp("choir", 0, 3, 40, 105)
    bass_line(c, "cello", ch1, 0, e1, vel=50, octave=38)
    ch2 = ["Gm", "Gm/Bb", "A7sus4", "A"]
    e2 = (c.beats - b1) / len(ch2)
    pad_chords(c, "strings", ch2, b1, e2, vel=44)
    pad_chords(c, "choir", ch2, b1, e2, vel=40, lo=60, hi=76, n=3)
    c.ramp("choir", b1, c.beats, 100, 55)
    bass_line(c, "cello", ch2, b1, e2, vel=44, octave=38)
    C.append(c)
    # 10 uproar ------------------------------------------------------------
    c = Cue("uproar", T("L24") - 0.6, T("L25") - 0.05, bpm=90, gain=0.7, fade_in=0.6, fade_out=0.12)
    c.inst("trem", 1, 90)
    c.inst("timp", 5, 95)
    c.inst("bass", 2, 85)
    c.note("trem", 0, c.beats, 50, 50)
    c.note("trem", 0, c.beats, 57, 46)
    c.note("trem", 0, c.beats, 63, 44)
    c.ramp("trem", 0, c.beats, 60, 120)
    c.note("bass", 0, c.beats, 38, 60)
    k = c.beats - 6
    while k < c.beats - 0.1:
        c.note("timp", k, 0.2, 38, 40 + 60 * (k - (c.beats - 6)) / 6)
        k += 0.125
    C.append(c)
    # 11 drone -------------------------------------------------------------
    c = Cue("drone", T("L25") + 0.2, T("L26") + 0.8, bpm=60, gain=1.0, fade_in=2.5, fade_out=2.0)
    c.inst("bass", 2, 80)
    c.inst("pad", 4, 60)
    c.inst("strings", 1, 60)
    c.note("bass", 0, c.beats, 26, 45)
    c.note("pad", 0, c.beats, 38, 34)
    c.note("strings", 3, c.beats - 3, 81, 22)
    C.append(c)
    # 12 communion ---------------------------------------------------------
    c = Cue("communion", T("L26") - 0.2, T("L30") - 0.5, bpm=58, gain=1.45, fade_in=3.0)
    c.inst("strings", 1, 82)
    c.inst("cello", 2, 72)
    c.inst("harp", 0, 78)
    ch = ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A", "F", "Am", "Bb", "F", "Dm", "Bb", "C", "C"]
    each = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, each, vel=36)
    c.ramp("strings", 0, 8, 50, 100)
    bass_line(c, "cello", ch, 0, each, vel=38, octave=38)
    tb = c.b(T("L28") - c.start)
    harp_arps(c, "harp", ["F", "Am", "Bb", "F", "Dm", "Bb", "C", "C"], tb, (c.beats - tb) / 8, vel=34, step=0.75, pattern=(0, 2, 4, 5, 4, 2))
    C.append(c)
    # 13 final teaching ----------------------------------------------------
    c = Cue("final", T("L30") - 0.8, T.scene_end["synagogue"] + 2.4, bpm=56, gain=0.85, fade_out=2.6)
    c.inst("strings", 1, 98)
    c.inst("choir", 3, 85)
    c.inst("cello", 2, 82)
    c.inst("harp", 0, 78)
    ch = ["Bb", "C", "Dm", "Bb", "F/A", "Gm", "C", "F", "F"]
    each = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, each, vel=46)
    c.ramp("strings", 0, c.beats * 0.75, 60, 118)
    pad_chords(c, "choir", ch[4:], each * 4, each, vel=46, lo=60, hi=77, n=3)
    c.ramp("choir", each * 4, each * 7, 50, 108)
    bass_line(c, "cello", ch, 0, each, vel=48, octave=38)
    harp_arps(c, "harp", ch, 0, each, vel=34, step=0.75)
    C.append(c)
    # 14 lament ------------------------------------------------------------
    c = Cue("lament", T.scene_end["synagogue"] + 1.0, T("L34") - 0.6, bpm=54, gain=1.2, fade_in=2.5)
    c.inst("strings", 1, 72)
    c.inst("shaku", 3, 82, pan=68)
    c.inst("pad", 4, 60)
    ch = ["Dm", "Gm/D", "Dm", "A/C#", "Dm", "Bb", "Gm", "A"]
    each = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, each, vel=32, lo=53, hi=72, n=3)
    c.note("pad", 0, c.beats, 38, 30)
    slow = [(p, d * 1.25) for p, d in shift(THEME_MIN, -12)]
    melody(c, "shaku", slow[:9], 2, vel=60)
    melody(c, "shaku", slow[9:], 2 + sum(d for _, d in slow[:9]) + 1, vel=56)
    C.append(c)
    # 15 question ----------------------------------------------------------
    c = Cue("question", T("L34") - 1.0, T("L35") - 0.6, bpm=60, gain=1.1, fade_in=1.5, fade_out=1.2)
    c.inst("strings", 1, 70)
    c.note("strings", 0, c.beats, 57, 30)
    c.note("strings", 0, c.beats, 62, 26)
    C.append(c)
    # 16 confession -> end ---------------------------------------------------
    c = Cue("confession", T("L35") - 0.8, T("L37") - 0.1, bpm=60, gain=0.85, fade_in=2.0, fade_out=1.8)
    c.inst("harp", 0, 85)
    c.inst("strings", 1, 92)
    c.inst("cello", 2, 80)
    c.inst("choir", 3, 85)
    c.inst("oboe", 4, 72, pan=70)
    b_holy = c.b(T("L36", seg=1) - c.start)
    ch1 = ["Dm", "Bb", "F", "C", "Dm", "Bb", "C"]
    e1 = b_holy / len(ch1)
    harp_arps(c, "harp", ch1, 0, e1, vel=40, step=0.5, pattern=(0, 1, 2, 3, 4, 3))
    pad_chords(c, "strings", ch1, 0, e1, vel=40)
    c.ramp("strings", 0, b_holy, 60, 110)
    bass_line(c, "cello", ch1, 0, e1, vel=44, octave=38)
    rest = c.beats - b_holy
    ch2 = ["D", "G/D", "D", "Bm", "G", "A", "D", "D"]
    e2 = rest / len(ch2)
    pad_chords(c, "strings", ch2, b_holy, e2, vel=50, lo=57, hi=81)
    pad_chords(c, "choir", ch2, b_holy, e2, vel=52, lo=60, hi=79, n=3)
    c.ramp("choir", b_holy, b_holy + 3, 40, 110)
    bass_line(c, "cello", ch2, b_holy, e2, vel=50, octave=38)
    harp_arps(c, "harp", ch2, b_holy, e2, vel=40, step=0.5, pattern=(0, 2, 4, 5, 4, 2))
    melody(c, "oboe", [(69, 1), (74, 0.5), (76, 0.5), (78, 2.5)], b_holy + c.b(T("L36", "end") - T("L36", seg=1)) + 0.1, vel=56)
    C.append(c)
    # 17 prayer -> end: a still bed under "Father...", the theme's cadence as the title holds
    c = Cue("prayer", T("L37") - 1.5, T.total + 0.5, bpm=52, gain=1.3, fade_in=2.5, fade_out=4.0)
    c.inst("harp", 0, 78)
    c.inst("strings", 1, 88)
    c.inst("cello", 2, 76)
    c.inst("choir", 3, 80)
    c.inst("oboe", 4, 70, pan=70)
    ch = ["D", "G/D", "D", "Bm", "G", "Em", "A", "D", "D"]
    e = c.beats / len(ch)
    pad_chords(c, "strings", ch, 0, e, vel=38, lo=57, hi=78)
    bass_line(c, "cello", ch, 0, e, vel=40, octave=38)
    harp_arps(c, "harp", ch, 0, e, vel=30, step=1.0, pattern=(0, 2, 4, 2))
    hb = c.b(T("L37", seg=2) - c.start)
    pad_chords(c, "choir", ch, 0, e, vel=44, lo=60, hi=79, n=3)
    c.ramp("choir", 0, hb, 0, 40)
    c.ramp("choir", hb, hb + 5, 40, 100)
    melody(c, "oboe", [(76, 1), (73, 1), (74, 3)], c.b(T("L37", "end") + 0.4 - c.start), vel=54)
    C.append(c)
    # 18 accents: a few deep notes under the weightiest words, and high swells where Jesus lifts
    # his eyes to the Father (used sparingly, on top of the cues above)
    C += accents()
    return C


def deep(name, t, root=26, dur=4.5, vel=74, timp=True, gain=1.0):
    """A low, swelling note (contrabass + celli an octave up), with a soft timpani roll."""
    c = Cue(name, t - 0.25, t + dur, bpm=60, gain=gain, fade_in=0.2, fade_out=2.2)
    c.inst("bass", 2, 105)
    c.inst("cello", 6, 92)
    c.note("bass", 0.25, dur, root, vel)
    c.note("cello", 0.25, dur, root + 12, vel - 12)
    c.ramp("bass", 0.0, 1.3, 64, 124)
    c.ramp("bass", 1.3, dur, 124, 70)
    c.ramp("cello", 0.0, 1.3, 50, 110)
    c.ramp("cello", 1.3, dur, 110, 60)
    if timp:
        c.inst("timp", 5, 92)
        tp = root + 12 if root + 12 >= 38 else root + 24
        k = 0.0
        while k < 1.7:
            c.note("timp", 0.25 + k, 0.12, tp, 20 + 42 * np.sin(np.pi * k / 1.7))
            k += 0.09
    return c


def swell(name, t, pitches, dur=4.2, peak=1.7, gain=1.0, choir=True):
    """High strings (and choir an octave down) rising to a peak and settling."""
    c = Cue(name, t - 0.3, t + dur, bpm=60, gain=gain, fade_in=0.3, fade_out=2.0)
    c.inst("strings", 1, 104)
    for p in pitches:
        c.note("strings", 0.3, dur, p, 60)
    c.ramp("strings", 0.3, 0.3 + peak, 18, 120)
    c.ramp("strings", 0.3 + peak, dur, 120, 46)
    if choir:
        c.inst("choir", 3, 92)
        for p in pitches[:-1]:
            c.note("choir", 0.5, dur - 0.2, p - 12, 52)
        c.ramp("choir", 0.3, 0.3 + peak, 12, 108)
        c.ramp("choir", 0.3 + peak, dur, 108, 36)
    return c


def accents():
    return [
        deep("deep_l13", T("L13") - 0.05, root=26, gain=0.6),                          # "I am the bread of life"
        deep("deep_l23", T("L23", word="flesh"), root=31, gain=0.82),                    # "This bread is my flesh"
        swell("swell_l23", T("L23", word="life") - 0.4, [67, 70, 74, 79], gain=0.45),    # "...for the life of the world"
        deep("deep_l25", T("L25", seg=2), root=26, dur=5.0, gain=0.36),                 # "you have no life in you"
        swell("swell_l29", T("L29") + 0.15, [62, 69, 74, 81], dur=4.6, peak=2.0, gain=0.4),       # eyes to heaven: "the living Father"
        deep("deep_l34", T("L34") - 0.2, root=26, timp=False, vel=64, gain=0.32),        # "You do not want to leave too?"
        swell("swell_l37a", T("L37") - 0.2, [62, 66, 69, 74, 78], dur=4.0, gain=0.36),  # "Father..."
        swell("swell_l37b", T("L37", word="with") - 0.2, [74, 78, 81, 86], dur=4.4, gain=0.4),  # "...with a part of me in them"
        deep("deep_l37", T("L37", word="them#1") - 0.1, root=26, timp=False, vel=62, gain=0.6),
    ]


def hall_ir(sr, rt60=2.6, pre=0.02, seed=1):
    n = int(sr * rt60 * 1.2)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / sr
    env = np.exp(-6.9 * t / rt60)
    ir = np.zeros((n, 2))
    for c in range(2):
        noise = rng.standard_normal(n)
        # darken the tail over time (simple one-pole lowpass with rising coefficient)
        out = np.empty(n)
        y = 0.0
        a0 = 0.3
        for i in range(0, n, 256):
            a = min(0.92, a0 + 0.6 * (i / n))
            seg = noise[i:i + 256]
            o = np.empty(len(seg))
            for j, x in enumerate(seg):
                y = a * y + (1 - a) * x
                o[j] = y
            out[i:i + 256] = o
        ir[:, c] = out * env
    ir[: int(pre * sr)] = 0
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))
    return ir


def render_cue(c, ir):
    mid = os.path.join(OUT, c.name + ".mid")
    wav = os.path.join(OUT, c.name + "_dry.wav")
    c.write(mid)
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.5", "-r", str(SR), "-o", "synth.reverb.active=0",
                    "-o", "synth.chorus.active=0", "-F", wav, SF2, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    x, sr = sf.read(wav)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    wet = np.stack([fftconvolve(x[:, k], ir[:, k])[: len(x) + len(ir) // 2] for k in range(2)], 1)
    dry = np.pad(x, ((0, len(wet) - len(x)), (0, 0)))
    y = 0.72 * dry + 0.55 * wet
    return y


def build():
    cues = build_cues()
    ir = hall_ir(SR)
    total = int((T.total + 1.0) * SR)
    mix = np.zeros((total, 2))
    for c in cues:
        y = render_cue(c, ir)
        dur = c.end - c.start
        n = min(len(y), int((dur + c.fade_out) * SR))
        y = y[:n] * c.gain
        env = np.ones(n)
        fi = int(c.fade_in * SR)
        if fi > 0:
            env[:fi] = np.linspace(0, 1, fi) ** 1.5
        fo_start = int(dur * SR)
        fo = int(c.fade_out * SR)
        if fo_start < n:
            m = n - fo_start
            env[fo_start:] = np.linspace(1, 0, m) ** 1.5
        y *= env[:, None]
        a = int(c.start * SR)
        b = min(total, a + n)
        mix[a:b] += y[: b - a]
        print(f"{c.name:12s} {c.start:7.2f}-{c.end:7.2f} peak {np.max(np.abs(y)):.3f}")
    sf.write(os.path.join(OUT, "music.wav"), mix.astype(np.float32), SR)
    return mix


if __name__ == "__main__":
    build()
