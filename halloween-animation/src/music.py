"""Procedural score, sound effects, ambience and final mix for "The House That Hums"."""
import json, os
import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
SR = 44100
tl = json.load(open(os.path.join(WORK, 'timeline.json')))
TOTAL = tl['total'] + 0.3
N = int(TOTAL * SR)
rng = np.random.default_rng(7)

music = np.zeros((2, N)); hits = np.zeros((2, N)); sfxb = np.zeros((2, N)); vox = np.zeros((2, N)); amb = np.zeros((2, N))

PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def m(name):
    p, o = (name[:-1], int(name[-1]))
    return 12 * (o + 1) + PC[p]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


CH = {'Dm': ('D', [0, 3, 7]), 'Bb': ('Bb', [0, 4, 7]), 'C': ('C', [0, 4, 7]), 'F': ('F', [0, 4, 7]), 'Gm': ('G', [0, 3, 7]),
      'A7': ('A', [0, 4, 7, 10]), 'A': ('A', [0, 4, 7]), 'D': ('D', [0, 4, 7]), 'Bm': ('B', [0, 3, 7]), 'G': ('G', [0, 4, 7]),
      'Em': ('E', [0, 3, 7]), 'Am': ('A', [0, 3, 7])}


def chord(name, octave):
    root, iv = CH[name]
    r = 12 * (octave + 1) + PC[root]
    return [r + i for i in iv]


def place(buf, x, t, pan=0.0, gain=1.0):
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.vstack([x * l * 1.414, x * r * 1.414])
    i = int(round(t * SR))
    if i >= N:
        return
    if i < 0:
        x = x[:, -i:]; i = 0
    n = min(x.shape[1], N - i)
    buf[:, i:i + n] += x[:, :n] * gain


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR * 0.45) / (SR / 2))
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR * 0.45) / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr and nr < n: e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


# ── instruments ──
def celesta(f, dur=1.8, vel=1.0):
    t = tvec(dur)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.32 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4)
         + 0.14 * np.sin(2 * np.pi * 4.07 * f * t) * np.exp(-t * 9) + 0.05 * np.sin(2 * np.pi * 6.1 * f * t) * np.exp(-t * 16))
    x *= env(len(t), 0.003, 0.05)
    return x * vel * 0.35


def bell(f, dur=3.2, vel=1.0):
    t = tvec(dur)
    idx = 2.2 * np.exp(-t * 3)
    x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 3.5 * f * t)) * np.exp(-t * 1.3)
    x += 0.25 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 2.5)
    return x * env(len(t), 0.002, 0.2) * vel * 0.28


def pluck(f, dur=0.7, vel=1.0, bright=1.0):
    t = tvec(dur)
    x = np.zeros_like(t)
    for k, a in enumerate([1, 0.5, 0.33, 0.22, 0.12], start=1):
        x += a * bright ** (k - 1) * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (5 + 3 * k))
    x[:80] += rng.normal(0, 0.15, 80) * np.linspace(1, 0, 80)
    return x * env(len(t), 0.002, 0.08) * vel * 0.4


def harp(f, dur=2.2, vel=1.0):
    t = tvec(dur)
    x = np.zeros_like(t)
    for k, a in enumerate([1, 0.4, 0.2, 0.1], start=1):
        x += a * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (1.6 + 1.4 * k))
    return x * env(len(t), 0.004, 0.2) * vel * 0.33


def xylo(f, dur=0.4, vel=1.0):
    t = tvec(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 14) + 0.4 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t * 30) + 0.1 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-t * 60)
    return x * env(len(t), 0.001, 0.03) * vel * 0.38


def tuba(f, dur=0.35, vel=1.0):
    t = tvec(dur)
    ph = f * t
    x = np.sign(np.sin(2 * np.pi * ph)) * 0.6 + 0.4 * (2 * (ph % 1) - 1)
    x = lp(x, 500) * env(len(t), 0.02, 0.12)
    return x * vel * 0.35


def clarinet(f, dur=0.3, vel=1.0):
    t = tvec(dur)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    ph = np.cumsum(f * vib) / SR
    x = np.sign(np.sin(2 * np.pi * ph)) * 0.7 + 0.3 * np.sin(2 * np.pi * 2 * ph)
    x = lp(x, 1600) * env(len(t), 0.02, 0.08)
    return x * vel * 0.18


def saw_stack(freqs, dur, detune=0.006, vib=0.003, seed=0):
    t = tvec(dur)
    r = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for f in freqs:
        for d in (-detune, 0, detune):
            v = 1 + vib * np.sin(2 * np.pi * (4.8 + r.random()) * t + r.random() * 6)
            ph = np.cumsum(f * (1 + d) * v) / SR + r.random()
            x += 2 * (ph % 1) - 1
    return x / (3 * max(1, len(freqs)))


def pad(freqs, dur, bright=1100, attack=0.6, release=1.0, vel=1.0, seed=0):
    x = lp(saw_stack(freqs, dur + release, seed=seed), bright, 2)
    return x * env(len(x), attack, release) * vel * 0.5


def cello(f, dur, attack=0.35, release=0.8, bright=900, vel=1.0):
    t = tvec(dur + release)
    v = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.6, 0, 1)
    ph = np.cumsum(f * v) / SR
    x = 2 * (ph % 1) - 1
    x = lp(x, bright, 2)
    return x * env(len(t), attack, release) * vel * 0.4


def choir(freqs, dur, vel=1.0, attack=0.8, release=1.5):
    t = tvec(dur + release)
    x = np.zeros_like(t)
    for f in freqs:
        for d in (-0.004, 0.0, 0.005):
            v = 1 + 0.005 * np.sin(2 * np.pi * 5 * t + f)
            ph = np.cumsum(f * (1 + d) * v) / SR
            x += np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph) + 0.12 * np.sin(6 * np.pi * ph)
    x = bp(x, 200, 2600)
    return x / (3 * len(freqs)) * env(len(t), attack, release) * vel * 0.5


def gong(f, dur=4.5, vel=1.0):
    t = tvec(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 0.9) + 0.4 * np.sin(2 * np.pi * f * 2.02 * t) * np.exp(-t * 1.6) + 0.2 * np.sin(2 * np.pi * f * 2.97 * t) * np.exp(-t * 2.2)
    return x * env(len(t), 0.03, 0.4) * vel * 0.45


def noise(dur):
    return rng.normal(0, 1, int(dur * SR))


# ── score ──
THEME_MIN = [[(0, 1, 'A4'), (1, 1, 'D5'), (2, 1, 'E5')], [(0, 3, 'F5')], [(0, 1, 'E5'), (1, 1, 'D5'), (2, 1, 'C5')], [(0, 3, 'A4')],
             [(0, 1, 'Bb4'), (1, 1, 'D5'), (2, 1, 'F5')], [(0, 2, 'A5'), (2, 1, 'G5')], [(0, 1, 'G5'), (1, 1, 'E5'), (2, 1, 'C#5')], [(0, 3, 'D5')]]
PROG_MIN = ['Dm', 'Bb', 'C', 'F', 'Gm', 'Dm', 'A7', 'Dm']
THEME_MAJ = [[(0, 1, 'A4'), (1, 1, 'D5'), (2, 1, 'E5')], [(0, 3, 'F#5')], [(0, 1, 'E5'), (1, 1, 'D5'), (2, 1, 'C#5')], [(0, 3, 'A4')],
             [(0, 1, 'B4'), (1, 1, 'D5'), (2, 1, 'F#5')], [(0, 2, 'A5'), (2, 1, 'G5')], [(0, 1, 'G5'), (1, 1, 'E5'), (2, 1, 'C#5')], [(0, 3, 'D5')]]
PROG_MAJ = ['D', 'Bm', 'A', 'D', 'G', 'D', 'A7', 'D']

MOODS = {
    'opening': dict(bpm=92, beats=3, prog=PROG_MIN),
    'skeletons': dict(bpm=140, beats=2, prog=['Dm', 'A', 'A', 'Dm', 'Dm', 'A', 'A7', 'Dm']),
    'lonely': dict(bpm=60, beats=4, prog=['Dm', 'Bb', 'Gm', 'A']),
    'tiptoe': dict(bpm=104, beats=4, prog=['Dm', 'A', 'Dm', 'A7']),
    'patch': dict(bpm=66, beats=4, prog=['F', 'C', 'Dm', 'Bb', 'F', 'C', 'Bb', 'A']),
    'warm': dict(bpm=70, beats=3, prog=['Bb', 'F', 'C', 'F']),
    'witch': dict(bpm=112, beats=3, prog=['Dm', 'Gm', 'A', 'Dm']),
    'tender': dict(bpm=64, beats=3, prog=['Dm', 'Bb', 'F', 'A', 'Dm', 'Gm', 'Bb', 'A']),
    'carving': dict(bpm=92, beats=3, prog=['F', 'C', 'Dm', 'Bb', 'F', 'C', 'Bb', 'C']),
    'wonder': dict(bpm=58, beats=4, prog=['D', 'Bm', 'G', 'A', 'D', 'Bm', 'G', 'D']),
    'hum': dict(bpm=84, beats=3, prog=PROG_MAJ),
    'ending': dict(bpm=72, beats=3, prog=PROG_MAJ),
    'finale': dict(bpm=60, beats=4, prog=['Bm', 'G', 'A', 'D']),
}

secs = tl['music']
sections = [(s['t'], secs[i + 1]['t'] if i + 1 < len(secs) else TOTAL, s['mood']) for i, s in enumerate(secs)]


def chord_at(t):
    for t0, t1, mood in sections:
        if t0 <= t < t1:
            M = MOODS[mood]
            bar = 60 / M['bpm'] * M['beats']
            k = int((t - t0) // bar)
            return M['prog'][k % len(M['prog'])], mood
    return 'D', 'finale'


def arrange(t0, t1, mood):
    M = MOODS[mood]
    beat = 60 / M['bpm']
    bar = beat * M['beats']
    nb = int(np.ceil((t1 - t0) / bar))
    span = t1 - t0
    for b in range(nb):
        bt = t0 + b * bar
        if bt >= t1 - 0.05:
            break
        ch = M['prog'][b % len(M['prog'])]
        prog_u = (bt - t0) / max(span, 1e-3)
        remain = min(bar, t1 - bt)
        if mood == 'opening':
            for off, d, nn in THEME_MIN[b % 8]:
                place(music, celesta(hz(m(nn)), 2.0, 0.85), bt + off * beat, 0.2)
            place(music, pluck(hz(chord(ch, 2)[0]), 0.9, 0.9), bt, -0.2)
            for k in (1, 2):
                for nn in chord(ch, 3)[1:]:
                    place(music, pluck(hz(nn), 0.4, 0.35, 0.6), bt + k * beat, 0.3)
            place(music, pad([hz(x) for x in chord(ch, 3)], remain, 900, 0.5, 0.9, 0.45, b), bt, 0)
        elif mood == 'skeletons':
            place(music, tuba(hz(chord(ch, 2)[0]), 0.3, 1.0), bt, 0)
            for nn in chord(ch, 3):
                place(music, pluck(hz(nn), 0.25, 0.3), bt + beat, 0.25)
            arp = chord(ch, 5)
            pat = [arp[0], arp[1], arp[2], arp[1]] if b % 2 == 0 else [arp[2], arp[1], arp[0] + 12, arp[2]]
            for k, nn in enumerate(pat):
                if (b * 4 + k) % 7 == 6:
                    continue
                place(music, xylo(hz(nn), 0.35, 0.8), bt + k * beat / 2, -0.3 + 0.2 * k)
            for k in (1, 3):
                place(music, bp(noise(0.03), 1500, 3500) * np.linspace(1, 0, int(0.03 * SR)) * 0.25, bt + k * beat / 2, 0.5)
        elif mood == 'lonely':
            place(music, cello(hz(chord(ch, 2)[0]), remain, 1.2, 1.5, 600, 0.55), bt, -0.1)
            place(music, pad([hz(x) for x in chord(ch, 3)], remain, 650, 1.5, 1.5, 0.35, b), bt, 0)
            frag = [('A4', 0), ('F5', 2)] if b % 2 == 0 else [('D5', 0.5), ('E5', 2.5)]
            for nn, off in frag:
                place(music, celesta(hz(m(nn)), 2.6, 0.45), bt + off * beat, 0.3)
        elif mood == 'tiptoe':
            r0 = chord(ch, 2)[0]
            for k, (nn, off) in enumerate([(r0, 0), (r0 + 7, 1), (r0 + 12, 2), (r0 + 7, 3)]):
                place(music, pluck(hz(nn), 0.3, 0.6), bt + off * beat, -0.2 + 0.15 * k)
            place(music, xylo(hz(chord(ch, 5)[(b) % 3]), 0.3, 0.35), bt + 3.5 * beat, 0.4)
        elif mood == 'patch':
            notes = chord(ch, 3) + [chord(ch, 4)[0], chord(ch, 4)[1]]
            seq = [notes[0], notes[2], notes[3], notes[1], notes[4], notes[2], notes[3], notes[1]]
            for k, nn in enumerate(seq):
                place(music, harp(hz(nn), 2.0, 0.55), bt + k * beat / 2, -0.3 + 0.08 * k)
            third = chord(ch, 3)[1]
            place(music, cello(hz(third), beat * 2, 0.4, 0.6, 800, 0.45), bt, 0.15)
            place(music, cello(hz(chord(ch, 3)[0]), beat * 2, 0.4, 0.8, 800, 0.45), bt + 2 * beat, 0.15)
            place(music, pad([hz(x) for x in chord(ch, 3)], remain, 800, 1.0, 1.2, 0.3, b), bt, 0)
        elif mood == 'warm':
            for k, nn in enumerate(chord(ch, 4) + [chord(ch, 5)[0]]):
                place(music, harp(hz(nn), 2.4, 0.6), bt + k * beat * 0.5, 0.2)
            place(music, celesta(hz(chord(ch, 5)[0]), 2.0, 0.5), bt + beat, 0.3)
            place(music, pad([hz(x) for x in chord(ch, 3) + [chord(ch, 4)[0]]], remain, 1800, 0.8, 1.2, 0.5, b), bt, 0)
        elif mood == 'witch':
            place(music, pluck(hz(chord(ch, 2)[0]), 0.6, 0.8), bt, -0.2)
            for k in (1, 2):
                place(music, pluck(hz(chord(ch, 3)[1]), 0.3, 0.35), bt + k * beat, 0.2)
            c5 = chord(ch, 4)
            for k, nn in enumerate([c5[0], c5[1], c5[2], c5[1] + 1 if False else c5[1], c5[0] + 12]):
                place(music, clarinet(hz(nn), beat * 0.42, 0.9), bt + k * beat * 0.5 + (0.03 if k % 2 else 0), 0.35)
        elif mood == 'tender':
            c = chord(ch, 4)
            seq = [c[0], c[2], c[1], c[0] + 12, c[1], c[2]]
            for k, nn in enumerate(seq):
                place(music, celesta(hz(nn + 12), 1.6, 0.32), bt + k * beat / 2, 0.25)
            place(music, pad([hz(x) for x in chord(ch, 3)], remain, 750, 1.0, 1.3, 0.35, b), bt, 0)
            place(music, cello(hz(chord(ch, 2)[0]), remain, 0.8, 1.0, 500, 0.35), bt, -0.2)
        elif mood == 'carving':
            grow = 0.5 + 0.5 * prog_u
            c = chord(ch, 4)
            for k in range(3):
                place(music, celesta(hz(c[k % len(c)] + (12 if k == 2 else 0)), 1.4, 0.45 * grow), bt + k * beat, 0.2)
            place(music, pluck(hz(chord(ch, 2)[0]), 0.7, 0.8 * grow), bt, -0.2)
            for k in (1, 2):
                place(music, pluck(hz(chord(ch, 3)[2]), 0.3, 0.3 * grow), bt + k * beat, 0.25)
            place(music, pad([hz(x) for x in chord(ch, 3)], remain, 900 + 900 * prog_u, 0.8, 1.0, 0.3 * grow, b), bt, 0)
        elif mood == 'wonder':
            c = chord(ch, 5)
            for k in range(8):
                place(music, celesta(hz(c[k % 3] + (12 if k >= 4 else 0)), 1.4, 0.18), bt + k * beat / 2, 0.4 - 0.1 * k)
            place(music, pad([hz(x) for x in chord(ch, 4)], remain, 1600, 1.4, 1.6, 0.3, b), bt, 0)
            place(music, choir([hz(x) for x in chord(ch, 3)], remain, 0.35, 1.2, 1.6), bt, -0.1)
        elif mood in ('hum', 'ending'):
            full = mood == 'hum' and b >= 2
            theme = THEME_MAJ[b % 8]
            for off, d, nn in theme:
                place(music, celesta(hz(m(nn)), 2.2, (1.15 if b < 2 else 0.8) if mood == 'hum' else 0.55), bt + off * beat, 0.15)
            if mood == 'hum' and b < 2:
                place(music, pad([hz(x) for x in chord(ch, 3)], remain, 700, 1.0, 1.2, 0.3, b), bt, 0)
                if full:
                    place(music, choir([hz(m(nn))], d * beat, 0.5, 0.15, 0.6), bt + off * beat, -0.15)
            if full or mood == 'ending':
                place(music, pluck(hz(chord(ch, 2)[0]), 0.9, 0.8 if full else 0.45), bt, -0.2)
                for k in (1, 2):
                    for nn in chord(ch, 3)[1:]:
                        place(music, pluck(hz(nn), 0.4, 0.3 if full else 0.18, 0.6), bt + k * beat, 0.3)
                place(music, pad([hz(x) for x in chord(ch, 3)], remain, 1400 if full else 900, 0.6, 1.0, 0.45 if full else 0.3, b), bt, 0)
            if full:
                place(music, choir([hz(x) for x in chord(ch, 3)], remain, 0.35, 0.6, 1.0), bt, 0.1)
                for k, nn in enumerate(chord(ch, 4)):
                    place(music, harp(hz(nn), 1.8, 0.35), bt + k * beat / 3, -0.3)


for t0, t1, mood in sections:
    if mood != 'finale':
        arrange(t0, t1, mood)

# finale: chord changes land on the words
light = [c for c in tl['cues'] if c['word'].lower() == 'light' and c['t'] > TOTAL - 12]
lost = [c for c in tl['cues'] if c['word'].lower() == 'lost']
t_f = [s for s in sections if s[2] == 'finale'][0][0]
t_light = light[-1]['t'] if light else TOTAL - 4
t_lost = lost[-1]['t'] if lost else t_f + 2.5
plan = [(t_f, 'Bm'), (t_lost + 0.6, 'G'), (t_light - 1.6, 'A'), (t_light, 'D')]
for i, (ts, ch) in enumerate(plan):
    te = plan[i + 1][0] if i + 1 < len(plan) else TOTAL + 1.5
    d = te - ts
    last = ch == 'D'
    place(music, pad([hz(x) for x in chord(ch, 3) + [chord(ch, 4)[0]]], d, 1500 if last else 900, 0.5 if last else 1.0, 2.5 if last else 1.0, 0.55 if last else 0.4, i), ts, 0)
    place(music, cello(hz(chord(ch, 2)[0]), d, 0.6, 2.0, 600, 0.45), ts, -0.15)
    c = chord(ch, 4)
    for k in range(int(d / 0.75)):
        place(music, celesta(hz(c[k % len(c)] + (12 if k % 4 == 3 else 0)), 1.6, 0.3), ts + k * 0.75, 0.3)
    if last:
        place(music, choir([hz(x) for x in chord('D', 3)], d, 0.6, 0.8, 2.5), ts, 0)
        for k, nn in enumerate(['D5', 'F#5', 'A5', 'D6']):
            place(music, bell(hz(m(nn)), 4.0, 0.5), ts + 0.12 * k, -0.3 + 0.2 * k)

# ── word cues: high notes on hopeful words, deep notes on heavy words ──
motif_cues = [c for c in tl['cues'] if c.get('motif')]
for c in tl['cues']:
    t = c['t']
    ch, mood = chord_at(t)
    if c.get('motif'):
        continue
    if c['kind'] == 'hi':
        root = chord(ch, 5)
        top = root[2] if len(root) > 2 else root[0]
        place(hits, bell(hz(top + 12 if top < m('C6') else top), 3.0, 0.55), t, 0.25)
        for k, nn in enumerate(root[:3]):
            place(hits, celesta(hz(nn + 12), 1.2, 0.35), t + 0.07 * (k + 1), -0.2 + 0.2 * k)
        sw = pad([hz(x) for x in chord(ch, 4)], 1.6, 2200, 0.7, 1.2, 0.35, 99)
        place(hits, sw, t - 0.7, 0)
    else:
        r = chord(ch, 1)[0]
        place(hits, cello(hz(r + 12), 2.2, 0.25, 1.4, 500, 0.75), t - 0.08, -0.1)
        place(hits, gong(hz(r), 4.5, 0.6), t, 0)
        place(hits, pad([hz(r + 12), hz(r + 19)], 1.6, 450, 0.5, 1.2, 0.4, 98), t - 0.3, 0)

# the remembered song: low... high... home
mnotes = [('A3', 'lo'), ('F#5', 'hi'), ('D5', 'hi')]
for c, (nn, kind) in zip(motif_cues, mnotes):
    f = hz(m(nn))
    place(hits, celesta(f, 2.6, 1.0), c['t'], 0.1)
    if nn == 'A3':
        place(hits, cello(hz(m('A2')), 1.4, 0.2, 1.2, 600, 0.6), c['t'], -0.1)
    elif nn == 'F#5':
        place(hits, bell(f, 3.0, 0.7), c['t'], 0.3)
    else:
        place(hits, bell(f, 4.0, 0.6), c['t'], 0)
        place(hits, choir([hz(x) for x in chord('D', 3)], 3.0, 0.7, 0.3, 2.0), c['t'], 0)
        place(hits, pad([hz(x) for x in chord('D', 4)], 3.0, 2000, 0.3, 2.0, 0.5, 97), c['t'], 0)

# ── Pip hums the remembered song (a soft, closed-mouth 'mmm') ──
def hum_voice(t0, beat, bars, cut_at):
    notes = []
    for b in range(bars):
        for off, d, nn in THEME_MAJ[b]:
            notes.append((t0 + (b * 3 + off) * beat, d * beat, m(nn) - 12))
    end = min(notes[-1][0] + notes[-1][1], cut_at)
    n = int((end - t0 + 0.6) * SR)
    f0 = np.zeros(n); amp = np.zeros(n)
    for st, d, mi in notes:
        i0, i1 = int((st - t0) * SR), int((st - t0 + d) * SR)
        f0[i0:i1] = hz(mi)
        k = np.arange(i1 - i0) / SR
        amp[i0:i1] = np.minimum(1, k / 0.08) * np.minimum(1, (d - k) / 0.1) * 0.7 + 0.3
    f0[f0 == 0] = hz(notes[-1][2])
    f0 = np.exp(lp(np.log(f0), 18, 1))
    tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.4 * tt) * np.clip(tt / 0.5, 0, 1)
    ph = np.cumsum(f0 * vib) / SR
    src = 2 * (ph % 1) - 1
    x = lp(lp(src, 700), 900) + 0.35 * bp(src, 2200, 3000) * 0.3 + lp(noise(n / SR), 1200) * 0.015
    amp = lp(amp, 12, 1)
    fade = np.ones(n); cut = int((cut_at - t0) * SR)
    if cut < n: fade[cut:] = 0; fade[max(0, cut - int(0.5 * SR)):cut] = np.linspace(1, 0, min(cut, int(0.5 * SR)))
    x = x * amp * fade
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.42
    return x


hum_sec = [s for s in sections if s[2] == 'hum']
if hum_sec:
    hb = 60 / MOODS['hum']['bpm']
    nxt = [sp['s'] for sp in tl['speech'] if sp['s'] > hum_sec[0][0]]
    HUM = (hum_sec[0][0], hb, 3, (nxt[0] if nxt else hum_sec[0][1]) - 0.05)


# ── sound effects ──
def sfx_creak(t, pitch=1.0, length=0.6, vol=1.0):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = (90 + 70 * np.sin(np.pi * tt / length) + 25 * np.sin(2 * np.pi * 7 * tt)) * pitch
    ph = np.cumsum(f) / SR
    x = (ph % 1 < 0.08).astype(float) + 0.3 * rng.normal(0, 1, n) * 0.1
    x = bp(x, 400 * pitch, 1800 * pitch) * np.sin(np.pi * tt / length) ** 0.7
    place(sfxb, x * 0.9 * vol, t, -0.1)


def sfx_whoosh(t, dur=0.9, vol=1.0, rev=False, pan=0.0):
    n = int(dur * SR)
    x = noise(dur)
    out = np.zeros(n)
    seg = 2048
    for i in range(0, n, seg):
        u = i / n
        u = 1 - u if rev else u
        fc = 300 + 2400 * np.sin(np.pi * u) ** 2
        out[i:i + seg] = bp(x[i:i + seg], fc * 0.6, fc * 1.6)[:len(out[i:i + seg])]
    e = np.sin(np.pi * np.arange(n) / n) ** 1.5
    place(sfxb, out * e * 0.5 * vol, t, pan)


def sfx_thump(t, vol=1.0):
    tt = tvec(0.45)
    x = np.sin(2 * np.pi * (70 - 30 * tt) * tt) * np.exp(-tt * 9) + lp(noise(0.45), 300) * np.exp(-tt * 25) * 0.5
    place(sfxb, x * 0.9 * vol, t, 0)


def sfx_clunk(t):
    tt = tvec(0.25)
    x = (np.sin(2 * np.pi * 190 * tt) + 0.6 * np.sin(2 * np.pi * 455 * tt) + 0.3 * np.sin(2 * np.pi * 1020 * tt)) * np.exp(-tt * 28)
    place(sfxb, x * 0.45, t, 0.1)


def sfx_bones(t):
    for k in range(9):
        place(sfxb, xylo(hz(m('G5')) * (1 + 0.3 * rng.random()), 0.12, 0.45), t + k * 0.08 + rng.random() * 0.03, rng.uniform(-0.5, 0.5))


def sfx_xylo_down(t):
    notes = ['D6', 'A5', 'F5', 'D5', 'A4', 'F4', 'D4']
    for k, nn in enumerate(notes):
        place(sfxb, xylo(hz(m(nn)), 0.3, 0.7), t + k * 0.06, 0.2)


def sfx_sparkle(t, vol=1.0):
    for k, nn in enumerate(['A5', 'D6', 'F#6', 'A6', 'D7']):
        place(sfxb, celesta(hz(m(nn)), 1.0, 0.35 * vol), t + k * 0.06, -0.4 + 0.2 * k)


def sfx_carve(t):
    for k in range(3):
        d = 0.18
        tt = tvec(d)
        x = bp(noise(d), 2200, 5200) * np.sin(np.pi * tt / d) * 0.25
        place(sfxb, x, t + k * 0.22, -0.15)


def sfx_snap(t):
    x = hp(noise(0.04), 2000) * np.exp(-tvec(0.04) * 120)
    place(sfxb, x * 0.8, t, -0.2)


def sfx_ignite(t):
    d = 0.9
    tt = tvec(d)
    x = lp(noise(d), 600) * (1 - np.exp(-tt * 12)) * np.exp(-tt * 3) * 0.6
    cr = np.zeros(len(tt))
    for _ in range(25):
        i = rng.integers(0, len(tt) - 200)
        cr[i:i + 60] += rng.normal(0, 1, 60) * np.exp(-np.arange(60) / 10)
    place(sfxb, x + hp(cr, 2500) * 0.25, t, -0.1)
    sfx_sparkle(t + 0.15, 0.7)


def sfx_hoot(t):
    for k, (d, f0) in enumerate([(0.32, 410), (0.55, 380)]):
        tt = tvec(d)
        f = f0 * (1 - 0.06 * tt / d)
        ph = np.cumsum(f) / SR
        x = np.sin(2 * np.pi * ph) * np.sin(np.pi * tt / d) ** 2 + lp(noise(d), 900) * 0.05
        place(sfxb, x * 0.25, t + k * 0.45, 0.4)


def sfx_glow(t):
    place(sfxb, bell(hz(m('D6')), 2.5, 0.35), t, 0.3)
    sfx_sparkle(t + 0.05, 0.6)


def sfx_giggle(t):
    for k, nn in enumerate(['E6', 'G6', 'E6', 'A6', 'G6']):
        place(sfxb, celesta(hz(m(nn)), 0.5, 0.22), t + k * 0.09, -0.3)


SFX = {
    'creak': lambda t: sfx_creak(t), 'creak2': lambda t: sfx_creak(t, 0.8, 0.7), 'creakBig': lambda t: sfx_creak(t, 0.6, 1.0, 1.3),
    'thump': sfx_thump, 'whoosh': lambda t: sfx_whoosh(t, 1.0, 1.0, False, 0.5), 'whoosh2': lambda t: sfx_whoosh(t, 0.8, 0.9, True, -0.5),
    'whooshSoft': lambda t: sfx_whoosh(t, 1.1, 0.45), 'clunk': sfx_clunk, 'bones': sfx_bones, 'xyloDown': sfx_xylo_down,
    'sparkle': sfx_sparkle, 'carve': sfx_carve, 'snap': sfx_snap, 'ignite': sfx_ignite, 'hoot': sfx_hoot, 'glowChime': sfx_glow,
    'giggle': sfx_giggle, 'wind': lambda t: sfx_whoosh(t, 2.4, 0.35, False, -0.3),
}
for s in tl['sfx']:
    SFX[s['name']](s['t'])

# ── ambience per set ──
sets = tl['sets']
spans = [(s['t'], sets[i + 1]['t'] if i + 1 < len(sets) else TOTAL, s['set']) for i, s in enumerate(sets)]
for t0, t1, st in spans:
    d = t1 - t0
    if d <= 0.05:
        continue
    n = int(d * SR)
    tt = np.arange(n) / SR
    fade = np.minimum(1, np.minimum(tt / 0.15, (d - tt) / 0.15))
    if st == 'roof':
        w = lp(noise(d), 380) * (0.55 + 0.45 * np.sin(2 * np.pi * tt / 7.3 + t0) ** 2) * 0.05
        place(amb, np.vstack([w, np.roll(w, 900)]) * fade, t0)
    elif st == 'hill':
        w = lp(noise(d), 300) * 0.03
        cr = np.zeros(n)
        for k in range(int(d * 1.6)):
            i = int(rng.random() * (n - SR // 4))
            ct = np.arange(SR // 5) / SR
            cr[i:i + len(ct)] += np.sin(2 * np.pi * 4300 * ct) * (np.sin(2 * np.pi * 28 * ct) > 0) * np.sin(np.pi * ct / ct[-1]) * 0.012
        place(amb, np.vstack([w + cr, w + np.roll(cr, 300)]) * fade, t0)
    elif st == 'attic':
        cr = np.zeros(n)
        idx = rng.integers(0, n, int(d * 18))
        cr[idx] = rng.normal(0, 0.18, len(idx))
        cr = hp(cr, 1500) + lp(noise(d), 200) * 0.01
        place(amb, np.vstack([cr, cr]) * fade, t0)

# ── voices ──
FXGAIN = {'NAR': 1.0, 'PIP': 1.0, 'PATCH': 1.05, 'BRAM': 1.0, 'RATTLE': 0.95, 'CLATTER': 0.95}
voice_rev = np.zeros((2, N))
for sp in tl['speech']:
    x, sr = sf.read(sp['wav'], dtype='float64')
    x = signal.resample_poly(x, 147, 80)
    who = sp['who']
    if who in ('RATTLE', 'CLATTER'):
        dl = int(0.0045 * SR)
        x = x + 0.35 * np.concatenate([np.zeros(dl), x[:-dl]])
    if who == 'PATCH':
        x = x + 0.35 * lp(x, 220)
    x = hp(x, 70)
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.02] ** 2)) + 1e-9
    x = x * (0.13 / rms) * FXGAIN[who]
    place(vox, x, sp['s'], 0)
    send = {'NAR': 0.22, 'PIP': 0.28, 'RATTLE': 0.3, 'CLATTER': 0.3}.get(who, 0.14)
    place(voice_rev, x * send, sp['s'], 0)


def reverb_ir(seconds, seed):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    irl = r.normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
    irr = r.normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
    irl, irr = lp(irl, 5000), lp(irr, 5000)
    s = np.sqrt(np.sum(irl ** 2))
    return irl / s, irr / s


if hum_sec:
    hx = hum_voice(*HUM)
    place(vox, hx, HUM[0], -0.05)
    place(voice_rev, hx * 0.3, HUM[0], 0)

il, ir_ = reverb_ir(1.2, 3)
vr = np.vstack([signal.fftconvolve(voice_rev[0], il)[:N], signal.fftconvolve(voice_rev[1], ir_)[:N]])
vox = vox + vr

ml, mr = reverb_ir(2.6, 5)
mus = music + hits
mus_wet = np.vstack([signal.fftconvolve(mus[0], ml)[:N], signal.fftconvolve(mus[1], mr)[:N]])
sfx_wet = np.vstack([signal.fftconvolve(sfxb[0], il)[:N], signal.fftconvolve(sfxb[1], ir_)[:N]])

# ducking: music dips under speech
ve = np.abs(vox[0]) + np.abs(vox[1])
win = int(0.03 * SR)
ve = np.convolve(ve, np.ones(win) / win, mode='same')
att, rel = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.45 * SR))
sm = signal.lfilter([1 - rel], [1, -rel], ve)
sm = np.maximum(sm, signal.lfilter([1 - att], [1, -att], ve))
duck = 1 - 0.5 * np.clip(sm / 0.08, 0, 1)
duck_hits = 1 - 0.25 * np.clip(sm / 0.08, 0, 1)

music_dry = music * duck
hits_dry = hits * duck_hits
wet_duck = 1 - 0.35 * np.clip(sm / 0.08, 0, 1)
mix = vox * 1.0 + (music_dry * 0.62 + hits_dry * 0.75) + mus_wet * 0.32 * wet_duck + sfxb * 0.9 + sfx_wet * 0.2 + amb
# gentle fade at the very end only (the first frame starts with sound)
fo = int(1.2 * SR)
mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.93
sf.write(os.path.join(WORK, 'mix.wav'), mix.T.astype(np.float32), SR, subtype='PCM_16')
print('mix written', mix.shape[1] / SR, 's; music rms', float(np.sqrt(np.mean((music_dry * 0.62) ** 2))), 'vox rms', float(np.sqrt(np.mean(vox ** 2))))
