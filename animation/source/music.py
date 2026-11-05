"""Procedural score + SFX, mixed with ducked dialogue -> final.wav (48k stereo)."""
import json, os, wave
import numpy as np

SR = 48000
D = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(D, 'timeline.json')))
voice = np.load(os.path.join(D, 'voice.npy'))
N = int((tl['duration'] + 0.6) * SR)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
rng = np.random.default_rng(3)

def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t, pan=0.0, gain=1.0):
    s = int(t * SR)
    if s >= N: return
    sig = sig[:N - s] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[s:s + len(sig)] += sig * l * 1.41; R[s:s + len(sig)] += sig * r * 1.41

from scipy.signal import lfilter
def lp(x, a):
    return lfilter([a], [1, a - 1], x).astype(np.float32)

def env_adsr(n, a, r, sus=1.0):
    e = np.ones(n, np.float32) * sus
    na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, sus, na)
    if nr < n: e[-nr:] *= np.linspace(1, 0, nr)
    return e

# ---------- instruments ----------
def pluck(f, dur=2.5, bright=0.5):
    """Karplus-Strong lyre pluck"""
    n = int(dur * SR); p = max(2, int(SR / f))
    buf = (rng.random(p).astype(np.float32) * 2 - 1)
    buf = lp(buf, 0.3 + bright * 0.6)
    out = np.empty(n, np.float32)
    decay = 0.996
    b = buf.copy(); idx = 0
    for i in range(0, n, p):
        k = min(p, n - i)
        out[i:i + k] = b[:k]
        b = decay * 0.5 * (b + np.roll(b, -1))
    out *= np.exp(-np.arange(n) / (SR * dur * 0.45))
    return out * 0.5

def bell(f, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3.5)
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6) + 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 2.2))
    s[:200] *= np.linspace(0, 1, 200)
    return (s * 0.22).astype(np.float32)

def pad(freqs, dur, att=1.5, rel=2.0, bright=0.08, gain=0.06):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            ph = rng.random() * 6.28
            # soft saw: few harmonics
            for h, a in ((1, 1), (2, 0.35), (3, 0.15), (4, 0.06)):
                s += (a * np.sin(2 * np.pi * ff * h * t + ph * h)).astype(np.float32)
    s = lp(s, bright)
    s *= env_adsr(n, att, rel)
    return s * gain / max(1, len(freqs))

def cello(f, dur, gain=0.18):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = np.zeros(n, np.float32)
    for h in range(1, 9):
        s += (np.sin(ph * h) / h).astype(np.float32)
    s = lp(s, 0.05)
    s *= env_adsr(n, min(0.5, dur * 0.3), min(1.6, dur * 0.5))
    return s * gain

def piano(f, dur=3.5, gain=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for h, a, d in ((1, 1, 1.2), (2, 0.45, 2.0), (3, 0.2, 3.0), (4, 0.1, 4.0)):
        s += (a * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * d)).astype(np.float32)
    s[:120] *= np.linspace(0, 1, 120)
    return s * gain

def drum(dur=0.5, f=90, gain=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f * (1 + 1.5 * np.exp(-t * 30))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 9)
    s += rng.standard_normal(n) * np.exp(-t * 40) * 0.25
    return (s * gain).astype(np.float32)

def tamb(gain=0.12):
    n = int(0.25 * SR); t = np.arange(n) / SR
    s = rng.standard_normal(n).astype(np.float32)
    s = s - lp(s, 0.3)
    s *= np.exp(-t * 18) * (1 + 0.5 * np.sin(2 * np.pi * 30 * t))
    return s * gain

def noise_bed(dur, a, gain, mod=0.0, modf=0.15):
    n = int(dur * SR); t = np.arange(n) / SR
    s = lp(rng.standard_normal(n).astype(np.float32), a)
    m = 1 + mod * np.sin(2 * np.pi * modf * t + rng.random() * 6) * np.sin(2 * np.pi * modf * 0.37 * t)
    return s * m * gain * env_adsr(n, 1.0, 1.0)

def crackle(dur, gain=0.2):
    n = int(dur * SR)
    s = np.zeros(n, np.float32)
    for _ in range(int(dur * 14)):
        p = rng.integers(0, n - 400)
        k = rng.integers(40, 300)
        s[p:p + k] += rng.standard_normal(k).astype(np.float32) * np.exp(-np.arange(k) / (k / 4)) * rng.random()
    return s * gain + noise_bed(dur, 0.02, 0.15)

def knock():
    out = np.zeros(int(0.9 * SR), np.float32)
    for k, tt in enumerate((0.0, 0.22, 0.44)):
        d = drum(0.25, 140 + k * 3, 0.55)
        d += rng.standard_normal(len(d)).astype(np.float32) * np.exp(-np.arange(len(d)) / 300) * 0.2
        s = int(tt * SR); out[s:s + len(d)] += d
    return out

# ---------- harmony ----------
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def chord(name, base=48):
    root = name.rstrip('m7s2').rstrip('m')
    r = NOTE[name[:2]] if name[:2] in NOTE else NOTE[name[0]]
    minor = 'm' in name[1:3] and not name.endswith('maj')
    ivs = [0, 3 if minor else 4, 7]
    if name.endswith('7'): ivs.append(10)
    if name.endswith('s2'): ivs = [0, 2, 7]
    return [midi(base + r + i) for i in ivs], base + r

MOODS = {
 'hill':        dict(prog=['D', 'G', 'Bm', 'A'], bar=3.0, pad=0.05, lyre=True, scale=[62, 64, 66, 69, 71, 74, 76]),
 'kitchen':     dict(prog=['F', 'Am', 'Bb', 'C'], bar=4.0, pad=0.035, piano=True, scale=[65, 69, 72, 74, 77]),
 'lyre':        dict(prog=['D', 'Bm', 'G', 'A'], bar=2.6, pad=0.05, lyre=True, scale=[62, 66, 69, 71, 74, 78]),
 'drums':       dict(prog=['D', 'C', 'D', 'C'], bar=2.0, pad=0.05, drums=True, lyre=True, scale=[62, 64, 66, 69, 72, 74]),
 'dark':        dict(prog=['Dm', 'Dm', 'Bb', 'A'], bar=4.0, pad=0.06, drone=38, fire=True),
 'dread':       dict(prog=['Dm', 'Bb', 'Gm', 'A'], bar=4.0, pad=0.06, drone=38, heart=True),
 'tension':     dict(prog=['Em', 'C', 'Em', 'B'], bar=3.5, pad=0.06, drone=40, resolve_at=2),
 'somber':      dict(prog=['Am', 'F', 'Dm', 'E'], bar=4.0, pad=0.06, cello=True),
 'kitchen_sad': dict(prog=['Dm', 'Bb', 'F', 'C'], bar=4.5, pad=0.035, piano=True, scale=[62, 65, 69, 72]),
 'musicbox':    dict(prog=['Am', 'Am', 'F', 'E'], bar=3.0, pad=0.04, box=True, drone=33, scale=[69, 72, 76, 81, 79, 76]),
 'grand':       dict(prog=['C', 'F', 'Am', 'G'], bar=2.8, pad=0.085, drums=False, lyre=False, brass=True, scale=[60, 64, 67, 72]),
 'empty':       dict(prog=['Cm', 'Ab', 'Cm', 'G'], bar=6.0, pad=0.03, wind=True, cello=True),
 'passage':     dict(prog=['Cm', 'Ab', 'Eb', 'Bb'], bar=4.5, pad=0.045, wind=True, piano=True, brighten=True, scale=[63, 67, 70, 72, 75]),
 'kitchen_hope':dict(prog=['F', 'Dm', 'Bb', 'C'], bar=4.0, pad=0.04, piano=True, scale=[65, 69, 72, 77]),
 'warm':        dict(prog=['D', 'A', 'Bm', 'G'], bar=3.0, pad=0.055, lyre=True, scale=[62, 66, 69, 74, 78]),
 'garden':      dict(prog=['Bm', 'G', 'D', 'A'], bar=3.5, pad=0.05, drone=35, lyre=True, scale=[59, 62, 66, 71]),
 'warm_sad':    dict(prog=['G', 'D', 'Em', 'C'], bar=3.5, pad=0.05, piano=True, scale=[67, 71, 74, 79]),
 'warm_full':   dict(prog=['D', 'G', 'Bm', 'A'], bar=3.0, pad=0.07, lyre=True, piano=True, scale=[62, 66, 69, 74, 76, 78]),
 'ending':      dict(prog=['F', 'C', 'Dm', 'Bb', 'F', 'C', 'Bb', 'F'], bar=3.2, pad=0.06, piano=True, lyre=True, scale=[65, 69, 72, 74, 77, 81]),
}

for si, sc in enumerate(tl['scenes']):
    m = MOODS[sc['mood']]
    t0, t1 = sc['start'], sc['end']
    dur = t1 - t0
    bar = m['bar']
    nb = int(np.ceil(dur / bar))
    xf = 0.6  # crossfade overlap
    for b in range(nb):
        cname = m['prog'][b % len(m['prog'])]
        if m.get('resolve_at') is not None and b >= m['resolve_at'] * 2:
            cname = ['G', 'C', 'Em', 'D'][b % 4]
        fs, root = chord(cname, 48)
        bt = t0 + b * bar
        if bt >= t1: break
        bd = min(bar + xf, t1 - bt + 1.2)
        g = m['pad']
        if m.get('brighten'):
            g *= 0.6 + 0.8 * b / max(1, nb)
        add(pad(fs, bd, att=min(1.2, bd * 0.4), rel=min(1.4, bd * 0.4), bright=0.06 if not m.get('brighten') else 0.04 + 0.08 * b / nb, gain=g), bt, pan=-0.2)
        add(pad([fs[0] / 2], bd, att=0.8, rel=1.0, bright=0.03, gain=g * 0.9), bt, pan=0.2)
        sc_notes = m.get('scale')
        if m.get('lyre') and sc_notes:
            # arpeggiated lyre motif: callback motif 1-3-5-6
            step = bar / 6
            pat = [0, 2, 4, 2, 5, 4] if b % 2 == 0 else [0, 2, 4, 6, 4, 2]
            chord_m = [int(round(12 * np.log2(f / 440) + 69)) + 12 for f in fs]
            pool = sorted(chord_m + [chord_m[0] + 12, chord_m[1] + 12, chord_m[2] + 12, chord_m[0] + 14])
            for k, pi in enumerate(pat):
                add(pluck(midi(pool[pi % len(pool)]), 2.2, 0.5), bt + k * step + rng.random() * 0.015,
                    pan=-0.4 + 0.15 * k, gain=0.33)
        if m.get('piano') and sc_notes:
            chord_m = [int(round(12 * np.log2(f / 440) + 69)) + 12 for f in fs]
            add(piano(midi(chord_m[0] - 12), 4.0, 0.10), bt, pan=-0.1)
            for k, nm in enumerate(chord_m):
                add(piano(midi(nm), 3.5, 0.06), bt + 0.04 * k + (0 if b % 2 == 0 else bar / 2), pan=0.15)
        if m.get('box') and sc_notes:
            for k in range(4):
                nm = sc_notes[(b * 3 + k * 2) % len(sc_notes)] + 12
                add(bell(midi(nm), 1.6) * 0.35, bt + k * bar / 4, pan=0.3)
        if m.get('drums'):
            beat = bar / 4
            for k in range(4):
                add(drum(0.5, 85, 0.45 if k % 2 == 0 else 0.3), bt + k * beat)
                add(tamb(0.10), bt + k * beat + beat / 2, pan=0.4)
        if m.get('brass'):
            add(cello(fs[0] * 2, bd * 0.9, 0.09), bt, pan=-0.3)
            add(cello(fs[2] * 2, bd * 0.9, 0.06), bt, pan=0.3)
        if m.get('cello') and b % 2 == 0:
            add(cello(midi(root - 12), min(bar * 2, dur - b * bar + 1), 0.16), bt)
        if m.get('heart'):
            for k in range(int(bar / 0.9)):
                add(drum(0.3, 55, 0.35), bt + k * 0.9); add(drum(0.3, 50, 0.22), bt + k * 0.9 + 0.22)
    if m.get('drone'):
        add(cello(midi(m['drone']), dur + 1.0, 0.13), t0)
    if m.get('fire'):
        add(crackle(dur + 0.5, 0.25), t0, pan=0.2)
    if m.get('wind'):
        add(noise_bed(dur + 0.5, 0.012, 0.9, mod=0.8), t0, pan=-0.3)

# ---------- accents: high notes on hopeful words, deep notes on heavy words ----------
for a in tl['accents']:
    t = a['t']
    if a['kind'] == 'hi':
        add(bell(midi(86), 3.2), t - 0.03, pan=0.35, gain=0.6)
        add(bell(midi(93), 2.5), t + 0.1, pan=-0.3, gain=0.35)
    else:
        add(cello(midi(31), 3.2, 0.32), t - 0.05)
        add(cello(midi(38), 2.8, 0.12), t - 0.05)

# ---------- scene-specific SFX ----------
sc = {s['id']: s for s in tl['scenes']}
def line(sid, i): return sc[sid]['lines'][i]
# crowd cheer
c = sc['cheer']
add(noise_bed(c['end'] - c['start'], 0.15, 0.12, mod=0.5, modf=0.5), c['start'], pan=0.1)
# sword clink & drop in garden
add(drum(0.4, 900, 0.2) + bell(midi(96), 0.4)[:int(0.4 * SR)] * 0.6, line('sword', 2)['end'] + 0.35, pan=0.2)
add(drum(0.4, 300, 0.25), line('sword', 4)['start'] + 0.8)
# knock on the door (ending)
e = sc['ending']
knock_t = line('ending', 1)['end'] + 0.55
add(knock(), knock_t, pan=-0.5, gain=1.0)
tl['sfx'].append({'kind': 'knock', 't': round(knock_t, 3)})
# final warm chord swell + bells
fs, _ = chord('F', 48)
add(pad(fs + [fs[0] * 2], 6.0, att=2.0, rel=3.0, gain=0.09, bright=0.08), e['end'] - 5.5)
add(bell(midi(89), 4.0), e['end'] - 3.0, pan=0.2, gain=0.4)
add(bell(midi(84), 4.0), e['end'] - 2.6, pan=-0.2, gain=0.3)
# helmet clatter (uriah)
u = sc['uriah']
add(drum(0.6, 220, 0.3), line('uriah', 2)['end'] + 0.3, pan=0.3)

json.dump(tl, open(os.path.join(D, 'timeline.json'), 'w'))

# ---------- duck music under voice ----------
v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
hop = 480
ve = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, 'same')[::hop])
duck = np.clip(ve / 0.05, 0, 1)
# smooth attack/release
sm = np.zeros_like(duck); acc = 0
for i, d in enumerate(duck):
    acc = acc + (0.5 if d > acc else 0.04) * (d - acc); sm[i] = acc
g = 1 - 0.45 * sm
g = np.repeat(g, hop)[:N]
if len(g) < N: g = np.pad(g, (0, N - len(g)), constant_values=1)
music_gain = 0.85
outL = L * g * music_gain + v
outR = R * g * music_gain + v
# gentle limiter
pk = max(np.abs(outL).max(), np.abs(outR).max())
print('peak', pk)
def soft(x): return np.tanh(x * 1.2) / np.tanh(1.2)
outL = soft(outL / max(pk, 1) * 0.98); outR = soft(outR / max(pk, 1) * 0.98)
st = np.stack([outL, outR], 1)
st = (st / np.abs(st).max() * 0.93 * 32767).astype(np.int16)
with wave.open(os.path.join(D, 'final.wav'), 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(st.tobytes())
print('wrote final.wav', len(st) / SR)
