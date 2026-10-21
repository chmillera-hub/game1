"""The band: an original spooky swing-polka arrangement + SFX, then the final song mix.

  python3 band.py  ->  build/song_mix.wav
"""
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, oaconvolve, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import score as SC  # noqa: E402
import synth as S  # noqa: E402

SR = S.SR
BUILD = os.path.join(HERE, "build")
B, BAR = SC.BEAT, SC.BAR

CH = {
    "Em": ("E2", "B1", ["E3", "G3", "B3"]), "Am": ("A1", "E2", ["A3", "C4", "E4"]),
    "B7": ("B1", "F#2", ["A3", "D#4", "F#4"]), "C": ("C2", "G2", ["G3", "C4", "E4"]),
    "D": ("D2", "A2", ["F#3", "A3", "D4"]), "G": ("G2", "D2", ["G3", "B3", "D4"]),
    "Fm": ("F2", "C2", ["F3", "Ab3", "C4"]), "Db": ("Db2", "Ab1", ["Ab3", "Db4", "F4"]),
    "Bbm": ("Bb1", "F2", ["Bb3", "Db4", "F4"]), "C7": ("C2", "G2", ["Bb3", "E4", "G4"]),
}


# ------------------------------------------------------------------ extra instruments
def kick(vel=0.9):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    ph = np.cumsum(52 * (1 + 2.2 * np.exp(-t * 32))) / SR
    y = np.sin(2 * np.pi * ph) * np.exp(-t * 7.5) + S.filt(S.noise(n), "lp", 2500) * np.exp(-t * 120) * 0.25
    return (y * vel).astype(np.float32)


def snare(vel=0.6, brush=False):
    n = int((0.5 if brush else 0.32) * SR)
    t = np.arange(n) / SR
    nz = S.filt(S.filt(S.noise(n), "hp", 1200), "lp", 7000)
    if brush:
        y = nz * np.exp(-t * 9) * 0.5 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.2
    else:
        y = nz * np.exp(-t * 18) * 0.8 + np.sin(2 * np.pi * 185 * t) * np.exp(-t * 25) * 0.5
    return (y * vel).astype(np.float32)


def hat(vel=0.3, open_=False):
    n = int((0.3 if open_ else 0.07) * SR)
    t = np.arange(n) / SR
    y = S.filt(S.noise(n), "hp", 7000) * np.exp(-t * (9 if open_ else 70))
    return (y * vel).astype(np.float32)


def clap(vel=0.5):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for k in range(3):
        i = int(k * 0.011 * SR)
        env[i:] += np.exp(-(t[: n - i]) * (60 if k < 2 else 16))
    y = S.filt(S.noise(n), "bp", 1500, 1.2) * env
    return (y * vel * 0.6).astype(np.float32)


def crash(vel=0.5):
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    y = S.filt(S.noise(n), "hp", 4000) * np.exp(-t * 2.2)
    for f in (3150, 4720, 6230, 8410):
        y += 0.08 * np.sin(2 * np.pi * f * t) * np.exp(-t * 3)
    return (y * vel * 0.5).astype(np.float32)


def shaker(vel=0.25):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    y = S.filt(S.noise(n), "bp", 6500, 1.5) * np.sin(np.pi * t / t[-1]) ** 2
    return (y * vel).astype(np.float32)


def tom(note, vel=0.6):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = S.hz(note)
    ph = np.cumsum(f * (1 + 0.5 * np.exp(-t * 20))) / SR
    return (np.sin(2 * np.pi * ph) * np.exp(-t * 6) * vel).astype(np.float32)


def xylo(note, vel=0.6):
    """Bony xylophone: bright wooden bar with a fast decay."""
    f = S.hz(note)
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.45 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t * 16)
    y += 0.15 * np.sin(2 * np.pi * f * 6.1 * t) * np.exp(-t * 30)
    y += S.filt(S.noise(n), "bp", min(f * 4, 9000), 2) * np.exp(-t * 200) * 0.4
    return (y * np.minimum(1, t / 0.001) * vel * 0.5).astype(np.float32)


def tuba(note, dur=0.35, vel=0.6):
    f = S.hz(note)
    n = int((dur + 0.12) * SR)
    t = np.arange(n) / SR
    ph = np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * 5 * t))) / SR
    x = (2 * (ph % 1.0) - 1).astype(np.float32)
    # dark body plus a brassy 'blat' at the attack
    y = S.filt(x, "lp", 480, 0.8) + S.filt(x, "lp", 2200, 0.7) * np.exp(-t * 14).astype(np.float32) * 0.6
    e = S.env_adsr(n, 0.012, 0.08, 0.75, 0.1, sustain_len=max(0.0, dur - 0.1))
    return (y * e * vel * 0.9).astype(np.float32)


def brass(notes, dur=0.3, vel=0.5):
    n = int((dur + 0.25) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for note in notes:
        f = S.hz(note)
        for d in (-0.004, 0.0, 0.005):
            ph = np.cumsum(f * (1 + d) * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))) / SR
            y += (2 * (ph % 1.0) - 1).astype(np.float32)
    y /= (len(notes) * 3) ** 0.5
    y = S.filt(y, "lp", 2600, 0.8) * 0.7 + S.filt(y, "lp", 900, 0.8) * 0.5
    e = S.env_adsr(n, 0.02, 0.1, 0.7, 0.18, sustain_len=max(0.0, dur - 0.12))
    return (y * e * vel).astype(np.float32)


def thunder(vel=0.8):
    n = int(3.5 * SR)
    t = np.arange(n) / SR
    crack = S.filt(S.noise(n), "hp", 800) * np.exp(-t * 9) * 0.5
    rumble = S.filt(S.pink(n), "lp", 160) * (np.exp(-t * 1.1) * (1 + 0.5 * np.sin(2 * np.pi * 1.7 * t)))
    y = crack + rumble * 1.4
    return (y / (np.abs(y).max() + 1e-9) * vel).astype(np.float32)


def rooster(vel=0.5):
    """Cock-a-doodle-doo: four nasal glides."""
    segs = [(0.0, 0.16, 820, 900), (0.2, 0.16, 900, 980), (0.4, 0.18, 980, 1040), (0.62, 0.75, 1080, 760)]
    out = np.zeros(int(1.5 * SR), np.float32)
    for st, d, f0, f1 in segs:
        n = int(d * SR)
        t = np.arange(n) / SR
        f = f0 + (f1 - f0) * (t / d) ** 1.5
        f = f * (1 + 0.02 * np.sin(2 * np.pi * 28 * t))
        ph = np.cumsum(f) / SR
        src = (2 * (ph % 1.0) - 1).astype(np.float32)
        y = S.filt(src, "bp", 1400, 3) + 0.8 * S.filt(src, "bp", 2600, 4) + 0.4 * S.filt(src, "bp", 900, 3)
        y *= S.env_adsr(n, 0.02, 0.05, 0.9, 0.08)
        i = int(st * SR)
        out[i:i + n] += y
    return out / (np.abs(out).max() + 1e-9) * vel


def bone_clatter(vel=0.6, dur=1.6, seed=3):
    rr = np.random.default_rng(seed)
    out = np.zeros(int((dur + 0.6) * SR), np.float32)
    k = 46
    for i in range(k):
        st = (i / k) ** 1.6 * dur + rr.uniform(-0.02, 0.02)
        note = 76 - int(i / k * 20) + int(rr.integers(-3, 4))
        y = xylo(note, vel * rr.uniform(0.3, 0.8))[: int(0.25 * SR)]
        y *= np.exp(-np.arange(len(y)) / SR * 18)
        j = int(max(0, st) * SR)
        out[j:j + len(y)] += y[: len(out) - j]
    return out


def knock(vel=0.6):
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    y = S.filt(S.noise(n), "bp", 380, 3) * np.exp(-t * 45) + np.sin(2 * np.pi * 140 * t) * np.exp(-t * 38) * 0.6
    return (y * vel).astype(np.float32)


# ------------------------------------------------------------------ arrangement
class Band:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.bus = {k: np.zeros((self.n, 2), np.float32) for k in ("drums", "bass", "keys", "lead", "sfx")}

    def add(self, bus, t, y, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i < 0 or i >= self.n:
            return
        m = min(len(y), self.n - i)
        a = (pan + 1) * math.pi / 4
        self.bus[bus][i:i + m, 0] += y[:m] * gain * math.cos(a)
        self.bus[bus][i:i + m, 1] += y[:m] * gain * math.sin(a)


def bar_t(bar, beat=0.0):
    return bar * BAR + beat * B


def swing_t(bar, eighth):
    """Time of the n-th eighth note in a bar, swung."""
    beat = eighth // 2
    off = (SC.SWING if eighth % 2 else 0.0)
    return bar_t(bar, beat + off)


def chord_at(chords, k, half):
    c = chords[k]
    if "/" in c:
        a, b2 = c.split("/")
        return a if half == 0 else b2
    return c


def groove(Bd, bar, chords_k, style):
    """One bar of groove. style: verse / chorus / bridge / pre / xylo."""
    name0 = chord_at(*chords_k, 0)
    name1 = chord_at(*chords_k, 1)
    if name0 == "NC":
        return
    # drums
    for beat in range(4):
        tb = bar_t(bar, beat)
        if style in ("chorus",) or (style == "pre" and beat % 2 == 0) or (beat % 2 == 0 and style != "bridge"):
            Bd.add("drums", tb, kick(0.9 if beat % 2 == 0 else 0.7), 1.0)
        if style == "bridge" and beat == 0:
            Bd.add("drums", tb, kick(0.85), 1.0)
        if beat % 2 == 1:
            if style == "bridge":
                Bd.add("drums", tb, clap(0.35), 1.0, 0.1)
            else:
                Bd.add("drums", tb, snare(0.55 if style != "verse" else 0.45, brush=(style == "verse")), 1.0, 0.05)
                if style == "chorus":
                    Bd.add("drums", tb + 0.004, clap(0.55), 1.0, -0.15)
    for e in range(8):
        te = swing_t(bar, e)
        Bd.add("drums", te, hat(0.22 if e % 2 else 0.3, open_=(style == "chorus" and e == 7)), 1.0, 0.35)
        if style in ("chorus", "xylo") and e % 2:
            Bd.add("drums", te, shaker(0.2), 1.0, -0.4)
    # oom-pah: tuba on 1 & 3 (root, fifth), stabs on 2 & 4
    for beat in range(4):
        name = name0 if beat < 2 else name1
        root, fifth, upper = CH[name]
        tb = bar_t(bar, beat)
        if beat % 2 == 0:
            note = root if beat == 0 else fifth
            Bd.add("bass", tb, tuba(note, 0.36, 0.7), 1.0, 0.0)
        elif style != "bridge":
            for j, nt in enumerate(upper):
                Bd.add("keys", tb, S.pizz(nt, 0.3, 0.32), 1.0, 0.3 - 0.2 * j)
            if style in ("chorus", "pre"):
                Bd.add("keys", tb, S.organ(upper, 0.18, 0.28, 0.005, 0.08), 1.0, -0.2)
    if style in ("chorus", "pre"):
        root, fifth, upper = CH[name0]
        Bd.add("keys", bar_t(bar), S.organ([root] + upper, BAR * 0.95, 0.14, 0.05, 0.3), 1.0, 0.0)


def build(Bd):
    secs = {name: (b0, nb, ch) for name, b0, nb, ch in SC.SECTIONS}
    styles = {"verse1": "verse", "verse2": "verse", "pre1": "pre", "pre2": "pre", "chorus1": "chorus",
              "chorus2": "chorus", "chorus3": "chorus", "chorus4": "chorus", "bridge": "bridge", "xylo": "xylo"}
    for name, (b0, nb, chords) in secs.items():
        if name in styles:
            for k in range(nb):
                if name == "pre2" and k >= 2:
                    continue  # stop-time under the cat's line
                if name == "bridge" and k in (6,):
                    continue  # FREEZE
                groove(Bd, b0 + k, (chords, k), styles[name])

    # ---------------- intro: thunder, organ, theremin motif, knocks, a drum fill
    Bd.add("sfx", 0.0, thunder(0.9), 1.0, 0.0)
    Bd.add("keys", 0.0, S.organ(["E2", "B2", "E3", "G3"], BAR * 2, 0.35, 0.05, 1.2), 1.0, 0.0)
    th = [("B4", 0.5), ("C5", 0.5), ("B4", 1.0), ("G4", 1.0), ("F#4", 1.5), ("D#4", 1.5), ("E4", 2.0)]
    tt = bar_t(0, 1.0)
    for nt, bb in th:
        f0 = S.hz(nt)
        Bd.add("lead", tt, S.theremin(lambda x, f=f0: f * np.ones_like(x), bb * B * 0.98, 0.3), 1.0, 0.25)
        tt += bb * B
    for k in range(3):
        Bd.add("sfx", bar_t(2, k * 0.5 + 0.5), knock(0.7), 1.0, -0.2)
    for k in range(3):
        Bd.add("sfx", bar_t(3, k * 0.5), knock(0.8), 1.0, 0.2)
    Bd.add("keys", bar_t(2), S.organ(["C3", "G3", "C4", "E4"], BAR, 0.3, 0.05, 0.4), 1.0, 0.0)
    Bd.add("keys", bar_t(3), S.organ(["B2", "F#3", "A3", "D#4"], BAR * 0.9, 0.32, 0.05, 0.3), 1.0, 0.0)
    for k, nt in enumerate(("B2", "D3", "E3", "F#3", "G3", "A3", "A#3", "B3")):
        Bd.add("drums", bar_t(3, 2 + k * 0.25), tom(nt, 0.45), 1.0, -0.4 + k * 0.1)
    Bd.add("drums", bar_t(4), crash(0.6), 1.0, 0.2)

    # ---------------- xylophone answers in the verses (bones!)
    fills = [("B4", .25), ("A4", .25), ("G4", .25), ("F#4", .25), ("E4", .5), ("B3", .5)]
    for vb in (4, 6, 8, 10, 24, 26, 28, 30):
        tt = bar_t(vb + 1, 2.0)
        for nt, bb in fills:
            Bd.add("lead", tt, xylo(nt, 0.55), 1.0, 0.4)
            tt += bb * B
    # bassoon counter-line in verse 2
    for vb in (24, 28):
        tt = bar_t(vb, 0)
        for nt, bb in (("E3", 1), ("G3", 1), ("B3", 1), ("A3", 1), ("G3", 2), ("F#3", 2)):
            Bd.add("lead", tt, S.reed(nt, bb * B * 0.9, 0.22, "bassoon", stacc=False), 1.0, -0.35)
            tt += bb * B

    # ---------------- pre-chorus builds
    for pb in (12, 32):
        Bd.add("lead", bar_t(pb), S.theremin(lambda x: S.hz("E4") * 2 ** (x / (4 * BAR)), 4 * BAR * 0.98, 0.16), 1.0,
               -0.3)
        for k in range(16):
            Bd.add("drums", bar_t(pb + 3, k * 0.25), snare(0.15 + 0.03 * k), 1.0, 0.0)
        Bd.add("drums", bar_t(pb + 4), crash(0.7), 1.0, -0.2)
    # stop-time for the cat in pre2: just a tick-tock and a hiss
    for k in range(8):
        Bd.add("sfx", bar_t(34, k), S.fx_tick(0.25, 1.0 if k % 2 == 0 else 0.8), 1.0, 0.3)

    # ---------------- choruses: hook doubling, brass hits, choir in the finals
    for cb, final in ((16, False), (36, False), (56, True), (64, True)):
        tr = 1 if final else 0
        hook = [(0, 0, "B4"), (0, 0.5, "B4"), (0, 1.0, "B4"), (0, 1.5, "E5"), (1, 0, "C5"), (1, 0.5, "C5"), (1, 1.0, "C5"),
                (1, 1.5, "B4"), (4, 0, "B4"), (4, 0.5, "B4"), (4, 1.0, "B4"), (4, 1.5, "E5")]
        for (bb, beat, nt) in hook:
            Bd.add("lead", bar_t(cb + bb, beat), xylo(S.midi(nt) + tr, 0.35), 1.0, 0.35)
        for (bb, beat, chord) in ((0, 1.5, "Em"), (1, 1.5, "C"), (3, 1.5, "B7"), (4, 1.5, "Em"), (7, 0.0, "Em")):
            root, fifth, upper = CH[chord]
            notes = [S.midi(n) + tr + 12 for n in upper[:2]] + [S.midi(upper[2]) + tr]
            Bd.add("keys", bar_t(cb + bb, beat), brass(notes, 0.28 if bb != 7 else 0.9, 0.42), 1.0, -0.1)
        Bd.add("drums", bar_t(cb + 7, 0), crash(0.55), 1.0, 0.25)
        if final:
            for k in range(4):
                root, fifth, upper = CH[["Fm", "Db", "Bbm", "C7"][k]]
                Bd.add("keys", bar_t(cb + 2 * k), S.choir([n for n in upper], 2 * BAR * 0.98, 0.18, "ah", 0.3, 0.6), 1.0,
                       0.0)
        if cb == 64:
            for k in range(8):
                Bd.add("lead", bar_t(cb + k, 3.5), S.glock(S.midi("F6") + (k % 3) * 3, 0.5, 0.25), 1.0, -0.4)

    # ---------------- bridge: dark groove, then FREEZE
    for k in range(6):
        Bd.add("keys", bar_t(44 + k), S.organ(["E2", "B2"], BAR * 0.95, 0.12, 0.1, 0.2), 1.0, 0.0)
        for e in range(4):
            Bd.add("drums", swing_t(44 + k, 2 * e + 1), clap(0.12), 1.0, 0.5 if e % 2 else -0.5)
    Bd.add("keys", bar_t(50), brass(["E3", "G3", "B3", "E4"], 0.35, 0.55), 1.0, 0.0)
    Bd.add("drums", bar_t(50), crash(0.5), 1.0, 0.0)
    for k, nt in enumerate(("B2", "D3", "E3", "G3")):
        Bd.add("drums", bar_t(51, 2.0 + k * 0.5), tom(nt, 0.5), 1.0, -0.3 + k * 0.2)
    Bd.add("drums", bar_t(52), crash(0.7), 1.0, 0.0)

    # ---------------- xylophone solo on the ribs
    solo = [("E5", .5), ("G5", .5), ("B5", .5), ("G5", .5), ("E5", .5), ("D#5", .5), ("E5", 1),
            ("C6", .5), ("B5", .5), ("A5", .5), ("G5", .5), ("E5", 1), ("_", 1),
            ("A5", .5), ("C6", .5), ("E6", .5), ("C6", .5), ("A5", .5), ("G5", .5), ("F#5", 1),
            ("B5", .25), ("A5", .25), ("G5", .25), ("F#5", .25), ("E5", .25), ("D#5", .25), ("C5", .25), ("B4", .25),
            ("B4", .5), ("D#5", .5), ("F#5", .5), ("B5", .5)]
    tt = bar_t(52)
    for nt, bb in solo:
        if nt != "_":
            Bd.add("lead", tt, xylo(nt, 0.75), 1.0, 0.2)
        tt += bb * B

    # ---------------- outro: last stab, rooster, collapse, button
    Bd.add("keys", bar_t(72), brass(["F3", "Ab3", "C4", "F4"], 0.6, 0.6), 1.0, 0.0)
    Bd.add("bass", bar_t(72), tuba("F2", 0.6, 0.8), 1.0, 0.0)
    Bd.add("drums", bar_t(72), crash(0.6), 1.0, 0.0)
    Bd.add("sfx", bar_t(72, 1.6), rooster(0.55), 1.0, 0.4)
    Bd.add("sfx", bar_t(74, 0.5), bone_clatter(0.75, 1.6), 1.0, 0.0)
    Bd.add("lead", bar_t(76, 3.0), S.theremin(lambda x: 600 - 200 * x, 0.6, 0.18), 1.0, 0.3)
    Bd.add("keys", bar_t(77, 0.25), brass(["F3", "Ab3", "C4", "F4"], 1.6, 0.6), 1.0, 0.0)
    Bd.add("bass", bar_t(77, 0.25), tuba("F2", 1.4, 0.8), 1.0, 0.0)
    Bd.add("drums", bar_t(77, 0.25), crash(0.7), 1.0, 0.0)
    Bd.add("lead", bar_t(77, 0.25), S.sparkle(1.5, 0.3, notes=("F6", "Ab6", "C7", "F5"), density=10), 1.0, 0.0)


def reverb_ir(seconds, seed, damp):
    n = int(seconds * SR)
    rr = np.random.default_rng(seed)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2), np.float32)
    for ch in range(2):
        x = rr.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / seconds)
        ir[:, ch] = S.filt(x, "lp", damp, 0.6)
    ir = np.vstack([np.zeros((int(0.02 * SR), 2), np.float32), ir])
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def conv(x, ir):
    out = np.zeros_like(x)
    for ch in range(2):
        out[:, ch] = oaconvolve(x[:, ch], ir[:, ch])[: len(x)]
    return out


def hp(x, f):
    sos = butter(2, f, btype="high", fs=SR, output="sos")
    return np.stack([sosfiltfilt(sos, x[:, c]) for c in range(2)], axis=1).astype(np.float32)


def presence(x, gain=0.35):
    """Gentle 2-5 kHz lift for vocal clarity."""
    sos = butter(2, [2000, 5000], btype="band", fs=SR, output="sos")
    return x + gain * np.stack([sosfiltfilt(sos, x[:, c]) for c in range(2)], axis=1).astype(np.float32)


def band_duck(x, duck, d_low, d_mid, d_high):
    """Duck mostly in the speech band (250 Hz - 3.5 kHz) while voices sing."""
    lo = butter(4, 250, btype="low", fs=SR, output="sos")
    hi = butter(4, 3500, btype="high", fs=SR, output="sos")
    out = np.zeros_like(x)
    dk = duck[:, 0]
    for ch in range(2):
        low = sosfiltfilt(lo, x[:, ch]).astype(np.float32)
        high = sosfiltfilt(hi, x[:, ch]).astype(np.float32)
        mid = x[:, ch] - low - high
        out[:, ch] = low * (1 - d_low * dk) + mid * (1 - d_mid * dk) + high * (1 - d_high * dk)
    return out


def main():
    dur = SC.TOTAL_BARS * SC.BAR + 2.0
    Bd = Band(dur)
    build(Bd)
    vox = {}
    for k in ("lead", "gang", "kids", "spoken"):
        y, sr = sf.read(os.path.join(BUILD, f"vox_{k}.wav"), dtype="float32")
        y = y[: Bd.n]
        if len(y) < Bd.n:
            y = np.pad(y, ((0, Bd.n - len(y)), (0, 0)))
        vox[k] = hp(y, 90)
    lead = presence(vox["lead"]) * 1.0
    gang = presence(vox["gang"]) * 0.75
    kids = vox["kids"] * 0.8
    spoken = presence(vox["spoken"]) * 1.05
    # slapback on the lead singer (eighth note, quiet)
    d = int(B / 2 * SR)
    slap = np.zeros_like(lead)
    slap[d:] = lead[:-d] * 0.16
    vox_all = lead + slap + gang + kids + spoken
    # band ducks a little under the voices
    env = np.abs(vox_all).max(axis=1)
    hop = SR // 100
    nb = len(env) // hop
    e = env[: nb * hop].reshape(nb, hop).max(axis=1)
    sm = np.zeros(nb)
    s = 0.0
    for i in range(nb):
        a = min(1.0, e[i] / 0.08)
        s = s + (a - s) * (0.5 if a > s else 0.05)
        sm[i] = s
    duck = np.pad(np.repeat(sm, hop), (0, Bd.n - nb * hop), mode="edge")[:, None]
    drums = band_duck(Bd.bus["drums"], duck, 0.1, 0.45, 0.2) * 0.62
    bass = hp(Bd.bus["bass"], 35) * 0.72
    keys = band_duck(Bd.bus["keys"], duck, 0.2, 0.8, 0.4) * 0.5
    leadi = band_duck(Bd.bus["lead"], duck, 0.2, 0.75, 0.4) * 0.55
    sfx = Bd.bus["sfx"] * 0.8
    band = drums + bass + keys + leadi + sfx
    plate = reverb_ir(1.3, 4, 5000)
    hall = reverb_ir(2.2, 6, 3800)
    wet = conv(vox_all * 0.5, plate) * 0.22 + conv(keys + leadi + sfx * 0.5, hall) * 0.18
    mix = band + vox_all * 1.9 + wet
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.5) / np.tanh(1.5) * 0.9
    sf.write(os.path.join(BUILD, "song_mix.wav"), mix.astype(np.float32), SR, subtype="FLOAT")
    np.save(os.path.join(BUILD, "dbg_vox.npy"), vox_all[::8].mean(axis=1))
    np.save(os.path.join(BUILD, "dbg_band.npy"), band[::8].mean(axis=1))
    print("mix", mix.shape, "dur %.2f" % (len(mix) / SR))


if __name__ == "__main__":
    main()
