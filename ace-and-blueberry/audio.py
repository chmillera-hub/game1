"""Synthesises the music + sound effects and mixes them with the voices -> mix.wav"""
import os, sys, json
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
TL = json.load(open(os.path.join(HERE, "timeline.json")))
DUR = TL["duration"]
N = int(np.ceil((DUR + 0.5) * SR))
rs = np.random.RandomState(1234)

LINES = {l["id"]: l for l in TL["lines"]}
SCN = {s["name"]: s for s in TL["scenes"]}
def M(n): return TL["marks"][n]
def LS(i): return LINES[i]["start"]
def LE(i): return LINES[i]["end"]

def midi_hz(m): return 440.0 * 2 ** ((m - 69) / 12)

# ------------------------------------------------------------ instruments --
INSTR = {
    # partials (ratio, amp), base decay (s), attack (s), partial decay exponent
    "pluck":    ([(1, 1), (2, .5), (3, .28), (4, .16), (5, .08)], 0.55, 0.004, 1.0),
    "glock":    ([(1, 1), (2.76, .32), (5.4, .12), (8.93, .05)], 0.95, 0.002, 1.2),
    "musicbox": ([(1, 1), (2, .22), (3.01, .1), (4.1, .05)], 1.4, 0.002, 1.0),
    "marimba":  ([(1, 1), (3.93, .28), (9.2, .05)], 0.42, 0.003, 1.3),
    "bass":     ([(1, 1), (2, .35), (3, .1)], 0.55, 0.008, 0.8),
    "pizz":     ([(1, 1), (2, .55), (3, .32), (4, .18), (5, .1)], 0.2, 0.003, 0.8),
    "harp":     ([(1, 1), (2, .4), (3, .18), (4, .08)], 1.1, 0.003, 1.0),
}

def note(instr, m, dur, vel=1.0):
    parts, dec, att, ex = INSTR[instr]
    f = midi_hz(m)
    length = min(dur + dec * 2.5, 4.0)
    t = np.arange(int(length * SR)) / SR
    y = np.zeros_like(t)
    for r, a in parts:
        if f * r > 16000: continue
        d = dec / (r ** (0.5 * ex))
        y += a * np.sin(2 * np.pi * f * r * t + rs.rand() * 6) * np.exp(-t / d)
    env = np.minimum(1, t / att)
    # release at end of note duration for long-decay instruments
    rel = np.clip(1 - (t - dur - 0.15) / 0.5, 0, 1) if instr in ("musicbox", "glock", "harp") else 1
    return y * env * rel * vel * 0.25

def pad_chord(ms, dur, vel=1.0):
    t = np.arange(int((dur + 1.0) * SR)) / SR
    y = np.zeros_like(t)
    for m in ms:
        f = midi_hz(m)
        for det in (-0.12, 0.0, 0.12):
            ff = f * 2 ** (det / 12)
            y += np.sin(2 * np.pi * ff * t + rs.rand() * 6) + 0.18 * np.sin(4 * np.pi * ff * t)
    env = np.minimum(1, t / 0.35) * np.clip(1 - (t - dur) / 0.9, 0, 1)
    return y * env * vel * 0.02

def noise_burst(dur, hp=4000, decay=0.03, vel=1.0):
    n = int(dur * SR)
    x = rs.randn(n)
    sos = butter(2, hp, "hp", fs=SR, output="sos")
    x = sosfilt(sos, x)
    t = np.arange(n) / SR
    return x * np.exp(-t / decay) * vel * 0.12

def kick(vel=1.0):
    t = np.arange(int(0.25 * SR)) / SR
    f = 50 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09) * vel * 0.35

CHORDS = {  # root (midi), chord tones
    "C": (48, [60, 64, 67]), "Am": (45, [57, 60, 64]), "F": (41, [57, 60, 65]), "G": (43, [55, 59, 62]),
    "Dm": (50, [57, 62, 65]), "E": (40, [56, 59, 64]), "Em": (40, [55, 59, 64]), "D": (50, [54, 57, 62]),
    "Bb": (46, [58, 62, 65]), "Gm": (43, [55, 58, 62]),
}

# ------------------------------------------------------------------ cues --
THEME_MEL = [
    [(0, 76, 1), (1, 79, 1), (2, 76, .5), (2.5, 74, .5), (3, 72, 1)],
    [(0, 69, 1), (1, 72, 1), (2, 76, 1.5), (3.5, 74, .5)],
    [(0, 72, 1), (1, 69, .5), (1.5, 72, .5), (2, 77, 1), (3, 76, 1)],
    [(0, 74, 1.5), (1.5, 71, .5), (2, 67, 2)],
    [(0, 76, 1), (1, 79, 1), (2, 81, 1), (3, 79, 1)],
    [(0, 76, 1), (1, 72, 1), (2, 74, 1), (3, 76, 1)],
    [(0, 77, 1), (1, 76, .5), (1.5, 74, .5), (2, 74, 1), (3, 71, 1)],
    [(0, 72, 3)],
]
THEME_CH = [["C"], ["Am"], ["F"], ["G"], ["C"], ["Am"], ["F", "G"], ["C"]]

class Track:
    def __init__(self, dur):
        self.buf = np.zeros(int((dur + 5) * SR))
    def add(self, y, t, gain=1.0):
        i = int(t * SR)
        if i < 0: y = y[-i:]; i = 0
        j = min(len(self.buf), i + len(y))
        if j > i: self.buf[i:j] += y[:j - i] * gain

def cue_theme(dur, bpm=100, melody=True, perc=True, mel_instr="glock", mel_gain=0.55, bright=1.0):
    tr = Track(dur); spb = 60 / bpm; bar = 4 * spb; b = 0
    while b * bar < dur:
        k = b % 8; t0 = b * bar
        chs = THEME_CH[k]
        for ci, ch in enumerate(chs):
            root, tones = CHORDS[ch]
            seg = 4 / len(chs); s0 = t0 + ci * seg * spb
            # ukulele-ish strums
            for beat in ([0, 1.5, 2, 3] if len(chs) == 1 else [0, 1]):
                if beat >= seg: continue
                for n_i, m in enumerate(tones + [tones[0] + 12]):
                    tr.add(note("pluck", m, 0.4, 0.55 if beat else 0.7), s0 + beat * spb + n_i * 0.012)
            tr.add(note("bass", root, spb * 1.5, 0.9), s0)
            if len(chs) == 1: tr.add(note("bass", root + 7, spb, 0.7), s0 + 2 * spb)
        if melody:
            for (bt, m, d) in THEME_MEL[k]:
                tr.add(note(mel_instr, m + 12 * (bright > 1), d * spb, mel_gain), t0 + bt * spb)
        if perc:
            for e in range(8):
                tr.add(noise_burst(0.06, 6000, 0.018, 0.45 if e % 2 else 0.7), t0 + e * spb / 2)
            tr.add(kick(0.6), t0); tr.add(kick(0.45), t0 + 2 * spb)
        b += 1
    return tr.buf

def cue_playful(dur, bpm=132):
    tr = Track(dur); spb = 60 / bpm; bar = 4 * spb
    prog = ["C", "F", "G", "C", "Am", "F", "G", "C"]
    runs = [[72, 76, 79, 84, 79, 76, 72, 76], [77, 81, 84, 81, 77, 72, 77, 81], [79, 83, 86, 83, 79, 74, 71, 74], [72, None, 79, None, 84, None, None, None],
            [69, 72, 76, 81, 76, 72, 69, 72], [77, 81, 84, 81, 77, 72, 77, 81], [79, 83, 86, 83, 79, 74, 71, 74], [84, None, 79, None, 72, None, None, None]]
    b = 0
    while b * bar < dur:
        k = b % 8; t0 = b * bar
        root, tones = CHORDS[prog[k]]
        for q in range(4):
            tr.add(note("pizz", root + (0 if q % 2 == 0 else 7) + 12, spb * 0.5, 0.9), t0 + q * spb)
            if q % 2 == 1:
                for m in tones: tr.add(note("pluck", m + 12, 0.15, 0.4), t0 + q * spb + 0.01)
        for e, m in enumerate(runs[k]):
            if m: tr.add(note("marimba", m, spb / 2, 0.55), t0 + e * spb / 2)
        for e in range(8): tr.add(noise_burst(0.05, 7000, 0.015, 0.5), t0 + e * spb / 2)
        b += 1
    return tr.buf

def cue_think(dur, bpm=92):
    tr = Track(dur); spb = 60 / bpm; bar = 4 * spb
    prog = ["Am", "Dm", "E", "Am", "F", "Dm", "E", "E"]
    mel = [[(0, 76), (1, 72), (2, 69), (3, 72)], [(0, 77), (1, 74), (2, 69), (3, 74)], [(0, 76), (1, 80), (2, 83), (3, 80)], [(0, 81), (2, 76)],
           [(0, 77), (.5, 76), (1, 77), (2, 81), (3, 77)], [(0, 74), (1, 77), (2, 81), (3, 77)], [(0, 76), (1, 80), (1.5, 83), (2, 88)], [(0, 83), (2, 80), (3, 76)]]
    b = 0
    while b * bar < dur:
        k = b % 8; t0 = b * bar
        root, tones = CHORDS[prog[k]]
        for q, iv in enumerate([0, 7, 12, 7]):
            tr.add(note("pizz", root + iv, spb * 0.4, 0.9), t0 + q * spb)
        for (bt, m) in mel[k]:
            tr.add(note("marimba", m - 12, 0.3, 0.5), t0 + bt * spb + 0.5 * spb)
            if k % 4 == 3: tr.add(note("glock", m + 12, 0.3, 0.12), t0 + bt * spb + 0.5 * spb)
        tr.add(noise_burst(0.04, 8000, 0.01, 0.4), t0 + 1.5 * spb); tr.add(noise_burst(0.04, 8000, 0.01, 0.4), t0 + 3.5 * spb)
        b += 1
    return tr.buf

def cue_lullaby(dur, bpm=66):
    tr = Track(dur); spb = 60 / bpm; bar = 3 * spb
    prog = [["F"], ["Dm"], ["Bb"], ["C"], ["F"], ["Dm"], ["Gm", "C"], ["F"]]
    mel = [[(0, 84, 2), (2, 81, 1)], [(0, 86, 2), (2, 81, 1)], [(0, 86, 1), (1, 84, 1), (2, 82, 1)], [(0, 79, 3)],
           [(0, 84, 2), (2, 81, 1)], [(0, 89, 2), (2, 86, 1)], [(0, 82, 1), (1, 81, 1), (2, 79, 1)], [(0, 77, 3)]]
    b = 0
    while b * bar < dur:
        k = b % 8; t0 = b * bar
        chs = prog[k]
        for ci, ch in enumerate(chs):
            root, tones = CHORDS[ch]
            seg = 3 / len(chs); s0 = t0 + ci * seg * spb
            arp = [root + 12, root + 19, root + 24, tones[1] + 12, root + 24, root + 19]
            for e in range(int(seg * 2)):
                tr.add(note("harp", arp[e % 6], spb * 0.5, 0.45), s0 + e * spb / 2)
            tr.add(pad_chord([m for m in tones], seg * spb, 0.8), s0)
        for (bt, m, d) in mel[k]:
            tr.add(note("musicbox", m, d * spb, 0.55), t0 + bt * spb)
        b += 1
    return tr.buf

def cue_morning(dur, bpm=96):
    tr = Track(dur); spb = 60 / bpm; bar = 4 * spb
    prog = ["G", "Em", "C", "D"]
    b = 0
    while b * bar < dur:
        k = b % 4; t0 = b * bar
        root, tones = CHORDS[prog[k]]
        arp = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 12 + 12 * 0]
        for e in range(8):
            tr.add(note("marimba", arp[e % 4] + (12 if e in (3, 7) else 0), spb / 2, 0.5), t0 + e * spb / 2)
        tr.add(note("bass", root, spb * 2, 0.8), t0); tr.add(note("bass", root + 7, spb, 0.6), t0 + 2 * spb)
        if b % 2 == 0: tr.add(note("glock", tones[2] + 24, spb, 0.25), t0 + 2.5 * spb)
        b += 1
    return tr.buf

def cue_end(dur):
    # last phrase of the theme slowing down, then a big final chord + sparkle arpeggio
    tr = Track(dur); t = 0.0
    spb = 60 / 96
    for k in (4, 5, 6, 7):
        chs = THEME_CH[k]
        for ci, ch in enumerate(chs):
            root, tones = CHORDS[ch]
            s0 = t + ci * (4 / len(chs)) * spb
            for n_i, m in enumerate(tones + [tones[0] + 12]): tr.add(note("pluck", m, 0.5, 0.6), s0 + n_i * 0.015)
            tr.add(note("bass", root, spb * 2, 0.8), s0)
        for (bt, m, d) in THEME_MEL[k]: tr.add(note("glock", m, d * spb, 0.5), t + bt * spb)
        t += 4 * spb
        spb *= 1.06
    # final chord
    for m in [48, 60, 64, 67, 72, 76, 79]:
        tr.add(note("harp", m, 2.5, 0.7), t)
    tr.add(pad_chord([60, 64, 67, 72], 3.5, 1.2), t)
    for i, m in enumerate([84, 88, 91, 96, 100]):
        tr.add(note("glock", m, 0.4, 0.4), t + 0.08 * i)
    return tr.buf

CUES = {
    "title": lambda d: cue_theme(d, 100),
    "theme": lambda d: cue_theme(d, 100, mel_gain=0.42),
    "playful": cue_playful,
    "think": cue_think,
    "lullaby": cue_lullaby,
    "morning": cue_morning,
    "finale": lambda d: cue_theme(d, 108, mel_gain=0.5, bright=2),
    "end": cue_end,
}
CUE_GAIN = {"title": 1.0, "theme": 0.9, "playful": 0.85, "think": 0.95, "lullaby": 1.1, "morning": 0.9, "finale": 1.0, "end": 1.0}

music_plan = [
    ("title", 0.0), ("theme", SCN["hello"]["start"]), ("playful", SCN["roll"]["start"]), ("theme", SCN["ooch"]["start"]),
    ("think", SCN["brother"]["start"]), ("lullaby", SCN["night1"]["start"]), ("morning", M("night1.morning") + 0.6),
    ("theme", SCN["blue"]["start"]), ("lullaby", SCN["night2"]["start"]), ("morning", M("night2.morning") + 0.4),
    ("finale", SCN["tuesday"]["start"]), ("end", SCN["end"]["start"]),
]

# ------------------------------------------------------------------ sfx ---
def env_t(n): return np.arange(n) / SR

def sfx_pop(pitch=1.0, vel=1.0):
    t = env_t(int(0.12 * SR)); f = 900 * pitch * np.exp(-t / 0.05) + 300 * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04) * 0.35 * vel

def sfx_bloop(pitch=1.0, vel=1.0):
    t = env_t(int(0.18 * SR)); f = (350 + 500 * (t / 0.18)) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.18) * 0.3 * vel

def sfx_boing(vel=1.0, up=True):
    t = env_t(int(0.5 * SR))
    base = 220 + (300 * (t / 0.5) if up else -120 * (t / 0.5))
    f = base * (1 + 0.25 * np.sin(2 * np.pi * 14 * t) * np.exp(-t / 0.25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22) * 0.32 * vel

def sfx_slide(up=True, dur=0.6, vel=1.0):
    t = env_t(int(dur * SR)); p = t / dur
    f = 500 * 2 ** ((p if up else 1 - p) * 1.6) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return y * np.sin(np.pi * p) ** 0.5 * 0.16 * vel

def sfx_whoosh(dur=0.7, vel=1.0, lo=400, hi=3000):
    n = int(dur * SR); x = rs.randn(n); t = env_t(n); p = t / dur
    out = np.zeros(n); seg = 2048
    for i in range(0, n, seg):
        fc = lo + (hi - lo) * np.sin(np.pi * min(1, i / n))
        sos = butter(2, [fc * 0.6, fc * 1.4], "bp", fs=SR, output="sos")
        out[i:i + seg] = sosfilt(sos, x[i:i + seg])
    return out * np.sin(np.pi * p) ** 1.5 * 0.5 * vel

def sfx_roll(dur=1.5, vel=1.0):
    n = int(dur * SR); x = rs.randn(n)
    sos = butter(2, [80, 400], "bp", fs=SR, output="sos")
    y = sosfilt(sos, x); t = env_t(n)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)
    fade = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.3)
    return y * am * fade * 0.5 * vel

def sfx_tok(vel=1.0, pitch=1.0):
    t = env_t(int(0.15 * SR))
    y = np.sin(2 * np.pi * 1100 * pitch * t) * np.exp(-t / 0.018) + 0.5 * np.sin(2 * np.pi * 2300 * pitch * t) * np.exp(-t / 0.01)
    return (y + noise_burst(0.15, 3000, 0.006, 1.5)[:len(t)]) * 0.35 * vel

def sfx_ding(m=96, vel=1.0):
    return note("glock", m, 0.6, 1.0) * 1.3 * vel

def sfx_sparkle(vel=1.0, base=96):
    tr = Track(1.5)
    for i, m in enumerate([base, base + 4, base + 7, base + 12, base + 16]):
        tr.add(note("glock", m, 0.25, 0.55), i * 0.055)
    return tr.buf[:int(1.6 * SR)] * vel

def sfx_tada(vel=1.0):
    tr = Track(2)
    for i, m in enumerate([72, 76, 79, 84]): tr.add(note("glock", m, 0.5, 0.6), i * 0.07)
    for m in [60, 64, 67, 72]: tr.add(note("pluck", m, 0.8, 0.8), 0.3)
    return tr.buf[:int(2 * SR)] * vel

def sfx_nibble(vel=1.0):
    y = noise_burst(0.07, 2500, 0.012, 2.0)
    t = env_t(len(y))
    return (y + 0.4 * np.sin(2 * np.pi * 700 * t) * np.exp(-t / 0.01)) * 0.8 * vel

def sfx_chirp(vel=1.0):
    tr = Track(1)
    for i in range(3):
        t = env_t(int(0.09 * SR)); f = 3200 + 1800 * np.sin(np.pi * t / 0.09)
        tr.add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.09) * 0.1, i * 0.12)
    return tr.buf[:int(0.6 * SR)] * vel

def sfx_sizzle(dur, vel=1.0):
    n = int(dur * SR); y = sosfilt(butter(2, 5000, "hp", fs=SR, output="sos"), rs.randn(n)); t = env_t(n)
    return y * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)) * np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.4) * 0.05 * vel

def sfx_gliss(up=True, vel=1.0):
    tr = Track(2); notes = [65, 69, 72, 77, 81, 84, 89, 93]
    if not up: notes = notes[::-1]
    for i, m in enumerate(notes): tr.add(note("harp", m, 0.4, 0.5), i * 0.06)
    return tr.buf[:int(2 * SR)] * vel

def sfx_thud(vel=1.0):
    t = env_t(int(0.2 * SR)); f = 140 * np.exp(-t / 0.05) + 60
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.06) * 0.45 * vel

def sfx_wah(vel=1.0):
    tr = Track(2)
    for i, (m, d) in enumerate([(55, 0.25), (54, 0.25), (53, 0.6)]):
        t = env_t(int(d * SR)); f = midi_hz(m) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = sum(np.sin(k * ph) / k for k in range(1, 7)) * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.08)
        tr.add(y * 0.12, i * 0.27)
    return tr.buf[:int(1.4 * SR)] * vel

def sfx_flip(vel=1.0):
    return sfx_whoosh(0.18, 0.5 * vel, 1500, 5000)

sfx = []  # (time, array, gain, pan)
def S(t, y, g=1.0, pan=0.0): sfx.append((t, y, g, pan))

# title
S(0.15, sfx_pop(1.2)); [S(t0 + 0.29, sfx_thud(), 0.8) for t0 in (0.7, 1.15, 1.6)]
S(2.1, sfx_boing(), 0.8, 0.4); S(2.9, sfx_tok(0.6, 0.8), 0.6, 0.4); S(5.6, sfx_sparkle(0.6, 100), 0.7, -0.3)
# hello
S(M("hello.ballIn"), sfx_roll(1.9), 0.9, 0.3); S(LS("N_play1") + 1.6, sfx_pop(1.4), 0.6)
S(M("hello.shine") + 0.1, sfx_sparkle(0.7), 0.7, 0.3); S(M("hello.spin"), sfx_roll(2.0, 0.6), 0.6, 0.3)
S(LS("BB_whee") - 0.12, sfx_boing(), 0.8, 0.3)
# roll
z1, z2, z3 = LS("N_fast") + 0.45, M("roll.fast") + 0.15, LE("BB_zoom") + 0.35
S(z1, sfx_whoosh(0.75), 1.0, 0.0); S(z2, sfx_whoosh(0.75), 1.0, 0.0); S(z3, sfx_whoosh(0.65), 1.0, 0.0)
S(LS("N_slow") + 0.1, sfx_roll(LE("BB_slow") + 0.4 - LS("N_slow") - 0.1, 0.5), 0.6)
S(M("roll.visit") + 0.6, sfx_roll(1.8, 0.6), 0.6); S(M("roll.visit") + 2.3, sfx_pop(1.3), 0.7)
# ooch
p = M("ooch.push"); tap = M("ooch.tap")
S(p + 1.55, sfx_tok(0.7), 0.8, 0.2); S(p + 1.6, sfx_roll(1.0, 0.5), 0.5, 0.3); S(p + 2.7, sfx_roll(1.1, 0.5), 0.5, 0.3)
S(tap, sfx_tok(1.0), 1.0, 0.1); S(tap + 0.02, sfx_pop(0.8), 0.5); S(LE("ACE_ooch") + 0.05, sfx_boing(1.0, up=False), 0.8)
S(M("ooch.sore"), sfx_whoosh(0.35, 0.6, 600, 2500), 0.6)
# brother
fl, fe = M("brother.flash"), M("brother.flashEnd")
S(fl, sfx_gliss(True), 0.8); S(fe, sfx_gliss(False), 0.7)
S(fl + 0.6, sfx_slide(True, 0.7), 0.7, 0.3)
tt = fl + 1.2
while tt < fe - 0.2:
    S(tt, sfx_nibble(), 0.55 if LS("BABY_nom") - 0.05 < tt < LE("BABY_nom") else 0.9, 0.3); tt += 2 * np.pi / 22
S(fe - 0.4, sfx_slide(False, 0.5), 0.5, 0.3)
hmm = M("brother.hmm")
for i in range(3): S(hmm + 0.3 + i * 0.18, sfx_bloop(1 + i * 0.2), 0.6, 0.2)
S(hmm + 0.8, sfx_pop(1.0), 0.6)
S(LE("N_idea") - 1.6, sfx_bloop(0.7), 0.5)
for i in range(3): S(LS("N_thought") + i * 0.4, sfx_bloop(1.3 + 0.15 * i), 0.55)
S(M("brother.bulb"), sfx_ding(98), 1.0); S(M("brother.bulb") + 0.05, sfx_sparkle(0.5, 103), 0.6)
S(LS("BB_gloves") + 0.5, sfx_sparkle(0.6), 0.6)
# night 1
b0 = M("night1.baby"); huh = LS("BABY_huh")
S(b0, sfx_slide(True, 0.7), 0.6, 0.4); S(b0 + 0.95, sfx_nibble(0.6), 0.5, 0.4); S(b0 + 1.65, sfx_nibble(0.6), 0.5, 0.4)
S(huh + 1.3, sfx_slide(False, 0.6), 0.6, 0.4)
mo = M("night1.morning")
for d in (1.0, 1.7, 2.6, 3.4): S(mo + d, sfx_chirp(), 0.9, -0.5 + 0.3 * d % 1)
S(M("night1.glovesOff") - 0.9, sfx_whoosh(0.6, 0.5, 800, 3000), 0.6, 0.3)
S(LS("N_fine") + 0.1, sfx_sparkle(0.6), 0.6, 0.3); S(LS("N_fine") + 0.8, sfx_ding(91), 0.7, 0.4)
S(M("night1.hot"), sfx_sizzle(M("night1.another") - M("night1.hot")), 1.0)
an = M("night1.another")
for i in range(3): S(an + 0.3 + i * 0.18, sfx_bloop(1 + i * 0.2), 0.6, 0.2)
S(an + 0.8, sfx_pop(1.0), 0.5); S(an + 0.9, sfx_ding(98), 1.0)
# blue
S(M("blue.blueSay"), sfx_sparkle(0.8, 93), 0.8, -0.2); S(M("blue.bottle") + 0.3, sfx_pop(1.1), 0.8, 0.3)
S(M("blue.taste") + 1.5, sfx_bloop(1.0), 0.5, 0.3)
p0 = M("blue.paint") + 0.6
for i, m in enumerate([96, 98, 100, 103, 108]):
    S(p0 + i * 0.8 + 0.1, sfx_boing(0.35), 0.5, 0.2)
    S(p0 + i * 0.8 + 0.4, sfx_whoosh(0.3, 0.35, 2000, 6000), 0.6, 0.1)
    S(p0 + i * 0.8 + 0.72, sfx_ding(m), 0.8, -0.2 + i * 0.1)
S(LS("BB_done") - 0.05, sfx_tada(0.7), 0.7)
S(M("blue.pretty"), sfx_sparkle(0.7, 98), 0.7)
# night 2
b0 = M("night2.baby"); bl = M("night2.bleh")
S(b0, sfx_slide(True, 0.7), 0.6, 0.4)
tt = b0 + 0.95
while tt < bl - 0.1: S(tt, sfx_nibble(), 0.8, 0.4); tt += 0.7
S(bl + 0.75, sfx_wah(), 0.9); S(bl + 1.3, sfx_slide(False, 0.5), 0.6, 0.4)
mo = M("night2.morning")
for d in (0.8, 1.5, 2.3): S(mo + d, sfx_chirp(), 0.9, 0.4)
S(M("night2.check") + 0.9, sfx_ding(96), 0.9); S(M("night2.check") + 0.95, sfx_sparkle(0.6), 0.6)
S(LE("ACE_yay") + 0.05, sfx_tada(0.7), 0.7)
g0 = M("night2.grow")
for i in range(9): S(g0 + 0.4 + i * 0.45, sfx_flip(0.7), 0.6, 0.4)
S(LS("N_grew") + 2.5, sfx_sparkle(0.4), 0.5)
tp = M("night2.tap")
S(tp + 0.9, sfx_tok(0.9), 0.9, 0.1); S(tp + 0.95, sfx_sparkle(0.5, 100), 0.6)
S(LS("BB_hooray") - 0.12, sfx_boing(), 0.8, 0.3)
# tuesday
c0 = M("tuesday.cal")
S(c0 + 0.33, sfx_thud(), 1.0); S(c0 + 1.0, sfx_pop(1.0), 0.7)
for key, extra in (("tuesday.c1", 0.55), ("tuesday.c2", 0.55), ("tuesday.c3", 0.75)):
    for i, m in enumerate([96, 98, 100, 103, 108]):
        S(M(key) + extra + i * 0.22 + 0.2, sfx_ding(m), 0.55, -0.3 + i * 0.15)
    S(M(key) + extra - 0.25, sfx_flip(), 0.6)
th = M("tuesday.thanks")
for i in range(6): S(th + 0.8 + i * 0.7, sfx_pop(1.5 + 0.1 * (i % 3), 0.5), 0.35, -0.4 + i * 0.15)
# end
es, ee = SCN["end"]["start"], SCN["end"]["end"]
S(es + 0.1, sfx_whoosh(1.4, 0.7, 200, 1200), 0.8)
ns = LS("N_end") - 0.35
S(ns + 0.29, sfx_thud(), 1.0); S(ns + 0.6, sfx_boing(0.8), 0.7); S(es + 2.4, sfx_pop(1.2), 0.6)
S(ee - 2.1, sfx_whoosh(1.4, 0.7, 200, 1200), 0.8)

# ------------------------------------------------------------- render ----
def reverb_ir(rt=1.4, length=2.0, seed=0):
    r = np.random.RandomState(seed); n = int(length * SR); t = np.arange(n) / SR
    ir = r.randn(n) * np.exp(-6.9 * t / rt)
    sos = butter(1, 5000, "lp", fs=SR, output="sos")
    ir = sosfilt(sos, ir); ir[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    return ir / np.sqrt(np.sum(ir ** 2))

def stereo_reverb(x, rt, wet):
    l = fftconvolve(x, reverb_ir(rt, rt * 1.4, 1))[:len(x)]
    r = fftconvolve(x, reverb_ir(rt, rt * 1.4, 2))[:len(x)]
    return np.stack([x + wet * l, x + wet * r], axis=1)

def pan2(y, pan):
    a = (pan + 1) * np.pi / 4
    return np.stack([y * np.cos(a), y * np.sin(a)], axis=1) * np.sqrt(2)

# music
music = np.zeros(N)
XF = 1.0
for idx, (cue, t0) in enumerate(music_plan):
    t1 = music_plan[idx + 1][1] if idx + 1 < len(music_plan) else DUR + 0.5
    d = t1 - t0 + XF
    y = CUES[cue](d + 0.5)[:int(d * SR)] * CUE_GAIN[cue]
    n = len(y); tt = np.arange(n) / SR
    fin = np.minimum(1, tt / (0.05 if idx == 0 else XF * 0.6))
    fout = np.clip((d - tt) / XF, 0, 1) if idx + 1 < len(music_plan) else np.clip((d - 0.5 - tt) / 1.5 + 1, 0, 1)
    y = y * fin * fout
    i0 = int(t0 * SR); j = min(N, i0 + n)
    music[i0:j] += y[:j - i0]
music_st = stereo_reverb(music, 1.3, 0.35)

# voices
voice = np.zeros(N)
for l in TL["lines"]:
    y, sr = sf.read(os.path.join(HERE, "voices", l["id"] + ".wav"))
    rms = np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) if np.any(np.abs(y) > 0.02) else 0.1
    g = 0.105 / rms
    g *= {"N": 1.0, "ACE": 1.05, "BB": 1.0, "BABY": 1.0}[l["who"]]
    y = y * g
    pk = np.max(np.abs(y))
    if pk > 0.9: y *= 0.9 / pk
    i0 = int(l["start"] * SR); j = min(N, i0 + len(y))
    voice[i0:j] += y[:j - i0]
voice_st = stereo_reverb(voice, 0.45, 0.06)

# ducking: music gets quieter under speech
pres = np.zeros(N)
for l in TL["lines"]:
    a, b = int((l["start"] - 0.15) * SR), int((l["end"] + 0.25) * SR)
    pres[max(0, a):min(N, b)] = 1
win = int(0.25 * SR)
kern = np.ones(win) / win
pres = np.convolve(pres, kern, mode="same")
duck = 1.0 - 0.6 * pres  # -8 dB under voice
# extra music dips for story moments
def dip(t0, t1, g, ramp=0.25):
    tt = np.arange(N) / SR
    w = np.clip(np.minimum((tt - t0) / ramp, (t1 - tt) / ramp), 0, 1)
    return 1 - (1 - g) * w
duck *= dip(M("ooch.tap") - 0.05, M("ooch.why") + 0.2, 0.35)
duck *= dip(M("night1.hot"), M("night1.another") - 0.2, 0.6)
duck *= dip(SCN["end"]["start"] - 0.05, SCN["end"]["start"] + 1.0, 1.0)
music_st *= duck[:, None] * 0.55

sfx_st = np.zeros((N, 2))
for (t0, y, g, pan) in sfx:
    i0 = int(t0 * SR); j = min(N, i0 + len(y))
    if j <= i0: continue
    sfx_st[i0:j] += pan2(y[:j - i0] * g, pan)
sfx_st = sfx_st * 0.8
sfx_st = stereo_reverb(sfx_st.mean(axis=1), 0.6, 0.0) * 0 + sfx_st  # keep dry

mix = voice_st + music_st + sfx_st
# gentle fade at very end
tt = np.arange(N) / SR
mix *= np.clip((DUR - tt) / 0.8, 0, 1)[:, None] ** 0.5
pk = np.max(np.abs(mix))
print("peak before norm", pk)
mix = mix / pk * 0.89
sf.write(os.path.join(HERE, "mix.wav"), mix.astype(np.float32), SR)
sf.write(os.path.join(HERE, "music_only.wav"), (music_st / (np.max(np.abs(music_st)) + 1e-9) * 0.8).astype(np.float32), SR)
print("wrote mix.wav", mix.shape[0] / SR, "s")
