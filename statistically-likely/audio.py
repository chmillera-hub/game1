"""Synthesizes the score for Statistically Likely from the film's own cues.

    python3 audio.py build/events.json build/soundtrack.wav

Every thread that forms becomes a chime, every thread that snaps a crack;
the chords follow the acts. Pure numpy, no samples.
"""
import json
import sys
import wave

import numpy as np

SR = 48000
events_path, out_path = sys.argv[1], sys.argv[2]
data = json.load(open(events_path))
T, EV = data['T'], data['events']
N = int((T['END'] + 0.5) * SR)
FREEZE = T['freeze']
rng = np.random.default_rng(1026)

bus_a = np.zeros((2, N))  # everything up to the freeze, cut dead at the freeze
bus_b = np.zeros((2, N))  # everything after the silence
chime_bus = np.zeros((2, N))  # thread chimes, levelled on their own before mixing


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(n):
    return np.arange(n) / SR


def add(sig, t, gain=1.0, pan=0.5, bus=None):
    if bus is None:
        bus = bus_b if t >= FREEZE + 0.3 else bus_a
    i0 = int(round(t * SR))
    if sig.ndim == 1:
        sig = np.vstack([sig * np.cos(pan * np.pi / 2), sig * np.sin(pan * np.pi / 2)]) * np.sqrt(2)
    if i0 < 0:
        sig, i0 = sig[:, -i0:], 0
    n = min(sig.shape[1], N - i0)
    if n > 0:
        bus[:, i0:i0 + n] += sig[:, :n] * gain


def shape(x, lo=None, hi=None, order=4):
    """Gentle FFT band-limit."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / f) ** order)
    if hi:
        m *= 1 / (1 + (f / hi) ** order)
    return np.fft.irfft(X * m, len(x))


def env_ar(n, attack, release):
    t = tt(n)
    dur = n / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.clip((dur - t) / max(release, 1e-4), 0, 1)
    return np.sin(a * np.pi / 2) ** 2 * np.sin(r * np.pi / 2) ** 2


# ---------- instruments ----------
def pad_note(f, dur, attack=2.2, release=2.6, bright=0.22, seed=0):
    n = int(dur * SR)
    t = tt(n)
    r = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for k, cents in enumerate((-7, 0, 6)):
        fd = f * 2 ** (cents / 1200)
        ph = r.uniform(0, 2 * np.pi)
        s = np.sin(2 * np.pi * fd * t + ph) + bright * np.sin(4 * np.pi * fd * t + ph * 1.3) \
            + bright * 0.3 * np.sin(6 * np.pi * fd * t + ph * 0.7)
        pan = (0.25, 0.5, 0.75)[k]
        out[0] += s * np.cos(pan * np.pi / 2)
        out[1] += s * np.sin(pan * np.pi / 2)
    trem = 1 + 0.13 * np.sin(2 * np.pi * r.uniform(0.06, 0.17) * t + r.uniform(0, 6))
    return out * env_ar(n, attack, release) * trem / 3


def bell(f, decay=1.4, bright=1.0, n_sec=None):
    n_sec = n_sec or decay * 4
    n = int(n_sec * SR)
    t = tt(n)
    s = np.zeros(n)
    for ratio, amp, dk in ((1, 1, 1), (2.0, 0.32, 0.6), (2.76, 0.2 * bright, 0.45), (5.4, 0.1 * bright, 0.25), (8.93, 0.04 * bright, 0.14)):
        s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (decay * dk))
    return s * np.clip(t / 0.003, 0, 1)


def sweep(f0, f1, dur, curve='exp'):
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    f = f0 * (f1 / f0) ** k if curve == 'exp' else f0 + (f1 - f0) * k
    return np.sin(np.cumsum(2 * np.pi * f / SR))


def noise(n_sec):
    return rng.standard_normal(int(n_sec * SR))


def snap_sound():
    n = int(0.1 * SR)
    t = tt(n)
    crack = shape(rng.standard_normal(n), lo=1800) * np.exp(-t / 0.01)
    f = 2600 * np.exp(-t / 0.018) + 260
    ping = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.035)
    return 0.7 * crack + 0.5 * ping


def thump(f0=64):
    n = int(0.4 * SR)
    t = tt(n)
    f = f0 * np.exp(-t / 0.09) + 34
    return np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / 0.12) * np.clip(t / 0.004, 0, 1)


def click():
    n = int(0.008 * SR)
    t = tt(n)
    return shape(rng.standard_normal(n), lo=2500) * np.exp(-t / 0.0014) + 0.3 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t / 0.002)


def voice_burst(f0, dur, vowel):
    """A shouted syllable: a buzzy glottal source pushed through vowel formants."""
    n = int(dur * SR)
    k = np.linspace(0, 1, n)
    f = f0 * (1 + 0.25 * np.sin(np.pi * k)) * (1 + 0.02 * np.sin(2 * np.pi * 6 * k * dur))
    ph = np.cumsum(2 * np.pi * f / SR)
    src = 2 * ((ph / (2 * np.pi)) % 1) - 1
    src += 0.25 * rng.standard_normal(n)
    X = np.fft.rfft(src)
    fr = np.fft.rfftfreq(n, 1 / SR)
    m = sum(a * np.exp(-0.5 * ((fr - fc) / bw) ** 2) for fc, bw, a in vowel)
    return np.fft.irfft(X * m, n) * env_ar(n, 0.03, 0.12)


def reverb(x, seconds=3.4, decay=0.78, wet=0.3, seed=3):
    r = np.random.default_rng(seed)
    n_ir = int(seconds * SR)
    t = tt(n_ir)
    out = np.zeros_like(x)
    size = 1 << int(np.ceil(np.log2(x.shape[1] + n_ir)))
    for ch in range(2):
        ir = r.standard_normal(n_ir) * np.exp(-t / decay)
        ir = shape(ir, lo=120, hi=5200, order=2)
        for d, a in ((0.013, 0.5), (0.029, 0.35), (0.047, 0.25)):
            ir[int((d + 0.004 * ch) * SR)] += a * 8
        ir /= np.sqrt(np.sum(ir ** 2))
        y = np.fft.irfft(np.fft.rfft(x[ch], size) * np.fft.rfft(ir, size), size)[:x.shape[1]]
        out[ch] = x[ch] * (1 - wet * 0.5) + y * wet
    return out


PENTA = [62, 64, 66, 69, 71]


def penta(i, octave):
    return PENTA[i % 5] + 12 * (octave + i // 5)


# ---------- the score ----------
CHORDS = [
    (0.3, 7.7, [38, 45, 54, 64], 0.45),                  # title: D add9
    (7.4, 22.3, [38, 45, 54, 61, 64], 0.8),              # arrival: Dmaj9
    (22.0, T['snap'], [35, 42, 50, 61], 0.7),            # the comment: Bm add9
    (T['snap'], 43.8, [34, 41, 50, 64], 0.75),           # the wall: Bb, with a tritone sitting on it
    (43.6, 55.2, [38, 57, 64, 83], 0.55),                # multiply: empty fifths, high and alone
    (55.0, 86.2, [40, 47], 0.42),                        # the mirror: open drone
    (86.0, 91.2, [41, 48, 57, 64], 0.65),                # a family: Fmaj7
    (100.4, 110.8, [50, 57, 64, 66], 0.6),               # the flame: D add9
    (110.4, 115.0, [35, 42, 50, 57], 0.7),               # Bm7
    (114.8, 119.4, [31, 38, 47, 54], 0.7),               # Gmaj7
    (119.0, 124.6, [33, 40, 47, 50], 0.62),              # Asus4: waiting
    (124.4, 127.7, [38, 45, 54, 57, 64], 0.85),          # doors: D
    (127.5, 130.7, [37, 45, 52, 57, 61], 0.85),          # A/C#
    (130.5, 133.7, [35, 42, 50, 57, 62], 0.85),          # Bm7
    (133.5, 136.4, [31, 38, 47, 54, 57], 0.85),          # Gmaj9
    (136.2, 148.0, [38, 45, 54, 57, 64, 66, 69], 0.95),  # to need each other: D, in full
]
for ci, (t0, t1, notes, g) in enumerate(CHORDS):
    dur = t1 - t0 + 2.4
    for ni, m in enumerate(notes):
        bright = 0.12 if m > 70 else 0.24
        level = 0.11 * g / np.sqrt(len(notes)) * (0.55 if m > 78 else 1)
        add(pad_note(midi(m), dur, attack=2.0, release=2.6, bright=bright, seed=ci * 31 + ni), t0, level,
            bus=bus_b if t0 >= FREEZE + 0.3 else bus_a)

# the mob: a dissonant cluster that swells until the freeze
for ni, m in enumerate([41, 42, 48, 49, 54]):
    n = int((FREEZE - T['mobStart'] + 3) * SR)
    s = pad_note(midi(m), n / SR, attack=0.5, release=0.5, bright=0.5, seed=900 + ni)
    s *= np.clip(tt(n) / (FREEZE - T['mobStart']), 0, 1) ** 2
    add(s, T['mobStart'], 0.1, bus=bus_a)

# heartbeat behind the wall
beat = 60 / 58
tb = T['ringStart'] + 0.3
while tb < 43.4:
    fade = min(1, (tb - T['ringStart']) / 3) * min(1, (43.6 - tb) / 2)
    add(thump(66), tb, 0.30 * fade, bus=bus_a)
    add(thump(58), tb + 0.27, 0.18 * fade, bus=bus_a)
    tb += beat

# crowd murmur
n = int((FREEZE - T['mobStart'] + 1) * SR)
t_m = tt(n)
lfo = sum(np.clip(np.sin(2 * np.pi * rng.uniform(2.5, 8) * t_m + rng.uniform(0, 6)), 0, None) for _ in range(14)) / 14
grow = np.clip(t_m / (FREEZE - T['mobStart']), 0, 1) ** 1.6
for ch in range(2):
    murmur = shape(rng.standard_normal(n), lo=260, hi=1900, order=2) * (0.35 + lfo) * grow
    sig = np.zeros((2, n))
    sig[ch] = murmur
    add(sig, T['mobStart'], 0.4, bus=bus_a)
riser = sweep(110, 900, FREEZE - 93) * np.linspace(0, 1, int((FREEZE - 93) * SR)) ** 2
add(riser, 93, 0.07, bus=bus_a)

# ---------- cues ----------
chimes = sorted([e for e in EV if e['type'] == 'chime'], key=lambda e: e['t'])
chime_t = np.array([e['t'] for e in chimes])
last, last_p = -1, -1
for e in chimes:
    t = e['t']
    sorting = T['sortStart'] <= t < 100
    if e.get('p'):
        if t - last_p < 0.12:
            continue
        last_p = t
        add(bell(midi(penta(int(t * 7) % 5, 0)), decay=1.6), t, 0.06, e['pan'], bus=chime_bus)
        continue
    if t - last < 0.07:
        continue
    last = t
    density = np.sum(np.abs(chime_t - t) < 0.5)
    g = 0.04 / np.sqrt(max(1, density / 3)) * (0.5 if sorting else 1)
    idx = int(rng.integers(0, 10))
    octave = 0 if sorting else 1 if t < 100 else int(rng.integers(0, 2)) + 1
    add(bell(midi(penta(idx, octave) - 12), decay=0.9), t, g, e['pan'], bus=chime_bus)

# level the chime bus so a burst of new threads shimmers instead of clipping
win_n = int(0.4 * SR)
power = np.concatenate([[0], np.cumsum((chime_bus[0] ** 2 + chime_bus[1] ** 2) / 2)])
rms = np.sqrt(np.maximum((power[win_n:] - power[:-win_n]) / win_n, 0))
rms = np.concatenate([rms, np.full(N - len(rms), rms[-1])])
level = np.minimum(1, 0.018 / (rms + 1e-9))
csum = np.concatenate([[0], np.cumsum(level)])
idx = np.clip(np.arange(N) - win_n // 2, 0, N - win_n)
level = (csum[idx + win_n] - csum[idx]) / win_n
chime_bus *= level
i_cut = int(FREEZE * SR)
bus_a[:, :i_cut] += chime_bus[:, :i_cut]
bus_b[:, i_cut:] += chime_bus[:, i_cut:]

snaps = sorted([e for e in EV if e['type'] == 'snap'], key=lambda e: e['t'])
snap_t = np.array([e['t'] for e in snaps]) if snaps else np.array([0.0])
for e in snaps:
    density = np.sum(np.abs(snap_t - e['t']) < 0.3)
    add(snap_sound(), e['t'], 0.08 / np.sqrt(max(1, density / 2)), e['pan'])

for e in EV:
    t, kind = e['t'], e['type']
    if kind == 'key':
        add(click(), t, 0.02 * rng.uniform(0.7, 1.3), rng.uniform(0.44, 0.56))
    elif kind == 'title':
        add(bell(midi(50), decay=2.5, bright=0.5), t, 0.09)
        add(bell(midi(74), decay=2.0, bright=0.3), t + 0.4, 0.03, 0.6)
    elif kind == 'bigsnap':
        add(sweep(72, 30, 1.6) * np.exp(-tt(int(1.6 * SR)) / 0.55), t, 0.3)
        add(snap_sound(), t, 0.16)
        add(shape(noise(1.2), lo=200, hi=3000, order=2) * np.exp(-tt(int(1.2 * SR)) / 0.25), t, 0.05)
    elif kind == 'ring':
        n = int((T['ringDur'] + 1.8) * SR)
        e_ring = env_ar(n, T['ringDur'], 1.6)
        glass = (np.sin(2 * np.pi * midi(81) * tt(n)) + 0.6 * np.sin(2 * np.pi * midi(88) * tt(n))) * e_ring
        add(glass, t, 0.03, 0.4)
        add(shape(noise(n / SR), lo=1500, hi=6000, order=2) * e_ring, t, 0.02, 0.6)
    elif kind == 'ghost':
        n = int(0.25 * SR)
        add(sweep(240, 170, 0.25) * np.exp(-tt(n) / 0.05), t, 0.16, 0.42)
        add(bell(midi(48), decay=1.2, bright=0.2), t + 0.02, 0.05, 0.42)
    elif kind == 'zoom':
        n = int(8 * SR)
        swell = shape(noise(8), lo=50, hi=380, order=2) * env_ar(n, 3, 5)
        add(swell, t, 0.16)
        add(np.sin(2 * np.pi * 38 * tt(n)) * env_ar(n, 3, 5), t, 0.08)
    elif kind == 'mirror':
        n = int(4 * SR)
        sh = (np.sin(2 * np.pi * 1760 * tt(n)) + 0.6 * np.sin(2 * np.pi * 2637 * tt(n))) * env_ar(n, 1.2, 2.6) \
            * (1 + 0.3 * np.sin(2 * np.pi * 5 * tt(n)))
        add(sh, t, 0.018)
    elif kind == 'pair':
        note = (69, 67, 64, 62, 69)[e['k']]
        n = int(3.6 * SR)
        add(np.sin(2 * np.pi * midi(note) * tt(n)) * env_ar(n, 0.5, 3.0), t, 0.065, 0.38)
    elif kind == 'flip':
        note = (69, 67, 64, 62, 69)[e['k']] + 6
        n = int(0.6 * SR)
        add(shape(noise(0.6), lo=900, hi=5500, order=2) * env_ar(n, 0.3, 0.3), t - 0.3, 0.05 if e['k'] < 4 else 0.08, 0.62)
        n2 = int(3.0 * SR)
        add(np.sin(2 * np.pi * midi(note) * tt(n2)) * env_ar(n2, 0.05, 2.6), t, 0.055, 0.62)
    elif kind == 'glitch':
        n = int(0.95 * SR)
        g = np.zeros(n)
        pos = 0
        while pos < n:
            seg = int(rng.uniform(0.02, 0.06) * SR)
            if rng.random() < 0.65:
                f = rng.uniform(180, 1200)
                sq = np.sign(np.sin(2 * np.pi * f * tt(seg)))
                g[pos:pos + seg] = (sq + 0.6 * rng.standard_normal(seg))[:max(0, min(seg, n - pos))]
            pos += seg
        g = np.round(g * 4) / 4
        add(shape(g, lo=150, hi=7000), t, 0.05)
    elif kind == 'collapse':
        add(sweep(220, 3200, 0.4) * env_ar(int(0.4 * SR), 0.3, 0.05), t - 0.2, 0.035)
    elif kind == 'shout':
        vowel = [((700, 90, 1), (1220, 110, 0.7), (2600, 160, 0.35)), ((400, 80, 1), (2000, 120, 0.6), (2550, 150, 0.4)),
                 ((550, 90, 1), (900, 100, 0.8), (2400, 150, 0.3))][int(rng.integers(0, 3))]
        f0 = rng.uniform(140, 290)
        for s in range(int(rng.integers(2, 4))):
            add(voice_burst(f0 * rng.uniform(0.9, 1.15), rng.uniform(0.12, 0.22), vowel), t + s * rng.uniform(0.13, 0.2), 0.075, e['pan'], bus=bus_a)
    elif kind == 'flame':
        n = int(0.7 * SR)
        add(shape(noise(0.7), hi=700, order=2) * env_ar(n, 0.05, 0.6), t, 0.06)
        add(np.sin(2 * np.pi * 90 * tt(n)) * env_ar(n, 0.05, 0.6), t, 0.05)
    elif kind == 'spark':
        n = int(0.55 * SR)
        add(sweep(700, 1500, 0.55) * np.linspace(0.2, 1, n) ** 2, t, 0.02, 0.5)
    elif kind == 'ignite':
        add(bell(midi((74, 78, 81, 83, 86, 88)[e['i']]), decay=1.8, bright=0.7), t, 0.065, e['pan'])
        n = int(0.4 * SR)
        add(shape(noise(0.4), lo=300, hi=2500, order=2) * env_ar(n, 0.02, 0.35), t, 0.04, e['pan'])
    elif kind == 'doors':
        n = int(1.8 * SR)
        rev = shape(noise(1.8), lo=2500, order=2) * np.linspace(0, 1, n) ** 3
        add(rev, t - 1.8, 0.07)
        add(sweep(60, 34, 2.0) * np.exp(-tt(int(2 * SR)) / 0.8), t, 0.14)
        add(bell(midi(74), decay=2.5, bright=0.5), t, 0.06, 0.4)
        add(bell(midi(81), decay=2.5, bright=0.5), t + 0.09, 0.05, 0.6)
    elif kind == 'final':
        for s, m in enumerate((74, 78, 81, 86)):
            add(bell(midi(m), decay=3.0, bright=0.6), t + s * 0.07, 0.065, 0.3 + s * 0.13)
    elif kind == 'endtitle':
        add(bell(midi(81), decay=3.0, bright=0.4), t, 0.05, 0.55)

tiny = sorted([e for e in EV if e['type'] == 'tiny'], key=lambda e: e['t'])
last = -1
for e in tiny:
    if e['t'] - last < 0.03:
        continue
    last = e['t']
    add(bell(midi(penta(int(rng.integers(0, 10)), 2)), decay=0.8, bright=0.4), e['t'], 0.014, e['pan'])

# after the freeze: one low bell in the silence
add(bell(midi(50), decay=3.6, bright=0.6), FREEZE + 0.7, 0.035, bus=bus_b)

# ---------- mix ----------
print('reverb...')
wet_a = reverb(bus_a, wet=0.32)
gate = np.ones(N)
i_f = int(FREEZE * SR)
ramp = int(0.012 * SR)
gate[i_f:i_f + ramp] = np.linspace(1, 0, ramp)
gate[i_f + ramp:] = 0
wet_a *= gate
wet_b = reverb(bus_b, wet=0.32, seed=4)
mix = wet_a + wet_b

for ch in range(2):
    mix[ch] = shape(mix[ch], lo=28, order=2)
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(1.4 * mix) / np.tanh(1.4)
tail = int(1.2 * SR)
mix[:, -tail:] *= np.linspace(1, 0, tail)
mix *= 0.89 / (np.max(np.abs(mix)) + 1e-9)

pcm = np.clip(mix.T * 32767 + rng.uniform(-0.5, 0.5, mix.T.shape), -32768, 32767).astype('<i2')
with wave.open(out_path, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out_path, f'{N / SR:.1f}s')
