"""Procedural score, sound effects and the final mix (numpy only)."""
import math
import numpy as np
import soundfile as sf
from common import SR

RNG = np.random.default_rng(7)
TAU = 2 * np.pi


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nm(s):
    """'C4', 'Eb3', 'F#2' -> midi"""
    base = NOTE[s[0]]
    i = 1
    while i < len(s) and s[i] in '#b':
        base += 1 if s[i] == '#' else -1
        i += 1
    return base + 12 * (int(s[i:]) + 1)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def lp1(x, fc):
    """one-pole lowpass via IIR in frequency domain approximation (fast)."""
    n = len(x)
    if n == 0:
        return x
    N = 1 << int(np.ceil(np.log2(n * 2)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR)
    H = 1.0 / (1.0 + 1j * f / fc)
    return np.fft.irfft(X * H, N)[:n]


def bandpass(x, lo, hi, order=2):
    n = len(x)
    N = 1 << int(np.ceil(np.log2(max(2, n) * 2)))
    X = np.fft.rfft(x, N)
    f = np.fft.rfftfreq(N, 1 / SR) + 1e-6
    H = (1 / np.sqrt(1 + (lo / f) ** (2 * order))) * (1 / np.sqrt(1 + (f / hi) ** (2 * order)))
    return np.fft.irfft(X * H, N)[:n]


def highpass(x, fc, order=2):
    return bandpass(x, fc, SR / 2.2, order)


def noise(dur):
    return RNG.standard_normal(int(dur * SR))


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * gain


def reverb_ir(rt=1.2, pre=0.02, bright=6000, seed=3):
    r = np.random.default_rng(seed)
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-6.9 * t / rt)
    ir = lp1(ir, bright)
    ir = np.concatenate([np.zeros(int(pre * SR)), ir])
    ir[int(pre * SR)] += 0.0
    return ir / np.sqrt(np.sum(ir ** 2))


def convolve(x, ir):
    n = len(x) + len(ir) - 1
    N = 1 << int(np.ceil(np.log2(n)))
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:n]
    return y


def add_reverb(x, mix=0.2, rt=1.2, bright=6000, pre=0.02):
    ir = reverb_ir(rt, pre, bright)
    wet = convolve(x, ir)
    out = np.zeros(len(wet))
    out[:len(x)] += x * (1 - mix * 0.5)
    out += wet * mix * 0.35
    return out


# ------------------------------------------------------------------ instruments
def epiano(m, dur, vel=0.6):
    f = mf(m)
    t = tvec(dur + 1.5)
    idx = 1.6 * vel * np.exp(-t * 3.0) + 0.25
    car = np.sin(TAU * f * t + idx * np.sin(TAU * f * t))
    tine = np.sin(TAU * f * 7.0 * t) * np.exp(-t * 28) * 0.18 * vel
    env = (1 - np.exp(-t * 500)) * np.exp(-t * (0.9 + f / 900))
    env *= np.where(t > dur, np.exp(-(t - dur) * 7), 1.0)
    trem = 1 + 0.12 * np.sin(TAU * 4.6 * t)
    return (car * 0.55 + tine) * env * vel * trem


def vibes(m, dur, vel=0.5):
    f = mf(m)
    t = tvec(dur + 2.0)
    s = np.sin(TAU * f * t) + 0.25 * np.sin(TAU * f * 4.0 * t) * np.exp(-t * 8)
    env = (1 - np.exp(-t * 800)) * np.exp(-t * 1.4)
    env *= np.where(t > dur + 0.3, np.exp(-(t - dur - 0.3) * 4), 1.0)
    trem = 1 + 0.25 * np.sin(TAU * 5.5 * t)
    return s * env * vel * trem * 0.6


def ubass(m, dur, vel=0.8):
    f = mf(m)
    t = tvec(dur + 0.4)
    s = (np.sin(TAU * f * t) + 0.45 * np.sin(TAU * 2 * f * t) * np.exp(-t * 5)
         + 0.18 * np.sin(TAU * 3 * f * t) * np.exp(-t * 9))
    env = (1 - np.exp(-t * 250)) * np.exp(-t * 2.4)
    env *= np.where(t > dur, np.exp(-(t - dur) * 25), 1.0)
    thump = lp1(RNG.standard_normal(len(t)), 900) * np.exp(-t * 60) * 0.25
    return (s * env + thump) * vel * 0.8


def saw_stack(m, dur, n_h=24, detune=(0.0, -0.08, 0.08), bright=2500, att=0.5, rel=1.0, vib=0.0):
    f = mf(m)
    t = tvec(dur + rel)
    out = np.zeros(len(t))
    for dt in detune:
        ff = f * 2 ** (dt / 12)
        ph0 = RNG.uniform(0, TAU)
        vb = 1 + vib * np.sin(TAU * 5.2 * t) * np.clip((t - 0.4) / 0.6, 0, 1)
        phase = TAU * ff * np.cumsum(vb) / SR + ph0
        for k in range(1, n_h + 1):
            if k * ff > 12000:
                break
            w = 1.0 / k / (1 + (k * ff / bright) ** 2)
            out += w * np.sin(k * phase)
    env = np.clip(t / att, 0, 1) ** 1.5
    env *= np.where(t > dur, np.exp(-(t - dur) * (5.0 / rel)), 1.0)
    return out * env / len(detune)


def strings(m, dur, vel=0.5, att=0.6, rel=1.2, bright=2200):
    return saw_stack(m, dur, 20, (0.0, -0.07, 0.07), bright, att, rel, vib=0.004) * vel


def brass(m, dur, vel=0.7, att=0.06, rel=0.4, swell=False):
    f = mf(m)
    t = tvec(dur + rel)
    phase = TAU * f * t + 0.6 * np.sin(TAU * 5.0 * t) * np.clip((t - 0.3), 0, 1) * 0.02
    if swell:
        ea = np.clip(t / max(dur * 0.8, 0.1), 0, 1) ** 2
    else:
        ea = np.clip(t / att, 0, 1)
    br = f * (1.5 + 5 * ea * vel)
    out = np.zeros(len(t))
    for k in range(1, 18):
        if k * f > 10000:
            break
        w = 1.0 / k / (1 + (k * f / br) ** 2)
        out += w * np.sin(k * phase)
    env = ea * np.where(t > dur, np.exp(-(t - dur) * (6.0 / rel)), 1.0)
    return out * env * vel


def bugle(m, dur, vel=0.6):
    f = mf(m)
    t = tvec(dur + 0.6)
    vib = 1 + 0.006 * np.sin(TAU * 5.0 * t) * np.clip((t - 0.35) / 0.5, 0, 1)
    phase = TAU * f * np.cumsum(vib) / SR
    att = np.clip(t / 0.07, 0, 1)
    br = f * (2.0 + 2.5 * att)
    out = np.zeros(len(t))
    for k in range(1, 14):
        w = 1.0 / k / (1 + (k * f / br) ** 2)
        out += w * np.sin(k * phase)
    env = att * np.where(t > dur, np.exp(-(t - dur) * 9), 1.0)
    return out * env * vel


def timp(m, vel=0.8, dur=2.0):
    f = mf(m)
    t = tvec(dur)
    fp = f * (1 + 0.08 * np.exp(-t * 20))
    ph = TAU * np.cumsum(fp) / SR
    s = np.sin(ph) + 0.5 * np.sin(1.5 * ph) * np.exp(-t * 3) + 0.25 * np.sin(2.0 * ph) * np.exp(-t * 4)
    hit = lp1(RNG.standard_normal(len(t)), 1500) * np.exp(-t * 35) * 0.6
    return (s * np.exp(-t * 2.2) + hit) * vel * 0.8


def kick(vel=0.7):
    t = tvec(0.5)
    f = 52 + 90 * np.exp(-t * 30)
    ph = TAU * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * vel


def ride(vel=0.4):
    t = tvec(1.4)
    n = highpass(RNG.standard_normal(len(t)), 5000) * np.exp(-t * 5) * 0.5
    ring = sum(np.sin(TAU * fr * t + RNG.uniform(0, 6)) for fr in (3150, 4270, 5340, 6930, 8110)) * 0.08
    ping = np.sin(TAU * 2600 * t) * np.exp(-t * 18) * 0.25
    return (n + ring * np.exp(-t * 3.5) + ping) * vel


def brush(vel=0.3, dur=0.25):
    t = tvec(dur)
    n = bandpass(RNG.standard_normal(len(t)), 1500, 7000)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return n * env * vel * 0.4


def snare(vel=0.6):
    t = tvec(0.4)
    n = bandpass(RNG.standard_normal(len(t)), 1200, 9000) * np.exp(-t * 18)
    body = np.sin(TAU * 190 * t) * np.exp(-t * 25)
    return (n * 0.7 + body * 0.5) * vel


def tom(m, vel=0.7):
    t = tvec(0.6)
    f = mf(m) * (1 + 0.25 * np.exp(-t * 18))
    ph = TAU * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 7) + bandpass(RNG.standard_normal(len(t)), 300, 3000) * np.exp(-t * 40) * 0.3) * vel


def crash(vel=0.5, dur=2.2):
    t = tvec(dur)
    n = highpass(RNG.standard_normal(len(t)), 3500) * np.exp(-t * 2.2)
    return n * vel * 0.5


def pluck(m, dur=0.5, vel=0.6):
    f = mf(m)
    t = tvec(dur + 0.2)
    s = np.zeros(len(t))
    for k in range(1, 10):
        s += np.sin(TAU * k * f * t) / k * np.exp(-t * (6 + k * 3))
    return s * (1 - np.exp(-t * 900)) * vel


# ------------------------------------------------------------------ cues
def chord(names):
    return [nm(n) for n in names]


def cue_lounge(dur, seed=0, outro=False):
    out = np.zeros(int((dur + 3) * SR))
    bpm = 112
    beat = 60 / bpm
    sw = 0.66   # swing
    prog = [('F2', ['A3', 'D4', 'F4', 'C5']), ('D2', ['F#3', 'C4', 'E4', 'A4']),
            ('G2', ['F3', 'Bb3', 'D4', 'A4']), ('C2', ['E3', 'Bb3', 'D4', 'G4']),
            ('A2', ['G3', 'C4', 'E4', 'G4']), ('D2', ['F#3', 'C4', 'E4', 'B4']),
            ('G2', ['F3', 'Bb3', 'D4', 'F4']), ('C2', ['E3', 'Bb3', 'D4', 'A4'])]
    bar = 4 * beat
    nb = int(dur / bar) + 1
    rnd = np.random.default_rng(seed)
    melody = ['A4', None, 'C5', 'D5', None, 'C5', 'A4', None, 'G4', None, 'F4', None, 'G4', 'A4', None, None]
    for b in range(nb):
        root, voic = prog[b % len(prog)]
        nroot = nm(prog[(b + 1) % len(prog)][0])
        r = nm(root)
        t0 = b * bar
        # walking bass
        walk = [r, r + (4 if b % 2 == 0 else 3), r + 7, nroot + (1 if rnd.random() < 0.5 else -1)]
        for i, mm in enumerate(walk):
            mm2 = mm if mm < nm('C3') + 5 else mm - 12
            place(out, ubass(mm2, beat * 0.9, 0.75 + 0.1 * (i == 0)), t0 + i * beat)
        # rhodes comping on 2& and 4
        for off, ln in ((beat * (1 + sw), beat * 0.9), (beat * 3, beat * 0.6)):
            if rnd.random() < 0.85:
                for k, n_ in enumerate(voic):
                    place(out, epiano(nm(n_), ln, 0.32), t0 + off + k * 0.006)
        # ride spang-a-lang
        for i in range(4):
            place(out, ride(0.16 if i % 2 == 0 else 0.12), t0 + i * beat)
            if i % 2 == 1:
                place(out, ride(0.09), t0 + i * beat + beat * sw)
            place(out, brush(0.22, beat * 0.9), t0 + i * beat)
        if b % 2 == 1:
            place(out, kick(0.25), t0)
        # sparse vibes melody in the first 4 bars of every 8
        if b % 8 < 4 and not outro:
            for i in range(4):
                n_ = melody[(b % 4) * 4 + i]
                if n_:
                    place(out, vibes(nm(n_), beat * 0.8, 0.35), t0 + i * beat + (beat * sw if i % 2 else 0))
    if outro:
        end = dur - 1.8
        for k, n_ in enumerate(['A3', 'D4', 'E4', 'G4', 'C5']):
            place(out, epiano(nm(n_), 1.6, 0.45), end + k * 0.03)
        place(out, ubass(nm('F2'), 1.6, 0.9), end)
        place(out, crash(0.35), end)
        place(out, vibes(nm('F5'), 1.4, 0.4), end + 0.05)
        out[int((end + 2.6) * SR):] = 0
    return out


def cue_tension(dur):
    out = np.zeros(int((dur + 3) * SR))
    t = tvec(dur + 1)
    # low drone
    for n_, v in (('D2', 0.5), ('A2', 0.35)):
        place(out, strings(nm(n_), dur, v, att=3.0, rel=2.0, bright=900), 0.0)
    beat = 60 / 92
    pat = ['D3', None, 'F3', None, 'E3', None, 'Eb3', None, 'D3', 'D3', 'F3', None, 'Ab3', None, 'G3', None]
    i = 0
    tt = 0.0
    while tt < dur - 0.5:
        n_ = pat[i % len(pat)]
        g = 0.35 + 0.35 * min(1, tt / dur * 1.5)
        if n_:
            place(out, pluck(nm(n_), 0.35, g), tt)
        if i % 4 == 0:
            place(out, kick(0.35 * g), tt)
            place(out, kick(0.22 * g), tt + 0.22)
        tt += beat / 2
        i += 1
    # eerie high harmonic swells
    for st in np.arange(4.0, dur - 3, 9.0):
        place(out, strings(nm('A5'), 3.0, 0.07, att=2.0, rel=1.5, bright=4000), st)
        place(out, strings(nm('Bb5'), 3.0, 0.05, att=2.0, rel=1.5, bright=4000), st + 1.0)
    return out


def cue_doom(dur):
    out = np.zeros(int((dur + 3) * SR))
    t = tvec(dur + 1)
    # dun dun DUNNN
    for k, (n_, ln) in enumerate((('D3', 0.25), ('D3', 0.25), ('A2', 1.6))):
        tt = k * 0.32
        for iv in (0, 7, 12):
            place(out, brass(nm(n_) + iv, ln, 0.6), tt)
        place(out, timp(nm(n_) - 12, 0.8), tt)
    # tremolo strings + stabs
    beat = 60 / 150
    chords = [['D3', 'F3', 'A3', 'D4'], ['Bb2', 'F3', 'Bb3', 'D4'], ['G2', 'G3', 'Bb3', 'D4'], ['A2', 'E3', 'A3', 'C#4']]
    st = 2.2
    bar = beat * 4
    b = 0
    while st < dur - 0.3:
        ch = chords[b % 4]
        seg = np.zeros(int((bar * 2 + 1.0) * SR))
        for n_ in ch:
            place(seg, strings(nm(n_), bar * 2, 0.22, att=0.05, rel=0.3, bright=3000), 0)
        tr = 0.55 + 0.45 * np.sign(np.sin(TAU * 11 * np.arange(len(seg)) / SR))
        place(out, lp1(seg * tr, 4000), st)
        for iv in (0, 12):
            place(out, brass(nm(ch[0]) + iv + 12, 0.28, 0.45), st)
        place(out, timp(nm(ch[0]) - 12 if nm(ch[0]) > nm('E2') else nm(ch[0]), 0.6), st)
        if b % 2 == 1:
            for k in range(8):
                place(out, timp(nm('D2'), 0.15 + 0.05 * k, 0.6), st + bar + k * beat / 2)
        st += bar * 2
        b += 1
    return out


def cue_pad(dur):
    out = np.zeros(int((dur + 3) * SR))
    prog = [['D3', 'A3', 'E4', 'F4'], ['Bb2', 'F3', 'A3', 'D4'], ['F2', 'C3', 'A3', 'C4'], ['C3', 'G3', 'E4', 'G4']]
    seg = 4.2
    i = 0
    st = 0.0
    while st < dur:
        ch = prog[i % 4]
        for n_ in ch:
            place(out, strings(nm(n_), seg + 0.4, 0.16, att=1.2, rel=1.5, bright=1600), st)
        for k, n_ in enumerate(ch[1:] + [ch[2]]):
            place(out, epiano(nm(n_) + 12, 1.2, 0.18), st + 0.6 + k * 0.9)
        place(out, ubass(nm(ch[0]) - 12 if nm(ch[0]) > nm('E2') else nm(ch[0]), seg * 0.9, 0.35), st)
        st += seg
        i += 1
    return out


def cue_taps(dur):
    out = np.zeros(int((dur + 4) * SR))
    for n_ in ('C2', 'G2', 'C3'):
        place(out, strings(nm(n_), dur, 0.18, att=2.0, rel=2.0, bright=700), 0.0)
    q = 1.05
    mel = [('G3', .75), ('G3', .25), ('C4', 2.0), ('G3', .75), ('C4', .25), ('E4', 2.0),
           ('G3', .5), ('C4', .5), ('E4', 1.0), ('G3', .5), ('C4', .5), ('E4', 1.0),
           ('C4', .75), ('E4', .25), ('G4', 2.0), ('E4', .75), ('C4', .25), ('G3', 2.0),
           ('G3', .75), ('G3', .25), ('C4', 3.0)]
    tt = 1.0
    bug = np.zeros_like(out)
    for n_, ln in mel:
        if tt > dur - 0.5:
            break
        place(bug, bugle(nm(n_), ln * q * 0.95, 0.5), tt)
        tt += ln * q
    bug = add_reverb(bug, 0.6, 2.6, 4000, 0.05)[:len(out)]
    out += bug
    return out


def cue_heroic(dur):
    out = np.zeros(int((dur + 3) * SR))
    prog = [(['C3', 'G3', 'C4', 'E4'], 3.0), (['C3', 'A3', 'C4', 'F4'], 3.0),
            (['D3', 'B3', 'D4', 'G4'], 3.0), (['C3', 'G3', 'C4', 'E4', 'G4'], 4.5)]
    st = 0.0
    for i, (ch, ln) in enumerate(prog):
        if st > dur:
            break
        for n_ in ch:
            place(out, brass(nm(n_), ln, 0.22 + 0.06 * i, swell=True, rel=0.8), st)
            place(out, strings(nm(n_) + 12, ln, 0.08, att=1.0, rel=1.0, bright=3000), st)
        for k in range(int(ln * 6)):
            place(out, timp(nm('C2'), 0.05 + 0.25 * (k / (ln * 6)) * (i + 1) / 4, 0.4), st + k / 6)
        st += ln
    fan = [('G4', 0.5), ('C5', 0.5), ('E5', 0.5), ('G5', 2.0)]
    tt = 9.0
    for n_, ln in fan:
        if tt < dur:
            place(out, brass(nm(n_), ln, 0.35), tt)
        tt += ln
    if dur > 9:
        place(out, timp(nm('C2'), 0.8), 10.5)
        place(out, crash(0.25), 10.5)
    return out


def cue_warm(dur):
    out = np.zeros(int((dur + 3) * SR))
    prog = [('F2', ['A3', 'C4', 'E4', 'G4']), ('E2', ['G3', 'B3', 'D4', 'G4']),
            ('D2', ['F3', 'A3', 'C4', 'E4']), ('C2', ['E3', 'G3', 'B3', 'D4']),
            ('Bb1', ['D3', 'F3', 'A3', 'C4']), ('A1', ['G3', 'C4', 'E4', 'A4']),
            ('G1', ['F3', 'A3', 'Bb3', 'D4']), ('C2', ['E3', 'G3', 'Bb3', 'D4'])]
    beat = 60 / 70
    bar = beat * 4
    b = 0
    st = 0.0
    while st < dur:
        root, voic = prog[b % len(prog)]
        place(out, ubass(nm(root) + 12, bar * 0.95, 0.45), st)
        for k, n_ in enumerate(voic):
            place(out, epiano(nm(n_), bar * 0.9, 0.22), st + k * 0.012)
        arp = voic + [voic[1]]
        for k in range(4):
            place(out, epiano(nm(arp[k % len(arp)]) + 12, beat * 0.8, 0.12), st + beat * (k + 0.5))
        for n_ in voic[:3]:
            place(out, strings(nm(n_), bar, 0.05, att=1.5, rel=1.5, bright=1400), st)
        st += bar
        b += 1
    return out


CUES = {'lounge': cue_lounge, 'tension': cue_tension, 'doom': cue_doom, 'pad': cue_pad,
        'taps': cue_taps, 'heroic': cue_heroic, 'warm': cue_warm,
        'outro': lambda d: cue_lounge(d, seed=5, outro=True)}
CUE_LEVEL = {'lounge': 0.33, 'tension': 0.40, 'doom': 0.49, 'pad': 0.71, 'taps': 0.37, 'heroic': 0.41,
             'warm': 0.96, 'outro': 0.47}


# ------------------------------------------------------------------ sound effects
def sfx(name, dur=None):
    if name == 'servo':
        t = tvec(1.8)
        f = 120 + 25 * np.sin(TAU * 3.2 * t)
        ph = TAU * np.cumsum(f) / SR
        s = np.sign(np.sin(ph)) * 0.3 + np.sin(2 * ph) * 0.2
        s = bandpass(s, 300, 2500) * (0.6 + 0.4 * np.sign(np.sin(TAU * 2.8 * t)))
        for k in range(5):
            i = int((0.18 + k * 0.36) * SR)
            s[i:i + 2000] += bandpass(RNG.standard_normal(2000), 2000, 8000) * np.exp(-np.arange(2000) / 300) * 0.8
        return s * np.clip(t / 0.1, 0, 1) * np.clip((1.8 - t) / 0.2, 0, 1) * 0.5
    if name == 'feedback':
        t = tvec(0.9)
        f = 2700 + 300 * t + 40 * np.sin(TAU * 6 * t)
        s = np.sin(TAU * np.cumsum(f) / SR)
        return s * np.clip(t / 0.5, 0, 1) ** 2 * np.clip((0.9 - t) / 0.1, 0, 1) * 0.35
    if name == 'claps_few':
        out = np.zeros(int(2.5 * SR))
        for tt in (0.0, 0.31, 0.55, 0.92, 1.3):
            c = bandpass(RNG.standard_normal(int(0.08 * SR)), 900, 5000) * np.exp(-np.arange(int(0.08 * SR)) / 500)
            place(out, c, tt + RNG.uniform(0, 0.05), RNG.uniform(0.4, 0.8))
        return add_reverb(out, 0.4, 1.0)[:len(out)] * 2.2
    if name == 'rimshot':
        out = np.zeros(int(2.4 * SR))
        place(out, tom(nm('D3'), 0.8), 0.0)
        place(out, snare(0.6), 0.0)
        place(out, tom(nm('A2'), 0.8), 0.24)
        place(out, kick(0.5), 0.24)
        place(out, crash(0.6, 1.8), 0.5)
        place(out, snare(0.5), 0.5)
        return out * 0.8
    if name == 'crickets':
        d = dur or 4.0
        out = np.zeros(int(d * SR))
        for (f, per, ph) in ((4300, 0.62, 0.0), (4750, 0.81, 0.3)):
            tt = ph
            while tt < d - 0.3:
                n = int(0.12 * SR)
                t = np.arange(n) / SR
                c = np.sin(TAU * f * t) * (0.5 + 0.5 * np.sin(TAU * 32 * t - np.pi / 2)) * np.sin(np.pi * t / 0.12)
                place(out, c, tt, 0.36)
                tt += per * RNG.uniform(0.9, 1.1)
        return out * np.clip(np.arange(len(out)) / SR / 0.3, 0, 1)
    if name == 'tick':
        n = int(0.05 * SR)
        return highpass(RNG.standard_normal(n), 3000) * np.exp(-np.arange(n) / 120) * 0.5
    if name == 'cough':
        out = np.zeros(int(0.8 * SR))
        for tt, g in ((0.0, 1.0), (0.28, 0.7)):
            n = int(0.18 * SR)
            t = np.arange(n) / SR
            c = bandpass(RNG.standard_normal(n), 300, 2500) * np.exp(-t * 18) * (1 - np.exp(-t * 400))
            c += np.sin(TAU * 180 * t) * np.exp(-t * 25) * 0.4
            place(out, c, tt, g)
        return add_reverb(out, 0.5, 1.4)[:len(out) + SR] * 0.9
    if name == 'crunch':
        out = np.zeros(int(0.7 * SR))
        for k in range(70):
            n = int(0.012 * SR)
            c = bandpass(RNG.standard_normal(n), 1500, 9000) * np.exp(-np.arange(n) / 90)
            place(out, c, RNG.uniform(0, 0.55), RNG.uniform(0.2, 0.8))
        return out * 0.6
    if name == 'popcorn':
        out = np.zeros(int(1.2 * SR))
        for k in range(30):
            n = int(0.01 * SR)
            c = bandpass(RNG.standard_normal(n), 2000, 10000) * np.exp(-np.arange(n) / 70)
            place(out, c, 0.15 + RNG.uniform(0, 0.9) ** 1.6, RNG.uniform(0.15, 0.5))
        return out
    if name == 'scratch':
        t = tvec(0.45)
        f = 600 + 900 * np.abs(np.sin(TAU * 4.5 * t))
        s = np.sin(TAU * np.cumsum(f) / SR) * 0.4 + bandpass(RNG.standard_normal(len(t)), 800, 4000) * 0.5
        return s * np.exp(-t * 3) * 0.7
    if name in ('whoosh', 'whip'):
        d = 0.45 if name == 'whoosh' else 0.18
        t = tvec(d)
        n = RNG.standard_normal(len(t))
        out = np.zeros(len(t))
        segs = 12
        for k in range(segs):
            a, b = int(k * len(t) / segs), int((k + 1) * len(t) / segs)
            fc = 400 + 3000 * (k / segs)
            out[a:b] = bandpass(n[a:b], fc * 0.6, fc * 1.6)
        return out * np.sin(np.pi * t / d) ** 2 * (0.6 if name == 'whoosh' else 0.45)
    if name == 'slurp':
        d = dur or 1.3
        t = tvec(d)
        n = bandpass(RNG.standard_normal(len(t)), 500, 3500)
        am = 0.5 + 0.5 * np.sin(TAU * (9 + 5 * np.sin(TAU * 1.3 * t)) * t)
        gurg = np.sin(TAU * (300 + 120 * np.sin(TAU * 11 * t)) * t) * 0.3
        return (n * am + gurg * am) * np.clip(t / 0.1, 0, 1) * np.clip((d - t) / 0.15, 0, 1) * 0.35
    if name == 'gulp':
        t = tvec(0.35)
        f = 330 * np.exp(-t * 4)
        s = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t * 9)
        return s * 0.55
    if name == 'impact':
        t = tvec(0.9)
        crack = highpass(RNG.standard_normal(len(t)), 2500) * np.exp(-t * 90) * 0.9
        f = 45 + 110 * np.exp(-t * 25)
        thump = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t * 6) * 0.9
        return add_reverb(crack + thump, 0.35, 1.2)[:len(t)] * 0.45
    if name == 'thud':
        t = tvec(1.0)
        f = 38 + 70 * np.exp(-t * 18)
        thump = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t * 5)
        rumble = lp1(RNG.standard_normal(len(t)), 300) * np.exp(-t * 8) * 0.8
        return (thump + rumble) * 0.75
    if name == 'tinnitus':
        d = dur or 12.0
        t = tvec(d)
        s = np.sin(TAU * 6200 * t) + 0.3 * np.sin(TAU * 6213 * t)
        env = np.clip(t / 0.15, 0, 1) * (0.25 + 0.75 * np.exp(-t * 0.35)) * np.clip((d - t) / 1.0, 0, 1)
        return s * env * 0.3
    raise KeyError(name)


# ------------------------------------------------------------------ mixing
def voice_bus(tl, total):
    """Returns (anger_bus, other_bus, activity envelope)."""
    import soundfile as sf
    keep = np.zeros(int(total * SR))
    world = np.zeros(int(total * SR))
    act = np.zeros(int(total * SR))
    for ln in tl.lines:
        a, sr = sf.read(ln['wav'], dtype='float64')
        fx = ln.get('fx', ())
        if ln.get('voiceover'):
            y = a * 1.0
        elif 'robot' in fx:
            y = add_reverb(a, 0.5, 1.6, 5000, 0.03)
        else:
            y = add_reverb(a, 0.22, 0.7, 6000, 0.012)
        target = keep if (ln['actor'] == 'anger' or ln.get('voiceover')) else world
        place(target, y, ln['t0'])
        i0 = int(ln['t0'] * SR)
        i1 = min(len(act), i0 + len(a))
        act[i0:i1] = np.maximum(act[i0:i1], 1.0 if not ln.get('voiceover') or True else 0.8)
    return keep, world, act


def smooth_env(x, att=0.05, rel=0.45, step=480):
    n = len(x)
    m = n // step + 1
    xs = np.array([x[i * step:(i + 1) * step].max() if i * step < n else 0 for i in range(m)])
    y = np.zeros(m)
    v = 0.0
    a_c = 1 - np.exp(-step / SR / att)
    r_c = 1 - np.exp(-step / SR / rel)
    for i in range(m):
        tgt = xs[i]
        v += (tgt - v) * (a_c if tgt > v else r_c)
        y[i] = v
    return np.interp(np.arange(n), np.arange(m) * step, y)


def mix(tl, out_wav):
    total = tl.end + 0.5
    N = int(total * SR)
    keep, world_v, act = voice_bus(tl, total)
    keep = keep[:N]
    world_v = world_v[:N]
    music = np.zeros(N)
    for c in tl.music:
        d = c['t1'] - c['t0']
        x = CUES[c['name']](d)
        n = int((d + c['fade_out']) * SR)
        x = x[:n]
        t = np.arange(len(x)) / SR
        env = np.ones(len(x))
        if c['fade_in'] > 0:
            env *= np.clip(t / c['fade_in'], 0, 1)
        env *= np.clip((d + c['fade_out'] - t) / max(c['fade_out'], 1e-3), 0, 1)
        place(music, x * env * c['gain'] * CUE_LEVEL[c['name']], c['t0'])
    music = add_reverb(music, 0.25, 1.4, 7000)[:N]
    fx = np.zeros(N)
    keep_fx = np.zeros(N)
    for e in tl.sfx:
        kw = {}
        if 'dur' in e:
            kw['dur'] = e['dur']
        x = sfx(e['name'], **kw)
        tgt = keep_fx if e['name'] == 'tinnitus' else fx
        place(tgt, x, e['t'], e['gain'])
    # ducking: music dips under dialogue
    duck = 1 - 0.6 * smooth_env(act)
    music *= duck
    world = music + fx + world_v
    # muffle (tinnitus / shell-shock) from the camera track
    mus = np.array([tl.state('cam', i / 50.0).get('muffle', 0.0) for i in range(int(total * 50) + 1)])
    mu = np.interp(np.arange(N) / SR, np.arange(len(mus)) / 50.0, mus)
    if mu.max() > 0.01:
        idx = np.where(mu > 0.001)[0]
        a, b = max(0, idx[0] - SR), min(N, idx[-1] + SR)
        seg = world[a:b]
        lp = lp1(lp1(seg, 700), 700)
        world[a:b] = seg * (1 - mu[a:b]) + lp * mu[a:b] * 1.3
    out = keep + world + keep_fx
    # gentle bus compression + limiter
    env = smooth_env(np.abs(out), 0.005, 0.25, 240)
    thr = 0.5
    g = np.where(env > thr, (thr + (env - thr) * 0.4) / np.maximum(env, 1e-9), 1.0)
    out *= g
    peak = np.max(np.abs(out))
    out = out / peak * 0.89
    sf.write(out_wav, out.astype(np.float32), SR, subtype='FLOAT')
    return out_wav
