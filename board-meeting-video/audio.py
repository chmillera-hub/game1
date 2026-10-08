"""Original score, sound effects and dialogue mix, all synthesized here.

Writes build/mix.wav (stereo 44.1 kHz, loudness-normalized).
"""
import json, math, os, random, subprocess, sys
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

sys.path.insert(0, os.path.dirname(__file__))
from common import Timeline, BUILD
from boardroom import Board
from opening import Opening
from epilogue import Epilogue

SR = 44100
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = max(1, min(A, n))
    e[:A] = np.linspace(0, 1, A)
    D = min(D, n - A)
    if D > 0:
        e[A:A + D] = np.linspace(1, s, D)
    if R > 0 and R < n:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments

def epiano(f, dur, vel=0.5):
    t = tvec(dur + 0.6)
    out = np.zeros_like(t)
    for k, (amp, dec) in enumerate(((1.0, 1.6), (0.32, 0.9), (0.1, 0.5), (0.05, 0.3))):
        out += amp * np.sin(2 * np.pi * f * (k + 1) * t) * np.exp(-t / dec)
    out += 0.06 * np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.05)
    out *= 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    env = np.ones_like(t)
    rel = int(0.5 * SR)
    env[int(dur * SR):] = np.linspace(1, 0, len(t) - int(dur * SR))
    return out * env * vel * 0.25


def piano(f, dur, vel=0.5):
    t = tvec(dur + 1.2)
    out = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 9000:
            break
        out += (1 / k ** 1.4) * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.6 + 0.5 * k) * (f / 400) ** 0.3)
    att = np.minimum(1, t / 0.004)
    env = np.ones_like(t)
    env[int(dur * SR):] = np.exp(-np.arange(len(t) - int(dur * SR)) / SR / 0.25)
    return out * att * env * vel * 0.22


def marimba(f, vel=0.5):
    t = tvec(1.2)
    out = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) + 0.3 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.08)
           + 0.08 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.03))
    return out * np.minimum(1, t / 0.002) * vel * 0.3


def glock(f, vel=0.5, dec=1.2):
    t = tvec(dec * 2.5)
    out = (np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / (dec * 0.4))
           + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / (dec * 0.2)))
    return out * np.minimum(1, t / 0.002) * vel * 0.2


def additive(f, dur, spectrum, vib=0.0, att=0.6, rel=1.2, detune=(-5, 0, 5)):
    t = tvec(dur + rel)
    out = np.zeros_like(t)
    vibm = 1 + vib * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6))
    for cents in detune:
        f0 = f * 2 ** (cents / 1200)
        ph = 2 * np.pi * f0 * np.cumsum(vibm) / SR
        k = 1
        while f0 * k < 7000 and k < 40:
            a = spectrum(f0 * k, k)
            if a > 1e-3:
                out += a * np.sin(k * ph + rng.uniform(0, 6))
            k += 1
    n_on = int(dur * SR)
    env = np.ones_like(t)
    A = int(att * SR)
    env[:A] = np.linspace(0, 1, A) ** 1.5
    env[n_on:] = np.linspace(1, 0, len(t) - n_on) ** 2
    return out * env / len(detune)


def pad(f, dur, vel=0.3, att=1.0, rel=1.6):
    return additive(f, dur, lambda fk, k: 1 / k * math.exp(-fk / 1800), 0.002, att, rel) * vel


def strings(f, dur, vel=0.3, att=0.9, rel=1.8):
    return additive(f, dur, lambda fk, k: 1 / k ** 0.9 * math.exp(-fk / 2600), 0.006, att, rel) * vel


def choir(f, dur, vel=0.3, att=1.2, rel=2.0):
    formants = ((750, 90), (1150, 110), (2600, 160))

    def sp(fk, k):
        g = sum(math.exp(-((fk - F) / bw) ** 2) * w for (F, bw), w in zip(formants, (1.0, 0.6, 0.25)))
        return (0.15 + g) / k ** 0.5
    return additive(f, dur, sp, 0.008, att, rel, detune=(-9, -3, 3, 9)) * vel


def bass(f, dur, vel=0.5):
    t = tvec(dur + 0.1)
    out = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return out * adsr(len(t), 0.005, 0.2, 0.6, 0.08) * vel * 0.35


def kick(vel=0.6):
    t = tvec(0.4)
    f = 45 + 90 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) * vel


def snare(vel=0.3, dur=0.2, lo=900, hi=6000):
    t = tvec(dur)
    n = bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t / (dur * 0.3))
    return n * vel


def hat(vel=0.15):
    t = tvec(0.06)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / 0.015) * vel


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def reverb_ir(sec=2.0, damp=3000, seed=1):
    r = np.random.default_rng(seed)
    t = tvec(sec)
    ir = r.standard_normal(len(t)) * np.exp(-t / (sec / 6.5))
    ir = lp(ir, damp)
    ir[0] = 0
    return ir / np.sqrt((ir ** 2).sum())


IR_L, IR_R = reverb_ir(2.4, 3500, 1), reverb_ir(2.4, 3500, 2)
ROOM_L, ROOM_R = reverb_ir(0.7, 4500, 3), reverb_ir(0.7, 4500, 4)


def verb(x, wet=0.25, room=False):
    L, R = (ROOM_L, ROOM_R) if room else (IR_L, IR_R)
    yl = fftconvolve(x, L)[: len(x)]
    yr = fftconvolve(x, R)[: len(x)]
    return np.stack([x + wet * yl, x + wet * yr])


# ---------------------------------------------------------------- track helper

class Track:
    def __init__(self, total):
        self.n = int((total + 2) * SR)
        self.buf = np.zeros((2, self.n))

    def add(self, t, x, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= self.n or i < -len(x if x.ndim == 1 else x[0]):
            return
        if x.ndim == 1:
            l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
            x = np.stack([x * l * 1.414, x * r * 1.414])
        if i < 0:
            x = x[:, -i:]
            i = 0
        m = min(x.shape[1], self.n - i)
        self.buf[:, i:i + m] += x[:, :m] * gain


def gate(track, segments, total, fade=0.15):
    """Multiply a track by 1 inside segments, 0 outside (with fades)."""
    g = np.zeros(track.n)
    for a, b in segments:
        ia, ib = int(a * SR), int(b * SR)
        g[ia:ib] = 1
    k = int(fade * SR)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    track.buf *= g


# ---------------------------------------------------------------- music cues

def chord_notes(root, kind):
    iv = {"maj": (0, 4, 7), "min": (0, 3, 7), "maj7": (0, 4, 7, 11), "min7": (0, 3, 7, 10),
          "dom7": (0, 4, 7, 10), "sus4": (0, 5, 7), "add9": (0, 4, 7, 14), "6": (0, 4, 7, 9)}[kind]
    return [root + i for i in iv]


def cue_lofi(tr, t0, t1, op, tl):
    beat = 60 / 76
    prog = [(57, "min7"), (53, "maj7"), (48, "maj7"), (55, "6")]
    t = t0
    bar = 0
    drums_on = tl.s("n3") - 0.4
    tense = op.wheel_start
    calm = tl.s("n9")
    while t < t1:
        root, kind = prog[bar % 4]
        notes = chord_notes(root, kind)
        lvl = 0.55 if t < tense or t > calm else 0.5
        for j, m in enumerate(notes):
            x = epiano(mtof(m + (12 if m < 52 else 0)), beat * 3.6, lvl * (0.8 + 0.2 * random.random()))
            tr.add(t + j * 0.025 + (0.02 if bar % 2 else 0), x, 1.0, pan=-0.2 + 0.13 * j)
        if t < tense or t > calm:
            # sparse melody
            for k, (off, m) in enumerate(((1.5, notes[-1] + 12), (2.5, notes[1] + 12))):
                if bar % 2 == k % 2:
                    tr.add(t + off * beat, epiano(mtof(m), beat * 0.9, 0.35), 1.0, 0.25)
        tr.add(t, bass(mtof(root - 24), beat * 1.8, 0.5 if t > drums_on else 0.25))
        if drums_on < t < calm:
            for b in range(4):
                tb = t + b * beat
                if b in (0, 2) or (b == 3 and bar % 2):
                    tr.add(tb + (beat * 0.5 if b == 3 else 0), kick(0.5))
                if b in (1, 3):
                    tr.add(tb, snare(0.12, 0.15, 1500, 5000))
                for h in range(2 if t < tense else 4):
                    tr.add(tb + h * beat / (2 if t < tense else 4) + 0.03 * (h % 2), hat(0.06 if h % 2 else 0.09), pan=0.3)
        if tense < t < calm:
            for e in range(8):
                tr.add(t + e * beat / 2, bass(mtof(root - 12), beat * 0.4, 0.35), pan=-0.1)
            tr.add(t, pad(mtof(root + 12), beat * 4, 0.12, 0.3, 0.6), pan=0.2)
        t += beat * 4
        bar += 1
    # vinyl crackle
    n = noise(t1 - t0)
    crack = (rng.random(len(n)) < 0.0006) * rng.uniform(-1, 1, len(n))
    tr.add(t0, lp(n, 1200) * 0.01 + crack * 0.08, 1.0)


def cue_stab(tr, t):
    for m in (33, 45, 52, 57, 60, 64):
        tr.add(t, strings(mtof(m), 0.6, 0.35, 0.01, 1.4))
    tr.add(t, kick(0.9))


def cue_title(tr, t):
    for j, m in enumerate((72, 76, 79, 84)):
        tr.add(t + 0.35 + j * 0.12, glock(mtof(m), 0.6), pan=-0.3 + 0.2 * j)
    for m in (48, 55, 60, 64, 67):
        tr.add(t + 0.35, strings(mtof(m), 2.6, 0.22, 0.15, 1.2))
    tr.add(t + 0.35, kick(0.6))
    tr.add(t + 1.6, glock(mtof(91), 0.4, 2.0))


def cue_muzak(tr, t0, t1):
    beat = 60 / 112
    prog = [(48, "maj"), (45, "min"), (41, "maj"), (43, "maj")]
    pat = [0, 2, 1, 2, 0, 2, 1, 2]
    t = t0
    bar = 0
    mel = [76, 74, 72, 74, 76, 76, 76, None, 74, 74, 74, None, 76, 79, 79, None]
    while t < t1:
        root, kind = prog[bar % 4]
        notes = chord_notes(root + 12, kind)
        for e in range(8):
            m = notes[pat[e]] + (12 if e in (3, 7) else 0)
            tr.add(t + e * beat / 2, marimba(mtof(m), 0.45 if e % 2 == 0 else 0.3), pan=-0.25)
        tr.add(t, bass(mtof(root - 12), beat * 1.5, 0.45))
        tr.add(t + 2 * beat, bass(mtof(root - 12 + 7), beat * 1.5, 0.35))
        for b in range(4):
            tr.add(t + b * beat, snare(0.025, 0.08, 4000, 9000), pan=0.4)
            tr.add(t + b * beat + beat / 2, snare(0.018, 0.06, 5000, 10000), pan=0.4)
        if bar % 8 >= 4:
            for k in range(4):
                m = mel[(bar % 4) * 4 + k]
                if m:
                    tr.add(t + k * beat, glock(mtof(m), 0.35), pan=0.3)
        t += beat * 4
        bar += 1


def cue_drone(tr, t0, t1):
    for m in (38, 45, 50):
        tr.add(t0, strings(mtof(m), t1 - t0, 0.18, 0.4, 1.0))


def cue_exit(tr, t0, t1):
    for m in (50, 57, 62, 66, 69):
        tr.add(t0, choir(mtof(m), t1 - t0, 0.16, 1.0, 2.0))
    for j, m in enumerate((74, 78, 81, 86)):
        tr.add(t0 + 0.6 + j * 0.45, piano(mtof(m), 1.0, 0.3), pan=0.2)


def cue_finale(tr, ep, tl, t0, t_end):
    bpm = 66
    beat = 60 / bpm
    prog = [(50, "maj", 50), (45, "maj", 49), (47, "min", 47), (43, "maj", 43),
            (50, "maj", 42), (52, "min7", 40), (45, "sus4", 45), (50, "add9", 38)]
    t = t0
    bar = 0
    while t < t_end - 2:
        root, kind, bassn = prog[bar % len(prog)]
        notes = chord_notes(root + 12, kind)
        # piano arpeggio
        arp = notes + [notes[1] + 12, notes[2] + 12]
        intensity = clamp01((t - ep.tl0) / 4) if t < ep.wheel0 else 0.35
        for e in range(8):
            m = arp[[0, 1, 2, 3, 2, 1, 3, 4][e] % len(arp)]
            tr.add(t + e * beat / 2, piano(mtof(m), beat * 0.9, 0.32 + 0.1 * intensity), pan=0.15)
        tr.add(t, piano(mtof(bassn - 12), beat * 3.5, 0.45))
        if t >= ep.tl0 - 0.5:
            for m in notes:
                tr.add(t, strings(mtof(m), beat * 4, 0.10 + 0.12 * intensity, 0.8, 1.6), pan=-0.2)
            tr.add(t, strings(mtof(bassn - 12), beat * 4, 0.12 + 0.1 * intensity, 0.8, 1.6))
        if ep.tl0 + 2.5 <= t < ep.wheel0:
            for m in notes[:3]:
                tr.add(t, choir(mtof(m + 12), beat * 4, 0.12 * intensity, 1.0, 1.8), pan=0.2)
        if ep.tl0 + 3.5 <= t < ep.wheel0 + 1 or t >= ep.dawn0:
            tr.add(t + beat * 2, glock(mtof(notes[-1] + 24), 0.25, 1.8), pan=0.35)
        t += beat * 4
        bar += 1
    # final chord over the end card
    tf = ep.end0 + 0.4
    for m in (50, 57, 62, 66, 69, 76):
        tr.add(tf, strings(mtof(m), t_end - tf - 1.5, 0.16, 1.0, 2.0))
    for j, m in enumerate((74, 78, 81, 86)):
        tr.add(tf + j * 0.3, glock(mtof(m), 0.35, 2.2), pan=-0.3 + j * 0.2)


def clamp01(x):
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------- sfx

def sfx_pop():
    t = tvec(0.12)
    f = 500 + 900 * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.04) * 0.4


def sfx_ding(f=1320):
    return glock(f, 0.9, 0.6)


def sfx_whoosh(dur=0.7, up=True):
    n = noise(dur)
    t = tvec(dur)
    env = np.sin(np.pi * t / dur) ** 2
    out = np.zeros_like(n)
    seg = int(0.02 * SR)
    for i in range(0, len(n), seg):
        u = i / len(n)
        fc = 300 + 3000 * (u if up else 1 - u)
        out[i:i + seg] = bp(n[max(0, i - 2000):i + seg], fc * 0.6, fc * 1.4)[-len(n[i:i + seg]):]
    return out * env * 0.5


def sfx_kaching():
    out = np.zeros(int(1.6 * SR))
    for k, f in enumerate((2093, 2637, 3136)):
        g = glock(f, 0.8, 0.7)
        out[int(0.09 * k * SR):int(0.09 * k * SR) + len(g)] += g[: len(out) - int(0.09 * k * SR)]
    out[: int(0.05 * SR)] += snare(0.4, 0.05, 2000, 8000)
    return out * 1.6


def sfx_coin():
    f = rng.uniform(2500, 4200)
    return glock(f, 0.35, 0.15)


def sfx_scratch():
    t = tvec(0.45)
    f = 200 + 1600 * np.abs(np.sin(2 * np.pi * 2.2 * t)) * np.exp(-t / 0.3)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bp(noise(0.45), 800, 4000) * 0.4
    return s * np.exp(-t / 0.25)


def sfx_tick():
    t = tvec(0.04)
    return hp(noise(0.04), 2500) * np.exp(-t / 0.004) * 0.5 + np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.006) * 0.3


def sfx_cricket():
    t = tvec(0.35)
    car = np.sin(2 * np.pi * 4300 * t)
    am = (np.sin(2 * np.pi * 30 * t) > 0.2).astype(float)
    return car * am * np.sin(np.pi * t / 0.35) * 0.05


def sfx_thump(f=70, dur=0.35, vel=0.9):
    t = tvec(dur)
    fr = f + 60 * np.exp(-t / 0.03)
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / (dur * 0.35)) + lp(noise(dur), 900) * np.exp(-t / 0.03) * 0.5) * vel


def sfx_spit():
    t = tvec(0.6)
    n = bp(noise(0.6), 800, 5000) * np.exp(-t / 0.15)
    n[: int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))
    return n * 0.7


def sfx_step():
    t = tvec(0.12)
    return lp(noise(0.12), 600) * np.exp(-t / 0.03) * 0.35


def sfx_creak():
    t = tvec(0.7)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.15
    return bp(s, 300, 2500) * np.sin(np.pi * t / 0.7) * 0.5


def sfx_click():
    t = tvec(0.03)
    return hp(noise(0.03), 1500) * np.exp(-t / 0.003) * 0.5


def sfx_shimmer(dur=2.0):
    out = np.zeros(int((dur + 1.5) * SR))
    r = random.Random(3)
    for k in range(18):
        f = mtof(r.choice([74, 78, 81, 86, 90, 93]))
        g = glock(f, 0.18, 0.5)
        i = int(k / 18 * dur * SR)
        out[i:i + len(g)] += g[: len(out) - i]
    return out


def sfx_chirp():
    t = tvec(0.18)
    f = 3000 + 1500 * np.sin(np.pi * t / 0.18) + 400 * np.sin(2 * np.pi * 25 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.18) ** 2 * 0.12


def sfx_squeak():
    t = tvec(0.15)
    f = 1100 + 500 * t / 0.15
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.15) * 0.05


# ---------------------------------------------------------------- main

def main():
    tl = Timeline()
    board = Board(tl)
    op = Opening(tl)
    ep = Epilogue(tl, board, op)
    total = tl.total
    T, E, Wd = tl.s, tl.e, tl.wfind
    title0 = E("n11") + 0.3

    # ---- dialogue
    dia = Track(total)
    activity = np.zeros(dia.n)
    pans = {"PAM": -0.25, "CFO": -0.12, "CEO": 0.0, "TYLER": 0.12, "JESUS": 0.2}
    for L in tl.spoken:
        a = np.load(f"{BUILD}/voice/{L['id']}.npy").astype(np.float64)
        who = L["who"]
        if who.startswith("C"):
            a = bp(a, 280, 3800) * 1.3
            x = verb(a, 0.08, room=True)
            g = 0.75
        elif who == "NARR":
            x = verb(a, 0.05, room=True)
            g = 0.95
        elif who == "JESUS":
            a = a + 0.3 * lp(a, 300)
            x = verb(a, 0.16)
            g = 0.95
        else:
            x = verb(a, 0.14, room=True)
            g = 0.92 if who != "CEO" or L["id"] not in ("b18", "b26") else 1.05
        p = pans.get(who, 0.0)
        x = np.stack([x[0] * (1 - max(0, p)), x[1] * (1 + min(0, p))])
        dia.add(L["start"], x, g)
        i0 = int(L["start"] * SR)
        activity[i0:i0 + len(a)] = 1
    k = int(0.25 * SR)
    duck = np.convolve(activity, np.ones(k) / k, mode="same")

    # ---- music
    mus = Track(total)
    cue_lofi(mus, 0.3, title0 - 0.1, op, tl)
    lofi_end = title0 - 0.1
    gate(mus, [(0, lofi_end)], total, 0.05)
    m2 = Track(total)
    cue_stab(m2, op.bag_t - 0.02)
    cue_title(m2, title0)
    muz = Track(total)
    m_start = E("title") - 0.2
    cue_muzak(muz, m_start, T("b27"))
    gate(muz, [(m_start, E("b11") + 0.15), (T("b12") + 0.1, T("b20")), (E("b20") + 0.8, T("b22") - 0.2), (E("b24") + 0.3, T("b27") - 0.3)], total, 0.12)
    cue_drone(m2, T("b20"), E("b20") + 1.0)
    cue_exit(m2, T("b22") - 0.2, E("b22") + 0.8)
    cue_exit(m2, T("rise") + 0.4, board.j_walk[1] + 0.8)
    fin = Track(total)
    cue_finale(fin, ep, tl, board.lights_off + 0.6, total)
    music = mus.buf * 0.55 + m2.buf * 0.6 + muz.buf * 0.33 + fin.buf * 0.62
    music = music * (1 - 0.62 * duck[None, :])
    music_st = verb(music[0], 0.0)  # placeholder to keep shapes simple
    ml = fftconvolve(music[0], IR_L)[: music.shape[1]]
    mr = fftconvolve(music[1], IR_R)[: music.shape[1]]
    music = music + 0.22 * np.stack([ml, mr])

    # ---- sfx
    fx = Track(total)
    # night ambience
    for i in range(int(19 / 0.9)):
        fx.add(0.4 + i * 0.9 + random.Random(i).uniform(0, 0.3), sfx_cricket(), 0.6, pan=0.5)
    for c in ("c1", "c2", "c3", "c4"):
        fx.add(T(c) - 0.15, sfx_pop(), 0.8)
    fx.add(Wd("n2", "Twelve") - 0.1, sfx_ding(1760), 0.5)
    fx.add(Wd("n3", "Sure"), sfx_pop(), 0.3)
    # wheel squeaks
    t = op.wheel_start
    while t < op.reveal + 2:
        fx.add(t, sfx_squeak(), 1.0, pan=-0.2)
        sp = 1.4 + (1.6 * min(2.5, max(0, t - Wd("n5", "Round"))))
        t += 2 * math.pi / 8 / sp * 2.2
    fx.add(op.reveal - 0.1, sfx_whoosh(1.2, False), 0.7)
    fx.add(op.bag_t, sfx_kaching(), 0.9)
    r = random.Random(5)
    for i in range(60):
        tc = op.reveal + 0.5 + i * 0.2 + r.uniform(0, 0.1)
        if tc < op.bed_back:
            fx.add(tc, sfx_coin(), 0.35, pan=r.uniform(-0.5, 0.5))
    fx.add(T("n8") - 0.05, sfx_pop(), 0.6)
    fx.add(Wd("n8", "Old") - 0.05, sfx_pop(), 0.6)
    fx.add(Wd("n8", "Not") + 0.12, sfx_thump(90, 0.3, 0.7), 0.9)
    tt = op.count_t
    while tt < op.bed_back:
        fx.add(tt, sfx_tick(), 0.25)
        tt += 0.07
    for i in range(12):
        fx.add(T("n9") + i * 0.9, sfx_cricket(), 0.5, pan=0.5)
    fx.add(Wd("n9", "Jesus") - 0.2, sfx_pop(), 0.5)
    fx.add(Wd("n10", "bury") + 0.12, sfx_thump(80, 0.3, 0.8), 0.9)
    fx.add(title0 - 0.12, sfx_scratch(), 1.0)
    fx.add(title0 + 0.05, sfx_whoosh(0.6, True), 0.6)
    # boardroom
    hum = lp(noise(board.lights_off - E("title")), 250) * 0.012
    fx.add(E("title") - 0.3, hum, 1.0)
    for (ts, name) in board.slides[1:]:
        fx.add(ts, sfx_click(), 0.6, pan=-0.1)
    for (a, b) in ((T("silence1"), E("silence1")), (T("silence2"), E("silence2"))):
        s = math.ceil(a)
        while s < b:
            fx.add(s, sfx_tick(), 0.6, pan=0.4)
            s += 1
    fx.add(T("silence1") + 0.9, sfx_cricket(), 1.0, pan=0.3)
    fx.add(T("silence1") + 1.4, sfx_cricket(), 1.0, pan=0.3)
    fx.add(T("spit"), sfx_spit(), 1.0)
    fx.add(T("b27") - 0.08, sfx_thump(60, 0.45, 1.0), 1.0)
    fx.add(board.stamp_t - 0.02, sfx_thump(65, 0.45, 1.0), 1.0)
    for i in range(10):
        fx.add(board.pat[0] + i * (board.pat[1] - board.pat[0]) / 10, snare(0.08, 0.12, 300, 2500), 0.8, pan=0.3)
    fx.add(board.j_rise[0], sfx_creak(), 0.6, pan=0.3)
    st = board.j_step[0]
    while st < board.j_step[1]:
        fx.add(st, sfx_step(), 0.8, pan=0.3)
        st += 0.32
    fx.add(board.j_seed, sfx_click(), 0.5)
    st = board.j_walk[0]
    while st < board.j_walk[1]:
        fx.add(st, sfx_step(), 0.8, pan=0.5)
        st += 0.42
    fx.add(board.j_walk[0] + 0.9, sfx_creak(), 0.7, pan=0.6)
    fx.add(board.j_walk[0] + 2.1, sfx_thump(55, 0.4, 0.7), 0.8, pan=0.6)
    fx.add(board.lights_off, sfx_click(), 1.0)
    fx.add(board.lights_off + 0.02, sfx_thump(40, 0.2, 0.3), 0.6)
    # epilogue
    fx.add(ep.sprout0, sfx_shimmer(2.2), 0.7)
    fx.add(ep.tl0 - 0.2, sfx_whoosh(2.5, True), 0.5)
    r = random.Random(8)
    for b in ep.birds:
        for k in range(3):
            fx.add(b["arrive"] + k * r.uniform(0.6, 1.8), sfx_chirp(), 0.8, pan=r.uniform(-0.6, 0.6))
    for i in range(14):
        tc = ep.tl0 + 4 + i * 0.5 + r.uniform(0, 0.3)
        if tc < ep.wheel0 - 0.3:
            fx.add(tc, sfx_chirp(), 0.5, pan=r.uniform(-0.6, 0.6))
    fx.add(ep.dawn0 + 0.35, sfx_ding(1568), 0.5)
    fx.add(ep.dawn0 + 0.47, sfx_ding(2093), 0.4)
    fx.add(T("e4") + 0.1, sfx_shimmer(1.4), 0.5)
    for i in range(6):
        fx.add(ep.dawn0 + 0.8 + i * 0.9, sfx_chirp(), 0.25, pan=-0.6)

    mixb = dia.buf + music + fx.buf
    n = int(total * SR)
    mixb = mixb[:, :n]
    # fade out at the very end
    f = int(1.4 * SR)
    mixb[:, -f:] *= np.linspace(1, 0, f)
    mixb /= max(1e-6, np.abs(mixb).max()) / 0.9
    raw = f"{BUILD}/mix_raw.wav"
    import wave
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mixb.T * 32767).astype(np.int16).tobytes())
    # two-pass loudness normalization to -14 LUFS
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    js = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-af", af, "-ar", "44100",
                    f"{BUILD}/mix.wav"], check=True)
    print("wrote", f"{BUILD}/mix.wav", js["input_i"])


if __name__ == "__main__":
    main()
