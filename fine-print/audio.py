"""Score and sound for Fine Print, built from the film's own cues.

    python3 audio.py build/events.json build/soundtrack.wav [build/voices.wav]

Cold drones that follow the five sections, a heartbeat under the force,
and a sound for every contact the picture shows: grips, cuffs, a cell door,
tally marks, a scan, a crack, a meter climbing. Everything stops at the
freeze. With the voice stem, the music ducks under whoever is speaking.
"""
import json
import sys
import wave

import numpy as np

SR = 48000
events_path, out_path = sys.argv[1], sys.argv[2]
voice_path = sys.argv[3] if len(sys.argv) > 3 else None
data = json.load(open(events_path))
T, EV = data['T'], data['events']
LINES = {c['id']: c for c in data['cues']['voice']}
N = int((T['END'] + 0.5) * SR)
DARK = T['dark']
rng = np.random.default_rng(301)

bus_a = np.zeros((2, N))  # everything until the freeze
bus_b = np.zeros((2, N))  # after it


def L(i):
    return LINES[i]['t0']


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(n):
    return np.arange(n) / SR


def add(sig, t, gain=1.0, pan=0.5, bus=None):
    if bus is None:
        bus = bus_b if t >= DARK else bus_a
    i0 = int(round(t * SR))
    if sig.ndim == 1:
        sig = np.vstack([sig * np.cos(pan * np.pi / 2), sig * np.sin(pan * np.pi / 2)]) * np.sqrt(2)
    if i0 < 0:
        sig, i0 = sig[:, -i0:], 0
    n = min(sig.shape[1], N - i0)
    if n > 0:
        bus[:, i0:i0 + n] += sig[:, :n] * gain


def shape(x, lo=None, hi=None, order=4):
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


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def sweep(f0, f1, dur):
    n = int(dur * SR)
    f = f0 * (f1 / f0) ** np.linspace(0, 1, n)
    return np.sin(np.cumsum(2 * np.pi * f / SR))


def drone(notes, dur, attack=3.0, release=3.0, bright=0.15, seed=0):
    n = int(dur * SR)
    t = tt(n)
    r = np.random.default_rng(seed)
    out = np.zeros((2, n))
    for m in notes:
        for k, cents in enumerate((-6, 0, 5)):
            fd = midi(m) * 2 ** (cents / 1200)
            ph = r.uniform(0, 6.3)
            s = np.sin(2 * np.pi * fd * t + ph) + bright * np.sin(4 * np.pi * fd * t + ph)
            pan = (0.3, 0.5, 0.7)[k]
            out[0] += s * np.cos(pan * np.pi / 2)
            out[1] += s * np.sin(pan * np.pi / 2)
    out *= (1 + 0.12 * np.sin(2 * np.pi * r.uniform(0.05, 0.12) * t))
    return out * env_ar(n, attack, release) / (3 * np.sqrt(len(notes)))


def bell(f, decay=1.5, bright=0.6):
    n = int(decay * 4 * SR)
    t = tt(n)
    s = np.zeros(n)
    for ratio, amp, dk in ((1, 1, 1), (2.0, 0.3, 0.6), (2.76, 0.18 * bright, 0.45), (5.4, 0.08 * bright, 0.25)):
        s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (decay * dk))
    return s * np.clip(t / 0.003, 0, 1)


def thud(f0=70, decay=0.14, click=0.3):
    n = int(0.5 * SR)
    t = tt(n)
    f = f0 * np.exp(-t / 0.08) + f0 * 0.5
    body = np.sin(np.cumsum(2 * np.pi * f / SR)) * np.exp(-t / decay)
    hit = shape(rng.standard_normal(n), lo=200, hi=2500, order=2) * np.exp(-t / 0.012)
    return body + click * hit


def metal(f, decay=0.35):
    n = int(decay * 5 * SR)
    t = tt(n)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (decay * d)) for r, a, d in ((1, 1, 1), (2.32, 0.6, 0.7), (4.25, 0.4, 0.5), (6.8, 0.25, 0.3)))
    tick = shape(rng.standard_normal(n), lo=3000, order=2) * np.exp(-t / 0.004)
    return s * 0.5 + tick


def reverb(x, seconds=3.0, decay=0.7, wet=0.3, seed=3):
    r = np.random.default_rng(seed)
    n_ir = int(seconds * SR)
    t = tt(n_ir)
    out = np.zeros_like(x)
    size = 1 << int(np.ceil(np.log2(x.shape[1] + n_ir)))
    for ch in range(2):
        ir = r.standard_normal(n_ir) * np.exp(-t / decay)
        ir = shape(ir, lo=120, hi=5000, order=2)
        ir /= np.sqrt(np.sum(ir ** 2))
        y = np.fft.irfft(np.fft.rfft(x[ch], size) * np.fft.rfft(ir, size), size)[:x.shape[1]]
        out[ch] = x[ch] * (1 - wet * 0.5) + y * wet
    return out


# ---------- the drones, section by section ----------
SCORE = [
    (0.2, T['act1'] + 1.0, [33, 40], 0.55),                              # title: an open fifth, low
    (T['act1'], L('cell') + 0.6, [33, 40, 47, 52], 0.7),                 # contact: A sus2, cold
    (L('cell') + 0.6, T['act2'] + 1.0, [33, 34, 40], 0.75),              # the cell: A against B-flat
    (T['act2'], L('solitary'), [38, 76, 77], 0.5),                       # search: D low, two thin tones high
    (L('solitary'), T['act3'] + 1.0, [26, 33], 0.6),                     # solitary: almost nothing
    (T['act3'], L('later'), [36, 42], 0.65),                             # misconduct: C against F-sharp
    (L('later'), T['act4'] + 1.0, [36, 88], 0.4),                        # accountability, receding
    (T['act4'], T['act5'] + 1.0, [33, 39, 40], 0.75),                    # force
    (T['act5'], L('killed'), [38, 45, 51], 0.6),                         # perception: D, A, E-flat
    (L('killed'), DARK + 0.05, [38, 45, 51, 86], 0.7),                   # and the last thing
    (T['coda'] + 0.5, T['END'], [33, 40, 47], 0.55),                     # coda: open, unresolved
]
for i, (t0, t1, notes, g) in enumerate(SCORE):
    add(drone(notes, t1 - t0 + 2.5, seed=i), t0, 0.14 * g, bus=bus_b if t0 >= DARK else bus_a)

# a heartbeat under the force, faster as it climbs
tb, end = T['act4'] + 0.8, LINES['worse']['t0'] + 1.2
while tb < end:
    k = (tb - T['act4']) / (end - T['act4'])
    add(thud(60, 0.12, 0.05), tb, 0.3 * min(1, (tb - T['act4']) / 3))
    add(thud(52, 0.1, 0.03), tb + 0.26, 0.18 * min(1, (tb - T['act4']) / 3))
    tb += 60 / (68 + 52 * k)

# fluorescent hum while exposed
s0, s1 = L('strip') + 0.4, L('solitary') + 0.8
n = int((s1 - s0) * SR)
hum = sum(np.sin(2 * np.pi * 60 * h * tt(n)) / h for h in (1, 2, 3, 5, 7)) * (1 + 0.3 * np.sin(2 * np.pi * 0.7 * tt(n)))
add(shape(hum, lo=80, hi=1200) * env_ar(n, 0.8, 0.8), s0, 0.025)

# the last seconds before the freeze: a slow rise
r0 = L('away') + 0.5
n = int((DARK - r0) * SR)
add(sweep(90, 320, DARK - r0) * np.linspace(0, 1, n) ** 2, r0, 0.05)
add(shape(noise(DARK - r0), lo=800, hi=6000, order=2) * np.linspace(0, 1, n) ** 3, r0, 0.03)

# ---------- cues ----------
last_tally = -1
for e in EV:
    t, k = e['t'], e['type']
    pan = e.get('pan', 0.5)
    if k == 'key':
        if e.get('soft'):
            add(shape(noise(0.006), lo=3000, order=2) * np.exp(-tt(int(0.006 * SR)) / 0.0012), t, 0.008, rng.uniform(0.2, 0.4))
        else:
            add(shape(noise(0.008), lo=2500, order=2) * np.exp(-tt(int(0.008 * SR)) / 0.0015), t, 0.02, 0.5)
    elif k == 'asterisk':
        add(bell(midi(88), 1.2, 0.3), t, 0.04, 0.6)
    elif k == 'title':
        add(bell(midi(45), 2.4, 0.4), t, 0.07)
    elif k == 'aura':
        n = int(3 * SR)
        add((np.sin(2 * np.pi * midi(64) * tt(n)) + 0.5 * np.sin(2 * np.pi * midi(71) * tt(n))) * env_ar(n, 1.2, 1.6), t, 0.025)
    elif k == 'handin':
        n = int(0.6 * SR)
        add(shape(noise(0.6), lo=300, hi=2500, order=2) * env_ar(n, 0.35, 0.2), t - 0.3, 0.06, pan)
    elif k == 'grip':
        n = int(0.25 * SR)
        add(shape(noise(0.25), lo=200, hi=1800, order=2) * np.exp(-tt(n) / 0.05) + 0.5 * thud(110, 0.06, 0.2)[:n], t, 0.12, 0.6)
    elif k == 'press':
        add(thud(55, 0.2, 0.3), t, 0.25)
    elif k == 'cuff':
        add(metal(2400, 0.08), t, 0.06, 0.45)
        add(metal(3100, 0.05), t + 0.03, 0.04, 0.55)
    elif k == 'no':
        n = int(1.8 * SR)
        add(np.sin(2 * np.pi * midi(69) * tt(n)) * np.exp(-tt(n) / 0.6) * np.clip(tt(n) / 0.02, 0, 1), t + 0.05, 0.02, 0.45)
    elif k == 'scuffle':
        n = int(0.4 * SR)
        add(shape(noise(0.4), lo=150, hi=2200, order=2) * env_ar(n, 0.05, 0.3), t, 0.1, 0.55)
    elif k == 'stamp':
        add(thud(48, 0.25, 0.8), t, 0.4)
        add(shape(noise(0.15), lo=600, hi=4000, order=2) * np.exp(-tt(int(0.15 * SR)) / 0.03), t, 0.1)
    elif k == 'concrete':
        n = int(2.6 * SR)
        add(shape(noise(2.6), hi=180, order=2) * env_ar(n, 2.0, 0.5), t, 0.18)
    elif k == 'slam':
        g = 0.55 if e.get('small') else 1.0
        add(thud(40, 0.5, 1.0), t, 0.5 * g)
        add(metal(180, 0.9), t, 0.12 * g)
        add(metal(415, 0.6), t + 0.01, 0.06 * g)
    elif k == 'tally':
        if t - last_tally < 0.045:
            continue
        last_tally = t
        n = int(0.09 * SR)
        add(shape(noise(0.09), lo=2200, hi=7000, order=2) * env_ar(n, 0.01, 0.07), t, 0.022, rng.uniform(0.35, 0.65))
    elif k == 'scan':
        n = int(2.3 * SR)
        f = np.linspace(900, 300, n)
        s = np.sin(np.cumsum(2 * np.pi * f / SR)) * 0.4 + shape(noise(2.3), lo=2000, hi=5000, order=2) * 0.5
        add(s * env_ar(n, 0.15, 0.4), t, 0.03, 0.6)
    elif k == 'pat':
        add(shape(noise(0.12), lo=150, hi=1500, order=2) * np.exp(-tt(int(0.12 * SR)) / 0.03), t, 0.09 if e.get('hot') else 0.06, 0.55)
    elif k == 'strip':
        n = int(2.0 * SR)
        add(sweep(2400, 600, 2.0) * env_ar(n, 0.1, 1.6), t, 0.02)
        add(shape(noise(2.0), lo=3000, order=2) * env_ar(n, 0.1, 1.6), t, 0.03)
    elif k == 'noted':
        add(shape(noise(0.03), lo=1500, order=2) * np.exp(-tt(int(0.03 * SR)) / 0.005), t, 0.06, 0.62)
        add(bell(midi(84), 0.25, 0.2), t, 0.02, 0.62)
    elif k == 'pin':
        add(thud(62, 0.16, 0.5), t, 0.2, rng.uniform(0.35, 0.65))
    elif k == 'crack':
        n = int(0.5 * SR)
        add(shape(noise(0.5), lo=1200, order=2) * np.exp(-tt(n) / 0.04), t, 0.12)
        add(bell(midi(91), 0.4, 1.0), t, 0.04)
        add(thud(45, 0.3, 0.2), t, 0.12)
    elif k == 'tag':
        add(bell(midi(79), 0.3, 0.2), t, 0.025, 0.6)
    elif k == 'drift':
        n = int(4.5 * SR)
        add(sweep(midi(88), midi(76), 4.5) * np.exp(-tt(n) / 1.6) * np.clip(tt(n) / 0.3, 0, 1), t, 0.03, 0.8)
    elif k == 'question':
        add(bell(midi(71), 1.5, 0.3), t, 0.03, 0.85)
    elif k == 'meter':
        add(bell(midi(57 + 3 * e['i']), 0.6, 0.6), t, 0.05, 0.85)
    elif k == 'impact':
        if e.get('sharp'):
            add(thud(90, 0.1, 1.0), t, 0.32)
            add(shape(noise(0.08), lo=1500, order=2) * np.exp(-tt(int(0.08 * SR)) / 0.01), t, 0.12)
        else:
            add(thud(42, 0.35, 0.8), t, 0.5)
    elif k == 'whoosh':
        n = int(0.22 * SR)
        add(shape(noise(0.22), lo=500, hi=4000, order=2) * env_ar(n, 0.15, 0.06), t, 0.08, 0.65)
    elif k == 'taser':
        n = int(1.15 * SR)
        clicks = np.zeros(n)
        idx = np.cumsum(rng.integers(int(0.004 * SR), int(0.018 * SR), size=200))
        idx = idx[idx < n - 200]
        for i in idx:
            clicks[i:i + 120] += rng.standard_normal(120) * np.exp(-np.arange(120) / 25)
        buzz = sum(np.sign(np.sin(2 * np.pi * 50 * h * tt(n))) / h for h in (1, 3))
        add(shape(clicks, lo=900, order=2) * 0.8 + 0.15 * shape(buzz, hi=3000), t, 0.12, 0.7)
    elif k == 'spray':
        n = int(1.6 * SR)
        add(shape(noise(1.6), lo=3500, order=2) * env_ar(n, 0.03, 1.2), t, 0.06, 0.65)
    elif k == 'fracture':
        add(shape(noise(0.12), lo=900, order=2) * np.exp(-tt(int(0.12 * SR)) / 0.015), t, 0.14)
        add(thud(75, 0.08, 0.6), t, 0.12)
    elif k == 'worse':
        add(sweep(50, 28, 2.5) * np.exp(-tt(int(2.5 * SR)) / 0.9), t, 0.4)
    elif k == 'law':
        add(bell(midi(50), 2.5, 0.3), t, 0.04)
    elif k == 'frame':
        add(np.sin(2 * np.pi * 1760 * tt(int(0.08 * SR))) * env_ar(int(0.08 * SR), 0.005, 0.02), t, 0.03, 0.75)
    elif k == 'scale':
        add(bell(midi(43), 1.8, 0.2), t, 0.05, 0.6)
    elif k == 'threat':
        n = int(0.32 * SR)
        add(shape(np.sign(np.sin(2 * np.pi * 220 * tt(n))), hi=2500) * env_ar(n, 0.005, 0.05), t, 0.03, 0.75)
    elif k == 'merge':
        n = int(1.5 * SR)
        add(shape(noise(1.5), lo=200, hi=1500, order=2) * env_ar(n, 0.8, 0.6), t, 0.04)
    elif k == 'dissolve':
        n = int(4.0 * SR)
        s = sum(np.sin(2 * np.pi * midi(m) * tt(n)) for m in (81, 88, 93)) * np.exp(-tt(n) / 1.4) * np.clip(tt(n) / 0.4, 0, 1)
        add(s, t, 0.012)
    elif k == 'fine':
        add(bell(midi(45), 3.0, 0.3), t, 0.05)

# ---------- mix ----------
print('reverb...')
wet_a = reverb(bus_a, wet=0.3)
gate = np.ones(N)
i_d, ramp = int(DARK * SR), int(0.01 * SR)
gate[i_d:i_d + ramp] = np.linspace(1, 0, ramp)
gate[i_d + ramp:] = 0
mix = wet_a * gate + reverb(bus_b, wet=0.35, seed=4)
for ch in range(2):
    mix[ch] = shape(mix[ch], lo=28, order=2)
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(1.4 * mix) / np.tanh(1.4)

if voice_path:
    with wave.open(voice_path) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').reshape(-1, 2).T / 32768.0
    voice = np.zeros((2, N))
    voice[:, :min(N, v.shape[1])] = v[:, :N]
    voice = reverb(voice, seconds=1.3, decay=0.25, wet=0.12, seed=5)
    voice /= np.max(np.abs(voice)) + 1e-9
    win_n = int(0.12 * SR)
    p = np.concatenate([[0], np.cumsum(voice[0] ** 2 + voice[1] ** 2)])
    rms = np.sqrt(np.maximum(p[win_n:] - p[:-win_n], 0) / (2 * win_n))
    talk = np.clip(rms / 0.04, 0, 1)
    talk = np.concatenate([talk[int(0.08 * SR):], np.zeros(N - len(talk) + int(0.08 * SR))])[:N]
    duck = np.zeros(N)
    level, attack, release = 0.0, 240 / (0.06 * SR), 240 / (0.5 * SR)
    for i in range(0, N, 240):
        target = talk[i]
        level = min(target, level + attack) if target > level else max(target, level - release)
        duck[i:i + 240] = level
    mix = mix * (1 - 0.7 * duck) * 0.62 + voice * 0.85
    mix = np.tanh(1.15 * mix) / np.tanh(1.15)

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
