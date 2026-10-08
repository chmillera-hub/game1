"""Original score + sound design + final mix, all synthesized here (no samples).

Reads build/timeline.json (scene/line times), build/voice/*.wav and build/sfx.json,
writes build/mix.wav. Music sections follow the scenes:
  night (scroll/weight) -> warming (reply) -> lo-fi beat (steps) -> music box (payoff)
  -> bright beat (styles) -> warm outro (close)
"""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
SR = 48000
BPM = 76
BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(7)

TL = json.load(open(os.path.join(BUILD, 'timeline.json')))
DUR = TL['duration'] + 0.5
N = int(DUR * SR)
SC = {s['id']: s for s in TL['scenes']}
LN = TL['lines']


def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR
def bp(lo, hi, order=2): return butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
def lp(f, order=2): return butter(order, f, 'lowpass', fs=SR, output='sos')
def hp(f, order=2): return butter(order, f, 'highpass', fs=SR, output='sos')


class Bus:
    def __init__(self): self.x = np.zeros((N, 2), dtype=np.float32)

    def add(self, sig, t, vol=1.0, pan=0.0):
        i = int(t * SR)
        if i >= N or len(sig) == 0: return
        if i < 0: sig, i = sig[-i:], 0
        sig = sig[: N - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        if sig.ndim == 1:
            self.x[i:i + len(sig), 0] += sig * vol * l * 1.414
            self.x[i:i + len(sig), 1] += sig * vol * r * 1.414
        else:
            self.x[i:i + len(sig)] += sig * vol


# ------------------------------------------------------------------ instruments
def env_adr(n, a, d, rel_at, rel):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    if rel_at is not None:
        e *= np.clip(1 - (t - rel_at) / rel, 0, 1)
    return e


def epiano(m, dur, vel=0.6):
    """FM electric piano (Rhodes-ish): bell-like attack, warm body, gentle tremolo."""
    f = mtof(m)
    L = dur + 1.6
    t = tt(L)
    idx = 1.6 * np.exp(-t / 0.22) + 0.35 * vel
    mod = np.sin(2 * np.pi * f * t)
    body = np.sin(2 * np.pi * f * t + idx * mod)
    tine = 0.18 * np.sin(2 * np.pi * f * 7.0 * t) * np.exp(-t / 0.05)
    decay = 1.3 + 2.5 * np.clip((72 - m) / 36, 0, 1)
    e = env_adr(len(t), 0.004, decay, dur, 0.35)
    s = (body + tine) * e * vel
    trem = 0.09 * np.sin(2 * np.pi * 4.2 * t)
    return np.stack([s * (1 + trem), s * (1 - trem)], axis=1).astype(np.float32)


def pad(m, dur, vel=0.3):
    """Soft additive-saw pad with three detuned voices and a slow swell."""
    L = dur + 1.8
    t = tt(L)
    out = np.zeros((len(t), 2), np.float32)
    for v, (det, pan) in enumerate([(-0.004, -0.6), (0.0, 0.0), (0.0045, 0.6)]):
        f = mtof(m) * (1 + det)
        s = np.zeros(len(t))
        for h in range(1, 10):
            s += np.sin(2 * np.pi * f * h * t + v * 1.3 * h) / h * np.exp(-h / 3.2)
        out[:, 0] += s * (1 - pan) * 0.5
        out[:, 1] += s * (1 + pan) * 0.5
    a = np.minimum(1, t / 0.9)
    r = np.clip(1 - (t - dur) / 1.6, 0, 1)
    return (out * (a * r * vel * 0.32)[:, None]).astype(np.float32)


def bass(m, dur, vel=0.6):
    f = mtof(m)
    t = tt(dur + 0.3)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    e = env_adr(len(t), 0.01, 1.4, dur, 0.25)
    return (s * e * vel).astype(np.float32)


def musicbox(m, vel=0.5):
    f = mtof(m)
    t = tt(2.6)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / 0.4) + 0.12 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.15)
    e = np.minimum(1, t / 0.002) * np.exp(-t / 0.9)
    return (s * e * vel).astype(np.float32)


def kick(vel=0.9):
    t = tt(0.5)
    f = 48 + 95 * np.exp(-t / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    s[:120] += rng.normal(0, 0.3, 120) * np.linspace(1, 0, 120)
    return (sosfilt(lp(4000), s) * vel).astype(np.float32)


def snare(vel=0.6):
    t = tt(0.35)
    n = sosfilt(bp(900, 6000), rng.normal(0, 1, len(t))) * np.exp(-t / 0.11)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.06)
    return (sosfilt(lp(5200), 0.8 * n + 0.6 * tone) * vel).astype(np.float32)


def hat(vel=0.3, open_=False):
    t = tt(0.25 if open_ else 0.08)
    n = sosfilt(hp(7000), rng.normal(0, 1, len(t))) * np.exp(-t / (0.09 if open_ else 0.025))
    return (n * vel).astype(np.float32)


def bell(f, d=0.8, vel=0.5):
    t = tt(d + 0.2)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.15)
    return (s * np.exp(-t / (d * 0.45)) * np.minimum(1, t / 0.002) * vel).astype(np.float32)


# ------------------------------------------------------------------ sound effects
def noise(d): return rng.normal(0, 1, int(d * SR))


def sfx(name):
    if name == 'swipe':
        t = tt(0.2); n = sosfilt(bp(800, 5000), noise(0.2)); return n * np.sin(np.pi * t / 0.2) ** 2 * 0.35
    if name == 'type':
        t = tt(0.03); n = sosfilt(bp(1500 + rng.random() * 1500, 7000), noise(0.03)) * np.exp(-t / 0.006)
        return n * 0.6 + np.sin(2 * np.pi * (900 + rng.random() * 300) * t) * np.exp(-t / 0.004) * 0.2
    if name == 'tap':
        t = tt(0.08); return sosfilt(bp(600, 4000), noise(0.08)) * np.exp(-t / 0.012) * 0.7 + np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.03) * 0.5
    if name == 'pop':
        t = tt(0.14); f = 260 + 900 * (1 - np.exp(-t / 0.03)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045) * 0.6
    if name in ('whoosh', 'zoomout', 'send', 'swoop'):
        d = {'whoosh': 0.55, 'zoomout': 1.0, 'send': 0.25, 'swoop': 0.6}[name]
        t = tt(d); x = noise(d); out = np.zeros_like(x)
        seg = 1024
        for i in range(0, len(x), seg):
            p = i / len(x)
            fc = {'whoosh': 400 + 2600 * np.sin(np.pi * p), 'zoomout': 2800 * (1 - p) + 250, 'send': 600 + 3500 * p, 'swoop': 500 + 2500 * np.sin(np.pi * p)}[name]
            out[i:i + seg] = sosfilt(bp(fc * 0.6, min(fc * 1.6, 20000)), x[max(0, i - 2048):i + seg])[-len(x[i:i + seg]):]
        e = np.sin(np.pi * t / d) ** 1.5
        s = out * e * 0.45
        if name == 'swoop': s += np.sin(2 * np.pi * np.cumsum(500 + 700 * np.sin(np.pi * t / d)) / SR) * e * 0.12
        if name == 'zoomout': s += np.sin(2 * np.pi * np.cumsum(220 - 120 * t / d) / SR) * e * 0.15
        return s
    if name == 'thud':
        t = tt(0.25); return np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.06) * 0.8 + sosfilt(lp(900), noise(0.25)) * np.exp(-t / 0.04) * 0.4
    if name == 'beep':
        t = tt(0.1); return np.sin(2 * np.pi * 1850 * t) * np.minimum(1, t / 0.003) * (t < 0.085) * 0.25
    if name == 'tick':
        t = tt(0.04); return sosfilt(bp(2500, 8000), noise(0.04)) * np.exp(-t / 0.005) * 0.6
    if name == 'clatter':
        out = np.zeros(int(0.5 * SR))
        for k, (dt, v) in enumerate([(0, 1), (0.12, 0.6), (0.2, 0.4), (0.26, 0.25), (0.3, 0.15)]):
            t = tt(0.06); c = sosfilt(bp(1200, 6000), noise(0.06)) * np.exp(-t / 0.01) * v + np.sin(2 * np.pi * (700 + 200 * k) * t) * np.exp(-t / 0.02) * v * 0.4
            i = int(dt * SR); out[i:i + len(c)] += c
        return out * 0.7
    if name == 'buzz':
        t = tt(0.32); s = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.5 + np.sin(2 * np.pi * 300 * t) * 0.3
        return sosfilt(lp(900), s) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t)) * np.sin(np.pi * t / 0.32) * 0.35
    if name == 'ping':
        a = bell(1318.5, 0.6, 0.35); b = bell(1975.5, 0.8, 0.3); out = np.zeros(len(b) + 4500); out[:len(a)] += a; out[4500:4500 + len(b)] += b; return out
    if name == 'chime':
        out = np.zeros(int(1.6 * SR))
        for k, f in enumerate([1046.5, 1318.5, 1568.0]):
            b = bell(f, 1.0, 0.22); i = int(k * 0.11 * SR); out[i:i + len(b)] += b[: len(out) - i]
        return out
    if name in ('sparkle', 'spark'):
        out = np.zeros(int(1.0 * SR))
        if name == 'spark':
            t = tt(0.25); out[:len(t)] += np.sin(2 * np.pi * np.cumsum(800 + 2500 * t / 0.25) / SR) * np.exp(-t / 0.1) * 0.15
        for k in range(7):
            f = mtof(84 + rng.choice([0, 2, 4, 7, 9, 12, 14, 16])); b = bell(f, 0.5, 0.12); i = int((0.05 + k * 0.055) * SR); out[i:i + len(b)] += b[: len(out) - i]
        return out
    if name == 'ding':
        a, b = bell(1568, 1.4, 0.4), bell(2093, 1.2, 0.18); a[:len(b)] += b; return a
    if name == 'boop':
        t = tt(0.22); f = np.where(t < 0.1, 620, 930); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((t % 0.11) / 0.06)) * 0.3
    if name == 'glitch':
        out = np.zeros(int(0.35 * SR))
        for k in range(6):
            t = tt(0.04); f = 200 + rng.random() * 1500; s = np.sign(np.sin(2 * np.pi * f * t)) * 0.18; i = int(k * 0.055 * SR); out[i:i + len(s)] += s
        return sosfilt(lp(5000), out)
    raise ValueError(name)


# ------------------------------------------------------------------ the score
CH = {  # (bass note, voicing)
    'Am9': (45, [60, 64, 67, 71]), 'Fmaj9': (41, [57, 60, 64, 67]), 'Cmaj9': (48, [62, 64, 67, 71]),
    'G6': (43, [59, 62, 64, 69]), 'Dm9': (50, [53, 57, 60, 64]), 'Em7': (40, [55, 59, 62, 67]),
    'G13': (43, [53, 59, 64, 69]), 'E7': (40, [56, 62, 64, 71]), 'Csus2': (48, [55, 62, 67, 72]),
}
PROG = {
    'night':  ['Am9', 'Fmaj9', 'Cmaj9', 'G6'],
    'weight': ['Dm9', 'Am9', 'Fmaj9', 'E7'],
    'reply':  ['Fmaj9', 'G6', 'Am9', 'Cmaj9'],
    'steps':  ['Fmaj9', 'Em7', 'Dm9', 'Cmaj9', 'Fmaj9', 'Em7', 'Dm9', 'Cmaj9', 'Dm9', 'G13', 'Cmaj9', 'Am9', 'Fmaj9', 'G13', 'Cmaj9', 'Cmaj9'],
    'payoff': ['Fmaj9', 'G6', 'Em7', 'Am9', 'Dm9', 'G13', 'Cmaj9', 'Cmaj9'],
    'styles': ['Cmaj9', 'Am9', 'Dm9', 'G13'],
    'close':  ['Fmaj9', 'G6', 'Em7', 'Am9'],
    'end':    ['Fmaj9', 'G6', 'Csus2', 'Csus2'],
}
MOTIF = [(0, 76), (0.75, 79), (1.5, 81), (2.5, 79), (3.5, 76), (4.5, 74), (5.0, 72), (6.0, 74)]
BOX = [[(0, 81), (1, 79), (1.5, 77), (2, 76), (3, 77)], [(0, 79), (1, 74), (2, 76), (3, 79)], [(0, 76), (1, 79), (2, 83), (3, 81)], [(0, 81), (2, 76), (3, 79)],
       [(0, 77), (1, 76), (2, 74), (3, 77)], [(0, 79), (1, 81), (2, 83), (3, 86)], [(0, 84), (2.5, 79)], [(0, 88)]]


def section_bars():
    """Map each bar to a section, switching at the bar nearest each scene start."""
    def b(t): return int(round(t / BAR))
    end_card = LN['r_c']['end'] + 1.1
    marks = [(0, 'night'), (b(SC['weight']['start']), 'weight'), (b(SC['reply']['start']), 'reply'), (b(SC['step1']['start']), 'steps'),
             (b(SC['payoff']['start']), 'payoff'), (b(SC['styles']['start']), 'styles'), (b(SC['close']['start']), 'close'), (b(end_card), 'end')]
    nbars = int(np.ceil(DUR / BAR))
    out = []
    for i in range(nbars):
        sec, s0 = [(m[1], m[0]) for m in marks if m[0] <= i][-1]
        out.append((sec, i - s0))
    return out


def swing(step):  # 16th-note grid with a lazy swing on the off-8ths
    beat, sub = divmod(step, 4)
    return (beat + [0, 0.29, 0.58, 0.79][sub]) * BEAT


def compose():
    music, drums = Bus(), Bus()
    bars = section_bars()
    for i, (sec, k) in enumerate(bars):
        t0 = i * BAR
        name = PROG[sec][k % len(PROG[sec])]
        bn, voicing = CH[name]
        last = sec == 'end' and k >= 2
        dur = BAR * (2.2 if last and k == 2 else 1.0)
        if sec == 'end' and k > 2:
            continue
        if sec in ('night', 'weight'):
            music.add(pad(bn + 12, BAR, 0.32 if sec == 'night' else 0.36), t0)
            for m in voicing[:3]: music.add(pad(m, BAR, 0.16), t0)
            music.add(bass(bn, BAR * 0.95, 0.35), t0)
            arp = [(0, voicing[0]), (1.5, voicing[2]), (2.5, voicing[3]), (3.25, voicing[1])] if sec == 'night' else [(0, voicing[1]), (2, voicing[3])]
            for b, m in arp: music.add(epiano(m, BEAT * 1.4, 0.26), t0 + b * BEAT, pan=0.2 if m % 2 else -0.2)
            if sec == 'weight':
                for b in range(4): drums.add(sfx('tick') * 0.5, t0 + b * BEAT, vol=0.45, pan=0.3)
        elif sec == 'reply':
            music.add(pad(bn + 12, BAR, 0.34), t0)
            for m in voicing: music.add(pad(m, BAR, 0.18), t0)
            music.add(bass(bn, BAR * 0.95, 0.4), t0)
            music.add(epiano(voicing[0], BEAT, 0.3), t0); music.add(epiano(voicing[2], BEAT, 0.25), t0 + 2 * BEAT)
            if k >= 2:
                for s in range(0, 16, 2): drums.add(hat(0.12 + 0.06 * (s % 4 == 0)), t0 + swing(s), pan=0.25)
        elif sec in ('steps', 'styles', 'close'):
            soft = sec == 'close'
            music.add(pad(bn + 12, BAR, 0.22), t0)
            # electric piano comping: chord on 1, a push on the "and" of 2
            for m in voicing: music.add(epiano(m, BEAT * 1.2, 0.2), t0 + 0.01 * (m % 3))
            for m in voicing[1:]: music.add(epiano(m, BEAT * 0.8, 0.14), t0 + swing(6))
            music.add(bass(bn, BEAT * 1.6, 0.55), t0); music.add(bass(bn + (7 if k % 2 else 12), BEAT * 1.2, 0.4), t0 + swing(10))
            if sec == 'steps' and k % 8 in (4, 5):
                for b, m in MOTIF:
                    if (b < 4) == (k % 8 == 4): music.add(epiano(m, BEAT * 0.9, 0.22), t0 + (b % 4) * BEAT, pan=0.3)
            if sec == 'styles':
                for s in (3, 7, 11, 15): music.add(epiano(voicing[3] + 12, BEAT * 0.3, 0.1), t0 + swing(s), pan=0.4)
            kicks = [0, 7, 10] if not soft else [0, 10]
            for s in kicks: drums.add(kick(0.8 if s == 0 else 0.6), t0 + swing(s))
            if not soft:
                for s in (4, 12): drums.add(snare(0.42), t0 + swing(s), pan=-0.05)
            for s in range(0, 16, 2): drums.add(hat(0.18 if s % 4 == 0 else 0.11), t0 + swing(s), pan=0.3)
            if k % 4 == 3 and not soft: drums.add(hat(0.12, True), t0 + swing(14), pan=0.3)
        elif sec == 'payoff':
            music.add(pad(bn + 12, BAR, 0.3), t0)
            for m in voicing: music.add(pad(m, BAR, 0.16), t0)
            music.add(bass(bn, BAR, 0.38), t0)
            for b, m in [(0, voicing[0]), (1, voicing[1]), (2, voicing[2]), (3, voicing[3])]: music.add(epiano(m, BEAT * 2, 0.16), t0 + b * BEAT)
            for b, m in BOX[k % len(BOX)]: music.add(musicbox(m, 0.32), t0 + b * BEAT, pan=0.15)
        elif sec == 'end':
            music.add(pad(bn + 12, dur, 0.3), t0)
            for m in voicing: music.add(pad(m, dur, 0.18), t0); music.add(epiano(m, dur, 0.18), t0 + 0.04 * voicing.index(m))
            music.add(bass(bn, dur, 0.45), t0)
            if k == 2: music.add(musicbox(84, 0.3), t0 + BEAT); music.add(musicbox(88, 0.25), t0 + BEAT * 2); music.add(musicbox(91, 0.25), t0 + BEAT * 3)
    return music.x, drums.x


def reverb(x, secs=2.4, wet=0.22):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = np.stack([rng.normal(0, 1, n), rng.normal(0, 1, n)], axis=1) * np.exp(-t / (secs / 5))[:, None]
    ir = sosfilt(lp(5000), ir, axis=0); ir /= np.sqrt((ir ** 2).sum() / 2)
    y = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return (x * (1 - wet) + y * wet).astype(np.float32)


def rain_bed():
    """Rain on the window for the night scenes (louder outside, softer when the lamp is on)."""
    x = rng.normal(0, 1, (N, 2)).astype(np.float32)
    x = sosfilt(bp(400, 6000), x, axis=0) * 0.05
    drops = np.zeros((N, 2), np.float32)
    idx = rng.integers(0, N - 2000, int(DUR * 25))
    for i in idx:
        c = rng.integers(0, 2); d = sfx('tick')[:600] * (0.08 + rng.random() * 0.12)
        drops[i:i + len(d), c] += d
    bed = sosfilt(lp(5000), x + drops, axis=0)
    g = np.zeros(N, np.float32)
    def ramp(a, b, va, vb):
        ia, ib = int(a * SR), int(b * SR); g[ia:ib] = np.linspace(va, vb, ib - ia)
    def hold(a, b, v): g[int(a * SR):int(b * SR)] = v
    s = SC
    hold(0, s['weight']['start'] - 0.5, 1.0); ramp(s['weight']['start'] - 0.5, s['weight']['start'] + 1.0, 1.0, 0.0)
    ramp(s['reply']['start'] - 0.3, s['reply']['start'] + 0.6, 0.0, 0.9); hold(s['reply']['start'] + 0.6, LN['a_hey']['start'], 0.9)
    ramp(LN['a_hey']['start'], LN['a_hey']['start'] + 2.0, 0.9, 0.35); hold(LN['a_hey']['start'] + 2.0, s['reply']['end'] - 0.6, 0.35)
    ramp(s['reply']['end'] - 0.6, s['reply']['end'] + 0.3, 0.35, 0.0)
    cut = LN['g_tuck']['end'] + 0.9
    ramp(cut, cut + 1.0, 0.0, 0.55); hold(cut + 1.0, s['payoff']['end'] - 0.4, 0.55); ramp(s['payoff']['end'] - 0.4, s['payoff']['end'] + 0.3, 0.55, 0.0)
    ramp(s['close']['start'] - 0.3, s['close']['start'] + 0.8, 0.0, 0.5); hold(s['close']['start'] + 0.8, LN['r_c']['end'] + 1.1, 0.5)
    ramp(LN['r_c']['end'] + 1.1, LN['r_c']['end'] + 2.5, 0.5, 0.0)
    return bed * g[:, None]


def load_voices():
    v = Bus()
    for l in LN.values():
        x, sr = sf.read(os.path.join(BUILD, 'voice', l['id'] + '.wav'), dtype='float32')
        x = resample_poly(x, SR, sr).astype(np.float32)
        x = sosfilt(hp(85), x).astype(np.float32)
        v.add(x, l['start'], vol=0.9)
    return v.x


def duck_env(voice, depth=0.74):
    e = np.abs(voice).max(axis=1)
    win = int(0.04 * SR)
    e = np.convolve(e, np.ones(win) / win, mode='same')
    e = np.clip(e / (np.percentile(e[e > 1e-4], 70) + 1e-6), 0, 1)
    # slow release so music doesn't pump between words
    out = np.zeros_like(e); a, r = np.exp(-1 / (0.05 * SR)), np.exp(-1 / (0.6 * SR)); prev = 0.0
    step = 64
    for i in range(0, len(e), step):
        x = e[i:i + step].max()
        prev = x + (prev - x) * (a ** step if x > prev else r ** step)
        out[i:i + step] = prev
    return 1 - depth * out


def main():
    print('composing...')
    music, drums = compose()
    music = sosfilt(hp(40), music, axis=0)
    # gentle lo-fi tone + vinyl crackle on the beat sections
    drums = sosfilt(lp(9000), drums, axis=0)
    bus = reverb(music + drums * 0.8, 2.4, 0.24)
    crackle = np.zeros((N, 2), np.float32)
    for i in rng.integers(0, N - 50, int(DUR * 9)): crackle[i:i + 30, rng.integers(0, 2)] += rng.normal(0, 0.08, 30)
    crackle = sosfilt(bp(1000, 7000), crackle, axis=0)
    beat_mask = np.zeros(N, np.float32)
    for a, b in [(SC['step1']['start'], SC['payoff']['start']), (SC['styles']['start'], SC['close']['end'])]: beat_mask[int(a * SR):int(b * SR)] = 1
    bus = bus + crackle * beat_mask[:, None] * 0.5
    print('voices + sfx...')
    voice = load_voices()
    fx = Bus()
    for e in json.load(open(os.path.join(BUILD, 'sfx.json'))):
        s = sfx(e['name']).astype(np.float32)
        fx.add(s, e['t'], vol=e.get('vol', 0.5) * 0.75, pan=e.get('pan', 0))
    fx_x = reverb(fx.x, 1.2, 0.12)
    rain = rain_bed()
    duck = duck_env(voice)
    # overall music level by section: quiet under the night scenes, fuller in the explainer
    lvl = np.full(N, 0.62, np.float32)
    def setl(a, b, v): lvl[int(a * SR):int(min(b, DUR) * SR)] = v
    setl(SC['step1']['start'], SC['payoff']['start'], 0.44); setl(SC['payoff']['start'], SC['styles']['start'], 0.72)
    setl(SC['styles']['start'], SC['close']['start'], 0.46); setl(SC['close']['start'], LN['r_c']['end'] + 1.0, 0.52); setl(LN['r_c']['end'] + 1.0, DUR, 0.85)
    lvl = np.convolve(lvl, np.ones(SR) / SR, mode='same')
    fade = np.ones(N, np.float32); fi = int(1.5 * SR); fade[:fi] = np.linspace(0, 1, fi)
    fo = int(2.5 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    stems = {'music': bus * (lvl * duck * fade)[:, None] * 0.32, 'voice': voice * 1.0, 'sfx': fx_x * 0.9, 'rain': rain * fade[:, None] * 0.6}
    mix = sum(stems.values())
    if os.environ.get('STEMS'):
        os.makedirs(os.path.join(BUILD, 'stems'), exist_ok=True)
        for k, v in stems.items(): sf.write(os.path.join(BUILD, 'stems', k + '.wav'), v, SR, subtype='FLOAT')
    peak = np.abs(mix).max()
    print(f'peak before limit {peak:.2f}')
    mix = np.tanh(mix / max(peak, 1e-6) * 1.3) * 0.89
    sf.write(os.path.join(BUILD, 'mix.wav'), mix, SR, subtype='PCM_16')
    print('wrote build/mix.wav', mix.shape[0] / SR, 's')


if __name__ == '__main__':
    main()
