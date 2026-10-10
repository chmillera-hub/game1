"""Tiny numpy synth: orchestra-ish instruments, the 'symphony', the ten
alternate snippets, ambience and sound effects. Everything is procedural."""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve

SR = 44100
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def t_arr(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a=0.01, d=0.1, s=0.8, r=0.2):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    env = np.ones(n) * s
    a = min(a, n)
    env[:a] = np.linspace(0, 1, a, endpoint=False) if a else env[:a]
    d2 = min(d, n - a)
    if d2 > 0:
        env[a:a + d2] = np.linspace(1, s, d2)
    r = min(r, n)
    if r > 0:
        env[n - r:] *= np.linspace(1, 0, r) ** 1.5
    return env


def lp(x, fc, order=2):
    fc = min(fc, SR * 0.45)
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)


def saw(f, t, phase=0.0):
    ph = (f * t + phase) % 1.0
    return 2 * ph - 1


def vib_phase(f, t, rate=5.5, depth=0.004, delay=0.25):
    ramp = np.clip((t - delay) / 0.4, 0, 1)
    inst = f * (1 + depth * ramp * np.sin(2 * np.pi * rate * t + rng.random() * 6))
    return np.cumsum(inst) / SR


# ---------------------------------------------------------------- instruments
def strings_note(m, dur, vel=1.0, att=0.25, rel=0.5, bright=1.0):
    f = mtof(m)
    t = t_arr(dur + rel)
    out = np.zeros_like(t)
    for det in (-0.006, -0.002, 0.003, 0.007):
        ph = vib_phase(f * (1 + det), t)
        out += 2 * ((ph + rng.random()) % 1.0) - 1
    out /= 4
    env = adsr(len(t), att, 0.2, 0.85, rel)
    return lp(out, min(900 + f * 4 * bright, 7000)) * env * vel


def choir_note(m, dur, vel=1.0, att=0.6, rel=0.9):
    f = mtof(m)
    t = t_arr(dur + rel)
    src = np.zeros_like(t)
    for det in (-0.008, -0.003, 0.0, 0.004, 0.009):
        ph = vib_phase(f * (1 + det), t, rate=4.8 + rng.random(), depth=0.006)
        src += 2 * ((ph + rng.random()) % 1.0) - 1
    src /= 5
    v = 1.0 * bp(src, 650, 950) + 0.6 * bp(src, 1050, 1350) + 0.25 * bp(src, 2500, 3100)
    v += 0.05 * bp(rng.standard_normal(len(t)), 2000, 6000)  # breath
    return v * adsr(len(t), att, 0.3, 0.9, rel) * vel * 1.6


def brass_note(m, dur, vel=1.0):
    f = mtof(m)
    t = t_arr(dur + 0.3)
    s = 0.5 * saw(f, t) + 0.5 * saw(f * 1.004, t, 0.3)
    env = adsr(len(t), 0.08, 0.25, 0.75, 0.3)
    dark = lp(s, 600 + f)
    bright = lp(s, 2500 + f * 2)
    mix = np.clip(env * 1.2, 0, 1)
    return (dark * (1 - mix * 0.6) + bright * mix * 0.6) * env * vel


def harp_note(m, dur=2.5, vel=1.0):
    f = mtof(m)
    t = t_arr(dur)
    out = np.zeros_like(t)
    for k, a in enumerate([1, 0.5, 0.28, 0.14, 0.08, 0.04], start=1):
        out += a * np.sin(2 * np.pi * f * k * 1.0005 ** k * t) * np.exp(-t * (1.6 + k * 0.9))
    out *= np.clip(t / 0.003, 0, 1)
    return out * vel * 0.6


def piano_note(m, dur=2.0, vel=1.0):
    f = mtof(m)
    t = t_arr(dur)
    out = np.zeros_like(t)
    for k, a in enumerate([1, 0.6, 0.3, 0.2, 0.1, 0.06, 0.03], start=1):
        out += a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (1.2 + k * 0.7))
    out *= np.clip(t / 0.002, 0, 1) * adsr(len(t), 0.001, 0.1, 1, 0.15)
    return out * vel * 0.5


def musicbox_note(m, dur=2.0, vel=1.0):
    f = mtof(m)
    t = t_arr(dur)
    out = np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2)
    out += 0.35 * np.sin(2 * np.pi * f * 4.07 * t) * np.exp(-t * 6)
    out += 0.15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 12)
    return out * np.clip(t / 0.001, 0, 1) * vel * 0.5


def ks_pluck(m, dur=1.0, vel=1.0, decay=0.996, bright=1.0):
    f = mtof(m)
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    x = np.zeros(n)
    burst = rng.uniform(-1, 1, N)
    if bright < 1:
        burst = lp(burst, 1500 + 6000 * bright)
    x[:N] = burst
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -0.5 * decay
    a[N + 1] = -0.5 * decay
    y = lfilter([1.0], a, x)
    return y * vel * adsr(n, 0.001, 0.05, 1, 0.05) * 0.7


def rhodes_note(m, dur=2.0, vel=1.0):
    f = mtof(m)
    t = t_arr(dur)
    mod = np.sin(2 * np.pi * f * t) * 1.2 * np.exp(-t * 3)
    out = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 0.9)
    out += 0.2 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 2)
    return out * adsr(len(t), 0.003, 0.1, 1, 0.2) * vel * 0.45


def timpani(m, vel=1.0, dur=2.0):
    f = mtof(m)
    t = t_arr(dur)
    ph = np.cumsum(f * (1 + 0.04 * np.exp(-t * 20))) / SR
    tone = np.sin(2 * np.pi * ph) * np.exp(-t * 2.2) + 0.4 * np.sin(2 * np.pi * ph * 1.5) * np.exp(-t * 3.5)
    noise = lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 25) * 0.6
    return (tone + noise) * vel * 0.9


def snare(vel=1.0, dur=0.3):
    t = t_arr(dur)
    n = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 18)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return (0.7 * n + 0.5 * tone) * vel * 0.6


def kick(vel=1.0, dur=0.4):
    t = t_arr(dur)
    ph = np.cumsum(50 + 110 * np.exp(-t * 35)) / SR
    return np.sin(2 * np.pi * ph) * np.exp(-t * 7) * vel


def cymbal(vel=1.0, dur=3.0, swell=False):
    t = t_arr(dur)
    n = hp(rng.standard_normal(len(t)), 5000)
    env = (t / dur) ** 2.5 if swell else np.exp(-t * 1.5)
    return n * env * vel * 0.35


# ------------------------------------------------------------------- helpers
class Track:
    def __init__(self, dur):
        self.L = np.zeros(int(dur * SR) + SR * 6)
        self.R = np.zeros_like(self.L)

    def add(self, sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= len(self.L):
            return
        sig = sig[: len(self.L) - i]
        gl = np.cos((pan + 1) * np.pi / 4) * gain
        gr = np.sin((pan + 1) * np.pi / 4) * gain
        self.L[i:i + len(sig)] += sig * gl
        self.R[i:i + len(sig)] += sig * gr

    def add_st(self, st, t0, gain=1.0):
        i = int(t0 * SR)
        n = min(st.shape[1], len(self.L) - i)
        if n <= 0:
            return
        self.L[i:i + n] += st[0, :n] * gain
        self.R[i:i + n] += st[1, :n] * gain

    def st(self):
        return np.vstack([self.L, self.R])


def make_ir(length=2.6, damp=3000):
    t = t_arr(length)
    irs = []
    for _ in range(2):
        n = rng.standard_normal(len(t)) * np.exp(-t * 6.9 / length)
        n = lp(n, damp)
        n[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        irs.append(n / np.sqrt(np.sum(n ** 2)))
    return irs


_IR_CACHE = {}


def reverb(st, wet=0.3, length=2.6, damp=3000):
    key = (length, damp)
    if key not in _IR_CACHE:
        _IR_CACHE[key] = make_ir(length, damp)
    irL, irR = _IR_CACHE[key]
    L = fftconvolve(st[0], irL)[: st.shape[1]]
    R = fftconvolve(st[1], irR)[: st.shape[1]]
    return np.vstack([st[0] * (1 - wet) + L * wet * 3, st[1] * (1 - wet) + R * wet * 3])


def trim(st, dur, fade=0.05):
    n = int(dur * SR)
    st = st[:, :n].copy()
    if st.shape[1] < n:
        st = np.pad(st, ((0, 0), (0, n - st.shape[1])))
    f = int(fade * SR)
    if f:
        st[:, -f:] *= np.linspace(1, 0, f)
        st[:, :min(f // 4, n)] *= np.linspace(0, 1, min(f // 4, n))
    return st


def norm(st, peak=0.9):
    m = np.max(np.abs(st)) + 1e-9
    return st * (peak / m)


# ----------------------------------------------------------------- symphony
CH = {  # chord tones (midi, mid register) and bass root
    'D': ([62, 66, 69], 38), 'Bm': ([59, 62, 66], 35), 'G': ([59, 62, 67], 31),
    'A': ([61, 64, 69], 33), 'F#m': ([61, 66, 69], 30), 'D/F#': ([62, 66, 69], 30),
    'Bb': ([58, 62, 65], 34), 'C': ([60, 64, 67], 36), 'E': ([64, 68, 71], 40),
    'C#m': ([61, 64, 68], 37), 'B': ([63, 66, 71], 35),
}
PROG = ['D', 'Bm', 'G', 'A', 'D', 'F#m', 'G', 'A', 'Bm', 'G', 'D/F#', 'A',
        'G', 'A', 'F#m', 'Bm', 'Bb', 'C', 'E', 'C#m', 'A', 'B', 'E', 'E', 'E']
WALK = {  # bar: descending quarter-note bassline (midi)
    10: [43, 42, 40, 38], 11: [42, 40, 38, 37], 12: [45, 43, 42, 40],
    13: [43, 42, 40, 38], 14: [45, 43, 42, 40], 15: [42, 40, 38, 37], 16: [35, 37, 38, 40],
}
MEL = {  # bar: [(beat, dur, midi)]
    5: [(0, 1.5, 69), (1.5, .5, 74), (2, 2, 78)],
    6: [(0, 1, 76), (1, .5, 78), (1.5, .5, 76), (2, 2, 73)],
    7: [(0, 1.5, 71), (1.5, .5, 74), (2, 1.5, 79), (3.5, .5, 78)],
    8: [(0, 3, 76), (3, 1, 69)],
    9: [(0, 1.5, 74), (1.5, .5, 78), (2, 2, 83)],
    10: [(0, 1, 81), (1, 1, 79), (2, 2, 74)],
    11: [(0, 1.5, 78), (1.5, .5, 79), (2, 1.5, 81), (3.5, .5, 86)],
    12: [(0, 2, 85), (2, 1, 83), (3, 1, 81)],
    13: [(0, 1.5, 83), (1.5, .5, 81), (2, 1, 79), (3, 1, 83)],
    14: [(0, 1.5, 81), (1.5, .5, 79), (2, 2, 76)],
    15: [(0, 1, 78), (1, 1, 81), (2, 2, 85)],
    16: [(0, 4, 83)],
    17: [(0, 2, 86), (2, 1, 84), (3, 1, 82)],
    18: [(0, 2, 84), (2, 1, 79), (3, 1, 83)],
    19: [(0, 2, 88), (2, 1, 83), (3, 1, 80)],
    20: [(0, 1.5, 80), (1.5, .5, 81), (2, 2, 83)],
    21: [(0, 1.5, 85), (1.5, .5, 83), (2, 1, 81), (3, 1, 85)],
    22: [(0, 2, 87), (2, 2, 90)],
    23: [(0, 10, 88)],
}


def symphony(bpm=70):
    """Returns (stereo, bar_times). ~88 s. Bars numbered from 1."""
    B = 60.0 / bpm
    nbars = len(PROG)
    dur = nbars * 4 * B + 6
    strings, harp, brass, choir, perc, solo = (Track(dur) for _ in range(6))
    bar_t = lambda b: (b - 1) * 4 * B
    for b, ch in enumerate(PROG, start=1):
        tones, root = CH[ch]
        t0 = bar_t(b)
        last = b == nbars
        hold = 4 * B * (2.5 if last else 1.0)
        # dynamics curve
        if b <= 4:
            dyn = 0.25 + 0.05 * b
        elif b <= 12:
            dyn = 0.45 + 0.03 * (b - 4)
        elif b <= 16:
            dyn = 0.75
        elif b <= 22:
            dyn = 0.9 + 0.02 * (b - 17)
        else:
            dyn = 0.7 - (0.25 if last else 0)
        # string pad (violas) and basses
        if b >= 2:
            for k, m in enumerate(tones):
                strings.add(strings_note(m, hold, 0.22 * dyn, att=0.6 if b < 5 else 0.3), t0, pan=-0.3 + 0.3 * k)
        if b >= 5:
            strings.add(strings_note(root, hold, 0.35 * dyn, bright=0.6), t0, pan=0.2)
            strings.add(strings_note(root + 12, hold, 0.25 * dyn, bright=0.6), t0, pan=0.35)
        else:
            strings.add(strings_note(root + 12, hold, 0.18 * dyn, att=1.0, bright=0.5), t0, pan=0.2)
        # harp arpeggios intro / outro / sparkle
        if b <= 4 or b >= 23 or b in (9, 10, 11, 12):
            pat = [tones[0] - 12, tones[1] - 12, tones[2] - 12, tones[0], tones[1], tones[2], tones[0] + 12, tones[1]]
            for i, m in enumerate(pat):
                harp.add(harp_note(m, 2.5, 0.55 if b <= 4 else 0.35), t0 + i * B / 2, pan=-0.5 + i * 0.12)
            if last:
                for i, m in enumerate([tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[0] + 24]):
                    harp.add(harp_note(m, 4, 0.4), t0 + 4 * B + i * B / 2, pan=0.3)
        # brass & timpani & choir build
        if 13 <= b <= 24:
            for k, m in enumerate([root + 12, tones[0] - 12, tones[1] - 12]):
                brass.add(brass_note(m, 2 * B * 0.95, 0.22 * dyn), t0, pan=0.4 - 0.2 * k)
                brass.add(brass_note(m, 2 * B * (0.95 if not last else 3), 0.2 * dyn), t0 + 2 * B, pan=0.4 - 0.2 * k)
            perc.add(timpani(root + 12, 0.9 * dyn), t0, pan=0.1)
            if b in (16, 18):
                for i in range(16):
                    perc.add(timpani(root + 12, (0.2 + 0.6 * i / 16) * dyn, 0.6), t0 + 2 * B + i * B / 8, pan=0.1)
        if b in (16, 18):
            perc.add(cymbal(0.7, 4 * B, swell=True), t0, pan=0)
        if b in (17, 19):
            perc.add(cymbal(0.9, 4.0), t0, pan=-0.2)
            perc.add(cymbal(0.8, 4.0), t0, pan=0.3)
        if b >= 17:
            for k, m in enumerate(tones + [tones[0] + 12]):
                choir.add(choir_note(m, hold, 0.22 * dyn), t0, pan=-0.6 + 0.4 * k)
        # high notes cascading down from the top (bells + high violins), entering just before the bass
        if 9 <= b <= 16:
            hi = sorted(tones)
            casc = [hi[2] + 24, hi[1] + 24, hi[0] + 24, hi[2] + 12, hi[1] + 12, hi[0] + 12, hi[2] + 12, hi[1] + 12]
            for i, m in enumerate(casc):
                v = (0.32 if b < 13 else 0.26) * (1.0 - 0.05 * i)
                harp.add(musicbox_note(m, 1.8, v), t0 + i * B / 2, pan=0.45 - 0.11 * i)
            for (bt, d, m) in MEL.get(b, []):
                solo.add(strings_note(m + 12, d * B, 0.16, att=0.15, rel=0.5, bright=1.4), t0 + bt * B, pan=0.35)
        # walking bassline stepping down (cellos + basses, low drum on every beat)
        if b in WALK:
            for i, m in enumerate(WALK[b]):
                tb = t0 + i * B
                acc = 1.0 if i == 0 else 0.8
                strings.add(strings_note(m, B * 0.92, 0.55 * acc, att=0.03, rel=0.25, bright=0.9), tb, pan=0.25)
                strings.add(strings_note(m - 12, B * 0.92, 0.45 * acc, att=0.04, rel=0.25, bright=0.5), tb, pan=0.1)
                perc.add(timpani(m + 12 if m < 40 else m, 0.55 * acc, 1.0), tb, pan=0.05)
                perc.add(kick(0.5 * acc), tb)
        # melody
        for (bt, d, m) in MEL.get(b, []):
            start = t0 + bt * B
            ln = d * B
            v = (0.42 if b < 13 else 0.5) * (1.0 if b < 22 else 1.1)
            solo.add(strings_note(m, ln, v, att=0.12, rel=0.6, bright=1.3), start, pan=-0.15)
            if b >= 13:
                solo.add(strings_note(m - 12, ln, v * 0.7, att=0.12, rel=0.6), start, pan=0.15)
            if b >= 19:
                solo.add(brass_note(m - 12, ln, 0.25), start, pan=0.0)
    # opening single high note (the "first note")
    solo.add(strings_note(81, 4 * B * 2, 0.18, att=1.5, rel=1.5), 0, pan=0)
    mix = (strings.st() * 1.0 + harp.st() * 0.9 + brass.st() * 0.9 + choir.st() * 0.8 +
           perc.st() * 0.8 + solo.st() * 1.0)
    mix = reverb(mix, wet=0.35, length=3.2, damp=4500)
    total = nbars * 4 * B + 4 * B * 1.5 + 4
    mix = trim(mix, total, fade=3.0)
    return norm(mix, 0.85), [bar_t(b) for b in range(1, nbars + 2)], B


# ------------------------------------------------------------------ snippets
def sn_harpsichord(dur=2.6):
    tr = Track(dur)
    B = 0.11
    seq = [60, 63, 67, 72, 67, 63, 60, 63, 58, 62, 65, 70, 65, 62, 58, 62, 56, 60, 63, 68, 63, 60]
    for i, m in enumerate(seq):
        tr.add(ks_pluck(m + 12, 0.6, 0.6, decay=0.993), i * B, pan=0.2)
        if i % 4 == 0:
            tr.add(ks_pluck(m - 12, 0.8, 0.5, decay=0.995), i * B, pan=-0.2)
    return trim(reverb(tr.st(), 0.15, 1.2), dur)


def sn_jazz(dur=2.8):
    tr = Track(dur)
    chords = [([62, 65, 69, 72], 38), ([60, 64, 67, 71], 43), ([59, 64, 67, 71], 36)]
    for i, (c, r) in enumerate(chords):
        t = i * 0.9
        for m in c:
            tr.add(rhodes_note(m, 1.4, 0.5), t + 0.02 * rng.random(), pan=0.2)
        tr.add(ks_pluck(r, 0.9, 1.0, decay=0.99, bright=0.2), t, pan=-0.2)
        tr.add(ks_pluck(r + 7, 0.5, 0.7, decay=0.99, bright=0.2), t + 0.45, pan=-0.2)
    for k in range(int(dur / 0.3)):
        tr.add(bp(rng.standard_normal(int(0.25 * SR)), 3000, 9000) * np.exp(-t_arr(0.25) * 10) * 0.08, k * 0.3)
    return trim(reverb(tr.st(), 0.3, 2.0), dur)


LULLABY = [(0, 1, 79), (1, 1, 83), (2, 1, 86), (3, 2, 83), (5, 1, 81), (6, 1, 79), (7, 1, 78), (8, 2, 79),
           (10, 1, 76), (11, 1, 79), (12, 1, 83), (13, 2, 81), (15, 1, 79), (16, 1, 78), (17, 1, 76), (18, 3, 74),
           (21, 1, 79), (22, 1, 83), (23, 1, 86), (24, 2, 88), (26, 1, 86), (27, 1, 83), (28, 1, 81), (29, 2, 83),
           (31, 1, 81), (32, 1, 79), (33, 1, 78), (34, 1, 81), (35, 4, 79)]


def sn_lullaby(dur=2.8, full=False):
    B = 0.42
    tr = Track(40 if full else dur)
    bass = [(0, 55), (5, 50), (10, 52), (15, 50), (21, 55), (26, 48), (31, 50), (35, 55)]
    for (bt, d, m) in LULLABY:
        tr.add(musicbox_note(m, 2.2, 0.7), bt * B, pan=0.1)
    for (bt, m) in bass:
        tr.add(musicbox_note(m, 3, 0.35), bt * B, pan=-0.2)
        if full:
            tr.add(strings_note(m - 12, 5 * B, 0.1, att=1.0, rel=1.0, bright=0.4), bt * B, pan=0)
    st = reverb(tr.st(), 0.35, 2.4)
    return trim(st, 39 * B + 3, fade=2.5) if full else trim(st, dur)


def sn_march(dur=2.6):
    tr = Track(dur)
    B = 0.22
    mel = [67, 67, 67, 72, 76, 74, 72, 79]
    for i, m in enumerate(mel):
        tr.add(brass_note(m - 12, B * 0.9, 0.6), i * B * 1.4, pan=0.1)
        tr.add(brass_note(m - 24, B * 0.9, 0.3), i * B * 1.4, pan=-0.1)
    for i in range(int(dur / B)):
        tr.add(snare(0.7 if i % 2 else 0.4), i * B * 0.7, pan=0.2)
        if i % 2 == 0:
            tr.add(kick(0.8), i * B * 1.4)
    return trim(reverb(tr.st(), 0.2, 1.5), dur)


def sn_choir(dur=2.8):
    tr = Track(dur)
    for k, m in enumerate([45, 52, 57, 61, 64, 69, 73, 76, 81]):
        tr.add(choir_note(m, dur, 0.3, att=0.25), 0, pan=-0.8 + 0.2 * k)
    return trim(reverb(tr.st(), 0.5, 3.5), dur)


# whale melody: (start s, duration s, midi note). Low, hummed, legato; glides only between notes.
WHALE_TUNE = [
    (0.0, 1.1, 50), (1.0, 0.7, 53), (1.6, 1.6, 57), (3.3, 0.6, 55), (3.8, 0.9, 53), (4.6, 1.5, 50),
    (6.6, 0.8, 57), (7.3, 0.7, 60), (7.9, 1.8, 62), (9.8, 0.6, 60), (10.3, 0.8, 57), (11.0, 1.6, 55),
    (13.0, 0.6, 53), (13.5, 0.6, 55), (14.0, 1.2, 57), (15.1, 0.5, 62), (15.5, 0.8, 60), (16.2, 2.6, 50),
]


def whale_song(dur, tune=WHALE_TUNE, gain=1.0):
    """A whale humming a melody: held notes, short scoops between them, gentle vibrato, vocal 'wah' timbre."""
    tr = Track(dur)
    # group notes into phrases (gap > 0.4 s starts a new breath)
    phrases, cur = [], []
    for nt in tune:
        if nt[0] >= dur:
            break
        if cur and nt[0] - (cur[-1][0] + cur[-1][1]) > 0.4:
            phrases.append(cur); cur = []
        cur.append(nt)
    if cur:
        phrases.append(cur)
    for ph_notes in phrases:
        p0 = ph_notes[0][0]
        p1 = min(dur, ph_notes[-1][0] + ph_notes[-1][1])
        n = int((p1 - p0) * SR)
        tt = np.arange(n) / SR
        f = np.zeros(n)
        amp = np.zeros(n)
        prev = mtof(ph_notes[0][2] - 3)  # each phrase scoops up into its first note
        for (st, d, m) in ph_notes:
            i0, i1 = int((st - p0) * SR), min(n, int((st - p0 + d) * SR))
            seg = np.arange(i1 - i0) / SR
            tgt = mtof(m)
            glide = np.clip(seg / 0.14, 0, 1)
            glide = glide * glide * (3 - 2 * glide)
            f[i0:i1] = prev + (tgt - prev) * glide
            swell = np.clip(seg / 0.12, 0, 1) * (0.85 + 0.15 * np.sin(np.pi * np.clip(seg / max(d, 0.01), 0, 1)))
            amp[i0:i1] = np.maximum(amp[i0:i1], swell)
            prev = tgt
        amp *= np.clip((p1 - p0 - tt) / 0.35, 0, 1)
        f *= 1 + 0.006 * np.sin(2 * np.pi * 4.3 * tt) * np.clip((tt - 0.3) / 0.5, 0, 1)
        ph = np.cumsum(f) / SR
        w = np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph) + 0.15 * np.sin(6 * np.pi * ph) + 0.06 * np.sin(8 * np.pi * ph)
        # 'wah': the mouth opens with the swell, brightening the tone
        dark, bright = lp(w, 450), lp(w, 1500)
        w = dark * (1 - 0.6 * amp) + bright * 0.6 * amp
        tr.add(w * amp * 0.75 * gain, p0, pan=-0.1)
    return tr


def sn_whale(dur=4.6):
    tr = whale_song(dur)
    for m in (50, 57, 62, 66):
        tr.add(strings_note(m, dur, 0.1, att=0.8, bright=0.4), 0, pan=0.3)
    return trim(reverb(tr.st(), 0.6, 4.5, 1800), dur)


def whale_full(dur=19.0):
    """End credits: the whale sings over a soft pad and distant surf."""
    tr = whale_song(dur, gain=1.0)
    for (t0, ch) in ((0, (50, 57, 62, 66)), (6.5, (47, 54, 59, 62)), (13, (43, 50, 55, 59))):
        for m in ch:
            tr.add(strings_note(m, 6.5, 0.09, att=1.5, rel=2.0, bright=0.4), t0, pan=0.25)
    t = t_arr(dur)
    surf = lp(rng.standard_normal(len(t)), 600) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t)) * 0.05
    tr.add(surf, 0, pan=0)
    return trim(reverb(tr.st(), 0.55, 4.5, 1800), dur, fade=3.0)


def sn_synth(dur=2.4):
    tr = Track(dur)
    seq = [57, 60, 64, 69, 64, 60] * 4
    for i, m in enumerate(seq):
        s = saw(mtof(m), t_arr(0.12)) * adsr(int(0.12 * SR), 0.002, 0.05, 0.5, 0.05)
        tr.add(lp(s, 3000) * 0.3, i * 0.1, pan=(-0.4 if i % 2 else 0.4))
    for i in range(int(dur / 0.4)):
        tr.add(kick(0.7), i * 0.4)
    return trim(reverb(tr.st(), 0.25), dur)


def sn_odd(dur=3.2):
    """'Time signature humans cannot perceive' — interlocking 13:7:5 pulses."""
    tr = Track(dur)
    for period, base, pan in ((dur / 13, 76, -0.6), (dur / 7, 64, 0.5), (dur / 5, 52, 0)):
        k = 0
        while k * period < dur:
            m = base + int(rng.integers(-5, 7))
            tr.add(piano_note(m, 0.4, 0.5), k * period, pan=pan)
            tr.add(hp(rng.standard_normal(600), 4000) * 0.15, k * period + period / 3, pan=-pan)
            k += 1
    return trim(reverb(tr.st(), 0.2, 1.0), dur)


def sn_kazoo(dur=2.4):
    tr = Track(dur)
    for i, m in enumerate([72, 74, 76, 72, 79, 77]):
        s = saw(mtof(m), t_arr(0.35)) + 0.3 * rng.standard_normal(int(0.35 * SR))
        s = bp(s, 400, 2200) * adsr(len(s), 0.02, 0.05, 0.9, 0.05)
        tr.add(s * 0.35, i * 0.36, pan=0.2)
    th = lp(rng.standard_normal(int(2.0 * SR)), 160) * np.exp(-t_arr(2.0) * 1.5) * 3
    tr.add(th, 0.5, pan=-0.2)
    return trim(reverb(tr.st(), 0.3), dur)


# --------------------------------------------------------------- ambience/sfx
def ambience(dur):
    t = t_arr(dur)
    hum = 0.05 * np.sin(2 * np.pi * 55 * t) + 0.03 * np.sin(2 * np.pi * 110.3 * t) + 0.012 * np.sin(2 * np.pi * 165.2 * t)
    hum *= 1 + 0.15 * np.sin(2 * np.pi * 0.11 * t)
    air = lp(rng.standard_normal(len(t)), 250) * 0.12
    L = hum + air
    R = hum + lp(rng.standard_normal(len(t)), 250) * 0.12
    return np.vstack([L, R]) * 0.5


def sfx_door(dur=0.7):
    t = t_arr(dur)
    n = rng.standard_normal(len(t))
    lo = bp(n, 300, 1200) * 0.6 + bp(n, 1500, 5000) * 0.25
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    s = lo * env
    return np.vstack([s, s]) * 0.6


def sfx_blip(f=1200, dur=0.12, up=True):
    t = t_arr(dur)
    ff = f * (1 + (0.6 if up else -0.4) * t / dur)
    s = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 20) * 0.25
    return np.vstack([s, s])


def sfx_compute(dur=1.1):
    tr = Track(dur)
    k = 0
    tt = 0.0
    while tt < dur - 0.04:
        f = 1800 + 1600 * rng.random()
        tr.add(np.sin(2 * np.pi * f * t_arr(0.025)) * 0.08, tt, pan=rng.uniform(-0.6, 0.6))
        tt += 0.03 + 0.03 * rng.random()
        k += 1
    tr.add(sfx_blip(2400, 0.2)[0] * 1.2, dur - 0.2)
    return trim(tr.st(), dur + 0.2)


def sfx_whoosh(dur=1.2, rev=False):
    t = t_arr(dur)
    n = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = 8
    for i in range(seg):
        a, b = i * len(t) // seg, (i + 1) * len(t) // seg
        fc = 300 + 5000 * (i / seg if not rev else 1 - i / seg)
        out[a:b] = bp(n[a:b], fc * 0.6, min(fc * 1.6, 20000))
    env = (t / dur) ** 2 if not rev else np.exp(-t * 4)
    s = out * env * 0.7
    return np.vstack([s, np.roll(s, 200)])


def sfx_dim(dur=2.0):
    t = t_arr(dur)
    ph = np.cumsum(220 * (1 - 0.5 * t / dur)) / SR
    s = np.sin(2 * np.pi * ph) * np.exp(-t * 1.5) * 0.15
    return np.vstack([s, s])


def sfx_holo(dur=0.5):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for f in (880, 1320, 1760):
        s += np.sin(2 * np.pi * f * (1 + 0.3 * t) * t) * np.exp(-t * 7) * 0.08
    s += bp(rng.standard_normal(len(t)), 3000, 8000) * np.exp(-t * 12) * 0.05
    return np.vstack([s, np.roll(s, 300)])


def sfx_gasp(dur=0.5):
    t = t_arr(dur)
    n = bp(rng.standard_normal(len(t)), 900, 4500)
    env = np.clip(t / 0.08, 0, 1) * np.exp(-np.clip(t - 0.12, 0, None) * 9)
    s = n * env * 0.35
    return np.vstack([s, s])


def sfx_footsteps(n=6, gap=0.22):
    tr = Track(n * gap + 0.4)
    for i in range(n):
        s = lp(rng.standard_normal(int(0.08 * SR)), 900) * np.exp(-t_arr(0.08) * 50) * 0.5
        tr.add(s, i * gap, pan=0.2 + 0.1 * i)
    return tr.st()


def sfx_clink():
    t = t_arr(0.6)
    s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((2100, 9), (3350, 12), (5100, 15))) * 0.08
    return np.vstack([s, s])


def sfx_typing(dur, density=11.0, seed=1):
    """Soft keyboard clatter."""
    r = np.random.default_rng(seed)
    tr = Track(dur)
    tt = 0.0
    while tt < dur - 0.05:
        n = int(0.03 * SR)
        click = bp(r.standard_normal(n), 1800, 7000) * np.exp(-t_arr(0.03) * 160)
        click += np.sin(2 * np.pi * (300 + 200 * r.random()) * t_arr(0.03)) * np.exp(-t_arr(0.03) * 120) * 0.4
        tr.add(click * (0.08 + 0.06 * r.random()), tt, pan=r.uniform(-0.3, 0.3))
        tt += r.exponential(1.0 / density) + 0.02
        if r.random() < 0.05:
            tt += 0.35
    return trim(tr.st(), dur, 0.02)


def android_chirp(text, base=900.0, seed=0):
    """Fast melodic chirps with a speech-like rhythm. Returns (stereo, envelope mono)."""
    r = np.random.default_rng(seed)
    words = text.split()
    tr = Track(0.06 * len(text) + 1)
    tt = 0.0
    for w in words:
        for s in range(max(1, (len(w) + 1) // 2)):
            d = 0.055 + 0.05 * r.random()
            t = t_arr(d)
            f0 = base * 2 ** (r.uniform(-0.5, 0.6))
            f1 = f0 * 2 ** r.uniform(-0.4, 0.4)
            f = np.linspace(f0, f1, len(t))
            ph = np.cumsum(f) / SR
            tone = np.sin(2 * np.pi * ph) + 0.3 * np.sign(np.sin(2 * np.pi * ph * 2)) * 0.3
            tone *= np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6
            tr.add(tone * 0.18, tt, pan=0)
            tt += d + 0.012
        tt += 0.06
    st = trim(tr.st(), tt + 0.1, 0.02)
    st = reverb(st, 0.12, 0.6)
    return st


def sfx_tap():
    """Fingertip-to-device data transfer: rising sparkle + confirm chime."""
    tr = Track(1.2)
    for i in range(10):
        tr.add(np.sin(2 * np.pi * (900 + 160 * i) * t_arr(0.05)) * np.exp(-t_arr(0.05) * 40) * 0.12, i * 0.035, pan=-0.3 + 0.06 * i)
    for k, f in enumerate((1319, 1760)):
        tr.add(np.sin(2 * np.pi * f * t_arr(0.6)) * np.exp(-t_arr(0.6) * 6) * 0.16, 0.38 + k * 0.09, pan=0)
    return trim(reverb(tr.st(), 0.25, 1.2), 1.2)


def sfx_birds(dur=12.0, seed=3):
    """Songbirds: quick chirps and trills scattered over time."""
    r = np.random.default_rng(seed)
    tr = Track(dur)
    tt = 0.3
    while tt < dur - 0.5:
        n = int(r.integers(2, 6))
        f0 = r.uniform(2800, 4800)
        pan = r.uniform(-0.8, 0.8)
        for k in range(n):
            d = r.uniform(0.04, 0.09)
            t = t_arr(d)
            f = f0 * (1 + r.uniform(-0.25, 0.35) * t / d) + 300 * np.sin(2 * np.pi * 60 * t)
            ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
            tr.add(ch * 0.12, tt + k * (d + 0.03), pan=pan)
        tt += r.uniform(0.35, 1.3)
    return reverb(tr.st(), 0.25, 1.6)[:, :int(dur * SR)]


def sfx_cough():
    """An airy 'ah-hem' throat-clear: breathy 'ah', then a short voiced 'hem' that closes to a hummed 'm'."""
    def voiced(dur, f0, f1, formants, breath):
        t = t_arr(dur)
        f = np.linspace(f0, f1, len(t))
        ph = np.cumsum(f) / SR
        src = (2 * (ph % 1.0) - 1) * 0.6 + rng.standard_normal(len(t)) * breath
        out = sum(g * bp(src, fc * 0.8, fc * 1.25) for fc, g in formants)
        return out
    tr = Track(0.9)
    # 'ah': mostly breath, a little voice
    ah = voiced(0.22, 230, 210, ((750, 1.0), (1250, 0.6), (2600, 0.25)), 1.4)
    ah *= np.clip(t_arr(0.22) / 0.02, 0, 1) * np.exp(-t_arr(0.22) * 9)
    tr.add(ah * 0.55, 0.0)
    # 'h' + 'e' + 'm'
    h = bp(rng.standard_normal(int(0.05 * SR)), 900, 3500) * np.linspace(0.2, 0.6, int(0.05 * SR))
    tr.add(h * 0.25, 0.27)
    e = voiced(0.11, 205, 190, ((520, 1.0), (1800, 0.5), (2500, 0.2)), 0.35)
    e *= np.clip(t_arr(0.11) / 0.015, 0, 1)
    tr.add(e * 0.5, 0.32)
    m = voiced(0.2, 190, 165, ((250, 1.0), (2200, 0.05)), 0.05)
    m *= np.linspace(1, 0, len(m)) ** 1.5
    tr.add(m * 0.55, 0.43)
    return trim(reverb(tr.st(), 0.12, 0.4), 0.9)
